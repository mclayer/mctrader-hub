# EPIC-RESULTS-MCT-97 — Admin Engine Control Panel

**Epic**: MCT-97 — Admin Engine Control Panel (5-engine inspect+control, remote-ready)  
**기간**: 2026-05-06 (single day, 6 phase)  
**Story Issue**: [mctrader-hub#110](https://github.com/mclayer/mctrader-hub/issues/110)  
**Status**: COMPLETED

---

## 1. 목적

mctrader 5 engine (collector / paper_runner / backtest / wfo / market_gw)을 점검하고 제어할 수 있는 admin panel 구현. localhost 및 원격(Tailscale/SSH) 환경 모두 지원. RBAC + audit log + hash chain tamper detection + cross-platform (Windows dev / Linux prod) 지원.

---

## 2. 산출 PR 목록

| # | Repo | PR | Phase | 내용 |
|---|------|----|-------|------|
| 1 | mctrader-web | [#16](https://github.com/mclayer/mctrader-web/pull/16) | P1 | Admin section skeleton (18 file, 25 test) |
| 2 | mctrader-web | [#17](https://github.com/mclayer/mctrader-web/pull/17) | P2 | Status read — 5 engine + heartbeat polling (7 file, +6 test) |
| 3 | mctrader-engine | [#36](https://github.com/mclayer/mctrader-engine/pull/36) | P3 | Cooperative cancel hook (BacktestExecutor + WFO) |
| 4 | mctrader-web | [#18](https://github.com/mclayer/mctrader-web/pull/18) | P3 | Control write — daemon/one-shot + idempotency + SM (13 prod + 4 test, 75 신규 test) |
| 5 | mctrader-web | [#19](https://github.com/mclayer/mctrader-web/pull/19) | P4 | RBAC + audit — MultiTokenAuth + hash chain + verify CLI (15 file, 74 신규 test) |
| 6 | mctrader-web | [#20](https://github.com/mclayer/mctrader-web/pull/20) | P5 | Remote security — TLS config + rate limit + CORS split (9 file, 54 신규 test) |
| 7 | mctrader-web | [#21](https://github.com/mclayer/mctrader-web/pull/21) | P6 | E2E + cross-platform + retention cron + perf + docs (14 file, 23 신규 E2E test) |

**합계**: 7 PR (6 web + 1 engine), ~79 file 변경, 437 pytest passed

---

## 3. 6 Phase Milestone

| Phase | 목표 | 완료 | 핵심 산출 |
|-------|------|------|-----------|
| P1 | Skeleton | 2026-05-06 | `api/admin/` 10 module + 4 dashboard page + data/ + gitignore |
| P2 | Status read | 2026-05-06 | `/admin/status/engines` 5 engine SM state + heartbeat age + 5s polling |
| P3 | Control write | 2026-05-06 | 5 verb + Idempotency-Key + SM guard + cooperative cancel hook (engine PR) |
| P4 | RBAC + audit | 2026-05-06 | MultiTokenAuth 3 role + audit_log hash chain + verify CLI + 360 test |
| P5 | Remote security | 2026-05-06 | TLS validate + rate limit 30/300/60 + CORS 분리 + Tailscale docs |
| P6 | E2E + xplat | 2026-05-06 | UC-1~UC-8 E2E + Windows/Linux smoke + retention cron + perf wrapper + 3 docs |

---

## 4. Architecture 결정 (ADR)

| ADR | 제목 | 결정 |
|-----|------|------|
| ADR-014 | Control plane vs data plane separation | control write / status read 독립 — data plane 장애 → control plane 무영향 |
| ADR-015 | Engine state machine (daemon + one-shot) | daemon 6 state, one-shot 5 state, valid transition table |
| ADR-016 | Audit log append-only + hash chain | SQLite WAL + HMAC-SHA256 hash chain + 일일 backup + verify CLI |

---

## 5. Defer Findings 처리 결과

| Finding | defer 단계 | 처리 단계 | 처리 방법 |
|---------|-----------|---------|-----------|
| F-SEC-1 | P1 | P4 | `_sanitize_audit_path()` — resolve()+absolute+.sqlite suffix |
| F-SEC-2 | P1 | P5 | `_AdminCORSMiddleware` — /admin/* CORS 독립 origin |
| F-SEC-P2-A | P2 | P4 | status.py OSError → `type(exc).__name__` (path 미노출) |
| F-PERF-1 | P2 | P6 | `scripts/run_perf.py` 박제 (httpx, p95<500ms baseline) |
| F-GOV-1 | P1 | governance backlog | CodeQL/Secret Scanning — 별도 Story 후보 |

---

## 6. Cross-repo Coordination

- **mctrader-engine#36** (P3): cooperative cancel hook 도입
  - `BacktestExecutor.run(cancel_token=None)` per-bar loop cancel check
  - `WFO coordinator.run_search(cancel_token=None)` trial cancel check
  - 기존 호출자 영향 0 (default None)
- **mctrader-web#16~21**: 6 phase PR, 모두 admin merge (CI 비용 한계)
- **mctrader-hub**: ADR-014/015/016 + engine-id-naming.v1.md (P1 설계 박제)

---

## 7. Story Acceptance Verdict

| AC | 항목 | 결과 |
|----|------|------|
| AC-1 | 5 engine × SM state + heartbeat age + history | PASS |
| AC-2 | daemon/one-shot verb + Idempotency-Key + SM guard | PASS |
| AC-3 | viewer/operator/admin 3 role + DB-backed revocable token | PASS |
| AC-4 | hash chain audit log + verify CLI + daily backup | PASS |
| AC-5 | TLS + rate limit + CORS + Tailscale/SSH docs | PASS |
| AC-6 | codeforge phase-gate-mergeable 채널 준수 | PASS |
| AC-7 | Windows dev (_USE_SUBPROCESS=True) + Linux prod smoke | PASS |

**7/7 AC PASS — Story MCT-97 COMPLETE**

---

## 8. codeforge Upstream Finding (PMOAgent 후속 등록 대상)

| # | Finding | 영향 |
|---|---------|------|
| CF-1 | CI 라운드 빈번 (ruff/pyright fix 반복) | dev workflow 비용 |
| CF-2 | phase-gate-mergeable CI Actions 비용 소진 | GitHub Actions quota |
| CF-3 | component label gap (cancel hook cross-repo PR) | PR labeling automation |
| CF-4 | enabledPlugins desync (codeforge debut CFP-96) | plugin config 정합 |

---

## 9. 다음 Epic 후보

| 후보 | 내용 | 선행 조건 |
|------|------|-----------|
| F-GOV-1 governance Story | CodeQL + Secret Scanning mctrader-web 활성화 | 없음 |
| codeforge upstream finding | CF-1~CF-4 plugin-codeforge issue 등록 | 없음 |
| live executor (MCT-12) | live trading executor 통합 | CFP-60 dependency 확인 |

---

*Story MCT-97 종료 — 2026-05-06*
