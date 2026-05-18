# ADR-017: Zero-loss ingestion via WAL + tiered compaction with multi-exchange ingester split

- **Status**: Proposed (2026-05-09, MCT-106 design lane)
- **Related**: ADR-009 (OHLCV/tick schema, forward-only invariant), ADR-033 (Docker-first, named volume DR)
- **Supersedes**: none
- **Amends**: ADR-009 §D5 / §D11 / §D14 (Hive layout amendment for L1/L2/L3 compaction tiers)

## Context

`mctrader-data`의 forward-only 수집 파이프라인은 단일 `mctrader-collector` 컨테이너에서
WS 수신 + 인메모리 버퍼링 + Parquet 직접 쓰기를 동시 수행해 왔다 (MCT-58/91/103).

2026-05-09 실측 — 총 Parquet 807개 중 **299개(37%) 손상** (footer 없는 incomplete file).
근본 원인:

1. `TickWriter.batch_size=500` — SIGKILL 시 최대 499건 인메모리 버퍼 유실
2. `pq.ParquetWriter`가 footer 미기록 상태에서 프로세스 종료 시 파일 자체 손상
3. SIGTERM 처리는 chore PR #17로 그레이스풀 종료 가능하나, OOM/SIGKILL/HW failure는 여전히 무방비

또한 사용자 의도상 **multi-exchange 확장** (upbit, binance 등) 시 단일 컨테이너 코드 분기는
운영 + 장애격리 측면에서 부담이며, exchange별 컨테이너 분리가 자연스럽다.

## Decision

수집 파이프라인을 **두 개의 책임으로 물리적 분리**한다:

### 1. Ingester 컨테이너 (exchange별 1개)

- **단일 책임**: WS 수신 → NDJSON WAL append (durable write) → ack
- **Zero-loss 보장**: 매 메시지를 `fsync` 동반 append-line 하여 SIGKILL 직전 메시지까지 디스크 보존
- **WAL 위치**: `<root>/wal/<exchange>/<channel>/<symbol>/<date>/segment-{startUtc}-{node}.ndjson`
- **WAL seal 방식 (D1 결정)**: **rotate-by-time** (5분 경계) + atomic rename `.ndjson` → `.ndjson.sealed`
  - 5분 경계에 도달하면 현재 segment를 close+fsync한 뒤 `.sealed` suffix로 atomic rename
  - 새 segment 파일은 동시에 open (gap 0)
  - sentinel file 방식 검토 후 거부 사유: filesystem race + 두 파일 atomic 조합 불가 → rename 단일 atomic syscall 채택
- **fsync 정책**: per-message fsync (zero-loss 우선) 디폴트, `--fsync-batch=N` 옵션으로 N건당 fsync (perf trade-off)

### 2. Compactor 컨테이너 (전역 1개, exchange-agnostic)

- **단일 책임**: sealed WAL segment scan → L1 (5min Parquet) → L2 (1h Parquet) → L3 (1day Parquet) tiered compaction
- **Compaction atomicity (D2 결정)**: **write-then-rename** + lineage manifest
  1. `tmp/<target>.parquet.tmp` 로 write
  2. ParquetWriter close + fsync
  3. atomic rename → 최종 경로
  4. lineage `compacted_from`에 source segment 경로 + sha256 기록
  5. source segment를 `wal/<...>/segment-*.ndjson.compacted` 로 atomic rename (delete 아님 — 24h grace 후 GC)
- **L1/L2/L3 layout (D3 결정)**: 기존 ADR-009 Hive layout 유지 + `tier=L{1,2,3}` 추가 키
  ```
  market/{ticks|orderbook|orderbook_snapshot}/schema_version=...v1/
    tier=L{1,2,3}/exchange=.../symbol=.../date=YYYY-MM-DD/
    node=<id>/part-{compaction_run_id}.parquet
  ```
  - `tier=L1` (5min Parquet, 정밀) — 기존 query API의 1차 source
  - `tier=L2` (1h Parquet, 압축) — query optimizer가 1h+ window에 대해 L1 대신 사용
  - `tier=L3` (1day Parquet, 콜드) — backtest 대량 스캔용

