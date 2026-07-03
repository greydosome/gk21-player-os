-- STEP-032: workout_item table + day_record.mvp_text + body_record.protein_items

CREATE TABLE workout_item (
    workout_item_id BIGINT GENERATED ALWAYS AS IDENTITY,
    day_record_id BIGINT NOT NULL,
    workout_type TEXT NOT NULL,
    minutes SMALLINT NOT NULL DEFAULT 0,
    calorie_estimate SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_workout_item PRIMARY KEY (workout_item_id),
    CONSTRAINT fk_workout_item_day_record FOREIGN KEY (day_record_id)
        REFERENCES day_record(day_record_id) ON DELETE CASCADE,
    CONSTRAINT ck_workout_item_minutes CHECK (minutes >= 0)
);

CREATE INDEX ix_workout_item_day_record_id ON workout_item (day_record_id);

ALTER TABLE day_record ADD COLUMN mvp_text TEXT;
COMMENT ON COLUMN day_record.mvp_text IS '오늘 MVP / 칭찬 포인트';

ALTER TABLE body_record ADD COLUMN protein_items JSONB;
COMMENT ON COLUMN body_record.protein_items IS '선택한 단백질 음식 목록';
