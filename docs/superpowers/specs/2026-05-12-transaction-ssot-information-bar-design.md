---
title: Transaction SSOT & Information-Driven Bar Architecture
date: 2026-05-12
status: Spec (brainstorm 완료, writing-plans 진입 대기)
brainstorm_skill: codeforge:codeforge-brainstorm
related_adrs:
  - ADR-009 (Major amendment 예정)
  - ADR-017 (amendment 예정)
related_new_adrs:
  - ADR-NNN: Aggregation Core Lib Contract
  - ADR-NNN+1: Legacy Candle Provenance & Retirement Policy
related_epics:
  - MCT-132 (Compactor Epic-A LAND, 2026-05-11) — framework 재사용
  - MCT-103 (50 sym universe LAND, 2026-05-09) — symbol scope
  - MCT-104 (OrderBook & wiretap) — wiretap 패턴 reference
hub_epic_candidate: MCT-XXX (PMO 가 다음 시퀀스 발급)
---

# Transaction SSOT & Information-Driven Bar Architecture

## 1. 배경 (Why)

**사용자 요청 원문**: "데이터에 대한 재설계 candlestick은 수집하지 않고 candlestick은 필요한 범위 내에서 transaction_history를 통해 생성한다. 이를 위해서는 새로운 데이터 도구도 필요할 것 같다."

**확정된 1차 동기 (WHY)**: 비표준 timeframe 유연성 — 시간 bar (1m/5m/13m/47s 임의) 외 **volume bar / tick bar / dollar bar** 등 information-driven bar (Lopez de Prado, AFML) 생성 자유도.

**보조 동기**: 단일 SSOT 단순화 (candle = derived view, transaction = raw), 거래소 API 의존 감소.

## 2. 핵심 SSOT 모델

```
[Bithumb WS transaction stream]
       │
       ▼ (forward-only, loss = 영구 손실)
   [Transaction WAL] (at-least-once + batch fsync 10-100ms/1000msg, SLA 100ms or 1000msg)
       │
       ▼
   [tick.v1.1 Parquet] (ADR-009 D10 extension: + ingest_seq + payload_hash + validation_status)
       │
       ├─────────────────────────────┐
       ▼                             ▼
 [Hot Aggregator]              [Cold Resample]
 Python asyncio                 DuckDB SQL over Parquet
 per-symbol state               + Polars lazy 보조
 ms-latency bar-close
       │                             │
       └──── shared core lib ────────┘
              (Aggregation Core Lib Contract)
       │
       ▼
 [bar contracts]
 time_5m / vol_1000000krw / tick_1000 / dollar_5000000krw / ...
 (immutable metadata: genesis_ts / threshold / precision / version)
       │
       ▼
 strategy signal (engine) / Streamlit UI (web) / backtest replay
```

## 3. 8 결정점 합성 (Phase 1 brainstorm + Codex review)

### D1. Hot path streaming aggregator
- **선택**: Python asyncio + per-symbol state machine. bounded queue 격리.
- **근거**: 50 sym × ~10-200 trades/sec (burst 5000) 는 Python state update (10-100 µs/tick) 로 충분. Python ecosystem 결합 (mctrader-engine = Python). Polars/Rust = profiling 후 도입.
- **목표**: p50 < 5ms, p99 < 50ms bar-close.
- **수치 표현**: KRW scaled integer (원 단위 = naturally integer-friendly), ingestion 경계에서만 Decimal.

### D2. Cold path 분석 도구
- **선택**: DuckDB primary (SQL over Parquet) + Polars lazy 보조.
- **근거**: in-process, SQL-native, Parquet 직접 read, Streamlit 통합 자연. ClickHouse/QuestDB/Druid/Materialize = v1 보류 (cold latency 병목 실증 후 도입).
- **연간 row 추정**: 100 trades/sec → ~3.15B rows/y. 1000 trades/sec → ~31.5B rows/y.

