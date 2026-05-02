---
adr_id: ADR-003
title: Backtest engine = self-built core + 외부 lib = reporting adapter only
status: Accepted
date: 2026-05-02
related_story: MCT-3
category: backtest
supersedes: []
amends: []
---

# ADR-003: Backtest engine 라이브러리 선정 — Self-built core + 외부 lib reporting adapter only

## Status

**Accepted** — 2026-05-02. MCT-3 Story Phase 1 PR 의 산출물.

## Context

mctrader 의 Backtest engine 라이브러리 선정. 후보:
- self-built (mctrader-engine 내부)
- vectorbt (vectorized, pandas)
- backtrader (event-driven, mature)
- Nautilus Trader (production-grade, Cython)
- freqtrade (crypto-specific)
- bt / backtesting.py / zipline / pyalgotrade / Hummingbot / 기타

이미 결정된 architectural constraints (MCT-1 / MCT-2):
1. Bithumb #1 → Upbit #2 (한국 KRW only)
2. 3 mode (Backtest/Paper/Live) = 동일 TradeExecutor Protocol 의 3 impl
3. TradeExecutor Protocol minimal trade-only + 별도 MarketDataProvider
4. StrategyContext = mode-agnostic
5. BacktestExecutor = orchestration only
6. Composite slippage + 8-state Order lifecycle + Lookahead bias 강제 + Event sourcing + SimulatedClock + UTC store

라이브러리 채택은 이 architecture 와 충돌하지 않아야 함. 본 ADR 의 핵심 framing = \"좋은 backtester 고르기\" 가 아니라 **boundary alignment + lock-in risk + 신뢰성 + 개발 속도**.

본 ADR 의 결정 범위:
- core engine = build-vs-buy 결정 (D1)
- Library boundary 정책 (D2-D4)
- 10 Hidden decisions (data format / decision timing / fee ownership / multi-pair / Python-only / event versioning / metrics / WFO / determinism / ADR wording)
- LOC estimate / 점진 발전 path / Nautilus 채택 trigger / freqtrade benchmark 의무

## Decision

### D1. Self-built core engine 채택 (main)

**mctrader 는 Backtest core engine 을 self-built 로 구현**. 외부 backtesting framework 는 canonical execution / order lifecycle / ledger / event sourcing 의 source-of-truth 채택 안 함.

`BacktestExecutor` = orchestration only. 공통 책임:
- `ExecutionSimulator` (composite slippage + partial fill + latency)
- `Ledger` (multi-pair central portfolio + KRW cash + reserved cash + open order exposure)
- `SimulatedClock` (deterministic, UTC)
- `MarketDataReader` (Parquet/DuckDB read)
- `RiskGate` (3 mode 공유 interface)
- `ExchangeCapabilities` (Bithumb/Upbit fee tier / KRW tick / min notional / precision)

근거:
- Codex score matrix: Self-built **88** > Nautilus 72 > vectorbt/freqtrade 57 > backtrader 51. 격차 16점 sensitivity 견고.
- mctrader 의 architectural requirements (8-state lifecycle / event sourcing / Korean exchange constraints / mode-agnostic StrategyContext) = 일반 backtester 범위 초과
- 라이브러리 adoption cost = \"기능 재사용\" 보다 \"mapping 유지비\"
- 가장 큰 재앙 risk = \"백테스트와 라이브가 다른 시스템\" — self-built 가 mode-agnostic Strategy / Executor consistency 가장 잘 보존

### D2. 외부 라이브러리 = post-process / reporting adapter only

외부 라이브러리는 **event log read-only adapter 로만 사용 가능**:
- 허용: event log → dataframe 변환 + metrics / plot 일부 계산 + WFO split helper
- 금지: order/fill/balance 결정 위임 / Strategy interface 변경 / source-of-truth 다툼

**canonical truth = 항상 mctrader event log**. 외부 lib 결과 ↔ event log 충돌 시 event log 가 우선.

### D3. vectorbt = optional reporting adapter (canonical 아님)

