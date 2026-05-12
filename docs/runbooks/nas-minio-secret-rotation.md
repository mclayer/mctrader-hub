# Runbook — NAS MinIO Credential Rotation (90d)

> **Story trail**: [MCT-147](../stories/MCT-147.md) · **Cadence**: 90 days · **Owner**: mclayer org operator
> **D2 amend mitigation**: HTTP 운영 환경에서 credential leak 위험 보완. .env 0600 + 본 rotation 의무.

본 runbook 은 mctrader cold tier MinIO 의 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` 를 90일 주기로 회전시키는 절차. NAS Container Manager + mctrader-data adapter 양측 동기 갱신.

---

## Rotation cadence

- **정기**: 90 days from last rotation (PMO retro 또는 calendar reminder 로 trigger)
- **긴급 (emergency)**: credential leak 의심 시 즉시 — 본 runbook 의 "긴급 rotation" 절 참조

### Last rotation log

| Rotation date | Operator | 다음 rotation due | Note |
|---|---|---|---|
| (TBD — MCT-147 deploy 일자) | (TBD) | (TBD + 90d) | Initial deploy, MCT-147 |

위 표는 매 rotation 시 row 1줄 append 의무 (가장 최근 row 가 truth).

---

## Step 1. 새 credential 생성

NAS 호스트 또는 안전한 로컬 환경에서:

```bash
# 새 user (선택 — 기존 user 유지 가능, password 만 회전해도 OK)
NEW_USER=$(echo "mctrader-admin-$(date +%Y%m%d)")
echo "NEW_USER=$NEW_USER"

# 새 password (32-char random, URL-safe base64)
NEW_PASSWORD=$(openssl rand -base64 24)
echo "NEW_PASSWORD=$NEW_PASSWORD"
```

**보안**: 위 값을 메모리/메신저/메일 등에 평문으로 보관 금지. 즉시 Step 2 진행하여 NAS .env 에 박제 + 본 터미널 history 정리 (`history -c`).

---

## Step 2. NAS .env 갱신

NAS SSH 접속:
```bash
ssh admin@<NAS_HOST>
cd /volume1/docker/minio
sudo cp .env .env.bak.$(date +%Y%m%d)   # 직전 .env 백업 (긴급 롤백용)
sudo chmod 600 .env.bak.$(date +%Y%m%d)
sudo nano .env
```

`MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` 두 값 Step 1 결과로 교체. `NAS_HOST` 는 그대로.

**Verify**:
```bash
ls -la .env*
# .env (mode 600) + .env.bak.YYYYMMDD (mode 600) 두 파일 확인
```

---

## Step 3. MinIO container restart

NAS DSM UI → Container Manager → Project `mctrader-minio` → Action → "Build" (rebuild — env reload).

또는 SSH 로:
```bash
cd /volume1/docker/minio
sudo docker compose down
sudo docker compose up -d
```

**주의**: `docker compose restart minio` 는 env 변경을 반영하지 않을 수 있음 (compose v2 의 known behavior). `down` → `up -d` 가 안전.

**Verify**:
```bash
sudo docker ps | grep mctrader-minio
# mctrader-minio: status = (healthy)
# mctrader-minio-init: exited (0)  ← idempotent: 기존 bucket 그대로, mc mb --ignore-existing 이 skip
```

`mc alias` 재설정 확인:
```bash
sudo docker exec mctrader-minio-init mc ls local/
# 기대 출력: mctrader-market/ 라인 (실패 시 새 credential 이 minio-init container 에 반영 안된 것)
```

---

## Step 4. mctrader-data 측 credential 갱신

mctrader 호스트 (`c:/workspace/mclayer/mctrader-data`) 에서:

```bash
cd c:/workspace/mclayer/mctrader-data
# .env 편집 (path 는 MCT-155 land 후 정해짐 — Stage 1 에서는 본 step skip)
```

**Stage 1 시점 (MCT-155 land 전)**: 본 step 은 cross-ref 만. mctrader-data 가 아직 NAS MinIO 를 endpoint 로 쓰지 않으므로 갱신 불필요.

**Stage 2 cutover (MCT-155 land 후)**: 
1. mctrader-data `.env` 의 `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` 를 Step 1 결과로 교체
2. mctrader-data process restart
3. 짧은 outage window (몇 초) 발생 가능 → 가능하면 시장 close 시간대에 rotation 실행

---

## Step 5. Rotation log 박제

본 파일의 "Last rotation log" 표에 새 row append:

```markdown
| 2026-XX-XX | mccho | 2026-YY-YY | Routine 90d rotation |
```

git commit:
```bash
cd c:/workspace/mclayer/mctrader-hub
git checkout -b chore/minio-rotation-$(date +%Y%m%d)
git add docs/runbooks/nas-minio-secret-rotation.md
git commit -m "chore(minio): rotation log — $(date +%Y-%m-%d)"
gh pr create --base main --title "chore(minio): credential rotation log $(date +%Y-%m-%d)" --body "Routine 90d rotation per MCT-147 runbook."
```

---

## Step 6. .env.bak 백업 파일 정리

rotation 후 1주일 이상 정상 운영 확인되면 백업 .env.bak 파일 삭제:

```bash
ssh admin@<NAS_HOST>
cd /volume1/docker/minio
sudo rm .env.bak.YYYYMMDD   # 1주일 이상 지난 파일만
```

---

## Step 7. NAS firewall 9000/9001 IP-allowlist re-audit

> **추가 trail**: MCT-150 FIX#1 F1 (2026-05-13) — AC-5 IP-allowlist re-audit 박제 위치 결정 = 본 runbook Step 7 신설 (90d rotation cadence 자연 정합).
> **cross-ref**: MCT-147 4중 mitigation 의 IP-allowlist 축 + R10 (방화벽 룰 drift) Stage 2 진입 시 사전 차단.

매 rotation 시점에 NAS 측 방화벽 port 9000/9001 의 IP-allowlist 무결성 audit 의무.

### 7.1 Re-audit 절차 (NAS Synology DSM UI)

1. NAS DSM 접속: `https://<NAS_HOST>:5001`
2. Control Panel → Security → Firewall → Edit Rules
3. port 9000 (MinIO API) + 9001 (MinIO Console) rule 확인:
   - **Source IP**: mctrader 호스트 IP **only** (단일 IP 또는 LAN /24 subnet)
   - **Action**: Allow
   - **외부 IP / 0.0.0.0/0 / wildcard 발견 0**

