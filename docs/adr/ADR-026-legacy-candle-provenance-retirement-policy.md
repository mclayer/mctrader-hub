---
adr_id: ADR-026
title: Legacy Candle Provenance & Retirement Policy — cutoff timestamp + dual-write + retirement procedure
status: Accepted
date: 2026-05-12
related_story: MCT-135
related_epic: MCT-112
category: data
is_transitional: false
related_adrs:
  - ADR-009 (OHLCV schema — §D15 Information bar contract + §D16 Provenance column)
  - ADR-017 (zero-loss ingestion + WAL + tiered compaction — Transaction-tier WAL policy)
  - ADR-025 (Aggregation Core Lib Contract — drift SLO < 0.01% source)
  - ADR-005 (lookahead verification — backtest 결정성 정합)
---

# ADR-026: Legacy Candle Provenance & Retirement Policy

## Status

Accepted — 2026-05-12. MCT-135 (Epic MCT-112 Story-1) — Transaction SSOT & Information-Driven Bar Architecture 의 historic asset 보존 정책 ADR.

## 해소 기준

**N/A — permanent policy**. 본 ADR 은 cutoff timestamp 후 영구 운영 정책 — Epic MCT-112 의 transaction SSOT cutover 후에도 legacy candle Parquet 자산은 immutable historic SSOT 로 유지 의무. supersede / amend 는 가능하나 dormant 종결 (해소) 은 N/A. retirement 절차 (Story-12) 가 본 ADR 의 cutover trigger 이지만 retirement 자체가 본 ADR 의 종결이 아님 — retirement 이후의 legacy 자산 immutable 운영 + dual-namespace 가 영구.

## Context

### Bithumb historical replay 불가 (ADR-009 §D12.2)

Bithumb public API 는 tick / orderbook 의 historical replay 를 제공하지 않음. mctrader-data 의 transaction stream 은 forward-only — restart 직후의 데이터는 영구 손실. **Bithumb candle endpoint (`/public/candlestick/{interval}/{market}`)** 는 historical candle 제공 (24h 이내 또는 그 이상의 historic) 이지만 tick-level replay 는 불가.

### 기존 candle Parquet 자산 (MCT-103 forward-only 누적)

MCT-103 (50 sym universe, LAND 2026-05-09) 이후 mctrader-data 의 candle collector 가 50 sym × 6 timeframe (1m / 5m / 15m / 1h / 4h / 1d) 의 candle Parquet 을 forward-only 누적. **historic 구간을 transaction 으로 재계산 불가** (Bithumb backfill 불가) — legacy candle 자산은 historic immutable SSOT 의무.

### Cutover risk (spec §6 Risk 3 — MEDIUM)

2-4주 dual-write 기간 strategy 가 어느 source 사용했는지 trace 불가 시 retro/audit 무력화. cutoff timestamp 의 정확 박제 + provenance column visibility 가 reproducibility 의무.

## Decision

### D1. Legacy candle 자산 immutable SSOT 유지

cutoff 이전 historic 구간의 candle Parquet 자산은 **영구 immutable SSOT 유지**:

- **No deletion, no overwrite** — legacy candle Parquet 의 row 변경 / 삭제 금지.
- **Dual-namespace operation** — legacy candle 과 transaction-derived candle 이 동일 partition root (`market/ohlcv/...`) 에 공존. row-level distinguish 는 ADR-009 §D16 `provenance` column.
- **별도 path 명명** (구현 선택, Story-12 implementation seal 시 결정):
  - Option A: 동일 partition (`market/ohlcv/...`) 에 provenance column 만으로 구분. partition layout 변경 없음. Reader 측 `WHERE provenance='legacy_candle'` filter.
  - Option B: 별도 sub-partition (`market/ohlcv_legacy/...` vs `market/ohlcv_derived/...`). partition layout 변경 + reader signature 분기 필요.
  - **권장 = Option A** (ADR-009 §D16 default). Reader transparency 확보.

### D2. Cutoff timestamp 정의 — month boundary

**`cutoff_timestamp`**: legacy candle SSOT → transaction-derived SSOT cutover 시점. **month boundary** (UTC 0시 00분 00초) 채택.

