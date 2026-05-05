---
adr_id: ADR-009
title: OHLCV 스키마 v1 — Canonical Parquet + 거래소 normalization + Candle Protocol + Lineage
status: Accepted
date: 2026-05-02
related_story: MCT-9
category: data
---

# ADR-009: OHLCV 스키마 v1 + 거래소 normalization + Candle Protocol contract

## Status

Accepted — 2026-05-02. MCT-9 Phase 1 PR.

**Amendment History**:
- 2026-05-04 — §D10 (Tick stream v1) + §D11 (Orderbook event stream v1) NEW. MCT-63 Epic Phase 1.
- 2026-05-05 — §D2.1 (Active-Active HA `node=` partition + dedup contract anchor) + §D10.7 (T2 tick logical key) + §D11.8 (T3 orderbook logical key) NEW. MCT-X1 Phase 1 (Collector HA active-active multi-node + shared storage).

## Context

mctrader-data canonical OHLCV. Baseline: ADR-002 D2 / ADR-003 H1 / ADR-005 path (c) / ADR-006 D10. mctrader-market 의 Candle Protocol contract 제공 (MCT-13 의존).

## Decision

### D1. v1 Canonical schema (16 columns)

| Column | Type |
|---|---:|
| schema_version | VARCHAR (`"ohlcv.v1"`) |
| exchange | VARCHAR (`bithumb`/`upbit`) |
| symbol | VARCHAR (`KRW-BTC`) |
| base_asset | VARCHAR |
| quote_asset | VARCHAR |
| timeframe | VARCHAR (`1m`/`5m`/`15m`/`1h`/`4h`/`1d`) |
| ts_utc | TIMESTAMP_MS |
| open | **DECIMAL(38,18)** |
| high | **DECIMAL(38,18)** |
| low | **DECIMAL(38,18)** |
| close | **DECIMAL(38,18)** |
| volume | **DECIMAL(38,18)** |
| value | **DECIMAL(38,18)** |
| source_ingested_at | TIMESTAMP_MS |
| data_snapshot_id | VARCHAR |
| data_hash | VARCHAR |

**Decimal(38,18) 채택**: KRW pair 가격 범위 + backtest 누적 정확도. float64 = query layer 명시 projection.

### D2. Hive partition layout

```
market/ohlcv/schema_version=ohlcv.v1/exchange=.../symbol=.../timeframe=.../year=.../month=.../date=.../*.parquet
```

**Physical partition = UTC date**. (KST daily 도 `ts_utc` 의 UTC date 로 저장.)

#### D2.1 Active-Active HA — `node=` partition level + dedup contract (NEW, MCT-X1 Phase 1, 2026-05-05 amendment)

Collector HA Epic (MCT-X1) 도입에 따라 모든 tier (`ohlcv.v1` / `tick.v1` / `orderbook.v1`) 의 partition path leaf 직전에 `node=` level 추가:

```
market/ohlcv/schema_version=ohlcv.v1/exchange=.../symbol=.../timeframe=.../
       year=.../month=.../date=.../node=NODE_A/
       {collector_run_id}-{batch_seq}.parquet
```

(`tick.v1` / `orderbook.v1` 도 §D10.2 / §D11.2 path 의 leaf 직전에 동일 `node=` level 추가)

- `node` = 호스트 식별자 (low cardinality, e.g., `NODE_A` / `NODE_B`)
- file name = `{collector_run_id}-{batch_seq}.parquet`
- DuckDB Hive partition pruning 으로 특정 node 의 데이터만 scan 가능 (lineage / debugging)
- 단일 node 운영 시 `node=DEFAULT` (또는 hostname) 적용 — backward compat (legacy single-host migration 무관)

**Active-Active dedup contract** (T1/T2/T3 공통, 본 amendment 의 anchor 절):

- read-side `scan_*` API (mctrader-data §D8 / §D11.3) 가 multi-node partition union + tier 별 logical key dedup
- conflict resolution 정책:
  - **node priority**: alphabetical / inventory 순 (deterministic). 다중 node 환경의 read-side sort 안정성 보장 용도.
  - **content mismatch handling**:
    - **T1 candle**: §D5 의 기존 late correction policy 와 align — append-only + serving view 가 최신 값 win. quarantine emit 하지 않음.
    - **T2 tick / T3 orderbook**: 신규 `active-active mismatch` quarantine reason emit. §D10.7 / §D11.8 의 logical key 정의 참조.
