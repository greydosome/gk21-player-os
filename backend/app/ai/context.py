
from datetime import date

from sqlalchemy import text

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

    return {

        "target_date": str(target_date),

        "today": dict(today) if today else {},

        "history": [dict(x) for x in history]

    }

