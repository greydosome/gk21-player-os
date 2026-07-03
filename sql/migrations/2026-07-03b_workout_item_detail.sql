-- STEP-036: add detail column to workout_item for specific exercises within a category

ALTER TABLE workout_item ADD COLUMN detail TEXT;
COMMENT ON COLUMN workout_item.detail IS '세부 운동 목록 (예: 랫풀다운, 티바로우)';
