---
story_key: MCT-2
status: phase:요구사항
component: engine
type: brainstorm
related_adr: ADR-002
---

# MCT-2: TradeExecutor Protocol + 3 mode (Backtest / Paper / Live) + executor module 구조

- **Issue**: (manual flow — story-init.yml 미배포, F2 finding 의존)
- **Status**: phase:요구사항 (Phase 1 PR)
- **Type**: brainstorm Story (architecture decision artifact)

## 1. 사용자 요구사항 (verbatim — story-section-1-immutable 강제)

mctrader 의 자동매매 핵심 abstraction = TradeExecutor Protocol interface + 3 mode 동일 Protocol 의 3 impl.

- **Backtest**: 적재 data + 정해진 기간 batch (storage only, simulated fills via slippage 모델)
- **Paper (실전가상)**: realtime market data + 적재 data + 가상 자금 / 가상 주문
- **Live (실거래)**: realtime market data + 적재 data + 실제 자금 + mctrader-market-* 호출

위치: mctrader-engine 내부 module (`executor/{protocol,backtest,paper,live}.py`) — 6 repo 유지.

## 2. 도메인 해석

자동매매 platform 의 가장 자주 망가지는 지점 = 전략 코드가 실행 환경을 직접 인지하는 순간 (`if mode == "backtest": ...`). 본 ADR 의 핵심 invariant = **\"Strategy 는 mode-agnostic, Executor 만 mode 별 동작\"**.

3 mode 의 차이는 단순 flag 가 아니라:
- 체결 원천 (simulated fill / virtual ledger / real exchange API)
- 시간 모델 (deterministic simulated clock / realtime+monotonic / realtime+monotonic)
- Ledger 영속성 (none / SQLite / SQLite + exchange truth)
- 외부 API 의존성 (none / none / mctrader-market-bithumb 등)
- Failure mode (모두 다름)

Codex push-back (gpt-5.5 high, Sonnet decider second-opinion): \"TradeExecutor 라는 이름 아래 주문 실행 + 잔고 + 시장 데이터 snapshot + stream + risk gate + ledger persistence 까지 넣으면 god interface\". → Q1=D (Protocol minimal trade-only + 별도 MarketDataProvider 분리) 채택.

## 3. 관련 ADR

- **ADR-002 TradeExecutor Protocol + 3 mode** ([`../adr/ADR-002-trade-executor.md`](../adr/ADR-002-trade-executor.md)) — 본 Story 의 결정을 ADR 형식으로 박제.

향후 ADR 후보 (out-of-scope of MCT-2):
- ADR-003 Backtest engine 라이브러리 선정 (self-built composite simulator vs vectorbt vs backtrader vs Nautilus) — MCT-3
- ADR-004 Slippage / fee / latency 모델 상세 (3 mode 적용 차이) — MCT-4
- ADR-005 Lookahead bias 검증 의무 — MCT-5
- ADR-006 Walk-forward / OOS 검증 protocol — MCT-6
- ADR-007 Kill switch / drawdown limit / max exposure 정책 — MCT-7
- ADR-008 API 키 secret 관리 + live CI 차단 정책 — MCT-8 (본 ADR 의 Q9 placeholder dependency)
- ADR-009 OHLCV 스키마 v1 — MCT-9 (본 ADR 의 MarketDataProvider 와 의존)

## 4. 관련 코드 경로 (목표 layout, mctrader-engine repo)

본 Story 는 doc-only governance hub. 실제 코드는 `mclayer/mctrader-engine` repo (향후 생성):

```
mctrader-engine/
├── src/mctrader/
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── protocol.py         # TradeExecutor / MarketDataProvider / StrategyContext Protocol
│   │   ├── backtest.py         # BacktestExecutor (orchestration only)
│   │   ├── paper.py            # PaperExecutor
│   │   ├── live.py             # LiveExecutor
│   │   └── components/
│   │       ├── ledger.py       # SQLite append-only event log (Paper)
│   │       ├── clock.py        # SimulatedClock / RealtimeClock + monotonic
│   │       ├── simulator.py    # ExecutionSimulator (composite slippage, Backtest+Paper share)
│   │       ├── market_data.py  # MarketDataReader (wraps mctrader-data)
│   │       ├── risk_gate.py    # RiskGate interface + 3-mode apply
│   │       ├── capabilities.py # ExchangeCapabilities frozen dataclass
│   │       ├── order_state.py  # OrderLifecycle enum + transitions
│   │       └── rejection.py    # RejectionReason enum + retryable classification
│   ├── strategy/...            # mode-agnostic strategy code (StrategyContext 받음)
│   ├── risk/...                # risk policies (kill switch / drawdown / exposure)
│   ├── runner/                 # CLI entry + factory DI
│   │   ├── cli.py              # mctrader run --mode {backtest|paper|live} --strategy <name>
│   │   ├── factory.py          # ExecutorFactory (mode → executor 조립)
│   │   └── manifest.py         # run manifest 기록 (resolved mode + config + slippage version + ...)
│   └── ...
```

