"""
일회성 백필 스크립트: 진료과 분류 기능이 생기기 전에 기록된 약들을
AI로 진료과(정신의학과/가정의학과/상비약)를 판단해서 다시 분류한다.

같은 이름의 약은 어느 날 기록됐든 항상 같은 진료과로 취급한다(약 이름 하나당
AI 호출 1번만). day_record.medication_items에 저장된 모든 항목(예전 문자열
형태든, 새 {name, category} 형태든)을 이름 기준으로 다시 써서 저장한다.

실행:
    cd /home/rocky/gk21/backend && uv run python scripts/reclassify_medication_history.py
"""

import json
import sys
import time

from sqlalchemy import text

from app.ai.llm import call_ai
from app.ai.medication_category_prompt import build_medication_category_prompt
from app.db.session import engine

VALID_CATEGORIES = {"psychiatry", "family_medicine", "otc"}


def extract_name(item) -> str | None:
    if isinstance(item, str):
        name = item.strip()
        return name or None
    if isinstance(item, dict):
        name = str(item.get("name", "")).strip()
        return name or None
    return None


def classify(name: str) -> str:
    try:
        prompt = build_medication_category_prompt(name)
        result = call_ai(prompt)
        category = result.get("analysis", {}).get("category")
        if category in VALID_CATEGORIES:
            return category
    except Exception as exc:  # noqa: BLE001 - 백필 스크립트는 실패해도 계속 진행
        print(f"  ! classify failed for {name!r}: {exc}", file=sys.stderr)
    return "otc"


def main():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT day_record_id, medication_items FROM day_record "
                "WHERE medication_items IS NOT NULL AND medication_items != '[]'::jsonb"
            )
        ).all()

    print(f"대상 day_record: {len(rows)}건")

    # 1) 이름 목록 수집 (중복 제거)
    all_names: set[str] = set()
    for row in rows:
        for item in row.medication_items or []:
            name = extract_name(item)
            if name:
                all_names.add(name)

    print(f"고유 약 이름: {len(all_names)}개")

    # 2) 이름별로 한 번씩만 AI 분류 호출
    name_to_category: dict[str, str] = {}
    counts = {"psychiatry": 0, "family_medicine": 0, "otc": 0}
    for i, name in enumerate(sorted(all_names), start=1):
        category = classify(name)
        name_to_category[name] = category
        counts[category] += 1
        print(f"  [{i}/{len(all_names)}] -> {category}")
        time.sleep(0.2)  # OpenAI 레이트리밋 여유

    print(f"분류 결과: 정신의학과 {counts['psychiatry']} / 가정의학과 {counts['family_medicine']} / 상비약 {counts['otc']}")

    # 3) 각 day_record의 medication_items를 새 카테고리로 다시 써서 저장
    updated = 0
    with engine.begin() as conn:
        for row in rows:
            new_items = []
            changed = False
            for item in row.medication_items or []:
                name = extract_name(item)
                if not name:
                    continue
                category = name_to_category.get(name, "otc")
                old_category = item.get("category") if isinstance(item, dict) else None
                if old_category != category or not isinstance(item, dict):
                    changed = True
                new_items.append({"name": name, "category": category})

            if changed:
                conn.execute(
                    text(
                        "UPDATE day_record SET medication_items = CAST(:items AS jsonb) "
                        "WHERE day_record_id = :id"
                    ),
                    {"items": json.dumps(new_items, ensure_ascii=False), "id": row.day_record_id},
                )
                updated += 1

    print(f"업데이트된 day_record: {updated}건")


if __name__ == "__main__":
    main()
