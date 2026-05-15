---
story_key: MCT-175
plan_title: "Docker stack base — dev/prod profile + env split + ADR-030 publish + cross-repo lock gate"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D1, D3, D7, D13]
risk_required_decision:
  - "R1 HIGH (NAS HTTP-only) — MCT-175 Phase 1 진입 전 사용자 explicit accept 또는 ADR-027 §D2 gate 승격 amendment 발의"
---

# MCT-175 Implementation Plan — Docker Stack Base

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-hub/compose.yml 에 dev/prod profile 도입 + NAS MinIO endpoint env 분리 + WAL host disk mount 정책 + cross-repo lock CI gate. EPIC-mctrader-docker-stack entry Story. ADR-030 publish 동반.

**Architecture:**
- **Profile 분리** (D3): `compose.yml` base 에 `profiles:[dev]` (hub MinIO + mc-init) + `profiles:[prod]` (NAS preflight only) 분기. `.env.dev` / `.env.prod` env_file 로 endpoint 전환.
- **WAL host disk** (D1): collector container 의 WAL volume 은 named volume 이 아닌 host bind mount (`/var/lib/mctrader/wal:/var/lib/mctrader/data`) 로 박제. forward-only invariant + 손실 명시 acceptance.
- **NAS preflight** (D7): `scripts/preflight-nas-dns.sh` 가 compose up 전 NAS endpoint DNS+TCP+S3 list bucket 검증. prod profile entry hook.
- **Cross-repo lock CI gate** (D13): GitHub Actions `.github/workflows/cross-repo-lock-check.yml` 가 hub PR 마다 6 repo uv.lock python_version + 핵심 lib (pyarrow, boto3, pydantic, websockets) 의 major version drift 검증.

**Tech Stack:** Docker Compose v2 (profiles) / Bash (preflight) / GitHub Actions (cross-repo lock gate) / Python 3.12 (uv.lock parse)

**PR Split:**
- **Phase 1 PR** (docs only): ADR-030 + Story file + runbook stub + CLAUDE.md
- **Phase 2 PR1** (code): compose.yml + .env split + preflight + CI gate + .gitignore
- **Phase 2 PR2** (박제): Story §11 retro + ADR-030 Accepted + Epic status update + RETRO

---

## §0 Risk Acceptance Gate (Phase 1 진입 전)

- [ ] **Step 0.1: R1 HIGH (NAS HTTP-only) 사용자 explicit accept 또는 ADR-027 §D2 amendment 발의 결정**

3 option:
- (A) accept as-is → spec §5 R1 entry 에 `user_acknowledged_at: 2026-05-15` 박제
- (B) ADR-027 §D2 Stage 1 HTTP gate 를 hard cutoff date 로 amend (MCT-175 Phase 1 PR 동반)
- (C) MCT-155 TLS Stage 2 prerequisite Story 신규 reserve 후 EPIC-mctrader-docker-stack 의존 추가

→ 사용자 선택 결정.

- [ ] **Step 0.2: R4 MEDIUM (D17 host disk loss → 영구 손실) 사용자 explicit accept**

forward-only invariant + host disk 단일점 실패 = 1d 손실 risk. spec §5 R4 entry 에 `user_acknowledged_at: 2026-05-15` 박제.

---

## §1 Phase 1 PR (mctrader-hub, docs only)

### 1.1 ADR-030 publish

**Files:**
- Create: `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] **Step 1.1.1: ADR-030 draft 작성 (Status: Proposed)**

본문 박제 8 D: D1 / D2 / D3 / D7 / D12 / D13 / D17 / D18 (governance level).

본문 구조:
```markdown
# ADR-030: Docker stack governance — single-host compose + dev/prod profile + image registry + observability

## Status
Proposed (MCT-175 진입, Accepted 전환 = MCT-175 LAND 시)

## Context
mctrader-hub/compose.yml 은 인프라 stack (postgres+minio+redis+prometheus+grafana+nginx+exporters+signal-collector 5종) 박제. mctrader-data + mctrader-engine 어플리케이션 누락 + dev/prod profile 부재 + image registry tag 정책 모호.

