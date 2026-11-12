> 2026-11-13: 열량 처리 규칙은 [meal-calories.md](meal-calories.md)를 우선한다. 실제 섭취는 자료 조회 및 출처 있는 추정으로 kcal를 보완한다.

# 실제 섭취 대화 연동

> 2026-11-12: 기존 음식 항목·합계 반영이 추가되었습니다. 현재 동작과 배포는 [meal-native-sync.md](meal-native-sync.md)를 따릅니다. 아래는 최초 구현 당시 기록이며, 별도 목록만 표시하던 제한은 해소됐습니다.

## 구현과 실제 동작 범위

기존 운동 연동의 로컬 Codex 대화 조회 → 구조화 JSON → 승인된 SSH → 서버 내부 HTTPS 인증 API 경로를 재사용한다. 별도 모델·유료 앱·상주 작업자·클라우드 OAuth는 추가하지 않는다. 서버가 ChatGPT 메시지를 직접 구독하는 웹훅은 아니다. Mac과 Codex가 실행 가능한 때 평일 한국 시간 08:00/14:00에 운동 및 지정 식단 대화를 확인한다. 정시 실행 자체는 다음 예정 시각 전에는 검증됐다고 주장하지 않는다.

추천 식단/레시피/계획/질문은 저장하지 않는다. 사용자가 실제 섭취했다고 확인한 음식만 저장한다. 한 메시지에 아침과 점심이 함께 있으면 식사 키를 나눠 각각 저장한다. 실제 날짜는 원본 사용자 메시지의 서울 시각을 기준으로 해석한다. 불확실하면 보류하며 실행 날짜로 바꾸지 않는다. 전체 원문·사진은 저장하지 않는다.

2026-11-10 운영 검증: 실제 사용자 보고에서 확인한 세 식사를 전송했고, 동일 보고 재전송은 unchanged, 각 revision=1 및 이벤트 총 3개를 확인했다. HTTPS 수신값, 앱 조회 API 및 실제 브라우저 표시를 확인했다. 기존 day/body/meal/workout/workout_item/sleep 행의 개수와 내용 해시가 모두 그대로였다. 추천 보고는 행 추가 없이 skip, 무인증 HTTPS=401, HTTP=403이었다. 실제 섭취가 아닌 합성 식사는 운영 DB에 넣지 않았다.

## 기존 앱/DB와의 관계

현재 음식 입력은 `body_record.general_food_items`의 문자열 목록과 카테고리별 kcal를 사용한다. `meal_record`는 자유 텍스트와 총량만 있어, 출처·수정 이력·미확인 영양값을 표현할 수 없다. 직접 입력 영역을 대화 동기화가 덮어쓰지 않도록 같은 PostgreSQL에 두 작은 테이블을 추가하고, **기존 식단 화면 안에서 실제 섭취를 자동 조회**한다. 별도 서비스나 DB는 만들지 않는다.

- `meal_conversation_event`: `(conversation_id,message_id,meal_key)`별 불변 수신 내역. 같은 메시지에서 여러 끼니를 허용한다.
- `meal_conversation_entry`: `(conversation_id,meal_key)`별 최신 상태, 날짜·revision·삭제 표시. 날짜 조회에 인덱스가 있다.
- 동일 수신 키/동일 내용은 무변경. 동일 키/다른 내용은 409.
- 기존 식사의 변경은 새 사용자 메시지 + 같은 meal_key + kind=correction/delete + 현재 expected_revision이 필요하다. 뒤늦은 재전송이 최신 정정을 덮지 않는다. 삭제도 이력을 남기는 soft delete다.
- 작은 전용 트랜잭션 잠금으로 식단 수신만 직렬화한다. 일반 기록/운동/수면 저장과 충돌하지 않는다.
- `/api/day` 자동저장은 두 식단 테이블을 쓰지 않는다. 화면을 오래 열어둔 경우도 대화 기록을 지울 수 없다.

