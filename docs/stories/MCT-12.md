---
story_key: MCT-12
status: phase:요구사항
component: hub
type: epic
related_stories: MCT-13, MCT-14, MCT-15, MCT-16, MCT-17
related_adrs: ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-12: Bithumb OHLCV → SMA backtest end-to-end (Epic)

## 1. 사용자 요구사항 (verbatim)

> "Epic MCT-12 (Bithumb OHLCV → SMA backtest end-to-end)"

> Child Story = MCT-13 (mctrader-market interface) → MCT-14 (Bithumb adapter) → MCT-15 (data daemon 7일 백필) → MCT-16 (BacktestExecutor + SMA + 결과) → MCT-17 (Streamlit equity curve)

## 2. 도메인 해석

mctrader 의 **첫 implementation Epic**. ADR-001~011 의 baseline 결정을 5 repo 에 첫 적용하여 **Bithumb 7일 OHLCV → SMA backtest → Streamlit equity curve** 한 번 관통 (proof of platform).

목적은 "통과한다" 의 검증이 아닌 **"6 repo invariant + 도메인 ADR + Candle Protocol contract + lookahead bias 검증 + ExecutionReport schema 가 모두 일관된 한 번의 path 를 만든다"**. 즉 첫 E2E 가 향후 Paper/Live/multi-strategy/WFO 의 baseline 이 됨.

ADR-006 promotion gate 의 **Backtest 단계 1 차 완성** = MCT-12. Paper/Live 진입은 이 Epic 의 후속 별도 Epic 결정.

## 3. 관련 ADR

