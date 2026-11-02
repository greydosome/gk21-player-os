-- Additive migration only. Run explicitly after backup and schema verification.
BEGIN;
CREATE TABLE IF NOT EXISTS apple_health_daily (
    record_date DATE PRIMARY KEY REFERENCES day_record(record_date) ON DELETE CASCADE,
    collected_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    summary JSONB NOT NULL,
    metric_collected_at JSONB NOT NULL,
    content_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apple_health_coaching_run (
    record_date DATE PRIMARY KEY REFERENCES day_record(record_date) ON DELETE CASCADE,
    input_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'superseded')),
    attempts INTEGER NOT NULL DEFAULT 1 CHECK(attempts > 0),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    error_code TEXT
);
COMMIT;
