---
story_key: MCT-63
status: phase:요구사항
component: epic
type: epic
parent_epic: null
related_adrs: ADR-002, ADR-004, ADR-005, ADR-006, ADR-009
---

# MCT-63 (Epic): Tick + Orderbook Backtest — Forward-only data tier + Tick scalping / Market making 전략

## 1. 사용자 요구사항 (verbatim, 2026-05-04)

> "다른 전략들을 추가할 필요가 있다. 그에 앞서 orderbook, transaction_history는 candlestick과 달리 과거 데이터를 얻지 못할 건데 이건 어떻게 관리하는게 좋겠는가"
> "전략 중에 틱띠기나 마켓 메이킹에 대한 전략도 필요하거든"
> "Q1. 너가 개발한 것은 데이터 컬렉터를 포함해 전부 Linux Server에서 구동하여 관리할 것이다. Q2. 우리가 관리할 필요가 있는 코인은 거래량 상위 40% coin이다. 양이 많을 것 같다면 조정을 해보고. 3번은 추천대로"
> "지금은 예정된 작업들을 모두 수행하도록 하자."

선행 context: ADR-009 Accepted (2026-05-02, MCT-9 Phase 1) 의 §D1~§D9 = OHLCV (candle) canonical schema + §D9 L3 depth-ladder snapshot **예약** (미구현). 현재 mctrader-engine 의 모든 `Strategy` 가 `on_candle(c)` callback 만 사용 = T1 (candle) 단일 tier. **Tick scalping / Market making 전략은 candle resolution 으로 표현 불가** (틱·호가창 micro-structure 의존).

직전 Epic MCT-48 (Paper Runtime Ops + Web Mgmt, 11 PR) + MCT-55 (WFO Execution, Phase 1 진행 중) 으로 candle-기반 backtest / paper 인프라 완성. **본 Epic 은 forward-only 시계열 데이터 (tick / orderbook event) 를 backtest 가능 자원으로 정착시킴**.

## 2. 도메인 해석

mctrader 8번째 implementation Epic = **3-tier market data 모델 + Tick replay backtest 인프라 + 전략 템플릿**.

핵심 framing (Codex 22-finding review 채택, 2026-05-04):

- **3-tier 시장 데이터 모델 (T1/T2/T3) = market-data input only**, execution result schema 와 분리 (F-16). T1 (candle, backfillable, ADR-009 §D1~§D8 ohlcv.v1) / T2 (tick stream, **forward-only**, §D10 tick.v1) / T3 (orderbook event stream, **forward-only**, §D11 orderbook.v1).
- **Forward-only invariant 의 lookahead 의미** (F-3, ADR-005 amendment): T2/T3 partition 은 collector 가동 시점 부터만 존재 → backtest 에서 사용 가능한 시점 = `available_from_ts := received_at` (collector 의 server-side 도착 시각). Backtest reader 는 `received_at <= simulated_clock` 인 event 만 읽음.
- **Strategy DATA_TIER multi-tier 선언** (F-4): `REQUIRED_DATA_TIERS: ClassVar[frozenset[DataTier]]`. 단일 Literal 거부 (예: TickScalping = {tick, orderbook}, MarketMaking = {orderbook}, 기존 candle-only = {candle}). Backtest 진입 시 union 검증 후 union 의 각 tier 별 coverage 요구.
- **TickReplayExecutor = ADR-002 D2 mode invariant 보장** (F-5): Backtest / Paper / Live 3 mode 가 동일 strategy callback API (`on_candle` / `on_tick` / `on_orderbook`) 노출. Backtest = TickReplayExecutor 가 적재 event 재생, Paper / Live = 실 WS stream 이 동일 callback 으로 dispatch. 전략 코드는 mode 무지.
- **FIFO end-of-queue matching = 보수적 simulation, 거래소 미러 아님** (F-7~F-9): LIMIT order 는 제출 시각의 해당 가격 레벨 큐 끝에 join, 큐 앞부분 소진 후 본인 차례. self-trade prevention 모델 (시뮬레이션 주문 ↔ 공개 호가 분리). Bithumb-faithful 표방 거부.
- **ADR-006 WFO 비적용 명시** (F-15): T2/T3 tier 전략에 WFO promotion gate 직접 적용 안 함. 별도 후속 Epic candidate (T2/T3 전용 cross-validation 방법론).
- **MCT-65 retroactive sealing**: mctrader-data PR #4 (commit 9f51fa0, label `[MCT-58]` 은 stale — Hub PR #74 가 MCT-58 점유) 가 이미 collector daemon 구현 완료. MCT-12 retroactive sealing 패턴 동일.

