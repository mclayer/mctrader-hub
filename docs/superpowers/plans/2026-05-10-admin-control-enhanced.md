# Admin Control 페이지 강화 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `admin_control` 페이지에 엔진/Signal Worker 상태 표시, 유효 버튼 활성화, 전환 상태 실시간 표현, Prometheus 리소스 메트릭을 추가한다.

**Architecture:** mctrader-web에 Signal Worker Docker 제어 API 2개 + `/metrics` Prometheus exposition 엔드포인트를 추가한다. Streamlit 페이지를 상태 인식형으로 전면 재구성하고, mctrader-hub prometheus.yml에 mctrader-web scrape job을 추가한다.

**Tech Stack:** FastAPI, docker-py>=7, prometheus-client>=0.20, httpx, Streamlit

---

## 파일 맵

| 파일 (mctrader-web repo) | 작업 | 역할 |
|---|---|---|
| `pyproject.toml` | 수정 | docker, prometheus-client 의존성 추가 |
| `src/mctrader_web/api/admin/signal_status.py` | 신규 | GET /admin/status/signal-workers |
| `src/mctrader_web/api/admin/signal_control.py` | 신규 | POST /admin/signal/{worker_id}/{verb} |
| `src/mctrader_web/api/admin/metrics.py` | 신규 | GET /metrics Prometheus exposition |
| `src/mctrader_web/api/admin/__init__.py` | 수정 | signal 라우터 2개 등록 |
| `src/mctrader_web/api/app.py` | 수정 | /metrics 라우터 등록 |
| `src/mctrader_web/dashboard/admin_control_helpers.py` | 신규 | 순수 헬퍼 함수 (Streamlit-free) |
| `src/mctrader_web/dashboard/pages/11_admin_control.py` | 전면 재구성 | 상태+폴링+Signal Worker 제어 |
| `compose.yml` | 수정 | api 서비스에 Docker 소켓 마운트 |
| `tests/api/test_admin_signal_status.py` | 신규 | signal_status 테스트 |
| `tests/api/test_admin_signal_control.py` | 신규 | signal_control 테스트 |
| `tests/api/test_admin_metrics.py` | 신규 | metrics 엔드포인트 테스트 |
| `tests/dashboard/test_admin_control_helpers.py` | 신규 | 헬퍼 단위 테스트 |

| 파일 (mctrader-hub repo) | 작업 | 역할 |
|---|---|---|
| `monitoring/prometheus.yml` | 수정 | mctrader-web scrape job 추가 |

---

### Task 1: 의존성 추가

**Files:**
- Modify: `pyproject.toml` (mctrader-web repo)

- [ ] **Step 1: docker, prometheus-client 추가**

`pyproject.toml`의 `dependencies` 배열에 추가 (기존 항목 뒤에):

```toml
    "docker>=7,<8",
    "prometheus-client>=0.20",
```

- [ ] **Step 2: 설치 확인**

```bash
cd c:/workspace/mclayer/mctrader-web
pip install -e ".[dev]"
python -c "import docker; import prometheus_client; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: 커밋**

```bash
git add pyproject.toml
git commit -m "deps: add docker-py and prometheus-client"
```

---

### Task 2: Signal Worker 상태 API

**Files:**
- Create: `src/mctrader_web/api/admin/signal_status.py`
- Create: `tests/api/test_admin_signal_status.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# tests/api/test_admin_signal_status.py
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest

WORKERS = ["fear-greed", "ecos", "kimchi", "announcement", "coinglass"]
TEST_TOKEN = "test-token-fixed-for-fast-tests-32-bytes!"


def _make_container(name: str, status: str = "running") -> MagicMock:
    c = MagicMock()
    c.status = status
    c.attrs = {"State": {"StartedAt": "2026-01-01T00:00:00Z"}}
    return c


def _mock_docker_all_running():
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = lambda name: _make_container(name, "running")
    return mock_client


def test_get_signal_workers_status_all_running():
    with (
        patch("mctrader_web.api.admin.signal_status.docker") as mock_docker,
        patch("mctrader_web.api.admin.signal_status._query_prometheus", return_value={}),
    ):
        mock_docker.from_env.return_value = _mock_docker_all_running()
        from mctrader_web.api.admin.signal_status import get_signal_workers_status
        result = get_signal_workers_status()
    assert len(result) == 5
    assert all(w.docker_state == "running" for w in result)
    assert {w.worker_id for w in result} == set(WORKERS)


def test_get_signal_workers_status_one_not_found():
    import docker.errors
    mock_client = MagicMock()
    def _get(name):
        if name == "signal-coinglass":
            raise docker.errors.NotFound("not found")
        return _make_container(name, "running")
    mock_client.containers.get.side_effect = _get
    with (
        patch("mctrader_web.api.admin.signal_status.docker") as mock_docker,
        patch("mctrader_web.api.admin.signal_status._query_prometheus", return_value={}),
    ):
        mock_docker.from_env.return_value = mock_client
        from mctrader_web.api.admin.signal_status import get_signal_workers_status
        result = get_signal_workers_status()
    coinglass = next(w for w in result if w.worker_id == "coinglass")
    assert coinglass.docker_state == "not_found"
    assert coinglass.cpu_percent is None
    assert coinglass.mem_mb is None


def test_get_signal_workers_prometheus_metrics():
    prom_cpu = {"signal-fear-greed": 2.5}
    prom_mem = {"signal-fear-greed": 30 * 1024 * 1024}  # 30MB in bytes
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = lambda name: _make_container(name, "running")
    with (
        patch("mctrader_web.api.admin.signal_status.docker") as mock_docker,
        patch("mctrader_web.api.admin.signal_status._query_prometheus") as mock_prom,
    ):
        mock_docker.from_env.return_value = mock_client
        mock_prom.side_effect = lambda q: prom_cpu if "cpu" in q else prom_mem
        from mctrader_web.api.admin.signal_status import get_signal_workers_status
        result = get_signal_workers_status()
    fg = next(w for w in result if w.worker_id == "fear-greed")
    assert fg.cpu_percent == 2.5
    assert fg.mem_mb == 30.0


