---
story_key: MCT-23
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-006, ADR-004, ADR-002
---

# MCT-23: Calibration metric + CLI integration acceptance + Paper E2E

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Calibration metric (Backtest vs Paper) + CLI integration + Paper E2E. **Epic close trigger**."

## 2. 도메인 해석

MCT-18 의 마지막 child = Epic close trigger. ADR-006 promotion gate (B→P→L) 의 calibration evidence 산출. C1~C5 metric 통계적 정의 + Backtest replay window matching + ExecutionReport extension + CLI duration/SIGTERM hardening + Paper E2E.

## 3. 관련 ADR

- ADR-006 (Promotion gate multi-metric AND, Paper artifacts = OOS validation evidence)
- ADR-004 (ExecutionReport schema 공유)
- ADR-002 (StrategyContext mode-agnostic verification)
- 의존: MCT-19 + MCT-20 + MCT-21 + MCT-22 freeze (모두)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── calibration/
│   ├── metric.py          # CalibrationMetrics (Pydantic v2)
│   ├── replay.py          # Backtest replay window matching
│   └── stats.py           # mean / p50 / p95 / max_abs
├── cli.py (extend)        # paper subcommand 완성 (--duration / --end / SIGTERM)
└── shutdown.py            # graceful shutdown sequence

mctrader-hub/
└── EPIC-RESULTS-MCT-18.md  # Epic close artifact

tests/
├── test_calibration_metrics.py
├── test_calibration_replay.py
├── test_paper_cli_integration.py
├── test_paper_shutdown.py
└── test_paper_e2e.py        # B1~B7 + C1~C5 통합
```

## 5-6. 요구사항

- ADR-006 multi-metric AND threshold 명시
- Backtest replay = 동일 historical period 의 동일 strategy 재실행
- POSIX SIGTERM + Windows SIGBREAK + asyncio.add_signal_handler

## 7. 설계 서사 (Codex 합성)

### 7.1 Calibration metric 통계 정의 + gate threshold (A1)

각 metric = `mean / p50 / p95 / max_abs` 기록, **gate = `abs_p95`** 사용.

**Gate threshold 권장 (MVP, calibration evidence 후 1회 조정 가능)**:

| Metric | Threshold | 의미 |
|---|---|---|
| `fill_price_deviation_bps.abs_p95` | < 20 bps | Paper fill vs Backtest assumption deviation |
| `realized_slippage_bps.abs_p95` | < 15 bps | composite slippage vs orderbook reality |
| `decision_to_fill_delay_ms.p95` | < 1000 ms | Paper execution path 품질 |
| `market_data_latency_ms.p95` | < 3000 ms | feed freshness (분리 측정) |
| `trade_count_delta` | ≤ 0.10 | abs(Paper - Backtest) / Backtest (division by zero handling) |
| `max_drawdown_delta` | ≤ 0.02 | absolute ratio point |

**Latency 분리 의무**: `decision_to_fill_delay_ms` (execution path) ≠ `market_data_latency_ms` (feed). 합치면 병목 진단 불가.

**Slippage reference price** = orderbook mid (microstructure 정확). last trade 비채택 (체결 방향 + 변동성 섞임).

**trade_count_delta division-by-zero**:
- `paper==0 && backtest==0` = 0
- `backtest==0 && paper>0` = hard fail (`null + violation`)

### 7.2 Backtest replay window matching (A2)

**채택**: option (a) 동일 historical period replay + (c) Paper aggregated bars artifact.

```python
def calibrate(paper_report: ExecutionReport, paper_root: Path) -> CalibrationMetrics:
    """
    1. paper_report 의 paper_started_at / paper_ended_at 추출
    2. 동일 window 의 historical OHLCV 로 Backtest 실행 (동일 strategy + config)
    3. Per-trade pair matching → fill_price_deviation 분포
    4. trade_count_delta + max_drawdown_delta 계산
    """
