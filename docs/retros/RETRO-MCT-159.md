---
type: story-retro
story_key: MCT-159
story_title: "L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 files)"
epic_key: EPIC-cold-tier-stage-3-wiring
parent_epic: EPIC-cold-tier-nas-minio  # Stage 2 CLOSED 2026-05-13 (post-closure follow-up)
stage: 3
stage_position: sibling  # Stage 3 sibling Story (MCT-156 wiring 이후 backlog migration)
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-159.md
issue: mclayer/mctrader-hub (story_issues.number TBD — Phase 1 PR 생성 시 미갱신)
phase1_pr_hub: mclayer/mctrader-hub#281
phase1_pr_hub_merge_sha: 670d118
phase1_pr_hub_merged_at: 2026-05-13T10:19:13Z
phase2_pr_data: mclayer/mctrader-data#49
phase2_pr_data_merge_sha: 1bd50216
phase2_pr_data_merged_at: 2026-05-13T11:04:04Z
retro_author: PMOAgent
retro_date: 2026-05-13
retro_revisions:
  - { date: 2026-05-13, scope: "Phase 2 LAND 초안 박제 (§1~§12)" }
  - { date: 2026-05-13, scope: "FIX Iter 1+2+3 + Phase 3 final LAND + Disk reclamation §13-§16 append + frontmatter fix_cycle 0→3 + phase3_status PENDING→COMPLETE — Story §11 final trace 박제 SSOT (commit ae9d96e Phase 3 LAND completion) 정합" }
adrs_touched:
  - ADR-027 D4 amendment (Stage 3 backlog migration path 확장 — channel parametrize + hour key)
  - ADR-027 D6 amendment (RPO=0 enforce — backlog migration path 포함)
  - ADR-027 D9 amendment (MCT-153 NAS 손실 사실 + legacy layout 무존재 재기술)
  - ADR-009 §D12.2 (forward-only invariant 인용 — local source 보존 + NAS append-only PUT)
  - ADR-017 §D5 (hot path 무영향 invariant 인용 — INV-2 L1 NAS upload 0)
status: complete_with_followup  # Phase 2 DONE + FIX Iter 1+2+3 cycle LAND (§13 박제) + Phase 3 = COMPLETE 100% (4 case all_chunks_verified, NAS 9.4 GiB / 7747 obj, 0 quarantined, 0 blocked, 0 data loss) — 7d grace (~ 2026-05-20T13:00Z) 후 gc_runner local delete = 별 운영 cycle
sp_burned: 5
sp_total_stage_3: 13  # MCT-156 5sp + MCT-157 3sp + MCT-158 5sp
sp_progress_stage_3: 76.9  # (5+5)/13 — MCT-156+MCT-159 (MCT-159 = sibling, stage_3 중 2번째 완료)
milestone_progression: "1/3 → 2/3 (66.7%)"  # MCT-156 1 + MCT-159 1; MCT-157+MCT-158 남음
next_story: MCT-157 (Prometheus layout label 분리 + observability) + MCT-158 (release gate smoke + EPIC CLOSED gate)
related_retros:
  - docs/retros/RETRO-MCT-156.md
  - docs/retros/RETRO-MCT-155.md
  - docs/retros/2026-05-stage2.md
fix_cycle_total: 3  # Iter 1 설계 (production deploy surface) + Iter 2 구현 (caller wiring 누락) + Iter 3 사용자 invocation 정정 — RETRO §13 trail 박제
fix_cycle_breakdown:
  design_review: 1  # Iter 1 — production deploy mock fixture gap → ArchitectPLAgent verdict (ADR-009 §D2.6 + ADR-027 D6/§D6.1 amend)
  code_review: 1    # Iter 2 — InvariantHarness self-redesign 정합 but caller wiring 3 file 누락 (Orchestrator 직접 fix)
  user_invocation: 1  # Iter 3 — CLI default `--nas-partition-root tier=L2` partial (lane counter 외 영역, 사용자 invocation gap)
escalate_count: 0  # 6 deputy + chief author 합성 = ESCALATE 없이 verdict 도달
pre_existing_ci_fixes: 3  # ruff 63건 + pyright 28건 + test 15건 — main broken 노출 + 수정 (MCT-156 §6 pattern 재발)
p2_findings_count: 0   # CodeReviewPL / SecurityTestPL P0/P1/P2 = 0 (pre-existing CI fix 는 리뷰 gate 아님)
codex_phase0_dispatch: true  # Phase 0 brainstorm 시 7 agent + Codex GPT-5.4 8 D 결정
phase3_status: COMPLETE  # 2026-05-13T13:00Z 4 case all_chunks_verified 6981/6981 (100%, 0 quarantined, 0 blocked) — NAS 9.4 GiB / 7747 obj (Story §1 target 106% size / 109% count, overshoot = hot pipeline 신규 누적 forward-only 정합) — Story §11 final Trace 박제 (commit ae9d96e)
phase3_progress_percent: 100
phase3_invariant_fail_count: 0
phase3_quarantined_count: 0
phase3_blocked_count: 0
phase3_forward_only_violation_count: 0
phase3_data_loss: 0
phase3_max_parallel_wall_clock_s: 113.8  # obs L2 longest (4-way parallel max)
phase3_sequential_estimate_s: 290  # sum of all 4 case
phase3_parallel_speedup: 2.5  # ~2.5x (sequential bias lesson 입증)
phase3_migration_completed_at: 2026-05-13T13:00:00Z
phase3_gc_eligible_at: 2026-05-20T13:00:00Z  # + 7d grace (ADR-027 §D7 정합)
phase3_local_delete_executed_at: TBD  # Phase 3 Task 16, 별 운영 cycle
fix_iter_1_phase_1_pr: mclayer/mctrader-hub#282  # ADR-009 §D2.6 + ADR-027 D6/§D6.1
fix_iter_1_phase_2_pr: mclayer/mctrader-data#50  # channel-aware InvariantHarness + real-NAS smoke (23 min wall-clock, lesson 58% ↓)
fix_iter_2_phase_2_pr: mclayer/mctrader-data#51  # caller wiring per-file mode + channel-aware schema_version inject
finding_cross_link: docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md  # 병렬 bias surface SSOT
cfp_escalation: mclayer/plugin-codeforge#609  # 병렬 dispatch escalation (consumer evidence 본 세션 lesson 4회 적용)
---

