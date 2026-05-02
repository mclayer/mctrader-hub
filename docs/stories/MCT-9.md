---
story_key: MCT-9
status: phase:요구사항
component: data
type: brainstorm
related_adr: ADR-009
---

# MCT-9: OHLCV 스키마 v1 + 거래소 normalization + Candle Protocol

## 1. 사용자 요구사항 (verbatim)

mctrader 의 OHLCV 스키마 v1 (mctrader-market 의존). ADR-002 D2 / ADR-003 H1 / ADR-005 path (c) / ADR-006 D10 의 baseline 위에 canonical schema + Bithumb/Upbit normalization + Candle Protocol contract 박제.

## 2. 도메인 해석

mctrader-data 의 storage canonical = Parquet/DuckDB. 모든 backtest / paper / live 가 같은 OHLCV view 를 read. **Decimal 정확도 + UTC 저장 + KST daily boundary + no forward-fill** 가 핵심 invariant.

## 3. 관련 ADR

- ADR-009 ([`../adr/ADR-009-ohlcv-schema.md`](../adr/ADR-009-ohlcv-schema.md))
- baseline: ADR-002 D2 / ADR-003 H1 / ADR-005 path (c) / ADR-006 D10
- 향후: MCT-13 (mctrader-market interface — Candle Protocol 구현)

## 4. 관련 코드 경로

```
mctrader-data/  (별도 repo)
├── src/mctrader_data/
│   ├── schema/ohlcv_v1.py        # canonical schema definition
│   ├── adapters/
│   │   ├── bithumb.py             # Bithumb candle → canonical
│   │   └── upbit.py               # Upbit candle → canonical
│   ├── resample.py                # 1m → 5m / 15m / 1h / 4h / 1d
│   ├── partition.py               # Hive layout writer
│   ├── quality/
│   │   ├── validator.py           # halt / skip / quarantine policy
│   │   └── lineage.py             # feature lineage metadata
│   └── reader.py                  # DuckDB-friendly read API

mctrader-market/  (별도 repo)
└── src/mctrader_market/
    └── protocol.py                # Candle Protocol (본 ADR contract)
```

## 5-6. 요구사항 / 외부 지식

Reference:
- Upbit candle REST: `market` / `candle_date_time_utc` / `candle_date_time_kst` / `opening_price` / `high_price` / `low_price` / `trade_price` / `timestamp` / `candle_acc_trade_price` / `candle_acc_trade_volume` / `unit`
- Bithumb v1.2 candlestick REST: `/public/candlestick/{order_currency}_{payment_currency}/{interval}` (1m/3m/5m/10m/15m/30m/1h/4h/6h/12h/24h/1w/1mm)
- Apache Arrow / Parquet / DuckDB hive_partitioning

## 7. 설계 서사 (요약)

### 7.1 v1 Canonical schema (16 columns)

| Column | Parquet/DuckDB type | 의미 |
|---|---:|---|
| schema_version | VARCHAR | `\"ohlcv.v1\"` |
| exchange | VARCHAR | `bithumb` / `upbit` (lower-case enum) |
| symbol | VARCHAR | `KRW-BTC` (canonical) |
| base_asset | VARCHAR | `BTC` |
| quote_asset | VARCHAR | `KRW` |
| timeframe | VARCHAR | `1m` / `5m` / `15m` / `1h` / `4h` / `1d` |
| ts_utc | TIMESTAMP_MS | candle open time UTC, ms resolution |
| open | DECIMAL(38,18) | 시가 |
| high | DECIMAL(38,18) | 고가 |
| low | DECIMAL(38,18) | 저가 |
| close | DECIMAL(38,18) | 종가 |
| volume | DECIMAL(38,18) | base asset 체결 수량 합 |
| value | DECIMAL(38,18) | quote asset 체결 금액 합 |
| source_ingested_at | TIMESTAMP_MS | 원천 수집 UTC 시각 |
| data_snapshot_id | VARCHAR | ADR-006 D10 manifest 참조 |
| data_hash | VARCHAR | row 또는 file content hash |

**Decimal(38,18) 채택 근거**: KRW pair = BTC 1700만 ~ 알트 0.01 KRW 이하 + 수량 소수. float64 누적 오차 = backtest reproducibility 위험. 성능 필요 시 query layer 에서 DOUBLE projection.

**ms resolution 채택 근거**: 5분 candle boundary 자체엔 불필요하나 Upbit/Bithumb 응답 ms 보존 + 재수집 / 중복 / 원천 추적.

### 7.2 Hive partition layout

```
market/ohlcv/
  schema_version=ohlcv.v1/
    exchange=upbit/
      symbol=KRW-BTC/
        timeframe=1m/
          year=2026/month=05/date=2026-05-02/
            part-*.parquet
```

**Physical partition = UTC date** (한국 KST daily candle 도 ts_utc 의 UTC date 로 저장. KST boundary 는 별도 처리).

DuckDB query:
```sql
SELECT ts_utc, open, high, low, close, volume, value
FROM read_parquet('market/ohlcv/**/*.parquet', hive_partitioning=true)
WHERE exchange='upbit' AND symbol='KRW-BTC' AND timeframe='5m'
  AND ts_utc BETWEEN ts1 AND ts2
ORDER BY ts_utc;
```

