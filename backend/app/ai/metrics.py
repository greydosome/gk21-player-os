
def _safe_float(value):

    if value is None:

        return None

    return float(value)

def _avg(values):

    clean_values = [

        _safe_float(value)

        for value in values

        if value is not None

    ]

    if not clean_values:

        return None

    return round(sum(clean_values) / len(clean_values), 2)

def _count_true(values):

    return sum(1 for value in values if value is True)

def calculate_ai_metrics(context):

    recent_7_days = context.get("recent_7_days") or []

    recent_30_days = context.get("recent_30_days") or []

    weight_values_7 = [row.get("weight_kg") for row in recent_7_days]

    sleep_values_7 = [row.get("sleep_hours") for row in recent_7_days]

    meal_score_values_7 = [row.get("meal_score") for row in recent_7_days]

    score_values_7 = [row.get("score") for row in recent_7_days]

    workout_values_7 = [row.get("workout_done_yn") for row in recent_7_days]

    weight_values_30 = [row.get("weight_kg") for row in recent_30_days]

    sleep_values_30 = [row.get("sleep_hours") for row in recent_30_days]

    meal_score_values_30 = [row.get("meal_score") for row in recent_30_days]

    score_values_30 = [row.get("score") for row in recent_30_days]

    workout_values_30 = [row.get("workout_done_yn") for row in recent_30_days]

    weight_change_7 = None

    if len(weight_values_7) >= 2 and weight_values_7[0] is not None and weight_values_7[-1] is not None:

        weight_change_7 = round(float(weight_values_7[0]) - float(weight_values_7[-1]), 2)

    weight_change_30 = None

    if len(weight_values_30) >= 2 and weight_values_30[0] is not None and weight_values_30[-1] is not None:

        weight_change_30 = round(float(weight_values_30[0]) - float(weight_values_30[-1]), 2)

    return {

        "days_7_count": len(recent_7_days),

        "days_30_count": len(recent_30_days),

        "avg_score_7": _avg(score_values_7),

        "avg_sleep_hours_7": _avg(sleep_values_7),

        "avg_meal_score_7": _avg(meal_score_values_7),

        "workout_days_7": _count_true(workout_values_7),

        "weight_change_7": weight_change_7,

        "avg_score_30": _avg(score_values_30),

        "avg_sleep_hours_30": _avg(sleep_values_30),

        "avg_meal_score_30": _avg(meal_score_values_30),

        "workout_days_30": _count_true(workout_values_30),

        "weight_change_30": weight_change_30,

    }

