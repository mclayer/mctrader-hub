---
adr_id: ADR-004
title: Slippage / Fee / Latency 모델 상세 + 3 mode 적용 차이
status: Accepted
date: 2026-05-02
related_story: MCT-4
category: backtest
supersedes: []
amends: []
---

# ADR-004: Slippage / Fee / Latency 모델 + 3 mode 적용 + Calibration

## Status

**Accepted** — 2026-05-02. MCT-4 Phase 1 PR.

## Context

ADR-002 / ADR-003 의 baseline (composite slippage / ExecutionSimulator / ExchangeCapabilities / 8-state lifecycle) 위에 formal model 박제.

핵심 framing (Codex push-back): \"가장 중요한 결정 = 정교한 확률 모델보다 나중에 실제 체결로 보정 가능한 audit trail\". 즉 **ExecutionReport schema 공유 + calibration mechanism**.

## Decision

### D1. Composite slippage 공식

```
slippage_bps = base_bps
             + size_factor * f(x)
             + volatility_factor * g(v)
             + tick_bps_adjustment

x = notional_krw / liquidity_ref_krw
v = recent_volatility_bps   # EWMA close-to-close, half-life 10 bars

f(x) = 0                                       if x ≤ 0
       sqrt(x)                                  if 0 < x ≤ 1
       1 + overflow_slope * (x-1)^1.25          if x > 1
       capped at f_cap=8.0

g(v) = log(1 + max(v,0) / vol_ref_bps) / log(2)
       capped at g_cap=4.0

tick_bps_adjustment = effective tick rounding (KRW 호가 단위 적용)
```

근거: sqrt impact (Almgren-Chriss / Kyle inspired) — 작은 주문 underweight + 큰 주문 oversimplify 회피. log-saturating volatility — 단일 outlier candle 의 backtest 왜곡 회피.

### D2. Liquidity_ref 3-level

- **L1** top-of-book size (orderbook 가용)
- **L2** 1-min traded notional median × participation_limit (default 0.10) over lookback (default 60 bars) — **MCT-4 baseline**
- **L3** orderbook depth integral within depth_bps of best quote — high-fidelity, MCT-9 의존

### D3. Parameter default

| Parameter | Default | Confidence |
|---|---:|---|
| base_bps | 1.0 | L-M |
| size_factor | 6.0 bps | L |
| volatility_factor | 2.0 bps | L |
| vol_ref_bps | 50 | M |
| EWMA half-life | 10 bars | M |
| liquidity fallback window | 60 1-min bars | M |
| participation_limit | 0.10 | M |
| depth_bps | 10 | M |
| overflow_slope | 1.5 | L |
| f_cap | 8.0 | M |
| g_cap | 4.0 | M |

### D4. Fee schedule

baseline:
- Bithumb KRW: maker/taker 0.04% (4 bps) — confidence M
- Upbit KRW: maker/taker 0.05% (5 bps) — confidence M

```python
@dataclass(frozen=True)
class FeeSchedule:
    exchange: str
    market: str           # KRW
    maker_bps: float
    taker_bps: float
    order_type_overrides: dict[OrderType, FeeOverride]
    vip_tier: int
    event_code: str | None
    valid_from: datetime
    valid_to: datetime | None
    source: str           # public_doc / account_api / event_announcement / user_override
    confidence: Literal["H", "M", "L"]
```

Override priority: **live API actual fee > account endpoint > user override > event schedule > default**.

Run 단위 lock per `run_id`. 과거 backtest 를 오늘 fee 로 재계산 시 회귀 비교 무의미.

Maker/taker 판정: limit 주문이라도 cross spread = taker. **Candle-only backtest 의 보수적 default = taker fee**.

### D5. Latency model

```python
ConstantLatency(ms: int)
GaussianLatency(mean_ms: float, std_ms: float, min_ms: int, max_ms: int, seed: int)
MeasuredDistribution(samples_ms: list[int], seed: int)
```

| Mode | Submit latency | Ack latency | Application |
|---|---|---|---|
| Backtest | 50ms deterministic | 50ms deterministic | composite simulator |
| Paper | truncated Gaussian(mean=50, std=20, min=10, max=200) seeded | same | simulator + orderbook adjustment |
| Live | N/A (model 미적용) | N/A | measured timestamp audit only |

**Backtest latency 와 lookahead bias 연결**: \"signal_time + decision_latency + submit_latency 이후 첫 executable market state 만 사용\". Candle-only backtest = 다음 bar open 또는 다음 tick 기준.

