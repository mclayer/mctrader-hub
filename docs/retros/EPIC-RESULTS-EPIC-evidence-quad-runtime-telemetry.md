---
type: epic-results
epic_key: EPIC-evidence-quad-runtime-telemetry
epic_title: "Evidence Quad — runtime telemetry counter 4번째 게이트 (triad v1 → quad v2)"
epic_status: IN_PROGRESS
milestone: "1/3 (MCT-191 COMPLETED)"
parent: "ADR-032 §8.1 future-work (MCT-190 LAND hub#375 6f19ec0)"
created_at: "2026-05-17"
author: Orchestrator (self-write SSOT)
---

# EPIC-RESULTS — EPIC-evidence-quad-runtime-telemetry

> **Status**: **IN_PROGRESS** · milestone **1/3** · MCT-191 COMPLETED (2026-05-17)
> ADR-032 evidence triad v1 → quad v2 확장. 4번째 게이트 = runtime telemetry counter ≥1
> over N days. cross-Epic governance singleton extension. 3 sub-Story sequential.

## §1 Epic 개요

ADR-032 evidence triad v1 (`file:line + caller grep ≥1 + integration test PASS`) 의 한계 =
**caller grep ≥1 게이트 만으로는 dead-in-prod false-negative 완전 차단 불가**. caller 가
존재해도 production traffic 미실행 시 silent false-negative (Hyrum's Law 역방향 — runtime
telemetry 0 over N days → production 의존자 실 부재 추정). 동형 사례 3건: MCT-184
dead-in-data (caller grep ≥1 but production caller 0) + MCT-180 paper daemon ReaderCache
미인스턴스화 + MCT-179 §D8 가공 metric (Phase 0 verify 미수행).

→ **Evidence Quad Rule v2** = `(file:line + caller_grep ≥1 + integration_test PASS) AND
(telemetry_counter ≥1 over N days)`. 4번째 게이트 (runtime telemetry counter) 가 dead-in-prod
역방향 차단. ADR-032 §8.1 future-work 의 owner Epic (MCT-190 LAND 후 진입). cross-Epic
governance singleton extension — ADR-032 quad rule SSOT / ADR-033 enforcement layer SSOT
(Q2=C 분리). 3 sub-Story sequential (SSOT chain 의존, 병렬 불가).

## §2 sub-Story 현황

| seq | Story | 상태 | scope | LAND |
|-----|-------|------|-------|------|
| 1 | **MCT-191** | **COMPLETED 2026-05-17** | governance amendment doc-only (ADR-032 §8.1→§3.2 본문 격상 + ADR-033 신규 + class taxonomy) | hub#382 (6582cc7, squash 1cde1ff, MERGED 2026-05-17T02:29:47Z) + hub post-merge cleanup PR |
| 2 | **MCT-192** | RESERVED | cross-repo telemetry counter emit (data collector/api + engine data_client/realtime/cold reader) + counter-emit triad v1 reapply (Q5=C meta-recursion 1단) + Q8=C scope_manifest verify_evidence.telemetry_counter field 적용 | — |
| 3 | **MCT-193** | RESERVED | post-LAND verify gate 운영 (Prometheus alert `increase(counter[Nd])==0` → critical + GitHub issue 자동 발의 + monthly PMO audit cron, Q7=C) + Q4+Q10=C traffic class 차등 window | — |

## §3 §Story-1 (MCT-191) — Evidence quad governance amendment (doc-only)

### 결과

- **AC 5/5 PASS / INV 3/3 PASS** (doc-only, code wiring 0 — production runtime untouched)
- doc cross-ref 1:1 reconcile verify (§8 Test Contract T-1~T-5 ALL ✅) — code lane 부재
- ADR-033 publish: Status **Proposed** (Accepted = sub-2 MCT-192 + sub-3 MCT-193 LAND 후)
- **FIX 0회** — design lane spec review iter1 **PASS FIX 0회**, code lane 부재 (doc-only)
- 단일 PR LAND timeline: hub#382 (`6582cc7`, squash `1cde1ff`, MERGED 2026-05-17T02:29:47Z,
  admin merge --squash --delete-branch) + hub post-merge cleanup PR (RETRO + PMO-AUDIT +
  EPIC-RESULTS §Story-1 + counters.json COMPLETED + Story §11 실 sha 박제)

### 10 design decisions (Codex 10 결정점 일괄 dispatch + Claude 채택, deviation 0건)