본 Epic 은 MCT-41 (Live Mode) / MCT-55 (WFO) 와 **별도 lane**:
- T2/T3 전략 = candle 기반 ADR-006 WFO 와 다른 검증 방법론 필요 (별도 Epic).
- T2/T3 데이터 = 적재 시점 부터만 사용 가능 → manual prereq = collector 가동 (Linux server, 사용자 manual). 본 Epic 의 **모든 전략 backtest 는 collector 가동 후 누적 기간 만큼만 가능**.

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Codex 22-finding review (codex-rescue, gpt-5.5 high, 2026-05-04)

22 finding (F-1~F-22) Sonnet 채택. 분류: 6 MUST FIX before Phase 1 / 7 MUST FIX before Phase 2-6 / 6 SHOULD CONSIDER / 3 NICE TO HAVE.

핵심 push-back 6건 (Phase 1 doc PR blocking):

1. **F-1 snapshot_id 용어 통일** — `partition_id` (parquet filename suffix) ↔ `collector_run_id` (lineage source) 1:1 매핑. v1 = collector_run_id == partition_id. `data_hash` 부재 (forward-only stream = source 자체).
2. **F-2 §D9 vs §D11 명확화** — §D9 (OHLCV ADR Accepted 시점 예약, **L3 depth-ladder snapshot, 미구현**) ↔ §D11 (NEW, **L2 event stream, 본 Epic 구현**). 별개 schema, 의도적 split.
3. **F-3 ADR-005 lookahead amendment** — T2/T3 의 `available_from_ts := received_at`. Backtest reader filter `received_at <= simulated_clock` 의무.
4. **F-4 REQUIRED_DATA_TIERS frozenset** — `Literal[…]` 단일 거부. `frozenset[DataTier]` 채택 (multi-tier 지원).
5. **F-5 mode invariant common API** — `on_candle` / `on_tick` / `on_orderbook` Strategy 콜백을 backtest / paper / live 3 mode 공통 노출. ADR-002 D2 보장.
6. **F-6 MCT-65 traceability** — stale `[MCT-58]` commit 라벨 + canonical Hub MCT-65 매핑표 inline.

### Sonnet decider Phase 1 (24 sub-decision batch, 2026-05-04)

