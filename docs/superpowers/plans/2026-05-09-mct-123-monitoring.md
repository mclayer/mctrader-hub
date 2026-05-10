# MCT-123: Prometheus + Grafana 모니터링 도입 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prometheus/Grafana 스택을 hub에 추가하고, ingester·compactor·engine에 커스텀 `/metrics` endpoint를 구현하여 WAL write lag, Parquet freshness, engine cycle delay 등 자동매매 도메인 지표를 실시간 관측한다.

**Architecture:** hub compose.yml에 prometheus + grafana + postgres_exporter + cadvisor + node-exporter 5개 서비스 추가. mctrader-data와 mctrader-engine의 기존 HealthServer에 `/metrics` 경로 추가. `prometheus_client` 라이브러리로 Counter/Gauge 노출.

**Tech Stack:** prom/prometheus:latest, grafana/grafana:latest, postgres_exporter, cadvisor, node-exporter, prometheus-client>=0.20 (Python)

---

## File Map

| Action | File |
|---|---|
| Modify | `mctrader-hub/compose.yml` |
| Modify | `mctrader-hub/.env.example` |
| Create | `mctrader-hub/monitoring/prometheus.yml` |
| Create | `mctrader-hub/monitoring/grafana/provisioning/datasources/prometheus.yml` |
| Create | `mctrader-hub/monitoring/grafana/provisioning/dashboards/dashboard.yml` |
| Modify | `mctrader-data/pyproject.toml` |
| Create | `mctrader-data/src/mctrader_data/metrics.py` |
| Modify | `mctrader-data/src/mctrader_data/health_server.py` |
| Modify | `mctrader-engine/pyproject.toml` |
| Create | `mctrader-engine/src/mctrader_engine/metrics.py` |
| Modify | `mctrader-engine/src/mctrader_engine/health_server.py` |
| Create | `mctrader-data/tests/test_metrics_endpoint.py` |
| Create | `mctrader-engine/tests/test_metrics_endpoint.py` |

---

## Task 1: prometheus-client 의존성 추가

**Files:**
- Modify: `mctrader-data/pyproject.toml`
- Modify: `mctrader-engine/pyproject.toml`

- [ ] **Step 1: mctrader-data에 추가**

`mctrader-data/pyproject.toml`의 `dependencies` 배열에 추가:

```toml
    "prometheus-client>=0.20",
```

- [ ] **Step 2: mctrader-engine에 추가**

`mctrader-engine/pyproject.toml`의 `dependencies` 배열에 추가:

```toml
    "prometheus-client>=0.20",
```

- [ ] **Step 3: 설치 확인**

```bash
cd c:\workspace\mclayer\mctrader-data && pip install -e ".[dev]"
cd c:\workspace\mclayer\mctrader-engine && pip install -e ".[dev]"
python -c "import prometheus_client; print(prometheus_client.__version__)"
```

Expected: 0.20.x 버전 출력

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-data
git add pyproject.toml
git commit -m "feat(mct-123): add prometheus-client dependency"

cd c:\workspace\mclayer\mctrader-engine
git add pyproject.toml
git commit -m "feat(mct-123): add prometheus-client dependency"
```

---

## Task 2: mctrader-data metrics 모듈 구현 (TDD)

**Files:**
- Create: `mctrader-data/src/mctrader_data/metrics.py`
- Create: `mctrader-data/tests/test_metrics_endpoint.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`mctrader-data/tests/test_metrics_endpoint.py` 생성:

```python
# tests/test_metrics_endpoint.py
import threading
import time
import urllib.request

import pytest

from mctrader_data.metrics import (
    ingester_events_total,
    compactor_last_l3_timestamp,
    record_ingester_event,
    record_l3_compaction,
)
from mctrader_data.health_server import HealthServer


def test_record_ingester_event_increments_counter():
    before = ingester_events_total.labels(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction"
    )._value.get()
    record_ingester_event(exchange="bithumb", symbol="KRW-BTC", channel="transaction")
    after = ingester_events_total.labels(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction"
    )._value.get()
    assert after == before + 1


def test_record_l3_compaction_sets_gauge():
    record_l3_compaction(exchange="bithumb", symbol="KRW-BTC", channel="transaction")
    ts = compactor_last_l3_timestamp.labels(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction"
    )._value.get()
    assert ts > 0


def test_health_server_exposes_metrics_endpoint():
    server = HealthServer(heartbeat_writer=None, port=18181)
    server.start()
    time.sleep(0.1)
    try:
        with urllib.request.urlopen("http://localhost:18181/metrics") as resp:
            assert resp.status == 200
            content_type = resp.headers.get("Content-Type", "")
            assert "text/plain" in content_type
            body = resp.read().decode()
            assert "mctrader_ingester_events_total" in body
    finally:
        server.stop()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd c:\workspace\mclayer\mctrader-data
pytest tests/test_metrics_endpoint.py -v
```

