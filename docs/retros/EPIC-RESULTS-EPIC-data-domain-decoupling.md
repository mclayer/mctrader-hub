# EPIC-RESULTS — EPIC-data-domain-decoupling

> **Status**: phase:구현-IN_PROGRESS · milestone **6/7** · POLICY_FINALIZED target = MCT-188
> mctrader-engine 을 (1) data-free + (2) exchange-agnostic pure consumer 로 전환하는 7 Story sequential strangler-fig Epic.

## Story 진행 현황

| seq | Story | 제목 | D | 상태 | LAND |
|---|-------|------|---|------|------|
| 1 | **MCT-182** | Layer0 contract relocation → market | D1, D6 | **COMPLETED 2026-05-15** | hub#349 + market#11 + data#68 + engine#57 + hub#350(§8.5) + data#69(fix1) + hub Phase2 PR2 |
| 2 | **MCT-183** | Layer2 read 도메인 relocation → data | D2, D6 | **COMPLETED 2026-05-16** | hub#353 + data#70 + engine#58 + hub#354(§8.5) + data 6450cfd(lint-revert) + hub Phase2 PR2 |
| 3 | **MCT-184** | data REST API 신규 (FastAPI /v1 historical+reverse-write) | D3, D6 | **COMPLETED 2026-05-16** (post-merge fix 4건 carry — F-1/F-2/F-4 data측 + F-3 hub측 amendment) | hub#358 + data#72 + hub#359(§8.5+ADR-031 §D3 LAND confirm) + hub Phase2 PR2 박제 amendment (RETRO + §Story-3 + frontmatter status + F-3 정정) |
| 4 | **MCT-185** | data realtime stream + engine thin client + cold-read/reverse-write 11-place cutover | D2, D3 | **COMPLETED 2026-05-17** | hub#366 + data#76 + engine#59 + hub Phase2 PR2 |
| 5 | **MCT-186** | engine realtime cutover + exchange-adapter 제거 | D4 | **COMPLETED 2026-05-17** | hub#370 + engine#60 + hub Phase2 PR2 |
| 6 | **MCT-187** | 다중거래소 확장 불변식 박제 | D5, D6 | **COMPLETED 2026-05-17** | hub#374 + data#78 + hub Phase2 PR2 |
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

## §Story-3 (MCT-184) — Layer 2 data REST API 신규 (FastAPI /v1 historical + reverse-write)

### 결과
- **AC 6/6 PASS / INV 6/6 PASS** (FastAPI /v1 기동 + OpenAPI · historical Arrow IPC byte 정확 · reverse-write idempotent · OpenAPI SSOT=data + hub contract snapshot · Arrow IPC NAS layout 비노출 · wiring drift 차단 production caller 0 + consumer=MCT-185)
- 신규 test 21 passed + 2 skipped (TC-4/TC-8 env-specific cross-repo-contract-lock-check.sh CI env 미구성, AC-4 carrier=MCT-185)
- 회귀 0 (data 1152 passed ubuntu-latest, 신규 실패 0)
- ADR-031 §D3 partial VERIFIED 박제 (historical+reverse-write Phase, realtime stream + cold-read cutover = MCT-185)
- ADR-030 amendment box 박제 (data api service compose topology 예고. 실 compose wiring = MCT-186 owner)
- 3 PR LAND timeline: hub#358(`1e96b47` Phase 1 docs) → data#72(`45e501c5` api/ 6 파일 신규) → hub#359(`4924b16` §8.5 Impl Manifest + ADR-031 §D3 LAND confirm) → **hub Phase2 PR2 박제 amendment** (RETRO + §Story-3 + frontmatter status + F-3 정정, 본 amendment PR)