- **예시**: `cutoff_timestamp = 2026-06-01T00:00:00Z` (UTC) — 2026-06-01 00:00 UTC 이전 = legacy_candle, 이후 = transaction_derived.
- **정확 cutoff 시점 박제 timing**: Story-12 retirement 진입 시점에 (a) Story-11 reconciliation harness 의 drift SLO < 0.01% 충족 확인 후 (b) 차월 1일 UTC midnight 을 cutoff 으로 박제.
- **Month boundary 채택 사유**:
  - Strategy retro / audit 의 month-grouped reporting 자연
  - daily candle (timeframe `1d`, ADR-009 §D4 = KST midnight) 의 boundary 와 conflict 회피 — month boundary 는 UTC midnight, daily candle 은 KST midnight, 둘 다 day-level 단위 alignment 자연
  - 명확한 documentation 가능 ("2026년 6월부터 transaction SSOT")
- **거부**: arbitrary timestamp (e.g., 2026-05-23T14:32:17Z) — strategy retro 의 cutoff alignment 노이즈 증가, reproducibility report 가독성 손실
- **거부**: day boundary (UTC midnight, but not month start) — month boundary 의 reporting / audit 자연성 손실

### D3. Provenance column (ADR-009 §D16 reference)

ADR-009 §D16 가 본 ADR 의 row-level visibility SSOT:

- **`provenance="legacy_candle"`**: `ts_utc < cutoff_timestamp` row. 거래소 candle API 또는 기존 collector polling 으로 수집. immutable SSOT.
- **`provenance="transaction_derived"`**: `ts_utc >= cutoff_timestamp` row. Aggregation Core Lib (ADR-025) algorithm 으로 derive. tick.v1.1 (ADR-009 §D10.8) source.

**Strategy / backtest 가 dataset 별 provenance 노출 의무**:

- Engine consumer (Story-9 `mctrader_engine.consumers.candle_view`) 가 strategy 입력 candle 에 provenance metadata 함께 전달 (e.g., `CandleRecord(ts_utc=..., open=..., provenance="legacy_candle", ...)`).
- Backtest report (Story-11 reconciliation harness) 가 backtest 결과의 source provenance 박제 — strategy retro 의 audit 의무.

### D4. Dual-write 검증 period — 2-4주

cutoff timestamp 박제 이전 2-4주 기간 동안 legacy candle + transaction-derived candle 양쪽 수집 + Story-11 reconciliation harness drift % 측정.

**Procedure**:

1. **Phase 5 entry** (Story-11 진입 시점): Bithumb candle collector daemon 유지 + transaction WS subscriber (Story-4) + Aggregation Core Lib (Story-3) 의 transaction-derived candle materialized output 양쪽 운영
2. **Reconciliation harness** (Story-11): daily random sample 1-5% 또는 100 symbol-contract window/day 비교, edge-case fixtures (ADR-025 §D5 fixtures 답습)
3. **Drift metric**: bar count mismatch ratio over symbol-day-contract window. SLO = drift < 0.01% (ADR-025 §D5)
4. **Strategy reproducibility report**: 동일 strategy 를 legacy candle vs transaction_derived 양쪽으로 backtest → PnL diff report (Story-11 산출물)

**기간 2-4주 (변동 허용)**:

- 최소 2주 — Bithumb 변동성 (high vol day + low vol day + 주말) 의 representative sampling
- 최대 4주 — drift SLO 미달 시 root cause analysis + fix + 재측정 buffer
- 4주 초과 시 → root cause 의 architecture impact 분석 → 본 ADR amendment 또는 retirement 보류

### D5. Reconciliation exit criteria

cutoff timestamp 박제 + retirement 진입의 prerequisite 2 조건 **AND**:

1. **Drift SLO 충족**: drift < 0.01% bar count mismatch (ADR-025 §D5). 위반 시 retire 보류.
2. **Strategy reproducibility report PnL diff 허용 tolerance 내**: Story-11 의 strategy backtest legacy vs derived PnL diff 가 사용자 정의 tolerance (default = ±0.1% NAV diff) 이내. 위반 시 retire 보류.

**위반 시 procedure**:

- Drift SLO 위반 → ADR-025 §D5 procedure (Hot path reset + Cold replay 비교 + root cause analysis) 답습
- PnL diff 초과 → strategy-by-strategy root cause (e.g., volume bar threshold boundary tick → strategy signal 변화) → fix 후 재측정
- 4주 초과 시 → 본 ADR §D4 의 4주 max 도달 → architecture impact 분석 → retirement 보류 또는 본 ADR amendment

### D6. Candle collector retirement 절차 (Story-12 owner)

§D5 exit criteria 충족 시 Story-12 가 다음 sequence 실행:

1. **Bithumb candle polling daemon 중지** — `mctrader-market-bithumb` 의 `candle_collector` daemon stop. Bithumb `/public/candlestick/{interval}/{market}` REST 호출 중단.
2. **Code 삭제 or deprecated module 이동** — **deletion preferred**:
  - **Option A (preferred)**: `mctrader_market_bithumb/collectors/candle_collector.py` 삭제 + collector unit / integration test 삭제 + compose service 제거
  - **Option B**: `mctrader_market_bithumb/deprecated/candle_collector.py` 이동 + 명시적 deprecated module + 6-month grace period 후 deletion
  - **권장 = Option A** — codebase 단순성 + 의도 명확성 (cutover 명시화). 단 cutover 이후 1-month 내 emergency fallback 필요성 검토 후 deletion 결정.
3. **Cutoff timestamp 박제** — `mctrader-hub/docs/cutoff-timestamps.yaml` (또는 ADR-026 의 amendment history) 에 정확 timestamp + 박제 일시 + Story-11 drift % final report + strategy PnL diff final report 기록.
4. **Provenance column write 활성화** — Story-3 Aggregation Core Lib 의 `transaction_derived` provenance write 가 cutoff 이후 row 부터 자연 활성 (ADR-009 §D16). legacy candle Parquet 의 provenance column 은 backfill 무관 — reader 측 default `legacy_candle` (ADR-009 §D16 backward compat) 적용.

**Rollback contingency**:

- Retirement 직후 1-month 내 transaction-derived 측 critical bug detected 시 → Bithumb candle collector daemon **재시작 가능** (deleted code 의 경우 git revert + redeploy). 단 retirement 이후 candle Parquet 수집 hole 발생 (collector down 기간). hole 은 transaction-derived 로 reconstruction 가능 (cutoff 이후 row) → critical bug fix 후 transaction-derived 우선 복구.

## Alternatives Considered

### A1. Legacy candle 폐기 (전체 deletion after cutover)

- **거부 사유**: historical context 손실 → backtest 의 long-history strategy (e.g., 1-year volatility study) 불가능. Bithumb 의 historical candle API 도 limited (24h 이내 또는 정해진 retention). mctrader 의 누적 자산 가치 (50 sym × ~6 month 이상 forward-only 누적) 보존 의무.
- **재고려 trigger**: storage cost 압박 (50 TB 이상) — 본 mctrader scale 에서는 무관.

### A2. Candle collector 영구 유지 (transaction SSOT 와 dual-run)

- **거부 사유**: 운영 중복 (Bithumb REST polling + WS subscribe 양쪽 운영) + SSOT 충돌 (legacy candle vs transaction_derived 의 drift detected 시 fallback 분기 복잡) + Bithumb API rate-limit budget 낭비.
- **재고려 trigger**: transaction-derived 의 production 신뢰성 미확보 (Story-11 drift SLO 영구 미달) — 본 ADR §D5 exit criteria 의 자연 trigger.

### A3. Cutoff timestamp 미정의 (provenance column 만, cutoff 박제 보류)

- **거부 사유**: reproducibility 무력화 — strategy retro 시 어느 row 가 legacy / derived 인지 정확 박제 없음 → audit 불가. Story-11 의 drift % final report 의 cutover timing 명확성 손실.
- **재고려 trigger**: 없음 (cutoff 박제 = 본 ADR 의 hard requirement).

### A4. Cutoff timestamp = day boundary (month 아님)

- **거부 사유**: §D2 의 month boundary 채택 사유 (reporting 자연성 + daily candle KST midnight conflict 회피) 손실. arbitrary day boundary 채택 시 strategy retro 의 month-grouped report 분기 (e.g., 5월 23일 cutoff = 5월 1-22 일은 legacy + 23-31 일은 derived) → audit 복잡도 증가.
- **재고려 trigger**: 사용자 explicit 요청 (e.g., 특정 event 시점 cutoff) — current spec 에서는 month boundary 정합.

