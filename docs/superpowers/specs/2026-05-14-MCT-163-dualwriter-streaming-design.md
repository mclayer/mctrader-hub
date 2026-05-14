---
story: MCT-163
title: DualWriter put_streaming + L2/L3 iter_batches + ADR-009 §D2.7 amend (MCT-160 F3+F6+F7 fix)
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
phase_1_decider: Codex (GPT-5.4) + Sonnet
trigger: MCT-160 F3+F6+F7 carry surface + EPIC-tier-promotion D9 last prerequisite
status: spec
---

# MCT-163 — DualWriter streaming + L2/L3 row-batch + ADR-009 amend

## 1. Why

사용자 prompt 자료 paste. MCT-160 spec claim 미증명 영역 3건 해소 + EPIC-tier-promotion D9 마지막 prerequisite.

- F3: dual_writer.py:156 `data.read_bytes()` 잔존 → MCT-160 NFR-2 "memory 재할당 0회" claim 미달성 (caller-side only)
- F6: l2.py/l3.py:75 `pq.ParquetFile(f).read()` fully load → MCT-160 D3 "1GB memory invariant" 미증명, orderbookdepth raw_json GB scale OOM 재발 risk
- F7: ADR-009 §D2.7 wording vs impl narrower (raw_json only nullable=True, 나머지 metadata nullable=False) — MCT-160 Story §6 D7 wording drift 만, ADR 본문은 이미 정합

## 2. Phase 0 Context

### DomainAgent
- ADR-017/027 §D5 hot path 무영향 (F3/F6/F7 cold path 한정)
- ADR-027 §D6 7종 invariant per-file (sha256 multipart ETag ≠ sha256, caller-side 별 hash 의무)
- ADR-009 §D11.9 raw_json large_string cast (F6 OOM root cause)
- 지식 공백: NAS MinIO multipart 호환 미검증 / iter_batches row_group boundary memory profile / orderbookdepth raw_json 실측 distribution

### ResearcherAgent
- 핵심 3: boto3 upload_fileobj+TransferConfig idiomatic / iter_batches batch_size=1024 OLAP standard / Backward compat via isinstance Union normalize
- Unknowns 2: psutil RSS vs tracemalloc heap 정확도 (병행 권장) / NAS MinIO multipart 호환 PoC 필요

### RequirementsAnalystAgent
- WHY: MCT-160 claim 정합 + ADR drift 해소 + L2/L3 OOM 회귀 차단
- AC: F3 chunk concat vs row-batch / F6 caller-side 단일 read vs DualWriter 내부 hash+write / F7 ADR narrower amend
- Edge: partial batch global sort 일관성 / malformed frame ValueError

### PMOAgent
- 1 Story (분리 비추천 5 reason)
- EPIC-compactor-operations CLOSED post-close follow-up
- HIGH risk: backward compat NASUploader.put(bytes) signature 보존 + DualWriter.put external caller surface

## 3. Phase 1 — 9 결정점 (Codex + Sonnet)

| D | 결정 | 핵심 |
|---|---|---|
| D1 | B | boto3 upload_fileobj + TransferConfig (multipart idiomatic) |
| D2 | A | caller-side single sha256 (MCT-160 D6 정합, ETag 의미 오염 회피) |
| D3 | A | 별 `put_streaming(Path|fileobj)` method (backward compat 격리) |
| D4 | A | iter_batches batch_size=1024 (OLAP, MCT-160 정합) |
| D5 | A | per-batch write_batch (true streaming, B는 F6 무력화) |
| D6 | C | psutil RSS + tracemalloc + delta-based assert (병행) |
| D7 | A | impl 답습 narrower (raw_json only nullable=True) |
| D8 | B | 기존 integration test extend (B 균형점) |
| D9 | A | 1 Story (분리 비추천) |

## 4. AC (6)

- **AC-1 (F3 chunk streaming)**: Given DualWriter.put_streaming(path), When 105 MiB payload, Then `Path.read_bytes()` 호출 0 + multipart 완료 + caller-side sha256 metadata header 검증 PASS
- **AC-2 (F3 backward compat)**: Given 기존 NASUploader.put(data=bytes), When 호출, Then 기존 contract 그대로 작동 (test_dual_writer 회귀 0)
- **AC-3 (F6 iter_batches)**: Given L1 file 1 GiB+ (orderbookdepth raw_json), When `compact_hour` 실행, Then `pq.ParquetFile.read()` 호출 0 + per-batch write_batch + peak memory ≤ 256 MB (RSS + tracemalloc delta)
- **AC-4 (F6 schema 정합)**: Given iter_batches per-batch write, When ParquetWriter close, Then 산출물 schema == 기존 L2/L3 schema (forward-only invariant)
- **AC-5 (F7 ADR amend + MCT-160 §6 D7 wording)**: Given ADR-009 §D2.7 amendment + MCT-160 Story §6 D7 wording impl narrower 박제, Then ADR-009 History entry + MCT-160 §6 D7 wording = "raw_json only nullable=True" 정합
- **AC-6 (Test extend D8=B)**: Given existing `tests/integration/test_dual_writer.py`, When MCT-163 test 추가, Then 신규 streaming path + memory invariant + backward compat 3 케이스 cover

