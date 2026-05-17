---
type: brainstorm-spec
story_key: MCT-193
epic_key: EPIC-evidence-quad-runtime-telemetry
title: "Post-LAND verify gate 운영 — quad violation alert + monthly PMO audit cron + ADR-033 §6 VERIFIED + EPIC POLICY_FINALIZED 3/3"
repo: mctrader-hub
phase_pair: phase1_phase2
sequential_phase: 3
status: IN_PROGRESS
parent_dependency: "MCT-192 (sub-2 LAND hub#384 + data#79 + hub#385 + #386)"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-193-verify-gate"
worktree_branch: worktree-mct-193-verify-gate
created_at: "2026-05-17"
author: Orchestrator (codeforge:brainstorm Phase 1 산출)
phase_0_agents:
  - DomainAgent (addd3ab2124ab85d8)
  - ResearcherAgent (a09f532074df57baa) — 4 모순 발견
  - RequirementsAnalystAgent (af982cbb496cded47)
  - PMOAgent_phase0 (a19f21f3654821f19)
  - PMOAgent_phase2 (afd73fbcbe58f7ee3) — verify-via 전수 (R1 false premise 동형 재발 0) + R-1 신규 발견
codex_dispatch: 8_decision_points_burst (Q1-Q8, 8/8 정합 deviation 0)
verified_sources:
  - "worktree HEAD = 0649782 (#386 MCT-192 LAND) — git log 직접 verify"
  - "monitoring/prometheus-alerts.yml = MCT-179/180 alert (groups: mctrader-docker-stack, increase() 패턴, ==0 선례 0) — Read 58 lines"
  - ".github/workflows/ 12개 전수 schedule:/cron: 선례 0 — git ls (repo 최초 cron)"
  - "prometheus.yml = rule_files only, alerting:/alertmanager 라우팅 0 (ResearcherAgent verified)"
  - "ADR-033 §3.2 line 104 (ADR-030 trading-hot market-open rolling) + §4 line 125 (KRX 09:00-15:30 75h rolling) ↔ Q4=A 14d 단일화 SSOT drift (Orchestrator 직접 grep verify — R-1 valid)"
  - "ADR-031 counter mctrader_data_redis_stream_publish_failures_total = dead-in-data (publish_tick caller 0, MCT-192 test-injected only)"
---

# MCT-193 — Post-LAND verify gate 운영 brainstorm spec

> EPIC-evidence-quad-runtime-telemetry sub-3 (마지막). ADR-033 §6 enforcement timing Q7=C 실 carrier.
> ADR-033 Proposed → Accepted + EPIC milestone 3/3 + POLICY_FINALIZED. repo = mctrader-hub 단독.

## §1 Trigger — ADR-033 §6 enforcement timing (MCT-192 LAND 후)

### 1.1 사용자 요구사항
"다음 작업 수행하라" + PMO-AUDIT-MCT-192 §(4) 권고 P1 = MCT-193 sub-3 (post-LAND verify gate).

### 1.2 Phase 0 verify 핵심 (Orchestrator 직접 verify SSOT — MCT-192 R1 false premise 동형 재발 0)

| # | 사실 | verified-via | 판정 |
|---|------|-------------|------|
| V1 | worktree base = #386 (MCT-192 LAND 완전 반영) | 직접 `git log` | ✓ |
| V2 | ADR-033(247L) + counters MCT-193 RESERVED + monitoring/prometheus-alerts.yml + scope_manifest 전부 존재 | PMOAgent verify-via 전수 + Orchestrator 직접 grep | ✓ — **MCT-192 R1 'file 부재' false premise 동형 재발 0 (trust-but-verify lesson reapply 효과)** |
| **R-1** | **ADR-033 §3.2 line 104 (ADR-030 = trading-hot market-open rolling) + §4 line 125 (KRX 09:00-15:30 KST × 10 trading days ≈ 75h rolling) ↔ Q4=A 14d calendar 단일화 SSOT drift** | **Orchestrator 직접 grep verify (valid HIGH risk)** | ⚠️ **MCT-179 cross-doc SSOT drift 9회째 — ADR-033 §6 amendment box caveat 박제 의무 (PR-1 DesignReview 핵심 gate)** |
| R-2 | ADR-031 counter = dead-in-data (publish_tick caller 0, test-injected only) | MCT-192 §8.5 + ADR-033 §3.2 line 105 | ✓ Q1=C 제외 mitigation (MCT-179 §D8 가공 metric 8회째 차단) |
| infra | prometheus.yml alerting:/alertmanager 라우팅 0 + .github/workflows schedule: 0 (repo 최초 cron) | ResearcherAgent + git ls verify | ✓ Q3=A cron carrier / Q5=B workflow_dispatch 병행 |

