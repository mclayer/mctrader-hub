# MCT-97 Engine Control Panel — Design Spec (codeforge-only, decider-free)

> **자율 결정 모드** — codeforge-requirements lane (PL + Domain + Analyst + Researcher) 내에서 모든 architectural 결정 마무리. codex / Sonnet decider alternatives picking 없음.
> **Source**: codeforge-requirements:RequirementsPLAgent v2, 2026-05-06
> **Channel**: codeforge-only (사용자 directive)

## §0. 메타

| 항목 | 값 |
|------|-----|
| Story key (잠정) | **MCT-97** |
| Title | Admin Engine Control Panel — 5-engine inspect+control, remote-ready |
| 작업 채널 | codeforge 의무 (story-init → phase-gate-mergeable) |
| 사전 정렬 | D1=admin section in mctrader-web / D2=α (collector + paper + backtest + WFO + market-gw) |
| Out (별도 Story) | live executor (MCT-12 / CFP-60) |
| 본 lane 자율 결정 | A-H 모두 본 spec 에서 박제 |

## §1. Background (사용자 원문 + 컨텍스트)

> "web의 요구조건이다. mctrader를 위해 작업하는 engine들을 점검하고 제어할 수 있는 panel을 만들어라. 현재는 localhost에 존재하지만 원격으로 작업될 수도 있기 때문에 이를 고려하라. codeforge를 통해 반드시 작업하라."

- mctrader 6-repo 중 mctrader-web 이 governance UI host. 기존 dashboard (`00_status` / `01_paper_panel` / `02_backtest_panel` / `03_wfo_panel`) + FastAPI lifecycle (`api/lifecycle.py`, `backtest_lifecycle.py`, `wfo_lifecycle.py`) 자산 존재.
- collector HA (MCT-89~96) 가 systemd unit + heartbeat sink 채택, ops scripts 완료.
- codeforge consumer debut (CFP-96) 직후 — 7 workflow (story-init / story-section-1-immutable / subissue-from-impl-manifest / fix-ledger-sync / phase-gate-mergeable / phase-label-invariant / story-section-schema) 가용.

## §2. Scope (in-scope, α 5 engine)

| Engine class | Repo | Lifecycle | Control verb |
|--------------|------|-----------|--------------|
| collector (HA) | mctrader-data | daemon (systemd, multi-node) | start / stop / restart (per node_id) |
| paper runner | mctrader-engine | long-running daemon (1 instance per strategy) | start / stop / restart |
| backtest executor | mctrader-engine | one-shot job | trigger / cancel |
| WFO executor | mctrader-engine | long-running multi-fold job | trigger / cancel |
| market gateway | mctrader-market(-bithumb) | library (paper_runner 내장 가정 — §AS-4) → 별도 process 면 daemon 추가 | (library) status only / (process) start/stop/restart |

신규 admin section in `mctrader-web/src/mctrader_web/dashboard/` + admin API in `mctrader-web/src/mctrader_web/api/admin/`.

## §3. Out of Scope (명시)

- live executor (MCT-12 / CFP-60 dependency 별도 Story)
- multi-tenant / 외주 협업자 (RBAC schema 만 multi-user, 구현 single-user)
- cloud (AWS/GCP) 배포
- alerting routing (PagerDuty/Slack) — read-only display 만
- panel 자체의 reverse tunnel/VPN 운영 — admin 수작업 (Tailscale 권장 docs)

## §4. 도메인 invariant (Domain 관점, 신규 ADR 후보)

### §4.1 control plane vs data plane 분리 (ADR-001-NEW)

- control plane: `/admin/control/*` (start/stop/restart/trigger/cancel)
- data plane: heartbeat sink + market quote/trade/OMS (read-only `/admin/status/*`)
- 이유: data plane 장애가 control 으로 전파 차단 (admin 이 복구 명령 가능 보장)

### §4.2 engine state machine (ADR-002-NEW)

