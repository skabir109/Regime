from app.services.news import fetch_market_news
from app.services.watchlist import load_watchlist


THEME_RULES = [
    {
        "theme": "Central Banks",
        "keywords": ["fed", "ecb", "boj", "central bank", "powell", "rate", "yield", "treasury", "inflation"],
        "region": "Global",
        "urgency": "high",
        "severity": "high",
        "affected_assets": ["US Treasuries", "USD", "Gold", "Growth Equities", "Banks"],
        "market_view": [
            "Higher-rate signals pressure long-duration equities and support the dollar.",
            "Softer inflation or dovish policy can support risk assets and rate-sensitive sectors.",
        ],
        "second_order_effects": [
            "Valuation pressure on growth names.",
            "Shifts in funding conditions and credit appetite.",
        ],
        "why": "Central bank policy changes discount rates, liquidity conditions, and global risk appetite.",
    },
    {
        "theme": "Energy Shock",
        "keywords": ["oil", "gas", "opec", "crude", "energy", "refinery"],
        "region": "Global",
        "urgency": "high",
        "severity": "high",
        "affected_assets": ["Crude Oil", "Energy Equities", "Airlines", "Inflation Breakevens"],
        "market_view": [
            "Higher energy prices support producers and raise inflation sensitivity.",
            "Fuel-intensive industries and transport names face margin pressure.",
        ],
        "second_order_effects": [
            "Potential upward pressure on inflation expectations.",
            "Margin compression for transport and consumer-facing sectors.",
        ],
        "why": "Energy shocks flow through inflation, transport costs, and consumer purchasing power.",
    },
    {
        "theme": "War And Security",
        "keywords": ["war", "missile", "attack", "military", "ceasefire", "troop", "defense", "drone"],
        "region": "Geopolitical",
        "urgency": "high",
        "severity": "high",
        "affected_assets": ["Defense Equities", "Oil", "Gold", "Shipping", "Safe-Haven FX"],
        "market_view": [
            "Escalation tends to support defense names, oil, and havens.",
            "Risk assets may weaken if conflict broadens or shipping routes are threatened.",
        ],
        "second_order_effects": [
            "Higher freight and insurance costs.",
            "Potential supply chain and commodity disruptions.",
        ],
        "why": "Conflict reprices energy, logistics, safe havens, and overall risk appetite.",
    },
    {
        "theme": "Trade And Sanctions",
        "keywords": ["tariff", "sanction", "trade", "export control", "restriction", "duty"],
        "region": "Global",
        "urgency": "medium",
        "severity": "medium",
        "affected_assets": ["Semiconductors", "Industrials", "Emerging Markets", "USD"],
        "market_view": [
            "Trade friction pressures exporters and globally exposed cyclicals.",
            "Selective domestic or protected industries may benefit from barriers.",
        ],
        "second_order_effects": [
            "Supply chain rerouting and margin pressure.",
            "Longer-term capex shifts across regions.",
        ],
        "why": "Trade restrictions alter supply chains, demand visibility, and cross-border pricing power.",
    },
    {
        "theme": "China Growth",
        "keywords": ["china", "beijing", "property", "stimulus", "yuan", "manufacturing"],
        "region": "China",
        "urgency": "medium",
        "severity": "medium",
        "affected_assets": ["Commodities", "Luxury", "Semiconductors", "Emerging Markets"],
        "market_view": [
            "China stimulus can support cyclicals, metals, and demand-sensitive exporters.",
            "Weak China data tends to weigh on commodity demand and global industrials.",
        ],
        "second_order_effects": [
            "Demand shifts in metals and energy.",
            "Pressure on companies with China revenue exposure.",
        ],
        "why": "China remains a major demand engine for global cyclicals and commodity-linked assets.",
    },
    {
        "theme": "Shipping And Supply Chains",
        "keywords": ["shipping", "freight", "red sea", "canal", "container", "supply chain", "port"],
        "region": "Global Logistics",
        "urgency": "high",
        "severity": "medium",
        "affected_assets": ["Shipping", "Retail", "Industrials", "Oil"],
        "market_view": [
            "Shipping stress can support freight-sensitive names but pressure importers and retailers.",
            "Extended disruption can reprice inventory and delivery expectations.",
        ],
        "second_order_effects": [
            "Input-cost inflation and inventory delays.",
            "Routing changes that affect energy and goods timing.",
        ],
        "why": "Logistics disruption affects input costs, delivery reliability, and inflation transmission.",
    },
    {
        "theme": "Elections And Policy",
        "keywords": ["election", "vote", "parliament", "congress", "policy", "government", "budget"],
        "region": "Political",
        "urgency": "medium",
        "severity": "medium",
        "affected_assets": ["Rates", "Defense", "Healthcare", "Banks"],
        "market_view": [
            "Policy uncertainty can delay risk-taking and increase sector-specific dispersion.",
            "Election outcomes may reprice regulation, spending, and tax-sensitive groups.",
        ],
        "second_order_effects": [
            "Sector rotation based on expected policy winners and losers.",
            "Budget and fiscal expectations moving rates markets.",
        ],
        "why": "Political transitions shape spending, regulation, taxes, and fiscal expectations.",
    },
]