Expected: `ImportError` (metrics 모듈 없음)

- [ ] **Step 3: metrics.py 구현**

`mctrader-data/src/mctrader_data/metrics.py` 생성:

```python
# src/mctrader_data/metrics.py
"""Prometheus metrics for mctrader-data ingester and compactor."""
from __future__ import annotations

import time

from prometheus_client import Counter, Gauge

ingester_events_total = Counter(
    "mctrader_ingester_events_total",
    "Total events written to WAL",
    ["exchange", "symbol", "channel"],
)

wal_write_lag_seconds = Gauge(
    "mctrader_wal_write_lag_seconds",
    "Seconds since last WAL write per (exchange, symbol)",
    ["exchange", "symbol"],
)

compactor_last_l3_timestamp = Gauge(
    "mctrader_compactor_last_l3_timestamp_seconds",
    "Unix timestamp of most recent successful L3 compaction",
    ["exchange", "symbol", "channel"],
)

compactor_l3_runs_total = Counter(
    "mctrader_compactor_l3_runs_total",
    "Total L3 compaction runs completed",
    ["exchange", "symbol", "channel"],
)


def record_ingester_event(*, exchange: str, symbol: str, channel: str) -> None:
    ingester_events_total.labels(exchange=exchange, symbol=symbol, channel=channel).inc()


def record_l3_compaction(*, exchange: str, symbol: str, channel: str) -> None:
    now = time.time()
    compactor_last_l3_timestamp.labels(
        exchange=exchange, symbol=symbol, channel=channel
    ).set(now)
    compactor_l3_runs_total.labels(
        exchange=exchange, symbol=symbol, channel=channel
    ).inc()
```

- [ ] **Step 4: health_server.py에 /metrics 경로 추가**

`mctrader-data/src/mctrader_data/health_server.py`의 `_HealthHandler.do_GET` 메서드를 수정:

기존:
```python
    def do_GET(self) -> None:  # noqa: N802 (stdlib API)
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        status, body = _build_response(self.heartbeat_writer, self.max_stale_seconds)
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
```

교체 후:
```python
    def do_GET(self) -> None:  # noqa: N802 (stdlib API)
        if self.path == "/health":
            status, body = _build_response(self.heartbeat_writer, self.max_stale_seconds)
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/metrics":
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
            payload = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/test_metrics_endpoint.py -v
```

Expected: 3개 PASSED

- [ ] **Step 6: Commit**

```bash
git add src/mctrader_data/metrics.py src/mctrader_data/health_server.py tests/test_metrics_endpoint.py
git commit -m "feat(mct-123): add Prometheus /metrics endpoint to mctrader-data health_server"
```

---

## Task 3: mctrader-engine metrics 모듈 구현 (TDD)

**Files:**
- Create: `mctrader-engine/src/mctrader_engine/metrics.py`
- Modify: `mctrader-engine/src/mctrader_engine/health_server.py`
- Create: `mctrader-engine/tests/test_metrics_endpoint.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`mctrader-engine/tests/test_metrics_endpoint.py` 생성:

```python
# tests/test_metrics_endpoint.py
import time
import urllib.request
from unittest.mock import MagicMock

import pytest

from mctrader_engine.metrics import (
    engine_open_positions,
    engine_open_orders,
    set_open_positions,
    set_open_orders,
)
from mctrader_engine.health_server import HealthServer


