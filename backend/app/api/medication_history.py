from fastapi import APIRouter

from app.crud.medication_history import get_medication_history

router = APIRouter()


@router.get("/api/medication-history")
def api_get_medication_history():
    return {
        "success": True,
        "items": get_medication_history(),
    }
