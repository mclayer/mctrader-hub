---
type: brainstorm-spec
story_key: MCT-191
epic_key: EPIC-evidence-quad-runtime-telemetry
title: "Evidence quad governance amendment (doc-only) — ADR-032 §8/§9 본문 격상 + ADR-033 신규 + class taxonomy"
epic_title: "Evidence Quad — runtime telemetry counter 4번째 게이트 (triad v1 → quad v2, Hyrum's Law 역방향 dead-in-prod false-negative 차단)"
repo: mctrader-hub
phase_pair: phase1_only
classification: doc-only-fast-path
sequential_phase: 1
status: IN_PROGRESS
parent_dependency: "ADR-032 §8.1 future-work (MCT-190 LAND 2026-05-17, hub#375 6f19ec0)"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-191-evidence-quad"
worktree_branch: worktree-mct-191-evidence-quad
created_at: "2026-05-17"
author: Orchestrator (codeforge:brainstorm Phase 1 산출)
phase_0_agents:
  - DomainAgent (a2e1548db25749353)
  - ResearcherAgent (ae43c1e5682799549)
  - RequirementsAnalystAgent (a862aa2fe6e93f785)
  - PMOAgent_phase0 (a1cec630581efc76f)
  - PMOAgent_phase2 (ab6681ddf60f513cf)
codex_dispatch: 10_decision_points_burst (Q1-Q10)
verified_sources:
  - "docs/adr/ADR-032-verified-badge-evidence-triad.md:196-200 (§8.1 quad future-work 이미 명시 — F-0a)"
  - "docs/adr/ADR-032-verified-badge-evidence-triad.md:212-227 (§9 Self-reference Caveat + INV-1 이미 보유 — R1 선제 완화)"
  - "docs/adr/ADR-032-verified-badge-evidence-triad.md:65-95 (§3 Triad Rule v1 SSOT)"
  - "ADR-029.md:1-9 / ADR-030.md:1 / ADR-031.md:1 / ADR-032.md:1-17 (frontmatter 3 스타일 비동질 — F-0b additive only invariant)"
  - "docs/domain-knowledge/domain/governance/evidence-triad-verified-badge.md (117 lines 존재 — F-0d sibling, DomainAgent 공백 가설 정정)"
  - ".codeforge/counters.json:6 (mctrader-hub.next=191) + ADR-033 reservation 부재 (F-0e)"
---

# MCT-191 — Evidence quad governance amendment brainstorm spec

> `codeforge:brainstorm` Phase 0+1+2 산출. EPIC-evidence-quad-runtime-telemetry sub-1 (doc-only).
> 다음 lane = `superpowers:writing-plans` → implementer dispatch (10 file author).

## §1 Trigger — ADR-032 §8.1 future-work owner

### 1.1 사용자 요구사항

> "다음 스토리 수행하라" + AskUserQuestion 채택 = MCT-191 (a) Evidence triad 4번째 게이트 telemetry counter (Recommended) + Story 분해 small Epic 3 sub-Story (PMO+Codex 권고).

### 1.2 Phase 0 verified facts (가설 정정 — F-0a~F-0e)

| # | session prompt 가설 | 실측 (verified-via) | 정정 |
|---|---|---|---|
| F-0a | "ADR-032 §8/§9 신규 보강" | §8.1 이미 quad 4th gate future-work 명시 (`ADR-032.md:196-200`) + §9 이미 Self-reference Caveat + INV-1 보유 (`ADR-032.md:212-227`) | quad = **future-work 본문 격상** (신규 발명 아님) → R1 HIGH **선제 완화** |
| F-0b | "4 ADR frontmatter class 추가" | 3 스타일 비동질 — ADR-029 `adr_id`+`category:data` / ADR-030·031 frontmatter 부재 / ADR-032 `adr_key`+`status` | **additive only** invariant (정규화 금지, SSOT drift 8회째 차단) |
| F-0c | "ADR-032 227 lines" | 총 228 lines, §8.1 = line 196-200 | quad owner Story = §8.1 "별 Story MCT-NNN" → 본 Epic 구체화 |
| F-0d | "governance/ dir 공백" | `evidence-triad-verified-badge.md` 이미 존재 (117 lines) | quad 페이지 = **sibling** (공백 아님), triad 페이지 cross-ref 의무 (R4 DRY) |
| F-0e | counters.json next | `counters.json:6` next=191 + ADR-033 reservation 부재 | MCT-191 + ADR-033 신규 reservation 가능 |