def test_set_open_positions_updates_gauge():
    set_open_positions(strategy="sma_cross", symbol="KRW-BTC", count=3)
    val = engine_open_positions.labels(strategy="sma_cross", symbol="KRW-BTC")._value.get()
    assert val == 3.0


def test_set_open_orders_updates_gauge():
    set_open_orders(strategy="sma_cross", symbol="KRW-BTC", count=1)
    val = engine_open_orders.labels(strategy="sma_cross", symbol="KRW-BTC")._value.get()
    assert val == 1.0


def test_engine_health_server_exposes_metrics():
    mock_runner = MagicMock()
    mock_runner.has_active_executor = True
    mock_runner.ws_connected = True

    server = HealthServer(runner_provider=lambda: mock_runner, port=18182)
    server.start()
    time.sleep(0.1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:18182/metrics") as resp:
            assert resp.status == 200
            body = resp.read().decode()
            assert "mctrader_engine_open_positions" in body
    finally:
        server.stop()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd c:\workspace\mclayer\mctrader-engine
pytest tests/test_metrics_endpoint.py -v
```

Expected: `ImportError` (metrics 모듈 없음)

- [ ] **Step 3: metrics.py 구현**

`mctrader-engine/src/mctrader_engine/metrics.py` 생성:

```python
# src/mctrader_engine/metrics.py
"""Prometheus metrics for mctrader-engine paper daemon."""
from __future__ import annotations

from prometheus_client import Counter, Gauge

engine_open_positions = Gauge(
    "mctrader_engine_open_positions",
    "Number of currently open positions",
    ["strategy", "symbol"],
)

engine_open_orders = Gauge(
    "mctrader_engine_open_orders",
    "Number of currently open orders",
    ["strategy", "symbol"],
)

engine_cycle_delay_seconds = Gauge(
    "mctrader_engine_cycle_delay_seconds",
    "Seconds elapsed since last strategy cycle execution",
    ["strategy"],
)

engine_db_write_latency_seconds = Gauge(
    "mctrader_engine_db_write_latency_seconds",
    "Latency of last database write operation",
    ["operation"],
)

engine_cycles_total = Counter(
    "mctrader_engine_cycles_total",
    "Total strategy cycles executed",
    ["strategy", "symbol"],
)


def set_open_positions(*, strategy: str, symbol: str, count: int) -> None:
    engine_open_positions.labels(strategy=strategy, symbol=symbol).set(count)


def set_open_orders(*, strategy: str, symbol: str, count: int) -> None:
    engine_open_orders.labels(strategy=strategy, symbol=symbol).set(count)


def record_cycle(*, strategy: str, symbol: str, delay_seconds: float) -> None:
    engine_cycles_total.labels(strategy=strategy, symbol=symbol).inc()
    engine_cycle_delay_seconds.labels(strategy=strategy).set(delay_seconds)
```

- [ ] **Step 4: health_server.py에 /metrics 경로 추가**

`mctrader-engine/src/mctrader_engine/health_server.py`의 `_Handler.do_GET` 메서드를 수정:

기존 `/health` 분기 외에 `/metrics` 분기 추가:

```python
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            runner = self.__class__.runner_provider()
            body, code = _evaluate(runner)
            payload = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/metrics":
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
            payload = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()
```

주의: 기존 `HealthServer` 코드에서 `_Handler`에 listen 주소가 `"127.0.0.1"`로 설정되어 있음. Prometheus가 컨테이너 네트워크에서 scrape하려면 `"0.0.0.0"`으로 변경 필요:

```python
        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), handler_cls)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/test_metrics_endpoint.py -v
```

Expected: 3개 PASSED

- [ ] **Step 6: Commit**

```bash
git add src/mctrader_engine/metrics.py src/mctrader_engine/health_server.py tests/test_metrics_endpoint.py
git commit -m "feat(mct-123): add Prometheus /metrics endpoint to mctrader-engine health_server"
```

---

## Task 4: hub — Prometheus scrape config 작성

**Files:**
- Create: `mctrader-hub/monitoring/prometheus.yml`

- [ ] **Step 1: 디렉토리 생성 및 prometheus.yml 작성**

`mctrader-hub/monitoring/prometheus.yml` 생성:

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: [localhost:9090]

  - job_name: postgres
    static_configs:
      - targets: [postgres_exporter:9187]

  - job_name: cadvisor
    static_configs:
      - targets: [cadvisor:8080]
    metrics_path: /metrics

  - job_name: node
    static_configs:
      - targets: [node_exporter:9100]

  - job_name: mctrader-data-ingester-bithumb
    static_configs:
      - targets: [mctrader-ingester-bithumb:8080]
    metrics_path: /metrics

  - job_name: mctrader-data-compactor
    static_configs:
      - targets: [mctrader-compactor:8080]
    metrics_path: /metrics

  - job_name: mctrader-engine-paper
    static_configs:
      - targets: [mctrader-engine-paper:8080]
    metrics_path: /metrics
```

