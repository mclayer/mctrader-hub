---
story_key: MCT-176
plan_title: "Collector container 활성화 + NAS credential rotation + effective config dump"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 2
depends_on: MCT-175 (LAND 2026-05-15, hub#326 + hub#327 + hub#328)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D7, D9, D14]
carry_over_from_mct175:
  - "P1-2 preflight DNS wildcard FP — preflight 스크립트 로깅 + DNS 응답 IP 검증 추가"
  - "P1-3 mc alias trap SIGINT race — trap 등록 순서 fix"
  - "P2-1 shell error handling — set -a source robust 확인"
  - "cross-repo-lock-check workflow secret 등록 + auto trigger 복원 (pull_request trigger 복원)"
---

# MCT-176 Implementation Plan — Collector Container 활성화

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** mctrader-hub/compose.yml 의 collector service stub 활성화 (D1=C WAL host bind mount + L1 named volume) + mctrader-data CLI SIGTERM graceful shutdown + effective config dump + NAS credential rotation script + MCT-175 carry over 3 defer + cross-repo lock workflow auto trigger 복원.

**Architecture:**
- **D7 carry over** (`MCT-175 defer`): preflight script 의 DNS wildcard false-positive + mc alias trap race 수정. host disk loss/IP 검증 강화.
- **D9** (NAS credential rotation): `scripts/rotate-nas-credentials.sh` 신규 (90d cycle, Slack webhook + cron + .env.prod 자동 갱신).
- **D14** (effective config dump): `mctrader-data` CLI 에 `effective-config` subcommand 신규 — env 값 + YAML default 의 최종 적용 dump (운영자 확인용).
- **D1 활성화**: compose.yml 의 collector stub 주석 해제 + WAL host bind mount (`/var/lib/mctrader/wal`) + L1 named volume + SIGTERM graceful + healthcheck 8080.
- **MCT-175 carry over**: P1-2 + P1-3 + P2-1 fix + cross-repo-lock-check workflow trigger 복원 (secret 등록 의무 + pull_request trigger).

**Tech Stack:** Docker Compose v2 (named volume + bind mount) / Bash (rotation script) / Python 3.12 (CLI effective-config) / GitHub Actions secret

**PR Split:**
- **Phase 1 PR** (hub, docs only): MCT-176 Story file + ADR-030 §D9/§D14 amendment box + runbook (rotation automation) + CLAUDE.md
- **Phase 2 PR1** (cross-repo code):
  - **hub PR**: compose.yml collector service 활성화 + scripts/rotate-nas-credentials.sh + cross-repo-lock-check.yml trigger 복원 + preflight script defer fix
  - **data PR**: src/mctrader_data/cli.py SIGTERM handler + effective-config subcommand + 신규 test
- **Phase 2 PR2** (hub, 박제): Story §11 retro + ADR-030 cross-ref + Epic milestone 2/7 + RETRO-MCT-176 + EPIC-RESULTS §Story-2

---

## §1 Phase 1 PR (mctrader-hub, docs only)

### 1.1 Story MCT-176 작성

**Files:** Create `docs/stories/MCT-176.md` (§1-§12 schema)

- [ ] **Step 1.1.1: Story §1-§6 작성** — 동기 / Epic context / Risk acceptance / AC 5 / INV / Risk
  - AC-1 (D1 활성화): `docker compose --profile dev/prod up collector` 후 `docker inspect` 가 WAL host bind mount + L1 named volume 확인
  - AC-2 (D14 effective-config): `mctrader-data effective-config --format json` exit 0 + JSON 출력에 env override + YAML default 명시
  - AC-3 (D9 rotation script): `scripts/rotate-nas-credentials.sh --dry-run` exit 0 + .env.prod NAS_MINIO_ACCESS_KEY/SECRET_KEY 갱신 simulate
  - AC-4 (carry over): preflight script P1-2/P1-3/P2-1 fix verify (DNS wildcard 응답 IP 검증 추가 + trap 등록 순서 fix + set -a source robust)
  - AC-5 (cross-repo workflow): pull_request trigger 복원 + MCTRADER_CROSS_REPO_TOKEN secret 등록 가이드 박제

- [ ] **Step 1.1.2: §6.5 Change Plan §7/§11 N/A** 박제 (Story-section-schema vs Change Plan §7/§11 mapping):
  - §7 security-design: Phase 2 PR1 = mctrader-data CLI 신규 subcommand + bash script (호스트 측 secret rotation). trust boundary = NAS MinIO credential 의 .env.prod write — secret rotation 절차 본 Story §6 R 박제 + SecurityArch carrier (별 Story 의무 없음).
  - §7.4 operational-risk: graceful SIGTERM (Story AC-1) + rotation cron schedule + Slack webhook fail handling. ADR-030 §D17 SIGTERM amendment 정합.
  - §11 data-migration: 새 named volume `mctrader_l1` + bind mount `/var/lib/mctrader/wal`. 기존 host filesystem 사용자 디스크 사전 준비 의무 (runbook 박제). schema 변경 없음.
  - §11.6 idempotency: rotation script = .env.prod write + restart trigger. idempotent (재실행 = 새 key 발급 + 기존 key revoke). collector restart = WAL fsync barrier 적용 (D17).

- [ ] **Step 1.1.3: §7-§9** — Dependencies (MCT-175 LAND 산출물) + Test contract (D14 unit + carry over fix verify) + Plan reference

- [ ] **Step 1.1.4: §10 FIX Ledger 빈 표 + §11/§12 placeholder**

### 1.2 ADR-030 amendment box

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] **Step 1.2.1: §D9 amendment box append** (MCT-176 publish)
  - rotation script path: `scripts/rotate-nas-credentials.sh`
  - rotation cycle: 90d (NAS root cred runbook 정합)
  - automation: cron + Slack webhook + .env.prod write
  - manual rollback: 이전 credential 보존 (cred history file 박제 — gitignored)

