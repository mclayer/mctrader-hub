---
story_key: MCT-171
plan_title: "DR runbook 본문 + invariant 8종 확장 + 4 layer capacity 제한 정책"
spec: docs/superpowers/specs/2026-05-14-MCT-171-dr-runbook-capacity-design.md
phase_pair: phase1_phase2
pr_split: 3  # Phase 1 hub docs / Phase 2 PR1 data code / Phase 2 PR2 hub 박제
created_at: 2026-05-14
status: phase1_in_progress
---

# MCT-171 implementation plan — DR runbook 본문 + invariant 8종 + 4 layer capacity

## §1 Phase 1 PR (mctrader-hub, docs only)

### 1.1 산출물

- [x] `.codeforge/counters.json` retitle_history append (Codex 9 결정점 합성 박제)
- [x] `docs/stories/MCT-171.md` 신규 (§1-§12 본문)
- [x] `docs/superpowers/specs/2026-05-14-MCT-171-dr-runbook-capacity-design.md` 신규
- [x] `docs/superpowers/plans/2026-05-14-mct-171-dr-runbook-capacity.md` (본 file)
- [ ] `docs/runbooks/nas-bucket-disaster-recovery.md` 본문 확장 (line 275-328 anchor 뒤 5 fail mode + invariant 8종 + 4 layer capacity step-by-step)
- [ ] `scope_manifests/EPIC-tier-promotion-single-source.yaml` (MCT-171 status: Reserved → IN_PROGRESS + started_date 2026-05-14)

### 1.2 Gate

- [ ] Phase 0 4 agent brainstorm 박제 verify (Story §2)
- [ ] Codex review 9 결정점 박제 verify (Story §3)
- [ ] DR runbook 본문 lines 추가 verify (stub 341 → 본문 N lines)
- [ ] DesignReviewPL dispatch (DR runbook 5 fail mode 정합 + invariant 8종 design + 4 layer capacity 정확성)
- [ ] CI green (lint + smoke)
- [ ] Admin merge (CI green 후, [[feedback_admin_merge_autonomy]])

### 1.3 진행 명령

```bash
# branch 생성 (이미 진행: story/MCT-171-phase1-dr-runbook-capacity)
git checkout -b story/MCT-171-phase1-dr-runbook-capacity

# author 4 file (위 1.1 list, 본 plan 작성 시점에 이미 진행 중)

# commit + push
git add docs/stories/MCT-171.md docs/superpowers/ docs/runbooks/ scope_manifests/ .codeforge/
git commit -m "docs(MCT-171): Phase 1 — DR runbook 본문 + Story / spec / plan 박제 (#TBD)"
git push -u origin story/MCT-171-phase1-dr-runbook-capacity

# PR 생성
gh pr create --title "docs(MCT-171): Phase 1 — DR runbook 본문 + Story / spec / plan + 4 layer capacity 박제"
```

## §2 Phase 2 PR1 (mctrader-data, code)

### 2.1 산출물

**신규 module 3**:
- `src/mctrader_data/capacity_probe.py` (4 layer hybrid probe, ~250 lines)
- `src/mctrader_data/ingest_blocker.py` (graceful drain + 80%/95% hysteresis, ~200 lines)
- `src/mctrader_data/capacity_thresholds.py` (CapacityThresholds dataclass SSOT, ~50 lines) — 필요 시 capacity_probe.py 내 inline

**기존 확장 2**:
- `src/mctrader_data/nas_migration/invariant_harness.py` (7종 → 8종, +`_check_ambiguity` method + status enum 9 variant)
- `src/mctrader_data/nas_metrics/prometheus_exporters.py` (capacity Gauge + invariant violation Counter + latency Histogram + ingest blocked Counter)
- `src/mctrader_data/collector.py` (IngestBlocker hook 1 callsite, hot path 영향 0)

**deprecate 1**:
- `src/mctrader_data/compactor/promotion.py` `verify_no_ambiguity` 함수 → InvariantHarness 측 흡수, caller 측 변경

**Integration test 3**:
- `tests/integration/test_invariant_harness_8.py` — 8종 enforcement timing + ambiguity 통합 + MCT-169 D10 회귀 0
- `tests/integration/test_capacity_probe.py` — hybrid timing + Prometheus emit
- `tests/integration/test_ingest_blocker.py` — graceful drain + 80%/95% hysteresis + Counter emit

### 2.2 TDD 순서 (subagent-driven, [[feedback_subagent_execution]])

1. **Test author (failing)** — QADeveloperAgent dispatch
   - test_invariant_harness_8.py (8종 ALL PASS + ambiguity violation 검출 + MCT-152/153/155 caller 회귀 0)
   - test_capacity_probe.py (hybrid timing + Gauge emit)
   - test_ingest_blocker.py (graceful drain + hysteresis)
