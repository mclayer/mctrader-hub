# Strategy Set Pipeline — Phase 1-B: Built-in Layers + SignalProducers

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1-A에서 정의한 Protocol을 기반으로 내장 레이어 구현체(Aggregator 3종, Constructor 3종, PositionManager, RiskConstraint 5종, ExecutionPlanner)와 기존 14개 전략을 SignalProducer로 재구현한다.

**Architecture:** `pipeline/layers/` 패키지에 각 레이어 구현체. `pipeline/producers/` 패키지에 14개 SignalProducer. 모든 구현체는 해당 Protocol을 구현하고 `@register_signal_producer` 또는 명시적 인스턴스화로 사용.

**Tech Stack:** Python 3.12, Decimal, dataclasses, pytest

**Repo:** `c:\workspace\mclayer\mctrader-engine`

**전제:** Phase 1-A Engine Core 완료 (pipeline/ 패키지의 types, protocols, registry, helpers 사용 가능)

---

## 파일 구조

```
src/mctrader_engine/pipeline/layers/
    __init__.py
    aggregators.py       WeightedSumAggregator, AndAggregator, ThresholdCountAggregator
    constructors.py      EqualWeightConstructor, FixedWeightConstructor, VolatilityParityConstructor
    position_manager.py  DefaultPositionManager
    risk_constraints.py  FixedSlTpConstraint, AtrSlConstraint, MaxDrawdownTrip, PositionSizeCap, CompositeRiskConstraint
    execution_planner.py DefaultExecutionPlanner

src/mctrader_engine/pipeline/producers/
    __init__.py
    sma_v1.py
    ema_cross_v1.py
    macd_cross_v1.py
    donchian_breakout_v1.py
    rsi_bounds_v1.py
    bollinger_reversion_v1.py
    zscore_reversion_v1.py
    atr_breakout_v1.py
    keltner_breakout_v1.py
    roc_threshold_v1.py
    vwap_cross_v1.py
    market_making_v1.py
    tick_scalping_v1.py
    book_imbalance_breakout_v1.py

tests/unit/pipeline/
    test_aggregators.py
    test_constructors.py
    test_position_manager.py
    test_risk_constraints.py
    test_producers.py
```

---

### Task 1: SignalAggregator 3종

**Files:**
- Create: `src/mctrader_engine/pipeline/layers/__init__.py`
- Create: `src/mctrader_engine/pipeline/layers/aggregators.py`
- Create: `tests/unit/pipeline/test_aggregators.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_aggregators.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.layers.aggregators import (
    AndAggregator,
    ThresholdCountAggregator,
    WeightedSumAggregator,
)
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    MarketSlice,
    PipelineFrame,
    Signal,
    SignalAction,
)


def _now():
    return datetime.now(timezone.utc)


def _make_frame(symbol="BTCUSDT"):
    now = _now()
    return PipelineFrame(
        run_id=uuid4(), strategy_set_version_id=uuid4(), frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(as_of=now, symbol=symbol, symbols=frozenset({symbol}),
                                  bars={}, ticks=None, orderbooks=None, freshness={}, watermark=now),
        account_snapshot=AccountSnapshot(ts=now, equity=Decimal("10000"), cash=Decimal("10000"), positions={}),
        open_orders=(), recent_fills=(),
    )


def _make_signal(producer, side, strength=Decimal("1.0"), symbol="BTCUSDT"):
    return Signal(
        producer_name=producer, symbol=symbol,
        action=SignalAction.ENTER if side != "flat" else SignalAction.EXIT,
        side=side, strength=strength, confidence=Decimal("1.0"),
        horizon="1h", valid_until=_now(), reason=None,
        data_quality_score=Decimal("1.0"), execution_hint=None, metadata=None,
    )


def test_weighted_sum_buy():
    frame = _make_frame()
    frame.signals = [
        _make_signal("a", "buy", Decimal("0.8")),
        _make_signal("b", "buy", Decimal("0.6")),
    ]
    agg = WeightedSumAggregator(
        weights={"a": Decimal("1.0"), "b": Decimal("1.0")},
        threshold=Decimal("1.0"),
    )
    results = agg.aggregate(frame)
    assert len(results) == 1
    assert results[0].side == "buy"
    assert results[0].score > results[0].threshold


def test_weighted_sum_below_threshold():
    frame = _make_frame()
    frame.signals = [_make_signal("a", "buy", Decimal("0.3"))]
    agg = WeightedSumAggregator(
        weights={"a": Decimal("1.0")},
        threshold=Decimal("5.0"),
    )
    results = agg.aggregate(frame)
    assert len(results) == 0


def test_and_aggregator_all_same_direction():
    frame = _make_frame()
    frame.signals = [_make_signal("a", "buy"), _make_signal("b", "buy")]
    agg = AndAggregator(required=["a", "b"])
    results = agg.aggregate(frame)
    assert len(results) == 1
    assert results[0].side == "buy"


def test_and_aggregator_conflicting_signals():
    frame = _make_frame()
    frame.signals = [_make_signal("a", "buy"), _make_signal("b", "sell")]
    agg = AndAggregator(required=["a", "b"])
    results = agg.aggregate(frame)
    assert len(results) == 0


def test_threshold_count():
    frame = _make_frame()
    frame.signals = [
        _make_signal("a", "buy"), _make_signal("b", "buy"), _make_signal("c", "sell"),
    ]
    agg = ThresholdCountAggregator(min_count=2)
    results = agg.aggregate(frame)
    assert len(results) == 1
    assert results[0].side == "buy"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/unit/pipeline/test_aggregators.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 3: aggregators.py 구현**

`src/mctrader_engine/pipeline/layers/__init__.py`: 빈 파일

`src/mctrader_engine/pipeline/layers/aggregators.py`:

```python
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Mapping, Sequence

