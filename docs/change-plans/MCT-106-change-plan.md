# Change Plan — MCT-106 Zero-loss ingestion (WAL + tiered compaction + multi-exchange)

- **Story**: MCT-106
- **Status**: design-review-ready (Iteration 2 — ArchitectPLAgent FIX 회귀 완료 2026-05-09, F1 P0 + F2-F12 P1/P2 모두 fix)
- **Story file**: [`docs/stories/MCT-106.md`](../stories/MCT-106.md)
- **ADR**: [ADR-017](../adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md) · amends [ADR-009](../adr/ADR-009-ohlcv-schema.md) · respects [ADR-033](../adr/ADR-033-docker-first-named-volume.md)
- **Target repo**: `mctrader-data`

## 1. 입력 요약 (Story §1 verbatim, immutable)

> "컨테이너 재시작 시에도 데이터가 소실되지 않는가?"
> "재시작 시에도 손실이 발생하지 않는 방법을 설계해봐"
> "만약에 그정도로 부담이 크다면 나눠라 container를 추후에 다른 마켓도 들어올 수 있으니 이것도 고려해라"
> "이중으로 할 수 있지 않을까? 5분마다 한번 compaction 하고 또 그걸 1시간 compaction하고 그걸 하루치 compaction 하는거다."
> "신규 MCT로 진행하자."

## 2. 현재 구조 (CodebaseMapperAgent 산출)

### 2.1 핵심 자산 인벤토리

| 자산 | 경로 | 본 Story 와 관계 |
|------|------|-------------------|
| `TickWriter` | `src/mctrader_data/tick_storage.py` | **변경 대상** — 인메모리 buffer(500) → ParquetWriter 직접 결합. Compactor 재사용 후보 (per-batch write_table 로직) |
| `OrderbookWriter` | `src/mctrader_data/orderbook_storage.py` | **변경 대상** — TickWriter와 동형 구조 (batch_size=1000) |
| `OrderbookSnapshotWriter` | `src/mctrader_data/orderbook_snapshot_storage.py` | **변경 대상** — §D14 throttle 포함, payload_hash dedup 보존 필요 |
| `CollectorDaemon` | `src/mctrader_data/collector.py:48-202` | **분할 대상** — `_handle_event` 가 직접 `*Writer.append()` 호출 → WAL append로 교체 |
| `MultiSymbolCollector` | `collector.py:205-285` | **유지 (Ingester 컨테이너로 재배치)** — heartbeat/health 통합 책임 |
| `MetadataRefreshScheduler` | `collector.py:328-411` | **유지** — Ingester 컨테이너 잔류 (HTTP REST는 WS와 무관) |
| `dedup.py` | `src/mctrader_data/dedup.py` | **유지 (Compactor로 이동)** — read-side dedup logic은 compaction 단계로 적합 |
| `manifest.py` / `lineage.py` | 同 디렉토리 | **유지** — Compactor가 lineage 기록 (compacted_from 추가) |
| `heartbeat.py` | `src/mctrader_data/heartbeat.py` | **확장** — `role` 필드 추가 (`ingester` vs `compactor`) |
| `compose.yml` | `mctrader-data/compose.yml` | **재구성** — `bithumb-ingester` + `compactor` 2 service |

### 2.2 결합도 분석

- WS 수신 ↔ Parquet 쓰기 결합도: **상**
  `_handle_event` → `tick_writer.append()` → `_flush_locked()` → `pq.ParquetWriter.write_table()` 모두 동기 동일 thread
- TickWriter는 `(symbol, date)` 단위 singleton — 50 symbol × 3 channel = 150 writer 인스턴스 동시 보유
- ParquetWriter는 footer까지 buffered → close 전 종료 시 손상 → **현재 손상 299/807 직접 원인**

### 2.3 변경 영향 지도

| 영향 자산 | 영향 종류 | 보존/대체 |
|----------|----------|----------|
| `tick_storage._records_to_arrow` | **재사용** | Compactor가 그대로 호출 |
| `_TICK_SCHEMA` / `_OB_SCHEMA` / `_OB_SNAPSHOT_SCHEMA` | **재사용 (SSOT)** | NDJSON deserializer가 동일 schema로 변환 |
| `transaction_event_to_record` / `delta_event_to_records` / `snapshot_event_to_snapshot_records` | **재사용** | Ingester가 호출 후 `record_to_ndjson_line()` 으로 직렬화 |
| `tests/test_tick_storage.py` 등 6개 storage 테스트 | **유지 + 신규** | Parquet writer 단위테스트 유지, Ingester/Compactor 신규 |
| 50sym 3ch production WS 수신 (compose.yml) | **runtime 영향** | rolling cutover (§11.3) |

## 3. 도입할 설계 (RefactorAgent 산출 + ArchitectAgent 통합)

### 3.1 high-level architecture

```
+-------------------+    +-------------------+    +-------------------+
| bithumb-ingester  |    | upbit-ingester    |    | binance-ingester  |
| (per exchange)    |    | (future)          |    | (future)          |
| WS -> NDJSON WAL  |    | WS -> NDJSON WAL  |    | WS -> NDJSON WAL  |
+----+--------------+    +----+--------------+    +----+--------------+
     |                        |                        |
     v                        v                        v
   +---------------------------------------------------------+
   |  named volume mctrader_data:/var/lib/mctrader/data       |
   |    wal/<exchange>/<channel>/<symbol>/<date>/             |
   |      segment-{startUtc}-{node}.ndjson(.sealed|.compacted)|
   |    market/.../tier=L{1,2,3}/.../part-*.parquet           |
   +-----------+---------------------------------------------+
               |
               v
   +---------------------+
   | compactor           |
   |  - WAL scan         |
   |  - L1 (5min) build  |
   |  - L2 (1h) build    |
   |  - L3 (1day) build  |
   |  - lineage emit     |
   |  - dedup+quarantine |
   +---------------------+
```

### 3.2 Ingester 책임 (RefactorAgent 채택)

```python
# src/mctrader_data/wal/ingester.py (신규)
class WalIngester:
    def __init__(self, root: Path, exchange: str, symbol: str, channel: str,
                 node_id: str,                       # MCTRADER_NODE_ID env (mandatory, ADR-009 §D2.1)
                 fsync_batch: int = 1,
                 segment_seconds: int = 300, ...): ...
    def append(self, record: dict) -> None:
        """Append-line + (optional) fsync. NEVER raises on partial write."""
    def maybe_seal(self) -> Path | None:
        """If wall-clock crossed segment boundary, atomic rename .ndjson -> .ndjson.sealed."""
    def close(self) -> None:
        """Final fsync + seal current segment."""
```

