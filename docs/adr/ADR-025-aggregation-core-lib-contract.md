---
adr_id: ADR-025
title: Aggregation Core Lib Contract — Hot/Cold shared pure-Python aggregation core (time + volume/tick/dollar bar SSOT)
status: Accepted
date: 2026-05-12
related_story: MCT-135
related_epic: MCT-112
category: data
is_transitional: false
related_adrs:
  - ADR-009 (OHLCV schema — §D15 Information bar contract reference)
  - ADR-017 (zero-loss ingestion + WAL + tiered compaction — Transaction-tier WAL policy)
  - ADR-026 (Legacy Candle Provenance & Retirement Policy)
  - ADR-005 (lookahead verification — backtest 결정성 정합)
---

# ADR-025: Aggregation Core Lib Contract — Hot/Cold shared pure-Python aggregation core

## Status

Accepted — 2026-05-12. MCT-135 (Epic MCT-112 Story-1) — Transaction SSOT & Information-Driven Bar Architecture 의 foundation ADR.

## 해소 기준

**N/A — permanent policy**. 본 ADR 은 Aggregation Core Lib 의 **영구 contract** — Epic MCT-112 의 architecture 핵심. Hot path (Python asyncio per-symbol state machine) ↔ Cold path (DuckDB SQL over Parquet) 양 경로의 동일 algorithm 보장 의무는 mctrader 의 backtest 결정성 + strategy reproducibility 의 hard constraint. supersede / amend 는 가능하나 dormant 종결 (해소) 은 N/A.

## Context

mctrader 의 데이터 lake 재정의 (Bronze/Silver 패턴) — transaction tick (ADR-009 §D10 tick.v1.1) = Bronze SSOT, candle = Silver derived view (ADR-009 §D15 amendment). Information-driven bar (Lopez de Prado, AFML) 의 4 알고리즘 — time / volume / tick / dollar bar — 가 Hot path 와 Cold path 양쪽에서 **결정론적으로 동일 결과** 발급 의무.

### Why Hot/Cold shared core

- **Hot path** (mctrader-engine `mctrader_engine.hot.streaming_aggregator`, Story-8): Python asyncio per-symbol state machine. ms-latency bar-close 의무 (p50 < 5ms, p99 < 50ms). per-tick incremental update.
- **Cold path** (mctrader-data `mctrader_data.cold.duckdb_resample`, Story-5): DuckDB SQL over Parquet (+Polars lazy 보조). batch aggregation over historical tick.v1.1 partition. backtest replay + reconciliation harness.
- **결정성 의무**: 같은 tick 입력 → 양 path 동일 bar 출력 (drift SLO < 0.01%, §D5). 위반 시 backtest 재현성 무력화 → strategy production deployment 불가.

### Why pure-Python core

- mctrader 전 ecosystem = Python (engine / data / market 모두 Python). Polars + Rust core (PyO3) 채택 시 Hot path 의 state machine ↔ Rust FFI boundary 추가 — debugging + observability 비용.
- DuckDB Python UDF (`db.create_function`) 가 pure-Python callable 을 wrap → Cold path 도 동일 Python core 호출 가능. SQL native 알고리즘 (e.g., `window functions`) 채택 시 Hot path 와 별도 implementation seal → drift 위험.
- Performance budget: Python state update (per-tick) = 10-100µs. 50 sym × peak 5000 ticks/sec ≈ 250,000 update/sec → Python 처리 budget 25-50% (충분, profiling 후 hot spot 만 Cython / Rust 도입 여지).

### MCT-103 Decimal prec=38 root fix (2026-05-09)

기존 mctrader-data 의 Decimal prec=28 → prec=38 root fix (MCT-103 universe expansion 시) 후 KRW pair 가격 범위 (BTC ~100M KRW × 18-decimal volume) 누적 정확도 확보. 본 ADR 은 Decimal(38,18) ↔ KRW scaled integer 변환 boundary 정의.

## Decision

### D1. Hot/Cold 양 path import 의무 — pure-Python aggregation core lib

**SSOT**: `mctrader-data` 의 `mctrader_data.aggregation.core` 모듈 (Story-3 implementation owner). 양 path 가 본 모듈 import:

```python
# mctrader-engine Hot path (Story-8)
from mctrader_data.aggregation.core import TimeBarAggregator, VolumeBarAggregator, ...

# mctrader-data Cold path (Story-5, DuckDB UDF wrap)
from mctrader_data.aggregation.core import time_bar_close, volume_bar_close, ...

con.create_function("time_bar_close", time_bar_close, ...)
```

