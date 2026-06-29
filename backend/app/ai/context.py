
from datetime import date

from sqlalchemy import text

from app.db.session import engine

def get_ai_context(target_date: date):

    sql_today = text("""

        SELECT *

        FROM v_day_record_summary

        WHERE record_date = :record_date

        LIMIT 1

    """)

    sql_recent = text("""

        SELECT *

        FROM v_day_record_summary

        WHERE record_date <= :record_date

        ORDER BY record_date DESC

        LIMIT :limit_count

    """)

    with engine.connect() as conn:

        today_row = conn.execute(

            sql_today,

            {

                "record_date": target_date

            }

        ).mappings().first()

        recent_7_rows = conn.execute(

            sql_recent,

            {

                "record_date": target_date,

                "limit_count": 7

            }

        ).mappings().all()

        recent_30_rows = conn.execute(

            sql_recent,

            {

                "record_date": target_date,

                "limit_count": 30

            }

        ).mappings().all()

    return {

        "target_date": str(target_date),

        "today": dict(today_row) if today_row else None,

        "recent_7_days": [dict(row) for row in recent_7_rows],

        "recent_30_days": [dict(row) for row in recent_30_rows],

    }

