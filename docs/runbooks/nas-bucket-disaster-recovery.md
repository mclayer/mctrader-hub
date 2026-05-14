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

## Epic-level DR scope (MCT-167 stub 확장, 본문 = MCT-171)

> **상태**: stub placeholder — 본문 = MCT-171 (DR runbook 본문 + invariant 8종 + 용량 제한 정책 Story) 작성 의무.
>
> **MCT-167 (governance singleton) scope** = 본 stub 확장만 — Epic-level DR 의 5 fail mode 박제 (placeholder), 본문 step-by-step = MCT-171 의무.

EPIC-tier-promotion-single-source (ADR-029 publish 후) 의 DR scope 확장:

### 5 Epic-level Fail Mode (MCT-171 본문 author)

1. **L1 NAS PUT fail** (R1, ADR-029 D1+D2 정합):
   - **검출**: compactor L1 path 에서 DualWriter status = `local_only` 또는 `hard_floor_blocked` 발생
   - **대응**: retry_queue 처리 + Prometheus alert (`mctrader_dual_write_result_total{tier=L1,status=local_only}` Counter 증가)
   - **escalate**: `hard_floor_blocked` 시 MANUAL_GATE (NAS unreachable + retry_queue 1000seg/10GB threshold 초과)
   - **본문 (MCT-171)**: step-by-step 진단 + retry_queue 처리 + Slack notification + restart 절차

2. **NAS unreachable (capacity-bounded ingest block)** (R2, ADR-029 D5 + D11 정합):
   - **검출**: NAS health check fail + WAL local volume usage >= 30 GiB 또는 L1 local volume usage >= 20 GiB
   - **대응**: collector ingest soft stop (graceful + alert) + L1 compactor pause + 4 layer capacity alert chain (80% / 95% / hard limit)
   - **본문 (MCT-171)**: NAS 복구 절차 + capacity 모니터링 + ingest 재개 절차

3. **Clock drift / version mismatch** (R4 ambiguity invariant false delete risk, ADR-029 D3 + D10 정합):
   - **검출**: NAS HEAD verify 시 version/etag eventual consistency 미스 (race condition)
   - **대응**: etag exact match 재시도 + sha256 verify + retry on NoSuchKey (3회 backoff)
   - **본문 (MCT-171)**: NAS MinIO clock drift 검출 + Synology NTP 동기 + version history 복원 절차

4. **Rate-limit / API throttle** (R6 신규, NAS MinIO API rate-limit):
   - **검출**: NAS MinIO `429 TooManyRequests` 또는 connection pool 고갈
   - **대응**: exponential backoff retry + connection pool 확대 + circuit breaker
   - **본문 (MCT-171)**: NAS MinIO connection pool tuning + retry policy 튜닝

5. **Replication failover (mcnas01 → mcnas02)** (R7 신규, ADR-029 D6 정합, MCT-174 의무):
   - **검출**: mcnas01 hardware fail / network unreachable / replication lag > threshold
   - **대응**: reader endpoint cutover (mcnas01 → mcnas02) + mcnas02 replica 검증 + 정상 운영 시 mcnas01 복구
   - **본문 (MCT-174)**: cross-NAS replication setup + failover 절차 + replica 검증 invariant
   - **현재 상태**: mcnas02 NAS box 물리 부재 (MCT-161 D2=D 결정 답습). MCT-174 별 backlog Story 의무.

### Invariant 8종 (MCT-171 본문 author)

MCT-151 InvariantHarness 7종 (sha256 / object count / row count / column count / column name order / dtype identity / schema_version pin) + **신규 8번째**:

- **8. ambiguity invariant** (ADR-029 D10 정합) — "tier promotion 완료 후 동일 logical entity (schema_version × tier × exchange × symbol × date × hour × node) 가 NAS + local 양쪽 동시 존재 시 violation". MCT-172 의 cross-Story verify scope.

### 용량 제한 4 layer (MCT-171 본문 author, ADR-029 D11 정합)

