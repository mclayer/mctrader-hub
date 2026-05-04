---
story_key: MCT-51
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-002, ADR-005, ADR-009
---

# MCT-51: SQLite Event Store + NDJSON Export — operational truth (ADR-002 D6 align)

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

ADR-002 D6 = "SQLite append-only event log = Paper operational truth". MCT-18 이 artifact (CSV/JSON) 를 truth 로 잘못 정착 — MCT-51 정정.

## 2. 도메인 해석

MCT-48 child #3. event sourcing transition 의 핵심 Story. PaperExecutor + PaperRiskGate + BarAggregator + SimulatedFillEngine 의 모든 substantive event 가 SQLite append-only table 로 기록됨. 11 event 모델 (Pydantic v2):

| Event | producer | 핵심 field |
|---|---|---|
| `LifecycleEvent` | PaperRunner | run_id / phase (start/stop/error) / reason / timestamp |
| `ClosedBarEvent` | BarAggregator | run_id / symbol / tf / open_ts / close_ts / OHLCV / source_hash |
| `OrderIntentEvent` | PaperExecutor | run_id / order_id / symbol / side / qty / price (limit) / order_type |
| `OrderEvent` | PaperExecutor | run_id / order_id / status_from / status_to / reason / fill_qty / fill_price |
| `FillEvent` | SimulatedFillEngine | run_id / order_id / fill_qty / fill_price / slippage_bps / fee_krw / latency_ms |
| `RiskDecisionEvent` | PaperRiskGate | run_id / trigger_name / severity / reason / current_metric / threshold |
| `EquitySnapshotEvent` | PaperExecutor | run_id / timestamp / equity_krw / cash_krw / position_qty / position_value_krw |
| `LatencyEvent` | PaperRunner | run_id / sample_kind (market_data / decision_to_fill / public_endpoint_rtt) / ms |
| `MarketDataFreshnessEvent` | BithumbWebSocketAdapter | run_id / last_message_ts / staleness_ms |
| `CalibrationProgressEvent` | PaperRunner | run_id / metric_name / value / threshold / pass |
| `OperatorActionEvent` | FastAPI / CLI | run_id / actor / action (start/stop/risk_ack) / reason / timestamp |

## 3. 관련 ADR

- **ADR-002 D6** — SQLite append-only event log 의무 명시 (이미 채택, MCT-51 = 실제 implementation)
- ADR-005 L3 (event log replay 기반 lookahead 검증)
- ADR-009 분리 — paper event store ≠ paper OHLCV partition. 전자 = SQLite operational, 후자 = Parquet historical.

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── event_store/
│   ├── __init__.py (NEW)
│   ├── schema.py (NEW — 11 Pydantic v2 모델 + canonical SQL DDL)
│   ├── writer.py (NEW — append-only, single writer per run)
│   ├── reader.py (NEW — query / since(seq) tail / status reconstruct)
│   ├── migration.py (NEW — schema_version paper_event_store.v1)
│   └── ndjson_export.py (NEW — finalization NDJSON dump)
└── runtime/paper_runner.py (MODIFY — emit events at lifecycle hooks)

mctrader-data/src/mctrader_data/
└── paper_event_store/ (NEW — read-only access path for evidence bundle MCT-54)
```

## 5-6. 요구사항

1. SQLite per run: `{output_dir}/{run_id}/event_store.sqlite`. **Master `events` table + 11 detail (Codex push-back)** + `schema_version` table (1 row, `paper_event_store.v1`). Master 가 global monotonic `seq` autoincrement 보장.
2. Append-only: writer = singleton per run, 모든 event INSERT only. **UPDATE/DELETE 절대 금지 — writer 메서드 제한 + SQL trigger (`events_block_update` / `events_block_delete`) 양쪽 enforce (D3)**.
3. Sequence: 모든 event = monotonic `seq` (master autoincrement) + `event_uuid` (uuid4) + `timestamp_utc`.
4. Pydantic v2 strict: 모든 event 의 `model_validate_json` strict mode pass. Decimal38_18 / UTCDateTime annotated 재사용.
5. Status reconstruction: `EventStoreReader.reconstruct_status(run_id) -> RunStatus` = LifecycleEvent latest + EquitySnapshotEvent latest + open OrderEvent set + active RiskDecisionEvent severity. Process restart 후 정확 reconstruction.
6. Tail query: `events_since(run_id, seq) -> list[Event]` for FastAPI `/runs/{id}/events?since=N` (MCT-50 stub 의 wire 완성).
7. NDJSON export: finalization 시 `event_store.sqlite` → `events.ndjson` (gzip optional). 기존 ExecutionReport.json 은 derivative summary 로 격하 (MCT-54 evidence bundle 의 input).
8. Test: 11 event 각 round-trip / strict reject / replay status reconstruction / append-only enforcement / single-writer enforcement.

### Codex push-back amendments (Phase 3 implementation 시 채택)

- **`MarketDataFreshnessEvent` producer** 는 본 Story 에서 **schema + writer-acceptance 만 제공**. Bithumb WebSocket stream 에 freshness 노출이 없으므로 actual emitter (wrapper / observer) 는 별도 후속 small Story (MCT-50/MCT-53 freshness 표시 시점) 로 deferred.
- **`ClosedBarEvent.source_hash`** 는 timestamp proxy 금지. `closed_bar_source_hash(symbol, timeframe, open_ts, close_ts, OHLCV)` 의 SHA-256 deterministic helper 제공 — 가짜 hash 가 audit 의 false confidence 야기 회피.
- **mctrader-data dependency**: Phase 3 에서는 engine-only. data 측 read 경로는 MCT-54 evidence bundle 시점에 추가 (premature dep 회피).

## 7. 보안 설계 / 11. 데이터 영향

- 보안: SQLite file = local filesystem only. file mode 600. operator action event 는 actor field 기록.
- 신규 file: 위 §4 module + tests/test_event_store_*.py.
- 수정 file: paper_runner.py emit hooks. version bump engine 0.13.0 → 0.14.0, data 0.3.0 → 0.4.0.
- DB schema: paper_event_store.v1 정착. ADR-009 OHLCV 와 별도 namespace, 충돌 없음.
- Reversible: SQLite file delete 충분.