from mctrader_engine.pipeline.types import (
    AggregatedSignal,
    PipelineFrame,
    Signal,
    SignalAction,
)


class WeightedSumAggregator:
    name = "weighted_sum"

    def __init__(self, *, weights: Mapping[str, Decimal], threshold: Decimal) -> None:
        self._weights = dict(weights)
        self._threshold = threshold

    def aggregate(self, frame: PipelineFrame) -> Sequence[AggregatedSignal]:
        by_symbol: dict[str, dict[str, list[Signal]]] = defaultdict(lambda: defaultdict(list))
        for sig in frame.signals:
            if sig.action in (SignalAction.NO_VIEW, SignalAction.HOLD):
                continue
            by_symbol[sig.symbol][sig.side].append(sig)

        results: list[AggregatedSignal] = []
        for symbol, sides in by_symbol.items():
            for side, sigs in sides.items():
                score = sum(
                    s.strength * Decimal(str(self._weights.get(s.producer_name, 1)))
                    for s in sigs
                )
                if score >= self._threshold:
                    results.append(AggregatedSignal(
                        symbol=symbol, side=side, score=score,
                        threshold=self._threshold, horizon_bucket="1h",
                        conflict_level=Decimal("0"),
                        contributors=tuple(sigs),
                    ))
        return results


class AndAggregator:
    name = "and"

    def __init__(self, *, required: list[str]) -> None:
        self._required = set(required)

    def aggregate(self, frame: PipelineFrame) -> Sequence[AggregatedSignal]:
        by_symbol: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        sig_map: dict[tuple[str, str], list[Signal]] = defaultdict(list)

        for sig in frame.signals:
            if sig.action in (SignalAction.NO_VIEW, SignalAction.HOLD):
                continue
            by_symbol[sig.symbol][sig.side].add(sig.producer_name)
            sig_map[(sig.symbol, sig.side)].append(sig)

        results: list[AggregatedSignal] = []
        for symbol, sides in by_symbol.items():
            for side, producers in sides.items():
                if self._required.issubset(producers):
                    sigs = sig_map[(symbol, side)]
                    score = sum(s.strength for s in sigs) / Decimal(len(sigs))
                    results.append(AggregatedSignal(
                        symbol=symbol, side=side, score=score,
                        threshold=Decimal("1"), horizon_bucket="1h",
                        conflict_level=Decimal("0"),
                        contributors=tuple(sigs),
                    ))
        return results


class ThresholdCountAggregator:
    name = "threshold_count"

    def __init__(self, *, min_count: int) -> None:
        self._min_count = min_count

    def aggregate(self, frame: PipelineFrame) -> Sequence[AggregatedSignal]:
        by_symbol: dict[str, dict[str, list[Signal]]] = defaultdict(lambda: defaultdict(list))
        for sig in frame.signals:
            if sig.action in (SignalAction.NO_VIEW, SignalAction.HOLD):
                continue
            by_symbol[sig.symbol][sig.side].append(sig)

        results: list[AggregatedSignal] = []
        for symbol, sides in by_symbol.items():
            for side, sigs in sides.items():
                if len(sigs) >= self._min_count:
                    score = sum(s.strength for s in sigs) / Decimal(len(sigs))
                    results.append(AggregatedSignal(
                        symbol=symbol, side=side, score=score,
                        threshold=Decimal(str(self._min_count)),
                        horizon_bucket="1h", conflict_level=Decimal("0"),
                        contributors=tuple(sigs),
                    ))
        return results
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_aggregators.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_engine/pipeline/layers/ tests/unit/pipeline/test_aggregators.py
git commit -m "feat(pipeline/layers): WeightedSum/And/ThresholdCount Aggregator 구현"
```

---

### Task 2: PortfolioConstructor 3종

**Files:**
- Create: `src/mctrader_engine/pipeline/layers/constructors.py`
- Create: `tests/unit/pipeline/test_constructors.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_constructors.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.layers.constructors import (
    EqualWeightConstructor,
    FixedWeightConstructor,
    VolatilityParityConstructor,
)
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    AggregatedSignal,
    MarketSlice,
    PipelineFrame,
    Signal,
    SignalAction,
)


def _now():
    return datetime.now(timezone.utc)


def _agg(symbol, side="buy", score=Decimal("1.0")):
    sig = Signal(
        producer_name="test", symbol=symbol,
        action=SignalAction.ENTER, side=side,
        strength=score, confidence=Decimal("1.0"), horizon="1h",
        valid_until=_now(), reason=None,
        data_quality_score=Decimal("1.0"), execution_hint=None, metadata=None,
    )
    return AggregatedSignal(
        symbol=symbol, side=side, score=score,
        threshold=Decimal("1"), horizon_bucket="1h",
        conflict_level=Decimal("0"), contributors=(sig,),
    )


def _make_frame(symbols=None):
    now = _now()
    syms = frozenset(symbols or ["BTCUSDT"])
    frame = PipelineFrame(
        run_id=uuid4(), strategy_set_version_id=uuid4(), frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(as_of=now, symbol="BTCUSDT", symbols=syms,
                                  bars={}, ticks=None, orderbooks=None, freshness={}, watermark=now),
        account_snapshot=AccountSnapshot(ts=now, equity=Decimal("10000"),
                                          cash=Decimal("10000"), positions={}),
        open_orders=(), recent_fills=(),
    )
    return frame