```
daemon: [stopped] -start-> [starting] -ready-> [running] -stop-> [stopping] -> [stopped]
                                       |
                                       +-crash-> [crashed] -restart-> [starting]
                                       +-heartbeat stale > N-> [degraded]

one-shot: [queued] -> [running] -> [completed | failed | cancelled]
```

idempotent guard: `[running]` 중 start 거부 (409), `[stopping]` 중 신규 start 거부.

### §4.3 audit log immutability (ADR-003-NEW)

append-only, no UPDATE/DELETE. row schema: `(ts, actor, role, engine_class, engine_id, action, params_hash, request_id, outcome, latency_ms, source_ip, prev_hash, row_hash)`. hash chain 으로 tamper detection.

### §4.4 engine_id naming SSOT

heartbeat schema (`docs/domain-knowledge/contracts/heartbeat-schema.v1.md`) 의 `node_id` 를 control plane 의 `engine_id` 와 unify. 신규 `docs/domain-knowledge/contracts/engine-id-naming.v1.md` 작성 (Researcher 권한).

## §5. Acceptance Criteria

### §5.1 점검 (read) — AC-1

- [ ] 5 engine class × N instance 의 현재 SM state (§4.2) panel 표시
- [ ] heartbeat age, last error, recent restart count, uptime 표시
- [ ] one-shot job (backtest/WFO) 최근 N건 history (queued/running/completed/cancelled/failed)
- [ ] refresh 주기 ≤ 5 sec (§E 결정 기반)
- [ ] read 경로는 control 장애와 독립 (data plane)

### §5.2 제어 (write) — AC-2

- [ ] daemon: start/stop/restart 3 verb, one-shot: trigger/cancel 2 verb
- [ ] 모든 control 은 `Idempotency-Key` header (Stripe pattern), 24h dedupe
- [ ] SM 위반 transition → 409 Conflict + audit log 기록
- [ ] graceful stop timeout (default 30s) 후 SIGKILL fallback (daemon)
- [ ] one-shot cancel 은 cooperative signal (engine-side hook 필요)

### §5.3 RBAC — AC-3

- [ ] role 3개: `viewer` (read) / `operator` (control) / `admin` (RBAC 변경 + audit query)
- [ ] solo dev 본인은 admin role single user 로 시작
- [ ] schema 는 multi-user (token table with role column), 구현은 1 user
- [ ] 모든 `/admin/*` route 는 token 필수, viewer 도 별도 token

### §5.4 Audit log — AC-4

- [ ] 모든 control 명령은 §4.3 schema row append
- [ ] panel 에서 query (filter: actor / engine / time range / outcome)
- [ ] DB 권한 + app guard 양면으로 UPDATE/DELETE 차단
- [ ] hash chain verification CLI 제공

### §5.5 원격 보안 — AC-5

- [ ] panel 은 TLS + token-bearer 만 책임 (transport 외부 위임)
- [ ] localhost binding 외 접속 시 TLS 필수 (self-signed dev OK)
- [ ] rate limit: control endpoint 분당 30회 / status 분당 300회 (per token)
- [ ] CSRF: token-bearer scheme (cookie 미사용) 으로 mitigation
- [ ] 외부망 직접 노출 금지 — Tailscale/SSH tunnel 권장 (docs)

### §5.6 codeforge 채널 — AC-6

- [ ] Story `docs/stories/MCT-97.md` 는 story-init workflow 로 생성
- [ ] §1 immutable (story-section-1-immutable workflow 가 보장)
- [ ] PR 은 phase-gate-mergeable workflow 통과
- [ ] phase 라벨 invariant 준수 (phase-label-invariant)
- [ ] FIX 발생 시 fix-ledger-sync workflow 로 §10 동기화

### §5.7 cross-platform — AC-7

- [ ] Windows local dev: panel UI + API 동작 (control 은 localhost in-process)
- [ ] Linux prod: panel + systemd-managed daemon control
- [ ] OS 분기는 control adapter 한 군데 (§D 결정)

