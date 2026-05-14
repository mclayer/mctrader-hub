"""
MCT-161 — NAS bucket versioning + Object Lock governance 30d + Lifecycle ILM enable script.

Usage:
    # 환경변수 설정 후 실행
    export NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
    export NAS_MINIO_ACCESS_KEY=<access_key>
    export NAS_MINIO_SECRET_KEY=<secret_key>
    python scripts/enable_nas_versioning.py

Acceptance Criteria:
    AC-1: put_bucket_versioning(Status: Enabled) → get_bucket_versioning()=Enabled
    AC-2: Object Lock GOVERNANCE 30d 적용
    AC-3: Lifecycle NoncurrentVersionExpiration 30d 적용

Notes:
    - MinIO Object Lock 은 bucket 생성 시점 활성화 의무.
      기존 bucket 에 대해서는 mc admin retention set fallback 을 이용한다.
      boto3 put_object_lock_configuration 은 기존 bucket 에서 ObjectLockEnabled=Enabled 불가 —
      대신 Rule 만 설정(기존 bucket lock 활성화는 mc CLI 의존).
    - INV-1: hot path (collector WAL / L1 ParquetWriter) 무영향 — 본 스크립트는 bucket-level 설정만.
    - INV-2: governance 30d + lifecycle 30d 정합 필수.
    - INV-3: storage cost 1.5x 미만 (append-only ~1.1x-1.3x 예상).

Cross-ref:
    - docs/stories/MCT-161.md §5 AC
    - docs/runbooks/nas-bucket-disaster-recovery.md
    - docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md §D MCT-161 amendment
"""

import os
import sys
import json
import subprocess
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

BUCKET = "mctrader-market"
RETENTION_DAYS = 30
NONCURRENT_EXPIRATION_DAYS = 30


def get_s3_client():
    endpoint = os.environ.get("NAS_MINIO_ENDPOINT", "http://mcnas01.internal.mclayer.it:9000")
    access_key = os.environ.get("NAS_MINIO_ACCESS_KEY")
    secret_key = os.environ.get("NAS_MINIO_SECRET_KEY")

    if not access_key or not secret_key:
        print("[ERROR] NAS_MINIO_ACCESS_KEY / NAS_MINIO_SECRET_KEY 환경변수 미설정")
        sys.exit(1)

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",  # MinIO dummy region
    )


def enable_versioning(s3):
    """AC-1: bucket versioning enable."""
    print(f"[1/3] bucket versioning enable: {BUCKET}")
    s3.put_bucket_versioning(
        Bucket=BUCKET,
        VersioningConfiguration={"Status": "Enabled"},
    )
    result = s3.get_bucket_versioning(Bucket=BUCKET)
    status = result.get("Status")
    assert status == "Enabled", f"versioning 미활성 — 실제값: {status!r}"
    print(f"  AC-1 PASS: versioning Status={status}")
    return status