vectorbt 의 vectorized stats / plot / parameter sweep helper 는 **event log 에서 파생된 reporting/research adapter 로 사용 가능**. 단:
- vectorbt portfolio simulation 결과 = canonical backtest result 절대 아님
- Strategy 가 vectorbt vector op 형태로 작성되는 것 금지 (StrategyContext 일관성 위반)
- vectorbt = MCT-6 walk-forward Story 시점부터 \"metrics calculation 가속화\" 용도 검토

### D4. backtrader / Nautilus / freqtrade = core 거부

**backtrader 거부 사유**: Cerebro-centric architecture 가 StrategyContext / TradeExecutor 와 충돌. event-driven 장점 있으나 framework lock-in + maintenance confidence 약함. Score 51.

**Nautilus Trader 거부 사유**: production-grade event-driven framework 자체는 mctrader 와 alignment 일부 있으나, complexity + native dep (Cython) + framework ownership cost 가 personal project 단계 과다. domain model 이 더 강해 mctrader 가 Nautilus wrapper 가 될 위험. Score 72 (차순위) 이나 D7 trigger 까지 채택 보류.

**freqtrade 거부 사유**: crypto-specific 으로 \"wheel reinventing\" challenge 의 가장 강한 후보. 그러나 자체 strategy interface / config / exchange abstraction / risk 가 mctrader 의 6-repo + KRW base + DuckDB/Parquet + own Executor Protocol 과 lock-in. core adoption 시 architecture 상당 포기 필요. Score 57.

**나머지 후보 거부 사유 요약**:
- bt: portfolio backtester, order/execution 약함
- backtesting.py: 단순, multi-pair / 8-state / event sourcing 부족
- zipline / zipline-reloaded: 미국 주식 가정 + maintenance 약함
- pyalgotrade: deprecated / Python 3.11 호환 의문
- Hummingbot: live bot framework, backtest engine 후보 부적합
- finmarketpy / 기타: 범위 mismatch

### D5. 10 Hidden decisions (Codex surface, Sonnet 채택)

| H# | 결정 |
|---|---|
| H1 Backtest data format | canonical = Parquet/DuckDB. library-specific format = adapter only. OHLCV schema (`exchange / symbol / timeframe / ts_utc / open / high / low / close / volume / value / source_ingested_at`) — MCT-9 상세. |
| H2 Candle decision timing | event log 에 4 timestamp: `observed_until_ts` / `decision_ts` / `eligible_fill_ts` / `fill_ts`. \"t candle close 본 결정 = t+1 open 이후만 fill\" 강제. lookahead audit (MCT-5) 의 mechanism. |
| H3 Fee/slippage ownership | `ExecutionSimulator` 소유. `ExchangeRuleProvider` (Bithumb/Upbit fee tier + KRW tick + min order) 주입. library default 사용 금지. |
| H4 Multi-pair portfolio constraint | central `Ledger` 가 KRW cash / reserved cash / open order exposure 관리. **Ordering rule** (동일 timestamp signal 발생 시): (1) timestamp 우선 → (2) strategy priority → (3) symbol sort → (4) score rank. 재현성 보장. |
| H5 100% Python core | core engine = pure Python. DuckDB/Polars/NumPy 같은 well-supported native dep 만 허용. Cython/Rust 기반 trading framework lock-in 금지 (MVP 단계). 성능 병목 확인 후 native acceleration 도입 가능. |
| H6 Event schema versioning | event log = `schema_version` field 처음부터. Event types: `OrderIntentCreated` / `RiskDecisionRecorded` / `OrderAccepted` / `FillRecorded` / `BalanceUpdated` 등 명확 분리. |
| H7 Metrics source | event log + ledger snapshot 에서 계산. 외부 lib stats = supplementary only. equity curve 정의 (realized-only vs mark-to-market) = MCT-6 결정. |
| H8 WFO runner | self-built, fold 마다 동일 backtest engine 호출. fold split / training / validation / embargo / parameter selection 명세 = MCT-6. vectorbt fast sweep = parameter exploration helper only (canonical 아님). |
| H9 Strategy determinism | random seed + clock + visible data window 주입. run metadata = code version + data version + parameter hash + seed. ML/optimization non-determinism 진입 시점 별도 처리. |
| H10 ADR final wording | \"mctrader 는 Backtest core engine 을 self-built 로 구현. 외부 backtesting framework 는 canonical execution / order lifecycle / ledger / event sourcing 의 source-of-truth 로 채택 안 함. BacktestExecutor 는 orchestration-only. ExecutionSimulator / Ledger / SimulatedClock / 자체 event log 가 책임. vectorbt 등 외부 라이브러리는 event log 에서 파생된 reporting/research adapter 로만 사용 가능.\" |

