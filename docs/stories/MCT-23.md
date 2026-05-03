---
story_key: MCT-23
status: phase:대기
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-006, ADR-004, ADR-002
---

# MCT-23: Calibration metric + CLI integration acceptance + Paper E2E

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Calibration metric (Backtest vs Paper comparison) + CLI integration acceptance + Streamlit live read"

## 2. 목표

`mctrader-engine` repo 확장:
- `calibration/metric.py` — `fill_price_deviation_bps / latency_p50_p95_ms / realized_slippage_bps / trade_count_delta / max_drawdown_delta`
- `cli.py` 의 `paper` subcommand 완성 (graceful SIGTERM + duration + final flush)
- E2E acceptance test (B1~B7 + C1~C5 + D1)
- ADR-006 promotion gate evidence artifacts
- Streamlit dashboard `mode=paper` filter (optional)

## 3. 시작 조건

- ✅ MCT-19 + MCT-20 + MCT-21 + MCT-22 freeze (모두)
- ✅ MCT-18 Phase 1 PR merge

## 4. 의존

- 상위: ADR-006 promotion gate, ADR-004 ExecutionReport schema 공유
- 하위: 없음 (MCT-18 Epic 의 마지막 child)

## 5. Acceptance (placeholder)

- TBD: calibration metric 의 통계적 정의 (percentile / mean / variance)
- TBD: Backtest replay vs Paper 비교 의 window matching (동일 period 가정 가능?)
- TBD: ExecutionReport 의 `summary.calibration_metrics` extension
- TBD: CLI duration parsing (e.g. `7d` / `1h` / `2026-05-10T00:00:00Z` end timestamp)
- TBD: SIGTERM handler + final ExecutionReport flush sequence
- TBD: integration test 구조 (mock Bithumb WebSocket vs recorded fixture)
- TBD: Streamlit dashboard mode filter UI

## 6. Phase 1 brainstorm

MCT-19/20/21/22 freeze 후 Codex 일괄 dispatch → Sonnet 합성 → docs/stories/MCT-23.md 본 brainstorm → Phase 1 PR.

## 7. Epic 종료 trigger

본 Story Phase 2 merge + B1~B7 + C1~C5 통과 시 **MCT-18 Epic close PR** (EPIC-RESULTS-MCT-18.md + Codex aggregate + 후속 candidate brainstorm: Live mode / WFO / Multi-symbol).

## 8. CFP-60 debut-audit

Phase 2 merge 후 audit signal check + Epic level audit (Paper Epic 전반).
