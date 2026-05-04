# mctrader-web Phase 2B — Engine artifact extension + candlestick chart

**Status**: Draft (2026-05-04). Phase 2A merge 후 시작.
**Author**: brainstormed via superpowers:brainstorming skill, Codex review + Sonnet decider 합성 closed
**Owner repos**: `mctrader-engine` (schema + artifact 확장) + `mctrader-web` (chart 렌더링)
**Companion spec**: `2026-05-04-mctrader-web-phase-2a-design.md` (web-only path)

## 1. Why this spec exists

Phase 2A 가 web-only path 를 닫음. 본 spec 은 **cross-repo schema + artifact 확장**:
- `mctrader-engine`: `OrderEvent` 에 `side / notional / fee` 필드, backtest finalize 시 `candles.csv` + `indicators.csv` 저장, opt-in `IndicatorProvider` Protocol, `ExecutionReport.candles_path / indicators_path` 추가
- `mctrader-web`: `candles.csv` + `indicators.csv` 읽어서 candlestick + indicator overlay + buy/sell scatter marker, events table 의 Side / Notional / Fee 컬럼이 schema 필드로 대체

Codex finding #11 의 spec split 에 따라 Phase 2A 와 별 spec — 본 spec 은 engine artifact contract change 를 main subject 로 다룸.

## 2. Scope

### In scope (Phase 2B)
- `mctrader-engine`:
  - `OrderEvent.side: Literal["BUY","SELL"] | None = None` 신규 (additive optional, **신규 backtest run 은 항상 채움**)
  - `OrderEvent.notional: Decimal38_18 | None = None` 신규 (additive)
  - `OrderEvent.fee: Decimal38_18 | None = None` 신규 (additive, 절대 KRW)
  - `ExecutionReport.candles_path: str | None = None` 신규
  - `ExecutionReport.indicators_path: str | None = None` 신규
  - `IndicatorProvider` opt-in Protocol (Strategy core 변경 없음)
  - `BacktestExecutor.finalize` 시 `candles.csv` + `indicators.csv` 저장
  - SMA strategy 에 `IndicatorProvider` implement
- `mctrader-web`:
  - `dashboard/loader.py`: `load_candles(path)`, `load_indicators(path)` 함수
  - `dashboard/chart.py`: `build_candlestick_chart(candles, indicators, events, tz)` 함수
  - `dashboard/pages/02_backtest_panel.py`: equity curve 와 candlestick chart 동시 표시
  - Events table 의 Side / Notional / Fee 컬럼: schema 필드 직접 표시 (legacy fallback 만 UI 계산)

### Out of scope
- KST 외 timezone (Phase 3)
- Paper panel candlestick (Phase 3)
- Strategy 다양화 (sma 외 — `IndicatorProvider` 가 자연 확장 enable, 실제 instance 추가는 별 spec)

## 3. Architecture

### 3.1 Repo boundary

| Repo | 변경 |
|---|---|
| `mctrader-engine` | `report/schema.py`, `executor/backtest.py`, `strategy/indicators.py` (NEW) |
| `mctrader-web` | `dashboard/loader.py`, `dashboard/chart.py`, `dashboard/pages/02_backtest_panel.py` |
| `mctrader-hub` | Story stub (engine + web cross-repo Epic 또는 2 Story chain) |

### 3.2 mctrader-engine 변경

#### 3.2.1 schema additions (`report/schema.py`)

```python
class OrderEvent(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    kind: Literal["OrderEvent"] = "OrderEvent"
    ts_utc: UTCDateTime
    order_id: OrderId
    status_from: OrderStatus
    status_to: OrderStatus
    fill_price: Decimal38_18 | None = None
    fill_quantity: Decimal38_18 | None = None
    fee_bps: Decimal38_18 | None = None
    slippage_bps: Decimal38_18 | None = None
    # NEW Phase 2B (additive optional)
    side: Literal["BUY", "SELL"] | None = None
    notional: Decimal38_18 | None = None  # fill_price * fill_quantity
    fee: Decimal38_18 | None = None  # absolute KRW (notional * fee_bps / 10000)
    # ... existing model_post_init


class ExecutionReport(BaseModel):
    # ... existing fields
    # NEW Phase 2B (additive optional)
    candles_path: str | None = None  # 항상 "candles.csv" (run-relative — Codex #12)
    indicators_path: str | None = None  # 항상 "indicators.csv" (run-relative)
```

