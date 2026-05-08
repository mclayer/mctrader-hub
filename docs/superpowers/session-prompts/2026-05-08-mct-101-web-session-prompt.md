# MCT-101 Phase 4 — mctrader-web Docker-first Containerization session prompt

> **사용법**: 새 Claude Code session 에서 working directory = `c:\workspace\mclayer\mctrader-hub` 진입 후 본 prompt 전체를 message 로 paste.

---

너는 mctrader Docker-first Migration Epic (MCT-98 #120) 의 **Phase 4 — mctrader-web sister** Story 를 진행한다. parallel 로 진행되는 Phase 3 (MCT-100 mctrader-engine, mctrader-hub#131) 와 독립.

## Context (이미 완료된 상태)

**Epic governance**:
- Epic Story: `mctrader-hub#120` (MCT-98 OPEN, Phase 6 close 까지 유지)
- Phase 1 Pilot DONE 2026-05-07 — mctrader-data Docker-first 전환 (PR #119 spec/plan + mctrader-data#11 impl, 8 commits, 0.8.0→0.9.0)
- Phase 2 entry DONE 2026-05-08 — mctrader-hub PR #122 (squash `44caa1a`)
- Phase 5 bithumb sister rollout entry condition = 이미 만족 (mctrader-market-bithumb PR #3 inline fix + integration smoke verified)

**본 Story key**: `MCT-101`, GitHub issue `mctrader-hub#132` (stub 등록 됨).

**Reference 의무**:
- **Pilot reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-07-mctrader-data-docker-pilot-design.md` + plan + mctrader-data PR #11 8 commits
- **Story §11 회고**: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-99.md` §11.4 — web 은 **high risk** (multi-service novel pattern) 명시
- **ADR-009 §D12**: `c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-009-ohlcv-schema.md` (named volume + forward-only + DR backup recipe — 본 Story 의 sqlite volume 에 적용 의무)
- **codeforge ADR-033**: carrier_story CFP-128 — `mclayer/plugin-codeforge` repo
- **codeforge `examples/webapp-minimal/`**: multi-service compose 패턴 reference (FastAPI + healthcheck + named volume — 본 Story 가 가장 가깝게 차용할 패턴)
- **ADR-002 D6 SQLite Event Store**: `c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-002-...md` (sqlite WAL mode + 영속화 invariant)

## Scope (Phase 4 본 Story)

**Repo**: `c:\workspace\mclayer\mctrader-web`

**Shape**: multi-service compose — FastAPI (`api/lifecycle.py` 등 mctrader-engine lifecycle proxy) + Streamlit (panel) + sqlite (event store, ADR-002 D6). Pilot Story §11.4 기준 **high risk**.

**Goal**: mctrader-web 의 Docker-first 전환. multi-service compose pattern + sqlite volume DR + 양 service healthcheck + image-lint workflow + (필요 시) ADR amendment.

## Open design 결정점 (brainstorming session 진입 시 결정)

다음 6+ 결정점은 brainstorming 시 사용자 승인 또는 Codex 일괄 dispatch → Sonnet decider 로 결정:

1. **Compose service 구성**:
   - α 2 service (api: FastAPI + panel: Streamlit)?
   - β 1 service multi-process (uvicorn + streamlit, supervisord)?
   - γ 3 service (api + panel + worker)?
2. **sqlite volume 분리 vs 통합**:
   - α 단일 named volume `mctrader_web_data` (api/panel 모두 공유)?
   - β 분리 (api: events, panel: caches)?
   - γ codeforge `examples/webapp-minimal/` 패턴 정확 차용?
3. **sqlite DR pattern**:
   - α ADR-009 §D12 named volume + WAL mode + 표준 backup recipe (alpine tar volume snapshot) 그대로?
   - β + litestream 등 sqlite 전용 backup tool?
   - γ + WAL checkpoint + cron snapshot 자동화?
4. **HealthServer 적용**:
   - α 양 service (api + panel) 모두 healthcheck endpoint?
   - β api 만 (Streamlit 자체 healthcheck endpoint 검토)?
   - γ 별도 sidecar healthcheck container?
5. **mctrader-engine 의존 처리** (cross-repo):
   - α FastAPI proxy → mctrader-engine 의 `paper_runner` 등 외부 process call?
   - β subprocess 직접 spawn?
   - γ message queue (Redis 등) 도입 여부?
6. **ADR-002 D6 SQLite Event Store invariant 정합**:
   - 본 Story 의 named volume + WAL 패턴이 ADR-002 D6 의 영속화 invariant 와 충돌 없는지 검증 의무
   - 충돌 시 ADR-002 amendment 후보 (Phase 5 외부로 escalate 필요?)

## Workflow (skill chain)

다음 skill chain 을 순서대로 진행:

1. **`superpowers:brainstorming`** — Q-by-Q 사용자 stop 금지 (memory feedback `Brainstorm Codex review pattern`). 모든 open design 결정점 식별 → Codex 일괄 dispatch (`codex:codex-rescue`) → Sonnet decider 합성 → user review gate 1회.
2. **`superpowers:writing-plans`** — bite-sized task breakdown. Pilot plan + codeforge `examples/webapp-minimal/` 참조.
3. **`superpowers:executing-plans`** (또는 subagent-driven-development) — inline 또는 subagent 모드 사용자 선택.
4. **`codex:codex-rescue`** Codex 7-area review per phase (memory feedback `phase_codex_review_loop`) → Sonnet decider 우선순위 채택, fix-back commit.
5. **CI watch + admin merge** (memory feedback `admin_merge_autonomy` + `ci_terminal_states_classify`).
6. **`superpowers:finishing-a-development-branch`**.

## Branch + commit naming

- mctrader-hub spec/plan branch: `docs/MCT-101-web-docker`
- mctrader-web impl branch: `feat/MCT-101-docker-first`
- commit prefix: `[MCT-101]`
- PR title prefix: `[MCT-101]`

## Coordination 의무 (Phase 3 engine parallel)

Phase 3 (`MCT-100` `mctrader-hub#131`) 는 **다른 session 에서 동시 진행**. 다음 race 회피:

1. **Epic #120 body race**: 본 Story PR merge 후 Epic body 업데이트 시 Phase 3 의 update 와 충돌 가능. 양쪽 PR merged 후 **별도 reconciliation commit** 으로 Phase 3+4 status 동시 박제 (둘 중 마지막 merge session 이 reconciliation 책임).
2. **Cross-cutting finding**: brainstorming 또는 Codex review 시 mctrader-engine 와 mctrader-web 양쪽에 영향 가는 finding 발견 시 → memory file 에 박제 + Phase 3 session 시 surface 의무. 특히 web 의 multi-service pattern 이 engine 의 daemon shape 에도 적용 가능한 경우 (예: paper daemon 의 별도 healthcheck endpoint 패턴) → engine session 에 surface 의무.
3. **ADR-009 §D12 추가 amendment 충돌 회피**: 본 Story 가 sqlite volume DR pattern 으로 §D12 추가 amendment (예: WAL mode 명시) 시 Phase 3 session 도 ADR-009 amend 가능 → merge 순서 조정 또는 단일 amendment commit 으로 통합. **본 Story 가 sqlite 도입 → ADR amendment 발생 확률 더 높음**.
4. **ADR-002 amendment 별도 Story 후보**: 본 Story 가 ADR-002 D6 SQLite Event Store 와 충돌 발견 시 → 별도 ADR amendment Story (Phase 4 scope 외부) 로 escalate.

memory file 위치: `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\` — `project_dockerization_epic.md` update 또는 `project_dockerization_phase4.md` 신규.

## 종료 조건 (Phase 4 acceptance)

- [ ] mctrader-hub `docs/superpowers/specs/2026-05-DD-mctrader-web-docker-design.md`
- [ ] mctrader-hub `docs/superpowers/plans/2026-05-DD-mctrader-web-docker-plan.md`
- [ ] mctrader-hub `docs/stories/MCT-101.md` (`## 1.` ~ `## 11.` 번호 section, MCT-99/97 reference format)
- [ ] (필요 시) mctrader-hub ADR amendment — ADR-009 §D12 sqlite WAL/backup 추가 또는 ADR-002 D6 amendment
- [ ] mctrader-web repo:
  - Dockerfile (2-stage, non-root user, codeforge ADR-033 정합)
  - compose.yml (결정된 multi-service 구성 — named volume + 양 service healthcheck per ADR-009 §D12)
  - .dockerignore
  - `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
  - `.github/workflows/image-lint.yml` (hadolint)
  - HealthServer (api 또는 양 service) — mctrader-data 의 `health_server.py` 패턴 차용
  - README "Docker deployment" 절 (multi-service 명시)
  - pyproject version bump + CHANGELOG entry
  - tests/integration/README.md (manual smoke 절차 — multi-service 특화 sqlite volume invariant + restart 검증 추가)
- [ ] hadolint clean + `docker compose config` PASS + `docker build` 성공 + image entrypoint smoke
- [ ] integration smoke — compose-up 양 service healthy + sqlite volume restart preservation + multi-service network connectivity
- [ ] mctrader-hub doc PR + mctrader-web impl PR phase-gate-mergeable green + admin merge
- [ ] Codex 7-area review push-back fix-back 또는 defer 박제
- [ ] Epic #120 body Phase 4 status update (parallel reconciliation 의무)
- [ ] mctrader-hub#132 close (Phase 4 DONE)

## 진행 시작 시 첫 메시지

```
mctrader Docker-first Migration Epic (MCT-98 #120) Phase 4 진행 — mctrader-web sister (multi-service compose).

본 session 은 parallel Phase 3 (MCT-100 mctrader-engine #131) 와 독립.

Pilot Story §11.4 기준 high risk (multi-service novel pattern + sqlite volume DR).

먼저 brainstorming 으로 open design 결정점 정리 후 Codex dispatch + Sonnet decider 진행.
```
