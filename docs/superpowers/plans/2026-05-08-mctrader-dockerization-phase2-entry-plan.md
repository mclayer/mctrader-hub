# mctrader Docker-first Migration — Phase 2 Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader Docker-first Migration Epic governance state 정렬. mctrader-data Pilot 구현 종료 후 Epic + Pilot Story 를 retroactive 등록하고 ADR-009 §D12 (named volume + forward-only + DR backup) 박제, mctrader-market-bithumb WS schema finding 별도 issue 등록. 5 sister rollout (Phase 3-5) 진입 전 의무.

**Architecture:** doc-only PR + GitHub issue 등록. 코드 변경 0. 산출 7 artifact: mctrader-hub `docs/stories/MCT-98.md` (Epic) + `docs/stories/MCT-99.md` (Pilot retroactive) + `docs/adr/ADR-009-ohlcv-schema.md` (§D12 amendment) + 3 GitHub issue (mctrader-hub × 2, mctrader-market-bithumb × 1) + Codex 7-area review + Sonnet decider 합성.

**Tech Stack:** GitHub CLI (`gh`), git, Markdown. codeforge consumer phase-gate-mergeable workflow (doc-only fast-pass).

**Working repo**: `c:\workspace\mclayer\mctrader-hub\` (모든 git task 본 repo). 일부 task 는 cross-repo `gh` CLI 호출.

**Spec reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-08-mctrader-dockerization-phase2-entry-design.md` (commit `366aa48` on branch `docs/MCT-98-MCT-99-phase-2-entry`)

**Pre-task setup**: branch `docs/MCT-98-MCT-99-phase-2-entry` 이미 존재 (spec commit 됨). 본 plan 의 모든 task 는 동일 branch 에서 실행.

---

## File Structure (변경 매트릭스)

### Create (mctrader-hub repo)

| 파일 | 책임 | 생성 task |
|---|---|---|
| `docs/stories/MCT-98.md` | Epic Story — mctrader Docker-first Migration. Phase 1-6 plan, child Story link, AC B1-B5, retrospection placeholder | Task 5 |
| `docs/stories/MCT-99.md` | Pilot Story (retroactive) — mctrader-data Docker-first Containerization (P1 DONE). §11 retrospective (Phase 2+ entry 조건 + 5 sister shape 분석 + Bithumb leftover finding link) | Task 6 |

### Modify (mctrader-hub repo)

| 파일 | 변경 | task |
|---|---|---|
| `docs/adr/ADR-009-ohlcv-schema.md` | Amendment History 항목 추가 (2026-05-08) + §D12 신설 (Docker-first persistence: D12.1 named volume + D12.2 forward-only + D12.3 DR backup recipe + D12.4 후속 자동화) | Task 7 |

### GitHub issue 등록

