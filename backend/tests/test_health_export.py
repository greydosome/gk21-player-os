from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from app.main import app
from app.db.session import engine
from app.services.apple_health import read_health
from app.services.health_export import normalize
from tests.test_apple_health import authorize, TOKEN

NOW = datetime.now(ZoneInfo("Asia/Seoul"))
DAY = NOW.date() - timedelta(days=1)
PATH = "/api/integrations/apple-health/export"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def fixture():
    midnight = datetime.combine(DAY, datetime.min.time(), NOW.tzinfo)
    return {"data": {
        "metrics": [{"name": "sleep_analysis", "units": "hr", "data": [
            {"date": midnight.isoformat(), "totalSleep": 4.875,
             "core": 3.0, "rem": 1.0, "deep": 0.875, "inBed": 9.0}]}],
        "workouts": [{"id": "test-cross-midnight", "name": "Running",
                      "start": (midnight - timedelta(minutes=30)).isoformat(),
                      "end": (midnight + timedelta(minutes=30)).isoformat(),
                      "duration": 1800}]
    }}


def test_export_authentication(monkeypatch):
    authorize(monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=fixture()).status_code == 401
    with TestClient(app, base_url="http://testserver") as client:
        assert client.post(PATH, json=fixture(), headers=HEADERS).status_code == 403


def test_export_round_trip_retry_and_midnight(monkeypatch):
    authorize(monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        response = client.post(PATH, json=fixture(), headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["success"] is True
        repeat = client.post(PATH, json=fixture(), headers=HEADERS)
        assert set(repeat.json()["dates"].values()) == {"unchanged"}
    with engine.connect() as conn:
        today = read_health(conn, DAY)["summary"]
        yesterday = read_health(conn, DAY - timedelta(days=1))["summary"]
        assert today["sleep_hours"] == 4.875
        assert today["workouts"] == [{"workout_type": "Running", "minutes": 15}]
        assert yesterday["workouts"] == [{"workout_type": "Running", "minutes": 15}]
        assert "sleep_hours" not in yesterday
        assert conn.execute(text("SELECT COUNT(*) FROM apple_health_workout")).scalar() == 1


def test_batched_workouts_do_not_replace_prior_batch(monkeypatch):
    authorize(monkeypatch)
    first = fixture()
    second = fixture()
    second["data"].pop("metrics")
    second["data"]["workouts"][0].update(id="second", name="Walking")
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=first, headers=HEADERS).status_code == 200
        assert client.post(PATH, json=second, headers=HEADERS).status_code == 200
    with engine.connect() as conn:
        summary = read_health(conn, DAY)["summary"]
        assert summary["sleep_hours"] == 4.875
        assert {w["workout_type"] for w in summary["workouts"]} == {"Running", "Walking"}


def test_ambiguous_sleep_rejected_without_partial_writes(monkeypatch):
    authorize(monkeypatch)
    body = fixture()
    body["data"]["metrics"][0]["data"] *= 2
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 422
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM apple_health_workout")).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM apple_health_daily")).scalar() == 0


def test_raw_sleep_is_not_blindly_summed():
    body = fixture()
    body["data"]["metrics"][0]["data"] = [{"date": NOW.isoformat(), "value": "Core", "qty": 9.0}]
    with pytest.raises(ValueError):
        normalize(body, NOW)


def test_corrected_workout_keeps_id_and_updates_daily_minutes(monkeypatch):
    authorize(monkeypatch)
    body = fixture()
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 200
        body["data"]["workouts"][0]["duration"] = 1200
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 200
    with engine.connect() as conn:
        assert read_health(conn, DAY)["summary"]["workouts"][0]["minutes"] == 10
        assert conn.execute(text("SELECT COUNT(*) FROM apple_health_workout")).scalar() == 1


def test_identical_workout_from_second_export_id_not_double_counted(monkeypatch):
    authorize(monkeypatch)
    body = fixture()
    duplicate = dict(body["data"]["workouts"][0], id="mirrored-id")
    body["data"]["workouts"].append(duplicate)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 200
    with engine.connect() as conn:
        assert read_health(conn, DAY)["summary"]["workouts"] == [{"workout_type": "Running", "minutes": 15}]


def test_zero_sleep_and_empty_export_do_not_clear_known_sleep(monkeypatch):
    authorize(monkeypatch)
    body = fixture()
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 200
        body["data"]["metrics"][0]["data"][0]["totalSleep"] = 0
        body["data"]["workouts"] = []
        assert client.post(PATH, json=body, headers=HEADERS).status_code == 200
    with engine.connect() as conn:
        assert read_health(conn, DAY)["summary"]["sleep_hours"] == 4.875