WATCHLIST_EXPOSURES = {
    "NVDA": {"sensitivity": "High", "themes": ["Trade And Sanctions", "China Growth"], "market_links": ["Semiconductors", "Export Controls", "AI Capex"]},
    "AMD": {"sensitivity": "High", "themes": ["Trade And Sanctions", "China Growth"], "market_links": ["Semiconductors", "PC Demand", "Data Center Spend"]},
    "AAPL": {"sensitivity": "Medium", "themes": ["China Growth", "Trade And Sanctions", "Shipping And Supply Chains"], "market_links": ["Consumer Demand", "Hardware Supply Chain"]},
    "TSLA": {"sensitivity": "High", "themes": ["China Growth", "Energy Shock", "Trade And Sanctions"], "market_links": ["EV Demand", "Battery Inputs", "China Production"]},
    "META": {"sensitivity": "Low", "themes": ["Elections And Policy"], "market_links": ["Advertising", "Platform Regulation"]},
    "AMZN": {"sensitivity": "Medium", "themes": ["Shipping And Supply Chains", "Energy Shock"], "market_links": ["Retail Logistics", "Consumer Margins"]},
    "GOOGL": {"sensitivity": "Low", "themes": ["Elections And Policy"], "market_links": ["Advertising", "Regulation"]},
    "XOM": {"sensitivity": "High", "themes": ["Energy Shock", "War And Security"], "market_links": ["Oil", "Global Supply"]},
    "CVX": {"sensitivity": "High", "themes": ["Energy Shock", "War And Security"], "market_links": ["Oil", "Global Supply"]},
    "LMT": {"sensitivity": "High", "themes": ["War And Security", "Elections And Policy"], "market_links": ["Defense Spending", "Security Risk"]},
}


def _match_theme(text: str) -> dict:
    lowered = text.lower()
    for rule in THEME_RULES:
        if any(keyword in lowered for keyword in rule["keywords"]):
            return rule
    return {
        "theme": "Macro Crosscurrents",
        "region": "Global",
        "urgency": "medium",
        "severity": "medium",
        "affected_assets": ["Equities", "Rates", "USD"],
        "market_view": [
            "The headline may matter through risk sentiment or cross-asset confirmation.",
        ],
        "second_order_effects": [
            "Monitor whether the theme broadens into rates, commodities, or sector leadership.",
        ],
        "why": "Macro headlines matter when they shift the backdrop or confirm an existing risk trend.",
    }


def classify_world_affairs_event(item: dict) -> dict:
    text = f'{item.get("title", "")} {item.get("summary") or ""}'
    rule = _match_theme(text)
    return {
        "title": item["title"],
        "source": item["source"],
        "published_at": item["published_at"],
        "url": item["url"],
        "summary": item.get("summary"),
        "theme": rule["theme"],
        "region": rule["region"],
        "urgency": rule["urgency"],
        "severity": rule["severity"],
        "affected_assets": rule["affected_assets"],
        "market_view": rule["market_view"],
        "second_order_effects": rule["second_order_effects"],
        "why_it_matters": rule["why"],
    }


def build_world_affairs_monitor(limit: int = 8) -> list[dict]:
    items = fetch_market_news(limit=max(limit * 2, 10))
    events = [classify_world_affairs_event(item) for item in items]
    urgency_rank = {"high": 0, "medium": 1, "low": 2}
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    events.sort(
        key=lambda item: (
            severity_rank.get(item["severity"], 3),
            urgency_rank.get(item["urgency"], 3),
            item["published_at"],
        )
    )
    return events[:limit]