| Layer | Hard Limit | Threshold Action |
|---|---|---|
| WAL local | 30 GiB | collector ingest block |
| L1 local | 20 GiB | oldest L1 FIFO delete after NAS verify |
| NAS bucket | target 500 GiB / hard 1 TiB | L3 cold archive 이전 (별 Story) |
| Host disk | 200 GiB | alert + manual cleanup |

---

## Epic-level DR 본문 (MCT-171 LAND 2026-05-14, Codex review 9 결정점 합성 박제)

> **상태**: 본문 정식 (stub 격상). MCT-171 Phase 1 LAND 분. 본문 = 5 fail mode step-by-step + invariant 8종 enforcement + 4 layer capacity 운영 매뉴얼.

### Quick triage flowchart (운영자 첫 act)

알람 수신 시 다음 순서:

```
1. NAS reachable? (mc admin info mcnas01)
   - NO → Fail mode (2) NAS unreachable: §3.2 절차
   - YES → next
2. WAL/L1/NAS/Host capacity ≥ 80%?
   - YES → Fail mode (2) 하위 disk full: §3.2 절차 + capacity probe report
   - NO → next
3. mctrader_dual_write_result_total{status=local_only} 증가?
   - YES → Fail mode (1) L1 NAS PUT fail: §3.1 절차
   - NO → next
4. NAS 429 TooManyRequests log?
   - YES → Fail mode (4) Rate-limit: §3.4 절차
   - NO → next
5. ambiguity invariant violation total > 0?
   - YES → Fail mode (3) Clock drift / version mismatch: §3.3 절차
   - NO → Fail mode (5) Replication failover (MCT-174 LAND 후 deploy): §3.5 절차
```

### §3.1 Fail Mode (1) — L1 NAS PUT fail

**Priority**: 2번째 (data loss risk: NAS unreachable 다음 수준)

**검출 신호**:
- Prometheus: `mctrader_dual_write_result_total{tier=L1,status=local_only}` Counter 증가 (1min rate > 5/min)
- Prometheus: `mctrader_dual_write_retry_queue_depth` Gauge > 100 (10min sustained)
- Slack alert: `[ALERT] L1 NAS PUT fail rate spike — retry_queue accumulating`

**진단 절차** (5분 이내):

```bash
# 1. retry_queue 상태 점검
docker exec mctrader-data python -c "
from mctrader_data.nas_storage.retry_queue import RetryQueue
rq = RetryQueue.from_default()
print(f'queue depth: {rq.depth()}')
print(f'oldest entry age: {rq.oldest_age()}s')
print(f'last successful PUT: {rq.last_success_ts()}')"

# 2. NAS reachability + capacity
docker exec mctrader-data mc admin info mcnas01
docker exec mctrader-data mc du mcnas01/mctrader-market

# 3. dual_write log 조회 (최근 100건)
docker logs mctrader-data --since 10m 2>&1 | grep "dual_write_result" | tail -100
```

**복구 절차**:

1. **NAS reachable + capacity OK** (retry 정상 가능):
   ```bash
   # retry_queue 수동 drain 시작
   docker exec mctrader-data python -m mctrader_data.cli retry-queue --drain --batch-size 10
   # 5분 후 queue depth 감소 verify
   ```

2. **NAS unreachable**: Fail Mode (2) escalate (§3.2 절차)

3. **NAS capacity 95% 도달**: 즉시 L3 cold archive 이전 절차 trigger (별 Story 의무)

4. **hard_floor_blocked** (retry_queue > 10GB or > 1000 segments):
   - MANUAL_GATE: 운영자 결재 필요
   - Slack: @oncall + @data-platform tag
   - escalate: Fail Mode (2) 동치 처리

**Verify**:
- `mctrader_dual_write_result_total{status=local_only}` rate → 0/min
- `mctrader_dual_write_retry_queue_depth` → 0
- NAS bucket `tier=L1/` prefix 의 최근 segment 출현 verify

