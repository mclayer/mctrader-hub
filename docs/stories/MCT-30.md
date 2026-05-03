---
story_key: MCT-30
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-25
related_adrs: ADR-007, ADR-002, ADR-004, ADR-006
---

# MCT-30: ADR-007 D5 SL/TP guards + Calibration AC + Epic E2E (sealing)

## 1. 사용자 요구사항 (verbatim, MCT-25 Epic)

> "ADR-007 D5 SL/TP guard (catastrophic_stop / max_position_age / price_gap_guard / intended_stop_loss_pct) + Calibration AC C1 (kill_switch_trigger_frequency baseline) + Epic E2E acceptance test"

## 2. 도메인 해석

MCT-25 의 통합 sealing Story. D5 SL/TP guard 추가 + 5 kill-switch (D1) + active_capital lock (D8) + RiskPolicy versioning (D9) + Recovery 3-tier (D7) 의 E2E integration. C1 calibration metric 으로 7d Paper run 의 kill-switch trigger frequency baseline 수집. ADR-006 promotion gate "risk violation 0" 의 5/5 enforce 검증.

## 3. 관련 ADR

- ADR-007 D5 (catastrophic_stop / max_position_age / price_gap_guard / intended_stop_loss_pct)
- ADR-007 D1 + D7 + D8 + D9 (E2E integration)
- ADR-006 (promotion gate "risk violation 0" = hard + critical = 0 AND soft = 0)
- ADR-002 (RiskGate Protocol check-only 보존)
- ADR-004 (CalibrationMetrics extension — kill_switch_trigger_frequency)
- 의존: MCT-26 + MCT-27 + MCT-28 + MCT-29 freeze

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── stop_loss_guard.py (NEW)        # D5 4 sub-guard
├── kill_switch.py (extend)         # evaluate_sl_tp_guards
└── enforcer.py (extend)            # SL/TP guard 통합

mctrader-engine/src/mctrader_engine/calibration/
└── metric.py (extend)              # kill_switch_trigger_frequency

mctrader-engine/tests/
└── test_risk_full_e2e.py (NEW)     # B1~B10 + C1 통합 acceptance
```

## 5-6. 요구사항

- catastrophic_stop = entry -3% 또는 position notional -1.0× active_capital (둘 중 먼저 도달)
- max_position_age = 24h (position open_ts vs now)
- price_gap_guard = mid 대비 1.0% 이상 불리 (BUY 시 ask > mid×1.01, SELL 시 bid < mid×0.99)
- intended_stop_loss_pct = strategy decision metadata (없으면 soft event, MCT-25 = strategy migration 부담 회피)

## 7. 설계 서사 (Codex 합성)

### 7.1 SL/TP guard sub-trigger (A1)

```python
def evaluate_sl_tp_guards(
    *, position: Position, current_mid: Decimal, decision: StrategyDecision,
    active_capital: Decimal, now: datetime,
    catastrophic_pct: Decimal, max_age_hours: int, price_gap_pct: Decimal
) -> SwitchEvaluation:
    # catastrophic_stop
    pnl_pct = (current_mid - position.entry_price) / position.entry_price
    if pnl_pct <= -catastrophic_pct: return hard("catastrophic_pnl")
    notional_loss = (position.entry_price - current_mid) * position.quantity
    if notional_loss >= active_capital: return hard("catastrophic_notional")
    
    # max_position_age
    age = now - position.open_ts_utc
    if age > timedelta(hours=max_age_hours): return hard("max_age")
    
    # price_gap_guard
    if decision.kind == "BUY" and decision.price > current_mid * (1 + price_gap_pct):
        return hard("price_gap_buy")
    if decision.kind == "SELL" and decision.price < current_mid * (1 - price_gap_pct):
        return hard("price_gap_sell")
    
    # intended_stop_loss_pct (soft if missing)
    if decision.kind in ("BUY", "SELL") and decision.intended_stop_loss_pct is None and decision.max_loss_krw is None:
        return soft("missing_sl")
    
    return pass
```

reason_code: `"SL_TP_GUARD:catastrophic_pnl_-0.034"` / `"SL_TP_GUARD:max_age_25h"` / `"SL_TP_GUARD:price_gap_buy_0.0123"` / `"SL_TP_GUARD:missing_sl"`.

### 7.2 StrategyDecision extension (A2)

```python
class StrategyDecision(BaseModel):
    kind: Literal["BUY", "SELL", "HOLD"]
    quantity: Decimal | None
    price: Decimal | None
    # 신규 (MCT-30, optional)
    intended_stop_loss_pct: Decimal | None = None
    max_loss_krw: Decimal | None = None
```

Backward compat = optional. SmaStrategy 는 None 으로 시작 (soft event 만, block X).

### 7.3 CalibrationMetrics extension (A3)

```python
@dataclass(frozen=True)
class KillSwitchTriggerFrequency:
    trigger: TriggerName
    soft_count: int
    hard_count: int
    critical_count: int
    first_trigger_ts_utc: datetime | None
    triggers_per_day: Decimal
```

ExecutionReport.metadata.calibration.kill_switch_trigger_frequency: list[...] = baseline only (gate threshold 결정 별도).

ADR-006 promotion gate: `risk_violation_count = hard + critical = 0 AND soft = 0` 검증 = `all(f.hard_count == 0 and f.critical_count == 0 and f.soft_count == 0 for f in frequency)`.

### 7.4 E2E acceptance test (A4)

`test_risk_full_e2e.py` = 5 fixture scenario:
- scenario_max_daily_loss = MAX_DAILY_LOSS hard trigger → block
- scenario_drawdown = DRAWDOWN_LIMIT hard → block
- scenario_consecutive_losses = 7 trailing losses → block
- scenario_unusual_activity = data_stale 15s → block
- scenario_external_signal = file sentinel manual_kill → block + recovery hard_stop ack flow

각 scenario = ExecutionReport 검증 + RiskGateEvent v2 schema validation + reason_code regex + RiskPolicySnapshot.policy_hash unchanged.

### 7.5 ADR-006 promotion gate verify (A5)

`test_promotion_gate.py`:
- scenario_clean = 0 violation → promotion eligible
- scenario_one_soft = soft 1 → promotion blocked
- scenario_drift = policy_hash drift → critical → promotion blocked

### 7.6 Out-of-scope

- TP enforcement (RiskGate 미강제, strategy 책임)
- trailing SL automation (strategy 책임)
- multi-symbol catastrophic_notional cross-correlation

### 7.7 Acceptance (12 AC)

| # | AC |
|---|---|
| AC1 | catastrophic_stop entry -3% trigger |
| AC2 | catastrophic_stop notional -1.0× active_capital trigger |
| AC3 | max_position_age 24h trigger |
| AC4 | price_gap_guard buy/sell |
| AC5 | intended_stop_loss_pct missing = soft (block X) |
| AC6 | StrategyDecision optional fields backward compat |
| AC7 | CalibrationMetrics.kill_switch_trigger_frequency 5 trigger 합산 |
| AC8 | ADR-006 promotion gate 5/5 enforce 검증 |
| AC9 | E2E test_risk_full_e2e 5 scenario green |
| AC10 | RiskGateEvent v2 schema validation 5 scenario |
| AC11 | RiskPolicySnapshot drift critical 검증 |
| AC12 | 5 required check green |

### 7.8 Codex 적용

7/7 채택. ADR conflict 0/7.

## 8-11

(Phase 2 = risk/stop_loss_guard.py + calibration/metric.py extension + tests/test_risk_full_e2e.py + tests/test_promotion_gate.py.)
