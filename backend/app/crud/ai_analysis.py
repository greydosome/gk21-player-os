
from datetime import date

from sqlalchemy import text

from app.db.session import engine

def get_daily_ai_analysis(target_date: date):

    sql = text("""

        SELECT

            a.analysis_id,

            a.analysis_type,

            a.lookback_days,

            a.overall_score,

            a.summary,

            a.strength,

            a.weakness,

            a.next_goal,

            a.body_comment,

            a.workout_comment,

            a.meal_comment,

            a.sleep_comment,

            a.model_name,

            a.prompt_version,

            a.created_at,

            a.updated_at

        FROM ai_analysis a

        JOIN day_record d

          ON a.day_record_id = d.day_record_id

        WHERE d.record_date = :record_date

          AND a.analysis_type = 'DAILY'

        LIMIT 1

    """)

    with engine.connect() as conn:

        row = conn.execute(

            sql,

            {

                "record_date": target_date

            }

        ).mappings().first()

    return dict(row) if row else None

