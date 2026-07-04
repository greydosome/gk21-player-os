import json

from sqlalchemy import text

from app.ai.llm import call_ai
from app.db.session import engine

FALLBACK_SUGGESTIONS = [
    "오늘도 출석했다",
    "오늘도 시즌을 이어갔다",
    "작은 것 하나는 해냈다",
    "완벽하지 않아도 이어갔다",
    "오늘은 회복이 필요했다",
    "다음을 위해 오늘을 버텼다",
]

PROMPT_TEMPLATE = """
당신은 골키퍼 컨디션 관리 앱 GK21의 코치입니다.
사용자가 하루를 마무리하며 고를 "오늘의 한마디" 짧은 문구 6개를 만들어주세요.

원칙
- 각 문구는 한국어로 10자 내외의 짧은 한 문장입니다.
- 결과를 비난하지 않고, 꾸준함과 과정을 응원하는 톤입니다.
- 좋은 날/보통인 날/힘든 날 모두 고를 수 있도록 다양한 감정 상태를 골고루 포함하세요.
- 매번 표현을 새롭게 바꿔서 다양성을 주세요.
- 반드시 아래 JSON 형식만 반환하세요.

{"suggestions": ["문구1", "문구2", "문구3", "문구4", "문구5", "문구6"]}
"""


def get_or_generate_mvp_suggestions(record_date):
    with engine.connect() as conn:
        cached = conn.execute(
            text("SELECT suggestions FROM mvp_suggestion_cache WHERE record_date = :record_date"),
            {"record_date": record_date}
        ).scalar()

    if cached:
        return cached

    try:
        result = call_ai(PROMPT_TEMPLATE)
        suggestions = result["analysis"]["suggestions"]
        if not isinstance(suggestions, list) or not suggestions:
            raise ValueError("empty suggestions")
    except Exception:
        suggestions = FALLBACK_SUGGESTIONS

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO mvp_suggestion_cache (record_date, suggestions)
                VALUES (:record_date, CAST(:suggestions AS jsonb))
                ON CONFLICT (record_date) DO NOTHING
            """),
            {
                "record_date": record_date,
                "suggestions": json.dumps(suggestions, ensure_ascii=False),
            }
        )

    return suggestions