- Lineage: `_lineage.json` + parquet file metadata 에 `node_id` 추가 (MCT-65 manifest 와 1:1 align). 기존 §D6 candle lineage 와 §D10.3 / §D11.x 의 collector_run_id 매핑은 변경 없음.

**Bithumb Public WS schema 검증 결과** (MCT-X1 Phase 1, 2026-05-05): transaction stream 에 unique transaction id (cont_no/tx_id 등) **부재**, orderbook stream 에 sequence number / version field **부재**. 따라서 §D10.7 / §D11.8 의 logical key 는 **fallback tuple only** + best-effort dedup 정확도. unique id 가 향후 Bithumb API 측에서 제공되면 별도 minor amendment 로 primary key 채택 가능 (backward compat).

References:
- Spec: [collector-ha-active-active-design.md](../superpowers/specs/2026-05-05-collector-ha-active-active-design.md)
- Heartbeat contract: [heartbeat-schema.v1.md](../domain-knowledge/contracts/heartbeat-schema.v1.md)

### D3. 거래소 normalization

**Upbit** mapping:
- `market` → `symbol` (그대로)
- `opening_price/high_price/low_price/trade_price` → `open/high/low/close`
- `candle_acc_trade_volume/price` → `volume/value`

**Bithumb** mapping:
- `BTC_KRW` → `KRW-BTC` (방향 반전 + dash)
- Array response = 명시 mapping table only
- `value` 부재 = quarantine

### D4. Resampling

**1m canonical → higher TF 자체 재계산** (거래소 higher TF = 검증/fallback 만):
```
open=first / high=max / low=min / close=last / volume=sum / value=sum
```

Boundary:
- `1m/5m/15m/1h/4h` = UTC epoch
- `1d` = **KST 자정** (UTC midnight = 금지)

### D5. Missing / duplicate / out-of-order

- **Forward-fill = 금지** (canonical 에서). 결측 = row 미생성 + quality manifest gap.
- Halt: 필수 값 누락 / decimal parse 실패 / `value` 부재 + 재계산 불가
- Quarantine: 일부 row 실패 + payload 보존
- Skip: quarantine 후 나머지 진행
- `volume=0 + open=high=low=close` = 허용
- 음수 = reject
- Duplicate (`exchange, symbol, timeframe, ts_utc`): 동일 hash = idempotent / 다른 값 = late correction (append-only + serving view)
- Out-of-order = 허용 (정렬 + 검증)

### D6. Feature lineage metadata (ADR-005 path c)

별도 Parquet dataset:

```
feature_set / feature_version / exchange / symbol / timeframe / ts_utc /
source_start_ts / source_end_ts / computed_at_ts / available_from_ts /
data_snapshot_id / data_hash
```

`available_from_ts` = lookahead 방지 핵심. KST daily = KST close 이후.

### D7. Schema versioning

`ohlcv.v1`. Minor (추가) = compatible / Major (삭제 / 변경 / partition / `value` optional) = incompatible. v1 reader = unknown 컬럼 무시.

### D8. mctrader-market Candle Protocol

```python
@runtime_checkable
class Candle(Protocol):
    schema_version: Literal["ohlcv.v1"]
    exchange: str
    symbol: str
    timeframe: str
    ts_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    value: Decimal
    source_ingested_at: datetime
    data_snapshot_id: str
    data_hash: str
```

Reader: `scan_candles(exchange, symbol, timeframe, start_ts, end_ts, snapshot_id) -> Iterable[Candle]` — `ts_utc` ASC, end exclusive, forward-fill 금지.

### D9. Orderbook snapshot v1 — L3 depth-ladder (예약, 미구현)

```
schema_version=orderbook_snapshot.v1
exchange / symbol / ts_utc / sequence_id /
bid_prices / bid_sizes / ask_prices / ask_sizes / depth /
source_ingested_at / data_snapshot_id / data_hash
```

Lists = LIST<DECIMAL(38,18)>. Upbit `orderbook_units` ↔ 자연 매핑.

**§D9 = L3 depth-ladder 형식 reservation (ADR-004 D2 L3 future).** 미구현. §D11 (L2 event stream) 와 별개 schema. Bithumb public WS 는 L2 만 제공 → §D11 이 v1 구현분.

