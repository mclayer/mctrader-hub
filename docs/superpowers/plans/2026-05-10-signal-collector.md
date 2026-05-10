# mctrader-signal-collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 외부 시그널 6종(Fear&Greed / ECOS FX / 김치프리미엄 / Upbit·Bithumb 공지 / CoinGlass 파생)을 수집해 Redis Stream에 publish하는 독립 서비스 `mctrader-signal-collector`를 신규 리포로 구축한다.

**Architecture:** 각 시그널 소스는 독립 Python 프로세스(Docker 컨테이너)로 실행하며 `BaseWorker` 추상 클래스를 구현한다. `Publisher`가 Redis Stream(`signals:{kind}`)에 XADD하고 `HealthExporter`가 Prometheus `/metrics`를 노출한다. stale 데이터 시 `stale=true` neutral 메시지를 publish해 engine이 fallback 처리한다.

**Tech Stack:** Python 3.12, httpx (sync), redis[hiredis]>=5, prometheus-client>=0.20, beautifulsoup4>=4.12, fakeredis>=2.23 (test), uv, hatchling, pytest>=8, ruff

**Spec:** `mctrader-hub/docs/superpowers/specs/2026-05-10-signal-collector-design.md`

---

## File Map

```
c:\workspace\mclayer\mctrader-signal-collector\   ← 신규 리포
├── src/
│   └── signal_collector/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── publisher.py      # Redis Stream XADD + stale fallback
│       │   ├── dedup.py          # Redis Set 기반 announcement dedup
│       │   └── health.py         # Prometheus Counter/Gauge + HTTP 노출
│       └── workers/
│           ├── __init__.py
│           ├── base_worker.py    # Abstract: poll_once() + _run_cycle() + run()
│           ├── fear_greed.py     # Alternative.me F&G, 5분
│           ├── ecos.py           # 한국은행 ECOS FX, 일별
│           ├── kimchi_premium.py # CryptoQuant Korea Premium, 1분
│           ├── announcement.py   # Upbit + Bithumb 공지, 15초
│           └── coinglass.py      # CoinGlass 청산·OI·펀딩비, 1분
├── tests/
│   ├── conftest.py               # fakeredis fixture 공유
│   ├── fixtures/
│   │   ├── upbit_notices.json    # Upbit XHR 응답 fixture
│   │   └── bithumb_notices.json  # Bithumb XHR 응답 fixture
│   ├── core/
│   │   ├── test_publisher.py
│   │   ├── test_dedup.py
│   │   └── test_health.py
│   └── workers/
│       ├── test_fear_greed.py
│       ├── test_ecos.py
│       ├── test_kimchi_premium.py
│       ├── test_announcement.py
│       └── test_coinglass.py
├── Dockerfile
├── compose.yml                   # 로컬 개발용 (redis 포함)
├── pyproject.toml
├── .env.example
└── README.md
```

`mctrader-hub/compose.yml` — signal-collector 서비스 5개 추가 (Task 12)

---

## Task 0: 리포 스캐폴드

**Files:**
- Create: `pyproject.toml`
- Create: `Dockerfile`
- Create: `compose.yml`
- Create: `.env.example`
- Create: `src/signal_collector/__init__.py`
- Create: `src/signal_collector/core/__init__.py`
- Create: `src/signal_collector/workers/__init__.py`

- [ ] **Step 1: 리포 디렉토리 초기화 및 Git 설정**

```powershell
cd c:\workspace\mclayer
mkdir mctrader-signal-collector
cd mctrader-signal-collector
git init
mkdir -p src/signal_collector/core src/signal_collector/workers tests/core tests/workers tests/fixtures
```

- [ ] **Step 2: pyproject.toml 작성**

`pyproject.toml`:
```toml
[project]
name = "mctrader-signal-collector"
version = "0.1.0"
description = "External signal ingestion service for mctrader — news, sentiment, on-chain, exchange announcements"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [{ name = "mccho8865", email = "mclayer8865@gmail.com" }]
dependencies = [
    "httpx>=0.27",
    "redis[hiredis]>=5",
    "prometheus-client>=0.20",
    "beautifulsoup4>=4.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    "fakeredis>=2.23",
    "pytest-mock>=3.14",
    "pyright>=1.1",
    "ruff>=0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/signal_collector"]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["UP017", "N801", "N818", "SIM300", "I001"]

[tool.pyright]
pythonVersion = "3.12"
include = ["src", "tests"]
reportMissingTypeStubs = "none"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers"
markers = [
    "integration: marks tests requiring real Redis (deselect with '-m \"not integration\"')",
]
```

- [ ] **Step 3: Dockerfile 작성 (mctrader-data 2-stage 패턴)**

`Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7

#─── Stage 1: deps ───
FROM python:3.12-slim AS deps

RUN pip install --no-cache-dir uv==0.5.11

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN uv pip install --system --no-cache .

#─── Stage 2: runner ───
FROM python:3.12-slim AS runner

RUN useradd --system --uid 1001 --no-create-home --shell /usr/sbin/nologin mctrader

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

ENV PYTHONUNBUFFERED=1

USER mctrader
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:9200/metrics').status==200 else 1)"]
```

- [ ] **Step 4: .env.example 및 compose.yml (개발용) 작성**

`.env.example`:
```
REDIS_URL=redis://localhost:6379
ECOS_API_KEY=your_ecos_api_key_here
CRYPTOQUANT_API_KEY=your_cryptoquant_api_key_here
COINGLASS_API_KEY=your_coinglass_api_key_here
```