### A5. Cutoff timestamp = arbitrary timestamp (e.g., reconciliation SLO 충족 직후 wall-clock)

- **거부 사유**: month boundary 의 alignment 자연성 손실. strategy retro / audit reporting 의 가독성 손실.
- **재고려 trigger**: §A4 동형.

## Consequences

### C1. Story-11 (reconciliation harness) — exit criteria source

본 ADR §D5 (drift SLO + PnL diff tolerance) 가 Story-11 의 production deployment exit criteria. Story-11 §8 Test Contract 에 본 ADR §D5 reference 의무.

### C2. Story-12 (retirement) — procedure SSOT

본 ADR §D6 (4-step retirement procedure) 가 Story-12 의 implementation seal SSOT. Story-12 §7 Change Plan 에 본 ADR §D6 reference 의무.

### C3. ADR-009 §D16 (Provenance column) — semantic 정의

본 ADR §D3 가 ADR-009 §D16 의 `legacy_candle` vs `transaction_derived` allowed values 의 semantic SSOT. ADR-009 §D16 의 column 정의는 본 ADR 의 cutoff timestamp policy 의존.

### C4. ADR-025 §D4 `source_cutoff` metadata — cutoff timestamp 정합

ADR-025 의 immutable contract metadata `source_cutoff` 필드 = 본 ADR §D2 cutoff timestamp. ADR-025 의 contract_id (hash) 는 본 ADR §D2 의 cutoff timestamp value 의존 → cutoff 박제 timing 이 ADR-025 contract_id 의 stability 영향.

### C5. Legacy candle 자산 immutable 운영 — storage cost 영구

- 본 ADR §D1 의 legacy candle 자산 immutable 유지는 영구 storage cost 발생. 50 sym × 6 timeframe × 수년 historic = ~수십 GB 추정 (candle compressed Parquet, low cardinality). 무시 가능 size.
- 단 storage policy 의 일관성 (no deletion / no overwrite) 의무 — backup / DR (ADR-009 §D12.3 named volume snapshot) 정합.

### C6. Dual-write 기간 운영 부담 (2-4주)

- Bithumb API rate-limit budget 증가 (candle collector 유지 + transaction WS subscribe). ADR-009 §D13.7 rate-limit 150 r/s 정합 — current candle collector 빈도 (50 sym × 6 timeframe × 1m cadence = ~300 req/min ≈ 5 req/sec) + WS subscribe (rate-limit budget 무관) → 합산 5 req/sec 정합.
- 운영 monitoring 부담 — 양 collector 의 health endpoint + drift % daily report. Story-11 산출물 의무.

### C7. Strategy production deployment gate

- 본 ADR §D5 exit criteria 충족 = strategy production deployment 의 prerequisite. drift SLO 미달 + PnL diff 초과 시 → Story-12 retirement 보류 + dual-write 연장 → production deployment 지연.
- 정합: ADR-025 §C7 (drift SLO 측정 → production deployment gate) 와 동형 정책.

## Cross-references

- ADR-009 §D10 (tick.v1 schema) + §D10.8 (tick.v1.1 minor extension) + §D12.2 (forward-only invariant) + §D15 (Information bar contract) + §D16 (Provenance column)
- ADR-017 §Transaction-tier WAL (amendment 2026-05-12) — Bronze SSOT WAL policy
- ADR-025 (Aggregation Core Lib Contract) — drift SLO < 0.01% source
- ADR-005 (lookahead verification path c) — backtest 결정성 정합
- MCT-103 (50 sym universe LAND 2026-05-09) — legacy candle 자산 누적 시점
- MCT-112 (Epic) — Transaction SSOT & Information-Driven Bar Architecture
- MCT-135 (Story-1) — 본 ADR draft Story
- Spec: [transaction-ssot-information-bar-design.md](../superpowers/specs/2026-05-12-transaction-ssot-information-bar-design.md) §3 D7 (Legacy candle 처리) + §6 Risk 3 (Dual-write 기간 strategy 재현성)
