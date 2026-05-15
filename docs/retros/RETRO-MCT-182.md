# RETRO MCT-182 — Layer 0 Contract Relocation → mctrader-market

> **EPIC-data-domain-decoupling sequential_phase 1 (milestone 1/7)** · COMPLETED 2026-05-15
> brainstorm 2026-05-16 → all-lane LAND 2026-05-15 (codeforge-brainstorm + 6-lane Story flow autonomous run)

## 1. 결과 요약

| 항목 | 결과 |
|------|------|
| AC | **6/6 PASS** (aggregation byte-equiv / records dataclass+pyarrow 비결합 / paper_lineage hash 동등 / CandleModel 4곳+grep0 / shim DeprecationWarning+is-동일성 / ADR-031 Proposed→Accepted+D-row 7/7 reconcile) |
| INV | **6/6 PASS** (byte-equiv / market→data 0 영구 / pyarrow 비결합 / SSOT 단일 is-동일성 / 재구현 0 / writer 무변경) |
| 신규 test | **72** (market 47 + data 18 + data fix1 5 + engine 2) ALL PASS |
| 회귀 cross-repo | 신규 실패 0 (market 156 / data 871 / engine 990) |
| FIX 루프 | 설계리뷰 iter1/3 PASS + 구현리뷰 iter1/3 PASS (둘 다 max 3 미달) |
| 영향 PR | hub#349 + market#11 + data#68 + engine#57 + hub#350(§8.5) + data#69(fix1) + hub Phase2 PR2 |

## 2. brainstorm + 설계 정합성 (자율 실행)

사용자 단일 지시 "시작해라" + 메모리(autonomous/subagent-driven/admin-merge autonomy)로 codeforge-brainstorm Phase 0 (4 에이전트 병렬) → Codex 9 결정점 일괄 → 3-repo transitive deep-verify → why-first 5R dialog → **4-Layer 다중거래소 확장 아키텍처** 확정. spec/scope_manifest(7 Story)/counters/plan/Story flow 6 lane 전 과정 게이트 없이 자율 진행. 사용자 개입 = brainstorm 의 가치 판단 fork 4건만(why/hot-path/contract owner/repo split/scope), 그 외 모든 기술 결정점은 Codex 일괄 review→Claude 합성(Sonnet decider 0).

## 3. Phase 0 deep-verify 정정 2건 (R1 가드 작동)

| # | 가설 | 실측 | 정정 시점 |
|---|------|------|-----------|
| **A** | engine CandleModel import 5곳 | **4곳** (candle_view.py:38=docstring 오집계) | MCT-182 요구사항 lane (코드 작업 전) |
| **B** | scope_manifest planned_files data `aggregation.py (shim)` flat | 실제 = 패키지 `aggregation/__init__.py` (core/scaled_int/contract_metadata 하위모듈) | 설계리뷰 FIX iter1 (ArchitectPL 회귀) |

가설↔실상 desync 2건 모두 **코드 영구 영향 전에 사전 차단** — docker-stack Epic Phase 0 verify gap 6회 누적 → 본 Epic 7회째 사전 차단 R1 가드 의도대로 작동.

## 4. FIX 루프 (lesson 기반 자기 정정)

### 4.1 설계리뷰 iter 1/3 — scope_manifest SSOT 결함 (P0×2, MCT-179 lesson)

- F-1: scope_manifest R1.mitigation '5곳 grep 실증' 잔존 (Phase0 SSOT 4곳 정정 후 1곳 누락) — R1 가드 자체의 self-contradiction
- F-2: planned_files data `aggregation.py (shim)` flat 모듈 표기 (실제 = 패키지) + paper_lineage/tick_storage/orderbook_storage data-side entry 누락
- 원인 = 설계 (DesignReview P0 → 항상 설계, root-cause-decision)
- 해소: ArchitectPL 직접 회귀 (deputy 재spawn 0, code-logic 무변경) → scope_manifest 텍스트 5곳 정합 + ADR-031 D-row owner_story annotated 통일 + ADR-025 cross-ref 보강
- 재검증 PASS: D-row↔scope_manifest 7/7 byte 1:1 (option_chosen 7/7 + owner_story 7/7) 양 peer 독립 확증

### 4.2 구현리뷰 iter 1/3 — Change Plan §4.2 self-contradiction + cold path SSOT 이중화 (P1×2 boundary)

