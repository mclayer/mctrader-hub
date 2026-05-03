---
story_key: MCT-35
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-32
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-35: BacktestExecutor "would-have-rate-limited" recording

## 1. 사용자 요구사항 (verbatim, MCT-32 Epic)

> "MCT-32 Backtest recording — over-limit 시 block 안 함 (simulation 계속), RateLimitEvent (allowed=True + mode=backtest) 만 기록"

## 2. 도메인 해석

mctrader-engine BacktestExecutor 에 RateLimiter check 통합. ADR-007 D4 mode 분리 — Backtest 는 block 하지 않고 "would-have-rate-limited" 기록만 (strategy 분석 가능). Paper / Live 와 schema 동일 (RateLimitEvent).

## 3. 관련 ADR

- ADR-007 D4 (Backtest = recording only, ADR-007 D4 명시)
- ADR-002 (BacktestExecutor TradeExecutor Protocol)
- ADR-004 (RateLimitEvent ExecutionReport.events stream)
- 의존: MCT-33 freeze (OrderRateLimiter API), MCT-34 freeze (RateLimitEvent schema)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/executor/
└── backtest.py (extend)              # would-have-rate-limited recording (block X)
```

## 5-6. 요구사항

- BacktestExecutor 의 fill loop 에 RateLimiter check 추가
- over-limit 시:
  - RateLimitEvent emit (`allowed=False` 의미적이지만, mode="backtest" 로 의미 분명)
  - **block 하지 않고** order 진행 (simulation 계속)
- under-limit 시:
  - RateLimitEvent emit 안 함
  - 정상 submit + record

→ Backtest 의 RateLimitEvent 는 strategy 분석에 사용 가능 (예: "이 전략은 minute-window 에서 20+ orders 시도 = Live 시 차단될 가능성")

## 7. 설계 서사 (Codex 합성, Phase 2 시점에 구체화)

### 7.1 BacktestExecutor pre-trade hook (A1)

PaperExecutor 와 유사하지만 block 하지 않음:

```python
# In BacktestExecutor decision handler
if self._rate_limiter is not None:
    rl_decision = self._rate_limiter.check_order_create(now=bar.ts_utc)
    if not rl_decision.allowed:
        # Emit "would-have-rate-limited" but DO NOT block.
        self._events.append(
            RateLimitEvent(
                ts_utc=bar.ts_utc,
                decision=rl_decision,  # allowed=False (간주적)
                correlation_id=None,
            )
        )
        # Continue processing — strategy analysis 가능
    # Always record (whether allowed or not — backtest models real behavior)
    self._rate_limiter.record_order_create(now=bar.ts_utc)
```

**Note**: Backtest 도 record 호출. 이는 다음 같은 minute 의 후속 요청에 대한 누적 효과 검증 위해.

### 7.2 RateLimitEvent.allowed semantic in backtest (A2)

Backtest 의 RateLimitEvent.allowed 의 의미:
- `allowed=True`: 정책 한도 내 (정상)
- `allowed=False`: 한도 초과 (would-have-rate-limited) — Live 였으면 block 됐을 시도

mode="backtest" 가 schema 에 박제되므로, reader 는 allowed=False 의 의미를 "advisory" 로 해석.

### 7.3 Out-of-scope

- BacktestExecutor 의 cancel rate recording (Backtest 에서 cancel 은 거의 발생 X)
- Public REST recording in Backtest (ADR-007 D4 의 의도가 broker private endpoint 한도, REST 는 일반적 backfill 시점에만)

### 7.4 Acceptance (5 AC)

| # | AC |
|---|---|
| AC1 | BacktestExecutor 의 fill loop 에 RateLimiter check 추가 |
| AC2 | over-limit 시 RateLimitEvent emit (mode="backtest" + allowed=False) |
| AC3 | over-limit 시 simulation 계속 (block X) |
| AC4 | under-limit 시 RateLimitEvent emit 안 함 + record |
| AC5 | 5 required check green |

### 7.5 Codex 적용

Phase 2 시점에 detail review (선택). ADR conflict 0/7.

## 8-11

(Phase 2 = executor/backtest.py.)
