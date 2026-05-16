# Grace-0 Local Delete Invariant (MCT-189 wiring 완결)

> **SSOT**: ADR-029 §D3 amend (MCT-189 2026-05-16, D-1 A unconditional).
> **caller-wired vs decision-defined 분리 의무** — 본 페이지 = caller-wired 측 invariant 박제.
> 배경: 2026-05-16 운영 진단에서 `promote_l1()` 정의는 LAND(MCT-169)됐으나 production caller = 0건 발견 (cross-document SSOT drift 2호). 본 페이지가 그 wiring invariant를 고정한다.

## 4 invariant

### INV-1: `promote_l1()` caller wiring 박제 (D-2 A)

`DualWriter.write()` 의 `status=committed` branch 가 source local file self-delete 책임. caller (l1/l2/l3/runner) 는 별도 `promote_l1()` 호출 불요 — NAS PUT commit boundary 안에서 self-delete.

이전 상태 (MCT-169 LAND ~ MCT-189 이전): `promote_l1()` 정의 존재, caller 0건 → wiring 누락 = local Parquet 영구 누적 (130 GB). 라인 주석 "caller source safe to delete" 가 책임을 caller 에 전가했으나 caller 도 호출 안 함.

**production caller grep ≥1 의무** (ADR-032 evidence triad (2)):
- `dual_writer.py` `write()` `status=="committed"` branch 내 `promote_l1(...)` 호출

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

## Cross-ref

- ADR-029 §D3 + §D10 + §D11 + Migration §Forward-only invariant amendment box (MCT-189 2026-05-16)
- ADR-032 Proposed — VERIFIED badge evidence triad 일반화 (owner Story 권고 MCT-190)
- `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` §Cross-ref (INV-3 sha256 SSOT — caller-side single computation, multipart ETag ≠ sha256)
- `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` (cross-document SSOT drift 2호 trigger — 본 wiring 누락이 그 사례)
- `docs/stories/MCT-189.md` (Story SSOT) / `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md` (10 결정점)
