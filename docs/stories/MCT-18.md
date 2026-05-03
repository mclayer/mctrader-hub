---
story_key: MCT-18
status: phase:요구사항
component: hub
type: epic
related_stories: MCT-19, MCT-20, MCT-21, MCT-22, MCT-23
related_adrs: ADR-002, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011
parent_epic: MCT-12 (predecessor)
---

# MCT-18: Paper mode = realtime + 가상 자금 (Epic)

## 1. 사용자 요구사항 (verbatim)

> "다음 작업 수행해" — Sonnet decider 자율 결정: 후속 candidate 7개 중 **Paper mode** = ADR-006 promotion gate (Backtest→Paper→Live) 의 두 번째 단계, ADR-002 3-mode 의 두 번째 적용, 다른 candidate 의 baseline.

## 2. 도메인 해석

mctrader 의 **두 번째 implementation Epic** (MCT-12 Backtest 다음). Backtest 의 simulated assumptions (slippage / fee / latency) 를 **realtime market 환경에서 OOS validation**.

핵심 가치 = ADR-006 promotion gate 의 Paper 단계 = **calibration mechanism** (Backtest 와 ExecutionReport schema 동일, calibration metric 으로 비교). Live mode 는 Paper validation 통과 후 별도 Epic.

## 3. 관련 ADR (Paper mode 핵심)

| ADR | Paper mode 적용 |
|---|---|
| ADR-002 | TradeExecutor 3-mode 의 두 번째 = PaperExecutor / StrategyContext mode-agnostic 의무 |
| ADR-004 | Slippage/Fee/Latency Paper 적용 (orderbook-aware slippage + 실제 latency proxy) + ExecutionReport schema 공유 |
| ADR-005 | L2 visible_window = closed bar only (partial bar 는 signal path 미사용) |
| ADR-006 | promotion gate B→P→L multi-metric AND, Paper artifacts 가 calibration evidence |
| ADR-007 | RiskGate Paper minimal enforcement (kill switch decision = order block + report event) |
| ADR-008 D5 | **Paper = secret 금지** (public endpoint 만, real broker API 호출 절대 X) |
| ADR-009 | Paper-generated OHLCV = separate partition `mode=paper/` (canonical historical 와 격리) + lineage extension (WebSocket batch hash) |

## 4. 관련 코드 경로 (5 신규 child Story 분담)

```
mctrader-market-bithumb/        # MCT-19 (WebSocket adapter)
└── src/mctrader_market_bithumb/
    ├── ws_client.py             # WebSocket client (subscribe + heartbeat + reconnect)
    └── stream.py                # ticker/orderbook/trade event stream (Protocol)

mctrader-data/                   # MCT-20 (Paper write-side + lineage extension)
└── src/mctrader_data/
    ├── paper_storage.py         # mode=paper partition writer
    └── lineage.py (extend)      # WebSocket batch hash mode

mctrader-engine/                 # MCT-21 (PaperExecutor + components)
└── src/mctrader_engine/
    ├── executor/
    │   └── paper.py             # PaperExecutor (TradeExecutor Protocol)
    ├── realtime/
    │   ├── clock.py             # RealtimeClock (vs SimulatedClock)
    │   ├── aggregator.py        # BarAggregator (closed bar dispatch only)
    │   └── stream_consumer.py   # Stream → BarAggregator 연결
    ├── account/
    │   └── virtual.py           # VirtualPortfolio (cash + position simulation)
    ├── fill/
    │   └── simulated.py         # SimulatedFillEngine (orderbook-aware + latency proxy)
    └── cli.py (extend)          # paper subcommand

mctrader-engine/                 # MCT-22 (RiskGate minimal Paper enforcement)
└── src/mctrader_engine/risk/
    ├── kill_switch.py           # MAX_DAILY_LOSS + DRAWDOWN_LIMIT (5 중 2 minimum)
    └── enforcer.py              # PaperExecutor 와의 hook

mctrader-engine/                 # MCT-23 (Calibration metric + CLI integration acceptance)
└── src/mctrader_engine/
    ├── calibration/
    │   └── metric.py            # fill_price_deviation_bps / latency_p50_p95 / slippage_realized_bps / trade_count_delta / max_drawdown_delta
    └── tests/test_paper_e2e.py  # AC1~AC15 통합 acceptance
```

## 5-6. 요구사항 / 외부 지식

- Bithumb WebSocket public endpoint: `wss://pubwss.bithumb.com/pub/ws` (ticker + orderbook + transaction)
- Subscribe message format / heartbeat / reconnection robustness
- Asyncio (httpx async or `websockets` library)
- ADR-009 OHLCV v1 schema + Decimal38_18 + UTC timestamp 보존
- `RealtimeClock` (`time.monotonic` + UTC datetime — vs `SimulatedClock` deterministic)
- pyright strict 완화 (Phase 2 baseline 동일)
- pytest + Linux+Windows CI matrix (mctrader-data 만 — engine 는 Linux only)

## 7. 설계 서사 (Codex 합성 결정)

### 7.1 End-to-end acceptance (A1 — 2 layer)

**Blocking AC** (Epic 종료 의무):