2. **Implementation (minimal pass)** — DeveloperAgent dispatch
   - capacity_thresholds.py + capacity_probe.py + ingest_blocker.py 신규
   - invariant_harness.py 8종 확장
   - prometheus_exporters.py 4 metric 신규
   - collector.py IngestBlocker hook
   - promotion.py verify_no_ambiguity deprecate
3. **Test PASS verify** — `pytest tests/integration/test_invariant_harness_8.py tests/integration/test_capacity_probe.py tests/integration/test_ingest_blocker.py -v`
4. **Phase 2 baseline 측정 (R-CRITICAL mitigation)**:
   - collector hot path runtime probe — 50 sym × 3 channel ingest 1h
   - WAL/L1/NAS/Host 4 layer 측정 baseline 박제 (CLAUDE.md + RETRO)
   - WAL 30G 산정 근거 verify — 초과 risk 검출 시 D11 hard_limit amendment 발의

### 2.3 Gate

- [ ] 3 integration test ALL PASS
- [ ] MCT-152/153/155 InvariantHarness caller 회귀 0 (기존 test suite ALL PASS)
- [ ] MCT-169 D10 ambiguity invariant test 회귀 0
- [ ] AC-1/2/3/5 verify (Story §4)
- [ ] Phase 2 runtime probe baseline 측정 결과 박제
- [ ] CI green
- [ ] CodeReviewPL dispatch
- [ ] SecurityTestPL dispatch (capacity probe + ingest blocker secret leak / log 측 0)
- [ ] Admin merge

### 2.4 진행 명령

```bash
# mctrader-data 측 working dir (별 worktree 권고, [[feedback_parallel_session_branch_race]])
cd c:/workspace/mclayer/mctrader-data

# branch 생성
git checkout -b story/MCT-171-phase2-invariant-capacity

# subagent-driven TDD ([[feedback_subagent_execution]])
# QADeveloperAgent → DeveloperAgent → 측정 → commit

# PR 생성
gh pr create --title "feat(MCT-171): invariant 8종 통합 + capacity_probe + ingest_blocker 신규"
```

## §3 Phase 2 PR2 (mctrader-hub, 박제)

### 3.1 산출물

- `docs/stories/MCT-171.md` §11 retro_file + §12 측정 결과 + status: IN_PROGRESS → COMPLETED + completed_at
- `docs/adr/ADR-029-tier-promotion-single-source.md` Status §D4 + §D5 + §D11 verify status entry append
- `docs/runbooks/nas-bucket-disaster-recovery.md` verify LAND footer
- `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 5/6 COMPLETED + story_sequence MCT-171 status: IN_PROGRESS → COMPLETED + land_date
- `CLAUDE.md` §MCT-171 COMPLETED + §EPIC milestone 5/6 박제
- `docs/retros/RETRO-MCT-171.md` 신규 (PMOAgent 자동 dispatch)

### 3.2 Gate

- [ ] Phase 2 PR1 LAND verify (mctrader-data PR merge commit)
- [ ] PMOAgent 자동 dispatch (ADR-045, 5min grace + 4 attempts cumulative offset 5/10/20/35min)
- [ ] RETRO-MCT-171.md write — 4 field schema (delivered / measurements / risks_realized / followups)
- [ ] Story §11 4 field schema update
- [ ] Epic milestone 5/6 갱신
- [ ] `gate:retro-complete` label add
- [ ] CI green + Admin merge

## §4 Risk mitigation 실행

| R | Phase | Action |
|---|-------|--------|
| **R-CRITICAL** WAL 30G 산정 미검증 | Phase 2 | Phase 2 baseline 측정 의무 (50 sym × 3 channel × 1h), 초과 검출 시 D11 amendment |
| **R1** invariant 통합 backward compat | Phase 2 PR1 | MCT-169 D10 test 회귀 0 + MCT-152/153/155 caller integration test ALL PASS |
| **R2** capacity_probe hot path 영향 | Phase 2 PR1 | collector.py sibling + 5min idle baseline + 1h sweep timing |
| **R3** graceful drain WAL atomic boundary | Phase 2 PR1 | WAL sealed segment drain 시점 정합 + ADR-017 zero-loss preserve |
| **R4** Prometheus cardinality drift | Phase 2 PR1 | label enum hardcoded enforce + free-form label fail-fast |
| **R5** DR runbook priority drift | Phase 1 | Codex 합의 priority 박제 + 본문 사용자 검토 1회 권고 |
| **R6** Host 200G bridge alert only | Phase 2 PR2 | CLAUDE.md note 박제 (LVM 별 infra task 발의) |

## §5 진행 순서 강제

**Phase 1 PR → Phase 2 PR1 → Phase 2 PR2 sequential LAND**. PR1 fail 시 PR2 발의 0. PR2 = PMOAgent 박제 PR (Phase 2 PR1 merge 후 자동 trigger).

## §6 verified-via 박제

ADR-073 §결정 1 + §결정 6 mandate. plan §1.1 / §2.1 file path 모두 spec frontmatter `pre_lookup_evidence` 인용분 정합.