### D10. Tick stream v1 (NEW, MCT-63 Epic Phase 1, 2026-05-04 amendment)

forward-only T2 (tick) market data partition. mctrader-data PR #4 (commit 9f51fa0, MCT-65 retroactive seal) 가 구현 완료.

#### D10.1 Schema (8 column)

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[ns, UTC] | no | 거래소 발생 시각 (Bithumb WS event_time) |
| received_at | timestamp[ns, UTC] | no | collector server-side 도착 시각 (= **available_from_ts**) |
| exchange | string | no | "bithumb" v1 only |
| symbol | string | no | canonical "{quote}-{base}" (e.g. "KRW-BTC") |
| price | decimal128(38, 18) | no | trade price |
| quantity | decimal128(38, 18) | no | trade quantity |
| side | string | no | "buy" / "sell" |
| raw_json | string | yes | original WS frame (debug, optional) |

#### D10.2 Hive partition layout

```
market/ticks/schema_version=tick.v1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/part-{collector_run_id}.parquet
```

Physical partition = UTC date. KST daily 도 `ts_utc` 의 UTC date 로 저장 (§D2 동일 규칙).

#### D10.3 partition_id ↔ collector_run_id 매핑

`partition_id` (parquet filename suffix) ↔ `collector_run_id` (lineage source) **1:1 매핑** (v1). data_hash 부재 (forward-only stream = source 자체 — 거래소 WS 에 동일 stream 재요청 불가). lineage record 는 §D6 schema 와 다른 collector-specific schema 사용 (MCT-65 의 `collector_run_id` + `started_at_utc` + `selected_symbols` manifest).

#### D10.4 Forward-only invariant + lookahead 방어

**`available_from_ts := received_at`**. Backtest reader (MCT-66 `scan_ticks`) 는 caller 의 `simulated_clock` 주입 시 `received_at <= simulated_clock` event 만 yield. ADR-005 lookahead 방어 정합 (§D6 candle 의 `available_from_ts` 와 다른 mechanism — candle 은 feature lineage table 별도, tick 은 row 자체 column).

#### D10.5 결정적 sort key

`(ts_utc ASC, received_at ASC, file_offset ASC)`. 동일 ts_utc 다중 event = received_at 순 → file_offset 순. backtest 결정성 의무.

#### D10.6 Missing / duplicate / out-of-order

- Forward-fill = N/A (tick = 본질적으로 이벤트 시계열).
- Halt: schema mismatch / 음수 price / 음수 quantity / unknown side.
- Duplicate detection: 미적용 v1 (Bithumb WS = at-most-once 가정). 동일 (ts_utc, price, quantity, side) row = idempotent 통과.
- Out-of-order = 허용 (sort 시점에 정렬, MCT-66 enforcement).
- Gap detection (collector reconnect 등) = MCT-66 `tier_coverage` API 의 책임 (threshold = 5분 default).

#### D10.7 Active-Active HA dedup logical key (NEW, MCT-X1 Phase 1, 2026-05-05 amendment)

T2 tick stream 의 active-active multi-node dedup logical key — §D2.1 의 contract anchor 참조.

**Logical key (fallback tuple only)**: `(exchange, symbol, ts_utc, price, quantity, side)` 6-tuple.

**근거**: Bithumb public WS transaction stream 검증 결과 (2026-05-05) — `cont_no` / `tx_id` / `seq` 등 unique transaction identifier **부재** (`mctrader-market-bithumb` `ws_mapping.py` `TransactionEvent` 도 unique id field 없음). primary key 채택 불가 → fallback tuple 적용.

**dedup procedure** (read-side `scan_ticks` + dedup module 책임):

1. multi-node partition union scan (Hive `node=` partition pruning 후 모든 node 순회)
2. 동일 logical key tuple 발견 시 **node priority** (alphabetical / inventory 순) 적용
3. content (raw_json 제외 7-col schema 의 비-key field) 일치 → idempotent skip (기존 §D10.6 정책 유지)
4. content mismatch → **`active-active mismatch` quarantine** emit (signal: tier=tick / node_a / node_b / logical_key / diff_summary)

**Timestamp tolerance**: `ts_utc` 가 message 의 server-side `contDtm` (Bithumb 가 발급) 인 경우 양 node identical 기대. message timestamp 부재로 `received_at` fallback 으로 채워진 row 는 양 node divergence 가능 → **strict equality 가 아닌 ms-tolerance** (default ±100ms) 적용. 정확 tolerance threshold 는 MCT-X3 Phase 의 Calibration AC 에서 freeze.

