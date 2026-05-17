# MCT-191 — Evidence Quad Governance Amendment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development — fresh subagent per task, file-disjoint parallel dispatch. **MCT-190 Lesson 5 reapply (plugin-codeforge#822 self-discipline gate v1 consumer)**: 각 implementer subagent 는 Write/Create 후 자동 verify report 의무 (ls + line count + Grep keyword) + status BLOCKED 시 success 보고 금지. Orchestrator 는 critical artifact (ADR/Story/scope_manifest) author 후 git status verify 의무.

**Goal:** ADR-032 evidence triad v1 → quad v2 확장 governance amendment (doc-only) — ADR-032 §8.1 future-work 본문 격상 + 신규 ADR-033 enforcement layer + class taxonomy + domain knowledge.

**Architecture:** EPIC-evidence-quad-runtime-telemetry sub-1 (doc-only, phase1_only, codeforge:story-cutoff-classification fast-path). 10 file author. 단일 PR (hub#TBD) + post-merge cleanup 별 PR (MCT-190 선례). ADR-032 = quad rule SSOT / ADR-033 = enforcement layer SSOT (Q2=C governance vs operational 분리). F-0a 핵심 = quad = §8.1 future-work 본문 격상 (신규 발명 아님 → R1 HIGH 선제 완화).

**Tech Stack:** Markdown (ADR/Story/domain-knowledge), YAML frontmatter (scope_manifest + ADR frontmatter class taxonomy), JSON (counters.json), Git workflow (worktree 격리 + 단일 PR + admin merge).

**Worktree:** `c:\workspace\mclayer\mctrader-hub\.claude\worktrees\mct-191-evidence-quad` (branch worktree-mct-191-evidence-quad, base=origin/main fresh).

**Spec reference:** `docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md` (§6 scope_manifest YAML SSOT 입력)

---

## File Structure

10 file (PMOAgent 2nd pass scope_manifest):

| # | path | action | lines | dependency |
|---|------|--------|-------|-----------|
| F1 | `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` | create | ~180 | none (Epic entry) |
| F2 | `docs/adr/ADR-032-verified-badge-evidence-triad.md` | amend | ~+45 | F1 (ADR-033 forward ref) |
| F3 | `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md` | create | ~130 | F1+F2 cross-ref |
| F4 | `docs/adr/ADR-029-tier-promotion-single-source.md` | amend | ~+1 | F1 (ADR-033 §3 class taxonomy) |
| F5 | `docs/adr/ADR-030-docker-stack-governance.md` | amend | ~+3 | F1 |
| F6 | `docs/adr/ADR-031-data-domain-decoupling.md` | amend | ~+3 | F1 |
| F7 | `docs/stories/MCT-191.md` | create | ~260 | F1-F6 cross-ref + §8.5 |
| F8 | `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` | create | ~200 | spec §6 carry |
| F9 | `CLAUDE.md` | amend | ~+45 | F1-F8 |
| F10 | `.codeforge/counters.json` | amend | ~+40 | none |

**Post-merge** (Story §11 LAND timeline 의무, MCT-190 선례):
| P | action |
|---|--------|
| P1 | counters.json MCT-191 COMPLETED + Story §11 LAND timeline 실 sha (별 cleanup PR) |
| P2 | RETRO-MCT-191.md + PMO-AUDIT-MCT-191.md + EPIC-RESULTS §Story-1 |
| P3 | PMO retro final dispatch |

---

## Task Decomposition

### Task 1: ADR-033 신규 author (F1)

**Files:** Create `docs/adr/ADR-033-evidence-quad-enforcement-layer.md`

**Reference:** spec §2 (Q1-Q10 채택) + spec §6 scope_manifest. ADR-031 (`docs/adr/ADR-031-data-domain-decoupling.md`) = 선례 governance singleton 패턴 참고.

- [ ] **Step 1: frontmatter + §1-§9 author**

```yaml
---
adr_key: ADR-033
title: Evidence Quad Enforcement Layer
status: Proposed
class: governance
proposed_at: "2026-05-17"
owner_story: MCT-191
epic: EPIC-evidence-quad-runtime-telemetry
parent: ADR-032 §8.1 future-work
cross_ref:
  - "ADR-032 §3 (Triad Rule v1 back ref) + §8.1 (quad future-work) + §9 (Self-reference Caveat)"
  - "ADR-029/030/031 (class:production grandfathering 대상)"
amendments: []
---
```

본문 §1-§9:
- §1 Trigger — ADR-032 §8.1 future-work (Hyrum's Law 역방향 dead-in-prod false-negative). MCT-184 dead-in-data + MCT-180 paper ReaderCache + MCT-179 §D8 가공 metric 동형 사례 3건.
- §2 Quad v2 Rule (triad + 4th telemetry gate). ADR-032 §3 Triad Rule v1 back ref. `(file:line + caller_grep ≥1 + integration_test PASS) AND (telemetry_counter ≥1 over N days)`. Counter monotonicity wiring proof (Prometheus Counter ≠ Gauge).
- §3 ADR class taxonomy — `class: governance|production|mixed` frontmatter field. governance = code wiring 0 (telemetry forever 0 정상) / production = code wiring 有 (quad 의무) / mixed = 부분. 분류표: ADR-029/030/031/017/009/027 = production, ADR-032/033/045/064 = governance.
- §4 Traffic class 차등 N days window (Q4+Q10=C): production-wired = 14d calendar / governance = N/A Caveat / trading-hot path (collector tick) = market-open hours rolling (KRX 09:00-15:30 KST, weekend/공휴일 제외) / trading-cold (engine cold reader) = 14d calendar. Counter `increase()` semantic 명시 (container restart counter reset 자동 보정).
- §5 Quad meta-recursion 1단 차단 (Q5=C): counter-emit code path 자체 = triad v1 reapply 의무 (counter file:line + counter caller grep ≥1 + counter integration test). 무한 recursion 차단 (counter-of-counter 미적용). MCT-179 §D8 가공 metric (Phase 0 verify 미수행 가공 metric) 동형 risk 차단.
- §6 Enforcement timing (Q7=C): Prometheus alert rule (`counter == 0 over Nd` → critical alert + GitHub issue 자동 발의) + monthly PMO audit batch verify (classification drift 보정). 실 운영 = sub-3 MCT-193 owner (carry).
- §7 Grandfathering scope (Q3=C): production-wired ADR (ADR-029/030/031/017/009/027) 만 quad 의무. governance ADR (ADR-032/033/045/064) = triad v1 + telemetry_counter_caveat. MCT-191 LAND 후 신규 production ADR = quad 의무 default.
- §8 Cross-ref — ADR-032 §3/§8.1/§9 + plugin-codeforge#804/#805/#822 + MCT-184/180/179 dead-in-prod 사례 + EPIC-evidence-quad-runtime-telemetry sub-2/sub-3.
- §9 Future Work — sub-2 MCT-192 (cross-repo telemetry emit) + sub-3 MCT-193 (verify gate 운영) carry. counter family SSOT = per-ADR scope_manifest verify_evidence.telemetry_counter field (Q8=C).

- [ ] **Step 2: verify**

Read full file. Grep `Hyrum|quad v2|class taxonomy|grandfathering|meta-recursion|telemetry_counter` 키워드 박제. line count ~180 verify. **verify report 의무 (BLOCKED 시 success 금지)**.

---

### Task 2: ADR-032 amend (F2)

**Files:** Modify `docs/adr/ADR-032-verified-badge-evidence-triad.md`

**Reference:** F1 (ADR-033 신규 — forward ref 대상). 기존 ADR-032 §3 (line 65-95 Triad Rule v1) + §8.1 (line 196-200 future-work) + §9 (line 212-227 Self-reference Caveat + INV-1).

- [ ] **Step 1: Read ADR-032 §3 + §8.1 + §9 위치 확인**

Grep `## §3|§8.1|## §9|caller_wired_caveat|INV-1` → 정확한 line range.

- [ ] **Step 2: frontmatter class:governance 추가 (additive only — adr_key+status 스타일 보존)**

```yaml
# frontmatter 기존 유지 + 추가:
class: governance
```

- [ ] **Step 3: §8.1 future-work → 본문 rule 격상**

§8.1 "Evidence triad 4번째 게이트 (별 Story MCT-NNN owner)" → §3.2 신규 본문 rule 격상:
```markdown
### §3.2 Evidence Quad Rule v2 (triad superset)

triad v1 (§3) + 4번째 게이트: **runtime telemetry counter ≥ 1 over N days** (production traffic 실 wiring evidence — Hyrum's Law 역방향 dead-in-prod false-negative 차단).

quad v2 enforcement layer 운영 = ADR-033 (forward ref). class taxonomy + traffic class N days + grandfathering = ADR-033 §3/§4/§7.

triad v1 = governance ADR (class:governance) SSOT 유지 (telemetry forever 0 정상, §9 Caveat). quad v2 = production ADR (class:production) 의무.
```
§8.1 위치 = "→ ADR-033 §2 본문 격상 완료 (MCT-191 LAND)" cross-ref 로 정정.

- [ ] **Step 4: §9 Self-reference Caveat quad 확장 (telemetry_counter_caveat field 추가)**

§9 기존 `caller_wired_caveat` 옆에 추가:
```markdown
- `telemetry_counter_caveat`: "governance ADR (class:governance) telemetry counter forever 0 정상 — ADR-033 §7 grandfathering (production-wired ADR만 quad 의무). false-positive fail 차단 INV (R1 mitigation). governance ADR singleton 의 quad verify gate 면제 = self-reference 첫 적용 (MCT-191 본 Story)."
```
INV-1 forcing function 확장: "quad verify gate 가 governance ADR 자체를 telemetry 0 으로 fail 시키지 않음 (자가붕괴 차단)".

- [ ] **Step 5: §8 cross-ref ADR-033 forward ref 추가**

§8 Consequences/Cross-ref 에 `ADR-033 (evidence quad enforcement layer, §8.1 본문 격상 carrier)` 추가.

- [ ] **Step 6: verify**

Read amended sections. Grep `§3.2|telemetry_counter_caveat|ADR-033|class: governance` 박제. ADR-032 §8.1↔ADR-033 §2 양방향 cross-ref 정합 verify. **verify report 의무**.

---

### Task 3: domain knowledge governance/evidence-quad-runtime-telemetry.md 신규 (F3)

**Files:** Create `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`

**Reference:** F1 ADR-033 §2 + F2 ADR-032 §3.2. sibling = `docs/domain-knowledge/domain/governance/evidence-triad-verified-badge.md` (117 lines, R4 cross-ref 의무).

- [ ] **Step 1: frontmatter + §1-§5 author**

```yaml
---
type: domain-knowledge
domain: governance
title: Evidence Quad — Runtime Telemetry Counter
adr_cross_ref: "ADR-033 (enforcement) + ADR-032 §3.2 (quad rule)"
sibling: evidence-triad-verified-badge.md
created_at: "2026-05-17"
author: MCT-191
---
```

§1 Concept (3 — ResearcherAgent):
- (1) Hyrum's Law 역방향 — "all observable behaviors will be depended on" 의 대우. telemetry counter == 0 over N days → production 의존자 부재 추정 (dead-in-prod detection). source: lawsofsoftwareengineering.com/laws/hyrums-law
- (2) Runtime fitness function — triad = static fitness (build-time), quad 4번째 = runtime fitness (production-time). source: Ford/Parsons/Kua "Building Evolutionary Architectures" ch.2
- (3) Counter monotonicity as wiring proof — Prometheus Counter (monotonic 누적) ≠ Gauge (current-state, scrape miss false-negative). counter ≥1 over Nd = irrefutable monotonic evidence. source: prometheus.io/docs/concepts/metric_types

§2 decision-defined / caller-wired / runtime-observed 3-tier 분리 invariant — triad = decision-defined + caller-wired (static), quad 4번째 = runtime-observed (dynamic). MCT-189 130GB 사례 = caller-wired LAND 부재 / MCT-184 dead-in-data = caller-wired LAND 有 but runtime-observed 0.

§3 traffic class 차등 N days (ADR-033 §4 cross-ref) — production-wired=14d / governance=N/A Caveat / trading-hot=market-open rolling. KRX 09:00-15:30 KST market-closed false-negative 차단 근거.

§4 meta-recursion 1단 차단 (ADR-033 §5 cross-ref) — counter-emit code path 자체 triad v1 reapply, counter-of-counter 미적용. MCT-179 §D8 가공 metric risk 차단.

§5 sibling cross-ref — `evidence-triad-verified-badge.md` (triad v1 SSOT 유지) forward ref. quad 페이지 = 4th gate delta 만 (DRY, R4 mitigation). ADR-033 (enforcement SSOT) + ADR-032 §3.2 (quad rule SSOT).

- [ ] **Step 2: verify**

Read full file. Grep `Hyrum|runtime fitness|Counter monotonicity|3-tier|sibling` 박제. line ~130 verify. **verify report 의무**.

---

### Task 4: ADR-029/030/031 frontmatter class:production additive (F4+F5+F6)

**Files:** Modify `docs/adr/ADR-029-tier-promotion-single-source.md` + `docs/adr/ADR-030-docker-stack-governance.md` + `docs/adr/ADR-031-data-domain-decoupling.md`

**Reference:** F1 ADR-033 §3 class 분류표 (production = ADR-029/030/031). **R3 additive only invariant — 3 스타일 비동질 보존, 정규화 금지**.

- [ ] **Step 1: Read 3 ADR frontmatter 현 스타일 확인**

Read ADR-029 line 1-12 (adr_id+category:data 스타일) + ADR-030 line 1-3 (frontmatter 부재, # 제목 직접) + ADR-031 line 1-3 (동형).

- [ ] **Step 2: ADR-029 frontmatter class:production 추가 (adr_id+category:data 스타일 보존)**

기존 frontmatter 안에 `class: production` 1 line additive (기존 adr_id/category/is_transitional 등 보존).

- [ ] **Step 3: ADR-030 최소 frontmatter 신규 (기존 # 제목 line 1 보존)**

ADR-030 frontmatter 부재 → file 최상단에 추가:
```yaml
---
class: production
---
```
기존 `# ADR-030 ...` 제목 line 보존 (frontmatter 위에 prepend).

- [ ] **Step 4: ADR-031 최소 frontmatter 신규 (동형)**

ADR-031 동일 — `---\nclass: production\n---` prepend, 기존 `# ADR-031 ...` 보존.

- [ ] **Step 5: verify**

Read 3 ADR frontmatter. Grep `class: production` 3 hits verify. ADR-029 기존 adr_id/category 보존 verify (정규화 0). ADR-033 §3 분류표 ↔ 3 ADR class 1:1 reconcile. **verify report 의무**.

---

### Task 5: Story MCT-191.md 신규 (F7)

**Files:** Create `docs/stories/MCT-191.md`

**Reference:** spec §1-§7 + spec §6 scope_manifest + F1-F6 산출 + `docs/stories/MCT-190.md` (선례 doc-only Story 패턴).

- [ ] **Step 1: frontmatter**

```yaml
---
key: MCT-191
title: "Evidence quad governance amendment (doc-only) — ADR-032 §8/§9 본문 격상 + ADR-033 신규 + class taxonomy"
status: COMPLETED  # post-LAND 전환 (phase:박제-amendment → COMPLETED)
repo: mctrader-hub
phase_pair: phase1_only
classification: doc-only-fast-path
epic: EPIC-evidence-quad-runtime-telemetry
sequential_phase: 1
parent_dependency: "ADR-032 §8.1 future-work (MCT-190 LAND hub#375 6f19ec0)"
owner_for_adr: "ADR-033 (신규 Proposed) + ADR-032 amendment"
created_at: "2026-05-17"
completed_at: "2026-05-17"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-191-evidence-quad"
worktree_branch: worktree-mct-191-evidence-quad
land_prs:
  - "mctrader-hub#TBD (Phase 1 단일 PR 10 file)"
  - "mctrader-hub#TBD-post-merge (counters COMPLETED + Story §11 + RETRO)"
---
```

- [ ] **Step 2: §0 Phase 0 Verify Gate (F-0a~F-0e 5 facts table)**

spec §1.2 박제 (F-0a quad=future-work 본문 격상 / F-0b frontmatter 3 스타일 additive / F-0c 228 lines / F-0d governance sibling / F-0e counters next=191).

- [ ] **Step 3: §1-§5 (요구사항 + spec/plan cross-ref + AC + design decisions Q1-Q10)**

§1 사용자 요구사항 verbatim ("다음 스토리 수행" + AskUserQuestion small Epic 채택). §2 spec cross-ref. §3 AC-1~5 (spec §4). §4 plan cross-ref. §5 design decisions Q1-Q10 (spec §2, Codex+Claude).

- [ ] **Step 4: §6 risks + §7 cross-ref + §8 Test Contract**

§6 R1-R5 (spec §6 risks). §7 cross-ref (ADR-032/033 + ADR-029/030/031 + plugin-codeforge#804/#805/#822 + MCT-190 §8.1 + EPIC sub-2/3). §8 Test Contract = doc cross-ref 정합 verify only (doc-only — ADR-032§8.1↔ADR-033§2 + ADR-033§3↔4 ADR frontmatter 1:1 reconcile).

- [ ] **Step 5: §8.5 Impl Manifest (ADR-032 self-reference quad 첫 적용)**

10 file checklist (spec §6 pr_completeness_checklist pre_merge). verify_evidence row:
- decision_defined_evidence: ADR-032 §3.2 + ADR-033 §2 + governance/evidence-quad-runtime-telemetry.md
- caller_wired_evidence: "MCT-191 LAND 시점 0건 (governance ADR singleton)"
- caller_wired_caveat: self-reference Caveat (ADR-032 §9 INV-1 reapply, MCT-192+ 누적 시작)
- telemetry_counter_caveat: "governance ADR class telemetry forever 0 정상 (ADR-033 §7 grandfathering). false-positive 차단 INV (R1)"
- integration_test: N/A (governance ADR). doc cross-ref 1:1 reconcile

- [ ] **Step 6: §9 cross-Story carry + Phase 0 verify lesson 9회째 + §10 FIX Ledger + §11 LAND timeline + §12 회고 placeholder**

§9 Phase 0 verify lesson 9회째 = doc-only cross-repo 0 구조적 회피 + worktree 격리. §10 FIX Ledger (doc-only, design lane only, "FIX 0회" placeholder). §11 LAND timeline (post-merge 박제). §12 회고 (CFP-138/ADR-045 4-field schema placeholder, RETRO-MCT-191.md cross-ref).

- [ ] **Step 7: verify**

Read full file. Grep `§8.5|verify_evidence|telemetry_counter_caveat|F-0a|quad` 박제. line ~260 verify. **verify report 의무**.

---

### Task 6: EPIC scope_manifest YAML 신규 (F8)

**Files:** Create `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`

**Reference:** spec §6 YAML 완전체 직접 carry.

- [ ] **Step 1: spec §6 YAML 직접 carry**

spec §6 의 YAML 전체 (epic_key + sub_stories 3 + design_decisions Q1-Q10 + planned_files 10 + planned_adrs 5 + verify_evidence quad + risks R1-R5 + pr_completeness_checklist) 를 `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` 로 carry.

- [ ] **Step 2: verify**

Read full file. YAML lint (python `yaml.safe_load`). Grep `epic_key|sub_stories|design_decisions|risks` 박제. **verify report 의무**.

---

### Task 7: CLAUDE.md §Epic section 신규 (F9)

**Files:** Modify `CLAUDE.md`

**Reference:** 기존 CLAUDE.md §MCT-190 COMPLETED section 직후 (Grep `## MCT-190 COMPLETED` → line). MCT-190 section 패턴 정합.

- [ ] **Step 1: Grep `## MCT-190 COMPLETED` line number 확인**

- [ ] **Step 2: §EPIC-evidence-quad-runtime-telemetry section append (MCT-190 직후 또는 §Key References 직전)**

```markdown
## EPIC-evidence-quad-runtime-telemetry (MCT-191 IN_PROGRESS 2026-05-17, milestone 1/3)

> ADR-032 evidence triad v1 → quad v2 확장 (4번째 게이트 runtime telemetry counter ≥1 over N days,
> Hyrum's Law 역방향 dead-in-prod false-negative 차단). cross-Epic governance singleton extension.
> 3 sub-Story sequential (MCT-191 doc-only / MCT-192 cross-repo emit / MCT-193 verify gate).

### sub-Story 현황

| seq | Story | 상태 | scope |
|---|-------|------|-------|
| 1 | **MCT-191** | **COMPLETED 2026-05-17** | governance amendment doc-only (ADR-032 §8.1→본문 격상 + ADR-033 신규 + class taxonomy) |
| 2 | MCT-192 | RESERVED | cross-repo telemetry counter emit (data+engine) + counter-emit triad v1 reapply |
| 3 | MCT-193 | RESERVED | post-LAND verify gate (Prometheus alert counter==0 over Nd + monthly PMO audit cron) |

### MCT-191 결과 (10 결정점 Q1-Q10)

Q1=C small Epic / Q2=C ADR-032 amend + ADR-033 신규 / Q3=C grandfathering production-wired만 / Q4=C traffic class 차등 N days / Q5=C meta-recursion 1단 / Q6=B class taxonomy / Q7=C alert+PMO audit / Q8=C per-ADR scope_manifest field / Q9=A governance/ 신규 / Q10=C market-closed traffic class 차등.

### ADR 산출

- **ADR-032 amend** — §8.1 future-work → §3.2 본문 rule 격상 + §9 telemetry_counter_caveat + frontmatter class:governance (Accepted 유지)
- **ADR-033 신규** (Proposed) — evidence quad enforcement layer §1-§9 (Accepted = sub-2/sub-3 LAND 후)
- **ADR-029/030/031 frontmatter class:production** additive (R3 — 3 스타일 비동질 보존, 정규화 0)

### Key References

- Story: `docs/stories/MCT-191.md`
- spec: `docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`
- ADR-033: `docs/adr/ADR-033-evidence-quad-enforcement-layer.md`
- ADR-032 §3.2 quad: `docs/adr/ADR-032-verified-badge-evidence-triad.md`
- domain-knowledge: `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`
- scope_manifest: `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`
- parent: ADR-032 §8.1 (MCT-190 LAND hub#375)

### 다음 Story 진입 권고

**MCT-192** (sub-2 cross-repo telemetry counter emit) — MCT-191 Phase 1 PR MERGED ✓ 후 진입.
```

- [ ] **Step 3: verify**

Read CLAUDE.md amended. Grep `## EPIC-evidence-quad-runtime-telemetry` 1 hit + `## MCT-190 COMPLETED` 기존 보존. **verify report 의무**.

---

### Task 8: counters.json amend (F10)

**Files:** Modify `.codeforge/counters.json`

**Reference:** 기존 counters.json line 6 (mctrader-hub.next=191) + reservations 끝부분 (MCT-190 entry 직후).

- [ ] **Step 1: mctrader-hub.next 191 → 194**

`"mctrader-hub": { "next": 191 }` → `"next": 194` (MCT-191 + MCT-192 + MCT-193 reserve).

- [ ] **Step 2: MCT-191/192/193 + ADR-033 reservation entry 추가 (MCT-190 entry 직후)**

```json
"MCT-191": {
  "title": "Evidence quad governance amendment (doc-only) — ADR-032 §8/§9 본문 격상 + ADR-033 신규 + class taxonomy",
  "reserved_at": "2026-05-17",
  "started_at": "2026-05-17",
  "completed_at": "2026-05-17",
  "status": "COMPLETED",
  "epic": "EPIC-evidence-quad-runtime-telemetry",
  "epic_milestone": "1/3",
  "sequential_phase": 1,
  "depends_on": [],
  "repo": "mctrader-hub",
  "phase_pair": "phase1_only (doc-only Story, codeforge:story-cutoff-classification fast-path)",
  "owner_for_adr": "ADR-033 (신규 Proposed) + ADR-032 amendment",
  "land_prs": ["mctrader-hub#TBD"],
  "rationale": "ADR-032 §8.1 future-work owner (MCT-190 LAND 후). Evidence triad v1 → quad v2 (4번째 게이트 runtime telemetry counter ≥1 over N days, Hyrum's Law 역방향 dead-in-prod false-negative 차단). Q1=C small Epic 3 sub-Story / Q2=C ADR-032 amend + ADR-033 신규 / Q3=C grandfathering production-wired만 / Q5=C meta-recursion 1단 / Q6=B class taxonomy / Q9=A governance/ 신규. F-0a = quad = §8.1 future-work 본문 격상 (신규 발명 아님 → R1 HIGH 선제 완화)."
},
"MCT-192": {
  "title": "Cross-repo telemetry counter emit (data collector/api + engine data_client/realtime/cold reader) + counter-emit triad v1 reapply",
  "reserved_at": "2026-05-17",
  "status": "RESERVED",
  "epic": "EPIC-evidence-quad-runtime-telemetry",
  "sequential_phase": 2,
  "depends_on": ["MCT-191"],
  "repo": "mctrader-hub + mctrader-data + mctrader-engine",
  "phase_pair": "phase1_phase2",
  "rationale": "EPIC sub-2. quad v2 4번째 게이트 telemetry counter 실 emit. mctrader-data collector/api routes + mctrader-engine data_client/realtime subscriber/cold reader. Q5=C counter-emit code path 자체 triad v1 reapply (meta-recursion 1단). Q8=C per-ADR scope_manifest verify_evidence.telemetry_counter field 적용. 진입 = MCT-191 LAND 후."
},
"MCT-193": {
  "title": "Post-LAND verify gate 운영 method (Prometheus alert counter==0 over Nd + GitHub issue 자동 발의 + monthly PMO audit cron)",
  "reserved_at": "2026-05-17",
  "status": "RESERVED",
  "epic": "EPIC-evidence-quad-runtime-telemetry",
  "sequential_phase": 3,
  "depends_on": ["MCT-192"],
  "repo": "mctrader-hub",
  "phase_pair": "phase1_phase2",
  "rationale": "EPIC sub-3. quad v2 enforcement timing 실 운영 (Q7=C). Prometheus alert rule (counter==0 over Nd → critical + GitHub issue 자동 발의) + monthly PMO audit batch (classification drift 보정). Q4+Q10=C traffic class 차등 window 운영. 진입 = MCT-192 LAND 후."
},
"ADR-033": {
  "title": "Evidence Quad Enforcement Layer — quad v2 rule + class taxonomy + traffic class N days + meta-recursion 1단 + enforcement timing + grandfathering",
  "reserved_at": "2026-05-17",
  "drafted_at": "2026-05-17",
  "status": "Proposed (MCT-191 LAND author, Accepted = sub-2 MCT-192 + sub-3 MCT-193 LAND 후)",
  "epic": "EPIC-evidence-quad-runtime-telemetry",
  "repo": "mctrader-hub",
  "owner_story": "MCT-191",
  "class": "governance",
  "parent": "ADR-032 §8.1 future-work",
  "expected_sections": "§1 trigger / §2 quad v2 rule (ADR-032 §3 back ref) / §3 class taxonomy (governance|production|mixed) / §4 traffic class N days / §5 meta-recursion 1단 / §6 enforcement timing (sub-3 carry) / §7 grandfathering (production-wired만) / §8 cross-ref / §9 future-work",
  "rationale": "ADR-032 §8.1 quad future-work 의 enforcement layer SSOT (Q2=C governance vs operational 분리). ADR-032 = quad rule SSOT (무엇이 evidence) / ADR-033 = enforcement layer SSOT (어떻게 강제) + class taxonomy. 양방향 cross-ref 의무 (MCT-179 D-row↔scope_manifest 1:1 reconcile lesson)."
}
```

- [ ] **Step 3: verify**

Read counters.json. python `json.load` syntax valid. Grep `MCT-191|MCT-192|MCT-193|ADR-033` + `"next": 194` 박제. **verify report 의무**.

---

### Task 9: PR open + admin merge (Orchestrator direct)

- [ ] **Step 1: git status verify (10 file)**

`git status --short` — 10 file 변경 confirm (ADR-033 신규 + ADR-032/029/030/031 amend + domain knowledge 신규 + Story 신규 + scope_manifest 신규 + CLAUDE.md amend + counters.json amend + spec + plan).

**Orchestrator trust-but-verify 의무 (MCT-190 Lesson 5)**: 각 critical artifact (ADR-033 / ADR-032 / Story / scope_manifest) `Get-ChildItem` + line count verify — implementer 보고 ≠ 실제 상태 gap 차단.

- [ ] **Step 2: 단일 commit (message file 방식, PowerShell quote escaping 회피 — MCT-190 lesson)**

`.git-commit-msg-mct-191.txt` 작성 후 `git commit -F`. Co-Authored-By: Claude Opus 4.7.

- [ ] **Step 3: push + PR open (body file 방식)**

`git push -u origin worktree-mct-191-evidence-quad` + `gh pr create --body-file`. PR completeness checklist 10 pre-merge 박제.

- [ ] **Step 4: CI status + admin merge**

`gh pr view --json statusCheckRollup` → doc-only CI minimal. `gh pr merge --admin --squash --delete-branch` (memory feedback_admin_merge_autonomy).

- [ ] **Step 5: PR# + commit sha 기록**

post-merge Task 10 입력.

---

### Task 10: post-merge cleanup + PMO retro (Orchestrator direct)

- [ ] **Step P1: 별 worktree (mct-191-post-merge) 진입 + counters.json COMPLETED + Story §11 LAND timeline 실 sha 박제 + RETRO-MCT-191.md + PMO-AUDIT-MCT-191.md + EPIC-RESULTS §Story-1**

MCT-190 post-merge 패턴 정합. RETRO-MCT-191 (CFP-138/ADR-045 4-field) + PMO-AUDIT-MCT-191 (§lane gate + quad self-reference verify) + EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md §Story-1 (milestone 1/3).

- [ ] **Step P2: 별 cleanup PR open + admin merge**

- [ ] **Step P3: PR gate:retro-complete label add (CFP-138/ADR-045)**

- [ ] **Step P4: PMOAgent retro final dispatch (memory feedback_pmo_retro_mandatory)**

---

## Self-Review

### Spec coverage

| spec §N | task | covered |
|---------|------|---------|
| §1 Trigger F-0a~F-0e | Task 5 §0 | ✓ |
| §2 Q1-Q10 채택 | Task 1 (ADR-033) + Task 2 (ADR-032) + Task 5 §5 + Task 7 | ✓ |
| §3 Phase 0 agent 산출 | Task 5 §0 + Task 3 (domain knowledge) | ✓ |
| §4 AC-1~5 | Task 5 §3 + Task 1 (ADR-033 §2-§7) | ✓ |
| §5 INV-1~3 | Task 2 (§9 INV-1) + Task 5 §6 (INV-2/3) | ✓ |
| §6 scope_manifest YAML | Task 6 (direct carry) | ✓ |
| §7 next lane | Task 9+10 | ✓ |

10 file 전수 task assign 완료.

### Placeholder scan

- "hub#TBD" = PR open 전 정상 placeholder (Task 10 실 PR# carry)
- 다른 placeholder 없음

### Type consistency

- `quad v2` 일관 (Task 1 §2 / Task 2 §3.2 / Task 3 §1 / Task 5 §8.5)
- `class taxonomy governance|production|mixed` 일관 (Task 1 §3 / Task 4 / Task 7)
- `telemetry_counter_caveat` 일관 (Task 2 §4 / Task 5 §8.5 / spec §6 verify_evidence)
- `meta-recursion 1단` 일관 (Task 1 §5 / Task 3 §4)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`.**

Execution = **Subagent-Driven** (memory feedback_subagent_execution + feedback_autonomous_execution 정합 — 자율 진행).

**dispatch plan** (file disjoint batch):
- **batch 1 (parallel 3)**: Task 1 (ADR-033) + Task 3 (domain knowledge) + Task 6 (scope_manifest) — file disjoint, content plan fully specified
- **batch 2 (parallel 2, Task 1 산출 cross-ref)**: Task 2 (ADR-032 amend, ADR-033 forward ref) + Task 4 (3 ADR frontmatter, ADR-033 §3 분류표)
- **batch 3 (parallel 3, 모든 산출 cross-ref)**: Task 5 (Story) + Task 7 (CLAUDE.md) + Task 8 (counters.json)
- **batch 4 (Orchestrator direct)**: Task 9 (PR open + admin merge) → Task 10 (post-merge + PMO retro)

**MCT-190 Lesson 5 reapply (plugin-codeforge#822 consumer)**: 각 implementer prompt 에 verify report 의무 강제 instruction + Orchestrator git status verify 의무 (trust-but-verify gap 차단).

REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`.
