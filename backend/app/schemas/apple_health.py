from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class WorkoutSummary(StrictModel):
    workout_type: str = Field(min_length=1, max_length=60)
    minutes: float = Field(gt=0, le=1440)


class HealthSummary(StrictModel):
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    weight_measured_at: AwareDatetime | None = None
    workouts: list[WorkoutSummary] | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def paired_weight(self):
        if (self.weight_kg is None) != (self.weight_measured_at is None):
            raise ValueError("weight requires value and measurement time")
        if sum(w.minutes for w in self.workouts or []) > 1440:
            raise ValueError("workout duration exceeds one day")
        return self


class AppleHealthRequest(StrictModel):
    schema_version: Literal[1] = 1
    record_date: date
    timezone: Literal["Asia/Seoul"] = "Asia/Seoul"
    collected_at: AwareDatetime
    summary: HealthSummary

    @model_validator(mode="after")
    def dates(self):
        now = datetime.now(ZoneInfo(self.timezone))
        if not now.date() - timedelta(days=30) <= self.record_date <= now.date():
            raise ValueError("record_date must be within the last 30 days")
        if self.collected_at > now + timedelta(minutes=5):
            raise ValueError("collected_at is in the future")
        if self.collected_at.astimezone(ZoneInfo(self.timezone)).date() < self.record_date:
            raise ValueError("collection precedes record date")
        measured = self.summary.weight_measured_at
        if measured and (measured > self.collected_at or measured.astimezone(ZoneInfo(self.timezone)).date() != self.record_date):
            raise ValueError("weight must be measured on record_date before collection")
        return self
