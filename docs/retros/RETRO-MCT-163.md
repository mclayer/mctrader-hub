---
type: story-retro
story_key: MCT-163
epic_key: EPIC-compactor-operations
status: COMPLETED
completed_at: "2026-05-14"
sp: 3
---

# RETRO — MCT-163 DualWriter put_streaming + L2/L3 iter_batches

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

MCT-160 F3+F6+F7 carry surface fix + EPIC-tier-promotion D9 마지막 prerequisite.

- **F3**: dual_writer.py read_bytes 잔존 → put_streaming streaming 전환 (MCT-160 NFR-2 claim 증명)
- **F6**: l2.py/l3.py pq.ParquetFile.read() fully load → iter_batches per-batch (MCT-160 D3 claim 증명)
- **F7**: ADR-009 §D2.7 wording drift → amendment (Phase 1 완료)

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR | mctrader-hub#303 MERGED (cad60d2) |
| Phase 2 data PR | mctrader-data#58 MERGED (d740920) |
| Phase 2 hub PR | TBD (본 RETRO 포함 PR) |
| 총 AC | 6/6 PASS |
| 총 테스트 | 22/22 PASS |
| FIX 루프 | 1회 (pyright type ignore — 재설계 없음) |
| D9 prerequisite | 100% 충족 |

## What Went Well

1. **TDD 엄격 준수**: failing test → impl → pass 사이클 정확히 수행
2. **Backward compat 격리**: put_streaming 신규 method + put() 보존 → R1 HIGH risk 완화
3. **Memory invariant 실측**: D6=C delta-based 접근이 정확하고 빠름 (0.2MB / 0.0MB)
4. **iter_batches 효과**: 300k rows 기준 TM delta = 0.3 MB (기존 ~180 MB 전체 로드 대비 ~600x 개선)
5. **Caller inventory 선행**: Phase 2.1 Grep audit 가 R1 HIGH risk 조기 확인에 유효

## What Could Be Better

1. **read_bytes 0회 달성**: 현재 구현은 sha256 verify 를 open+iter로 수행해 read_bytes 0 달성. 초기 구현에서 read_bytes 1회를 잘못 남겼다가 수정 (TDD가 잡아냄)
2. **pyright MagicMock type**: mock spec으로 NASUploader를 사용하면 put_streaming이 MagicMock에서 MethodType으로 resolve되어 call_count/call_args 접근 시 pyright error 발생 → `# type: ignore` 필요 (pre-emptive 대응 가능했음)
3. **test_l2_l3_row_batch_streaming.py 파일 생성 시간**: L1 300k rows 생성에 ~54초 소요 → @slow marker 적용으로 CI fast-path 분리 가능

## AC Verdict

| AC | 설명 | 결과 |
|----|------|------|
| AC-1 | F3 chunk streaming (read_bytes 0) | PASS |
| AC-2 | F3 backward compat | PASS |
| AC-3 | F6 iter_batches peak ≤ 256 MB | PASS |
| AC-4 | F6 schema 정합 (INV-5) | PASS |
| AC-5 | F7 ADR-009 §D2.7 amendment | PASS (Phase 1) |
| AC-6 | Test extend D8=B | PASS |

## Memory Invariant 측정 결과 (INV-4)

| Target | 임계값 | RSS delta | TM delta | PASS |
|--------|--------|-----------|----------|------|
| DualWriter (105 MiB) | ≤ 50 MB | 0.2 MB | 0.0 MB | PASS |
| L2Compactor (300k rows) | ≤ 256 MB | 0.0 MB | 0.3 MB | PASS |
| L3Compactor (300k rows) | ≤ 256 MB | 0.0 MB | 0.3 MB | PASS |

## EPIC-tier-promotion D9 prerequisite 충족

- MCT-161 LAND (2026-05-14): EPIC-compactor-operations 마지막 Story
- MCT-163 LAND (2026-05-14): F3+F6+F7 carry surface fix
- **MCT-167 (EPIC-tier-promotion) 진입 가능**: D9 prerequisite = MCT-161 + MCT-163 모두 COMPLETED

## 후속 Story (필요 시)

| ID | 제목 | 우선순위 | 비고 |
|----|------|---------|------|
| MCT-167 | EPIC-tier-promotion governance | HIGH | D9 prerequisite 100% 충족 → 즉시 진입 가능 |
| MCT-174 | NAS replication | LOW | single NAS box 해소 후 (D2=D deferred) |

## 9 D 요약

| D | 결정 | 결과 |
|---|------|------|
| D1 | B (boto3 upload_fileobj + TransferConfig) | 적합 — streaming effective |
| D2 | A (caller sha256 SSOT) | 적합 — INV-3 정합 |
| D3 | A (put_streaming 별 method) | 적합 — INV-2 격리 |
| D4 | A (iter_batches 1024) | 적합 — OLAP standard, 효과 실증 |
| D5 | A (per-batch write_batch) | 적합 — true streaming |
| D6 | C (psutil + tracemalloc delta) | 적합 — 정확하고 빠름 |
| D7 | A (impl narrower, raw_json only) | 적합 — Phase 1 wording 수정 |
| D8 | B (기존 test extend) | 적합 — regression 0 |
| D9 | A (1 Story) | 적합 — 분리 비추천 이유 타당 |
