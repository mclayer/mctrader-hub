---
type: story-retro
story_key: MCT-152
story_title: "Stage 2 세 번째 Story — dual-write window 운영 + IOPS during 측정 + NAS unreachable SOP 실전 가동"
epic_key: EPIC-cold-tier-nas-minio
epic_milestone: mctrader-hub#4 Epic-cold-tier-stage-2-migration
stage: 2
stage_position: third  # Stage 2 세 번째 Story
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-152.md
issue: mclayer/mctrader-hub#261
phase1_pr: mclayer/mctrader-hub#262
phase1_pr_merge_sha: 6e8b853
phase2_pr_data: mclayer/mctrader-data#44
phase2_pr_data_merge_sha: 309b123
phase2_pr_data_merged_at: 2026-05-13T02:54:57Z
phase2_pr_hub: mclayer/mctrader-hub#264
phase2_pr_hub_merge_sha: d8d9514
phase2_pr_hub_merged_at: 2026-05-13T02:51:32Z
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched: [ADR-027 (D5 amendment deferred — dual-write 실 운영 evidence 박제 후 재평가), ADR-017, ADR-009]
status: complete
sp_burned: 5
sp_total_stage_2: 36
sp_progress_stage_2: 50.0
next_story: MCT-153 (5 SP, backfill 76GB NAS MinIO cold tier 영구 이관)
codeforge_escalation: mclayer/plugin-codeforge#525 (lesson #5 후보 — scope_manifest planned_files invariant Phase 1 박제 의무)
related_retros:
  - docs/retros/RETRO-EPIC-cold-tier-nas-minio-preflight.md
  - docs/retros/RETRO-EPIC-cold-tier-stage-1-complete.md
  - docs/retros/RETRO-MCT-150.md
  - docs/retros/RETRO-MCT-151.md
fix_cycle_total: 1
fix_cycle_breakdown:
  design_review: 1  # FIX#1 semantic (1 P0 + 3 P1)
  code_review: 0
escalate_count: 0
---

# RETRO — MCT-152: Stage 2 세 번째 Story (dual-write window 운영 + IOPS during 측정 + NAS unreachable SOP)

## 1. Stage 2 세 번째 Story 위치 박제

EPIC-cold-tier-nas-minio Stage 2 의 **세 번째 단계, 운영 layer owner**. MCT-150 (uploader hardening + SOP primitive) + MCT-151 (dual-write atomic primitives + 7종 invariant harness) 위에서 spawn — **dual-write window 운영 cron layer** 박제.

