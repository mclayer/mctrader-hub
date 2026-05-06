# Change Plan — MCT-97 Admin Engine Control Panel

- **Story**: MCT-97
- **Status**: design (ArchitectPLAgent + 6 deputies + ArchitectAgent chief — 2026-05-06)
- **Story file**: [`docs/stories/MCT-97.md`](../stories/MCT-97.md)
- **ADR**: [ADR-014](../adr/ADR-014-control-plane-separation.md) · [ADR-015](../adr/ADR-015-engine-state-machine.md) · [ADR-016](../adr/ADR-016-audit-log-immutability.md)
- **Domain contract**: [engine-id-naming.v1.md](../domain-knowledge/contracts/engine-id-naming.v1.md)

## 1. 입력 요약 (Story §1 verbatim, immutable)

> web의 요구조건이다. mctrader를 위해 작업하는 engine들을 점검하고 제어할 수 있는 panel을 만들어라. 현재는 localhost에 존재하지만 원격으로 작업될 수도 있기 때문에 이를 고려하라. codeforge를 통해 반드시 작업하라.

## 2. 현재 구조 (CodebaseMapperAgent 산출)

### 2.1 mctrader-web (확장 대상)

| 자산 | 경로 | 본 Story 와 관계 |
|------|------|-------------------|
| FastAPI app | `src/mctrader_web/api/app.py` | `include_router(get_router(...))` 단일 — `/admin` mount 지점 추가 필요 |
| `auth.py` | `src/mctrader_web/api/auth.py` | **단일 static token** (MCT-50, `~/.mctrader/local_token`) — §7.B 호환 layer 출발점 |
| `config.py` | `src/mctrader_web/api/config.py` | `default_token_path` + 환경변수 override pattern 재사용 |
| `lifecycle.py` | `src/mctrader_web/api/lifecycle.py` | `LifecycleManager` 보유 — `paper_lock` host-wide + GRACEFUL_STOP_TIMEOUT_SECONDS=30s + asyncio Task — admin paper control 의 backbone |
| `backtest_lifecycle.py` | 同上 | `BacktestExecutor` `asyncio.to_thread` wrap — cancel hook 부재 (engine 측 작업 필요) |
| `wfo_lifecycle.py` | 同上 | WFO 동일 패턴 |
| `routes.py` | 同上 | router prefix 없이 root mount — `/admin/control` + `/admin/status` 두 sub-router 추가 |
| `dashboard/pages/` | `src/mctrader_web/dashboard/pages/` | `00_status.py` 등 numeric prefix — `10-13_admin_*.py` 추가 |
| `data/` | **미존재** | ADR-016 신규 생성 (audit SQLite 위치) |

### 2.2 mctrader-engine (cooperative cancel hook 분석)

| 자산 | 경로 | Cancel hook 상태 |
|------|------|------------------|
| `paper_runner.PaperRunner` | `src/mctrader_engine/runtime/paper_runner.py` | **존재** — `cancel()` async + `_on_shutdown` 콜백 + `executor.cancel()` |
| `executor.paper.PaperExecutor` | 同上 디렉토리 | **존재** — `_cancel_event: asyncio.Event` + `cancel()` |
| `executor.backtest.BacktestExecutor` | 同上 | **부재** — synchronous `run()` per-bar loop (line 105-111). Cancel 도입 필요 |
| `wfo.search.coordinator` | `src/mctrader_engine/wfo/search/coordinator.py` | **부재** — fail-fast 분기는 있으나 외부 cancel 미수용 |

→ mctrader-engine PR 1건 (P3 진입 직전, ADR-015 후속).

### 2.3 mctrader-market / mctrader-market-bithumb (§AS-4 검증)

| Repo | layout | entry_points / `if __name__` |
|------|--------|-----------------------------|
| `mctrader-market/src/mctrader_market/` | `candle.py` `lifecycle.py` `order.py` `orderbook.py` `providers.py` `types.py` 등 | grep 결과 **0건** |
| `mctrader-market-bithumb/src/mctrader_market_bithumb/` | `adapter.py` `client.py` `ws_client.py` `rest_throttle.py` 등 | grep 결과 **0건** |

→ §AS-4 가정 확정: **library only** (별도 process 없음). market gateway 는 status read 전용 (paper_runner / collector 내부에서 import 되는 라이브러리). control 명령 대상 외. cross-repo PR 없음.

### 2.4 mctrader-hub (문서화 자산)