### D6. Partial fill probability

```
threshold = 0.30  # x = notional / liquidity_ref
p_partial(x) = 0                                  if x ≤ threshold
               min(p_max, 1 - exp(-k * (x - threshold)))   if x > threshold

k = 1.8
p_max = 0.85

if partial:
  fill_ratio = clamp(liquidity_ref / notional * U(0.6, 1.0),
                     min_fill_ratio=0.10, 1.0)
```

Backtest deterministic mode = `U` 는 `(run_id, order_id, symbol, ts)` seeded pseudo-random.

**Recovery policy** default = `cancel_remainder` (잔여 cancel + 체결분 포지션 반영). 대안 `reissue_remainder` (재발주, 새 slippage/latency/fee/rounding 적용) = strategy config 노출.

### D7. 3 Mode 적용 차이

| Mode | Slippage | Fee | Latency | Partial fill | Source of truth |
|---|---|---|---|---|---|
| Backtest | composite full + tick rounding | snapshot lock per run_id | deterministic | seeded probabilistic | simulator |
| Paper | depth-weighted (orderbook walk) + composite residual | snapshot | Gaussian (seed-able) | live depth-based | simulator + realtime adjustment |
| Live | not applied to fill (model is informational) | exchange API actual | measured (audit) | exchange truth | exchange API |

**Live audit fields** (모든 Live order):

```
expected_price / expected_slippage_bps / expected_fee_bps / expected_latency_ms
actual_avg_fill_price / actual_slippage_bps / actual_fee_bps
submit_to_ack_ms / submit_to_first_fill_ms / submit_to_final_fill_ms
fill_ratio
```

### D8. Calibration policy

**Tuning trigger** (rolling window 기반, single-trade 금지):

```
minimum sample: 100 live fills per (exchange, symbol, side, order_type)
                OR 7 calendar days, whichever later

trigger:
  median absolute slippage_error > 3 bps
  OR p90 absolute slippage_error > 10 bps
  OR mean fee_error > 0.5 bps
  OR median latency_error > 50 ms
  OR partial fill rate error > 15 percentage points
```

Parameter key = `(exchange, symbol, side, order_type, liquidity_bucket)`. 데이터 부족 시 exchange-level default fallback (confidence 낮춤).

### D9. Regression target (backtest accuracy)

| 종목 분류 | median slippage drift | p90 slippage drift | fee drift | fill ratio drift |
|---|---:|---:|---:|---:|
| Liquid KRW pair | ≤ 3 bps | ≤ 10 bps | ≤ 0.5 bps | ≤ 10 pp |
| Illiquid KRW pair | ≤ 7 bps | ≤ 25 bps | ≤ 0.5 bps | ≤ 20 pp |

Regression fixture = fixed market data + ExchangeCapabilities + simulator config + seed. fee/tick policy 변경 = snapshot version up + old snapshot regression 유지.

### D10. ExecutionReport schema (3 mode 공유)

**MCT-4 의 가장 중요한 결정** (Codex 강조). 3 mode 가 동일 schema 로 ExecutionReport 생성 → 추후 Live empirical → Backtest simulator calibration 가능.

```python
@dataclass(frozen=True)
class ExecutionReport:
    # 공통
    mode: Literal["backtest", "paper", "live"]
    run_id: str
    order_id: str
    client_order_id: str
    exchange: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: OrderType
    intent_qty: Decimal
    intent_notional_krw: Decimal
    state: OrderLifecycle  # 8-state

    # Timestamps (latency-adjusted)
    signal_ts: datetime
    decision_ts: datetime
    submit_ts: datetime
    ack_ts: datetime | None
    first_fill_ts: datetime | None
    final_fill_ts: datetime | None

    # Fills (cumulative)
    fills: list[Fill]
    avg_fill_price: Decimal | None
    fill_qty: Decimal
    fill_ratio: float

    # Costs
    expected_slippage_bps: float
    actual_slippage_bps: float | None
    fee_paid_krw: Decimal
    fee_bps: float

    # State / rejection
    rejection_reason: RejectionReason | None
    audit_ext: dict   # Live = exchange raw response, Backtest = simulator deterministic seed
```

### D11-D19. 9 Hidden decisions

