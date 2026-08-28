from fastapi import APIRouter, HTTPException

from app.ai.llm import call_ai
from app.ai.period_prompt import build_period_prompt
from app.schemas.period_coaching import PeriodCoachingRequest

router = APIRouter()


@router.post("/api/ai/period-coaching")
def api_period_coaching(req: PeriodCoachingRequest):
    # 위클리/먼슬리 탭에서 버튼을 눌렀을 때만 호출되는 온디맨드 코칭이라, 하루
    # 코칭과 달리 백그라운드 큐/DB 저장 없이 요청-응답으로 바로 처리한다
    # (매 렌더마다 자동으로 도는 게 아니라 명시적 클릭에만 실제 LLM 호출이 나간다).
    payload = {
        "period": req.period,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "daily_budget": req.budget_kcal // max(len(req.days), 1),
        "total_kcal": req.total_kcal,
        "budget_kcal": req.budget_kcal,
        "ratio_percent": req.ratio_percent,
        "avg_sleep_hours": req.avg_sleep_hours,
        "avg_water_liter": req.avg_water_liter,
        "avg_weight_kg": req.avg_weight_kg,
        "diet_by_day": [
            {"record_date": d.record_date, "diet_kcal": d.diet_kcal} for d in req.days
        ],
        "cardio_by_day": [
            {"record_date": d.record_date, "items": d.cardio_labels} for d in req.days if d.cardio_labels
        ],
        "strength_by_day": [
            {"record_date": d.record_date, "items": d.strength_labels} for d in req.days if d.strength_labels
        ],
    }

    try:
        prompt = build_period_prompt(payload)
        result = call_ai(prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    analysis = result.get("analysis", {})

    return {
        "success": True,
        "coaching": {
            "workout_good": analysis.get("workout_good"),
            "workout_improve": analysis.get("workout_improve"),
            "meal_praise": analysis.get("meal_praise"),
            "summary": analysis.get("summary"),
        },
    }
