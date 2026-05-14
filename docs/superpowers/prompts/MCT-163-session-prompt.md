# MCT-163 별 세션 prompt — DualWriter 내부 streaming + L2/L3 row-batch + ADR-009 D7 spec amend

> **사용법**: 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 에서 본 파일 전체 내용을 paste. Claude 가 자동으로 brainstorm Phase 0 → spec/plan → Phase 1 → Phase 2 → PMO retro cycle 진행.

---

## 작업 instruction (paste 시작)

MCT-163 cycle 자율 진행. EPIC-compactor-operations follow-up Story.

### 사용자 directive (autonomous)

본 Story 는 EPIC-tier-promotion-single-source (별 Epic) 의 prerequisite. 본 cycle 만 자율 진행 + 종료 보고. 시간 압박, 적극 병렬 진행.

### Story scope (counters.json 박제 정합)

`.codeforge/counters.json` 의 MCT-163 reservation:

> "DualWriter 내부 streaming + L2/L3 row-batch streaming + ADR-009 D7 spec amend (MCT-160 F3+F6+F7 follow-up)"
> rationale: "MCT-160 RETRO §7 surface (F3+F6+F7 3 finding 묶음). F3 (P1 DualWriter 내부 read_bytes 잔존, caller-side reduction만 달성 — dual_writer.py:156) + F6 (P1 true row-batch streaming = iter_batches(batch_size=1024) 필요, per-L1-file fully read 한계, D3/AC-3 1GB invariant 미증명) + F7 (P2 D7 nullability spec drift — Story §6 wording 'raw_json/node_id/collector_run_id nullable=True' vs impl 'raw_json만 True', impl narrower acceptable)."

### Background

MCT-160 cycle 의 CodeReviewPL FIX iter 1 에서 surface 한 3 finding:

#### F3 (P1) DualWriter 내부 read_bytes 잔존

- 위치: `mctrader-data/src/mctrader_data/nas_storage/dual_writer.py:156`
- 문제: `DualWriter.write(data=Path)` 가 즉시 `data.read_bytes()` 호출 → `tmp_path.write_bytes(payload)` (line 172) → `NASUploader.put(...,payload,...)` 까지 전체 parquet bytes 1회 fully materialize
- MCT-160 D6/AC-5 spec "memory 재할당 1회 → 0회" claim 미달성 (caller-side reduction 만 달성)
- fix path: DualWriter 내부 `open(path,"rb")` chunk loop + NASUploader streaming put_object (multipart upload 또는 chunked PUT)

#### F6 (P1) true row-batch streaming 미달성

- 위치: `mctrader-data/src/mctrader_data/compactor/l2.py:75` / `l3.py:75`
- 문제: `for f in l1_files: tbl = pq.ParquetFile(str(f)).read()` — 각 L1 file 을 fully load. 단일 L1 file 이 ≤ 1GB 라는 사전조건 0 (orderbookdepth 60-level × N frame raw_json large_string → 단일 파일 GB 단위 가능).
- MCT-160 D3/AC-3 spec "1GB memory invariant" 미증명
- fix path: `iter_batches(batch_size=1024)` API 도입 → per-batch streaming write

#### F7 (P2) D7 nullability spec drift

- MCT-160 Story §6 D7 본문 = "nullable=True 허용 = raw_json / node_id / collector_run_id (metadata)"
- 실 impl (MCT-160 commit 5c81602) = `raw_json` 만 nullable=True, `node_id` + `collector_run_id` 는 nullable=False
- impl 이 spec 보다 narrower (acceptable narrowing) — Story §6 D7 wording amend 의무

### 작업 흐름 (codeforge 표준 cycle)

#### Phase 0: brainstorm 자동 진입

