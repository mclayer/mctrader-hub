---
story_key: MCT-13
status: phase:요구사항
component: market
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-002, ADR-004, ADR-009, ADR-010, ADR-011
---

# MCT-13: mctrader-market interface (Candle/OrderBook/Order Protocol)

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-13: mctrader-market interface (Candle/OrderBook/Order Protocol)"

## 2. 도메인 해석

`mctrader-market` repo 의 첫 commit. ADR-009 의 "Candle Protocol = repo 경계 contract" 의 source of truth. Exchange-neutral data shape + Order lifecycle value contract 정의. **Execution semantics (place/cancel/get) 는 본 Story 미포함** — ADR-002 의 TradeExecutor (mctrader-engine 내부) 책임.

## 3. 관련 ADR

- ADR-002 (TradeExecutor + 8-state Order lifecycle) — Order lifecycle state 정의 위치
- ADR-004 (ExecutionReport schema 공유) — Order/Trade ID 의 stability + idempotency 요구
- ADR-009 (OHLCV v1 16-column / Candle Protocol contract) — Candle data shape source
- ADR-010 (Pydantic v2 외부 경계 / Decimal canonical) — boundary validation 의 policy
- ADR-011 (Branch protection + 5 required check) — 첫 commit standard

## 4. 관련 코드 경로

```
mctrader-market/
├── pyproject.toml
├── uv.lock
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/ci.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
├── src/mctrader_market/
│   ├── __init__.py
│   ├── types.py             # Symbol value object + Timeframe StrEnum + ID NewTypes
│   ├── candle.py            # CandleLike Protocol + CandleModel (Pydantic v2)
│   ├── orderbook.py         # OrderBookLike Protocol + OrderBookModel
│   ├── order.py             # OrderStatus / OrderSide / OrderType StrEnum + Order snapshot model
│   ├── lifecycle.py         # can_transition() pure function (8-state matrix)
│   ├── providers.py         # CandleProvider + OrderBookProvider Protocol
│   └── fixtures.py          # importable canonical fixtures (valid + invalid)
└── tests/
    ├── test_candle_model.py
    ├── test_order_lifecycle.py
    ├── test_symbol_timeframe.py
    └── test_fixtures.py
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ + Pydantic v2 + typing.Protocol (PEP 544) + typing.NewType
- Decimal canonical (ADR-010) — Annotated[Decimal, MaxDigits(38), DecimalPlaces(18)] = boundary
- ISO-8601 "Z" UTC serialization
- pyright strict + pytest (ADR-011)

## 7. 설계 서사 (요약)

### 7.1 Protocol method set 범위 (A1 결정)

본 Story 에 포함할 Protocol set:

| Protocol | 위치 | 책임 |
|---|---|---|
| `CandleLike` | `candle.py` | Candle data shape (read-only structural type) |
| `CandleModel` (Pydantic) | `candle.py` | boundary validation model |
| `OrderBookLike` | `orderbook.py` | OrderBook data shape |
| `OrderBookModel` (Pydantic) | `orderbook.py` | boundary validation model |
| `Order` (snapshot model) | `order.py` | immutable Order snapshot + 8-state |
| `CandleProvider` | `providers.py` | `get_candles(symbol, timeframe, start, end) → Iterable[CandleLike]` |
| `OrderBookProvider` | `providers.py` | `get_orderbook(symbol) → OrderBookLike` |

본 Story **미포함**:
- `OrderClient` / `BrokerClient` Protocol (place/cancel/get) — MCT-14 adapter 실험 + ADR-002 TradeExecutor (engine repo) 의 책임 경계
- TradeExecutor 자체 — mctrader-engine 내부 (ADR-002)

근거: read-side full + Order value contract 까지가 exchange-neutral repo 의 자연 경계. write-side execution semantics 는 adapter capability + engine execution 의 만남 지점이라 MCT-14/16 에서 결정.

### 7.2 Decimal type 정책 — dataclass + Pydantic v2 이중 layer (A2 결정)

**Protocol layer** (lightweight, structural):
```python
from typing import Protocol, runtime_checkable
from decimal import Decimal
from datetime import datetime