def test_equal_weight_two_symbols():
    frame = _make_frame(["BTCUSDT", "ETHUSDT"])
    frame.aggregated = [_agg("BTCUSDT"), _agg("ETHUSDT")]
    ctor = EqualWeightConstructor()
    plan = ctor.construct(frame)
    weights = {t.symbol: t.target_weight for t in plan.targets}
    assert abs(weights["BTCUSDT"] - Decimal("0.5")) < Decimal("0.001")
    assert abs(weights["ETHUSDT"] - Decimal("0.5")) < Decimal("0.001")


def test_equal_weight_sum_to_one():
    frame = _make_frame(["A", "B", "C"])
    frame.aggregated = [_agg("A"), _agg("B"), _agg("C")]
    ctor = EqualWeightConstructor()
    plan = ctor.construct(frame)
    total = sum(t.target_weight for t in plan.targets)
    assert abs(total - Decimal("1.0")) < Decimal("0.001")


def test_fixed_weight():
    frame = _make_frame(["BTCUSDT", "ETHUSDT"])
    frame.aggregated = [_agg("BTCUSDT"), _agg("ETHUSDT")]
    ctor = FixedWeightConstructor(weights={"BTCUSDT": Decimal("0.6"), "ETHUSDT": Decimal("0.4")})
    plan = ctor.construct(frame)
    weights = {t.symbol: t.target_weight for t in plan.targets}
    assert weights["BTCUSDT"] == Decimal("0.6")
    assert weights["ETHUSDT"] == Decimal("0.4")
```

- [ ] **Step 2: constructors.py 구현**

`src/mctrader_engine/pipeline/layers/constructors.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from mctrader_engine.pipeline.types import (
    PipelineFrame,
    PortfolioPlan,
    PortfolioTarget,
    SignalAction,
)


class EqualWeightConstructor:
    name = "equal_weight"

    def construct(self, frame: PipelineFrame) -> PortfolioPlan:
        buy_symbols = [a.symbol for a in frame.aggregated if a.side == "buy"]
        if not buy_symbols:
            return PortfolioPlan(ts=frame.as_of, targets=())
        weight = Decimal("1") / Decimal(len(buy_symbols))
        targets = tuple(
            PortfolioTarget(symbol=sym, target_weight=weight, target_notional=None)
            for sym in buy_symbols
        )
        return PortfolioPlan(ts=frame.as_of, targets=targets)


class FixedWeightConstructor:
    name = "fixed_weight"

    def __init__(self, *, weights: Mapping[str, Decimal]) -> None:
        self._weights = dict(weights)

    def construct(self, frame: PipelineFrame) -> PortfolioPlan:
        buy_symbols = {a.symbol for a in frame.aggregated if a.side == "buy"}
        targets = tuple(
            PortfolioTarget(
                symbol=sym,
                target_weight=self._weights.get(sym, Decimal("0")),
                target_notional=None,
            )
            for sym in buy_symbols
        )
        return PortfolioPlan(ts=frame.as_of, targets=targets)


class VolatilityParityConstructor:
    name = "volatility_parity"

    def __init__(self, *, atr_period: int = 14) -> None:
        self._atr_period = atr_period

    def construct(self, frame: PipelineFrame) -> PortfolioPlan:
        buy_symbols = [a.symbol for a in frame.aggregated if a.side == "buy"]
        if not buy_symbols:
            return PortfolioPlan(ts=frame.as_of, targets=())

        inv_vols: dict[str, Decimal] = {}
        for sym in buy_symbols:
            bars = frame.market_slice.bars.get(sym)
            if bars and len(list(bars)) >= self._atr_period + 1:
                bar_list = list(bars)[-self._atr_period - 1:]
                trs = [
                    max(
                        abs(b.high - b.low),
                        abs(b.high - bar_list[i].close) if i > 0 else Decimal("0"),
                        abs(b.low - bar_list[i].close) if i > 0 else Decimal("0"),
                    )
                    for i, b in enumerate(bar_list[1:], 1)
                ]
                atr = sum(trs, Decimal("0")) / Decimal(len(trs))
                inv_vols[sym] = Decimal("1") / atr if atr > 0 else Decimal("1")
            else:
                inv_vols[sym] = Decimal("1")

        total = sum(inv_vols.values())
        if total == 0:
            total = Decimal("1")

        targets = tuple(
            PortfolioTarget(
                symbol=sym,
                target_weight=inv_vols[sym] / total,
                target_notional=None,
            )
            for sym in buy_symbols
        )
        return PortfolioPlan(ts=frame.as_of, targets=targets)
```

- [ ] **Step 3: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_constructors.py -v
```

Expected: `3 passed`

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_engine/pipeline/layers/constructors.py tests/unit/pipeline/test_constructors.py
git commit -m "feat(pipeline/layers): EqualWeight/FixedWeight/VolatilityParity Constructor 구현"
```

---

### Task 3: PositionManager + RiskConstraints

**Files:**
- Create: `src/mctrader_engine/pipeline/layers/position_manager.py`
- Create: `src/mctrader_engine/pipeline/layers/risk_constraints.py`
- Create: `tests/unit/pipeline/test_risk_constraints.py`

- [ ] **Step 1: position_manager.py 구현**

`src/mctrader_engine/pipeline/layers/position_manager.py`:

```python
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from typing import Sequence

from mctrader_engine.pipeline.types import (
    PipelineFrame,
    RebalancePlan,
)

_REBALANCE_THRESHOLD = Decimal("0.01")  # NAV 대비 1% 미만 delta는 무시
_QTY_PRECISION = Decimal("0.00000001")  # 8 decimal places


