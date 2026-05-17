---
adr_id: ADR-034
title: NAS Object Key Unification — 4-way split SSOT → single flat layout collapse
status: Accepted
date: 2026-05-17
related_story: U1-ADR (mctrader-data #87)
related_epic: EPIC-nas-key-unification (mctrader-data #86)
category: data
class: production
is_transitional: false
successor_of: []
complements:
  - ADR-027 (Cold Tier Object Storage on NAS MinIO — §D1 Hive prefix layout, §D6 7종 invariant)
  - ADR-029 (Cold tier governance v2 — NAS = SoT for ALL tiers)
amends:
  - ADR-027 §D1 (Bucket layout — single bucket + Hive prefix) — l1/ prefix sub-namespace 제거 박제 (cross-ref 추가)
  - ADR-017 §3 D3 (L1/L2/L3 tier layout) — NAS object key 의 tier sub-namespace 가 partition 컴포넌트 (`tier=L{1,2,3}/`) 로 충분, prefix 별도 불요 박제
references:
  - ADR-009 §D2 (16-col schema + Hive partition layout)
  - ADR-009 §D12 (forward-only invariant)
  - ADR-017 (Zero-loss ingestion via WAL + tiered compaction — §3 D2 channel matrix SSOT)
  - ADR-027 §D5 (L1 NAS upload 정책 — ADR-029 amendment 후 의무)
  - ADR-029 §D9 (NAS = SoT for ALL tiers)
  - ADR-031 (Data domain decoupling — Layer 2 mctrader-data SSOT)
related_stories:
  - U1-ADR (mctrader-data #87 — 본 ADR 본문 publish, Phase 2 Epic 진입 게이트)
  - U2-HELPER (mctrader-data #88 — 단일 helper SSOT impl, forward-fix, LAND 2026-05-18 + Amendment 1-4 carrier)
  - U3-MIGRATE (mctrader-data #89 — 기존 l1/ 객체 1회성 멱등 re-key 마이그레이션 + Amendment 5 carrier)
  - U4-XREPO (mctrader-data #90 — close, §결정 5 verbatim 박제)
  - U5-VERIFY (mctrader-data #91 — 통합 검증 + Phase 1 helper dead-code 회수 + forward-only invariant 박제)
prerequisite_stories:
  - WS-B (mctrader-data #84 — Phase 1 tactical helper `_resolve_legacy_nas_key` LAND 후 본 Epic 진입; U5 가 dead-code 회수)
  - MCT-161 (bucket versioning + Object Lock — U3 rollback 안전망)
  - MCT-173 (backfill mode + `.compacted` sentinel — U3 멱등 패턴 재사용)
amendment_history:
  - date: 2026-05-17
    author: ArchitectAgent (U2-HELPER chief author, mctrader-data#88)
    amended_adr: ADR-034 (mctrader-hub:docs/adr/ADR-034-nas-key-unification.md, Accepted PR #393 sha 8dbae415)
    scope:
      - "§결정 2 caller 표 4 rows → 6 rows (SSOT-5 + SSOT-6 흡수)"
      - "§결정 2 Public API 2+1 → 3+2 (build_nas_prefix 일반화 + build_legacy_l1_prefix §11.2-A Option A carrier)"
      - "§결정 2 keyword-only 의무 추가 (build_l1_prefix / build_nas_prefix / build_legacy_l1_prefix)"
      - "§결정 3 wording 정정 (reader fallback 실질 영역 = L2 compactor SSOT-4 GET 측 dual-prefix list union)"
      - "전 caller 표 line number 정정 (WS-A #85 sha f2e2bc9 post-merge)"
      - "§Monitoring cardinality 갱신 (4 → 6 caller, active 10 / max 18)"
      - "(FIX iteration 1) Amendment 3 verification 표에 MCT-159 Issue 2 (l2.py:44 unchanged) row 추가 — F-codex-5 박제"
    reason: |
      U2-HELPER Story 진행 중 Orchestrator + chief author Verify-via 발견:
      (1) SSOT-5 (runner.py:448 _historical_dual_write WS-A historical promotion path)
          — byte-equivalent to SSOT-2, 4 deputy 만장일치 흡수.
      (2) SSOT-6 (l3.py:153-156 L3Compactor._compact_day_nas L2 GET source) —
          Refactor §5 일반화 advocacy + L3Compactor production active verified.
      (3) §결정 3 wording "reader fallback" 의 실질 영역 박제.
      (4) Line number 정정 — WS-A #85 (sha f2e2bc9, merged 2026-05-14) 가 ADR-034 publish 직전 ~25 lines 삽입.
      (FIX iteration 1) DesignReview Codex F-codex-5 + F-codex-7 박제.
      Codex consult result: codex_check_no_findings (P0/P1 0). 4 deputy 만장일치.
    related_story: U2-HELPER (mctrader-data#88)
    related_change_plan: mctrader-data:docs/change-plans/U2-HELPER.md
    convergence: "4 deputy unanimous + chief author Verify-via + Codex consult no_findings"
    phase_3_verdict: "PASS — mechanical/boundary/dimensional 3 boolean self-check 모두 PASS, findings=[]"
    design_review_verdict: "PASS (FIX iteration 1 RESOLVED, 14 of 14 findings inline 해소, DesignReviewPL lighter re-verify confirmed)"
  - date: 2026-05-18
    author: ArchitectAgent (U3-MIGRATE chief author, mctrader-data#89)
    amended_adr: ADR-034 (mctrader-hub:docs/adr/ADR-034-nas-key-unification.md, Accepted PR #393 sha 8dbae415 + Amendment 1-4 LAND PR #395 sha 4c973849)
    scope:
      - "§결정 4 #4 Manifest YAML filename wording 정정 (rekey-manifest- → rekey-l1-manifest-, tier scope clarity 박제)"
    reason: |
      U3-MIGRATE Story §3.4 + DataMigrationArchitectAgent §wording drift primary advocacy + chief
      author 결정 결과 박제:
      (1) ADR-034 §결정 4 #4 current wording `<root>/audit/rekey-manifest-<exchange>-<channel>.yaml`
          (tier 미명시) = scope 모호. 본 Epic scope = L1 객체만 (Story §1 verbatim "기존 117 GB
          `l1/` 잔존 객체"). L2/L3 객체 = 이미 평면 (SSOT-2/SSOT-5 박제) → re-key 대상 아님.
      (2) Story §3.4 wording `<root>/audit/rekey-l1-manifest-<exchange>-<channel>.yaml` (tier 명시)
          = scope clarity 박제 — 향후 L2/L3 re-key 등 별 Story 시 file name 분리 가능
          (rekey-l2-manifest-* / rekey-l3-manifest-* 패턴 확장 박제).
      (3) MCT-173 BackfillManifest 패턴 = `backfill-manifest-<exchange>-<channel>.yaml` (tier
          미명시) — backfill 자체가 L1 scope only 이라 모호성 0. U3 는 future-proofing 의무
          (L2/L3 re-key 별 Story 가능성 박제).
      (4) DataMigrationArch §11.5 advocacy 채택 + chief author 결정 = Story §3.4 wording 유지 +
          ADR-034 본문 wording 정정 (본 Amendment 5 carrier).
      Codex consult result: codex_check_no_findings (P0/P1 0, debate-protocol-v1 v1.2 Round 0 미발동, Touchpoint #2 carry-over 미트리거).
    related_story: U3-MIGRATE (mctrader-data#89)
    related_change_plan: mctrader-data:docs/change-plans/U3-MIGRATE.md
    convergence: "DataMigrationArchitectAgent §wording drift primary advocacy + chief author 채택 결정 (Story §3.4 verbatim 채택 + ADR 본문 정정) + 6 deputy 통합 정합 + Codex consult no_findings"
    phase_3_verdict: "PASS — mechanical/boundary/dimensional 3 boolean self-check 모두 PASS (10 param: 6 VERIFIED + 4 PROVISIONAL [empirical-source: TBD]), findings=[], marketplace_sync_declared=false"
    design_review_verdict: "TBD (Phase 2 sibling docs PR LAND 후 DesignReview lane Codex consult)"
---

# ADR-034: NAS Object Key Unification — 4-way split SSOT → single flat layout collapse

## Status

Accepted — 2026-05-17. U1-ADR Story (`mctrader-data#87`, Phase 2 EPIC-nas-key-unification 전체 설계 SSOT) 가 본 ADR 본문을 publish. 본 ADR Accepted 시점 = Phase 2 Epic 의 후속 Story (U2-HELPER / U3-MIGRATE / U4-XREPO / U5-VERIFY) 진입 게이트.

**Amendment (2026-05-17)**: U2-HELPER chief author synthesis 결과 amendment_history 박제 — 본문 §결정 2 / §결정 3 / §Monitoring 영역의 현행 운영 wording 은 **본 ADR 말미 `## Amendments — U2-HELPER chief author (2026-05-17)` 섹션** 우선 인용 (Amendment 1-4 verbatim).

**Amendment (2026-05-18)**: U3-MIGRATE chief author synthesis 결과 amendment_history 박제 — 본문 §결정 4 #4 Manifest YAML filename wording 의 현행 운영 wording 은 **본 ADR 말미 `## Amendments — U3-MIGRATE chief author (2026-05-18)` 섹션** 우선 인용 (Amendment 5 verbatim).

**Stage 1 (사전 박제)**: Phase 1 WS-B (`mctrader-data#84` open, `_resolve_legacy_nas_key` helper 임시 도입) = 본 Epic 의 stepping stone. WS-B LAND 후 본 Epic 진입 → U5 가 WS-B helper dead-code 회수.

## 해소 기준

**해소 조건 = U5-VERIFY LAND + 4 invariant 박제 grep gate green**:

1. INV-1 (단일 helper SSOT) — `tests/integration/test_nas_key_ssot.py` 가 nas_key 산출 분산점 grep 가드, helper import 외 `"l1/"` literal 직접 사용 0
2. INV-2 (forward-only) — repo-wide grep `_resolve_legacy_nas_key` 정의/호출 0
3. INV-6 (dual-read fallback 제거) — reader 의 `l1/` HEAD fallback 코드 경로 0 (grep gate)
4. INV-7 (마이그레이션 완료) — `l1/` prefix 잔존 NAS object 0 (NAS bucket 실측 + per-partition `.rekey-completed` sentinel 전수 박제)

본 ADR 자체 = permanent policy. 위 4 invariant 박제 후 본 ADR 의 dual-read 윈도우 (§결정 3) 가 종료 — fallback 코드 회수 완료 상태로 영구 운영. 후속 NAS key layout 변경 시점은 별 ADR (successor) 로 처리.

## Context

(Context section 본문 unchanged — see Amendment 1-4 for SSOT-5/SSOT-6 발견 박제 및 reader-side / cross-repo isolation invariant)

상세 Context = U2-HELPER Amendment 1 박제 (Ground Truth 6 SSOT, Reader-side disjoint, Cross-repo isolation engine=candles only).

## Decision

### §결정 1 — 목표 스킴: 전 tier 단일 평면 SSOT

**확정 layout** (`l1/` prefix 제거):

```
market/<channel>/schema_version=<ver>/tier=L{1,2,3}/exchange=<ex>/symbol=<sym>/date=<YYYY-MM-DD>/[hour=<HH>/][node=<NODE>/]part-<name>.parquet
```

(Rationale + Alternative — see U1-ADR original publish)

### §결정 2 — 단일 helper SSOT

> **AMENDED (2026-05-17, U2-HELPER chief author)**: caller 표 4 rows → 6 rows + Public API 3 → 5 + keyword-only 의무 추가. 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 1` 우선 인용.

`src/mctrader_data/nas_storage/nas_key.py` 신규 module. 모든 nas_key 산출 = 본 helper 1곳 경유 (4 분산점 흡수; U2-HELPER amendment 후 6 분산점).

(Public API + Caller 흡수 plan = Amendment 1 section verbatim 인용)

### §결정 3 — Dual-read 전환 윈도우 + cutover sequence

> **AMENDED (2026-05-17, U2-HELPER chief author)**: "reader fallback" wording 정정 — 실질 영역 = L2 compactor `_l1_nas_source` (SSOT-4) GET 측 dual-prefix list union. data REST io/ reader 영역 변경 0 박제. 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 2` 우선 인용.

**Cutover ordering** (spec §5 verbatim, 본 ADR 이 정책 박제):

```
1. 본 ADR Accepted (dual-read 윈도우 + sequence 정의)
2. U2 코드 forward-fix land — 신규 PUT = 평면 / reader = dual-read fallback enabled
3. U4 cross-repo isolation 박제 (§결정 5 verbatim) — close 또는 axiom 박제
   U3 dry-run + copy + 4-HEAD verify (delete 보류)
4. cross-repo 회귀 전수 green → U3 old l1/ key delete 단계 진입
5. U5 통합 검증 + dual-read fallback 제거 + Phase 1 helper dead-code 회수 + forward-only invariant 박제
```

(Dual-read 윈도우 정의 = Amendment 2 section verbatim 인용)

### §결정 4 — 마이그레이션 안전 게이트 (4-HEAD verify)

> **AMENDED (2026-05-18, U3-MIGRATE chief author)**: §결정 4 #4 Manifest YAML filename wording 정정 — `rekey-manifest-` → `rekey-l1-manifest-` (tier scope clarity 박제). 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 5` 우선 인용.

U3-MIGRATE 의 `l1/` → 평면 1회성 re-key 마이그레이션 안전 정책:

1. **대상 = `.compacted` sentinel 완료 객체만** (active compactor 제외, MCT-173 INV-1/2 패턴 재사용 — source immutable 보장).
2. **3-step per-partition**:
   - **Step A copy**: boto3 `copy_object(CopySource={Bucket: mctrader-market, Key: l1/<old>}, Bucket: mctrader-market, Key: <new-flat>, MetadataDirective: "COPY")` — sha256 Metadata + ContentLength 정합 보존.
   - **Step B 4-HEAD verify** (ALL PASS 의무):
     - HEAD-1: ETag exact match (source vs target)
     - HEAD-2: VersionId 존재 (bucket versioning=Enabled 박제, MCT-161)
     - HEAD-3: sha256 Metadata 존재 + source/target 일치 (ADR-027 §D6 7종 invariant 정합)
     - HEAD-4: ContentLength exact match
   - **Step C delete**: 4-HEAD ALL PASS 후에만 boto3 `delete_object(Bucket: mctrader-market, Key: l1/<old>)`. 1-HEAD fail 시 delete 0 (source 보존, retry 가능).
3. **per-partition `.rekey-completed` sentinel**: `<root>/audit/rekey-sentinels/<exchange>/<channel>/<partition_id>.completed` — 재실행 시 sentinel 발견 → skip + `mctrader_l1_rekey_skipped_already_migrated_total{exchange,channel}` Counter +1.
4. **BackfillManifest YAML 재사용** (MCT-173 INV-4 패턴): `<root>/audit/rekey-l1-manifest-<exchange>-<channel>.yaml` — per-partition status + ETag/sha256/VersionId/ContentLength 4-tuple 박제. (tier 명시 — 본 ADR scope = L1 객체만, 향후 L2/L3 re-key 별 Story 시 `rekey-l2-manifest-*` / `rekey-l3-manifest-*` 패턴 확장 박제)
5. **batch self-pacing**: `runner.py:347-348` 패턴 재사용 (batch_limit=500 / sweep). SLO: per-batch p99 < 60s, total cutover < 72h.

**Rollback 안전망** (bucket versioning + Phase 1 helper):

- bucket versioning=Enabled (MCT-161 LAND 박제) — re-key 후 issue 발견 시 boto3 `copy_object` from VersionId 로 old `l1/` 복원 가능.
- Phase 1 `_resolve_legacy_nas_key` helper (U5 회수 대기) 보존 — 회복 reader 임시 활성 가능 (rollback path).
- dual-read 윈도우 (§결정 3) = U5 완료 시점까지 reader 가 양쪽 호출 가능 → rollback 시 reader 변경 0.

**Rationale (R2 안전 게이트 — spec §5)**:

마이그레이션 중 in-flight compaction race — `.compacted` sentinel 완료 객체만 대상 + U2 선행 보장 (cutover step 2) 시 신규 PUT = 평면 → race 없음. source immutable until 4-HEAD ALL PASS.

### §결정 5 — Cross-repo isolation 박제 (engine = candles only)

(원본 unchanged — see U1-ADR publish + Amendment 박제)

### §결정 6 — Phase 1 helper 회수 + forward-only invariant 박제

(원본 unchanged — see U1-ADR publish)

## Alternatives

(원본 unchanged — Alt-1 ~ Alt-4)

## Consequences

(원본 unchanged — 긍정 / 부정 / Risk / Monitoring sections)

### Monitoring (Prometheus emit 의무)

> **AMENDED (2026-05-17, U2-HELPER chief author)**: Counter cardinality 갱신 — caller 4 → 6, active 10 / max 18. 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 4` 우선 인용.

U2/U3/U5 가 각자 implement:

- `mctrader_nas_key_helper_call_total{caller, tier}` Counter — helper 호출 횟수 (U2). Original: 4 caller. Amendment 4 후: 6 caller × 3 tier max, active cardinality = 10.
- `mctrader_l1_rekey_copied_total{exchange,channel}` Counter — U3 copy 성공
- `mctrader_l1_rekey_verified_total{exchange,channel,head_check}` Counter — U3 4-HEAD verify (head_check ∈ {etag, version_id, sha256, content_length})
- `mctrader_l1_rekey_deleted_total{exchange,channel}` Counter — U3 old key delete
- `mctrader_l1_rekey_skipped_already_migrated_total{exchange,channel}` Counter — U3 멱등 skip
- `mctrader_l1_rekey_partial_state_count` Gauge — copy != delete 발생 시 emit (O-R1 OpRiskArch surface)
- `mctrader_reader_dual_read_fallback_hit_total{tier}` Counter — reader dual-read fallback hit (윈도우 종료 시점 결정 metric)

Grafana alert 임계: `partial_state_count > 0` (P0) + `dual_read_fallback_hit > 0 after U5 land` (P0 — invariant 위반).

## Amendments — U2-HELPER chief author (2026-05-17)

(Amendment 1-4 본문 — U2-HELPER chief author synthesis 결과, hub#395 LAND sha 4c973849)

상세 본문 = U2-HELPER chief author 박제 (Amendment 1 caller 표 6 rows + Public API 3+2 / Amendment 2 §결정 3 wording 정정 / Amendment 3 line number + l2.py:44 disjoint pledge / Amendment 4 cardinality 10 active / max 18).

## Amendments — U3-MIGRATE chief author (2026-05-18)

> U3-MIGRATE (mctrader-data#89) Phase 2 chief author synthesis 결과 박제. 본문 §결정 4 #4 Manifest YAML filename wording 의 현행 운영 wording = 본 섹션 우선 인용.
> Convergence: DataMigrationArchitectAgent §wording drift primary advocacy + chief author 채택 결정 (Story §3.4 verbatim 채택 + ADR 본문 정정) + 6 deputy 통합 정합 (CodebaseMapper + Refactor + SecurityArch + OpRiskArch + TestContractArch + DataMigrationArch) + Codex consult `codex_check_no_findings` (debate-protocol-v1 v1.2 Round 0 미발동, Phase 0.5 blanket debate Touchpoint #2 carry-over 미트리거).

### Amendment 5 — §결정 4 #4 Manifest YAML filename wording 정정

**Trigger**: U3-MIGRATE Story §3.4 + DataMigrationArchitectAgent §wording drift primary advocacy + chief author 결정.

**Rationale**:
- ADR-034 §결정 4 #4 current wording `rekey-manifest-<exchange>-<channel>.yaml` = tier 미명시 → scope 모호 ("rekey-manifest-" = 어느 tier?).
- 본 Epic scope = L1 객체만 (Story §1 verbatim "기존 117 GB `l1/` 잔존 객체"). L2/L3 객체 = 이미 평면 (SSOT-2/SSOT-5 박제) → re-key 대상 아님.
- Story §3.4 wording `rekey-l1-manifest-` = scope clarity (tier 명시) + future-proofing (L2/L3 re-key 별 Story 가능성 박제 — `rekey-l2-manifest-` / `rekey-l3-manifest-` 패턴 확장).
- MCT-173 BackfillManifest 패턴 = `backfill-manifest-<exchange>-<channel>.yaml` (tier 미명시) — backfill 자체가 L1 scope only 이라 모호성 0. U3 는 future-proofing 의무.

**Current Manifest YAML filename wording 박제 (실질 영역)**:

본 ADR §결정 4 #4 Manifest YAML filename = **`<root>/audit/rekey-l1-manifest-<exchange>-<channel>.yaml`** (tier 명시 — 본 ADR scope = L1 객체만).

- 활성 시점: U3-MIGRATE (#89) Phase 2 cutover step 4 진입 시점
- 종료 시점: U5-VERIFY (#91) LAND + 30일 cool-down 종료 (script 자체 회수 시점)
- 확장 규약 (future-proofing): L2/L3 re-key 별 Story 발생 시 `rekey-l2-manifest-*` / `rekey-l3-manifest-*` 패턴 신설 박제

**Cross-Story carrier**:
- **U5-VERIFY (#91)**: grep gate `rekey-l1-manifest-` 단일 wording 박제 의무 (U5 lane verify)
- **future L2/L3 re-key 별 Story**: `rekey-l2-manifest-` / `rekey-l3-manifest-` 패턴 확장 박제

**convergence**: DataMigrationArchitectAgent §wording drift primary advocacy + chief author 채택 결정 (Story §3.4 verbatim 채택 + ADR 본문 정정 by Amendment 5).

**related_story**: U3-MIGRATE (mctrader-data#89)
**related_change_plan**: mctrader-data:docs/change-plans/U3-MIGRATE.md
**design_review_verdict**: TBD (Phase 2 sibling docs PR LAND 후 DesignReview lane Codex consult)

## References (cross-link)

### ADR carrier (본 ADR amends/complements)

- ADR-009 §D2 + §D12 — Hive partition layout + forward-only invariant
- ADR-017 §3 D2 (channel matrix SSOT) + §3 D3 (L1/L2/L3 tier layout)
- ADR-027 §D1 (Hive prefix layout) + §D6 (7종 invariant) + §D5 (L1 NAS upload — ADR-029 amend 후 의무)
- ADR-029 §D9 (NAS = SoT for ALL tiers)
- ADR-031 (Data domain decoupling — Layer 2 scope 박제)
- ADR-045 Amend5 §D-9 (Mandatory ADR trigger)
- ADR-054 (doc-only Story fast-path)
- ADR-052 Amendment 4 (mandatory Codex proactive check — U3 chief author §3 통합 직후 발동)
- ADR-068 Amendment 1 (dimensional empirical annotation — U3 PROVISIONAL [empirical-source: TBD] 4 row)

### Story SSOT

- U1-ADR `mctrader-data#87` — 본 ADR 본문 publish
- U2-HELPER `mctrader-data#88` — 단일 helper SSOT impl + Amendment 1-4 carrier (chief author) + FIX iteration 1 RESOLVED + LAND 2026-05-18 (PR #95 sha 4aa5483a)
- **U3-MIGRATE `mctrader-data#89`** — 1회성 멱등 re-key 마이그레이션 + **Amendment 5 carrier (chief author)** + Phase 2 cutover step 4 진입
- U4-XREPO `mctrader-data#90` — closed not_planned (§결정 5 cross-repo isolation 박제)
- U5-VERIFY `mctrader-data#91` — 통합 검증 + Phase 1 helper 회수
- EPIC `mctrader-data#86` — Phase 2 Epic 전체 SSOT

### Spec + Change Plan

- `mctrader-data:docs/superpowers/specs/2026-05-17-nas-key-unification-design.md` — brainstorm-complete spec, 본 ADR 의 출처
- `mctrader-data:docs/change-plans/U2-HELPER.md` — Amendment 1-4 evidence trail + FIX iteration 1 박제 (chief author)
- **`mctrader-data:docs/change-plans/U3-MIGRATE.md`** — **Amendment 5 evidence trail (chief author)** + 4-HEAD verify impl + Manifest YAML schema + IAM Option B + Container Option B

### 기존 ADR cross-ref (별 amendment scope)

- ADR-027 §D1 amendment box: "본 ADR §결정 1 cross-ref — `l1/` sub-namespace 제거, Hive prefix layout 단순화"
- ADR-029 §D9 amendment box: "본 ADR §결정 1 cross-ref — L1 ↔ L2/L3 key namespace 균질화"

위 cross-ref 추가는 본 ADR PR 의 ADR-027 동시 amendment 로 진행 (sibling sync).
