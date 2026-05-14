# mctrader-hub CLAUDE.md

mctrader 자동매매 platform governance hub. Story / ADR / Epic / cross-repo 조정. codeforge consumer.

## 프로젝트 구조

- `docs/stories/` — Story 파일 (MCT-NNN.md)
- `docs/adr/` — ADR (ADR-NNN-title.md)
- `docs/runbooks/` — 운영 runbook
- `docs/retros/` — RETRO + EPIC-RESULTS
- `docs/audit/` — 실행 결과 박제 artifact
- `docs/superpowers/specs/` — brainstorm spec
- `docs/superpowers/plans/` — implementation plan
- `scope_manifests/` — Epic scope_manifest YAML
- `scripts/` — NAS admin + 운영 스크립트
- `.codeforge/counters.json` — Story key reservation SSOT

## NAS versioning + Object Lock 현황 (MCT-161)

> Phase 2 land: 2026-05-14

### 설정 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| bucket versioning | **Enabled** | AC-1 PASS (2026-05-14T06:38Z) |
| Object Lock GOVERNANCE 30d | **SKIP** | 기존 bucket MinIO 제약 (--with-lock 생성 시점 의무) |
| Lifecycle NoncurrentVersionExpiration 30d | **Enabled** | AC-3 PASS |
| DR runbook | `docs/runbooks/nas-bucket-disaster-recovery.md` | AC-4 PASS |

### 운영 스크립트

- `scripts/enable_nas_versioning.py` — versioning + Object Lock + Lifecycle enable
- `scripts/verify_nas_versioning.py` — AC-1/2/3 verify (exit code 0=PASS)

```bash
# 환경변수 설정 후 실행
export NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
export NAS_MINIO_ACCESS_KEY=<access_key>
export NAS_MINIO_SECRET_KEY=<secret_key>
python scripts/verify_nas_versioning.py
```

### 제약 사항

- Object Lock은 bucket 생성 시(`--with-lock`) 활성화 의무. 기존 `mctrader-market`에는 적용 불가.
- NoncurrentVersionExpiration 30d — versioning 활성화(2026-05-14) 이전 null version은 복원 불가 (Edge-1).

## DR runbook (MCT-161 AC-4)

NAS data loss / hard delete 복원 절차:
- `docs/runbooks/nas-bucket-disaster-recovery.md` — 5-step (Triage / Version 조회 / Restore / Verify / Postmortem)
- 복원 가능 window: versioning 활성화 이후 + 30d NoncurrentVersionExpiration 이내

## Pending Stories (Replication Backlog)

| Story | 상태 | 내용 |
|-------|------|------|
| MCT-174 | RESERVED | NAS replication (D2=D 결정, single NAS box mcnas02 물리 부재 해소 후 진입) |

MCT-174 근거: ADR-027 §D MCT-161 amendment D2=D (replication deferred). INV-5 의무 = 후속 별 Story 예약 완료.

## Streaming refactor cross-ref (MCT-163, 2026-05-14)

### F3 DualWriter streaming

- `mctrader-data/src/mctrader_data/nas_storage/nas_uploader.py`: `put_streaming(Path|IO, key, sha256)` 신규
- `mctrader-data/src/mctrader_data/nas_storage/dual_writer.py`: `write(Path)` read_bytes 0 (streaming)
- INV-4: DualWriter peak RSS+TM delta ≤ 50 MB (105 MiB 실측: 0.2 MB / 0.0 MB)
- INV-3: sha256 SSOT caller-side (multipart ETag ≠ sha256)

### F6 L2/L3 iter_batches

- `mctrader-data/src/mctrader_data/compactor/l2.py`: `pq.ParquetFile.read()` → `iter_batches(1024)` + `write_batch`
- `mctrader-data/src/mctrader_data/compactor/l3.py`: 동형
- INV-4: L2/L3 peak RSS+TM delta ≤ 256 MB (300k rows 실측: 0.0 MB / 0.3 MB)
- INV-5: iter_batches per-batch write schema == 기존 L2/L3 schema

