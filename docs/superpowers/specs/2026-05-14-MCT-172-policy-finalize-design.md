---
story_key: MCT-172
title: "EPIC-tier-promotion-single-source policy finalize — 8 invariant smoke + D8 sunset policy + promotion.py cleanup + WAL synthetic baseline"
epic: EPIC-tier-promotion-single-source
phase_in_epic: 6
mode: sequential
repos: [mctrader-hub, mctrader-data]
phase_pair: phase1_phase2
status: brainstorm_complete_spec_authored
created_at: 2026-05-14
brainstorm_phase0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
codex_review: 2026-05-14 (9 결정점 단일 패스 합성, D8-1~D8-9)
pre_lookup_evidence:
  - "verified-via: Read docs/adr/ADR-029-tier-promotion-single-source.md (§D8 sunset criterion line 54-63)"
  - "verified-via: Grep verify_no_ambiguity → compactor/promotion.py:177 잔존 박제"
  - "verified-via: Grep _INVARIANT_NAMES → nas_migration/invariant_harness.py:140 8개 확장 (MCT-171 LAND)"
  - "verified-via: Read docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md (5/6 박제, MCT-172 row Reserved)"
  - "verified-via: Read scope_manifests/EPIC-tier-promotion-single-source.yaml (story_sequence MCT-172 Reserved, milestone 5/6)"
  - "verified-via: Bash df -h c:/ (476G total / 199G avail, production data dir 부재)"
---

# MCT-172 brainstorm spec — EPIC-tier-promotion-single-source policy finalize

## §1 Brainstorm 배경

EPIC-tier-promotion-single-source Story-6 (마지막). prerequisite MCT-167~171 ALL LAND (2026-05-14) 후 Epic 의 **policy finalize Story**. Codex review 합의 (D8-3+D8-6+D8-9): **Epic CLOSED 는 production evidence 완성 후 별 PR**. 본 Story = policy finalize + cleanup + integration smoke + WAL synthetic baseline 박제.

사용자 directive: autonomous + 끝까지 진행 ([[feedback_autonomous_execution]]).

## §2 Phase 0 verify finding

§Story-MCT-172.md §1.2 박제분 동치:

1. ✅ ADR-029 §D8 sunset criterion 박제 (cutoff 2026-09-01 + telemetry 0-hit 14d AND)
2. ⚠️ `compactor/promotion.py:177` `verify_no_ambiguity` 잔존 → 본 Story cleanup
3. ✅ InvariantHarness 8종 통합 LAND (MCT-171)
4. ✅ EPIC-RESULTS 5/6 박제
5. ❌ Production data dir 부재 → paper mode synthetic baseline + production = 별 PR

## §3 Phase 0 4-agent burst 합성

§Story-MCT-172.md §2 박제분 동치.

- **Domain** 5 핵심 사실
- **Researcher** 3 핵심 개념 + 2 Unknown unknowns (production data 부재 / D8 14d 측정 timing)
- **Analyst** AC 5 + Edge 4 + 모호성 7건
- **PMO** 단일 Story 확정, R = Epic close fail risk (D8-9 mitigation)

## §4 Codex review 9 결정점 합성

§Story-MCT-172.md §3 박제분 동치. 9 design point 채택:

| D8-N | 채택 |
|---|---|
| D8-1 | A (InvariantHarness 8종 SSOT) |
| D8-2 | C (baseline 30min + peak simulate 30min hybrid) |
| D8-3 | A (정책 finalize only) |
| D8-4 | C (2026-08-18 ~ 2026-09-01 14d window) |
| D8-5 | A (verify_no_ambiguity 즉시 제거 + caller migrate) |
| D8-6 | A (production deploy 후 실측, paper mode synthetic 만 evidence 대체 X) |
| D8-7 | A (초과 시 Epic close FAIL gate) |
| D8-8 | A (동일 1h window evidence quad) |
| D8-9 | C (production 14d 후 Epic CLOSED 별 PR) |

## §5 설계 결정

### 5.1 promotion.py verify_no_ambiguity 제거 (D8-5=A)

**File**: `mctrader-data/src/mctrader_data/compactor/promotion.py:177`

cleanup 절차:
1. `grep -rn "verify_no_ambiguity" mctrader-data/src` — caller graph 전수 식별
2. caller 측 InvariantHarness 호출 변경 (`InvariantHarness._check_ambiguity` 또는 full `verify()` 호출)
3. `def verify_no_ambiguity` 함수 본문 제거 (line 177-XXX)
4. `_nas_partition_exists` helper (line 296+) 측 검토 — `verify_no_ambiguity` 단독 의존이면 함께 제거
5. promotion.py import 정리 + caller 측 import 갱신
6. Integration test 회귀 0 verify (MCT-152/153/155/169/171 caller integration test ALL PASS)

### 5.2 ADR-029 §D8 amendment (D8-3=A + D8-4=C)

**File**: `mctrader-hub/docs/adr/ADR-029-tier-promotion-single-source.md`

amendment 박제 (Status 섹션 신규 entry):

