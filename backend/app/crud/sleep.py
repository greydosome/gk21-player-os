
from sqlalchemy import text

def save_sleep(conn, day_record_id, sleep):

    if sleep is None:

        return

    sleep_exists = conn.execute(

        text("""

            SELECT sleep_record_id

            FROM sleep_record

            WHERE day_record_id = :day_record_id

        """),

        {

            "day_record_id": day_record_id

        }

    ).scalar()

    params = {

        "day_record_id": day_record_id,

        "sleep_start_time": sleep.sleep_start_time,

        "sleep_end_time": sleep.sleep_end_time,

        "sleep_hours": sleep.sleep_hours,

        "sleep_quality_score": sleep.sleep_quality_score,

        "wake_condition": sleep.wake_condition,

    }

    if sleep_exists:

        params["sleep_record_id"] = sleep_exists

        conn.execute(

            text("""

                UPDATE sleep_record

                SET

                    sleep_start_time = :sleep_start_time,

                    sleep_end_time = :sleep_end_time,

                    sleep_hours = :sleep_hours,

                    sleep_quality_score = :sleep_quality_score,

                    wake_condition = :wake_condition,

                    updated_at = now()

                WHERE sleep_record_id = :sleep_record_id

            """),

            params

        )

    else:

        conn.execute(

            text("""

                INSERT INTO sleep_record

                (

                    day_record_id,

                    sleep_start_time,

                    sleep_end_time,

                    sleep_hours,

                    sleep_quality_score,

                    wake_condition

                )

                VALUES

                (

                    :day_record_id,

                    :sleep_start_time,

                    :sleep_end_time,

                    :sleep_hours,

                    :sleep_quality_score,

                    :wake_condition

                )

            """),

            params

        )

