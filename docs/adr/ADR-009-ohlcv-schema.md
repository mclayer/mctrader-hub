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
- 2026-05-08 — §D12 (Docker-first persistence: named volume `mctrader_data` + forward-only invariant + DR backup recipe) NEW. MCT-98 Phase 2 entry (mctrader Docker-first Migration Epic, Pilot reference 박제).
- 2026-05-09 — §D9 amendment (L3 reservation = future exchanges only, Bithumb KRW 한정 L2-30 only) + §D13 (`exchange_metadata.v1`) NEW + §D14 (`orderbook_snapshot.v1` L2 30-level snapshot stream + ordering invariant) NEW. MCT-104 Phase 1 (Bithumb 데이터 surface 전수 탐색 + P1 metadata + P2 orderbook snapshot 채택).
- 2026-05-09 — §D13/§D14 wiretap-based amendment (MCT-104 Phase 2 entry): §D13 의 tick_size / min_order_qty / fee_maker / fee_taker / min_order_notional_krw 모두 nullable (P2-F-003: public REST 미노출 검증) — Phase 2 = public-fillable subset only, private column 은 Live Epic 진입 시 채움. §D14 baseline_seq 모델 datetime-micro-epoch 으로 변경 (Bithumb 실측: 16-digit micro epoch string 노출, sequence number 부재 — P2-F-002/004). §D14.10 신설 = 1-sec subsample throttle (실측 push interval ≈200ms, ArchitectPL 30s 가정 대비 150x 차이, C1 storage 정책 재설계). §D13.7 rate-limit 135→150 r/s 정확화 (Codex P2-F-007).
- 2026-05-12 — **Major amendment** (MCT-135, Epic MCT-112 Story-1):
  - **§D10 amendment** — tick.v1 → tick.v1.1 minor extension: `ingest_seq` (uint64) + `payload_hash` (string) + `validation_status` (string) 3 column 추가. Bithumb WS transaction stream 의 sequence hole / content-mismatch / GAP 검출 의무화. fallback dedup key 확장 (§D10.7 reference, `ingest_seq` 추가로 6-tuple → 8-tuple).
  - **§D15 신설** — Information bar contract (`time_5m` / `vol_1000000krw` / `tick_1000` / `dollar_5000000krw` label format) + immutable contract metadata (genesis_ts / threshold / precision / rounding_rule / source_cutoff / tie_breaking / version / contract_id SHA256). **Candle = stored entity 에서 derived view 로 격하** (transaction tick = Bronze SSOT, candle = Silver derived). Aggregation Core Lib (ADR-025) reference.
  - **§D16 신설** — `provenance` column (`legacy_candle` cutoff 이전 immutable / `transaction_derived` cutoff 이후 derive). Legacy Candle Provenance & Retirement Policy (ADR-026) reference.
- 2026-05-13 — **§D11 amendment** (MCT-162, EPIC-compactor-operations Story-1) — §D11.9 신규 (`orderbook_depth.v1` flat row schema 박제). bithumb collector 의 `orderbookdepth` WS channel payload = delta `changes` event (per-frame N levels). MCT-156 deploy 후 L1Compactor `_schema_version` allowlist mismatch 로 48,629 sealed segment NotImplementedError 누적 (silent skip, Prometheus alert 0) 의 root cause schema 박제. §D11 (`orderbook.v1` L2 event stream) 의 per-level flat row 패턴 답습 + metadata column 4종 inject (`node_id` / `collector_run_id` / `ingest_seq` / `validation_status`) → tick.v1.1 / orderbook_snapshot.v1 동형 dedup logical key. raw_json column = **`large_string` (LargeUtf8)** 의무 (L2 `pa.concat_tables` i32 4 GB offset overflow 사례 박제). ADR-027 D4 amendment (channel parity 정책 + fail-fast invariant) 와 dual-binding.
- 2026-05-13 — **§D2.7 신규 (Schema nullability discipline)** (MCT-160, EPIC-compactor-operations Story-2). 3 schema (`_TRANSACTION_SCHEMA` + `_ORDERBOOKSNAPSHOT_SCHEMA` + `_ORDERBOOKDEPTH_SCHEMA`) 의 `pa.field(name, dtype, nullable=False/True)` 명시 의무 박제. `raw_json` 만 `nullable=True`, 나머지 essential column (`ts_utc` / `exchange` / `symbol` / `side` / `price` / `quantity`) 은 `nullable=False`. MCT-162 CodeReviewPL P1 finding (orderbookdepth schema nullable=False 명시 부재) 합병. InvariantHarness `dtype_identity` invariant 가 nullability 도 verify (ADR-027 §D6 정합). ADR-027 D4 amendment (MCT-160 silent-skip 차단 + post-write verify + quarantine) 와 sibling — Phase 1 ADR amendment 2건 박제.

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
- **Mixed legacy partition layout 지원 (영구)**: Read API (`scan_candles` / `scan_ticks` / `scan_orderbook_events`) 는 다음 두 layout 이 같은 root 안에 공존하는 mixed scan 을 지원해야 한다:
  - **Pre-HA partition** (`node=` level 없음, 본 amendment 도입 전 기존 mctrader-data 가 쓴 데이터) → reader 가 `node=DEFAULT` 로 취급하고 partition pruning 적용
  - **Post-HA partition** (`node=NODE_A` / `node=NODE_B` 등 explicit) → 그대로 read
  - caller 변경 0 (engine / web / WFO 측 transparent — 기존 scan API signature 유지)
  - 영구 지원 (Sonnet decider 결정 — legacy partition 폐기는 별도 migration Epic 의 scope)

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

### D9. Orderbook depth-ladder v1 — L3 reservation (예약, 미구현, future exchanges only)

```
schema_version=orderbook_depth_ladder.v1
exchange / symbol / ts_utc / sequence_id /
bid_prices / bid_sizes / ask_prices / ask_sizes / depth /
source_ingested_at / data_snapshot_id / data_hash
```

Lists = LIST<DECIMAL(38,18)>. Upbit `orderbook_units` ↔ 자연 매핑.

**§D9 = L3 depth-ladder 형식 reservation (ADR-004 D2 L3 future).** 미구현. §D11 (L2 event stream) 와 별개 schema.

#### D9 Amendment (NEW, MCT-104 Phase 1, 2026-05-09)

**§D9 reservation scope = L3 depth-ladder 를 노출하는 future exchange 대상 only**. Bithumb KRW 스팟 public WS 는 **L2 30-level only** (`orderbookdepth` channel 의 delta event + `orderbooksnapshot` channel 의 30-level full snapshot push) — Bithumb KRW 한정으로는 §D9 활성화 대상 **아님**. Bithumb 운용은:

- L2 event stream (delta) → §D11 (`orderbook.v1`)
- L2 30-level snapshot stream → **§D14 (`orderbook_snapshot.v1`)** (NEW, MCT-104 Phase 1)

§D9 의 schema_version (`orderbook_depth_ladder.v1`) 은 §D14 의 schema_version (`orderbook_snapshot.v1`) 과 **별개 namespace**. 향후 L3 노출 거래소 도입 시 §D9 활성화 + §D14 와 양립. naming collision 회피 위해 §D9 의 schema_version label 을 명시적으로 `orderbook_depth_ladder.v1` 로 박제 (기존 `orderbook_snapshot.v1` 라벨은 §D14 가 점유).

본 amendment 는 Bithumb KRW 노출 사실 (L2 30-level only) 을 §D9 reservation 의 dormant 상태와 분리하기 위한 명시화 작업. Bithumb KRW 가 L3 미노출 → §D9 활성화 trigger 에 해당 안 함. 후속 거래소 도입 시 본 절 amendment 로 활성화.

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

#### D10.8 tick.v1 → tick.v1.1 minor extension (NEW, MCT-135, Epic MCT-112 Story-1, 2026-05-12 amendment)

Transaction SSOT & Information-Driven Bar Architecture (Epic MCT-112) 의 foundation. tick = Bronze SSOT, candle = Silver derived view (§D15 격하) 로 의미가 변경됨에 따라 tick stream 의 record-level invariants 강화 의무. ADR-009 §D7 (Schema versioning) 의 minor 정의 (추가 column = compatible) 정합 — v1 reader 는 v1.1 의 신규 column 무시하면 그대로 동작 (backward compat).

**추가 column (3)**:

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ingest_seq | uint64 | no | collector 측 monotonic 발급 sequence. dedup + 결정론적 replay key. process restart 시 reset 허용 (collector_run_id 와 결합 시 monotonic). |
| payload_hash | string | no | raw WS frame SHA256 16-hex prefix. content-mismatch 검출 + active-active dedup tie-breaker. raw_json 보존 여부와 무관 — frame 도착 시점에 계산. |
| validation_status | string | no | `"OK"` / `"GAP"` / `"MALFORMED"` / `"RECONNECT_BOUNDARY"`. Bithumb WS reconnect 시 sequence hole 검출 + 박제 의무. |

**Rationale (3 column 별)**:

- **`ingest_seq`** — Bithumb WS transaction stream 의 unique trade_id 부재 (§D2.1 / §D10.7 anchor) 가정 하에 collector 측 monotonic seq 발급으로 결정론적 ordering 확보. process restart 후 reset 발생하지만 `collector_run_id` 와 결합 시 (run_id, ingest_seq) tuple 이 monotonic — backtest replay 결정성 확보.
- **`payload_hash`** — content-based dedup + active-active mismatch 검출. ADR-017 §Transaction-tier WAL (amendment 2026-05-12) 의 fsync window 내 process crash 후 재시작 시 in-flight WAL buffer 의 일부 row 가 다음 sealed segment 에 재기록되는 경우 content equality 로 자연 dedup. raw_json column 이 nullable (debug optional) 인 환경에서도 hash 는 항상 기록.
- **`validation_status`** — Bithumb WS forward-only invariant (D12.2) 위반 사건 (gap / malformed / reconnect boundary) 의 row-level 박제 의무. `GAP` 박제 = backfill 불가 명시화. `MALFORMED` = schema mismatch 후 quarantine (§D10.6 정책 답습 + row-level visibility). `RECONNECT_BOUNDARY` = collector 측 reconnect 직후 첫 frame, dedup 의 ms-tolerance 적용 대상 marker.

