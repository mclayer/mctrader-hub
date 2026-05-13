---
type: story-retro
story_key: MCT-153
story_title: "Stage 2 네 번째 Story — backfill 76GB closed-day per-(symbol,day) chunking + 10-symbol 병렬 + node=DEFAULT"
epic_key: EPIC-cold-tier-nas-minio
epic_milestone: mctrader-hub#4 Epic-cold-tier-stage-2-migration
stage: 2
stage_position: fourth  # Stage 2 네 번째 Story
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-153.md
issue: mclayer/mctrader-hub#265
phase1_pr: mclayer/mctrader-hub#266
phase1_pr_merge_sha: 0b68b3d
phase2_pr_data: mclayer/mctrader-data#45
phase2_pr_data_merge_sha: 8cbbdd04
phase2_pr_data_merged_at: 2026-05-13
phase2_pr_hub: mclayer/mctrader-hub#268
phase2_pr_hub_merge_sha: 61cfc649
phase2_pr_hub_merged_at: 2026-05-13
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched: [ADR-027 (D4 step 2 owner — historic backfill), ADR-009 (S6 node=DEFAULT enforcement), ADR-017 (hot path 무영향 closed-day scope)]
status: complete
sp_burned: 8
sp_total_stage_2: 36
sp_progress_stage_2: 72.2
next_story: MCT-154 (reader endpoint cutover + dual-write 7d 연장 + engine smoke)
codeforge_escalation: mclayer/plugin-codeforge#525 (lesson #5 sub-invariant 후보 — cross-section quantitative consistency)
related_retros:
  - docs/retros/RETRO-EPIC-cold-tier-nas-minio-preflight.md
  - docs/retros/RETRO-EPIC-cold-tier-stage-1-complete.md
  - docs/retros/RETRO-MCT-150.md
  - docs/retros/RETRO-MCT-151.md
  - docs/retros/RETRO-MCT-152.md
fix_cycle_total: 1
fix_cycle_breakdown:
  design_review: 1  # FIX#1 dimensional + mechanical (§5.2 NFR-3 estimate + §7.4.4 rate-limit + scope_manifest stale comment)
  code_review: 0    # lesson 4+1 invariants 사전 박제 효과 — 0 FIX cycle (MCT-151 0 + MCT-152 0 패턴 연속 ✅)
escalate_count: 0
---

# RETRO — MCT-153: Stage 2 네 번째 Story (backfill 76GB 영구 이관 + resumability chaos)

## 1. Stage 2 네 번째 Story 위치 박제

EPIC-cold-tier-nas-minio Stage 2 의 **네 번째 단계, Phase C backfill 단독 owner**. MCT-150 (NASUploader + RetryQueue + SOPRunner) + MCT-151 (InvariantHarness 7종 + dual-write primitives) + MCT-152 (dual_write_window_runner cron + IOPS evidence) 위에서 spawn — **historic 76GB cold L2 영구 이관 orchestrator** 박제.

**핵심 산출물**:
- mctrader-data: 신규 5 파일 + 수정 1 파일 = 총 7 파일, **26 PASS test**
  - `nas_migration/backfill_orchestrator.py` (+926L): BackfillOrchestrator Phase A→E + BackfillCheckpoint sqlite-WAL
    S1 closed-day filter / S6 node=DEFAULT enforcement / S7 ThreadPoolExecutor(10) / AC-4 7종 verify / AC-5 resumability
  - `scripts/migration/run_backfill.py` (+386L): click CLI --dry-run/--execute/--resume-from, exit codes 0/2/3/4/5
  - `scripts/__init__.py` + `scripts/migration/__init__.py`: 패키지 marker
  - `nas_metrics/prometheus_exporters.py` (+148L): emit_backfill_* 6종 method (nas_backfill_* prefix, NFR-4)
  - `tests/nas_migration/test_backfill_orchestrator.py` (+663L): 22 test (P0×7 + P1×7 + §8.5×3 + P2×5)
  - `tests/nas_migration/test_backfill_resumability_chaos.py` (+423L): 4 chaos test (AC-5 50%→100% + RPO=0)
- mctrader-hub: §8.5 Impl Manifest 추가

**품질 게이트**: pytest 26/26 PASS / ruff ALL PASS / mypy 0 errors

## 2. 핵심 설계 결정 trail

