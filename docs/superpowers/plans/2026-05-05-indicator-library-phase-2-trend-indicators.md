# Indicator library Phase 2 — Trend indicators (EMA, MACD, Donchian)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three trend-following indicators (EMA, MACD, Donchian Channels) on top of the Phase 1 scaffold. EMA = textbook (`alpha = 2 / (N+1)`) with SMA seed. MACD = EMA(fast) − EMA(slow) + EMA-on-MACD signal + histogram. Donchian = rolling max(high) / min(low) with O(n) monotonic-deque. All three obey the Phase 1 contract suite (5 invariants) + per-indicator 50k-bar < 500ms perf gate. INDICATOR_META gains 3 entries (`ema`, `macd`, `donchian`).

**Architecture:** Pure module-level functions in `mctrader_engine.indicators.trend`. EMA exposes a public `compute_ema(candles, *, period)` plus a private `_ema_values(values, *, period)` helper that MACD reuses on a Decimal-or-None sequence. Multi-output indicators (MACD, Donchian) return `typing.NamedTuple` types defined in `indicators.types`. Contract suite extends via lambda adapters in `INDICATOR_FUNCS` (one entry per output field of multi-output indicators) — no boilerplate test functions needed.

**Tech Stack:** Python 3.11–3.12, Decimal arithmetic only, pytest 8. No new runtime dependencies. Stays at mctrader-engine 0.29.0 (single-Epic version per spec §6).

**Branch:** `feat/mct-90-phase-2-trend-indicators` (off main commit `4f4a4e1`).

**Out of scope (later phases):**
- Mean-reversion / volatility / momentum / volume indicators (phases 3–4)
- Wilder smoothing variant (RSI/ATR Phase 3)
- Strategies that use these indicators (phases 5–6)
- CLI `indicator list` (Phase 7)

---

## File map (Phase 2)

**Modify:**
- `mctrader-engine/src/mctrader_engine/indicators/types.py` — add `MacdSeries`, `DonchianChannels` NamedTuples
- `mctrader-engine/src/mctrader_engine/indicators/trend.py` — add `_ema_values`, `compute_ema`, `compute_macd`, `compute_donchian`
- `mctrader-engine/src/mctrader_engine/indicators/__init__.py` — re-export new public names
- `mctrader-engine/src/mctrader_engine/indicators/meta.py` — add 3 `INDICATOR_META` entries
- `mctrader-engine/tests/indicators/test_trend.py` — add value-level fixtures for EMA, MACD, Donchian (incl. MACD warmup boundary)
- `mctrader-engine/tests/indicators/test_meta.py` — no required change (existing self-consistency loop already covers new entries)
- `mctrader-engine/tests/indicators/test_lookahead_contract.py` — extend `INDICATOR_FUNCS` with EMA + MACD-field + Donchian-field lambda adapters
- `mctrader-engine/tests/indicators/test_perf_budget.py` — add per-indicator 50k-bar gates

**Create:** none.

**Existing tests must continue to pass (regression):** all of Phase 1's 28 indicator tests + the SmaStrategy tests (5).

---

## Task 1: compute_ema end-to-end

EMA is the foundation for MACD. Implement the public function, the private values-level helper that MACD will reuse, the metadata entry, the contract suite extension, and the perf gate — all in one task so the indicator lands as a self-contained unit.

**Files:**
- Modify: `mctrader-engine/src/mctrader_engine/indicators/trend.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/__init__.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/meta.py`
- Modify: `mctrader-engine/tests/indicators/test_trend.py`
- Modify: `mctrader-engine/tests/indicators/test_lookahead_contract.py`
- Modify: `mctrader-engine/tests/indicators/test_perf_budget.py`

- [ ] **Step 1.1: Add EMA value tests (TDD Red)**

Append to `mctrader-engine/tests/indicators/test_trend.py`:

