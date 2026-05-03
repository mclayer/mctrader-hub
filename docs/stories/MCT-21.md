---
story_key: MCT-21
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-002, ADR-004, ADR-005, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-21: PaperExecutor + RealtimeClock + BarAggregator + VirtualPortfolio + SimulatedFillEngine

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "PaperExecutor core (TradeExecutor Protocol Paper impl). MCT-18 의 가장 큰 single Story."

## 2. 도메인 해석

`mctrader-engine` 0.1.0 의 Paper mode 확장 = MCT-18 Epic 의 **가장 큰 single Story**. 5 components 동시 구현:
- `PaperExecutor` (async runtime, 별도 `AsyncTradeExecutor` Protocol)
- `Clock` Protocol + `RealtimeClock` + `SimulatedClock` 통합
- `BarAggregator` (closed bar only, hybrid Transaction + Ticker)
- `VirtualPortfolio` (8-state schema 보존, MVP 3-state runtime)
- `SimulatedFillEngine` (orderbook-aware VWAP + conservative bps + latency proxy)

ADR-002 mode-agnostic StrategyContext 보존 — Backtest 의 SmaStrategy 동일 코드로 Paper 실행 의무.

## 3. 관련 ADR

- ADR-002 (TradeExecutor Protocol → AsyncTradeExecutor 추가, 8-state schema 보존)
- ADR-004 (Slippage/Fee/Latency Paper + ExecutionReport schema 공유)
- ADR-005 (L2 closed bar only)
- ADR-008 D5 (real broker API call 절대 X mechanical 검증)
- ADR-009 (OHLCV v1 16-column 보존)
- ADR-010 (Pydantic v2 / Decimal canonical / async)
- ADR-011 (5 required check)
- 의존: MCT-12 + MCT-19 + MCT-20 freeze (모두 main merge)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── executor/
│   ├── async_base.py          # AsyncTradeExecutor Protocol (별도, sync 와 분리)
│   └── paper.py               # PaperExecutor (async runtime)
├── clock/
│   ├── base.py                # Clock Protocol
│   ├── realtime.py            # RealtimeClock (datetime.now UTC + time.monotonic)
│   └── simulated.py           # SimulatedClock (candle-based, Backtest 기존 통합)
├── realtime/
│   ├── aggregator.py          # BarAggregator (Transaction primary + Ticker confirmation)
│   └── stream_consumer.py     # MarketStream consumer + dispatch
├── account/
│   └── virtual.py             # VirtualPortfolio (cash / position / open_orders / pnl)
├── fill/
│   └── simulated.py           # SimulatedFillEngine (orderbook VWAP + conservative bps + latency proxy)
└── cli.py (extend)            # paper subcommand skeleton

tests/
├── test_clock.py
├── test_bar_aggregator.py
├── test_virtual_portfolio.py
├── test_simulated_fill.py
├── test_paper_executor.py     # integration (mock MarketStream + in-memory paper_storage)
├── test_paper_no_broker_api.py  # ADR-008 D5 mechanical scan
└── test_paper_cli_smoke.py
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ asyncio + Pydantic v2 + Decimal canonical
- mctrader-market `>=0.1,<0.2` (Symbol + Timeframe + Order schema 8-state)
- mctrader-market-bithumb `>=0.2,<0.3` (MCT-19 WebSocket adapter, MarketStream Protocol)
- mctrader-data `>=0.2,<0.3` (MCT-20 paper_storage)
- click + signal handlers

## 7. 설계 서사 (Codex 합성)

### 7.1 PaperExecutor pure async + 별도 AsyncTradeExecutor Protocol (A1)

**채택**: `AsyncTradeExecutor` Protocol 별도 정의, BacktestExecutor 의 sync `TradeExecutor` 분리.

```python
# executor/async_base.py
@runtime_checkable
class AsyncTradeExecutor(Protocol):
    async def run(self) -> ExecutionReport: ...
    async def cancel(self) -> None: ...

# executor/paper.py
class PaperExecutor:
    async def run(self) -> ExecutionReport: ...
    async def cancel(self) -> None: ...   # graceful shutdown trigger
```

**근거**:
- ADR-002 의 sync `TradeExecutor` 와 충돌 회피
- `ExecutionReport` / `StrategyContext` / Order schema 공유 (Protocol 분리, 산출물 동일)
- 내부 strategy/fill/portfolio = sync 함수 (event loop 안에서 호출, asyncio task 분산 X)
- CLI = `asyncio.run(executor.run())`, signal handler 통합

**StrategyContext mode-agnostic** = Backtest 의 SmaStrategy 변경 X (closed bar 받으면 동작 동일).

### 7.2 Clock Protocol + DI (A2)

```python
# clock/base.py
@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...        # timezone-aware UTC only (naive 거부)
    def monotonic(self) -> float: ...     # elapsed time / RTT 측정

# clock/realtime.py
class RealtimeClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
    def monotonic(self) -> float:
        return time.monotonic()

# clock/simulated.py (Backtest 기존 SimulatedClock 통합)
class SimulatedClock:
    # candle ts_utc 기반 progression
    ...
```

