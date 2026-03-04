from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.error import URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


NEWS_FEEDS = [
    ("Reuters Markets", "https://feeds.reuters.com/reuters/businessNews"),
    ("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
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
        if article["title"] in seen:
            continue
        seen.add(article["title"])
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
    items = []
    seen_titles = set()

    for source_name, feed_url in NEWS_FEEDS:
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
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = _parse_pubdate(item.findtext("pubDate"))
            summary = (item.findtext("description") or "").strip()

            if not title or title in seen_titles:
                continue

            seen_titles.add(title)
            items.append(
                {
                    "title": title,
                    "source": source_name,
                    "published_at": pub_date,
                    "url": link,
                    "summary": summary or None,
                    "tags": classify_news_tags(title, summary),
                }
            )

            if len(items) >= limit:
                return items

    return items if items else FALLBACK_NEWS