**F-0a 가 본 spec 최대 가치**: quad 확장 = ADR-032 기존 §8.1/§9 구조와 이미 정합 → cross-document drift risk 대폭 ↓. PMO Phase 0 주요 위험 (§9 Self-reference Caveat quad 호환성 미검증) = F-0a 로 선제 완화 (§9 이미 `caller_wired_caveat` + INV-1 forcing function 보유, quad Caveat = telemetry 축 확장).

## §2 핵심 결정 (Codex 10 결정점 일괄 dispatch + Claude 합성)

| Q | 결정점 | Codex | **Claude 채택** | owner |
|---|--------|-------|---------------|-------|
| Q1 | Story 분해 | C | **C (사용자 confirm)** small Epic 3 sub-Story | epic-level |
| Q2 | ADR carrier | C | **C** hybrid (ADR-032 §8.1→본문 격상 + §9 Caveat 확장 + 신규 ADR-033 enforcement) | MCT-191 |
| Q3 | grandfathering scope | C | **C** production-wired ADR만 quad 의무 + governance ADR triad v1+Caveat | MCT-191 |
| Q4 | N days window | C | **C** traffic class 차등 (production-wired=14d / governance=N/A Caveat / trading-hot=market-open rolling) | MCT-191 rule + MCT-193 운영 |
| Q5 | quad vs triad×2 | C | **C** quad 4 evidence flat + counter-emit path triad v1 reapply (meta-recursion 1단 한정, MCT-179 §D8 가공 metric risk 차단) | MCT-191 rule + MCT-192 적용 |
| Q6 | governance/production 분류 | B | **B** ADR frontmatter `class: governance\|production\|mixed` taxonomy | ADR-033 §3 + MCT-191 4 ADR reapply |
| Q7 | enforcement timing | C | **C** Prometheus alert (counter==0 over Nd → critical + GitHub issue) + monthly PMO audit batch | MCT-193 |
| Q8 | counter family SSOT | C | **C** per-ADR scope_manifest `verify_evidence.telemetry_counter` field | MCT-191 schema + MCT-192 적용 |
| Q9 | domain knowledge | A | **A** `governance/evidence-quad-runtime-telemetry.md` 신규 (triad 페이지 §5 sibling cross-ref) | MCT-191 |
| Q10 | market-closed window | C | **C** traffic class 차등 (collector tick=market-open rolling / engine cold reader=14d calendar / governance=N/A Caveat) | MCT-191 rule + MCT-193 운영 |

## §3 Phase 0 agent 산출 합성

### 3.1 DomainAgent
governance/evidence-triad-verified-badge.md 117 lines 존재 (F-0d sibling). Hyrum's Law 역방향 + quad 어휘 박제 0 → 신규 페이지 carrier. 14d rolling + `nas_reader_ambiguity_total` 모델 박제.

### 3.2 ResearcherAgent
3 concept: (1) Hyrum's Law 역방향 (telemetry 0 over Nd → production 의존자 부재 추정). (2) runtime fitness function (Ford/Parsons/Kua — triad=static / quad 4th=runtime). (3) Counter monotonicity wiring proof (Prometheus Counter ≠ Gauge, monotonic = irrefutable). **2 unknowns**: U1 counter-emit dead-in-prod (quad=triad×2 가능, Q5=C 채택으로 처리) / U2 14d + market-closed false-negative (Q4+Q10=C traffic class 차등 채택으로 처리).

### 3.3 RequirementsAnalystAgent
WHY = MCT-189 130GB + Hyrum's Law 역방향. 일치. 5 AC + 2 Edge:
- AC-1 quad v2 rule 정의 / AC-2 enforcement timing 별 N-day gate / AC-3 governance vs production Caveat 분류 / AC-4 counter family SSOT / AC-5 기존 ADR amendment
- Edge-1 test-only caller ≥1 but production 0 (Q5=C) / Edge-2 governance ADR dual self-reference Caveat (ADR-032 §9 단순 참조, 중첩 회피)

### 3.4 PMOAgent
Epic = evidence-quad-runtime-telemetry, 3 sub-Story sequential (SSOT chain 의존, 병렬 불가). ADR-032=quad rule SSOT / ADR-033=enforcement layer SSOT. R1 HIGH (F-0a 선제 완화).

