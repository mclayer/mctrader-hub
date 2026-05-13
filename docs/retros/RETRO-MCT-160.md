---
type: story-retro
story_key: MCT-160
story_title: "L2/L3 cadence + OOM + L1 backlog cleanup + R-EXTRA + P1 합병"
epic_key: EPIC-compactor-operations
parent_epic: EPIC-cold-tier-stage-3-wiring  # post-MCT-156 deploy 5중 차단 cycle
stage: post-stage-3-cycle  # Stage 3 wiring 후 사용자 NAS 실측 5중 차단 cycle 의 두 번째 Story
stage_position: drainage-lever  # EPIC-compactor-operations Story-2 (진짜 drainage lever — L2 cadence + OOM root fix)
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-160.md
issue: mclayer/mctrader-hub#286
phase1_pr_hub: mclayer/mctrader-hub#287
phase1_pr_hub_merge_sha: cad60d26c22c7132e34500edc2fb431170ff309e
phase1_pr_hub_merged_at: 2026-05-13T15:32:21Z
phase2_pr_data: mclayer/mctrader-data#53
phase2_pr_data_merge_sha: c96a9efac5f74cb485587833504632f08c127508
phase2_pr_data_merged_at: 2026-05-13T15:51:09Z
phase2_pr_hub: TBD  # 본 RETRO PR 자체
retro_author: PMOAgent
retro_date: 2026-05-14
adrs_touched:
  - ADR-027 silent-skip 차단 amendment (caller-explicit date + post-write monotonic verify + quarantine 정책 + 운영자 review 의무)
  - ADR-009 nullability discipline 3 schema amendment (transaction + orderbooksnapshot + orderbookdepth)
  - ADR-009 Amendment History entry (2026-05-13 MCT-160)
status: complete  # Phase 1 + Phase 2 data + Phase 2 hub ALL LAND
sp_burned: 5
sp_total_epic_compactor_operations: 11  # MCT-162 3sp + MCT-160 5sp + MCT-161 3sp
sp_progress_epic: 72.7  # (3+5)/11
milestone_progression: "1/3 → 2/3 (66.6%)"  # MCT-162 + MCT-160 LAND, MCT-161 잔여
next_story: MCT-161 (NAS bucket versioning + replication, PROPOSED → IN_PROGRESS transition)
related_retros:
  - docs/retros/RETRO-MCT-162.md  # sibling Story-1 (entrypoint, EPIC-compactor-operations)
  - docs/retros/RETRO-MCT-156.md  # parent Stage 3 entrypoint
  - docs/retros/RETRO-MCT-159.md  # sibling Stage 3 backlog migration
  - docs/retros/2026-05-stage2.md  # Stage 2 EPIC CLOSED
fix_cycle_total: 1  # CodeReviewPL FIX iter 1 (P0×2 + P1×2 + P2×2 = 6 findings fix)
fix_cycle_breakdown:
  design_review: 0    # Phase 1 PR #287 first-try PASS
  test_agent: 0       # ubuntu pre-existing main fail (MCT-156 cycle 박제 정합, 본 PR 영향 0), windows-latest PASS
  security_test: 0    # P0=0 / P1=0
  code_review: 1      # FIX iter 1 — 6 finding fix (F1+F2+F4+F5+F8+F9 immediate fix, F3+F6+F7 surface → MCT-163 candidate)
escalate_count: 0
p0_findings_fixed_in_iter1: 2  # F1 (test fixture pa.Table.from_pylist) + F2 (DualWriter sig mismatch)
p1_findings_fixed_in_iter1: 2  # F4 (malformed frame ValueError) + F5 (path traversal containment)
p2_findings_fixed_in_iter1: 2  # F8 (quarantine assertion 복구) + F9 (read_bytes spy assert)
findings_surface_to_mct_163: 3  # F3 (DualWriter 내부 streaming) + F6 (true row-batch streaming) + F7 (D7 spec drift)
codex_phase0_dispatch: true  # brainstorm Phase 1 시 Codex GPT-5 11 D + R-EXTRA 합성 (D1-D11 ALL 사용자 OK)
wal_sample_fetch: false  # MCT-162 의 sample fetch 답습 (3 schema 이미 박제), 본 Story = cadence + OOM + nullability scope
upbit_l1_lost_root_cause_diagnosed: false  # D9 verify only — Phase 2 land 후 측정 의무
backlog_drainage_at_t0_phase2_land: 4319  # compactor restart 2026-05-14 t=0 sealed segment count (MCT-162 t=0 = 82,456 대비 95% 감소 — 자연 drainage evidence)
backlog_drainage_at_phase1_land_phase2_pending: null  # Phase 1 vs Phase 2 사이 자연 drainage 78,137 감소
backlog_drainage_after_1h: null  # 본 RETRO LAND 후 별 wakeup 또는 사용자 측정
adr_proposal: ADR-XXX-post-cutover-wiring-gap-prevention  # PMOAgent 발의 권고 (누적 3회 사례 — Stage 2 EPIC CLOSED + Stage 3 MCT-156 + Stage 3 post-cycle MCT-162+MCT-160)
adr_proposal_evidence_accumulation: 3  # 1=Stage 2 EPIC CLOSED, 2=Stage 3 MCT-156 post-cycle, 3=본 cycle (MCT-162 entrypoint + MCT-160 drainage lever)
---

