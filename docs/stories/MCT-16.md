---
story_key: MCT-16
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-009, ADR-010, ADR-011
---

# MCT-16: mctrader-engine BacktestExecutor + SMA + ExecutionReport + CLI

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-16: mctrader-engine BacktestExecutor + SMA strategy + 결과"

## 2. 도메인 해석

`mctrader-engine` repo 의 첫 commit. **MCT-12 Epic 의 가장 큰 single Story** — ADR-002/003/004/005/006/007/009 의 7 개 ADR 을 동시 적용하는 reference impl.

핵심 책임:
- ADR-002 TradeExecutor Protocol 의 Backtest mode 구현 (3 mode 중 첫 적용)
- ADR-003 self-built backtest core (88 score, lib = adapter only)
- ADR-004 Slippage/Fee/Latency Backtest mode + ExecutionReport schema (3 mode 공유 — calibration mechanism)
- ADR-005 Lookahead bias 4-layer (L2 + L3 minimal — L1/L4 defer)
- ADR-006 Promotion gate Backtest 1 단계 완성 (single-window — full WFO 별도 Epic)
- ADR-007 RiskGate **minimal pass-through hook** (full kill switch 별도 Epic)
- ADR-002 StrategyContext mode-agnostic (visible_window + read-only state)

## 3. 관련 ADR

- ADR-002 (TradeExecutor + StrategyContext + 8-state)
- ADR-003 (self-built core)
- ADR-004 (Slippage/Fee/Latency + ExecutionReport)
- ADR-005 (Lookahead 4-layer)
- ADR-006 (WFO + promotion gate)
- ADR-007 (RiskGate)
- ADR-009 (Candle Protocol)
- ADR-010 / ADR-011 (Python + uv + CI)
- 의존:
  - MCT-13 (`mctrader-market` 0.1.0 freeze) — CandleLike + Symbol + Timeframe + Order + 8-state + can_transition() + UTCDateTime + Decimal38_18 + NewType IDs
  - MCT-15 (`mctrader-data` 0.1.0 freeze) — `scan_candles(...) → Iterable[CandleLike]`
  - MCT-14 (`mctrader-market-bithumb` 0.1.0 freeze) — raw fixture 가 deterministic test input

## 4. 관련 코드 경로

```
mctrader-engine/
├── pyproject.toml
├── uv.lock
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/ci.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
├── src/mctrader_engine/
│   ├── __init__.py
│   ├── strategy/
│   │   ├── base.py             # Strategy Protocol + Decision dataclass
│   │   ├── context.py          # StrategyContext Protocol (visible_window + read-only state)
│   │   └── sma.py              # SmaStrategy (event-driven per-bar)
│   ├── executor/
│   │   ├── base.py             # TradeExecutor Protocol (ADR-002, 3 mode 공유)
│   │   ├── backtest.py         # BacktestExecutor (self-built core, per-bar loop)
│   │   ├── slippage.py         # composite slippage formula (ADR-004)
│   │   ├── fee.py              # ADR-004 Bithumb 0.04% maker=taker
│   │   └── portfolio.py        # PortfolioState (ts_utc/cash/position/equity/unrealized_pnl)
│   ├── lookahead/
│   │   ├── reader.py           # MarketDataReader (L2 visible_window guard, ADR-005)
│   │   └── audit.py            # used_data_window post-hoc check (L3 minimal)
│   ├── risk/
│   │   └── gate.py             # RiskGate Protocol + RiskGateBlocked + NullRiskGate (pass-through)
│   ├── report/
│   │   ├── schema.py           # ExecutionReport / OrderEvent / StrategyDecision / RiskGateEvent (Pydantic v2)
│   │   ├── equity.py           # EquityRowModel + EquityCurveWriter (Decimal string CSV)
│   │   └── summary.py          # final equity / max drawdown / sharpe / win rate
│   ├── clock.py                # SimulatedClock (deterministic UTC)
│   └── cli.py                  # `mctrader-cli backtest ...`
└── tests/
    ├── test_strategy_sma.py
    ├── test_backtest_executor.py
    ├── test_lookahead_l2.py    # visible_window guard (ADR-005 L2)
    ├── test_lookahead_l3.py    # used_data_window post-hoc (ADR-005 L3)
    ├── test_slippage.py        # composite formula
    ├── test_fee.py             # Bithumb 0.04%
    ├── test_execution_report.py
    ├── test_equity_curve_csv.py
    ├── test_risk_gate.py       # NullRiskGate + Protocol satisfaction
    ├── test_cli.py
    └── test_e2e_bithumb_sma.py # MCT-14 raw fixture → MCT-15 storage → MCT-16 backtest → AC B1~B6
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ + numpy + pandas + Pydantic v2 + click (CLI)
- mctrader-market `>=0.1,<0.2` (CandleLike + Symbol + Timeframe + Order + 8-state)
- mctrader-data `>=0.1,<0.2` (scan_candles)
- pyright strict + pytest + ADR-011 5 required check

## 7. 설계 서사 (요약)

### 7.1 SMA signal generation = event-driven per-bar (A1 결정)

**채택**: event-driven per-bar (vectorized 비채택).

**근거**:
- ADR-003 self-built core = per-bar loop 의무
- ADR-002 StrategyContext mode-agnostic = visible_window 만 (Backtest/Paper/Live 동일 strategy 코드)
- ADR-005 L2 = mechanical lookahead prevention (visible_window guard)
- 7-day 1h = 168 candle 규모 → 성능 우려 무시 가능

```python
# strategy/sma.py
class SmaStrategy:
    def __init__(self, fast: int = 5, slow: int = 20):
        self._fast = fast
        self._slow = slow

    def on_bar(self, ctx: StrategyContext) -> Decision:
        window = list(ctx.visible_window(self._slow))  # max(slow) candle 만 노출
        if len(window) < self._slow:
            return Decision.HOLD()  # warmup
        fast_ma = self._sma(window[-self._fast:])
        slow_ma = self._sma(window)
        prev_fast_ma = self._sma(window[-self._fast-1:-1])
        prev_slow_ma = self._sma(window[:-1])

        # cross detection
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma and ctx.position_quantity == 0:
            return Decision.BUY(target_quantity=...)
        if prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma and ctx.position_quantity > 0:
            return Decision.SELL(target_quantity=ctx.position_quantity)
        return Decision.HOLD()

    def _sma(self, candles: list[CandleLike]) -> Decimal:
        # Decimal canonical (ADR-010)
        return sum(c.close for c in candles) / Decimal(len(candles))
