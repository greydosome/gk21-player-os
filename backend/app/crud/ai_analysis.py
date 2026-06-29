
from datetime import date

from sqlalchemy import text

from app.db.session import engine

def _build_ai_response(row):

    if row is None:

        return None

    data = dict(row)

    detail = data.get("analysis_detail") or {}

    return {

        "analysis_id": data.get("analysis_id"),

        "analysis_type": data.get("analysis_type"),

        "lookback_days": data.get("lookback_days"),

        "provider": data.get("provider"),

        "model_name": data.get("model_name"),

        "prompt_version": data.get("prompt_version"),

        "ai_status": data.get("ai_status"),

        "overall_score": data.get("overall_score"),

        "confidence": data.get("confidence"),

        "summary": data.get("summary"),

        "strength": data.get("strength"),

        "weakness": data.get("weakness"),

        "next_goal": data.get("next_goal"),

        "comments": {

            "body": data.get("body_comment"),

            "workout": data.get("workout_comment"),

            "meal": data.get("meal_comment"),

            "sleep": data.get("sleep_comment"),

        },

        "cards": {

            "today": detail.get("today_card"),

            "week": detail.get("week_card"),

            "goal": detail.get("goal_card"),

            "coach": detail.get("coach_card"),

        },

        "recommendations": {

            "exercises": detail.get("recommended_exercises") or [],

            "nutrition_focus": detail.get("nutrition_focus") or [],

            "risk_factors": detail.get("risk_factors") or [],

            "motivation": detail.get("motivation"),

        },

        "usage": {

            "latency_ms": data.get("latency_ms"),

            "token_input": data.get("token_input"),

            "token_output": data.get("token_output"),

            "cost_usd": data.get("cost_usd"),

        },

        "error_message": data.get("error_message"),

        "created_at": data.get("created_at"),

        "updated_at": data.get("updated_at"),

    }

def get_daily_ai_analysis(target_date: date):

    sql = text("""

        SELECT

            a.analysis_id,

            a.analysis_type,

            a.lookback_days,

            a.provider,

            a.model_name,

            a.prompt_version,

            a.ai_status,

            a.confidence,

            a.overall_score,

            a.summary,

            a.strength,

            a.weakness,

            a.next_goal,

            a.body_comment,

            a.workout_comment,

            a.meal_comment,

            a.sleep_comment,

            a.analysis_detail,

            a.latency_ms,

            a.token_input,

            a.token_output,

            a.cost_usd,

            a.error_message,

            a.created_at,

            a.updated_at

        FROM ai_analysis a

        JOIN day_record d

          ON a.day_record_id = d.day_record_id

        WHERE d.record_date = :record_date

          AND a.analysis_type = 'DAILY'

        LIMIT 1

    """)

    with engine.connect() as conn:

        row = conn.execute(

            sql,

            {

                "record_date": target_date

            }

        ).mappings().first()

    return _build_ai_response(row)