| Q | 결정점 | Codex | Claude 채택 | owner |
|---|--------|-------|-------------|-------|
| Q1 | Story 분해 | C | **C (사용자 confirm)** small Epic 3 sub-Story | epic-level |
| Q2 | ADR carrier | C | **C** hybrid (ADR-032 §8.1→본문 격상 + §9 Caveat 확장 + 신규 ADR-033) | MCT-191 |
| Q3 | grandfathering scope | C | **C** production-wired ADR만 quad 의무 + governance ADR triad v1+Caveat | MCT-191 |
| Q4 | N days window | C | **C** traffic class 차등 (production-wired=14d / governance=N/A / trading-hot=market-open rolling) | MCT-191 rule + MCT-193 운영 |
| Q5 | quad vs triad×2 | C | **C** quad 4 evidence flat + counter-emit path triad v1 reapply (meta-recursion 1단 한정) | MCT-191 rule + MCT-192 적용 |
| Q6 | governance/production 분류 | B | **B** ADR frontmatter `class: governance\|production\|mixed` taxonomy | ADR-033 §3 + MCT-191 4 ADR reapply |
| Q7 | enforcement timing | C | **C** Prometheus alert (counter==0 over Nd → critical + GitHub issue) + monthly PMO audit batch | MCT-193 |
| Q8 | counter family SSOT | C | **C** per-ADR scope_manifest `verify_evidence.telemetry_counter` field | MCT-191 schema + MCT-192 적용 |
| Q9 | domain knowledge | A | **A** `governance/evidence-quad-runtime-telemetry.md` 신규 (triad 페이지 §5 sibling cross-ref) | MCT-191 |
| Q10 | market-closed window | C | **C** traffic class 차등 (collector tick=market-open rolling / engine cold reader=14d / governance=N/A) | MCT-191 rule + MCT-193 운영 |

→ Codex 권고 deviation 0건 (10/10 채택 일치). Q1 = AskUserQuestion 사용자 confirm.

### 12 file LAND (hub#382 단일 commit 6582cc7, 1556+/3-)

