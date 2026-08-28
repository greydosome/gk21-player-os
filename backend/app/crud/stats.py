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


def get_period_detail(end_date, days):
    # 주간 요약(식단 총합, 요일별 운동 종목)을 만들려면 매크로별 kcal 합계뿐 아니라
    # 보충음식/일반식이 들어있는 general_food_items 원본과, 그날 실제 수행한
    # 운동 종목 목록(workout_item)이 필요하다. 카테고리(유산소/근력) 분류와
    # CUSTOM|... 인코딩 해석은 프론트엔드에 이미 있는 로직을 그대로 재사용하도록
    # 원본 데이터만 넘긴다.
    start_date = end_date - timedelta(days=days - 1)

    day_sql = text("""
        SELECT
            gs.day::date AS record_date,
            d.day_record_id,
            b.general_food_items
        FROM generate_series(:start_date, :end_date, interval '1 day') AS gs(day)
        LEFT JOIN day_record d ON d.record_date = gs.day::date
        LEFT JOIN body_record b ON b.day_record_id = d.day_record_id
        ORDER BY gs.day
    """)

    workout_sql = text("""
        SELECT
            dr.record_date,
            wi.workout_type,
            wi.minutes,
            wi.calorie_estimate,
            wi.detail
        FROM workout_item wi
        JOIN day_record dr ON dr.day_record_id = wi.day_record_id
        WHERE dr.record_date BETWEEN :start_date AND :end_date
        ORDER BY dr.record_date, wi.workout_item_id
    """)

    with engine.connect() as conn:
        day_rows = conn.execute(day_sql, {"start_date": start_date, "end_date": end_date}).mappings().all()
        workout_rows = conn.execute(workout_sql, {"start_date": start_date, "end_date": end_date}).mappings().all()

    workouts_by_date = {}
    for row in workout_rows:
        key = str(row["record_date"])
        workouts_by_date.setdefault(key, []).append({
            "workout_type": row["workout_type"],
            "minutes": row["minutes"],
            "calorie_estimate": row["calorie_estimate"],
            "detail": row["detail"],
        })

    result = []
    for row in day_rows:
        key = str(row["record_date"])
        result.append({
            "record_date": key,
            "general_food_items": row["general_food_items"] or [],
            "workout_items": workouts_by_date.get(key, []),
        })

    return result
