from fastapi import APIRouter, HTTPException, Query

from app.ai.llm import call_ai
from app.ai.medication_info_prompt import build_medication_info_prompt
from app.crud.medication_info import get_cached_medication_info, save_medication_info

router = APIRouter()


@router.get("/api/medication-info")
def api_get_medication_info(name: str = Query(..., min_length=1, max_length=100)):
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="name is required")

    # 같은 약 이름은 한 번만 OpenAI를 호출하고, 이후에는 캐시된 결과를 그대로 돌려준다.
    cached = get_cached_medication_info(clean_name)
    if cached is not None:
        return {"success": True, "cached": True, **cached}

    try:
        prompt = build_medication_info_prompt(clean_name)
        result = call_ai(prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    analysis = result.get("analysis", {})
    known = bool(analysis.get("known", False))
    efficacy = analysis.get("efficacy")
    side_effects = analysis.get("side_effects")
    caution = analysis.get("caution")

    save_medication_info(clean_name, known, efficacy, side_effects, caution)

    return {
        "success": True,
        "cached": False,
        "known": known,
        "efficacy": efficacy,
        "side_effects": side_effects,
        "caution": caution,
    }
