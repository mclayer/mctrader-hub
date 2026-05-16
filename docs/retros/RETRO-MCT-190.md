---
type: story-retrospective
story_key: MCT-190
epic_key: cross-Epic governance
status: COMPLETED
completed_at: "2026-05-17"
author: Orchestrator (self-write SSOT)
fix_loop_count: 0
land_prs:
  - "mctrader-hub#375 (6f19ec0, MERGED 2026-05-16T22:45:05Z) — Phase 1 단일 PR 10 file (9 deliverable+부수 + spec/plan)"
  - "mctrader-hub#TBD-post-merge — counters.json COMPLETED + Story §11 LAND timeline + RETRO §carry + plugin-codeforge#804/#805 consumer comment"
duration:
  start: "2026-05-17"
  end: "2026-05-17"
  hours: 6
---

# RETRO-MCT-190 — ADR-032 owner Story (VERIFIED Badge Evidence Triad 본문 author + §5 보강 + memory amendment)

> **Story**: MCT-190. **Epic**: cross-Epic governance (singleton).
> **Land window**: 2026-05-17 단일일 (brainstorm Phase 0+1+2 → spec/plan → 9 file author → 단일 PR LAND).
> **Classification**: doc-only-fast-path (phase1_only, code lane 부재).

## §1 Story summary + 5 결정점 채택 결과

### 1.1 Story 1줄 summary

MCT-190 = ADR-032 "VERIFIED Badge Evidence Triad" governance ADR owner Story. cross-Epic governance singleton, doc-only Story (phase1_only, classification: doc-only-fast-path). 단일 PR bundle LAND (sub-Story 분리 = self-reference 위반).

4 deliverable scope:
1. ADR-032 본문 author (`docs/adr/ADR-032-verified-badge-evidence-triad.md`, Status Proposed → Accepted)
2. §5 expected_sections 보강 (caller code spec FIX iter compliance + cross-Story PR scope guard)
3. PMO 메모리 amendment (`feedback_parallel_session_branch_race` hub-only → 6 repo tier 차등)
4. plugin-codeforge#804/#805 consumer 박제 (post-merge PMO-AUDIT-MCT-190 + comment)

### 1.2 5 결정점 (Codex 일괄 dispatch + Claude 합성)

| Q | 결정점 | Codex 권고 | Claude 채택 | 정합 |
|---|--------|-----------|------------|------|
| Q1 | ADR-032 §5 enforcement scope | B (self-discipline gate v1) | **B** | 정합 |
| Q2 | PMO 메모리 6 repo amendment 범위 | C (hub+data만) | **B** (tier 차등) | **deviation** |
| Q3 | evidence triad 4번째 게이트 (telemetry counter) | B (§7 future-work carry) | **B** | 정합 |
| Q4 | plugin-codeforge#804/#805 consumer 박제 형식 | B (PMO retro + comment) | **B** | 정합 |
| Q5 | Domain knowledge 신규 page 위치 | B (governance/ dir 신규) | **B** | 정합 |

**5/5 채택**. 4 Codex 정합 + 1 deviation (Q2). Q2 deviation 사유 = 사용자 prompt verbatim "6 repo 전수" + Researcher unknown #1 over-generalization 위험 균형 = tier 차등 (tier-1 의무 hub+data+engine / tier-2 권고 market 3 repo).

## §2 Lessons (4건)

### Lesson 1: ADR meta-circular self-reference 첫 실증 (worktree 격리 사전 차단 의도적 활용)

본 Story 가 ADR-032 §5.2 cross-Story PR scope guard rule 발의 + 본 Story 자체가 그 rule 의 첫 적용 사례 = meta-circular self-reference.

worktree `mct-190-adr-032-author` 격리 적용 = ADR-032 §5.2 self-discipline gate v1 의 첫 실증. Phase 0 verify lesson 8회째 사전 차단 (MCT-186 working tree contamination risk 회피, MCT-189 §Lessons.3 cross-Story PR contamination 재현 방지).

**Why**: ADR-032 evidence triad 의 caller-wired evidence 가 ADR-032 자체 publication 시점 "0건" — false-positive fail risk (R2). Caveat 명시 박제로 차단 (governance singleton, MCT-NNN reapply 시점부터 누적 시작).

**How to apply**: governance ADR 의 self-reference 박제 시 `caller_wired_caveat` 필드 의무 박제 — "self-reference Caveat: governance ADR singleton, MCT-NNN reapply 시점부터 누적".

### Lesson 2: doc-only Story fast-path 효율 (FIX 0회 + 단일 PR + 단순 9 file author)

doc-only Story = code lane + 통합테스트 + 보안테스트 BYPASS. design lane iter 0 (brainstorm Phase 0 4 agent burst 흡수). spec review iter1 PASS FIX 0회.