**Fallback dedup key 확장**:

§D10.7 의 fallback tuple `(exchange, symbol, ts_utc, price, quantity, side)` 6-tuple 에 `ingest_seq` + `payload_hash` 추가:

- **Logical key (확장)**: `(exchange, symbol, ts_utc, price, quantity, side, raw_json_hash, ingest_seq)` — 단, `raw_json_hash` 는 v1.1 의 `payload_hash` 와 의미 일치 (`raw_json` 의 SHA256 이지만 v1.1 부터는 payload 직접 hash 도 동치, raw_json nullable 시 payload 직접 hash 채택)
- **Tie-breaking**: `payload_hash` 일치 → idempotent skip. mismatch → `active-active mismatch` quarantine (§D10.7 정책 유지) + `validation_status` 변경 (`OK` → `MALFORMED`) 박제.

**Hive partition layout — 변경 없음**: §D10.2 그대로 (`market/ticks/schema_version=tick.v1/...`). schema_version label = `tick.v1` (minor `tick.v1.1` 은 column 추가만 — partition label 변경 트리거 아님, §D7 minor compatibility 규칙). 단 reader 가 신규 3 column 의 존재 여부로 `tick.v1` vs `tick.v1.1` 자연 분기.

**Backward compat**:

- 기존 `tick.v1` Parquet (legacy, 신규 3 column 부재) → v1.1 reader 는 신규 column 을 `validation_status=NULL` / `payload_hash=NULL` / `ingest_seq=NULL` 로 보거나, `validation_status="OK"` default 적용 (caller 정책). Story-4 (mctrader-market-bithumb transaction WS subscriber 강화) 가 신규 row 부터 3 column 의무 채움.
- 신규 row 부터 3 column non-null write 의무 (Story-4 implementation seal). legacy row 는 ADR-026 §D1 legacy candle 자산 정책 (immutable 유지) 동형 — `tick.v1` legacy partition 도 immutable 유지 + dual-namespace operation 가능.

References:
- Spec: [transaction-ssot-information-bar-design.md](../superpowers/specs/2026-05-12-transaction-ssot-information-bar-design.md) §3 D8 (tick.v1 schema 확장)
- §D15 (Information bar contract) — tick 이 bronze SSOT 임을 박제하는 동위 amendment
- §D16 (Provenance column) — legacy_candle vs transaction_derived 의 row-level provenance
- ADR-017 §Transaction-tier WAL (amendment 2026-05-12) — at-least-once + batch fsync + WAL buffer policy
- ADR-025 (Aggregation Core Lib Contract) — tick.v1.1 row 를 입력으로 받는 bar aggregation algorithm SSOT
- ADR-026 (Legacy Candle Provenance & Retirement Policy) — cutoff timestamp 후 retirement 의 prerequisite

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

#### D11.9 `orderbook_depth.v1` schema (NEW, MCT-162 Phase 1, 2026-05-13 amendment)

bithumb collector 의 **`orderbookdepth` WS channel** payload = **delta `changes` event** (frame 당 N levels, qty=0 = level delete). transaction (flat trade row) + `orderbook_snapshot.v1` (per-level full snapshot row) 와 schema mismatch → 별 `schema_version` namespace 박제 의무.

**Amendment trigger**: MCT-156 (EPIC-cold-tier-stage-3-wiring) production deploy 후 L1Compactor `_schema_version` allowlist 가 `("transaction", "orderbooksnapshot")` 만 supported → bithumb `orderbookdepth` sealed segment 가 `NotImplementedError` 100% throw → **48,629 sealed silent backlog 누적** (Prometheus alert 0, operator 인지 0). RETRO-MCT-156 §13.4 cross-ref.

##### D11.9.1 WAL payload sample (CodebaseMapperAgent fetch, 2026-05-13)

bithumb collector emit NDJSON (3 line sample, ingester `bithumb-ingester` runtime):

```json
{
  "ts_utc": "2026-05-10T17:55:02.849786+00:00",
  "received_at": "2026-05-10T17:55:00.171083+00:00",
  "exchange": "bithumb",
  "symbol": "KRW-NIL",
  "changes": [
    {"side": "ask", "price": "90.790000000000000000", "quantity": "28701.748000000000000000"},
    {"side": "bid", "price": "89.200000000000000000", "quantity": "5483.600000000000000000"}
  ],
  "raw_json": "<original WS frame>",
  "channel": "orderbookdepth"
}
```

`changes` = per-frame N levels (1 sample = 2 levels 관측, 가변). `qty=0.0` = level delete (orderbook book maintenance semantic). collector top-level metadata (`node_id` / `collector_run_id` / `ingest_seq` / `validation_status`) = WAL payload 부재 — L1Compactor segment metadata 에서 inject (transaction.v1.1 / orderbook_snapshot.v1 동일 패턴, §D2.1 정합).

##### D11.9.2 Schema (per-level flat row, 11 column — `orderbook.v1` per-level row pattern 답습)

`schema_version` 은 partition path (`schema_version=orderbook_depth.v1`) 에 박제 — column 화 안 함 (§D10.1 / §D11.1 / §D14.1 동형). row column **11**:

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[us, UTC] | no | event timestamp (WAL frame `ts_utc`) |
| received_at | timestamp[us, UTC] | no | collector server-side 도착 시각 (= **available_from_ts**, §D11.4 동형) |
| exchange | string | no | `"bithumb"` v1 only |
| symbol | string | no | canonical (`"KRW-NIL"` 형식) |
| side | string | no | `"bid"` / `"ask"` (frame `changes[].side` flatten) |
| price | decimal128(38, 18) | no | level price (frame `changes[].price` cast) |
| quantity | decimal128(38, 18) | no | level quantity (`0` = remove level, book maintenance) |
| raw_json | **large_string (LargeUtf8)** | yes | original WS frame (per row 반복 — `changes` flatten 시 N rows share 동일 raw_json). **LargeUtf8 의무** (§D11.9.6 박제) |
| node_id | string | no | L1Compactor inject (segment metadata, §D2.1 정합) |
| collector_run_id | string | no | L1Compactor inject (run identifier, lineage anchor) |
| ingest_seq | int64 | no | L1Compactor inject (monotonic seq, §D10 tick.v1.1 동형 GAP 검출 anchor) |

**Flat 변환 규칙**: WAL frame 1개 (N levels) → parquet **N rows** (per-level flatten). row count = `Σ len(frame.changes)` (across all frames in segment). transaction (1 frame → 1 row) / orderbook_snapshot.v1 (1 frame → N=60 rows, fixed) 와 다른 fan-out 비율.

##### D11.9.3 Hive partition layout (§D2.1 HA `node=` 적용)

```
market/orderbookdepth/schema_version=orderbook_depth.v1/tier=L1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/node={node_id}/part-{collector_run_id}.parquet
```

- partition root = `market/orderbookdepth/` (별 partition root, `market/orderbook/` § D11 본문 / `market/orderbook_snapshot/` §D14 와 분리)
- `tier=L1` = ADR-027 D4 amendment (channel parity) 정합 — L1 hot path (compactor local write only, L1 NAS upload 0 invariant, ADR-027 §D5)
- L2 partition layout = MCT-160 Phase 1 author scope (본 amendment 외 — Story-2 의 L2 cadence + offset overflow fix scope)

##### D11.9.4 Forward-only invariant + lookahead 방어

**`available_from_ts := received_at`** — §D11.4 동형 mechanism. `event_time` (`ts_utc`) 사용 금지 — bithumb 측 server clock skew 가능 (§D14.3 wiretap-validated baseline_seq 미존재, orderbookdepth = collector-side receive ordering 의존).

**Forward-only stream**: `orderbookdepth` = collector restart 시 baseline reset 가능 (upbit ingester WAL sample `ls /var/lib/mctrader/data/wal/upbit/` 실측 = `orderbooksnapshot` / `transaction` only, **`orderbookdepth` 0** → upbit emit 없음. bithumb 만 emit). reconnect 경계 frame = `validation_status='RECONNECT_BOUNDARY'` (Phase 2 implementation scope, optional).

##### D11.9.5 결정적 sort key + dedup logical key

**Sort key (per parquet file)**: `(ts_utc ASC, received_at ASC, ingest_seq ASC, side ASC, price ASC)` — §D11.5 의 `file_offset` 자리에 `ingest_seq` 채택 (tick.v1.1 동형, sequence number primary).

**Dedup logical key (§D2.1 active-active HA contract anchor)**: `(exchange, symbol, ts_utc, ingest_seq, node_id, side, price, quantity)` 8-tuple — orderbook_snapshot.v1 (§D14.6) + tick.v1.1 (§D10.7) 와 동형 fallback tuple.

- **multi-node node priority**: alphabetical (deterministic read-side sort).
- **content mismatch**: §D11.8 동형 `active-active mismatch` quarantine emit. silent skip 금지.
- **best-effort dedup 명시**: bithumb `orderbookdepth` WS = sequence number 부재 (collector 측 `ingest_seq` = collector-side monotonic, 양 node 동시 receive frame 의 sequence 정렬 일치 보장 0). 정확도 목표 > 95% (§D11.8 동형 — broadcast source 동일 하나 split 가능).

##### D11.9.6 `raw_json` column = `large_string` (LargeUtf8) 의무

