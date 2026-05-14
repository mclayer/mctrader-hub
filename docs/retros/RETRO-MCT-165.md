---
type: story-retro
story_key: MCT-165
story_title: "Data Accumulation Health Verification (Framework + 3 follow-up Verify 통합)"
epic_key: EPIC-data-accumulation-umbrella  # D7=C carry-over umbrella label only (scope_manifests/EPIC-*.yaml 없음)
parent_epic: null  # 본 Story 가 umbrella entrypoint
stage: framework-entrypoint  # health framework MVP + D+5 verify 통합
stage_position: entrypoint  # umbrella Story-1
phase_pair: phase1_phase2
story_file: docs/stories/MCT-165.md
issue: mclayer/mctrader-hub#289
phase1_pr_hub: mclayer/mctrader-hub#290
phase1_pr_hub_merge_sha: f948b17e41e038db7967c088b57063ee90554afe
phase1_pr_hub_merged_at: 2026-05-14T00:11:58Z
phase2_pr_data: mclayer/mctrader-data#54
phase2_pr_data_merge_sha: 251c90edf66cf52db00f29f326da4d19e1ae5002
phase2_pr_data_merged_at: 2026-05-14T01:12:09Z
phase2_pr_hub: mclayer/mctrader-hub#291
phase2_pr_hub_merge_sha: 793c3025b691976b13ed5d785c714168b6f50f11
phase2_pr_hub_merged_at: 2026-05-14T01:18:21Z
retro_author: PMOAgent
retro_date: 2026-05-14
sprint_period: "2026-05-14 ~ 2026-05-14"  # 단일일 cycle (Phase 1 spec/plan + Phase 2 framework + D+5 verify ALL LAND 2026-05-14)
adrs_touched:
  - ADR-028 (Reserved stub) — rolling baseline threshold (본문은 D+7 checkpoint 결과 의존, Phase 1 PR #290 stub 박제)
  - ADR-009 §D12 (forward-only invariant) — INV-1 정합 박제만 (변경 0)
  - ADR-017 / ADR-027 (L1/L2/L3 tiering) — 측정 대상 layer 정합 박제만 (변경 0)
status: complete  # Phase 1 PR #290 + Phase 2 data PR #54 + Phase 2 hub PR #291 ALL LAND 2026-05-14
sp_burned: 4
next_story:
  - MCT-164 (V2 trigger — upbit L1 partition 0 root cause, 예약분 counters.json)
  - D+7 checkpoint (2026-05-16 — verify-d7-2026-05-16.md 박제, ~6 GiB ±20% 5d 완전 window 재검증)
related_retros:
  - docs/retros/RETRO-MCT-160.md  # MCT-160 §11 R7 upbit L1 verify carry — V2 verdict 의 sentinel
  - docs/retros/RETRO-MCT-162.md  # 5중 차단 cycle entrypoint
  - docs/retros/RETRO-MCT-156.md  # Stage 3 wiring entrypoint
fix_cycle_total: 1  # CI ubuntu ruff lint fail (E401/E402/F401/SIM108) — mechanical P2
fix_cycle_breakdown:
  design_review: 0
  test_agent: 1   # CI ubuntu ruff lint fail (mechanical, 구현 원인) — commit 0911f30 fix
  security_test: 0
  code_review: 0  # first-try PASS
escalate_count: 0
codex_phase0_dispatch: true  # brainstorm Phase 1 시 Codex GPT-5 9 D + 3 OQ 동시 합성 (D2=B 사용자 명시 변경 외 ALL Codex 권고 답습)
inv_achieved: 5  # INV-1/2/3/4/5 모두 PASS
risk_realized:
  - R3 (Medium): storage layout 가정 차이 — plan 가정 vs 실제 NAS Hive partition 구조 불일치, Plan Task 5 Step 3 reconcile mitigation 발동
risk_not_realized:
  - R1 (High): 정적 ±20% over-fit — V1 5d FAIL but 4d 재추산 PASS (deviation 11.3%), D+7 checkpoint 의존
  - R2 (Medium): collector lag spike — lag layer ~60s SLO PASS (정상 수집)
verify_d5_results:
  v1_volume_5d: "FAIL (deviation 31.7%, 2.973 GiB vs 4.35 GiB expected)"
  v1_volume_4d_reestimate: "PASS (deviation 11.3%, 3.35 GiB ±20% 재추산 기준)"
  v2_upbit_l1: "잔존 YES — MCT-164 trigger (별 root cause Story)"
  v3_per_sym: "PASS (50 sym × 4d, median 35.04 MiB, gap=0, lag ~60s)"
adr_proposal: null  # 본 Story 가 새 ADR 발의 trigger 아님 (ADR-028 stub 은 Phase 1 PR 박제, 본문은 D+7 결과 의존)
---

# RETRO — MCT-165: Data Accumulation Health Verification (Framework + 3 follow-up Verify 통합)

기간: 2026-05-14 ~ 2026-05-14 (단일일 cycle)
범위: 1 Story (MCT-165) + 3 PR (mctrader-hub#290 Phase 1 + mctrader-data#54 Phase 2 + mctrader-hub#291 Phase 2 hub) + 1 framework module (health/) + 1 D+5 verify evidence file + 1 신규 follow-up Story 예약 (MCT-164)
선행 retro: [RETRO-MCT-160.md](RETRO-MCT-160.md) (V2 upbit L1 verify carry-over sentinel)

---

## §1 결과 (closure)

### 1.1 commit·PR

| Story / 작업 | PR | merge commit | merged_at | 비고 |
|---|---|---|---|---|
| MCT-165 Phase 1 (hub docs) | mclayer/mctrader-hub#290 | f948b17 | 2026-05-14T00:11:58Z | spec + plan + Story §1-§7 + ADR-028 Reserved stub + domain-knowledge README + counters reservation (+1284/-2) |
| MCT-165 Phase 2 (mctrader-data impl) | mclayer/mctrader-data#54 | 251c90e | 2026-05-14T01:12:09Z | health/ module (volume/gap/file_count/lag) + CLI `health-check` subcommand + 24 tests + CLAUDE.md §health (+1401/-25) |
| MCT-165 Phase 2 hub (verify + Story §8-§12) | mclayer/mctrader-hub#291 | 793c302 | 2026-05-14T01:18:21Z | D+5 verify-d5-2026-05-14.md 박제 + Story §8 Test Contract + §9 Operational Risk + §10 FIX Ledger + §11 INV cross-ref + §12 PMO Retro placeholder + CLAUDE.md §데이터 헬스 프레임워크 (+335/-3) |
| Post-merge frontmatter 박제 | (direct commit) | 3ae5a12 | 2026-05-14 | Story `completed_at: "2026-05-14"` 박제 — Phase 1+2 ALL MERGED |
| **MCT-165 PMO Retro** (본 RETRO PR) | (direct commit to main) | TBD | 2026-05-14 | RETRO file + Story §12 4-field schema + Issue #289 gate:retro-complete label |

### 1.2 lint·invariant 상태

| 항목 | Status | 비고 |
|---|---|---|
| INV-1 (forward-only read-only fs walk) | PASS | rglob/stat only, write 0 |
| INV-2 (cut-in 2026-05-09) | PASS | start_date default 박제 + 테스트 검증 |
| INV-3 (4 layer freeze) | PASS | volume/gap/file_count/lag 4개만, parity/schema/presence 추가 0 |
| INV-4 (exit code contract) | PASS | 0=PASS, 1=FAIL, 2=tool error — integration test 검증 |
| INV-5 (박제 경로 단일) | PASS | docs/domain-knowledge/domain/data-health/ 단일 위치 |
| CI windows-latest pytest | PASS | 24 new tests + regression PASS (mctrader-data#54) |
| CI ubuntu-latest ruff lint (initial) | FAIL → PASS | F1 — E401/E402/F401/SIM108, mechanical P2, fix commit 0911f30 |
| CodeReviewPL first-try | PASS | 0 finding (FIX iteration 0 from review lane) |
| SecurityTestPL | PASS | P0=0 / P1=0 (read-only fs walk, no credential surface) |
| DesignReviewPL Phase 1 | PASS | spec/plan/Story §1-§7 + ADR-028 stub 정합 first-try |

### 1.3 INV 달성 표

5/5 INV ALL PASS. Phase 2 impl 단계에서 R3 (storage layout 가정 차이) 실현 — Plan Task 5 Step 3 의 명시적 reconcile step mitigation 이 발동되어 INV 회귀 없이 closure 달성. 실제 NAS Hive partition layout (`market/<channel>/schema_version=*/tier=*/exchange=*/symbol=*/date=*/[hour=*/][node=*/]part-*.parquet`) 답습 후 volume/gap/file_count/lag 4 layer 모두 실제 layout 기준으로 재작성 완료.

---

## §2 무엇이 잘 갔나 (kept)

### 2.1 Codex GPT-5 + Sonnet 합성 정확성 — 9 D + 3 OQ ALL first-try 답습

본 Story brainstorm Phase 1 의 가장 강력한 evidence = **9 D + 3 OQ 합성의 high accuracy** (사용자 D2=B 1 Story 통합 명시 변경 1건 외 Codex 권고 ALL 답습, 4 review lane first-try PASS 3/4 + ruff lint 1 mechanical FIX).

- **brainstorm Phase 1 trigger**: 2026-05-14 (MCT-160 R7 upbit L1 verify carry-over + MCT-103 50-sym universe LAND 후 부피 추산 검증 의무 surface 시점)
- **9 D 결정**: D1 (motivation=B 운영화 framework) / D2 (Story 분해=**B 1 Story 통합, 사용자 명시 변경**) / D3 (timing=A 즉시 D+5/D+7) / D4 (4 layer MVP=C volume/gap/file_count/lag) / D5 (threshold=C 정적 ±20% + ADR-028 Reserved stub) / D6 (산출물=B CLI + CSV/JSON + markdown) / D7 (Epic=C umbrella carry-over only) / D8 (boundary crossing=A 2026-05-09 cut-in) / D9 (domain-knowledge=A 신규 페이지)
- **3 OQ Resolution**: OQ-1 (mctrader-data CLI subcommand 선택 — data 도메인 응집도), OQ-2 (V2 narrow 정의 — `expected > 0 ∧ actual = 0`), OQ-3 (ADR-028 stub placeholder)
- **4 review lane 결과**: DesignReviewPL PASS first-try + TestAgent (CI windows PASS / CI ubuntu ruff F1 mechanical fix) + SecurityTestPL PASS + CodeReviewPL first-try PASS = **결정점 자체의 mis-decision 0**

### 2.2 R3 (storage layout 차이) Plan mitigation 발동 성공

Phase 1 plan 단계에 명시한 **Plan Task 5 Step 3 reconcile step** (mctrader_data.path 확인 의무) 이 실제로 발동. Phase 2 구현 진입 직후 가정 (`<root>/<symbol>/<date>/`) 과 실제 Hive layout (`market/<channel>/schema_version=*/tier=*/exchange=*/symbol=*/date=*/...`) 차이 surface 즉시 reconcile → volume/gap/file_count/lag 4 layer ALL 실제 layout 기준 재작성. **R3 risk pre-emption 의 정확성 박제** — brainstorm 단계 risk identification → plan mitigation 명시 → impl 단계 자동 발동 의 3 step trail.

### 2.3 1 Story 통합 결정 (D2=B 사용자 명시) 의 통합 효율

원 Codex 권고 = 분해 (framework Story + 3 verify Story = 4 Story). 사용자 명시 변경 = **1 Story 통합** (D2=B). 결과:

- **wall-clock 단축**: 4 Story 분해 시 ≥ 4 PR pair (Phase 1+2) = ≥ 8 PR + 4 retro = 1 daily cycle 초과 wall-clock. 1 Story 통합 = 3 PR (#290 + #54 + #291) + 1 retro **단일일 cycle 내 ALL LAND**
- **검증 누락 회피**: 산분된 verify 를 framework + verify 묶음으로 통합 → 4-layer 측정값과 V1/V2/V3 verdict 가 동일 framework 산출물에서 박제, 도구 drift 회피
- **D+7 checkpoint follow-up 깔끔**: 본 Story = framework + D+5 박제 closure, D+7 checkpoint = 단일 verify-d7 file commit + EPIC-RESULTS 갱신 (별 Story 의무 0)

### 2.4 4-layer MVP scope 결정 (D4=C) 의 minimal change discipline

7 layer (volume/gap/file_count/lag + parity/schema/presence) → **4 layer MVP (volume/gap/file_count/lag)** 결정. parity/schema/presence 는 후속 ADR 발의 후 진입 (INV-3 freeze 명시). 본 Story Phase 2 wall-clock 안전 + 후속 layer 의 SSOT 정합 박제 (parity 진입 시 별 ADR + Story).

### 2.5 Phase 1 docs-only PR + Phase 2 cross-repo PR 분리의 effectiveness

Phase 1 PR (#290, hub docs-only) = spec + plan + Story 골격 + ADR-028 Reserved stub + domain-knowledge README + counters reservation 만 = **DesignReview first-try PASS** (security/test gate 회피). Phase 2 cross-repo (mctrader-data#54 impl + mctrader-hub#291 evidence 박제) = 분리 evidence 박제. Phase 2 hub PR 이 framework impl 직후 D+5 evidence 박제만 담당 = **measurement evidence와 impl 분리의 깔끔한 정합**.

---

## §3 무엇이 막혔나 (problem)

### 3.1 V1 5d expected (4.35 GiB) 의 boundary crossing 미고려 — 4d 재추산 의무 surface

원 expected = `5d × ~870 MiB/day = 4.35 GiB` 추산은 5d 완전 수집 가정. 실측 결과:

- **2026-05-09 (cut-in 당일)**: 0 MiB (파티션 미수집)
- **2026-05-10 ~ 2026-05-13**: 4d × ~760-910 MiB = 2.973 GiB
- **5d 기준 deviation**: 31.7% → **FAIL**
- **4d 재추산 expected** = `4 × 860 MiB ≈ 3.35 GiB ±20% = [2.68, 4.02] GiB`, deviation 11.3% → **PASS (4d 기준)**

**문제 본질**: D8 boundary crossing 결정 (2026-05-09 이후 cut-in 정합) 은 박제했으나, **V1 expected 추산이 5d 완전 수집 가정** 으로 박제됨. INV-2 cut-in 정합 + V1 expected 보정 의 cross-validation 부재. D+7 (2026-05-16) checkpoint = 5d 완전 window 재검증으로 자연 closure, 단 D+5 만 본 framework 의 false negative trigger.

**향후 회피책**: ADR-028 본문 진입 시 rolling baseline 도입 → boundary crossing 자동 흡수. 정적 ±20% threshold 는 5d 완전 수집 기준 유지하되, framework 가 **유효 window 자동 산출** (cut-in 일자 ≤ start_date 시 자동 보정) 필요. **MCT-165 후속 ADR-028 본문 Story 의무**.

### 3.2 V2 upbit L1 잔존 YES — MCT-160 R7 carry-over 의 closure 미달성

MCT-160 §11 R7 (upbit L1 verify carry) 의 verdict = **잔존 YES** (D+5 측정 결과). upbit WAL 은 `orderbooksnapshot` 채널로 정상 수집 중 (segment-* 존재), 단 `tier=L1/exchange=upbit` 파티션 자체 미존재 — compactor 가 upbit orderbookdepth channel 을 L1 으로 승격 못 함.

**문제 본질**: MCT-160 (compactor cadence + OOM fix) LAND 후에도 upbit L1 lost 가 **자연 회복되지 않음** = D2 (compact_hour caller-explicit date) fix 만으로는 충분 조건 아님. 별 root cause 진단 의무 (MCT-164 trigger 확정).

**처리**: MCT-164 = upbit L1 partition 0 root cause 분석 (별 Story, counters.json 기존 reservation, V2 verdict 확정 → 별 세션 발의). **본 Story scope 외 — verify only 정합 박제**.

### 3.3 CI ubuntu ruff lint pre-existing main fail vs 본 PR 영향 분리 부담

본 Story F1 (CI ubuntu ruff lint fail) = **mctrader-data#54 본 PR 영향** (E401/E402/F401/SIM108 ruff rule violation, 구현 원인), fix commit 0911f30 으로 mechanical fix. 단 ubuntu-latest 의 pre-existing main fail (MCT-156 cycle 누적 박제) 와 본 PR ruff 회귀 의 surface 분리 부담은 누적 — 매 PR 에서 "본 PR 회귀 vs pre-existing fail" 분리 검증 의무.

**처리**: 본 PR 회귀 = ruff lint 1건 mechanical fix, pre-existing main fail = 별 cycle 누적 박제 (MCT-156/159/160/162/165 ALL Story 답습). main 회복 cycle 별 Story 또는 chore commit 의무는 잔여.

---

## §4 다음에 할 일 (try)

### 4.1 MCT-164 IN_PROGRESS transition (V2 verdict 확정 trigger)

- **trigger 박제**: D+5 verify V2 잔존 YES = MCT-164 (upbit L1 partition 0 root cause) 발의 trigger 충족
- **scope**: upbit WAL `orderbooksnapshot` 채널 → L1 compaction 미연결 또는 미완료 의 root cause 진단 + (필요 시) compactor channel 승격 로직 fix
- **prerequisites**: 본 RETRO LAND 후 즉시 발의 가능 (별 세션, counters.json 기존 reservation)
- **expected wall-clock**: 1-2 daily cycle (Phase 1 Story file + Phase 2 fix + verify)

### 4.2 D+7 (2026-05-16) checkpoint 실행 — ~6 GiB ±20% 정합 판정

- **trigger 박제**: D+7 (2026-05-16) 시점 = 5d 완전 window (2026-05-09 ~ 2026-05-13) + 2026-05-14 ~ 2026-05-16 추가 3d = 8d 누적 / 또는 D+7 의 5d 완전 window (2026-05-12 ~ 2026-05-16) 둘 중 측정 기준 명시
- **실행 의무**: `mctrader-data health-check --target collector --window 7d` 실행 → `verify-d7-2026-05-16.md` 박제 (single commit, 별 PR 또는 follow-up commit)
- **expected**: 5d 완전 window → ~6 GiB ±20% 정합 PASS expected (per-day ~860 MiB × 5d = 4.30 GiB 또는 ~870 × 7d = 6.09 GiB — 측정 기준 명시 시 자동 판정)
- **회귀 처리**: framework 회귀 시 issue 발의 (AC-6)

### 4.3 ADR-028 본문 진입 결정 (D+7 결과 의존)

- **trigger**: D+7 checkpoint 결과 (PASS or FAIL) → ADR-028 rolling baseline threshold 본문 진입 시점 결정
- **PASS 시**: 정적 ±20% threshold 유지 가능 가설 → ADR-028 본문 진입 시점 = 후속 universe rebalance (월 1회, MCT-103 §7 D4) 시점으로 연기 가능
- **FAIL 시**: 정적 ±20% over-fit 가설 강화 → ADR-028 본문 immediate 진입 의무 (rolling baseline 도입 후 volume threshold 재보정)
- **별 Story**: ADR-028 본문 = ArchitectAgent author dispatch 별 PR (Orchestrator dispatch, codeforge-design plugin)

### 4.4 D+30 (2026-06-08) framework follow-up commit

- **trigger 박제**: D+30 = MCT-165 framework merge + 1 month 시점 = 정적 threshold 의 operational fitness final verdict
- **실행 의무**: single commit + EPIC-RESULTS 갱신 (PR scope 외)
- **scope**: framework 자체의 회귀 검증 + 30d 누적 부피 / gap / lag 분포 박제

### 4.5 V1 expected 산출 절차 명시화 (rolling baseline 도입 전까지 단기 mitigation)

- **scope**: ADR-028 본문 진입 전까지 정적 ±20% threshold 유지 시, **유효 window 자동 산출** logic 추가 의무 (cut-in 일자 ≤ start_date 시 자동 보정)
- **위치**: `src/mctrader_data/health/thresholds.py` + `volume.py` — 측정 window 가 framework 자동 산출, expected 추산 시 cut-in 보정 적용
- **별 chore commit 또는 MCT-165 D+30 follow-up 시 합병 결정**

---

## §5 cross-Story 패턴

본 RETRO 자체로 신규 cross-Story pattern 발의 trigger 는 없음. 단 누적 패턴 박제:

### 5.1 "verify carry-over → follow-up Story trigger" 패턴 (누적 2회)

| # | carry-over Story | verify carry | verdict | follow-up Story |
|---|---|---|---|---|
| 1 | MCT-160 §11 R7 (upbit L1 partition 0) | MCT-165 V2 | **잔존 YES** | **MCT-164 trigger 확정** |
| 2 | MCT-165 D+7 checkpoint | (2026-05-16 실행 예정) | TBD | ADR-028 본문 진입 시점 결정 |

**패턴 본질**: Phase 2 LAND 후 measurement 의무 가 Story 종료 gate 가 아닌 별 Story trigger 로 carry-over 되는 정합. **`measurement carry-over → follow-up Story trigger` 패턴 자체는 ADR-045 forcing function (gate:retro-complete) 의 보완재** — measurement carry 자체가 retro completion 의 closure gate 가 되지 않도록 별 verify Story / D+N checkpoint follow-up 으로 분리.

### 5.2 "boundary crossing expected 추산의 cut-in 자동 보정 부재" 패턴 (단발)

§3.1 surface — V1 expected 가 5d 완전 수집 가정으로 박제되었으나 INV-2 cut-in 정합으로 실 유효 window = 4d. **단발 사례**, ADR-028 본문 진입 시 자동 closure (rolling baseline 도입).

---

## §6 ADR 후보 발의

본 RETRO 자체로 **신규 ADR 발의 trigger 없음**. ADR-028 (Reserved) 은 Phase 1 PR 박제 완료, 본문은 D+7 결과 의존 (§4.3 cross-link).

### 6.1 ADR-028 본문 진입 trigger 박제

- **trigger 시점**: 2026-05-16 D+7 checkpoint 결과 후
- **dispatch**: Orchestrator → ArchitectAgent direct author (codeforge-design plugin)
- **scope**: rolling baseline threshold 산출 logic + 정적 ±20% deprecation 시점 + cut-in 자동 보정 logic 통합

### 6.2 (참고) 별 RETRO 의 ADR 발의 trigger 카운트 박제

- **ADR-XXX-post-cutover-wiring-gap-prevention**: RETRO-MCT-160 §10 발의 (누적 3회) — 본 RETRO 와 무관 (Compactor stage cycle 영역)
- **ADR-028**: 본 Story Phase 1 PR 박제 (Reserved stub) — 본문 진입은 D+7 결과 의존

---

## §7 토큰 예산 vs 실제

본 Story 단일 daily cycle 박제 — 별 sprint-level 토큰 예산 비교 N/A. brainstorm Phase 1 + Phase 1 docs + Phase 2 cross-repo impl + D+5 evidence + Phase 2 hub PR 박제 ALL 단일일 cycle 내 closure (Codex GPT-5 합성 정확성 + 1 Story 통합 결정 효과 — §2.3 cross-link).

| 단계 | 박제 |
|---|---|
| brainstorm Phase 1 (Codex 9 D + 3 OQ) | 2026-05-14 cycle 초반 |
| Phase 1 PR (#290) | f948b17 LAND 2026-05-14T00:11:58Z |
| Phase 2 mctrader-data PR (#54) | 251c90e LAND 2026-05-14T01:12:09Z (F1 ruff fix 0911f30 포함) |
| D+5 verify 실행 + verify-d5-2026-05-14.md 박제 | 2026-05-14 cycle 후반 |
| Phase 2 hub PR (#291) | 793c302 LAND 2026-05-14T01:18:21Z |
| frontmatter completed_at 박제 | 3ae5a12 (post-merge direct commit) |
| **PMOAgent retro** | 본 RETRO PR (TBD direct commit to main) |

---

## §8 개선 제안 (3건)

### 1. V1 expected 추산의 cut-in 자동 보정 logic 즉시 도입 (D+7 checkpoint 이전 mitigation)

D+7 (2026-05-16) checkpoint 시점에 5d 완전 window 확보 → 정적 expected (4.35 GiB or ~6 GiB) 정합 expected. 단 framework 가 자동으로 **유효 window 산출 + expected 보정 적용** 하면 boundary crossing trigger 의 false FAIL 회피. `src/mctrader_data/health/thresholds.py` + `volume.py` 에 cut-in 자동 보정 logic 추가 (별 chore commit, 1-2 hour wall-clock). **ADR-028 본문 진입 전까지 단기 mitigation 으로 충분**.

### 2. measurement carry-over → follow-up Story trigger 의 retro template 박제

본 RETRO §5.1 의 "verify carry-over → follow-up Story trigger" 패턴이 **ADR-045 forcing function (gate:retro-complete) 와 정합** 하도록, templates/retro.md schema 에 명시 entry 추가 권고:

- `next_story` (list) — measurement carry / follow-up trigger 별 Story 후보 박제
- `verify_results` (dict) — D+N measurement 결과 verdict 박제 (PASS/FAIL/잔존 + trigger 의존)

본 RETRO frontmatter 가 이미 두 field 박제 — templates/retro.md schema PR 시 reference 로 사용 가능.

### 3. ubuntu pre-existing main fail vs 본 PR 회귀 surface 분리의 chore Story 의무

MCT-156 cycle 누적 박제 (MCT-156/159/160/162/165 ALL Story 답습) — **별 chore Story (또는 PMOAgent direct main 회복 commit)** 의무. 본 Story 와 무관 하나, 매 PR 의 ruff/lint surface 분리 부담 누적 ≥ 5 회. **chore Story 발의 권고 — 별 daily cycle 1회 분량**.

---

## 부록: 산출 파일 manifest

### Phase 1 (mctrader-hub#290, MERGED 2026-05-14T00:11:58Z, mergeCommit=f948b17, +1284/-2)

| 파일 | 변경 |
|---|---|
| `docs/superpowers/specs/2026-05-14-MCT-165-data-accumulation-health-design.md` | brainstorm Phase 1 spec 박제 (9 D + 3 OQ + R3 reconcile mitigation) |
| `docs/superpowers/plans/2026-05-14-mct-165-data-accumulation-health.md` | Phase 2 plan (Task 1-7, Task 5 Step 3 = R3 storage layout reconcile) |
| `docs/stories/MCT-165.md` (§1-§7) | Story 골격 — 9 D 결정 + 7 AC + 2 Edge + 5 INV + 3 Risk + Phase 분할 + Cross-ref |
| `docs/adr/ADR-028-rolling-baseline-threshold.md` | Reserved stub 박제 (본문 D+7 결과 의존) |
| `docs/domain-knowledge/domain/data-health/README.md` | 7-layer + forward-only detective + SLO budget |
| `.codeforge/counters.json` | MCT-164 + MCT-165 reservations, next=166 |

### Phase 2 mctrader-data (mclayer/mctrader-data#54, MERGED 2026-05-14T01:12:09Z, mergeCommit=251c90e, +1401/-25)

| 파일 | 변경 |
|---|---|
| `src/mctrader_data/health/__init__.py` | health module skeleton |
| `src/mctrader_data/health/thresholds.py` | 정적 ±20% + rolling NotImplementedError stub (AC-7) |
| `src/mctrader_data/health/volume.py` | parquet fs walk 합산 (INV-1/INV-2, R3 reconcile 답습) |
| `src/mctrader_data/health/gap.py` | missing partition detect |
| `src/mctrader_data/health/file_count.py` | parquet file count 실측 |
| `src/mctrader_data/health/lag.py` | WAL mtime lag 계산 |
| `src/mctrader_data/health/report.py` | JSON/CSV/markdown 생성 (overall_verdict) |
| `src/mctrader_data/cli.py` | `health-check` subcommand 추가 (INV-4 exit code 0/1/2) |
| `tests/unit/health/test_{thresholds,volume,gap,file_count,lag,report}.py` | 6 unit test files (21 cases) |
| `tests/integration/health/test_cli_exit_code.py` | CLI exit code contract (3 cases) |
| `.claude/_overlay/CLAUDE.md` | §health 모듈 신규 |
| (fix commit 0911f30) | F1 ruff lint fix (E401/E402/F401/SIM108) |

### Phase 2 hub (mclayer/mctrader-hub#291, MERGED 2026-05-14T01:18:21Z, mergeCommit=793c302, +335/-3)

| 파일 | 변경 |
|---|---|
| `docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md` | D+5 V1/V2/V3 evidence pack — V1 5d FAIL → 4d 재추산 PASS, V2 upbit L1 잔존 YES, V3 per-sym 분포 박제 |
| `docs/stories/MCT-165.md` §8-§12 | Test Contract (24 case) + Impl Manifest (R3 reconcile note) + Operational Risk (R1/R2/R3 실현 여부) + FIX Ledger (F1) + INV cross-ref + EPIC-RESULTS 후보 |
| `.claude/_overlay/CLAUDE.md` | §데이터 헬스 프레임워크 신규 |

### Phase 2 hub post-merge (direct commit, 3ae5a12)

| 파일 | 변경 |
|---|---|
| `docs/stories/MCT-165.md` frontmatter | `completed_at: "2026-05-14"` 박제 — Phase 1+2 ALL MERGED |

### MCT-165 PMO Retro (본 RETRO PR, TBD direct commit to main)

| 파일 | 변경 |
|---|---|
| `docs/retros/RETRO-MCT-165.md` | 본 RETRO file 신규 (PMOAgent self-write, templates/retro.md schema 정합) |
| `docs/stories/MCT-165.md` §12 | 4-field PMO Retro schema 박제 (retro_file + retro_summary + learnings_count + feedback_back_to_codeforge) |
| Issue #289 | `gate:retro-complete` label 추가 + retro completion 코멘트 |