@pytest.mark.anyio
async def test_signal_workers_endpoint_requires_auth(app_client):
    resp = await app_client.get("/admin/status/signal-workers")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_signal_workers_endpoint_ok(app_client):
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = lambda name: _make_container(name, "running")
    with (
        patch("mctrader_web.api.admin.signal_status.docker") as mock_docker,
        patch("mctrader_web.api.admin.signal_status._query_prometheus", return_value={}),
    ):
        mock_docker.from_env.return_value = mock_client
        resp = await app_client.get(
            "/admin/status/signal-workers",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["workers"]) == 5
    assert "fetched_at" in data
    assert data["workers"][0]["worker_id"] in WORKERS
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

```bash
cd c:/workspace/mclayer/mctrader-web
pytest tests/api/test_admin_signal_status.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'mctrader_web.api.admin.signal_status'`

- [ ] **Step 3: signal_status.py 구현**

```python
# src/mctrader_web/api/admin/signal_status.py
"""Signal Worker container status (GET /admin/status/signal-workers)."""
from __future__ import annotations
import datetime
from typing import Any

import docker
import docker.errors
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

SIGNAL_WORKERS: list[str] = [
    "fear-greed", "ecos", "kimchi", "announcement", "coinglass"
]
_CONTAINER_PREFIX = "signal-"
_PROMETHEUS_BASE = "http://prometheus:9090"


class SignalWorkerStatus(BaseModel):
    worker_id: str
    container_name: str
    docker_state: str
    cpu_percent: float | None = None
    mem_mb: float | None = None
    uptime_seconds: float | None = None


class SignalWorkersStatusResponse(BaseModel):
    workers: list[SignalWorkerStatus]
    fetched_at: str


def _query_prometheus(query: str) -> dict[str, float]:
    """Return {container_name: float_value} from a Prometheus instant query."""
    try:
        resp = httpx.get(
            f"{_PROMETHEUS_BASE}/api/v1/query",
            params={"query": query},
            timeout=5.0,
        )
        out: dict[str, float] = {}
        for item in resp.json().get("data", {}).get("result", []):
            name = item.get("metric", {}).get("name", "")
            out[name] = float(item.get("value", [0, "0"])[1])
        return out
    except Exception:
        return {}


def get_signal_workers_status() -> list[SignalWorkerStatus]:
    """Core logic: Docker SDK + Prometheus. Never raises — returns degraded entries on failure."""
    try:
        client = docker.from_env()
    except Exception:
        return [
            SignalWorkerStatus(
                worker_id=w,
                container_name=f"{_CONTAINER_PREFIX}{w}",
                docker_state="unknown",
            )
            for w in SIGNAL_WORKERS
        ]

    cpu_data = _query_prometheus(
        'rate(container_cpu_usage_seconds_total{name=~"signal-.*"}[1m]) * 100'
    )
    mem_data = _query_prometheus(
        'container_memory_usage_bytes{name=~"signal-.*"}'
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    results: list[SignalWorkerStatus] = []

    for worker_id in SIGNAL_WORKERS:
        container_name = f"{_CONTAINER_PREFIX}{worker_id}"
        try:
            container = client.containers.get(container_name)
            state = container.status
            started_str = container.attrs.get("State", {}).get("StartedAt", "")
            uptime: float | None = None
            if state == "running" and started_str:
                started = datetime.datetime.fromisoformat(
                    started_str.replace("Z", "+00:00")
                )
                uptime = round((now - started).total_seconds(), 1)
        except docker.errors.NotFound:
            state = "not_found"
            uptime = None

        cpu_pct = round(cpu_data.get(container_name, 0.0), 2) if state == "running" else None
        mem_bytes = mem_data.get(container_name)
        mem_mb = round(mem_bytes / 1024 / 1024, 1) if mem_bytes and state == "running" else None

        results.append(SignalWorkerStatus(
            worker_id=worker_id,
            container_name=container_name,
            docker_state=state,
            cpu_percent=cpu_pct,
            mem_mb=mem_mb,
            uptime_seconds=uptime,
        ))
    return results


def get_admin_signal_status_router(*, auth_dep: Any) -> APIRouter:
    router = APIRouter(tags=["admin-signal-status"])

    @router.get("/signal-workers", response_model=SignalWorkersStatusResponse)
    def signal_workers_status(_token: Any = Depends(auth_dep)) -> SignalWorkersStatusResponse:
        return SignalWorkersStatusResponse(
            workers=get_signal_workers_status(),
            fetched_at=datetime.datetime.utcnow().isoformat() + "Z",
        )

    return router
```

- [ ] **Step 4: 테스트 재실행해서 통과 확인**

```bash
pytest tests/api/test_admin_signal_status.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: 커밋**

```bash
git add src/mctrader_web/api/admin/signal_status.py tests/api/test_admin_signal_status.py
git commit -m "feat(admin): signal worker status API (GET /admin/status/signal-workers)"
```

---

### Task 3: Signal Worker 제어 API

**Files:**
- Create: `src/mctrader_web/api/admin/signal_control.py`
- Create: `tests/api/test_admin_signal_control.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# tests/api/test_admin_signal_control.py
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest

TEST_TOKEN = "test-token-fixed-for-fast-tests-32-bytes!"
_HEADERS = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "Idempotency-Key": "00000000-0000-0000-0000-000000000001",
}


def _mock_client(worker_id: str, status: str):
    mock_client = MagicMock()
    container = MagicMock()
    container.status = status
    mock_client.containers.get.return_value = container
    return mock_client, container