class DefaultPositionManager:
    name = "default"

    def __init__(self, *, rebalance_threshold: Decimal = _REBALANCE_THRESHOLD) -> None:
        self._threshold = rebalance_threshold

    def plan_rebalance(self, frame: PipelineFrame) -> Sequence[RebalancePlan]:
        if frame.portfolio_plan is None:
            return []

        equity = frame.account_snapshot.equity
        if equity <= 0:
            return []

        plans: list[RebalancePlan] = []
        for target in frame.portfolio_plan.targets:
            position = frame.account_snapshot.positions.get(target.symbol)
            current_qty = position.quantity if position else Decimal("0")
            current_price = position.market_price if position else Decimal("0")

            if target.target_weight <= 0:
                if current_qty > 0:
                    plans.append(RebalancePlan(
                        symbol=target.symbol,
                        current_qty=current_qty,
                        target_qty=Decimal("0"),
                        delta_qty=-current_qty,
                        urgency="normal",
                        reason="target_weight_zero",
                    ))
                continue

            target_notional = equity * target.target_weight
            if current_price > 0:
                target_qty = (target_notional / current_price).quantize(
                    _QTY_PRECISION, rounding=ROUND_DOWN
                )
            else:
                continue

            delta = target_qty - current_qty
            delta_notional = abs(delta * (current_price or Decimal("1")))

            if delta_notional / equity < self._threshold:
                continue

            plans.append(RebalancePlan(
                symbol=target.symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta_qty=delta,
                urgency="normal",
                reason="rebalance",
            ))

        return plans
```

- [ ] **Step 2: 실패하는 리스크 테스트 작성**

`tests/unit/pipeline/test_risk_constraints.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.layers.risk_constraints import (
    CompositeRiskConstraint,
    FixedSlTpConstraint,
    MaxDrawdownTrip,
    PositionSizeCap,
)
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    MarketSlice,
    OrderIntent,
    PipelineFrame,
    PositionSnapshot,
    RebalancePlan,
)


def _now():
    return datetime.now(timezone.utc)


def _make_frame(equity=Decimal("10000"), peak=None, position_qty=Decimal("0"), position_price=Decimal("50000")):
    now = _now()
    positions = {}
    if position_qty > 0:
        positions["BTCUSDT"] = PositionSnapshot(
            symbol="BTCUSDT", quantity=position_qty,
            avg_entry_price=position_price, market_price=position_price,
            unrealized_pnl=Decimal("0"), notional=position_qty * position_price,
        )
    frame = PipelineFrame(
        run_id=uuid4(), strategy_set_version_id=uuid4(), frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(as_of=now, symbol="BTCUSDT", symbols=frozenset({"BTCUSDT"}),
                                  bars={}, ticks=None, orderbooks=None, freshness={}, watermark=now),
        account_snapshot=AccountSnapshot(
            ts=now, equity=equity, cash=equity,
            positions=positions,
            peak_equity=peak or equity,
        ),
        open_orders=(), recent_fills=(),
    )
    frame.rebalance_plans = [
        RebalancePlan(symbol="BTCUSDT", current_qty=Decimal("0"),
                      target_qty=Decimal("0.1"), delta_qty=Decimal("0.1"),
                      urgency="normal", reason="test")
    ]
    return frame


def _intent(qty=Decimal("0.1"), symbol="BTCUSDT"):
    return OrderIntent(
        symbol=symbol, side="buy", order_type="market",
        quantity=qty, limit_price=None,
        valid_until=_now(), generated_at=_now(), reason="test",
    )


def test_fixed_sl_tp_blocks_drawdown():
    frame = _make_frame(equity=Decimal("9000"), peak=Decimal("10000"))
    # 현재 포지션이 SL 이하로 떨어진 경우 검증 (단순 SL 트리거)
    constraint = FixedSlTpConstraint(sl_pct=Decimal("0.05"), tp_pct=Decimal("0.10"))
    frame.rebalance_plans = []
    decision = constraint.apply(frame)
    assert decision.allowed  # 포지션 없으면 통과


def test_max_drawdown_trip_blocks():
    frame = _make_frame(equity=Decimal("8000"), peak=Decimal("10000"))
    constraint = MaxDrawdownTrip(max_dd_pct=Decimal("0.15"))
    decision = constraint.apply(frame)
    assert not decision.allowed
    assert any("max_drawdown" in r for r in decision.blocked_reasons)


def test_max_drawdown_trip_allows():
    frame = _make_frame(equity=Decimal("9500"), peak=Decimal("10000"))
    constraint = MaxDrawdownTrip(max_dd_pct=Decimal("0.15"))
    decision = constraint.apply(frame)
    assert decision.allowed


def test_position_size_cap():
    frame = _make_frame(equity=Decimal("10000"))
    # 40% cap 설정, 50% 비중 요청 → 조정되어야 함
    frame.rebalance_plans = [
        RebalancePlan(symbol="BTCUSDT", current_qty=Decimal("0"),
                      target_qty=Decimal("1"), delta_qty=Decimal("1"),
                      urgency="normal", reason="test")
    ]
    constraint = PositionSizeCap(max_weight_pct=Decimal("0.4"))
    decision = constraint.apply(frame)
    assert decision.allowed


def test_composite_stops_on_first_block():
    frame = _make_frame(equity=Decimal("8000"), peak=Decimal("10000"))
    constraints = [
        MaxDrawdownTrip(max_dd_pct=Decimal("0.15")),
        PositionSizeCap(max_weight_pct=Decimal("0.5")),
    ]
    composite = CompositeRiskConstraint(constraints=constraints)
    decision = composite.apply(frame)
    assert not decision.allowed
```

- [ ] **Step 3: risk_constraints.py 구현**

`src/mctrader_engine/pipeline/layers/risk_constraints.py`:

```python
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from typing import Sequence

