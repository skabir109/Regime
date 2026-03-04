from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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
]

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


def _normalize_title(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9 ]", "", lowered)
    return lowered


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
    all_items = []
    seen_titles = set()
    per_source_cap = max(4, min(limit * 2, 14))

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
            summary = _safe_text(item.findtext("description"))
            title_key = _normalize_title(title)

            if not title or title_key in seen_titles:
                continue

            seen_titles.add(title_key)
            all_items.append(
                {
                    "title": title,
                    "source": source_name,
                    "published_at": pub_date,
                    "url": link,
                    "summary": summary or None,
                    "tags": classify_news_tags(title, summary),
                    "_source_key": _source_key(source_name, link),
                    "_ts": _parse_timestamp_for_sort(pub_date),
                }
            )
            source_added += 1

            if source_added >= per_source_cap:
                break

    if not all_items:
        return FALLBACK_NEWS

    # Most recent first.
    ranked = sorted(
        all_items,
        key=lambda item: (item.get("_ts", datetime.min.replace(tzinfo=timezone.utc)), item.get("title", "")),
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

    return selected