**Postmortem**:
- audit log 박제 (`docs/audit/MCT-171-fail-mode-1-<date>.md`)
- root cause classification: NAS 측 (network / capacity / API) vs mctrader 측 (DualWriter bug / WAL corrupt)
- ADR-027 §D5 retry_queue 정책 보강 필요 시 amendment 발의

---

### §3.2 Fail Mode (2) — NAS unreachable + capacity-bounded ingest block

**Priority**: **최상위** (RPO ≠ 0 risk, 시장 실시간 data 손실)

**하위 trigger**: disk full (WAL/L1/Host capacity ≥ 95%) 도 본 mode 하위 (운영자 동일 절차 적용)

**검출 신호**:
- Prometheus: `mctrader_capacity_threshold_ratio{layer=WAL_local}` >= 0.95 또는 `{layer=L1_local}` >= 0.95
- Prometheus: `mctrader_ingest_blocked_total{reason=nas_unreachable}` Counter 증가
- Prometheus: NAS health probe `up{job=nas_minio}` == 0 (5min sustained)
- Slack alert: `[CRITICAL] NAS unreachable + capacity hard limit — ingest blocked`

**진단 절차** (3분 이내):

```bash
# 1. NAS reachability 즉시 verify
docker exec mctrader-data mc admin info mcnas01 || echo "NAS UNREACHABLE"

# 2. 4 layer capacity report
docker exec mctrader-data python -c "
from mctrader_data.capacity_probe import CapacityProbe
probe = CapacityProbe.from_default()
report = probe.probe_once()
print(report.summary())"

# 3. collector ingest state
docker exec mctrader-data python -c "
from mctrader_data.ingest_blocker import IngestBlocker
ib = IngestBlocker.from_default()
print(f'state: {ib.state()}')
print(f'last_block_reason: {ib.last_block_reason()}')"

# 4. network 진단 (NAS host ping + port check)
docker exec mctrader-data ping -c 3 mcnas01.internal.mclayer.it
docker exec mctrader-data nc -zv mcnas01.internal.mclayer.it 9000
```

**복구 절차**:

1. **NAS 측 복구** (Synology NAS 측 트리거):
   - Synology DSM 콘솔 접속 (`https://mcnas01.internal.mclayer.it:5001`)
   - MinIO 컨테이너 status 확인 + restart 필요 시 진행
   - network / firewall / DNS 정상화

2. **NAS reachable 회복 후** (mctrader 측 절차):
   ```bash
   # 1. dual_write retry_queue drain
   docker exec mctrader-data python -m mctrader_data.cli retry-queue --drain --batch-size 20
   # 2. capacity_probe 5분 sample → 80% 이하 확인
   # 3. ingest_blocker state == NORMAL 자동 전이 verify (90% unblock hysteresis)
   docker exec mctrader-data python -c "
   from mctrader_data.ingest_blocker import IngestBlocker
   print(IngestBlocker.from_default().state())"  # expected: NORMAL
   ```

3. **WAL/L1 capacity 95% hard limit 도달 + NAS 복구 지연**:
   - **option A** (data 우선): collector graceful stop (manual gate)
   - **option B** (운영 우선): WAL segment manual rotate + L1 oldest FIFO delete (NAS verify 없이 cold path 만 정리)
   - Slack: @oncall + @data-platform escalate

**Verify**:
- `up{job=nas_minio}` == 1
- `mctrader_capacity_threshold_ratio{layer=*}` < 0.95
- `mctrader_ingest_blocked_total` rate → 0/min
- collector ingest 정상 재개 (rate 정상 수준 회복)

**Postmortem**:
- audit log + Slack 박제
- NAS RTO 측정 (down → up time)
- WAL/L1 capacity 도달 시점 + drain window 측정 (graceful drain 정상 동작 verify)
- ingest_blocker hysteresis 전이 그래프 박제

---

### §3.3 Fail Mode (3) — Clock drift / version mismatch (ambiguity invariant 트리거 가능)

