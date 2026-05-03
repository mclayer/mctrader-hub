---
story_key: MCT-34
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-32
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-34: PaperExecutor pre-trade RateLimiter hook + RateLimitDecision/Event schema

## 1. 사용자 요구사항 (verbatim, MCT-32 Epic)

> "MCT-32 engine integration — PaperExecutor 의 pre-trade hook 에 RateLimiter 통합 + RateLimitDecision schema + RateLimitEvent (correlation_id 로 RiskGateEvent 연결)"

## 2. 도메인 해석

mctrader-engine PaperExecutor 의 strategy decision → submit 사이에 RateLimiter check 추가. over-limit 시 pre-trade block + RateLimitEvent emit. RiskGateEvent 와 correlation_id 연결 (operator 가 추적 가능).

## 3. 관련 ADR

- ADR-007 D4 + D6 + D9
- ADR-002 (TradeExecutor Protocol unchanged)
- ADR-004 (RateLimitEvent + RateLimitDecision + ExecutionReport.events Union 확장)
- 의존: MCT-33 freeze (OrderRateLimiter API)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── executor/paper.py (extend)        # OrderRateLimiter hook + correlation_id
├── report/schema.py (extend)         # RateLimitDecision + RateLimitEvent + Event union
└── risk/enforcer.py (extend)         # PaperRiskGate ↔ RateLimiter correlation
```

## 5-6. 요구사항

- PaperExecutor 의 fill loop 에 pre-trade RateLimiter check 추가
- over-limit 시 PaperExecutor 가:
  - RateLimitEvent emit (allowed=False)
  - order submit 차단
  - PaperRiskGate.check 는 호출하지 않음 (이미 차단됨)
  - run continue (다음 closed bar 까지 대기)
- under-limit 시:
  - RateLimitEvent emit 안 함 (allowed=True)
  - record (counter update)
  - 정상 submit → RiskGateEvent 후행 가능

## 7. 설계 서사 (Codex 합성, Phase 2 시점에 구체화)

### 7.1 RateLimitDecision schema (A1)

```python
class RateLimitDecision(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    allowed: bool
    category: Literal["ORDER_CREATE", "CANCEL", "TOTAL_PRIVATE", "PUBLIC_REST"]
    scope: Literal["sec", "min", "day"]
    limit_window_seconds: int
    limit_value: int
    observed_count: int
    retry_after_ms: int
    mode: Literal["backtest", "paper", "live"]
    ts_utc: UTCDateTime
    policy_hash: str
    policy_version: str
```

### 7.2 RateLimitEvent schema (A2)

```python
class RateLimitEvent(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    kind: Literal["RateLimitEvent"] = "RateLimitEvent"
    ts_utc: UTCDateTime
    decision: RateLimitDecision
    correlation_id: str | None  # OrderEvent.order_id 또는 RiskGateEvent 의 식별자
```

ExecutionReport.events Union 확장:
```python
Event = Annotated[
    OrderEvent | StrategyDecision | RiskGateEvent | RateLimitEvent,
    Field(discriminator="kind"),
]
```

### 7.3 PaperExecutor pre-trade hook (A3)

```python
def _on_closed_bar(self, closed):
    # ... existing decision + StrategyDecision emit ...
    if decision.kind is DecisionKind.HOLD: return
    
    # NEW: RateLimit check before RiskGate
    if self._rate_limiter is not None:
        rl_decision = self._rate_limiter.check_order_create(now=closed.candle.ts_utc)
        if not rl_decision.allowed:
            self._events.append(
                RateLimitEvent(
                    ts_utc=closed.candle.ts_utc,
                    decision=rl_decision,
                    correlation_id=None,  # no order created
                )
            )
            return  # block submit, run continue
        # Also check total_private
        tp_decision = self._rate_limiter.check_total_private(now=closed.candle.ts_utc)
        if not tp_decision.allowed:
            self._events.append(RateLimitEvent(ts_utc=..., decision=tp_decision, correlation_id=None))
            return
    
    # Existing RiskGate check
    if self._risk_gate is not None: ...
    
    # Submit + RECORD on success
    self._submit_and_fill(decision, closed)
    if self._rate_limiter is not None:
        self._rate_limiter.record_order_create(now=closed.candle.ts_utc)
```

### 7.4 Correlation_id (A4)

- RateLimitEvent.correlation_id = None (over-limit 시 order 생성 X)
- under-limit 시 → submit → OrderEvent.order_id 발생 → 후속 RiskGateEvent 가 발생하면 그 event 의 correlation_id 에 OrderEvent.order_id 채움 (operator 추적용)

### 7.5 Out-of-scope

- Live mode integration (Live Epic)
- Cancel rate (cancel order = MCT-32 scope 외, 본 Epic 은 paper 의 cancel 이 적은 환경)

### 7.6 Acceptance (7 AC)

| # | AC |
|---|---|
| AC1 | RateLimitDecision Pydantic v2 frozen + 모든 fields |
| AC2 | RateLimitEvent + Event union 확장 (Backward compat) |
| AC3 | PaperExecutor pre-trade RateLimit check (RiskGate 전) |
| AC4 | over-limit 시 RateLimitEvent emit + submit block + run continue |
| AC5 | under-limit 시 normal flow + record_order_create 호출 |
| AC6 | TOTAL_PRIVATE check 도 동시 수행 (ORDER_CREATE 통과 후) |
| AC7 | 5 required check green |

### 7.7 Codex 적용

Phase 2 시점에 detail review (선택). ADR conflict 0/7.

## 8-11

(Phase 2 = executor/paper.py + report/schema.py + risk/enforcer.py.)