대화 기록의 열량은 직접 입력 합계나 통계에 자동 합산하지 않는다. 같은 음식을 수동 입력한 경우의 이중 합산을 피하기 위한 현재 범위다. 앱에 이 구분을 표시한다. 미확인 영양값은 0이 아니라 null/‘미확인’이다. 제품명만 보고 다른 제품의 영양값을 넣지 않는다. 출처를 확보하면 후속 정정으로 채울 수 있다. 숫자는 유한·음수 금지·상한을 검증하며 출처 없는 영양값은 거절한다.

## 자동 처리 규칙

식단 전용 체크포인트는 저장소 밖 개인 설정 폴더에 권한600으로 둔다. 운동 체크포인트와 섞지 않는다. 승인된 식단 대화만 읽고 read_thread는 최근 10턴 및 cursor를 사용한다. 활성화 전에 존재하던 메시지는 최초로 검증해 반영한 보고 외에 임의 소급하지 않는다.

1. 사용자 메시지에서 명확한 실제 섭취만 추출한다. 추천/질문/재료 보유/단순 재확인은 skip한다.
2. 원본 시각·메시지 ID·실제 식사 날짜와 끼니를 유지한다. 같은 식사의 후속 추가는 기존 foods 전체에 명시한 추가만 합쳐 정정한다. 별도 식사라고 명시하지 않으면 새 키로 중복 생성하지 않는다.
3. 날짜별 status를 읽어 현재 키/메시지/revision을 확인한다. 영양 출처가 없으면 null, nutrition_basis=unknown, estimated=true다. 추정값에는 estimate와 근거를 반드시 남긴다.
4. 권한600 outbox JSON을 저장소 밖에 만들고 전송한다. 실패하면 동일 JSON을 보존해 재시도한다. 서버 상태에서 모든 끼니의 message_id/meal_key/revision/foods를 확인한 후에만 메시지를 처리 완료로 체크포인트에 원자 저장한다.
5. 원본보다 14일 넘게 지연됐거나 대상이 불명확하면 최소 이유만 pending에 남긴다. 정상/변경 없음에는 사용자에게 알림을 보내지 않는다.

## API와 실행 계정

- `POST /api/integrations/meal-reports`: 최대32KiB, HTTPS+기존 업로드 Bearer 키, 별도 기능 플래그. `GET`은 삭제 포함 상태 조회.
- `GET /api/consumed-meals?record_date=YYYY-MM-DD`: 기존 앱과 같은 조회 접근 정책이며 삭제된 식사는 제외한다. 화면은 최초·포커스 복귀·활성 상태의 60초 간격으로 갱신한다. 비공개 식단을 위한 새로운 별도 인증 체계를 추가한 것은 아니다.
- Mac 현재 사용자: 지정 대화 읽기, 개인 체크포인트와 임시 JSON, CLI 실행.
- VM `rocky`: `/home/rocky/gk21` 앱과 backend/frontend systemd 서비스.
- VM `root`: `/etc/gk21/health.env`, `/etc/gk21/health-upload.token`, nginx, 서비스 조작 및 백업. 키를 Mac/저장소/명령 출력으로 복사하지 않는다.
- VM `postgres`: `/postgres/scripts/migrations`의 마이그레이션과 DB DDL. 애플리케이션 DB 역할 `gk21_app`에는 새 두 테이블의 SELECT/INSERT/UPDATE만 부여한다.

```sh
# Mac, 프로젝트 루트. 실제 JSON은 저장소 밖 권한600 파일.
python3 scripts/sync_workout_conversation.py --resource meal \
  --ssh-host rocky@217.142.230.185 \
  --token-file /etc/gk21/health-upload.token status --date YYYY-MM-DD
# 동일 옵션 뒤: submit --file /absolute/private/report.json
```

## 코드와 검증

수신 모델/API/서비스는 `backend/app/{schemas,api,services}/meal_reports.py` 중 모델만 `meal_report.py`다. 인증 플래그는 core/config.py와 core/access.py, 등록은 main.py. 화면은 frontend/app/ConsumedMeals.tsx, app/api/consumed-meals/route.ts와 기존 page.tsx. 전송 도구는 scripts/sync_workout_conversation.py의 선택적 --resource meal이며 기존 운동 기본값을 유지한다. DDL은 sql/migrations/2026-11-10_meal_conversation.sql이다.