@runtime_checkable
class CandleLike(Protocol):
    ts_utc: datetime          # tzinfo == timezone.utc
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    value: Decimal | None     # ADR-009 Bithumb 부재 시 quarantine
    # ... ADR-009 v1 16-column logical view
```

**Boundary model** (Pydantic v2 strict):
```python
from typing import Annotated
from pydantic import BaseModel, Field

Decimal38_18 = Annotated[
    Decimal,
    Field(max_digits=38, decimal_places=18),
]

class CandleModel(BaseModel):
    model_config = {"strict": True}
    ts_utc: UTCDateTime  # see 7.3
    open: Decimal38_18
    high: Decimal38_18
    low: Decimal38_18
    close: Decimal38_18
    volume: Decimal38_18
    value: Decimal38_18 | None
    # ...
```

**원칙**:
- 외부 boundary (adapter output / API I/O / config / fixture) = `CandleModel` validation 의무
- 내부 hot path (engine SMA 계산) = dataclass / TypedDict / NumPy 허용 (ADR-010 7.10)
- `TypeAdapter(CandleModel).validate_python(raw_dict)` = downstream repo 가 import 해서 사용

### 7.3 Timezone 정책 (A3 결정)

**Protocol shape** = `datetime` (timezone-aware).

**Boundary model** = Pydantic v2 validator (`UTCDateTime` Annotated):

```python
from pydantic import AfterValidator

def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("naive datetime not allowed (ADR-009 boundary)")
    if value.utcoffset() != timedelta(0):
        # 비-UTC offset 의 datetime = adapter normalization 책임 (MCT-14)
        # boundary 에서는 reject (또는 normalize 정책 — 본 Story = strict reject)
        raise ValueError(f"non-UTC datetime: {value.tzinfo} (ADR-009 boundary)")
    return value.replace(tzinfo=timezone.utc)  # canonicalize tzinfo

UTCDateTime = Annotated[datetime, AfterValidator(_ensure_utc)]
```

**Serialization**:
- JSON / API = ISO-8601 with `"Z"` suffix (예: `"2026-05-02T03:00:00Z"`)
- Parquet / DuckDB = TIMESTAMP WITH TIME ZONE (UTC)
- Pydantic = `datetime` 그대로 (tzinfo 보장)

**KST 1d boundary 처리** (ADR-009 D4): aggregation / partition 단계 에서만 적용. Candle Protocol 의 `ts_utc` 는 항상 UTC.

### 7.4 ID type 정책 (A4 결정)

```python
from typing import NewType

OrderId = NewType("OrderId", str)
TradeId = NewType("TradeId", str)
RunId = NewType("RunId", str)
```

**Boundary validation** (Pydantic v2 minimal):
- non-empty
- length ≤ 256
- allowed character class = `[A-Za-z0-9._:-]`
- UUID4-only validator 비채택 (exchange-native ID 와 충돌 위험)

**Backtest deterministic ID** (engine 책임, MCT-16):
```
order_id = f"bt:{run_id}:{seq}"
trade_id = f"bt:{run_id}:{order_id}:fill:{fill_seq}"
```

`run_id` 는 strategy run 단위 고정. `seq` = monotonic order creation order. → deterministic replay anchor.

### 7.5 Symbol 정책 (A5 결정 — value object)

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Symbol:
    base: str   # e.g., "BTC"
    quote: str  # e.g., "KRW"

    @classmethod
    def from_string(cls, s: str) -> "Symbol":
        # boundary canonical = "{quote}-{base}" (KRW base 기준)
        q, _, b = s.partition("-")
        if not q or not b:
            raise ValueError(f"invalid symbol: {s}")
        return cls(base=b.upper(), quote=q.upper())

    def __str__(self) -> str:
        return f"{self.quote}-{self.base}"
```

**근거**:
- Symbol enum 으로 listing freeze = 신규 listing 마다 breaking change → 비채택
- plain `str` = type 안전성 약함 → 비채택
- value object (frozen dataclass) = exchange-neutral semantics + canonical string + immutable hashable
- Pydantic boundary validator = uppercase, separator, non-empty 검증

**Boundary canonical string**: `"{quote}-{base}"` (Upbit 스타일 — KRW-BTC). Bithumb adapter (MCT-14) 는 `"BTC_KRW"` → `Symbol(base="BTC", quote="KRW")` normalization 책임.

