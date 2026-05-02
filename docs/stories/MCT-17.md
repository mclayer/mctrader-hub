---
story_key: MCT-17
status: phase:요구사항
component: web
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-010, ADR-011
---

# MCT-17: mctrader-web Streamlit equity curve dashboard

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-17: mctrader-web Streamlit equity curve"

## 2. 도메인 해석

`mctrader-web` repo 의 첫 commit. **Epic MCT-12 의 마지막 child** = 가장 가벼운 Story. MCT-16 산출 (`equity_curve.csv` + `ExecutionReport JSON`) 을 read 해 chart + summary stats 표시.

**MCT-12 Demonstration AC** (D1: equity curve chart visible, D2: final equity / max drawdown / sharpe report) 의 reference impl. **Manual refresh** (live concurrent DuckDB read = MCT-12 out-of-scope).

ADR-010 = `mctrader-web` 의 base = `fastapi + uvicorn + pydantic-settings` (API). `streamlit` = optional dep group (`[dependency-groups] dashboard`). 본 Story = **dashboard group** 만 사용 (FastAPI API = future Epic).

## 3. 관련 ADR

- ADR-010 (Python 3.11+ / uv / Pydantic v2 boundary / Decimal canonical / `streamlit` optional dep group `dashboard`)
- ADR-011 (5 required check + Pre-commit)
- 의존: MCT-16 Phase 1 freeze (`equity_curve.csv` 6 column + ExecutionReport schema)

## 4. 관련 코드 경로

```
mctrader-web/
├── pyproject.toml             # base = fastapi + uvicorn + pydantic-settings
                               # [dependency-groups] dashboard = streamlit + plotly + pandas
├── uv.lock
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/ci.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
├── src/mctrader_web/
│   ├── __init__.py
│   ├── api/                   # FastAPI placeholder (future Epic)
│   │   └── __init__.py
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py             # Streamlit entry: `streamlit run src/mctrader_web/dashboard/app.py`
│       ├── loader.py          # load_equity_curve(path) + load_execution_report(path)
│       ├── discovery.py       # discover_runs(output_dir) — run_id list
│       ├── transform.py       # parse_decimal_columns(df) + format_krw(decimal)
│       ├── chart.py           # build_equity_chart(df) — Plotly figure
│       └── summary.py         # build_summary_metrics(report, curve)
└── tests/
    ├── fixtures/
    │   ├── equity_curve_sample.csv
    │   └── execution_report_sample.json
    ├── test_loader.py
    ├── test_discovery.py
    ├── test_transform.py
    ├── test_summary.py
    ├── test_chart.py
    └── test_app_smoke.py      # streamlit.testing.AppTest minimal
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ + `streamlit` (dashboard group) + `plotly` (dashboard group) + `pandas`
- `pandas.read_csv(..., dtype=str)` 의무 (MCT-16 read contract)
- `decimal.Decimal` precision 보존
- `streamlit.testing.AppTest` (Streamlit 1.28+)
- pyright strict + pytest + ADR-011 5 required check

## 7. 설계 서사 (요약)

### 7.1 Streamlit page 구성 = single page (A1 결정)

**채택**: single page (top-down scroll) + sidebar = run selection only.

**근거**:
- MCT-12 = single backtest run output → multi-tab navigation 불필요
- D1/D2 manual confirmation = chart + summary 즉시 visible 우선
- 첫 commit = layout state / tab routing 복잡도 회피
- Streamlit 표준 패턴 (sidebar input + main area result)

**Layout**:
```
[sidebar]
  📁 Output directory: (text input, default = MCTRADER_OUTPUT_DIR or ./out/)
  🎯 Run: [selectbox of discovered runs]
  🔄 Refresh button

