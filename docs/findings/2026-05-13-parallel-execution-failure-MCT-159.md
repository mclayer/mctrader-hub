---
finding_id: FINDING-2026-05-13-parallel-execution-failure
type: cross-cutting-pattern
severity: HIGH
trigger_story: MCT-159
discovered_at: 2026-05-13
discovered_by: 사용자 surface (Orchestrator session post-MCT-159 Phase 2 LAND)
upstream_target: codeforge plugin (mclayer/codeforge)
upstream_counter: CFP-TBD (escalation prompt 박제 — 본 문서 §6)
related_retros:
  - docs/retros/RETRO-MCT-159.md (§8.1 cross-Story pre-existing CI pattern 와 별 영역)
status: ESCALATION_READY
---

# FINDING — codeforge consumer Orchestrator session 의 병행 수행 실패 pattern (MCT-159 Phase 2)

## 0. 사용자 directive (verbatim — 변경 차단)

> "구현에 있어서 너무 순차적으로 구현하고 있어서 시간이 지체된다. 의존성이 없는 작업들은 병행해서 작업할 수 있었을텐데 그럴 수 없었나?"
>
> "병행 수행이 되지 않는 주제는 CFP로 escalation할 수 있도록 너의 상황 중에 발생했던 부분에서 병행 수행하지 못했던 이유와 어떻게 해야 효과적으로 병행 수행 할 수 있었는지 맥락 중심으로 문서를 작성하고 esclaltion하기 위한 프롬프트를 작성하라."

본 finding = codeforge consumer (mctrader) workaround 가 아닌 **codeforge upstream plugin 수정 의무** 영역 (memory `escalate_to_codeforge` 정합).

---

## 1. Executive Summary

MCT-159 Phase 2 (`mctrader-data#49`) 구현 dispatch (DeveloperPLAgent) 가 약 **55분 wall-clock** 소요. plan 박제 Task 8~14 가 모두 sequential 진행되어 의존성 부재 영역의 **잠재 wall-clock 감축 ~40-50% 손실** 추정.

### 실패 root cause 6 영역

| # | 영역 | 본질 |
|---|------|------|
| F1 | **writing-plans skill 의 linear task 분해 bias** | `depends_on` / `parallel_with` field 부재 — DAG 박제 0 |
| F2 | **Orchestrator dispatch prompt 의 sequential lock** | "plan 박제 그대로 sequential" wording 으로 PL 자율 병렬 권한 차단 |
| F3 | **DeveloperPLAgent 의 default sequential 패턴** | Plan task 별 next subagent dispatch = 전 subagent 완료 의존. parallel branch decision tree 부재 |
| F4 | **superpowers:subagent-driven-development skill 자체 sequential 권고** | task-by-task review checkpoint 사이 sequential. parallel branch escape hatch 부재 |
| F5 | **superpowers:dispatching-parallel-agents skill 의 activation trigger 부재** | Orchestrator 가 Plan 에 parallel hint 없으면 본 skill 미invoke. auto-detect 부재 |
| F6 | **codeforge consumer Orchestrator template 의 default dispatch pattern** | codeforge consumer (mctrader) 의 Orchestrator 가 PL dispatch 시 default = sequential plan-following. parallel hint propagation 부재 |

### 효과적 병렬화 시 추정 wall-clock 감축

- Phase 2 DeveloperPLAgent dispatch: **55 min → ~30 min (~45% 감축)**
- 6 영역 모두 해소 시 Story 평균 lead-time 1 cycle 당 30-50% wall-clock 감축 추정 (cross-Story 누적 효과 큼)

---

## 2. 본 세션 Timeline 박제 (사실 only)

### Phase 0 — brainstorm 7 agent 병렬 ✅ 잘됨

| 항목 | 측정값 |
|------|--------|
| dispatch 방식 | 단일 message 안에 7 `Agent` tool calls + `run_in_background: true` |
| agent 종류 | DomainAgent / ResearcherAgent / RequirementsAnalystAgent / ContinuityAgent / FeasibilityAgent / ChangeImpactAgent / PMOAgent (1st pass) |
| 최장 agent duration_ms | 188,378 (ContinuityAgent, ~3분) |
| 최단 | 15,280 (ResearcherAgent, ~15초) |
| sequential 가정 wall-clock | ~7-10분 |
| 실제 wall-clock | ~3분 (= 최장 agent) |
| **speedup** | **2-3x** |