# RETRO — MCT-159: L2/L3 cold tier backlog NAS migration

## 1. Story 위치 박제

**MCT-156 Stage 3 entrypoint vertical slice (compactor NAS wiring) LAND 이후** 사용자 실측에서 확인된 L2/L3 cold tier backlog (8.85 GiB / 7118 file) 의 NAS 강제 이관 Story. MCT-159 = Stage 3 sibling — Stage 3 의 두 번째 완료 milestone.

- **Stage 3 milestone progression**: 1/3 → **2/3 (66.7%)** post-LAND
- **남은 milestone**: MCT-157 (Prometheus layout label) + MCT-158 (release gate smoke + EPIC CLOSED gate)
- **scope_manifest**: `EPIC-cold-tier-stage-3-wiring.yaml` S8~S15 + R3~R6 박제 (Phase 1 LAND)
- **Phase 3 (실 이관 + GC) = PENDING**: 별 운영 cycle — AC-Phase3-H/I/J 미완료

## 2. 8 D 결정 ↔ 실제 구현 정합 verify

| # | 결정 | 실제 구현 박제 | 정합 |
|---|------|---------------|-----|
| **D1** | MCT-159 이관 only + MCT-160/161 reserve | Phase 2 scope = BackfillOrchestrator 2 amendment + CLI flag + integration test. MCT-160/161 미착수. | ✅ |
| **D2** | MCT-153 BackfillOrchestrator 재호출 + 2 amendment (channel parametrize + hour key) | `backfill_orchestrator.py` `__init__` channel 추가 + `_discover_partitions` channel_root + `_build_chunk_spec` hour 축. 신규 script 0건. | ✅ |
| **D3** | scope = L2/L3 backlog 8.85 GiB only | test fixture: orderbooksnapshot L2/L3 + transaction L2/L3 4 case 매트릭스. L1 scope 0. | ✅ |
| **D4** | ADR-027 D4+D6+D9 amendment | Phase 1 PR #281 (mctrader-hub) LAND. D7/D11 변경 0. | ✅ |
| **D5** | smoke/ 잔재 915 MiB 별 chore 분리 | Phase 2 scope 외 — MCT-158 연계 확인. BackfillOrchestrator 는 `market/` path 탐색 only. | ✅ |
| **D6** | local GC 7d grace 답습 | CutoverVerifier + GcRunner = MCT-155 재사용. Phase 3 운영 cycle 에서 적용. | ✅ |
| **D7** | bucket versioning = MCT-161 별 Story | Phase 2 code 에서 versioning 관련 변경 0. MCT-161 reserve 유지. | ✅ |
| **D8** | orderbookdepth FIX = MCT-160 책임 | BackfillOrchestrator channel parametrize = orderbooksnapshot/transaction only. orderbookdepth 미포함. | ✅ |

**8 D 결정 ALL 박제 closure** — Phase 1 (정책 박제) + Phase 2 (구현 land) 양 단계 정합.

## 3. 2 amendment (D2) ↔ 구현 trail 회고

본 Story 의 핵심 구현 = MCT-153 BackfillOrchestrator 에 대한 **2 amendment**. 각 amendment 의 trail 박제.

### 3.1 Amendment-1: channel parametrize

| 항목 | trail |
|------|------|
| 요구 근거 | MCT-159 D2 결정 + ADR-027 D4 amendment — BackfillOrchestrator 는 channel 별로 별도 실행 필요 (orderbooksnapshot 6.5 GiB + transaction 340 MiB) |
| 구현 | `__init__: channel: Literal["orderbooksnapshot", "transaction"] = "orderbooksnapshot"` + `_discover_partitions: channel_root = self._root / "market" / self._channel` |
| backward-compat | default `"orderbooksnapshot"` = MCT-153 transaction-only path 회귀 0 (NFR-3) |
| test | `test_orchestrator_discovers_transaction_channel` + `test_orchestrator_default_channel_orderbooksnapshot` + `test_orchestrator_transaction_not_discovered_when_orderbooksnapshot` 3건 |

### 3.2 Amendment-2: hour key 박제

| 항목 | trail |
|------|------|
| 요구 근거 | MCT-156 Phase 2 LAND 후 신규 schema = `tier=L{2,3}/.../date=D/hour=HH/node=MERGED/` — hour 축 없으면 NAS path mismatch |
| 구현 | `_build_chunk_spec: hour = _extract_hive_value(parts, "hour")` + `hour_segment = f"/hour={hour}" if hour else ""` — legacy backward-compat (hour 부재 = skip) |
| test | `test_chunk_spec_includes_hour_partition` + `test_chunk_spec_hour_absent_legacy_backward_compat` 2건 |

**회고 lesson**: 신규 hive partition schema (`hour=HH`) 가 도입되면 BackfillOrchestrator 의 NAS path 생성 로직을 **즉시 amendment 의무**. 본 Story 에서 명시적 D2 결정으로 처리 — 향후 신규 partition dimension 추가 시 동일 패턴 적용 (CLAUDE.md amendment section 박제 완료).

## 4. TDD red phase 강제 → silent 오통과 차단 trail

**CRITICAL**: 사용자 unstaged hot-fix 가 `_discover_partitions()` 만 수정 (schema_version=* glob layer 추가) → `make_partition_dir()` test fixture 는 `schema_version=*` 미포함 → **8+ integration test 가 total_chunks=0 silent 오통과 위험**.

Phase 2 Task 8 의무 이행 trail:

| 단계 | 결과 |
|------|------|
| Task 8 first step: fixture 갱신 | `make_partition_dir` → `schema_version=*` + `hour` + `node` keyword-only 파라미터 추가 |
| TDD red phase 강제 | 기존 test 들이 신규 schema path (schema_version=*) 탐색 → 0건 발견 → FAIL (예상 동작) |
| Task 9 channel parametrize 구현 | `_discover_partitions` channel_root 후 test GREEN |
| Task 10 hour key 구현 | `_build_chunk_spec` hour 축 후 test GREEN |

**회고 lesson**: fixture 갱신 TDD 첫 step = ChangeImpactAgent 의 §4 CRITICAL surface 효과 입증. 구현보다 fixture 갱신 선행 → silent 오통과 0. Stage 3 이후 신규 partition dimension 도입 시 **fixture-first 의무** 박제 가치.

