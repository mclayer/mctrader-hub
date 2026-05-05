---
spec_id: 2026-05-05-indicator-library-and-strategy-templates
title: Technical indicator library + strategy templates expansion (MCT-90)
status: Draft
date: 2026-05-05
related_adrs: ADR-002, ADR-003, ADR-005, ADR-006
related_stories: MCT-90 (Epic), MCT-64, MCT-68, sma_v1 (existing)
component: mctrader-engine
version_target: 0.29.0
---

# Technical indicator library + strategy templates expansion

## 1. 사용자 요구사항 (verbatim)

> "지금 너가 보유하고 있는 전략은 어떤 것들이 있ㄴ"
> "이외에 추가할만한 다른 지표들을 마련해달라."

사용자 의도 명확화 (multi-choice batch):
- Q1: **c** — indicator library + strategy 둘 다
- Q2: **t1+** — T1 candle (WFO-gated) + 일부 T2/T3 (WFO 비대상)
- Q3: **all** — 모든 카테고리 (trend / mean-rev / vol / momentum / volume)
- Q4: **h** — hybrid (core 직접 구현, 외부 lib 는 보조)
- Q5: **big** — 단일 Epic 하 multi child stories

## 2. 도메인 해석

현재 mctrader-engine 의 strategy 는 3개:
- `sma_v1` (T1 candle, WFO-gated)
- `market_making_v1` (T3 orderbook, NOT WFO-gated, MCT-68)
- `tick_scalping_v1` (T2 tick + T3 orderbook, NOT WFO-gated, MCT-68)

**Gap**: standalone technical indicator library 부재. SMA 도 strategy 내부에 inline. RSI/MACD/Bollinger/ATR/Stochastic 등 표준 기술지표 전무. Trend / mean-reversion / volatility / momentum / volume 카테고리별 strategy template 부족 → 사용자가 production 전략 작성 시 starting point 가 sma_v1 하나 + T2/T3 template 2개뿐.

**This Epic**: indicator library 신설 + 그 위에 candle strategy 10종 + T3 strategy 1종 추가.

## 3. 관련 ADR

- **ADR-002 D2** — Strategy callback API 가 backtest/paper/live 모두 동일. 신규 strategy 모두 동일 invariant.
- **ADR-003 H8** — strategy callback per-bar 결정성. 신규 strategy 도 동일.
- **ADR-005 L2/L4** — lookahead 안전성. Indicator 함수는 sequence in/list out. caller 가 `visible_window` 만 전달 의무. L4 known-bias fixture per strategy family.
- **ADR-006** — WFO promotion gate. 신규 candle strategy 전부 default 적용. T3 strategy `book_imbalance_breakout_v1` 비대상 (MCT-68 패턴).
- **신규 ADR** (선택, MCT-90 phase 7): indicator library 의 Decimal/lookahead/메타데이터 contract 명시.

## 4. 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── indicators/                          # NEW
│   ├── __init__.py                      # public re-exports + INDICATOR_META
│   ├── trend.py                         # compute_sma, compute_ema, compute_macd, compute_donchian
│   ├── meanrev.py                       # compute_rsi, compute_bollinger, compute_zscore,
│   │                                    # compute_stochastic, compute_williams_r
│   ├── volatility.py                    # compute_atr, compute_keltner,
│   │                                    # compute_stddev, compute_bb_width
│   ├── momentum.py                      # compute_roc
│   ├── volume.py                        # compute_obv, compute_vwap_rolling
│   ├── types.py                         # MacdSeries, BollingerBands, StochasticSeries,
│   │                                    # KeltnerChannels, DonchianChannels NamedTuples
│   └── meta.py                          # IndicatorMeta dataclass + INDICATOR_META dict
│
├── strategy/
│   ├── sma.py                           # MODIFIED — internal SMA → indicators.compute_sma
│   ├── ema_cross.py                     # NEW
│   ├── macd_cross.py                    # NEW
│   ├── donchian_breakout.py             # NEW
│   ├── rsi_bounds.py                    # NEW
│   ├── bollinger_reversion.py           # NEW
│   ├── zscore_reversion.py              # NEW
│   ├── atr_breakout.py                  # NEW
│   ├── keltner_breakout.py              # NEW
│   ├── roc_threshold.py                 # NEW
│   ├── vwap_cross.py                    # NEW
│   └── templates/
│       └── book_imbalance_breakout.py   # NEW (T3, NOT WFO-gated)
│
└── cli.py                               # MODIFIED — add `indicator list` subcommand