scope: 9 file author (ADR-032 본문 + RETRO-MCT-190 + PMO-AUDIT-MCT-190 + Story MCT-190.md + spec + plan + scope_manifest + Change Plan + memory amendment) + CLAUDE.md MCT-190 entry.

**Why**: codeforge `story-cutoff-classification` fast-path = code 변경 0 인 governance / RETRO / memory amendment Story 의 단순 운영. 통합테스트 SKIP + Code Review BYPASS + Security Test BYPASS 정합 (게이트 매트릭스 doc-only-fast-path row).

**How to apply**: phase_pair=phase1_only + classification=doc-only-fast-path 명시 + 단일 PR bundle + pr_completeness_checklist 10 pre-merge 박제 의무 (MCT-184 incomplete 박제 PR 패턴 재발 방지).

### Lesson 3: Codex 5 결정점 일괄 dispatch + Claude 합성 (Q-by-Q stop 회피)

memory `feedback_brainstorm_codex_review_pattern` 정합 = brainstorm session 의 모든 open design 결정점 Codex 일괄 dispatch (Q-by-Q 사용자 stop 금지). 본 Story = 5 결정점 (Q1-Q5) 1회 dispatch 로 일괄 권고 수신 + Claude 합성 → spec 작성 진입.

dispatch 효과 측정:
- decision-making elapsed: ~10분 (Codex round-trip 1회) vs Q-by-Q 예상 ~50분 (5 round-trip)
- Claude 가 합성 책임 (Sonnet decider 금지 정합) → spec §2 박제 즉시 가능
- deviation 1건 (Q2) 명시 박제 → 사용자 정정 channel 보존

**Why**: Q-by-Q 사용자 stop = decision fatigue + brainstorm session 시간 ↑. 일괄 dispatch = parallel speed + Claude 가 결정 합성 책임 + 사용자 검토 1회 (전체 5 결정점 한 번에 review).

**How to apply**: open 결정점 4+ 시 Codex 일괄 dispatch 의무 (단일 prompt 안 모든 Q + 옵션 + sources 박제). Sonnet decider 금지. Claude 합성 + deviation 명시 박제.

### Lesson 5: trust-but-verify 동형 1회 — implementer subagent 보고 부정확 (MCT-189 §3 패턴 #5 재현)

Task 1 implementer subagent 가 ADR-032 본문 작성 시 **worktree path 가 아닌 main repo path 에 file write 시도 + 결과 file 부재 + 그러나 success "DONE_WITH_CONCERNS" 보고** (203 lines + grep keywords 26 hits 보고). Orchestrator git status verify 로 file 부재 발견 → 직접 write 정정 (158 lines).

**Why**: subagent prompt 에 worktree path 명시했지만 path resolution gap (worktree internal CLAUDE.md 또는 file system layer 불명확). subagent 보고 = 의도된 작업 (intent) 이지만 실제 결과 (actual) 와 불일치.

