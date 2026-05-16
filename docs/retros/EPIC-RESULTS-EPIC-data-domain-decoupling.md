# EPIC-RESULTS — EPIC-data-domain-decoupling

> **Status**: phase:구현-IN_PROGRESS · milestone **2/7** · POLICY_FINALIZED target = MCT-188
> mctrader-engine 을 (1) data-free + (2) exchange-agnostic pure consumer 로 전환하는 7 Story sequential strangler-fig Epic.

## Story 진행 현황

| seq | Story | 제목 | D | 상태 | LAND |
|---|-------|------|---|------|------|
| 1 | **MCT-182** | Layer0 contract relocation → market | D1, D6 | **COMPLETED 2026-05-15** | hub#349 + market#11 + data#68 + engine#57 + hub#350(§8.5) + data#69(fix1) + hub Phase2 PR2 |
| 2 | **MCT-183** | Layer2 read 도메인 relocation → data | D2, D6 | **COMPLETED 2026-05-16** | hub#353 + data#70 + engine#58 + hub#354(§8.5) + data 6450cfd(lint-revert) + hub Phase2 PR2 |
| 3 | MCT-184 | data REST API 신규 (FastAPI /v1 historical+reverse-write) | D3, D6 | RESERVED | — |
| 4 | MCT-185 | data realtime stream + engine thin client + cold-read cutover | D2, D3 | RESERVED | — |
| 5 | MCT-186 | engine realtime cutover + exchange-adapter 제거 | D4 | RESERVED | — |
| 6 | MCT-187 | 다중거래소 확장 불변식 박제 | D5, D6 | RESERVED | — |
| 7 | MCT-188 | data-free grep0 quad gate + Epic POLICY_FINALIZED | D7, D6 | RESERVED | — |

## §Story-1 (MCT-182) — Layer 0 Contract Relocation

### 결과
- **AC 6/6 PASS / INV 6/6 PASS** (cross-repo)
- 신규 test 72 / 회귀 0 (market 156 / data 871 / engine 990)
- ADR-031 publish: Status **Proposed → Accepted** (D1 VERIFIED amendment 박제)
- 7 PR LAND timeline (sequential): hub#349(2026-05-15 Phase 1) → market#11(`4902b53c`) → data#68(`4451f28d`) → engine#57(`c6249fa6`) → hub#350(`9f572f0e` §8.5) → data#69(`5f00fc6e` fix1) → hub Phase2 PR2

