from datetime import date

from sqlalchemy import text

from app.db.session import engine


def get_dashboard(record_date: date):
    sql = text("""
        SELECT *
        FROM v_dashboard
        WHERE record_date = :record_date
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(
            sql,
            {"record_date": record_date}
        ).mappings().first()

    return dict(row) if row else None


def get_day_detail(record_date: date):
    with engine.connect() as conn:
        day_record_id = conn.execute(
            text("SELECT day_record_id FROM day_record WHERE record_date = :record_date"),
            {"record_date": record_date}
        ).scalar()

        if not day_record_id:
            return {"workout_items": [], "protein_items": [], "mvp_text": None, "is_sick": False}

        workout_items = conn.execute(
            text("""
                SELECT workout_type, minutes, detail
                FROM workout_item
                WHERE day_record_id = :day_record_id
                ORDER BY workout_item_id
            """),
            {"day_record_id": day_record_id}
        ).mappings().all()

        protein_items = conn.execute(
            text("SELECT protein_items FROM body_record WHERE day_record_id = :day_record_id"),
            {"day_record_id": day_record_id}
        ).scalar()

        day_row = conn.execute(
            text("SELECT mvp_text, is_sick FROM day_record WHERE day_record_id = :day_record_id"),
            {"day_record_id": day_record_id}
        ).mappings().first()

    return {
        "workout_items": [dict(row) for row in workout_items],
        "protein_items": protein_items or [],
        "mvp_text": day_row["mvp_text"] if day_row else None,
        "is_sick": day_row["is_sick"] if day_row else False,
    }


def get_active_goal():
    sql = text("""
        SELECT target_weight_kg, target_water_liter, target_protein_gram, target_calorie
        FROM user_goal
        WHERE goal_status = 'ACTIVE'
        ORDER BY started_at DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(sql).mappings().first()

    return dict(row) if row else None
