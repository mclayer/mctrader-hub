# mctrader-web Phase 2A — Web-only enhancement (active runs visibility + TZ + datetime picker + events table)

**Status**: Draft (2026-05-04)
**Author**: brainstormed via superpowers:brainstorming skill, Codex review + Sonnet decider 합성 closed
**Owner repo**: `mctrader-web` (UI 변경 only)
**Companion spec**: `2026-05-04-mctrader-web-phase-2b-design.md` (engine artifact + chart, Phase 2A merge 후 시작)

## 1. Why this spec exists

사용자 요구 5건 중 cross-repo (engine schema + artifact) 변경을 동반하지 **않는** 4건을 1차 spec 으로 분리. Phase 2A merge 후 Phase 2B (engine artifact + candlestick chart) 시작. 단일 PR 단위로 가능한 web-only path 를 닫는 게 목적.

| 사용자 요구 | Phase 2A | Phase 2B |
|---|---|---|
| Global-1 진행중 작업 가시성 | ✓ active runs sidebar | — |
| Global-2 TZ selector + KST | ✓ sidebar TZ selector | — |
| Backtest-1 datetime picker | ✓ native split | — |
| Backtest-2 candlestick + indicators + buy/sell vline | — (engine artifact 필요) | ✓ |
| Backtest-3 events table 정비 | ✓ legacy schema 기준 (Side="—") | ✓ Side/Notional/Fee 컬럼 schema 필드로 대체 |

## 2. Scope

### In scope (Phase 2A)
- 모든 page 공통 sidebar helper `render_common_sidebar(client)` 신설
- Active runs 가시성: FastAPI `GET /runs/active` 신규 + sidebar 섹션
- TimeZone selector (sidebar, options = `UTC` / `Asia/Seoul`, default = `Asia/Seoul`)
- Datetime picker: `st.date_input` + `st.time_input` split (native streamlit)
- Events table 재구성 (현 OrderEvent schema 기준): order_id prefix 제거, 컬럼 재배치, status_to default filter, KRW formatter 중앙화
- 공통 formatter 모듈 (`format_ts`, `format_krw`, `format_qty`, `format_bps`, `parse_order_seq`)

### Out of scope (Phase 2B 또는 이후)
- `OrderEvent.side / notional / fee` 신규 schema 필드 (engine 변경 필요 → Phase 2B)
- `candles.csv` / `indicators.csv` 저장 (engine 변경 → Phase 2B)
- Candlestick + indicator overlay + buy/sell scatter marker (Phase 2B)
- Paper panel candlestick (Phase 3)
- KST 외 TZ option (Phase 3 — Browser local, US/Eastern 등)
- FastAPI 서버 재시작 후 진행중 작업 복구 (in-memory tracker 유지, "페이지 벗어나도" = navigation only 해석)

## 3. Architecture

### 3.1 Repo boundary
- `mctrader-web` — 모든 변경
- `mctrader-hub` — Story stub 작성
- `mctrader-engine` — 변경 **없음**

### 3.2 File map

| File | Action | 내용 |
|---|---|---|
| `src/mctrader_web/dashboard/common.py` | NEW | `render_common_sidebar(client)`, formatter 함수, `parse_order_seq`, `compute_notional`, `compute_fee` |
| `src/mctrader_web/dashboard/app.py` | MODIFY | TZ default 초기화 (session_state), common sidebar import |
| `src/mctrader_web/dashboard/pages/01_paper_panel.py` | MODIFY | 자체 sidebar 의 Service health 부분 → `render_common_sidebar(client)` 호출. paper-specific status (uptime, active_run_id) 는 main panel 의 status 섹션으로 이동. ts 표시 모두 `format_ts` 통과 |
| `src/mctrader_web/dashboard/pages/02_backtest_panel.py` | MODIFY | datetime picker (native split), events table 재구성, common sidebar |
| `src/mctrader_web/api/routes.py` | MODIFY | `GET /runs/active` 신규 endpoint |
| `src/mctrader_web/api/models.py` | MODIFY | `ActiveRun` Pydantic DTO |
| `src/mctrader_web/api_client/client.py` | MODIFY | `list_active_runs()` 메서드 추가 |
| `tests/test_common.py` | NEW | formatter + parse_order_seq edge cases |
| `tests/test_active_runs_endpoint.py` | NEW | FastAPI TestClient |
| `tests/test_apptest_smoke.py` | NEW or MODIFY | streamlit AppTest sidebar + TZ + form |

