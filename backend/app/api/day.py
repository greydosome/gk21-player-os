from datetime import date

from fastapi import APIRouter, Query

from app.crud.day import get_today
from app.crud.day import save_day
from app.schemas.day import DayRecordRequest

router = APIRouter()


@router.get("/api/today")
def api_get_today(record_date: date | None = Query(default=None)):

    target = record_date or date.today()

    return {
        "success": True,
        "record_date": str(target),
        "record": get_today(target)
    }


@router.post("/api/day")
def api_save_day(req: DayRecordRequest):

    day_record_id = save_day(req)

    return {
        "success": True,
        "day_record_id": day_record_id
    }
