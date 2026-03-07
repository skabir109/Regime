from pathlib import Path

import pytest
from sqlmodel import SQLModel, create_engine

from app.services import api_protection as protection


@pytest.fixture(autouse=True)
def reset_limit_state() -> None:
    protection._BURST_WINDOWS.clear()
    protection._REDIS_CLIENT = None


def test_burst_limit_memory_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(protection, "_enforce_burst_limit_redis", lambda *_args, **_kwargs: False)

    protection.enforce_burst_limit(user_id=7, endpoint="ai_analyze", limit_per_minute=2)
    protection.enforce_burst_limit(user_id=7, endpoint="ai_analyze", limit_per_minute=2)

    with pytest.raises(protection.APILimitError):
        protection.enforce_burst_limit(user_id=7, endpoint="ai_analyze", limit_per_minute=2)


def test_daily_limit_increments_and_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "limits.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr(protection, "get_engine", lambda: engine)

    first = protection.enforce_daily_limit(user_id=11, endpoint="ai_analyze", limit_per_day=2)
    second = protection.enforce_daily_limit(user_id=11, endpoint="ai_analyze", limit_per_day=2)

    assert first["used"] == 1
    assert first["remaining"] == 1
    assert second["used"] == 2
    assert second["remaining"] == 0

    with pytest.raises(protection.APILimitError):
        protection.enforce_daily_limit(user_id=11, endpoint="ai_analyze", limit_per_day=2)


def test_rate_limit_backend_status_defaults_to_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(protection, "REDIS_URL", "")
    monkeypatch.setattr(protection, "_REDIS_CLIENT", None)

    status = protection.rate_limit_backend_status()

    assert status["configured"] is False
    assert status["mode"] == "memory"
    assert status["redis_ok"] is False