**Priority**: 4번째 (detective only, data 손실 직접 trigger 0)

**ambiguity invariant 트리거 가능성 명시** (Codex review 보완): clock drift 가 NAS HEAD eventual consistency 미스 유발 → D3 local delete fail → NAS+local 양쪽 동시 존재 → ambiguity invariant violation 발생.

**검출 신호**:
- Prometheus: `mctrader_invariant_violation_total{invariant_name=ambiguity}` Counter 증가
- Prometheus: `nas_reader_ambiguity_total` Counter 증가 (MCT-170 LAND, engine reader 측)
- mctrader log: `verify_no_ambiguity FAIL` 발생
- Slack alert: `[WARN] ambiguity invariant violation — clock drift suspected`

**진단 절차**:

```bash
# 1. NAS MinIO 시각 확인
docker exec mctrader-data mc admin info mcnas01 | grep -i time

# 2. mctrader host NTP status
docker exec mctrader-data chronyc tracking 2>/dev/null || timedatectl status

# 3. clock drift 측정 (NAS - host)
docker exec mctrader-data python -c "
import datetime, requests
nas_time_resp = requests.head('http://mcnas01.internal.mclayer.it:9000/').headers.get('Date')
nas_dt = datetime.datetime.strptime(nas_time_resp, '%a, %d %b %Y %H:%M:%S %Z')
host_dt = datetime.datetime.utcnow()
print(f'drift: {(host_dt - nas_dt).total_seconds()}s')"
```

**복구 절차**:

1. **drift > 1초**: NAS MinIO NTP 동기 재실행
   - Synology DSM → Control Panel → Regional Options → Time → Synchronize with NTP server (`pool.ntp.org`)
2. **drift < 1초 + ambiguity 지속**: version history 복원 절차 (§Step 2-3 본 runbook 위 본문)
3. **ambiguity 자동 해소 confirm**: 1h periodic sweep 후 `mctrader_invariant_violation_total{invariant_name=ambiguity}` rate → 0/min verify

**Verify**:
- NAS - host clock drift < 1초
- ambiguity violation Counter rate → 0/min
- 1h periodic InvariantHarness sweep ALL PASS

**Postmortem**:
- NTP 동기 빈도 정책 검토 (현재 default chrony 1024s interval 적정성)
- ambiguity 발생 시점 ↔ clock drift 측정값 상관관계 audit

---

### §3.4 Fail Mode (4) — Rate-limit / API throttle

**Priority**: 3번째 (capacity 미도달 시 transient, retry 정상 가능)

**검출 신호**:
- Prometheus: NAS MinIO 429 response rate > 5/min
- mctrader log: `requests.exceptions.HTTPError: 429 Too Many Requests`
- connection pool 고갈: `urllib3.exceptions.MaxRetryError`

**진단 절차**:

```bash
# 1. recent 429 errors
docker logs mctrader-data --since 5m 2>&1 | grep "429" | wc -l

# 2. connection pool status
docker exec mctrader-data python -c "
from mctrader_data.nas_storage.nas_uploader import NASUploader
up = NASUploader.from_default()
print(f'pool_size: {up.pool_size()}')
print(f'pool_active: {up.pool_active()}')"

# 3. NAS MinIO API rate
docker exec mctrader-data mc admin trace mcnas01 --verbose 2>&1 | head -50
```

**복구 절차**:

1. **transient 429** (5min 내 자연 회복):
   - 자동 exponential backoff retry 의존 (개입 0)
2. **sustained 429** (10min 이상):
   - connection pool 확대: `NAS_MINIO_POOL_SIZE` env 50 → 100
   - circuit breaker manual trigger (NASUploader 측 5min cooldown)
   - mctrader-data 컨테이너 restart (pool 초기화)
3. **NAS API throttle** (NAS 측 정책 변경):
   - Synology MinIO config 측 rate-limit policy 검토 + 조정

**Verify**:
- 429 rate → 0/min
- connection pool active < pool_size × 80%

