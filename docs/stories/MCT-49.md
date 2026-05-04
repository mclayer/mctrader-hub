---
story_key: MCT-49
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-002, ADR-005, ADR-007
---

# MCT-49: Paper CLI Runtime Gap Sealing — `mctrader-cli paper` E2E wiring

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

MCT-23 commit `4915029` 가 calibration / shutdown / risk extension library 만 추가, **`cli.py:178-211` paper command 는 MCT-21 시점 skeleton 그대로** (config print + "[paper] runtime hardening (SIGTERM / final flush) lands in MCT-23." 메시지만 출력 후 종료). MCT-18 + MCT-23 retroactive sealing.

## 2. 도메인 해석

MCT-48 child #1 = serialized first. 모든 후속 child (FastAPI / event store / RiskGate ack / Streamlit / evidence) 의 ground = "paper run 이 CLI 에서 실제 작동". 본 Story 종료 시 사용자가 다음 single command 로 7일 KRW-BTC 1h SMA(5,20) Paper run 시작 가능:

```
mctrader-cli paper --strategy sma --symbol KRW-BTC --timeframe 1h \
  --fast 5 --slow 20 --initial-capital 1000000 --duration 7d \
  --output-dir ./out
```

E2E flow:

1. CLI parse + validate (기존 skeleton 유지)
2. `BithumbWebSocketAdapter` instantiate (mctrader-market-bithumb, async)
3. `PaperExecutor` (mctrader-engine, sync TradeExecutor) + `BarAggregator` + `SimulatedFillEngine` + `PaperRiskGate`
4. AsyncTradeExecutor wrapper or asyncio.run loop bridging async WS feed → sync executor
5. `install_signal_handlers` (POSIX SIGTERM + Windows SIGBREAK + Ctrl+C)
6. graceful shutdown → `build_calibration_metrics` → `equity_curve.csv` + `execution_report.json` + `_lineage.json` + paper OHLCV partition (MCT-20 paper_storage) flush

MCT-51 event store wiring 은 후속 Story — MCT-49 는 기존 artifact (CSV/JSON) 그대로 유지 + lifecycle skeleton 만 정착.

## 3. 관련 ADR

- ADR-002 D2 (state isolation per run_id) / D6 (SQLite ledger — 본 Story 미적용, MCT-51 에서) / D9 (3-condition AND — Live only, Paper 는 wrapper N/A)
- ADR-005 L2/L3 (closed bar only / event log replay) — 기존 PaperExecutor 보존 verify
- ADR-007 PaperRiskGate (MAX_DAILY_LOSS + DRAWDOWN_LIMIT subset) integration

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── cli.py (MODIFY — paper command body 교체)
├── executor/
│   ├── paper.py (READ — 기존 PaperExecutor 사용)
│   ├── async_base.py (READ — AsyncTradeExecutor Protocol 확인)
│   └── components/
│       ├── bar_aggregator.py (READ)
│       └── simulated_fill_engine.py (READ)
├── shutdown.py (READ — install_signal_handlers / resolve_stop_at)
├── calibration/metric.py (READ — build_calibration_metrics)
└── risk/enforcer.py (READ — PaperRiskGate)

mctrader-market-bithumb/src/mctrader_market_bithumb/
└── ws/adapter.py (READ — BithumbWebSocketAdapter)
```

신규 file 후보: `mctrader-engine/src/mctrader_engine/runtime/paper_runner.py` (CLI ↔ executor wiring helper, async/sync bridge).

## 5-6. 요구사항

1. `mctrader-cli paper ...` 가 actual run 시작 (config print 후 종료 X). exit 0 = duration 만료 또는 SIGTERM graceful shutdown 후 final flush 성공.
2. SIGTERM / Ctrl+C 시 in-flight bar 마무리 + final flush + exit 0. Force kill (SIGKILL) 시 partial state 허용 (event store 도입 전 acceptable).
3. WebSocket disconnect → graceful stop + reason="WS_DISCONNECT" + exit 1 (비정상 종료 명시).
4. equity_curve.csv + execution_report.json + _lineage.json finalization 완료. paper OHLCV partition (mode=paper/) write 완료.
5. CLI E2E smoke test: `--duration 30s --max-events 10` mock WS feed (fixture) 으로 60초 내 완주. Calibration AC C5.
6. Unit test: PaperRunner async↔sync bridge / signal handler / WS disconnect path.
7. CI: mctrader-engine + mctrader-market-bithumb cross-repo Git+HTTPS install (ADR-010) + lint + pyright strict + pytest pass.
8. Host-wide single session lock: `~/.mctrader/paper.lock` (JSON: `{run_id, pid, started_ts}`) startup 시 확인 — 존재 + pid alive → exit 1 with conflict reason. 정상 종료 시 삭제. stale (pid dead) auto cleanup. MCT-50 FastAPI 도 동일 lock 적용 (host-wide enforce).

## 7. 보안 설계 / 11. 데이터 영향

- 보안: Paper = no secret. WebSocket public endpoint only. ADR-008 secret loader 미사용.
- 신규 file: `runtime/paper_runner.py` + `tests/test_paper_runner.py` + `tests/fixtures/ws_mock_feed.json`.
- 수정 file: `cli.py` paper command body. version bump engine 0.12.0 → 0.13.0.
- DB schema: 변경 없음 (event store 는 MCT-51).
- Reversible: yes (file revert 충분).