**Critical constraint** (Refactor + DataMigration deputy 통합 박제):

- pyarrow `string` (Utf8) = **i32 offset array** → 1 chunk 4 GB cap. L2 compaction 의 `pa.concat_tables` 호출 시 N 시간 분 segment concat → raw_json column 누적 size 가 i32 offset overflow 도달 가능 → `OOM exit 137` 또는 `ArrowInvalid: offset overflow` raise (MCT-156 production deploy 사례, RETRO-MCT-156 §13.5.3 박제).
- `large_string` (LargeUtf8) = **i64 offset array** → 8 EB cap (실질 무제한). MCT-160 Phase 1 의 streaming `ParquetWriter.write_table` per-file loop (D3) 와 결합 시 단일 buffer 누적 0 보장.

**L1Compactor 의무**:
1. WAL NDJSON → pyarrow Table 변환 시 `raw_json` column dtype = `pa.large_string()` cast 의무 (default `pa.string()` 금지)
2. integration test 의무 (Phase 2 §8 Test-5) — 생성된 parquet 의 `raw_json` field type = `large_string` 검증

**Backward-compat**: 기존 `orderbook.v1` (§D11.1) / `orderbook_snapshot.v1` (§D14.1) 의 `raw_json` column type = `string` → L2 compaction OOM 시점에 별 amendment (MCT-160 scope or 후속 Story) 로 일괄 `large_string` 전환 가능. 본 amendment = 신규 `orderbook_depth.v1` 한정으로 `large_string` 박제 (volume × per-frame raw_json N-fan-out → fastest path to overflow).

##### D11.9.7 Fail-closed channel parity invariant (ADR-027 D4 cross-binding)

L1Compactor 의 channel allowlist = ADR-027 D4 amendment (MCT-162 2026-05-13 박제) 의 **fail-fast invariant** 정합:

- `orderbookdepth` 채널 = `_CHANNEL_SCHEMA_VERSION` 매핑 추가 (`"orderbookdepth" → "orderbook_depth.v1"`)
- unsupported channel = `NotImplementedError` raise + Prometheus counter `compactor_unsupported_channel_total{channel}` Counter +1 (silent skip 금지)
- silent skip 차단 invariant = ADR-027 D4 amendment 본문 (MCT-162) 참조

##### D11.9.8 Active-Active HA dedup contract (§D2.1 anchor 정합)

§D2.1 / §D10.7 / §D11.8 / §D14.6 와 동형 — 본 §D11.9.5 의 8-tuple logical key 가 active-active multi-node dedup 의 primary contract. Phase 2 L1 compaction 후 L2/L3 layer 에서 InvariantHarness (ADR-027 §D6) `column_count`/`column_name_order`/`dtype_identity`/`schema_version_pin` 4종 schema invariant 자동 verify — channel-aware (ADR-027 §D6 FIX Iter 1 amendment 정합).

##### D11.9.9 Read API contract (MCT-66 후속 Story scope)

`scan_orderbook_depth(symbol, start, end) -> Iterable[OrderbookDepthRecord]` 신규 read API = **MCT-66 후속 Story scope** (본 amendment 외, forward-only invariant L1 partition 박제만이 본 Phase 1 scope). reconstruction (`get_orderbook_at`) 의 baseline source 확장 = §D14 (`orderbook_snapshot.v1`) primary, §D11.9 = optional delta supplement (별 Story design).

##### D11.9.10 Out-of-scope (본 amendment 한계)

- **upbit `orderbookdepth` channel** = bithumb collector 만 emit (upbit WAL sample 실측 = `orderbooksnapshot` / `transaction` only, **`orderbookdepth` 0**). upbit L1 partition 0 별 root cause = **MCT-160 또는 별 Story 진단 의무** — orderbookdepth allowlist 와 무관 (Story §6 D9 운영 risk 박제 cross-ref).
- **L2/L3 compaction cadence + offset overflow fix** = MCT-160 Phase 1 author scope (D2 + D3 + R-EXTRA).
- **MCT-153 backfill 산출물 4.2 GiB / 1370 obj 손실 재발 방지** = MCT-161 scope (bucket versioning).

### D12. Docker-first persistence (Amendment 2026-05-08, MCT-98 Phase 2 entry)

mctrader-data Pilot (MCT-99, 2026-05-07 merged) 의 Docker-first 전환 박제 패턴. 5 sister rollout (mctrader-engine / -web — deployable trio) 의 reference.

#### D12.1 Named volume `mctrader_data` 영속화

mctrader-data collector daemon 의 OHLCV / tick / orderbook 데이터는 Docker named volume 에 보관:

| 항목 | 값 |
|---|---|
| volume name | `mctrader_data` |
| container mount | `/var/lib/mctrader/data` |
| env | `MCTRADER_DATA_ROOT=/var/lib/mctrader/data` |
| compose driver | local (default, compose.yml 미명시) |

codeforge ADR-033 §결정 6 (named volume 권장) 정합. host bind mount 거절 — Windows host path mapping 비호환 + production Linux host 와 dev Windows host 의 volume 패턴 통일.

#### D12.2 Forward-only invariant 명시

Bithumb public API 는 ticks/orderbook 의 historical replay 를 제공하지 않음. mctrader-data collector 는 forward-only:

- restart 시 데이터 누락 회피 → compose `restart: unless-stopped`
- container kill / volume detach 동안의 데이터 = 영구 손실
- backfill = candle (OHLCV) 만 가능, ticks/orderbook 은 backfill 없음
- HA active-active partition (§D2.1) 가 single-node 데이터 누락 회피의 일부 — node 별 forward-only 보장 + scan-side merge

본 invariant 는 collector lifecycle 의 hard constraint. 5 sister rollout 시 동일 패턴 적용.

#### D12.3 DR backup recipe (volume snapshot)

표준 backup 명령 (PowerShell, mctrader-data Pilot reference):

```powershell
# Backup
$timestamp = Get-Date -Format yyyyMMdd_HHmmss
docker run --rm `
  -v mctrader_data:/source:ro `
  -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_data_${timestamp}.tar.gz -C /source .

# Restore
docker run --rm `
  -v mctrader_data:/dest `
  -v ${PWD}:/backup `
  alpine tar xzf /backup/mctrader_data_<TIMESTAMP>.tar.gz -C /dest
```

bash 등가 명령:

```bash
# Backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker run --rm \
  -v mctrader_data:/source:ro \
  -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_data_${TIMESTAMP}.tar.gz -C /source .

# Restore
docker run --rm \
  -v mctrader_data:/dest \
  -v "$(pwd):/backup" \
  alpine tar xzf /backup/mctrader_data_<TIMESTAMP>.tar.gz -C /dest
```

5 sister rollout (deployable trio: data, engine, web) 의 volume backup 표준 reference.

#### D12.4 후속 자동화 (별도 Story)

- volume backup cron / scheduled snapshot 자동화 — Phase 6 또는 별도 ops Story (Pilot F5/O4 carry-over)
- ghcr.io publish 후 image-ref + volume data lineage tracking — Pilot F1-F3 carry-over
- multi-host volume replication (production scale-out 시점) — TBD

#### D12.5 의무

본 §D12 의 invariant + recipe 는 5 sister rollout 시점에 deployable repo (data, engine, web) 가 reference 의무. library quartet (market, bithumb, hub) 는 `infra_strategy: none` 으로 본 §D12 미적용.

### D13. Exchange metadata v1 (NEW, MCT-104 Phase 1, 2026-05-09)

거래소 capability snapshot 의 forward-only partitioned record. ADR-002 H5 `ExchangeCapabilities` frozen dataclass 의 first implementation source. mctrader-data collector daemon 이 daily cadence 로 Bithumb public REST `/public/ticker/ALL_KRW` (symbol list + asset_status proxy) + 코드화된 Bithumb price-band lookup table (tick_size) + 공식 fee schedule (fee_maker / fee_taker 정율) 결합 후 snapshot 적재.

#### D13.1 Schema (14 column)

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| schema_version | string | no | `"exchange_metadata.v1"` |
| exchange | string | no | `"bithumb"` v1 only |
| symbol | string | no | canonical `"{quote}-{base}"` (e.g. `"KRW-BTC"`) |
| base_asset | string | no | canonical (e.g. `"BTC"`) |
| quote_asset | string | no | canonical (e.g. `"KRW"`) |
| tick_size | decimal128(38, 18) | **yes** (Phase 2 nullable) | 가격 단위. Bithumb public REST 미노출 (P2-F-003) → Phase 2 = NULL. Live Epic 진입 시 hand-coded price-band lookup 또는 private endpoint 로 채움. |
| min_order_qty | decimal128(38, 18) | **yes** (Phase 2 nullable) | 최소 주문 수량. Bithumb public REST 미노출 → Phase 2 = NULL. Live Epic 진입 시 채움. |
| min_order_notional_krw | decimal128(38, 18) | yes | 최소 주문 KRW 명목 (Bithumb KRW 스팟 = `5000` 정율, future exchange = nullable). Phase 2 = NULL (public REST 미노출), Live Epic 진입 시 hand-code. |
| fee_maker | decimal128(38, 18) | **yes** (Phase 2 nullable) | maker 수수료율. Bithumb public REST 미노출, private `/info/order_chance` (인증 의무) → Phase 2 = NULL. Live Epic 진입 시 채움. |
| fee_taker | decimal128(38, 18) | **yes** (Phase 2 nullable) | taker 수수료율. Phase 2 = NULL. Live Epic 진입 시 채움. |
| asset_status | string | no | `"active"` / `"deposit_only"` / `"withdraw_only"` / `"halted"` (Bithumb `/public/assetsstatus` 응답 normalize). Phase 2 fillable. |
| fetched_at | timestamp[ns, UTC] | no | collector REST 호출 응답 도착 시각 (= **available_from_ts**, ADR-005 path c) |
| source_snapshot_id | string | no | logical key 의 일부 — collector 가 daily refresh 시 발급한 deterministic id (e.g. SHA256(`exchange|fetched_date|collector_run_id`)[:16]) |
| data_hash | string | no | (exchange + symbol + tick_size + min_order_qty + fee_maker + fee_taker + asset_status) tuple 의 SHA256. 동일 hash = idempotent skip + dedup. |

근거:
- `tick_size` / `min_order_qty` / `fee_maker` / `fee_taker` = ADR-002 H5 `ExchangeCapabilities` 의 4 hard requirement. **Phase 2 = NULL** (P2-F-003 wiretap 검증: Bithumb public REST 미노출). Live Epic 진입 시 (a) hand-coded price-band lookup table (`tick_size` / `min_order_qty` / `min_order_notional_krw`) + (b) private `/info/order_chance` (인증 의무, fee) 로 채움. **§D13.10 Public-fillable subset 절** 참조.
- `asset_status` = Live executor 의 H9 data freshness gate + asset halt 시 order block source. **Phase 2 fillable** (Bithumb `/public/assetsstatus/ALL` public REST 노출).
- `min_order_notional_krw` = Bithumb KRW 스팟 의 `5000 KRW` 명목 minimum (Bithumb 공식 공지). Phase 2 = NULL, Live Epic hand-code.
- `data_hash` = §D13.5 logical key 와 별도 — content-based dedup 보강 (capability 가 변경 안 된 day 의 idempotent skip). **Phase 2 의 NULL column 은 hash 입력에서 제외** (NULL → hash skip, 비-NULL 만 hash → Phase 2 vs Live Epic 진입 시점 동일 row content 의 hash 충돌 회피).

#### D13.2 Hive partition layout

```
market/exchange_metadata/schema_version=exchange_metadata.v1/exchange={ex}/
       fetched_date={YYYY-MM-DD}/node={node_id}/
       part-{collector_run_id}.parquet