**MCT-167 amendment 박제 (2026-05-14, EPIC-tier-promotion-single-source, ADR-029 publish)** — D3 의 L1 storage backend 정책 확장. ADR-017 원안 = L1 local volume only (hot path optimization). ADR-029 D1 (사용자 directive 1, 2026-05-14) 박제 후 **L1 = local + NAS dual-write 의무**:

- **L1 NAS PUT timing**: ParquetWriter close + fsync + atomic rename `tmp/<target>.parquet.tmp` → `<target>.parquet` 직후 (compactor 측, ADR-029 D1=B 채택).
- **호출 primitive**: `DualWriter.put_streaming(path)` (MCT-163 LAND 산출물, ADR-029 D2=B). NAS PUT fail = DualWriter retry_queue 흡수 (caller block 0).
- **hot path 영향**: 0 — compactor = async / batched path, NAS PUT latency 가 collector WAL append 에 propagate 0.
- **invariant 폐기 후행**: ADR-027 §D5 "L1 NAS upload 금지" invariant 폐기 (ADR-029 D1 정합).
- **D3 의 nuance**: 본 amendment 도 D3 의 Hive layout / tier= partition 키 / `node=` mandatory 정책 = 변경 0. NAS PUT 의 추가만 박제 (storage backend 확장 only).
- **RPO=0 보장 chain**: WAL local (D1 fsync) → sealed atomic rename (D2 atomicity) → L1 ParquetWriter atomic (D2 step 3) → **L1 NAS PUT atomic (본 amendment, ADR-029 D1)**. ADR-029 D4=B (WAL sealed local only) 의 trade-off = L1 NAS PUT 완료 시점에 NAS 측 RPO=0 도달.
- **capacity-bounded ingest block (ADR-029 D5)**: NAS unreachable 시 정상 운영 시 hot path 영향 0, 단 WAL local volume usage >= 30 GiB 도달 시점에만 collector ingest soft stop (graceful + alert). ADR-029 D11 4 layer capacity 제한 정책 reference.

본 amendment 의 cross-ref:
- **ADR-029 D1/D2/D4/D5/D11** (NAS = SoT 전면 재설계)
- **ADR-027 §D5 amendment** (L1 upload 금지 invariant 폐기)
- **ADR-009 §D12.2 amendment** (forward-only invariant NAS object SoT 격상)
- **MCT-167** (governance singleton publish)
- **MCT-168** (L1 NAS DualWriter wiring impl)
  - **`node=<id>` mandatory (ADR-009 §D2.1 anchor)**: 모든 tier (`ohlcv.v1`/`tick.v1`/`orderbook.v1`/`orderbook_snapshot.v1`) Parquet partition leaf 직전에 `node=` level **mandatory** 강제. `<id>` = source ingester `MCTRADER_NODE_ID` env (compose service 별 unique). Compactor 는 sealed segment 의 source ingester `node_id` 를 emit Parquet partition 에 보존. 단일 node 운영 시 `node=DEFAULT` 또는 hostname 으로 partition 강제. 본 ADR 의 D3 결정은 §D2.1 의 mandatory partition contract 를 약화하지 않음 — optional 표기는 의도가 아니며, mandatory 이다.
  - **Legacy `node=` 부재 파일 처리 (영구 지원)**: 본 amendment 도입 전 mctrader-data 가 쓴 기존 healthy 508 파일은 `node=` partition 키 부재. ADR-009 §D2.1 "Mixed legacy partition layout 지원 (영구)" 정책에 따라 read API (`scan_ticks` / `scan_orderbook_events` / `scan_orderbook_snapshots`) 가 `node=` 부재 row 를 `node=DEFAULT` 로 취급하여 mixed scan 영구 지원. legacy partition 폐기는 별도 migration Epic 의 scope (본 ADR 범위 외).
  - **기존 `tier=` 키 없는 파일**: legacy migration mode 로 query layer 가 `tier 절대 부재 = treat as L1` 호환 처리. 본 정책은 §D2.1 의 `node=` 부재 mixed scan 정책과 양립 — `tier` + `node=` 양 키 모두 부재한 legacy file 도 read API 가 (`tier=L1`, `node=DEFAULT`) 로 자연 호환.
