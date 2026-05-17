---
type: brainstorm-spec
story_key: MCT-192
epic_key: EPIC-evidence-quad-runtime-telemetry
title: "Cross-repo telemetry counter emit — ADR-029/030/031 quad evidence (기존 2 재사용 + realtime_stream 1 신규 emit, engine DROP)"
repo: "mctrader-hub + mctrader-data"
phase_pair: phase1_phase2
sequential_phase: 2
status: IN_PROGRESS
parent_dependency: "MCT-191 (EPIC sub-1, ADR-033 §2 quad rule + §7 grandfathering LAND, hub#382/#383)"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-192-telemetry-emit"
worktree_branch: worktree-mct-192-telemetry-emit
created_at: "2026-05-17"
author: Orchestrator (codeforge:brainstorm Phase 1 산출)
phase_0_agents:
  - DomainAgent (a9b6dd4653ec9275d)
  - ResearcherAgent (af4cc9cb5341cacf7) — cross-repo verify
  - RequirementsAnalystAgent (a8c5ef8a7608313e5)
  - PMOAgent_phase0 (a263e6731ed81f9fe)
  - PMOAgent_phase2 (a0a87af804302a1c1) — R1 false premise 기각, D3/D4/D5/D6 채택
codex_dispatch: 9_decision_points_burst (Q1-Q9, 9/9 정합 deviation 0)
verified_sources:
  - "worktree HEAD = 25fc1c4 (#383) + 1cde1ff (#382) — MCT-191 LAND 완전 반영 (직접 git verify)"
  - "docs/adr/ADR-033-evidence-quad-enforcement-layer.md (210L 존재 — PMOAgent R1 'ADR-033 부재' = false premise, 직접 ls verify)"
  - "mctrader-data compactor/runner.py:285 dual_write_result_total.labels(status,tier).inc() (ADR-029 anchor, git grep verified)"
  - "mctrader-data nas_metrics/prometheus_exporters.py:45-46 = Counter('mctrader_dual_write_result_total') (실 Prometheus name)"
  - "mctrader-data metrics.py:9-10 collector_ticks_total = Counter('mctrader_collector_ticks_total') + collector.py:189 record_collector_tick (ADR-030 anchor)"
  - "mctrader-data api/realtime_stream.py:147 _emit_failure_counter() no-op stub + line 145 publish_tick 호출 (ADR-031 신규 emit anchor)"
  - "mctrader-data api/realtime_stream.py publish_tick producer caller src/ 0건 (dead-in-data 정합, ResearcherAgent verified)"
---

# MCT-192 — Cross-repo telemetry counter emit brainstorm spec

> EPIC-evidence-quad-runtime-telemetry sub-2. ADR-033 §2 quad v2 4번째 게이트 runtime telemetry
> counter 실 emit. cross-repo = hub + data (engine DROP — Phase 0 verify 정합).

## §1 Trigger — ADR-033 §9.1 sub-2 (MCT-191 LAND 후)

### 1.1 사용자 요구사항
"다음 작업 진행" + PMO-AUDIT-MCT-191 권고 P1 = MCT-192 (sub-2 cross-repo telemetry counter emit).

### 1.2 Phase 0 verify 핵심 (실측 — PMOAgent R1 false premise 기각 포함)

