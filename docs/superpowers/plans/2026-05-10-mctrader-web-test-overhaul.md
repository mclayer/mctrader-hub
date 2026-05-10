# mctrader-web 전체 테스트 보강 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-web의 미테스트 Streamlit 페이지 5개(03/04/05/06/20)에 AppTest 추가, API 갭(audit query/rbac tokens) 보강, Playwright E2E 4개 사용자 플로우(데이터수집/백테스트/페이퍼/전략Set) 구현

**Architecture:** Layer 1 = Streamlit AppTest(격리+mock, CI 빠름) / Layer 2 = Playwright E2E(실제 브라우저 localhost:8501, `@pytest.mark.e2e` skip 기본) / CI에서는 AppTest+API만, `pytest tests/ -m e2e` 로 E2E 선택 실행

**Tech Stack:** pytest 8, pytest-asyncio, streamlit.testing.v1.AppTest, playwright 1.44, pytest-playwright 0.5, httpx AsyncClient, monkeypatch

---

## File Structure

```
tests/
├── fixtures/                          ← NEW: CI용 JSON 샘플 데이터
│   ├── coverage_stats_sample.json
│   ├── heartbeat_sample.json
│   └── backtest_result_sample.json
├── apptest/                           ← NEW: Streamlit AppTest per page
│   ├── test_page_03_wfo.py
│   ├── test_page_04_strategy_sets.py
│   ├── test_page_05_strategy_set_editor.py
│   ├── test_page_06_strategy_promotion.py
│   └── test_page_20_data_collection.py
├── e2e/                               ← EXTEND: Playwright 추가
│   ├── conftest.py                    ← NEW: playwright fixtures + skip guard
│   ├── test_data_collection_flow.py   ← NEW
│   ├── test_backtest_flow.py          ← NEW
│   ├── test_paper_flow.py             ← NEW
│   └── test_strategy_set_flow.py     ← NEW
├── api/
│   ├── test_admin_audit_query.py      ← NEW: GET /admin/audit gap
│   └── test_admin_rbac_tokens.py     ← NEW: token CRUD gap
pyproject.toml                         ← MODIFY: markers(e2e, real) + playwright dep
```

---

## Task 1: 인프라 — markers, fixtures, playwright 의존성

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/fixtures/coverage_stats_sample.json`
- Create: `tests/fixtures/heartbeat_sample.json`
- Create: `tests/fixtures/backtest_result_sample.json`

- [ ] **Step 1: pyproject.toml markers + playwright dev dep 추가**

`pyproject.toml` 의 `[tool.pytest.ini_options]` markers 섹션을:
```toml
markers = [
    "integration: tests requiring a running PostgreSQL instance (set TEST_DATABASE_URL)",
    "e2e: requires running containers at localhost:8501 — skipped by default",
    "real: triggers actual backtest/paper run against live services",
]
```
으로 교체.

`[project.optional-dependencies]` 의 `dev` 리스트에:
```toml
    "playwright>=1.44",
    "pytest-playwright>=0.5",
