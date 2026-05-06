---
story_key: MCT-97
story_issues:
  - repo: mclayer/mctrader-hub
    number: 110
status: phase:요구사항
---

# MCT-97: Admin Engine Control Panel — 5-engine inspect+control, remote-ready

- **Issue**: #110
- **Status**: phase:요구사항

## 1. 사용자 요구사항 (verbatim — Phase 2 후속 CFP 까지 CODEOWNERS manual review 로 변경 차단)

web의 요구조건이다. mctrader를 위해 작업하는 engine들을 점검하고 제어할 수 있는 panel을 만들어라. 현재는 localhost에 존재하지만 원격으로 작업될 수도 있기 때문에 이를 고려하라. codeforge를 통해 반드시 작업하라.

## 2. 도메인 해석

> 사용자 directive: codeforge-only. codex / Sonnet decider 제외. 본 §2-§6 은 codeforge-requirements lane (PL + Domain + Analyst + Researcher) 자율 결정 박제.

### 2.1 "engine" 의 정확한 정의 (D2=α scope = 5 process class)

| Engine class | Repo | Process | 현재 lifecycle 자산 |
|--------------|------|---------|---------------------|
| **collector** | mctrader-data | `mctrader-data collect` (HA 다중 노드) | systemd unit + heartbeat sink (MCT-89~96) |
| **paper runner** | mctrader-engine | `paper_runner` (realtime stream + runtime executor) | mctrader-web `api/lifecycle.py` 부분 존재 |
| **backtest executor** | mctrader-engine | `BacktestExecutor` (one-shot job) | `api/backtest_lifecycle.py` |
| **WFO executor** | mctrader-engine | WFO orchestrator (multi-fold job) | `api/wfo_lifecycle.py` |
| **market gateway** | mctrader-market(-bithumb) | exchange WS/REST adapter | 미정 (별도 process or paper_runner 내부 — Architect grep §11 Q2) |

→ control plane verb 가 engine class 별로 다름 — daemon 은 `start/stop/restart`, one-shot 은 `trigger/cancel`.

### 2.2 도메인 invariant (신규 ADR 후보)

#### 2.2.1 control plane vs data plane 분리 (ADR-NEW-1)

- control plane: `/admin/control/*` (start/stop/restart/trigger/cancel)
- data plane: heartbeat sink + market quote/trade/OMS (read-only `/admin/status/*`)
- **이유**: data plane 장애 (예: market gateway WS 끊김) 가 control plane 으로 전파 차단 — admin 이 복구 명령 가능 보장. heartbeat sink (MCT-89~96) 는 read-only 관측 채널, control 용 아님.

#### 2.2.2 engine state machine (ADR-NEW-2)

```
daemon: [stopped] -start-> [starting] -ready-> [running] -stop-> [stopping] -> [stopped]
                                       |
                                       +-crash-> [crashed] -restart-> [starting]
                                       +-heartbeat stale > N-> [degraded]

one-shot: [queued] -> [running] -> [completed | failed | cancelled]
```

- `[degraded]` = collector HA partial node failure 와 동일 의미 (control 가능, alarm).
- idempotent guard: `[running]` 중 start 거부 (409), `[stopping]` 중 신규 start 거부.

#### 2.2.3 audit log immutability (ADR-NEW-3)

모든 control 명령 (start/stop/restart/cancel/trigger) 은 **append-only audit log** 에 기록. row schema:
```
(ts, actor, role, engine_class, engine_id, action, params_hash,
 request_id, outcome, latency_ms, source_ip, prev_hash, row_hash)
```
hash chain (`prev_hash` + `row_hash`) tamper detection.

#### 2.2.4 engine_id naming SSOT

heartbeat schema (`docs/domain-knowledge/contracts/heartbeat-schema.v1.md`) 의 `node_id` 를 control plane `engine_id` 와 unify. 신규 `docs/domain-knowledge/contracts/engine-id-naming.v1.md` 박제 의무.

## 3. 관련 ADR

기존 `docs/adr/` 검색: control plane / panel / RBAC 관련 ADR 부재.

**신규 ADR 박제 (codeforge-design lane, 2026-05-06)**:

| ADR | 제목 | 위치 |
|-----|------|------|
| ADR-014 | Control plane vs data plane separation | [`docs/adr/ADR-014-control-plane-separation.md`](../adr/ADR-014-control-plane-separation.md) |
| ADR-015 | Engine state machine (daemon + one-shot) | [`docs/adr/ADR-015-engine-state-machine.md`](../adr/ADR-015-engine-state-machine.md) |
| ADR-016 | Audit log append-only + hash chain | [`docs/adr/ADR-016-audit-log-immutability.md`](../adr/ADR-016-audit-log-immutability.md) |

발번: `docs/adr/` 최신 (ADR-013) + 1 = 014부터 순서대로 부여.

**신규 domain-knowledge 박제**:
- [`docs/domain-knowledge/contracts/engine-id-naming.v1.md`](../domain-knowledge/contracts/engine-id-naming.v1.md) — heartbeat `node_id` ↔ control `engine_id` SSOT, regex `^(collector|paper_runner|backtest|wfo|market_gw)-[a-z0-9_-]{1,64}$`

**관련 Change Plan**:
- [`docs/change-plans/MCT-97-change-plan.md`](../change-plans/MCT-97-change-plan.md) — 6 phase 분할 + module layout + Test Contract

## 4. 관련 코드 경로

### mctrader-web (확장 대상)