**Postmortem**:
- rate-limit 발생 시점 ↔ collector ingest spike 상관관계
- ADR-027 §retry policy amendment 필요 시 발의

---

### §3.5 Fail Mode (5) — Replication failover (mcnas01 → mcnas02)

**Priority**: 최하위 (mcnas02 물리 부재 상태에서는 deploy 0, MCT-174 LAND 후 진입)

**현재 상태**: MCT-174 reservation active. mcnas02 NAS box 물리 도입 후 본 절차 deploy.

**검출 신호** (MCT-174 LAND 후):
- mcnas01 hardware fail (Synology NAS 측 alert)
- network unreachable (5min sustained)
- replication lag > 10min (MCT-174 LAND 후 정의)

**복구 절차** (MCT-174 LAND 후 본문):
- engine reader endpoint cutover (mcnas01 → mcnas02, `NAS_MINIO_ENDPOINT` env update)
- mcnas02 replica 검증 invariant (MCT-174 의무 정의)
- 정상 운영 시 mcnas01 복구

**현 시점 절차** (MCT-174 미LAND):
- mcnas01 단일 의존, 본 fail mode 발생 = data 손실 risk HIGH
- 운영 절차: NAS bucket versioning 의존 (MCT-161 LAND), 30d window 내 version 복원 (본 runbook §Step 2-3)

---

## §4 Invariant 8종 enforcement 본문 (MCT-171 LAND)

InvariantHarness (`mctrader-data/src/mctrader_data/nas_migration/invariant_harness.py`) 8종 = MCT-151 7종 + ambiguity 8번째 통합 (D7-1=A Codex 채택, MCT-171 LAND).

| # | Invariant | 검출 layer | violation 시 action | Prometheus emit |
|---|---|---|---|---|
| 1 | sha256 | byte-level | mismatch_files 박제 + Slack alert | `mctrader_invariant_violation_total{invariant_name=sha256}` |
| 2 | object_count | set-level | NAS+local set diff log + audit | `{invariant_name=object_count}` |
| 3 | row_count | set-level | per-file granularity diff log | `{invariant_name=row_count}` |
| 4 | column_count | schema-level | ADR009_CHANNEL_SCHEMA_MATRIX SSOT 비교 | `{invariant_name=column_count}` |
| 5 | column_order | schema-level | ADR-009 §D2.1 정의 비교 | `{invariant_name=column_order}` |
| 6 | dtype | schema-level | pyarrow type identity 비교 (Decimal precision/scale 포함) | `{invariant_name=dtype}` |
| 7 | schema_version | schema-level | partition prefix vs schema_version=v1 비교 | `{invariant_name=schema_version}` |
| **8** | **ambiguity** | **logical entity-level** | **NAS+local XOR violation log + ingest_blocker trigger consideration** | `{invariant_name=ambiguity}` |

**Enforcement timing** (D7-3=B Codex 채택): 1h periodic sweep — collector hot path 영향 0 (ADR-017 §D5 정합).

**Violation 시 escalate 절차**:
1. mismatch_files audit log 박제 (`docs/audit/MCT-171-invariant-violation-<date>.md`)
2. 8번째 ambiguity violation = 즉시 fail mode (3) Clock drift 진단 (§3.3 절차)
3. 1~7번 violation = D6 verify (bucket versioning) 검증 + version 복원 후보 평가

**1h periodic sweep 실행**:
```bash
# cron-style (별 Story or systemd timer)
docker exec mctrader-data python -m mctrader_data.cli invariant-sweep --interval 1h
```

---

## §5 4 layer capacity step-by-step 본문 (MCT-171 LAND)

`capacity_probe.py` (D7-2=A Codex 채택, `mctrader-data/src/mctrader_data/capacity_probe.py`) — hybrid timing (5min audit + threshold approach continuous, D7-4=C).

### §5.1 WAL local (30 GiB hard limit)

