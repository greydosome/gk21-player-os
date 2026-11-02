# 로그인 없이 건강 기록 자동 업데이트

## 현재 범위

- 앱과 기존 조회/수정 API: 지금처럼 공개, 로그인 없음.
- 기존 Scriptable 위젯: 인증 추가나 주소 변경 없이 사용 가능.
- 새 건강 업로드: `https://217.142.230.185/api/integrations/apple-health/daily`에 전용 Bearer 토큰을 한 번 설정.
- 단축어 업로드 → 날짜별 자동 기록 카드 → 기존 식단/운동 코칭에 반영.
- 앱 로그인/30일 세션/로그아웃/위젯 인증은 제거했다.

공개 조회는 사용자가 선택한 동작이며 기존 쓰기 API도 공개 상태다. 업로드 토큰은 새 건강 수신 경로만 보호한다. 운영에 아직 적용하지 않았다.

## 담당자가 수행할 HTTPS 준비 (배포 승인 후)

도메인 구매 없이 현재 IP에 Let’s Encrypt 인증서를 사용한다. Certbot 5.4 이상 및 443 inbound 필요. 3000/8000은 loopback으로 제한하고 nginx를 경유한다. 사내 SASE 차단 해결은 범위 밖이며 모바일 데이터/개인 Wi-Fi에서 검증한다.

1. 실제 서버 설정을 확인·백업하고 기존 nginx HTTP 설정에 아래 경로를 먼저 추가한다. 아직 인증서가 없는 상태에서 443 설정을 먼저 설치하지 않는다.

```nginx
location ^~ /.well-known/acme-challenge/ {
    root /var/www/letsencrypt;
    try_files $uri =404;
}
```

2. webroot 디렉터리를 준비하고 테스트 인증서를 발급한다.

```sh
certbot certonly --staging --preferred-profile shortlived \
  --webroot --webroot-path /var/www/letsencrypt \
  --ip-address 217.142.230.185 --cert-name gk21-ip-staging
```

3. 검증 후 신뢰되는 운영 인증서를 발급한다. 약관/계정 연락처는 운영 설정에 맞게 처리한다.

```sh
certbot certonly --preferred-profile shortlived \
  --webroot --webroot-path /var/www/letsencrypt \
  --ip-address 217.142.230.185 --cert-name 217.142.230.185
```

4. `deploy/nginx-apple-health.conf.example`를 기존 설정에 병합하고 nginx -t 후 reload. 기존 HTTP 앱/위젯은 유지하고 건강 업로드만 HTTPS를 강제한다. Backend는 `--host 127.0.0.1 --proxy-headers --forwarded-allow-ips=127.0.0.1`로 nginx 헤더만 신뢰한다.
5. 기존 certbot 갱신 스케줄이 있으면 재사용한다. 없으면 제공된 renew service/timer에서 실제 실행 경로를 확인하고 설치한다. 갱신 후 nginx 검사/reload hook을 반드시 적용한다. 6일 인증서라 자동 갱신 실패를 방치하면 업로드가 끊긴다.
6. `certbot renew --cert-name 217.142.230.185 --dry-run`으로 갱신을 확인한다. 테스트 인증서는 `certbot delete --cert-name gk21-ip-staging`으로 정리할 수 있다. 외부 알림 연결은 별도로 구현하지 않았다.

## 건강 업로드 활성화와 확인

1. 백업 후 추가 마이그레이션만 적용한다. 앱/실제 DB 변경은 별도 승인 대상이다.
2. 업로드 토큰 해시를 서버에, 원문을 단축어에 설정한다. 앱 비밀번호나 세션 키는 필요 없다.
3. 수신만 켜서 가상 데이터 한 건 업로드 → 앱 날짜별 카드에 수면/운동/체중 표시 → 재전송 중복 없음 → 기존 수동 기록 보존을 확인한다.
4. 실제 아이폰 건강 데이터를 비교한다. 잠금 상태 수집 실패, 누락 항목, 지연 동기화도 확인한다. 상세 JSON/단축어 순서는 `apple-health-integration.md` 참고.
5. 코칭 플래그와 서버 스케줄을 켜고 기존 식단과 함께 결과가 저장되는지 확인한다.

롤백은 단축어/코칭 스케줄 중지 후 건강 두 플래그를 끄는 것으로 시작한다. 기존 수동 기록은 보존한다. 토큰 교체는 단축어 값과 서버 해시만 변경하면 된다.

공식 근거: https://letsencrypt.org/2026/03/11/shorter-certs-certbot/