- [ ] **Step 2: Grafana datasource provisioning 작성**

`mctrader-hub/monitoring/grafana/provisioning/datasources/prometheus.yml` 생성:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

- [ ] **Step 3: Grafana dashboard provisioning 설정**

`mctrader-hub/monitoring/grafana/provisioning/dashboards/dashboard.yml` 생성:

```yaml
apiVersion: 1
providers:
  - name: mctrader
    folder: mctrader
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-hub
git add monitoring/
git commit -m "feat(mct-123): add Prometheus scrape config + Grafana provisioning"
```

---

## Task 5: hub compose.yml — 모니터링 서비스 5개 추가

**Files:**
- Modify: `mctrader-hub/compose.yml`
- Modify: `mctrader-hub/.env.example`

- [ ] **Step 1: compose.yml에 5개 서비스 추가**

`mctrader-hub/compose.yml`의 `services:` 블록에 추가 (MCT-120/121 변경 이후 기준):

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: mctrader-prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - mctrader_prometheus:/prometheus
    networks:
      mctrader_net:
        aliases:
          - prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped
    labels:
      mctrader.role: "prometheus"
      mctrader.story: "MCT-123"

  grafana:
    image: grafana/grafana:latest
    container_name: mctrader-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_AUTH_ANONYMOUS_ENABLED: "false"
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - mctrader_grafana:/var/lib/grafana
    networks:
      mctrader_net:
        aliases:
          - grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped
    labels:
      mctrader.role: "grafana"
      mctrader.story: "MCT-123"

  postgres_exporter:
    image: quay.io/prometheuscommunity/postgres-exporter:latest
    container_name: mctrader-postgres-exporter
    environment:
      DATA_SOURCE_NAME: postgresql://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader?sslmode=disable
    networks:
      - mctrader_net
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    labels:
      mctrader.role: "postgres-exporter"
      mctrader.story: "MCT-123"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: mctrader-cadvisor
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    networks:
      - mctrader_net
    restart: unless-stopped
    labels:
      mctrader.role: "cadvisor"
      mctrader.story: "MCT-123"

  node_exporter:
    image: prom/node-exporter:latest
    container_name: mctrader-node-exporter
    command:
      - --path.procfs=/host/proc
      - --path.sysfs=/host/sys
      - --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - mctrader_net
    restart: unless-stopped
    labels:
      mctrader.role: "node-exporter"
      mctrader.story: "MCT-123"
```

`volumes:` 섹션에 추가:

```yaml
  mctrader_prometheus:
  mctrader_grafana:
```

- [ ] **Step 2: .env.example에 Grafana 변수 추가**

`mctrader-hub/.env.example`:

```
POSTGRES_PASSWORD=changeme
MINIO_ACCESS_KEY=mctrader
MINIO_SECRET_KEY=changeme_minio
GRAFANA_ADMIN_PASSWORD=changeme_grafana
```

- [ ] **Step 3: 기동 확인**

```bash
cd c:\workspace\mclayer\mctrader-hub
docker compose up -d prometheus grafana postgres_exporter node_exporter
```

```bash
# Prometheus UI 확인
curl http://localhost:9090/-/healthy
# Grafana UI 확인
curl http://localhost:3000/api/health
```

Expected: 양쪽 모두 200 OK

- [ ] **Step 4: Prometheus targets 확인**

브라우저에서 `http://localhost:9090/targets` 열어 scrape 대상 목록 확인.

Expected: postgres, node, cadvisor targets `UP` 상태

- [ ] **Step 5: Commit**

