"""Durable run metadata + PostgreSQL locks; reuse the existing coach and output."""
import copy
import json
from sqlalchemy import text
from app.ai.context import get_ai_context
from app.ai.metrics import calculate_ai_metrics
from app.ai.prompt_builder import build_prompt
from app.ai.rule_engine import build_daily_rule_analysis
from app.ai.saver import save_ai_analysis, mark_ai_analysis_running, update_ai_analysis_from_llm, mark_ai_analysis_failed
from app.ai.llm import call_ai
from app.core.config import settings
from app.db.session import engine
from app.services.apple_health import digest


def prepare(conn, day):
    context = get_ai_context(day, conn=conn)
    metrics = calculate_ai_metrics(context)
    prompt = build_prompt(context, metrics)
    # Collection timestamps refresh the UI but identical measurements need no new LLM call.
    fingerprint_context = copy.deepcopy(context)
    for row in fingerprint_context.get("apple_health", {}).get("days", []):
        row.pop("collected_at", None)
        row.pop("metric_collected_at", None)
    fingerprint = digest([build_prompt(fingerprint_context, metrics), settings.AI_MODEL, settings.AI_PROMPT_VERSION])
    return context, metrics, prompt, fingerprint


def run_health_coaching(day):
    if not (settings.APPLE_HEALTH_ENABLED and settings.APPLE_HEALTH_COACHING_ENABLED):
        return "disabled"
    with engine.connect() as lock_conn:
        acquired = lock_conn.execute(text("SELECT pg_try_advisory_lock(2102, :day)"), {"day": day.toordinal()}).scalar()
        lock_conn.commit()
        if not acquired:
            return "busy"
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT pg_advisory_xact_lock(2101, :day)"), {"day": day.toordinal()})
                day_id = conn.execute(text("SELECT day_record_id FROM day_record WHERE record_date=:day"), {"day": day}).scalar()
                if not day_id:
                    return "missing"
                context, metrics, prompt, fingerprint = prepare(conn, day)
                previous = conn.execute(text("SELECT * FROM apple_health_coaching_run WHERE record_date=:day"), {"day": day}).mappings().first()
                if previous and previous["status"] == "completed" and previous["input_hash"] == fingerprint:
                    return "unchanged"
                same_input = previous and previous["input_hash"] == fingerprint
                attempts = previous["attempts"] + 1 if same_input else 1
                if attempts > 3:
                    return "retry_limit"
                conn.execute(text("""INSERT INTO apple_health_coaching_run(record_date,input_hash,status,attempts)
                    VALUES (:day,:hash,'running',:attempts) ON CONFLICT(record_date) DO UPDATE SET
                    input_hash=EXCLUDED.input_hash,status='running',attempts=EXCLUDED.attempts,attempted_at=now(),completed_at=NULL,error_code=NULL"""), {"day": day, "hash": fingerprint, "attempts": attempts})
                save_ai_analysis(conn, day_id, context, metrics, build_daily_rule_analysis(context, metrics))
                mark_ai_analysis_running(conn, day_id)
            try:
                result = call_ai(prompt)
                with engine.begin() as conn:
                    conn.execute(text("SELECT pg_advisory_xact_lock(2101, :day)"), {"day": day.toordinal()})
                    if prepare(conn, day)[3] != fingerprint:
                        conn.execute(text("UPDATE apple_health_coaching_run SET status='superseded' WHERE record_date=:day"), {"day": day})
                        mark_ai_analysis_failed(conn, day_id, "INPUT_CHANGED")
                        return "superseded"
                    update_ai_analysis_from_llm(conn, day_id, result)
                    conn.execute(text("""UPDATE ai_analysis SET input_snapshot=CAST(:snapshot AS jsonb)
                        WHERE day_record_id=:id AND analysis_type='DAILY'"""),
                        {"id": day_id, "snapshot": json.dumps({"input_hash": fingerprint, "health_included": True})})
                    conn.execute(text("UPDATE apple_health_coaching_run SET status='completed',completed_at=now() WHERE record_date=:day"), {"day": day})
                return "completed"
            except Exception:
                with engine.begin() as conn:
                    conn.execute(text("UPDATE apple_health_coaching_run SET status='failed',error_code='COACHING_FAILED' WHERE record_date=:day"), {"day": day})
                    mark_ai_analysis_failed(conn, day_id, "COACHING_FAILED")
                return "failed"
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(2102, :day)"), {"day": day.toordinal()})
            lock_conn.commit()
