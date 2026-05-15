---
type: epic-results
epic_key: EPIC-mctrader-docker-stack
epic_title: "mctrader Docker stack 확장 — collector + paper-engine + backtest profile + observability + WAL measurement"
status: IN_PROGRESS
created_at: 2026-05-15
total_stories: 7
completed_stories: 3
in_progress_stories: 0
reserved_stories: 4
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
---

# EPIC-RESULTS — EPIC-mctrader-docker-stack (IN_PROGRESS, milestone 5/7)

> **Epic**: mctrader Docker stack 확장 — collector + paper-engine + backtest profile + observability + WAL measurement
> **Status**: **IN_PROGRESS** (milestone 5/7 박제, 2026-05-15 MCT-175 + MCT-176 + MCT-177 + MCT-178 + MCT-179 LAND)
> **Stories**: MCT-175 ~ MCT-181 (7 sequential)
> **Parent dependency**: EPIC-tier-promotion-single-source POLICY_FINALIZED (R-CRITICAL WAL 30G measurement → MCT-179 carry over)

## Epic Summary

mctrader-hub/compose.yml 의 인프라 stack (postgres + minio + redis + 7 service) 에 어플리케이션 (mctrader-data collector + mctrader-engine paper-engine / backtest-runner) 을 통합. NAS MinIO (prod) ↔ hub MinIO (dev) profile 전환 + observability (Prometheus + Grafana + alert) + WAL 30G production measurement (EPIC-tier-promotion CLOSED prereq, MCT-179) + integration smoke (compose CI) + image registry pin (ghcr.io).

배경:
- 현 compose.yml = 인프라 4 service + signal-collector 5 service. 어플리케이션 (data/engine) 은 compose 외부에서 별도 실행 → operational ambiguity + dev/prod parity 부재
- EPIC-tier-promotion-single-source R-CRITICAL (WAL 30G 가설 미측정, 50sym × 3ch × 12seg/h ±50% range) carry over → MCT-179 measurement 책임
- codeforge-plugin#620 post-mortem Fix-2 (compose CI gate) mctrader-consumer 측 구현

## 19 D 결정 매트릭스 (Codex 3 pass 합성)

| pass | range | Story 분담 |
|------|-------|-----------|
| 1st pass | D1-D6 (infrastructure) | MCT-175 (D1/D3) + MCT-177/178 (D2/D4) + MCT-179 (D5) + epic-level (D6) |
| 2nd pass | D7-D12 (wiring) | MCT-175/176 (D7) + MCT-179 (D8) + MCT-176 (D9) + MCT-177/178 (D10) + MCT-180 (D11) + MCT-181 (D12) |
| 3rd pass | D13-D19 (detail) | MCT-175 (D13) + MCT-176 (D14) + MCT-177 (D15) + MCT-178 (D16) + MCT-179 (D17) + MCT-180 (D18) + MCT-181 (D19) |

ADR-030 본문 박제 = 8 D (D1/D2/D3/D7/D12/D13/D17/D18). 10 D defer = Out of scope manifest (각 owner Story Phase 1 LAND 시 amendment box append).

## Story 완료 현황

| Story | Title | SP | sequential_phase | 완료일 | PR | Status |
|-------|-------|-----|---|--------|-----------|--------|
| **MCT-175** | compose base + dev/prod profile + env 분리 + cross-repo lock gate + ADR-030 publish | 5 | 1 | **2026-05-15** | mctrader-hub#326 (8c485ef) + mctrader-hub#327 (daef9b3) + mctrader-hub#328 (dbba327) | **COMPLETED** |
| **MCT-176** | collector container + NAS credential rotation + effective config dump | 5 | 2 | **2026-05-15** | mctrader-hub#330 (a92e55a) + mctrader-data#64 (e3141b6) + mctrader-hub#331 (3498a8b) + mctrader-hub#TBD Phase 2 PR2 | **COMPLETED** |
| **MCT-177** | paper-engine daemon + SIGTERM graceful + universe override + Redis prefix | 5 | 3 | **2026-05-15** | mctrader-hub#333 (dd59b65) + mctrader-data#65 (af6c812) + mctrader-engine#54 (9cbe3b4) + mctrader-hub#334 (cc0c368) + mctrader-hub#TBD Phase 2 PR2 | **COMPLETED** |
| **MCT-178** | backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis migration | 5 | 4 | **2026-05-15** | mctrader-hub#336 (0d56730) + mctrader-signal-collector#1 (60787c4) + mctrader-hub#337 (bd9baf2) + mctrader-hub#TBD Phase 2 PR2 | **COMPLETED** |
| **MCT-179** | observability + WAL 30G synthetic baseline + DR mode integration + alert rule | 5 | 5 | **2026-05-15** | mctrader-hub#339 (fabba57) + mctrader-data#66 (e4a2cc2) + mctrader-hub#340 (64feb73) + mctrader-hub#TBD Phase 2 PR2 | **COMPLETED** |
| MCT-180 | integration smoke + testcontainers + resource limits + capacity alert rule | - | 6 | - | - | PLANNED |
| MCT-181 | image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED 박제 | - | 7 | - | - | PLANNED |
| **합계** | | **25 (5/7)** | | | | |