**Probe**: `du -sh /data/wal/` (LVM mount or fallback to host disk)
**Threshold action** (D7-8=C 80%/95% hysteresis):
- 80% (24 GiB): warn + aggressive L1 rotate trigger (`compactor signal`)
- 95% (28.5 GiB): graceful drain + ingest block (in-flight WAL write 완료 후 reject)
- 90% (27 GiB) 회복: ingest unblock 자동 전이 (5% gap hysteresis)

**측정 baseline** (Phase 2 runtime probe 의무):
- 50 sym × 3 channel × 12 seg/h ingest rate × NDJSON byte/record × retention window 역산
- peak market open burst (09:00 KST) 시 fill rate vs L1 promotion rate 측정
- **R-CRITICAL**: 30G 산정 근거 미검증 — 초과 risk 검출 시 D11 hard_limit amendment 발의

### §5.2 L1 local (20 GiB hard limit)

**Probe**: `du -sh /data/l1/`
**Threshold action**:
- 80% (16 GiB): warn + oldest L1 FIFO delete after NAS verify trigger
- 95% (19 GiB): graceful drain + ingest block (WAL 측 동치 처리)
- 90% (18 GiB) 회복: unblock 전이

### §5.3 NAS bucket (target 500 GiB / hard 1 TiB)

**Probe**: `mc du mcnas01/mctrader-market`
**Threshold action**:
- 80% target (400 GiB): warn + L3 cold archive 이전 plan trigger (별 Story)
- 95% target (475 GiB): critical + L3 cold archive 즉시 실행
- 100% hard (1 TiB) 도달: 시스템 stop + 운영자 결재 의무

### §5.4 Host disk (200 GiB hard limit)

**Probe**: `df -h <host_mount>` (LVM volume or fallback to host disk total)
**Threshold action** (D7-9 A+C bridge):
- **장기 (A)**: LVM/Docker volume quota 분리 mount — 별 infra task 의무
- **단기 (C bridge)**: Prometheus `mctrader_capacity_usage_bytes{layer=Host_disk}` alert + 운영자 수동 cleanup

**Host disk 200 GiB 산정 근거** (사용자 환경): Host C: 476G 의 ~42%, mctrader 외 다른 영역과 공유. 별 infra task 측 LVM 분리 의무.

---

## §6 Slack notification template

각 fail mode 별 alert template (mctrader-data 측 emit, Slack webhook 수신):

```text
[<SEVERITY>] MCT-171 DR — Fail Mode (<N>) <name>
- 발생 시각: <UTC ISO>
- detect signal: <metric_name>=<value>
- 영향 범위: <layer / sym / partition>
- runbook: docs/runbooks/nas-bucket-disaster-recovery.md §3.<N>
- escalate: <@oncall | @data-platform | @ALL>
```

SEVERITY enum: `INFO` / `WARN` / `CRITICAL`. Slack channel: `#mctrader-alerts`.

---

## Cross-ref

- `docs/stories/MCT-161.md` §5 AC-4 / §10 FIX Ledger
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` §D MCT-161 amendment + §D5/§D7/§D9 MCT-167 amendment
- `docs/adr/ADR-029-tier-promotion-single-source.md` (D1-D11 박제, MCT-167 publish)
- `docs/adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md` §3 D3 MCT-167 amendment
- `docs/adr/ADR-009-ohlcv-schema.md` §D12.2 MCT-167 amendment (forward-only invariant NAS object SoT 격상)
- `scripts/enable_nas_versioning.py` — 초기 설정 스크립트
- `scripts/verify_nas_versioning.py` — versioning 상태 verify
- `docs/audit/MCT-161-versioning-enable.md` — 초기 enable 실행 결과
- MCT-153 / RETRO-MCT-156 §13.5.2 — 4.2 GiB 손실 원인 박제 (본 runbook 필요성 근거)
- **MCT-171** (DR runbook 본문 + invariant 8종 + 용량 제한 정책 — 본문 author)
- **MCT-174** (NAS bucket replication — cross-NAS target mcnas02, MCT-161 D2=D deferred backlog)