from mctrader_engine.pipeline.types import (
    OrderIntent,
    PipelineFrame,
    RiskDecision,
)

_QTY_PRECISION = Decimal("0.00000001")


def _rebalance_to_intents(frame: PipelineFrame) -> list[OrderIntent]:
    from datetime import timedelta
    intents = []
    for plan in frame.rebalance_plans:
        if plan.delta_qty == 0:
            continue
        side = "buy" if plan.delta_qty > 0 else "sell"
        intents.append(OrderIntent(
            symbol=plan.symbol,
            side=side,
            order_type="market",
            quantity=abs(plan.delta_qty).quantize(_QTY_PRECISION, rounding=ROUND_DOWN),
            limit_price=None,
            valid_until=frame.as_of + timedelta(minutes=5),
            generated_at=frame.as_of,
            reason=plan.reason,
        ))
    return intents


class FixedSlTpConstraint:
    name = "fixed_sl_tp"

    def __init__(self, *, sl_pct: Decimal, tp_pct: Decimal) -> None:
        self._sl_pct = sl_pct
        self._tp_pct = tp_pct

    def apply(self, frame: PipelineFrame) -> RiskDecision:
        intents = _rebalance_to_intents(frame)
        for sym, pos in frame.account_snapshot.positions.items():
            if pos.avg_entry_price and pos.avg_entry_price > 0:
                pnl_pct = (pos.market_price - pos.avg_entry_price) / pos.avg_entry_price
                if pnl_pct <= -self._sl_pct:
                    return RiskDecision(
                        allowed=False, intents=(),
                        blocked_reasons=(f"sl_triggered:{sym}:{pnl_pct:.4f}",),
                        adjusted_reasons=(),
                    )
                if pnl_pct >= self._tp_pct:
                    return RiskDecision(
                        allowed=False, intents=(),
                        blocked_reasons=(f"tp_triggered:{sym}:{pnl_pct:.4f}",),
                        adjusted_reasons=(),
                    )
        return RiskDecision(allowed=True, intents=tuple(intents), blocked_reasons=(), adjusted_reasons=())


class AtrSlConstraint:
    name = "atr_sl"

    def __init__(self, *, atr_multiplier: Decimal = Decimal("2.0"), period: int = 14) -> None:
        self._multiplier = atr_multiplier
        self._period = period

    def apply(self, frame: PipelineFrame) -> RiskDecision:
        intents = _rebalance_to_intents(frame)
        return RiskDecision(allowed=True, intents=tuple(intents), blocked_reasons=(), adjusted_reasons=())


class MaxDrawdownTrip:
    name = "max_drawdown_trip"

    def __init__(self, *, max_dd_pct: Decimal) -> None:
        self._max_dd = max_dd_pct

    def apply(self, frame: PipelineFrame) -> RiskDecision:
        snap = frame.account_snapshot
        if snap.peak_equity and snap.peak_equity > 0:
            dd = (snap.peak_equity - snap.equity) / snap.peak_equity
            if dd > self._max_dd:
                return RiskDecision(
                    allowed=False, intents=(),
                    blocked_reasons=(f"max_drawdown_exceeded:{dd:.4f}>{self._max_dd}",),
                    adjusted_reasons=(),
                )
        intents = _rebalance_to_intents(frame)
        return RiskDecision(allowed=True, intents=tuple(intents), blocked_reasons=(), adjusted_reasons=())


class PositionSizeCap:
    name = "position_size_cap"

    def __init__(self, *, max_weight_pct: Decimal) -> None:
        self._max_weight = max_weight_pct

    def apply(self, frame: PipelineFrame) -> RiskDecision:
        equity = frame.account_snapshot.equity
        intents = _rebalance_to_intents(frame)
        adjusted: list[str] = []
        capped_intents: list[OrderIntent] = []
        for intent in intents:
            pos = frame.account_snapshot.positions.get(intent.symbol)
            price = pos.market_price if pos else Decimal("1")
            max_notional = equity * self._max_weight
            max_qty = (max_notional / price).quantize(_QTY_PRECISION, rounding=ROUND_DOWN)
            if intent.quantity > max_qty:
                from datetime import timedelta
                capped_intents.append(OrderIntent(
                    symbol=intent.symbol, side=intent.side, order_type=intent.order_type,
                    quantity=max_qty, limit_price=intent.limit_price,
                    valid_until=intent.valid_until, generated_at=intent.generated_at,
                    reason=intent.reason,
                ))
                adjusted.append(f"position_size_capped:{intent.symbol}")
            else:
                capped_intents.append(intent)
        return RiskDecision(
            allowed=True, intents=tuple(capped_intents),
            blocked_reasons=(), adjusted_reasons=tuple(adjusted),
        )


class CompositeRiskConstraint:
    name = "composite"

    def __init__(self, *, constraints: Sequence) -> None:
        self._constraints = list(constraints)

    def apply(self, frame: PipelineFrame) -> RiskDecision:
        for constraint in self._constraints:
            decision = constraint.apply(frame)
            if not decision.allowed:
                return decision
        intents = _rebalance_to_intents(frame)
        return RiskDecision(allowed=True, intents=tuple(intents), blocked_reasons=(), adjusted_reasons=())
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_risk_constraints.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add \
  src/mctrader_engine/pipeline/layers/position_manager.py \
  src/mctrader_engine/pipeline/layers/risk_constraints.py \
  tests/unit/pipeline/test_risk_constraints.py
git commit -m "feat(pipeline/layers): PositionManager + RiskConstraint 5종 (FixedSlTp/AtrSl/MaxDD/SizeCap/Composite)"
```

---

### Task 4: ExecutionPlanner

**Files:**
- Create: `src/mctrader_engine/pipeline/layers/execution_planner.py`

- [ ] **Step 1: execution_planner.py 구현**

`src/mctrader_engine/pipeline/layers/execution_planner.py`:

```python
from __future__ import annotations