| # | Decision | Pick | 근거 |
|---|----------|------|------|
| A | Tier model 표현 | A2 — `frozenset[DataTier]` per Strategy | F-4 multi-tier 강제, single Literal 거부 |
| B | Tier 명세 위치 | B1 — `mctrader_engine.strategy.tiers.DataTier` Enum | engine 내 정착, market 무관 |
| C | available_from_ts 의미 | C1 — `received_at` (collector server-side 도착) | F-3 단순 + 적재 직후 사용 가능, 가공 지연 무시 |
| D | partition_id 명명 | D1 — `collector_run_id` ↔ `partition_id` 1:1 매핑 | F-1 명확성, hash 부재 (forward-only source) |
| E | §D9 L3 vs §D11 L2 | E1 — 별개 schema, §D9 = 미구현 reservation 유지, §D11 = 본 Epic | F-2 의도적 split |
| F | TickReplayExecutor 모듈 | F1 — `mctrader_engine.executor.tick_replay` | ADR-002 D2 새 모듈 |
| G | Strategy callback API | G2 — `on_candle` / `on_tick` / `on_orderbook` 의 default no-op + 필요한 callback 만 override | mode invariant + tier 기반 dispatch |
| H | Driver loop algorithm | H2 — heap-merge `scan_ticks` + `scan_orderbook_events` ASC ts | F-18 sort key 통일, 메모리 bounded (스트림) |
| I | Sort tie-break | I1 — `(ts_utc ASC, received_at ASC, file_offset ASC)` | F-18 deterministic |
| J | Matching model | J1 — FIFO end-of-queue 보수적 simulation, Bithumb-faithful 거부 | Q3 user 채택 + F-8 가정 명시 |
| K | Self-trade prevention | K1 — 시뮬레이션 주문 별개 layer, 공개 호가 와 매칭 안 함 | F-9 prevention default-on |
| L | Cancel/replace priority | L1 — replace = cancel + new (queue 끝으로) | F-7 단순 + 보수적 |
| M | Latency timing 분해 | M1 — ADR-004 D3 5단계 (decision/submit/exchange-arrival/ack/fill) 채택, exchange-arrival = queue placement 시각 | F-13 ADR-004 정합 |
| N | Reconstruction 캐시 | N1 — per-symbol-day-session bounded LRU, max N=1 reconstructed snapshot, checkpoint = N delta interval | F-10 메모리 bound |
| O | Reconstruction error mode | O1 — fail-closed (gap / non-monotonic / missing baseline = halt + emit GapDetectedEvent) | F-11 reproducibility 우선 |
| P | Coverage API | P1 — `tier_coverage(symbol, tier, start, end) -> CoverageReport` (min/max ts, gaps, collector_run_ids, symbol manifest) | F-12 + F-21 |
| Q | Strategy template list | Q2 — TickScalpingStrategy ({tick, orderbook}) + MarketMakingStrategy ({orderbook}) | Q3 user request, 2개로 한정 |
| R | WFO applicability | R2 — T2/T3 tier WFO 비적용 명시, 별도 후속 Epic | F-15 ADR-006 명시 분리 |
| S | Web API 우선순위 | S1 — contract-first (`GET /strategies` + `GET /backtests/{id}/tick_detail` schema 먼저 freeze) | F-17 endpoints 후 UI |
| T | Tick detail pagination | T1 — cursor-pagination + ts-window downsample (max 10k point default) | F-22 large payload 회피 |
| U | Symbol universe drift | U1 — collector run 마다 symbol manifest persist, replay 시 manifest 의무 참조 | F-21 reproducibility |
| V | MCT-65 retroactive | V1 — full inline checklist + 충돌 매핑표, MCT-12 패턴 답습 | F-6 + F-20 |
| W | ADR amendment 위치 | W1 — ADR-009 §D10 (tick.v1) + §D11 (orderbook.v1) 신설 + ADR-005 amendment note (T2/T3 lookahead = received_at) | F-19 schema 표 정식 ADR 수록 |
| X | Strategy registry 위치 | X1 — `mctrader_engine.strategy.registry` (decorator + dict) | engine 내 정착, lifecycle hook 없이 단순 |

24/24 escalation 0건. Phase 1 large scope (Epic + 6 child + ADR-009 §D10/§D11 + ADR-005 amendment note).

## 4. Child Story decomposition