- **Compaction 주기**: 5min → L1 (sealed segment 도착 즉시), 매시 정각 → L2, UTC 자정 → L3
- **Replay 트리거 (D5 결정)**: Compactor 컨테이너 startup 시 자동으로 `*.ndjson` (active, never sealed) + `*.ndjson.sealed` (unprocessed) 모두 scan → sealed는 즉시 L1 compact, active는 대기 (Ingester가 seal하면 처리)
  - 단, active segment의 last-modified가 30min 초과이면 **orphan ingester crash** 판정 → forced seal + L1 compact 후 quarantine 표시

### 3. Ingester ↔ Compactor 인터페이스 (D4 결정)

**공유 named volume only** (sidecar API 거부)
- 단순성 + Docker named volume DR 정합 (ADR-033)
- segment 파일 자체가 "메시지 큐" 역할
- backpressure: Compactor가 처리 못 하면 WAL 누적 → 디스크 모니터링으로 alert (§7.4 OperationalRiskArch 항목)

### 4. 패키지 분리 (D6 결정)

**`mctrader-data` 내부 모듈 분리** (별도 repo 거부 사유: collector가 이미 `tick_storage`/`orderbook_storage` 모듈에 의존, schema SSOT 공유 필요)
- 신규 모듈: `mctrader_data.wal` (Ingester writer/segment) + `mctrader_data.compactor` (Compactor)
- 기존 `tick_storage`/`orderbook_storage`/`orderbook_snapshot_storage` 의 Parquet writer는 Compactor가 재사용 (코드 중복 X)
- 기존 collector는 **deprecated → wrapper**: 내부적으로 ingester+compactor 동시 실행 (single-host dev 모드, 운영은 분리)

## Migration

### 손상 파일 처리

- 기존 299개 손상 Parquet은 **read-side quarantine list**로 격리 (delete X)
  - reader가 footer-missing 감지 시 quarantine list에 ledger
  - forward-only invariant 위반 (ADR-009 §D12) — 데이터 복구 불가
- 신규 데이터부터 zero-loss 보장
- **migration 방향**: forward-only — 기존 healthy Parquet은 `tier=L1`로 in-place rename (atomic) 또는 query layer가 tier-absent를 L1으로 해석하는 호환 모드 (Story §11 매핑 참조)

## Consequences

### Pros

- SIGKILL/OOM/HW failure에도 zero-loss (per-message fsync 기준)
- 새 exchange = `<exchange>-ingester` 컨테이너 + compose service 1개 추가 (코드 변경 0)
- 장애격리: 한 exchange ingester crash가 다른 exchange 수집에 영향 X
- Compaction 분리로 read query latency 개선 (L2/L3 작은 파일 수)

### Cons

- 레이어 1개 추가 (WAL → Parquet) → 디스크 사용량 약 2-3x 일시 (sealed compacted 후 GC 24h)
- per-message fsync는 IOPS 증가 (per-symbol per-event ~1ms latency 추가) — 50symbol × 3channel benchmark 필요 (§8 Test Contract)
- Compactor 단일 인스턴스 = SPOF — initial release는 active-passive (heartbeat 기반 takeover 없음, single-host dev 우선) → 후속 ADR
- 손상 299파일 = 영구 데이터 손실 (forward-only, recovery 불가)

### Neutral

- 기존 query API (`scan_ticks`/`scan_orderbook` 등)는 tier 키 호환 처리 후 변경 없음
- Heartbeat / health endpoint는 ingester/compactor 각각 별도 export (heartbeat-{node_id} → heartbeat-{role}-{node_id})

## Alternatives considered

