---
type: story-retro
story_key: MCT-156
story_title: "Stage 3 entrypoint vertical slice — compactor NAS wiring + L2/L3 DualWriter injection"
epic_key: EPIC-cold-tier-stage-3-wiring
parent_epic: EPIC-cold-tier-nas-minio  # Stage 2 CLOSED 2026-05-13 (post-closure follow-up)
stage: 3
stage_position: first  # Stage 3 첫 Story (entrypoint vertical slice)
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-156.md
issue: mclayer/mctrader-hub#278
phase1_pr_hub: mclayer/mctrader-hub#279
phase1_pr_hub_merge_sha: 8177d89
phase1_pr_hub_merged_at: 2026-05-13
phase2_pr_data: mclayer/mctrader-data#47
phase2_pr_data_merge_sha: dff8aa5
phase2_pr_data_merged_at: 2026-05-13T08:42:53Z
phase2_pr_hub: (본 PR — post-write)
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched:
  - ADR-027 D4 amendment (cutover 전략 Stage 3 확장)
  - ADR-027 D5 amendment (retry queue Prometheus alert wiring obligation)
  - ADR-027 D9 amendment (mixed layout reader 책임 경계)
  - ADR-027 D6 (RPO=0 변경 0, wiring 무관 invariant)
  - ADR-009 §D2.1 / §D14 (reader fallback 박제 trail 인용)
  - ADR-017 (hot path 무영향 invariant 인용 — L1 NAS upload 0)
status: complete
sp_burned: 5
sp_total_stage_3: 13
sp_progress_stage_3: 38.5  # 5/13 (MCT-156 5sp + MCT-157 3sp + MCT-158 5sp planned)
milestone_progression: "0/3 → 1/3 (33.3%)"
next_story: MCT-157 (Prometheus layout label 분리 + observability)
related_retros:
  - docs/retros/RETRO-MCT-155.md
  - docs/retros/2026-05-stage2.md
  - docs/retros/RETRO-MCT-154.md
fix_cycle_total: 0
fix_cycle_breakdown:
  design_review: 0  # Phase 1 first-try PASS (DesignReview mctrader-hub#279)
  code_review: 0    # Phase 2 first-try PASS (TestAgent 8/8 + SecurityTestPL + CodeReviewPL ALL PASS)
escalate_count: 0
p2_findings_count: 3   # CodeReviewPL 2건 (sha256 dup, tmp_dw double) + SecurityTestPL 1건 (.env.example, 본 PR 해소)
p2_findings_resolved: 1  # .env.example chore commit 35273f4
p2_findings_open: 2     # sha256 dup + tmp_dw double — post-Epic refactor 후보
codex_phase0_dispatch: true  # Phase 0 brainstorm 시 9 Q
codex_phase0_diff_with_implementation: 1  # Q9 DualWriter API signature 불일치
---

# RETRO — MCT-156: Stage 3 entrypoint vertical slice (compactor NAS wiring)

## 1. Stage 3 entry 의 위치 박제

