---
adr_id: ADR-002
title: TradeExecutor Protocol + 3 mode (Backtest / Paper / Live) + executor module 구조
status: Accepted
date: 2026-05-02
related_story: MCT-2
category: engine
supersedes: []
amends: []
---

# ADR-002: TradeExecutor Protocol + 3 mode + executor module 구조

## Status

**Accepted** — 2026-05-02. MCT-2 Story Phase 1 PR 의 산출물.

## Context

mctrader 의 자동매매 핵심 abstraction = TradeExecutor Protocol + 3 mode 동일 Protocol 의 3 impl (Backtest / Paper / Live). 사용자 사전 결정 (첫 메시지):

- 위치 = `mctrader-engine` 내부 module (`executor/{protocol,backtest,paper,live}.py`) — 6 repo 유지
- Backtest = 적재 data + batch + simulated fills via slippage 모델
- Paper (실전가상) = realtime + 적재 + 가상 자금 / 가상 주문
- Live (실거래) = realtime + 적재 + 실 자금 + mctrader-market-* 호출
- Strategy 코드 = mode-agnostic (Executor 만 mode 별 동작)

본 ADR 의 결정 범위:
1. TradeExecutor Protocol 의 method surface (Q1)
2. 3 mode 간 state isolation 정책 (Q2)
3. Mode switching mechanism (Q3)
4. Risk gate per mode (Q4)
5. Backtest slippage 모델 baseline (Q5)
6. Paper virtual ledger persistence (Q6)
7. Validation pipeline (Backtest → Paper → Live consistency, Q7)
8. Strategy code share across modes (Q8)
9. Configuration / secret management per mode (Q9)
10. 10 Hidden decisions (Codex surface): order lifecycle / error handling / clock / lookahead bias / fee+rounding / capital allocation / idempotency / event sourcing / data staleness / exchange capability model

본 ADR 은 MCT-1 (ADR-001 거래소 우선순위) 의 후속 도메인 ADR. 결정 traceability: 사용자 사전 결정 + Codex (codex-rescue, gpt-5.5 high) Sonnet decider protocol second-opinion + Sonnet 합성.

## Decision

### D1. TradeExecutor Protocol method surface (Q1=D)

**Trade-only Protocol** (4 methods) + **별도 MarketDataProvider Protocol** (data feed) + **StrategyContext** (mode-agnostic strategy interface).

```python
# mctrader-engine/src/mctrader/executor/protocol.py

@runtime_checkable
class TradeExecutor(Protocol):
    def place_order(self, intent: OrderIntent) -> OrderRef: ...
    def cancel_order(self, order_ref: OrderRef) -> CancelResult: ...
    def get_position(self, symbol: Symbol) -> Position: ...
    def get_balance(self, currency: Currency) -> Balance: ...

@runtime_checkable
class MarketDataProvider(Protocol):
    def get_candles(self, symbol: Symbol, interval: Interval, end: datetime, lookback: int) -> Candles: ...
    def get_orderbook(self, symbol: Symbol) -> Orderbook: ...
    def stream_trades(self, symbol: Symbol) -> AsyncIterator[Trade]: ...   # Paper/Live only

@dataclass(frozen=True)
class StrategyContext:
    market: MarketDataProvider
    executor: TradeExecutor
    risk_constraints: RiskConstraints
    clock: Clock
    capabilities: ExchangeCapabilities
```

근거: god interface 회피 (Codex push-back). 3 mode 간 data feed 결합 회피 (Backtest = storage replay / Paper = storage + realtime / Live = storage + realtime). MarketDataProvider 분리는 mctrader-data 의 추상화 boundary 와 align.

### D2. 3 mode state isolation (Q2)

**Market data cache 만 share. 모든 execution + account + strategy runtime state 는 (mode, run_id, exchange, strategy_id) namespace 로 isolate.**

