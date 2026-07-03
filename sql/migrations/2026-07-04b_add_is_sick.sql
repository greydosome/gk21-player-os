-- STEP-040: add is_sick flag to day_record for "sick day" override state

ALTER TABLE day_record ADD COLUMN is_sick BOOLEAN NOT NULL DEFAULT false;
COMMENT ON COLUMN day_record.is_sick IS '아픈 날 여부 - 오늘 상태 카드에서 등급 대신 별도 메시지로 표시';