### 3.3 FastAPI new endpoint

```
GET /runs/active
Authorization: Bearer <token>

Response 200:
{
  "active_runs": [ActiveRun, ...]
}
```

**`ActiveRun` DTO** (`api/models.py`):
```python
from mctrader_market.types import UTCDateTime  # tz-aware UTC, Pydantic v2 strict

class ActiveRun(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    run_id: str
    mode: Literal["backtest", "paper", "live"]
    symbol: str
    timeframe: str
    started_at_utc: UTCDateTime  # tz-aware UTC enforce (naive datetime 거부)
    status: str  # "queued" | "running" | "completed" | "error" | ...
    output_dir: str | None = None
```

**Source**: 기존 in-memory backtest tracker + paper session manager 를 union.
- backtest: `BacktestLifecycleManager.list()` filter (lifecycle ∈ {queued, running})
- paper: `PaperLifecycleManager.active()` if `active_run_id` set
- 두 source 합쳐서 ActiveRun list 반환.

### 3.4 Streamlit session_state contract

```python
# app.py entry
if "tz" not in st.session_state:
    st.session_state["tz"] = "Asia/Seoul"  # default per Q2-B
```

- **Session-scoped only**: 새 browser tab / 서버 재시작 시 default 로 reset.
- Cookie / query param 미사용 (Phase 2A 의 ergonomics 한계 명시 — durable preference 는 Phase 3).
- 모든 ts 표시는 `format_ts(ts_utc, st.session_state["tz"])` 통과.

### 3.5 TimeZone boundary protocol (Codex finding #5 해소)

**규칙**:
1. **Backend storage / API request body** = 항상 ISO 8601 UTC tz-aware string (예: `"2026-04-27T07:00:00Z"`).
2. **UI input field label**: selected TZ 명시 — `"Start Date (KST)"`, `"Start Time (KST)"`, `"End Date (KST)"`, `"End Time (KST)"`.
3. **Submit 직전 read-only UTC echo**: form 하단에 `"→ FastAPI: 2026-04-27T07:00:00Z (UTC)"` 표시.
4. **모든 column header / 표시 timestamp** = `(KST)` 또는 `(UTC)` suffix.

이 규칙 위반 = test 로 fail (formatter 가 naive datetime 거부).

### 3.6 Datetime picker UX (native split)

```python
# in 02_backtest_panel.py form
tz_name = st.session_state["tz"]  # "UTC" or "Asia/Seoul"
tz_label = "KST" if tz_name == "Asia/Seoul" else "UTC"

col1, col2, col3, col4 = st.columns(4)
start_date = col1.date_input(f"Start Date ({tz_label})", value=default_start.date())
start_time = col2.time_input(f"Start Time ({tz_label})", value=default_start.time(), step=timedelta(minutes=1))
end_date = col3.date_input(f"End Date ({tz_label})", value=default_end.date())
end_time = col4.time_input(f"End Time ({tz_label})", value=default_end.time(), step=timedelta(minutes=1))

# combine + tz attach + UTC convert
start_utc = ZoneInfo(tz_name).localize(...).astimezone(timezone.utc)
end_utc = ...

# UTC echo
st.caption(f"→ FastAPI: {start_utc.isoformat()} → {end_utc.isoformat()} (UTC)")

# validation
if start_utc >= end_utc:
    st.error(f"Start must be before End. start={start_utc} end={end_utc}")
    submit_disabled = True
elif end_utc > now_utc:
    st.error(f"End must be in the past (backtest = historical). end={end_utc} now={now_utc}")
    submit_disabled = True
else:
    submit_disabled = False
```