`CollectorDaemon._handle_event`는 `*Writer.append()` 대신 `record_to_dict()` → `WalIngester.append()` 로 교체. ParquetWriter는 Ingester에서 완전히 사라진다.

**F4 — 코드 시그니처 강화 (구현 모호성 차단, 4 항목 박제)**:

(a) **fd open 정책**: `WalIngester.__init__` 안에서
```python
import os
self._fd = os.open(
    self._segment_path,
    flags=os.O_WRONLY | os.O_APPEND | os.O_CREAT,
    mode=0o640,
)
# 단일 fd, single-writer (per-symbol-channel) — POSIX O_APPEND atomic
```
`open(..., 'a')` 대신 `os.open(..., O_APPEND|O_CREAT)` — Python file object 의 buffer 회피 + write barrier 제어 명시. mode `0o640` (§7.3 권한).

(b) **Segment boundary 알고리즘**: epoch 기반 정수 division — wall-clock 표기 회피 (DST / leap second 안전):
```python
def _segment_index(self, ts: float) -> int:
    return int(ts // self._segment_seconds)

def maybe_seal(self) -> Path | None:
    now_idx = self._segment_index(time.time())
    if now_idx > self._segment_start_idx:
        sealed = self._seal_current()
        self._open_new_segment(start_idx=now_idx)
        return sealed
    return None
```
`now - segment_start >= 300` 형식 거부 (drift 누적 위험). `(now // 300) > (segment_start // 300)` 채택 — 5분 epoch boundary 정확.

(c) **Orphan ingester forced-seal 록**: file lock based — `wal/<exchange>/<channel>/<symbol>/_lock/<node_id>.pid`
- WalIngester startup 시 PID file write + `fcntl.flock(..., LOCK_EX | LOCK_NB)` 시도 (POSIX) — 실패 = 다른 ingester active = exit
- Compactor orphan force-seal:
  1. active `.ndjson` 의 last-modified > 30min detected
  2. PID file 의 lock try-acquire (`LOCK_EX | LOCK_NB`) — 성공 = orphan (이전 ingester 사망 + lock release 됨), 실패 = 활성 ingester 가 단지 idle 한 상태 → seal 거부 + alert
  3. orphan 확인 후 forced atomic rename `.ndjson` → `.ndjson.sealed` + quarantine 표시
- Windows host (dev only) 는 `msvcrt.locking()` 사용 — production Linux 만 final correctness 보장 (ADR-033 Linux production 정합)

(d) **NDJSON Decimal serialization**: SSOT 박제 — `str(Decimal)` Python 직렬화 사용 (scientific notation 발생 안 함을 unit test 로 검증)
```python
# src/mctrader_data/wal/ndjson_codec.py
import json
from decimal import Decimal

def encode_record(record: dict) -> str:
    return json.dumps(record, default=_default, ensure_ascii=False, separators=(',', ':')) + '\n'

def _default(obj):
    if isinstance(obj, Decimal):
        # str(Decimal('123.456')) == '123.456' — Python promise: no scientific notation for normal Decimal
        # Edge case: Decimal('1E+10') → '1E+10' (scientific). Compactor 측에서 _records_to_arrow() 가 Decimal()
        # 으로 다시 parse 가능 — round-trip safe. test_decimal_roundtrip_no_precision_loss (INV-5) 검증.
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()  # ISO 8601 with offset
    raise TypeError(...)

def decode_line(line: str) -> dict:
    return json.loads(line, parse_float=Decimal)  # Decimal preservation on read
```
`to_eng_string()` 거부 사유: scientific notation 더 자주 발생 (e.g., 1E+10) → Arrow Table cast 시 추가 변환 필요. JSON number 직접 거부 사유: `decimal128(38,18)` 정밀 손실 (float64 cast 거침).

### 3.3 Compactor 책임 (RefactorAgent 채택)

```python
# src/mctrader_data/compactor/runner.py (신규)
class CompactorRunner:
    async def run(self) -> None:
        """Scan WAL volume, drive L1/L2/L3 schedulers."""

class L1Compactor:
    def compact_segment(self, sealed_path: Path) -> Path:
        """sealed NDJSON -> tier=L1 Parquet (atomic write-then-rename).

        Pipeline (channel-aware):
          1. read sealed NDJSON line-by-line (utf-8, '\n' terminator)
          2. each line → record dict via ndjson_codec.decode_line()
          3. **channel == 'orderbook_snapshot' only**: ADR-009 §D14.10 1-sec
             subsample throttle 적용 (per-symbol last-write-wins window).
             tick / orderbook delta 는 throttle 안 함 (모든 record append).
          4. **payload_hash dedup** (orderbook_snapshot 만, ADR-009 §D14.6):
             동일 (symbol, baseline_seq, side, level) 의 다른 payload_hash
             detected → fail-closed halt + quarantine emit (upstream incident).
             동일 payload_hash 중복 → idempotent skip (per-row).
          5. 정렬 + Arrow Table 변환 (`_records_to_arrow()` 재사용)
          6. tier=L1 / node=<source_node_id> Parquet write-then-rename
          7. lineage manifest emit (compacted_from + sha256 + node_id)
        """
class L2Compactor:
    def compact_hour(self, exchange: str, symbol: str, channel: str, hour_utc: datetime) -> Path: ...
class L3Compactor:
    def compact_day(self, exchange: str, symbol: str, channel: str, date_utc: date) -> Path: ...
```

NDJSON → Arrow Table 변환은 기존 `_records_to_arrow()` 재사용 — **schema SSOT 보존**.

**Throttle/dedup 책임 위치 박제 (F2)**: Ingester 는 raw NDJSON append only — throttle / payload_hash dedup 모두 미적용 (zero-loss 우선). 적용 시점 = L1Compactor.compact_segment 안 (sealed NDJSON → Arrow Table 변환 전 단계). 기존 `OrderbookSnapshotWriter._write_if_eligible()` (ADR-009 §D14.10) 의 sliding-window throttle 로직은 본 PR 에서 Compactor 의 `_throttle_subsample()` helper 로 이전 + unit test 보존.

**`compaction_run_id` determinism 박제 (F10, §11.6 SSOT)**: L1/L2/L3 Compactor 의 `compaction_run_id = sha256(sealed_segment_relative_path).hexdigest()[:16]` (timestamp portion 제거). 동일 sealed segment 재처리 시 동일 run_id → 동일 partition 안 single file 보장. 자세한 invariant + collision 처리는 §11.6 Idempotency 절 참조.

### 3.4 패키지 트리