```sh
# Mac; 운영 DB를 사용하지 않는 격리 PostgreSQL
PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH PYTHONPATH=backend \
  backend/.venv/bin/pytest backend/tests -q
cd frontend
npx tsc --noEmit
npm run build
```

61개 backend 검사가 통과했다(기존 의존성 경고2개). 동일 메시지의 여러 식사, 중복/정정/삭제/삭제 후 재전송, revision 충돌, 추천·질문·미확정 제외, 수동 기록 보존, 영양 출처/NaN 거절, 인증·HTTP·Origin·본문 크기를 검사했다. TypeScript 검사와 Next production build도 통과했다.

## 배포 및 롤백

운영 배포 전 root 전용 `/var/backups/gk21-meal-20261110/`에 DB dump, 변경 전 소스, nginx, health.env, 기존 frontend .next, Git HEAD와 배포 후 설정 해시를 보관했다. 기존의 별도 MCP 파일 수정은 보존했다.

저사양 VM의 빌드 부하를 피하기 위해 같은 Next 16.2.9의 로컬 production build를 전달했다. `.next/cache`, `.next/dev`, macOS 확장 속성은 배포할 필요가 없다. 소스는 rocky 소유로 전달하고 DB 데이터 디렉터리는 옮기지 않는다.

```sh
# VM: 소스 및 검증된 frontend build를 먼저 준비한 뒤 관리자 실행
sudo install -d -o postgres -g postgres -m 750 /postgres/scripts/migrations
sudo install -o postgres -g postgres -m 640 \
  /home/rocky/gk21/sql/migrations/2026-11-10_meal_conversation.sql /postgres/scripts/migrations/
sudo -u postgres psql -v ON_ERROR_STOP=1 -d gk21 \
  -f /postgres/scripts/migrations/2026-11-10_meal_conversation.sql
sudo -u postgres psql -v ON_ERROR_STOP=1 -d gk21 \
  -c 'GRANT SELECT, INSERT, UPDATE ON meal_conversation_entry, meal_conversation_event TO gk21_app;'
# root: health.env에 MEAL_CONVERSATION_ENABLED=true 추가.
# nginx: HTTP meal-reports exact 경로403, HTTPS exact 경로는 기존 workout-reports와
# 같은 proxy/auth 전달/no-store/access_log off 설정. nginx -t 후 reload.
sudo systemctl restart gk21-backend
# frontend의 기존 .next를 백업한 후 검증된 .next로 교체하고 restart.
```

즉시 기능 중단은 root가 health.env의 MEAL_CONVERSATION_ENABLED=false로 바꿔 backend를 재시작한다. 데이터는 보존되고 앱 식단 조회도 숨겨진다. 로컬 자동화에서도 식단 처리를 중단한다. 전체 되돌리기는 이 기능의 소스 커밋만 git revert하고, frontend를 중지해 `next.before` 빌드로 복구한 뒤 시작한다. 설정 해시가 배포 후 값과 같은지 확인한 경우에만 해당 백업 설정을 복원한다. 다르면 후속 운영 변경을 보존하도록 식단 추가 부분만 되돌린다. 새 테이블을 DROP하거나 전체 DB dump를 덮어써 이후 사용자 기록을 없애지 않는다. 잘못된 식사 한 건은 새 정정/삭제 메시지로 처리한다.

## Git 및 전체 코드 전달

비공개 로컬 작업 브랜치 전체를 공개 저장소로 push하면 안 된다. 공개 안전 브랜치 `codex/health-record-sync`의 최신 커밋을 부모로, **이번 변경 파일만** 적용한 커밋을 만든다. 키·원본 대화·체크포인트·실제 보고 JSON·DB dump·검증 화면은 제외한다. 공개 브랜치 HEAD를 재확인한 후 non-force 갱신한다. VM에서는 관련 파일만 stage/commit하며 기존의 다른 파일 수정은 포함하지 않는다.

사용자에게 전달하는 로컬 전체 코드 묶음에는 변경 파일 원본 전체, 변경 diff, 이 문서를 포함한다. 공개 Git에는 코드와 일반 운영 문서만 포함한다. 실제 사용자 식단과 인증 자료는 코드 묶음에도 넣지 않는다.