### A. SQLite WAL layer

- 거부 사유: 멀티 writer (per-symbol thread) 시 single-writer lock contention; sqlite WAL은 process 단위 lock
- ndjson append는 file-level append이며 단일 file descriptor write가 atomic (POSIX `O_APPEND`) → multi-thread 안전

### B. Kafka / RabbitMQ

- 거부 사유: 운영 부담 (broker 별도 운영) + Docker-first ADR-033 단순성 위배 + single-host pilot 단계 과잉설계
- 추후 multi-host 확장 시 재검토

### C. PostgreSQL append + LISTEN/NOTIFY (이번 sprint MCT-105)

- 거부 사유: tick stream rate (per-symbol 수십 events/s × 50sym × 3ch ≈ 수천/sec)에 대해 RDB 적합성 부족
- RDB는 metadata/account/order 등 transactional state 용도 (MCT-105 범위)

### D. Stay with single-container collector + SIGKILL 방어 강화

- 거부 사유: Parquet footer 구조상 graceful close 외 zero-loss 불가능 (footer는 close 시점에 written) → 근본 해결 X

## References

- Story: `docs/stories/MCT-106.md`
- Change Plan: `docs/change-plans/MCT-106-change-plan.md`
- ADR-009 (forward-only, Hive layout SSOT)
- ADR-033 (Docker-first, named volume DR)
- POSIX `write(2)` O_APPEND atomicity for single-writer ndjson

## Amendment History

- 2026-05-12 — **Transaction-tier WAL policy + Compactor MCT-132 framework 확장 + Fallback dedup + Gap detection** (MCT-135, Epic MCT-112 Story-1). 본 amendment 는 본 ADR-017 의 ingester / compactor 분리 + WAL + tiered compaction 패턴을 transaction.v1.1 stream (ADR-009 §D10 amendment) 의 SSOT 운영에 확장. ADR-009 D10.7 fallback dedup key + ADR-009 D12.2 forward-only invariant 정합.
- 2026-05-14 — **Compactor Source 규약 (channel matrix SSOT) + multi-channel exchange 지원** (MCT-164, EPIC-data-accumulation-umbrella). MCT-165 V2 verify 잔존 YES (upbit L1 partition 0) trigger. L1/L2/L3 compactor 의 source channel 매핑 SSOT (`docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md`) + snapshot → depth 변환 의무 + multi-channel exchange 지원. ADR-027 Amendment 2 silent-skip 차단 sibling.
- 2026-05-18 — **Compactor sort key 규약 (content-derived, 파일명 untrusted) — Amendment 3** (`mctrader-data#96` LAND, WS-A 117GB unblock). L2/L3 compactor input 파일 정렬 키 = content-derived `ts_utc` (`pq.read_metadata` stats.min primary + `iter_batches[:1]` fallback). 파일명 byte-order/mtime sort 금지. L1 파일명 `part-<sha[:16]>` 시간정보 0 → `sorted(rglob)` quarantine root cause 영구 해소. ADR-009 §D2 Amendment N (L1 dual filename) sibling. ADR-027 Amendment 1 (MCT-160 monotonic verify) downstream 정합.

## §Amendment — Transaction-tier WAL & Compactor extension (NEW, MCT-135, Epic MCT-112 Story-1, 2026-05-12)

본 amendment 는 ADR-017 의 zero-loss + WAL + tiered compaction 아키텍처를 **transaction.v1.1** (ADR-009 §D10 minor extension) stream 의 SSOT 운영에 확장한다. MCT-132 Compactor Epic-A (LAND 2026-05-11) 의 framework + ParquetWriter mechanics 재사용 + policy 신규.

### §Transaction-tier WAL policy

**Goal**: Bithumb WS transaction stream 의 zero-loss SSOT 보장 (ADR-009 §D12.2 forward-only invariant + §D10 tick.v1.1 schema + §D10.7 fallback dedup).

**Policy**:

