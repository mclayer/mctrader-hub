---
type: story-retrospective
story_key: MCT-191
epic_key: EPIC-evidence-quad-runtime-telemetry
status: COMPLETED
completed_at: "2026-05-17"
author: Orchestrator (self-write SSOT)
fix_loop_count: 0
land_prs:
  - "mctrader-hub#382 (6582cc7 squash 1cde1ff, MERGED 2026-05-17T02:29:47Z) Phase 1 12 file"
  - "mctrader-hub#TBD-post-merge"
duration:
  start: "2026-05-17"
  end: "2026-05-17"
  hours: 5
---

# RETRO-MCT-191 — Evidence quad governance amendment (ADR-032 §8.1→§3.2 본문 격상 + ADR-033 신규 + class taxonomy)

> **Story**: MCT-191. **Epic**: EPIC-evidence-quad-runtime-telemetry (sub-1, 3 sub-Story sequential 중 1번째).
> **Land window**: 2026-05-17 단일일 (brainstorm Phase 0+1+2 → spec/plan → 12 file author → 단일 PR LAND).
> **Classification**: doc-only-fast-path (phase1_only, code lane 부재).

## §1 Story summary + 10 결정점 채택 결과

### 1.1 Story 1줄 summary

MCT-191 = ADR-032 §8.1 future-work ("Evidence triad 4번째 게이트 runtime telemetry counter — 별 Story MCT-NNN owner") 의 본문 rule 격상 owner Story. triad v1 (`file:line + caller_grep ≥1 + integration_test PASS`) 의 caller-grep dead-in-prod false-negative 한계 (Hyrum's Law 역방향, MCT-184/180/179 동형 3건) 를 quad v2 (`+ telemetry_counter ≥1 over N days`) 로 차단. EPIC-evidence-quad-runtime-telemetry sub-1, doc-only governance amendment Story (phase1_only, classification: doc-only-fast-path).

5 deliverable scope:
1. ADR-033 신규 author (`docs/adr/ADR-033-evidence-quad-enforcement-layer.md`, §1-§10, Proposed)
2. ADR-032 amend (§8.1 future-work → §3.2 본문 rule 격상 + §9 `telemetry_counter_caveat` field + frontmatter `class: governance`)
3. domain knowledge author (`docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`, triad 페이지 §5 sibling cross-ref)
4. ADR-029/030/031 frontmatter `class: production` additive reapply (3 스타일 비동질 보존)
5. class taxonomy 체계화 (ADR-033 §3 `class: governance|production|mixed`) + EPIC scope_manifest + Story + CLAUDE.md + counters.json

단일 PR bundle LAND (hub#382, 6582cc7 squash 1cde1ff, MERGED 2026-05-17T02:29:47Z, 12 file 1556+/3-) + post-merge cleanup 별 PR (MCT-190 선례 정합).

### 1.2 10 결정점 (Codex 일괄 dispatch + Claude 합성, deviation 0)

| Q | 결정점 | Codex 권고 | Claude 채택 | 정합 |
|---|--------|-----------|------------|------|
| Q1 | Story 분해 | C | **C (사용자 confirm)** small Epic 3 sub-Story | 정합 |
| Q2 | ADR carrier | C | **C** hybrid (ADR-032 §8.1→본문 격상 + §9 Caveat 확장 + 신규 ADR-033 enforcement) | 정합 |
| Q3 | grandfathering scope | C | **C** production-wired ADR만 quad 의무 + governance ADR triad v1+Caveat | 정합 |
| Q4 | N days window | C | **C** traffic class 차등 (production-wired=14d / governance=N/A / trading-hot=market-open rolling) | 정합 |
| Q5 | quad vs triad×2 | C | **C** quad 4 evidence flat + counter-emit path triad v1 reapply (meta-recursion 1단 한정) | 정합 |
| Q6 | governance/production 분류 | B | **B** ADR frontmatter `class: governance\|production\|mixed` taxonomy | 정합 |
| Q7 | enforcement timing | C | **C** Prometheus alert (counter==0 over Nd → critical + GitHub issue) + monthly PMO audit | 정합 |
| Q8 | counter family SSOT | C | **C** per-ADR scope_manifest `verify_evidence.telemetry_counter` field | 정합 |
| Q9 | domain knowledge | A | **A** `governance/evidence-quad-runtime-telemetry.md` 신규 (triad 페이지 §5 sibling) | 정합 |
| Q10 | market-closed window | C | **C** traffic class 차등 (collector=market-open rolling / engine cold=14d / governance=N/A) | 정합 |

**10/10 채택 일치 — Codex 권고 deviation 0건**. Q1 = AskUserQuestion 사용자 confirm (small Epic 3 sub-Story 분해). MCT-190 5 결정점 Q2 deviation 1건 대비 **full alignment** — derived default 정합 누적 효과 (§2 Lesson 3 분석).

## §2 Lessons (4건)

### Lesson 1: F-0a Phase 0 verify 최대 가치 — quad = ADR-032 §8.1 future-work 본문 격상 (신규 발명 아님) → R1 HIGH 선제 완화

brainstorm Phase 0 첫 act = 코드/파일 실측 (memory `feedback_phase0_verify_mandatory` 정합). session prompt 가설 "ADR-032 §8/§9 신규 보강" 을 실측 정정: §8.1 이미 quad 4th gate future-work 명시 (`ADR-032.md:196-200`) + §9 이미 Self-reference Caveat + INV-1 보유 (`ADR-032.md:212-227`). → quad 확장 = **future-work 본문 격상** (신규 발명 아님).

PMO Phase 0 주요 위험 = R1 HIGH ("§9 Self-reference Caveat quad 호환성 미검증 시 governance ADR 자체 영구 fail = 자가붕괴"). F-0a 가 이 R1 을 **선제 완화**: §9 가 이미 `caller_wired_caveat` + INV-1 forcing function 보유 → quad Caveat = telemetry 축 확장 (`telemetry_counter_caveat` field 1개 추가) 만으로 충분. 신규 발명이 아니므로 cross-document drift risk 대폭 ↓ + Q3=C grandfathering 구조적 면제.

**Why**: session prompt 의 "신규 보강" 표현이 가설로 수용되었으나 실측은 "기존 구조 정합 격상". 가설을 verified-via 로 정정하지 않았다면 ADR-032 §9 를 중복 재설계 (R2 cross-document SSOT drift 증폭) + R1 HIGH 잔존. F-0a~F-0e 가설 5건 선제 정정이 design lane FIX 0회 + R1 구조적 면제의 직접 원인.

**How to apply**: governance ADR amendment Story 의 Phase 0 첫 act = 대상 ADR §전수 실독 (line range 박제) + "신규 발명 vs 기존 구조 격상" 이분 판정 의무. 기존 §N future-work / Caveat / INV forcing function 보유 시 = 본문 격상 (delta only) → cross-document drift risk + HIGH risk 선제 면제. spec §1.2 verified facts table 박제 의무.

### Lesson 2: plugin-codeforge#822 self-discipline gate v1 consumer reapply 효과 1회 실증 — 6 implementer subagent 전수 verify report 의무

MCT-190 Lesson 5 = Task 1 implementer subagent 가 ADR-032 본문을 worktree path 가 아닌 main repo path 에 write 시도 → file 부재 → 그러나 "DONE_WITH_CONCERNS" 성공 보고 (trust-but-verify gap). MCT-191 = 본 gap 재현 차단을 위해 plugin-codeforge#822 (subagent self-report verify gate v1) consumer reapply — 6 implementer subagent 전원에게 "Write 후 자동 file existence + line count + grep keyword + git status 4-항목 verify report 의무, 부재 시 BLOCKED 반환" instruction 강제.

효과 실증: Task 1 (ADR-033 신규 author) 가 MCT-190 Task 1 (ADR-032 author) 와 동형 risk (file 부재 false-positive 보고) 보유했으나 — verify report 4-항목 강제로 file 부재 risk **0 달성** (12 file 전수 LAND, hub#382 1556+ confirm). MCT-190 trust-but-verify gap 재현 차단의 첫 caller-wired evidence.

**Why**: subagent 보고 = intent (의도된 작업) ≠ actual (실제 결과). MCT-190 에서 Orchestrator git status verify 로 사후 발견 (정정 비용 1회 직접 write). MCT-191 = subagent self-report verify report 의무화로 **사전 차단** (사후 발견 → 사전 차단 전환). self-discipline gate v1 의 3-tier (subagent self-report / Orchestrator git status / PMO audit) 중 1-tier 를 subagent 측으로 push-down.

**How to apply**: implementer subagent dispatch prompt 에 verify report 4-항목 (file existence Read line 1-5 / line count / keyword grep hit count / git status --short) + "verify report 부재 시 BLOCKED 반환 의무" 강제 instruction 의무 박제. critical artifact (ADR/spec/Story) 작성 subagent = 예외 없이 적용. ADR-032 §3.1.3 PMO audit gate consumer reapply.

### Lesson 3: Codex 10 결정점 deviation 0 (MCT-190 Q2 deviation 1건 대비 full alignment) — derived default 정합 누적 효과

memory `feedback_brainstorm_codex_review_pattern` 정합 = 10 결정점 (Q1-Q10) 1회 burst dispatch → Claude 합성 (Q-by-Q 사용자 stop 회피, Sonnet decider 금지). 결과 = **10/10 Codex 권고 채택 일치, deviation 0건**. MCT-190 = 5 결정점 중 Q2 deviation 1건 (Codex C hub+data만 ↔ Claude B tier 차등, 사용자 prompt verbatim 우선).

deviation 0 의 의미 분석:
- MCT-190 RETRO §Lessons.4 = "5 결정점 중 1건 deviation = 정상 calibration 신호 (full alignment = 의심)". MCT-191 deviation 0 = 본 신호와 표면 충돌 — 그러나 **사유 정상**.
- MCT-191 10 결정점 = 전부 EPIC-evidence-quad-runtime-telemetry 의 derived default (triad v1 SSOT = ADR-032, MCT-190 LAND 직후 sub-1). Codex 권고 = ADR-032 기존 구조 + Q3=C grandfathering + traffic class 차등 derived → 사용자 의도와 충돌 지점 부재 (MCT-190 Q2 = "6 repo 전수" verbatim vs over-generalization 균형 = 사용자 prompt 충돌 지점 존재했음).
- Q1 (Story 분해) = AskUserQuestion 사용자 confirm 으로 사용자 의도 명시 channel 보존 (deviation channel 대체).

**Why**: deviation 0 가 정상인 경우 = (1) 결정점이 전부 parent ADR derived default + (2) 사용자 의도 충돌 지점 부재 + (3) AskUserQuestion 으로 사용자 confirm channel 별도 보존. full alignment 의심 신호는 "Codex 무비판 채택" 일 때만 valid — derived default 정합은 무비판 아님.

**How to apply**: deviation 0 보고 시 "정상 vs 무비판 채택" 이분 판정 의무 박제. 정상 조건 = parent ADR/Epic derived default + 사용자 confirm channel (AskUserQuestion) 별도 보존. deviation 0 이면서 derived default 아님 + 사용자 confirm 부재 시 = Codex 무비판 채택 risk → 재검토.

### Lesson 4: ADR-032 self-reference quad 첫 적용 (telemetry_counter_caveat governance ADR forever 0 정상) — governance 시스템 자가붕괴 차단 INV

ADR-032 evidence triad → quad 확장의 첫 self-reference 적용. 본 Story = governance ADR singleton 산출 (ADR-033 신규 Proposed) 이므로 caller_wired + telemetry_counter 모두 LAND 시점 0건. quad verify gate 가 이를 영구 fail 처리하면 governance ADR 자체 = 영구 fail (자가붕괴). Story §8.5.2 verify_evidence row 에 `telemetry_counter_caveat` field 박제: "governance ADR (class:governance) telemetry counter forever 0 정상 — ADR-033 §7 grandfathering (Q3=C production-wired만 quad). false-positive fail 차단 INV (R1 mitigation, governance 시스템 자가붕괴 차단)".

triad → quad self-reference Caveat 진화:
- MCT-190 = `caller_wired_caveat` 박제 (governance ADR 첫 publication caller_grep 부재 정상, MCT-NNN reapply 시점부터 누적)
- MCT-191 = `telemetry_counter_caveat` 박제 (governance ADR class telemetry forever 0 정상, caller_wired 와 달리 누적 시작 시점도 없음 — 영구 면제)

→ caller_wired Caveat (지연 누적) vs telemetry_counter Caveat (영구 면제) 의 의미 차이 박제. governance ADR 은 production traffic 부재가 본질 → telemetry counter 누적 자체가 불가 (영구 0 정상).

**Why**: evidence quad 의 4번째 게이트 (telemetry counter ≥1) 가 governance ADR 에 무차별 적용되면 governance 시스템 (ADR-032/033/045/064) 이 자기 자신의 verify gate 에 영구 fail → governance 자가붕괴. Q3=C grandfathering (production-wired ADR만 quad 의무) + `telemetry_counter_caveat` field 의 2-tier 차단이 INV.

**How to apply**: governance ADR (class:governance) 의 scope_manifest verify_evidence row 에 `telemetry_counter_caveat` field 의무 박제 — "governance ADR class telemetry counter forever 0 정상, false-positive fail 차단 INV". production-wired ADR (class:production) 만 quad telemetry 게이트 적용. ADR frontmatter `class:` taxonomy (ADR-033 §3) 가 grandfathering 분류 SSOT.

## §3 cross-Story patterns

### 3.1 MCT-184 / MCT-189 / MCT-190 / MCT-191 = 4 sequential governance Story (cross-Epic) — 1 PR bundle + post-merge cleanup 패턴 정합 진화

| Story | 핵심 산출 | Story bundle 패턴 | 박제 정합 |
|-------|----------|----------------|----------|
| MCT-184 | data REST API 신규 + 박제 PR incomplete (≈58% carry) | 1 PR + 1 별 amendment PR (hub#359 → hub#361) | incomplete (carry) |
| MCT-189 | ADR-029 §D3 wiring 완결 + cross-Story PR contamination 첫 박제 | 4 PR sequential (hub#357 + data#73 + data#75 + hub#363) | 정직 박제 (lessons 3건) |
| MCT-190 | ADR-032 본문 author + §5 보강 + memory amendment | 1 PR bundle (hub#375) + post-merge cleanup 별 PR | self-reference Caveat 박제 (Q2 deviation 1건) |
| **MCT-191** | **ADR-032 §8.1→§3.2 격상 + ADR-033 신규 + class taxonomy** | **1 PR bundle (hub#382 12 file) + post-merge cleanup 별 PR** | **quad self-reference 첫 적용 (deviation 0건)** |

→ governance Story 패턴 진화: MCT-184 (incomplete) → MCT-189 (4 PR sequential + 결함 정직 박제) → MCT-190 (1 PR bundle + self-reference Caveat + worktree 사전 차단) → **MCT-191 (1 PR bundle 안정화 + quad self-reference 첫 적용 + verify report 의무 reapply)**. governance Story 운영 성숙도 누적 ↑↑↑ (1 PR bundle + post-merge cleanup 패턴 = MCT-190/191 2회 정합 = 패턴 안정화).

### 3.2 ADR-032 evidence triad → quad 확장 reapply 시점 = MCT-192+ 부터 누적

MCT-191 = quad rule v2 정의 SSOT (ADR-032 §3.2 + ADR-033 §2) 박제 완결. 그러나 본 Story 는 doc-only governance singleton — caller-wired + telemetry_counter evidence "0건" (self-reference Caveat). quad evidence 실 누적 시작 = sub-2 MCT-192 (cross-repo telemetry counter emit, data collector/api + engine data_client/realtime/cold reader) 부터.

evidence quad v2 (4 evidence):
1. file:line — `docs/adr/ADR-033-*.md:NN` reference 박제
2. caller grep ≥1 — `git grep ADR-033` consumer Story scope_manifest 박제
3. integration test PASS — caller Story 측 통합테스트 PASS evidence
4. **telemetry_counter ≥1 over N days** — Prometheus Counter monotonic emit (production-wired만, traffic class 차등 N days)

self-reference Caveat (R1 mitigation):
- `caller_wired_caveat` (MCT-190) = governance ADR 첫 publication caller_grep 부재 정상, MCT-192+ reapply 시점부터 누적 (지연 누적)
- `telemetry_counter_caveat` (MCT-191) = governance ADR class telemetry forever 0 정상, Q3=C grandfathering 구조적 면제 (영구 면제)

### 3.3 Phase 0 verify lesson 9회째 history (MCT-170~191 누적 — 사전 차단 3번째)

| Story | lesson | 차단 방식 |
|-------|--------|----------|
| MCT-170 | engine io/ 3 module 존재 미인지 (재구현 가설 오류) | Phase 0 verify (counters.json + scope_manifest 정정) |
| MCT-177 | data 동기 SIGTERM stub cross-repo 오적용 | CodeReviewPL FIX iter1 ArchitectPL (A) dead path 제거 |
| MCT-178~180 | cross-repo Phase 0 verify 독립 의무 누적 5회 재현 | spec amend |
| MCT-182 | CandleModel 5곳 가설 정정 (실측 4곳, docstring 오집계) | Phase 0 verify 정정 박제 |
| MCT-189 | promote_l1() caller 0건 발견 (decision-defined ≠ caller-wired) | ADR-032 trigger + 별 Story 4 PR sequential |
| MCT-190 | cross-Story PR contamination (MCT-186 working tree share) | **8회째 = 사전 차단 1번째** (worktree 격리 의도적 활용) |
| **MCT-191** | **doc-only cross-repo 0 구조적 회피 + worktree 격리 (MCT-186 IN_PROGRESS share risk) + F-0a 가설 5건 선제 정정** | **9회째 = 사전 차단 2번째** (doc-only + worktree 2축 결합, 정정 비용 0) |

→ Phase 0 verify lesson = MCT-170 ~ MCT-189 (7회 = 사후 발견·정정) → MCT-190 (8회째 = 사전 차단 1번째) → MCT-191 (9회째 = 사전 차단 2번째). 사후 발견 → 사전 차단 forcing function 전환 누적 효과 실증 (MCT-190 forcing function reapply). doc-only Story = cross-repo 0 구조적 회피 + worktree 격리 2축 결합 = Phase 0 verify gap 구조적 회피 (정정 비용 0).

## §4 carry over (3건)

1. **sub-2 MCT-192 (cross-repo telemetry counter emit)** — MCT-191 Phase 1 PR MERGED ✓ 후 진입:
   - mctrader-data collector/api + mctrader-engine data_client/realtime/cold reader 측 Prometheus Counter emit 신규
   - counter-emit code path triad v1 reapply (Q5=C meta-recursion 1단 한정, MCT-179 §D8 가공 metric risk 차단)
   - Q8=C per-ADR scope_manifest `verify_evidence.telemetry_counter` field 적용 (counter name + family + emit location)
   - phase_pair=phase1_phase2 (cross-repo code lane 존재) — doc-only sub-1 과 분류 상이

2. **sub-3 MCT-193 (post-LAND verify gate 운영)** — MCT-192 LAND ✓ 후 진입:
   - Prometheus alert rule `increase(counter[Nd])==0` → critical + GitHub issue 자동 발의 (Q7=C)
   - monthly PMO audit batch cron (Q7=C)
   - Q4+Q10=C traffic class 차등 window 운영 (production-wired=14d / collector tick=market-open rolling / engine cold reader=14d calendar / governance=N/A Caveat)
   - ADR-033 Status transition: Proposed (MCT-191 LAND) → Accepted (sub-2 + sub-3 LAND 후) → POLICY_FINALIZED (EPIC 3/3 milestone COMPLETED)

3. **post-merge cleanup PR (본 RETRO 산출 step P1-P4)** — PR #382 LAND 후 별 cleanup PR 박제 의무:
   - P1: ☐ `.codeforge/counters.json` MCT-191 IN_PROGRESS → COMPLETED + completed_at + land_prs 실 PR# 박제 (별 commit on main, worktree exit 후) + Story §11 LAND timeline 실 commit sha + PR# 박제
   - P1: ☐ RETRO-MCT-191.md (본 file) + PMO-AUDIT-MCT-191.md (§lane gate + quad self-reference verify) + EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md §Story-1 (milestone 1/3)
   - P2: ☐ 별 cleanup PR open + admin merge (MCT-190 post-merge 패턴 정합)
   - P3: ☐ PR `gate:retro-complete` label add (CFP-138 / ADR-045 forcing function 정합)
   - P4: ☐ PMOAgent retro final dispatch (memory `feedback_pmo_retro_mandatory` 정합 — 본 RETRO §Lessons 4건 + §cross-Story patterns 추가 박제)

## §5 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | 전수 PASS (code lane BYPASS + 통합테스트 SKIP + 보안테스트 BYPASS + design lane PASS, doc-only fast-path 정합) |
| FIX 루프 | 0회 (design lane spec review iter1 PASS, code lane 부재 doc-only) |
| 12 file author | ALL LAND (ADR-033 신규 + ADR-032 amend + domain knowledge + ADR-029/030/031 frontmatter class + Story + EPIC scope_manifest + CLAUDE.md + counters.json + spec + plan) |
| ADR-033 status | 신규 Proposed (Accepted = sub-2/3 LAND 후) |
| ADR-032 status | Accepted 유지 (§8.1 future-work → §3.2 본문 격상 transition) |
| 10 결정점 | Q1-Q10 전수 채택 (10/10 Codex 정합, **deviation 0건**) |
| F-0a 선제 완화 | quad = ADR-032 §8.1 future-work 본문 격상 (신규 발명 아님) → R1 HIGH 구조적 면제 |
| self-reference quad | ADR-032 quad 첫 적용 (`telemetry_counter_caveat` field 박제, governance ADR forever 0 정상 INV) |
| subagent verify report | 6 implementer 전수 verify report 의무 (plugin-codeforge#822 consumer reapply) — Task 1 file 부재 risk 0 (MCT-190 trust-but-verify gap 재현 차단 실증) |
| Phase 0 verify lesson | 9회째 = 사전 차단 2번째 (doc-only cross-repo 0 + worktree 격리 2축 결합, 정정 비용 0) |
| MCT-186 contamination | 회피 (worktree mct-191-evidence-quad + mct-191-post-merge 격리, MCT-190 8회째 forcing function reapply) |

**Story 진화 정합**: MCT-184 incomplete → MCT-189 4 PR sequential + 정직 박제 → MCT-190 1 PR bundle + self-reference Caveat + worktree 사전 차단 → MCT-191 1 PR bundle 안정화 + quad self-reference 첫 적용 + deviation 0 + subagent verify report 의무 reapply (governance Story 운영 ↑↑↑, 1 PR bundle + post-merge cleanup 패턴 안정화 2회 정합).

## Key References

- Story: `docs/stories/MCT-191.md` (332 lines, §0-§12 + §8.5 Impl Manifest quad self-reference 첫 적용)
- spec: `docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md` (Phase 0 4 agent burst + Codex 10 결정점 일괄 dispatch)
- plan: `docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md` (10 task decomposition, file disjoint 4 batch)
- ADR-033 본문: `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` (신규 Proposed, MCT-191 LAND)
- ADR-032 amend: `docs/adr/ADR-032-verified-badge-evidence-triad.md` (§3.2 quad v2 + §9 telemetry_counter_caveat + frontmatter class:governance, Accepted 유지)
- domain-knowledge: `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md` (신규, triad 페이지 §5 sibling cross-ref)
- scope_manifest: `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` (EPIC + MCT-191 SSOT, YAML valid)
- PMO audit: `docs/retros/PMO-AUDIT-MCT-191.md` (post-merge step P1 산출, §lane gate + quad self-reference verify)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md` §Story-1 (milestone 1/3, post-merge step P1 산출)
- 선례 RETRO: `docs/retros/RETRO-MCT-190.md` (Orchestrator self-write SSOT, lesson 6건 + carry over 3건, Q2 deviation 1건)
- upstream: plugin-codeforge#822 (subagent self-report verify gate v1, 6 implementer consumer reapply) + #804/#805 (CI mechanical gate consumer carry, ADR-033 §8)
- LAND: hub#382 (6582cc7 squash 1cde1ff, MERGED 2026-05-17T02:29:47Z, 12 file 1556+/3-) + post-merge cleanup PR (counters COMPLETED + Story §11 + 본 RETRO + PMO-AUDIT + EPIC-RESULTS §Story-1)
