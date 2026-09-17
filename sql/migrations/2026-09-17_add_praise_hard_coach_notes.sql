-- "오늘 칭찬 포인트/MVP 후보", "오늘 힘들었던 것", "코치 피드백 저장" 자유 입력 필드 추가.
-- gk_record(lightness_score 등)는 이미 존재하지만 프론트엔드에 입력 UI가 없어 실제로는
-- 한 번도 쓰인 적이 없었다 — 이번에 함께 프론트엔드에 연결한다(테이블/컬럼 추가는 불필요).

ALTER TABLE day_record ADD COLUMN IF NOT EXISTS praise_note TEXT;
ALTER TABLE day_record ADD COLUMN IF NOT EXISTS hard_note TEXT;
ALTER TABLE day_record ADD COLUMN IF NOT EXISTS coach_feedback TEXT;

COMMENT ON COLUMN day_record.praise_note IS '오늘 칭찬 포인트 / MVP 후보';
COMMENT ON COLUMN day_record.hard_note IS '오늘 힘들었던 것';
COMMENT ON COLUMN day_record.coach_feedback IS '코치(사람 또는 ChatGPT) 피드백을 붙여넣어 DAY 기록과 함께 저장';