## §6. Edge Cases

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
| EC-9 | systemd 미설치 (Windows dev) | §D adapter 가 in-process subprocess fallback |
| EC-10 | token 만료 중 long-running poll | refresh token + UI re-auth prompt |
| EC-11 | hash chain tamper detect | 검증 실패 시 panel 경고 + 운영자 manual review trigger |

## §7. 암묵 가정 + Open Questions

### §7.1 자율 결정 모드 → PL 가정으로 확정

| # | 가정 | 확정 근거 |
|---|------|-----------|
| AS-1 | "원격 운영" = solo dev 본인 외부 노트북 LAN/VPN 접속 (cloud 배포 아님) | 보수적 가정, cloud 별도 Story |
| AS-2 | admin = solo dev 본인 single user, schema 만 multi-user 준비 | mctrader 프로젝트 컨텍스트 |
| AS-5 | audit log SQLite 단일 파일 (외부 SIEM 미연동) | solo dev 환경 적정선 |
| AS-6 | reverse tunnel 은 admin 수작업 (panel 외부) | panel 책임 경계 명확화 |

### §7.2 Architect lane 으로 위임 (코드 grep 으로 해소 가능)

| # | 항목 | Architect 액션 |
|---|------|----------------|
| AS-4 | market gateway = 별도 process? library? | mctrader-market(-bithumb) `src/` grep |

→ **본 spec 은 library 가정 (paper_runner 내장)** 으로 진행, Architect 가 process 발견 시 phase 추가.

## §8. Decisions (A-H 자율 결정 박제)

### §A. Streamlit admin section 구현 패턴 → **(a1) numeric prefix 확장**

`10_admin_overview.py` / `11_admin_control.py` / `12_admin_audit.py` / `13_admin_rbac.py`. 기존 `dashboard/` 의 numeric prefix 규칙 (00-03) 연장.

**근거**: 학습 비용 0, Streamlit native multipage, prefix gap 으로 admin 영역 시각 분리.

**Reject**: (a2) `st.navigation` Streamlit ≥1.36 lock-in + 4 page 마이그레이션. (a3) 별도 sub-app 두 entry point → 운영 부담.

### §B. 인증/RBAC 모델 → **(b1) Bearer token + role claim (signed)**

`Authorization: Bearer <token>` header. token 은 SQLite `tokens` table row 참조 (role column). signed (HMAC-SHA256, secret in env). 만료/취소 가능.

**선행**: Architect 가 `mctrader-web/src/mctrader_web/api/auth.py` 현 scheme grep 후 호환 layer.

**근거**: viewer/operator/admin 3 role claim 1개 충분, DB-backed revoke, signed 위변조 차단, FastAPI dependency injection 호환.

**Reject**: (b2) role 별 token revoke 복잡. (b3) OIDC overkill. (b4) mTLS hybrid Tailscale 책임 중복 + Windows cert 부담.

### §C. 원격 transport 모델 → **(c1) FastAPI `/admin/*` 단일 control plane**

mctrader-web 가 모든 engine 의 단일 control gateway. engine repo 추가 endpoint 없음. mctrader-web 내부 §D 메커니즘으로 위임.

**근거**: single TLS endpoint → 인증/audit/rate-limit 한 곳, engine repo 에 web 의존성 0, 기존 lifecycle 자산 재사용, cross-repo PR 최소화.

**Reject**: (c2) engine 자체 endpoint 인증/audit 5중. (c3) hybrid 의사결정 분산.

### §D. Engine process control 메커니즘 → **(d4) hybrid adapter pattern**

`mctrader-web/src/mctrader_web/api/admin/control_adapter.py` 단일 abstraction.

| Engine | Linux prod | Windows dev |
|--------|-----------|-------------|
| collector (HA) | systemd (`systemctl --user`) | subprocess (in-process tracking) |
| paper runner | systemd | subprocess |
| backtest | in-process Python | 동일 |
| WFO | in-process Python | 동일 |
| market gateway | library status read only | 동일 |

