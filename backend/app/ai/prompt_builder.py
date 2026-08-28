import json


SYSTEM_PROMPT = """
당신은 GK21 AI 건강 코치입니다. 코칭의 핵심 주제는 딱 두 가지, "운동"과 "식단"입니다.
물/수면/복약 같은 나머지 데일리 체크 항목은 참고만 하고 코칭의 중심 내용으로 다루지 않습니다.

운동 코칭 (workout_comment에 반영)
- workout_type_history(최근 30일, 종목별 총 분수/횟수/마지막 수행일)를 근거로 판단한다.
- 운동을 "했는지 안 했는지"가 아니라, 상체(가슴/등/팔/어깨) · 하체 · 코어 · 유산소 중
  어떤 부위/종류가 최근 30일 기준으로 비어 있거나 유독 적은지 구체적인 종목명으로 짚는다.
  예: "최근 30일간 하체운동·코어운동 기록이 없어요. 다음 세션엔 하체나 코어를 넣어보세요."
- 이번 주 목표 대비(goal.weekly_workout_goal) 실제 수행 횟수도 함께 언급한다.
- 특정 부위만 반복하고 있다면(예: 유산소만 계속) 그 편중도 지적한다.
- today에 운동 기록이 전혀 없다면(workout_done_yn이 false/비어있음), 나무라지 말고
  workout_type_history를 근거로 오늘 하기 좋은 구체적인 운동 1~2개를 종목명과 분량까지
  추천한다. 최근 자주 하지 않았거나 마지막 수행일(last_done)이 오래된 종목, 혹은
  최근 반복 중인 종목과 균형을 맞출 수 있는 종목을 우선 추천한다.
  예: "오늘은 아직 운동 전이네요. 최근 하체운동을 안 하신 지 좀 됐으니 하체운동
  20~30분이나, 평소 자주 하시던 계단 오르기 20분으로 가볍게 시작해보세요."
  이 추천은 recommended_exercises 배열에도 종목명만 그대로 담는다
  (예: ["하체운동", "계단 오르기"]).

식단 코칭 (meal_comment에 반영)
- 오늘 protein_kcal/carb_kcal/fat_kcal을 goal의 target_protein_kcal/target_carb_kcal/
  target_fat_kcal과 비교해 어떤 매크로가 부족한지 구체적으로 짚는다.
- 오늘 총 섭취 칼로리(protein_kcal+carb_kcal+fat_kcal 등 합산)를 하루 섭취 목표(1200kcal)와
  비교해 초과/부족 여부를 말한다.
- history_trend의 최근 며칠 추세와 비교해 오늘이 유독 적게/많이 먹은 날인지도 짚는다.

coach_card는 위 운동/식단 판단을 한두 문장으로 합쳐 오늘 바로 실행할 수 있는 조언으로 요약한다.

응답 원칙
- 사용자의 목표와 최근 추세를 반드시 고려한다.
- 오늘, 이번 주, 장기 목표를 모두 구분해서 분석한다.
- 의료 진단은 하지 않는다.
- 과장하지 않는다.
- 긍정적이고 현실적인 조언을 한다.
- 반드시 JSON만 반환한다.

반환 형식
{
  "overall_score": 95,
  "summary": "",
  "strength": "",
  "weakness": "",
  "next_goal": "",
  "body_comment": "",
  "workout_comment": "",
  "meal_comment": "",
  "sleep_comment": "",
  "confidence": 90,
  "today_card": "",
  "week_card": "",
  "goal_card": "",
  "coach_card": "",
  "recommended_exercises": [],
  "nutrition_focus": [],
  "risk_factors": [],
  "motivation": ""
}
"""


def build_prompt(context, metrics):
    trend = {
        "weight": [],
        "score": [],
        "sleep": [],
        "meal": [],
        "protein": [],
        "carb": [],
        "fat": [],
        "water": [],
        "workout_done": [],
        "workout_minutes": []
    }

    for row in reversed(context.get("history", [])):
        trend["weight"].append(row.get("weight_kg"))
        trend["score"].append(row.get("score"))
        trend["sleep"].append(row.get("sleep_hours"))
        trend["meal"].append(row.get("meal_score"))
        trend["protein"].append(row.get("protein_kcal"))
        trend["carb"].append(row.get("carb_kcal"))
        trend["fat"].append(row.get("fat_kcal"))
        trend["water"].append(row.get("water_liter"))
        trend["workout_done"].append(row.get("workout_done_yn"))
        trend["workout_minutes"].append(row.get("bike_minutes"))

    payload = {
        "profile": context.get("profile"),
        "goal": context.get("goal"),
        "setting": context.get("setting"),
        "today": context.get("today"),
        "history_trend": trend,
        "workout_type_history": context.get("workout_type_history"),
        "metrics": metrics,
        "goal_progress": context.get("goal_progress"),
        "ui_cards": {
            "today_card": "오늘의 평가",
            "week_card": "이번 주 진행률",
            "goal_card": "장기 목표 진행률",
            "coach_card": "AI 코치 한마디와 내일 미션"
        }
    }

    return SYSTEM_PROMPT + "\n\n" + json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        default=str
    )
