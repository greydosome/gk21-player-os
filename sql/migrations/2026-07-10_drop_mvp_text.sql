-- STEP-051: remove 오늘의 한마디 (MVP text) feature entirely, including stored data

BEGIN;

ALTER TABLE day_record DROP COLUMN mvp_text;

DROP TABLE IF EXISTS mvp_suggestion_cache;

COMMIT;
