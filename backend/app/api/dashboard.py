from datetime import date

from fastapi import APIRouter, Query

from app.crud.dashboard import get_dashboard
from app.crud.ai_analysis import get_daily_ai_analysis
from app.services.mission import build_today_missions

router = APIRouter()


@router.get("/api/dashboard")
def api_get_dashboard(record_date: date | None = Query(default=None)):
    target = record_date or date.today()

    dashboard = get_dashboard(target)
    ai = get_daily_ai_analysis(target)
    missions = build_today_missions(dashboard)

    return {
        "success": True,
        "record_date": str(target),
        "dashboard": dashboard,
        "ai": ai,
        "missions": missions,
    }
