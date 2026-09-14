-- add sick_note free-text field to day_record, paired with is_sick (parallel to injury_note)

ALTER TABLE day_record ADD COLUMN IF NOT EXISTS sick_note TEXT;
COMMENT ON COLUMN day_record.sick_note IS '아픈 날에 어디가/어떻게 아픈지 자유 입력 메모';
