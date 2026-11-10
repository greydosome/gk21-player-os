from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

# These are existing diary categories and checkboxes, not inferred Watch metadata.
DETAILS = {
    '하체운동': {'스쿼트', '레그프레스', '런지', '레그컬', '카프레이즈', '레그익스텐션', '힙쓰러스트'},
    '등운동': {'랫풀다운', '티바로우', '데드리프트', '풀업', '시티드로우', '벤트오버 바벨로우', '원암 덤벨로우'},
    '가슴운동': {'벤치프레스', '인클라인 벤치프레스', '덤벨 플라이', '딥스', '푸시업', '디클라인 벤치프레스', '케이블 크로스오버'},
    '팔운동': {'바벨컬', '덤벨컬', '트라이셉스 익스텐션', '케이블 푸시다운', '해머컬', '스컬크러셔', '컨센트레이션컬'},
    '어깨운동': {'숄더프레스', '사이드 레터럴 레이즈', '프론트 레이즈', '페이스풀', '아놀드프레스', '업라이트로우', '리버스 펙덱 플라이'},
    '코어운동': {'플랭크', '크런치', '레그레이즈', '러시안트위스트', '사이드플랭크', '마운틴클라이머', '행잉레그레이즈'},
    '하체모빌리티': {'힙 서클', '90/90 스트레치', '카프 스트레치', '월드 그레이티스트 스트레치', '폼롤러', '런지 스트레치', '발목 모빌리티'},
    '클럽벨': {'숄더 캐스트', '밀', '스위치', '프라이멀 스윙', '180 스윙', '숄더 스윙'},
    **{name: set() for name in ('근력운동', '풋살', '걷기', '달리기', '자전거', '계단 오르기', '인클라인 워킹', '스텝퍼')},
}


class ReportWorkout(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str
    details: list[str] = Field(default_factory=list, max_length=15)
    minutes: float | None = Field(default=None, gt=0, le=1440, allow_inf_nan=False)
    session_key: str = Field(min_length=1, max_length=160)
    watch_external_id: str | None = Field(default=None, min_length=1, max_length=300)
    untracked: bool = False

    @model_validator(mode='after')
    def valid_exercises(self):
        if self.category not in DETAILS or not set(self.details) <= DETAILS[self.category]:
            raise ValueError('Unknown diary exercise')
        if self.untracked and self.watch_external_id:
            raise ValueError('Conflicting session source')
        self.details = list(dict.fromkeys(self.details))
        return self


class WorkoutReport(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_message_id: str = Field(min_length=1, max_length=300)
    record_date: date
    reported_at: datetime
    kind: Literal['completed', 'plan', 'question', 'none']
    workouts: list[ReportWorkout] = Field(default_factory=list, max_length=20)

    @model_validator(mode='after')
    def valid_day(self):
        today = datetime.now(ZoneInfo('Asia/Seoul')).date()
        if not today - timedelta(days=14) <= self.record_date <= today:
            raise ValueError('Workout date outside import window')
        if self.reported_at.tzinfo is None:
            raise ValueError('Timezone required')
        return self
