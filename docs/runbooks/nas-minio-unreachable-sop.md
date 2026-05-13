# NAS MinIO Unreachable — SOP Runbook

> **Version pin**: 본 runbook 은 `NASUnreachableSOPRunner v1` 박제
> (mctrader-data HEAD 65041bd2 기준 — MCT-151 MERGED 시점 + MCT-152 update).
> **state machine 변경 시 본 runbook 우선 amendment 의무 (EC-4 drift 차단).**

| Item | Value |
|---|---|
| Story | MCT-152 (Stage 2 — dual-write window 운영) |
| Issue | mclayer/mctrader-hub#261 |
| Module | `mctrader-data/src/mctrader_data/ops/nas_unreachable_sop.py` |
| ADR | ADR-027 D5 (NAS unreachable failure mode) |
| Related | [nas-minio-deploy.md](./nas-minio-deploy.md) · [nas-minio-secret-rotation.md](./nas-minio-secret-rotation.md) |

---

## Overview

`NASUnreachableSOPRunner` 는 NAS MinIO endpoint unreachable 상태를 감지 + 3단계 state machine
으로 자동 복구 / threshold 알림 / 24h manual gate 를 관리한다.

```
AUTO_RESUME ──(threshold 초과)──► THRESHOLD_BREACHED ──(24h 도달)──► MANUAL_GATE
     ▲                                     │
     └─────────(NAS 복구 시 자동 복귀)──────┘
```

**운영 범위**: dual-write window 기간 (`dual_write_window_runner` cron 실행 중, MCT-152 이후).

---

## 1. AUTO_RESUME state — 정상 거동 + 모니터링

### 1.1 동작 설명

NAS endpoint 가 일시적으로 unreachable 상태일 때 자동 재시도.

- **ping 주기**: 30초 (`ping_interval_seconds=30`)
- **NAS 복구 감지**: HEAD ping 성공 → retry queue drain → `AUTO_RESUME` 복귀
- **hot path 무영향**: WAL + L1 ParquetWriter 는 계속 정상 동작 (ADR-017 정합)

### 1.2 모니터링 절차

**Grafana dashboard**: `mctrader/Cold Writer Health`

확인 항목:
- `nas_uploader_queue_depth` — retry queue backlog segment count (정상: 0~수십)
- `nas_uploader_queue_bytes` — retry queue bytes (정상: < 1GB)
- `nas_uploader_success_count` — NAS PUT 성공 카운터 (incremental)
- `nas_dual_write_window_status_count{status="healthy"}` — daily cron 정상 실행 확인

**threshold 의미** (S10 박제):
- `1000 segments` (~50GB at 50MB/seg) → `THRESHOLD_BREACHED` 진입
- `10 GB` (backlog bytes) → `THRESHOLD_BREACHED` 진입

### 1.3 정상 로그 패턴

```
INFO [sop] NAS reachable — queue_depth=0
INFO [runner] healthy — 7종 invariant ALL PASS
INFO [runner] lock released: /data/dual_write_window.lock
```

---

## 2. THRESHOLD_BREACHED state — operator 행동 매뉴얼

### 2.1 Prometheus alert 발화

| Alert | Rule file |
|---|---|
| `NASUploaderBacklogBytesHigh` | `configs/prometheus/nas_uploader_rules.yml` |

**수신 채널**: Alertmanager → Slack `#mctrader-alerts` / PagerDuty (운영 설정에 따라)

### 2.2 즉시 확인 사항

**Step 1: NAS endpoint 상태 확인**

```bash
# NAS DSM Container Manager 접속
# URL: <NAS_DSM_URL>:5000 (실 URL 은 .env 참조)
# 경로: Container Manager → Container → mctrader-minio → 상태 확인
```

또는:
```bash
# NAS MinIO health check (endpoint URL 은 env에서 조회)
curl -s http://<NAS_ENDPOINT>/minio/health/live
# 응답: 200 OK = 정상, timeout = unreachable
```

**Step 2: retry queue drain status 확인 (Prometheus query)**

```promql
# retry queue depth (pending + quarantined)
nas_uploader_queue_depth

# retry queue bytes
nas_uploader_queue_bytes

# 10GB 초과 여부
nas_uploader_queue_bytes > 10737418240
```

**Step 3: ADR-017 archive failure 7d grace 확인**

NAS unreachable 발생 시 WAL grace 7d 연장 신호가 자동 emit 됨.
→ 7일 이내에 NAS 복구되면 WAL segments 손실 0 보장 (ADR-017 archive failure grace tie-in).

### 2.3 threshold breach 원인 분류

| 증상 | 원인 후보 | 조치 |
|---|---|---|
| NAS Container 응답 없음 | NAS Container 재시작 필요 | §3.1 MANUAL_GATE recovery 진행 |
| NAS Container 정상 / 네트워크 timeout | 방화벽 룰 변경 / IP-allowlist drift | §2.4 방화벽 확인 |
| queue depth 증가 / NAS 복구 중 | 일시적 transient (정상 AUTO_RESUME 대기) | 30분 후 재확인 |

### 2.4 방화벽 룰 확인