## §4 AC (RequirementsAnalystAgent 5 + PMO 정합)

- **AC-1**: Evidence quad v2 rule 정의 — ADR-032 §3.2(quad) + ADR-033 §2 본문 박제. `(file:line + caller_grep ≥1 + integration_test PASS) AND (telemetry_counter ≥1 over N days)`. governance ADR 제외 (Caveat).
- **AC-2**: enforcement timing = 별 N-day gate 명시 (Story LAND triad v1 의무 + post-LAND telemetry verify = MCT-193 owner). ADR-033 §6 박제.
- **AC-3**: Governance vs Production ADR 분류 체계화 — ADR frontmatter `class: governance|production|mixed` taxonomy (ADR-033 §3) + ADR-029/030/031/032 frontmatter class 4건 reapply.
- **AC-4**: counter family SSOT — per-ADR scope_manifest `verify_evidence.telemetry_counter` field schema 정의 (ADR-033 §본문). counter name + family + emit location.
- **AC-5**: 기존 ADR amendment grandfathering — production-wired ADR (ADR-029/030/031/017/009/027) 만 quad 의무, governance ADR triad v1+Caveat. ADR-033 §7 박제.

## §5 INV (3종)

- **INV-1**: ADR-032 §9 Self-reference Caveat quad 확장 = `telemetry_counter_caveat` field 박제 의무 (governance ADR class telemetry forever 0 정상 — false-positive fail 차단, R1 mitigation). ADR-032 §9 INV-1 reapply.
- **INV-2**: doc-only Story = code wiring 0 (production runtime untouched). cross-repo telemetry emit = MCT-192 sub-2 carry.
- **INV-3**: ADR frontmatter class taxonomy = additive only (3 스타일 비동질 보존, 정규화 금지 — F-0b/R3).

## §6 scope_manifest (PMOAgent 2nd pass 산출 — SSOT 입력)

> 본 spec §6 = `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` 직접 입력. implementer 가 본 YAML 인용 → planned_files 10 + design_decisions Q1-Q10 + risks R1-R5 + pr_completeness_checklist 전수 carry.

