from datetime import date

from sqlalchemy import text

from app.db.session import engine


def get_dashboard(record_date: date):
    sql = text("""
        SELECT *
        FROM v_dashboard
        WHERE record_date = :record_date
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(
            sql,
            {"record_date": record_date}
        ).mappings().first()

    return dict(row) if row else None
