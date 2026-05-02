---
story_key: MCT-3
status: phase:요구사항
component: backtest
type: brainstorm
related_adr: ADR-003
---

# MCT-3: Backtest engine 라이브러리 선정 (self-built vs vectorbt vs backtrader vs Nautilus)

- **Issue**: (manual flow — story-init.yml 미배포, F2 finding 의존)
- **Status**: phase:요구사항 (Phase 1 PR)
- **Type**: brainstorm Story (architecture decision artifact)

## 1. 사용자 요구사항 (verbatim — story-section-1-immutable 강제)

mctrader 의 Backtest engine 라이브러리 선정. self-built / vectorbt / backtrader / Nautilus 등 후보 평가 후 채택 결정 또는 self-built 전면 결정.

## 2. 도메인 해석

본 ADR 의 핵심 framing = "좋은 backtester 고르기" 가 아니라 **이미 결정된 mctrader 의 execution architecture (MCT-1 / MCT-2) 를 훼손하지 않으면서 backtest 신뢰성 + 개발 속도 확보**. 라이브러리 평가는 backtester 의 일반 quality 보다 mctrader 와의 boundary alignment 가 우선.

이미 결정된 architectural constraints:
- 3 mode (Backtest/Paper/Live) 가 동일 TradeExecutor Protocol 의 3 impl
- Strategy = mode-agnostic StrategyContext 받음 (mode 미노출)
- BacktestExecutor = orchestration only, 공통 책임 (ExecutionSimulator / Ledger / SimulatedClock / MarketDataReader / RiskGate / Capabilities) 은 components/ 의 DI
- Composite slippage (E baseline) — self-built ExecutionSimulator 채택
- 8-state Order lifecycle / Lookahead bias 강제 / Event sourcing / SimulatedClock + UTC store

라이브러리 채택 시 위 architecture 와 충돌하면 lock-in cost > 사용 이득.

## 3. 관련 ADR

- **ADR-003 Backtest engine 라이브러리** ([`../adr/ADR-003-backtest-library.md`](../adr/ADR-003-backtest-library.md))

향후 ADR (out-of-scope of MCT-3):
- ADR-004 Slippage / fee / latency 모델 상세 — MCT-4 (composite parameter default)
- ADR-005 Lookahead bias 자동 검증 — MCT-5
- ADR-006 Walk-forward / OOS 검증 protocol — MCT-6
- ADR-009 OHLCV 스키마 v1 — MCT-9

## 4. 관련 코드 경로 (목표 layout)

본 Story 는 doc-only. 실제 코드는 mctrader-engine repo:

```
mctrader-engine/src/mctrader/
├── executor/
│   ├── backtest.py           # BacktestExecutor orchestration
│   └── components/
│       ├── simulator.py      # ExecutionSimulator (composite slippage, self-built)
│       ├── ledger.py         # central ledger (multi-pair portfolio)
│       ├── clock.py          # SimulatedClock
│       ├── market_data.py    # candle/orderbook reader
│       ├── risk_gate.py
│       ├── capabilities.py   # ExchangeCapabilities (fee/tick/min/precision)
│       ├── order_state.py    # 8-state lifecycle
│       └── rejection.py
├── runner/
│   ├── backtest_runner.py    # event loop + run manifest
│   └── walk_forward.py       # WFO runner (calls backtest_runner per fold)
├── reporting/
│   ├── event_log.py          # append-only event store schema + writer + replay
│   ├── metrics.py            # PnL / Sharpe / MDD / turnover / exposure (event log 기반)
│   └── adapters/
│       └── vectorbt_adapter.py   # event log → vectorbt dataframe (optional, post-process)
```

핵심 invariant: **canonical truth = mctrader event log**. 외부 라이브러리는 event log read-only adapter 로만 사용 가능, source-of-truth 가 될 수 없음.

## 5. 요구사항 확장 해석

### 5.1 Scope 분리

본 Story = backtest engine 의 build-vs-buy 결정 + library boundary 정책 + 10 hidden decision (data format / decision timing / fee ownership / multi-pair constraint / Python-only / event versioning / metrics / WFO / determinism / ADR wording).

다음은 future Story:
- Slippage parameter default + tuning → MCT-4
- Lookahead bias 자동 검증 mechanism → MCT-5
- Walk-forward fold split / embargo / parameter selection → MCT-6 (단, runner skeleton 위치는 본 ADR 에서 결정)
- 자세한 metrics formula (equity curve 정의 / realized vs mark-to-market) → MCT-6 또는 별도

### 5.2 사용자 언급 후보 외 surface

Codex 가 추가 surface 한 후보 (각 평가됨):
- bt (lightweight portfolio) — core 부적합
- backtesting.py (단순) — core 작음
- zipline / zipline-reloaded — 미국 주식 가정 + maintenance 약함
- pyalgotrade — deprecated
- Hummingbot — live bot framework, backtest 후보로 부적합
- **freqtrade — crypto-specific, "wheel reinventing" challenge 의 가장 강한 후보**
- finmarketpy / 기타 — 범위 mismatch

freqtrade 는 별도 검토 — 자세한 사유는 §A2 (ADR Alternatives).