```
mctrader-web/src/mctrader_web/
├── api/
│   ├── auth.py              ← RBAC 확장 진입점 (§11 Q1 grep)
│   ├── lifecycle.py         ← paper runner control 기존
│   ├── backtest_lifecycle.py ← backtest trigger 기존
│   ├── wfo_lifecycle.py     ← WFO trigger 기존
│   ├── routes.py            ← /admin/* prefix 신규
│   └── (신규) admin/
│       ├── control.py       ← 5 engine control endpoint
│       ├── status.py        ← heartbeat sink read-only
│       ├── audit.py         ← audit log query
│       └── control_adapter.py ← OS/engine-class 분기 (§7.D)
└── dashboard/
    ├── 00_status.py         ← 기존 (00-03)
    └── (신규) 1{0..3}_admin_*.py ← admin section entry
```

### 의존 repo (read-only reference)
- `mctrader-data/src/mctrader_data/heartbeat/` — heartbeat sink schema
- `mctrader-engine/src/mctrader_engine/runtime/` — paper_runner lifecycle hook
- `mctrader-engine/src/mctrader_engine/{executor,wfo}/` — cooperative cancel hook (§11 Q3 grep)
- `mctrader-market(-bithumb)/src/` — market gateway process spec (§11 Q2 grep)

### 기존 자산 (재사용)
- mctrader-web FastAPI: `api/{auth,lifecycle,backtest_lifecycle,wfo_lifecycle,routes,models,config,app}.py`
- mctrader-web Streamlit: `dashboard/{00_status,01_paper_panel,02_backtest_panel,03_wfo_panel}.py` + `status_adapter.py`
- mctrader-web client: `api_client/client.py`

## 5. 요구사항 확장 해석

### 5.1 유스케이스 (8 시나리오)

| # | Actor | 상황 | Trigger | Expected outcome |
|---|-------|------|---------|------------------|
| **UC-1** | admin (정상) | 아침 점검 — 모든 engine green 확인 | 대시보드 진입 | 5 engine 상태 + heartbeat age + last error 한 화면 |
| **UC-2** | admin (정상) | paper runner 전략 변경 후 재시작 | "Restart paper" 클릭 | graceful stop → state=[stopped] 확인 → start → state=[running] within SLO |
| **UC-3** | admin (정상) | backtest 1회 실행 | "Trigger backtest" + 파라미터 입력 | job queued → running → completed, 결과 link |
| **UC-4** | admin (장애) | collector node A heartbeat stale | 자동 alarm + 수동 restart | engine_id=collector-A restart, B/C 영향 없음 |
| **UC-5** | admin (장애) | paper runner crash loop | crash 감지 후 control | 자동 restart 회수 N회 도달 시 panel "manual intervention" 표시, admin 이 stop 으로 loop 중단 |
| **UC-6** | admin (원격) | 외부망에서 노트북으로 점검 | VPN 또는 reverse tunnel 통해 접속 | 인증 + TLS, 동작은 localhost 동일 |
| **UC-7** | admin (원격) | 원격 회선 latency 500ms+ | control 명령 발신 | UI 가 "in-flight" indicator + idempotent retry 차단 (중복 click 방지) |
| **UC-8** | admin (장애 복구) | 모든 engine 동시 down (전원 재투입 후) | "Boot sequence" 또는 순차 start | dependency order: market-gw → collector → paper, 한 줄 명령 |

### 5.2 Acceptance Criteria

#### AC-1 점검 (read)
- [ ] 5 engine class × N instance 의 현재 SM state (§2.2.2) panel 표시
- [ ] heartbeat age, last error, recent restart count, uptime 표시
- [ ] one-shot job (backtest/WFO) 최근 N건 history (queued/running/completed/cancelled/failed)
- [ ] refresh 주기 ≤ 5 sec
- [ ] read 경로는 control 장애와 독립 (data plane)

#### AC-2 제어 (write)
- [ ] daemon: start/stop/restart 3 verb, one-shot: trigger/cancel 2 verb
- [ ] 모든 control 은 `Idempotency-Key` header (Stripe pattern), 24h dedupe
- [ ] SM 위반 transition → 409 Conflict + audit log 기록
- [ ] graceful stop timeout (default 30s) 후 SIGKILL fallback (daemon)
- [ ] one-shot cancel 은 cooperative signal (engine-side hook 필요 — §11 Q3)

#### AC-3 RBAC
- [ ] role 3개: `viewer` (read) / `operator` (control) / `admin` (RBAC 변경 + audit query)
- [ ] solo dev 본인은 admin role single user 로 시작
- [ ] schema 는 multi-user (token table with role column), 구현은 1 user
- [ ] 모든 `/admin/*` route 는 token 필수, viewer 도 별도 token

#### AC-4 audit log
- [ ] 모든 control 명령은 §2.2.3 schema row append
- [ ] panel 에서 query (filter: actor / engine / time range / outcome)
- [ ] DB 권한 + app guard 양면으로 UPDATE/DELETE 차단
- [ ] hash chain verification CLI 제공

#### AC-5 원격 보안
- [ ] panel 은 TLS + token-bearer 만 책임 (transport 외부 위임)
- [ ] localhost binding 외 접속 시 TLS 필수 (self-signed dev OK)
- [ ] rate limit: control endpoint 분당 30회 / status 분당 300회 (per token)
- [ ] CSRF: token-bearer scheme (cookie 미사용) 으로 mitigation
- [ ] 외부망 직접 노출 금지 — Tailscale/SSH tunnel 권장 (docs)