| # | AC | 검증 |
|---|---|---|
| B1 | CLI `mctrader-cli paper --strategy sma --symbol KRW-BTC --tf 1h --initial-capital 1000000 --duration 7d` 종료 코드 = 0 (graceful SIGTERM 또는 duration 만료) | bash exit |
| B2 | ExecutionReport JSON `mode="paper"` + `schema_version="execution_report.v1"` validation 통과 (Backtest 와 동일 schema) | pydantic v2 validator |
| B3 | equity_curve.csv = Backtest 와 동일 6-column schema (Decimal string + ISO-8601 Z) | Phase 2 동일 |
| B4 | **Mode-agnostic verification** — `SmaStrategy` 가 Backtest 와 동일 코드로 Paper 에서 실행 (StrategyContext interface 동일) | pytest + integration |
| B5 | Paper OHLCV = `mode=paper/...` separate partition (canonical Backtest 데이터와 격리) | mctrader-data scan_candles + filter test |
| B6 | RiskGate minimal (MAX_DAILY_LOSS + DRAWDOWN_LIMIT) decision = order block + RiskGateEvent 기록 | pytest |
| B7 | Public-only enforcement — Authorization header / Api-Key 사용 X (Phase 2 secret_guard 와 동일) | mctrader-market-bithumb policy lint |

**Calibration AC** (Paper 의 OOS validation evidence):

| # | metric | 의미 |
|---|---|---|
| C1 | `fill_price_deviation_bps` | Backtest assumption 의 fill price 와 실제 Paper realtime fill price 의 deviation (분포) |
| C2 | `latency_p50_p95_ms` | public endpoint RTT + WebSocket message arrival lag 의 percentile |
| C3 | `realized_slippage_bps` | composite formula 가 실제 orderbook 으로 만든 slippage 의 distribution |
| C4 | `trade_count_delta` | 동일 strategy 의 Backtest replay vs Paper run 의 trade 횟수 차이 |
| C5 | `max_drawdown_delta` | drawdown 차이 (Backtest assumption conservativeness 검증) |

**Demonstration AC**:

| # | AC | 검증 |
|---|---|---|
| D1 | mctrader-web Streamlit dashboard 가 Paper run artifacts (finalized) 도 read | manual review (defer 가능) |

### 7.2 5 child Story 분해

```
                  MCT-19 (Bithumb WebSocket adapter)
                  ┌────────┴────────┐
                  ↓                 ↓
              MCT-20            MCT-21 (PaperExecutor core, parallel 가능)
              (Paper            (RealtimeClock + BarAggregator + VirtualPortfolio + FillEngine)
               data store)
                  └────────┬────────┘
                           ↓
                  MCT-22 (RiskGate minimal Paper enforcement)
                           ↓
                  MCT-23 (Calibration metric + CLI integration)
```

| Story | repo | 의존 |
|---|---|---|
| MCT-19 | mctrader-market-bithumb | MCT-12 freeze (mctrader-market 0.1.0) |
| MCT-20 | mctrader-data | MCT-12 freeze (ADR-009 v1 schema, mode partition extension) |
| MCT-21 | mctrader-engine | MCT-12 freeze + MCT-19 freeze (stream Protocol) |
| MCT-22 | mctrader-engine | MCT-21 freeze (PaperExecutor hook) |
| MCT-23 | mctrader-engine | MCT-19 + MCT-20 + MCT-21 + MCT-22 freeze (E2E) |

**Parallel start = MCT-19 + MCT-20** (WebSocket adapter + Paper storage write-side 동시 가능).

### 7.3 Realtime data source = WebSocket primary (A2)

**채택**: Bithumb WebSocket (`wss://pubwss.bithumb.com/pub/ws`) primary.

**비채택**:
- REST polling = polling interval 이 latency / slippage 측정 오염 → calibration value 약함
- Hybrid (WebSocket + REST fallback) = MCT-18 scope 비대화 (별도 Story)

**Stream subscriptions** (MCT-19 결정):
- ticker (1m / continuous)
- orderbook (depth snapshot + delta updates — slippage estimation)
- transaction (per-trade events)

REST polling = development fallback (degraded mode, calibration metric 에 명시 X).

### 7.4 Closed bar only (A3, ADR-005 L2 보존)

**채택**: completed bar only.

- BarAggregator 가 partial bar state 를 maintain (1h 단위, 60 분 of tick aggregation)
- bar_end_ts 시점에만 StrategyContext 에 dispatch
- Strategy 는 Backtest 와 동일 visible_window API 사용

**Diagnostics path** (분리):
- 진행 중 partial bar 정보 = dashboard / log 만 (signal path X)
- mctrader-web 의 future Story 에서 live partial bar visualization

### 7.5 Simulated fill engine (A4 — Conservative hybrid)

**채택**: orderbook-aware reference price + composite slippage + latency proxy.

**Fill mechanism**:
1. T0 = strategy decision time
2. simulated latency: T0 + `decision_to_fill_delay_ms` (configurable proxy)
3. fill timestamp = T0 + latency
4. fill price = orderbook depth-aware VWAP (BUY = ask sweep, SELL = bid sweep) + configurable conservative bps
5. fee = Bithumb 0.04% (ADR-004 동일)