## 6. 외부 지식 배경

### 6.1 Codex score matrix (가중 100점 환산)

| 후보 | Weighted score |
|---|---:|
| Self-built | **88** |
| Nautilus Trader | 72 |
| vectorbt | 57 |
| freqtrade | 57 |
| Hummingbot | 52 |
| backtrader | 51 |
| backtesting.py | 47 |
| zipline / zipline-reloaded | 43 |
| bt | 42 |
| pyalgotrade | 36 |
| finmarketpy / 기타 | 31 |

**Self-built 가 16점 격차로 1위.** 격차 sensitivity 견고 — 라이브러리 후보 1점 변화로 ranking 역전 안 됨.

### 6.2 평가 framework (11 dimension, Codex 권장 가중)

| Dimension | Weight | 근거 |
|---|---:|---|
| 3-mode architecture 호환성 | 18 | TradeExecutor Protocol + StrategyContext lock-in risk |
| Lookahead bias 강제 가능성 | 12 | MCT 핵심 신뢰성 invariant |
| Execution realism plug-in | 13 | Composite slippage + 8-state lifecycle 자체 책임 |
| Event sourcing 호환 | 10 | append-only log + audit + replay |
| Performance | 8 | 1 거래소 / 10-30 KRW pair / 5분-1일 candle / 1-5년 충분성 |
| Reporting / metrics | 8 | metrics 자체 구현 비용 |
| Walk-forward / OOS | 6 | MCT-6 future |
| Maintenance / Python 3.11+ | 8 | 개인 프로젝트 dependency churn 대응 약함 |
| License / deployment | 5 | MIT/Apache 친숙, native lock-in 비용 |
| KRW exchange specificity | 6 | Bithumb/Upbit fee tier / tick / min notional |
| 학습 곡선 / 디버깅 | 6 | 개인 platform = "내가 언제든 이해/수정 가능" 가치 |

총점 = Σ(점수 × weight) — 5 점 만점 weight 사용, 100점 환산.

## 7. 설계 서사

### 7.1 Sonnet 결정 = Codex 권장 그대로 채택

**Self-built core engine** (BacktestExecutor / ExecutionSimulator / Ledger / SimulatedClock / Event log). **외부 라이브러리 = reporting/analytics adapter only** (event log read-only).

근거:
- Self-built 88 vs 차순위 Nautilus 72 = 격차 16점 (sensitivity 견고)
- mctrader 의 8-state lifecycle / event sourcing / Korean exchange constraints / mode-agnostic StrategyContext = 일반 백테스터 범위 초과
- 라이브러리 adoption cost = "기능 재사용" 보다 "mapping 유지비"
- Architecture purity 외에도 lock-in risk 가 가장 큰 재앙 = "백테스트와 라이브가 다른 시스템"

### 7.2 Hybrid boundary 정책

**허용되는 hybrid**:
- mctrader-engine = event log + canonical fills/trades 생성
- reporting adapter = event log → dataframe 변환
- vectorbt / pandas / empyrical = metrics / plot 일부 계산 (event log read-only)
- walk-forward runner = mctrader engine 반복 호출 + split / aggregation

**피해야 할 hybrid**:
- 일부 strategy = self-built engine, 일부 strategy = vectorbt simulation
- 일부 order = mctrader simulator, 일부 fee/slippage = library broker
- event log vs library trade history 가 source-of-truth 다툼
- Strategy interface 가 backtest 에서 vectorized / live 에서 event-driven 으로 갈라짐

핵심 원칙: **canonical truth = 항상 mctrader event log**. 외부 라이브러리는 read-only.

### 7.3 19 결정 (1 main + 10 hidden + 8 sub)

