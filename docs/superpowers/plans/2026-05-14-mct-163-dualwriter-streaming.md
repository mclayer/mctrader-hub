# MCT-163 DualWriter streaming + L2/L3 row-batch Plan

> Subagent-Driven execution.

**Goal:** MCT-160 F3+F6+F7 carry fix. F3 DualWriter put_streaming (boto3 upload_fileobj + caller sha256) + F6 L2/L3 iter_batches per-batch write_batch + F7 ADR-009 §D2.7 + MCT-160 §6 D7 wording amend.

**Architecture:** 1 Story (D9=A, 분리 비추천). Phase 1 hub docs only (ADR amend + Story + MCT-160 wording fix). Phase 2 mctrader-data 4 commit (preflight / F3 / F6 / verify). Phase 2 hub PR (박제 + RETRO).

**Spec:** [specs/2026-05-14-MCT-163-dualwriter-streaming-design.md](../specs/2026-05-14-MCT-163-dualwriter-streaming-design.md)

## File Structure

### mctrader-hub
- docs/stories/MCT-163.md (§1-§12)
- docs/adr/ADR-009-ohlcv-schema.md (History + §D2.7 MCT-163 amendment 1 줄)
- docs/stories/MCT-160.md (§6 D7 wording amend — raw_json only nullable=True 명시)
- .codeforge/counters.json (title 확장)
- docs/retros/RETRO-MCT-163.md
- CLAUDE.md (§streaming + §memory invariant)

### mctrader-data (Phase 2)
- src/mctrader_data/nas_storage/nas_uploader.py (put_streaming method 신규, D3=A)
- src/mctrader_data/nas_storage/dual_writer.py (write() 내부 read_bytes 제거, put_streaming caller)
- src/mctrader_data/compactor/l2.py (iter_batches per-batch write_batch, D4=A D5=A)
- src/mctrader_data/compactor/l3.py (동형)
- tests/integration/test_dual_writer_streaming_v2.py (AC-1/INV-3/INV-4)
- tests/integration/test_l2_l3_row_batch_streaming.py (AC-3/INV-4)

## Task 1: Phase 1 hub PR

- [ ] **Step 1**: branch + counters (이미 완료)
- [ ] **Step 2**: ADR-009 §D2.7 amend (History 1 줄 + 본문 amendment block 1)
- [ ] **Step 3**: MCT-160 §6 D7 wording amend (Story file edit — "raw_json/node_id/collector_run_id nullable=True" → "raw_json only nullable=True, node_id/collector_run_id nullable=False (impl narrower)")
- [ ] **Step 4**: Story file MCT-163.md §1-§7
- [ ] **Step 5**: commit + push + PR + label + DesignReviewPL + admin merge

## Task 2: Phase 2.1 preflight + caller inventory (mctrader-data)

- [ ] **Step 1**: `docker compose -f compose.yml stop compactor` (preflight 의무, R1 회귀 방지)
- [ ] **Step 2**: `Grep "NASUploader.*put\(" mctrader-data/src/` full-repo scan — 기존 caller inventory 박제

## Task 3: Phase 2.2 F3 NASUploader.put_streaming + DualWriter refactor

- [ ] **Step 1 (TDD)**: failing test `tests/integration/test_dual_writer_streaming_v2.py`:
  - `test_dual_writer_no_read_bytes` (mock Path.read_bytes 호출 0)
  - `test_dual_writer_streaming_memory_invariant` (105 MiB payload, peak RSS + tracemalloc delta ≤ 50 MB, INV-4)
  - `test_dual_writer_caller_sha256_metadata` (D2=A, sha256 metadata header 검증)
- [ ] **Step 2**: NASUploader.put_streaming(local_path|fileobj, nas_key, sha256) 신규 method (D3=A, boto3 upload_fileobj + TransferConfig)
- [ ] **Step 3**: DualWriter.write 내부 read_bytes 제거 → put_streaming 호출
- [ ] **Step 4**: 기존 test_dual_writer.py 회귀 0 (AC-2 backward compat)
- [ ] **Step 5**: commit

## Task 4: Phase 2.3 F6 L2/L3 iter_batches

- [ ] **Step 1 (TDD)**: failing test `tests/integration/test_l2_l3_row_batch_streaming.py`:
  - `test_l2_iter_batches_memory_invariant` (1 GiB+ L1 file, peak ≤ 256 MB, INV-4)
  - `test_l3_iter_batches_memory_invariant` (동형)
- [ ] **Step 2**: l2.py/l3.py `pq.ParquetFile(f).read()` → `iter_batches(batch_size=1024)` per-batch
- [ ] **Step 3**: ParquetWriter.write_batch incremental (D5=A)
- [ ] **Step 4**: 기존 test_compactor_l2/l3 회귀 0
- [ ] **Step 5**: commit

## Task 5: Phase 2.4 verify + compactor restart

- [ ] **Step 1**: memory invariant verify (RSS + tracemalloc delta-based assert)
- [ ] **Step 2**: backward compat 회귀 test 전체 PASS
- [ ] **Step 3**: `docker compose -f compose.yml restart compactor` + drainage 측정 (streaming 효과 verify)
- [ ] **Step 4**: commit + mctrader-data Phase 2 PR open + CodeReview/TestAgent/Security parallel + CI green + admin merge

## Task 6: Phase 2 hub PR

- [ ] Story §8-§12 박제 (Test Contract / FIX Ledger + memory invariant 측정 결과 / Invariant / PMO retro)
- [ ] CLAUDE.md §streaming refactor + §memory invariant
- [ ] RETRO-MCT-163.md
- [ ] EPIC-tier-promotion D9 prerequisite 100% 충족 cross-ref 박제
- [ ] hub Phase 2 PR open → DesignReviewPL → CI → admin merge

## Execution: Subagent-Driven