**Granularity**: minute (`step=timedelta(minutes=1)` 명시).
**Default value**: 마지막 7일 (`now_in_tz - 7d` → `now_in_tz`), wall time in selected TZ.
**Validation**:
- `start_utc < end_utc`
- `end_utc <= now_utc`
- 둘 중 하나라도 fail → "Run Backtest" button disabled (`st.form_submit_button(disabled=submit_disabled)`)
- 에러 메시지 = 양쪽 TZ + UTC echo 동시 표시.

### 3.7 Active runs sidebar

```python
def render_common_sidebar(client: MctraderApiClient) -> None:
    with st.sidebar:
        # 1. TZ selector (Codex #6: column header 와 별도, 가장 위에 노출)
        st.session_state["tz"] = st.selectbox(
            "🌐 TimeZone",
            options=["Asia/Seoul", "UTC"],
            index=0 if st.session_state.get("tz") == "Asia/Seoul" else 1,
        )

        # 2. Service health
        st.subheader("Service")
        if client.health():
            st.success("FastAPI OK (127.0.0.1:7821)")
        else:
            st.error("FastAPI unreachable.")

        # 3. Active runs (Q1-A)
        st.subheader("Active runs")
        try:
            active = client.list_active_runs()
        except Exception as exc:
            st.caption(f"Active runs unavailable: {type(exc).__name__}")
            return

        if not active:
            st.caption("No active runs.")
            return

        for run in active:
            elapsed = (now_utc() - run.started_at_utc).total_seconds()
            st.markdown(
                f"**{run.run_id}** · `{run.mode}` · {run.symbol}/{run.timeframe} · "
                f"elapsed {elapsed:.0f}s · status `{run.status}`"
            )
```

