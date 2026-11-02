import base64
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.schemas.apple_health import AppleHealthRequest
from app.services.apple_health import save_health, read_health

NOW = datetime.now(ZoneInfo("Asia/Seoul"))
DAY = NOW.date()
PASSWORD = "test-only-owner-password-with-high-entropy-placeholder"
TOKEN = "test-only-separate-upload-token"


def payload(**overrides):
    return {"record_date": str(DAY), "collected_at": NOW.isoformat(), "summary": {"sleep_hours": 7.25, "workouts": [{"workout_type": "걷기", "minutes": 30}]}, **overrides}


def authorize(monkeypatch):
    for key, value in {"APP_AUTH_ENABLED": True, "APPLE_HEALTH_ENABLED": True, "APP_AUTH_PASSWORD_SHA256": hashlib.sha256(PASSWORD.encode()).hexdigest(), "APPLE_HEALTH_TOKEN_SHA256": hashlib.sha256(TOKEN.encode()).hexdigest()}.items():
        monkeypatch.setattr(settings, key, value)


def test_disabled_and_fail_closed(monkeypatch):
    with TestClient(app) as client:
        assert client.post("/api/integrations/apple-health/daily", json=payload()).status_code == 404
        monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
        assert client.get("/api/dashboard").status_code == 503


def test_auth_scope_tls_size_and_validation(monkeypatch):
    authorize(monkeypatch)
    bearer = {"Authorization": f"Bearer {TOKEN}"}
    basic = {"Authorization": "Basic " + base64.b64encode(f"{settings.APP_AUTH_USER}:{PASSWORD}".encode()).decode()}
    path = "/api/integrations/apple-health/daily"
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(path, json=payload()).status_code == 401
        assert client.post(path, json=payload(), headers=basic).status_code == 401
        assert client.get("/api/dashboard", headers=bearer).status_code == 401
        assert client.get("/openapi.json").status_code == 401
        assert client.get("/openapi.json", headers=basic).status_code == 200
        response = client.post(path, json=payload(), headers=bearer)
        assert response.status_code == 200 and response.json()["status"] == "created"
        assert response.headers["cache-control"] == "no-store"
        assert client.post(path, content="x" * 32769, headers={**bearer, "Content-Type": "application/json"}).status_code == 413
        assert client.post(path, json=payload(summary={"sleep_hours": -1}), headers=bearer).status_code == 422
        assert client.post(path, json=payload(), headers={**bearer, "Origin": "https://attacker.invalid"}).status_code == 403
    with TestClient(app, base_url="http://testserver") as client:
        assert client.post(path, json=payload(), headers=bearer).status_code == 403
        # Client-supplied headers alone do not bypass trusted proxy processing.
        assert client.post(path, json=payload(), headers={**bearer, "X-Forwarded-Proto": "https"}).status_code == 403


def test_preserves_manual_duplicate_missing_and_stale(monkeypatch):
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO day_record(record_date,memo,is_injured) VALUES (:d,'manual',true)"), {"d": DAY})
        assert save_health(conn, AppleHealthRequest(**payload())) == "created"
        assert save_health(conn, AppleHealthRequest(**payload())) == "ignored_older_or_duplicate"
        assert save_health(conn, AppleHealthRequest(**payload(collected_at=(NOW-timedelta(minutes=1)).isoformat(), summary={"sleep_hours": 1}))) == "ignored_older_or_duplicate"
        save_health(conn, AppleHealthRequest(**payload(collected_at=(NOW+timedelta(minutes=1)).isoformat(), summary={"sleep_hours": None, "workouts": []})))
        record = read_health(conn, DAY)
        assert record["summary"]["sleep_hours"] == 7.25
        assert record["summary"]["workouts"] == []
        assert record["metric_collected_at"]["sleep_hours"] == NOW.isoformat()
        assert conn.execute(text("SELECT memo,is_injured FROM day_record")).one() == ("manual", True)
        assert conn.execute(text("SELECT COUNT(*) FROM apple_health_daily")).scalar() == 1
        assert read_health(conn, DAY-timedelta(days=1))["status"] == "missing"


@pytest.mark.parametrize("summary", [{"sleep_hours": 25}, {"sleep_hours": float("nan")}, {"weight_kg": 70}, {"gps": "private"}, {"workouts": [{"workout_type": "x", "minutes": 0}]}])
def test_invalid_metrics(summary):
    with pytest.raises(ValidationError):
        AppleHealthRequest(**payload(summary=summary))


def test_future_date_rejected():
    with pytest.raises(ValidationError):
        AppleHealthRequest(**payload(record_date=str(DAY+timedelta(days=1))))


def test_transaction_rollback():
    with pytest.raises(RuntimeError):
        with engine.begin() as conn:
            save_health(conn, AppleHealthRequest(**payload()))
            raise RuntimeError("rollback")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM day_record")).scalar() == 0