### D3. Information-driven bar 데이터 모델
- **선택**: 결정론적 materialized output 저장 (strategy/backtest 입력). research 전용 derive-on-demand 별도 허용.
- **Contract metadata (immutable)**: genesis_ts, threshold, precision, rounding rule, source cutoff, tie-breaking, version, contract_id (hash).
- **Label format**: `time_5m` / `vol_1000000krw` / `tick_1000` / `dollar_5000000krw` 형식.
- **수치 정확도**: scaled integer 또는 명시적 precision + rounding rule Decimal — boundary drift 방지.

### D4. 유실 차단 (ADR-017 transaction-tier amendment)
- **선택**: ADR-017 amendment (신규 ADR 아님 — 기존 zero-loss 아키텍처의 transaction-tier 확장).
- **WAL 정책**: at-least-once + batch fsync 10-100ms 또는 1000 msg, WAL memory buffer 50,000 msg (5000 msg/sec × 10 sec burst).
- **SLA**: power-loss window ≤ 100ms or ≤ 1000 msg (먼저 도달).
- **Dedup**: fallback tuple `(exchange, symbol, ts_utc, price, quantity, side, raw_json_hash) + ingest_seq` (ADR-009 D10.7 reference, Bithumb trade_id 부재).
- **Gap detection**: Bithumb WS reconnect 시 sequence hole 검출 + alert. backfill 불가 (D12.2) → `validation_status=GAP` 박제.

### D5. Hot ↔ Cold consistency
- **선택**: shared aggregation core library + reconciliation harness.
- **mechanism**:
  - Hot/Cold 양 path 가 동일 core lib (D3 contract) import — same algorithm, different driver
  - Cold = transaction WAL/Parquet 만 의존 (hot snapshot 의존 금지) — backtest 결정성 보장
  - Reconciliation harness: daily random sample 1-5% 또는 100 symbol-contract window/day 비교, edge-case fixtures (threshold 정확 boundary, time bar inclusion edge, KRW rounding edge)
- **SLO**: drift % < 0.01% bar count mismatch (ADR-NNN 에 명문화).
- **위반 시**: Hot path bar 를 strategy 입력에서 제외, Cold path replay fallback.

### D6. Compactor 재사용 (MCT-132 Epic-A)
- **선택**: framework + ParquetWriter mechanics 재사용, **policy 신규**.
- **수치**:
  - 256 MB Parquet file roll (1000 ticks/sec 시 15-45분, 100 ticks/sec 시 ~10x 길이)
  - 4-8 GB process limit (32 GB host mem_limit 답습, streaming row groups, whole-partition load 금지)
  - partition = `exchange/symbol/date` 우선. 파일 폭발 시 `exchange/date/hour` + symbol column 화 (D6 risk fallback).
- **provenance**: `legacy_candle` vs `transaction_derived` column.

### D7. Legacy candle 처리
- **선택**: immutable legacy SSOT 유지 + cutoff timestamp 부터 transaction SSOT. 2-4주 dual-write 검증 후 candle collector retire.
- **Provenance column**: `legacy_candle` (cutoff 이전) / `transaction_derived` (이후) — strategy / backtest 가 dataset 별 provenance 노출.
- **Cutoff timestamp**: strategy retro 가능 시점 (month boundary 등) — ADR-NNN+1 에 정확 시점 박제.
- **Dual-write 기간**: 2-4주 — reconciliation SLO 충족 + drift < SLO 검증 완료 시 retire.

### D8. tick.v1 schema 확장 → tick.v1.1
- **선택**: ADR-009 D10 의 8-col schema 유지 + minor extension 3 column.
- **추가 column**:
  - `ingest_seq` (uint64) — collector 측 monotonic 발급. dedup + 결정론적 replay key.
  - `payload_hash` (string) — raw WS frame SHA256 16-hex. content-mismatch 검출.
  - `validation_status` (string) — `OK` / `GAP` / `MALFORMED` / `RECONNECT_BOUNDARY` 등.