| 구분 | 정책 |
|---|---|
| OHLCV cache | shared (read-only / immutable / append-only) |
| Orderbook historical snapshot | shared |
| Ledger (자금) | **isolate** per (mode, run_id, exchange) |
| Position state | **isolate** per (mode, run_id, exchange, strategy_id) |
| Open order book | **isolate** per (mode, run_id) |
| Strategy runtime state (signals / cooldowns / memory) | **isolate** per (mode, run_id, strategy_id) |

3 mode **동시 실행 정책**:
- Backtest + Paper 병행 = OK (다른 run_id)
- Live + Paper shadow 병행 = OK (Paper = Live signal 검증)
- Live + Live 동시 = **금지** (1 account 당 1 LiveExecutor 강제, lock / capital allocator 부재시)

### D3. Mode switching mechanism (Q3=A+D)

**CLI flag (외부 인터페이스) + Factory DI (내부 조립).**

- 사용자 인터페이스: `mctrader run --mode {backtest|paper|live} --strategy <name> [--confirm-live]`
- 내부 조립: `ExecutorFactory(mode, config) → TradeExecutor + dependencies (Clock, MarketDataProvider, RiskGate, Ledger 등)`
- **Strategy config 안에 mode field 미포함** (strategy ↔ execution environment 결합 회피)
- Run manifest 에 resolved mode + config + slippage version + data range + strategy version 기록 (reproducibility)

### D4. Risk gate per mode (Q4)

**3 mode 모두 동일 RiskGate interface 통과**. Mode 별 동작 차이:

| Mode | RiskGate 동작 |
|---|---|
| Backtest | gate violation = \"rejected order event\" 기록 + simulation 계속. Strategy 의 risk-incompatible 행동 검출 의무. |
| Paper | Live 와 동일 — block + audit log. \"실전가상\" 의 의미 충실. |
| Live | block + audit log + escalation (kill switch / drawdown limit / max exposure / max order notional / max daily loss / order rate limit / symbol allowlist) |

본 ADR 은 RiskGate interface 만 정의. 실제 threshold + policy 는 **MCT-7 ADR-007** 으로 위임.

### D5. Backtest slippage model (Q5)

**Composite (E) baseline**: `slippage_bps = base_bps + size_factor * (notional / liquidity_ref) + volatility_factor * recent_volatility`. 추가:

- **Latency model**: 최소 \"market order = next tick / next candle open 기준 deterministic fill\". limit order = touch만으로 fill 안 함 (\"보수적 조건\" 명시).
- **Partial fill probability**: minimum 5% (size 가 liquidity_ref 의 일정 % 초과 시 partial fill 가능).
- **Orderbook walk (D)** = high-fidelity 확장. orderbook 데이터 가용 시 활성 (mctrader-data MCT-9 의존).
- **Fixed bps (A) 단독** = smoke test 만 허용.

상세 파라미터 default + tuning 은 **MCT-4 ADR-004** 으로 위임. 본 ADR 은 model class 의 인터페이스만:

```python
class SlippageModel(Protocol):
    def compute(self, intent: OrderIntent, market_state: MarketState) -> SlippageResult: ...

class CompositeSlippageModel:
    def __init__(self, base_bps: float, size_factor: float, volatility_factor: float, partial_fill_threshold: float): ...
```

### D6. Paper virtual ledger persistence (Q6)

**SQLite append-only event log + current snapshot view.**

Tables:
- `paper_orders` — order intents + state transitions
- `paper_fills` — fill events (potentially partial)
- `paper_ledger_events` — balance changes (deposit / fill / fee / cancel refund)
- `paper_balances` — current snapshot per (run_id, currency)

Process restart = event replay 또는 latest snapshot 복구. JSON snapshot = debug export 만 (operational truth 아님).

근거: in-memory 는 Paper 의 \"Live rehearsal\" 의미 손실. file snapshot 은 order lifecycle 복원 약함. PostgreSQL 은 personal project 과도. SQLite = transactional + 단일 파일 + Python 표준 ecosystem.

### D7. Validation pipeline (Q7)

**Replay + Shadow + Metric comparison + Decision reproducibility 보장.**