- **At-least-once delivery** — Bithumb WS frame 도착 시점에 collector 가 WAL append 후 ack. fsync 보류 가능 (batch fsync 정책 적용).
- **Batch fsync window** — `min(10-100ms wall-clock, 1000 msg count)` 둘 중 먼저 도달 시 fsync trigger. tunable (default = 50ms / 1000 msg). per-message fsync (본 ADR Ingester default) 와 trade-off — per-message fsync 는 IOPS 증가, batch fsync 는 power-loss window 트레이드.
- **WAL memory buffer** — 50,000 msg (5,000 msg/sec sustained × 10 sec burst). overflow 시 backpressure (Bithumb WS receive thread pause) — 적재 우선, throttle 차선. 기존 ADR-017 §3 (named volume) shared volume backpressure 패턴 정합.
- **SLA**: **power-loss window ≤ 100ms or ≤ 1000 msg (먼저 도달)**. process crash / SIGKILL / power-loss 시점 직전 batch fsync 후의 in-memory buffer = 손실. 100ms wall-clock 또는 1000 msg count 가 SLA 의 hard ceiling.

**Rationale (per-message fsync 대비 batch fsync 채택)**:

- Bithumb WS transaction stream peak rate ≈ 5,000 msg/sec (50 sym, burst). per-message fsync × 5,000 IOPS/sec = 디스크 IOPS budget 압박 (consumer-grade SSD = 50,000 IOPS, 10% 점유). batch fsync (50ms / 1000 msg) = 100 IOPS/sec → ~0.2% 점유, headroom 충분.
- power-loss window 100ms 는 production-acceptable (Bithumb WS reconnect 후 sequence hole detection 의 grace + gap 박제 정책 §D10.6 amendment 정합).
- 본 ADR-017 §1 Ingester 의 per-message fsync 정책 (orderbook tier) 은 그대로 유지 — orderbook = sequence number 부재 + reconstruction utility 의존, transaction = §D15 information bar contract 의 immutable input 으로 batch trade-off 정당.

**WAL file format**: 기존 ADR-017 §1 NDJSON segment (`<root>/wal/<exchange>/transaction/<symbol>/<date>/segment-{startUtc}-{node}.ndjson`) 답습. tick.v1.1 schema (§D10.1 + §D10.8 신규 3 column) 가 NDJSON line 의 JSON object. rotate-by-time (5분 경계) + atomic rename (`.sealed`) 정책 그대로 적용.

### §Fallback tuple dedup (tick.v1.1)

**ADR-009 §D10.7 fallback dedup key 확장 reference**:

- **Logical key (8-tuple)**: `(exchange, symbol, ts_utc, price, quantity, side, raw_json_hash, ingest_seq)`. `raw_json_hash` 는 ADR-009 §D10.8 의 `payload_hash` (raw frame SHA256 16-hex) 와 의미 일치 — raw_json column 이 nullable (debug optional) 일 경우 payload_hash 채택. `ingest_seq` 는 collector 측 monotonic seq (process restart 시 reset, `collector_run_id` 와 결합 시 monotonic).
- **근거**: Bithumb 가 unique `trade_id` 미제공 (ADR-009 §D2.1 anchor + §D10.7 fallback only) → primary key 채택 불가 → fallback tuple 적용. `ingest_seq` + `payload_hash` 추가는 dedup 정확도 향상 + active-active mismatch 검출 (ADR-009 §D10.8).
- **dedup procedure** (Compactor 의 sealed segment → L1 Parquet write 시점 + reader-side `scan_ticks` 시점 양쪽 책임):
  1. WAL sealed segment 의 NDJSON line union scan
  2. 동일 8-tuple 발견 시 idempotent skip (content equality 자연 검증)
  3. content mismatch (동일 7-tuple key + different payload_hash) → `active-active mismatch` quarantine emit (ADR-009 §D10.7 정책 답습)

### §Gap detection (Bithumb WS reconnect → sequence hole)

**Goal**: ADR-009 §D12.2 forward-only invariant 위반 사건 (Bithumb WS reconnect 시 sequence hole / backfill 불가) 의 row-level 박제 의무화.