| Story | repo | scope | 의존 |
|---|---|---|---|
| **MCT-64** Strategy registry + DATA_TIER | mctrader-engine | `mctrader_engine.strategy.tiers.DataTier` Enum (candle/tick/orderbook) + `Strategy` ABC (`REQUIRED_DATA_TIERS: ClassVar[frozenset[DataTier]]`) + `STRATEGY_REGISTRY` + `@register_strategy("name")` decorator + Backtest 진입 시 tier coverage 검증. `mctrader_engine.strategy.registry` 모듈. | — |
| **MCT-65** Forward-only collector daemon (RETROACTIVE SEAL) | mctrader-data | mctrader-data PR #4 (commit 9f51fa0, label `[MCT-58]` stale) 의 retroactive sealing. 검증: `tick_storage.py` (TickWriter) / `orderbook_storage.py` (OrderbookWriter, flat snapshot+delta) / `collector.py` (CollectorDaemon + MultiSymbolCollector + fetch_top_n_krw_symbols) / `cli.py mctrader-data collect` / `deploy/mctrader-collector.service` (systemd unit) / 17 unit tests / Hive partition `market/{ticks,orderbook}/schema_version=…/exchange=.../symbol=.../date=YYYY-MM-DD/part-{collector_run_id}.parquet`. **추가**: collector run 마다 symbol manifest persist (F-21). | — (mctrader-data 가 MCT-9 / MCT-12 의존, 본 Epic 진행에 추가 prereq 없음) |
| **MCT-66** Orderbook reconstruction utility | mctrader-data | `mctrader_data.orderbook_replay` 모듈 (NEW). API: `scan_ticks(symbol, start, end) -> Iterable[TickRecord]` / `scan_orderbook_events(symbol, start, end) -> Iterable[OrderbookEventRecord]` / `get_orderbook_at(symbol, ts_utc) -> OrderbookSnapshot` (start-of-day baseline → fold delta forward) / `tier_coverage(symbol, tier, start, end) -> CoverageReport`. **Fail-closed**: gap / non-monotonic / missing baseline = halt + `GapDetectedEvent`. **Sort key**: `(ts_utc ASC, received_at ASC, file_offset ASC)`. **Bounded cache**: per-symbol-day-session LRU max N=1 snapshot, checkpoint every M deltas. **available_from_ts**: `received_at` filter 의무. | MCT-65 |
| **MCT-67** TickReplayExecutor + FIFO matching | mctrader-engine | `mctrader_engine.executor.tick_replay.TickReplayExecutor` (TradeExecutor Protocol per ADR-002 D2). **4 acceptance section**: (1) replay driver — `scan_ticks` + `scan_orderbook_events` heap-merge ASC ts, dispatch `on_tick` / `on_orderbook` / `on_candle` callback. (2) FIFO matching — LIMIT 큐 끝 join + 큐 앞 소진 후 본인 차례 fill, MARKET 호가 walk, partial fill / cancel-replace = priority reset / 가격 레벨 disappearance / crossed book deterministic 처리. (3) latency model — ADR-004 D3 5단계 (decision/submit/exchange-arrival/ack/fill), exchange-arrival 시각이 queue placement. (4) provenance — result manifest 에 source partition `collector_run_id` 다수 기록 + symbol manifest reference. **Self-trade prevention**: 시뮬레이션 주문 별개 layer, 공개 호가 비매칭. **보수적 simulation 명시**: Bithumb-faithful 표방 거부. | MCT-64, MCT-66 |
| **MCT-68** Strategy templates (TickScalping + MarketMaking) | mctrader-engine | `mctrader_engine.strategy.templates.tick_scalping.TickScalpingStrategy(REQUIRED_DATA_TIERS={tick, orderbook})` (N consecutive same-direction tick > threshold → 반대편 LIMIT at top-of-book ± spread, take-profit K bps / stop -K bps / time-based forced exit) + `mctrader_engine.strategy.templates.market_making.MarketMakingStrategy(REQUIRED_DATA_TIERS={orderbook})` (top-of-book ± half-spread 양방 post, book imbalance > threshold 시 quote refresh, position > target 시 inventory skew). **WFO 비적용 명시** (F-15 + R2). 템플릿 only — 실제 전략 = 사용자 별도 repo. | MCT-64, MCT-67 |
| **MCT-69** Web UI tick backtest integration | mctrader-web | mctrader-web `02_backtest_panel.py` 확장 + 신규 FastAPI endpoint. **Contract first** (F-17 + S1): `GET /strategies` (registry 노출, name + REQUIRED_DATA_TIERS) / `GET /backtests/{id}/tick_detail?cursor=&downsample=` (per-fill orderbook context, T1 cursor pagination + ts-window downsample 의무, max 10k point default). UI: strategy class selector (registry 조회) + DATA_TIER badge + tick backtest 결과 viewer (trade list + per-fill queue position chart + orderbook depth mini-ladder). | MCT-67 |

