---
type: story-retro
story_key: MCT-171
epic_key: EPIC-tier-promotion-single-source
status: COMPLETED
completed_at: "2026-05-14"
sp: 5
---

# RETRO — MCT-171 DR runbook 본문 + invariant 8종 확장 + 4 layer capacity 제한 정책 (D4+D5+D6+D11, EPIC-tier-promotion-single-source Story-5)

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

EPIC-tier-promotion-single-source 의 **운영 안전성 박제 Story** (phase1_phase2, cross-repo 2 PR sequential).

ADR-029 D4=B (WAL sealed local only) + D5=A_modified (capacity-bounded ingest block) + D6=B (bucket versioning, MCT-161 prerequisite LAND) + D11 (4 layer capacity: WAL 30G / L1 20G / NAS 500G target+1TB hard / Host 200G hard) owner Story. mctrader-data 측 `capacity_probe.py` 신규 + `ingest_blocker.py` 신규 + `invariant_harness.py` 8번째 invariant 통합 + `prometheus_exporters.py` +5 metric 확장 + `collector.py` IngestBlocker hook + `promotion.py` DEPRECATED 주석. 38 신규 통합 test + 931 회귀 ALL PASS.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + DR runbook 본문) | mctrader-hub#317 + #318 MERGED (Phase 2 PR2 본 PR, 2026-05-14) |
| Phase 2 PR#1 (data invariant+capacity+blocker) | mctrader-data#62 MERGED (3fb9d60, 2026-05-14T12:20:08Z) |
| Phase 2 PR#2 (hub 박제, 본 PR) | mctrader-hub#317 (3399abd) + #318 (0b25975) MERGED 2026-05-14 |
| 총 AC | 5/5 PASS (AC-1~5) |
| 총 INV | 6/6 PASS (INV-1~6) |
| 산출물 | data 6 신규/확장 + 3 test 파일 / hub docs 박제 |
| 총 신규 테스트 | 38 (test_invariant_harness_8: 8 + test_capacity_probe: 15 + test_ingest_blocker: 15) ALL PASS |
| 회귀 | 0 (MCT-152/153/155/169 D10 회귀 0 + 931 passed) |
| FIX 루프 | 3회 (ruff lint 3-pass + pyright type 2-pass) |
| D4+D5+D11 verify | ADR-029 §D4/§D5/§D11 verify status entry 박제 (Phase 2 PR2) |
| D6 verify | bucket versioning ✓ (MCT-161 LAND 확인), cross-NAS = MCT-174 defer (mcnas02 미설치) |
| Epic milestone | 5/6 박제 (MCT-167 + MCT-168 + MCT-169 + MCT-170 + MCT-171 COMPLETED) |

## §1 Story 개요 + Phase 0 verify 발견

### 1.1 Phase 0 verify 발견 (path discrepancy 박제)

session prompt (MCT-171-session-prompt.md) 가설 vs 실 코드 verify:

1. ✅ DR runbook stub 341 lines, line 275-328 = 본 Story author 영역.
2. ⚠️ **Path discrepancy 1**: InvariantHarness 실 위치 = `nas_migration/invariant_harness.py` (prompt 의 `nas_storage/` 정정). 7종 SSOT 확인.
3. ⚠️ **Path discrepancy 2**: collector = `collector.py` 단일 468 lines (prompt 의 `collector/dir` 정정). `capacity_probe.py` sibling 확인.
4. ✅ WAL module = `wal/` dir. D11 WAL 30G = segment.py rotate threshold 정합.
5. ⚠️ **Ambiguity invariant 분산** — `compactor/promotion.py` 단독, InvariantHarness 외부. D7-1=A 채택 = InvariantHarness 통합 (status enum 9 variant + `_INVARIANT_NAMES` 8개).
6. ❌ **Production data dir 부재** (host-local 측정 부재). WAL/L1 baseline = synthetic/mock으로 대체.

### 1.2 Story 동기

MCT-169 (immediate local delete + ambiguity invariant) LAND 후 단계. 운영 안전성 박제의 4종 축:

1. **D4=B**: WAL sealed segment NAS PUT 금지 (사용자 directive). RPO=0 = D1 (L1 ParquetWriter atomic NAS PUT) 단독 의존.
2. **D5=A_modified**: capacity-bounded ingest block — WAL 30G/L1 20G 도달 시에만 block. 정상 운영 시 hot path 영향 0 (ADR-017 §D5 정합).
3. **D6=B verify**: bucket versioning ✓ (MCT-161 LAND). cross-NAS replication = MCT-174 defer (mcnas02 물리 미설치).
4. **D11**: 80%/95% hysteresis 4 layer + Prometheus Gauge + graceful drain 후 reject.

## §2 결정 D7-1~D7-9 (Codex 권고 합성)