| 자산 | 경로 | 본 Story 와 관계 |
|------|------|-------------------|
| ADR | `docs/adr/` (ADR-001 ~ ADR-013) | ADR-014/015/016 신규 추가 |
| domain-knowledge contracts | `docs/domain-knowledge/contracts/heartbeat-schema.v1.md` | engine-id-naming.v1.md 신규 추가 (heartbeat node_id ↔ engine_id unify) |
| stories | `docs/stories/MCT-97.md` | §1 immutable, §3·§7·§11 본 단계 형식화 |

## 3. 도입할 설계 (RefactorAgent 산출 + ArchitectAgent 통합)

### 3.1 high-level architecture

```
                  +--------------------------------------------+
                  |          Streamlit admin pages              |
                  |  10_admin_overview / 11_admin_control /     |
                  |  12_admin_audit / 13_admin_rbac             |
                  +-----------+----------------+----------------+
                              |                |
                              | api_client     |
                              v                v
+-------------------+   +----------------------+----------------------+
|  TLS + token-bearer transport (Tailscale 권장 / SSH tunnel fallback) |
+-------------------+   +----------------------+----------------------+
                              |                |
                              v                v
            +-----------------+----------------+-------------------+
            |  FastAPI mctrader-web                                  |
            |  +-------------------------+  +---------------------+ |
            |  | /admin/control/* (POST) |  | /admin/status/* (G) | |
            |  |  ROLE: operator | admin |  |  ROLE: viewer+      | |
            |  |  Idempotency-Key 필수    |  |  audit 미적용        | |
            |  |  rate 30/min            |  |  rate 300/min       | |
            |  |  audit append (append-only hash chain ADR-016)   | |
            |  +-----------+-------------+  +----------+----------+ |
            |              |                           |            |
            +--------------|---------------------------|------------+
                           v                           v
                 control_adapter (§7.D hybrid)   status_adapter (재사용)
                  +-----+-----+-----+              + heartbeat sink
                  |     |     |     |              + last-known cache
                  v     v     v     v
              systemd  subprocess  in-process  in-process
              (Linux)  (Windows)   (backtest)  (WFO)
```

### 3.2 Module layout (mctrader-web 신규)

```
src/mctrader_web/api/admin/
├── __init__.py
├── control.py           # POST /admin/control/<engine_class>/<verb>
├── status.py            # GET  /admin/status/<engine_class | overview>
├── audit.py             # GET  /admin/status/audit + helper append_audit_row
├── rbac.py              # GET/POST /admin/control/rbac/* (admin role only)
├── control_adapter.py   # systemd / subprocess / in-process abstraction
├── state_machine.py     # daemon SM + one-shot SM (ADR-015)
├── tokens.py            # SQLite tokens table + HMAC sign/verify
├── audit_db.py          # SQLite WAL connection + chain helpers (ADR-016)
└── idempotency.py       # request_id cache (24h)

src/mctrader_web/dashboard/pages/
├── 10_admin_overview.py # 5 engine 한 화면
├── 11_admin_control.py  # control verb buttons (RBAC-gated)
├── 12_admin_audit.py    # audit query + filter
└── 13_admin_rbac.py     # token + role 관리 (admin only)

data/                    # 신규 (gitignore)
└── admin_audit.sqlite   # ADR-016 WAL DB
```

### 3.3 결합도 분석

- **control_adapter** 는 mctrader-web 단일 책임. mctrader-engine 의 `paper_runner`, mctrader-data 의 collector systemd unit 등을 외부 capability 로 wrap. engine repo 측은 cancel hook 1건 외 추가 결합 0.
- **status_adapter** 는 기존 dashboard 의 자산 재사용 (`dashboard/status_adapter.py`) — 신규 결합 없음.
- **audit_db** + **state_machine** 은 admin 모듈 내부 — 외부 import 없음.
- 기존 `auth.py` 호환: 단일 static token 을 `tokens` table 의 1개 row 로 마이그레이션 (id=`local-default`, role=admin) — legacy `Authorization: Bearer <local_token>` 사용자가 P5 까지 admin 권한으로 자동 정합 (Phase 4 마이그레이션 step).

## 4. 작업 분할 (§7.G 6 phase)

### Phase 1 — Skeleton (P1)

- mctrader-web `api/admin/__init__.py` + 7 module skeleton (no impl)
- `app.py` 에 admin sub-router 2개 mount (control / status, ROLE check stub)
- `dashboard/pages/10-13_admin_*.py` placeholder (Streamlit page heading + "WIP" notice)
- `data/` 디렉토리 + `.gitignore` 항목 추가
- mctrader-hub: ADR-014/015/016 + engine-id-naming.v1.md (본 단계 산출)
- Test: import-only smoke test (4 신규 page + 7 신규 module 모두 import OK)

