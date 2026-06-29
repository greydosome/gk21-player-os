
def build_daily_rule_analysis(context, metrics):

    today = context.get("today")

    if today is None:

        return {

            "overall_score": None,

            "summary": "아직 오늘 기록이 없습니다.",

            "strength": "기록을 시작할 준비가 되어 있습니다.",

            "weakness": "오늘 기록이 아직 없어 분석할 데이터가 부족합니다.",

            "next_goal": "오늘의 몸 상태, 운동, 식단, 수면을 먼저 기록해 주세요.",

            "body_comment": None,

            "workout_comment": None,

            "meal_comment": None,

            "sleep_comment": None,

        }

    score = today.get("score")

    weight_kg = today.get("weight_kg")

    workout_done_yn = today.get("workout_done_yn")

    bike_minutes = today.get("bike_minutes")

    meal_score = today.get("meal_score")

    sleep_hours = today.get("sleep_hours")

    sleep_quality_score = today.get("sleep_quality_score")

    avg_sleep_7 = metrics.get("avg_sleep_hours_7")

    workout_days_7 = metrics.get("workout_days_7")

    days_7_count = metrics.get("days_7_count")

    weight_change_7 = metrics.get("weight_change_7")

    overall_score = score

    summary = "오늘 기록이 안정적으로 저장되었습니다."

    strength = "오늘도 기록을 남겼다는 점이 가장 좋은 출발입니다."

    weakness = "아직 뚜렷한 개선점은 없습니다."

    next_goal = "내일도 같은 흐름으로 기록을 이어가세요."

    if score is not None and score >= 90:

        summary = "오늘은 전체적으로 좋은 흐름입니다."

        strength = "점수 기준으로 보면 루틴 수행 상태가 매우 안정적입니다."

        next_goal = "현재 흐름을 유지하면서 무리하지 않는 것이 좋습니다."

    if sleep_hours is not None and sleep_hours < 6:

        summary = "오늘은 회복이 조금 부족한 하루입니다."

        weakness = "수면 시간이 부족해 피로가 누적될 수 있습니다."

        next_goal = "오늘은 취침 시간을 조금 앞당기는 것을 목표로 해보세요."

    if workout_done_yn is False:

        weakness = "운동 기록이 완료되지 않았습니다."

        next_goal = "내일은 짧게라도 운동을 완료하는 것을 목표로 해보세요."

    if meal_score is not None and meal_score >= 90:

        strength = "식단 관리가 매우 좋습니다."

    body_comment = "신체 기록이 저장되었습니다."

    if weight_kg is not None and weight_change_7 is not None:

        if weight_change_7 < 0:

            body_comment = f"최근 기록 기준 체중이 {abs(weight_change_7)}kg 증가했습니다. 급하게 판단하지 말고 흐름을 조금 더 지켜보면 좋겠습니다."

        elif weight_change_7 > 0:

            body_comment = f"최근 기록 기준 체중이 {weight_change_7}kg 감소했습니다. 좋은 흐름입니다."

        else:

            body_comment = "최근 기록 기준 체중이 안정적으로 유지되고 있습니다."

    workout_comment = "운동 기록이 아직 충분하지 않습니다."

    if workout_done_yn is True:

        workout_comment = "오늘 운동을 완료했습니다."

        if bike_minutes is not None:

            workout_comment = f"오늘 운동을 완료했고, 자전거 운동 {bike_minutes}분이 기록되었습니다."

    if days_7_count and days_7_count > 1:

        workout_comment += f" 최근 {days_7_count}일 중 {workout_days_7}일 운동을 완료했습니다."

    meal_comment = "식단 기록이 저장되었습니다."

    if meal_score is not None:

        if meal_score >= 90:

            meal_comment = "식단 점수가 매우 좋습니다. 현재 식단 흐름을 유지해도 좋습니다."

        elif meal_score < 70:

            meal_comment = "식단 점수가 낮은 편입니다. 단백질과 수분 섭취를 다시 점검해보세요."

    sleep_comment = "수면 기록이 저장되었습니다."

    if sleep_hours is not None:

        if sleep_hours >= 7:

            sleep_comment = f"수면 시간이 {sleep_hours}시간으로 회복에 도움이 되는 수준입니다."

        elif sleep_hours < 6:

            sleep_comment = f"수면 시간이 {sleep_hours}시간으로 부족합니다. 회복을 우선해 주세요."

    if avg_sleep_7 is not None and days_7_count and days_7_count > 1:

        sleep_comment += f" 최근 {days_7_count}일 평균 수면은 {avg_sleep_7}시간입니다."

    if sleep_quality_score is not None and sleep_quality_score >= 90:

        sleep_comment += " 수면 품질 점수도 좋은 편입니다."

    return {

        "overall_score": overall_score,

        "summary": summary,

        "strength": strength,

        "weakness": weakness,

        "next_goal": next_goal,

        "body_comment": body_comment,

        "workout_comment": workout_comment,

        "meal_comment": meal_comment,

        "sleep_comment": sleep_comment,

    }

