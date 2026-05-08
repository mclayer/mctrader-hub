# MCT-100 Phase 3 — mctrader-engine Docker-first Containerization session prompt

> **사용법**: 새 Claude Code session 에서 working directory = `c:\workspace\mclayer\mctrader-hub` 진입 후 본 prompt 전체를 message 로 paste.

---

너는 mctrader Docker-first Migration Epic (MCT-98 #120) 의 **Phase 3 — mctrader-engine sister** Story 를 진행한다. parallel 로 진행되는 Phase 4 (MCT-101 mctrader-web, mctrader-hub#132) 와 독립.

## Context (이미 완료된 상태)

**Epic governance**:
- Epic Story: `mctrader-hub#120` (MCT-98 OPEN, Phase 6 close 까지 유지)
- Phase 1 Pilot DONE 2026-05-07 — mctrader-data Docker-first 전환 (PR #119 spec/plan + mctrader-data#11 impl, 8 commits, 0.8.0→0.9.0)
- Phase 2 entry DONE 2026-05-08 — mctrader-hub PR #122 (squash `44caa1a`)
- Phase 5 bithumb sister rollout entry condition = 이미 만족 (mctrader-market-bithumb PR #3 inline fix + integration smoke verified)

**본 Story key**: `MCT-100`, GitHub issue `mctrader-hub#131` (stub 등록 됨).

**Reference 의무**:
- **Pilot reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-07-mctrader-data-docker-pilot-design.md` + plan + mctrader-data PR #11 8 commits
- **Story §11 회고**: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-99.md` §11.4 (5 sister shape 분석)
- **ADR-009 §D12**: `c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-009-ohlcv-schema.md` (named volume + forward-only + DR backup recipe — 본 Story 의 reference 의무)
- **codeforge ADR-033**: carrier_story CFP-128, Docker-first Infra Engineering — `mclayer/plugin-codeforge` repo
- **codeforge `examples/cli-tool-minimal/`**: CLI shape Dockerfile 패턴 (mctrader-data Pilot 가 차용한 패턴)

## Scope (Phase 3 본 Story)

**Repo**: `c:\workspace\mclayer\mctrader-engine`

**Shape**: backtest one-shot CLI + paper daemon (dual mode, Pilot Story §11.4 기준 medium risk)

**Goal**: mctrader-engine 의 Docker-first 전환. backtest executor (one-shot) + paper_runner (long-running daemon) + WFO executor (multi-fold one-shot) 의 compose surface 결정 + Dockerfile + healthcheck + named volume + image-lint workflow.

## Open design 결정점 (brainstorming session 진입 시 결정)

다음 5+ 결정점은 brainstorming 시 사용자 승인 또는 Codex 일괄 dispatch → Sonnet decider 로 결정:

1. **Compose surface**:
   - α 1 service `paper` (paper daemon) + `compose run` (backtest, WFO one-shot)?
   - β 2 service (paper + backtest profile)?
   - γ 3 service (paper + backtest + wfo profile)?
2. **HealthServer 적용**:
   - 모든 paper daemon 에 mctrader-data Pilot 패턴 (HTTP /health endpoint, ws_state 기반 200/503)?
   - one-shot (backtest, WFO) 은 exit code 만 (HEALTHCHECK 없음)?
3. **Data input**:
   - named volume 공유 (mctrader_data 와 동일)?
   - host bind mount (개발 편의성, ADR-033 §결정 6 host bind 거절 근거 검토)?
   - `compose run` argument 로 path 전달?
4. **Engine state machine (ADR-015) compose 매핑**:
   - daemon `[stopped/starting/running/stopping/crashed/degraded]` 와 Docker container state alignment?
   - one-shot `[queued/running/completed/failed/cancelled]` 와 `compose run` lifecycle alignment?
5. **mctrader-engine 내부 process 분리** (도메인 해석):
   - `paper_runner` daemon 1개 vs N (per-strategy) 인지 검토?
   - `BacktestExecutor` + `WFO executor` 의 `api/lifecycle.py` (mctrader-web 가 호출) 와 Docker entrypoint 정합?

## Workflow (skill chain)

다음 skill chain 을 순서대로 진행:

1. **`superpowers:brainstorming`** — Q-by-Q 사용자 stop 금지 (memory feedback `Brainstorm Codex review pattern`). 모든 open design 결정점 식별 → Codex 일괄 dispatch (`codex:codex-rescue`) → Sonnet decider 합성 → user review gate 1회.
2. **`superpowers:writing-plans`** — bite-sized task breakdown. Pilot plan (`docs/superpowers/plans/2026-05-07-mctrader-data-docker-pilot-plan.md`) 의 8 task 구조 참조 가능.
3. **`superpowers:executing-plans`** (또는 subagent-driven-development) — inline 또는 subagent 모드 사용자 선택.
4. **`codex:codex-rescue`** Codex 7-area review per phase (memory feedback `phase_codex_review_loop`) → Sonnet decider 우선순위 채택, fix-back commit.
5. **CI watch + admin merge** (memory feedback `admin_merge_autonomy` + `ci_terminal_states_classify`).
6. **`superpowers:finishing-a-development-branch`**.

## Branch + commit naming

- mctrader-hub spec/plan branch: `docs/MCT-100-engine-docker`
- mctrader-engine impl branch: `feat/MCT-100-docker-first`
- commit prefix: `[MCT-100]`
- PR title prefix: `[MCT-100]`

## Coordination 의무 (Phase 4 web parallel)

Phase 4 (`MCT-101` `mctrader-hub#132`) 는 **다른 session 에서 동시 진행**. 다음 race 회피:

1. **Epic #120 body race**: 본 Story PR merge 후 Epic body 업데이트 시 Phase 4 의 update 와 충돌 가능. 양쪽 PR merged 후 **별도 reconciliation commit** 으로 Phase 3+4 status 동시 박제 (둘 중 마지막 merge session 이 reconciliation 책임).
2. **Cross-cutting finding**: brainstorming 또는 Codex review 시 mctrader-engine 와 mctrader-web 양쪽에 영향 가는 finding (예: 공통 helper, ADR amendment 후보) 발견 시 → 해당 finding 을 memory file 에 박제 + Phase 4 session 시 surface 의무.
3. **ADR amendment 충돌 회피**: 본 Story 가 ADR-009 §D12 의 추가 amendment (예: backtest 데이터 별도 volume 명시) 가 필요하면 Phase 4 session 도 동일 ADR-009 를 amend 가능 → merge 순서 조정 또는 단일 amendment commit 으로 통합.

memory file 위치: `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\` — `project_dockerization_epic.md` update 또는 `project_dockerization_phase3.md` 신규.

## 종료 조건 (Phase 3 acceptance)

- [ ] mctrader-hub `docs/superpowers/specs/2026-05-DD-mctrader-engine-docker-design.md`
- [ ] mctrader-hub `docs/superpowers/plans/2026-05-DD-mctrader-engine-docker-plan.md`
- [ ] mctrader-hub `docs/stories/MCT-100.md` (`## 1.` ~ `## 11.` 번호 section, MCT-99/97 reference format)
- [ ] mctrader-engine repo:
  - Dockerfile (2-stage, non-root user, codeforge ADR-033 정합)
  - compose.yml (결정된 service 구성, named volume + healthcheck per ADR-009 §D12)
  - .dockerignore
  - `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
  - `.github/workflows/image-lint.yml` (hadolint)
  - HealthServer (paper daemon 적용 시) — mctrader-data 의 `health_server.py` 패턴 차용
  - README "Docker deployment" 절
  - pyproject version bump + CHANGELOG entry
  - tests/integration/README.md (manual smoke 절차 — mctrader-data 의 패턴 차용)
- [ ] hadolint clean + `docker compose config` PASS + `docker build` 성공 + image entrypoint smoke
- [ ] integration smoke (compose-up → healthy)
- [ ] mctrader-hub doc PR + mctrader-engine impl PR phase-gate-mergeable green + admin merge
- [ ] Codex 7-area review push-back fix-back 또는 defer 박제
- [ ] Epic #120 body Phase 3 status update (parallel reconciliation 의무)
- [ ] mctrader-hub#131 close (Phase 3 DONE)

## 진행 시작 시 첫 메시지

```
mctrader Docker-first Migration Epic (MCT-98 #120) Phase 3 진행 — mctrader-engine sister.

본 session 은 parallel Phase 4 (MCT-101 mctrader-web #132) 와 독립.

먼저 brainstorming 으로 open design 결정점 정리 후 Codex dispatch + Sonnet decider 진행.
```