**거부**: SQL native window function (Cold) ↔ Python state machine (Hot) 의 분리 구현 — drift 위험 증대.
**거부**: Rust core PyO3 binding — debugging / observability 비용 (mctrader 의 production 단계 가 아직 alpha, profiling-driven optimization 우선).

### D2. 4 bar 알고리즘 (label format = ADR-009 §D15)

#### D2.1 Time bar

- **Threshold**: 임의 timeframe (e.g., `time_5m`, `time_47s`, `time_1h`, `time_13m`)
- **Boundary**: `[start, end)` half-open inclusion (ADR-005 path c 정합)
- **Aggregation**:
  - `open` = first tick price in window
  - `high` = max tick price
  - `low` = min tick price
  - `close` = last tick price
  - `volume` = sum(quantity)
  - `value` = sum(price × quantity)
- **State machine (Hot)**: window start ts 기준 incremental update. window end 도달 시 emit bar + reset state.
- **SQL (Cold)**: `time_bucket(...)` (DuckDB native) 또는 Python UDF wrap.
- **Edge**: 동일 ts_utc 의 multiple tick = received_at ASC + file_offset ASC (ADR-009 §D10.5) 답습.

#### D2.2 Volume bar

- **Threshold**: cumulative volume (quantity sum) 도달 시 bar close (e.g., `vol_1000000krw` = 1M KRW notional, `vol_100btc` = 100 BTC volume)
- **Unit**:
  - `krw` suffix → cumulative `value` (price × quantity) threshold
  - base asset suffix (e.g., `btc`) → cumulative `quantity` threshold
- **Boundary tick tie-breaking** (`tie_breaking` contract metadata):
  - `"include_in_current"` (default): threshold-crossing tick 의 entire quantity 를 current bar 에 포함 (next bar 의 first tick 은 다음 trade)
  - `"include_in_next"`: threshold-crossing tick 을 next bar 의 first tick 으로 (current bar 의 cumulative 가 threshold 미달)
  - `"split"`: threshold-crossing tick 을 양 bar 에 split (current = threshold 까지, next = 잔여) — boundary drift 위험, 기본 거부
- **State machine (Hot)**: cumulative running sum. threshold 도달 시 emit + reset.
- **SQL (Cold)**: running window sum + threshold detection (Python UDF wrap 권장 — SQL window 으로 incremental threshold 구현 복잡).

#### D2.3 Tick bar

- **Threshold**: cumulative tick count (e.g., `tick_1000` = 1000 trade 마다 close)
- **Aggregation**: tick count = N 도달 시 bar close. open/high/low/close/volume/value 는 §D2.1 동형.
- **State machine (Hot)**: tick counter. N 도달 시 emit + reset.
- **SQL (Cold)**: `ROW_NUMBER()` window function + integer division (`row_num / N` 으로 bar group 부여).
- **Edge**: order arrival rate 의 균일 분포 → information arrival 의 stationarity 향상 (Lopez de Prado §2.3).

#### D2.4 Dollar bar

- **Threshold**: cumulative KRW notional (price × quantity sum) 도달 시 bar close (e.g., `dollar_5000000krw` = 5M KRW notional 마다 close)
- **State machine (Hot)**: cumulative `value` sum. threshold 도달 시 emit + reset.
- **Tie-breaking**: §D2.2 동형 (default `"include_in_current"`).
- **SQL (Cold)**: §D2.2 동형 (running window sum + Python UDF threshold detect).

### D3. 수치 표현 — KRW scaled integer + Decimal boundary

#### D3.1 Scaled integer 채택

- **단위**: 원 (1 KRW = 1 scaled int unit) — KRW pair 가격 + value 모두 정수 친화 (Bithumb KRW price tick = 정수)
- **Volume / quantity**: 18-decimal Decimal(38,18) → scaled int 변환 시 `quantity × 10^18` 으로 표현 (base asset 별 precision 다를 수 있음, default 18)
- **Cumulative running sum**: Python `int` (arbitrary precision) — overflow 무관, KRW notional 1 trillion (10^12) × 10^18 = 10^30 < `int` capacity 무한
- **Rationale**: float / Decimal 의 rounding ambiguity 차단. Hot path 의 per-tick update × 50 sym × peak 5000 ticks/sec 의 누적 정확도 확보.

#### D3.2 Decimal boundary 명시

