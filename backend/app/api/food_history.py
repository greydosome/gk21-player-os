from fastapi import APIRouter

from app.crud.food_history import get_general_food_history

router = APIRouter()


@router.get("/api/food-history")
def api_get_food_history():
    return {
        "success": True,
        "items": get_general_food_history(),
    }