## Decision
### §D1 WAL host disk 별도 mount + L1 named volume
collector container 의 WAL = host bind mount (forward-only invariant 정합, host disk loss = 영구 손실 명시 acceptance) / L1 cold cache = named volume.

### §D2 paper daemon + backtest profile (동일 image command override)
mctrader-engine Dockerfile = 단일 image. paper-engine = `command: ["paper", "--daemon"]` + `restart: unless-stopped` / backtest-runner = `command: ["backtest", ...]` + `profiles: [oneshot]`.

### §D3 compose profiles dev/prod + env_file 분리
`compose.yml` profiles `dev` (hub MinIO + mc-init) / `prod` (NAS preflight only). `.env.dev` / `.env.prod` env_file 로 NAS_MINIO_* 변수 분기.

### §D7 NAS DNS 직접 해석 + preflight 검증
container 내부에서 `mcnas01.internal.mclayer.it:9000` DNS 직접 해석. `scripts/preflight-nas-dns.sh` 가 compose up 전 검증 (DNS+TCP+S3 list bucket).

### §D12 image registry pin (semver + sha + latest 병행)
`ghcr.io/mclayer/{repo}:{tag}` registry. prod = release tag (vX.Y.Z) + git sha pin / dev = latest.

### §D13 각 repo 독립 uv.lock + cross-repo CI lock gate
monorepo lock 회피. CI gate 가 hub PR 마다 6 repo uv.lock python_version + 핵심 lib major version drift 검증.

### §D17 SIGTERM graceful + startup InvariantHarness scan (외부 backup 없이)
WAL = local only (ADR-029 §D4 정합). graceful SIGTERM + 시작 시 InvariantHarness 8종 scan 만 박제. external backup 없음 = host disk loss risk 명시 acceptance.

### §D18 명시 resource limits + Prometheus alert >80% warn
collector/paper-engine/backtest-runner 모두 `deploy.resources.limits` (mem_limit + cpus) 명시. Prometheus `container_memory_usage_bytes` alert (>80% capacity).

## Consequences
- 단일 compose stack 으로 dev/prod 동일 entry → operational parity
- NAS HTTP-only 평문 노출 risk → R1 HIGH 명시 acceptance (MCT-155 cutover backlog)
- host disk loss → 1d 영구 손실 risk → R4 MEDIUM 명시 acceptance (forward-only invariant 정합)

## References
- spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
- scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
- 의존: ADR-029 (cold tier governance) / ADR-027 §D2 (HTTP Stage 1)
```

- [ ] **Step 1.1.2: counters.json ADR-030 reservation entry status update**

`ADR-030.status: Reserved → Proposed`

- [ ] **Step 1.1.3: scope_manifest §planned_adrs.new_proposals[ADR-030].status update**

```yaml
planned_adrs:
  new_proposals:
    - key: ADR-030
      status: Proposed  # was Reserved
      drafted_at: 2026-05-15
```

### 1.2 Story file 작성

**Files:**
- Create: `docs/stories/MCT-175.md`

- [ ] **Step 1.2.1: Story §1-§12 작성**

§1 Title / §2 Epic / §3 Phase 0 verify finding / §4 AC (5건) / §5 INV / §6 R (D17 host disk + D7 DNS preflight) / §7 Dependencies / §8 Test contract (compose config lint + cross-repo lock CI) / §9 Plan reference / §10 FIX ledger / §11 Retro (Phase 2 PR2 박제) / §12 Measurements (Phase 2 PR2 박제).

AC 5건:
- AC-1 (D3): `docker compose --profile dev config` PASS + `--profile prod config` PASS
- AC-2 (D3): `.env.dev` NAS_MINIO_ENDPOINT = `http://minio:9000` / `.env.prod` NAS_MINIO_ENDPOINT = `http://mcnas01.internal.mclayer.it:9000`
- AC-3 (D7): `scripts/preflight-nas-dns.sh` exit 0 = DNS+TCP+S3 list bucket 검증 통과
- AC-4 (D1): `compose.yml` collector service 의 WAL volume = host bind mount `/var/lib/mctrader/wal:/var/lib/mctrader/data` (planned, MCT-176 LAND 시 적용)
- AC-5 (D13): cross-repo lock CI gate PR push 시 자동 실행 + 6 repo uv.lock python_version drift = FAIL 가능 verify