**Detection 책임**: collector 측 (Ingester, Story-4 owner). Bithumb WS subscriber 가 reconnect detected 시 다음 procedure:

1. Reconnect 직후 첫 frame 의 `validation_status="RECONNECT_BOUNDARY"` 박제 (ADR-009 §D10.8 column).
2. Reconnect 전후의 `ingest_seq` gap > threshold (default = 1) 시 gap 박제. 단 Bithumb 가 unique trade_id 미제공 → gap size 추정 불가 (sequence number 부재). 다음 frame 의 ts_utc - reconnect 직전 frame 의 ts_utc = wall-clock gap 으로 표현.
3. Gap > threshold (default = 5 sec wall-clock, MCT-66 `tier_coverage` API 와 일치 — ADR-009 §D10.6) 시 `validation_status="GAP"` 박제. **backfill 불가** (ADR-009 §D12.2). row 자체 없음 → 다음 frame 의 validation_status column 으로만 표시.
4. `MALFORMED` 박제 — schema mismatch / 음수 price / 음수 quantity / unknown side 시 quarantine + row-level `validation_status="MALFORMED"` (ADR-009 §D10.6 halt 정책의 row-level visibility 추가).

### §Compactor MCT-132 framework 확장

**Goal**: MCT-132 Compactor Epic-A (LAND 2026-05-11) 의 framework + ParquetWriter mechanics 재사용 + transaction-tier policy 신규.

**Policy 수치**:

- **256 MB Parquet file roll** — 1000 ticks/sec 시 ~15-45분 (zstd level 3 압축률 ~50%, row size ~50 bytes), 100 ticks/sec 시 ~10x 길이. 50 sym × 평균 20 ticks/sec = 1000 ticks/sec sustained → ~30분/file.
- **4-8 GB process limit** — 32 GB host mem_limit 답습 (MCT-132 Compactor convention). streaming row groups 채택, whole-partition load 금지.
- **Partition layout** — `market/ticks/schema_version=tick.v1/tier=L{1,2,3}/exchange=bithumb/symbol={sym}/date={YYYY-MM-DD}/node={node_id}/part-{compaction_run_id}.parquet` (ADR-017 §3 D3 D3 layout 답습 + ADR-009 §D10.2 path).
- **Symbol cardinality fallback** — 파일 폭발 시 `exchange/date/hour` + symbol column 화 (D6 risk fallback, ADR-009 §D2.1 정합). 50 sym × 365 day × 24 file/day = ~438k file/year — manageable, fallback 미발동 가정.
- **ParquetWriter context manager pattern** — MCT-132 의 `with ParquetWriter(...) as w` 답습 (atomic write + footer flush + tmp → atomic rename, ADR-017 §2 D2 정합). MCT-132 source: `mctrader-data/.../compactor/parquet_writer.py` (Story-7 implementation reference).

**MCT-132 framework 답습 항목**:

- spec / plan / runbook / Grafana dashboard 답습 (Story-7 owner 의무, MCT-132 → MCT-135 Story-1 → MCT-XXX Story-7 line of reference).
- ndjson tail-reader + atomic tmp → rename + lineage manifest emit + replay trigger (orphan ingester 30min detection).

### §Archive failure → WAL extension

**Gap**: Compactor archive 실패 (Parquet write fail / atomic rename fail / disk full) 시 sealed WAL segment 의 보존 기간 연장 의무. 기존 ADR-017 §1 의 GC grace (24h) 가 archive 실패 longstanding 시 데이터 손실 위험.

**Policy**: archive 실패 detected 시 sealed WAL segment 의 GC grace 를 **24h → 7d 연장**. Compactor 가 sealed segment 의 `_archive_failed` sentinel file 박제 → GC daemon 이 sentinel 인식 시 grace extend. 7d 내 archive 성공 시 sentinel removal + GC 24h 복귀. 7d 도달 시 OperationalRiskArch alert (Story-7 §7.4 source).

