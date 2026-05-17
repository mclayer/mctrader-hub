# MCT-193 — Post-LAND Verify Gate 운영 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. **trust-but-verify 강제 (MCT-190 Lesson 5 / MCT-192 R1 false premise / plugin-codeforge#822 N=3)**: implementer subagent 는 Write/Edit/Create 후 자동 verify report (ls + line/grep + git status). **Orchestrator 는 모든 critical artifact + BLOCKER 보고를 직접 ls/grep 재verify** (PMOAgent verify-via 전수 효과 — MCT-192 R1 false premise 동형 재발 0 유지).

**Goal:** ADR-033 §6 enforcement timing Q7=C 실 carrier — quad violation alert (ADR-029/030) + monthly PMO audit cron + ADR-033 §6 VERIFIED + Proposed→Accepted + EPIC POLICY_FINALIZED 3/3.

**Architecture:** EPIC-evidence-quad-runtime-telemetry sub-3 (마지막). repo = mctrader-hub 단독 (cross-repo 0). 2 PR sequential: PR-1 hub docs (Story + ADR-033 §6/§4 amend + scope_manifest + counters) → PR-2 alert/cron/박제 통합 (prometheus-alerts.yml + 신규 cron workflow + Accepted transition + POLICY_FINALIZED). ADR-031 dead-in-data alert 제외 (Q1=C). market-open rolling = 14d 단일화 (Q4=A, KRX calendar PromQL 불가, R-1 §4 SSOT drift caveat 박제).

**Tech Stack:** Prometheus alert rules YAML (`absent() or increase()==0`), GitHub Action cron workflow (repo 최초 — schedule+workflow_dispatch, Prometheus HTTP API, gh issue create), Markdown/YAML/JSON governance 박제, Git single-repo 2 PR.