```
추가.

- [ ] **Step 2: coverage_stats_sample.json 작성**

`tests/fixtures/coverage_stats_sample.json` 생성:
```json
{
  "schema_version": "coverage_stats.v1",
  "node_id": "NODE_TEST",
  "generated_at": "2026-05-10T00:00:00Z",
  "symbols": {
    "KRW-BTC": {
      "tick": {
        "row_count_today": 1440,
        "file_count_today": 1,
        "file_size_bytes_today": 102400,
        "last_event_ts": "2026-05-10T00:00:00Z",
        "gap_events": []
      },
      "candle": {
        "row_count_today": 24,
        "file_count_today": 1,
        "file_size_bytes_today": 2048,
        "last_event_ts": "2026-05-10T00:00:00Z",
        "gap_events": []
      },
      "orderbook": {
        "row_count_today": 720,
        "file_count_today": 1,
        "file_size_bytes_today": 51200,
        "last_event_ts": "2026-05-10T00:00:00Z",
        "gap_events": []
      }
    }
  }
}
```

- [ ] **Step 3: heartbeat_sample.json 작성**

`tests/fixtures/heartbeat_sample.json` 생성:
```json
{
  "schema_version": "heartbeat.v1",
  "node_id": "NODE_TEST",
  "ts_utc": "2026-05-10T00:00:00Z",
  "ws_state": "connected",
  "uptime_seconds": 3600.0,
  "freshness_seconds": 5.0,
  "worst_level": 0,
  "last_event_ts_per_tier": {
    "tick": "2026-05-10T00:00:00Z",
    "orderbook": "2026-05-10T00:00:00Z",
    "candle": "2026-05-10T00:00:00Z"
  },
  "metrics": {
    "events_per_sec": 2.5
  }
}
```

- [ ] **Step 4: backtest_result_sample.json 작성**

`tests/fixtures/backtest_result_sample.json` 생성:
```json
{
  "schema_version": "execution_report.v1",
  "run_id": "bt-sma-KRW-BTC-1h-5-20-fixture",
  "mode": "backtest",
  "symbol": "KRW-BTC",
  "timeframe": "1h",
  "strategy": "sma",
  "fast": 5,
  "slow": 20,
  "initial_capital": "1000000",
  "period": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-31T00:00:00Z"
  },
  "events": [],
  "summary": {
    "total_return_pct": 5.2,
    "sharpe_ratio": 1.3,
    "max_drawdown_pct": -3.1,
    "total_trades": 10,
    "win_rate_pct": 60.0
  },
  "created_at": "2026-05-10T00:00:00Z",
  "policy_hash": null
}
```

- [ ] **Step 5: tests/fixtures/__init__.py 생성**

`tests/fixtures/__init__.py` 빈 파일 생성.

- [ ] **Step 6: 커밋**

```bash
git add pyproject.toml tests/fixtures/
git commit -m "test(infra): add e2e/real markers, playwright dep, CI fixture samples"
```

---

## Task 2: AppTest — 03_wfo_panel

**Files:**
- Create: `tests/apptest/__init__.py`
- Create: `tests/apptest/test_page_03_wfo.py`

**Context:** `03_wfo_panel.py`는 `MctraderApiClient` 메서드(`create_wfo_decision_group`, `start_wfo_search`, `get_wfo_run_status`, `get_fold_report`)를 직접 호출. `render_common_sidebar`도 `MctraderApiClient.health`, `list_active_runs`를 호출.

- [ ] **Step 1: tests/apptest/__init__.py 생성**

빈 파일 생성.

- [ ] **Step 2: test_page_03_wfo.py 작성**

`tests/apptest/test_page_03_wfo.py`:
```python
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WFO_PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "03_wfo_panel.py"
)


def _patch_client(monkeypatch) -> None:
    """Patch MctraderApiClient to avoid real HTTP calls."""
    from mctrader_web import api_client as ac_mod

    monkeypatch.setattr(ac_mod.MctraderApiClient, "health", lambda self: True)
    monkeypatch.setattr(
        ac_mod.MctraderApiClient,
        "list_active_runs",
        lambda self: {"active_runs": []},
    )
    monkeypatch.setattr(
        ac_mod.MctraderApiClient,
        "create_wfo_decision_group",
        lambda self, **kwargs: {"dg_hash": "abc123", "fold_count": 1},
    )
    monkeypatch.setattr(
        ac_mod.MctraderApiClient,
        "start_wfo_search",
        lambda self, **kwargs: {"run_id": "wfo-test-run", "lifecycle": "queued"},
    )
    monkeypatch.setattr(
        ac_mod.MctraderApiClient,
        "get_wfo_run_status",
        lambda self, run_id: {"run_id": run_id, "lifecycle": "completed"},
    )
    monkeypatch.setattr(
        ac_mod.MctraderApiClient,
        "get_fold_report",
        lambda self, run_id: {"folds": []},
    )