**Dedup 정확도 목표**: > 99% (T2 tick = same Bithumb stream 이라 byte-identical 기대 매우 높음). MCT-X3 Calibration C2 측정 의무.

**raw_json column 정책**: `raw_json` (§D10.1 nullable, debug optional) 은 content 비교 제외 (양 node 의 WS frame 직렬화 형식 차이 가능). dedup 후 살아남은 row 의 `raw_json` 은 node priority 우선 row 의 값 채택.

### D11. Orderbook event stream v1 (NEW, MCT-63 Epic Phase 1, 2026-05-04 amendment)

forward-only T3 (orderbook) market data partition. **L2 event stream — §D9 L3 depth-ladder 와 별개 schema**. snapshot + delta event 가 동일 table 에 flat 으로 저장 (per-level row).

#### D11.1 Schema (10 column)

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[ns, UTC] | no | 거래소 발생 시각 |
| received_at | timestamp[ns, UTC] | no | collector server-side 도착 시각 (= **available_from_ts**) |
| exchange | string | no | "bithumb" v1 only |
| symbol | string | no | canonical |
| event_type | string | no | "snapshot" / "delta" |
| side | string | no | "bid" / "ask" |
| level | int32 | no | snapshot: 0..N-1 (top-of-book = 0) / delta: -1 |
| price | decimal128(38, 18) | no | level price |
| quantity | decimal128(38, 18) | no | level quantity (delta `0` = remove level) |
| raw_json | string | yes | original WS frame (optional) |

#### D11.2 Hive partition layout

```
market/orderbook/schema_version=orderbook.v1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/part-{collector_run_id}.parquet
```

#### D11.3 Reconstruction read API contract (MCT-66)

- **`scan_orderbook_events(symbol, start, end, *, snapshot_id=None) -> Iterable[OrderbookEventRecord]`** — half-open `[start, end)`, sort key §D11.5.
- **`get_orderbook_at(symbol, ts_utc) -> OrderbookSnapshot`** — start-of-day baseline (해당 일 첫 `event_type="snapshot"` event 다발) → fold delta forward → ts 시점 state.
- **`tier_coverage(symbol, "orderbook", start, end) -> CoverageReport`** — gap / `collector_run_ids` / symbol manifest 참조.

#### D11.4 Forward-only invariant + lookahead 방어

**`available_from_ts := received_at`**. §D10.4 동일 mechanism.

#### D11.5 결정적 sort key

`(ts_utc ASC, received_at ASC, file_offset ASC)`. §D10.5 동일.

#### D11.6 Fail-closed reconstruction error mode (MCT-66)

다음 cases halt + emit `GapDetectedEvent` / `ReconstructionError`:

- gap > threshold (collector reconnect 등) — default 5분
- non-monotonic ts (스트림 내 sort key 역순)
- duplicate event with different hash (동일 hash = idempotent skip)
- missing baseline (해당 일 첫 snapshot event 부재)
- schema mismatch

silent skip 거부 (research-grade reproducibility 우선).

#### D11.7 L2 vs L3 분리

§D9 (L3 depth-ladder snapshot, 예약 미구현) 와 본 §D11 (L2 event stream, v1 구현) 는 **별개 schema**. Bithumb public WS = L2 only → v1 = §D11. L3 가 필요한 strategy 는 §D9 미구현 = unsupported. 후속 Epic 에서 §D9 구현 시 L2 + L3 양립 가능.

#### D11.8 Active-Active HA dedup logical key (NEW, MCT-X1 Phase 1, 2026-05-05 amendment)

T3 orderbook event stream 의 active-active multi-node dedup logical key — §D2.1 의 contract anchor 참조.

**Logical key (fallback tuple only)**: `(exchange, symbol, ts_utc, event_type, side, level, price, quantity)` 8-tuple (delta event 의 경우 `level=-1` 고정).

**근거**: Bithumb public WS orderbook stream 검증 결과 (2026-05-05) — sequence number / version field **부재** (`orderbookdepth` channel + `mctrader-market-bithumb` `ws_mapping.py` `OrderbookDeltaEvent` / `OrderbookSnapshotEvent` 모두 sequence column 없음). primary key 채택 불가 → fallback tuple 적용.