### 7.2 Re-audit 절차 (CLI alternative)

DSM UI 접근 불가 시:

```bash
ssh admin@<NAS_HOST>
sudo /usr/syno/bin/synofirewall list | grep -E "9000|9001"
# 기대 출력: 단일 mctrader 호스트 IP 만 listed
```

또는 외부 connectivity probe (LAN 외부 host 에서):

```bash
# mctrader 호스트 외 환경에서 실행
curl -sI --max-time 5 http://<NAS_HOST>:9000 || echo "BLOCKED (expected)"
# 기대 출력: BLOCKED — 외부 IP 에서 NAS:9000 unreachable
```

### 7.3 Audit cadence record 표 갱신 의무

본 runbook 의 "Last rotation log" 표 의 Note 열에 audit 결과 박제:

```markdown
| 2026-XX-XX | mccho | 2026-YY-YY | Routine 90d rotation + IP-allowlist re-audit PASS (단일 mctrader 호스트 IP only 확인) |
```

### 7.4 Failure mode (외부 IP 발견 시)

audit 중 외부 IP 또는 wildcard rule 발견:

1. **즉시 방화벽 rule 갱신** — DSM UI 또는 `synofirewall` cli 로 외부 IP 삭제
2. **긴급 credential rotation trigger** — Step 1~5 즉시 재실행 (외부 노출 기간 동안 credential leak 의심 가정)
3. **leak 원인 분석** — `긴급 Rotation` 절차 3번 (MinIO access log 회수) 동일 적용
4. **PMO Story trigger** — finding 박제 + R10 (방화벽 룰 drift) 사례 누적, ADR-027 mitigation 강화 후보

---

## 긴급 Rotation (Emergency)

credential leak 의심 시 (예: `.env` 파일이 git 에 commit 됨, 로그에 평문 노출, NAS 외부 노출 발견):

1. **즉시 Step 1~3 실행** — 정기 schedule 무시
2. mctrader-data 측이 운영 중이면 **outage 감수하고 Step 4 동시 실행** (credential mismatch 로 일시 작동 불가 허용)
3. leak 원인 분석:
   - git log 조사 (`git log --all --full-history -- .env`)
   - 노출된 채널의 audit log 회수
   - 노출 시점 ~ rotation 시점 사이 무단 접근 흔적 (MinIO access log) 확인:
     ```bash
     sudo docker logs mctrader-minio --since 24h | grep -E "(GetObject|PutObject|ListBuckets)" | head -50
     ```
4. PMO Story trigger — finding 박제 + 회수 절차 / 재발 방지책 ADR 화

---

## 완료 기준

각 정기 rotation 1 cycle:
- [x] Step 1: 새 credential 생성 (메모리 외 평문 잔존 없음)
- [x] Step 2: NAS .env 교체 + .env.bak 백업
- [x] Step 3: MinIO container down → up → healthy + bucket 존재 확인
- [x] Step 4: mctrader-data 측 갱신 (Stage 2 land 이후만 적용)
- [x] Step 5: rotation log row append + git commit
- [x] Step 6: 백업 .env.bak 정리 (1주일 후)
- [x] Step 7: NAS firewall 9000/9001 IP-allowlist re-audit (MCT-150 FIX#1 F1 신설, 2026-05-13 — Stage 2 진입 시 + 매 90d rotation 동반)

본 7 step PASS = 1 rotation cycle 완료. 다음 rotation due date 를 calendar 에 등록.
