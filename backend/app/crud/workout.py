
from sqlalchemy import text

def save_workout(conn, day_record_id, workout):

    if workout is None:

        return

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

        "planned_workout": workout.planned_workout,

        "completed_workout": workout.completed_workout,

        "bike_minutes": workout.bike_minutes,

        "workout_done_yn": workout.workout_done_yn,

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