### Ordering 의무

- **MCT-64 = serialized first** (registry + tier 의무 declaration — 모든 후속 Story 가 의존)
- **MCT-65 = parallel** (RETROACTIVE — 이미 merged, doc 만 추가)
- **MCT-66 = MCT-65 후** (read API 가 MCT-65 partition 의무)
- **MCT-67 = MCT-64 + MCT-66 후** (executor 가 registry + reconstruction 의무)
- **MCT-68 = MCT-64 + MCT-67 후** (template 이 executor 동작 의무)
- **MCT-69 = MCT-67 후** (web 은 backtest 결과 view 가능 시점 진입, MCT-68 의무 아님)

## 5-6. 요구사항

### Blocking AC (B1~B14)

| # | AC | 충족 시점 |
|---|-----|----------|
| B1 | `mctrader_engine.strategy.tiers.DataTier` Enum + `Strategy.REQUIRED_DATA_TIERS: frozenset[DataTier]` 도입. Backtest 진입 시 tier union coverage 의무 검증, 부족 시 fail-fast. | MCT-64 |
| B2 | `STRATEGY_REGISTRY` + `@register_strategy("name")` decorator 도입. `register_strategy` 동일 name 재등록 = error. | MCT-64 |
| B3 | mctrader-data PR #4 (commit 9f51fa0) 의 collector daemon retroactive sealing. MCT-65.md 에 conflict 매핑표 + evidence inventory inline. **추가**: collector run 마다 `manifest.json` (selected symbols list + collector_run_id + started_ts) 작성. | MCT-65 |
| B4 | `scan_ticks(symbol, start, end)` / `scan_orderbook_events(symbol, start, end)` / `get_orderbook_at(symbol, ts)` API 동작. **available_from_ts** = `received_at` filter 의무. **sort key**: `(ts_utc ASC, received_at ASC, file_offset ASC)`. | MCT-66 |
| B5 | `tier_coverage(symbol, tier, start, end) -> CoverageReport` API 동작. report = `{min_ts, max_ts, gaps, collector_run_ids, symbol_manifests}`. | MCT-66 |
| B6 | Reconstruction fail-closed: gap detected / non-monotonic ts / missing baseline = halt + `GapDetectedEvent` emit. duplicate event = 동일 hash idempotent / 다른 hash halt. | MCT-66 |
| B7 | `TickReplayExecutor` ADR-002 D2 invariant — `on_candle` / `on_tick` / `on_orderbook` Strategy callback API 동일 (Backtest / Paper / Live 모두). Strategy 코드 mode 무지. | MCT-67 |
| B8 | FIFO end-of-queue matching: LIMIT 큐 끝 join + 큐 앞 소진 후 fill, partial fill 누적, cancel-replace = priority reset, 가격 레벨 disappearance = open order auto-cancel + emit, MARKET = top-of-book outward walk. **자기체결방지**: 시뮬레이션 주문 별개 layer. | MCT-67 |
| B9 | Latency model ADR-004 D3 정합: 5단계 timing (decision/submit/exchange-arrival/ack/fill), exchange-arrival 시각 = queue placement. | MCT-67 |
| B10 | Result manifest 에 source partition `collector_run_id` 다수 기록 + symbol manifest reference. ADR-006 reproducibility 동등 보장 (T2/T3 buffer). | MCT-67 |
| B11 | TickScalpingStrategy + MarketMakingStrategy 템플릿 + 단위 테스트 (각 1 fixture event window 재생 + invariant assertion). **WFO 비적용 명시** (template docstring + ADR-006 amendment note 인용). | MCT-68 |
| B12 | `GET /strategies` (registry listing) + `GET /backtests/{id}/tick_detail?cursor=&downsample=` (cursor pagination + ts-window downsample, max 10k point default) FastAPI endpoint. 127.0.0.1 + token (`~/.mctrader/local_token` 재사용). | MCT-69 |
| B13 | `02_backtest_panel.py` 확장 = strategy class selector (registry 조회) + DATA_TIER badge + tick result viewer (trade list + per-fill queue position chart + orderbook mini-ladder). | MCT-69 |
| B14 | ADR-009 §D10 (tick.v1) + §D11 (orderbook.v1) full schema 표 + ADR-005 amendment note (T2/T3 lookahead = received_at) PR merge (Phase 1). | Phase 1 (이 PR) |

