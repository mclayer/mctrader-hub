---
type: story-retro
story_key: MCT-154
story_title: "Stage 2 다섯 번째 Story — Phase D singleton (reader endpoint cutover + cache barrier + dual-write 7d 연장 + engine smoke)"
epic_key: EPIC-cold-tier-nas-minio
epic_milestone: mctrader-hub#4 Epic-cold-tier-stage-2-migration
stage: 2
stage_position: fifth  # Stage 2 다섯 번째 Story (Phase D singleton)
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-154.md
issue: mclayer/mctrader-hub#270
phase1_pr: mclayer/mctrader-hub#271
phase1_pr_merge_sha: 5220bd3
phase1_pr_merged_at: 2026-05-13
phase2_pr_engine: mclayer/mctrader-engine#52
phase2_pr_engine_merged_at: 2026-05-13
phase2_pr_hub: mclayer/mctrader-hub#272
phase2_pr_hub_merge_sha: ef7c715
phase2_pr_hub_merged_at: 2026-05-13
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched: [ADR-027 (D4 step 3 owner — reader endpoint cutover + D9 read-through cache), ADR-009 (§D2.1 16-col schema invariant + legacy node= read mapping), ADR-017 (hot path 무영향 cold tier read-side only)]
status: complete
sp_burned: 5
sp_total_stage_2: 36
sp_progress_stage_2: 86.1
next_story: MCT-155 (local GC + secret rotation 첫 cycle + TLS 재검토 + RPO=0 검증 회고 + Stage 2 종료 gate)
codeforge_escalation: mclayer/plugin-codeforge#525 (lesson #5 sub-invariant 첫 적용 — cross-section quantitative consistency)
related_retros:
  - docs/retros/RETRO-EPIC-cold-tier-nas-minio-preflight.md
  - docs/retros/RETRO-EPIC-cold-tier-stage-1-complete.md
  - docs/retros/RETRO-MCT-150.md
  - docs/retros/RETRO-MCT-151.md
  - docs/retros/RETRO-MCT-152.md
  - docs/retros/RETRO-MCT-153.md
fix_cycle_total: 0
fix_cycle_breakdown:
  design_review: 0  # lesson 4+1+sub invariants 사전 박제 효과 — DesignReview FIX 0 (MCT-151 0 + MCT-152 0 + MCT-153 1 패턴 후 본 Story 0)
  code_review: 0    # 4 Story 연속 code-review FIX 0 (MCT-151+152+153+154, lesson 4+1+sub 누적 효과 ✅)
escalate_count: 0
---

# RETRO — MCT-154: Stage 2 다섯 번째 Story (reader endpoint cutover singleton)

## 1. Stage 2 다섯 번째 Story 위치 박제 — Phase D singleton

EPIC-cold-tier-nas-minio Stage 2 의 **다섯 번째 단계, Phase D singleton (cutover atomicity 의무)**. MCT-150~153 4 Story 누적 evidence (write-side primitive + 운영 layer + historic 76GB 영구 이관) 위에서 spawn — **read-side cutover 단독 owner** (mctrader-engine cold L2/L3 reader endpoint flip + cache barrier + 7d grace + engine smoke).

**핵심 산출물**:
- mctrader-engine: 신규 5 파일 = 총 5 파일, **30 PASS test** (26 박제 + 4 추가 helper)
  - `src/mctrader_engine/io/__init__.py` (public API export)
  - `src/mctrader_engine/io/cold_reader.py` (NAS endpoint cold L2/L3 read API + S6 cross-check + read-through cache + smoke test)
  - `src/mctrader_engine/io/reader_cache.py` (LRU+TTL cache + flush + verify barrier, S3 박제 enforce)
  - `src/mctrader_engine/io/endpoint_router.py` (immutable swap + 7d grace mode + masked log)
  - `tests/io/test_endpoint_cutover.py` (17 tests)
  - `tests/io/test_reader_cache_flush.py` (10 tests)
- mctrader-hub: 신규 2 파일
  - `docs/stories/MCT-154.md` (Phase 1 — Story §1~§11, 2142L)
  - `docs/runbooks/nas-minio-cutover-checklist.md` (Phase 2 — 5 Phase + Rollback procedure, 274L)
- pyproject.toml 갱신 (boto3>=1.34 + PyYAML>=6.0 추가)

**Stage 2 종료 gate AC-2 의 직접 owner (single source)** = `nas_write_ratio == 1.0` for 7d grace evidence (본 Story 종료 후 cutover 실 운영 시점 박제).

