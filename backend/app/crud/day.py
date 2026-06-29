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

        #################################################
        # day_record UPSERT
        #################################################

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
                {
                    "record_date": req.record_date,
                    "score": req.score,
                    "grade": req.grade,
                    "mood_score": req.mood_score,
                    "memo": req.memo
                }
            ).scalar_one()

        #################################################
        # body_record UPSERT
        #################################################

        if req.body is not None:

            body_exists = conn.execute(
                text("""
                    SELECT body_record_id
                    FROM body_record
                    WHERE day_record_id = :day_record_id
                """),
                {
                    "day_record_id": day_record_id
                }
            ).scalar()

            params = {
                "day_record_id": day_record_id,
                "weight_kg": req.body.weight_kg,
                "waist_cm": req.body.waist_cm,
                "water_liter": req.body.water_liter,
                "protein_gram": req.body.protein_gram,
                "binge_yn": req.body.binge_yn,
            }

            if body_exists:

                params["body_record_id"] = body_exists

                conn.execute(
                    text("""
                        UPDATE body_record
                        SET
                            weight_kg = :weight_kg,
                            waist_cm = :waist_cm,
                            water_liter = :water_liter,
                            protein_gram = :protein_gram,
                            binge_yn = :binge_yn,
                            updated_at = now()
                        WHERE body_record_id = :body_record_id
                    """),
                    params
                )

            else:

                conn.execute(
                    text("""
                        INSERT INTO body_record
                        (
                            day_record_id,
                            weight_kg,
                            waist_cm,
                            water_liter,
                            protein_gram,
                            binge_yn
                        )
                        VALUES
                        (
                            :day_record_id,
                            :weight_kg,
                            :waist_cm,
                            :water_liter,
                            :protein_gram,
                            :binge_yn
                        )
                    """),
                    params
                )

        #################################################
        # workout_record UPSERT
        #################################################

        if req.workout is not None:

            workout_exists = conn.execute(
                text("""
                    SELECT workout_record_id
                    FROM workout_record
                    WHERE day_record_id = :day_record_id
                """),
                {
                    "day_record_id": day_record_id
                }
            ).scalar()

            params = {
                "day_record_id": day_record_id,
                "planned_workout": req.workout.planned_workout,
                "completed_workout": req.workout.completed_workout,
                "bike_minutes": req.workout.bike_minutes,
                "workout_done_yn": req.workout.workout_done_yn,
            }

            if workout_exists:

                params["workout_record_id"] = workout_exists

                conn.execute(
                    text("""
                        UPDATE workout_record
                        SET
                            planned_workout = :planned_workout,
                            completed_workout = :completed_workout,
                            bike_minutes = :bike_minutes,
                            workout_done_yn = :workout_done_yn,
                            updated_at = now()
                        WHERE workout_record_id = :workout_record_id
                    """),
                    params
                )

            else:

                conn.execute(
                    text("""
                        INSERT INTO workout_record
                        (
                            day_record_id,
                            planned_workout,
                            completed_workout,
                            bike_minutes,
                            workout_done_yn
                        )
                        VALUES
                        (
                            :day_record_id,
                            :planned_workout,
                            :completed_workout,
                            :bike_minutes,
                            :workout_done_yn
                        )
                    """),
                    params
                )

    return day_record_id
