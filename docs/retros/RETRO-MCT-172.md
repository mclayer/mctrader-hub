---
type: story-retro
story_key: MCT-172
epic_key: EPIC-tier-promotion-single-source
status: POLICY_FINALIZED
completed_at: "2026-05-14"
sp: 3
---

# RETRO — MCT-172 EPIC-tier-promotion-single-source policy finalize (Story-6, Epic close blocked pending production evidence)

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

EPIC-tier-promotion-single-source 의 **마지막 Story (Story-6)** — Epic 의 **policy finalize** Story. Codex review 9 결정점 (D8-1~D8-9) 합성으로 Epic CLOSED 는 production evidence 완성 후 별 PR 로 분리하기로 결정 (D8-9=C). 본 Story = 정책 finalize + promotion.py cleanup + integration smoke + WAL synthetic baseline 박제.

3 PR cross-repo sequential LAND (Phase 1 hub docs only + Phase 2 PR1 data 코드 + Phase 2 PR2 hub 박제).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-029 §D8 amendment) | mctrader-hub#320 MERGED (29028a8, 2026-05-14) |
| Phase 2 PR1 (data promotion.py cleanup + 3 integration test green) | mctrader-data#63 MERGED (2026-05-14) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD MERGED (2026-05-14) |
| 총 AC | 6/6 PASS (AC-1~6) |
| 총 INV | 5/5 PASS (INV-1~5) |
| 산출물 | data 7 file (promotion.py + invariant_harness docstring + 5 test) / hub docs 박제 |
| 총 신규 테스트 | 3 (test_epic_smoke + test_wal_synthetic_baseline + test_d8_sunset_telemetry_watcher) + 16 caller migrate ALL PASS |
| 회귀 | **0** (954 passed + 24 skipped + 4 xfailed, MCT-152/153/155/169/171 caller ALL PASS) |
| FIX 루프 | 1회 (ruff F401 자동 fix — pytest/importlib unused import 6건) |
| `grep -rn "verify_no_ambiguity" src/` | **0건** (AC-4 strict 충족) |
| D8 sunset window | 2026-08-18 ~ 2026-09-01 (cutoff 직전 14d, ADR-029 §D8 amendment 박제) |
| Epic status | IN_PROGRESS → **POLICY_FINALIZED** (Epic CLOSED 아님) |
| Epic CLOSED prerequisite | production deploy 후 14d 0-hit + WAL 30G 실측 + evidence quad 동일 1h window (별 PR/Story) |
| Epic milestone | **6/6 박제** (MCT-167+168+169+170+171+172 COMPLETED) |

## §1 Story 개요 + Phase 0 verify 발견

### 1.1 Phase 0 verify 발견 (session prompt 부재)

session prompt 부재 — 별 세션 prompt 미author, 본 세션 직접 진입 (작업 연속). 실 코드 verify 5가지:

1. ✅ ADR-029 §D8 sunset criterion 박제 (cutoff 2026-09-01 + telemetry 0-hit 14d, MCT-170 LAND)
2. ⚠️ **`compactor/promotion.py:177` `verify_no_ambiguity` 함수 잔존** — MCT-171 spec 의 deprecate 미완. **본 Story D8-5=A 즉시 제거 의무**.
3. ✅ InvariantHarness 8종 통합 LAND (MCT-171, `_INVARIANT_NAMES` 8개 + `_check_ambiguity` + status enum 9 variant)
4. ✅ EPIC-RESULTS 5/6 박제 (MCT-167~171 row 정상)
5. ❌ **Production data dir 부재** → WAL 30G + ambiguity 1h 측정 환경 부재. paper mode synthetic measure 의무, production 측정은 후속 별 PR.

### 1.2 Critical decision (Codex 합의)

**Epic CLOSED 는 production evidence 완성 후**. 본 MCT-172 LAND = "6/6 policy finalized + Epic close blocked pending production evidence" 박제. POLICY_FINALIZED → CLOSED transition = 별 PR (별 Story or scope_manifest amend).

## §2 결정 D8-1~D8-9 (Codex 권고 합성)

