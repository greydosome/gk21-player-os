-- STEP-042: cache table for daily AI-generated "오늘의 한마디" suggestion phrases

CREATE TABLE mvp_suggestion_cache (
    record_date DATE PRIMARY KEY,
    suggestions JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE mvp_suggestion_cache IS '날짜별 AI 생성 오늘의 한마디 추천 문구 캐시';
