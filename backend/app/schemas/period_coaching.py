from pydantic import BaseModel


class PeriodDayInput(BaseModel):
    record_date: str
    diet_kcal: int
    cardio_labels: list[str] = []
    strength_labels: list[str] = []
    is_sick: bool = False
    is_injured: bool = False


class PeriodCoachingRequest(BaseModel):
    period: str  # "week" | "month"
    start_date: str
    end_date: str
    days: list[PeriodDayInput]
    total_kcal: int
    budget_kcal: int
    ratio_percent: int
    avg_sleep_hours: float | None = None
    avg_water_liter: float | None = None
    avg_weight_kg: float | None = None
    # 기간 동안 하루라도 기록된 약 이름(중복 제거). 코칭에 참고만 하고, 의학적 판단은 하지 않는다.
    medications: list[str] = []
