---
story_key: MCT-27
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-25
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-27: CONSECUTIVE_LOSSES kill-switch (closed trade ledger 기반)

## 1. 사용자 요구사항 (verbatim, MCT-25 Epic)

> "ADR-007 D1 CONSECUTIVE_LOSSES — soft 5 closed loss / hard 7, min 10 closed orders before trigger"

## 2. 도메인 해석

mctrader-engine 의 closed trade 단위 손익 추적. 현재 VirtualPortfolio 는 cash + position state + realized_pnl 누적만 — trade 단위 entry/exit FIFO matching 은 별도 ledger 의무. CONSECUTIVE_LOSSES = trailing N consecutive realized_pnl<0 trades 카운트.

## 3. 관련 ADR

- ADR-007 D1 (CONSECUTIVE_LOSSES soft 5 / hard 7, min 10)
- ADR-002 (RiskGate Protocol check-only 유지)
- ADR-004 (ClosedTrade event ExecutionReport stream)
- 의존: MCT-26 freeze (RiskPolicy.consecutive_losses_*)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── kill_switch.py (extend)         # evaluate_consecutive_losses
├── trade_ledger.py (NEW)           # FIFO matching + closed trade tracking
└── enforcer.py (extend)            # PaperRiskGate.check 통합

mctrader-engine/src/mctrader_engine/executor/
└── paper.py (extend)               # fill 시 trade_ledger.on_fill 호출
```

## 5-6. 요구사항

- Closed trade 정의: FIFO matching — entry side 매수 → exit side 매도 (or reverse), full close 또는 partial close 시 each closed unit
- realized_pnl = (exit_price - entry_price) × quantity - fees (long) / inverse (short)
- min_closed = 10 trades 누적 후 trigger 활성화
- streak = trailing consecutive losses (last_loss_ts > last_win_ts)

## 7. 설계 서사 (Codex 합성 — Phase 2 시점에 구체화)

### 7.1 ClosedTrade dataclass (A1)

```python
@dataclass(frozen=True, slots=True)
class ClosedTrade:
    trade_id: str  # uuid
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_ts_utc: datetime
    entry_price: Decimal
    exit_ts_utc: datetime
    exit_price: Decimal
    quantity: Decimal
    realized_pnl_krw: Decimal
    fees_krw: Decimal
    is_loss: bool  # realized_pnl_krw < 0
```

### 7.2 TradeLedger FIFO matching (A2)

```python
class TradeLedger:
    def __init__(self): self._open_lots: dict[str, deque[OpenLot]] = defaultdict(deque)
    def on_fill(self, fill: Fill) -> list[ClosedTrade]: ...
    @property
    def closed_trades(self) -> list[ClosedTrade]: ...
```

PARTIALLY_FILLED 처리: fill 마다 quantity 누적, opposite side fill 시 FIFO match. cancel-only (no fill) = ledger 영향 없음.

### 7.3 evaluate_consecutive_losses (A3)

```python
def evaluate_consecutive_losses(
    *, recent_closed_trades: list[ClosedTrade],
    soft_count: int, hard_count: int, min_closed: int
) -> SwitchEvaluation:
    if len(recent_closed_trades) < min_closed:
        return SwitchEvaluation(severity="pass", ...)
    streak = 0
    for trade in reversed(recent_closed_trades):
        if trade.is_loss: streak += 1
        else: break
    severity = "hard" if streak >= hard_count else "soft" if streak >= soft_count else "pass"
    return SwitchEvaluation(severity=severity, threshold_value=Decimal(hard_count), observed_value=Decimal(streak))
```

### 7.4 PaperRiskGate.check 통합 (A4)

PaperExecutor 의 fill loop 에서 TradeLedger.on_fill() 호출, RiskGate.check 시 enforcer 가 ledger.closed_trades 참조. closed_trades 가 size O(trades) 이지만 paper run 일반적 100~1000 단위 → 메모리 무관.

### 7.5 reason_code (A5)

`"CONSECUTIVE_LOSSES:streak_5"` (soft) / `"CONSECUTIVE_LOSSES:streak_7"` (hard).

### 7.6 Out-of-scope

- multi-symbol consecutive_losses (per-symbol vs portfolio-wide) — single-symbol baseline 유지, per-symbol future
- streak window 시간 제한 (예: 24h 내 7회) — count-only

### 7.7 Acceptance (7 AC)

| # | AC |
|---|---|
| AC1 | ClosedTrade Pydantic dataclass + FIFO matching |
| AC2 | TradeLedger PaperExecutor 통합 (fill loop hook) |
| AC3 | evaluate_consecutive_losses min_closed gating |
| AC4 | streak counting (trailing losses, win 시 reset) |
| AC5 | PaperRiskGate.check trigger + RiskGateBlocked + RiskGateEvent emit |
| AC6 | reason_code `CONSECUTIVE_LOSSES:streak_<n>` 형식 |
| AC7 | 5 required check green |

### 7.8 Codex 적용

7/7 채택 (Phase 2 시점에 detail review). ADR conflict 0/7.

## 8-11

(Phase 2 = risk/kill_switch.py + trade_ledger.py + enforcer.py + executor/paper.py.)