### Phase 2 — Status read (P2)

- `status.py`: `/admin/status/overview` — 5 engine SM state + heartbeat age 통합
- `status.py`: `/admin/status/<engine_class>` — engine 별 detail
- `status_adapter` 기존 자산 호출 + heartbeat sink read (mctrader-data heartbeat schema v1)
- `dashboard/10_admin_overview.py` polling 5s 구현
- Test: heartbeat sink stub fixture + read endpoint contract test

### Phase 3 — Control write (P3)

- **선행 PR (mctrader-engine)**: `BacktestExecutor` + `WFO coordinator` cancel hook 도입 (`cancel_token: threading.Event`)
- `control_adapter.py` hybrid abstraction 구현 (systemd `systemctl --user` + subprocess 추적 + in-process invoke)
- `control.py`: 5 engine × verb (start/stop/restart for daemon, trigger/cancel for one-shot)
- `state_machine.py` SM transition validator (ADR-015)
- `idempotency.py` Idempotency-Key cache (ADR-016)
- `dashboard/11_admin_control.py` button + confirm dialog + in-flight indicator
- Test: SM transition unit test (모든 valid + invalid 조합) + control_adapter 모킹 + idempotent dedupe contract test

### Phase 4 — RBAC + audit (P4)

- `tokens.py` SQLite tokens table + 3 role + HMAC sign/verify + 기존 single-token 마이그레이션
- `audit_db.py` audit_log + idempotency_cache 두 table + hash chain append (ADR-016)
- `audit.py` query API + filter
- `rbac.py` admin-only token 관리
- `13_admin_rbac.py` + `12_admin_audit.py` UI
- CLI: `mctrader-web admin audit verify` + `mctrader-web admin audit backup`
- Test: RBAC 3 role × 6 path 조합 + hash chain 정합성 + tamper detection (강제 row 변조 후 verify FAIL 검증)

### Phase 5 — Remote security (P5)

- TLS 자체 서명 cert 자동 생성 (Windows + Linux), `--ssl-keyfile / --ssl-certfile` 옵션
- Rate limit middleware (control 30/min, status 300/min, per token)
- localhost binding 외 접속 시 TLS 강제 enforcement
- Tailscale + SSH tunnel docs (`docs/operations/admin-panel-remote-access.md` — mctrader-hub)
- Test: rate-limit 경계 테스트 (29/30/31 회) + TLS 강제 enforcement test

### Phase 6 — E2E + cross-platform (P6)

- Windows + Linux smoke test (control_adapter 분기 둘 다)
- 일일 backup cron docs (Windows Task Scheduler + Linux cron)
- retention 90일 default + override
- E2E: UC-1 ~ UC-8 8 시나리오 모두 자동화
- 회고 + Story §11 작성

## 5. 마이그레이션 / 호환성 (DataMigrationArchitect 산출)

### 5.1 Schema migration (audit DB)

- 첫 부팅: `audit_db.py` 가 DDL 실행 (CREATE TABLE IF NOT EXISTS). seed row 0건. 이후 control 명령부터 append.
- 향후 schema 변경: `ALTER TABLE ADD COLUMN ... DEFAULT ...` 만, DROP / RENAME 금지.

### 5.2 Token table migration (Phase 4)

- 기존 `~/.mctrader/local_token` 의 token 을 신규 `tokens` table 에 row 1개로 import (role=`admin`, alias=`local-default`).
- 기존 file 은 read-only fallback 으로 유지 (P4 가 release 되어도 P3 와 호환).
- P5 에서 file fallback deprecate, P6 에서 file 자동 삭제 + DB 단일 SSOT.

### 5.3 Rollback

- Phase 별 PR 단위 rollback. audit DB 는 stateless (rollback = 신규 install 과 동일, file 삭제로 reset).
- Token table rollback: `tokens` table drop + file fallback 재활성 (P4 PR revert 시 자동).

## 6. 리팩터링 선행 (RefactorAgent 산출)

### 6.1 mctrader-web

- 기존 `lifecycle.py` 의 `GRACEFUL_STOP_TIMEOUT_SECONDS` 상수를 `api/admin/control_adapter.py` 에서도 import 하여 timeout SSOT 유지. 별도 상수 도입 금지.
- 기존 `auth.py` `TokenAuth` 클래스는 P4 에서 `MultiTokenAuth` (DB-backed) 로 확장. 인터페이스 (FastAPI Header dependency) 동일 유지.