mctrader-engine/tests/
├── indicators/                          # NEW
│   ├── test_trend.py
│   ├── test_meanrev.py
│   ├── test_volatility.py
│   ├── test_momentum.py
│   ├── test_volume.py
│   ├── test_lookahead_contract.py       # property tests: monotonic, warmup None, no mutation
│   └── fixtures/
│       └── golden_<indicator>.csv       # hand-computed reference values
├── strategy/
│   ├── test_ema_cross.py                # SMA pattern: warmup HOLD / BUY / SELL / lookahead
│   ├── test_macd_cross.py
│   ├── test_donchian_breakout.py
│   ├── test_rsi_bounds.py
│   ├── test_bollinger_reversion.py
│   ├── test_zscore_reversion.py
│   ├── test_atr_breakout.py
│   ├── test_keltner_breakout.py
│   ├── test_roc_threshold.py
│   ├── test_vwap_cross.py
│   └── templates/test_book_imbalance_breakout.py
├── lookahead/fixtures/                  # NEW per-family known-bias fixtures
│   ├── known_bias_macd_future_signal.py
│   ├── known_bias_rsi_future_close.py
│   ├── known_bias_atr_future_high.py
│   └── known_bias_vwap_future_volume.py
└── helpers.py                           # EXTENDED — make_candles_rising / falling / choppy /
                                         # spike / regime_change / btc_like_synthetic
```

## 5. 요구사항

### 5.1 Indicator library

**API contract**:
- 모든 함수 module-level pure function: `compute_<name>(candles: Sequence[CandleLike], **params) -> list[Decimal | None] | <NamedTuple>`
- Multi-output → typed NamedTuple (mypy/autocomplete 우선; `dict[str, list]` 거부)
- 단일출력 indicator → `list[Decimal | None]`, length == `len(candles)`, warmup 구간 leading None
- Decimal 18-place quantize 는 **결과 boundary 에만**. 내부 누적은 raw Decimal (recursive EMA/MACD/ATR rounding drift 방지)
- Caller 가 lookahead-safe sequence 전달 책임. 함수 자체는 context-aware 하지 않음. Library docstring 에 명시.

**Indicator 16종 (v1)**:

| Module | Function | 출력 | Params |
|---|---|---|---|
| trend | `compute_sma` | `list[Decimal\|None]` | period |
| trend | `compute_ema` | `list[Decimal\|None]` | period |
| trend | `compute_macd` | `MacdSeries(macd, signal, histogram)` | fast=12, slow=26, signal=9 |
| trend | `compute_donchian` | `DonchianChannels(upper, middle, lower)` | period=20 |
| meanrev | `compute_rsi` | `list[Decimal\|None]` | period=14 |
| meanrev | `compute_bollinger` | `BollingerBands(upper, middle, lower)` | period=20, num_std=2 |
| meanrev | `compute_zscore` | `list[Decimal\|None]` | period=20 |
| meanrev | `compute_stochastic` | `StochasticSeries(percent_k, percent_d)` | k_period=14, d_period=3 |
| meanrev | `compute_williams_r` | `list[Decimal\|None]` | period=14 |
| vol | `compute_atr` | `list[Decimal\|None]` | period=14 |
| vol | `compute_keltner` | `KeltnerChannels(upper, middle, lower)` | period=20, atr_mult=2 |
| vol | `compute_stddev` | `list[Decimal\|None]` | period=20 |
| vol | `compute_bb_width` | `list[Decimal\|None]` | period=20, num_std=2 |
| momentum | `compute_roc` | `list[Decimal\|None]` | period=10 |
| volume | `compute_obv` | `list[Decimal\|None]` | (none) |
| volume | `compute_vwap_rolling` | `list[Decimal\|None]` | period=20 |

**Defer to v2**: Ichimoku, SuperTrend, ADX/DMI, DEMA/TEMA, CCI, AO, MFI, A/D, CMF, session-anchored VWAP.

**INDICATOR_META** ([meta.py](mctrader-engine/src/mctrader_engine/indicators/meta.py)):
```python
@dataclass(frozen=True, slots=True)
class IndicatorMeta:
    key: str                # e.g., "rsi"
    display_name: str       # e.g., "RSI (Relative Strength Index)"
    role: Literal["overlay", "subplot"]   # overlay = on price axis; subplot = separate panel
    yaxis_label: str | None # e.g., "RSI" for subplot, None for overlay