```
codeforge:codeforge-brainstorm 호출 시 ARGUMENTS:

MCT-163 — DualWriter 내부 streaming + L2/L3 row-batch streaming + ADR-009 D7 spec amend

## Scope
- F3 fix: DualWriter 내부 read_bytes 제거 → chunk streaming PUT
- F6 fix: L2/L3 compactor true row-batch streaming (iter_batches API)
- F7 fix: ADR-009 §D2.7 nullability discipline wording amend (impl narrower 정합)

## 핵심 결정점 (예상)
1. DualWriter streaming PUT 방식 — boto3 multipart upload vs chunked PUT
2. NASUploader.put 의 streaming signature 변경 (data: bytes → data: bytes | Iterator[bytes])
3. iter_batches batch_size = 1024 vs 4096 vs file size 기반 dynamic
4. memory invariant 측정 — Test 본문에 psutil peak memory ≤ 1GB assertion 의무
5. ADR-009 §D2.7 amendment wording (impl narrower 채택 vs spec 답습)
6. backward compat — 기존 NASUploader.put(data=bytes) 호환 유지 의무

## 참고 자료
- MCT-160 RETRO-MCT-160.md §7 (F3+F6+F7 surface 박제)
- mctrader-data/src/mctrader_data/nas_storage/dual_writer.py (현재 152-180 line, read_bytes 잔존 위치)
- mctrader-data/src/mctrader_data/compactor/l2.py + l3.py (compact_hour/compact_day, 75-95 line streaming write)
- mctrader-hub/docs/adr/ADR-009-ohlcv-schema.md §D2.7 (nullability discipline)
- mctrader-hub/docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md D4 amendment (MCT-160 amend, streaming write 정책)

## Cross-Epic 의존
- 본 Story 는 EPIC-tier-promotion-single-source 의 prerequisite (L1 NAS PUT latency 완화 필수). 본 Story LAND 후 MCT-167 (governance singleton) 진입 가능.

## 의무
- Phase 0 4-agent burst → Codex review → Sonnet 합성 → 사용자 final OK → PMO 2nd pass → spec/plan → Phase 1 worktree + ArchitectPL + DesignReview + merge → Phase 2 worktree + DevPL + QADev + Test + Security + CodeReview + merge → PMOAgent retro
- 사용자 명시 "시간 없다 + 적극 병렬" + "Always subagent-driven execution" + "Admin merge autonomy" + "CI failure auto-recovery" 정합
- Issue 생성 + counters.json reservations.MCT-163 DELETE (Phase 2 §11) + scope_manifests/EPIC-compactor-operations.yaml 갱신 + RETRO-MCT-163.md 신규 + CLAUDE.md 후속 섹션
- Codex 권고 일괄 dispatch 패턴 (Q-by-Q 사용자 stop 금지)
```

#### Phase 1: ArchitectPL dispatch (worktree mct-163-phase1-architect)

ADR amendment:
- ADR-009 §D2.7 amend (nullability discipline wording — `raw_json` 만 nullable=True 박제, impl narrower 정합)
- ADR-027 D4 amend trail append (streaming write 정책 — boto3 multipart 또는 chunked PUT 박제, F3 fix)

Story §1-§11.

#### Phase 2: DevPL + QADev parallel dispatch

**DevPL 산출**:

- `mctrader-data/src/mctrader_data/nas_storage/dual_writer.py`:
  - `write()` 내부 `read_bytes()` 제거
  - `open(path,"rb") + iter(chunk)` streaming
  - `NASUploader.put_streaming(local_path, nas_key, sha256)` 호출 (multipart upload)
- `mctrader-data/src/mctrader_data/nas_storage/nas_uploader.py`:
  - `put_streaming` 메소드 신규 (boto3 multipart_upload API)
- `mctrader-data/src/mctrader_data/compactor/l2.py + l3.py`:
  - `compact_hour/compact_day` 의 `for f in l1_files: tbl = pq.ParquetFile(f).read()` → `pq.ParquetFile(f).iter_batches(batch_size=1024)` per-batch streaming write
  - `ParquetWriter.write_batch(batch, row_group_size=100_000)` per-batch

**QADev 산출**:

- `tests/integration/test_dual_writer_streaming_v2.py` 신규:
  - `test_dual_writer_no_read_bytes` — mock spy 로 `Path.read_bytes` 호출 0 verify
  - `test_dual_writer_chunk_streaming` — payload large (60-105 MiB) 시 peak memory ≤ 50 MB invariant (psutil)
- `tests/integration/test_l2_l3_row_batch_streaming.py` 신규:
  - `test_l2_iter_batches_memory_invariant` — large L1 file (1GB+) 시 L2 compact_hour peak memory ≤ 256 MB invariant
  - `test_l3_iter_batches_memory_invariant` — 동형

#### Phase 2 PMOAgent retro

RETRO-MCT-163.md 신규 + Story §12 + counters DELETE + scope_manifest milestone update + CLAUDE.md.

EPIC-compactor-operations milestone 3/4 → 4/4 (MCT-161 land 후) 또는 본 Story LAND 시 milestone update.

### 진행 메모

- 사용자 명시 "시간 없다 + 적극 병렬" — DesignReviewPL + preflight + worktree 생성 + DevPL/QADev parallel + TestAgent + Security/CodeReview parallel + 2 PR merge 모두 가능한 한 병렬 dispatch.
- 본 Story = code-heavy (DualWriter signature 변경 + L2/L3 compact_hour streaming refactor). 신중한 backward compat 검증 의무.
- preflight stop compactor (Phase 2 진입 직전 의무).

### 산출 후 보고 의무

(a) Phase 1 + Phase 2 PR # + merge commit
(b) 4 review lane 결과
(c) memory invariant 측정 결과 (DualWriter ≤ 50 MB + L2/L3 ≤ 256 MB)
(d) backward compat verify (기존 test_dual_writer / test_compactor_l2/l3 ALL PASS)
(e) compactor 재시작 + drainage 측정 (streaming 효과 verify)

---

## paste 끝 — 별 세션에서 Claude 가 자동 진행

본 prompt 가 self-contained. 사용자가 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 열고 paste 만 하면 cycle 자율 진행 가능.

소요 시간 추정: brainstorm 30min + spec/plan 30min + Phase 1 1-2h + Phase 2 3-5h (code-heavy) + PMO retro 30min = **~5-9h 총 소요**.