**Default**: `PaperExecutor(clock: Clock = RealtimeClock())`. CLI 또는 test = inject 가능.

**`Clock.now()` 는 UTC only** (naive datetime reject — ADR-009 boundary 와 일관).

### 7.3 BarAggregator = Hybrid (Transaction primary + Ticker fallback) (A3)

**채택**: TransactionEvent primary + TickerEvent diagnostics/confirmation.

```python
class BarAggregator:
    def __init__(self, *, timeframe: Timeframe, symbol: Symbol, exchange: str): ...
    
    def on_transaction(self, event: TransactionEvent) -> ClosedBarEvent | None:
        """누적 + boundary 도달 시 closed bar emit, partial 은 None."""
    
    def on_ticker(self, event: TickerEvent) -> None:
        """diagnostics / confirmation 만, signal path X."""
```

**Boundary 정의**:
- 1h timeframe → UTC hour boundary (`bar_end_ts` exclusive)
- 1d timeframe → KST midnight (ADR-009 D4 align)
- e.g. 00:00 ≤ trades < 01:00 → `bar_end_ts = 01:00 UTC`

**Closed bar = ADR-009 v1 schema** (open/high/low/close/volume + value 추정). `value` (거래대금) = sum(price × quantity) per transaction.

### 7.4 VirtualPortfolio + 8-state schema 보존, MVP 3-state runtime (A4)

**Order schema** = ADR-002 full 8-state (NEW / ACCEPTED / PARTIALLY_FILLED / FILLED / CANCEL_REQUESTED / CANCELED / REJECTED / EXPIRED). MCT-21 runtime = `NEW → ACCEPTED → FILLED` 만 생성.

```python
class VirtualPortfolio:
    cash: Decimal38_18
    position_quantity: Decimal38_18
    realized_pnl: Decimal38_18
    unrealized_pnl: Decimal38_18
    open_orders: dict[OrderId, Order]   # ACCEPTED 상태 (latency 기간)
    
    def submit(self, order: Order) -> None:   # NEW → ACCEPTED, open_orders 추가
    def fill(self, order_id: OrderId, fill: FillEvent) -> None:   # ACCEPTED → FILLED, position 갱신
```

**Latency 동안 ACCEPTED 유지** = Backtest 의 next-bar 즉시 fill 과 분리 (Paper realtime 핵심 차이).

**Future expansion**:
- partial fill = depth 부족 시 (Story scope 외)
- limit order = `EXPIRED` / `CANCEL_REQUESTED` (future Epic)

### 7.5 SimulatedFillEngine — Conservative hybrid (A5)

```python
class SimulatedFillEngine:
    def __init__(
        self,
        *,
        decision_to_fill_delay_ms: int = 200,    # 가설 default
        conservative_bps: Decimal = Decimal("5"),
        fee_bps: Decimal = Decimal("4"),         # Bithumb 0.04% maker=taker
        clock: Clock,
    ): ...
    
    def fill(
        self,
        *,
        order: Order,
        orderbook: OrderbookSnapshotEvent,
        decision_time: datetime,
    ) -> FillResult:
        """
        1. fill_timestamp = decision_time + decision_to_fill_delay_ms
        2. fill_price = orderbook depth-aware VWAP (BUY = ask sweep, SELL = bid sweep)
        3. fill_price ± conservative_bps (BUY = +, SELL = -)
        4. fee = fill_price × quantity × (fee_bps / 10000)
        5. visible depth 초과 = InsufficientLiquidityError (MVP, partial 비채택)
        """
```

**Default 값** (MVP 가설 — calibration evidence 전):
- `decision_to_fill_delay_ms = 200` (Bithumb public RTT proxy)
- `conservative_bps = 5` (Backtest 동일)
- `fee_bps = 4` (Bithumb spot 0.04%)

**ExecutionReport extension** (Paper-specific calibration evidence):
- `OrderEvent.slippage_bps` / `fee_bps` (기본)
- 추가 emit: `market_data_latency_ms` (WebSocket arrival lag) / `public_endpoint_rtt_ms` (REST ping baseline) / `decision_to_fill_delay_ms` (configured value vs measured)

**Visible depth 초과 = reject** (insufficient liquidity, partial fill MVP 비채택). 향후 partial fill = MVP 후속.

### 7.6 CLI `paper` subcommand split (A6)

**채택**: option (c) split.

| 책임 | MCT-21 | MCT-23 |
|---|---|---|
| `paper` subcommand parsing | ✓ skeleton | — |
| Executor factory wiring | ✓ (Bithumb stream + paper_storage + SmaStrategy + Clock injection) | — |
| `--duration` parsing | ✓ pass-through (experimental) | full timeout policy |
| SIGTERM handler | ✓ basic `signal.SIGTERM` → `executor.cancel()` | hardening + Windows compat |
| Final flush | ✓ contract (ExecutionReport JSON + equity_curve.csv + paper_storage flush) | full integration test |
| Calibration metric | ✗ | ✓ (MCT-23) |