| D7-N | 채택 Option | 결과 |
|------|------------|------|
| D7-1 invariant_harness 확장 | A — 기존 InvariantHarness 통합 | 8종 SSOT 단일 (promotion.py 분산 흡수). MCT-152/153/155 caller 회귀 0. |
| D7-2 capacity_probe 위치 | A — `capacity_probe.py` 단독 | collector.py sibling, hot path/exporter 의존 0. |
| D7-3 enforcement timing | B — 1h periodic sweep | D5 hot path 영향 0 정합. detection lag 1h = 허용. |
| D7-4 probe 주기 | C — hybrid (5min + approach continuous) | WAL >= 80% 진입 시 15s interval 전이. |
| D7-5 block 정책 | B — graceful drain 후 reject | in-flight WAL write 완료 후 신규 ingest reject. |
| D7-6 Prometheus metric | mandatory 3종 + violation Counter + latency Histogram | label = invariant_name 8 enum + layer 4 enum (cardinality 제한 enforce). |
| D7-7 DR runbook priority | (2)>(1)>(4)>(3)>(5) | disk full → mode (2) 하위 명시. clock drift = ambiguity trigger 가능 명시. |
| D7-8 WAL 30G fallback | C — 80%/95% hysteresis | 80% warn + aggressive L1 rotate, 95% graceful block. unblock at 90%. |
| D7-9 Host 200G 강제 | A+C bridge | Prometheus bridge alert (단기). LVM infra quota = 별 task (미완, R6 유지). |

## §3 진행 timeline

| 시각 | 작업 | 결과 |
|------|------|------|
| 2026-05-14 (mid) | Phase 1 PR (hub docs + DR runbook 본문 확장 + spec + plan) | hub#317 MERGED (3399abd) |
| 2026-05-14 (mid-late) | Phase 2 PR1 (data) — 6 file 신규/확장 + 3 test 파일 | data#62 MERGED (3fb9d60, 12:20Z) |
| 2026-05-14 (late) | Phase 2 PR2 (hub 박제) — RETRO + §8.5 + ADR verify + scope_manifest + CLAUDE.md | hub#318 MERGED (0b25975) |

**FIX 루프 3회 (ruff + pyright)**:

1. **FIX-MCT-171-001 (ruff pass 1)**: E501 (line too long 120) + E741 (ambiguous `l`) + SIM105 (contextlib.suppress) + SIM108 (ternary) + B905 (zip strict) + F401 (unused import). 자동 fix + 수동 보완.
2. **FIX-MCT-171-002 (ruff pass 2)**: F841 (unused variable: `sha`, `result`) + UP037 (string annotation quotes). hashlib 제거, tick_schema rename.
3. **FIX-MCT-171-003 (pyright pass)**: `-> object` → `TYPE_CHECKING` forward ref 패턴. `MagicMock cast_ingester` type: ignore[assignment]. `_schema: pa.Schema =` narrowing. 502 Bad Gateway → `--squash --admin --delete-branch` retry.

## §4 AC-1 ~ AC-5 verify status

| AC | 설명 | Test | 결과 |
|----|------|------|------|
| AC-1 | invariant 8종 enforcement (D7-1=A + D7-3=B) | test_invariant_harness_8.py (8 tests) | **PASS** |
| AC-2 | capacity_probe hybrid timing (D7-2=A + D7-4=C) | test_capacity_probe.py (15 tests) | **PASS** |
| AC-3 | ingest_blocker graceful drain (D7-5=B + D7-8=C) | test_ingest_blocker.py (15 tests) | **PASS** |
| AC-4 | DR runbook 본문 (D7-7) | phase1 PR review (runbook 본문 5 fail mode + 8종 invariant + 4 layer) | **PASS** |
| AC-5 | Prometheus metric design (D7-6) | test_capacity_probe + test_ingest_blocker Gauge/Counter/Histogram verify | **PASS** |

## §5 INV-1 ~ INV-6 verify status

| INV | 설명 | 결과 |
|-----|------|------|
| INV-1 (D4 WAL local only) | WAL sealed segment NAS PUT 금지 (사용자 directive) | **PASS** — promotion.py DEPRECATED 주석 + WAL sealed 경로 NAS PUT 0 verify |
| INV-2 (D5 hot path 영향 0) | 정상 운영 시 collector hot path 영향 0 | **PASS** — capacity_probe = sibling module, probe loop hot path 미접근 |
| INV-3 (D11 hard limit 정확성) | 4 layer hard limit (WAL 30G + L1 20G + NAS 1TB + Host 200G) | **PASS** — CapacityThresholds SSOT + test verify |
| INV-4 (8종 backward compat) | MCT-152/153/155 caller integration test ALL PASS | **PASS** — 931 passed 회귀 0 (MCT-169 D3+D10 포함) |
| INV-5 (DR runbook actionable) | 5 fail mode 본문 step-by-step placeholder 0건 | **PASS** — Phase 1 PR runbook 본문 expand |
| INV-6 (cardinality 제한) | Prometheus label = 8 enum + 4 enum hardcoded enforce | **PASS** — prometheus_exporters.py label list hardcoded |