def test_coach_dedup_retry_and_superseded(monkeypatch):
    from app.services import health_coaching as coach
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    monkeypatch.setattr(settings, "APPLE_HEALTH_COACHING_ENABLED", True)
    with engine.begin() as conn:
        save_health(conn, AppleHealthRequest(**payload()))
    version = ["v1"]
    monkeypatch.setattr(coach, "prepare", lambda conn, day: ({}, {}, "prompt", version[0]))
    monkeypatch.setattr(coach, "build_daily_rule_analysis", lambda *a: {})
    for name in ["save_ai_analysis", "mark_ai_analysis_running", "mark_ai_analysis_failed", "update_ai_analysis_from_llm"]:
        monkeypatch.setattr(coach, name, lambda *a: None)
    calls = []
    monkeypatch.setattr(coach, "call_ai", lambda prompt: calls.append(prompt) or {})
    assert coach.run_health_coaching(DAY) == "completed"
    assert coach.run_health_coaching(DAY) == "unchanged"
    assert len(calls) == 1
    version[0] = "v2"
    def fail(prompt):
        raise RuntimeError("sensitive body must not be persisted")
    monkeypatch.setattr(coach, "call_ai", fail)
    assert coach.run_health_coaching(DAY) == "failed"
    with engine.connect() as conn:
        assert conn.execute(text("SELECT error_code FROM apple_health_coaching_run")).scalar() == "COACHING_FAILED"
    def concurrent_update(prompt):
        version[0] = "v3"
        return {}
    monkeypatch.setattr(coach, "call_ai", concurrent_update)
    assert coach.run_health_coaching(DAY) == "superseded"
    monkeypatch.setattr(coach, "call_ai", lambda prompt: {})
    assert coach.run_health_coaching(DAY) == "completed"
    version[0] = "v4"
    monkeypatch.setattr(coach, "call_ai", fail)
    for _ in range(3):
        assert coach.run_health_coaching(DAY) == "failed"
    assert coach.run_health_coaching(DAY) == "retry_limit"
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(2102,:day)"), {"day": DAY.toordinal()})
        assert coach.run_health_coaching(DAY) == "busy"
        conn.execute(text("SELECT pg_advisory_unlock(2102,:day)"), {"day": DAY.toordinal()})


def test_metrics_history_contract():
    from app.ai.metrics import calculate_ai_metrics
    rows = [{"sleep_hours": 7, "workout_done_yn": True}, {"sleep_hours": 8, "workout_done_yn": False}]
    result = calculate_ai_metrics({"recent_7_days": rows, "recent_30_days": rows})
    assert result["avg_sleep_hours_7"] == 7.5
    assert result["workout_days_7"] == 1


def test_coach_persists_existing_output_contract(monkeypatch):
    from app.services import health_coaching as coach
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    monkeypatch.setattr(settings, "APPLE_HEALTH_COACHING_ENABLED", True)
    with engine.begin() as conn:
        save_health(conn, AppleHealthRequest(**payload()))
    monkeypatch.setattr(coach, "get_ai_context", lambda day, conn=None: {"target_date": str(day), "today": {"record_date": day}, "apple_health": {"days": [{"summary": {"sleep_hours": 7.25}}]}})
    monkeypatch.setattr(coach, "call_ai", lambda prompt: {"provider": "TEST", "model_name": "fake", "prompt_version": "test", "analysis": {"summary": "자동 코칭", "workout_comment": "가볍게 걷기", "meal_comment": "기존 식단 참고", "coach_card": "오늘의 코칭"}})
    assert coach.run_health_coaching(DAY) == "completed"
    from app.crud.ai_analysis import get_daily_ai_analysis
    result = get_daily_ai_analysis(DAY)
    assert result["overview"]["status"] == "COMPLETED"
    assert result["cards"]["coach"] == "오늘의 코칭"
    with engine.begin() as conn:
        save_health(conn, AppleHealthRequest(**payload(collected_at=(NOW+timedelta(minutes=1)).isoformat(), summary={"sleep_hours": 8})))
        assert conn.execute(text("SELECT status FROM apple_health_coaching_run")).scalar() == "superseded"
        assert conn.execute(text("SELECT ai_status FROM ai_analysis")).scalar() == "RULE_DONE"


def test_token_revocation_and_unicode_basic(monkeypatch):
    authorize(monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        malformed = "Basic " + base64.b64encode("사용자:wrong".encode()).decode()
        assert client.get("/openapi.json", headers={"Authorization": malformed}).status_code == 401
        monkeypatch.setattr(settings, "APPLE_HEALTH_TOKEN_SHA256", hashlib.sha256(b"rotated").hexdigest())
        assert client.post("/api/integrations/apple-health/daily", json=payload(), headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 401


def test_stale_status_and_collection_only(monkeypatch):
    from app.services.apple_health import health_context
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    previous_day = DAY - timedelta(days=2)
    with engine.begin() as conn:
        save_health(conn, AppleHealthRequest(**payload(record_date=str(previous_day), collected_at=(NOW-timedelta(days=2)).isoformat())))
        assert read_health(conn, previous_day)["status"] == "stale"
        assert health_context(conn, DAY) == {}
        monkeypatch.setattr(settings, "APPLE_HEALTH_COACHING_ENABLED", True)
        assert len(health_context(conn, DAY)["days"]) == 1
        monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", False)
        assert read_health(conn, DAY) == {"enabled": False}
        assert health_context(conn, DAY) == {}
