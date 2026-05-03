---
story_key: MCT-32
status: phase:요구사항
component: hub
type: epic
related_stories: MCT-33, MCT-34, MCT-35, MCT-36
related_adrs: ADR-002, ADR-004, ADR-007
parent_epic: MCT-25 (predecessor)
---

# MCT-32: ADR-007 D4 Order rate limit (자체 throttle, pre-trade) (Epic)

## 1. 사용자 요구사항 (verbatim)

> "ㅇㅇ 그건 이제 codeforge가 트리거했을때 수행할 수 있도록 두고 mctrader는 mctrader의 일을 하자. codex 리뷰를 통해 sonnet decider로 수행하라" — 8 후속 candidate 중 Codex 추천 1순위 = **D4 Order rate limit** (Foundation dependency / Reversibility / Live mode prerequisite, bounded blast radius).

## 2. 도메인 해석

mctrader 의 **네 번째 implementation Epic** (MCT-12 Backtest, MCT-18 Paper, MCT-25 RiskGate full 다음). Live mode 의 prerequisite — 거래소 측 rate limit 위반 = API_BAN trigger 직결. 자체 throttle 로 broker side rate limit error 진입 전 차단.

핵심 가치 = (a) **Live mode prerequisite** — broker rate limit 보호 → 책임 있는 production 진입. (b) **Reversibility 최고** — throttle tuning 만으로 rollback, broker state 영향 X. (c) **Bounded blast radius** — pre-trade block 으로 strategy bug 의 cascade 차단.

## 3. 관련 ADR

| ADR | D4 적용 |
|---|---|
| ADR-002 | TradeExecutor Protocol unchanged (RateLimiter = pre-trade layer, RiskGate 와 분리) |
| ADR-004 | RateLimitEvent 신규 schema, RiskGateEvent v2 와 correlation_id 연결 |
| ADR-007 D4 | 4 limit category (Order create / Cancel / Total private / Public REST) hard threshold |
| ADR-007 D6 | KST midnight reset (daily counter — 300/day, 500/day) |
| ADR-007 D9 | RiskPolicy 확장 (rate_limit_* fields), policy_hash 통합 |

## 4. 관련 코드 경로 (4 신규 child Story 분담)

```
mctrader-engine/                       # MCT-33 (foundation: RateLimiter core)
└── src/mctrader_engine/risk/
    ├── rate_limiter.py (NEW)            # SlidingWindow + 4 category counter
    ├── policy.py (extend)                # rate_limit_* thresholds (12 fields)
    └── kill_switch.py (extend)           # ORDER_RATE_LIMIT trigger enum

mctrader-engine/                       # MCT-34 (engine integration)
└── src/mctrader_engine/
    ├── executor/paper.py (extend)        # PaperExecutor pre-trade RateLimiter hook
    ├── report/schema.py (extend)         # RateLimitDecision + RateLimitEvent schema
    └── risk/enforcer.py (extend)         # PaperRiskGate ↔ RateLimiter correlation_id

mctrader-engine/                       # MCT-35 (Backtest recording)
└── src/mctrader_engine/
    └── executor/backtest.py (extend)     # would-have-rate-limited recording (block X)

mctrader-market-bithumb/               # MCT-33 (Public REST throttle decorator)
└── src/mctrader_market_bithumb/
    └── rest_throttle.py (NEW)            # Public REST 5/sec self-throttle

mctrader-engine/                       # MCT-36 (sealing)
└── src/mctrader_engine/
    ├── calibration/rate_limit_baseline.py (NEW)  # 20-30% Bithumb 한도 baseline
    └── tests/test_rate_limit_e2e.py      # Epic E2E acceptance
```

## 5-6. 요구사항 / 외부 지식

- ADR-007 D4 4 limit category (hard 만, soft 없음):
  - Order create: 2/sec, 20/min, 300/day
  - Cancel: 3/sec, 30/min, 500/day
  - Total private: 10/sec, 300/min (별도 counter — order+cancel union 도출 X)
  - Public REST: 5/sec (mctrader-market-bithumb 의 REST adapter self-throttle)
- 거래소 공식 한도의 20-30% (Bithumb 기준, ADR-007 footnote). 보수적 정책.
- Algorithm: **sliding window** (hard cap + boundary precision 우세)
- Time source: 기존 `Clock` Protocol (`RealtimeClock` / `SimulatedClock`) 재사용
- KST midnight reset (daily counter): PaperRiskGate 와 동일 mechanism
- mode 별 동작:
  - Backtest: "would-have-rate-limited" 기록 (block X, simulation 계속)
  - Paper / Live: pre-trade block + RateLimitEvent emit (correlation_id 로 RiskGateEvent 연결)