`compose.yml` (로컬 개발 전용 — redis 포함):
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  signal-fear-greed:
    build: .
    command: ["python", "-m", "signal_collector.workers.fear_greed"]
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]

  signal-ecos:
    build: .
    command: ["python", "-m", "signal_collector.workers.ecos"]
    environment:
      - REDIS_URL=redis://redis:6379
      - ECOS_API_KEY=${ECOS_API_KEY}
    depends_on: [redis]

  signal-kimchi:
    build: .
    command: ["python", "-m", "signal_collector.workers.kimchi_premium"]
    environment:
      - REDIS_URL=redis://redis:6379
      - CRYPTOQUANT_API_KEY=${CRYPTOQUANT_API_KEY}
    depends_on: [redis]

  signal-announcement:
    build: .
    command: ["python", "-m", "signal_collector.workers.announcement"]
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]

  signal-coinglass:
    build: .
    command: ["python", "-m", "signal_collector.workers.coinglass"]
    environment:
      - REDIS_URL=redis://redis:6379
      - COINGLASS_API_KEY=${COINGLASS_API_KEY}
    depends_on: [redis]
```

- [ ] **Step 5: 빈 __init__.py 및 README.md 생성, 초기 커밋**

```
# src/signal_collector/__init__.py  → 빈 파일
# src/signal_collector/core/__init__.py  → 빈 파일
# src/signal_collector/workers/__init__.py  → 빈 파일
```

`README.md`:
```markdown
# mctrader-signal-collector

External signal ingestion service for mctrader. Collects Fear & Greed, ECOS FX, Kimchi Premium, exchange announcements, and CoinGlass derivatives data into Redis Streams.

## Quick Start

```bash
cp .env.example .env
# Fill in API keys
uv pip install -e ".[dev]"
pytest
docker compose up
```

```

```powershell
git add .
git commit -m "chore: initial scaffold — pyproject, Dockerfile, compose"
```

---

## Task 1: publisher.py

**Files:**
- Create: `src/signal_collector/core/publisher.py`
- Create: `tests/core/test_publisher.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: conftest.py — fakeredis fixture 작성**

`tests/conftest.py`:
```python
import fakeredis
import pytest
from signal_collector.core.publisher import Publisher


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis()


@pytest.fixture
def publisher(fake_redis):
    return Publisher(fake_redis)
```

- [ ] **Step 2: 테스트 작성**

`tests/core/test_publisher.py`:
```python
import json
import pytest
from signal_collector.core.publisher import Publisher


def test_publish_normal_message(publisher, fake_redis):
    publisher.publish("fear_greed", {"value": 72, "label": "Greed"}, stale=False)

    msgs = fake_redis.xrange("signals:fear_greed")
    assert len(msgs) == 1
    _, fields = msgs[0]
    assert fields[b"kind"] == b"fear_greed"
    assert fields[b"stale"] == b"false"
    data = json.loads(fields[b"raw"])
    assert data["value"] == 72
    assert data["label"] == "Greed"


def test_publish_stale_message(publisher, fake_redis):
    publisher.publish("fear_greed", {}, stale=True, reason="upstream_timeout")

    msgs = fake_redis.xrange("signals:fear_greed")
    assert len(msgs) == 1
    _, fields = msgs[0]
    assert fields[b"stale"] == b"true"
    assert fields[b"reason"] == b"upstream_timeout"
    assert json.loads(fields[b"raw"]) == {}


def test_publish_ts_field_present(publisher, fake_redis):
    publisher.publish("fear_greed", {"value": 50})
    _, fields = fake_redis.xrange("signals:fear_greed")[0]
    assert b"ts" in fields
    assert fields[b"ts"].endswith(b"Z")


def test_publish_different_kinds_go_to_different_streams(publisher, fake_redis):
    publisher.publish("fear_greed", {"value": 60})
    publisher.publish("kimchi_premium", {"premium_pct": 1.5})

    assert len(fake_redis.xrange("signals:fear_greed")) == 1
    assert len(fake_redis.xrange("signals:kimchi_premium")) == 1
```

- [ ] **Step 3: 테스트 실패 확인**

```powershell
cd c:\workspace\mclayer\mctrader-signal-collector
uv pip install -e ".[dev]"
pytest tests/core/test_publisher.py -v
```

Expected: `ModuleNotFoundError: No module named 'signal_collector'`

- [ ] **Step 4: publisher.py 구현**

`src/signal_collector/core/publisher.py`:
```python
import json
from datetime import datetime, timezone

import redis as redis_lib


class Publisher:
    def __init__(self, r: redis_lib.Redis) -> None:
        self._r = r

    def publish(
        self,
        kind: str,
        raw: dict,
        stale: bool = False,
        reason: str | None = None,
    ) -> None:
        fields: dict[str, str] = {
            "kind": kind,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stale": "true" if stale else "false",
            "raw": json.dumps(raw, ensure_ascii=False),
        }
        if reason is not None:
            fields["reason"] = reason
        self._r.xadd(f"signals:{kind}", fields, maxlen=10000, approximate=True)
```

- [ ] **Step 5: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/core/test_publisher.py -v
```

Expected: 4 passed

```powershell
git add src/signal_collector/core/publisher.py tests/conftest.py tests/core/test_publisher.py
git commit -m "feat: add Publisher — Redis Stream XADD with stale fallback"
```

---

## Task 2: dedup.py

**Files:**
- Create: `src/signal_collector/core/dedup.py`
- Create: `tests/core/test_dedup.py`

- [ ] **Step 1: 테스트 작성**

`tests/core/test_dedup.py`:
```python
from signal_collector.core.dedup import DedupStore


def test_new_id_not_seen(fake_redis):
    dedup = DedupStore(fake_redis)
    assert dedup.seen("abc123") is False


def test_mark_seen_then_seen(fake_redis):
    dedup = DedupStore(fake_redis)
    dedup.mark_seen("abc123")
    assert dedup.seen("abc123") is True


