---
story_key: MCT-7
status: phase:요구사항
component: risk
type: brainstorm
related_adr: ADR-007
---

# MCT-7: Kill switch / Drawdown limit / Max exposure 정책 (RiskGate threshold)

## 1. 사용자 요구사항 (verbatim)

mctrader 의 Kill switch / drawdown limit / max exposure 정책 (live + paper 적용). ADR-002 D4 (RiskGate 3 mode 동일 interface) + ADR-006 promotion gate 의 \"risk violation 0\" criterion 의 구체화.

## 2. 도메인 해석

ADR-002 / ADR-006 baseline 위에 5 kill switch trigger + drawdown 정의 + exposure / order rate 한도 + SL/TP enforce + reset / recovery + risk policy versioning 박제. **Personal-platform** (1억 이하 KRW 계정) 단계 default 명시.

## 3. 관련 ADR

- ADR-007 ([`../adr/ADR-007-risk-gate.md`](../adr/ADR-007-risk-gate.md))
- baseline: ADR-002 D4 / ADR-006 D6/D7
- 향후: MCT-8 (secret 관리 — risk policy versioning 의 amend 권한)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader/risk/
├── gate.py                # RiskGate interface + 3 mode dispatch
├── triggers.py            # 5 kill switch trigger
├── drawdown.py            # strategy + portfolio dual
├── exposure.py            # gross / position / symbol concentration
├── order_rate.py          # per-sec / per-min / per-day limit
├── stop_loss.py           # catastrophic_stop + intended_stop_loss metadata
├── reset.py               # daily / weekly KST 00:00
├── recovery.py            # soft / hard / critical lifecycle
└── policy.py              # risk_policy_version + hash + amendment
```

## 5-6. 요구사항 / 외부 지식

Reference: SEC Rule 15c3-5 (pre-trade threshold) / CFTC automated trading risk controls / FIA best practices / Upbit rate limit (주문 8/sec, quotation 10/sec, 429/418) / Bithumb rate limit (주문 관련 10/sec 초과 제한).

## 7. 설계 서사 (요약)

### 7.1 5 Kill switch trigger

| Category | Soft | Hard | 3 mode 적용 |
|---|---|---|---|
| MAX_DAILY_LOSS | -2% active capital | -3% active capital | Backtest=record / Paper+Live=block |
| DRAWDOWN_LIMIT | strategy peak -3% / portfolio rolling 24h -3% | strategy peak -5% / portfolio peak -4% | 동일 |
| CONSECUTIVE_LOSSES | 5 (min 10 closed trades) | 7 | 동일 |
| UNUSUAL_ACTIVITY | order reject rate >20%/5min / market data stale >3s | duplicate client_order_id 1회 / opposite orders within 1s 3회 / reject rate >40% / stale >10s / balance mismatch >0.5% | 동일 |
| EXTERNAL_SIGNAL | market data outage 30s+ | manual kill / API ban / key compromise | manual ack 의무 |

**Soft**: 신규 진입 금지 + 포지션 축소만 허용.
**Hard**: 전체 block + open order cancel.

### 7.2 Drawdown — strategy + portfolio dual

| 축 | 정의 |
|---|---|
| peak drawdown | run 시작 이후 equity HWM 대비 현재 하락률 |
| rolling drawdown | 최근 24h / 7d window HWM 대비 |
| absolute loss | 기준 capital 대비 실현+미실현 손실 KRW |

**Strategy + portfolio dual 계산**. 충돌 시 **portfolio 우선** (개인 계정 = 수동 보유분 / 외부 입출금 / 다른 exchange exposure 가능).

주문 허용 = `strategy_check == pass AND portfolio_check == pass`.

### 7.3 Exposure — spot only, leverage 1.0

```
gross_exposure = spot_position_value + open_buy_notional + open_sell_notional_risk_adjusted

threshold:
  gross / active_capital ≤ 60% soft / 80% hard
  single_order_notional ≤ min(active_capital × 2%, 500K KRW) soft / min(5%, 1,500K KRW) hard
  symbol_concentration ≤ 20% soft / 30% hard
  KRW_cash_min ≥ 20%
  per-side bias (open buy + spot inventory) ≤ 80% active capital