## 7. 설계 서사 (Codex 7-area + Sonnet 합성)

### 7.1 End-to-end acceptance (A1 — 2 layer)

**Blocking AC** (Epic 종료 의무):

| # | AC | 검증 |
|---|---|---|
| B1 | 4 limit category 모두 enforce — Order create / Cancel / Total private / Public REST | pytest 4 fixture |
| B2 | Sliding window algorithm (hard cap + boundary precision) | unit test (boundary cross + drift) |
| B3 | Total private = order + cancel **별도 counter** (derived X) | counter independence test |
| B4 | KST midnight reset for daily counters (PaperRiskGate 와 동기화) | KST boundary test |
| B5 | Backtest = "would-have-rate-limited" 기록 (block X, simulation 계속) | BacktestExecutor test |
| B6 | Paper = pre-trade block + RateLimitEvent emit | PaperExecutor integration |
| B7 | RateLimitEvent + RiskGateEvent correlation_id 연결 | schema validation |
| B8 | Public REST 5/sec = mctrader-market-bithumb REST adapter self-throttle | rest_throttle test |
| B9 | RiskPolicy 확장 (12 신규 fields) + policy_hash 통합 | canonical_json + hash test |
| B10 | RateLimitDecision schema — allowed / category / scope / limit_window / limit_value / observed / retry_after_ms / mode / ts / policy_hash | pydantic validator |

**Calibration AC** (Bithumb 공식 한도 baseline 검증):

| # | metric | 의미 | gate |
|---|---|---|---|
| C1 | `rate_limit_threshold_baseline` | 정책 한도가 Bithumb 공식 한도의 20-30% 범위 내 | hard threshold validation |

**Demonstration AC**:

| # | AC | 검증 |
|---|---|---|
| D1 | mctrader-web Streamlit RateLimitEvent 시각화 = **MCT-31 분리** | manual review (defer) |

### 7.2 4 child Story 분해

```
              MCT-33 (foundation: RateLimiter core + Policy + Public REST)
              ┌────────────┴────────────┐
              ↓                         ↓
          MCT-34                    MCT-35 (parallel)
          (PaperExecutor            (BacktestExecutor
           pre-trade hook)           would-have-rate-limited)
              └────────────┬────────────┘
                           ↓
                       MCT-36 (sealing: Calibration + E2E)
```

| Story | repo | 의존 |
|---|---|---|
| MCT-33 | mctrader-engine + mctrader-market-bithumb | MCT-30 freeze (engine 0.6.0) |
| MCT-34 | mctrader-engine | MCT-33 freeze (RateLimiter API) |
| MCT-35 | mctrader-engine | MCT-33 freeze (parallel with 34) |
| MCT-36 | mctrader-engine | MCT-33 + MCT-34 + MCT-35 freeze (E2E) |

**Parallel start 후보** = MCT-34 + MCT-35 (MCT-33 freeze 후 동시 가능). MCT-36 = 통합 sealing.

### 7.3 Sliding window algorithm (A1, MCT-33)

**채택**: Sliding window (per category, per scope).

```python
class SlidingWindowCounter:
    def __init__(self, *, window_seconds: int, limit: int): ...
    def try_consume(self, *, now: datetime) -> tuple[bool, int]:
        """Returns (allowed, retry_after_ms). Drops timestamps older than window."""
```

**비채택**:
- Token bucket = burst tolerance 우세하지만 hard cap precision 약함
- Per-day counter (300, 500) = 하루치 timestamp deque 메모리 부담? 아니, sparse (300 건 정도) → 무관

**Time source 추상화**: 기존 `Clock` Protocol (`now()` 호출). RealtimeClock / SimulatedClock 모두 호환 → Backtest 의 simulated time 정확 적용.

### 7.4 Counter 구조 (A2, MCT-33)

```python
class OrderRateLimiter:
    """Per-category sliding window counter (ADR-007 D4).
    
    Total private 은 별도 counter — order create + cancel union 도출 X (Codex 권고).
    """
    
    def __init__(self, *, policy: RiskPolicy, clock: Clock): ...
    
    def check_order_create(self, *, now: datetime) -> RateLimitDecision: ...
    def check_cancel(self, *, now: datetime) -> RateLimitDecision: ...
    def check_total_private(self, *, now: datetime) -> RateLimitDecision: ...
    
    def record_order_create(self, *, now: datetime) -> None: ...
    def record_cancel(self, *, now: datetime) -> None: ...
    # total_private 은 record 가 아닌 별도 mechanism — order create / cancel 의 record 가 동시에 total_private window 도 update
```

