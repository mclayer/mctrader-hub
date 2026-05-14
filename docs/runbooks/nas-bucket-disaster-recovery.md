---
runbook: nas-bucket-disaster-recovery
created: 2026-05-14
story: MCT-161
related_adrs:
  - "ADR-027 §D MCT-161 amendment — NAS bucket versioning + Object Lock + Lifecycle ILM"
trigger: "NAS data loss / hard delete 실수 / version 복원 필요 / MCT-153 유사 손실 감지"
owner: Operations
cadence: ad-hoc (incident response)
severity_scope: P1 (data loss) / P2 (partial delete)
---

# NAS Bucket Disaster Recovery Runbook

> **Story trail**: [MCT-161](../stories/MCT-161.md) · **Epic**: EPIC-compactor-operations
> **Prerequisite**: bucket versioning=Enabled (MCT-161 AC-1), NoncurrentVersionExpiration 30d (AC-3)
> **Cross-ref**: MCT-153 (4.2 GiB 손실 원인 박제) · RETRO-MCT-156 §13.5.2 · ADR-027 §D MCT-161 amendment

본 runbook 은 `mctrader-market` NAS bucket 에서 데이터 손실(hard delete / 잘못된 GC / 손상)이 발생했을 때 version history 에서 복원하는 step-by-step 절차. bucket versioning 활성화(MCT-161 AC-1) 이후 신규 write 되는 object 에 대해 적용됨.

---

## Prerequisites

| 항목 | 요구사항 |
|---|---|
| bucket versioning | Enabled (AC-1 PASS — `scripts/verify_nas_versioning.py` 확인) |
| NAS 접근 | mctrader 호스트가 mcnas01.internal.mclayer.it:9000 도달 가능 |
| 환경변수 | NAS_MINIO_ENDPOINT / NAS_MINIO_ACCESS_KEY / NAS_MINIO_SECRET_KEY |
| boto3 | pip install boto3 |
| 복원 가능 window | versioning 활성화 이후 write된 object + 30d 이내 noncurrent version |

---

## Trigger 조건

- NAS bucket 에서 object 미스가 발견됨 (조회 실패, 크기 0, 손상)
- GC 또는 mc 명령으로 의도치 않은 hard delete 발생
- MCT-153 유사 손실 (4.2 GiB / 1370 obj 급 대량 손실)
- compactor 또는 uploader 버그로 일부 L1 파일 삭제됨

---

## Step 1 — Triage (목표: 5분 이내)

### 1a. 손실 범위 파악

```bash
# 전체 object count (기대값 대비 비교)
aws s3 ls s3://mctrader-market --recursive --summarize \
  --endpoint-url http://mcnas01.internal.mclayer.it:9000 2>&1 | tail -3
```

```python
# Python: 특정 prefix 에서 version 있는 object vs current object 비교
import boto3, os
s3 = boto3.client(
    's3',
    endpoint_url=os.environ['NAS_MINIO_ENDPOINT'],
    aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'],
    aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'],
    region_name='us-east-1',
)
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket='mctrader-market', Prefix='<your-prefix>'):
    for dm in page.get('DeleteMarkers', []):
        print(f"DeleteMarker: {dm['Key']} versionId={dm['VersionId']} LastModified={dm['LastModified']}")
```

### 1b. 손실 시점 식별

- DeleteMarker 의 `LastModified` 가 손실 추정 시점과 일치하는지 확인
- 특정 channel / symbol / date 범위에 집중 (예: `upbit/orderbooksnapshot/2026-05-12/`)

### 1c. 손실 규모 분류

| 분류 | 기준 | 조치 |
|---|---|---|
| P1 (대량) | 100+ obj 또는 1 GiB 이상 | 즉시 이 runbook Step 2-5 완료, RETRO 의무 |
| P2 (소량) | 10-100 obj | Step 2-4 진행, Postmortem optional |
| P3 (1건) | 1-9 obj | Step 2-3 직접 복원, audit log 만 박제 |

---

## Step 2 — Version history 조회

```python
# 손실된 key 의 version list (DeleteMarker + 이전 version) 확인
import boto3, os

s3 = boto3.client(
    's3',
    endpoint_url=os.environ['NAS_MINIO_ENDPOINT'],
    aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'],
    aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'],
    region_name='us-east-1',
)

BUCKET = 'mctrader-market'
PREFIX = '<손실된 object key prefix>'  # 예: 'upbit/orderbooksnapshot/2026-05-12/'

resp = s3.list_object_versions(Bucket=BUCKET, Prefix=PREFIX)

print("=== DeleteMarkers ===")
for dm in resp.get('DeleteMarkers', []):
    print(f"  {dm['Key']} | versionId={dm['VersionId']} | {dm['LastModified']}")

print("=== Versions (복원 후보) ===")
for v in resp.get('Versions', []):
    print(f"  {v['Key']} | versionId={v['VersionId']} | size={v['Size']} | {v['LastModified']} | isLatest={v['IsLatest']}")
```

**핵심 식별 목표**:
- DeleteMarker 의 `VersionId` = 현재 "삭제됨" 상태를 나타내는 마커
- 그 직전 version (IsLatest=False 중 LastModified 최신) = 복원 대상

---

## Step 3 — Restore-from-version

### 3a. 단일 object 복원

```python
# DeleteMarker 를 제거하면 이전 version 이 current 로 복구됨
s3.delete_object(
    Bucket='mctrader-market',
    Key='<target_key>',
    VersionId='<DeleteMarker_VersionId>',  # DeleteMarker 의 VersionId
)
# 또는 이전 version 을 현재 key 로 복사 (명시적 restore)
s3.copy_object(
    CopySource={
        'Bucket': 'mctrader-market',
        'Key': '<target_key>',
        'VersionId': '<previous_VersionId>',
    },
    Bucket='mctrader-market',
    Key='<target_key>',
)
```

