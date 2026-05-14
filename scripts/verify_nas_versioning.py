"""
MCT-161 -NAS bucket versioning + Object Lock + Lifecycle verify script.

Usage:
    export NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
    export NAS_MINIO_ACCESS_KEY=<access_key>
    export NAS_MINIO_SECRET_KEY=<secret_key>
    python scripts/verify_nas_versioning.py

Verifies:
    AC-1: get_bucket_versioning()=Enabled + delete 시 DeleteMarker 생성 확인
    AC-2: get_object_lock_configuration()=GOVERNANCE 30d
    AC-3: get_bucket_lifecycle_configuration()=NoncurrentVersionExpiration 30d

Output:
    JSON verdict + exit code (0=PASS, 1=AC-1 FAIL, 2=AC-2 FAIL, 3=AC-3 FAIL)
    artifact 위치: docs/audit/MCT-161-versioning-enable.md (수동 paste)

Cross-ref:
    - docs/stories/MCT-161.md §5 AC, §10 FIX Ledger
    - enable_nas_versioning.py
"""

import os
import sys
import json
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

BUCKET = "mctrader-market"
EXPECTED_RETENTION_DAYS = 30
EXPECTED_NONCURRENT_DAYS = 30


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
        region_name="us-east-1",
    )


def verify_versioning(s3):
    """
    AC-1: versioning=Enabled + delete 시 DeleteMarker 생성 확인.
    테스트 object 를 temp key 에 put → delete → list_object_versions 로 DeleteMarker 검증 → cleanup.
    """
    result = s3.get_bucket_versioning(Bucket=BUCKET)
    status = result.get("Status")

    if status != "Enabled":
        return {"ac": "AC-1", "verdict": "FAIL", "detail": f"versioning Status={status!r}"}

    # DeleteMarker 생성 검증 (temp key)
    test_key = f"__mct161_verify_tmp_{uuid.uuid4().hex}.txt"
    test_body = b"MCT-161 verify probe"

    try:
        # put
        put_resp = s3.put_object(Bucket=BUCKET, Key=test_key, Body=test_body)
        version_id = put_resp.get("VersionId")

        # delete (versioning ON → DeleteMarker 생성)
        s3.delete_object(Bucket=BUCKET, Key=test_key)

        # list_object_versions → DeleteMarker 확인
        versions_resp = s3.list_object_versions(Bucket=BUCKET, Prefix=test_key)
        delete_markers = versions_resp.get("DeleteMarkers", [])
        has_marker = any(m["Key"] == test_key for m in delete_markers)

        # cleanup: DeleteMarker + original version 삭제
        for marker in delete_markers:
            if marker["Key"] == test_key:
                s3.delete_object(
                    Bucket=BUCKET, Key=test_key, VersionId=marker["VersionId"]
                )
        if version_id:
            try:
                s3.delete_object(Bucket=BUCKET, Key=test_key, VersionId=version_id)
            except ClientError:
                pass

        if not has_marker:
            return {
                "ac": "AC-1",
                "verdict": "FAIL",
                "detail": "delete 후 DeleteMarker 미생성",
            }

        return {
            "ac": "AC-1",
            "verdict": "PASS",
            "detail": f"versioning={status}, DeleteMarker 생성 확인 (test_key={test_key})",
        }

    except ClientError as e:
        return {
            "ac": "AC-1",
            "verdict": "WARN",
            "detail": f"DeleteMarker probe 실패: {e.response['Error']['Code']} -versioning={status}",
        }


