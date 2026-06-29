from app.ai.context import get_ai_context
from app.ai.llm import call_ai
from app.ai.metrics import calculate_ai_metrics
from app.ai.prompt_builder import build_prompt
from app.ai.rule_engine import build_daily_rule_analysis
from app.ai.saver import mark_ai_analysis_failed
from app.ai.saver import mark_ai_analysis_running
from app.ai.saver import save_ai_analysis
from app.ai.saver import update_ai_analysis_from_llm
from app.db.session import engine


def generate_daily_rule_analysis(conn, day_record_id, record_date):
    context = get_ai_context(record_date)
    metrics = calculate_ai_metrics(context)
    rule_analysis = build_daily_rule_analysis(context, metrics)

    save_ai_analysis(
        conn=conn,
        day_record_id=day_record_id,
        context=context,
        metrics=metrics,
        analysis=rule_analysis
    )


def run_daily_llm_analysis(day_record_id, record_date):
    try:
        with engine.begin() as conn:
            mark_ai_analysis_running(conn, day_record_id)

        context = get_ai_context(record_date)
        metrics = calculate_ai_metrics(context)
        prompt = build_prompt(context, metrics)
        llm_result = call_ai(prompt)

        with engine.begin() as conn:
            update_ai_analysis_from_llm(
                conn=conn,
                day_record_id=day_record_id,
                llm_result=llm_result
            )

    except Exception as exc:
        with engine.begin() as conn:
            mark_ai_analysis_failed(
                conn=conn,
                day_record_id=day_record_id,
                error_message=exc
            )
