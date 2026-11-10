import json
from datetime import date
from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from app.db.session import engine
from app.schemas.meal_report import MealReport
from app.services.meal_reports import save_report, read_meals
router=APIRouter()

def persist(report):
    with engine.begin() as conn:
        return save_report(conn,report)

@router.post('/api/integrations/meal-reports')
async def ingest(request: Request):
    body=bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body)>32768:
            raise HTTPException(413,'Payload too large')
    try:
        report=MealReport.model_validate(json.loads(body))
    except ValueError:
        raise HTTPException(422,'Invalid meal report') from None
    try:
        return await run_in_threadpool(persist,report)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from None

@router.get('/api/integrations/meal-reports')
def status(record_date: date):
    with engine.connect() as conn:
        return read_meals(conn,record_date,include_deleted=True)

@router.get('/api/consumed-meals')
def meals(record_date: date):
    with engine.connect() as conn:
        return read_meals(conn,record_date)
