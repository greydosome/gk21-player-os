
import json

from sqlalchemy import text

MAIN_ANALYSIS_KEYS = {

    "overall_score",

    "summary",

    "strength",

    "weakness",

    "next_goal",

    "body_comment",

    "workout_comment",

    "meal_comment",

    "sleep_comment",

    "confidence",

}

DETAIL_ANALYSIS_KEYS = {

    "today_card",

    "week_card",

    "goal_card",

    "coach_card",

    "recommended_exercises",

    "nutrition_focus",

    "risk_factors",

    "motivation",

}

def _build_analysis_detail(analysis):

    if not analysis:

        return {}

    return {

        key: analysis.get(key)

        for key in DETAIL_ANALYSIS_KEYS

        if key in analysis

    }

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

            "protein_kcal": today.get("protein_kcal"),

            "carb_kcal": today.get("carb_kcal"),

            "fat_kcal": today.get("fat_kcal"),

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

        "goal_progress": context.get("goal_progress"),

    }

def save_ai_analysis(conn, day_record_id, context, metrics, analysis):

    input_snapshot = build_input_snapshot(context, metrics)

    params = {

        "day_record_id": day_record_id,

        "analysis_type": "DAILY",

        "lookback_days": metrics.get("days_30_count") or metrics.get("days_7_count") or 1,

        "provider": "RULE",

        "model_name": "rule-engine-v1",

        "prompt_version": "rule-v1",

        "ai_status": "RULE_DONE",

        "confidence": 100,

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

    }

    conn.execute(

        text("""

            INSERT INTO ai_analysis

            (

                day_record_id,

                analysis_type,

                lookback_days,

                provider,

                model_name,

                prompt_version,

                ai_status,

                confidence,

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

                started_at,

                completed_at

            )

            VALUES

            (

                :day_record_id,

                :analysis_type,

                :lookback_days,

                :provider,

                :model_name,

                :prompt_version,

                :ai_status,

                :confidence,

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

                now(),

                now()

            )

            ON CONFLICT (day_record_id, analysis_type)

            DO UPDATE SET

                lookback_days = EXCLUDED.lookback_days,

                provider = EXCLUDED.provider,

                model_name = EXCLUDED.model_name,

                prompt_version = EXCLUDED.prompt_version,

                ai_status = EXCLUDED.ai_status,

                confidence = EXCLUDED.confidence,

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

                started_at = now(),

                completed_at = now(),

                error_message = NULL,

                updated_at = now()

        """),

        params

    )

def mark_ai_analysis_running(conn, day_record_id):

    conn.execute(

        text("""

            UPDATE ai_analysis

            SET

                ai_status = 'GPT_RUNNING',

                started_at = now(),

                completed_at = NULL,

                error_message = NULL,

                updated_at = now()

            WHERE day_record_id = :day_record_id

              AND analysis_type = 'DAILY'

        """),

        {"day_record_id": day_record_id}

    )

def update_ai_analysis_from_llm(conn, day_record_id, llm_result):

    analysis = llm_result.get("analysis") or {}

    analysis_detail = _build_analysis_detail(analysis)

    params = {

        "day_record_id": day_record_id,

        "analysis_type": "DAILY",

        "provider": llm_result.get("provider"),

        "model_name": llm_result.get("model_name"),

        "prompt_version": llm_result.get("prompt_version"),

        "latency_ms": llm_result.get("latency_ms"),

        "token_input": llm_result.get("token_input"),

        "token_output": llm_result.get("token_output"),

        "overall_score": analysis.get("overall_score"),

        "summary": analysis.get("summary"),

        "strength": analysis.get("strength"),

        "weakness": analysis.get("weakness"),

        "next_goal": analysis.get("next_goal"),

        "body_comment": analysis.get("body_comment"),

        "workout_comment": analysis.get("workout_comment"),

        "meal_comment": analysis.get("meal_comment"),

        "sleep_comment": analysis.get("sleep_comment"),

        "confidence": analysis.get("confidence"),

        "analysis_detail": json.dumps(analysis_detail, ensure_ascii=False, default=str),

    }

    conn.execute(

        text("""

            UPDATE ai_analysis

            SET

                provider = :provider,

                model_name = :model_name,

                prompt_version = :prompt_version,

                ai_status = 'COMPLETED',

                latency_ms = :latency_ms,

                token_input = :token_input,

                token_output = :token_output,

                overall_score = :overall_score,

                summary = :summary,

                strength = :strength,

                weakness = :weakness,

                next_goal = :next_goal,

                body_comment = :body_comment,

                workout_comment = :workout_comment,

                meal_comment = :meal_comment,

                sleep_comment = :sleep_comment,

                confidence = :confidence,

                analysis_detail = CAST(:analysis_detail AS jsonb),

                completed_at = now(),

                error_message = NULL,

                updated_at = now()

            WHERE day_record_id = :day_record_id

              AND analysis_type = :analysis_type

        """),

        params

    )

def mark_ai_analysis_failed(conn, day_record_id, error_message):

    conn.execute(

        text("""

            UPDATE ai_analysis

            SET

                ai_status = 'RULE_DONE',

                error_message = :error_message,

                completed_at = now(),

                updated_at = now()

            WHERE day_record_id = :day_record_id

              AND analysis_type = 'DAILY'

        """),

        {

            "day_record_id": day_record_id,

            "error_message": str(error_message)[:2000],

        }

    )