### D6. LOC estimate

| Component | LOC |
|---|---:|
| event loop / clock integration | 300-700 |
| market data reader / alignment | 300-800 |
| order lifecycle / execution simulator | 800-1,800 |
| ledger / portfolio accounting | 700-1,500 |
| event sourcing schema / writer / replay | 500-1,200 |
| metrics / report basics | 500-1,500 |
| walk-forward basic | 400-1,000 |
| tests / fixtures | 1,000-2,500 |
| **Total MVP** | **3,000-5,000** |
| **Total v1 (production-trustworthy)** | **6,000-12,000** |

추정 = minimal 개인 backtester 기준. multi-asset portfolio constraints + partial fill 진지 구현 시 상단.

### D7. Nautilus 채택 trigger (향후 재평가)

다음 중 하나 발생 시 본 ADR amend + Nautilus core PoC 검토 (mapping verification 필수):
1. multi-venue + tick-level + low-latency execution 요구
2. Live trading 안정성 / replay / reconciliation 이 self-built core 의 reliability 한계 초과
3. mctrader 가 personal research tool 단계 졸업 (multi-user / SaaS / 외부 traders 사용)

현재 단계 (KRW spot crypto + 10-30 pairs + candle-level backtest) = full adoption 과다.

### D8. 점진 발전 path

**MCT-12 first end-to-end 단계 (minimal)**:
- single exchange (Bithumb) KRW spot
- 5분/1시간/1일 OHLCV candle
- market/limit order minimal lifecycle (8-state subset)
- fee + tick size + min notional 적용
- deterministic next-candle-open fill
- simple slippage bps (composite 의 base_bps 만 활성)
- event log writer + replay
- basic metrics: PnL / MDD / win rate / turnover / exposure

**MCT-6 이후 (production-trustworthy v1)**:
- composite slippage E 정식화 (size factor + volatility factor 활성)
- partial fill probability model
- latency distribution model
- multi-pair portfolio-level risk constraints
- WFO runner (fold split + embargo + parameter selection)
- result comparison dashboard
- vectorbt / pandas reporting adapter
- event replay + audit UI

### D9. freqtrade design benchmark 의무

freqtrade core adoption 거부했으나 **design benchmark 로 검토 의무**. ADR-003 amend 시점 또는 MCT-6 의 hyperopt 도입 시점에 freqtrade 의 다음 항목 비교:
- hyperopt 패턴
- reporting workflow
- dry-run / live transition flow
- exchange abstraction 구조
- crypto-specific risk / protection (stoploss / trailing stop / cooldown)

비교 결과 = mctrader 의 차별 결정 ADR 명시.

## Alternatives Considered

### A1. vectorbt core engine 채택 (D3 reject)
- vectorized signal-to-portfolio simulation
- **기각 사유**: vectorized paradigm 이 mctrader 의 event-driven 8-state lifecycle / mode-agnostic StrategyContext / append-only event log 와 본질적 충돌. Strategy 가 vector op 산출 형태로 기울 위험 → Paper/Live 와 strategy code 갈라짐. lookahead bias 도 shift 한 줄 누락으로 발생 위험. Score 57.
- 단, reporting adapter 로는 유지 (D3).

