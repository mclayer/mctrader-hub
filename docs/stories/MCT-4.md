---
story_key: MCT-4
status: phase:요구사항
component: backtest
type: brainstorm
related_adr: ADR-004
---

# MCT-4: Slippage / Fee / Latency 모델 상세 + 3 mode 적용 차이

## 1. 사용자 요구사항 (verbatim)

mctrader 의 Slippage / Fee / Latency 모델 상세화 + 3 mode (Backtest / Paper / Live) 적용 차이 명시. ADR-002 / ADR-003 의 baseline (composite slippage / ExecutionSimulator / ExchangeCapabilities / 8-state lifecycle) 위에 정확한 공식 + parameter default + calibration policy + regression test target 박제.

## 2. 도메인 해석

ADR-002 D5 / ADR-003 H3 / ADR-003 D5 가 본 ADR 의 baseline. 본 ADR = baseline 의 formal definition. Codex push-back: \"가장 중요한 MCT-4 결정 = 정교한 확률 모델보다 나중에 실제 체결로 보정 가능한 audit trail\" — 즉 ExecutionReport schema 공유 + calibration mechanism.

## 3. 관련 ADR

- ADR-004 Slippage/Fee/Latency 모델 ([`../adr/ADR-004-slippage-fee-latency.md`](../adr/ADR-004-slippage-fee-latency.md))
- ADR-002 / ADR-003 — baseline architecture
- 향후: MCT-5 (Lookahead bias 검증 — latency timestamp shift 의 자동 audit), MCT-9 (OHLCV 스키마 — orderbook depth 가용성 결정)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader/executor/components/
├── simulator.py              # CompositeSlippageModel + LatencyModel + PartialFillModel
├── fee_schedule.py           # FeeSchedule per (exchange, market, tier)
├── exchange_rule_provider.py # tick_size + min_notional + rounding (per exchange)
└── execution_report.py       # ExecutionReport schema (Backtest/Paper/Live 공유)
```

## 5. 요구사항 확장 해석

본 Story scope = composite slippage 의 정확한 공식 + KRW 호가 단위 + fee schedule + latency model + partial fill + 3 mode flow + calibration trigger + regression target. Codex 가 surface 한 9 hidden decision 동시 처리.

## 6. 외부 지식 배경

- Almgren-Chriss / Kyle's lambda — sqrt impact baseline 근거
- Bithumb / Upbit 공식 fee 페이지 — 정책 시점 민감, ExchangeCapabilities encode
- KRW 호가 단위 = 가격대별 차등 (Upbit/Bithumb 동일 tier 구조, public knowledge)
- Garman-Klass realized vol — wick 품질 의존, default 비채택

## 7. 설계 서사

본 ADR 의 결정 17건 (Codex 권장 채택률 17/17). 상세 = ADR-004. 핵심 요약:

### 7.1 Composite slippage 공식

```
slippage_bps = base_bps + size_factor * f(x) + volatility_factor * g(v) + tick_bps_adjustment
where x = notional_krw / liquidity_ref_krw
      v = recent_volatility_bps (EWMA close-to-close, half-life 10 bars)

f(x) = sqrt(x)                                  if 0 < x ≤ 1
       1 + overflow_slope * (x - 1)^1.25         if x > 1, capped at f_cap=8.0
       0                                         if x ≤ 0

g(v) = log(1 + max(v, 0) / vol_ref_bps) / log(2), capped at g_cap=4.0
       (vol_ref_bps default = 50)