- **거부**: `trade_id` (Bithumb 미노출, nullable 추가는 오해 소지) / `maker_or_taker` (Bithumb WS 노출 검증 안 됨).

## 4. PMOAgent Phase 2 분해

### Hub Epic: MCT-XXX — Transaction SSOT & Information-Driven Bar Architecture

총 12 Story (5 Phase), 4 ADR.

### Phase 1 (순차 — foundation)
- **Story-1** (hub): ADR amendments + 신규 ADR draft (ADR-009 Major + ADR-017 + 2 신규)
- **Story-2** (market): Candle Protocol 재정의 (derived view), Information bar Protocol 신설, tick.v1.1 schema 확장
- **Story-3** (data): Aggregation Core Lib — time + volume/tick/dollar bar aggregator, immutable contract metadata

### Phase 2 (병렬)
- **Story-4** (market-bithumb): transaction WS subscriber 강화 (ingest_seq + payload_hash + gap detection)
- **Story-5** (data): Cold path — DuckDB resample over Parquet + Polars lazy fallback

### Phase 3 (순차 — storage layer)
- **Story-6** (data): Transaction WAL + at-least-once + batch fsync + fallback tuple dedup
- **Story-7** (data): Compactor transaction-tier policy (MCT-132 framework 재사용)

### Phase 4 (병렬 — consumer 전환)
- **Story-8** (engine): Hot path streaming aggregator (per-symbol state machine)
- **Story-9** (engine): candle 소비 derived view 전환 (backtest/paper/live)
- **Story-10** (web): Streamlit UI DuckDB 전환

### Phase 5 (순차 — cutover)
- **Story-11** (data+engine): Dual-write reconciliation harness (2-4주)
- **Story-12** (market-bithumb+data): Legacy candle collector retirement (cutoff cutover)

### 의존 graph

```
Story-1 (ADR)
  -> Story-2 (Protocol + market)
       -> Story-3 (Core Lib)
            -> Story-5 (Cold)  -+
            -> Story-8 (Hot)   -+-> Story-11 -> Story-12
       -> Story-4 (Bithumb WS)
            -> Story-6 (WAL)
                 -> Story-7 (Compactor) ----+
                                            |
                                Story-9 (engine consumer)
                                Story-10 (web UI)
```

## 5. scope_manifest 초안