### Calibration AC (C1~C5)

| # | metric | 의미 | 채택 |
|---|--------|------|------|
| C1 | `Strategy.REQUIRED_DATA_TIERS` 누락 = type error AND `register_strategy` 거부 | F-4 강제 | MCT-64 |
| C2 | `scan_ticks` / `scan_orderbook_events` 출력 = strict ascending `(ts_utc, received_at, file_offset)` 순 | F-18 sort 결정성 | MCT-66 |
| C3 | `available_from_ts > simulated_clock` event = filter out, audit log 기록 | F-3 lookahead 방어 | MCT-66 |
| C4 | TickReplayExecutor result manifest = source partition `collector_run_id` 다수 OR ≥ 1 + symbol manifest hash 의무 | F-21 reproducibility | MCT-67 |
| C5 | E2E smoke `tick_backtest_smoke_duration_seconds < 600` (10min smoke, top-1 symbol + 1일 fixture, registry → executor → result manifest) | E2E 회귀 방지 | MCT-69 (Epic close) |

### Demonstration AC (D1)

D1 = Streamlit `02_backtest_panel.py` 가 strategy class selector + DATA_TIER badge + tick result viewer 노출 = **MCT-69 의 deliverable**.

## 7. 보안 설계

- **§7.1 Trust boundary**: collector daemon = Linux server (사용자 manual deployment, 본 Epic prereq 외부). FastAPI bind = `127.0.0.1` only (MCT-48 / MCT-55 동일). token 재사용 (`~/.mctrader/local_token`).
- **§7.2 Threat model**: T2/T3 = public Bithumb WS data only (no order placement). 위협 surface = Linux server collector 운영 (사용자 책임). Replay backtest = simulated, no live API.
- **§7.3 Auth/authz**: localhost token (single user "local-user"). `GET /strategies` / `GET /backtests/{id}/tick_detail` read-only token 의무.
- **§7.4 OpRisk**: backtest CPU + memory bound (top-1 symbol + 1일 ≈ 수십만 event, bounded LRU 캐시). Collector + Backtest 동시 실행 가능 (별개 process / repo). Web FastAPI runner + Backtest CPU 경합 → 기존 BacktestLifecycleManager (MCT-48) N concurrent 제한 재사용.
- **§7.5 민감 데이터**: 없음 (T2/T3 = public data). Live mode tick execution (별도 Epic) 진입 시 동일 control plane 재사용 시 secret 누설 위험 → 별도 검토.

## 8. 테스트 / 11. 데이터 영향

### 신규 file (Phase 1)

- `docs/adr/ADR-009-ohlcv-schema.md` amendment §D10 + §D11
- `docs/adr/ADR-005-lookahead-verification.md` amendment note (T2/T3 lookahead = received_at)
- `docs/stories/MCT-63.md` (Epic, 본 file)
- `docs/stories/MCT-64.md` ~ `MCT-69.md` (6 child Story stub)

