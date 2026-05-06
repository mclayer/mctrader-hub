# Collector HA Phase 6 — Streamlit `00_status` Panel

**Date**: 2026-05-06
**Story**: MCT-95 (#106) — X6 child of MCT-89
**Sister Stories MERGED**: MCT-91 (X2) + MCT-92 (X3) + MCT-93 (X4) + MCT-94 (X5)

## 0. Codex Phase 6 design review (6/6 ADOPT 합)

| F | Codex | Sonnet | Action |
|---|---|---|---|
| F-1 approach choice | SUGGEST | 채택 | A: subprocess + 5s cached adapter |
| F-2 auto-refresh | SUGGEST | 채택 | Streamlit native rerun (no time.sleep / autorefresh dep) |
| F-3 layout | ADOPT-AS-IS | 채택 | per-node card + worst_level banner |
| F-4 AppTest scope | SUGGEST | 채택 | 6 scenarios (green/yellow/red/no_heartbeat/malformed/two_nodes) |
| F-5 deps | SUGGEST | 채택 | mctrader-data declared (later promoted to core via impl review F-4) |
| F-6 out-of-scope | ADOPT-AS-IS | 채택 | — |

## 1. Step plan

1. status_adapter.py — cached subprocess wrapper
2. pages/00_status.py — Streamlit page
3. tests/test_status_adapter.py — 10 unit tests
4. tests/test_apptest_status_panel.py — 6 AppTest smoke scenarios
5. pyproject.toml — mctrader-data dep + version bump 0.13.0
6. PR open + Codex implementation review + admin merge
7. Hub Story §8-9 close + memory update

## 2. Acceptance Criteria

- [x] All 6 design scenarios covered by AppTest
- [x] ruff clean
- [x] 155+16=171 pytest PASS, regression 0
- [x] Codex implementation review ADOPT 합 (F-4 PUSH-BACK fix 적용)
- [x] backward compat 100% (기존 page 영향 0)

## 3. Out-of-scope (X7/v2)

- Calibration C1/C2 + 양 node 30분 E2E demo (X7)
- Slack/email proactive alerting (v2)
- Real-time WebSocket push (out-of-scope)
- Per-symbol drilldown (out-of-scope)
- streamlit-autorefresh extension 평가 (후속)
