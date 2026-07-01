from datetime import date
from fastapi import APIRouter, Query
from app.crud.ai_analysis import get_daily_ai_analysis
router = APIRouter()

@router.get("/api/ai/daily")
def api_get_daily_ai_analysis(record_date: date | None = Query(default=None)):
    target = record_date or date.today()
    analysis = get_daily_ai_analysis(target)
    return {
        "success": True,
        "record_date": str(target),
        "analysis": analysis
    }