## 5. 요구사항 확장 해석

### 5.1 Scope 분리

본 Story = **TradeExecutor Protocol + MarketDataProvider Protocol + 3 mode skeleton + 9 design point + 10 hidden decision** 만. 다음은 별도 Story:
- Slippage 모델 상세 (composite 의 정확한 공식 + 파라미터 default) → MCT-4
- Risk gate 정책 상세 (kill switch threshold / drawdown limit 수치) → MCT-7
- Backtest 라이브러리 선정 (self-built vs vectorbt 등) → MCT-3
- Lookahead bias 검증 자동화 → MCT-5
- Walk-forward protocol → MCT-6
- Live secret 관리 + CI 차단 → MCT-8
- OHLCV schema → MCT-9

### 5.2 사용자 사전 결정 retain

- 3 mode = 3 impl class (Codex 도 동의, 단 내부 Strategy pattern + DI 권장 — 채택)
- `mctrader-engine` 내부 module 위치 (Codex \"중장기적으로 mctrader-execution 별도 repo 트리거 발생 시 재검토\" 권장 — ADR Consequences 에 박제)
- Protocol typing (PEP 544) — Codex H confidence 동의

## 6. 외부 지식 배경

### 6.1 자동매매 platform 의 hidden bug 카테고리 (Codex surface)

- **Lookahead bias**: candle 의 high/low/close 를 다 본 뒤 같은 candle 안에서 주문 → 결과 왜곡
- **Slippage underestimate**: fixed bps 만 적용 → 유동성 낮은 코인 / 큰 주문 / 변동성 급등 구간 미반영
- **Partial fill ignore**: backtest 가 모든 주문 fully fill 가정 → Live 에서 reconcile 실패
- **Latency assumption**: zero-latency 가정 → realtime stream gap / tick miss / order timeout
- **Clock drift**: wall clock 기반 backtest → reproducibility 손실
- **Cancel race**: cancel 요청과 체결 동시 발생 → ledger 불일치
- **Idempotency 누락**: timeout 후 retry → 중복 주문

본 ADR-002 의 핵심 결정이 위 7 가지를 prevent 하는 방향으로 alignment.

### 6.2 Python ecosystem 참고

- `typing.Protocol` (PEP 544) — 구조적 타이핑, mock 작성 친숙
- `abc.ABC` — 명시적 상속 + 런타임 강제 (대안)
- backtest library: vectorbt (vectorized, fast), backtrader (event-driven, mature), Nautilus (production-grade, complex), zipline (deprecated)
- ledger persistence: SQLite (transactional, single file), DuckDB (OLAP, mctrader-data 와 동일 stack 이나 app-state 부적합)

→ MCT-2 = Protocol typing + 3 impl class + composite slippage simulator self-built. 라이브러리 의존 최소화 (개인 platform, 검증 가능성 우선).

## 7. 설계 서사

### 7.1 9 Design Point 결정 (Sonnet decider, Codex review 적용)

| # | Design point | 결정 | Codex 권장 vs Sonnet 결정 |
|---|---|---|---|
| Q1 | TradeExecutor Protocol method surface | **D + minor**: trade-only Protocol (place_order, cancel_order, get_position, get_balance) + 별도 `MarketDataProvider` Protocol | Codex H — 그대로 채택 |
| Q2 | 3 mode state isolation | **Mode + run_id + exchange + strategy_id namespace 로 분리**. market data cache 만 share | Codex H — 그대로 채택 |
| Q3 | Mode switching mechanism | **A + D 조합**: CLI flag (`--mode {backtest|paper|live}`) + factory DI (내부). Strategy config 에 mode 미포함. Run manifest 에 resolved mode 기록 | Codex H — 그대로 채택 |
| Q4 | Risk gate per mode | **3 mode 모두 동일 RiskGate interface 통과**. Backtest = 거부 이벤트 기록 후 simulation 계속 / Paper = Live 와 동일 block / Live = block + audit + kill switch | Codex H — 그대로 채택 |
| Q5 | Backtest slippage 모델 | **Composite (E) default**: fixed bps + size factor + volatility factor. Latency 모델 + partial fill probability 최소 model 포함. Orderbook walk (D) = high-fidelity 확장 (orderbook 데이터 가용 시 활성). Fixed bps 단독 (A) = smoke test 만 | Codex M-H — 그대로 채택. MCT-4 에서 파라미터 default 상세화. |
| Q6 | Paper virtual ledger persistence | **SQLite append-only event log + current snapshot view**. tables: paper_orders / paper_fills / paper_ledger_events / paper_balances. Process restart = event replay 또는 latest snapshot 복구. JSON snapshot = debug export 만 | Codex H — 그대로 채택 |
| Q7 | Validation pipeline | **replay + shadow + metric comparison + decision reproducibility**. Promotion gate Backtest → Paper → Live (e.g. \"최근 N일 Paper run 에서 risk violation 0 + slippage drift < 임계\"). Live 는 \"decision reproducibility\" + \"execution auditability\" 분리 | Codex H — 그대로 채택. promotion gate 임계값은 MCT-6 walk-forward Story 에서 상세. |
| Q8 | Strategy code share across modes | **C — Strategy 는 mode 미인지**. StrategyContext (market data + portfolio snapshot + risk constraints + clock) 받음. Live 보수적 운영 시 strategy branch 가 아닌 risk profile/config 로 조정 | Codex H — 그대로 채택 |
| Q9 | Configuration / secret management per mode | **Backtest/Paper = secret 불필요. Live 는 explicit `--mode live` + `--confirm-live` (또는 별도 safety flag) + 별도 secret 주입**. CI default = Live mode integration test 차단. ADR-002 = placeholder + MCT-8 dependency 명시 | Codex H — 그대로 채택 |

### 7.2 10 Hidden Decision 결정 (Codex surface, Sonnet decider 채택)

| H# | Hidden decision | 결정 |
|---|---|---|
| H1 | Order lifecycle / state machine | 8-state: `NEW → ACCEPTED → PARTIALLY_FILLED → FILLED / CANCEL_REQUESTED → CANCELED / REJECTED / EXPIRED`. 3 mode 공유 state 모델. Cancel race = \"취소 성공 + 일부 체결\" composite state 처리. |
| H2 | Error handling 정책 | `RejectionReason` enum + retryable classification. retryable: timeout / 5xx / rate limit / nonce drift. immediate-fail: insufficient balance / min order size / tick size violation / duplicate client_order_id / unknown symbol. 3 mode 공유 enum. |
| H3 | Clock / timezone | **저장 + 내부 계산 = UTC**. **사용자 표시 (Streamlit) = KST**. **Backtest = SimulatedClock (deterministic, wall clock 금지)**. **Paper/Live = realtime + monotonic clock (latency / timeout 측정용)**. Candle close boundary 명시 (decision uses bars where close_time ≤ now). |
| H4 | Lookahead bias 방지 규칙 | **\"t 시점 decision 은 t-1 close 까지 관측 가능 데이터만 사용. 주문 체결 = 다음 tick 또는 다음 candle open\"**. BacktestExecutor 가 강제 (현재/미래 bar 대상 주문 reject). MCT-5 에서 자동화된 검증 의무. |
| H5 | Fee model + tick / min order / rounding | `ExchangeCapabilities` frozen dataclass 에 encode: fee schedule (maker/taker per 등급), tick size, min notional, quantity precision, rounding direction. **Backtest/Paper = Live 와 동일 capability 적용** (Live 전환 시 거부 surprise 방지). |
| H6 | Capital allocation (multi-strategy) | **MCT-2 minimal = (mode, run_id, exchange) 당 active strategy 1**. Multi-strategy capital allocator = future ADR. |
| H7 | Idempotency + client_order_id | 모든 OrderIntent 에 deterministic `client_order_id` (e.g. `f\"{strategy_id}-{symbol}-{intent_seq}\"`). Live retry = 같은 id 로 reconcile. 거래소 capability 따라 local intent_id ↔ exchange order_id mapping 저장 (Bithumb/Upbit support 차이 capability 흡수). |
| H8 | Event sourcing / replay | append-only event log per (mode, run_id) — order intents / risk decisions / exchange request+response / fills / balance updates. 3 mode 공유 event store (namespace 분리). 디버깅 + validation + paper recovery + live incident analysis 의 기반. |
| H9 | Data freshness / staleness | Paper/Live = orderbook age > N sec OR candle age > M sec → 주문 block. N/M = `ExchangeCapabilities` per-exchange. Backtest = missing/duplicate/out-of-order data → halt 또는 skip per policy (MCT-9 OHLCV schema 의존). |
| H10 | Exchange capability model | `ExchangeCapabilities` frozen dataclass per-exchange. 지원 order type / min notional / precision / fee schedule / rate limit / cancel semantics 등 encode. Live executor 가 mctrader-market-{exchange} 주입 시 capability 함께. Bithumb 초기 minimal: market+limit buy/sell, cancel, balance, positions, get_orderbook (Live only). |

### 7.3 TradeExecutor Protocol (Q1=D 결정 결과)

```python
# mctrader-engine/src/mctrader/executor/protocol.py

from typing import Protocol, runtime_checkable
from datetime import datetime
from decimal import Decimal

@runtime_checkable
class TradeExecutor(Protocol):
    \"\"\"Mode-agnostic trade execution surface. 3 impl: BacktestExecutor / PaperExecutor / LiveExecutor.\"\"\"

    def place_order(self, intent: OrderIntent) -> OrderRef: ...
    def cancel_order(self, order_ref: OrderRef) -> CancelResult: ...
    def get_position(self, symbol: Symbol) -> Position: ...
    def get_balance(self, currency: Currency) -> Balance: ...

@runtime_checkable
class MarketDataProvider(Protocol):
    \"\"\"Read-only market data. 분리된 Protocol — Backtest = storage replay / Paper = storage + realtime / Live = same as Paper.\"\"\"

    def get_candles(self, symbol: Symbol, interval: Interval, end: datetime, lookback: int) -> Candles: ...
    def get_orderbook(self, symbol: Symbol) -> Orderbook: ...
    def stream_trades(self, symbol: Symbol) -> AsyncIterator[Trade]: ...   # Paper/Live only

@dataclass(frozen=True)
class StrategyContext:
    \"\"\"Mode-agnostic strategy interface. mode 이름 미포함 (Q8=C).\"\"\"

    market: MarketDataProvider
    executor: TradeExecutor
    risk_constraints: RiskConstraints
    clock: Clock
    capabilities: ExchangeCapabilities
```

### 7.4 Mode-specific Executor 책임 분리

```
BacktestExecutor:
  - SimulatedClock (deterministic) 사용
  - ExecutionSimulator (composite slippage + latency + partial fill probability)
  - RiskGate 통과 (violation = 거부 이벤트 기록 + simulation 계속)
  - 결과 = run manifest + event log + metric (PnL / Sharpe / drawdown / turnover)

PaperExecutor:
  - RealtimeClock + monotonic
  - SQLite ledger (event sourced)
  - ExecutionSimulator (Backtest 와 같은 simulator 공유)
  - RiskGate 통과 (Live 와 동일 — block 의무)
  - Process restart 시 event replay 복구

LiveExecutor:
  - RealtimeClock + monotonic
  - mctrader-market-{exchange} adapter 호출 (실 API)
  - RiskGate 통과 (kill switch + audit log + escalation)
  - Idempotent client_order_id (H7)
  - Capability 기반 order type / precision / min notional 검증 (H5)
  - Event log + exchange truth reconciliation
```

### 7.5 Mode 동시 실행 정책 (Q2 영향)

- **Backtest + Paper 병행 가능** (서로 다른 run_id namespace)
- **Live + Paper shadow 병행 가능** (Paper = Live 와 같은 strategy + signal, 주문은 가상 — Live 의 \"shadow\" 검증)
- **Live + Live 동시 = 1 account 당 1 LiveExecutor 강제** (lock / capital allocator 없이는 deadlock + double-spend risk)

### 7.6 Codex Framework critique 적용

| Concern | 적용 |
|---|---|
| god interface 위험 | Q1=D 로 TradeExecutor minimal + MarketDataProvider 분리 |
| Protocol vs ABC | Protocol typing 채택 (Codex H 동의) + mypy/pyright + contract test 보강 |
| 3 impl class 가 코드 중복 | 내부 Strategy pattern + DI: ExecutionSimulator / Ledger / Clock / MarketDataReader / RiskGate / Capabilities 주입. 각 Executor = orchestration only |
| 위치 결정 (mctrader-engine 내부) | 현재 단계 채택. 향후 mctrader-execution 별도 repo trigger (= 여러 engine/app 이 같은 execution layer 재사용 / exchange abstraction + simulator 비대 / live trading code 가 strategy/CLI 와 분리 필요) 발생 시 재검토 — ADR-002 §C7 박제 |

### 7.7 Codex 의견 적용 결과

Codex (codex-rescue, gpt-5.5 high) 가 Sonnet decider protocol 의 second-opinion 으로 dispatch. 19 결정 (9 design + 10 hidden) 중:

- **Codex 권장 그대로 채택**: 19/19 (모든 결정)
- **Sonnet 거부**: 0
- **부분 수용**: 0

Codex 권장이 모두 H confidence + strong evidence + 자동매매 anti-pattern 직접 prevent. 거부할 strong 근거 없음.

다만 **다음은 future Story 에 위임**:
- Slippage composite 의 정확한 파라미터 default → MCT-4
- Risk gate threshold 수치 → MCT-7
- Lookahead bias 자동 검증 의무 → MCT-5
- Walk-forward / OOS 검증 protocol → MCT-6
- Live secret 관리 상세 → MCT-8
- OHLCV schema → MCT-9

### 7.8 Anti-pattern prevention checklist (Codex 의 4 가장 피해야 할 것)

본 ADR-002 의 결정이 다음 4 anti-pattern 을 prevent 하는지 검증:

- [x] Strategy 가 mode 직접 분기 → Q8=C (StrategyContext 가 mode 미노출)
- [x] Backtest 가 미래 정보 사용 → H4 (lookahead bias prevention 규칙)
- [x] Partial fill / cancel race 무시 → H1 (8-state lifecycle 명시)
- [x] Paper ledger ephemeral → Q6 (SQLite event-sourced + restart replay)

## 8. 개발 서사

(Phase 2 PR — 본 Story 는 doc-only Story 로 종결. 실제 코드 작성은 mctrader-engine repo 에서 향후 Story.)

본 ADR-002 가 mctrader-engine 의 architecture skeleton 정의. 향후 구현 Story:
- mctrader-engine repo 생성 (Epic MCT-12 의 child Story 일부)
- TradeExecutor / MarketDataProvider / StrategyContext Protocol 코드화
- BacktestExecutor minimal 구현 (composite slippage 포함)
- PaperExecutor minimal (SQLite ledger)
- LiveExecutor minimal (Bithumb-only 호출)
- ExecutorFactory + CLI

## 9. 품질 게이트 이력

(Phase 2 PR — N/A for doc-only Story.)

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

(FIX 발생 시 append.)

## 11. 회고

본 Story 는 \"Codex 종합 review → Sonnet 결정 패턴\" 첫 적용 (memory `feedback_brainstorm_codex_review_pattern.md` 박제). 결과:

- **사용자 stop 최소화 달성**: Q-by-Q 사용자 input 0회 (이전 MCT-1 = 5회). brainstorm 시작부터 최종 정지까지 사용자 input = 1 (MCT-2 시작 trigger 만).
- **Codex push-back 효과**: 9 design point 외 **10 hidden decision surface** (order lifecycle / error handling / clock / lookahead / fee+rounding / capital allocation / idempotency / event sourcing / data staleness / capability model). Sonnet 단독으로는 일부만 surface 했을 가능성 — 특히 idempotency (H7) + cancel race composite state (H1) + ExchangeCapabilities (H10) 가 critical.
- **Codex 권장 채택률 19/19**: 단순 rubber-stamp 가 아닌 **strong evidence + anti-pattern direct prevention** 일치. 부분 수용/거부 case 가 발생하지 않은 이유 = Codex 가 자동매매 platform domain knowledge + best practice 를 정확하게 제공.
- **codeforge plugin finding 추가 발견**: 본 Story 진행 중 발견된 finding 없음 (MCT-1 의 Codex agent 직접 file write 행동은 본 task 에서 명시적으로 \"docs/ 직접 작성 금지\" 추가 → 그대로 준수, finding 회피).
- **Story 분량**: 본 Story = ~ 5000+ 단어. ADR-002 = ~ 4000+ 단어. brainstorm 1회로 9 design + 10 hidden = 19 결정 처리 → 이후 MCT-3 ~ MCT-11 의 efficiency baseline.

향후 본 패턴 적용 시 Codex prompt 의 \`<dig_deeper_nudge>\` 에 \"hidden decision surface 의무\" 명시가 hidden decision 발굴 효과 = 큼.