def build_world_affairs_briefing(limit: int = 5) -> dict:
    events = build_world_affairs_monitor(limit=limit)
    if not events:
        return {
            "headline": "Global macro monitor",
            "summary": "No major world-affairs events were classified from the current feed set.",
            "key_themes": [],
            "market_implications": [],
            "watchpoints": [],
        }

    lead = events[0]
    themes = []
    implications = []
    watchpoints = []
    seen_implications = set()
    seen_watchpoints = set()

    for event in events:
        if event["theme"] not in themes:
            themes.append(event["theme"])
        for implication in event["market_view"]:
            normalized = implication.strip().lower()
            if normalized not in seen_implications:
                implications.append(implication)
                seen_implications.add(normalized)
                break
        for watchpoint in event["second_order_effects"]:
            normalized = watchpoint.strip().lower()
            if normalized not in seen_watchpoints:
                watchpoints.append(watchpoint)
                seen_watchpoints.add(normalized)
                break

    return {
        "headline": f'{lead["theme"]} leads the global macro tape',
        "summary": lead["why_it_matters"],
        "key_themes": themes[:5],
        "market_implications": implications[:5],
        "watchpoints": watchpoints[:5],
    }


def _timeline_market_reaction(theme: str) -> str:
    mapping = {
        "Central Banks": "Rates, dollar, and long-duration equities tend to move first.",
        "Energy Shock": "Oil, inflation-sensitive assets, and transport margins react quickly.",
        "War And Security": "Defense, havens, and shipping-sensitive assets usually reprice first.",
        "Trade And Sanctions": "Exporters, semis, and globally exposed cyclicals tend to react early.",
        "China Growth": "Commodities, industrials, and China-linked growth names feel it first.",
        "Shipping And Supply Chains": "Retail, freight, and input-cost-sensitive groups absorb it first.",
        "Elections And Policy": "Sector-specific regulation and fiscal expectations drive the first move.",
    }
    return mapping.get(theme, "Cross-asset sentiment and confirmation channels tend to react first.")


def _timeline_follow_through(event: dict) -> str:
    if event["severity"] == "high":
        return "Monitor whether the theme broadens into sector leadership and volatility confirmation."
    if event["urgency"] == "high":
        return "Watch for a second move after the initial headline reaction."
    return "Follow-through matters more than the first headline print."


def build_narrative_timeline(limit: int = 6) -> list[dict]:
    events = build_world_affairs_monitor(limit=max(limit * 2, 10))
    timeline = []
    seen_titles = set()

    for event in events:
        normalized_title = event["title"].strip().lower()
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)
        timeline.append(
            {
                "title": event["title"],
                "theme": event["theme"],
                "region": event["region"],
                "published_at": event["published_at"],
                "event_summary": event.get("summary") or event["why_it_matters"],
                "market_reaction": _timeline_market_reaction(event["theme"]),
                "follow_through": _timeline_follow_through(event),
                "current_implication": event["market_view"][0] if event["market_view"] else event["why_it_matters"],
                "affected_assets": event["affected_assets"][:4],
            }
        )
        if len(timeline) >= limit:
            break

    return timeline


def build_world_affairs_regions(limit: int = 6) -> list[dict]:
    events = build_world_affairs_monitor(limit=max(limit * 2, 8))
    grouped: dict[str, dict] = {}

    for event in events:
        region = event["region"]
        bucket = grouped.setdefault(
            region,
            {
                "region": region,
                "theme_count": 0,
                "active_themes": [],
                "affected_assets": [],
                "headline": event["title"],
            },
        )
        if event["theme"] not in bucket["active_themes"]:
            bucket["active_themes"].append(event["theme"])
            bucket["theme_count"] += 1
        for asset in event["affected_assets"]:
            if asset not in bucket["affected_assets"]:
                bucket["affected_assets"].append(asset)

    summaries = list(grouped.values())
    summaries.sort(key=lambda item: (-item["theme_count"], item["region"]))
    for item in summaries:
        item["active_themes"] = item["active_themes"][:4]
        item["affected_assets"] = item["affected_assets"][:5]
    return summaries[:limit]


def build_watchlist_exposures(user_id: int) -> list[dict]:
    watchlist = load_watchlist(user_id)
    if not watchlist:
        return []

    events = build_world_affairs_monitor(limit=8)
    active_themes = {event["theme"]: event for event in events}
    exposures = []

    for item in watchlist:
        base = WATCHLIST_EXPOSURES.get(
            item["symbol"],
            {
                "sensitivity": "Medium",
                "themes": ["Macro Crosscurrents"],
                "market_links": ["Broad market beta", "Rates sensitivity"],
            },
        )

        active_matches = [theme for theme in base["themes"] if theme in active_themes]
        drivers = [active_themes[theme]["why_it_matters"] for theme in active_matches]
        if not drivers:
            drivers = [f'{item["symbol"]} is mainly exposed to {", ".join(base["market_links"][:2])}.']

        exposures.append(
            {
                "symbol": item["symbol"],
                "label": item["label"],
                "sensitivity": base["sensitivity"],
                "themes": active_matches or base["themes"][:2],
                "drivers": drivers[:3],
                "market_links": base["market_links"][:3],
            }
        )

    return exposures