```
src/mctrader_data/
├── wal/
│   ├── __init__.py
│   ├── ingester.py        # WalIngester (per-symbol-channel writer)
│   ├── segment.py         # Segment naming, seal, scan
│   └── ndjson_codec.py    # record <-> ndjson line encoder/decoder
├── compactor/
│   ├── __init__.py
│   ├── runner.py          # CompactorRunner (asyncio orchestrator)
│   ├── l1.py              # L1Compactor (5min)
│   ├── l2.py              # L2Compactor (1h)
│   ├── l3.py              # L3Compactor (1day)
│   └── gc.py              # 24h grace, .compacted segment GC
├── tick_storage.py        # _records_to_arrow / schema 유지 (writer 클래스 deprecated)
├── orderbook_storage.py   # 同上
├── orderbook_snapshot_storage.py  # 同上 (§D14 throttle은 Compactor로 이동)
└── collector.py           # CollectorDaemon: TickWriter -> WalIngester 호출로 교체
```

## 4. 외부 인터페이스

### 4.1 CLI

- 신규: `mctrader-data compact --root <path>` — Compactor 단일 실행 (Docker entrypoint)
- 기존: `mctrader-data collect ...` — Ingester 모드 (의미 변경 — Parquet 직접 쓰기 제거)
- 신규 옵션: `--wal-fsync-batch=N` (default 1 = per-message fsync), `--segment-seconds=300`

**F7 — `collect` CLI 부작용 변경 (Phase C cutover 시점) 영향 분석**:

기존 `mctrader-data collect` 호출자가 가정하던 부작용:
- (구) collect 호출 직후 Parquet 파일이 즉시 `market/<channel>/...` 경로에 생성됨 → caller 가 즉시 read 가능 (synchronous Parquet emit).
- (신) collect 호출 후 WAL NDJSON 만 즉시 생성. Parquet 는 Compactor 가 5분 sealed segment seal cycle + L1 build 처리 후 emit (async, **최대 5분 지연**).

호출자 영향 + 마이그레이션 path:

| 호출자 | 기존 가정 | Phase C 후 영향 | 마이그레이션 |
|--------|----------|----------------|-------------|
| `mctrader-engine docker integration` (backtest dataset prep) | collect 종료 직후 Parquet read | 5분 wait 또는 수동 `compact --once` 호출 의무 | engine compose 의 collect-and-prepare 스크립트 갱신: collect → `sleep 300 && compact --once --max-age 300` 또는 `wait-for-parquet --since <ts>` helper 사용 |
| `mctrader-data` 내부 WFO 스크립트 (`scripts/run_wfo.sh`) | collect 직후 backtest run | Compactor process 가 동일 compose 안 이미 running → 자연 처리 (5분 후 Parquet 생성) | 없음 (compose 가 이미 ingester+compactor 동시 운영) |
| `tests/integration/test_*.py` (Parquet read 가정) | mock collect → 즉시 Parquet read | mock 수정 의무 — WalIngester+L1Compactor.compact_segment 동기 호출 fixture | `tests/conftest.py` 에 `compact_now()` fixture 추가 — WAL → L1 즉시 동기 변환 |
| 운영 쉘 스크립트 (`mctrader-data/ops/*.sh`) | 없음 (현재 1개도 read-after-collect 의존 없음 — codebase grep 검증) | 없음 | N/A |

**옵션 호환성**: `--exchange / --symbols / --include` 등 기존 옵션 모두 유지 (interface 변경 0). 부작용 변경 (synchronous → async Parquet emit) 만 발생.

**Phase D 의무**: legacy TickWriter / OrderbookWriter 클래스의 deprecation warning 외에 README + CHANGELOG 에 "Phase C cutover 시 `collect` CLI 부작용 변경 — Parquet 즉시 read 가정 깨짐, 호출자 마이그레이션 의무" 명시. 본 항목 누락 시 외부 호출자 (engine / WFO) silent regression 위험.

### 4.2 Volume / 파일 layout

- WAL: `<root>/wal/<exchange>/<channel>/<symbol>/<date>/segment-{YYYYMMDDHHMMSS}-{node}.ndjson{,.sealed,.compacted}`
- Parquet: `<root>/market/<channel>/schema_version=...v1/tier=L{1,2,3}/exchange=.../symbol=.../date=.../node=<id>/part-{run}.parquet`
  - `node=<id>` **mandatory** (ADR-009 §D2.1 contract — 모든 tier `ohlcv.v1`/`tick.v1`/`orderbook.v1` partition leaf 직전에 `node=` level enforced)
  - `<id>` 값 = source ingester 의 `MCTRADER_NODE_ID` env (compose service 별 unique). Compactor 는 sealed segment 의 source ingester `node_id` 를 emit Parquet partition 에 보존 (multi-node SPOF 단계와 무관 — single-node 운영도 `node=DEFAULT` 또는 hostname 으로 partition 강제)
  - **Legacy `node=` 부재 파일 (기존 healthy 508개) 처리**: ADR-009 §D2.1 "Mixed legacy partition layout 영구 지원" 정책 준수 — read API (`scan_ticks` / `scan_orderbook_events` / `scan_orderbook_snapshots`) 가 `node=` 부재 row 를 `node=DEFAULT` 로 취급하여 mixed scan 영구 지원 (별도 migration Epic 의 scope, 본 Story 범위 외)
- Lineage: `<root>/market/.../<partition>/lineage-{run_id}.json` — 신규 필드 `compacted_from: [{wal_path, sha256, segment_start, segment_end}]` + `node_id` (source ingester 식별)

### 4.3 Compose

```yaml
services:
  bithumb-ingester:
    image: mctrader-data:pilot
    command: ["collect", "--exchange", "bithumb", "--symbols", "...", "--include", "transactions,orderbook,orderbook_snapshot"]
    volumes: [mctrader_data:/var/lib/mctrader/data]
    healthcheck: ...  # /health on 8080
    restart: unless-stopped
  compactor:
    image: mctrader-data:pilot
    command: ["compact", "--root", "/var/lib/mctrader/data"]
    volumes: [mctrader_data:/var/lib/mctrader/data]
    depends_on: [bithumb-ingester]  # soft (named volume race-free)
    healthcheck: ...  # /health on 8081
    restart: unless-stopped
```

## 5. 비기능 (perf / observability)

### 5.1 Performance Baseline (TestContractArch 검증 필요)

| 항목 | 현재 (단일 collector) | 목표 (ingester) |
|------|---------------------|----------------|
| 50sym × 3ch event rate | ~수백/sec | 동등 |
| per-event WS-to-disk latency | ~ms (메모리 버퍼) | per-message fsync 기준 < 5ms p99 |
| ingester CPU / mem | 1 core / ~300 MB | 동등 (Parquet 부담 제거) |
| compactor 처리량 | N/A | L1: 12 segments/min/symbol-channel sustainable |

