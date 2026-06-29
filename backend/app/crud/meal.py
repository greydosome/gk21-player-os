
from sqlalchemy import text

def save_meal(conn, day_record_id, meal):

    if meal is None:

        return

    meal_exists = conn.execute(

        text("""

            SELECT meal_record_id

            FROM meal_record

            WHERE day_record_id = :day_record_id

        """),

        {

            "day_record_id": day_record_id

        }

    ).scalar()

    params = {

        "day_record_id": day_record_id,

        "breakfast": meal.breakfast,

        "lunch": meal.lunch,

        "dinner": meal.dinner,

        "snack": meal.snack,

        "total_calorie": meal.total_calorie,

        "meal_score": meal.meal_score,

    }

    if meal_exists:

        params["meal_record_id"] = meal_exists

        conn.execute(

            text("""

                UPDATE meal_record

                SET

                    breakfast = :breakfast,

                    lunch = :lunch,

                    dinner = :dinner,

                    snack = :snack,

                    total_calorie = :total_calorie,

                    meal_score = :meal_score,

                    updated_at = now()

                WHERE meal_record_id = :meal_record_id

            """),

            params

        )

    else:

        conn.execute(

            text("""

                INSERT INTO meal_record

                (

                    day_record_id,

                    breakfast,

                    lunch,

                    dinner,

                    snack,

                    total_calorie,

                    meal_score

                )

                VALUES

                (

                    :day_record_id,

                    :breakfast,

                    :lunch,

                    :dinner,

                    :snack,

                    :total_calorie,

                    :meal_score

                )

            """),

            params

        )