## §2 핵심 결정 (Codex 8 결정점 일괄 dispatch + Claude 합성, 8/8 정합 deviation 0 — MCT-191/192 동형 full alignment 연속 3 Story)

| Q | 결정점 | 채택 | 결과 |
|---|--------|------|------|
| Q1 | ADR-031 alert 처리 | C | MCT-193 = ADR-029/030 carrier + ADR-031 alert 미등록 caveat 박제 (dead-in-data, engine MCT-186 cutover 후 별 Story enable, rolling gate 영구 fire 차단) |
| Q2 | absent() | A | `absent(<counter>) or increase(<counter>[14d]) == 0` (never-emitted series-missing + emitted-no-inc 양쪽) |
| Q3 | GitHub issue carrier | A | GitHub Action cron 이 Prometheus HTTP API query → quad violation 시 gh issue create (alertmanager 부재). prometheus-alerts.yml alert = 보조 visibility |
| Q4 | market-open rolling | A | production-wired 14d calendar 단일화 (trading-hot collector 도 14d, KRX calendar PromQL 불가 → market-open rolling 후속 carry). **R-1: ADR-033 §4 SSOT drift caveat 박제 의무** |
| Q5 | PMO audit cron 자동화 | B | schedule(monthly) + workflow_dispatch 병행 hybrid (정상 silent / drift·violation 자동 issue, repo 최초 cron risk mitigation) |
| Q6 | ADR-033 §6 VERIFIED + Accepted | A | alert rule + cron LAND 시 즉시 Proposed → Accepted (구현 완료 = transition). frontmatter 전환 = PR-2 (실 LAND 후, false-Accepted 차단) |
| Q7 | EPIC POLICY_FINALIZED timing | B | MCT-193 sub-3 박제 = ADR-033 Accepted + EPIC 3/3 + POLICY_FINALIZED. Epic CLOSED = production evidence carry 별 PR (docker-stack/tier-promotion/data-domain-decoupling 패턴) |
| Q8 | PR 구조 | A | 2 PR: PR-1 Phase 1 docs / PR-2 alert+cron+박제 통합 (hub 단독 cross-repo 0) |

## §3 Phase 0 agent 산출 합성

### 3.1 DomainAgent
quad 5 어휘 전부 기존 박제 (increase() semantic / traffic class 4종 / GitHub issue 발의 / monthly PMO audit / ADR-031 dead-in-data). governance class N/A + market-open false-positive + alert fatigue (data-health SLO budget) 핵심. 도메인 공백 없음.

### 3.2 ResearcherAgent (4 모순 — 설계 방향 결정)
1. absent() trap (dead-in-data counter series 부재 → increase() no-data) → Q2=A
2. rolling gate ↔ alert prerequisite 역설 (ADR-031 `==0` 영구 fire) → Q1=C
3. alertmanager 부재 (GitHub issue carrier = Action cron PromQL query) → Q3=A
4. market-open rolling PromQL 불가 (KRX calendar) → Q4=A 14d 단일화

### 3.3 RequirementsAnalystAgent
5 UC + 2 Edge (E-1 Prometheus restart window / E-2 dead-in-data forever 0 alert). Q1/Q2/Q3 confirm 영역 = Codex Q1/Q4/Q5 채택으로 해소.

### 3.4 PMOAgent (Phase 0 + Phase 2)
1 Story sub-3 / 2 PR / single-repo. verify-via 전수 (R1 false premise 동형 재발 0). **R-1 HIGH 신규 발견** (ADR-033 §4 market-open rolling ↔ Q4=A 14d SSOT drift). R-2 ADR-031 dead-in-data alert (MCT-179 §D8 8회째). scope_manifest YAML 완전체 (§6 박제).