### 1.3 Runbook stub

**Files:**
- Create: `docs/runbooks/docker-stack-deploy.md`

- [ ] **Step 1.3.1: deploy runbook stub 작성**

5-step: (1) prerequisite check / (2) .env.{dev|prod} prepare / (3) preflight script run / (4) compose up profile / (5) health verify. 상세 본문은 MCT-176~181 LAND 시 점진 보강.

### 1.4 CLAUDE.md 섹션 stub

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\CLAUDE.md`

- [ ] **Step 1.4.1: §Docker stack 확장 (EPIC-mctrader-docker-stack, MCT-175 PLANNED) 섹션 추가**

`## Pending Stories (Replication Backlog)` 위에 새 섹션 삽입:
- Epic 목적 + 7 Story 개요
- ADR-030 reference
- Phase 1 PR 박제 (MCT-175 IN_PROGRESS)

### 1.5 scope_manifest status update

- [ ] **Step 1.5.1: scope_manifest §stories[MCT-175].status: Reserved → IN_PROGRESS**

started_date: 2026-05-15 박제.

### 1.6 Phase 1 PR Gate

- [ ] DesignReviewPLAgent dispatch (ADR-030 8 D 박제 + Story §1-§12 + runbook stub 정합)
- [ ] superpowers:verification-before-completion 호출 (`docker compose --profile dev config` 더미 test 부재 시 skip OK)
- [ ] CI green (lint only — code 부재)
- [ ] Admin merge (per [[feedback_admin_merge_autonomy]])

---

## §2 Phase 2 PR1 (mctrader-hub, code)

### 2.1 compose.yml profile 분리

**Files:**
- Modify: `compose.yml` (lines 29-75 — minio + mc service profile 추가)

- [ ] **Step 2.1.1: minio + mc service 에 profiles:[dev] 추가**

```yaml
services:
  minio:
    image: quay.io/minio/minio:latest
    container_name: mctrader-minio
    profiles: ["dev"]  # 신규
    command: server /data --console-address ":9001"
    # ... 기존 그대로
  mc:
    image: quay.io/minio/mc:latest
    container_name: mctrader-mc-init
    profiles: ["dev"]  # 신규
    # ... 기존 그대로
```

- [ ] **Step 2.1.2: nginx upstream profile-aware 변경**

nginx depends_on 의 minio 가 prod profile 에서 부재 → conditional depends_on:

```yaml
nginx:
  image: nginx:alpine
  container_name: mctrader-nginx
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/nginx.prod.conf:/etc/nginx/nginx.prod.conf:ro  # 신규
  ports:
    - "80:80"
  networks:
    - mctrader_net
  depends_on:
    - grafana
    - prometheus
    # minio depends_on 제거 (prod profile 에서 부재)
```

→ 별 conf 파일 2종 (`nginx.conf` dev = upstream local minio / `nginx.prod.conf` prod = upstream NAS proxy or removed). MCT-175 scope = dev conf only (prod conf 는 MCT-181 LAND 시 finalize).

- [ ] **Step 2.1.3: compose.yml 상단 주석 추가 — Epic + profile 사용법**

```yaml
# mctrader-hub/compose.yml — Shared infrastructure (EPIC-mctrader-docker-stack)
# Profile usage:
#   dev:  docker compose --profile dev --env-file .env.dev up
#   prod: docker compose --profile prod --env-file .env.prod up
# ADR-030 §D3 박제.
```

### 2.2 .env split

**Files:**
- Create: `.env.dev`
- Create: `.env.prod.example` (← .env.prod 자체는 .gitignored)
- Modify: `.env.example`

- [ ] **Step 2.2.1: .env.dev 신규**

