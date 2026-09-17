from contextlib import nullcontext

from datetime import date

from sqlalchemy import text

from app.db.session import engine


def get_dashboard(record_date: date, conn=None):
    sql = text("""
        SELECT *
        FROM v_dashboard
        WHERE record_date = :record_date
        LIMIT 1
    """)

    with (nullcontext(conn) if conn is not None else engine.connect()) as conn:
        row = conn.execute(
            sql,
            {"record_date": record_date}
        ).mappings().first()

    return dict(row) if row else None


def get_day_detail(record_date: date, conn=None):
    with (nullcontext(conn) if conn is not None else engine.connect()) as conn:
        day_record_id = conn.execute(
            text("SELECT day_record_id FROM day_record WHERE record_date = :record_date"),
            {"record_date": record_date}
        ).scalar()

        if not day_record_id:
            return {
                "workout_items": [],
                "protein_items": [],
                "carb_items": [],
                "fat_items": [],
                "supplement_items": [],
                "general_food_items": [],
                "is_sick": False,
                "sick_note": None,
                "is_injured": False,
                "injury_note": None,
                "medication_items": [],
                "praise_note": None,
                "hard_note": None,
                "lightness_score": None,
                "reaction_score": None,
                "side_score": None,
                "shoulder_score": None,
            }

        workout_items = conn.execute(
            text("""
                SELECT workout_type, minutes, calorie_estimate, detail
                FROM workout_item
                WHERE day_record_id = :day_record_id
                ORDER BY workout_item_id
            """),
            {"day_record_id": day_record_id}
        ).mappings().all()

        food_items = conn.execute(
            text("""
                SELECT protein_items, carb_items, fat_items, supplement_items, general_food_items
                FROM body_record
                WHERE day_record_id = :day_record_id
            """),
            {"day_record_id": day_record_id}
        ).mappings().first()

        day_row = conn.execute(
            text(
                "SELECT is_sick, sick_note, is_injured, injury_note, medication_items, "
                "praise_note, hard_note "
                "FROM day_record WHERE day_record_id = :day_record_id"
            ),
            {"day_record_id": day_record_id}
        ).mappings().first()

        gk_row = conn.execute(
            text(
                "SELECT lightness_score, reaction_score, side_score, shoulder_score "
                "FROM gk_record WHERE day_record_id = :day_record_id"
            ),
            {"day_record_id": day_record_id}
        ).mappings().first()

    return {
        "workout_items": [dict(row) for row in workout_items],
        "protein_items": (food_items["protein_items"] if food_items else None) or [],
        "carb_items": (food_items["carb_items"] if food_items else None) or [],
        "fat_items": (food_items["fat_items"] if food_items else None) or [],
        "supplement_items": (food_items["supplement_items"] if food_items else None) or [],
        "general_food_items": (food_items["general_food_items"] if food_items else None) or [],
        "is_sick": day_row["is_sick"] if day_row else False,
        "sick_note": (day_row["sick_note"] if day_row else None),
        "is_injured": day_row["is_injured"] if day_row else False,
        "injury_note": (day_row["injury_note"] if day_row else None),
        "medication_items": (day_row["medication_items"] if day_row else None) or [],
        "praise_note": (day_row["praise_note"] if day_row else None),
        "hard_note": (day_row["hard_note"] if day_row else None),
        "lightness_score": (gk_row["lightness_score"] if gk_row else None),
        "reaction_score": (gk_row["reaction_score"] if gk_row else None),
        "side_score": (gk_row["side_score"] if gk_row else None),
        "shoulder_score": (gk_row["shoulder_score"] if gk_row else None),
    }


def get_active_goal(conn=None):
    sql = text("""
        SELECT
            target_weight_kg,
            target_water_liter,
            target_protein_kcal,
            target_carb_kcal,
            target_fat_kcal,
            target_calorie
        FROM user_goal
        WHERE goal_status = 'ACTIVE'
        ORDER BY started_at DESC
        LIMIT 1
    """)

    with (nullcontext(conn) if conn is not None else engine.connect()) as conn:
        row = conn.execute(sql).mappings().first()

    return dict(row) if row else None