| # | 결정 |
|---|---|
| **D1 Main** | Self-built core engine 채택 |
| **D2** | 외부 lib = post-process adapter only (event log read-only) |
| **D3** | vectorbt = optional reporting adapter (canonical 아님) |
| **D4** | backtrader / Nautilus / freqtrade = core 거부 |
| **H1 data format** | canonical = Parquet/DuckDB. library-specific = adapter only. |
| **H2 candle decision timing** | event log 에 `observed_until_ts` / `decision_ts` / `eligible_fill_ts` / `fill_ts` 4 timestamp 명시. lookahead audit 의 mechanism. |
| **H3 fee/slippage ownership** | `ExecutionSimulator` 가 소유. exchange rule provider (Bithumb/Upbit fee tier / KRW tick / min order) 주입. library default 사용 금지. |
| **H4 multi-pair portfolio constraint** | central ledger 가 KRW cash / reserved cash / open order exposure 관리. ordering rule = (timestamp 우선, 동일 시 strategy priority → symbol sort → score rank). |
| **H5 100% Python core** | core engine = pure Python. DuckDB/Polars/NumPy 같은 well-supported native dep 만 허용. Cython/Rust 기반 framework lock-in 금지 (MVP). |
| **H6 event schema versioning** | event log 처음부터 `schema_version` 필드. event types 명확 분리: `OrderIntentCreated` / `RiskDecisionRecorded` / `OrderAccepted` / `FillRecorded` / `BalanceUpdated` 등. |
| **H7 metrics source** | event log + ledger snapshot 에서 계산. 외부 lib stats = supplementary only. equity curve 정의 (realized vs mark-to-market) = MCT-6 결정. |
| **H8 WFO runner** | self-built, fold 마다 동일 backtest engine 호출. fold split / training / validation / embargo / parameter selection 명세 = MCT-6. vectorbt fast sweep = parameter exploration helper only. |
| **H9 strategy determinism** | random seed + clock + visible data window 주입. run metadata = code version + data version + parameter hash + seed. ML/optimization non-determinism 진입 시점 별도 처리. |
| **H10 ADR-003 결정 문장** | "mctrader 는 Backtest core engine 을 self-built. 외부 backtesting framework 는 canonical execution / order lifecycle / ledger / event sourcing 의 source-of-truth 채택 안 함. BacktestExecutor = orchestration only. vectorbt 등 외부 라이브러리 = event log 에서 파생된 reporting/research adapter only." |
| **D5 LOC estimate** | MVP 3,000-5,000 LOC / production-trustworthy v1 6,000-12,000 LOC (개인 백테스터 기준). |
| **D6 점진 발전 path** | MCT-12 minimal = single exchange + 5분/1시간/1일 candle + market/limit minimal lifecycle + simple slippage bps + event log + basic PnL/MDD. → MCT-6 이후 = composite slippage E + partial fill + latency + multi-pair + WFO. |
| **D7 Nautilus 채택 trigger** | mctrader 가 multi-venue + tick-level + low-latency + production-grade execution 으로 진화 시점 재평가. 현재 단계 채택 = 학습 곡선 + native dep + framework ownership cost 과다. |
| **D8 freqtrade benchmark** | freqtrade core adoption 거부 사유 ADR 명시. 그러나 freqtrade 의 hyperopt / reporting / dry-run 흐름 = design benchmark 로 검토 의무 (참고만). |

### 7.4 Self-built 의 대형 risk = reporting/WFO underbuild

Codex 가 명시적으로 challenge: \"self-built 가 실패하는 전형적인 이유는 execution core 가 아니라 metrics / experiment tracking / parameter sweep / OOS split / result comparison 이 미완성으로 남는 것\".

대응:
- ADR-003 §C5 에 \"reporting / WFO underbuild = 본 ADR 의 가장 큰 risk\" 박제
- MCT-6 walk-forward Story 의 priority = high (MCT-12 first end-to-end 후 즉시)
- MCT-12 minimal 단계의 metrics = basic PnL / MDD / win rate / turnover / exposure 만. 나머지 (Sharpe / Sortino / Calmar / variance metric / regime analysis) = MCT-6 이후
- vectorbt adapter = MCT-6 시점 부터 \"metrics calculation 가속화\" 용도로 검토 — event log → vectorbt dataframe 변환만, simulation 위임 안 함

### 7.5 Codex 의견 적용 결과

Codex (codex-rescue, gpt-5.5 high) Sonnet decider second-opinion. 19 결정 (1 main + 10 hidden + 8 sub) 중:

- **Codex 권장 그대로 채택**: 19/19
- **Sonnet 거부**: 0
- **부분 수용**: 0

Codex 권장이 모두 strong evidence. 거부할 근거 없음. 본 결과 는 MCT-2 (19/19 채택) 와 동일 — Codex 가 substantive multi-decision 의 quality 안정적 검증.

### 7.6 Anti-pattern prevention 검증

Codex 명시 anti-pattern 4:

- [x] 라이브러리 lock-in 후 architectural decision 충돌 → D1 self-built 로 회피
- [x] self-built reporting/WFO underbuild → §C5 risk 박제 + MCT-6 priority high
- [x] Hybrid boundary 갈라짐 (디버깅 어려움) → §7.2 명확한 boundary 정책
- [x] backtest vs live 가 다른 시스템 → MCT-2 의 mode-agnostic StrategyContext + 본 ADR 의 self-built 일관성 ↔

## 8. 개발 서사

(Phase 2 PR — 본 Story 는 doc-only. 실제 코드는 mctrader-engine 의 향후 Story.)

## 9. 품질 게이트 이력

(Phase 2 PR — N/A for doc-only Story.)

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

## 11. 회고

본 Story = MCT-2 의 Codex 종합 review → Sonnet 결정 패턴 2회차 적용. 결과:

- **사용자 stop = 1회** (시작 trigger 만, MCT-2 와 동일)
- **Codex 권장 채택률 19/19** (MCT-2 = 19/19, MCT-3 = 19/19 — 패턴 안정성 검증)
- **Codex score matrix 격차 16점** (Self-built 88 vs Nautilus 72) — sensitivity 견고
- **freqtrade benchmark requirement** = Codex 의 명시적 surface — \"채택 안 하더라도 design 비교 의무\". ADR Alternatives 에 박제.
- **Self-built 의 underbuild risk** = ADR §C5 + MCT-6 priority high 로 mitigation 명시

본 패턴 (Codex 종합 review → Sonnet 결정) 의 efficiency = MCT-3 도 sub-decision stop 0회. MCT-4 ~ MCT-11 동일 적용 가능.
