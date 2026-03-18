import hashlib
import json
from pathlib import Path
import time
from threading import Lock

import requests

from app.config import (
    AI_ANALYZE_CACHE_PATH,
    AI_ANALYZE_CACHE_MAX_ENTRIES,
    AI_ANALYZE_CACHE_TTL_SECONDS,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
    REGIME_ANALYST_PROMPT_PATH,
)
from app.schemas import AIAnalyzeRequest, AIAnalyzeResponse
from app.services.analysis_validator import validate_analysis


_PROMPT_CACHE: str | None = None
_ANALYZE_CACHE: dict[str, tuple[float, AIAnalyzeResponse]] = {}
_CACHE_IO_LOCK = Lock()
_DISK_CACHE_LOADED = False


def _load_prompt(path: Path) -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE
    if not path.exists():
        raise RuntimeError(f"Prompt file not found: {path}")
    _PROMPT_CACHE = path.read_text(encoding="utf-8").strip()
    return _PROMPT_CACHE


def _require_llm_config() -> None:
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY (or OPENAI_API_KEY) is not configured.")


def _completion_urls() -> list[str]:
    base = LLM_BASE_URL.rstrip("/")
    if base.endswith("/chat/completions"):
        return [base]
    urls = [
        f"{base}/chat/completions",
        f"{base}/v1/chat/completions",
        f"{base}/api/v1/chat/completions",
    ]
    # De-dup while preserving order.
    seen: set[str] = set()
    return [url for url in urls if not (url in seen or seen.add(url))]


def _chat_completion(messages: list[dict[str, str]], max_tokens: int | None = None, temperature: float = 0.2) -> str:
    _require_llm_config()

    errors: list[str] = []
    for url in _completion_urls():
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": messages,
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:
            errors.append(f"{url} -> 404")
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"LLM request failed ({response.status_code}) at {url}: {response.text[:500]}")

        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError(f"LLM response had no choices at {url}.")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            # OpenAI-compatible multimodal responses can return list parts.
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            content = "\n".join(part for part in text_parts if part)

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"LLM response had empty content at {url}.")
        return content.strip()

    raise RuntimeError(
        "LLM request failed (404) for completion URLs: " + " | ".join(errors)
    )


def _build_user_message(payload: AIAnalyzeRequest) -> str:
    watchlist_text = ", ".join(symbol.upper() for symbol in payload.watchlist) if payload.watchlist else "None"
    kb_context_text = "\n".join(f"- {item}" for item in payload.kb_context[:8]) if payload.kb_context else "- None"
    context_json = json.dumps(payload.context or {}, indent=2, ensure_ascii=True)

    return (
        f"Mode: {payload.mode.strip().upper() or 'BRIEFING'}\n"
        f"Word budget: {max(120, min(payload.max_words, 320))}\n"
        f"Watchlist: {watchlist_text}\n\n"
        f"User query:\n{payload.query.strip() or 'No extra query provided.'}\n\n"
        f"Structured context (JSON):\n{context_json}\n\n"
        f"KB context snippets:\n{kb_context_text}\n\n"
        "Requirements:\n"
        "- Use only the selected mode template.\n"
        "- Complete required headers before adding detail.\n"
        "- Keep bullet caps and include at least one explicit invalidation condition.\n"
        "- For symbols, use: SYMBOL: Stance; driver(s); condition; invalidation.\n"
    )


def _serialize_payload(payload: AIAnalyzeRequest) -> str:
    canonical = {
        "mode": (payload.mode or "BRIEFING").strip().upper(),
        "query": payload.query or "",
        "context": payload.context or {},
        "watchlist": sorted([item.strip().upper() for item in (payload.watchlist or []) if item.strip()]),
        "kb_context": payload.kb_context or [],
        "max_words": payload.max_words,
        "regenerate_on_fail": bool(payload.regenerate_on_fail),
    }
    return json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _cache_key(payload: AIAnalyzeRequest) -> str:
    material = f"{LLM_MODEL}|{_serialize_payload(payload)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> AIAnalyzeResponse | None:
    _load_disk_cache_once()
    item = _ANALYZE_CACHE.get(key)
    now = time.time()
    if not item:
        return None
    expires_at, value = item
    if expires_at <= now:
        _ANALYZE_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: AIAnalyzeResponse) -> None:
    ttl = max(0, AI_ANALYZE_CACHE_TTL_SECONDS)
    if ttl == 0:
        return
    _load_disk_cache_once()
    now = time.time()
    _ANALYZE_CACHE[key] = (now + ttl, value)

    max_entries = max(32, AI_ANALYZE_CACHE_MAX_ENTRIES)
    if len(_ANALYZE_CACHE) > max_entries:
        overflow = len(_ANALYZE_CACHE) - max_entries
        for cache_key, _ in sorted(_ANALYZE_CACHE.items(), key=lambda item: item[1][0])[:overflow]:
            _ANALYZE_CACHE.pop(cache_key, None)
    _flush_disk_cache()


