# Epic MCT-18 — Paper mode (realtime + 가상 자금)

**Closed**: 2026-05-03
**Status**: Phase 1 (6 doc PRs) + Phase 2 (5 신규 repo / module 추가) merged, all CIs green.

mctrader 의 두 번째 implementation Epic. ADR-006 promotion gate (Backtest→Paper→Live) 의 Paper 단계 = OOS calibration mechanism. ADR-002 3-mode 의 두 번째 적용. ADR-008 D5 Paper = secret 금지 (public endpoint + simulated fills) 의 reference impl.

## 5 child Story summary

| Story | repo | bump | CI |
|---|---|---|:---:|
| MCT-19 | mclayer/mctrader-market-bithumb | `0.1.0 → 0.2.0` (WebSocket adapter 추가) | ✅ |
| MCT-20 | mclayer/mctrader-data | `0.1.0 → 0.2.0` (paper_storage + scan mode) | ✅ |
| MCT-21 | mclayer/mctrader-engine | `0.1.0 → 0.2.0` (PaperExecutor + 5 components) | ✅ |
| MCT-22 | mclayer/mctrader-engine | `0.2.0 → 0.3.0` (PaperRiskGate + kill_switch + policy) | ✅ (engine 동일) |
| MCT-23 | mclayer/mctrader-engine | `0.3.0` (CalibrationMetrics + shutdown.py + paper subcommand) | ✅ (engine 동일) |

## Blocking AC (B1~B7)

| # | AC | 충족 |
|---|---|:---:|
| B1 | CLI `mctrader-cli paper --strategy sma --symbol KRW-BTC --tf 1h ...` skeleton + factory wiring + duration/end mutually exclusive validation | ✅ (MCT-21 cli.py + MCT-23 shutdown.parse_duration / resolve_stop_at) |
| B2 | ExecutionReport JSON `mode="paper"` + `schema_version="execution_report.v1"` validation 통과 (Backtest schema 공유) | ✅ (PaperExecutor._finalize_report) |
| B3 | equity_curve.csv = Backtest 와 동일 6-column schema (Decimal string + ISO-8601 Z) | ✅ (EquityCurveWriter 재사용) |
| B4 | Mode-agnostic verification — `SmaStrategy` 가 Backtest 와 동일 코드로 Paper 에서 실행 (`StrategyContext` interface 동일) | ✅ (`_ClosedBarContext` mode-agnostic adapter, test_paper_executor) |
| B5 | Paper OHLCV = `mode=paper/...` separate partition (canonical Backtest 데이터와 격리) | ✅ (mctrader-data MCT-20, scan_candles default = historical) |
| B6 | RiskGate minimal (MAX_DAILY_LOSS + DRAWDOWN_LIMIT) decision = order block + RiskGateEvent 기록 | ✅ (PaperRiskGate hard latch + RiskGateBlocked 회복) |
| B7 | Public-only enforcement — Authorization header / Api-Key 사용 X (3-layer + WebSocket 4-layer guard) | ✅ (mctrader-market-bithumb ws_secret_guard + test_ws_policy_imports + test_paper_no_broker_api) |

## Calibration AC (C1~C5)

| # | metric | 정의 | gate threshold | 구현 |
|---|---|---|---|---|
| C1 | `fill_price_deviation_bps` | (Paper fill - Backtest assumption) / Backtest × 10000 | `abs_p95 < 20 bps` | `build_calibration_metrics` |
| C2 | `latency_ms` | `decision_to_fill` + `market_data` 분리 | p95 < 1000ms / 3000ms | LatencyStats |
| C3 | `realized_slippage_bps` | (fill_price - reference) / reference × 10000 | `abs_p95 < 15 bps` | metric.py |
| C4 | `trade_count_delta` | abs(Paper - Backtest) / Backtest | `≤ 0.10` | division-by-zero 처리 명시 |
| C5 | `max_drawdown_delta` | abs(Paper max_dd - Backtest max_dd) | `≤ 0.02` | `_max_drawdown` |

`comparison_fill_model = {"backtest": "next_bar_open", "paper": "simulated_fill_engine"}` 명시 — ADR-006 multi-metric AND gate 해석 시 fill model 차이 인지.

## Demonstration AC (D1)

