---
title: Stage 3 wiring deploy runbook (MCT-156)
epic: EPIC-cold-tier-stage-3-wiring
adr: ADR-027 (D4/D5/D9 amendment)
date: 2026-05-13
status: Active
---

# Stage 3 — Compactor NAS Wiring Deploy Runbook

본 runbook 은 MCT-156 (compactor L2/L3 → NAS MinIO DualWriter injection) 의 production deploy 절차 + verify checklist + rollback 박제.

## Phase 0. Prerequisites

- Phase 1 PR (`mctrader-hub#279`) MERGED — ADR-027 D4/D5/D9 amendment land
- Phase 2 PR (`mctrader-data#47` + `mctrader-hub#280`) MERGED — code + Story §11 + RETRO
- NAS host (mcnas01.internal.mclayer.it) 가용 + DNS 정상 해석
- MinIO root credential 박제 위치 확인 (`mctrader-hub/docker/minio/.env`)

## Phase 1. NAS endpoint 정합 검증

```powershell
# DNS 해석
Resolve-DnsName mcnas01.internal.mclayer.it -Type A

# HTTP health
curl -s -o /dev/null -w "%{http_code} %{time_total}s`n" http://mcnas01.internal.mclayer.it:9000/minio/health/live --max-time 5
```

기대 출력: `200 0.0xxs` (LAN 내부망, <100ms).

**중요**: `.env` 의 `NAS_MINIO_ENDPOINT` 는 **DNS 사용 의무** (IP 직접 박제 비권고 — DR / NAS hardware 교체 시 endpoint 갱신 cost).

## Phase 2. `mctrader-data/.env` 갱신

```bash
# 기존 (ingester service legacy MinIO env 유지):
MINIO_ACCESS_KEY=mctrader
MINIO_SECRET_KEY=changeme_minio

# MCT-156 신규 추가 (compactor service):
NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
NAS_MINIO_ACCESS_KEY=mctrader-admin
NAS_MINIO_SECRET_KEY=<NAS MinIO root password — mctrader-hub/docker/minio/.env 참조>
NAS_MINIO_BUCKET=mctrader-market
```

**보안 의무**:
- `.env` permission = `0600` (ADR-027 D2 4중 mitigation #1)
- `.gitignore` 박제 확인 (commit 차단, ADR-027 D2 4중 mitigation #1)
- 90일 credential rotation (ADR-027 D2 4중 mitigation #2)
- NAS 측 방화벽 port 9000 = mctrader host IP only (ADR-027 D2 4중 mitigation #3)
- IAM user 분리 의무 (ADR-027 D2 4중 mitigation #4 — Stage 2 scope 박제, 실 분리는 별 Story 권고)

## Phase 3. Compactor image rebuild + restart

```bash
cd c:/workspace/mclayer/mctrader-data
docker compose build compactor
docker compose up -d compactor
```

기대 출력:
- `Container mctrader-compactor Recreated`
- `Container mctrader-compactor Started`

## Phase 4. Env inject verify

```bash
docker exec mctrader-compactor env | grep NAS_MINIO
```

기대 출력 (4종):
```
NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
NAS_MINIO_ACCESS_KEY=mctrader-admin
NAS_MINIO_SECRET_KEY=<masked>
NAS_MINIO_BUCKET=mctrader-market
```

## Phase 5. Compactor startup logs verify

```bash
docker logs mctrader-compactor 2>&1 | head -5
```

기대 출력 (필수 메시지):
```
[INFO] mctrader_data.compactor.metrics_server: [metrics_server] started port=8080
[INFO] mctrader-data.compact: [compactor] NAS dual-write enabled: endpoint=http://mcnas01.internal.mclayer.it:9000 bucket=mctrader-market
[INFO] mctrader_data.compactor.runner: [compactor] runner started root=/var/lib/mctrader/data
```

**FAIL 시**: `[compactor] NAS_MINIO_ENDPOINT not set — L2/L3 NAS upload disabled (degraded mode)` 메시지 = .env inject 실패 → Phase 2 재시도.

## Phase 6. NAS bucket write 정합 verify (force PUT)

자연 cadence (L1 backlog 처리 후 5min L2 trigger) 가 ETA 길 경우 (~9시간), force PUT 으로 wiring 즉시 검증 가능:

```python
# docker exec mctrader-compactor python -c "..."
import os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from mctrader_data.compactor.l2 import L2Compactor
from mctrader_data.nas_storage.dual_writer import DualWriter
from mctrader_data.nas_storage.nas_uploader import NASUploader
from mctrader_data.nas_storage.retry_queue import RetryQueue

