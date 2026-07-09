-- STEP-046: kcal-based macro tracking (protein switches g->kcal, adds carb/fat goals + food logging, supplement checklist)
-- Must drop/recreate dependent views (v_dashboard depends on v_day_record_summary, which depends on protein_gram)

BEGIN;

ALTER TABLE user_goal
    ADD COLUMN target_protein_kcal SMALLINT,
    ADD COLUMN target_carb_kcal SMALLINT,
    ADD COLUMN target_fat_kcal SMALLINT;

COMMENT ON COLUMN user_goal.target_protein_kcal IS '단백질 목표 kcal';
COMMENT ON COLUMN user_goal.target_carb_kcal IS '탄수화물 목표 kcal';
COMMENT ON COLUMN user_goal.target_fat_kcal IS '지방 목표 kcal';

UPDATE user_goal
SET target_protein_kcal = 430,
    target_carb_kcal = 700,
    target_fat_kcal = 160
WHERE goal_status = 'ACTIVE';

DROP VIEW IF EXISTS v_dashboard;
DROP VIEW IF EXISTS v_day_record_summary;

ALTER TABLE body_record
    ADD COLUMN protein_kcal SMALLINT,
    ADD COLUMN carb_items JSONB,
    ADD COLUMN carb_kcal SMALLINT,
    ADD COLUMN fat_items JSONB,
    ADD COLUMN fat_kcal SMALLINT,
    ADD COLUMN supplement_items JSONB,
    ADD CONSTRAINT ck_body_record_protein_kcal CHECK (protein_kcal IS NULL OR protein_kcal >= 0),
    ADD CONSTRAINT ck_body_record_carb_kcal CHECK (carb_kcal IS NULL OR carb_kcal >= 0),
    ADD CONSTRAINT ck_body_record_fat_kcal CHECK (fat_kcal IS NULL OR fat_kcal >= 0);

COMMENT ON COLUMN body_record.protein_kcal IS '단백질 kcal';
COMMENT ON COLUMN body_record.carb_items IS '선택한 탄수화물 음식 목록';
COMMENT ON COLUMN body_record.carb_kcal IS '탄수화물 kcal';
COMMENT ON COLUMN body_record.fat_items IS '선택한 지방 음식 목록';
COMMENT ON COLUMN body_record.fat_kcal IS '지방 kcal';
COMMENT ON COLUMN body_record.supplement_items IS '보충 음식 목록 (목표 계산 미포함)';

CREATE VIEW v_day_record_summary AS
WITH active_goal AS (
        SELECT user_goal.started_at
          FROM user_goal
         WHERE user_goal.goal_status::text = 'ACTIVE'::text
         ORDER BY user_goal.started_at DESC
        LIMIT 1
       )
SELECT d.record_date - ag.started_at + 1 AS day_no,
   (floor((d.record_date - ag.started_at)::numeric / 7::numeric) + 1::numeric)::integer AS week_no,
   d.day_record_id,
   d.record_date,
   d.score,
   d.grade,
   d.mood_score,
   d.morning_med_taken,
   d.evening_med_taken,
   d.medication_note,
   b.weight_kg,
   b.waist_cm,
   b.water_liter,
   b.protein_kcal,
   b.carb_kcal,
   b.fat_kcal,
   b.binge_yn,
   w.planned_workout,
   w.completed_workout,
   w.bike_minutes,
   w.workout_done_yn,
   m.breakfast,
   m.lunch,
   m.dinner,
   m.snack,
   m.total_calorie,
   m.meal_score,
   s.sleep_start_time,
   s.sleep_end_time,
   s.sleep_hours,
   s.sleep_quality_score,
   s.wake_condition,
   g.lightness_score::integer AS lightness_score,
   g.reaction_score::integer AS reaction_score,
   g.side_score::integer AS side_score,
   g.shoulder_score::integer AS shoulder_score,
   NULL::text AS coach_note,
   NULL::text AS ai_summary,
   NULL::text AS next_goal,
   d.memo,
   d.created_at,
   d.updated_at,
   g.gk_memo
  FROM day_record d
    CROSS JOIN active_goal ag
    LEFT JOIN body_record b ON d.day_record_id = b.day_record_id
    LEFT JOIN workout_record w ON d.day_record_id = w.day_record_id
    LEFT JOIN meal_record m ON d.day_record_id = m.day_record_id
    LEFT JOIN sleep_record s ON d.day_record_id = s.day_record_id
    LEFT JOIN gk_record g ON d.day_record_id = g.day_record_id;