def test_different_ids_independent(fake_redis):
    dedup = DedupStore(fake_redis)
    dedup.mark_seen("id-A")
    assert dedup.seen("id-A") is True
    assert dedup.seen("id-B") is False


def test_mark_seen_idempotent(fake_redis):
    dedup = DedupStore(fake_redis)
    dedup.mark_seen("dup")
    dedup.mark_seen("dup")
    assert dedup.seen("dup") is True
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/core/test_dedup.py -v
```

Expected: `ImportError`

- [ ] **Step 3: dedup.py 구현**

`src/signal_collector/core/dedup.py`:
```python
import redis as redis_lib

_KEY = "signal_collector:seen_announcements"


class DedupStore:
    def __init__(self, r: redis_lib.Redis) -> None:
        self._r = r

    def seen(self, announcement_id: str) -> bool:
        return bool(self._r.sismember(_KEY, announcement_id))

    def mark_seen(self, announcement_id: str) -> None:
        self._r.sadd(_KEY, announcement_id)
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/core/test_dedup.py -v
```

Expected: 4 passed

```powershell
git add src/signal_collector/core/dedup.py tests/core/test_dedup.py
git commit -m "feat: add DedupStore — Redis Set for announcement dedup"
```

---

## Task 3: health.py

**Files:**
- Create: `src/signal_collector/core/health.py`
- Create: `tests/core/test_health.py`

- [ ] **Step 1: 테스트 작성**

`tests/core/test_health.py`:
```python
from signal_collector.core.health import HealthExporter


def test_record_success_increments_counter():
    health = HealthExporter()
    health.record_success("fear_greed")
    health.record_success("fear_greed")
    val = health._success.labels(kind="fear_greed")._value.get()
    assert val == 2.0


def test_record_error_increments_counter():
    health = HealthExporter()
    health.record_error("kimchi_premium")
    val = health._errors.labels(kind="kimchi_premium")._value.get()
    assert val == 1.0


def test_record_success_updates_last_success_ts():
    import time
    health = HealthExporter()
    before = time.time()
    health.record_success("ecos_fx")
    after = time.time()
    ts = health._last_success.labels(kind="ecos_fx")._value.get()
    assert before <= ts <= after
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/core/test_health.py -v
```

Expected: `ImportError`

- [ ] **Step 3: health.py 구현**

`src/signal_collector/core/health.py`:
```python
import time

from prometheus_client import Counter, Gauge, start_http_server


class HealthExporter:
    def __init__(self) -> None:
        self._success = Counter(
            "signal_worker_success_total",
            "Successful upstream polls",
            ["kind"],
        )
        self._errors = Counter(
            "signal_worker_error_total",
            "Failed upstream polls",
            ["kind"],
        )
        self._last_success = Gauge(
            "signal_worker_last_success_timestamp_seconds",
            "Unix timestamp of last successful poll",
            ["kind"],
        )

    def record_success(self, kind: str) -> None:
        self._success.labels(kind=kind).inc()
        self._last_success.labels(kind=kind).set(time.time())

    def record_error(self, kind: str) -> None:
        self._errors.labels(kind=kind).inc()

    def start(self, port: int = 9200) -> None:
        start_http_server(port)
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/core/test_health.py -v
```

Expected: 3 passed

```powershell
git add src/signal_collector/core/health.py tests/core/test_health.py
git commit -m "feat: add HealthExporter — Prometheus counters for worker freshness"
```

---

## Task 4: base_worker.py

**Files:**
- Create: `src/signal_collector/workers/base_worker.py`
- Create: `tests/workers/__init__.py`

- [ ] **Step 1: base_worker.py 구현 (테스트는 구체 Worker로 통합 검증)**

`src/signal_collector/workers/base_worker.py`:
```python
import logging
import time
from abc import ABC, abstractmethod

from signal_collector.core.health import HealthExporter
from signal_collector.core.publisher import Publisher

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    kind: str
    interval_seconds: int

    def __init__(self, publisher: Publisher, health: HealthExporter) -> None:
        self.publisher = publisher
        self.health = health

    @abstractmethod
    def poll_once(self) -> dict:
        """외부 API를 한 번 호출해 raw dict을 반환한다. 실패 시 예외를 raise한다."""

    def _run_cycle(self) -> None:
        """poll_once → publish → health 한 사이클. 테스트에서 직접 호출한다."""
        try:
            raw = self.poll_once()
            self.publisher.publish(self.kind, raw, stale=False)
            self.health.record_success(self.kind)
        except Exception as exc:
            logger.error("%s poll failed: %s", self.kind, exc)
            self.publisher.publish(self.kind, {}, stale=True, reason=str(exc))
            self.health.record_error(self.kind)

    def run(self) -> None:
        """프로세스 메인 루프. 무한 폴링."""
        while True:
            self._run_cycle()
            time.sleep(self.interval_seconds)
```

- [ ] **Step 2: `tests/workers/__init__.py` 빈 파일 생성 후 커밋**

```powershell
git add src/signal_collector/workers/base_worker.py tests/workers/__init__.py
git commit -m "feat: add BaseWorker — poll_once / _run_cycle / run abstract base"
```

---

## Task 5: fear_greed Worker (E2E 파이프라인 검증)

**Files:**
- Create: `src/signal_collector/workers/fear_greed.py`
- Create: `tests/workers/test_fear_greed.py`

- [ ] **Step 1: 테스트 작성**

`tests/workers/test_fear_greed.py`:
```python
import json
import pytest
from unittest.mock import MagicMock, patch
from signal_collector.workers.fear_greed import FearGreedWorker


MOCK_RESPONSE = {
    "data": [{"value": "72", "value_classification": "Greed", "timestamp": "1715000000"}]
}