### 수정 file (Phase 2+)

- `mctrader-engine/src/mctrader_engine/strategy/tiers.py` (NEW DataTier Enum) — MCT-64
- `mctrader-engine/src/mctrader_engine/strategy/registry.py` (NEW STRATEGY_REGISTRY) — MCT-64
- `mctrader-engine/src/mctrader_engine/strategy/__init__.py` (Strategy ABC 확장 — `REQUIRED_DATA_TIERS` + `on_tick` / `on_orderbook` callbacks default no-op) — MCT-64
- `mctrader-data/src/mctrader_data/orderbook_replay.py` (NEW) — MCT-66
- `mctrader-engine/src/mctrader_engine/executor/tick_replay.py` (NEW) — MCT-67
- `mctrader-engine/src/mctrader_engine/strategy/templates/tick_scalping.py` (NEW) — MCT-68
- `mctrader-engine/src/mctrader_engine/strategy/templates/market_making.py` (NEW) — MCT-68
- `mctrader-web/src/mctrader_web/api/strategies.py` (NEW) — MCT-69
- `mctrader-web/src/mctrader_web/api/backtests.py` (MODIFY — `/tick_detail` endpoint 추가) — MCT-69
- `mctrader-web/src/mctrader_web/dashboard/pages/02_backtest_panel.py` (MODIFY) — MCT-69

### DB schema / migration

- 신규 schema: 없음 (T2/T3 partition = mctrader-data 의 §D10/§D11 신규, MCT-65 retroactive 가 이미 sealed).
- `mctrader-engine` event store SQLite = 기존 (`paper_event_store.v1`) 재사용. Backtest result store = 별도 Parquet manifest (file-based, 신규 SQLite 없음).

### Reversible

- Phase 1 doc = yes.
- Phase 2-6 implementation = yes (file revert + 0 cost rollback. T2/T3 데이터는 collector 보관 분만 영향).

## 12. Sonnet Decision Log

| packet_id | trigger | options_count | decider_pick | override? | audit_result | timestamp |
|-----------|---------|---------------|--------------|-----------|--------------|-----------|
| MCT-63-Phase1-24dec | substantive-multi-decision-batch | 24 sub × 2~3 options | A2/B1/C1/D1/E1/F1/G2/H2/I1/J1/K1/L1/M1/N1/O1/P1/Q2/R2/S1/T1/U1/V1/W1/X1 | no | direct | 2026-05-04Z (Codex 22-finding review + Sonnet 합성, 사용자 approve "지금은 예정된 작업들을 모두 수행하도록 하자") |

24/24 escalation 0건. Codex 22 finding 모두 ADOPT. Phase 1 large scope (Epic + 6 child + ADR-009 §D10/§D11 + ADR-005 amendment note).

## 13. Out-of-scope (확정 거부)

- Live mode tick execution (별도 Epic, 본 Epic = backtest only)
- T2/T3 전략 ADR-006 WFO 적용 (별도 후속 Epic, F-15 명시)
- Bithumb-faithful matching mirror (FIFO end-of-queue 보수적 simulation only, F-8)
- L3 depth-ladder snapshot (ADR-009 §D9 reservation 유지, Bithumb public WS = L2 only)
- Multi-exchange tick collection (v1 = Bithumb only, MCT-65 동일)
- Tick-level paper / live execution (Paper / Live 측 tick callback 도입은 별도 Epic)
- Hidden order / iceberg matching (FIFO simulation 가정)
- Cross-symbol portfolio strategy (Single-symbol backtest only v1)
- Fee tier queue priority (균일 priority 가정)
- Adaptive cache eviction (per-session bounded LRU N=1 v1)
- DuckDB read view (Parquet direct read v1)
- WebSocket / SSE 실시간 backtest progress (polling v1, MCT-48 / MCT-55 동일)
- Tick-level WFO statistical correction (ADR-006 D8 비적용)