```

**vectorized 가능성**: analytics / report 후처리 (summary 계산) 만 numpy/pandas 허용. core decision loop = event-driven.

### 7.2 Lookahead 4-layer minimal subset (A2 결정)

| Layer | MCT-12 | 구현 위치 |
|---|---|---|
| L1 — libcst lint (static) | ✗ defer | future Story |
| L2 — `visible_window` runtime guard | ✓ **required** | `lookahead/reader.py::MarketDataReader` |
| L3 — used_data_window post-hoc | ✓ **minimal required** | `report/schema.py::StrategyDecision.used_data_window` + `lookahead/audit.py` |
| L4 — known-bias fixture | ✗ defer | future Story |

**L2 — `MarketDataReader.visible_window(n)`**:
```python
class MarketDataReader:
    def __init__(self, all_candles: list[CandleLike], current_idx: int):
        self._all = all_candles
        self._current_idx = current_idx  # SimulatedClock 의 현재 시점

    def visible_window(self, n: int) -> Iterable[CandleLike]:
        # current_idx 까지의 candle 만 노출 (current bar 포함, future bar X)
        start = max(0, self._current_idx - n + 1)
        return self._all[start : self._current_idx + 1]
```

**Timestamp semantics** (ADR-005):
- `decision_ts` = `bar_end_ts` (방금 닫힌 bar 까지 visible)
- `fill_ts` = `next_bar_open_ts` (= `bar_end_ts`, ADR-004 next-bar fill)
- `bar_end_ts == next_bar_open_ts` (ADR-005 close_time)
- ExecutionReport 에 decision_ts ≠ fill_ts 분리 기록 (의미 혼동 회피)

**L3 — `StrategyDecision.used_data_window`**:
```python
class StrategyDecision(BaseModel):
    ts_utc: UTCDateTime         # decision_ts
    decision_kind: Literal["BUY", "SELL", "HOLD"]
    used_data_window_start: UTCDateTime
    used_data_window_end: UTCDateTime  # MUST < ts_utc
    target_quantity: Decimal38_18 | None