#### AC-6 codeforge 채널
- [ ] Story `docs/stories/MCT-97.md` 는 story-init workflow 로 생성 ✓ (본 PR)
- [ ] §1 immutable (story-section-1-immutable workflow 가 보장)
- [ ] PR 은 phase-gate-mergeable workflow 통과
- [ ] phase 라벨 invariant 준수 (phase-label-invariant)
- [ ] FIX 발생 시 fix-ledger-sync workflow 로 §10 동기화

#### AC-7 cross-platform
- [ ] Windows local dev: panel UI + API 동작 (control 은 localhost in-process)
- [ ] Linux prod: panel + systemd-managed daemon control
- [ ] OS 분기는 control adapter 한 군데 (§7.D)

### 5.3 Edge Cases

| # | Case | 처리 |
|---|------|------|
| EC-1 | 동시 control 요청 | `Idempotency-Key` dedupe + DB row lock, 후행 409 |
| EC-2 | crash 중 stop | SM no-op, audit "no-op" 기록, UI success |
| EC-3 | 원격 latency 5sec 중 재클릭 | UI button disable + server idempotent guard |
| EC-4 | network partition 중 status | last-known cache + "stale since X" 표시, control 시 명시적 confirm dialog |
| EC-5 | RBAC bypass 시도 | rate limit + audit + (옵션) Tailscale ACL |
| EC-6 | one-shot cancel 중 partial result | engine-side cooperative cancel, 부분 결과는 폐기 (default) |
| EC-7 | engine_id collision (HA node 추가/제거) | heartbeat `node_id` SSOT, panel dynamic enumerate |
| EC-8 | audit SQLite 손상 | WAL fsync + 일일 백업 cron, read 실패 시 control 은 계속 (graceful degrade) |
| EC-9 | systemd 미설치 (Windows dev) | §7.D adapter 가 in-process subprocess fallback |
| EC-10 | token 만료 중 long-running poll | refresh token + UI re-auth prompt |
| EC-11 | hash chain tamper detect | 검증 실패 시 panel 경고 + 운영자 manual review trigger |

### 5.4 자율 결정 모드 가정 (사용자 directive 로 PL 가정 확정)

| # | 가정 | 확정 근거 |
|---|------|-----------|
| AS-1 | "원격 운영" = solo dev 본인 외부 노트북 LAN/VPN 접속 (cloud 배포 아님) | 보수적 가정, cloud 별도 Story |
| AS-2 | admin = solo dev 본인 single user, schema 만 multi-user 준비 | mctrader 프로젝트 컨텍스트 |
| AS-3 | 5 engine 외 추가 engine (live executor) 별도 Story | D2=α scope |
| AS-5 | audit log SQLite 단일 파일 (외부 SIEM 미연동) | solo dev 환경 적정선 |
| AS-6 | reverse tunnel 은 admin 수작업 (panel 외부) | panel 책임 경계 명확화 |
| AS-4 | market gateway = 별도 process? library? | **Architect grep (§11 Q2)** |

본 spec 은 library 가정 (paper_runner 내장) — Architect grep 결과 process 발견 시 phase 추가.

## 6. 외부 지식 배경

### 6.1 control plane / admin panel 선행사례

| 사례 | 시사점 |
|------|--------|
| **systemd + cockpit** | Linux daemon 표준 control. → mctrader collector 가 이미 systemd unit (MCT-94). admin panel 이 systemd wrapping 자연 |
| **Apache Airflow webserver** | one-shot job (DAG run trigger / cancel) UI 표준. → backtest/WFO trigger UI 참고 |
| **Grafana + Loki/Prometheus** | read-only observability. → 점검(read) dashboard pattern 참고 |
| **Portainer (Docker)** | container start/stop/restart UI + RBAC + audit log. → RBAC + audit 패턴 참고 |
| **Kubernetes Dashboard** | Pod restart / log query / RBAC. 너무 무거움 → 패턴만 |

### 6.2 원격 보안 선행 패턴

| 패턴 | 적합성 |
|------|--------|
| **Tailscale (WireGuard mesh)** | solo dev 최적. zero-config, MagicDNS, ACL. mctrader-web 이 Tailnet IP 만 binding → 외부 노출 zero |
| **Cloudflare Tunnel** | 도메인 + Cloudflare Access 필요 시. solo dev overkill |
| **SSH local port forward** | 가장 간단, 추가 인프라 0. 단점: forward 항상 유지 필요 |
| **VPN (WireGuard/OpenVPN)** | self-host 부담 |

→ **권고**: Tailscale 1순위, SSH tunnel 2순위. panel 은 TLS + token auth 만, transport 는 외부 도구 위임.

### 6.3 RBAC + audit 라이브러리

| 옵션 | 평가 |
|------|------|
| **FastAPI + python-jose (JWT)** | 표준, mctrader-web 이미 FastAPI 기반. token-based RBAC 자체 구현 적합 |
| **Casbin** | 정책 RBAC. solo dev overkill |
| **audit log: SQLite + WAL** | 단순, 의존성 0. hash chain tamper detection |

### 6.4 idempotent control + request dedupe

- **Stripe Idempotency-Key 패턴**: `Idempotency-Key` header → server 가 24h DB 에 저장, 동일 key 재요청 시 캐시된 response 반환. 채택.

## 7. 설계 서사