```

Physical partition = UTC date of `fetched_at` (`fetched_date`). §D2 ohlcv 의 year/month/date 계층보다 단순 — metadata 의 cardinality (50 sym × 365 day) 가 낮아 단일 `fetched_date` partition 으로 충분.

§D2.1 HA = `node=` partition 적용. mixed legacy partition (pre-HA) 지원은 본 partition 신규 도입이라 N/A — 모든 row 가 `node=NODE_A` 또는 `node=NODE_B` 또는 `node=DEFAULT` (단일 node).

#### D13.3 Forward-only invariant + lookahead 방어

**`available_from_ts := fetched_at`**. ADR-005 path c. Backtest reader (`scan_exchange_metadata`) 는 caller 의 `simulated_clock` 주입 시 `fetched_at <= simulated_clock` row 만 yield + 가장 가까운 row 선택 (lookback semantics). `fetched_at > simulated_clock` row 노출 = lookahead violation → reject + halt (D11.6 동형).

#### D13.4 Refresh cadence + scheduling

- Default cadence: **1 day** (Bithumb capability 변경 빈도 낮음). 
- Schedule: 매 UTC 0시 + 1분 grace (collector daemon scheduler 가 `next_fetch_at = ceil_to_utc_midnight(now()) + 1min` 계산).
- Rate-limit budget (§D13.7 별도 절) 준수 의무.
- 변경 detection: 적재 직전 직전 day 의 `data_hash` 와 비교 — 동일 시 idempotent skip (row 미생성, 단 manifest 에 "skipped" 기록). 다른 시 신규 row append.

#### D13.5 Active-Active HA dedup logical key

T2/T3 와 다른 cardinality (low frequency, daily snapshot) — logical key:

**Logical key**: `(exchange, symbol, fetched_date, source_snapshot_id)` 4-tuple.

**dedup procedure** (read-side `scan_exchange_metadata` 책임):

1. multi-node partition union scan
2. 동일 logical key tuple 발견 시 **node priority** (alphabetical) — §D2.1 동형
3. content (data_hash 비교) 일치 → idempotent skip
4. content mismatch → **`active-active mismatch` quarantine** emit (signal: tier=metadata / node_a / node_b / logical_key / data_hash_diff)

**Dedup 정확도 목표**: > 99% (양 node 가 같은 day 에 같은 REST endpoint 호출 → 양 node identical 기대 매우 높음). 미달 시 root cause = REST upstream change mid-day 또는 fetched_at clock skew (host clock drift).

**Timestamp tolerance**: `fetched_at` 은 collector 측 도착 시각 → 양 node divergence 가능 (ms-tolerance ±60s 적용 — daily cadence 라 수십초 drift 수용). `fetched_date` partition key 는 strict equality.

#### D13.6 Read API contract

```python
def scan_exchange_metadata(
    exchange: str,
    symbol: str,
    ts_utc: datetime,
    *,
    snapshot_id: str | None = None,
) -> ExchangeMetadataRecord:
    """가장 가까운 fetched_at <= ts_utc 의 row 반환 (lookback semantics).

    Lookahead 방어: fetched_at > ts_utc row 노출 금지.
    """
```

ADR-002 H5 `ExchangeCapabilities` frozen dataclass 매핑:
- `fee_maker` / `fee_taker` → `Capabilities.fee` (maker/taker 분리)
- `tick_size` → `Capabilities.tick`
- `min_order_qty` → `Capabilities.min_order_size`
- `min_order_notional_krw` → `Capabilities.min_order_notional`
- `asset_status` → ADR-002 H9 data freshness gate 의 입력 (halt = order reject)

#### D13.7 Rate-limit + backoff + halt 정책 (Calibration C2)

- Bithumb public REST rate-limit: **150 req/sec** (Bithumb v2.1 공식 — https://apidocs.bithumb.com/v2.1.0/docs/api-요청-수-제한-안내). collector daemon 의 daily cadence + 50 sym 가정 시 **2 req/day** (`/public/ticker/ALL_KRW` + `/public/assetsstatus/ALL`) **× 1 endpoint = budget overhead 무시 가능**.
- Endpoint 호출 실패 시 exponential backoff (initial 1s, doubling, max 5min, retry budget 5회). 5회 실패 = halt + emit `MetadataFetchHaltEvent`.
- 직전 day metadata 가 살아있으면 stale-but-acceptable (ADR-005 path c — `available_from_ts` 가 lookahead 방어). collector daemon 은 retry budget 소진 후에도 halt 안 함 — 다음 day cadence 재시도 + alert. 단 14일 이상 fetch 실패 시 `MetadataStaleHaltEvent` (Live executor consumer 측 capability gate 가 halt trigger).

#### D13.8 Lineage + manifest

- `_lineage.json` per partition (§D6 candle 동형) — endpoint URL + request_params_hash + fetched_at_utc + response_hash + adapter_version.
- `CollectorManifest` (MCT-65 schema) 에 "skipped daily refresh" 기록 의무 — idempotent skip 도 manifest 에 row 1 (`event_type="skipped"`).

#### D13.9 Out-of-scope

- Private REST `/info/account` 등 (KRW 스팟 인증 의무 + Live Epic).
- `tick_size` 의 dynamic refresh (Bithumb price-band lookup 변경) — Live Epic 진입 시 코드화된 lookup table 채택. Bithumb 공식 변경 발표 시 hand-amend.
- Multi-exchange — Bithumb only v1.

#### D13.10 Public-fillable subset (MCT-104 Phase 2 = NEW, 2026-05-09)

P2-F-003 wiretap 검증 결과 — Bithumb public REST 미노출 column (tick_size / min_order_qty / fee_maker / fee_taker / min_order_notional_krw) 5 종은 **Phase 2 = NULL**. Phase 2 fillable subset:

| Column | Phase 2 source | Phase 2 채움 |
|---|---|---|
| schema_version | static | YES |
| exchange | static | YES |
| symbol | `/public/ticker/ALL_KRW` 응답 key | YES |
| base_asset | symbol parse | YES |
| quote_asset | symbol parse | YES |
| tick_size | (Live Epic) | **NULL** |
| min_order_qty | (Live Epic) | **NULL** |
| min_order_notional_krw | (Live Epic) | **NULL** |
| fee_maker | (Live Epic) | **NULL** |
| fee_taker | (Live Epic) | **NULL** |
| asset_status | `/public/assetsstatus/ALL` normalize | YES |
| fetched_at | collector clock | YES |
| source_snapshot_id | SHA256 derived | YES |
| data_hash | non-NULL column hash | YES (subset-aware) |

**Phase 2 partition 의 의미**: ADR-002 H5 `ExchangeCapabilities` 의 **producer 자리 박제** + symbol universe / asset_status 만 sealed-pending. quantization 의 hard requirement (tick / qty / fee) 는 Live Epic 진입 시 채워서 producer + consumer 의 동시 transition 가능.

**Live Epic transition path**: 동일 partition (§D13.2 layout) 에 NULL column 채운 새 row append (forward-only, 기존 row 변경 안 함). data_hash 변경 → 신규 row → reader 가 자연스럽게 새 capability 채택. Backward-compat 0 breakage.

**Story carry-over**: H5 dormant 종결의 produce-only meaning 명시 — ADR-002 H5 의 implementation seal 은 Phase 2 = "produce only seal" + Live Epic 진입 시 "produce + consume seal" 로 단계 분리. ADR-002 H5 amendment 2 참조.

### D14. Orderbook L2 snapshot stream v1 (NEW, MCT-104 Phase 1, 2026-05-09)

forward-only L2 30-level orderbook **full snapshot** stream — Bithumb public WS `orderbooksnapshot` channel 의 push event partition. §D11 (`orderbook.v1` L2 event stream — snapshot + delta 가 flat 으로 mix) 와는 **별개 partition**: §D14 = full snapshot only (no delta), §D11.6 fail-closed reconstruction 의 missing baseline gap window 단축의 baseline source.

§D9 (L3 depth-ladder reservation, future exchanges only) 와도 별개 schema — §D9 의 schema_version 은 `orderbook_depth_ladder.v1`, 본 §D14 의 schema_version 은 `orderbook_snapshot.v1` (별도 namespace).

#### D14.1 Schema (11 column — §D11.1 / §D10.1 의 schema_version-out-of-row 패턴 답습)

`schema_version` 은 partition path (`schema_version=orderbook_snapshot.v1`) 에 박제 — column 화 안 함 (§D11.1 / §D10.1 동형). row column 11 (P2-F-002 wiretap amendment: payload_hash 추가):

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[ns, UTC] | no | 거래소 발생 시각 (Bithumb WS event_time, snapshot 자체의 stamp) |
| received_at | timestamp[ns, UTC] | no | collector server-side 도착 시각 (= **available_from_ts**, §D11.4 동형) |
| exchange | string | no | `"bithumb"` v1 only |
| symbol | string | no | canonical |
| baseline_seq | int64 | no | snapshot 내 결정성 sort key = Bithumb WS `content.datetime` 16-digit micro epoch (string→int64). §D14.5 ordering invariant + §D14.10 wiretap 검증 참조 |
| payload_hash | string | no | SHA256 of (symbol, datetime, all 60 levels canonicalized) first 16 hex chars. §D14.6 dedup tie-breaker (Bithumb sequence number 부재 fallback) |
| side | string | no | `"bid"` / `"ask"` |
| level | int32 | no | 0..29 (top-of-book = 0, Bithumb L2 30-level) |
| price | decimal128(38, 18) | no | level price |
| quantity | decimal128(38, 18) | no | level quantity |
| raw_json | string | yes | original WS frame (debug, optional) |

`event_type` column 부재 — 본 partition 은 snapshot 만 보유 (delta 는 §D11).

`baseline_seq` 정의 — **Bithumb WS payload `content.datetime` 16-digit micro epoch string 을 int64 cast**:
- Wiretap 검증 (P2-F-002, 2026-05-09): Bithumb WS `orderbooksnapshot` payload = `{"type":"orderbooksnapshot","content":{"symbol":"BTC_KRW","datetime":"1778310602820158","asks":[...30 levels],"bids":[...30 levels]}}`. `datetime` = 마이크로초 epoch (microseconds since Unix epoch) string, fixed-width 16 digits, lexicographic = numeric ordering 동치.
- `baseline_seq := int64(content.datetime)` — 거래소측 발급, collector 측 추가 발급 불요 (§D11.8 fallback 미사용).
- 동일 (symbol, baseline_seq) row 60건 (bid 30 + ask 30) 이 single message 로 도착 → frame split 미관측 (wiretap 3 message 모두 atomic 60-row).
- 단조성: Bithumb 측 datetime 단조 증가 (실측 200ms 간격 +201ms +231ms 단조 verified).
- **Active-Active dedup**: `baseline_seq` (= 거래소측 datetime) 가 양 node 식별 동일 → §D14.6 logical key tuple `(exchange, symbol, baseline_seq, side, level, payload_hash)` 매핑.

#### D14.2 Hive partition layout

```
market/orderbook_snapshot/schema_version=orderbook_snapshot.v1/exchange={ex}/
       symbol={sym}/date={YYYY-MM-DD}/node={node_id}/
       part-{collector_run_id}.parquet