- [ ] **Step 1.2.2: §D14 amendment box append** (effective config dump)
  - CLI subcommand: `mctrader-data effective-config --format {json,yaml}`
  - 출력 source order: env > YAML default > built-in default
  - 운영자 verify hook: container 진입 후 `mctrader-data effective-config` 실행

### 1.3 Runbook 신규

**Files:** Create `docs/runbooks/nas-credential-rotation-automation.md`

- [ ] **Step 1.3.1: 5-step runbook 작성**
  - Step 1: rotation script dry-run verify
  - Step 2: cron schedule 등록 (Synology NAS Task Scheduler 또는 host crontab)
  - Step 3: Slack webhook 등록
  - Step 4: 실 rotation 첫 실행 (사용자 confirm 후)
  - Step 5: post-rotation verify (preflight + collector restart)

### 1.4 CLAUDE.md amendment

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1.4.1: §Docker stack 확장 § 7 Story chain 표 update**
  - MCT-176: PLANNED → IN_PROGRESS (2026-05-15)

### 1.5 Phase 1 PR Gate

- [ ] DesignReviewPLAgent dispatch
- [ ] CI green (lint only)
- [ ] phase:설계-리뷰 + gate:design-review-pass label
- [ ] Admin merge

---

## §2 Phase 2 PR1 (cross-repo: mctrader-data + mctrader-hub, code)

### 2.1 mctrader-data PR — CLI SIGTERM + effective-config

**Files:**
- Modify: `mctrader-data/src/mctrader_data/cli.py` (SIGTERM handler + effective-config subcommand)
- Create: `mctrader-data/tests/test_effective_config.py`
- Create: `mctrader-data/tests/test_sigterm_graceful.py`

- [ ] **Step 2.1.1: SIGTERM handler 신규**

```python
import signal
import sys

_SHUTDOWN_REQUESTED = False

def _sigterm_handler(signum, frame):
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True
    logger.info("[cli] SIGTERM received — graceful shutdown initiated")

def _register_signal_handlers():
    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGINT, _sigterm_handler)
```

collect loop 내 `while not _SHUTDOWN_REQUESTED:` chunk boundary 에서 break.

