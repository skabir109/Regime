import re
from dataclasses import dataclass


MODE_SECTIONS: dict[str, list[tuple[str, int | None]]] = {
    "BRIEFING": [
        ("Headline", None),
        ("What Changed", 3),
        ("Market Implications", 3),
        ("Watchlist Impact", None),
        ("Bull Case", 2),
        ("Bear Case", 2),
        ("Risk Flags", 3),
        ("Next Actions", 3),
    ],
    "ALERT_DRILLDOWN": [
        ("Alert Summary", None),
        ("Trigger Drivers", 4),
        ("What Changed Since Prior State", 3),
        ("Supporting Evidence", 3),
        ("Conflicting Evidence", 3),
        ("Affected Assets/Sectors", 5),
        ("Invalidation Signals", 3),
        ("Immediate Watchlist Priorities", 3),
    ],
    "WORLD_AFFAIRS": [
        ("Event Summary", None),
        ("Why It Matters Now", 3),
        ("First-Order Market Effects", 4),
        ("Second-Order Effects", 3),
        ("Most Exposed Watchlist Names", 5),
        ("What Would Confirm This Theme", 3),
        ("What Would Weaken This Theme", 3),
    ],
    "WATCHLIST_CONTEXT": [
        ("Regime Alignment", None),
        ("Key Drivers", 4),
        ("Catalyst Risk", 3),
        ("Sector Read-Through", 2),
        ("Related Macro Themes", 3),
        ("Monitoring Checklist", 3),
    ],
}


HEADER_RE = re.compile(r"^\s*\*{0,2}([A-Za-z0-9\-/ ]+)\*{0,2}:\*{0,2}\s*(.*)?$")
BULLET_RE = re.compile(r"^\s*(?:-|[*]|\d+[.])\s+")
SYMBOL_LINE_RE = re.compile(r"^\s*-\s*([A-Z]{1,5}):\s*(.+)$")


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


def _normalize_header(raw: str) -> str:
    return raw.strip().strip("*").strip()


def _header_positions(lines: list[str]) -> list[tuple[int, str]]:
    positions: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        if BULLET_RE.match(line):
            continue
        match = HEADER_RE.match(line)
        if match:
            positions.append((idx, _normalize_header(match.group(1))))
    return positions


def _count_bullets_between(lines: list[str], start: int, end: int) -> int:
    return sum(1 for line in lines[start:end] if BULLET_RE.match(line))


def _extract_symbol_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if SYMBOL_LINE_RE.match(line)]


def validate_analysis(mode: str, text: str, watchlist: list[str] | None = None) -> ValidationResult:
    normalized_mode = (mode or "BRIEFING").strip().upper()
    specs = MODE_SECTIONS.get(normalized_mode)
    if not specs:
        return ValidationResult(ok=False, errors=[f"Unsupported mode: {normalized_mode}"])

    lines = (text or "").splitlines()
    header_positions = _header_positions(lines)
    header_map = {header: idx for idx, header in header_positions}
    expected_headers = [header for header, _ in specs]
    errors: list[str] = []

    for header in expected_headers:
        if header not in header_map:
            errors.append(f"Missing required section header: {header}:")

    if errors:
        return ValidationResult(ok=False, errors=errors)

    # Enforce no unknown headers other than Need.
    allowed_headers = set(expected_headers) | {"Need"}
    for _, header in header_positions:
        if header not in allowed_headers:
            errors.append(f"Unexpected section header for {normalized_mode}: {header}:")

    # Enforce bullet caps by section.
    ordered = sorted((header_map[h], h) for h in expected_headers)
    for i, (start_idx, header) in enumerate(ordered):
        end_idx = ordered[i + 1][0] if i + 1 < len(ordered) else len(lines)
        max_bullets = dict(specs)[header]
        if max_bullets is not None:
            bullets = _count_bullets_between(lines, start_idx + 1, end_idx)
            if bullets > max_bullets:
                errors.append(f"Section '{header}' exceeds bullet cap ({bullets}/{max_bullets}).")

    # Require explicit invalidation condition.
    if "invalidation" not in text.lower():
        errors.append("Missing explicit invalidation trigger/signal.")

    # Symbol schema check when symbol lines are present.
    for line in _extract_symbol_lines(lines):
        payload = line.split(":", 1)[1]
        if payload.count(";") < 3:
            errors.append(f"Symbol line missing required schema fields: {line.strip()}")

    # Watchlist coverage check.
    if watchlist:
        body_upper = text.upper()
        for symbol in {item.strip().upper() for item in watchlist if item.strip()}:
            if symbol and symbol not in body_upper:
                errors.append(f"Missing watchlist symbol coverage: {symbol}")

    return ValidationResult(ok=len(errors) == 0, errors=errors)
