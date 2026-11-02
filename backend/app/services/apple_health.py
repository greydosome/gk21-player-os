import hashlib
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text
from app.core.config import settings


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def save_health(conn, req):
    # Serializes ingestion and coaching publication for this date across processes.
    conn.execute(text("SELECT pg_advisory_xact_lock(2101, :day)"), {"day": req.record_date.toordinal()})
    existing = conn.execute(text("SELECT * FROM apple_health_daily WHERE record_date=:day FOR UPDATE"), {"day": req.record_date}).mappings().first()
    if existing and req.collected_at <= existing["collected_at"]:
        return "ignored_older_or_duplicate"
    summary = req.summary.model_dump(mode="json")
    # Missing means unavailable, never zero or deletion. Keep last known metric.
    previous = dict(existing["summary"]) if existing else {}
    measured_at = dict(existing["metric_collected_at"]) if existing else {}
    for key, value in summary.items():
        if value is not None:
            previous[key] = value
            measured_at[key] = req.collected_at.isoformat()
    fingerprint = digest({"summary": previous, "metric_collected_at": measured_at})
    conn.execute(text("""
        INSERT INTO day_record(record_date) VALUES (:day) ON CONFLICT(record_date) DO NOTHING
    """), {"day": req.record_date})
    conn.execute(text("""
        INSERT INTO apple_health_daily(record_date, collected_at, summary, metric_collected_at, content_hash)
        VALUES (:day, :collected, CAST(:summary AS jsonb), CAST(:times AS jsonb), :hash)
        ON CONFLICT(record_date) DO UPDATE SET collected_at=EXCLUDED.collected_at,
          summary=EXCLUDED.summary, metric_collected_at=EXCLUDED.metric_collected_at,
          content_hash=EXCLUDED.content_hash, received_at=now()
    """), {"day": req.record_date, "collected": req.collected_at, "summary": json.dumps(previous), "times": json.dumps(measured_at), "hash": fingerprint})
    if settings.APPLE_HEALTH_COACHING_ENABLED and (not existing or existing["summary"] != previous):
        conn.execute(text("""UPDATE ai_analysis SET ai_status='RULE_DONE'
            WHERE day_record_id=(SELECT day_record_id FROM day_record WHERE record_date=:day)
            AND analysis_type='DAILY'"""), {"day": req.record_date})
        conn.execute(text("UPDATE apple_health_coaching_run SET status='superseded' WHERE record_date=:day AND status='completed'"), {"day": req.record_date})
    return "updated" if existing else "created"


def read_health(conn, day):
    if not settings.APPLE_HEALTH_ENABLED:
        return {"enabled": False}
    row = conn.execute(text("SELECT * FROM apple_health_daily WHERE record_date=:day"), {"day": day}).mappings().first()
    if not row:
        return {"enabled": True, "status": "missing", "record_date": str(day)}
    result = dict(row)
    result.update(enabled=True, status="synced", source="Apple 건강")
    if datetime.now(ZoneInfo("Asia/Seoul")) - row["collected_at"] > timedelta(hours=24):
        result["status"] = "stale"
    return result


def health_context(conn, day):
    if not settings.APPLE_HEALTH_ENABLED or not settings.APPLE_HEALTH_COACHING_ENABLED:
        return {}
    rows = conn.execute(text("""SELECT record_date, collected_at, summary, metric_collected_at
        FROM apple_health_daily WHERE record_date BETWEEN :day - INTERVAL '29 days' AND :day
        ORDER BY record_date DESC"""), {"day": day}).mappings().all()
    return {"source": "Apple 건강", "days": [dict(row) for row in rows],
            "policy": "Separate reference data; never add to manual workouts. Null means unavailable. Sleep belongs to wake date. Each metric has its own collection time."}