```yaml
epic: MCT-XXX
title: "Transaction SSOT & Information-Driven Bar Architecture"

planned_adrs:
  amendments:
    - ADR-009: |
        Major amendment — Candle 정의를 stored entity 에서 derived view 로 격하.
        tick.v1.1 minor extension (ingest_seq uint64 + payload_hash + validation_status).
        provenance column (legacy_candle / transaction_derived).
        Information bar contract (time_5m / vol_1000000krw / tick_1000 / dollar_5000000krw).
        immutable contract metadata (genesis_ts / threshold / precision / version).
    - ADR-017: |
        Amendment — transaction-tier WAL 정책 (at-least-once + batch fsync 10-100ms/1000msg,
        WAL buffer 50,000 msg, SLA = power-loss window ≤ 100ms or ≤ 1000 msg).
        Compactor MCT-132 framework 확장 — transaction-tier policy
        (256MB Parquet roll 15-45분, 4-8 GB process limit, partition exchange/symbol/date).
        fallback tuple dedup reference (ADR-009 D10.7).
  new:
    - ADR-NNN: |
        Aggregation Core Lib Contract — Hot(asyncio) / Cold(DuckDB) 양쪽이 import 하는
        shared pure-Python aggregation core. time bar + volume/tick/dollar bar SSOT.
        immutable contract metadata 발급. Hot/Cold consistency SLO (drift < 0.01%).
    - ADR-NNN+1: |
        Legacy Candle Provenance & Retirement Policy — cutoff timestamp 정의,
        2-4주 dual-write 검증 period, reconciliation exit criteria,
        candle collector retirement 절차, provenance column semantic.

planned_files:
  - repo: mctrader-hub
    files:
      - docs/adr/ADR-009-*.md: "Major amendment — derived view + tick.v1.1 + provenance + information bar contract"
      - docs/adr/ADR-017-*.md: "Amendment — transaction-tier WAL + Compactor extension"
      - docs/adr/ADR-NNN-aggregation-core-lib-contract.md: "신규"
      - docs/adr/ADR-NNN+1-legacy-candle-provenance-policy.md: "신규"
      - docs/stories/MCT-XXX-*.md: "Epic + Story 12개 file"
      - CLAUDE.md: "Information-Driven Bar Architecture 섹션 추가"

  - repo: mctrader-market
    files:
      - mctrader_market/protocols/candle.py: "Candle Protocol 재정의 (source field, derived view semantics)"
      - mctrader_market/protocols/information_bar.py: "신설"
      - mctrader_market/schemas/tick.py: "tick.v1.1 schema 확장"
      - tests/protocols/test_information_bar_contract.py: "신설"

  - repo: mctrader-market-bithumb
    files:
      - mctrader_market_bithumb/subscribers/transaction_ws.py: "ingest_seq + payload_hash + gap detection"
      - mctrader_market_bithumb/collectors/candle_collector.py: "retire (Phase 5)"
      - tests/subscribers/test_transaction_ws_gap_detection.py: "신설"

  - repo: mctrader-data
    files:
      - mctrader_data/aggregation/core.py: "신설 — Aggregation Core Lib"
      - mctrader_data/aggregation/contract_metadata.py: "신설"
      - mctrader_data/wal/transaction_wal.py: "신설 — at-least-once + batch fsync + 50k buffer"
      - mctrader_data/wal/dedup.py: "신설 — fallback tuple dedup"
      - mctrader_data/compactor/transaction_tier.py: "신설 — MCT-132 framework 재사용"
      - mctrader_data/cold/duckdb_resample.py: "신설"
      - mctrader_data/cold/polars_fallback.py: "신설"
      - mctrader_data/reconciliation/dual_write_harness.py: "신설"
      - mctrader_data/reconciliation/hot_cold_consistency.py: "신설"
      - tests/aggregation/test_core_information_bar.py: "신설"
      - tests/wal/test_transaction_wal_power_loss.py: "신설 — SLA 100ms / 1000msg"
      - tests/compactor/test_transaction_tier_roll.py: "신설"
      - tests/reconciliation/test_legacy_vs_derived.py: "신설"

  - repo: mctrader-engine
    files:
      - mctrader_engine/hot/streaming_aggregator.py: "신설 — per-symbol state machine"
      - mctrader_engine/hot/state_machine.py: "신설"
      - mctrader_engine/consumers/candle_view.py: "candle = derived view 전환"
      - mctrader_engine/backtest/data_source.py: "Cold path DuckDB"
      - mctrader_engine/paper/data_source.py: "Cold/Hot 분기"
      - mctrader_engine/live/data_source.py: "Hot path streaming aggregator"
      - tests/hot/test_streaming_aggregator_latency.py: "신설 — ms-latency bar-close"
      - tests/consumers/test_derived_view_consistency.py: "신설"

  - repo: mctrader-web
    files:
      - mctrader_web/data/candle_query.py: "DuckDB query 전환"
      - tests/data/test_duckdb_candle_query.py: "신설"

planned_claude_md_sections:
  - repo: mctrader-hub
    section: "Information-Driven Bar Architecture (신규)"
    reason: "transaction SSOT + Hot/Cold 2 path + shared core lib 정책"
  - repo: mctrader-data
    section: "WAL & Compactor"
    reason: "transaction-tier WAL SLA + Compactor extension"
  - repo: mctrader-data
    section: "Aggregation Core Lib"
    reason: "Hot/Cold shared core 위치 + import 규칙"
  - repo: mctrader-market
    section: "Protocols"
    reason: "Candle = derived view + Information bar Protocol"
  - repo: mctrader-market-bithumb
    section: "Transaction WS subscriber"
    reason: "ingest_seq + gap detection + candle collector retirement 예고"
  - repo: mctrader-engine
    section: "Hot vs Cold data source"
    reason: "backtest/paper/live 별 data source 분기"
  - repo: mctrader-web
    section: "Streamlit data source"
    reason: "DuckDB query"
```

