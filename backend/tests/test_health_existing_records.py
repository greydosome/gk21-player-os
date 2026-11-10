from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.apple_health import AppleHealthRequest
from app.schemas.day import DayRecordRequest
from app.services.apple_health import save_health
from app.services.health_export import save_export
from app.services.health_records import raw_workouts, sync_record, protect_stale_form, revision

NOW = datetime.now(ZoneInfo('Asia/Seoul'))
DAY = NOW.date() - timedelta(days=1)


@pytest.fixture(autouse=True)
def native_tables(monkeypatch):
    monkeypatch.setattr(settings, 'APPLE_HEALTH_ENABLED', True)
    monkeypatch.setattr(settings, 'APPLE_HEALTH_RECORD_SYNC_ENABLED', True)
    monkeypatch.setattr(settings, 'APPLE_HEALTH_SLEEP_ENABLED', True)
    with engine.begin() as conn:
        conn.exec_driver_sql('''CREATE TABLE IF NOT EXISTS sleep_record(
            day_record_id BIGINT UNIQUE REFERENCES day_record(day_record_id) ON DELETE CASCADE,
            sleep_hours NUMERIC,updated_at TIMESTAMPTZ DEFAULT now())''')
        conn.exec_driver_sql('''CREATE TABLE IF NOT EXISTS workout_item(
            workout_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            day_record_id BIGINT REFERENCES day_record(day_record_id) ON DELETE CASCADE,
            workout_type TEXT,minutes SMALLINT,calorie_estimate SMALLINT,detail TEXT)''')
        conn.exec_driver_sql('''CREATE TABLE IF NOT EXISTS workout_record(
            day_record_id BIGINT UNIQUE REFERENCES day_record(day_record_id) ON DELETE CASCADE,
            completed_workout TEXT,workout_done_yn BOOLEAN,updated_at TIMESTAMPTZ DEFAULT now())''')
        migration = (Path(__file__).parents[2] / 'sql/migrations/2026-11-10_health_existing_records.sql').read_text()
        conn.exec_driver_sql(migration.replace('BEGIN;', '').replace('COMMIT;', ''))


def workout(name='Traditional Strength Training', duration=873.84):
    midnight = datetime.combine(DAY, datetime.min.time(), NOW.tzinfo)
    return {'workouts': [{'id': 'cross-midnight', 'name': name,
        'start': (midnight - timedelta(seconds=51)).isoformat(),
        'end': (midnight + timedelta(seconds=823)).isoformat(), 'duration': duration}]}


def items(conn):
    return [dict(r) for r in conn.execute(text('SELECT workout_type,minutes,detail FROM workout_item ORDER BY workout_item_id')).mappings()]


def test_confirmed_back_session_is_fifteen_minutes_on_finish_date_and_retry_safe():
    with engine.begin() as conn:
        save_export(conn, workout(), NOW)
        conn.execute(text("UPDATE apple_health_workout SET record_workout_type='등운동', record_detail='랫풀다운'"))
        save_export(conn, workout(), NOW + timedelta(seconds=1))
        expected = [{'workout_type': '등운동', 'minutes': 15, 'detail': '랫풀다운'}]
        assert items(conn) == expected
        assert conn.execute(text('SELECT d.record_date FROM workout_item w JOIN day_record d USING(day_record_id)')).scalar() == DAY
        identity = conn.execute(text('SELECT workout_item_id FROM workout_item')).scalar()
        save_export(conn, workout(), NOW + timedelta(seconds=2))
        assert items(conn) == expected
        assert conn.execute(text('SELECT workout_item_id FROM workout_item')).scalar() == identity
        assert conn.execute(text('SELECT workout_done_yn FROM workout_record')).scalar() is True


def test_manual_exercises_are_not_added_twice_or_overwritten():
    with engine.begin() as conn:
        day_id = conn.execute(text('INSERT INTO day_record(record_date) VALUES (:d) RETURNING day_record_id'), {'d': DAY}).scalar()
        conn.execute(text("INSERT INTO workout_item(day_record_id,workout_type,minutes,detail) VALUES (:id,'풋살',60,NULL),(:id,'팔운동',15,'덤벨컬')"), {'id': day_id})
        body = workout('Soccer')
        save_export(conn, body, NOW)
        save_export(conn, body, NOW + timedelta(seconds=1))
        assert items(conn) == [{'workout_type': '풋살', 'minutes': 60, 'detail': None},
                               {'workout_type': '팔운동', 'minutes': 15, 'detail': '덤벨컬'}]


def test_user_edit_or_delete_of_import_is_respected():
    with engine.begin() as conn:
        body = workout('Soccer')
        save_export(conn, body, NOW)
        conn.execute(text('UPDATE workout_item SET minutes=40'))
        save_export(conn, body, NOW + timedelta(seconds=1))
        assert items(conn)[0]['minutes'] == 40
        conn.execute(text('DELETE FROM workout_item'))
        save_export(conn, body, NOW + timedelta(seconds=2))
        assert items(conn) == []


@pytest.mark.parametrize(('hours','expected'), [(4 + 53/60,5), (3 + 13/60,3), (6.5,7)])
def test_sleep_rounds_to_existing_whole_hour_input_without_copying_other_fields(hours, expected):
    with engine.begin() as conn:
        save_health(conn, AppleHealthRequest(record_date=DAY, collected_at=NOW, summary={'sleep_hours': hours}))
        assert conn.execute(text('SELECT sleep_hours FROM sleep_record')).scalar() == expected
        conn.execute(text('UPDATE sleep_record SET sleep_hours=8'))
        save_health(conn, AppleHealthRequest(record_date=DAY, collected_at=NOW + timedelta(seconds=1), summary={'sleep_hours': hours}))
        assert conn.execute(text('SELECT sleep_hours FROM sleep_record')).scalar() == 8


def test_stale_open_form_cannot_erase_new_import_but_current_revision_can_edit():
    with engine.begin() as conn:
        save_export(conn, workout('Soccer'), NOW)
        save_health(conn, AppleHealthRequest(record_date=DAY, collected_at=NOW + timedelta(seconds=1), summary={'sleep_hours': 6.5}))
        stale = DayRecordRequest(record_date=DAY, sleep={'sleep_hours': 0}, workout_items=[])
        protect_stale_form(conn, stale)
        assert stale.sleep.sleep_hours == 7
        assert [(x.workout_type, x.minutes) for x in stale.workout_items] == [('풋살',15)]
        assert stale.workout.workout_done_yn is True
        assert stale._health_merge is not None
        edited = DayRecordRequest(record_date=DAY, health_record_revision=revision(conn, DAY),
                                  sleep={'sleep_hours': 5}, workout_items=[])
        protect_stale_form(conn, edited)
        assert edited.sleep.sleep_hours == 5 and edited.workout_items == []


def test_distinct_ids_for_same_source_session_do_not_double_native_minutes():
    with engine.begin() as conn:
        body = workout('Soccer')
        body['workouts'].append({**body['workouts'][0], 'id': 'same-interval-other-id'})
        save_export(conn, body, NOW)
        assert items(conn) == [{'workout_type': '풋살','minutes':15,'detail':None}]