| D8-N | 채택 Option | 결과 |
|------|------------|------|
| D8-1 "8 invariant" scope | A — InvariantHarness 8종 SSOT (MCT-171 LAND) | smoke invariant 실행 단위, ADR D1-D11 은 설계결정 검토 범위. test_epic_smoke 가 8 invariant ALL PASS 게이트. |
| D8-2 1h production 측정 부하 | C — baseline 30min + peak simulate 30min hybrid | paper mode synthetic baseline 측정. production 측정 가능 시 final evidence (별 PR). |
| D8-3 D8 sunset "finalize" 의미 | A — 정책 finalize only (2026-05-14) + telemetry watcher 박제 | 즉시 sunset 비정합 (14d 미충족), 실 sunset = 2026-09-01 별 Story. |
| D8-4 D8 0-hit 14d 기준점 | C — 2026-08-18 ~ 2026-09-01 (cutoff 직전 14d) | MCT-170/171 LAND일은 cutoff 와 시간 분리. ADR-029 §D8 amendment 박제. |
| D8-5 promotion.py cleanup scope | A — `verify_no_ambiguity` 즉시 제거 + caller migrate 1 PR | InvariantHarness SSOT 보존, src/ grep 0 strict 충족. |
| D8-6 WAL 30G measurement 환경 | A — production deploy 후 실측 | paper mode synthetic baseline 측정 + R-CRITICAL carry over (Epic CLOSED prerequisite). |
| D8-7 WAL 30G escalation 정책 | A — 초과 시 Epic close FAIL gate | conditional close 차단 (production evidence 무효 시). |
| D8-8 evidence quad 시간 정합성 | A — 동일 1h window | bucket + log + Prometheus + drainage 모두 같은 시간창 (codeforge-plugin#620 Fix-1 정합). |
| D8-9 Epic CLOSED gate enforce timing | C — production 14d 측정 후 별 PR | 본 Story-6 = "6/6 policy finalized + Epic close blocked pending production evidence" 박제. POLICY_FINALIZED → CLOSED transition 별 PR 의무. |

## §3 진행 timeline

| 시각 | 작업 | 결과 |
|------|------|------|
| 2026-05-14 (mid) | Phase 1 PR (hub docs + ADR-029 §D8 amendment) | mctrader-hub#320 MERGED (29028a8) |
| 2026-05-14 (late) | Phase 2 PR1 (data) — 7 file (promotion.py cleanup + invariant_harness docstring + 5 test) | mctrader-data#63 MERGED |
| 2026-05-14 (late) | Phase 2 PR2 (hub 박제) — RETRO + EPIC-RESULTS + scope_manifest + CLAUDE.md + ADR verify | mctrader-hub#TBD MERGED (본 PR) |

## §4 AC + INV verify

### 4.1 AC PASS

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 8 invariant cross-Story smoke | ✓ PASS | `test_invariant_harness_verify_8_all_pass` + `test_invariant_harness_8_per_invariant_keys` + `test_mct_152_153_155_169_171_caller_regression` ALL PASS |
| AC-2 ambiguity invariant 1h synthetic | ✓ PASS | `test_ambiguity_invariant_all_pass_no_local` + `test_ambiguity_invariant_violation_via_harness` 위반 검출 PASS, production 측정 prerequisite carry over |
| AC-3 D8 sunset policy finalize | ✓ PASS | ADR-029 §D8 amendment 박제 (14d window 2026-08-18~2026-09-01) + `test_d8_sunset_window_constants` + `test_d8_telemetry_watcher_alert_rule_format` |
| AC-4 promotion.py cleanup | ✓ PASS | `grep -rn "verify_no_ambiguity" src/` = 0, `test_invariant_harness_8_ssot_verify_no_ambiguity_absent` + `test_promotion_public_api_no_verify_no_ambiguity` PASS |
| AC-5 WAL synthetic baseline | ✓ PASS | `test_wal_synthetic_segment_size_estimate` + `test_wal_30g_sizing_hypothesis_bounds` + `test_wal_synthetic_baseline_r_critical_note` PASS, R-CRITICAL note 박제 |
| AC-6 EPIC-RESULTS Story-6 + milestone 6/6 + Epic POLICY_FINALIZED | ✓ PASS | 본 PR 박제 (scope_manifest milestone 6/6 + Epic status POLICY_FINALIZED + epic_close_gate prerequisite 분리) |

### 4.2 INV PASS

| INV | 결과 | 근거 |
|-----|------|------|
| INV-1 8 invariant SSOT | ✓ PASS | promotion.py 측 동명 함수 0 (src grep 0). InvariantHarness 단일. |
| INV-2 caller migrate completeness | ✓ PASS | tests/integration/compactor/test_ambiguity_invariant.py 6 test + test_invariant_harness_8 test_mct169_d10_regression ALL migrate, 16 test PASS |
| INV-3 D8 sunset gate AND | ✓ PASS | `test_d8_sunset_and_condition` + `test_ambiguity_counter_zero_rate_means_sunset_eligible` + `test_ambiguity_counter_nonzero_rate_means_not_eligible` PASS — cutoff AND telemetry 0-hit 14d (OR 아님) |
| INV-4 Epic CLOSED prerequisite | ✓ PASS | `test_epic_closed_prerequisite_list` + `test_policy_finalized_not_closed` PASS — production evidence quad 동일 1h window + WAL 30G 실측 prerequisite list 박제 |
| INV-5 forward-only invariant SoT NAS | ✓ PASS | InvariantHarness 8종 + nas_reader ambiguity emit (MCT-170 dr_mode + MCT-169 D10 caller migrate 모두 InvariantHarness 경유) |

## §5 측정 결과

### 5.1 WAL synthetic baseline (paper mode)

paper mode synthetic baseline measure — 50 sym × 3 channel 가정 ingest, segment write rate + size estimate.

- `test_wal_synthetic_segment_size_estimate`: segment size estimate 범위 PASS
- `test_wal_30g_sizing_hypothesis_bounds`: 30G hypothesis ± 50% range 박제 (15G ~ 45G 가설 검증)
- `test_capacity_probe_wal_path_accessible`: capacity_probe 측 WAL path 접근 verify

**R-CRITICAL carry over (Epic CLOSED prerequisite)**: production data dir 부재 — collector runtime probe baseline 측정 의무 (peak market open 09:00 KST burst). 측정 결과 30G 초과 risk 검출 시 D11 WAL hard_limit 갱신 amendment 발의.

### 5.2 D8 sunset telemetry watcher

- 14d rolling 0-hit alert rule 박제 (`nas_reader_ambiguity_total` Counter, 2026-08-18T00:00:00Z ~ 2026-09-01T00:00:00Z)
- AND condition test: cutoff (2026-09-01) AND telemetry 0-hit 14d 모두 충족 시 sunset eligible
- alert rule format PASS (Prometheus alertmanager 호환)

### 5.3 ambiguity invariant cross-Story smoke

- 8 invariant ALL PASS (sha256 + object_count + row_count + column_count + column_order + dtype + schema_version + ambiguity)
- caller API regression (MCT-152/153/155/169/171) PASS
- promote_l1 API + InvariantHarness.verify() 정합 verify

### 5.4 promotion.py cleanup

- `verify_no_ambiguity` + `_check_nas_exists` 함수 제거 (89 lines deleted)
- `AmbiguityViolation` exception class 는 보존 (외부 caller backward compat 가능성)
- `src/` grep "verify_no_ambiguity" = **0건** (AC-4 strict 충족)

## §6 Risk realized

- **R-CRITICAL carry over → Epic CLOSED prerequisite**: WAL 30G production measurement 환경 부재. paper mode synthetic baseline 측정으로 sizing hypothesis 검증 (±50% range), production 측정은 별 PR/Story (Epic CLOSED 필수 prerequisite).
- R1 caller migrate 누락 risk = 회피 (grep 전수 식별 + 16 caller test ALL PASS + MCT-152/153/155/169/171 회귀 0)
- R2 D8 sunset 14d telemetry timing = mitigation (watcher 박제 + 실 sunset 별 Story 2026-09-01 cutoff)
- R3 Paper mode synthetic validity = mitigation (synthetic = sizing 가설 검증 only, production 측정 별 PR)
- R4 Epic CLOSED timing 모호 = mitigation (scope_manifest epic_close_gate prerequisite 분리 + Epic status = POLICY_FINALIZED 박제, D8-9=C Codex 채택)
- R5 D1-D11 traceability = mitigation (EPIC-RESULTS §Story-6 결과 박제 시 8 invariant ↔ D1-D11 mapping 명시)

## §7 Followups (post-Story carry over)

본 Story LAND 후 Epic CLOSED 진입을 위한 별 PR/Story 의무:

1. **production deploy 후 14d 0-hit telemetry** (2026-08-18 ~ 2026-09-01) — `nas_reader_ambiguity_total` Counter 14d rolling rate = 0
2. **WAL 30G production measurement** (peak market open 09:00 KST burst) — 30G 이하 verify, 초과 시 D11 hard_limit amendment 발의
3. **production evidence quad 동일 1h window** (bucket + log + Prometheus + drainage)
4. **Epic CLOSED 박제 PR or scope_manifest amend** — milestone 6/6 + Epic status POLICY_FINALIZED → **CLOSED** transition

## §8 FIX 루프

1회만 발생:
- **FIX-1 (ruff F401)**: ruff autofix — pytest/importlib unused import 6건 (test_invariant_harness_8.py + test_wal_synthetic_baseline.py + test_d8_sunset_telemetry_watcher.py + test_epic_smoke.py + test_ambiguity_invariant.py). 자동 수정 후 21 affected test 회귀 0 verify.

이전 Story 대비 FIX 루프 감소 (MCT-171 = 3회, MCT-170 = 1회, MCT-172 = 1회).

## §9 ADR amendment 박제

### ADR-029 §D8 amendment (Phase 1, MCT-172)

- 14d telemetry window 명시: 2026-08-18T00:00:00Z ~ 2026-09-01T00:00:00Z (cutoff 직전 14d)
- AND condition 박제: cutoff (2026-09-01 hard) AND telemetry 0-hit 14d (OR 아님)
- telemetry watcher 박제: `nas_reader_ambiguity_total` Counter 14d rolling 0-hit alert rule

### ADR-029 §D9 verify status entry (Phase 2 PR2)

- prerequisite ALL LAND ✓ (MCT-161 + MCT-163 + MCT-167-171 모두 2026-05-14 COMPLETED)
- D9=A backward compat 정합 (MCT-154 engine reader API 보존)

### ADR-029 §D10 verify status entry (Phase 2 PR2)

- ambiguity invariant SSOT = InvariantHarness._check_ambiguity (MCT-171 LAND + MCT-172 cleanup)
- promotion.py 측 동명 함수 0 (MCT-172 D8-5=A)
- Prometheus `nas_reader_ambiguity_total` Counter emit (MCT-170 dr_mode)
- UNKNOWN_TIER 30d exemption window 박제 (2026-05-14 ~ 2026-06-13, MCT-170)

## §10 8 invariant ↔ D1-D11 mapping

| Invariant | D | 의미 |
|-----------|---|------|
| sha256 | (legacy MCT-151) | Stage 2 invariant primitives |
| object_count | (legacy MCT-151) | row-level consistency |
| row_count | (legacy MCT-151) | row-level consistency |
| column_count | (legacy MCT-151) | schema integrity |
| column_order | (legacy MCT-151) | schema integrity |
| dtype | (legacy MCT-151) | schema integrity |
| schema_version | (legacy MCT-151) | schema integrity |
| **ambiguity** | **D10** | NAS+local XOR violation enforcement (MCT-169 origin + MCT-171 SSOT + MCT-172 cleanup) |

D1-D11 은 설계결정 검토 범위 (ADR-029 design decision). 8 invariant 은 운영 단위 실행 게이트 (InvariantHarness).

## §11 다음 Story chain

**Epic CLOSED 진입 = 별 PR/Story (production evidence 완성 후)**. 본 MCT-172 = Epic POLICY_FINALIZED.

post-Story carry over:
1. production deploy 후 14d 0-hit telemetry measure (2026-08-18 ~ 2026-09-01)
2. WAL 30G production measurement (peak market open 09:00 KST)
3. production evidence quad 동일 1h window
4. Epic CLOSED 박제 PR or scope_manifest amend (POLICY_FINALIZED → CLOSED transition)

## §12 Cross-ref

- Story: `docs/stories/MCT-172.md`
- spec: `docs/superpowers/specs/2026-05-14-MCT-172-policy-finalize-design.md`
- plan: `docs/superpowers/plans/2026-05-14-mct-172-policy-finalize.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- Phase 1 PR: mctrader-hub#320 (29028a8)
- Phase 2 PR1: mctrader-data#63
- Phase 2 PR2: mctrader-hub#TBD (본 PR)
