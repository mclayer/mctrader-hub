---
story_key: MCT-16
status: phase:대기
component: engine
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-009, ADR-010, ADR-011
---

# MCT-16: mctrader-engine BacktestExecutor + SMA strategy + ExecutionReport

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-16: mctrader-engine BacktestExecutor + SMA strategy + 결과"

## 2. 목표

`mctrader-engine` repo:
- `BacktestExecutor` (ADR-002 TradeExecutor Protocol 의 Backtest impl)
- SMA fast/slow crossover strategy (ADR-005 lookahead bias 4-layer 통과 의무)
- Slippage/Fee/Latency 적용 (ADR-004) — Backtest mode 의 simulated fill
- ExecutionReport JSON + equity_curve.csv 산출 (ADR-004 schema)
- RiskGate minimal pass-through hook (ADR-007 — full integration 별도 Epic)
- CLI entrypoint: `mctrader-cli backtest --strategy sma --symbol KRW-BTC --tf 1h --start <T-7d> --end <T> --fast 5 --slow 20`
- StrategyContext mode-agnostic (ADR-002 — visible_window API 만 노출)

## 3. 시작 조건

- MCT-13 Phase 2 merge — Candle/Order Protocol freeze
- MCT-15 Phase 2 merge — Storage read API freeze
- MCT-14 Phase 2 merge — raw fixture (deterministic test input)
- 첫 publish version = `0.1.0`

## 4. 의존

- 상위 의존: ADR-002 / ADR-003 / ADR-004 / ADR-005 / ADR-006 / ADR-007, MCT-13, MCT-14, MCT-15
- 하위 의존자: MCT-17 (Streamlit reads equity_curve.csv)

## 5. Acceptance (placeholder — Phase 1 brainstorm 에서 확정)

- TBD: SMA signal 생성의 vectorized vs event-driven (ADR-003 self-built core)
- TBD: lookahead 4-layer 의 minimal subset (signal timestamp align + warmup exclude + next-bar fill + future candle access guard)
- TBD: ExecutionReport JSON 구조 (top-level keys)
- TBD: equity_curve.csv schema (timestamp + equity + position + pnl)
- TBD: RiskGate hook 의 interface placeholder
- TBD: CLI option set + default value 충돌 검증

## 6. Phase 1 brainstorm 진행

MCT-13 + MCT-15 Phase 2 merge 후 Codex 일괄 dispatch → Sonnet 합성 → Story doc → Phase 1 PR. (가장 큰 single Story — ADR 7 건 동시 적용.)

## 7. CFP-60 debut-audit

Phase 2 merge 직후 audit signal check + 7-카테고리 평가. **R3 (lookahead 4-layer infra friction) high-severity = 본 Story 가 첫 strategy 의 검증.**
