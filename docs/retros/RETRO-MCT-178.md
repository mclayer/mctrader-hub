---
type: story-retro
story_key: MCT-178
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 4
---

# RETRO — MCT-178 EPIC-mctrader-docker-stack Story-4 (backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis migration)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-4 (sequential_phase 4)** — MCT-177 LAND (paper-engine daemon) 위에 두 번째 engine service `backtest-runner` 를 oneshot profile 로 추가하고, compose config CI lint workflow (`compose-validate.yml`) 를 신규 박제. 동시에 MCT-177 carry over 1건 — signal-collector 5 worker Redis key prefix code migration (unprefixed → `signal:*` rename + 1주일 dual write + Prometheus Gauge) 을 통합 처리. ADR-030 §D2 (backtest-runner) + §D16 (compose config CI lint, 신규) amendment box VERIFIED 박제 + §D15 cross-ref carry over 이행 완료.

3 PR cross-repo sequential LAND (hub Phase 1 docs + signal-collector Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). **첫 mctrader-signal-collector repo PR (#1)** — 6번째 cross-repo 대상 repo 데뷔. DesignReview iter 1 **CONDITIONAL_PASS** — ADR-030 자기모순 누적 (MCT-175 LAND 시 D11/D16 swap 박제 + §D2 본문/amendment box profiles 불일치) fast-fix (ba87b3c). MCT-175~177 design P0 연속 감소 기록 (P0×1→P0×1→P0×0) 단절 — 단 원인은 정책 문서 누적 drift (Story §6.5 부재 아님).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D2/§D16 amend + CLAUDE.md) | mctrader-hub#336 MERGED (0d56730, 2026-05-15T10:20:05Z) |
| Phase 2 PR1 (signal-collector code: 5 worker Publisher 계층 Redis prefix dual write + Gauge, land_order 1) | mctrader-signal-collector#1 MERGED (60787c4, 2026-05-15T10:35:04Z) |
| Phase 2 PR1 (hub code: backtest-runner service + compose-validate.yml, land_order 2) | mctrader-hub#337 MERGED (bd9baf2, 2026-05-15T10:35:55Z) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 ~ AC-5) |
| 총 INV | 4/4 박제 (forward-only + backtest stateless oneshot + Redis dual write idempotent + INV-5 1주일 grace) |
| 산출물 | hub Phase 1 docs (Story + ADR-030 + CLAUDE.md + plan) + signal-collector Phase 2 PR1 (5 worker + test) + hub Phase 2 PR1 (compose.yml + workflow) + hub 박제 (6 file) |
| FIX 루프 | **1 iter** (design iter 1 = CONDITIONAL_PASS F-001/F-002 fast-fix ba87b3c + code iter 1 = PASS 양 PR) |
| ADR-030 amendment | §D2 + §D16 VERIFIED 박제 (Phase 2 PR2) + §D15 cross-ref carry over 이행 완료 |
| Epic milestone | **4/7** (MCT-175 + MCT-176 + MCT-177 + MCT-178 COMPLETED) |
| MCT-177 carry over 처리 | 1/1 (signal-collector 5종 Redis prefix code migration — Publisher 계층 집중) |
| MCT-181 carry over | `${IMAGE_TAG}` prod pin (D12, dev=latest 현행 유지) |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#336, 0d56730)

- `docs/stories/MCT-178.md` — Story §1-§12 신규 (Story file, §6.5 §7/§11 N/A 4 entry 사전 박제)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D2 (backtest-runner) + §D16 (compose config CI lint, 신규) amendment box 본문 박제 (Phase 1) + F-001/F-002 reconciliation note
- `CLAUDE.md` — Docker stack 섹션 MCT-178 IN_PROGRESS 섹션 추가 (sequential_phase 4 entry)
- `docs/superpowers/plans/2026-05-15-mct-178-backtest-runner.md` — 신규 (Phase 1 + Phase 2 PR1 + Phase 2 PR2 plan)

### 1.2 Phase 2 PR1 — signal-collector (mctrader-signal-collector#1, 60787c4, land_order 1)

- 5 worker (fear_greed / ecos / kimchi / announcement / coinglass) — **Publisher 계층 집중** `signal:*` prefix + legacy unprefixed dual write + Prometheus `redis_key_migration_dual_write_active` Gauge=1
- `tests/test_redis_prefix_migration.py` — CO-1 dual write 4 test (양방 SET / Gauge active / legacy==prefixed / env disable)

### 1.3 Phase 2 PR1 — hub (mctrader-hub#337, bd9baf2, land_order 2)

- `compose.yml` MODIFY — D2 `backtest-runner` service 신규 (image: ghcr.io/mclayer/mctrader-engine:latest + `profiles: ["oneshot"]` + `command: ["backtest","--help"]` + `restart: "no"` + volumes mctrader_engine_runs + mctrader_l1:ro + no healthcheck)
- `.github/workflows/compose-validate.yml` CREATE — D16 compose config lint 3종 (dev/prod/oneshot config --quiet) + health gate (`up -d postgres redis minio --wait --wait-timeout 180` infra only + down cleanup). trigger = pull_request (paths) + workflow_dispatch

### 1.4 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-178.md` — frontmatter (story_issues 4 PR + status COMPLETED + completed_at) + §8.5 Impl Manifest confirm + §10 FIX Ledger 3 row + §10.5 Git Ops Log 4 row + §11 retro + §12 측정 PASS
- `docs/adr/ADR-030-docker-stack-governance.md` — Amendment box (MCT-178 LAND confirm) §D2/§D16 VERIFIED + §D15 cross-ref carry over 이행 + Phase 2 PR1 cross-repo LAND timeline
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-178 status COMPLETED + completed_date + prs[] + milestone 4/7 + **F-001 정정** (line 170/244)
- `CLAUDE.md` — Docker stack 7 Story chain MCT-178 COMPLETED + §MCT-178 IN_PROGRESS → COMPLETED 전면 재작성
- `docs/retros/RETRO-MCT-178.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-4 박제 (milestone 4/7)

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 backtest-runner compose oneshot (D2+D4) | ✓ PASS | `docker compose --profile oneshot config` exit 0 + backtest-runner service 정의 (profiles ["oneshot"] + restart "no" + no healthcheck). oneshot 실행 후 exit 0 → 컨테이너 종료 |
| AC-2 backtest-runner restart "no" (D4) | ✓ PASS | `restart: "no"` + oneshot 1회 실행 후 exit 0, 자동 재기동 없음 |
| AC-3 universe override (D10) | ✓ PASS | `--universe-id <id>` CLI override (MCT-177 LAND option 재사용) + 미등록 universe-id exit 1 (R-MCT-178-3 mitigation) |
| AC-4 compose-validate workflow CI (D16) | ✓ PASS | `compose-validate.yml` 3 profile lint (dev/prod/oneshot config --quiet) exit 0 + health gate (infra only, 180s budget) PASS + down cleanup |
| AC-5 signal-collector Redis dual write (carry over) | ✓ PASS | 5 worker Publisher 계층 `signal:*` prefix + legacy unprefixed dual write + Prometheus `redis_key_migration_dual_write_active` Gauge=1 |

### 2.2 INV 박제 (4/4)

| INV | 결과 |
|-----|------|
| forward-only (WAL 객체 삭제 금지) | ✓ 박제 — backtest-runner 실행 후 WAL 기존 파일 유지 (ADR-009 §D12 정합) |
| backtest stateless oneshot | ✓ 박제 — restart "no" + 1회 실행 후 exit 0 (컨테이너 재기동 없음, D4 policy) |
| Redis dual write idempotent | ✓ 박제 — legacy key + `signal:*` key 동시 존재 + 동일 value (Redis SET 덮어쓰기, SETNX 아님) |
| INV-5 dual write 1주일 grace | ✓ 박제 — LAND+7d 이전 legacy key 항상 존재. cleanup 별 PR (`scripts/redis-prefix-cleanup.sh`) |

### 2.3 Test + 회귀

| 항목 | 결과 |
|------|------|
| Phase 2 PR1 신규 test (signal-collector) | CO-1 dual write 4 test ALL PASS |
| Phase 2 PR1 신규 test (hub) | compose config parse 검증 (profiles oneshot / restart no / no healthcheck) ALL PASS |
| 회귀 (signal-collector full suite) | 회귀 0 (Publisher 계층 집중으로 worker 측 변경 최소) |
| 회귀 (hub) | compose config lint 3 profile green |
| ruff + pyright | PASS |

### 2.4 FIX 루프 (1 iter — design CONDITIONAL_PASS + code PASS 양 PR)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub docs) | **CONDITIONAL_PASS** — F-001 (scope_manifest SSOT ↔ ADR "Out of scope" 표 D11/D16 swap) + F-002 (§D2 본문 `["backtest"]` ↔ amendment box `["oneshot"]` 자기모순) | fast-fix ba87b3c — §D2/§D16 amendment box reconciliation note 박제 (scope_manifest = SSOT, oneshot = SSOT). MCT-175 LAND 누적 swap 박제 정정 |
| 1 | code (signal-collector#1) | **0 blocking (PASS)** — 5 worker Publisher 계층 dual write + Gauge contract 정합 | PASS, LAND (60787c4, land_order 1) |
| 1 | code (hub#337) | **PASS** + P2 noise 2건 (scope_manifest line ~170/244 stale, non-blocking) | PASS, LAND (bd9baf2, land_order 2). P2 noise = Phase 2 PR2 본 PR §F-001 정정 영역 carry |

design lane = MCT-175 (P0×1) → MCT-176 (P0×1) → MCT-177 (P0×0) → **MCT-178 (CONDITIONAL_PASS)**. P0×0 연속 기록 단절 — 단 §5.2 참조 (원인 = 정책 문서 누적 drift, Story §6.5 부재 아님).

## §3 risks_realized

### 3.1 R-MCT-178-1 (compose-validate workflow CI budget 초과, MEDIUM)

- **위협**: `docker compose --profile dev up -d --wait` health gate 가 3분 budget 초과 → PR CI FAIL
- **mitigation 적용**: `--wait-timeout 180` 명시 + health gate = infra only (postgres + redis + minio, 어플리케이션 service 제외) + 초과 시 compose down cleanup
- **realized**: NO — health gate infra only scope 로 budget 내 완료
- **carry over**: CI runner resource 제약 → MCT-180 testcontainers 보완

### 3.2 R-MCT-178-2 (signal-collector dual write silent fail, MEDIUM)

- **위협**: 5종 worker 중 일부 prefixed write 실패 → paper-engine `signal:*` read miss silent data hole
- **mitigation 적용**: **Publisher 계층 집중** (개별 worker 산재 SET 아닌 단일 Publisher 계층 dual write — silent fail surface 축소) + Prometheus `redis_key_migration_dual_write_active` Gauge (비활성 시 alert)
- **realized**: NO — Publisher 계층 단일 경로로 dual write contract 검증 (4 test)
- **carry over**: Redis container crash 시 양방 write 소실 = Redis AOF MCT-179 결정

### 3.3 R-MCT-178-3 (compose-validate profile 미매칭, LOW)

- **위협**: `--profile oneshot` config lint 시 backtest-runner service 부재 (profiles 설정 오류)
- **mitigation 적용**: `--profile oneshot config --quiet` lint 별도 step (AC-4) + AC-1 실 실행 verify
- **realized**: NO — F-002 reconciliation (`["backtest"]` → `["oneshot"]`) 으로 profile SSOT 일치, lint green
- **carry over**: 없음 (LOW, fully mitigated)

## §4 followups (post-Story carry over → MCT-179)

본 Story LAND 후 다음 Story (MCT-179, sequential_phase 5, observability + WAL 30G measurement) 진입 시 처리 의무:

### 4.1 Epic-level carry over (MCT-179 R2 CRITICAL 유지)

- **R2 WAL 30G production measurement**: MCT-172 R-CRITICAL carry over 유지. peak market open 09:00 KST burst window 측정 의무 (MCT-179 owner). 30G 초과 시 D11 hard_limit amendment 발의 (FAIL gate). EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 정합.

### 4.2 MCT-181 carry over (image registry pin)

- `${IMAGE_TAG}` prod pin (D12, MCT-181 owner) — 현 compose.yml backtest-runner `image: ghcr.io/mclayer/mctrader-engine:latest` (dev=latest 현행 유지). prod = `sha-<7char>` pin = MCT-181.

### 4.3 LAND+7d signal-collector legacy cleanup (별 PR)

- signal-collector 5 worker legacy unprefixed key cleanup = LAND+7d 별 PR (`scripts/redis-prefix-cleanup.sh`). 진입 gate: LAND 일시 + 7d 이후 + Prometheus `redis_key_migration_dual_write_active` Gauge=0 확인.

## §5 lessons (process learnings)

### 5.1 signal-collector Publisher 계층 집중 lesson — cross-repo Phase 0 verify 독립 의무 (MCT-170/177 §5.1 재현)

Phase 0 verify 결과 signal-collector 5 worker (fear_greed/ecos/kimchi/announcement/coinglass) 의 Redis SET 이 worker 별 개별 산재 (가설) 가 아닌 **Publisher 단일 계층** 집중 구조 확인. session prompt 표현 ("5 worker Redis key prefix migration") ≠ 코드 실상 (Publisher 계층 단일 dual write 지점).

→ migration scope = 5 worker 개별 수정 아닌 Publisher 계층 1지점 dual write + Gauge. silent fail surface 축소 (R-MCT-178-2 mitigation 강화). MCT-170 ("engine io/ 3 module MCT-154 LAND 존재 재인지 → 재구현 아닌 확장") + MCT-177 §5.1 ("data 동기 SIGTERM stub cross-repo 오적용 — engine asyncio SSOT 존재") lesson 동형 3회 재현.

**lesson**: cross-repo Story 는 각 repo 별 Phase 0 verify 독립 의무. session prompt 의 구현 표현 ("5 worker migration") 은 가설로만 수용 (memory feedback_phase0_verify_mandatory 정합). cross-repo plan 작성 시 대상 repo 의 데이터 write 계층 SSOT (Publisher / Repository / 개별 caller) 사전 grep 의무. **첫 진입 repo (signal-collector #1) 일수록 Phase 0 verify 비용 우선.**

### 5.2 design P0×0 연속 단절 — 정책 문서 누적 drift 가 §6.5 lesson 효과를 무력화

MCT-175~177 design iter 1 P0 = 1→1→0 연속 감소 (§6.5 §7/§11 N/A 사유 사전 박제 lesson 누적 효과). MCT-178 = **CONDITIONAL_PASS** 로 P0×0 연속 단절. 단 원인 ≠ Story §6.5 부재 (4 entry 사전 박제 정상 reapply). 원인 = **ADR-030 자기모순 누적 drift**:

- F-001: scope_manifest D11/D16 정의/owner (SSOT) ↔ ADR-030 "Out of scope" 표 swap — **MCT-175 LAND 시 박제된 stale** 이 4 Story 만에 surface
- F-002: §D2 본문 `profiles: ["backtest"]` (MCT-175 base body) ↔ MCT-177/178 amendment box `["oneshot"]` 자기모순

**lesson**: Story §6.5 lesson reapply 는 Story 단위 design FIX 만 차단. **누적 정책 문서 (ADR / scope_manifest) 의 SSOT drift 는 별도 차단 mechanism 필요** — Epic 진행 중 amendment box append 시 본문/SSOT 정합 cross-check 의무 (ArchitectPLAgent §3 deputy author input 통합 정합성 검수 범위). 정정 비용 = DesignReview iter 1 fast-fix (ba87b3c, 1 iter, ESCALATE 없음) + Phase 2 PR2 §F-001 scope_manifest line 170/244 정정. **lesson reapply 누적 효과는 신규 finding 만 감소, 기존 박제 stale 은 별 trigger 로 surface — Epic 중간 Story 일수록 누적 문서 audit 필요.**

### 5.3 첫 mctrader-signal-collector repo PR (#1) — 6번째 cross-repo 대상 repo 데뷔

본 Story Phase 2 PR1 = mctrader-signal-collector repo 첫 PR (#1). 기존 cross-repo 대상 = hub / data / engine / web / market 5 repo → signal-collector 6번째. 신규 repo 진입 시 점검:
- `MCTRADER_CROSS_REPO_TOKEN` secret 등록 확인 (MCT-177 CO-3 `verify_cross_repo_secret.py` 6 repo scope 에 signal-collector 포함)
- repo CI workflow 정합 (test_redis_prefix_migration.py green gate)
- worktree convention (ADR-040) — signal-collector worktree = 별 repo cleanup (hub worktree 와 분리)

**lesson**: cross-repo Epic 에서 신규 repo 데뷔 Story 는 secret/CI/worktree 3종 사전 점검 의무. MCT-177 CO-3 6 repo secret verify 가 signal-collector 데뷔 prerequisite 선제 충족 (carry over 설계의 사전 효과). 향후 신규 repo 진입 Story 는 동형 점검 reapply.

### 5.4 FIX 루프 cost — 1 iter (design CONDITIONAL fast-fix + code PASS 양 PR)

MCT-177 = 2 iter (design PASS no FIX + code 1 iter). MCT-178 = **1 iter** (design CONDITIONAL_PASS fast-fix 1회 + code PASS 양 PR, blocking 0). 원인:
- design lane = §6.5 lesson reapply 정상 (신규 finding 0) + 누적 drift F-001/F-002 만 surface → CONDITIONAL_PASS fast-fix 1회 (ESCALATE 없음)
- code lane = Publisher 계층 집중 (§5.1) 으로 signal#1 blocking 0 + hub#337 P2 noise 2 non-blocking → 1 iter PASS

MCT-177 대비 FIX iter 50% 추가 감소. lesson: Phase 0 verify (§5.1 Publisher 계층) 가 code FIX iter 0 핵심. design drift (§5.2) 는 fast-fix 로 흡수 가능 (별 FIX 루프 아님 — CONDITIONAL_PASS gate).

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#336) — §D2/§D16 amendment box 본문

- §D2: backtest-runner service block (image + profiles ["oneshot"] + command backtest + restart "no" + no healthcheck) + F-002 reconciliation note
- §D16: compose config lint 3종 + up --wait health gate (3분 budget) + F-001 reconciliation note (신규)
- §D15 cross-ref: signal-collector Redis migration = MCT-178 carry over 이행 영역

### 6.2 Phase 2 PR2 (본 PR) — §D2/§D16 VERIFIED 박제

- §D2 VERIFIED: backtest-runner service LAND (compose.yml, hub#337) + paper-engine 동일 image command 분기
- §D16 VERIFIED: `compose-validate.yml` LAND (실 파일명 정합 — NOT docker-compose-validate.yml) + 3 profile lint + health gate
- §D15 cross-ref VERIFIED: signal-collector#1 (60787c4) 5 worker Publisher 계층 carry over 이행 완료
- F-001/F-002 reconciliation 최종 정합 (scope_manifest SSOT + line 170/244 정정)

ADR-030 본문 만 박제 (Status = Accepted 유지, MCT-175 LAND 시점 박제분). MCT-179 ~ MCT-181 LAND 시 추가 D 본문 박제 의무.

## §7 다음 Story chain

**MCT-179** (observability + WAL 30G production measurement + DR mode integration + alert rule) — sequential_phase 5.

진입 prerequisite:
1. MCT-178 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. carry over: `${IMAGE_TAG}` prod pin (D12, MCT-181 owner — dev=latest 현행 유지)
3. **R2 (WAL 30G 미측정 CRITICAL) carry 유지 (MCT-179 owner)** — peak market open 09:00 KST burst window 측정 의무. EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 정합

채택 결정: D5 (Prometheus metric + WAL measurement script + amendment trigger) + D8 (앱 내장 /metrics + Grafana + alert rule) + D17 (SIGTERM graceful + startup InvariantHarness scan).

## §8 Cross-ref

- Story: `docs/stories/MCT-178.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-178-backtest-runner.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (§D2/§D16 VERIFIED 박제 + F-001/F-002 reconciliation)
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (milestone 4/7 + F-001 정정 line 170/244)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-4 박제)
- MCT-177 RETRO (§5.1 lesson 동형): `docs/retros/RETRO-MCT-177.md`
- MCT-175 RETRO (§6.5 lesson origin): `docs/retros/RETRO-MCT-175.md`
- Phase 1 PR: mctrader-hub#336 (0d56730, 2026-05-15T10:20:05Z) — Story + ADR-030 §D2/§D16 amend + CLAUDE.md
- Phase 2 PR1 (signal-collector): mctrader-signal-collector#1 (60787c4, 2026-05-15T10:35:04Z) — 5 worker Publisher 계층 Redis prefix dual write + Gauge + test (land_order 1)
- Phase 2 PR1 (hub): mctrader-hub#337 (bd9baf2, 2026-05-15T10:35:55Z) — backtest-runner service + compose-validate.yml workflow (land_order 2)
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-4 + F-001 정정)
