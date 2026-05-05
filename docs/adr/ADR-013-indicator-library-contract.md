---
adr_id: ADR-013
title: Technical indicator library contract — Decimal precision, lookahead safety, metadata
status: Accepted
date: 2026-05-05
related_story: MCT-90
category: backtest
---

# ADR-013: Indicator library contract

## Status

Accepted — 2026-05-05. MCT-90 Phase 7.

## Context

MCT-90 introduced `mctrader_engine.indicators` — a Decimal-precision pure-function library used by all candle strategies. The contract has invariants enforced at multiple levels (function signatures, parametrized property tests, perf gates). This ADR canonicalizes the contract so future indicators (Ichimoku, SuperTrend, ADX, etc.) extend it consistently rather than diverging.

## Decision

### D1. Public API shape

- All indicators are pure module-level functions in `mctrader_engine.indicators.<module>` and re-exported from `mctrader_engine.indicators` (flat namespace).
- Single-output: `compute_<name>(candles: Sequence[CandleLike], *, ...params) -> list[Decimal | None]`.
- Multi-output: `compute_<name>(...) -> NamedTuple` defined in `mctrader_engine.indicators.types`. Each field is a `list[Decimal | None]`.
- Length invariant: `len(output) == len(candles)`. No padding, no trimming.
- Warmup: leading entries are `None` until the indicator's parameter requirements are met. The exact warmup count is documented per-indicator and asserted in the contract test.
- Empty input: `compute_<name>([], ...)` returns an empty list (or NamedTuple with empty lists).

### D2. Decimal precision

- All indicators use `Decimal` arithmetic. **No `float`** in runtime code.
- Internal accumulators (rolling sum, EMA recurrence, Wilder smoothing) stay raw `Decimal` to avoid recursive rounding drift.
- Output values are quantized to 18 decimal places at the boundary via `_QUANTIZE_18 = Decimal("1.000000000000000000")`.

### D3. Lookahead safety

The library is **context-agnostic**. The caller is responsible for passing a lookahead-safe sequence (typically `StrategyContext.visible_window(...)` per ADR-005 L2).

The library guarantees:
- **Prefix-stable**: `compute_X(candles[:k])[-1] == compute_X(candles)[k-1]` for all valid `k`. This is the core no-future-leakage invariant, enforced by `tests/indicators/test_lookahead_contract.py::test_prefix_stable`.
- **No input mutation**: input `candles` is not modified.

The library does **not** guarantee:
- **Suffix stability**: recursive indicators (EMA, Wilder smoothing, ATR, MACD, etc.) computed on a suffix differ from the same indicator on a prefix because the seed point shifts. Strategies that use recursive indicators must request a sufficiently large `visible_window(N)` so the suffix's seed is far enough back that its contribution to the current value has decayed (rule of thumb: `N = 10 * period`).

### D4. Metadata registry (`INDICATOR_META`)

Every indicator registers an `IndicatorMeta(key, display_name, role, yaxis_label)` entry in `INDICATOR_META`. `role` is `"overlay"` (renders on price axis) or `"subplot"` (separate panel). `yaxis_label` is the subplot's label or `None` for overlays.

The metadata is consumed by:
- `mctrader-cli indicator list` for discovery (Phase 7).
- `mctrader-web` overlay/subplot dispatch (follow-up Epic).

### D5. Contract test parametrization

`tests/indicators/test_lookahead_contract.py::INDICATOR_FUNCS` is a single source of truth. Adding a new single-output indicator: append one entry. Multi-output: append one entry per field (lambda adapter). Five invariants run automatically:

1. prefix-stable
2. length matches input
3. warmup leading None matches declared count
4. all non-None entries are `Decimal`
5. no input mutation (open/high/low/close/volume snapshot)

### D6. Performance budget

Each indicator must compute 50,000 bars in under 500ms on developer hardware. Tests in `tests/indicators/test_perf_budget.py`. The budget catches algorithmic regressions (e.g., naive O(n*period) rolling extrema) — it is intentionally generous to absorb CI runner variance.

### D7. External library policy

No `TA-Lib`, `pandas-ta`, `pandas`, or `numpy` in **runtime** code (D2 invariant). Optional cross-validation against external libraries may live in `[indicators-xv]` uv extras for developer-only sanity checks; CI does not exercise them.

### D8. Wilder vs textbook EMA

- Textbook EMA (`alpha = 2 / (period + 1)`): exposed via `compute_ema`. Used by MACD, Keltner middle, etc.
- Wilder smoothing (`alpha = 1 / period`): exposed via private `_wilder_values` helper. Used by RSI and ATR. Not a public API — RSI/ATR own their seeding logic.
- These are semantically different algorithms; do not parameterize them into a single function.

### D9. IndicatorProvider Protocol

Strategies that ship in this Epic implement `compute_indicators(candles) -> dict[str, list[Decimal | None]]` (Phase 2B Protocol) by delegating to the library. T2/T3 templates (market_making_v1 / tick_scalping_v1 / book_imbalance_breakout_v1) are exempt — their callbacks operate on book/tick events, not candle series, so there is no canonical indicator series to export.

## Consequences

### Positive

- One contract test fixture covers any new indicator.
- Decimal precision invariant eliminates an entire class of float-rounding bugs visible only in production.
- Metadata registry decouples the engine from web visualization: web Epic just consumes `INDICATOR_META` without engine knowing about Plotly.
- Naming + module conventions make the library predictable to extend.

### Negative

- No `numpy`/`pandas` means slower than typical Python charting libraries on huge datasets. Benchmarked at ~50ms for 50k-bar SMA — acceptable for backtesting, may need C extensions if we ever do live tick-level indicator computation at 1M+ events/sec.
- Recursive indicators (EMA, Wilder) require strategy callers to request large `visible_window` for accuracy. This is documented per-strategy but is a sharp edge for new strategy authors.

### Mitigations

- Future "indicator-cython" or "indicator-rust" extension (out of scope MCT-90) if perf becomes a bottleneck.
- `compute_ema` / `compute_macd` / `compute_atr` / `_wilder_values` docstrings explicitly note the caller's responsibility to size `visible_window` for convergence.

## References

- Spec: `docs/superpowers/specs/2026-05-05-indicator-library-and-strategy-templates-design.md`
- ADR-005 (lookahead verification, L2 contract)
- ADR-006 (WFO promotion gate — applies to all candle strategies in this Epic)
- MCT-68 — T2/T3 template precedent
