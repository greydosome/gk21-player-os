from app.data.philosophy import PHILOSOPHY_QUOTES


def get_daily_philosophy(day_no: int | None) -> dict:
    if not PHILOSOPHY_QUOTES:
        return {
            "category": "GK21",
            "text": "오늘도 Journey는 이어졌습니다.",
        }

    safe_day_no = day_no or 1
    index = (safe_day_no - 1) % len(PHILOSOPHY_QUOTES)

    return PHILOSOPHY_QUOTES[index]