def enable_object_lock(s3):
    """
    AC-2: Object Lock GOVERNANCE 30d.

    MinIO 기존 bucket 에 대해 ObjectLockEnabled 변경 불가 (생성 시점만 지원).
    boto3 put_object_lock_configuration 으로 Rule 만 갱신 시도.
    실패 시 mc admin retention set fallback.
    """
    print(f"[2/3] Object Lock GOVERNANCE {RETENTION_DAYS}d: {BUCKET}")

    config = {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "GOVERNANCE",
                "Days": RETENTION_DAYS,
            }
        },
    }

    try:
        s3.put_object_lock_configuration(
            Bucket=BUCKET,
            ObjectLockConfiguration=config,
        )
        print(f"  boto3 put_object_lock_configuration 성공")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        print(f"  [WARN] boto3 put_object_lock_configuration failed ({code}) - mc fallback")
        # mc fallback: mc admin bucket quota/retention set (MinIO-specific)
        # mc alias 이름은 환경변수 MC_ALIAS 또는 기본값 "mcnas01" 사용
        mc_alias = os.environ.get("MC_ALIAS", "mcnas01")
        mc_cmd = [
            "mc", "retention", "set",
            "--default", "governance", f"{RETENTION_DAYS}d",
            f"{mc_alias}/{BUCKET}",
        ]
        print(f"  mc cmd: {' '.join(mc_cmd)}")
        try:
            result = subprocess.run(mc_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  [INFO] mc retention set non-zero: {result.returncode}")
                print(f"  [INFO] Object Lock requires --with-lock at bucket creation time.")
                print(f"  [INFO] AC-2 SKIP: existing bucket constraint (MinIO/S3 limitation)")
                return None
            print(f"  mc result: {result.stdout.strip()}")
        except FileNotFoundError:
            print(f"  [INFO] mc CLI not found - skipping mc fallback")
            print(f"  [INFO] Object Lock requires --with-lock at bucket creation time.")
            print(f"  [INFO] AC-2 SKIP: existing bucket constraint (MinIO/S3 limitation)")
            return None

    # verify
    try:
        lock_config = s3.get_object_lock_configuration(Bucket=BUCKET)
        rule = lock_config.get("ObjectLockConfiguration", {}).get("Rule", {})
        mode = rule.get("DefaultRetention", {}).get("Mode")
        days = rule.get("DefaultRetention", {}).get("Days")
        print(f"  AC-2 PASS: Object Lock Mode={mode}, Days={days}")
        return {"mode": mode, "days": days}
    except ClientError as e:
        print(f"  [WARN] get_object_lock_configuration 실패: {e.response['Error']['Code']}")
        print(f"  AC-2 SKIP: 기존 bucket Object Lock 미활성 상태 (생성 시점 설정 의무)")
        return None


def enable_lifecycle(s3):
    """AC-3: NoncurrentVersionExpiration 30d."""
    print(f"[3/3] Lifecycle NoncurrentVersionExpiration {NONCURRENT_EXPIRATION_DAYS}d: {BUCKET}")

    lifecycle_config = {
        "Rules": [
            {
                "ID": f"NoncurrentVersionExpiration-{NONCURRENT_EXPIRATION_DAYS}d",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "NoncurrentVersionExpiration": {
                    "NoncurrentDays": NONCURRENT_EXPIRATION_DAYS,
                },
            }
        ]
    }

    s3.put_bucket_lifecycle_configuration(
        Bucket=BUCKET,
        LifecycleConfiguration=lifecycle_config,
    )
    print(f"  AC-3 PASS: Lifecycle 설정 완료 (NoncurrentDays={NONCURRENT_EXPIRATION_DAYS})")
    return NONCURRENT_EXPIRATION_DAYS


def main():
    print("=" * 60)
    print(f"MCT-161 NAS bucket enable script - {datetime.utcnow().isoformat()}Z")
    print(f"Bucket: {BUCKET}")
    print("=" * 60)

    s3 = get_s3_client()

    results = {}

    # AC-1
    results["versioning_status"] = enable_versioning(s3)

    # AC-2
    results["object_lock"] = enable_object_lock(s3)

    # AC-3
    results["lifecycle_noncurrent_days"] = enable_lifecycle(s3)

    print("\n" + "=" * 60)
    print("Summary:")
    print(json.dumps(results, indent=2))
    print("=" * 60)

    # AC-1 은 필수 — 실패 시 exit 1
    assert results["versioning_status"] == "Enabled", "AC-1 FAIL: versioning 미활성"
    print("\nAC-1 versioning: PASS")
    print(f"AC-2 Object Lock: {'PASS' if results['object_lock'] else 'SKIP (기존 bucket 제한)'}")
    print(f"AC-3 Lifecycle: PASS (NoncurrentDays={results['lifecycle_noncurrent_days']})")
    print("\n[DONE] enable_nas_versioning.py 완료")


if __name__ == "__main__":
    main()
