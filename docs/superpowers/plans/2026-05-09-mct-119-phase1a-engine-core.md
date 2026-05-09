# Strategy Set Pipeline — Phase 1-A: Engine Core Protocols

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-engine에 Strategy Set Pipeline의 핵심 데이터 모델, Protocol, 레지스트리, 헬퍼를 구현한다.

**Architecture:** 기존 `strategy/` 모듈과 별개로 `pipeline/` 패키지를 신설. `types.py`에 모든 frozen dataclass DTO, `protocols.py`에 모든 Protocol 정의, `registry.py`에 `@register_signal_producer` 데코레이터, `helpers.py`에 전략 작성자용 헬퍼 함수를 둔다.

**Tech Stack:** Python 3.12, dataclasses (frozen), typing.Protocol, Decimal, pytest

**Repo:** `c:\workspace\mclayer\mctrader-engine`

---

## 파일 구조

```
src/mctrader_engine/pipeline/
    __init__.py          공개 인터페이스 re-export
    types.py             모든 DTO (MarketSlice, Signal, AggregatedSignal, PortfolioPlan, ...)
    protocols.py         모든 Protocol (SignalProducer, SignalAggregator, ...)
    registry.py          @register_signal_producer 데코레이터 + 레지스트리
    helpers.py           emit_long / emit_short / emit_flat / emit_no_view

tests/unit/pipeline/
    __init__.py
    test_types.py
    test_registry.py
    test_helpers.py
```

---

### Task 1: pipeline 패키지 뼈대

**Files:**
- Create: `src/mctrader_engine/pipeline/__init__.py`
- Create: `tests/unit/pipeline/__init__.py`

- [ ] **Step 1: 디렉토리 및 빈 파일 생성**

```bash
cd c:\workspace\mclayer\mctrader-engine
mkdir -p src/mctrader_engine/pipeline tests/unit/pipeline
touch src/mctrader_engine/pipeline/__init__.py
touch tests/unit/pipeline/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add src/mctrader_engine/pipeline/__init__.py tests/unit/pipeline/__init__.py
git commit -m "chore(pipeline): pipeline 패키지 뼈대 생성"
```

---

### Task 2: types.py — 핵심 DTO

**Files:**
- Create: `src/mctrader_engine/pipeline/types.py`
- Create: `tests/unit/pipeline/test_types.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_types.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mctrader_engine.pipeline.types import (
    AggregatedSignal,
    DataFreshness,
    MarketSlice,
    OrderIntent,
    PortfolioPlan,
    PortfolioTarget,
    RebalancePlan,
    RiskDecision,
    Signal,
    SignalAction,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_signal_action_enum_values():
    assert SignalAction.ENTER == "enter"
    assert SignalAction.EXIT == "exit"
    assert SignalAction.NO_VIEW == "no_view"


def test_signal_is_frozen():
    sig = Signal(
        producer_name="test",
        symbol="BTCUSDT",
        action=SignalAction.ENTER,
        side="buy",
        strength=Decimal("0.8"),
        confidence=Decimal("0.9"),
        horizon="1h",
        valid_until=_now(),
        reason="test",
        data_quality_score=Decimal("1.0"),
        execution_hint=None,
        metadata=None,
    )
    with pytest.raises((AttributeError, TypeError)):
        sig.strength = Decimal("0.5")  # type: ignore[misc]


def test_market_slice_freshness():
    freshness = DataFreshness(lag_ms=50, sequence_gap=False, is_stale=False)
    slc = MarketSlice(
        as_of=_now(),
        symbol="BTCUSDT",
        symbols=frozenset({"BTCUSDT"}),
        bars={},
        ticks=None,
        orderbooks=None,
        freshness={"BTCUSDT": freshness},
        watermark=_now(),
    )
    assert not slc.freshness["BTCUSDT"].is_stale


def test_risk_decision_blocked():
    decision = RiskDecision(
        allowed=False,
        intents=(),
        blocked_reasons=("max_drawdown_exceeded",),
        adjusted_reasons=(),
    )
    assert not decision.allowed
    assert "max_drawdown_exceeded" in decision.blocked_reasons


def test_order_intent_frozen():
    intent = OrderIntent(
        symbol="BTCUSDT",
        side="buy",
        order_type="market",
        quantity=Decimal("0.01"),
        limit_price=None,
        valid_until=_now(),
        generated_at=_now(),
        reason="test",
    )
    with pytest.raises((AttributeError, TypeError)):
        intent.quantity = Decimal("0.02")  # type: ignore[misc]
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/unit/pipeline/test_types.py -v 2>&1 | head -30
```

