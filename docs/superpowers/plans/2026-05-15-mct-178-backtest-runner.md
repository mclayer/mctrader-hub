---
story_key: MCT-178
plan_title: "backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis migration"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 4
depends_on: MCT-177 (LAND 2026-05-15, hub#333+#334+#335 + data#65 + engine#54)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D2_backtest, D4_oneshot, D10, D16]
carry_over_from_mct177:
  - "signal-collector 5종 Redis prefix code migration (unprefixed → signal:* + 1주일 dual write + Prometheus Gauge + LAND+7d cleanup)"
---

# MCT-178 Implementation Plan — backtest-runner profile

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** compose.yml backtest-runner service (D2 oneshot profile) + D4 oneshot completion (exit 0 후 컨테이너 종료) + D10 universe override + D16 compose config CI lint + signal-collector 5종 Redis prefix code migration (MCT-177 carry over).

**Architecture:**
- **D2 backtest-runner**: compose.yml `backtest-runner` service (image: ghcr.io/mclayer/mctrader-engine, command: `backtest ...`, profiles: [oneshot], restart: "no"). paper-engine 와 동일 image, command 만 분기.
- **D4 oneshot completion**: backtest 1회 실행 후 exit 0 → 컨테이너 종료. healthcheck 없음 (one-shot). SIGTERM = 진행 중 backtest graceful abort.
- **D10 universe override**: `docker compose run --rm backtest-runner backtest --universe-id <id>` case-specific override.
- **D16 compose config CI lint**: `.github/workflows/compose-validate.yml` 신규 — PR 마다 `docker compose --profile dev/prod/oneshot config` lint + `docker compose --profile dev up -d --wait` health gate (3분 budget).
- **signal-collector Redis migration (carry over)**: signal-collector 5종 (fear_greed/ecos/kimchi/announcement/coinglass) Redis key 를 unprefixed → `signal:*` rename. 1주일 dual write (legacy + prefixed 동시 write) + Prometheus `redis_key_migration_dual_write_active` Gauge. LAND+7d legacy cleanup 별 PR.

**Tech Stack:** Docker Compose v2 (profiles oneshot) / GitHub Actions (compose validate) / Python 3.12 (signal-collector Redis client) / Redis 7

**PR Split:**
- **Phase 1 PR** (hub, docs): Story + ADR-030 §D2 backtest + §D16 amendment + CLAUDE.md
- **Phase 2 PR1** (cross-repo: hub + signal-collector):
  - **hub PR**: compose.yml backtest-runner service + .github/workflows/compose-validate.yml
  - **signal-collector PR**: 5종 worker Redis key prefix migration (dual write + Prometheus Gauge)
- **Phase 2 PR2** (hub, 박제): Story §11 retro + Epic milestone 4/7 + RETRO + EPIC-RESULTS §Story-4

---

## §1 Phase 1 PR (hub, docs only)

### 1.1 Story MCT-178.md

**Files:** Create `docs/stories/MCT-178.md`

- [ ] §1-§6: 동기 / Epic context / Risk acceptance / AC 5건 / INV / Risk
  - AC-1 (D2): `docker compose --profile oneshot run --rm backtest-runner backtest --help` exit 0
  - AC-2 (D4): backtest-runner 1회 실행 → exit 0 → 컨테이너 종료 (restart "no" verify, docker ps 부재)
  - AC-3 (D10): `docker compose run --rm backtest-runner backtest --universe-id alt-30` override
  - AC-4 (D16): `.github/workflows/compose-validate.yml` PR push 시 compose config lint + up --wait health gate PASS
  - AC-5 (carry over): signal-collector 5종 Redis key `signal:*` prefix + dual write + Prometheus Gauge verify

- [ ] §6.5 Change Plan §7/§11 N/A 박제 (MCT-175 P0 lesson)
  - §7 security: backtest-runner = read-only NAS + local runs volume write. trust boundary 신규 없음 (paper-engine 동일 image).
  - §7.4 op-risk: oneshot 실행 실패 시 exit code != 0 → CI gate FAIL. compose-validate workflow 3분 budget.
  - §11 data-migration: signal-collector Redis key rename = 1주일 dual write rollback (legacy key 항상 존재 → consumer rollback 가능). cutover = LAND+7d 별 PR.
  - §11.6 idempotency: backtest-runner = stateless oneshot (idempotent). signal-collector dual write = idempotent (legacy + prefixed 동일 value).

- [ ] §7-§12: Dependencies / Test contract / Plan ref / FIX Ledger 빈 표 (fix-event-v1 schema) / Retro placeholder

### 1.2 ADR-030 amendment

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] §D2 amendment box (MCT-178 publish): backtest-runner service block (profiles oneshot + restart no + command backtest + no healthcheck)
- [ ] §D16 amendment box (MCT-178 publish, 신규): compose config CI lint (`docker compose config` + `up -d --wait` health gate, 3분 budget) + workflow `.github/workflows/compose-validate.yml`
- [ ] §D15 cross-ref: signal-collector Redis migration LAND (MCT-178 = MCT-177 §D15 carry over 이행)
- [ ] §References Plan(MCT-178) 1줄