### Edge (2)
- partial batch global sort 일관성
- malformed frame ValueError (essential column null → raise)

## 5. INV (5)

- **INV-1**: Hot path 무영향 (ADR-017/027 §D5) — collector/L1 latency 영향 0
- **INV-2**: Backward compat — NASUploader.put(data=bytes) signature 보존
- **INV-3**: sha256 SSOT — caller-side single hash (multipart ETag ≠ sha256)
- **INV-4**: Memory invariant — DualWriter ≤ 50 MB / L2/L3 ≤ 256 MB (peak RSS + tracemalloc delta)
- **INV-5**: Schema 정합 — iter_batches per-batch write 산출물 schema == 기존 L2/L3 schema (forward-only)

## 6. Risk (3)

- **R1 (High)**: NASUploader.put backward compat 위반 시 L1 ingestion caller 회귀. **완화**: Phase 2 Grep "NASUploader.*put\(" full-repo + AC-2 회귀 test 의무
- **R2 (Mid)**: NAS MinIO multipart 미지원 fallback 필요 시 D1=B 채택 무력화. **완화**: D8=B integration test extend 에 multipart 호환 검증 commit + ListMultipartUploads endpoint 응답 선검증
- **R3 (Low)**: psutil RSS vs tracemalloc 측정 mismatch. **완화**: D6=C 양쪽 + delta-based assert (절대값 X)

## 7. Phase 분할

| Phase | 산출물 | PR |
|---|---|---|
| Phase 1 | spec + plan + Story §1-§7 + ADR-009 §D2.7 amendment + MCT-160 §6 D7 wording amend + counters | hub Phase 1 |
| Phase 2.1 (preflight) | docker compose stop compactor + Grep caller inventory | data Phase 2 PR (audit commit) |
| Phase 2.2 (F3) | NASUploader.put_streaming + DualWriter streaming refactor + tests | data Phase 2 PR (F3 commit) |
| Phase 2.3 (F6) | L2/L3 compact_hour/compact_day iter_batches per-batch + tests | data Phase 2 PR (F6 commit) |
| Phase 2.4 (verify) | memory invariant test (RSS+tracemalloc) + backward compat 회귀 + compactor restart | data Phase 2 PR (verify commit) |
| Phase 2 hub | Story §8-§12 + CLAUDE.md + RETRO + EPIC-tier-promotion D9 prerequisite cross-ref | hub Phase 2 PR |

## 8. scope_manifest

```yaml
planned_adrs:
  amendment: [ADR-009 §D2.7 — MCT-163 history append + impl narrower 명시]
  reservation_only: []

planned_files:
  mctrader-data:
    - src/mctrader_data/nas_storage/dual_writer.py: F3 — put_streaming caller chain
    - src/mctrader_data/nas_storage/nas_uploader.py: F3 — put_streaming(Path|fileobj) 신규 method (D3=A)
    - src/mctrader_data/compactor/l2.py: F6 — iter_batches per-batch
    - src/mctrader_data/compactor/l3.py: F6 — 동형
    - tests/integration/test_dual_writer_streaming_v2.py: AC-1/INV-3/INV-4
    - tests/integration/test_l2_l3_row_batch_streaming.py: AC-3/INV-4
    - tests/integration/test_dual_writer.py: 기존 backward compat 회귀 (AC-2)
    - CLAUDE.md: §streaming refactor + §memory invariant

  mctrader-hub:
    - docs/stories/MCT-163.md
    - docs/superpowers/specs/2026-05-14-MCT-163-dualwriter-streaming-design.md
    - docs/superpowers/plans/2026-05-14-mct-163-dualwriter-streaming.md
    - docs/adr/ADR-009-ohlcv-schema.md: History + §D2.7 amendment (MCT-163 박제)
    - docs/stories/MCT-160.md: §6 D7 wording amend (raw_json only nullable=True)
    - docs/retros/RETRO-MCT-163.md
    - CLAUDE.md: §streaming refactor cross-ref
    - .codeforge/counters.json: MCT-163 title 확장 + retitle_history
```

## 9. Cross-ref

- MCT-160 §6 D7 (F7 wording amend 대상) + §7 F3+F6+F7 carry surface
- MCT-161 (sibling, EPIC-compactor-operations CLOSED 후 post-close follow-up)
- MCT-167 (EPIC-tier-promotion, 본 Story land 시 D9 prerequisite 100% 충족)
- ADR-009 §D2.7 (amendment 대상) + §D11.9 (raw_json large_string)
- ADR-017/027 §D5 (hot path 무영향)
- ADR-027 §D6 (7종 invariant per-file)
- EPIC-compactor-operations CLOSED (post-close follow-up)
- EPIC-tier-promotion-single-source D9 prerequisite
