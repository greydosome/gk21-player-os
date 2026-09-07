-- add is_injured flag to day_record for "injured day" override state (parallel to is_sick)

ALTER TABLE day_record ADD COLUMN IF NOT EXISTS is_injured BOOLEAN NOT NULL DEFAULT false;
COMMENT ON COLUMN day_record.is_injured IS '다친 날 여부 - 오늘 상태 카드에서 등급 대신 별도 메시지로 표시';
