---
story_key: MCT-71
status: phase:완료
component: web
type: brainstorm
parent_epic: MCT-70
related_adrs: ADR-002
---

# MCT-71: BacktestRequest tier-aware extension + 422 coverage validation

## 1. 사용자 요구사항 (verbatim, MCT-70 Epic Phase 1)

`POST /backtests` 가 T1/T2/T3 모든 strategy 수락 + tier coverage 부족 시 fail-fast 422.

## 2. 도메인 해석

MCT-70 child #1 = **POST 입구 schema 확장 + validation hook**.

핵심 design:

- **`BacktestRequest.strategy: str`** (Literal 제거) — registry lookup 으로 변경. 미등록 = 422.
- **Legacy alias**: `strategy="sma"` → `sma_v1` 자동 변환 (기존 web client 무파괴).
- **Tier coverage 의무 호출**: T2/T3 strategy 인 경우 `tier_coverage(symbol, tier, start, end)` 호출 → 부족 시 422 with `detail.missing_tiers + missing_window`.
- **fail-fast**: executor 진입 전 차단 (큐잉 비용 회피).

## 3. 관련 ADR

- **ADR-002 D2** — Backtest mode 의 input contract 정의.

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/api/
├── models.py               (MODIFY — BacktestRequest.strategy Literal 제거 + alias resolution)
└── routes.py               (MODIFY — POST handler tier coverage 의무 호출)

mctrader-web/tests/api/
└── test_backtest.py        (MODIFY — 422 unknown strategy + 422 coverage fixtures 추가)
```

## 5-6. 요구사항

1. **`BacktestRequest.strategy: str`** (Literal 제거) — `extra="forbid"` 유지.
2. **Legacy alias resolution** in POST handler:
   - `"sma"` → `"sma_v1"` (warn-log only).
3. **Strategy registry lookup**:
   - `STRATEGY_REGISTRY[strategy]` lookup → 미존재 시 422 `{detail: "unknown strategy: 'X'"}`.
4. **REQUIRED_DATA_TIERS 추출**:
   - lookup 후 `cls.REQUIRED_DATA_TIERS` 추출.
5. **Tier coverage 의무 호출** (T2/T3 인 경우만, T1 candle = 기존 path):
   - For each `tier ∈ REQUIRED_DATA_TIERS - {CANDLE}`:
     - `report = tier_coverage(root, exchange, symbol, tier, start, end)`
     - `report.min_ts_utc is None` → tier 데이터 부족 → 422
     - 부족 detail: `{missing_tiers: [...], available_window: {min, max}, requested_window: {start, end}}`
6. **422 response Pydantic**:
   - `BacktestValidationError(detail: dict)` with structured fields:
     - `unknown_strategy: str | None`
     - `missing_tiers: list[str] | None`
     - `available_window: {min_ts: ts, max_ts: ts} | None`
     - `requested_window: {start: ts, end: ts}`
7. **CANDLE only strategy** = 기존 path (BacktestRequest.fast/slow/strategy → SmaStrategy 직접 instantiation), tier coverage check 생략.
8. **Unit test 추가**:
   - 미등록 strategy → 422 with `detail.unknown_strategy`.
   - T2/T3 strategy + 데이터 부재 → 422 with `detail.missing_tiers`.
   - T2/T3 strategy + 일부 tier 만 존재 → 422 with `detail.missing_tiers` (정확 tier 명시).
   - Legacy `strategy="sma"` → 정상 dispatch (`sma_v1` registry hit).
   - candle-only strategy + 정상 데이터 → 기존 path (no tier coverage call).
9. **버전 bump**: mctrader-web 0.6.0 → 0.7.0.
10. **CI green** (ubuntu).

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: 기존 token + 127.0.0.1. registry lookup 은 process-local.
- **신규 file**: 없음 (모두 modify).
- **수정 file**: `models.py` / `routes.py` / `test_backtest.py`.
- **Reversible**: yes (legacy alias 유지로 rollback 가능).