> **codeforge-design lane 통합 산출 (2026-05-06)** — ArchitectPLAgent + 6 deputy (CodebaseMapper / Refactor / SecurityArchitect / TestContractArchitect / DataMigrationArchitect / OperationalRiskArchitect) + ArchitectAgent (chief). codeforge-requirements lane 의 §7.A-§7.J 사전 채택 결정 모두 검증 통과. 상세 narrative 는 [`docs/change-plans/MCT-97-change-plan.md`](../change-plans/MCT-97-change-plan.md) 참조 (본 §7 은 결정 SSOT, Change Plan 이 구현 매핑).
>
> **검증 결과 요약** (deputy 별):
> - **CodebaseMapper** (§2.1-§2.4): mctrader-web 자산 + mctrader-engine cancel hook 분포 + mctrader-market(-bithumb) library only 확정
> - **RefactorAgent** (§3.2 module layout): `api/admin/` 7 module + `dashboard/pages/10-13_admin_*.py` 4 page + `data/` 신규 디렉토리
> - **SecurityArchitect** (§7.B 검증): Bearer + role + HMAC 결정 유지, `MultiTokenAuth` 신설로 기존 `TokenAuth` 호환
> - **OperationalRiskArchitect** (§7.D 검증): hybrid adapter 결정 유지, systemd unavailable detection (`shutil.which("systemctl") is None or os.name=="nt"`) 부팅 시 1회 캐시
> - **DataMigrationArchitect** (§7.F 검증): SQLite WAL + hash chain 결정 유지, `idempotency_cache` table 분리 (audit 영구성과 격리)
> - **TestContractArchitect** (AC-7 검증): cross-platform smoke 컨트랙트 + UC-1~UC-8 E2E 시나리오 8개 모두 testable

### 7.A Streamlit admin section 구현 패턴 → **(a1) numeric prefix 확장**

`10_admin_overview.py` / `11_admin_control.py` / `12_admin_audit.py` / `13_admin_rbac.py`. 기존 `dashboard/` 의 numeric prefix 규칙 (00-03) 연장.

**근거**: 학습 비용 0, Streamlit native multipage, prefix gap 으로 admin 영역 시각 분리.

**Reject**: (a2) `st.navigation` Streamlit ≥1.36 lock-in + 4 page 마이그레이션. (a3) 별도 sub-app 두 entry point → 운영 부담.

### 7.B 인증/RBAC 모델 → **(b1) Bearer token + role claim (signed)**

`Authorization: Bearer <token>` header. token 은 SQLite `tokens` table row 참조 (role column). signed (HMAC-SHA256, secret in env). 만료/취소 가능.

**Token 형식 (SecurityArchitect 변호)**: `<token_id>.<HMAC_SHA256(token_id || role || created_at, secret)>`. `token_id` 만 DB lookup (정수 PK), HMAC 가 위조 차단. secret 환경변수 `MCTRADER_ADMIN_TOKEN_SECRET`. revoke 메커니즘: `tokens.revoked_at IS NOT NULL` 체크 (DB-backed, 즉시 효력) + `expires_at` (TTL 자연 만료).

**기존 `TokenAuth` 호환 (Q1 결과 반영)**: P3 까지는 기존 `~/.mctrader/local_token` file fallback 유지. P4 에서 신규 `MultiTokenAuth` (DB-backed) 가 `tokens` table 검증 + 기존 token 을 row 1개로 자동 import (id=`local-default`, role=`admin`). FastAPI Header dependency interface 동일 유지로 호출자 영향 0. P6 에서 file 자동 삭제.

**근거**: viewer/operator/admin 3 role claim 1개 충분, DB-backed revoke, signed 위변조 차단, FastAPI dependency injection 호환.

**Reject**: (b2) role 별 token revoke 복잡. (b3) OIDC overkill. (b4) mTLS hybrid Tailscale 책임 중복 + Windows cert 부담.

### 7.C 원격 transport 모델 → **(c1) FastAPI `/admin/*` 단일 control plane**

mctrader-web 가 모든 engine 의 단일 control gateway. engine repo 추가 endpoint 없음. mctrader-web 내부 §7.D 메커니즘으로 위임.

**근거**: single TLS endpoint → 인증/audit/rate-limit 한 곳, engine repo 에 web 의존성 0, 기존 lifecycle 자산 재사용, cross-repo PR 최소화.

**Reject**: (c2) engine 자체 endpoint 인증/audit 5중. (c3) hybrid 의사결정 분산.

### 7.D Engine process control 메커니즘 → **(d4) hybrid adapter pattern**

`mctrader-web/src/mctrader_web/api/admin/control_adapter.py` 단일 abstraction.

| Engine | Linux prod | Windows dev |
|--------|-----------|-------------|
| collector (HA) | systemd (`systemctl --user`) | subprocess (in-process tracking) |
| paper runner | systemd | subprocess |
| backtest | in-process Python | 동일 |
| WFO | in-process Python | 동일 |
| market gateway | library status read only | 동일 |

**근거**: collector 가 이미 systemd (MCT-94), backtest/WFO in-process 자연, adapter 한 군데 분기로 AC-7 충족, 의존성 0.

**OperationalRiskArchitect 변호 (failure mode + 추적 안정성)**:
- **systemd unit failure mode**: `systemctl --user start <unit>` 실패 시 stdout/stderr capture + `systemctl --user status` 로 last exit code 조회. failure 는 SM `[crashed]` 전이. lingering enable 미설정 시 user logout 으로 unit 종료 — Story §7.J Risk + P5 docs 에서 `loginctl enable-linger <user>` 명시.
- **subprocess 추적 안정성 (Windows dev)**: `subprocess.Popen` PID + return code polling (1 sec interval). orphan 회피 — mctrader-web 종료 시 SIGTERM (Linux) / `terminate()` (Windows) 후 30s graceful timeout, 이후 SIGKILL / `kill()`. PID 영속화: `data/runtime/<engine_id>.pid` 파일 (재시작 후 reattach 시도).
- **OS detection 1회 캐시**: `shutil.which("systemctl") is None or os.name == "nt"` → subprocess 분기. 부팅 시 1회 결정, runtime 변경 가정 안 함.

