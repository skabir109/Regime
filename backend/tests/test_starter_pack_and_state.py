from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlmodel import SQLModel, Session, create_engine

from app.schemas import User
from app.services import starter_pack, state, watchlist


@pytest.fixture
def starter_pack_engine(tmp_path: Path):
    db_path = tmp_path / "starter_pack.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def test_apply_starter_pack_seeds_default_watchlist(
    monkeypatch: pytest.MonkeyPatch,
    starter_pack_engine,
) -> None:
    monkeypatch.setattr(starter_pack, "get_engine", lambda: starter_pack_engine)
    monkeypatch.setattr(watchlist, "get_engine", lambda: starter_pack_engine)

    with Session(starter_pack_engine) as session:
        user = User(
            email="starter@example.com",
            name="Starter User",
            password_hash="hash",
            tier="free",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = int(user.id)

    result = starter_pack.apply_starter_pack(user_id, only_if_empty=True)

    assert result["already_seeded"] is False
    assert result["applied_symbols"] == ["SPY", "QQQ", "GLD", "TLT", "XLE"]
    assert [item["symbol"] for item in result["watchlist"]] == ["XLE", "TLT", "GLD", "QQQ", "SPY"]


def test_build_market_state_summary_includes_scorecard(monkeypatch: pytest.MonkeyPatch) -> None:
    feature_frame = pd.DataFrame(
        [
            {
                "spy_mom_20d": 0.03,
                "spy_mom_5d": 0.01,
                "spy_vol_20d": 0.015,
                "vix_level": 16.0,
                "gld_mom_20d": 0.02,
                "uso_mom_20d": 0.01,
                "gbp_mom_20d": 0.02,
            },
            {
                "spy_mom_20d": 0.05,
                "spy_mom_5d": 0.02,
                "spy_vol_20d": 0.014,
                "vix_level": 15.0,
                "gld_mom_20d": 0.03,
                "uso_mom_20d": 0.02,
                "gbp_mom_20d": 0.01,
            },
        ]
    )

    monkeypatch.setattr(state, "load_prices", lambda: pd.DataFrame({"SPY": [1, 2]}))
    monkeypatch.setattr(state, "build_feature_frame", lambda _prices: feature_frame)
    monkeypatch.setattr(
        state,
        "compute_market_panels",
        lambda: [
            {"symbol": "SPY", "signal": "Bullish"},
            {"symbol": "GLD", "signal": "Calm"},
            {"symbol": "TLT", "signal": "Bullish"},
        ],
    )
    monkeypatch.setattr(
        state,
        "compute_market_snapshot",
        lambda: [
            {"symbol": "SPY", "label": "S&P 500", "change_1d": 0.01},
            {"symbol": "GLD", "label": "Gold", "change_1d": -0.01},
            {"symbol": "TLT", "label": "Treasury Bonds", "change_1d": 0.02},
        ],
    )
    monkeypatch.setattr(
        state,
        "fetch_sector_breadth",
        lambda limit=8: [
            {"symbol": "XLK", "label": "Technology", "signal": "Leading", "change_1d": 0.02},
            {"symbol": "XLU", "label": "Utilities", "signal": "Lagging", "change_1d": -0.01},
        ],
    )
    monkeypatch.setattr(state, "fetch_market_news", lambda limit=6: [{"title": "Risk appetite improves", "tags": ["Growth"]}])
    monkeypatch.setattr(state, "_refresh_executive_summary_async", lambda *args, **kwargs: None)
    state._SUMMARY_CACHE["text"] = ""
    state._SUMMARY_CACHE["timestamp"] = 0.0

    class ModelStub:
        def predict_proba(self, _ordered):
            return np.array([[0.8, 0.2]])

    prediction = type("Prediction", (), {"regime": "RiskOn", "confidence": 0.82})()
    meta = {"features": list(feature_frame.columns), "classes": ["RiskOn", "RiskOff"]}

    summary = state.build_market_state_summary(ModelStub(), meta, prediction=prediction)

    assert summary["scorecard"]["conviction"] == "High conviction"
    assert len(summary["scorecard"]["metrics"]) == 4
    assert summary["scorecard"]["metrics"][0]["label"] == "SPY 20D Momentum"
    assert summary["scorecard"]["caution_flag"]
