\c gk21

DROP VIEW IF EXISTS v_day_record_summary CASCADE;
DROP TABLE IF EXISTS coach_record CASCADE;
DROP TABLE IF EXISTS gk_record CASCADE;
DROP TABLE IF EXISTS workout_record CASCADE;
DROP TABLE IF EXISTS body_record CASCADE;
DROP TABLE IF EXISTS day_record CASCADE;

CREATE TABLE day_record (
    day_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    record_date DATE NOT NULL DEFAULT CURRENT_DATE,
    score SMALLINT NOT NULL DEFAULT 0,
    grade VARCHAR(10),
    mood_score SMALLINT,
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_day_record PRIMARY KEY (day_record_id),
    CONSTRAINT uk_day_record_record_date UNIQUE (record_date),
    CONSTRAINT ck_day_record_score CHECK (score BETWEEN 0 AND 100)
);

CREATE TABLE body_record (
    body_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    day_record_id BIGINT NOT NULL,
    weight_kg NUMERIC(5,2),
    waist_cm NUMERIC(5,2),
    water_liter NUMERIC(4,1),
    protein_gram SMALLINT,
    binge_yn BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_body_record PRIMARY KEY (body_record_id),
    CONSTRAINT uk_body_record_day_record_id UNIQUE (day_record_id),
    CONSTRAINT fk_body_record_day_record FOREIGN KEY (day_record_id)
        REFERENCES day_record(day_record_id) ON DELETE CASCADE,
    CONSTRAINT ck_body_record_weight_kg CHECK (weight_kg IS NULL OR weight_kg > 0),
    CONSTRAINT ck_body_record_waist_cm CHECK (waist_cm IS NULL OR waist_cm > 0),
    CONSTRAINT ck_body_record_water_liter CHECK (water_liter IS NULL OR water_liter >= 0),
    CONSTRAINT ck_body_record_protein_gram CHECK (protein_gram IS NULL OR protein_gram >= 0)
);

CREATE TABLE workout_record (
    workout_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    day_record_id BIGINT NOT NULL,
    planned_workout TEXT,
    completed_workout TEXT,
    bike_minutes SMALLINT NOT NULL DEFAULT 0,
    workout_done_yn BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_workout_record PRIMARY KEY (workout_record_id),
    CONSTRAINT uk_workout_record_day_record_id UNIQUE (day_record_id),
    CONSTRAINT fk_workout_record_day_record FOREIGN KEY (day_record_id)
        REFERENCES day_record(day_record_id) ON DELETE CASCADE,
    CONSTRAINT ck_workout_record_bike_minutes CHECK (bike_minutes >= 0)
);

CREATE TABLE gk_record (
    gk_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    day_record_id BIGINT NOT NULL,
    lightness_score SMALLINT,
    reaction_score SMALLINT,
    side_score SMALLINT,
    shoulder_score SMALLINT,
    gk_memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_gk_record PRIMARY KEY (gk_record_id),
    CONSTRAINT uk_gk_record_day_record_id UNIQUE (day_record_id),
    CONSTRAINT fk_gk_record_day_record FOREIGN KEY (day_record_id)
        REFERENCES day_record(day_record_id) ON DELETE CASCADE
);

CREATE TABLE coach_record (
    coach_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    day_record_id BIGINT NOT NULL,
    coach_note TEXT,
    ai_summary TEXT,
    next_goal TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_coach_record PRIMARY KEY (coach_record_id),
    CONSTRAINT uk_coach_record_day_record_id UNIQUE (day_record_id),
    CONSTRAINT fk_coach_record_day_record FOREIGN KEY (day_record_id)
        REFERENCES day_record(day_record_id) ON DELETE CASCADE
);

CREATE INDEX ix_day_record_score ON day_record(score);
CREATE INDEX ix_day_record_grade ON day_record(grade);
CREATE INDEX ix_body_record_weight_kg ON body_record(weight_kg);
CREATE INDEX ix_body_record_waist_cm ON body_record(waist_cm);
CREATE INDEX ix_body_record_binge_yn ON body_record(binge_yn);
CREATE INDEX ix_workout_record_bike_minutes ON workout_record(bike_minutes);
CREATE INDEX ix_workout_record_done_yn ON workout_record(workout_done_yn);
CREATE INDEX ix_gk_record_reaction_score ON gk_record(reaction_score);
CREATE INDEX ix_gk_record_lightness_score ON gk_record(lightness_score);

CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_day_record_updated_at
BEFORE UPDATE ON day_record
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_body_record_updated_at
BEFORE UPDATE ON body_record
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_workout_record_updated_at
BEFORE UPDATE ON workout_record
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_gk_record_updated_at
BEFORE UPDATE ON gk_record
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_coach_record_updated_at
BEFORE UPDATE ON coach_record
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

COMMENT ON TABLE day_record IS '일일 기록';
COMMENT ON TABLE body_record IS '신체 및 식단 기록';
COMMENT ON TABLE workout_record IS '운동 기록';
COMMENT ON TABLE gk_record IS '골키퍼 훈련 기록';
COMMENT ON TABLE coach_record IS '코치 피드백 기록';

COMMENT ON COLUMN day_record.day_record_id IS '일일 기록 ID';
COMMENT ON COLUMN day_record.record_date IS '기록일자';
COMMENT ON COLUMN day_record.score IS '점수';
COMMENT ON COLUMN day_record.grade IS '등급';
COMMENT ON COLUMN day_record.mood_score IS '기분 점수';
COMMENT ON COLUMN day_record.memo IS '메모';
COMMENT ON COLUMN day_record.created_at IS '생성일시';
COMMENT ON COLUMN day_record.updated_at IS '수정일시';

COMMENT ON COLUMN body_record.body_record_id IS '신체 기록 ID';
COMMENT ON COLUMN body_record.day_record_id IS '일일 기록 ID';
COMMENT ON COLUMN body_record.weight_kg IS '체중 kg';
COMMENT ON COLUMN body_record.waist_cm IS '허리 cm';
COMMENT ON COLUMN body_record.water_liter IS '물 섭취량 L';
COMMENT ON COLUMN body_record.protein_gram IS '단백질 g';
COMMENT ON COLUMN body_record.binge_yn IS '폭식 여부';

COMMENT ON COLUMN workout_record.workout_record_id IS '운동 기록 ID';
COMMENT ON COLUMN workout_record.planned_workout IS '예정 운동';
COMMENT ON COLUMN workout_record.completed_workout IS '완료 운동';
COMMENT ON COLUMN workout_record.bike_minutes IS '자전거 시간 분';
COMMENT ON COLUMN workout_record.workout_done_yn IS '운동 완료 여부';

COMMENT ON COLUMN gk_record.gk_record_id IS '골키퍼 기록 ID';
COMMENT ON COLUMN gk_record.lightness_score IS '몸 가벼움 점수';
COMMENT ON COLUMN gk_record.reaction_score IS '반응 점수';
COMMENT ON COLUMN gk_record.side_score IS '사이드 움직임 점수';
COMMENT ON COLUMN gk_record.shoulder_score IS '어깨 상태 점수';
COMMENT ON COLUMN gk_record.gk_memo IS '골키퍼 메모';

COMMENT ON COLUMN coach_record.coach_record_id IS '코치 기록 ID';
COMMENT ON COLUMN coach_record.coach_note IS '코치 메모';
COMMENT ON COLUMN coach_record.ai_summary IS 'AI 요약';
COMMENT ON COLUMN coach_record.next_goal IS '다음 목표';

CREATE OR REPLACE VIEW v_day_record_summary AS
SELECT
    ROW_NUMBER() OVER (ORDER BY d.record_date) AS day_no,
    EXTRACT(WEEK FROM d.record_date)::INTEGER AS week_no,
    d.day_record_id,
    d.record_date,
    d.score,
    d.grade,
    d.mood_score,
    b.weight_kg,
    b.waist_cm,
    b.water_liter,
    b.protein_gram,
    b.binge_yn,
    w.bike_minutes,
    w.workout_done_yn,
    g.lightness_score,
    g.reaction_score,
    g.side_score,
    g.shoulder_score,
    c.coach_note,
    c.ai_summary,
    c.next_goal,
    d.memo,
    d.created_at,
    d.updated_at
FROM day_record d
LEFT JOIN body_record b ON b.day_record_id = d.day_record_id
LEFT JOIN workout_record w ON w.day_record_id = d.day_record_id
LEFT JOIN gk_record g ON g.day_record_id = d.day_record_id
LEFT JOIN coach_record c ON c.day_record_id = d.day_record_id;

COMMENT ON VIEW v_day_record_summary IS '일일 기록 통합 조회 뷰';
