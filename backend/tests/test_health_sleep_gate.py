from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.db.session import engine
from app.services.apple_health import read_health, health_context
from tests.test_apple_health import authorize, payload, TOKEN, DAY
from tests.test_health_export import fixture

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_workout_only_mode_hides_legacy_sleep_from_app_and_coaching(monkeypatch):
    authorize(monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post('/api/integrations/apple-health/daily', json=payload(), headers=HEADERS).status_code == 200
    monkeypatch.setattr(settings, 'APPLE_HEALTH_SLEEP_ENABLED', False)
    monkeypatch.setattr(settings, 'APPLE_HEALTH_COACHING_ENABLED', True)
    with engine.connect() as conn:
        result = read_health(conn, DAY)
        assert result['summary'] == {'workouts': [{'workout_type': '걷기', 'minutes': 30}]}
        assert 'sleep_hours' not in result['metric_collected_at']
        assert 'content_hash' not in result
        assert all('sleep_hours' not in row['summary'] for row in health_context(conn, DAY)['days'])
        # The hidden source remains recoverable, not overwritten/deleted.
        assert conn.execute(text('SELECT summary FROM apple_health_daily')).scalar()['sleep_hours'] == 7.25


def test_sleep_gate_rejects_both_upload_formats_without_partial_workouts(monkeypatch):
    authorize(monkeypatch)
    monkeypatch.setattr(settings, 'APPLE_HEALTH_SLEEP_ENABLED', False)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post('/api/integrations/apple-health/daily', json=payload(), headers=HEADERS).status_code == 422
        assert client.post('/api/integrations/apple-health/export', json=fixture(), headers=HEADERS).status_code == 422
    with engine.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM apple_health_daily')).scalar() == 0
        assert conn.execute(text('SELECT COUNT(*) FROM apple_health_workout')).scalar() == 0


def test_workout_only_export_is_authenticated_retry_safe_and_visible(monkeypatch):
    authorize(monkeypatch)
    monkeypatch.setattr(settings, 'APPLE_HEALTH_SLEEP_ENABLED', False)
    body = fixture(); body['data'].pop('metrics')
    with TestClient(app, base_url="https://testserver") as client:
        assert client.post('/api/integrations/apple-health/export', json=body).status_code == 401
        assert client.post('/api/integrations/apple-health/export', json=body, headers=HEADERS).status_code == 200
        assert set(client.post('/api/integrations/apple-health/export', json=body, headers=HEADERS).json()['dates'].values()) == {'unchanged'}
    with engine.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM apple_health_workout')).scalar() == 1
        for summary in conn.execute(text('SELECT record_date FROM apple_health_daily')).scalars():
            assert 'workouts' in read_health(conn, summary)['summary']
            assert 'sleep_hours' not in read_health(conn, summary)['summary']