```

post-hoc audit (`lookahead/audit.py`):
- 모든 `StrategyDecision` 의 `used_data_window_end <= ts_utc` 검증
- violation 시 LookaheadBiasError raise

### 7.3 ExecutionReport schema (A3 결정)

**위치**: `mctrader-engine/src/mctrader_engine/report/schema.py` (contract module 분리, 추후 shared package 이동 가능).

```python
class ExecutionReport(BaseModel):
    schema_version: Literal["execution_report.v1"] = "execution_report.v1"
    run_id: RunId
    mode: Literal["backtest", "paper", "live"]
    strategy: StrategyConfig            # name + params
    symbol: Symbol
    timeframe: Timeframe
    period: PeriodConfig                # start / end (UTC)
    initial_capital: Decimal38_18
    slippage_fee_latency_config: SlippageFeeLatencyConfig
    events: list[Event]                 # OrderEvent | StrategyDecision | RiskGateEvent
    summary: SummaryStats
    created_at: UTCDateTime

class OrderEvent(BaseModel):
    ts_utc: UTCDateTime                 # fill_ts
    order_id: OrderId
    status_from: OrderStatus
    status_to: OrderStatus              # MUST: can_transition(from, to) (MCT-13 lifecycle)
    fill_price: Decimal38_18 | None
    fill_quantity: Decimal38_18 | None
    fee_bps: Decimal38_18 | None
    slippage_bps: Decimal38_18 | None

class StrategyDecision(BaseModel):
    ts_utc: UTCDateTime                 # decision_ts
    decision_kind: Literal["BUY", "SELL", "HOLD"]
    used_data_window_start: UTCDateTime
    used_data_window_end: UTCDateTime   # < ts_utc (ADR-005 L3)
    target_quantity: Decimal38_18 | None

class RiskGateEvent(BaseModel):
    ts_utc: UTCDateTime
    blocked: bool                        # MCT-12 = always False (pass-through)
    trigger: str | None                  # 5 kill switch trigger name (future)
    reason: str | None
```

**OrderEvent 검증**: `status_from → status_to` = MCT-13 `can_transition()` 통과 의무 (8-state lifecycle). model validator 로 강제.

**RiskGateEvent emit 정책**: MCT-12 = pass-through 만 → `blocked=False` event 전 bar 마다 발화 = bloat. **Configured RiskGate (≠ NullRiskGate) 또는 blocked=True 일 때만 emit**.

### 7.4 equity_curve.csv schema (A4 결정)

**Pydantic `EquityRowModel`**:
```python
class EquityRowModel(BaseModel):
    ts_utc: UTCDateTime
    equity: Decimal38_18
    position_quantity: Decimal38_18
    realized_pnl: Decimal38_18
    unrealized_pnl: Decimal38_18
    cash: Decimal38_18
```

**CSV writer** (`report/equity.py::EquityCurveWriter`):
- Column 순서 (deterministic): `ts_utc,equity,position_quantity,realized_pnl,unrealized_pnl,cash`
- timestamp = ISO-8601 "Z" UTC (예: `2026-05-02T03:00:00Z`)
- Decimal = **string serialize** (precision 보존, float 미사용)
- Header row 의무
- 매 bar end 마다 1 row (warmup 포함 — equity = initial_capital 유지)

**MCT-17 read contract** (downstream): pandas `read_csv(..., dtype=str)` 의무 (Decimal string column 자동 float 변환 회피). docstring + README 에 명시.

### 7.5 RiskGate minimal pass-through hook (A5 결정)

**Protocol** (`risk/gate.py`):
```python
@runtime_checkable
class RiskGate(Protocol):
    def check(self, *, decision: StrategyDecision, portfolio_state: PortfolioState) -> None: ...
        # 통과 = no-op / blocked = raise RiskGateBlocked

class RiskGateBlocked(Exception):
    def __init__(self, *, trigger: str, reason: str): ...

class NullRiskGate:
    """MCT-12 default — pass-through, no kill switch."""
    def check(self, *, decision, portfolio_state): pass
```

**PortfolioState** (`executor/portfolio.py`) — first commit minimal:
```python
class PortfolioState(BaseModel):
    ts_utc: UTCDateTime
    symbol: Symbol
    cash: Decimal38_18
    position_quantity: Decimal38_18
    equity: Decimal38_18                 # cash + position_quantity * current_close
    unrealized_pnl: Decimal38_18
```

**BacktestExecutor 통합**:
```python
class BacktestExecutor:
    def __init__(
        self,
        strategy: Strategy,
        candle_provider: CandleProvider,
        slippage_model: SlippageModel,
        fee_model: FeeModel,
        initial_capital: Decimal,
        risk_gate: RiskGate | None = None,    # MCT-12 = NullRiskGate or None
    ): ...

    def _on_bar(self, candle):
        ctx = self._build_context(candle)
        decision = self._strategy.on_bar(ctx)
        if decision.kind != "HOLD":
            if self._risk_gate is not None:
                self._risk_gate.check(decision=decision, portfolio_state=self._portfolio)
            self._submit_order(decision)