## §6 위험 R1-R6 해소 결과

| R | severity | 결과 |
|---|----------|------|
| R-CRITICAL | HIGH (WAL 30G 산정 근거 미검증) | **미완** — production 측정 없음. synthetic mock 대체. 30G 초과 risk = D11 amendment trigger (MCT-172 Epic CLOSE 전 측정 의무 carry over) |
| R1 | HIGH (invariant 8번째 통합 회귀) | **PASS** — 931 passed 회귀 0. promotion.py backward compat 유지 (DEPRECATED 주석만) |
| R2 | HIGH (capacity_probe hot path 영향) | **PASS** — sibling module + 5min probe + exporter 의존 0 |
| R3 | MID (ingest_blocker graceful drain 일관성) | **PASS** — test_ingest_blocker drain_then_reject verify |
| R4 | MID (Prometheus label cardinality drift) | **PASS** — hardcoded enum list, free-form label 검출 fail-fast |
| R5 | LOW (DR runbook priority drift) | **PASS** — (2)>(1)>(4)>(3)>(5) + disk full mode(2) 하위 + clock drift ambiguity 박제 |
| R6 | LOW (D7-9 Host 200G bridge alert only) | **OPEN** — LVM quota 설정 미완 (별 infra task 예약, MCT-172 scope 외) |

## §7 PMO 관찰 + 다음 Story 권고

### 7.1 PMO 관찰

1. **FIX 루프 3회**: ruff E501 + E741 + SIM105 + SIM108 + B905 + F401 → F841 + UP037 → pyright forward ref 패턴. 3회가 필요했던 이유 = 신규 모듈 3개 (capacity_probe + ingest_blocker + test 3) 동시 작성 시 lint/type 통합 검증 지연. 교훈: 모듈 단위 lint pass 즉시 의무.
2. **GitHub 502 Bad Gateway**: `gh pr merge --squash` 1차 실패 → `--squash --admin --delete-branch` retry 성공. 패턴 박제 (memory feedback_admin_merge_autonomy 정합).
3. **R-CRITICAL 미완**: WAL 30G 산정 = production 측정 없이 가정치. MCT-172 Epic CLOSE 전 collector runtime probe 의무 (carry over).
4. **promotion.py 처리**: DEPRECATED 주석만 추가 (module 삭제 0) — MCT-172 Epic smoke test 이후 cleanup 권고.

### 7.2 다음 Story 진입 조건

**MCT-172** (Epic CLOSED, D9+D10 verify + D8 sunset finalize) — MCT-171 COMPLETED 후 진입 가능.
- D9=A (MCT-161+163 prerequisite sequential) verify + D10=A (ambiguity invariant enforcement) cross-Story verify
- D8 sunset criterion 상태 확인 (2026-09-01 cutoff + telemetry 0-hit 14d)
- promotion.py cleanup + WAL 30G production measurement 의무 carry over
- Epic CLOSE 후 EPIC-RESULTS entry 박제

### 7.3 MCT-174 replication reserve

D6 cross-NAS replication = MCT-174 defer (mcnas02 물리 미설치). MCT-174 reservation = `.codeforge/counters.json` RESERVED. Epic 진입 조건 = mcnas02 물리 설치 완료.

## §8 측정 결과

### 8.1 신규 test 38개 전수 PASS

| 파일 | test 수 | 결과 |
|------|---------|------|
| `tests/integration/test_invariant_harness_8.py` | 8 | PASS |
| `tests/integration/test_capacity_probe.py` | 15 | PASS |
| `tests/integration/test_ingest_blocker.py` | 15 | PASS |
| 합계 | 38 | ALL PASS |

### 8.2 회귀 결과

- 전체 931 passed, 0 failed (CI ubuntu-latest + windows-latest)
- MCT-152/153/155 caller backward compat 회귀 0
- MCT-169 D3+D10 invariant test 회귀 0

### 8.3 D4+D5+D11 verify (ADR-029 박제)

- **D4=B VERIFIED**: WAL sealed segment NAS PUT 없음. `promotion.py` DEPRECATED 주석 박제. WAL wal/ module NAS 호출 코드 0 (grep verify).
- **D5=A_modified VERIFIED**: `ingest_blocker.py` collector hook 통합. 95% threshold block → 90% unblock hysteresis. graceful drain test PASS.
- **D11=capacity_bounded VERIFIED**: `capacity_probe.py` 4 layer probe. `CapacityThresholds` SSOT (WAL 30G / L1 20G / NAS 1TB hard / Host 200G). `prometheus_exporters.py` 5 metric 확장 (capacity Gauge + threshold Gauge + violation Counter + latency Histogram + ingest blocked Counter).

### 8.4 WAL 30G 산정 미측정 (R-CRITICAL 유지)

Production data dir 부재로 peak burst fill rate 미측정. 50 sym × 3 channel × 12 seg/h 가정치 유지. MCT-172 Epic CLOSE 전 collector runtime probe baseline 측정 의무.