| 결정 | 채택 | 근거 |
|---|---|---|
| chunking mechanism | **single partition = 1 chunk** | chunk size aggregate (50MB target) 거부 — per-partition idempotency 정합, invariant 범위 보존 |
| parallelism mechanism | **ThreadPoolExecutor(10)** | asyncio 거부 — boto3 sync API + threading.Lock 정합, GIL boto3 native |
| resumability checkpoint | **sqlite-WAL persistent** | NAS bucket listing (external dependency) + in-memory (chaos 부적합) 거부 — MCT-150 RetryQueue 패턴 정합 |
| rollback vs quarantine | **quarantine retain (NAS object DELETE 0)** | rollback DELETE 거부 — RPO=0 보존 + root cause 분석 가능 경로 보존 (§6.1 chief decision) |
| Prometheus metric 추가 위치 | **MCT-150 land prometheus_exporters.py 확장** | 별 exporter 신설 0, 기존 PrometheusExporter pattern 정합 |
| scope_manifest sync | **옵션 A (사전 박제)** | lesson #5 후보 첫 적용 — DesignReview FIX 회피 효과 입증 (file-level ✅ / cross-section 새 gap 발생) |
| evidence pack location | **별 file + Story §10 summary** | MCT-148 + MCT-152 패턴 정합 (gitignored) |
| CLI 환경 분리 | **mctrader-data 컨테이너 내 CLI 실행** | sidecar 0, 단순성 우선 |

## 3. FIX Cycle 분석

### FIX#1 (design-review, 2026-05-13)

| Finding | 분류 | 내용 |
|---|---|---|
| F1 (P1) | 설계 dimensional | §5.2 NFR-3 + §5.1 AC-2 chunk count estimate 정정 (1520 chunk → 76,000 chunk, ~7분 → ~42-67분) |
| F2 (P1) | 설계 semantic | §7.4.4 rate-limit 정량값 정정 (~36 PUT/sec → ~19-30 PUT/sec, NFR-3 gate ~80분 / ~120분 재평가 표면화) |
| F3 (P2) | mechanical | scope_manifest line 429 stale comment 정정 (5 SP → 8 SP) |

**code-review FIX 0건** — lesson 4+1 invariants 사전 박제 효과 연속 입증 (MCT-151 code-review 0 → MCT-152 code-review 0 → MCT-153 code-review 0, **3 Story 연속 code-review FIX 0**).

**Pattern trail**:
- MCT-150: 5 FIX cycle (design 2 + code 3)
- MCT-151: 1 FIX cycle (design 1 + code 0) — lesson 4 효과 ✅
- MCT-152: 1 FIX cycle (design 1 + code 0) — lesson #5 후보 발의
- MCT-153: 1 FIX cycle (design 1 + code 0) — lesson #5 첫 적용 부분 효과 ✅ + sub-invariant 신규 발견

## 4. codeforge #525 Lesson #5 sub-invariant 후보 (RETRO 시점 surface)

### 4.1 Lesson #5 첫 적용 결과 평가

**file-level scope_manifest sync (옵션 A)**: ✅ 효과 입증
- RequirementsPL 시점 `prometheus_exporters.py` MODIFY 사전 박제 + `nas_migration/` prefix 갱신 → DesignReview file-level gap 0
- MCT-152 FIX#1 F1 (P0) 재발 방지 확인

**cross-section quantitative consistency**: ❌ 신규 gap 발견
- lesson #5 (file-level sync) 적용했으나 FIX#1 F1-F2 dimensional cascade 발생
- §5.1 AC-2 chunk count estimate ↔ §5.2 NFR-3 ↔ §7.4.4 rate-limit 3곳 inconsistency
- file manifest 동기화만으로 단면 간 수치 일관성 보장 불가

### 4.2 Lesson #5 sub-invariant 후보 (codeforge #525 amendment 대상)

```
cross-section quantitative consistency invariant (lesson #5 extension):
핵심 설계 수치 (chunk count / 처리 시간 / 병렬도 / rate-limit) 결정 후
cascade update 의무 — §5.1 AC ↔ §5.2 NFR ↔ §7 보안/운영 정량값 동기화.
요구: §6.1 chunking mechanism 결정 시점 cascade table 작성
      (영향 섹션 × 정량값 × 변경 전/후 표).
```