```

**RiskGate full kill switch (5 trigger)** = future Epic. drawdown / consecutive_losses / unusual_activity / external_signal 등의 metric 은 본 Story 미수집 (PortfolioState extension defer).

### 7.6 CLI option set (A6 결정)

**Required**:
- `--strategy` (`sma` only — 다른 strategy = future)
- `--symbol` (canonical "KRW-BTC", `Symbol.from_string`)
- `--tf` (Timeframe StrEnum)
- `--start` (ISO 8601 UTC inclusive)
- `--end` (ISO 8601 UTC exclusive)
- `--fast` (default = 5)
- `--slow` (default = 20)

**Operational** (재현성):
- `--output-dir` (default = `./out/`) — ExecutionReport JSON + equity_curve.csv 출력
- `--run-id` (default = auto-generated deterministic = `bt-{strategy}-{symbol}-{tf}-{start}-{end}-{fast}-{slow}`)
- `--initial-capital` (default = `1000000` KRW)
- `--root` (storage root override — MCT-15 align)
- `--snapshot-id` (특정 OHLCV snapshot — replay)

**Defer**:
- `--fee-bps / --slippage-bps` (composite model 친화 X — ADR-004 default constant 사용)
- `--seed` (deterministic backtest = no random, 불필요)
- `--dry-run` (의미 약함)

**Validation**:
- `Symbol.from_string` (canonical 검증)
- `Timeframe StrEnum` binding
- `start < end` + UTC + `tzinfo == timezone.utc` 의무
- `fast < slow` + `fast > 0` + `slow > 0`
- `initial_capital > 0`
- requested `[start, end)` ⊆ MCT-15 `scan_candles` 범위 (없으면 `InsufficientCoverageError`)

### 7.7 StrategyContext + Slippage/Fee/Latency (A7 결정)

**StrategyContext Protocol** (`strategy/context.py`):
```python
@runtime_checkable
class StrategyContext(Protocol):
    # market data — visible_window only (ADR-005 L2)
    def visible_window(self, n: int) -> Iterable[CandleLike]: ...

    # read-only execution state (lookahead source X — past + present)
    @property
    def current_ts(self) -> datetime: ...
    @property
    def position_quantity(self) -> Decimal: ...
    @property
    def cash(self) -> Decimal: ...
```

**ADR-002 "visible_window API only" 해석**: market data access only. Position/cash 는 execution state (future market data 아님) → 노출 허용. README + docstring 에 명시.

**Strategy contract**:
```python
@runtime_checkable
class Strategy(Protocol):
    def on_bar(self, ctx: StrategyContext) -> Decision: ...

@dataclass(frozen=True)
class Decision:
    kind: Literal["BUY", "SELL", "HOLD"]
    target_quantity: Decimal | None = None  # BUY/SELL only

    @classmethod
    def BUY(cls, target_quantity: Decimal) -> "Decision": ...
    @classmethod
    def SELL(cls, target_quantity: Decimal) -> "Decision": ...
    @classmethod
    def HOLD(cls) -> "Decision": ...
```

**Slippage / Fee / Latency** (executor 책임, strategy 미관여):

| Component | MCT-12 Backtest 적용 |
|---|---|
| Latency | 0 (next-bar fill) |
| Fee | Bithumb 0.04% maker=taker (ADR-004) |
| Slippage | composite `base_bps + size_factor*f(x) + volatility_factor*g(v) + tick_bps_adjustment` |

**Slippage formula details**:
- `base_bps` = 5 bps (Bithumb spot 보수적 default)
- `size_factor * f(x)` = `0.0` (size 작음 — 5만 KRW ≪ Bithumb depth)
- `volatility_factor * g(v)` = `volatility_factor * std(returns, window=20)` (rolling std — ATR 보다 단순)
- `tick_bps_adjustment` = `0` (Bithumb tick metadata 부재 — `[VERIFY]` future Story)

**Per trade event**: ExecutionReport `OrderEvent.slippage_bps` + `fee_bps` 기록 (calibration mechanism 의무).

### 7.8 Pyproject + 첫 commit standard

```toml
[project]
name = "mctrader-engine"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
  "mctrader-market>=0.1,<0.2",
  "mctrader-data>=0.1,<0.2",
  "pydantic>=2,<3",
  "numpy>=1.26,<2",
  "pandas>=2.2,<3",
  "click>=8",
]