```

대출 / 선물 / 마진 = MCT-7 scope 외 (Personal-platform 단계).

### 7.4 Order rate limit (자체 제한 — 거래소 공식의 20-30%)

| 작업 | 자체 제한 | Upbit 공식 | Bithumb 공식 |
|---|---:|---|---|
| Order create / sec | 2 | 8 | 10 (주문 관련) |
| Order create / min | 20 | - | - |
| Order create / day | 300 | - | - |
| Cancel / sec | 3 | 8 | 10 |
| Cancel / min | 30 | - | - |
| Cancel / day | 500 | - | - |
| Total private / sec | 10 | 30 | 140 |
| Total private / min | 300 | - | - |
| Public REST / sec | 5 | 10 | 150 |

WebSocket 우선. Backtest = \"would-have-rate-limited\" violation 기록.

### 7.5 SL / TP enforce

**RiskGate 의무 enforce**:
- `intended_stop_loss_pct` 또는 `max_loss_krw` metadata 의무 (없으면 Paper/Live block, Backtest violation)
- `catastrophic_stop` (RiskGate 최후방어선): symbol position entry basis 대비 -3.0% 또는 position notional 대비 -1.0× active_capital 손실 중 먼저
- `max_position_age` (default 24h hard, 전략별 조정 가능)
- `price_gap_guard` (시장가성 주문 예상 체결가가 mid 대비 1.0% 이상 불리 시 block)

**Strategy 위임** (RiskGate 미강제):
- TP 부재 = violation 아님 (개인 spot 자동매매 = TP 강제 시 다양성 손실)
- SL 미세조정 (e.g. trailing / time-stopped) 은 strategy 책임. RiskGate = catastrophic floor 만.

### 7.6 Reset

- **Daily reset**: KST 00:00:00. Reset 대상 = 일일 손실 / 일일 주문 수 / consecutive intraday counters. **Reset 안 함**: peak HWM / weekly drawdown.
- **Weekly reset**: 월요일 KST 00:00:00. Weekly counters / rolling 7d window 별개 (시간 경과로 자연 빠짐).
- Reset = kill switch 자동 해제 안 함 (recovery 별도).

### 7.7 Recovery 3-tier

| Tier | 자동 / Manual | 조건 |
|---|---|---|
| **soft_stop** | 자동 | 15분 cooldown + health check pass 5분 |
| **hard_stop** | manual ack | operator_ack + risk_snapshot + open_orders_reconciled + positions_reconciled + cooldown ≥30min + risk_policy_hash unchanged |
| **critical_stop** | manual + key rotation | key compromise / reconcile mismatch >2% / unknown position / withdrawal anomaly |

같은 날 hard_stop 2회 = 다음 daily reset 후에도 manual override 없이는 재개 안 함.

Recovery 후 첫 1시간 = **reduced mode** (max order notional 50% / max exposure 50% / order rate 50%).

### 7.8 Capital lock

```
active_capital = min(account_equity × 20%, 10,000,000 KRW)
reserve_capital = remaining (RiskGate portfolio drawdown 에 포함, 신규 주문 재원 미사용)

active_capital 상향 = versioned amendment 의무 + Live 6개월+ 경험 + violation 임계 이하 조건
```

### 7.9 Risk policy versioning

ADR-006 D10 의 `risk_policy_hash` lock per run_id.

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

Run 중 threshold 변경 = 금지. 필요 시 amendment:
- **완화 amendment** (e.g. max exposure 60→80) = Live 에서 신규 run_id 요구
- **강화 amendment** (e.g. 80→60) = 같은 run_id 적용 가능, `risk_policy_hash_amended_from` 박제

Promotion gate (ADR-006 D6/D7) 의 \"risk violation 0\" = `hard + critical = 0` AND `soft = 0`. `info` 만 허용. Paper 에서 1회라도 block 발생 = Live 승격 불가.

### 7.10 Personal-platform starting threshold (확정값)

| 항목 | Soft | Hard |
|---|---|---|
| Daily loss (active capital) | -2% | -3% |
| Portfolio daily loss | — | min(-2%, -1M KRW) |
| Strategy peak drawdown | -3% | -5% |
| Portfolio peak drawdown | — | -4% |
| Rolling 24h portfolio drawdown | — | -3% |
| Gross exposure | 60% | 80% |
| Single order notional | min(2%, 500K) | min(5%, 1,500K) |
| Symbol concentration | 20% | 30% |
| Catastrophic position stop | — | -3% from entry |
| Order create | — | 2/sec, 20/min, 300/day |
| Cancel | — | 3/sec, 30/min, 500/day |
| Consecutive losses | 5 (min 10 closed) | 7 |
| Active capital | — | min(equity×20%, 10M KRW) |
| Max position age | — | 24h |
| Price gap guard | — | 1.0% from mid |

운영 표본 누적 후 versioned amendment 만 허용.

### 7.11 Codex 적용

채택률 16/16. Sonnet 거부 0.

## 8-11

(Phase 2 N/A — doc-only Story.)
