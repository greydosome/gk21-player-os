BEGIN;
CREATE TABLE IF NOT EXISTS workout_conversation_report (
    source_message_id TEXT PRIMARY KEY,
    record_date DATE NOT NULL REFERENCES day_record(record_date) ON DELETE CASCADE,
    reported_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS workout_conversation_report_day ON workout_conversation_report(record_date);
COMMIT;
