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
  - U4-XREPO (mctrader-data #90 — closed not_planned, §결정 5 verbatim 박제)
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
      (3) §결정 3 wording "reader fallback" 의 실질 영역 박제 — 3 source (CodebaseMapper §4
          + TestContractArch §6 + chief author Verify-via) 모두 src/mctrader_data/io/ 영역
          `"l1/"` literal 0 hits → 실제 fallback = L2 compactor (SSOT-4) GET 측 dual-prefix
          list union (§11.2-A Option A). data REST io/ reader 변경 0 박제.
      (4) Line number 정정 — WS-A #85 (sha f2e2bc9, merged 2026-05-14) 가 ADR-034 publish
          (2026-05-17) 직전 ~25 lines 삽입.
      (FIX iteration 1) DesignReview Codex F-codex-5 + F-codex-7 박제 — Amendment 3
      verification 표에 MCT-159 Issue 2 (forbidden l2.py:44) line-level disjoint pledge row
      추가 + amendment_history entry 에 amended_adr field 추가.
      Codex consult result: codex_check_no_findings (P0/P1 0). 4 deputy 만장일치.
    related_story: U2-HELPER (mctrader-data#88)
    related_change_plan: mctrader-data:docs/change-plans/U2-HELPER.md
    convergence: "4 deputy unanimous (CodebaseMapper + Refactor + SecurityArch + OpRiskArch + TestContractArch + DataMigrationArch) + chief author Verify-via (l3.py production active runner.py:54+521, minio_uploader deprecated 활성 caller 0) + Codex consult no_findings"
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
      Codex consult result: codex_check_no_findings (P0/P1 0, debate-protocol-v1 v1.2 Round 0 미발동, Phase 0.5 Touchpoint #2 carry-over 미트리거).
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

### WHY — 4 SSOT 분산으로 인한 반복 패치 루프 (사용자 직접 보고)

사용자 원문 (브레인스토밍 spec §1 verbatim):

> 단순 디렉터리 정리가 아니라, **tier별 NAS key 스킴 분산(현 4곳)으로 인한 반복 패치 루프를 구조적으로 종결**하는 것. 사용자 원문 뉘앙스("세 번 더 작업하게 하지 말고 이번에 제대로"): MCT-168/169/189/190 이 nas_key 를 반복 touch 했으나 매번 전술 패치 → 분산 SSOT 잔존 → 다음 작업이 또 같은 곳을 건드림. 사용자의 실제 필요 = **단일 SSOT + 기존 데이터 전량 정리 + 신규 수집 자동 통합 적재(forward-fix) + 부분 성공 상태 잔존 0**. 핵심 가치는 이동이 아니라 **재작업 영구 차단과 완결성 보증**.

**Mandatory ADR trigger (ADR-045 Amend5 §D-9 정합)**: MCT-168/169/189/190 동일 `nas_key` 영역 ≥2 touch — Mandatory ADR 의무.

### Ground Truth — 4 SSOT 분산점 (U2-HELPER amendment 후 6 분산점)

**Original (4 분산점)**:

| 항목 | 사실 | verified-via |
|---|---|---|
| **SSOT-1 (PUT L1)** | `put_l1()` `nas_key = "l1/" + rel.as_posix()` → `l1/market/<channel>/schema_version=*/tier=L1/…` | Read `src/mctrader_data/nas_storage/dual_writer.py:329-371` (line 371) |
| **SSOT-2 (PUT L2/L3)** | `_dispatch_dual_write()` `nas_key = str(parquet_path.relative_to(self._root))` 평면 → `market/<channel>/schema_version=*/tier=L{2,3}/…` | Read `src/mctrader_data/compactor/runner.py:255-285` (line 265) |
| **SSOT-3 (cleanup)** | `scan_and_cleanup_legacy()` `nas_key = str(rel).replace("\\", "/")` 평면 단일 → L1(=`l1/`) HEAD 404 → preserved (RC-2, 117 GB 미회수 유발) | Read `src/mctrader_data/compactor/runner.py:304-364` (line 350-351). Phase 1 WS-B (`mctrader-data#84` 진행 중) 가 `_resolve_legacy_nas_key` helper 로 tier-aware 임시 fix — U5 가 dead-code 회수 |
| **SSOT-4 (GET L1)** | `l2.py:_l1_nas_source()` `nas_prefix = f"l1/market/{channel}/schema_version={ver}/tier=L1/exchange={exchange}/symbol={symbol}/date={date_str}/"` 하드코딩 (MCT-169 D3=C) | Read `src/mctrader_data/compactor/l2.py:140-170` (line 157-160) |

**U2-HELPER amendment (2 분산점 추가 — Amendment 1 박제, 본 ADR 말미 참조)**:

| 항목 | 사실 | verified-via |
|---|---|---|
| **SSOT-5 (PUT L2/L3 historical)** | `_historical_dual_write()` line 448 — byte-equivalent to SSOT-2 (WS-A historical promotion path) | Read `src/mctrader_data/compactor/runner.py:439-475` |
| **SSOT-6 (GET L2)** | `l3.py:_compact_day_nas()` `nas_prefix = f"l2/market/...tier=L2/..."` — 구조 동형 to SSOT-4 (L3Compactor production active) | Read `src/mctrader_data/compactor/l3.py:153-156` |

**구조 결함**: nas_key 가 6곳 분산 산출 (Original 4 + U2-HELPER amendment 2). PUT 키/GET 키/cleanup 키 불일치 시 무손실 게이트 통과해도 orphan·split-brain 위험.

### Reader-side (변경 영향 0 박제)

| 항목 | 사실 | verified-via |
|---|---|---|
| **L1 reader `_build_key`** | `tier=L1/exchange=DEFAULT/symbol={SYM}/date={date}/hour={HH}/{SYM}_{date}_{HH}.parquet` — **candles namespace** (`l1/` 0, `market/` 0, `schema_version=` 0) | Read `src/mctrader_data/io/l1_reader.py:75-84` |
| **cold reader `_build_nas_object_key`** | partition_path-as-is (또는 `node=DEFAULT/` 주입) — 평면 정합 | Read `src/mctrader_data/io/cold_reader.py:195-238` |
| **tier_reader facade** | partition_path → `_extract_tier` → L1 reader (candles) or cold_reader. **tier_reader 자체는 nas_key 산출 없음 — partition_path 그대로 reader 위임** | Read `src/mctrader_data/io/tier_reader.py:147-223` |
| **REST endpoint** | `partition_path: str = Query(...)` 수신, validation 후 `tier_reader.read(partition_path)` 위임 — REST 측 nas_key 변환 없음 | Read `src/mctrader_data/api/routes_v1.py:63-91` |

### Cross-repo isolation (engine 변경 0 박제 — §결정 5 결정적 근거)

| 항목 | 사실 | verified-via |
|---|---|---|
| **engine `historical.py`** | `partition_path = f"tier=L1/exchange={exchange}/symbol={symbol_str}/timeframe={timeframe_str}/date={date_str}/part-00.parquet"` — **candles namespace (`timeframe=` 포함), market data L1 namespace (`market/<channel>/schema_version=*/`) 미참조** | Read `mctrader-engine/src/mctrader_engine/data_client/historical.py:35-87` (line 42, 65, 87) |

**engine = candles only, market data L1 unification cross-repo impact = none** (§결정 5 verbatim).

### ADR Relationships

- **ADR-027 complements (§D1 Hive prefix layout amend)**: 본 ADR 이 ADR-027 §D1 의 "단일 bucket `mctrader-market` + Hive prefix" 정책 위에서 `l1/` sub-namespace 만 제거. 단일 bucket / Hive partition layout / 7종 invariant (§D6) 정책 무변경.
- **ADR-029 complements (§D9 NAS SoT for ALL tiers)**: 본 ADR 이 ADR-029 의 all-tier NAS SoT 정책을 key namespace 측면에서 통일 — L1 이 L2/L3 와 "완전히 동일한 형식" 으로 (사용자 Q2 confirm 정합). NAS PUT 의무/grace 정책 (§D5/§D7) 무변경.
- **ADR-009 §D12 forward-only invariant**: U5 의 grep gate 박제가 본 invariant 의 nas_key 영역 적용 — `_resolve_legacy_nas_key` 정의/호출 0 박제로 forward-only 강화.
- **ADR-017 §3 D3 tier layout**: tier 구분이 NAS object key 의 `tier=L{1,2,3}/` Hive partition 컴포넌트 (ADR-009 §D2) 로 충분하다는 ADR-017 의 layout 정합 — `l1/` prefix sub-namespace 는 ADR-017 정의 외 도입된 잉여.
- **ADR-031 (Data domain decoupling)**: 본 ADR 의 scope = mctrader-data Layer 2 내부 (data REST API → io reader → NAS object). cross-repo impact 0 (§결정 5 verbatim).

## Decision

### §결정 1 — 목표 스킴: 전 tier 단일 평면 SSOT

**확정 layout** (`l1/` prefix 제거):

```
market/<channel>/schema_version=<ver>/tier=L{1,2,3}/exchange=<ex>/symbol=<sym>/date=<YYYY-MM-DD>/[hour=<HH>/][node=<NODE>/]part-<name>.parquet
```

**Rationale**:

1. **tier 구분 충분성**: Hive partition `tier=L{1,2,3}/` 컴포넌트가 이미 tier 구분 (ADR-009 §D2 + ADR-017 §3 D3 정합). `l1/` prefix sub-namespace 는 정의 외 잉여.
2. **L1 ↔ L2/L3 균질성** (사용자 Q2 confirm): L1 이 L2/L3 와 "완전히 동일한 형식" — reader / compactor / promotion path 의 분기 코드 감소.
3. **단일 helper 산출 가능성**: §결정 2 helper 가 path 의 `tier=` 컴포넌트만 보고 key 결정. tier 별 분기 0.
4. **ADR-027 §D1 Hive prefix 정책 정합**: 단일 bucket `mctrader-market` + Hive partition layout 유지. `l1/` 제거는 sub-namespace 제거일 뿐 ADR-027 정책 위반 0.

**Alternative rejected**: `l{1,2,3}/` prefix 균등 도입 — sub-namespace 잉여 (`tier=` 컴포넌트와 중복) + reader 분기 코드 영구 잔존 → 거부.

### §결정 2 — 단일 helper SSOT

> **AMENDED (2026-05-17, U2-HELPER chief author)**: caller 표 4 rows → 6 rows + Public API 3 → 5 + keyword-only 의무 추가. 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 1` 우선 인용.

`src/mctrader_data/nas_storage/nas_key.py` 신규 module. 모든 nas_key 산출 = 본 helper 1곳 경유 (4 분산점 흡수; U2-HELPER amendment 후 6 분산점).

**Public API (U2-HELPER 가 impl, 본 ADR 이 계약 박제, Original 박제 — Amendment 1 후 갱신)**:

```python
def build_nas_key(parquet_path: Path, root: Path, *, tier: str | None = None) -> str:
    """단일 평면 SSOT — 전 tier 동일 layout.

    Layout: market/<channel>/schema_version=*/tier=L{1,2,3}/...

    Args:
        parquet_path: local parquet 절대 경로 (root 하위 의무)
        root: data root (예: /var/lib/mctrader/data)
        tier: 명시적 tier override (None = path 의 tier= 컴포넌트에서 자동 추출)

    Returns:
        평면 NAS object key (POSIX, l1/ 제거)

    Raises:
        ValueError: parquet_path 가 root 하위가 아닌 경우 (forward-only invariant 가드)
    """

def build_l1_prefix(channel: str, schema_ver: str, exchange: str, symbol: str, date_str: str) -> str:
    """L2 compactor 의 L1 GET source prefix (SSOT-4 흡수).

    Layout: market/<channel>/schema_version=*/tier=L1/exchange=*/symbol=*/date=*/
    (l1/ prefix 제거, tier=L1 partition 컴포넌트로 구분)
    """
```

**dual-read 윈도우 활성 시 한시적 추가 helper (U5 가 회수)**:

```python
def build_legacy_nas_key(parquet_path: Path, root: Path) -> str:
    """[Deprecated U5 회수] tier=L1 → 'l1/' + rel.as_posix(), 그 외 → 평면.

    Phase 1 WS-B `_resolve_legacy_nas_key` 흡수. dual-read fallback 윈도우
    (§결정 3) 동안만 활성. U5 가 본 helper + 호출처 모두 grep gate 0 박제.
    """
```

**Caller 흡수 plan** (U2-HELPER scope, ADR 가 계약만 박제 — Original 4 rows, Amendment 1 후 6 rows):

| Caller | 현재 | U2 후 | 변경 line |
|---|---|---|---|
| `dual_writer.py::put_l1` | `nas_key = "l1/" + rel.as_posix()` | `nas_key = build_nas_key(path, local_root, tier="L1")` | line 371 (Amendment 3 후 376) |
| `runner.py::_dispatch_dual_write` | `nas_key = str(parquet_path.relative_to(self._root)).replace(...)` | `nas_key = build_nas_key(parquet_path, self._root, tier=tier)` | line 265 |
| `runner.py::scan_and_cleanup_legacy` | `nas_key = str(rel).replace(...)` (현 평면, Phase 1 WS-B 후 tier-aware) | `nas_key = build_nas_key(parquet, root)` (Phase 1 helper 흡수) | line 350-351 (Amendment 3 후 370-371) |
| `l2.py::_l1_nas_source` | f-string `nas_prefix = f"l1/market/..."` | `nas_prefix = build_l1_prefix(channel, schema_ver, exchange, symbol, date_str)` | line 157-160 |

**Rationale**:

- **`src/mctrader_data/nas_storage/` 패키지 위치**: DualWriter / NASUploader / get_streaming 동거 — nas_key SSOT 가 동일 패키지 함께 위치 시 cohesion 최대 (Refactor deputy 분석).
- **`tier` override 인자**: `put_l1()` 같은 명시 tier caller 의 호출 명확성 보장. None 시 path 의 `tier=` 컴포넌트 자동 추출 — cleanup glob 패턴 정합.
- **`ValueError` raise**: path traversal / scope 위반 가드 — ADR-009 §D12 forward-only invariant 의 정합.

### §결정 3 — Dual-read 전환 윈도우 + cutover sequence

> **AMENDED (2026-05-17, U2-HELPER chief author)**: "reader fallback" wording 정정 — 실질 영역 = L2 compactor `_l1_nas_source` (SSOT-4) GET 측 dual-prefix list union. data REST io/ reader 영역 변경 0 박제. 현행 운영 wording 은 본 ADR 말미 `## Amendments — Amendment 2` 우선 인용.

**Cutover ordering** (spec §5 verbatim, 본 ADR 이 정책 박제):

```
1. 본 ADR Accepted (dual-read 윈도우 + sequence 정의)
2. U2 코드 forward-fix land — 신규 PUT = 평면 / reader = dual-read fallback enabled
3. U4 cross-repo isolation 박제 (§결정 5 verbatim) — close 또는 axiom 박제
   U3 dry-run + copy + 4-HEAD verify (delete 보류)
   (위 2 항목 병렬, repo 경계 / 파일경로 disjoint)
4. cross-repo 회귀 전수 green → U3 old l1/ key delete 단계 진입
5. U5 통합 검증 + dual-read fallback 제거 + Phase 1 helper dead-code 회수 + forward-only invariant 박제
```

**Dual-read 윈도우 정의** (Original — Amendment 2 후 갱신):

- **활성 시점**: U2 land 직후 (cutover step 2 완료) — reader 의 nas_key 결정 path 가 평면 우선 조회 → 404 시 `l1/` fallback 조회 (`build_legacy_nas_key` 경로).
- **종료 시점**: U5 land (cutover step 5) — fallback 코드 path 제거 + `build_legacy_nas_key` helper + 호출처 모두 grep gate 0 박제.
- **활성 기간 SLO**: U3 100% 완료 + cross-repo isolation 박제 + 30일 cool-down (rollback 안전망 보존). 예상 cutover 윈도우 길이 = 약 2-4주 (Phase 2 Epic 진행 속도 종속).

**Rationale (R1 안전 게이트 — spec §5)**:

forward-only 위반 — U2 평면 cutover 시 마이그레이션 미완 객체 `l1/` 잔존 → reader split-brain 위험. dual-read fallback 가 양쪽 조회 가능 상태 보장 → cutover step 2 (U2 land) 와 cutover step 4 (U3 delete 완료) 사이 모든 시점에서 reader 정상 동작.

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

**EPIC-nas-key-unification 의 cross-repo impact 결과 verbatim 박제** — U4-XREPO Story scope 결정의 결정적 근거.

**검증 결과** (전수 코드 verified, 본 ADR Context "Cross-repo isolation" 표 참조):

> engine `historical.py:42,65,87` 의 partition_path = `tier=L1/exchange={exchange}/symbol={symbol_str}/timeframe={timeframe_str}/date={date_str}/part-00.parquet` — **candles namespace (`timeframe=` 포함), market data L1 namespace (`market/<channel>/schema_version=*/`) 미참조**. engine = candles only, market data L1 layout 미사용.

**결정**:

1. **U4-XREPO Story scope = close 후보** (또는 최소 scope 로 축소) — 본 Epic 의 market data L1 unification cross-repo impact = none. data REST resolver = mctrader-data 내부 (`tier_reader.py` / `cold_reader.py` / `l1_reader.py` / `routes_v1.py`) — 별도 service 없음. engine 측 변경 0.
2. **Epic 의 "cross-repo Epic" 프레이밍 축소**: market data L1 unification = mctrader-data 내부 구조 fix. cross-repo Story U4 의 잔류 역할 = axiom-of-symmetry 정합 / candles vs market data 영역 격리 명시 (코드 변경 없음, 문서 commit only) — 또는 close 후 본 ADR §결정 5 가 격리 invariant carrier.
3. **L1Reader namespace 분리 박제** (verified-via Read `l1_reader.py:75-84`): L1Reader 의 `_build_key` 가 candles namespace (`tier=L1/exchange=DEFAULT/symbol={SYM}/date={date}/hour={HH}/{SYM}_{date}_{HH}.parquet`) 만 처리. market data L1 namespace (`market/<channel>/schema_version=*/tier=L1/...`) 는 L2 compactor 의 `_l1_nas_source` (SSOT-4) 가 GET — L1Reader 와 disjoint.

**Architect 판정 (본 ADR U1 publish 시점)**:

- **case A 채택 (close 권고)** — U4-XREPO scope = 0. body 갱신 후 close. 본 ADR §결정 5 가 cross-repo isolation invariant carrier 역할.
- **case B 비채택**: scope 축소 (axiom 문서 commit) 도 가능하나 case A 가 정합 — 코드 변경 0 / 문서 영역 본 ADR 흡수 시 별 Story 잉여.

**Rationale (R3 안전 게이트 spec §5 — 본 ADR 이 해소)**:

R3 (cross-repo cutover ordering — data REST resolver 위치/계약 미확인 → engine fetch 404) 의 prerequisite "resolver 위치 식별" = §7.1 Explore 결과로 **해소**. resolver = mctrader-data 내부 (별도 service 없음). engine = candles only → cross-repo fetch 404 risk 0. R3 무효화 박제.

### §결정 6 — Phase 1 helper 회수 + forward-only invariant 박제

U5-VERIFY Story 의 명시 scope:

1. **Phase 1 `_resolve_legacy_nas_key` helper 회수**: WS-B (`mctrader-data#84`) 가 도입한 `src/mctrader_data/compactor/runner.py::_resolve_legacy_nas_key` 함수 정의 + 모든 호출처 제거. repo-wide grep gate 0 박제 (`tests/integration/test_forward_only_nas_key.py`).
2. **dual-read fallback 코드 회수**: §결정 3 의 dual-read 윈도우 종료 — reader path 의 `l1/` fallback 코드 path 제거. `build_legacy_nas_key` helper + 호출처 모두 grep gate 0 박제.
3. **forward-only invariant 박제 테스트** (ADR-009 §D12 정합):
   ```python
   # tests/integration/test_forward_only_nas_key.py
   def test_no_l1_prefix_literal_in_src() -> None:
       """ADR-034 §결정 6: l1/ prefix literal 직접 사용 0 (helper 외)."""
       # grep src/ for "l1/" literal (helper 정의 라인 제외)
       # assert 0 hits

   def test_no_resolve_legacy_nas_key_definition() -> None:
       """ADR-034 §결정 6: Phase 1 WS-B helper dead-code 0."""
       # grep src/ + tests/ for "_resolve_legacy_nas_key"
       # assert 0 hits (정의 + 호출 모두)

   def test_no_dual_read_fallback_in_readers() -> None:
       """ADR-034 §결정 3: dual-read 윈도우 종료 후 reader 의 l1/ fallback 0."""
       # grep src/mctrader_data/io/ for "build_legacy_nas_key" + "l1/" fallback path
       # assert 0 hits
   ```

**Rationale (ADR-009 §D12 정합)**:

forward-only invariant = 한 번 layout 결정 후 그 결정을 따르지 않는 코드 path 잔존 0. Phase 1 helper + dual-read fallback 은 cutover 윈도우 동안만 한시적 활성 — 종료 시점에 코드 path 제거가 forward-only invariant 의 자연스러운 적용.

## Alternatives

### Alt-1: `l1/` prefix 보존 + L2/L3 도 `l{2,3}/` prefix 추가 (균등 sub-namespace)

- 거부 사유: sub-namespace 가 Hive partition `tier=L{1,2,3}/` 컴포넌트와 중복. reader 측 분기 코드 영구 잔존 (`tier=L1` → `l1/` 분기, `tier=L2` → `l2/` 분기). 사용자 Q2 confirm ("L1 이 L2/L3 와 완전히 동일한 형식") 위반.

### Alt-2: 4 분산점 각자 fix (helper 도입 없이)

- 거부 사유: MCT-168/169/189/190 가 이미 시도한 패턴 — 매번 전술 패치 → 다음 작업이 또 같은 곳을 건드림. 사용자 직접 보고 ("세 번 더 작업하게 하지 말고 이번에 제대로") 의 거부 대상.

### Alt-3: big-bang cutover (dual-read 윈도우 없이)

- 거부 사유: U2 land 후 U3 완료 전까지 reader 가 `l1/` 객체 read 불가 → 117 GB 데이터 일시적 inaccessible. forward-only invariant 위반 + 운영 영향 大. ADR-027 §D4 의 dual-write 윈도우 패턴 (MCT-150~155) 정합.

### Alt-4: U4-XREPO scope 보존 (engine reader 정합 작업)

- 거부 사유: §7.1 Explore 결과 verbatim — engine = candles only, market data L1 namespace 미참조. engine 측 변경 0. U4 scope = 0 → close 정합 (§결정 5).

## Consequences

### 긍정

1. **반복 패치 루프 종결**: 4 SSOT → 1 helper → 다음 작업이 nas_key 영역 touch 시 단일 helper 만 변경. ADR-045 Amend5 §D-9 Mandatory ADR trigger 의 근본 해소.
2. **forward-fix 보증**: 신규 수집 자동 평면 적재 (U2 land 후) — 수동 개입 없이 통합. WAL → L1 → L2/L3 전 tier 균질 layout.
3. **운영 단순화**: NAS bucket browse 시 `l1/` vs `market/` 양분 시각 혼란 해소. `aws s3 ls` 단일 prefix 로 전 tier 조회.
4. **L1Reader / cold_reader 분기 감소**: 향후 L1 backfill (MCT-173) / historical fetch 의 nas_key 산출 분기 코드 잠재적 감소 (별 Story scope, 본 ADR 직접 영향 0).

### 부정

1. **Cutover 윈도우 운영 부담**: dual-read 윈도우 (약 2-4주) 동안 reader 가 양쪽 fallback 조회 — latency p99 영향 측정 의무 (U2 acceptance criteria). U5 완료까지 fallback 코드 유지.
2. **U3 117 GB re-key 비용**: NAS LAN 트래픽 spike + MinIO 백엔드 fsync 압박. batch self-pacing (500/sweep) 으로 분산 — total cutover < 72h SLO.
3. **delete-marker 누적**: bucket versioning=Enabled → re-key 후 117 GB 의 delete-marker 영구 잔존 (rollback 안전망). 본 Epic scope 외 (별 maintenance Story 의 lifecycle ILM rule).
4. **Phase 1 WS-B helper 한시 활성**: WS-B (`mctrader-data#84`) merge 후 U5 land 까지 `_resolve_legacy_nas_key` 잔존. forward-only invariant 의 한시적 위반 — U5 의 grep gate 박제로 해소.

### Risk

| # | 위험 | 안전 게이트 | 책임 |
|---|---|---|---|
| R1 | forward-only 위반 — U2 평면 cutover 시 마이그레이션 미완 객체 `l1/` 잔존 → reader split-brain | §결정 3 dual-read 윈도우 + U5 grep gate | U5-VERIFY |
| R2 | 마이그레이션 중 in-flight compaction race | §결정 4 `.compacted` sentinel + U2 선행 | U3-MIGRATE |
| R3 | cross-repo cutover ordering — data REST resolver 위치/계약 미확인 | §결정 5 (Explore §7.1 결과 박제로 R3 무효화) | U4-XREPO (close) |
| R4 | 117 GB 대량 delete 비용/오류 | §결정 4 batch self-pacing + bucket versioning rollback | U3-MIGRATE |
| R5 | MCT-159 Issue 1/2 회귀 은닉 — compactor touch 시 동시 변경 | U2 scope = nas_key helper 로 격리 (schema_version/pyarrow concat 경로 변경 금지) | U2-HELPER scope guard |

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

> U2-HELPER (mctrader-data#88) Phase 2 chief author synthesis 결과 박제. 본문 §결정 2 / §결정 3 / §Monitoring 의 현행 운영 wording = 본 섹션 우선 인용.
> Convergence: 4 deputy 만장일치 (CodebaseMapper + Refactor + SecurityArch + OpRiskArch + TestContractArch + DataMigrationArch) + chief author Verify-via (l3.py production active runner.py:54+521 + minio_uploader deprecated 활성 caller 0) + Codex consult `codex_check_no_findings` (debate-protocol-v1 v1.2 Round 0 미발동).
> FIX iteration 1 (2026-05-18): DesignReview lane Claude+Codex peer review — 14 findings (0 P0 / 4 P1 / 9 P2 / 1 NIT) inline 해소. Amendment 3 verification row 추가 + amended_adr field 추가 (F-codex-5 + F-codex-7 박제). DesignReviewPL re-verify PASS (14 of 14 RESOLVED).

### Amendment 1 — §결정 2 caller 표 (4 rows → 6 rows + Public API 3 → 5)

**Trigger**:
1. **SSOT-5 발견** (Orchestrator): `runner.py:448 _historical_dual_write` (WS-A historical promotion path). CodebaseMapper §2 byte-equivalence verification — SSOT-2 ↔ SSOT-5 mechanical replacement OK.
2. **SSOT-6 발견** (Refactor §5 + chief author Verify-via): `l3.py:153-156 L3Compactor._compact_day_nas` L2 GET source. L3Compactor production active (runner.py:54 + 521 verified).

**Rationale**:
- Epic §동기 정합: 사용자 명시 거부 패턴 ("세 번 더 작업하게 하지 말고") 회피
- 단일 SSOT invariant (AC-1): 5+1 caller (PUT 5 + GET 2) 전부 helper 경유
- forward-only invariant (ADR-009 §D12): 한 번 layout 결정 후 그 결정 따르지 않는 코드 path 잔존 0
- 4 deputy convergence: SecurityArch (T-S2 surface 경고) + DataMigrationArch + OpRiskArch + TestContractArch 만장일치

**Current caller 표 (6 rows + sub-helper)**:

| Caller | 현재 | U2 후 | 변경 line | 추가 sub-helper |
|---|---|---|---|---|
| `dual_writer.py::put_l1` | `nas_key = "l1/" + rel.as_posix()` | `nas_key = build_nas_key(path, local_root, tier="L1")` | line 376 (정정: pre-WS-A 371) | — |
| `runner.py::_dispatch_dual_write` | `nas_key = str(parquet_path.relative_to(self._root)).replace(...)` | `nas_key = build_nas_key(parquet_path, self._root, tier=tier)` | line 265 | — |
| `runner.py::scan_and_cleanup_legacy` | `nas_key = _resolve_legacy_nas_key(parquet, root)` (Phase 1 WS-B helper) | `nas_key = build_legacy_nas_key(parquet, root)` (Phase 1 helper module 이관, dual-read transitional) | line 370-371 (정정: pre-WS-A 350-351). 함수 정의 304-321 (이관 후 삭제) | `build_legacy_nas_key` (Deprecated U5 회수) |
| `l2.py::_l1_nas_source` | f-string `nas_prefix = f"l1/market/..."` | `flat = build_l1_prefix(...)` 평면 + `legacy = build_legacy_l1_prefix(...)` legacy → `_list_objects` dual-list union (§11.2-A Option A, dual-read 윈도우 안전 정책) | line 157-160 | `build_legacy_l1_prefix` (Deprecated U5 회수, §11.2-A Option A carrier) |
| **`runner.py::_historical_dual_write`** (SSOT-5, WS-A historical) | `nas_key = str(parquet_path.relative_to(root)).replace(...)` (byte-equivalent to SSOT-2) | `nas_key = build_nas_key(parquet_path, root, tier=tier)` | line 448 | — |
| **`l3.py::_compact_day_nas`** (SSOT-6, L3 GET L2 source) | f-string `nas_prefix = f"l2/market/.../tier=L2/..."` (구조 동형 to SSOT-4) | `nas_prefix = build_nas_prefix(tier="L2", channel, schema_ver, exchange, symbol, date_str)` | line 153-156 | `build_nas_prefix` (tier-agnostic 일반화 helper, l3.py SSOT-6 흡수) |

**Public API 확장 (3 public + 2 transitional)**:

```python
def build_nas_key(parquet_path: Path, root: Path, *, tier: str | None = None) -> str
def build_l1_prefix(*, channel: str, schema_ver: str, exchange: str, symbol: str, date_str: str) -> str
def build_nas_prefix(*, tier: str, channel: str, schema_ver: str, exchange: str, symbol: str, date_str: str) -> str
def build_legacy_nas_key(parquet_path: Path, root: Path) -> str  # [Deprecated U5 회수]
def build_legacy_l1_prefix(*, channel: str, schema_ver: str, exchange: str, symbol: str, date_str: str) -> str  # [Deprecated U5 회수, §11.2-A Option A]
```

**keyword-only 의무** (Refactor §2 advocacy): `build_l1_prefix` / `build_nas_prefix` / `build_legacy_l1_prefix` = 5 동형 `str` 인자 → positional 순서 오류 silent wrong key 차단.

### Amendment 2 — §결정 3 wording 정정

**Trigger**: ADR-034 §결정 3 wording "reader fallback" 의 실질 의미 ambiguity. 3 source 검증 (CodebaseMapper §4 + TestContractArch §6 + chief author Verify-via) 결과 `src/mctrader_data/io/` 영역 `"l1/"` literal 0 hits — reader-side 변경 영역 자체가 부재.

**Rationale**: 실제 fallback 영역 = L2 compactor `_l1_nas_source` (SSOT-4) GET 측 dual-prefix list union. data REST io/ reader 영역 (`tier_reader.py` / `cold_reader.py` / `l1_reader.py` / `routes_v1.py`) 변경 0 박제. DataMigrationArch §11.2 primary advocacy 정합.

**Current Dual-read 윈도우 정의** (실질 영역 박제):

본 ADR §결정 3 "reader fallback" 의 실질 의미 = **L2 compactor `_l1_nas_source` (SSOT-4) GET 측 dual-prefix list union**. data REST io/ reader 영역 (`tier_reader.py` / `cold_reader.py` / `l1_reader.py` / `routes_v1.py`) 변경 0 박제 (§결정 5 "Reader-side 변경 영향 0" 표 정합).

3 data plane subsystem 의 dual key acceptance:
1. **Cleanup HEAD path** (SSOT-3, `scan_and_cleanup_legacy`): `build_legacy_nas_key` 가 tier-aware (`l1/` + 평면 양쪽 알고있음).
2. **L2 GET L1 source path** (SSOT-4, `_compact_hour_nas`): `build_l1_prefix` 평면 + `build_legacy_l1_prefix` legacy 양쪽 `_list_objects` → union (§11.2-A Option A, U2-HELPER chief author 결정).
3. **data REST reader path**: 변경 0 박제 (3 source 0 hits 수렴: CodebaseMapper §4 + TestContractArch §6 + chief author Verify-via).

- **활성 시점**: U2 land 직후 (cutover step 2 완료) — L2 compactor 가 평면 + legacy 양쪽 list 조회 + cleanup HEAD 가 양쪽 정합.
- **종료 시점**: U5 land (cutover step 5) — fallback 코드 path 제거 + `build_legacy_nas_key` + `build_legacy_l1_prefix` helper + 호출처 모두 grep gate 0 박제.
- **활성 기간 SLO**: U3 100% 완료 + cross-repo isolation 박제 + 30일 cool-down (rollback 안전망 보존). 예상 cutover 윈도우 길이 = 약 2-4주.

### Amendment 3 — Caller 표 line number 정정 (WS-A #85 sha f2e2bc9 post-merge)

**Trigger**: WS-A (mctrader-data#85, merged 2026-05-14 sha f2e2bc9) 가 ADR-034 publish (2026-05-17) 직전 ~25 lines 삽입 → ADR-034 의 line number 박제 일부 stale.

**Verified lines** (base sha ecfe150b, CodebaseMapper §1 verified):

| SSOT | ADR-034 박제 line | 실제 line (base sha ecfe150b) | 변경 origin |
|---|---|---|---|
| SSOT-1 PUT L1 | 371 | **376** | WS-A 가 SSOT-1 위 5 lines 삽입 |
| SSOT-3 helper 호출 | 350-351 | **370-371** | WS-A 가 호출 site 위 20 lines 삽입 |
| SSOT-3 helper 정의 | (미수재) | 304-321 (WS-B #84 도입) | WS-B PR #84 |
| SSOT-2 / SSOT-4 / SSOT-5 / SSOT-6 | 265 / 157-160 / 448 / 153-156 | 동일 | 변경 0 |
| **MCT-159 Issue 2 (forbidden)** (F-codex-5 FIX iteration 1) | `l2.py:44` | **변경 0** (line-level disjoint pledge 박제) | Refactor §7 MCT-159 Issue 2 (orderbookdepth/pyarrow line) pledge — 본 amendment 가 SSOT-4 (l2.py:157-160) 만 touch, line 44 영역 disjoint |

### Amendment 4 — Monitoring 표 cardinality 갱신

**Trigger**: §Monitoring `mctrader_nas_key_helper_call_total{caller, tier}` Counter — SSOT-5 + SSOT-6 흡수로 caller 4 → 6 row.

**Verified cardinality matrix (chief author)**:

| caller (verbatim) | tier values | active cardinality |
|---|---|---|
| `dual_writer_put_l1` | L1 | 1 |
| `runner_dispatch_dual_write` | L2, L3 | 2 |
| `runner_cleanup` | L1, L2, L3 | 3 |
| `runner_historical_dual_write` | L2, L3 | 2 |
| `l2_compactor_get_source` | L1 | 1 |
| `l3_compactor_get_source` | L2 | 1 |

**active cardinality = 10** (max 6 × 3 = 18). Prometheus best practice (<100 per metric) 안전.

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
- ADR-054 (doc-only Story fast-path — 본 U1-ADR Story 적용 후보)
- ADR-052 Amendment 4 (mandatory Codex proactive check — U2 + U3 chief author §3 통합 직후 발동)
- ADR-068 Amendment 1 (dimensional empirical annotation — U3 PROVISIONAL [empirical-source: TBD] 4 row)

### Story SSOT

- U1-ADR `mctrader-data#87` — 본 ADR 본문 publish
- U2-HELPER `mctrader-data#88` — 단일 helper SSOT impl + Amendment 1-4 carrier (chief author) + FIX iteration 1 RESOLVED + LAND 2026-05-18 (PR #95 sha 4aa5483a)
- **U3-MIGRATE `mctrader-data#89`** — 1회성 멱등 re-key 마이그레이션 + **Amendment 5 carrier (chief author)** + Phase 2 cutover step 4 진입
- U4-XREPO `mctrader-data#90` — closed not_planned (§결정 5 cross-repo isolation 박제)
- U5-VERIFY `mctrader-data#91` — 통합 검증 + Phase 1 helper 회수
- EPIC `mctrader-data#86` — Phase 2 Epic 전체 SSOT

### Spec + Change Plan

- `mctrader-data:docs/superpowers/specs/2026-05-17-nas-key-unification-design.md` — brainstorm-complete spec, 본 ADR 의 출처 (§1-§7 verbatim 인용)
- `mctrader-data:docs/change-plans/U2-HELPER.md` — Amendment 1-4 evidence trail + FIX iteration 1 박제 (chief author author)
- **`mctrader-data:docs/change-plans/U3-MIGRATE.md`** — **Amendment 5 evidence trail (chief author)** + 4-HEAD verify impl + Manifest YAML schema + IAM Option B + Container Option B

### 기존 ADR cross-ref (본 ADR 박제 후 추가 의무 — 별 amendment scope)

- ADR-027 §D1 amendment box (별 carrier amendment): "본 ADR §결정 1 cross-ref — `l1/` sub-namespace 제거, Hive prefix layout 단순화"
- ADR-029 §D9 amendment box (별 carrier amendment): "본 ADR §결정 1 cross-ref — L1 ↔ L2/L3 key namespace 균질화"

위 cross-ref 추가는 본 ADR PR 의 ADR-027 동시 amendment 로 진행 (sibling sync).
