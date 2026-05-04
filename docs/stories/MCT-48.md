---
story_key: MCT-48
status: phase:요구사항
component: epic
type: epic
parent_epic: null
related_adrs: ADR-002, ADR-005, ADR-006, ADR-007, ADR-009
---

# MCT-48 (Epic): Paper Runtime Operations + Web Management

## 1. 사용자 요구사항 (verbatim, 2026-05-04)

> "paper를 굴려보면 좋겠는데" → "cli로도 잘 되는게 좋지만 무엇보다 web으로 관리할 수 있어야 한다."

선행 discrepancy 발견 (Sonnet, 2026-05-04): MCT-23 commit `4915029` 가 calibration / shutdown / risk extension library 만 추가, **`mctrader-engine/src/mctrader_engine/cli.py` 의 `paper` command 는 MCT-21 시점 skeleton 그대로** (config print + "[paper] runtime hardening lands in MCT-23." 메시지만 출력 후 종료). MCT-18 Epic 종료가 operationally incomplete 상태로 close.

mctrader-web `0.1.0` 은 read-only run viewer 에 그침 (`./out` directory scan + 1개 run 선택 + equity curve + 5 metric + events). FastAPI 의존 선언만 있고 `src/mctrader_web/api/` 비어있음.

## 2. 도메인 해석

mctrader 6번째 implementation Epic = **Paper mode 실제 운영 가능 상태로 완성** + **web 1차 user interface 격상**. 4 prior implementation Epic (MCT-12 / MCT-18 / MCT-25 / MCT-32 / MCT-37) 의 retroactive 후속 — 구체적으로 MCT-18 + MCT-23 의 CLI runtime gap 봉합 + MCT-17 web read-only viewer 의 control plane 격상.

핵심 framing (Codex 7-area review 채택, 2026-05-04):

- **Web 은 1차 user interface 이지만 runtime 소유자 아님.** FastAPI local service 가 PaperExecutor lifecycle 소유, Streamlit + CLI 모두 client. 이 dependency order 는 ADR-002 D9 (3-condition AND, runtime isolation) 의 Paper 측 적용.
- **Artifact thinking → event sourcing 전환.** ADR-002 D6 = "SQLite append-only event log = Paper operational truth". MCT-18 이 `equity_curve.csv` + `execution_report.json` artifact 를 truth 로 잘못 정착 — MCT-48 에서 정정. file 은 finalization export only.
- **Product 목적 = ADR-006 Promotion Evidence.** Paper 의 존재 이유 = "B→P→L 승격 evidence 생성". 30일 또는 100 trade + violation 0 + slippage/fill/latency drift 측정 + calibration drift < 5%. dashboard usability 는 evidence 표시 수단, evidence 자체가 아님.

본 Epic 은 MCT-41 (Live Mode) 와 **별도 lane** 으로 진행 가능:
- MCT-41 Phase 1 doc-only 이미 merge, Phase 2 는 사용자 manual prereq 5건 (1Password / Bithumb live API / KRW 입금 / age backup / gitleaks) 으로 blocked.
- MCT-48 은 manual prereq 0건 (Paper = simulated KRW, 실 자금 노출 없음). 즉시 진행 가능, MCT-41 Phase 2 진입 시 narrow schema hooks (RunLifecycleEvent / RiskDecisionEvent / OperatorActionEvent / ExecutionReport schema) 재사용.

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Codex 7-area review (codex-rescue, gpt-5.5 high, 2026-05-04)

12 open design point (A~L) framework critique + per-decision option scoring + push-back. 핵심 push-back 3건 Sonnet 채택:

1. **"web primary" 재정의** — runtime 이 1차, web 은 client. F3+G3 채택.
2. **artifact thinking → event sourcing** — SQLite append-only 가 ADR-002 D6 align truth.
3. **ADR-006 promotion evidence = 진짜 product 목적** — 30일 evidence bundle 이 success criterion.

### Sonnet decider Phase 1 (12 sub-decision batch, 2026-05-04)

