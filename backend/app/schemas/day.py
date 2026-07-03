from datetime import date
from pydantic import BaseModel


class BodyRecord(BaseModel):
    weight_kg: float | None = None
    waist_cm: float | None = None
    water_liter: float | None = None
    protein_gram: int | None = None
    protein_items: list[str] | None = None
    binge_yn: bool | None = None


class WorkoutRecord(BaseModel):
    planned_workout: str | None = None
    completed_workout: str | None = None
    bike_minutes: int | None = None
    workout_done_yn: bool | None = None


class WorkoutItem(BaseModel):
    workout_type: str
    minutes: int
    calorie_estimate: int | None = None
    detail: str | None = None


class MealRecord(BaseModel):
    breakfast: str | None = None
    lunch: str | None = None
    dinner: str | None = None
    snack: str | None = None
    total_calorie: int | None = None
    meal_score: int | None = None


class SleepRecord(BaseModel):
    sleep_start_time: str | None = None
    sleep_end_time: str | None = None
    sleep_hours: float | None = None
    sleep_quality_score: int | None = None
    wake_condition: str | None = None


class GkRecord(BaseModel):
    lightness_score: int | None = None
    reaction_score: int | None = None
    side_score: int | None = None
    shoulder_score: int | None = None
    gk_memo: str | None = None


class DayRecordRequest(BaseModel):
    record_date: date
    score: int = 0
    grade: str = "GREEN"
    mood_score: int = 3
    memo: str | None = None
    mvp_text: str | None = None
    is_sick: bool = False

    morning_med_taken: bool | None = False
    evening_med_taken: bool | None = False
    medication_note: str | None = None

    body: BodyRecord | None = None
    workout: WorkoutRecord | None = None
    workout_items: list[WorkoutItem] = []
    meal: MealRecord | None = None
    sleep: SleepRecord | None = None
    gk: GkRecord | None = None