## 6. 위험 요소

### Risk 1: Forward-only transaction stream — 영구 손실 (CRITICAL)
- **상황**: SSOT 유실 = 영구 손실 (Bithumb backfill 불가, ADR-009 D12.2 확정).
- **trigger**: WS reconnect gap / WAL fsync window 내 process crash / Compactor archive 실패.
- **완화**: Story-4 gap detection + `validation_status=GAP` 박제 / Story-6 SLA 100ms/1000msg + retro 위반 카운터 / Story-7 archive 실패 시 WAL 보존 24h→7d 연장.
- **강제 박제**: Story-1 ADR-017 amendment SLA 명문화 + Story-6 §8 Test Contract power-loss fixture (kill -9 + disk full).

### Risk 2: Hot/Cold consistency drift — strategy 재현성 (HIGH)
- **상황**: 같은 core lib 이라도 Hot(per-tick incremental) vs Cold(SQL batch) 의 실행 경로 차이로 boundary tick drift 가능.
- **trigger**: volume/tick/dollar bar threshold crossing 1-tick 어긋남 / scaled int vs DECIMAL rounding / time bar `[start,end)` vs `(start,end]`.
- **완화**: Story-11 daily random sample + edge-case fixtures, drift SLO < 0.01% 명문화 (ADR-NNN), 위반 시 strategy 입력 Cold fallback.
- **강제 박제**: Story-11 §8 Test Contract drift SLO green gate.

### Risk 3: Dual-write 기간 strategy 재현성 (MEDIUM)
- **상황**: 2-4주 dual-write 기간 strategy 가 어느 source 사용했는지 trace 불가 시 retro/audit 무력화.
- **완화**: Story-9 engine 에 signal-to-bar provenance log (bar timestamp + source + contract_metadata_version) / Story-11 reconciliation harness 에 "동일 strategy legacy vs derived 양쪽 backtest → PnL diff report" / cutoff timestamp = month boundary (Story-12 명시).
- **강제 박제**: Story-12 §11 retro 에 dual-write 재현성 검증 결과.

## 7. 의존 Epic / ADR / Story 관계

| 외부 | 관계 | 영향 |
|---|---|---|
| MCT-132 Compactor Epic-A | 재사용 | Story-7 가 framework + spec/plan/runbook/Grafana dashboard 답습 |
| MCT-133/134 | 참조 | retro lesson learned 를 Story-7 plan 입력 |
| MCT-103 50 sym | upstream | Story-4 가 50 sym subscribe 보장. Decimal prec=38 유지 |
| MCT-104 OrderBook & wiretap | 병행 | wiretap 패턴 = Story-4 payload_hash reference |
| ADR-009 | Major amendment | Story-1 핵심 산출물 (candle 정체성 변경, Codex review careful) |
| ADR-017 | Amendment | Story-1 + Story-6 + Story-7 reference |
| CFP-60 | 무관 | codeforge plugin 변경 불필요 |
| #276 EPIC-RESULTS | pending | Epic 종료 시 EPIC-RESULTS-MCT-XXX 작성 위치 #276 close 후 |

## 8. 다음 단계

`superpowers:writing-plans` 진입 — Story-1 (ADR amendments + 신규 ADR draft) 부터 plan 작성. PMOAgent 가 Epic key (MCT-XXX) 발급 후 hub Story 와 5 sister repo Story 동시 scaffold.

scope_manifest 는 Phase 1 PR 시 Hub Epic Issue body 에 붙여넣기.
