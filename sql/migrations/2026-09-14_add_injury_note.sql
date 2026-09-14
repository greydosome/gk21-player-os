-- add injury_note free-text field to day_record, paired with is_injured (parallel to medication_note)

ALTER TABLE day_record ADD COLUMN IF NOT EXISTS injury_note TEXT;
COMMENT ON COLUMN day_record.injury_note IS '다친 날에 어디를 다쳤는지 자유 입력 메모';
