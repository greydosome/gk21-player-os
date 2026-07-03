from datetime import timedelta

from sqlalchemy import text

from app.db.session import engine


def get_period_stats(end_date, days):
    start_date = end_date - timedelta(days=days - 1)

    sql = text("""
        SELECT
            COUNT(*) AS days_logged,
            AVG(sleep_hours) AS avg_sleep_hours,
            AVG(water_liter) AS avg_water_liter,
            AVG(protein_gram) AS avg_protein_gram,
            AVG(mood_score) AS avg_mood_score,
            SUM(CASE WHEN workout_done_yn THEN 1 ELSE 0 END) AS workout_days,
            SUM(CASE WHEN morning_med_taken AND evening_med_taken THEN 1 ELSE 0 END) AS full_medication_days,
            SUM(CASE WHEN binge_yn THEN 1 ELSE 0 END) AS binge_days
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
