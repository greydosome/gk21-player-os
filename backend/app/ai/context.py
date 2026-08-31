
from collections import Counter

from contextlib import nullcontext

from datetime import date

from sqlalchemy import text

from app.ai.progress import calculate_goal_progress

from app.crud.food_history import get_general_food_history

from app.db.session import engine


def _summarize_food_history(limit=40):
    # get_general_food_history()는 "CUSTOM|이름|수량|단위|칼로리(|분류)" 원본 문자열을 그대로 준다.
    # 프롬프트에 그대로 넣기엔 형식이 프론트 전용이라, 이름/분류만 뽑아 자주 먹은 순으로 추린다.
    # 이렇게 하면 AI가 실존하지 않는 음식명을 지어내지 않고, 사용자가 실제로 먹어본 음식 중에서
    # 추천할 수 있다.
    counter = Counter()
    category_by_name = {}
    for raw in get_general_food_history():
        parts = raw.split("|")
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        if not name:
            continue
        category = parts[5] if len(parts) >= 6 and parts[5] else "general"
        counter[name] += 1
        category_by_name.setdefault(name, category)

    return [
        {"name": name, "category": category_by_name.get(name, "general"), "count": count}
        for name, count in counter.most_common(limit)
    ]

def get_ai_context(target_date: date, conn=None):

    # save_day()처럼 이미 열려있는 트랜잭션 안에서 호출될 때는 그 conn을 그대로 재사용해
    # 커넥션 풀을 추가로 점유하거나(같은 요청에서 커넥션 2개), 아직 커밋되지 않은 방금 쓴
    # 데이터를 별도 커넥션이 못 보는 문제를 피한다. conn이 없을 때(예: 백그라운드 LLM 분석)만
    # 새 커넥션을 연다.
    with (nullcontext(conn) if conn is not None else engine.connect()) as conn:

        today = conn.execute(

            text("""

                SELECT *

                FROM v_day_record_summary

                WHERE record_date = :record_date

            """),

            {"record_date": target_date}

        ).mappings().first()

        history = conn.execute(

            text("""

                SELECT

                    record_date,

                    score,

                    weight_kg,

                    waist_cm,

                    water_liter,

                    protein_kcal,

                    carb_kcal,

                    fat_kcal,

                    meal_score,

                    sleep_hours,

                    bike_minutes,

                    workout_done_yn

                FROM v_day_record_summary

                WHERE record_date <= :record_date

                ORDER BY record_date DESC

                LIMIT 30

            """),

            {"record_date": target_date}

        ).mappings().all()

        profile = conn.execute(

            text("""

                SELECT

                    nickname,

                    height_cm,

                    birth_date,

                    gender

                FROM user_profile

                LIMIT 1

            """)

        ).mappings().first()

        goal = conn.execute(

            text("""

                SELECT

                    goal_type,

                    target_weight_kg,

                    target_body_fat_percent,

                    target_waist_cm,

                    target_water_liter,

                    target_protein_kcal,

                    target_carb_kcal,

                    target_fat_kcal,

                    target_calorie,

                    weekly_workout_goal,

                    workout_style

                FROM user_goal

                WHERE goal_status = 'ACTIVE'

                LIMIT 1

            """)

        ).mappings().first()

        setting = conn.execute(

            text("""

                SELECT

                    ai_personality,

                    language,

                    timezone

                FROM user_setting

                LIMIT 1

            """)

        ).mappings().first()

        # 최근 30일간 실제로 수행한 운동을 종류별로 집계한다. workout_comment에서
        # "어떤 운동이 부족한지"를 구체적으로 짚어주려면 done/not-done 여부만으로는
        # 부족하고, 부위/종목별 빈도가 필요하다.
        workout_type_history = conn.execute(

            text("""

                SELECT

                    wi.workout_type,

                    SUM(wi.minutes) AS total_minutes,

                    COUNT(*) AS sessions,

                    MAX(dr.record_date) AS last_done

                FROM workout_item wi

                JOIN day_record dr ON dr.day_record_id = wi.day_record_id

                WHERE dr.record_date <= :record_date

                  AND dr.record_date > :record_date - INTERVAL '30 days'

                GROUP BY wi.workout_type

                ORDER BY total_minutes DESC

            """),

            {"record_date": target_date}

        ).mappings().all()

        # today.workout_done_yn은 "했다/안 했다"만 알려줘서, "근력만 하고 유산소는
        # 안 했다" 같은 종목 단위 판단을 하려면 오늘 실제로 기록된 운동 목록이 필요하다.
        today_workout_items = conn.execute(

            text("""

                SELECT wi.workout_type, wi.minutes, wi.detail

                FROM workout_item wi

                JOIN day_record dr ON dr.day_record_id = wi.day_record_id

                WHERE dr.record_date = :record_date

                ORDER BY wi.workout_item_id

            """),

            {"record_date": target_date}

        ).mappings().all()

    context = {

        "target_date": str(target_date),

        "today": dict(today) if today else {},

        "today_workout_items": [dict(row) for row in today_workout_items],

        "history": [dict(row) for row in history],

        "workout_type_history": [dict(row) for row in workout_type_history],

        "food_history": _summarize_food_history(),

        "profile": dict(profile) if profile else {},

        "goal": dict(goal) if goal else {},

        "setting": dict(setting) if setting else {},

    }

    context["goal_progress"] = calculate_goal_progress(context)

    return context