```

Physical partition = UTC date of `received_at`. §D2.1 HA `node=` partition 적용. §D11.2 (`orderbook.v1`) 와 비슷한 layout 이지만 partition root 가 별도 (`market/orderbook_snapshot/` vs `market/orderbook/`).

#### D14.3 Forward-only invariant + lookahead 방어

**`available_from_ts := received_at`** — §D11.4 동형 mechanism. `event_time` (`ts_utc`) 사용 금지 — Bithumb 측 server clock skew 가능.

#### D14.4 결정적 sort key

`(baseline_seq ASC, side ASC ['ask' < 'bid' alphabetical], level ASC)`. 동일 baseline_seq (= 거래소측 datetime micro epoch) 내 60 row 는 side+level 순. Backtest 결정성 의무.

`ts_utc` 는 sort key 미사용 — `ts_utc` 의미 = `baseline_seq` 를 ns precision timestamp 로 cast (`datetime.fromtimestamp(baseline_seq / 1_000_000)`) — 동일 source. baseline_seq 가 1차 sort key. ns timestamp 손실 없음 (micro source).

§D11.5 (delta event stream) 의 sort key 와 다름 — §D14 는 60-row snapshot frame 내 ordering (snapshot 자체의 60 row 가 결정적) 의무가 추가.

#### D14.5 Ordering invariant — baseline_seq + delta applicability window (Calibration C3 freeze)

본 절은 §D11.6 fail-closed reconstruction 정책의 **contract base alignment**. 3 invariant freeze:

**(1) 동일 (symbol, baseline_seq) 의 60-row 결정성 — wiretap 검증 (P2-F-002, 2026-05-09)**

Bithumb WS 의 single message 는 **atomic 60-row** (bid 30 + ask 30 + datetime + symbol):
- Wiretap 3 message 모두 single-frame, multi-frame split 미관측 — 직전 가정 (§D11.8 divergence source) 거부됨
- `baseline_seq := int64(content.datetime)` (거래소측 발급) — collector 측 frame_seq 발급 불요
- 동일 (symbol, baseline_seq) row 60건 = 동일 message → single-write atomic insertion
- 양 node 가 동일 message 받으면 동일 baseline_seq → §D2.1 dedup 자연 적용 (§D14.6 logical key tuple)

**(2) Snapshot 적용 후 §D11 delta event 가 어느 시점부터 fold-forward 가능한지 (=delta applicability window)**

Reconstruction utility (MCT-66 `get_orderbook_at`) 의 fold sequence:

1. **Baseline 선택**: 시점 T 에 대해 `received_at <= T` 인 가장 최근 §D14 snapshot 의 60-row 를 baseline 으로 채택. 없으면 §D11 의 `event_type="snapshot"` event (legacy) 로 fallback.
2. **Delta applicability window**: 채택한 snapshot 의 `received_at` (= `T_baseline`) 기점, **`(T_baseline, T]` 구간의 §D11 delta event** 만 fold-forward. `received_at <= T_baseline` 인 §D11 delta 는 **무시** (이미 snapshot 에 반영된 state 의 prior delta — replay 시 over-apply 발생).
3. **60-row atomicity safety**: 동일 baseline_seq 의 row count 가 60 미만 detected 시 fail-closed (`ReconstructionError("incomplete snapshot 60-row")`). silent skip 거부. 직전 baseline 으로 fallback 또는 halt 의 caller 정책 의무. (Bithumb single-frame atomic insertion 가정 — wiretap verified, but collector parquet write partial fail 가능성 보호.)

**(3) Snapshot 도달 전 delta 도달 시 처리 정책**

WS reconnect 직후 또는 collector startup 직후 시점:

- 처리 path = **2-step**:
  1. Pending queue 보관 (in-memory, FIFO, default size 10,000 event). reconnect 후 첫 snapshot 도달 시점까지의 delta 만 보관.
  2. 첫 snapshot 도달 시 (2) applicability window (= snapshot 의 `received_at` = T_baseline 이후 delta 만) 적용 후 fold. snapshot 도달 전 delta = T_baseline 이전 → 무시 (queue drop). snapshot 도달 후 도착 delta = queue 비우면서 fold.
- Fail-closed trigger:
  - Queue overflow (10,000 event 초과 도달) = halt + emit `PendingDeltaOverflow`. snapshot push interval 이 reconnect 후에도 도달 안 함 = upstream incident.
  - Reconnect 후 first-snapshot-timeout (default 60sec) = halt + emit `MissingBaselineHaltEvent`. §D11.6 의 "missing baseline" 정책 답습.
- 본 정책은 §D11.6 fail-closed 의 단축 효과 = "다음 snapshot 도달 시점까지의 wall-clock 단축". **Wiretap 검증 (P2-F-005, 2026-05-09)**: BTC_KRW 측정 push interval ≈ 200ms (3 message 0.43s) → ArchitectPL 30s 가정의 ~150x 더 빈번. **§D14.10 1-sec subsample throttle 의무 (적재 측면)** — first-snapshot timeout 는 **WS native push 기준** 60sec 유지 (subsample 적용 전 단계).

본 invariant 3종은 §D11.6 fail-closed 정책의 "missing baseline" gap window 단축 mechanism 의 contract — silent skip / over-apply / under-apply 어느 violation 도 fail-closed.

#### D14.6 Active-Active HA dedup logical key

Wiretap 결과 (P2-F-002 / P2-F-004, 2026-05-09): Bithumb sequence number 부재, **datetime micro epoch (16-digit string) 가 거래소측 ordering anchor**. 양 node 가 동일 message 받으면 동일 `baseline_seq` (= datetime int64) 자연 일치.

**Logical key**: `(exchange, symbol, baseline_seq, side, level, payload_hash)` 6-tuple.

- `baseline_seq` = 거래소측 datetime micro epoch — 양 node 동일 (Bithumb broadcast).
- `(side, level)` = snapshot 의 60-row position.
- `payload_hash` = SHA256(canonical message body) first 16 hex — 동일 baseline_seq 의 다른 hash detected = upstream 변경 (impossible in normal operation, fail-closed trigger).

**dedup procedure**:
1. multi-node partition union scan
2. 동일 6-tuple 발견 시 **node priority** (alphabetical) — §D2.1 동형
3. content (price + quantity) 일치 → idempotent skip
4. content mismatch (`payload_hash` 불일치) → **`active-active mismatch` quarantine** emit + **fail-closed halt** (Bithumb broadcast 정합성 위반 = upstream incident)

**Dedup 정확도 목표**: **> 99%** (T2 동형 — broadcast source 동일하므로 양 node 일치 기대 매우 높음). 미달 시 root cause: (a) network drop on one node + Bithumb non-replay → 한쪽 row 만 존재 (자연), (b) host clock skew (영향 없음, baseline_seq 가 거래소측), (c) collector parquet write partial fail (60-row atomicity safety §D14.5 (3) 의 보호 대상).

**Timestamp tolerance**: 불요 (`baseline_seq` strict equality — 거래소측 micro epoch).

**raw_json column 정책**: §D11.8 동형 (node priority 우선 row 의 값 채택).

**§D11.6 Fail-closed reconstruction 와의 관계**: 기존 §D11.6 은 §D14 도입 후에도 유지. 단 baseline source 가 §D11 의 `event_type="snapshot"` event 만이 아니라 §D14 의 snapshot frame 도 포함 — reconstruction utility 의 baseline 선택 알고리즘 (D14.5 (1)/(2)) 가 양 source union.

#### D14.7 Read API contract

```python
def scan_orderbook_snapshots(
    exchange: str,
    symbol: str,
    start: datetime,
    end: datetime,  # half-open [start, end)
    *,
    snapshot_id: str | None = None,
) -> Iterable[OrderbookSnapshotRecord]:
    """L2 30-level full snapshot stream. ts_utc ASC + baseline_seq ASC + side+level ASC."""
