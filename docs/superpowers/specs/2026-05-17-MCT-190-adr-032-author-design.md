---
type: brainstorm-spec
story_key: MCT-190
title: "ADR-032 owner Story — VERIFIED badge evidence triad 본문 author + §5 expected_sections 보강 + PMO 메모리 amendment (6 repo tier 차등 격리) + 자매 plugin-codeforge#804/#805 consumer 박제"
epic: cross-Epic governance
parent_audit: PMO-AUDIT-MCT-189 §4.2
repo: mctrader-hub
phase_pair: phase1_only
classification: doc-only-fast-path
status: IN_PROGRESS
owner_for_adr: ADR-032
adr_status_transition: "Proposed → Accepted"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-190-adr-032-author"
worktree_branch: worktree-mct-190-adr-032-author
self_reference_evidence: "ADR-032 §5 self-reference 첫 실증 — 본 Story 가 worktree 격리 적용 (Phase 0 verify lesson 8회째 사전 차단)"
created_at: "2026-05-17"
author: Orchestrator (codeforge:brainstorm Phase 1 산출)
phase_0_agents:
  - DomainAgent (a250e6160bd753902)
  - ResearcherAgent (a8c98a1109fa94137)
  - RequirementsAnalystAgent (a51a6256a2e8534d7)
  - PMOAgent_phase0 (a5bd70abaab3e47b7)
  - PMOAgent_phase2_scope_manifest (a27b9e2a0eb0431e0)
codex_dispatch: 5_decision_points_burst (Q1-Q5)
verified_sources:
  - ".codeforge/counters.json:327-347 (MCT-190 RESERVED + ADR-032 Proposed entry)"
  - "docs/retros/PMO-AUDIT-MCT-189.md:299-326 (§4.2 MCT-190 reservation 발의 + 4 deliverable scope)"
  - "C:\\Users\\mccho\\.claude\\projects\\c--workspace-mclayer-mctrader-hub\\memory\\feedback_parallel_session_branch_race.md (full file, 8 days old, single hub working dir 박제)"
  - "git ls-files docs/adr/ADR-032-*.md = 0 lines (본문 부재 confirm)"
  - "Bash ls docs/domain-knowledge/domain/ = data-health/parquet-streaming/tier-promotion (governance/ 부재 confirm)"
  - "Glob docs/retros/PMO-AUDIT-*.md = MCT-189 까지만 (PMO-AUDIT-MCT-190.md 부재 confirm)"
  - "plugin-codeforge#804 OPEN (priority:high, MCT-189 evidence comment LAND 4467327837)"
  - "plugin-codeforge#805 OPEN (priority:high, MCT-189 P0×4 누적 evidence comment LAND 4467328716)"
---

# MCT-190 — ADR-032 owner Story brainstorm spec

> `codeforge:brainstorm` Phase 0 + Phase 1 산출. Phase 2 PMOAgent scope_manifest YAML = §6 박제.
> 다음 lane = `superpowers:writing-plans` → ArchitectPLAgent (5 deliverable + 4 부수 file author).

## §1 Trigger — 사용자 요구사항 + Phase 0 verified facts

### 1.1 사용자 prompt verbatim

> "MCT-190 진입해" — ADR-032 owner Story 4 deliverable 자율 실행 mandate:
> (1) ADR-032 본문 author (`docs/adr/ADR-032-verified-badge-evidence-triad.md`, Status Proposed → Accepted, evidence triad = file:line + production caller grep ≥1 + integration test PASS)
> (2) §5 보강 — caller code 의 spec FIX iter compliance + cross-Story PR scope guard
> (3) PMO 메모리 amendment — `feedback_parallel_session_branch_race` 를 hub 한정 → 6 repo 전수 격리 일반화
> (4) 자매 plugin-codeforge#804/#805 consumer 측 박제

### 1.2 Phase 0 verified facts (사용자 prompt 가설 검증)

