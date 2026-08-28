from pydantic import BaseModel


class PeriodDayInput(BaseModel):
    record_date: str
    diet_kcal: int
    cardio_labels: list[str] = []
    strength_labels: list[str] = []


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