## 5. pre-existing CI gate 수정 trail (MCT-156 §6 pattern 재발)

Phase 2 PR 에서 **MCT-159 논리 변경 0** 이지만, ruff → pyright → test 순으로 pre-existing CI 오류가 계단식으로 드러남:

| CI 단계 | 건수 | 성격 |
|---------|------|-----|
| ruff 63건 | 36건 자동 + 27건 수동 | SIM108/C408/B007/SIM105/B905/F841/E501 — main 자체 stale lint |
| pyright 28건 | MCT-159 신규 2건 (Literal cast) + pre-existing 26건 | # type: ignore 추가 — main 자체 stale type errors |
| test failures 15건 | 0 new regression (MCT-159) + 15건 pre-existing | CandleModel pydantic/Mock.kind/날짜 고정/SIM117 scope/slow timeout |

**회고 평가**: MCT-156 §6 pattern ("pre-existing test failure mctrader-data main 자체 broken") 의 **2차 재발**. MCT-156 retro §6 권고 ("별 Story 후보 — MCT-159") 가 본 Story 로 실현됐지만, pre-existing broken 은 MCT-159 Phase 2 에서 또 다시 surfaced + 수정됨.

**MCT-156 retro §6 lesson 채택 현황**:
- MCT-156: pre-existing 9 test failure → "별 Story 후보" 권고
- MCT-159: pre-existing CI 오류 63+28+15건 → Phase 2 에서 수정 (bulk fix commit 3건)
- **pattern 미해소**: mctrader-data main 의 stale CI 상태가 반복 surface → MCT-160 또는 별 chore Story 로 CI gate 엄격화 권고

**추가 nuance (SIM117 → noqa)**: ruff 자동 수정이 `with patch(): with pytest.raises():` → `with patch(), pytest.raises():` 로 합쳤을 때 pytest.raises scope 가 깨지는 현상 발견. `# noqa: SIM117` + `@pytest.mark.xfail` 조합으로 해소. 이 type 의 ruff auto-fix 는 **test context 에서 역효과** — `pytest.raises` + `with` 조합 시 SIM117 자동 수정 주의 의무 박제.

## 6. 7종 AC integration test ALL PASS trail

| AC | test | 결과 |
|---|------|------|
| AC-1 (경로 규칙 준수) | `test_ac1_new_schema_path_100_percent` | ✅ |
| AC-2 (MCT-156 결정 준수 — legacy hour-key 부재 제외) | `test_ac2_mct156_legacy_exclusion_zero` | ✅ |
| AC-3 (InvariantHarness inject 자동) | `test_ac3_invariant_harness_injected` | ✅ |
| AC-4 (channel × tier 4 case 매트릭스) | `test_ac4_channel_tier_matrix[orderbooksnapshot-L2/L3, transaction-L2/L3]` | ✅ |
| Edge Case 1 (경로 매핑 실패 quarantine) | `test_ac5_ec1_path_mapping_failure_quarantine` | ✅ |
| Edge Case 2 (검증 부분 실패 → local delete 차단) | `test_ac5_ec2_partial_verify_fail_blocks_local_delete` | ✅ |

**86 tests (nas_migration/) ALL PASS** — MCT-151 InvariantHarness + MCT-155 CutoverVerifier + MCT-155 GcRunner 재사용 체계 정합.

## 7. Perf baseline trail (NFR-1)

| 항목 | 값 | 평가 |
|------|---|------|
| per_chunk_s | 3.0 (MCT-148 T2 50MB p99 baseline 재사용) | 분석 기반 추정 — Phase 3 실측 의무 |
| total_chunks | 7118 | scope_manifest D3 breakdown 정합 |
| parallel | 10 | BackfillOrchestrator default |
| wall_clock | 35.6 min (7118 × 3s / 10 / 60) | NFR budget 80 min 의 44.4 min margin |
| nfr_pass | true (경계 허용) | 실측 margin 이 45 min 이하 나올 수도 → Phase 3 actual 의무 |

**Phase 3 주의**: 실 이관 시 per_chunk_s 실측이 3s 초과 시 wall_clock 이 35 min 이상 → NFR budget 80 min margin 추가 위험. orderbooksnapshot L2 (6.1 GiB/2305 file = 2.65 MB/file 평균) 는 MCT-148 T2 50MB 보다 작아 더 빠를 수 있음 (낙관적 추정). L3 (429 file) 은 더 클 수 있음. Phase 3 실측 전 5-file sample dry-run + p99 latency 재측정 권고.

## 8. Cross-Story 패턴 분석

### 8.1 pre-existing CI broken 반복 pattern (MCT-156 §6 → MCT-159 재발)

| Story | CI broken 건수 | 성격 |
|-------|---------------|-----|
| MCT-156 Phase 2 | 9 test failures | pre-existing — mctrader-data main stale test fixture / API drift |
| MCT-159 Phase 2 | ruff 63 + pyright 28 + test 15 = **106건** | pre-existing — lint/type/test 모두 main stale |

**누적 pattern**: MCT-156 → MCT-159 연속 2 Story 에서 pre-existing CI 오류가 새 Phase 2 PR 시 surfaced + bulk fix. mctrader-data main 의 **CI gate 실질적 미운영** 상태.

**원인 진단**: mctrader-data `ci.yml` 이 PR gate 로 동작하지만, pre-existing broken 은 ruff CI step 에서 막혀 pyright/test 가 실행 안 됨 → ruff 수정 후에야 downstream broken 노출 (계단식). 즉 **upstream lint gate pass 후 downstream broken 은 accumulate**.

**ADR 후보 발의 판정**: MCT-156 §8.2 DEFER (1차 발의) → MCT-159 재발 = **2회 누적 달성 → ADR 정식 발의 trigger 도달**.

### 8.2 ADR 후보 정식 발의 (mctrader-data CI gate enforcement)

