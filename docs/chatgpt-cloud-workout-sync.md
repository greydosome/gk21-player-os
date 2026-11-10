# ChatGPT 클라우드 운동 연결

## 상태와 범위

`app.mcp_server:app_factory`는 기존 GK21 API와 별도로 실행하는 인증된 MCP 서버다.
OpenAI API를 호출하지 않으며 별도 OpenAI API 키를 사용하지 않는다.
서버 설치만으로 ChatGPT의 기존 대화를 읽거나 예약 작업을 만들지는 않는다.
ChatGPT 계정에 연결하고 해당 대화의 도구·예약 실행을 실제 검증해야 클라우드 전환이 완료된다.
그 전까지 기존 로컬 자동화를 끄지 않는다.

도구는 기존 운동 분류 조회, 최근 14일 중 하루의 워치 세션/처리 상태 조회,
사용자가 실제 완료한 운동 보고 저장의 세 개뿐이다. 저장은 기존 `persist`와
`WorkoutReport` 검증을 그대로 사용하며 워치 시간 우선·중복 방지·수동 수정 보호가 적용된다.
수면·식단·심박·경로·일반 대화 원문은 이 연결로 제공하지 않는다.

## 인증

MCP Python SDK의 OAuth 2.1/PKCE 구현을 사용한다. 독립된 SQLite 인증 저장소는
서버 `/var/lib/gk21-mcp`에 두며 디렉터리 700, 파일 600, systemd UMask 0077을 적용한다.
등록은 ChatGPT의 정확한 콜백 주소만 허용하며 리소스 `/mcp`와 `workout:sync` 범위를 고정한다.
건강 업로드 키를 ChatGPT에 전달하거나 URL에 넣지 않는다.

처음 연결할 때 브라우저는 10분짜리 승인 대기 화면을 보여준다.
승인 후에는 자동 새로고침을 멈추고 ‘ChatGPT로 돌아가기’를 눌러 인증 코드를 발급한다.
단순 새로고침·미리보기 요청은 승인 요청을 소모하지 않는다.
웹에는 승인 엔드포인트가 없다. 소유자의 기존 SSH 접근으로 요청 번호·클라이언트·
콜백을 대조한 후 해당 요청만 승인한다. 승인 전에 사용자에게 실제 접근 범위를 확인한다.

서버 backend 폴더에서:

```sh
PYTHONPATH=. .venv/bin/python scripts/mcp_connection.py pending
PYTHONPATH=. .venv/bin/python scripts/mcp_connection.py approve REQUEST_ID
# 연결 폐기
PYTHONPATH=. .venv/bin/python scripts/mcp_connection.py revoke-all
```

인증 코드는 2분·한 번만 사용 가능하고 토큰은 해시로만 저장한다.
액세스 토큰은 1시간, 갱신 토큰은 90일이며 갱신할 때 두 토큰을 교체한다.
소유자가 승인을 취소하면 같은 연결의 액세스/갱신 토큰을 함께 폐기한다.
요청 본문·인증 헤더·OAuth 쿼리는 접근 로그에 남기지 않는다.

## 배포와 연결

`uv sync --frozen` 후 `deploy/gk21-mcp.service`를 설치하고
`deploy/gk21-mcp-start.sh`를 `/usr/local/bin/gk21-mcp-start.sh`에 755로 설치한다.
`/var/lib/gk21-mcp`는 서비스 계정 소유로 만들고 700을 적용한다.
HTTPS에만 `deploy/nginx-gk21-mcp.conf.example` 경로를 연결하며 HTTP는 403으로 거절한다.
백엔드/프런트엔드의 기존 경로는 변경하지 않는다.

ChatGPT 웹 플러그인 메뉴 → 사용자 지정 MCP 서버 추가에서
`https://217.142.230.185/mcp`, OAuth를 선택한다.
고급 OAuth 설정에 표시된 해당 플러그인의 정확한 ChatGPT 콜백 URL은
root 전용 `/etc/gk21/mcp.env`의 `GK21_MCP_CALLBACK_URL`로 설정한다.
임의 외부 콜백이나 전체 도메인 와일드카드는 허용하지 않는다.
도구 검토 및 소유자 승인 후 운동 코치 대화에 설치한다.
클라우드 예약 실행 목표는 Asia/Seoul 매일 10:00·16:00·22:00·04:00이다.
완료 보고가 없으면 저장하지 않고, 원래 운동 날짜에 기존 항목을 보완한다.
사용 가능한 대화 메타데이터·도구 승인 유지·예약 실행 권한은 실제 계정에서 검증한다.
검증하지 못한 기능을 완료로 표시하거나 임의의 메시지 ID를 만들어 저장하지 않는다.