### §Cross-references (transaction-tier amendment)

- ADR-009 §D10 (tick.v1 schema) + §D10.7 (fallback dedup key) + §D10.8 (tick.v1.1 minor extension) + §D12.2 (forward-only invariant)
- ADR-009 §D15 (Information bar contract — tick = Bronze SSOT 격하)
- ADR-009 §D16 (Provenance column)
- ADR-025 (Aggregation Core Lib Contract)
- ADR-026 (Legacy Candle Provenance & Retirement Policy)
- MCT-132 (Compactor Epic-A, LAND 2026-05-11) — framework + ParquetWriter + spec/plan/runbook/Grafana 답습 reference
- MCT-103 (50 sym universe LAND 2026-05-09) — symbol scope baseline
- MCT-112 (Epic) — Transaction SSOT & Information-Driven Bar Architecture
- MCT-135 (Story-1) — 본 amendment Story
- Spec: [transaction-ssot-information-bar-design.md](../superpowers/specs/2026-05-12-transaction-ssot-information-bar-design.md) §3 D4 (유실 차단 ADR-017 transaction-tier amendment) + §3 D6 (Compactor 재사용)

## §Amendment — Compactor Source 규약 (channel matrix SSOT) + multi-channel exchange 지원 (NEW, MCT-164, 2026-05-14)

본 amendment 는 ADR-017 의 L1/L2/L3 tiered compaction 패턴에 **multi-channel exchange** 지원 의무를 박제. MCT-165 V2 verify 잔존 YES (upbit L1 partition 0) trigger.

### Compactor Source 규약 (channel matrix SSOT)

L1 / L2 / L3 compactor 의 source channel 매핑 SSOT = `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` (MCT-164 발의). compactor 는 본 matrix 기반 dispatch 의무.

**규약** (MCT-164 §10 진단 결과 후 본문 갱신 의무):

| Tier | Source Channel (WAL) | Target Dataset | 변환 의무 |
|---|---|---|---|
| L1 | orderbookdepth | orderbookdepth | 1:1 |
| L1 | orderbooksnapshot | orderbookdepth | snapshot → depth 변환 의무 (MCT-164 AC-5 검증 대상) |
| L2 | orderbookdepth | orderbooksnapshot (per-hour) | aggregation |
| L3 | orderbooksnapshot | orderbooksnapshot (per-day) | aggregation |
| L1/L2/L3 | transaction | transaction | 1:1 |

### 적용 의무

1. **Source channel 인식**: compactor 는 source channel 명을 명시적으로 read 후 matrix dispatch. silent skip 금지 (ADR-027 Amendment 정합).
2. **Multi-channel exchange**: 같은 exchange 에서 다중 channel 가능 (예: bithumb = orderbookdepth, upbit = orderbooksnapshot). channel matrix 기반 dispatch.
3. **Snapshot → Depth 변환**: L1 source = orderbooksnapshot 시 compactor 가 변환 의무. 미구현 시 fail-fast + ADR-027 (MCT-164 sibling) 미지원 source silent-skip 차단 정합.

### 검증 의무

- MCT-164 진단 결과 (`docs/stories/MCT-164.md` §10) 가 본 규약과 정합 확인
- MCT-166 fix Story = 본 규약 위반 발견 시 fix scope 포함 의무 (INV-5 정합)
- Phase 2 회귀 test = 미지원 source 주입 시 fail-fast 검증

### Cross-ref