- **F1** ADR-033 신규 (`docs/adr/ADR-033-evidence-quad-enforcement-layer.md`, §1-§10, 210 lines, Proposed)
- **F2** ADR-032 amend (`docs/adr/ADR-032-verified-badge-evidence-triad.md`, §3.2 Evidence Quad Rule v2 본문 격상 + §9 `telemetry_counter_caveat` + frontmatter class:governance + §8.1 본문 격상 transition, +16/-2)
- **F3** domain knowledge (`docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`, 126 lines — Hyrum's Law 역방향 + runtime fitness function + Counter monotonicity 3 concept + decision-defined/caller-wired/runtime-observed 3-tier invariant)
- **F4** ADR-029 frontmatter class:production additive (adr_id+category:data 스타일 보존)
- **F5** ADR-030 최소 frontmatter 신규 (class:production, 기존 # 제목 보존)
- **F6** ADR-031 최소 frontmatter 신규 (class:production, 동형)
- **F7** Story (`docs/stories/MCT-191.md`, 332 lines)
- **F8** EPIC scope_manifest (`scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`, 79 lines YAML valid)
- **F9** CLAUDE.md §EPIC-evidence-quad-runtime-telemetry section 신규 (+43)
- **F10** counters.json (Epic 신설 + MCT-191/192/193 + ADR-033 Proposed, next 191→194)
- **Ref1** spec (`docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md`)
- **Ref2** plan (`docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`)

CI = 6 SUCCESS + 2 IN_PROGRESS CodeQL + 1 ACTION_REQUIRED → admin merge 우회 (memory
`feedback_admin_merge_autonomy` 정합).

### F-0a 핵심 — quad = ADR-032 §8.1 future-work 본문 격상 (신규 발명 아님)

브레인스토밍 Phase 0 (codeforge:brainstorm 4 agent burst + PMOAgent 2nd pass) verified-via
실측 = session prompt 가설 5건 (F-0a~F-0e) 선제 정정. 최대 가치 = **F-0a**:

- session prompt 가설 "ADR-032 §8/§9 신규 보강" → 실측: §8.1 이미 quad 4th gate
  future-work 명시 (`ADR-032.md:196-200`) + §9 이미 Self-reference Caveat + INV-1 보유
  (`ADR-032.md:212-227`)
- → quad = **future-work 본문 격상** (신규 발명 아님). PMO Phase 0 주요 위험 (§9
  Self-reference Caveat quad 호환성 미검증 — governance ADR telemetry forever 0 정상 logic
  미박제 시 quad verify gate 가 governance ADR 자체를 영구 fail = 자가붕괴) = **F-0a 로 선제
  완화**. §9 이미 `caller_wired_caveat` + INV-1 forcing function 보유, quad Caveat = telemetry
  축 확장 (`telemetry_counter_caveat` field 추가) → **R1 HIGH 구조적 면제** (Q3=C
  grandfathering).

### ADR-032 self-reference quad 첫 적용

Story §8.5 = evidence quad 4종 동시 박제 template. MCT-191 = governance ADR singleton 이므로
`caller_wired` + `telemetry_counter` 0건 정상 (self-reference Caveat). `telemetry_counter`
forever 0 = governance ADR (class:governance) 정상 — ADR-033 §7 grandfathering (Q3=C
production-wired ADR만 quad 의무). false-positive fail 차단 INV (R1 mitigation, governance
시스템 자가붕괴 차단). ADR-032 §9 INV-1 forcing function 의 telemetry 축 확장 첫 시연.

### plugin-codeforge#822 self-discipline gate v1 consumer reapply 효과 1회 실증

doc-only Story 의 Task 1 file 부재 동형 risk = plugin-codeforge#822 (subagent self-report
verify gate) consumer reapply 로 사전 차단 (risk 0). `feedback_brainstorm_codex_review_pattern`
(Q-by-Q stop 회피, 10 결정점 burst dispatch → Claude 합성) + worktree 격리 (Phase 0 verify
lesson 9회째 사전 차단 2번째 — MCT-186 IN_PROGRESS working tree share contamination 회피, 정정
비용 0) 결합 = doc-only Story fast-path 효율 실증 (codeforge:story-cutoff-classification
classification=doc-only-fast-path 정합).

## §4 ADR 산출물 (Epic 전체)

- **ADR-033** (신규, MCT-191 author, 2026-05-17) — Evidence Quad Enforcement Layer — quad v2
  rule (ADR-032 §3 back ref) + class taxonomy + traffic class N days + meta-recursion 1단 +
  enforcement timing + grandfathering. Status: **Proposed**. Accepted = sub-2 MCT-192 + sub-3
  MCT-193 LAND 후 → POLICY_FINALIZED (Epic 3/3 milestone COMPLETED).
- **ADR-032** amend (Accepted 유지) — §3.2 Evidence Quad Rule v2 본문 격상 (§8.1 future-work →
  본문 rule) + §9 `telemetry_counter_caveat` field 추가 + frontmatter class:governance + ADR-033
  forward ref. Status: **Accepted (유지)** — boundary = quad v2 rule SSOT (무엇이 evidence).
- **ADR-029/030/031** frontmatter `class:production` additive (Accepted/POLICY_FINALIZED 유지) —
  additive only invariant (3 스타일 비동질 보존, 정규화 금지, SSOT drift 8회째 차단). ADR-029
  = adr_id+category:data 스타일 보존 / ADR-030·031 = 최소 frontmatter 신규 (기존 # 제목 보존).

## §5 핵심 결정 (Q1-Q10 ↔ ADR-033 §1-§9 ↔ scope_manifest 1:1 reconcile, MCT-179 c8e4b8e 패턴)

| Q | 결정 | option | Owner | 상태 |
|---|------|--------|-------|------|
| Q1 | small Epic 3 sub-Story | C | epic-level | **VERIFIED** (사용자 confirm) |
| Q2 | hybrid ADR carrier (ADR-032 본문 격상 + ADR-033 신규) | C | MCT-191 | **VERIFIED 2026-05-17** (ADR-033 Proposed + ADR-032 amend LAND) |
| Q3 | grandfathering (production-wired만 quad) | C | MCT-191 | **VERIFIED 2026-05-17** (ADR-033 §7 박제) |
| Q4 | N days traffic class 차등 | C | MCT-191 rule + MCT-193 운영 | **partial VERIFIED** (rule 박제, 운영 = MCT-193) |
| Q5 | quad 4 evidence flat + counter-emit triad v1 reapply | C | MCT-191 rule + MCT-192 적용 | **partial VERIFIED** (rule 박제, 적용 = MCT-192) |
| Q6 | ADR frontmatter class taxonomy | B | ADR-033 §3 + MCT-191 reapply | **VERIFIED 2026-05-17** (4 ADR frontmatter LAND) |
| Q7 | Prometheus alert + monthly PMO audit | C | MCT-193 | RESERVED (sub-3 owner) |
| Q8 | scope_manifest verify_evidence.telemetry_counter field | C | MCT-191 schema + MCT-192 적용 | **partial VERIFIED** (schema 박제, 적용 = MCT-192) |
| Q9 | governance/evidence-quad-runtime-telemetry.md 신규 | A | MCT-191 | **VERIFIED 2026-05-17** (126 lines LAND + triad §5 cross-ref) |
| Q10 | market-closed traffic class 차등 | C | MCT-191 rule + MCT-193 운영 | **partial VERIFIED** (rule 박제, 운영 = MCT-193) |

→ Codex deviation 0건. R2 mitigation (MCT-179 8회째 cross-document SSOT drift risk) = Q1-Q10
↔ ADR-033 §1-§9 ↔ scope_manifest design_decisions 1:1 전수 reconcile + ADR-032 §8.1→ADR-033
forward + ADR-033 §2→ADR-032 §3 back ref.

## §6 Risk 현황

| Risk | Severity | 상태 |
|------|----------|------|
| R1 | HIGH | **F-0a 선제 완화 실증** — §9 이미 caller_wired_caveat+INV-1 보유, quad Caveat=telemetry 축 확장. `telemetry_counter_caveat` field self-reference 첫 적용 + Q3=C grandfathering 구조적 면제 (governance ADR 자가붕괴 차단) |
| R2 | MEDIUM | **완화** — Q1-Q10 ↔ ADR-033 §1-§9 ↔ scope_manifest 1:1 전수 reconcile (MCT-179 c8e4b8e 패턴) + ADR-032↔ADR-033 양방향 cross-ref. MCT-179 8회째 risk 사전 차단 |
| R3 | MEDIUM | **완화** — additive only invariant (스타일 보존, class: field만). ADR-030/031 최소 frontmatter 신규. ADR-033 §3 분류표 SSOT |
| R4 | LOW | **완화** — quad=4th gate delta만 + triad 페이지 §5 양방향 forward ref (DRY) |
| R5 | LOW | **사전 차단 2번째** — doc-only=cross-repo 0 구조적 회피 + worktree mct-191-evidence-quad base=origin/main fresh 격리 (Phase 0 verify lesson 9회째, MCT-190 8회째 forcing function reapply) |

## §7 Epic CLOSED prerequisite (POLICY_FINALIZED → CLOSED, post-Epic 별 PR/Story)

| prereq | 내용 | timing |
|--------|------|--------|
| sub-2 MCT-192 LAND | cross-repo telemetry counter emit (data collector/api + engine data_client/realtime/cold reader) + counter-emit triad v1 reapply + scope_manifest verify_evidence.telemetry_counter field 적용 | MCT-191 Phase 1 PR MERGED ✓ 후 진입 |
| sub-3 MCT-193 LAND | post-LAND verify gate 운영 (Prometheus alert `increase(counter[Nd])==0` → critical + GitHub issue 자동 발의 + monthly PMO audit cron) + traffic class 차등 window 운영 | MCT-192 LAND ✓ 후 진입 |
| ADR-033 Proposed → Accepted | sub-2 + sub-3 LAND 후 (enforcement layer 실 운영 evidence) → POLICY_FINALIZED (Epic 3/3 milestone COMPLETED) | sub-2/sub-3 LAND 후 |
| Epic CLOSED 박제 PR | IN_PROGRESS → CLOSED transition (scope_manifest + CLAUDE.md + EPIC-RESULTS amend). production evidence 완성 후 별 PR (docker-stack/tier-promotion/data-domain-decoupling 패턴 정합) | 별 PR |

## §8 Key References + 다음 Story 진입 권고

### Key References

- spec: `docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`
- scope_manifest: `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`
- ADR-033 (신규, Proposed): `docs/adr/ADR-033-evidence-quad-enforcement-layer.md`
- ADR-032 amend (Accepted 유지): `docs/adr/ADR-032-verified-badge-evidence-triad.md` §3.2/§9
- domain knowledge: `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`
- Story: `docs/stories/MCT-191.md`
- RETRO: `docs/retros/RETRO-MCT-191.md` (post-merge step P1 신규)
- PMO-AUDIT: `docs/retros/PMO-AUDIT-MCT-191.md` (§lane gate + quad self-reference verify)

### 다음 Story 진입 권고

**MCT-192** (sub-2, sequential_phase 2) — cross-repo telemetry counter emit (mctrader-data
collector/api + mctrader-engine data_client/realtime/cold reader) + counter-emit code path
triad v1 reapply (Q5=C meta-recursion 1단) + Q8=C scope_manifest
`verify_evidence.telemetry_counter` field 적용.

진입 prerequisite = MCT-191 Phase 1 PR MERGED ✓ (hub#382 1cde1ff, 2026-05-17T02:29:47Z).
채택 결정 carry: Q5=C (counter-emit path triad v1 reapply, MCT-179 §D8 가공 metric risk 차단)
+ Q8=C (per-ADR scope_manifest verify_evidence.telemetry_counter field 적용). ADR-033 Status
= Proposed 유지 (Accepted = sub-2 + sub-3 LAND 후).