### A2. backtrader core engine 채택 (D4 reject)
- event-driven, mature API (Cerebro / Strategy / Broker / Feed / Analyzer)
- **기각 사유**: Cerebro-centric architecture 가 StrategyContext / TradeExecutor 와 충돌. mctrader 가 backtrader 안에 끼워 넣거나 backtrader 를 wrapper 로 써야 → boundary 어색. Composite slippage + 8-state lifecycle + Korean exchange constraints 가 backtrader Broker/Filler/Commission model 에 mapping 시 mctrader 설계 오염. maintenance confidence 약함 (Python 3.11+ 장기 지원 의문). Score 51.

### A3. Nautilus Trader core engine 채택 (D7 trigger 까지 reject)
- production-grade event-driven, realistic order/execution model
- **기각 사유**: complexity + native dep (Cython) + framework ownership cost 가 personal project 단계 과다. domain model 이 더 강해 mctrader 가 Nautilus wrapper 화 위험. Windows/WSL/macOS deployment 비용. 단, D7 trigger 발생 시 재평가 — 현재 Score 72 차순위.

### A4. freqtrade core engine 채택 (D4 reject + D9 benchmark)
- crypto-specific, hyperopt + dry-run/live + reporting 풍부
- **기각 사유**: 자체 strategy interface / config / exchange abstraction / risk-protection 이 mctrader 의 6-repo + KRW base + DuckDB/Parquet + own Executor Protocol 과 lock-in. core adoption 시 architecture 상당 포기 필요. 단 design benchmark 의무 (D9).

### A5. Hybrid (일부 mode = self-built, 일부 mode = library)
- e.g. Backtest = vectorbt, Paper/Live = self-built
- **기각 사유**: 가장 위험한 hybrid. \"backtest 와 live 가 다른 시스템\" 은 본 ADR 이 막으려는 가장 큰 anti-pattern. mode-agnostic StrategyContext 의 의미 자체 손실.

### A6. Library 제한적 hybrid (canonical 은 self-built, library = simulation 일부)
- e.g. fee/slippage 만 library 의 broker 모델 사용
- **기각 sources of truth 다툼 risk**: ExecutionSimulator 가 일부만 책임지면 audit / lookahead prevention / partial fill realism 의 일관성 약화. 본 ADR 의 \"ExecutionSimulator 가 fee/slippage 소유 (H3)\" 와 충돌.

### A7. zipline / zipline-reloaded 채택 (D4 reject)
- institutional backtester
- **기각 사유**: 미국 주식 중심 가정 + bundle/data ingest 방식 + trading calendar model 이 KRW crypto 24/7 market 과 어긋남. maintenance 약함. Score 43.

### A8. backtesting.py 단순 채택 (D4 reject)
- 단순한 학습 곡선
- **기각 사유**: custom execution realism / event sourcing / multi-pair portfolio constraints / 8-state lifecycle 부족. mctrader core 요구에 작음. Score 47.

### A9. core engine = self-built / metrics = library 강제
- 모든 metrics 는 외부 lib 으로만 계산
- **기각 사유**: equity curve 정의 / realized vs mark-to-market 결정이 mctrader domain decision. 외부 lib stats 강제 시 mctrader 의 reporting decision 이 lib 의 default 에 종속. metrics source = event log + ledger snapshot (H7) 정합.

## Consequences

### C1. 단기 (즉시)

- mctrader-engine repo 의 backtest core 가 self-built. ADR-002 의 BacktestExecutor / ExecutionSimulator / Ledger / Clock / Event log 구조 그대로 구현 의무.
- 외부 backtesting framework dependency 추가 시 ADR-003 amend 의무 (canonical adoption 인지 adapter 인지 명시).
- vectorbt 도입 시점 = MCT-6 walk-forward Story 또는 그 이후. MCT-12 first end-to-end 에서는 vectorbt 미사용.

### C2. Reporting / WFO underbuild = 본 ADR 의 가장 큰 risk

Codex 명시 challenge: \"self-built 가 실패하는 전형 = execution core 가 아니라 metrics / experiment tracking / parameter sweep / OOS split / result comparison 미완성\".

