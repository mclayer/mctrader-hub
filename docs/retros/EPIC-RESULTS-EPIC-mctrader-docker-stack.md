---
type: epic-results
epic_key: EPIC-mctrader-docker-stack
epic_title: "mctrader Docker stack 확장 — collector + paper-engine + backtest profile + observability + WAL measurement"
status: IN_PROGRESS
created_at: 2026-05-15
total_stories: 7
completed_stories: 2
in_progress_stories: 0
reserved_stories: 5
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
---

# EPIC-RESULTS — EPIC-mctrader-docker-stack (IN_PROGRESS, milestone 2/7)

> **Epic**: mctrader Docker stack 확장 — collector + paper-engine + backtest profile + observability + WAL measurement
> **Status**: **IN_PROGRESS** (milestone 2/7 박제, 2026-05-15 MCT-175 + MCT-176 LAND)
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
| MCT-177 | paper-engine daemon + SIGTERM graceful + universe override + Redis prefix | - | 3 | - | - | PLANNED |
| MCT-178 | backtest-runner profile + oneshot + compose config CI lint + universe override | - | 4 | - | - | PLANNED |
| MCT-179 | observability + WAL 30G production measurement + DR mode integration + alert rule | - | 5 | - | - | PLANNED |
| MCT-180 | integration smoke + testcontainers + resource limits + capacity alert rule | - | 6 | - | - | PLANNED |
| MCT-181 | image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED 박제 | - | 7 | - | - | PLANNED |
| **합계** | | **10 (2/7)** | | | | |

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

## Epic close gate

| # | gate | 상태 |
|---|------|------|
| 1 | MCT-175 PR MERGED + ADR-030 publish + compose base + dev/prod profile LAND | ✓ (2026-05-15, hub#326 + hub#327 + hub#328) |
| 2 | MCT-176 PR MERGED + collector container + NAS credential rotation | ✓ (2026-05-15, hub#330 + data#64 + hub#331 + hub Phase 2 PR2) |
| 3 | MCT-177 PR MERGED + paper-engine daemon + SIGTERM graceful | PENDING |
| 4 | MCT-178 PR MERGED + backtest profile + compose config CI gate | PENDING |
| 5 | MCT-179 PR MERGED + WAL 30G production measurement (R2 CRITICAL 해소) + observability | PENDING |
| 6 | MCT-180 PR MERGED + integration smoke + resource limits + alert rule | PENDING |
| 7 | MCT-181 PR MERGED + Epic POLICY_FINALIZED 박제 + image registry pin + backtest artifact NAS sync | PENDING |

## Cross-Epic carry over

- **EPIC-tier-promotion-single-source Epic CLOSED 박제 prereq prod-2**: WAL 30G production measurement = 본 Epic 의 MCT-179 책임. peak market open 09:00 KST burst window 측정 + 30G 초과 시 D11 hard_limit amendment 발의 (D8-7=A FAIL gate)
- **EPIC-tier-promotion-single-source D8 sunset 14d window (2026-08-18 ~ 2026-09-01)**: MCT-179 telemetry watcher alert rule 정합

## Risk 현황 (Epic 전체)

| Risk | Severity | 상태 | Owner |
|------|----------|------|-------|
| R1 NAS HTTP-only 평문 통신 | HIGH | **사용자 explicit accept (2026-05-15)** — MCT-155 TLS cutover 별 Story 백로그 | MCT-176 |
| R2 WAL 30G 미측정 | CRITICAL | MCT-179 peak 09:00 KST 1h burst 측정 의무 (EPIC-tier-promotion CLOSED prereq) | MCT-179 |
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
- Parent Epic results (POLICY_FINALIZED): `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
