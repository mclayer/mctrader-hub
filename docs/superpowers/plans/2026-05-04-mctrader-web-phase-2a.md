# mctrader-web Phase 2A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-web Streamlit UI 의 web-only 4-건 enhancement (active runs sidebar / TZ selector / native datetime picker / events table 정비) 를 단일 PR 로 완성.

**Architecture:** Streamlit multi-page sidebar 를 공통 helper (`render_common_sidebar`) 로 추상화 + FastAPI `GET /runs/active` 신규 endpoint + 중앙화된 formatter 모듈. Backend 는 항상 UTC tz-aware ISO 8601, UI 표시만 selected TZ. session_state 로 TZ 유지.

**Tech Stack:** Python 3.11, Streamlit 1.28+, FastAPI 0.110+, Pydantic v2 strict, httpx, plotly, pandas. pytest + pytest-asyncio + streamlit AppTest.

**Spec:** `docs/superpowers/specs/2026-05-04-mctrader-web-phase-2a-design.md` (mctrader-hub repo)

**Working directory:** `c:\workspace\mclayer\mctrader-web` (모든 file path 는 이 repo 기준)

**Branch convention:** mctrader-web repo 에 `feat/phase-2a-web-ui` 같은 branch. 본 plan 은 mctrader-hub 에 저장만, 실 작업은 mctrader-web.

---

## File Structure

| File | Action | 책임 |
|---|---|---|
| `src/mctrader_web/dashboard/common.py` | NEW | session_state TZ default 초기화, formatter 함수 (`format_ts/krw/qty/bps`), `parse_order_seq`, `compute_notional`, `compute_fee`, `render_common_sidebar` |
| `src/mctrader_web/api/models.py` | MODIFY | `ActiveRun` Pydantic DTO 추가 + `ActiveRunsResponse` 추가 |
| `src/mctrader_web/api/routes.py` | MODIFY | `GET /runs/active` 신규 endpoint |
| `src/mctrader_web/api_client/client.py` | MODIFY | `list_active_runs` 메서드 추가 |
| `src/mctrader_web/dashboard/app.py` | MODIFY | TZ default session_state 초기화, common sidebar import 표기 |
| `src/mctrader_web/dashboard/pages/01_paper_panel.py` | MODIFY | 자체 sidebar Service 섹션 → `render_common_sidebar(client)` 로 교체. paper-specific status 는 main panel 의 status 섹션으로 이동 (이미 그러함). ts 표시는 `format_ts` 통과 |
| `src/mctrader_web/dashboard/pages/02_backtest_panel.py` | MODIFY | datetime picker (date_input + time_input split + UTC echo + validation), events table 재구성, common sidebar |
| `tests/test_common.py` | NEW | formatter / parse / compute unit tests |
| `tests/api/test_active_runs_endpoint.py` | NEW | FastAPI TestClient async tests |
| `tests/api/test_models_active_run.py` | NEW | Pydantic ActiveRun DTO validation tests |
| `tests/test_apptest_phase2a.py` | NEW | Streamlit AppTest smoke (sidebar TZ + datetime form validation + events table render) |

---

## Task 1: `common.py` — Time / Currency / Quantity / Bps formatters (TDD)

**Files:**
- Create: `src/mctrader_web/dashboard/common.py`
- Test: `tests/test_common.py`

- [ ] **Step 1: Write the failing tests for formatters**

Create `tests/test_common.py`:

```python
"""Phase 2A — central formatter unit tests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mctrader_web.dashboard.common import (
    format_bps,
    format_krw,
    format_qty,
    format_ts,
)


class TestFormatTs:
    def test_kst_format(self) -> None:
        ts = datetime(2026, 4, 27, 7, 5, 0, tzinfo=timezone.utc)
        assert format_ts(ts, "Asia/Seoul") == "2026-04-27 16:05"

    def test_utc_format(self) -> None:
        ts = datetime(2026, 4, 27, 7, 5, 0, tzinfo=timezone.utc)
        assert format_ts(ts, "UTC") == "2026-04-27 07:05"

    def test_none_input(self) -> None:
        assert format_ts(None, "UTC") == "—"

    def test_naive_datetime_raises(self) -> None:
        naive = datetime(2026, 4, 27, 7, 5, 0)  # no tzinfo
        with pytest.raises(ValueError, match="naive datetime"):
            format_ts(naive, "UTC")


class TestFormatKrw:
    def test_positive_thousands_separator(self) -> None:
        assert format_krw(Decimal("145200000")) == "₩145,200,000"

    def test_zero(self) -> None:
        assert format_krw(Decimal("0")) == "₩0"

    def test_none(self) -> None:
        assert format_krw(None) == "—"

    def test_drops_decimals(self) -> None:
        # KRW: 0 decimals (banker's rounding to integer)
        assert format_krw(Decimal("145200.7")) == "₩145,201"

    def test_large_value(self) -> None:
        assert format_krw(Decimal("1234567890")) == "₩1,234,567,890"


class TestFormatQty:
    def test_eight_decimals(self) -> None:
        assert format_qty(Decimal("0.001")) == "0.00100000"

    def test_zero(self) -> None:
        assert format_qty(Decimal("0")) == "0.00000000"

    def test_none(self) -> None:
        assert format_qty(None) == "—"


class TestFormatBps:
    def test_two_decimals(self) -> None:
        assert format_bps(Decimal("25")) == "25.00"

    def test_fractional(self) -> None:
        assert format_bps(Decimal("5.789")) == "5.79"

    def test_none(self) -> None:
        assert format_bps(None) == "—"
```

- [ ] **Step 2: Run tests to verify they fail**

```
cd c:/workspace/mclayer/mctrader-web
.venv/Scripts/python -m pytest tests/test_common.py -v
```

Expected: ImportError — `mctrader_web.dashboard.common` does not exist yet.

- [ ] **Step 3: Implement formatters in `common.py`**

Create `src/mctrader_web/dashboard/common.py`:

```python
"""Phase 2A — central formatter + parsing + computation helpers + common sidebar.

All ts inputs MUST be timezone-aware UTC datetimes. Naive datetimes raise
ValueError per Codex finding #5 (TZ boundary protocol).
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo


def format_ts(ts: datetime | None, tz_name: str) -> str:
    """Return 'YYYY-MM-DD HH:MM' in the selected timezone.

    Raises ValueError if ts is naive (no tzinfo). None → '—'.
    """
    if ts is None:
        return "—"
    if ts.tzinfo is None:
        raise ValueError(f"naive datetime not allowed (got {ts!r})")
    converted = ts.astimezone(ZoneInfo(tz_name))
    return converted.strftime("%Y-%m-%d %H:%M")


def format_krw(value: Decimal | None) -> str:
    """KRW currency: thousands separator + 0 decimals + ₩ prefix. None → '—'."""
    if value is None:
        return "—"
    rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    return f"₩{rounded:,}"


def format_qty(value: Decimal | None) -> str:
    """Crypto quantity: 8 fixed decimals. None → '—'."""
    if value is None:
        return "—"
    quantized = value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)
    return f"{quantized:.8f}"


def format_bps(value: Decimal | None) -> str:
    """Basis points: 2 fixed decimals. None → '—'."""
    if value is None:
        return "—"
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return f"{quantized:.2f}"
```

- [ ] **Step 4: Run tests to verify they pass**

```
.venv/Scripts/python -m pytest tests/test_common.py -v
```

