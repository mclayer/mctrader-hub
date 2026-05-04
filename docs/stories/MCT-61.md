---
story_key: MCT-61
status: phase:요구사항
component: web
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-002, ADR-006
---

# MCT-61: WFO Web Integration — FastAPI endpoints + Streamlit panel + 1 active session lock 확장

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

> "web에도 이 WFO를 활용가능하도록 하자."

MCT-48 의 FastAPI runner + Streamlit client 패턴 재사용. Sonnet decider M3 (monitor + control 모두) + N1 (기존 mctrader-web FastAPI 확장) + O2 (Streamlit 별도 page sidebar nav) + P1 (host-wide 1 active session mutex, paper|wfo) + Q1 (polling status).

## 2. 도메인 해석

MCT-55 child #6. MCT-58 fold report 가능 시점 진입 (MCT-59 / MCT-60 의무 아님 — fold_report.json 만 있으면 view 가능).

본 Story 종료 시 사용자가:

1. `python -m mctrader_web.api.runner` 실행 (MCT-48 의 FastAPI service, WFO endpoint 추가됨)
2. `streamlit run src/mctrader_web/dashboard/app.py` 실행 → sidebar 에 "Paper" / "WFO" 별 page
3. WFO page 에서 decision_group create button → search start button → progress polling → fold report view → promote ack button
4. Paper 와 WFO 동시 진입 시 host-wide `~/.mctrader/runtime.lock` mutex 거부

## 3. 관련 ADR

- ADR-002 D6 (event sourcing / audit log) / ADR-006 D6 / D7 / amendment §D7 (Bundle)

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/
├── api/
│   ├── runner.py             (MODIFY — WFO endpoint 5종 추가)
│   ├── wfo.py                (NEW — FastAPI router)
│   └── lifecycle.py          (MODIFY — runtime_lock mode field 적용)
├── dashboard/
│   ├── app.py                (MODIFY — sidebar nav)
│   ├── pages/
│   │   ├── paper.py          (MODIFY — sidebar nav 통합 only)
│   │   └── wfo.py            (NEW — Streamlit WFO page)
│   └── api_client.py         (MODIFY — WFO endpoint client method 추가)
└── tests/
    └── test_wfo_api.py       (httpx ASGI test)

mctrader-engine/src/mctrader_engine/runtime/
├── paper_lock.py             (MODIFY → rename runtime_lock.py with mode field)
└── runtime_lock.py           (NEW or rename — mode: "paper"|"wfo")
```

## 5-6. 요구사항

1. FastAPI WFO endpoints (5종):
   - `POST /wfo/decision-groups` body `{strategy_family, symbol, timeframe, train_days, val_days, oos_days, embargo_days}` → registry_hash 응답
   - `POST /wfo/runs` body `{decision_group_hash, budget}` → run_id 응답 (search start, runtime_lock mode=wfo 획득)
   - `GET /wfo/runs/{run_id}/status` → `{state: pending|running|done|failed, progress_pct, current_trial, total_trials, audit_event_tail}` (polling Q1)
   - `GET /wfo/runs/{run_id}/fold-report` → `fold_report.json` content (MCT-58 결과)
   - `POST /wfo/promote` body `{decision_group_hash, ack_text}` → `promotion_decision.json` 작성 (CLI parity, 본 endpoint 가 MCT-62 wiring 의 web 측)
2. 127.0.0.1 bind + token auth = MCT-48 의 `~/.mctrader/local_token` 재사용 (Bearer header 의무).
3. `runtime_lock.py` 확장: `~/.mctrader/runtime.lock` JSON `{run_id, pid, started_ts, mode: "paper"|"wfo"}`. paper + wfo 동시 진입 시 mode 다르면 거부 (mutex). 기존 `paper.lock` 은 backward-compat alias 또는 migration (단순 rename).
4. Streamlit `pages/wfo.py` (별도 page, sidebar nav O2):
   - Section 1 — Decision Group: list (`~/.mctrader/wfo/decision_groups/`) + create form
   - Section 2 — Search Run: start form (decision_group select + budget) + progress polling (1s interval, MCT-48 패턴)
   - Section 3 — Fold Report: gate D6 12-metric pass/fail + fold-level median/IQR/worst/CI + Plotly chart (equity curve per fold, optional)
   - Section 4 — Promote ack: ack text input + submit button → `POST /wfo/promote` (MCT-62 의무 prerequisite)
5. `dashboard/app.py` sidebar nav: Paper / WFO 두 page (existing read-only run viewer 도 같은 nav 에 통합 — Run List page).
6. `api_client.py` WFO client method 6종 추가 (5 endpoint + status polling helper).
7. httpx ASGI test — WFO endpoint 5종 + auth + lock mutex (paper lock held → wfo POST runs 거부).
8. Streamlit AppTest smoke — WFO page render + form submit (mock api_client).
9. CI green: mctrader-web + mctrader-engine cross-repo, runtime_lock migration 검증.

## 7. 보안 설계 / 11. 데이터 영향

- §7.1 Trust boundary: 127.0.0.1 hard enforce (MCT-48 동일).
- §7.2 Threat model: WFO = 적재 OHLCV only, no live API. operator action 추적 = audit log JSONL append-only (decision_group 별).
- §7.3 Auth: localhost token. `POST /wfo/promote` 는 ack event 로 audit log 기록 (`promotion_decision_created`).
- §7.4 OpRisk: WFO + Paper 동시 거부 (runtime_lock mutex). search 중 process kill → audit log finalize, decision_group 재진입 가능.
- §7.5 민감 데이터: 없음 (WFO = simulated).

### 신규 file

- `mctrader-web/src/mctrader_web/api/wfo.py` (FastAPI router)
- `mctrader-web/src/mctrader_web/dashboard/pages/wfo.py` (Streamlit page)
- `mctrader-engine/src/mctrader_engine/runtime/runtime_lock.py` (rename or new)
- 양 repo tests.

### 수정 file

- `mctrader-web/src/mctrader_web/api/runner.py` (WFO router include) / `lifecycle.py` (mode field) / `dashboard/app.py` (sidebar nav) / `dashboard/pages/paper.py` (sidebar nav 통합 only) / `dashboard/api_client.py` (WFO method)
- `mctrader-engine/src/mctrader_engine/runtime/paper_lock.py` (rename or migration)

### Version bump

- mctrader-web 0.4.0 → 0.5.0
- mctrader-engine 0.20.0 → 0.21.0 (이미 MCT-60 에서 bump 됐으면 동일 minor)

### Reversible

- yes (file revert + lock file rename rollback). runtime_lock 은 backward-compat alias 로 안전.