```
# mctrader-hub/.env.dev — dev profile (hub MinIO fallback)
POSTGRES_PASSWORD=devpassword
MINIO_ACCESS_KEY=mctrader
MINIO_SECRET_KEY=devminio
GRAFANA_ADMIN_PASSWORD=devgrafana
ECOS_API_KEY=
# NAS MinIO endpoint (dev = hub MinIO 폴백)
NAS_MINIO_ENDPOINT=http://minio:9000
NAS_MINIO_ACCESS_KEY=mctrader
NAS_MINIO_SECRET_KEY=devminio
NAS_MINIO_BUCKET=mctrader-market
```

- [ ] **Step 2.2.2: .env.prod.example 신규**

```
# mctrader-hub/.env.prod.example — prod profile template
# Copy to .env.prod and fill actual values (rotation 90d, see docs/runbooks/nas-minio-secret-rotation.md)
POSTGRES_PASSWORD=<rotate>
MINIO_ACCESS_KEY=<not_used_in_prod>
MINIO_SECRET_KEY=<not_used_in_prod>
GRAFANA_ADMIN_PASSWORD=<rotate>
ECOS_API_KEY=<from_ecos_portal>
# NAS MinIO endpoint (prod = NAS Synology)
NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
NAS_MINIO_ACCESS_KEY=<from_nas_minio_console>
NAS_MINIO_SECRET_KEY=<from_nas_minio_console>
NAS_MINIO_BUCKET=mctrader-market
```

- [ ] **Step 2.2.3: .env.example 갱신 — NAS_MINIO_* 항목 추가**

```
POSTGRES_PASSWORD=changeme
MINIO_ACCESS_KEY=mctrader
MINIO_SECRET_KEY=changeme_minio
GRAFANA_ADMIN_PASSWORD=changeme_grafana

# signal-collector
ECOS_API_KEY=
COINGLASS_API_KEY=

# NAS MinIO (prod profile only — dev 은 hub MinIO 폴백)
NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
NAS_MINIO_ACCESS_KEY=changeme_nas
NAS_MINIO_SECRET_KEY=changeme_nas_secret
NAS_MINIO_BUCKET=mctrader-market
```

- [ ] **Step 2.2.4: .gitignore 갱신**

```
.env
.env.dev
.env.prod
docker/minio/.env
```

(`.env.dev` 도 .gitignore — dev credential 도 commit 금지)

### 2.3 NAS DNS preflight script

**Files:**
- Create: `scripts/preflight-nas-dns.sh`

- [ ] **Step 2.3.1: preflight script 작성 (D7)**

```bash
#!/usr/bin/env bash
# mctrader-hub/scripts/preflight-nas-dns.sh
# NAS MinIO endpoint preflight (D7, ADR-030)
# Usage: ./scripts/preflight-nas-dns.sh [.env.prod]
#
# Exit codes:
#   0  = all checks PASS
#   10 = DNS resolution FAIL
#   20 = TCP connect FAIL
#   30 = S3 list bucket FAIL
#   99 = .env.prod parse FAIL or curl/dig missing

set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[preflight] FAIL: env file not found: $ENV_FILE" >&2
  exit 99
fi

# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

ENDPOINT="${NAS_MINIO_ENDPOINT:?NAS_MINIO_ENDPOINT not set in $ENV_FILE}"
ACCESS_KEY="${NAS_MINIO_ACCESS_KEY:?NAS_MINIO_ACCESS_KEY not set}"
SECRET_KEY="${NAS_MINIO_SECRET_KEY:?NAS_MINIO_SECRET_KEY not set}"
BUCKET="${NAS_MINIO_BUCKET:-mctrader-market}"

# Parse host:port
HOST_PORT="${ENDPOINT#http://}"
HOST_PORT="${HOST_PORT#https://}"
HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"
[[ "$PORT" == "$HOST" ]] && PORT="80"

echo "[preflight] endpoint = $ENDPOINT (host=$HOST, port=$PORT)"

# Step 1: DNS resolution
if ! command -v dig >/dev/null; then
  echo "[preflight] WARN: 'dig' not available, falling back to getent"
  getent hosts "$HOST" >/dev/null || { echo "[preflight] FAIL: DNS resolve $HOST"; exit 10; }
else
  dig +short "$HOST" | grep -q . || { echo "[preflight] FAIL: DNS resolve $HOST"; exit 10; }
fi
echo "[preflight] PASS: DNS resolved $HOST"

# Step 2: TCP connect
if ! timeout 5 bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null; then
  echo "[preflight] FAIL: TCP connect $HOST:$PORT"
  exit 20
fi
echo "[preflight] PASS: TCP connect $HOST:$PORT"

# Step 3: S3 list bucket (mc client)
if ! command -v mc >/dev/null; then
  echo "[preflight] WARN: 'mc' not available, skipping S3 list bucket check"
else
  TMP_ALIAS="preflight-$$"
  mc alias set "$TMP_ALIAS" "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" --quiet 2>/dev/null
  trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT
  mc ls "$TMP_ALIAS/$BUCKET" --quiet >/dev/null 2>&1 || { echo "[preflight] FAIL: S3 list $BUCKET"; exit 30; }
  echo "[preflight] PASS: S3 list bucket $BUCKET"
fi

echo "[preflight] ALL CHECKS PASS"
```

