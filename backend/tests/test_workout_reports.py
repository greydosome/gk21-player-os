from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.schemas.workout_report import WorkoutReport
from app.services.workout_reports import save_report
from app.services.health_export import save_export
from app.services.health_records import revision, protect_stale_form
from app.schemas.day import DayRecordRequest
from tests.test_health_existing_records import native_tables, NOW, DAY, workout as native_workout, items
from datetime import datetime
from tests.test_apple_health import authorize, TOKEN


@pytest.fixture(autouse=True)
def enable_reports(native_tables, monkeypatch):
    monkeypatch.setattr(settings, 'WORKOUT_CONVERSATION_ENABLED', True)


def report(**changes):
    values = dict(source_message_id='synthetic-message', record_date=DAY, reported_at=NOW,
                  kind='completed', workouts=[dict(category='하체운동',details=['런지'],session_key='strength-1')])
    values.update(changes)
    return WorkoutReport(**values)


def workout(duration=873.84):
    body = native_workout(duration=duration)
    row = body['workouts'][0]
    row['start'] = (datetime.fromisoformat(row['end']) - timedelta(seconds=duration)).isoformat()
    return body


@pytest.mark.parametrize('kind', ['none','question','plan'])
def test_no_completed_conversation_skips_without_touching_watch_record(kind):
    with engine.begin() as conn:
        save_export(conn, workout(), NOW)
        before = items(conn)
        assert save_report(conn, report(kind=kind))['status'] == 'skipped_no_completed_workout'
        assert items(conn) == before
        assert conn.execute(text('SELECT count(*) FROM workout_conversation_report')).scalar() == 0


def test_lunge_refines_existing_watch_time_without_adding_another_workout():
    with engine.begin() as conn:
        save_export(conn, workout(duration=1200), NOW)
        save_report(conn, report())
        assert items(conn) == [{'workout_type':'하체운동','minutes':20,'detail':'런지'}]
        before = revision(conn, DAY)
        save_report(conn, report())
        save_export(conn, workout(duration=1200), NOW + timedelta(seconds=2))
        assert items(conn) == [{'workout_type':'하체운동','minutes':20,'detail':'런지'}]
        assert revision(conn, DAY) == before


def test_report_first_late_watch_replaces_report_time_instead_of_adding():
    with engine.begin() as conn:
        save_report(conn, report(workouts=[dict(category='하체운동',details=['런지'],minutes=15,session_key='strength-1')]))
        assert items(conn)[0]['minutes'] == 15
        save_export(conn, workout(duration=1200), NOW)
        assert items(conn) == [{'workout_type':'하체운동','minutes':20,'detail':'런지'}]


def test_unrecorded_exercise_added_and_unknown_time_is_not_invented():
    with engine.begin() as conn:
        save_report(conn, report(workouts=[dict(category='하체운동',details=['런지'],untracked=True,session_key='off-watch')]))
        assert items(conn) == [{'workout_type':'하체운동','minutes':0,'detail':'런지'}]
        save_report(conn, report(source_message_id='time-correction', reported_at=NOW+timedelta(seconds=1),
            workouts=[dict(category='하체운동',details=['런지'],minutes=12,untracked=True,session_key='off-watch')]))
        assert items(conn)[0]['minutes'] == 12
        save_report(conn, report(source_message_id='time-correction', reported_at=NOW+timedelta(seconds=1),
            workouts=[dict(category='하체운동',details=['런지'],minutes=12,untracked=True,session_key='off-watch')]))
        assert items(conn)[0]['minutes'] == 12


def test_unrecorded_exercise_stays_separate_from_a_different_watch_session():
    with engine.begin() as conn:
        save_export(conn, workout(duration=1200), NOW)
        save_report(conn, report(workouts=[dict(category='코어운동',details=['플랭크'],minutes=5,untracked=True,session_key='off-watch')]))
        assert sorted((x['workout_type'],x['minutes']) for x in items(conn)) == [('근력운동',20),('코어운동',5)]


def test_manual_edits_and_stale_forms_are_protected():
    with engine.begin() as conn:
        save_report(conn, report())
        stale=DayRecordRequest(record_date=DAY,workout_items=[])
        protect_stale_form(conn,stale)
        assert stale.workout_items[0].detail == '런지'
        conn.execute(text('UPDATE workout_item SET minutes=40'))
        save_export(conn, workout(duration=1200), NOW)
        assert items(conn)[0]['minutes'] == 40


def test_multiple_watch_sessions_are_not_guessed():
    with engine.begin() as conn:
        one=workout(); two=workout(); two['workouts'][0]['id']='second'
        # Keep both workouts on the requested local day.
        two['workouts'][0]['start']=one['workouts'][0]['end']
        two['workouts'][0]['end']=(NOW.replace(hour=0,minute=40,second=0)-timedelta(days=1)).isoformat()
        save_export(conn, {'workouts':one['workouts']+two['workouts']}, NOW)
        save_report(conn,report())
        assert all(x['workout_type']!='하체운동' for x in items(conn))


def test_report_api_is_authenticated_and_rejects_invalid_details(monkeypatch):
    authorize(monkeypatch)
    with TestClient(app,base_url='https://testserver') as client:
        body=report().model_dump(mode='json')
        assert client.post('/api/integrations/workout-reports',json=body).status_code==401
        headers={'Authorization':f'Bearer {TOKEN}'}
        assert client.post('/api/integrations/workout-reports',json=body,headers=headers).status_code==200
        body['workouts'][0]['details']=['랫풀다운']
        assert client.post('/api/integrations/workout-reports',json=body,headers=headers).status_code==422
        assert client.get('/api/integrations/workout-reports',params={'record_date':str(DAY)},headers=headers).status_code==200


def test_one_watch_session_with_multiple_muscle_groups_does_not_duplicate_its_minutes():
    with engine.begin() as conn:
        save_export(conn,workout(duration=1200),NOW)
        save_report(conn,report(workouts=[
            dict(category='하체운동',details=['런지'],session_key='strength-1'),
            dict(category='등운동',details=['랫풀다운'],session_key='strength-1')]))
        assert items(conn)==[{'workout_type':'근력운동','minutes':20,'detail':None}]


def test_message_id_conflict_is_rejected_and_http_is_not_accepted(monkeypatch):
    authorize(monkeypatch)
    headers={'Authorization':f'Bearer {TOKEN}'}
    body=report().model_dump(mode='json')
    with TestClient(app,base_url='https://testserver') as client:
        assert client.post('/api/integrations/workout-reports',json=body,headers=headers).status_code==200
        body['workouts'][0]['minutes']=22
        assert client.post('/api/integrations/workout-reports',json=body,headers=headers).status_code==409
    with TestClient(app,base_url='http://testserver') as client:
        assert client.post('/api/integrations/workout-reports',json=body,headers=headers).status_code==403


def test_watch_mapping_uses_explicit_session_when_day_has_multiple_candidates():
    with engine.begin() as conn:
        one=workout(duration=1200); two=workout(duration=1200)
        two['workouts'][0].update(id='second', start=(NOW.replace(hour=1,minute=0,second=0)-timedelta(days=1)).isoformat(),
                                 end=(NOW.replace(hour=1,minute=20,second=0)-timedelta(days=1)).isoformat())
        save_export(conn,{'workouts':one['workouts']+two['workouts']},NOW)
        save_report(conn,report(workouts=[dict(category='하체운동',details=['런지'],watch_external_id='second',session_key='strength-2')]))
        assert sorted((x['workout_type'],x['minutes']) for x in items(conn))==[('근력운동',20),('하체운동',20)]
