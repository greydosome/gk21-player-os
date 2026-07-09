def build_today_missions(dashboard: dict | None) -> list[dict]:
    if not dashboard:
        return []

    missions = []

    if not dashboard.get("morning_med_taken"):
        missions.append({
            "title": "아침약 복용",
            "done": False,
            "kind": "MED"
        })

    if not dashboard.get("evening_med_taken"):
        missions.append({
            "title": "저녁약 복용",
            "done": False,
            "kind": "MED"
        })

    water = float(dashboard.get("water_liter") or 0)
    if water >= 3.0:
        missions.append({
            "title": "수분 3L 유지",
            "done": True,
            "kind": "WATER"
        })
    else:
        remain = round(3.0 - water, 1)
        missions.append({
            "title": f"물 {remain}L 더 마시기",
            "done": False,
            "kind": "WATER"
        })

    protein = int(dashboard.get("protein_kcal") or 0)
    if protein >= 430:
        missions.append({
            "title": "단백질 목표 유지",
            "done": True,
            "kind": "PROTEIN"
        })
    else:
        missions.append({
            "title": "단백질 한 번 더 챙기기",
            "done": False,
            "kind": "PROTEIN"
        })

    if dashboard.get("workout_done_yn"):
        missions.append({
            "title": "오늘 운동 완료",
            "done": True,
            "kind": "WORKOUT"
        })
    else:
        missions.append({
            "title": "가벼운 운동 20분",
            "done": False,
            "kind": "WORKOUT"
        })

    # 모바일 화면 복잡도 방지: 최대 3개만 노출
    undone = [m for m in missions if not m["done"]]
    done = [m for m in missions if m["done"]]

    return (undone + done)[:3]