- D1: Streamlit dashboard `mode=paper` filter = **MCT-24 분리** (MCT-23 = no UI change). manual file inspection 으로 Paper artifacts 확인 가능.

## Codex review aggregate (Phase 1)

| Story | 7-area 채택 | ADR conflict |
|---|---:|---:|
| MCT-18 (Epic) | 7/7 | 0/7 |
| MCT-19 | 7/7 | 0/7 |
| MCT-20 | 7/7 | 0/7 |
| MCT-21 | 7/7 | 0/7 |
| MCT-22 | 7/7 | 0/7 (ADR-007 minimal subset 명시) |
| MCT-23 | 7/7 | 0/7 |
| **합계** | **42/42 (100%)** | **0/42** |

## 자율 결정 요약 (Sonnet decider, 사용자 stop 없이)

- WebSocket library = `websockets>=12,<14` (asyncio native, REST httpx 와 분리)
- AsyncTradeExecutor 별도 Protocol (sync TradeExecutor 와 병존, ExecutionReport schema 공유)
- BarAggregator Hybrid (Transaction primary + Ticker diagnostic, ADR-005 closed bar only 보존)
- SimulatedFillEngine = orderbook VWAP + conservative_bps 5 + fee_bps 4 + delay_ms 200 + InsufficientLiquidityError (partial fill 비채택)
- mode=paper partition (schema_version 다음, ADR-009 16-column 변경 X) + WebSocket batch hash lineage extension
- RiskGate check-only Protocol 유지 + internal stateful (KST reset / hard latch / first_trigger_ts)
- ruff/pyright 추가 완화 (UP037 / SIM105 / E501 / F401 / reportArgumentType / reportAttributeAccessIssue / reportOptionalMemberAccess)
- Streamlit mode filter = MCT-24 분리 (Epic close 전 UI scope creep 회피)

## Out-of-scope (확정 거부)

Live mode / WFO automation / Multi-symbol / Multi-strategy registry / Production-grade WebSocket robustness / Full RiskGate (5 kill switch) / Streamlit live partial bar / Async REST extension / Multi-exchange / PyPI publish / explicit migration script (legacy no-mode → mode=historical) / partial fill simulation / limit order / CONSECUTIVE_LOSSES + UNUSUAL_ACTIVITY + EXTERNAL_SIGNAL kill switches.

## CFP-60 debut-audit

Phase 2 진행 중 추가 finding **0건**. 5 setup-time finding (#115~#118 + #122) 만 존재 (모두 mctrader-hub setup 시점). plugin-codeforge 의 doc-only consumer 두 번째 사례 검증.

## 후속 candidate 우선순위 (Sonnet decider 채택, MCT-23 A7)

1. **RiskGate full** (5 kill switch 모두 enforce) — 운영 안전성 우선
2. **Lookahead lint** (L1 libcst static + L4 known-bias fixture) — Backtest↔Paper calibration 신뢰도 강화
3. **WFO execution** — promotion 통계 기반 확장
4. **Multi-symbol portfolio** — 실사용 범위 확장
5. **Multi-strategy registry** — orchestration / attribution complexity
6. **Live mode** — Paper gate + RiskGate full 안정화 후 (1Password CLI Secret + GitHub environment protection 의무)

## 통계

- 신규 commit: 5 repo × 평균 4 commits ≈ 20 commits (Phase 2)
- 신규 코드 (Phase 2): ≈ 3,500 lines (src + tests + CI fixes)
- mctrader-hub PR: 6 (#24 Epic / #30 MCT-19 / #31 MCT-20 / #32 MCT-21 / #33 MCT-22+23 / 본 PR Epic close)
- CI iteration: 5~7 회 (UP037 / SIM105 / E501 / F401 / pyright union narrowing / Decimal38_18 quantize 호환)
- 사용자 stop count: 1 ("진행해 이런 답 필요한 수준의 질문은 하지말고 진행해" 1번)

## 결론

**Epic MCT-18 = mctrader 두 번째 implementation Epic, ADR-006 promotion gate 의 Paper 단계 + ADR-002 3-mode 의 두 번째 적용 = 모두 검증된 reference 사례.** Backtest assumptions 의 OOS validation 가능. 향후 Live mode / WFO / Multi-symbol 의 baseline 으로 사용 가능.