**근거**: collector 가 이미 systemd (MCT-94), backtest/WFO in-process 자연, adapter 한 군데 분기로 §AC-7 충족, 의존성 0.

**Reject**: (d1) systemd 통일 backtest unit 부담 + Windows 불가. (d2) HTTP 통일 §C 중복. (d3) supervisord Windows 미지원.

### §E. 실시간 metric/event 채널 → **(e1) polling 5s + (e4) heartbeat sink 재활용**

Streamlit `time.sleep` + `st.rerun` polling 5초. underlying data 는 collector heartbeat sink + status_adapter 재활용.

**근거**: Streamlit SSE/WebSocket native 약함, 5s latency 점검 panel 충족 (실시간 trading UI 아님), heartbeat sink 1초 interval 활용, Tailscale 호환 검증 부담 회피.

**Reject**: (e2) SSE / (e3) WebSocket Streamlit custom component 부담.

control 응답 은 polling 과 별개로 즉시 동기 응답 (POST → 200/409).

### §F. Audit log scheme → **(f2) SQLite (single file, WAL, hash chain)**

`mctrader-web/data/admin_audit.sqlite` (WAL mode). schema §4.3. hash chain (`prev_hash` + `row_hash`) tamper detection. 일일 백업 cron 권장.

**근거**: 단일 파일 backup 단순, WAL concurrent read 중 write, hash chain forensic, mctrader-engine event_store 와 책임 경계 명확.

**Reject**: (f1) JSONL query 부담. (f3) event_store 통합 trading domain pollution. (f4) 이중 sync 복잡.

### §G. Story 분할 → **(g1) 단일 MCT-97 + 6 phase**

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

### §H. Cross-repo 영향 + 순서 → **mctrader-web 단일 repo 작업**

§C + §D 결정으로 mctrader-web 외 PR **0건** 목표.

**예외**:
- mctrader-data: heartbeat schema docs 정합 만 (mctrader-hub 박제, mctrader-data 코드 변경 0)
- mctrader-engine: cooperative cancel hook 부재 시 P3 minimal hook PR 1건
- mctrader-market(-bithumb): §AS-4 결과 후 process 면 control endpoint PR 1건

**PR 순서**:
1. mctrader-hub: ADR-001/002/003 + engine-id-naming.v1.md (P1 시작 전)
2. mctrader-web: P1 → P6 순차 (codeforge phase-gate-mergeable green 유지)
3. (조건부) mctrader-engine cancel hook PR — P3 진입 직전
4. (조건부) mctrader-market process control PR — §AS-4 결과 후

**근거**: single-repo CI green 관리 단순, codeforge phase-gate-mergeable 가 phase 별 PR merge 보장.

## §9. Plan (Phase 요약 — DeveloperPL 입력)

| Phase | Goal | Key files | Exit criterion |
|-------|------|-----------|----------------|
| P1 | skeleton | `dashboard/10-13_admin_*.py` + `api/admin/__init__.py` + auth.py 확장 | placeholder page render + `/admin/health` 200 + token bearer 인증 |
| P2 | status read | `api/admin/status.py` + heartbeat sink reuse | 5 engine state 표시 + 5s polling |
| P3 | control write | `api/admin/control.py` + `control_adapter.py` (§D) | start/stop/restart/trigger/cancel + idempotent + SM guard |
| P4 | RBAC + audit | `api/admin/auth_rbac.py` + `audit.py` + SQLite migration | 3 role + audit append + hash chain verify CLI |
| P5 | remote security | TLS config + rate limit middleware + Tailscale docs | TLS green + rate limit test pass |
| P6 | E2E + xplat | smoke tests Win/Linux + retention cron | 양 OS green + audit backup 검증 |

## §10. Risk + Mitigation

