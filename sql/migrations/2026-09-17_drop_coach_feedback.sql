-- "코치 피드백" 빈 텍스트박스 기능을 뺐다. AI 코치가 이미 ai_analysis 테이블에 결과를
-- 저장하고 있어서, 사람이 따로 붙여넣어 보관하는 이 필드는 실사용 가치가 없다고 판단.
-- 실제 데이터가 없었음을 확인 후(count=0) 컬럼을 드롭한다.

ALTER TABLE day_record DROP COLUMN IF EXISTS coach_feedback;
