---
story_key: MCT-36
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-32
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-36: RateLimit Calibration C1 + Epic E2E + Bithumb baseline (sealing)

## 1. 사용자 요구사항 (verbatim, MCT-32 Epic)

> "MCT-32 sealing — Calibration C1 (Bithumb 공식 한도의 20-30% baseline) + Epic E2E acceptance test (4 limit category × 3 scope × 3 mode coverage)"

## 2. 도메인 해석

MCT-32 통합 sealing Story. Bithumb 공식 한도와 정책 한도 비교 검증 (20-30% range 의무) + 4 mode-aware E2E test. ADR-006 promotion gate "rate_limit_violations = 0" 검증 mechanism 추가.

## 3. 관련 ADR

- ADR-007 D4 (Bithumb 공식 한도 reference, 정책 한도 = 20-30% range)
- ADR-006 (promotion gate "rate_limit_violations = 0")
- ADR-002 (mode-aware integration)
- ADR-004 (RateLimitEvent + CalibrationMetrics extension)
- 의존: MCT-33 + MCT-34 + MCT-35 freeze

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── calibration/rate_limit_baseline.py (NEW)  # Bithumb 한도 비교
└── tests/test_rate_limit_e2e.py (NEW)        # Epic E2E acceptance
```

## 5-6. 요구사항

- Bithumb 공식 한도 (ADR-007 footnote 기준):
  - Order create: 10/sec, 100/min, 1500/day (가정 값, 실제 ADR 인용 시 정확화 의무)
  - Cancel: 10/sec, 100/min, 1500/day
  - Total private: 30/sec, 1000/min
  - Public REST: 20/sec
- 정책 한도가 위 한도의 20-30% range 내 의무
- E2E test:
  - 4 mode-aware scenario (backtest record / paper block / paper-then-recover / live stub)
  - 3 category (ORDER_CREATE / CANCEL / TOTAL_PRIVATE)
  - sliding window precision test (boundary cross + retry_after_ms 정확)

## 7. 설계 서사 (Codex 합성, Phase 2 시점에 구체화)

### 7.1 RateLimitBaseline (A1)

```python
@dataclass(frozen=True)
class BithumbOfficialLimit:
    order_create_per_sec: int = 10
    order_create_per_min: int = 100
    order_create_per_day: int = 1500
    cancel_per_sec: int = 10
    cancel_per_min: int = 100
    cancel_per_day: int = 1500
    total_private_per_sec: int = 30
    total_private_per_min: int = 1000
    public_rest_per_sec: int = 20

class RateLimitBaselineCheck(BaseModel):
    policy_limit: int
    official_limit: int
    ratio: Decimal  # policy / official
    in_range: bool  # 0.20 <= ratio <= 0.30
    category: str
    scope: str

def validate_policy_baseline(policy: RiskPolicy) -> list[RateLimitBaselineCheck]:
    """모든 9 (categories × scopes) 비교, in_range = ADR-007 D4 conformance"""
```

### 7.2 ExecutionReport.summary 확장 (A2)

```python
class SummaryStats(BaseModel):
    # ... existing ...
    rate_limit_violations_count: int = 0  # paper/live block 발생 횟수
    rate_limit_warnings_count: int = 0     # backtest would-have-rate-limited 횟수
```

ADR-006 promotion gate: `rate_limit_violations_count == 0` 검증.

### 7.3 E2E test scenarios (A3)

`test_rate_limit_e2e.py`:
- scenario_paper_order_create_per_sec_block: 3 orders within 1s → 3rd blocked + RateLimitEvent
- scenario_paper_total_private_block: 11 mixed (order+cancel) within 1s → 11th blocked
- scenario_backtest_records_no_block: 3 orders within 1s → 3rd recorded + simulation 계속
- scenario_kst_midnight_daily_reset: day 1 endpoint → day 2 fresh quota
- scenario_policy_baseline_in_range: validate_policy_baseline 9/9 in_range

### 7.4 Out-of-scope

- WFO-based threshold 재튜닝 (별도 Epic)
- Per-symbol baseline (Multi-symbol Epic)
- Bithumb 공식 한도 자체 변경 추적 (manual ADR amendment 의무)

### 7.5 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | RateLimitBaselineCheck 9/9 in_range (20-30%) |
| AC2 | SummaryStats.rate_limit_violations_count + warnings_count |
| AC3 | E2E paper order_create per_sec block scenario |
| AC4 | E2E paper total_private block scenario |
| AC5 | E2E backtest records no block scenario |
| AC6 | E2E KST midnight daily reset (자연 sliding evidence) |
| AC7 | ADR-006 promotion gate (rate_limit_violations_count == 0) |
| AC8 | 5 required check green |

### 7.6 Codex 적용

Phase 2 시점에 detail review (선택). ADR conflict 0/7.

## 8-11

(Phase 2 = calibration/rate_limit_baseline.py + tests/test_rate_limit_e2e.py.)