### 5.2 Observability

- Heartbeat: `heartbeat-{role}-{node_id}.json` (role = ingester | compactor)
- HTTP `/health` (port 8080 ingester, 8081 compactor) — `/metrics` Prometheus exposition (후속, 본 Story 범위 외)

**Compactor metrics — type / labels / semantics 박제 (F8 fix)**:

| Metric | Type | Labels (cardinality) | Cold-start 값 | Semantic |
|--------|------|---------------------|--------------|----------|
| `compaction_lag_seconds` | **gauge** | `exchange`, `channel`, `node_id` (3 dim, ~3×3×N nodes ≈ 9-27) | **`-1`** (sentinel "no sealed segment yet") — `null` / `0` / `infinity` 모두 거부 (Prometheus 호환 + alert 식 `compaction_lag_seconds > 60` 가 cold-start 시 false 평가 보장) | latest sealed segment age = `now - max(sealed_segment.last_modified)`. Compactor 가 모든 sealed segment 처리 완료 시 `0`, sealed segment 없으면 `-1`. |
| `wal_disk_used_bytes` | **gauge** | `exchange`, `channel` (2 dim, ~3×3 = 9) | `0` (정상) | `du -sb wal/<exchange>/<channel>/` 의 매 분 polling. |
| `compaction_failures_total` | **counter** | `exchange`, `channel`, `tier` (L1/L2/L3), `reason` (collision / sha256_mismatch / parquet_write_fail / lock_timeout) (4 dim, ~3×3×3×4 = 108) | `0` | irreversible counter. process restart 시 reset (Prometheus 가 reset detect). |
| `compaction_processed_total` | **counter** | `exchange`, `channel`, `tier` | `0` | sealed segment → Parquet 성공 emit 횟수. 회귀 detect 용. |
| `wal_segments_active` | **gauge** | `exchange`, `channel` | `0` | active (`.ndjson` 미 sealed) segment 개수. Ingester 정상 시 = active symbol 수. |

**Alert 임계 — `wal_disk_used_bytes` 분모 정의 (F8 fix)**:

- **분모 = named volume host disk 용량** (NOT dedicated quota — Phase A/B/C 단계는 dedicated quota 미설정).
- 산출 방법: 매 5분 `docker system df --format '{{json .}}'` → `Volumes` 항목 중 `Name=mctrader_data` 의 `Size` 값 + host root partition 잔여 용량 (`df -B1 /var/lib/docker/volumes`). 외부 metric `host_disk_total_bytes` (gauge, label=`mountpoint`) 박제.
- **Alert rule (Prometheus)**:
  ```
  sum(wal_disk_used_bytes) by (exchange, channel) / on() host_disk_total_bytes{mountpoint="/var/lib/docker/volumes"} > 0.80
  ```
  → 80% 도달 시 P1 alert (operator notify). 90% 도달 시 P0 alert + ingester `WAL write fail-fast` (§7.4.1 정합).

**§5.3 — Internal pipeline SLO N/A 명시 (F11 fix)**:

본 Story 의 결과물 (`mctrader-data` ingester + compactor) = **internal data collection pipeline**. 외부 사용자 facing API 노출 없음. 따라서:

- **Public SLO = N/A** — uptime / availability target 미설정 (자동룰 P0 면제 적용).
- **Error budget 정책 = N/A** — internal tool, 운영자 alert 기반 dispatch 의무 (정량 budget 미정의).
- **사유**: 본 Story 의 invariant 는 zero-loss data preservation (INV-1) 이며 통계적 SLO (예: 99.9% uptime) 는 부적합. crash 발생 시 데이터 보존 (zero-loss) 가 측정 대상 — binary pass/fail.

본 N/A 박제는 docs/superpowers/specs 의 자동룰 SSOT 정합 ("내부 도구·plugin meta Story → N/A 명시 + 사유 1줄").

## 6. 리팩터링 선행

- **PR #17 (SIGTERM handler) merge 선행** — Ingester graceful close 의 prerequisite
- 기존 `tick_storage.TickWriter` 클래스는 **deprecated** 표기 + 내부 사용처 (없음 확인) — 단위 테스트는 유지하되 신규 사용 금지
- `collector.CollectorDaemon._handle_event` → `_emit_to_wal` 으로 rename + WalIngester 의존성 주입

## 7. 보안 / 운영 리스크 설계

### 7.1 Trust boundary (SecurityArchitectAgent 산출)

| Boundary | from → to | 위협 | 완화 |
|----------|-----------|------|------|
| WS endpoint → Ingester | Bithumb (untrusted external) → Ingester process | malformed payload, rate flood | 기존 `BithumbWebSocketStream` 검증 + ingester는 이를 그대로 NDJSON으로 직렬화 (검증은 compactor 단계 schema validation) |
| Ingester → WAL volume | container A → shared FS | 권한 우회 write | named volume + container UID isolation (ingester / compactor 동일 UID 1000, host root squash via Docker default) |
| Compactor → Parquet partition | container B → shared FS | concurrent write race | atomic rename + per-partition file naming with `compaction_run_id` (collision 0) |
| operator → host volume | host shell → mctrader_data | 임의 read/delete | named volume (host path leak X) + backup recipe in compose.yml comment (ADR-033) |

### 7.2 Auth / authz

- 본 변경은 internal pipeline only — 외부 API 노출 없음
- Compactor `/health` 8081은 container 내부 only (compose `ports:` 미지정)

### 7.3 데이터 보호

- WAL NDJSON 파일은 `0640` (owner read/write, group read) — multi-user host 시 group leak 방지
- 재기동 시 자동 replay = 데이터 복구가 아닌 **forward-only 누락 0 보장** (ADR-009 §D12 invariant 유지)
- raw_json (WS payload) 포함 시 거래소 별도 PII 없음 — public WS 데이터

### 7.4 운영 리스크 (OperationalRiskArchitectAgent 산출)

