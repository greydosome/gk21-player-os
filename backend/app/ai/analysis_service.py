from app.ai.context import get_ai_context
from app.ai.metrics import calculate_ai_metrics
from app.ai.rule_engine import build_daily_rule_analysis
from app.ai.saver import save_ai_analysis


def generate_daily_ai_analysis(conn, day_record_id, record_date):

    context = get_ai_context(record_date)
    metrics = calculate_ai_metrics(context)
    analysis = build_daily_rule_analysis(context, metrics)

    save_ai_analysis(
        conn=conn,
        day_record_id=day_record_id,
        context=context,
        metrics=metrics,
        analysis=analysis
    )