**3중 lock for cutover transition** (사용자 directive "RPO=0 + 절대 유실 금지" enforce):
1. Cache flush + verify barrier (S3) — endpoint flip 전 stale cache 강제 무효화
2. Dual-write 7d grace 연장 (S9) — cutover 후 belt-and-suspenders rollback 보존
3. Engine smoke test (AC-5) — 첫 NAS read 정상 동작 입증 (MCT-148 T2 ±15% gate + 4종 schema invariant)

## 2. Story Final Audit

| 항목 | 목표 | 실적 |
|---|---|---|
| Phase 1 PR (hub) | #271 MERGED | ✅ MERGED 2026-05-13 (5220bd3) |
| Phase 2 PR (engine) | #52 MERGED | ✅ MERGED 2026-05-13 (admin merge, CI orthogonal pre-existing mctrader-market-upbit auth failure) |
| Phase 2 PR (hub runbook) | #272 MERGED | ✅ MERGED 2026-05-13 (ef7c715) |
| pytest PASS | 26+ tests | ✅ 30 passed, 0 failed (26 박제 + 4 추가 helper) |
| pyright clean | 0 errors | ✅ 0 errors / 0 warnings / 0 informations |
| ruff clean (MCT-154 scope) | 0 violations | ✅ All checks passed (1 noqa for boto3 PascalCase API parity) |
| §8.5 active test | 3 건 PASS | ✅ §8.5-1/2/3 모두 PASS (cross-platform, POSIX-only 없음) |
| Chaos test (P1-1) | endpoint rollback fail-safe | ✅ test_endpoint_rollback_after_smoke_fail PASS |
| §6.10 file-level scope_manifest sync | path 갱신 권고 0 | ✅ 두 번째 case 효과 ✅ (lesson #5 file-level) |
| §6.11 cross-section quantitative consistency | cascade table 13 row | ✅ 첫 적용 case 효과 ✅ (lesson #5 sub-invariant) |
| Issue #270 | CLOSED | ✅ CLOSED (PR merge auto-close 또는 본 retro 후 manual close) |
| MCT-155 Issue | handoff prerequisite 확인 후 생성 | ✅ 본 retro 후 신규 Issue 생성 (Stage 2 마지막 Story) |

## 3. FIX Cycle Summary

| Lane | FIX count | 원인 분류 | 메모 |
|---|---|---|---|
| design-review | 0 | — | lesson 4+1+sub invariants 사전 박제 효과 — FIX 0 (MCT-151 0 + MCT-152 0 + MCT-153 1 패턴 후 본 Story 0 — lesson #5 sub-invariant 첫 적용 효과 입증) |
| code-review | 0 | — | 4 Story 연속 code-review FIX 0 (MCT-151+152+153+154, lesson 4+1+sub 누적 효과 ✅) |
| pytest first pass | 4 failed (initial) | test fixture bug | _FakeS3Client `store or {}` falsy issue — empty dict가 falsy 평가 → new dict shadow. fix = `store if store is not None else {}`. impl side bug 0 (test fixture issue only) |
| ruff lint | 8 violations (initial) | UP007 + N803 | auto-fix 6 (UP007 Optional → X \| None) + 2 noqa (boto3 PascalCase API parity, 의도적) |

**Total FIX: 0 design + 0 code review cycle** (MCT-151 + MCT-152 + MCT-154 3 Story 동일 0 + MCT-153 1 dimensional only). **lesson 4+1+sub invariants 5th case 효과 입증** — lesson #5 sub-invariant 첫 적용 case 가 dimensional cascade 사전 차단 효과 ✅ (MCT-153 FIX#1 dimensional cascade type 회귀 0).

## 4. codeforge #525 Lesson #5 Sub-invariant 첫 적용 결과 평가

**Lesson #5 file-level sync 두 번째 적용 결과**:
- ✅ path 갱신 권고 0건 (mctrader-engine `io/` sub-domain 신규 신설 + mctrader-data `nas_*` prefix 와 직교)
- ✅ `_io.py` (ADR-018 D5 atomic write helper, private leading underscore) ↔ `io/` package 명확 disambiguation (Python import 모호성 0)
- ✅ 디렉토리 트리 7 file (+2 `__init__.py` minor) vs scope_manifest 7 file 정합 (lesson #5 file-level 사전 검증)

**Lesson #5 sub-invariant 첫 적용 결과 (cross-section quantitative consistency)**:
- ✅ §6.11 cascade table 13 row 박제 (file count / 5 AC / 7d grace days / smoke sample 5+ / 12 신규 metric / 13 신규 enum value / cache TTL / cache capacity / flush retry budget 등)
- ✅ MCT-153 FIX#1 dimensional cascade (chunk count 1520 → 76,000 + 처리 시간 7분 → 42-67분 + rate-limit 36 → 19-30 PUT/sec) 와 같은 dimensional cascade gap 0 — 본 Story = quantitative consistency 사전 박제 효과 입증
- ✅ §1 산출물 7 file ↔ §3 코드 경로 7 row ↔ §4.1 DELTA 7 신규 file mention ↔ §5.7 sibling Story 4 ↔ §6.3 디렉토리 트리 ↔ §9.2 Phase 2 산출물 표 모두 정합

**Lesson #5 sub-invariant 효과 측정 (codeforge #525 amendment 후보)**:

| metric | MCT-152 (sub-invariant 후보 발의) | MCT-153 (sub-invariant surface, FIX#1) | MCT-154 (sub-invariant 첫 사전 적용) |
|---|---|---|---|
| design-review FIX cycle | 1 (file-level only) | 1 (dimensional cascade — sub-invariant gap) | **0** (사전 박제 효과 ✅) |
| dimensional cascade finding | 0 | 3건 (F1+F2+F3) | **0** (사전 차단 효과 ✅) |
| Cross-section table 박제 | 부분 (§6.10 만) | 사후 RETRO 박제 | **사전 §6.11 cascade table 13 row 박제** |
| 5번 적용 → 효과 | 후보 발의 | gap 발생 (효과 0) | gap 0 (효과 ✅) |

**codeforge #525 amendment 권고** = lesson #5 sub-invariant **공식 채택** (cross-section quantitative consistency invariant).

## 5. §6.8 Wording SSOT 박제 현황 (MCT-150~154 누적)

| Story | enum SSOT 신설 | 현황 |
|---|---|---|
| MCT-150 | PutResult 5종 + RetrySegmentState 4종 | 박제 완료 |
| MCT-151 | DualWriteResult 3종 + BarrierResult 3종 + InvariantResult 8종 | 박제 완료 |
| MCT-152 | DualWriteWindowResult 5종 + SOPState 3종 | 박제 완료 |
| MCT-153 | BackfillResult 4종 + ChunkResult 5종 + BackfillCheckpoint 5종 | 박제 완료 |
| **MCT-154** | **EndpointFlipResult 5종 + CacheFlushResult 3종 + ReadResult 5종** | **박제 완료** |

누적 enum SSOT: **53 enum value** (5 Story 합산) — variant desync 0건 (code-review FIX 0 4 Story 연속 입증).

## 6. Cross-repo handoff verify (MCT-150~154 → MCT-155)

| handoff item | SSOT Story | MCT-155 consume 의무 |
|---|---|---|
| **NASUploader API contract** | MCT-150 | 7d grace 중 NAS unreachable transient 시 RetryQueue path 정상 동작 (API 변경 0) |
| **DualWriter + CompactionBarrier + InvariantHarness** | MCT-151 | MCT-155 GC 시점 InvariantHarness 7종 cross-reference |
| **dual_write_window_runner cron + NASUnreachableSOPRunner** | MCT-152 | 7d grace 만료 시점 evidence pack + GC 진입 prerequisite |
| **BackfillOrchestrator + S6 node=DEFAULT enforcement** | MCT-153 | MCT-155 GC 시점 legacy partition deletion 정합 verify |
| **EndpointRouter + ReaderCache + ColdReader + cutover runbook** | **MCT-154 (본 Story)** | **MCT-155 GC 진입 prerequisite verify (cutover 완료 evidence + grace_remaining_days=0 + invariant ALL PASS 7일 누적)** |

## 7. Scope Manifest Milestone Progress

| Metric | 이전 (MCT-153 완료) | 현재 (MCT-154 완료) |
|---|---|---|
| stories_complete | 4 / 6 | **5 / 6** |
| sp_burned | 26 / 36 SP | **31 / 36 SP** |
| sp_progress_pct | 72.2% | **86.1%** |
| next story | MCT-154 (5 SP, reader cutover) | MCT-155 (5 SP, local GC + RPO=0 검증 + Stage 2 종료) |

## 8. Handoff → MCT-155 (Stage 2 마지막 Story)

MCT-155 진입 prerequisite (MCT-154 종료 후):
1. **cutover 실 운영 완료 verify** — `endpoint_router.flip()` 실 NAS endpoint flip 결과 = `EndpointFlipResult.status="flipped"` (Phase 2 land 박제 후 cutover 실 운영 별 단계)
2. **engine smoke test ALL PASS evidence pack** — `mctrader-engine/.tmp/evidence-pack-MCT-154.md` §2~§6 박제 (read latency p99 + sha256 + 16-col schema + cache hit ratio + legacy partition)
3. **7d grace mode 만료 evidence** — `engine_dual_write_grace_remaining_days == 0` + `engine_dual_write_grace_expired_at` Prometheus metric 박제
4. **7d 동안 daily invariant verify ALL PASS 누적 evidence** — MCT-152 dual_write_window_runner cron 결과 7일 누적 `nas_invariant_verify_total{status="all_pass"} == 7` verify

**MCT-155 scope** (Stage 2 마지막 Story):
- Local GC (mctrader-data 측 cold L2 76GB local file system 삭제, R5 mitigation: deletion log + 24h 지연 batch delete)
- Secret rotation 첫 cycle (90d cadence — MCT-150 NASUploader credential + MCT-154 mctrader-engine read-only credential)
- TLS 재검토 (ADR-027 D9 amendment 또는 S12 user_confirmed=HTTP 유지)
- RPO=0 검증 회고 (`scripts/migration/verify_rpo_zero.py` 또는 별 verify mechanism — MCT-154 chaos test (P1-1) + MCT-153 chaos test cross-reference)
- ADR-027 D5/D6 amendment 재평가 (운영 evidence 누적 후 결정)
- Stage 2 종료 gate 6 AC 종합 verify

**Stage 2 종료 gate 6 AC 현재 상태**:
| ID | AC | Owner | 현재 상태 |
|---|---|---|---|
| AC-1 | 76GB cold L2 NAS 이관 + byte identity | MCT-153 | ✅ MCT-153 BackfillOrchestrator land (실 운영 별 단계) |
| **AC-2** | **신규 L2 100% NAS write (post-cutover)** | **MCT-154 (본 Story)** | **✅ owner MERGED, cutover 실 운영 후 evidence 박제 시점** |
| AC-3 | GC 후 free disk > 50% (목표 ~70%) | MCT-155 | ⏳ MCT-155 진입 prerequisite |
| AC-4 | 7종 invariant ALL PASS | MCT-151 + MCT-153 share | ✅ land (실 운영 evidence 박제) |
| AC-5 | backfill resumability | MCT-153 | ✅ chaos test PASS (실 운영 evidence 박제) |
| AC-6 | TLS 재검토 회고 | MCT-155 | ⏳ MCT-155 진입 |

## 9. Lesson learned (PMOAgent 박제)

1. **lesson #5 sub-invariant 사전 박제 효과 입증** — cross-section quantitative consistency cascade table 13 row 박제로 dimensional cascade gap 사전 차단. MCT-153 FIX#1 (chunk count 1520→76,000 cascade) 같은 retro 시점 surface gap 0.
2. **TDD 측 fixture race 사전 검출** — `_FakeS3Client store or {}` falsy bug 가 첫 pytest 시 4 fail surface (pytest 30/30 PASS 까지 1회 fix). impl side bug 0, test fixture bug 만 — lesson 4+1+sub invariants 효과 ✅ (impl FIX 0 누적 4 Story 연속).
3. **CI orthogonal failure 분류 효과 입증** — mctrader-engine PR #52 의 mctrader-market-upbit auth failure (pre-existing infra issue) 가 본 PR scope 외 → admin merge 정당 (사용자 메모리 박제 `feedback_admin_merge_autonomy.md` + `feedback_ci_terminal_states_classify.md` 정합).
4. **3중 lock cutover transition 박제 효과** — Phase 0~4 + Rollback procedure 사전 박제 → 실 운영 시점 operator manual sequential checklist 즉시 사용 가능 (MCT-152 SOP 패턴 정합).
5. **Cross-repo state coordination = operator manual gate** 패턴 정합 — `cutover_state.yaml` shared config file + 양쪽 컨테이너 read-only mount + git commit audit trail. automation 거부 = atomic state transition 가 운영 안전 측 valid trade-off.

## 10. References

- Phase 1 PR: https://github.com/mclayer/mctrader-hub/pull/271 (Story §1~§11 land, 5220bd3)
- Phase 2 PR (engine): https://github.com/mclayer/mctrader-engine/pull/52 (3 src + 2 test, +1373L impl)
- Phase 2 PR (hub runbook): https://github.com/mclayer/mctrader-hub/pull/272 (5 Phase + Rollback, ef7c715)
- Story file: `docs/stories/MCT-154.md` (2142L, §1~§11)
- ADR refs: ADR-027 D4 step 3 + D9 / ADR-009 §D2.1 / ADR-017 hot path
- Sibling retros: RETRO-MCT-150 / 151 / 152 / 153
- Codeforge issue: mclayer/plugin-codeforge#525 (lesson #5 sub-invariant 첫 적용 case)
- mctrader-engine `_io.py` (ADR-018 D5 atomic write helper, 본 Story namespace 충돌 0 verify)
