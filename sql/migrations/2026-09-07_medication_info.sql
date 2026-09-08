-- cache table for AI(OpenAI)-looked-up medication efficacy/side-effect summaries,
-- keyed by medication name so the same drug isn't re-queried every time.

CREATE TABLE IF NOT EXISTS medication_info (
  medication_info_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  known BOOLEAN NOT NULL DEFAULT true,
  efficacy TEXT,
  side_effects TEXT,
  caution TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE medication_info IS 'AI(OpenAI)로 조회한 약 이름별 효능/부작용 요약 캐시 - 같은 약을 다시 조회할 때 재호출 방지';