**Reject**: (d1) systemd 통일 backtest unit 부담 + Windows 불가. (d2) HTTP 통일 §7.C 중복. (d3) supervisord Windows 미지원.

### 7.E 실시간 metric/event 채널 → **(e1) polling 5s + (e4) heartbeat sink 재활용**

Streamlit `time.sleep` + `st.rerun` polling 5초. underlying data 는 collector heartbeat sink + status_adapter 재활용.

**근거**: Streamlit SSE/WebSocket native 약함, 5s latency 점검 panel 충족 (실시간 trading UI 아님), heartbeat sink 1초 interval 활용, Tailscale 호환 검증 부담 회피.

**Reject**: (e2) SSE / (e3) WebSocket Streamlit custom component 부담.

control 응답은 polling 과 별개로 즉시 동기 응답 (POST → 200/409).

### 7.F Audit log scheme → **(f2) SQLite (single file, WAL, hash chain)**

`mctrader-web/data/admin_audit.sqlite` (WAL mode). schema §2.2.3. hash chain (`prev_hash` + `row_hash`) tamper detection. 일일 백업 cron 권장.

**DataMigrationArchitect 변호 (백업/복구 + retention 전략)** — ADR-016 SSOT, 본 §7.F 는 요약:
- **두 table 분리**: `audit_log` (영구, hash chain) + `idempotency_cache` (24h cleanup, dedupe 전용). 24h cleanup 이 audit chain 영향 0 (별도 table).
- **Backup**: 일일 cron — POSIX `cron` (Linux) / Windows Task Scheduler. SQLite `VACUUM INTO` 로 consistent snapshot. backup 직후 `mctrader-web admin audit verify` 자동 실행 — verify FAIL 시 backup 롤백 + alert.
- **Retention**: 90일 default (env override `MCTRADER_AUDIT_RETENTION_DAYS`). pruning 미강제 (solo dev 환경 1년 < 100MB 추정). pruning 도입 시 archive DB 로 export + chain genesis 재설정 (chain continuation 보존).
- **Cross-platform**: WAL 은 local fs 만 가정 — NFS/SMB placement 금지 (fsync 보장 부재).
- **Concurrent access**: WAL = 다중 reader + 단일 writer 자연 지원, panel polling 중 control append 안전.

**근거**: 단일 파일 backup 단순, WAL concurrent read 중 write, hash chain forensic, mctrader-engine event_store 와 책임 경계 명확.

**Reject**: (f1) JSONL query 부담. (f3) event_store 통합 trading domain pollution. (f4) 이중 sync 복잡.

### 7.G Story 분할 → **(g1) 단일 MCT-97 + 6 phase**

| Phase | 범위 |
|-------|------|
| P1 | admin section skeleton (Streamlit `10-13_admin_*` + FastAPI `/admin/*` route + auth.py 호환) |
| P2 | status read (5 engine + heartbeat sink 통합 + polling) |
| P3 | control write (daemon + one-shot + idempotent guard + SM transition) |
| P4 | RBAC + audit (token table + role + audit log + hash chain) |
| P5 | remote security (TLS + rate limit + Tailscale docs) |
| P6 | E2E + cross-platform (Windows + Linux smoke + retention cron) |

**근거**: codeforge debut (CFP-96) 직후 Epic ceremony 회피, 6 phase phase-gate-mergeable 표준 부담 적정, cross-cutting (auth/audit) sub-Story 분할 비효율.

**Reject**: (g2) Epic + 7 sub ceremony 7배. (g3) Epic + 2 인위적 분리.

**TestContractArchitect 변호 (AC-7 cross-platform smoke 컨트랙트)**:
- **Phase 1**: import-only smoke (7 신규 module + 4 신규 page) — Windows + Linux 모두 동일.
- **Phase 3**: `control_adapter` 분기별 contract test:
  - Linux CI: `systemd` 가용 시 systemd 분기 (mock `systemctl --user`) + 미가용 시 subprocess 분기 (실제 `python -m` 호출 + cleanup) 두 path 모두 실행
  - Windows CI: `os.name == "nt"` 분기에서 in-process / subprocess 두 path 실행 (systemd 분기 skip)
- **Phase 6**: UC-1 ~ UC-8 8 시나리오 자동화 — Windows + Linux GitHub Actions matrix.
- **Performance baseline (Phase 6)**: status overview p95 < 500ms, control endpoint p95 < 1s, audit verify CLI 100k row < 10s.

### 7.H Cross-repo 영향 + 순서 → **mctrader-web 단일 repo 작업**

§7.C + §7.D 결정으로 mctrader-web 외 PR **0건** 목표.

**예외**:
- mctrader-data: heartbeat schema docs 정합 만 (mctrader-hub 박제, mctrader-data 코드 변경 0)
- mctrader-engine: cooperative cancel hook 부재 시 P3 minimal hook PR 1건 (§11 Q3)
- mctrader-market(-bithumb): §11 Q2 결과 후 process 면 control endpoint PR 1건

**PR 순서**:
1. mctrader-hub: ADR-NEW-1/2/3 + engine-id-naming.v1.md (P1 시작 전)
2. mctrader-web: P1 → P6 순차 (codeforge phase-gate-mergeable green)
3. (조건부) mctrader-engine cancel hook PR — P3 진입 직전
4. (조건부) mctrader-market process control PR — §11 Q2 결과 후