**핵심 산출물**:
- mctrader-data: 신규 2 src module + 수정 1 src module + 신규 2 test file = 총 5 파일, **22 PASS test** (2 SKIP POSIX-only)
  - `ops/dual_write_window_runner.py` (724 lines): DualWriteWindowRunner Phase A→E sequential + DualWriteWindowResult 5-enum + IOPSDelta 7-field + IOPSCollector
  - `nas_metrics/prometheus_exporters.py` (+104 lines): `emit_dual_write_window_*` 4 method (NFR-4 prefix-disjoint)
  - `tests/ops/test_dual_write_window.py` (914 lines): 16 test 함수 (P0×5 + P1×6 + §8.5×2 + P2×2 + FIX#1 F4×1)
  - `tests/ops/__init__.py`: 패키지 초기화
- mctrader-hub: 신규 1 docs file + §8.5 Impl Manifest + §12 retro = 총 3 파일
  - `docs/runbooks/nas-minio-unreachable-sop.md` (237 lines): NASUnreachableSOPRunner v1 state machine 3단계 operator runbook

## 2. 핵심 설계 결정 trail

| 결정 | 채택 | 근거 |
|---|---|---|
| DWWR module 분리 vs 단일 | **단일 module + IOPSCollector helper** | MCT-151 단일-module 성공 패턴 정합, 복잡도 최소화 |
| Prometheus metric 추가 위치 | **MCT-150 land prometheus_exporters.py 확장** | 별 exporter 신설 0, DRY 원칙 |
| evidence pack location | **mctrader-data/.tmp/evidence-pack-MCT-152.md (gitignored) + Story §10 summary** | 운영 데이터 git 오염 방지 + retro 추적 |
| cron daemon 환경 | **mctrader-data 컨테이너 내 cron daemon** | sidecar 0, 단순성 우선 |
| alert rule 신설 | **RETRO 시점 결정 deferred** | 실 운영 false positive rate 데이터 없이 threshold 결정 = speculative |

## 3. FIX Cycle 분석

### FIX#1 (design-review, 2026-05-13)

| Finding | 분류 | 내용 |
|---|---|---|
| F1 (P0) | 설계 dimensional | scope_manifest planned_files MCT-152 에 prometheus_exporters.py MODIFY 미박제 |
| F2 (P1) | 설계 semantic | NFR-3 strict less-than 미준수: cron interval 24h = drain timeout 24h → 23h로 수정 |
| F3 (P1) | 설계 semantic | status priority pseudocode 불일치: iops_gate_breached가 drift_detected override → healthy만 override로 수정 |
| F4 (P1) | 설계 semantic | test_status_priority_drift_over_iops 테스트 신설 의무 박제 |

**Pattern trail**:
- MCT-150: 5 FIX cycle (2 dimensional)
- MCT-151: 1 FIX cycle (0 dimensional) — lesson 4 효과 ✅
- MCT-152: 1 FIX cycle (1 dimensional) — planned_files 동기화 gap → lesson #5 후보

## 4. codeforge #525 Lesson #5 후보 (RETRO 시점 surface)

**Lesson #5 후보** (codeforge #525 amendment 발의 대상):

```
scope_manifest planned_files invariant:
Phase 1 author 시점 모든 산출물 manifest 박제 의무 (Phase 2 impl 시점 추가 0).
RequirementsPL §1 산출물 + §3 코드 경로 + ArchitectPL §6 디렉토리 트리 + §9 Phase 2 산출물 표
↔ scope_manifest planned_files 동기화 검증 step 추가.
```

**근거**: MCT-152 FIX#1 F1 (P0 dimensional) — ArchitectPL §6.4 에서 prometheus_exporters.py MODIFY 를 박제했으나 scope_manifest `planned_files.MCT-152.mctrader-data` 에 추가하지 않음. lesson 4 의 "API contract completeness" + "cross-module propagation" invariant 로는 파일 manifest 동기화 갭을 체계적으로 차단 불가.

**MCT-151 비교**: planned_files 갭 0 (lesson 4 효과) → MCT-152 에서 새 gap 발생 (planned_files 동기화 누락) → lesson #5 신설 필요.

## 5. ADR-027 D5 amendment 상태

| Decision | Trigger Story | Status | 근거 |
|---|---|---|---|
| D5 (NAS unreachable failure mode) | MCT-150 → deferred MCT-155 | **DEFERRED** | 본 Story MCT-152 dual-write 실 운영 데이터 (false positive rate / MANUAL_GATE 발동 빈도) 누적 후 amend 의미 있음. 운영 window 완료 후 MCT-155 retro 시 재평가. |
| D6 (7종 invariant) | MCT-151 | pending — MCT-155 retro | MCT-151 §5 amendment 정합 확인 의무 |

## 6. Stage 2 Milestone Progress (MCT-152 완료 시점)

| Metric | MCT-151 완료 | MCT-152 완료 |
|---|---|---|
| stories_complete | 2 / 6 | 3 / 6 |
| sp_burned | 13 / 36 SP | 18 / 36 SP |
| sp_progress_pct | 36.1% | **50.0%** |
| next | MCT-152 | MCT-153 (#265) |

**Stage 2 milestone 50% 달성 — 6 Story 중 3 MERGED (MCT-150 + MCT-151 + MCT-152)**

## 7. MCT-153 handoff prerequisites

| Prerequisite | 달성 조건 | 현재 상태 |
|---|---|---|
| dual-write window 운영 active | DualWriteWindowResult.status="healthy" 다중 cycle | 운영 시작 (2026-05-13), 모니터링 중 |
| IOPS during evidence | `.tmp/evidence-pack-MCT-152.md` §4 누적 | 운영 window 중 박제 중 |
| 7일 연속 healthy | EC-6 mechanism 달성 | 목표: 2026-05-20 |
| MCT-153 Issue | #265 생성 | ✅ CREATED |

MCT-153 진입 기준: DualWriteWindowResult.status="healthy" 안정 확인 후 (사용자 확인 또는 7일 연속 자동 trigger).

## 8. 운영 Evidence Pack 박제 계획

본 Story MCT-152 의 핵심 deliverable = 2-4주 운영 evidence pack 누적:

```
mctrader-data/.tmp/evidence-pack-MCT-152.md (gitignored)
├── §1 DualWriteWindowResult per-day report (drift / healthy / IOPS delta)
├── §2 IOPS during 측정값 (MCT-148 T2 baseline 2870.65ms ±15%)
├── §3 7종 invariant ALL PASS 연속 기록
└── §4 SOP Trigger Log (threshold breached + recovery time + MANUAL_GATE 발동)
```

이 evidence pack 이 MCT-155 retro 시점 ADR-027 D5 amendment evidence-rich source 의 직접 input.

---

**RETRO 완료** (PMOAgent, 2026-05-13)
MCT-153 Issue #265 CREATED — Stage 2 Phase C 순차 진행 (backfill 76GB 진입 prerequisite 모니터링 중).
