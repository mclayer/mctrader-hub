---
story_key: MCT-70
status: phase:완료
component: epic
type: epic
parent_epic: null
related_adrs: ADR-002, ADR-006, ADR-009
---

# MCT-70 (Epic): T2/T3 Backtest Lifecycle Integration — TickReplayExecutor wire-through web

## 1. 사용자 요구사항 (verbatim, 2026-05-05)

> "진행해라"

선행 context: Epic MCT-63 (Tick + Orderbook Backtest, 8 PR) 종료 시 명시적으로 deferred:

> "TickReplayExecutor lifecycle wiring through web `/backtests` POST (v1 = endpoint contract only)"

MCT-69 의 `02_backtest_panel.py` strategy selector 가 `tick_scalping_v1` / `market_making_v1` 을 노출하지만 `POST /backtests` 는 `Literal["sma"]` strategy 만 수락 → T2/T3 전략은 selector 에서 선택해도 422. **Engine capability 존재 + UI 노출 ↔ 실제 dispatch 미연결** = Codex F-debt: largest API/product mismatch.

## 2. 도메인 해석

mctrader 9번째 implementation Epic = **MCT-63 의 deferred obligation 봉합** + UI 에서 T2/T3 전략 backtest 실제 실행 가능.

핵심 framing (Codex 7-area review + Sonnet 합성):

- **Engine capability → UI usability gap closure.** TickReplayExecutor 는 직접 Python call 로만 reachable. 본 Epic 으로 `POST /backtests` + Streamlit 표준 UI surface 로 routing.
- **BacktestLifecycleManager polymorphic dispatch.** 현 `_run_backtest` 는 `BacktestExecutor` (T1) 단일 hard-wired. 본 Epic 으로 `Strategy.REQUIRED_DATA_TIERS` lookup → `BacktestExecutor` (T1 only) vs `TickReplayExecutor` (T2/T3) 분기.
- **Tier coverage 422.** `/backtests` POST 시 `tier_coverage(symbol, tier, start, end)` (MCT-66) 호출 → 부족 시 422 with `detail.missing_tiers + missing_window`. Backtest 시작 전 fail-fast.
- **Result manifest lifecycle.** TickReplayExecutor `manifest.json` (matching_model + collector_run_ids + symbol_manifests + latency_config) 를 `<output_dir>/<run_id>/` 에 persist. ADR-006 reproducibility 의 T2/T3 buffer (data_hash 부재 stream → collector_run_id chain).
- **`/tick_detail` 실 데이터 노출.** MCT-69 의 v1 stub (빈 페이지) → `TickReplayResult.fills` 를 cursor pagination + downsample 으로 노출.
- **Streamlit tick result viewer.** trade list + per-fill orderbook context + queue position chart + book mini-ladder.
- **Multi-strategy params 거부.** v1 = template default param 만. strategy-specific param injection 은 별도 후속 Epic (MCT-68 templates 의 `__init__` kwargs 를 BacktestRequest 에 expose).

본 Epic 은 MCT-41 (Live Mode) / MCT-55 (WFO) / MCT-63 와 **별도 lane**:

- MCT-41 = manual prereq blocked (1Password / Bithumb live key)
- MCT-55 = closed (WFO 자동 실행 도구)
- MCT-63 = closed (T2/T3 capability)
- MCT-70 = MCT-63 의 deferred obligation only, manual prereq 0건

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Codex 7-area review (codex-rescue, gpt-5 high, 2026-05-05)

**TOP RECOMMENDATION**: T2/T3 Backtest Lifecycle Integration. Codex grounding:
- `EPIC-RESULTS-MCT-63.md` 의 Out-of-scope 명시 항목
- `MCT-69.md` spec 이 `POST /backtests` strategy_name 의무 + tier coverage 422 명시했으나 미구현
- `MCT-67.md` manifest schema 정의 + lifecycle persistence 미연결

**Codex DEBT WARNING**:
1. API/product mismatch — T2/T3 전략 직접 Python only, UI surface 미연결
2. Result reproducibility — manifest schema 정의 vs lifecycle ownership 분리
3. **L3 depth-ladder 거부** (Bithumb public WS = L2 only, hard external constraint)

### Sonnet decider Phase 1 (12 sub-decision batch, 2026-05-05)