**평가**: codeforge-brainstorm skill 의 Phase 0 = 명시적 parallel burst 패턴 박제. **본 영역 = 정상 작동.**

### Phase 1 — Codex review ✅ 잘됨

| 항목 | 측정값 |
|------|--------|
| Codex dispatch 횟수 | 1회 (8 D 일괄 review) |
| duration_ms | 125,351 (~2분) |
| 비교 | 8 D 각각 별 Codex dispatch 시 ~16-20분 추정 |
| **speedup** | **8-10x (단일 prompt 일괄 review pattern)** |

**평가**: 사용자 memory `feedback_brainstorm_codex_review_pattern` 정합 — 모든 open design 결정점 Codex 일괄 dispatch → Sonnet 합성. **본 영역 = 정상 작동.**

### Phase 1 — governance docs 작성 ⚠️ partial

본 Orchestrator (Claude) 가 직접 처리. subagent dispatch 0 (consumer Orchestrator level 직접 write).

| 작업 | 도구 | 병렬화 가능? |
|------|------|-----------|
| ADR-027 D4 amendment | Edit (single block) | N/A (직렬 1회) |
| ADR-027 D6 amendment | Edit | ↑ D4 와 같은 file = sequential 필수 |
| ADR-027 D9 amendment | Edit | ↑ D4/D6 와 같은 file = sequential 필수 |
| ADR-027 History append | Edit | ↑ 같은 file = sequential 필수 |
| docs/stories/MCT-159.md write | Write | ⭐ **다른 file = ADR amend 와 병렬 가능** |
| scope_manifest patch 5편 | Edit × 5 | ↑ 같은 file = sequential 필수 |
| CLAUDE.md (hub) | Edit | ⭐ **다른 file = scope_manifest 와 병렬 가능** |
| CLAUDE.md (data) | Edit | ⭐ **다른 repo = 모두와 병렬 가능** |

**부분 병렬화 성공**: 일부 batch 안에서 multiple Edit/Read tool calls in single message — 본 Orchestrator 가 자연 적용.

**부분 병렬화 실패**: 큰 file (Story.md = 296 line, plan.md = 1068 line) write 가 single Write tool call 이라 atomic. multiple Write calls in parallel 자체는 가능했으나 시도 안 함. ADR amend 와 Story write 가 다른 file 임에도 sequential 진행.

**추정 손실**: ~3-5분 (Phase 1 governance 약 15분 → 병렬화 시 10-12분 가능). **critical bottleneck 아님.**

### Phase 2 — DeveloperPLAgent dispatch ❌❌ MAJOR

| 항목 | 측정값 |
|------|--------|
| dispatch 방식 | 단일 DeveloperPLAgent invocation (Orchestrator → 1 PL) |
| PL duration_ms | 3,285,465 (**~55분**) |
| PL 내부 tool_uses | 419회 |
| Phase 2 PR merged_at - Orchestrator dispatch | 10:19:13 → 11:04:04 (45분, PR review/merge gap 제외) |
| pre-existing CI fix commits | 3 bulk (ruff 63 + pyright 28 + test 15) |

**실제 진행 순서 (PL 내부, plan §Task 박제 그대로)**:

```
Task 8 (fixture 갱신, ~5min)
   ↓ sequential
Task 9 (channel parametrize, ~5min)
   ↓ sequential
Task 10 (hour key 박제, ~5min)
   ↓ sequential
Task 11 (CLI --channel + evidence pack, ~3min)
   ↓ sequential
Task 12 (integration test 7종 작성, ~10min)
   ↓ sequential
Task 13 (perf baseline 측정, ~2min)
   ↓ sequential
pre-existing CI fix iteration (ruff → pyright → test, ~15-20min)
   ↓ sequential
Task 14 (PR create + CI watch + admin merge, ~5min)
   ↓ sequential
PMOAgent retro dispatch + §8.5 Impl Manifest + §12 retro summary (~5min)
```

**병렬 가능했던 영역**:

```
Task 8 (fixture, same file = sequential 필수)
   ↓
   ├─→ Task 9 (channel parametrize, _discover_partitions method)  ┐
   ├─→ Task 10 (hour key, _build_chunk_spec method)               │ same file 다른 method =
   │                                                                병렬 가능 (atomic commit 분리,
   │                                                                conflict resolution 1회만)
   └─→ Task 11 (CLI --channel, 다른 file run_backfill.py)         ┘ different file =
                                                                     Task 9 의 __init__ signature LAND
                                                                     후 자연 병렬
                                                                     │
                                                                     ↓
Task 12 (integration test 7종, AC-1~5 + Edge Case 2 = 7 독립 test) ─→ 6-way 병렬 가능
                                                                     │
                                                                     ↓
Task 13 (perf baseline) ─→ Task 12 와 자연 병렬 (다른 file scope)
                                                                     │
                                                                     ↓
Task 14 (PR + CI + merge)

pre-existing CI fix:
   ruff 63건 (lint, auto-fix + 수동) ─┐
   pyright 28건 (type 추가)             │ 모두 main broken, 서로 disjoint
   test 15건 (CandleModel/Mock 등)     ┘ 영역 = 3-way 병렬 가능
```

**잠재 wall-clock 감축**:
- Task 9 + Task 10 + Task 11 동시 dispatch (max ~5min) vs sequential (~13min) = **8min 절약**
- Task 12 7 test parallel write (max ~3min) vs sequential (~10min) = **7min 절약**
- pre-existing CI fix 3-way 병렬 (max ~10min) vs sequential (~20min) = **10min 절약**
- **합 ~25min wall-clock 감축 추정 (55min → ~30min, 45% 감축)**

---

## 3. 6 Escalation 영역 (codeforge upstream issue)

### F1. writing-plans skill 의 linear task 분해 bias

**위치**: `claude-plugins-official/superpowers/5.1.0/skills/writing-plans` (superpowers plugin, codeforge 와는 별 upstream but codeforge orchestrator 가 invoke)

**현 상태**: writing-plans skill 의 task structure 박제 (`### Task N: [Component Name]`) — 각 task 가 sequential 박제. `parallel_with: [...]` / `depends_on: [...]` field 부재. Plan 작성자 (Claude or PL) 가 의존성 그래프 도출 의무 0.

**문제**:
- consumer agent (Orchestrator / PL) 가 plan 따를 때 default = task 박제 순서 sequential
- 의존성 부재 영역 (e.g. 같은 file 다른 method) 식별 부담이 consumer 에 100% 부여
- consumer 도 sequential 박제 그대로 진행하면 (본 세션) 손실 자연 발생

**제안**: writing-plans skill 의 task structure 에 다음 field 추가 의무 (or 권장):

```markdown
### Task N: [Component Name]

**Files:**
- Modify: `path/to/file.py`

**Dependencies:**
- depends_on: [Task M]  # Task M complete 의존
- parallel_with: [Task K, Task L]  # 동시 dispatch 가능
- conflict_scope: file:path/to/file.py  # 동일 파일 충돌 시 sequential merge

- [ ] Step 1: ...
```

→ consumer agent 가 DAG 직접 도출 (topological sort + 병렬 batch 식별).

### F2. Orchestrator dispatch prompt 의 sequential lock

**위치**: codeforge consumer 의 Orchestrator (본 세션의 Claude) 가 PL dispatch 시 작성하는 prompt template.

**현 상태**: 본 세션의 DeveloperPLAgent dispatch prompt 가 다음 wording 박제:

> "각 task 별 plan 의 step 박제 그대로 (TDD red→green→commit pattern). commit 은 task 별 분할 권고이나 PR 은 단일 (Phase 2 PR)."
>
> "진행. plan 의 Task 8 부터 sequential."

**문제**: "plan 박제 그대로" + "Task 8 부터 sequential" 명시 = PL agent 의 자율 병렬 권한 차단. PL 이 plan 의 의존성 그래프 분석 후 병렬 dispatch 결정 의무 부재.

**제안**: codeforge 의 Orchestrator dispatch prompt template 에 다음 default 추가:

```
PL agent 의무:
1. plan 의 task 의존성 DAG 도출 (depends_on / parallel_with / conflict_scope 필드 분석)
2. 의존성 그래프 기반 parallel batch 식별
3. 동일 batch 내 task 는 DeveloperAgent / QADeveloperAgent multi-instance 병렬 dispatch
4. file-level conflict (same-file-different-method) 는 git commit 분리 + branch 1 안에서 atomic commit interleave
5. 단, 다음 경우 sequential 의무:
   - TDD red phase 강제 (fixture/test 갱신 first → red → green)
   - schema migration sequential 의무
   - pre-existing broken fix 가 본 Story 코드의 prerequisite
```

→ PL agent 의 자율 병렬 dispatch 권한 명시.

### F3. DeveloperPLAgent 의 default sequential 패턴