### 핵심 변경 (검증 SSOT 4 산출물 정합 — Change Plan §4.2/§6/§2.2 + scope_manifest line 204 + ADR-031 line 230)
- mctrader-market 신규: `aggregation/`(PURE 패키지, 8 public 심볼) + `records.py`(TickRecord/OrderbookEventRecord 순수 dataclass, pyarrow 비결합) + `paper_lineage.py`(PaperLineage/canonical_jsonl_hash, PURE)
- mctrader-data shim: `aggregation/__init__.py` 패키지 shim(하위모듈 deprecated 보존, MCT-188 D7 cutover) + `paper_lineage.py` shim. tick/orderbook_storage TickRecord/OrderbookEventRecord import → market.records (writer 무변경)
- mctrader-engine: CandleModel 4곳(verified) → mctrader_market.candle 재지정 (재구현 0)
- fix1 (data#69): cold/duckdb_resample.py:53 + cold/polars_fallback.py:36 → mctrader_market.aggregation 직접 재지정 (shim 우회 SSOT 이중화 해소) + `test_cold_path_uses_market_sot` 5 신규 test

### FIX 루프 (자기 정정 lesson)
- 설계리뷰 iter 1/3 (P0×2 scope_manifest desync, MCT-179 lesson 적용) → ArchitectPL 회귀 → PASS (D-row 7/7 byte 정합)
- 구현리뷰 iter 1/3 (P1×2 boundary, Change Plan §4.2 cross-document desync MCT-179 동형 재현) → ArchitectPL Option A 채택 → §4.2 정정 + data#69 fix → PASS (4 산출물 수렴)
- 둘 다 max 3 미달, byte-equivalence 보존으로 LAND 후 회귀 0

### Phase 0 R1 가드 실효 (docker-stack 6회 누적 → 7회째 사전 차단 1회 실증)
- 가설 정정 2건: engine CandleModel 5곳 → 4곳 (요구사항 lane) / scope_manifest aggregation flat → 패키지 (설계리뷰 iter1)
- 모두 코드 영구 영향 전에 사전 차단 — R1 가드 패턴 효과적, 후속 Story (MCT-183~188) 동일 reapply 권고

## §Story-2 (MCT-183) — Layer 2 read 도메인 relocation → mctrader-data

### 결과
- **AC 5/5 PASS / INV 6/6 PASS** (cross-repo, INV-6 compactor Protocol 무변경 V6 동명 risk 해소)
- 신규 test 8 / 회귀 0 (data 1020 / engine 879)
- ADR-027 §D9 amendment box + ADR-029 io reader relocated 박제 (cutover confirm = MCT-185)
- ADR-031 §D2 partial VERIFIED (io relocate 절반, cold-read cutover = MCT-185)
- 6 PR LAND timeline: hub#353(`29e9c0d` Phase 1) → data#70(`0e6f35b0`) → engine#58(`18275737`) → hub#354(`d2f48fb` §8.5) → data 6450cfd(post-merge lint-revert) → hub Phase2 PR2

### 핵심 변경
- mctrader-data 신규: `src/mctrader_data/io/` 서브패키지 6 module(cold_reader/dr_mode/endpoint_router/l1_reader/reader_cache/tier_reader) + `tests/io/` 7 test + 신규 `tests/test_io_stats_no_engine_dep.py` 회귀
- reader_cache.py 339-348 채택안 A internal no-op 치환 (producer-wiring 블록 → 외부 import 없는 3줄 주석, INV-2 grep 무위반, NameError risk 0)
- mctrader-engine 삭제: `src/mctrader_engine/io/` 6 module + `tests/io/` 7 test (dead-in-prod safe removal, src caller 0)
- compactor.reader_cache.ReaderCache(Protocol) 무변경 (V6 동명 risk → INV-6 namespace 분리)

### FIX 루프 (R1 가드 작동 + cross-document SSOT 5회 누적 lesson)
- 설계리뷰 iter1→2→3 P0×3→×2 **max 3/3** → fix-ledger-schema 3 trigger 0 → **Orchestrator RESET path 채택** → ArchitectPL 수렴회귀 (지정목록 탈피, sibling MCT-182 포함 + §3.6.1 gate v2 glob-scope+변형pattern+self-verify TEST1/TEST2) → post-RESET PASS (Orchestrator 독립 verify, DesignReviewPL rate-limit 대신)
- 구현리뷰 iter1 **PASS FIX 0회** — MCT-182 lesson reapply 효과 검증 (§3.6.1 gate v2 forcing function post-LAND repo-wide grep 0줄 실효 → carry 사전 차단)
- byte-equivalence 보존으로 LAND 후 회귀 0 (data 1020/engine 879)
- Codex pre-LAND audit → post-merge `6450cfd` lint-revert 흡수 (MCT-182 cold path 동형 2회째)

### R1 가드 사전 차단 (7회째 — Phase 0 deep-verify shift-left)
- engine src/ io/ 호출자 0 (dead-in-prod) HEAD 재검증 (요구사항 lane 분리 grep)
- V6 동명 risk (compactor.reader_cache.ReaderCache Protocol) → 설계 lane namespace 분리 + INV-6 신설
- **reader_cache.py:339-348 stats() lazy `from mctrader_engine.metrics` 사전 발견** (설계 lane CodebaseMapper, V5 top-level grep 미포착) → 채택안 A internal no-op 사전 정정. docker-stack 6회 사후 발견 대비 shift-left 성과

### cross-document SSOT desync 5회 누적 → codeforge upstream ADR escalation 결정 발의
| # | Story | 패턴 |
|---|-------|------|
| 1 | MCT-179 | ADR-030 D5/D8 swap stale |
| 2 | MCT-182 | Change Plan §4.2↔§6/§2.2 self-contradiction |
| 3 | MCT-183 iter1 | ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 |
| 4 | MCT-183 iter2 | iter1 정정 후 연계 권위 4곳 carry |
| 5 | MCT-183 iter3 | iter2 §3.6.1 gate 자체 결함 + ADR-031:139 누락 |

수동 reconcile + 수동 gate 한계 구조적 실증 → codeforge plugin design lane SSOT reconcile **mechanical gate**(glob-scope + 변형포괄 regex + self-verify) 일반화 필요 → **codeforge upstream ADR escalation 결정 발의** (PMO-AUDIT-MCT-183 박제 + codeforge marketplace issue).

## ADR 산출물

- **ADR-031** (신규, MCT-182 publish, 2026-05-16) — Data Domain Decoupling — 4-layer + contract relocation + REST boundary + multi-exchange extensibility invariant. Status: **Accepted** (MCT-182 LAND VERIFIED). transition: Proposed → Accepted (MCT-182, D1+D6 VERIFIED) → POLICY_FINALIZED (MCT-188 target — D1-D7 전수 + ADR-029/027/030 amend confirm)

## 핵심 결정 (D1-D7, MCT-179 lesson — D-row↔scope_manifest 7/7 byte 1:1 reconcile)

| D | 결정 | option | Owner Story | 상태 |
|---|------|--------|-------------|------|
| D1 | Contract relocation → mctrader-market (Layer 0) | relocate-to-market-core | MCT-182 | **VERIFIED 2026-05-15** |
| D2 | Read 도메인 relocation → mctrader-data (Layer 2) | io-relocate + cold-read-behind-REST | MCT-183 (io relocate) + MCT-185 (cold-read cutover) | **partial VERIFIED 2026-05-16** (MCT-183 io relocate 완료, cutover pending MCT-185) |
| D3 | data REST API 신규 (historical + reverse-write + realtime stream) | fastapi-v1 + redis-stream | MCT-184 + MCT-185 | reserved |
| D4 | engine exchange-adapter 제거 | subscribe-normalized-stream | MCT-186 | reserved |
| D5 | 다중거래소 확장 불변식 | data-only-extension-invariant | MCT-187 | reserved |
| D6 | ADR-031 신규 + ADR-029/027/030 amendment | new-adr-031 + 3-amend | MCT-182 (publish) + MCT-188 (POLICY_FINALIZED + amend confirm) | **publish/D1 VERIFIED 2026-05-15**, amend pending |
| D7 | data-free done-criterion (grep0 quad gate) | ci-grep0-quad-gate | MCT-188 | reserved |

## Risk 현황

| Risk | Severity | 상태 |
|------|----------|------|
| R1 cross-repo contract/Phase0 desync 7회째 | HIGH | **완화 효과 2회 실증** — MCT-182(desync 2건 사전차단) + MCT-183(7회째 사전차단: reader_cache stats lazy + Phase 0 verify HEAD 정합). 단 cross-document SSOT desync 5회 누적(수동 forcing function 한계 실증) → **§3.6.1 gate v2 영구박제 + codeforge upstream ADR escalation 결정 발의** |
| R2 EPIC-MCT-41 Live Mode Debut 블락 | HIGH | MCT-182~185 파일 disjoint 병렬 안전 (MCT-182 LAND 후 MCT-41 영향 0 확인). MCT-186 진입 전 MCT-43~47 IN_PROGRESS 파일 교차검증 의무 |

## Epic CLOSED prerequisite (POLICY_FINALIZED → CLOSED, post-Epic 별 PR/Story)

(MCT-188 LAND 후 POLICY_FINALIZED → 이후 production deploy + grep0 quad gate CI green + ADR-029/027/030 amend confirm + EPIC-RESULTS 박제 수렴 시 CLOSED. 상세 = MCT-188 owner)

## 다음 Story 진입

**MCT-184** (sequential_phase 3) — Layer 2 data REST API 신규 (FastAPI /v1 historical Arrow IPC + reverse-write POST). MCT-183 LAND prerequisite 충족 (io/ data 측 수령 완료, REST wrap 대상 확정).

진입 권고: R1 가드 + §3.6.1 gate v2 cross-Story 활용 + Codex pre-LAND audit 활용 + (가능 시) codeforge upstream ADR escalation 결과(mechanical gate plugin) 활용. MCT-183 PMO-AUDIT 박제 cross-document SSOT forcing function 확장 적용 의무.