CREATE VIEW v_dashboard AS
WITH base AS (
        SELECT s.day_no,
           s.week_no,
           s.day_record_id,
           s.record_date,
           s.score,
           s.grade,
           s.mood_score,
           s.morning_med_taken,
           s.evening_med_taken,
           s.medication_note,
           s.weight_kg,
           s.waist_cm,
           s.water_liter,
           s.protein_kcal,
           s.carb_kcal,
           s.fat_kcal,
           s.binge_yn,
           s.planned_workout,
           s.completed_workout,
           s.bike_minutes,
           s.workout_done_yn,
           s.breakfast,
           s.lunch,
           s.dinner,
           s.snack,
           s.total_calorie,
           s.meal_score,
           s.sleep_start_time,
           s.sleep_end_time,
           s.sleep_hours,
           s.sleep_quality_score,
           s.wake_condition,
           s.lightness_score,
           s.reaction_score,
           s.side_score,
           s.shoulder_score,
           s.coach_note,
           s.ai_summary,
           s.next_goal,
           s.memo,
           s.created_at,
           s.updated_at,
               CASE
                   WHEN s.sleep_hours >= 7::numeric THEN 20
                   WHEN s.sleep_hours >= 6::numeric THEN 15
                   WHEN s.sleep_hours >= 5::numeric THEN 10
                   ELSE 5
               END +
               CASE
                   WHEN s.water_liter >= 3.0 THEN 20
                   WHEN s.water_liter >= 2.5 THEN 15
                   WHEN s.water_liter >= 2.0 THEN 10
                   ELSE 5
               END +
               CASE
                   WHEN s.protein_kcal >= 430 THEN 15
                   WHEN s.protein_kcal >= 320 THEN 10
                   WHEN s.protein_kcal >= 215 THEN 5
                   ELSE 0
               END +
               CASE
                   WHEN s.workout_done_yn = true THEN 20
                   ELSE 10
               END +
               CASE
                   WHEN s.morning_med_taken = true AND s.evening_med_taken = true THEN 15
                   WHEN s.morning_med_taken = true OR s.evening_med_taken = true THEN 8
                   ELSE 0
               END +
               CASE
                   WHEN s.mood_score >= 5 THEN 10
                   WHEN s.mood_score >= 4 THEN 8
                   WHEN s.mood_score >= 3 THEN 5
                   ELSE 2
               END AS gk_readiness_score
          FROM v_day_record_summary s
       )
SELECT day_no,
   week_no,
   day_record_id,
   record_date,
   score,
   grade,
   mood_score,
   morning_med_taken,
   evening_med_taken,
   medication_note,
   weight_kg,
   waist_cm,
   water_liter,
   protein_kcal,
   carb_kcal,
   fat_kcal,
   binge_yn,
   planned_workout,
   completed_workout,
   bike_minutes,
   workout_done_yn,
   breakfast,
   lunch,
   dinner,
   snack,
   total_calorie,
   meal_score,
   sleep_start_time,
   sleep_end_time,
   sleep_hours,
   sleep_quality_score,
   wake_condition,
   lightness_score,
   reaction_score,
   side_score,
   shoulder_score,
   coach_note,
   ai_summary,
   next_goal,
   memo,
   created_at,
   updated_at,
   gk_readiness_score,
       CASE
           WHEN gk_readiness_score >= 95 THEN 'ELITE'::text
           WHEN gk_readiness_score >= 80 THEN 'READY'::text
           WHEN gk_readiness_score >= 60 THEN 'NORMAL'::text
           WHEN gk_readiness_score >= 40 THEN 'CARE'::text
           ELSE 'RECOVERY'::text
       END AS gk_readiness_level,
       CASE
           WHEN gk_readiness_score >= 95 THEN '오늘은 몸 상태가 매우 좋습니다. 적극적으로 움직여도 좋습니다.'::text
           WHEN gk_readiness_score >= 80 THEN '오늘은 계획한 운동을 진행하기 좋은 상태입니다.'::text
           WHEN gk_readiness_score >= 60 THEN '오늘은 평소 루틴을 유지하면 충분합니다.'::text
           WHEN gk_readiness_score >= 40 THEN '오늘은 강도보다 회복을 함께 고려하세요.'::text
           ELSE '오늘은 회복이 훈련입니다. 무리하지 않아도 괜찮습니다.'::text
       END AS gk_readiness_message
  FROM base;

COMMIT;