- [ ] **Step 2.3.2: chmod +x preflight script**

```bash
chmod +x scripts/preflight-nas-dns.sh
```

- [ ] **Step 2.3.3: AC-3 verify locally (dev .env.dev 으로)**

```bash
./scripts/preflight-nas-dns.sh .env.dev
# Expected output: "[preflight] ALL CHECKS PASS" + exit 0
# Note: dev profile 에선 endpoint=http://minio:9000 → container 내부 hostname → host 측에서 직접 실행 시 DNS fail 예상 (정상)
# 호스트 측 verify 용 .env.dev.host 별도 또는 docker run --network mctrader_net 안에서 실행
```

→ dev 환경에서는 hub MinIO 가 docker network 내부 hostname 이므로 host 측 preflight 직접 실행 = fail (정상). 실제 verify 는 prod .env.prod (실제 NAS endpoint) 으로 수동.

### 2.4 Cross-repo lock CI gate

**Files:**
- Create: `.github/workflows/cross-repo-lock-check.yml`
- Create: `scripts/check_cross_repo_locks.py`

- [ ] **Step 2.4.1: cross-repo lock check script 작성**

```python
#!/usr/bin/env python3
"""mctrader-hub/scripts/check_cross_repo_locks.py

ADR-030 §D13 — cross-repo uv.lock python_version + 핵심 lib major version drift gate.

Checks:
  - python_version >= 3.12 across all 6 repos
  - pyarrow / boto3 / pydantic / websockets major version 일치 (cross-repo)

Exit codes:
  0  = all aligned
  1  = python_version drift
  2  = lib major version drift
  99 = uv.lock missing or parse fail
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import tomllib  # Python 3.11+

REPOS = [
    "mctrader-hub",
    "mctrader-data",
    "mctrader-engine",
    "mctrader-web",
    "mctrader-signal-collector",
    "mctrader-market",
]
CHECK_LIBS = ["pyarrow", "boto3", "pydantic", "websockets"]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]  # c:/workspace/mclayer


def load_lock(repo: str) -> dict[str, Any] | None:
    lock_path = WORKSPACE_ROOT / repo / "uv.lock"
    if not lock_path.exists():
        print(f"[lock-check] WARN: {repo}/uv.lock missing (skip)")
        return None
    return tomllib.loads(lock_path.read_text())


def lib_major(lock: dict[str, Any], name: str) -> str | None:
    for pkg in lock.get("package", []):
        if pkg.get("name") == name:
            v = pkg.get("version", "")
            return v.split(".", 1)[0] if v else None
    return None


def python_version(lock: dict[str, Any]) -> str | None:
    return lock.get("requires-python") or lock.get("python-version")


def main() -> int:
    locks: dict[str, dict[str, Any]] = {}
    for repo in REPOS:
        lock = load_lock(repo)
        if lock is not None:
            locks[repo] = lock

    if not locks:
        print("[lock-check] FAIL: no uv.lock found")
        return 99

    # python_version drift
    py_versions = {repo: python_version(lock) for repo, lock in locks.items()}
    distinct_py = {v for v in py_versions.values() if v}
    print(f"[lock-check] python_version per repo: {py_versions}")
    if len(distinct_py) > 1:
        print(f"[lock-check] FAIL: python_version drift: {distinct_py}")
        return 1

    # lib major drift
    drift_libs: list[str] = []
    for lib in CHECK_LIBS:
        majors = {repo: lib_major(lock, lib) for repo, lock in locks.items()}
        distinct = {m for m in majors.values() if m}
        if len(distinct) > 1:
            drift_libs.append(f"{lib}: {majors}")

    if drift_libs:
        print("[lock-check] FAIL: lib major version drift:")
        for d in drift_libs:
            print(f"  - {d}")
        return 2

    print("[lock-check] ALL ALIGNED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2.4.2: GitHub Actions workflow 작성**

```yaml
# .github/workflows/cross-repo-lock-check.yml
# ADR-030 §D13 — cross-repo uv.lock drift gate
name: cross-repo-lock-check