| Layer | 책임 |
|---|---|
| Decision reproducibility | Strategy 가 동일 input (data + clock + seed + warmup) 에 대해 동일 decision. `datetime.now()` 사용 금지 강제 (BacktestClock + RealtimeClock 통일 interface). |
| Replay validation | Backtest run = run manifest + event log → strategy update 후 replay 시 결과 재현 가능 |
| Shadow validation | Paper = Live data feed 받으면서 가상 주문 — Live transition 전 검증 |
| Metric comparison | Backtest / Paper / Live 의 fill price drift / order rejection rate / slippage / turnover / exposure / drawdown 비교 |
| Promotion gate | Backtest → Paper → Live transition 시 \"최근 N일 violation 0 + drift < threshold\" 검증 (threshold = MCT-6 walk-forward Story 에서 상세) |

Live 는 외부 API 응답 + latency 로 완전 재현 불가능 → \"decision reproducibility\" + \"execution auditability\" 분리.

### D8. Strategy code share across modes (Q8=C)

**Strategy 는 mode 미인지. StrategyContext (market data + portfolio snapshot + risk constraints + clock + capabilities) 받음.**

```python
# mode-agnostic strategy 예
def my_strategy(context: StrategyContext) -> list[OrderIntent]:
    candles = context.market.get_candles(...)
    position = context.executor.get_position(...)
    if signal_buy(candles) and not_at_max_exposure(position, context.risk_constraints):
        return [OrderIntent(symbol=..., side=BUY, ...)]
    return []
```

Live 보수적 운영 시 strategy branch 가 아닌 risk profile / config 로 조정. e.g. `risk_constraints.max_order_notional` 을 Live profile 에서 더 작게.

### D9. Configuration / secret management per mode (Q9)

**Backtest/Paper = secret 불필요. Live = explicit `--mode live` + `--confirm-live` (또는 별도 safety flag) + 별도 secret 주입.**

- Live 가 아닌 경우 secret loader 호출 자체 차단
- CI default = Live mode integration test 차단 (env var `MCTRADER_ALLOW_LIVE_TEST` 명시 시만 허용, 그래도 dry-run / shadow 만)
- 상세 secret 관리 (env vs file vs vault) = **MCT-8 ADR-008** placeholder dependency

### D10. Hidden decisions (Codex surface, Sonnet 채택)