**Latency naming** (ADR-008 align — "real broker RTT" 표현 회피):
- `market_data_latency_ms` = WebSocket message arrival lag
- `public_endpoint_rtt_ms` = HTTP REST ping (calibration baseline)
- `decision_to_fill_delay_ms` = strategy decision → simulated fill timestamp delta

**Real broker API call 절대 X** (ADR-008 D5).

### 7.6 PaperExecutor placement (A5)

**채택**: `mctrader-engine/src/mctrader_engine/executor/paper.py` + small components (`realtime/` + `account/` + `fill/`).

**비채택**:
- 별도 `mctrader-paper` repo = 6-repo invariant 위반 (ADR-002)
- `realtime_base.py` 추상화 = premature (Live Epic 시점에 실제 중복 발견 후 추출)

**Stream client = Protocol injection** (mctrader-engine 가 Bithumb 구체에 직접 의존 X):
- mctrader-engine `realtime/stream_consumer.py` 가 `MarketStream` Protocol 정의
- mctrader-market-bithumb `BithumbMarketStream` impl
- CLI `paper` subcommand 에서 wire-up

### 7.7 Paper data write-side (A6 — Separate partition)

**채택**: `{root}/market/ohlcv/schema_version=ohlcv.v1/mode=paper/exchange=.../symbol=.../timeframe=.../year=.../month=.../date=.../*.parquet`

**Canonical Backtest reader** (MCT-15) = `mode=historical` 또는 default (mode 미지정) 만 read. `mode=paper` 는 explicit query.

**Lineage extension** (MCT-20 결정):
- `adapter_name = "mctrader-market-bithumb-ws"` (REST adapter 와 분리)
- `adapter_version = 0.1.0+`
- `fetched_at_utc = aggregation_finalized_at` (REST fetch time 아님)
- `response_hash` = WebSocket normalized message batch canonical JSONL hash

ADR-009 v1 schema 자체 변경 X (16-column 보존). lineage extension 만 Paper documentation 명시.

### 7.8 RiskGate minimal Paper enforcement (A7)

**채택**: 5 kill switch 중 MCT-18 = **2 critical 만**:
- `MAX_DAILY_LOSS` (e.g. 초기 자본 의 5% 일일 손실)
- `DRAWDOWN_LIMIT` (e.g. peak 의 10% drawdown)

**Trigger 시 동작** (RiskGateBlocked + RiskGateEvent ExecutionReport stream):
- order intent 차단 (Paper 의 simulated order)
- log 기록
- continue (terminate X — Paper run 은 자체 종료 trigger 별도)

**Out-of-scope** (full RiskGate Epic):
- CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL = future Epic
- production-grade risk operator UI = future
- automatic position liquidation = future

### 7.9 Out-of-scope (명시 거부)

| 항목 | MCT-18 미포함 | 이유 |
|---|---|---|
| Live mode | ✗ | 별도 Epic (1Password CLI Secret + GitHub environment protection 의무) |
| WFO promotion gate full automation | ✗ | manual trigger + artifact-based evaluation 만 |
| Multi-symbol (KRW-ETH 등) | ✗ | KRW-BTC only 유지 |
| Multi-strategy registry | ✗ | SMA only 유지 |
| Production-grade WebSocket robustness | ✗ | basic reconnect/backoff 만 |
| Full RiskGate (5 kill switch) | ✗ | minimal 2 (MAX_DAILY_LOSS + DRAWDOWN_LIMIT) |
| Streamlit live partial bar visualization | ✗ | finalized output read only |
| Async streamline (HTTP REST async client) | ✗ | sync REST + async WebSocket only |
| Multi-exchange | ✗ | Bithumb only |
| PyPI publish | ✗ | local editable + git+https main |

### 7.10 CFP-60 debut-audit checklist

각 child Phase 2 merge 직후 codeforge plugin 의 audit signal check + 7-카테고리 평가:
- **lane-progression** (B→P 전환 evidence 명확성)
- **decision-table** (Paper run config / promotion gate metric 결정 표)
- **workflow-invariant** (ADR-008 D5 secret 금지 mechanical 검증)
- **contract-schema** (ExecutionReport schema 공유 + ADR-009 lineage extension)

추가 finding 시 mclayer/plugin-codeforge issue (`audit:from-mctrader-debut + category:*`).

### 7.11 Phase 1 / Phase 2 분담

**Phase 1** (본 Story):
- 본 Epic doc + 5 child stub (MCT-19 ~ MCT-23) registration
- AC freeze (B1~B7 + C1~C5 + D1)
- CFP-60 debut-audit checklist
- Phase 1 PR

**Phase 2** (child PR):
- 5 신규 issue Phase 1 brainstorm + Phase 2 implementation
- 각 child = Codex 7-area review → Sonnet 합성 → Story doc → PR

### 7.12 Codex 적용

7/7 area 채택. ADR conflict 0/7 (별도 mctrader-paper repo 비채택 = no conflict).

## 8-11

(Phase 2 = 5 child Story PR 분담. 본 Epic Story 자체는 doc-only.)
