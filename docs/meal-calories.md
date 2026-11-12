# 식단 열량 보완과 합계 표시

사용자 요청에 따라 실제 섭취한 음식은 열량을 조사해 기존 카탈로그/일반식 필드에 반영한다. 공식 제조사 영양표, 공공 식품성분 DB, 신뢰 가능한 식품 DB 순으로 확인한다. 수량·제품을 정확히 알 수 없으면 대표 식품과 통상 분량으로 추정하고 출처 URL, 가정, 계산식을 nutrition_source에 기록한다. 추정은 nutrition_basis=estimate / estimated=true다. 사용자가 말한 quantity는 임의로 바꾸지 않는다. 자료를 조사하지 않고 null로 종료하지 않으며, 음식 자체를 특정할 수 없을 때만 보류한다. 칼로리 질문이나 추천은 섭취 증거가 아니다.

신규 섭취는 기존 meal report CLI를 사용한다. 이미 저장된 식사의 열량 보완은 `scripts/enrich_meal_nutrition.py`를 사용한다. 이 도구는 같은 conversation_id/meal_key/expected_revision과 food index/name을 확인하고 영양 필드만 변경한다. 이벤트 ID `nutrition:<요청 해시>`는 시스템 보완 이벤트이며 사용자 메시지 ID가 아니다. 최초 사용자 메시지는 기존 불변 이벤트에 유지된다. 원본 reported_at과 record_date도 유지한다. 동일 요청은 재실행해도 중복되지 않는다. 새로운 식사나 자유 텍스트 메모를 만들지 않는다. 수동으로 수정한 음식은 기존 native conflict 보호를 유지한다.

실행 계정은 VM rocky다. 권한600 입력 JSON을 저장소 밖에 두고 다음 명령으로 실행한다. 토큰이나 DB 암호를 읽거나 출력하지 않는다.

```sh
cd /home/rocky/gk21/backend
MEAL_CONVERSATION_ENABLED=true .venv/bin/python ../scripts/enrich_meal_nutrition.py /private/input.json
```

입력은 `[{conversation_id,meal_key,expected_revision,updates:[{index,name,kcal,nutrition_source,nutrition_basis,estimated}]}]`이다. 먼저 기존 status를 조회하고 저장 후 원장과 `/api/dashboard`의 기존 음식 배열을 대조한다. 충돌은 성공 반영으로 취급하지 않는다. 실패한 요청은 그대로 보존하고 성공 확인 후만 삭제한다.

칼로리 화면은 `총 섭취 kcal / 1,200kcal 초과분`을 표시한다. 초과분은 max(0, 총섭취-1200)이며 총섭취를 1200으로 제한하지 않는다. 기준 이하에서는 별도 카드에 남은 양을 표시한다. 2,000kcal에 300kcal 음식 추가 시 총 2,300kcal / 초과 1,100kcal다. 기존 식품 합계 및 기간 집계에서 일반식은 한 번만 더한다.

검증: 격리 PostgreSQL 시험으로 2000+300 합계, 재실행 중복 방지, 원본 수량/시각 보존, revision 충돌을 확인한다. Next production build, 실제 화면의 추가 전후 표시와 재조회도 검사한다.

배포는 기존 /home/rocky/gk21 경로를 사용하고 DB 디렉터리 /postgres를 이동하지 않는다. 변경 소스와 기존 frontend/.next를 /var/backups 아래에 백업한다. 롤백은 변경 소스/빌드만 복구하고 서비스 재시작한다. 영양값 롤백은 백업의 이전 값으로 새 보완 이벤트를 만들며 운영 DB 전체를 덮어쓰지 않는다. 공개 Git에는 소스/테스트/문서만 올리고 실제 식사 JSON과 백업은 제외한다.