| H# | 결정 |
|---|---|
| H1 Order lifecycle | 8-state: `NEW → ACCEPTED → PARTIALLY_FILLED → FILLED / CANCEL_REQUESTED → CANCELED / REJECTED / EXPIRED`. Cancel race composite state (\"취소 성공 + 일부 체결\") 명시 처리. 3 mode 공유 state machine. |
| H2 Error handling | `RejectionReason` enum + retryable classification. retryable: timeout / 5xx / rate limit / nonce drift. immediate-fail: insufficient balance / min order size / tick size / duplicate client_order_id / unknown symbol. |
| H3 Clock / timezone | UTC (저장 + 내부 계산) / KST (사용자 표시 only). Backtest = SimulatedClock (deterministic). Paper/Live = realtime + monotonic. Candle close boundary = decision uses bars where close_time ≤ now. |
| H4 Lookahead bias 방지 | \"t decision 은 t-1 close 까지 데이터만. 체결 = 다음 tick / next candle open\". BacktestExecutor 가 강제. MCT-5 에서 자동 검증. |
| H5 Fee + tick + min order + rounding | `ExchangeCapabilities` frozen dataclass per-exchange. Backtest/Paper = Live 와 동일 capability 적용 (Live 전환 surprise 방지). |
| H6 Capital allocation | MCT-2 minimal = (mode, run_id, exchange) 당 active strategy 1. Multi-strategy = future ADR. |
| H7 Idempotency | deterministic `client_order_id` (e.g. `f\"{strategy_id}-{symbol}-{intent_seq}\"`). Live retry = 같은 id 로 reconcile. 거래소 capability 별 local intent_id ↔ exchange order_id mapping. |
| H8 Event sourcing | append-only event log per (mode, run_id) — 모든 order intent / risk decision / exchange request+response / fill / balance update. 디버깅 + validation + recovery + audit 의 기반. |
| H9 Data freshness | Paper/Live = orderbook age > N sec / candle age > M sec → block. N/M = `ExchangeCapabilities` per-exchange. Backtest = missing/dup/out-of-order data → halt 또는 skip per policy (MCT-9 의존). |
| H10 Exchange capability model | `ExchangeCapabilities` per-exchange dataclass. Live executor 가 mctrader-market-{exchange} 주입 시 capability 함께. |

### D11. Module 구조 + 컴포넌트 책임

```
mctrader-engine/src/mctrader/executor/
├── protocol.py              # TradeExecutor / MarketDataProvider / StrategyContext
├── backtest.py              # BacktestExecutor (orchestration only)
├── paper.py                 # PaperExecutor
├── live.py                  # LiveExecutor
└── components/
    ├── ledger.py            # SQLite event-sourced ledger (Paper)
    ├── clock.py             # SimulatedClock / RealtimeClock + monotonic
    ├── simulator.py         # ExecutionSimulator (composite slippage, Backtest+Paper share)
    ├── market_data.py       # MarketDataReader (wraps mctrader-data + mctrader-market-{exchange})
    ├── risk_gate.py         # RiskGate interface + 3-mode apply
    ├── capabilities.py      # ExchangeCapabilities frozen dataclass
    ├── order_state.py       # OrderLifecycle 8-state + transitions
    └── rejection.py         # RejectionReason enum + retryable classification
```

각 Executor = orchestration only. 공통 책임 (ExecutionSimulator / Ledger / Clock / MarketDataReader / RiskGate / Capabilities) 은 components 내부에서 DI.

## Alternatives Considered

### A1. TradeExecutor god interface (Q1=B/C reject)
- B: trade + data snapshot in same Protocol (6+ methods)
- C: full execution + data + advanced (10+ methods)
- **기각 사유**: god interface. 3 mode 간 data feed 결합 강제. Backtest 는 stream 미해당 / Live 만 advanced order 가용 — 모든 거래소 공통 표면 강제 시 lowest common denominator 손실. Codex strong push-back (H confidence).

### A2. 3 mode 완전 공유 state (Q2 reject)
- ledger / position / strategy state 까지 3 mode 가 공유
- **기각 사유**: Paper 와 Live 가 같은 ledger 실수 공유 시 치명적. 동시 실행 시 strategy state 충돌. Codex H confidence.

### A3. Strategy config 에 mode field 포함 (Q3 reject)
- strategy YAML 에 `mode: live` 명시
- **기각 사유**: strategy ↔ execution environment 결합. \"같은 strategy 가 3 mode 에서 동일 동작\" 목표와 충돌. Run manifest 에 resolved mode 기록은 따로 함.

### A4. Backtest 에서 risk gate 생략 (Q4 reject)
- simulation 이라 violation = informational
- **기각 사유**: Live 에서 실행 불가능한 strategy 가 Backtest 만 통과 → \"Backtest 좋음, Live 매번 거부\" 패턴. Codex strong push-back (H).

### A5. Paper 에서 risk gate 완화 (Q4 reject)
- 가상 자금이라 lighter risk
- **기각 사유**: Paper 의 의미 = Live rehearsal. gate 완화 시 Live 전환 시 동작 차이 발생. kill switch / daily loss / max order size 는 Paper 에서도 검증 의무.

### A6. Backtest slippage = fixed bps 단독 (Q5 reject)
- 5bp constant
- **기각 사유**: 유동성 낮은 코인 / 큰 주문 / 변동성 급등 미반영 → backtest 과도 낙관. 자동매매 anti-pattern (\"slippage underestimate\"). smoke test 만 허용.

### A7. Paper ledger in-memory only (Q6 reject)
- process restart = reset
- **기각 사유**: Paper 의 \"Live rehearsal\" 의미 손실. restart recovery 부재. SQLite event log 가 운영 필수.

### A8. Strategy 가 mode 인지 (Q8=B reject)
- Strategy 코드에 `if mode == \"live\": ...` 분기
- **기각 사유**: 자동매매 anti-pattern #1 (Codex surface). Backtest/Paper/Live consistency 즉시 깨짐. Live 에서 더 보수적 운영 시 risk profile / config 로 조정 (StrategyContext.risk_constraints).

### A9. Protocol 대신 abc.ABC (Q1 sub-reject)
- 명시적 상속 + 런타임 강제
- **기각 사유**: personal Python project. Mock executor / replay executor / dry-run executor 작성 시 Protocol 의 구조적 타이핑이 더 친숙. mypy/pyright + contract test 보강. 단, 향후 plugin boundary 명확해지면 ABC 재검토 가능.

### A10. mctrader-execution 별도 repo (위치 결정 reject)
- executor module 을 mctrader-engine 외부 별도 repo
- **기각 사유**: 현재 단계 (1 engine + 1 strategy + 1 risk + 1 CLI 모두 mctrader-engine) 에서 분리 시 import / 배포 / 변경 비용 증가. 향후 trigger (\"여러 engine/app 이 같은 execution layer 재사용\" 또는 \"execution surface 비대\" 또는 \"live trading code 분리 필요\") 발생 시 재검토. ADR-002 §C7 박제.

## Consequences

### C1. 단기 (즉시)

- **mctrader-engine repo 생성 시 본 ADR 의 layout 준수**. executor/ + executor/components/ + runner/ 구조 강제.
- TradeExecutor / MarketDataProvider / StrategyContext Protocol 이 mctrader-engine 의 stable interface — 변경 시 ADR amend 의무.
- StrategyContext 의 dependency (RiskConstraints / Clock / ExchangeCapabilities) 가 다른 ADR (MCT-7 / MCT-8 / MCT-9) 의 출력에 의존 — 의존 graph 명시.

### C2. Strategy 코드 mode-agnostic 강제

- 향후 모든 strategy 코드는 `if mode == ...` branch 금지.
- StrategyContext 가 mode 미노출 — 강제 mechanism.
- Live 에서 보수적 운영 시 strategy branch 대신 risk profile / config 변경.
- Code review 시 mode branch 발견 = 즉시 reject.

### C3. Backtest 결과 신뢰성

- Lookahead bias prevention (H4) 강제 — BacktestExecutor 가 \"current/future bar 대상 주문\" reject.
- Composite slippage (D5) 가 fixed bps 보다 realistic — 백테스트 과도 낙관 회피.
- Partial fill probability + latency 모델 = 백테스트 vs Live drift 최소화.
- 단, slippage 파라미터 default 는 MCT-4 에서 추가 calibration 의무 — 본 ADR 만으로는 production-grade 아님.

### C4. Paper Mode 의 Live rehearsal 책임

- SQLite event log 가 process restart 후 ledger 복구 보장.
- RiskGate Live 와 동일 — Paper run 통과한 strategy 만 Live promote 가능 (Q7 promotion gate).
- Shadow validation = Live signal 검증의 표준 mechanism.

### C5. Live mode 의 strict opt-in

- `--mode live` + `--confirm-live` 없이는 Live executor 미생성.
- CI 차단 default = `MCTRADER_ALLOW_LIVE_TEST` env var 명시 시만 허용 (그래도 dry-run / shadow 만).
- Secret loader 가 Live 가 아닌 경우 호출 차단 — fail-safe.
- 상세 = MCT-8.

### C6. Multi-strategy 운영 차후 (capital allocator 미정)

- MCT-2 minimal = (mode, run_id, exchange) 당 active strategy 1 강제.
- 동일 KRW 잔고를 두 strategy 가 동시 사용 시 race condition / double-spend 위험.
- 사용자가 multi-strategy 운영 원할 시 future ADR (capital allocator pattern + strategy lock) 추가.

### C7. mctrader-execution 분리 trigger (향후)

다음 중 하나 발생 시 본 ADR amend + executor module 의 별도 repo (`mclayer/mctrader-execution`) 분리 검토:

1. **여러 engine 또는 app 이 같은 execution layer 재사용** (e.g. CLI engine + Streamlit web 에서 동일 LiveExecutor)
2. **Exchange abstraction + ExecutionSimulator 가 mctrader-engine repo 의 50% 이상 차지** — 분리 boundary 명확
3. **Live trading code 의 안정성 / audit 책임이 strategy + CLI 와 분리되어야 할 때** (e.g. live 코드만 별도 deploy / monitoring)
4. **Multi-engine** (e.g. mctrader-research engine 추가) 시점

현재 단계 (1 engine + 1 strategy + 1 risk + 1 CLI 모두 mctrader-engine) = 분리 시 비용 > 가치.

### C8. 본 ADR 의 amend / supersede trigger

- TradeExecutor Protocol 의 4 method 변경 (e.g. `place_order` signature 변경) → amend
- MarketDataProvider Protocol 변경 → amend
- 3 mode 외 신규 mode 추가 (e.g. ReplayMode for incident analysis) → amend
- 위치 결정 변경 (mctrader-execution 분리) → amend
- Capital allocator 도입 → 본 ADR §C6 amend
- abc.ABC 로 전환 → supersede

## Cross-references

- **MCT-2 Story** ([`../stories/MCT-2.md`](../stories/MCT-2.md)) — 본 ADR 의 source Story (Phase 1 PR).
- **MCT-1 / ADR-001** — 거래소 우선순위. Bithumb #1 / Upbit #2 implementation sequence. 본 ADR 의 Live executor 가 mctrader-market-bithumb 첫 의존.
- **MCT-3** — Backtest engine 라이브러리 선정 (self-built vs vectorbt vs backtrader vs Nautilus). 본 ADR 의 ExecutionSimulator 가 self-built composite 채택 — MCT-3 가 라이브러리 의존 여부 final.
- **MCT-4** — Slippage / fee / latency 모델 상세. 본 ADR D5 의 composite parameter default + tuning.
- **MCT-5** — Lookahead bias 자동 검증. 본 ADR H4 의 강제 mechanism 자동화.
- **MCT-6** — Walk-forward / OOS 검증 protocol. 본 ADR D7 의 promotion gate threshold.
- **MCT-7** — Kill switch / drawdown limit / max exposure 정책. 본 ADR D4 RiskGate threshold.
- **MCT-8** — API 키 secret + Live CI 차단. 본 ADR D9 placeholder dependency.
- **MCT-9** — OHLCV 스키마 v1. 본 ADR D2 market data cache + D5 slippage 의 input schema.
- **MCT-13** — mctrader-market interface (Candle / OrderBook / Order Protocol). 본 ADR 의 MarketDataProvider 와 Live executor 가 의존.
- **CFP-60** — cross-repo Epic + debut-audit. 본 ADR 의 cross-repo 의존 (mctrader-data / mctrader-market-{exchange}) graph 가 Epic MCT-12 의 토대.
- **Codex 의견 dispatch** — Sonnet decider protocol (CFP-59 / ADR-019). 본 ADR 의 19 결정 (9 design + 10 hidden) 모두 Codex 권장 채택률 100%.

## 데뷔작 audit pre-Story note

본 Story (MCT-2) 진행 중 codeforge plugin 추가 install-time finding 발견 안 됨 (기존 5 finding #115~#118 + #122 외). MCT-1 의 finding 후보 (\"Codex agent 직접 file write\") = 본 task 에서 명시적으로 \"docs/ 직접 작성 금지\" 추가 후 그대로 준수 — agent 행동 변경 가능 확인.

## Live Mode Kill Switch (D4 engine-enforced — Amendment 1, 2026-05-04, MCT-42)

ADR-012 §D4 에서 Sonnet decider Phase 1 D4 pick=A — kill switch enforcement = **`mctrader-engine`** 측 (LiveExecutor 가 source). UI/web/monitoring = trigger only.

### D11.1 components/kill_switch.py 신설

```
mctrader-engine/src/mctrader/executor/components/
└── kill_switch.py    # NEW (Amendment 1) — engine-enforced kill switch
```

`KillSwitch` class. LiveExecutor 가 모든 order call site 직전 본 class verify — bypass 불가능.

### D11.2 자동 trigger 5종 (engine 내)

- ADR-007 D1 critical_stop (drawdown limit)
- ADR-007 D2 max_exposure violation
- ADR-007 D4 rate limit hard violation (order block, MCT-32 sliding window)
- ADR-012 D2 KRW cap violation (Stage 3 tiny-live 10,000 KRW 초과)
- KRW position reconciliation drift ≥ 1 KRW (MCT-45 invariant)

### D11.3 Manual trigger interface (operator-action-v1 consumer)

UI/CLI/incident response → `operator-action-v1` event (kill / resume / acknowledge) → engine `KillSwitch.consume_action()` → enforcement.

UI 장애 시에도 CLI / direct API call 로 kill 가능 — engine = enforcement source 보장.

### D11.4 Bypass 차단

- Strategy code 가 `LiveExecutor` instance 우회 불가 (ADR-002 D8 mode-agnostic strategy)
- 모든 order call = `KillSwitch.check()` 통과 의무 — call site enforcement

### D11.5 cross-ref

- MCT-42 (carrier ADR-012)
- MCT-46 (engine impl)
- ADR-008 D8 (incident response 7-step)

## H5 Implementation seal — `ExchangeCapabilities` source partition (Amendment 2, 2026-05-09, MCT-104)

ADR-002 D10 H5 (`ExchangeCapabilities` frozen dataclass per-exchange) 은 ADR 채택 시점 (2026-05-02) 에 dataclass shape 만 freeze, **source 미정** 상태였다. mctrader-engine 코드 grep 결과 (2026-05-09, MCT-104 §2 audit) — `ExchangeCapabilities` 는 어떤 형태 (dataclass / hardcode / config / DI) 로도 미구현 상태였다 (Live executor blocker dormant).

**MCT-104 Phase 1 PR 이 H5 first implementation seal**:

- **Source partition**: ADR-009 §D13 (`exchange_metadata.v1`) — mctrader-data collector daemon 이 daily cadence 로 Bithumb public REST `/public/ticker/ALL_KRW` + 코드화된 price-band lookup table + 공식 fee schedule 결합 후 적재.
- **Capability 매핑** (§D13.6 박제):
  - `fee_maker` / `fee_taker` → `Capabilities.fee` (maker/taker 분리 필수, ADR-002 H5 의 "fee" 단일 field 가 maker/taker 분리로 명시화 amend)
  - `tick_size` → `Capabilities.tick`
  - `min_order_qty` → `Capabilities.min_order_size`
  - `min_order_notional_krw` → `Capabilities.min_order_notional`
  - `asset_status` → ADR-002 H9 data freshness gate 의 입력 (asset halt = order reject)
- **Live executor consumer 책임**: ADR-002 H5 의 dormant 상태 종결. 단 mctrader-engine 측 `ExchangeCapabilities` consumer 구현 = Live executor Epic (별도 Story) 책임. MCT-104 = produce only — `exchange_metadata.v1` partition 적재까지 책임.
- **Capability schema drift 정책**: `ExchangeCapabilities` dataclass 의 field 추가 = ADR-002 amendment + ADR-009 §D13 schema migration (minor `exchange_metadata.v1.M`). field 삭제 = supersede.

본 amendment 로 ADR-002 H5 의 dormant 상태가 종결되며, ADR-009 §D13 이 H5 의 canonical source 로 박제된다. ADR-009 §D13.6 의 "ADR-002 H5 매핑" 절이 SSOT 으로 cross-reference.
