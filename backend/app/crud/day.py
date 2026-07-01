from datetime import date

from sqlalchemy import text

from app.ai.analysis_service import generate_daily_rule_analysis
from app.crud.body import save_body
from app.crud.meal import save_meal
from app.crud.sleep import save_sleep
from app.crud.workout import save_workout
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
            {"record_date": target_date}
        ).mappings().first()

    return dict(row) if row else None


def save_day_record(conn, req):
    existing = conn.execute(
        text("""
            SELECT day_record_id
            FROM day_record
            WHERE record_date = :record_date
        """),
        {"record_date": req.record_date}
    ).scalar()

    params = {
        "record_date": req.record_date,
        "score": req.score,
        "grade": req.grade,
        "mood_score": req.mood_score,
        "memo": req.memo,
        "morning_med_taken": req.morning_med_taken,
        "evening_med_taken": req.evening_med_taken,
        "medication_note": req.medication_note,
    }

    if existing:
        params["day_record_id"] = existing

        conn.execute(
            text("""
                UPDATE day_record
                SET
                    score = :score,
                    grade = :grade,
                    mood_score = :mood_score,
                    memo = :memo,
                    morning_med_taken = :morning_med_taken,
                    evening_med_taken = :evening_med_taken,
                    medication_note = :medication_note,
                    updated_at = now()
                WHERE day_record_id = :day_record_id
            """),
            params
        )

        return existing

    return conn.execute(
        text("""
            INSERT INTO day_record
            (
                record_date,
                score,
                grade,
                mood_score,
                memo,
                morning_med_taken,
                evening_med_taken,
                medication_note
            )
            VALUES
            (
                :record_date,
                :score,
                :grade,
                :mood_score,
                :memo,
                :morning_med_taken,
                :evening_med_taken,
                :medication_note
            )
            RETURNING day_record_id
        """),
        params
    ).scalar_one()


def save_day(req):
    with engine.begin() as conn:
        day_record_id = save_day_record(conn, req)

        save_body(conn, day_record_id, req.body)
        save_workout(conn, day_record_id, req.workout)
        save_meal(conn, day_record_id, req.meal)
        save_sleep(conn, day_record_id, req.sleep)

        generate_daily_rule_analysis(
            conn=conn,
            day_record_id=day_record_id,
            record_date=req.record_date
        )

    return day_record_id
