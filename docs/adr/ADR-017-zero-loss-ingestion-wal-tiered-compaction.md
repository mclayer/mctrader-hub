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