### 7.6 Timeframe 정책 (A5 결정 — closed StrEnum)

```python
from enum import StrEnum

class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
```

**근거**:
- ADR-009 partition path = `timeframe=1h` 형태 → canonical string form 안정 필요
- closed StrEnum = type 안전성 + canonical string + serialization 일관
- 신규 timeframe 추가 = minor version addition (SemVer 0.x strict)
- timedelta 기반 비채택 — `1mo`, `1w`, KST-aware `1d` calendar-aware unit 부적합

### 7.7 8-state Order lifecycle (A6 결정)

```python
from enum import StrEnum

class OrderStatus(StrEnum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
```

**Order = immutable snapshot** (Pydantic v2 frozen):
```python
class Order(BaseModel):
    model_config = {"strict": True, "frozen": True}
    order_id: OrderId
    symbol: Symbol
    side: OrderSide
    type: OrderType
    status: OrderStatus
    price: Decimal38_18 | None  # MARKET = None
    quantity: Decimal38_18
    filled_quantity: Decimal38_18
    created_at: UTCDateTime
    updated_at: UTCDateTime
    # ... ADR-002 의 추가 field
```

**상태 변경 = 새 Order snapshot 반환 (immutable)** — `MutableOrder.set_status` 패턴 비채택 (deterministic replay 친화).

**Transition matrix** (`lifecycle.py`):
```python
def can_transition(from_: OrderStatus, to: OrderStatus) -> bool:
    """ADR-002 8-state lifecycle valid transition matrix (pure function)."""
    matrix = {
        OrderStatus.NEW: {OrderStatus.ACCEPTED, OrderStatus.REJECTED},
        OrderStatus.ACCEPTED: {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCEL_REQUESTED, OrderStatus.EXPIRED},
        OrderStatus.PARTIALLY_FILLED: {OrderStatus.FILLED, OrderStatus.CANCEL_REQUESTED, OrderStatus.EXPIRED},
        OrderStatus.CANCEL_REQUESTED: {OrderStatus.CANCELED, OrderStatus.FILLED},  # race: cancel 요청 직후 fill 가능
        OrderStatus.FILLED: set(),       # terminal
        OrderStatus.CANCELED: set(),     # terminal
        OrderStatus.REJECTED: set(),     # terminal
        OrderStatus.EXPIRED: set(),      # terminal
    }
    return to in matrix.get(from_, set())
```

**ExecutionReport 와의 align**: ADR-004 의 ExecutionReport 가 OrderEvent stream (시간순 append) 으로 8-state 변화 기록. 본 Story 는 OrderStatus + Order snapshot + transition matrix 만 정의. ExecutionReport schema 자체 = MCT-16 (engine).

### 7.8 Provider Protocol (A1 결정 — read-side)

```python
from typing import Iterable
from datetime import datetime

class CandleProvider(Protocol):
    def get_candles(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: datetime,  # UTC
        end: datetime,    # UTC, exclusive
    ) -> Iterable[CandleLike]: ...

class OrderBookProvider(Protocol):
    def get_orderbook(self, symbol: Symbol) -> OrderBookLike: ...
```

`runtime_checkable` 적용 (mypy/pyright = static check, isinstance() = runtime smoke). 단 method 만 check, 시그니처 차이는 pyright strict 가 잡음.

**End semantics** = exclusive (`[start, end)`) — half-open interval. ADR-009 의 candle bar 정의 (close_time = bar_end_ts == next_bar_open_ts) 와 일관.

### 7.9 Importable contract fixtures (A7 결정)

`fixtures.py` 가 downstream test 의 input source:

```python
# valid fixtures
def make_valid_candle(...) -> CandleModel: ...
def make_valid_orderbook(...) -> OrderBookModel: ...
def make_valid_order(...) -> Order: ...

# invalid fixtures (boundary rejection 검증)
def make_invalid_naive_datetime_candle() -> dict: ...  # tzinfo=None
def make_invalid_decimal_scale_candle() -> dict: ...   # 19 decimal places
def make_invalid_symbol_string() -> str: ...           # "btckrw"
def make_invalid_transition_pair() -> tuple: ...       # (NEW, FILLED)
```

