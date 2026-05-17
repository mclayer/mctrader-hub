---
type: story-retrospective
story_key: MCT-192
epic_key: EPIC-evidence-quad-runtime-telemetry
status: COMPLETED
completed_at: "2026-05-17"
author: Orchestrator (self-write SSOT)
fix_loop_count: 1
land_prs:
  - "mctrader-hub#384 (c9b9f2c PR-1 hub Phase 1 docs — Story + ADR-033 §3.2 counter mapping table + scope_manifest sub-2 + counters IN_PROGRESS, MERGED 2026-05-17)"
  - "mctrader-data#79 (58d99ad squash PR-2 Phase 2 PR1 code — realtime_stream.py _emit_failure_counter no-op stub 해소 + metrics.py Counter + test, ruff SIM105 fix fee6186, MERGED 2026-05-17)"
  - "mctrader-hub#385 (1b4a727 PR-3) (PR-3 hub Phase 2 PR2 박제 — §8.5 Impl Manifest + RETRO + PMO-AUDIT + EPIC-RESULTS §Story-2)"
duration:
  start: "2026-05-17"
  end: "2026-05-17"
  hours: 4
---

# RETRO-MCT-192 — Cross-repo telemetry counter emit (ADR-029/030/031 quad evidence)

> **Story**: MCT-192. **Epic**: EPIC-evidence-quad-runtime-telemetry (sub-2, 3 sub-Story sequential 중 2번째).
> **Land window**: 2026-05-17 단일일 (brainstorm Phase 0+1+2 → spec/plan → cross-repo 3 PR sequential LAND).
> **Classification**: cross-repo (hub governance docs + data code, **engine DROP**), phase_pair=phase1_phase2.

## §1 Story summary + Q1-Q9 채택 결과

### 1.1 Story 1줄 summary

MCT-192 = ADR-033 §2 quad v2 4번째 게이트 (`telemetry_counter ≥1 over N days`) 의 실 cross-repo wiring owner Story. MCT-191 = quad rule **정의** (governance doc-only) 만 박제 → MCT-192 = 정의 → 실 counter emit wiring 으로 전환. ADR-029/030 = MCT-189/179/180 LAND production-wired counter **재사용** (신규 emit code 0, INV-1 production runtime untouched) / ADR-031 = data `realtime_stream.py:147-154` `_emit_failure_counter()` **no-op stub 해소** (실 `.inc()` + Counter 정의 신규, dead-in-data 정직 박제). EPIC-evidence-quad-runtime-telemetry sub-2, cross-repo hub+data 2-repo (engine DROP — ADR-031 pure consumer telemetry zero 정상).

3 PR cross-repo sequential LAND:
1. **PR-1 hub#384** (c9b9f2c) — Story + ADR-033 §3.2 per-ADR counter mapping table + scope_manifest sub-2 + verify_evidence_telemetry_counter_schema 3 ADR + counters IN_PROGRESS + spec + plan
2. **PR-2 data#79** (58d99ad squash) — realtime_stream.py `_emit_failure_counter()` no-op → `.inc()` + Counter 정의 + 주석 MCT-186→MCT-192 정정 + test 신규 + **ruff SIM105 fix fee6186** (try/except/pass → contextlib.suppress)
3. **PR-3 hub#385 (1b4a727 PR-3)** (본 RETRO 산출) — Story §8.5 Impl Manifest + §11 LAND timeline 실 PR# + counters COMPLETED + ADR-033 §9.1 sub-2 VERIFIED + CLAUDE.md §EPIC 1/3→2/3 + RETRO + PMO-AUDIT + EPIC-RESULTS §Story-2

### 1.2 9 결정점 (Codex 일괄 dispatch + Claude 합성, deviation 0)

