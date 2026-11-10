"""Completion-only conversation overlays on Watch sessions and existing diary items."""
import json

from sqlalchemy import text

from app.core.config import settings

STRENGTH = {'근력운동', '하체운동', '등운동', '가슴운동', '팔운동', '어깨운동', '코어운동'}


def project_reports(conn, day, rows):
    if not settings.WORKOUT_CONVERSATION_ENABLED:
        return rows, [], {}
    from app.services.health_records import NAMES
    reports = conn.execute(text('''SELECT source_message_id,payload FROM workout_conversation_report
        WHERE record_date=:day ORDER BY reported_at,source_message_id'''), {'day': day}).mappings()
    grouped = {}
    for report in reports:
        for entry in report['payload']['workouts']:
            key = (entry['session_key'], entry['category'])
            value = grouped.setdefault(key, {**entry, 'details': [], 'messages': []})
            value['details'] = list(dict.fromkeys(value['details'] + entry['details']))
            value['messages'].append(report['source_message_id'])
            for field in ('minutes', 'watch_external_id'):
                if entry.get(field) is not None:
                    value[field] = entry[field]
            value['untracked'] = entry['untracked']
    proposals, extras, statuses = {}, [], {}
    for entry in grouped.values():
        category = entry['category']
        if entry['untracked']:
            candidates = []
        elif entry.get('watch_external_id'):
            candidates = [r for r in rows if r['external_id'] == entry['watch_external_id']]
            if not candidates:
                for message in entry['messages']:
                    statuses[message] = 'pending_watch'
                continue
        else:
            candidates = [r for r in rows if
                (r['record_workout_type'] == category) or
                (r['record_workout_type'] is None and
                 (NAMES.get(r['workout_type']) == category or
                  (category in STRENGTH and NAMES.get(r['workout_type']) == '근력운동')))]
        if len(candidates) > 1:
            status = 'pending_session_match'
        elif candidates:
            proposals.setdefault(candidates[0]['external_id'], []).append(entry)
            continue
        else:
            extras.append(entry)
            status = 'added' if entry['minutes'] is not None else 'added_time_unknown'
        for message in entry['messages']:
            statuses[message] = status
    for row in rows:
        entries = proposals.get(row['external_id'], [])
        categories = {entry['category'] for entry in entries}
        if len(categories) > 1:
            # Never assign a whole session's minutes to every muscle group.
            status = 'pending_time_split'
        elif entries:
            row['record_workout_type'] = entries[0]['category']
            details = (row['record_detail'] or '').split(', ')
            details += [detail for entry in entries for detail in entry['details']]
            row['record_detail'] = ', '.join(dict.fromkeys(filter(None, details))) or None
            status = 'matched_watch'
        else:
            continue
        for entry in entries:
            for message in entry['messages']:
                statuses[message] = status
    return rows, extras, statuses


def save_report(conn, req):
    if req.kind != 'completed' or not req.workouts:
        return {'success': True, 'status': 'skipped_no_completed_workout'}
    from app.services.health_records import raw_workouts, sync_record
    conn.execute(text('SELECT pg_advisory_xact_lock(2101,:day)'), {'day': req.record_date.toordinal()})
    payload = req.model_dump(mode='json')
    existing = conn.execute(text('SELECT payload FROM workout_conversation_report WHERE source_message_id=:id'),
                            {'id': req.source_message_id}).scalar()
    if existing is not None and existing != payload:
        raise ValueError('A processed message cannot change; submit a new correction message')
    conn.execute(text('INSERT INTO day_record(record_date) VALUES (:day) ON CONFLICT DO NOTHING'), {'day': req.record_date})
    conn.execute(text('''INSERT INTO workout_conversation_report(source_message_id,record_date,reported_at,payload)
        VALUES (:id,:day,:at,CAST(:payload AS jsonb)) ON CONFLICT DO NOTHING'''),
        {'id': req.source_message_id, 'day': req.record_date, 'at': req.reported_at, 'payload': json.dumps(payload)})
    sync_record(conn, req.record_date, workouts=raw_workouts(conn, req.record_date))
    return {'success': True, 'status': 'unchanged' if existing is not None else 'processed'}