- ADR-027 (MCT-164 sibling) — 미지원 source silent-skip 차단
- channel matrix SSOT: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md`
- MCT-165 V2 (upbit L1 trigger source — verify-d5-2026-05-14.md §V2)
- MCT-164 (본 amendment 발의 Story)
- MCT-166 (fix Story, 본 규약 위반 fix 의무)

## §Amendment — Compactor sort key 규약 (content-derived, 파일명 untrusted) — Amendment 3 (NEW, mctrader-data#96, 2026-05-18)

본 amendment 는 L2/L3 compactor 의 input 파일 정렬 키를 **content-derived `ts_utc`** 로 박제한다. trigger = 운영 실측 2026-05-17 `promote-historical 2026-05-13/upbit/orderbooksnapshot` → 480 compact_hour calls 중 456 quarantine (`l2_compacted=0`), WS-A 117GB 회수 unblock 차단.

### 근본 원인

- L1 Parquet 파일명 `part-<sha[:16]>.parquet` 에 시간 정보 0 (`_derive_run_id = sha256(sealed_path)[:16]`, structural).
- `compact_hour` local fallback `sorted(l1_dir.rglob("part-*.parquet"))` = byte-order = sha-order ≠ time-order. 24h ≈ 48 segments interleave → `ts_utc` 단조 위반 → post-write monotonic verify quarantine (ADR-027 Amendment 1 MCT-160 D4).
- `_compact_hour_nas` `sorted(_list_objects(nas_prefix))` NAS key 동형 latent broken (이슈 A NAS 403 로 가려진 latent — 이슈 A LAND 즉시 forward 도 quarantine 시작 = ADR-009 §D12 forward-only invariant 위반).

### 결정

L2/L3 compactor input 파일 정렬 키 = **content-derived `ts_utc`** (`src/mctrader_data/compactor/sort_key.py` 단일 SSOT helper `_extract_min_ts`):

1. **Primary**: `pq.read_metadata(path).row_group(N).column(ts_utc_idx).statistics.min`. read I/O ≈ 0 (metadata footer만). multi-row-group 시 `min(rg.statistics.min for rg in row_groups)` 명시 집계. pyarrow `write_statistics=True` default + TIMESTAMP=INT64 storage = stats reliable (byte-comparator == logical-comparator).
2. **Fallback**: stats 부재/null 시 `next(pf.iter_batches(batch_size=1)).column("ts_utc")[0].as_py()`. L1 `compact_segment` step 5 `table.sort_by("ts_utc")` intra-file mono 명시 보장 활용 (first-row = file_min).
3. **0-row file**: skip + warning emit (quarantine 0).
4. **파일명 untrusted 원칙**: `sorted(files)` (byte-order) / mtime 기반 sort 금지. content-derived 만 신뢰.

### 적용 의무

- `src/mctrader_data/compactor/l2.py` — `compact_hour` local + `_compact_hour_nas` (NAS GET path) 양쪽 `_extract_min_ts` key.
- `src/mctrader_data/compactor/l3.py` — `compact_day` local + `_compact_day_nas` 동형 (현재 incidentally safe but uniform sort key API + hour-당-다중-L2 regression 차단).
- 신규 helper `_extract_min_ts` = 단일 SSOT (l2/l3 중복 sort 로직 금지).

### 검증 의무

- `mctrader-data#96` LAND 산출물 = unit (stats primary + fallback + 0-row + multi-rg + BytesIO) + testcontainers MinIO 통합 + `scripts/verify_l2_l3_sort_correctness.py` 운영 게이트.
- 운영 검증 (이슈 A LAND 후): `promote-historical --start 2026-05-13 --end 2026-05-13 --exchange upbit --channel orderbooksnapshot` → `{l2_compacted: ≥456, l3_compacted: 20, skipped_no_l1: ≤24, errors: 0}`.

### Cross-ref

- ADR-009 §D2 Amendment N (L1 dual filename pattern — sha-only legacy + ts-prefix new) sibling
- ADR-027 Amendment 1 (MCT-160 — post-write monotonic verify quarantine) downstream 정합
- ADR-027 Amendment 2 (MCT-164 — source channel silent-skip) sibling
- ADR-027 INCIDENT-2026-05-17 amendment (이슈 A NAS 403 — sequencing only, code dependency 0)
- `mctrader-data#96` (본 amendment 발의 + 구현 LAND Story)
- Spec: `mctrader-data/docs/superpowers/specs/2026-05-17-compactor-sort-key-l1-naming.md`
