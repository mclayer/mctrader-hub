---
story_key: MCT-28
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-25
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-28: UNUSUAL_ACTIVITY kill-switch (5min rolling window + minimum sample)

## 1. 사용자 요구사항 (verbatim, MCT-25 Epic)

> "ADR-007 D1 UNUSUAL_ACTIVITY — soft reject_rate>20%/5min / data_stale>3s; hard duplicate client_order_id, opposite orders/1s≥3, reject>40%, stale>10s, balance_mismatch>0.5%"

## 2. 도메인 해석

mctrader-engine 의 활동 이상 탐지. paper 환경의 simulated reject 가 적으므로 minimum sample (20) + fixture replay 로 보완. data_stale = WebSocket last_message_ts 추적, duplicate client_order_id = order ledger hash check, opposite orders = decision history rolling 1s, balance_mismatch = VirtualPortfolio invariant.

## 3. 관련 ADR

- ADR-007 D1 (UNUSUAL_ACTIVITY 5 sub-trigger)
- ADR-002 (RiskGate Protocol check-only 유지)
- ADR-004 (RiskGateEvent v2 schema)
- 의존: MCT-26 freeze (RiskPolicy.unusual_*)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── kill_switch.py (extend)         # evaluate_unusual_activity
├── activity_window.py (NEW)        # 5min rolling window + minimum sample
└── enforcer.py (extend)            # UNUSUAL_ACTIVITY 통합
```

## 5-6. 요구사항

- 5min rolling window (deque), minimum sample 20
- data_stale: market_stream.last_message_ts vs clock.now()
- duplicate client_order_id: order ledger 의 client_order_id set
- opposite orders/1s: decision history 의 (BUY ↔ SELL) sequence within 1s ≥ 3
- balance_mismatch: VirtualPortfolio invariant — `cash + sum(position * mark_price) - equity` ≤ 0.5% × equity

## 7. 설계 서사 (Codex 합성)

### 7.1 ActivityWindow (A1)

```python
class ActivityWindow:
    def __init__(self, *, window_minutes: int, min_sample: int): ...
    def record_decision(self, ts: datetime, decision: StrategyDecision): ...
    def record_fill(self, ts: datetime, fill: Fill): ...
    def record_reject(self, ts: datetime, reason: str): ...
    
    def reject_rate(self, now: datetime) -> Decimal | None: ...  # None if insufficient sample
    def data_stale_seconds(self, now: datetime, last_market_ts: datetime) -> int: ...
    def duplicate_client_order_id(self) -> str | None: ...
    def opposite_order_burst(self, now: datetime) -> bool: ...
```

### 7.2 evaluate_unusual_activity (A2)

5 sub-trigger 각각 SwitchEvaluation 산출, 최대 severity 채택. reason_code = 첫 trigger 의 subkey:
- `"UNUSUAL_ACTIVITY:reject_rate_0.42"` (hard)
- `"UNUSUAL_ACTIVITY:data_stale_15s"` (hard)
- `"UNUSUAL_ACTIVITY:duplicate_oid_<id>"` (hard)
- `"UNUSUAL_ACTIVITY:opposite_burst_3"` (hard)
- `"UNUSUAL_ACTIVITY:balance_mismatch_0.0083"` (hard)

### 7.3 Paper-specific note (A3)

paper 의 simulated reject = 부족. minimum sample 20 + fixture test 가 reject sequence 명시 inject.

opposite_orders = ADR-007 D1 hard. 단 strategy 의 의도된 reverse signal (SMA cross 등) 도 burst trigger 가능 → reasonable threshold (1s 내 3회 이상은 비정상). strategy 책임 = 1s 내 cross 발생 가능한 timeframe 사용 금지.

balance_mismatch (paper) = VirtualPortfolio 의 cash + position * mark_price 가 equity 와 일치 의무. 0.5% drift = floating point 또는 logic bug. paper 에서는 사실상 hard event (dev fixture 외 발생 X).

### 7.4 Out-of-scope

- API rate limit 계산 (D4 Epic)
- broker error code 분류 (Live Epic)
- multi-exchange reject sequence (Bithumb only)

### 7.5 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | ActivityWindow rolling 5min |
| AC2 | minimum sample 20 gating (insufficient → pass) |
| AC3 | reject_rate threshold 0.20 / 0.40 |
| AC4 | data_stale threshold 3s / 10s |
| AC5 | duplicate client_order_id detection |
| AC6 | opposite orders/1s ≥ 3 detection |
| AC7 | balance_mismatch VirtualPortfolio invariant |
| AC8 | 5 required check green |

### 7.6 Codex 적용

7/7 채택. ADR conflict 0/7.

## 8-11

(Phase 2 = risk/activity_window.py + kill_switch.py + enforcer.py.)