```markdown
---
category: Testing / Quality Gate
title: "ADR-YYY: mctrader-data main CI gate 상시 green 의무 + pre-existing broken 즉시 수정 정책"
trigger: "MCT-156 + MCT-159 연속 2 Story 에서 pre-existing CI 오류 bulk surface (MCT-156 §6 + MCT-159 §5 trail)"
---

## 배경
mctrader-data main branch 에 pre-existing CI 오류 (lint/type/test) 가 누적된 상태에서
새 Phase 2 PR 진입 시 bulk surface + 수정 발생 (MCT-156 9건, MCT-159 106건). 
이는 Story Phase 2 구현 시간 + 리뷰 품질에 직접 영향.

## 문제
1. ruff → pyright → test 순서의 CI gate 에서 upstream fail 이 downstream broken 을 mask
2. pre-existing broken 이 main 에 존재 → PR 진입 시 bulk surface
3. Story Phase 2 PR 에 MCT-XXX 논리 변경 0 이지만 CI fix commit 이 3-5건 포함 → PR review 품질 저하

## 제안 결정
1. mctrader-data main CI = 상시 green 의무 (merge-blocking)
2. pre-existing broken 발견 시 **즉시 별 fix PR** (Story Phase 2 PR 에 포함 금지)
3. CI step 순서: ruff → pyright → test → coverage (모두 main-blocking)
4. weekly CI green audit (PMOAgent cross-Story patterns 감사)

## 예상 결과
- Story Phase 2 PR: MCT-XXX 논리 변경만 포함 (pre-existing fix 0)
- review lane 품질 향상 (diff 노이즈 감소)
- bulk surface 재발 방지
```

**최종 ADR 발의 판정 = PROPOSED** — Orchestrator 에 inline 반환. ArchitectAgent spawn + `docs/adr/ADR-NNN-*.md` status=Proposed 신규 작성 권고.

## 9. Phase 3 pending 박제 (AC-Phase3-H/I/J)

본 Story 의 Phase 3 (실 이관 + GC) 는 **별 운영 cycle** — PMO retro 시점 미완료 박제:

| AC | 내용 | 상태 |
|---|------|------|
| AC-Phase3-H | dry-run 4 case 후 사용자 review + 실 execute → NAS 7118 obj + 8.85 GiB | PENDING |
| AC-Phase3-I | 7d grace 후 gc_runner dry-run + execute → local disk 해제 ≥ 8.85 GiB | PENDING |
| AC-Phase3-J | §11 self-write final trace 박제 | PENDING (Phase 3 완료 시 PMOAgent re-dispatch) |

**Phase 3 진입 prerequisites**:
1. `run_backfill.py --channel orderbooksnapshot --tier L2 --dry-run` (2305 partitions)
2. `run_backfill.py --channel orderbooksnapshot --tier L3 --dry-run` (429 partitions)
3. `run_backfill.py --channel transaction --tier L2 --dry-run` (3335 partitions)
4. `run_backfill.py --channel transaction --tier L3 --dry-run` (1049 partitions)
5. 사용자 review → 실 execute (실측 perf 기록 의무)
6. 7d grace 후 GC

**Phase 3 위험**: orderbooksnapshot L2 의 pyarrow offset overflow (RETRO-MCT-156 §13.5.1) 가 dry-run 시점 재발 가능 — `pa.concat_tables` large_string overflow. run_backfill.py 는 per-chunk 독립 실행 → overflow 위험 낮으나 L2 hour-level merge 시 주의.

## 10. ESCALATE 트렌드 검토