| Q | 결정점 | Codex 권고 | Claude 채택 | 정합 |
|---|--------|-----------|------------|------|
| Q1 | ADR-029 counter | A | **A** 기존 `mctrader_dual_write_result_total{status,tier}` 재사용 (runner.py:285 MCT-189 LAND, 신규 emit 0) | 정합 |
| Q2 | counter granularity | A | **A** ADR 전체 1 counter (E2 cardinality 폭발 차단) | 정합 |
| Q3 | ADR-031 engine scope | C | **C** engine telemetry zero 정상 (pure consumer). ADR-031 quad = data realtime_stream producer counter. engine 변경 0 | 정합 |
| Q4 | land_order | A | **A** hub Phase1 docs (counter name SSOT) → data Phase2 PR1 emit → hub Phase2 PR2 박제 | 정합 |
| Q5 | mapping SSOT | C | **C** scope_manifest `verify_evidence.telemetry_counter` (실행 SSOT) + ADR-033 §본문 mapping table (governance reference, drift 시 scope_manifest 우선) | 정합 |
| Q6 | ADR-029 cardinality | C | **C** 기존 counter 유지 + quad query filter (`increase(...{status="success"}[14d]) >= 1`) | 정합 |
| Q7 | triad reapply 범위 | B | **B** 기존 재사용 = MCT-189/179 LAND evidence 재인용. 신규 emit (ADR-031 realtime_stream) 만 새 triad v1 | 정합 |
| Q8 | MCT-192↔193 boundary | C | **C** MCT-192 = emit + 단발성 integration test (counter ≥1 1회) / MCT-193 = over-Nd rolling + alert + monthly PMO audit | 정합 |
| Q9 | realtime_stream TODO | A | **A** MCT-192 가 `realtime_stream.py:147-154` no-op stub 해소 (실 `.inc()`, ADR-031 anchor) + 주석 MCT-186→MCT-192 정정 | 정합 |

**9/9 채택 일치 — Codex 권고 deviation 0건**. MCT-191 (10/10 deviation 0) → MCT-192 (9/9 deviation 0) = **full alignment 연속 2회**. derived default 정합 누적 trend (parent EPIC + ADR-033/032 derived + 사용자 prompt 충돌 지점 부재 — MCT-191 RETRO §Lesson 3 분석 동형 reapply, 무비판 채택 아님: D3/D4/D5/D6 anchor 정정은 실 code 실측 기반 채택).

## §2 Lessons (4건)

### Lesson A: trust-but-verify 동형 재발 3회째 — PMOAgent 2nd pass R1 false premise

