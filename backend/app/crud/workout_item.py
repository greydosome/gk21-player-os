
from sqlalchemy import text

def save_workout_items(conn, day_record_id, items):

    conn.execute(

        text("""

            DELETE FROM workout_item

            WHERE day_record_id = :day_record_id

        """),

        {

            "day_record_id": day_record_id

        }

    )

    if not items:

        return

    conn.execute(

        text("""

            INSERT INTO workout_item

            (

                day_record_id,

                workout_type,

                minutes,

                calorie_estimate

            )

            VALUES

            (

                :day_record_id,

                :workout_type,

                :minutes,

                :calorie_estimate

            )

        """),

        [
            {

                "day_record_id": day_record_id,

                "workout_type": item.workout_type,

                "minutes": item.minutes,

                "calorie_estimate": item.calorie_estimate,

            }
            for item in items
        ]

    )
