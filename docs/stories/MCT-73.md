---
story_key: MCT-73
status: phase:완료
component: web
type: brainstorm
parent_epic: MCT-70
related_adrs: ADR-002, ADR-006
---

# MCT-73: TickReplayResult manifest persistence + /tick_detail real data wire + equity_curve post-process

## 1. 사용자 요구사항 (verbatim, MCT-70 Epic Phase 1)

TickReplayExecutor 결과를 `<run_dir>/manifest.json` 에 저장 + MCT-69 의 `/tick_detail` v1 stub 봉합 + fills 누적 → equity_curve.csv post-process (T1 schema 동일).

## 2. 도메인 해석

MCT-70 child #3 = **lifecycle artifact 봉합**.

핵심 design:

- **manifest.json persistence**: `TickReplayResult.write(path)` 호출. matching_model + collector_run_ids + symbol_manifests + latency_config + fills 모두 기록. 결정성 보장 (동일 input → 동일 hash).
- **`/tick_detail` 실 데이터 노출**: manifest 읽기 → fills cursor pagination + ts downsample 적용. v1 stub 봉합.
- **equity_curve post-process**: T2/T3 fills 누적 → ts × cash + position 시계열 → equity_curve.csv (T1 schema 동일). T1/T2/T3 통일된 후속 view.

## 3. 관련 ADR

- **ADR-002 D6** — execution result 의무 persistence (operational truth).
- **ADR-006** — reproducibility 의무 (T2/T3 buffer = collector_run_id chain, data_hash 부재 stream 특성).

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/api/
├── backtest_lifecycle.py   (MODIFY — manifest write 호출, equity_rows post-process)
└── routes.py               (MODIFY — /tick_detail v1 stub → manifest read + cursor + downsample)

mctrader-engine/src/mctrader_engine/executor/
└── tick_replay.py          (MODIFY — TickReplayResult.equity_rows() helper)

mctrader-web/tests/api/
└── test_strategies.py      (MODIFY — /tick_detail 실 데이터 fixture)
```

## 5-6. 요구사항

### Manifest persistence

1. **`<run_dir>/manifest.json`** write — `TickReplayResult.write(run_dir / "manifest.json")` 호출 (MCT-72 dispatch 직후).
2. **결정성 의무**: 동일 input → 동일 manifest content (sort_keys=True for JSON ordering deterministic).
3. **`<run_dir>/manifest.json` schema** (이미 MCT-67 정의): run_id / matching_model / strategy_class_name / symbol / window / source_collector_run_ids / final_position_qty / final_cash / fill_count / fills / latency_config.

### Equity curve post-process (T1 schema parity)

4. **`TickReplayResult.equity_rows() -> list[EquityRow]`** helper (mctrader-engine):
   - 시작 = `(start_ts, initial_cash, 0)` row
   - 각 fill 후 = `(fill.ts_utc, current_cash, current_position_qty)` row
   - 종료 = `(end_ts, final_cash, final_position_qty)` row
5. **`<run_dir>/equity_curve.csv`** write — T1 와 동일 6 column schema (ts_utc / cash / position_qty / equity / pnl / cumulative_pnl). equity = `cash + position_qty * mark_to_market_price`. mark_to_market = 마지막 알려진 top_bid (or close 가격, T2/T3 = last fill price proxy).
6. **MCT-72 dispatch 가 호출**: TickReplayResult → equity_rows → EquityCurveWriter.

### /tick_detail real data wire

7. **`GET /backtests/{id}/tick_detail`** v1 stub 봉합:
   - `<run_dir>/manifest.json` 읽기 → `fills: list[Fill]`
   - cursor parsing: cursor = base64(`{fill_index: int}`). 미주입 = 0.
   - downsample: `downsample_seconds > 0` 인 경우 ts-window 마다 1 sample.
   - limit: max [1, 10000].
   - response: `TickDetailResponse(points: list[TickDetailPoint], next_cursor, total_estimate)`.
8. **`TickDetailPoint`** 필드 채우기 (현재 schema):
   - `ts_utc` = fill.ts_utc
   - `fill_price` = str(fill.price)
   - `side` = fill.side
   - `own_qty` = str(fill.quantity)
   - `queue_position` = None v1 (manifest 에 미저장 — TickReplayExecutor 가 fill 시점 queue_position 기록 미구현 — 후속 work)
   - `book_top_bid` / `book_top_ask` = None v1 (book 시점 reconstruction 미저장 — 후속 work)
9. **404 / 422 동일**: 미존재 run = 404, invalid limit/downsample = 400.

### Tests

10. **manifest persistence** unit test: T2/T3 backtest 종료 후 manifest.json 존재 + 결정성.
11. **equity_curve post-process** unit test: T1 schema 동일 + 시작/fill/종료 row 정확.
12. **/tick_detail real data** unit test: cursor pagination + downsample 동작 + 빈 fills 의 경우 response.points = [].

### Common

13. **버전 bump**: mctrader-web 0.7.x → 0.8.0 / mctrader-engine (`equity_rows` helper) 0.27.0.
14. **CI green**.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: read-only manifest, token 의무.
- **신규 file**: 없음 (modify only).
- **수정 file**: `backtest_lifecycle.py` / `routes.py` / `tick_replay.py` / 테스트.
- **Reversible**: yes (additive).
- **Performance budget**: tick_detail 1 page < 10k row, response payload < 5MB. cursor pagination 보장.
