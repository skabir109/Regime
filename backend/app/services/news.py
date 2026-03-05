from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import re
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


NEWS_FEEDS = [
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
    ("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch Top Stories", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Nasdaq Market Activity", "https://www.nasdaq.com/feed/rssoutbound?category=Market%20Activity"),
    ("Investing.com Markets", "https://www.investing.com/rss/news_25.rss"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("NYTimes Business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
    ("NYTimes World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
]

SOURCE_RELIABILITY = {
    "reuters business": 1.00,
    "reuters world": 1.00,
    "ap business": 0.98,
    "ap world": 0.98,
    "marketwatch top stories": 0.90,
    "nytimes business": 0.90,
    "nytimes world": 0.90,
    "bbc business": 0.88,
    "nasdaq market activity": 0.85,
    "cnbc markets": 0.82,
    "yahoo finance": 0.78,
    "investing.com markets": 0.74,
}

TAG_URGENCY_WEIGHT = {
    "Geopolitics": 0.20,
    "Volatility": 0.18,
    "Rates": 0.14,
    "Energy": 0.12,
    "Earnings": 0.08,
    "AI": 0.07,
    "Macro": 0.03,
}

TITLE_STOPWORDS = {
    "the", "a", "an", "to", "for", "of", "and", "in", "on", "at", "as", "with", "from", "by",
    "after", "before", "over", "under", "amid", "into", "about", "new", "says", "say", "us",
    "u", "s", "market", "markets",
}

FALLBACK_NEWS = [
    {
        "title": "Market feed unavailable in local mode. Connect deployment to fetch live headlines.",
        "source": "System",
        "published_at": "offline",
        "url": "#",
        "summary": "The application is running, but external RSS feeds could not be reached from the current environment.",
        "tags": ["System"],
    },
    {
        "title": "Use this panel for macro headlines, catalyst tracking, and regime context.",
        "source": "System",
        "published_at": "offline",
        "url": "#",
        "summary": "This workspace is designed to behave like a lightweight terminal feed for catalyst monitoring and market narrative review.",
        "tags": ["System"],
    },
]

WATCHLIST_ALIASES = {
    "AAPL": ["apple", "iphone"],
    "MSFT": ["microsoft", "azure"],
    "NVDA": ["nvidia", "semiconductor", "chipmaker"],
    "AMZN": ["amazon", "aws"],
    "META": ["meta", "facebook", "instagram"],
    "TSLA": ["tesla", "musk"],
    "AMD": ["amd", "advanced micro devices"],
    "GOOGL": ["alphabet", "google", "youtube"],
}


def _parse_pubdate(raw_value: str | None) -> str:
    if not raw_value:
        return "unknown"
    try:
        return parsedate_to_datetime(raw_value).isoformat()
    except (TypeError, ValueError, IndexError):
        return raw_value


def _parse_timestamp_for_sort(value: str) -> datetime:
    floor = datetime.min.replace(tzinfo=timezone.utc)
    if not value or value in {"unknown", "offline"}:
        return floor
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return floor


def _clamp_future_timestamp(timestamp: datetime, now_utc: datetime) -> datetime:
    floor = datetime.min.replace(tzinfo=timezone.utc)
    if timestamp == floor:
        return timestamp
    max_allowed = now_utc.replace(microsecond=0) + timedelta(minutes=10)
    if timestamp > max_allowed:
        return max_allowed
    return timestamp


def _normalize_title(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9 ]", "", lowered)
    return lowered


def _headline_tokens(title: str) -> list[str]:
    normalized = _normalize_title(title)
    tokens = [token for token in normalized.split(" ") if token and token not in TITLE_STOPWORDS and len(token) > 2]
    return tokens[:12]


def _headline_signature(title: str) -> str:
    return " ".join(_headline_tokens(title))


def _signature_overlap(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_set = set(left.split(" "))
    right_set = set(right.split(" "))
    if not left_set or not right_set:
        return 0.0
    inter = len(left_set.intersection(right_set))
    union = len(left_set.union(right_set))
    return inter / union if union else 0.0


def _find_cluster_signature(signature: str, existing_signatures: list[str]) -> str | None:
    if not signature:
        return None
    if signature in existing_signatures:
        return signature
    for candidate in existing_signatures:
        if _signature_overlap(signature, candidate) >= 0.84:
            return candidate
    return None


def _source_key(source: str, url: str) -> str:
    if source:
        return source.strip().lower()
    try:
        host = (urlparse(url).hostname or "").lower()
        return host or "unknown"
    except ValueError:
        return "unknown"


def _safe_text(value: str | None) -> str:
    return (value or "").strip()


def _clean_description(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    cleaned = html.unescape(raw)
    # Remove CSS/script blocks and HTML tags that leak into RSS descriptions.
    cleaned = re.sub(r"(?is)<style.*?>.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?is)<script.*?>.*?</script>", " ", cleaned)
    cleaned = re.sub(r"@media\s*\([^)]*\)\s*\{[^{}]*\}", " ", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"(?i)\bimage source\s*:[^.;\n]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 420:
        cleaned = cleaned[:417].rstrip() + "..."
    return cleaned


def _recency_weight(timestamp: datetime, now_utc: datetime) -> float:
    if timestamp == datetime.min.replace(tzinfo=timezone.utc):
        return 0.0
    age_hours = max(0.0, (now_utc - timestamp).total_seconds() / 3600.0)
    # Fast decay after 24h, but still retain some value through 3 days.
    if age_hours <= 24:
        return 1.0 - (age_hours / 24.0) * 0.40
    if age_hours <= 72:
        return 0.60 - ((age_hours - 24) / 48.0) * 0.45
    return 0.10


def _article_score(article: dict, now_utc: datetime) -> float:
    source_name = str(article.get("source", "")).lower()
    source_weight = SOURCE_RELIABILITY.get(source_name, 0.70)
    recency = _recency_weight(article.get("_ts", datetime.min.replace(tzinfo=timezone.utc)), now_utc)
    tags = article.get("tags", []) or []
    urgency = max((TAG_URGENCY_WEIGHT.get(tag, 0.02) for tag in tags), default=0.02)
    source_count = int(article.get("_source_count", 1))
    confirmation_boost = min(0.25, max(0, source_count - 1) * 0.05)
    return (source_weight * 1.4) + (recency * 1.2) + urgency + confirmation_boost


def classify_news_tags(title: str, summary: str | None = None) -> list[str]:
    text = f"{title} {summary or ''}".lower()
    tags = []
    rules = {
        "Rates": ["fed", "yield", "rate", "inflation", "treasury", "powell"],
        "Earnings": ["earnings", "guidance", "revenue", "profit", "quarter"],
        "Geopolitics": ["war", "tariff", "sanction", "election", "government", "china"],
        "Energy": ["oil", "gas", "opec", "crude", "energy"],
        "Volatility": ["vix", "volatility", "selloff", "panic", "risk-off"],
        "AI": ["ai", "chip", "semiconductor", "nvidia"],
    }
    for label, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            tags.append(label)
    return tags or ["Macro"]


def _watch_terms(symbol: str, label: str) -> list[str]:
    terms = {symbol.lower(), label.lower()}
    normalized_words = [part.strip().lower() for part in label.replace(",", " ").split() if len(part.strip()) > 2]
    terms.update(normalized_words)
    terms.update(WATCHLIST_ALIASES.get(symbol.upper(), []))
    return [term for term in terms if term]


def match_related_news(symbol: str, label: str, items: list[dict], limit: int = 3) -> list[dict]:
    terms = _watch_terms(symbol, label)
    matches = []
    for item in items:
        haystack = f'{item.get("title", "")} {item.get("summary") or ""}'.lower()
        if any(term in haystack for term in terms):
            matches.append(
                {
                    "title": item["title"],
                    "source": item["source"],
                    "url": item["url"],
                }
            )
        if len(matches) >= limit:
            break
    return matches


def build_watchlist_news(items: list[dict], watchlist: list[dict], limit: int = 10) -> list[dict]:
    matched = []
    seen = set()
    for article in items:
        symbols = []
        haystack = f'{article.get("title", "")} {article.get("summary") or ""}'.lower()
        for entry in watchlist:
            terms = _watch_terms(entry["symbol"], entry["label"])
            if any(term in haystack for term in terms):
                symbols.append(entry["symbol"])
        if not symbols:
            continue
        title_key = _normalize_title(article["title"])
        if title_key in seen:
            continue
        seen.add(title_key)
        matched.append(
            {
                "title": article["title"],
                "source": article["source"],
                "published_at": article["published_at"],
                "url": article["url"],
                "summary": article.get("summary"),
                "tags": article.get("tags", []),
                "matched_symbols": sorted(set(symbols)),
            }
        )
        if len(matched) >= limit:
            break
    return matched


def fetch_market_news(limit: int = 8) -> list[dict]:
    all_items: list[dict] = []
    seen_titles = set()
    cluster_index: dict[str, int] = {}
    cluster_signatures: list[str] = []
    per_source_cap = max(4, min(limit * 2, 14))
    now_utc = datetime.now(timezone.utc)

    for source_name, feed_url in NEWS_FEEDS:
        source_added = 0
        try:
            request = Request(
                feed_url,
                headers={"User-Agent": "RegimeTerminal/0.2"},
            )
            with urlopen(request, timeout=4) as response:
                payload = response.read()
        except (TimeoutError, URLError, ValueError):
            continue

        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            continue

        for item in root.findall(".//item"):
            title = _safe_text(item.findtext("title"))
            link = _safe_text(item.findtext("link"))
            pub_date = _parse_pubdate(item.findtext("pubDate"))
            summary = _clean_description(item.findtext("description"))
            title_key = _normalize_title(title)
            signature = _headline_signature(title)

            if not title or title_key in seen_titles:
                continue

            seen_titles.add(title_key)
            cluster_sig = _find_cluster_signature(signature, cluster_signatures)
            candidate_ts = _clamp_future_timestamp(_parse_timestamp_for_sort(pub_date), now_utc)
            if cluster_sig and cluster_sig in cluster_index:
                idx = cluster_index[cluster_sig]
                canonical = all_items[idx]
                canonical["_source_cluster"].add(source_name)
                canonical["_source_count"] = len(canonical["_source_cluster"])
                # Prefer fresher headline/summary timing for the cluster representative.
                if candidate_ts > canonical.get("_ts", datetime.min.replace(tzinfo=timezone.utc)):
                    canonical["published_at"] = candidate_ts.isoformat()
                    canonical["_ts"] = candidate_ts
                continue

            article = {
                "title": title,
                "source": source_name,
                "published_at": candidate_ts.isoformat(),
                "url": link,
                "summary": summary or None,
                "tags": classify_news_tags(title, summary),
                "_source_key": _source_key(source_name, link),
                "_ts": candidate_ts,
                "_signature": signature,
                "_source_cluster": {source_name},
                "_source_count": 1,
            }
            all_items.append(article)
            if signature:
                cluster_index[signature] = len(all_items) - 1
                cluster_signatures.append(signature)
            source_added += 1

            if source_added >= per_source_cap:
                break

    if not all_items:
        return FALLBACK_NEWS

    for article in all_items:
        article["_score"] = _article_score(article, now_utc)

    # Rank by reliability/urgency/recency score, then timestamp.
    ranked = sorted(
        all_items,
        key=lambda item: (
            float(item.get("_score", 0.0)),
            item.get("_ts", datetime.min.replace(tzinfo=timezone.utc)),
            item.get("title", ""),
        ),
        reverse=True,
    )

    # Diversity pass: limit source concentration in top results.
    selected = []
    per_source_counts: dict[str, int] = {}
    max_per_source = 2
    for article in ranked:
        source_key = str(article.get("_source_key", "unknown"))
        if per_source_counts.get(source_key, 0) >= max_per_source:
            continue
        per_source_counts[source_key] = per_source_counts.get(source_key, 0) + 1
        selected.append(article)
        if len(selected) >= limit:
            break

    # Fill pass: if diversity filter is too strict, top up from remainder.
    if len(selected) < limit:
        seen_urls = {item.get("url") for item in selected}
        for article in ranked:
            if article.get("url") in seen_urls:
                continue
            selected.append(article)
            seen_urls.add(article.get("url"))
            if len(selected) >= limit:
                break

    # Strip internal ranking fields before returning.
    for article in selected:
        article.pop("_source_key", None)
        article.pop("_ts", None)
        article.pop("_signature", None)
        article.pop("_source_cluster", None)
        article.pop("_source_count", None)
        article.pop("_score", None)

    return selected