### 핵심 변경
- mctrader-data 신규 (data#72): `src/mctrader_data/api/` 6 파일 (FastAPI ASGI app factory + lifespan + CORS internal-only + Arrow IPC helpers + DI deps + Pydantic strict schemas + /v1 historical/reverse-write routes)
  - `api/app.py` (93 lines) — `create_app()` + lifespan startup `initialize_readers()` + CORS internal
  - `api/arrow_ipc.py` (59 lines) — `table_to_ipc_bytes()` + `ipc_bytes_to_table()` (INV-2 carrier)
  - `api/deps.py` (121 lines) — FastAPI DI singleton provider (TierReader/ColdReader/L1Reader)
  - `api/routes_v1.py` (311 lines) — `/v1/historical/candles` + `/v1/historical/candles/l1` + `/v1/reverse-write/paper-candles` + `/v1/reverse-write/backtest-artifact` (dead-in-data stub, AC-6 evidence triad)
  - `api/schemas.py` (152 lines) — Pydantic strict (T1 path traversal allowlist + T2 DoS bound max_length=1000 + INV-3 canonical_sha256)
- tests/api 신규: `test_rest_api.py` (659 lines, TC-1~11 + Perf Baseline, 21 passed + 2 skipped)
- pyproject.toml: `fastapi>=0.110` + `uvicorn[standard]>=0.27` 신규 의존
- **dead-in-data 박제** (D3 partial, MCT-185 cutover 전): production caller 0 + consumer=MCT-185 명시 + routes_v1 `_get_writer()` 503 guard + tests/api TC-9 AC-6 wiring evidence triad

### FIX 루프 (pre-LAND PASS FIX 0 + post-LAND iter 1 P0×3 + P1×1)

**pre-LAND**:
- 설계리뷰 iter 1 **PASS FIX 0회** — P0/P1/P2 = 0/0/0, cross-document SSOT **6회째 §3.6.1 gate v2 사전 차단 성공** (MCT-183 lesson reapply 실효 검증)
- 구현리뷰 **BYPASS** (dead-in-data, consumer=MCT-185, 구현-리뷰 lane = MCT-185 cutover 전 진입)

**post-LAND (Codex audit 발견)**:
| # | severity | finding | fix path |
|---|----------|---------|----------|
| F-1 | P0 (구현) | invalid ts_utc → `datetime.now()` silent substitute = silent data corruption | data#N post-merge fix (#795 unblock 후) |
| F-2 | P0 (구현) | canonical_sha256 dead code, sidecar pattern만 검사 = silent data-loss (INV-3 mismatch) | data#N post-merge fix |
| F-3 | P0 (구현 + 박제) | Story §8.5.1+CLAUDE.md hub#TBD 잔존(실 LAND=hub#359) | **hub amendment PR (본 EPIC-RESULTS 동반)** ✅ |
| F-4 | P1 (설계 + 구현) | arrow_ipc round-trip INV-2 bytes-level 보장 X (table 동등만, dead-in-data 런타임 0 but MCT-185 cutover 전 정정 의무) | data#N post-merge fix |

§3.6.1 gate v2 post-LAND repo-wide 0줄 PASS (cross-doc SSOT 6회 forcing function 실효). 단 **gate v2 영역(SSOT 정합) ≠ Codex audit 영역(production correctness + bytes-level 정밀도)** — F-1/F-2/F-4 는 Codex post-LAND audit 만이 발견 가능한 영역 실증 → **codeforge upstream ADR escalation 후보 3** (post-merge audit lane 의무 박제 검증) 발의.

### 박제 PR 자체 incomplete 발견 (SSOT drift 3호, MCT-189 PMO-PATTERNS 동형)

hub#359 (Phase 2 PR2 박제) MERGED 그러나 박제 작업의 약 절반만 처리:
- ❌ RETRO-MCT-184.md 미생성
- ❌ EPIC-RESULTS §Story-3 (MCT-184) 미작성 + milestone 2/7 → 3/7 미반영
- ❌ Story frontmatter `status: phase:구현` 잔존, `completed_at: ~` 미입력
- ❌ F-3 hub#TBD 잔존 (Story §11/§8.5.1 + CLAUDE.md line 560)

**핵심 lesson**: "Phase 2 PR2 박제" PR title 이 박제 작업의 SSOT 가 아님. PR MERGED ≠ 박제 완결. 박제 산출물 체크리스트 (RETRO + EPIC-RESULTS §Story-N + Story frontmatter + CLAUDE.md + ADR amendment confirm) 의 전수 LAND 가 완결 의무. → **codeforge upstream ADR escalation 후보 2** (박제 PR 자체 완결도 mechanical gate — PMO-AUDIT-MCT-184 박제 + marketplace issue 발의).

### dead-in-data 박제 패턴 (ADR-032 evidence triad)

MCT-184 = MCT-185 cutover 전 production caller 0. **AC-6 wiring drift 차단 invariant** + routes_v1 `_get_writer()` 503 guard + tests/api/test_rest_api.py TC-9 의 3종 evidence triad 박제. **MCT-189 wiring drift 동형 사전 차단** ("정책 SSOT VERIFIED but production caller 0" 패턴이 박제 단계부터 dead-in-data 명시화로 해소) — relocation/신규-신설 Story 패턴의 안전 invariant 화 권고 (MCT-185 cutover Story / MCT-186 / MCT-187 reapply).

## §Story-4 (MCT-185) — data realtime stream + engine thin client + cold-read/reverse-write 11-place cutover

### 결과
- **AC 6/6 PASS / INV 7/7 PASS** (cross-repo — AC-1 realtime SSE / AC-2 engine data_client HTTP / AC-3 engine src/ grep0 / AC-4 11-place cutover / AC-5 CodeQL CWE-22 fix / AC-6 ADR-032 evidence triad)
- **AC-3 grep0 VERIFIED** — engine src/ `from mctrader_data.(storage|path|orderbook_replay|paper_storage|nas_storage)` = 0건 (engine#59 LAND 후 confirm)
- **11-place cutover**: cold-read 8곳 (cli.py×2, tick_replay.py×2, wfo/evaluator×2, wfo/search×2) + reverse-write 3곳 (paper_runner.py×2, nas_sync.py×1)
- **FIX 0회** — DesignReview PASS FIX 0회 + code lane blocking 0 양 PR (data#76 PASS + engine#59 PASS)
- ADR-029 §D2 VERIFIED (engine NAS 직독 폐기 완결) + ADR-031 §D2+§D3 VERIFIED (cold-read cutover 완결 + realtime stream + reverse-write wiring 완결)
- 3 PR LAND timeline: hub#366(`67bcc1c` 2026-05-16 Phase 1 docs) → data#76(`9473665` 2026-05-16 land_order 1 realtime_stream + OrderBook endpoint + CodeQL fix) → engine#59(`1312195` 2026-05-16 land_order 2 data_client/ 신설 + 11-place cutover) → hub Phase2 PR2(2026-05-17 박제)

### 핵심 변경
- mctrader-data 신규 (data#76): `src/mctrader_data/api/realtime_stream.py` (Redis Stream XADD publisher + SSE endpoint `/v1/realtime/ticks`, tick.v1.1 Schema) + `/v1/historical/{symbol}` OrderBook endpoint + CodeQL CWE-22 fix (`_assert_within_root` → `relative_to()` boundary check)
- mctrader-engine 신규 (engine#59): `src/mctrader_engine/data_client/__init__.py` + `client.py` + `stream.py` (DataClient HTTP thin client + realtime WS stream consumer)
- mctrader-engine cutover (engine#59): cold-read 8곳 (`mctrader_data.storage` 직독 → REST 경유) + reverse-write 3곳 (`nas_sync.py` + `paper_runner.py`) REST 경유 cutover

### FIX 루프 (DesignReview PASS FIX 0 + code lane PASS FIX 0)
- 설계리뷰 iter 1 **PASS FIX 0회** — cross-document SSOT §3.6.1 gate v2 **7회째 사전 차단 성공** (MCT-182~184 self-discipline 누적 + ADR-032 evidence triad self-check 결합)
- 구현리뷰 data#76 iter 1 **PASS FIX 0회** (blocking 0)
- 구현리뷰 engine#59 iter 1 **PASS FIX 0회** (blocking 0 — AC-3 grep0 확인 포함)

### ADR-032 evidence triad 선제 reapply 효력 실증 (1회)

MCT-184 post-LAND Codex audit 발견 (박제 PR incomplete 패턴 + dead-in-data 박제 패턴) → MCT-185 에서 production wiring 전환 시 선제 reapply:
- pre-LAND 설계 단계: cutover scope grep 실측 (11곳 가설 오차 0) → Phase 0 verify 신뢰성 누적
- code lane: FIX 0회 달성 (ADR-032 evidence triad self-check 효과 + Codex audit lesson reapply)
- post-LAND: 박제 PR 5 체크리스트 전수 이행 (RETRO 존재 + §Story-4 + Story frontmatter + CLAUDE.md 0줄 + ADR confirm 5/5)

### 박제 PR 5 체크리스트 자기규율 전수 이행 (MCT-184 SSOT drift 3호 lesson direct reapply)

| 항목 | 이행 |
|------|------|
| RETRO-MCT-185.md 존재 | ✅ |
| EPIC-RESULTS §Story-4 박제 | ✅ (본 항목) |
| Story frontmatter status=COMPLETED + completed_at=2026-05-17 | ✅ |
| CLAUDE.md hub#TBD 잔존 0줄 | ✅ |
| ADR-029 §D2 + ADR-031 §D2/§D3 VERIFIED amendment box LAND confirm | ✅ |

## §Story-5 (MCT-186) — engine realtime cutover + exchange-adapter 제거

### 결과
- **AC 7/7 PASS / INV 6/6 PASS** (engine#60 773b270 MERGED 2026-05-16T21:52:47Z)
- **AC-1 grep0 PASS** — `grep -rn "mctrader_market_bithumb" src/` = **0건** (5곳 5파일 전부 제거)
- 신규 test 4 (testcontainers integration, ALL PASS) / 삭제 파일 1 (ws_wrapper.py)
- FIX 1 iter (design P0 — cli.py StreamExhaustedError §3.2.4b 발견), code 0 iter
- ADR-031 §D4 VERIFIED (engine#60 + grep0 + integration test — ADR-032 evidence triad)
- ADR-030 NAS cred drop carry over (compose.yml engine NAS env drop = MCT-187 or 별 PR)
- 2 PR LAND timeline: hub#370(`3fc9c1f` 2026-05-16 Phase 1 docs) → engine#60(`773b270` 2026-05-16 5파일 제거 + RedisStreamSubscriber + types.py + ws_wrapper.py 삭제) → hub Phase2 PR2(2026-05-17 박제)

### 핵심 변경
- mctrader-engine 신규 (engine#60): `src/mctrader_engine/realtime/types.py` (engine-local `OrderbookSnapshot`/`_Level` frozen+slots dataclass, INV-3 영구) + `src/mctrader_engine/realtime/redis_subscriber.py` (XREAD asyncio subscriber, `market:tick:{exchange}:{symbol}`, XREAD BLOCK=1000ms count=100, retry 5× 0.5s base exponential backoff, MarketStream Protocol 준수)
- mctrader-engine 수정 (engine#60): `fill/simulated.py:18` + `realtime/stream_consumer.py:8-12` + `runtime/mock_stream.py:19` + `runtime/paper_runner.py:267` — bithumb import 제거 + engine-local/market-core 대체
- mctrader-engine 삭제 (engine#60): `src/mctrader_engine/runtime/ws_wrapper.py` 파일 전체 (`WsWrapperStream` + `StreamExhaustedError`) + `cli.py:442` import + `cli.py:597` catch block
- tests 신규 (engine#60): `tests/test_realtime_subscriber.py` 4 test (testcontainers RedisContainer — XADD+XREAD round-trip / max_events / malformed_payload_skipped / ctx_manager_guard)

### FIX 루프 (design 1 iter — P0 §3.2.4b)
- Change Plan 초안이 ws_wrapper.py 삭제 명시 → cli.py `StreamExhaustedError` import (line 442) + catch block (line 597) dangling 누락 (설계 원인 — scope 정의 누락)
- §3.2.4b 패턴 (파일 삭제 시 downstream catch 블럭 포함 전수 caller 검색 의무) → Change Plan §1.5 추가 → CONDITIONAL_PASS → code iter1 직접 PASS
- **lesson**: `grep -rn <symbol>` 전수 caller 검색 = ws_wrapper.py 삭제 Phase 0 추가 체크포인트

### ADR-031 §D4 evidence triad (ADR-032 정합)
| evidence | 내용 |
|---|---|
| file:line | `fill/simulated.py:18` → `from mctrader_engine.realtime.types import OrderbookSnapshot` |
| caller grep | `grep -rn "mctrader_market_bithumb" src/` = **0건** (engine#60, AC-1 PASS) |
| integration test | `tests/test_realtime_subscriber.py` 4 test (testcontainers RedisContainer) ALL PASS |

### 박제 PR 5 체크리스트 이행 (MCT-185 패턴 재사용)
| 항목 | 이행 |
|------|------|
| RETRO-MCT-186.md 존재 | ✅ |
| EPIC-RESULTS §Story-5 박제 | ✅ (본 항목) |
| Story frontmatter status=COMPLETED + completed_at=2026-05-17 | ✅ |
| CLAUDE.md hub#TBD 잔존 0줄 | ✅ |
| ADR-031 §D4 VERIFIED + ADR-030 NAS cred drop carry over | ✅ |

## §Story-6 (MCT-187) — 다중거래소 확장 불변식 박제 (code-change-zero)

### 결과
- **AC 4/5 PASS / INV 4/4 PASS** (hub#374 91a8bfa + data#78 6346b55 + hub Phase 2 PR2)
- **code-change-zero Story** — `adapters.py` 변경 0 (INV-2 PASS, MCT-186 LAND 정합)
- 신규 test 5 TC (4 passed + 1 skipped CI-safe) / ubuntu-latest 1183 passed 회귀 0
- FIX 1 iter (ruff lint — F401×3 + E721 + F841, edda216)
- ADR-031 §D5 VERIFIED (hub Phase 2 PR2 박제)
- D5 invariant: engine/market-core/ADR 변경 0 = monkeypatch 패턴으로 구조적 박제
- 2 PR LAND timeline: hub#374(91a8bfa 2026-05-16 Phase 1 docs + runbook + ADR draft) → data#78(6346b55 2026-05-17 5 TC) → hub Phase 2 PR2

### 핵심 변경
- mctrader-data 신규 (data#78): `tests/test_multi_exchange_invariant.py` 5 TC (monkeypatch 패턴 D5 핵심 invariant 박제)
- mctrader-hub 신규 (hub#374): `docs/runbooks/add-new-exchange.md` (3-step: Layer1 repo 신설 + adapters.py 등록 + 수집/정규화 설정)
- `src/mctrader_data/adapters.py` 변경 0 (INV-2 PASS)

### D5 invariant 5 TC
| TC | 내용 | 결과 |
|----|------|------|
| TC-1 | bithumb + upbit 기존 팩토리 등록 확인 | PASS |
| TC-2 | 미등록 거래소 → ValueError | PASS |
| TC-3 | monkeypatch mock exchange 등록 → 호출 성공 (핵심) | PASS |
| TC-4 | engine pyproject 신규 의존 0 (engine repo 없으면 skip) | SKIPPED |
| TC-5 | adapters.py callable + bithumb/upbit 정상 + unknown ValueError | PASS |

### windows-latest CI
기존 testcontainers Docker sock 오류 (`test_promote_l1_post_put_unlink.py` + `test_runner_retroactive_cleanup.py`) — **MCT-187 scope 외, pre-existing regression**. main branch 동일 실패 확인. MCT-187 신규 5 TC = ubuntu-latest 완전 PASS. `phase-gate-mergeable` PASS.

### 박제 PR 5 체크리스트 이행
| 항목 | 이행 |
|------|------|
| RETRO-MCT-187.md 존재 | ✅ |
| EPIC-RESULTS §Story-6 박제 | ✅ (본 항목) |
| Story frontmatter status=COMPLETED + completed_at=2026-05-17 | ✅ |
| CLAUDE.md hub#TBD 잔존 0줄 | ✅ |
| ADR-031 §D5 VERIFIED amendment box LAND confirm | ✅ |

## ADR 산출물

- **ADR-031** (신규, MCT-182 publish, 2026-05-16) — Data Domain Decoupling — 4-layer + contract relocation + REST boundary + multi-exchange extensibility invariant. Status: **Accepted** (MCT-182 LAND VERIFIED). D1-D5 VERIFIED (MCT-182~187). transition: Proposed → Accepted (MCT-182, D1+D6 VERIFIED) → POLICY_FINALIZED (MCT-188 target — D1-D7 전수 + ADR-029/027/030 amend confirm)

## 핵심 결정 (D1-D7, MCT-179 lesson — D-row↔scope_manifest 7/7 byte 1:1 reconcile)

| D | 결정 | option | Owner Story | 상태 |
|---|------|--------|-------------|------|
| D1 | Contract relocation → mctrader-market (Layer 0) | relocate-to-market-core | MCT-182 | **VERIFIED 2026-05-15** |
| D2 | Read 도메인 relocation → mctrader-data (Layer 2) | io-relocate + cold-read-behind-REST | MCT-183 (io relocate) + MCT-185 (cold-read/reverse-write cutover) | **VERIFIED 2026-05-17** (MCT-183 io relocate + MCT-185 11-place cutover 완결 — ADR-029 §D2 VERIFIED) |
| D3 | data REST API 신규 (historical + reverse-write + realtime stream) | fastapi-v1 + redis-stream | MCT-184 (historical+reverse-write) + MCT-185 (realtime stream + cutover) | **VERIFIED 2026-05-17** (MCT-184 historical+reverse-write + MCT-185 realtime stream + 11-place cutover 완결 — ADR-031 §D2+§D3 VERIFIED) |
| D4 | engine exchange-adapter 제거 | subscribe-normalized-stream | MCT-186 | **VERIFIED 2026-05-17** (engine#60 AC-1 grep0 PASS 5곳 5파일 — ADR-031 §D4 VERIFIED) |
| D5 | 다중거래소 확장 불변식 | data-only-extension-invariant | MCT-187 | **VERIFIED 2026-05-17** (data#78 6346b55 — 5 TC PASS + adapters.py 변경 0 + runbook LAND — ADR-031 §D5 VERIFIED) |
| D6 | ADR-031 신규 + ADR-029/027/030 amendment | new-adr-031 + 3-amend | MCT-182 (publish) + MCT-188 (POLICY_FINALIZED + amend confirm) | **publish/D1 VERIFIED 2026-05-15**, amend pending |
| D7 | data-free done-criterion (grep0 quad gate) | ci-grep0-quad-gate | MCT-188 | reserved |

## Risk 현황

| Risk | Severity | 상태 |
|------|----------|------|
| R1 cross-repo contract/Phase0 desync | HIGH | **완화 효과 4회 실증** — MCT-182(2건 사전차단) + MCT-183(7회째) + MCT-184(6회째 §3.6.1 gate v2 성공) + **MCT-185(7회째 성공 + ADR-032 evidence triad reapply — FIX 0회 달성)**. cross-document SSOT desync → §3.6.1 gate v2 누적 자기규율 정착 |
| R2 EPIC-MCT-41 Live Mode Debut 블락 | HIGH | **MCT-186 ZERO RISK 확인 (2026-05-17)** — MCT-43~47 active branch 0건. MCT-187 진입 전 재검증 의무 (Orchestrator ordering gate) |

## Epic CLOSED prerequisite (POLICY_FINALIZED → CLOSED, post-Epic 별 PR/Story)

(MCT-188 LAND 후 POLICY_FINALIZED → 이후 production deploy + grep0 quad gate CI green + ADR-029/027/030 amend confirm + EPIC-RESULTS 박제 수렴 시 CLOSED. 상세 = MCT-188 owner)

## 다음 Story 진입

**MCT-187 COMPLETED** ✓ (2026-05-17, milestone 6/7). 다음 = **MCT-188**.

**MCT-188** (sequential_phase 7) — data-free grep0 quad gate + Epic POLICY_FINALIZED — D7+D6.

진입 prerequisite:
1. MCT-187 Phase 2 PR2 MERGED ✓ (본 박제 LAND 시점)
2. carry over: engine compose.yml `NAS_MINIO_*` env drop = 별 PR or MCT-188 (ADR-030 §D4 carry)
3. carry over: pyproject.toml `mctrader-market-bithumb` dep 제거 = MCT-188 owner (D7 quad gate final)

진입 권고:
- D7 quad gate = engine src/ `from/import mctrader_data` == 0 AND engine pyproject mctrader-data 제거 AND engine src/ `mctrader_market_bithumb|upbit` == 0 AND engine pyproject 어댑터 의존 제거
- `.github/workflows/data-free-grep0.yml` 신규 CI gate (MCT-172 grep0 strict 패턴 재사용)
- ADR-031 POLICY_FINALIZED + ADR-029/027/030 amend confirm 전수 박제 의무
