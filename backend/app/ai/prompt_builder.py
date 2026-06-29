import json


SYSTEM_PROMPT = """
당신은 GK21 AI 건강 코치입니다.

규칙

- 의료 진단을 하지 않는다.
- 과장하지 않는다.
- 반드시 긍정적인 표현을 사용한다.
- 최근 추세를 함께 분석한다.
- 목표를 고려하여 조언한다.
- JSON만 반환한다.

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

    history = context.get("history", [])

    trend = {

        "score": [],

        "weight": [],

        "sleep": [],

        "meal": [],

        "water": [],

        "protein": []

    }

    for row in reversed(history):

        trend["score"].append(row.get("score"))

        trend["weight"].append(row.get("weight_kg"))

        trend["sleep"].append(row.get("sleep_hours"))

        trend["meal"].append(row.get("meal_score"))

        trend["water"].append(row.get("water_liter"))

        trend["protein"].append(row.get("protein_gram"))

    payload = {

        "today": context.get("today"),

        "metrics": metrics,

        "trend": trend,

        "goal": {

            "target_weight": 75,

            "target_protein": 180,

            "style": "상체 프레임"

        }

    }

    return SYSTEM_PROMPT + "\n\n" + json.dumps(

        payload,

        ensure_ascii=False,

        indent=2,

        default=str

    )
