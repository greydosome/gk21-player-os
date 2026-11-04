-- Minimal per-workout fields only; no routes, heart-rate samples or raw exports.
BEGIN;
CREATE TABLE IF NOT EXISTS apple_health_workout (
    external_id TEXT PRIMARY KEY,
    workout_type TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL CHECK(duration_seconds > 0 AND duration_seconds <= 86400),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK(ended_at > started_at)
);
CREATE INDEX IF NOT EXISTS apple_health_workout_interval_idx ON apple_health_workout(started_at, ended_at);
COMMIT;
