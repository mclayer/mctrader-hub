---
story_key: MCT-21
status: phase:대기
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-002, ADR-004, ADR-005, ADR-008, ADR-010, ADR-011
---

# MCT-21: mctrader-engine PaperExecutor + RealtimeClock + BarAggregator + VirtualPortfolio + SimulatedFillEngine

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "PaperExecutor core (TradeExecutor Protocol Paper impl)"

## 2. 목표

`mctrader-engine` repo 확장:
- `executor/paper.py` — `PaperExecutor` (TradeExecutor Protocol impl)
- `realtime/clock.py` — `RealtimeClock` (vs `SimulatedClock`)
- `realtime/aggregator.py` — `BarAggregator` (closed bar only dispatch, ADR-005 L2 보존)
- `realtime/stream_consumer.py` — `MarketStream` Protocol → BarAggregator wire
- `account/virtual.py` — `VirtualPortfolio` (cash + position simulation)
- `fill/simulated.py` — `SimulatedFillEngine` (orderbook-aware reference price + composite slippage + latency proxy)
- `cli.py` extension — `paper` subcommand placeholder

## 3. 시작 조건

- ✅ MCT-12 freeze (mctrader-engine 0.1.0)
- ✅ MCT-18 Phase 1 PR merge
- ✅ MCT-19 freeze (`MarketStream` Protocol)
- MCT-20 freeze 권장 (paper write-side)

## 4. 의존

- 상위: ADR-002 / ADR-004 / ADR-005 / ADR-008 D5
- 하위: MCT-22 RiskGate hook, MCT-23 calibration metric

## 5. Acceptance (placeholder)

- TBD: SmaStrategy mode-agnostic 검증 (Backtest 와 동일 코드)
- TBD: BarAggregator partial bar state 관리 (1m candle 의 60 분 aggregation)
- TBD: SimulatedFillEngine 의 orderbook depth handling (BUY ask sweep / SELL bid sweep)
- TBD: latency proxy naming / emission to ExecutionReport (`market_data_latency_ms` / `public_endpoint_rtt_ms` / `decision_to_fill_delay_ms`)
- TBD: graceful termination (SIGTERM / duration 만료) + final ExecutionReport flush
- TBD: real broker API call 절대 X mechanical 검증 (test_policy_imports)

## 6. Phase 1 brainstorm

MCT-19 + MCT-20 freeze 후 Codex 일괄 dispatch → Sonnet 합성 → docs/stories/MCT-21.md 본 brainstorm → Phase 1 PR. **MCT-18 의 가장 큰 single Story** (executor + 4 components 동시 적용).

## 7. CFP-60 debut-audit

Phase 2 merge 후 audit signal check (특히 lane-progression + workflow-invariant + decision-table).