| Risk | Mitigation |
|------|-----------|
| §AS-4 (market gateway 구조) 미확인 | P1 진입 전 Architect grep 1회, library 면 spec 그대로, process 면 P3 scope 추가 |
| systemd 권한 (sudo 없이 user unit) | `systemctl --user` + lingering enable docs |
| Windows dev 에서 systemd 부재 | §D adapter 분기로 subprocess fallback |
| Tailscale 미설치 사용자 | docs 에 SSH local forward fallback 명시 |
| audit hash chain 검증 비용 (DB 큼) | 검증 CLI 는 on-demand, panel runtime 검증 안 함 |
| codeforge workflow 신규 (debut) bug | 발견 시 plugin-codeforge upstream issue (consumer workaround 금지 — 사용자 directive) |

## §11. Open Questions (Architect 진입 전 grep 으로 해소)

| # | Question | Owner |
|---|----------|-------|
| Q1 | `mctrader-web/api/auth.py` 현 scheme? (§B 호환 layer 필요?) | Architect grep |
| Q2 | mctrader-market(-bithumb) 별도 process 유무? (§AS-4) | Architect grep |
| Q3 | mctrader-engine paper_runner / BacktestExecutor / WFO cooperative cancel hook 존재? | Architect grep |
| Q4 | mctrader-web `data/` 디렉토리 convention? (audit SQLite 위치) | Architect grep |

→ 4건 모두 코드 grep 으로 해소, 사용자 응답 불필요.

## §12. 도메인 ADR 박제 의무 (3건)

| ADR | 제목 | 위치 |
|-----|------|------|
| ADR-NEW-1 | Control plane vs data plane separation | `mctrader-hub/docs/adr/ADR-NNN-control-plane-separation.md` |
| ADR-NEW-2 | Engine state machine (daemon + one-shot) | `mctrader-hub/docs/adr/ADR-NNN-engine-state-machine.md` |
| ADR-NEW-3 | Audit log append-only + hash chain | `mctrader-hub/docs/adr/ADR-NNN-audit-log-immutability.md` |

번호는 PMOAgent 가 `docs/adr/` 최신 +1 부터 발번. P1 시작 전 박제.

신규 domain-knowledge:
- `mctrader-hub/docs/domain-knowledge/contracts/engine-id-naming.v1.md` (heartbeat node_id ↔ control engine_id SSOT)

## §13. 다음 단계 (codeforge channel)

1. **사용자 spec review + 승인**
2. **codeforge story-init**: MCT-97 GitHub issue (story form) 생성 → mctrader-hub `docs/stories/MCT-97.md` 자동 박제
3. **codeforge-design 활성화**: ArchitectPLAgent + SecurityArchitectAgent + OperationalRiskArchitectAgent 가용화 → §11 Q1-Q4 grep 해소 + ADR-NEW-1/2/3 박제 + §D adapter 인터페이스 설계
4. **codeforge-review**: 설계 + ADR 검토
5. **codeforge-develop**: §9 phase 분할 실행 (P1 → P6)

## 관련 파일 경로 (absolute)

- Story file (생성 예정): `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-97.md`
- ADR 디렉토리: `c:\workspace\mclayer\mctrader-hub\docs\adr\`
- domain-knowledge 디렉토리: `c:\workspace\mclayer\mctrader-hub\docs\domain-knowledge\contracts\`
- 기존 lifecycle: `c:\workspace\mclayer\mctrader-web\src\mctrader_web\api\lifecycle.py`, `backtest_lifecycle.py`, `wfo_lifecycle.py`
- 기존 auth (Q1 grep 대상): `c:\workspace\mclayer\mctrader-web\src\mctrader_web\api\auth.py`
- 기존 dashboard: `c:\workspace\mclayer\mctrader-web\src\mctrader_web\dashboard\` (00-03 *.py)
- 신규 admin section: `c:\workspace\mclayer\mctrader-web\src\mctrader_web\dashboard\1{0..3}_admin_*.py` + `api\admin\`
- heartbeat schema (SSOT): `c:\workspace\mclayer\mctrader-hub\docs\domain-knowledge\contracts\heartbeat-schema.v1.md`
- codeforge plugin: `c:\workspace\mclayer\plugin-codeforge\` (CFP-96 자산 7 workflow)