### 7.3 거래소 normalization

**Upbit**:
- `market=KRW-BTC` → `symbol=KRW-BTC`, `quote=KRW`, `base=BTC`
- `opening_price` → `open` / `high_price` → `high` / `low_price` → `low` / `trade_price` → `close`
- `candle_acc_trade_volume` → `volume` / `candle_acc_trade_price` → `value`

**Bithumb**:
- `BTC_KRW` → `symbol=KRW-BTC` (방향 반전 + dash separator)
- Array response → 명시 mapping table only
- `value` 부재 시 `quarantine` (canonical 승격 금지)

### 7.4 Resampling rules

**1m canonical → higher TF 자체 재계산** (거래소 higher TF = 검증용 / fallback 만):
```
open  = first non-null open
high  = max(high)
low   = min(low)
close = last non-null close
volume= sum(volume)
value = sum(value)
```

**Boundary**:
- `1m / 5m / 15m / 1h / 4h` = UTC epoch boundary
- `1d` = **KST 자정 기준** (`2026-05-02 KST daily` → `ts_utc=2026-05-01T15:00:00Z`)
  - UTC midnight daily 사용 시 거래소 UI / 원천 API 와 불일치 → **금지**

### 7.5 Missing / duplicate / out-of-order

**3 종 결측 분류**:
- Expected gap (거래 없음, candle 미생성)
- Ingest gap (API 장애 / 수집 실패)
- Lifecycle gap (상장 전 / 거래정지 / 점검)

**Forward-fill = 금지** (canonical 에서). 결측 = row 생성 안 함 + quality manifest gap 기록. Strategy / chart layer 가 시각적 연속성 원하면 canonical 외 view 에서 명시적 `fill_policy`.

**Halt / Skip / Quarantine 정책**:
- 필수 값 누락 / decimal parse 실패 = batch halt
- 일부 row 만 실패 + payload 보존 = quarantine + manifest 기록 + 나머지 skip
- `value` 부재 + 재계산 근거 부재 = canonical 승격 halt
- `volume=0` + open=high=low=close 동일 = 허용 (실제 거래소 candle)
- 음수 가격 / 수량 / 거래대금 = reject

**Duplicate key** = `(exchange, symbol, timeframe, ts_utc)`:
- 동일 hash = idempotent no-op
- 다른 값 = late correction → conflict manifest + append-only + serving view (latest accepted only)

**Out-of-order** = 정상 (정렬 후 key uniqueness + boundary alignment 검증).

### 7.6 Feature lineage metadata schema (ADR-005 path c)

별도 Parquet dataset (OHLCV row 와 분리):

| column | type |
|---|---|
| feature_set | VARCHAR (e.g. `ohlcv_resampled` / `rsi_14`) |
| feature_version | VARCHAR |
| exchange | VARCHAR |
| symbol | VARCHAR |
| timeframe | VARCHAR |
| ts_utc | TIMESTAMP_MS |
| source_start_ts | TIMESTAMP_MS |
| source_end_ts | TIMESTAMP_MS (exclusive) |
| computed_at_ts | TIMESTAMP_MS |
| **available_from_ts** | TIMESTAMP_MS |
| data_snapshot_id | VARCHAR |
| data_hash | VARCHAR |

`available_from_ts` = lookahead 방지 핵심. 5m feature = `ts_utc + 5m` 이후 가용. KST daily = KST 일봉 close 이후 가용 (UTC partition 과 혼동 금지).

### 7.7 Schema versioning

`ohlcv.v1` 고정. **Backward compat policy**:
- **Minor (compatible)**: 컬럼 추가
- **Major (incompatible)**: 컬럼 삭제 / 타입 변경 / 의미 변경 / partition key 변경 / `value` optional 화

v1 reader = unknown 추가 컬럼 무시.

### 7.8 mctrader-market Candle Protocol contract

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

# Reader contract
def scan_candles(
    exchange: str, symbol: str, timeframe: str,
    start_ts: datetime, end_ts: datetime,
    snapshot_id: str | None = None,
) -> Iterable[Candle]:
    """ts_utc ASC, end exclusive. forward-fill 금지. missing interval 가능."""
```

### 7.9 Orderbook snapshot schema (v1 예약 — ADR-004 D2 L3 future)

Path: `market/orderbook_snapshot/schema_version=orderbook_snapshot.v1/exchange=.../`

후보 columns:
```
schema_version / exchange / symbol / ts_utc / sequence_id /
bid_prices: LIST<DECIMAL(38,18)> / bid_sizes: LIST<DECIMAL(38,18)> /
ask_prices: LIST<DECIMAL(38,18)> / ask_sizes: LIST<DECIMAL(38,18)> /
depth / source_ingested_at / data_snapshot_id / data_hash
```

Upbit `orderbook_units[{ask_price, bid_price, ask_size, bid_size}]` ↔ 본 contract 자연 매핑.

### 7.10 Codex 적용

채택률 13/13. Sonnet 거부 0.

## 8-11

(Phase 2 N/A — doc-only Story.)
