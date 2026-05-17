# Runbook — NAS MinIO Deploy (Stage 1)

> **Story trail**: [MCT-147](../stories/MCT-147.md) · **Issue**: mclayer/mctrader-hub#245 · **Epic**: EPIC-cold-tier-nas-minio
> **D2 amend**: HTTP 운영 (TLS 없음, LAN 내부망 + Stage 1 한정). Stage 2 cutover (MCT-155) 시 TLS 재검토 의무.

본 runbook 은 Synology NAS Container Manager 위에 mctrader cold tier MinIO 컨테이너를 배포하는 step-by-step 절차. 첫 deploy 와 재배포 모두 idempotent — `mc mb --ignore-existing` 이 bucket 존재 시 안전하게 skip.

---

## Prerequisites

| 항목 | 요구사항 | 확인 명령 |
|---|---|---|
| NAS DSM | 7.2 이상 | DSM UI → Control Panel → Info Center |
| Container Manager | 설치 + active | DSM Package Center → Container Manager |
| NAS volume 가용 공간 | 최소 50GB (Stage 1 추정 워크로드) | DSM UI → Storage Manager |
| LAN 접근성 | mctrader 호스트가 NAS IP 9000/9001 port 도달 가능 | mctrader 호스트에서 `nc -zv <NAS_HOST> 9000` |
| credential 생성 | 32-char random string × 2 | `openssl rand -base64 24` (2회 실행, USER/PASSWORD) |

---

## Step 1. NAS DSM + Container Manager 확인

