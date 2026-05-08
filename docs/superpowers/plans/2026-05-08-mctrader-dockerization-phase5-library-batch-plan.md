# mctrader Docker-first Migration — Phase 5 Library Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader Docker-first Migration Epic (MCT-98 #120) Phase 5 — library/governance 3 repo (`mctrader-market`, `mctrader-market-bithumb`, `mctrader-hub`) 의 `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 명시. codeforge `check-container-strategy.sh` lint 가 SKIP 으로 정확 분류되도록 declarative governance 박제.

**Architecture:** 3 PR joint sweep (CFP-96 Phase 6b 패턴). mctrader-hub PR 가 anchor (Story file `MCT-102.md` + hub project.yaml 1줄), 2 sister PR 가 child (각 1줄). 각 repo 로컬 `check-container-strategy.sh` 실행해 SKIP 출력 PR evidence 로 capture. Codex 7-area review 1회 (mctrader-hub PR anchor).

**Tech Stack:** YAML, git, GitHub CLI (`gh`), bash (codeforge `scripts/check-container-strategy.sh`).

**Working repos:**
- `c:\workspace\mclayer\mctrader-hub\` (anchor, Story file + own project.yaml)
- `c:\workspace\mclayer\mctrader-market\`
- `c:\workspace\mclayer\mctrader-market-bithumb\`

**Lint script source**: `c:\workspace\mclayer\plugin-codeforge\scripts\check-container-strategy.sh` (Phase 5 verification 시 사용; consumer repo 들에는 미설치 → plugin-codeforge 의 script 를 직접 invoke)

---

## File Structure (변경 매트릭스)

### Create (mctrader-hub)

| 파일 | 책임 | task |
|---|---|---|
| `docs/stories/MCT-102.md` | Phase 5 Story file — Single Story covering 3 repo joint sweep. `## 1.` ~ `## 11.` numbered section. AC = 3 repo 모두 `infra_strategy: none` 명시 + lint SKIP 검증. | Task 4 |

### Modify (3 repos)

| 파일 | 변경 (1줄 + 주석) | task |
|---|---|---|
| `c:\workspace\mclayer\mctrader-market\.claude\_overlay\project.yaml` | `project:` block 다음, `github:` 전에 `infra_strategy: none` + 주석 1줄 | Task 5 |
| `c:\workspace\mclayer\mctrader-market-bithumb\.claude\_overlay\project.yaml` | 동일 | Task 6 |
| `c:\workspace\mclayer\mctrader-hub\.claude\_overlay\project.yaml` | 동일 | Task 4 |

### GitHub issue 등록

| Repo | Issue | task |
|---|---|---|
| mclayer/mctrader-hub | Story MCT-102 stub | Task 2 |

---

## Task 1: Pre-flight 검증

**Files:** N/A (read-only)