```

### 7.2 Liquidity_ref 3-level fallback

- L1: top-of-book size (orderbook 가용)
- L2: 1-minute traded notional median × participation_limit (default 0.10) over lookback (default 60 bars)
- L3: orderbook depth integral within depth_bps (default 10) of best quote (high-fidelity, MCT-9 의존)

MCT-4 baseline = L2 의무 + L3 = MCT-9 이후.

### 7.3 Parameter default

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

### 7.4 Fee schedule

baseline (override priority: live API > account endpoint > user override > event > default):
- Bithumb KRW: maker/taker 0.04% (4 bps), confidence M
- Upbit KRW: maker/taker 0.05% (5 bps), confidence M

`FeeSchedule(exchange, market, maker_bps, taker_bps, vip_tier, event_code, valid_from, valid_to, source, confidence)`. Run 단위 lock per run_id.

Maker/taker 판정 = limit 주문이라도 cross spread = taker. candle-only backtest 에서 maker 판정 불확실 = 보수적 taker default.

### 7.5 Latency model

3 종 — `ConstantLatency / GaussianLatency / MeasuredDistribution`

| Mode | Default |
|---|---|
| Backtest | submit 50ms + ack 50ms deterministic |
| Paper | submit ~ truncated Gaussian(mean=50, std=20, min=10, max=200), seeded |
| Live | model 미적용. measured timestamp audit only |

Backtest 의 latency = lookahead bias 와 직접 연결 — \"signal_time + decision_latency + submit_latency 이후 첫 executable market state 만 사용\" 강제.

### 7.6 Partial fill

```
threshold = 0.30
p_partial(x) = 0                                              if x ≤ threshold
               min(p_max=0.85, 1 - exp(-k=1.8 * (x - threshold)))   else

if partial:
  fill_ratio = clamp(liquidity_ref/notional * U(0.6, 1.0), min_fill_ratio=0.10, 1.0)
```

deterministic mode = `U` 가 `(run_id, order_id, symbol, ts)` seeded. recovery default = `cancel_remainder`. 대안 `reissue_remainder` = strategy config 에 노출.

### 7.7 3 Mode 적용 차이

| Mode | Slippage | Fee | Latency | Partial fill | source-of-truth |
|---|---|---|---|---|---|
| Backtest | composite full | snapshot lock | deterministic | seeded probabilistic | simulator |
| Paper | orderbook walk + composite residual | snapshot | Gaussian | live depth-based | simulator + realtime adjustment |
| Live | N/A (audit only) | exchange API truth | measured (audit) | exchange truth | exchange API |

### 7.8 Calibration trigger (rolling window, single-trade 금지)

```
minimum sample: 100 live fills per (exchange, symbol, side, order_type) OR 7 calendar days

trigger:
  median absolute slippage_error > 3 bps
  OR p90 absolute slippage_error > 10 bps
  OR mean fee_error > 0.5 bps
  OR median latency_error > 50 ms
  OR partial fill rate error > 15 pp
```

Parameter key = `(exchange, symbol, side, order_type, liquidity_bucket)`. 데이터 부족 시 exchange-level default fallback (confidence 낮춤).

### 7.9 Regression target

| 종목 분류 | median slippage drift | p90 slippage drift | fee drift | fill ratio drift |
|---|---:|---:|---:|---:|
| Liquid KRW pair | ≤ 3 bps | ≤ 10 bps | ≤ 0.5 bps | ≤ 10 pp |
| Illiquid KRW pair | ≤ 7 bps | ≤ 25 bps | ≤ 0.5 bps | ≤ 20 pp |

Regression fixture = fixed market data + ExchangeCapabilities + simulator config + seed. fee/tick policy 변경 시 snapshot version up.

### 7.10 9 Hidden decisions (Codex surface)

- Negative slippage = clamp to 0 in cost. Live audit 은 raw 저장.
- Bid-ask spread 이중 계상 방지: orderbook 가용 시 base_bps 0.25 또는 disable.
- Depth-weighted price = 매수 ask 누적 / 매도 bid 누적 (VWAP).
- KRW tick rounding: buy = ceil, sell = floor. tick_bps_adjustment 항으로 audit.
- Cancel race after partial: PARTIALLY_FILLED → CANCEL_REQUESTED → CANCELED. fee = cumulative fills 기준.
- liquidity_ref ≤ 0 = `NO_LIQUIDITY_REJECTED` or `PARTIAL_FILL_ZERO` (fallback 임의 liquidity 금지).
- Volatility spike haircut: `recent_volatility_bps > 300` 시 `liquidity_ref *= max(0.25, 1 - haircut)`.
- Parameter key 5-tuple (exchange / symbol / side / order_type / liquidity_bucket).
- **ExecutionReport schema 공유**: 3 mode 동일 schema (fill_price / fill_qty / fee / state transition / latency-adjusted timestamp / rejection reason). MCT-4 의 가장 중요한 결정.

## 8-11

(Phase 2 N/A — doc-only Story.)
