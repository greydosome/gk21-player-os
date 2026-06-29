import json


SYSTEM_PROMPT = """
당신은 GK21 AI 건강 코치입니다.

규칙

- 사용자의 목표를 반드시 고려한다.
- 최근 추세를 함께 분석한다.
- 긍정적이고 현실적인 조언을 한다.
- 의료 진단은 하지 않는다.
- 반드시 JSON만 반환한다.

{
  "overall_score":95,
  "summary":"",
  "strength":"",
  "weakness":"",
  "next_goal":"",
  "body_comment":"",
  "workout_comment":"",
  "meal_comment":"",
  "sleep_comment":"",
  "confidence":90,
  "recommended_exercises":[],
  "nutrition_focus":[],
  "risk_factors":[],
  "motivation":""
}
"""


def build_prompt(context, metrics):

    trend = {
        "weight": [],
        "score": [],
        "sleep": [],
        "meal": [],
        "protein": [],
        "water": []
    }

    for row in reversed(context.get("history", [])):

        trend["weight"].append(row.get("weight_kg"))
        trend["score"].append(row.get("score"))
        trend["sleep"].append(row.get("sleep_hours"))
        trend["meal"].append(row.get("meal_score"))
        trend["protein"].append(row.get("protein_gram"))
        trend["water"].append(row.get("water_liter"))

    payload = {

        "profile": context.get("profile"),

        "goal": context.get("goal"),

        "setting": context.get("setting"),

        "today": context.get("today"),

        "trend": trend,

        "metrics": metrics

    }

    return SYSTEM_PROMPT + "\n\n" + json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        default=str
    )