| # | 결정 |
|---|---|
| H1 | Negative slippage = clamp to 0 in cost. Live audit raw 저장. |
| H2 | Bid-ask spread 이중 계상 방지: orderbook 가용 시 base_bps → 0.25 또는 disable. |
| H3 | Depth-weighted price = 매수 ask 누적 / 매도 bid 누적 (VWAP). notional 기반 = level_notional 누적. |
| H4 | KRW tick rounding: `buy_eff = ceil(raw / tick) * tick`, `sell_eff = floor(raw / tick) * tick`. tick_bps_adjustment 항으로 audit. |
| H5 | Cancel race after partial: `PARTIALLY_FILLED → CANCEL_REQUESTED → CANCELED`. Fee = cumulative fills 기준. fee 는 fill event 단위 누적. |
| H6 | liquidity_ref ≤ 0 = `NO_LIQUIDITY_REJECTED` or `PARTIAL_FILL_ZERO` (fallback 임의 liquidity 생성 금지). |
| H7 | Volatility spike haircut: `recent_volatility_bps > 300` 시 `liquidity_ref *= max(0.25, 1 - haircut)`. |
| H8 | Parameter key 5-tuple = `(exchange, symbol, side, order_type, liquidity_bucket)`. |
| H9 | ExecutionReport schema 공유 (D10) — 3 mode 동일 → Live → Backtest calibration mechanism. |

## Alternatives Considered

### A1. Linear size factor (sqrt 대신 linear)
- f(x) = x
- **기각**: 작은 주문 cost underweight + 큰 주문 oversimplify. Almgren-Chriss / Kyle 의 sqrt impact 가 보수적.

### A2. Fixed bps slippage 단독 (D5 baseline 대신)
- composite 미적용
- **기각**: 유동성 / 변동성 / size 무시. ADR-003 의 \"slippage underestimate\" anti-pattern.

### A3. Implied volatility 사용 (g(v) 의 input)
- **기각**: KRW crypto 옵션시장 부재. realized volatility 만 사용 가능.

### A4. Backtest 에 latency 미적용 (deterministic = zero latency 가정)
- **기각**: lookahead bias 증가. signal close → 같은 candle high/low fill 가능. \"submit latency 이후 first executable market state\" 강제 의무.

### A5. Maker/taker 판정 = limit = always maker (candle-only)
- **기각**: cross spread limit 도 taker. 보수적 taker default 가 옳음.

### A6. parameter key 단일 (exchange-level only)
- **기각**: BTC/KRW 의 size_factor 가 알트코인에 적용 시 inaccurate. 5-tuple key 필수 (D11 H8).

### A7. ExecutionReport schema 분리 (mode 별)
- **기각**: Live ↔ Backtest calibration mechanism 손실. **D10 의 가장 강한 invariant 위반**.

## Consequences

### C1. simulator 의 실제 vs 예상 audit 의무
모든 Live order = ExecutionReport 의 expected/actual 양쪽 저장. simulator drift 측정 가능.

### C2. fee/tick policy 변경 = snapshot versioning
ExchangeCapabilities + FeeSchedule 변경 = `valid_from / valid_to` 갱신 + new snapshot. 과거 backtest = old snapshot lock 유지.

### C3. parameter default = educated guess (calibration 의무)
base_bps / size_factor / volatility_factor 의 default 는 confidence L 의 educated guess. **Live 100 fill 또는 7일 후 calibration tuning 의무**. 미수행 = simulator drift 위험.

### C4. liquidity_ref 부재 종목 = 거래 불가 정책
illiquid 종목에 fallback liquidity 생성 금지. backtest 가 \"체결되지 않을 종목\" 으로 분류 → strategy 검증의 핵심.

### C5. ExecutionReport schema 변경 = ADR-004 amend
schema field 추가/삭제 시 본 ADR amend 의무. 3 mode 공유 invariant 보존.

## Cross-references

- **MCT-4 Story** ([`../stories/MCT-4.md`](../stories/MCT-4.md))
- **ADR-002 / ADR-003** — baseline architecture
- **MCT-5 (예정)** — Lookahead bias 자동 검증. 본 ADR D5 latency 와 D10 timestamp 4-tuple (signal/decision/eligible_fill/fill) 의 mechanism.
- **MCT-9 (예정)** — OHLCV 스키마 v1. 본 ADR D2 L3 (orderbook depth) 의 활성화 의존.
- **MCT-7 (예정)** — Risk gate threshold. 본 ADR 의 calibration trigger threshold (3bp / 10bp / 50ms) 가 risk gate 의 input 가능.
- **MCT-6 (예정)** — Walk-forward / OOS. 본 ADR D9 regression target 의 fold 별 적용.
