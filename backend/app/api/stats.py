from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.crud.stats import get_period_stats

router = APIRouter()


@router.get("/api/stats")
def api_get_stats(
    period: Literal["week", "month"] = Query(default="week"),
    record_date: date | None = Query(default=None),
):
    target = record_date or date.today()
    days = 7 if period == "week" else 30

    stats = get_period_stats(target, days)

    return {
        "success": True,
        "period": period,
        "stats": stats,
    }