```

`get_orderbook_at(symbol, ts_utc)` (§D11.3 의 기존 utility) 의 baseline source 는 §D14 (`orderbook_snapshot.v1`) → §D11 (`event_type="snapshot"`) → halt 순으로 fallback. caller 변경 0 — utility 내부 baseline selection 이 §D14 우선.

#### D14.8 Storage budget 정량 추정 (Calibration C1 freeze)

**Wiretap 검증 (P2-F-005, 2026-05-09)**: BTC_KRW push interval **≈ 200ms** (3 message 0.43s 측정). ArchitectPL 30s 가정 대비 ~150x. **§D14.10 1-sec subsample throttle 적용 후** 산출:

- Native push: **~200ms (variable, BTC peak — 거래량 비례 추정 50-sym 평균 ≈ 1-5sec)**
- **§D14.10 subsample throttle: 1-sec/symbol** (적재 측면 hard cap)
- Per-snapshot rows: **60 (bid 30 + ask 30 + 1 payload_hash column)**
- Per-day snapshots/symbol (post-throttle): 24 × 3600 / 1 = **86,400**
- Per-row size compressed (zstd level 3): **~45 bytes** (decimal128 2 + int32 1 + int64 1 + string 6 + timestamp 2, raw_json nullable null 가정, payload_hash 추가)
- 50 symbols × 1년 × 2 node = **~3 TB/year** (post-throttle, **uncapped retention**)
- **Retention freeze: 180 days** → annual rolling **~1.5 TB** (2 node)
- **Phase 3 lock-in 의무**: 첫 7일 측정 후 (a) 50-sym 평균 native push interval (b) 1-sec throttle 후 실효 row 수 (c) zstd 압축률 측정 → retention 단축 또는 throttle 강화 (예: 5-sec) 결정.

**대안 검토**:
- Throttle 5-sec (24×3600/5 = 17,280/day) → **~600 GB/year 2 node**, 180-day rolling ~300 GB. reconstruction baseline window 단축 효과 약화 (max 5sec gap 까지 §D11.6 fail-closed 발동 가능).
- Throttle 1-sec 채택 사유: §D11.6 fail-closed 의 missing baseline window 단축 = 본 §D14 의 핵심 motivation. 1-sec 이 reconstruction 신뢰성과 storage cost 의 균형점.

P1 `exchange_metadata.v1` 은 daily × 50 sym × 2 node × ~50 bytes = **~1.8 MB/year, 영구 retention**. 무시 가능.

Compression: zstd (level 3) 통일.

#### D14.9 Out-of-scope

- L3 depth-ladder (§D9 future exchanges only).
- Bithumb private WS (KRW 스팟 미공개).
- multi-exchange (Bithumb only v1).
- §D11 delta partition 의 retention 변경 (별도 ops Story).
- WS subscribe option `isOnlySnapshot=true` (P2-F-002 wiretap 시도 결과: `orderbookdepth + isOnlySnapshot=true` 가 delta-style payload 응답 — snapshot mode 미동작 또는 의미 다름. `orderbooksnapshot` lowercase literal 만 채택).
- WS subscribe option `orderbookSnapshot` camelCase (P2-F-002 wiretap: `Wrong Filter Type` 에러 — Bithumb 가 lowercase 만 인정).

#### D14.10 Subsample throttle 정책 (NEW, MCT-104 Phase 2 entry, 2026-05-09)

**Wiretap 검증 (P2-F-005)**: Bithumb WS `orderbooksnapshot` native push interval ≈ 200ms (BTC_KRW), 거래량 상위 50 sym 의 평균 1-5sec 추정. ArchitectPL 30s 가정 대비 ~150x 더 빈번.

**정책**: collector daemon 의 `OrderbookSnapshotWriter` 가 symbol 별 1-sec sliding window 으로 **last-write-wins throttle** 적용:

```python
# pseudo-code
class OrderbookSnapshotWriter:
    _last_write_ts_per_symbol: dict[str, datetime] = {}

    def write_if_eligible(symbol, snapshot_event):
        last = self._last_write_ts_per_symbol.get(symbol)
        if last is None or (snapshot_event.received_at - last) >= timedelta(seconds=1):
            # write parquet row(s) for this snapshot (60 rows)
            self._last_write_ts_per_symbol[symbol] = snapshot_event.received_at
        # else: drop (subsample)
