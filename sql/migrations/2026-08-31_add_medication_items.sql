-- add medication_items to day_record: free-text list of medication names taken that day
-- (same JSONB-array-of-strings convention as body_record.general_food_items)

ALTER TABLE day_record ADD COLUMN IF NOT EXISTS medication_items JSONB;
COMMENT ON COLUMN day_record.medication_items IS '오늘 복용한 약 이름 목록(자유 입력) - CUSTOM 음식 목록과 같은 방식';