**근거**: MCT-153 FIX#1 F1-F2 — §6.1 single partition = 1 chunk 결정 후 §5.2 NFR-3 (7분 → 42-67분), §7.4.4 rate-limit (36 → 19-30 PUT/sec) 3곳 미반영 → dimensional cascade. lesson #5 (file sync)로는 file 추가/삭제 갭만 체계적 차단, section 간 수치 cascade update gap는 별 invariant 필요.

## 5. §6.8 Wording SSOT 박제 현황 (MCT-150~153 누적)

| Story | enum SSOT 신설 | 현황 |
|---|---|---|
| MCT-150 | PutResult 5종 + RetrySegmentState 4종 | 박제 완료 |
| MCT-151 | DualWriteResult 3종 + BarrierResult 3종 + InvariantResult 8종 | 박제 완료 |
| MCT-152 | DualWriteWindowResult 5종 + SOPState 3종 | 박제 완료 |
| **MCT-153** | **BackfillResult 4종 + ChunkResult 5종 + BackfillCheckpoint 5종** | **박제 완료** |

누적 enum SSOT: **40+ enum value** (4 Story 합산) — variant desync 0건 (code-review FIX 0 연속 입증).

## 6. Stage 2 Milestone Progress (MCT-153 완료 시점)

| Metric | MCT-152 완료 | MCT-153 완료 |
|---|---|---|
| stories_complete | 3 / 6 | **4 / 6** |
| sp_burned | 18 / 36 SP | **26 / 36 SP** |
| sp_progress_pct | 50.0% | **72.2%** |
| next | MCT-153 | MCT-154 (reader cutover) |

**Stage 2 72.2% 달성 — 6 Story 중 4 MERGED (MCT-150 + MCT-151 + MCT-152 + MCT-153)**

Stage 2 종료 gate 기여:
- **AC-1 76GB cold L2 NAS 이관** — 본 Story 직접 owner (orchestrator land + CLI + chaos test)
- **AC-4 7종 invariant ALL PASS** — MCT-151 + MCT-153 share owner
- **AC-5 backfill resumability** — 본 Story 직접 owner (chaos test 26/26 PASS)

## 7. MCT-154 handoff prerequisites

| Prerequisite | 달성 조건 | 현재 상태 |
|---|---|---|
| historic 76GB cold L2 이관 완료 | BackfillResult.status="all_chunks_verified" | orchestrator READY (실 운영 실행 필요) |
| 7종 invariant ALL PASS evidence | evidence-pack-MCT-153.md §3 박제 | 실 운영 실행 후 박제 |
| node=DEFAULT legacy enforcement | S6 enforcement log 확인 | orchestrator 구현 완료 |
| RPO=0 + drop 0 chaos 입증 | 26/26 PASS (4 chaos test) | ✅ PASS |
| MCT-153 Phase 2 MERGED | data#45 + hub#268 | ✅ MERGED 2026-05-13 |

**MCT-154 진입 prerequisite**: 실 운영 `python -m scripts.migration.run_backfill --tier=L2 --execute` 실행 → BackfillResult.status="all_chunks_verified" + evidence-pack 박제 후 MCT-154 Issue 생성 (사용자 trigger 또는 orchestrator 자동).

## 8. 운영 실행 계획

```
mctrader-data 컨테이너 내 실행:

# dry-run 먼저 (partition 수 + 추정 시간 확인)
docker exec mctrader-data python -m scripts.migration.run_backfill --tier=L2 --dry-run

# 실 실행 (76GB 이관, ~42-67분 예상)
docker exec mctrader-data python -m scripts.migration.run_backfill --tier=L2 --execute

# 재실행 시 (checkpoint 활용)
docker exec mctrader-data python -m scripts.migration.run_backfill --tier=L2 --execute \
  --resume-from=/data/.tmp/backfill_checkpoint.sqlite
```

**환경변수 필요**: `NAS_MINIO_ENDPOINT` + `NAS_MINIO_ACCESS_KEY` + `NAS_MINIO_SECRET_KEY` + `NAS_MINIO_BUCKET`

---

**RETRO 완료** (PMOAgent, 2026-05-13)
MCT-154 Issue 생성 대기 (실 운영 실행 결과 확인 후). Stage 2 72.2% = 6 Story 중 4 MERGED.
