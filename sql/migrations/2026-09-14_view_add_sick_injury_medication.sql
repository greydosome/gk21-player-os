-- v_day_record_summary에 is_sick/is_injured/injury_note/sick_note/medication_items를 추가한다.
-- 이 뷰는 AI 코칭 컨텍스트(app/ai/context.py의 "SELECT * FROM v_day_record_summary")가
-- 그대로 읽어가는 소스라서, 컬럼을 뷰에 노출시키지 않으면 코칭 프롬프트에 절대 들어갈 수 없다.
-- CREATE OR REPLACE VIEW는 기존 컬럼 순서를 바꿀 수 없어서 새 컬럼은 맨 뒤에 추가한다.

CREATE OR REPLACE VIEW v_day_record_summary AS
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
    g.gk_memo,
    d.is_sick,
    d.sick_note,
    d.is_injured,
    d.injury_note,
    d.medication_items
FROM day_record d
    CROSS JOIN active_goal ag
    LEFT JOIN body_record b ON d.day_record_id = b.day_record_id
    LEFT JOIN workout_record w ON d.day_record_id = w.day_record_id
    LEFT JOIN meal_record m ON d.day_record_id = m.day_record_id
    LEFT JOIN sleep_record s ON d.day_record_id = s.day_record_id
    LEFT JOIN gk_record g ON d.day_record_id = g.day_record_id;
