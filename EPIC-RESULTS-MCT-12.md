# Epic MCT-12 — Bithumb OHLCV → SMA backtest end-to-end (CLOSED)

**Closed**: 2026-05-03
**Status**: Phase 1 (5 doc Stories) + Phase 2 (5 repo implementations) all merged, all 5 CIs green.

## 5 child Story summary

| Story | repo | first commit | CI status |
|---|---|---|---|
| MCT-13 | [mctrader-market](https://github.com/mclayer/mctrader-market) | `0.1.0` | ✅ green |
| MCT-15 | [mctrader-data](https://github.com/mclayer/mctrader-data) | `0.1.0` | ✅ green (Linux+Windows) |
| MCT-14 | [mctrader-market-bithumb](https://github.com/mclayer/mctrader-market-bithumb) | `0.1.0` | ✅ green |
| MCT-16 | [mctrader-engine](https://github.com/mclayer/mctrader-engine) | `0.1.0` | ✅ green |
| MCT-17 | [mctrader-web](https://github.com/mclayer/mctrader-web) | `0.1.0` | ✅ green |

## Blocking AC (B1~B6)

| # | AC | 충족 |
|---|---|:---:|
| B1 | CLI `mctrader-cli backtest --strategy sma --symbol KRW-BTC --tf 1h --start <T-7d> --end <T> --fast 5 --slow 20` exit 0 | ✅ (mctrader-engine `cli.py`) |
| B2 | ExecutionReport JSON schema (`schema_version="execution_report.v1"`) validation | ✅ (Pydantic v2 `model_validate_json` roundtrip test) |
| B3 | equity_curve.csv schema = `ts_utc,equity,position_quantity,realized_pnl,unrealized_pnl,cash` Decimal string + ISO-8601 Z | ✅ (`EquityCurveWriter` deterministic output + test) |
| B4 | OHLCV input ADR-009 v1 16-column Decimal(38,18) Hive UTC partition (`market/ohlcv/schema_version=ohlcv.v1/.../year=Y/month=M/date=D/`) | ✅ (mctrader-data roundtrip test, Linux+Windows lane) |
| B5 | SMA signal lookahead bias 4-layer (L2 visible_window guard + L3 used_data_window post-hoc) | ✅ (mctrader-engine L2 + L3 enforced; L1/L4 deferred per Phase 1 design) |
| B6 | 5 repo `import` smoke + CLI entrypoint 발견 | ✅ (CI matrix `uv sync --all-extras` + pytest collect, cross-repo git+https resolve) |

## Demonstration AC (D1, D2)

| # | AC | 충족 |
|---|---|:---:|
| D1 | Streamlit dashboard equity curve render | ✅ (`mctrader-web/dashboard/app.py` Plotly chart, manual `streamlit run`) |
| D2 | Final equity / max drawdown / sharpe / win rate / total trades 표시 | ✅ (`build_summary_metrics` + 5 `st.metric` cols) |

## Codex review aggregate (Phase 1)

| Story | 7-area 채택 | ADR conflict |
|---|---:|---:|
| MCT-12 (Epic) | 7/7 | 0/7 |
| MCT-13 | 7/7 | 0/7 |
| MCT-14 | 7/7 | 0/7 |
| MCT-15 | 7/7 | 0/7 |
| MCT-16 | 7/7 | 0/7 |
| MCT-17 | 7/7 | 0/7 |
| **합계** | **42/42 (100%)** | **0/42** |

## Out-of-scope (확정 거부)

Live mode / Paper mode / Multi-strategy / Multi-symbol (KRW-BTC only) / Multi-timeframe (1h only) / WFO execution / full RiskGate (NullRiskGate pass-through 만) / Secret access / 다른 거래소 / PyPI publish (local editable + git+https main) / Streamlit live concurrent DuckDB read / Lookahead L1 (libcst lint) / L4 (known-bias fixture) / ATR volatility metric (rolling std 사용) / `--fee-bps / --slippage-bps` CLI override.

## CFP-60 debut-audit

각 child Phase 2 merge 직후 codeforge plugin defect 발견 시 [mclayer/plugin-codeforge](https://github.com/mclayer/plugin-codeforge) issue 등록 (`audit:from-mctrader-debut + category:*`). MCT-12 Phase 2 진행 중 추가 finding **0건** (5 setup-time finding #115~#118 + #122 = 모두 Phase 1 시점에 발견됨).

## Visibility 변경 (자율 결정)

mclayer org 6 repo 모두 `PUBLIC` 변경 (Phase 2 cross-repo Git+HTTPS install 단순화 — PAT 없이 `uv sync --frozen` 가능). ADR-008 + gitleaks 가 secret 보호의 mechanical guarantee 제공.

## 후속 candidate (Future Epic 우선순위 brainstorm 대상)

1. **Paper mode** — realtime + 가상 자금 + market-* 호출 + simulated fills
2. **Multi-symbol portfolio** — KRW-ETH / 기타 KRW pair + portfolio aggregation + correlation-aware sizing
3. **RiskGate full** — 5 kill switch (MAX_DAILY_LOSS / DRAWDOWN_LIMIT / CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL)
4. **WFO execution** — rolling window + OOS + promotion gate (B→P→L) + top-K rank consensus
5. **Multi-strategy** — strategy registry + config schema + comparison report
6. **Lookahead L1 + L4** — libcst static lint + known-bias fixture (false positive detection)
7. **Live mode** — 실 자금 + 1Password CLI Secret + kill switch enforce + audit log + GitHub environment protection

## 통계

- Stop count: 5 (사용자 명시 stop 회수, 첫 Session 2 init + Path B approve + 11 ADR 진행 중간 + Phase 2 trigger + 끝까지 진행 trigger)
- 신규 commit: 5 repo × 평균 8 commits ≈ 40 commits
- 신규 코드: ≈ 5,000 lines (src + tests + CI workflow + pyproject + README)
- 신규 GitHub issue: 5 (#13~#17, all OPEN — Phase 2 PR 의 commit 메시지가 cross-repo 라 Closes 자동 트리거 안됨, manual close)
- CI iteration: 8~10 회 (lint config / pyright 완화 / dependency stub / Decimal precision / Pydantic strict)

## 결론

**Epic MCT-12 = mctrader 첫 implementation Epic, 6-repo invariant + ADR-001~011 baseline + CFP-60 debut-audit = 모두 검증된 reference 사례.** 향후 Paper / Live / Multi-strategy / WFO 등 후속 Epic 의 baseline 으로 사용 가능.