[main area]
  # mctrader Backtest Dashboard
  ## Run: bt-sma-KRW-BTC-1h-2026-04-25-2026-05-02-5-20

  📊 Equity Curve  (Plotly chart, full width)

  📈 Summary
  ┌────────────────┬──────────────┬──────────┬──────────┬──────────────┐
  │ Final Equity   │ Max Drawdown │ Sharpe   │ Win Rate │ Total Trades │
  │ ₩1,012,345.67  │ -2.34%       │ 0.85     │ 58.3%    │ 12           │
  └────────────────┴──────────────┴──────────┴──────────┴──────────────┘

  📋 Trade Events  (optional, expander - default closed)
  | ts_utc | side | price | quantity | fee_bps | slippage_bps |
```

### 7.2 Chart library = Plotly (A2 결정)

**채택**: `plotly` (dashboard optional dep group).

**근거**:
- KRW axis = 큰 숫자 (1 BTC ≈ 100,000,000 KRW) → axis tick format + hover 가독성 critical
- Plotly = `tickformat`, hover template, zoom/pan, legend customization 강력
- Streamlit 와 통합 단순 (`st.plotly_chart(fig)`)
- Decimal canonical 유지: chart input = float (시각화만), hover = Decimal-derived formatted string

**비채택 이유**:
- Altair = KRW formatting 약함
- Streamlit native (`st.line_chart`) = tooltip / axis customization 제한
- Matplotlib = static, interactive UX 약함

**chart.py 핵심**:
```python
def build_equity_chart(df: pd.DataFrame) -> plotly.graph_objects.Figure:
    # df: read=str + Decimal 변환된 상태
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["ts_utc"],                  # ISO-8601 Z UTC (datetime)
        y=df["equity"].astype(float),     # chart 만 float (precision 무관)
        mode="lines",
        name="Equity",
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %H:%M UTC}</b><br>"
            "Equity: ₩%{customdata}<extra></extra>"  # customdata = formatted Decimal string
        ),
        customdata=df["equity"].apply(format_krw),
    ))
    fig.update_layout(
        yaxis_tickformat=",.0f",        # 1,000,000 readable
        xaxis_title="UTC Time",
        yaxis_title="Equity (KRW)",
    )
    return fig
```

### 7.3 Refresh policy = manual (A3 결정)

**채택**: Manual refresh button + `st.cache_data` (button click 시 cache clear).

**근거**:
- MCT-12 = single backtest run, live concurrent DuckDB read = out-of-scope
- File watch / auto-rerun = 첫 commit 의 dependency / OS 차이 부담
- 사용자가 backtest 재실행 후 명시적 refresh = 단순한 mental model

**구현**:
```python
@st.cache_data
def load_run(output_dir: Path, run_id: str) -> tuple[pd.DataFrame, ExecutionReport]: ...

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
```

### 7.4 Run discovery = default path + selectbox (A4 결정)

**채택**: `MCTRADER_OUTPUT_DIR` env var → default `./out/` → directory list → run selectbox.

**Discovery rule**:
- Output directory 안의 sub-directory = 1 run (directory name = `run_id`)
- 각 run directory 의 의무: `equity_curve.csv` + `execution_report.json` 모두 존재
- 두 file 모두 missing = run 으로 인식 X (incomplete)

```python
def discover_runs(output_dir: Path) -> list[RunInfo]:
    runs = []
    for child in output_dir.iterdir():
        if not child.is_dir():
            continue
        equity_csv = child / "equity_curve.csv"
        report_json = child / "execution_report.json"
        if equity_csv.exists() and report_json.exists():
            runs.append(RunInfo(run_id=child.name, path=child))
    return sorted(runs, key=lambda r: r.run_id, reverse=True)  # newest first

class RunInfo(BaseModel):
    run_id: str
    path: Path