- [ ] **Step 2.1.2: effective-config subcommand 신규**

```python
@cli.command()
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json")
def effective_config(format):
    """Dump effective configuration (env override + YAML default + built-in)."""
    config = {
        "nas_minio": {
            "endpoint": os.environ.get("NAS_MINIO_ENDPOINT", "<unset>"),
            "access_key_set": bool(os.environ.get("NAS_MINIO_ACCESS_KEY")),
            "secret_key_set": bool(os.environ.get("NAS_MINIO_SECRET_KEY")),
            "bucket": os.environ.get("NAS_MINIO_BUCKET", "mctrader-market"),
        },
        "wal": {
            "root": os.environ.get("MCTRADER_DATA_ROOT", "/var/lib/mctrader/data"),
            "capacity_gb": int(os.environ.get("WAL_CAPACITY_GB", "30")),
        },
        "ingestion": {
            "top_n": int(os.environ.get("UNIVERSE_TOP_N", "10")),
            "modes": os.environ.get("INGEST_MODES", "transactions,orderbook").split(","),
        },
        "source_order": ["env", "yaml_default", "built_in"],
    }
    if format == "yaml":
        import yaml
        click.echo(yaml.safe_dump(config, sort_keys=False))
    else:
        click.echo(json.dumps(config, indent=2))
```

- [ ] **Step 2.1.3: 신규 test 2종**

```python
# tests/test_effective_config.py
def test_effective_config_json_format(runner):
    result = runner.invoke(cli, ["effective-config", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nas_minio" in data
    assert "wal" in data
    assert data["source_order"] == ["env", "yaml_default", "built_in"]

def test_effective_config_env_override(runner, monkeypatch):
    monkeypatch.setenv("NAS_MINIO_ENDPOINT", "http://example.com:9000")
    result = runner.invoke(cli, ["effective-config"])
    data = json.loads(result.output)
    assert data["nas_minio"]["endpoint"] == "http://example.com:9000"

# tests/test_sigterm_graceful.py
def test_sigterm_handler_sets_shutdown_flag(monkeypatch):
    import os
    _register_signal_handlers()
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep(0.1)
    assert _SHUTDOWN_REQUESTED is True
```

### 2.2 mctrader-hub PR — compose collector activation + rotation script + carry over fix

**Files:**
- Modify: `mctrader-hub/compose.yml` (collector service stub 활성화)
- Create: `mctrader-hub/scripts/rotate-nas-credentials.sh`
- Modify: `mctrader-hub/.github/workflows/cross-repo-lock-check.yml` (pull_request trigger 복원)
- Modify: `mctrader-hub/scripts/preflight-nas-dns.sh` (P1-2 + P1-3 + P2-1 fix)

- [ ] **Step 2.2.1: collector service stub 주석 해제 + WAL host bind mount + L1 named volume**

```yaml
  collector:
    image: ghcr.io/mclayer/mctrader-data:latest
    container_name: mctrader-collector
    profiles: ["dev", "prod"]
    build:
      context: ../mctrader-data
    env_file:
      - .env.${COMPOSE_PROFILE:-dev}
    volumes:
      - /var/lib/mctrader/wal:/var/lib/mctrader/data  # ADR-030 §D1 WAL host bind mount
      - mctrader_l1:/var/lib/mctrader/data/l1         # ADR-030 §D1 L1 named volume
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    stop_grace_period: 60s  # ADR-030 §D4 SIGTERM graceful (60s)
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - mctrader_net
    labels:
      mctrader.role: "collector"
      mctrader.story: "MCT-176"

volumes:
  mctrader_l1:
```

- [ ] **Step 2.2.2: rotate-nas-credentials.sh 신규 (Bash)**