### 7.I Open Questions (codeforge-design lane grep 해소, 2026-05-06)

| # | Question | 해소 결과 |
|---|----------|-----------|
| Q1 | `mctrader-web/api/auth.py` 현 scheme? | **단일 static token** (MCT-50, `~/.mctrader/local_token`, `secrets.token_urlsafe(32)`, file mode 600). `TokenAuth` FastAPI dependency 가 `Authorization: Bearer <token>` 검증. → §7.B 호환 layer 는 **`MultiTokenAuth` (DB-backed) 신설 + 기존 single token 을 P4 에서 admin role row 1개로 import** (Change Plan §5.2). 인터페이스 (FastAPI Header dependency) 동일 유지로 P3 까지 호환. |
| Q2 | mctrader-market(-bithumb) 별도 process 유무? (§AS-4) | **library only**. `mctrader_market` (candle/lifecycle/order/orderbook/providers/types) + `mctrader_market_bithumb` (adapter/client/ws_client/rest_throttle) 모두 라이브러리 module — `if __name__ == "__main__"` / `console_scripts` / `entry_points` grep **0건**. → §AS-4 가정 확정, market gateway 는 status read 전용 (`market_gw-<exchange>-<env>` engine_id). control 명령 대상 외. mctrader-market(-bithumb) repo PR **0건**. |
| Q3 | mctrader-engine cooperative cancel hook 존재? | **부분 존재**. ① `runtime.paper_runner.PaperRunner.cancel()` async + `_on_shutdown` 콜백 + `executor.cancel()` 보유 (asyncio.Event). ② `executor.paper.PaperExecutor._cancel_event` 보유. ③ `executor.backtest.BacktestExecutor.run()` 은 synchronous per-bar loop, **cancel hook 부재**. ④ `wfo.search.coordinator` 도 **부재** (fail-fast 분기만). → P3 진입 직전 mctrader-engine PR 1건 필요 (BacktestExecutor + WFO coordinator 에 `cancel_token: threading.Event` 인자 추가, default None 으로 호환 유지). ADR-015 §"Cooperative cancel hook 요구" 참조. |
| Q4 | mctrader-web `data/` 디렉토리 convention? | **미존재**. `mctrader-web/` 직접 자식 디렉토리 grep 결과 `data/` 없음 (`.venv/Lib/site-packages/...` 만 검색됨). → ADR-016 가 신규 디렉토리 `mctrader-web/data/` 생성 + `.gitignore` 항목 추가 + 환경변수 override `MCTRADER_ADMIN_AUDIT_PATH` 지원. audit SQLite 위치 = `mctrader-web/data/admin_audit.sqlite`. |

### 7.J Risk + Mitigation

| Risk | Mitigation |
|------|-----------|
| §AS-4 (market gateway 구조) 미확인 | **해소 완료** (§11 Q2): library only 확정, mctrader-market(-bithumb) PR 0건 |
| BacktestExecutor / WFO cancel hook 부재 | **해소 완료** (§11 Q3): P3 진입 직전 mctrader-engine PR 1건 — `cancel_token: threading.Event` 인자 추가 (default None 호환) |
| systemd 권한 (sudo 없이 user unit) | `systemctl --user` + `loginctl enable-linger <user>` docs (P5) |
| Windows dev systemd 부재 | §7.D adapter 분기로 subprocess fallback, OS detection 부팅 시 1회 캐시 |
| subprocess orphan (Windows mctrader-web 종료 후) | PID 영속화 `data/runtime/<engine_id>.pid` + 재시작 시 reattach 시도 + 30s graceful timeout 후 kill |
| Tailscale 미설치 | docs 에 SSH local forward fallback 명시 |
| audit hash chain 검증 비용 | 검증 CLI on-demand, panel runtime 검증 안 함, 일일 backup 후 자동 verify |
| audit DB pruning 미강제 | solo dev 환경 1년 < 100MB 추정, P6 retention cron 만 (90일 default), pruning 도입 시 archive export + chain genesis 재설정 |
| DR (모든 engine 동시 down, UC-8) | 자동 boot 미제공, admin manual "Boot sequence" — dependency order: market_gw library load → collector → paper_runner |
| heartbeat sink stall 시 control 차단 | ADR-014 plane 분리 — data plane 장애 control plane 영향 0, last-known cache + "stale since X" UI |
| codeforge workflow 신규 (debut) bug | plugin-codeforge upstream issue (consumer workaround 금지) |

## 8. 개발 서사

*(§7.G 6 phase 분할 기반 — DeveloperPL P1 완료, P2+ 진행 예정)*

### §8.5 Impl Manifest