### 6.2 mctrader-engine

- `BacktestExecutor.run` signature 에 `cancel_token: threading.Event | None = None` 추가 (default None → 기존 호출자 호환). loop 첫 iteration 에서 `cancel_token.is_set()` 체크 + `CancelledError` raise.
- WFO `coordinator.run` 동일 인자 추가, trial 시작 시 체크.
- 기존 동기 호출자 (CLI / 테스트) 영향 0 (default None).

## 7. 보안 설계 (SecurityArchitectAgent 산출)

### 7.1 Trust boundary

ADR-014 §"Trust boundary" 참조. 본 절은 위협 모델 + 완화 매핑.

### 7.2 인증 (Bearer + role + HMAC)

- `Authorization: Bearer <token>` header (§7.B 사전 채택, 본 단계 검증).
- Token 형식: `<token_id>.<HMAC_SHA256(token_id || role || created_at, secret)>` — token_id 만 DB lookup, HMAC 가 위조 차단.
- DB row: `tokens(id PK, role, alias, created_at, expires_at, revoked_at)`.
- secret: 환경변수 `MCTRADER_ADMIN_TOKEN_SECRET` (또는 file-based dev fallback).

### 7.3 인가 (RBAC)

| Role | `/admin/status/*` | `/admin/control/*` | `/admin/rbac/*` |
|------|-------------------|---------------------|------------------|
| viewer | OK | 403 | 403 |
| operator | OK | OK | 403 |
| admin | OK | OK | OK |

403 은 audit row append (`outcome=rbac_reject`).

### 7.4 운영 리스크 (OperationalRiskArchitectAgent 산출, 5 항목)

| # | 항목 | 설계 / 완화 |
|---|------|-------------|
| 7.4.1 | DR (disaster recovery) | UC-8 admin "Boot sequence" 수동 명령 — dependency order: market_gw library load → collector → paper_runner. 자동 boot 미제공. SQLite WAL 부팅 시 auto-checkpoint. |
| 7.4.2 | Disconnect (heartbeat stale) | heartbeat sink read 시 `now - last_ts > N (default 15s)` → SM `[degraded]` 표시. control 명령 미차단. UI 가 "stale" 라벨 표시. |
| 7.4.3 | Clock skew | server clock (`datetime.now(timezone.utc)`) 단독 사용. heartbeat schema 의 `ts` vs server clock ±5s drift 허용. SM transition 의 `since_ts` 는 server clock 만. |
| 7.4.4 | Rate limit | control 30/min/token, status 300/min/token. 초과 시 429 + audit (`outcome=rate_limit`). engine_id 별 추가 bucket 미적용. |
| 7.4.5 | Env isolation | `control_adapter` 는 OS 분기를 단일 abstraction. systemd unavailable detection (`shutil.which("systemctl") is None or os.name=="nt"`) → subprocess fallback. 분기 결정은 부팅 시 1회 캐시. |

### 7.5 입력 검증

- `engine_id` 는 engine-id-naming.v1.md regex 검증 (`^(collector|paper_runner|backtest|wfo|market_gw)-[a-z0-9_-]{1,64}$`).
- POST body 는 Pydantic model — 필드 외 거부.
- `Idempotency-Key` 는 UUID4 또는 ULID format 강제.

### 7.6 Output / 로그

- audit row 의 `params_hash` 만 저장, plaintext params 미저장 (전략 파라미터 leak 방지).
- 로그 (FastAPI access log) 에 token plaintext 출력 금지 — token_id 만.

### 7.7 N/A 항목

데이터 prepared 외부 호출 / 3rd-party API 호출 없음 (control_adapter 는 모두 local capability). CSRF 는 cookie 미사용 (token-bearer scheme) 으로 mitigation.

## 8. Test Contract (TestContractArchitectAgent 산출)

### 8.1 Unit (Phase 별)

