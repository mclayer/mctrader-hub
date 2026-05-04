---
story_key: MCT-50
status: phase:요구사항
component: web
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-002, ADR-007, ADR-011
---

# MCT-50: FastAPI Local Runner Service — 1 active session lifecycle owner

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

"web 으로 관리할 수 있어야 한다" 의 backbone. Streamlit 도, CLI 도 모두 이 service 의 client.

## 2. 도메인 해석

MCT-48 child #2. Codex F3+G3 채택의 product 측 구현. FastAPI 가 PaperExecutor lifecycle 의 single owner — 1 active paper session enforce, start/stop/status/health endpoint 제공. localhost (`127.0.0.1`) bind + token auth.

핵심 invariant:
- Streamlit 은 절대 subprocess 를 spawn 하지 않음. 모든 lifecycle action 은 FastAPI 호출.
- CLI `mctrader-cli paper start` 는 v1 default = standalone 실행 (MCT-49 의 자기 process 안에서). FastAPI 는 web 만 호출. CLI 가 FastAPI service 에 attach 하는 client mode = 후속 candidate (Epic 외).

CLI ↔ FastAPI separation 이유: ADR-011 branch protection F5 mitigation 의 CI smoke 가 CLI smoke 만으로 deterministic. FastAPI 도 별도 smoke (httpx test client) 추가, 둘은 동일 PaperRunner library (MCT-49) 호출 — 따라서 G3 parity 자동 보장.

**Single active session enforcement (host-wide)**: CLI standalone 과 FastAPI service 가 동시에 다른 paper run 을 spawn 하지 못하도록 host-wide lock file `~/.mctrader/paper.lock` (JSON: `{run_id, pid, started_ts}`) 사용. 양쪽 entry point (CLI MCT-49 + FastAPI MCT-50) 가 startup 시 lock 확인 — 존재 + pid alive → refuse. 정상 종료 시 lock 삭제. stale lock (pid dead) → 자동 cleanup.

## 3. 관련 ADR

- ADR-002 D2 (run_id namespace), D9 (Live only — 본 Story 미적용)
- ADR-007 D7 manual ack (operator action endpoint = MCT-52)
- ADR-011 D1 F5 (mctrader-web 기존 branch protection 적용 후)

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/
├── api/
│   ├── __init__.py (existing — empty placeholder)
│   ├── server.py (NEW — FastAPI app)
│   ├── auth.py (NEW — token loader / Depends)
│   ├── lifecycle.py (NEW — PaperRunner ownership + state machine)
│   ├── routes/
│   │   ├── runs.py (NEW — POST /runs / DELETE /runs/{id} / GET /runs/{id})
│   │   ├── status.py (NEW — GET /status / GET /health)
│   │   └── events.py (NEW — GET /runs/{id}/events?since=N — MCT-51 dependent stub)
│   └── schemas/
│       └── run_request.py (NEW — RunRequest / RunStatus pydantic v2)
└── pyproject.toml (MODIFY — fastapi script entry add: mctrader-web-api)
```

신규 entry: `mctrader-web-api = "mctrader_web.api.server:run"` (uvicorn 127.0.0.1:7821 default — port 7821 = "mctrader" 의 임의 token).

## 5-6. 요구사항

1. `mctrader-web-api` 명령 = uvicorn 127.0.0.1:7821 bind. 외부 IP bind 시 startup error.
2. `~/.mctrader/local_token` 자동 생성 (file mode 700, `secrets.token_urlsafe(32)`). 매 startup 시 존재하지 않으면 생성, 있으면 reuse.
3. Endpoint:
   - `POST /runs` (body: RunRequest = strategy/symbol/tf/fast/slow/capital/duration). 1 active session 이미 존재 시 409 Conflict.
   - `DELETE /runs/{run_id}` = graceful stop (cancellation token + 최대 30초 wait, 미응답 시 SIGTERM).
   - `GET /runs/{run_id}` = RunStatus (lifecycle / current_equity / open_orders / risk_state).
   - `GET /status` = service-level (active_run_id or null / version / uptime).
   - `GET /health` = liveness (no auth).
   - `GET /runs/{run_id}/events?since={seq}` = stub returning empty list (MCT-51 implementation 시 wire).
4. Auth: 모든 endpoint (except `/health`) 가 `Authorization: Bearer <token>` 의무. token mismatch = 401.
5. Concurrency: 1 active session enforce. POST 시 active 있으면 reject. DELETE 후 active 해제 까지 wait.
6. Graceful shutdown: uvicorn SIGTERM → in-flight DELETE wait → service exit.
7. Test: httpx test client unit + integration test (start → status → stop → status).

## 7. 보안 설계

- §7.1 Trust boundary: 127.0.0.1 hard enforce (external bind = startup refuse).
- §7.2 Threat model: token leak (file mode 700) / missing token reject (401) / session smuggling (1 active enforce).
- §7.3 Auth: Bearer token only. operator = "local-user" hardcoded (multi-user out-of-scope).
- §7.4 OpRisk: PaperRunner crash → service restart 후 status reconciliation (MCT-51 event store 으로 가능, v1 = "no active run" 으로 reset acceptable).

## 11. 데이터 영향

- 신규 file: `api/server.py` / `auth.py` / `lifecycle.py` / `routes/*.py` / `schemas/run_request.py` / `tests/test_api_*.py`.
- 수정 file: `pyproject.toml` (script entry + fastapi/uvicorn 의존 활성).
- version bump web 0.1.0 → 0.2.0.
- DB schema: 없음 (lifecycle in-memory v1, MCT-51 event store 도입 시 reconcile).
- Reversible: yes.