```markdown
### MCT-172 amendment (2026-05-14) — D8 sunset policy finalize

본 amendment = EPIC-tier-promotion-single-source Story-6 (MCT-172) Phase 1 박제분. 본 ADR §D8 의 **policy finalize** + 14d telemetry window 명시.

**D8 sunset policy finalize**:
- **시점 cutoff**: 2026-09-01T00:00:00Z (hard sunset, MCT-170 amendment 박제분 유지)
- **telemetry 14d window**: **2026-08-18T00:00:00Z ~ 2026-09-01T00:00:00Z** (cutoff 직전 14d, D8-4=C Codex 채택)
- **rolling 0-hit metric**: `nas_reader_ambiguity_total` Counter 14d rolling rate = 0/min 의무 (Prometheus alert rule 박제)
- **combined criterion (AND)**: cutoff timestamp 도달 **AND** 14d window 내 telemetry rate = 0 충족 → D8 local fallback 영구 disable
- **실 sunset 실행**: 2026-09-01 별 Story or scheduled cron (telemetry watcher 측 alert rule trigger 시 별 PR 발의)
- **본 Story (MCT-172) scope**: policy finalize + telemetry watcher 박제 only. 실 sunset 실행은 후속.
```

### 5.3 Integration smoke test 신규 (D8-1=A + D8-2=C)

**File**: `mctrader-data/tests/integration/test_epic_smoke.py` (신규)

scope:
1. 8 invariant cross-Story integration smoke — InvariantHarness 8종 (MCT-171 SSOT) ALL PASS
2. Paper mode synthetic ingest baseline 30min + peak simulate 30min hybrid
3. ambiguity invariant 위반 0 verify
4. MCT-152/153/155/169/171 caller 회귀 0

**File**: `mctrader-data/tests/integration/test_wal_synthetic_baseline.py` (신규)

scope:
1. Paper mode synthetic ingest 50 sym × 3 channel × 1h
2. WAL local segment 누적 size 측정 → 30G sizing 가설 검증 (± 50% range 박제)
3. R-CRITICAL carry over note 박제 (production 측정 = 별 PR)

**File**: `mctrader-data/tests/integration/test_d8_sunset_telemetry_watcher.py` (신규)

scope:
1. `nas_reader_ambiguity_total` Counter 14d rolling rate 측정 mock
2. Prometheus alert rule 검증 (14d rate = 0 → silence, > 0 → alert)
3. telemetry watcher 박제 invariant

### 5.4 EPIC-RESULTS Story-6 결과 박제 (Phase 2 PR2)

**File**: `mctrader-hub/docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`

amendment:
- frontmatter `completed_stories: 5 → 6` + `status: IN_PROGRESS → POLICY_FINALIZED`
- 헤더 "(IN_PROGRESS, 5/6 완료)" → "(**POLICY_FINALIZED**, 6/6 policy 완료, Epic CLOSED pending production evidence)"
- Story 완료 현황 table MCT-172 row = Reserved/TBD → POLICY_FINALIZED + 3 PR commit SHA 박제
- 합계 row: 19 (5/6) → 24 (6/6 policy)
- §Story-6 결과 박제 section 신규 추가 (3 PR timeline + D8-1~D8-9 채택 박제 + AC ALL PASS + R-CRITICAL carry over + Epic CLOSED prerequisite)
- §Epic CLOSED prerequisite 신규 section (production 14d 측정 + WAL 30G 실측 + evidence quad 동일 1h window + Epic CLOSED 박제 별 PR)

### 5.5 scope_manifest milestone + Epic status transition

**File**: `mctrader-hub/scope_manifests/EPIC-tier-promotion-single-source.yaml`

amendment (Phase 2 PR2):
- `status: IN_PROGRESS` → `status: POLICY_FINALIZED` (CLOSED 아님)
- `milestone_progress.completed: 5 → 6` + `in_progress: 0` + `reserved: 0`
- `story_sequence` MCT-172 status: Reserved → POLICY_FINALIZED + land_date
- `epic_close_gate` 측 미충족 항목 명시:
  - "MCT-172 PR MERGED + Epic policy finalize PASS" ✅ (본 Story LAND)
  - "production deploy 후 14d 0-hit telemetry" ❌ (별 PR)
  - "WAL 30G production measurement" ❌ (별 PR)
  - "production evidence quad 동일 1h window" ❌ (별 PR)
  - "PMOAgent retro + gate:retro-complete" ✅ (Phase 2 PR2)
  - "production evidence quad ALL PASS (codeforge-plugin#620 Fix-1)" ❌ (별 PR)

## §6 ADR amendment 의무

- ADR-029 §D8 amendment (MCT-172) — 14d window 박제 (2026-08-18 ~ 2026-09-01) + telemetry watcher policy
- ADR-029 §D9 + §D10 verify status entry (prerequisite ALL LAND + InvariantHarness 8종 SSOT)

신규 ADR 0.

## §7 scope_manifest 초안

§Story-MCT-172.md §6 박제분 동치.

## §8 PR 분리

§Story-MCT-172.md §8 박제분 동치. 3 PR cross-repo sequential.

## §9 plan link

`docs/superpowers/plans/2026-05-14-mct-172-policy-finalize.md` 참조.
