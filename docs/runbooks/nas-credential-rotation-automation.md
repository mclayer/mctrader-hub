# Runbook — NAS MinIO Credential Rotation Automation (90d cron)

> **Story trail**: [MCT-176](../stories/MCT-176.md) · **D9=D** (ADR-030 §D9) · **Cadence**: 90 days
> **Owner**: mclayer org operator
> **cross-ref**: [Manual rotation](nas-minio-secret-rotation.md) — 본 runbook 은 automation layer.
>   manual rotation 의 Step 1~7 절차를 `scripts/rotate-nas-credentials.sh` 로 자동화.
>   manual runbook 은 emergency / audit / NAS DSM UI 절차에 그대로 유효.

---

## Overview

`rotate-nas-credentials.sh` 는 NAS MinIO credential 90d 정기 rotation 을 5 step 으로 자동화:

1. 새 credential 생성 (openssl rand)
2. `.env.prod` 갱신 (sed in-place + 백업)
3. mctrader compose restart (down → up -d, 30s health poll)
4. Slack webhook 알림 발송
5. rotation log git commit

cron schedule 로 90d 마다 자동 실행. Slack send 실패 시 GitHub Issue 자동 발의.

---

## Step 1. 사전 준비 (초기 1회)

### 1.1 환경변수 설정 (`.env.prod`)

rotation script 가 읽는 변수:

```bash
# .env.prod (0600 권한 필수)
NAS_MINIO_ACCESS_KEY=<current_access_key>
NAS_MINIO_SECRET_KEY=<current_secret_key>
NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
SLACK_ROTATION_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
GITHUB_ROTATION_ISSUE_REPO=mclayer/mctrader-hub
```

```bash
chmod 600 .env.prod
```

### 1.2 Slack webhook 생성

1. Slack → Apps → Incoming Webhooks → Add New Webhook to Workspace
2. 채널 선택 (예: `#mctrader-ops`)
3. Webhook URL 복사 → `.env.prod` 의 `SLACK_ROTATION_WEBHOOK_URL` 에 박제

### 1.3 GitHub token 설정 (Issue 자동 발의용)

```bash
# gh CLI 로그인 확인
gh auth status
# github.com: mclayer8865@gmail.com  ← 인증 확인
```

`gh auth token` 이 유효하면 Issue 자동 발의 (`gh issue create`) 동작.

---

## Step 2. 스크립트 배치 확인

```bash
ls -la scripts/rotate-nas-credentials.sh
# 기대: -rwxr-xr-x  (실행 권한 확인)
bash -n scripts/rotate-nas-credentials.sh
# 기대: syntax OK (출력 없음)
```

dry-run 사전 검증:

```bash
bash scripts/rotate-nas-credentials.sh --dry-run
# 기대:
# [DRY-RUN] Step 1: would generate new credentials
# [DRY-RUN] Step 2: would update .env.prod (backup → sed)
# [DRY-RUN] Step 3: compose down && up -d: skipped
# [DRY-RUN] Step 4: Slack webhook: would send rotation notice
# [DRY-RUN] Step 5: git commit rotation log: skipped
# [DRY-RUN] exit 0
```

---

## Step 3. cron schedule 등록

### 3.1 crontab 등록 (mctrader 호스트)

```bash
crontab -e
```

아래 라인 추가:

```cron
# NAS MinIO credential rotation — 90d cadence
# 매년 1월 1일 + 4월 1일 + 7월 1일 + 10월 1일 03:00 KST (UTC 18:00 전일)
0 18 1 1,4,7,10 * cd /path/to/mctrader-hub && bash scripts/rotate-nas-credentials.sh >> /var/log/mctrader-rotation.log 2>&1
```

**주의**: 실 rotation date 는 최초 rotation 일 기준 +90d 로 조정. 위 예시 cron 은 분기 1일 고정 (조정 필요).

### 3.2 cron 등록 확인

```bash
crontab -l | grep rotate
# 기대: 위 rotate-nas-credentials.sh 라인 출력
```

### 3.3 log 파일 설정

```bash
sudo touch /var/log/mctrader-rotation.log
sudo chmod 644 /var/log/mctrader-rotation.log
# logrotate 설정 (선택)
sudo tee /etc/logrotate.d/mctrader-rotation <<'EOF'
/var/log/mctrader-rotation.log {
    monthly
    rotate 12
    compress
    missingok
    notifempty
}
EOF
```

---

## Step 4. 실 rotation 흐름 (자동 실행)

cron 이 `rotate-nas-credentials.sh` 를 실행하면 아래 순서로 진행:

### 4.1 새 credential 생성

```bash
NEW_ACCESS_KEY="mctrader-admin-$(date +%Y%m%d)"
NEW_SECRET_KEY="$(openssl rand -base64 24 | tr '+/' '-_')"
```

생성된 값은 메모리 내 변수만 사용. 디스크/로그에 평문 기록 금지 (script 내 `set +x` 로 echo 차단).