### EPIC-tier-promotion D9 prerequisite

- MCT-161 + MCT-163 모두 COMPLETED (2026-05-14)
- **MCT-167 (EPIC-tier-promotion governance singleton)** COMPLETED 2026-05-14 (PR #305, 1b83c28)
- **MCT-168 (L1 NAS DualWriter wiring — D1+D2 impl)** COMPLETED 2026-05-14 (hub PR #307 + data PR #59)
  - put_l1() 신규 + l1.py inject + runner pass-through + 22 tests ALL PASS
  - ADR-029 D1=B + D2=B VERIFIED (mctrader-data#59)
- cross-ref: `docs/retros/RETRO-MCT-163.md` + `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md`

## EPIC-tier-promotion-single-source (MCT-168 L1 NAS DualWriter wiring LAND 2026-05-14)

> milestone 2/6 박제 (MCT-167 + MCT-168 COMPLETED)

### ADR 산출물

- **ADR-029** (신규, MCT-167 publish) — Cold tier governance v2 — NAS = SoT for ALL tiers (D1-D11 박제)
- **ADR-017 §3 D3 amendment** — L1 NAS PUT 의무 박제
- **ADR-027 §D5+D7+D9 amendment** — L1 NAS upload 금지 invariant 폐기 + L1 grace 0 + SoT all-tier 격상
- **ADR-009 §D12.2 amendment** — forward-only invariant NAS object SoT 격상

### 핵심 결정 (D1-D11)

| D | 결정 | Option | Owner Story |
|---|---|---|---|
| D1 | L1 NAS PUT timing — ParquetWriter atomic 직후 | B | MCT-168 |
| D2 | DualWriter retry_queue + local_only 재사용 | B | MCT-168 |
| D3 | Local delete — NAS HEAD verify + grace 0 | C | MCT-169 |
| D4 | WAL sealed local only 유지 | B | MCT-171 |
| D5 | Capacity-bounded ingest block | A_modified | MCT-171 |
| D6 | bucket versioning + cross-NAS replication | B | MCT-171 (MCT-161 ✓) |
| D7 | Reader cache 95% hit + p99 <100ms | A | MCT-170 |
| D8 | forward-only + local fallback migration | B | MCT-170 |
| D9 | MCT-161 + MCT-163 prerequisite sequential ✓ | A | epic-level ✓ |
| D10 | Ambiguity invariant violation enforcement | A | MCT-169 + MCT-172 |
| D11 | 4 layer capacity 제한 (WAL 30G / L1 20G / NAS 500G / Host 200G) | capacity_bounded | MCT-171 |

### DR runbook stub 확장

- `docs/runbooks/nas-bucket-disaster-recovery.md` — Epic-level scope (5 fail mode + invariant 8종 + 용량 4 layer placeholder)
- **본문 step-by-step = MCT-171 의무**

### 다음 Story (sequential)

- **MCT-168** COMPLETED 2026-05-14 (hub#307 + data#59) — D1+D2 VERIFIED
- **MCT-169** (immediate local delete + tier promotion, D3+D10) — **진입 가능** (MCT-168 LAND 후 gate 충족)
- MCT-170 ∥ MCT-171 (engine reader ∥ DR runbook 본문) — MCT-168+169 LAND 후
- MCT-172 (Epic CLOSED, D9+D10 verify)

## Key References

- ADR-027 §D MCT-161 amendment: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
- **ADR-029 (신규, MCT-167 2026-05-14)**: `docs/adr/ADR-029-tier-promotion-single-source.md`
- EPIC-compactor-operations scope_manifest: `scope_manifests/EPIC-compactor-operations.yaml` (CLOSED 2026-05-14)
- **EPIC-tier-promotion-single-source scope_manifest**: `scope_manifests/EPIC-tier-promotion-single-source.yaml` (IN_PROGRESS, 2/6 milestone)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md`
- **EPIC-RESULTS (tier-promotion, IN_PROGRESS)**: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- MCT-174 reservation: `.codeforge/counters.json`
