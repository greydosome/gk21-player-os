# 사용자가 신경 쓸 일을 줄인 접속 방식

## 확정한 방식

- 새 도메인 구매/가입 없이 `https://217.142.230.185` 사용.
- 앱은 비밀번호 한 번 입력 → 이 브라우저/PWA에서 최대 30일 로그인 유지. 기기별로 처음 로그인은 필요하며 쿠키 삭제/비밀번호 교체/만료 시 다시 로그인한다.
- 위젯은 기존 Basic 인증 호환을 유지해 Scriptable Keychain에 한 번 저장. 정기적인 로그인 화면 없음.
- 단축어는 별도 업로드 토큰 한 번 저장. 업로드할 때마다 로그인하지 않음.
- 인증서는 서버가 자동 갱신한다. 별도 VPN 앱을 켜거나 도메인을 관리할 필요 없음.
- 앱에서 로그아웃 가능. 쿠키는 JavaScript로 읽을 수 없고 건강 API/로그인 페이지/앱 HTML은 서비스워커에 저장하지 않는다.

이 문서는 배포 준비이며 서버에 적용된 상태가 아니다. 현재 HTTP 주소에 비밀번호/토큰/건강 정보를 보내지 않는다.

## 담당자가 수행할 서버 전환 순서 (사용자에게 명령 실행을 맡기지 않음)

1. SSH 접근 권한과 배포 승인을 확보한 뒤 실제 nginx/service/firewall/DB를 확인한다. 서버 설정 백업과 인증 없이 노출된 기존 경로 목록을 먼저 확보한다.
2. `nginx -V`에서 http_auth_request_module 확인. Certbot 5.4 이상, nginx/uvicorn/Next 실행 경로와 IP가 고정인지 확인. 443 inbound를 허용하고 3000/8000은 loopback만 사용한다. 사내 SASE 차단 우회는 이 작업 범위가 아니며 아이폰 모바일 데이터/개인 Wi-Fi 기준으로 검증한다.
3. `/var/www/letsencrypt`를 만들고 HTTP nginx에 `/.well-known/acme-challenge/` webroot만 먼저 추가한다. 아직 존재하지 않는 인증서 파일을 참조하는 443 블록을 먼저 설치하지 않는다.
4. 아래 명령으로 staging 발급 검증. staging 인증서는 iPhone에서 신뢰되지 않으므로 앱에 사용하지 않는다.

```sh
certbot certonly --staging --preferred-profile shortlived \
  --webroot --webroot-path /var/www/letsencrypt \
  --ip-address 217.142.230.185 --cert-name gk21-ip-staging
```

5. staging 검증 후 production 인증서를 발급한다. ACME 계정 약관·연락처 선택은 실제 운영 설정에 맞게 처리한다.

```sh
certbot certonly --preferred-profile shortlived \
  --webroot --webroot-path /var/www/letsencrypt \
  --ip-address 217.142.230.185 --cert-name 217.142.230.185
```

6. `deploy/nginx-apple-health.conf.example`를 기존 설정에 병합한다. 중복 server/default_server와 예전 IP HTTP API 경로를 확인한다. `nginx -t` 성공 후 reload. 공인 IP로 실제 인증서 체인과 인증 우회 차단을 검증한다.
7. backend에 랜덤 앱 비밀번호의 SHA-256, 업로드 토큰의 SHA-256, 독립적인 32바이트 이상 랜덤 `APP_SESSION_SECRET`을 설정한다. 앱 비밀번호/토큰은 각각 32바이트 이상의 난수 기반 값을 사용한다. 키는 저장소·채팅·로그에 넣지 않는다. 세션 키는 브라우저나 단축어에 보내지 않는다.
8. APP_AUTH_ENABLED를 켜고 `/login` → `/api/auth/check` → 기존 앱 읽기/쓰기 순서로 검증한다. 건강 수신과 코칭은 기존 안내의 수집-only 검증 후 켠다. 별도 htpasswd 설정은 필요 없다.
9. 인증서 갱신을 구성한다. 기존 certbot timer가 있으면 그것을 재사용하고 nginx reload deploy-hook을 추가한다. 없으면 제공한 `gk21-cert-renew.service`/`.timer`의 실행 경로를 확인해 설치한다. 두 스케줄을 중복 설치하지 않는다. 갱신 후 `nginx -t && systemctl reload nginx`가 실행돼야 새 인증서가 반영된다.
10. 검증용 인증서는 더 이상 필요 없으면 `certbot delete --cert-name gk21-ip-staging`으로 정리한다. `certbot renew --cert-name 217.142.230.185 --dry-run`과 timer의 다음 실행 시각, reload 성공을 검증한다. 6일 인증서이므로 갱신 실패를 방치하면 앱/위젯/단축어 모두 연결이 끊긴다. 기존 서버 장애 알림이 있으면 이 unit 실패를 연결한다. 현재 저장소에는 별도의 외부 알림 연결은 없다.
11. 모바일 데이터에서 Safari와 홈 화면 PWA를 각각 검증한다. 위젯 주소/Keychain 자격 증명과 단축어 주소/토큰을 한 번 설정하고 HTTP 이전 위젯을 교체한다.

## 세션·기기 교체·롤백

쿠키는 발급 시점부터 30일간 유효하며 자동 무기한 연장하지 않는다. 비밀번호 해시 또는 세션 서명 키를 바꾸면 모든 브라우저 세션이 즉시 무효화된다. 앱 로그아웃은 해당 브라우저 쿠키를 삭제한다. 유출된 쿠키 사본까지 즉시 폐기해야 할 경우 키를 교체한다. 별도 세션 DB는 추가하지 않는다.

위젯은 앱 비밀번호 교체 시 Keychain 값만 바꾼다. 단축어 토큰은 별도여서 앱 로그아웃/세션 만료의 영향을 받지 않는다. 기기를 잃어버리면 관련 자격 증명을 교체한다.

롤백할 때 HTTPS와 앱 인증은 유지한다. 새 건강 수신/코칭만 끄고 기존 기록 화면으로 돌아간다. 세션 방식이 문제면 인증된 Basic 클라이언트로 조사할 수 있지만 무인증 공개로 돌아가지 않는다.

## 검증된 공식 근거

Let’s Encrypt는 IP 인증서를 일반 제공하며 Certbot 5.4 이상 webroot 방식을 안내한다. IP 인증서는 shortlived 프로필로 약 6일 유효하고, 자동 갱신 및 웹 서버 reload hook이 필요하다.
https://letsencrypt.org/2026/03/11/shorter-certs-certbot/