Expected: 11 PASS.

- [ ] **Step 5: Commit**

```bash
cd c:/workspace/mclayer/mctrader-web
git checkout -b feat/phase-2a-web-ui
git add src/mctrader_web/dashboard/common.py tests/test_common.py
git commit -m "feat(common): add format_ts/krw/qty/bps formatters (Phase 2A Task 1)"
```

---

## Task 2: `common.py` — order_id parsing + UI fallback computation (TDD)

**Files:**
- Modify: `src/mctrader_web/dashboard/common.py`
- Modify: `tests/test_common.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_common.py`:

```python
from mctrader_web.dashboard.common import (
    compute_fee,
    compute_notional,
    parse_order_seq,
)


class TestParseOrderSeq:
    def test_match_simple(self) -> None:
        assert parse_order_seq("bt:run-001:42", "run-001") == "42"

    def test_run_id_prefix_mismatch_returns_original(self) -> None:
        assert parse_order_seq("bt:run-002:42", "run-001") == "bt:run-002:42"

    def test_paper_schema_returns_original(self) -> None:
        assert parse_order_seq("paper:run-001:1", "run-001") == "paper:run-001:1"

    def test_run_id_with_regex_metachars(self) -> None:
        # run_id may contain '.', '*' — ensure re.escape
        assert parse_order_seq("bt:run.v2:7", "run.v2") == "7"
        # do NOT match run-v2 (regex would otherwise match because '.' is wildcard)
        assert parse_order_seq("bt:run-v2:7", "run.v2") == "bt:run-v2:7"

    def test_unanchored_match_rejected(self) -> None:
        # extra prefix should not match
        assert parse_order_seq("xbt:run-001:42", "run-001") == "xbt:run-001:42"

    def test_seq_must_be_digits(self) -> None:
        assert parse_order_seq("bt:run-001:abc", "run-001") == "bt:run-001:abc"


class TestComputeNotional:
    def test_happy(self) -> None:
        assert compute_notional(Decimal("145200000"), Decimal("0.001")) == Decimal("145200")

    def test_none_price(self) -> None:
        assert compute_notional(None, Decimal("0.001")) is None

    def test_none_qty(self) -> None:
        assert compute_notional(Decimal("145200000"), None) is None


class TestComputeFee:
    def test_happy_25_bps(self) -> None:
        # notional = 145_200, fee_bps = 25 → 145_200 * 25/10000 = 363
        assert compute_fee(Decimal("145200"), Decimal("25")) == Decimal("363.000")

    def test_none_notional(self) -> None:
        assert compute_fee(None, Decimal("25")) is None

    def test_none_bps(self) -> None:
        assert compute_fee(Decimal("145200"), None) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv/Scripts/python -m pytest tests/test_common.py -v
```

Expected: ImportError on `compute_notional`, `compute_fee`, `parse_order_seq`.

- [ ] **Step 3: Append implementation to `common.py`**

Append to `src/mctrader_web/dashboard/common.py`:

```python
def parse_order_seq(order_id: str, run_id: str) -> str:
    """Anchored regex `^bt:<run_id>:(\\d+)$`. fail → return original.

    Per Codex finding #18: do not fabricate sequence numbers when format
    doesn't match. Use re.escape so run_id containing regex metachars
    ('.', '*') is treated literally.
    """
    pattern = rf"^bt:{re.escape(run_id)}:(\d+)$"
    match = re.match(pattern, order_id)
    if match is None:
        return order_id
    return match.group(1)


def compute_notional(
    price: Decimal | None, qty: Decimal | None
) -> Decimal | None:
    """price * qty. None propagate. Phase 2A UI fallback only — Phase 2B
    schema field replaces this."""
    if price is None or qty is None:
        return None
    return price * qty


def compute_fee(
    notional: Decimal | None, fee_bps: Decimal | None
) -> Decimal | None:
    """notional * (fee_bps / 10000). None propagate."""
    if notional is None or fee_bps is None:
        return None
    return notional * (fee_bps / Decimal("10000"))
```

- [ ] **Step 4: Run tests to verify they pass**

```
.venv/Scripts/python -m pytest tests/test_common.py -v
```

Expected: All Task 1 + Task 2 tests PASS (~22 tests).

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_web/dashboard/common.py tests/test_common.py
git commit -m "feat(common): add parse_order_seq + compute_notional/fee (Phase 2A Task 2)"
```

---

## Task 3: `api/models.py` — ActiveRun DTO + ActiveRunsResponse (TDD)

**Files:**
- Modify: `src/mctrader_web/api/models.py`
- Test: `tests/api/test_models_active_run.py`

- [ ] **Step 1: Write failing test**

Create `tests/api/test_models_active_run.py`:

```python
"""Phase 2A — ActiveRun + ActiveRunsResponse Pydantic DTO tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mctrader_web.api.models import ActiveRun, ActiveRunsResponse


class TestActiveRun:
    def test_happy_backtest(self) -> None:
        run = ActiveRun(
            run_id="bt-sma-KRW-BTC-1h-2026-04-27-2026-05-04-5-20",
            mode="backtest",
            symbol="KRW-BTC",
            timeframe="1h",
            started_at_utc=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
            status="running",
            output_dir="./out",
        )
        assert run.mode == "backtest"
        assert run.started_at_utc.tzinfo is not None

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ActiveRun(
                run_id="x",
                mode="paper",
                symbol="KRW-BTC",
                timeframe="5m",
                started_at_utc=datetime(2026, 4, 27, 7, 0, 0),  # naive
                status="running",
            )

    def test_non_utc_aware_rejected(self) -> None:
        """Codex finding #1: only UTC tz allowed (Asia/Seoul aware → reject)."""
        from zoneinfo import ZoneInfo

        with pytest.raises(ValidationError):
            ActiveRun(
                run_id="x",
                mode="paper",
                symbol="KRW-BTC",
                timeframe="5m",
                started_at_utc=datetime(
                    2026, 4, 27, 16, 0, 0, tzinfo=ZoneInfo("Asia/Seoul")
                ),  # non-UTC aware
                status="running",
            )

    def test_invalid_mode_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ActiveRun(
                run_id="x",
                mode="other",  # type: ignore[arg-type]
                symbol="KRW-BTC",
                timeframe="5m",
                started_at_utc=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
                status="running",
            )

    def test_optional_output_dir(self) -> None:
        run = ActiveRun(
            run_id="x",
            mode="paper",
            symbol="KRW-BTC",
            timeframe="5m",
            started_at_utc=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
            status="running",
        )
        assert run.output_dir is None


class TestActiveRunsResponse:
    def test_empty_default(self) -> None:
        resp = ActiveRunsResponse()
        assert resp.active_runs == []

    def test_with_runs(self) -> None:
        run = ActiveRun(
            run_id="x",
            mode="paper",
            symbol="KRW-BTC",
            timeframe="5m",
            started_at_utc=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
            status="running",
        )
        resp = ActiveRunsResponse(active_runs=[run])
        assert len(resp.active_runs) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv/Scripts/python -m pytest tests/api/test_models_active_run.py -v
