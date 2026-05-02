---
adr_id: ADR-005
title: Lookahead bias 검증 의무 — 4-layer verification + StrategyContext visible_window
status: Accepted
date: 2026-05-02
related_story: MCT-5
category: backtest
supersedes: []
---

# ADR-005: Lookahead bias 4-layer verification + StrategyContext visible_window 강제

## Status

Accepted — 2026-05-02. MCT-5 Phase 1 PR.

## Context

ADR-002 H4: \"t decision = t-1 close 데이터만, 체결 = next tick / next candle open\". 본 ADR = 강제 mechanism design.

핵심 framing: 단일 layer 로 lookahead bias 완전 차단 불가능 (Pandas `.copy()` / numpy 변환 / global cache 우회). **L1-L4 4-layer combined defense** 의무.

## Decision

### D1. 4 Lookahead bias paths

| Path | 설명 | 책임 |
|---|---|---|
| (a) Future data access | `shift(-1)` / `iloc[i+1]` / `rolling(center=True)` / future column ref | L1 + L2 |
| (b) Same-candle fill | current candle high/low/close 를 같은 candle 에서 fill | L3 (event log) |
| (c) Data prep leakage | full-sample scaler fit / future bar in feature engineering | L1 + L2 (feature lineage) |
| (d) OOS optimization | hyperparameter tuning OOS peek | MCT-6 (별도 ADR) |

### D2. 4 Verification layers

#### L1 Static lint (libcst AST scan)
- Severity: strategy runtime path = error / research notebook + label builder = warning + allowlist
- Detection: `shift(-n)` / `pct_change(-n)` / `diff(-n)` / `rolling(center=True)` / `iloc[i+1]` / `bfill` / `merge_asof(direction="forward")` / future/target/label column strategy runtime 참조 / 전체 dataset scaler fit before split
- Tool: `libcst` (formatting 보존 + suppression annotation 가능)
- 한계: aliasing / dynamic getattr / helper function wrap / third-party indicator 미커버

#### L2 Runtime read-window enforcement
- MarketDataReader: `read(symbol, timeframe, as_of_ts, lookback)` API. `as_of_ts` 이하 row 만 반환
- StrategyContext: raw DataFrame 미노출. `visible_window()` API 만
- Invariant: `max(data.visible_ts) <= context.observed_until_ts < context.eligible_fill_ts`
- 한계: `.copy()` / numpy 변환 / external read / global cache 우회 가능 — boundary 아닌 default-safe

#### L3 Post-hoc event log invariant
- 모든 order event = ADR-003 H2 의 4 timestamp + price source identity 기록
- Invariant:
  ```
  observed_until_ts <= decision_ts <= eligible_fill_ts <= fill_ts
  observed_until_ts == previous_closed_bar_ts
  eligible_fill_ts >= next_tick_ts OR next_bar_open_ts
  fill_price_source_ts >= eligible_fill_ts
  fill_price_source_ts <= fill_ts
  ```
- Event schema 추가: `price_source_type ∈ {tick, bar_open, bar_high, bar_low, bar_close}`, `price_source_start_ts`, `price_source_end_ts`
- CI / pre-commit 자동 audit

#### L4 Fixture regression test
- known-bias strategy 가 L1-L3 중 적어도 하나에서 fail 검증
- 기본 fixtures:
  - `known_bias_shift_minus_1_strategy` — L1 fail
  - `known_bias_same_candle_high_low_fill` — L3 fail
  - `known_bias_future_feature_dataset` — L2 fail (feature metadata)
  - `known_bias_oos_selection_loop` — MCT-6 split registry fail
- production incident / review 발견 lookahead 사례 = fixture 승격 의무

### D3. StrategyContext interface

```python
@dataclass(frozen=True)
class StrategyContext:
    mode: Literal["backtest", "paper", "live"]
    run_id: str
    decision_ts: datetime
    observed_until_ts: datetime  # event log audit field
    as_of_ts: datetime           # strategy interface field (initially == observed_until_ts)
    market: MarketDataProvider
    executor: TradeExecutor
    risk_constraints: RiskConstraints
    clock: Clock
    capabilities: ExchangeCapabilities

    def visible_window(self, symbol: str, timeframe: str, lookback: int | None = None) -> MarketDataWindow: ...
```

