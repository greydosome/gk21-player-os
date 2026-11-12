BEGIN;
CREATE TABLE IF NOT EXISTS meal_native_sync (
 record_date date PRIMARY KEY,
 state jsonb NOT NULL,
 revision text NOT NULL
);
COMMIT;