```

**Comparison metadata 명시** (fill model 차이 숨기지 않음):
- `backtest_fill_model = "next_bar_open"`
- `paper_fill_model = "simulated_fill_engine"`
- 차이 = report 명시, gate 해석 시 고려

**Paper aggregated bars artifact** = `paper_ohlcv.csv` (mctrader-data `mode=paper` partition + run_id 기반). future calibration 재현 가능 + 디버깅 강화.

### 7.3 ExecutionReport `summary.calibration_metrics` extension (A3)

**채택**: 혼합 — summary 에 compact pass/fail + 별도 `calibration_report.json` 상세.

```json
{
  "summary": {
    "calibration_metrics": {
      "status": "pass",
      "baseline_report_id": "bt-sma-KRW-BTC-1h-...-replay",
      "fill_price_deviation_bps": {"abs_p95": 18.4, "threshold": 20.0, "pass": true},
      "latency_ms": {
        "decision_to_fill": {"p50": 120, "p95": 600, "threshold_p95": 1000, "pass": true},
        "market_data": {"p50": 300, "p95": 1800, "threshold_p95": 3000, "pass": true}
      },
      "realized_slippage_bps": {"abs_p95": 9.2, "threshold": 15.0, "pass": true},
      "trade_count_delta": {"value": 0.04, "threshold": 0.10, "pass": true},
      "max_drawdown_delta": {"value": 0.01, "threshold": 0.02, "pass": true}
    }
  }
}
```

**Backtest single run** 도 `calibration_metrics: null` 허용 (ADR-004 schema 공유 보존).

**상세 분포** = `calibration_report.json` (per-trade matching, raw samples, unmatched orders) — Streamlit dashboard / 디버깅 용도.

### 7.4 CLI duration / --end mutually exclusive + SIGTERM hardening (A4)

```python
@click.option("--duration", type=str, default=None, help="e.g. 30m / 6h / 7d")
@click.option("--end", "end_iso", type=str, default=None, help="ISO 8601 UTC timezone-aware")
def paper(duration, end_iso, ...):
    if duration is not None and end_iso is not None:
        raise click.UsageError("--duration and --end are mutually exclusive")
    stop_at = _resolve_stop_at(duration, end_iso, clock=RealtimeClock())
    # internal stop_at = UTC datetime
```

**Graceful shutdown sequence** (deterministic order):
1. `shutdown_reason` 기록 (`duration_elapsed` / `end_reached` / `sigterm` / `risk_gate`)
2. New market-data decisions 중지
3. `open_orders` cancel 처리 + cancel event ExecutionReport 기록
4. Pending fills 생성 중단
5. Final equity snapshot 계산
6. ExecutionReport flush → `equity_curve.csv` flush → paper_storage flush durable write

**Signal handler** (cross-platform):
- POSIX `signal.SIGTERM` (Linux/macOS)
- Windows `signal.SIGBREAK` (Ctrl+Break)
- asyncio event loop 통합 (`add_signal_handler` Linux only, Windows = polling fallback)

### 7.5 Integration test = Hybrid (A5)

**채택**: option (c) JSONL fixture replay deterministic async iterator + 별도 thin WebSocket contract test.

```python
# test_paper_e2e.py
@pytest.mark.asyncio
async def test_paper_full_run_deterministic(tmp_path, clock_fixture, ws_jsonl_fixture):
    """
    1. JSONL fixture (MCT-19) → deterministic async MarketStream
    2. Clock injection (fixed sequence)
    3. PaperExecutor full run (BarAggregator → SmaStrategy → SimulatedFillEngine → VirtualPortfolio)
    4. ExecutionReport JSON + equity_curve.csv 산출
    5. mode=paper partition 산출 (paper_storage)
    6. RiskGate minimal trigger 검증 (forced low threshold)
    7. Shutdown via duration 만료 + final flush
    """

# test_ws_contract.py (별도)
def test_subscribe_and_heartbeat_sequence():
    """fake WS server = subscribe ack + market message + heartbeat → client = correct subscribe payload + pong + graceful close."""