**How to apply**:
- Orchestrator 가 critical artifact 의 file existence verify 의무 (git status + actual file Read)
- subagent prompt 에 "Write 후 자동 ls verify report 의무" 강제 instruction 추가 권고
- ADR-032 §5.1 caller code spec FIX iter compliance amendment 의 caller code = trust-but-verify reviewer baseline 직접 측정 패턴 동형 일반화 (PMO-AUDIT-MCT-189 §3 패턴 #5 cross-ref)

이번 case = MCT-190 self-reference 강화 — ADR-032 §3.1.3 PMO audit gate 의 효력 실증 (Orchestrator-level git status verify = self-discipline gate v1 의 3-tier 중 1-tier).

### Lesson 6: parallel session branch race 재현 (mctrader-hub main working tree mct-187-phase2-pr2-bagje switch)

본 session 진행 동안 parallel session 이 mctrader-hub main working tree 의 branch 를 `mct-186-phase2-pr2-hub` → `mct-187-phase2-pr2-bagje` 로 switch + MCT-187 Phase 1 (#374) + MCT-183 amendment 2건 (#372/#373) + MCT-186 PMO retro 모두 origin/main LAND.

**Why**: memory `feedback_parallel_session_branch_race` 가 정확히 다루는 영역의 본 session 진행 중 실시간 재현. tier-1 hub 영역 — 본 session 의 worktree 격리 (mct-190-adr-032-author + mct-190-post-merge) 가 사전 차단 효과 실증.

**How to apply**:
- 본 RETRO 자체가 amendment trigger 정합 (Q2=B tier 차등 정책 = hub tier-1 의무 격리)
- 본 lesson 박제 = memory amendment 의 첫 reapply evidence (caller-wired LAND, ADR-032 §3 evidence triad)
- MCT-191+ Story 진입 시 모든 tier-1 (hub+data+engine) repo 작업 시 worktree 격리 의무 적용 권고

### Lesson 4: Codex Q2 권고 deviation 박제 (사용자 prompt verbatim 우선)

Q2 = Codex 권고 (C) hub+data 만 ↔ Claude 채택 (B) 6 repo tier 차등. 사유 = 사용자 prompt verbatim "6 repo 전수 격리" 명시 + Researcher unknown #1 over-generalization 위험 균형.

tier 분류:
- **tier-1 의무**: hub + data + engine (parallel session 빈도 高, MCT-186 IN_PROGRESS 시 engine cutover 정합)
- **tier-2 권고**: market + market-bithumb + market-upbit (변경 빈도 低, vendor wheel 작업 시 parallel session 가능)
- **별 분류**: web + signal-collector (codeforge 자체 plugin 영역 아님)

**Why**: memory `feedback_autonomous_execution` "끝까지 진행해" mandate = 사용자 선호 + Codex 권고 균형 (사용자 정정 의무). Codex = senior architect 자문, Claude = 사용자 의도 합성 책임. Q2 deviation = 정상 calibration 신호 (full alignment = 의심).

**How to apply**: Codex 권고 deviation 시 RETRO 명시 박제 의무 (사용자 정정 의무 row). 5 결정점 중 1건 deviation = 정상 (full alignment 가 의심 — Codex 권고 무비판 채택 risk).

## §3 cross-Story patterns

### 3.1 MCT-184 / MCT-189 / MCT-190 = 3 sequential governance Story (cross-Epic)

| Story | 핵심 산출 | Story bundle 패턴 | 박제 정합 |
|-------|----------|----------------|----------|
| MCT-184 | data REST API 신규 + 박제 PR incomplete (≈58% carry) | 1 PR + 1 별 amendment PR (hub#359 → hub#360 28분) | incomplete (carry) |
| MCT-189 | ADR-029 §D3 wiring 완결 + cross-Story PR contamination 첫 박제 | 4 PR sequential (hub#357 + data#73 + data#75 + hub#363) | 정직 박제 (lessons 3건) |
| **MCT-190** | **ADR-032 본문 author + §5 보강 + memory amendment** | **1 PR bundle** (option A, sub-Story 분리 = self-reference 위반) | **self-reference Caveat 박제** |

→ governance Story 패턴 진화: MCT-184 (incomplete) → MCT-189 (cross-repo 4 PR sequential + 결함 정직 박제) → MCT-190 (1 PR bundle + self-reference Caveat + worktree 사전 차단). governance Story 운영 성숙도 누적 ↑↑.

### 3.2 ADR-032 evidence triad reapply 시점

MCT-191+ Story scope_manifest `verify_evidence` row 의무. MCT-190 LAND 후 첫 reapply Story = 본 ADR-032 의 caller-wired evidence 누적 시작 시점.

evidence triad v1 (3 evidence):
1. file:line — `docs/adr/ADR-032-*.md:NN` reference 박제
2. production caller grep ≥1 — `git grep ADR-032` consumer Story scope_manifest 박제
3. integration test PASS — caller Story 측 통합테스트 PASS evidence

self-reference Caveat (R2 mitigation): ADR-032 자체 publication 시점 caller-wired evidence "0건" 정상 — governance ADR singleton 특성, MCT-NNN reapply 시점부터 누적.

### 3.3 Phase 0 verify lesson 누적 (8회째 사전 차단)

| Story | lesson | 차단 방식 |
|-------|--------|----------|
| MCT-170 | engine reader 재구현 가설 정정 (확장+wiring) | Phase 0 verify (counters.json + scope_manifest 정정) |
| MCT-177 | engine daemon 신규 구현 가설 정정 (shutdown.py SSOT 재사용) | Phase 0 verify (RefactorAgent A 판정) |
| MCT-178~180 | cross-repo Phase 0 verify 독립 의무 누적 5회 재현 | spec amend |
| MCT-182 | CandleModel 5곳 가설 정정 (실측 4곳) | Phase 0 verify 정정 박제 |
| MCT-189 | promote_l1() caller 0건 발견 (decision-defined ≠ caller-wired) | ADR-032 trigger |
| **MCT-190** | **worktree 격리 사전 차단 (self-reference 첫 실증)** | **8회째 = 사전 차단 의도적 활용** |

## §4 carry over (3건)

1. **MCT-191 reservation 권고** — ADR-032 §7 future-work 3건 중 1건 owner Story:
   - (a) Evidence triad 4번째 게이트 (telemetry counter, ADR-032 §7 future-work)
   - (b) CI mechanical gate (plugin-codeforge#804/#805 LAND 후 consumer 적용 — schema 검증 자동화)
   - (c) `docs/domain-knowledge/process/cross-story-pr-contamination.md` 신규 (MCT-189 §Lessons.3 패턴 일반화)

2. **post-merge step P1-P5** (PR #375 LAND 후 본 post-merge cleanup PR 박제 의무):
   - P1: ✓ `.codeforge/counters.json` MCT-190 IN_PROGRESS → COMPLETED + completed_at + land_prs 박제 (Phase 1 PR f9d6d4d 의 part) + ADR-032 Proposed → Accepted 전환 (이미 LAND)
   - P2: ☐ plugin-codeforge#804 consumer comment 추가 (ADR-032 §3.1 self-discipline gate v1 + §5.2 cross-Story PR scope guard evidence row + CI mechanical gate consumer 적용 carry §7.2)
   - P3: ☐ plugin-codeforge#805 consumer comment 추가 (ADR-032 §2 trigger 3 사례 + PMO-AUDIT-MCT-190 §3 자매 consumer 박제 evidence row + post-merge audit lane consumer 적용 carry §7.2)
   - P4: ☐ PR #375 `gate:retro-complete` label add (CFP-138 / ADR-045 forcing function 정합)
   - P5: ☐ PMOAgent retro final dispatch (memory `feedback_pmo_retro_mandatory` 정합 — Story fix/ADR 작성/Story 생성 후 세션 종료 전 PMOAgent 자동 dispatch + 본 RETRO §Lessons.5+§Lessons.6 lesson 추가 박제)

3. **MCT-186 IN_PROGRESS 복귀** — worktree exit 후 mctrader-hub working dir branch `mct-186-phase2-pr2-hub` Phase 2 PR2 박제 작업 continuation. MCT-186 §10/§11/§12 작성 + ADR-031 §D4 amendment + scope_manifest 5/7 + RETRO-MCT-186 + EPIC-RESULTS §Story-5.

## §5 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | 전수 PASS (3 BYPASS + 1 SKIP + 3 PASS, doc-only fast-path 정합) |
| FIX 루프 | 0회 (design lane iter 0, code lane 부재) |
| 9 file author | ALL LAND (ADR-032 본문 + RETRO + PMO-AUDIT + Story + spec + plan + scope_manifest + Change Plan + memory amendment + CLAUDE.md entry) |
| ADR-032 status | Proposed → Accepted |
| 5 결정점 | Q1=B / Q2=B / Q3=B / Q4=B / Q5=B (4 Codex 정합 + 1 deviation) |
| self-reference Caveat | 박제 완결 (R2 mitigation, governance ADR singleton 특성 명시) |
| MCT-186 contamination | RESOLVED (worktree 격리 사전 차단, Phase 0 verify lesson 8회째) |
| upstream consumer | plugin-codeforge#804 + #805 comment evidence row 추가 (post-merge P2) |
| Codex deviation 박제 | Q2 deviation 명시 (사용자 정정 channel 보존) |

**Story 진화 정합**: MCT-184 incomplete → MCT-189 4 PR sequential + cross-Story PR contamination 정직 박제 → MCT-190 1 PR bundle + self-reference Caveat + worktree 사전 차단 (governance Story 운영 ↑↑).

## Key References

- Story: `docs/stories/MCT-190.md`
- spec: `docs/superpowers/specs/2026-05-17-MCT-190-adr-032-author-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mct-190-adr-032-author.md`
- ADR-032 본문: `docs/adr/ADR-032-verified-badge-evidence-triad.md` (Status Accepted, MCT-190 LAND)
- PMO audit: `docs/retros/PMO-AUDIT-MCT-190.md` (plugin-codeforge#804/#805 consumer 박제)
- Change Plan: N/A (doc-only Story, codeforge:story-cutoff-classification fast-path)
- scope_manifest: `scope_manifests/MCT-190.yaml` (156 lines, YAML lint PASS)
- memory amendment: `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\feedback_parallel_session_branch_race.md` (hub-only → 6 repo tier 차등, MEMORY.md index sync)
- domain-knowledge: `docs/domain-knowledge/domain/governance/evidence-triad-verified-badge.md` (Q5=B 신규 생성, governance/ dir 동시 신규)
- 선례 RETRO: `docs/retros/RETRO-MCT-189.md` (Orchestrator self-write SSOT, lesson 3건 + carry over 4건)
- upstream: plugin-codeforge#804 + plugin-codeforge#805 (priority:high, MCT-189 evidence comment LAND, MCT-190 consumer comment 추가 post-merge)
- LAND: hub#375 (6f19ec0, MERGED 2026-05-16T22:45:05Z) + post-merge cleanup PR (counters COMPLETED + Story §11 + RETRO §carry)
