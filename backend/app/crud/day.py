from datetime import date

from sqlalchemy import text

from app.db.session import engine


def get_today(target_date: date):

    sql = text("""
        SELECT *
        FROM v_day_record_summary
        WHERE record_date = :record_date
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


def save_day(req):

    with engine.begin() as conn:

        existing = conn.execute(
            text("""
                SELECT day_record_id
                FROM day_record
                WHERE record_date=:record_date
            """),
            {
                "record_date": req.record_date
            }
        ).scalar()

        if existing:

            conn.execute(
                text("""
                    UPDATE day_record
                    SET
                        score=:score,
                        grade=:grade,
                        mood_score=:mood_score,
                        memo=:memo,
                        updated_at=now()
                    WHERE day_record_id=:day_record_id
                """),
                {
                    **req.model_dump(),
                    "day_record_id": existing
                }
            )

            return existing

        day_record_id = conn.execute(
            text("""
                INSERT INTO day_record
                (
                    record_date,
                    score,
                    grade,
                    mood_score,
                    memo
                )
                VALUES
                (
                    :record_date,
                    :score,
                    :grade,
                    :mood_score,
                    :memo
                )
                RETURNING day_record_id
            """),
            req.model_dump()
        ).scalar_one()

        return day_record_id