### 7.5 Public REST self-throttle (A3, MCT-33, mctrader-market-bithumb)

**채택**: REST adapter 자기 repo 에서 self-throttle (5/sec).

**비채택**:
- mctrader-engine 에서 모든 REST 호출 wrap = cross-repo 위반 (ADR-008 boundary)
- mctrader-market 에서 Protocol 정의 = abstraction premature (Bithumb only)

```python
# mctrader-market-bithumb/rest_throttle.py
class RestThrottle:
    def __init__(self, *, limit_per_sec: int = 5): ...
    async def throttle(self) -> None: ...  # awaits if necessary

# REST adapter 가 매 호출 전 self.throttle.throttle() 호출
```

### 7.6 RateLimitDecision + RateLimitEvent schema (A4, MCT-34)

```python
class RateLimitDecision(BaseModel):
    allowed: bool
    category: Literal["ORDER_CREATE", "CANCEL", "TOTAL_PRIVATE", "PUBLIC_REST"]
    scope: Literal["sec", "min", "day"]
    limit_window_seconds: int
    limit_value: int
    observed_count: int
    retry_after_ms: int | None
    mode: Literal["backtest", "paper", "live"]
    ts_utc: datetime
    policy_hash: str
    policy_version: str

class RateLimitEvent(BaseModel):
    kind: Literal["RateLimitEvent"] = "RateLimitEvent"
    ts_utc: datetime
    decision: RateLimitDecision
    correlation_id: str | None  # 연결되는 RiskGateEvent 또는 OrderEvent 의 id
```

**ExecutionReport.events** 에 추가 (Event union 확장).

### 7.7 Mode 별 동작 (A5, MCT-34 + MCT-35)

| mode | RateLimit hard | 동작 |
|---|---|---|
| Backtest | over limit | "would-have-rate-limited" RateLimitEvent (`allowed=True` + `mode=backtest`), simulation 계속 |
| Paper | over limit | pre-trade block + RateLimitEvent (`allowed=False` + `mode=paper`) + RiskGateEvent correlation_id 연결 |
| Live | over limit | pre-trade block + RateLimitEvent (`allowed=False` + `mode=live`) — Live Epic 시점에 broker error code 매핑 추가 |

### 7.8 Out-of-scope (확정 거부)

| 항목 | MCT-32 미포함 | 이유 |
|---|---|---|
| Broker side rate limit error code mapping | ✗ | Live Epic 시점에 통합 |
| Per-symbol rate limit | ✗ | Multi-symbol Epic |
| Retry / backoff strategy | ✗ | 별도 Story (RateLimit 은 block + retry_after_ms 만, retry policy 는 strategy/runner 책임) |
| Public REST mode 별 차별화 | ✗ | 5/sec hard, mode 무관 |
| Streamlit RateLimitEvent dashboard | ✗ | MCT-31 분리 |
| Token bucket algorithm | ✗ | sliding window 채택 (boundary precision 우세) |
| RateLimit policy WFO 재튜닝 | ✗ | 별도 Epic |

### 7.9 CFP-60 debut-audit checklist

각 child Phase 2 merge 직후:
- **lane-progression** (rate limit 의 mode-aware 동작 evidence)
- **decision-table** (4 category × 3 scope = 12 threshold 결정 표)
- **workflow-invariant** (ADR-007 D4 + D6 KST reset + D9 policy_hash 통합)
- **contract-schema** (RateLimitDecision + RateLimitEvent schema, ExecutionReport.events 확장)

### 7.10 Phase 1 / Phase 2 분담

**Phase 1** (본 Epic Story):
- 본 Epic doc + 4 child stub (MCT-33 ~ MCT-36) registration
- AC freeze (B1~B10 + C1 + D1)
- Algorithm freeze: **sliding window**
- Time source 결정: 기존 Clock Protocol 재사용
- Total private = separate counter
- Public REST 위치: mctrader-market-bithumb self-throttle
- RateLimitEvent + correlation_id 결정
- Phase 1 PR

**Phase 2** (child Story PR):
- 4 신규 issue Phase 2 implementation
- 각 child = Codex review (선택, micro task 는 skip 가능) → 합성 → PR

### 7.11 Codex 적용

7/7 area 채택. ADR conflict 0/7 (D4 가 ADR-007 D4 의 구체화, 충돌 없음).

## 8-11

(Phase 2 = 4 child Story PR 분담. 본 Epic Story 자체는 doc-only.)