```bash
git add compose.yml .env.example
git commit -m "feat(mct-123): add Prometheus+Grafana+exporters to hub compose"
```

---

## Task 6: ingester metrics 호출 연결

**Files:**
- Modify: `mctrader-data/src/mctrader_data/collector.py`

- [ ] **Step 1: _emit_to_wal에서 record_ingester_event 호출**

`collector.py`의 `_emit_to_wal` 각 분기에서 `ingester.append(record)` 직후 호출 추가.

TransactionEvent 분기:

```python
                ingester.append(record)
                from mctrader_data.metrics import record_ingester_event
                record_ingester_event(exchange=event.exchange, symbol=str(event.symbol), channel="transaction")
```

OrderbookSnapshotEvent 분기:

```python
                ingester.append(record)
                from mctrader_data.metrics import record_ingester_event
                record_ingester_event(exchange=event.exchange, symbol=str(event.symbol), channel="orderbooksnapshot")
```

OrderbookDeltaEvent 분기:

```python
                ingester.append(record)
                from mctrader_data.metrics import record_ingester_event
                record_ingester_event(exchange=event.exchange, symbol=str(event.symbol), channel="orderbookdepth")
```

- [ ] **Step 2: 기존 테스트 통과 확인**

```bash
cd c:\workspace\mclayer\mctrader-data
pytest tests/ -v --ignore=tests/integration
```

Expected: 전체 PASSED

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_data/collector.py
git commit -m "feat(mct-123): emit ingester_events_total metric on each WAL write"
```

---

## Task 7: compactor metrics 호출 연결

**Files:**
- Modify: `mctrader-data/src/mctrader_data/compactor/runner.py`

- [ ] **Step 1: _run_l3_for_parquet에서 record_l3_compaction 호출**

`runner.py`의 `_run_l3_for_parquet` 메서드에서 `self._minio.upload(out)` 호출 블록 이후:

```python
    def _run_l3_for_parquet(
        self,
        *,
        exchange: str,
        symbol: str,
        channel: str,
        now_date: date | None,
    ) -> None:
        from datetime import date as _date
        d = now_date or datetime.now(timezone.utc).date()
        out = self._l3.compact_day(
            exchange=exchange, symbol=symbol, channel=channel, date_utc=d,
        )
        if out is not None:
            from mctrader_data.metrics import record_l3_compaction
            record_l3_compaction(exchange=exchange, symbol=symbol, channel=channel)
            if self._minio is not None:
                try:
                    self._minio.upload(out)
                except Exception:
                    log.exception("[compactor] MinIO upload failed %s", out)
```

- [ ] **Step 2: 기존 테스트 통과 확인**

```bash
pytest tests/compactor/ -v
```

Expected: 전체 PASSED

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_data/compactor/runner.py
git commit -m "feat(mct-123): emit compactor_last_l3_timestamp metric after L3 compaction"
```

---

## Self-Review

**Spec coverage:**
- [x] prometheus 컨테이너 (30d retention) (Task 5)
- [x] grafana 컨테이너 + datasource provisioning (Task 4, 5)
- [x] postgres_exporter (Task 5)
- [x] cadvisor (Task 5)
- [x] node-exporter (Task 5)
- [x] mctrader-data /metrics endpoint (Task 2)
- [x] mctrader-engine /metrics endpoint (Task 3)
- [x] ingester_events_total Counter (Task 2, 6)
- [x] compactor_last_l3_timestamp Gauge (Task 2, 7)
- [x] engine_open_positions, engine_open_orders Gauge (Task 3)
- [x] engine HealthServer listen 0.0.0.0 (Task 3 — prometheus scrape 필요)
- [x] GRAFANA_ADMIN_PASSWORD 환경변수 (Task 5)

**Prometheus scrape 대상 전체 목록:**
```
prometheus:9090, postgres_exporter:9187, cadvisor:8080, node_exporter:9100,
mctrader-ingester-bithumb:8080/metrics, mctrader-compactor:8080/metrics,
mctrader-engine-paper:8080/metrics
```

**주의사항:** symbol label은 54개로 안전하나 order_id/trade_id는 label로 절대 사용 금지 (카디널리티 폭발).
