from datetime import timedelta

from sqlalchemy import text

from app.db.session import engine


def get_period_stats(end_date, days):
    start_date = end_date - timedelta(days=days - 1)

    sql = text("""
        SELECT
            COUNT(*) AS days_logged,
            AVG(weight_kg) AS avg_weight_kg,
            AVG(sleep_hours) AS avg_sleep_hours,
            AVG(water_liter) AS avg_water_liter,
            AVG(protein_kcal) AS avg_protein_kcal,
            AVG(carb_kcal) AS avg_carb_kcal,
            AVG(fat_kcal) AS avg_fat_kcal,
            AVG(mood_score) AS avg_mood_score,
            COALESCE(SUM(CASE WHEN workout_done_yn THEN 1 ELSE 0 END), 0) AS workout_days,
            COALESCE(SUM(CASE WHEN morning_med_taken AND evening_med_taken THEN 1 ELSE 0 END), 0) AS full_medication_days,
            COALESCE(SUM(CASE WHEN binge_yn THEN 1 ELSE 0 END), 0) AS binge_days
        FROM v_day_record_summary
        WHERE record_date BETWEEN :start_date AND :end_date
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, {"start_date": start_date, "end_date": end_date}).mappings().first()

    result = dict(row) if row else {}
    result["start_date"] = str(start_date)
    result["end_date"] = str(end_date)
    result["period_days"] = days

    return result


def get_period_history(end_date, days):
    start_date = end_date - timedelta(days=days - 1)

    sql = text("""
        SELECT
            gs.day::date AS record_date,
            v.weight_kg,
            v.sleep_hours,
            v.water_liter,
            v.protein_kcal,
            v.carb_kcal,
            v.fat_kcal,
            v.workout_done_yn,
            v.mood_score,
            v.binge_yn
        FROM generate_series(:start_date, :end_date, interval '1 day') AS gs(day)
        LEFT JOIN v_day_record_summary v ON v.record_date = gs.day::date
        ORDER BY gs.day
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"start_date": start_date, "end_date": end_date}).mappings().all()

    return [dict(row) for row in rows]