| # | Decision | Pick | 근거 |
|---|----------|------|------|
| A | Dispatch logic 위치 | A1 — `BacktestLifecycleManager._run_backtest` 내 if/else | 단일 책임, polymorphism v1 거부 (premature) |
| B | Tier coverage check 위치 | B1 — POST handler 진입 시 (executor 호출 전) | fail-fast, 큐잉 비용 회피 |
| C | Coverage 부족 응답 | C1 — 422 + `detail.missing_tiers + missing_window` | client-actionable |
| D | Strategy param injection v1 | D1 — template default only (kwargs 미수락) | scope 단순, MCT-68 default 충분 |
| E | T2/T3 backtest window default | E1 — last 1d UTC (collector 누적 여부 caller 책임) | Backtest 측 책임 분리 |
| F | Result manifest path | F1 — `<output_dir>/<run_id>/manifest.json` | T1 `execution_report.json` 와 parallel |
| G | tick_detail data source | G1 — manifest 의 `fills` field 직접 read | TickReplayResult.fills 가 source of truth |
| H | tick_detail pagination strategy | H1 — fill index based cursor + ts downsample | F-22 정합 |
| I | Streamlit T2/T3 viewer | I1 — 같은 `02_backtest_panel.py` 에 conditional render | 별도 page 분리 거부 (UX consistency) |
| J | Backward compat | J1 — `strategy="sma"` legacy 라벨 유지 (sma_v1 alias) | 기존 web 호출 미파괴 |
| K | Capital allocation T2/T3 | K1 — `initial_capital` 그대로 → TickReplayExecutor 의 ctx._cash | 기존 패턴 재사용 |
| L | Equity curve T2/T3 | L1 — fills 누적 → equity_rows 변환 (post-process) | 기존 EquityCurveWriter 재사용 |

12/12 escalation 0건. Sonnet decider auto-proceed (사용자 "진행해라" trigger).

## 4. Child Story decomposition

| Story | repo | scope | 의존 |
|---|---|---|---|
| **MCT-71** BacktestRequest tier-aware extension + 422 coverage validation | mctrader-web | `BacktestRequest.strategy: str` (Literal 제거, registry lookup) + `Pydantic v2 strict` + POST handler 가 `STRATEGY_REGISTRY` lookup + `REQUIRED_DATA_TIERS` 추출 → T2/T3 인 경우 `tier_coverage(symbol, tier, start, end)` 호출 → 부족 시 422 with detail. Legacy `strategy="sma"` → `sma_v1` alias. | MCT-66 + MCT-69 (이미 main) |
| **MCT-72** BacktestLifecycleManager polymorphic dispatch | mctrader-web | `_run_backtest` 분기: `REQUIRED_DATA_TIERS` 가 `{CANDLE}` 만 → 기존 `BacktestExecutor` path 유지 (sma_v1 등). `{TICK, ORDERBOOK}` 등 = `TickReplayExecutor(root, exchange, symbol, start, end, strategy)` path. ctx._cash = `initial_capital` 주입. | MCT-71 + MCT-67 (이미 main) |
| **MCT-73** Result manifest persistence + /tick_detail wire | mctrader-web + mctrader-engine | `TickReplayResult.write(<run_dir>/manifest.json)` 호출. `/backtests/{id}/tick_detail` v1 stub → 실 fills 노출 (manifest 읽어서 cursor + downsample 적용). MCT-69 의 빈 페이지 stub 봉합. equity_rows post-process (fills → equity_curve.csv) → 기존 EquityCurveWriter 재사용. | MCT-72 |
| **MCT-74** Streamlit tick result viewer + Epic close | mctrader-web + mctrader-hub | `02_backtest_panel.py` conditional render: T1 (candle) 결과 = 기존 chart. T2/T3 결과 = trade list + per-fill orderbook context (queue_position chart + top-of-book + own_qty). `/tick_detail` API 호출 + downsample slider. EPIC-RESULTS-MCT-70 + child Story close. | MCT-73 |

### Ordering 의무

- **MCT-71 = serialized first** (BacktestRequest schema + 422 validation — POST 입구)
- **MCT-72 = MCT-71 후** (dispatch 가 schema 의무 사용)
- **MCT-73 = MCT-72 후** (manifest persistence 가 dispatch 의무)
- **MCT-74 = MCT-73 후** (UI viewer 가 manifest + /tick_detail 의무)

## 5-6. 요구사항

### Blocking AC (B1~B10)

| # | AC | 충족 시점 |
|---|-----|----------|
| B1 | `BacktestRequest.strategy: str` (Literal 제거) + Pydantic v2 strict + 미등록 strategy = 422 with `detail.unknown_strategy` | MCT-71 |
| B2 | POST `/backtests` 가 strategy 의 `REQUIRED_DATA_TIERS` 추출 + T2/T3 인 경우 `tier_coverage` 호출 → 부족 시 422 with `detail.missing_tiers + missing_window` | MCT-71 |
| B3 | Legacy `strategy="sma"` → `sma_v1` alias 자동 적용 (기존 web client 무파괴) | MCT-71 |
| B4 | `BacktestLifecycleManager._run_backtest` polymorphic dispatch: T1 = BacktestExecutor (기존), T2/T3 = TickReplayExecutor | MCT-72 |
| B5 | TickReplayExecutor 사용 시 `initial_capital` 주입 + `data_root` resolve (MCTRADER_DATA_ROOT 동일) | MCT-72 |
| B6 | T2/T3 backtest 결과 `<output_dir>/<run_id>/manifest.json` (matching_model + collector_run_ids + symbol_manifests + latency_config + fills) persist | MCT-73 |
| B7 | T2/T3 fills 누적 → `equity_curve.csv` post-process (T1 와 schema 동일) | MCT-73 |
| B8 | `GET /backtests/{id}/tick_detail` 실 데이터 노출 (manifest 읽기 + cursor pagination + ts downsample) | MCT-73 |
| B9 | Streamlit `02_backtest_panel.py` conditional render: T1 = 기존 chart, T2/T3 = trade list + queue_position chart + book mini-ladder | MCT-74 |
| B10 | EPIC-RESULTS-MCT-70 + 4 child Story close (status=`phase:완료`) + memory finalize | MCT-74 |

