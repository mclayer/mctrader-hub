---
story_key: MCT-15
status: phase:대기
component: data
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-009, ADR-010, ADR-011
---

# MCT-15: mctrader-data 7-day OHLCV backfill daemon

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-15: mctrader-data daemon 7일 백필"

## 2. 목표

`mctrader-data` repo:
- ADR-009 OHLCV v1 16-column canonical schema impl
- Decimal(38,18) numeric / UTC timestamp / Hive partition (`exchange=bithumb/symbol=KRW-BTC/timeframe=1h/year=2026/month=05/day=01/`)
- KST 1d boundary aware partition (1d timeframe 만 KST, 그 외 UTC)
- DuckDB / Parquet / pyarrow read+write
- 7-day backfill daemon CLI (`mctrader-data backfill --exchange bithumb --symbol KRW-BTC --tf 1h --days 7`)
- Halt / Skip / Quarantine policy (ADR-009)
- Lineage 메타데이터 (어떤 exchange / 어떤 endpoint / 어떤 시점 fetch 되었는가)

## 3. 시작 조건

- MCT-12 Phase 1 PR merge — MCT-13 의 `Candle` Protocol logical mapping 만 정렬되면 시작 가능
- MCT-14 Bithumb adapter 의 raw fixture 또는 live response 가 input source
- 첫 publish version = `0.1.0`

## 4. 의존

- 상위 의존: ADR-009 (16-column canonical), MCT-13 (logical Candle mapping), MCT-14 (input source)
- 하위 의존자: MCT-16 (engine 이 read)

## 5. Acceptance (placeholder — Phase 1 brainstorm 에서 확정)

- TBD: storage path layout (`data/parquet/` 또는 별도 root) + Windows 호환성
- TBD: DuckDB query interface (직접 SQL 또는 wrapper API)
- TBD: 부분 실패 시 정책 (1 hour gap 발견 — Halt vs Skip vs Quarantine)
- TBD: lineage record 형식 (별도 metadata file 또는 column 내장)

## 6. Phase 1 brainstorm 진행

MCT-12 Phase 1 merge 후 Codex 일괄 dispatch → Sonnet 합성 → Story doc → Phase 1 PR. (MCT-13 과 병렬 가능.)

## 7. CFP-60 debut-audit

Phase 2 merge 직후 audit signal check + 7-카테고리 평가. **Windows path / partition discovery = 첫 R2 high-severity risk source — 적극 detection.**