```

Expected: ImportError — `ActiveRun` / `ActiveRunsResponse` not defined.

- [ ] **Step 3: Add DTOs to `models.py`**

Append to `src/mctrader_web/api/models.py` (after `BacktestListResponse`):

```python
class ActiveRun(BaseModel):
    """Active run snapshot for the common sidebar — Phase 2A.

    started_at_utc MUST be tz-aware (Pydantic v2 strict rejects naive datetime
    via UTCDateTime annotation). mode covers all 3 executor types even though
    Phase 2A only sources from backtest + paper lifecycle managers.
    """

    model_config = ConfigDict(strict=True, frozen=True)
    run_id: str
    mode: Literal["backtest", "paper", "live"]
    symbol: str
    timeframe: Literal["1m", "5m", "15m", "1h", "4h", "1d"]
    started_at_utc: datetime  # validated tz-aware below
    status: str
    output_dir: str | None = None

    @model_validator(mode="after")
    def _enforce_utc(self) -> "ActiveRun":
        """Codex finding #1: enforce UTC, not just any tz-aware."""
        from datetime import timedelta

        if self.started_at_utc.tzinfo is None:
            raise ValueError("started_at_utc must be timezone-aware (UTC)")
        offset = self.started_at_utc.utcoffset()
        if offset != timedelta(0):
            raise ValueError(
                f"started_at_utc must be UTC (offset=0), got offset={offset}"
            )
        return self


class ActiveRunsResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    active_runs: list[ActiveRun] = Field(default_factory=list)
```

Add `model_validator` to imports:
```python
from pydantic import BaseModel, ConfigDict, Field, model_validator
```

- [ ] **Step 4: Run test to verify it passes**

```
.venv/Scripts/python -m pytest tests/api/test_models_active_run.py -v
```

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_web/api/models.py tests/api/test_models_active_run.py
git commit -m "feat(api/models): add ActiveRun + ActiveRunsResponse DTOs (Phase 2A Task 3)"
```

---

## Task 4: `api/routes.py` — `GET /runs/active` endpoint (TDD)

**Files:**
- Modify: `src/mctrader_web/api/routes.py`
- Test: `tests/api/test_active_runs_endpoint.py`

- [ ] **Step 1: Write failing test**

Create `tests/api/test_active_runs_endpoint.py`:

```python
"""Phase 2A — GET /runs/active endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.conftest import auth_headers


@pytest.mark.asyncio
async def test_runs_active_empty(app_client: AsyncClient) -> None:
    resp = await app_client.get("/runs/active", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"active_runs": []}


@pytest.mark.asyncio
async def test_runs_active_unauthorized_without_token(app_client: AsyncClient) -> None:
    resp = await app_client.get("/runs/active")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_runs_active_with_backtest(
    app, app_client: AsyncClient, monkeypatch
) -> None:
    """When a backtest is queued, it shows up in the active runs list."""
    from datetime import datetime, timezone

    from mctrader_web.api.models import BacktestRequest, BacktestStatus

    fake_status = BacktestStatus(
        run_id="bt-sma-KRW-BTC-1h-2026-04-27-2026-05-04-5-20",
        lifecycle="running",
        started_at=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
    )
    fake_request = BacktestRequest(
        strategy="sma",
        symbol="KRW-BTC",
        timeframe="1h",
        start_iso="2026-04-27T07:00:00Z",
        end_iso="2026-05-04T07:00:00Z",
        fast=5,
        slow=20,
    )

    async def fake_list_all() -> list[BacktestStatus]:
        return [fake_status]

    def fake_get_request(run_id: str) -> BacktestRequest | None:
        return fake_request if run_id == fake_status.run_id else None

    monkeypatch.setattr(app.state.backtest_lifecycle, "list_all", fake_list_all)
    monkeypatch.setattr(app.state.backtest_lifecycle, "get_request", fake_get_request)

    resp = await app_client.get("/runs/active", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["active_runs"]) == 1
    run = body["active_runs"][0]
    assert run["mode"] == "backtest"
    assert run["status"] == "running"
    assert run["run_id"] == fake_status.run_id
    assert run["symbol"] == "KRW-BTC"
    assert run["timeframe"] == "1h"


@pytest.mark.asyncio
async def test_runs_active_filters_completed(
    app, app_client: AsyncClient, monkeypatch
) -> None:
    """Backtests in lifecycle 'completed' / 'error' are excluded."""
    from datetime import datetime, timezone

    from mctrader_web.api.models import BacktestRequest, BacktestStatus

    completed = BacktestStatus(
        run_id="bt-old",
        lifecycle="completed",
        started_at=datetime(2026, 4, 26, 7, 0, 0, tzinfo=timezone.utc),
    )
    running = BacktestStatus(
        run_id="bt-new",
        lifecycle="running",
        started_at=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
    )
    fake_request = BacktestRequest(
        strategy="sma", symbol="KRW-BTC", timeframe="1h",
        start_iso="2026-04-27T07:00:00Z", end_iso="2026-05-04T07:00:00Z",
    )

    async def fake_list_all() -> list[BacktestStatus]:
        return [completed, running]

    def fake_get_request(run_id: str) -> BacktestRequest | None:
        return fake_request

    monkeypatch.setattr(app.state.backtest_lifecycle, "list_all", fake_list_all)
    monkeypatch.setattr(app.state.backtest_lifecycle, "get_request", fake_get_request)

    resp = await app_client.get("/runs/active", headers=auth_headers())
    body = resp.json()
    assert len(body["active_runs"]) == 1
    assert body["active_runs"][0]["run_id"] == "bt-new"


@pytest.mark.asyncio
async def test_runs_active_with_paper_run(
    app, app_client: AsyncClient, monkeypatch
) -> None:
    """Codex finding #5: paper active run path."""
    from datetime import datetime, timezone

    from mctrader_web.api.models import RunRequest, RunStatus

    paper_status = RunStatus(
        run_id="paper-sma-KRW-BTC-5m-5-20",
        lifecycle="running",
        started_at=datetime(2026, 4, 27, 7, 0, 0, tzinfo=timezone.utc),
    )
    paper_request = RunRequest(
        strategy="sma",
        symbol="KRW-BTC",
        timeframe="5m",
        fast=5,
        slow=20,
    )

    paper_manager = app.state.lifecycle
    monkeypatch.setattr(
        type(paper_manager), "active_run_id",
        property(lambda self: paper_status.run_id),
    )

    async def fake_get_status(run_id: str) -> RunStatus:
        return paper_status

    def fake_get_request(run_id: str) -> RunRequest | None:
        return paper_request if run_id == paper_status.run_id else None

    monkeypatch.setattr(paper_manager, "get_status", fake_get_status)
    monkeypatch.setattr(paper_manager, "get_request", fake_get_request)

    resp = await app_client.get("/runs/active", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    paper_runs = [r for r in body["active_runs"] if r["mode"] == "paper"]
    assert len(paper_runs) == 1
    assert paper_runs[0]["run_id"] == paper_status.run_id
    assert paper_runs[0]["symbol"] == "KRW-BTC"
    assert paper_runs[0]["timeframe"] == "5m"
```

- [ ] **Step 2: Run tests to verify failure**

```
.venv/Scripts/python -m pytest tests/api/test_active_runs_endpoint.py -v
```

Expected: 404 for `/runs/active` (route undefined).

- [ ] **Step 3: Implement `GET /runs/active` in `routes.py`**

Add to `src/mctrader_web/api/routes.py` after the `get_evidence` route, before `# ─── Backtest endpoints ───`:

```python
    @router.get(
        "/runs/active",
        response_model=ActiveRunsResponse,
        dependencies=[Depends(auth_dep)],
    )
    async def get_active_runs(request: Request) -> ActiveRunsResponse:
        """Phase 2A — union of backtest + paper active runs for common sidebar."""
        from mctrader_web.api.models import ActiveRun

        bt_manager: BacktestLifecycleManager = request.app.state.backtest_lifecycle
        paper_manager: LifecycleManager = request.app.state.lifecycle

        active: list[ActiveRun] = []

        # Backtest active = lifecycle ∈ {queued, running, stopping}
        for bt in await bt_manager.list_all():
            if bt.lifecycle in ("queued", "running", "stopping"):
                # symbol/timeframe parsed from run_id pattern
                # bt-{strategy}-{symbol}-{tf}-{start}-{end}-{fast}-{slow}
                # We get them from the request stored alongside in lifecycle manager.
                req = bt_manager.get_request(bt.run_id)
                active.append(
                    ActiveRun(
                        run_id=bt.run_id,
                        mode="backtest",
                        symbol=req.symbol if req else "?",
                        timeframe=req.timeframe if req else "1h",
                        started_at_utc=bt.started_at,
                        status=bt.lifecycle,
                        output_dir=req.output_dir if req else None,
                    )
                )

        # Paper active = single-active model
        if paper_manager.active_run_id is not None:
            try:
                paper_status = await paper_manager.get_status(paper_manager.active_run_id)
                paper_req = paper_manager.get_request(paper_manager.active_run_id)
                active.append(
                    ActiveRun(
                        run_id=paper_status.run_id,
                        mode="paper",
                        symbol=paper_req.symbol if paper_req else "?",
                        timeframe=paper_req.timeframe if paper_req else "5m",
                        started_at_utc=paper_status.started_at,
                        status=paper_status.lifecycle,
                        output_dir=None,  # paper output dir not tracked yet
                    )
                )
            except Exception:  # noqa: BLE001 — fall back silently
                pass

        return ActiveRunsResponse(active_runs=active)
```

Add `ActiveRunsResponse` to the import block at top of file:
```python
from mctrader_web.api.models import (
    ActiveRun,
    ActiveRunsResponse,
    BacktestListResponse,
    # ...
)
```

- [ ] **Step 4a: Add `get_request` helper to `BacktestLifecycleManager`**

Modify `src/mctrader_web/api/backtest_lifecycle.py`. Add method (after `list_all`):

```python
    def get_request(self, run_id: str) -> BacktestRequest | None:
        """Synchronous lookup of stored request — None if unknown."""
        entry = self._tasks.get(run_id)
        return entry["request"] if entry else None
```

(Verified: `BacktestLifecycleManager.start` already stores `"request": request` at line 60.)

- [ ] **Step 4b: Modify `LifecycleManager.start` to store `request` + add `get_request`**

Open `src/mctrader_web/api/lifecycle.py`. Locate the `self._active = { ... }` assignment (around line 97-102):

```python
            self._active = {
                "runner": runner,
                "status": status,
                "task": task,
                "lock_cm": lock_cm,
            }
```

Change to:

```python
            self._active = {
                "runner": runner,
                "status": status,
                "task": task,
                "lock_cm": lock_cm,
                "request": request,  # Phase 2A — used by GET /runs/active
            }
```

Add `get_request` method on `LifecycleManager`:

```python
    def get_request(self, run_id: str) -> RunRequest | None:
        """Synchronous lookup of stored request — None if not active or mismatch."""
        if self._active is None:
            return None
        if self._active["status"].run_id != run_id:
            return None
        return self._active.get("request")
```

- [ ] **Step 4c: Extend conftest with `app` fixture for direct app.state access**

Modify `tests/api/conftest.py`. Refactor to expose the FastAPI `app` directly:

```python
"""Shared fixtures for FastAPI MCT-50 tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from mctrader_web.api.app import create_app

TEST_TOKEN = "test-token-fixed-for-fast-tests-32-bytes!"


@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("MCTRADER_TOKEN_PATH", str(tmp_path / "local_token"))
    monkeypatch.setenv("MCTRADER_LOCK_PATH", str(tmp_path / "paper.lock"))
    return tmp_path


@pytest.fixture
def app(isolated_paths: Path) -> FastAPI:
    """Phase 2A — expose the FastAPI app directly for state introspection."""
    return create_app(token=TEST_TOKEN)


@pytest_asyncio.fixture
async def app_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TEST_TOKEN}"}
```

Existing tests using only `app_client` continue to work. New tests can request both `app` and `app_client` fixtures.

- [ ] **Step 5: Run tests to verify pass**

```
.venv/Scripts/python -m pytest tests/api/test_active_runs_endpoint.py -v
```

Expected: 4 PASS.

- [ ] **Step 6: Run full api test suite to confirm no regression**

```
.venv/Scripts/python -m pytest tests/api/ -v
```