| 항목 | 위협 | 완화 |
|------|------|------|
| **7.4.1 Compactor 실패 → WAL 무한 누적** | Compactor crash loop / disk full 미감지 | (a) `wal_disk_used_bytes` 메트릭 export → 임계 80% 시 alert (operator-readable in `/health`); (b) compactor restart_policy=unless-stopped + max retry; (c) ingester는 WAL write 실패 시 SIGTERM (data loss 회피 위해 fail-fast) |
| **7.4.2 WS disconnect / reconnect flap** | reconnect 동안 누락 (ADR-009 forward-only invariant 한계) | 기존 `BithumbWebSocketStream` reconnect logic 보존 + heartbeat `ws_state` 모니터링 (이미 존재) |
| **7.4.3 Clock skew (multi-node)** | segment 파일명 충돌 / L2 hour boundary 오작동 | NTP 의존 (ADR-033 host-level NTP enforced); segment 파일명에 `node_id` 포함하여 충돌 회피 |
| **7.4.4 Bithumb rate-limit / IP block** | ingester 전체 disconnect | 기존 reconnect logic; multi-exchange 후 다른 exchange는 영향 X (격리 효과) |
| **7.4.5 Env isolation (dev/prod 동일 volume race)** | dev 머신에서 동일 named volume 사용 시 prod와 충돌 | named volume name에 prefix 강제 (`mctrader_data_<env>`); compose.yml 주석으로 안내 |

**§7.4.6 (consult to DataMigrationArch §11.6) — Idempotency**: Compactor가 동일 sealed segment를 두 번 처리해도 동일 결과 (write-then-rename + sha256 비교). 자세한 사항은 §11.6 참조.

### 7.5 Threat modeling 인용 (STRIDE 요약)

- **Spoofing**: 내부 컨테이너 only, IPC 없음 → N/A
- **Tampering**: WAL 손상 detection — sealed segment에 sha256 (file trailer) 추가 (§8 Test Contract)
- **Repudiation**: lineage manifest에 `compacted_from` 기록 (audit trail)
- **Information disclosure**: 위 §7.3 권한
- **DoS**: WS flood — Bithumb 측 throttle; ingester는 fail-fast (WAL write 실패 = SIGTERM)
- **Elevation**: container 격리 (Docker default, root squash)

**raw_json log redact 정책 (F9 fix)**:

- ADR-009 §D10.1 / §D11.1 / §D14.1 의 `raw_json` column = nullable (debug optional). WAL NDJSON 에는 보존되나 **로그 stream 에는 redact 의무**.
- **로그 emit 정책**:
  - heartbeat / health-check / alert log = `raw_json` field 제외 (메타데이터만 — symbol / channel / ts_utc / received_at / event_type / level)
  - error log (parse fail / WAL write fail) = `raw_json` 의 first 200 chars + suffix `... [truncated, len=N]` (전문 leak 방지 + line-length DoS 회피)
  - debug log (env var `MCTRADER_DEBUG_RAW_JSON=1` 명시 시) = full `raw_json` 허용 (production 미설정)
- **Implementation**: `mctrader_data.logging` 모듈에 `_redact_raw_json(record_dict)` helper — log emit 직전 `raw_json` field 가 dict 에 있으면 default 로 제거. 모든 ingester / compactor log call 이 본 helper 경유 의무.
- **Bithumb public WS 데이터의 PII 부재 검증**: 본 정책은 PII 보호가 아닌 (a) log line 길이 폭발 회피 (raw_json ≈ 1KB × 수만 line/min) + (b) future private endpoint (Live Epic) 진입 시 자연스러운 redact 기본값 보장.

### 7.6 보안 ack

SecurityArchitectAgent 채택 — author Architect agree. 본 변경은 외부 trust boundary 추가 없음, 내부 IPC만 named volume.

### 7.7 N/A 영역

- 외부 API 노출 없음 (admin control plane은 MCT-97 별도)
- Secret/credential 신규 없음 (ADR-008 변경 없음)

## 8. Test Contract (TestContractArch 산출 + Architect 통합)

### 8.1 Invariant (zero-loss)

- **INV-1 [Crash-recovery zero-loss]**: Ingester가 메시지 K개 수신 후 SIGKILL → 재시작 → Compactor 처리 후 Parquet에 K개 모두 존재 (per-message fsync 기준)
  - 테스트: `tests/test_wal_ingester_crash_recovery.py::test_sigkill_after_n_messages_yields_zero_loss`
  - **경계 (F12 fix — per-message fsync 설계 alignment, batch_size 개념 제거)**: K=1 (single-message fsync barrier), K=10_000 (segment seal 다중 발생 — 5분 sustained window). 기존 K=499/500 boundary 는 legacy `TickWriter.batch_size=500` 의 buffer flush boundary 의미였으나, 신규 per-message fsync 설계 (Ingester 가 매 record 마다 fsync) 에서는 batch_size 개념이 제거되어 motivation 약화 → boundary 에서 제거. (정보 보존 차원으로 legacy batch_size=500 의 historical context 만 §3.2 또는 ADR-017 Context 절에 1줄 박제.)
  - **Fsync-batch fallback boundary**: `--wal-fsync-batch=N` (N>1) 옵션 사용 시 (perf trade-off mode) 추가 boundary K=N (N건 buffer 후 fsync, last partial batch 가 SIGKILL 시 유실 가능) — 이 mode 의 INV-1 약화 = "최대 N-1 건 유실" 명시 invariant 로 분리 (INV-1-fallback).
- **INV-2 [Atomic seal]**: WAL `.ndjson` → `.ndjson.sealed` rename은 atomic (rename 도중 crash 시 둘 중 하나만 존재)
  - 테스트: `tests/test_wal_segment::test_seal_is_atomic_under_crash` (mock os.replace + crash injection)
- **INV-3 [Compaction idempotency]**: 동일 sealed segment를 N번 compact해도 최종 Parquet는 동일 sha256
  - 테스트: `tests/test_compactor_l1::test_idempotent_double_compaction`
- **INV-4 [Forward-only preservation]**: ADR-009 §D12 invariant — Ingester가 timestamp 역행 record 수신 시에도 WAL append 허용 (정렬은 Compactor 책임), Compactor는 Parquet write 시 sort-by-ts_utc 보장
  - 테스트: `tests/test_compactor_l1::test_out_of_order_records_sorted_in_parquet`
- **INV-5 [Schema preservation]**: NDJSON → Parquet 변환 후 모든 필드 (`ts_utc`, `received_at`, `price` decimal128(38,18) 정밀) 유지
  - 테스트: `tests/test_wal_ndjson_codec::test_decimal_roundtrip_no_precision_loss`
- **INV-6 [Lineage 무결성]**: compacted Parquet의 lineage에 `compacted_from` 모든 source segment + sha256 기록
  - 테스트: `tests/test_compactor_l1::test_lineage_records_compaction_provenance`
- **INV-7 [Tier 멱등 합성]**: L1 12개 → L2 1개 합성 결과 = L1 raw concat 결과 (sort + dedup 후)
  - 테스트: `tests/test_compactor_l2::test_l1_to_l2_preserves_records`