- ADR-001 (거래소 = Bithumb#1) — symbol = `KRW-BTC`
- ADR-002 (TradeExecutor Protocol + 3 mode) — BacktestExecutor 가 Backtest mode 구현
- ADR-003 (Backtest engine self-built core) — lib adapter 미사용, BacktestExecutor 직접 구현
- ADR-004 (Slippage/Fee/Latency + ExecutionReport schema) — Backtest 의 fee/slippage 모델 + report 출력
- ADR-005 (Lookahead bias 4-layer) — SMA signal 검증 의무
- ADR-006 (WFO + Promotion gate) — Backtest 1 단계 완성
- ADR-007 (RiskGate) — minimal pass-through hook only (full integration 별도 Epic)
- ADR-008 (Secret) — Backtest = secret access 금지 (public OHLCV endpoint only)
- ADR-009 (OHLCV v1 schema + Candle Protocol) — 데이터 저장 / 거래소 normalization 의 contract
- ADR-010 (Python 3.11 + uv + 6 repo install) — repo 생성 + dependency wiring 의 정책
- ADR-011 (Branch protection + CI standard) — 5 신규 repo 의 첫 commit 표준

## 4. 관련 코드 경로

새로 생성될 5 repo (parent dir = `c:\workspace\mclayer\`):

```
mctrader-market/                  # MCT-13 (interface)
├── pyproject.toml
└── src/mctrader_market/
    ├── protocol.py               # Candle/OrderBook/Order Protocol (PEP 544)
    ├── types.py                  # Decimal-based types
    └── __init__.py

mctrader-data/                    # MCT-15 (storage daemon)
├── pyproject.toml
└── src/mctrader_data/
    ├── schema.py                 # ADR-009 v1 16-column canonical
    ├── storage.py                # Parquet/DuckDB write/read
    ├── daemon.py                 # 7일 backfill CLI
    └── __init__.py

mctrader-market-bithumb/          # MCT-14 (adapter)
├── pyproject.toml
└── src/mctrader_market_bithumb/
    ├── client.py                 # HTTP client (public OHLCV endpoint)
    ├── adapter.py                # CandleProvider impl
    └── __init__.py

mctrader-engine/                  # MCT-16 (executor + strategy + CLI)
├── pyproject.toml
└── src/mctrader_engine/
    ├── executor/
    │   └── backtest.py           # BacktestExecutor
    ├── strategy/
    │   └── sma.py                # SMA fast/slow crossover
    ├── lookahead.py              # ADR-005 4-layer wrappers
    ├── report.py                 # ExecutionReport / equity_curve
    ├── cli.py                    # `mctrader-cli backtest ...`
    └── __init__.py

mctrader-web/                     # MCT-17 (Streamlit dashboard)
├── pyproject.toml
└── src/mctrader_web/
    ├── app.py                    # Streamlit equity curve
    └── __init__.py
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11 / uv / pydantic v2 (boundary only) / Decimal canonical
- DuckDB / Parquet / pyarrow (storage)
- httpx 또는 aiohttp (Bithumb HTTP)
- streamlit (UI)
- ruff / pyright / pytest / pytest-cov / pre-commit / gitleaks

## 7. 설계 서사 (요약)

### 7.1 End-to-end acceptance (2 layer)

**Blocking AC** (Epic 완료 필수):

| # | AC | 검증 도구 |
|---|---|---|
| B1 | CLI `mctrader-cli backtest --strategy sma --symbol KRW-BTC --tf 1h --start <T-7d> --end <T>` 종료 코드 = 0 | bash exit code |
| B2 | ExecutionReport JSON 산출, ADR-004 schema validation 통과 | pydantic v2 validator |
| B3 | `equity_curve.csv` 산출, schema validation 통과 (timestamp UTC + equity Decimal) | pydantic v2 + pandera |
| B4 | OHLCV input data 가 ADR-009 v1 16-column Decimal(38,18) Hive UTC partition 통과 | duckdb schema check |
| B5 | SMA signal 이 lookahead bias 4-layer (libcst lint / runtime / event log / fixture) 통과 | ADR-005 검증 모듈 |
| B6 | 5 repo `import` smoke + CLI entrypoint 발견 | pytest-collect |

**Demonstration AC** (Epic 완료 시 demo, 자동 검증 의무 X):

| # | AC | 검증 |
|---|---|---|
| D1 | Streamlit dashboard 가 equity_curve.csv 를 읽어 chart 표시 | manual |
| D2 | Backtest 결과의 final equity / max drawdown / sharpe 가 report 에 포함 | manual review |

**Backfill data-set 명세 (B1~B5 의 deterministic input)**:
- Symbol: `KRW-BTC`
- Timeframe: `1h`
- Period: 7 calendar days (KST 기준 종료 일자 = 직전 자정)
- SMA: `fast=5`, `slow=20`
- Fee: ADR-004 Bithumb spot 0.04% 양면 (maker = taker = 0.04%)
- Slippage: ADR-004 base + size+volatility composite 의 단순 적용 (size 작아서 거의 base_bps 만)
- Latency: Backtest mode = 0 (next-bar fill, ADR-004 정의)

### 7.2 5 child story 분해 + 의존 그래프

```
                  MCT-13 (mctrader-market Protocol)
                  ┌──────┴──────┐
                  ↓             ↓
              MCT-14         MCT-15 (병렬 가능)
              (Bithumb       (mctrader-data
               adapter)       schema + daemon)
                  └──────┬──────┘
                         ↓
                  MCT-16 (engine + BacktestExecutor + SMA)
                         ↓
                  MCT-17 (Streamlit equity curve)
```

| Story | 핵심 산출 | 시작 조건 |
|---|---|---|
| MCT-13 | `Candle` / `OrderBook` / `Order` Protocol (PEP 544) + Decimal types + symbol/timeframe enum | MCT-12 Phase 1 merge |
| MCT-14 | Bithumb HTTP client + `CandleProvider` adapter (`get_candles()`) + raw response fixture | MCT-13 의 `Candle` Protocol freeze |
| MCT-15 | ADR-009 v1 schema + Parquet/DuckDB write/read + 7일 backfill daemon CLI | MCT-12 Phase 1 merge (MCT-13 의 logical Candle 과 mapping 만 정렬) |
| MCT-16 | `BacktestExecutor` + SMA strategy + lookahead 4-layer + ExecutionReport + equity_curve | MCT-13 + MCT-15 freeze (MCT-14 의 raw fixture 만 dependency) |
| MCT-17 | Streamlit app reading equity_curve.csv | MCT-16 freeze |

**Parallel start 가능 = MCT-13 + MCT-15** (interface 와 storage 가 logical Candle 정렬만 맞으면 동시 진행).

각 child Story 의 Codex adoption rate = 별도 측정. Epic aggregate = child rate 평균.

### 7.3 Out-of-scope (명시 거부)

| 항목 | MCT-12 미포함 | 이유 / 후속 |
|---|---|---|
| Live mode | ✗ | ADR-002 / ADR-008 — 별도 Epic |
| Paper mode | ✗ | ADR-002 — 별도 Epic |
| Multi-strategy | ✗ | SMA only. strategy registry / config schema = 후속 Epic |
| Multi-symbol | ✗ | KRW-BTC only. portfolio aggregation = 후속 Epic |
| Multi-timeframe | ✗ | 1h only. CLI option 으로 expansion 여지만 |
| WFO execution | ✗ | ADR-006 single-window backtest 만. WFO 자체는 후속 Epic |
| Full RiskGate | ✗ | ADR-007 — minimal pass-through hook 만 (BacktestExecutor 가 RiskGate interface placeholder 호출) |
| Secret access | ✗ | ADR-008 — Backtest = secret 금지. public OHLCV endpoint 만 |
| 다른 거래소 (Upbit / Binance / Coinone / Korbit) | ✗ | ADR-001 — Bithumb 첫 Epic |
| PyPI publish | ✗ | ADR-010 — local editable + Git SHA pin. publish 는 Epic 후 별도 release task |
| Streamlit live concurrent DuckDB read | ✗ | finalized equity_curve.csv 만 read. live table read = 후속 Epic |

### 7.4 Repo 생성 순서 + first commit 표준

| Phase | Repo | first commit 의무 |
|---|---|---|
| Phase 1 | (없음 — Epic Story + child issue 등록만) | — |
| Phase 2-A | `mctrader-market` (MCT-13) | uv init + Python `>=3.11,<3.13` + ruff/pyright/pytest + pre-commit + ADR-011 5 required check + branch protection F5 mitigation |
| Phase 2-B | `mctrader-data` (MCT-15) | 위 + DuckDB/pyarrow + Windows lane CI |
| Phase 2-C | `mctrader-market-bithumb` (MCT-14) | 위 + httpx 또는 aiohttp + Bithumb HTTP fixture |
| Phase 2-D | `mctrader-engine` (MCT-16) | 위 + numpy/pandas + lookahead 4-layer + CLI entrypoint |
| Phase 2-E | `mctrader-web` (MCT-17) | 위 + streamlit |

모든 repo 첫 publishable version = `0.1.0`. CODEOWNERS = `@mccho8865`. branch protection = F5 mitigation set (required approvals = 0, CODEOWNERS off, admin override on).

### 7.5 Cross-repo install 정책

- **Local dev**: `uv pip install -e ../mctrader-market -e ../mctrader-data -e .` (path/editable)
- **CI**: workspace checkout layout + Git SHA pin (commit hash)
- **PyPI publish**: defer. MCT-12 Epic AC 통과 후 별도 release task
- **Release `pyproject.toml`**: path/editable dependency **금지** (ADR-010 7.6)

각 child Story 의 `pyproject.toml` 에 SemVer 0.x strict pin:
```toml
# mctrader-engine
[project]
dependencies = [
  "mctrader-market>=0.1,<0.2",
  "mctrader-data>=0.1,<0.2",
  # mctrader-market-bithumb 는 runtime adapter selection — engine 직접 의존 X
]
```

### 7.6 Risk + mitigation

| # | Risk | Severity | Mitigation | Fail-fast vs Defer |
|---|---|---|---|---|
| R1 | Bithumb API rate limit / response shape 변화 | High | small fixed volume + retry bounded backoff + raw fixture 저장 + adapter schema validation | **Fail-fast** (schema mismatch) |
| R2 | DuckDB / Parquet Windows path / partition discovery | Med-High | `pathlib.Path` + forward-slash normalize + roundtrip test + Windows local CI lane | **Fail-fast** (roundtrip) |
| R3 | Lookahead 4-layer infra friction (첫 strategy) | High | SMA 에 필요한 minimum 4 check (signal timestamp align + warmup exclude + next-bar fill + future candle access guard) | **Fail-fast** |
| R4 | Cross-repo install / version pin friction | Med | repo 순서 고정 + 0.1.0 baseline + import smoke test | **Fail-fast** (import) |
| R5 | Streamlit + DuckDB concurrent read | Med | finalized equity_curve.csv read 만 (live DuckDB read 회피) | **Defer** (별도 Epic) |
| R6 | PyPI publish friction | Med | local editable + Git SHA pin | **Defer** |

### 7.7 Phase 1 / Phase 2 분담

**Phase 1** (MCT-12 자체):
- 본 Story doc + Epic-level decision (AC / out-of-scope / repo 순서 / dependency / risk)
- 5 child issue (MCT-13~17) 등록 (mctrader-hub Issue Forms = `audit` / `bug` 만 — degraded mode 라 manual issue body)
- CFP-60 debut-audit checklist freeze (각 child Story 종료 시 audit:from-mctrader-debut + category:* 등록 의무)

**Phase 2** (5 Child PR):
- MCT-13: mctrader-market repo 생성 + Protocol + 0.1.0 publish (local editable)
- MCT-14: mctrader-market-bithumb repo 생성 + adapter + raw fixture
- MCT-15: mctrader-data repo 생성 + ADR-009 schema + 7일 backfill daemon
- MCT-16: mctrader-engine repo 생성 + BacktestExecutor + SMA + report
- MCT-17: mctrader-web repo 생성 + Streamlit equity curve

각 child Phase 2 PR merge 직후:
- `scripts/check-debut-audit-signals.sh` (CFP-60 Phase 2) 실행 — R1-R4 measurable signal mechanical detection
- finding 발견 시 `audit:from-mctrader-debut` + `category:*` 으로 mclayer/plugin-codeforge issue 등록 (CFP-60 §4 Issue 등록 절차)

### 7.8 Codex 리뷰 패턴 (Story 단위)

각 child Story Phase 1 = Codex 일괄 dispatch (7-area design review) → Sonnet 합성 → Story doc 작성 → Phase 1 PR. (MCT-2~11 와 동일 패턴, F5 mitigation merge.)

각 child Story Phase 2 = Codex implementation 검토 + 테스트 작성 + lookahead 검증 → Sonnet 합성 → Phase 2 PR.

**Phase 1 stop 1 회 / Phase 2 stop 1 회 = child 당 사용자 stop 최대 2 회**. 5 child * 2 = 최대 10 stop. ADR-006 의 promotion gate 와 동일 의미: child Phase 2 merge = Epic 의 progress 측정.

### 7.9 RiskGate minimal pass-through hook

ADR-007 의 5 kill switch 는 MCT-12 미구현. 그러나 BacktestExecutor 의 architecture 는 RiskGate interface 가 미래에 결합 가능한 자리를 보존:

```python
# mctrader-engine/executor/backtest.py
class BacktestExecutor:
    def __init__(self, ..., risk_gate: RiskGate | None = None):
        self._risk_gate = risk_gate  # MCT-12 = always None (no-op)

    def _on_bar(self, candle: Candle):
        # ...
        if self._risk_gate is not None:
            self._risk_gate.check(...)  # MCT-12 = unreachable
```

별도 Epic (MCT-N+) 에서 RiskGate 구현 시 BacktestExecutor 변경 최소.

### 7.10 데뷔 audit checklist (CFP-60)

각 child Phase 2 PR merge 직후 의무:
1. Codex 7-카테고리 평가 (lane-progression / agent-gap / decision-table / deputy-mandate / workflow-invariant / template / contract-schema)
2. (b) WARN 또는 (c) FAIL finding 시 mclayer/plugin-codeforge Issue 등록
3. label: `audit:from-mctrader-debut` + `category:<해당 1 개>` (mutually exclusive)
4. Issue body = Codex 평가 발췌 + CFP-NN proposal draft outline
5. CFP-60 §5 비차단 — finding 발견 시 mctrader 진행 차단 X

### 7.11 Epic 종료 trigger + handoff

Epic MCT-12 종료 = 5 child 모두 Phase 2 merge + B1~B6 Blocking AC 통과. 이후:
- Epic close PR: README.md + EPIC-RESULTS.md 작성 (final equity / sharpe / drawdown / Codex aggregate adoption rate)
- 후속 Epic candidate: Paper mode (MCT-N+) / Multi-symbol (MCT-N+) / RiskGate full (MCT-N+) / WFO (MCT-N+)
- 후속 candidate 우선순위 결정 = 별도 brainstorm Story (MCT-12 종료 후 user 의사결정)

### 7.12 Codex 채택 (본 Epic Story 자체)

Codex review 7 area (acceptance / decomposition / out-of-scope / data spec / cross-repo / risk / phase scope) — 모두 채택. ADR conflict 0 / 7.

채택률 7/7 (Epic-level). 각 child Story 채택률은 별도 측정.

## 8-11

(Phase 2 = 각 child Story PR 분담. 본 Epic Story 자체는 doc-only.)
