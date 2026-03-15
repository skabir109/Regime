from datetime import datetime, timezone

import pandas as pd
import pytest

from app.services import system_status


def test_build_system_status_reports_database_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query):
            return 1

    class DummyEngine:
        def connect(self):
            return DummyConn()

    monkeypatch.setattr(system_status, "get_engine", lambda use_direct=True: DummyEngine())
    monkeypatch.setattr(system_status, "_load_model_artifacts", lambda: (object(), {
        "classes": ["RiskOn", "RiskOff"],
        "features": ["spy_mom_20d", "vix_level"],
        "training": {
            "date_range": {"start": "2020-01-01", "end": "2026-02-27"},
            "metrics": {"accuracy": 0.91},
        },
    }))
    monkeypatch.setattr(system_status, "DATA_PATH", type("PathStub", (), {
        "exists": lambda self: True,
        "stat": lambda self: type("StatStub", (), {"st_mtime": datetime(2026, 3, 10, tzinfo=timezone.utc).timestamp()})(),
    })())
    monkeypatch.setattr(system_status.pd, "read_csv", lambda *args, **kwargs: pd.DataFrame({"SPY": [1.0, 2.0]}, index=pd.to_datetime(["2026-03-11", "2026-03-12"])))
    monkeypatch.setattr(system_status, "build_feature_frame", lambda prices: pd.DataFrame({"spy_mom_20d": [0.02]}, index=pd.to_datetime(["2026-03-12"])))
    monkeypatch.setattr(system_status, "rate_limit_backend_status", lambda: {"configured": False, "mode": "memory", "redis_ok": False})

    status = system_status.build_system_status()

    assert status["database"]["connected"] is True
    assert status["model"]["loaded"] is True
    assert status["model"]["feature_count"] == 2
    assert status["data"]["rows"] == 2
    assert status["data"]["latest_market_data_at"].startswith("2026-03-12")


def test_build_system_status_captures_db_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingEngine:
        def connect(self):
            raise RuntimeError("db down")

    monkeypatch.setattr(system_status, "get_engine", lambda use_direct=True: FailingEngine())
    monkeypatch.setattr(system_status, "_load_model_artifacts", lambda: (object(), {"classes": [], "features": [], "training": {}}))
    monkeypatch.setattr(system_status, "DATA_PATH", type("PathStub", (), {"exists": lambda self: False})())
    monkeypatch.setattr(system_status, "rate_limit_backend_status", lambda: {"configured": False, "mode": "memory", "redis_ok": False})

    status = system_status.build_system_status()

    assert status["database"]["connected"] is False
    assert "db down" in status["database"]["error"]
    assert "Database connectivity check failed." in status["warnings"]