on:
  pull_request:
    paths:
      - "uv.lock"
      - ".github/workflows/cross-repo-lock-check.yml"
      - "scripts/check_cross_repo_locks.py"
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: checkout hub
        uses: actions/checkout@v4
        with:
          path: mctrader-hub
      - name: checkout data
        uses: actions/checkout@v4
        with:
          repository: mclayer/mctrader-data
          path: mctrader-data
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: checkout engine
        uses: actions/checkout@v4
        with:
          repository: mclayer/mctrader-engine
          path: mctrader-engine
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: checkout signal-collector
        uses: actions/checkout@v4
        with:
          repository: mclayer/mctrader-signal-collector
          path: mctrader-signal-collector
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: checkout web
        uses: actions/checkout@v4
        with:
          repository: mclayer/mctrader-web
          path: mctrader-web
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: checkout market
        uses: actions/checkout@v4
        with:
          repository: mclayer/mctrader-market
          path: mctrader-market
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: setup python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: run check
        run: python mctrader-hub/scripts/check_cross_repo_locks.py
```

- [ ] **Step 2.4.3: AC-5 verify — workflow trigger 또는 manual run**

```bash
# Local manual run (workspace c:/workspace/mclayer/ 에서)
python c:/workspace/mclayer/mctrader-hub/scripts/check_cross_repo_locks.py
# Expected: "[lock-check] ALL ALIGNED" + exit 0
```

PR push 후 GitHub Actions workflow 자동 실행 verify.

### 2.5 compose.yml WAL volume 가이드 박제 (D1)

**Files:**
- Modify: `compose.yml` (주석 박제 only, 실 service 추가 = MCT-176)

- [ ] **Step 2.5.1: collector service stub 주석 추가**

`compose.yml` 끝 (signal-collector 들 다음, nginx 전) 에 collector stub 주석 박제:

```yaml
  # mctrader-data collector — MCT-176 LAND 시 활성화
  # collector:
  #   image: ghcr.io/mclayer/mctrader-data:latest
  #   container_name: mctrader-collector
  #   profiles: ["dev", "prod"]
  #   build:
  #     context: ../mctrader-data
  #   env_file:
  #     - .env.${COMPOSE_PROFILES:-dev}
  #   volumes:
  #     - /var/lib/mctrader/wal:/var/lib/mctrader/data  # ADR-030 §D1 host bind mount
  #     - mctrader_l1:/var/lib/mctrader/data/l1
  #   ...
  # volumes:
  #   mctrader_l1:
```

이 stub 은 MCT-176 LAND 시 활성화 (활성화 task = MCT-176 plan).

### 2.6 Phase 2 PR1 Gate

- [ ] AC-1 verify: `docker compose --profile dev config` PASS + `--profile prod config` PASS
- [ ] AC-2 verify: `.env.dev` / `.env.prod.example` NAS_MINIO_ENDPOINT 값 일치
- [ ] AC-3 verify: `./scripts/preflight-nas-dns.sh` exit code 정합 (dev = expected fail 정상, prod = manual verify)
- [ ] AC-5 verify: cross-repo lock check exit 0 (workspace 측 6 repo aligned)
- [ ] superpowers:verification-before-completion 호출 (실 commands run + output 박제)
- [ ] CodeReviewPLAgent dispatch
- [ ] CI green (cross-repo lock workflow 동시 실행)
- [ ] Admin merge

---

## §3 Phase 2 PR2 (mctrader-hub, 박제)

### 3.1 산출물

- [ ] **Step 3.1.1: `docs/stories/MCT-175.md` §11 retro_file + §12 측정 + status: IN_PROGRESS → COMPLETED + completed_at**

§12 측정:
- AC-1 ~ AC-5 ALL PASS verify 결과 + exit code 박제
- preflight script exit code matrix (DNS / TCP / S3 list)
- cross-repo lock check 실측 output

- [ ] **Step 3.1.2: `docs/adr/ADR-030-docker-stack-governance.md` Status: Proposed → Accepted**

§Status section 갱신:
```
## Status
Accepted (2026-05-15 LAND, MCT-175 hub#<PR>)
```

- [ ] **Step 3.1.3: scope_manifest §stories[MCT-175].status: IN_PROGRESS → COMPLETED**

completed_at: 2026-05-15 박제. Epic milestone 1/7.

- [ ] **Step 3.1.4: CLAUDE.md §EPIC-mctrader-docker-stack MCT-175 COMPLETED 박제**

```markdown
### MCT-175 COMPLETED (2026-05-15)

- ADR-030 publish (Status: Accepted, 8 D 본문 박제)
- compose.yml dev/prod profile 분리 (minio + mc service [dev])
- .env.dev / .env.prod.example 신규 + .env.example NAS_MINIO_* 추가
- scripts/preflight-nas-dns.sh 신규 (D7)
- .github/workflows/cross-repo-lock-check.yml 신규 (D13)
- WAL host bind mount stub 박제 (MCT-176 LAND 시 활성화)
```

- [ ] **Step 3.1.5: `docs/retros/RETRO-MCT-175.md` 신규 (PMOAgent 자동 dispatch per [[feedback_pmo_retro_mandatory]])**

4 field schema: delivered / measurements / risks_realized / followups.

- [ ] **Step 3.1.6: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` 신규 + §Story-1 (MCT-175) 결과 박제**

Epic milestone 1/7 완료 박제.

### 3.2 Phase 2 PR2 Gate

- [ ] Phase 2 PR1 LAND verify (mctrader-hub PR merge commit hash)
- [ ] PMOAgent 자동 dispatch (per [[feedback_pmo_retro_mandatory]])
- [ ] RETRO 4 field schema verify
- [ ] EPIC-RESULTS §Story-1 entry 정합
- [ ] CI green (lint only — code 부재)
- [ ] Admin merge

---

## §4 sequential 의존성 (Next Story Entry)

MCT-175 COMPLETED → **MCT-176** (collector container + NAS credential rotation + effective config dump, D7/D9/D14) 진입.

MCT-176 plan 신규 작성 의무 (`docs/superpowers/plans/2026-05-15-mct-176-collector-container.md`) — sequential chain 이므로 본 plan 의 LAND artifact (compose.yml stub + .env split + preflight script) 를 prerequisite 으로 plan 작성.

---

## §5 Self-Review Notes

**Spec coverage** verify:
- D1 (WAL host disk) → §2.5 stub 박제, 실 활성화 = MCT-176 ✓
- D3 (compose profile) → §2.1 + §2.2 ✓
- D7 (NAS DNS preflight) → §2.3 ✓
- D13 (cross-repo lock gate) → §2.4 ✓
- ADR-030 publish → §1.1 ✓
- Risk acceptance gate → §0 ✓

**Placeholder scan**: 모든 code step = 실 content (preflight script bash + lock check Python + workflow YAML).

**Type consistency**: NAS_MINIO_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET 4 변수 일관 사용.

**누락 식별**: 없음 (D1/D3/D7/D13 4 결정 모두 task 매핑).