- F-1: Change Plan §4.2("하위모듈 삭제") ↔ §6/§2.2("무중단 보존, 사전 마이그레이션 불요") **cross-document desync** (설계리뷰 iter1 F-2가 scope_manifest만 정정·§4.2 동반 누락 — MCT-179 lesson 동형 재현)
- F-2: cold/duckdb_resample.py:53 + cold/polars_fallback.py:36 가 `__init__` shim 우회 → 잔존 data 원본 직접 import → market SSOT 이중화 (INV-4 정신 위반, byte-equiv로 런타임 0이나 MCT-188 D7 ImportError 기술부채)
- 원인 = 설계 (Code review P1 boundary → 설계, DeveloperPL 1차 진단 → ArchitectPL 최종 수용)
- 해소: ArchitectPL 판정 = Option A 채택 (B=production 파손+scope creep 보수적 기각, 사용자 directive 2026-05-13 정합). Change Plan §4.2 정정 ("MCT-188 D7까지 deprecated 보존")+§8 INV-4 test 보강+§12.2 박제. 4 산출물 수렴 (§4.2/§6/§2.2/scope_manifest/ADR-031). data#69 fix PR — cold path 2곳 mctrader_market.aggregation 직접 재지정 + `test_cold_path_uses_market_sot` 5 신규 test (AST+런타임 dual-modal is-동일성, 사각지대 해소)
- 재검증 PASS: F-1/F-2 양 peer 독립 RESOLVED 확증. 회귀 0

## 5. lesson 누적 (cross-Story 트렌드)

1. **R1 가드 실효 검증 1회**: docker-stack 6회 Phase 0 verify gap 누적 → 본 Epic R1 가드(Story별 Phase 0 deep-verify 독립 게이트 + D-row 1:1 reconcile) 가 desync 2건(가설 5곳 / 패키지 표기) **사전 차단**. R1 가드 패턴 = 효과적, 후속 Story (MCT-183~188) 동일 패턴 reapply 권고.
2. **MCT-179 SSOT desync lesson 동형 재현 (1회)**: 설계리뷰 iter1 F-2 부분 정정(scope_manifest만)이 구현리뷰 iter1 F-1(Change Plan §4.2 stale) 으로 carry — **cross-document SSOT 정합은 1차 정정 시 4 산출물(spec/scope_manifest/ADR/Change Plan) 전수 수렴 의무**. 본 Story FIX 사이클로 보완 인지, 후속 Story 동반 정합 체크리스트 의무화 권고.
3. **byte-equivalence 보존 = 런타임 무결성 안전망**: 두 FIX 모두 byte-equivalence 가 보존돼 LAND 후 회귀 0 (data 871 PASS 후 fix1 후도 871 PASS). relocation Story 의 핵심 안전 invariant 가 실증.
4. **Option A vs B 보수적 기각 정합**: ArchitectPL Option B(즉시 삭제) 기각 사후 검증 = data tests/aggregation/ 7건 + reconciliation 1건 + engine/hot 1건 + tests/hot 1건 = **10건 ImportError 폭증** 사전 차단. 사용자 directive 2026-05-13 (타협 어려운 부분 보수적 평가) 정합.

## 6. carry over (post-Story)

| # | 항목 | severity | owner |
|---|------|----------|-------|
| 1 | engine `consumers/candle_view.py:38` docstring `mctrader_data.cold.duckdb_resample.CandleModel` → market 정정 | P2 cosmetic | 차기 박제 권고 (이미 Phase 2 PR2 동반 정합 권장) |
| 2 | engine `hot/state_machine.py:89` docstring `mctrader_data.aggregation.core._BaseAggregator` → market 정정 | P2 cosmetic | **MCT-188 D7 cutover** (shim 제거 + docstring drift 일괄 해소) |
| 3 | data `aggregation/{core,scaled_int,contract_metadata}.py` 하위모듈 파일 물리 삭제 + grep0 quad gate | scope 외 | **MCT-188 D7 owner** |
| 4 | engine `hot/state_machine.py:33` shim 경유 import (INV-4 정합 — is-동일성 보장, MCT-182 무변경) | scope 외 | MCT-188 D7 cutover |
| 5 | `paper_storage.py` 등 여타 data 내부 사용처 cleanup | scope 외 | MCT-183 owner |

## 7. 다음 Story 진입

**MCT-183** (sequential_phase 2) — Layer 2 read 도메인 relocation: engine `io/` 6 module(tier_reader/reader_cache/endpoint_router/dr_mode/cold_reader/l1_reader, src caller 0 verified dead-in-prod) → mctrader-data 물리 이전 + ADR-029/027 amendment box. MCT-182 LAND prerequisite 충족 (Layer0 contract 안정화).

진입 권고: **R1 가드 패턴 reapply** (Phase 0 deep-verify 독립 게이트 + Change Plan ↔ scope_manifest ↔ ADR cross-document 정합 체크리스트 의무 — 본 Story FIX 사이클 lesson reapply).