| Phase | scope | PR | 완료일 | 변경 파일 |
|-------|-------|----|--------|-----------|
| P1 | skeleton | [mctrader-web#16](https://github.com/mclayer/mctrader-web/pull/16) | 2026-05-06 | production 10 / test 3 (합계 13 file, 25 test green) |
| P2 | status read | [mctrader-web#17](https://github.com/mclayer/mctrader-web/pull/17) | 2026-05-06 | production 4 / test 3 (합계 7 file, 31 test green) |
| P3 | control write | [engine#36](https://github.com/mclayer/mctrader-engine/pull/36) + [web#18](https://github.com/mclayer/mctrader-web/pull/18) | 2026-05-06 | engine 3 file (backtest.py+coordinator.py+test_cancel_hook.py) / web 13 file production + 4 file test (75 test green) |

**P1 production 파일 (DeveloperAgent)**

| 파일 경로 | Change Plan 매핑 |
|-----------|-----------------|
| `src/mctrader_web/api/admin/__init__.py` | §4 P1 — admin sub-router 2개 mount (control/status ADR-014) |
| `src/mctrader_web/api/admin/health.py` | §4 P1 — GET /admin/health 200 + version |
| `src/mctrader_web/api/admin/control.py` | §3.2 module layout — P3+ skeleton |
| `src/mctrader_web/api/admin/status.py` | §3.2 module layout — P2+ skeleton |
| `src/mctrader_web/api/admin/audit.py` | §3.2 module layout — P4+ skeleton |
| `src/mctrader_web/api/admin/control_adapter.py` | §3.2 + §7.D hybrid adapter — P3+ skeleton |
| `src/mctrader_web/api/admin/state_machine.py` | ADR-015 SM constants — P3+ skeleton |
| `src/mctrader_web/api/admin/tokens.py` | §7.B MultiTokenAuth — P4+ skeleton |
| `src/mctrader_web/api/admin/audit_db.py` | ADR-016 WAL DB path helper — P4+ skeleton |
| `src/mctrader_web/api/admin/idempotency.py` | §8.3 Idempotency-Key cache — P3+ skeleton |
| `src/mctrader_web/api/app.py` *(modified)* | /admin/* router mount 추가 |
| `src/mctrader_web/dashboard/pages/10_admin_overview.py` | §7.A P1 placeholder |
| `src/mctrader_web/dashboard/pages/11_admin_control.py` | §7.A P1 placeholder |
| `src/mctrader_web/dashboard/pages/12_admin_audit.py` | §7.A P1 placeholder |
| `src/mctrader_web/dashboard/pages/13_admin_rbac.py` | §7.A P1 placeholder |
| `data/.gitkeep` | ADR-016 §11.1 data/ 신규 디렉토리 |
| `data/runtime/.gitkeep` | §7.D PID 영속화 디렉토리 |
| `.gitignore` *(modified)* | ADR-016 SQLite + WAL + pid gitignore 항목 추가 |

**P1 test 파일 (QADeveloperAgent)**

| 파일 경로 | Test Contract 매핑 |
|-----------|--------------------|
| `tests/api/test_admin_health.py` (6 test) | §8.1 P1 import smoke — GET /admin/health 200 + version field + no-auth EC |
| `tests/api/test_admin_routing.py` (10 test) | §8.1 P1 — /admin/control + /admin/status sub-router mount 확인 |
| `tests/dashboard/test_admin_pages_smoke.py` (9 test) | §8.4 P1 — 4 placeholder page import-only smoke (AC-7 cross-platform) |

**P2 production 파일 (DeveloperAgent)**

| 파일 경로 | Change Plan 매핑 |
|-----------|-----------------|
| `src/mctrader_web/api/admin/__init__.py` *(modified)* | §4 P2 — get_admin_status_router mount under /admin/status prefix |
| `src/mctrader_web/api/admin/status.py` *(modified)* | §4 P2 — GET /admin/status/engines 실제 구현 (5 engine class, ADR-014 data plane) |
| `src/mctrader_web/dashboard/admin_status_fetcher.py` | §3.1 status_adapter 재사용 — httpx fetcher wrapper for admin overview |
| `src/mctrader_web/dashboard/pages/10_admin_overview.py` *(modified)* | §7.A P2 — 5 engine status display + time.sleep(5)+st.rerun() polling |

**P2 test 파일 (QADeveloperAgent)**

| 파일 경로 | Test Contract 매핑 |
|-----------|--------------------|
| `tests/api/test_admin_status.py` (20 test) | §8.2 P2 — auth 401, schema, EC-4 fresh/stale/age, EC-7 multi/remove, prefix synthesis |
| `tests/dashboard/test_admin_overview.py` (11 test) | §8.2 P2 — isolated import smoke + fetcher unit (200/non-200/OSError/no-token) |
| `tests/dashboard/test_admin_pages_smoke.py` *(modified)* | §8.4 P2 — stub 확장 (st.rerun/columns/expander + fetcher stub + sleep stub) |

**P3 production 파일 (mctrader-engine)**

| 파일 경로 | Change Plan 매핑 |
|-----------|-----------------|
| `src/mctrader_engine/executor/backtest.py` *(modified)* | §6.2 — `run(cancel_token: threading.Event | None = None)` per-bar loop cancel check |
| `src/mctrader_engine/wfo/search/coordinator.py` *(modified)* | §6.2 — `run_search(..., cancel_token=None)` trial loop cancel check |

**P3 test 파일 (mctrader-engine)**

| 파일 경로 | Test Contract 매핑 |
|-----------|--------------------|
| `tests/test_cancel_hook.py` (7 test) | §8.1 P3 — cancel_token compat, pre-set, thread-safe, WFO signature validation |

**P3 production 파일 (mctrader-web)**

| 파일 경로 | Change Plan 매핑 |
|-----------|-----------------|
| `src/mctrader_web/api/admin/control.py` *(P3 실구현)* | §4 P3 — POST 5 verb, Idempotency-Key, SM guard, auth |
| `src/mctrader_web/api/admin/control_adapter.py` *(P3 실구현)* | §7.D hybrid adapter — systemd/subprocess/in-process, PID persistence |
| `src/mctrader_web/api/admin/state_machine.py` *(P3 실구현)* | ADR-015 — validate_transition(), SMViolation, full daemon+oneshot table |
| `src/mctrader_web/api/admin/idempotency.py` *(P3 실구현)* | ADR-016 — idempotency_cache table, 24h dedupe, INSERT OR IGNORE |
| `src/mctrader_web/api/admin/audit_db.py` *(P3 수정)* | ADR-016 — idempotency_cache DDL 주석 |
| `src/mctrader_web/api/admin/__init__.py` *(P3 수정)* | §4 P3 — control router mount |
| `src/mctrader_web/api/admin/status.py` *(P2 boundary 수정)* | P1-1 cancelling state 추가, P1-2 node_id regex 검증 |
| `src/mctrader_web/dashboard/pages/11_admin_control.py` *(P3 실구현)* | §7.A P3 — 5 engine class verb buttons, in-flight indicator |

**P3 test 파일 (QADeveloperAgent, mctrader-web)**

| 파일 경로 | Test Contract 매핑 |
|-----------|--------------------|
| `tests/api/test_admin_control.py` (20 test) | §8.1 P3 — auth, idempotency key format, SM violation 409, daemon/oneshot happy path, dedupe |
| `tests/api/test_admin_idempotency.py` (13 test) | §8.1 P3 — key validation, check/store/cleanup, TTL, INSERT OR IGNORE, 409 cached |
| `tests/api/test_admin_state_machine.py` (39 test) | §8.1 P3 — daemon/oneshot all valid+invalid transitions, market_gw, SMViolation attrs |
| `tests/dashboard/test_admin_control_page.py` (3 test) | §8.4 P3 — page import smoke, ENGINE_DEFS structure, _send_control callable |
| `tests/dashboard/test_admin_pages_smoke.py` *(modified)* | §8.4 P3 — st stub P3 확장 (success/stop/button/session_state/json/spinner) |

## 9. 품질 게이트 이력

### P1 (skeleton) 리뷰 결과 — 2026-05-06

| Lane | 결과 | Iter | Finding |
|------|------|------|---------|
| 설계 리뷰 (DesignReviewPL) | PASS | 2/3 | iter 1 = FIX_REQUIRED (P0×1 + P1×6) → ArchitectPL 회귀 후 PASS |
| 구현 리뷰 (CodeReviewPL) | PASS | 1/3 | 3 non-blocking comment-only finding (mechanical) |
| 구현 테스트 (TestAgent) | PASS | - | 179 passed, p95 2.91ms < 500ms threshold, admin/health 88% coverage |
| 보안 테스트 (SecurityTestPL) | PASS | 1/3 | 0 blocker, 3 informational defer (F-SEC-1 P4 / F-SEC-2 P5 / F-GOV-1 governance) |

### Defer findings (후속 phase 책임)

- **F-SEC-1 (P2-LOW)** — `audit_db.py:25-33` MCTRADER_ADMIN_AUDIT_PATH env path sanitize 누락 (현 P1 dead path) → P4 audit_db write/read 구현 시 resolve()/is_absolute()/suffix whitelist 도입
- **F-SEC-2 (P2-LOW)** — `app.py:55-61` /admin/* 가 root API 와 동일 CORS 정책 → P5 원격 보안에서 별도 origin 화이트리스트
- **F-GOV-1 (P3-INFO)** — mctrader-web repo CodeQL 미설정 + Secret Scanning disabled → governance backlog (P5 진입 전 활성화 권고)

### P2 (status read) 리뷰 결과 — 2026-05-06

| Lane | 결과 | Iter | Finding |
|------|------|------|---------|
| 구현 리뷰 (CodeReviewPL) | PASS | 1/3 | 5 non-blocking (P1-1/P1-2 boundary → P3 처리, P2-1~3 comment-only) |
| 구현 테스트 (TestAgent) | PASS | - | 211/211, status.py 80% / dashboard 78% coverage. perf wrapper 부재로 §8.5 baseline 측정 SKIP |
| 보안 테스트 (SecurityTestPL) | PASS | 1/3 | 0 blocker, 1 advisory non-blocking (status.py:96 OSError path leak, defer P3+ RBAC) |

### Defer findings 누적 (P2 종료 시점)

- **F-SEC-1 (P4)**: audit_db path sanitize
- **F-SEC-2 (P5)**: /admin/* CORS 분리
- **F-GOV-1 (governance)**: mctrader-web CodeQL/Secret Scanning
- **F-PERF-1 (NEW)**: perf wrapper `.claude/_overlay/run-perf.sh` 부재 → §8.5 baseline 측정 미수행, P5 또는 P6 에서 wrapper 박제 필요
- **F-SEC-P2-A (NEW, advisory)**: status.py:96 OSError path leak → P3+ RBAC viewer role 도입 시 path-stripped error message

### P3 (control write) 구현 진행 — 2026-05-06

| 항목 | 결과 |
|------|------|
| mctrader-engine cancel hook | PR [#36](https://github.com/mclayer/mctrader-engine/pull/36) MERGED |
| mctrader-web P3 PR | PR [#18](https://github.com/mclayer/mctrader-web/pull/18) — review chain 대기 중 |
| pytest (P3 신규 75개) | 286/286 passed (regression 0) |

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|
| 1 | 2026-05-06 | 설계-리뷰 | engine_id mapping invariant + ADR convention | mapping 모호 + draft 흔적 + DDL self-contradict + degraded SM gap + observability metric 미명시 | ADR-014/015/016 + engine-id-naming.v1.md + Change Plan §8.5 정정 후 재리뷰 | NO |

## 11. 회고

*(PMOAgent 작성 예정 — Story 완료 시)*
