---
story_key: MCT-67
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-002, ADR-004, ADR-005
---

# MCT-67: TickReplayExecutor + FIFO matching + ADR-004 latency model

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

T2/T3 backtest executor. Q3 user 채택: "추천대로(matching)" → FIFO end-of-queue 보수적 simulation. Codex F-5/F-7~F-9/F-13 push-back 반영: ADR-002 D2 mode invariant common API + 자기체결방지 + 보수적 simulation 명시 + ADR-004 D3 5단계 latency timing.

## 2. 도메인 해석

MCT-63 child #4 = **executor core**. 4 acceptance section:

1. **Replay driver** — `scan_ticks` + `scan_orderbook_events` heap-merge ASC ts dispatch.
2. **FIFO matching model** — LIMIT 큐 끝 join, MARKET top-of-book walk, partial fill / cancel-replace / 가격 레벨 disappearance / crossed book deterministic 처리.
3. **Latency model** — ADR-004 D3 5단계 timing.
4. **Provenance** — result manifest 에 source partition `collector_run_id` 다수 기록 + symbol manifest reference.

핵심 invariant:

- **ADR-002 D2** (F-5): `on_candle` / `on_tick` / `on_orderbook` Strategy callback API 가 Backtest / Paper / Live 모두 동일. 본 executor 가 backtest 측 dispatcher.
- **자기체결방지** (F-9): 시뮬레이션 주문 = 별개 layer (`SimulatedOrderBook`), 공개 호가 (`PublicOrderBook` 재구성 from MCT-66) 와 매칭 안 함. 자기 호가 ↔ 공개 호가 cross 시 = 자기 호가 fill (실제 거래소가 cross 시 매칭하므로).
- **보수적 simulation** (F-8): Bithumb-faithful 표방 거부. docstring + manifest 에 `matching_model: "fifo_eoq_conservative_v1"` 명시.

## 3. 관련 ADR

- **ADR-002 D2 / D6** — TradeExecutor Protocol 의무. event store SQLite (paper_event_store.v1) 재사용 (backtest mode 식별 via metadata). D6 SQL trigger append-only 동일 enforcement.
- **ADR-004 D3** — slippage / fee / latency 5단계 (decision/submit/exchange-arrival/ack/fill). exchange-arrival = queue placement 시각.
- **ADR-005** — lookahead 방어 = MCT-66 가 enforcement, 본 executor 는 caller 로서 `simulated_clock` 주입 의무.

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/executor/
├── __init__.py
├── tick_replay.py              (NEW — TickReplayExecutor core)
├── matching/
│   ├── __init__.py
│   ├── public_book.py          (NEW — reconstructed public book from MCT-66)
│   ├── simulated_book.py       (NEW — strategy 의 own orders)
│   ├── fifo_engine.py          (NEW — FIFO end-of-queue matching)
│   └── latency.py              (NEW — ADR-004 D3 5단계 timing)
├── manifest.py                 (NEW — result manifest writer)
└── exceptions.py               (NEW — MatchingError, LatencyConfigError)

