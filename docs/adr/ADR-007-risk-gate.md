---
adr_id: ADR-007
title: RiskGate — Kill switch / Drawdown / Exposure / Order rate / Recovery / Policy versioning
status: Accepted
date: 2026-05-02
related_story: MCT-7
category: risk
---

# ADR-007: RiskGate threshold + 5 kill switch trigger + Personal-platform default

## Status

Accepted — 2026-05-02. MCT-7 Phase 1 PR.

## Context

ADR-002 D4 (3 mode 동일 RiskGate) + ADR-006 D6/D7 (promotion gate \"risk violation 0\") 구체화.

Reference: SEC Rule 15c3-5 / CFTC automated trading / FIA best practices / Upbit Bithumb rate limit 공식.

## Decision

### D1. 5 Kill switch trigger

| Trigger | Soft | Hard |
|---|---|---|
| MAX_DAILY_LOSS | -2% active capital | -3% |
| DRAWDOWN_LIMIT | strategy peak -3% / portfolio rolling 24h -3% | strategy peak -5% / portfolio peak -4% |
| CONSECUTIVE_LOSSES | 5 (min 10 closed) | 7 |
| UNUSUAL_ACTIVITY | reject rate >20%/5min / data stale >3s | duplicate client_order_id 1 / opposite orders/1s 3회 / reject >40% / stale >10s / balance mismatch >0.5% |
| EXTERNAL_SIGNAL | data outage 30s+ | manual kill / API ban / key compromise (manual ack 의무) |

**Soft = 신규 진입 금지 + 축소만**. **Hard = 전체 block + cancel**.

3 mode 적용:
- Backtest = `risk_violation` event 기록 (시뮬 계속)
- Paper / Live = pre-trade block

### D2. Drawdown — strategy + portfolio dual, portfolio 우선

3 축: peak / rolling / absolute. 둘 다 계산, 보수적 결과 적용. 주문 허용 = `strategy_check == pass AND portfolio_check == pass`.

### D3. Exposure — spot only, leverage 1.0

```
gross_exposure / active_capital ≤ 60% soft / 80% hard
single_order_notional ≤ min(2%×AC, 500K) soft / min(5%×AC, 1.5M) hard
symbol_concentration ≤ 20% soft / 30% hard
KRW_cash_min ≥ 20%
per-side bias ≤ 80% AC
```

Margin / 선물 = scope 외.

### D4. Order rate limit (자체 제한)

| 작업 | Hard |
|---|---:|
| Order create | 2/sec, 20/min, 300/day |
| Cancel | 3/sec, 30/min, 500/day |
| Total private | 10/sec, 300/min |
| Public REST | 5/sec |

거래소 공식 한도의 20-30%. WebSocket 우선. Backtest = \"would-have-rate-limited\" 기록.

### D5. SL / TP enforce 계층

**RiskGate 의무**:
- `intended_stop_loss_pct` 또는 `max_loss_krw` metadata 의무 (없으면 block / violation)
- `catastrophic_stop` = entry -3% 또는 position notional -1.0× active capital
- `max_position_age` = 24h
- `price_gap_guard` = mid 대비 1.0% 이상 불리

**Strategy 위임** (RiskGate 미강제):
- TP 부재 = violation 아님
- SL 미세조정 (trailing / time-based) = strategy 책임. RiskGate = catastrophic floor only.

### D6. Reset

- Daily KST 00:00 = 일일 손실 / 주문 수 / intraday counters. **HWM / weekly drawdown reset 안 함**.
- Weekly KST 월요일 00:00 = weekly counters. rolling 7d 별개.
- Reset ≠ kill switch 자동 해제.

### D7. Recovery 3-tier

| Tier | Auto / Manual | 조건 |
|---|---|---|
| soft_stop | 자동 | 15분 cooldown + health check pass 5분 |
| hard_stop | manual ack | operator_ack + risk_snapshot + open_orders_reconciled + positions_reconciled + ≥30min cooldown + risk_policy_hash unchanged |
| critical_stop | manual + key rotation | key compromise / mismatch >2% / unknown position / withdrawal anomaly |

같은 날 hard_stop 2회 = 다음 daily reset 후 manual override 의무.

Recovery 첫 1h = **reduced mode** (notional / exposure / rate 모두 50%).

### D8. Capital lock

```
active_capital = min(account_equity × 20%, 10,000,000 KRW)
reserve_capital = remaining (portfolio drawdown 계산 포함, 신규 주문 재원 미사용)

상향 amendment = Live 6개월+ 경험 + violation 임계 이하
```

### D9. Risk policy versioning

```python
@dataclass(frozen=True)
class RiskPolicy:
    version: str
    canonical_json: str
    hash: str
    effective_at: datetime
    operator: str
    mode: Literal["backtest", "paper", "live"]
    exchange: str
    amendment_from: str | None
```

Run 중 threshold 변경 = 금지.
- **완화 amendment** = Live 신규 run_id 요구
- **강화 amendment** = 같은 run_id, `risk_policy_hash_amended_from` 박제

ADR-006 promotion \"risk violation 0\" = `hard + critical = 0 AND soft = 0`. `info` 만 허용.

### D10. Personal-platform starting threshold (확정값)

(Story §7.10 의 표와 동일.)

## Alternatives Considered

### A1. Strategy-level drawdown only (portfolio 미고려)
- **기각**: 개인 계정 수동 보유분 / 외부 입출금 / 다른 exchange exposure 미반영. portfolio 우선 의무.

### A2. Daily 5% drawdown limit (사용자 보편적 기준)
- **기각**: KRW spot 1억 이하 personal 단계는 -3% hard 가 더 합리적. promotion gate \"violation 0\" 와 align. 6개월+ 후 amendment 가능.

### A3. RiskGate 가 모든 SL/TP enforce
- **기각**: strategy alpha 자유도 손실. catastrophic floor 만 RiskGate 의무.

### A4. Kill switch 자동 recovery (전체)
- **기각**: 손실 기반 hard stop 의 root cause 자동 구분 불가능 (시장 / 전략 / 데이터). manual ack 의무.

### A5. Backtest 에 RiskGate 미적용
- **기각**: ADR-002 D4 invariant. 동일 interface 강제. Backtest = block 대신 violation 기록 (전략 분석 가능).

### A6. Paper 에 RiskGate 완화
- **기각**: Paper = Live rehearsal. 완화 시 promotion gate 의미 손실.

### A7. Hash 비밀성 의존 risk policy lock
- **기각**: hash = audit. 실질 lock = run_id 단위 + amendment lifecycle.

## Consequences

### C1. Backtest 도 RiskGate 통과 의무
strategy 가 risk-incompatible 행동 시 backtest violation 기록 → promotion 차단.

### C2. ADR-006 promotion gate 와 직접 연결
violation severity = info / soft / hard / critical. Paper 의 1회 block = Live 승격 불가.

### C3. Personal-platform starting threshold 확정
(Story §7.10 표). Versioned amendment 만 허용.

### C4. Active capital lock 정책
1억 이하 personal 계정 = active 20% / 10M KRW 중 작은 값. reserve 보호.

### C5. Risk policy versioning + audit
모든 event log 에 `risk_policy_hash` 박제. promotion gate = hash + violation count 검증.

### C6. MCT-8 dependency
risk policy amendment 권한 = MCT-8 의 secret + operator authority 와 연계.

## Cross-references

- ADR-002 D4 / ADR-006 D6/D7 — baseline
- MCT-8 — secret + operator authority