**위치**: `mclayer/codeforge` (codeforge plugin 의 develop lane agent) 의 DeveloperPLAgent prompt template / 책임 정의.

**현 상태**: DeveloperPLAgent 의 description = "구현 레인 PL — role:dev 에이전트 동적 roster + QADev 병렬 감독, 구현 FIX 1차 원인 진단 → ArchitectPLAgent 회부". 

description 에 "QADev 병렬 감독" 박제는 있으나 **production code DeveloperAgent 의 multi-instance 병렬 dispatch 박제 부재**. Phase 2 의 실제 동작 = DeveloperAgent 1 instance + QADeveloperAgent 1 instance sequential interleave.

**제안**: DeveloperPLAgent 의 description + 책임 정의 amendment:

> "구현 레인 PL — role:dev 에이전트 동적 roster + QADev **양쪽 모두 multi-instance 병렬 dispatch** (plan DAG 의 parallel_with hint 기반) + 구현 FIX 1차 원인 진단 → ArchitectPLAgent 회부.
>
> 병렬 dispatch decision tree:
> 1. plan 의 parallel_with hint 있음 → multi-instance 병렬 (default)
> 2. parallel_with hint 부재 + 파일 disjoint + interface 의존 0 → 자율 병렬 (default)
> 3. same-file-different-method + commit atomic 분리 가능 → 병렬 + merge 시점 sync
> 4. same-file-same-method 또는 schema migration → sequential 의무"

### F4. superpowers:subagent-driven-development skill 의 sequential 권고

**위치**: `claude-plugins-official/superpowers/skills/subagent-driven-development`

**현 상태**: skill 의 핵심 패턴 = "fresh subagent per task + two-stage review". task 별 fresh subagent → 다음 task 진입 전 review checkpoint = **sequential default**.

**문제**:
- review checkpoint 의무 자체는 valid (regression 방지)
- 그러나 의존성 부재 영역에서도 sequential = 손실
- skill 에 parallel branch escape hatch 부재

**제안**: subagent-driven-development skill 에 parallel mode 추가:

```markdown
## Parallel Mode (의존성 부재 task 영역)

plan 의 task DAG 에 parallel_with batch 식별 시:

1. batch 내 task 들에 대해 fresh subagent multi-instance 동시 dispatch
2. 모든 batch member 완료 후 single review checkpoint (개별 task 별 review 회피)
3. file-level conflict 발생 시 merge resolution 1회 (자동 또는 PL agent)

batch 내 task 가 1개 = sequential mode (현 default).
batch 내 task 가 N>1 개 = parallel mode + integrated review.

skill 자체가 plan 의 parallel_with hint 를 auto-detect + 자동 모드 전환 의무.
```

### F5. superpowers:dispatching-parallel-agents skill 의 activation trigger 부재

**위치**: `claude-plugins-official/superpowers/skills/dispatching-parallel-agents`

**현 상태**: skill description = "Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies".

**문제**:
- Orchestrator 가 본 skill 의 activation trigger 를 자동 인지 못함
- writing-plans / subagent-driven-development 와 별 skill 이라 자연 연계 부재
- Plan 의 task DAG 분석 후 본 skill 호출 의무 = consumer Orchestrator 책임 100%

**제안**: superpowers 의 skill cross-link 강화:

1. writing-plans skill 의 self-review section 에 추가: "task DAG 분석 후 parallel batch 식별 시 subagent-driven-development 의 parallel mode 또는 dispatching-parallel-agents skill 호출 권고"
2. subagent-driven-development skill 의 진입 검토 step 에 추가: "plan 의 parallel_with field 발견 시 dispatching-parallel-agents skill 자동 escalate"
3. dispatching-parallel-agents skill 의 trigger condition 명시: "(a) 동일 batch N≥2 task (b) file disjoint OR same-file-different-method (c) interface signature 안정"

### F6. codeforge consumer Orchestrator template 의 default dispatch pattern

**위치**: `mclayer/codeforge` (codeforge plugin) 의 consumer Orchestrator behavior 정의 (CLAUDE.md template / project.yaml).

**현 상태**: codeforge consumer (mctrader) 의 Orchestrator 가 PL dispatch 시 default = "plan 박제 그대로 sequential". codeforge plugin 의 Orchestrator behavior 가 sequential bias.

**제안**: codeforge plugin 의 consumer overlay (`.claude/_overlay/CLAUDE.md` template) 에 다음 default 박제:

```markdown
## Story Phase 2 dispatch (DeveloperPLAgent) default pattern

Orchestrator → DeveloperPLAgent dispatch 시 prompt 의무:

1. plan 의 task DAG 분석 결과 박제 (parallel_with batches list)
2. PL agent 에 자율 병렬 권한 명시 ("plan DAG hint 기반 multi-instance 병렬 default")
3. sequential 의무 영역만 명시 (TDD red phase / schema migration / pre-existing prerequisite)
4. file-level conflict resolution 패턴 박제 ("same-file-different-method = commit atomic 분리 후 PL merge")

위 4 박제 부재 dispatch prompt 는 codeforge prereq-check hook 에서 warn (CFP-475 hook 확장).
```

→ codeforge consumer 의 default behavior 가 parallel-aware 로 전환.

---

## 4. 효과적 병렬화 패턴 (대안)

### 4.1 Plan 작성 단계 (writing-plans skill)

```markdown
### Task 9: channel parametrize

**Files:**
- Modify: `src/mctrader_data/nas_migration/backfill_orchestrator.py:350-382, 596`

**Dependencies:**
- depends_on: [Task 8]  # fixture 갱신 prerequisite
- parallel_with: [Task 10, Task 11]  # 동시 dispatch 가능
- conflict_scope: file:backfill_orchestrator.py  # Task 10 와 same-file 충돌 — commit atomic 분리 + PL merge

- [ ] Step 1: ...
```

### 4.2 Orchestrator dispatch prompt

```
DeveloperPLAgent dispatch — MCT-159 Phase 2 plan §Task 8-14.

**Parallel DAG 박제** (plan 의 parallel_with field 추출):

batch_1: [Task 8]  # fixture 갱신, TDD red phase, sequential 의무 (모든 후속 prerequisite)
batch_2: [Task 9, Task 10, Task 11]  # 의존성 disjoint, 병렬 dispatch
  - Task 9 + Task 10: same-file-different-method, commit atomic 분리 후 PL merge
  - Task 11: different-file, Task 9 signature LAND 후 자연 병렬
batch_3: [Task 12, Task 13]  # batch_2 LAND 후, 7 AC test 6-way 병렬 + perf baseline 자연 병렬
batch_4: [Task 14]  # PR + CI + merge

PL 의무:
- batch 별 multi-instance subagent 동시 dispatch
- batch 완료 후 통합 review checkpoint 1회 (개별 task review 회피)
- file-level conflict 발생 시 PL 직접 merge (subagent 회수 없이)
```

### 4.3 DeveloperPLAgent 의 실 작동

```python
# pseudo-code
plan = parse_plan(plan_path)
dag = build_dag(plan.tasks)  # depends_on / parallel_with / conflict_scope 기반
batches = topological_batches(dag)

for batch in batches:
    if len(batch) == 1:
        # sequential mode (TDD red phase, schema migration 등)
        result = await dispatch_single_subagent(batch[0])
    else:
        # parallel mode — multi-instance 동시 dispatch
        results = await asyncio.gather(*[
            dispatch_single_subagent(task) for task in batch
        ])
        if has_file_conflict(batch):
            await merge_conflicts(results)
    
    # 통합 review checkpoint (batch 단위)
    await review_checkpoint(batch, results)
```

### 4.4 pre-existing CI fix 병렬화

pre-existing CI broken = MCT-159 논리 변경 0. 그러나 본 PR 에 흡수 (ADR-YYY 권고 = 별 PR 의무, MCT-160 또는 별 chore Story).

만약 본 PR 흡수 시: ruff fix / pyright fix / test fix 가 main broken 의 disjoint 영역 → 3-way 병렬 dispatch 가능.

```
Orchestrator → 3 multi-instance dispatch:
  - ruff-fix-agent: ruff 63건 (auto-fix + 수동 27건)
  - pyright-fix-agent: pyright 28건 (# type: ignore + signature 정정)
  - test-fix-agent: test 15건 (CandleModel/Mock/scope/timeout)

3 agent 병렬 → max ~10분 (sequential ~20분 대비 2x speedup)
```

---

## 5. 본 finding 의 cross-Story 가치

본 finding 박제 = **codeforge consumer cycle 의 메타 효율** 영역. MCT-159 단독이 아니라 mctrader 전체 Story flow 의 wall-clock 감축 영향.

### 5.1 Story 평균 lead-time 추정 효과