**`schema_version` 유지**: `"execution_report.v1"` 그대로. 모든 변경이 additive optional 이라 v1 reader 가 새 필드 무시 가능. Codex #14 push-back 에 대한 응답:
- Schema level 은 `Optional` 유지 (legacy read 호환)
- **Engine writer enforcement**: `BacktestExecutor` 가 항상 `side / notional / fee / candles_path / indicators_path` 채움. test 로 검증.
- 신규 run 은 항상 모든 필드 present, legacy run 만 `None`.
- Web layer 는 `None` 일 때 fallback 표시 — 이게 contract.

#### 3.2.2 IndicatorProvider opt-in Protocol (`strategy/indicators.py` NEW)

```python
from typing import Protocol, Sequence
from decimal import Decimal
from mctrader_market.candle import CandleLike


class IndicatorProvider(Protocol):
    """Opt-in protocol — strategy 가 implement 안 하면 indicators.csv 는 header only."""

    def compute_indicators(
        self, candles: Sequence[CandleLike]
    ) -> dict[str, list[Decimal | None]]:
        """Return mapping of indicator name → candle-aligned series.

        - length == len(candles)
        - warmup period 는 leading `None` (예: SMA fast=5 의 처음 4개 = `None`)
        - CSV serialize 시 None → 빈 셀 (pandas `read_csv` 는 NaN 으로 read)
        - chart 는 leading None 영역에 indicator line 미표시 (Plotly 자연 처리)
        """
```

**Codex #9 응답**: `Strategy` core protocol 에는 추가 **하지 않음**. 별도 `IndicatorProvider` 가 opt-in. Strategy 가 implement 안 하면 indicators.csv = header-only empty file.

#### 3.2.3 SMA strategy implement

```python
class SmaStrategy(Strategy, IndicatorProvider):
    def compute_indicators(self, candles):
        closes = [c.close for c in candles]
        return {
            "sma_fast": _rolling_mean(closes, self.fast),
            "sma_slow": _rolling_mean(closes, self.slow),
        }
```

#### 3.2.4 Backtest finalize artifacts (`executor/backtest.py`)

```python
def _finalize(self) -> None:
    # existing: write equity_curve.csv, execution_report.json
    
    # NEW: candles.csv
    candles_path = self._output_dir / f"{self._run_id}/candles.csv"
    _write_candles_csv(candles_path, self._candles)
    
    # NEW: indicators.csv (only if strategy is IndicatorProvider)
    indicators_path = self._output_dir / f"{self._run_id}/indicators.csv"
    if isinstance(self._strategy, IndicatorProvider):
        indicators = self._strategy.compute_indicators(self._candles)
        _write_indicators_csv(indicators_path, self._candles, indicators)
    else:
        _write_empty_indicators_csv(indicators_path)  # header only, ts_utc column
    
    # report fields
    report.candles_path = "candles.csv"
    report.indicators_path = "indicators.csv"
```