| # | Decision | Pick | 근거 |
|---|----------|------|------|
| A | Web start/stop architecture | A2 — FastAPI lifecycle | A1 subprocess 는 ADR-002 run isolation + ADR-007 manual ack 무결성 X |
| B | Realtime update mechanism | B3 — NDJSON event log + SQLite mirror | B1 file polling 은 fill/risk/latency event miss |
| C | Process lifecycle | C1 — Single active session | C2 multi 는 ADR-009 multi-process DuckDB write 위험 (MCT-18 명시 거부) |
| D | State persistence | D2 — SQLite (operational) + Parquet (historical) | D1 file-only = MCT-18 약점 그대로, ADR-002 D6 conflict |
| E | Auth | localhost token | bind 127.0.0.1 + 자동 생성 token + operator 로그 = ADR-007 operator action 책임 |
| F | Frontend stack | F3 — Streamlit (monitor+control) + FastAPI (control plane) | F2 React premature, F1 Streamlit 단독 owns runtime 위험 |
| G | CLI ↔ Web parity | G3 — FastAPI = runner, CLI+Web = clients | G2 (양쪽 library 직접) = MCT-23 재발 패턴 |
| H | Mode coverage | H1 — Paper only | H3 Live 는 ADR-008 secret + MCT-41 manual prereq blocked |
| I | MCT-41 prep hooks | narrow only — schema/event/storage compatibility | 1Password / 실 broker / Live kill UI 는 MCT-41 |
| J | Scope decomposition | J1 — Single Epic + 6 child | MCT-12/18/25/32/37 패턴 (5 Epic × 6-child 평균, 42/42 ADR conflict 0) 검증됨 |
| K | Graceful shutdown IPC | FastAPI cancellation token + OS signal fallback. RiskGate ack 별도 event | ADR-007 D7 recovery ≠ shutdown |
| L | Realtime data schema | Pydantic v2 NDJSON event + SQLite mirror. closed-bar only, partial bar = diagnostic feed state label | ADR-005 lookahead UI trap 회피 |

12/12 escalation 0건. 사용자 사전 approval = "A" (Sonnet 전체 채택, evidence 1순위, OPS-1~6 순서).

## 4. Child Story decomposition

| Story | repo | scope | 의존 |
|---|---|---|---|
| **MCT-49** Paper CLI Runtime Gap Sealing | mctrader-engine | `mctrader-cli paper` 가 PaperExecutor 실제 instantiate + WebSocket adapter + RiskGate + Calibration + shutdown wiring. MCT-23 C1-C5 실제 실행. MCT-18+23 retroactive sealing. | — |
| **MCT-50** FastAPI Local Runner Service | mctrader-web | 1 active paper session lifecycle owner (start/stop/status/health). 127.0.0.1 + token. CLI 도 이 service attach. | MCT-49 |
| **MCT-51** SQLite Event Store + NDJSON Export | mctrader-engine + mctrader-data | append-only event schema (Pydantic v2 모델 11종). SQLite operational truth. NDJSON export. status reconstructable after restart. | MCT-49 |
| **MCT-52** RiskGate Operator Action Exposure | mctrader-engine | hard-stop / manual ack / cooldown / risk_policy_hash unchanged enforcement. ADR-007 D7 web button + CLI parity. operator-action event emit. | MCT-50 + MCT-51 |
| **MCT-53** Streamlit Paper Control Panel + Monitoring | mctrader-web | start/stop/status/equity/fills/risk/calibration. FastAPI client only (subprocess 미소유). partial bar = "diagnostic feed state" label only. | MCT-50 + MCT-51 + MCT-52 |
| **MCT-54** Promotion Evidence Bundle (ADR-006) | mctrader-engine + mctrader-hub | 30일 / 100 trade / violation 0 / drift threshold report. "not promotable" explicit signal + reason list. Epic close trigger. | MCT-51 + MCT-52 |

### Ordering 의무

