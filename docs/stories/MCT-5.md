---
story_key: MCT-5
status: phase:요구사항
component: backtest
type: brainstorm
related_adr: ADR-005
---

# MCT-5: Lookahead bias 검증 의무 (Test Contract §8 강제)

## 1. 사용자 요구사항 (verbatim)

mctrader 의 Lookahead bias 자동 검증 mechanism. ADR-002 H4 (\"t decision 은 t-1 close 데이터만, 체결 = next tick / next candle open\") 의 강제 + Test Contract §8 align.

## 2. 도메인 해석

ADR-002 / ADR-003 / ADR-004 의 baseline (8-state lifecycle / 4 timestamp event log / latency model) 위에 **4-layer verification** mechanism 박제. 단일 layer 로는 우회 가능 — combined defense 의무.

## 3. 관련 ADR

- ADR-005 ([`../adr/ADR-005-lookahead-verification.md`](../adr/ADR-005-lookahead-verification.md))
- baseline: ADR-002 H4 + ADR-003 H2 + ADR-004 D5 (latency)
- 향후: MCT-6 (OOS / hyperparameter governance — path d 의 enforcement)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader/
├── executor/components/
│   ├── market_data.py        # MarketDataReader read-window enforcement (L2)
│   └── strategy_context.py   # StrategyContext + visible_window
├── verification/
│   ├── lint.py               # libcst AST scan (L1)
│   ├── runtime_check.py      # invariant assert (L2 supplement)
│   ├── event_log_audit.py    # post-hoc 4-timestamp invariant (L3)
│   └── fixtures/             # known-bias regression test (L4)
└── ...
```

## 5. 요구사항 확장

본 ADR 의 결정 = 4 path taxonomy + 4 layer verification + StrategyContext interface + close-of-bar 정의 + multi-timeframe + Live audit + .copy() 우회 한계.

## 6. 외부 지식

- pandas `shift(-1)` / `iloc[i+1]` / `rolling(center=True)` / `bfill` / `merge_asof(forward)` 등 위험 패턴
- AST scan tool: stdlib `ast` 또는 `libcst` (formatting 보존 + suppression annotation)
- ML/quant academic: train-test leak / global scaler fit / future label as feature

## 7. 설계 서사 (요약)

### 7.1 4 Path Taxonomy

| Path | 설명 | Detection layer |
|---|---|---|
| (a) Future data access | `df.shift(-1)`, `iloc[i+1]`, `rolling(center=True)` 등 | L1 + L2 |
| (b) Same-candle fill | current candle high/low/close 를 같은 candle 안에서 fill 가정 | L3 (event log invariant) |
| (c) Data prep leakage | feature engineering 시 future bar 사용, full-sample scaler fit | L1 + L2 (feature metadata) |
| (d) OOS optimization | hyperparameter tuning 시 OOS data peek | MCT-6 (optimization governance) |

### 7.2 4 Verification Layers

| Layer | Detection | 한계 |
|---|---|---|
| **L1 Static (lint)** | libcst AST scan: shift(-n), iloc[i+1], rolling(center=True), bfill, merge_asof(forward), label/future/target 컬럼 strategy runtime 참조 | False positive (label 생성 script 합법) → severity 분리 (strategy runtime=error, research notebook=warning) |
| **L2 Runtime** | MarketDataReader 가 `as_of_ts` 기준 read-window 강제. StrategyContext 가 raw DataFrame 미노출, `visible_window()` API 만 | `.copy()`, numpy 변환, global cache, external file read 우회 가능. boundary 가 아닌 default-safe |
| **L3 Post-hoc** | event log 의 4 timestamp invariant 검증 (`observed_until_ts ≤ decision_ts ≤ eligible_fill_ts ≤ fill_ts` + candle-specific rules) | event log 가 거짓말하면 약함. price source schema 추가 필수 |
| **L4 Fixture** | known-bias fixture 가 L1-L3 중 하나에 의해 fail. mechanism 자체 regression. | 새 우회 패턴 미커버 — production incident → fixture 승격 의무 |

### 7.3 StrategyContext visible_window 강제

```python
@dataclass(frozen=True)
class StrategyContext:
    mode: Literal["backtest", "paper", "live"]
    run_id: str
    decision_ts: datetime
    observed_until_ts: datetime
    as_of_ts: datetime          # strategy 명시 인지 의무
    market: MarketDataProvider
    executor: TradeExecutor
    risk_constraints: RiskConstraints
    clock: Clock
    capabilities: ExchangeCapabilities

    def visible_window(self, symbol: str, timeframe: str, lookback: int | None = None) -> MarketDataWindow:
        """as_of_ts 이하 row 만 반환. raw DataFrame 미노출."""
```

DataFrame view 방식 baseline (기존 quant workflow 호환) + generator mode optional (가장 lookahead-safe, 고위험 전략).

### 7.4 close-of-bar boundary 정의

`bar_end_ts == next_bar_open_ts`. 5분 bar 10:00-10:05 = `close_time=10:05:00`. decision 가능 시점 = `decision_ts >= 10:05:00`. fill = next tick 또는 next bar open (10:05:00 시작 next bar). artificial offset (e.g. +1ms) 없음.

동일 timestamp event ordering = sequence number: `BAR_CLOSE_OBSERVED → ORDER_DECISION → ORDER_SUBMITTED`.

### 7.5 Multi-timeframe window

```
visible_window(symbol, "5m", as_of_ts=10:35) → max bar close ≤ 10:35
visible_window(symbol, "1h", as_of_ts=10:35) → max bar close ≤ 10:00 (last closed 1h bar)
```

incomplete higher timeframe bar 를 forward-fill 해 lower timeframe decision 에 제공 = 금지.

### 7.6 Live mode audit

Live 도 자동 lookahead-safe 선언 금지. 별도 invariant:

```
market_event_received_ts <= decision_ts
submit_ts >= decision_ts
ack_ts >= submit_ts
fill_ts >= eligible_fill_ts
```

vendor timestamp ↔ local receipt timestamp 차이 / clock skew / late-arriving tick / candle aggregation = Live bias source.

### 7.7 .copy() 우회 한계 + 4-step 대안

Runtime enforcement = security boundary 아님. 4-step:
1. Strategy 가 raw data path import / direct read 금지
2. StrategyContext API 외 data access = lint + code review 차단
3. BacktestExecutor event log invariant 사후 검증
4. (고신뢰) strategy = separate process / sandbox + IPC visible_window only

### 7.8 Test Contract §8 align

7 lane (unit / integration / fixture / replay / backtest / paper / live audit) 모두에서 `strategy_view.max_ts ≤ context.as_of_ts` 검증. backtest ↔ paper/live lane 동일 StrategyContext interface.

### 7.9 Codex 의견 적용

Codex 권장 채택률 11/11 (4 path + 4 layer + StrategyContext + close-boundary + multi-timeframe + Live audit + .copy() 한계).

## 8-11

(Phase 2 N/A — doc-only Story.)
