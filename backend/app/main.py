from datetime import date

from fastapi import FastAPI, Query
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.day import DayRecordRequest

app = FastAPI(
    title="GK21 API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
    }


@app.get("/api/db/ping")
def db_ping():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()

    return {
        "database": "ok",
        "ping": result,
    }


@app.get("/api/today")
def get_today(record_date: date | None = Query(default=None)):
    target_date = record_date or date.today()

    sql = text("""
        SELECT *
        FROM v_day_record_summary
        WHERE record_date = :record_date
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(
            sql,
            {"record_date": target_date}
        ).mappings().first()

    return {
        "success": True,
        "record_date": str(target_date),
        "record": dict(row) if row else None,
    }


@app.post("/api/day")
def save_day(req: DayRecordRequest):

    with engine.begin() as conn:

        existing = conn.execute(
            text("""
                SELECT day_record_id
                FROM day_record
                WHERE record_date = :record_date
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

            day_record_id = existing

        else:

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

    return {
        "success": True,
        "day_record_id": day_record_id,
    }