```bash
# mctrader-data → NAS MinIO 포트 접근 확인 (9000/9001)
# IP-allowlist: NAS DSM → 제어판 → 방화벽 → mctrader-data 컨테이너 IP 확인
# (90d rotation cadence: nas-minio-secret-rotation.md Step 7 참조)
```

---

## 3. MANUAL_GATE state — 24h 도달 시 manual recovery

### 3.1 진입 조건

NAS endpoint unreachable 상태가 **24시간 이상 지속**.
`dual_write_window_runner` 가 `sop_manual_gate` status emit → daily cron cycle skip.

**확인 로그**:
```
CRITICAL [sop] MANUAL_GATE: NAS unreachable > 24h — user intervention required.
WARNING  [runner] SOPRunner MANUAL_GATE — cycle skip (EC-5, sop_manual_gate)
```

**Prometheus metric**:
```promql
nas_dual_write_window_status_count{status="sop_manual_gate"}  # > 0 이면 MANUAL_GATE 진입
nas_dual_write_window_sop_trigger_count{sop_state="manual_gate"}
```

### 3.2 NAS Container Manager UI 경유 복구 절차

**Step 1: NAS DSM Container Manager 접속**
```
URL: <NAS_DSM_URL>:5000
→ Container Manager → 컨테이너 탭
→ mctrader-minio 컨테이너 선택
```

**Step 2: Container STOP → START**
```
1. 컨테이너 선택 → "중지" 클릭 (STOP)
2. 약 30초 대기
3. 컨테이너 선택 → "시작" 클릭 (START)
4. 컨테이너 상태 "실행 중" 확인
```

**Step 3: MinIO endpoint health 확인**
```bash
# 약 10초 후 health check
curl -s http://<NAS_ENDPOINT>/minio/health/live
# 기대: 200 OK
```

**Step 4: NASUnreachableSOPRunner 자동 복구 대기**
- ping 주기 = 30초 → 1분 이내 AUTO_RESUME 복귀 예상
- 로그 확인: `[sop] NAS reachable — queue_depth=N`

**Step 5: retry queue drain 확인**
```bash
# Grafana → nas_uploader_queue_depth 추이 확인 (감소 추세)
# NAS 복구 후 retry queue 자동 drain (SOPRunner.run_once() 내 drain 로직)
```

### 3.3 방화벽 룰 재확인

MANUAL_GATE 진입 원인이 방화벽 룰 변경인 경우:

```bash
# NAS DSM → 제어판 → 방화벽
# mctrader-data 컨테이너의 IP/대역대가 NAS 포트 9000/9001 에 접근 허용 확인
# IP-allowlist drift 발생 시 재추가 (MCT-147 R10 mitigation 정합)
# 참조: nas-minio-secret-rotation.md Step 7 (90d rotation + IP-allowlist 재확인)
```

### 3.4 endpoint failover 옵션 (Stage 2 scope 외 — 참고용)

NAS 장애가 장기화될 경우 향후 endpoint 다중화 시 참조:
- MinIO endpoint 다중화 (multi-site replication) = Stage 2 scope 외
- 현재는 단일 NAS endpoint — failover 구현 후 본 runbook amendment 의무

### 3.5 dual_write_window_runner cron 재개 확인

MANUAL_GATE 해제 (NAS 복구 + SOPRunner AUTO_RESUME 복귀) 후:
1. 다음 daily cron trigger 시 `dual_write_window_runner.run()` 자동 재진입
2. `sop_runner.is_manual_gate()` → False 확인 (MANUAL_GATE 해제)
3. 정상 cycle: `DualWriteWindowResult.status="healthy"` 확인

```promql
# MANUAL_GATE 해제 후 정상 cycle 확인
nas_dual_write_window_status_count{status="healthy"}  # 증가 추세
nas_dual_write_window_status_count{status="sop_manual_gate"}  # 증가 멈춤
```

---

## 4. Evidence pack 포인터

SOP 실전 가동 per-trigger evidence 는 아래 위치에 박제:

- **운영 evidence pack**: `mctrader-data/.tmp/evidence-pack-MCT-152.md` (gitignored)
  - §4 SOP Trigger Log: timestamp + threshold breached + recovery time + MANUAL_GATE 발동 여부
- **Story §10 summary**: `docs/stories/MCT-152.md §10`
  - SOP trigger count (false positive rate / MANUAL_GATE 발동 빈도 + recovery time)

본 evidence pack 은 MCT-155 retro 시점 ADR-027 D5 amendment evidence-rich source.

---

## 5. Cross-references

| 참조 | 위치 |
|---|---|
| NAS MinIO deploy runbook | `docs/runbooks/nas-minio-deploy.md` |
| NAS MinIO secret rotation (90d cadence) | `docs/runbooks/nas-minio-secret-rotation.md` |
| MCT-152 Story (DualWriteWindowResult enum) | `docs/stories/MCT-152.md §6.2.1` |
| ADR-027 D5 (NAS unreachable failure mode) | `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` |
| ADR-017 (archive failure 7d grace) | `docs/adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md` |
| NASUnreachableSOPRunner source | `mctrader-data/src/mctrader_data/ops/nas_unreachable_sop.py` |
| DualWriteWindowRunner source | `mctrader-data/src/mctrader_data/ops/dual_write_window_runner.py` |
