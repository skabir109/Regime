from typing import List, Dict

REGIME_PLAYBOOKS = {
    "RiskOn": {
        "title": "Expansionary Strategy",
        "posture": "Aggressive / Trend-Following",
        "actions": [
            "Maintain core exposure to high-beta tech and growth equities.",
            "Utilize dips in SPY/QQQ as liquidity-driven entry points.",
            "Consider rotation into laggard cyclicals if breadth remains positive.",
            "Keep volatility hedges (VIX calls) light but present for tail risk."
        ],
        "asset_allocation": [
            {"asset": "Equities", "weight": "Overweight", "target": "Tech / Semis"},
            {"asset": "Fixed Income", "weight": "Underweight", "target": "Short-Duration"},
            {"asset": "Commodities", "weight": "Neutral", "target": "Copper / Lithium"},
            {"asset": "Safe Havens", "weight": "Underweight", "target": "Gold / USD"}
        ],
        "tactical_watch": "Monitor for divergence in credit spreads or a sharp spike in real yields."
    },
    "RiskOff": {
        "title": "Defensive / Capital Preservation",
        "posture": "Conservative / Risk-Averse",
        "actions": [
            "Reduce total gross exposure and increase cash weightings.",
            "Rotate from cyclical tech into staples, healthcare, and utilities.",
            "Tighten stop-losses on remaining long positions.",
            "Look for 'flight-to-quality' setups in long-dated Treasuries (TLT)."
        ],
        "asset_allocation": [
            {"asset": "Equities", "weight": "Underweight", "target": "Low-Vol / Staples"},
            {"asset": "Fixed Income", "weight": "Overweight", "target": "Long-Duration (TLT)"},
            {"asset": "Commodities", "weight": "Neutral", "target": "Gold / Energy"},
            {"asset": "Safe Havens", "weight": "Overweight", "target": "USD / CHF"}
        ],
        "tactical_watch": "Watch for a VIX 'blow-off' top or a stabilize in corporate bond spreads as signs of a bottom."
    },
    "HighVol": {
        "title": "Volatility / Crisis Management",
        "posture": "Reactive / Neutral",
        "actions": [
            "Prioritize liquidity; avoid illiquid small-caps or complex derivatives.",
            "Active hedging: Long VIX or inverse ETFs (SH/PSQ) to offset beta.",
            "Expect 'gap' moves; reduce position sizing to account for wider ranges.",
            "Wait for a multi-day volatility contraction before re-entering trends."
        ],
        "asset_allocation": [
            {"asset": "Equities", "weight": "Underweight", "target": "Cash"},
            {"asset": "Fixed Income", "weight": "Neutral", "target": "Cash / Short-Bills"},
            {"asset": "Commodities", "weight": "Tactical", "target": "Gold / VIX"},
            {"asset": "Safe Havens", "weight": "Overweight", "target": "Cash / USD"}
        ],
        "tactical_watch": "Focus on the 5-day moving average of VIX; a downward crossover is the first sign of stabilization."
    }
}

def get_playbook_for_regime(regime: str) -> dict:
    return REGIME_PLAYBOOKS.get(regime, REGIME_PLAYBOOKS["RiskOff"])