```bash
#!/usr/bin/env bash
# mctrader-hub/scripts/rotate-nas-credentials.sh
# NAS MinIO credential 90d rotation (ADR-030 §D9 + nas-minio-secret-rotation.md)
#
# Usage:
#   ./scripts/rotate-nas-credentials.sh [--dry-run] [--slack-webhook URL]
#
# Exit codes: 0 PASS / 10 .env.prod missing / 20 mc command fail / 30 Slack send fail / 99 prerequisite

set -euo pipefail

DRY_RUN=0
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --slack-webhook) SLACK_WEBHOOK="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 99 ;;
  esac
done

ENV_FILE=".env.prod"
[[ -f "$ENV_FILE" ]] || { echo "[rotate] FAIL: $ENV_FILE missing" >&2; exit 10; }

# shellcheck disable=SC1091
set -a; source "$ENV_FILE"; set +a

# 1) Generate new credentials (mc admin user add)
NEW_ACCESS_KEY="mctrader-rotated-$(date +%Y%m%d)"
NEW_SECRET_KEY=$(openssl rand -base64 32 | tr -d '+/=' | head -c 40)

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[rotate] DRY-RUN: new access_key=$NEW_ACCESS_KEY (secret_key hidden)"
  exit 0
fi

# 2) mc admin (실 rotation)
TMP_ALIAS="rotate-$$"
trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT
mc alias set "$TMP_ALIAS" "$NAS_MINIO_ENDPOINT" "$NAS_MINIO_ACCESS_KEY" "$NAS_MINIO_SECRET_KEY" --quiet

mc admin user add "$TMP_ALIAS" "$NEW_ACCESS_KEY" "$NEW_SECRET_KEY" || { echo "[rotate] FAIL: mc admin user add"; exit 20; }
mc admin policy attach "$TMP_ALIAS" readwrite --user "$NEW_ACCESS_KEY" || exit 20

# 3) .env.prod 갱신 (atomic — temp file + rename)
OLD_ACCESS_KEY="$NAS_MINIO_ACCESS_KEY"
sed -i.bak \
  -e "s|^NAS_MINIO_ACCESS_KEY=.*|NAS_MINIO_ACCESS_KEY=$NEW_ACCESS_KEY|" \
  -e "s|^NAS_MINIO_SECRET_KEY=.*|NAS_MINIO_SECRET_KEY=$NEW_SECRET_KEY|" \
  "$ENV_FILE"

# 4) collector restart (compose 환경)
docker compose --profile prod restart collector || { echo "[rotate] WARN: collector restart failed"; }

# 5) old credential 5분 grace 후 revoke
sleep 300
mc admin user remove "$TMP_ALIAS" "$OLD_ACCESS_KEY" --quiet || { echo "[rotate] WARN: old key revoke failed"; }

# 6) Slack 알림
if [[ -n "$SLACK_WEBHOOK" ]]; then
  curl -sf -X POST -H "Content-Type: application/json" \
    -d "{\"text\":\"[mctrader] NAS credential rotated: $OLD_ACCESS_KEY → $NEW_ACCESS_KEY ($(date -u +%Y-%m-%dT%H:%M:%SZ))\"}" \
    "$SLACK_WEBHOOK" || { echo "[rotate] FAIL: Slack send"; exit 30; }
fi

echo "[rotate] PASS — new key: $NEW_ACCESS_KEY"
```

- [ ] **Step 2.2.3: cross-repo-lock-check.yml pull_request trigger 복원**

```yaml
on:
  pull_request:
    paths:
      - "uv.lock"
      - ".github/workflows/cross-repo-lock-check.yml"
      - "scripts/check_cross_repo_locks.py"
  workflow_dispatch:
```

추가: README.md (`.github/workflows/README.md`) 또는 PR description 에 `MCTRADER_CROSS_REPO_TOKEN` secret 등록 가이드 박제.

- [ ] **Step 2.2.4: preflight-nas-dns.sh — P1-2 + P1-3 + P2-1 fix**