| 사실 | verified-via | 결과 |
|------|-------------|------|
| MCT-190 RESERVED at counters.json | Read `.codeforge/counters.json:338-347` | ✓ (RESERVED, 4 deliverable rationale 박제) |
| ADR-032 Proposed at counters.json | Read `.codeforge/counters.json:327-336` | ✓ (Proposed, expected_sections §1-§5 박제) |
| ADR-032 본문 file 부재 | Bash `git ls-files docs/adr/ADR-032-*.md` | ✓ (0 lines, 본문 author 미완 confirm) |
| `docs/domain-knowledge/domain/governance/` dir 부재 | Bash `ls docs/domain-knowledge/domain/` | ✓ (data-health/parquet-streaming/tier-promotion 만, governance/ 신규 생성 의무) |
| PMO-AUDIT-MCT-190.md 부재 | Glob `docs/retros/PMO-AUDIT-*.md` | ✓ (MCT-189 까지만, 190 author 의무) |
| `feedback_parallel_session_branch_race.md` = single hub working dir 박제 | Read memory file (8 days old) | ✓ (6 repo 일반화 미반영, rewrite 의무) |
| plugin-codeforge#804 OPEN + MCT-189 evidence comment LAND | `gh issue view 804 --repo mclayer/plugin-codeforge` | ✓ (priority:high, comment 4467327837 LAND 2026-05-16) |
| plugin-codeforge#805 OPEN + MCT-189 P0×4 evidence LAND | `gh issue view 805 --repo mclayer/plugin-codeforge` | ✓ (priority:high, comment 4467328716 LAND 2026-05-16) |
| 현 hub branch = mct-186-phase2-pr2-hub (MCT-186 IN_PROGRESS) | git status + log | ✓ (Phase 1 commit 3fc9c1f + MCT-186.md uncommitted M) |
| worktree 격리 적용 | `EnterWorktree mct-190-adr-032-author` | ✓ (base=origin/main fresh, ADR-032 §5 self-reference 첫 실증) |

### 1.3 핵심 trigger context (Phase 0 4 agent burst 합성)

- **MCT-189 LAND (2026-05-17) 시 ADR-032 사실상 Accepted 후보 충족**: §8.5 Impl Manifest = evidence triad 3종 evidence 첫 적용 (file:line `promote_l1` promotion.py:95-180 + caller grep 3+ DualWriter/runner + 13 integration test PASS).
- **MCT-189 진행 중 cross-Story PR contamination 발견**: mctrader-data 측 `45e501c feat(MCT-184)` commit 이 partial MCT-189 commit 포함 → spec FIX iter1-3 부재 결함 main 일시 도달 → `git rebase --strategy-option=theirs` 복구. ADR-032 §5 self-reference trigger.
- **Phase 0 verify lesson 7회째 → 8회째 사전 차단**: 본 Story = worktree 격리로 사전 차단 의도적 활용 (PMOAgent 2nd pass 권고).

## §2 핵심 결정 (Codex 5 결정점 일괄 dispatch + Claude 합성)

### 2.1 결정점 채택 summary

| Q | 결정점 | Codex 권고 | **Claude 채택** | 사유 |
|---|--------|-----------|---------------|------|
| Q1 | ADR-032 §5 enforcement scope | (B) self-discipline gate | **(B)** | CI gate = #804 의존, phase1_only 정합. 3-tier (scope_manifest verify_evidence schema + Story §11 + PMO audit) 충분 |
| Q2 | PMO 메모리 6 repo amendment 범위 | (C) hub+data만 | **(B) 차등 정책** | 사용자 prompt "6 repo 전수" + Researcher unknown #1 균형 = tier-1 hub+data+engine 의무 / tier-2 market+market-bithumb+market-upbit 권고 |
| Q3 | evidence triad 4번째 게이트 (telemetry counter) | (B) §7 future-work carry | **(B)** | triad v1 = 3 evidence 유지, quad 확장 = 별 Story (MCT-NNN) |
| Q4 | plugin-codeforge#804/#805 consumer 박제 형식 | (B) PMO-AUDIT-MCT-190 별 retro + comment | **(B)** | memory `feedback_pmo_retro_mandatory` 정합 |
| Q5 | Domain knowledge 신규 page 위치 | (B) governance/ dir 신규 | **(B)** | ADR=결정 / domain-knowledge=재사용 지식 분리. process/cross-story-* = 별 Story carry |