```

**의미**:
- §D11 delta event stream 은 throttle **안 함** (delta 는 모든 변경 event 적재 의무).
- §D14 snapshot 은 적재 측면만 throttle (1-sec interval). reconstruction 측면 = 1-sec 간격 baseline 충분 (§D11.6 fail-closed missing baseline window 단축 효과 유지).
- WS 채널 자체 unsubscribe 안 함 (Bithumb push 는 그대로 받음, collector 측 drop).
- TBD (Phase 3): 1-sec throttle 의 reconstruction 정확도 측정 — gap 크기 분포 + 실효 baseline window — 측정 후 (a) throttle 강화 (5-sec) 또는 (b) retention 단축 결정.

**Storage 효과**: native ~200ms × 50 sym = ~21.6M row/day → 1-sec throttle = ~4.32M row/day (~5x 감소, 30s 가정 대비 5x 더 적음). §D14.8 ~3 TB/year (180-day rolling 1.5 TB) 가 본 throttle 후 lock-in 값.

**Calibration C2 의무**: throttle drop ratio + reconstruction gap distribution 측정 후 정책 lock-in. Phase 3 entry 시 (50 sym × 7-day 측정) 결과 박제.

### D15. Information bar contract (NEW, MCT-135, Epic MCT-112 Story-1, 2026-05-12)

**Candle = derived view 격하 — ADR-009 의 정체성 변경**:

본 amendment 는 candle (§D8 Candle Protocol) 을 stored entity 에서 **derived view** 로 격하한다. transaction tick (§D10 tick.v1.1) 이 유일한 Bronze SSOT, candle 은 Silver derived view (aggregation result). 거래소 candle API 의존 완전 제거 (Bithumb / Upbit / 모든 거래소). 1차 동기 = 비표준 timeframe 유연성 + information-driven bar (Lopez de Prado AFML) 자유도.

**의미 변경 boundary**:

| 측면 | Before (이전 §D1-§D8) | After (본 §D15 amendment) |
|---|---|---|
| Candle 정의 | stored entity (거래소 candle API → §D1 schema 저장) | derived view (aggregation function of tick.v1.1 stream) |
| Primary source | 거래소 candle endpoint + §D1 16-column Parquet | tick.v1.1 (Bronze SSOT) |
| Candle Protocol (§D8) | scan_candles → stored Parquet read | scan_candles → on-demand aggregation (또는 materialized cache, contract metadata 의무) |
| Backfill 가능성 | candle endpoint 호출 | tick stream 누적 시점부터만 가능 (legacy candle 은 §D16 / ADR-026 정책 적용) |

**Information bar contract — 4 알고리즘 (ADR-025 SSOT)**:

본 §D15 는 information bar 의 **label format + metadata contract** 만 정의 (alg 구현 SSOT 는 ADR-025 Aggregation Core Lib Contract). 4 알고리즘:

| 알고리즘 | Label format | 의미 |
|---|---|---|
| Time bar | `time_5m` / `time_15m` / `time_1h` / `time_47s` (임의 timeframe) | tick 도착 시각 의 fixed time window aggregation. `[start, end)` inclusion (ADR-005 동형). |
| Volume bar | `vol_1000000krw` / `vol_100btc` | cumulative volume threshold 도달 시 bar close. quantity 단위 (base asset) 또는 KRW notional. |
| Tick bar | `tick_1000` / `tick_500` | cumulative tick count threshold 도달 시 bar close. order arrival rate 균일화. |
| Dollar bar | `dollar_5000000krw` / `dollar_100000000krw` | cumulative KRW notional threshold 도달 시 bar close. trade value (price × quantity) 누적. |

**Label format invariants**:

- Format: `<algorithm>_<threshold><unit>` (snake_case + unit 명시).
- Algorithm = `time` / `vol` / `tick` / `dollar` (4 종, ADR-025 SSOT).
- Threshold = positive integer + unit suffix. `time` = `s` / `m` / `h` / `d` (seconds/minutes/hours/days), `vol` = `krw` (KRW notional) / `<base>` (base asset 명, e.g., `btc`), `tick` = no unit (count), `dollar` = `krw`.
- Backward compat: 기존 `1m` / `5m` / `15m` / `1h` / `4h` / `1d` (§D1 timeframe column) 는 implicit `time_*` 으로 해석 (`1m` ≡ `time_1m`).

**Immutable contract metadata (8 필드)**:

각 information bar instance 가 발급된 시점에 **immutable contract metadata** 박제 의무. 본 metadata 가 backtest 결정성 + Hot/Cold consistency (ADR-025 §D5 SLO) 의 alignment 기준.

| 필드 | 타입 | 의미 |
|---|---|---|
| genesis_ts | timestamp[ns, UTC] | 본 bar contract 가 처음 발급된 시각 (= 첫 tick 의 ts_utc) |
| threshold | string | algorithm 의 threshold parameter (e.g., `"5m"` / `"1000000"` / `"1000"` / `"5000000"`) |
| precision | string | 수치 표현 정밀도 (e.g., `"krw_scaled_int"` / `"decimal_38_18"`) — ADR-025 §D3 reference |
| rounding_rule | string | boundary rounding policy (e.g., `"ROUND_HALF_EVEN"` / `"ROUND_DOWN"`) |
| source_cutoff | timestamp[ns, UTC] | 본 bar 가 의존하는 tick 의 cutoff (§D16 provenance + ADR-026 cutoff timestamp 정합) |
| tie_breaking | string | 동일 threshold-crossing tick 처리 정책 (e.g., `"include_in_current"` / `"include_in_next"`) |
| version | string | contract metadata schema version (e.g., `"contract_metadata.v1"`) |
| contract_id | string | 위 7 필드의 canonical JSON → SHA256 hex. immutable hash. |

**`contract_id` 결정성 의무**: 동일 (genesis_ts, threshold, precision, rounding_rule, source_cutoff, tie_breaking, version) tuple → 동일 contract_id. Hot/Cold 양 path (ADR-025 §D1) 가 동일 contract_id 발급 의무. mismatch detected 시 strategy 입력 reject + fail-closed.

**수치 표현**:

ADR-025 §D3 SSOT. KRW pair 는 원 단위 = naturally integer-friendly → KRW scaled integer 채택. boundary 에서만 Decimal(38,18) ↔ scaled int 변환. backtest 누적 정확도 + Hot/Cold 양 path 의 rounding alignment 확보. 본 §D15 의 `precision` metadata 가 알고리즘 별 수치 표현 박제.

**Hot/Cold consistency**:

- Hot path (Python asyncio per-symbol state machine) ↔ Cold path (DuckDB SQL over Parquet) 양 path 가 ADR-025 Aggregation Core Lib import 의무
- SLO: drift < 0.01% bar count mismatch (ADR-025 §D5)
- 위반 시: strategy 입력 Cold fallback (Hot path bar reject)

References:
- ADR-025 (Aggregation Core Lib Contract) — 4 알고리즘 SSOT + Hot/Cold consistency SLO
- ADR-026 (Legacy Candle Provenance & Retirement Policy) — cutoff timestamp + dual-write period
- §D8 (Candle Protocol) — derived view 격하 후 의미 변경 (consumer 코드 영향, Story-9 owner)
- §D16 (Provenance column) — legacy_candle vs transaction_derived row-level provenance
- Lopez de Prado, "Advances in Financial Machine Learning" Ch.2 — information-driven bar

### D16. Provenance column (NEW, MCT-135, Epic MCT-112 Story-1, 2026-05-12)

**`provenance` column 신설** — ohlcv.v1 (§D1) + tick.v1.1 (§D10) + 신규 information bar materialized output 모두에 row-level provenance 박제 의무. ADR-026 (Legacy Candle Provenance & Retirement Policy) 의 cutoff timestamp policy 의 row-level visibility.

**Column 정의**:

| Column | Type | Nullable | Allowed values | 의미 |
|---|---|---|---|---|
| provenance | string | no | `"legacy_candle"` / `"transaction_derived"` | row 가 cutoff 이전 legacy candle Parquet 에서 유래했는지, cutoff 이후 transaction tick aggregation 으로 derive 됐는지 박제 |

**Semantic**:

- **`"legacy_candle"`**: ADR-026 §D2 의 cutoff timestamp 이전 historic 구간의 candle Parquet row. 거래소 candle API 또는 기존 collector polling 으로 수집된 row. immutable SSOT 유지 (ADR-026 §D1). transaction 으로 재계산 불가 (Bithumb backfill 불가 §D12.2). strategy / backtest 가 dataset 별로 본 provenance 인지 의무.
- **`"transaction_derived"`**: ADR-026 §D2 의 cutoff timestamp 이후 transaction tick (§D10 tick.v1.1) aggregation 으로 derive 된 row. Aggregation Core Lib (ADR-025) algorithm 채택 + immutable contract metadata (§D15) 박제.

**Provenance 분기 정책**:

- 동일 partition (e.g., `market/ohlcv/schema_version=ohlcv.v1/exchange=bithumb/symbol=KRW-BTC/timeframe=1m/date=...`) 내에 두 provenance 가 공존 불가 — cutoff timestamp 가 row-level boundary. cutoff 이전 row = `legacy_candle`, cutoff 이후 row = `transaction_derived`. 동일 (exchange, symbol, timeframe, ts_utc) tuple 의 양 provenance row 가 동시 존재 시 = dual-write 기간 (ADR-026 §D4) — reconciliation harness (Story-11) 의 drift 측정 대상.
- `legacy_candle` row 의 `data_hash` / `data_snapshot_id` (§D1 schema) 는 legacy collector 발급 그대로 보존 (immutable).
- `transaction_derived` row 의 `data_hash` / `data_snapshot_id` 는 ADR-025 contract_id 의 prefix 또는 별도 hash (Story-3 / Story-5 implementation 정책 박제).

**Hive partition layout — 변경 없음**: §D1 (`market/ohlcv/...`) + §D10.2 (`market/ticks/...`) 그대로. `provenance` 는 partition key 아님 — column 화. partition key 추가 시 Hive 의 directory cardinality 폭증 + ADR-026 §D4 dual-write 기간 의 양 provenance 동시 존재가 partition layout 의 directory split 을 강요 — 거부.

**Backward compat**:

- 기존 ohlcv.v1 / tick.v1 Parquet (provenance column 부재, 본 amendment 이전 land) → reader 가 `provenance="legacy_candle"` default 적용. Story-9 (engine candle consumer derived view 전환) 가 reader 측 default 박제.
- 신규 row 부터 `provenance` non-null write 의무 (Story-3 / Story-5 / Story-12 implementation seal).

References:
- ADR-026 (Legacy Candle Provenance & Retirement Policy) — cutoff timestamp 정의 + dual-write period + retirement procedure
- §D15 (Information bar contract) — `transaction_derived` row 의 contract metadata SSOT
- §D7 (Schema versioning) — `provenance` column 추가는 minor (compatible)
- Spec: [transaction-ssot-information-bar-design.md](../superpowers/specs/2026-05-12-transaction-ssot-information-bar-design.md) §3 D7 (Legacy candle 처리)

## §D2 amendment — Tier partition for compaction (MCT-106, 2026-05-09)

All Parquet layouts under `market/` gain a mandatory `tier=L{1,2,3}` partition key
**between** `schema_version=` and `exchange=`:

```
market/<channel>/schema_version=*.v1/tier=L{1,2,3}/exchange=.../symbol=.../date=.../node=<id>/part-*.parquet
```

- `node=<id>` remains **mandatory** per §D2.1 (enforced at every tier level).
- `tier=` absent legacy files are treated as `tier=L1` by all `scan_*` read APIs.
- `node=` absent legacy files are treated as `node=DEFAULT` by all `scan_*` read APIs.
  Both mixed-scan behaviours are permanent (no forced migration).

Cross-references: ADR-017 §Decision 2; MCT-106 Change Plan §4.2.

## §D2.6 — ADR009_CHANNEL_SCHEMA_MATRIX SSOT (MCT-159 FIX Iter 1, 2026-05-13)

**Amendment trigger**: MCT-159 production deploy verification (2026-05-13T11:40:44Z) 의 `column_count_fail` 빈발 surface (Story `MCT-159.md` §10 FIX Ledger Iter 1 박제). InvariantHarness `_expected_column_count=16` (ADR009_EXPECTED_COLUMN_COUNT default) **channel-blind enforce** vs 실 schema (orderbook_snapshot.v1=11 / tick.v1=8) **cardinal mismatch**.

§D2.1 의 OHLCV 16-col schema 박제는 **OHLCV row 의 SSOT — 변경 0**. 단 ADR-009 의 column schema SSOT 는 §D2.1 만 아니라 §D10 (tick.v1 8-col / tick.v1.1 11-col) + §D14 (orderbook_snapshot.v1 11-col) 가 별 §section 박제. 본 사실 = `ADR009_CHANNEL_SCHEMA_MATRIX` SSOT 박제 (본 amendment 신규).

### Channel matrix (SSOT)

| schema_version | column_count | column_names | source §section |
|---|---|---|---|
| `orderbook_snapshot.v1` | **11** | ts_utc / received_at / exchange / symbol / baseline_seq / side / level / price / quantity / payload_hash / raw_json | §D14 (P2-F-002 wiretap amendment 2026-05-09) |
| `orderbook_depth.v1` | **11** | ts_utc / received_at / exchange / symbol / side / price / quantity / raw_json / node_id / collector_run_id / ingest_seq | §D11.9 (MCT-162 amendment 2026-05-13) |
| `tick.v1` | **8** | ts_utc / received_at / exchange / symbol / price / quantity / side / raw_json | §D10 (baseline) |
| `tick.v1.1` | **11** | tick.v1 8 col + ingest_seq + payload_hash + validation_status | §D10 amendment (MCT-141) |
| `ohlcv.v1` | **16** | schema_version / exchange / symbol / date / ts / open / high / low / close / volume / vwap / trade_count / bid_count / ask_count / source_provenance / ingestion_ts | §D2.1 (baseline) |

본 matrix = MCT-151 `InvariantHarness` (`mctrader_data/nas_migration/invariant_harness.py`) 의 channel-aware lookup **SSOT**. 신규 schema_version 추가 시 본 §D2.6 matrix amendment 의무 (CFP-26 sibling sync 정합).

**MCT-162 amendment 박제 (2026-05-13)** — `orderbook_depth.v1` row 추가 (column_count=11). bithumb `orderbookdepth` WS channel payload (delta `changes` event) per-level flatten schema. `raw_json` column **`large_string` (LargeUtf8)** 의무 — L2 `pa.concat_tables` i32 offset overflow 차단 (§D11.9.6 박제, MCT-156 OOM exit 137 사례 cross-ref). 본 row 추가 = MCT-159 FIX Iter 1 의 InvariantHarness channel-aware path 자동 정합 — MCT-162 Phase 2 L1 compaction 산출물 (orderbook_depth.v1) 의 L2 cadence (MCT-160 scope) 진입 시 `column_count` invariant lookup 자동 PASS.

### Resolution strategy (channel_count invariant)

1. **Primary**: partition prefix `schema_version=*` extraction → matrix lookup
2. **Fallback**: caller 측 `expected_column_count` explicit injection (backward-compat — 기존 OHLCV cutover path 회귀 0)
3. **Miss strategy**: `column_count_fail` with diagnostic `unknown_schema_version` (schema evolution detection surface)

### MCT-151 InvariantHarness 적용

본 §D2.6 amendment 의 InvariantHarness 적용 = MCT-159 FIX Iter 1 **Phase 2 follow-up PR** (mctrader-data) scope:
- `ADR009_CHANNEL_SCHEMA_MATRIX` constant 추가 (module-level)
- `InvariantHarness.__init__` signature amend: `expected_column_count: int | None = None` (None 시 schema_version 추출 → matrix lookup)
- `_check_schema_version` channel-aware extension (tuple/list 지원)

Cross-references: ADR-027 D6 amendment (MCT-159 FIX Iter 1, channel-aware column_count resolve) + Story `MCT-159.md` §10 FIX Ledger Iter 1.

## §D2.7 — Schema nullability discipline (MCT-160 amendment, 2026-05-13)

**Amendment trigger**: MCT-162 (EPIC-compactor-operations Story-1) CodeReviewPL P1 finding — L1Compactor `_ORDERBOOKDEPTH_SCHEMA` 의 `nullable=False` 명시 부재 surface. ADR-009 §D10 / §D11 / §D11.9 schema 정의 시 `pa.schema([(name, dtype), ...])` tuple 형식의 default = pyarrow 의 `nullable=True` 가정 — silent default 차단 의무 박제. MCT-160 (EPIC-compactor-operations Story-2) 가 3 schema 일관 nullability 명시 의무 합병.

### Convention (SSOT)

ADR-009 의 모든 schema (§D10 / §D11 / §D14 / §D11.9 / §D15 등 forward stream) 의 column 정의 시 다음 nullability convention 의무:

- **`raw_json` column** = **`nullable=True`** (collector emit 시 fallback 가능, debug optional — §D10.1 / §D11.1 / §D11.9.2 / §D14.1 baseline 박제)
- **나머지 column** = **`nullable=False`** (NULL 값 = data corruption signal, well-formed emission 의무) — schema 별 essential field (e.g., `ts_utc` / `exchange` / `symbol` / `side` / `price` / `quantity` 등)
- **Metadata column** (`node_id` / `collector_run_id` / `ingest_seq` / `validation_status` 등 L1Compactor inject) = **`nullable=False`** (L1Compactor inject path 의 invariant — segment metadata 부재 시 corruption signal)

### Schema definition syntax (의무)

`pa.schema([(name, dtype), ...])` tuple 형식 default = `nullable=True` (pyarrow default 가정). SSOT 의무 = `pa.field(name, dtype, nullable=...)` 명시:

```python
# 금지 (silent default nullable=True):
pa.schema([
    ("ts_utc", pa.timestamp("us", tz="UTC")),
    ("price", pa.decimal128(38, 18)),
    # ...
])