brainstorm Phase 0 PMOAgent 2nd pass 가 R1 CRITICAL BLOCKER ("ADR-033 / EPIC scope_manifest / MCT-191 Story 부재 → Case A/B 분기 강제") 보고. Orchestrator 직접 `git log` + `ls`/`grep` 재verify 결과 — worktree HEAD = c9b9f2c (#384 PR-1) + 25fc1c4 (#383 MCT-191 post-merge) + 1cde1ff (#382 MCT-191 LAND) = MCT-191 sub-1 LAND 완전 반영 + ADR-033 (210L) + EPIC scope_manifest + MCT-191 Story/RETRO/PMO-AUDIT + counters MCT-191~193 entry **전부 존재** = **false premise** (잘못된 path verify 추정, worktree vs main repo stale 혼동). R1 BLOCKER 기각 — D3/D4/D5/D6 anchor 정정 + engine drop 만 채택 (실 code 실측 기반, Orchestrator 재verify confirmed).

trust-but-verify 동형 누적 3회째: MCT-190 Lesson 5 (Task 1 implementer subagent ADR-032 file 부재 false-positive 보고) → MCT-191 (plugin-codeforge#822 self-discipline gate v1 consumer reapply = 6 implementer 전수 verify report 의무, 동형 재현 0 차단) → **MCT-192 (PMOAgent 2nd pass R1 false premise 재발 — #822 self-discipline gate v1 적용에도 PMOAgent path 오류)**. #822 = implementer subagent (write 산출물) verify report 의무 범위 → PMOAgent 2nd pass 류 read-only analysis subagent 의 path/state verify 는 범위 미포함 = gap.

**Why**: subagent (PMOAgent 포함) 의 path/state verify 가 worktree vs main repo stale 혼동 시 false CRITICAL BLOCKER 생성. #822 self-discipline gate v1 은 write 산출 implementer 대상 — read-only analysis subagent (PMOAgent 2nd pass) 의 environment verify 는 미포함.

**How to apply**: Orchestrator 가 subagent (PMOAgent 포함) critical BLOCKER 보고 수령 시 **무조건 직접 `git log`/`ls`/`grep` 재verify 의무** (subagent 보고 ≠ SSOT). #822 escalation evidence row 추가 후보 — self-report verify gate 를 read-only analysis subagent (PMOAgent 2nd pass) path verify 까지 확장 (subagent 가 verify 한 path = worktree absolute path 명시 + 부재 보고 시 candidate path 전수 박제 의무).

### Lesson B: implementer "회귀 0" 보고 vs CI ruff 누락 (trust-but-verify gap 4회째)

PR-2 (data#79) Task 5 implementer 가 "회귀 0 (pytest baseline 22 failed → 22 failed / 1179, MCT-192 touch 파일 연관 0)" 보고 — pytest full suite 만 확인, **ruff lint 미포함** → CI #79 ubuntu/windows FAILURE (`ruff SIM105` — `try/except/pass` 패턴, `realtime_stream.py` `_emit_failure_counter()` no-op stub 해소 시 신규 도입). fix subagent 가 fee6186 (`contextlib.suppress` 전환) 으로 정정 → CI green. trust-but-verify gap 4회째 (Lesson A 3회 + 본 Lesson 1회 = 동형 누적 4회), 단 carrier 상이 — Lesson A = subagent path/state verify, Lesson B = subagent 회귀 verify 범위.

**Why**: implementer 의 "회귀 0" verify 가 pytest full suite 만 포함, ruff/pyright lint 미포함 → CI mechanical gate (ruff) 통과 보장 부재. "회귀 0" 의 정의가 implementer 측에서 pytest-only 로 축소 해석됨.

**How to apply**: implementer dispatch prompt 에 "회귀 0 보고 = pytest + ruff + pyright 전수 의무" 명시 박제. plugin-codeforge#822 verify report 4-항목 (file existence / line count / keyword grep / git status) 에 **lint 5번째 항목 추가 확장** (code lane implementer = `ruff check` + `pyright` 결과 verify report 첨부 의무). MCT-192 = #822 verify report schema 에 lint 항목 추가 escalation 후보.

### Lesson C: ADR-029/030 기존 counter 재사용 = 신규 emit 최소화 (가공 metric risk 구조적 축소)

Codex Q1=A / Q7=B = ADR-029/030 quad 4번째 게이트 = 기존 production-wired counter 재사용 (`mctrader_dual_write_result_total` runner.py:285 MCT-189 LAND / `mctrader_collector_ticks_total` collector.py:189 MCT-179/180 LAND) → 신규 emit code **0** + MCT-189/179/180 caller-wired triad v1 evidence 재인용. ADR-031 만 신규 emit (data realtime_stream 1곳, no-op stub 해소). MCT-179 §D8 가공 metric (LAND 후 producer caller 0 발견 패턴) 7회째 risk 를 **신규 emit 최소화 (3 ADR 중 1곳만)** 로 구조적 축소. ADR-031 신규 emit 도 `publish_tick` producer caller src/ 0건 = dead-in-data → scope_manifest `traffic_class: "test-injected only"` + `caller_wired_evidence_caveat` 정직 박제 (R2 가공 metric 차단, MCT-191 §9 self-reference Caveat telemetry 축 적용 모델 reapply).

**Why**: 신규 emit code 가 많을수록 producer caller 0 (가공 metric, MCT-179 §D8 7회째 동형) risk 누적 확대. 기존 production-wired counter 재사용 = caller-wired evidence 이미 LAND 검증 완료 → 신규 risk 0.

**How to apply**: quad telemetry counter wiring Story 의 1순위 = 기존 production-wired counter 재사용 (caller-wired evidence 재인용) > 신규 emit. 신규 emit 불가피 시 producer caller grep Phase 0 verify gate 의무 + dead-in-data (caller 0) 시 `traffic_class` + `caller_wired_evidence_caveat` scope_manifest 정직 박제 (가공 metric LAND 후 발견 → Phase 0 사전 차단 전환).

### Lesson D: engine DROP 정합 — Phase 0 verify 가 cross-repo scope 축소 trigger

session prompt / PMO-AUDIT-MCT-191 §7 권고 = "cross-repo telemetry counter emit (mctrader-data collector/api + mctrader-engine data_client/realtime/cold reader)" 명시 (3-repo 가정). Phase 0 ResearcherAgent verify (ED) = engine `data_client`/`realtime`/`cold reader` 측 prometheus import 0 + counter 0 = MCT-185 LAND engine pure consumer cutover 정합 (ADR-031 quad = **data realtime_stream producer counter**, engine subscriber = consumer telemetry zero 정상). → engine 변경 0 (INV-3), cross-repo = hub + data **2-repo 축소** (MCT-185 류 동형, engine drop). Phase 0 verify 가 단순 가설 검증이 아닌 **cross-repo scope 축소 trigger** 로 작동 (3-repo → 2-repo).

**Why**: session prompt / parent audit 권고의 cross-repo scope (3-repo) 가 가설 — engine pure consumer cutover (MCT-185 LAND) 정합 = ADR-031 telemetry producer = data only. engine 측 counter wiring 은 ADR-031 cutover 무계측 정상에 반함 (가공 metric 역방향 risk).

**How to apply**: cross-repo telemetry/wiring Story 의 Phase 0 = 각 repo 측 실 producer/consumer 경계 grep verify 의무 (prometheus import + counter caller). parent audit 권고의 repo scope = 가설로 수용, repo별 독립 verify 후 scope 축소/확대 정정 (MCT-170/177/178 cross-repo Phase 0 verify 독립 의무 동형 reapply). DROP 정합 = scope_manifest INV + Story §0 ED row 정직 박제.

## §3 cross-Story patterns

### 3.1 MCT-184 / MCT-189 / MCT-190 / MCT-191 / MCT-192 = 5 sequential governance Story (cross-Epic)

| Story | 핵심 산출 | Story bundle 패턴 | 박제 정합 |
|-------|----------|----------------|----------|
| MCT-184 | data REST API 신규 + 박제 PR incomplete (≈58% carry) | 2 PR (hub#359 + hub#361 amendment) | incomplete (SSOT drift 3호) |
| MCT-189 | ADR-029 §D3 wiring 완결 + cross-Story PR contamination 첫 박제 | 4 PR sequential | 정직 박제 (lessons 3건) |
| MCT-190 | ADR-032 본문 author + §5 보강 + memory amendment | 1 PR bundle (hub#375) + post-merge | self-reference Caveat 박제 (Q2 deviation 1건) |
| MCT-191 | ADR-032 §8.1→§3.2 격상 + ADR-033 신규 + class taxonomy | 1 PR bundle (hub#382) + post-merge | quad self-reference 첫 적용 (deviation 0건) |
| **MCT-192** | **cross-repo telemetry counter emit (ADR-029/030 재사용 + ADR-031 신규 emit, engine DROP)** | **3 PR cross-repo sequential (hub#384 + data#79 + hub#385 (1b4a727 PR-3))** | **quad 4th gate 첫 실 wiring + dead-in-data 정직 박제 (deviation 0건)** |

→ governance Story 패턴 진화: MCT-184 (incomplete) → MCT-189 (4 PR + 정직 박제) → MCT-190 (1 PR bundle + self-reference Caveat) → MCT-191 (1 PR bundle 안정화 + quad self-reference 첫 적용) → **MCT-192 (quad rule 정의 → 실 cross-repo wiring 전환, ADR-032 evidence triad → quad reapply 실 시점)**. MCT-191 = quad rule SSOT 정의 (caller_wired + telemetry "0건" self-reference Caveat) → **MCT-192 = quad evidence 실 누적 시작 시점** (ADR-029/030 production-wired counter 14d + ADR-031 test-injected only dead-in-data).

### 3.2 ADR-032 evidence triad → quad 확장 reapply 실 시점 = MCT-192 (정의→실 wiring 전환)

MCT-191 RETRO §3.2 = "quad evidence 실 누적 시작 = sub-2 MCT-192 부터". 본 Story 가 그 reapply 실 시점:

evidence quad v2 (4 evidence) 실 적용:
1. file:line — ADR-031 `realtime_stream.py:147-154` + Counter 정의 박제 (PR-2 data#79 58d99ad)
2. caller grep ≥1 — `_emit_failure_counter` line 145 `publish_tick` 내부 호출 (PR-2 verify)
3. integration test PASS — `tests/api/test_realtime_stream_counter.py` XADD fail inject → counter ≥1 단발성 (T-1 PASS)
4. **telemetry_counter ≥1 over N days** — ADR-029/030 = production-wired 14d (`mctrader_dual_write_result_total` / `mctrader_collector_ticks_total` 재사용) / ADR-031 = `increase(...[14d]) >= 0` **test-injected only (dead-in-data, MCT-193 rolling gate prerequisite)**

self-reference Caveat telemetry 축 reapply:
- ADR-029/030 = production-wired, caller-wired evidence 이미 MCT-189/179/180 LAND 검증 완료 → quad telemetry 게이트 정상 적용 (재사용)
- ADR-031 = `publish_tick` producer caller src/ 0건 (dead-in-data) → `caller_wired_evidence_caveat` + `traffic_class: test-injected only` 정직 박제 (MCT-191 governance ADR `telemetry_counter_caveat` 의 production-wired-pending ADR 축 변형 reapply). production caller-wired = MCT-186 engine cutover 후 또는 MCT-193 rolling gate prerequisite

### 3.3 Phase 0 verify lesson 10회째 history (MCT-170~192 누적 — 사전 차단 3번째)

| Story | lesson | 차단 방식 |
|-------|--------|----------|
| MCT-170~189 | engine io/ 3 module / cross-repo Phase 0 독립 의무 / promote_l1 caller 0건 (7회 사후 발견·정정) | Phase 0 verify 정정 + 별 Story |
| MCT-190 | cross-Story PR contamination (worktree share) | 8회째 = 사전 차단 1번째 (worktree 격리) |
| MCT-191 | doc-only cross-repo 0 회피 + F-0a 가설 5건 선제 정정 | 9회째 = 사전 차단 2번째 (doc-only + worktree 2축) |
| **MCT-192** | **PMOAgent 2nd pass R1 false premise + engine DROP scope 축소 (ED) + D3/D4/D5/D6 anchor 정정** | **10회째 = 사전 차단 3번째 (Orchestrator 직접 `git log`/`grep` 재verify 가 subagent SSOT 보다 우선, false premise 사전 기각 + scope 축소 trigger)** |

→ Phase 0 verify lesson = MCT-170~189 (7회 사후 발견) → MCT-190~192 (8~10회째 사전 차단 3연속). MCT-192 = Orchestrator 직접 verify 가 subagent (PMOAgent 2nd pass) 보고보다 우선하는 forcing function 정착 — false premise 사전 기각 (정정 비용 0) + engine DROP scope 축소 trigger 동시 작동.

## §4 carry over (3건)

1. **sub-3 MCT-193 (post-LAND verify gate 운영)** — MCT-192 LAND ✓ 후 진입:
   - Prometheus alert rule `increase(counter[Nd])==0` over N days → critical + GitHub issue 자동 발의 (Q7=C / Q8=C boundary)
   - monthly PMO audit batch cron (Q7=C)
   - Q4+Q10=C traffic class 차등 window 운영 (production-wired=14d / collector tick=market-open rolling / governance=N/A Caveat)
   - ADR-033 Status transition: Proposed (MCT-191) → sub-2 LAND (MCT-192 counter emit wiring) → Accepted (sub-3 MCT-193 LAND 후) → POLICY_FINALIZED (EPIC 3/3 milestone COMPLETED)

2. **ADR-031 production caller-wired transition** — MCT-192 = dead-in-data 정직 박제 (`publish_tick` caller src/ 0건, test-injected only):
   - production caller-wired = **MCT-186 engine realtime cutover 후** (engine subscriber → data realtime_stream producer 실 호출 경로 형성) **또는 MCT-193 rolling gate prerequisite**
   - dead-in-data → caller-wired transition carrier = MCT-186 또는 MCT-193 (scope_manifest `caller_wired_evidence_caveat` resolve 시점)

3. **plugin-codeforge#822 escalation evidence row 추가 후보 (2건)** — post-merge step P4 PMOAgent retro dispatch 시 발의 의무:
   - **(a) PMOAgent 2nd pass path verify gap** — #822 self-discipline gate v1 (subagent verify report 의무) 가 implementer write 산출물 대상 → read-only analysis subagent (PMOAgent 2nd pass) 의 path/state verify 미포함 = false CRITICAL BLOCKER gap. self-report verify gate 를 read-only analysis subagent 까지 확장 (verify 한 path = worktree absolute path 명시 + 부재 보고 시 candidate path 전수 박제 의무)
   - **(b) implementer 회귀 verify lint 미포함** — #822 verify report 4-항목 (file/line/grep/git status) 에 lint 5번째 항목 추가 (code lane implementer = `ruff check` + `pyright` 결과 verify report 첨부 의무, "회귀 0" = pytest-only 축소 해석 차단)

## §5 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | 전수 PASS (요구사항/설계/설계-리뷰 PASS + 구현 PR-1 hub docs + PR-2 data code FIX iter1 ruff SIM105 + 구현-리뷰 PASS + 통합테스트 T-1 PASS + 보안 SKIP) |
| FIX 루프 | **1회** (code lane PR-2 data#79 — ruff SIM105 try/except/pass → contextlib.suppress fee6186. design lane PR-1 spec review iter1 PASS FIX 0회) |
| 14 file 산출 | ALL LAND (PR-1 F1-F4 + Ref1/Ref2 / PR-2 F6-F7 / PR-3 F8-F14 본 post-merge) |
| ADR-033 status | Proposed 유지 (sub-2 LAND = §9.1 sub-2 VERIFIED + §본문 per-ADR mapping table amend, Accepted = sub-3 LAND 후) |
| ADR-029/030 status | 기존 production-wired counter 재사용 (신규 emit 0, INV-1 production runtime untouched). MCT-189/179/180 caller-wired triad v1 재인용 |
| ADR-031 status | data realtime_stream 신규 emit (no-op stub 해소) + dead-in-data 정직 박제 (`publish_tick` caller 0, traffic_class test-injected only) |
| 9 결정점 | Q1-Q9 전수 채택 (9/9 Codex 정합, **deviation 0건**, MCT-191 10/10 동형 full alignment 연속 2회) |
| trust-but-verify 동형 | 3회째 (PMOAgent 2nd pass R1 false premise) — Orchestrator 직접 `git log`/`grep` 재verify 가 subagent SSOT 보다 우선 (false premise 사전 기각, D3/D4/D5/D6 anchor 정정만 채택) |
| implementer ruff 누락 | 4회째 (PR-2 "회귀 0" pytest-only → CI ruff SIM105 FAILURE, fee6186 fix). #822 verify report lint 항목 추가 escalation 후보 |
| 기존 counter 재사용 | ADR-029/030 신규 emit 0 (caller-wired evidence MCT-189/179/180 재인용) = MCT-179 §D8 가공 metric 7회째 risk 구조적 축소 |
| engine DROP | 정합 (ED ResearcherAgent verified — MCT-185 pure consumer cutover, ADR-031 quad = data producer counter, engine 변경 0 INV-3). cross-repo 축소 hub+data 2-repo |
| Phase 0 verify lesson | 10회째 = 사전 차단 3번째 (Orchestrator 직접 verify > subagent 보고, false premise 사전 기각 + scope 축소 trigger) |

**Story 진화 정합**: MCT-184 incomplete → MCT-189 4 PR + 정직 박제 → MCT-190 1 PR bundle + self-reference Caveat → MCT-191 1 PR bundle 안정화 + quad self-reference 첫 적용 (정의) → **MCT-192 quad 4th gate 첫 실 cross-repo wiring (정의→실 wiring 전환) + dead-in-data 정직 박제 + Codex deviation 0 연속 2회 + trust-but-verify 동형 재발 정직 박제 (Orchestrator 직접 verify forcing function 정착)**.

## Key References

- Story: `docs/stories/MCT-192.md` (377 lines, §0-§12 + §8.5 Impl Manifest 3 ADR quad evidence + §9.1 trust-but-verify 동형 재발 박제)
- spec: `docs/superpowers/specs/2026-05-17-MCT-192-telemetry-emit-design.md` (Phase 0 5 agent burst + Codex 9 결정점 일괄 dispatch Q1-Q9)
- plan: `docs/superpowers/plans/2026-05-17-mct-192-telemetry-emit.md` (14 file task decomposition, 3 PR sequential)
- ADR-033 amend: `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` (§본문 per-ADR counter mapping table + §9.1 sub-2 VERIFIED, Proposed 유지)
- ADR-029/030/031: counter mapping (`mctrader_dual_write_result_total` 재사용 / `mctrader_collector_ticks_total` 재사용 / `mctrader_data_redis_stream_publish_failures_total` 신규 emit)
- scope_manifest: `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` (sub-2 + verify_evidence_telemetry_counter_schema 3 ADR, YAML valid)
- PMO audit: `docs/retros/PMO-AUDIT-MCT-192.md` (post-merge step P1 산출, §lane gate + R1 false premise 기각 박제 + KPI trend)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md` §Story-2 (milestone 2/3, post-merge 산출)
- 선례 RETRO: `docs/retros/RETRO-MCT-191.md` (Orchestrator self-write SSOT, CFP-138/ADR-045 4-field schema, lesson 4건 + deviation 0)
- upstream: plugin-codeforge#822 (subagent self-report verify gate v1 — escalation evidence row 추가 후보 2건: PMOAgent 2nd pass path verify + implementer 회귀 lint) + #804/#805 (CI mechanical gate consumer carry, ADR-033 §8)
- LAND: hub#384 (c9b9f2c PR-1 docs) + data#79 (58d99ad squash PR-2 code + ruff fix fee6186) + hub#385 (1b4a727 PR-3) (PR-3 박제 — counters COMPLETED + Story §11 + 본 RETRO + PMO-AUDIT + EPIC-RESULTS §Story-2)