Expected: `ImportError` — `mctrader_engine.pipeline.types` 없음

- [ ] **Step 3: types.py 구현**

`src/mctrader_engine/pipeline/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Mapping
from uuid import UUID


class SignalAction(str, Enum):
    ENTER = "enter"
    INCREASE = "increase"
    DECREASE = "decrease"
    EXIT = "exit"
    HOLD = "hold"
    NO_VIEW = "no_view"


@dataclass(frozen=True)
class ExecutionHint:
    urgency: Literal["low", "normal", "high"]
    preferred_order_type: Literal["market", "limit"]
    max_slippage_bps: int
    post_only_preferred: bool
    ttl_ms: int


@dataclass(frozen=True)
class DataFreshness:
    lag_ms: int
    sequence_gap: bool
    is_stale: bool


@dataclass(frozen=True)
class MarketSlice:
    as_of: datetime
    symbol: str
    symbols: frozenset[str]
    bars: Mapping[str, Any]           # symbol → BarWindow (CandleLike 시퀀스)
    ticks: Mapping[str, Any] | None
    orderbooks: Mapping[str, Any] | None
    freshness: Mapping[str, DataFreshness]
    watermark: datetime


@dataclass(frozen=True)
class AccountSnapshot:
    ts: datetime
    equity: Decimal
    cash: Decimal
    positions: Mapping[str, "PositionSnapshot"]
    peak_equity: Decimal | None = None


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal | None
    market_price: Decimal
    unrealized_pnl: Decimal
    notional: Decimal


@dataclass(frozen=True)
class OpenOrder:
    order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    filled_qty: Decimal
    limit_price: Decimal | None
    created_at: datetime


@dataclass(frozen=True)
class Fill:
    fill_id: str
    order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    price: Decimal
    fee: Decimal
    ts: datetime


@dataclass(frozen=True)
class Signal:
    producer_name: str
    symbol: str
    action: SignalAction
    side: Literal["buy", "sell", "flat"]
    strength: Decimal          # 0..1 확신의 크기 (포지션 크기 아님)
    confidence: Decimal        # 0..1
    horizon: str               # "1m" | "5m" | "1h" | "1d"
    valid_until: datetime
    reason: str | None
    data_quality_score: Decimal
    execution_hint: ExecutionHint | None
    metadata: Mapping[str, Any] | None


@dataclass(frozen=True)
class AggregatedSignal:
    symbol: str
    side: Literal["buy", "sell", "flat"]
    score: Decimal
    threshold: Decimal
    horizon_bucket: str
    conflict_level: Decimal    # 0..1
    contributors: tuple[Signal, ...]


@dataclass(frozen=True)
class PortfolioTarget:
    symbol: str
    target_weight: Decimal     # NAV 대비 목표 비중
    target_notional: Decimal | None


@dataclass(frozen=True)
class PortfolioPlan:
    ts: datetime
    targets: tuple[PortfolioTarget, ...]


@dataclass(frozen=True)
class RebalancePlan:
    symbol: str
    current_qty: Decimal
    target_qty: Decimal
    delta_qty: Decimal
    urgency: Literal["immediate", "normal", "passive"]
    reason: str | None


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: Decimal
    limit_price: Decimal | None
    valid_until: datetime
    generated_at: datetime
    reason: str | None


@dataclass(frozen=True)
class ExecutionPlan:
    intent: OrderIntent
    order_type: Literal["market", "limit"]
    limit_price: Decimal | None
    time_in_force: Literal["GTC", "IOC", "FOK"]
    post_only: bool
    reduce_only: bool
    ttl_ms: int


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    intents: tuple[OrderIntent, ...]
    blocked_reasons: tuple[str, ...]
    adjusted_reasons: tuple[str, ...]


@dataclass
class PipelineFrame:
    run_id: UUID
    strategy_set_version_id: UUID
    frame_id: UUID
    as_of: datetime
    market_slice: MarketSlice
    account_snapshot: AccountSnapshot
    open_orders: tuple[OpenOrder, ...]
    recent_fills: tuple[Fill, ...]
    signals: list[Signal] = field(default_factory=list)
    aggregated: list[AggregatedSignal] = field(default_factory=list)
    portfolio_plan: PortfolioPlan | None = None
    rebalance_plans: list[RebalancePlan] = field(default_factory=list)
    risk_decision: RiskDecision | None = None
    execution_plans: list[ExecutionPlan] = field(default_factory=list)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_types.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_engine/pipeline/types.py tests/unit/pipeline/test_types.py
git commit -m "feat(pipeline): 핵심 DTO 타입 정의 (Signal, MarketSlice, PipelineFrame 등)"
```