```

**MCT-16 align**: `--run-id` deterministic = `bt-{strategy}-{symbol}-{tf}-{start}-{end}-{fast}-{slow}` → directory name 사용.

### 7.5 Display 구성 (A5 결정 — minimal)

**필수**:
- Equity curve chart (D1)
- Summary stats 5: `final_equity / max_drawdown / sharpe / win_rate / total_trades` (D2 + ExecutionReport.summary)

**Optional** (default closed expander):
- Trade events table (`ExecutionReport.events[]` 의 OrderEvent 만 — `status_to == FILLED`)

**Defer** (future):
- Position quantity over time chart (CSV column 있지만 D1 필수 아님, dual axis 혼란 회피)
- Strategy decision log (BUY/SELL/HOLD timeline)
- RiskGate events (MCT-12 = empty)
- Slippage / Fee analysis chart

**final_equity source**: `ExecutionReport.summary.equity` 우선, equity_curve.csv 마지막 row 와 비교 — 불일치 시 warning (default rule). conflict detection 의무 X.

### 7.6 Read contract — Decimal handling (A6 결정 — 4 layer)

| Layer | 책임 | 실제 변환 |
|---|---|---|
| Read | `pandas.read_csv(..., dtype=str)` | 모든 column = string (precision 보존) |
| Domain | `parse_decimal_columns(df, cols=...)` | `equity / position_quantity / realized_pnl / unrealized_pnl / cash` → `decimal.Decimal` |
| Display | `format_krw(decimal) → str` | `1012345.67` → `"₩1,012,345.67"` |
| Chart | float 변환 (시각화 only) | `df["equity"].astype(float)` — chart 의 y 값만 |

**ExecutionReport JSON** 도 동일:
```python
class ExecutionReport(BaseModel):
    # ... Pydantic v2 가 string → Decimal 자동 parse (Annotated Decimal38_18)
```

**timestamp**:
- read = string ("2026-05-02T03:00:00Z")
- parse = `pd.to_datetime(..., utc=True)` → tz-aware UTC datetime
- chart = datetime
- display = formatted string ("2026-05-02 03:00 UTC")

### 7.7 Test 전략 — pure unit + Streamlit smoke (A7 결정)

**Layer 1 — Pure unit test** (대부분):

| 함수 | 테스트 |
|---|---|
| `load_equity_curve(path)` | dtype=str 보장 + 6 column 존재 + ts_utc UTC parse |
| `load_execution_report(path)` | Pydantic v2 ExecutionReport.validate_json + Decimal38_18 보존 |
| `discover_runs(dir)` | sub-directory 의 equity_curve.csv + execution_report.json 둘 다 존재 → run / 하나만 = skip |
| `parse_decimal_columns(df, cols)` | string → Decimal 정확 (`"1000000.123456789012345678"` precision 보존) |
| `format_krw(decimal)` | `1012345.67` → `"₩1,012,345.67"` (천 단위 separator) |
| `build_summary_metrics(report, curve)` | summary 5 stats 계산 정확 / final_equity discrepancy detection |
| `build_equity_chart(df)` | Plotly Figure 반환 + x = ts_utc / y = equity / hovertemplate 정의 |

**Layer 2 — Streamlit smoke test** (`streamlit.testing.AppTest`, 1 test):

```python
def test_app_smoke_with_sample_run():
    at = AppTest.from_file("src/mctrader_web/dashboard/app.py")
    at.run()
    # sample fixture = tests/fixtures/ 가 default discovery path
    assert any("Equity Curve" in t.value for t in at.markdown)
    assert at.metric  # summary metrics 존재
```

**Defer**: Playwright / Selenium / image diff snapshot — flaky + scope 과대.

**Coverage target**: ADR-011 60% baseline. pure unit test 가 대부분 → 충분.

### 7.8 Pyproject + 첫 commit standard

```toml
[project]
name = "mctrader-web"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
  "fastapi>=0.110",
  "uvicorn>=0.30",
  "pydantic>=2,<3",
  "pydantic-settings>=2",
]

[dependency-groups]
dashboard = [
  "streamlit>=1.28",
  "plotly>=5",
  "pandas>=2.2,<3",
]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "pyright>=1.1",
  "ruff>=0.6",
]

