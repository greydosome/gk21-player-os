import json
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.db.session import engine
from app.schemas.workout_report import WorkoutReport
from app.services.workout_reports import save_report, project_reports
from app.services.health_records import KOREA
from datetime import datetime, timedelta

router = APIRouter()


@router.post('/api/integrations/workout-reports')
async def ingest_report(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 32768:
            raise HTTPException(413, 'Payload too large')
    try:
        report = WorkoutReport.model_validate(json.loads(body))
    except ValueError:
        raise HTTPException(422, 'Invalid workout report') from None
    try:
        return await run_in_threadpool(persist, report)
    except ValueError:
        raise HTTPException(409, 'Report message already processed with different content') from None


def persist(report):
    with engine.begin() as conn:
        return save_report(conn, report)


@router.get('/api/integrations/workout-reports')
def report_status(record_date: date = Query(...)):
    begin = datetime.combine(record_date, datetime.min.time(), KOREA)
    with engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(text('''SELECT * FROM apple_health_workout
            WHERE ended_at>=:begin AND ended_at<:end ORDER BY started_at,external_id'''),
            {'begin': begin, 'end': begin + timedelta(days=1)}).mappings()]
        _, _, statuses = project_reports(conn, record_date, [dict(r) for r in rows])
        reports = conn.execute(text('SELECT source_message_id FROM workout_conversation_report WHERE record_date=:day'),
                               {'day': record_date}).scalars().all()
    return {'success': True, 'record_date': str(record_date), 'reports': reports, 'statuses': statuses,
            'watch_sessions': [{key: row[key] for key in ('external_id', 'workout_type', 'started_at', 'ended_at', 'duration_seconds', 'record_workout_type')} for row in rows]}