| Story 단계 | 현 sequential wall-clock | 병렬화 후 추정 | 감축률 |
|-----------|------------------------|---------------|--------|
| Phase 0 (brainstorm) | 5-10 min (이미 병렬) | 변경 0 | 0% |
| Phase 1 (governance) | 15-20 min | 12-15 min | ~25% |
| Phase 2 (impl) | 30-60 min | 18-35 min | ~40-45% |
| pre-existing CI fix | 15-25 min (포함 시) | 8-12 min | ~50% |
| **Story 전체** | **65-115 min** | **40-65 min** | **~38-43%** |

mctrader 의 Story 누적 (현재 ~150+ Story) × Story 당 30-50분 감축 = **상당한 누적 효과**.

### 5.2 Critical path 분석

본 finding 이 해소되지 않으면:
- 모든 Story Phase 2 가 sequential bias → wall-clock 지속 손실
- codeforge consumer cycle 의 efficiency 천장 = subagent-driven-development 의 sequential 패턴 한계
- 사용자 (solo dev) 의 cognitive load = "왜 sequential 인가" 매 cycle 의문

본 finding 해소 시:
- Orchestrator + PL agent 의 자율 병렬 분석 + dispatch 패턴 박제
- Plan 작성 시 DAG 명시 의무 → 자동 병렬 batch 식별
- Story lead-time 30-45% 감축 → 사용자 frustration 감소

---

## 6. CFP Escalation Prompt (codeforge upstream issue body)

본 §6 = codeforge plugin maintainer 에게 전달되는 issue body. `mclayer/codeforge` repo 의 issue 로 직접 제출 또는 codeforge agent dispatch prompt 로 사용.

### 6.1 Issue Title

```
[CFP-TBD] codeforge consumer Orchestrator + DeveloperPLAgent 의 sequential bias 해소
(Plan DAG field + parallel dispatch 패턴 박제 의무)
```

### 6.2 Issue Body (한국어, 직접 issue submit 가능)

````markdown
## 배경

codeforge consumer (mctrader) 의 MCT-159 Phase 2 (`mctrader-data#49`) DeveloperPLAgent dispatch 가 **55분 wall-clock** 소요. plan 박제 Task 8~14 가 모두 sequential 진행되어 의존성 부재 영역 (same-file-different-method + different-file + 독립 test) 의 잠재 wall-clock 감축 ~40-45% 손실 확인.

사용자 surface (mctrader-hub `docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md` §1-§4) — codeforge consumer workaround 가 아닌 **codeforge upstream plugin 수정 의무** 영역 (memory `escalate_to_codeforge` 정합).

## 문제 6 영역 (root cause)

### F1. writing-plans skill 의 linear task 분해 bias (`claude-plugins-official/superpowers/writing-plans`)

- task 박제 시 `depends_on` / `parallel_with` / `conflict_scope` field 부재
- consumer agent 가 DAG 도출 의무 100% — 자연 sequential 진행 유도

### F2. Orchestrator dispatch prompt 의 sequential lock (codeforge consumer Orchestrator behavior)

- "plan 박제 그대로 sequential" wording 으로 PL 자율 병렬 권한 차단
- 본 세션 실측: dispatch prompt 의 "plan 의 Task 8 부터 sequential" 명시가 PL 의 병렬 분석 0건

### F3. DeveloperPLAgent 의 default sequential 패턴 (`mclayer/codeforge` develop lane)

- description = "QADev 병렬 감독" 만 박제, production code multi-instance 병렬 부재
- 실측: DeveloperAgent 1 instance + QADeveloperAgent 1 instance sequential interleave

### F4. subagent-driven-development skill 의 sequential 권고 (`claude-plugins-official/superpowers`)

- task-by-task review checkpoint = sequential default
- parallel branch escape hatch 부재

### F5. dispatching-parallel-agents skill 의 activation trigger 부재 (`claude-plugins-official/superpowers`)

- skill 진입 trigger 의 auto-detect 부재
- writing-plans + subagent-driven-development 와 cross-link 부재 → 자연 invoke 0

### F6. codeforge consumer Orchestrator template 의 default dispatch pattern (`mclayer/codeforge`)

- consumer overlay (`.claude/_overlay/CLAUDE.md`) 의 default behavior = sequential bias
- prereq-check hook (CFP-475) 의 parallel hint 검사 부재

## 제안 결정 (6 영역 각 patch)

### F1 patch — writing-plans skill task schema 확장

`### Task N` block 에 `**Dependencies:**` section 추가 의무 (또는 강력 권장):