[project.scripts]
mctrader-dashboard = "mctrader_web.dashboard.app:main"
```

**uv install for dashboard**:
```
uv sync --group dashboard
```

**CI** (ADR-011): 5 required check + dashboard group install (test 실행 위해 필요).

### 7.9 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| FastAPI API endpoints | ✗ (placeholder dir 만) | future Epic — `mctrader-web` base 는 fastapi 이지만 본 Story = dashboard group 만 |
| Multi-page (Streamlit `pages/`) | ✗ | single page 충분 |
| Position quantity chart | ✗ | D1 필수 X (dual axis 혼란) |
| Strategy decisions log | ✗ | Defer |
| RiskGate events display | ✗ | MCT-12 = empty |
| Slippage / Fee analysis chart | ✗ | Defer |
| Live concurrent DuckDB read | ✗ | MCT-12 out-of-scope |
| File upload | ✗ | local solo dev workflow = directory discovery 충분 |
| Auto-refresh / file watch | ✗ | manual refresh button |
| Authentication / authz | ✗ | local-only |
| Browser e2e (Playwright/Selenium) | ✗ | streamlit.testing.AppTest smoke 만 |
| Image diff snapshot | ✗ | flaky |

### 7.10 Acceptance (Phase 2)

| # | AC | 검증 | Demonstration AC |
|---|---|---|:---:|
| AC1 | `pyproject.toml` `version = "0.1.0"` + base = fastapi/uvicorn/pydantic-settings + `[dependency-groups] dashboard = streamlit/plotly/pandas` | uv sync --frozen + uv sync --group dashboard | — |
| AC2 | 5 required check green | CI | — |
| AC3 | `load_equity_curve(path)` = `dtype=str` + 6 column 검증 + ts_utc UTC datetime parse | pytest | — |
| AC4 | `load_execution_report(path)` = Pydantic v2 ExecutionReport (schema_version="execution_report.v1") parse + Decimal38_18 string → Decimal 보존 | pytest | — |
| AC5 | `discover_runs(dir)` = sub-directory + equity_curve.csv + execution_report.json 모두 존재 = run / 하나만 = skip + newest first sort | pytest | — |
| AC6 | `parse_decimal_columns(df, cols)` = string → Decimal precision 18 보존 (float 우회) | pytest | — |
| AC7 | `format_krw(Decimal("1012345.67"))` = `"₩1,012,345.67"` 천 단위 separator | pytest | — |
| AC8 | `build_summary_metrics(report, curve)` = 5 stats (final_equity / max_drawdown / sharpe / win_rate / total_trades) 정확 + ExecutionReport.summary 우선 | pytest | — |
| AC9 | `build_equity_chart(df)` = Plotly Figure 반환 + x=ts_utc datetime + y=equity float + hovertemplate 정의 | pytest | — |
| AC10 | `streamlit.testing.AppTest` smoke = sample fixture run 으로 page load + Equity Curve markdown + summary metric 존재 | pytest | **D1 + D2** |
| AC11 | Manual refresh button click → `st.cache_data.clear()` + `st.rerun()` | pytest (mock) | — |

**Demonstration AC mapping** (MCT-12):
- D1 (Streamlit equity curve render) = AC9 + AC10
- D2 (final equity / max drawdown / sharpe) = AC8 + AC10

### 7.11 Epic 종료 trigger

본 Story Phase 2 merge + Blocking AC B1~B6 (MCT-13 + MCT-14 + MCT-15 + MCT-16) 통과 시 **MCT-12 Epic close PR** 작성:
- `EPIC-RESULTS.md` (final equity / max drawdown / sharpe / total trades)
- Codex aggregate adoption rate (5 child Phase 1 + 5 child Phase 2 의 평균)
- 후속 candidate (Paper / Multi-symbol / RiskGate full / WFO / multi-strategy) 우선순위 brainstorm trigger

### 7.12 Codex 적용

7/7 area 채택 (Streamlit page 구성 / Chart library / Refresh / Run discovery / Display / Read contract / Test). ADR conflict 0/7.

## 8-11

(Phase 2 = `mctrader-web` repo 생성 + 첫 commit + AC1~AC11 통과 PR. MCT-16 Phase 2 merge 후 시작. **Epic 의 마지막 child** — Phase 2 merge 가 Epic close PR trigger.)