## §4 AC (5종)

- **AC-1**: `monitoring/prometheus-alerts.yml` 신규 group `evidence-quad-enforcement` + QuadViolationADR029NoDualWrite (`absent(mctrader_dual_write_result_total{status="success"}) or increase(...[14d])==0` critical) + QuadViolationADR030NoCollectorTicks (`absent(mctrader_collector_ticks_total) or increase(...[14d])==0` critical). ADR-031 = 미등록 caveat 주석 (Q1=C).
- **AC-2**: `.github/workflows/quad-evidence-audit.yml` 신규 cron (repo 최초 — schedule monthly + workflow_dispatch). Prometheus HTTP API query (PROMETHEUS_URL secret, 부재 시 graceful skip) → ADR-029/030 quad violation 시 gh issue create + class taxonomy drift audit (Q3=A + Q5=B).
- **AC-3**: ADR-033 §6 VERIFIED amendment box + §4 SSOT drift caveat 박제 (Q4=A 14d 단일화 채택, §4 market-open rolling = KRX calendar PromQL 한계 후속 carry — R-1 mitigation) + §9.2 sub-3 VERIFIED + frontmatter Proposed → Accepted (PR-2).
- **AC-4**: ADR-031 dead-in-data alert 제외 정직 박제 (Q1=C — alert 미등록 + caveat, engine MCT-186 cutover 후 별 Story enable, rolling gate 영구 fire 차단). ADR-033 §3.2 ADR-031 traffic_class='test-injected only' 정합.
- **AC-5**: EPIC POLICY_FINALIZED 3/3 박제 (MCT-193 sub-3 LAND = ADR-033 Accepted + EPIC milestone 3/3) + EPIC-RESULTS §Story-3 + §3.5 PR-3 #TBD→#385 carry 정정 (PMO-AUDIT-MCT-192 §(4)-(a) piggyback). Epic CLOSED = production evidence carry 별 PR (Q7=B).

## §5 INV (3종)

- **INV-1**: ADR-031 dead-in-data counter alert 미등록 (Q1=C) — rolling gate 영구 fire 차단 (MCT-179 §D8 가공 metric 8회째). production caller-wired = engine MCT-186 cutover 후 별 Story (caveat resolve).
- **INV-2**: alert PromQL = `absent(<counter>) or increase(<counter>[14d])==0` (Q2=A) — never-emitted + emitted-no-inc 양쪽 capture. 배포 grace = cron primary carrier (Q3=A) 로 false-positive 영향 = cron issue 발의 한정 (alert page 아님, alertmanager 부재 정합).
- **INV-3**: ADR-033 §4 ↔ Q4=A SSOT drift caveat 박제 의무 (R-1) — Q4=A ↔ ADR-033 §4 amendment ↔ alert yaml comment 3-source 1:1 reconcile (MCT-179 c8e4b8e 패턴 reapply, PR-1 DesignReview gate).

## §6 scope_manifest (PMOAgent 2nd pass 산출 — verify-via 전수, R-1 HIGH 박제)

> EPIC-evidence-quad-runtime-telemetry.yaml sub-3 MCT-193 정밀화 + mct_193_* 블록 6종 (mct_192_* 패턴 mirror). PMOAgent 2nd pass YAML SSOT 직접 입력.

