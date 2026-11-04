# Health Auto Export → GK21

이 경로는 운동 종류/시간과 날짜별 수면 요약을 받기 위한 추가 연동이다.
원래 단축어의 최근 24시간 합계는 2026-11-04 건강 앱과 불일치가 확인되어
운영 수신/표시를 껐다. 이 문서의 경로를 실제 기기와 대조하기 전까지 자동화하지 않는다.

## 앱 설정

- 앱: Health Auto Export - JSON+CSV, 개발자 Lybron Sobers, App Store ID 1115567069.
- 무료 다운로드만 승인됨. 유료 구매/구독은 금액을 확인하고 별도 사용자 승인 필요.
- 읽기 권한은 수면과 운동에 한정. 경로/GPS·심박 시계열은 이 연동에 사용하지 않는다.
- REST API 주소: `https://217.142.230.185/api/integrations/apple-health/export`.
- JSON, export v2. 헤더 `Authorization: Bearer <개인 업로드 키>`.
- 주소나 공유 링크에 키를 포함하지 않는다. 토큰은 저장소/채팅/로그에 기록하지 않는다.
- 수면용 자동화: Health Metrics, sleep_analysis만, 일별 요약 ON, 시간 그룹 Day,
  실제 사용하는 수면 기록 출처 한 개를 Preferred Sources로 지정.
- 운동용 자동화: Workouts, Include Routes OFF, Include Workout Metrics OFF.
- 최근 7일을 재조회할 수 있다. 재전송 및 나누어 전송한 배치는 ID로 병합한다.
- 잠금 상태에서는 읽기가 제한될 수 있으므로 정시 무인 수집을 보장하지 않는다.

## 서버 처리

`data.metrics` / `data.workouts` 배열 또는 최상위의 동일 배열을 받는다.
32KiB 제한. 필요 필드만 추출하고 전체 원본은 저장하지 않는다.

수면은 `units=hr`, 날짜별 `totalSleep` 숫자만 받는다. 같은 날짜에 여러 수면
요약이 있거나 원시 단계 표본만 오면 합산하지 않고 422로 거절한다.
0이나 누락은 이전 수면 값을 지우지 않는다. 실제 수면이 0인 날의 확정 입력은
이 경로에서 지원하지 않는다.

운동은 `id`, `name`, `start`, `end`, `duration`(초)을 추출한다. 동일 ID 갱신,
재전송 중복 방지 및 동일 종류/구간/시간인 복제 표본 중복 합산 방지를 지원한다.
자정을 넘으면 서울 날짜별로 나눈다. 일시정지가 있는 운동의 일별 활동 시간은
경과 시간 비율로 나누며, 분할 합계는 원래 활동 시간을 보존한다.
배치에 없는 운동을 삭제로 해석하지 않는다. Apple 건강에서 삭제한 운동의
삭제 동기화는 지원하지 않는다.

기존 직접 입력한 운동은 바꾸지 않고 자동 기록 카드에 표시한다.

## 검증

- 로컬 임시 PostgreSQL에서 인증/TLS, 일별 요약, 재전송, 배치 병합,
  수정된 운동, 자정 분할, 중복 출처 및 0/누락 처리 검증.
- 운영 적용 시 `2026-11-04_health_export_workouts.sql`을 별도로 적용한다.
- 수면/운동 각각 실제 내보내기 후 건강 앱과 대조해야 운영 수신을 재활성화한다.

공식 형식 및 설정:
- https://help.healthyapps.dev/en/health-auto-export/export-format/health-metrics/
- https://help.healthyapps.dev/en/health-auto-export/export-format/workouts/
- https://help.healthyapps.dev/en/health-auto-export/automations/rest-api/
- https://apps.apple.com/kr/app/health-auto-export-json-csv/id1115567069
