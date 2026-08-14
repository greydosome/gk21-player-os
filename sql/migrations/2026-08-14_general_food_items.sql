-- STEP-069: body_record.general_food_items — 매크로 미분류 직접입력 음식(일반식) 목록

ALTER TABLE body_record ADD COLUMN general_food_items JSONB;
COMMENT ON COLUMN body_record.general_food_items IS '일반식(매크로 미분류) 직접입력 음식 목록 (name/unit/quantity/total_calorie/calories_per_100g)';