root = Path('/var/lib/mctrader/data')
retry_queue = RetryQueue(path=root / 'nas_retry_queue.sqlite')
nas = NASUploader(
    endpoint=os.environ['NAS_MINIO_ENDPOINT'],
    access_key=os.environ['NAS_MINIO_ACCESS_KEY'],
    secret_key=os.environ['NAS_MINIO_SECRET_KEY'],
    bucket=os.environ['NAS_MINIO_BUCKET'],
    retry_queue=retry_queue,
)
dw = DualWriter(nas_uploader=nas, local_root=root)

l2 = L2Compactor(root)
now = datetime.now(timezone.utc)

# transaction channel 권고 (orderbooksnapshot 은 pyarrow offset overflow pre-existing bug)
out = l2.compact_hour(exchange='upbit', symbol='KRW-BTC', channel='transaction', hour_utc=now)
if out:
    payload = out.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    nas_key = str(out.relative_to(root)).replace('\\', '/')
    result = dw.write(local_path=out, nas_key=nas_key, data=payload, sha256=sha)
    print(f'status={result.status}, key={nas_key}')
```

기대 출력: `status=committed, key=market/transaction/schema_version=tick.v1/tier=L2/.../hour=HH/node=MERGED/part-*.parquet`

## Phase 7. NAS bucket listing verify

```python
import boto3, os
s3 = boto3.client('s3',
    endpoint_url=os.environ['NAS_MINIO_ENDPOINT'],
    aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'],
    aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'])
resp = s3.list_objects_v2(Bucket='mctrader-market', Prefix='market/transaction/schema_version=tick.v1/tier=L2/', MaxKeys=5)
for o in resp.get('Contents', []):
    print(f"{o['Key']} size={o['Size']} mtime={o['LastModified']}")
```

기대 출력 (최소 1건):
- prefix root `market/` 출현 (hot pipeline 산출물)
- prefix `tier=L2/.../hour=HH/node=MERGED/` 출현 (신규 schema)
- 별도 prefix `smoke/` = MCT-148 PoC 잔여 (무시 가능)

## Phase 8. Rollback

문제 발생 시 (NAS unreachable / credential 오류 / disk full 등):

```bash
# .env 의 NAS_MINIO_ENDPOINT 주석 처리 (degraded mode 진입)
# NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000

cd c:/workspace/mclayer/mctrader-data
docker compose up -d compactor
docker logs mctrader-compactor | head -5
```

기대 출력 (degraded mode):
```
[compactor] NAS_MINIO_ENDPOINT not set — L2/L3 NAS upload disabled (degraded mode)
```

이 상태에서 hot pipeline (L1/L2/L3 compaction) 은 local volume 정상 동작 — ADR-027 §D5 hot path 무영향 invariant 정합. local SoT 보존.

## Pre-existing 운영 issue (별 Story #MCT-159 발의)

본 deploy 시점 surface 된 pre-existing issue 3건 (MCT-156 scope 외):

1. **L1Compactor `orderbookdepth` channel 미지원** — 48,629 sealed segments fail 누적 (NotImplementedError: `_schema_version: channel 'orderbookdepth' not supported. Supported: 'transaction', 'orderbooksnapshot'`)
2. **L2Compactor `orderbooksnapshot` pyarrow offset overflow** — large string column 4GB+ 한계 (`ArrowInvalid: offset overflow while concatenating arrays`)
3. **MCT-153 backfill 산출물 4.2GiB / 1370 obj 손실** — bucket versioning 미활성 = 복구 불가 (hard delete 또는 처음부터 본 NAS 진입 안 함, S1/S6/S7 결정 전제 깨짐)

MCT-159 발의 시 별 brainstorm + spec/plan 진행.

## References

- ADR-027 (`docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`) — D4/D5/D9 amendment
- Story (`docs/stories/MCT-156.md`) — §1~§12 박제
- RETRO (`docs/retros/RETRO-MCT-156.md`) — §13 deploy verification cycle
- PR: mctrader-hub#279 (Phase 1), mctrader-data#47 (Phase 2 code), mctrader-hub#280 (Phase 2 governance)