**Format** (Codex #10 — parquet 거절, csv 일관성):

`candles.csv`:
```
ts_utc,open,high,low,close,volume
2026-04-27T07:00:00Z,145200000,145300000,145100000,145250000,12.5
...
```

`indicators.csv`:
```
ts_utc,sma_fast,sma_slow
2026-04-27T07:00:00Z,,
2026-04-27T07:01:00Z,,
2026-04-27T07:02:00Z,,
2026-04-27T07:03:00Z,,
2026-04-27T07:04:00Z,145200000,
...
2026-04-27T07:19:00Z,145200000,145100000
...
```
(빈 셀 = warmup period None — sma_fast 5개 / sma_slow 20개 leading)

- Decimal as string (precision 보존, equity_curve.csv 와 동일 패턴)
- ts_utc = ISO 8601 UTC tz-aware
- 각 indicator = column. 신규 indicator 자연 확장.

#### 3.2.5 OrderEvent.side / notional / fee 채우기

`executor/backtest.py` 의 `_submit_and_fill`:
```python
# existing fill_price, slippage_bps, fee_bps 계산 후
notional = fill_price * target_qty
fee_amount = notional * (fee_bps / Decimal("10000"))

self._events.append(
    OrderEvent(
        ts_utc=next_candle.ts_utc,
        order_id=order_id,
        status_from=OrderStatus.ACCEPTED,
        status_to=OrderStatus.FILLED,
        fill_price=fill_price,
        fill_quantity=target_qty,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        # NEW
        side=decision.kind.value,  # "BUY" or "SELL"
        notional=notional,
        fee=fee_amount,
    )
)
```

**Codex #15 응답**: UI 측 계산 fallback 만 남김. `BacktestExecutor` 가 항상 채움 → paper / live executor 도 동일 contract 수렴 (별 spec 추후).

### 3.3 mctrader-web 변경

#### 3.3.1 `dashboard/loader.py` 추가

```python
CANDLE_COLUMNS = ("ts_utc", "open", "high", "low", "close", "volume")

def load_candles(path: Path) -> pd.DataFrame:
    """Load candles.csv with dtype=str, parse ts_utc as UTC, return Decimal columns as strings."""

def load_indicators(path: Path) -> pd.DataFrame:
    """Load indicators.csv. ts_utc column required, 나머지는 dynamic indicator columns."""
```

#### 3.3.2 `dashboard/chart.py` 확장

```python
def build_candlestick_chart(
    candles: pd.DataFrame,
    indicators: pd.DataFrame,
    events: list[dict],  # OrderEvent FILLED only
    tz_name: str,
) -> plotly.graph_objects.Figure:
    """Plotly subplots:
      row=1: Candlestick (OHLCV) + indicator line traces + scatter markers
      x-axis: tz_name 포맷 (KST or UTC)

    Markers (Codex #17, #20):
      - BUY: scatter symbol="triangle-up" color="red", hover text=order_id+qty+price+fee
      - SELL: scatter symbol="triangle-down" color="blue"
      - 보조 vline: red/blue 30% alpha (옵션)
      - 같은 ts_utc 의 multiple fills → hover text aggregate (e.g. "2 fills @ same ts")
    """
```

#### 3.3.3 `dashboard/pages/02_backtest_panel.py` 변경

Completed runs 섹션:
```python
# existing equity chart 유지
st.plotly_chart(build_equity_chart(df), use_container_width=True)

# NEW Phase 2B: candlestick if available
if report.get("candles_path"):
    try:
        candles = load_candles(run.path / report["candles_path"])
        indicators = load_indicators(run.path / report["indicators_path"])
        events = [e for e in report["events"] if e.get("kind") == "OrderEvent" and e.get("status_to") == "FILLED"]
        st.subheader("Candlestick + Indicators")
        st.plotly_chart(
            build_candlestick_chart(candles, indicators, events, st.session_state["tz"]),
            use_container_width=True,
        )
    except Exception as exc:
        st.warning(f"Candlestick chart unavailable: {type(exc).__name__}: {exc}")
else:
    st.caption("OHLCV chart unavailable for legacy runs (no candles.csv).")
```

#### 3.3.4 Events table 변경 (Phase 2A 와 차이)

| 컬럼 | Phase 2A | Phase 2B |
|---|---|---|
| Side | `"—"` | `OrderEvent.side` 직접 (BUY=red text + ▲, SELL=blue text + ▼) |
| Notional | UI 계산 (`compute_notional`) | `OrderEvent.notional` 직접 (legacy run 만 fallback) |
| Fee | UI 계산 (`compute_fee`) | `OrderEvent.fee` 직접 (legacy run 만 fallback) |

**Side coloring + symbol** (Codex #20 colorblind 보조):
```python
def render_side_cell(side: str | None) -> str:
    if side == "BUY":
        return "<span style='color:red'>▲ BUY</span>"
    elif side == "SELL":
        return "<span style='color:blue'>▼ SELL</span>"
    else:
        return "—"
```

### 3.4 Backward compatibility

| Surface | Legacy 처리 |
|---|---|
| `ExecutionReport.candles_path` 없음 (legacy run) | candlestick chart skip + caption "OHLCV chart unavailable for legacy runs" |
| `ExecutionReport.indicators_path` 없음 | candlestick chart 는 OHLCV only (indicator overlay 없음) |
| `OrderEvent.side` 없음 | 표시 `"—"`, chart marker 미생성, chart caption "Buy/sell markers unavailable for legacy runs" |
| `OrderEvent.notional / fee` 없음 | UI fallback (`compute_notional`, `compute_fee`) |
| Strategy 가 `IndicatorProvider` implement 안 함 | indicators.csv = header only → chart 는 OHLCV + markers only |

**Cross-version test**: legacy run + 신규 run 디렉토리 mixed 환경에서 page 진입 시 어느 쪽도 crash 없이 fallback.

## 4. Testing strategy

### 4.1 mctrader-engine
- `tests/test_schema.py`:
  - `OrderEvent` round-trip with `side / notional / fee` populated
  - Legacy JSON (필드 없음) → parse 성공, fields = None
- `tests/test_backtest_finalize.py`:
  - finalize 후 `candles.csv` 존재 + 컬럼 + content
  - finalize 후 `indicators.csv` 존재 + SMA strategy 의 `sma_fast` / `sma_slow` columns
  - non-IndicatorProvider strategy → `indicators.csv` header only
  - `report.candles_path == "candles.csv"`, `report.indicators_path == "indicators.csv"`
- `tests/test_strategy_sma_indicators.py`:
  - `SmaStrategy.compute_indicators` shape (`{"sma_fast": [...], "sma_slow": [...]}`)
  - candle-aligned length

### 4.2 mctrader-web
- `tests/test_loader.py`:
  - `load_candles` happy path + missing column raise
  - `load_indicators` dynamic column handling
  - File 부재 → FileNotFoundError (caller 가 fallback)
- `tests/test_chart.py`:
  - `build_candlestick_chart` `fig.to_dict()` 검증:
    - row=1 candlestick trace count
    - indicator line trace 갯수 (SMA = 2)
    - BUY scatter trace `marker.symbol == "triangle-up"`, `marker.color == "red"`
    - SELL scatter `marker.symbol == "triangle-down"`, `marker.color == "blue"`
    - x-axis tickformat 가 selected TZ
    - 같은 ts_utc 의 multiple events → hover text aggregate
- `tests/test_apptest_phase2b.py`:
  - 신규 run + legacy run 두 fixture 디렉토리 → 둘 다 page 진입 가능
  - 신규: candlestick + indicator overlay 표시
  - legacy: equity only + caption 메시지 표시

## 5. Schema versioning note

**Codex #14 응답 (정리)**:
- `schema_version` = `"execution_report.v1"` 유지 (모든 변경 additive)
- `OrderEvent.side / notional / fee` 그리고 `ExecutionReport.candles_path / indicators_path` 모두 `Optional` 으로 schema 에 선언
- Engine writer (BacktestExecutor) = test 로 항상 채움 검증
- Web reader = `None` 시 graceful fallback (legacy run support)
- 향후 `schema_version` bump (v2) 시점에 required 로 승격 검토

## 6. References

- `mctrader-engine/src/mctrader_engine/report/schema.py` (OrderEvent / ExecutionReport baseline)
- `mctrader-engine/src/mctrader_engine/executor/backtest.py:208-271` (현재 _submit_and_fill — side / notional / fee 채울 위치)
- `mctrader-engine/src/mctrader_engine/strategy/` (Strategy core, sma 만 존재)
- `mctrader-web/src/mctrader_web/dashboard/chart.py` (build_equity_chart baseline)
- ADR-002 (TradeExecutor 3-mode)
- ADR-004 (slippage / fee / latency contract)
- MCT-48 Epic
- Phase 2A spec (`2026-05-04-mctrader-web-phase-2a-design.md`)
- Brainstorm decisions: Q4-C (engine artifact 확장) / Q5 (events table + side 필드 추가) / Codex finding #9, #10, #11, #14, #15

## 7. Open questions

(없음 — Codex review + Sonnet decider 합성 후 모두 closed)