- **MCT-49 = serialized first** (CLI runtime gap sealing — 모든 후속 Story 의 ground)
- **MCT-50 + MCT-51 = parallel after MCT-49** (control plane + event store 양쪽 동시 가능)
- **MCT-52 = after MCT-50 + MCT-51** (operator action 은 control plane + event store 모두 의존)
- **MCT-53 = after MCT-52** (UI 는 모든 backend stable 후)
- **MCT-54 = after MCT-51 + MCT-52** (evidence bundle 은 event store + risk policy 의존, MCT-53 미의존 — UI 분리 가능)

## 5-6. 요구사항

### Blocking AC (B1~B10)

| # | AC | 충족 시점 |
|---|-----|----------|
| B1 | `mctrader-cli paper` 가 실제 PaperExecutor instantiate → WebSocket subscribe → 시뮬 fill → equity_curve update → SIGTERM final flush 까지 E2E 작동 | MCT-49 |
| B2 | FastAPI local service `127.0.0.1` bind + auto-generated token + start/stop/status/health endpoint + 1 active session enforce | MCT-50 |
| B3 | SQLite append-only event store (Pydantic v2 11 event 모델) 의 status reconstructable after process restart | MCT-51 |
| B4 | NDJSON export from SQLite event store (run finalization 시 export, mid-run streaming export optional) | MCT-51 |
| B5 | RiskGate hard-stop → web "Acknowledge" button + CLI `mctrader-cli risk ack` 양방향 parity. risk_policy_hash unchanged enforcement | MCT-52 |
| B6 | Streamlit page = FastAPI REST client only (subprocess spawn / library import 으로 runtime own 금지). partial bar "diagnostic feed state" label visible | MCT-53 |
| B7 | Streamlit = start (params: strategy/symbol/tf/fast/slow/capital/duration) + stop + status (lifecycle/equity/fills/risk/calibration) UI | MCT-53 |
| B8 | Promotion evidence bundle = 30일 또는 100 trade + violation 0 + slippage/fill/latency drift + calibration drift < 5% 검증 + "promotable: bool" + "blocking_reasons: list[str]" | MCT-54 |
| B9 | 3 repo (mctrader-engine 0.12→0.16 / mctrader-data 0.3→0.4 / mctrader-web 0.1→0.4) version bump + CI green + cross-repo import smoke pass | MCT-49 ~ MCT-54 점진 |
| B10 | MCT-18 + MCT-23 retroactive scope acknowledgment — `EPIC-RESULTS-MCT-48.md` 에 "MCT-18+23 operationally incomplete (CLI runtime gap), MCT-48 resolved" 명시 | MCT-54 (Epic close) |

### Calibration AC (C1~C5)

| # | metric | 의미 | 채택 |
|---|--------|------|------|
| C1 | `event_store_event_count >= 1` per active run | event sourcing 작동 verify | MCT-51 |
| C2 | `lifecycle_event_count == 1` (start) AND finalization 시 `+1` (stop) | lifecycle event 정합성 | MCT-51 |
| C3 | `web_round_trip_p95_ms < 500` | web ↔ FastAPI control plane 응답 | MCT-50 |
| C4 | `evidence_bundle_promotable_decision in {true, false}` (null 금지) | evidence bundle 결론 명확성 | MCT-54 |
| C5 | `cli_paper_e2e_smoke_duration_seconds < 60` (60초 smoke) | CLI E2E 회귀 방지 | MCT-49 |

### Demonstration AC (D1)

D1 = Streamlit Paper control + monitoring page = **MCT-53 의 deliverable**. MCT-31 (Live event dashboard) 와 별도, MCT-48 = Paper UI 만.

## 7. 보안 설계

