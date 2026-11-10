"""Merge health imports into the existing diary, with retry and manual-edit protection."""
import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text
from app.core.config import settings

KOREA = ZoneInfo('Asia/Seoul')
NAMES = {'Soccer': '풋살', 'Cycling': '자전거', 'Indoor Cycling': '자전거',
         'Walking': '걷기', 'Running': '달리기', 'Stair Climbing': '계단 오르기',
         'Traditional Strength Training': '근력운동', 'Functional Strength Training': '근력운동'}
CALORIES = {'풋살': 8, '자전거': 7, '걷기': 4, '달리기': 8, '계단 오르기': 10,
            '등운동': 6, '근력운동': 6, '하체운동': 7, '가슴운동': 6,
            '팔운동': 5, '어깨운동': 5, '코어운동': 5, '하체모빌리티': 3,
            '클럽벨': 5, '인클라인 워킹': 200 / 30, '스텝퍼': 6}


def rounded(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def raw_workouts(conn, day):
    """One whole session belongs to its local finish date; never split its minutes."""
    begin = datetime.combine(day, datetime.min.time(), KOREA)
    rows = conn.execute(text('''SELECT * FROM apple_health_workout
        WHERE ended_at >= :begin AND ended_at < :finish ORDER BY started_at, external_id'''),
        {'begin': begin, 'finish': begin + timedelta(days=1)}).mappings().all()
    rows = [dict(row) for row in rows]
    unique_rows = {}
    for row in rows:
        identity = (row['workout_type'], row['started_at'], row['ended_at'], row['duration_seconds'])
        unique_rows.setdefault(identity, row)
    rows = list(unique_rows.values())
    from app.services.workout_reports import project_reports
    rows, extras, _ = project_reports(conn, day, rows)
    result, seen = {}, set()
    for row in rows:
        identity = (row['workout_type'], row['started_at'], row['ended_at'], row['duration_seconds'])
        if identity in seen:
            continue
        seen.add(identity)
        name = row['record_workout_type'] or NAMES.get(row['workout_type'])
        if not name:  # An unspecified "Other" workout does not identify a diary exercise.
            continue
        value = result.setdefault(name, {'minutes': 0.0, 'details': []})
        value['minutes'] += float(row['duration_seconds']) / 60
        for detail in (row['record_detail'] or '').split(', '):
            if detail and detail not in value['details']:
                value['details'].append(detail)
    for extra in extras:
        value = result.setdefault(extra['category'], {'minutes': 0.0, 'details': []})
        value['minutes'] += extra['minutes'] or 0
        value['details'] = list(dict.fromkeys(value['details'] + extra['details']))
    return {name: {'workout_type': name, 'minutes': max(1 if value['minutes'] > 0 else 0, rounded(value['minutes'])),
                   'detail': ', '.join(value['details']) or None,
                   'calorie_estimate': rounded(max(1 if value['minutes'] > 0 else 0, rounded(value['minutes'])) * CALORIES.get(name, 6))}
            for name, value in result.items()}


def revision(conn, day):
    if not settings.APPLE_HEALTH_RECORD_SYNC_ENABLED:
        return None
    return conn.execute(text('SELECT revision FROM apple_health_record_sync WHERE record_date=:day'),
                        {'day': day}).scalar()


def sync_record(conn, day, *, sleep_hours=None, workouts=None):
    if not settings.APPLE_HEALTH_RECORD_SYNC_ENABLED:
        return
    conn.execute(text('SELECT pg_advisory_xact_lock(2101, :day)'), {'day': day.toordinal()})
    old = conn.execute(text('SELECT * FROM apple_health_record_sync WHERE record_date=:day FOR UPDATE'),
                       {'day': day}).mappings().first()
    if sleep_hours is None and not workouts and not old:
        return
    day_id = conn.execute(text('''INSERT INTO day_record(record_date) VALUES (:day)
        ON CONFLICT(record_date) DO UPDATE SET record_date=EXCLUDED.record_date RETURNING day_record_id'''),
        {'day': day}).scalar_one()
    before = dict(old['state']) if old else {}
    state = json.loads(json.dumps(before))
    if sleep_hours is not None:
        current = conn.execute(text('SELECT sleep_hours FROM sleep_record WHERE day_record_id=:id FOR UPDATE'),
                               {'id': day_id}).scalar()
        may_update = (('sleep' not in before and current in (None, 0)) or
                      ('sleep' in before and before['sleep'] is not None and current == before['sleep']))
        if may_update:
            value = rounded(sleep_hours)
            conn.execute(text('''INSERT INTO sleep_record(day_record_id,sleep_hours) VALUES (:id,:value)
                ON CONFLICT(day_record_id) DO UPDATE SET sleep_hours=EXCLUDED.sleep_hours,updated_at=now()'''),
                {'id': day_id, 'value': value})
            state['sleep'] = value
        else:
            state['sleep'] = None  # A manual edit wins over a later automatic retry.
    if workouts is not None:
        previous = before.get('workouts', {})
        current = {r['workout_type']: dict(r) for r in conn.execute(text('''SELECT workout_type, minutes,
            calorie_estimate,detail FROM workout_item WHERE day_record_id=:id ORDER BY workout_item_id'''),
            {'id': day_id}).mappings()}
        managed = dict(previous)
        for name in set(previous) | set(workouts):
            existing, desired = current.get(name), workouts.get(name)
            can_write = (name not in previous and existing is None) or (
                name in previous and previous[name] is not None and existing == previous[name])
            if can_write:
                if existing == desired:
                    if desired:
                        managed[name] = desired
                    else:
                        managed.pop(name, None)
                    continue
                conn.execute(text('DELETE FROM workout_item WHERE day_record_id=:id AND workout_type=:name'),
                             {'id': day_id, 'name': name})
                if desired:
                    conn.execute(text('''INSERT INTO workout_item(day_record_id,workout_type,minutes,calorie_estimate,detail)
                        VALUES (:id,:workout_type,:minutes,:calorie_estimate,:detail)'''), {'id': day_id, **desired})
                    managed[name] = desired
                else:
                    managed.pop(name, None)
            else:
                # Do not add imported minutes on top of an already-entered exercise.
                # Explicitly confirmed exercise details can still check existing boxes.
                if name not in previous and existing and desired and desired['detail']:
                    details = list(dict.fromkeys(filter(None, (existing['detail'] or '').split(', ') + desired['detail'].split(', '))))
                    conn.execute(text('UPDATE workout_item SET detail=:detail WHERE day_record_id=:id AND workout_type=:name'),
                                 {'id': day_id, 'name': name, 'detail': ', '.join(details)})
                managed[name] = None
        state['workouts'] = managed
        names = conn.execute(text('SELECT workout_type FROM workout_item WHERE day_record_id=:id ORDER BY workout_item_id'),
                             {'id': day_id}).scalars().all()
        if names:
            conn.execute(text('''INSERT INTO workout_record(day_record_id,completed_workout,workout_done_yn)
                VALUES (:id,:names,true) ON CONFLICT(day_record_id) DO UPDATE
                SET completed_workout=EXCLUDED.completed_workout,workout_done_yn=true,updated_at=now()'''),
                {'id': day_id, 'names': ', '.join(names)})
    if not old or state != before:
        conn.execute(text('''INSERT INTO apple_health_record_sync(record_date,state,revision)
            VALUES (:day,CAST(:state AS jsonb),:revision) ON CONFLICT(record_date) DO UPDATE
            SET state=EXCLUDED.state,revision=EXCLUDED.revision'''),
            {'day': day, 'state': json.dumps(state), 'revision': str(uuid4())})


def protect_stale_form(conn, req):
    """An open form from before an import must not autosave stale values over it."""
    current_revision = revision(conn, req.record_date)
    if not current_revision or req.health_record_revision == current_revision:
        return
    from app.schemas.day import SleepRecord, WorkoutItem, WorkoutRecord
    row = conn.execute(text('SELECT state FROM apple_health_record_sync WHERE record_date=:day'),
                       {'day': req.record_date}).scalar_one()
    day_id = conn.execute(text('SELECT day_record_id FROM day_record WHERE record_date=:day'),
                          {'day': req.record_date}).scalar_one()
    applied = {'workout_types': list(row.get('workouts', {})), 'workout_items': []}
    if 'sleep' in row:
        value = conn.execute(text('SELECT sleep_hours FROM sleep_record WHERE day_record_id=:id'), {'id': day_id}).scalar()
        if value is not None:
            req.sleep = req.sleep or SleepRecord()
            req.sleep.sleep_hours = float(value)
            applied['sleep_hours'] = float(value)
    types = set(applied['workout_types'])
    canonical = [dict(r) for r in conn.execute(text('''SELECT workout_type,minutes,calorie_estimate,detail
        FROM workout_item WHERE day_record_id=:id'''), {'id': day_id}).mappings() if r['workout_type'] in types]
    req.workout_items = [item for item in req.workout_items if item.workout_type not in types] + [WorkoutItem(**r) for r in canonical]
    if canonical:
        req.workout = req.workout or WorkoutRecord()
        req.workout.workout_done_yn = True
        req.workout.completed_workout = ', '.join(item.workout_type for item in req.workout_items)
    applied['workout_items'] = canonical
    req.health_record_revision = current_revision
    req._health_merge = applied
