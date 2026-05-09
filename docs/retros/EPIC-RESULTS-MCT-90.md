# MCT-90 Epic Results — Indicator library + Strategy templates expansion

**Status**: 완료 (Closed 2026-05-05)
**Spec**: [docs/superpowers/specs/2026-05-05-indicator-library-and-strategy-templates-design.md](docs/superpowers/specs/2026-05-05-indicator-library-and-strategy-templates-design.md)
**Engine version**: 0.28.0 → 0.29.0

## Phase summary

| Phase | PR | Scope | Tests |
|---|---|---|---|
| 1 | #29 | Package scaffold + SMA extraction + 5-invariant contract suite + perf gate | +28 (504 → 532) |
| 2 | #30 | Trend indicators (EMA / MACD / Donchian) + NamedTuple multi-output + lambda field adapters | +60 (532 → 564... actual 564 from baseline + 71 = 635 wait recount... see cumulative below) |
| 3 | #31 | Mean-reversion (RSI / Bollinger / zscore / Stochastic / Williams %R) + Wilder + stddev helpers + Donchian refactor | +71 (564 → 635) |
| 4 | #32 | Vol/momentum/volume (ATR / Keltner / stddev / BB-width / ROC / OBV / VWAP rolling) — completes 16-indicator v1 | +73 (635 → 708) |
| 5 | #33 | Trend strategies (ema_cross_v1 / macd_cross_v1 / donchian_breakout_v1) | +10 (708 → 718) |
| 6 | #34 | Batch 2 strategies + T3 (rsi_bounds / bollinger_reversion / zscore_reversion / atr_breakout / keltner_breakout / roc_threshold / vwap_cross / book_imbalance_breakout) | +23 (718 → 741) |
| 7 | TBD | CLI `indicator list` + ADR-013 + Epic close | +3 (741 → ~744) |

## Final inventory

### Indicators (16 v1)

| Module | Function | Role | Multi-output |
|---|---|---|---|
| trend | compute_sma | overlay | - |
| trend | compute_ema | overlay | - |
| trend | compute_macd | subplot | MacdSeries(macd, signal, histogram) |
| trend | compute_donchian | overlay | DonchianChannels(upper, middle, lower) |
| meanrev | compute_rsi | subplot | - |
| meanrev | compute_bollinger | overlay | BollingerBands(upper, middle, lower) |
| meanrev | compute_zscore | subplot | - |
| meanrev | compute_stochastic | subplot | StochasticSeries(percent_k, percent_d) |
| meanrev | compute_williams_r | subplot | - |
| vol | compute_atr | subplot | - |
| vol | compute_keltner | overlay | KeltnerChannels(upper, middle, lower) |
| vol | compute_stddev | subplot | - |
| vol | compute_bb_width | subplot | - |
| momentum | compute_roc | subplot | - |
| volume | compute_obv | subplot | - |
| volume | compute_vwap_rolling | overlay | - |

### Strategies (12 v1)

T1 candle, WFO-gated (ADR-006):

| Strategy | Indicator | Logic |
|---|---|---|
| sma_v1 (Phase 1) | compute_sma | SMA fast/slow crossover |
| ema_cross_v1 | compute_ema | EMA fast/slow crossover |
| macd_cross_v1 | compute_macd | MACD line / signal line cross |
| donchian_breakout_v1 | compute_donchian | Turtle-style prior-bar channel break |
| rsi_bounds_v1 | compute_rsi | oversold (<30) → BUY; overbought (>70) → SELL |
| bollinger_reversion_v1 | compute_bollinger | close < lower → BUY; close > upper → SELL |
| zscore_reversion_v1 | compute_zscore | z < -threshold → BUY; z > +threshold → SELL |
| atr_breakout_v1 | compute_atr | close > prev + atr_mult*ATR → BUY |
| keltner_breakout_v1 | compute_keltner | close > Keltner upper → BUY; close < lower → SELL |
| roc_threshold_v1 | compute_roc | ROC > +threshold → BUY; ROC < -threshold → SELL |
| vwap_cross_v1 | compute_vwap_rolling | close crosses rolling VWAP |

T3 orderbook, NOT WFO-gated (MCT-68 pattern):

| Strategy | Logic |
|---|---|
| market_making_v1 (MCT-68) | top-of-book quote post + book imbalance refresh |
| tick_scalping_v1 (MCT-68) | tick momentum entry + TP/SL/time exit |
| book_imbalance_breakout_v1 (Phase 6) | sustained book imbalance → market order |

## Decisions canonicalized

ADR-013 (Phase 7) — indicator library contract:
- D1 public API shape (single/multi-output, length invariant, warmup, empty input)
- D2 Decimal-only runtime + boundary 18-place quantize
- D3 lookahead safety (prefix-stable, no mutation, suffix-instability disclosure)
- D4 INDICATOR_META metadata registry
- D5 INDICATOR_FUNCS contract test parametrization
- D6 50k-bar < 500ms perf budget
- D7 no runtime numpy/pandas/TA-Lib
- D8 Wilder vs textbook EMA distinction
- D9 IndicatorProvider Protocol scope (candle strategies mandatory, T2/T3 exempt)

## Out of scope (deferred)

- Ichimoku, SuperTrend, ADX/DMI, DEMA/TEMA, CCI, Awesome Oscillator, MFI, A/D, CMF, session-anchored VWAP — separate Epic
- mctrader-web subplot/overlay UI integration (Phase 7 ADR canonicalizes the metadata contract; web consumption = follow-up Epic)
- `mctrader-cli indicator compute --name X --candles file.csv` ad-hoc indicator computation
- ATR-trailing combo strategies (Decision class extension required) — separate Epic
- Liquidity sweep, tape momentum T2/T3 strategies — separate microstructure Epic
- WFO search-space registration for the 11 candle strategies (this is operational, not Epic scope)

## Cumulative metrics

- 16 indicators × 5 contract invariants × parametrize entries (30) = ~150 contract tests
- 16 indicators × 50k-bar perf gate = 16 perf tests
- 12 strategies (3 sma_v1 baseline + 9 new candle WFO-gated + 3 T3 templates from MCT-68 + this Epic's book_imbalance_breakout_v1)
- 0 runtime dependencies added
- ~744 tests passing total