- **DataFrame view baseline** (기존 quant workflow 호환)
- **generator mode optional** (가장 lookahead-safe, 고위험 전략 / live-like)
- Strategy 는 raw data path import 또는 direct read 금지

### D4. close-of-bar boundary 정의

```
bar_end_ts == next_bar_open_ts
bar 는 bar_end_ts 시점 이후 observable
order decision after observing bar_end_ts → fill at first eligible market event >= bar_end_ts
```

Artificial offset (+1ms / +1us) 없음. 동일 timestamp event ordering = sequence number: `BAR_CLOSE_OBSERVED → ORDER_DECISION → ORDER_SUBMITTED`.

### D5. Multi-timeframe window

```
decision_ts = 10:35
visible_window(symbol, "5m", as_of_ts=10:35) -> max bar close <= 10:35
visible_window(symbol, "1h", as_of_ts=10:35) -> max bar close <= 10:00
```

- Higher timeframe incomplete bar → lower timeframe decision provide 금지
- Resampled feature 의 `available_from_ts` = candle close 시점

### D6. Live mode audit

Live 도 자동 lookahead-safe 선언 금지.

```
market_event_received_ts <= decision_ts
submit_ts >= decision_ts
ack_ts >= submit_ts
fill_ts >= eligible_fill_ts
```

Live bias source: vendor timestamp ↔ local receipt 차이 / clock skew / late-arriving tick / candle aggregation.

### D7. Runtime enforcement 한계 + 4-step 대안

1. Strategy 의 raw data path import / direct read 금지
2. StrategyContext API 외 data access = lint + code review 차단
3. BacktestExecutor event log invariant 사후 검증
4. (고신뢰 옵션) Strategy = separate process / sandbox + IPC visible_window only

### D8. Test Contract §8 align

7 lane (unit / integration / fixture / replay / backtest / paper / live audit) 모두에서 `strategy_view.max_ts <= context.as_of_ts` 검증. backtest ↔ paper/live 동일 StrategyContext interface.

## Alternatives Considered

### A1. Post-hoc event log only (L3 단독)
- L1/L2/L4 미적용
- **기각**: bug-found-late. lookahead 가 backtest 결과 신뢰성 직접 손상 → pre-fail (L1/L2) 우선.

### A2. Static lint only (L1 단독)
- **기각**: false negative 폭증 (aliasing / dynamic / third-party). runtime + post-hoc 의무.

### A3. raw DataFrame 그대로 strategy 노출
- **기각**: 가장 흔한 lookahead path (a) 직접 노출. visible_window 강제 의무.

### A4. close_time = bar_end_ts + epsilon (artificial offset)
- **기각**: timestamp ordering 만 명확화 — sequence number 로 충분. epsilon 은 floating-point / timezone artifact 위험.

### A5. multi-timeframe = lower timeframe 의 incomplete higher TF 를 forward-fill
- **기각**: 가장 미묘한 lookahead. 명시적 금지.

### A6. Live = lookahead 자동 free 선언
- **기각**: vendor timestamp / clock skew / late-arriving tick = Live bias source. 별도 audit 의무.

## Consequences

### C1. Strategy code 작성 제약
- raw DataFrame 직접 받기 불가
- StrategyContext API 만 사용 의무
- lint 통과 의무 (false positive 시 explicit suppression)

### C2. Event log schema 확장
- ADR-003 H6 event schema_version up — `price_source_type` / `price_source_start_ts` / `price_source_end_ts` 추가

### C3. CI / pre-commit
- L1 lint = pre-commit + CI gate
- L3 invariant = backtest run 종료 시 자동 audit
- L4 fixture = test suite 의무

### C4. .copy() 우회 risk 박제
- runtime enforcement = security boundary 아님 명시
- 고신뢰 strategy = separate process / sandbox option (MCT-7 risk gate Story 와 연계)

### C5. MCT-6 dependency
- path (d) OOS optimization governance = MCT-6 의무
- ADR-006 의 split registry 가 본 ADR L4 fixture (`known_bias_oos_selection_loop`) 의 fail mechanism 제공

## Cross-references

- ADR-002 H4 / ADR-003 H2 / ADR-004 D5 — baseline
- MCT-6 — OOS governance (path d enforcement)
- ADR-009 (예정) — feature lineage metadata schema
