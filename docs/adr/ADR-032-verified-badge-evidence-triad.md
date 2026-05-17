---
adr_key: ADR-032
title: VERIFIED Badge Evidence Triad
status: Accepted
class: governance
proposed_at: "2026-05-16"
accepted_at: "2026-05-17"
owner_story: MCT-190
first_application: "MCT-189 §8.5 Impl Manifest (hub#363 ccacdce 2026-05-17)"
amendments: []
cross_ref:
  - "ADR-029 §D3 (evidence triad 첫 적용 대상)"
  - "ADR-030 (MCT-179 reconcile 5회 사례)"
  - "ADR-031 (MCT-182 owner, 동일 governance singleton 패턴)"
  - "plugin-codeforge#804 (박제 PR completeness CI gate, §7 carry)"
  - "plugin-codeforge#805 (post-merge audit lane, §7 carry)"
  - "MCT-189 §9 (cross-Story PR contamination 첫 박제)"
---

# ADR-032 — VERIFIED Badge Evidence Triad

## §1 Status

**Accepted** (2026-05-17, MCT-190 LAND 시 Proposed → Accepted transition)

- **owner_story**: MCT-190 (cross-Epic governance singleton, PMO 발의 from `docs/retros/PMO-AUDIT-MCT-189.md` §4.2)
- **first_application**: MCT-189 §8.5 Impl Manifest (hub#363 ccacdce, 2026-05-17). decision-defined evidence + caller-wired evidence + integration test 13 시나리오 PASS 3종 evidence 동시 박제 첫 사례.

## §2 Context — Trigger 3 사례 분석

3 사례 종합 = "badge SSOT ↔ 실 SSOT forcing function 부재" 의 3 layer 확장 (operational evidence ≠ policy LAND date / design SSOT ≠ code SSOT / PR title ≠ 박제 산출물 SSOT).

### §2.1 Trigger #1 — MCT-189 D3=C wiring drift (decision-defined LAND ≠ caller-wired LAND)

| 단계 | 내용 |
|------|------|
| **가설** | MCT-169 D3=C "NAS HEAD verify → grace-0 local delete" VERIFIED 박제 (2026-05-14) → production runtime 정합 |
| **실측** | 2026-05-16 운영 진단 (production 디스크 압박 보고) — `git grep promote_l1\(` 결과 **caller 0건** |
| **영향** | 130 GB legacy Parquet 영구 누적 (forward-only invariant 위반, 2일 production 결함 운영) |
| **정정** | MCT-189 4 PR sequential LAND (hub#357 3f138a6 + data#73 de12f43 + data#75 a1a8ccf + hub#363 ccacdce, 2026-05-16~17) + ADR-029 §MCT-189 amendment box VERIFIED |

**핵심**: VERIFIED badge 박제 시점 (decision-defined LAND) ≠ production caller LAND 시점 (caller-wired LAND). 두 LAND 분리 가능 — evidence triad 부재 시 silent failure (130GB 누적).

### §2.2 Trigger #2 — MCT-179 ADR-030 Out-of-scope reconcile (design SSOT ≠ scope_manifest SSOT)

| 단계 | 내용 |
|------|------|
| **가설** | ADR-030 §Out-of-scope D5/D8 정의 정합 → cross-document SSOT 정합 |
| **실측** | DesignReview iter1 P0 — ADR-030 §Out-of-scope D5/D8 정의 swap stale (scope_manifest §design_decisions SSOT 와 D1-D19 전체 row swap stale) |
| **영향** | cross-document SSOT desync 5회 누적 (MCT-178 F-001 swap 동형 누적), MCT-180/181 재발 risk |
| **정정** | ArchitectPL 전수 reconcile commit c8e4b8e (D1-D19 SSOT 1:1 정합). MCT-180/181 design P0×0 회수 (lesson reapply 누적 효과 1회 실증) |

**핵심**: design SSOT (ADR) 와 scope_manifest SSOT 분리 — cross-document mechanical reconcile gate 부재 시 누적 drift. plugin-codeforge#795 (cross-document SSOT mechanical reconcile gate, design lane) escalation 발의 근거.

### §2.3 Trigger #3 — MCT-184 박제 PR incomplete (PR title SSOT ≠ 박제 산출물 SSOT)

| 단계 | 내용 |
|------|------|
| **가설** | PR title "Phase 2 PR2 박제 milestone 3/7" = 박제 SSOT (의무 산출물 완결) |
| **실측** | hub#359 MERGED 후 박제 산출물 12 의무 항목 중 5 처리 (≈42%) — RETRO 부재 + EPIC-RESULTS §Story-3 부재 + frontmatter status 미전환 + F-3 hub#TBD 잔존 |
| **영향** | 박제 SSOT divergence window 28분 발생 (hub#359 → hub#360 별 amendment 시간) |
| **정정** | hub#360 별 amendment PR (fa7ea64, 2026-05-16T15:19:39Z). plugin-codeforge#804 (박제 PR completeness CI gate) ADR escalation 발의 |

**핵심**: PR title 만으로는 박제 산출물 완결 보장 불가. 박제 PR auto-classification + 의무 산출물 grep gate 필요 (mechanical forcing function).

## §3 Decision — Evidence Triad Rule v1

VERIFIED badge 박제 시 다음 **3 evidence 동시 박제 의무**:

### §3.0 Evidence 3종 정의

1. **file:line citation** — function/class/section 정의 위치 박제 (**decision-defined evidence**)
   - 형식: `<path>:<line_start>-<line_end>` (예: `mctrader-data/src/mctrader_data/compactor/promotion.py:95-180`)
   - 의의: ADR/decision 의 production code anchor 박제 — 변경 시 cross-ref 추적 가능

2. **production caller `git grep` ≥ 1** — wiring proof (**caller-wired evidence**)
   - 명령: `git grep -nE "<symbol>" -- ':!tests/' ':!src/**/test_*' src/`
   - 의의: dead-in-prod (test-only / deprecated code path) 회피. caller 0건 = silent wiring drift 발견 (MCT-189 130GB 누적 실증)

3. **integration test PASS** — 실 경로 evidence
   - 형식: `tests/integration/test_*.py N 시나리오 ALL PASS` (testcontainers 외부 의존 포함 시 더 강한 evidence)
   - 의의: unit test 만으로 미흡 — boundary 통과 evidence 의무. integration test = caller-wired evidence 와 함께 production wiring 완결 박제

### §3.1 decision-defined ≠ caller-wired 분리 (Michael Nygard ADR 원본 정합)

Michael Nygard "Documenting Architecture Decisions" (2011) 정합:
- **"Accepted"** status = 결정 채택 (decision-defined evidence). 의사결정 완결.
- **"Implemented"** status = production 실배선 (caller-wired evidence). 두 LAND 시점 분리 가능 (정의 LAND ≠ 운영 LAND).

ADR-032 evidence triad = **"Implemented" status 의 mechanical 박제 forcing function** — caller grep ≥1 + integration test PASS 로 caller-wired evidence 동시 박제.

**실증 사례**:
- MCT-169 (2026-05-14) D3=C "VERIFIED" 박제 — decision-defined LAND
- 그러나 `promote_l1()` production caller 0건 — caller-wired LAND 부재
- 결과: 130 GB legacy Parquet 영구 누적 (§2.1 trigger #1)
- 해소: MCT-189 (2026-05-17) 4 PR sequential LAND — caller-wired LAND 완결 (3+ caller)

### §3.2 Evidence Quad Rule v2 (triad superset)

triad v1 (§3) + 4번째 게이트: **runtime telemetry counter ≥ 1 over N days** (production traffic 실 wiring evidence — Hyrum's Law 역방향 dead-in-prod false-negative 차단). Counter monotonicity wiring proof (Prometheus Counter ≠ Gauge).

quad v2 = `(file:line + production caller git grep ≥1 + integration test PASS) AND (runtime telemetry counter ≥ 1 over N days)`.

quad v2 enforcement layer 운영 = **ADR-033** (forward ref). class taxonomy (governance|production|mixed) + traffic class 차등 N days + grandfathering = ADR-033 §3/§4/§7.

triad v1 (§3) = governance ADR (class:governance) SSOT 유지 (telemetry counter forever 0 정상, §9 telemetry_counter_caveat). quad v2 = production ADR (class:production) 의무 (ADR-033 §7 grandfathering).

## §4 Enforcement Layer (3-tier, self-discipline gate v1)

CI mechanical gate = plugin-codeforge#804 amendment 의존 (§7 carry). v1 = self-discipline gate 3-tier:

### §4.1 scope_manifest `verify_evidence` schema 신규 frontmatter row

Story file 마다 ADR-N reapply 시 박제 row 의무 (scope_manifests/MCT-N.yaml):

```yaml
verify_evidence:
  - rule: "<ADR-N §M rule 설명>"
    decision_defined_evidence: "<file:line citation>"
    caller_wired_evidence: "<production caller git grep 결과 ≥ 1>"
    caller_wired_caveat: "<governance ADR 의 self-reference Caveat — 적용 시점 0건 → reapply 누적 명시 (해당 시)>"
    integration_test: "<test path 또는 N/A>"
    forcing_function: ["<Story §8.5 체크리스트>", "<PMO audit lane gate>"]
```

### §4.2 Story §11 LAND timeline 박제 의무

LAND PR 별로 (file:line + commit sha + integration test 결과) 박제. MCT-189 §11 LAND timeline 4 PR sequential 박제 = 선례 정합.

형식:
```markdown
| land_order | repo | PR | commit | git verify | 박제 내용 |
|-----------|------|----|--------|-----------|----------|
| 1 | <repo> | <PR#> | <sha> | <MERGED date> | <evidence triad 3종 cross-ref> |
```

### §4.3 PMO audit gate

PMO-AUDIT-*.md §lane gate 전수 검증 row — verify_evidence triad 의 3 evidence 동시 verify (MCT-189 §2 audit pattern 정합, PMOAgent self-write SSOT).

§2.4 (또는 동등 section) = ADR-032 evidence triad reapply 정합 verify table:

| Evidence | 박제 내용 | 검증 |
|----------|----------|------|
| (1) file:line | `<path>:<line>` | ✅ / ❌ |
| (2) production caller grep ≥1 | `git grep` = N caller | ✅ / ❌ |
| (3) integration test PASS | `tests/integration/test_*.py` N 시나리오 PASS | ✅ / ❌ |

## §5 Story §8.5 Impl Manifest 통합

§8.5 = evidence triad 3종 동시 박제 template. MCT-189 §8.5 첫 적용 사례:

| Evidence | 박제 내용 |
|----------|----------|
| (1) file:line | `mctrader-data/src/mctrader_data/compactor/promotion.py:95-180` (`promote_l1` 4중 verify) + caller `dual_writer.py:_promote_after_nas_put` + `runner.py:cycle_hook(scan_and_cleanup_legacy)` |
| (2) production caller grep | `git grep -nE "promote_l1\(|_promote_after_nas_put"` = **3+ caller** (MCT-169 시점 0건 → MCT-189 LAND 후 3+ caller, decision-defined → caller-wired 회복) |
| (3) integration test | `tests/integration/test_l1_grace0_local_delete.py` 13 시나리오 ALL PASS (data#73) + `tests/integration/test_scan_legacy_cleanup.py` 5 시나리오 ALL PASS (data#75) |

후속 Story 들이 §8.5 작성 시 본 template 정합 의무. PMO-AUDIT 가 §2.4 에 reapply 정합 verify.

## §6 Amendments (MCT-189 self-reference 적용)

### §6.1 caller code 의 spec FIX iter compliance 까지 evidence triad 확장

caller grep ≥1 만으로 **"caller code 가 spec FIX iter 통과한 정합 코드"** 미판단. §10 FIX Ledger resolution 필드 cross-ref 의무.

**MCT-189 사례** — F-1/F-2/F-3/F-4 spec FIX iter 4회 통과:
- F-1 spec compliance P0×2 + P1 + P2 (retry_queue enqueue + head_5xx + concurrent ENOENT + call_count) → resolution: `iter 1 commit 72c9aac`
- F-2 spec P2 test gap → resolution: `iter 2 commit 94f1219`
- F-3 code-quality P0×2 + P1×2 (sha256 TOCTOU + helper extraction) → resolution: `iter 3 commit 09ef2d0 → rebase a5d5a83`
- F-4 PR2 P1 + P2×3 + P3 (batch_limit + strict ==) → resolution: `iter 4 commit 7029f98`

→ caller LAND 시점 spec FIX iter pass evidence 박제 의무.

### §6.2 cross-Story PR scope guard

PR squash 내 commit message 의 Story key 추출 + PR title mismatch alert (plugin-codeforge#804 amendment 후보).

**MCT-184 data#71 contamination 사례** — mctrader-data origin/main `45e501c feat(MCT-184): data REST API 신규` commit 이 **partial MCT-189 commit 포함** → spec FIX iter1-3 부재 결함 main 일시 도달. PR review 가 squash 내용물 cross-Story scope 검증 부재.

**forcing function (self-discipline gate v1)**:
- parallel session worktree 격리 (memory `feedback_parallel_session_branch_race` 6 repo tier 차등 amendment, ADR-032 §6.2 cross-ref)
- PR squash scope 검증 (CI gate plugin-codeforge#804 carry)

## §7 Consequences / Cross-ref

**Positive**:
- decision-defined ≠ caller-wired 분리 invariant 박제 → silent wiring drift detection (MCT-189 130GB 누적 실증)
- 3-tier enforcement (scope_manifest + Story §11 + PMO audit) self-discipline gate v1 충분 (MCT-189 evidence)
- evidence triad reapply 누적 → future Story 자동 forcing function

**Negative**:
- 박제 의무 ↑ (Story §8.5 + scope_manifest verify_evidence + PMO-AUDIT §lane gate)
- CI mechanical gate 부재 (self-discipline gate v1 한계, plugin-codeforge#804 carry)
- governance ADR self-reference Caveat 의무 (false-positive fail risk, §9 mitigation)

**Cross-ref**:
- **ADR-029 §D3** (evidence triad 첫 적용 대상, MCT-189 §8.5)
- **ADR-030** (MCT-179 reconcile 5회 사례, §2.2 trigger #2)
- **ADR-031** (MCT-182 owner, 동일 governance singleton 패턴)
- **plugin-codeforge#804** (박제 PR completeness CI gate, §4 self-discipline gate v1 의 mechanical 대체)
- **plugin-codeforge#805** (post-merge audit lane, PMO-AUDIT-MCT-190 §3 consumer 적용)
- **MCT-189 §9** (cross-Story PR contamination 첫 박제, §6.2 self-reference trigger)
- **ADR-033** (evidence quad enforcement layer — §8.1 quad future-work 본문 격상 carrier + class taxonomy + grandfathering SSOT)

## §8 Future Work / Out of Scope (carry)

### §8.1 Evidence triad 4번째 게이트 — runtime telemetry counter (별 Story MCT-NNN owner)

Hyrum's Law 역방향 (dead-in-prod false-negative 차단) — caller grep ≥1 만으로 production wiring evidence 충분 아닌 경우 (dead-in-prod caller test-only/deprecated). runtime telemetry counter ≥ 1 over N days = 실 wiring evidence.

**triad v1 = 3 evidence 유지** (MCT-189 130GB legacy detection 실증 충분). **quad 확장 = ADR-033 §2 본문 격상 완료 (MCT-191 LAND)** — quad enforcement layer (class taxonomy + traffic class N days + grandfathering) = ADR-033 cross-ref. 본 §8.1 future-work → §3.2 본문 rule 격상 transition 완결.

### §8.2 CI mechanical gate (plugin-codeforge#804/#805 LAND 후 consumer 적용 carry)

self-discipline gate v1 = 3-tier (scope_manifest + Story §11 + PMO audit) 충분. plugin-codeforge#804 (박제 PR completeness CI gate) + #805 (post-merge audit lane) consumer 적용 = 별 Story (MCT-NNN reservation, plugin LAND 후 진입).

### §8.3 `docs/domain-knowledge/process/cross-story-pr-contamination.md` 신규 (별 Story)

cross-Story PR contamination pattern + 6 repo worktree 격리 + PR squash scope 검증 = process domain entry. governance domain 과 별 — 본 ADR-032 = governance singleton, process = 별 분류.

별 Story (MCT-NNN reservation, ADR-032 §6.2 implementation carry).

## §9 Self-reference Caveat (INV-1 forcing function)

본 ADR-032 자체 = ADR-032 evidence triad 적용 의무 (**meta-circular self-reference**).

scope_manifest `verify_evidence` row 의 caller_wired_caveat 필드 명시 의무:

```yaml
verify_evidence:
  - rule: "Evidence Triad Rule v1 정의 박제 (ADR-032 self-reference 첫 적용)"
    decision_defined_evidence: "docs/adr/ADR-032-verified-badge-evidence-triad.md §3"
    caller_wired_evidence: "MCT-190 LAND 시점 0건 (governance ADR singleton)"
    caller_wired_caveat: "self-reference Caveat — governance ADR 의 첫 publication 시점 caller_grep evidence 부재 정상. MCT-191+ Story scope_manifest verify_evidence row 에서 본 ADR-032 §3 rule 인용 시 누적 시작. false-positive fail 차단."
    integration_test: "N/A (governance ADR, code wiring 0)"
```

- `telemetry_counter_caveat`: governance ADR (class:governance) telemetry counter forever 0 정상 — ADR-033 §7 grandfathering (production-wired ADR만 quad 의무). false-positive fail 차단 INV (governance ADR singleton 의 quad verify gate 면제 = self-reference 첫 적용, MCT-191 본 Story). quad verify gate 가 governance ADR 자체를 telemetry 0 으로 fail 시키지 않음 (governance 시스템 자가붕괴 차단).

**INV-1 forcing function**: false-positive fail 차단 의무. 향후 governance ADR 신규 author 시 동일 Caveat pattern reapply. quad 확장 시에도 governance ADR self-reference Caveat 적용 (telemetry_counter_caveat) — false-positive fail 차단.