```

**Random seed** = test config 고정 (jitter 없으면 N/A, 있으면 명시 record metadata).

### 7.6 Streamlit dashboard mode=paper filter (A6)

**채택**: option (a) MCT-23 = no UI change + (c) MCT-24 별도 Story 분리.

**MCT-23 Demonstration AC** = manual file inspection:
- ExecutionReport JSON `summary.calibration_metrics.status == "pass"`
- C1~C5 pass/fail
- `equity_curve.csv` 존재 + render 가능 (mctrader-web 기존)

**MCT-24 후보 stub** (future Epic 또는 별도 Story):
- mctrader-web 의 sidebar `mode in {historical, paper, live}` filter
- Paper report `calibration_metrics` badge / table 표시

### 7.7 Epic close PR trigger + 후속 candidate 우선순위 (A7)

**Close trigger**: B1~B7 + C1~C5 모두 pass + artifact path / command log 문서화.

**`EPIC-RESULTS-MCT-18.md` 의무 contents**:
- 실행 command (`mctrader-cli paper --strategy sma --symbol KRW-BTC --tf 1h --duration 7d ...`)
- Paper run window (start / end UTC)
- Backtest comparison window
- Report artifact 경로 (`out/{run_id}/execution_report.json` + `equity_curve.csv` + `calibration_report.json`)
- C1~C5 metric table (실제 측정값 + threshold + pass/fail)
- RiskGate 결과 (triggered_count + final_status)
- Known limitations (gate threshold 가설, ADR-007 minimal subset 등)

**C1~C5 중 미달 = close PR X, remediation issue 생성** (ADR-006 align).

**후속 candidate 우선순위 (Sonnet decider 자율 채택)**:

| 순위 | Epic | 근거 |
|---|---|---|
| 1 | **RiskGate full** (5 kill switch 모두) | 운영 안전성 우선 |
| 2 | **Lookahead lint** (L1 libcst + L4 known-bias fixture) | Backtest→Paper calibration 신뢰도 강화 |
| 3 | **WFO execution** | promotion 통계 기반 확장 |
| 4 | **Multi-symbol portfolio** | 실사용 범위 확장 (portfolio/risk 복잡도 증가) |
| 5 | **Multi-strategy registry** | orchestration / attribution complexity |
| 6 | **Live mode** | Paper gate + RiskGate full 안정화 후 |

### 7.8 Out-of-scope

- Streamlit dashboard mode filter (MCT-24)
- Production-grade resilience (network outage / DuckDB lock contention 등)
- WFO automation (promotion gate manual trigger 만)
- Live mode prep (1Password CLI / GitHub environment protection)

### 7.9 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | `CalibrationMetrics` Pydantic = mean/p50/p95/max_abs 기록 + gate `abs_p95` | pytest |
| AC2 | `latency_ms.decision_to_fill` ≠ `market_data` 분리 측정 | pytest |
| AC3 | `realized_slippage_bps` reference = orderbook mid | pytest |
| AC4 | `trade_count_delta` division-by-zero handling | pytest |
| AC5 | Backtest replay 동일 historical window + comparison_fill_model 명시 | pytest |
| AC6 | `summary.calibration_metrics` Pydantic schema (Backtest = null 허용) | pytest |
| AC7 | `calibration_report.json` 상세 분포 + per-trade matching | pytest |
| AC8 | CLI `--duration` + `--end` mutually exclusive + ISO 8601 UTC | pytest |
| AC9 | Graceful shutdown sequence (open_orders cancel + final flush 순서) | pytest |
| AC10 | SIGTERM (POSIX) + SIGBREAK (Windows) handler | pytest (subprocess) |
| AC11 | Paper E2E = JSONL fixture replay + Clock injection + ExecutionReport + paper_storage | pytest |
| AC12 | WebSocket contract test (subscribe ack + heartbeat + graceful close) | pytest |
| AC13 | B1~B7 + C1~C5 통합 테스트 (Epic close gate) | pytest |
| AC14 | `EPIC-RESULTS-MCT-18.md` 작성 + 5 child issue close (#25~#29) | manual + git |

### 7.10 Codex 적용

7/7 area 채택. ADR conflict 0/7. Sonnet decider 가 후속 candidate 우선순위 채택 (RiskGate full → Lookahead → WFO → Multi-symbol → Multi-strategy → Live).

## 8-11

(Phase 2 = calibration/* + cli paper 완성 + shutdown.py + AC1~AC14 + Epic close PR)