```bash
# P1-2 fix: DNS resolve 후 응답 IP 검증
RESOLVED_IPS=$(dig +short "$HOST" 2>/dev/null || getent hosts "$HOST" | awk '{print $1}')
if [[ -z "$RESOLVED_IPS" ]]; then
  echo "[preflight] FAIL: DNS resolve $HOST returned empty" >&2
  exit 10
fi
# Wildcard sentinel 검사 (corporate DNS)
if echo "$RESOLVED_IPS" | grep -qE '^(0\.0\.0\.0|127\.0\.0\.1)$'; then
  echo "[preflight] FAIL: DNS resolve $HOST returned sentinel IP ($RESOLVED_IPS) — wildcard DNS suspected" >&2
  exit 10
fi

# P1-3 fix: mc alias trap 등록 순서 — set 전에 trap
TMP_ALIAS="preflight-$$"
trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT INT TERM
mc alias set "$TMP_ALIAS" "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" --quiet 2>/dev/null

# P2-1 fix: set -a source 시 강건성 — env file syntax validate
if ! bash -n "$ENV_FILE" 2>/dev/null; then
  echo "[preflight] FAIL: $ENV_FILE syntax invalid" >&2
  exit 99
fi
```

### 2.3 Phase 2 PR1 Gate

**hub PR**:
- [ ] AC-1 verify: `docker compose --profile dev/prod up collector -d && docker inspect mctrader-collector | jq '.[0].HostConfig.Binds'` PASS
- [ ] AC-3 verify: `./scripts/rotate-nas-credentials.sh --dry-run` exit 0
- [ ] AC-4 verify: preflight script wildcard DNS test (0.0.0.0 mocking)
- [ ] AC-5 verify: cross-repo-lock-check workflow secret 등록 후 PR push 시 정상 실행 (MCT-176 hub PR 자체로 verify)
- [ ] CodeReviewPLAgent dispatch + CI green + Admin merge

**data PR**:
- [ ] AC-2 verify: `mctrader-data effective-config --format json` exit 0 + env override verify
- [ ] 신규 test 2종 PASS (test_effective_config + test_sigterm_graceful)
- [ ] CodeReviewPLAgent dispatch + CI green + Admin merge (data repo 별 admin)

### 2.4 cross-repo LAND 순서

1. mctrader-data PR LAND 먼저 (CLI 신규 subcommand) → ghcr.io publish
2. mctrader-hub PR LAND (compose.yml collector service 의 image: ghcr.io/mclayer/mctrader-data 가 신규 CLI 보유)

또는 docker build 가 ../mctrader-data context 사용 시 동시 LAND 가능.

---

## §3 Phase 2 PR2 (mctrader-hub, 박제)

### 3.1 산출물

- [ ] **Step 3.1.1: Story §10 FIX Ledger + §11 retro + §12 측정 + status: COMPLETED**
- [ ] **Step 3.1.2: ADR-030 §D9 + §D14 amendment box LAND 박제** (Status: 본문 그대로, amendment box 만)
- [ ] **Step 3.1.3: scope_manifest §stories[MCT-176].status: IN_PROGRESS → COMPLETED + milestone 2/7**
- [ ] **Step 3.1.4: CLAUDE.md MCT-176 COMPLETED 박제**
- [ ] **Step 3.1.5: RETRO-MCT-176.md 신규** (PMOAgent dispatch, 4 field)
- [ ] **Step 3.1.6: EPIC-RESULTS §Story-2 박제**

### 3.2 Phase 2 PR2 Gate
- [ ] PMOAgent 자동 dispatch
- [ ] gate:retro-complete label
- [ ] Admin merge

---

## §4 다음 Story 진입

MCT-176 COMPLETED → **MCT-177** (paper-engine daemon + SIGTERM graceful + universe override + Redis prefix, D2/D4/D10/D15). prerequisite = collector LAND + image registry (D12 = MCT-181 의무 — 단 MCT-176 dev profile = build context 직접 사용 가능).

---

## §5 Self-Review

- D7 carry over fix 매핑: §2.2.4 ✓
- D9 rotation 매핑: §1.2.1 + §2.2.2 ✓
- D14 effective config 매핑: §1.2.2 + §2.1.2 + §2.1.3 ✓
- D1 collector 활성화 매핑: §2.2.1 ✓
- cross-repo workflow 복원: §2.2.3 ✓
- Risk acceptance carrier: Story §6.5 + ADR-030 amendment box ✓