- 각 page 의 entry 직후 호출 (`render_common_sidebar(client)`).
- Backward compat: `/runs/active` endpoint 부재 (older FastAPI) → "Active runs unavailable" caption 으로 silent fallback (Codex #4 의 graceful 처리).

### 3.8 Events table (legacy schema 기준 — Phase 2A, **backtest_panel 한정**)

본 spec 의 events table 변경은 `02_backtest_panel.py` 에 한정. paper events 의 동일 처리는 별 spec (Phase 3 또는 별도 paper-events Story).


```
| Time (KST)        | Side | # | Status | Price        | Qty        | Notional      | Fee      | Fee bps | Slip bps |
|-------------------|------|---|--------|--------------|------------|---------------|----------|---------|----------|
| 2026-04-27 16:05  | —    | 1 | FILLED | ₩145,200,000 | 0.00100000 | ₩145,200      | ₩363     | 25.00   | 5.00     |
```

- **Default filter**: `status_to == "FILLED"` (Codex #13, #16). Toggle "Show all events" → 모든 status_to 노출.
- **Side column**: Phase 2A 에서는 schema 에 필드 없음 → `"—"` 표시. Phase 2B 에서 `OrderEvent.side` 채워짐 (BUY=red, SELL=blue text + 마커 prefix).
- **# column**: `parse_order_seq(order_id, run_id)` — anchored regex `^bt:{re.escape(run_id)}:(\d+)$` → match 시 `(\d+)`, fail 시 원본 (Codex #18).
- **Notional / Fee**: UI 측 계산 (`compute_notional(price, qty)`, `compute_fee(notional, fee_bps)`). Phase 2B 에서 `OrderEvent.notional` / `OrderEvent.fee` schema 필드 추가 시 fallback only 로 강등.
- **Status column**: `status_to` keep. Codex #13 의 lifecycle visibility.

### 3.9 Centralized formatter (`common.py`)

```python
# Time
def format_ts(ts_utc: datetime, tz_name: str) -> str:
    """예: '2026-04-27 16:05'. ts_utc must be tz-aware."""

# Currency
def format_krw(value: Decimal | None) -> str:
    """예: '₩145,200,000' (thousands sep, 0 decimals). None → '—'."""

# Quantity
def format_qty(value: Decimal | None) -> str:
    """예: '0.00100000' (8 decimals). None → '—'."""

# Basis points
def format_bps(value: Decimal | None) -> str:
    """예: '25.00' (2 decimals). None → '—'."""

# Order id parsing (Codex #18)
def parse_order_seq(order_id: str, run_id: str) -> str:
    """Anchored regex match. fail 시 원본 order_id 반환 (no fabrication)."""

# UI fallback computation (Phase 2B 에서 schema 로 강등)
def compute_notional(price: Decimal | None, qty: Decimal | None) -> Decimal | None:
    """price * qty. 둘 중 하나라도 None → None."""

def compute_fee(notional: Decimal | None, fee_bps: Decimal | None) -> Decimal | None:
    """notional * (fee_bps / Decimal('10000')). 둘 중 하나라도 None → None."""
```

**Precision rules** (Codex #19):
- KRW (price/notional/fee): thousands separator + 0 decimals
- Crypto qty: 8 decimals
- bps: 2 decimals
- 모든 값 ambient locale 의존 X (명시적 format).

## 4. Testing strategy

### 4.1 Unit (`tests/test_common.py`)
- `format_ts`: KST/UTC 둘 다, naive datetime 입력 시 raise
- `format_krw`: 0, 양수, None, 매우 큰 값 (`Decimal("1234567890")`)
- `format_qty`: 8 decimals 보정, None
- `format_bps`: 2 decimals
- `parse_order_seq`:
  - match: `("bt:run-001:42", "run-001")` → `"42"`
  - prefix mismatch: `("bt:run-002:42", "run-001")` → `"bt:run-002:42"` (원본)
  - schema 다름: `("paper:run-001:1", "run-001")` → `"paper:run-001:1"` (원본)
  - run_id 에 regex meta char (e.g. `.`, `*`) → `re.escape` 으로 안전
- `compute_notional` / `compute_fee`: edge cases (None propagate)

### 4.2 FastAPI endpoint (`tests/test_active_runs_endpoint.py`)
- `GET /runs/active` returns 200 + correct DTO
- backtest active + paper active 동시
- empty case → `{"active_runs": []}`
- Authorization 미동봉 → 401

### 4.3 Streamlit AppTest (`tests/test_apptest_smoke.py`)
- 각 page entry → sidebar 에 TZ selector + active runs 섹션 보임
- TZ 변경 → session_state["tz"] 업데이트
- Backtest panel 의 datetime form: invalid range (start >= end) → button disabled + 에러 메시지
- UTC echo 표시 확인

### 4.4 Cross-page navigation
- AppTest 에서 page switch (paper → backtest → paper) 후에도 active runs 갱신
- session_state 유지 (TZ 선택)

## 5. Backward compatibility

| Surface | Legacy 처리 |
|---|---|
| `/runs/active` endpoint 부재 (구버전 FastAPI) | sidebar caption "Active runs unavailable: {error}", silent fallback |
| Legacy events `status_to != FILLED` | default filter 자동 처리 ("Show all events" toggle 로 노출) |
| Legacy `order_id` regex 미일치 | 원본 표시 (fabrication 금지) |
| `st.session_state["tz"]` 미초기화 | app.py entry 에서 default `"Asia/Seoul"` |

## 6. References

- `mctrader-engine/src/mctrader_engine/report/schema.py` (OrderEvent / ExecutionReport baseline)
- `mctrader-web/src/mctrader_web/dashboard/pages/02_backtest_panel.py` (현 baseline, commit `057fb9e`)
- `mctrader-web/src/mctrader_web/api/routes.py` (FastAPI baseline)
- ADR-002 (TradeExecutor 3-mode runtime isolation)
- MCT-48 Epic (Paper Runtime Operations + Web Mgmt)
- Brainstorm decisions: Q1-A / Q2-B / Q3-A (Codex push-back 으로 사용자 B → A 뒤집음) / Q5-events table 컬럼 셋

## 7. Open questions

(없음 — Codex review + Sonnet decider 합성 후 모두 closed)