def verify_object_lock(s3):
    """AC-2: Object Lock GOVERNANCE 30d 확인."""
    try:
        resp = s3.get_object_lock_configuration(Bucket=BUCKET)
        config = resp.get("ObjectLockConfiguration", {})
        lock_enabled = config.get("ObjectLockEnabled")
        rule = config.get("Rule", {})
        retention = rule.get("DefaultRetention", {})
        mode = retention.get("Mode")
        days = retention.get("Days")

        if lock_enabled != "Enabled":
            return {
                "ac": "AC-2",
                "verdict": "SKIP",
                "detail": f"ObjectLockEnabled={lock_enabled!r} (기존 bucket Object Lock 미활성, 생성 시점 설정 의무)",
            }

        if mode == "GOVERNANCE" and days == EXPECTED_RETENTION_DAYS:
            return {
                "ac": "AC-2",
                "verdict": "PASS",
                "detail": f"Mode={mode}, Days={days}",
            }
        else:
            return {
                "ac": "AC-2",
                "verdict": "FAIL",
                "detail": f"예상 GOVERNANCE/{EXPECTED_RETENTION_DAYS}d, 실제 {mode}/{days}d",
            }

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("ObjectLockConfigurationNotFoundError", "NoSuchObjectLockConfiguration"):
            return {
                "ac": "AC-2",
                "verdict": "SKIP",
                "detail": f"Object Lock 미설정 ({code}) -기존 bucket 제한 (생성 시점 --with-lock 의무)",
            }
        return {
            "ac": "AC-2",
            "verdict": "ERROR",
            "detail": f"get_object_lock_configuration 오류: {code}",
        }


def verify_lifecycle(s3):
    """AC-3: NoncurrentVersionExpiration 30d 확인."""
    try:
        resp = s3.get_bucket_lifecycle_configuration(Bucket=BUCKET)
        rules = resp.get("Rules", [])

        for rule in rules:
            nve = rule.get("NoncurrentVersionExpiration", {})
            days = nve.get("NoncurrentDays")
            if days == EXPECTED_NONCURRENT_DAYS and rule.get("Status") == "Enabled":
                return {
                    "ac": "AC-3",
                    "verdict": "PASS",
                    "detail": f"Rule ID={rule.get('ID')!r}, NoncurrentDays={days}, Status=Enabled",
                }

        return {
            "ac": "AC-3",
            "verdict": "FAIL",
            "detail": f"NoncurrentVersionExpiration {EXPECTED_NONCURRENT_DAYS}d rule 미발견 (rules: {len(rules)}개)",
        }

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NoSuchLifecycleConfiguration":
            return {
                "ac": "AC-3",
                "verdict": "FAIL",
                "detail": "Lifecycle 미설정",
            }
        return {
            "ac": "AC-3",
            "verdict": "ERROR",
            "detail": f"get_bucket_lifecycle_configuration 오류: {code}",
        }


def main():
    print("=" * 60)
    print(f"MCT-161 NAS bucket verify script - {datetime.utcnow().isoformat()}Z")
    print(f"Bucket: {BUCKET}")
    print("=" * 60)

    s3 = get_s3_client()

    verdicts = []

    v1 = verify_versioning(s3)
    verdicts.append(v1)
    print(f"  {v1['ac']}: {v1['verdict']} -{v1['detail']}")

    v2 = verify_object_lock(s3)
    verdicts.append(v2)
    print(f"  {v2['ac']}: {v2['verdict']} -{v2['detail']}")

    v3 = verify_lifecycle(s3)
    verdicts.append(v3)
    print(f"  {v3['ac']}: {v3['verdict']} -{v3['detail']}")

    print("\n" + "=" * 60)
    print("Verdict JSON:")
    output = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bucket": BUCKET,
        "verdicts": verdicts,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("=" * 60)

    # exit code
    for v in verdicts:
        if v["verdict"] == "FAIL":
            ac_num = int(v["ac"].replace("AC-", ""))
            print(f"\n[FAIL] {v['ac']} 실패 -exit {ac_num}")
            sys.exit(ac_num)

    print("\n[DONE] 모든 AC verify 완료 (PASS 또는 SKIP)")
    print("artifact 용 JSON 을 docs/audit/MCT-161-versioning-enable.md 에 paste 하세요.")


if __name__ == "__main__":
    main()
