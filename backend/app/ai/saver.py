
import json

from sqlalchemy import text

def build_input_snapshot(context, metrics):

    today = context.get("today") or {}

    return {

        "target_date": context.get("target_date"),

        "today": {

            "day_record_id": today.get("day_record_id"),

            "record_date": str(today.get("record_date")) if today.get("record_date") else None,

            "score": today.get("score"),

            "grade": today.get("grade"),

            "mood_score": today.get("mood_score"),

            "weight_kg": float(today.get("weight_kg")) if today.get("weight_kg") is not None else None,

            "waist_cm": float(today.get("waist_cm")) if today.get("waist_cm") is not None else None,

            "water_liter": float(today.get("water_liter")) if today.get("water_liter") is not None else None,

            "protein_gram": today.get("protein_gram"),

            "binge_yn": today.get("binge_yn"),

            "workout_done_yn": today.get("workout_done_yn"),

            "bike_minutes": today.get("bike_minutes"),

            "meal_score": today.get("meal_score"),

            "total_calorie": today.get("total_calorie"),

            "sleep_hours": float(today.get("sleep_hours")) if today.get("sleep_hours") is not None else None,

            "sleep_quality_score": today.get("sleep_quality_score"),

            "wake_condition": today.get("wake_condition"),

        },

        "metrics": metrics,

    }

def save_ai_analysis(conn, day_record_id, context, metrics, analysis):

    input_snapshot = build_input_snapshot(context, metrics)

    params = {

        "day_record_id": day_record_id,

        "analysis_type": "DAILY",

        "lookback_days": metrics.get("days_30_count") or metrics.get("days_7_count") or 1,

        "overall_score": analysis.get("overall_score"),

        "summary": analysis.get("summary"),

        "strength": analysis.get("strength"),

        "weakness": analysis.get("weakness"),

        "next_goal": analysis.get("next_goal"),

        "body_comment": analysis.get("body_comment"),

        "workout_comment": analysis.get("workout_comment"),

        "meal_comment": analysis.get("meal_comment"),

        "sleep_comment": analysis.get("sleep_comment"),

        "input_snapshot": json.dumps(input_snapshot, ensure_ascii=False, default=str),

        "model_name": "rule-engine-v1",

        "prompt_version": "rule-v1",

    }

    conn.execute(

        text("""

            INSERT INTO ai_analysis

            (

                day_record_id,

                analysis_type,

                lookback_days,

                overall_score,

                summary,

                strength,

                weakness,

                next_goal,

                body_comment,

                workout_comment,

                meal_comment,

                sleep_comment,

                input_snapshot,

                model_name,

                prompt_version

            )

            VALUES

            (

                :day_record_id,

                :analysis_type,

                :lookback_days,

                :overall_score,

                :summary,

                :strength,

                :weakness,

                :next_goal,

                :body_comment,

                :workout_comment,

                :meal_comment,

                :sleep_comment,

                CAST(:input_snapshot AS jsonb),

                :model_name,

                :prompt_version

            )

            ON CONFLICT (day_record_id, analysis_type)

            DO UPDATE SET

                lookback_days = EXCLUDED.lookback_days,

                overall_score = EXCLUDED.overall_score,

                summary = EXCLUDED.summary,

                strength = EXCLUDED.strength,

                weakness = EXCLUDED.weakness,

                next_goal = EXCLUDED.next_goal,

                body_comment = EXCLUDED.body_comment,

                workout_comment = EXCLUDED.workout_comment,

                meal_comment = EXCLUDED.meal_comment,

                sleep_comment = EXCLUDED.sleep_comment,

                input_snapshot = EXCLUDED.input_snapshot,

                model_name = EXCLUDED.model_name,

                prompt_version = EXCLUDED.prompt_version,

                updated_at = now()

        """),

        params

    )