- **Ingestion boundary**: tick.v1.1 (`price` / `quantity` = Decimal(38,18)) → Aggregation core import boundary 에서 scaled int 변환. `price_scaled := int(price)` (KRW = 정수, native cast), `quantity_scaled := int(quantity × 10^18)`.
- **Emission boundary**: bar emit 시점에 scaled int → Decimal(38,18) 또는 사용자 정의 precision. ADR-009 §D1 OHLCV schema (open/high/low/close/volume/value 가 Decimal(38,18)) 와 backward compat.
- **Rounding rule**: `precision` contract metadata (§D15 + 본 §D2 immutable contract metadata) 에 박제. default = `ROUND_HALF_EVEN` (banker's rounding).

#### D3.3 base asset 별 precision

- BTC / ETH / KRW pair = 18-decimal default
- 향후 다른 base asset 추가 시 (e.g., USDT, future exchange) precision 별도 metadata 박제 — backward compat 의무.

### D4. Immutable contract metadata (8 필드)

각 bar instance 발급 시점에 immutable metadata 박제 — backtest 결정성 + Hot/Cold consistency alignment 의 기준. ADR-009 §D15 SSOT.

| 필드 | 타입 | 의미 |
|---|---|---|
| genesis_ts | timestamp[ns, UTC] | 본 bar contract 가 처음 발급된 시각 (첫 tick 의 ts_utc) |
| threshold | string | algorithm 의 threshold parameter (e.g., `"5m"` / `"1000000"` / `"1000"` / `"5000000"`) |
| precision | string | 수치 표현 정밀도 (`"krw_scaled_int"` / `"decimal_38_18"`) |
| rounding_rule | string | boundary rounding policy (`"ROUND_HALF_EVEN"` 등) |
| source_cutoff | timestamp[ns, UTC] | 본 bar 가 의존하는 tick 의 cutoff (ADR-026 cutoff timestamp 정합) |
| tie_breaking | string | 동일 threshold-crossing tick 처리 정책 (`"include_in_current"` 등) |
| version | string | contract metadata schema version (`"contract_metadata.v1"`) |
| contract_id | string | 위 7 필드의 canonical JSON → SHA256 hex. immutable hash. |

**`contract_id` 결정성 의무**: 동일 (genesis_ts, threshold, precision, rounding_rule, source_cutoff, tie_breaking, version) tuple → 동일 contract_id. Hot/Cold 양 path 가 동일 contract_id 발급. mismatch detected 시 strategy 입력 reject + fail-closed.

### D5. Hot/Cold consistency SLO

- **Drift metric**: bar count mismatch ratio over symbol-day-contract window
- **SLO**: drift < **0.01%** (1 bar in 10,000 mismatch). 위반 시 strategy 입력 Cold path fallback (Hot path bar reject).
- **측정 cadence**: Story-11 reconciliation harness — daily random sample 1-5% 또는 100 symbol-contract window/day 비교.
- **Edge-case fixtures** (Story-11 의무):
  - Volume / tick / dollar bar threshold 정확 boundary (cumulative sum == threshold 동일)
  - Time bar `[start, end)` 의 boundary tick (`ts_utc == window_end`)
  - KRW scaled int rounding edge (Decimal → scaled int 변환 후 boundary)
  - Multi-tick same ts_utc (received_at ordering)
- **위반 시 procedure** (ADR-005 lookahead verification 답습):
  1. drift % > SLO detected → emit `HotColdDriftEvent` alert
  2. strategy 입력 Cold path fallback (engine consumer 측 switch)
  3. Hot path state machine reset + Cold path replay 비교 → root cause analysis
  4. fix 후 Hot path 복귀 (재현성 검증 의무)

## Alternatives Considered

### A1. Polars + state machine (Rust core)

- **거부 사유**: Polars 의 state machine 은 per-row UDF callback 으로 표현 가능하나, per-tick critical path (Hot, p50<5ms) 의 Python ↔ Rust FFI overhead 가 부자연. Python state machine + numpy/Decimal 이 충분 (Python 처리 budget 25-50% 점유 분석, §Context).
- **재고려 trigger**: profiling 결과 Python state update 가 budget > 80% 점유 시 hot spot 만 Cython / Rust 도입 (PyO3 binding, native call frequency 최소화).

### A2. Rust core PyO3 binding

- **거부 사유**: 구현 비용 (Rust crate + PyO3 + maturin 빌드 chain) + debugging / observability 비용 (Python stack trace 손실, profiling 도구 분기). mctrader = production alpha 단계, optimization 우선순위 후순위.
- **재고려 trigger**: production live (10+ symbol live trading) + Python aggregation budget 압박 측정.

### A3. Materialize / Flink / Faust (stream processing platform)

- **거부 사유**: 단일 host pilot 단계 + Docker-first 단순성 (ADR-033). broker (Kafka) 운영 + cluster 관리 부담. ADR-017 §A.B 답습 (Kafka 거부 사유 동형). pure-Python state machine 이 50 sym × peak 5000 ticks/sec 처리 충분.
- **재고려 trigger**: multi-host scale-out + cross-exchange ingestion 통합 시점.

### A4. TimescaleDB Continuous Aggregate (CAGG)

- **거부 사유**: time bar 는 CAGG 자연 매핑이나 volume / tick / dollar bar 는 cumulative threshold 의 incremental refresh 가 CAGG 모델과 부자연 (CAGG = window-based, threshold-based 아님). information-driven bar 4 종 중 1 종만 cover → Hot/Cold consistency 의 alignment 분기 → SLO 측정 복잡도 증가.
- **재고려 trigger**: time bar only ecosystem (volume/tick/dollar bar 제외) 으로 scope 축소 시.

### A5. DuckDB SQL native (window function only, Python UDF 거부)

- **거부 사유**: §Why pure-Python core — Hot path Python state machine ↔ Cold path SQL native 분리 → drift 위험 증대. SQL window 의 cumulative threshold 구현 복잡도 (recursive CTE 또는 ARRAY_AGG + UNNEST 등).
- **재고려 trigger**: SQL native algorithm 의 drift-free 증명 확보 시 (Story-11 reconciliation harness 의 drift SLO < 0.01% verified after 30-day production).

## Consequences

### C1. Story-3 (Aggregation Core Lib 구현, mctrader-data) — primary input

본 ADR 이 Story-3 의 implementation spec source. `mctrader_data.aggregation.core` 모듈 + `contract_metadata.py` 가 본 ADR 의 D1-D5 SSOT.

### C2. Story-8 (engine Hot path) + Story-5 (Cold path) — dependency

- Story-8 (`mctrader_engine.hot.streaming_aggregator`) = 본 ADR §D1 의 Hot path import
- Story-5 (`mctrader_data.cold.duckdb_resample`) = 본 ADR §D1 의 Cold path import (DuckDB UDF wrap)

### C3. Story-11 (reconciliation harness) — SLO 측정

- 본 ADR §D5 의 drift SLO < 0.01% 측정 의무. daily random sample + edge-case fixtures.
- 위반 시 procedure (§D5) 의 `HotColdDriftEvent` alert + Cold fallback 채택 의무.

### C4. ADR-009 §D15 (Information bar contract) — label format alignment

- 본 ADR 의 §D2 4 알고리즘 label format = ADR-009 §D15 label format 정합 (`time_5m` / `vol_1000000krw` / `tick_1000` / `dollar_5000000krw`).
- ADR-009 §D15 의 immutable contract metadata 8 필드 = 본 ADR §D4 동형 (SSOT).

### C5. ADR-026 (Legacy Candle Provenance) — cutoff timestamp source

- 본 ADR §D4 `source_cutoff` metadata = ADR-026 §D2 cutoff timestamp.
- cutoff 이전 row 는 `legacy_candle` provenance (ADR-009 §D16), cutoff 이후 row 는 `transaction_derived`.

### C6. Python performance budget — profiling 의무

- 본 ADR 채택 후 Hot path Python state update 의 latency / CPU budget 점유 측정 의무 (Story-8 §8 Test Contract).
- Budget 압박 시 (>80%) hot spot Cython / Rust 도입 (A1 / A2 재고려).

### C7. Drift SLO 측정 → strategy production deployment gate

- §D5 drift SLO < 0.01% 가 strategy production live 배포 의 prerequisite. ADR-026 §D5 reconciliation exit criteria 와 동형.
- 위반 시 Cold path fallback 강제 → Hot path latency 이득 (ms-latency) 손실 → production 영향 분석 의무.

## Cross-references

- ADR-009 §D10 (tick.v1 schema) + §D10.8 (tick.v1.1 minor extension) + §D15 (Information bar contract) + §D16 (Provenance column)
- ADR-017 §Transaction-tier WAL (amendment 2026-05-12) — Bronze SSOT WAL policy
- ADR-026 (Legacy Candle Provenance & Retirement Policy) — cutoff timestamp source
- ADR-005 (lookahead verification path c) — backtest 결정성 정합
- MCT-103 (50 sym universe, Decimal prec=38 root fix, 2026-05-09)
- MCT-112 (Epic) — Transaction SSOT & Information-Driven Bar Architecture
- MCT-135 (Story-1) — 본 ADR draft Story
- Spec: [transaction-ssot-information-bar-design.md](../superpowers/specs/2026-05-12-transaction-ssot-information-bar-design.md) §3 D1 (Hot path) + §3 D2 (Cold path) + §3 D3 (Information-driven bar 데이터 모델) + §3 D5 (Hot ↔ Cold consistency)
- Lopez de Prado, "Advances in Financial Machine Learning" (Wiley, 2018), Ch.2 — information-driven bar (volume/tick/dollar bar)
