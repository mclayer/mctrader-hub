# Docker Stack Deploy Runbook

> **Stub** — MCT-175 Phase 1 박제. 상세 본문 = MCT-176~181 LAND 시 점진 보강.
> Owner: GitOpsAgent / DevOps (MCT-175 seed, MCT-179 확장)

## Overview

mctrader-hub compose stack (EPIC-mctrader-docker-stack, ADR-030) 운영 deploy 절차.

- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`

## Profile 구분

| Profile | MinIO endpoint | 용도 |
|---------|---------------|------|
| `dev`   | `http://minio:9000` (hub MinIO) | 로컬 개발 + 테스트 |
| `prod`  | `http://mcnas01.internal.mclayer.it:9000` | 운영 (NAS MinIO) |

## Step 1: Prerequisite check

```bash
# git pull + worktree clean
git -C c:/workspace/mclayer/mctrader-hub pull origin main

# .env 파일 존재 확인
# dev: .env.dev / prod: .env.prod (gitignored, 별도 secure 관리)
ls c:/workspace/mclayer/mctrader-hub/.env.dev     # dev
ls c:/workspace/mclayer/mctrader-hub/.env.prod    # prod (secret — 0600)

# Docker 실행 확인
docker info >/dev/null 2>&1 && echo "Docker OK"
```

## Step 2: .env.{dev|prod} prepare

```bash
# dev: .env.example 참조 → .env.dev 생성
cp .env.example .env.dev
# 편집: NAS_MINIO_ENDPOINT=http://minio:9000 (hub MinIO)

# prod: .env.prod.example 참조 → .env.prod 생성 (secret 포함)
cp .env.prod.example .env.prod
chmod 0600 .env.prod
# 편집: NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
#       NAS_MINIO_ACCESS_KEY=<from_nas_minio_console>
#       NAS_MINIO_SECRET_KEY=<from_nas_minio_console>
```

**rotation**: NAS credential 90d 순환 의무 (MCT-176 `scripts/rotate-nas-credentials.sh` 참조).

## Step 3: Preflight script (prod only)

```bash
# prod profile 진입 전 NAS endpoint preflight 의무 (ADR-030 §D7)
./scripts/preflight-nas-dns.sh .env.prod

# exit 0  = DNS + TCP + S3 ALL PASS → compose up 진행 가능
# exit 10 = DNS FAIL → NAS hostname 확인 (mcnas01.internal.mclayer.it 해석 여부)
# exit 20 = TCP FAIL → NAS port 9000 방화벽 확인
# exit 30 = S3 FAIL → credential 또는 bucket 확인
# exit 99 = env parse FAIL → .env.prod 파일 경로 확인
```

## Step 4: compose up (profile 지정)

```bash
# dev
docker compose --profile dev --env-file .env.dev up -d

# prod (MCT-176+ LAND 후 어플리케이션 service 포함)
docker compose --profile prod --env-file .env.prod up -d

# 특정 service 만
docker compose --profile dev --env-file .env.dev up -d postgres redis prometheus grafana
```

healthcheck 대기:
```bash
docker compose ps          # STATUS 확인
docker compose logs -f     # 기동 로그 실시간 확인
```

## Step 5: Health verify

```bash
# 인프라 service health
curl -s http://localhost:9090/-/healthy      # Prometheus
curl -s http://localhost:3000/api/health     # Grafana

# 어플리케이션 (MCT-176+ LAND 후 활성화)
# curl -s http://localhost:<collector_port>/metrics  # collector /metrics
# curl -s http://localhost:<engine_port>/metrics     # paper-engine /metrics
```

---

## Appendix A: DR mode (MCT-179 보강 예정)

NAS 접근 불가 시 DR mode state machine (ADR-030 §D17, `dr_mode.py`):

| state | 의미 |
|-------|------|
| CLOSED | 정상 운영 |
| OPEN | NAS 차단 (sliding window 5xx 5회 또는 p99 >500ms 3회) |
| HALF_OPEN | 30s 후 probe |
| UNKNOWN_TIER | D10 exemption (30d window) |

manual override: `set_mode(state, reason)` (MCT-179 LAND 후 CLI 제공 예정).

## Appendix B: Cross-repo lock gate (D13)

hub PR push 마다 자동 실행:
```bash
python scripts/check_cross_repo_locks.py
# exit 0 = 6 repo python_version + lib major version aligned
# exit 1 = python_version drift
# exit 2 = lib major version drift (pyarrow/boto3/pydantic/websockets)
```

### Secret 등록 가이드 (MCT-176 AC-5 — MCTRADER_CROSS_REPO_TOKEN)

`.github/workflows/cross-repo-lock-check.yml` 의 pull_request auto trigger 는
`MCTRADER_CROSS_REPO_TOKEN` GitHub Actions secret 이 등록된 상태에서만 정상 동작합니다.

**등록 절차:**

1. GitHub PAT (Personal Access Token) 생성
   - scope: `repo` (read 권한으로 6 repo checkout 가능)
   - Expiration: 90d 권장 (credential rotation 주기와 동일)

2. mctrader-hub repo secret 등록
   ```
   GitHub repo → Settings → Secrets and variables → Actions → New repository secret
   Name:  MCTRADER_CROSS_REPO_TOKEN
   Value: <PAT 값>
   ```

3. 등록 후 verify
   ```bash
   # hub repo 에서 PR push 시 cross-repo-lock-check workflow 자동 실행 확인
   # 또는 workflow_dispatch 로 수동 trigger
   gh workflow run cross-repo-lock-check.yml --repo mclayer/mctrader-hub
   ```

**미등록 시 동작**: `pull_request` trigger 시 checkout 단계에서 403 → workflow fail.
`workflow_dispatch` (수동) 는 secret 미등록 상태에서도 실행 가능 (internal token 사용).

> ADR-030 §D13 amendment: "MCT-176 secret 등록 후 auto trigger 활성화 의무"

## Changelog

| 날짜 | Story | 변경 내용 |
|------|-------|----------|
| 2026-05-15 | MCT-175 | 초기 stub 생성 (Phase 1 박제) |
| 2026-05-15 | MCT-176 | MCTRADER_CROSS_REPO_TOKEN secret 등록 가이드 + collector service 활성화 (Phase 2 PR1) |
| TBD | MCT-177 | paper-engine daemon 절차 추가 |
| TBD | MCT-179 | observability + DR mode 절차 추가 |
| TBD | MCT-180 | integration smoke verify 절차 추가 |