**dedup procedure** (read-side `scan_orderbook_events` + dedup module 책임):

1. multi-node partition union scan (Hive `node=` partition pruning 후 모든 node 순회)
2. 동일 logical key tuple 발견 시 **node priority** (alphabetical / inventory 순) 적용
3. content (raw_json 제외 9-col schema 의 비-key field — 사실상 logical key 가 모든 비-raw_json field 를 포함) 일치 → idempotent skip (기존 §D11.6 동일 hash idempotent skip 정책의 logical-key 확장)
4. content mismatch → **`active-active mismatch` quarantine** emit (signal: tier=orderbook / node_a / node_b / logical_key / diff_summary)

**Best-effort dedup 명시**: T3 의 dedup 정확도 < 100% 가능. 다음 source 에서 divergence 발생:

- **Snapshot frame split**: Bithumb 가 한 snapshot 을 multiple frame 으로 split 하면 양 node 의 frame 분할 경계가 다를 수 있음 → row count 차이 (logical key 는 각 row 단위)
- **Reconnect 직후 baseline**: 양 node 의 reconnect 시점 다르면 reconnect 직후 첫 snapshot 의 timestamp 차이 발생
- **received_at fallback**: ts_utc 가 server-side timestamp 부재로 received_at 으로 채워진 경우 양 node divergence (mctrader-market-bithumb `ws_mapping.py:24-33` 참조)

**Dedup 정확도 목표**: > 95% (T2 보다 낮음, 위 divergence source 인정). 미달 시 root cause analysis. MCT-X3 Calibration C2 측정 의무.

**Timestamp tolerance**: §D10.7 동일 — server-side ts 인 row 는 strict equality, received_at fallback row 는 ms-tolerance (default ±100ms). 정확 threshold MCT-X3 freeze.

**raw_json column 정책**: §D10.7 동일 (node priority 우선 row 의 값 채택).

**§D11.6 Fail-closed reconstruction 와의 관계**: 기존 §D11.6 의 "duplicate event with different hash = halt" 정책은 active-active 도입 시 single-node 환경 (legacy 또는 `node=DEFAULT`) 에 한정 적용. multi-node 환경 (`node=NODE_A` + `node=NODE_B`) 에서는 본 §D11.8 의 logical key + quarantine 정책이 우선 — halt 가 아닌 quarantine + 진행.

## Alternatives Considered

### A1. float64 instead of Decimal(38,18)
- **기각**: backtest 누적 정확도 손실. Reproducibility 위험.

### A2. UTC midnight daily (KST 무시)
- **기각**: 거래소 UI / API 와 불일치. 한국 거래소 daily candle 의미 손상.

### A3. Forward-fill in canonical
- **기각**: lookahead bias 위험 (`available_from_ts` 잘못 잡힘).

### A4. 거래소 higher TF 그대로 사용
- **기각**: cross-exchange 일관성 손실. 1m 자체 재계산 우선.

### A5. Single schema for OHLCV + lineage
- **기각**: feature dataset 별도 schema. row 책임 분리.

### A6. Second resolution timestamp
- **기각**: 원천 ms 보존 손실. ms canonical.

## Consequences

### C1. mctrader-data 가 mctrader-market Candle Protocol 의 source
mctrader-market interface 는 본 ADR 의 contract 만 의존.

### C2. Backtest / Paper / Live 가 같은 OHLCV view
ADR-002 D2 invariant. mode 간 reproducibility 보장.

### C3. Decimal(38,18) = 저장 비용 + 정확도 trade-off
파일 크기 증가. 단 backtest 신뢰성 우선. 성능 query 는 명시적 DOUBLE projection.

### C4. KST daily boundary
한국 거래소 daily candle 의 UI / API 와 일치. UTC date partition 과 혼동 금지.

### C5. Schema version 변경 = ADR amend / supersede
v2 (major) = 본 ADR supersede.

### C6. MCT-13 (mctrader-market interface) 의존
Candle Protocol contract = MCT-13 구현의 input.

## Cross-references

- ADR-002 D2 / ADR-003 H1 / ADR-005 path (c) / ADR-006 D10
- ADR-004 D2 L3 — orderbook snapshot future activation
- MCT-13 (mctrader-market interface) — Candle Protocol 구현