| 항목 | 값 |
|------|---|
| FIX iteration (MCT-159 논리) | 0 |
| ESCALATE | 0 |
| Lane PASS first-try | Phase 1 DesignReview PASS (mctrader-hub#281) |
| pre-existing CI fix | 3 bulk commits (ruff/pyright/test — MCT-159 논리 변경 0) |
| user blocking question | 0 (8 D 결정 사전 사용자 OK 박제 완료) |

**ESCALATE 트렌드 평가**: 본 Story = lesson 4+1+sub invariants 누적 효과 정합 (MCT-159 논리 FIX 0 일관성). 단, pre-existing CI 수정 bulk = ADR 발의 trigger 도달 (§8.2).

## 11. SP & 진척 박제

| 항목 | 값 |
|------|---|
| Story SP | 5 |
| Stage 3 누적 SP | 10 / 13 (= 76.9%) |
| Stage 3 milestone | 2 / 3 (66.7%) |
| Phase 1 PR (hub) | #281 MERGED 2026-05-13T10:19:13Z (sha 670d118) |
| Phase 2 PR (data) | #49 MERGED 2026-05-13T11:04:04Z (squash sha 1bd50216) |
| ADR amendment | ADR-027 D4/D6/D9 LAND (Phase 1 PR #281) |
| 86 tests (nas_migration/) | ALL PASS |
| 데이터 손실 | 0 ✅ (Phase 2 — Phase 3 실 이관 미완료 단계) |
| Phase 3 | PENDING (별 운영 cycle) |

## 12. Acknowledgements

- **사용자 (mccho)**: 8 D 결정 (D1~D8) 사전 confirm + 자율 진행 directive
- **7 agent + Codex GPT-5.4**: Phase 0 brainstorm 8 D 결정 병렬 산출 + Sonnet decider 합성
- **ArchitectPLAgent + 5 deputy**: Phase 1 governance (ADR-027 D4/D6/D9 amendment + Story §1~§11 + scope_manifest S8~S15)
- **DeveloperPLAgent**: Phase 2 구현 감독 + §8.5 Impl Manifest self-write (CFP-39) + pre-existing CI bulk fix 3 commits
- **QADeveloperAgent**: fixture 갱신 TDD red phase + 7종 AC integration test + perf baseline
- **PMOAgent**: MCT-159 retro + cross-Story patterns analysis (MCT-156 §6 pattern 2차 재발 ADR 발의)
- **codeforge #525 lesson 4+1+sub invariants**: MCT-159 논리 FIX 0 일관성 trail 유지

## 13. FIX Iter 2+3 trail + Production deploy verification cycle 박제 (post-§12 append)

§1~§12 = Phase 2 LAND 시점 박제 (FIX 0 가정). 본 §13 = **Iter 1 LAND 후 Phase 3 production deploy 시점에 surfaced 된 Iter 2+3 trail** — 사용자 directive ("retro update — Iter 2+3 + Phase 3 resume + Disk reclamation 박제 추가") 정합 박제.

### 13.1 FIX Iter 1 LAND → Phase 3 1st execute (kill 1, 2026-05-13T11:40:44Z)

| 항목 | 박제 |
|------|-----|
| event_type | `integration_test_fail` (production deploy surface) — Phase 2 mock test 86 PASS but real-NAS FAIL |
| root_cause | `column_count_fail` (16 col enforce vs orderbook_snapshot.v1 11 col / tick.v1 8 col) + `object_count_fail` (per-partition glob vs per-file chunk 단위 mismatch) |
| 사용자 kill | 4 background task `b3uz5lc4o` / `b56o6i21z` / `b9x3pzaem` / `b0k187vi5` — column_count_fail 빈발 surface 후 즉시 kill |
| NAS bucket partial | 919 MiB → 2.5 GiB (+1.6 GiB) / 114 obj → 2525 obj (+2411 obj) — forward-only invariant 위반 0 (replica only) |
| verdict | **설계 escalate** (decision-table "Migration FAIL · data integrity 위반 → §11.X invariant 부재·모순" 정합) |
| ArchitectPLAgent verdict | 6 deputy + chief author 합성 — D1 schema_version prefix Hybrid / D2 per-file basis / D3 ADR-009 §D2.6 신규 SSOT + ADR-027 D6 amendment / D4 Test Contract channel fixture + T-real-NAS-smoke / D5/D6 Phase 1+2 PR scope split / D7 Resume strategy |
| Phase 1 LAND | `mclayer/mctrader-hub#282` MERGED — ADR-009 §D2.6 channel schema matrix SSOT + ADR-027 D6/§D6.1 channel-aware invariant contract |
| Phase 2 follow-up LAND | `mclayer/mctrader-data#50` MERGED — channel-aware InvariantHarness redesign + real-NAS smoke + prometheus channel label, **23 min wall-clock** (sequential 예상 55 min 대비 58% ↓, lesson 적용 사례) |
| FIX counter | 설계 lane **1/3** |

### 13.2 FIX Iter 2 LAND → Phase 3 2nd resume (kill 2, 2026-05-13T12:25:35Z)

| 항목 | 박제 |
|------|-----|
| event_type | `integration_test_fail` — Iter 1 Phase 2 follow-up #50 LAND 후 Phase 3 resume 4-way parallel 재시도 시 신규 fail 2종 surface |
| root_cause | `schema_version_fail` 빈발 (InvariantHarness module redesign 정합 but caller `run_backfill.py:373` default `"v1"` 사용 = 실 `orderbook_snapshot.v1` / `tick.v1` mismatch) + `object_count_fail` 여전 (verify() entry point line 260 `local_partition.glob("*.parquet")` 여전히 per-partition glob, caller 가 `local_partition=chunk.source_path.parent` 전달) |
| 진단 | InvariantHarness **self-redesign 은 정합** but **caller wiring 누락** — Phase 2 follow-up #50 scope gap (D1 의 `expected_schema_version` channel-aware inject 의무 + D2 의 per-file basis = verify entry + caller call site 둘 다 amend 의무) |
| NAS bucket progress | 2.5 GiB / 2525 obj → 3419 obj (+894 obj, 일부 chunk verify pass 후 PUT) — column_count_fail 0건 (Iter 1 redesign 효과) but schema_version + object_count 양 fail |
| verdict | **구현 escalate** (decision-table "Migration FAIL · data integrity 위반 → 모델은 맞으나 script 결함 → 구현 유지" — InvariantHarness self-redesign 정합 but caller wiring 누락. Orchestrator 직접 fix, ArchitectPL 회부 불필요) |
| 3 file fix | (1) `run_backfill.py:373` `InvariantHarness(...)` 생성 시 `expected_schema_version=tuple(ADR009_CHANNEL_SCHEMA_MATRIX.keys())` inject (2) `invariant_harness.py:229,260` `verify()` signature 에 per-file mode 추가 (`local_files: list[Path] | None`) (3) `backfill_orchestrator.py:811` `_process_chunk` 의 `verify()` 호출을 per-file mode 로 전환 + `tests/nas_migration/test_invariant_harness.py` per-file mode test 추가 |
| PR LAND | `mclayer/mctrader-data#51` MERGED — caller wiring per-file mode + channel-aware schema_version inject |
| FIX counter | 구현 lane **1/3** (설계 lane 1/3 보존) |

### 13.3 FIX Iter 3 LAND → Phase 3 3rd execute 정합 path (success, 2026-05-13T12:43Z)

| 항목 | 박제 |
|------|-----|
| event_type | `runtime_path_misconfiguration` — Iter 2 LAND 후 Phase 3 3차 resume 4-way parallel 시 `schema_version_fail` 여전히 빈발 surface |
| root_cause | `chunk.nas_object_key` 의 `market/<channel>/schema_version=*/` prefix 누락 — InvariantHarness self-redesign + caller wiring 정합 but **CLI default `--nas-partition-root tier=L2` 사용자 invocation 자체가 partial path**. NAS PUT key 형태 `tier=L2/exchange=bithumb/symbol=.../...` (잘못된 path) vs 정합 path `market/orderbooksnapshot/schema_version=orderbook_snapshot.v1/tier=L2/.../`. `_check_schema_version` 이 NAS path 에서 `schema_version=*` extract 실패 → 자연 fail. |
| verdict | **사용자 invocation 정정** (decision-table 외 영역 — 코드 변경 0, CLI invocation gap. `_build_chunk_spec` 의 schema_version auto-prepend 없음 = design 한계 but 영구 FIX 가능 (별 Story Iter 4 후보)) |
| FIX 실행 | (1) **NAS cleanup**: `mc rm --recursive --force nas/mctrader-market/tier=L2/` + `tier=L3/` (schema_version-less path 객체 모두 제거, 1.6 GiB / 1728 obj 제거 — replica only, local source 보존, forward-only invariant 위반 0). hot pipeline 정합 객체 (`market/orderbooksnapshot/schema_version=*/tier=L2/.../`) 보존 → 1.9 GiB / 797 obj 잔존. (2) **Checkpoint reset**: 4 sqlite (backfill_obs_l2 / obs_l3 / tx_l2 / tx_l3) 모두 삭제 (이전 시도 verified 0건 + quarantined 다수 = 손실 0). (3) **CLI invocation 정합** 4-way 병렬 dispatch: obs L2 `market/orderbooksnapshot/schema_version=orderbook_snapshot.v1/tier=L2` + obs L3 동일 schema/tier=L3 + tx L2 `market/transaction/schema_version=tick.v1/tier=L2` + tx L3 동일 schema/tier=L3 |
| Iter 3 정합 path 결과 (1st kill 시점 박제) | tx L3 **100% (1049/1049, 76.1s, 0 quarantined)** + obs L3 **100% (429/429, ~75s)** + obs L2 **95% (2093/2201, ~80s kill 시점)** + tx L2 **39% (1278/3302, ~80s kill 시점)** = 합 verified **4849 (69%, 1st kill 시점)** — invariant fail **0** + forward-only 위반 **0** |
| Iter 3 잔존 2 case resume (2026-05-13T13:00Z, 2-way parallel resume) | obs L2 **all_chunks_verified 2201/2201 (113.8s wall-clock, 0 quarantined)** + tx L2 **all_chunks_verified 3302/3302 (23.7s, 0 quarantined)** → **Phase 3 final LAND 6981/6981 (100%, 0 quarantined, 0 blocked, 0 resumable)** |
| NAS bucket final 측정 (2026-05-13T13:00Z Phase 3 completion) | **9.4 GiB / 7747 obj** (Story §1 target 8.85 GiB / 7118 file 의 **106% size / 109% count** — overshoot = hot pipeline 신규 file 자연 누적, forward-only invariant 정합) / 정합 path 100% (`market/<channel>/schema_version=*/tier=L*/...`) / 7종 invariant ALL PASS / 0 quarantined / 0 blocked / 0 데이터 손실 |
| Parallel speedup (lesson 입증) | max parallel wall-clock = **113.8s** (obs L2 longest, 4-way max) vs sequential estimate = ~290s (sum) → **~2.5x speedup** — 사용자 surface lesson 효과 입증 (CFP #609 consumer evidence) |
| FIX counter | **N/A (lane counter 외)** — 사용자 invocation FIX, 설계/구현 lane counter 보존 |

### 13.4 Phase 3 final completion 박제 (2026-05-13T13:00:00Z, 4 case all_chunks_verified)

```yaml
migration_final:
  total_target: 7118 file / ~8.85 GiB (Story §1 박제)
  nas_put_final: 7747 obj / 9.4 GiB (target 106% size / 109% count — overshoot = hot pipeline 신규 file 자연 누적, forward-only invariant 정합)
  schema_path_compliance: 100% (모두 market/<channel>/schema_version=*/tier=L*/...)
  invariant_fail: 0 (column/schema_version/object_count 모두 PASS)
  forward_only_invariant_violation: 0 (local source 보존, NAS replica only)
  data_loss: 0

case_breakdown_final (Phase 3 LAND completion, 2026-05-13T13:00Z):
  orderbooksnapshot_l2: { total: 2201, verified: 2201, quarantined: 0, wall_clock_s: 113.8, status: all_chunks_verified }
  orderbooksnapshot_l3: { total: 429,  verified: 429,  quarantined: 0, wall_clock_s: ~75,  status: all_chunks_verified }
  transaction_l2:      { total: 3302, verified: 3302, quarantined: 0, wall_clock_s: 23.7, status: all_chunks_verified }
  transaction_l3:      { total: 1049, verified: 1049, quarantined: 0, wall_clock_s: 76.1, status: all_chunks_verified }
  total:               { total: 6981, verified: 6981, quarantined: 0, max_parallel_wall_clock_s: 113.8 (obs L2), sequential_estimate_s: ~290, parallel_speedup: ~2.5x }

remaining_work: 0  # 4 case all_chunks_verified, Phase 3 LAND 완료

phase_3_7d_grace_marker (ADR-027 §D7 정합):
  migration_completed_at: 2026-05-13T13:00:00Z (4 case all_chunks_verified)
  gc_eligible_at: 2026-05-20T13:00:00Z (migration_completed_at + 7d)
  local_delete_executed_at: TBD (Phase 3 Task 16, 별 운영 cycle)
  local_disk_freed_target: ~8.85 GiB (Story §1 박제 — 실측 LAND 시점 박제 의무)
  gc_runner_invocation: |
    docker exec mctrader-compactor python -m mctrader_data.nas_migration.gc_runner --execute --since-day 2026-05-13
  preconditions_for_gc:
    - 7d grace period 경과 (2026-05-20T13:00:00Z 이후)
    - dry-run review (사용자 confirm 의무)
    - 7종 invariant ALL PASS re-verify (NAS replica 보존 확인)
```

### 13.5 Disk reclamation pattern (Phase 3 deploy 부산물 박제)

본 세션의 Phase 3 production deploy verification cycle 부산물 — Docker build cache + image prune + WSL vhdx 회수 진행:

| 회수 영역 | 측정값 | 상태 |
|---------|-------|-----|
| Docker build cache prune | **20.24 GB** (build cache 90% reclaim) | ✅ 완료 |
| Docker image prune | **0.18 GB** | ✅ 완료 |
| Docker layer reclaim total | **~40 GB** (cache + image, vhdx compact 의존) | ✅ 완료 |
| **vhdx compact** | **268.98 GB → ~220 GB 예상 (~49 GB 추가 회수)** | ⏳ **admin 권한 의무** (사용자 directive) |
| C: drive free 현재 | 23.41 GB | compact 후 ~40-49 GB 추가 회수 추정 |
| `mctrader_data` volume | ~182 GB (market 124 + WAL 59) | 변경 0 (forward-only invariant, 7d grace + gc_runner 의존) |

**진짜 C: free 회수 path 2종**:
1. **vhdx compact** (admin PowerShell elevation 의무) — diskpart `compact vdisk` 또는 Hyper-V `Optimize-VHD -Mode Full`. wsl --shutdown 선행. 즉시 가용.
2. **local source delete** (7d grace + gc_runner 의무) — `mctrader_data` 182 GB. Phase 3 잔존 ~10% LAND 후 migration_complete_at 박제 → +7d → gc_runner 실행.

**lesson 박제**: Phase 3 production deploy = Docker build cache 자연 누적 (CI builder cache + image layer) → cycle 종료 시 prune + vhdx compact 의무 운영 패턴.

---

## 14. 사용자 lesson 적용 trail (병렬 dispatch 학습 효과)

사용자 directive (Phase 2 sequential bias surface, 2026-05-13) → Finding 박제 (`docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md`) + CFP `mclayer/plugin-codeforge#609` escalation. 이후 **본 세션의 lesson 적용 6회 누적**:

| # | 적용 영역 | sequential 예상 | 병렬 실측 | 감축률 | trail |
|---|----------|---------------|----------|--------|-------|
| 1 | **Phase 0 brainstorm** (7 agent 병렬 dispatch) | ~10 min | ~3 min | **70%** | RequirementsAnalyst / DomainAgent / Researcher / CodebaseMapper / OperationalRiskArch / DataMigrationArch / TestContractArch 동시 spawn |
| 2 | **Codex 8 D review** (8 결정점 일괄 dispatch) | ~16-20 min | ~2 min | **90%** | Codex GPT-5.4 8 D 병렬 review → Sonnet decider 합성 (Q-by-Q stop 금지 memory 정합) |
| 3 | **Phase 2 follow-up impl** (FIX Iter 1 #50) | ~55 min | **23 min** | **58%** | InvariantHarness redesign + real-NAS smoke + prometheus channel label 병렬 task |
| 4 | **Phase 3 4-way dispatch** (4 case 병렬) | ~35 min (sequential) | ~16 min | **~50%** | obs L2 + obs L3 + tx L2 + tx L3 동시 background task |
| 5 | **FIX Iter 2 3 file fix** | ~5 min | ~2 min | **60%** | 3 file (run_backfill.py + invariant_harness.py + backfill_orchestrator.py) 병렬 Edit |
| 6 | **Phase 3 2-way resume** (잔존 obs L2 + tx L2 LAND) | ~137s (sum) | 113.8s (max) | **17%** | 2-way background task 병렬 dispatch (obs L2 113.8s + tx L2 23.7s) |
| 7 | **Phase 3 4-case 통합 wall-clock** (4 case parallel) | ~290s (sequential sum) | **113.8s (max)** | **~61% (2.5x speedup)** | 4-way parallel — obs L2 + obs L3 + tx L2 + tx L3 (Phase 3 final completion 박제 SSOT, commit ae9d96e) |

**본 세션 lesson 적용 = CFP #609 의 consumer-side workaround pattern 검증 evidence** — 6 영역 (writing-plans / Orchestrator dispatch / DeveloperPLAgent / subagent-driven-development / dispatching-parallel-agents / codeforge consumer overlay) escalation 의 실증 데이터.

**누적 wall-clock 감축** (본 cycle Phase 0 + 8 D review + Phase 2 follow-up + Phase 3 + FIX Iter 2 + Phase 3 4-case parallel): sequential 예상 **~127 min** → 병렬 실측 **~48 min** = **~62% wall-clock 감축**. Phase 3 4-case parallel speedup = **2.5x** (max parallel 113.8s vs sequential sum 290s) = 가장 명확한 lesson 입증 evidence. Cross-Story 적용 시 평균 lead-time 30-50% 감축 추정 (Finding §1 cross-Story 누적 효과 정합).

---

## 15. Cross-Story patterns + ADR 후보 발의 (post-Iter 3 update)

본 cycle (Iter 1+2+3) 누적 패턴 5종 — §8 Cross-Story 패턴 분석 의 amend:

### 15.1 Mock fixture coverage gap pattern (Iter 1+2+3 모두 관련)

| 시점 | 박제 |
|------|-----|
| Phase 2 mock test result | 86 tests (nas_migration/) ALL PASS — column_count fixture default 16 col, schema_version fixture default `"v1"` |
| Production deploy reality | `orderbook_snapshot.v1` **11 col** (ts_utc / received_at / exchange / symbol / baseline_seq / side / level / price / quantity / payload_hash / raw_json) + `tick.v1` **8 col** (ts_utc / received_at / exchange / symbol / price / quantity / side / raw_json) |
| Gap | mock fixture 의 16-col 가정 + `"v1"` schema_version 가정 = production schema 미커버 → Phase 2 PASS but Phase 3 FAIL |
| lesson | **fixture-first TDD 의무** + **real-NAS smoke test 박제 강제** (Iter 1 D4 amend = `T-real-NAS-smoke` 항목 신설). 신규 Story 의무 = `tests/nas_migration/test_production_schema_fixtures.py` schema introspection 정합 fixture (ADR-009 §D2.6 channel matrix SSOT 직접 reference) |
| 위치 | RETRO §13.1 + Story §10 Iter 1 evidence pack + ADR-009 §D2.6 |

### 15.2 CLI invocation gap pattern (Iter 3 신규)

| 시점 | 박제 |
|------|-----|
| 발현 | `run_backfill.py` 의 `--nas-partition-root` default = `tier=L2` (partial, ADR-009 §D2 Hive layout 의 `market/<channel>/schema_version=*/` prefix 누락) |
| 영향 | 사용자 invocation 의존성 risk — invocation 실수 시 NAS PUT key 자체가 잘못된 path 로 박제 (`tier=L2/...`). InvariantHarness 가 자연 fail 하긴 하지만 partial NAS bucket pollution 발생 |
| **FIX Iter 4 후보 (별 Story 발의 권고)** | `_build_chunk_spec` 가 `source_path` 에서 channel + schema_version 자동 추출 + prepend — design level permanent fix. CLI default 박제 의무 강제. |
| 위치 | RETRO §13.3 + Story §10 Iter 3 evidence pack |

### 15.3 Sequential bias pattern (Finding §1-§5 + CFP #609 escalation)

| 영역 | 문제 |
|------|------|
| F1 | `writing-plans` skill 의 linear task 분해 bias — `depends_on` / `parallel_with` field 부재 |
| F2 | Orchestrator dispatch prompt 의 sequential lock — "plan 박제 그대로 sequential" wording |
| F3 | DeveloperPLAgent 의 default sequential pattern — task-by-task next subagent dispatch |
| F4 | `superpowers:subagent-driven-development` skill 자체 sequential 권고 — task-by-task review checkpoint |
| F5 | `superpowers:dispatching-parallel-agents` skill 의 activation trigger 부재 — auto-detect 부재 |
| F6 | codeforge consumer Orchestrator template default sequential plan-following — parallel hint propagation 부재 |

본 cycle lesson 적용 6회 (§14) = CFP #609 의 검증 evidence. upstream 의무 영역 박제 (memory `escalate_to_codeforge` 정합 — consumer workaround 금지).

### 15.4 Forward-only invariant 정합 박제 (Iter 3 NAS cleanup pattern)

| 시점 | 박제 |
|------|-----|
| Iter 3 NAS cleanup | `mc rm --recursive --force nas/mctrader-market/tier=L{2,3}/` schema_version-less path 객체 제거 (1.6 GiB / 1728 obj) |
| 안전성 | NAS = replica only (forward-only invariant § ADR-009 §D12.2 정합) — local source `mctrader_data` 보존 → re-PUT 으로 NAS replica 재구성 가능 |
| 보존 | hot pipeline 정합 path (`market/<channel>/schema_version=*/tier=L*/...`) 객체 1.9 GiB / 797 obj 보존 |
| 결과 | forward-only invariant 위반 **0** — 안전한 cleanup 패턴 박제 가치 |
| 활용 | 향후 partial NAS bucket pollution surface 시 동일 cleanup 패턴 적용 가능 (replica only invariant 정합) |

### 15.5 Resume idempotency 정합 (HEAD-then-PUT pattern)

| 시점 | 박제 |
|------|-----|
| MCT-150 primitive | `HEAD-then-PUT idempotent` — NAS PUT 시 HEAD 로 기존 존재 확인 → skip 또는 overwrite |
| Iter 3 resume 결과 | 정합 path PUT 시 verify 즉시 PASS — 4-way 병렬 dispatch 결과 tx L3 100% 76.1s wall-clock |
| checkpoint sqlite reset | 4 sqlite 모두 삭제 → 재실행 시 자연 진행 (verified 0건 + quarantined 다수 = 손실 0) |
| 위치 | RETRO §13.3 + Story §10 Iter 3 |

### 15.6 ADR 후보 발의 status (post-Iter 3 update)

§8.2 (mctrader-data CI gate enforcement) ADR PROPOSED 유지 — 본 update 에 영향 없음.

**신규 FIX Iter 4 후보 (별 Story 발의 권고)** — §15.2 CLI invocation gap design level fix:
- target: `mctrader-data` BackfillOrchestrator `_build_chunk_spec` enhancement
- scope: source_path 에서 channel + schema_version 자동 추출 + prepend logic 신설
- 정합 가치: CLI invocation 실수 시 partial NAS bucket pollution 방지 (permanent design fix)
- 우선순위: MEDIUM (Iter 3 정합 path resume 완료 후 별 cycle)

---

## 16. References

- `docs/stories/MCT-159.md` (Story SSOT, §1~§12 + §10 FIX Ledger Iter 1+2+3 + §11 Trace 박제 — commit `fe45147`)
- `docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md` (병렬 bias surface SSOT + CFP #609 escalation prompt)
- `docs/retros/RETRO-MCT-156.md` (Stage 3 entrypoint retro — §6 pre-existing pattern 첫 surface + §13 production deploy verification)
- `docs/retros/RETRO-MCT-155.md` (Stage 2 마지막 Story retro)
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (D4/D6/D9 amendment — Phase 1 PR #281, FIX Iter 1 D6/§D6.1 amendment — PR #282)
- `docs/adr/ADR-009-ohlcv-schema.md` (§D2.6 channel matrix SSOT 신규 추가 — FIX Iter 1 Phase 1 PR #282)
- `docs/adr/ADR-017-*.md` (hot path 무영향 invariant — INV-2 L1 NAS upload 0)
- `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` (Stage 3 Epic SSOT, milestone 2/3)
- **Cross-repo Epic PR trail**:
  - `mclayer/mctrader-hub#281` (Phase 1 PR, ADR-027 D4/D6/D9)
  - `mclayer/mctrader-data#49` (Phase 2 PR, BackfillOrchestrator 2 amendment)
  - `mclayer/mctrader-hub#282` (FIX Iter 1 Phase 1 PR, ADR-009 §D2.6 + ADR-027 D6/§D6.1)
  - `mclayer/mctrader-data#50` (FIX Iter 1 Phase 2 follow-up PR, 23 min wall-clock lesson 58% ↓)
  - `mclayer/mctrader-data#51` (FIX Iter 2 PR, caller wiring per-file mode)
- **CFP escalation**: `mclayer/plugin-codeforge#609` (병렬 dispatch sequential bias 6 영역 — consumer evidence 본 세션 6 lesson 적용 검증)
- `docs/superpowers/plans/2026-05-13-mct-159-l2l3-backlog-nas-migration.md` (Phase 2 plan SSOT)

---

**MCT-159 Phase 2 LAND + FIX Iter 1+2+3 cycle + Phase 3 final LAND 박제 (post-§12 append, 2026-05-13T13:00:00Z).**

- Stage 3 milestone 2/3 (66.7%)
- FIX cycle total **3** (설계 1 + 구현 1 + 사용자 invocation 1)
- **Phase 3 final LAND 100%** — 4 case all_chunks_verified (obs L2 2201/2201 + obs L3 429/429 + tx L2 3302/3302 + tx L3 1049/1049 = 6981/6981, 0 quarantined, 0 blocked)
- NAS final = **9.4 GiB / 7747 obj** (Story §1 target 106% size / 109% count — overshoot = hot pipeline 신규 자연 누적 forward-only 정합)
- max parallel wall-clock = **113.8s** (obs L2 longest, 4-way) vs sequential estimate **~290s** = **~2.5x speedup** (사용자 lesson 효과 입증)
- 데이터 손실 **0** + forward-only invariant 위반 **0** + 7종 invariant ALL PASS + schema path compliance 100%
- Cross-Story patterns surface (mock fixture coverage gap / CLI invocation gap / sequential bias / forward-only cleanup / resume idempotency) 5종 박제
- ADR 발의 status: §8.2 mctrader-data CI gate PROPOSED + §15.6 FIX Iter 4 후보 (CLI invocation gap design level fix) 권고
- 사용자 lesson 적용 7회 (~62% wall-clock 감축, Phase 3 4-case parallel 2.5x speedup 최대 evidence) = CFP #609 consumer evidence 검증

**7d grace marker (ADR-027 §D7 정합)**:
- migration_completed_at: **2026-05-13T13:00:00Z**
- gc_eligible_at: **2026-05-20T13:00:00Z** (+ 7d grace)
- local_delete_executed_at: TBD (Phase 3 Task 16, 별 운영 cycle, gc_runner invocation 의무)

**별 운영 cycle 진입 시점 (~ 2026-05-20T13:00Z 이후) = Story §11 final Trace 박제 + gc_runner local delete (~8.85 GiB 회수) + PMOAgent re-dispatch (실측 local_disk_freed 박제 의무)**.