- **INV-8 [Forward-only 시 데이터 추가만]**: L3 생성 후 같은 day의 L2를 다시 합성해도 L3 record count는 단조증가 (재처리 허용, 손실 X)
  - 테스트: `tests/test_compactor_l3::test_reprocessing_same_day_is_monotone`
- **INV-9 [Multi-node active-active partition 정합 — F5 fix]**: ingester 2개 (`node=NODE_A` + `node=NODE_B`) 동시 실행 + 동일 WS upstream 수신 시 (a) 양 node 의 sealed segment 가 각각의 `node=` partition 으로 분리 emit, (b) read API 의 mixed scan 이 ADR-009 §D2.1 dedup contract 적용 (T2 tick = §D10.7, T3 orderbook = §D11.8, snapshot = §D14.6 logical key) 후 단일 view 반환, (c) `node=` 부재 legacy partition 도 `node=DEFAULT` 로 mixed scan 양립.
  - 테스트: `tests/integration/test_active_active_partition_integrity.py::test_dual_node_dedup_with_legacy_partition`

### 8.2 Crash injection 시나리오 (R8)

| 시나리오 | 주입 시점 | 기대 결과 |
|---------|----------|----------|
| Ingester SIGKILL during ndjson write | append-line 직후 (fsync 미완) | last record may be lost (per-message fsync 디폴트는 OS write barrier) |
| Ingester SIGKILL during seal rename | os.replace 직전 | `.ndjson` 잔존, 다음 startup 시 active로 인식 → 재처리 |
| Compactor SIGKILL during Parquet write | tmp file write 중 | tmp 파일 잔존, sealed segment 미처리 상태 → 재시작 시 재처리 (idempotent) |
| Compactor SIGKILL during atomic rename | os.replace 직전 | tmp 파일만 존재, 최종 경로 미생성 → 재시작 시 재처리 |
| Compactor SIGKILL during source `.compacted` rename | Parquet 완료 후 source rename 직전 | sealed segment 그대로 → 재처리 시 same Parquet 결과 (INV-3 idempotency) |

### 8.3 Performance baseline 테스트

- `tests/test_wal_perf.py::test_50sym_3ch_sustained_rate` — 50sym × 3ch synthetic load, per-message fsync 기준 disk write throughput 측정 (제거 X, 회귀 감지)
- 임계: WS-to-disk p99 latency < 5ms, sustained rate > 1000 msg/sec/node

**Mean 10% regression 차단 protocol (R8 R9, F5 fix)**:

- **Sample N**: 단일 run = 60초 sustained, 측정 sample = 1초 단위 60 bucket. p99 = bucket 별 latency p99 의 60-bucket mean.
- **Variance threshold**: bucket 별 std dev / mean ratio < 20% (Coefficient of Variation < 0.2). 미달 시 measurement-noise 판정 + 재시도 3회.
- **Baseline locking**: 첫 PR-2 (Phase B) merge 직후 main 브랜치에서 5회 측정 → mean p99 = baseline 박제 (commit SHA 와 함께 `tests/perf_baselines/wal_perf_baseline.json`).
- **회귀 차단 조건**: 후속 PR 의 mean p99 > baseline mean p99 × 1.10 (10% 마진) AND p-value < 0.05 (Welch's t-test, n=5 vs n=5) → CI fail. ADR-029 (perf measurement) 의 dual-criterion 정합.
- **Cold cache**: 매 측정 전 `sync && echo 3 > /proc/sys/vm/drop_caches` (Linux only — CI runner Linux 만 신뢰).

### 8.4 통합 테스트

- `tests/integration/test_ingester_compactor_roundtrip.py` — Ingester+Compactor 동시 실행 → 60초 후 Parquet 재구성 → 입력 record와 1:1 매칭
- `tests/integration/test_multi_exchange_isolation.py` — 2개 ingester (mock bithumb + mock upbit) 동시 실행 → 한쪽 crash가 다른쪽 영향 X 확인

### 8.5 채택/반박

- TestContractArch 8 invariant 모두 chief author 채택
- Performance baseline은 production 50sym 환경에서 측정 (synthetic 외 추가) — DesignReview 단계 R8 evidence 요구

## 9. Rollout / Backout

### 9.1 Rollout (Phased)

1. **Phase A (mctrader-data PR-1)**: WAL ingester 모듈 + ndjson codec + 단위 테스트 — collector.py 미변경, 코드 dormant
2. **Phase B (PR-2)**: Compactor 모듈 + L1/L2/L3 + integration test
3. **Phase C (PR-3)**: collector.py `_handle_event` 를 WalIngester 호출로 전환 + compose.yml에 compactor service 추가 (production cutover)
4. **Phase D (PR-4)**: legacy TickWriter / OrderbookWriter 클래스 deprecated 마킹 + 단위 테스트 유지

### 9.2 Cutover 전략

- 기존 collector container를 stop → wal/ 디렉토리 빈 상태 확인 → ingester+compactor compose up → 5분 모니터링 (heartbeat / compaction_lag)
- Rollback: ingester+compactor stop → 기존 collector image rollback (legacy code path 유지하므로 가능). 신규 WAL 파일은 다음 release에서 manual `compact` CLI로 흡수.

**Phase C 진입 직전 canary / shadow run (F5 fix — production 50sym 측정 의무)**:

1. **Shadow run window** (Phase B merge 후 ~ Phase C cutover 전 사이): 기존 collector container 가 production 운영 중인 상태에서 별도 호스트 또는 별도 named volume (`mctrader_data_shadow`) 으로 신규 ingester+compactor 를 dual-run. 단일 symbol (BTC_KRW) shadow window — 5분 측정.
2. **Heartbeat 비교**: shadow ingester 의 `heartbeat-ingester-shadow.json` 의 `events_received` 와 production collector 의 `heartbeat-{node_id}.json` 의 `events_received` 가 ±1% 이내 일치. 미달 = root cause analysis (WS reconnect 시점 차이 / drop / parse error).
3. **Compaction-lag 측정**: shadow compactor 의 `compaction_lag_seconds` 가 5분 sustained < 10s. 미달 = Phase C 진입 거부 + IOPS bottleneck 분석.
4. **Disk overhead 측정**: shadow named volume 의 `wal/` + `market/` 사용량 = 5분 sustained < 100MB (BTC_KRW single-symbol 기준 sanity check).
5. PASS → Phase C 진입 (production volume cutover). FAIL → Phase B 회귀 + 측정 결과 박제.

본 canary run 은 Phase A/B dormant code 단계의 production 측정 부재 risk (R8) 를 차단한다.

### 9.3 Backout 조건

- per-message fsync 기준 disk IOPS 한계 도달 (production 50sym × 3ch 측정 후 결정)
- → fallback: `--fsync-batch=10` 으로 throughput 회복, zero-loss 보장은 약화 (최대 9건 유실 가능) — 운영자 명시 trade-off

## 10. ADR 판단

- **ADR-017 신규** (위 첨부): WAL + tiered compaction 결정 박제
- **ADR-009 amendment** (PR ordering: **Phase A PR-1 의 head commit 1건**으로 land — Phase B/C/D 모두 본 amendment 의 partition contract 에 의존하므로 별도 PR 거부): §D2 / §D5 / §D10.2 / §D11.2 / §D14.2 의 Hive layout 에 `tier=L{1,2,3}` 추가 키 명시 + 본 ADR-017 §Decision 2 의 mandatory `node=` partition contract cross-reference. amendment 절 신규: §D2 amendment ("Tier partition for compaction, MCT-106 Phase A entry, 2026-05-09") — `tier=` 키가 모든 read API (`scan_*`) 에서 partition pruning 대상 + tier 부재 시 `tier=L1` 호환 처리 박제. 본 amendment commit 은 Phase A PR-1 의 첫 commit (코드 변경 0 — docs only) 으로 land 하여 Phase B/C/D 의 compactor 구현이 ADR-009 SSOT 와 동기화된 상태에서 진행.
- **ADR-033 정합**: 변경 없음 (named volume DR / restart unless-stopped 그대로 사용)

## 11. 데이터 마이그레이션 (DataMigrationArchitectAgent 산출)

### 11.1 기존 Parquet 자산 분류

| 분류 | 개수 (2026-05-09 실측) | 처리 |
|------|----------------------|------|
| Healthy Parquet (footer present) | 508 | tier 키 부재 → query layer가 L1으로 해석 (backward-compat) 또는 in-place rename to `tier=L1` partition |
| Corrupted Parquet (footer missing) | 299 | quarantine list ledger → `<root>/market/quarantine/corrupted-2026-05-09.json` 에 path + reason 기록. 파일은 **유지** (fsck 도구 사후 확보 시 재시도 가능). forward-only 데이터 손실은 회복 불가. |

### 11.2 Migration 전략

- **Forward-only**: 신규 데이터부터 WAL → tier=L1 / `node=<id>` 경로로 진입. 기존 Parquet은 in-place 유지.
- **Query layer compatibility shim**: `scan_ticks` / `scan_orderbook` 등 read API에 (a) `tier` 키 부재 시 L1 동등 처리 분기 + (b) `node=` 키 부재 시 `node=DEFAULT` 동등 처리 분기 (ADR-009 §D2.1 mixed scan 영구 정책 정합) — 1줄씩 2 분기 추가, 후속 PR
- **`node=` 값 정의 (F6 fix)**:
  - **Compactor emit Parquet 의 `node=` 값**: source ingester 의 `MCTRADER_NODE_ID` env (compose service 별 unique). Compactor 자체는 `node=COMPACTOR` 고정값 사용 거부 — Compactor 는 단순 변환자이며 source `node_id` 보존 의무. multi-node ingester (active-active HA) 도입 시 ADR-009 §D2.1 dedup contract 가 자연 적용 (compactor 가 임의 fixed 값으로 덮어쓰면 contract 깨짐).
  - **단일 node 운영 시**: Phase A/B/C dormant cutover 단계 = compose.yml 의 `bithumb-ingester` service 가 `MCTRADER_NODE_ID=NODE_A` env 박제 (또는 hostname 자동 detect). single-node 운영도 partition 강제.
  - **Sealed segment 의 `node_id` source**: WAL segment 파일명 `segment-{YYYYMMDDHHMMSS}-{node}.ndjson.sealed` 의 `{node}` portion 을 Compactor 가 parse 하여 emit Parquet 의 `node=` 값으로 채택. ingester startup 시 env 에서 읽어 segment 명에 박제 → compaction 시 자연스럽게 보존.
- **L2/L3 backfill**: 기존 L1-equivalent (legacy) Parquet에 대해 1회 `compact --backfill --since 2026-05-01` 실행하여 L2/L3 생성 (optional, 운영자 결정). backfill 결과의 `node=` 값 = `node=DEFAULT` (legacy file 은 node 정보 없으므로). 이후 ADR-009 §D2.1 mixed scan 자연 적용.

### 11.3 Cutover 절차

1. 기존 collector stop (graceful — chore PR #17 SIGTERM)
2. `mctrader_data` 볼륨 backup (ADR-033 recipe)
3. quarantine ledger 작성 — 손상 299파일 path 기록
4. compose.yml swap (collector → ingester + compactor)
5. **UID 1000 정합성 검증 (F6 fix, §7.1 named volume UID isolation cross-ref)**:
   - compose.yml 의 `bithumb-ingester` + `compactor` service 모두 `user: "1000:1000"` entrypoint 명시 (Dockerfile USER instruction 또는 compose.yml `user:` 키)
   - 기존 named volume `mctrader_data` 의 owner 가 UID 1000 인지 `docker run --rm -v mctrader_data:/data alpine stat -c '%u:%g' /data` 으로 사전 확인
   - 미달 시 (host root 등) 거부 + ADR-033 named volume DR recipe 의 UID 정합성 절 확장 의무 (별도 ADR-033 amendment)
6. 5분간 heartbeat / compaction_lag 모니터링
7. PASS → 완료 / FAIL → §9.3 rollback

### 11.4 Rollback

- compose.yml 이전 commit revert (collector single-container 복구)
- WAL 디렉토리 (`<root>/wal/`)는 잔존 — 다음 cutover 시 compactor가 처리 (zero-loss 보존)
- tier=L1 partition은 그대로 (legacy reader가 backward-compat으로 read 가능)

### 11.5 Integrity invariant

- 기존 healthy Parquet 508개의 row count + sha256 = 마이그레이션 전후 동일
- 손상 299파일은 quarantine ledger에 명시적 기록 — silently delete 금지
- WAL → Parquet 변환 결과 row count = WAL line count (per segment)

### 11.6 Idempotency (DataMigrationArch primary + OperationalRiskArchitect consult)

- Compactor가 동일 sealed segment 처리:
  1. tmp 파일에 write
  2. sha256 계산
  3. 기존 final 경로의 sha256과 비교
  4. 동일 → tmp 삭제 + source `.compacted` rename (no-op write)
  5. 다름 → DataMigration ledger에 `compaction_collision` 기록 (운영자 검토)

**`compaction_run_id` determinism (F10 fix)**:

- 박제 정의: `compaction_run_id = sha256(sealed_segment_relative_path).hexdigest()[:16]`
- **timestamp 제거** (이전 정의의 `+timestamp` portion 제거 사유): 동일 sealed segment 의 재처리 시 동일 `compaction_run_id` 보장 → 동일 partition 안 multiple file 발생 회피.
- **Determinism invariant**: 동일 sealed segment 가 N번 compact 되어도 항상 동일 `compaction_run_id` → emit Parquet 의 filename `part-{run_id}.parquet` 동일 → atomic write-then-rename 의 destination 도 동일. tmp 충돌 회피 = tmp 파일명에 `os.getpid()` 포함 (`part-{run_id}.{pid}.tmp`).
- **Same-partition uniqueness invariant (F10 fix)**: 동일 (`tier`, `exchange`, `symbol`, `date`, `node=`) partition 안에서 동일 `compaction_run_id` = 동일 source sealed segment. 다른 sealed segment 가 동일 partition 에 emit 시 sha256 prefix 16-hex 충돌 확률 = 2^-64 (negligible). 충돌 detected 시 fail-closed halt + ledger emit (`compaction_run_id_collision` reason).
- **Step 5 확장 (F10 fix)**: 동일 final path + 다른 sha256 detected case (legacy ambiguity 해소):
  - case A: 동일 sealed segment 재처리 + Compactor 코드 변경 (e.g., column ordering 변경) → 동일 sha256 보장 안 됨 → `compaction_collision` ledger 의 sub-reason `code_change_detected` 박제 + 운영자 검토 의무 (Compactor 의 deterministic_compactor_version 이 변경되었는지 확인)
  - case B: 동일 sealed segment 재처리 + 코드 변경 0 + sha256 다름 → 비결정적 처리 (parallel ordering / float roundoff 등) → fail-closed halt + bug report (deterministic invariant violation)
  - 두 case 모두 silent overwrite 거부 — 기존 final file 보존, tmp 삭제, 운영자 dispatch.

### 11.7 N/A

- Schema breaking change 없음 (`tier` 키 추가는 additive Hive partition)
- RDB 마이그레이션 없음 (MCT-105 별도 sprint)

## 12. PL 검수 결과

### 12.1 ArchitectPL 1차 (2026-05-09, Iteration 1 entry)

- §섹션별 deputy author input 통합 정합성: PASS
  - §2 CodebaseMapperAgent: 결합도 분석 + 변경 영향 지도 반영 ✓
  - §3·§6 RefactorAgent: 패키지 분리 (wal/ + compactor/) + Phased PR 채택 ✓
  - §7 (§7.1-§7.3, §7.5-§7.6) SecurityArchitectAgent: trust boundary 4 항목 + STRIDE 인용 ✓
  - §7.4 OperationalRiskArchitectAgent: 5 항목 (compactor failure / WS / clock / rate-limit / env) 모두 반영 ✓
  - §8 TestContractArchitectAgent: 8 invariant + 5 crash injection + perf baseline ✓
  - §11 (§11.1-§11.5) DataMigrationArchitectAgent: 손상 299파일 quarantine + forward-only migration ✓
  - §11.6 DataMigration primary + OpRisk consult: idempotency 5단계 ✓
- §섹션 누락 차단: §7 ✓ §7.4 ✓ §8 ✓ §10 ✓ §11 ✓ — 모두 present
- **VERDICT (1차)**: PASS → DesignReview lane 진입 요청

### 12.2 ArchitectPL FIX 회귀 (2026-05-09, Iteration 1 → Iteration 2)

DesignReviewPL Iteration 1 → P0=1 / P1=8 / P2=2 finding (Story §10 FIX Ledger 참조) → ArchitectPL 회귀 → ArchitectAgent 재spawn → 12 finding 모두 fix:

| FIX | Severity | 반영 위치 | 검증 |
|-----|---------|----------|------|
| F1 | P0 (adr-mismatch) | §4.2 + ADR-017 §Decision 2 — `node=<id>` mandatory + legacy mixed scan 영구 anchor | ADR-009 §D2.1 contract 인용 ✓ |
| F2 | P1 (design-completeness) | §3.3 — L1Compactor.compact_segment pipeline 안에 §D14.10 throttle + payload_hash dedup 시점 박제 | ADR-009 §D14.6 / §D14.10 cross-ref ✓ |
| F3 | P1 (adr-mismatch) | §10 — ADR-009 amendment commit 을 Phase A PR-1 head 로 land | dependency 차단 ✓ |
| F4 | P1 (implementability ×4) | §3.2 — O_APPEND fd / `(now // 300) > (start // 300)` boundary / fcntl.flock orphan lock / `str(Decimal)` SSOT | unit test plan 4건 포함 ✓ |
| F5 | P1 (test-contract ×3) | §8.3 perf protocol (CV<0.2 + Welch t-test) + §8.1 INV-9 multi-node + §9.2 5분 canary shadow | INV-9 추가 ✓ |
| F6 | P1 (data-migration) | §11.2 `node=` 값 정의 (source ingester 보존, COMPACTOR fixed 거부) + §11.3 step 5 UID 1000 검증 | §7.1 cross-ref ✓ |
| F7 | P1 (api-compatibility) | §4.1 — `collect` CLI 부작용 변경 (synchronous → async Parquet emit) 영향 표 + 마이그레이션 path | engine / WFO / test 영향 분석 ✓ |
| F8 | P1 (observability ×3) | §5.2 — metric type/labels/cold-start `-1` sentinel + alert 분모 = host disk + Prometheus alert rule | counter/gauge/histogram 분류 ✓ |
| F9 | P1 (observability) | §7.5 — `_redact_raw_json()` helper + log emit 정책 박제 | debug env override ✓ |
| F10 | P1 (implementability) | §3.3 + §11.6 — `compaction_run_id = sha256(path)[:16]` (timestamp 제거) + same-partition uniqueness invariant + collision step 5 case A/B 분리 | determinism 박제 ✓ |
| F11 | P2 (slo-missing advisory) | §5.3 (신설) — Internal pipeline SLO N/A + 사유 1줄 | 자동룰 면제 박제 ✓ |
| F12 | P2 (test-contract) | §8.1 INV-1 — K=1 / K=10_000 boundary 만 유지 + INV-1-fallback (fsync-batch mode) 분리 | per-message fsync alignment ✓ |

- **VERDICT (FIX)**: PASS → DesignReview Iteration 2 진입 요청
- **다음 단계**: Orchestrator → DesignReviewPLAgent 재spawn (Iteration 2)