| Phase | 테스트 그룹 | 항목 |
|-------|-------------|------|
| P1 | import smoke | 7 module + 4 page import OK |
| P2 | status read | heartbeat sink stub × 5 engine class × 3 state (running/degraded/stopped) |
| P3 | SM transition | daemon SM 6 state × 4 verb 매트릭스 + one-shot SM 4 state × 2 verb |
| P3 | control_adapter | systemd mock + subprocess mock + in-process 3 OS 분기 |
| P3 | idempotency | 동일 Idempotency-Key 재요청 → cached response (24h 내) |
| P4 | RBAC | 3 role × 6 path × 2 method matrix |
| P4 | audit hash chain | 1000 row append + verify CLI OK + 강제 변조 후 verify FAIL |
| P5 | rate limit | 29 / 30 / 31 회 (control), 299 / 300 / 301 회 (status) |
| P6 | E2E | UC-1 ~ UC-8 시나리오 자동화 |

### 8.2 경계 조건 (Edge Cases)

Story §5.3 EC-1 ~ EC-11 모두 testable. 특히:
- EC-1 동시 control 요청 — `Idempotency-Key` 동일 / 다른 두 케이스
- EC-7 engine_id collision — heartbeat sink dynamic enumerate vs static config 통합
- EC-8 audit SQLite 손상 — DB 부재 / corrupt 두 케이스, control 은 graceful degrade

### 8.3 Invariant test

- audit_log table 의 `prev_hash` chain 무결성 — `seq=N+1.prev_hash == seq=N.row_hash` 항등성
- SM transition table — ADR-015 정의된 valid transition 만 허용, 그 외 모두 409

### 8.4 Cross-platform smoke (AC-7)

- Windows: pytest 가 `os.name=="nt"` 분기에서 in-process / subprocess fallback 실행
- Linux CI: systemd 가용 시 systemd 분기 실행, 미가용 시 subprocess fallback

### 8.5 Performance baseline (TestContract 검증)

- status overview endpoint p95 < 500ms (5 engine 조회 + heartbeat sink read)
- control endpoint p95 < 1s (audit append + adapter dispatch)
- audit verify CLI: 100k row < 10s (sha256 hash chain)

### 8.6 Observability metric 카탈로그 (Phase 4-6 박제)

mctrader-web `/metrics` (Prometheus exposition format) — Phase 4 (audit 도입) 시작 시점부터 emit.

| Metric | type | label |
|--------|------|-------|
| `mctrader_admin_control_dispatch_total` | counter | `engine_class`, `verb`, `outcome` |
| `mctrader_admin_audit_append_latency_ms` | histogram | (none) |
| `mctrader_admin_idempotency_hit_total` | counter | (none) |
| `mctrader_admin_rate_limit_block_total` | counter | `bucket` (`control` / `status`) |
| `mctrader_admin_sm_transition_total` | counter | `engine_class`, `from_state`, `to_state` |

label cardinality 고정 (engine_class 5, verb ≤ 5, outcome ≤ 6, bucket 2, state ≤ 6 × 6) — Prometheus scrape 부담 무시 가능 수준.

scrape 주기: 15s default (Phase 5 docs).

## 9. 재시작 가능 작업 단위

각 Phase 는 독립 PR. 단일 PR 실패 시 `git revert` 가능. ADR / contract 박제 PR (현재) 은 코드 변경 없음 — 후속 PR 의 기준 SSOT.

## 10. ADR 판단

- ADR-014 (control plane separation) — Accepted, 본 단계 박제
- ADR-015 (engine state machine) — Accepted, 본 단계 박제
- ADR-016 (audit log immutability) — Accepted, 본 단계 박제
- engine-id-naming.v1.md (domain contract) — Active, 본 단계 박제

## 11. 데이터 마이그레이션

§5 + ADR-016 §"Schema migration" + §"Backup + retention" 참조. 본 단계 핵심:

| 항목 | 결정 |
|------|------|
| 11.1 audit DB 위치 | `mctrader-web/data/admin_audit.sqlite` (신규 디렉토리, gitignore) |
| 11.2 schema migration | DDL on first boot, ALTER ADD COLUMN only |
| 11.3 backup | 일일 cron `data/backups/admin_audit_<YYYYMMDD>.sqlite` (P6 docs) |
| 11.4 retention | 90일 default, env override |
| 11.5 rollback | Phase PR revert 단위, audit DB 는 stateless |
| 11.6 idempotency | 별도 `idempotency_cache` table 24h cleanup (audit 영구성과 분리, OperationalRiskArch consult) |
| 11.7 token table migration | 기존 single static token → DB row 1개 (admin role, P4 자동 마이그레이션, P6 file 삭제) |

## 12. Open Questions (해소 결과)

§Story §11 Q1-Q4 grep 결과 박제. 본 Change Plan §2 + §6 + ADR-014/015/016 에 통합 반영 완료.