Expected: all existing + new tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/mctrader_web/api/routes.py src/mctrader_web/api/backtest_lifecycle.py src/mctrader_web/api/lifecycle.py tests/api/test_active_runs_endpoint.py
git commit -m "feat(api): GET /runs/active endpoint (Phase 2A Task 4)"
```

---

## Task 5: `api_client/client.py` — `list_active_runs` method (TDD)

**Files:**
- Modify: `src/mctrader_web/api_client/client.py`
- Test: `tests/api/test_active_runs_endpoint.py` (extend) or new `tests/test_api_client_active_runs.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_api_client_active_runs.py`:

```python
"""Phase 2A — MctraderApiClient.list_active_runs tests."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from mctrader_web.api_client.client import MctraderApiClient


@pytest.fixture
def fake_token(tmp_path: Path, monkeypatch) -> Path:
    token_file = tmp_path / "local_token"
    token_file.write_text("fake-token", encoding="utf-8")
    monkeypatch.setenv("MCTRADER_TOKEN_PATH", str(token_file))
    return token_file


def test_list_active_runs_happy(fake_token: Path, monkeypatch) -> None:
    fake_response = {
        "active_runs": [
            {
                "run_id": "bt-x",
                "mode": "backtest",
                "symbol": "KRW-BTC",
                "timeframe": "1h",
                "started_at_utc": "2026-04-27T07:00:00Z",
                "status": "running",
                "output_dir": "./out",
            }
        ]
    }

    captured = {}

    def fake_get(self, url, **kwargs):  # type: ignore[no-untyped-def]
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        return httpx.Response(200, json=fake_response, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    client = MctraderApiClient(token_path=fake_token)
    result = client.list_active_runs()

    assert result is not None
    assert len(result["active_runs"]) == 1
    assert result["active_runs"][0]["mode"] == "backtest"
    assert captured["url"] == "/runs/active"
    assert captured["headers"]["Authorization"] == "Bearer fake-token"


def test_list_active_runs_returns_none_on_500(fake_token: Path, monkeypatch) -> None:
    def fake_get(self, url, **kwargs):  # type: ignore[no-untyped-def]
        return httpx.Response(500, json={"error": "boom"}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    client = MctraderApiClient(token_path=fake_token)
    assert client.list_active_runs() is None


def test_list_active_runs_returns_none_on_connection_error(
    fake_token: Path, monkeypatch
) -> None:
    def fake_get(self, url, **kwargs):  # type: ignore[no-untyped-def]
        raise httpx.ConnectError("connect failed")

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    client = MctraderApiClient(token_path=fake_token)
    assert client.list_active_runs() is None
```

- [ ] **Step 2: Run test to verify failure**

```
.venv/Scripts/python -m pytest tests/test_api_client_active_runs.py -v
```

Expected: AttributeError on `list_active_runs`.

- [ ] **Step 3: Add method to `client.py`**

Append to `src/mctrader_web/api_client/client.py`:

```python
    # ─── Active runs (Phase 2A) ───
    def list_active_runs(self) -> dict[str, Any] | None:
        """Phase 2A — fetch backtest + paper active run list. None on any error."""
        try:
            with httpx.Client(base_url=self._base_url, timeout=5.0) as c:
                r = c.get("/runs/active", headers=self._headers())
                if r.status_code == 200:
                    return r.json()
                return None
        except (httpx.HTTPError, OSError):
            return None
```

- [ ] **Step 4: Run tests to verify pass**

```
.venv/Scripts/python -m pytest tests/test_api_client_active_runs.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_web/api_client/client.py tests/test_api_client_active_runs.py
git commit -m "feat(api_client): add list_active_runs method (Phase 2A Task 5)"
```

---

## Task 6: `dashboard/common.py` — `render_common_sidebar` + TZ default init

**Files:**
- Modify: `src/mctrader_web/dashboard/common.py`
- Test: deferred to Task 11 (AppTest smoke covers UI render)

- [ ] **Step 1: Add TZ session_state initializer**

Append to `src/mctrader_web/dashboard/common.py`:

```python
import streamlit as st

from mctrader_web.api_client import MctraderApiClient

DEFAULT_TZ = "Asia/Seoul"
TZ_OPTIONS = ("Asia/Seoul", "UTC")


def init_tz_session_state() -> None:
    """Set st.session_state['tz'] = DEFAULT_TZ if not already set.

    Session-scoped only — survives page navigation but not browser tab close
    or server restart (Codex finding #4).
    """
    if "tz" not in st.session_state:
        st.session_state["tz"] = DEFAULT_TZ


def tz_label(tz_name: str) -> str:
    """Human-friendly TZ label for column headers / form labels."""
    return "KST" if tz_name == "Asia/Seoul" else "UTC"
```

- [ ] **Step 2: Add `render_common_sidebar`**

Append to `src/mctrader_web/dashboard/common.py`:

```python
def render_common_sidebar(client: MctraderApiClient) -> None:
    """Common sidebar block called from every page.

    Order: TZ selector → Service health → Active runs.
    Active runs failure is silent (caption + continue) per Codex finding #4.
    """
    with st.sidebar:
        # 1. TZ selector
        st.subheader("🌐 TimeZone")
        current_tz = st.session_state.get("tz", DEFAULT_TZ)
        index = TZ_OPTIONS.index(current_tz) if current_tz in TZ_OPTIONS else 0
        st.session_state["tz"] = st.selectbox(
            "TimeZone",
            options=TZ_OPTIONS,
            index=index,
            label_visibility="collapsed",
        )

        # 2. Service health
        st.subheader("Service")
        if client.health():
            st.success("FastAPI OK (127.0.0.1:7821)")
        else:
            st.error("FastAPI unreachable. Start with `mctrader-web-api`.")

        # 3. Active runs (Phase 2A Q1-A)
        st.subheader("Active runs")
        try:
            payload = client.list_active_runs()
        except Exception as exc:  # noqa: BLE001 — graceful fallback
            st.caption(f"Active runs unavailable: {type(exc).__name__}")
            return

        if not payload or not payload.get("active_runs"):
            st.caption("No active runs.")
            return

        from datetime import datetime, timezone as dt_tz
        now_utc = datetime.now(dt_tz.utc)

        for run in payload["active_runs"]:
            started_iso = run.get("started_at_utc", "")
            try:
                started = datetime.fromisoformat(started_iso.replace("Z", "+00:00"))
                elapsed = (now_utc - started).total_seconds()
                elapsed_text = f"{elapsed:.0f}s"
            except (ValueError, TypeError):
                elapsed_text = "?"
            st.markdown(
                f"**`{run.get('run_id', '?')}`** · "
                f"`{run.get('mode', '?')}` · "
                f"{run.get('symbol', '?')}/{run.get('timeframe', '?')} · "
                f"elapsed {elapsed_text} · "
                f"`{run.get('status', '?')}`"
            )
```

- [ ] **Step 3: Sanity-check syntax**

```
.venv/Scripts/python -c "import mctrader_web.dashboard.common as m; print(dir(m))"
```

Expected: prints module attrs incl. `render_common_sidebar`, `init_tz_session_state`.

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_web/dashboard/common.py
git commit -m "feat(dashboard/common): add render_common_sidebar + tz init (Phase 2A Task 6)"
```

---

## Task 7: `dashboard/app.py` — TZ default + entry comment

**Files:**
- Modify: `src/mctrader_web/dashboard/app.py`

- [ ] **Step 1: Add TZ init in `main()`**

Read `src/mctrader_web/dashboard/app.py` and modify `main()`. After `st.set_page_config(...)` and before any other UI, add:

```python
    from mctrader_web.dashboard.common import init_tz_session_state
    init_tz_session_state()
```

The full `main()` should look like:

```python
def main() -> None:  # pragma: no cover - Streamlit entrypoint
    st.set_page_config(page_title="mctrader dashboard", layout="wide")

    from mctrader_web.dashboard.common import init_tz_session_state
    init_tz_session_state()

    st.sidebar.title("mctrader")
    # ... rest of existing main()
```

(Keep the existing `main()` body intact — only insert the 2 lines above.)

- [ ] **Step 2: Sanity-check import resolution**

```
.venv/Scripts/python -c "from mctrader_web.dashboard.app import main; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_web/dashboard/app.py
git commit -m "feat(dashboard/app): init TZ session_state on entry (Phase 2A Task 7)"
```

---

## Task 8: `dashboard/pages/01_paper_panel.py` — common sidebar migration

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/01_paper_panel.py`

- [ ] **Step 1: Replace existing sidebar block with common sidebar call**

In `src/mctrader_web/dashboard/pages/01_paper_panel.py`, locate this block (lines ~22-33):

```python
# Sidebar — service health + token status.
with st.sidebar:
    st.subheader("Service")
    if client.health():
        st.success("FastAPI OK (127.0.0.1:7821)")
    else:
        st.error("FastAPI unreachable. Start with `mctrader-web-api`.")
    svc = client.status()
    if svc:
        st.write(f"version: `{svc.get('version', '?')}`")
        st.write(f"uptime: `{float(svc.get('uptime_seconds', 0)):.1f}s`")
        st.write(f"active_run_id: `{svc.get('active_run_id') or 'none'}`")
```

Replace with:

```python
from mctrader_web.dashboard.common import init_tz_session_state, render_common_sidebar

init_tz_session_state()
render_common_sidebar(client)

# paper-specific service status (was in sidebar) → main panel header strip
svc = client.status()
if svc:
    st.caption(
        f"version: `{svc.get('version', '?')}` · "
        f"uptime: `{float(svc.get('uptime_seconds', 0)):.1f}s` · "
        f"active_run_id: `{svc.get('active_run_id') or 'none'}`"
    )
```

- [ ] **Step 2: Verify page imports clean**

```
.venv/Scripts/python -c "import importlib.util; spec = importlib.util.spec_from_file_location('p', 'src/mctrader_web/dashboard/pages/01_paper_panel.py'); m = importlib.util.module_from_spec(spec); print('import ok')"
```

(Note: streamlit pages can't run standalone fully, but imports should resolve.)

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_web/dashboard/pages/01_paper_panel.py
git commit -m "refactor(paper_panel): use render_common_sidebar (Phase 2A Task 8)"
```

---

## Task 9: `dashboard/pages/02_backtest_panel.py` — datetime picker (native split)

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/02_backtest_panel.py`

- [ ] **Step 1: Replace ISO text inputs with date_input + time_input split**

In `src/mctrader_web/dashboard/pages/02_backtest_panel.py`, locate this block:

```python
    col4, col5 = st.columns(2)
    start_iso = col4.text_input("start (ISO 8601 UTC)", value="2026-04-27T07:00:00Z")
    end_iso = col5.text_input("end (ISO 8601 UTC)", value="2026-05-04T07:00:00Z")
```

Replace with:

```python
    from datetime import datetime, timedelta, timezone as dt_tz
    from zoneinfo import ZoneInfo
    from mctrader_web.dashboard.common import init_tz_session_state, tz_label

    init_tz_session_state()
    tz_name = st.session_state["tz"]
    tz_lbl = tz_label(tz_name)
    user_zone = ZoneInfo(tz_name)

    now_in_tz = datetime.now(dt_tz.utc).astimezone(user_zone)
    default_end = now_in_tz.replace(second=0, microsecond=0)
    default_start = default_end - timedelta(days=7)

    col_sd, col_st, col_ed, col_et = st.columns(4)
    start_date = col_sd.date_input(
        f"Start Date ({tz_lbl})", value=default_start.date()
    )
    start_time = col_st.time_input(
        f"Start Time ({tz_lbl})",
        value=default_start.time().replace(second=0, microsecond=0),
        step=timedelta(minutes=1),
    )
    end_date = col_ed.date_input(
        f"End Date ({tz_lbl})", value=default_end.date()
    )
    end_time = col_et.time_input(
        f"End Time ({tz_lbl})",
        value=default_end.time().replace(second=0, microsecond=0),
        step=timedelta(minutes=1),
    )
```

- [ ] **Step 2: Add UTC echo + validation directly above the submit button**

Below the time inputs and above `submitted = st.form_submit_button("Run Backtest")`, insert:

```python
    # Combine date+time and convert to UTC ISO 8601
    try:
        start_dt_local = datetime.combine(start_date, start_time, tzinfo=user_zone)
        end_dt_local = datetime.combine(end_date, end_time, tzinfo=user_zone)
        start_utc = start_dt_local.astimezone(dt_tz.utc)
        end_utc = end_dt_local.astimezone(dt_tz.utc)
        start_iso = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError) as exc:
        st.error(f"Invalid date/time: {exc}")
        start_iso = ""
        end_iso = ""

    # Read-only UTC echo (Codex finding #5)
    if start_iso and end_iso:
        st.caption(f"→ FastAPI: `{start_iso}` → `{end_iso}` (UTC)")

    # Validation
    now_utc = datetime.now(dt_tz.utc)
    submit_disabled = False
    if not start_iso or not end_iso:
        submit_disabled = True
    elif start_utc >= end_utc:  # type: ignore[possibly-undefined]
        st.error(
            f"Start must be before End. "
            f"start={start_dt_local.isoformat()} ({tz_lbl}) / "
            f"end={end_dt_local.isoformat()} ({tz_lbl}) — "
            f"UTC: start={start_iso} end={end_iso}"
        )
        submit_disabled = True
    elif end_utc > now_utc:  # type: ignore[possibly-undefined]
        st.error(
            f"End must be in the past (backtest = historical). "
            f"end={end_dt_local.isoformat()} ({tz_lbl}) — "
            f"now_utc={now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
        submit_disabled = True
```

Then change the submit button line:

```python
    submitted = st.form_submit_button("Run Backtest", disabled=submit_disabled)
```

- [ ] **Step 3: Sanity-check syntax**

```
.venv/Scripts/python -c "import ast; ast.parse(open('src/mctrader_web/dashboard/pages/02_backtest_panel.py').read()); print('ok')"
```

Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_web/dashboard/pages/02_backtest_panel.py
git commit -m "feat(backtest_panel): native date+time picker + UTC echo + validation (Phase 2A Task 9)"
```

---

## Task 10: `dashboard/pages/02_backtest_panel.py` — common sidebar + events table redesign

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/02_backtest_panel.py`

- [ ] **Step 1: Move Task 9 inline imports to file top + replace sidebar with common sidebar (Codex #15)**

Open `src/mctrader_web/dashboard/pages/02_backtest_panel.py`. Two coordinated edits:

**(a)** **Move Task 9 inline imports** out of the form body. Task 9 added `from datetime import datetime, timedelta, timezone as dt_tz` / `from zoneinfo import ZoneInfo` / `from mctrader_web.dashboard.common import init_tz_session_state, tz_label` inside `with st.form("backtest_form"):`. Remove those inline imports entirely from inside the form.

**(b)** Replace the existing sidebar block at the file's top:

```python
with st.sidebar:
    st.subheader("Service")
    if client.health():
        st.success("FastAPI OK (127.0.0.1:7821)")
    else:
        st.error("FastAPI unreachable. Start with `mctrader-web-api`.")
```

with the consolidated import-and-init block:

```python
from datetime import datetime, timedelta, timezone as dt_tz
from zoneinfo import ZoneInfo

from mctrader_web.dashboard.common import (
    compute_fee,
    compute_notional,
    format_bps,
    format_krw,
    format_qty,
    format_ts,
    init_tz_session_state,
    parse_order_seq,
    render_common_sidebar,
    tz_label,
)

init_tz_session_state()
render_common_sidebar(client)
```

After this edit, `init_tz_session_state()` is called exactly **once** at module top — Task 9's inline `init_tz_session_state()` inside the form must also be removed (it was redundant if left).

- [ ] **Step 2: Replace events dataframe with rich table**

Locate this block (in the Completed runs section):

```python
        with st.expander("Trade Events"):
            events = [
                e for e in report.get("events", [])
                if e.get("kind") == "OrderEvent" and e.get("status_to") == "FILLED"
            ]
            if events:
                st.dataframe(events)
            else:
                st.write("No fills.")
```

Replace with:

```python
        with st.expander("Trade Events"):
            from decimal import Decimal as _Dec

            tz_name = st.session_state["tz"]
            tz_lbl = tz_label(tz_name)

            show_all = st.checkbox(
                "Show all events (default = FILLED only)", value=False
            )

            all_order_events = [
                e for e in report.get("events", []) if e.get("kind") == "OrderEvent"
            ]
            events = (
                all_order_events
                if show_all
                else [e for e in all_order_events if e.get("status_to") == "FILLED"]
            )

            if not events:
                st.caption("No matching events.")
            else:
                rows = []
                for e in events:
                    ts_str = e.get("ts_utc", "")
                    try:
                        ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        ts_dt = None

                    side = e.get("side")  # Phase 2A: legacy events have None
                    side_cell = "—"  # Phase 2A — Phase 2B fills BUY/SELL with color

                    fill_price = e.get("fill_price")
                    fill_qty = e.get("fill_quantity")
                    fee_bps_v = e.get("fee_bps")
                    slip_bps_v = e.get("slippage_bps")

                    price_dec = _Dec(fill_price) if fill_price is not None else None
                    qty_dec = _Dec(fill_qty) if fill_qty is not None else None
                    fee_bps_dec = _Dec(fee_bps_v) if fee_bps_v is not None else None
                    slip_bps_dec = _Dec(slip_bps_v) if slip_bps_v is not None else None

                    notional_dec = compute_notional(price_dec, qty_dec)
                    fee_dec = compute_fee(notional_dec, fee_bps_dec)

                    rows.append(
                        {
                            f"Time ({tz_lbl})": format_ts(ts_dt, tz_name),
                            "Side": side_cell,
                            "#": parse_order_seq(e.get("order_id", ""), run.run_id),
                            "Status": e.get("status_to", "—"),
                            "Price": format_krw(price_dec),
                            "Qty": format_qty(qty_dec),
                            "Notional": format_krw(notional_dec),
                            "Fee": format_krw(fee_dec),
                            "Fee bps": format_bps(fee_bps_dec),
                            "Slip bps": format_bps(slip_bps_dec),
                        }
                    )

                st.dataframe(rows, use_container_width=True, hide_index=True)
```

Make sure `from datetime import datetime` is in the file's imports. It should already be there from Task 9; if not add it at the top.

- [ ] **Step 3: Sanity-check**

```
.venv/Scripts/python -c "import ast; ast.parse(open('src/mctrader_web/dashboard/pages/02_backtest_panel.py').read()); print('ok')"
```

Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_web/dashboard/pages/02_backtest_panel.py
git commit -m "feat(backtest_panel): common sidebar + events table redesign (Phase 2A Task 10)"
```

---

## Task 11: AppTest smoke — sidebar TZ + datetime form validation + events table

**Files:**
- Test: `tests/test_apptest_phase2a.py`

- [ ] **Step 1: Write AppTest scenarios (Codex push-back: rich coverage, not just smoke)**

Create `tests/test_apptest_phase2a.py`:

```python
"""Phase 2A — Streamlit AppTest scenarios.

Covers (per Codex phase review):
- App loads + TZ default = Asia/Seoul
- Common sidebar fallback when client raises (Codex #6)
- Common sidebar populated active runs (Codex #2)
- Backtest panel datetime invalid range disables submit (Codex #3)
- Backtest panel events table with populated event row builder (Codex #4)
- Both pages render without crash (FastAPI unreachable acceptable)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

# Codex #14 — path hardening: resolve from this file's location, not CWD.
REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = str(REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "app.py")
BACKTEST_PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "02_backtest_panel.py"
)
PAPER_PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "01_paper_panel.py"
)


def _make_minimal_run(out_dir: Path, *, events: list[dict] | None = None) -> Path:
    """Create a minimal run directory with execution_report.json + equity_curve.csv."""
    run_dir = out_dir / "bt-test"
    run_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "execution_report.v1",
        "run_id": "bt-test",
        "mode": "backtest",
        "strategy": {"name": "sma", "params": {}},
        "symbol": "KRW-BTC",
        "timeframe": "1h",
        "period": {"start": "2026-04-27T07:00:00Z", "end": "2026-05-04T07:00:00Z"},
        "initial_capital": "1000000",
        "slippage_fee_latency_config": {
            "fee_bps": "25",
            "base_slippage_bps": "5",
            "volatility_factor": "1",
            "tick_bps_adjustment": "0",
            "latency_ms": 0,
        },
        "events": events or [],
        "summary": {
            "final_equity": "1000000",
            "max_drawdown": "0",
            "total_trades": 0,
        },
        "created_at": "2026-04-27T07:00:00Z",
    }
    (run_dir / "execution_report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    (run_dir / "equity_curve.csv").write_text(
        "ts_utc,equity,position_quantity,realized_pnl,unrealized_pnl,cash\n"
        "2026-04-27T07:00:00Z,1000000,0,0,0,1000000\n",
        encoding="utf-8",
    )
    return run_dir


# ─── App entry + TZ default ──────────────────────────────────────────────────


def test_app_loads_without_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert not at.exception, f"app crashed: {at.exception}"


def test_tz_session_state_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert at.session_state["tz"] == "Asia/Seoul"


# ─── Common sidebar — fallback paths (Codex #2, #6) ──────────────────────────


def test_sidebar_fallback_when_client_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex finding #6: sidebar's try/except path renders 'unavailable' caption."""
    from mctrader_web.api_client.client import MctraderApiClient

    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    def boom(self) -> None:
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(MctraderApiClient, "list_active_runs", boom)
    monkeypatch.setattr(MctraderApiClient, "health", lambda self: False)

    at = AppTest.from_file(BACKTEST_PAGE).run(timeout=30)
    assert not at.exception, f"page crashed: {at.exception}"
    # Look for 'Active runs unavailable' in any sidebar caption
    captions = [c.value for c in at.sidebar.caption]
    assert any("Active runs unavailable" in str(c) for c in captions), (
        f"expected fallback caption, got captions={captions}"
    )


def test_sidebar_populated_active_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex finding #2: sidebar renders run_id, mode, symbol/timeframe."""
    from mctrader_web.api_client.client import MctraderApiClient

    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    def fake_list(self):
        return {
            "active_runs": [
                {
                    "run_id": "bt-sma-KRW-BTC-1h-x",
                    "mode": "backtest",
                    "symbol": "KRW-BTC",
                    "timeframe": "1h",
                    "started_at_utc": "2026-04-27T07:00:00Z",
                    "status": "running",
                    "output_dir": "./out",
                }
            ]
        }

    monkeypatch.setattr(MctraderApiClient, "list_active_runs", fake_list)
    monkeypatch.setattr(MctraderApiClient, "health", lambda self: True)

    at = AppTest.from_file(BACKTEST_PAGE).run(timeout=30)
    assert not at.exception, f"page crashed: {at.exception}"
    # markdown 으로 출력된 run_id text 확인
    sidebar_text = " ".join(
        m.value for m in at.sidebar.markdown if hasattr(m, "value")
    )
    assert "bt-sma-KRW-BTC-1h-x" in sidebar_text
    assert "backtest" in sidebar_text


# ─── Backtest panel — datetime form (Codex #3) ───────────────────────────────


def test_backtest_form_renders_with_utc_echo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex finding #3: UTC echo caption appears below datetime inputs."""
    from mctrader_web.api_client.client import MctraderApiClient

    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    monkeypatch.setattr(MctraderApiClient, "health", lambda self: True)
    monkeypatch.setattr(MctraderApiClient, "list_active_runs", lambda self: None)

    at = AppTest.from_file(BACKTEST_PAGE).run(timeout=30)
    assert not at.exception, f"page crashed: {at.exception}"
    captions = " ".join(c.value for c in at.caption if hasattr(c, "value"))
    # form 의 default 값은 7-day-ago → now, 즉 valid range. UTC echo 가 보여야 함.
    assert "→ FastAPI:" in captions and "(UTC)" in captions, (
        f"expected UTC echo caption, got: {captions}"
    )


def test_backtest_form_invalid_range_shows_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex finding #3: setting end < start shows error + disables submit.

    AppTest 에서 date_input 의 set_value 후 rerun 하여 validation 흐름 trigger.
    """
    from datetime import date

    from mctrader_web.api_client.client import MctraderApiClient

    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path)

    monkeypatch.setattr(MctraderApiClient, "health", lambda self: True)
    monkeypatch.setattr(MctraderApiClient, "list_active_runs", lambda self: None)

    at = AppTest.from_file(BACKTEST_PAGE).run(timeout=30)
    assert not at.exception

    # Set start = today, end = 7 days ago → invalid (start > end)
    # date_input widgets are at index 0/2 of the form's date_inputs
    date_inputs = at.date_input
    if len(date_inputs) >= 2:
        # 0 = start, 1 = end (per form column order col_sd, col_ed)
        # column order in the plan: start_date, start_time, end_date, end_time
        # so date_input[0] = start_date, date_input[1] = end_date
        date_inputs[0].set_value(date(2026, 5, 4))  # start
        date_inputs[1].set_value(date(2026, 4, 27))  # end (earlier)
        at = at.run(timeout=30)
        assert not at.exception
        errors = " ".join(e.value for e in at.error if hasattr(e, "value"))
        assert "Start must be before End" in errors, f"expected error, got: {errors}"


# ─── Backtest panel — events table populated row (Codex #4) ──────────────────


def test_backtest_events_table_populated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex finding #4: events row builder runs against a real OrderEvent."""
    from mctrader_web.api_client.client import MctraderApiClient

    populated_events = [
        {
            "kind": "OrderEvent",
            "ts_utc": "2026-04-27T07:05:00Z",
            "order_id": "bt:bt-test:1",
            "status_from": "ACCEPTED",
            "status_to": "FILLED",
            "fill_price": "145200000",
            "fill_quantity": "0.001",
            "fee_bps": "25",
            "slippage_bps": "5",
        },
        {
            # malformed ts_utc → format_ts should display "—" or similar fallback
            "kind": "OrderEvent",
            "ts_utc": "not-a-timestamp",
            "order_id": "paper:other-run:99",  # mismatched run_id → original returned
            "status_from": "ACCEPTED",
            "status_to": "FILLED",
            "fill_price": "150000000",
            "fill_quantity": "0.0005",
            "fee_bps": "25",
            "slippage_bps": "5",
        },
    ]

    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))
    _make_minimal_run(tmp_path, events=populated_events)

    monkeypatch.setattr(MctraderApiClient, "health", lambda self: True)
    monkeypatch.setattr(MctraderApiClient, "list_active_runs", lambda self: None)

    at = AppTest.from_file(BACKTEST_PAGE).run(timeout=30)
    assert not at.exception, f"page crashed: {at.exception}"
    # No exception = row builder ran. Detailed DOM cell value assertion is
    # brittle in AppTest; the row count + non-crash is the contract here.


