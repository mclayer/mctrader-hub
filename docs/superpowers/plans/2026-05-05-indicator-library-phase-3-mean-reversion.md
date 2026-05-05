# Indicator library Phase 3 — Mean-reversion (RSI, Bollinger, z-score, Stochastic, Williams %R)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Add 5 mean-reversion indicators on top of Phase 1+2 scaffold. Introduces 2 new internal helpers (`_wilder_values`, `_stddev_values`) and 1 refactor (`_rolling_max_min` extracted from compute_donchian, reused by Stochastic + Williams). All 5 invariants pass per output field; all 5 indicators meet 50k-bar < 500ms perf budget.

**Architecture:**
- `_wilder_values(values, *, period)` — Wilder smoothing alpha=1/period, used by RSI here and ATR in Phase 4.
- `_stddev_values(values, *, period)` — population std-dev via rolling sum + rolling sum-of-squares (`var = E[X²] - E[X]²`). Used by Bollinger + zscore here, std-dev + BB-width in Phase 4.
- `_rolling_max_min(candles, *, period)` — monotonic-deque tuple `(upper, lower)` extracted from compute_donchian. Reused by compute_donchian, compute_stochastic, compute_williams_r.
- All indicators stay in `mctrader_engine.indicators.meanrev` (new module).
- 2 new NamedTuples: `BollingerBands(upper, middle, lower)`, `StochasticSeries(percent_k, percent_d)`.
- 5 INDICATOR_META entries: rsi=subplot/RSI, bollinger=overlay, zscore=subplot/z-score, stochastic=subplot/Stochastic, williams_r=subplot/%R.
- INDICATOR_FUNCS goes 12 → 20 entries (8 new = 1 RSI + 3 Bollinger fields + 1 zscore + 2 Stochastic fields + 1 Williams). 5 invariants × 20 = 100 contract tests.
- Per-indicator perf gate (50k-bar < 500ms) — 5 new tests.

**Branch:** `feat/mct-90-phase-3-mean-reversion`. No version bump (stays 0.29.0).

## File map
- Create: `mctrader-engine/src/mctrader_engine/indicators/meanrev.py`
- Modify: `mctrader-engine/src/mctrader_engine/indicators/trend.py` (extract `_rolling_max_min`, refactor compute_donchian)
- Modify: `mctrader-engine/src/mctrader_engine/indicators/__init__.py` (re-exports)
- Modify: `mctrader-engine/src/mctrader_engine/indicators/types.py` (BollingerBands, StochasticSeries)
- Modify: `mctrader-engine/src/mctrader_engine/indicators/meta.py` (5 entries)
- Create: `mctrader-engine/tests/indicators/test_meanrev.py`
- Modify: `mctrader-engine/tests/indicators/test_lookahead_contract.py` (8 new INDICATOR_FUNCS entries)
- Modify: `mctrader-engine/tests/indicators/test_perf_budget.py` (5 new gates)

## Tasks

### Task 1 — Refactor compute_donchian to use _rolling_max_min helper
- Extract deque logic to `_rolling_max_min(candles, *, period) -> tuple[list[Decimal | None], list[Decimal | None]]`.
- compute_donchian becomes 4-line wrapper: call helper, build middle, return DonchianChannels.
- Regression: existing Donchian tests stay green.
- Commit: "refactor(indicators): extract _rolling_max_min helper from compute_donchian".

### Task 2 — _stddev_values + _wilder_values helpers (TDD)
- _wilder_values: alpha=1/period, SMA seed at idx=period-1.
- _stddev_values: rolling sum + rolling sum-of-squares, population variance (ddof=0). Boundary 18-place quantize. Edge: variance < 0 due to rounding → clamp to 0.
- Add internal helper unit tests (verify against hand-computed values for short series).
- Commit: "feat(indicators): _wilder_values + _stddev_values internal helpers".

### Task 3 — compute_rsi end-to-end (TDD)
- closes [10,12,11,13] period=2 fixture: avg_gain=1, avg_loss=0.5, RS=2, RSI=66.666... → quantized.
- Edge: avg_loss=0 → RSI=100. avg_gain=0 → RSI=0.
- Warmup = `period` (RSI[period] is first non-None — see decision B).
- meanrev.py module + INDICATOR_META["rsi"] + INDICATOR_FUNCS entry + perf gate.
- Commit: "feat(indicators): compute_rsi (Wilder smoothing) + meanrev module + meta + contract + perf".

### Task 4 — BollingerBands + compute_bollinger end-to-end (TDD)
- middle=SMA(period), upper=middle + num_std*stddev, lower=middle - num_std*stddev.
- BollingerBands NamedTuple in types.py.
- INDICATOR_META["bollinger"] (overlay).
- 3 field adapters in INDICATOR_FUNCS.
- Perf gate.
- Commit: "feat(indicators): BollingerBands + compute_bollinger + meta + contract + perf".

### Task 5 — compute_zscore end-to-end (TDD)
- z[t] = (close[t] - SMA[t]) / stddev[t]. Edge: stddev=0 → z=0.
- Single-output; INDICATOR_META["zscore"] (subplot).
- 1 INDICATOR_FUNCS entry.
- Perf gate.
- Commit: "feat(indicators): compute_zscore + meta + contract + perf".

### Task 6 — StochasticSeries + compute_stochastic end-to-end (TDD)
- %K = 100 * (close - lo) / (hi - lo); %D = SMA(%K, d_period).
- Reuse _rolling_max_min for hi/lo.
- Edge: hi==lo → %K=50.
- Warmup: %K at k_period-1; %D at k_period+d_period-2.
- StochasticSeries NamedTuple.
- INDICATOR_META["stochastic"] (subplot).
- 2 field adapters in INDICATOR_FUNCS.
- Perf gate.
- Commit: "feat(indicators): StochasticSeries + compute_stochastic + meta + contract + perf".

### Task 7 — compute_williams_r end-to-end (TDD)
- %R = -100 * (hi - close) / (hi - lo).
- Reuse _rolling_max_min.
- Edge: hi==lo → %R=-50.
- Single-output.
- INDICATOR_META["williams_r"] (subplot, "%R").
- 1 INDICATOR_FUNCS entry.
- Perf gate.
- Commit: "feat(indicators): compute_williams_r + meta + contract + perf".

### Task 8 — Final regression + lint + push + PR + admin merge
- `uv run python -m pytest`: ~624 tests (Phase 2 baseline 564 + 60 new = 40 contract + 5 perf + ~15 value tests).
- ruff + pyright clean.
- gh pr create + label + watch CI + admin merge.

## Acceptance criteria
- 5 indicators public, all in `mctrader_engine.indicators.meanrev` module re-exported from `__init__.py`.
- INDICATOR_META = 9 entries (sma/ema/macd/donchian/rsi/bollinger/zscore/stochastic/williams_r).
- INDICATOR_FUNCS = 20 entries; contract suite green = 100 tests.
- Each indicator 50k-bar < 500ms.
- Donchian regression — existing tests green after _rolling_max_min refactor.
- No mctrader-engine version bump.
- No strategy or Decision changes.

## Hand-off to Phase 4
- _wilder_values reused by ATR.
- _stddev_values reused by std-dev / BB-width.
- _rolling_max_min reused by Keltner channels (uses ATR-derived band, not max/min, so actually only Donchian/Stochastic/Williams keep using it).
- New module `vol.py` for ATR/Keltner/std-dev/BB-width, `momentum.py` for ROC, `volume.py` for OBV/VWAP-rolling.