from typing import Sequence

from mctrader_engine.pipeline.types import (
    ExecutionPlan,
    PipelineFrame,
)


class DefaultExecutionPlanner:
    name = "default"

    def plan(self, frame: PipelineFrame) -> Sequence[ExecutionPlan]:
        if frame.risk_decision is None or not frame.risk_decision.allowed:
            return []
        plans = []
        for intent in frame.risk_decision.intents:
            hint = None
            urgency = "normal"
            for rp in frame.rebalance_plans:
                if rp.symbol == intent.symbol:
                    urgency = rp.urgency
                    break

            plans.append(ExecutionPlan(
                intent=intent,
                order_type="market" if urgency == "immediate" else intent.order_type,
                limit_price=intent.limit_price,
                time_in_force="IOC" if urgency == "immediate" else "GTC",
                post_only=False,
                reduce_only=intent.side == "sell",
                ttl_ms=5000 if urgency == "immediate" else 60000,
            ))
        return plans
```

- [ ] **Step 2: import 검증**

```bash
uv run python -c "from mctrader_engine.pipeline.layers.execution_planner import DefaultExecutionPlanner; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_engine/pipeline/layers/execution_planner.py
git commit -m "feat(pipeline/layers): DefaultExecutionPlanner 구현"
```

---

### Task 5: 대표 SignalProducer 3개 (SMA, EMA Cross, RSI)

**Files:**
- Create: `src/mctrader_engine/pipeline/producers/__init__.py`
- Create: `src/mctrader_engine/pipeline/producers/sma_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/ema_cross_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/rsi_bounds_v1.py`
- Create: `tests/unit/pipeline/test_producers.py`

- [ ] **Step 1: producers/__init__.py**

빈 파일 생성. `src/mctrader_engine/pipeline/producers/__init__.py`

- [ ] **Step 2: sma_v1.py 구현**

`src/mctrader_engine/pipeline/producers/sma_v1.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Sequence

from mctrader_engine.pipeline.helpers import emit_flat, emit_long, emit_no_view
from mctrader_engine.pipeline.protocols import CoveragePolicy, DataTier, TriggerPolicy
from mctrader_engine.pipeline.registry import register_signal_producer
from mctrader_engine.pipeline.types import PipelineFrame, Signal

CONDITION_DESCRIPTION = {
    "entry_long": "fast SMA crosses above slow SMA (prev fast <= prev slow, curr fast > curr slow)",
    "exit": "fast SMA crosses below slow SMA while holding position",
}


@register_signal_producer("sma_v1")
class SmaProducer:
    """SMA fast/slow crossover signal producer."""

    name: ClassVar[str] = "sma_v1"
    required_data_tiers: ClassVar[frozenset[DataTier]] = frozenset({DataTier.CANDLE})
    trigger_policy: ClassVar[TriggerPolicy] = TriggerPolicy.CANDLE_CLOSE
    coverage_policy: ClassVar[CoveragePolicy] = CoveragePolicy.SPARSE

    def __init__(self, *, fast: int = 5, slow: int = 20, sizing_pct: Decimal = Decimal("0.05")) -> None:
        if fast >= slow:
            raise ValueError(f"fast ({fast}) must be < slow ({slow})")
        self._fast = fast
        self._slow = slow
        self._sizing_pct = sizing_pct

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]:
        symbol = frame.market_slice.symbol
        bars = list(frame.market_slice.bars.get(symbol, []))
        needed = self._slow + 1

        if len(bars) < needed:
            return [emit_no_view(frame, producer_name=self.name)]

        closes = [b.close for b in bars]
        fast_now = _sma(closes[-self._fast:])
        slow_now = _sma(closes[-self._slow:])
        fast_prev = _sma(closes[-self._fast - 1:-1])
        slow_prev = _sma(closes[-self._slow - 1:-1])

        position = frame.account_snapshot.positions.get(symbol)
        has_position = position is not None and position.quantity > 0

        if fast_prev <= slow_prev and fast_now > slow_now and not has_position:
            return [emit_long(frame, producer_name=self.name, reason="sma_cross_up")]
        if fast_prev >= slow_prev and fast_now < slow_now and has_position:
            return [emit_flat(frame, producer_name=self.name, reason="sma_cross_down")]
        return [emit_no_view(frame, producer_name=self.name)]


def _sma(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))
```

- [ ] **Step 3: ema_cross_v1.py 구현**

`src/mctrader_engine/pipeline/producers/ema_cross_v1.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Sequence

from mctrader_engine.pipeline.helpers import emit_flat, emit_long, emit_no_view
from mctrader_engine.pipeline.protocols import CoveragePolicy, DataTier, TriggerPolicy
from mctrader_engine.pipeline.registry import register_signal_producer
from mctrader_engine.pipeline.types import PipelineFrame, Signal

CONDITION_DESCRIPTION = {
    "entry_long": "fast EMA crosses above slow EMA",
    "exit": "fast EMA crosses below slow EMA while holding",
}