```markdown
**Dependencies:**
- depends_on: [Task M]
- parallel_with: [Task K, Task L]
- conflict_scope: file:path/to/file.py
```

skill 의 Self-Review section 에 추가: "task DAG 분석 후 parallel batch 식별 결과 박제. parallel_with 명시 부재 시 plan 작성자가 의도적 sequential 박제 명시 의무."

### F2 patch — codeforge Orchestrator dispatch prompt template

codeforge consumer overlay 의 Orchestrator behavior 박제 (PL dispatch 시 default 4종):

```markdown
1. plan 의 task DAG 분석 결과 박제 (parallel_with batches list)
2. PL agent 에 자율 병렬 권한 명시 ("plan DAG hint 기반 multi-instance 병렬 default")
3. sequential 의무 영역만 명시 (TDD red phase / schema migration / pre-existing prerequisite)
4. file-level conflict resolution 패턴 박제 ("same-file-different-method = commit atomic 분리 후 PL merge")
```

prereq-check hook (CFP-475) 의 dispatch prompt validation 확장: 위 4 항목 누락 시 warn.

### F3 patch — DeveloperPLAgent description + 책임 amendment

description 확장:

> "구현 레인 PL — role:dev 에이전트 동적 roster + QADev **양쪽 모두 multi-instance 병렬 dispatch** (plan DAG 의 parallel_with hint 기반) + 구현 FIX 1차 원인 진단 → ArchitectPLAgent 회부."

내부 dispatch decision tree 박제 (위 §3.F3 참조).

### F4 patch — subagent-driven-development skill 에 parallel mode 추가

skill 자체에 다음 section 추가:

```markdown
## Parallel Mode (의존성 부재 task 영역)

plan 의 task DAG 에 parallel_with batch 식별 시:
1. batch 내 task 들에 대해 fresh subagent multi-instance 동시 dispatch
2. 모든 batch member 완료 후 single review checkpoint
3. file-level conflict 발생 시 merge resolution 1회

batch 내 task 가 1개 = sequential mode (현 default).
batch 내 task 가 N>1 개 = parallel mode + integrated review.

skill 자체가 plan 의 parallel_with hint 를 auto-detect + 자동 모드 전환 의무.
```

### F5 patch — superpowers skill cross-link 강화

- writing-plans skill 의 Self-Review section 에 cross-link 추가
- subagent-driven-development skill 의 진입 검토 step 에 auto-escalate 박제
- dispatching-parallel-agents skill 의 trigger condition 명시

### F6 patch — codeforge consumer overlay default 박제

codeforge consumer template (`.claude/_overlay/CLAUDE.md` 의 codeforge section) 에 §3.F6 박제 default 4종 추가. prereq-check hook 의 검증 확장.

## 예상 결과 (consumer cycle wall-clock 감축 추정)

| Story 단계 | 현 wall-clock | 병렬화 후 추정 | 감축률 |
|-----------|--------------|---------------|--------|
| Phase 0 brainstorm | 5-10 min (이미 병렬) | 변경 0 | 0% |
| Phase 1 governance | 15-20 min | 12-15 min | ~25% |
| Phase 2 impl | 30-60 min | 18-35 min | ~40-45% |
| pre-existing CI fix | 15-25 min | 8-12 min | ~50% |
| **Story 전체** | **65-115 min** | **40-65 min** | **~38-43%** |

mctrader 누적 150+ Story × 30-50분 감축 = **수십 시간 누적 효과**.

## 검증 방식

- 본 CFP patch 후 다음 Story (MCT-160 codec FIX 묶음) Phase 2 wall-clock 측정 + 본 finding 의 §2 timeline 비교
- patch 효과 = MCT-160 wall-clock < MCT-159 wall-clock × 0.6 시 verified
- patch 효과 부재 = wall-clock 감축률 < 20% 시 추가 진단 (별 CFP)

## References

- mctrader-hub `docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md` (본 finding SSOT, §1-§5)
- mctrader-hub `docs/retros/RETRO-MCT-159.md` (Phase 2 PMOAgent retro)
- `mclayer/mctrader-data#49` (MCT-159 Phase 2 PR, 55분 wall-clock 박제)
- `mclayer/mctrader-hub#281` (MCT-159 Phase 1 PR)
- `claude-plugins-official/superpowers/5.1.0/skills/writing-plans/` (F1 영역)
- `claude-plugins-official/superpowers/5.1.0/skills/subagent-driven-development/` (F4 영역)
- `claude-plugins-official/superpowers/5.1.0/skills/dispatching-parallel-agents/` (F5 영역)
- `mclayer/codeforge` consumer overlay template (F2/F6 영역)
- `mclayer/codeforge` develop lane DeveloperPLAgent agent definition (F3 영역)