@pytest.fixture
def worker(publisher, fake_redis):
    health = MagicMock()
    return FearGreedWorker(publisher=publisher, health=health)


def test_poll_once_returns_value_and_label(worker):
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        result = worker.poll_once()

    assert result["value"] == 72
    assert result["label"] == "Greed"


def test_poll_once_raises_on_http_error(worker):
    import httpx
    with patch("httpx.get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(httpx.TimeoutException):
            worker.poll_once()


def test_run_cycle_publishes_to_redis(worker, fake_redis):
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        worker._run_cycle()

    msgs = fake_redis.xrange("signals:fear_greed")
    assert len(msgs) == 1
    _, fields = msgs[0]
    assert fields[b"stale"] == b"false"
    data = json.loads(fields[b"raw"])
    assert data["value"] == 72


def test_run_cycle_publishes_stale_on_error(worker, fake_redis):
    import httpx
    with patch("httpx.get", side_effect=httpx.TimeoutException("timeout")):
        worker._run_cycle()

    msgs = fake_redis.xrange("signals:fear_greed")
    assert len(msgs) == 1
    _, fields = msgs[0]
    assert fields[b"stale"] == b"true"
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/workers/test_fear_greed.py -v
```

Expected: `ImportError`

- [ ] **Step 3: fear_greed.py 구현**

`src/signal_collector/workers/fear_greed.py`:
```python
import httpx

from signal_collector.workers.base_worker import BaseWorker

_URL = "https://api.alternative.me/fng/?limit=1"

_LABEL_MAP = {
    "Extreme Fear": "Extreme Fear",
    "Fear": "Fear",
    "Neutral": "Neutral",
    "Greed": "Greed",
    "Extreme Greed": "Extreme Greed",
}


class FearGreedWorker(BaseWorker):
    kind = "fear_greed"
    interval_seconds = 300  # 5분 (API 5분마다 갱신)

    def poll_once(self) -> dict:
        resp = httpx.get(_URL, timeout=10)
        resp.raise_for_status()
        entry = resp.json()["data"][0]
        return {
            "value": int(entry["value"]),
            "label": entry["value_classification"],
        }


if __name__ == "__main__":
    import os
    import redis
    from signal_collector.core.publisher import Publisher
    from signal_collector.core.health import HealthExporter

    r = redis.from_url(os.environ["REDIS_URL"])
    health = HealthExporter()
    health.start(port=9200)
    FearGreedWorker(Publisher(r), health).run()
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/workers/test_fear_greed.py -v
```

Expected: 4 passed

```powershell
git add src/signal_collector/workers/fear_greed.py tests/workers/test_fear_greed.py
git commit -m "feat: add FearGreedWorker — Alternative.me F&G 5분 폴링"
```

---

## Task 6: ecos Worker (한국은행 KRW/USD)

**Files:**
- Create: `src/signal_collector/workers/ecos.py`
- Create: `tests/workers/test_ecos.py`

- [ ] **Step 1: 테스트 작성**

`tests/workers/test_ecos.py`:
```python
import json
import pytest
from unittest.mock import MagicMock, patch
from signal_collector.workers.ecos import EcosWorker

MOCK_ECOS_RESPONSE = {
    "StatisticSearch": {
        "row": [{"DATA_VALUE": "1342.50", "TIME": "20260510"}]
    }
}

MOCK_ECOS_EMPTY = {"StatisticSearch": {"row": []}}


@pytest.fixture
def worker(publisher, fake_redis):
    health = MagicMock()
    return EcosWorker(publisher=publisher, health=health)


def test_poll_once_returns_usd_krw(worker, monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "test_key")
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_ECOS_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        result = worker.poll_once()

    assert result["usd_krw"] == pytest.approx(1342.50)


def test_poll_once_raises_on_empty_rows(worker, monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "test_key")
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_ECOS_EMPTY
        mock_get.return_value.raise_for_status.return_value = None
        with pytest.raises(ValueError, match="no rows"):
            worker.poll_once()


def test_run_cycle_publishes_ecos_fx(worker, fake_redis, monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "test_key")
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_ECOS_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        worker._run_cycle()

    msgs = fake_redis.xrange("signals:ecos_fx")
    assert len(msgs) == 1
    data = json.loads(msgs[0][1][b"raw"])
    assert data["usd_krw"] == pytest.approx(1342.50)
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/workers/test_ecos.py -v
```

Expected: `ImportError`

- [ ] **Step 3: ecos.py 구현**

`src/signal_collector/workers/ecos.py`:
```python
import os
from datetime import date

import httpx

from signal_collector.workers.base_worker import BaseWorker

# 731Y001 = 원달러 환율 일별 시계열 (한국은행 ECOS)
_SERIES_CODE = "731Y001"
_BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"


class EcosWorker(BaseWorker):
    kind = "ecos_fx"
    interval_seconds = 3600 * 6  # 6시간 (일 1회 갱신, 안전 마진)

    def poll_once(self) -> dict:
        api_key = os.environ["ECOS_API_KEY"]
        today = date.today().strftime("%Y%m%d")
        url = f"{_BASE_URL}/{api_key}/json/kr/1/1/{_SERIES_CODE}/D/{today}/{today}"
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        rows = resp.json().get("StatisticSearch", {}).get("row", [])
        if not rows:
            raise ValueError(f"ECOS returned no rows for {today}")
        return {"usd_krw": float(rows[0]["DATA_VALUE"])}


if __name__ == "__main__":
    import redis
    from signal_collector.core.publisher import Publisher
    from signal_collector.core.health import HealthExporter

    r = redis.from_url(os.environ["REDIS_URL"])
    health = HealthExporter()
    health.start(port=9200)
    EcosWorker(Publisher(r), health).run()
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/workers/test_ecos.py -v
```

Expected: 3 passed

```powershell
git add src/signal_collector/workers/ecos.py tests/workers/test_ecos.py
git commit -m "feat: add EcosWorker — 한국은행 ECOS KRW/USD 환율 수집"
```

---

## Task 7: kimchi_premium Worker

**Files:**
- Create: `src/signal_collector/workers/kimchi_premium.py`
- Create: `tests/workers/test_kimchi_premium.py`

- [ ] **Step 1: 테스트 작성**

`tests/workers/test_kimchi_premium.py`:
```python
import json
import pytest
from unittest.mock import MagicMock, patch
from signal_collector.workers.kimchi_premium import KimchiPremiumWorker

MOCK_RESPONSE = {
    "result": {
        "data": [
            {"korea_premium_index": "2.53", "datetime": 1715000000000}
        ]
    }
}


@pytest.fixture
def worker(publisher, fake_redis):
    health = MagicMock()
    return KimchiPremiumWorker(publisher=publisher, health=health)


def test_poll_once_returns_premium_pct(worker, monkeypatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "test_key")
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        result = worker.poll_once()

    assert result["premium_pct"] == pytest.approx(2.53)


def test_poll_once_raises_on_empty_data(worker, monkeypatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "test_key")
    empty = {"result": {"data": []}}
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = empty
        mock_get.return_value.raise_for_status.return_value = None
        with pytest.raises(ValueError, match="no data"):
            worker.poll_once()


def test_run_cycle_publishes_kimchi_premium(worker, fake_redis, monkeypatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "test_key")
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None
        worker._run_cycle()

    msgs = fake_redis.xrange("signals:kimchi_premium")
    assert len(msgs) == 1
    data = json.loads(msgs[0][1][b"raw"])
    assert data["premium_pct"] == pytest.approx(2.53)
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/workers/test_kimchi_premium.py -v
```

Expected: `ImportError`

- [ ] **Step 3: kimchi_premium.py 구현**

`src/signal_collector/workers/kimchi_premium.py`:
```python
import os

import httpx

from signal_collector.workers.base_worker import BaseWorker

_URL = "https://api.cryptoquant.com/v1/btc/market-data/korea-premium-index"


class KimchiPremiumWorker(BaseWorker):
    kind = "kimchi_premium"
    interval_seconds = 60  # 1분

    def poll_once(self) -> dict:
        api_key = os.environ["CRYPTOQUANT_API_KEY"]
        resp = httpx.get(
            _URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("result", {}).get("data", [])
        if not data:
            raise ValueError("CryptoQuant Korea Premium returned no data")
        latest = data[-1]
        return {
            "premium_pct": float(latest["korea_premium_index"]),
            "source_ts": latest.get("datetime"),
        }


if __name__ == "__main__":
    import redis
    from signal_collector.core.publisher import Publisher
    from signal_collector.core.health import HealthExporter

    r = redis.from_url(os.environ["REDIS_URL"])
    health = HealthExporter()
    health.start(port=9200)
    KimchiPremiumWorker(Publisher(r), health).run()
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/workers/test_kimchi_premium.py -v
```

Expected: 3 passed

```powershell
git add src/signal_collector/workers/kimchi_premium.py tests/workers/test_kimchi_premium.py
git commit -m "feat: add KimchiPremiumWorker — CryptoQuant Korea Premium 1분 폴링"
```

---

## Task 8: announcement Worker — 공지 API 엔드포인트 탐색

Upbit / Bithumb 는 React SPA 이므로 `httpx.get(notice_page_url)` 로는 목록을 얻을 수 없다. 실제 XHR API 엔드포인트를 먼저 찾아야 한다.

**Files:** (코드 없음, 발견 정보만 기록)

- [ ] **Step 1: Upbit 공지 XHR API 탐색**

1. Chrome에서 `https://upbit.com/service_center/notice` 열기
2. DevTools → Network 탭 → XHR/Fetch 필터
3. 페이지 새로고침 후 `notice` 또는 `announcement` 키워드가 포함된 요청 찾기
4. 응답 JSON 구조 확인 후 아래 파일에 기록:

`tests/fixtures/upbit_notices.json` — 실제 API 응답과 동일한 구조의 fixture 저장.

예상 구조 (실제 응답 확인 후 수정):
```json
{
  "data": {
    "list": [
      {
        "id": 12345,
        "title": "[거래지원] BTCS (BTC+S) 거래 지원 안내",
        "created_at": "2026-05-10T10:00:00+09:00"
      }
    ]
  }
}
```

- [ ] **Step 2: Bithumb 공지 XHR API 탐색**

1. Chrome에서 `https://www.bithumb.com/react/customer-support/notice/list` 열기
2. 동일하게 XHR 탐색
3. `tests/fixtures/bithumb_notices.json` 에 실제 응답 구조 저장

- [ ] **Step 3: 발견한 엔드포인트를 .env.example에 추가**

`.env.example` 에 추가:
```
UPBIT_NOTICE_API_URL=https://upbit.com/api/v1/...   # Step 1에서 발견한 실제 URL
BITHUMB_NOTICE_API_URL=https://www.bithumb.com/api/...  # Step 2에서 발견한 실제 URL
```

---

## Task 9: announcement Worker — 구현

**Files:**
- Create: `src/signal_collector/workers/announcement.py`
- Create: `tests/fixtures/upbit_notices.json`
- Create: `tests/fixtures/bithumb_notices.json`
- Create: `tests/workers/test_announcement.py`

- [ ] **Step 1: fixture JSON 파일 작성 (Task 8 발견 결과 기반)**

`tests/fixtures/upbit_notices.json` (Upbit 실제 구조로 교체):
```json
{
  "data": {
    "list": [
      {
        "id": 10001,
        "title": "[거래지원] BTCS (BTC+S) 마켓 거래 지원 안내",
        "created_at": "2026-05-10T10:00:00+09:00"
      },
      {
        "id": 10002,
        "title": "[점검] 서버 정기 점검 안내 (5/11 02:00~04:00)",
        "created_at": "2026-05-09T18:00:00+09:00"
      }
    ]
  }
}
```

`tests/fixtures/bithumb_notices.json` (Bithumb 실제 구조로 교체):
```json
{
  "data": [
    {
      "id": 20001,
      "title": "[거래지원] XYZ (XYZ) 원화마켓 거래 지원 안내",
      "regDt": "2026-05-10 11:00:00"
    },
    {
      "id": 20002,
      "title": "[입출금] ABC 입출금 일시 중단 안내",
      "regDt": "2026-05-09 15:00:00"
    }
  ]
}
```

- [ ] **Step 2: 테스트 작성**

`tests/workers/test_announcement.py`:
```python
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from signal_collector.core.dedup import DedupStore
from signal_collector.workers.announcement import AnnouncementWorker, classify_title

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def worker(publisher, fake_redis):
    health = MagicMock()
    dedup = DedupStore(fake_redis)
    return AnnouncementWorker(publisher=publisher, health=health, dedup=dedup)


def test_classify_listing():
    assert classify_title("[거래지원] BTCS 마켓 거래 지원 안내") == "listing"
    assert classify_title("[상장] XYZ 상장 안내") == "listing"


def test_classify_delisting():
    assert classify_title("[거래종료] ABC 거래 종료 안내") == "delisting"
    assert classify_title("[상장폐지] DEF 상장폐지 안내") == "delisting"


def test_classify_maintenance():
    assert classify_title("[점검] 서버 점검 안내") == "maintenance"


def test_classify_withdrawal():
    assert classify_title("[입출금] GHI 입출금 일시 중단") == "withdrawal"


def test_classify_other():
    assert classify_title("이벤트 당첨자 안내") == "other"


def test_fetch_upbit_parses_listings(worker, monkeypatch, fake_redis):
    monkeypatch.setenv("UPBIT_NOTICE_API_URL", "https://mock.upbit/notices")
    fixture = json.loads((FIXTURES / "upbit_notices.json").read_text())
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = fixture
        mock_get.return_value.raise_for_status.return_value = None
        events = worker._fetch_upbit()

    assert len(events) == 2
    listings = [e for e in events if e["type"] == "listing"]
    assert len(listings) == 1
    assert listings[0]["exchange"] == "upbit"


def test_fetch_bithumb_parses_listings(worker, monkeypatch, fake_redis):
    monkeypatch.setenv("BITHUMB_NOTICE_API_URL", "https://mock.bithumb/notices")
    fixture = json.loads((FIXTURES / "bithumb_notices.json").read_text())
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = fixture
        mock_get.return_value.raise_for_status.return_value = None
        events = worker._fetch_bithumb()

    assert len(events) == 2
    listings = [e for e in events if e["type"] == "listing"]
    assert len(listings) == 1
    assert listings[0]["exchange"] == "bithumb"


def test_dedup_prevents_duplicate_publish(worker, fake_redis, monkeypatch):
    monkeypatch.setenv("UPBIT_NOTICE_API_URL", "https://mock.upbit/notices")
    monkeypatch.setenv("BITHUMB_NOTICE_API_URL", "https://mock.bithumb/notices")
    upbit_fixture = json.loads((FIXTURES / "upbit_notices.json").read_text())
    bithumb_fixture = json.loads((FIXTURES / "bithumb_notices.json").read_text())

    def side_effect(url, **kwargs):
        m = MagicMock()
        m.raise_for_status.return_value = None
        if "upbit" in url:
            m.json.return_value = upbit_fixture
        else:
            m.json.return_value = bithumb_fixture
        return m

    with patch("httpx.get", side_effect=side_effect):
        worker._run_cycle()
        worker._run_cycle()  # 두 번째 사이클: 동일 공지

    msgs = fake_redis.xrange("signals:announcement")
    # 첫 사이클에서만 publish, 두 번째는 dedup으로 차단
    first_raw = json.loads(msgs[0][1][b"raw"])
    total_events = sum(len(json.loads(m[1][b"raw"])["events"]) for m in msgs)
    # 모든 이벤트가 1번씩만 publish됨
    assert total_events == len(first_raw["events"])
```

- [ ] **Step 3: 테스트 실패 확인**

```powershell
pytest tests/workers/test_announcement.py -v
```

Expected: `ImportError`

- [ ] **Step 4: announcement.py 구현**

`src/signal_collector/workers/announcement.py`:
```python
import hashlib
import os

import httpx

from signal_collector.core.dedup import DedupStore
from signal_collector.core.health import HealthExporter
from signal_collector.core.publisher import Publisher
from signal_collector.workers.base_worker import BaseWorker

_CLASSIFY_MAP = {
    "거래지원": "listing",
    "거래 지원": "listing",
    "상장": "listing",
    "상장폐지": "delisting",
    "거래종료": "delisting",
    "거래 종료": "delisting",
    "입출금": "withdrawal",
    "점검": "maintenance",
}


def classify_title(title: str) -> str:
    for keyword, kind in _CLASSIFY_MAP.items():
        if keyword in title:
            return kind
    return "other"


def _make_id(exchange: str, notice_id: str | int) -> str:
    raw = f"{exchange}:{notice_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class AnnouncementWorker(BaseWorker):
    kind = "announcement"
    interval_seconds = 15

    def __init__(self, publisher: Publisher, health: HealthExporter, dedup: DedupStore) -> None:
        super().__init__(publisher, health)
        self._dedup = dedup

    def poll_once(self) -> dict:
        events = self._fetch_upbit() + self._fetch_bithumb()
        new_events = []
        for e in events:
            if not self._dedup.seen(e["id"]):
                self._dedup.mark_seen(e["id"])
                new_events.append(e)
        return {"events": new_events}

    def _fetch_upbit(self) -> list[dict]:
        url = os.environ["UPBIT_NOTICE_API_URL"]
        try:
            resp = httpx.get(url, timeout=10, headers={"User-Agent": "mctrader-signal/1.0"})
            resp.raise_for_status()
            # 구조: {"data": {"list": [{"id": int, "title": str, "created_at": str}]}}
            # Task 8에서 발견한 실제 구조로 아래 키 경로를 수정할 것
            items = resp.json()["data"]["list"]
            return [
                {
                    "id": _make_id("upbit", item["id"]),
                    "exchange": "upbit",
                    "notice_id": item["id"],
                    "title": item["title"],
                    "type": classify_title(item["title"]),
                }
                for item in items
            ]
        except Exception:
            return []

    def _fetch_bithumb(self) -> list[dict]:
        url = os.environ["BITHUMB_NOTICE_API_URL"]
        try:
            resp = httpx.get(url, timeout=10, headers={"User-Agent": "mctrader-signal/1.0"})
            resp.raise_for_status()
            # 구조: {"data": [{"id": int, "title": str, "regDt": str}]}
            # Task 8에서 발견한 실제 구조로 아래 키 경로를 수정할 것
            items = resp.json()["data"]
            return [
                {
                    "id": _make_id("bithumb", item["id"]),
                    "exchange": "bithumb",
                    "notice_id": item["id"],
                    "title": item["title"],
                    "type": classify_title(item["title"]),
                }
                for item in items
            ]
        except Exception:
            return []


if __name__ == "__main__":
    import redis
    from signal_collector.core.publisher import Publisher
    from signal_collector.core.health import HealthExporter
    from signal_collector.core.dedup import DedupStore

    r = redis.from_url(os.environ["REDIS_URL"])
    health = HealthExporter()
    health.start(port=9200)
    AnnouncementWorker(Publisher(r), health, DedupStore(r)).run()
```

- [ ] **Step 5: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/workers/test_announcement.py -v
```

Expected: 8 passed

```powershell
git add src/signal_collector/workers/announcement.py tests/workers/test_announcement.py tests/fixtures/
git commit -m "feat: add AnnouncementWorker — Upbit/Bithumb 공지 15초 폴링 + dedup"
```

---

## Task 10: coinglass Worker

**Files:**
- Create: `src/signal_collector/workers/coinglass.py`
- Create: `tests/workers/test_coinglass.py`

- [ ] **Step 1: 테스트 작성**

`tests/workers/test_coinglass.py`:
```python
import json
import pytest
from unittest.mock import MagicMock, patch, call
from signal_collector.workers.coinglass import CoinGlassWorker

MOCK_LIQ = {
    "data": {
        "buyLiquidationMap": {"BTC": 120000000},
        "sellLiquidationMap": {"BTC": 85000000},
    }
}

MOCK_FUNDING = {
    "data": [
        {"exchangeName": "Binance", "fundingRate": 0.0001},
        {"exchangeName": "OKX", "fundingRate": -0.0002},
    ]
}

MOCK_OI = {
    "data": {"openInterest": 28500000000}
}


@pytest.fixture
def worker(publisher, fake_redis):
    health = MagicMock()
    return CoinGlassWorker(publisher=publisher, health=health)


def test_poll_once_returns_all_fields(worker, monkeypatch):
    monkeypatch.setenv("COINGLASS_API_KEY", "test_key")

    responses = [MOCK_LIQ, MOCK_FUNDING, MOCK_OI]
    call_count = 0

    def side_effect(url, **kwargs):
        nonlocal call_count
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = responses[call_count]
        call_count += 1
        return m

    with patch("httpx.get", side_effect=side_effect):
        result = worker.poll_once()

    assert "liquidations" in result
    assert "funding_rates" in result
    assert "open_interest" in result


def test_run_cycle_publishes_coinglass(worker, fake_redis, monkeypatch):
    monkeypatch.setenv("COINGLASS_API_KEY", "test_key")
    responses = [MOCK_LIQ, MOCK_FUNDING, MOCK_OI]
    call_count = 0

    def side_effect(url, **kwargs):
        nonlocal call_count
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = responses[call_count % len(responses)]
        call_count += 1
        return m

    with patch("httpx.get", side_effect=side_effect):
        worker._run_cycle()

    msgs = fake_redis.xrange("signals:coinglass")
    assert len(msgs) == 1
    assert msgs[0][1][b"stale"] == b"false"
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
pytest tests/workers/test_coinglass.py -v
```

Expected: `ImportError`

- [ ] **Step 3: coinglass.py 구현**

`src/signal_collector/workers/coinglass.py`:
```python
import os

import httpx

from signal_collector.workers.base_worker import BaseWorker

_BASE = "https://open-api.coinglass.com/public/v2"


class CoinGlassWorker(BaseWorker):
    kind = "coinglass"
    interval_seconds = 60  # 1분

    def poll_once(self) -> dict:
        api_key = os.environ["COINGLASS_API_KEY"]
        headers = {"coinglassSecret": api_key}

        liq_resp = httpx.get(
            f"{_BASE}/liquidation/detail",
            headers=headers,
            params={"symbol": "BTC", "time_type": "h1"},
            timeout=10,
        )
        liq_resp.raise_for_status()

        funding_resp = httpx.get(
            f"{_BASE}/funding",
            headers=headers,
            params={"symbol": "BTC"},
            timeout=10,
        )
        funding_resp.raise_for_status()

        oi_resp = httpx.get(
            f"{_BASE}/open_interest",
            headers=headers,
            params={"symbol": "BTC"},
            timeout=10,
        )
        oi_resp.raise_for_status()

        return {
            "liquidations": liq_resp.json().get("data", {}),
            "funding_rates": funding_resp.json().get("data", [])[:10],
            "open_interest": oi_resp.json().get("data", {}),
        }


if __name__ == "__main__":
    import redis
    from signal_collector.core.publisher import Publisher
    from signal_collector.core.health import HealthExporter

    r = redis.from_url(os.environ["REDIS_URL"])
    health = HealthExporter()
    health.start(port=9200)
    CoinGlassWorker(Publisher(r), health).run()
```

- [ ] **Step 4: 테스트 통과 확인 및 커밋**

```powershell
pytest tests/workers/test_coinglass.py -v
```

Expected: 2 passed

```powershell
git add src/signal_collector/workers/coinglass.py tests/workers/test_coinglass.py
git commit -m "feat: add CoinGlassWorker — 청산/OI/펀딩비 1분 폴링"
```

---

## Task 11: Hub compose.yml 통합

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\compose.yml`

- [ ] **Step 1: 현재 hub compose.yml 마지막 서비스 확인**

```powershell
Get-Content c:\workspace\mclayer\mctrader-hub\compose.yml | Select-Object -Last 30
```

- [ ] **Step 2: signal-collector 서비스 5개 추가**

`c:\workspace\mclayer\mctrader-hub\compose.yml` 의 `services:` 블록에 추가 (기존 서비스 아래):

```yaml
  signal-fear-greed:
    image: ghcr.io/mclayer/mctrader-signal-collector:latest
    build:
      context: ../mctrader-signal-collector
    command: ["python", "-m", "signal_collector.workers.fear_greed"]
    environment:
      - REDIS_URL=redis://redis:6379
    networks: [mctrader_net]
    restart: unless-stopped
    depends_on: [redis]

  signal-ecos:
    image: ghcr.io/mclayer/mctrader-signal-collector:latest
    build:
      context: ../mctrader-signal-collector
    command: ["python", "-m", "signal_collector.workers.ecos"]
    environment:
      - REDIS_URL=redis://redis:6379
      - ECOS_API_KEY=${ECOS_API_KEY}
    networks: [mctrader_net]
    restart: unless-stopped
    depends_on: [redis]

  signal-kimchi:
    image: ghcr.io/mclayer/mctrader-signal-collector:latest
    build:
      context: ../mctrader-signal-collector
    command: ["python", "-m", "signal_collector.workers.kimchi_premium"]
    environment:
      - REDIS_URL=redis://redis:6379
      - CRYPTOQUANT_API_KEY=${CRYPTOQUANT_API_KEY}
    networks: [mctrader_net]
    restart: unless-stopped
    depends_on: [redis]

  signal-announcement:
    image: ghcr.io/mclayer/mctrader-signal-collector:latest
    build:
      context: ../mctrader-signal-collector
    command: ["python", "-m", "signal_collector.workers.announcement"]
    environment:
      - REDIS_URL=redis://redis:6379
      - UPBIT_NOTICE_API_URL=${UPBIT_NOTICE_API_URL}
      - BITHUMB_NOTICE_API_URL=${BITHUMB_NOTICE_API_URL}
    networks: [mctrader_net]
    restart: unless-stopped
    depends_on: [redis]

  signal-coinglass:
    image: ghcr.io/mclayer/mctrader-signal-collector:latest
    build:
      context: ../mctrader-signal-collector
    command: ["python", "-m", "signal_collector.workers.coinglass"]
    environment:
      - REDIS_URL=redis://redis:6379
      - COINGLASS_API_KEY=${COINGLASS_API_KEY}
    networks: [mctrader_net]
    restart: unless-stopped
    depends_on: [redis]
```

- [ ] **Step 3: hub .env.example 에 신규 키 추가**

`c:\workspace\mclayer\mctrader-hub\.env.example` 에 추가:
```
ECOS_API_KEY=
CRYPTOQUANT_API_KEY=
COINGLASS_API_KEY=
UPBIT_NOTICE_API_URL=
BITHUMB_NOTICE_API_URL=
```

- [ ] **Step 4: hub 커밋**

```powershell
cd c:\workspace\mclayer\mctrader-hub
git add compose.yml .env.example
git commit -m "feat(compose): add signal-collector 5 services to hub compose"
```

---

## Task 12: 전체 테스트 통과 확인

- [ ] **Step 1: signal-collector 리포 전체 pytest**

```powershell
cd c:\workspace\mclayer\mctrader-signal-collector
pytest -v
```

Expected: 전체 통과. 실패 시 에러 메시지 기반으로 수정.

- [ ] **Step 2: 로컬 Docker 빌드 확인**

```powershell
cd c:\workspace\mclayer\mctrader-signal-collector
docker build -t mctrader-signal-collector:local .
```

Expected: 빌드 성공

- [ ] **Step 3: fear_greed 워커 단독 연기 (실제 API 호출 확인)**

```powershell
docker run --rm -e REDIS_URL=redis://host.docker.internal:6380 mctrader-signal-collector:local python -m signal_collector.workers.fear_greed
```

별도 터미널에서 Redis Stream 확인:
```powershell
# redis-cli 가 설치된 경우
redis-cli -p 6380 XRANGE signals:fear_greed - + COUNT 1
```

Expected: `value`, `label`, `stale=false` 필드 포함 메시지 1개

- [ ] **Step 4: signal-collector 리포 최종 커밋**

```powershell
cd c:\workspace\mclayer\mctrader-signal-collector
git add .
git commit -m "chore: all workers implemented and tested"
```