```yaml
# EPIC-evidence-quad-runtime-telemetry.yaml sub-3 MCT-193 amend (PR-1)
# PR-2 박제 시: epic_status IN_PROGRESS → POLICY_FINALIZED, milestone 2/3 → 3/3

sub_stories_MCT_193: {key: MCT-193, seq: 3, status: IN_PROGRESS, repo: "mctrader-hub (cross-repo 0)", depends_on: [MCT-192], phase_pair: phase1_phase2, decisions: ["Q1-C","Q2-A","Q3-A","Q4-A","Q5-B","Q6-A","Q7-B","Q8-A"], scope: "post-LAND verify gate — prometheus-alerts.yml quad alert + .github/workflows quad-evidence-audit.yml 신규 cron (repo 최초) + ADR-033 §6 VERIFIED + Accepted + EPIC POLICY_FINALIZED"}

mct_193_decisions:
  Q1: {chosen: C, decision: "ADR-031 alert 미등록 + caveat 박제 (dead-in-data, engine MCT-186 cutover 후 별 Story enable, rolling gate 영구 fire 차단 — MCT-179 §D8 8회째 mitigation). ADR-029/030 만 alert carrier"}
  Q2: {chosen: A, decision: "alert PromQL = absent(<counter>) or increase(<counter>[14d]) == 0 (never-emitted + emitted-no-inc 양쪽, absent() trap 차단)"}
  Q3: {chosen: A, decision: "GitHub issue carrier = GitHub Action cron Prometheus HTTP API query → quad violation gh issue create (alertmanager 부재 정합). prometheus-alerts.yml alert = 보조 visibility"}
  Q4: {chosen: A, decision: "production-wired 14d calendar 단일화 (KRX calendar PromQL 불가 — market-open rolling 후속 carry). R-1: ADR-033 §4 SSOT drift caveat 박제 의무"}
  Q5: {chosen: B, decision: "PMO audit cron = schedule(monthly) + workflow_dispatch hybrid (정상 silent / drift·violation 자동 issue, repo 최초 cron risk mitigation)"}
  Q6: {chosen: A, decision: "ADR-033 §6 VERIFIED + Accepted = alert+cron LAND 시 즉시 transition. frontmatter 전환 = PR-2 (실 LAND 후, false-Accepted 차단)"}
  Q7: {chosen: B, decision: "EPIC POLICY_FINALIZED = MCT-193 sub-3 박제 (3/3 + ADR-033 Accepted). Epic CLOSED = production evidence carry 별 PR (docker-stack/tier-promotion/data-domain-decoupling 패턴)"}
  Q8: {chosen: A, decision: "2 PR — PR-1 Phase 1 docs / PR-2 alert+cron+박제 통합 (hub 단독 cross-repo 0)"}

mct_193_quad_alert_spec:
  alert_group: "evidence-quad-enforcement (monitoring/prometheus-alerts.yml 신규 group, mctrader-docker-stack sibling, MCT-179 헤더 주석 패턴)"
  ADR-029: {alert: "QuadViolationADR029NoDualWrite", expr: 'absent(mctrader_dual_write_result_total{status="success"}) or increase(mctrader_dual_write_result_total{status="success"}[14d]) == 0', severity: critical, for: "0m", annotation: "ADR-029 quad violation — dual_write success 14d 무증가 (dead-in-prod 의심). production-wired 14d. SSOT=ADR-033 §3.2 / scope_manifest verify_evidence_telemetry_counter_schema.ADR-029"}
  ADR-030: {alert: "QuadViolationADR030NoCollectorTicks", expr: 'absent(mctrader_collector_ticks_total) or increase(mctrader_collector_ticks_total[14d]) == 0', severity: critical, for: "0m", annotation: "ADR-030 quad violation — collector ticks 14d 무증가. Q4=A 14d 단일화 (ADR-033 §4 trading-hot market-open rolling SSOT drift caveat R-1, market-open rolling 후속 carry)"}
  ADR-031: {alert: "(미등록 — Q1=C caveat)", rationale: "dead-in-data (publish_tick caller=0, MCT-192 caller_wired_evidence_caveat). engine MCT-186 cutover 후 별 Story enable. rolling gate 영구 fire 차단 (MCT-179 §D8 8회째). ADR-033 §3.2 traffic_class='test-injected only' 정합"}

mct_193_cron_workflow_spec:
  path: ".github/workflows/quad-evidence-audit.yml"
  precedent: "repo 최초 cron (12 workflow schedule: 0건 — git ls verify)"
  trigger: "on.schedule(cron monthly) + on.workflow_dispatch (Q5=B hybrid, 선례 0 risk → 수동 fallback)"
  logic: "Prometheus HTTP API query (PROMETHEUS_URL env/secret) → ADR-029/030 quad_query 평가 → violation 시 gh issue create (Q3=A) + class taxonomy drift audit row"
  secret_dependency: "PROMETHEUS_URL (미검증 가정 — Phase 2 verify 의무 R-4). 부재 시 graceful skip + warning (hard fail 금지 — MCT-179 D17 graceful skip 패턴)"
  permissions: "issues: write (gh issue create GITHUB_TOKEN 기본 권한)"

mct_193_planned_files:
  PR-1_hub_docs:
    - {path: "docs/stories/MCT-193.md", action: create}
    - {path: "docs/adr/ADR-033-evidence-quad-enforcement-layer.md", action: amend, detail: "§6 VERIFIED amendment box draft + §4 SSOT drift caveat (R-1) + §9.2 sub-3 draft. frontmatter Proposed 유지 (PR-1)"}
    - {path: "scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml", action: amend, detail: "sub-3 정밀화 + mct_193_* 6 블록"}
    - {path: ".codeforge/counters.json", action: amend, detail: "MCT-193 RESERVED → IN_PROGRESS"}
    - {path: "docs/superpowers/specs/2026-05-17-MCT-193-verify-gate-design.md", action: create}
    - {path: "docs/superpowers/plans/2026-05-17-mct-193-verify-gate.md", action: create}
  PR-2_hub_alert_cron_archive:
    - {path: "monitoring/prometheus-alerts.yml", action: amend, detail: "신규 group evidence-quad-enforcement + ADR-029/030 2 alert (absent() or increase()==0). ADR-031 미등록 caveat 주석"}
    - {path: ".github/workflows/quad-evidence-audit.yml", action: create, detail: "repo 최초 cron — schedule+workflow_dispatch + Prometheus HTTP API + gh issue + drift audit + PROMETHEUS_URL graceful skip"}
    - {path: "docs/adr/ADR-033-evidence-quad-enforcement-layer.md", action: amend, detail: "§6 VERIFIED 확정 + §4 caveat 확정 + frontmatter Proposed → Accepted (Q6=A) + §9.2 VERIFIED 2026-05-17"}
    - {path: "docs/stories/MCT-193.md", action: amend, detail: "§8.5 Impl Manifest + §11 LAND timeline 2 PR sha + frontmatter COMPLETED"}
    - {path: ".codeforge/counters.json", action: amend, detail: "MCT-193 IN_PROGRESS → COMPLETED + ADR-033 Proposed → Accepted + EPIC POLICY_FINALIZED + decisions Q1-Q8 정정 (reservation Q7=C stale)"}
    - {path: "docs/retros/RETRO-MCT-193.md", action: create, detail: "FIX Ledger + repo 최초 cron lesson + absent() trap mitigation lesson"}
    - {path: "docs/retros/PMO-AUDIT-MCT-193.md", action: create, detail: "§lane gate + EPIC POLICY_FINALIZED 감사 + KPI 갱신 + EPIC CLOSED prereq registry"}
    - {path: "docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md", action: amend, detail: "§Story-3 + milestone 3/3 + POLICY_FINALIZED + §3.5 PR-3 #TBD→#385 carry 정정 (PMO-AUDIT-MCT-192 §(4)-(a))"}
    - {path: "CLAUDE.md", action: amend, detail: "§EPIC 2/3 → 3/3 POLICY_FINALIZED + EPIC CLOSED prereq registry"}

mct_193_land_order: "PR-1 hub docs (ADR-033 §6 + counter SSOT 선행) → PR-2 alert/cron/박제 (Accepted + POLICY_FINALIZED). single-repo sequential 2 PR"

mct_193_risks:
  - {id: R-1, severity: HIGH, desc: "ADR-033 §3.2 line 104 + §4 line 125 (ADR-030 trading-hot market-open rolling KRX 75h) ↔ Q4=A 14d 단일화 SSOT drift (MCT-179 cross-doc 9회째)", mitigation: "Q4=A = KRX calendar PromQL 구조적 불가. ADR-033 §6 VERIFIED amendment box 에 'Q4=A 14d 단일화 채택, §4 market-open rolling = KRX calendar PromQL 한계 후속 carry' caveat 명시 박제. Q4=A ↔ ADR-033 §4 amendment ↔ alert yaml comment 3-source 1:1 reconcile (PR-1 DesignReview 핵심 gate, MCT-179 c8e4b8e 패턴)"}
  - {id: R-2, severity: HIGH, desc: "ADR-031 dead-in-data alert 영구 fire (MCT-179 §D8 가공 metric 8회째)", mitigation: "Q1=C ADR-031 alert 미등록 + caveat. ADR-033 §3.2 traffic_class='test-injected only' + caller_wired_evidence_caveat 정합. engine MCT-186 cutover 후 별 Story enable"}
  - {id: R-3, severity: MEDIUM, desc: "absent() trap — production counter 배포 직후 series 미존재 false-positive", mitigation: "Q2=A absent() never-emitted 의도. Q3=A cron primary carrier → false-positive 영향 = cron issue 한정 (alert page 아님). 배포 grace caveat 박제 (RETRO lesson)"}
  - {id: R-4, severity: MEDIUM, desc: "PROMETHEUS_URL secret 미검증 (repo 최초 cron HTTP API 접근성)", mitigation: "Phase 2 verify 의무 (gh secret list). 부재 시 graceful skip (MCT-179 D17 패턴). Q5=B workflow_dispatch fallback. secret 등록 = EPIC CLOSED prereq carry"}
  - {id: R-5, severity: MEDIUM, desc: "repo 최초 cron 선례 0 (12 workflow schedule: 0건)", mitigation: "Q5=B schedule+workflow_dispatch 병행 수동 검증 path. permissions issues:write 명시. Phase 2 workflow_dispatch dry-run 의무"}
  - {id: R-6, severity: LOW, desc: "박제 PR incomplete (MCT-184 3호)", mitigation: "pr_completeness_checklist PR-2 9 항목 전수. EPIC-RESULTS §3.5 #TBD→#385 carry 정정 = MCT-192 carry 흡수"}

mct_193_pr_completeness_checklist:
  PR-1: ["Story MCT-193.md §1-§12 + §8 Test Contract", "ADR-033 §6 VERIFIED draft + §4 R-1 caveat amend (status Proposed 유지)", "scope_manifest sub-3 + mct_193_* 6 블록", "counters MCT-193 IN_PROGRESS", "spec + plan", "DesignReview PASS (R-1 3-source 1:1 reconcile gate)"]
  PR-2: ["prometheus-alerts.yml 신규 group + ADR-029/030 2 alert (absent() or increase()==0)", "quad-evidence-audit.yml 신규 cron (repo 최초)", "ADR-033 §6 VERIFIED 확정 + §4 caveat + frontmatter Accepted + §9.2 VERIFIED", "Story §8.5 + §11 2 PR sha + COMPLETED", "counters COMPLETED + ADR-033 Accepted + EPIC POLICY_FINALIZED + decisions Q1-Q8 정정", "RETRO + PMO-AUDIT + EPIC-RESULTS §Story-3 milestone 3/3", "EPIC-RESULTS §3.5 PR-3 #TBD→#385 carry 정정", "CLAUDE.md §EPIC 3/3 POLICY_FINALIZED + CLOSED prereq", "yaml lint + workflow syntax CodeReview PASS", "gate:retro-complete label"]

mct_193_next: "MCT-193 LAND → EPIC POLICY_FINALIZED (3/3). EPIC CLOSED = production evidence (alert 실 fire + cron 실 issue) carry 별 PR. ADR-031 production caller-wired = engine MCT-186 cutover 후 별 Story (caveat resolve)"
```

## §7 다음 lane = superpowers:writing-plans

1. `superpowers:writing-plans` → plan (`docs/superpowers/plans/2026-05-17-mct-193-verify-gate.md`)
2. 2 PR sequential: PR-1 hub docs → PR-2 alert/cron/박제 (single-repo)
3. post-merge — ADR-033 Accepted + EPIC POLICY_FINALIZED + EPIC-RESULTS §3.5 #385 carry + PMO retro

worktree = mct-193-verify-gate (hub 단독, cross-repo 0). trust-but-verify lesson reapply (Orchestrator 직접 verify SSOT, PMOAgent verify-via 전수 효과 — MCT-192 R1 false premise 동형 재발 0).