- [ ] **Step 1.1: 현재 branch 확인 + main HEAD 정합**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git status
git branch --show-current
git log --oneline -3
```
Expected: `main` clean, latest commit 이 `[MCT-100/101] docs: parallel session bootstrap prompts (#133)` 또는 그 이후.

- [ ] **Step 1.2: MCT-102 collision check**

Run:
```powershell
gh issue list --repo mclayer/mctrader-hub --state all --search "MCT-102 in:title" --json number,title
```
Expected: `[]` (collision 없음). 만약 collision 발견 시 → 다음 available key 로 shift (MCT-103, etc.) — 본 plan 의 모든 reference 도 함께 update.

- [ ] **Step 1.3: 3 sister project.yaml 의 현재 `infra_strategy:` 미명시 재확인**

Run:
```powershell
for repo in 'mctrader-market', 'mctrader-market-bithumb', 'mctrader-hub'; do
  echo "=== $repo ==="
  Get-Content "c:/workspace/mclayer/$repo/.claude/_overlay/project.yaml" | Select-String "infra_strategy"
}
```
Expected: 3 repo 모두 `infra_strategy:` line 0 (미명시 상태 확정).

- [ ] **Step 1.4: codeforge lint script 위치 + 동작 확인**

Run:
```powershell
$script = "c:/workspace/mclayer/plugin-codeforge/scripts/check-container-strategy.sh"
Test-Path $script
# 미명시 default = docker_first lint 실패 재현 (mctrader-market 에서)
cd c:/workspace/mclayer/mctrader-market
bash $script 2>&1
```
Expected: `FAIL: Dockerfile missing under infra_strategy=docker_first` (default `docker_first` 로 fail — 본 task 의 motivation 재확정).

- [ ] **Step 1.5: 작업 시작 시 main 으로 복귀**

Run:
```powershell
cd c:/workspace/mclayer/mctrader-hub
git checkout main
```

---

## Task 2: Story MCT-102 stub issue 등록

**Files:** N/A (GitHub issue create)

- [ ] **Step 2.1: Issue body 작성**

Create file `C:\Users\mccho\AppData\Local\Temp\mct-102-body.md`:

```markdown
# [STORY] MCT-102 — Phase 5 library batch (`infra_strategy: none` × 3 repo)

> **Joint sweep**: mctrader-market + mctrader-market-bithumb + mctrader-hub 3 repo 의 `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 명시. codeforge `check-container-strategy.sh` lint 가 SKIP 으로 정확 분류되도록 declarative governance 박제.

## Status

**Phase 5 — pending merge** (3 PR joint sweep, CFP-96 Phase 6b 패턴)

## Parent Epic

mctrader-hub#120 — mctrader Docker-first Migration (MCT-98)

## Scope

3 repo `.claude/_overlay/project.yaml` 에 1 줄 추가:
```yaml
# CFP-128 / ADR-033 — none (library / governance, no Docker artifacts)
infra_strategy: none
```

## Codex review (Phase 5 entry)

- agentId `a66da458a451e3169` (5 결정 합의: Single Story + 3 PR joint sweep + No version bump + Single Codex review + 로컬 lint SKIP evidence)
- 결정:
  - P5-1=A Single Story MCT-102
  - P5-2=A 3 PR joint sweep
  - P5-3=A No version bump
  - P5-4=B Single Codex 7-area review (mctrader-hub PR anchor)
  - P5-5=A 로컬 `check-container-strategy.sh` SKIP evidence

## 진입 조건 (이미 만족)

- Phase 2 entry merged (mctrader-hub PR #122) ✅
- Codex Phase 5 design review 합의 ✅

## 산출 (예정)

- mctrader-hub PR (Story file MCT-102.md + hub project.yaml)
- mctrader-market PR (project.yaml)
- mctrader-market-bithumb PR (project.yaml)
- 3 PR all phase-gate-mergeable green + admin merge (joint sweep)
- Epic #120 body Phase 5 status = DONE 박제
```

저장:
```powershell
# editor 로 작성
```

- [ ] **Step 2.2: Issue 생성**

Run:
```powershell
gh issue create --repo mclayer/mctrader-hub --title "[STORY] MCT-102 — Phase 5 library batch (infra_strategy: none × 3 repo)" --body-file "C:/Users/mccho/AppData/Local/Temp/mct-102-body.md"
```
Expected: issue URL 출력. 번호 기록 (이하 `$MCT_102_ISSUE`).

- [ ] **Step 2.3: 검증**

Run:
```powershell
gh issue view $MCT_102_ISSUE --repo mclayer/mctrader-hub --json number,title,state
```
Expected: `state: OPEN`.

---

## Task 3: mctrader-hub branch + project.yaml edit

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\.claude\_overlay\project.yaml`

- [ ] **Step 3.1: Branch 생성**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git checkout main
git pull origin main
git checkout -b feat/MCT-102-infra-strategy-none
```

- [ ] **Step 3.2: project.yaml edit**

Find `project:` block 끝 (현재 line ~6: `  name: mctrader`), 다음 line 부터 빈 줄 + 주석 + `infra_strategy: none` 추가.

기존 (line 4-10):
```yaml
project:
  name: mctrader

github:
  org: mclayer
  repo: mctrader-hub
```

수정 후 (line 4-12):
```yaml
project:
  name: mctrader

# CFP-128 / ADR-033 — none (governance hub, no Docker artifacts)
infra_strategy: none

github:
  org: mclayer
  repo: mctrader-hub
```

Edit tool 사용:

old_string:
```
project:
  name: mctrader

github:
  org: mclayer
  repo: mctrader-hub
```

new_string:
```
project:
  name: mctrader

# CFP-128 / ADR-033 — none (governance hub, no Docker artifacts)
infra_strategy: none

github:
  org: mclayer
  repo: mctrader-hub
```

- [ ] **Step 3.3: 로컬 lint 실행 (SKIP evidence)**

Run:
```powershell
bash c:/workspace/mclayer/plugin-codeforge/scripts/check-container-strategy.sh
```
Expected output: `[check-container-strategy] SKIP: infra_strategy=none`

- [ ] **Step 3.4: lint output 캡처 (PR evidence 용)**

Run:
```powershell
bash c:/workspace/mclayer/plugin-codeforge/scripts/check-container-strategy.sh > C:/Users/mccho/AppData/Local/Temp/mct-102-hub-lint.txt 2>&1
Get-Content C:/Users/mccho/AppData/Local/Temp/mct-102-hub-lint.txt
```
Expected: `[check-container-strategy] SKIP: infra_strategy=none`

---

## Task 4: mctrader-hub Story file MCT-102.md 작성 + commit

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-102.md`

- [ ] **Step 4.1: Story file 작성**

Create file `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-102.md` with full content:

```markdown
---
story_key: MCT-102
story_issues:
  - repo: mclayer/mctrader-hub
    number: <MCT_102_ISSUE>
status: complete
---

# MCT-102: Phase 5 library batch — infra_strategy: none × 3 repo

- **Issue**: #<MCT_102_ISSUE>
- **Status**: complete
- **Parent Epic**: mctrader-hub#120 — mctrader Docker-first Migration (MCT-98)
- **Trigger ADR**: codeforge ADR-033 (carrier_story CFP-128)

## 1. 사용자 요구사항 (verbatim)

> "그러니까 이게 뭐하는 작업이지?"
> "ㅇㅋ 그럼 해야지"

본 Story 는 declarative governance 작업 — 3 repo `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 한 줄 추가. codeforge `check-container-strategy.sh` 가 SKIP 으로 분류되도록 명시.

## 2. 도메인 해석

### 2.1 Library / governance shape 의 infra_strategy 의미

3 repo (mctrader-market, mctrader-market-bithumb, mctrader-hub) 는 deployable runtime 부재:

| Repo | Shape | Docker artifact 의무 |
|---|---|---|
| mctrader-market | library (pure Python, Candle Protocol) | 없음 |
| mctrader-market-bithumb | library + WS adapter | 없음 |
| mctrader-hub | governance / docs (no runtime) | 없음 |

→ `infra_strategy: none` = "이 repo 는 라이브러리/문서이므로 Docker 필요 없음" 명시.

### 2.2 codeforge `check-container-strategy.sh` lint logic

`infra_strategy:` 미명시 시 default = `docker_first` → Dockerfile + compose.yml 의무 → 3 repo 가 부당하게 FAIL. `infra_strategy: none` 명시 시 SKIP 분류.

## 3. 관련 ADR

- codeforge ADR-033 (carrier_story CFP-128) — Docker-first Infra Engineering, lint script 동작 정의

## 4. 관련 코드 경로 (per repo)

| Repo | 변경 파일 | 변경 내용 |
|---|---|---|
| mctrader-hub | `.claude/_overlay/project.yaml` | `project:` block 다음 + `github:` 전, 주석 + `infra_strategy: none` (1+1줄) |
| mctrader-market | `.claude/_overlay/project.yaml` | 동일 |
| mctrader-market-bithumb | `.claude/_overlay/project.yaml` | 동일 |

## 5. Acceptance Criteria

| ID | AC | 검증 |
|---|---|---|
| A1 | mctrader-hub `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 명시 | `grep -E '^infra_strategy:' project.yaml` |
| A2 | mctrader-market 동일 | 동일 grep |
| A3 | mctrader-market-bithumb 동일 | 동일 grep |
| A4 | 3 repo 모두 `bash check-container-strategy.sh` 출력 = `SKIP: infra_strategy=none` | 본 PR evidence 박제 |
| A5 | 3 PR all phase-gate-mergeable green + admin merge | `gh pr view` |
| A6 | Epic #120 body Phase 5 status = DONE 박제 | Epic body update commit |

## 6. 외부 지식 배경

- codeforge `scripts/check-container-strategy.sh` (CFP-128 / ADR-033 의무): infra_strategy 값별 분기 (`docker_first` / `legacy_systemd` / `none`)
- mctrader-data Pilot precedent (`infra_strategy: docker_first`, MCT-99 Phase 1 reference)

## 7. 결정점 (Phase 5 entry session, 사용자 승인)

| Decision | 채택 | 거절 |
|---|---|---|
| P5-1 Story granularity | A Single Story MCT-102 | B 3 separate (MCT-102/103/104) — tracking noise |
| P5-2 PR pattern | A 3 PR joint sweep (CFP-96 Phase 6b 패턴) | B sequential / C hub anchor + sister parallel |
| P5-3 Version bump | A No bump (declarative meta) | B patch / C minor |
| P5-4 Codex review depth | B Single 7-area review (mctrader-hub PR anchor) | A skip / C per-PR |
| P5-5 Verification | A 로컬 `check-container-strategy.sh` SKIP evidence | B no run / C CI wiring scope creep |

Codex agent: `a66da458a451e3169`

## 8.5 Implementation Manifest

| # | repo | commit (post-merge fill) | 내용 |
|---|---|---|---|
| 1 | mctrader-hub | `<hub-commit>` | Story file MCT-102.md + hub project.yaml |
| 2 | mctrader-market | `<market-commit>` | project.yaml |
| 3 | mctrader-market-bithumb | `<bithumb-commit>` | project.yaml |

## 9. Evidence

### 9.1 Lint SKIP evidence (3 repo, 로컬 검증)

각 repo 에서 `bash check-container-strategy.sh` 실행:

```
[mctrader-hub]
[check-container-strategy] SKIP: infra_strategy=none

[mctrader-market]
[check-container-strategy] SKIP: infra_strategy=none

[mctrader-market-bithumb]
[check-container-strategy] SKIP: infra_strategy=none
```

### 9.2 PR merge evidence (post-merge fill)

- mctrader-hub PR `<hub-pr-#>` MERGED `<timestamp>`
- mctrader-market PR `<market-pr-#>` MERGED `<timestamp>`
- mctrader-market-bithumb PR `<bithumb-pr-#>` MERGED `<timestamp>`

### 9.3 Codex review trace

agentId `<codex-pr-review-id>` (Phase 5 mctrader-hub PR 7-area review)

## 10. 거절된 대안

(§7 결정점 거절 column 참조)

## 11. 회고

본 Story 는 declarative governance 박제. 의의:

- Epic #120 AC B1 (6 repo 모두 `infra_strategy:` 명시) 만족 — 이전 1/6 (mctrader-data) → 4/6 (mctrader-data + library quartet 3)
- AC B3 (library quartet `infra_strategy: none` lint pass) 만족
- Phase 6 Epic close 진입 조건 = Phase 3 + Phase 4 + Phase 5 모두 종료 (Phase 5 본 Story 가 그 일부)

### 11.1 후속

- Phase 3 mctrader-engine (MCT-100 #131) — parallel session 진행 중
- Phase 4 mctrader-web (MCT-101 #132) — parallel session 진행 중
- Phase 6 Epic close — 3 phase 모두 종료 후 진입
```

저장 시 `<MCT_102_ISSUE>` 2곳 (frontmatter + Issue link) 모두 Task 2 의 실제 번호로 치환.

- [ ] **Step 4.2: Story file 작성 검증**

Run:
```powershell
Get-Content docs/stories/MCT-102.md -TotalCount 10
grep -c "^## " docs/stories/MCT-102.md
```
Expected: frontmatter 정상 (`story_key: MCT-102`), section 11개 (`## 1.` ~ `## 11.`).

- [ ] **Step 4.3: hub commit (project.yaml + Story file 한번에)**

Run:
```powershell
git add .claude/_overlay/project.yaml docs/stories/MCT-102.md
git commit -m "[MCT-102] feat(infra): infra_strategy: none + Phase 5 Story file"
```
Expected: commit 성공.

---

## Task 5: mctrader-market branch + project.yaml edit + commit

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-market\.claude\_overlay\project.yaml`

- [ ] **Step 5.1: Branch 생성**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-market
git checkout main
git pull origin main
git checkout -b feat/MCT-102-infra-strategy-none
```

- [ ] **Step 5.2: project.yaml edit**

Edit `c:\workspace\mclayer\mctrader-market\.claude\_overlay\project.yaml`:

old_string:
```
project:
  name: mctrader

github:
  org: mclayer
  repo: mctrader-market
```

new_string:
```
project:
  name: mctrader

# CFP-128 / ADR-033 — none (library, no Docker artifacts)
infra_strategy: none

github:
  org: mclayer
  repo: mctrader-market
```

- [ ] **Step 5.3: 로컬 lint 실행 + capture**

Run:
```powershell
bash c:/workspace/mclayer/plugin-codeforge/scripts/check-container-strategy.sh > C:/Users/mccho/AppData/Local/Temp/mct-102-market-lint.txt 2>&1
Get-Content C:/Users/mccho/AppData/Local/Temp/mct-102-market-lint.txt
```
Expected: `[check-container-strategy] SKIP: infra_strategy=none`

- [ ] **Step 5.4: commit**

Run:
```powershell
git add .claude/_overlay/project.yaml
git commit -m "[MCT-102] feat(infra): infra_strategy: none (library, no Docker)"
```

---

## Task 6: mctrader-market-bithumb branch + project.yaml edit + commit

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-market-bithumb\.claude\_overlay\project.yaml`

- [ ] **Step 6.1: Branch 생성**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-market-bithumb
git checkout main
git pull origin main
git checkout -b feat/MCT-102-infra-strategy-none
```

- [ ] **Step 6.2: project.yaml edit**

Edit `c:\workspace\mclayer\mctrader-market-bithumb\.claude\_overlay\project.yaml`:

old_string:
```
project:
  name: mctrader

github:
  org: mclayer
  repo: mctrader-market-bithumb
```

new_string:
```
project:
  name: mctrader

# CFP-128 / ADR-033 — none (library + WS adapter, no Docker artifacts)
infra_strategy: none

github:
  org: mclayer
  repo: mctrader-market-bithumb
```

- [ ] **Step 6.3: 로컬 lint 실행 + capture**

Run:
```powershell
bash c:/workspace/mclayer/plugin-codeforge/scripts/check-container-strategy.sh > C:/Users/mccho/AppData/Local/Temp/mct-102-bithumb-lint.txt 2>&1
Get-Content C:/Users/mccho/AppData/Local/Temp/mct-102-bithumb-lint.txt
```
Expected: `[check-container-strategy] SKIP: infra_strategy=none`

- [ ] **Step 6.4: commit**

Run:
```powershell
git add .claude/_overlay/project.yaml
git commit -m "[MCT-102] feat(infra): infra_strategy: none (library + WS adapter, no Docker)"
```

---

## Task 7: 3 branch push + 3 PR open

**Files:** N/A (git + gh)

- [ ] **Step 7.1: mctrader-hub branch push**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git push -u origin feat/MCT-102-infra-strategy-none
```

- [ ] **Step 7.2: mctrader-hub PR body 작성**

Create file `C:\Users\mccho\AppData\Local\Temp\mct-102-hub-pr-body.md`:

```markdown
## Summary

mctrader Docker-first Migration Epic (MCT-98 #120) Phase 5 — library/governance batch joint sweep. mctrader-hub anchor (Story file MCT-102.md + hub project.yaml). 2 sister PRs (market + bithumb) 별도 진행.

**1 commit (governance only)**:
1. `<hub-commit>` Story file `docs/stories/MCT-102.md` + hub `.claude/_overlay/project.yaml` `infra_strategy: none` 추가

## Linked

- Story: mctrader-hub#<MCT_102_ISSUE>
- Parent Epic: mctrader-hub#120 (MCT-98)
- Sister PR (mctrader-market): linked after open
- Sister PR (mctrader-market-bithumb): linked after open

## Lint SKIP evidence

각 repo 에서 `bash check-container-strategy.sh` 출력 (Phase 5 P5-5=A 결정 정합):

```
[mctrader-hub]
[check-container-strategy] SKIP: infra_strategy=none
```

(2 sister 의 lint output 은 각 sister PR 본문 참조)

## Codex review (Phase 5 design)

agentId `a66da458a451e3169` — 5 결정 합의: P5-1=A Single Story / P5-2=A 3 PR joint sweep / P5-3=A No bump / P5-4=B Single Codex review (this PR anchor) / P5-5=A 로컬 lint evidence

## Test Plan

- [x] 로컬 lint SKIP 확인
- [ ] DesignReview (Codex 7-area review on this PR, governance + Story file + 3-repo batch coverage)
- [ ] codeforge phase-gate-mergeable green
- [ ] 2 sister PR 동시 admin merge (joint sweep)

## Spec / Plan reference

- plan: `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase5-library-batch-plan.md`
- Story: `docs/stories/MCT-102.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

`<MCT_102_ISSUE>` Task 2 의 실제 번호로 치환. `<hub-commit>` 은 `git log --oneline -1` hash 로 치환.

- [ ] **Step 7.3: mctrader-hub PR open**

Run:
```powershell
gh pr create --repo mclayer/mctrader-hub --base main --head feat/MCT-102-infra-strategy-none --title "[MCT-102] feat(infra): Phase 5 library batch — hub infra_strategy: none + Story file" --body-file C:/Users/mccho/AppData/Local/Temp/mct-102-hub-pr-body.md
```
Expected: PR URL. 번호 기록 (`$HUB_PR`).

- [ ] **Step 7.4: mctrader-market branch push + PR**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-market
git push -u origin feat/MCT-102-infra-strategy-none
```

PR body file `C:\Users\mccho\AppData\Local\Temp\mct-102-market-pr-body.md`:

```markdown
## Summary

mctrader Docker-first Migration Epic (MCT-98 #120) Phase 5 — mctrader-market `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 명시 (library, no Docker artifacts).

## Linked

- Parent Story: mclayer/mctrader-hub#<MCT_102_ISSUE> (MCT-102)
- Parent Epic: mclayer/mctrader-hub#120 (MCT-98)
- Anchor PR: mclayer/mctrader-hub#<HUB_PR>

## Lint SKIP evidence

```
[check-container-strategy] SKIP: infra_strategy=none
```

## Test Plan

- [x] 로컬 lint SKIP 확인
- [ ] codeforge phase-gate-mergeable green
- [ ] joint sweep admin merge (mctrader-hub anchor + 2 sister 동시)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

`<MCT_102_ISSUE>` + `<HUB_PR>` 치환.

PR open:
```powershell
gh pr create --repo mclayer/mctrader-market --base main --head feat/MCT-102-infra-strategy-none --title "[MCT-102] feat(infra): infra_strategy: none (library, no Docker)" --body-file C:/Users/mccho/AppData/Local/Temp/mct-102-market-pr-body.md
```
Expected: PR URL. 번호 기록 (`$MARKET_PR`).

- [ ] **Step 7.5: mctrader-market-bithumb branch push + PR**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-market-bithumb
git push -u origin feat/MCT-102-infra-strategy-none
```

PR body file `C:\Users\mccho\AppData\Local\Temp\mct-102-bithumb-pr-body.md`:

```markdown
## Summary

mctrader Docker-first Migration Epic (MCT-98 #120) Phase 5 — mctrader-market-bithumb `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 명시 (library + WS adapter, no Docker artifacts).

## Linked

- Parent Story: mclayer/mctrader-hub#<MCT_102_ISSUE> (MCT-102)
- Parent Epic: mclayer/mctrader-hub#120 (MCT-98)
- Anchor PR: mclayer/mctrader-hub#<HUB_PR>

## Lint SKIP evidence

```
[check-container-strategy] SKIP: infra_strategy=none
```

## Note

본 repo 의 PR #3 (`fix(ws_mapping)`, 2026-05-07T12:02:24Z merged) 가 mctrader-data Pilot 의 healthy state 를 unblock 함은 Phase 2 entry session (mctrader-hub PR #122) 에서 integration smoke 로 verification 완료 — 본 Phase 5 PR scope 외 (declarative governance only).

## Test Plan

- [x] 로컬 lint SKIP 확인
- [ ] codeforge phase-gate-mergeable green
- [ ] joint sweep admin merge (mctrader-hub anchor + 2 sister 동시)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

PR open:
```powershell
gh pr create --repo mclayer/mctrader-market-bithumb --base main --head feat/MCT-102-infra-strategy-none --title "[MCT-102] feat(infra): infra_strategy: none (library + WS adapter, no Docker)" --body-file C:/Users/mccho/AppData/Local/Temp/mct-102-bithumb-pr-body.md
```
Expected: PR URL. 번호 기록 (`$BITHUMB_PR`).

- [ ] **Step 7.6: 3 PR 검증**

Run:
```powershell
gh pr view $HUB_PR --repo mclayer/mctrader-hub --json number,state,mergeable
gh pr view $MARKET_PR --repo mclayer/mctrader-market --json number,state,mergeable
gh pr view $BITHUMB_PR --repo mclayer/mctrader-market-bithumb --json number,state,mergeable
```
Expected: 3 PR 모두 `state: OPEN`, `mergeable: MERGEABLE`.

---

## Task 8: Codex 7-area review (mctrader-hub PR anchor)

**Files:** N/A (review subagent dispatch)

- [ ] **Step 8.1: Codex agent dispatch**

Use `codex:codex-rescue` agent with prompt:

> You are Codex (GPT-5) doing a 7-area review of a 3-repo joint sweep PR set for Phase 5 of mctrader Docker-first Migration Epic.
>
> **PR set**:
> - Anchor: mclayer/mctrader-hub#<HUB_PR> (Story file MCT-102.md + hub project.yaml)
> - mclayer/mctrader-market#<MARKET_PR> (project.yaml only)
> - mclayer/mctrader-market-bithumb#<BITHUMB_PR> (project.yaml only)
>
> **Scope**: 각 repo `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 1줄 + 주석 1줄 추가. mctrader-hub 가 Story file MCT-102.md 추가.
>
> **Files in scope**:
> - `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-102.md` (NEW, Story file `## 1.` ~ `## 11.`)
> - 3 `.claude/_overlay/project.yaml` (1+1 line addition each)
>
> **7-area review**:
> 1. Story file completeness — `## 1.` ~ `## 11.` numbered section, AC verifiability, 결정점 trace, 거절된 대안
> 2. project.yaml edit correctness — placement (project: 다음, github: 전), comment 의미 정합, schema 정합 (codeforge `docs/project-config-schema.md`)
> 3. lint SKIP evidence completeness — 3 repo 모두 expected output 박제 됨
> 4. Joint sweep coordination — anchor PR ↔ sister PR cross-link 정확, merge 순서 의존 부재 확인
> 5. Epic governance trace — MCT-102 Story → Epic MCT-98 link, Phase 5 acceptance 만족
> 6. 거절된 대안 trace (P5-1~P5-5 결정 의 거절 column)
> 7. Cross-doc consistency — Story file ↔ PR body ↔ Epic body link 정확
>
> **Output**: per-area finding (CLEAN or severity HIGH/MEDIUM/LOW + concrete fix). TOP 2 push-back. DEFER 후보. OVERALL VERDICT (APPROVE / APPROVE WITH FIXES / BLOCK). 최대 400 words.

- [ ] **Step 8.2: Review 결과 보존**

Codex review 결과 → `C:\Users\mccho\AppData\Local\Temp\codex-review-mct-102.md` 저장.

---

## Task 9: Sonnet decider 합성 + fix-back (조건부)

**Files:** N/A or fix commits

- [ ] **Step 9.1: push-back 분류**

- HIGH → 즉시 fix-back commit (해당 repo 에)
- MEDIUM → fix 또는 defer 결정
- LOW → defer 박제

- [ ] **Step 9.2: fix-back commit (필요 시)**

각 fix 항목 별 atomic commit. 예시:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git add docs/stories/MCT-102.md
git commit -m "[MCT-102] docs(story): fix per Codex review (HIGH-1)"
git push origin feat/MCT-102-infra-strategy-none
```

- [ ] **Step 9.3: PR comment 에 합성 trace 박제**

Run:
```powershell
gh pr comment $HUB_PR --repo mclayer/mctrader-hub --body "Codex review push-back 처리:
- <항목 1> → <fix or defer>
- <항목 2> → <fix or defer>
agentId: <codex-pr-review-id>"
```

---

## Task 10: CI watch + 3 PR admin merge (joint sweep)

**Files:** N/A

- [ ] **Step 10.1: 3 PR CI watch (foreground polling)**

Run (각 PR 각각, 또는 병렬 polling):
```powershell
gh pr checks $HUB_PR --repo mclayer/mctrader-hub --watch
gh pr checks $MARKET_PR --repo mclayer/mctrader-market --watch
gh pr checks $BITHUMB_PR --repo mclayer/mctrader-market-bithumb --watch
```

memory feedback `ci_terminal_states_classify` 정합:
- SUCCESS → Step 10.2 진행
- FAILURE / ACTION_REQUIRED / BLOCKED → 즉시 분류 + 처리

- [ ] **Step 10.2: 3 PR admin merge (joint sweep)**

CI green 후 즉시 admin merge (memory feedback `admin_merge_autonomy`). 짧은 시간 안에 3 PR 모두 merge (CFP-96 Phase 6b 패턴, admin merge window <30초 권장):

Run:
```powershell
gh pr merge $HUB_PR --repo mclayer/mctrader-hub --admin --squash --delete-branch
gh pr merge $MARKET_PR --repo mclayer/mctrader-market --admin --squash --delete-branch
gh pr merge $BITHUMB_PR --repo mclayer/mctrader-market-bithumb --admin --squash --delete-branch
```

- [ ] **Step 10.3: Merge 검증**

Run:
```powershell
gh pr view $HUB_PR --repo mclayer/mctrader-hub --json state,mergedAt
gh pr view $MARKET_PR --repo mclayer/mctrader-market --json state,mergedAt
gh pr view $BITHUMB_PR --repo mclayer/mctrader-market-bithumb --json state,mergedAt
```
Expected: 3 PR 모두 `state: MERGED`.

- [ ] **Step 10.4: 3 repo main sync**

Run:
```powershell
cd c:\workspace\mclayer\mctrader-hub
git checkout main
git pull origin main

cd c:\workspace\mclayer\mctrader-market
git checkout main
git pull origin main

cd c:\workspace\mclayer\mctrader-market-bithumb
git checkout main
git pull origin main
```

- [ ] **Step 10.5: 3 repo local feature branch 삭제**

Run (각 repo):
```powershell
git branch -D feat/MCT-102-infra-strategy-none
```

---

## Task 11: Post-merge — MCT-102 close + Epic body update + memory

**Files:** N/A (issue ops + memory)

- [ ] **Step 11.1: MCT-102 issue close**

Run:
```powershell
gh issue close $MCT_102_ISSUE --repo mclayer/mctrader-hub --reason completed --comment "Phase 5 library batch DONE 2026-05-08. 3 PR joint sweep (mctrader-hub#$HUB_PR + mctrader-market#$MARKET_PR + mctrader-market-bithumb#$BITHUMB_PR) all MERGED. Epic MCT-98 (#120) AC B1 + B3 만족."
```

- [ ] **Step 11.2: Epic #120 body update — Phase 5 DONE 표기**

Epic body 의 Phase plan 표 update:
- Phase 5 status: `(TBD MCT-102 candidate)` → `✅ DONE 2026-05-08 (MCT-102 #<MCT_102_ISSUE>)` + 3 PR link
- AC B1 / B3 checkbox check

Run:
```powershell
# Epic body 현재 가져오기
gh issue view 120 --repo mclayer/mctrader-hub --json body --jq '.body' > C:/Users/mccho/AppData/Local/Temp/mct-98-epic-body-v3.md
# editor 로 Phase 5 줄 + AC B1/B3 checkbox edit
gh issue edit 120 --repo mclayer/mctrader-hub --body-file C:/Users/mccho/AppData/Local/Temp/mct-98-epic-body-v3.md
```

- [ ] **Step 11.3: Memory 업데이트**

`C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\project_dockerization_epic.md` 업데이트:
- Phase 5 status: TBD → DONE
- 3 PR link 추가
- "Phase 5 entry 시점 단순화 (bithumb#4 already closed) → 별도 fix Story 불필요" 박제

Edit (Edit tool 사용):

old_string:
```
- **Phase 5** library batch (market+bithumb+hub joint) TBD — MCT-102 candidate (`infra_strategy: none`). bithumb WS schema fix 의무 = **이미 만족** (PR #3 inline fix + smoke verified 2026-05-08)
```

new_string:
```
- **Phase 5** library batch DONE 2026-05-08 — MCT-102 (#<MCT_102_ISSUE>) 3 PR joint sweep: mctrader-hub#<HUB_PR> + mctrader-market#<MARKET_PR> + mctrader-market-bithumb#<BITHUMB_PR>. 3 repo `infra_strategy: none` 명시.
```

---

## 종료 조건

- [ ] 1 stub issue (MCT-102) 등록 + close
- [ ] 3 PR all MERGED (mctrader-hub anchor + 2 sister)
- [ ] 3 repo `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 박제
- [ ] 3 repo 로컬 `bash check-container-strategy.sh` SKIP evidence 캡처 (PR body 박제)
- [ ] Codex 7-area review 처리 trace 박제
- [ ] Epic #120 body Phase 5 status DONE + AC B1/B3 checkbox check
- [ ] Memory `project_dockerization_epic.md` Phase 5 update

본 plan 종료 = mctrader Docker-first Migration Epic Phase 5 완료. Phase 3 + Phase 4 (parallel session) 종료 시 Phase 6 Epic close 진입 가능.
