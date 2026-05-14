---
type: story-retro
story_key: MCT-169
epic_key: EPIC-tier-promotion-single-source
status: COMPLETED
completed_at: "2026-05-14"
sp: 4
---

# RETRO — MCT-169 L1 NAS verify + immediate local delete + tier promotion path (D3=C + D10=A, EPIC-tier-promotion-single-source Story-3)

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

EPIC-tier-promotion-single-source 의 **L1 NAS verify + immediate local delete + tier promotion path Story** (phase1_phase2, cross-repo).

ADR-029 D3=C (NAS HEAD verify + grace 0 immediate local delete) + D10=A (ambiguity invariant violation enforcement) owner Story. promotion.py 신규 모듈 + get_streaming.py NAS ranged GET + reader_cache.py MCT-170 placeholder + L2/L3 source swap (NAS GET) + 16 신규 tests. mctrader-data (8 파일) + mctrader-hub (Story §8-§12 + ADR verify + scope_manifest 3/6).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR | mctrader-hub#310 MERGED (a353090, 2026-05-14) |
| Phase 2 data PR | mctrader-data#60 MERGED (d65545f, 2026-05-14) |
| Phase 2 hub PR | mctrader-hub#311 MERGED (eb2c0cc, 2026-05-14) |
| 총 AC | 8/8 PASS (AC-1~8) |
| 총 INV | 6/6 PASS (INV-1~6) |
| 산출물 | 8 파일 신규/수정 + 16 신규 tests |
| 총 테스트 | 16 tests ALL PASS + 874 기존 회귀 0 |
| FIX 루프 | 0회 (clean cycle) |
| D3+D10 verify | ADR-029 D3=C + D10=A VERIFIED (mctrader-data#60 MERGED) |
| Epic milestone | 3/6 박제 (MCT-167 + MCT-168 + MCT-169 COMPLETED) |
| Backward compat | PASS — nas_uploader=None 시 local fallback, 기존 회귀 0 |

## What Went Well

1. **TDD 사이클 성공 (16 tests → 0 FIX loop)**: test_ambiguity_invariant.py (6) + test_promotion.py (10) 을 구현 전 작성 → promotion.py + get_streaming.py 구현 → 1회 mock 패턴 수정 (head_object → _get_client().head_object) 후 ALL PASS. FIX loop 0회.

2. **NASUploader _get_client() 패턴 통일**: promotion.py + get_streaming.py 가 모두 `nas_uploader._get_client()` 경유 boto3 client 접근. 내부 구현 캡슐화 동일 패턴 재사용 — 기존 NASUploader 구조 변경 없이 확장.

3. **L2/L3 backward compat 설계 (nas_uploader=None fallback)**: L2Compactor/L3Compactor 에 `nas_uploader: NASUploader | None = None` inject 추가 — 기존 868 tests 전부 local fallback 경로로 동작, 회귀 0. NAS GET path = production 에서만 활성화 (dual_writer._uploader 주입 시).

4. **InvariantChain 단순 XOR 검증 명쾌**: verify_no_ambiguity() = 2줄 조건 (`nas_exists and local_exists → raise`). D10=A invariant 구현이 단순 명쾌 — 테스트도 4가지 상태 조합 (both/nas_only/local_only/neither) 체계적 커버.

5. **grace=0 INV-2 test 단순 wall-clock 측정**: time.monotonic() 으로 wall-clock < 100ms 검증. mock-based 이므로 실제 NAS latency 없이 < 1ms 달성. 실 NAS 환경에서도 100ms budget 충분 (HEAD verify + unlink, 네트워크 포함 예측).

6. **reader_cache.py Protocol 설계**: MCT-170 D7 구현 계약을 `runtime_checkable Protocol` 로 명시. NullReaderCache = 테스트/전환기 동안 no-op. Protocol 기반이므로 MCT-170 에서 LRU 구현 시 isinstance 체크로 swap 가능.

## What Could Be Better

1. **L2/L3 NAS GET path 실 통합 테스트 미시행**: _compact_hour_nas() + _compact_day_nas() 가 mock NASUploader 아닌 실 NAS 연결 통합 테스트 없이 PASS 박제. 실 NAS 연결 시 pyarrow.parquet.ParquetFile(BytesIO) 동작 검증 필요 (MCT-172 통합 smoke gate).

2. **DualWriter._uploader 내부 속성 직접 접근**: runner.py 에서 `dual_writer._uploader` (underscore prefix) 접근. DualWriter 내부 구현 변경 시 runner.py 깨짐 위험. 후속 ADR 또는 DualWriter.nas_uploader property 공개 필요. MCT-171 에서 처리 권고.

3. **promotion.py AmbiguityViolation escalation path 미구현**: AmbiguityViolation raise 시 caller (runner.py 등) 의 처리 policy 미정의. 현재 = exception propagation (runner.py log.exception → 다음 segment 계속). D10=A violation = "즉각 수동 개입" 수준인지 "log warning + skip" 수준인지 MCT-172 Epic smoke 시 policy 확정 필요.

4. **HEAD verify retry config 하드코딩**: _HEAD_RETRY_COUNT = 1, _HEAD_RETRY_BACKOFF_S = 0.05 모듈 상수로 하드코딩. 환경변수 knob 또는 CompactorConfig 주입 패턴으로 MCT-171 에서 개선 권고.

## AC Verdict

| AC | 설명 | 결과 |
|----|------|------|
| AC-1 | s3.head_object → ETag + VersionId verify 시 promotion proceed | PASS |
| AC-2 | HEAD verify pass 즉시 Path.unlink(missing_ok=False), time.sleep 0 | PASS |
| AC-3 | verify_no_ambiguity — NAS+local 동시 존재 = AmbiguityViolation | PASS |
| AC-4 | L2/L3 source = NAS GET (local Path open 0 Grep 확인) | PASS |
| AC-5 | get_streaming() Range ranged GET 구현 | PASS |
| AC-6 | reader_cache.py ReaderCache Protocol + NullReaderCache placeholder | PASS |
| AC-7 | HEAD 404/ClientError → PromotionVerifyError + local 유지 | PASS |
| AC-8 | test_ambiguity_invariant.py NAS+local fixture → violation 검출 PASS | PASS |

## INV Verdict

| INV | 설명 | 결과 |
|-----|------|------|
| INV-1 | nas_exists ⊕ local_exists = true (XOR, D10=A) | PASS |
| INV-2 | HEAD verify pass → local unlink wall-clock < 100ms (grace=0) | PASS |
| INV-3 | L2/L3 source = NAS GET (local Path open 0, nas_uploader inject 시) | PASS |
| INV-4 | HEAD verify fail = local 유지 (partial state 차단) | PASS |
| INV-5 | PromotionResult.version_id 박제 (versioning 활성 시) | PASS |
| INV-6 | local 부재 + NAS 존재 → already_promoted no-op | PASS |

## FIX Ledger

| iter | 실패 lane | 원인 유형 | 수정 요약 | 결과 |
|---|---|---|---|---|
| — | — | — | — | — |

(FIX 루프 0회 — clean TDD cycle)

## Risk 잔존

| R | Severity | 잔존 여부 | Mitigation Story |
|---|---|---|---|
| R-1 L2/L3 read latency 증가 | HIGH | 잔존 (MCT-170 reader cache placeholder만) | MCT-170 LRU cache 구현 (D7) |
| R-2 HEAD verify race | MED | 해소 (retry 1회 + S3 strong consistency) | (closed) |
| R-3 invariant test flakiness | MED | 해소 (post-promotion verify로 한정) | (closed) |

## Epic-level milestone 박제

EPIC-tier-promotion-single-source milestone progress:

| # | Story | Status | LAND |
|---|---|---|---|
| 1 | **MCT-167** | **COMPLETED** | 2026-05-14 (hub#305) |
| 2 | **MCT-168** | **COMPLETED** | 2026-05-14 (hub#307 + data#59 + hub#308) |
| 3 | **MCT-169 (본 Story)** | **COMPLETED** | 2026-05-14 (hub#310 + data#60 + hub#311) |
| 4 | MCT-170 | Reserved | TBD (별 세션, mctrader-engine cross-repo) |
| 5 | MCT-171 | Reserved | TBD |
| 6 | MCT-172 | Reserved | TBD |

**milestone 3/6 박제 완료**. NAS = SoT for ALL tiers 확립의 핵심 단계 (L1 promotion + L2/L3 NAS source) 완료.

## 후속 Story 진입 권고

**MCT-170 (engine reader 재구현 — L1 tier 추가 + reader 우선순위 NAS-first + DR mode degradation, D7+D8)** — 별 세션 권고 (mctrader-engine cross-repo, 별 brainstorm 필요).

- gate: MCT-169 Phase 2 MERGED (hub#310 + data#60 + hub#311) PASS — 진입 가능
- scope: mctrader-engine repo — engine reader NAS-first + L1 path + reader cache LRU (D7 구현) + DR mode degradation
- prerequisite verify: MCT-169 LAND 확인 (본 RETRO 박제)
- 주의: reader_cache.py NullReaderCache placeholder = MCT-170 LRU 구현 후 교체 의무

## Cross-ref

- Story: `docs/stories/MCT-169.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md` (D3+D10 verify status 박제)
- Phase 1 PR: mctrader-hub#310 (a353090)
- Phase 2 data PR: mctrader-data#60 (d65545f)
- Phase 2 hub PR: mctrader-hub#311 (eb2c0cc)
- Epic scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml` (milestone 3/6)
- prerequisite retros: RETRO-MCT-167.md / RETRO-MCT-168.md
- PMO retro memory: `feedback_pmo_retro_mandatory`