# 의무 (explicit nullability):
pa.schema([
    pa.field("ts_utc", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("price", pa.decimal128(38, 18), nullable=False),
    pa.field("raw_json", pa.large_string(), nullable=True),
    # ...
])
```

### Verify (의무)

1. **L1Compactor 3 schema 명시 의무** (MCT-160 Phase 2 land 대상): `_TRANSACTION_SCHEMA` + `_ORDERBOOKSNAPSHOT_SCHEMA` + `_ORDERBOOKDEPTH_SCHEMA` 모두 `pa.field(..., nullable=...)` 명시. malformed frame (essential field = None) 검출 시 `ValueError(f"malformed {channel} frame at index={i}")` raise + Prometheus `compactor_malformed_frame_total{channel,exchange}` Counter +1 emit.
2. **InvariantHarness nullability verify** (MCT-151 land, ADR-027 §D6 정합): `dtype_identity` invariant 가 column dtype 만 비교하는 기존 동작에 더해 nullability 도 check 의무 (Phase 2 follow-up scope, MCT-160 Phase 2 또는 후속 ops Story 박제). 위반 시 `dtype_identity_fail` diagnostic `nullability_mismatch` surface.
3. **Consumer smoke verify** (MCT-160 Phase 3 의무, NFR-5): mctrader-engine reader (`pyarrow.parquet.read_table`) sample query 시 nullable=False column 의 null_count = 0 + nullable=True column 의 null_count 가능 (raw_json optional). DuckDB read 시점도 nullability mismatch 0 (Story `MCT-160.md` §6 D9 consumer nullability smoke verify 박제).

### 3 schema nullable matrix (MCT-160 Phase 2 land 대상 SSOT)

| schema | column | nullable | rationale |
|---|---|---|---|
| `_TRANSACTION_SCHEMA` (tick.v1.1) | `ts_utc` / `received_at` / `exchange` / `symbol` / `price` / `quantity` / `side` / `ingest_seq` / `payload_hash` / `validation_status` | **False** | essential trade row + dedup key + GAP detect anchor |
| `_TRANSACTION_SCHEMA` | `raw_json` | **True** | debug optional (§D10.1 nullable baseline 정합) |
| `_ORDERBOOKSNAPSHOT_SCHEMA` (orderbook_snapshot.v1) | `ts_utc` / `received_at` / `exchange` / `symbol` / `baseline_seq` / `side` / `level` / `price` / `quantity` / `payload_hash` | **False** | essential per-level snapshot row + dedup key |
| `_ORDERBOOKSNAPSHOT_SCHEMA` | `raw_json` | **True** | debug optional (§D14.1 nullable baseline 정합) |
| `_ORDERBOOKDEPTH_SCHEMA` (orderbook_depth.v1) | `ts_utc` / `received_at` / `exchange` / `symbol` / `side` / `price` / `quantity` / `node_id` / `collector_run_id` / `ingest_seq` | **False** | essential delta level row + L1Compactor inject metadata |
| `_ORDERBOOKDEPTH_SCHEMA` | `raw_json` | **True** | debug optional (§D11.9.2 nullable baseline 정합 + `large_string` 의무 — §D11.9.6) |

### Backward-compat invariant

- 기존 L1 산출물 (legacy nullable=True 가정 default 박제) read 호환성 100% — `nullable=False` 명시 후에도 기존 parquet read 시 nullability metadata 가 strict mismatch raise 0 (pyarrow / DuckDB read 측 nullable=False schema cast 가능). MCT-160 §1 AC-6 / §6 D5 / §11 backward-compat invariant 박제 정합.
- L1Compactor 가 신규 emit 부터 `pa.field(..., nullable=False)` 명시 적용 = forward-only 자연 누적, 기존 산출물 retroactive migration 0 (ADR-009 §D12.2 정합).

### Cross-references

- ADR-027 §D4 MCT-160 amendment (cadence silent-skip 차단 + post-write verify + quarantine 정책) — sibling Phase 1 ADR amendment 2건 박제, dual-binding 정합
- Story `docs/stories/MCT-160.md` §1 AC-6 (P1 nullability hardening 합병) + §6 D7 (3 schema 일관 nullability) + §7.4 DataMigrationArch D11=NONE 변호 + §8 Test-6/Test-7 (nullability + malformed frame ValueError)
- MCT-162 Phase 2 CodeReviewPL P1 finding (orderbookdepth schema nullable=False 명시 부재) 합병 anchor
- §D2.6 (ADR009_CHANNEL_SCHEMA_MATRIX) — column count invariant 영향 0 (matrix row 변경 0, nullability metadata 추가만)

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
- ADR-017 — Zero-loss ingestion + WAL + tiered compaction (transaction-tier WAL policy)
- ADR-025 — Aggregation Core Lib Contract (Hot/Cold shared aggregation core, 4 알고리즘 SSOT)
- ADR-026 — Legacy Candle Provenance & Retirement Policy (cutoff timestamp + dual-write + retirement)
- MCT-112 (Epic) — Transaction SSOT & Information-Driven Bar Architecture
- MCT-135 (Story-1) — 본 amendment Major + ADR-017 amendment + 2 신규 ADR draft Story
