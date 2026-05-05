---
story_key: MCT-72
status: phase:요구사항
component: web
type: brainstorm
parent_epic: MCT-70
related_adrs: ADR-002
---

# MCT-72: BacktestLifecycleManager polymorphic dispatch — TickReplayExecutor branch

## 1. 사용자 요구사항 (verbatim, MCT-70 Epic Phase 1)

T2/T3 strategy 인 경우 `BacktestLifecycleManager._run_backtest` 가 TickReplayExecutor 로 dispatch.

## 2. 도메인 해석

MCT-70 child #2 = **lifecycle dispatch 분기**.

핵심 design:

- **Strategy.REQUIRED_DATA_TIERS 검사**: `{CANDLE}` 만 = 기존 BacktestExecutor path. `{TICK, ...}` 또는 `{ORDERBOOK, ...}` 또는 union 포함 = TickReplayExecutor path.
- **strategy instantiation**: registry lookup + template default param (v1, kwargs 미수락).
- **TickReplayExecutor 호출**: `(root, exchange, symbol, start, end, strategy, initial_cash)`.
- **결과 status 통일**: T1/T2/T3 모두 `BacktestStatus.lifecycle ∈ {queued, running, completed, error}` 동일.

## 3. 관련 ADR

- **ADR-002 D2** — 동일 Strategy callback API across modes. 본 dispatch 가 backtest-side enforcement.

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/api/
└── backtest_lifecycle.py   (MODIFY — _run_backtest polymorphic dispatch)

mctrader-web/tests/api/
└── test_backtest_lifecycle.py  (MODIFY — T2/T3 dispatch fixtures)
```

## 5-6. 요구사항

1. **Strategy lookup + tier inspection** in `_run_backtest`:
   - `cls = STRATEGY_REGISTRY[request.strategy]`
   - `tiers = cls.REQUIRED_DATA_TIERS`
2. **Dispatch 분기**:
   - `tiers == frozenset({DataTier.CANDLE})` → 기존 BacktestExecutor path (sma_v1 등). 기존 코드 유지.
   - else (T2/T3 포함) → TickReplayExecutor path.
3. **TickReplayExecutor path**:
   - Strategy instantiate: `cls()` (template default param)
   - `executor = TickReplayExecutor(root=data_root, exchange="bithumb", symbol=str(sym), start=start_dt, end=end_dt, strategy=strategy, initial_cash=Decimal(request.initial_capital))`
   - `result = await asyncio.to_thread(executor.run)` (sync TickReplayResult 반환)
   - Status update: `lifecycle="completed"`, `final_equity=str(result.final_cash + result.final_position_qty * top_bid_proxy)` (note: T2/T3 mark-to-market 은 MCT-73 에서 결정)
4. **Result manifest write**: `result.write(<run_dir>/manifest.json)` — MCT-73 에서 책임 (본 Story 는 dispatch 만).
5. **Error handling**: TickReplayExecutor 가 raise 한 ReconstructionError / GapDetectedError / TierCoverageError → `error_kind` 명시.
6. **Backward compat**: candle path 변경 0건 (sma_v1 등 기존 backtest 동일 결과).
7. **Unit test 추가**:
   - sma_v1 strategy → BacktestExecutor path (기존 동일).
   - tick_scalping_v1 → TickReplayExecutor path. 적재 데이터 부족 = error_kind 명시.
   - market_making_v1 (orderbook only) → TickReplayExecutor path.
8. **버전 bump**: mctrader-web 0.7.0 → 0.7.1 (또는 minor 0.8.0).
9. **CI green**.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: registry lookup process-local.
- **신규 file**: 없음.
- **수정 file**: `backtest_lifecycle.py` / 테스트.
- **Reversible**: yes (T1 path 보존).
