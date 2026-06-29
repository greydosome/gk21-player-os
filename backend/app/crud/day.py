
from datetime import date

from sqlalchemy import text

from app.ai.context import get_ai_context

from app.ai.metrics import calculate_ai_metrics

from app.ai.rule_engine import build_daily_rule_analysis

from app.ai.saver import save_ai_analysis

from app.db.session import engine

from app.crud.body import save_body

from app.crud.workout import save_workout

from app.crud.meal import save_meal

from app.crud.sleep import save_sleep

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

def save_day_record(conn, req):

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

                    score = :score,

                    grade = :grade,

                    mood_score = :mood_score,

                    memo = :memo,

                    updated_at = now()

                WHERE day_record_id = :day_record_id

            """),

            {

                "day_record_id": existing,

                "score": req.score,

                "grade": req.grade,

                "mood_score": req.mood_score,

                "memo": req.memo

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

        {

            "record_date": req.record_date,

            "score": req.score,

            "grade": req.grade,

            "mood_score": req.mood_score,

            "memo": req.memo

        }

    ).scalar_one()

    return day_record_id

def generate_daily_ai_analysis(conn, day_record_id, record_date):

    context = get_ai_context(record_date)

    metrics = calculate_ai_metrics(context)

    analysis = build_daily_rule_analysis(context, metrics)

    save_ai_analysis(

        conn=conn,

        day_record_id=day_record_id,

        context=context,

        metrics=metrics,

        analysis=analysis

    )

def save_day(req):

    with engine.begin() as conn:

        day_record_id = save_day_record(conn, req)

        save_body(conn, day_record_id, req.body)

        save_workout(conn, day_record_id, req.workout)

        save_meal(conn, day_record_id, req.meal)

        save_sleep(conn, day_record_id, req.sleep)

        generate_daily_ai_analysis(conn, day_record_id, req.record_date)

    return day_record_id