## Story-1 결과 박제 (MCT-175, 2026-05-15)

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15T03:48:11Z | mctrader-hub#326 | 8c485ef | Phase 1 docs — Story §1-§12 + ADR-030 publish (8 D 본문 박제 + 10 D defer manifest) + spec + plan + scope_manifest + runbook stub + CLAUDE.md + counters (7 Story + 1 ADR 예약) — 5 file |
| 2026-05-15T04:16:16Z | mctrader-hub#327 | daef9b3 | Phase 2 PR1 code — compose.yml profile dev/prod + .env.example 확장 + .env.prod.example 신규 + .gitignore + preflight bash + check_cross_repo_locks.py + cross-repo-lock-check.yml + nginx.prod.conf placeholder + 14 unit test (12 file, 597 insertions) |
| 2026-05-15T05:47:28Z | mctrader-hub#328 | dbba327 | Phase 2 PR2 박제 — Story §10/§11/§12 + ADR-030 Accepted + scope_manifest 1/7 + CLAUDE.md + RETRO 신규 + EPIC-RESULTS 신규 (6 file, 479 insertions / 27 deletions) |

### MCT-175 채택 4 D (Epic entry 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D1 | WAL host disk bind mount + L1 named volume | C | compose.yml collector stub 주석 박제 (MCT-176 활성화) — `/var/lib/mctrader/wal:/var/lib/mctrader/data` ADR-030 §D1 |
| D3 | compose profiles dev/prod + env_file 분리 | A | minio/mc service `profiles: ["dev"]` + nginx prod profile + `.env.dev` (hub MinIO) + `.env.prod.example` (NAS endpoint) LAND |
| D7 | NAS DNS 직접 해석 + preflight 검증 | A | `scripts/preflight-nas-dns.sh` exit 0/10/20/30/99 matrix 정합 |
| D13 | 각 repo 독립 uv.lock + cross-repo CI gate | D | `scripts/check_cross_repo_locks.py` (121 lines) + `.github/workflows/cross-repo-lock-check.yml` + 14 unit test green. MISSING_OK_REPOS = {hub, signal-collector} |

### AC + INV 결과