- **§7.1 Trust boundary**: FastAPI bind = `127.0.0.1` only (외부 노출 절대 금지). token = 자동 생성 (`secrets.token_urlsafe(32)`) + `~/.mctrader/local_token` (700) + Streamlit / CLI 가 이 파일 읽어 Authorization header 첨부. localhost cross-origin = same-origin policy.
- **§7.2 Threat model**: Paper = 실 자금 노출 0 → 위협 surface 작음. 그러나 (a) operator action 추적 부재 (web button push 누가 했는지 모름) → ADR-007 D7 recovery 무효화 / (b) malicious local process 가 token 탈취 후 paper run 조작 → file mode 700 / (c) 내부 네트워크 노출 (외부 bind) → 127.0.0.1 hard enforce.
- **§7.3 Auth/authz**: localhost token (single user "local-user"). 모든 control plane mutation (start/stop/risk-ack) 은 operator action event 로 기록. read-only (status/event tail) 도 token 의무.
- **§7.4 OpRisk**: WebSocket disconnect → degraded mode 명시 거부 (ADR-018 candidate, MCT-48 out-of-scope) → 즉시 graceful stop + final flush + risk_event(WS_DISCONNECT 미정의 → MCT-48 add as TriggerName candidate). DuckDB single-writer 정책 (MCT-18 검증) 유지 — paper event store 는 SQLite separate.
- **§7.5 민감 데이터**: 없음 (Paper = simulated). 단, Live mode 진입 시 동일 control plane 재사용 시 1Password vault path / API key 누설 위험 → MCT-41 별도 검토.

## 8. 테스트 / 11. 데이터 영향

### 신규 file

- `docs/adr/ADR-005-lookahead-verification.md` amendment §D5 (UI partial bar diagnostic label 의무)
- `docs/adr/ADR-006-walk-forward.md` amendment §D7 (Paper Promotion Evidence Bundle 정의)
- `docs/stories/MCT-48.md` (Epic, 본 file)
- `docs/stories/MCT-49.md` ~ `MCT-54.md` (6 child Story stub)

### 수정 file (Phase 2+)

- `mctrader-engine/src/mctrader_engine/cli.py` (paper command runtime wiring) — MCT-49
- `mctrader-engine/src/mctrader_engine/event_store/` (NEW module) — MCT-51
- `mctrader-engine/src/mctrader_engine/calibration/` (evidence bundle generator extension) — MCT-54
- `mctrader-web/src/mctrader_web/api/` (FastAPI runner service) — MCT-50
- `mctrader-web/src/mctrader_web/dashboard/app.py` (Paper control + monitoring) — MCT-53

### DB schema / migration

- 신규 SQLite schema: `paper_event_store.sqlite` (per run, 11 event table). schema_version `paper_event_store.v1`. ADR-002 D6 align.
- ADR-009 partition mode=paper/ 와 별도 namespace. event store = operational truth, parquet = historical artifact (calibration / lineage).

### Reversible

- Phase 1 doc 단계 = yes.
- Phase 2-5 implementation = yes (Paper = simulated, file delete + git revert 으로 0 cost rollback).

## 12. Sonnet Decision Log

| packet_id | trigger | options_count | decider_pick | override? | audit_result | timestamp |
|-----------|---------|---------------|--------------|-----------|--------------|-----------|
| MCT-48-Phase1-12dec | substantive-multi-decision-batch | 12 sub × 2~4 options | A2/B3/C1/D2/Etoken/F3/G3/H1/Inarrow/J1/Kfastapi-cancel/L-pydantic-ndjson | no | direct | 2026-05-04Z (Codex review + Sonnet 합성 + 사용자 approve "A") |

12/12 escalation 0건. Phase 1 large scope (Epic + 6 child + 2 ADR amendment). Codex 7-area review (codex-rescue gpt-5.5 high) + Sonnet (claude-opus-4-7) 합의.

## 13. Out-of-scope (확정 거부)

- Live mode (MCT-41 별도 Epic, manual prereq blocked)
- Multi-session concurrent paper run (C1 single-session)
- React / Vue / 별도 SPA frontend (F1+F3 Streamlit 유지)
- OAuth / multi-user (E localhost token only)
- Redis / RQ / APScheduler (D2 SQLite 충분)
- WebSocket push from FastAPI to web (NDJSON polling v1, push 후속)
- Multi-symbol / multi-strategy / WFO automation (별도 후속 Epic)
- PyPI publish (Live debut 후)
- Streamlit live concurrent DuckDB read (MCT-18 거부 유지)
- WS_DISCONNECT 자동 reconnect (graceful stop only)
- Live event dashboard (MCT-31 별도 Epic)
