---
epic_key: MCT-63
status: closed
closed_at: 2026-05-05
related_adrs: ADR-002, ADR-004, ADR-005, ADR-006, ADR-009
---

# Epic MCT-63 — Tick + Orderbook Backtest

## Trigger

사용자 발화 (2026-05-04):
> "다른 전략들을 추가할 필요가 있다. 그에 앞서 orderbook, transaction_history는 candlestick과 달리 과거 데이터를 얻지 못할 건데 이건 어떻게 관리하는게 좋겠는가"
> "전략 중에 틱띠기나 마켓 메이킹에 대한 전략도 필요하거든"
> "지금은 예정된 작업들을 모두 수행하도록 하자."

3-tier market data 모델 (T1 candle / T2 tick / T3 orderbook event) 도입 + Tick scalping / Market making 전략 backtest 인프라.

## Phases

| Phase | PR | merge SHA | scope |
|---|---|---|---|
| Phase 1 | mctrader-hub#82 | d0e24d0 | Epic doc + 6 child Story stub + ADR-009 §D10 (tick.v1) + §D11 (orderbook.v1 L2 event stream) + ADR-005 §D6 (T2/T3 lookahead = received_at) |
| Phase 2 | mctrader-engine#17 | (squash merged) | MCT-64 Strategy registry + REQUIRED_DATA_TIERS frozenset + DataTier StrEnum + decorator + StrategyInfo (0.18.0) |
| Phase 3 | mctrader-data#5 | afec82f | MCT-65 collector run manifest persistence — CollectorManifest + derive_collector_run_id + write/read + selected_symbols 의무 (0.4.1) |
| Phase 4 | mctrader-data#6 | 4af0a76 | MCT-66 orderbook reconstruction utility — scan_ticks + scan_orderbook_events + get_orderbook_at + tier_coverage + fail-closed gap policy + bounded LRU cache + deterministic sort key (0.5.0) |
| Phase 5 | mctrader-engine#20 | dc4c37c | MCT-67 TickReplayExecutor — heap-merge driver + FIFO end-of-queue 보수적 matching + ADR-004 D3 5-stage latency + result manifest + 자기체결방지 별개 layer (0.21.0) |
| Phase 6 | mctrader-engine#21 | (squash merged) | MCT-68 strategy templates — TickScalpingStrategy ({TICK, ORDERBOOK}) + MarketMakingStrategy ({ORDERBOOK}) (0.22.0) |
| Phase 7 | mctrader-web#6 | (squash merged) | MCT-69 Web UI tick backtest — GET /strategies + GET /backtests/{id}/tick_detail (cursor pagination + downsample) + Streamlit selector + DATA_TIER badge (0.5.0) |
| Phase 8 (close) | mctrader-hub#TBD (this PR) | — | EPIC-RESULTS-MCT-63 + 7 child Story close + memory finalize |

**Single-day Epic** (2026-05-04 → 2026-05-05). 8 PRs across 4 repos (hub + engine + data + web).

## Codex review summary

**Phase 1 Codex review** (codex-rescue, gpt-5.5 high): 22 finding (F-1~F-22) Sonnet 채택.

| Category | Count | Outcome |
|---|---|---|
| MUST FIX before Phase 1 doc PR | 6 | 모두 ADOPT |
| MUST FIX before Phase 2-7 implementation | 7 | 모두 ADOPT (defer to children) |
| SHOULD CONSIDER | 6 | 모두 ADOPT (일부 PARTIAL) |
| NICE TO HAVE | 3 | 모두 ADOPT |

**ADR conflict 0/22**. Sonnet decider 24/24 escalation 0건.

## ADR amendments

- **ADR-009 §D10**: Tick stream v1 — schema_version="tick.v1", 8-col schema, daily Hive partition layout, forward-only invariant, `partition_id ↔ collector_run_id` 1:1 매핑, sort key `(ts_utc, received_at, file_offset)`
- **ADR-009 §D11**: Orderbook event stream v1 — schema_version="orderbook.v1", 10-col flat L2 events schema, reconstruction read API contract, fail-closed gap policy, §D9 L3 reservation 와 별개
- **ADR-005 §D6**: T2/T3 lookahead = `received_at` (row column-based, candle 의 §D6 lineage table 과 다른 mechanism)

