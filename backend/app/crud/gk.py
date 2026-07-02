
from sqlalchemy import text

def save_gk(conn, day_record_id, gk):

    if gk is None:

        return

    gk_exists = conn.execute(

        text("""

            SELECT gk_record_id

            FROM gk_record

            WHERE day_record_id = :day_record_id

        """),

        {

            "day_record_id": day_record_id

        }

    ).scalar()

    params = {

        "day_record_id": day_record_id,

        "lightness_score": gk.lightness_score,

        "reaction_score": gk.reaction_score,

        "side_score": gk.side_score,

        "shoulder_score": gk.shoulder_score,

        "gk_memo": gk.gk_memo,

    }

    if gk_exists:

        params["gk_record_id"] = gk_exists

        conn.execute(

            text("""

                UPDATE gk_record

                SET

                    lightness_score = :lightness_score,

                    reaction_score = :reaction_score,

                    side_score = :side_score,

                    shoulder_score = :shoulder_score,

                    gk_memo = :gk_memo,

                    updated_at = now()

                WHERE gk_record_id = :gk_record_id

            """),

            params

        )

    else:

        conn.execute(

            text("""

                INSERT INTO gk_record

                (

                    day_record_id,

                    lightness_score,

                    reaction_score,

                    side_score,

                    shoulder_score,

                    gk_memo

                )

                VALUES

                (

                    :day_record_id,

                    :lightness_score,

                    :reaction_score,

                    :side_score,

                    :shoulder_score,

                    :gk_memo

                )

            """),

            params

        )