대응:
- MCT-12 minimal 에서는 basic metrics (PnL / MDD / win rate / turnover / exposure) 만. 나머지 (Sharpe / Sortino / Calmar / regime analysis) 미구현 명시.
- MCT-6 walk-forward Story = priority high (MCT-12 직후).
- vectorbt adapter = MCT-6 시점부터 metrics 가속화 도입.
- analytics backlog 별도 관리 의무.

### C3. Lock-in risk = 내부 abstraction quality

Library lock-in 회피했으나 **self-built 의 lock-in = 내부 abstraction quality 와 maintenance budget**.

Mitigation:
- ExecutionSimulator / Ledger / MarketDataReader / Metrics 분리 명확화 (D5 layout)
- Event schema versioning (H6) — schema 변경 시 backward compatibility 명시
- 단위 테스트 + 통합 테스트 budget allocation (LOC tests/fixtures = 1,000-2,500)

### C4. 한국 거래소 specific 자체 구현

KRW exchange rules (Bithumb/Upbit fee tier / 호가 단위 / min notional / KRW pair specific) = `ExchangeRuleProvider` 가 책임 (H3). 다른 라이브러리 default 와 무관.

Bithumb #1 → Upbit #2 implementation sequence 는 ExchangeRuleProvider 의 두 instance.

### C5. freqtrade benchmark 의무

freqtrade core 채택 안 했으나 **design benchmark 의무**. 다음 시점에 freqtrade 비교 ADR 명시:
- ADR-003 amend 시점
- MCT-6 hyperopt 도입 시점
- mctrader 가 \"왜 freqtrade 를 쓰지 않았는가\" 정당화 의무

미수행 시 = wheel reinventing 인식 부재 finding.

### C6. Nautilus 재평가 trigger

D7 의 3 trigger 발생 시 본 ADR amend + Nautilus core PoC. 현재 단계 = 모니터링 only.

### C7. 본 ADR amend / supersede trigger

- self-built core 의 stable interface 변경 (BacktestExecutor signature / ExecutionSimulator interface) → amend
- 외부 lib core adoption (Nautilus / freqtrade 등) 결정 → supersede
- vectorbt 가 reporting adapter 외 영역 (e.g. canonical metrics source) 으로 promote → amend
- Hybrid boundary 정책 (D2) 변경 → amend

## Cross-references

- **MCT-3 Story** ([`../stories/MCT-3.md`](../stories/MCT-3.md))
- **ADR-001 거래소 우선순위** — Bithumb #1 / Upbit #2. 본 ADR 의 ExchangeRuleProvider 가 두 거래소 instance.
- **ADR-002 TradeExecutor + 3 mode** — 본 ADR 의 BacktestExecutor + ExecutionSimulator + Ledger + Clock 의 architecture skeleton.
- **MCT-4 (예정)** — Slippage / fee / latency 모델 상세. 본 ADR D5 의 composite parameter default.
- **MCT-5 (예정)** — Lookahead bias 자동 검증. 본 ADR H2 의 4 timestamp mechanism.
- **MCT-6 (예정)** — Walk-forward / OOS protocol. 본 ADR H8 / H7 / D8 의 promotion gate threshold + metrics formula + vectorbt adapter 도입.
- **MCT-9 (예정)** — OHLCV 스키마 v1. 본 ADR H1 의 canonical schema.
- **MCT-12 (예정 Epic)** — Bithumb OHLCV → SMA backtest end-to-end. 본 ADR D8 의 \"minimal\" 단계 구체화.
- **CFP-60** — cross-repo Epic + debut-audit. 본 ADR 의 cross-repo 의존 (mctrader-data / mctrader-market-bithumb) graph 가 Epic MCT-12 토대.

## 데뷔작 audit pre-Story note

본 Story (MCT-3) 진행 중 codeforge plugin 추가 install-time finding 발견 안 됨 (기존 5 finding #115~#118 + #122 외). \"Codex 종합 review → Sonnet 결정\" 패턴 2회차 적용 결과 = MCT-2 와 동일 19/19 채택률. 패턴 안정성 검증.