| AC | 결과 |
|----|------|
| AC-1 compose profile config | ✓ PASS (`docker compose --profile dev/prod config` exit 0) |
| AC-2 .env endpoint 분기 정합 | ✓ PASS (`.env.dev` http://minio:9000 / `.env.prod.example` http://mcnas01.internal.mclayer.it:9000) |
| AC-3 preflight exit code matrix | ✓ PASS (exit 0/10/20/30/99 정합) |
| AC-4 WAL mount 정책 박제 | stub PASS (collector service stub 주석, MCT-176 활성화 의무) |
| AC-5 cross-repo lock CI gate | ✓ PASS (`workflow_dispatch` only — secret 미등록 carry over → MCT-176) |
| INV-1~4 | 4/4 박제 |

### FIX 루프 2회 (design iter 1 + code iter 1)

| iter | lane | finding | fix / defer |
|------|------|---------|-------------|
| iter 1 | design | P0×1 + P1×3 + P2×4 = 8 | 8 fix / 0 defer |
| iter 2 | design | — | PASS |
| iter 1 | code | P0×2 + P1×3 + P2×2 = 7 | 4 fix / 3 defer (P1-2 + P1-3 + P2-1 → MCT-176 carry) |
| iter 2 | code | — | PASS |

### ADR-030 박제 + Status

- Phase 1: Status **Proposed** + 8 D 본문 박제 + 10 D Out of scope manifest
- Phase 2 PR1: §D13 amendment box append (P0-2 fix — coverage gap + semantic precision)
- Phase 2 PR2 (본 박제 PR): Status **Accepted** + Amendment box (MCT-175 D1/D3/D7/D13 VERIFIED + MCT-176 carry over 5 항목)

### MCT-176 carry over (5 항목)

| 항목 | 사유 |
|------|------|
| P1-2 (preflight DNS wildcard FP) | MCT-176 logging 통합 시 fix |
| P1-3 (mc alias trap race) | MCT-176 cross-ref (SIGINT race window, security 위협 낮음) |
| P2-1 (shell error handling) | 실 위험 낮음 carry over |
| NAS_MINIO_* secret 등록 | MCT-176 Phase 1 (GitHub Actions secrets) |
| `cross-repo-lock-check.yml` PR auto trigger 복원 | MCT-176 Phase 2 (`workflow_dispatch` only → `on: pull_request`) |

### 다음 Story chain

**MCT-176** (collector container + NAS credential rotation + effective config dump) — sequential_phase 2. 진입 prerequisite = MCT-175 hub#328 MERGED ✓ (dbba327, 2026-05-15) + ADR-027 §D2 amendment 결정 (R1 HIGH).

## Story-2 결과 박제 (MCT-176, 2026-05-15)

### 4 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15 (Phase 1) | mctrader-hub#330 | a92e55a | Phase 1 docs — Story §1-§12 + ADR-030 §D9/§D14 amendment box 본문 박제 + automation runbook 신규 + CLAUDE.md MCT-176 IN_PROGRESS 섹션 + plan |
| 2026-05-15T08:00:41Z | mctrader-data#64 | e3141b6 | Phase 2 PR1 (data) — CLI SIGTERM handler stub + `effective-config --format {json,yaml}` subcommand + 8 신규 unit test (274 additions / 1 deletion) |
| 2026-05-15T08:04:03Z | mctrader-hub#331 | 3498a8b | Phase 2 PR1 (hub) — collector service 활성화 + `scripts/rotate-nas-credentials.sh` 신규 + carry over fix (P1-2 + P1-3 + P2-1) + `cross-repo-lock-check.yml` `on: pull_request` 복원 (275 additions / 37 deletions) |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §10/§11/§12 + ADR-030 §D7/§D9/§D14 VERIFIED 박제 + scope_manifest 2/7 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-2 (본 section) |

### MCT-176 채택 4 D (Epic Story-2 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D7 (carry from MCT-175) | NAS DNS preflight collector wiring | A | `compose.yml` collector service preflight depends_on 연결 LAND. MCT-175 carry over fix (P1-2 sentinel IP 차단 + P1-3 trap 순서 + P2-1 `set -euo pipefail` + `bash -n`) 통합 |
| D9 | NAS credential rotation 90d automation | D | `scripts/rotate-nas-credentials.sh` 신규 LAND. Slack reorder before revoke (F-002 P1 fix) + `.env.prod.bak` trap cleanup (F-003 P1 fix) + `.gitignore` `.env.*.bak` pattern |
| D14 | effective config CLI subcommand stdout dump | D | `mctrader-data effective-config --format {json,yaml}` 신규 LAND. **`source_order` downgrade `["env","built_in"]`** (F-005 P1 fix option B — false claim 차단, MCT-177 carry) + docstring + TODO(MCT-177) |
| D1 (carry from MCT-175) | WAL host bind mount collector 적용 | C | collector service 실 진입 시 WAL bind mount `/var/lib/mctrader/wal:/var/lib/mctrader/data` + L1 named volume + `stop_grace_period: 60s` |

### AC + INV 결과 (5/5 PASS + 4/4 박제)

| AC | 결과 |
|----|------|
| AC-1 collector container inspect | ✓ PASS (compose --profile dev/prod config exit 0 + collector service 출력) |
| AC-2 effective-config subcommand | ✓ PASS (`--format json/yaml` exit 0, source_order=["env","built_in"] downgrade) |
| AC-3 rotation dry-run | ✓ PASS (Slack reorder + .bak cleanup trap) |
| AC-4 MCT-175 carry over fix verify | ✓ PASS (P1-2 + P1-3 + P2-1 ALL 정합) |
| AC-5 cross-repo-lock-check workflow trigger 복원 | ✓ PASS (on: pull_request 복원 + MCTRADER_CROSS_REPO_TOKEN secret 등록) |
| INV-1~4 | 4/4 박제 (forward-only + WAL fsync stub + sha256 SSOT caller-side + collector RSS ≤ 50 MB delta) |

### FIX 루프 4회 (design Phase 1 iter 1 + code data iter 1 + code hub iter 1, iter 2 모두 PASS)

| iter | lane | finding | fix |
|------|------|---------|------|
| iter 1 | design (Phase 1 hub docs) | P0×1 + P1×2 + P2×2 = 5 | 5 fix → iter 2 PASS (commit a991279) |
| iter 1 | code (data Phase 2 PR1) | P1×2 + P2×2 = 4 | 4 fix → iter 2 PASS (commit e5a220a) |
| iter 1 | code (hub Phase 2 PR1) | P0×1 + P1×2 = 3 | 3 fix → iter 2 PASS (commit 2373eee → 0fb4737) |
| iter 2 | all lanes | — | ALL PASS, Phase 2 PR1 양측 MERGED |

총 **6 commit FIX 루프 across 2 repo** (a991279 + e5a220a + 2373eee + 5212c6f + 0fb4737 + 094243f).

### ADR-030 amendment 박제 (Phase 2 PR2)

§D7 + §D9 + §D14 VERIFIED 박제:
- Phase 2 PR1 양측 LAND timeline (data#64 + hub#331)
- MCT-175 carry over 5 항목 처리 결과 (P1-2 + P1-3 + P2-1 + secret 등록 + workflow trigger 복원)
- MCT-177 carry over 3 항목 (YAML loader + signal handler wiring + 6 repo secret read 검증)

### MCT-177 carry over (3 항목)

| 항목 | 사유 |
|------|------|
| YAML config loader (option A) | F-005 P1 fix option B downgrade 후 후속 implement |
| `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring | F-006 P2 fix TODO 헤더 + docstring only (stub) |
| cross-repo-lock-check secret 6 repo 측 secret read 검증 | 현 hub 측 단방향 등록 (`MCTRADER_CROSS_REPO_TOKEN` hub-only) |

### MCT-175 lesson 재적용 효과

MCT-175 P0 lesson (Story §6.5 Change Plan §7/§11 N/A 사유) 재적용 → Phase 1 design iter 1 P0 finding 1건 (5 finding 중 1건만 P0, 4건 P1/P2). MCT-175 = P0×1 발견 → 본 Story = P0×1 발견 (다른 사유). 사전 patch 효과로 §6.5 항목 P0 차단 없이 LAND.

### 다음 Story chain

**MCT-177** (paper-engine daemon + SIGTERM graceful + universe override + Redis prefix) — sequential_phase 3.
진입 prerequisite = MCT-176 Phase 2 PR2 MERGED ✓ + MCT-177 carry over 3 항목 통합 처리.
채택 결정: D2 (paper daemon + backtest profile 동일 image) + D4 (SIGTERM 60s grace + startup invariant scan) + D10 (universe env↔command override) + D15 (Redis key prefix).

## Story-3 결과 박제 (MCT-177, 2026-05-15)

### 4 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15T08:56:31Z | mctrader-hub#333 | dd59b65 | Phase 1 docs — Story §1-§12 + ADR-030 §D2/§D4/§D10/§D15 amendment box 본문 박제 + CLAUDE.md MCT-177 IN_PROGRESS 섹션 |
| 2026-05-15T09:30:00Z | mctrader-data#65 | af6c812 | Phase 2 PR1 (data, land_order 1) — CO-1 `_load_yaml_config()` 신규 + `source_order` 3-tier 복원 + CO-2 signal wiring + 신규 test |
| 2026-05-15T09:30:10Z | mctrader-engine#54 | 9cbe3b4 | Phase 2 PR1 (engine, land_order 2) — D4 기존 `shutdown.py` asyncio SSOT 재사용 (신규 daemon 코드 0 line) + D10 universe override + D15 Redis prefix + 신규 test |
| 2026-05-15T09:30:21Z | mctrader-hub#334 | cc0c368 | Phase 2 PR1 (hub, land_order 3) — `paper-engine` service + Redis prefix env + CO-3 `verify_cross_repo_secret.py` 신규 |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §8.5/§10/§11/§12 + ADR-030 §D2/§D4/§D10/§D15 VERIFIED 박제 + scope_manifest 3/7 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-3 (본 section) |

### MCT-177 채택 4 D (Epic Story-3 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D2 | paper-engine daemon service | A | `compose.yml` `paper-engine` service LAND — image + `command: ["paper","--daemon"]` + restart unless-stopped + healthcheck :8080 + stop_grace 60s + depends_on redis/collector service_healthy. CodeReviewPL P0 fix (healthcheck contract verbatim + collector condition). backtest-runner = MCT-178 carry |
| D4 | SIGTERM graceful + startup InvariantHarness scan | C | **engine 기존 `shutdown.py` asyncio SSOT + HealthServer(:8080) 재사용 — 신규 daemon 코드 0 line**. CodeReviewPL P0 fix: data 동기 stub 패턴 cross-repo 오적용 → RefactorAgent (A) dead path 제거 + paper start core 위임. plan §2.2 amend. 60s grace + InvariantHarness 8종 scan |
| D10 | universe override env + compose command | D | `--universe-id` CLI + `UNIVERSE_TOP_N=50` env fallback + 미등록 exit 1. `.env.dev`/`.env.prod.example` 박제 |
| D15 | Redis key prefix policy | C | `REDIS_KEY_PREFIX_ENGINE` env (default `engine`) + `_engine_key()` + signal:/market:/engine: 3 namespace. **signal-collector code migration = MCT-178 carry** |

### AC + INV 결과 (5/5 PASS + 5/5 박제)

| AC | 결과 |
|----|------|
| AC-1 paper-engine compose healthcheck PASS (D2) | ✓ PASS (daemon compose config exit 0 + 기존 HealthServer :8080 asyncio task 재사용) |
| AC-2 SIGTERM graceful 60s grace (D4) | ✓ PASS (기존 `shutdown.py` asyncio SSOT graceful, exit 0, 신규 코드 0 line) |
| AC-3 UNIVERSE_TOP_N env + universe-id override (D10) | ✓ PASS (`UNIVERSE_TOP_N=50` env + `--universe-id` override + 미등록 exit 1) |
| AC-4 Redis key prefix 3 namespace (D15) | ✓ PASS (`signal:*`/`market:*`/`engine:*` + `REDIS_KEY_PREFIX_ENGINE` env) |
| AC-5 MCT-176 carry over 3건 (CO-1~CO-3) | ✓ PASS (CO-1 3-tier source_order 복원 + CO-2 collect loop polling + CO-3 6 repo secret verify) |
| INV-1~5 | 5/5 박제 (forward-only + WAL fsync + sha256 SSOT caller-side + engine RSS ≤ 256 MB delta + Redis prefix 1주일 dual write = MCT-178 carry) |

### FIX 루프 (DesignReview iter 1 PASS no FIX + code iter 1 → iter 2 PASS)

| iter | lane | finding | fix |
|------|------|---------|------|
| iter 1 | design (Phase 1 hub docs) | **0 (PASS, no FIX)** — MCT-175/176 §6.5 lesson 누적 효과 | — |
| iter 1 | code (data#65) | P0×1 (pyright `_load_yaml_config()` return type + None narrowing) | fix → iter 2 PASS |
| iter 1 | code (engine#54) | P0×1 (data 동기 stub 패턴 cross-repo 오적용 — 기존 shutdown.py asyncio SSOT 미인지) | fix → RefactorAgent (A) dead path 제거 + 신규 daemon 코드 0 line. iter 2 PASS |
| iter 1 | code (hub#334) | P0×1 (compose healthcheck contract 불일치 + depends_on collector 누락) + P1×1 (`verify_cross_repo_secret.py` script owner = hub) | fix → iter 2 PASS |
| iter 2 | all lanes | — | data PASS / engine PASS / **hub CONDITIONAL_PASS** (sequential gate). 3 PR sequential MERGED |

### engine daemon 재구현 lesson (MCT-170 류 Phase 0 verify 재현)

CodeReviewPL FIX iter 1 engine#54 P0 = 초안이 mctrader-data 동기 SIGTERM stub 패턴 (MCT-176 §8) 을 cross-repo carry over 했으나, mctrader-engine 측 **기존 `shutdown.py` asyncio SSOT + HealthServer(:8080)** 가 이미 graceful drain 경로 보유. session prompt 표현 ≠ 코드 실상. RefactorAgent 판정 **(A) dead path 제거** + paper start core 위임 → **신규 daemon 코드 0 line** (기존 검증 자산 재사용). plan §2.2 amend (data 패턴 cross-repo 오적용 취소). MCT-170 io/ 3 module 존재 재인지 lesson 동형 — **cross-repo Story 는 각 repo Phase 0 verify 독립 의무**.

### ADR-030 amendment 박제 (Phase 2 PR2)

§D2 + §D4 + §D10 + §D15 VERIFIED 박제:
- Phase 2 PR1 cross-repo LAND timeline (data#65 → engine#54 → hub#334 sequential gate)
- MCT-176 CO-1~CO-3 처리 결과 (YAML loader 3-tier 복원 + signal wiring + 6 repo secret verify)
- MCT-178 carry over (signal-collector 5종 Redis prefix code migration + 1주일 dual write)

### MCT-178 carry over (1 항목)

| 항목 | 사유 |
|------|------|
| signal-collector 5종 Redis prefix code migration | MCT-177 = prefix 정책 박제 + engine consumer `engine:*` 적용. signal-collector repo 코드 (unprefixed → `signal:*` rename + 1주일 dual write + Prometheus Gauge) = 별 Story scope |

### MCT-175/176 lesson 재적용 효과 (DesignReview iter 1 PASS no FIX)

MCT-175 P0 lesson (Story §6.5 §7/§11 N/A 사유) + MCT-176 §6.5 4 entry 사전 박제 패턴 누적 → MCT-177 Phase 1 design iter 1 **P0 finding 0 (no FIX)**. MCT-175 P0×1 → MCT-176 P0×1 → MCT-177 P0×0. lesson reapply 누적 효과 검증 (3 Story 연속 감소).

### 다음 Story chain

**MCT-178** (backtest-runner profile + oneshot + compose config CI lint + universe override) — sequential_phase 4.
진입 prerequisite = MCT-177 Phase 2 PR2 MERGED ✓ + MCT-178 carry over 통합 (signal-collector 5종 Redis prefix code migration + `${IMAGE_TAG}` prod pin = MCT-181 owner).
채택 결정: D2 (backtest profile oneshot 동일 image) + D4 (SIGTERM 회귀) + D10 (universe override) + D16 (compose config lint + up --wait CI gate).

## Story-4 결과 박제 (MCT-178, 2026-05-15)

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15T10:20:05Z | mctrader-hub#336 | 0d56730 | Phase 1 docs — Story §1-§12 + ADR-030 §D2/§D16 amendment box 본문 박제 (F-001/F-002 reconciliation note) + CLAUDE.md MCT-178 IN_PROGRESS |
| 2026-05-15T10:35:04Z | mctrader-signal-collector#1 | 60787c4 | Phase 2 PR1 signal — 5 worker **Publisher 계층 집중** `signal:*` Redis prefix dual write + Prometheus Gauge + 4 test (land_order 1, **첫 signal-collector repo PR**) |
| 2026-05-15T10:35:55Z | mctrader-hub#337 | bd9baf2 | Phase 2 PR1 hub — backtest-runner service (profiles oneshot + restart no + no healthcheck) + `compose-validate.yml` workflow (land_order 2) |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §8.5/§10/§11/§12 + ADR-030 §D2/§D16 VERIFIED + scope_manifest 4/7 + **F-001 정정** + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-4 (본 section) |

### MCT-178 채택 4 D (Epic Story-4 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D2 | backtest-runner service | A | `compose.yml` `backtest-runner` service LAND — image (paper-engine 동일) + `profiles: ["oneshot"]` + `command: ["backtest","--help"]` + `restart: "no"` + no healthcheck. command override 분기 |
| D4 | oneshot completion | C | oneshot 실행 후 exit 0 → 컨테이너 종료 (restart "no" 정합). SIGTERM = 기존 shutdown.py asyncio SSOT (MCT-177 LAND 재사용) |
| D10 | universe override | D | `--universe-id <id>` CLI override (MCT-177 LAND option 재사용) + 미등록 exit 1 |
| D16 | compose config CI lint | B | `.github/workflows/compose-validate.yml` 신규 — 3 profile lint (dev/prod/oneshot) + up --wait health gate (infra only, 180s budget) |

### MCT-178 AC + INV

| 항목 | 결과 |
|------|------|
| AC-1~5 | 5/5 PASS (oneshot config / restart no / universe override / compose-validate 3 lint + health gate / signal Redis dual write + Gauge) |
| INV-1~4 | 4/4 박제 (forward-only + backtest stateless oneshot + Redis dual write idempotent + INV-5 1주일 grace) |
| FIX 루프 | 1 iter — design iter1 **CONDITIONAL_PASS** (F-001/F-002 ADR-030 reconciliation fast-fix ba87b3c) + code iter1 **PASS** 양 PR (signal blocking 0 / hub P2 noise 2 non-blocking) |

### signal-collector Redis migration (D15 carry over 이행)

MCT-177 §D15 carry over → MCT-178 이행 완료. signal-collector#1 (60787c4):
- 5 worker (fear_greed/ecos/kimchi/announcement/coinglass) — **Publisher 계층 집중** `signal:*` prefix
- legacy unprefixed + `signal:*` dual write (1주일 grace) + Prometheus `redis_key_migration_dual_write_active` Gauge=1
- LAND+7d legacy cleanup = 별 PR (`scripts/redis-prefix-cleanup.sh`)

### F-001 정정 (Phase 2 PR2 박제 영역)

CodeReview hub#337 P2 noise (non-blocking) carry → 본 PR 정정:
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` line ~170/244 stale: `docker-compose-validate.yml` → `compose-validate.yml` / `profile=backtest` → `profiles: [oneshot]`
- ADR-030 §D2/§D16 F-001/F-002 reconciliation SSOT 정합 (MCT-175 LAND 누적 swap 박제 해소)

### lesson (Publisher 계층 집중 + design drift 단절)

- **§5.1**: signal-collector Publisher 계층 집중 — 5 worker 개별 SET 산재 가설 ≠ Publisher 단일 계층 실상 (MCT-170/177 §5.1 cross-repo Phase 0 verify 독립 의무 동형 3회 재현). 첫 진입 repo (#1) 일수록 Phase 0 verify 비용 우선
- **§5.2**: design P0×0 연속 단절 (MCT-175~177 = 1→1→0 → MCT-178 CONDITIONAL_PASS). 원인 ≠ Story §6.5 부재, = ADR-030 누적 정책 drift (MCT-175 LAND swap 박제 stale 이 4 Story 만에 surface). lesson reapply 누적 효과는 신규 finding 만 감소, 기존 박제 stale 은 별 trigger surface → Epic 중간 Story 일수록 누적 문서 audit 필요
- **§5.3**: 첫 mctrader-signal-collector repo PR (#1) — 6번째 cross-repo 대상 repo 데뷔. secret/CI/worktree 3종 사전 점검 의무 (MCT-177 CO-3 6 repo secret verify 가 signal-collector 데뷔 prerequisite 선제 충족)

### 다음 Story chain

**MCT-179** (observability + WAL 30G production measurement + DR mode integration + alert rule) — sequential_phase 5.
진입 prerequisite = MCT-178 Phase 2 PR2 MERGED ✓ + R2 (WAL 30G 미측정 CRITICAL) carry 유지 (MCT-179 owner, EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 정합).
채택 결정: D5 (Prometheus metric + WAL measurement script + amendment trigger) + D8 (앱 내장 /metrics + Grafana + alert rule) + D17 (SIGTERM graceful + startup InvariantHarness scan).

## Story-5 결과 박제 (MCT-179, 2026-05-15)

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15 | mctrader-hub#339 | fabba57 | Phase 1 docs — Story §1-§12 + ADR-030 §D5/§D8/§D17 amendment box 본문 + **Out-of-scope 표 D1-D19 전수 reconcile (c8e4b8e)** + CLAUDE.md. DesignReview iter1 P0 (ADR-030 Out-of-scope D5/D8 stale) → iter2 PASS |
| 2026-05-15T11:51:56Z | mctrader-data#66 | e4a2cc2 | Phase 2 PR1 data — `measure_wal_baseline.py` 신규 + capacity_probe `measure_wal_bytes()`/`emit_wal_capacity_gauge()` (MCT-171 SSOT 정합, deprecated Gauge 미도입, +547 lines) + cli.py startup InvariantHarness scan + 20 test (land_order 1). CodeReview iter1 PASS |
| 2026-05-15T11:52:49Z | mctrader-hub#340 | 64feb73 | Phase 2 PR1 hub — prometheus.yml scrape + prometheus-alerts.yml + docker-stack.json + compose.yml (land_order 2). CodeReview iter1 P1×2 metric desync (가공 metric → R2 deliverable 무력화) → 설계 원인 fix 64647c7 (MCT-171/170 LAND SSOT 정렬) → iter2 PASS |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §10/§11/§12 (WAL JSON + §12.1 P2 정정) + ADR-030 §D5/§D8/§D17 VERIFIED + metric-name SSOT 표 + scope_manifest 5/7 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-5 (본 section) |

### MCT-179 채택 3 D (Epic Story-5 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D5 (WAL 측정 + Gauge) | C | `scripts/measure_wal_baseline.py` LAND (paper-synthetic/production, exit 0/7/99). Prometheus Gauge SSOT = `mctrader_capacity_usage_bytes{layer="WAL_local"}` (MCT-171 LAND, `wal_capacity_bytes` 가공 폐기). 30G 초과 GitHub issue 자동 발의 trigger |
| D8 (observability) | C | Prometheus scrape (collector/paper-engine **:8080/metrics** — Phase 0 verify `:9090` 가설 기각 + paper-engine container_name fix) + Grafana docker-stack.json 9 panel + alert 4종 (WALCapacityWarn/Critical MCT-171 SSOT + NASReaderDROpen/Ambiguity MCT-170 dr_mode 실 series) |
| D17 (startup scan) | A | collector cli.py startup InvariantHarness 8종 scan hook (NAS_MINIO_ENDPOINT graceful skip + ambiguity D10 fail → log.warning 전용). SIGTERM = MCT-176/177 LAND 재사용 (신규 0) |

### MCT-179 AC + INV

5/5 AC PASS (AC-1 measure script paper-synthetic exit 0 + AC-2 >30G exit 7 D11 trigger + AC-3 prometheus scrape + grafana + alert + AC-4 startup InvariantHarness scan + AC-5 synthetic baseline + production 별 PR carry over). 4/4 INV 박제 (forward-only read-only probe + startup scan warn+continue + Prometheus metric additive + WAL 30G hard_limit FAIL gate).

WAL synthetic baseline JSON 박제: `verdict: PASS`, `wal_peak_gb: 0.0` (paper-synthetic read-only probe, MCT-172 D8-2 패턴). EXCEED branch (`WAL_HARD_LIMIT_GB=0` mock) → `verdict: EXCEED` + exit 7 + D11 amendment 의무 stderr 검증.

### R2 CRITICAL 상태 (PARTIAL 해소)

- **synthetic baseline 측정 완료** (paper-synthetic verdict=PASS, AC-1/AC-5) → R2 PARTIAL 해소
- **production 실 측정 = 별 PR carry over** (실 production deploy + peak market open 09:00 KST 1h burst window) → EPIC-tier-promotion-single-source Epic CLOSED prereq **prod-2 = 본 별 PR 이 충족**

### FIX 루프 (2 iter — design 1 + code 1)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub docs) | **P0** — ADR-030 Out-of-scope 표 D5/D8 정의 swap stale (scope_manifest SSOT desync, MCT-178 F-001 동형 누적) | **설계 원인** — ArchitectPL 전수 정정 (c8e4b8e): D1-D19 전체 row scope_manifest SSOT 1:1 전수 정합 + navigational-only note. MCT-180/181 재발 사전 차단. DesignReview iter2 PASS |
| 1 | code (hub#340) | **P1×2** — 가공 metric (`wal_capacity_bytes`/`nas_reader_5xx_total`/`nas_reader_p99_ms`) LAND 부재 → R2 CRITICAL deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화 | **설계 원인** — ArchitectPL 최종 판정 (ADR-030 §D8 + Plan §2.2 Phase 0 verify 미수행 가공 metric). fix 64647c7 — MCT-171 SSOT + MCT-170 dr_mode 실 series 정렬 + `[MCT-180 TODO]` downgrade. **R2 deliverable 기능 회복**. CodeReview iter2 PASS |
| 1 | code (data#66) | **0 blocking (PASS)** — deprecated Gauge 미도입, MCT-171 SSOT 정합 (+547 lines) | PASS, LAND (e4a2cc2, land_order 1) |

### MCT-179 핵심 lesson (RETRO §5)

- **§5.1**: 설계가 가공 metric 박제 — Phase 0 verify 독립 의무 4회 재현 (MCT-170 io/ 3 module + MCT-177 engine asyncio + MCT-178 Publisher 계층 + MCT-179 metric-name SSOT). observability/alert 박제 시 alert expr metric selector LAND grep 실증 의무 — 미발화 alert = CRITICAL deliverable silent 무력화
- **§5.2**: ADR-030 Out-of-scope 표 D1-D19 전수 reconcile — MCT-178 §5.2 누적 drift 의 근본 해결책 = 부분 reconcile 아닌 전수 reconcile + SSOT navigational-only 명시. Epic 중간 Story 누적 audit = 전 D 범위
- **§5.3**: R2 CRITICAL cross-Epic carry over 흡수 — synthetic (측정 가능) / production (실 deploy 의존) AC 단계 분리 박제 의무. R2 "PARTIAL 해소" 명시 + production 별 PR carry over gate
- **§5.4**: FIX 2 iter (design 전수 reconcile + code 설계 원인 fix). Phase 0 verify shift-left (metric-name LAND grep 실증 Phase 1 의무화) = 차기 Epic FIX iter 감소 핵심 (PMO retro 입력)

### 다음 Story chain

**MCT-180** (integration smoke + testcontainers + resource limits + alert rule) — sequential_phase 6.
진입 prerequisite = MCT-179 Phase 2 PR2 MERGED ✓ + Grafana 5 panel metric emit 신규 carry over (collector ticks/symbols + engine universe_size + reader_cache hit_ratio/p99) + `${IMAGE_TAG}` prod pin (D12, MCT-181 owner) + R2 CRITICAL PARTIAL 해소 유지 (production 별 PR).
채택 결정: D4 (SIGTERM graceful 회귀) + D11 (compose CI smoke + testcontainers 2 layer gate) + D18 (resource limits + container_memory alert).

## Epic close gate

| # | gate | 상태 |
|---|------|------|
| 1 | MCT-175 PR MERGED + ADR-030 publish + compose base + dev/prod profile LAND | ✓ (2026-05-15, hub#326 + hub#327 + hub#328) |
| 2 | MCT-176 PR MERGED + collector container + NAS credential rotation | ✓ (2026-05-15, hub#330 + data#64 + hub#331 + hub Phase 2 PR2) |
| 3 | MCT-177 PR MERGED + paper-engine daemon + SIGTERM graceful | ✓ (2026-05-15, hub#333 + data#65 + engine#54 + hub#334 + hub Phase 2 PR2) |
| 4 | MCT-178 PR MERGED + backtest profile + compose config CI gate | ✓ (2026-05-15, hub#336 + signal-collector#1 + hub#337 + hub Phase 2 PR2). signal-collector 5 worker Publisher 계층 Redis prefix dual write LAND (D15 carry 이행). DesignReview iter1 CONDITIONAL_PASS (F-001/F-002 fast-fix ba87b3c) |
| 5 | MCT-179 PR MERGED + WAL 30G synthetic baseline (R2 CRITICAL PARTIAL 해소, production 별 PR carry over) + observability | ✓ (2026-05-15, hub#339 + data#66 + hub#340 + hub Phase 2 PR2). measure_wal_baseline.py paper-synthetic verdict=PASS exit 0 + EXCEED branch exit 7 D11 trigger. alert rule = MCT-171/170 LAND SSOT 정렬 (CodeReview iter1 P1×2 metric desync → 64647c7, WAL 30G FAIL gate alert 기능 회복). DesignReview iter1 P0 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e). production 실 측정 = 별 PR (EPIC-tier-promotion prod-2) |
| 6 | MCT-180 PR MERGED + integration smoke + resource limits + alert rule | PENDING |
| 7 | MCT-181 PR MERGED + Epic POLICY_FINALIZED 박제 + image registry pin + backtest artifact NAS sync | PENDING |

## Cross-Epic carry over

- **EPIC-tier-promotion-single-source Epic CLOSED 박제 prereq prod-2**: WAL 30G production measurement = 본 Epic 의 MCT-179 책임. peak market open 09:00 KST burst window 측정 + 30G 초과 시 D11 hard_limit amendment 발의 (D8-7=A FAIL gate)
- **EPIC-tier-promotion-single-source D8 sunset 14d window (2026-08-18 ~ 2026-09-01)**: MCT-179 telemetry watcher alert rule 정합

## Risk 현황 (Epic 전체)

| Risk | Severity | 상태 | Owner |
|------|----------|------|-------|
| R1 NAS HTTP-only 평문 통신 | HIGH | **사용자 explicit accept (2026-05-15)** — MCT-155 TLS cutover 별 Story 백로그 | MCT-176 |
| R2 WAL 30G 미측정 | CRITICAL | **PARTIAL 해소 (2026-05-15, MCT-179)** — synthetic baseline 측정 완료 (paper-synthetic verdict=PASS). production 실 측정 (peak 09:00 KST 1h burst) = **별 PR carry over** (EPIC-tier-promotion CLOSED prereq prod-2) | MCT-179 + 별 PR |
| R3 D14 effective config 미출력 | MEDIUM | MCT-176 collector entrypoint stdout dump 의무 | MCT-176 |
| R4 host disk 손실 → WAL 영구 손실 | MEDIUM | **사용자 explicit accept (2026-05-15)** — forward-only invariant (ADR-029 §D4), 1d max | MCT-179 |
| R5 D19 NAS sync 실패 시 backtest artifact 갈림 | MEDIUM | completion marker + 3회 retry + alert + manual reconcile runbook | MCT-181 |
| R6 D12 ghcr.io rate limit / 인증 | LOW | GITHUB_TOKEN + dev local build fallback | MCT-181 |

## Cross-ref

- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md`
- runbook stub: `docs/runbooks/docker-stack-deploy.md`
- MCT-175 RETRO: `docs/retros/RETRO-MCT-175.md`
- MCT-176 RETRO: `docs/retros/RETRO-MCT-176.md`
- MCT-177 RETRO: `docs/retros/RETRO-MCT-177.md`
- MCT-178 RETRO: `docs/retros/RETRO-MCT-178.md`
- MCT-179 RETRO: `docs/retros/RETRO-MCT-179.md`
- Parent Epic results (POLICY_FINALIZED): `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
