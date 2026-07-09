
import json

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

        "protein_kcal": body.protein_kcal,

        "protein_items": json.dumps(body.protein_items or [], ensure_ascii=False),

        "carb_kcal": body.carb_kcal,

        "carb_items": json.dumps(body.carb_items or [], ensure_ascii=False),

        "fat_kcal": body.fat_kcal,

        "fat_items": json.dumps(body.fat_items or [], ensure_ascii=False),

        "supplement_items": json.dumps(body.supplement_items or [], ensure_ascii=False),

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

                    protein_kcal = :protein_kcal,

                    protein_items = CAST(:protein_items AS jsonb),

                    carb_kcal = :carb_kcal,

                    carb_items = CAST(:carb_items AS jsonb),

                    fat_kcal = :fat_kcal,

                    fat_items = CAST(:fat_items AS jsonb),

                    supplement_items = CAST(:supplement_items AS jsonb),

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

                    protein_kcal,

                    protein_items,

                    carb_kcal,

                    carb_items,

                    fat_kcal,

                    fat_items,

                    supplement_items,

                    binge_yn

                )

                VALUES

                (

                    :day_record_id,

                    :weight_kg,

                    :waist_cm,

                    :water_liter,

                    :protein_kcal,

                    CAST(:protein_items AS jsonb),

                    :carb_kcal,

                    CAST(:carb_items AS jsonb),

                    :fat_kcal,

                    CAST(:fat_items AS jsonb),

                    CAST(:supplement_items AS jsonb),

                    :binge_yn

                )

            """),

            params

        )