### 3b. 대량 복원 스크립트

```python
import boto3, os

s3 = boto3.client(
    's3',
    endpoint_url=os.environ['NAS_MINIO_ENDPOINT'],
    aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'],
    aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'],
    region_name='us-east-1',
)

BUCKET = 'mctrader-market'
PREFIX = '<손실된 prefix>'

paginator = s3.get_paginator('list_object_versions')
restored = 0
skipped = 0

for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
    for dm in page.get('DeleteMarkers', []):
        key = dm['Key']
        dm_version_id = dm['VersionId']

        # DeleteMarker 삭제 → 이전 version current 복원
        try:
            s3.delete_object(Bucket=BUCKET, Key=key, VersionId=dm_version_id)
            print(f"  RESTORED: {key}")
            restored += 1
        except Exception as e:
            print(f"  SKIP {key}: {e}")
            skipped += 1

print(f"복원 완료: {restored}건, 스킵: {skipped}건")
```

**주의**: NoncurrentVersionExpiration 30d — versioning 활성화 전 null version 은 복원 불가 (Edge-1). 30d 이내 noncurrent version 만 복원 가능.

---

## Step 4 — Verify

### 4a. 복원된 object 검증

```bash
# 복원된 key 의 size / ETag 확인
aws s3api head-object \
  --bucket mctrader-market \
  --key <target_key> \
  --endpoint-url http://mcnas01.internal.mclayer.it:9000
```

```python
# Python: 복원된 object 의 metadata 검증
resp = s3.head_object(Bucket='mctrader-market', Key='<target_key>')
print(f"ContentLength: {resp['ContentLength']}")
print(f"ETag: {resp['ETag']}")
print(f"LastModified: {resp['LastModified']}")
```

### 4b. 복원 후 Integration Test 실행 (INV-1 검증)

```bash
# Integration Test 5 회귀 (MCT-156 박제 기준)
cd /path/to/mctrader-data
python -m pytest tests/integration/test_nas_*.py -v --timeout=60
```

### 4c. audit log 박제

- `docs/audit/incident-YYYY-MM-DD-restore.md` 파일 신규 생성
- 포함 항목: 손실 key/count/size, 복원 key/count, 스크립트 stdout, 검증 결과

---

## Step 5 — Postmortem

### 5a. Root cause 분석

| 손실 유형 | 확인 포인트 |
|---|---|
| GC 버그 | MCT-153 유형 — compactor GC dry-run → real-run 분기 확인 |
| 잘못된 mc 명령 | `mc rm --recursive` 오타 또는 prefix 오지정 |
| uploader 버그 | retry_queue 재처리 중 중복 삭제 |
| NAS 디스크 장애 | SMART/DSM Storage Manager → btrfs scrub 결과 확인 |

### 5b. RETRO 작성

- `docs/retros/RETRO-incident-YYYY-MM-DD-data-loss.md` 신규 생성 (MCT-161 RETRO 패턴 준수)
- root cause + 재발 방지 action + 손실 규모 박제

### 5c. MCT-153 Cross-ref 박제 (대량 손실 시)

- RETRO-MCT-156 §13.5.2 참조 — 동일 유형인지 비교
- 새로운 prevention 조치 식별 → ADR-027 §D amendment 추가 고려

---

## 완료 기준 (Story AC-4)

- [ ] Step 1 Triage: 손실 범위 + 시점 식별 완료
- [ ] Step 2 Version 조회: DeleteMarker + 복원 가능 version list 확인
- [ ] Step 3 Restore: 복원 스크립트 실행, restored 건수 확인
- [ ] Step 4 Verify: 복원 object metadata + Integration Test 통과
- [ ] Step 5 Postmortem: audit log + RETRO 박제

**restore success rate 목표**: versioning 활성화(MCT-161 AC-1 PASS) 이후 write된 object 기준 ≥ 95% (DeleteMarker 보존된 version 한정)

---

## Edge case (2)

- **Edge-1**: MCT-161 versioning enable 이전 null version (1884 L1 parquet, forward-only 누적분) — restore 불가. list_object_versions 에서 `VersionId=null` 로 식별됨.
- **Edge-2**: 30d NoncurrentVersionExpiration 경과 version — lifecycle ILM 에 의해 만료됨. 30d window 내에서만 restore 보장.

---

## 관련 명령 참고

```bash
# MinIO mc CLI (설치된 경우)
mc alias set mcnas01 http://mcnas01.internal.mclayer.it:9000 <access_key> <secret_key>
mc ls --versions mcnas01/mctrader-market/<prefix>
mc cp --version-id <versionId> mcnas01/mctrader-market/<key> mcnas01/mctrader-market/<key>

# aws CLI (boto3 endpoint 대체)
aws --endpoint-url http://mcnas01.internal.mclayer.it:9000 \
    s3api list-object-versions --bucket mctrader-market --prefix <prefix>
```

---

## Cross-ref

- `docs/stories/MCT-161.md` §5 AC-4 / §10 FIX Ledger
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` §D MCT-161 amendment
- `scripts/enable_nas_versioning.py` — 초기 설정 스크립트
- `scripts/verify_nas_versioning.py` — versioning 상태 verify
- `docs/audit/MCT-161-versioning-enable.md` — 초기 enable 실행 결과
- MCT-153 / RETRO-MCT-156 §13.5.2 — 4.2 GiB 손실 원인 박제 (본 runbook 필요성 근거)