---

### Task 3: protocols.py — 레이어 Protocol 정의

**Files:**
- Create: `src/mctrader_engine/pipeline/protocols.py`

- [ ] **Step 1: protocols.py 구현**

`src/mctrader_engine/pipeline/protocols.py`:

```python
from __future__ import annotations

from enum import Enum
from typing import ClassVar, Protocol, Sequence, runtime_checkable

from mctrader_engine.pipeline.types import (
    AggregatedSignal,
    ExecutionPlan,
    PipelineFrame,
    PortfolioPlan,
    RebalancePlan,
    RiskDecision,
    Signal,
)


class DataTier(str, Enum):
    CANDLE = "candle"
    TICK = "tick"
    ORDERBOOK = "orderbook"


class TriggerPolicy(str, Enum):
    CANDLE_CLOSE = "candle_close"
    TICK_BATCH = "tick_batch"
    ORDERBOOK_CHANGE = "orderbook_change"
    TIMER = "timer"


class CoveragePolicy(str, Enum):
    SPARSE = "sparse"                        # 신호 있을 때만 반환
    FULL_UNIVERSE = "full_universe"          # 모든 심볼에 NO_VIEW 포함
    HELD_POSITIONS_ONLY = "held_positions_only"  # 보유 포지션만


@runtime_checkable
class SignalProducer(Protocol):
    name: ClassVar[str]
    required_data_tiers: ClassVar[frozenset[DataTier]]
    trigger_policy: ClassVar[TriggerPolicy]
    coverage_policy: ClassVar[CoveragePolicy]

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]: ...


@runtime_checkable
class SignalAggregator(Protocol):
    name: ClassVar[str]
    def aggregate(self, frame: PipelineFrame) -> Sequence[AggregatedSignal]: ...


@runtime_checkable
class PortfolioConstructor(Protocol):
    name: ClassVar[str]
    def construct(self, frame: PipelineFrame) -> PortfolioPlan: ...


@runtime_checkable
class PositionManagerProtocol(Protocol):
    name: ClassVar[str]
    def plan_rebalance(self, frame: PipelineFrame) -> Sequence[RebalancePlan]: ...


@runtime_checkable
class RiskConstraintProtocol(Protocol):
    name: ClassVar[str]
    def apply(self, frame: PipelineFrame) -> RiskDecision: ...


@runtime_checkable
class ExecutionPlannerProtocol(Protocol):
    name: ClassVar[str]
    def plan(self, frame: PipelineFrame) -> Sequence[ExecutionPlan]: ...
```

- [ ] **Step 2: 프로토콜 import 테스트**

`tests/unit/pipeline/test_types.py`에 추가:

```python
def test_protocols_importable():
    from mctrader_engine.pipeline.protocols import (
        CoveragePolicy,
        DataTier,
        ExecutionPlannerProtocol,
        PortfolioConstructor,
        PositionManagerProtocol,
        RiskConstraintProtocol,
        SignalAggregator,
        SignalProducer,
        TriggerPolicy,
    )
    assert DataTier.CANDLE == "candle"
    assert TriggerPolicy.CANDLE_CLOSE == "candle_close"
```

