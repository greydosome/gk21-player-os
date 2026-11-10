BEGIN;
ALTER TABLE apple_health_workout ADD COLUMN IF NOT EXISTS record_workout_type TEXT;
ALTER TABLE apple_health_workout ADD COLUMN IF NOT EXISTS record_detail TEXT;
CREATE TABLE IF NOT EXISTS apple_health_record_sync (
    record_date DATE PRIMARY KEY REFERENCES day_record(record_date) ON DELETE CASCADE,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    revision TEXT NOT NULL
);
COMMIT;
