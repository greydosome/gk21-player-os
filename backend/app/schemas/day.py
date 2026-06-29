
from datetime import date

from pydantic import BaseModel

class BodyRecord(BaseModel):

    weight_kg: float | None = None

    waist_cm: float | None = None

    water_liter: float | None = None

    protein_gram: int | None = None

    binge_yn: bool | None = None

class WorkoutRecord(BaseModel):

    planned_workout: str | None = None

    completed_workout: str | None = None

    bike_minutes: int | None = None

    workout_done_yn: bool | None = None

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

class DayRecordRequest(BaseModel):

    record_date: date

    score: int

    grade: str

    mood_score: int

    memo: str | None = None

    body: BodyRecord | None = None

    workout: WorkoutRecord | None = None

    meal: MealRecord | None = None

    sleep: SleepRecord | None = None