- [ ] **Step 3: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_types.py -v
```

Expected: `6 passed`

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_engine/pipeline/protocols.py tests/unit/pipeline/test_types.py
git commit -m "feat(pipeline): SignalProducer/Aggregator/Constructor/Risk/ExecutionPlanner Protocol 정의"
```

---

### Task 4: registry.py — @register_signal_producer

**Files:**
- Create: `src/mctrader_engine/pipeline/registry.py`
- Create: `tests/unit/pipeline/test_registry.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_registry.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Sequence

import pytest

from mctrader_engine.pipeline.protocols import (
    CoveragePolicy,
    DataTier,
    TriggerPolicy,
)
from mctrader_engine.pipeline.registry import (
    ProducerInfo,
    _clear_registry_for_tests,
    get_producer,
    list_producers,
    register_signal_producer,
)
from mctrader_engine.pipeline.types import PipelineFrame, Signal


@pytest.fixture(autouse=True)
def clear_registry():
    _clear_registry_for_tests()
    yield
    _clear_registry_for_tests()


def _make_producer_class(name: str):
    @register_signal_producer(name)
    class _Producer:
        name: ClassVar[str] = name
        required_data_tiers: ClassVar[frozenset[DataTier]] = frozenset({DataTier.CANDLE})
        trigger_policy: ClassVar[TriggerPolicy] = TriggerPolicy.CANDLE_CLOSE
        coverage_policy: ClassVar[CoveragePolicy] = CoveragePolicy.SPARSE

        def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]:
            return []

    return _Producer


def test_register_and_get():
    cls = _make_producer_class("test_producer")
    retrieved = get_producer("test_producer")
    assert retrieved is cls


def test_duplicate_registration_raises():
    _make_producer_class("dup_producer")
    with pytest.raises(ValueError, match="already registered"):
        _make_producer_class("dup_producer")


def test_list_producers():
    _make_producer_class("prod_a")
    _make_producer_class("prod_b")
    names = [p.name for p in list_producers()]
    assert "prod_a" in names
    assert "prod_b" in names


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get_producer("nonexistent")


def test_missing_required_data_tiers_raises():
    with pytest.raises(TypeError, match="required_data_tiers"):

        @register_signal_producer("bad_producer")
        class _Bad:
            name = "bad_producer"
            # required_data_tiers 없음
            trigger_policy = TriggerPolicy.CANDLE_CLOSE
            coverage_policy = CoveragePolicy.SPARSE

            def generate_signals(self, frame):
                return []
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
uv run pytest tests/unit/pipeline/test_registry.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 3: registry.py 구현**

`src/mctrader_engine/pipeline/registry.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PRODUCER_REGISTRY: dict[str, type] = {}


@dataclass(frozen=True)
class ProducerInfo:
    name: str
    required_data_tiers: frozenset
    trigger_policy: str
    coverage_policy: str
    docstring: str | None


def register_signal_producer(name: str):
    def decorator(cls: type) -> type:
        if not hasattr(cls, "required_data_tiers") or not cls.required_data_tiers:
            raise TypeError(
                f"{cls.__name__}: required_data_tiers ClassVar must be a non-empty frozenset"
            )
        if name in PRODUCER_REGISTRY:
            raise ValueError(f"SignalProducer '{name}' already registered")
        cls.name = name
        PRODUCER_REGISTRY[name] = cls
        return cls

    return decorator


def get_producer(name: str) -> type:
    if name not in PRODUCER_REGISTRY:
        raise KeyError(f"SignalProducer '{name}' not found in registry")
    return PRODUCER_REGISTRY[name]


def list_producers() -> list[ProducerInfo]:
    result = []
    for name, cls in PRODUCER_REGISTRY.items():
        result.append(
            ProducerInfo(
                name=name,
                required_data_tiers=frozenset(cls.required_data_tiers),
                trigger_policy=str(cls.trigger_policy),
                coverage_policy=str(cls.coverage_policy),
                docstring=cls.__doc__,
            )
        )
    return result