### 1.3 CLAUDE.md + scope_manifest + counters
- [ ] 7 Story chain 표 MCT-178 PLANNED → IN_PROGRESS
- [ ] §MCT-178 IN_PROGRESS 섹션
- [ ] scope_manifest stories[MCT-178].status + started_date
- [ ] counters.json MCT-178 status

### 1.4 plan 파일 git add (MCT-176 P0 lesson)

### 1.5 Phase 1 Gate
- [ ] DesignReviewPL + iter PASS + admin merge

---

## §2 Phase 2 PR1 (cross-repo: hub + signal-collector, code)

### 2.1 mctrader-hub PR

**Files:**
- Modify: `compose.yml` (backtest-runner service 신규)
- Create: `.github/workflows/compose-validate.yml`

- [ ] backtest-runner service block:

```yaml
backtest-runner:
  image: ghcr.io/mclayer/mctrader-engine:latest
  container_name: mctrader-backtest-runner
  profiles: ["oneshot"]
  build:
    context: ../mctrader-engine
  command: ["backtest", "--help"]
  env_file:
    - .env.${COMPOSE_PROFILES:-dev}
  volumes:
    - mctrader_engine_runs:/var/lib/mctrader/runs
    - mctrader_l1:/var/lib/mctrader/data/l1:ro
  restart: "no"
  networks:
    - mctrader_net
  labels:
    mctrader.role: "backtest-runner"
    mctrader.story: "MCT-178"
```

- [ ] `.github/workflows/compose-validate.yml`:

```yaml
name: compose-validate
on:
  pull_request:
    paths:
      - "compose.yml"
      - ".env.example"
      - ".env.prod.example"
      - ".github/workflows/compose-validate.yml"
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: compose config lint (dev)
        run: cp .env.example .env.dev && docker compose --profile dev --env-file .env.dev config --quiet
      - name: compose config lint (prod)
        run: cp .env.prod.example .env.prod && docker compose --profile prod --env-file .env.prod config --quiet
      - name: compose config lint (oneshot)
        run: docker compose --profile oneshot --env-file .env.dev config --quiet
      - name: compose up health gate (dev infra only)
        run: |
          docker compose --profile dev --env-file .env.dev up -d postgres redis minio --wait --wait-timeout 180
          docker compose --profile dev down
```

### 2.2 mctrader-signal-collector PR (carry over)

**Files:**
- Modify: signal-collector 5 worker (fear_greed/ecos/kimchi/announcement/coinglass) Redis client

- [ ] Redis key prefix 적용 (dual write):

```python
REDIS_KEY_PREFIX = os.environ.get("REDIS_KEY_PREFIX", "signal")
DUAL_WRITE = os.environ.get("REDIS_MIGRATION_DUAL_WRITE", "true").lower() == "true"

def _signal_key(suffix: str) -> str:
    return f"{REDIS_KEY_PREFIX}:{suffix}"

def write_signal(redis, suffix, value):
    redis.set(_signal_key(suffix), value)  # prefixed
    if DUAL_WRITE:
        redis.set(suffix, value)  # legacy unprefixed (1주일 grace)
    DUAL_WRITE_GAUGE.set(1 if DUAL_WRITE else 0)
```

- [ ] Prometheus `redis_key_migration_dual_write_active` Gauge
- [ ] 신규 test: dual write verify (legacy + prefixed 동일 value)

### 2.3 cross-repo LAND 순서
1. signal-collector PR LAND 먼저 (Redis dual write)
2. hub PR LAND (compose backtest-runner + workflow)

### 2.4 Gate
- AC-1~5 verify + CodeReviewPL + admin merge

---

## §3 Phase 2 PR2 (hub, 박제)

- Story §10 FIX Ledger + §11 retro + §12 측정 + status COMPLETED
- ADR-030 §D2 backtest + §D16 amendment LAND confirm
- scope_manifest milestone 3/7 → 4/7
- CLAUDE.md MCT-178 COMPLETED
- RETRO-MCT-178.md (PMOAgent)
- EPIC-RESULTS §Story-4

---

## §4 다음 Story

MCT-178 COMPLETED → **MCT-179** (observability + WAL 30G prod measurement + DR mode + alert, D5/D8/D17). R2 CRITICAL (WAL 30G 미측정) 해소 owner.

---

## §5 Self-Review
- D2 backtest profile: §2.1 ✓
- D4 oneshot completion: §2.1 (restart no) ✓
- D10 universe override: §1.1 AC-3 ✓
- D16 compose CI lint: §2.1 workflow ✓
- carry over signal-collector Redis migration: §2.2 ✓
- §6.5 N/A 박제: §1.1 ✓
- §11 dual write rollback: §1.1 ✓
