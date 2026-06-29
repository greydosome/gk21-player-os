from datetime import date

from sqlalchemy import text

from app.ai.progress import calculate_goal_progress
from app.db.session import engine


def get_ai_context(target_date: date):

    with engine.connect() as conn:

        today = conn.execute(
            text("""
                SELECT *
                FROM v_day_record_summary
                WHERE record_date = :record_date
            """),
            {
                "record_date": target_date
            }
        ).mappings().first()

        history = conn.execute(
            text("""
                SELECT
                    record_date,
                    score,
                    weight_kg,
                    waist_cm,
                    water_liter,
                    protein_gram,
                    meal_score,
                    sleep_hours,
                    bike_minutes,
                    workout_done_yn
                FROM v_day_record_summary
                WHERE record_date <= :record_date
                ORDER BY record_date DESC
                LIMIT 30
            """),
            {
                "record_date": target_date
            }
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
                    target_protein_gram,
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

    context = {
        "target_date": str(target_date),
        "today": dict(today) if today else {},
        "history": [dict(row) for row in history],
        "profile": dict(profile) if profile else {},
        "goal": dict(goal) if goal else {},
        "setting": dict(setting) if setting else {},
    }

    context["goal_progress"] = calculate_goal_progress(context)

    return context
