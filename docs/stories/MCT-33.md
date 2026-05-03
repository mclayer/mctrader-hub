---
story_key: MCT-33
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-32
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-33: RateLimiter core + RiskPolicy 확장 + Public REST self-throttle (foundation)

## 1. 사용자 요구사항 (verbatim, MCT-32 Epic)

> "MCT-32 foundation — sliding window algorithm + 4 limit category counter + RiskPolicy 확장 + mctrader-market-bithumb Public REST 5/sec self-throttle"

## 2. 도메인 해석

mctrader-engine 0.6.0 RiskPolicy (MCT-26 도입) 의 D4 rate limit thresholds 확장. SlidingWindowCounter 알고리즘 + OrderRateLimiter 4 category counter + mctrader-market-bithumb 의 RestThrottle decorator. MCT-34 / MCT-35 / MCT-36 모두 이 foundation 기반 동작.

## 3. 관련 ADR

- ADR-007 D4 (4 limit category hard threshold)
- ADR-007 D6 (KST midnight reset for daily counter)
- ADR-007 D9 (RiskPolicy versioning, policy_hash 통합)
- ADR-002 (TradeExecutor Protocol unchanged, RateLimiter = pre-trade layer)
- 의존: MCT-30 freeze (engine 0.6.0)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── rate_limiter.py (NEW)         # SlidingWindowCounter + OrderRateLimiter
├── policy.py (extend)            # rate_limit_* fields (12 신규)
└── kill_switch.py (extend)       # ORDER_RATE_LIMIT TriggerName

mctrader-market-bithumb/src/mctrader_market_bithumb/
└── rest_throttle.py (NEW)        # async RestThrottle decorator (5/sec)
```

## 5-6. 요구사항

- SlidingWindowCounter: window_seconds + limit, deque[datetime] timestamp 추적
- OrderRateLimiter: 3 category (ORDER_CREATE, CANCEL, TOTAL_PRIVATE) × 3 scope (sec, min, day)
  - ORDER_CREATE: 2/sec, 20/min, 300/day (ADR-007 D4)
  - CANCEL: 3/sec, 30/min, 500/day
  - TOTAL_PRIVATE: 10/sec, 300/min (별도 counter)
- KST midnight reset (daily counter): 기존 PaperRiskGate 와 동일 mechanism
- RiskPolicy 확장 (12 신규 fields):
  ```
  order_create_per_sec: int = 2 / order_create_per_min: int = 20 / order_create_per_day: int = 300
  cancel_per_sec: int = 3 / cancel_per_min: int = 30 / cancel_per_day: int = 500
  total_private_per_sec: int = 10 / total_private_per_min: int = 300
  public_rest_per_sec: int = 5
  ```
  + `policy_version: str = "mct-32-v1"`

## 7. 설계 서사 (Codex 합성, Phase 2 시점에 구체화)

### 7.1 SlidingWindowCounter (A1)

```python
class SlidingWindowCounter:
    def __init__(self, *, window_seconds: int, limit: int): ...
    def try_consume(self, *, now: datetime) -> tuple[bool, int]:
        """Drops timestamps older than window_seconds before now.
        Returns (allowed, retry_after_ms). retry_after_ms = 0 if allowed."""
    def record(self, *, now: datetime) -> None:
        """Append timestamp (call AFTER try_consume returns True)."""
```

### 7.2 OrderRateLimiter (A2)

```python
class OrderRateLimiter:
    def __init__(self, *, policy: RiskPolicy, clock: Clock): ...
    
    def check_order_create(self, *, now: datetime) -> RateLimitDecision: ...
    def check_cancel(self, *, now: datetime) -> RateLimitDecision: ...
    def check_total_private(self, *, now: datetime) -> RateLimitDecision: ...
    
    def record_order_create(self, *, now: datetime) -> None:
        # records both ORDER_CREATE counters AND TOTAL_PRIVATE counters
    def record_cancel(self, *, now: datetime) -> None:
        # records both CANCEL counters AND TOTAL_PRIVATE counters
    
    @property
    def policy_hash(self) -> str: ...  # for policy_hash propagation
```

**Total private = 별도 counter** (Codex 권고). order_create 의 record 가 ORDER_CREATE 와 TOTAL_PRIVATE 모두 update.

### 7.3 KST midnight reset (A3)

PaperRiskGate 의 daily bucket reset mechanism 재사용. SlidingWindowCounter 의 window_seconds=86400 일 때, KST midnight cross 시점에 deque clear (또는 그냥 sliding window 자체로 자연 처리 — daily counter 도 sliding 방식이면 reset 불필요).

**채택**: 자연 sliding (KST 수동 reset 불필요). day window = trailing 86400 sec.

### 7.4 mctrader-market-bithumb RestThrottle (A4)

```python
class RestThrottle:
    def __init__(self, *, limit_per_sec: int = 5): ...
    async def throttle(self) -> None:
        """Block (await asyncio.sleep) if necessary to keep 5/sec rate."""
```

REST adapter 의 매 HTTP call 전 `await self._throttle.throttle()` 호출.

### 7.5 RiskPolicy 확장 (A5)

기존 RiskPolicy (MCT-26) 에 12 신규 fields 추가. policy_version "mct-25-v1" → "mct-32-v1" amendment_from chain.

`canonical_json()` 자동 sort_keys 통합 — 신규 fields 도 같은 hash 영향.

### 7.6 Out-of-scope

- broker error code mapping (Live Epic)
- per-symbol rate limit (Multi-symbol Epic)
- retry / backoff strategy (별도 Story)

### 7.7 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | SlidingWindowCounter try_consume + record + retry_after_ms 정확 |
| AC2 | OrderRateLimiter 3 category × 3 scope (사실상 8 unique counter — daily 가 없는 total_private 빼고) |
| AC3 | TOTAL_PRIVATE = order_create + cancel record 시 동시 update |
| AC4 | RiskPolicy 12 신규 fields + canonical_json hash 변경 |
| AC5 | KST midnight 자연 sliding (수동 reset 불필요 evidence) |
| AC6 | mctrader-market-bithumb RestThrottle async 5/sec |
| AC7 | TriggerName.ORDER_RATE_LIMIT enum 추가 |
| AC8 | 5 required check green |

### 7.8 Codex 적용

Phase 2 시점에 detail review (선택). ADR conflict 0/7.

## 8-11

(Phase 2 = risk/rate_limiter.py + policy.py + mctrader-market-bithumb/rest_throttle.py.)