## 우선순위

**HIGH** — 본 finding 미해소 시 mctrader 의 모든 Story Phase 2 가 sequential bias 누적. 매 Story 30-50분 손실 누적.

## Acceptance Criteria

- [ ] F1 patch LAND: writing-plans skill 의 task schema 에 Dependencies section 추가
- [ ] F2 patch LAND: codeforge prereq-check hook 의 dispatch prompt validation 확장
- [ ] F3 patch LAND: DeveloperPLAgent description amendment + decision tree 박제
- [ ] F4 patch LAND: subagent-driven-development skill 에 Parallel Mode section 추가
- [ ] F5 patch LAND: superpowers skill cross-link 3건 강화
- [ ] F6 patch LAND: codeforge consumer overlay default 4종 박제
- [ ] 검증: 다음 Story (MCT-160) Phase 2 wall-clock 감축 ≥ 20% 측정
````

### 6.3 Issue 제출 방식 권고

**Option A — 직접 GitHub issue 제출** (사용자 직접 또는 `gh` CLI):

```bash
gh issue create \
  --repo mclayer/codeforge \
  --title "[CFP-TBD] codeforge consumer Orchestrator + DeveloperPLAgent 의 sequential bias 해소" \
  --body-file c:/workspace/mclayer/mctrader-hub/docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md \
  --label "type:enhancement,severity:high,area:orchestrator,area:develop-lane"
```

**Option B — codeforge agent dispatch** (codeforge plugin 의 Orchestrator 가 본 finding 을 수신):

```
codeforge upstream Orchestrator 에 본 finding 박제 dispatch:

"finding source = mctrader-hub/docs/findings/2026-05-13-parallel-execution-failure-MCT-159.md
trigger = MCT-159 Phase 2 wall-clock 55min sequential bias
scope = F1~F6 6 영역 patch 의무
acceptance = §6.2 7 AC + 검증 (MCT-160 wall-clock 감축 ≥ 20%)

codeforge plugin 내부 6 영역 patch 진행 + CFP-NNN 신규 reserve + PR sequence 발의 의무."
```

**Option C — codeforge community discussion** (CFP 발의 전 사전 논의):

`mclayer/codeforge` Discussions 카테고리에 본 finding §1-§5 박제 제출 → community feedback → CFP 정식 발의.

---

## 7. 본 finding 의 follow-up actions (사용자 결정 영역)

1. **사용자 confirm** — 본 finding 의 §6 escalation prompt 를 codeforge upstream 에 제출 의무 여부
2. **CFP 신규 reserve** — `mclayer/codeforge` 의 counters / CFP reservation 박제 (codeforge plugin 자체 의 의존)
3. **patch 우선순위** — F1~F6 의 patch 순서 (F1+F2 가 가장 영향 큼, F3-F6 는 후속)
4. **mctrader-hub consumer side 적용 시점** — codeforge patch LAND 후 mctrader 의 다음 Story (MCT-160) 에 적용 + wall-clock 측정 verify

---

## 8. References

- `docs/stories/MCT-159.md` (Story SSOT, §1-§12)
- `docs/retros/RETRO-MCT-159.md` (Phase 2 PMOAgent retro, §5 pre-existing CI pattern + §11 SP 진척)
- `docs/superpowers/plans/2026-05-13-mct-159-l2l3-backlog-nas-migration.md` (Phase 2 plan SSOT, Task 8-17)
- `mclayer/mctrader-data#49` (Phase 2 PR, 55분 wall-clock 박제, merged sha 1bd50216)
- `mclayer/mctrader-hub#281` (Phase 1 PR, merged sha 670d118)
- Memory `feedback_escalate_to_codeforge` (codeforge usage mandatory + consumer workaround 금지)
- Memory `feedback_brainstorm_codex_review_pattern` (Phase 0 7 agent + Phase 1 Codex 일괄 정합)
- Memory `feedback_subagent_execution` (Always subagent-driven, 방법 묻는 stop 금지)

---

**finding LAND** — codeforge upstream escalation 의무. 사용자 confirm 시 §6 prompt 그대로 issue 제출 진행.