def _clear_registry_for_tests() -> None:
    PRODUCER_REGISTRY.clear()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_registry.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_engine/pipeline/registry.py tests/unit/pipeline/test_registry.py
git commit -m "feat(pipeline): @register_signal_producer 데코레이터 + 레지스트리"
```

---

### Task 5: helpers.py — 전략 작성자용 헬퍼

**Files:**
- Create: `src/mctrader_engine/pipeline/helpers.py`
- Create: `tests/unit/pipeline/test_helpers.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_helpers.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.helpers import (
    emit_flat,
    emit_long,
    emit_no_view,
    emit_short,
)
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    MarketSlice,
    PipelineFrame,
    SignalAction,
)


def _make_frame(symbol: str = "BTCUSDT") -> PipelineFrame:
    now = datetime.now(timezone.utc)
    return PipelineFrame(
        run_id=uuid4(),
        strategy_set_version_id=uuid4(),
        frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(
            as_of=now,
            symbol=symbol,
            symbols=frozenset({symbol}),
            bars={},
            ticks=None,
            orderbooks=None,
            freshness={},
            watermark=now,
        ),
        account_snapshot=AccountSnapshot(
            ts=now,
            equity=Decimal("10000"),
            cash=Decimal("10000"),
            positions={},
        ),
        open_orders=(),
        recent_fills=(),
    )


def test_emit_long_returns_buy_signal():
    frame = _make_frame()
    sig = emit_long(frame, producer_name="test", strength=Decimal("0.8"))
    assert sig.action == SignalAction.ENTER
    assert sig.side == "buy"
    assert sig.strength == Decimal("0.8")
    assert sig.valid_until > frame.as_of


def test_emit_short_returns_sell_signal():
    frame = _make_frame()
    sig = emit_short(frame, producer_name="test")
    assert sig.side == "sell"
    assert sig.action == SignalAction.ENTER


def test_emit_flat_returns_exit():
    frame = _make_frame()
    sig = emit_flat(frame, producer_name="test", reason="trend_reversed")
    assert sig.action == SignalAction.EXIT
    assert sig.side == "flat"
    assert sig.reason == "trend_reversed"


def test_emit_no_view():
    frame = _make_frame()
    sig = emit_no_view(frame, producer_name="test")
    assert sig.action == SignalAction.NO_VIEW
    assert sig.strength == Decimal("0")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
uv run pytest tests/unit/pipeline/test_helpers.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 3: helpers.py 구현**

`src/mctrader_engine/pipeline/helpers.py`:

```python
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from mctrader_engine.pipeline.types import (
    PipelineFrame,
    Signal,
    SignalAction,
)

_DEFAULT_HORIZON = "1h"
_DEFAULT_TTL_SECONDS = 3600


def emit_long(
    frame: PipelineFrame,
    *,
    producer_name: str,
    strength: Decimal = Decimal("1.0"),
    confidence: Decimal = Decimal("0.8"),
    horizon: str = _DEFAULT_HORIZON,
    reason: str | None = None,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> Signal:
    return Signal(
        producer_name=producer_name,
        symbol=frame.market_slice.symbol,
        action=SignalAction.ENTER,
        side="buy",
        strength=strength,
        confidence=confidence,
        horizon=horizon,
        valid_until=frame.as_of + timedelta(seconds=ttl_seconds),
        reason=reason,
        data_quality_score=_quality_score(frame),
        execution_hint=None,
        metadata=None,
    )


def emit_short(
    frame: PipelineFrame,
    *,
    producer_name: str,
    strength: Decimal = Decimal("1.0"),
    confidence: Decimal = Decimal("0.8"),
    horizon: str = _DEFAULT_HORIZON,
    reason: str | None = None,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> Signal:
    return Signal(
        producer_name=producer_name,
        symbol=frame.market_slice.symbol,
        action=SignalAction.ENTER,
        side="sell",
        strength=strength,
        confidence=confidence,
        horizon=horizon,
        valid_until=frame.as_of + timedelta(seconds=ttl_seconds),
        reason=reason,
        data_quality_score=_quality_score(frame),
        execution_hint=None,
        metadata=None,
    )


def emit_flat(
    frame: PipelineFrame,
    *,
    producer_name: str,
    reason: str | None = None,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> Signal:
    return Signal(
        producer_name=producer_name,
        symbol=frame.market_slice.symbol,
        action=SignalAction.EXIT,
        side="flat",
        strength=Decimal("1.0"),
        confidence=Decimal("1.0"),
        horizon="immediate",
        valid_until=frame.as_of + timedelta(seconds=ttl_seconds),
        reason=reason,
        data_quality_score=_quality_score(frame),
        execution_hint=None,
        metadata=None,
    )


def emit_no_view(
    frame: PipelineFrame,
    *,
    producer_name: str,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> Signal:
    return Signal(
        producer_name=producer_name,
        symbol=frame.market_slice.symbol,
        action=SignalAction.NO_VIEW,
        side="flat",
        strength=Decimal("0"),
        confidence=Decimal("0"),
        horizon="n/a",
        valid_until=frame.as_of + timedelta(seconds=ttl_seconds),
        reason=None,
        data_quality_score=_quality_score(frame),
        execution_hint=None,
        metadata=None,
    )


def _quality_score(frame: PipelineFrame) -> Decimal:
    symbol = frame.market_slice.symbol
    freshness = frame.market_slice.freshness.get(symbol)
    if freshness is None:
        return Decimal("1.0")
    if freshness.is_stale or freshness.sequence_gap:
        return Decimal("0.5")
    if freshness.lag_ms > 5000:
        return Decimal("0.7")
    return Decimal("1.0")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_helpers.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_engine/pipeline/helpers.py tests/unit/pipeline/test_helpers.py
git commit -m "feat(pipeline): emit_long/short/flat/no_view 헬퍼 구현"
```

---

### Task 6: __init__.py 공개 인터페이스 확정

**Files:**
- Modify: `src/mctrader_engine/pipeline/__init__.py`

- [ ] **Step 1: 공개 인터페이스 정의**

`src/mctrader_engine/pipeline/__init__.py`:

```python
from mctrader_engine.pipeline.helpers import (
    emit_flat,
    emit_long,
    emit_no_view,
    emit_short,
)
from mctrader_engine.pipeline.protocols import (
    CoveragePolicy,
    DataTier,
    ExecutionPlannerProtocol,
    PortfolioConstructor,
    PositionManagerProtocol,
    RiskConstraintProtocol,
    SignalAggregator,
    SignalProducer,
    TriggerPolicy,
)
from mctrader_engine.pipeline.registry import (
    ProducerInfo,
    get_producer,
    list_producers,
    register_signal_producer,
)
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    AggregatedSignal,
    DataFreshness,
    ExecutionHint,
    ExecutionPlan,
    Fill,
    MarketSlice,
    OpenOrder,
    OrderIntent,
    PipelineFrame,
    PortfolioPlan,
    PortfolioTarget,
    PositionSnapshot,
    RebalancePlan,
    RiskDecision,
    Signal,
    SignalAction,
)

__all__ = [
    "Signal", "SignalAction", "AggregatedSignal", "MarketSlice", "DataFreshness",
    "AccountSnapshot", "PositionSnapshot", "OpenOrder", "Fill",
    "PortfolioPlan", "PortfolioTarget", "RebalancePlan",
    "OrderIntent", "ExecutionPlan", "ExecutionHint", "RiskDecision",
    "PipelineFrame",
    "SignalProducer", "SignalAggregator", "PortfolioConstructor",
    "PositionManagerProtocol", "RiskConstraintProtocol", "ExecutionPlannerProtocol",
    "DataTier", "TriggerPolicy", "CoveragePolicy",
    "register_signal_producer", "get_producer", "list_producers", "ProducerInfo",
    "emit_long", "emit_short", "emit_flat", "emit_no_view",
]
```

- [ ] **Step 2: 전체 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/ -v
```

Expected: 전부 pass

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_engine/pipeline/__init__.py
git commit -m "feat(pipeline): pipeline 패키지 공개 인터페이스 확정"
```