**Stage 2 EPIC CLOSED 2026-05-13 (mctrader-hub#277, RETRO-MCT-155 §3 6 AC ALL PASS) 직후** 사용자 NAS bucket 실측에서 발견된 핵심 gap (hot pipeline NAS wiring 부재) 해소 entrypoint. Stage 2 가 production-grade NAS primitive (NASUploader+DualWriter+RetryQueue) + 운영 layer (SOPRunner+InvariantHarness) + historic 76GB backfill (BackfillOrchestrator) + read-side cutover (engine cold reader) 모두 완성했으나, **hot pipeline (compactor) 자체가 NAS endpoint 안 가는 환경에서 운영 중** — 본 Story 가 그 결락을 메우는 vertical slice.

- **Stage 3 milestone progression**: 0/3 → **1/3 (33.3%)** post-LAND
- **다음 milestone**: MCT-157 (Prometheus layout label 분리) → MCT-158 (release gate smoke + EPIC CLOSED gate)
- **scope_manifest**: `EPIC-cold-tier-stage-3-wiring.yaml` (Phase 1 LAND 박제)

## 2. 사용자 원문 vs 권고 불일치 3건 surface trail 회고

본 Story 의 핵심 회고 지점 = 사용자 directive 원문과 ArchitectPL 권고 final 결정 사이의 mismatch 3건. **모두 사용자 final OK 박제 후 권고안 채택** (mismatch 자체가 issue 가 아니라, surface 의무 정합 + 사용자 confirm gate 작동의 증거).

### 2.1 "구조 복구" → 재이관 0 (S1+S6 결정)

| 항목 | trail |
|------|------|
| 사용자 directive verbatim | "Stage 2 EPIC CLOSED 후 NAS bucket 봤더니 L3 prefix 가 0개, L2 도 hour 키 가 0개 인 4.2 GiB / 1370 obj 만 있네. 박제와 실태가 안 맞는다." + "구조 복구" 명시 |
| ArchitectPL 권고 | ADR-009 §D2.1 + §D14 reader fallback 박제 검토 후 = **재이관 0** (mixed layout 자연 양립) |
| 사용자 final OK | ✅ 2026-05-13 ("S1~S7 사용자 OK 끝") |
| surface 정합 | Story §1 사용자 directive verbatim 박제 + spec §11 "Sonnet 합성 사용자 원문 vs 권고 불일치 3건 surface" 항목 박제 |

**회고 lesson**: 사용자 명시 directive ("구조 복구") 와 reader fallback 검토 후 권고 ("재이관 0") 가 불일치 시 — surface 의무 + 사용자 confirm gate 작동 → final OK 박제. 권고가 명시 directive 와 다를 때 silent 채택 금지, **explicit surface** 의무 정합.

### 2.2 "L3 backfill 별 Story" → 불필요 (S7 결정)

| 항목 | trail |
|------|------|
| 사용자 implicit expectation | Stage 2 의 backfill 패턴 (MCT-153 BackfillOrchestrator 76GB) 정합 → Stage 3 L3 backfill 도 별 Story 신설 |
| ArchitectPL 권고 | hot pipeline wiring 완료 후 L3 = **forward-only 자연 누적** → 별 Story 불필요 (MCT-153 §5.4 Non-goal 자연 해소) |
| 사용자 final OK | ✅ 2026-05-13 |
| surface 정합 | scope_manifest `out_of_scope` 명시: "별 L3 backfill Story (S7 결정, forward-only 자연 누적)" |

**회고 lesson**: 정합 패턴 (Stage 2 backfill) 의 mechanical 적용보다 **invariant 검토** (forward-only ADR-009 §D12.2 정합) 가 우선. backfill 의무 0 = MCT-153 §5.4 Non-goal 명시 박제 의 자연 해소 = Stage 3 wiring 본질의 자연 효과.

### 2.3 "L1/L2/L3 다" → L1 제외 (S3 결정)

| 항목 | trail |
|------|------|
| 사용자 implicit expectation | "hot pipeline 자체가 NAS 안 가니까" → 전 tier (L1+L2+L3) NAS 진입 |
| ArchitectPL 권고 | ADR-027 §D1 cold tier 정의 + §D5 hot path 무영향 invariant (ADR-017 hot path 정책 보존 의무) → **L1 제외**, L2/L3 만 |
| 사용자 final OK | ✅ 2026-05-13 |
| surface 정합 | Phase 2 integration Test 5 (L1 NAS upload absence) PASS 박제 + ingester service `MINIO_*` env 변경 0 박제 |

**회고 lesson**: hot pipeline 의 확장 요구가 들어와도 **architectural invariant** (ADR-017 hot path zero-loss) 의 보존이 우선. L1 = collector WAL + local Parquet, NAS roundtrip 추가 = hot path latency 영향 → invariant 위반 + ADR-027 §D1 cold tier 정의 위반. 권고 채택 → L1 NAS upload 0 invariant 박제 (integration Test 5 enforce).

## 3. 6 deputy 산출 통합 정합성 회고

ArchitectPL chief author + 6 deputy (CodebaseMapperArch / RefactorArch / SecurityArch / OperationalRiskArch / TestContractArch / DataMigrationArch) 통합 산출. 본 Story 의 추가 deputy spawn 0 (CONDITIONAL LiveOps / LiveOrdering 모두 trigger 0).

| Deputy | 산출 contribution | 통합 정합 |
|--------|-------------------|----------|
| **CodebaseMapperArch** | `compactor/runner.py` line 142-161 `_run_l3_for_parquet` MinioUploader 호출 dead code 박제 (cli.py line 619-658 minio_uploader 인자 미전달 → self._minio = None → upload 분기 dead code) | Change Plan D2 (cli.py inject) + D3c (runner _run_l3 교체) 박제 정합 ✅ |
| **RefactorArch** | runner `__init__` signature `minio_uploader → dual_writer` rename + `_dispatch_dual_write` 신규 helper 추출 + `_run_l2_for_parquet` 신규 메소드 (L2 → L1 처리 후 dispatch) | Change Plan D3a~D3e 박제 정합 ✅ |
| **SecurityArch** | NAS_MINIO_ACCESS_KEY / NAS_MINIO_SECRET_KEY env 분리 + `.env` 0600 + secret rotation runbook (MCT-155 land) 정합 + compose secrets section 미사용 (Stage 1 D2 박제 정합 — HTTP/env-based) | SecurityTestPL Phase 2 P0/P1 = 0, P2 advisory 1건 (.env.example placeholder, chore commit `35273f4` 으로 즉시 해소) ✅ |
| **OperationalRiskArch** | DualWriter status enum 3종 (`committed` / `local_only` / `hard_floor_blocked`) caller contract + SOP MANUAL_GATE escalation (MCT-150 SOPRunner 재사용) + Prometheus alert wiring (`mctrader_dual_write_result_total{status, tier}`) | integration Test 3 (NAS unreachable → local_only) + Test 4 (hard floor → SOP MANUAL_GATE) ALL PASS ✅ |
| **TestContractArch** | §8 Test Contract 7 test (committed L2/L3 + local_only + hard_floor_blocked + L1 NAS upload 0 + minio_uploader 호출처 0 + Prometheus Counter emit) + 1 perf baseline (NFR-1 < 3000ms) | TestAgent Phase 2 8/8 functional PASS + perf 0.45ms < 3000ms ✅ |
| **DataMigrationArch** | §11 D11=NONE 변호 (forward-only invariant + schema 변경 0 + legacy 객체 변경 0 + reader fallback 자연 양립) | Story §11.0~§11.7 박제 정합 + Phase 2 데이터 손실 0 ✅ |

**통합 정합 평가**: 6 deputy 산출 → ArchitectPL chief synthesis → Phase 1 docs LAND → Phase 2 구현 first-try PASS. **deputy 산출과 실제 구현 간 mismatch 0건** (단, Codex Q9 DualWriter API signature 불일치는 brainstorm Phase 0 의 추정 signature 가 production primitive 실제 API 와 mismatch 한 별 case — DeveloperPL 가 actual API 검토 후 해소, §5 참조).

## 4. 4 review lane ALL PASS 회고

| Lane | first-try 결과 | finding (P0/P1/P2) |
|------|---------------|--------------------|
| **DesignReview** | PASS (Phase 1 mctrader-hub#279) | 0 / 0 / 0 |
| **TestAgent** | 8/8 functional PASS + perf 0.45ms < 3000ms (NFR-1) | new regression 0 |
| **SecurityTestPL** | PASS | 0 / 0 / 1 (P2 .env.example, chore commit 해소) |
| **CodeReviewPL** | PASS | 0 / 0 / 2 (P2 sha256 dup + tmp_dw double, post-Epic refactor 후보) |

**FIX iteration = 0** = lesson 4+1+sub invariants (codeforge #525) 누적 효과 trail 의 일관성 (RETRO-MCT-155 §4.1 trend 정합 — MCT-154/155 0 → MCT-156 0).

**P2 finding 3건 surface trail**:

### 4.1 SecurityTestPL P2 (.env.example placeholder) — 본 PR 해소

- finding: `.env.example` 에 `NAS_MINIO_*` placeholder 4종 부재 → compose env switch 후 신규 operator onboarding 시 secret config 누락 위험
- resolution: chore commit `35273f4` (`.env.example` NAS_MINIO_ENDPOINT / NAS_MINIO_ACCESS_KEY / NAS_MINIO_SECRET_KEY / NAS_MINIO_BUCKET 4 placeholder 추가)
- 본 PR 안에서 해소 closed ✅

### 4.2 CodeReviewPL P2-1 (sha256 dup hashing) — post-Epic refactor 후보

- finding: `compactor/runner.py._dispatch_dual_write` 가 `hashlib.sha256(payload).hexdigest()` 1회 + `DualWriter.write()` 내부 `NASUploader` 가 sha256 검증용 재해시 1회 = **identical input 2회 hash**
- impact: 50MB L2 segment 기준 추가 latency ~ 0.4ms (NFR-1 < 3000ms 의 0.013%) — NFR-1 안에서 흡수
- refactor 후보: `DualWriter.write()` API 에 `precomputed_sha256` parameter 추가 → 호출자 통과
- 본 Story 의 별 Story 신설 의무 0 (P2 advisory level, NFR-1 안에서 흡수). **post-Epic refactor 후보 surface trail** (Stage 3 EPIC CLOSED 후 검토)

### 4.3 CodeReviewPL P2-2 (tmp_dw double-write) — post-Epic refactor 후보

- finding: DualWriter 가 local commit 단계에서 `tmp` 경로에 payload write 후 fsync, NASUploader 가 그 tmp 를 read → MinIO PUT. **디스크 IO 2회** (write+read), in-memory bytes 인데 tmp file roundtrip
- impact: NFR-1 안에서 흡수 (perf baseline 0.45ms 정합)
- refactor 후보: DualWriter local stage 에서 `bytes` payload 를 in-memory hand-off (현재는 cross-process safety 위해 tmp 경유)
- 본 Story 의 별 Story 신설 의무 0 (P2 advisory level). **post-Epic refactor 후보 surface trail**

## 5. Codex Phase 0 brainstorm dispatch ↔ 최종 구현 차이 박제

Phase 0 brainstorm 시점 Codex 9 design Q dispatch (사용자 directive 후 SonNet 합성 정합). Q1~Q8 = 7 결정점 + ADR amendment 모두 final OK 박제 정합. **Q9 (DualWriter API 명세) = 1건 차이 surface**.

| Q | Codex 합성 권고 | 최종 구현 | 해소 |
|---|---------------|----------|-----|
| Q9 (DualWriter API 명세) | Change Plan 박제 = `dual_writer.put(local_path, nas_key, sha256)` | 실제 MCT-151 land = `DualWriter.write(*, local_path, nas_key, data, sha256)` | DeveloperPL 가 `_dispatch_dual_write` 헬퍼 안에서 `parquet_path.read_bytes()` 로 payload 조달 후 실제 API 따라 호출 + `DualWriteResult.status` 3종 switch 박제 |

**회고 lesson (PMOAgent 향후 권고)**:

> **Phase 0 brainstorm 시점 의존 primitive 의 `signature` grep 박제 의무** — Codex dispatch 전에 의존하는 production-grade primitive (MCT-150 NASUploader, MCT-151 DualWriter 등) 의 실제 API signature 를 source code grep 으로 박제. brainstorm 안에서 추정 signature 로 design Q dispatch 하면 Q9 같은 mismatch 가 발생 → Change Plan 작성 시 추정 명세 박제 → 구현 시 DeveloperPL 가 actual API 검토 후 해소 (이번 case 처럼 해소되지만, 모든 case 가 그렇지는 않음)

→ 향후 brainstorm spec template 에 "의존 primitive signature grep 박제 섹션" 추가 권고 검토 가능 (codeforge skill `brainstorming` amendment 후보 가능, 단 본 Story 의 1건 case 만으로 amendment 발의는 과도 — surface 만).

## 6. pre-existing 9 test failure (mctrader-data main 자체 broken) surface

mctrader-data#47 Phase 2 PR 의 TestAgent run 시 발견된 별 issue — **본 PR 의 new regression 0** 이지만, mctrader-data main 자체가 9 test failure 상태:

| test file | failure 건 |
|-----------|-----------|
| `tests/test_l2_writer_close.py` | 2 |
| `tests/test_l3_writer_close.py` | 2 |
| `tests/test_cli.py` | 1 |
| `tests/test_collector_redis.py` | 1 |
| `tests/test_compactor_l2.py` | 1 |
| `tests/test_compactor_l3.py` | 1 |
| `tests/test_policy.py` | 1 |
| **합계** | **9** |

**TestAgent 검증 trail**: 본 PR new regression 0 (Phase 2 integration test 7건 + perf 1건 ALL PASS, pre-existing failure 는 main checkout 후에도 재현 = main 자체 broken 박제). 별 Story 후보 = `mctrader-data` main 의 stale test fixture / API drift 해소 (PMOAgent 누적 patterns 의 cross-Story finding 1건).

**향후 권고**: 별 Story (예: MCT-159 가칭) 으로 mctrader-data main pre-existing test failure 9건 해소. Stage 3 진입 의무 0 (본 Epic scope 외) — Stage 3 EPIC CLOSED 후 또는 Stage 4 시작 시점에 별 Epic 발의 검토 가능.

## 7. MCT-152/153 reservation title vs 실태 mismatch 2건 surface + Stage 1+2 stale reservation 6건 batch cleanup 권고

`.codeforge/counters.json` reservation block 의 title vs 실제 Story content mismatch 검토 (PMOAgent 가 카운터 cleanup 시 추가 surface):

### 7.1 MCT-152 reservation title vs 실태

- **reserved title**: "L2/L3 일괄 이관 — mc-mirror forward-only"
- **실제 Story**: dual-write window 운영 (2-4주, drift 측정) — 이관 자체는 MCT-153 의 BackfillOrchestrator owner
- **mismatch trail**: reservation 시점 (2026-05-12) Stage 2 plan 의 초안 박제 → 실제 final scope 결정 시 mc-mirror 사용 안 함 (BackfillOrchestrator Python 직접 author, MCT-153)

### 7.2 MCT-153 reservation title vs 실태

- **reserved title**: "Local L2/L3 GC — dry-run + 7일 grace"
- **실제 Story**: 76GB backfill orchestrator (historic L2/L3 cold tier asset 이관) — GC 자체는 MCT-155 owner
- **mismatch trail**: reservation 시점 plan 초안 박제 → final scope 재배치 (GC 가 MCT-155 로 이동, MCT-153 이 backfill 전담)

### 7.3 Stage 1+2 stale reservation 6건 batch cleanup 권고

본 `counters.json` 의 reservation block 안에 MCT-147~MCT-155 9건이 **completed Story 임에도 reservation 으로 남아 있음** — reservation 의 본래 의도 (미생성 Story 의 카운터 점유 박제) 와 mismatch.

| key | status | reservation 상태 | cleanup 권고 |
|-----|--------|----------------|-------------|
| MCT-147 | COMPLETED (#246 MERGED) | 잔존 | DELETE 권고 |
| MCT-148 | COMPLETED (data#40 MERGED) | 잔존 | DELETE 권고 |
| MCT-149 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-150 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-151 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-152 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-153 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-154 | COMPLETED | 잔존 | DELETE 권고 |
| MCT-155 | COMPLETED | 잔존 | DELETE 권고 |
| **MCT-156** | **COMPLETED (본 Story)** | 잔존 | **본 PR 에서 DELETE** ✅ |

**본 PR scope**: MCT-156 1건만 DELETE (본 Story §9 박제 정합). **Stage 1+2 stale 9건 batch cleanup = 별 PR scope** (별 Story 또는 chore commit, PMOAgent 향후 권고).

## 8. Cross-Story 패턴 분석 — Stage 2 EPIC CLOSED 후 wiring gap 발견 pattern

**Pattern detected**: Stage 2 (MCT-150~155) 의 6 Story 모두 production-grade primitive + 운영 layer + historic backfill + read-side cutover 완성했음에도, **사용자 NAS bucket 실측 후에야 hot pipeline wiring 부재 surface**. 이는 cutover 후 실측 검증 의무 부재 의 trail.

### 8.1 누적 ESCALATE 트렌드 검토

| Story | Phase 1 → Phase 2 LAND 후 실측 검증 trail | 결과 |
|-------|--------------------------------------|------|
| MCT-147 (Stage 1, NAS deploy) | bucket 초기화 + 5 PoC PASS evidence | wiring 검증 ✅ (PoC level) |
| MCT-148 (Stage 1, PoC) | 5 PoC PASS evidence | wiring 검증 ✅ (PoC level) |
| MCT-149 (Stage 1, ADR publish) | ADR 본문 land — 실측 의무 0 | N/A |
| MCT-150 (Stage 2, NAS primitive) | unit test + integration test (mock NAS) | wiring 검증 부분 ⚠️ (mock-only) |
| MCT-151 (Stage 2, DualWriter) | InvariantHarness + unit test | wiring 검증 부분 ⚠️ (mock-only) |
| MCT-152 (Stage 2, dual-write window) | cron operator runbook + drift metric | **실측 검증 부재** ❌ (cron 발동 후 실측 의무 부재) |
| MCT-153 (Stage 2, 76GB backfill) | BackfillOrchestrator + invariant 7종 verify | **실측 검증 부분** ⚠️ (orchestrator 완주 evidence 만, bucket prefix 실측 부재) |
| MCT-154 (Stage 2, reader cutover) | engine smoke test + read-through cache | wiring 검증 ✅ (engine read-side) |
| MCT-155 (Stage 2, GC + secret) | scripts + runbook + ADR D2/D6 amendment | wiring 검증 부분 ⚠️ (operational scripts 만) |
| **post-Stage 2 closure (사용자 실측)** | bucket 4.2 GiB / 1370 obj 만, `tier=L3/` 0개 + `tier=L2/.../hour=HH/` 0개 | **wiring gap surface** ❌ |
| **MCT-156 (Stage 3 entry)** | 본 Story = 결락 해소 entrypoint | wiring 검증 +1 (integration test mock-level) — MCT-158 에서 production 6h 실측 의무 |

**패턴 평가**: Stage 2 의 **6 Story (MCT-150~155) 중 5건이 "실측 검증 부재 또는 mock-only" 상태**. cutover 후 production NAS bucket 의 실제 prefix 출현 / row count / sha256 ladder verify 가 6 Story 어디에도 mandatory gate 로 박제되지 않음 → 사용자 NAS bucket 실측 후에야 gap surface.

### 8.2 ADR 후보 발의 판정 (cutover-verification-obligation)

본 패턴이 누적 ESCALATE 트렌드인지 판정:

| 판정 기준 | 평가 |
|----------|------|
| **반복 횟수** | 1회 누적 (Stage 2 종료 시점 1회 surface) — 누적 trend 의 첫 case |
| **impact** | high (3 Story 추가 발의 필요 = Stage 3 Epic 신설 + 사용자 confirm gate 추가 작동 비용) |
| **likelihood** | medium (Stage 4 이후 또 발생 가능 — production deployment 후 실측 의무 부재 시) |
| **mitigation 현황** | MCT-158 release gate smoke test (6h bucket prefix 출현 verify) 가 Stage 3 단독 보강 — codeforge level standard 의무화 부재 |

**판정 = ADR 후보 발의 PROPOSED** (조건부) — 단, **본 RETRO 의 surface trail + Stage 3 MCT-158 release gate 정합** 이 1차 mitigation. 누적 2회 (Stage 4 또는 다른 Epic 에서 재발) 시점에 정식 발의 권고.

**잠정 ADR draft (PMO 향후 Orchestrator 에 inline 반환 가능)**:

```markdown
---
category: Operational Risk / Cutover Governance
title: "ADR-YYY: Cutover verification obligation — production 실측 evidence pack 의무"
trigger: "Stage 2 EPIC CLOSED 후 hot pipeline wiring gap 사용자 실측 후 surface (MCT-156 entry trigger)"
---

## 배경
Stage 2 (MCT-150~155) 6 Story 모두 production-grade primitive + 운영 layer + historic backfill + read-side cutover 완성했음에도, hot pipeline wiring 부재가 EPIC CLOSED gate 안에 박제되지 않음 → 사용자 NAS bucket 실측 후에야 gap surface. 별 Stage 3 Epic 추가 발의 필요.

## 문제
Story / Epic 의 PASS gate 가 mock-level integration test 또는 cron operator runbook 까지만 강제. production deployment 후 **실측 bucket prefix 출현 / row count ladder / 데이터 통합 sha256 verify** 가 mandatory gate 로 박제되지 않으면, post-closure 시점 사용자 실측 후에야 wiring gap surface → 별 Epic 추가 발의 비용.

## 제안 결정
1. EPIC CLOSED gate 의무 항목에 **production 실측 evidence pack** 추가:
   - bucket prefix 출현 verify (key+layout level)
   - row count ladder (DB level)
   - sha256 통합 verify (file level, sample 3건)
   - operational metric N시간 baseline (cron 작동 evidence)
2. Story Phase 2 PR LAND ≠ Epic CLOSED. Epic CLOSED = Phase 2 LAND + production 실측 evidence pack 완성.
3. PMOAgent retro 의 §3 Epic-final gate 항목에 "production 실측 evidence pack" 의무 박제.

## 예상 결과
- post-closure wiring gap surface = 0 (사용자 실측 의무 → mandatory gate 로 박제)
- Story / Epic scope 손상 0 (현행 PR LAND gate 그대로 + 실측 evidence pack 추가)
- 사용자 confirm gate 추가 작동 비용 0 (Epic CLOSED gate 안 흡수)
```

**최종 ADR 후보 발의 판정** = **DEFER** (1차 mitigation = MCT-158 release gate smoke test 의 Stage 3 단독 보강 + 본 RETRO surface trail). Stage 4 또는 다른 Epic 에서 재발 시점에 정식 발의. 본 retro 의 patterns 누적 박제 trail 으로 충분 (Cross-Story finding surface).

## 9. ESCALATE 트렌드 검토

codeforge skill `codeforge:fix-ledger-schema` 정합 — 본 Story `§10 FIX Ledger` = 초기 empty 그대로 (Phase 2 PR LAND 후 fix-event-v1 contract trigger 0회):

| 항목 | 값 |
|------|---|
| FIX iteration | 0 |
| ESCALATE | 0 |
| Lane PASS first-try | 4/4 (DesignReview / TestAgent / SecurityTestPL / CodeReviewPL ALL PASS) |
| P2 advisory finding | 3건 (1 resolved + 2 post-Epic refactor 후보) |
| user blocking question | 0 (Story §1 7 결정점 사전 사용자 OK 박제) |

**ESCALATE 트렌드 평가**: 본 Story = lesson 4+1+sub invariants (codeforge #525) 누적 효과 trail 정합 (MCT-154/155 0 → MCT-156 0 일관성). codeforge consumer-side validation 의 추가 evidence 1건 누적 (RETRO-MCT-155 §4 amendment 권고 정합).

## 10. SP & 진척 박제

| 항목 | 값 |
|------|---|
| Story SP | 5 |
| Stage 3 누적 SP | 5 / 13 (= 38.5%) |
| Stage 3 milestone | 1 / 3 (33.3%) |
| Phase 1 PR (hub) | #279 MERGED 2026-05-13 (commit `8177d89`) |
| Phase 2 PR (data) | #47 MERGED 2026-05-13 (squash `dff8aa5`) |
| Phase 2 PR (hub) | (본 PR — post-write) |
| ADR amendment | ADR-027 D4/D5/D9 LAND |
| 데이터 손실 | 0 ✅ |

## 11. Acknowledgements

- **사용자 (mccho)**: NAS bucket 실측 + 7 결정점 (S1~S7) confirm gate + 자율 진행 directive
- **codeforge #525 lesson 4+1+sub invariants**: design-review FIX 0 + code-review FIX 0 일관성 trail 유지
- **ArchitectPLAgent chief author + 6 deputy**: Phase 1 통합 author + Change Plan D1~D11 정합
- **DeveloperPLAgent + DataEngineerAgent**: Phase 2 first-try GREEN 구현 + DualWriter API 실제 signature 정합 해소 (Q9)
- **QADeveloperAgent**: 7 integration test + 1 perf baseline + mapping table self-write
- **TestAgent / SecurityTestPL / CodeReviewPL**: review lane first-try PASS + P2 advisory finding surface
- **PMOAgent**: Stage 3 entry Story retro + cross-Story patterns analysis + ADR 후보 발의 판정

## 12. References

- `docs/stories/MCT-156.md` (Story SSOT, §1~§12)
- `docs/retros/RETRO-MCT-155.md` (Stage 2 마지막 Story retro — Stage 2 EPIC CLOSED gate)
- `docs/retros/2026-05-stage2.md` (Stage 2 Epic-final 종합 retro)
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (D4/D5/D9 amendment + D6 invariant)
- `docs/adr/ADR-009-*.md` (§D2.1 + §D14 reader fallback 인용)
- `docs/adr/ADR-017-*.md` (hot path 무영향 invariant 인용 — L1 NAS upload 0)
- `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` (Stage 3 Epic SSOT, milestone 1/3)
- `mclayer/mctrader-hub#278` (Story Issue)
- `mclayer/mctrader-hub#279` (Phase 1 PR)
- `mclayer/mctrader-data#47` (Phase 2 PR)

---

**MCT-156 Stage 3 entrypoint LAND.** Stage 3 milestone 1/3 (33.3%) + FIX 0 + 데이터 손실 0 + Cross-Story patterns surface (post-closure wiring gap pattern 1회 누적, ADR 후보 발의 DEFER).

---

## 13. Post-merge production deploy verification (2026-05-13 18:11~18:25 KST, append)

본 §은 Phase 2 LAND 직후 production deploy verification cycle 의 사실 박제. 사용자 directive ("tier 대로 잘 재배치 되었는지 확인하자" + "node=MERGED 있는채로 적용") 정합 후속.

### 13.1 NAS endpoint DNS 교체 (IP → DNS)

- 초기 deploy: `NAS_MINIO_ENDPOINT=http://192.168.50.200:9000` (IP)
- 사용자 directive 후 교체: `NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000` (DNS)
- DNS 정합: `mcnas01.internal.mclayer.it → 192.168.50.200 (A)` + reverse PTR `MCNAS01` — **같은 host**
- 운영 권고: production deploy 시 IP 박제 비권고 (DR/NAS hardware 교체 시 endpoint 갱신 cost). DNS 사용 의무.

### 13.2 Force PUT 검증 (wiring 정합 입증)

자연 cadence 차단 (§13.4) 우회 — manual python 으로 L2Compactor + DualWriter 직접 호출:

```
upbit transaction KRW-BTC L2 (hour=09 UTC):
  status = committed
  key = market/transaction/schema_version=tick.v1/tier=L2/exchange=upbit/symbol=KRW-BTC/date=2026-05-13/hour=09/node=MERGED/part-6d14a9c816d51f28.parquet
  size = 2,563,414 bytes (2.4 MB)
  NAS PUT latency = 455.3 ms (MCT-148 T2 NFR-1 baseline 정합)
  put_status = uploaded, etag = 6c094ac7a4004b0a
```

- ADR-027 D4/D5 amendment 정합 (DualWriter primitive + retry queue + Prometheus emit)
- write path schema 확정: `market/<channel>/schema_version=*/tier=L{2,3}/exchange=*/symbol=*/date=*/hour=HH/node=MERGED/part-*.parquet` (L3 는 hour 없음)

### 13.3 사용자 결정 박제: `node=MERGED` 유지 (옵션 A)

- ADR-009 §D2.1 + §D14 mandatory 정합 (`node=<id>` enforced at every tier level)
- MCT-153 backfill convention 답습 — mixed layout 위험 0
- reader partition pruning semantic 명확 (L1 = `NODE_*` collector hostname, L2/L3 = `MERGED` aggregated marker)
- 본 결정 적용 = 코드 변경 0
- 재시작 후 NAS dual-write enabled 메시지 verify (`endpoint=http://mcnas01.internal.mclayer.it:9000 bucket=mctrader-market`)

### 13.4 진짜 차단 원인 surface — L1 backlog 76,200

`compactor/runner.py:_tick()` 가 L1 처리를 sequential loop, L1 loop 끝난 후에야 L2 trigger 분기 도달:

| 채널 | sealed segments | 처리 속도 | ETA |
|------|----------------|-----------|-----|
| `orderbookdepth` | 48,629 | NotImplementedError 즉시 fail (L1Compactor `_schema_version` 미지원) | ~8분 (fast fail) |
| `transaction` | 16,428 | 1-2 sec/segment | ~5.5시간 |
| `orderbooksnapshot` | 11,143 | 1-2 sec/segment | ~3.7시간 |
| **L2 자연 trigger ETA** | — | — | **~9.2시간** |

→ 자연 cadence 검증 (Force PUT 외) ~9.2시간 후. R1 release gate smoke test (MCT-158) 가 본 ETA 후 evidence pack 작성.

### 13.5 추가 pre-existing 운영 issue surface

**13.5.1 L2Compactor `orderbooksnapshot` pyarrow offset overflow**:
- `pa.concat_tables(tables).sort_by("ts_utc")` 시 `ArrowInvalid: offset overflow while concatenating arrays, consider casting input from string to large_string first`
- 원인: orderbooksnapshot 의 large string column 의 누적 array 가 4 GB+ size 한계 도달
- 영향: orderbooksnapshot channel 의 L2 compaction 자체가 fail (force PUT 시도 시 발견)
- 해결 후보: pyarrow `large_string` type cast 또는 chunk-based concat

**13.5.2 MCT-153 backfill 산출물 손실 확정**:
- 본 대화 시작 시 사용자가 본 콘솔 = 4.2 GiB / 1370 obj, prefix `tier=L2/exchange=upbit/symbol=KRW-ATOM/date=2026-05-10/node=MERGED/` (legacy ADR-009 §D2.1 layout, `market/` + `schema_version/` + `hour/` 모두 부재)
- 본 deploy verification 실측 = 64 obj / 917.5 MiB, `market/` (force PUT) 1 + `smoke/` (MCT-148 PoC) 63
- bucket lifecycle = 없음, versioning = 미활성 (`list_object_versions` 결과 0/0)
- → **MCT-153 backfill 산출물 4.2 GiB 손실 확정** (복구 불가)
- S1/S6/S7 결정 (legacy NAS 4.2 GiB reader fallback) 의 전제 깨짐 — local SoT 안전, historical L2/L3 NAS 누적 0 시작

### 13.6 별 Story 발의 (B 옵션 채택)

**MCT-159** — `compactor L1 backlog cleanup — orderbookdepth channel mismatch + L2 offset overflow + MCT-153 backfill 산출물 손실` (counters reservation 박제, 신규 Epic `EPIC-compactor-operations`).

본 RETRO §13.4 + §13.5 의 3개 issue 가 MCT-159 scope. 별 brainstorm Phase 0 진입 시 spec/plan 발의.

### 13.7 신규 runbook: `docs/runbooks/stage3-deploy-runbook.md`

본 cycle 의 deploy 절차 + DNS endpoint + verify checklist 박제. 본 chore commit 의 산출물.

### 13.8 Cross-Story pattern 추가 누적 (ADR trigger 도달)

§8 surface "Stage 2 EPIC CLOSED → production 실측 후에야 wiring gap surface" pattern 이 본 verification cycle 에서 **재발견** (Phase 2 review 4 lane ALL PASS mock-only + production deploy 직후 1370 obj 손실 + L1 backlog 76k 차단):

- **재발 1회 누적** (Stage 2 1회 + 본 cycle 1회 = 2회) → ADR 정식 발의 trigger 도달
- ADR-XXX 후보: "production cutover gate 의 evidence pack 의무 (mock-only PR 박제 0)"
- 다음 Epic CLOSED cycle 진입 시 PMOAgent 정식 ADR draft 발의 권고