1. NAS DSM (https://<NAS_HOST>:5001) 로그인 (admin 계정)
2. Control Panel → Info Center → "DSM version" 7.2 이상인지 확인
3. Package Center → Container Manager → "Open" 클릭하여 active 상태 확인 (없으면 install)

**FAIL 시**: DSM 7.2 미만이면 사전 DSM upgrade 필요. 본 runbook 진행 전 mclayer org 운영팀에 escalate.

---

## Step 2. 호스트 디렉터리 + 권한 준비

1. NAS DSM File Station → `/volume1/docker/` 디렉터리가 없으면 생성
2. `/volume1/docker/minio/data` 하위 경로 생성 (File Station 우클릭 → Create folder)
3. SSH (DSM Control Panel → Terminal & SNMP → Enable SSH) 로 NAS 접속:
   ```bash
   ssh admin@<NAS_HOST>
   sudo chown -R 1000:1000 /volume1/docker/minio/data
   sudo chmod 750 /volume1/docker/minio/data
   ```
   - MinIO container 는 uid 1000 으로 실행 → 디렉터리 owner 1000:1000 필수
   - `chmod 750` = owner rwx, group rx, others none

**Verify**:
```bash
ls -ld /volume1/docker/minio/data
# 출력 예: drwxr-x--- 2 1000 1000 ... /volume1/docker/minio/data
```

---

## Step 3. compose 파일 + .env transfer

mctrader-data repo 의 `docker/minio/` 디렉터리 전체를 NAS 로 이동. (2026-05-17 이전: mctrader-hub. data 도메인 운영 산출물로 mctrader-data 로 재배치됨.)

### Option A: Synology File Station 업로드

1. DSM File Station → `/volume1/docker/minio/` 디렉터리로 이동
2. mctrader-data repo 의 `docker/minio/docker-compose.yml` + `.env.example` 두 파일 업로드

### Option B: scp (recommended)

mctrader 호스트에서:
```bash
cd c:/workspace/mclayer/mctrader-data
scp docker/minio/docker-compose.yml admin@<NAS_HOST>:/volume1/docker/minio/
scp docker/minio/.env.example admin@<NAS_HOST>:/volume1/docker/minio/
```

---

## Step 4. .env 작성

NAS SSH 접속 후:
```bash
cd /volume1/docker/minio
sudo cp .env.example .env
sudo chmod 600 .env
sudo nano .env   # 또는 vi
```

3 값 모두 채우기:
- `MINIO_ROOT_USER` — `mctrader-admin` 권장 (또는 사용자 임의)
- `MINIO_ROOT_PASSWORD` — `openssl rand -base64 24` 결과로 생성된 32-char random string
- `NAS_HOST` — NAS LAN IP (예: `192.168.1.100`) 또는 DNS name (예: `nas.lan`)

**보안 확인**:
```bash
ls -la /volume1/docker/minio/.env
# 출력 예: -rw------- 1 admin users ... .env  (mode 600)
```

---

## Step 5. Container Manager Compose Import

1. DSM UI → Container Manager → Project → Create
2. **Project name**: `mctrader-minio`
3. **Path**: `/volume1/docker/minio`
4. **Source**: "Use existing docker-compose.yml" 선택
5. **Environment file**: `/volume1/docker/minio/.env` 입력 (또는 UI 가 자동 감지)
6. "Next" → "Build" → 진행 상황 모니터링

**예상 동작**:
- `minio` container start → healthcheck pending → 30s start_period 후 healthcheck PASS
- `minio-init` container start (`minio` healthy 조건 충족 시) → bucket create → exit 0 (정상)
- `minio-init` 가 `restart: "no"` 이므로 1회 실행 후 stopped 상태로 남는다 (정상)

---

## Step 6. Health Check (외부 호스트)

mctrader 호스트 (e.g. `c:/workspace/mclayer`) 에서:

```bash
# S3 API health
curl -sf http://<NAS_HOST>:9000/minio/health/live
# 기대 출력: 응답 body 없음, HTTP 200 (-sf flag 로 fail 시 exit 1)

curl -sI http://<NAS_HOST>:9000/minio/health/live | head -1
# 기대 출력: HTTP/1.1 200 OK
```

**FAIL 시 트러블슈팅**: 본 runbook 부록 B 참조.

---

## Step 7. Console UI bucket 확인

브라우저로 `http://<NAS_HOST>:9001` 접속:

1. `.env` 의 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` 로 로그인
2. 좌측 Navigation → "Buckets" 클릭
3. `mctrader-market` bucket 이 목록에 존재 확인 (size 0 B, objects 0)

**대안 (mc CLI verify)**: NAS SSH 접속 후:
```bash
sudo docker exec mctrader-minio-init mc ls local/
# 기대 출력: mctrader-market/ 라인 1줄
```

---

## Step 8. mctrader-data 측 endpoint 변경 (MCT-155 scope — 본 runbook 명시만)

본 Stage 1 deploy 는 **infra 만** 구성. mctrader-data 의 storage adapter endpoint 변경은 별도 Story (**MCT-155 — Storage adapter S3 cutover**) 에서 처리. 본 runbook 의 step 1~7 PASS 이후 MCT-155 진입.

MCT-155 가 처리할 내용 (cross-ref 만):
- mctrader-data `src/storage/minio_adapter.py` 의 endpoint config 추가
- mctrader-data `.env` 에 `MINIO_ENDPOINT=http://<NAS_HOST>:9000` 박제
- L2/L3 compactor 출력 경로 `s3://mctrader-market/...` 로 cutover
- backfill (기존 로컬 parquet → NAS MinIO upload)

---

## 부록 A: NAS down 시 fallback

NAS 가 down 되어 mctrader-data L2/L3 write 가 fail 하는 경우:

1. mctrader-data `.env` 의 `MINIO_ENDPOINT` 를 일시적으로 unset 또는 `http://localhost:9000` (로컬 fallback MinIO) 으로 변경
2. mctrader-data restart
3. NAS 복구 후 backlog parquet → NAS MinIO 로 manual upload (mc CLI 사용)
4. `MINIO_ENDPOINT` 를 NAS 로 복원 후 다시 restart

**주의**: 본 fallback 절차는 Stage 1 한정. Stage 2 cutover (MCT-155) 이후 정식 retry/backlog 메커니즘이 storage adapter 에 들어가면 fallback runbook 갱신.

---

## 부록 B: 트러블슈팅

### B.1. minio container healthcheck FAIL (`unhealthy` 상태)

증상: Container Manager UI 에서 `minio` 가 unhealthy 표시, `minio-init` 가 시작 못함.

진단:
```bash
sudo docker logs mctrader-minio --tail 50
```

주요 원인 + 해결:
- **mount 실패** (`/data` 경로 read-only): NAS host 의 `/volume1/docker/minio/data` 권한 재확인 (Step 2 재실행)
- **port 충돌** (9000 또는 9001 이미 사용 중): 다른 컨테이너 / DSM 서비스 점유 여부 확인 → port 변경
- **credential parsing 실패**: `.env` 의 password 에 `$` `"` `\` 등 특수 문자 escape 필요 (single quote 로 감싸기)

### B.2. minio-init container loop 또는 fail

증상: `minio-init` 가 종료되지 않고 반복 재시작 (`restart: "no"` 이므로 정상은 1회 실행 후 exit 0).

진단:
```bash
sudo docker logs mctrader-minio-init --tail 50
```

주요 원인 + 해결:
- **mc alias set 실패**: minio container 가 healthy 가 아님 → B.1 먼저 해결
- **bucket create permission denied**: root credential 이 잘못됨 → `.env` 재확인 + minio container restart

### B.3. 외부 호스트에서 curl 실패 (Step 6)

증상: `curl http://<NAS_HOST>:9000/...` 가 timeout 또는 connection refused.

확인 순서:
1. NAS 측 방화벽 (DSM Control Panel → Security → Firewall) 에서 port 9000/9001 허용 (LAN 만)
2. 라우터 측 firewall (NAS port 외부 노출 막혀 있는지 확인 — **외부 노출 금지** 가 정책)
3. mctrader 호스트 측 firewall (드물게 outbound block) 확인

### B.4. Console UI 접속 시 redirect loop

증상: `http://<NAS_HOST>:9001` 접속 시 무한 redirect.

원인: `MINIO_BROWSER_REDIRECT_URL` 의 `${NAS_HOST}` 가 클라이언트가 도달 가능한 주소가 아님.

해결: `.env` 의 `NAS_HOST` 를 클라이언트 (브라우저 실행 host) 가 실제 도달 가능한 IP/DNS 로 수정 후 `docker compose restart minio`.

---

## 완료 기준 (Story MCT-147 AC)

본 runbook step 1~7 모두 PASS = MCT-147 구현완료. AC는 Story §11 PMO retro 시 검증 evidence 로 박제.

- [x] Step 1: DSM 7.2 + Container Manager 확인
- [x] Step 2: 호스트 디렉터리 + 권한 (1000:1000, 750)
- [x] Step 3: compose + .env transfer
- [x] Step 4: .env 작성 (mode 600)
- [x] Step 5: Container Manager Compose import + minio healthy + minio-init exit 0
- [x] Step 6: 외부 호스트 healthcheck HTTP 200
- [x] Step 7: Console UI 또는 mc CLI 로 bucket `mctrader-market` 존재 확인