# ─── Page-level smoke (regression) ───────────────────────────────────────────


def test_paper_panel_renders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Smoke: paper panel page imports + renders without crash (FastAPI unreachable OK)."""
    monkeypatch.setenv("MCTRADER_OUTPUT_DIR", str(tmp_path))

    at = AppTest.from_file(PAPER_PAGE).run(timeout=30)
    assert not at.exception, f"paper panel crashed: {at.exception}"
```

- [ ] **Step 2: Run AppTest smoke**

```
.venv/Scripts/python -m pytest tests/test_apptest_phase2a.py -v
```

Expected: 4 PASS. (FastAPI is unreachable in test env — common sidebar shows "FastAPI unreachable" but doesn't crash.)

- [ ] **Step 3: Run full test suite to confirm no regression**

```
.venv/Scripts/python -m pytest tests/ -v
```

Expected: all PASS (existing + Phase 2A new tests).

- [ ] **Step 4: Run ruff + pyright**

```
.venv/Scripts/python -m ruff check src/ tests/
.venv/Scripts/python -m pyright src/ tests/
```

Expected: 0 errors. Fix any reported issues before committing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_apptest_phase2a.py
git commit -m "test(phase-2a): AppTest smoke for sidebar + panels (Phase 2A Task 11)"
```

---

## Task 12: PR creation + final integration verification

**Files:** none (git + GitHub)

- [ ] **Step 1: Verify branch state**

```
cd c:/workspace/mclayer/mctrader-web
git status
git log --oneline main..feat/phase-2a-web-ui
```

Expected: 11 commits (one per Task 1-11).

- [ ] **Step 2: Push branch**

```
git push -u origin feat/phase-2a-web-ui
```

- [ ] **Step 3: Open PR**

```
gh pr create \
  --title "feat: mctrader-web Phase 2A — active runs sidebar + TZ selector + native datetime picker + events table" \
  --body "$(cat <<'EOF'
## Summary
Phase 2A web-only enhancement (5 user requirements minus engine artifact contract).

- **Active runs sidebar (FastAPI `GET /runs/active` + common sidebar helper)** — page 간 navigation 시에도 진행중 작업 가시성.
- **TimeZone selector** (sidebar 상단, UTC + KST, default KST). backend 는 항상 UTC 영구 보존, UI 표시만 변환.
- **Native datetime picker** (`st.date_input` + `st.time_input` split, minute granularity, validation: start < end + end <= now, UTC echo).
- **Events table 재구성**: order_id prefix 제거 (anchored regex), Notional/Fee UI 계산 (Phase 2B 에서 schema 필드로 강등 예정), status_to default filter + show all toggle, KRW formatter 중앙화.
- **Side column 은 \"—\"** (현 schema 필드 없음 — Phase 2B 에서 BUY/SELL color coding 추가).

Spec: `mctrader-hub/docs/superpowers/specs/2026-05-04-mctrader-web-phase-2a-design.md`
Plan: `mctrader-hub/docs/superpowers/plans/2026-05-04-mctrader-web-phase-2a.md`

## Test plan
- [ ] `pytest tests/` all PASS
- [ ] `ruff check` + `pyright` clean
- [ ] manual: `streamlit run src/mctrader_web/dashboard/app.py` — sidebar shows TZ + service + active runs sections, both pages load without crash
- [ ] manual: backtest panel datetime form — invalid range disables button + shows TZ + UTC error
- [ ] manual: backtest panel events table — column order matches design, status_to filter toggle works
EOF
)"
```

- [ ] **Step 4: Wait for CI**

```
gh pr checks --watch
```

Expected: CI green.

- [ ] **Step 5: Admin merge + return to main** (per user memory: admin merge autonomy)

```
gh pr merge --admin --squash
git checkout main
git pull origin main
```

---

## Spec coverage map

| Spec section | Implementing task |
|---|---|
| §3.2 file map | Tasks 1-10 |
| §3.3 FastAPI new endpoint `/runs/active` | Task 4 |
| §3.4 session_state contract | Task 6 (`init_tz_session_state`), Task 7 (entry init) |
| §3.5 TZ boundary protocol | Task 9 (UTC echo + ISO 8601 conversion) + format_ts naive rejection (Task 1) |
| §3.6 datetime picker UX | Task 9 |
| §3.7 active runs sidebar | Tasks 4, 5, 6 |
| §3.8 events table redesign | Task 10 |
| §3.9 centralized formatter | Tasks 1, 2 |
| §4 Testing strategy | Tasks 1, 2, 3, 4, 5, 11 |
| §5 Backward compatibility | Task 6 (silent fallback for `/runs/active` missing), Task 10 (status_to filter for legacy) |

## Out of scope (not in plan)
- `OrderEvent.side / notional / fee` schema 추가 → Phase 2B
- `candles.csv / indicators.csv` → Phase 2B
- Candlestick + indicator overlay + buy/sell marker → Phase 2B
- Browser local TZ / US/Eastern / 등 → Phase 3
- Cookie / query param 으로 TZ persist → Phase 3