mctrader-engine/tests/executor/
├── test_tick_replay_driver.py      (NEW — heap-merge 결정성)
├── test_fifo_matching.py           (NEW — partial fill / cancel-replace / disappearance)
├── test_latency_5stage.py          (NEW — D3 timing)
├── test_self_trade_prevention.py   (NEW — 자기체결방지)
├── test_mode_invariant.py          (NEW — ADR-002 D2 callback API parity)
└── test_result_manifest.py         (NEW — provenance)
```

## 5-6. 요구사항

### Section 1 — Replay Driver (B1~B4)

1. **`TickReplayExecutor(TradeExecutor Protocol)`** — `mctrader_engine.executor.tick_replay.TickReplayExecutor`.
2. **Driver loop**: `scan_ticks(symbol, start, end)` + `scan_orderbook_events(symbol, start, end)` heap-merge ASC `(ts_utc, received_at, file_offset)`. 결정성 의무.
3. **Strategy callback dispatch**: tick → `strategy.on_tick(t)` / orderbook → `strategy.on_orderbook(e)` / candle (optional, T1 fallback) → `strategy.on_candle(c)`.
4. **simulated_clock injection**: 매 step 마다 `simulated_clock = event.received_at` 주입 후 MCT-66 `scan_*` filter (lookahead 방어). 동일 clock 의 다중 event = stable order.

### Section 2 — FIFO Matching (B5~B12)

5. **`PublicOrderBook`** — MCT-66 `get_orderbook_at` 으로 매 event 시점 재구성. read-only.
6. **`SimulatedOrderBook`** — strategy own LIMIT orders. 별개 layer (F-9 자기체결방지).
7. **LIMIT order placement**: 제출 시각의 해당 가격 레벨 큐 끝 join. queue position = `사전_qty_at_level_P + own_pending`.
8. **LIMIT fill rule**: 매 incoming public book event 가 해당 레벨 qty 감소 시 → 큐 앞부분 (`사전_qty_at_level_P`) 부터 차감 → 0 도달 시 own order fill 시작 → 자기 own qty 만큼 fill (or partial).
9. **MARKET order**: top-of-book outward walk. partial fill 누적, 호가 부족 시 잔량 cancel + emit `PartialFillEvent`.
10. **Cancel-replace**: cancel = remove from queue, replace = priority reset (queue 끝 새로 join).
11. **가격 레벨 disappearance**: 해당 레벨 의 모든 public + own qty 가 disappear 시 own order 자동 cancel + emit `OrderCancelledEvent(reason="level_disappeared")`.
12. **Crossed book**: bid >= ask (data anomaly) 발생 시 = halt + emit `MatchingError`. silent skip 거부.

### Section 3 — Latency Model (B13~B16)

13. **ADR-004 D3 5단계 timing**:
   - `decision_time` = strategy callback return 시각
   - `submit_time` = `decision_time + decision_delay` (configurable)
   - `exchange_arrival_time` = `submit_time + network_delay` ← **queue placement 시각** (F-13)
   - `ack_time` = `exchange_arrival_time + exchange_processing` 
   - `fill_time` = `ack_time + matching_delay`
14. 각 단계 delay = config dict, default = ADR-004 D3 baseline (e.g., decision=0ms, network=20ms, exchange=10ms, matching=5ms — placeholder, ADR-004 spec 참조).
15. queue placement 시 **다른 simulated/public order 가 동일 가격 레벨 에 동일 시각 도착** 시 tie-break = `(submit_time, decision_time, order_id)` deterministic.
16. submit 시 already-arrived public events 위에 placement (실제 거래소 같이 시간 순).

### Section 4 — Provenance (B17~B19)

17. **Result manifest** (`<run_dir>/manifest.json`):
    ```
    {
      "run_id": "...",
      "matching_model": "fifo_eoq_conservative_v1",
      "strategy_class": "...",
      "strategy_required_data_tiers": ["tick", "orderbook"],
      "symbol": "KRW-BTC",
      "window": {"start": "...", "end": "..."},
      "source_partitions": [
         {"tier": "tick", "collector_run_id": "...", "date": "...", "schema_version": "tick.v1"},
         {"tier": "orderbook", "collector_run_id": "...", "date": "...", "schema_version": "orderbook.v1"},
         ...
      ],
      "symbol_manifests": ["<MCT-65 manifest path or hash>"],
      "latency_config": {...},
      "result_metrics": {...}
    }
    ```
18. 동일 input 재실행 = 동일 manifest hash (결정성 의무).
19. ADR-006 reproducibility 동등 (T2/T3 제한적 — `data_hash` 부재 stream 특성, `collector_run_id` chain 으로 대체).

### Section 5 — Common (B20~B23)

20. **자기체결방지 unit test** (F-9): 자기 LIMIT bid + 자기 LIMIT ask 가 cross 시 양 order 모두 cancel + emit + position 변동 없음.
21. **mode invariant unit test** (F-5): 동일 Strategy class 가 backtest (`TickReplayExecutor`) + paper (`PaperRunner` MCT-49) + live (별도 Epic) 에서 동일 callback 호출 시 동일 동작.
22. **보수적 simulation 명시**: docstring `"FIFO end-of-queue conservative simulation; not a Bithumb-faithful matching mirror"` + manifest `matching_model` field.
23. **버전 bump**: mctrader-engine 0.19.0 (MCT-64) → 0.20.0.
24. **CI green**.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: backtest = simulated only, no live API. Result manifest = local file.
- **신규 file**: `executor/tick_replay.py` + `matching/*.py` + `manifest.py` + tests (~6 file).
- **수정 file**: 없음 (모두 신규 모듈).
- **Reversible**: yes (executor 추가 = backward-compat. 기존 candle backtest executor 기존 유지).
- **Performance**: top-1 symbol 1일 = 추정 200만 event. heap-merge O(N log N). FIFO matching = O(M) per event (M = own pending order, 일반 < 10). 600초 smoke target (B C5, MCT-69 측 measure).
