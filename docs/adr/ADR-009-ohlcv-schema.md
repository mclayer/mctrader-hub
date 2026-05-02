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

### D9. Orderbook snapshot v1 (예약, ADR-004 D2 L3 future)

```
schema_version=orderbook_snapshot.v1
exchange / symbol / ts_utc / sequence_id /
bid_prices / bid_sizes / ask_prices / ask_sizes / depth /
source_ingested_at / data_snapshot_id / data_hash
```

Lists = LIST<DECIMAL(38,18)>. Upbit `orderbook_units` ↔ 자연 매핑.

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
