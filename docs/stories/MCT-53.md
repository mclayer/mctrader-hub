---
story_key: MCT-53
status: phase:요구사항
component: web
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-005, ADR-007
---

# MCT-53: Streamlit Paper Control Panel + Monitoring — FastAPI client only

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

"무엇보다 web 으로 관리할 수 있어야 한다" 의 user-facing deliverable. Streamlit page = start/stop/status/equity/fills/risk/calibration. **FastAPI 호출 전용** — subprocess spawn / library import 금지.

## 2. 도메인 해석

MCT-48 child #5. UI 가 모든 backend (MCT-50 control plane + MCT-51 event store + MCT-52 ack flow) stable 후. Streamlit single page (sidebar control + main monitoring).

핵심 invariant (ADR-005 lookahead UI trap 회피):
- 모든 candle display = "**closed bar only**" — partial bar (현재 진행 중인 bar) 는 별도 "diagnostic feed state" panel 에 label 분리 표시. strategy decision 과 동일 visual context 에 절대 mix 금지.
- equity_curve = closed bar 기준 EquitySnapshotEvent 만 plot.

기존 mctrader-web 0.1.0 의 read-only viewer page 는 **별도 page** (`backtest_dashboard`) 로 유지. 신규 MCT-53 page = `paper_panel`. Streamlit `pages/` 디렉토리 구조.

## 3. 관련 ADR

- **ADR-005 D2 amendment §D5** — UI partial bar diagnostic label 의무 (MCT-48 amendment, 본 Story 검증)
- ADR-007 D7 manual ack — web button → MCT-52 endpoint 호출

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/
├── dashboard/
│   ├── app.py (MODIFY — Streamlit multi-page entry, sidebar 분기)
│   └── pages/
│       ├── backtest_dashboard.py (MOVE — 기존 0.1.0 viewer)
│       └── paper_panel.py (NEW — control + monitoring)
├── api_client/ (NEW)
│   ├── __init__.py
│   ├── client.py (httpx + Bearer token loader)
│   └── poller.py (NDJSON tail poller for events)
└── pyproject.toml (MODIFY — dashboard entry 그대로, dev deps + httpx[client])
```

## 5-6. 요구사항

1. Streamlit multi-page: sidebar = "Backtest dashboard" / "Paper panel" 선택.
2. `paper_panel` page sections:
   - **Control**: "Start" form (strategy/symbol/tf/fast/slow/capital/duration) + "Stop" button + "Acknowledge risk" button (active hard-stop 시 only).
   - **Status**: lifecycle (running/stopped/error) + active run_id + uptime.
   - **Monitoring**: equity curve (Plotly, closed bar only) + fills table (FillEvent stream) + risk events table (RiskDecisionEvent + OperatorActionEvent) + calibration progress (6 metric live).
   - **Diagnostic feed state**: partial bar 진행 상태 + last WS message timestamp + staleness ms. **절대 strategy panel 과 mix 금지** — 별도 expander.
3. Polling: `GET /runs/{id}/events?since={seq}` 매 3초 (manual refresh button + auto checkbox). NDJSON tail.
4. Auth: `~/.mctrader/local_token` 자동 read. mismatch 시 sidebar error.
5. Single active session: web start 호출 시 active 있으면 명시 reject 표시.
6. Out-of-scope: WebSocket push (NDJSON polling v1). multi-session UI. Live affordance (button/icon 일체 X).
7. Test: Streamlit AppTest smoke (sidebar 진입 + page switch + httpx mock client).

## 7. 보안 설계 / 11. 데이터 영향

- 보안: localhost token only. cross-origin = same-origin. Live affordance forbidden (operator confusion 회피).
- 신규 file: `dashboard/pages/paper_panel.py` + `api_client/*.py` + tests.
- 수정 file: `dashboard/app.py` (multi-page entry), `pages/backtest_dashboard.py` (move).
- version bump web 0.3.0 → 0.4.0.
- DB schema: 없음 (read-only client).
- Reversible: yes.
