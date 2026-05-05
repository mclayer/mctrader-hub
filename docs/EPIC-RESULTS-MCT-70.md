---
epic_key: MCT-70
status: closed
closed_at: 2026-05-05
related_adrs: ADR-002, ADR-006, ADR-009
---

# Epic MCT-70 — T2/T3 Backtest Lifecycle Integration

## Trigger

사용자 발화 (2026-05-05):
> "진행해라"

선행 context: Epic MCT-63 (Tick + Orderbook Backtest, 8 PR) 종료 시 명시적으로 deferred:

> "TickReplayExecutor lifecycle wiring through web `/backtests` POST (v1 = endpoint contract only)"

Codex review TOP RECOMMENDATION 채택 — **largest debt = API/product mismatch**: T2/T3 strategies 중요 선언 + UI selector 노출 + POST `/backtests` = 422 (Literal["sma"] only).

## Phases

| Phase | PR | merge SHA | scope |
|---|---|---|---|
| Phase 1 | mctrader-hub#86 | (squash) | Epic doc + 4 child Story stub |
| Phase 2 | mctrader-web#10 | (squash) | MCT-71 BacktestRequest tier-aware + 422 coverage validation (0.9.0) |
| Phase 3 | mctrader-web#11 | (squash) | MCT-72 BacktestLifecycleManager polymorphic dispatch (0.10.0) |
| Phase 4a | mctrader-engine#27 | 25cd1954 | MCT-73 TickReplayResult.equity_rows() + fills serialization (0.28.0) |
| Phase 4b | mctrader-web#12 | (squash) | MCT-73 equity_curve.csv + /tick_detail real data wire (0.11.0) |
| Phase 5 | mctrader-web#13 | (squash) | MCT-74 Streamlit T2/T3 tick result viewer (0.12.0) |
| Phase 6 (close) | mctrader-hub#TBD (this PR) | — | EPIC-RESULTS-MCT-70 + 5 child Story close + memory |

**Single-day Epic** (2026-05-05). 7 PRs across 3 repos (hub + engine + web). data repo 영향 0건 (이미 MCT-66 완료).

## Codex review summary

**Codex 7-area review** (codex-rescue, gpt-5 high, 2026-05-05):

> **TOP RECOMMENDATION**: T2/T3 Backtest Lifecycle Integration — closes the deferred obligation from MCT-63, directly resolves the API/product mismatch debt.
>
> **DEBT WARNING**: Largest debt = T2/T3 reachable via 직접 Python only, not 표준 UI/API surface. Result reproducibility partially valuable until manifests = lifecycle-owned. Do NOT prioritize L3 depth-ladder (Bithumb public WS = L2 only, hard external constraint).

Sonnet decider 12/12 escalation 0건 (A1 / B1 / C1 / D1 / E1 / F1 / G1 / H1 / I1 / J1 / K1 / L1).

## Backtest infrastructure delta

**Before Epic**:
- `BacktestRequest.strategy: Literal["sma"]` only
- `BacktestLifecycleManager._run_backtest` hardcoded `SmaStrategy(fast, slow)` + `BacktestExecutor`
- T2/T3 strategy 직접 Python call only (`TickReplayExecutor`, MCT-67)
- MCT-69 `/tick_detail` v1 = 빈 페이지 stub
- Streamlit `02_backtest_panel.py` strategy selector 가 T2/T3 표시하지만 POST 시 422

**After Epic**:
- `BacktestRequest.strategy: str` (registry lookup)
- POST `/backtests` 에서:
  - registry resolution + `"sma"` → `"sma_v1"` legacy alias
  - 미등록 strategy = 422 `detail.error="unknown_strategy"` + available list
  - `REQUIRED_DATA_TIERS - {CANDLE}` 비어있지 않은 경우 (T2/T3) `tier_coverage` 의무 호출 → 부족 시 422 `detail.error="tier_coverage_insufficient"` + missing_tiers + windows
- `_run_backtest` polymorphic dispatch: T1 (CANDLE only) = `BacktestExecutor` / T2/T3 = `TickReplayExecutor`
- `<run_dir>/manifest.json` persisted (TickReplayResult.write — matching_model + fills + collector_run_ids + latency_config)
- `<run_dir>/equity_curve.csv` post-process (T1 schema parity, `result.equity_rows(initial_cash)` → `EquityCurveWriter`)
- `GET /backtests/{id}/tick_detail` 실 데이터 노출 (manifest read + cursor pagination + downsample)
- Streamlit `02_backtest_panel.py` conditional render: T1 = 기존 chart, T2/T3 = 5 metric + downsample slider + per-fill DataFrame + equity curve

## Sonnet decider 자율 결정 핵심

- BacktestRequest.strategy = `str` (Literal 제거, registry lookup)
- Legacy alias `"sma"` → `"sma_v1"` (run_id = `bt-sma_v1-...` 변경, breaking 미세)
- POST handler 진입 시 tier coverage 의무 (큐잉 비용 회피)
- 422 detail schema = `error / strategy / available / missing_tiers / requested_window / available_windows`
- Polymorphic dispatch = if/else (premature polymorphism 거부)
- TickReplayExecutor 호출 = template default param (kwargs 미수락 v1)
- T2/T3 final_equity = final_cash + position_qty * last_fill_price (mark-to-market proxy)
- equity_curve.csv = T1 schema parity (시작 row + per-fill row + 종료 row)
- /tick_detail cursor = base64({fill_index: int}) opaque
- downsample = ts-window seconds, last_emit_ts gating
- Streamlit 분기 = `st.stop()` early exit (T1 render block 보호)
- 동일 page (별도 page 분리 거부 — UX consistency)

## Out-of-scope (확정 거부)

- Strategy-specific param injection via API (template default only v1)
- Multi-strategy single backtest (별도 후속 Epic)
- L3 depth-ladder snapshot (ADR-009 §D9 reservation)
- T2/T3 ADR-006 WFO promotion (별도 후속 Epic)
- Live mode tick execution (별도 후속 Epic)
- TickReplayExecutor cancel via DELETE
- Cross-symbol portfolio T2/T3
- WebSocket / SSE for tick_detail
- Strategy registry hot-reload
- T2/T3 Paper-mode parity (Paper tick callback)
- Custom matching_model selection
- queue_position / book_top_bid/ask in TickDetailPoint (manifest 미저장 — TickReplayExecutor 가 fill 시점 book context 미기록)

## Total stop count Epic MCT-70

User stops: 0 ("진행해라" 단일 trigger 후 admin merge autonomy + Sonnet decider auto-proceed 패턴 적용).

## Manual deployment prerequisite

본 Epic 의 모든 T2/T3 전략 backtest 는 **collector 가동 후 누적 기간 만큼만 가능** (변경 없음, MCT-63 동일).

사용자 명시 (2026-05-04): "가동은 추후 하도록 하고" — 본 Epic 종료 후 별도 시점에 사용자가 Linux server collector 가동 + ~1주 누적 후 T2/T3 backtest 가능.

## Related work

- MCT-63 (Tick + Orderbook Backtest) — 본 Epic 의 deferred obligation 봉합
- MCT-67 (TickReplayExecutor) — 본 Epic dispatch target
- MCT-69 (Web UI tick backtest stub) — 본 Epic 가 v1 stub 봉합 (`/tick_detail` 실 데이터 + selector POST 가능)
- MCT-66 (orderbook reconstruction + tier_coverage) — 본 Epic 의 422 검증 의존
