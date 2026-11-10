from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Food(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    quantity: str | None = Field(default=None, max_length=100)
    kcal: float | None = Field(default=None, ge=0, le=20000, allow_inf_nan=False)
    protein_g: float | None = Field(default=None, ge=0, le=2000, allow_inf_nan=False)
    carbohydrate_g: float | None = Field(default=None, ge=0, le=5000, allow_inf_nan=False)
    fat_g: float | None = Field(default=None, ge=0, le=2000, allow_inf_nan=False)
    nutrition_source: str | None = Field(default=None, min_length=1, max_length=500)
    nutrition_basis: Literal['label','database','user','estimate','unknown'] = 'unknown'
    estimated: bool = True

    @model_validator(mode='after')
    def provenance(self):
        values = (self.kcal, self.protein_g, self.carbohydrate_g, self.fat_g)
        if any(v is not None for v in values):
            if not self.nutrition_source or self.nutrition_basis == 'unknown':
                raise ValueError('Nutrition values require provenance')
        if self.nutrition_basis in ('estimate','unknown') and not self.estimated:
            raise ValueError('Unknown or estimated nutrition cannot be exact')
        return self

class MealReport(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    conversation_id: str = Field(min_length=1, max_length=300)
    message_id: str = Field(min_length=1, max_length=300)
    reported_at: datetime
    record_date: date
    kind: Literal['consumed','correction','delete','recommendation','plan','question']
    confirmed_by_user: bool = False
    meal_key: str = Field(min_length=1, max_length=300)
    expected_revision: int = Field(default=0, ge=0)
    meal_type: Literal['breakfast','lunch','dinner','snack','unknown'] = 'unknown'
    foods: list[Food] = Field(default_factory=list, max_length=40)

    @model_validator(mode='after')
    def validate_report(self):
        now = datetime.now(ZoneInfo('Asia/Seoul'))
        if self.reported_at.tzinfo is None or self.reported_at > now + timedelta(minutes=5):
            raise ValueError('Valid source timestamp required')
        if not now.date()-timedelta(days=14) <= self.record_date <= now.date():
            raise ValueError('Date outside import window')
        if self.kind in ('consumed','correction') and not self.foods:
            raise ValueError('Consumed foods required')
        if self.kind == 'delete' and self.foods:
            raise ValueError('Delete must not contain foods')
        return self
