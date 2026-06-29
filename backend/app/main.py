from datetime import date

from fastapi import FastAPI, Query
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


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
        result = conn.execute(text("SELECT 1 AS ping")).scalar_one()

    return {
        "database": "ok",
        "ping": result,
    }


@app.get("/api/today")
def get_today(record_date: date | None = Query(default=None)):
    target_date = record_date or date.today()

    sql = text("""
        SELECT
            day_no,
            week_no,
            day_record_id,
            record_date,
            score,
            grade,
            mood_score,
            weight_kg,
            waist_cm,
            water_liter,
            protein_gram,
            binge_yn,
            bike_minutes,
            workout_done_yn,
            lightness_score,
            reaction_score,
            side_score,
            shoulder_score,
            coach_note,
            ai_summary,
            next_goal,
            memo,
            created_at,
            updated_at
        FROM v_day_record_summary
        WHERE record_date = :record_date
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, {"record_date": target_date}).mappings().first()

    return {
        "success": True,
        "record_date": str(target_date),
        "record": dict(row) if row else None,
    }