def _load_disk_cache_once() -> None:
    global _DISK_CACHE_LOADED
    if _DISK_CACHE_LOADED:
        return
    with _CACHE_IO_LOCK:
        if _DISK_CACHE_LOADED:
            return
        _DISK_CACHE_LOADED = True
        path = AI_ANALYZE_CACHE_PATH
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return

        now = time.time()
        rows = payload.get("entries", {})
        if not isinstance(rows, dict):
            return

        for key, item in rows.items():
            if not isinstance(item, dict):
                continue
            expires_at = float(item.get("expires_at", 0))
            if expires_at <= now:
                continue
            response_payload = item.get("response")
            if not isinstance(response_payload, dict):
                continue
            try:
                parsed = AIAnalyzeResponse(**response_payload)
            except Exception:
                continue
            _ANALYZE_CACHE[key] = (expires_at, parsed)


def _flush_disk_cache() -> None:
    path = AI_ANALYZE_CACHE_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        now = time.time()
        rows = {}
        for key, (expires_at, value) in _ANALYZE_CACHE.items():
            if expires_at <= now:
                continue
            rows[key] = {
                "expires_at": expires_at,
                "response": value.dict(),
            }
        payload = {"saved_at": now, "entries": rows}
        with _CACHE_IO_LOCK:
            path.write_text(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    except Exception:
        # Cache persistence failure should not impact primary response path.
        return


def generate_analysis(payload: AIAnalyzeRequest) -> AIAnalyzeResponse:
    mode = payload.mode.strip().upper() or "BRIEFING"
    cache_key = _cache_key(payload)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    system_prompt = _load_prompt(REGIME_ANALYST_PROMPT_PATH)
    user_message = _build_user_message(payload)

    attempts = 1
    initial = _chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )

    result = validate_analysis(mode=mode, text=initial, watchlist=payload.watchlist)
    content = initial

    if not result.ok and payload.regenerate_on_fail:
        attempts = 2
        revision_prompt = (
            "Revise the prior response so it passes all validator errors below. "
            "Keep the same intent and mode, but fix only compliance and clarity issues.\n"
            + "\n".join(f"- {err}" for err in result.errors)
        )
        content = _chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": initial},
                {"role": "user", "content": revision_prompt},
            ],
            temperature=0.2,
        )
        result = validate_analysis(mode=mode, text=content, watchlist=payload.watchlist)

    response = AIAnalyzeResponse(
        mode=mode,
        content=content,
        attempts=attempts,
        model=LLM_MODEL,
        validator_passed=result.ok,
        validation_errors=result.errors,
    )
    _cache_set(cache_key, response)
    return response


def generate_executive_summary(regime: str, confidence: float, headlines: list[str]) -> str:
    """Compatibility helper used by market state summary generation."""
    if not LLM_API_KEY:
        return (
            "Market intelligence active. AI commentary is unavailable right now, "
            "so Regime is showing the live model state and core market signals instead."
        )

    headline_list = "\n".join([f"- {h}" for h in headlines[:5]])
    prompt = (
        "You are a senior macro strategist. Provide a concise, 3-sentence executive summary.\n\n"
        f"CURRENT MARKET REGIME: {regime} (Model Confidence: {confidence * 100:.1f}%)\n"
        f"TOP HEADLINES:\n{headline_list}\n\n"
        "INSTRUCTIONS:\n"
        "1) Summarize dominant market mood vs regime.\n"
        "2) Identify primary catalyst or contradiction.\n"
        "3) State one trader priority right now.\n"
        "IMPORTANT: Return ONLY plain text. Do NOT use markdown bolding (**) or any other formatting.\n"
        "Tone: professional, direct, concise."
    )

    try:
        return _chat_completion(
            [
                {"role": "system", "content": "You are a professional market analyst."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.4,
        )
    except Exception:
        return (
            "Market intelligence active. AI commentary is taking longer than expected, "
            "so Regime is falling back to the live regime snapshot and deterministic market signals."
        )
