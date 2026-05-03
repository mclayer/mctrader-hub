---
story_key: MCT-22
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-22: RiskGate minimal Paper enforcement (MAX_DAILY_LOSS + DRAWDOWN_LIMIT)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "RiskGate minimal Paper — 5 kill switch 중 2 critical (MAX_DAILY_LOSS + DRAWDOWN_LIMIT)"

## 2. 도메인 해석

mctrader-engine 0.1.0 RiskGate 의 첫 enforcement (NullRiskGate 외). ADR-007 5 kill switch 중 2 = MVP. 나머지 3 (CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL) = future Epic.

## 3. 관련 ADR

- ADR-007 (5 kill switch full Accepted, MCT-22 = minimal subset 명시)
- ADR-002 (RiskGate Protocol — check-only interface 유지)
- ADR-004 (RiskGateEvent ExecutionReport stream)
- 의존: MCT-21 freeze (PaperExecutor + VirtualPortfolio)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── kill_switch.py        # MaxDailyLossSwitch + DrawdownLimitSwitch
├── enforcer.py           # PaperRiskGate (RiskGateProtocol impl, internal stateful)
└── policy.py             # RiskPolicy config
```

## 5-6. 요구사항

- ADR-007 D8: `active_capital = min(account_equity × 20%, 10,000,000 KRW)`
- ADR-007 D6: KST midnight daily reset (kill switch 자동 해제 X)
- ADR-007 D7: hard_stop manual ack 의무

## 7. 설계 서사 (Codex 합성)

### 7.1 MAX_DAILY_LOSS = active_capital 기반 + KST reset (A1)

```python
class MaxDailyLossSwitch:
    hard_pct: Decimal = Decimal("0.03")    # ADR-007 D1 hard
    soft_pct: Decimal = Decimal("0.02")    # severity 기록만 (MVP enforcement = hard)
    # base = ADR-007 D8 active_capital
```

KST midnight reset (D6) = 새 daily bucket 시작, kill switch 자동 해제 X.

### 7.2 DRAWDOWN_LIMIT = run-local portfolio peak (A2)

```python
class DrawdownLimitSwitch:
    hard_pct: Decimal = Decimal("0.04")    # ADR-007 D1 hard portfolio
    # peak = run-local high-water mark (per-bar mark-to-market)
    # block: current_equity <= peak_equity * (1 - hard_pct)
```

**MVP subset 명시**: ADR-007 D1/D2 strategy peak / rolling 24h dual = future Epic.

### 7.3 Metric update frequency (A3)

| 시점 | Action |
|---|---|
| Per closed bar | VirtualPortfolio mark-to-market (unrealized_pnl + equity snapshot) |
| Per fill | cash / position / realized_pnl / open_orders 즉시 |
| Per decision | RiskGate.check() (block enforcement) |

per second 비채택 (overhead). RiskGate.check 에 넘기는 portfolio_state 가 항상 latest invariant.

### 7.4 RiskGateEvent emit = blocked-only + status-change (A4)

| 시나리오 | Emit |
|---|---|
| Pass → Pass | ✗ |
| Pass → Soft | ✓ warning |
| Soft → Hard | ✓ block |
| Hard → Hard | ✗ (latch) |
| 새 daily bucket → Pass | ✓ transition (manual ack 명시) |

Payload: trigger / severity / threshold_value / observed_value / risk_policy_version / portfolio_snapshot.

### 7.5 5 kill switch future priority (A5)

| Trigger | 우선순위 | 근거 |
|---|:---:|---|
| UNUSUAL_ACTIVITY | 1 | Paper 가치 (data stale / duplicate / opposite order) |
| CONSECUTIVE_LOSSES | 2 | closed trade ledger + position lifecycle 의존 |
| EXTERNAL_SIGNAL | 3 | Live 전환 직전 (manual kill / API ban / ADR-008 secret 통합) |

MCT-22 RiskGateEvent schema = 5 모두 표현 가능 (future-proof). enforcement 활성화 = 2 만.

### 7.6 RiskGate interface = check-only 유지 (A6)

`update()` 추가 비채택 (ADR-002 D4 동일 interface 보존). Stateful internal history = `PaperRiskGate` 내부:

```python
class PaperRiskGate:
    def __init__(self, policy: RiskPolicy, clock: Clock): ...
    
    def check(self, *, decision, portfolio_state):
        self._maybe_reset_daily_bucket(portfolio_state)
        self._update_peak(portfolio_state)
        # MAX_DAILY_LOSS / DRAWDOWN_LIMIT check
        # block 시 raise RiskGateBlocked
```

"check() 가 side effect 가능" = 문서 명시.

### 7.7 Post-kill-switch = order block + run continue + hard_stop latch (A7)

| 동작 | 정책 |
|---|---|
| New order intent | block (RiskGateBlocked) |
| Strategy / bar aggregation | continue (calibration 위해) |
| hard_stop latch | run 종료까지 유지 (KST reset 도 자동 해제 X) |
| SIGTERM / duration 만료 | RiskGate 와 분리 (executor lifecycle) |

ExecutionReport summary 추가:
- `risk_gate_triggered_count`
- `risk_gate_first_trigger_ts_utc`
- `risk_gate_final_status`

### 7.8 Out-of-scope

5 kill switch 나머지 3 / strategy peak + rolling 24h soft / Recovery tier / Manual ack UI / `update()` interface / Configurable post_block_action.

### 7.9 Acceptance (12 AC)

| # | AC |
|---|---|
| AC1 | RiskPolicy Pydantic config |
| AC2 | MaxDailyLossSwitch active_capital base + KST reset |
| AC3 | DrawdownLimitSwitch portfolio peak + per-bar mark-to-market |
| AC4 | PaperRiskGate check-only Protocol 만족 |
| AC5 | RiskGateBlocked → order block + RiskGateEvent stream |
| AC6 | RiskGateEvent emit = blocked-only + transition |
| AC7 | hard_stop latch (자동 해제 X manual ack 명시) |
| AC8 | KST midnight reset |
| AC9 | post-kill-switch = strategy continue + new order block |
| AC10 | ExecutionReport summary risk fields |
| AC11 | trigger enum 5 kill switch future-proof |
| AC12 | 5 required check green |

### 7.10 Codex 적용

7/7 채택. ADR-007 full 아닌 **minimal subset 명시**, conflict 0/7.

## 8-11

(Phase 2 = risk/* + AC1~AC12.)
