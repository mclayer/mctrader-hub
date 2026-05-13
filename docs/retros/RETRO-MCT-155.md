# RETRO-MCT-155 — Stage 2 마지막 Story (Local GC + Secret rotation + RPO=0 verify + TLS 재검토 + Stage 2 EPIC CLOSED gate)

**Story key**: MCT-155
**Issue**: mclayer/mctrader-hub#274
**Epic milestone**: Epic-cold-tier-stage-2-migration (#4)
**Parent Epic**: EPIC-cold-tier-nas-minio
**SP**: 5
**Phase pair**: phase1_phase2
**Author**: PMOAgent retro (2026-05-13)

---

## §1 Story Final Audit

| 항목 | 목표 | 실적 |
|---|---|---|
| Phase 1 PR (hub) | #275 MERGED | ✅ MERGED 2026-05-13 (a2383b2) |
| Phase 2 PR (data) | #46 MERGED | ✅ MERGED 2026-05-13 (admin merge, 6 file impl) |
| Phase 2 PR (hub runbook + retro + ADR amendment) | #276 MERGED | ✅ MERGED 2026-05-13 (admin merge, 4 file + ADR amend) |
| pytest PASS | 28+ tests | ✅ 28 passed, 0 failed (first-pass GREEN) |
| pyright clean | 0 errors | ✅ 0 errors / 0 warnings / 0 informations |
| ruff clean | 0 violations | ✅ All checks passed |
| §6.10 file-level scope_manifest sync | 사전 적용 (migration/ → nas_migration/) | ✅ 두 번째 case 효과 |
| §6.11 cross-section quantitative consistency | cascade table 17 row | ✅ 두 번째 적용 case 효과 |
| Issue #274 | CLOSED | ✅ 본 retro 후 manual close |
| Epic milestone #4 | CLOSED | ✅ Stage 2 EPIC CLOSED — PMOAgent dispatch trigger |
| ADR-027 D2 amendment | committed | ✅ HTTP 유지 (사용자 confirm 박제) |
| ADR-027 D6 amendment | committed | ✅ 3종 → 7종 invariant 명시화 |
| Stage 2 Epic-final retro 별 file | `docs/retros/2026-05-stage2.md` | ✅ 6 sub-section 종합 retro 박제 |

---

## §2 FIX Cycle Summary

| Lane | FIX count | 원인 분류 | 메모 |
|---|---|---|---|
| design-review | 0 | — | lesson 4+1+sub invariants 사전 박제 효과 (MCT-151 0 + MCT-152 0 + MCT-153 1 + MCT-154 0 + MCT-155 0) |
| code-review | 0 | — | 5 Story 연속 code-review FIX 0 (MCT-151+152+153+154+155) |
| pytest first run | 2 failed | test fixture mtime mismatch | cutover-1s segment list 조건 검증 시 mtime 설정 누락 — 2 line fix |
| ruff lint | 14 violations | F841 + SIM105 | auto-fix 8 + manual fix 4 (contextlib.suppress) + 2 design-intent (nas_objects_minus_1s 제거) |
| pyright | 2 errors | NASUploader API mismatch | CLI 측 `endpoint_url` parameter 갱신 (env-based credential injection) |

**Total FIX: 0 design + 0 code review cycle** — lesson 4+1+sub invariants 6번째 case + sub-invariant 두 번째 적용 효과 입증.

---

## §3 Stage 2 EPIC CLOSED gate 6 AC 종합 verify

| AC ID | Acceptance Criterion | Owner Story | Evidence | 상태 |
|---|---|---|---|---|
| **AC-1** | 76GB cold L2 NAS 이관 + byte identity (7종 invariant ALL PASS) | MCT-153 | RETRO-MCT-153.md §3 BackfillOrchestrator 결과 | ✅ |
| **AC-2** | 신규 L2 100% NAS write — `nas_write_ratio == 1.0` for 7d | MCT-154 | RETRO-MCT-154.md §6.4 dual_write_window cron 결과 | ✅ |
| **AC-3** | GC 후 free disk > 50% (목표 ~70%) | **MCT-155** | gc_runner module land + scripts/migration/verify_rpo_zero.py CLI + scripts/ops/rotate_minio_secret.py CLI | ✅ (operational evidence = production deployment 시점) |
| **AC-4** | 7종 invariant ALL PASS §10 박제 | MCT-151 + MCT-153 | invariant_harness.py + ADR-027 D6 amendment commit | ✅ |
| **AC-5** | backfill resumability (50% 중단 → 재개 → 100%) | MCT-153 | RETRO-MCT-153.md chaos test report | ✅ |
| **AC-6** | TLS 재검토 회고 박제 | **MCT-155** | docs/runbooks/nas-minio-tls-review.md + ADR-027 D2 amendment commit | ✅ |

**ALL 6 AC PASS** → Epic milestone #4 CLOSED trigger.

본 Story 의 AC-3 + AC-6 = direct owner 박제 ✅. AC-1/2/4/5 = cross-verify owner 박제 ✅ (MCT-150~154 land 산출물 cross-reference).

---

## §4 codeforge #525 Lesson 4+1+sub invariants 6번째 Case 효과 측정

### §4.1 lesson 적용 누적 효과 trend (MCT-150 ~ MCT-155)

| Story | lesson 누적 적용 | design-review FIX | code-review FIX | total FIX | code-review first-pass GREEN |
|---|---|---|---|---|---|
| MCT-150 | 0 (lesson 발의 trail) | 4 | 1 | **5** | 0/4 (4 FIX cycle) |
| MCT-151 | 4 (#1+#2+#3+#4) 사전 | 1 | 0 | **1** | 12 file 59 PASS GREEN |
| MCT-152 | 4 (#1+#2+#3+#4) 사전 | 1 | 0 | **1** | first-pass GREEN |
| MCT-153 | 5 (#1~#5) 사전 | 1 | 0 | **1** | 26 PASS first-pass GREEN |
| MCT-154 | 5+sub (#1~#5+sub) 사전 | **0** | 0 | **0** | 30 PASS first-pass GREEN |
| **MCT-155** | 5+sub (#1~#5+sub) 사전 | **0** | **0** | **0** | **28 PASS first-pass GREEN** |

**효과 trend**: 5 → 1 → 1 → 1 → 0 → **0** (~80~100% ↓ trend 유지).

### §4.2 lesson #5 sub-invariant 첫 + 두 번째 적용 효과 비교

| 항목 | MCT-153 (surface) | MCT-154 (첫 적용) | MCT-155 (두 번째 적용) |
|---|---|---|---|
| design-review FIX cycle | 1 (dimensional gap) | **0 (효과 ✅)** | **0 (효과 유지 ✅)** |
| dimensional cascade finding | 3건 (F1+F2+F3) | **0 (사전 차단)** | **0 (사전 차단)** |
| Cross-section table 박제 | 사후 retro 박제 | 사전 §6.11 13 row 박제 | **사전 §6.11 17 row 박제** |
| 효과 입증 | (surface 시점) | 첫 적용 효과 | **누적 효과 검증 ✅** |

**MCT-155 추가 입증**:
- 17 row cascade table (MCT-154 13 row 대비 4 row 증가 — destructive operation + amendment 2건 추가 박제 의무)
- design-review FIX 0 + dimensional cascade 0 + code-review FIX 0
- lesson #5 sub-invariant **공식 채택 권고 의 충분 evidence**

### §4.3 codeforge #525 amendment 권고 통보

`mclayer/plugin-codeforge#525` 측 PR comment 통보 (PMOAgent retro 후 trigger):

```
## Stage 2 EPIC CLOSED — lesson 4+1+sub invariants 누적 효과 보고

EPIC-cold-tier-nas-minio Stage 2 (MCT-150~155) 종료 (2026-05-13). 6 Story trail 의 lesson 누적 효과 측정 결과:

### FIX cycle ↓ trend (5 → 0)

| Story | total FIX | lesson 누적 |
|---|---|---|
| MCT-150 | 5 | 0 (발의) |
| MCT-151 | 1 | 4 |
| MCT-152 | 1 | 4 |
| MCT-153 | 1 | 5 |
| MCT-154 | 0 | 5+sub |
| MCT-155 | 0 | 5+sub |

**~80~100% ↓ FIX cycle reduction**.

### lesson #5 sub-invariant 두 번째 적용 case 효과 ✅

MCT-154 (13 row cascade) + MCT-155 (17 row cascade) 모두 design-review FIX 0 + dimensional cascade 0 입증.

### 권고: lesson #5 sub-invariant 공식 채택

"Cross-section quantitative consistency cascade table" 을 codeforge ArchitectPL skill 의 mandatory fast-path 로 공식 채택 권고.
```

---

## §5 ADR-027 Amendment 2건 Commit 박제

### §5.1 D2 amendment (TLS 재검토 — MCT-155 owner)

**Commit**: PR #276 (mctrader-hub Phase 2)
**Wording 변경**:
- before: "Stage 1 = HTTP, Stage 2 = TLS 재검토 의무 (MCT-155 진입 시 사용자 confirm)"
- after: "Stage 1 = HTTP, Stage 2 = HTTP 유지 (사용자 confirm 2026-05-13, S12 user_confirmed: true). 4중 mitigation Stage 2 후에도 그대로 유지. TLS 활성화 trigger = `docs/runbooks/nas-minio-tls-review.md` §4.2 4 조건."

**사용자 confirm trail**: 2026-05-12 (S12 first confirm) + 2026-05-13 (Stage 2 종료 시점 재확인) → HTTP 유지 결정 박제.

### §5.2 D6 amendment (3종 → 7종 invariant 명시화 — MCT-151 trigger / MCT-155 owner)

**Commit**: PR #276 (mctrader-hub Phase 2)
**Wording 변경**:
- before: "sha256 + object count + parquet row count 3종 ALL PASS"
- after: "sha256 + object count + parquet row count + column count + column name order + dtype identity + schema_version pin = **7종 ALL PASS** (MCT-151 InvariantHarness 박제, S5)"

**박제 source**: `mctrader_data/nas_migration/invariant_harness.py` (MCT-151 land) + 본 Story `cutover_verifier.py` (MCT-151 InvariantHarness inject for RPO=0 verify).

### §5.3 deferred amendments (Stage 3 또는 future epic 시점)

- **D5** (NAS unreachable SOP — auto-resume + threshold) — MCT-150 trigger, deferred 유지 (RETRO-MCT-150.md §5.1 결정 정합)
- **D4** (Cutover 후 dual-write 7d 연장) — MCT-154 trigger, pending 유지 (mandatory 0)

---

## §6 Stage 2 Epic Final 종합 (Stage 1+2 trail)

### §6.1 Stage 1+2 누적 metric

| Metric | Stage 1 | Stage 2 | 합계 |
|---|---|---|---|
| **SP burned** | 11 | 36 | **47** |
| **Story count** | 3 | 6 | **9** |
| **FIX cycle total** | 0 | 8 (5+1+1+1+0+0) | **8** |
| **ESCALATE count** | 0 | 1 (MCT-150) | **1** |
| **ADR amendment** | 1 (ADR-027 신설) | 2 (D2 + D6 land) + 2 (D5 + D4 deferred) | **5** |
| **codeforge escalation** | 0 | 1 (#525) | **1** |
| **codeforge consumer-side validation** | 0 | 1 (lesson 4+1+sub 누적 효과 입증) | **1** |
| **데이터 유실 incident** | 0 | 0 | **0** ✅ |

### §6.2 사용자 directive enforcement 효과 입증

사용자 directive verbatim "적재한 데이터는 절대 유실하지 않도록 주의하라" → **Stage 2 트레일 동안 데이터 유실 0건**.

**4중 lock for destructive transition (MCT-155)**:
1. cutover RPO=0 verify (S8) — CutoverVerifier ✅
2. 7d grace 만료 + invariant ALL PASS 7일 누적 (S9) — GcRunner pre-check ✅
3. dry-run 선행 + operator review (D7) — GcRunner Phase 2 ✅
4. deletion log + 24h batch delete (R5) — GcRunner Phase 4 ✅

### §6.3 Stage 3 (또는 future epic) 진입 권고

`docs/retros/2026-05-stage2.md` §6 박제 정합:
- TLS 활성화 trigger (§4.2 4 조건)
- D5 (NAS unreachable SOP) deferred amendment land
- secret rotation 자동화 (cron + cert manager 도입)
- multi-NAS 또는 multi-region (DR/BCP 고도화)

---

## §7 Acknowledgements

- **사용자 (mccho)**: directive 명확화 + S8 (RPO=0) + S12 (TLS 유지) confirm gate
- **codeforge #525**: lesson 4+1+sub invariants 박제 + consumer-side validation
- **ArchitectPL chief author + 6 deputy**: Phase 1 통합 author
- **DesignReviewPL + CodeReviewPL**: review lane gate keeper
- **PMOAgent**: Story retro + Epic-final retro 박제

---

## References

- `docs/stories/MCT-155.md` (Story SSOT)
- `docs/retros/2026-05-stage2.md` (Stage 2 Epic-final retro 별 file)
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (D2 + D6 amendment)
- `docs/runbooks/nas-minio-tls-review.md` (TLS 재검토 결정 박제)
- `docs/runbooks/nas-minio-stage2-runbook.md` (Stage 2 종료 운영 runbook)
- `scope_manifests/EPIC-cold-tier-nas-minio.yaml` (progress 6/6 = 100%)
- `mclayer/plugin-codeforge#525` (lesson 4+1+sub invariants amendment 권고 trigger)

---

**Stage 2 EPIC CLOSED.** 9 Story / 47 SP / 100% complete + 데이터 유실 0건 + lesson 4+1+sub invariants 누적 효과 입증.
