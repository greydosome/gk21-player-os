-- STEP-037: widen day_record.grade to fit new level labels (e.g. "Not too bad")
-- Must drop/recreate dependent views (v_dashboard depends on v_day_record_summary, which depends on grade)

BEGIN;

DROP VIEW IF EXISTS v_dashboard;
DROP VIEW IF EXISTS v_day_record_summary;

ALTER TABLE day_record ALTER COLUMN grade TYPE VARCHAR(20);

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
   b.protein_gram,
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
           s.protein_gram,
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
                   WHEN s.protein_gram >= 160 THEN 15
                   WHEN s.protein_gram >= 120 THEN 10
                   WHEN s.protein_gram >= 80 THEN 5
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
   protein_gram,
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
