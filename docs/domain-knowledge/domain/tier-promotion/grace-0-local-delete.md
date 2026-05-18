# Grace-0 Local Delete Invariant (3-tier cascade 완결, MCT-202 amendment)

> **SSOT**: ADR-029 §D3 + §D11 (MCT-189 2026-05-16 WAL→L1 LAND, MCT-202 2026-05-18 L1→L2 + L2→L3 cascade LAND, D-1 옵션 B caller-side `source_to_delete`).
> **caller-wired vs decision-defined 분리 의무** — 본 페이지 = caller-wired 측 invariant 박제.
> 배경 (MCT-189 trigger, 2026-05-16): 운영 진단에서 `promote_l1()` 정의는 LAND(MCT-169)됐으나 production caller = 0건 발견 (cross-document SSOT drift 2호) — WAL→L1 wiring invariant 박제.
> 배경 (MCT-202 trigger, 2026-05-18): 운영 진단 `0e244e9` 에서 WAL→L1 만 작동 + L1→L2 / L2→L3 cascade 미작동 발견 (`runner.py:284 data=parquet_path` 동일 객체 → `dual_writer.py:249 data != local_path` guard False → `_promote_after_nas_put` 미실행). 117GB 누적 + 컨테이너 disk-full 빈발 — 3-tier cascade wiring invariant 박제.

## 4 invariant (3-tier 확장, MCT-202 amendment)

### INV-1: `promote_l1()` caller wiring 박제 (3-tier cascade, MCT-202 amendment)

`DualWriter.write()` 의 `status=committed` branch 가 source local file self-delete 책임. caller (`compactor/runner.py::_dispatch_dual_write` + `_historical_dual_write`) 는 별도 `promote_l1()` 호출 불요 — NAS PUT commit boundary 안에서 self-delete.

이전 상태 (MCT-169 LAND ~ MCT-189 이전): `promote_l1()` 정의 존재, caller 0건 → wiring 누락 = local Parquet 영구 누적 (130 GB). 라인 주석 "caller source safe to delete" 가 책임을 caller 에 전가했으나 caller 도 호출 안 함.

이전 상태 (MCT-189 LAND ~ MCT-202 이전, 2026-05-16 ~ 2026-05-18): WAL→L1 wiring 만 LAND. L1→L2 + L2→L3 cascade caller wiring 미작동 — `runner.py:284 data=parquet_path` 동일 객체 전달이 `dual_writer.py:249 data != local_path` guard 를 False 로 만들어 `_promote_after_nas_put` 미실행 → L1 / L2 source parquet local 영구 누적 (117GB).

MCT-202 LAND 후 (2026-05-18): 3-tier cascade 완결. `DualWriter.write()` 시그니처에 `source_to_delete: Path | None = None` keyword-only 파라미터 추가. caller 가 명시 cascade intent 박제:

```python
# _dispatch_dual_write (forward L2/L3 path) — runner.py:281-286
result = self._dual_writer.write(
    local_path=parquet_path, nas_key=nas_key, data=parquet_path,
    sha256=sha256, source_to_delete=parquet_path,  # MCT-202 cascade intent
)

# _historical_dual_write (WS-A historical promotion) — runner.py:447-487
result = dual_writer.write(
    local_path=parquet_path, nas_key=nas_key, data=parquet_path,
    sha256=sha256, source_to_delete=parquet_path,  # MCT-202 D-3 동형
)
```

**3-tier production caller grep ≥1 의무 (ADR-032 evidence triad (2), MCT-202 cascade)**:

| cascade 단계 | caller location | grep 의무 |
|---|---|---|
| WAL → L1 | `dual_writer.py::write()` `_COMMITTED_STATUSES` branch (MCT-189 LAND) | `promote_l1(` 호출 ≥1 |
| L1 → L2 | `compactor/runner.py::_dispatch_dual_write(tier="L2", ...)` (MCT-202 LAND) | `source_to_delete=parquet_path` 전달 ≥1 |
| L2 → L3 | `compactor/runner.py::_dispatch_dual_write(tier="L3", ...)` (MCT-202 LAND) | `source_to_delete=parquet_path` 전달 ≥1 |
| historical (L1/L2/L3) | `compactor/runner.py::_historical_dual_write` (MCT-202 D-3 LAND) | `source_to_delete=parquet_path` 전달 ≥1 |

### INV-2: 4중 HEAD verify primitive (D-4 C)

`nas_uploader.head_object(key)` 반환 dict 4 field 모두 비교:
- `ETag` — strip(`"`)
- `VersionId` — versioning Enabled 시 강제 (MCT-161 bucket versioning Enabled)
- `Metadata['sha256']` — caller-side single computation. **multipart ETag ≠ sha256** (INV-3 SSOT: `parquet-streaming/cold-path-memory-invariant.md`). NAS PUT 시 metadata 에 sha256 박제.
- `ContentLength` — local source `Path.stat().st_size` 와 일치

**1개라도 mismatch = `PromotionVerifyError` raise** → local 보존 (INV-4). silent corruption (ETag 동일하나 내용 다름) 차단.

### INV-3: pre-delete HEAD guard (D-8 B)

`unlink()` 직전 동일 4중 primitive 로 한 번 더 HEAD 호출. 최초 HEAD verify 와 unlink 사이 race window (다른 process 가 NAS object 덮어쓰기 / evict) 차단. ETag + ContentLength 미일치 시 unlink 미실행 + `PromotionVerifyError` raise + local 보존.