| Repo | Issue | 생성 task |
|---|---|---|
| mclayer/mctrader-hub | Epic MCT-98 | Task 2 |
| mclayer/mctrader-hub | Pilot Story MCT-99 | Task 3 |
| mclayer/mctrader-market-bithumb | WS schema finding (#1) | Task 4 |

---

## Task 1: Pre-flight 검증

**Files:** N/A (read-only)

- [ ] **Step 1.1: 현재 branch 확인**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git branch --show-current
```
Expected output: `docs/MCT-98-MCT-99-phase-2-entry`

- [ ] **Step 1.2: Spec commit 존재 확인**

Run:
```powershell
git log --oneline -3
```
Expected: 최상단에 `366aa48 docs(spec): mctrader Docker-first Migration Phase 2 entry design` 표시.

- [ ] **Step 1.3: MCT-98 / MCT-99 Story key 충돌 검사 (mctrader-hub)**

Run:
```powershell
gh issue list --repo mclayer/mctrader-hub --state all --search "MCT-98 in:title" --json number,title
gh issue list --repo mclayer/mctrader-hub --state all --search "MCT-99 in:title" --json number,title
```
Expected: 둘 다 `[]` (collision 없음). 만약 collision 발견 시 → 작업 중단, 사용자에게 보고 후 next available key 로 shift.

- [ ] **Step 1.4: mctrader-market-bithumb issue 부재 확인**

Run:
```powershell
gh issue list --repo mclayer/mctrader-market-bithumb --state all --limit 5 --json number,title
```
Expected: `[]` (issue 부재 — 본 등록이 #1 됨).

- [ ] **Step 1.5: ADR-009 현재 상태 확인 (insert 위치 식별)**

Run:
```powershell
gh api repos/mclayer/mctrader-hub/contents/docs/adr/ADR-009-ohlcv-schema.md --jq '.content' | python -c "import sys, base64; print(base64.b64decode(sys.stdin.read()).decode()[:500])"
```
또는 로컬:
```powershell
Get-Content docs/adr/ADR-009-ohlcv-schema.md -TotalCount 25
```
Expected: line 16-18 에 Amendment History 2건 (2026-05-04, 2026-05-05). 신규 entry 는 line 18 다음에 추가.

---

## Task 2: Epic issue MCT-98 등록 (mctrader-hub)

**Files:** N/A (GitHub issue create)

- [ ] **Step 2.1: Epic issue body file 작성**

Create file `c:\tmp\mct-98-body.md` (임시):

```markdown
# [EPIC] MCT-98 — mctrader Docker-first Migration

## Trigger

codeforge ADR-033 (CFP-128 Accepted 2026-05-07) — InfraEngineerAgent default = Docker-first. mctrader 6-repo 의무 follow-on Epic.

## Phase plan (6 phase)

- **Phase 1 — Pilot (mctrader-data)** ✅ DONE 2026-05-07
  - mctrader-hub PR #119 (spec/plan)
  - mctrader-data PR #11 (impl, 8 commits, 0.8.0→0.9.0)
- **Phase 2 — Entry / bookkeeping** ⬅ this issue 의 phase
  - Epic + Pilot Story retroactive 등록
  - ADR-009 §D12 amendment (named volume + forward-only + DR backup)
  - mctrader-market-bithumb WS finding 등록 (Phase 5 blocker)
- **Phase 3 — mctrader-engine sister** (TBD MCT-100 candidate, 별도 spec/plan)
- **Phase 4 — mctrader-web sister** (TBD MCT-101 candidate, multi-service compose)
- **Phase 5 — Library batch (market+bithumb+hub joint)** (TBD MCT-102 candidate, infra_strategy: none)
- **Phase 6 — Epic close** (`EPIC-RESULTS-MCT-98.md`)

## Acceptance Criteria

- [ ] B1 6 repo 모두 `.claude/_overlay/project.yaml` `infra_strategy:` 명시 (docker_first or none)
- [ ] B2 deployable trio (data, engine, web) Docker artifact 박제 + healthcheck pattern
- [ ] B3 library quartet (market, bithumb, hub) `infra_strategy: none` lint pass
- [ ] B4 mctrader-market-bithumb WS finding close 또는 별도 Story 로 처리
- [ ] B5 EPIC-RESULTS-MCT-98 작성 (회고 + 6 phase 결과 + cross-cutting finding + 후속 ADR 후보)

## Codex review (Phase 2 entry)

- agentId `af61a4c87e9d7906c` (8 결정 + top 5 risk + 7 sequencing nit)
- 결정 합의:
  - D1=C 4 artifact 묶음
  - D2=C Hybrid by shape (deployable trio engine→web; library quartet joint)
  - D3=engine first sister
  - D4=B Bithumb issue+blocker (Epic inline fix 안 함)
  - D5=A library = `infra_strategy: none`
  - D6=A ADR-009 amendment 지금 (sister rollout 전)
  - D7=A 둘 다 retroactive 등록
  - D8="Docker-first Migration"

## Spec / Plan reference

- spec: `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase2-entry-design.md`
- plan: `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase2-entry-plan.md`

## Related

- codeforge ADR-033: https://github.com/mclayer/plugin-codeforge (carrier_story CFP-128)
- Pilot reference: mctrader-hub#119, mclayer/mctrader-data#11
- Pilot Story (retroactive): #<MCT-99 issue, will be linked after Task 3>
- Bithumb finding: mclayer/mctrader-market-bithumb#1 (will be linked after Task 4)
```

Save the file:
```powershell
$body = @'
[paste full content above]
'@
Set-Content -Path c:\tmp\mct-98-body.md -Value $body -Encoding utf8
```

(또는 Editor 로 직접 작성)

- [ ] **Step 2.2: Epic issue 생성**

Run:
```powershell
gh issue create `
  --repo mclayer/mctrader-hub `
  --title "[EPIC] MCT-98 — mctrader Docker-first Migration" `
  --body-file c:\tmp\mct-98-body.md
```
Expected output: `https://github.com/mclayer/mctrader-hub/issues/<NUMBER>` 출력. 출력된 NUMBER 를 기록 (이하 `$EPIC_ISSUE`).

- [ ] **Step 2.3: Issue 등록 검증**

Run:
```powershell
gh issue view $EPIC_ISSUE --repo mclayer/mctrader-hub --json number,title,state,labels
```
Expected: `state: OPEN`, title 에 `[EPIC] MCT-98` 포함.

- [ ] **Step 2.4: Epic issue 번호 환경 변수로 보존**

Run (PowerShell session 내):
```powershell
$env:MCT_98_ISSUE = "<number from Step 2.2>"
```

---

## Task 3: Pilot Story issue MCT-99 등록 (mctrader-hub, retroactive)

**Files:** N/A

- [ ] **Step 3.1: Pilot Story issue body 작성**

Create file `c:\tmp\mct-99-body.md`:

```markdown
# [STORY] MCT-99 — mctrader-data Docker-first Containerization (Pilot, P1)

> **Retroactive registration**: Pilot 구현 이미 merged (mctrader-hub PR #119 spec/plan, mctrader-data PR #11 impl). 본 issue 는 governance state 정렬용 anchor.

## Status

**Phase 1 DONE** — 2026-05-07 merged

본 issue 는 Phase 2 entry PR merge 후 close (P1 회고 박제 완료 상태).

## Parent Epic

mctrader-hub#<EPIC_ISSUE> — mctrader Docker-first Migration

## Implementation reference

- mctrader-hub PR #119 — `docs(spec/plan): mctrader-data Docker-first Pilot design + plan + Amendment 1`
- mctrader-data PR #11 — `feat: Docker-first containerization Pilot (CFP-128/ADR-033)`, 8 commits, 0.8.0→0.9.0

## Pilot 산출

- Dockerfile (2-stage python:3.12-slim, non-root mctrader UID 1001)
- compose.yml (collector daemon 1 service, named volume `mctrader_data`, restart unless-stopped, healthcheck)
- HealthServer HTTP /health endpoint (4 TDD test, ws_state 기반 200/503 판정)
- `.github/workflows/image-lint.yml` (hadolint job)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
- systemd 자산 일괄 삭제 (BREAKING)
- 186 pytest PASS, hadolint clean

## Story file

`docs/stories/MCT-99.md` (Phase 2 entry PR 안에 작성, §11 retrospective 포함)

## Pilot leftover finding

mclayer/mctrader-market-bithumb#1 — WS schema mismatch (orderbookdepth missing symbol ws_mapping.py:90, invalid event_time ws_mapping.py:33). blocks Phase 5 bithumb sister rollout.

## ADR amendments

- ADR-009 §D12 (Docker-first persistence: named volume + forward-only + DR backup recipe) — Phase 2 entry PR (mctrader-hub) 안에 작성

## Codex review trace

- Pilot session: brainstorming 2026-05-07 (Sonnet decider)
- Phase 2 entry session: agentId `af61a4c87e9d7906c` (Codex 7-area review, 8 결정 합의)

## Spec / Plan reference

- Pilot spec: `docs/superpowers/specs/2026-05-07-mctrader-data-docker-pilot-design.md`
- Pilot plan: `docs/superpowers/plans/2026-05-07-mctrader-data-docker-pilot-plan.md`
- Phase 2 entry spec: `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase2-entry-design.md`
- Phase 2 entry plan: `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase2-entry-plan.md`
```

저장:
```powershell
# editor 로 c:\tmp\mct-99-body.md 작성, <EPIC_ISSUE> placeholder 를 Task 2 의 실제 번호로 치환
```

- [ ] **Step 3.2: Pilot Story issue 생성**

Run:
```powershell
gh issue create `
  --repo mclayer/mctrader-hub `
  --title "[STORY] MCT-99 — mctrader-data Docker-first Containerization (Pilot, P1 DONE retroactive)" `
  --body-file c:\tmp\mct-99-body.md
```
Expected: issue URL 출력. 번호 기록 (이하 `$PILOT_ISSUE`).

- [ ] **Step 3.3: 환경 변수 보존**

Run:
```powershell
$env:MCT_99_ISSUE = "<number from Step 3.2>"
```

- [ ] **Step 3.4: 검증**

Run:
```powershell
gh issue view $env:MCT_99_ISSUE --repo mclayer/mctrader-hub --json number,title,state
```
Expected: `state: OPEN`, title 에 `[STORY] MCT-99` 포함.

---

## Task 4: Bithumb finding issue 등록 (mctrader-market-bithumb)

**Files:** N/A

- [ ] **Step 4.1: Bithumb finding body 작성**

Create file `c:\tmp\bithumb-finding-body.md`:

```markdown
# WS schema mismatch — orderbookdepth missing symbol + invalid event_time format

> **Blocks Phase 5 bithumb sister rollout** (Dockerization Epic mctrader-hub#<EPIC_ISSUE>)

## Symptoms (mctrader-data Pilot live test 2026-05-07)

mctrader-data Docker container 의 collector daemon → mctrader-market-bithumb WS adapter call 시 schema validation fail:

### F1. `orderbookdepth missing symbol`

- location: `src/mctrader_market_bithumb/ws_mapping.py` line 90
- expected: orderbookdepth event payload 에 `symbol` field 보존 + downstream 으로 propagate
- actual: symbol field missing, downstream HeartbeatWriter 가 mapping 실패

### F2. `invalid event_time: '2026-05-07 16:38:49.198650'`

- location: `src/mctrader_market_bithumb/ws_mapping.py` line 33
- expected: ISO 8601 format with timezone offset (예: `2026-05-07T16:38:49.198650+00:00`)
- actual: space separator + no timezone marker → datetime parse 실패

## Pilot impact (verified)

- Docker artifact 동작 검증 OK:
  - image build 성공
  - container start 성공
  - module import OK
  - HealthServer listen + Docker HEALTHCHECK 정확 호출
- HealthServer unhealthy 응답 정확 (HTTP 503 + `ws_state=disconnected` body)
- healthy-state 도달 = WS schema fix 후 가능

본 finding 은 Pilot Docker 작업 자체에는 무관 (Docker artifact 정확 동작). WS adapter 의 사전 결함이 healthy-state 검증을 차단.

## Reference

- Pilot Story: mctrader-hub#<PILOT_ISSUE>
- Pilot PR (mctrader-data): https://github.com/mclayer/mctrader-data/pull/11 (§11 finding)
- Dockerization Epic: mctrader-hub#<EPIC_ISSUE>

## Expected fix scope

- 별도 Story (mctrader-market-bithumb 본 repo)
- Phase 5 bithumb sister rollout entry 시점에 fix 의무 (blocker)
- fix 후 mctrader-data live WS test → HealthServer healthy 응답 확인 (acceptance)

## Acceptance

- [ ] orderbookdepth event payload 에 symbol field 정확 mapping (downstream propagate 포함)
- [ ] event_time ISO 8601 format with timezone offset (UTC 명시)
- [ ] mctrader-data live WS test → HealthServer 200 + ws_state=connected 응답
- [ ] regression test (ws_mapping unit test 추가)

## Codex review trace

- Phase 2 entry session: agentId `af61a4c87e9d7906c` (D4=B 결정 — issue 등록 + Phase 5 blocker, Epic inline fix 안 함)
```

저장 (placeholder `<EPIC_ISSUE>`, `<PILOT_ISSUE>` 치환):
```powershell
# editor 로 c:\tmp\bithumb-finding-body.md 작성 + 두 placeholder 치환
```

- [ ] **Step 4.2: Bithumb finding issue 생성**

Run:
```powershell
gh issue create `
  --repo mclayer/mctrader-market-bithumb `
  --title "WS schema mismatch — orderbookdepth missing symbol + invalid event_time format (blocks Phase 5 rollout)" `
  --body-file c:\tmp\bithumb-finding-body.md
```
Expected: 출력된 issue URL 의 number = `1` (첫 issue).

- [ ] **Step 4.3: 환경 변수 보존**

Run:
```powershell
$env:BITHUMB_ISSUE = "<number from Step 4.2, 보통 1>"
```

- [ ] **Step 4.4: 검증**

Run:
```powershell
gh issue view $env:BITHUMB_ISSUE --repo mclayer/mctrader-market-bithumb --json number,title,state
```
Expected: `state: OPEN`, number = 1.

---

## Task 5: Epic Story file `docs/stories/MCT-98.md` 작성

**Files:**
- Create: `docs/stories/MCT-98.md`

- [ ] **Step 5.1: Epic Story file 작성**

Create file `docs/stories/MCT-98.md` with full content:

```markdown
---
story_key: MCT-98
story_issues:
  - repo: mclayer/mctrader-hub
    number: <EPIC_ISSUE>
status: phase:2-entry
---

# MCT-98: mctrader Docker-first Migration

- **Issue**: #<EPIC_ISSUE>
- **Status**: phase:2-entry
- **Trigger ADR**: codeforge ADR-033 (carrier_story CFP-128, 2026-05-07 Accepted)
- **Pilot reference**: mctrader-hub#119 + mctrader-data#11 (DONE 2026-05-07)

## 1. 사용자 요구사항 (verbatim)

> "이전에 작업하다 끊긴 게 있을텐데"
> "dockerization 관련이다"

세션 직전: codeforge plugin 의 ADR-033 (CFP-128) Accepted 후 mctrader 6-repo 가 Docker-first migration 을 follow-on Epic 의무로 받음. mctrader-data Pilot 종료 후 Epic governance state 가 engineering state 와 격차.

## 2. 도메인 해석

### 2.1 mctrader 6-repo shape 분석

| Repo | Shape | infra_strategy | Phase |
|---|---|---|---|
| mctrader-data | collector daemon (long-running) | docker_first | **1 (DONE)** |
| mctrader-engine | backtest one-shot CLI + paper daemon | docker_first | 3 |
| mctrader-web | multi-service (FastAPI + Streamlit + sqlite) | docker_first | 4 |
| mctrader-market | library (pure Python) | none | 5 (joint) |
| mctrader-market-bithumb | library + WS adapter | none | 5 (joint) |
| mctrader-hub | governance / docs (no runtime) | none | 5 (joint) |

### 2.2 Phase 분해 근거 (Codex review 합의)

- **Hybrid by shape (D2=C)**: deployable trio (data, engine, web) 와 library quartet (market, bithumb, hub) 가 review 부피 다름 — 동일 path 강제 ROI 0.
- **engine first (D3)**: data Pilot 와 가장 유사한 daemon shape. web 의 multi-service novel pattern 전에 reference 박제.
- **library = none (D5)**: 배포 표면 부재 → fake infra ownership ROI 0.

## 3. 관련 ADR

| ADR | 제목 | 본 Epic 내 역할 |
|---|---|---|
| codeforge ADR-033 | Docker-first Infra Engineering | trigger (carrier_story CFP-128) |
| ADR-009 | OHLCV 스키마 + Candle Protocol | §D12 amendment (Docker-first persistence: named volume + forward-only + DR backup) — Phase 2 entry |
| ADR-008 | (관련 시 추가) | TBD per phase |

## 4. 관련 코드 경로

### Phase 1 (mctrader-data, DONE)

- `Dockerfile` + `.dockerignore`
- `compose.yml`
- `src/mctrader_data/health_server.py`
- `src/mctrader_data/cli.py` (collect subcommand HealthServer wiring)
- `src/mctrader_data/collector.py` (HealthServer dependency injection)
- `tests/test_health_server.py` (4 TDD scenario)
- `.github/workflows/image-lint.yml` (hadolint)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`

### Phase 3+ (TBD per phase)

- mctrader-engine: `Dockerfile` + `compose.yml` (one-shot + daemon dual mode 검토)
- mctrader-web: `Dockerfile` + `compose.yml` (multi-service: api + web + sqlite volume)
- library quartet (market, bithumb, hub): `.claude/_overlay/project.yaml` `infra_strategy: none` 만

## 5. Acceptance Criteria

| ID | AC | 검증 phase |
|---|---|---|
| B1 | 6 repo 모두 `.claude/_overlay/project.yaml` `infra_strategy:` 명시 | Phase 5 종료 |
| B2 | deployable trio (data, engine, web) Docker artifact + healthcheck 박제 | Phase 4 종료 |
| B3 | library quartet (market, bithumb, hub) `infra_strategy: none` lint pass | Phase 5 종료 |
| B4 | mctrader-market-bithumb WS finding (#1) close 또는 별도 Story 처리 | Phase 5 종료 |
| B5 | EPIC-RESULTS-MCT-98.md 작성 + 회고 + 6 phase 결과 박제 | Phase 6 |

## 6. 외부 지식 배경

- codeforge plugin ADR-033 (Docker-first Infra Engineering) — InfraEngineerAgent default 출력 패턴
- Docker Compose v2 — `compose.yml` (legacy `docker-compose.yml` 대신)
- hadolint — Dockerfile lint
- python:3.12-slim — base image (uv 호환)
- Pilot reference 패턴: 2-stage build, non-root user, named volume, HEALTHCHECK directive

## 7. Phase plan

### Phase 1 — Pilot (mctrader-data) ✅ DONE

- 2026-05-07 merged
- mctrader-hub PR #119 (spec/plan)
- mctrader-data PR #11 (impl, 8 commits, 0.8.0→0.9.0)

### Phase 2 — Entry / bookkeeping ⬅ this PR

- Epic + Pilot Story (MCT-99) retroactive 등록
- ADR-009 §D12 amendment
- mctrader-market-bithumb#1 finding 등록 (Phase 5 blocker)

### Phase 3 — mctrader-engine sister (TBD MCT-100)

- 별도 brainstorming session — backtest one-shot + paper daemon Docker-first 패턴
- spec/plan + impl PR (mctrader-engine)
- entry 조건: Phase 2 entry merged + ADR-009 amendment land

### Phase 4 — mctrader-web sister (TBD MCT-101)

- 별도 brainstorming session — multi-service compose (FastAPI + Streamlit + sqlite volume)
- spec/plan + impl PR (mctrader-web)
- entry 조건: Phase 3 종료 + engine reference 박제

### Phase 5 — Library batch joint (TBD MCT-102)

- market + bithumb + hub 3 repo `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 추가
- bithumb 의 경우 mctrader-market-bithumb#1 finding fix Story 선행 (blocker)
- CFP-96 Phase 6b 패턴 (sister 일괄 sweep)
- entry 조건: Phase 4 종료 + bithumb#1 fix 또는 별도 Story 진행 중

### Phase 6 — Epic close

- `EPIC-RESULTS-MCT-98.md` 작성
- 회고 + 6 phase 결과 + cross-cutting finding + 후속 ADR 후보

## 8. Implementation Manifest (per phase)

### 8.1 Phase 1 (mctrader-data, DONE)

mctrader-data PR #11 8 commits:
1. `46dc5c6` HealthServer HTTP /health endpoint + 4 TDD scenarios
2. `d8bdb67` Dockerfile + .dockerignore (2-stage, non-root)
3. `be2e708` compose.yml (collector daemon, named volume, restart, healthcheck)
4. `609d5f1` project.yaml `infra_strategy: docker_first`
5. `7c0fd81` README "Docker deployment" 절 + systemd 자산 삭제 (BREAKING)
6. `78ffb64` `.github/workflows/image-lint.yml` (hadolint)
7. `d1f2910` tests/integration/README.md (5 manual smokes)
8. `645e476` pyproject 0.8.0 → 0.9.0 + CHANGELOG.md

### 8.2 Phase 2 (this PR)

본 PR 의 commit:
- `<commit-1>` `[MCT-98] docs(story): Epic Story file + Phase 1-6 plan`
- `<commit-2>` `[MCT-99] docs(story): Pilot Story file + §11 retrospective`
- `<commit-3>` `[MCT-98] docs(adr): ADR-009 §D12 amendment — named volume + forward-only + DR`

### 8.3-8.6 Phase 3-6 (TBD)

각 phase merge 시 commit hash + PR # 추가.

## 9. Evidence

### Phase 1 evidence (DONE)

- 186 pytest PASS (mctrader-data, 기존 182 + 신규 4 test_health_server)
- hadolint Dockerfile = warning 0
- `docker compose config` syntax PASS
- `docker build` 성공 + image entrypoint smoke (--help / collect / backfill / status)
- `bash scripts/check-container-strategy.sh` PASS
- actionlint image-lint.yml clean
- ruff check PASS (health_server.py + 영향받은 file)

### Phase 2 evidence (this PR)

- 본 PR merge 시 추가:
  - phase-gate-mergeable green
  - Codex 7-area review push-back 처리 trace (agentId `af61a4c87e9d7906c`)
  - Sonnet decider 합성 commit (있을 시)

### Phase 3-6 evidence

각 phase merge 시 추가.

## 10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| Phase 2 scope | C 4 artifact 묶음 | A retro only — engineering/governance 격차 유지 / B retro+Bithumb — Epic registration 누락 / D + first sister start — review 부피 폭증 |
| Sequencing | C Hybrid by shape | Mode A serial — library 5 phase 소진 ROI 0 / Mode B 5-parallel — shape 다양성으로 review 정합성 약 |
| First sister | engine | web — multi-service novel pattern, Pilot reference 약 / library batch first — deployable runtime 경험 박제 약 |
| Bithumb handling | B issue + blocker | A defer-only — Phase 5 진입 시 healthy signal 부정직 / C inline fix — Epic scope creep |
| infra_strategy 일관성 | A library = none | B 일괄 docker_first — fake infra ownership ROI 0 / C hybrid (hub만 docker_first) — 일관성 약 |
| ADR-009 amendment 시점 | A 지금 | B post-Epic — sister 들이 패턴 invent 위험 / C defer — DR 어휘 tribal knowledge 화 |
| 등록 mechanic | A 둘 다 retroactive | B Epic only — Pilot Story 박제 누락 / C skip — governance trace 단절 |
| Epic 명칭 | "Docker-first Migration" | "Containerization" — 모호 / "Dockerization" — 비공식 |

## 11. 회고

본 §11 은 Phase 6 (Epic close) 시점에 박제. 항목:

- 6 phase 별 실제 vs 계획 시간 비교
- Hybrid by shape sequencing 의 ROI 실측
- Pilot reference 가 sister rollout 들에 얼마나 reuse 됐는지
- ADR-009 §D12 amendment 의 5 sister 적용 정합성
- Bithumb finding fix 가 Phase 5 timeline 에 미친 영향
- 후속 ADR 후보 (Phase 6 cross-cutting finding 정리)

(Phase 2 entry 시점 placeholder — Phase 6 시 보강.)
```

저장 시 `<EPIC_ISSUE>` 두 곳 (frontmatter + Issue link) 모두 Task 2 Step 2.4 환경 변수로 치환. 본 step 은 file 작성만 — commit 은 Step 5.2.

- [ ] **Step 5.2: Epic Story file 작성 검증**

Run:
```powershell
Get-Content docs/stories/MCT-98.md -TotalCount 10
grep -c "^## " docs/stories/MCT-98.md
```
Expected: frontmatter 정상 (`story_key: MCT-98`), section 11개 (## 1. ~ ## 11.).

- [ ] **Step 5.3: Epic Story file commit**

Run:
```powershell
git add docs/stories/MCT-98.md
git commit -m "[MCT-98] docs(story): Epic Story file + Phase 1-6 plan"
```
Expected: commit 성공.

---

## Task 6: Pilot Story file `docs/stories/MCT-99.md` 작성

**Files:**
- Create: `docs/stories/MCT-99.md`

- [ ] **Step 6.1: Pilot Story file 작성**

Create file `docs/stories/MCT-99.md` with full content:

```markdown
---
story_key: MCT-99
story_issues:
  - repo: mclayer/mctrader-hub
    number: <PILOT_ISSUE>
status: complete
---

# MCT-99: mctrader-data Docker-first Containerization (Pilot, P1 retroactive)

- **Issue**: #<PILOT_ISSUE>
- **Status**: complete (Phase 1 DONE 2026-05-07)
- **Parent Epic**: mctrader-hub#<EPIC_ISSUE> — mctrader Docker-first Migration
- **Trigger**: codeforge ADR-033 (CFP-128 Accepted 2026-05-07)

> **Retroactive registration**: Pilot 구현 이미 merged. 본 Story file 은 governance anchor + §11 retrospection 박제용.

## 1. 사용자 요구사항 (verbatim, 2026-05-07 Pilot session)

> "codeeforge의 변경에 따라 mctrader에서 작업해야할 내용이 있다. docker containerize에 관한 부분이다."
> "현재 systemd 작업은 수행하고 있지 않으니 편하게 stop해도 된다."

## 2. 도메인 해석

### 2.1 Pilot scope

mctrader-data repo 의 Docker-first 전환. collector daemon 1 service compose. backfill 은 동일 image 의 ad-hoc `compose run` 처리. systemd 자산 일괄 삭제 (production 미가동 확인).

### 2.2 ADR-033 §7.4 OpRiskArch 4 항목 박제 의무

- restart policy
- volume DR
- health check tuning
- network mode

→ 5 sister rollout 의 reference 패턴 만들기.

## 3. 관련 ADR

- codeforge ADR-033 (carrier_story CFP-128) — Pilot trigger
- ADR-009 — OHLCV 스키마 (Pilot §11 회고에서 §D12 amendment 후보 박제 → Phase 2 entry 에서 land)

## 4. 관련 코드 경로 (mctrader-data)

### 신규
- `Dockerfile` (2-stage python:3.12-slim, non-root mctrader UID 1001)
- `.dockerignore` (codeforge cli-tool-minimal 패턴 + `data/` 추가)
- `compose.yml` (collector daemon 1 service, named volume `mctrader_data`, restart unless-stopped, healthcheck)
- `src/mctrader_data/health_server.py` (HTTP /health endpoint, ws_state 기반 200/503)
- `tests/test_health_server.py` (4 TDD scenario)
- `.github/workflows/image-lint.yml` (hadolint job)
- `tests/integration/README.md` (5 manual smoke 절차)

### 수정
- `src/mctrader_data/cli.py` (collect subcommand HealthServer wiring)
- `src/mctrader_data/collector.py` (HealthServer dependency injection)
- `.claude/_overlay/project.yaml` (`infra_strategy: docker_first`)
- `README.md` (systemd 절 → Docker 절 전면 교체)
- `pyproject.toml` (0.8.0 → 0.9.0)
- `CHANGELOG.md` (`[0.9.0]` BREAKING entry)

### 삭제
- `deploy/mctrader-collector.service`
- `deploy/README.md`
- `deploy/` 디렉터리

## 5. Acceptance Criteria (Pilot, met 2026-05-07)

| ID | AC | 결과 |
|---|---|---|
| A1 | Dockerfile 2-stage build + non-root user | ✅ |
| A2 | compose.yml 1 service + named volume + restart + healthcheck | ✅ |
| A3 | HealthServer HTTP /health endpoint (ws_state 200/503) | ✅ (4 TDD test pass) |
| A4 | systemd 자산 삭제 (BREAKING) | ✅ |
| A5 | `infra_strategy: docker_first` lint pass | ✅ (`scripts/check-container-strategy.sh` PASS) |
| A6 | hadolint warning 0 | ✅ |
| A7 | `docker compose config` syntax PASS | ✅ |
| A8 | image entrypoint smoke (--help / collect / backfill / status) | ✅ |
| A9 | 186 pytest PASS (기존 182 + 신규 4) | ✅ |

## 7. 결정점 (Pilot D1-D7, 모두 사용자 승인)

| Decision | 채택 | 거절 |
|---|---|---|
| D1 응답 경로 | Dockerization Epic 진입 | 방어적 선언 (legacy_systemd) / 단계적 일부 |
| D2 Epic sequencing | Pilot → Rollout (1 + 5) | Mode B Joint Epic / repo-by-repo |
| D3 Pilot 후보 | mctrader-data | mctrader-web / mctrader-engine |
| D4 systemd 처리 | Docker-only 전환 (unit 삭제) | Docker primary + systemd 보존 |
| D5 Compose surface | collector daemon 1 service | + backfill profiles / + cold-archive sidecar |
| D6 Pilot depth | Approach 1 — baseline + lint-only CI | Approach 2 (ghcr publish) / Approach 3 (distroless) |
| D7 Build target | linux/amd64 단일 | Multi-arch buildx |

### Amendment 1 (Pilot session 중)

Task 1 진입 시 기존 `heartbeat.py` 의 HA active-active 패턴 (`<root>/market/manifest/heartbeat-<node_id>.json`, MCT-91/93)이 plan 의 단순 `.heartbeat` mtime 가정과 불일치 발견. 사용자 결정: **HTTP `/health` API endpoint 채택** (webapp-minimal 패턴 정합 + 5 sister rollout reference 강화).

## 8.5 Implementation Manifest (mctrader-data PR #11, 8 commits)

| # | commit | 내용 |
|---|---|---|
| 1 | `46dc5c6` | HealthServer HTTP /health endpoint + TDD 4 시나리오 |
| 2 | `d8bdb67` | Dockerfile + .dockerignore (2-stage, python:3.12-slim, non-root mctrader UID 1001) |
| 3 | `be2e708` | compose.yml (collector daemon, named volume, restart unless-stopped, healthcheck) |
| 4 | `609d5f1` | project.yaml `infra_strategy: docker_first` (codeforge lint PASS) |
| 5 | `7c0fd81` | README "Docker deployment" 절 + systemd 자산 삭제 (BREAKING) |
| 6 | `78ffb64` | `.github/workflows/image-lint.yml` (hadolint) |
| 7 | `d1f2910` | tests/integration/README.md (5 manual smokes) |
| 8 | `645e476` | pyproject 0.8.0 → 0.9.0 + CHANGELOG.md |

## 9. Evidence

- 186 pytest PASS (기존 182 + 신규 4 test_health_server)
- hadolint Dockerfile = warning 0
- `docker compose config` syntax PASS
- `docker build` 성공 + image entrypoint smoke (--help / collect / backfill / status 모두 노출)
- `bash scripts/check-container-strategy.sh` PASS
- actionlint image-lint.yml clean
- ruff check PASS (health_server.py + 영향받은 file)
- mctrader-data PR #11 admin merge 2026-05-07T07:54:14Z

## 10. 거절된 대안

(§7 결정점 의 거절 column 참조 — Pilot session 박제 그대로)

## 11. 회고 (Phase 2+ entry 조건 + 5 sister 분석)

### 11.1 Pilot 성과 요약

- ADR-033 §7.4 4 항목 박제 성공:
  - **restart policy**: `unless-stopped` (forward-only, 데이터 누락 회피)
  - **volume DR**: named volume `mctrader_data` + backup recipe (ADR-009 §D12 박제 의무)
  - **health check**: HTTP /health endpoint, interval 30s, start_period 60s, retries 3
  - **network mode**: bridge default, 호스트 port 매핑 0
- HealthServer pattern = 5 sister rollout 의 reference. webapp-minimal 패턴과도 정합.
- BREAKING 변경 (systemd 자산 삭제) 사용자 사전 승인 — production 미가동 검증 후.

### 11.2 Pilot 발견

#### 11.2.1 Bithumb WS schema mismatch (별도 issue 박제)

Live test 진입 시 mctrader-market-bithumb WS adapter schema 결함 2건:
- `orderbookdepth missing symbol` (`ws_mapping.py:90`)
- `invalid event_time: '2026-05-07 16:38:49.198650'` (`ws_mapping.py:33`)

→ mclayer/mctrader-market-bithumb#1 (Phase 2 entry 에서 등록, Phase 5 bithumb sister rollout blocker)

#### 11.2.2 ADR-009 §D12 amendment 의무

Pilot 의 named volume + forward-only invariant + DR backup recipe 가 ADR-009 amendment 후보 → Phase 2 entry 에서 land (sister rollout 진입 전 의무).

### 11.3 Phase 2+ entry 조건 (Codex 7-area review agentId `af61a4c87e9d7906c`)

| 결정 | 합의 | 근거 |
|---|---|---|
| D1 carry-over scope | C 4 artifact 묶음 | governance state 가 engineering state 뒤따라야 |
| D2 sequencing | C Hybrid by shape | deployable trio + library quartet 분리, review 부피 정합 |
| D3 first sister | engine | data Pilot 와 가장 유사한 daemon shape |
| D4 Bithumb 처리 | B issue + blocker | WS schema = correctness, containerization 분리 |
| D5 library infra_strategy | A `none` | 배포 표면 부재, fake infra ROI 0 |
| D6 ADR-009 amendment | A 지금 | sister rollout 들이 패턴 복사 전 박제 |
| D7 등록 mechanic | A 둘 다 retroactive | git history 외 governance anchor 의무 |
| D8 Epic 명칭 | "Docker-first Migration" | ADR-033 정책 어휘 정합 |

### 11.4 5 sister shape 분석

| Repo | Shape | infra_strategy | Phase | Risk |
|---|---|---|---|---|
| mctrader-engine | backtest one-shot CLI + paper daemon | docker_first | 3 | medium — one-shot + daemon 이중 mode 검토 의무 |
| mctrader-web | multi-service (FastAPI + Streamlit + sqlite volume) | docker_first | 4 | high — multi-service novel pattern, sqlite volume DR 분리 vs 통합 결정 |
| mctrader-market | library (pure Python, Candle Protocol) | none | 5 (joint) | low — `infra_strategy: none` lint pass 만 |
| mctrader-market-bithumb | library + WS adapter | none | 5 (joint) | medium — #1 WS finding fix 선행 의무 |
| mctrader-hub | governance / docs (no runtime) | none | 5 (joint) | low — `infra_strategy: none` lint pass 만 |

### 11.5 본 §11 박제 시점

- Phase 2 entry PR (mctrader-hub `docs/MCT-98-MCT-99-phase-2-entry`) 안에 commit
- Pilot Story issue MCT-99 (mctrader-hub) close = Phase 2 entry PR merge 시점
- Epic Story issue MCT-98 (mctrader-hub) = Phase 6 close 시점까지 OPEN
```

저장 시 `<EPIC_ISSUE>` (3곳: frontmatter / Parent Epic / 11.4 link), `<PILOT_ISSUE>` (frontmatter + Issue link) 모두 환경 변수로 치환.

- [ ] **Step 6.2: Pilot Story file 작성 검증**

Run:
```powershell
Get-Content docs/stories/MCT-99.md -TotalCount 10
grep -c "^## " docs/stories/MCT-99.md
grep -c "^### 11\." docs/stories/MCT-99.md
```
Expected: frontmatter 정상 (`story_key: MCT-99`), section 9개 (1, 2, 3, 4, 5, 7, 8.5, 9, 10, 11), §11 sub-section 5개 (11.1~11.5).

- [ ] **Step 6.3: Pilot Story file commit**

Run:
```powershell
git add docs/stories/MCT-99.md
git commit -m "[MCT-99] docs(story): Pilot Story file + §11 retrospective"
```
Expected: commit 성공.

---

## Task 7: ADR-009 §D12 Amendment

**Files:**
- Modify: `docs/adr/ADR-009-ohlcv-schema.md`

- [ ] **Step 7.1: Amendment History entry 추가**

Edit `docs/adr/ADR-009-ohlcv-schema.md` line 18 다음에 신규 entry 추가:

old_string:
```
- 2026-05-05 — §D2.1 (Active-Active HA `node=` partition + dedup contract anchor) + §D10.7 (T2 tick logical key) + §D11.8 (T3 orderbook logical key) NEW. MCT-X1 Phase 1 (Collector HA active-active multi-node + shared storage).
```

new_string:
```
- 2026-05-05 — §D2.1 (Active-Active HA `node=` partition + dedup contract anchor) + §D10.7 (T2 tick logical key) + §D11.8 (T3 orderbook logical key) NEW. MCT-X1 Phase 1 (Collector HA active-active multi-node + shared storage).
- 2026-05-08 — §D12 (Docker-first persistence: named volume `mctrader_data` + forward-only invariant + DR backup recipe) NEW. MCT-98 Phase 2 entry (mctrader Docker-first Migration Epic, Pilot reference 박제).
```

- [ ] **Step 7.2: §D12 section 추가 (file 끝에 append)**

Edit `docs/adr/ADR-009-ohlcv-schema.md` — 마지막 section 다음에 신규 §D12 추가. 정확한 insert 위치는:

먼저 현재 마지막 §Dxx section 위치 식별:
```powershell
grep -n "^### D[0-9]" docs/adr/ADR-009-ohlcv-schema.md | Select-Object -Last 5
```

마지막 §Dxx section (또는 그 다음 section) 다음에 아래 텍스트 append:

```markdown

### D12. Docker-first persistence (Amendment 2026-05-08, MCT-98 Phase 2 entry)

mctrader-data Pilot (MCT-99, 2026-05-07 merged) 의 Docker-first 전환 박제 패턴. 5 sister rollout (mctrader-engine / -web — deployable trio) 의 reference.

#### D12.1 Named volume `mctrader_data` 영속화

mctrader-data collector daemon 의 OHLCV / tick / orderbook 데이터는 Docker named volume 에 보관:

| 항목 | 값 |
|---|---|
| volume name | `mctrader_data` |
| container mount | `/var/lib/mctrader/data` |
| env | `MCTRADER_DATA_ROOT=/var/lib/mctrader/data` |
| compose driver | local (default, compose.yml 미명시) |

codeforge ADR-033 §결정 6 (named volume 권장) 정합. host bind mount 거절 — Windows host path mapping 비호환 + production Linux host 와 dev Windows host 의 volume 패턴 통일.

#### D12.2 Forward-only invariant 명시

Bithumb public API 는 ticks/orderbook 의 historical replay 를 제공하지 않음. mctrader-data collector 는 forward-only:

- restart 시 데이터 누락 회피 → compose `restart: unless-stopped`
- container kill / volume detach 동안의 데이터 = 영구 손실
- backfill = candle (OHLCV) 만 가능, ticks/orderbook 은 backfill 없음
- HA active-active partition (§D2.1) 가 single-node 데이터 누락 회피의 일부 — node 별 forward-only 보장 + scan-side merge

본 invariant 는 collector lifecycle 의 hard constraint. 5 sister rollout 시 동일 패턴 적용.

#### D12.3 DR backup recipe (volume snapshot)

표준 backup 명령 (PowerShell, mctrader-data Pilot reference):

```powershell
# Backup
$timestamp = Get-Date -Format yyyyMMdd_HHmmss
docker run --rm `
  -v mctrader_data:/source:ro `
  -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_data_${timestamp}.tar.gz -C /source .

# Restore
docker run --rm `
  -v mctrader_data:/dest `
  -v ${PWD}:/backup `
  alpine tar xzf /backup/mctrader_data_<TIMESTAMP>.tar.gz -C /dest
```

bash 등가 명령:

```bash
# Backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker run --rm \
  -v mctrader_data:/source:ro \
  -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_data_${TIMESTAMP}.tar.gz -C /source .

# Restore
docker run --rm \
  -v mctrader_data:/dest \
  -v "$(pwd):/backup" \
  alpine tar xzf /backup/mctrader_data_<TIMESTAMP>.tar.gz -C /dest
```

5 sister rollout (deployable trio: data, engine, web) 의 volume backup 표준 reference.

#### D12.4 후속 자동화 (별도 Story)

- volume backup cron / scheduled snapshot 자동화 — Phase 6 또는 별도 ops Story (Pilot F5/O4 carry-over)
- ghcr.io publish 후 image-ref + volume data lineage tracking — Pilot F1-F3 carry-over
- multi-host volume replication (production scale-out 시점) — TBD

#### D12.5 의무

본 §D12 의 invariant + recipe 는 5 sister rollout 시점에 deployable repo (data, engine, web) 가 reference 의무. library quartet (market, bithumb, hub) 는 `infra_strategy: none` 으로 본 §D12 미적용.
```

- [ ] **Step 7.3: ADR-009 amendment 검증**

Run:
```powershell
grep -n "2026-05-08" docs/adr/ADR-009-ohlcv-schema.md
grep -n "^### D12" docs/adr/ADR-009-ohlcv-schema.md
grep -c "^#### D12\." docs/adr/ADR-009-ohlcv-schema.md
```
Expected:
- `2026-05-08` line — Amendment History 1건 + §D12.x 부분 (총 2~3 라인)
- `### D12` section 1개
- `#### D12.` sub-section 5개 (D12.1, D12.2, D12.3, D12.4, D12.5)

- [ ] **Step 7.4: ADR-009 amendment commit**

Run:
```powershell
git add docs/adr/ADR-009-ohlcv-schema.md
git commit -m "[MCT-98] docs(adr): ADR-009 §D12 amendment — Docker-first persistence"
```
Expected: commit 성공.

---

## Task 8: Branch push + PR open

**Files:** N/A (git + gh)

- [ ] **Step 8.1: Local commit 검증**

Run:
```powershell
git log --oneline origin/main..HEAD
```
Expected: 4 commit (spec + Epic Story + Pilot Story + ADR amendment).

- [ ] **Step 8.2: Branch push**

Run:
```powershell
git push -u origin docs/MCT-98-MCT-99-phase-2-entry
```
Expected: branch 정상 push.

- [ ] **Step 8.3: PR body file 작성**

Create file `c:\tmp\mct-98-pr-body.md`:

```markdown
## Summary

mctrader Docker-first Migration Epic (MCT-98) Phase 2 entry — bookkeeping + governance docs + ADR-009 amendment + Bithumb finding cross-link. Pilot (mctrader-data, MCT-99 retroactive) 종료 후 governance state 정렬, 5 sister rollout (Phase 3-5) 진입 전 의무.

**4 commits (doc only — code change 0)**:
1. `366aa48` Spec — Phase 2 entry design (8 결정 + Codex 7-area review trace)
2. `<commit-2>` Epic Story file `docs/stories/MCT-98.md` (Phase 1-6 plan, AC B1-B5)
3. `<commit-3>` Pilot Story file `docs/stories/MCT-99.md` (retroactive, §11 retrospective)
4. `<commit-4>` ADR-009 §D12 amendment (named volume + forward-only + DR backup recipe)

## Linked issues

- Epic: mctrader-hub#$env:MCT_98_ISSUE
- Pilot Story: mctrader-hub#$env:MCT_99_ISSUE (retroactive, P1 DONE)
- Bithumb finding: mclayer/mctrader-market-bithumb#$env:BITHUMB_ISSUE (Phase 5 blocker)

## Phase plan (Epic 6 phase)

| Phase | Status | Reference |
|---|---|---|
| 1 — Pilot mctrader-data | ✅ DONE 2026-05-07 | mctrader-hub#119 + mctrader-data#11 |
| 2 — Entry / bookkeeping | ⬅ this PR | (본 PR) |
| 3 — engine sister | TBD | MCT-100 candidate |
| 4 — web sister | TBD | MCT-101 candidate |
| 5 — library batch joint | TBD | MCT-102 candidate (market+bithumb+hub) |
| 6 — Epic close | TBD | EPIC-RESULTS-MCT-98.md |

## Codex 7-area review (Phase 2 entry)

agentId `af61a4c87e9d7906c` — 8 결정 합의:
- D1=C 4 artifact 묶음
- D2=C Hybrid by shape (deployable trio engine→web; library quartet joint)
- D3=engine first
- D4=B Bithumb issue+blocker (Epic inline fix 안 함)
- D5=A library = `infra_strategy: none`
- D6=A ADR-009 amendment 지금
- D7=A 둘 다 retroactive
- D8="Docker-first Migration"

## Test Plan

- [x] Spec self-review (placeholder / 일관성 / scope / ambiguity 통과 + minor 4건 inline fix)
- [ ] DesignReview (Codex 7-area review on PR scope, doc-only)
- [ ] Sonnet decider 합성 (push-back 처리)
- [ ] codeforge phase-gate-mergeable green

## Spec / Plan reference

- spec: `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase2-entry-design.md`
- plan: `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase2-entry-plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

`<commit-2>` `<commit-3>` `<commit-4>` 는 실제 commit hash 로 치환:
```powershell
git log --oneline -4
```

- [ ] **Step 8.4: PR open**

Run:
```powershell
gh pr create `
  --repo mclayer/mctrader-hub `
  --base main `
  --head docs/MCT-98-MCT-99-phase-2-entry `
  --title "[MCT-98/99] docs: Phase 2 entry — Epic + Pilot Story + ADR-009 §D12 amendment" `
  --body-file c:\tmp\mct-98-pr-body.md
```
Expected: PR URL 출력. 번호 기록 (`$PR_NUMBER`).

- [ ] **Step 8.5: PR 검증**

Run:
```powershell
gh pr view $PR_NUMBER --repo mclayer/mctrader-hub --json number,title,state,mergeable
```
Expected: `state: OPEN`, `mergeable: MERGEABLE` 또는 `UNKNOWN` (CI 진행 중).

---

## Task 9: Codex 7-area review

**Files:** N/A (review subagent dispatch)

- [ ] **Step 9.1: Codex review packet 준비**

Review scope: doc-only PR. 가중치:
- governance 정합 (Epic Story file + Pilot Story file + ADR amendment 의 cross-reference 정확성)
- ADR amendment correctness (codeforge ADR-033 §결정 정합 + ADR-009 기존 §D1-§D11 와 conflict 부재)
- retrospection 완전성 (§11.1-§11.5)
- issue cross-link 정확성 (Epic ↔ Pilot Story ↔ Bithumb finding)
- 거절된 대안 trace 박제 (D1-D8)
- AC B1-B5 검증 가능성

Review packet 에 포함:
- spec file path
- plan file path
- Story file path × 2
- ADR amendment diff
- 3 issue body
- PR URL

- [ ] **Step 9.2: Codex agent dispatch**

Use `codex:codex-rescue` agent:

```
Agent({
  description: "Codex 7-area review of Phase 2 entry doc PR",
  subagent_type: "codex:codex-rescue",
  prompt: <see Step 9.3>
})
```

- [ ] **Step 9.3: Review prompt**

Review prompt content (Codex 에 dispatch):

> You are Codex GPT-5 doing a 7-area review of a doc-only PR for mctrader Docker-first Migration Epic Phase 2 entry. Repo: mclayer/mctrader-hub. PR: <PR_URL>. Branch: docs/MCT-98-MCT-99-phase-2-entry.
>
> Files in scope:
> - `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase2-entry-design.md` (spec, commit `366aa48`)
> - `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase2-entry-plan.md` (plan)
> - `docs/stories/MCT-98.md` (Epic Story, NEW)
> - `docs/stories/MCT-99.md` (Pilot Story retroactive, NEW)
> - `docs/adr/ADR-009-ohlcv-schema.md` (Amendment History + §D12 NEW)
>
> Issues registered:
> - mclayer/mctrader-hub#<EPIC_ISSUE> (Epic MCT-98)
> - mclayer/mctrader-hub#<PILOT_ISSUE> (Pilot Story MCT-99 retroactive)
> - mclayer/mctrader-market-bithumb#<BITHUMB_ISSUE> (WS schema finding, Phase 5 blocker)
>
> 7-area review:
> 1. Governance state 정합 (Epic ↔ Pilot Story ↔ Bithumb finding cross-link 정확)
> 2. ADR-009 §D12 correctness (codeforge ADR-033 §결정 정합 + 기존 §D1-§D11 conflict 부재 + named volume + forward-only + DR backup)
> 3. Retrospection 완전성 (§11.1-§11.5: Pilot 성과 + 발견 + Phase 2+ 조건 + 5 sister 분석 + 박제 시점)
> 4. AC B1-B5 검증 가능성 (Phase 6 close 시점 검증 가능 여부)
> 5. 거절된 대안 trace (Pilot D1-D7 + Phase 2 entry D1-D8 모두 박제)
> 6. Phase 분해 정확성 (Phase 1-6 entry 조건 + Story key candidate)
> 7. 문서 cross-reference 정확성 (spec ↔ plan ↔ Story file ↔ ADR ↔ issue)
>
> 출력: per-area finding (severity HIGH/MEDIUM/LOW + concrete fix). Top 3 push-back. Defer 후보 명시.

- [ ] **Step 9.4: Codex review 결과 보존**

Codex review 결과 → `c:\tmp\codex-review-mct-98-phase-2-entry.md` 에 저장 (Sonnet decider 합성용).

---

## Task 10: Sonnet decider 합성 (Codex push-back 처리)

**Files:** N/A or fix-back commits (conditional)

- [ ] **Step 10.1: Codex push-back 분류**

Codex review 결과 항목별 판정:
- HIGH severity → 즉시 fix-back commit
- MEDIUM → 본 PR 안에서 fix 또는 defer (별도 issue / 별도 phase)
- LOW → defer (memory 박제 또는 next phase)

- [ ] **Step 10.2: Fix-back commit (필요 시)**

각 HIGH push-back 항목 별로 atomic commit:

Run:
```powershell
# 예시: §D12.3 backup recipe 의 PowerShell + bash dual command 정확성 fix
git add docs/adr/ADR-009-ohlcv-schema.md
git commit -m "[MCT-98] docs(adr): fix §D12.3 backup recipe per Codex review (HIGH)"
git push origin docs/MCT-98-MCT-99-phase-2-entry
```

- [ ] **Step 10.3: Sonnet decider 합성 commit**

전체 push-back 처리 trace 박제 commit (fix 가 1개라도 있는 경우):

PR comment 또는 별도 commit message 안에 Sonnet 합성 요약:
```
Codex review push-back 처리:
- HIGH-1: <항목> → fix commit <hash>
- MEDIUM-1: <항목> → defer (별도 issue #<N>)
- LOW-1: <항목> → memory 박제
```

---

## Task 11: CI watch + admin merge

**Files:** N/A

- [ ] **Step 11.1: CI watch (foreground polling)**

Run (foreground polling — memory feedback `no_background_watch` 정합):
```powershell
gh pr checks $PR_NUMBER --repo mclayer/mctrader-hub --watch
```

memory feedback `ci_terminal_states_classify` 정합 — terminal state 분류:
- SUCCESS → Step 11.2 진행
- FAILURE / ACTION_REQUIRED / BLOCKED → 즉시 분류 + 처리 (codeforge phase-gate doc-only fast-pass label 부착 또는 fix)

- [ ] **Step 11.2: Admin merge (memory feedback `admin_merge_autonomy` 정합)**

CI green 또는 phase-gate-mergeable green 후 즉시 admin merge:

Run:
```powershell
gh pr merge $PR_NUMBER --repo mclayer/mctrader-hub --admin --squash --delete-branch
```
Expected: merge 성공, branch 삭제, PR closed.

- [ ] **Step 11.3: Merge 검증**

Run:
```powershell
gh pr view $PR_NUMBER --repo mclayer/mctrader-hub --json state,mergedAt
git checkout main
git pull origin main
git log --oneline -5
```
Expected: PR `state: MERGED`, main 의 latest commit 에 본 PR squash commit 포함.

---

## Task 12: Post-merge — Pilot Story issue close + memory update

**Files:** N/A (issue ops + memory)

- [ ] **Step 12.1: Pilot Story issue MCT-99 close (Phase 1 DONE 박제)**

Run:
```powershell
gh issue close $env:MCT_99_ISSUE `
  --repo mclayer/mctrader-hub `
  --reason completed `
  --comment "Phase 1 (Pilot mctrader-data) DONE 2026-05-07. §11 retrospective 박제 완료 via mctrader-hub PR #$PR_NUMBER (merged 2026-05-08). Epic MCT-98 (#$env:MCT_98_ISSUE) Phase 2 entry 종료."
```

- [ ] **Step 12.2: Epic issue MCT-98 body update (Phase 2 entry DONE 표기)**

Epic issue body 의 Phase plan 표:
- Phase 2 status `⬅ this issue 의 phase` → `✅ DONE 2026-05-08`
- 본 PR # link 추가

Run:
```powershell
gh issue edit $env:MCT_98_ISSUE --repo mclayer/mctrader-hub --body-file <updated-body-file>
```
또는 GitHub web UI 직접 edit.

- [ ] **Step 12.3: Memory 업데이트**

mctrader 의 auto memory `project_codeforge_debut.md` 또는 별도 `project_dockerization_epic.md` 작성:

신규 memory file `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\project_dockerization_epic.md` 작성:

```markdown
---
name: mctrader Dockerization Epic state — Phase 1+2 done
description: mctrader Docker-first Migration Epic (MCT-98) state, Phase 1 Pilot done + Phase 2 entry done, Phase 3-6 TBD
type: project
---

mctrader Docker-first Migration Epic (mctrader-hub#<EPIC_ISSUE> = MCT-98) Phase 1+2 종료 (2026-05-08).

## State

- Phase 1 (Pilot mctrader-data) DONE 2026-05-07 — mctrader-hub#119 + mctrader-data#11
- Phase 2 entry DONE 2026-05-08 — mctrader-hub#$PR_NUMBER (Epic MCT-98 + Pilot Story MCT-99 retroactive + ADR-009 §D12 + Bithumb finding cross-link)
- Phase 3 mctrader-engine TBD — MCT-100 candidate
- Phase 4 mctrader-web TBD — MCT-101 candidate (multi-service compose)
- Phase 5 library batch (market+bithumb+hub joint) TBD — MCT-102 candidate (`infra_strategy: none`)
- Phase 6 Epic close TBD — EPIC-RESULTS-MCT-98.md

## Pilot leftover finding

mclayer/mctrader-market-bithumb#1 — WS schema mismatch (Phase 5 bithumb sister rollout blocker, fix 별도 Story)

## ADR amendments

- ADR-009 §D12 (Docker-first persistence: named volume `mctrader_data` + forward-only invariant + DR backup recipe) — Phase 2 entry 박제

## Codex review trace

- Phase 2 entry: agentId `af61a4c87e9d7906c` (8 결정 합의 — D1-D8)

## 다음 phase entry 조건

- Phase 3 (engine): Phase 2 entry merged + ADR-009 amendment land → 별도 brainstorming session
- Phase 4 (web): Phase 3 종료 + engine reference 박제
- Phase 5 (library batch): Phase 4 종료 + bithumb#1 fix 또는 별도 Story 진행 중
```

`MEMORY.md` 에도 entry 추가:

Run:
```powershell
# MEMORY.md 의 마지막 line 다음에 entry 추가
Add-Content -Path C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\MEMORY.md -Value "- [Dockerization Epic state](project_dockerization_epic.md) — MCT-98 Phase 1+2 done, Phase 3 (engine) TBD"
```

- [ ] **Step 12.4: Final 검증**

Run:
```powershell
# Pilot Story 닫혔는지
gh issue view $env:MCT_99_ISSUE --repo mclayer/mctrader-hub --json state
# Epic OPEN 유지
gh issue view $env:MCT_98_ISSUE --repo mclayer/mctrader-hub --json state
# Bithumb finding OPEN 유지
gh issue view $env:BITHUMB_ISSUE --repo mclayer/mctrader-market-bithumb --json state
# main branch 최신 commit
git log --oneline -3
```
Expected:
- MCT-99 `state: CLOSED`
- MCT-98 `state: OPEN`
- Bithumb finding `state: OPEN`
- main 최상단 = 본 PR squash commit

---

## 종료 조건

- [ ] 4 commit + 1 spec commit (총 5) → 1 PR squash merge
- [ ] 3 issue 등록 (Epic + Pilot Story + Bithumb finding) cross-link 정합
- [ ] ADR-009 §D12 amendment land
- [ ] phase-gate-mergeable green
- [ ] Codex 7-area review 처리 trace 박제
- [ ] Pilot Story (MCT-99) close + Epic (MCT-98) Phase 2 표기
- [ ] Memory 업데이트 (`project_dockerization_epic.md` + MEMORY.md entry)

본 plan 종료 = mctrader Docker-first Migration Epic Phase 2 entry 완료. Phase 3 (engine) 은 별도 brainstorming session 으로 진행.