| # | 사실 | verified-via | 판정 |
|---|------|-------------|------|
| V1 | worktree base = origin/main fresh (HEAD 25fc1c4 #383 + 1cde1ff #382) = MCT-191 LAND 완전 반영 | 직접 `git log` | ✓ |
| V2 | ADR-033 (210L) + EPIC scope_manifest + MCT-191 Story/PMO-AUDIT/RETRO + counters MCT-191~193 entry **전부 존재** | 직접 `ls`/`grep` | ✓ — **PMOAgent 2nd pass R1 "ADR-033/scope_manifest 부재 BLOCKER" = false premise (잘못된 path verify, trust-but-verify 동형 재발). Case A/B 분기 기각** |
| D3 | ADR-029 counter = `mctrader_dual_write_result_total{status,tier}` (정의 `prometheus_exporters.py:45-46` + emit caller `compactor/runner.py:285`) — DESIGN `dual_write_result_total`(no prefix)+dual_writer.py:420 anchor 오기 | `git grep` mctrader-data | ✓ 정정 valid (채택) |
| D4 | ADR-030 counter = `mctrader_collector_ticks_total{exchange,symbol}` (정의 `metrics.py:9-10` + caller `collector.py:189 record_collector_tick`) | `git grep` | ✓ 정정 valid (채택) |
| D5 | ADR-031 counter = `mctrader_data_redis_stream_publish_failures_total` realtime_stream.py:147 `_emit_failure_counter()` no-op stub (line 145 publish_tick 호출) | `git grep` | ✓ 정정 valid (채택) |
| D6 | realtime_stream.py = MCT-185 단일 commit (MCT-186 미변경) → MCT-192 carry 정합 (충돌 아님). 코드 주석 `MCT-186 owner` → MCT-192 정정 의무 | `git log` | ✓ 정합 확정 |
| ED | engine telemetry zero = MCT-185 pure consumer cutover 정합 (publish_tick producer caller 0 = dead-in-data). ADR-031 quad = data realtime producer counter | ResearcherAgent verified | ✓ engine DROP PASS |

**trust-but-verify 동형 재발 (MCT-190 Lesson 5 / plugin-codeforge#822)**: PMOAgent 2nd pass 가 R1 CRITICAL BLOCKER (ADR-033/scope_manifest/Story 부재) 보고 — 실제로는 worktree 에 전부 존재 (잘못된 path verify 추정, main repo stale 혼동). Orchestrator 직접 `ls`/`grep` verify 로 false premise 기각. **plugin-codeforge#822 self-discipline gate v1 = subagent verify report 의무 적용에도 PMOAgent path 오류 발생 → escalate evidence row 추가 후보 (RETRO §Lesson 박제 의무)**. 단 D3/D4/D5/D6 + engine drop 은 valid (실 code 실측 기반, Orchestrator 재verify confirmed).

## §2 핵심 결정 (Codex 9 결정점 일괄 dispatch + Claude 합성, 9/9 정합 deviation 0)

| Q | 결정점 | 채택 | 결과 |
|---|--------|------|------|
| Q1 | ADR-029 counter | A | 기존 `mctrader_dual_write_result_total{status,tier}` 재사용 (runner.py:285 MCT-189 LAND, 신규 emit code 0) |
| Q2 | counter granularity | A | ADR 전체 1 counter (ADR-029=1 / ADR-030=1 / ADR-031=1) |
| Q3 | ADR-031 engine scope | C | engine telemetry zero 정상 (pure consumer). ADR-031 quad = data `realtime_stream` producer counter. **engine 변경 0** |
| Q4 | land_order | A | hub Phase1 docs (counter name SSOT) → data Phase2 PR1 emit → hub Phase2 PR2 박제 (MCT-185 류 2-repo, engine drop) |
| Q5 | mapping SSOT | C | scope_manifest verify_evidence.telemetry_counter field (실행 SSOT) + ADR-033 §본문 mapping table (governance reference, drift 시 scope_manifest 우선) |
| Q6 | ADR-029 cardinality | C | 기존 counter 유지 + quad query filter (`increase(mctrader_dual_write_result_total{status="success"}[14d]) >= 1`). emit code 0 변경, bounded label {status,tier} |
| Q7 | triad reapply 범위 | B | 기존 재사용 (ADR-029 runner.py:285 / ADR-030 collector.py:189) = MCT-189/179 LAND evidence 재인용. **신규 emit (ADR-031 realtime_stream) 만 새 triad v1** |
| Q8 | MCT-192↔193 boundary | C | MCT-192 = emit + 단발성 integration test 실증 (counter ≥1 1회) / MCT-193 = over N days rolling + alert rule + monthly PMO audit (sub-3) |
| Q9 | realtime_stream TODO | A | MCT-192 가 `realtime_stream.py:147-154` `_emit_failure_counter()` no-op stub 해소 (실 `.inc()`, ADR-031 anchor) + 코드 주석 MCT-186→MCT-192 정정 |

## §3 Phase 0 agent 산출 합성

### 3.1 DomainAgent
quad v2 = Counter ≥1 over Nd AND triad v1, `increase(counter[Nd]) >= 1` semantic. Prometheus Counter 강제 (Gauge 금지). per-ADR counter mapping SSOT 부재 → Q5=C scope_manifest field + ADR-033 §본문 reference.

### 3.2 ResearcherAgent (cross-repo verify — 가장 critical)
data `dual_write_result_total{status,tier}` ADR-029 실 emit 존재 (재사용) / engine `data_client`/`realtime`/`cold reader` counter 0, prometheus import 0 (ADR-031 cutover 무계측 정상) / data `realtime_stream.py` counter docstring TODO only (실 .inc() 부재). Unknown: engine telemetry zero (ADR-031 = data producer) / land_order hub-first.

### 3.3 RequirementsAnalystAgent
WHY = MCT-189 caller-wired 부재 + MCT-184 runtime-observed 부재 차단 실 wiring. 5 AC + E1 counter dead path + **E2 cardinality 폭발** (bounded label {status,tier} 로 차단). counter granularity 불일치 → Q2=A ADR 전체 1 counter.

### 3.4 PMOAgent
1 Story cross-repo 3 PR sequential (MCT-185 축소 동형, engine drop). R1 BLOCKER = false premise 기각 (V2 verified). D3/D4/D5/D6 anchor 정정 valid 채택. R2 = MCT-179 §D8 가공 metric 7회째 (realtime_stream dead-in-data caveat 정직 박제로 차단).

## §4 AC (5종)

- **AC-1**: ADR-029 quad evidence — scope_manifest verify_evidence.telemetry_counter 박제 (`mctrader_dual_write_result_total{status,tier}` + quad_query `increase(...{status="success"}[14d]) >= 1` + emit_location `compactor/runner.py:285` + triad_v1_evidence "MCT-189 재인용"). 신규 emit code 0.
- **AC-2**: ADR-030 quad evidence — scope_manifest 박제 (`mctrader_collector_ticks_total{exchange,symbol}` + emit_location `collector.py:189 record_collector_tick` + triad "MCT-179/180 재인용"). 신규 emit code 0.
- **AC-3**: ADR-031 quad evidence — data `realtime_stream.py:147-154` `_emit_failure_counter()` no-op stub → 실 `mctrader_data_redis_stream_publish_failures_total` Counter `.inc()` emit + Counter 정의. counter-emit triad v1 reapply (file:line + caller grep + integration test PASS, Q7=B 신규 emit = 새 triad). 코드 주석 `MCT-186 owner` → `MCT-192` 정정.
- **AC-4**: ADR-031 dead-in-data 정직 박제 — `publish_tick` producer caller src/ 0건 → scope_manifest `traffic_class: "test-injected only"` + `caller_wired_evidence_caveat` 명시 (R2 가공 metric 7회째 차단, MCT-179 §D8 lesson). production caller-wired = MCT-186 engine cutover 후 또는 MCT-193 rolling gate prerequisite.
- **AC-5**: ADR-033 §본문 per-ADR counter mapping table amend (Q5=C governance 중앙 reference) + §9.1 sub-2 LAND confirm (PR-3 박제). scope_manifest ↔ ADR-033 mapping table ↔ Q1-Q9 1:1 reconcile (R4, MCT-179 lesson).

## §5 INV (3종)

- **INV-1**: 기존 counter 재사용 (ADR-029/030) = emit code 0 변경 (production runtime untouched). 신규 emit = ADR-031 realtime_stream 1곳만.
- **INV-2**: counter-emit triad v1 reapply (Q5=C ADR-033 meta-recursion 1단) — ADR-031 신규 emit code = (file:line + caller grep ≥1 + integration test PASS). counter-of-counter 미적용.
- **INV-3**: engine 변경 0 (ADR-031 pure consumer telemetry zero 정상, ED verified). cross-repo = hub + data.

## §6 scope_manifest (PMOAgent 2nd pass 산출 — R1 false premise 기각 + D3/D4/D5 정정 반영)

> EPIC-evidence-quad-runtime-telemetry.yaml = **존재** (worktree V2 verified, PMOAgent "부재" = false). MCT-192 = sub-2 **amend** (Case B "create" 기각 — MCT-191 sub-1 LAND 완료).

```yaml
# scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml amend (sub-2 MCT-192)
epic_key: EPIC-evidence-quad-runtime-telemetry
milestone: "2/3 (MCT-192 LAND 후, post-merge)"

sub_stories:
  - {key: MCT-191, seq: 1, status: COMPLETED, land: "hub#382/#383"}
  - {key: MCT-192, seq: 2, status: IN_PROGRESS, repo: "mctrader-hub + mctrader-data (engine DROP)", depends_on: [MCT-191],
     decisions: ["Q1-A","Q2-A","Q3-C","Q4-A","Q5-C","Q6-C","Q7-B","Q8-C","Q9-A"]}
  - {key: MCT-193, seq: 3, status: RESERVED, scope: "over-Nd rolling + alert rule + monthly PMO audit (Q8=C boundary)"}

verify_evidence_telemetry_counter_schema:
  ADR-029:
    counter: "mctrader_dual_write_result_total"
    labels: "{status, tier}"
    quad_query: 'increase(mctrader_dual_write_result_total{status="success"}[14d]) >= 1'
    definition_location: "mctrader-data src/mctrader_data/nas_metrics/prometheus_exporters.py:45-46"
    emit_location: "mctrader-data src/mctrader_data/compactor/runner.py:285 (MCT-189 LAND 재사용, 신규 emit code 0)"
    traffic_class: "production-wired 14d (MCT-189 grace-0 wiring LAND, 실 caller-wired)"
    triad_v1_evidence: "MCT-189 evidence 재인용 (Q7=B — 기존 counter, 신규 triad 미발급)"
  ADR-030:
    counter: "mctrader_collector_ticks_total"
    labels: "{exchange, symbol}"
    quad_query: 'increase(mctrader_collector_ticks_total[14d]) >= 1'
    definition_location: "mctrader-data src/mctrader_data/metrics.py:9-13"
    emit_location: "mctrader-data src/mctrader_data/collector.py:189 record_collector_tick() (MCT-180/179 LAND 재사용, 신규 emit code 0)"
    traffic_class: "trading-hot market-open rolling (collector daemon production-wired)"
    triad_v1_evidence: "MCT-180/179 evidence 재인용 (Q7=B)"
  ADR-031:
    counter: "mctrader_data_redis_stream_publish_failures_total"
    labels: "[]"
    quad_query: 'increase(mctrader_data_redis_stream_publish_failures_total[14d]) >= 0'
    definition_location: "mctrader-data src/mctrader_data/api/realtime_stream.py (MCT-192 PR-2 신규 Counter 정의)"
    emit_location: "mctrader-data src/mctrader_data/api/realtime_stream.py:147-154 _emit_failure_counter() (MCT-192 신규 emit, no-op stub 해소)"
    traffic_class: "test-injected only (publish_tick producer caller=0 src/ grep verified, dead-in-data — Q8=C MCT-192 단발성 실증, production rolling=MCT-193 sub-3)"
    triad_v1_evidence: "MCT-192 신규 triad v1 (Q7=B — file:line + caller grep ≥1 + integration test PASS)"
    caller_wired_evidence_caveat: "dead-in-data — publish_tick producer caller=0 (src grep verified). engine subscriber=ADR-031 consumer (telemetry zero 정상). production caller-wired = MCT-186 engine cutover 후 또는 MCT-193 rolling gate prerequisite"

planned_files:
  mctrader-hub:
    - {path: "docs/stories/MCT-192.md", action: create}
    - {path: "docs/adr/ADR-033-evidence-quad-enforcement-layer.md", action: amend, detail: "§본문 per-ADR counter mapping table 추가 (Q5=C) + §9.1 sub-2 LAND confirm draft"}
    - {path: "scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml", action: amend, detail: "sub-2 MCT-192 정밀화 + verify_evidence_telemetry_counter_schema 3 ADR"}
    - {path: ".codeforge/counters.json", action: amend, detail: "MCT-192 RESERVED → IN_PROGRESS → COMPLETED"}
    - {path: "docs/retros/RETRO-MCT-192.md", action: create, detail: "PR-3, trust-but-verify 동형 재발 Lesson 박제"}
    - {path: "docs/retros/PMO-AUDIT-MCT-192.md", action: create, detail: "PR-3, §lane gate + R1 false premise 기각 박제"}
    - {path: "docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md", action: amend, detail: "§Story-2 milestone 2/3"}
    - {path: "CLAUDE.md", action: amend, detail: "§EPIC milestone 1/3 → 2/3 (PR-3 post-merge)"}
  mctrader-data:
    - {path: "src/mctrader_data/api/realtime_stream.py", action: modify, detail: "PR-2: _emit_failure_counter() no-op(line 147-154) → 실 Counter .inc() + Counter 정의 + 주석 MCT-186→MCT-192 정정"}
    - {path: "tests/api/test_realtime_stream_counter.py", action: create, detail: "PR-2 신규: XADD fail inject → counter ≥1 단발성 (Q8=C boundary)"}

planned_adrs:
  - {adr: ADR-033, action: amend, detail: "§본문 mapping table + §9.1 sub-2 VERIFIED"}

land_order: "PR-1 hub docs → PR-2 data emit → PR-3 hub 박제 (MCT-185 류 2-repo sequential, engine drop)"

risks:
  - {id: R1, severity: RESOLVED, desc: "PMOAgent 2nd pass 'ADR-033/scope_manifest 부재 BLOCKER'", mitigation: "Orchestrator 직접 ls/grep verify = false premise 기각 (worktree V2 전부 존재). MCT-191 sub-1 LAND 완료, MCT-192 = sub-2 정상 진입. trust-but-verify 동형 재발 = RETRO Lesson 박제"}
  - {id: R2, severity: HIGH, desc: "MCT-179 §D8 가공 metric 7회째 — ADR-031 realtime_stream publish_tick caller=0 dead-in-data", mitigation: "Q1/Q7 기존 counter 재사용 (신규 emit ADR-031 1곳만) + scope_manifest traffic_class 'test-injected only' + caller_wired_evidence_caveat 정직 박제. PR-2 Phase 0 verify (producer caller grep) gate 의무"}
  - {id: R3, severity: LOW, desc: "realtime_stream 코드 주석 MCT-186 owner vs MCT-192 Q9=A", mitigation: "git log = MCT-185 단일 commit (MCT-186 미변경) → carry 정합 확정 (충돌 아님). PR-2가 주석 MCT-186→MCT-192 정정"}
  - {id: R4, severity: MEDIUM, desc: "cross-document SSOT (ADR-033 mapping ↔ scope_manifest ↔ Q1-Q9) drift (MCT-179 lesson)", mitigation: "Q5=C drift 시 scope_manifest 우선. PR-1 DesignReview 1:1 byte reconcile gate"}
  - {id: R5, severity: MEDIUM, desc: "박제 PR incomplete (MCT-184 SSOT drift 3호)", mitigation: "pr_completeness_checklist 전수 LAND. PMO-AUDIT-MCT-192 §lane gate"}

pr_completeness_checklist:
  PR-1_hub_docs: ["Story MCT-192.md create", "ADR-033 §본문 mapping table + §9.1 draft amend", "scope_manifest sub-2 + verify_evidence 3 ADR amend", "counters MCT-192 IN_PROGRESS", "DesignReview PASS gate"]
  PR-2_data_code: ["realtime_stream.py _emit_failure_counter no-op → .inc() + Counter 정의", "주석 MCT-186→MCT-192 정정", "counter-emit triad v1 (file:line+caller grep+integration test)", "tests/api/test_realtime_stream_counter.py create", "회귀 0", "CodeReview PASS gate"]
  PR-3_hub_archive: ["Story §8.5 Impl Manifest (3 ADR quad evidence)", "§11 LAND timeline 3 PR sha", "RETRO-MCT-192 (trust-but-verify Lesson)", "PMO-AUDIT-MCT-192 (R1 false premise 기각)", "EPIC-RESULTS §Story-2 milestone 2/3", "counters COMPLETED", "ADR-033 §9.1 VERIFIED", "CLAUDE.md §EPIC 2/3", "gate:retro-complete label"]

next_story: "MCT-193 (sub-3 over-Nd rolling + alert rule + monthly PMO audit) — MCT-192 LAND 후"
```

## §7 다음 lane = superpowers:writing-plans

1. `superpowers:writing-plans` → plan file (`docs/superpowers/plans/2026-05-17-mct-192-telemetry-emit.md`)
2. 3 PR cross-repo sequential implementer (PR-1 hub docs → PR-2 data emit → PR-3 hub 박제)
3. cross-repo PR LAND (data PR = mctrader-data repo, hub PR = mctrader-hub)
4. post-merge + PMO retro 자동 dispatch (memory feedback_pmo_retro_mandatory)

worktree = `mct-192-telemetry-emit` (hub). data 작업 = mctrader-data repo 별 worktree 격리 의무 (memory feedback_parallel_session_branch_race tier-1 hub+data+engine — data 도 tier-1).
