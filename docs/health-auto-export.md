# Health Export 수신 형식

무료 단축어 연동을 사용한다. Health Auto Export의 유료 전송 기능은 필수 의존성이 아니다.
현재 설정은 [무료 건강 연동](free-health-shortcuts.md)을 참고한다.

## 수신 API

POST /api/integrations/apple-health/export는 인증된 HTTPS에서만 사용한다.
JSON 본문은 32KiB까지 받는다. Authorization 헤더로 개인 전송 키를 전달하며 URL이나 소스에 키를 넣지 않는다.

- data.metrics / data.workouts 또는 최상위의 동일 배열을 받는다.
- 수면은 units=hr 및 날짜별 totalSleep 요약을 받는다. 같은 날짜의 중복 요약이나 원시 단계 표본만 오면 거절한다.
- 운동은 id, name, start, end, duration(초)을 사용한다. GPS·경로·심박 시계열은 저장하지 않는다.
- 같은 운동 ID의 갱신과 재전송을 지원하고 동일 세션의 복제 표본을 중복 합산하지 않는다.
- 배치에 없는 운동을 삭제로 해석하지 않는다. 원본에서 삭제한 운동의 삭제 동기화는 지원하지 않는다.
- 원본 요약은 자정 경계로 분할할 수 있으나 기존 운동 입력에는 세션 전체 활동 시간을 종료 날짜로 반영한다.
- 수동 입력 보호 및 반올림 규칙은 health_records.py에서 처리한다.

실제 기기 권한과 자동화 동작은 사용 기기에서 확인해야 한다. 잠금 상태의 읽기와 정시 무인 실행을 보장하지 않는다.
