---
type: domain-knowledge
domain: governance
title: Evidence Triad VERIFIED Badge
adr_cross_ref: ADR-032
first_application: "MCT-189 §8.5 (hub#363 ccacdce 2026-05-17)"
created_at: "2026-05-17"
author: MCT-190
---

# Evidence Triad VERIFIED Badge (ADR-032 carrier)

> **SSOT**: ADR-032 §3 Evidence Triad Rule v1 (Proposed 2026-05-17, MCT-190 publish).
> 본 페이지 = 일반 evidence triad rule 의 domain-knowledge SSOT. domain-specific 사례
> (MCT-189 grace-0 wiring 등) 는 각 도메인 페이지 보존, 본 페이지로 cross-ref.
> **decision-defined vs caller-wired 분리 invariant** — VERIFIED badge 박제는 두 LAND
> 시점 모두 evidence 의무 (정의 LAND ≠ 운영 LAND).

## §1 Concept (3 evidence 정의)

VERIFIED badge 1개 충족 = 아래 3 evidence 모두 박제 의무. 하나라도 결락 시 badge 박제 금지.

### (1) file:line citation — 정의 위치 박제

function / class / section 정의 위치를 `<path>:<line_start>-<line_end>` 형식으로 박제.

예시: `mctrader-data/src/mctrader_data/compactor/promotion.py:95-180`

목적: decision-defined 측 산출물의 SSOT 위치 명시. ADR / Story / Change Plan 어느 layer
에서든 동일 형식 강제.

### (2) production caller `git grep` ≥ 1 — wiring proof

dead-in-prod (test-only / deprecated / 정의만 LAND 된 후 caller 0건) 회피 의무. test/ 경로
제외하여 production caller 만 grep:

```bash
git grep -nE "<symbol>" -- ':!tests/' ':!src/**/test_*' src/
```

caller 0건 = caller-wired LAND 부재 = VERIFIED badge 박제 금지 (decision-defined LAND 만
박제 후 wiring 별 Story carry over 명시 의무).

### (3) integration test PASS — 실 경로 evidence

unit test 만으로 미흡 — boundary 통과 evidence 의무. testcontainers MinIO 류 외부 의존
포함 시 더 강한 evidence. 최소 1개 integration test 가 해당 caller 경로를 실행하고
PASS 해야 badge 박제 가능.

## §2 Caller guide (production caller grep 명령 예시)

**function caller grep**:

```bash
git grep -nE "promote_l1\(|_promote_after_nas_put" -- src/
```

**class caller grep**:

```bash
git grep -nE "DualWriter\(\)|InvariantHarness\(\)" -- src/
```

**dead-in-prod 판정 — test/ 경로 제외**:

```bash
git grep -nE "<symbol>" -- ':!tests/' ':!src/**/test_*' src/
```

grep 결과 ≥ 1 이면 caller-wired evidence 충족. 0 = dead-in-prod 판정 (VERIFIED badge 차단).

## §3 decision-defined vs caller-wired 분리 invariant

Michael Nygard ADR 원본 ("Documenting Architecture Decisions", 2011) 정합 — "Accepted"
status = 결정 채택 (decision-defined), "Implemented" status = production 실배선
(caller-wired). 두 LAND 시점 분리 가능 (정의 LAND ≠ 운영 LAND).

ADR-032 evidence triad = "Implemented" status 의 mechanical 박제 forcing function —
caller grep ≥ 1 + integration test PASS 로 caller-wired evidence 동시 박제.

**실증 사례 — MCT-169 → MCT-189 (3일 caller-wired LAND 지연)**:

- MCT-169 (2026-05-14) D3=C "VERIFIED" 박제 — decision-defined LAND
- 그러나 `promote_l1()` production caller 0건 — caller-wired LAND 부재
- 결과: 130 GB legacy Parquet 영구 누적 (2026-05-16 운영 진단 trigger, cross-document
  SSOT drift 2호)
- 해소: MCT-189 (2026-05-17) 4 PR sequential LAND — caller-wired LAND 완결
  (`DualWriter._promote_after_nas_put` + `runner.scan_and_cleanup_legacy` +
  `promotion` self = 3+ caller)

본 사례 = ADR-032 evidence triad 도입 motivation 직접 원인. "VERIFIED" badge 가 decision
LAND 만으로 박제될 수 있는 governance gap 이 130 GB 누적의 root cause.

## §4 적용 사례 (current + future)

**현재 (2026-05-17 시점)**:

- **MCT-189 §8.5** — ADR-029 §D3 evidence triad 첫 적용. file:line `promote_l1`
  `promotion.py:95-180` + caller grep 3+ (DualWriter / runner / promotion self) +
  13 integration test PASS (testcontainers MinIO 실 경로)

**future (MCT-191+ reapply 시점부터 누적)**:

- 모든 Story `scope_manifest` `verify_evidence` row 의무 (ADR-032 §3.1.1 SSOT)
- 모든 Story §11 LAND timeline 박제 의무 (ADR-032 §3.1.2)
- 모든 Story PMO-AUDIT §lane gate 전수 검증 row (ADR-032 §3.1.3)

## §5 cross-ref

- **ADR-032** (decision SSOT, `docs/adr/ADR-032-verified-badge-evidence-triad.md`)
- **`docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`** (첫 evidence
  triad 박제 사례 — MCT-189 LAND 시 작성. domain-specific knowledge 보존, 일반 evidence
  triad rule = 본 페이지 SSOT 로 transition)
- **plugin-codeforge#804** (박제 PR completeness CI gate, ADR-032 §3.1 mechanical 대체 carry)
- **plugin-codeforge#805** (post-merge audit lane, ADR-032 §3.1.3 자동화 carry)
- **`docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`**
  (cross-document SSOT drift 2호 — 본 evidence triad 도입의 motivation trigger)