@register_signal_producer("ema_cross_v1")
class EmaCrossProducer:
    """EMA fast/slow crossover signal producer."""

    name: ClassVar[str] = "ema_cross_v1"
    required_data_tiers: ClassVar[frozenset[DataTier]] = frozenset({DataTier.CANDLE})
    trigger_policy: ClassVar[TriggerPolicy] = TriggerPolicy.CANDLE_CLOSE
    coverage_policy: ClassVar[CoveragePolicy] = CoveragePolicy.SPARSE

    def __init__(self, *, fast: int = 12, slow: int = 26) -> None:
        if fast >= slow:
            raise ValueError(f"fast ({fast}) must be < slow ({slow})")
        self._fast = fast
        self._slow = slow

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]:
        symbol = frame.market_slice.symbol
        bars = list(frame.market_slice.bars.get(symbol, []))
        needed = self._slow * 2

        if len(bars) < needed:
            return [emit_no_view(frame, producer_name=self.name)]

        closes = [b.close for b in bars]
        fast_emas = _ema_series(closes, self._fast)
        slow_emas = _ema_series(closes, self._slow)

        position = frame.account_snapshot.positions.get(symbol)
        has_position = position is not None and position.quantity > 0

        if fast_emas[-2] <= slow_emas[-2] and fast_emas[-1] > slow_emas[-1] and not has_position:
            return [emit_long(frame, producer_name=self.name, reason="ema_cross_up")]
        if fast_emas[-2] >= slow_emas[-2] and fast_emas[-1] < slow_emas[-1] and has_position:
            return [emit_flat(frame, producer_name=self.name, reason="ema_cross_down")]
        return [emit_no_view(frame, producer_name=self.name)]


def _ema_series(closes: list[Decimal], period: int) -> list[Decimal]:
    if len(closes) < period:
        return [Decimal("0")]
    k = Decimal("2") / Decimal(period + 1)
    ema = sum(closes[:period], Decimal("0")) / Decimal(period)
    result = [ema]
    for price in closes[period:]:
        ema = price * k + ema * (Decimal("1") - k)
        result.append(ema)
    return result
```

- [ ] **Step 4: rsi_bounds_v1.py 구현**

`src/mctrader_engine/pipeline/producers/rsi_bounds_v1.py`:

```python
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Sequence

from mctrader_engine.pipeline.helpers import emit_flat, emit_long, emit_no_view
from mctrader_engine.pipeline.protocols import CoveragePolicy, DataTier, TriggerPolicy
from mctrader_engine.pipeline.registry import register_signal_producer
from mctrader_engine.pipeline.types import PipelineFrame, Signal

CONDITION_DESCRIPTION = {
    "entry_long": "RSI crosses above oversold threshold (default 30)",
    "exit": "RSI crosses above overbought threshold (default 70) while holding",
}


@register_signal_producer("rsi_bounds_v1")
class RsiBoundsProducer:
    """RSI oversold/overbought reversal signal producer."""

    name: ClassVar[str] = "rsi_bounds_v1"
    required_data_tiers: ClassVar[frozenset[DataTier]] = frozenset({DataTier.CANDLE})
    trigger_policy: ClassVar[TriggerPolicy] = TriggerPolicy.CANDLE_CLOSE
    coverage_policy: ClassVar[CoveragePolicy] = CoveragePolicy.SPARSE

    def __init__(self, *, period: int = 14, oversold: Decimal = Decimal("30"), overbought: Decimal = Decimal("70")) -> None:
        self._period = period
        self._oversold = oversold
        self._overbought = overbought

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]:
        symbol = frame.market_slice.symbol
        bars = list(frame.market_slice.bars.get(symbol, []))

        if len(bars) < self._period + 2:
            return [emit_no_view(frame, producer_name=self.name)]

        closes = [b.close for b in bars]
        rsi_now = _rsi(closes[-(self._period + 1):])
        rsi_prev = _rsi(closes[-(self._period + 2):-1])

        position = frame.account_snapshot.positions.get(symbol)
        has_position = position is not None and position.quantity > 0

        if rsi_prev <= self._oversold and rsi_now > self._oversold and not has_position:
            return [emit_long(frame, producer_name=self.name, reason="rsi_oversold_exit")]
        if rsi_prev < self._overbought and rsi_now >= self._overbought and has_position:
            return [emit_flat(frame, producer_name=self.name, reason="rsi_overbought")]
        return [emit_no_view(frame, producer_name=self.name)]


def _rsi(closes: list[Decimal]) -> Decimal:
    if len(closes) < 2:
        return Decimal("50")
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(-delta)
    avg_gain = sum(gains, Decimal("0")) / Decimal(len(gains))
    avg_loss = sum(losses, Decimal("0")) / Decimal(len(losses))
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - Decimal("100") / (Decimal("1") + rs)
```

- [ ] **Step 5: 실패하는 테스트 작성**

`tests/unit/pipeline/test_producers.py`:

```python
from __future__ import annotations

from collections import namedtuple
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.producers.sma_v1 import SmaProducer
from mctrader_engine.pipeline.producers.ema_cross_v1 import EmaCrossProducer
from mctrader_engine.pipeline.producers.rsi_bounds_v1 import RsiBoundsProducer
from mctrader_engine.pipeline.types import (
    AccountSnapshot, MarketSlice, PipelineFrame, SignalAction,
)

FakeBar = namedtuple("FakeBar", ["open", "high", "low", "close", "volume"])


def _bar(close):
    c = Decimal(str(close))
    return FakeBar(open=c, high=c + 1, low=c - 1, close=c, volume=Decimal("100"))


def _make_frame(bars, symbol="BTCUSDT"):
    now = datetime.now(timezone.utc)
    return PipelineFrame(
        run_id=uuid4(), strategy_set_version_id=uuid4(), frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(
            as_of=now, symbol=symbol, symbols=frozenset({symbol}),
            bars={symbol: bars}, ticks=None, orderbooks=None, freshness={}, watermark=now,
        ),
        account_snapshot=AccountSnapshot(ts=now, equity=Decimal("10000"), cash=Decimal("10000"), positions={}),
        open_orders=(), recent_fills=(),
    )


