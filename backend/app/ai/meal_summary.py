import re

# 프론트엔드가 저장하는 식단 문자열을 끼니별로 묶어 AI 프롬프트용으로 요약한다.
#  - 카탈로그 음식: "참치 마일드 90g@점심" ("@끼니"는 선택, 예전 기록에는 없다)
#  - 보충음식:      "블루베리@아침"
#  - 직접입력:      "CUSTOM|이름|수량|단위|칼로리|분류|끼니" (분류/끼니는 뒤쪽 선택 항목)
# 카탈로그 음식의 칼로리는 프론트엔드에만 있어서 양(g/개)만 보여주고, 직접입력은 칼로리도 같이 준다.
MEALS = ("아침", "점심", "저녁")
UNASSIGNED = "끼니 미지정"

_CATALOG_RE = re.compile(r"^(.*) (\d+)(g|개)(?:@(아침|점심|저녁))?$")


def _split_meal(label: str):
    name, sep, meal = label.rpartition("@")
    if sep and meal in MEALS:
        return name, meal
    return label, None


def _custom_text(parts: list[str]):
    if len(parts) < 5 or not parts[1].strip():
        return None, None
    name, quantity, unit, kcal = parts[1].strip(), parts[2], parts[3], parts[4]
    meal = parts[6] if len(parts) >= 7 and parts[6] in MEALS else None
    amount = f"{quantity}{'g' if unit != 'count' else '개'} " if quantity else ""
    return f"{name} {amount}{kcal}kcal", meal


def summarize_meals(*item_lists) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}

    def add(meal, text):
        groups.setdefault(meal or UNASSIGNED, []).append(text)

    for items in item_lists:
        for raw in items or []:
            if not isinstance(raw, str):
                continue
            if raw.startswith("CUSTOM|"):
                text, meal = _custom_text(raw.split("|"))
                if text:
                    add(meal, text)
                continue
            match = _CATALOG_RE.match(raw)
            if match:
                add(match.group(4), f"{match.group(1)} {match.group(2)}{match.group(3)}")
            else:
                label, meal = _split_meal(raw)
                if label.strip():
                    add(meal, label.strip())

    ordered = {meal: groups[meal] for meal in (*MEALS, UNASSIGNED) if meal in groups}
    return ordered