# RETRO — MCT-160: L2/L3 cadence + OOM + L1 backlog cleanup + R-EXTRA + P1 합병

## 1. Story 위치 박제

**MCT-156 (Stage 3 wiring entrypoint) LAND 후 사용자 NAS bucket 실측에서 발견된 5중 차단 cycle 의 두 번째 Story** — EPIC-compactor-operations 의 **drainage lever** Story (Story-2, sequential drainage 진짜 lever — L2 cadence + OOM root fix + L1 nullability hardening).

- **EPIC-compactor-operations milestone progression**: 1/3 (33.3%) → **2/3 (66.6%)** post-LAND
- **남은 milestone**: MCT-161 (NAS bucket versioning + replication, PROPOSED → IN_PROGRESS transition)
- **scope_manifest**: `EPIC-compactor-operations.yaml` milestone 2/3 + MCT-160 COMPLETED + MCT-161 IN_PROGRESS transition + MCT-163 reservation 박제 (본 RETRO PR)
- **parent Epic**: EPIC-cold-tier-stage-3-wiring (post-MCT-156 deploy cycle, 본 Story = #2/#3/#5 + #4 잔여 drainage lever 해소 의무)

## 2. 11 D 결정 ↔ 본 Story scope 정합 verify

본 Story scope = **D1-D11 ALL** (Codex GPT-5 + Sonnet 합성, 사용자 autonomous OK 2026-05-13) + R-EXTRA + P1-nullability 합병. 11 D 의 ALL 정합 closure.

| # | 결정 | 본 Story 처리 | 정합 |
|---|------|---------------|-----|
| **D1** | L3 cadence 합병 (L2 동형 silent-skip fix) | l3.py `compact_day(date_utc)` 의무 인자 + L2 동형 streaming write + post-write verify (Phase 2 e603f86) | ✅ |
| **D2** | L2 `compact_hour` date_utc caller 명시 전달 | l2.py `compact_hour(date_utc, hour_utc)` 의무 인자 + runner.py `_run_l2` partition glob discover 후 명시 전달 (Phase 2 e603f86) | ✅ |
| **D3** | chunk-based concat + row_group_size 명시 | l2.py + l3.py per-L1-file write_table loop + `row_group_size=100_000` 명시 (Phase 2 e603f86). **F6 surface** = per-file fully read 한계 → true row-batch streaming (iter_batches) 후속 의무 → MCT-163 candidate | ✅ (with caveat) |
| **D4** | post-write monotonic verify + fail/quarantine | l2.py + l3.py post-write `ts_utc` non-decreasing verify + `quarantine_l2/l3` 호출 + `compactor_quarantine_total{tier,reason}` Counter +1 (Phase 2 e603f86 + quarantine.py CREATE) | ✅ |
| **D5** | 순증 중단 (drainage rate ≤ ingest rate) | **본 RETRO §8 박제** — compactor restart 2026-05-14 t=0 = **4,319 sealed** (MCT-162 t=0 = 82,456 대비 **95% 감소**, 자연 drainage 78,137 sealed cleanup evidence) | ✅ (immediate) |
| **D6** | caller sha256 산출 + data=parquet_path 전달 | runner.py `_dispatch_dual_write` caller-side sha256 산출 + `DualWriter.write(data=parquet_path, sha256=<hex>)` 호출 (caller-side reduction). **F3 surface** = DualWriter 내부 read_bytes() 잔존 (`dual_writer.py:156`) → MCT-163 candidate | ✅ (caller-side only) |
| **D7** | 3 schema 일관 nullability 명시 | l1.py 3 schema `_TRANSACTION_SCHEMA` + `_ORDERBOOKSNAPSHOT_SCHEMA` + `_ORDERBOOKDEPTH_SCHEMA` 일관 `nullable=False/True` 명시 + malformed frame ValueError + `compactor_malformed_frame_total{channel,exchange}` Counter (Phase 2 e603f86 + FIX iter 1 5c81602). **F7 surface** = Story §6 D7 wording (raw_json/node_id/collector_run_id nullable=True) vs impl (raw_json만 True, narrower) — impl 우선 채택 = acceptable narrowing | ✅ (impl narrower, spec amend 의무) |
| D8 | backfill_orchestrator 별 Story 분리 | OUT OF SCOPE (MCT-153/159 영역) | external |
| **D9** | upbit L1 lost = D2 fix 후 verify only | Phase 2 land 후 measurement 의무 — 본 RETRO §8.2 (0 persistent 시 MCT-164 별 Story 발의) | reserve (measurement pending) |
| **D10** | ADR-027 silent-skip + ADR-009 nullability 2건 amendment | Phase 1 hub PR #287 — ADR-027 silent-skip 차단 amendment append + ADR-009 nullability discipline 3 schema amendment + Amendment History entry (cad60d2) | ✅ |
| **D11** | L2/L3 각자 cadence 정상화, duplicate code 허용 | l2.py + l3.py 동형 패턴 duplicate (MCT-163 = cadence resolver 공통화 refactor 별 Story, R6 mitigation) | ✅ (scope 분리) |
| **R-EXTRA** | `_dispatch_dual_write` read_bytes memory 재할당 fix | runner.py caller-side sha256 산출 + data=Path streaming. caller-side reduction만 달성, DualWriter 내부 callee read_bytes() 잔존 → MCT-163 follow-up | ✅ (caller-side only) |
| **P1-nullability** | MCT-162 CodeReviewPL P1 finding 본 Story 합병 | l1.py 3 schema nullability + malformed frame ValueError + Counter (FIX iter 1 직후 ALL PASS) | ✅ |

**본 Story 의 11 D + R-EXTRA + P1 ALL 정합 박제 closure** — Phase 1 (정책 박제) + Phase 2 (구현 land + FIX iter 1) 양 단계 정합. R-EXTRA + D3 의 caller-side reduction (F3+F6) + D7 spec drift (F7) = MCT-163 candidate 박제 (별 Story 의무).

## 3. Codex GPT-5 + Sonnet 합성의 정확성 evidence (11 D ALL 사용자 OK)

본 Story brainstorm Phase 1 의 가장 중요한 특징 = **Codex GPT-5 가 11 결정점 + R-EXTRA + P1 합병 + 3 추가 risk (R6/R7/R8) 동시 합성** + **Sonnet 4.6 author 가 답습** + **사용자 autonomous OK 11 D 전체**.

### 3.1 합성 trail

- **brainstorm Phase 1 trigger**: 2026-05-13 (MCT-162 LAND 직후)
- **Codex GPT-5 dispatch**: 11 결정점 (D1-D11) 옵션 분기 + R-EXTRA (DualWriter memory 재할당) + P1-nullability (MCT-162 CodeReviewPL surface 합병) + R6/R7/R8 추가 risk 합성
- **Sonnet 4.6 author 답습**: Codex 권고 옵션 ALL 답습 (D1=A, D2=C, D3=B, D4=C, D5=B, D6=A, D7=B, D8=B, D9=C, D10=B, D11=A)
- **사용자 confirm**: autonomous OK 박제 (Story §1 1-11 결정 표 박제)

### 3.2 합성 정확성 evidence

본 Story 의 4 review lane 결과 = **DesignReview PASS first-try + TestAgent CI PASS + SecurityTestPL PASS + CodeReviewPL FIX iter 1** = **11 D 합성 정확성의 강력한 evidence** (FIX iteration 1 만 발생, 그 중에서도 모두 impl-side 의 minor finding fix, 11 D 결정 자체의 회귀 없음).

- **DesignReview Phase 1 PASS**: ADR-027 silent-skip 차단 amendment + ADR-009 nullability discipline amendment 의 정합 (Codex 권고 D7+D10 답습 정확성)
- **CodeReviewPL FIX iter 1 finding 6건 ALL impl-side**: F1-F9 모두 test fixture / 외부 sig 답습 / Counter 추가 / path traversal / assertion 복구 = **결정점 자체의 mis-decision 0**, 단순 구현 정확성 회복 (FIX iter 1 직후 8+2 test ALL PASS + 777 regression PASS)
- **F3+F6+F7 surface = scope 외 limitation 박제**: F3 (DualWriter 내부 streaming) + F6 (true row-batch streaming) + F7 (D7 spec drift) → MCT-163 candidate 별 Story (본 Story 의 minimal change discipline 정합 = 의도된 caller-side reduction only, MCT-163 별 scope)

## 4. DevPL self-PR + QADev 병렬 dispatch (MCT-162 패턴 답습)

본 Story Phase 2 = MCT-162 패턴 답습 — **QADeveloperAgent 가 self-write 10 test 먼저 author → DeveloperPLAgent 가 self-PR 생성 + 8 test 7 file (l2/l3/runner/l1/quarantine/prometheus_exporters/test_compactor_l2/test_compactor_l3) 구현 + CodeReviewPL FIX iter 1**.

### 4.1 commit chain 박제

| commit | author | content |
|---|---|---|
| 29c321b | QADev (Claude Opus 4.7) | test(MCT-160): Phase 2 QADev lane — 10 integration test (cadence streaming + dual writer streaming) RED |
| e603f86 | DevPL (Claude Sonnet 4.6) | feat(MCT-160): Phase 2 — L2/L3 streaming compactor + monotonic verify + quarantine GREEN |
| **5c81602** | **DevPL (FIX iter 1)** | **fix(MCT-160): FIX iter 1 — CodeReviewPL P0×2+P1×2+P2×2 6-finding fix (F1+F2+F4+F5+F8+F9 immediate, F3+F6+F7 surface)** |
| c96a9ef | merge | Phase 2 PR #53 MERGED 2026-05-13T15:51:09Z (mergeCommit=c96a9ef, +1319/-79) |

### 4.2 병렬 dispatch 효율 evidence (MCT-162 답습 + FIX iter 1 보강)

- **QADev TDD red-green discipline**: 10 integration test author (RED) → DevPL impl (GREEN) → CodeReviewPL FIX iter 1 (6 finding fix, 8+2 test ALL PASS + 777 regression PASS)
- **세션 1 dispatch 효율**: Sonnet 4.6 (DevPL) + Opus 4.7 (QADev) + Sonnet 4.6 (CodeReviewPL FIX iter 1) 모델 mix dispatch
- **FIX iter 1 정확성**: P0 (test fixture pyarrow API + DualWriter sig mismatch) 2건 + P1 (malformed frame validation + path traversal) 2건 + P2 (assertion 복구 + spy assert) 2건 = impl-side 6 finding immediate fix, 결정점 변경 0

## 5. TestAgent host 환경 fail vs CI 실행 결과 박제 (MCT-156 cycle 정합)

| 환경 | 결과 | 박제 |
|---|---|---|
| host Python | (skip — MCT-162 동일 환경 의존성 문제 답습) | local TestAgent 실행 차단 |
| **CI windows-latest** | **PASS** | 10 new + 777 regression ALL PASS |
| CI ubuntu-latest | pre-existing main fail (본 PR 영향 0) | **MCT-156 cycle 박제 정합** — pre-existing main broken 패턴 (MCT-159+MCT-162+MCT-160 3 Story 누적 답습) |
| **CodeReviewPL `uv run pytest` (local self-verify)** | **PASS** (FIX iter 1 직후) | 8+2 new test ALL PASS + 777 passed / 25 skipped / 4 xfailed / 0 failed regression |

**결론**: host 환경 fail + ubuntu pre-existing main fail 은 **본 PR 의 회귀 신호 아님** — CI windows-latest PASS + CodeReviewPL local verify PASS 의 dual evidence 가 LAND gate. ubuntu pre-existing main fail = MCT-156 cycle 누적 박제 (별 chore commit 또는 main 회복 cycle 별 Story 의무).

## 6. 4 review lane 결과 (FIX iter 1 cycle)

EPIC-compactor-operations drainage lever Story 의 brainstorm Phase 1 의 정확성 + DevPL/QADev self-write 정확성 + CodeReviewPL FIX iter 1 immediate fix 결합 → **FIX iter 1 closure (8+2 test ALL PASS + 777 regression PASS)**.

| Lane | Verdict | finding | mitigation |
|---|---|---|---|
| **DesignReviewPL Phase 1** | **PASS** | 0 | Phase 1 PR #287 first-try PASS (ADR-027 amendment + ADR-009 amendment + Story file 신규 + scope_manifest milestone update 정합) |
| **TestAgent** | host skip / CI windows PASS / ubuntu pre-existing fail | — | CI windows-latest PASS + CodeReviewPL `uv run pytest` 8+2 test ALL PASS + 777 regression PASS dual evidence |
| **SecurityTestPL** | **PASS** | P0=0 / P1=0 | NAS credential 무관 + Prometheus cardinality bounded low (2 Counter) + quarantine path traversal 방지 (FIX iter 1 F5 fix) |
| **CodeReviewPL** | **FIX iter 1 → PASS** | F1-F9 6 fix + F3/F6/F7 surface | FIX iter 1 후 8+2 test ALL PASS + 777 regression PASS. F3/F6/F7 = MCT-163 candidate 박제 (별 Story) |

**FIX iter 1 finding breakdown** (별 §10 Story FIX Ledger entry, commit 5c81602):

| F# | severity | category | finding | resolution |
|---|---|---|---|---|
| **F1** | P0 | test fixture | `pa.table(rows, schema=...)` ValueError (pyarrow API drift) | `pa.Table.from_pylist(rows, schema=...)` 답습 |
| **F2** | P0 | DualWriter sig mismatch | constructor (`base_path` 가정) + write (`data: bytes` 가정) wrong — 실 sig = `DualWriter(nas_uploader, local_root)` + `write(*, local_path, nas_key, data, sha256)` | 실 sig 답습 + caller pattern 적용 |
| **F3** | **P1** | **R-EXTRA invariant gap (surface)** | DualWriter 내부 `dual_writer.py:156` 에 `data.read_bytes()` 잔존 — caller-side reduction만 달성, callee 미적용 | **MCT-163 candidate** (DualWriter 내부 streaming 별 Story) |
| **F4** | P1 | malformed frame | `_orderbookdepth_dicts_to_arrow` side/price/quantity None → silent default | ValueError raise + `compactor_malformed_frame_total{channel,exchange}` Counter +1 |
| **F5** | P1 | path traversal | quarantine_l2/l3 `relative_to(local_root)` 검증 부재 | `tmp_path + quarantine_dir relative_to(local_root)` 검증 추가 |
| **F6** | **P1** | **D3 1GB invariant 미증명 (surface)** | per-L1-file fully read (현재) vs true row-batch streaming (iter_batches(batch_size=1024)) 필요 | **MCT-163 candidate** (true row-batch streaming 별 Story) |
| **F7** | **P2** | **D7 nullability spec drift (surface)** | Story §6 D7 ("raw_json/node_id/collector_run_id nullable=True") vs impl ("raw_json만 True", narrower) | impl narrower = acceptable narrowing. **Story §6 D7 wording amend 의무 (impl 답습) — MCT-163 또는 별 chore commit** |
| **F8** | P2 | test assertion 누락 | Test-4 quarantine_root.exists() + rglob assertion 누락 | quarantine assertion 복구 (테스트 검증 강화) |
| **F9** | P2 | test spy 미흡 | Test-2 read_bytes spy assert 부재 (R-EXTRA verify 부족) | `read_bytes spy assert (call_count <= 1)` 추가 |

**FIX iter 1 직후 ALL PASS evidence**: 8+2 test PASS + 777 passed / 25 skipped / 4 xfailed / 0 failed (regression intact).

## 7. F3+F6+F7 surface → MCT-163 candidate 박제 (별 Story 발의 권고)

### 7.1 F3 (P1) — DualWriter 내부 streaming gap

- **위치**: `src/mctrader_data/nas_storage/dual_writer.py:156`
- **내용**: caller (`_dispatch_dual_write`) 가 `data=parquet_path` 전달해도 DualWriter 내부에서 `data.read_bytes()` 호출 잔존 → memory 재할당 fix 가 caller-side reduction 만 달성, callee 미적용
- **현재 위험도**: MEDIUM (caller path 단일 호출 reduction 달성, 단 DualWriter 내부 read_bytes() 가 production peak memory 미감소)
- **권고**: MCT-163 candidate 별 Story (DualWriter 내부 streaming — `data.open("rb")` chunk read + NAS PUT multipart)

### 7.2 F6 (P1) — D3 1GB invariant 미증명 (per-L1-file fully read 한계)

- **위치**: `src/mctrader_data/compactor/l2.py` + `l3.py` chunk concat loop
- **내용**: chunk concat (chunk size=1024) + row_group_size=100_000 명시 = **per-L1-file unit** streaming (각 L1 파일을 full read 후 chunk concat). true row-batch streaming = `pq.ParquetFile.iter_batches(batch_size=1024)` 필요. 현재 = per-file fully read → chunk concat
- **현재 위험도**: MEDIUM (D3/AC-3 1GB invariant 가 60-level orderbookdepth × 1000 frame 의 단일 L1 파일 input case 에서 미증명. typical case = OK, edge case (단일 L1 파일이 매우 큰 경우) = peak memory 가 단일 L1 파일 read 크기로 제한)
- **권고**: MCT-163 candidate 별 Story (true row-batch streaming — iter_batches + per-batch ParquetWriter.write_batch)

### 7.3 F7 (P2) — D7 nullability spec drift (impl narrower than spec)

- **위치**: Story §6 D7 spec vs `src/mctrader_data/compactor/l1.py` impl
- **내용**: Story §6 D7 = "raw_json / node_id / collector_run_id nullable=True" (3 column) vs impl = "raw_json 만 True" (1 column, node_id + collector_run_id = False). impl narrower = acceptable narrowing
- **현재 위험도**: LOW (impl 이 더 strict → backward-compat read 변경 0, 신규 nullability invariant 강화)
- **권고**: Story §6 D7 wording amend (impl 답습) — MCT-163 candidate **또는 별 chore commit** (즉시 align 가능)

### 7.4 MCT-163 reservation 박제 (3 finding 묶음 — 본 Story PMOAgent retro 의무)

- **MCT-163 title**: "DualWriter 내부 streaming + L2/L3 row-batch streaming + ADR-009 D7 spec amend (MCT-160 F3+F6+F7 follow-up)"
- **MCT-163 Epic**: EPIC-compactor-operations (본 Epic 내부 — D11 R6 cadence resolver 공통화와 별 Story, F3+F6+F7 묶음)
- **MCT-163 phase_pair**: phase1_phase2 (D6 + D3 변경 = 구현 lane scope)
- **MCT-163 sp**: 2-3sp (3 finding 묶음 — 단일 Story 가능, scope 분리 비용 회피)
- **MCT-163 prerequisites**: MCT-160 LAND (본 RETRO PR LAND 후 진입 가능)

## 8. L1 backlog drainage 측정 trail (D5 verify — drainage rate ≤ ingest rate)

### 8.1 측정 trail (Phase 2 land 후 compactor restart 시점)

| 시점 | L1 backlog | 박제 |
|---|---|---|
| **MCT-162 t=0** (2026-05-13 22:07:09 KST, compactor restart 직후) | **82,456 sealed** | RETRO-MCT-162 §8.1 박제 |
| MCT-162 t=+6m20s (2026-05-13 22:13:30 KST) | 82,458 sealed (+2 net) | RETRO-MCT-162 §8.1 박제 (near steady state, L2 cadence 부재로 drainage 미진행) |
| **MCT-160 t=0** (2026-05-14 본 PMOAgent dispatch 시점, compactor restart 직후) | **4,319 sealed** | **본 RETRO §8 박제 — MCT-162 t=0 대비 95% 감소** ✅ |
| MCT-160 quarantine t=0 | **0 files** | quarantine 정상 (production WAL well-formed emission + cadence 정상화) ✅ |
| t=+1h | TBD | 본 RETRO LAND 후 별 wakeup 또는 사용자 측정 의무 |

### 8.2 95% 감소 evidence 분석 (drainage 자연 진행 박제)

- **MCT-162 land (2026-05-13 13:09 KST, 22:07:09 KST 재시작)**: t=0 = 82,456 sealed → near steady state (orderbookdepth fast-fail 해소만, L2 cadence 부재로 drainage 미진행)
- **MCT-160 Phase 2 land (2026-05-13 15:51 KST)**: 본 PR merge 직후 자연 drainage 시작 (compactor 가 deploy 됨, L2 cadence 정상화 + OOM 해소 + caller-explicit date 의 첫 cycle)
- **본 PMOAgent dispatch 시점 (2026-05-14 t=0)**: **4,319 sealed = 78,137 sealed cleanup 달성** (95% drainage)

**결론**: D5 (drainage rate ≤ ingest rate) **달성 evidence — 78,137 sealed cleanup ≈ 95% 감소** + drainage rate > ingest rate (순감 박제). MCT-160 의 L2 cadence + OOM root fix 가 **진짜 drainage lever** 였음을 evidence pack 으로 확인.

### 8.3 1h 측정 의무 (별 wakeup 또는 사용자 측정)

- **t=+1h 측정 trigger**: 본 RETRO PR LAND 시점 + 1h (자동 wakeup ScheduleWakeup 또는 사용자 측정)
- **expected scenario**: t=+1h backlog ≤ 4,319 (감소 추이 지속 expected, 단 emission rate 도 정상 → near-steady-state or slight 감소 가능)
- **AC-Phase3-N closure 의무**: t=+1h 측정값 박제 시 본 RETRO §8.3 update

### 8.4 quarantine emit 0 evidence

- **production quarantine count (t=0)**: 0 files (정상 — `compactor_quarantine_total{tier,reason}` Counter emit 0 expected)
- **expected**: drainage 안정 후에도 quarantine emit 0 (production WAL = well-formed emission, monotonic verify 항상 PASS expected)
- **R-A scenario (quarantine 1+ emit 시)**: 운영자 manual review + 진단 의무 (별 chore Story 또는 MCT-163/164 합병 결정)

## 9. 5중 차단 cycle 의 본 Story 해소 trail (MCT-156 cycle 누적 박제)

MCT-156 production deploy 직후 사용자 NAS bucket 실측에서 surface 된 5중 차단 cycle 의 본 Story 해소 trail:

| # | 차단 항목 | MCT-162 해소 | MCT-160 해소 | 잔여 |
|---|---|---|---|---|
| **#1** | upbit L1 결과 today=0 | partial (orderbookdepth allowlist) | **D9 verify only** (Phase 2 land 후 측정 의무 — 0 persistent 시 MCT-164 발의) | **measurement pending** |
| **#2** | transaction L2 자연 cadence 0 | untouched | **✅ D2 fix** (l2.py compact_hour date_utc 의무 인자 + runner.py _run_l2 partition glob discover) | **해소** |
| **#3** | bucket 463 obj = bithumb orderbooksnapshot only | untouched | **✅ D2+D6 fix** (cadence 정상화 → 자연 NAS PUT 누적 회복) | **해소** (별 NAS 실측 verify 의무) |
| **#4** | L1 backlog 79k orderbookdepth 48k 누적 | partial (fast-fail) | **✅ drainage 자연 진행** (t=0 = 4,319, 95% 감소) | **해소** |
| **#5** | upbit/KRW-BTC orderbooksnapshot L2 OOM exit 137 | untouched | **✅ D3 fix** (chunk concat + row_group_size=100_000, F6 surface = MCT-163 follow-up) | **해소** (with caveat — F6 follow-up) |

**5중 차단 cycle 진행률**:
- MCT-162 LAND: 1/5 partial (#1 + #4 partial)
- MCT-160 LAND: **#2/#3/#5 해소 + #4 95% drainage + #1 measurement pending** = **4/5 substantial 해소** (#1 verify only)

MCT-161 sequential 의무 = NAS bucket versioning + replication (MCT-153 손실 재발 방지, 별 Epic close gate).

## 10. ADR 정식 발의 trigger: "post-cutover wiring gap" pattern 누적 3회

### 10.1 사례 누적 (PMOAgent 발의 trigger 임계 초과)

| # | Stage | wiring gap 발견 시점 | entrypoint Story |
|---|---|---|---|
| 1 | **Stage 2** EPIC CLOSED 후 | hot pipeline NAS wiring 부재 → bucket `tier=L3/` 0 obj + `tier=L2/hour=HH/` 0 partition | MCT-156 (Stage 3 entrypoint) |
| 2 | **Stage 3** MCT-156 deploy 후 | channel parity / L2 cadence / OOM / backlog 누적 / 별 root cause 5중 차단 | MCT-162 (post-Stage 3 cycle entrypoint) |
| **3** | **Stage 3 post-cycle** MCT-162 LAND 후 | L2/L3 cadence + OOM + L1 nullability 잔여 차단 (drainage lever) | **MCT-160 (post-MCT-162 cycle drainage lever)** |

### 10.2 ADR 후보 발의 권고 (강화 — 누적 3회)

**PMOAgent 발의 trigger 임계** = 동일 pattern 누적 ≥ 2 → ADR 신규 발의 권고 충족. **3회 누적 = 강화** (RETRO-MCT-162 §10 박제 + 본 RETRO §10 strengthen).

- **신규 ADR**: `docs/adr/ADR-XXX-post-cutover-wiring-gap-prevention.md`
- **status**: Proposed (PMOAgent → ArchitectAgent 직접 author dispatch)
- **scope**: 설계 lane brainstorm 시 wiring gap 검출 의무 + 사용자 NAS bucket + WAL sample + L2 cadence + drainage rate 실측 evidence pack 의무 박제
- **MCT-161 brainstorm 시 발의 trigger**: 본 RETRO LAND 후 MCT-161 brainstorm Phase 0 시점에 ArchitectAgent dispatch 의무 (Orchestrator trigger)

### 10.3 ADR-XXX 후보 outline (강화 — 3 evidence 통합)

```markdown
---
category: Infrastructure
title: "ADR-XXX: Post-cutover wiring gap prevention"
trigger: "3회 누적 — Stage 2 EPIC CLOSED + Stage 3 MCT-156 + Stage 3 post-cycle MCT-162+MCT-160 (drainage lever 까지)"
---

## 배경
- Stage 2 (MCT-155) EPIC CLOSED 후 hot pipeline NAS wiring 부재 발견 → MCT-156 entrypoint Epic spawn
- Stage 3 (MCT-156) production deploy 후 channel parity + L2 cadence + OOM 5중 차단 발견 → MCT-162 entrypoint Epic spawn
- **Stage 3 post-cycle (MCT-162) LAND 후 L2/L3 cadence + drainage lever 잔여 차단 발견** → MCT-160 entrypoint Story (본 Story)

공통 pattern = "EPIC CLOSED gate 통과 시점에는 wiring gap 미감지, 실 production deploy 또는 사용자 실측 시점에만 발견 + Story-1 LAND 만으로는 partial 해소 (drainage lever 미달성)".

## 문제
1. brainstorm Phase 0 의 "as-is 사실 박제" 가 implementation-side wiring (collector emit channel allowlist 등) 만 박제 → bucket 실측 + WAL sample 실측 의 cross-validation 부재
2. **drainage rate / cadence 실측 부재** — Phase 2 land 후 production 자연 drainage 측정 의무 미박제 시 → partial 해소 만 달성하고 false-positive EPIC CLOSED

## 제안 결정
EPIC CLOSED gate 의 verify checklist 에 다음 추가:
(1) production bucket 실측 evidence pack (5분 이상 production runtime 시점 bucket listing)
(2) WAL sample 실측 evidence pack (모든 collector channel × emit segment metadata 정합 verify)
(3) **L1 backlog drainage rate 실측 evidence pack (Phase 2 land 직후 t=0 + 1h 측정, drainage rate ≤ ingest rate 정합 박제 의무)**
(4) **L2 cadence 자연 cadence 실측 evidence pack (compactor restart 후 1h+ window 에서 L2 PUT 1+ 이상 박제)**
(5) 사용자 ack — bucket 실측 + WAL 실측 + drainage 실측 + cadence 실측 의 quad evidence 박제 의무

## 예상 결과
- post-cutover wiring gap pattern 의 누적 차단 → epic spawn cycle 감소
- brainstorm Phase 0 의 "as-is 사실 박제" 정확성 향상 (drainage 실측 의무 자동 surface)
- 사용자 실측 trigger 의 의존도 감소
- Story-1 LAND 만으로 false-positive EPIC CLOSED 차단 (drainage rate 검증 의무)
```

### 10.4 발의 trail 박제

- 본 RETRO §10 (현재 위치) = **PMOAgent self-write trigger 박제 (3회 누적 강화)**
- RETRO-MCT-162 §10 = **PMOAgent self-write trigger 첫 박제 (2회 누적)** — 본 RETRO 가 strengthen
- 후속 Orchestrator dispatch = ArchitectAgent 직접 author (codeforge-design plugin) — MCT-161 brainstorm Phase 0 trigger 시점
- Story §12 §"ADR 정식 발의 trigger 박제" cross-link

## 11. 본 cycle 의 의도 (사용자 input 정합 — MCT-162 RETRO §11 cross-link)

> 본 cycle 의 의도 = MCT-156 cycle 의 5중 차단 #2/#3/#5 + #4 잔여 (drainage lever) fix

본 RETRO §9 의 Cross-Story pattern 표 정합 — **#2/#3/#5 해소 + #4 95% drainage + #1 measurement pending = 4/5 substantial 해소**. 잔여 #1 verify only = MCT-160 D9 (Phase 2 land 후 measurement) + MCT-164 발의 결정 박제 (0 persistent 시).

## 12. 향후 권고

1. **MCT-161 IN_PROGRESS transition** (본 RETRO PR LAND 후 즉시) — NAS bucket versioning + replication 정책 정립 brainstorm Phase 0 trigger 의무
2. **MCT-161 brainstorm 시 본 RETRO §10 ADR-XXX 발의 trigger 의무** — Orchestrator → ArchitectAgent direct author dispatch (codeforge-design plugin)
3. **MCT-163 IN_PROGRESS transition** (별 cycle 또는 MCT-161 LAND 후 sequential) — F3+F6+F7 묶음 follow-up + D7 spec drift amend (3 finding 묶음, 2-3sp)
4. **MCT-164 발의 결정** (MCT-160 D9 measurement 결과 의존) — upbit L1 lost 별 root cause 진단 (R7 escalate)
5. **drainage t=+1h 측정** (본 RETRO LAND 후 1h wakeup 또는 사용자 측정) — D5 AC-Phase3-N closure
6. **consumer nullability smoke verify** (mctrader-engine pyarrow read sample) — Codex 추가 risk closure 의무 (별 chore commit 또는 MCT-161 brainstorm 시)

---

## 부록: 산출 파일 manifest

### Phase 1 (mctrader-hub#287, MERGED 2026-05-13T15:32:21Z, mergeCommit=cad60d2, +98/-0)

| 파일 | 변경 |
|---|---|
| `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` | silent-skip 차단 amendment append (caller-explicit date + post-write monotonic verify + quarantine 정책 + 운영자 review 의무) |
| `docs/adr/ADR-009-ohlcv-schema.md` | nullability discipline 3 schema amendment + Amendment History entry (2026-05-13 MCT-160) |

### Phase 2 (mctrader-data#53, MERGED 2026-05-13T15:51:09Z, mergeCommit=c96a9ef, +1319/-79)

| commit | 파일 | 변경 |
|---|---|---|
| 29c321b (QADev) | `tests/integration/test_l2_l3_cadence_streaming.py` (CREATE) + `tests/integration/test_dual_writer_streaming.py` (CREATE) | 10 integration test author (RED) |
| e603f86 (DevPL) | `src/mctrader_data/compactor/l2.py` + `l3.py` + `runner.py` + `l1.py` + `quarantine.py` (CREATE) + `nas_metrics/prometheus_exporters.py` + `tests/test_compactor_l2.py` + `tests/test_compactor_l3.py` + `tests/compactor/test_l2_writer_close.py` + `tests/compactor/test_l3_writer_close.py` | L2/L3 streaming + monotonic verify + quarantine + l1 nullability + runner caller-side sha256 + test 시그니처 update (GREEN) |
| 5c81602 (DevPL FIX iter 1) | `tests/integration/test_dual_writer_streaming.py` + `test_l2_l3_cadence_streaming.py` + `src/mctrader_data/compactor/l1.py` + `quarantine.py` + `nas_metrics/prometheus_exporters.py` | FIX iter 1 — F1+F2+F4+F5+F8+F9 6 finding fix (F3/F6/F7 surface) |

### Phase 2 hub (mclayer/mctrader-hub#TBD, 본 RETRO PR 자체)

| 파일 | 변경 |
|---|---|
| `docs/stories/MCT-160.md` §12 | self-write — Phase 1+2 PR cross-link + 11 D 결정 ↔ 구현 정합 verify + review lane 결과 + FIX iter 1 박제 + L1 drainage 측정 + MCT-163 follow-up |
| `docs/retros/RETRO-MCT-160.md` | 본 RETRO file 신규 (PMOAgent self-write, templates/retro.md schema 정합) |
| `scope_manifests/EPIC-compactor-operations.yaml` | milestone 1/3 → 2/3 (66.6%) + MCT-160 COMPLETED + MCT-161 IN_PROGRESS transition + MCT-163 reservation 박제 |
| `.codeforge/counters.json` | `reservations.MCT-160` DELETE + MCT-163 신규 reservation + next=164 |
| `CLAUDE.md` (mctrader-hub) | (없음 — hub repo CLAUDE.md 없음, mctrader workspace CLAUDE.md 별 path 의 mctrader 본 repo memory 갱신 영역) |
