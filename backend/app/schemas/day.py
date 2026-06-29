from datetime import date

from pydantic import BaseModel


class BodyRecord(BaseModel):
    weight_kg: float | None = None
    waist_cm: float | None = None
    water_liter: float | None = None
    protein_gram: int | None = None
    binge_yn: bool | None = None


class DayRecordRequest(BaseModel):
    record_date: date
    score: int
    grade: str
    mood_score: int
    memo: str | None = None

    body: BodyRecord | None = None