### Calibration AC (C1~C3)

| # | metric | 의미 | 채택 |
|---|--------|------|------|
| C1 | T2/T3 backtest with insufficient coverage = 422 deterministic (`detail.missing_tiers` non-empty) | F-12 contract 의무 | MCT-71 |
| C2 | T2/T3 backtest result manifest = `model_validate_json` strict pass + `matching_model="fifo_eoq_conservative_v1"` 명시 | F-8 conservative simulation 명시 | MCT-73 |
| C3 | T2/T3 backtest E2E smoke `tick_lifecycle_smoke_duration_seconds < 600` (1d fixture × top-1 symbol, registry → 422 → executor → manifest → tick_detail GET) | E2E 회귀 방지 | MCT-74 (Epic close) |

### Demonstration AC (D1)

D1 = Streamlit `02_backtest_panel.py` 가 T2/T3 strategy backtest 시작 + 결과 viewer (trade list + queue_position chart) 노출 = **MCT-74 deliverable**.

## 7. 보안 설계

- **§7.1 Trust boundary**: 기존 MCT-48 / MCT-50 패턴 유지. FastAPI 127.0.0.1 + `~/.mctrader/local_token` 동일.
- **§7.2 Threat model**: T2/T3 backtest = 적재 data only (Bithumb 도착 후 collector persistence 된 데이터). live API 호출 없음.
- **§7.3 Auth/authz**: localhost token (single user). `/tick_detail` read-only token 의무.
- **§7.4 OpRisk**: T2/T3 backtest CPU+memory bound (top-1 symbol 1일 ≈ 200만 event). 기존 BacktestLifecycleManager N concurrent 한도 재사용.
- **§7.5 민감 데이터**: 없음 (public Bithumb data).

## 8. 테스트 / 11. 데이터 영향

### 신규 file (Phase 1)

- `docs/stories/MCT-70.md` (Epic, 본 file)
- `docs/stories/MCT-71.md` ~ `MCT-74.md` (4 child Story stub)

### 수정 file (Phase 2+)

- `mctrader-web/src/mctrader_web/api/models.py` — `BacktestRequest.strategy: str` Literal 제거 + tier_validation hook — MCT-71
- `mctrader-web/src/mctrader_web/api/routes.py` — `POST /backtests` tier coverage 의무 호출 + 422 변환 — MCT-71
- `mctrader-web/src/mctrader_web/api/backtest_lifecycle.py` — `_run_backtest` polymorphic dispatch — MCT-72
- `mctrader-web/src/mctrader_web/api/routes.py` — `/tick_detail` v1 stub 봉합 — MCT-73
- `mctrader-web/src/mctrader_web/dashboard/pages/02_backtest_panel.py` — conditional render T1/T2/T3 + tick result viewer — MCT-74

### DB schema / migration

- 신규 schema: 없음. T2/T3 manifest = file-based JSON.
- 기존 `BacktestStatus` 모델 재사용 (lifecycle/started_at/finished_at/run_id).

### Reversible

- Phase 1 doc = yes.
- Phase 2-5 implementation = yes (file revert + 0 cost rollback).

## 12. Sonnet Decision Log

| packet_id | trigger | options_count | decider_pick | override? | audit_result | timestamp |
|-----------|---------|---------------|--------------|-----------|--------------|-----------|
| MCT-70-Phase1-12dec | substantive-multi-decision-batch | 12 sub × 2~3 options | A1/B1/C1/D1/E1/F1/G1/H1/I1/J1/K1/L1 | no | direct | 2026-05-05Z (Codex top-recommendation + Sonnet 합성) |

12/12 escalation 0건.

## 13. Out-of-scope (확정 거부)

- Strategy-specific param injection via API (v1 = template default only)
- Multi-strategy single backtest (별도 후속 Epic)
- L3 depth-ladder snapshot (ADR-009 §D9 reservation, Bithumb public WS = L2)
- T2/T3 ADR-006 WFO promotion (별도 후속 Epic)
- Live mode tick execution (별도 후속 Epic)
- TickReplayExecutor cancel via DELETE /backtests (T2/T3 sync run 단순성 v1)
- Cross-symbol portfolio T2/T3 backtest (별도 후속 Epic)
- WebSocket / SSE push for tick_detail streaming (cursor polling v1)
- Strategy registry hot-reload (process restart required v1)
- T2/T3 backtest paper-mode parity (Paper tick callback = 별도 후속 Epic)
- Custom matching_model selection via API (v1 = fifo_eoq_conservative_v1 only)