```python
# cli.py
@main.command()
@click.option("--strategy", required=True)
# ...
def paper(...):
    executor = _build_paper_executor(...)
    asyncio.run(_run_with_signals(executor))
```

**Cancel hook** = async cancellation-friendly (`asyncio.Task.cancel()` + cleanup).

### 7.7 Test 전략 + ADR-008 D5 mechanical (A7)

**Test pyramid**:
- Pure unit (compoenent 별): Clock / BarAggregator / VirtualPortfolio / SimulatedFillEngine / Order lifecycle
- Integration: PaperExecutor + mock MarketStream (MCT-19 fixture replay) + in-memory paper_storage
- E2E = MCT-23

**Deterministic test**:
- `Clock` injection (fixed sequence)
- MarketStream replay (deterministic async iterator from JSONL fixture)
- random slippage jitter = MVP 미사용 (또는 seed 명시)

**ADR-008 D5 mechanical**:
- `tests/test_paper_no_broker_api.py` = source scan
  - `httpx.post / put / delete` 호출 = forbidden (private order endpoint 의심)
  - `Authorization` / `Api-Key` literal 사용 X
  - `1password` / `op` import X
  - subscribe = MCT-19 의 type allowlist 만 (ticker/orderbookdepth/transaction)
- AST 기반 검사 = future enhancement (MVP = source grep test)

### 7.8 Pyproject extension

```toml
dependencies = [
    "mctrader-market @ git+...",
    "mctrader-data @ git+...",
    "mctrader-market-bithumb @ git+...",   # 새 dependency (MCT-21)
    "pydantic>=2,<3",
    "click>=8",
]
```

mctrader-engine 가 mctrader-market-bithumb 직접 의존 시 future Live 또는 다른 exchange 확장 시 migration 필요. 현재 = Bithumb 단일 (acceptable). future = `MarketStream` Protocol injection 으로 Bithumb 직접 의존 제거 가능.

### 7.9 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| Limit order simulation | ✗ | market order MVP 만 |
| Partial fill | ✗ | depth 초과 = reject (insufficient liquidity) |
| CANCEL_REQUESTED / EXPIRED runtime transition | ✗ | 8-state schema 보존, runtime = 3-state |
| Multi-symbol PaperExecutor | ✗ | KRW-BTC single |
| Multi-strategy registry | ✗ | SMA only |
| Async strategy / async fill | ✗ | strategy/fill = sync 함수 |
| Production-grade signal handling | ✗ | basic SIGTERM (MCT-23 = hardening) |
| Calibration metric implementation | ✗ | MCT-23 |
| Live concurrent DuckDB read for Paper run | ✗ | finalized output 만 |

### 7.10 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | dependency = mctrader-market + market-bithumb + data (모두 git+https) | uv sync |
| AC2 | 5 required check green | CI |
| AC3 | `PaperExecutor` = `AsyncTradeExecutor` Protocol 만족 (pyright + isinstance) | pytest |
| AC4 | `Clock` Protocol + `RealtimeClock` + `SimulatedClock` 모두 만족 | pytest |
| AC5 | `BarAggregator` Transaction primary aggregation (open/high/low/close/volume/value 정확) + 1h boundary close | pytest |
| AC6 | `BarAggregator` 1d KST midnight boundary | pytest |
| AC7 | `VirtualPortfolio` 8-state schema 보존 + MVP 3-state runtime (NEW→ACCEPTED→FILLED) | pytest |
| AC8 | `SimulatedFillEngine` orderbook VWAP (BUY ask sweep / SELL bid sweep) + conservative_bps 5 + fee_bps 4 | pytest |
| AC9 | `SimulatedFillEngine` visible depth 초과 = `InsufficientLiquidityError` | pytest |
| AC10 | ExecutionReport `mode="paper"` + slippage_bps / fee_bps / market_data_latency_ms / public_endpoint_rtt_ms / decision_to_fill_delay_ms 기록 | pytest |
| AC11 | StrategyContext mode-agnostic — Backtest SmaStrategy 동일 코드로 Paper 실행 | pytest (integration) |
| AC12 | Closed bar only — partial bar 가 StrategyContext 에 dispatch X | pytest |
| AC13 | CLI `paper` subcommand skeleton + executor factory wiring + basic SIGTERM | pytest (smoke) |
| AC14 | Integration: mock MarketStream replay → BarAggregator → SmaStrategy → SimulatedFillEngine → VirtualPortfolio → ExecutionReport | pytest |
| AC15 | ADR-008 D5 mechanical: source scan = httpx.post/put/delete X, Authorization X, 1password import X | pytest (test_paper_no_broker_api) |

### 7.11 Codex 적용

7/7 area 채택. ADR conflict 0/7 (별도 `AsyncTradeExecutor` Protocol = ADR-002 sync `TradeExecutor` 병존, 8-state schema 보존, ADR-008 D5 mechanical 검증).

## 8-11

(Phase 2 = mctrader-engine 5 components + paper subcommand skeleton + AC1~AC15.)
