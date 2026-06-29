from datetime import date

from pydantic import BaseModel


class DayRecordRequest(BaseModel):
    record_date: date
    score: int
    grade: str
    mood_score: int
    memo: str | None = None