### INV-4: forward-only NAS-SoT 격상 (D-5 A)

local fallback 제거 (MCT-170 D8=B local fallback cutoff 2026-09-01 sunset 정합). NAS bucket versioning Enabled (MCT-161) + NoncurrentVersionExpiration 30d = PITR/operational recovery 단일 보증 (ADR-027 §D7 7-day local grace motivation 흡수). local copy = ephemeral cache only. HEAD verify fail 시에만 local 보존 (retry_queue carrier, ADR-029 §D2=B 정합).

## decision-defined vs caller-wired 분리

`promote_l1()` 함수 **정의** (decision-defined) = MCT-169 LAND (2026-05-14). 그러나 caller **wiring** (caller-wired) = MCT-189 LAND (2026-05-16). **정의 LAND ≠ 운영 LAND.**

VERIFIED badge 충족 = ADR-032 evidence triad 3 evidence 모두:
1. `file:line` (정의 위치)
2. production caller `git grep` ≥ 1 (wiring 존재 증명)
3. integration test PASS (testcontainers MinIO 실 경로 검증)

review lane PASS 만으로는 불충분 — post-LAND 14d rolling `nas_reader_ambiguity_total` Counter = 0 production 실측 의무 (Epic CLOSED prereq prod-5).

## evidence triad cascade 3-tier 박제 (MCT-202 amendment)

ADR-032 evidence triad 3 evidence 가 cascade 3 단계 모두 명시:

### WAL → L1 단계 (MCT-189 LAND)

1. **file:line**: `src/mctrader_data/nas_storage/dual_writer.py:246-250` `_promote_after_nas_put` (MCT-189 D-2 A)
2. **production caller grep ≥1**: `dual_writer.py::write()` `_COMMITTED_STATUSES` branch 내 `_promote_after_nas_put` 호출
3. **integration test PASS**: `tests/test_dualwriter_grace0.py` (MCT-189 박제) — testcontainers MinIO

### L1 → L2 단계 (MCT-202 LAND)

1. **file:line**: `src/mctrader_data/compactor/runner.py:281-286` `_dispatch_dual_write(tier="L2", source_to_delete=parquet_path, ...)` (MCT-202 D-1 옵션 B)
2. **production caller grep ≥1**: `grep -n 'source_to_delete=parquet_path' src/mctrader_data/compactor/runner.py` ≥ 2 hits (forward + historical)
3. **integration test PASS**: `tests/integration/test_eager_cleanup_cascade.py::test_l1_to_l2_cascade_source_eager_unlink` — testcontainers MinIO 3-tier E2E

### L2 → L3 단계 (MCT-202 LAND)

1. **file:line**: `src/mctrader_data/compactor/runner.py:281-286` `_dispatch_dual_write(tier="L3", source_to_delete=parquet_path, ...)` (MCT-202 D-1 옵션 B)
2. **production caller grep ≥1**: 동일 caller, tier="L3" 분기 hit
3. **integration test PASS**: `tests/integration/test_eager_cleanup_cascade.py::test_l2_to_l3_cascade_source_eager_unlink`

### historical cascade (MCT-202 D-3 LAND)

1. **file:line**: `src/mctrader_data/compactor/runner.py:447-487` `_historical_dual_write` (`NASOperationalAlert` re-raise wrap 동시 LAND)
2. **production caller grep ≥1**: WS-A `promote-historical` CLI 진입점 의 `_historical_dual_write` 호출
3. **integration test PASS**: `tests/unit/compactor/test_runner_historical_dual_write.py::test_historical_passes_source_to_delete`

### post-LAND 14d production evidence gate

VERIFIED badge 충족 = 위 evidence triad 3-tier 모두 + post-LAND 14d rolling Counter:
- `mctrader_retry_orphan_total` rate = 0 (정상)
- `compactor_local_self_delete_total{outcome="committed_unlinked"}` 정상 ramp-up (3-tier 분포 균형)
- `compactor_local_self_delete_total{outcome="committed_unlink_failed"}` rate < 0.1% (P0 alarm 임계)
- local disk usage 정상 감소 (117GB → 안정 수준)

review lane PASS 만으로는 불충분 — production 실측 의무 (Epic CLOSED prereq prod-5).

## Cross-ref

- ADR-029 §D3 + §D10 + §D11 (3-tier eager unlink invariant 12종, MCT-202 amendment)
- ADR-027 §D5 + §D7 amendment box (MCT-202 — eager unlink ↔ sweep race + WAL 24h grace 폐기)
- ADR-017 §Amendment 4 (Compactor cascade self-delete + DualWriter status XOR source invariant, MCT-202)
- ADR-009 §D12.2 (forward-only invariant 3-tier 확장 annotation, MCT-202)
- ADR-032 Proposed — VERIFIED badge evidence triad 일반화 (owner Story 권고 MCT-190)
- `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` §Cross-ref (INV-3 sha256 SSOT — caller-side single computation, multipart ETag ≠ sha256)
- `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` (cross-document SSOT drift 2호 trigger — 본 wiring 누락이 그 사례)
- `docs/stories/MCT-189.md` (WAL→L1 wiring SSOT) + `docs/stories/MCT-202.md` (3-tier cascade SSOT)
- `docs/change-plans/MCT-202-eager-cleanup-cascade.md` (Change Plan §3 + §7 + §11)
- `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md` (10 결정점, WAL→L1)
