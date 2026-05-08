# EPIC-RESULTS-MCT-98 — mctrader Docker-first Migration

**Epic**: MCT-98 — mctrader Docker-first Migration (6-repo, 6-phase)
**기간**: 2026-05-07 → 2026-05-08 (2 calendar day)
**Story Issue**: [mctrader-hub#120](https://github.com/mclayer/mctrader-hub/issues/120)
**Status**: COMPLETED
**Trigger**: codeforge ADR-033 (CFP-128 Accepted 2026-05-07) — InfraEngineerAgent default = Docker-first, mctrader 6-repo 의무 follow-on Epic

---

## 1. 목적

codeforge plugin 의 ADR-033 Accepted 후 mctrader 6-repo 가 Docker-first migration 을 follow-on Epic 의무로 받음. 본 Epic 는:

- mctrader-data Pilot 박제 (Phase 1) → 5 sister rollout reference 패턴 확립
- deployable trio (data, engine, web) Docker artifact + healthcheck + named volume DR
- library quartet (market, bithumb, hub) `infra_strategy: none` declarative governance
- ADR-009 §D12 (Docker-first persistence: named volume + forward-only + DR backup) 박제 → sister rollout 의 reference 의무 확정
- ADR-015 cross-ref Docker SM mapping anchor (Phase 3)
- ADR-016 §A1-A4 hash chain integrity-aware DR amendment (Phase 4)
- D13 fcntl.flock cross-container mutex 신규 pattern (Phase 3, ADR formalization F9 carry-over)

---

## 2. 산출 PR 목록

| # | Repo | PR | Phase | merged at | 핵심 |
|---|------|----|-------|-----------|------|
| 1 | mctrader-hub | [#119](https://github.com/mclayer/mctrader-hub/pull/119) | P1 | 2026-05-07T07:54:10Z | Pilot spec + plan + Amendment 1 (HealthServer 채택) |
| 2 | mctrader-data | [#11](https://github.com/mclayer/mctrader-data/pull/11) | P1 | 2026-05-07 | Dockerfile + compose + HealthServer + 8 commit 0.8.0→0.9.0 |
| 3 | mctrader-hub | [#122](https://github.com/mclayer/mctrader-hub/pull/122) | P2 | 2026-05-08T00:49:04Z | Epic+Pilot Story retroactive + ADR-009 §D12 + Bithumb#4 close |
| 4 | mctrader-hub | [#137](https://github.com/mclayer/mctrader-hub/pull/137) | P5 | 2026-05-08T01:58:58Z | Phase 5 anchor — hub project.yaml + Story + plan |
| 5 | mctrader-market | [#2](https://github.com/mclayer/mctrader-market/pull/2) | P5 | 2026-05-08 | project.yaml `infra_strategy: none` |
| 6 | mctrader-market-bithumb | [#5](https://github.com/mclayer/mctrader-market-bithumb/pull/5) | P5 | 2026-05-08 | project.yaml `infra_strategy: none` |
| 7 | mctrader-hub | [#136](https://github.com/mclayer/mctrader-hub/pull/136) | P4 | 2026-05-08T01:59:25Z | Phase 4 mctrader-web spec + plan + Story scaffold + ADR-016 amendment |
| 8 | mctrader-hub | [#135](https://github.com/mclayer/mctrader-hub/pull/135) | P3 | 2026-05-08T02:33:04Z | Phase 3 mctrader-engine spec + plan + Story + ADR-015 cross-ref |
| 9 | mctrader-engine | [#37](https://github.com/mclayer/mctrader-engine/pull/37) | P3 | 2026-05-08 | Dockerfile + 4 named volume + paper/engine 2-service + D13 fcntl.flock + 10 commit 0.29.0→0.30.0 |
| 10 | mctrader-web | [#22](https://github.com/mclayer/mctrader-web/pull/22) | P4 | 2026-05-08T07:13:11Z | 2-service compose + ADR-016 amendment + D6 TLS exempt + D8 cross-stack RO + 15 commit (squash a0ac2ce) 0.13.0→0.14.0 |
| 11 | mctrader-hub | [#141](https://github.com/mclayer/mctrader-hub/pull/141) | P4 | 2026-05-08T07:19:28Z | Phase 4 Story close — §8.5 Impl + §9 Evidence + §11 회고 + Epic body Phase 4 status DONE |
| 12 | mctrader-hub | (this PR) | **P6** | 2026-05-08 | **EPIC-RESULTS-MCT-98 + Story §8.6/§11 + Closes #120** |

**합계**: 12 PR (mctrader-hub 7 + mctrader-data 1 + mctrader-engine 1 + mctrader-web 1 + mctrader-market 1 + mctrader-market-bithumb 1)

---

## 3. 6 Phase Milestone

| Phase | Story | Issue | 완료일 | 핵심 산출 |
|-------|-------|-------|--------|-----------|
| 1 Pilot (data) | MCT-99 | #121 | 2026-05-07 | Dockerfile + compose + HealthServer + 7 D + ADR-033 §7.4 4항목 박제 |
| 2 Entry/bookkeeping | (Phase 2 of MCT-98) | (in #122) | 2026-05-08 | Epic+Pilot Story retroactive + ADR-009 §D12 amendment + 8 D + Bithumb#4 close |
| 3 Engine sister | MCT-100 | #131 | 2026-05-08 | 13 D (D13 fcntl.flock 신규) + 4 named volume + paper/engine 2-service + ADR-015 cross-ref |
| 4 Web sister | MCT-101 | #132 | 2026-05-08 | 13 D + 2-service compose + ADR-016 §A1-A4 + D6 TLS exempt + D8 cross-stack RO + 5 fix-back |
| 5 Library batch | MCT-102 | #134 | 2026-05-08 | 3 PR joint sweep + `infra_strategy: none` × 3 (market+bithumb+hub) |
| 6 Epic close | (Phase 6 of MCT-98) | (this PR) | 2026-05-08 | EPIC-RESULTS-MCT-98 + 9 D + Story §8.6/§11 fill-in + F6 follow-up issue |

→ Phase 1-6 모두 2 calendar day 안에 완료. Phase 3+4 parallel revision 이 critical path 단축 효과 (≈50% 추정).

---

## 4. Architecture 결정 (ADR amendment + 신규 pattern)

### 4.1 ADR amendment 박제 (3건, all landed)

| ADR | 제목 | 본 Epic 내 amendment | Phase |
|-----|------|---------------------|-------|
| ADR-009 | OHLCV 스키마 + Candle Protocol | §D12 Docker-first persistence — named volume + forward-only invariant + DR backup recipe (PowerShell + bash dual command) | P2 entry |
| ADR-015 | engine state machine | Cross-references 절 — Docker SM mapping anchor (cross-ref to MCT-100) | P3 |
| ADR-016 | Audit log append-only + hash chain | §A1-A4 — Docker volume backup recipe + backup-then-verify + WAL race avoidance + restore safety + NFS/SMB 금지 + storage class preflight | P4 |

### 4.2 신규 pattern (1건, ADR formalization defer)

| Pattern | 발견 phase | 근거 | ADR formalization |
|---|---|---|---|
| **D13 fcntl.flock cross-container mutex** | P3 (engine) | 기존 atomic-write+pid-alive 패턴이 cross-container PID namespace 격리에서 mutex 깨짐 — POSIX OFD-managed mutex 가 kernel 레벨에서 cross-container 동기화 보장 | **F9 carry-over** — 2nd reuse 시점에 ADR formalize (현재 단일 사용처 = engine) |

### 4.3 13 D × 3 phase summary (33 결정 박제)

- Phase 1 Pilot 7 D (D1-D7): 응답 경로 / Epic sequencing / Pilot 후보 / systemd 처리 / Compose surface / Pilot depth / Build target
- Phase 2 entry 8 D (D1-D8): Phase 2 scope / Sequencing / First sister / Bithumb handling / library infra_strategy / ADR-009 amendment 시점 / 등록 mechanic / Epic 명칭
- Phase 3 engine 13 D (D1-D13): Compose surface / HealthServer / Data input mount / Engine output / WFO root / runtime_lock 조정 / mctrader-web 통합 / Image deps / SM↔Docker / Process model / Image scope / DR backup / **D13 runtime_lock impl 교체**
- Phase 4 web 13 D (D1-D13): 2-service compose / sqlite volume / Backup-then-verify / Healthcheck / In-process asyncio / Env override TLS / mctrader-data git+https / External cross-stack RO / Audit retention / Streamlit /_stcore/health / .dockerignore / ADR-016 amendment 단독 / Phase 3 cross-cutting coordination
- Phase 5 library 5 D: Story granularity / PR pattern / Version bump / Codex review depth / Verification
- Phase 6 close 9 D (D1-D9): Document location / Structure / D13 ADR formalization / F1-F8 carry-over / Close mechanic / Findings depth / Phase 6 Story / Metrics depth / F7 live smoke

→ 약 55 design 결정 일괄 Codex 7-area review + Sonnet decider 합성 + 사용자 승인 트라이악 패턴.

---

## 5. Cross-cutting Findings (5 deep dive + carry-over)

### 5.1 F6 collector e2e Linux-only failure (HIGH priority)

**증상**: `tests/api/test_admin_engines_e2e_linux.py::test_linux_systemd_collector_start - assert 500 == 200` Linux 전용 실패. Windows 미발생.

**Origin**: MCT-97 (Admin Engine Control Panel) P6 era pre-existing. Phase 4 시점 책임 0.

**Surfacing trigger**: Phase 4 Codex review fix-back 의 root pyright fix (4 admin fixture `AsyncGenerator[AsyncClient, None]` 정정) 후 노출. 이전에는 pyright type 오류로 가려져 있었음.

**진단 단서**:
- e2e 가 collector subprocess 시작 시 500 응답
- `_USE_SUBPROCESS=True` 모드 의 cross-platform 차이 의심
- mctrader-web PR #22 admin merge 시점 evidence 박제 (commit a0ac2ce, 2026-05-08T07:13:11Z)

**처리**: 본 Epic close 와 동시 mctrader-web 별도 GitHub issue 등록 (priority HIGH, label `inherited-pre-existing`). Story link: §10 다음 Epic 후보.

### 5.2 D13 fcntl.flock cross-container mutex (Phase 3 신규 pattern)

**발견**: Phase 3 engine 의 D6 (runtime_lock 조정) 검토 시. 기존 `~/.mctrader/runtime.lock` 의 atomic-write+pid-alive 패턴이 단일 host 단일 PID-ns 환경에서만 동작. Docker 환경에서 paper / wfo / backtest 가 별도 container 로 분리 시:

- container 별 PID namespace 격리 → 다른 container 의 PID 가 host 기준 alive 인지 알 수 없음
- pid-alive 검증이 false negative 또는 false positive 모두 가능
- mutex invariant 깨짐 — 2 container 가 동시 paper start 가능

**채택 근거**: POSIX `fcntl.flock(LOCK_EX|LOCK_NB)` 가 OFD (Open File Description) 기반 kernel-managed mutex — cross-container 동일 named volume mount 시점 동일 inode 위에서 단일 mutex enforcement 보장. linux kernel 의 file lock 자체가 PID namespace 와 독립.

**검증** (Phase 3 §9.7 박제):
```
Linux Docker container 안에서 cross-OFD test:
  A acquired flock on /tmp/mct100-d13-evidence.lock
  PASS: B got BlockingIOError (mutex enforced)
  A released
  PASS: B acquired after A released
  cleanup OK
```

**Windows 대응**: Windows 는 fcntl 부재 → pid-fallback 채택 (Windows host 단일 PID-ns 환경에 한정 정합).

**ADR formalization**: F9 carry-over. 2nd reuse 시점 (Pilot 외 다른 데몬 mutex 의무 발생 시) 에 ADR formalize. 현재 단일 사용처 (engine) 만 → 일반화 데이터 부족.

### 5.3 Phase 3+4 parallel session race + worktree isolation pattern

**발견**: Phase 3 (engine) 와 Phase 4 (web) parallel session 진행 중 mctrader-hub working dir (`c:\workspace\mclayer\mctrader-hub`) 가 두 session + Phase 5 session 사이 공유되어 git HEAD race 발생.

**구체 증상**:
- Phase 5 의 commit (`2a7ea14`) 가 Phase 4 의 `docs/MCT-101-web-docker` branch 에 contamination
- Phase 3 spec commit 이 Phase 4 branch 로 들어가 cherry-pick + branch reset 으로 복구 의무 (Phase 4 session 박제)

**복구 패턴**:
- cherry-pick `<contaminated commit>` to correct branch
- `git branch -f <wrong branch> <last good commit>` 로 wrong branch reset (non-destructive — commit 자체는 cherry-pick 으로 다른 branch 에 보존)
- worktree 추가 — `git worktree add <path> -b <branch>` 로 별도 working dir 격리

**미래 의무** (memory feedback `parallel_session_branch_race` 박제):
- 동일 repo 의 다중 phase parallel 진행 시 각 session 은 별도 worktree 또는 별도 clone 의무
- Epic body update 는 양쪽 PR merged 후 reconciliation commit 으로 단일 session 이 처리 (Phase 4 가 last merge 책임 수행)

### 5.4 ADR-016 hash chain integrity-aware DR (Phase 4 amendment)

**발견**: Phase 4 spec 작성 시 audit_log 의 hash chain integrity (HMAC-SHA256 chain, ADR-016 P4 era 박제) 와 Docker volume backup 사이 conflict:

- 기본 backup recipe (`docker run --rm -v vol:/data alpine tar czf /backup.tgz /data`) 는 sqlite WAL 활성 상태에서 inconsistent snapshot 가능 → hash chain corruption 위험
- audit_log 는 retention 의 의미가 통상 backup 과 달라 — 한 row 도 잃을 수 없는 forward-only invariant + 변조 검증이 본질

**amendment 결정** (D12=B Codex 권장 → Sonnet 채택 D12=γ ADR-016 amendment 단독):
- Phase 2 entry 의 ADR-009 §D12 추가 amend 0 (Pilot reference 그대로) — Phase 3 race 회피
- ADR-016 §A1-A4 단독 신규 절: backup-then-verify (genesis preserve 후 verify CLI 통과 시 backup 인정) + WAL checkpoint 의무 + restore safety (genesis row 보존) + NFS/SMB 금지 (file lock fragility) + storage class preflight

**Codex fix-back** (PR #136 7-area review): 3 High — backup-then-verify 의무 / NFS 명시 금지 / WAL race avoidance alternative — 모두 amendment 본문에 land.

### 5.5 ADR-009 §D12 5-sister adoption verification

Phase 2 entry 의 ADR-009 §D12 박제 invariant:
- named volume (host bind 금지)
- forward-only invariant (named volume 가 destroy 시 데이터 영구 손실)
- DR backup recipe (PowerShell + bash dual command)

5 sister 적용 정합성 매트릭스:

| Sister | volume topology | §D12 정합 | 비고 |
|---|---|---|---|
| Phase 1 mctrader-data 자체 | `mctrader_data` (named, rw) | invariant 자체 source | Pilot |
| Phase 3 mctrader-engine | `mctrader_data:ro` (cross-stack) + `engine_runs` + `engine_wfo` + `engine_lock` (4 named volumes) | ✅ 4/4 named, forward-only | engine 자체 named 추가는 §D12 의 spirit 정합 |
| Phase 4 mctrader-web | `mctrader_web_data:rw` (api 자체) + `mctrader-data_mctrader_data:ro` (external cross-stack) | ✅ 2/2 named, forward-only | RO mount 는 named volume 그대로 — §D12 정합 |
| Phase 5 mctrader-market | n/a | n/a | 배포 표면 부재 |
| Phase 5 mctrader-market-bithumb | n/a | n/a | 배포 표면 부재 |
| Phase 5 mctrader-hub | n/a | n/a | 배포 표면 부재 |

→ deployable trio 5/5 named volume + forward-only 정합. ADR-009 §D12 가 sister rollout 의 reference 로서 안정 작동, 추가 amend 0.

### 5.6 Carry-over 표 (F1-F9, post-Epic Story 후보)

| ID | 항목 | priority | 등록 |
|---|---|---|---|
| F1 | mctrader-data CLI dep semver pinning (Pilot leftover) | low | list-only |
| F2 | audit-cron sidecar 자동화 (Phase 4 retention 자동화) | mid | list-only — ops Story 후보 |
| F3 | TLS production cert 자동화 (Phase 4 D6 production hardening) | low | list-only — ops Story 후보 |
| F4 | ghcr.io publish + multi-arch buildx (Pilot F1-F2 carry) | mid | list-only — release Story 후보 |
| F5 | webapp-minimal codeforge example update (Streamlit 2-service 패턴) | low | list-only — codeforge upstream |
| **F6** | **collector e2e Linux-only fix (MCT-97 P6 era)** | **HIGH** | **GitHub issue (mctrader-web) — 본 Epic close 와 동시 등록** |
| F7 | manual integration smoke 10 항목 actual deploy verification | mid | list-only — deploy event 시 ops 책임 |
| F8 | dev sqlite git history cleanup | low | list-only — history rewrite Story 후보 |
| F9 | D13 fcntl.flock cross-container mutex ADR formalization | low | list-only — 2nd reuse 시점 |

→ 1 HIGH (F6 즉시 issue) + 3 mid (F2/F4/F7) + 5 low (F1/F3/F5/F8/F9).

---

## 6. Cross-repo Coordination

### 6.1 Per-repo PR commit 박제

| Repo | PR | Commit (squash 또는 merge) | branch |
|---|---|---|---|
| mctrader-hub | #119 | 64830f5 | docs/MCT-93-data-docker-pilot |
| mctrader-data | #11 | 645e476 (final commit of 8) | feat/MCT-99-docker-first |
| mctrader-hub | #122 | 44caa1a | docs/MCT-98-MCT-99-phase-2-entry |
| mctrader-hub | #135 | 9a5e956 | docs/MCT-100-engine-docker |
| mctrader-engine | #37 | f6c8c12 (final commit of 10) | feat/MCT-100-docker-first |
| mctrader-hub | #136 | 443807e | docs/MCT-101-web-docker |
| mctrader-web | #22 | a0ac2ce (squash) | feat/MCT-101-docker-first |
| mctrader-hub | #141 | f8d5b83 | docs/MCT-101-story-close |
| mctrader-hub | #137 | e763352 | feat/MCT-102-infra-strategy-none |
| mctrader-market | #2 | (post-merge fill) | feat/MCT-102-infra-strategy-none |
| mctrader-market-bithumb | #5 | (post-merge fill) | feat/MCT-102-infra-strategy-none |
| mctrader-hub | (this PR) | (post-merge fill) | docs/MCT-98-phase6-epic-close |

### 6.2 Reconciliation pattern 박제

- **Phase 2 entry reconciliation**: Pilot 박제 timeline 누락 (별도 issue 등록 의도) → smoke verification 후 close — Bithumb#4 처리
- **Phase 4 last-merge reconciliation 책임**: Phase 4 가 (PR #141) Phase 4 마지막 merge → Phase 4 가 Epic body Phase 4 status DONE update 단일 책임 수행 (race 회피)
- **Phase 6 close reconciliation**: Phase 1-5 ALL DONE 기 박제 → Phase 6 close 가 EPIC-RESULTS doc + Epic body 최종 update + Closes #120

---

## 7. Story Acceptance Verdict (B1-B5)

| AC | 항목 | 결과 | 근거 |
|----|------|------|------|
| B1 | 6 repo 모두 `.claude/_overlay/project.yaml` `infra_strategy:` 명시 (`docker_first` or `none`) | **PASS** | data docker_first / engine docker_first / web docker_first / market none / bithumb none / hub none = 6/6 |
| B2 | deployable trio (data, engine, web) Docker artifact 박제 + healthcheck pattern | **PASS** | data Dockerfile+compose+HealthServer / engine Dockerfile + paper+engine 2-service + HealthServer / web Dockerfile + api+panel 2-service + /health + /_stcore/health |
| B3 | library quartet (market, bithumb, hub) `infra_strategy: none` lint pass | **PASS** | Phase 5 MCT-102 #134 3 PR joint sweep — `bash check-container-strategy.sh` SKIP 3/3 |
| B4 | mctrader-market-bithumb WS finding 처리 | **PASS** | mctrader-market-bithumb#4 closed 2026-05-08 (PR #3 inline fix 2026-05-07 + Phase 2 entry session smoke verified) |
| B5 | EPIC-RESULTS-MCT-98.md 작성 | **PASS** | 본 doc + Story §8.6/§11 fill-in + 9 D Codex+Sonnet 합의 + F6 follow-up issue 등록 |

**5/5 PASS — Epic MCT-98 COMPLETE**.

---

## 8. codeforge Upstream Finding (PMOAgent 후속 등록 대상)

본 Epic 진행 중 codeforge plugin 자체 개선 후보 5건 surface:

| # | Finding | 영향 |
|---|---------|------|
| CF-Docker-1 | parallel session hub working dir branch race 패턴 — superpowers worktree 의무 추가 후보 | dev workflow 비용 / data integrity risk |
| CF-Docker-2 | `check-container-strategy.sh` lint UX — FAIL 메시지 명확성 (resolve options 표기 OK, 단 default value 의 의도 표시 부족) | dev experience |
| CF-Docker-3 | cross-stack volume namespacing fragility — `<stack>_<volume>` external true 패턴 의 stack rename 시 silent break | dev experience / data integrity risk |
| CF-Docker-4 | hadolint inline DL3008/DL3013 ignore directive 의 cross-Dockerfile 정합 (5 sister × Dockerfile policy 일관성) | maintainability |
| CF-Docker-5 | webapp-minimal codeforge example update — Streamlit 2-service compose 패턴 박제 의무 | downstream consumer (mctrader-web 외 future webapp) |

→ codeforge plugin 측 별도 issue 등록 후보. PMOAgent retrospective 후속.

---

## 9. Aggregate Metrics (Docker-specific)

### 9.1 PR / commit / test 수

| metric | 수치 |
|---|---|
| 총 mctrader-hub PR (P1-P6) | 7 (#119, #122, #135, #136, #137, #141, this PR) |
| 총 sister repo PR | 5 (data#11, engine#37, web#22, market#2, bithumb#5) |
| 총 commit (sister repo) | data 8 + engine 10 + web 15-squashed (실 commit 다수) + market 1 + bithumb 1 = ~35+ |
| 총 commit (mctrader-hub) | P1-P6 합 ~30 |
| 총 신규 test | data +4 (HealthServer) + engine +6 (HealthServer + flock + paper_runner) + web +12 (D6/D8/compose invariant + 4 admin pyright fix) + library 0 = +22 |
| 총 baseline → final test 수 (per repo) | data 182→186 / engine 751→757 / web (이미 460+ baseline) → +5 신규 + 4 fix = +9 net |
| Linux-only e2e regression | F6 (1 test, MCT-97 era pre-existing surface 후 admin merge bypass + 본 Epic close 와 동시 follow-up issue 등록) |

### 9.2 ADR amendment / 신규 pattern 수

- ADR amendment: 3건 (ADR-009 §D12 / ADR-015 cross-ref / ADR-016 §A1-A4)
- 신규 pattern: 1건 (D13 fcntl.flock cross-container mutex — F9 carry-over for ADR formalization)
- ADR-002 D6 변경 0 (paper ledger 정정 — Phase 4 session prompt 정정 only)
- ADR-014 single-process invariant 변경 0 (Phase 4 D5 in-process asyncio.Task 채택, invariant 보존)

### 9.3 Codex review round (per phase agentId)

| Phase | 단계 | agentId | 결과 |
|---|---|---|---|
| P1 Pilot | brainstorm | (Pilot session 박제) | 7 D 합의 |
| P2 entry | initial design | `af61a4c87e9d7906c` | 8 D + top 5 risk + 7 sequencing nit |
| P2 entry | PR #122 7-area review | `a5ff38a167380b3d8` | APPROVE WITH FIXES, 3 MEDIUM fix-back commit `6e40b18` |
| P3 engine | initial design | (specific agentId 미박제) | 11 D + Codex D12 + Sonnet D13 fcntl.flock 합의 (총 13) |
| P3 engine | PR #135 + #37 reviews | (specific agentId 미박제) | passed |
| P4 web | initial design | `a9897ebe62347932a` | 13 D 채택 + 4 sub-decision adjustment |
| P4 web | PR #136 + #22 7-area review | (각각 별도 agentId — #136 3 High + 2 Medium fix-back / #22 1 High + 2 Medium fix-back) | 5 fix-back land 100% |
| P5 library | brainstorm | `a66da458a451e3169` | 5 D 합의 (Single Story / 3 PR joint / No bump / Single Codex / 로컬 lint evidence) |
| **P6 close** | **본 design 합의** | **`a63731290d7d25208`** | **9 D 합의 (D1-D9)** |

→ 총 Codex review round 8회 이상. Sonnet decider 합성 + 사용자 승인 트라이악 패턴 모든 phase 적용.

### 9.4 Phase 3+4 parallel ROI 실측

- Phase 3 + Phase 4 모두 2026-05-08 단일 calendar day 완료
- Phase 3 mctrader-hub merge: PR #135 02:33:04Z → mctrader-engine PR #37 후속 → (engine PR # 시점 미박제, but P3 close 02:30~03:00 KST 추정)
- Phase 4 mctrader-hub merge: PR #136 (01:59:25Z) → mctrader-web PR #22 (07:13:11Z) → PR #141 Story close (07:19:28Z)
- 두 phase parallel 진행 시점 시간차 약 4-5시간 → serial 가정 시 8-10시간 → 실제 4-5시간 으로 약 50% 단축

→ Hybrid by shape sequencing (D2=C, deployable trio + library 분리) 의 critical path 단축 효과 확인. parallel session race 비용 (Phase 5 contamination 1건) 은 worktree isolation pattern 으로 mitigation.

### 9.5 Version bump summary

| Repo | from | to | bump kind | BREAKING? |
|---|---|---|---|---|
| mctrader-data | 0.8.0 | 0.9.0 | minor | YES (systemd 자산 삭제) |
| mctrader-engine | 0.29.0 | 0.30.0 | minor | YES (Docker-first containerization) |
| mctrader-web | 0.13.0 | 0.14.0 | minor | YES (compose surface change + env override) |
| mctrader-market | 0.x.x | (no bump) | n/a | NO (declarative meta only) |
| mctrader-market-bithumb | 0.x.x | (no bump) | n/a | NO (declarative meta only) |
| mctrader-hub | (no version) | n/a | n/a | NO (governance repo) |

→ deployable trio 모두 minor + BREAKING 명시. library quartet 모두 no bump (declarative meta only) — Phase 5 D3 결정.

### 9.6 Carry-over 항목 수

| priority | 수 | 항목 |
|---|---|---|
| HIGH | 1 | F6 |
| mid | 3 | F2, F4, F7 |
| low | 5 | F1, F3, F5, F8, F9 |

총 9 carry-over.

---

## 10. 다음 Epic 후보

| 후보 | 내용 | priority | 선행 조건 |
|------|------|----------|-----------|
| **F6 mctrader-web collector e2e fix** | Linux-only failure 진단 + fix (MCT-97 P6 era pre-existing) | **HIGH (CI 정상화 의무)** | 없음 — 본 Epic close 와 동시 issue 등록 |
| F4 ghcr.io publish | multi-arch buildx + 5 sister deployable trio image push automation | mid | release 정책 결정 |
| F2 audit-cron sidecar | mctrader-web audit_log 자동 retention (compose sidecar 또는 host cron) | mid | F4 image push 후 |
| live executor (MCT-12) Docker 통합 | live trading executor compose run pattern | mid (Epic 후) | CFP-60 dependency 확인 |
| F9 D13 ADR formalization | 2nd reuse 시점에 author (현재 단일 사용처 = engine) | low | 2nd reuse 발생 시 |
| F1/F3/F5/F8 | 개별 carry-over | low | 별도 trigger |

---

## 11. 회고 (Epic-level 통합)

본 §11 은 Story file (MCT-98 §11) 의 6 항목 회고와 dual-anchor. Story file 박제 결과:

1. **6 phase 별 실제 vs 계획 시간 비교**: 전체 2 calendar day, Phase 3+4 parallel 50% 단축
2. **Hybrid by shape sequencing ROI**: deployable trio + library quartet 분리 정합, library 3 PR joint sweep 으로 process weight 1× 유지
3. **Pilot reference 5 sister rollout reuse 매트릭스**: 7/8 patterns reused (engine, web), library quartet 의도적 0 재사용 (배포 표면 부재)
4. **ADR-009 §D12 5-sister 적용 정합**: 5/5 정합, sister rollout 의 reference 로 안정 작동
5. **Phase 2 entry Bithumb verification 의 Phase 5 entry 단순화**: critical path simplification + AC 박제 가능 시점 1 phase 단축
6. **후속 ADR 후보**: ADR-009 §D12 / ADR-015 cross-ref / ADR-016 §A1-A4 land + D13 F9 carry-over

→ 자세한 retrospection 은 `docs/stories/MCT-98.md` §11 박제.

---

*Epic MCT-98 종료 — 2026-05-08*