### 4.2 `.env.prod` 갱신

```bash
cp .env.prod ".env.prod.bak.$(date +%Y%m%d)"
chmod 600 ".env.prod.bak.$(date +%Y%m%d)"
sed -i "s/^NAS_MINIO_ACCESS_KEY=.*/NAS_MINIO_ACCESS_KEY=${NEW_ACCESS_KEY}/" .env.prod
sed -i "s/^NAS_MINIO_SECRET_KEY=.*/NAS_MINIO_SECRET_KEY=${NEW_SECRET_KEY}/" .env.prod
```

### 4.3 compose restart

```bash
docker compose --profile prod down
docker compose --profile prod up -d
# 30s health poll
for i in $(seq 1 30); do
  STATUS=$(docker inspect mctrader-collector --format '{{.State.Status}}' 2>/dev/null || echo "not_found")
  [ "$STATUS" = "running" ] && break
  sleep 1
done
```

compose restart = secret 갱신 vehicle (D9 ADR-030 결정).

### 4.4 Slack 알림

성공 시:

```json
{
  "text": ":key: NAS MinIO credential rotation DONE ($(date +%Y-%m-%d)). Next due: $(date -d '+90 days' +%Y-%m-%d). Operator: cron@mctrader-host"
}
```

### 4.5 실패 시 처리 (Slack send 실패 → GitHub Issue 자동 발의)

```bash
# Slack webhook 실패 시 (exit code ≠ 0)
gh issue create \
  --repo "${GITHUB_ROTATION_ISSUE_REPO}" \
  --title "[ALERT] NAS credential rotation Slack notification FAILED ($(date +%Y-%m-%d))" \
  --body "cron rotation 완료됐으나 Slack webhook 발송 실패. 수동 확인 의무. log: /var/log/mctrader-rotation.log"
```

### 4.6 rotation log git commit

```bash
# rotation log row append (nas-minio-secret-rotation.md "Last rotation log" 표)
git checkout -b "chore/minio-rotation-$(date +%Y%m%d)"
git add docs/runbooks/nas-minio-secret-rotation.md
git commit -m "chore(minio): credential rotation log — $(date +%Y-%m-%d) (auto)"
gh pr create \
  --base main \
  --title "chore(minio): credential rotation log $(date +%Y-%m-%d)" \
  --body "Automated 90d rotation per MCT-176 D9. Manual verify: run AC-1~AC-5."
```

---

## Step 5. failure handling 상세

| 실패 단계 | 증상 | 자동 처리 | 수동 처리 |
|-----------|------|-----------|-----------|
| Step 4.1 openssl 실패 | exit 非0 | `trap ERR` → rollback + Slack/Issue alert | 호스트 `openssl` 버전 확인 |
| Step 4.2 sed 실패 | `.env.prod` 불변 | `.env.prod.bak` 자동 복원 + alert | 파일 권한/경로 확인 |
| Step 4.3 compose 기동 실패 | container unhealthy > 60s | compose down + `.env.prod.bak` 복원 + emergency rotation alert | [manual rotation](nas-minio-secret-rotation.md) Step 3 참조 |
| Step 4.4 Slack 실패 | webhook 4xx/5xx | GitHub Issue 자동 발의 (`gh issue create`) | Issue 수동 확인 후 Slack 설정 점검 |
| Step 4.6 git commit 실패 | push reject / branch 충돌 | warning log | 수동 `git push` 후 PR 생성 |

### 긴급 rollback

rotation 후 collector 이상 감지 시:

```bash
# 직전 .env.prod.bak 복원
cp ".env.prod.bak.$(date +%Y%m%d)" .env.prod
docker compose --profile prod down && docker compose --profile prod up -d
```

`.env.prod.bak` 파일은 rotation 후 1주일 유지 후 삭제:

```bash
find . -name ".env.prod.bak.*" -mtime +7 -delete
```

---

## 완료 기준 (자동 rotation 1 cycle)

- [ ] Step 4.1: 새 credential 생성 (평문 잔존 없음)
- [ ] Step 4.2: `.env.prod` 갱신 + `.env.prod.bak` 백업 (0600)
- [ ] Step 4.3: compose down → up -d → collector running (30s health poll)
- [ ] Step 4.4: Slack webhook 발송 성공 (또는 GitHub Issue 자동 발의)
- [ ] Step 4.6: rotation log git commit + PR 생성
- [ ] 1주일 후: `.env.prod.bak` 삭제

## cross-ref

- [Manual rotation runbook](nas-minio-secret-rotation.md) — NAS DSM UI 경유 수동 절차 (emergency 시 참조)
- [ADR-030 §D9](../adr/ADR-030-docker-stack-governance.md) — D9 credential rotation 결정 근거
- `scripts/rotate-nas-credentials.sh` — 자동화 스크립트 (MCT-176 Phase 2 PR1 LAND 시 신규)
- [MCT-176 Story](../stories/MCT-176.md) §6 R-MCT-176-2 — rotation 실패 risk 상세
