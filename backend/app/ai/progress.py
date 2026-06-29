
def _to_float(value):

    if value is None:

        return None

    return float(value)

def _round(value, digits=2):

    if value is None:

        return None

    return round(value, digits)

def calculate_goal_progress(context):

    today = context.get("today") or {}

    goal = context.get("goal") or {}

    history = context.get("history") or []

    current_weight = _to_float(today.get("weight_kg"))

    target_weight = _to_float(goal.get("target_weight_kg"))

    current_waist = _to_float(today.get("waist_cm"))

    target_waist = _to_float(goal.get("target_waist_cm"))

    weekly_workout_goal = goal.get("weekly_workout_goal")

    weekly_workout_done = sum(

        1

        for row in history[:7]

        if row.get("workout_done_yn") is True

    )

    remaining_weight = None

    if current_weight is not None and target_weight is not None:

        remaining_weight = _round(current_weight - target_weight)

    remaining_waist = None

    if current_waist is not None and target_waist is not None:

        remaining_waist = _round(current_waist - target_waist)

    weekly_workout_percent = None

    if weekly_workout_goal:

        weekly_workout_percent = _round(

            weekly_workout_done / weekly_workout_goal * 100,

            1

        )

    return {

        "today": {

            "score": today.get("score"),

            "workout_done_yn": today.get("workout_done_yn"),

            "protein_gram": today.get("protein_gram"),

            "water_liter": _to_float(today.get("water_liter")),

            "sleep_hours": _to_float(today.get("sleep_hours")),

            "meal_score": today.get("meal_score"),

        },

        "this_week": {

            "weekly_workout_goal": weekly_workout_goal,

            "weekly_workout_done": weekly_workout_done,

            "weekly_workout_percent": weekly_workout_percent,

            "remaining_workout_count": (

                max(weekly_workout_goal - weekly_workout_done, 0)

                if weekly_workout_goal is not None

                else None

            ),

        },

        "long_term": {

            "current_weight_kg": current_weight,

            "target_weight_kg": target_weight,

            "remaining_weight_kg": remaining_weight,

            "current_waist_cm": current_waist,

            "target_waist_cm": target_waist,

            "remaining_waist_cm": remaining_waist,

            "goal_type": goal.get("goal_type"),

            "workout_style": goal.get("workout_style"),

        },

    }

