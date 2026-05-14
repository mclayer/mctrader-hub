---
story_key: MCT-172
plan_title: "EPIC-tier-promotion-single-source policy finalize"
spec: docs/superpowers/specs/2026-05-14-MCT-172-policy-finalize-design.md
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-14
status: phase1_in_progress
---

# MCT-172 implementation plan — Epic policy finalize

## §1 Phase 1 PR (mctrader-hub, docs only)

### 1.1 산출물

- [x] `.codeforge/counters.json` retitle_history append (Codex 9 결정점 합성)
- [x] `docs/stories/MCT-172.md` 신규 (§1-§12)
- [x] `docs/superpowers/specs/2026-05-14-MCT-172-policy-finalize-design.md` 신규
- [x] `docs/superpowers/plans/2026-05-14-mct-172-policy-finalize.md` (본 file)
- [ ] `docs/adr/ADR-029-tier-promotion-single-source.md` §D8 amendment (MCT-172) — 14d window 박제 + telemetry watcher policy
- [ ] `scope_manifests/EPIC-tier-promotion-single-source.yaml` (MCT-172 status: Reserved → IN_PROGRESS + started_date 2026-05-14)

### 1.2 Gate

- [ ] Phase 0 4 agent brainstorm 박제 verify (Story §2)
- [ ] Codex review 9 결정점 박제 verify (Story §3)
- [ ] DesignReviewPL dispatch (D8 amendment 정합 + Epic CLOSED prerequisite 박제 정확성)
- [ ] CI green (lint + smoke)
- [ ] Admin merge

## §2 Phase 2 PR1 (mctrader-data, code)

### 2.1 산출물

**Cleanup 1**:
- `src/mctrader_data/compactor/promotion.py` — `verify_no_ambiguity` 함수 **제거** + caller migrate

**caller migrate (grep 전수 식별 후)**:
- MCT-152/153/155/169/171 측 caller — `InvariantHarness._check_ambiguity` 또는 full `verify()` 호출로 변경

**Integration test 3 신규**:
- `tests/integration/test_epic_smoke.py` — 8 invariant cross-Story smoke + baseline+peak hybrid
- `tests/integration/test_wal_synthetic_baseline.py` — paper mode WAL 30G synthetic measure
- `tests/integration/test_d8_sunset_telemetry_watcher.py` — telemetry watcher 14d rolling 0-hit alert rule

### 2.2 TDD 순서 (subagent-driven, [[feedback_subagent_execution]])

1. **QADeveloperAgent dispatch** — 3 integration test (failing) author
2. **DeveloperAgent dispatch** — promotion.py cleanup + caller migrate
3. **Test PASS verify** — 3 신규 test + 기존 회귀 0 (MCT-152/153/155/169/171 caller)

### 2.3 Gate

- [ ] 3 integration test ALL PASS
- [ ] MCT-152/153/155/169/171 InvariantHarness caller 회귀 0
- [ ] `grep -rn "verify_no_ambiguity" mctrader-data/src` = 0
- [ ] AC-1/2/3/4/5 verify (Story §4)
- [ ] CI green + Admin merge

## §3 Phase 2 PR2 (mctrader-hub, 박제)

### 3.1 산출물

- `docs/stories/MCT-172.md` §11 retro_file + §12 측정 결과 + status: IN_PROGRESS → POLICY_FINALIZED + completed_at
- `docs/adr/ADR-029-tier-promotion-single-source.md` Status §D8 + §D9 + §D10 verify status entry
- `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 6/6 + Epic status POLICY_FINALIZED + epic_close_gate prerequisite 분리
- `CLAUDE.md` §MCT-172 COMPLETED + §EPIC Story-6 박제 + Epic CLOSED pending production
- `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` §Story-6 결과 + Epic POLICY_FINALIZED + Epic CLOSED prerequisite
- `docs/retros/RETRO-MCT-172.md` 신규 (PMOAgent 자동 dispatch)

### 3.2 Gate

- [ ] Phase 2 PR1 LAND verify (mctrader-data PR merge commit)
- [ ] PMOAgent 자동 dispatch (ADR-045)
- [ ] RETRO 4 field schema (delivered / measurements / risks_realized / followups)
- [ ] Story §11 4 field schema + §12 측정 결과
- [ ] Epic milestone 6/6 + Epic status POLICY_FINALIZED
- [ ] EPIC-RESULTS §Story-6 + Epic CLOSED prerequisite 박제
- [ ] CI green + Admin merge

## §4 Risk mitigation 실행

| R | Phase | Action |
|---|-------|--------|
| **R-CRITICAL** | Phase 2 PR1 | paper mode synthetic baseline 측정 + production = 별 PR 명시 박제 |
| R1 caller migrate 누락 | Phase 2 PR1 | grep 전수 식별 + MCT-152/153/155/169/171 caller integration test 회귀 0 |
| R2 D8 sunset 14d timing | Phase 2 PR1 + PR2 | telemetry watcher 박제 + 실 sunset = 별 Story (2026-09-01 cutoff) |
| R3 Paper mode synthetic validity | Phase 2 PR1 | synthetic = sizing 가설 검증 only, production 측정은 별 PR |
| R4 Epic CLOSED timing 모호 | Phase 2 PR2 | scope_manifest epic_close_gate prerequisite 분리 + Epic status POLICY_FINALIZED |
| R5 D1-D11 traceability | Phase 2 PR2 | EPIC-RESULTS §Story-6 결과 박제 시 8 invariant ↔ D1-D11 mapping 명시 |

## §5 진행 순서 강제

Phase 1 PR → Phase 2 PR1 → Phase 2 PR2 sequential.

## §6 post-Story carry over (Epic CLOSED prerequisite)

본 Story LAND 후 Epic CLOSED 진입을 위한 별 PR/Story 의무:

1. **production deploy 후 14d 0-hit telemetry** (2026-08-18 ~ 2026-09-01)
2. **WAL 30G production measurement** (peak market open 09:00 KST burst)
3. **production evidence quad 동일 1h window** (bucket + log + Prometheus + drainage)
4. **Epic CLOSED 박제 PR or scope_manifest amend** (POLICY_FINALIZED → CLOSED transition)