## Backtest infrastructure delta

**Before Epic**:
- T1 (candle, ohlcv.v1) backtest only
- 단일 `Strategy` Protocol with `on_bar(ctx) -> Decision`
- BacktestExecutor (candle-based)
- Web UI: candle backtest control + result viewer

**After Epic**:
- 3-tier (T1 / T2 / T3) market data 모델
- `Strategy` Protocol 확장: `REQUIRED_DATA_TIERS: frozenset[DataTier]` ClassVar 의무 + `TickStrategy` / `OrderbookStrategy` callbacks (`on_tick` / `on_orderbook`)
- `STRATEGY_REGISTRY` + `@register_strategy("name")` decorator
- mctrader-data 의 `orderbook_replay` 모듈 — `scan_ticks` / `scan_orderbook_events` / `get_orderbook_at` / `tier_coverage`
- `TickReplayExecutor` (ADR-002 D2 mode invariant, ADR-004 D3 5-stage latency, FIFO end-of-queue 보수적 matching)
- 2 strategy templates (TickScalping + MarketMaking) — production strategy starting point
- Web UI: strategy class selector + DATA_TIER badge + tick_detail endpoint (cursor pagination)
- Collector run manifest: `<root>/market/manifest/run-{collector_run_id}.json` (replay reproducibility)

## Out-of-scope (확정 거부)

- Live mode tick execution (별도 후속 Epic)
- T2/T3 전략 ADR-006 WFO 적용 (별도 후속 Epic, 본 Epic 의 §13 + Codex F-15)
- Bithumb-faithful matching mirror (FIFO end-of-queue 보수적 simulation only, F-8)
- L3 depth-ladder snapshot (ADR-009 §D9 reservation 유지, Bithumb public WS = L2 only)
- Multi-exchange tick collection (v1 = Bithumb only)
- Cross-symbol portfolio strategy
- Tick-level WFO statistical correction (ADR-006 D8 비적용)
- TickReplayExecutor lifecycle wiring through web `/backtests` POST (v1 = endpoint contract only, full integration = 별도 후속 PR)

## Manual deployment prerequisite

본 Epic 의 모든 T2/T3 전략 backtest 는 **collector 가동 후 누적 기간 만큼만 가능**. 사용자 manual prereq:

1. Linux server 에 `mctrader-data` 0.5.0+ install
2. `mctrader-data collect --top-n 10 --include transactions,orderbook` (혹은 systemd unit)
3. 누적 1주 이상 후 backtest 가능 (T2/T3 데이터 충분량)

사용자 명시 (2026-05-04): "가동은 추후 하도록 하고" — 본 Epic 종료 후 별도 시점에 사용자가 수행.

## Numbering 충돌 해결

**Discrepancy** (Phase 1 시점 발견): Hub PR #74 (4664a4e, 22:31 KST WFO Execution Epic) 가 MCT-55~62 점유 + mctrader-data PR #4 (9f51fa0, 22:28 KST) commit 라벨 `[MCT-58]` stale.

**Resolution**: Tick + Orderbook Backtest Epic = MCT-63 (Epic) + MCT-64~MCT-69 (6 children). MCT-65 = mctrader-data PR #4 retroactive seal (MCT-12 패턴). 매핑표 = MCT-65.md 인라인.

## Total stop count

User stops: 1 (Phase 1 시작 시 "그냥 실행하면 안되나 무조건 yes" — Monitor permission 거부 → Bash polling 으로 전환)

## Related work

- MCT-12 (mctrader-data backfill retroactive seal, 패턴 동일)
- MCT-48 (Paper Runtime Ops + Web Mgmt) — web UI / lifecycle 패턴 재사용
- MCT-55 (WFO Execution) — 동일 시점 진행, MCT-58 numbering 충돌 발견 trigger
- MCT-37 (Lookahead lint L4 fixture) — ADR-005 §D6 amendment 의 `known_bias_t2t3_lookahead_simulated_clock_missing` future fixture point
