from datetime import date

from fastapi import APIRouter, Query

from app.ai.mvp_suggestions import get_or_generate_mvp_suggestions

router = APIRouter()


@router.get("/api/mvp-suggestions")
def api_get_mvp_suggestions(record_date: date | None = Query(default=None)):
    target = record_date or date.today()

    suggestions = get_or_generate_mvp_suggestions(target)

    return {
        "success": True,
        "record_date": str(target),
        "suggestions": suggestions,
    }