@pytest.mark.anyio
async def test_restart_running_worker_ok(app_client):
    mock_client, container = _mock_client("fear-greed", "running")
    with patch("mctrader_web.api.admin.signal_control.docker") as mock_docker:
        mock_docker.from_env.return_value = mock_client
        resp = await app_client.post(
            "/admin/signal/fear-greed/restart", headers=_HEADERS
        )
    assert resp.status_code == 200
    container.restart.assert_called_once_with(timeout=30)
    data = resp.json()
    assert data["worker_id"] == "fear-greed"
    assert data["verb"] == "restart"
    assert data["outcome"] == "accepted"


@pytest.mark.anyio
async def test_start_exited_worker_ok(app_client):
    mock_client, container = _mock_client("ecos", "exited")
    with patch("mctrader_web.api.admin.signal_control.docker") as mock_docker:
        mock_docker.from_env.return_value = mock_client
        resp = await app_client.post(
            "/admin/signal/ecos/start", headers=_HEADERS
        )
    assert resp.status_code == 200
    container.start.assert_called_once()


@pytest.mark.anyio
async def test_start_running_worker_409(app_client):
    mock_client, _ = _mock_client("kimchi", "running")
    with patch("mctrader_web.api.admin.signal_control.docker") as mock_docker:
        mock_docker.from_env.return_value = mock_client
        resp = await app_client.post(
            "/admin/signal/kimchi/start", headers=_HEADERS
        )
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_restart_restarting_worker_409(app_client):
    mock_client, _ = _mock_client("announcement", "restarting")
    with patch("mctrader_web.api.admin.signal_control.docker") as mock_docker:
        mock_docker.from_env.return_value = mock_client
        resp = await app_client.post(
            "/admin/signal/announcement/restart", headers=_HEADERS
        )
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_unknown_worker_422(app_client):
    resp = await app_client.post(
        "/admin/signal/nonexistent/restart", headers=_HEADERS
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_requires_auth(app_client):
    resp = await app_client.post(
        "/admin/signal/fear-greed/restart",
        headers={"Idempotency-Key": "00000000-0000-0000-0000-000000000001"},
    )
    assert resp.status_code in (401, 403)
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

```bash
pytest tests/api/test_admin_signal_control.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'mctrader_web.api.admin.signal_control'`

- [ ] **Step 3: signal_control.py 구현**

```python
# src/mctrader_web/api/admin/signal_control.py
"""Signal Worker Docker control (POST /admin/signal/{worker_id}/{verb})."""
from __future__ import annotations
from typing import Any

import docker
import docker.errors
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from mctrader_web.api.admin.auth_rbac import MultiTokenAuth, require_role

_SIGNAL_WORKERS: frozenset[str] = frozenset(
    ["fear-greed", "ecos", "kimchi", "announcement", "coinglass"]
)
_CONTAINER_PREFIX = "signal-"

# allowed docker_states per verb
_ALLOWED_FROM: dict[str, frozenset[str]] = {
    "start":   frozenset({"stopped", "exited", "paused"}),
    "stop":    frozenset({"running", "paused"}),
    "restart": frozenset({"running", "paused"}),
}


class SignalControlResponse(BaseModel):
    worker_id: str
    container_name: str
    verb: str
    outcome: str


def get_admin_signal_control_router(*, auth_dep: Any) -> APIRouter:
    router = APIRouter(tags=["admin-signal-control"])
    _operator_dep = (
        require_role("operator") if isinstance(auth_dep, MultiTokenAuth) else auth_dep
    )

    @router.post("/signal/{worker_id}/{verb}", response_model=SignalControlResponse)
    def control_signal_worker(
        worker_id: str,
        verb: str,
        idempotency_key: str = Header(..., alias="Idempotency-Key"),
        _token: Any = Depends(_operator_dep),
    ) -> SignalControlResponse:
        if worker_id not in _SIGNAL_WORKERS:
            raise HTTPException(status_code=422, detail=f"Unknown worker: {worker_id!r}")
        if verb not in _ALLOWED_FROM:
            raise HTTPException(status_code=422, detail=f"Unknown verb: {verb!r}")

        container_name = f"{_CONTAINER_PREFIX}{worker_id}"

        try:
            client = docker.from_env()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Docker socket unavailable") from exc

        try:
            container = client.containers.get(container_name)
            current_state = container.status
        except docker.errors.NotFound:
            current_state = "not_found"

        if current_state not in _ALLOWED_FROM[verb]:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot {verb} '{worker_id}' in state '{current_state}'",
            )

        try:
            if verb == "start":
                container.start()
            elif verb == "stop":
                container.stop(timeout=30)
            elif verb == "restart":
                container.restart(timeout=30)
        except docker.errors.APIError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return SignalControlResponse(
            worker_id=worker_id,
            container_name=container_name,
            verb=verb,
            outcome="accepted",
        )

    return router
```

- [ ] **Step 4: 테스트 재실행해서 통과 확인**

```bash
pytest tests/api/test_admin_signal_control.py -v
```

Expected: 6 tests PASS

- [ ] **Step 5: 커밋**

```bash
git add src/mctrader_web/api/admin/signal_control.py tests/api/test_admin_signal_control.py
git commit -m "feat(admin): signal worker control API (POST /admin/signal/{worker}/{verb})"
```

---

### Task 4: Prometheus metrics 엔드포인트

**Files:**
- Create: `src/mctrader_web/api/admin/metrics.py`
- Create: `tests/api/test_admin_metrics.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# tests/api/test_admin_metrics.py
from __future__ import annotations
from unittest.mock import patch
import pytest


def _engine_payload():
    return {
        "engines": [
            {"engine_id": "collector-default", "engine_class": "collector",
             "sm_state": "running", "heartbeat_age_seconds": 3.0,
             "restart_count": 0, "uptime_seconds": 100.0, "last_error": None},
            {"engine_id": "paper_runner-default", "engine_class": "paper_runner",
             "sm_state": "stopped", "heartbeat_age_seconds": None,
             "restart_count": 0, "uptime_seconds": None, "last_error": None},
        ]
    }


def _signal_payload():
    return {
        "workers": [
            {"worker_id": "fear-greed", "container_name": "signal-fear-greed",
             "docker_state": "running", "cpu_percent": 0.5, "mem_mb": 30.0, "uptime_seconds": 200.0},
            {"worker_id": "coinglass", "container_name": "signal-coinglass",
             "docker_state": "exited", "cpu_percent": None, "mem_mb": None, "uptime_seconds": None},
        ]
    }


@pytest.mark.anyio
async def test_metrics_returns_prometheus_format(app_client, tmp_path, monkeypatch):
    token_file = tmp_path / "local_token"
    token_file.write_text("test-token-fixed-for-fast-tests-32-bytes!")
    monkeypatch.setenv("MCTRADER_TOKEN_PATH", str(token_file))

    import httpx
    from unittest.mock import MagicMock

    def _fake_get(url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        if "signal-workers" in url:
            mock_resp.json.return_value = _signal_payload()
        else:
            mock_resp.json.return_value = _engine_payload()
        return mock_resp

    with patch("mctrader_web.api.admin.metrics.httpx.get", side_effect=_fake_get):
        resp = await app_client.get("/metrics")

    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "mctrader_engine_state" in body
    assert "mctrader_signal_worker_up" in body
    assert "mctrader_collector_heartbeat_age_seconds" in body


@pytest.mark.anyio
async def test_metrics_engine_state_value(app_client, tmp_path, monkeypatch):
    token_file = tmp_path / "local_token"
    token_file.write_text("test-token-fixed-for-fast-tests-32-bytes!")
    monkeypatch.setenv("MCTRADER_TOKEN_PATH", str(token_file))

    from unittest.mock import MagicMock

    def _fake_get(url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        if "signal-workers" in url:
            mock_resp.json.return_value = {"workers": []}
        else:
            mock_resp.json.return_value = {
                "engines": [{"engine_id": "collector-default", "engine_class": "collector",
                              "sm_state": "running", "heartbeat_age_seconds": 5.0,
                              "restart_count": 0, "uptime_seconds": 50.0, "last_error": None}]
            }
        return mock_resp

    with patch("mctrader_web.api.admin.metrics.httpx.get", side_effect=_fake_get):
        resp = await app_client.get("/metrics")

    # running = 2
    assert 'mctrader_engine_state{engine_class="collector",engine_id="collector-default"} 2.0' in resp.text
    assert "mctrader_collector_heartbeat_age_seconds" in resp.text
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

```bash
pytest tests/api/test_admin_metrics.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'mctrader_web.api.admin.metrics'`

- [ ] **Step 3: metrics.py 구현**

```python
# src/mctrader_web/api/admin/metrics.py
"""Prometheus /metrics endpoint.

Calls /admin/status/engines and /admin/status/signal-workers via localhost
to collect current state, then exposes as Prometheus Gauges.
Scrape interval: 15s (see monitoring/prometheus.yml job mctrader-web).
"""
from __future__ import annotations
from pathlib import Path

import httpx
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

from mctrader_web.api.config import DEFAULT_PORT, default_token_path

_BASE_URL = f"http://127.0.0.1:{DEFAULT_PORT}"

_ENGINE_STATE_MAP: dict[str, int] = {
    "stopped": 0, "starting": 1, "running": 2, "stopping": 3,
    "degraded": 4, "crashed": 5, "queued": 6, "cancelling": 7,
    "completed": 2, "failed": 5, "cancelled": 0,
}

# Isolated registry — avoids duplicate registration errors on app reload
_REGISTRY = CollectorRegistry()

_engine_state_g = Gauge(
    "mctrader_engine_state",
    "Engine SM state: 0=stopped 1=starting 2=running 3=stopping 4=degraded 5=crashed 6=queued 7=cancelling",
    ["engine_class", "engine_id"],
    registry=_REGISTRY,
)
_signal_up_g = Gauge(
    "mctrader_signal_worker_up",
    "Signal worker container up (1=running 0=other)",
    ["worker"],
    registry=_REGISTRY,
)
_heartbeat_age_g = Gauge(
    "mctrader_collector_heartbeat_age_seconds",
    "Collector heartbeat age in seconds",
    ["engine_id"],
    registry=_REGISTRY,
)


def _collect(token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = httpx.get(f"{_BASE_URL}/admin/status/engines", headers=headers, timeout=5.0)
        r.raise_for_status()
        for eng in r.json().get("engines", []):
            numeric = _ENGINE_STATE_MAP.get(eng["sm_state"], 0)
            _engine_state_g.labels(
                engine_class=eng["engine_class"],
                engine_id=eng["engine_id"],
            ).set(numeric)
            if eng["engine_class"] == "collector" and eng.get("heartbeat_age_seconds") is not None:
                _heartbeat_age_g.labels(engine_id=eng["engine_id"]).set(
                    eng["heartbeat_age_seconds"]
                )
    except Exception:
        pass

    try:
        r = httpx.get(f"{_BASE_URL}/admin/status/signal-workers", headers=headers, timeout=5.0)
        r.raise_for_status()
        for w in r.json().get("workers", []):
            up = 1 if w["docker_state"] == "running" else 0
            _signal_up_g.labels(worker=w["worker_id"]).set(up)
    except Exception:
        pass


def get_metrics_router() -> APIRouter:
    router = APIRouter(tags=["metrics"])
    _token_path: Path = default_token_path()

    @router.get("/metrics")
    def metrics() -> Response:
        token = _token_path.read_text(encoding="utf-8").strip() if _token_path.exists() else ""
        _collect(token)
        return Response(
            content=generate_latest(_REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )

    return router
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/api/test_admin_metrics.py -v
```

Expected: 2 tests PASS

- [ ] **Step 5: 커밋**

```bash
git add src/mctrader_web/api/admin/metrics.py tests/api/test_admin_metrics.py
git commit -m "feat(admin): prometheus /metrics endpoint (engine state + signal worker gauges)"
```

---

### Task 5: 라우터 등록

**Files:**
- Modify: `src/mctrader_web/api/admin/__init__.py`
- Modify: `src/mctrader_web/api/app.py`

- [ ] **Step 1: admin/__init__.py에 signal 라우터 추가**

`src/mctrader_web/api/admin/__init__.py`에서 기존 import 블록 뒤에 추가:

```python
from mctrader_web.api.admin.signal_control import get_admin_signal_control_router
from mctrader_web.api.admin.signal_status import get_admin_signal_status_router
```

`get_admin_router()` 함수 내부 `rbac_router` 등록 바로 뒤에 추가:

```python
    # MCT-125: Signal Worker 상태 조회 (GET /admin/status/signal-workers)
    signal_status_router = get_admin_signal_status_router(auth_dep=auth_dep)
    admin_router.include_router(
        signal_status_router,
        prefix="/status",
        tags=["admin-signal-status"],
    )

    # MCT-125: Signal Worker 제어 (POST /admin/signal/{worker_id}/{verb})
    signal_control_router = get_admin_signal_control_router(auth_dep=auth_dep)
    admin_router.include_router(
        signal_control_router,
        tags=["admin-signal-control"],
    )
```

- [ ] **Step 2: app.py에 /metrics 라우터 추가**

`src/mctrader_web/api/app.py`에서 기존 import 블록 뒤에 추가:

```python
from mctrader_web.api.admin.metrics import get_metrics_router
```

`create_app()` 함수 내부 `app.include_router(strategy_sets_router)` 바로 뒤에 추가:

```python
    # MCT-125: Prometheus /metrics exposition (no auth — Prometheus scraper)
    app.include_router(get_metrics_router())
```

- [ ] **Step 3: 라우터 등록 확인**

```bash
cd c:/workspace/mclayer/mctrader-web
python -c "
from mctrader_web.api.app import create_app
app = create_app(token='test', use_multi_token_auth=False)
paths = [r.path for r in app.routes]
print([p for p in paths if 'signal' in p or 'metrics' in p])
"
```

Expected (순서 무관):
```
['/admin/status/signal-workers', '/admin/signal/{worker_id}/{verb}', '/metrics']
```

- [ ] **Step 4: 전체 테스트 suite 통과 확인**

```bash
pytest tests/api/ -v --tb=short 2>&1 | tail -20
```

Expected: 기존 테스트 포함 모두 PASS (새 3개 파일 테스트 포함)

- [ ] **Step 5: 커밋**

```bash
git add src/mctrader_web/api/admin/__init__.py src/mctrader_web/api/app.py
git commit -m "feat(admin): register signal worker and metrics routers (MCT-125)"
```

---

### Task 6: 인프라 변경

**Files:**
- Modify: `compose.yml` (mctrader-web repo)
- Modify: `monitoring/prometheus.yml` (mctrader-hub repo)

- [ ] **Step 1: mctrader-web compose.yml에 Docker 소켓 마운트 추가**

`c:/workspace/mclayer/mctrader-web/compose.yml`의 `api` 서비스 `volumes` 블록에 추가:

```yaml
      - /var/run/docker.sock:/var/run/docker.sock  # MCT-125: Signal Worker Docker 제어
```

전체 api volumes 블록 최종 형태:
```yaml
    volumes:
      - mctrader_web_data:/var/lib/mctrader/web
      - mctrader-data_mctrader_data:/var/lib/mctrader/data:ro
      - /var/run/docker.sock:/var/run/docker.sock
```

- [ ] **Step 2: mctrader-web compose.yml 커밋**

```bash
cd c:/workspace/mclayer/mctrader-web
git add compose.yml
git commit -m "infra: mount Docker socket into api container for signal worker control (MCT-125)"
```

- [ ] **Step 3: mctrader-hub prometheus.yml에 mctrader-web scrape job 추가**

`c:/workspace/mclayer/mctrader-hub/monitoring/prometheus.yml`의 `scrape_configs` 배열 끝에 추가:

```yaml
  - job_name: mctrader-web
    static_configs:
      - targets: ['mctrader-web-api:7821']
    metrics_path: /metrics
    scrape_interval: 15s
```

- [ ] **Step 4: mctrader-hub prometheus.yml 커밋**

```bash
cd c:/workspace/mclayer/mctrader-hub
git add monitoring/prometheus.yml
git commit -m "infra: add mctrader-web prometheus scrape job (MCT-125)"
```

---

### Task 7: admin_control_helpers.py + 단위 테스트

**Files:**
- Create: `src/mctrader_web/dashboard/admin_control_helpers.py`
- Create: `tests/dashboard/test_admin_control_helpers.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# tests/dashboard/test_admin_control_helpers.py
import pytest
from mctrader_web.dashboard.admin_control_helpers import (
    _allowed_engine_verbs,
    _allowed_signal_verbs,
    _any_transitioning,
    _format_uptime,
    _state_badge,
)


# _allowed_engine_verbs
def test_daemon_running_allows_stop_restart():
    assert _allowed_engine_verbs("daemon", "running") == {"stop", "restart"}

def test_daemon_stopped_allows_start():
    assert _allowed_engine_verbs("daemon", "stopped") == {"start"}

def test_daemon_crashed_allows_start():
    assert _allowed_engine_verbs("daemon", "crashed") == {"start"}

def test_daemon_starting_allows_nothing():
    assert _allowed_engine_verbs("daemon", "starting") == set()

def test_daemon_stopping_allows_nothing():
    assert _allowed_engine_verbs("daemon", "stopping") == set()

def test_daemon_degraded_allows_stop_restart():
    assert _allowed_engine_verbs("daemon", "degraded") == {"stop", "restart"}

def test_oneshot_stopped_allows_trigger():
    assert _allowed_engine_verbs("oneshot", "stopped") == {"trigger"}

def test_oneshot_running_allows_cancel():
    assert _allowed_engine_verbs("oneshot", "running") == {"cancel"}

def test_oneshot_queued_allows_cancel():
    assert _allowed_engine_verbs("oneshot", "queued") == {"cancel"}

def test_oneshot_cancelling_allows_nothing():
    assert _allowed_engine_verbs("oneshot", "cancelling") == set()

def test_library_allows_nothing():
    assert _allowed_engine_verbs("library", "running") == set()


# _allowed_signal_verbs
def test_signal_running_allows_stop_restart():
    assert _allowed_signal_verbs("running") == {"stop", "restart"}

def test_signal_exited_allows_start():
    assert _allowed_signal_verbs("exited") == {"start"}

def test_signal_restarting_allows_nothing():
    assert _allowed_signal_verbs("restarting") == set()

def test_signal_not_found_allows_nothing():
    assert _allowed_signal_verbs("not_found") == set()


# _any_transitioning
def test_any_transitioning_engine_starting():
    engines = [{"sm_state": "starting"}]
    signals: list = []
    assert _any_transitioning(engines, signals) is True

def test_any_transitioning_signal_restarting():
    engines = [{"sm_state": "running"}]
    signals = [{"docker_state": "restarting"}]
    assert _any_transitioning(engines, signals) is True

def test_no_transitioning_all_stable():
    engines = [{"sm_state": "running"}, {"sm_state": "stopped"}]
    signals = [{"docker_state": "running"}, {"docker_state": "exited"}]
    assert _any_transitioning(engines, signals) is False


# _format_uptime
def test_format_uptime_seconds():
    assert _format_uptime(45) == "45s"

def test_format_uptime_minutes():
    assert _format_uptime(125) == "2m 5s"

def test_format_uptime_hours():
    assert _format_uptime(3661) == "1h 1m"


# _state_badge
def test_state_badge_running_contains_colour():
    html, colour = _state_badge("running")
    assert "#28a745" in html
    assert colour == "#28a745"

def test_state_badge_transitioning_contains_spinner():
    html, _ = _state_badge("starting")
    assert "⟳" in html

def test_state_badge_docker_running():
    html, colour = _state_badge("running", is_docker=True)
    assert "#28a745" in colour
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

```bash
pytest tests/dashboard/test_admin_control_helpers.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: admin_control_helpers.py 구현**

```python
# src/mctrader_web/dashboard/admin_control_helpers.py
"""Pure helper functions for 11_admin_control.py. No Streamlit imports."""
from __future__ import annotations

_STATE_COLOUR: dict[str, str] = {
    "running":    "#28a745",
    "degraded":   "#fd7e14",
    "crashed":    "#dc3545",
    "stopped":    "#6c757d",
    "starting":   "#17a2b8",
    "stopping":   "#17a2b8",
    "queued":     "#007bff",
    "cancelling": "#fd7e14",
    "completed":  "#28a745",
    "failed":     "#dc3545",
    "cancelled":  "#6c757d",
    "exited":     "#dc3545",
    "restarting": "#17a2b8",
    "paused":     "#fd7e14",
    "not_found":  "#dc3545",
    "unknown":    "#888888",
}

_TRANSITIONING_SM = frozenset({"starting", "stopping", "cancelling"})
_TRANSITIONING_DOCKER = frozenset({"restarting"})

_DAEMON_ALLOWED: dict[str, set[str]] = {
    "stopped":   {"start"},
    "crashed":   {"start"},
    "failed":    {"start"},
    "cancelled": {"start"},
    "running":   {"stop", "restart"},
    "degraded":  {"stop", "restart"},
    "completed": {"stop", "restart"},
}

_ONESHOT_ALLOWED: dict[str, set[str]] = {
    "stopped":   {"trigger"},
    "failed":    {"trigger"},
    "cancelled": {"trigger"},
    "completed": {"trigger"},
    "queued":    {"cancel"},
    "running":   {"cancel"},
}

_SIGNAL_ALLOWED: dict[str, set[str]] = {
    "running":  {"stop", "restart"},
    "stopped":  {"start"},
    "exited":   {"start"},
    "paused":   {"start", "stop", "restart"},
}


def _allowed_engine_verbs(engine_type: str, sm_state: str) -> set[str]:
    if engine_type == "daemon":
        return _DAEMON_ALLOWED.get(sm_state, set())
    if engine_type == "oneshot":
        return _ONESHOT_ALLOWED.get(sm_state, set())
    return set()


def _allowed_signal_verbs(docker_state: str) -> set[str]:
    return _SIGNAL_ALLOWED.get(docker_state, set())


def _any_transitioning(
    engine_statuses: list[dict],
    signal_statuses: list[dict],
) -> bool:
    return any(e.get("sm_state") in _TRANSITIONING_SM for e in engine_statuses) or any(
        s.get("docker_state") in _TRANSITIONING_DOCKER for s in signal_statuses
    )


def _state_badge(state: str, *, is_docker: bool = False) -> tuple[str, str]:
    """Return (badge_html, colour_hex) for a given SM or Docker state."""
    colour = _STATE_COLOUR.get(state, "#888888")
    if state in _TRANSITIONING_SM or state in _TRANSITIONING_DOCKER:
        label = f"⟳ {state.upper()}..."
    else:
        label = f"● {state.upper()}"
    html = (
        f'<span style="background:{colour};color:#fff;padding:2px 8px;'
        f'border-radius:10px;font-size:12px">{label}</span>'
    )
    return html, colour


def _format_uptime(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    h, rem = divmod(s, 3600)
    return f"{h}h {rem // 60}m"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/dashboard/test_admin_control_helpers.py -v
```

Expected: 26 tests PASS

- [ ] **Step 5: 커밋**

```bash
git add src/mctrader_web/dashboard/admin_control_helpers.py tests/dashboard/test_admin_control_helpers.py
git commit -m "feat(dashboard): admin_control_helpers — verb gating + state badge + uptime format"
```

---

### Task 8: Admin Control 페이지 전면 재구성

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/11_admin_control.py`

- [ ] **Step 1: 파일 전면 교체**

`src/mctrader_web/dashboard/pages/11_admin_control.py` 전체를 아래 내용으로 교체:

```python
# src/mctrader_web/dashboard/pages/11_admin_control.py
"""Admin — Control (MCT-125).

Unified control dashboard: engine process status + Signal Worker container grid.
Shows current state, gates buttons by SM/Docker state, auto-polls during transitions.
"""
from __future__ import annotations

import time
import uuid

import httpx
import streamlit as st

from mctrader_web.api.config import DEFAULT_HOST, DEFAULT_PORT, default_token_path
from mctrader_web.dashboard.admin_control_helpers import (
    _allowed_engine_verbs,
    _allowed_signal_verbs,
    _any_transitioning,
    _format_uptime,
    _state_badge,
)

st.set_page_config(page_title="Admin — Control", layout="wide")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_token_path = default_token_path()
_token: str | None = None
if _token_path.exists():
    _token = _token_path.read_text(encoding="utf-8").strip()

_BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

with st.sidebar:
    st.divider()
    st.caption("Admin section — MCT-125")
    if _token is None:
        st.error("No token found. Run the server once to generate ~/.mctrader/local_token.")
    else:
        st.success("Token loaded.")

st.title("Admin — Control")

if _token is None:
    st.error("Cannot send control commands: no auth token available.")
    st.stop()

# ---------------------------------------------------------------------------
# Engine definitions
# ---------------------------------------------------------------------------
_ENGINE_DEFS = [
    {"label": "Collector",     "engine_class": "collector",    "engine_id": "collector-default",          "type": "daemon"},
    {"label": "Paper Runner",  "engine_class": "paper_runner", "engine_id": "paper_runner-default",       "type": "daemon"},
    {"label": "Backtest",      "engine_class": "backtest",     "engine_id": "backtest-idle",              "type": "oneshot"},
    {"label": "WFO",           "engine_class": "wfo",          "engine_id": "wfo-idle",                   "type": "oneshot"},
    {"label": "Market GW",     "engine_class": "market_gw",    "engine_id": "market_gw-bithumb-paper",    "type": "library"},
]
_SIGNAL_WORKERS = ["fear-greed", "ecos", "kimchi", "announcement", "coinglass"]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _hdrs() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token}"} if _token else {}


def _fetch_engines() -> list[dict]:
    try:
        r = httpx.get(f"{_BASE_URL}/admin/status/engines", headers=_hdrs(), timeout=5.0)
        r.raise_for_status()
        return r.json().get("engines", [])
    except Exception:
        return []


def _fetch_signals() -> list[dict]:
    try:
        r = httpx.get(f"{_BASE_URL}/admin/status/signal-workers", headers=_hdrs(), timeout=5.0)
        r.raise_for_status()
        return r.json().get("workers", [])
    except Exception:
        return []


def _send_engine(engine_class: str, engine_id: str, verb: str) -> dict:
    ik = str(uuid.uuid4())
    prefix = f"{engine_class}-"
    suffix = engine_id[len(prefix):] if engine_id.startswith(prefix) else engine_id
    url = f"{_BASE_URL}/admin/control/{engine_class}/{suffix}/{verb}"
    try:
        resp = httpx.post(url, headers={**_hdrs(), "Idempotency-Key": ik}, timeout=35.0)
        ct = resp.headers.get("content-type", "")
        body = resp.json() if "json" in ct else resp.text
        return {"status_code": resp.status_code, "body": body, "ik": ik}
    except httpx.HTTPError as exc:
        return {"status_code": 0, "body": str(exc), "ik": ik}


def _send_signal(worker_id: str, verb: str) -> dict:
    ik = str(uuid.uuid4())
    url = f"{_BASE_URL}/admin/signal/{worker_id}/{verb}"
    try:
        resp = httpx.post(url, headers={**_hdrs(), "Idempotency-Key": ik}, timeout=35.0)
        ct = resp.headers.get("content-type", "")
        body = resp.json() if "json" in ct else resp.text
        return {"status_code": resp.status_code, "body": body, "ik": ik}
    except httpx.HTTPError as exc:
        return {"status_code": 0, "body": str(exc), "ik": ik}


def _show_result(r: dict) -> None:
    sc = r.get("status_code", 0)
    label = r.get("label", "?")
    verb = r.get("verb", "?")
    if sc == 200:
        st.success(f"{label} / {verb.upper()} — OK (200)")
    elif sc == 409:
        st.warning(f"{label} / {verb.upper()} — SM 충돌 (409): {r['body']}")
    elif sc == 401:
        st.error("Unauthorized (401) — 토큰을 확인하세요.")
    elif sc == 0:
        st.error(f"네트워크 오류: {r['body']}")
    else:
        st.error(f"{label} / {verb.upper()} — 오류 ({sc}): {r['body']}")
    st.caption(f"Idempotency-Key: {r.get('ik', 'n/a')}")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

# ---------------------------------------------------------------------------
# Fetch statuses
# ---------------------------------------------------------------------------
engine_statuses = _fetch_engines()
signal_statuses = _fetch_signals()

engine_by_id = {e["engine_id"]: e for e in engine_statuses}
signal_by_id = {s["worker_id"]: s for s in signal_statuses}

# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------
running_eng = sum(1 for e in engine_statuses if e.get("sm_state") == "running")
running_sig = sum(1 for s in signal_statuses if s.get("docker_state") == "running")

c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    st.markdown(
        f"**엔진** {running_eng}/5 running &nbsp;·&nbsp; **Signal** {running_sig}/{len(signal_statuses)} up",
        unsafe_allow_html=True,
    )
any_trans = _any_transitioning(engine_statuses, signal_statuses)
with c3:
    if any_trans:
        st.markdown("🔄 **전환 중 — 2s 자동 갱신**")
    else:
        st.caption("10s 자동 갱신")

st.divider()

# ---------------------------------------------------------------------------
# Engine section
# ---------------------------------------------------------------------------
st.markdown("#### 엔진 프로세스")

for eng in _ENGINE_DEFS:
    ecls = eng["engine_class"]
    eid  = eng["engine_id"]
    etype = eng["type"]
    info = engine_by_id.get(eid, {})
    sm_state = info.get("sm_state", "unknown")
    badge_html, _ = _state_badge(sm_state)

    with st.container(border=True):
        left, right = st.columns([4, 2])
        with left:
            st.markdown(f"**{eng['label']}** &nbsp; {badge_html}", unsafe_allow_html=True)
            meta: list[str] = []
            hb = info.get("heartbeat_age_seconds")
            rc = info.get("restart_count", 0)
            up = info.get("uptime_seconds")
            if hb is not None:
                meta.append(f"heartbeat {hb:.0f}s 전")
            if rc:
                meta.append(f"재시작 {rc}회")
            if up is not None:
                meta.append(f"업타임 {_format_uptime(up)}")
            if meta:
                st.caption(" · ".join(meta))
        with right:
            st.caption(f"state: `{sm_state}`")

        if etype == "library":
            st.info("library-only — 제어 불가. Status 페이지에서 확인하세요.")
            continue

        verbs = ["start", "stop", "restart"] if etype == "daemon" else ["trigger", "cancel"]
        allowed = _allowed_engine_verbs(etype, sm_state)
        btn_cols = st.columns(len(verbs))
        for i, verb in enumerate(verbs):
            with btn_cols[i]:
                if st.button(
                    verb.upper(),
                    key=f"btn_{ecls}_{verb}",
                    disabled=(verb not in allowed),
                    use_container_width=True,
                ):
                    with st.spinner(f"{eng['label']} {verb}..."):
                        result = _send_engine(ecls, eid, verb)
                        st.session_state["last_result"] = {
                            "label": eng["label"], "verb": verb, **result
                        }
                    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Signal Worker section
# ---------------------------------------------------------------------------
st.markdown("#### Signal Worker 컨테이너")

hdr_l, hdr_r = st.columns([3, 3])
with hdr_r:
    sw_all_cols = st.columns(3)
    with sw_all_cols[0]:
        if st.button("전체 START", key="sw_all_start", use_container_width=True):
            for wid in _SIGNAL_WORKERS:
                _send_signal(wid, "start")
            st.rerun()
    with sw_all_cols[1]:
        if st.button("전체 STOP", key="sw_all_stop", use_container_width=True):
            for wid in _SIGNAL_WORKERS:
                _send_signal(wid, "stop")
            st.rerun()
    with sw_all_cols[2]:
        if st.button("전체 RESTART", key="sw_all_restart", use_container_width=True):
            for wid in _SIGNAL_WORKERS:
                _send_signal(wid, "restart")
            st.rerun()

# 2-column grid
rows = [_SIGNAL_WORKERS[i:i + 2] for i in range(0, len(_SIGNAL_WORKERS), 2)]
for row in rows:
    grid_cols = st.columns(2)
    for col_idx, wid in enumerate(row):
        with grid_cols[col_idx]:
            s_info = signal_by_id.get(wid, {})
            docker_state = s_info.get("docker_state", "unknown")
            badge_html, _ = _state_badge(docker_state, is_docker=True)

            with st.container(border=True):
                top_l, top_r = st.columns([2, 1])
                with top_l:
                    st.markdown(f"**{wid}** &nbsp; {badge_html}", unsafe_allow_html=True)
                with top_r:
                    cpu = s_info.get("cpu_percent")
                    mem = s_info.get("mem_mb")
                    if cpu is not None and mem is not None:
                        st.caption(f"CPU {cpu}% · {mem:.0f}MB")

                allowed_sw = _allowed_signal_verbs(docker_state)
                sw_btns = st.columns(3)
                for j, verb in enumerate(["start", "stop", "restart"]):
                    with sw_btns[j]:
                        if st.button(
                            verb.upper(),
                            key=f"sw_{wid}_{verb}",
                            disabled=(verb not in allowed_sw),
                            use_container_width=True,
                        ):
                            with st.spinner(f"{wid} {verb}..."):
                                result = _send_signal(wid, verb)
                                st.session_state["last_result"] = {
                                    "label": wid, "verb": verb, **result
                                }
                            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Last action result
# ---------------------------------------------------------------------------
if st.session_state["last_result"] is not None:
    st.subheader("마지막 액션 결과")
    _show_result(st.session_state["last_result"])
    with st.expander("Raw response"):
        st.json(st.session_state["last_result"].get("body", {}))

# ---------------------------------------------------------------------------
# Auto-poll (blocking sleep → rerun)
# ---------------------------------------------------------------------------
time.sleep(2 if any_trans else 10)
st.rerun()
```

- [ ] **Step 2: 전체 테스트 suite 통과 확인**

```bash
cd c:/workspace/mclayer/mctrader-web
pytest tests/ -v --ignore=tests/e2e --ignore=tests/integration --ignore=tests/apptest --tb=short 2>&1 | tail -30
```

Expected: 모든 테스트 PASS (기존 테스트 회귀 없음)

- [ ] **Step 3: 커밋**

```bash
git add src/mctrader_web/dashboard/pages/11_admin_control.py
git commit -m "feat(dashboard): admin_control page — inline status + valid-verb gating + signal worker grid + auto-poll (MCT-125)"
```

---

## 완료 후 검증

1. `docker compose up` (mctrader-hub) → mctrader-web 컨테이너 재빌드 후 기동
2. http://mctrader.mclayer.it/admin_control 접속
3. 각 엔진 상태 badge 확인 (running/stopped 표시)
4. running 엔진의 START 버튼이 비활성 상태인지 확인
5. Signal Worker 중 하나를 STOP → DOWN 배지로 전환 확인
6. `curl http://mctrader-web-api:7821/metrics` (Prometheus 컨테이너 내부) → Gauge 출력 확인
7. Prometheus UI (`/graph`) → `mctrader_engine_state` 쿼리 → 데이터 포인트 확인