**Worktree:** `c:\workspace\mclayer\mctrader-hub\.claude\worktrees\mct-193-verify-gate` (base=origin/main #386 MCT-192 LAND).

**Spec reference:** `docs/superpowers/specs/2026-05-17-MCT-193-verify-gate-design.md` (§6 scope_manifest YAML SSOT — mct_193_* 6 블록)

---

## File Structure

### PR-1 (hub Phase 1 docs)
| F | path | action |
|---|------|--------|
| F1 | `docs/stories/MCT-193.md` | create (~280L §1-§12) |
| F2 | `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` | amend (§6 VERIFIED draft + §4 R-1 SSOT drift caveat + §9.2 sub-3 draft, frontmatter Proposed 유지) |
| F3 | `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` | amend (sub-3 정밀화 + mct_193_* 6 블록) |
| F4 | `.codeforge/counters.json` | amend (MCT-193 RESERVED → IN_PROGRESS) |
| F5 | spec + plan | create (자동 포함) |

### PR-2 (hub Phase 2 alert/cron/박제)
| F | path | action |
|---|------|--------|
| F6 | `monitoring/prometheus-alerts.yml` | amend (신규 group evidence-quad-enforcement + ADR-029/030 2 alert) |
| F7 | `.github/workflows/quad-evidence-audit.yml` | create (repo 최초 cron) |
| F8 | `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` | amend (§6 VERIFIED 확정 + frontmatter Accepted + §9.2 VERIFIED) |
| F9 | `docs/stories/MCT-193.md` | amend (§8.5 + §11 2 PR sha + frontmatter COMPLETED) |
| F10 | `.codeforge/counters.json` | amend (MCT-193 COMPLETED + ADR-033 Accepted + EPIC POLICY_FINALIZED + decisions Q1-Q8 정정) |
| F11 | `docs/retros/RETRO-MCT-193.md` | create |
| F12 | `docs/retros/PMO-AUDIT-MCT-193.md` | create |
| F13 | `docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md` | amend (§Story-3 + milestone 3/3 + POLICY_FINALIZED + §3.5 PR-3 #TBD→#385 carry 정정) |
| F14 | `CLAUDE.md` | amend (§EPIC 2/3 → 3/3 POLICY_FINALIZED + EPIC CLOSED prereq registry) |

---

## Task Decomposition

### PR-1 (hub Phase 1 docs) — land_order 1

#### Task 1: Story MCT-193.md 신규 (F1)

**Files:** Create `docs/stories/MCT-193.md` (~280L)

**Reference:** spec §1-§7 + `docs/stories/MCT-192.md` (선례 hub Story 패턴).

- [ ] **Step 1: frontmatter + §0 Phase 0 Verify Gate**

```yaml
---
key: MCT-193
title: "Post-LAND verify gate 운영 — quad violation alert + monthly PMO audit cron + ADR-033 §6 VERIFIED + EPIC POLICY_FINALIZED 3/3"
status: COMPLETED  # post-LAND 전환
repo: mctrader-hub
phase_pair: phase1_phase2
classification: hub-governance + infra (alert yaml + cron workflow)
epic: EPIC-evidence-quad-runtime-telemetry
sequential_phase: 3
parent_dependency: "MCT-192 (sub-2 LAND hub#384 + data#79 + hub#385 + #386)"
owner_for_adr: "ADR-033 §6 VERIFIED + Proposed → Accepted"
created_at: "2026-05-17"
completed_at: "2026-05-17"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-193-verify-gate"
land_prs:
  - "mctrader-hub#TBD (PR-1 hub docs)"
  - "mctrader-hub#TBD (PR-2 alert/cron/박제)"
---
```

§0 Phase 0 Verify Gate = spec §1.2 table 전수 (V1 worktree base #386 / V2 R1 false premise 동형 재발 0 trust-but-verify lesson reapply / R-1 ADR-033 §4 SSOT drift 9회째 / R-2 ADR-031 dead-in-data §D8 8회째 / infra alertmanager 부재 + repo 최초 cron).

- [ ] **Step 2: §1-§5 (요구사항 + spec/plan cross-ref + AC-1~5 + Q1-Q8 table)**

§1 사용자 요구사항 ("다음 작업 수행하라" + PMO-AUDIT-MCT-192 §(4) P1). §2 spec cross-ref. §3 AC-1~5 (spec §4). §4 plan cross-ref. §5 Q1-Q8 table (Codex 8/8 정합 deviation 0, MCT-191/192 동형 full alignment 연속 3 Story).

- [ ] **Step 3: §6 risks (R-1 HIGH ~ R-6 LOW, spec §6 mct_193_risks) + §7 cross-ref + §8 Test Contract**

§8 Test Contract = doc cross-ref 정합 (alert PromQL syntax + cron yaml lint + R-1 3-source 1:1 reconcile: Q4=A ↔ ADR-033 §4 amendment ↔ alert yaml comment). code = alert/cron infra (production runtime untouched, ADR-031 dead-in-data 제외).

- [ ] **Step 4: §9 cross-Story carry + §10 FIX Ledger placeholder + §11 LAND timeline placeholder + §12 회고 placeholder**

§9 = trust-but-verify lesson reapply 효과 (MCT-192 R1 false premise → PMOAgent verify-via 전수 → MCT-193 동형 재발 0). MCT-179 cross-doc SSOT drift 9회째 (R-1) + §D8 가공 metric 8회째 (R-2). carry = EPIC CLOSED production evidence 별 PR + ADR-031 caller-wired engine MCT-186 cutover 후 별 Story.

- [ ] **Step 5: verify (ls + line ~280 + grep `§0|Q1-Q8|R-1|absent|dead-in-data|POLICY_FINALIZED` + git status). verify report 의무.**

#### Task 2: ADR-033 §6 VERIFIED draft + §4 R-1 SSOT drift caveat amend (F2)

**Files:** Modify `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` (~+25L, amend only — frontmatter Proposed 유지 PR-1)

**Reference:** ADR-033 §3.2 line 103-105 (counter mapping) + §4 line 116-127 (traffic class table — R-1 SSOT drift 대상) + §6 line 147-156 (enforcement timing) + §9.2 (sub-3).

- [ ] **Step 1: §6 enforcement timing VERIFIED amendment box draft 추가**

§6 (line 147-156) 직후 또는 §6 내 amendment box:
```markdown
### §6.1 VERIFIED amendment box (MCT-193 sub-3 carrier, draft — PR-2 확정)

MCT-193 = §6 enforcement timing 실 carrier. PR-1 docs draft → PR-2 alert/cron LAND 후 VERIFIED 확정:
- Prometheus alert rule: monitoring/prometheus-alerts.yml 신규 group `evidence-quad-enforcement` — ADR-029 QuadViolationADR029NoDualWrite + ADR-030 QuadViolationADR030NoCollectorTicks (`absent(<counter>) or increase(<counter>[14d]) == 0` critical, Q2=A absent() trap 차단). ADR-031 = 미등록 (Q1=C dead-in-data caveat — engine MCT-186 cutover 후 별 Story enable, rolling gate 영구 fire 차단)
- GitHub issue 자동 발의 carrier: alertmanager 부재 (prometheus.yml alerting: 라우팅 0) → .github/workflows/quad-evidence-audit.yml 신규 cron (Q3=A — repo 최초 cron, schedule monthly + workflow_dispatch hybrid Q5=B, Prometheus HTTP API query, PROMETHEUS_URL 부재 시 graceful skip)
- monthly PMO audit batch = 동 cron workflow class taxonomy drift audit row

**§4 traffic class SSOT drift caveat (R-1, MCT-179 cross-doc 9회째 mitigation)**: §4 (line 121-127) `trading-hot path (collector tick) = market-open hours rolling (KRX 09:00-15:30 KST ≈ 75h)` 는 **Prometheus PromQL 로 KRX 거래일/공휴일 calendar 표현 구조적 불가**. MCT-193 Q4=A = production-wired **14d calendar 단일화** 채택 (trading-hot collector 도 14d). §4 market-open rolling = **후속 과제 carry** (recording rule + 외부 trading-calendar gate 필요, 별 Story). 본 caveat = §4 ↔ §6 자기모순 차단 (scope_manifest mct_193_decisions.Q4 ↔ 본 §6.1 ↔ alert yaml comment 3-source 1:1 reconcile, PR-1 DesignReview gate).
```

- [ ] **Step 2: §9.2 sub-3 LAND confirm draft**

§9.2 sub-3 (MCT-193) 항목에 "PR-1 docs LAND (§6.1 amendment box draft + scope_manifest mct_193_*). PR-2 alert/cron LAND 후 §6 VERIFIED 확정 + frontmatter Proposed → Accepted + §9.2 VERIFIED 2026-05-17." draft 박제.

- [ ] **Step 3: verify (Read §6.1 + §9.2 + §4 caveat. Grep `§6.1|VERIFIED amendment|SSOT drift caveat|R-1|14d calendar 단일화`. 기존 §1-§10 본문 (frontmatter Proposed 포함) 보존 confirm. git status). verify report 의무 — R-1 3-source reconcile (Q4=A ↔ §6.1 caveat ↔ scope_manifest) 명시.**

#### Task 3: scope_manifest sub-3 amend (F3)

**Files:** Modify `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`

**Reference:** spec §6 YAML (mct_193_* 6 블록: decisions / quad_alert_spec / cron_workflow_spec / planned_files / land_order / risks / pr_completeness_checklist).

- [ ] **Step 1: spec §6 mct_193_* 블록 직접 carry**

spec §6 YAML 의 sub_stories_MCT_193 row + mct_193_decisions (Q1-Q8) + mct_193_quad_alert_spec + mct_193_cron_workflow_spec + mct_193_planned_files + mct_193_land_order + mct_193_risks (R-1~R-6) + mct_193_pr_completeness_checklist 를 기존 scope_manifest 에 amend (sub-1 MCT-191 + sub-2 MCT-192 mct_192_* 보존, MCT-192 패턴 mirror).

- [ ] **Step 2: verify (Read full + YAML lint python yaml.safe_load + Grep `mct_193_decisions|mct_193_quad_alert_spec|R-1|QuadViolationADR029` + 기존 sub-1/sub-2 보존. git status). verify report 의무 (YAML lint 결과).**

#### Task 4: counters.json MCT-193 IN_PROGRESS (F4)

**Files:** Modify `.codeforge/counters.json`

- [ ] **Step 1: MCT-193 entry RESERVED → IN_PROGRESS** + started_at + worktree (기존 title/epic/depends_on/rationale 보존). post-merge PR-2 = COMPLETED + ADR-033 Accepted + EPIC POLICY_FINALIZED + decisions Q1-Q8 정정 (reservation Q7=C stale).

- [ ] **Step 2: verify (python json.load valid + Grep MCT-193 IN_PROGRESS + 기존 MCT-191/192/ADR-033 보존. git status). verify report 의무.**

#### Task PR-1-LAND: hub docs commit + push + PR open + admin merge (Orchestrator direct)

- [ ] git status verify (Orchestrator 직접 — 5 file). **R-1 3-source 1:1 reconcile gate** (Q4=A scope_manifest ↔ ADR-033 §6.1 caveat ↔ §4 market-open rolling 정합 직접 grep verify, MCT-192 R1 false premise 동형 차단).
- [ ] message file commit + push + PR open (body file) + CI status + admin merge. PR# 기록 (PR-2 입력).

---

### PR-2 (hub Phase 2 alert/cron/박제) — land_order 2

> **PR-1 MERGED 후 진입** (ADR-033 §6 + counter SSOT 박제 후).

#### Task 5: prometheus-alerts.yml quad alert group (F6)

**Files:** Modify `monitoring/prometheus-alerts.yml` (신규 group, MCT-179/180 패턴 정합)

**Reference (verified):** 기존 `groups: - name: mctrader-docker-stack rules:` (WALCapacity/NASReader/ContainerMemory 5 alert, `increase()` 패턴, line 1-4 SSOT 주석 헤더).

- [ ] **Step 1: 신규 group `evidence-quad-enforcement` 추가 (mctrader-docker-stack sibling)**

```yaml
  - name: evidence-quad-enforcement
    # MCT-193 sub-3 — ADR-033 §6 enforcement timing Q7=C carrier
    # SSOT = ADR-033 §3.2 per-ADR counter mapping + scope_manifest verify_evidence_telemetry_counter_schema
    # ADR-031 미등록 (Q1=C dead-in-data caveat — publish_tick caller=0, engine MCT-186 cutover 후 별 Story enable, rolling gate 영구 fire 차단)
    # Q4=A 14d calendar 단일화 (KRX calendar PromQL 불가, ADR-033 §6.1 R-1 caveat — market-open rolling 후속 carry)
    rules:
      - alert: QuadViolationADR029NoDualWrite
        expr: 'absent(mctrader_dual_write_result_total{status="success"}) or increase(mctrader_dual_write_result_total{status="success"}[14d]) == 0'
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "ADR-029 quad violation — dual_write success counter 14d 무증가 (dead-in-prod false-negative 의심)"
          description: "mctrader_dual_write_result_total{status=success} 14d increase==0 또는 series 부재 (absent). ADR-029 production-wired 14d. SSOT=ADR-033 §3.2 / scope_manifest verify_evidence_telemetry_counter_schema.ADR-029. quad 4번째 게이트 (runtime telemetry) 위반 — caller-wired LAND 됐으나 production traffic 0 (Hyrum's Law 역방향)."
      - alert: QuadViolationADR030NoCollectorTicks
        expr: 'absent(mctrader_collector_ticks_total) or increase(mctrader_collector_ticks_total[14d]) == 0'
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "ADR-030 quad violation — collector ticks counter 14d 무증가"
          description: "mctrader_collector_ticks_total 14d increase==0 또는 series 부재. ADR-030 Q4=A 14d calendar 단일화 (ADR-033 §6.1 R-1 caveat — §4 trading-hot market-open rolling 은 KRX calendar PromQL 한계로 후속 carry). SSOT=ADR-033 §3.2."
```

- [ ] **Step 2: verify (Read amended group. yamllint 또는 `python -c "import yaml; yaml.safe_load(open('monitoring/prometheus-alerts.yml'))"` PASS. Grep `evidence-quad-enforcement|QuadViolationADR029|QuadViolationADR030|absent(`. 기존 mctrader-docker-stack group 보존 confirm. git status). verify report 의무 (yaml lint + 기존 group 보존).**

#### Task 6: quad-evidence-audit.yml cron workflow 신규 (F7, repo 최초 cron)

**Files:** Create `.github/workflows/quad-evidence-audit.yml`

**Reference (verified):** `.github/workflows/` 12개 전수 schedule:/cron: 선례 0 (repo 최초). 기존 workflow 패턴 (gh CLI 사용, GITHUB_TOKEN). prometheus.yml alerting: 부재 (ResearcherAgent verified).

- [ ] **Step 1: cron workflow 작성 (Q3=A + Q5=B)**

```yaml
name: Quad Evidence Audit (monthly)
# MCT-193 sub-3 — ADR-033 §6 enforcement timing Q7=C carrier (repo 최초 cron workflow)
# Q3=A: alertmanager 부재 → GitHub Action cron 이 Prometheus HTTP API query → quad violation gh issue create
# Q5=B: schedule(monthly) + workflow_dispatch hybrid (정상 silent / violation·drift 자동 issue, 선례 0 risk → 수동 fallback)

on:
  schedule:
    - cron: '0 2 1 * *'   # monthly 1일 02:00 UTC
  workflow_dispatch: {}

permissions:
  issues: write
  contents: read

jobs:
  quad-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Quad evidence audit (ADR-029/030 production-wired)
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROMETHEUS_URL: ${{ secrets.PROMETHEUS_URL }}
        run: |
          set -euo pipefail
          if [ -z "${PROMETHEUS_URL:-}" ]; then
            echo "::warning::PROMETHEUS_URL secret 미설정 — quad evidence audit graceful skip (MCT-179 D17 graceful skip 패턴 정합, hard fail 금지). secret 등록 = EPIC CLOSED prereq carry."
            exit 0
          fi
          violations=""
          for q in \
            'ADR-029|mctrader_dual_write_result_total{status="success"}|increase(mctrader_dual_write_result_total{status="success"}[14d])' \
            'ADR-030|mctrader_collector_ticks_total|increase(mctrader_collector_ticks_total[14d])'; do
            adr="${q%%|*}"; rest="${q#*|}"; counter="${rest%%|*}"; expr="${rest##*|}"
            # absent() or increase()==0 quad violation 판정 (Q2=A)
            result=$(curl -sf --get "${PROMETHEUS_URL}/api/v1/query" --data-urlencode "query=${expr}" || echo '{"data":{"result":[]}}')
            n=$(echo "$result" | python -c "import sys,json; d=json.load(sys.stdin); rs=d.get('data',{}).get('result',[]); print(0 if not rs else float(rs[0]['value'][1]))" 2>/dev/null || echo "absent")
            if [ "$n" = "absent" ] || [ "$n" = "0" ] || [ "$n" = "0.0" ]; then
              violations="${violations}\n- **${adr}** quad violation: \`${counter}\` 14d increase==0 또는 series 부재 (absent). dead-in-prod false-negative 의심 (Hyrum's Law 역방향)."
            fi
          done
          if [ -n "$violations" ]; then
            title="[quad-violation] ADR-029/030 evidence quad gate 위반 ($(date -u +%Y-%m))"
            body=$(printf "## Quad Evidence Audit 위반 (monthly cron)\n\nADR-033 §6 enforcement timing Q7=C — production-wired ADR quad 4번째 게이트 (runtime telemetry counter ≥1 over 14d) 위반 감지.\n%b\n\n### 처리\n- caller-wired LAND 됐으나 production traffic 0 = MCT-189 130GB (decision-defined ≠ caller-wired) 동형 risk\n- ADR-031 = dead-in-data 제외 (Q1=C, engine MCT-186 cutover 후 별 Story)\n- SSOT: ADR-033 §3.2 / scope_manifest verify_evidence_telemetry_counter_schema\n\n🤖 quad-evidence-audit.yml (MCT-193 sub-3 cron)" "$violations")
            gh issue create --title "$title" --body "$body" --label "quad-violation" 2>&1 || echo "::warning::gh issue create 실패 (label quad-violation 부재 가능 — 수동 확인)"
          else
            echo "quad evidence audit PASS — ADR-029/030 production-wired counter 14d increase>=1 (위반 0)"
          fi
```

- [ ] **Step 2: verify (Read full. yamllint 또는 actionlint syntax. Grep `schedule:|cron:|workflow_dispatch|PROMETHEUS_URL|graceful skip|gh issue create`. git status). verify report 의무 (workflow syntax + repo 최초 cron 명시).**

#### Task 7: ADR-033 Accepted + Story §8.5/§11 + counters COMPLETED + EPIC POLICY_FINALIZED (F8/F9/F10/F13/F14)

- [ ] **Step 1: ADR-033 §6 VERIFIED 확정 + frontmatter Proposed → Accepted + §9.2 VERIFIED**

§6.1 amendment box draft → VERIFIED 확정 (PR-2 alert/cron LAND 사실: prometheus-alerts.yml `evidence-quad-enforcement` group + quad-evidence-audit.yml cron). frontmatter `status: Proposed` → `Accepted` (Q6=A 구현 LAND = transition). §9.2 sub-3 → VERIFIED 2026-05-17. 기존 §1-§10 본문 보존 (amend only).

- [ ] **Step 2: Story §8.5 Impl Manifest + §11 LAND timeline + frontmatter COMPLETED**

§8.5 = alert yaml (prometheus-alerts.yml:line evidence-quad-enforcement) + cron workflow (quad-evidence-audit.yml) file:line 박제 + ADR-033 §6 VERIFIED cross-ref. §11 LAND timeline 2 PR (#TBD → 실 PR# + sha, post-merge). ADR-031 dead-in-data 제외 정직 박제 (Q1=C, engine MCT-186 cutover 후 별 Story).

- [ ] **Step 3: counters.json MCT-193 COMPLETED + ADR-033 Accepted + EPIC POLICY_FINALIZED + decisions Q1-Q8 정정**

MCT-193 = COMPLETED + completed_at + land_prs 2 PR + epic_milestone 3/3. ADR-033 entry status Proposed → Accepted. EPIC POLICY_FINALIZED. MCT-193 decisions Q7=C → Q1-Q8 정정 (reservation stale).

- [ ] **Step 4: EPIC-RESULTS §Story-3 + milestone 3/3 + POLICY_FINALIZED + §3.5 PR-3 #TBD→#385 carry 정정 + CLAUDE.md §EPIC 3/3**

EPIC-RESULTS §Story-3 (MCT-193) 추가 + frontmatter milestone 2/3 → 3/3 + POLICY_FINALIZED + **§3.5 PR-3 row #TBD → #385 (1b4a727) carry 정정 (PMO-AUDIT-MCT-192 §(4)-(a) piggyback)**. CLAUDE.md §EPIC-evidence-quad-runtime-telemetry milestone 2/3 → 3/3 POLICY_FINALIZED + EPIC CLOSED prereq registry (production evidence: alert 실 fire + cron 실 issue 발의 carry 별 PR). 기존 §Story-1/§Story-2 + MCT-191/192 보존.

- [ ] **Step 5: verify (각 file Read + Grep `Accepted|POLICY_FINALIZED|§Story-3|milestone.*3/3|#385` + 기존 본문 보존 (ADR-033 §1-§10 / EPIC-RESULTS §Story-1/2 / CLAUDE.md MCT-191/192). counters JSON valid. git status). verify report 의무.**

#### Task 8: RETRO-MCT-193 + PMO-AUDIT-MCT-193 (F11/F12) — parallel subagent

- [ ] **RETRO-MCT-193.md** (~180L, CFP-138/ADR-045 4-field) — Lessons: (A) trust-but-verify lesson reapply 효과 (MCT-192 R1 false premise → PMOAgent verify-via 전수 → MCT-193 동형 재발 0) (B) repo 최초 cron workflow (선례 0, Q5=B workflow_dispatch hybrid risk mitigation) (C) absent() trap mitigation (Q2=A) (D) R-1 ADR-033 §4 SSOT drift 9회째 (Q4=A 14d 단일화 + §6.1 caveat 박제, MCT-179 c8e4b8e 패턴 reapply) + EPIC POLICY_FINALIZED 3/3 완결.

- [ ] **PMO-AUDIT-MCT-193.md** (~250L) — §lane gate 전수 + EPIC POLICY_FINALIZED 감사 (3 sub-Story MCT-191/192/193 완결) + cross-Story KPI 갱신 (Codex deviation 0 연속 3 Story / trust-but-verify 동형 MCT-192 1회 → MCT-193 0회 PMOAgent verify-via 전수 효과 / cross-doc SSOT drift 9회째 R-1) + EPIC CLOSED prereq registry (production evidence carry 별 PR) + ADR-031 caller-wired engine MCT-186 후 별 Story carry.

#### Task PR-2-LAND: alert/cron/박제 commit + push + PR open + admin merge + gate:retro-complete + PMO retro (Orchestrator direct)

- [ ] Orchestrator git status verify (직접 — 9 file). critical artifact (ADR-033 Accepted / prometheus-alerts.yml / cron workflow / EPIC-RESULTS POLICY_FINALIZED) ls/grep verify.
- [ ] message file commit + push + PR open + CI status + admin merge. PR# §11 박제. PR-1 gate:retro-complete label. PMOAgent retro final dispatch (memory feedback_pmo_retro_mandatory).
- [ ] **Phase 2 verify**: gh secret list PROMETHEUS_URL 존재 확인 (R-4, 부재 시 graceful skip 정합 박제) + workflow_dispatch dry-run 1회 (R-5 repo 최초 cron 검증).

---

## Self-Review

### Spec coverage
| spec §N | task | covered |
|---------|------|---------|
| §1 Trigger V1-V2/R-1/R-2 | Task 1 §0 | ✓ |
| §2 Q1-Q8 | Task 1 §5 + Task 2 + Task 5/6 | ✓ |
| §4 AC-1~5 | Task 5 (AC-1) + Task 6 (AC-2) + Task 2/7 (AC-3) + Task 5 caveat (AC-4) + Task 7 (AC-5) | ✓ |
| §5 INV-1~3 | Task 5 (INV-1 ADR-031 제외) + Task 5/6 (INV-2 absent) + Task 2 (INV-3 R-1 caveat) | ✓ |
| §6 scope_manifest | Task 3 (direct carry) | ✓ |
| §7 next lane | PR-1/PR-2 LAND tasks | ✓ |

14 file 전수 task assign.

### Placeholder scan
- "#TBD" = PR open 전 정상 (PR-LAND task 실 PR# carry)
- 다른 placeholder 없음

### Type consistency
- counter name 일관: `mctrader_dual_write_result_total{status="success"}` / `mctrader_collector_ticks_total` (Task 2/3/5/7, spec §6 SSOT)
- alert name 일관: QuadViolationADR029NoDualWrite / QuadViolationADR030NoCollectorTicks (Task 5/7)
- `absent(<counter>) or increase(<counter>[14d])==0` 일관 (Task 5/6)
- R-1 §4 SSOT drift caveat 일관 (Task 2 §6.1 / Task 5 group comment / spec §6 mct_193_decisions.Q4)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-17-mct-193-verify-gate.md`.**

Execution = **Subagent-Driven** (memory feedback_subagent_execution + feedback_autonomous_execution).

**dispatch plan** (2 PR sequential, single-repo):
- **PR-1 hub docs**: batch (Task 1 Story + Task 2 ADR-033 + Task 3 scope_manifest + Task 4 counters — file disjoint parallel) → Orchestrator R-1 3-source reconcile gate + PR-1 LAND
- **PR-2 alert/cron/박제**: Task 5 (prometheus-alerts.yml) + Task 6 (cron workflow) parallel → Task 7 (ADR-033 Accepted + Story §8.5/§11 + counters + EPIC-RESULTS + CLAUDE.md) → Task 8 (RETRO + PMO-AUDIT parallel) → Orchestrator PR-2 LAND + label + PMO retro + Phase 2 verify (PROMETHEUS_URL + cron dry-run)

**trust-but-verify 강제**: 각 implementer verify report 의무 + **Orchestrator 모든 BLOCKER 직접 ls/grep 재verify** (MCT-192 R1 false premise 동형 재발 0 유지 — PMOAgent verify-via 전수 효과).

REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`.
