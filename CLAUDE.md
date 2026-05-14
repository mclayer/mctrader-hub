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

## Key References

- ADR-027 §D MCT-161 amendment: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
- EPIC-compactor-operations scope_manifest: `scope_manifests/EPIC-compactor-operations.yaml` (CLOSED 2026-05-14)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md`
- MCT-174 reservation: `.codeforge/counters.json`