```yaml
epic_key: EPIC-evidence-quad-runtime-telemetry
epic_status: IN_PROGRESS
parent_dependency: "ADR-032 §8.1 future-work (MCT-190 LAND 2026-05-17, hub#375 6f19ec0)"
sequential: true
owner_adr: "ADR-033 (신규 Proposed) + ADR-032 amendment (§8.1→본문 격상 + §9 quad Caveat)"

sub_stories:
  - {key: MCT-191, seq: 1, status: IN_PROGRESS, depends_on: [],       phase_pair: phase1_only,   scope: "governance amendment doc-only"}
  - {key: MCT-192, seq: 2, status: RESERVED,    depends_on: [MCT-191], phase_pair: phase1_phase2, scope: "cross-repo telemetry counter emit (data+engine) + counter-emit triad v1 reapply"}
  - {key: MCT-193, seq: 3, status: RESERVED,    depends_on: [MCT-192], phase_pair: phase1_phase2, scope: "post-LAND verify gate (Prometheus alert counter==0 over Nd + GitHub issue 자동 발의 + monthly PMO audit cron)"}

design_decisions:
  Q1:  {chosen: C, decision: "small Epic 3 sub-Story", source: "사용자 confirm"}
  Q2:  {chosen: C, decision: "hybrid — ADR-032 §8.1→본문 격상 + §9 Caveat 확장 + 신규 ADR-033 enforcement layer"}
  Q3:  {chosen: C, decision: "grandfathering — production-wired ADR만 quad 의무 + governance ADR triad v1+Caveat"}
  Q4:  {chosen: C, decision: "N days traffic class 차등 (production-wired=14d / governance=N/A Caveat / trading-hot=market-open rolling)"}
  Q5:  {chosen: C, decision: "quad 4 evidence flat + counter-emit path triad v1 reapply (meta-recursion 1단 한정)"}
  Q6:  {chosen: B, decision: "ADR frontmatter class: governance|production|mixed taxonomy"}
  Q7:  {chosen: C, decision: "Prometheus alert (counter==0 over Nd → critical + GitHub issue) + monthly PMO audit batch"}
  Q8:  {chosen: C, decision: "per-ADR scope_manifest verify_evidence.telemetry_counter field"}
  Q9:  {chosen: A, decision: "governance/evidence-quad-runtime-telemetry.md 신규 (triad 페이지 §5 sibling cross-ref)"}
  Q10: {chosen: C, decision: "market-closed traffic class 차등 (collector=market-open rolling / engine cold=14d / governance=N/A)"}

planned_files:
  - {path: "docs/adr/ADR-032-verified-badge-evidence-triad.md", action: amend, lines: "~+45", rationale: "§8.1 future-work → 본문 rule 격상 (quad v2 = triad + 4th telemetry) + §9 telemetry_counter_caveat field 추가 + frontmatter class:governance + ADR-033 forward ref"}
  - {path: "docs/adr/ADR-033-evidence-quad-enforcement-layer.md", action: author, lines: "~+180", rationale: "신규 Proposed. §1 trigger / §2 quad v2 rule (ADR-032 §3 back ref) / §3 class taxonomy / §4 traffic class N days / §5 meta-recursion 1단 / §6 enforcement timing (sub-3 carry) / §7 grandfathering / §8 cross-ref / §9 future-work"}
  - {path: "docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md", action: author, lines: "~+130", rationale: "신규. Hyrum's Law 역방향 + runtime fitness function + Counter monotonicity 3 concept + decision-defined/caller-wired/runtime-observed 3-tier invariant. triad 페이지 §5 sibling cross-ref"}
  - {path: "docs/adr/ADR-029-tier-promotion-single-source.md", action: amend, lines: "~+1", rationale: "frontmatter class: production 추가 (additive, adr_id+category:data 스타일 보존)"}
  - {path: "docs/adr/ADR-030-docker-stack-governance.md", action: amend, lines: "~+3", rationale: "최소 frontmatter 신규 (--- + class: production + ---) — 기존 # 제목 보존"}
  - {path: "docs/adr/ADR-031-data-domain-decoupling.md", action: amend, lines: "~+3", rationale: "동형 (최소 frontmatter 신규)"}
  - {path: "docs/stories/MCT-191.md", action: author, lines: "~+260", rationale: "Story §1-§12 + §8.5 Impl Manifest quad self-reference 첫 적용"}
  - {path: "scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml", action: author, lines: "~+200", rationale: "본 Epic + MCT-191 scope_manifest"}
  - {path: "CLAUDE.md", action: amend, lines: "~+45", rationale: "§EPIC-evidence-quad-runtime-telemetry section 신규"}
  - {path: ".codeforge/counters.json", action: amend, lines: "~+40", rationale: "Epic 신설 + MCT-191 IN_PROGRESS + MCT-192/193 RESERVED + ADR-033 Proposed (next 191→194)"}

planned_adrs:
  - {adr_key: ADR-032, action: amend, status: "Accepted (유지)", boundary: "quad v2 rule SSOT (무엇이 evidence)"}
  - {adr_key: ADR-033, action: author, status: Proposed, boundary: "enforcement layer SSOT (어떻게 강제) + class taxonomy. Accepted=sub-2/3 LAND 후"}
  - {adr_key: ADR-029, action: "frontmatter class:production", status: "Accepted (유지)"}
  - {adr_key: ADR-030, action: "frontmatter class:production", status: "POLICY_FINALIZED (유지)"}
  - {adr_key: ADR-031, action: "frontmatter class:production", status: "POLICY_FINALIZED (유지)"}

verify_evidence:
  - rule: "Evidence Quad Rule v2 정의 박제 (ADR-032 §8.1→본문 격상 + ADR-033 신규) — ADR-032 self-reference quad 첫 적용"
    decision_defined_evidence: "docs/adr/ADR-032-*.md §3.2(quad) + docs/adr/ADR-033-*.md §2"
    caller_wired_evidence: "MCT-191 LAND 시점 0건 (governance ADR singleton, code wiring 0)"
    caller_wired_caveat: "self-reference Caveat — governance ADR 첫 publication caller_grep 부재 정상 (ADR-032 §9 INV-1 reapply). MCT-192+ 가 ADR-033 §2 quad rule 인용 시 누적 시작"
    telemetry_counter_caveat: "governance ADR (class:governance) telemetry counter forever 0 정상 — ADR-033 §7 grandfathering (Q3=C production-wired만 quad). false-positive fail 차단 INV (R1 mitigation)"
    integration_test: "N/A (governance ADR, code wiring 0). doc cross-ref 정합 = ADR-032§8.1↔ADR-033§2 + ADR-033§3↔4 ADR frontmatter class 1:1 reconcile"

risks:
  - {id: R1, severity: HIGH, description: "ADR-032 §9 Self-reference Caveat quad 호환성 — governance ADR telemetry forever 0 정상 logic 미박제 시 quad verify gate가 governance ADR 자체 영구 fail (자가붕괴)", mitigation: "F-0a 선제 완화 — §9 이미 caller_wired_caveat+INV-1 보유, quad Caveat=telemetry 축 확장. MCT-191이 telemetry_counter_caveat field 박제 self-reference 첫 적용 + Q3=C grandfathering 구조적 면제"}
  - {id: R2, severity: MEDIUM, description: "ADR-033 신규 ↔ ADR-032 cross-document SSOT drift (MCT-179 8회째 risk)", mitigation: "Q1-Q10 ↔ ADR-033 §1-§9 ↔ scope_manifest 1:1 전수 reconcile (MCT-179 c8e4b8e 패턴) + ADR-032 §8.1→ADR-033 forward + ADR-033 §2→ADR-032 §3 back ref"}
  - {id: R3, severity: MEDIUM, description: "ADR frontmatter class 4 ADR touch — 3 스타일 비동질 정규화 시 SSOT drift / 분류 오판", mitigation: "additive only invariant — 스타일 보존, class: field만. ADR-030/031 최소 frontmatter 신규. ADR-033 §3 분류표 SSOT"}
  - {id: R4, severity: LOW, description: "domain knowledge sibling 중복 — triad 페이지 ↔ quad 페이지 desync", mitigation: "quad=4th gate delta만 + triad 페이지 §5 forward ref (DRY)"}
  - {id: R5, severity: LOW, description: "Phase 0 verify lesson 9회째", mitigation: "doc-only=cross-repo 0 구조적 회피. worktree mct-191-evidence-quad base=origin/main fresh 격리"}

pr_completeness_checklist:
  pre_merge:
    - "ADR-032 §8.1→본문 격상 + §9 telemetry_counter_caveat + frontmatter class:governance"
    - "ADR-033 신규 §1-§9 (Proposed) + ADR-032 §3 back ref"
    - "ADR-032 §8.1 ↔ ADR-033 §2 양방향 cross-ref 정합"
    - "ADR-033 §3 class 분류표 ↔ ADR-029/030/031/032 frontmatter class 4건 1:1 reconcile"
    - "evidence-quad-runtime-telemetry.md 신규 + triad 페이지 §5 sibling cross-ref"
    - "Q1-Q10 ↔ ADR-033 §1-§9 ↔ scope_manifest 1:1 전수 reconcile (R2)"
    - "Story MCT-191 §1-§12 + §8.5 Impl Manifest quad self-reference template"
    - "CLAUDE.md §Epic section + counters.json (Epic+MCT-191/192/193+ADR-033, next 191→194)"
  post_merge:
    - "RETRO-MCT-191.md 신규"
    - "EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md §Story-1 (milestone 1/3)"
    - "PMO-AUDIT-MCT-191.md §lane gate + verify_evidence quad self-reference verify"
    - "Story frontmatter COMPLETED + §11 LAND timeline 실 PR sha"
    - "counters.json MCT-191 COMPLETED + ADR-033 Proposed 유지 (Accepted=sub-2/3 LAND 후)"

next_story: "MCT-192 (sub-2, cross-repo telemetry counter emit) — MCT-191 LAND 후 진입"
```

## §7 다음 lane = superpowers:writing-plans

1. `superpowers:writing-plans` 호출 → plan file (`docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`)
2. implementer dispatch (10 file author, doc-only file disjoint batch)
3. PR open + admin merge + post-merge cleanup
4. PMO retro 자동 dispatch (memory `feedback_pmo_retro_mandatory`)

worktree = `c:\workspace\mclayer\mctrader-hub\.claude\worktrees\mct-191-evidence-quad` (Phase 1 PR LAND 후 post-merge cleanup 별 worktree 패턴, MCT-190 선례 정합).