**원칙**:
- exchange-neutral fixture only (Bithumb-specific = MCT-14 의 raw fixture 책임)
- canonical example = pyright + pytest 의 contract test input
- `TypeAdapter(CandleModel).validate_python(invalid)` 가 reject 검증 의무

### 7.10 검증 전략 (A7 결정)

| Layer | 도구 | 검증 |
|---|---|---|
| Static type | pyright strict (ADR-011 required) | Protocol satisfaction (CandleProvider impl 의 method shape) |
| Runtime structural | `isinstance(adapter, CandleProvider)` | smoke (method 존재) |
| Boundary data | `TypeAdapter(CandleModel).validate_python(raw)` | Decimal scale + UTC + non-empty |
| Transition | `can_transition(from, to)` | 8-state matrix |
| Schema export | `CandleModel.model_json_schema()` | downstream contract test (mctrader-web 등 API boundary) |

**ABC 강제 비채택** — PEP 544 Protocol 정신 + Pydantic boundary validation 으로 충분.

### 7.11 Pyproject + 첫 commit standard

```toml
# pyproject.toml
[project]
name = "mctrader-market"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
  "pydantic>=2,<3",
  "typing-extensions>=4.12",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "pyright>=1.1",
  "ruff>=0.6",
]
```

**.pre-commit-config.yaml** (ADR-011 D6):
- ruff check --fix + ruff format
- pyright (lightweight)
- gitleaks
- trailing-whitespace / end-of-file-fixer / check-yaml / check-toml
- uv lock --check

**CI** (`.github/workflows/ci.yml`, ADR-011 D2 + D3):
- pull_request + push (main) trigger
- 5 required check (phase-gate / lint / type / test / coverage 60%)
- compat lane Python 3.12 (non-blocking)

**Branch protection** (ADR-011 D1 + F5):
- required approvals = 0
- CODEOWNERS review = false
- enforce_admins = false
- 5 required status checks
- linear history + no force push + no deletion

### 7.12 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| OrderClient / BrokerClient Protocol | ✗ | MCT-14 (adapter 실험) + ADR-002 TradeExecutor (engine) 책임 경계 |
| TradeExecutor 자체 | ✗ | ADR-002 — mctrader-engine 내부 |
| ExecutionReport schema | ✗ | ADR-004 — MCT-16 (engine) |
| Bithumb-specific normalization | ✗ | MCT-14 (adapter) 책임 |
| Storage I/O | ✗ | MCT-15 (data) 책임 |
| WebSocket / streaming Protocol | ✗ | MCT-12 = REST polling only / future Epic |
| 다중 거래소 union enum | ✗ | Symbol = value object, listing freeze X |

### 7.13 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | `pyproject.toml` `version = "0.1.0"` + Python 3.11+ + Pydantic v2 | uv sync --frozen |
| AC2 | 5 required check green (phase-gate / lint / type / test / coverage 60%) | CI |
| AC3 | `Candle` Protocol + `CandleModel` boundary 가 `make_valid_candle()` validate 통과 + `make_invalid_*()` reject | pytest |
| AC4 | `Order` snapshot + `can_transition()` 가 8-state matrix 의 valid + invalid 모두 통과 | pytest (matrix exhaustive) |
| AC5 | `Symbol.from_string("KRW-BTC")` + `str(Symbol(base="BTC", quote="KRW")) == "KRW-BTC"` roundtrip | pytest |
| AC6 | `Timeframe("1h") == Timeframe.H1` 일관 | pytest |
| AC7 | `runtime_checkable` Protocol 의 isinstance smoke 통과 | pytest |
| AC8 | downstream fixture import: `from mctrader_market.fixtures import make_valid_candle` | pytest (separate test repo) |
| AC9 | `CandleModel.model_json_schema()` 가 valid JSON Schema export | pytest |

### 7.14 Codex 적용

7/7 area 채택 (Protocol method set / Decimal type / Timezone / ID type / Symbol/Timeframe / 8-state lifecycle / 검증 전략). ADR conflict 0/7.

## 8-11

(Phase 2 = `mctrader-market` repo 생성 + 첫 commit + AC1~AC9 통과 PR.)