```python
def test_compute_ema_basic_period_3() -> None:
    # alpha = 2/(3+1) = 0.5. SMA seed at idx=2 = mean(10,20,30)=20.
    # idx=3: 0.5*40 + 0.5*20 = 30
    # idx=4: 0.5*50 + 0.5*30 = 40
    # idx=5: 0.5*60 + 0.5*40 = 50
    candles = make_candles(closes=[Decimal(c) for c in (10, 20, 30, 40, 50, 60)])
    result = compute_ema(candles, period=3)
    assert result == [
        None,
        None,
        Decimal("20"),
        Decimal("30"),
        Decimal("40"),
        Decimal("50"),
    ]


def test_compute_ema_period_2_alpha_two_thirds() -> None:
    # alpha = 2/3. Seed at idx=1 = mean(10,20)=15.
    # idx=2: (2/3)*30 + (1/3)*15 = 20 + 5 = 25
    # idx=3: (2/3)*40 + (1/3)*25 = 26.666... + 8.333... = 35
    candles = make_candles(closes=[Decimal(c) for c in (10, 20, 30, 40)])
    result = compute_ema(candles, period=2)
    assert result[0] is None
    assert result[1] == Decimal("15")
    assert result[2] == Decimal("25")
    assert result[3] == Decimal("35")


def test_compute_ema_warmup_only_when_insufficient() -> None:
    candles = make_candles(closes=[Decimal("100"), Decimal("200")])
    result = compute_ema(candles, period=5)
    assert result == [None, None]


def test_compute_ema_empty_returns_empty() -> None:
    assert compute_ema([], period=5) == []


def test_compute_ema_invalid_period_raises() -> None:
    candles = make_candles(closes=[Decimal("100")])
    with pytest.raises(ValueError):
        compute_ema(candles, period=0)
    with pytest.raises(ValueError):
        compute_ema(candles, period=-1)
```

Add the import at the top of the file alongside the existing `compute_sma` import:

```python
from mctrader_engine.indicators import compute_ema, compute_sma
```

- [ ] **Step 1.2: Run test to verify it fails (Red)**

```
cd c:/workspace/mclayer/mctrader-engine
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -10
```

Expected: collection error (`ImportError: cannot import name 'compute_ema'`).

- [ ] **Step 1.3: Implement `_ema_values` + `compute_ema` in trend.py**

In `mctrader-engine/src/mctrader_engine/indicators/trend.py`, append (after `compute_sma`):

```python
def _ema_values(
    values: Sequence[Decimal | None],
    *,
    period: int,
) -> list[Decimal | None]:
    """Textbook EMA over a values sequence (may contain leading None for upstream warmup).

    Internal helper. ``compute_ema`` (public, candle-based) and ``compute_macd``
    (signal line over MACD series) both call this with different inputs.

    Algorithm:
        alpha = 2 / (period + 1)
        Seed = SMA of first ``period`` non-None values (seed at the index of the
        period-th non-None value).
        Recurse: EMA_t = alpha * value_t + (1 - alpha) * EMA_{t-1}.
        Boundary 18-place quantize at output. Internal accumulation stays raw.
    """
    if period <= 0:
        raise ValueError(f"period={period} must be positive")

    n = len(values)
    out: list[Decimal | None] = [None] * n
    alpha = Decimal(2) / Decimal(period + 1)
    one_minus_alpha = Decimal(1) - alpha

    # Find the period-th non-None value to seed.
    non_none_seen: list[Decimal] = []
    seed_idx: int | None = None
    for i in range(n):
        v = values[i]
        if v is None:
            continue
        non_none_seen.append(v)
        if len(non_none_seen) == period:
            seed_idx = i
            break

    if seed_idx is None:
        return out  # Insufficient values, all None.

    seed = sum(non_none_seen, Decimal("0")) / Decimal(period)
    out[seed_idx] = seed.quantize(_QUANTIZE_18)

    prev = seed
    for i in range(seed_idx + 1, n):
        v = values[i]
        if v is None:
            # Should not happen post-seed for typical inputs, but be defensive:
            # propagate the previous EMA (no recurrence step on missing value).
            out[i] = prev.quantize(_QUANTIZE_18)
            continue
        prev = alpha * v + one_minus_alpha * prev
        out[i] = prev.quantize(_QUANTIZE_18)

    return out


def compute_ema(
    candles: Sequence[CandleLike],
    *,
    period: int,
) -> list[Decimal | None]:
    """Textbook Exponential Moving Average over close prices (alpha = 2/(N+1)).

    Returns a list of length ``len(candles)``. Leading ``period - 1`` entries
    are ``None`` (warmup). Index ``period - 1`` is the SMA seed; subsequent
    entries follow the EMA recurrence. Boundary 18-place quantize at output.

    Caller is responsible for passing a lookahead-safe sequence (e.g.,
    ``visible_window(...)`` output).
    """
    if period <= 0:
        raise ValueError(f"period={period} must be positive")

    closes: list[Decimal | None] = [c.close for c in candles]
    return _ema_values(closes, period=period)
```

- [ ] **Step 1.4: Re-export `compute_ema` from `__init__.py`**

In `mctrader-engine/src/mctrader_engine/indicators/__init__.py`, modify the imports + `__all__`:

```python
from mctrader_engine.indicators.meta import INDICATOR_META
from mctrader_engine.indicators.trend import compute_ema, compute_sma
from mctrader_engine.indicators.types import IndicatorMeta, IndicatorRole

__all__ = [
    "compute_ema",
    "compute_sma",
    "IndicatorMeta",
    "IndicatorRole",
    "INDICATOR_META",
]
```

- [ ] **Step 1.5: Add INDICATOR_META["ema"] entry**

In `mctrader-engine/src/mctrader_engine/indicators/meta.py`, modify the registry:

```python
INDICATOR_META: Final[dict[str, IndicatorMeta]] = {
    "sma": IndicatorMeta(
        key="sma",
        display_name="SMA (Simple Moving Average)",
        role="overlay",
        yaxis_label=None,
    ),
    "ema": IndicatorMeta(
        key="ema",
        display_name="EMA (Exponential Moving Average)",
        role="overlay",
        yaxis_label=None,
    ),
}
```

- [ ] **Step 1.6: Run EMA value tests to verify Green**

```
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -15
```

Expected: 12 passed (7 existing SMA tests + 5 new EMA tests).

- [ ] **Step 1.7: Extend INDICATOR_FUNCS contract suite with EMA**

In `mctrader-engine/tests/indicators/test_lookahead_contract.py`, modify:

```python
from mctrader_engine.indicators import compute_ema, compute_sma
```

Then extend `INDICATOR_FUNCS`:

```python
INDICATOR_FUNCS: list[tuple[str, Callable[..., list[Decimal | None]], dict[str, Any], int]] = [
    ("sma_period_5", compute_sma, {"period": 5}, 4),
    ("sma_period_3", compute_sma, {"period": 3}, 2),
    ("sma_period_1", compute_sma, {"period": 1}, 0),
    ("ema_period_5", compute_ema, {"period": 5}, 4),
    ("ema_period_3", compute_ema, {"period": 3}, 2),
    ("ema_period_1", compute_ema, {"period": 1}, 0),
]
```

- [ ] **Step 1.8: Run contract suite**

```
uv run python -m pytest tests/indicators/test_lookahead_contract.py -v 2>&1 | tail -20
```

Expected: 30 passed (5 invariants × 6 entries).

- [ ] **Step 1.9: Add EMA perf gate**

In `mctrader-engine/tests/indicators/test_perf_budget.py`, add the import and a new test:

```python
from mctrader_engine.indicators import compute_ema, compute_sma
```

```python
def test_compute_ema_50k_bars_under_budget(long_candles) -> None:
    start = time.perf_counter()
    result = compute_ema(long_candles, period=20)
    elapsed = time.perf_counter() - start
    assert len(result) == N_BARS
    assert elapsed < PERF_BUDGET_SEC, (
        f"compute_ema(period=20) on {N_BARS} bars took {elapsed*1000:.1f}ms "
        f"(budget {PERF_BUDGET_SEC*1000:.0f}ms). Likely algorithmic regression."
    )
```

- [ ] **Step 1.10: Run perf gate**

```
uv run python -m pytest tests/indicators/test_perf_budget.py -v 2>&1 | tail -10
```

Expected: 2 passed.

- [ ] **Step 1.11: Commit**

```
cd c:/workspace/mclayer/mctrader-engine
git checkout -b feat/mct-90-phase-2-trend-indicators
git add src/mctrader_engine/indicators/trend.py src/mctrader_engine/indicators/__init__.py src/mctrader_engine/indicators/meta.py tests/indicators/test_trend.py tests/indicators/test_lookahead_contract.py tests/indicators/test_perf_budget.py
git commit -m "feat(indicators): compute_ema textbook EMA + INDICATOR_META + contract + perf gate (MCT-90 Phase 2)"
```

---

## Task 2: MacdSeries + compute_macd end-to-end

MACD = EMA(close, fast) − EMA(close, slow). Signal = EMA-on-MACD with SMA seed of first `signal` non-None MACD values. Histogram = MACD − Signal. Each output is a full-length `list[Decimal | None]`; warmup propagates per Codex risk-1 (MACD warmup = `slow - 1`, Signal/Histogram warmup = `slow + signal - 2`).

**Files:**
- Modify: `mctrader-engine/src/mctrader_engine/indicators/types.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/trend.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/__init__.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/meta.py`
- Modify: `mctrader-engine/tests/indicators/test_trend.py`
- Modify: `mctrader-engine/tests/indicators/test_lookahead_contract.py`
- Modify: `mctrader-engine/tests/indicators/test_perf_budget.py`

- [ ] **Step 2.1: Add MacdSeries NamedTuple**

In `mctrader-engine/src/mctrader_engine/indicators/types.py`, append:

```python
from decimal import Decimal
from typing import NamedTuple


class MacdSeries(NamedTuple):
    """MACD multi-output: macd line, signal line, histogram.

    All three are full-length ``list[Decimal | None]`` matching ``len(candles)``.
    Warmup boundaries:
        macd     — first non-None at index ``slow - 1``
        signal   — first non-None at index ``slow - 1 + signal - 1 == slow + signal - 2``
        histogram — same as signal (computed as macd - signal at each index where both are non-None).
    """

    macd: list[Decimal | None]
    signal: list[Decimal | None]
    histogram: list[Decimal | None]
```

(Make sure the file's existing `from __future__ import annotations` line stays at the top.)

- [ ] **Step 2.2: Add MACD value tests (TDD Red)**

In `mctrader-engine/tests/indicators/test_trend.py`, add the import:

```python
from mctrader_engine.indicators import MacdSeries, compute_macd
```

Then append:

```python
def test_compute_macd_short_series_warmup_boundaries() -> None:
    """Codex top-risk-1 guard: assert exact first non-None index per field."""
    # 6 closes, fast=2, slow=3, signal=2.
    # MACD warmup = slow-1 = 2. Signal/Histogram warmup = slow+signal-2 = 3.
    candles = make_candles(closes=[Decimal(c) for c in (10, 20, 30, 40, 50, 60)])
    result = compute_macd(candles, fast=2, slow=3, signal=2)

    assert isinstance(result, MacdSeries)
    assert len(result.macd) == 6
    assert len(result.signal) == 6
    assert len(result.histogram) == 6

    # MACD warmup: indices 0,1 None; index 2 first non-None.
    assert result.macd[0] is None
    assert result.macd[1] is None
    assert result.macd[2] is not None

    # Signal warmup: indices 0,1,2 None; index 3 first non-None.
    assert result.signal[0] is None
    assert result.signal[1] is None
    assert result.signal[2] is None
    assert result.signal[3] is not None

    # Histogram = MACD - Signal at each index where both non-None.
    assert result.histogram[0] is None
    assert result.histogram[3] is not None
    assert result.histogram[3] == result.macd[3] - result.signal[3]


def test_compute_macd_default_params_canonical() -> None:
    """fast=12, slow=26, signal=9 — boundary indices 25 and 33."""
    candles = make_candles(closes=[Decimal(100 + i) for i in range(40)])
    result = compute_macd(candles)
    assert isinstance(result, MacdSeries)
    assert all(v is None for v in result.macd[:25])
    assert result.macd[25] is not None
    assert all(v is None for v in result.signal[:33])
    assert result.signal[33] is not None
    assert result.histogram[33] == result.macd[33] - result.signal[33]


def test_compute_macd_invalid_params_raise() -> None:
    candles = make_candles(closes=[Decimal("100") for _ in range(5)])
    with pytest.raises(ValueError):
        compute_macd(candles, fast=0, slow=26, signal=9)
    with pytest.raises(ValueError):
        compute_macd(candles, fast=26, slow=12, signal=9)  # fast >= slow
    with pytest.raises(ValueError):
        compute_macd(candles, fast=12, slow=26, signal=0)
```

- [ ] **Step 2.3: Run tests to verify Red**

```
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -10
```

Expected: import error (`cannot import name 'MacdSeries'` or `compute_macd`).

- [ ] **Step 2.4: Implement compute_macd**

In `mctrader-engine/src/mctrader_engine/indicators/trend.py`, append:

```python
from mctrader_engine.indicators.types import MacdSeries  # placed after existing imports


def compute_macd(
    candles: Sequence[CandleLike],
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> MacdSeries:
    """MACD = EMA(close, fast) - EMA(close, slow); Signal = EMA-on-MACD(signal); Histogram = MACD - Signal.

    Returns a NamedTuple of three full-length lists. Warmup propagation:
        macd      first non-None at index slow - 1
        signal    first non-None at index slow + signal - 2
        histogram first non-None at index slow + signal - 2

    Boundary 18-place quantize at output. Internal EMA recurrence stays raw.
    """
    if fast <= 0 or slow <= 0 or signal <= 0:
        raise ValueError(f"fast={fast} slow={slow} signal={signal} — all must be positive")
    if fast >= slow:
        raise ValueError(f"fast={fast} must be < slow={slow}")

    ema_fast = compute_ema(candles, period=fast)
    ema_slow = compute_ema(candles, period=slow)

    n = len(candles)
    macd_line: list[Decimal | None] = [None] * n
    for i in range(n):
        f = ema_fast[i]
        s = ema_slow[i]
        if f is None or s is None:
            continue
        macd_line[i] = (f - s).quantize(_QUANTIZE_18)

    signal_line = _ema_values(macd_line, period=signal)

    histogram: list[Decimal | None] = [None] * n
    for i in range(n):
        m = macd_line[i]
        s = signal_line[i]
        if m is None or s is None:
            continue
        histogram[i] = (m - s).quantize(_QUANTIZE_18)

    return MacdSeries(macd=macd_line, signal=signal_line, histogram=histogram)
```

- [ ] **Step 2.5: Re-export `compute_macd` and `MacdSeries`**

In `mctrader-engine/src/mctrader_engine/indicators/__init__.py`:

```python
from mctrader_engine.indicators.meta import INDICATOR_META
from mctrader_engine.indicators.trend import compute_ema, compute_macd, compute_sma
from mctrader_engine.indicators.types import IndicatorMeta, IndicatorRole, MacdSeries

__all__ = [
    "compute_ema",
    "compute_macd",
    "compute_sma",
    "IndicatorMeta",
    "IndicatorRole",
    "INDICATOR_META",
    "MacdSeries",
]
```

- [ ] **Step 2.6: Add INDICATOR_META["macd"] entry**

In `mctrader-engine/src/mctrader_engine/indicators/meta.py`, extend the dict:

```python
    "macd": IndicatorMeta(
        key="macd",
        display_name="MACD (Moving Average Convergence Divergence)",
        role="subplot",
        yaxis_label="MACD",
    ),
```

- [ ] **Step 2.7: Run MACD value tests to verify Green**

```
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -15
```

Expected: 15 passed (12 from before + 3 new MACD tests).

- [ ] **Step 2.8: Extend INDICATOR_FUNCS with MACD field adapters**

In `mctrader-engine/tests/indicators/test_lookahead_contract.py`:

```python
from mctrader_engine.indicators import compute_ema, compute_macd, compute_sma
```

Append to `INDICATOR_FUNCS`:

```python
    # MACD multi-output — one entry per field. Default params: fast=12, slow=26, signal=9.
    # MACD warmup = slow - 1 = 25.
    # Signal/Histogram warmup = slow + signal - 2 = 33.
    ("macd_field_macd",
     lambda c, **kw: compute_macd(c, **kw).macd,
     {"fast": 12, "slow": 26, "signal": 9},
     25),
    ("macd_field_signal",
     lambda c, **kw: compute_macd(c, **kw).signal,
     {"fast": 12, "slow": 26, "signal": 9},
     33),
    ("macd_field_histogram",
     lambda c, **kw: compute_macd(c, **kw).histogram,
     {"fast": 12, "slow": 26, "signal": 9},
     33),
```

NOTE: The contract suite uses 30-candle fixture (`_candles_long`). With default MACD params, signal/histogram warmup is at index 33 — past the fixture length. To keep the contract valid for default params, extend the fixture OR use shorter MACD params (`fast=2, slow=3, signal=2` → warmups 2 and 3). Use shorter params:

Replace the three append entries above with:

```python
    # MACD multi-output — short params so warmup falls within 30-candle fixture.
    # fast=2 slow=3 signal=2: macd warmup = 2, signal/histogram warmup = 3.
    ("macd_field_macd",
     lambda c, **kw: compute_macd(c, **kw).macd,
     {"fast": 2, "slow": 3, "signal": 2},
     2),
    ("macd_field_signal",
     lambda c, **kw: compute_macd(c, **kw).signal,
     {"fast": 2, "slow": 3, "signal": 2},
     3),
    ("macd_field_histogram",
     lambda c, **kw: compute_macd(c, **kw).histogram,
     {"fast": 2, "slow": 3, "signal": 2},
     3),
```

- [ ] **Step 2.9: Run contract suite**

```
uv run python -m pytest tests/indicators/test_lookahead_contract.py -v 2>&1 | tail -10
```

Expected: 45 passed (5 invariants × 9 entries — 6 SMA/EMA + 3 MACD fields).

- [ ] **Step 2.10: Add MACD perf gate**

In `mctrader-engine/tests/indicators/test_perf_budget.py`:

```python
from mctrader_engine.indicators import compute_ema, compute_macd, compute_sma
```

```python
def test_compute_macd_50k_bars_under_budget(long_candles) -> None:
    start = time.perf_counter()
    result = compute_macd(long_candles)
    elapsed = time.perf_counter() - start
    assert len(result.macd) == N_BARS
    assert elapsed < PERF_BUDGET_SEC, (
        f"compute_macd(default) on {N_BARS} bars took {elapsed*1000:.1f}ms "
        f"(budget {PERF_BUDGET_SEC*1000:.0f}ms). Likely algorithmic regression."
    )
```

- [ ] **Step 2.11: Run perf gate**

```
uv run python -m pytest tests/indicators/test_perf_budget.py -v 2>&1 | tail -10
```

Expected: 3 passed.

- [ ] **Step 2.12: Commit**

```
git add src/mctrader_engine/indicators/types.py src/mctrader_engine/indicators/trend.py src/mctrader_engine/indicators/__init__.py src/mctrader_engine/indicators/meta.py tests/indicators/test_trend.py tests/indicators/test_lookahead_contract.py tests/indicators/test_perf_budget.py
git commit -m "feat(indicators): MacdSeries NamedTuple + compute_macd + meta + contract + perf (MCT-90 Phase 2)"
```

---

## Task 3: DonchianChannels + compute_donchian end-to-end

Donchian = (max(high) over period bars, min(low) over period bars, midpoint). O(n) monotonic-deque rolling extrema. Period bars include the current bar (pandas / TA-Lib default). Turtle-style "exclude current bar" is a strategy-level decision and out of scope here.

**Files:** same set as Task 2.

- [ ] **Step 3.1: Add DonchianChannels NamedTuple**

In `mctrader-engine/src/mctrader_engine/indicators/types.py`, append:

```python
class DonchianChannels(NamedTuple):
    """Donchian Channels: rolling max(high), midpoint, min(low) over ``period`` bars.

    All three full-length ``list[Decimal | None]``; first non-None at index ``period - 1``.
    """

    upper: list[Decimal | None]
    middle: list[Decimal | None]
    lower: list[Decimal | None]
```

- [ ] **Step 3.2: Add Donchian value tests (TDD Red)**

In `mctrader-engine/tests/indicators/test_trend.py`:

```python
from mctrader_engine.indicators import DonchianChannels, MacdSeries, compute_donchian, compute_macd
```

Append:

```python
def test_compute_donchian_basic_period_3() -> None:
    # Use make_candles(closes=...): high = close + 100000, low = close - 100000.
    # period=3 over closes 100, 200, 300:
    #   upper[2] = max(100100, 200100, 300100) = 300100
    #   lower[2] = min(99900, 199900, 299900)  = 99900
    #   middle[2] = (300100 + 99900) / 2 = 200000
    candles = make_candles(closes=[Decimal(c) for c in (100, 200, 300)])
    result = compute_donchian(candles, period=3)
    assert isinstance(result, DonchianChannels)
    assert result.upper == [None, None, Decimal("300100")]
    assert result.lower == [None, None, Decimal("99900")]
    assert result.middle == [None, None, Decimal("200000")]


def test_compute_donchian_rolling_window() -> None:
    candles = make_candles(closes=[Decimal(c) for c in (100, 200, 300, 400, 500)])
    result = compute_donchian(candles, period=2)
    # Each candle: high = close + 100000, low = close - 100000.
    # idx 1: max(high[0:2]) = 200100, min(low[0:2]) = 99900
    # idx 2: max(high[1:3]) = 300100, min(low[1:3]) = 199900
    # idx 3: max(high[2:4]) = 400100, min(low[2:4]) = 299900
    # idx 4: max(high[3:5]) = 500100, min(low[3:5]) = 399900
    assert result.upper[0] is None
    assert result.upper[1] == Decimal("200100")
    assert result.upper[2] == Decimal("300100")
    assert result.upper[3] == Decimal("400100")
    assert result.upper[4] == Decimal("500100")
    assert result.lower[1] == Decimal("99900")
    assert result.lower[4] == Decimal("399900")


def test_compute_donchian_invalid_period_raises() -> None:
    candles = make_candles(closes=[Decimal("100")])
    with pytest.raises(ValueError):
        compute_donchian(candles, period=0)
    with pytest.raises(ValueError):
        compute_donchian(candles, period=-1)


def test_compute_donchian_empty_returns_empty_named_tuple() -> None:
    result = compute_donchian([], period=5)
    assert result.upper == []
    assert result.middle == []
    assert result.lower == []
```

- [ ] **Step 3.3: Run tests to verify Red**

```
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -10
```

Expected: import error.

- [ ] **Step 3.4: Implement compute_donchian (deque-based O(n))**

In `mctrader-engine/src/mctrader_engine/indicators/trend.py`:

```python
from collections import deque

from mctrader_engine.indicators.types import DonchianChannels, MacdSeries


def compute_donchian(
    candles: Sequence[CandleLike],
    *,
    period: int = 20,
) -> DonchianChannels:
    """Donchian Channels: rolling max(high) / min(low) over ``period`` bars.

    O(n) implementation using monotonic deques (Lee 1996). ``period`` includes
    the current bar — Turtle-style "exclude current bar" handling is a
    strategy-level decision (pass ``candles[:-1]`` or use ``t-1`` index in
    decision logic).
    """
    if period <= 0:
        raise ValueError(f"period={period} must be positive")

    n = len(candles)
    upper: list[Decimal | None] = [None] * n
    lower: list[Decimal | None] = [None] * n
    middle: list[Decimal | None] = [None] * n

    # Monotonic deques storing indices.
    max_dq: deque[int] = deque()  # decreasing high; front = arg-max
    min_dq: deque[int] = deque()  # increasing low; front = arg-min

    for i, candle in enumerate(candles):
        h = candle.high
        l = candle.low

        # Drop indices outside window.
        while max_dq and max_dq[0] <= i - period:
            max_dq.popleft()
        while min_dq and min_dq[0] <= i - period:
            min_dq.popleft()

        # Maintain monotonic property.
        while max_dq and candles[max_dq[-1]].high <= h:
            max_dq.pop()
        max_dq.append(i)

        while min_dq and candles[min_dq[-1]].low >= l:
            min_dq.pop()
        min_dq.append(i)

        if i + 1 < period:
            continue

        u = candles[max_dq[0]].high
        lo = candles[min_dq[0]].low
        upper[i] = u.quantize(_QUANTIZE_18)
        lower[i] = lo.quantize(_QUANTIZE_18)
        middle[i] = ((u + lo) / Decimal(2)).quantize(_QUANTIZE_18)

    return DonchianChannels(upper=upper, middle=middle, lower=lower)
```

- [ ] **Step 3.5: Re-export compute_donchian and DonchianChannels**

In `mctrader-engine/src/mctrader_engine/indicators/__init__.py`:

```python
from mctrader_engine.indicators.meta import INDICATOR_META
from mctrader_engine.indicators.trend import compute_donchian, compute_ema, compute_macd, compute_sma
from mctrader_engine.indicators.types import DonchianChannels, IndicatorMeta, IndicatorRole, MacdSeries

__all__ = [
    "compute_donchian",
    "compute_ema",
    "compute_macd",
    "compute_sma",
    "DonchianChannels",
    "IndicatorMeta",
    "IndicatorRole",
    "INDICATOR_META",
    "MacdSeries",
]
```

- [ ] **Step 3.6: Add INDICATOR_META["donchian"] entry**

In `mctrader-engine/src/mctrader_engine/indicators/meta.py`, extend:

```python
    "donchian": IndicatorMeta(
        key="donchian",
        display_name="Donchian Channels",
        role="overlay",
        yaxis_label=None,
    ),
```

- [ ] **Step 3.7: Run Donchian value tests to verify Green**

```
uv run python -m pytest tests/indicators/test_trend.py -v 2>&1 | tail -15
```

Expected: 19 passed (15 + 4 Donchian).

- [ ] **Step 3.8: Extend INDICATOR_FUNCS with Donchian field adapters**

In `mctrader-engine/tests/indicators/test_lookahead_contract.py`:

```python
from mctrader_engine.indicators import compute_donchian, compute_ema, compute_macd, compute_sma
```

Append to `INDICATOR_FUNCS`:

```python
    # Donchian multi-output — period=5, warmup at idx 4 (period - 1).
    ("donchian_field_upper",
     lambda c, **kw: compute_donchian(c, **kw).upper,
     {"period": 5},
     4),
    ("donchian_field_middle",
     lambda c, **kw: compute_donchian(c, **kw).middle,
     {"period": 5},
     4),
    ("donchian_field_lower",
     lambda c, **kw: compute_donchian(c, **kw).lower,
     {"period": 5},
     4),
```

- [ ] **Step 3.9: Run contract suite**

```
uv run python -m pytest tests/indicators/test_lookahead_contract.py -v 2>&1 | tail -10
```

Expected: 60 passed (5 invariants × 12 entries).

- [ ] **Step 3.10: Add Donchian perf gate**

In `mctrader-engine/tests/indicators/test_perf_budget.py`:

```python
from mctrader_engine.indicators import compute_donchian, compute_ema, compute_macd, compute_sma
```

```python
def test_compute_donchian_50k_bars_under_budget(long_candles) -> None:
    start = time.perf_counter()
    result = compute_donchian(long_candles, period=20)
    elapsed = time.perf_counter() - start
    assert len(result.upper) == N_BARS
    assert elapsed < PERF_BUDGET_SEC, (
        f"compute_donchian(period=20) on {N_BARS} bars took {elapsed*1000:.1f}ms "
        f"(budget {PERF_BUDGET_SEC*1000:.0f}ms). Likely algorithmic regression — "
        "naive max()/min() per window is O(n*period); use monotonic deque."
    )
```

- [ ] **Step 3.11: Run perf gate**

```
uv run python -m pytest tests/indicators/test_perf_budget.py -v 2>&1 | tail -10
```

Expected: 4 passed.

- [ ] **Step 3.12: Commit**

```
git add src/mctrader_engine/indicators/types.py src/mctrader_engine/indicators/trend.py src/mctrader_engine/indicators/__init__.py src/mctrader_engine/indicators/meta.py tests/indicators/test_trend.py tests/indicators/test_lookahead_contract.py tests/indicators/test_perf_budget.py
git commit -m "feat(indicators): DonchianChannels NamedTuple + compute_donchian deque-based + meta + contract + perf (MCT-90 Phase 2)"
```

---

## Task 4: Final regression + lint + push + PR + admin merge

- [ ] **Step 4.1: Run full pytest**

```
uv run python -m pytest 2>&1 | tail -5
```

Expected: all pass. Phase 1 baseline was 504 passed. Phase 2 adds:
- test_trend.py: +12 (5 EMA + 3 MACD + 4 Donchian) → total 19
- test_lookahead_contract.py: +45 (5 inv × 9 new entries: 3 EMA + 3 MACD-fields + 3 Donchian-fields) → total 60
- test_perf_budget.py: +3 (EMA / MACD / Donchian) → total 4
Net: ~+60 → 564 passed approx.

- [ ] **Step 4.2: Lint + type check**

```
uv run python -m ruff check src/mctrader_engine/indicators tests/indicators
uv run python -m pyright src/mctrader_engine/indicators tests/indicators
```

Expected: no errors.

- [ ] **Step 4.3: Push branch + create PR**

```
git push -u origin feat/mct-90-phase-2-trend-indicators
```

Then `gh pr create --base main --title "[MCT-90] feat(indicators): Phase 2 — EMA + MACD + Donchian trend indicators" --body "..."` with body referencing this plan + spec, and listing the test counts.

- [ ] **Step 4.4: Add phase + gate labels to PR**

(Labels were created on the repo during Phase 1.)

```
gh pr edit <PR-NUM> --add-label "phase:보안-테스트" --add-label "gate:security-test-pass"
```

- [ ] **Step 4.5: Watch CI to terminal state**

```
gh pr checks <PR-NUM> --watch
```

If any check is FAILURE / ACTION_REQUIRED / BLOCKED: classify, fix, push.

- [ ] **Step 4.6: Admin merge once green**

```
gh pr merge <PR-NUM> --admin --squash --delete-branch
```

Then:

```
git checkout main
git pull --ff-only
```

---

## Acceptance criteria for Phase 2

- [ ] `compute_ema(candles, period=N)` — textbook alpha = 2/(N+1), SMA-seeded, leading None warmup of length `N - 1`. Boundary 18-place quantize.
- [ ] `compute_macd(candles, fast=12, slow=26, signal=9)` — returns `MacdSeries(macd, signal, histogram)`. Warmup boundaries: macd at `slow - 1`, signal/histogram at `slow + signal - 2`. Codex risk-1 guard: warmup-boundary value tests.
- [ ] `compute_donchian(candles, period=20)` — returns `DonchianChannels(upper, middle, lower)`. O(n) deque. Boundary 18-place quantize.
- [ ] `INDICATOR_META` has 4 entries: sma + ema (overlay) + macd (subplot, "MACD") + donchian (overlay).
- [ ] `INDICATOR_FUNCS` has 12 entries: 3 SMA + 3 EMA + 3 MACD-fields + 3 Donchian-fields. All 5 invariants pass per entry → 60 contract tests.
- [ ] `test_perf_budget.py` has 4 gates (one per indicator) all passing < 500ms.
- [ ] No mctrader-engine version bump (stays 0.29.0).
- [ ] No SmaStrategy or any strategy file touched.
- [ ] No new runtime dependencies (no TA-Lib, no pandas-ta).

## Hand-off to Phase 3

Phase 3 (mean-reversion indicators — RSI, Bollinger Bands, z-score, Stochastic, Williams %R) reuses:
- `_ema_values` helper for any RSI variant that uses EMA-style smoothing.
- The `INDICATOR_FUNCS` lambda-adapter pattern for multi-output (Bollinger has 3 fields, Stochastic has 2).
- Wilder smoothing helper will land here (RSI default uses Wilder; ATR in phase 4 also uses Wilder).
- New NamedTuples in `types.py`: `BollingerBands`, `StochasticSeries`.