[project.scripts]
mctrader-cli = "mctrader_engine.cli:main"
```

**CI** (ADR-011): 5 required check + pre-commit + Linux ubuntu-latest. Windows lane = optional (MCT-15 가 storage Windows 책임 — engine 은 read-only consume).

### 7.9 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| Live mode / Paper mode | ✗ | ADR-002 — 별도 Epic |
| WFO / promotion gate full | ✗ | ADR-006 — single-window only |
| RiskGate 5 kill switch full | ✗ | ADR-007 — minimal pass-through hook |
| Multi-strategy registry | ✗ | SMA only |
| Multi-symbol / portfolio aggregation | ✗ | KRW-BTC only |
| ATR volatility metric | ✗ | rolling std 사용 (ADR-004 metric 미강제) |
| Lookahead L1 (libcst lint) | ✗ defer | future Story |
| Lookahead L4 (known-bias fixture) | ✗ defer | future Story |
| `--fee-bps / --slippage-bps` CLI override | ✗ defer | composite model 친화 X |
| Async / streaming engine | ✗ | sync per-bar loop |
| Web realtime | ✗ | MCT-17 = finalized CSV read only |

### 7.10 Acceptance (Phase 2)

| # | AC | 검증 | Blocking AC |
|---|---|---|:---:|
| AC1 | `pyproject.toml` `version = "0.1.0"` + dependency = mctrader-market/data + numpy/pandas/pydantic/click | uv sync --frozen | — |
| AC2 | 5 required check green | CI | — |
| AC3 | `BacktestExecutor` 가 `TradeExecutor` Protocol 만족 (pyright + isinstance) | pytest | — |
| AC4 | `SmaStrategy.on_bar(ctx)` event-driven per-bar (vectorized 미사용) — `visible_window` 만 access | pytest (visible_window monkey-patch 검증) | — |
| AC5 | L2 — `MarketDataReader.visible_window(n)` 가 `current_idx` 이후 candle access X | pytest (future bar 접근 = LookaheadBiasError) | — |
| AC6 | L3 — `StrategyDecision.used_data_window_end < ts_utc` 모든 event | pytest (audit replay) | — |
| AC7 | ExecutionReport schema validation (model_json_schema export + roundtrip) | pytest | **B2** |
| AC8 | OrderEvent `status_from → status_to` = `can_transition()` 통과 | pytest (8-state matrix) | — |
| AC9 | equity_curve.csv = `ts_utc,equity,position_quantity,realized_pnl,unrealized_pnl,cash` 순서 + Decimal string + ISO-8601 Z + header | pytest (deterministic write/read) | **B3** |
| AC10 | NullRiskGate pass-through + RiskGate Protocol 만족 | pytest | — |
| AC11 | CLI `mctrader-cli backtest --strategy sma --symbol KRW-BTC --tf 1h --start ... --end ... --fast 5 --slow 20` 종료 코드 0 | pytest (subprocess) | **B1** |
| AC12 | CLI validation: `start < end` / `fast < slow` / Symbol canonical / Timeframe enum / UTC / initial_capital > 0 | pytest | — |
| AC13 | Slippage formula: composite (base_bps + size_factor + volatility_factor*std + tick_bps_adjustment) → ExecutionReport `slippage_bps` 기록 | pytest | — |
| AC14 | Fee = 0.04% maker=taker (Bithumb spot, ADR-004) → ExecutionReport `fee_bps` 기록 | pytest | — |
| AC15 | E2E test: MCT-14 raw fixture → MCT-15 storage → MCT-16 backtest → equity_curve + ExecutionReport 검증 | pytest | **B4 + B5 + B6** |

**Blocking AC mapping** (MCT-12 Epic):
- B1 (CLI exit 0) = AC11
- B2 (ExecutionReport JSON schema) = AC7
- B3 (equity_curve.csv schema) = AC9
- B4 (ADR-009 OHLCV schema) = AC15 (MCT-15 의 책임 통해 검증)
- B5 (lookahead 4-layer pass) = AC5 + AC6
- B6 (5 repo import smoke) = AC11 + AC15 (engine 가 market + data import)

### 7.11 Codex 적용

7/7 area 채택 (event-driven SMA / lookahead L2+L3 / ExecutionReport schema / equity_curve CSV / RiskGate placeholder / CLI / StrategyContext + Slippage). ADR conflict 0/7.

## 8-11

(Phase 2 = `mctrader-engine` repo 생성 + 첫 commit + AC1~AC15 통과 PR. MCT-13 + MCT-15 Phase 2 merge + MCT-14 fixture 후 시작. **Epic 의 가장 큰 Story** — Phase 2 implementation 자체가 큰 작업.)
