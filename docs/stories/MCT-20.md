---
story_key: MCT-20
status: phase:대기
component: data
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-009, ADR-010, ADR-011
---

# MCT-20: mctrader-data Paper mode write-side (mode=paper partition + lineage extension)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Paper-generated OHLCV separate partition + lineage extension"

## 2. 목표

`mctrader-data` repo 확장:
- `mode=paper/...` separate Hive partition (ADR-009 v1 schema 보존, canonical historical 와 격리)
- `paper_storage.write_paper_candles()` API (PaperExecutor 가 BarAggregator 산출 시 호출)
- Lineage extension: `adapter_name="mctrader-market-bithumb-ws"` + `fetched_at_utc=aggregation_finalized_at` + `response_hash=normalized_message_batch_canonical_hash`
- `scan_candles` API extension: `mode="historical" | "paper"` filter (default = historical)

## 3. 시작 조건

- ✅ MCT-12 freeze (mctrader-data 0.1.0)
- ✅ MCT-18 Phase 1 PR merge
- MCT-19 와 병렬 가능

## 4. 의존

- 상위: ADR-009 v1 schema (16-column 변경 X)
- 하위: MCT-21 PaperExecutor (write 호출), MCT-23 calibration metric (read mode=paper)

## 5. Acceptance (placeholder)

- TBD: partition path 정확한 위치 (`mode=paper` 가 schema_version 다음? exchange 다음?)
- TBD: lineage extension Pydantic v2 model
- TBD: scan_candles `mode` parameter API design
- TBD: canonical reader (Backtest) 의 default behavior — `mode=paper` 자동 exclude
- TBD: WebSocket batch hash 의 canonical form (msgpack? canonical JSONL?)

## 6. Phase 1 brainstorm

MCT-18 Phase 1 merge 후 Codex 일괄 dispatch → Sonnet 합성 → docs/stories/MCT-20.md 본 brainstorm → Phase 1 PR.

## 7. CFP-60 debut-audit

Phase 2 merge 후 audit signal check (특히 contract-schema = ADR-009 lineage extension).