INDICATOR_META: Final[dict[str, IndicatorMeta]] = { ... }
```
**Role 분류**:
- overlay: SMA, EMA, MACD signal-on-price (no — MACD is subplot), Donchian, Bollinger, Keltner, VWAP
- subplot: MACD, RSI, z-score, Stochastic, Williams%R, ATR, std-dev, BB-width, ROC, OBV

`mctrader-web` Phase 2C+ 가 metadata 소비 → Plotly subplot vs overlay 자동 dispatch (이번 Epic 에서는 metadata 만 노출, web 통합은 후속 Epic).

### 5.2 Strategy 11종 (v1)

모든 candle strategy:
- `@register_strategy("<name>_v1")`
- `REQUIRED_DATA_TIERS: ClassVar[frozenset[DataTier]] = frozenset({DataTier.CANDLE})`
- `on_bar(ctx) -> Decision` (Strategy Protocol)
- `compute_indicators(candles)` 의무 구현 (IndicatorProvider, mctrader-web overlay/subplot 용)
- 사이징: `cash * sizing_pct / current_close` quantize 18 decimals ROUND_DOWN (sma_v1 패턴)
- ADR-006 WFO promotion gate **적용**

| Strategy | Tier | Indicator 사용 | 진입/청산 logic |
|---|---|---|---|
| `ema_cross_v1` | T1 | compute_ema | EMA(fast) crosses above/below EMA(slow) |
| `macd_cross_v1` | T1 | compute_macd | MACD line crosses signal line |
| `donchian_breakout_v1` | T1 | compute_donchian | close > upper(N) → BUY; close < lower(N) → SELL |
| `rsi_bounds_v1` | T1 | compute_rsi | RSI < oversold → BUY; RSI > overbought → SELL |
| `bollinger_reversion_v1` | T1 | compute_bollinger | close < lower → BUY; close > upper → SELL |
| `zscore_reversion_v1` | T1 | compute_zscore | z < -threshold → BUY; z > +threshold → SELL |
| `atr_breakout_v1` | T1 | compute_atr | close > prev_close + atr_mult*ATR → BUY (장기 trend-follow) |
| `keltner_breakout_v1` | T1 | compute_keltner | close > upper → BUY; close < lower → SELL |
| `roc_threshold_v1` | T1 | compute_roc | ROC > +threshold → BUY; ROC < -threshold → SELL |
| `vwap_cross_v1` | T1 | compute_vwap_rolling | close crosses VWAP (rolling N) |
| `book_imbalance_breakout_v1` | T3 (orderbook) | (no indicator lib — direct book state) | imbalance > threshold + sustained N events → submit market |

**T3 strategy 는 WFO 비적용** (MCT-68 패턴). docstring 명시.

**Decision class 불변**: BUY / SELL / HOLD + `target_quantity` only. Stop-loss/TP/trailing 등은 strategy 내부 state 또는 별도 risk/ 모듈 책임 — 이번 Epic 에서 schema 확장 없음. (ATR-trailing combo strategy = v2 candidate.)

### 5.3 Test patterns

**Indicator library**:
- Hand-computed fixture: 단순 indicator (SMA, EMA, RSI, ROC, ATR) — test 파일 내 직접 expected list 명시
- Golden CSV fixture: multi-output indicator (MACD, Bollinger, Stochastic, Keltner, Donchian) — `tests/indicators/fixtures/golden_<indicator>.csv` 에 (input candles, expected outputs) 저장
- Property tests (`test_lookahead_contract.py`):
  - `len(output) == len(input)`
  - warmup 구간 모두 None
  - 모든 non-None value 가 `Decimal` 인스턴스
  - input mutation 없음 (deep-copy 비교)
  - **lookahead invariant**: `compute_X(candles[:k])[-1] == compute_X(candles)[k-1]` (prefix-stable)
- Optional cross-validation: TA-Lib / pandas-ta 결과와 비교 — `[indicators-xv]` uv extras 에 두고 CI 에서 비활성, dev 가 수동 실행. **Runtime 의존 금지**.

**Strategy**:
- SMA pattern 따라 (`tests/test_sma_strategy.py` 참조):
  - warmup 동안 HOLD
  - rising series → BUY trigger
  - falling series → SELL trigger
  - `_RecordingCtx` 로 `visible_window` 호출 invariant
  - invalid params → ValueError
- ADR-005 L4 known-bias fixture: per strategy **family** (trend / mean-rev / vol / volume), 모든 strategy 마다 1개씩은 아님

**Test data fixtures** (`tests/helpers.py` 확장):
- `make_candles_rising(n, start, step)`
- `make_candles_falling(n, start, step)`
- `make_candles_flat(n, level)`
- `make_candles_choppy(n, base, amplitude, period)`
- `make_candles_spike(n, base, spike_idx, magnitude)`
- `make_candles_regime_change(n, regime_break_idx, ...)`
- `make_candles_btc_like_synthetic(n, seed)` — 결정론적 random walk + volatility cluster
- 기존 `make_candles(closes=[...])` 유지

### 5.4 CLI surface

`mctrader-cli indicator list` 신규 — registry-style 출력:
```
$ mctrader-cli indicator list
NAME              MODULE   ROLE     OUTPUTS
sma               trend    overlay  [value]
ema               trend    overlay  [value]
macd              trend    subplot  [macd, signal, histogram]
donchian          trend    overlay  [upper, middle, lower]
rsi               meanrev  subplot  [value]
bollinger         meanrev  overlay  [upper, middle, lower]
...
```

`mctrader-cli indicator compute --name rsi --period 14 --candles file.csv` = **defer to v2** (CSV schema, parameter encoding 등 별도 brainstorm).

`mctrader-cli strategy list` (기존, MCT-64) — 자동으로 11개 신규 strategy 노출 (registry 등록 부수효과).

### 5.5 mctrader-web 통합 (이번 Epic 비대상)

이 Epic 는 engine 만. Web overlay/subplot 통합은 별도 후속 Epic (mctrader-web Phase 2C 또는 별도 MCT-XX). 단, `INDICATOR_META` 가 engine 에서 노출되어 후속 Epic 이 metadata 만 read 하면 즉시 plot 분기 가능 (overlay vs subplot, axis label).

기존 indicators.csv export 파이프라인 (Phase 2B) 은 작동 — 모든 신규 strategy 가 `compute_indicators()` 의무 구현이므로 CSV 파일에 자동 노출.

## 6. 비기능 요구사항

- **Decimal 일관성**: 모든 indicator 누적 + 출력 Decimal. 외부 라이브러리 (pandas-ta/TA-Lib) **runtime 미사용**.
- **Lookahead 안전**: prefix-stable invariant property test 로 모든 indicator 검증.
- **Performance budget**: 50,000-bar 시계열 기준 모든 indicator 단일 호출 < 200ms (laptop CPU). Phase 1 에 perf benchmark test 추가.
- **버전 bump**: 0.28.0 → 0.29.0. Strategy/Decision public contract 미파괴.
- **Backward compat**: 기존 sma_v1 동작 동일. SMA 내부 구현이 indicators.compute_sma 호출로 바뀌어도 외부 결과 동일 (golden CSV regression).

## 7. Epic 구조 (7 child stories)

| # | Story | 산출물 | Depends |
|---|---|---|---|
| 1 | Indicator package scaffold | `indicators/` 패키지, `types.py`, `meta.py`, `INDICATOR_META`, `test_lookahead_contract.py` (empty fixture skeleton), Decimal+lookahead+perf contract test 인프라 | none |
| 2 | Trend indicators | compute_sma (extracted), compute_ema, compute_macd, compute_donchian + tests + INDICATOR_META 등록 | #1 |
| 3 | Mean-reversion indicators | compute_rsi, compute_bollinger, compute_zscore, compute_stochastic, compute_williams_r + tests | #1 |
| 4 | Volatility/momentum/volume indicators | compute_atr, compute_keltner, compute_stddev, compute_bb_width, compute_roc, compute_obv, compute_vwap_rolling + tests | #1 |
| 5 | Strategy batch 1 (trend) | ema_cross_v1, macd_cross_v1, donchian_breakout_v1 + tests + L4 known-bias fixture | #2 |
| 6 | Strategy batch 2 (meanrev/vol/momentum/volume + T3) | rsi_bounds_v1, bollinger_reversion_v1, zscore_reversion_v1, atr_breakout_v1, keltner_breakout_v1, roc_threshold_v1, vwap_cross_v1, book_imbalance_breakout_v1 + tests + L4 fixtures | #3, #4 |
| 7 | CLI + IndicatorProvider 의무화 + ADR + docs | `mctrader-cli indicator list`, IndicatorProvider 의무 enforcement (registry 측 보조 검증), 새 ADR (`indicator-library-contract`), README/CLAUDE.md 갱신 | #5, #6 |

**예상 PR 5–7개**, 코드 약 2.5k–5k LOC (테스트 포함).

**Phase gate (abort/split criteria)**:
- Phase #1 → #2 진행 전: contract test 모두 green + perf benchmark within budget
- Phase #5 → #6 진행 전: batch 1 strategy 모두 WFO + lookahead L4 통과
- Phase #6 → #7 진행 전: 전 strategy `compute_indicators()` 구현 검증

## 8. 보안 / 데이터 영향

- **보안**: indicator/strategy = 순수 numerical 코드. 외부 입출력 없음. Registry 등록 = import 부수효과만.
- **데이터**: 기존 candle/tick/orderbook reader contract 변경 없음. ADR-009 OHLCV schema 유지.
- **신규 file** ≈ 35 (indicator 6 module + types + meta + 11 strategy + tests). 기존 수정 = sma.py (내부 SMA 호출 indicators 로 위임), cli.py (subcommand 추가), `tests/helpers.py` (fixture builder).

## 9. WFO promotion / search space

10개 신규 candle strategy 각각 ADR-006 search_space_hash registry 등록 필요:
- ema_cross: (fast, slow, sizing_pct)
- macd_cross: (fast, slow, signal, sizing_pct)
- donchian_breakout: (period, sizing_pct)
- rsi_bounds: (period, oversold, overbought, sizing_pct)
- bollinger_reversion: (period, num_std, sizing_pct)
- zscore_reversion: (period, threshold, sizing_pct)
- atr_breakout: (atr_period, atr_mult, sizing_pct)
- keltner_breakout: (period, atr_mult, sizing_pct)
- roc_threshold: (period, threshold, sizing_pct)
- vwap_cross: (period, sizing_pct)

각 strategy story 의 acceptance: `pytest tests/test_wfo_search_data_loader.py -k <strategy>` green.

## 10. 사용자 ownership

본 Epic 은 **opinionated baseline** 제공. Production 전략 = 사용자가 본 template subclass + parameter tuning + WFO promotion. 사용자별 strategies repo (e.g., `mctrader-strategies/`) 가 본 패키지 import + 확장.

## 11. 결정 로그 (Codex review + Sonnet decider)

| # | Decision point | 결정 | 근거 |
|---|---|---|---|
| A | Library structure | flat namespace, pure functions, NamedTuple multi-output | 현재 SMA `compute_indicators` shape + mypy 친화 |
| B | Indicator coverage | 16종 v1, 10종 defer | 모든 카테고리 cover + Decimal 안전한 것만 |
| C | Strategy coverage | 10 candle + 1 T3 | indicator 와 1:1 매핑 + Decision 불변 유지 |
| D | T2/T3 추가 | book_imbalance_breakout 1종만 | candle Epic 에 microstructure 침범 방지 |
| E | WFO 정책 / Decision | 신규 candle 전부 WFO-gated, Decision 불변 | ADR-006 + 스코프 제어 |
| F | Epic shape | MCT-90 + 7 child | MCT-63 패턴, batch review 가능 |
| G | IndicatorProvider | candle strategy 의무 / T2/T3 면제 | 기존 패턴 일관 |
| H | Naming | `<indicator>_<style>_v1`, `compute_<name>` | 기존 registry 일관 |
| I | Tests | hand + golden + property + L4 family fixture | 정확성 + 실용성 |
| J | 외부 라이브러리 | runtime 직접 구현, test cross-val 옵션 | Decimal 불변 |
| K | Version | 0.29.0 | minor — public contract 미파괴 |
| L | CLI | `indicator list` 추가 / `compute` defer | 발견성 + scope 제어 |
| M | Web 통합 | metadata 만 노출, plot 통합 후속 Epic | 의존 분리 |
| N | Fixtures | 7개 builder 공유 + per-strategy edge | 재사용성 |
| O | Risk | phase gate 3곳 + abort criteria | 큰 Epic 의 scope creep 방지 |

## 12. Top 3 risks + mitigations

1. **Lookahead leakage** (full-series API 오용): caller 가 visible_window 외 candle 통째 전달 시 leak 가능
   - mitigation: prefix-stable property test + StrategyContext 측 sentinel slice (필요 시) + ADR-005 L4 fixture
2. **Decimal performance** (recursive EMA/MACD/ATR 누적 비용)
   - mitigation: Phase 1 perf benchmark test (50k-bar < 200ms) — 초과 시 Decimal context precision 튜닝 또는 알고리즘 재검토 (예: SMA-based EMA approximation 대신 Wilder smoothing 명시)
3. **Scope creep** (risk exits, web charting, CLI compute, T2/T3 microstructure 가 Epic 안으로 침투)
   - mitigation: Phase gate + child story 별 acceptance + Decision schema 동결 명시 (본 spec §11 row E 인용)

## 13. Open issues / future Epics

- **MCT-XX (web Phase 2C)**: subplot indicator UI 통합 — INDICATOR_META 소비
- **MCT-XX (combo strategies)**: ATR-trailing exit + MACD entry 같은 multi-component strategy. Decision 또는 risk/ 확장 필요 시 별도 brainstorm
- **MCT-XX (deferred indicators)**: Ichimoku / SuperTrend / ADX/DMI / DEMA-TEMA / CCI / AO / MFI / A/D / CMF / session VWAP
- **MCT-XX (T2/T3 strategy expansion)**: liquidity_sweep, tape_momentum 등 — microstructure 전용 Epic
- **MCT-XX (CLI indicator compute)**: ad-hoc indicator 계산 + CSV 입출력