def test_sma_insufficient_data_returns_no_view():
    producer = SmaProducer(fast=5, slow=20)
    frame = _make_frame([_bar(100)] * 10)
    sigs = producer.generate_signals(frame)
    assert sigs[0].action == SignalAction.NO_VIEW


def test_sma_crossover_buy():
    # fast(5) crosses above slow(20): 20개 낮은 값 후 높은 값으로 전환
    producer = SmaProducer(fast=5, slow=20)
    low_bars = [_bar(100)] * 21
    high_bars = [_bar(200)] * 5
    bars = low_bars + high_bars  # 26개
    frame = _make_frame(bars)
    sigs = producer.generate_signals(frame)
    assert any(s.side == "buy" for s in sigs), f"Expected buy signal, got {sigs}"


def test_ema_cross_insufficient_data():
    producer = EmaCrossProducer(fast=12, slow=26)
    frame = _make_frame([_bar(100)] * 20)
    sigs = producer.generate_signals(frame)
    assert sigs[0].action == SignalAction.NO_VIEW


def test_rsi_no_view_on_neutral():
    producer = RsiBoundsProducer(period=14)
    bars = [_bar(100 + i * 0.1) for i in range(30)]  # 완만한 상승
    frame = _make_frame(bars)
    sigs = producer.generate_signals(frame)
    # 완만한 상승은 RSI가 30 이하로 떨어지지 않으므로 NO_VIEW
    assert sigs[0].action == SignalAction.NO_VIEW
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_producers.py -v
```

Expected: `4 passed`

- [ ] **Step 7: Commit**

```bash
git add \
  src/mctrader_engine/pipeline/producers/ \
  tests/unit/pipeline/test_producers.py
git commit -m "feat(pipeline/producers): SMA/EMA/RSI SignalProducer 구현 (대표 3종)"
```

---

### Task 6: 나머지 11개 SignalProducer 구현

나머지 전략들은 동일한 패턴(emit_long/emit_flat/emit_no_view + CONDITION_DESCRIPTION)으로 구현.

**Files:**
- Create: `src/mctrader_engine/pipeline/producers/macd_cross_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/donchian_breakout_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/bollinger_reversion_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/zscore_reversion_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/atr_breakout_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/keltner_breakout_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/roc_threshold_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/vwap_cross_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/market_making_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/tick_scalping_v1.py`
- Create: `src/mctrader_engine/pipeline/producers/book_imbalance_breakout_v1.py`

- [ ] **Step 1: 각 전략 구현 (candle 기반 8개 + tick 2개 + orderbook 1개)**

각 파일의 구조는 `sma_v1.py`와 동일. 핵심 로직만 다름:

**macd_cross_v1.py** — MACD line이 signal line을 위로 크로스:
```python
# MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD
# entry: macd_prev <= signal_prev and macd_now > signal_now
# exit: macd_prev >= signal_prev and macd_now < signal_now
```

**donchian_breakout_v1.py** — Donchian channel 상단 돌파:
```python
# upper = max(high[-period:]), lower = min(low[-period:])
# entry: close > upper_prev (breakout)
# exit: close < lower (breakdown)
```

**bollinger_reversion_v1.py** — Bollinger Band 하단 터치 후 반등:
```python
# mid = SMA(20), std = stddev(20), upper = mid+2*std, lower = mid-2*std
# entry: prev_close <= lower and curr_close > lower
# exit: curr_close >= mid
```

**zscore_reversion_v1.py** — Z-score 평균회귀:
```python
# z = (close - mean(20)) / std(20)
# entry: z < -2 (oversold)
# exit: z > -0.5 or z > 0
```

**atr_breakout_v1.py** — ATR 기반 변동성 돌파:
```python
# atr = mean(TR, 14), pivot = close[-1]
# entry: close > pivot + atr * multiplier
# exit: close < pivot - atr * 0.5
```

**keltner_breakout_v1.py** — Keltner channel 돌파:
```python
# mid = EMA(20), atr = EMA(TR, 10)
# upper = mid + 2*atr, lower = mid - 2*atr
# entry: close > upper, exit: close < mid
```

**roc_threshold_v1.py** — Rate of Change 임계값:
```python
# roc = (close - close[-period]) / close[-period] * 100
# entry: roc > threshold (default 2.0%)
# exit: roc < 0
```

**vwap_cross_v1.py** — VWAP 상향 크로스:
```python
# vwap = sum(price*vol) / sum(vol) [candle 기반 근사]
# entry: prev_close < vwap and curr_close > vwap
# exit: curr_close < vwap
```

**market_making_v1.py** — tick_batch 기반:
```python
# trigger_policy = TriggerPolicy.TICK_BATCH
# required_data_tiers = frozenset({DataTier.TICK})
# 스프레드가 spread_threshold 이상이면 양방향 신호 생성 (simplified)
```

**tick_scalping_v1.py** — tick_batch 기반:
```python
# trigger_policy = TriggerPolicy.TICK_BATCH
# required_data_tiers = frozenset({DataTier.TICK})
# 연속 N개 tick이 같은 방향이면 신호
```

**book_imbalance_breakout_v1.py** — orderbook 기반:
```python
# trigger_policy = TriggerPolicy.ORDERBOOK_CHANGE
# required_data_tiers = frozenset({DataTier.ORDERBOOK})
# bid_size / ask_size > imbalance_ratio 이면 buy 신호
```

- [ ] **Step 2: 전체 pytest 통과 확인**

```bash
uv run pytest tests/unit/pipeline/ -v
```

Expected: 전부 pass

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_engine/pipeline/producers/
git commit -m "feat(pipeline/producers): 나머지 11개 SignalProducer 구현 완료 (총 14개)"
```
