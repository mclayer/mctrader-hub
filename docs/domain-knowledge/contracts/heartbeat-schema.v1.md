# Heartbeat Schema v1 — Collector HA Active-Active

## Purpose

Active-active multi-node collector 에서 각 node 의 liveness / lag / dedup 상태를 cross-host visible 하게 노출하는 storage-side artifact. Streamlit `00_status` page + CLI `mctrader-data status` + Ansible rolling deploy health gate 의 single source of truth.

## Path

```
<MCTRADER_DATA_ROOT>/market/manifest/heartbeat-{node_id}.json
```

- `node_id` = 호스트 식별자 (e.g., `NODE_A`, `NODE_B`). low cardinality (호스트 수 만큼).
- 각 node 가 **자기 file 만** write. cross-host write contention 0.

## Write 규약 (atomic)

1. write to temp file: `heartbeat-{node_id}.json.tmp`
2. `fsync` temp file
3. `rename` temp → `heartbeat-{node_id}.json` (POSIX atomic rename, NFS atomic rename within same directory)
4. write interval = 5 seconds (default, configurable via `--heartbeat-interval` CLI flag)

## JSON Schema (v1)

```json
{
  "schema_version": "heartbeat.v1",
  "node_id": "NODE_A",
  "collector_run_id": "A-2026-05-05T12:34:56Z",
  "version": "git-sha-abc1234",
  "started_at": "2026-05-05T00:00:00Z",
  "now": "2026-05-05T12:34:56Z",
  "uptime_seconds": 45296,
  "ws_state": "connected",
  "last_event_ts_per_tier": {
    "candle": "2026-05-05T12:34:55Z",
    "tick": "2026-05-05T12:34:56.123Z",
    "orderbook": "2026-05-05T12:34:56.045Z"
  },
  "queue_depth": 0,
  "metrics": {
    "events_per_sec": 42.3,
    "dup_skip_count": 0,
    "quarantine_count": 0,
    "ws_reconnect_count": 0,
    "backfill_pending_seconds": 0
  }
}
```

### Field 정의

| Field | Type | 설명 |
|---|---|---|
| `schema_version` | str literal | `"heartbeat.v1"` 고정 |
| `node_id` | str | 호스트 식별자 |
| `collector_run_id` | str | 현재 collector run 의 unique id (MCT-65 manifest 와 1:1 align) |
| `version` | str | git commit sha (deploy 추적) |
| `started_at` | ISO8601 UTC | collector process 기동 시각 |
| `now` | ISO8601 UTC | heartbeat write 시각 (freshness 판정 기준) |
| `uptime_seconds` | int | `now - started_at` (편의 derived field) |
| `ws_state` | enum | `"connected"` / `"reconnecting"` / `"disconnected"` |
| `last_event_ts_per_tier` | dict[str, ISO8601 UTC] | 각 tier (candle/tick/orderbook) 의 마지막 event 수신 시각 |
| `queue_depth` | int | 내부 buffer 의 미처리 event 수 |
| `metrics.events_per_sec` | float | 최근 5s window 평균 |
| `metrics.dup_skip_count` | int (cumulative) | 본 run 시작 이래 dup-hash skip 누적 |
| `metrics.quarantine_count` | int (cumulative) | 본 run 시작 이래 quarantine 누적 (active-active mismatch 포함) |
| `metrics.ws_reconnect_count` | int (cumulative) | 본 run 시작 이래 WS reconnect 횟수 |
| `metrics.backfill_pending_seconds` | int | 현재 backfill queue 의 가장 오래된 gap 길이 |

## Freshness 판정 (consumer 측)

`now - mtime(heartbeat-{node_id}.json) > 30s` → node liveness 위반. 다음 alert level:

- `< 10s`: green
- `10s ≤ Δ < 30s`: yellow (clock drift 가능)
- `≥ 30s`: red (node down 또는 restart 중)

## Lag 판정 (consumer 측)

`now - last_event_ts_per_tier[candle] > 2 * timeframe_seconds` → candle lag (T1 closed bar 기준 2-bar 이상 빠짐).

`now - last_event_ts_per_tier[tick] > 60s` → tick lag (default).

`now - last_event_ts_per_tier[orderbook] > 60s` → orderbook lag (default).

threshold 는 `mctrader-data` 의 status CLI 가 default 적용, 사용자 override 가능.

## Related Manifest Artifacts (MCT-93 X4 amendment)

Active-active mismatch quarantine artifacts:

```
<MCTRADER_DATA_ROOT>/market/manifest/quarantine/{tier}-{detected_at_iso}-{batch_seq}.json
```

- `tier`: `"tick"` / `"orderbook"` (T1 candle 은 §D5 late correction policy 로 quarantine emit 안 함)
- `detected_at_iso`: ISO8601 UTC compact (e.g. `20260506T123456Z`), `_BackpressureLimiter` flush 시각
- `batch_seq`: 6-digit zero-padded per-second batch index (per-second 100 mismatch cap 의 backpressure batching 결과, 동일 second 내 multiple flush 시 단조 증가)
- payload schema:
  ```json
  {
    "tier": "tick",
    "count": 1,
    "records": [
      {
        "reason": "ACTIVE_ACTIVE_MISMATCH",
        "logical_key": ["bithumb", "KRW-BTC", "2026-05-06T12:34:56+00:00", "100", "0.01", "buy"],
        "rows": ["..."],
        "detected_at": "2026-05-06T12:34:56+00:00"
      }
    ]
  }
  ```
- atomic write (temp → fsync → os.replace), append-only (existing file 덮어쓰지 않음)

**중요**: `metrics.quarantine_count` 는 cumulative mismatch *count* (artifact file 개수와 다름 — backpressure batching 으로 multiple records 가 single artifact file 에 합쳐짐).

## 호환성

- **v1 → v2 (후속)**: 새 field 추가는 backward compatible (consumer 가 unknown field ignore). field 제거 / type 변경은 schema_version bump 의무.
- consumer 는 `schema_version` mismatch 시 warning + best-effort parse.
- §Related Manifest Artifacts 의 quarantine artifact path/format 도 schema_version 과 별개 contract — file format 변경 시 별도 versioning (`quarantine.v2/...`).

## 참조

- Spec: [collector-ha-active-active-design.md](../../superpowers/specs/2026-05-05-collector-ha-active-active-design.md) §4.2 / §5.1
- ADR-009 §D2.1 / §D10.1 / §D11.1 amendment (active-active dedup contract)