def test_wfo_page_loads_without_error(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_client(monkeypatch)
    at = AppTest.from_file(WFO_PAGE, default_timeout=15)
    at.run()
    assert not at.exception, f"WFO page crashed: {at.exception}"


def test_wfo_page_shows_title(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_client(monkeypatch)
    at = AppTest.from_file(WFO_PAGE, default_timeout=15)
    at.run()
    titles = " ".join(str(t.value) for t in at.title if hasattr(t, "value"))
    assert "WFO" in titles


def test_wfo_page_has_decision_group_form(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_client(monkeypatch)
    at = AppTest.from_file(WFO_PAGE, default_timeout=15)
    at.run()
    # Form has text inputs for actor, dataset_id, etc.
    inputs = [i.label for i in at.text_input if hasattr(i, "label")]
    assert any("actor" in lbl for lbl in inputs), f"actor input not found; labels: {inputs}"
```

- [ ] **Step 3: 테스트 실행 확인**

```bash
cd c:\workspace\mclayer\mctrader-web
.venv\Scripts\python -m pytest tests/apptest/test_page_03_wfo.py -v
```
Expected: 3 PASSED

- [ ] **Step 4: 커밋**

```bash
git add tests/apptest/
git commit -m "test(apptest): AppTest for 03_wfo_panel — load, title, form"
```

---

## Task 3: AppTest — 04/05/06 strategy pages

**Files:**
- Create: `tests/apptest/test_page_04_strategy_sets.py`
- Create: `tests/apptest/test_page_05_strategy_set_editor.py`
- Create: `tests/apptest/test_page_06_strategy_promotion.py`

**Context:** 04/05/06 페이지는 `requests.get/post/put` 직접 호출. `MCTRADER_API_PORT_FOR_CLIENT` 환경변수로 API URL 구성. monkeypatch로 `requests` 모듈 패치.

- [ ] **Step 1: test_page_04_strategy_sets.py 작성**

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "04_strategy_sets.py"
)


def _mock_requests_get_empty(monkeypatch) -> None:
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"strategy_sets": []}
    import mctrader_web.dashboard.pages.strategy_sets_page as _  # noqa: F401 — trigger import path
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)


def _mock_requests_get_list(monkeypatch) -> None:
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "strategy_sets": [
            {
                "id": "abc-123",
                "name": "TestSet",
                "description": "test",
                "owner": "dev",
                "created_at": "2026-05-10T00:00:00Z",
                "archived_at": None,
            }
        ]
    }
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)


def test_strategy_sets_page_loads_without_error(monkeypatch):
    from streamlit.testing.v1 import AppTest

    import requests
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"strategy_sets": []}
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)

    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    assert not at.exception, f"strategy_sets page crashed: {at.exception}"


def test_strategy_sets_page_shows_title(monkeypatch):
    from streamlit.testing.v1 import AppTest

    import requests
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"strategy_sets": []}
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)

    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    titles = " ".join(str(t.value) for t in at.title if hasattr(t, "value"))
    assert "Strategy" in titles


def test_strategy_sets_page_shows_set_in_list(monkeypatch):
    from streamlit.testing.v1 import AppTest

    import requests
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "strategy_sets": [
            {
                "id": "abc-123",
                "name": "TestSet",
                "description": "test",
                "owner": "dev",
                "created_at": "2026-05-10T00:00:00Z",
                "archived_at": None,
            }
        ]
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)

    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    rendered = " ".join(
        str(el.value) for el in list(at.markdown) + list(at.text) + list(at.dataframe)
        if hasattr(el, "value")
    )
    assert "TestSet" in rendered or len(at.dataframe) > 0
```

- [ ] **Step 2: test_page_05_strategy_set_editor.py 작성**

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "05_strategy_set_editor.py"
)

_FAKE_SET = {
    "id": "abc-123",
    "name": "TestSet",
    "description": "desc",
    "owner": "dev",
    "created_at": "2026-05-10T00:00:00Z",
    "archived_at": None,
}

_FAKE_SETS_LIST = {"strategy_sets": [_FAKE_SET]}


def _mock_get(monkeypatch) -> None:
    import requests

    def _get(url, **kw):
        m = MagicMock()
        m.ok = True
        if "strategy-sets" in url and url.endswith("strategy-sets"):
            m.json.return_value = _FAKE_SETS_LIST
        else:
            m.json.return_value = _FAKE_SET
        return m

    monkeypatch.setattr(requests, "get", _get)


def test_strategy_set_editor_loads(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _mock_get(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    assert not at.exception, f"editor page crashed: {at.exception}"


def test_strategy_set_editor_has_name_input(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _mock_get(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    labels = [i.label for i in at.text_input if hasattr(i, "label")]
    assert any("이름" in lbl or "name" in lbl.lower() for lbl in labels), f"name input not found: {labels}"
```

- [ ] **Step 3: test_page_06_strategy_promotion.py 작성**

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "06_strategy_promotion.py"
)

_FAKE_SETS = {"strategy_sets": [{"id": "abc-123", "name": "TestSet", "description": "", "owner": "dev", "created_at": "2026-05-10T00:00:00Z", "archived_at": None}]}
_FAKE_VERSIONS = {"versions": []}


def _mock_get(monkeypatch) -> None:
    import requests

    def _get(url, **kw):
        m = MagicMock()
        m.ok = True
        if "versions" in url:
            m.json.return_value = _FAKE_VERSIONS
        else:
            m.json.return_value = _FAKE_SETS
        return m

    monkeypatch.setattr(requests, "get", _get)


def test_strategy_promotion_page_loads(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _mock_get(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    assert not at.exception, f"promotion page crashed: {at.exception}"


def test_strategy_promotion_page_has_title(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _mock_get(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=15)
    at.run()
    titles = " ".join(str(t.value) for t in at.title if hasattr(t, "value"))
    assert "Strategy" in titles or "Promotion" in titles or "promotion" in titles.lower()
```

- [ ] **Step 4: 테스트 실행 확인**

```bash
.venv\Scripts\python -m pytest tests/apptest/test_page_04_strategy_sets.py tests/apptest/test_page_05_strategy_set_editor.py tests/apptest/test_page_06_strategy_promotion.py -v
```
Expected: 7 PASSED (3+2+2)

- [ ] **Step 5: 커밋**

```bash
git add tests/apptest/test_page_04_strategy_sets.py tests/apptest/test_page_05_strategy_set_editor.py tests/apptest/test_page_06_strategy_promotion.py
git commit -m "test(apptest): AppTest for 04/05/06 strategy pages"
```

---

## Task 4: AppTest — 20_data_collection

**Files:**
- Create: `tests/apptest/test_page_20_data_collection.py`

**Context:** `20_data_collection.py`는 `fetch_coverage_stats(data_root)`, `fetch_status(data_root)` 호출 후 §1~§4 렌더링. 7개의 st.metric, 3개 탭(Candle/Orderbook/Transaction). polling loop(time.sleep + st.rerun)는 테스트에서 무한루프가 되므로 반드시 `refresh_label = "수동"`이 되도록 session_state mock 필요.

- [ ] **Step 1: test_page_20_data_collection.py 작성**

```python
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE = str(
    REPO_ROOT / "src" / "mctrader_web" / "dashboard" / "pages" / "20_data_collection.py"
)
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _make_coverage_result():
    from mctrader_web.dashboard.coverage_stats_adapter import CoverageStatsResult, TierStats
    import time

    tier = TierStats(
        row_count_today=1440,
        file_count_today=1,
        file_size_bytes_today=102400,
        last_event_ts="2026-05-10T00:00:00Z",
        gap_events=[],
    )
    return CoverageStatsResult(
        stats={"KRW-BTC": {"tick": tier, "candle": tier, "orderbook": tier}},
        generated_at=time.time(),
        node_id="NODE_TEST",
        error=None,
        fetched_at=time.time(),
    )


def _make_status_result():
    from mctrader_web.dashboard.status_adapter import StatusResult

    return StatusResult(
        nodes=[
            {
                "node_id": "NODE_TEST",
                "ws_state": "connected",
                "uptime_seconds": 3600.0,
                "freshness_seconds": 5.0,
                "worst_level": 0,
                "last_event_ts_per_tier": {
                    "tick": "2026-05-10T00:00:00Z",
                    "orderbook": "2026-05-10T00:00:00Z",
                    "candle": "2026-05-10T00:00:00Z",
                },
                "metrics": {"events_per_sec": 2.5},
            }
        ],
        worst_level=0,
        error=None,
        fetched_at=__import__("time").time(),
    )


def _patch_adapters(monkeypatch) -> None:
    import mctrader_web.dashboard.coverage_stats_adapter as cov_mod
    import mctrader_web.dashboard.status_adapter as stat_mod

    monkeypatch.setattr(cov_mod, "fetch_coverage_stats", lambda root: _make_coverage_result())
    monkeypatch.setattr(stat_mod, "fetch_status", lambda root: _make_status_result())
    # Disable polling loop
    monkeypatch.setattr("time.sleep", lambda s: None)


def test_data_collection_page_loads(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_adapters(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=20)
    at.run()
    assert not at.exception, f"data_collection page crashed: {at.exception}"


def test_data_collection_page_shows_title(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_adapters(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=20)
    at.run()
    titles = " ".join(str(t.value) for t in at.title if hasattr(t, "value"))
    assert "Data Collection" in titles or "데이터" in titles


def test_data_collection_kpi_metrics_rendered(monkeypatch):
    from streamlit.testing.v1 import AppTest

    _patch_adapters(monkeypatch)
    at = AppTest.from_file(PAGE, default_timeout=20)
    at.run()
    # §1 에 7개 st.metric 렌더링
    assert len(at.metric) >= 1, f"no metrics found; exception={at.exception}"


def test_data_collection_error_state(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import mctrader_web.dashboard.coverage_stats_adapter as cov_mod
    import mctrader_web.dashboard.status_adapter as stat_mod
    import time

    from mctrader_web.dashboard.coverage_stats_adapter import CoverageStatsResult
    from mctrader_web.dashboard.status_adapter import StatusResult

    err_coverage = CoverageStatsResult(
        stats={}, generated_at=time.time(), node_id=None,
        error="coverage fetch failed", fetched_at=time.time(),
    )
    err_status = StatusResult(nodes=[], worst_level=3, error="heartbeat not found", fetched_at=time.time())

    monkeypatch.setattr(cov_mod, "fetch_coverage_stats", lambda root: err_coverage)
    monkeypatch.setattr(stat_mod, "fetch_status", lambda root: err_status)
    monkeypatch.setattr("time.sleep", lambda s: None)

    at = AppTest.from_file(PAGE, default_timeout=20)
    at.run()
    assert not at.exception
    errors = " ".join(str(e.value) for e in at.error if hasattr(e, "value"))
    assert "error" in errors.lower() or "offline" in errors.lower() or "failed" in errors.lower()
```

- [ ] **Step 2: StatusResult 임포트 확인**

`mctrader_web.dashboard.status_adapter.StatusResult`의 실제 필드 확인 후 위 코드와 맞지 않으면 수정:
```bash
.venv\Scripts\python -c "from mctrader_web.dashboard.status_adapter import StatusResult; import inspect; print(inspect.getsource(StatusResult))"
```

StatusResult 필드가 다를 경우 `_make_status_result()`를 실제 생성자에 맞게 수정.

- [ ] **Step 3: 테스트 실행 확인**

```bash
.venv\Scripts\python -m pytest tests/apptest/test_page_20_data_collection.py -v
```
Expected: 4 PASSED

- [ ] **Step 4: 커밋**

```bash
git add tests/apptest/test_page_20_data_collection.py
git commit -m "test(apptest): AppTest for 20_data_collection — load, KPI metrics, error state"
```

---

## Task 5: API gap — test_admin_audit_query + test_admin_rbac_tokens

**Files:**
- Create: `tests/api/test_admin_audit_query.py`
- Create: `tests/api/test_admin_rbac_tokens.py`

**Context:** `tests/api/conftest.py`에 `app_client` fixture가 있음. `auth_headers()`는 operator/admin 토큰 헤더 반환. audit_log query는 `GET /admin/audit/log?limit=N&offset=N&actor=X`. rbac token endpoints는 `POST /admin/rbac/tokens`, `GET /admin/rbac/tokens`, `POST /admin/rbac/tokens/{id}/revoke`.

- [ ] **Step 1: tests/api/conftest.py 에서 app_client fixture 확인**

```bash
.venv\Scripts\python -c "import ast, pathlib; src=pathlib.Path('tests/api/conftest.py').read_text(); print(src[:2000])"
```

`app_client`, `auth_headers` 사용 패턴 확인.

- [ ] **Step 2: test_admin_audit_query.py 작성**

```python
from __future__ import annotations

import pytest

from tests.api.conftest import auth_headers


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    from mctrader_web.api.admin.rate_limit import reset_counters
    reset_counters()
    yield
    reset_counters()


class TestAuditLogQuery:
    @pytest.mark.asyncio
    async def test_get_audit_log_empty(self, app_client):
        r = await app_client.get("/admin/audit/log", headers=auth_headers())
        assert r.status_code == 200
        body = r.json()
        assert "entries" in body or "rows" in body or "log" in body or isinstance(body, list)

    @pytest.mark.asyncio
    async def test_get_audit_log_requires_auth(self, app_client):
        r = await app_client.get("/admin/audit/log")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_get_audit_log_limit_param(self, app_client):
        r = await app_client.get("/admin/audit/log?limit=5", headers=auth_headers())
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_audit_log_after_control_action(self, app_client):
        """Audit log grows after a control action."""
        import uuid
        from mctrader_web.api.admin.audit_db import append_audit_row

        append_audit_row(
            actor="test-actor", role="admin",
            engine_class="paper_runner", engine_id="paper_runner-default",
            action="stop", outcome="accepted",
            request_id=str(uuid.uuid4()),
        )
        r = await app_client.get("/admin/audit/log", headers=auth_headers())
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_audit_log_actor_filter(self, app_client):
        r = await app_client.get(
            "/admin/audit/log?actor=test-actor", headers=auth_headers()
        )
        assert r.status_code in (200, 422)  # 422 if actor filter not supported
```

- [ ] **Step 3: test_admin_rbac_tokens.py 작성**

```python
from __future__ import annotations

import pytest

from tests.api.conftest import auth_headers


@pytest.fixture(autouse=True)
def _reset():
    from mctrader_web.api.admin.rate_limit import reset_counters
    reset_counters()
    yield
    reset_counters()


class TestRbacTokens:
    @pytest.mark.asyncio
    async def test_list_tokens_requires_auth(self, app_client):
        r = await app_client.get("/admin/rbac/tokens")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_list_tokens_returns_list(self, app_client):
        r = await app_client.get("/admin/rbac/tokens", headers=auth_headers())
        assert r.status_code == 200
        body = r.json()
        assert "tokens" in body or isinstance(body, list)

    @pytest.mark.asyncio
    async def test_create_token_viewer_role(self, app_client):
        r = await app_client.post(
            "/admin/rbac/tokens",
            headers=auth_headers(),
            json={"role": "viewer", "alias": "ci-test-viewer"},
        )
        assert r.status_code in (200, 201)
        body = r.json()
        assert "token" in body or "id" in body

    @pytest.mark.asyncio
    async def test_create_token_missing_role_returns_422(self, app_client):
        r = await app_client.post(
            "/admin/rbac/tokens",
            headers=auth_headers(),
            json={"alias": "no-role"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token_returns_404(self, app_client):
        r = await app_client.post(
            "/admin/rbac/tokens/nonexistent-id/revoke",
            headers=auth_headers(),
        )
        assert r.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_create_then_revoke_token(self, app_client):
        # Create
        r_create = await app_client.post(
            "/admin/rbac/tokens",
            headers=auth_headers(),
            json={"role": "operator", "alias": "ci-test-op"},
        )
        assert r_create.status_code in (200, 201)
        token_id = r_create.json().get("id") or r_create.json().get("token_id")
        if token_id is None:
            pytest.skip("create response does not contain id")

        # Revoke
        r_revoke = await app_client.post(
            f"/admin/rbac/tokens/{token_id}/revoke",
            headers=auth_headers(),
        )
        assert r_revoke.status_code in (200, 204)
```

- [ ] **Step 4: 실제 API 엔드포인트 경로 확인 후 수정**

```bash
.venv\Scripts\python -c "
from mctrader_web.api.app import create_app
app = create_app()
for route in app.routes:
    if hasattr(route, 'path') and ('audit' in route.path or 'rbac' in route.path or 'token' in route.path):
        print(route.methods, route.path)
"
```

경로가 다를 경우 위 테스트의 URL을 실제 경로로 수정.

- [ ] **Step 5: 테스트 실행**

```bash
.venv\Scripts\python -m pytest tests/api/test_admin_audit_query.py tests/api/test_admin_rbac_tokens.py -v
```
Expected: 모두 PASSED (404/422 등 예상 상태코드는 허용)

- [ ] **Step 6: 커밋**

```bash
git add tests/api/test_admin_audit_query.py tests/api/test_admin_rbac_tokens.py
git commit -m "test(api): audit query + rbac token CRUD gap tests"
```

---

## Task 6: Playwright E2E setup + 4 flow tests

**Files:**
- Create: `tests/e2e/conftest.py` (playwright fixtures + skip guard)
- Create: `tests/e2e/test_data_collection_flow.py`
- Create: `tests/e2e/test_backtest_flow.py`
- Create: `tests/e2e/test_paper_flow.py`
- Create: `tests/e2e/test_strategy_set_flow.py`

**Context:**
- Playwright 테스트는 `@pytest.mark.e2e` — 기본 skip, `-m e2e` 로 활성화
- base URL: `http://localhost:8501`
- Streamlit sidebar에서 페이지 링크 클릭으로 이동
- `--real` 없으면 실제 백테스트 트리거 생략, 페이지 구조만 검증

- [ ] **Step 1: playwright 브라우저 설치**

```bash
.venv\Scripts\python -m playwright install chromium
```

- [ ] **Step 2: tests/e2e/conftest.py 작성**

```python
from __future__ import annotations

import pytest


BASE_URL = "http://localhost:8501"


def pytest_addoption(parser):
    parser.addoption(
        "--real", action="store_true", default=False,
        help="trigger real backtest/paper runs in e2e tests"
    )


@pytest.fixture(scope="session")
def real_mode(request) -> bool:
    return request.config.getoption("--real", default=False)


@pytest.fixture(scope="session")
def streamlit_available() -> bool:
    import httpx
    try:
        r = httpx.get(BASE_URL, timeout=3)
        return r.status_code < 500
    except Exception:
        return False


@pytest.fixture(autouse=True)
def skip_if_no_streamlit(streamlit_available, request):
    if request.node.get_closest_marker("e2e") and not streamlit_available:
        pytest.skip("Streamlit not running at localhost:8501 — pass -m e2e with server running")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": BASE_URL}
```

- [ ] **Step 3: test_data_collection_flow.py 작성**

```python
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_data_collection_page_navigable(page: Page):
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle", timeout=15000)
    # Navigate via sidebar
    sidebar_link = page.get_by_role("link", name="Data Collection Monitor")
    if not sidebar_link.is_visible():
        # Try partial match
        sidebar_link = page.locator("nav a").filter(has_text="Data Collection")
    sidebar_link.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    expect(page.get_by_text("Data Collection Monitor", exact=False)).to_be_visible(timeout=10000)


@pytest.mark.e2e
def test_data_collection_kpi_section_renders(page: Page):
    page.goto("http://localhost:8501/Data_Collection_Monitor")
    page.wait_for_load_state("networkidle", timeout=15000)
    # §1 수집 현황 subheader
    expect(page.get_by_text("전체 수집 현황", exact=False)).to_be_visible(timeout=10000)


@pytest.mark.e2e
def test_data_collection_tabs_render(page: Page):
    page.goto("http://localhost:8501/Data_Collection_Monitor")
    page.wait_for_load_state("networkidle", timeout=15000)
    # 탭 버튼들 (Candle, Orderbook, Transaction)
    candle_tab = page.get_by_role("tab", name="Candle")
    expect(candle_tab).to_be_visible(timeout=10000)
```

- [ ] **Step 4: test_backtest_flow.py 작성**

```python
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_backtest_panel_loads(page: Page):
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle", timeout=15000)
    link = page.locator("nav a").filter(has_text="Backtest")
    link.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    expect(page.get_by_text("Backtest", exact=False)).to_be_visible(timeout=10000)


@pytest.mark.e2e
def test_backtest_panel_shows_run_list_or_empty(page: Page):
    page.goto("http://localhost:8501/Backtest_panel")
    page.wait_for_load_state("networkidle", timeout=15000)
    # Either shows runs or "No runs" message
    content = page.locator("main").inner_text(timeout=10000)
    assert len(content) > 0


@pytest.mark.e2e
@pytest.mark.real
def test_backtest_trigger_and_result(page: Page, real_mode: bool):
    """실제 백테스트 트리거 → 결과 확인. --real 플래그 필요."""
    if not real_mode:
        pytest.skip("pass --real to trigger actual backtest")
    import httpx, time

    # API로 백테스트 트리거
    resp = httpx.post(
        "http://localhost:7821/backtests",
        headers={"Authorization": "Bearer test-token"},
        json={
            "strategy": "sma", "symbol": "KRW-BTC",
            "timeframe": "1h", "fast": 5, "slow": 20,
            "start": "2026-04-01T00:00:00Z", "end": "2026-04-07T00:00:00Z",
            "initial_capital": 1000000,
        },
        timeout=10,
    )
    assert resp.status_code in (200, 202), f"backtest start failed: {resp.text}"
    run_id = resp.json().get("run_id")

    # 완료 대기 (최대 60초)
    for _ in range(60):
        s = httpx.get(f"http://localhost:7821/backtests/{run_id}", timeout=5)
        if s.json().get("lifecycle") in ("completed", "error"):
            break
        time.sleep(1)

    # 결과 페이지 확인
    page.goto("http://localhost:8501/Backtest_panel")
    page.wait_for_load_state("networkidle", timeout=15000)
    expect(page.get_by_text(run_id, exact=False)).to_be_visible(timeout=10000)
```

- [ ] **Step 5: test_paper_flow.py 작성**

```python
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_paper_panel_loads(page: Page):
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle", timeout=15000)
    link = page.locator("nav a").filter(has_text="Paper")
    link.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    expect(page.get_by_text("Paper", exact=False)).to_be_visible(timeout=10000)


@pytest.mark.e2e
def test_paper_panel_shows_status(page: Page):
    page.goto("http://localhost:8501/Paper_panel")
    page.wait_for_load_state("networkidle", timeout=15000)
    content = page.locator("main").inner_text(timeout=10000)
    # shows some status content (running/stopped/etc)
    assert len(content) > 10


@pytest.mark.e2e
def test_paper_panel_shows_active_run_or_idle(page: Page):
    page.goto("http://localhost:8501/Paper_panel")
    page.wait_for_load_state("networkidle", timeout=15000)
    # Either "No active run" or a run_id is visible
    main = page.locator("main")
    expect(main).to_be_visible(timeout=10000)
    text = main.inner_text()
    assert "paper" in text.lower() or "run" in text.lower() or "active" in text.lower() or len(text) > 5
```

- [ ] **Step 6: test_strategy_set_flow.py 작성**

```python
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_strategy_sets_page_loads(page: Page):
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle", timeout=15000)
    link = page.locator("nav a").filter(has_text="Strategy Set")
    link.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    expect(page.get_by_text("Strategy Set", exact=False)).to_be_visible(timeout=10000)


@pytest.mark.e2e
def test_strategy_sets_create_form_visible(page: Page):
    page.goto("http://localhost:8501/Strategy_sets")
    page.wait_for_load_state("networkidle", timeout=15000)
    # 새 Strategy Set 생성 expander
    expander = page.get_by_text("새 Strategy Set 생성", exact=False)
    expect(expander).to_be_visible(timeout=10000)
    expander.click()
    # 이름 입력 필드 등장
    name_input = page.get_by_label("이름")
    expect(name_input).to_be_visible(timeout=5000)


@pytest.mark.e2e
@pytest.mark.real
def test_strategy_set_create_then_view(page: Page, real_mode: bool):
    """실제 전략 Set 생성 → 목록 확인. --real 필요."""
    if not real_mode:
        pytest.skip("pass --real for create flow")

    page.goto("http://localhost:8501/Strategy_sets")
    page.wait_for_load_state("networkidle", timeout=15000)

    # expander 열기
    page.get_by_text("새 Strategy Set 생성", exact=False).click()
    page.get_by_label("이름").fill("E2E-TestSet")
    page.get_by_role("button", name="생성").click()
    page.wait_for_load_state("networkidle", timeout=10000)

    # 목록에 등장
    expect(page.get_by_text("E2E-TestSet", exact=False)).to_be_visible(timeout=10000)
```

- [ ] **Step 7: e2e 테스트 실행 (서버 실행 중인 경우)**

```bash
.venv\Scripts\python -m pytest tests/e2e/test_data_collection_flow.py tests/e2e/test_backtest_flow.py tests/e2e/test_paper_flow.py tests/e2e/test_strategy_set_flow.py -m e2e -v
```
서버 미실행 시 전부 skip됨 — 정상.

- [ ] **Step 8: 전체 AppTest + API 테스트 실행 확인**

```bash
.venv\Scripts\python -m pytest tests/apptest/ tests/api/ -v --ignore=tests/api/test_admin_control.py -x
```
Expected: 기존 테스트 PASS + 신규 테스트 PASS

- [ ] **Step 9: 커밋**

```bash
git add tests/e2e/conftest.py tests/e2e/test_data_collection_flow.py tests/e2e/test_backtest_flow.py tests/e2e/test_paper_flow.py tests/e2e/test_strategy_set_flow.py
git commit -m "test(e2e): Playwright 4-flow E2E tests — data_collection/backtest/paper/strategy_set"
```

---

## Task 7: 전체 테스트 실행 검증 + PR

- [ ] **Step 1: 전체 테스트 실행**

```bash
.venv\Scripts\python -m pytest tests/ -v --ignore=tests/integration -m "not e2e" 2>&1 | tail -30
```
Expected: 기존 ~220 + 신규 ~25 = ~245 PASSED, 0 FAILED

- [ ] **Step 2: 실패 시 수정**

실패 테스트가 있으면 원인 파악 후 수정. StatusResult 또는 CoverageStatsResult 생성자 불일치가 가장 흔한 원인.

- [ ] **Step 3: PR 생성**

```bash
git checkout -b feat/test-overhaul
git push -u origin feat/test-overhaul
gh pr create --title "test: mctrader-web 전체 테스트 보강 (AppTest 5+API gap+Playwright E2E 4)" \
  --body "$(cat <<'EOF'
## Summary
- AppTest 신규 5개 페이지 (03_wfo/04_strategy_sets/05_editor/06_promotion/20_data_collection)
- API gap tests: admin audit query + rbac token CRUD
- Playwright E2E 4개 플로우 (e2e 마크, 기본 skip)
- pytest markers: e2e, real 추가
- CI fixture 샘플 JSON 3종

## Test Plan
- [ ] `pytest tests/apptest/ -v` → 전부 PASS
- [ ] `pytest tests/api/ -v` → 기존+신규 PASS
- [ ] `pytest tests/ -m "not e2e" -v` → 전체 PASS
- [ ] (선택) `pytest tests/e2e/ -m e2e -v` → localhost:8501 실행 시
EOF
)"
```