### 2.2 Q2 채택 차이 사유 (Codex (C) vs Claude (B))

Codex 권고 (C) = "실측 race 발생 repo hub+data 만, 6 repo 전수는 over-generalization".
Claude 채택 (B) = "tier 차등 (tier-1 의무 hub+data+engine / tier-2 권고 market 3 repo)".

**사유**:
- 사용자 prompt verbatim "6 repo 전수 격리" 명시 정합 (autonomous_execution memory: 사용자 정정 의무)
- engine = MCT-186 IN_PROGRESS (engine realtime cutover Story) 의 parallel session contamination risk 高 (data 와 동등 수준)
- market+market-bithumb+market-upbit = 변경 빈도 低 but vendor wheel 작업 시 parallel session 가능 → 권고 (의무 아님)
- web/signal-collector = 별 분류 명시 (codeforge 자체 plugin 영역 아님)

→ 사용자가 (C) 또는 (A) 선호 시 정정 의무 (Q1-Q5 중 유일 Codex 권고 deviation).

### 2.3 5 결정점이 ADR-032 본문에 미치는 영향

| ADR-032 section | 영향 결정점 | 박제 내용 |
|-----------------|----------|----------|
| §0 frontmatter | (전체) | Status: Proposed → Accepted. owner_story: MCT-190. first_application: MCT-189 §8.5 |
| §1 Trigger (3 사례) | (전체) | MCT-169 D3=C 130GB / MCT-179 ADR-030 reconcile 5회 / MCT-184 박제 PR incomplete (≈58%) |
| §2 Evidence Triad Rule v1 | Q3 (triad 유지) | (1) file:line / (2) caller grep ≥1 / (3) integration test PASS. decision-defined ≠ caller-wired 분리 |
| §3 Enforcement Layer (3-tier) | Q1 (self-discipline) | scope_manifest verify_evidence schema + Story §11 박제 + PMO audit gate |
| §4 Story §8.5 Impl Manifest 통합 | (전체) | §8.5 = evidence triad 3종 동시 박제 template |
| §5 expected_sections amendments | Q1 + cross-Story PR contamination | (5.1) caller code spec FIX iter compliance + (5.2) cross-Story PR scope guard |
| §6 cross-ref | Q4 (#804/#805) | 자매 plugin-codeforge#804+#805 + MCT-189 §9 |
| §7 future-work / Out of scope | Q3 + Q5 process/ | (7.1) triad → quad (telemetry counter) / (7.2) CI mechanical gate (#804 carry) / (7.3) process/cross-story-pr-contamination.md |

## §3 Phase 0 agent 산출 합성 (verbatim 압축)

### 3.1 DomainAgent

- domain-knowledge governance/ + process/ dir 부재. grace-0-local-delete.md 1 file 만 evidence triad 박제 (decision-defined ≠ caller-wired 분리 박제 완료, ADR-032 cross-ref + MCT-190 권고 명시).
- 신규 후보 = `domain/governance/evidence-triad-verified-badge.md` (Q5=B 채택 정합). 조건부 = `process/cross-story-pr-contamination.md` (별 Story carry).

### 3.2 ResearcherAgent

- 핵심 개념 3: (1) decision-defined ≠ caller-wired (Michael Nygard ADR "Accepted ≠ Implemented"). (2) evidence triad as mechanical forcing function (Ford/Parsons/Kua "Building Evolutionary Architectures" fitness function). (3) ADR meta-circular self-reference (ADR-032 자체가 ADR-032 evidence triad 적용 의무).
- Unknown #1: 6 repo 전수 격리 over-generalization 위험 (Q2 채택 (B) 차등 정책 결정 input).
- Unknown #2: triad false-negative blind spot (dead-in-prod caller test-only/deprecated triad PASS but production wiring 0) → 4번째 게이트 (runtime telemetry counter ≥1 over N days) 필요성 (Q3 (B) §7 carry 결정 input).

### 3.3 RequirementsAnalystAgent

- WHY = "MCT-189 LAND 시 ADR-032 사실상 Accepted 후보 충족 but 본문 미완 + cross-Story PR contamination 일반화 의무"
- 5 AC (§4 박제). Edge-1: MCT-191+ 진입 시 §5 amendment box / Edge-2: upstream 거부 시 mctrader-hub 자체 governance 강화

### 3.4 PMOAgent (Phase 0 + Phase 2)

- 1 Story bundle (옵션 A) 채택, sub-Story 분리 = ADR-032 self-reference 첫 violation
- 의존 Epic 없음 (cross-Epic governance singleton)
- 위험: MCT-186 working tree contamination → worktree 격리 사전 차단 (ADR-032 §5 self-reference 첫 실증 의도적 활용)
- Phase 2 scope_manifest YAML = §6 박제

## §4 AC (5종, RequirementsAnalystAgent 도출)

- **AC-1 ADR-032 본문 완성도**: ADR-032.md file 존재 + (1) trigger 3 사례 분석 + (2) evidence triad rule + (3) enforcement layer 3-tier 박제 + PMOAgent reader verify ✅
- **AC-2 cross-Story 오염 방지 시스템**: MCT-190 LAND 후 신규 cross-repo Story 진입 시 PR squash commit cross-Story scope mismatch 발견 시 Orchestrator pre-merge git-diff check + PMO 메모리 escalation (self-discipline v1)
- **AC-3 6-repo 메모리 amendment 일관성**: 6 repo (hub + data + engine + market + market-bithumb + market-upbit) tier-1/tier-2 차등 정책 명시 + web/signal-collector 별 분류 명시
- **AC-4 plugin-codeforge #804/#805 consumer 박제**: MCT-190 LAND 후 #804/#805 comment evidence row 추가 + PMO-AUDIT-MCT-190.md §3 자매 consumer 박제 LAND
- **AC-5 POLICY_FINALIZED ↔ ACCEPTED transition**: ADR-032.md frontmatter status = "Accepted" + counters.json status 동기 (finalized_by_story 미기재 — POLICY_FINALIZED 는 Epic 완결 후 별 PR, ADR-032 는 singleton 이라 future Story 들이 reapply 시점부터 누적)

## §5 INV (3종)

- **INV-1**: ADR-032 본문 = self-reference Caveat 박제 의무 (`caller_grep` evidence "MCT-190 LAND 시점 0건, MCT-191+ reapply 시점부터 누적" 명시 — false-positive fail 차단)
- **INV-2**: doc-only Story = 코드 변경 0 (production runtime untouched, INV preserve)
- **INV-3**: phase_pair=phase1_only = 단일 PR 완결 의무 (MCT-184 hub#359 → hub#360 28분 amendment 동형 차단)

## §6 scope_manifest (PMOAgent 2nd pass 산출, YAML 전체)

본 spec 의 §6 = `scope_manifests/MCT-190.yaml` SSOT 직접 입력. ArchitectPLAgent 가 실 plan 작성 시 본 YAML 인용 → planned_files 9건 + design_decisions 5건 + risks 4건 + pr_completeness_checklist 10건 전수 carry.

(PMOAgent 산출 YAML = §6 박제 — Phase 2 산출 SSOT, ArchitectPL 실행 input)

```yaml
story_key: MCT-190
title: "ADR-032 owner Story — VERIFIED badge evidence triad 본문 author + §5 expected_sections 보강 + PMO 메모리 amendment (6 repo 차등 격리) + 자매 plugin-codeforge#804/#805 consumer 박제"
epic: cross-Epic governance
parent_audit: PMO-AUDIT-MCT-189 §4.2
repo: mctrader-hub
phase_pair: phase1_only
classification: doc-only-fast-path
status: IN_PROGRESS
land_order: single-pr
owner_for_adr: ADR-032
adr_status_transition: "Proposed → Accepted"
first_application_evidence: "MCT-189 §8.5 Impl Manifest (hub#363 ccacdce 2026-05-17)"

design_decisions:
  - {id: Q1, chosen: B, title: "ADR-032 §5 enforcement scope = self-discipline gate v1"}
  - {id: Q2, chosen: B, title: "PMO 메모리 6 repo amendment = tier 차등 (hub+data+engine 의무 / market+market-bithumb+market-upbit 권고)"}
  - {id: Q3, chosen: B, title: "evidence triad 4번째 게이트 = §7 future-work carry"}
  - {id: Q4, chosen: B, title: "plugin-codeforge#804/#805 consumer 박제 = PMO-AUDIT-MCT-190 별 retro + comment"}
  - {id: Q5, chosen: B, title: "Domain knowledge governance/ dir 신규 생성"}

planned_files:
  - {path: "docs/adr/ADR-032-verified-badge-evidence-triad.md", action: create, lines: "300-400"}
  - {path: "docs/domain-knowledge/domain/governance/evidence-triad-verified-badge.md", action: create, lines: "100-150"}
  - {path: "docs/retros/PMO-AUDIT-MCT-190.md", action: create, lines: "200-300"}
  - {path: "docs/retros/RETRO-MCT-190.md", action: create, lines: "150-250"}
  - {path: "docs/stories/MCT-190.md", action: create, lines: "250-350"}
  - {path: "scope_manifests/MCT-190.yaml", action: create, lines: "100-150"}
  - {path: "memory feedback_parallel_session_branch_race.md", action: modify, lines: "30-50"}
  - {path: "memory MEMORY.md", action: modify, lines: "1-2"}
  - {path: "CLAUDE.md", action: modify, lines: "30-50"}
  - {path: ".codeforge/counters.json", action: modify, lines: "5-10"}

planned_adrs:
  - {adr_key: ADR-032, action: author, status_transition: "Proposed → Accepted", expected_sections_count: 8}

planned_claude_md_sections:
  - {section_name: "MCT-190 COMPLETED (2026-05-17)", insertion_point: "after §MCT-189 COMPLETED"}

planned_upstream_consumer_comments:
  - {upstream: plugin-codeforge#804, evidence: "ADR-032 §3 self-discipline gate v1 + §5.2 cross-Story PR scope guard 박제. CI mechanical gate consumer 적용 carry"}
  - {upstream: plugin-codeforge#805, evidence: "ADR-032 §1 trigger 3 사례 + PMO-AUDIT-MCT-190 §3 자매 consumer 박제. post-merge audit lane consumer 적용 carry"}

verify_evidence:
  - rule: "Evidence Triad Rule v1 정의 박제 (self-reference 첫 적용)"
    decision_defined_evidence: "docs/adr/ADR-032-verified-badge-evidence-triad.md §2"
    caller_wired_evidence_caveat: "MCT-190 LAND 시점 0건 (governance ADR, MCT-191+ reapply 시점부터 누적)"
    integration_test: "N/A (governance ADR, code wiring 0)"
    forcing_function:
      - "Story §8.5 Impl Manifest 체크리스트 PR description 박제 (MCT-184 incomplete 사전 차단)"
      - "PMO-AUDIT-MCT-190 §lane gate 전수 검증"

risks:
  - {id: R1, severity: MEDIUM, description: "MCT-184 박제 PR incomplete 패턴 재현 (≈58% carry)", mitigation: "Story §8.5 Impl Manifest 10 file 체크리스트 PR description 박제 의무"}
  - {id: R2, severity: LOW, description: "ADR-032 self-reference Caveat 누락 → false-positive fail risk", mitigation: "verify_evidence.caller_wired_evidence_caveat 명시"}
  - {id: R3, severity: LOW, description: "§5.2 CI mechanical gate 부재 (self-discipline gate v1)", mitigation: "ADR-032 §7 future-work carry, 3-tier enforcement 충분"}
  - {id: R4, severity: RESOLVED, description: "MCT-186 working tree contamination", mitigation: "worktree mct-190-adr-032-author 격리 완료"}

pr_completeness_checklist:
  pre_merge:
    - "ADR-032 본문 file 신규 (8/8 expected_sections)"
    - "governance dir + first entry 신규"
    - "PMO-AUDIT-MCT-190.md 신규"
    - "RETRO-MCT-190.md 신규"
    - "Story file §1-§11 전수"
    - "scope_manifest MCT-190.yaml"
    - "memory rewrite + MEMORY.md sync"
    - "CLAUDE.md §MCT-190 COMPLETED append"
    - "counters.json MCT-190 IN_PROGRESS + ADR-032 Accepted 전환"
    - "plugin-codeforge#804/#805 consumer comment 추가"
  post_merge:
    - "counters.json MCT-190 IN_PROGRESS → COMPLETED 전환"
    - "Story §11 LAND timeline 실 commit sha + PR number 박제"
    - "gate:retro-complete label add (CFP-138 / ADR-045)"

next_story_recommendation: "MCT-191 = ADR-032 §7 future-work 1건 owner (triad → quad telemetry counter or CI mechanical gate consumer or process/cross-story-pr-contamination.md governance entry)"
```

## §7 ADR-032 본문 expected_sections 골격 (ArchitectPL 실 author input)

```markdown
# ADR-032 — VERIFIED Badge Evidence Triad

## Status

Accepted (2026-05-17, MCT-190 LAND 시 Proposed → Accepted transition)

## Context

(§1 Trigger — 3 사례 분석)

## Decision

(§2 Evidence Triad Rule v1)
- (1) file:line
- (2) production caller `git grep` ≥ 1
- (3) integration test PASS

(§3 Enforcement Layer)
- (3.1) scope_manifest verify_evidence schema
- (3.2) Story §11 LAND timeline 박제
- (3.3) PMO audit gate

(§4 Story §8.5 Impl Manifest 통합)

(§5 Amendments)
- (5.1) caller code spec FIX iter compliance
- (5.2) cross-Story PR scope guard

## Consequences

(§6 cross-ref)
- plugin-codeforge#804/#805
- MCT-189 §9 self-reference

## Future Work

(§7 carry over)
- (7.1) Evidence triad 4번째 게이트 (telemetry counter ≥1 over N days)
- (7.2) CI mechanical gate (plugin-codeforge#804/#805 consumer)
- (7.3) docs/domain-knowledge/process/cross-story-pr-contamination.md 신규
```

## §8 다음 lane = superpowers:writing-plans

본 spec 산출물 = brainstorm Phase 1+2 종료. 다음 step:

1. **superpowers:writing-plans 호출** → plan file 작성 (`docs/superpowers/plans/2026-05-17-mct-190-adr-032-author.md`)
2. **ArchitectPLAgent dispatch** (5 deliverable + 4 부수 = 9 file author 분담)
3. **Phase 1 PR open + admin merge**
4. **PMO retro 자동 dispatch** (memory `feedback_pmo_retro_mandatory` 정합)

worktree = `c:\workspace\mclayer\mctrader-hub\.claude\worktrees\mct-190-adr-032-author` 유지 (Phase 1 PR LAND 후 keep, MCT-186 hub 본 working tree 분리 보존).
