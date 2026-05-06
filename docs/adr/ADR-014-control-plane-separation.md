---
adr_id: ADR-014
title: Control plane vs data plane separation for Admin Engine Control Panel
status: Accepted
date: 2026-05-06
related_story: MCT-97
category: web
supersedes: []
amends: []
---

# ADR-014: Control plane vs data plane separation for Admin Engine Control Panel

## Status

Accepted — 2026-05-06. MCT-97 design phase.

- Authors: ArchitectAgent (chief) + SecurityArchitectAgent (deputy)
- Reviewers: ArchitectPLAgent

## Context

MCT-97 은 5 engine class (collector / paper runner / backtest executor / WFO executor / market gateway) 의 점검 + 제어 admin panel 을 도입한다. 기존 mctrader-web 은 `api/lifecycle.py` 등 lifecycle 로직과 heartbeat sink 의 read 경로를 동일 FastAPI 위에서 운용한다. 별도 plane 분리 없이 `/admin/*` 을 단일 router 로 추가하면 다음 위험이 발생:

- collector heartbeat sink 가 stall 또는 데이터 corruption 상태에 있을 때 동일 인증 의존성 / rate-limit / lock 을 통해 control 명령이 차단될 수 있음
- read 경로의 burst (Streamlit polling 5s × 5 engine × N instance) 가 control endpoint 의 latency 를 오염
- 보안 위협 모델: read 위주 token (viewer) 이 control endpoint 의 trust boundary 를 우회할 가능성
- audit log 의 책임 경계 불명확 — read 도 audit 에 포함되면 audit 볼륨이 control 비율을 압도

## Decision

`/admin/control/*` (write) 와 `/admin/status/*` (read) 를 **plane 으로 분리** 한다. 코드 / 인증 / rate-limit / audit / SM transition 모두 plane 별로 독립.

### Plane 정의

| 항목 | Control plane | Data plane |
|------|---------------|------------|
| Path prefix | `/admin/control/*` | `/admin/status/*` |
| HTTP verb | POST 만 (idempotent guard 포함) | GET 만 |
| Required role | `operator` 또는 `admin` | `viewer` 이상 (3 role 모두) |
| Idempotency-Key | 필수 (Stripe pattern, 24h dedupe) | 불필요 |
| Rate limit (per token) | 분당 30 회 | 분당 300 회 |
| Audit log | 모든 요청 append (성공/실패/no-op) | 기록 없음 (overhead 회피) |
| 데이터 source | `control_adapter` (subprocess / systemd / in-process) | heartbeat sink + DB (`status_adapter` 재사용) |
| 장애 격리 | data plane 장애가 control plane 으로 전파 금지 | 독립 장애 (control 지속 가능) |

### Trust boundary (SecurityArchitect 변호)

```
   [Streamlit admin UI]
         |
         | Bearer token (HMAC signed) + Idempotency-Key
         v
   [FastAPI /admin/*]
    +------ /admin/control/* -- ROLE: operator|admin -- audit append
    |                          |
    |                          v
    |                       control_adapter (§7.D hybrid: systemd | subprocess | in-process)
    |
    +------ /admin/status/*  -- ROLE: viewer|operator|admin -- no audit
                               |
                               v
                            status_adapter -> heartbeat sink (read-only) + audit DB query
```

trust boundary 위반 시:
- viewer token 이 `/admin/control/*` 호출 → 403 Forbidden + 보안 audit row (`outcome=rbac_reject`)
- 어떤 role 이든 token 무효 → 401 + audit row 없음 (token-pre 실패)

### 장애 격리 invariant

1. **read-side stall (heartbeat sink loss / SQLite WAL contention)** 가 control plane 의 응답 시간 / 가용성에 영향 없음.
2. **write-side blockage (subprocess hang / systemd unresponsive)** 가 status panel 표시에 영향 없음 (last-known cached state + "stale since X").
3. 두 plane 은 **별개 FastAPI router** 로 분리하되 동일 process 내 mount (단일 TLS endpoint 책임 §7.C 유지). 다중 process 분리는 solo dev scope 외 (CFP 추가 시 재고).

## Alternatives considered

| 대안 | Reject 사유 |
|------|-------------|
| (1) 단일 `/admin/*` router (plane 미분리) | 위 4 위험 그대로, 본 ADR 의도 회피 |
| (2) 별도 process (control daemon + status server) | solo dev IPC 부담, single-active-session 보장 복잡, 디버깅 비용 증가 |
| (3) GraphQL 단일 endpoint | mctrader-web 의 FastAPI-only stack 과 mismatch, role-별 schema 분리 어려움 |

## Consequences

- mctrader-web `api/admin/control.py` + `api/admin/status.py` 별개 module
- 단일 FastAPI app 내 `/admin/control` + `/admin/status` 두 sub-router mount
- audit log append 는 control-side decorator (`@audit_emit`) 만, status-side 미적용
- rate limit middleware 가 path prefix 로 bucket 분리

## Follow-up impact

- ADR-015 (state machine) 의 transition 시점 = control plane 진입 직후
- ADR-016 (audit hash chain) 의 row 발생 source = control plane only
- Phase 3 (control write) 는 control plane 만 활성, Phase 2 (status read) 는 data plane 만 활성 — phase-gate 분리 자연
