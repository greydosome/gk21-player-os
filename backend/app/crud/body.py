
from sqlalchemy import text

def save_body(conn, day_record_id, body):

    if body is None:

        return

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

        "weight_kg": body.weight_kg,

        "waist_cm": body.waist_cm,

        "water_liter": body.water_liter,

        "protein_gram": body.protein_gram,

        "binge_yn": body.binge_yn,

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

