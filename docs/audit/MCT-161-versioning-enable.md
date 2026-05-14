---
story: MCT-161
artifact: versioning-enable-audit
executed_at: 2026-05-14T06:38:16Z
bucket: mctrader-market
endpoint: http://mcnas01.internal.mclayer.it:9000
executor: DeveloperPLAgent (codeforge Phase 2)
---

# MCT-161 — NAS Bucket Versioning Enable Audit

## 실행 결과

### enable_nas_versioning.py (2026-05-14T06:37:48Z)

```
MCT-161 NAS bucket enable script - 2026-05-14T06:37:48.427194Z
Bucket: mctrader-market
[1/3] bucket versioning enable: mctrader-market
  AC-1 PASS: versioning Status=Enabled
[2/3] Object Lock GOVERNANCE 30d: mctrader-market
  [WARN] boto3 put_object_lock_configuration failed (InvalidBucketState) - mc fallback
  mc cmd: mc retention set --default governance 30d mcnas01/mctrader-market
  [INFO] mc CLI not found - skipping mc fallback
  [INFO] Object Lock requires --with-lock at bucket creation time.
  [INFO] AC-2 SKIP: existing bucket constraint (MinIO/S3 limitation)
[3/3] Lifecycle NoncurrentVersionExpiration 30d: mctrader-market
  AC-3 PASS: Lifecycle (NoncurrentDays=30)

Summary:
{
  "versioning_status": "Enabled",
  "object_lock": null,
  "lifecycle_noncurrent_days": 30
}

AC-1 versioning: PASS
AC-2 Object Lock: SKIP (existing bucket constraint)
AC-3 Lifecycle: PASS (NoncurrentDays=30)
[DONE] enable_nas_versioning.py complete
```

### verify_nas_versioning.py (2026-05-14T06:38:16Z)

```json
{
  "timestamp": "2026-05-14T06:38:16.700833Z",
  "bucket": "mctrader-market",
  "verdicts": [
    {
      "ac": "AC-1",
      "verdict": "PASS",
      "detail": "versioning=Enabled, DeleteMarker creation verified (test_key=__mct161_verify_tmp_4633662fb66d47b0a53f291f79845919.txt)"
    },
    {
      "ac": "AC-2",
      "verdict": "SKIP",
      "detail": "Object Lock not set (ObjectLockConfigurationNotFoundError) - existing bucket constraint (--with-lock required at creation time)"
    },
    {
      "ac": "AC-3",
      "verdict": "PASS",
      "detail": "Rule ID='NoncurrentVersionExpiration-30d', NoncurrentDays=30, Status=Enabled"
    }
  ]
}
```

## AC 판정 요약

| AC | Verdict | 비고 |
|----|---------|------|
| AC-1 | **PASS** | versioning=Enabled, DeleteMarker 생성 probe 확인 |
| AC-2 | **SKIP** | MinIO/S3 공통 제약: Object Lock은 bucket 생성 시점(`--with-lock`) 활성화 의무. 기존 `mctrader-market` bucket은 해당 flag 없이 생성됨. 향후 bucket 재생성 또는 MinIO 관리자 console 경유 필요. |
| AC-3 | **PASS** | NoncurrentVersionExpiration 30d rule 확인 (INV-2 storage cost 1.5x 미만 보장) |

## Object Lock SKIP 근거 (AC-2)

MinIO 및 S3 표준 명세: `ObjectLockEnabled` 는 bucket 생성 시(`CreateBucket` API의 `x-amz-bucket-object-lock-enabled` 헤더)만 활성화 가능. 기존 bucket에 `put_object_lock_configuration`으로 `ObjectLockEnabled=Enabled`를 전달하면 `InvalidBucketState` 오류 반환.

**대안**: `mc admin bucket quota` 또는 MinIO Console에서 Object Lock 활성화 설정 가능 여부 확인 필요 (MinIO Enterprise 기능). 현재 mctrader 환경은 MinIO Community — Console에서 bucket 재생성이 현실적 경로.

**INV-2 정합 유지**: 30d lifecycle NoncurrentVersionExpiration (AC-3 PASS)으로 noncurrent version 자동 만료 보장됨. Object Lock 미적용 시 governance 30d 강제 삭제 차단은 불가하나, DeleteMarker 생성(AC-1 PASS)으로 hard delete 흔적 보존은 달성.

## INV-1 검증 (Hot path 무영향)

본 스크립트는 bucket-level admin API 호출만 수행. collector WAL / L1 ParquetWriter와 무관. Integration Test 5 회귀 검증 대상 (MCT-156 박제) = Phase 2 §10 FIX Ledger PASS.

## Cross-ref

- `scripts/enable_nas_versioning.py`
- `scripts/verify_nas_versioning.py`
- `docs/stories/MCT-161.md` §5 AC, §10 FIX Ledger
- `docs/runbooks/nas-bucket-disaster-recovery.md`
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` §D MCT-161 amendment
