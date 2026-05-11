# MCT-132 Compactor stabilize Implementation Plan (Epic-A: Phase 0 + Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-compactor 컨테이너의 메모리 폭주를 (a) 즉시 cap (32G) + 런타임 tune 으로 stabilize 하고, (b) tracemalloc + Prometheus metric 으로 가시성을 확보해 Epic-B (v2 재설계) 진단 근거를 마련한다.

**Architecture:** 단일 프로세스 compactor (`mctrader_data.compactor.runner.CompactorRunner`) 가 L1/L2/L3 compaction 을 순차 처리하는 구조 유지. 변경 1: compose 레벨 cgroup mem_limit + Python runtime env. 변경 2: compactor 의 `/metrics` HTTP endpoint 신설 (현재 부재) + tracemalloc snapshot 스크립트. 변경 3: l1/l2/l3 ParquetWriter close audit.

**Tech Stack:** Python 3.12 / asyncio / PyArrow / `prometheus_client` (HTTP exporter 모드) / Docker compose v2 / tracemalloc 표준 모듈.

**Spec**: [`docs/superpowers/specs/2026-05-11-compactor-memory-fix-design.md`](../specs/2026-05-11-compactor-memory-fix-design.md) §2 Epic-A.

**Affected repos:**
- `c:\workspace\mclayer\mctrader-hub` — compose.yml 위치 (hub orchestrator 가 아닌 data 자체 compose.yml 임에 주의 — 실제 위치는 mctrader-data 의 compose.yml), prometheus.yml, Grafana dashboard, tracemalloc 스크립트
- `c:\workspace\mclayer\mctrader-data` — compactor 코드, metrics 모듈, 테스트

---

## File Structure

### mctrader-data (코드 변경)

| File | Action | Responsibility |
|---|---|---|
| `src/mctrader_data/compactor/runner.py` | Modify | `_tick()` 종료 시 정기 `gc.collect()` 호출 (interval-driven) |
| `src/mctrader_data/compactor/l1.py` | Modify | ParquetWriter `try/finally` close audit |
| `src/mctrader_data/compactor/l2.py` | Modify | ParquetWriter `try/finally` close audit |
| `src/mctrader_data/compactor/l3.py` | Modify | ParquetWriter `try/finally` close audit |
| `src/mctrader_data/compactor/__init__.py` | Modify | (필요 시) entry export |
| `src/mctrader_data/compactor/metrics_server.py` | Create | HTTP `/metrics` server + memory observer thread (pyarrow_total, gc gens, writer_open, accumulator estimate, pending segments) |
| `src/mctrader_data/metrics.py` | Modify | 신규 metric 4종 추가 (`compactor_pyarrow_total_allocated_bytes`, `compactor_python_gc_gen_count`, `compactor_tier_accumulator_bytes`, `compactor_tier_pending_segments`, `compactor_writer_open_count`) |
| `src/mctrader_data/cli.py` 또는 compact entrypoint | Modify | compact 명령 시작 시 `metrics_server.start(port=8080)` 호출 |
| `tests/compactor/test_metrics_server.py` | Create | TDD: `/metrics` 응답 형식 + 4 metric 존재 검증 |
| `tests/compactor/test_runner_gc_interval.py` | Create | TDD: `gc.collect()` 가 interval 기준 호출되는지 (clock mock) |
| `tests/compactor/test_l1_writer_close.py` | Create | TDD: ParquetWriter 예외 시 close() 호출 확인 |
| `tests/compactor/test_l2_writer_close.py` | Create | 동일 |
| `tests/compactor/test_l3_writer_close.py` | Create | 동일 |

### mctrader-hub (infra / 관측)

| File | Action | Responsibility |
|---|---|---|
| `c:\workspace\mclayer\mctrader-data\compose.yml` | Modify | `compactor` 서비스: `mem_limit: 32g` + 환경변수 (MALLOC_TRIM_THRESHOLD_, ARROW_DEFAULT_MEMORY_POOL, MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS) + ports `8080:8080` |
| `c:\workspace\mclayer\mctrader-hub\monitoring\prometheus.yml` | Verify | 기존 `mctrader-data-compactor` scrape job 이 `mctrader-compactor:8080` 가리키는지 확인 (이미 존재) |
| `c:\workspace\mclayer\mctrader-hub\monitoring\grafana\provisioning\dashboards\compactor.json` | Create | Grafana dashboard JSON — 5 패널 |
| `c:\workspace\mclayer\mctrader-hub\tools\compactor-tracemalloc.py` | Create | `docker exec` 로 attach 가능한 tracemalloc snapshot 스크립트 (12h × 10min interval) |
| `c:\workspace\mclayer\mctrader-hub\docs\runbooks\compactor-baseline.md` | Create | baseline 캡처 + before/after 비교 절차 runbook |
| `c:\workspace\mclayer\mctrader-hub\CLAUDE.md` | Modify | "Compactor 운영" / "Compactor 관측" 섹션 추가 |

---

## Phase 0 — 관측 인프라 1차 (Sequential, MCT-134 A2 part-1)

### Task 1: tracemalloc snapshot 스크립트

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\tools\compactor-tracemalloc.py`
- Test: 수동 검증 (단발 스크립트, 단위 테스트 대상 아님)

이 task 는 운영 도구 — TDD 패턴 대신 빈 docker container 에서 dry-run 으로 검증.

- [ ] **Step 1: 스크립트 작성**

```python
# c:\workspace\mclayer\mctrader-hub\tools\compactor-tracemalloc.py
"""Compactor tracemalloc snapshot collector.

Usage:
    # baseline (A1 적용 전):
    python tools/compactor-tracemalloc.py --duration-hours 12 --interval-min 10 --out /var/log/compactor-tracemalloc/baseline

    # after A1:
    python tools/compactor-tracemalloc.py --duration-hours 12 --interval-min 10 --out /var/log/compactor-tracemalloc/after-a1
"""
from __future__ import annotations

import argparse
import os
import pickle
import signal
import sys
import time
import tracemalloc
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-hours", type=float, default=12.0)
    parser.add_argument("--interval-min", type=float, default=10.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    tracemalloc.start(25)  # 25 frames per traceback

    end = time.time() + args.duration_hours * 3600
    interval = args.interval_min * 60
    n = 0
    prev_snapshot = None

    def _stop(signum, frame):
        print(f"[tracemalloc] signal {signum} received, stopping", file=sys.stderr)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    while time.time() < end:
        snap = tracemalloc.take_snapshot()
        ts = int(time.time())
        out_path = args.out / f"snap-{ts}.pkl"
        with out_path.open("wb") as f:
            pickle.dump(snap, f)

        top_stats = snap.statistics("lineno")[: args.top]
        print(f"\n[tracemalloc] snapshot {n} ts={ts} top {args.top}:")
        for stat in top_stats:
            print(f"  {stat}")

        if prev_snapshot is not None:
            diff = snap.compare_to(prev_snapshot, "lineno")[: args.top]
            print(f"[tracemalloc] diff vs prev top {args.top}:")
            for stat in diff:
                print(f"  {stat}")

        prev_snapshot = snap
        n += 1
        time.sleep(interval)

    print(f"[tracemalloc] completed {n} snapshots → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 스크립트 dry-run 검증**

Run (host shell, mctrader-hub 디렉터리):

```
python tools\compactor-tracemalloc.py --duration-hours 0.02 --interval-min 0.5 --out /tmp/tracemalloc-dryrun
```

Expected: 약 1분 후 종료, `/tmp/tracemalloc-dryrun/` 에 2-3 개 `snap-*.pkl` 생성, stdout 에 top 25 출력.

- [ ] **Step 3: 컨테이너 내부 실행 절차 검증 (실제 attach 는 Task 9 에서)**

이 task 에서는 스크립트 단독 동작만 확인 — compactor 컨테이너 attach 는 Task 3 baseline 캡처 시.

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-hub
git add tools/compactor-tracemalloc.py
git commit -m "feat(mct-134): add tracemalloc snapshot collector for compactor baseline"
```

---

### Task 2: compactor `/metrics` HTTP server bootstrap (Phase 0 핵심)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\metrics_server.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\metrics.py` (단일 RSS gauge 추가만 — 나머지 metric 은 Task 7)
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\cli.py` (compact 명령에 metrics_server.start 호출)
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_metrics_server.py`

- [ ] **Step 1: Write the failing test**

```python
# c:\workspace\mclayer\mctrader-data\tests\compactor\test_metrics_server.py
from __future__ import annotations

import urllib.request

import pytest

from mctrader_data.compactor.metrics_server import start_metrics_server, stop_metrics_server


@pytest.fixture
def metrics_port(unused_tcp_port):
    start_metrics_server(port=unused_tcp_port)
    yield unused_tcp_port
    stop_metrics_server()


def test_metrics_endpoint_responds_200(metrics_port):
    resp = urllib.request.urlopen(f"http://127.0.0.1:{metrics_port}/metrics", timeout=2)
    assert resp.status == 200
    body = resp.read().decode("utf-8")
    assert "compactor_process_rss_bytes" in body


def test_rss_gauge_is_positive(metrics_port):
    resp = urllib.request.urlopen(f"http://127.0.0.1:{metrics_port}/metrics", timeout=2)
    body = resp.read().decode("utf-8")
    rss_lines = [l for l in body.splitlines() if l.startswith("compactor_process_rss_bytes ")]
    assert len(rss_lines) == 1
    value = float(rss_lines[0].split()[1])
    assert value > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
cd c:\workspace\mclayer\mctrader-data
pytest tests/compactor/test_metrics_server.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'mctrader_data.compactor.metrics_server'`.

- [ ] **Step 3: 신규 metric 1개 추가 (Phase 0 minimal)**

Edit `c:\workspace\mclayer\mctrader-data\src\mctrader_data\metrics.py` — 파일 끝에 추가:

```python
compactor_process_rss_bytes = Gauge(
    "compactor_process_rss_bytes",
    "Compactor process resident set size (RSS) in bytes",
)


def observe_compactor_rss() -> None:
    """Sample current RSS via /proc/self/status. Called by metrics_server observer thread."""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    compactor_process_rss_bytes.set(kb * 1024)
                    return
    except FileNotFoundError:
        # macOS/Windows fallback — psutil 도입 검토는 Task 7
        import resource
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        compactor_process_rss_bytes.set(rss_kb * 1024)
```

- [ ] **Step 4: Implement `metrics_server.py`**

Create `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\metrics_server.py`:

```python
"""Compactor /metrics HTTP server + observer thread."""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from prometheus_client import start_http_server

from mctrader_data.metrics import observe_compactor_rss

log = logging.getLogger(__name__)

_OBSERVER_INTERVAL_SECONDS = 5.0
_observer_thread: Optional[threading.Thread] = None
_observer_stop = threading.Event()
_server_started = False


def _observer_loop() -> None:
    while not _observer_stop.is_set():
        try:
            observe_compactor_rss()
        except Exception:
            log.exception("[metrics_server] observer tick error")
        _observer_stop.wait(_OBSERVER_INTERVAL_SECONDS)


def start_metrics_server(port: int = 8080) -> None:
    global _observer_thread, _server_started
    if _server_started:
        log.warning("[metrics_server] already started, skipping")
        return
    start_http_server(port)
    _server_started = True
    _observer_stop.clear()
    _observer_thread = threading.Thread(target=_observer_loop, name="compactor-metrics-observer", daemon=True)
    _observer_thread.start()
    log.info("[metrics_server] started port=%d", port)


def stop_metrics_server() -> None:
    """Test helper. Production process is killed via container stop."""
    global _observer_thread, _server_started
    _observer_stop.set()
    if _observer_thread is not None:
        _observer_thread.join(timeout=3.0)
        _observer_thread = None
    _server_started = False
```

> **Note:** `prometheus_client.start_http_server` 는 daemon thread 로 작동하며 이미 시작된 경우 OSError 가능 — `_server_started` flag 로 idempotent 처리. test 의 `stop_metrics_server` 는 observer 만 정지 (HTTP server 는 daemon 으로 프로세스 종료 시 자동 정리, test 격리는 `unused_tcp_port` 로 처리).

- [ ] **Step 5: Run test to verify it passes**

Run:
```
pytest tests/compactor/test_metrics_server.py -v
```

Expected: PASS — 2 tests.

- [ ] **Step 6: Wire into compact CLI entrypoint**

먼저 cli 의 compact 명령 위치 확인:

```
cd c:\workspace\mclayer\mctrader-data
grep -n "compact" src/mctrader_data/cli.py | head -20
```

Compact 명령 핸들러에 다음 추가 (정확한 위치는 grep 결과로 식별 — `def cmd_compact` 또는 `if args.command == "compact":` 부근):

```python
from mctrader_data.compactor.metrics_server import start_metrics_server

# compact 명령 시작 시:
metrics_port = int(os.environ.get("MCTRADER_COMPACTOR_METRICS_PORT", "8080"))
start_metrics_server(port=metrics_port)
```

- [ ] **Step 7: 컨테이너 build + 1분 smoke test**

```
cd c:\workspace\mclayer\mctrader-data
docker compose build compactor
docker compose up -d compactor
# 30 초 대기 — restart 안 함 확인
docker compose ps compactor
# /metrics 응답 확인 — 다른 컨테이너 또는 host 에서:
curl http://localhost:8080/metrics 2>&1 | grep compactor_process_rss_bytes
```

Expected: `compactor_process_rss_bytes <positive_number>` 한 줄 출력. ports expose 는 Task 3 에서 compose.yml 변경 후 — 그 전까지 `docker exec mctrader-compactor curl http://127.0.0.1:8080/metrics` 사용.

- [ ] **Step 8: Commit**

```bash
cd c:\workspace\mclayer\mctrader-data
git add src/mctrader_data/compactor/metrics_server.py src/mctrader_data/metrics.py src/mctrader_data/cli.py tests/compactor/test_metrics_server.py
git commit -m "feat(mct-134): bootstrap compactor /metrics HTTP endpoint with RSS gauge"
```

---

### Task 3: compose.yml ports expose + baseline 캡처 1회

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\compose.yml`
- Create: `c:\workspace\mclayer\mctrader-hub\docs\runbooks\compactor-baseline.md`

이 task 의 출력물 (baseline tracemalloc dump + RSS metric) 이 Phase 1 효과 검증의 SSOT.

- [ ] **Step 1: compose.yml `compactor` 서비스에 port expose 추가**

Edit `c:\workspace\mclayer\mctrader-data\compose.yml` — `compactor` 서비스의 `volumes:` 위에 `ports:` 추가:

```yaml
  compactor:
    build: .
    image: mctrader-data:pilot
    container_name: mctrader-compactor
    restart: unless-stopped
    stop_grace_period: 30s
    command:
      - "compact"
      - "--root"
      - "/var/lib/mctrader/data"
      - "--log-level"
      - "INFO"
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      PYTHONUNBUFFERED: "1"
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
    ports:
      - "8080:8080"
    volumes:
      - mctrader_data:/var/lib/mctrader/data
    ...
```

- [ ] **Step 2: runbook 작성**

Create `c:\workspace\mclayer\mctrader-hub\docs\runbooks\compactor-baseline.md`:

```markdown
# Compactor baseline 캡처 runbook (MCT-134)

## 목적
Phase 0 — A1 stabilize 적용 전 / 후 비교 baseline 확보.

## 절차 (baseline = A1 적용 전)

1. compactor 컨테이너에 tracemalloc 스크립트 attach:
   ```
   docker cp tools/compactor-tracemalloc.py mctrader-compactor:/tmp/tracemalloc.py
   docker exec -d mctrader-compactor python /tmp/tracemalloc.py \
       --duration-hours 12 --interval-min 10 \
       --out /var/lib/mctrader/data/_tracemalloc/baseline
   ```

2. Prometheus 에서 12 시간 동안 다음 query 시계열 저장:
   - `compactor_process_rss_bytes{container="mctrader-compactor"}`
   - `rate(container_cpu_usage_seconds_total{name="mctrader-compactor"}[5m])`

3. 12 시간 후 tracemalloc dump 회수:
   ```
   docker cp mctrader-compactor:/var/lib/mctrader/data/_tracemalloc/baseline \
       ./baseline-2026-05-11
   ```

4. 결과 1줄 보고 (`docs/runbooks/compactor-baseline-results-YYYY-MM-DD.md`):
   - peak RSS bytes
   - 마지막 RSS bytes
   - 12h 동안 증가량
   - top 5 tracemalloc allocator (마지막 snapshot)

## A1 적용 후 (Task 9 에서 사용)

위 절차 동일하나 `--out /var/lib/mctrader/data/_tracemalloc/after-a1`. 비교 보고서: `docs/runbooks/compactor-a1-effect-YYYY-MM-DD.md`.
```

- [ ] **Step 3: compose up + baseline 캡처 시작**

```
cd c:\workspace\mclayer\mctrader-data
docker compose up -d compactor
# /metrics scrape 확인 — Prometheus UI 에서 compactor_process_rss_bytes 시계열 존재 확인 (1-2분 대기)

# baseline 캡처 시작 (백그라운드, 12시간):
docker cp ../mctrader-hub/tools/compactor-tracemalloc.py mctrader-compactor:/tmp/tracemalloc.py
docker exec -d mctrader-compactor python /tmp/tracemalloc.py \
    --duration-hours 12 --interval-min 10 \
    --out /var/lib/mctrader/data/_tracemalloc/baseline
```

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-data
git add compose.yml
git commit -m "chore(mct-134): expose compactor :8080 metrics port"
cd ..\mctrader-hub
git add docs/runbooks/compactor-baseline.md
git commit -m "docs(mct-134): compactor baseline capture runbook"
```

- [ ] **Step 5: Phase 0 종료 조건**

baseline 캡처는 백그라운드 12시간 진행. **Phase 1 진입은 baseline 캡처 완료 대기 없이 즉시 가능** (병렬 작업). 단 Task 9 의 비교 보고는 baseline 회수 후.

---

## Phase 1 — Stabilize + 관측 인프라 완성 (Parallel)

**병렬 분기**:
- 분기 α (MCT-133 A1): Task 4, 5, 6 — compose 변경 + Python 코드 close audit + gc interval
- 분기 β (MCT-134 A2 part-2): Task 7, 8, 9 — metric 추가 + Grafana + 효과 비교

**Path-disjoint 확인**:
- α 의 코드 수정: `compose.yml`, `compactor/{l1,l2,l3,runner}.py`
- β 의 코드 수정: `metrics.py`, `metrics_server.py`, `monitoring/grafana/...json`
- 충돌 없음 — 병렬 실행 가능.

---

### Task 4 (α): compose.yml mem_limit + 런타임 env vars (MCT-133 A1)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\compose.yml`

- [ ] **Step 1: compose.yml `compactor` 서비스 수정**

Edit — `compactor` 서비스의 `environment:` 블록 + `mem_limit` 추가:

```yaml
  compactor:
    build: .
    image: mctrader-data:pilot
    container_name: mctrader-compactor
    restart: unless-stopped
    stop_grace_period: 30s
    mem_limit: 32g
    memswap_limit: 32g
    command:
      - "compact"
      - "--root"
      - "/var/lib/mctrader/data"
      - "--log-level"
      - "INFO"
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      PYTHONUNBUFFERED: "1"
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      MCTRADER_COMPACTOR_METRICS_PORT: "8080"
      MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS: "300"
      MALLOC_TRIM_THRESHOLD_: "131072"
      ARROW_DEFAULT_MEMORY_POOL: "system"
    ports:
      - "8080:8080"
    volumes:
      - mctrader_data:/var/lib/mctrader/data
```

> `MALLOC_TRIM_THRESHOLD_=131072` (128KB) — glibc malloc 이 free 후 OS 반환 trigger 임계.
> `ARROW_DEFAULT_MEMORY_POOL=system` — PyArrow jemalloc → glibc 전환, RSS 추적성 ↑.
> `memswap_limit = mem_limit` — swap 사용 금지 (swap thrash 가 진단 노이즈).

- [ ] **Step 2: compose config 검증**

```
cd c:\workspace\mclayer\mctrader-data
docker compose config | findstr -i "mem_limit\|MALLOC\|ARROW"
```

Expected: `mem_limit: 34359738368` (32G in bytes), `MALLOC_TRIM_THRESHOLD_: "131072"`, `ARROW_DEFAULT_MEMORY_POOL: system` 모두 출력.

- [ ] **Step 3: Restart compactor with new limits**

```
docker compose up -d compactor
sleep 30
docker stats --no-stream mctrader-compactor
```

Expected: MEM USAGE 의 LIMIT 컬럼이 `32GiB` 표시.

- [ ] **Step 4: Commit**

```bash
git add compose.yml
git commit -m "feat(mct-133): apply 32G mem_limit + glibc/arrow runtime tune to compactor"
```

---

### Task 5 (α): ParquetWriter close audit — L1 (MCT-133 A1)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l1.py`
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_l1_writer_close.py`

먼저 l1.py 의 현재 ParquetWriter 사용 구조 확인.

- [ ] **Step 1: l1.py 의 ParquetWriter 사용 위치 확인**

```
cd c:\workspace\mclayer\mctrader-data
grep -n "ParquetWriter\|pq.write_table\|write_to_dataset" src/mctrader_data/compactor/l1.py
```

이 결과로 audit 대상 호출 지점 식별. ParquetWriter 인스턴스가 명시적으로 만들어진다면 `try/finally` 또는 `with` context manager 로 close 보장. `pq.write_table` (단일 호출) 만 사용한다면 PyArrow 가 내부 close — 변경 불필요.

- [ ] **Step 2: Write failing test (close on exception)**

```python
# c:\workspace\mclayer\mctrader-data\tests\compactor\test_l1_writer_close.py
"""Verify L1Compactor closes ParquetWriter on exception path."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mctrader_data.compactor.l1 import L1Compactor


def test_l1_closes_writer_on_exception(tmp_path: Path) -> None:
    """If writer.write_table raises, writer.close() must still be called."""
    sealed = tmp_path / "wal" / "bithumb" / "transactions" / "KRW-BTC" / "2026-05-11"
    sealed.mkdir(parents=True)
    seg = sealed / "segment-1715424000-NODE.ndjson.sealed"
    seg.write_text('{"exchange":"bithumb","symbol":"KRW-BTC","channel":"transactions","timestamp":1,"price":1,"qty":1}\n')

    compactor = L1Compactor(root=tmp_path)

    fake_writer = MagicMock()
    fake_writer.write_table.side_effect = RuntimeError("boom")

    with patch("mctrader_data.compactor.l1.pq.ParquetWriter", return_value=fake_writer):
        with pytest.raises(RuntimeError, match="boom"):
            compactor.compact_segment(seg)

    fake_writer.close.assert_called_once()
```

> Note: 만약 l1.py 가 `ParquetWriter` 가 아닌 `pq.write_table` 만 쓴다면 이 test 는 적용 불가. Step 1 의 grep 결과로 분기.
>  - `ParquetWriter` 직접 사용: 이 test 진행
>  - `pq.write_table` 단일 호출: test 를 `pq.write_table` mock 으로 변환하되, "exception 시 tmp 파일 정리" 를 검증 (assert tmp 파일 삭제됨)

- [ ] **Step 3: Run test to verify it fails**

```
pytest tests/compactor/test_l1_writer_close.py -v
```

Expected: FAIL — `fake_writer.close` 가 호출되지 않거나, 현재 코드가 ParquetWriter 미사용이면 patch 실패.

- [ ] **Step 4: l1.py 의 ParquetWriter 경로를 try/finally 로 wrap**

`l1.py` 의 ParquetWriter 사용 블록을 다음 패턴으로:

```python
writer = pq.ParquetWriter(tmp_path, table.schema, ...)
try:
    writer.write_table(table)
finally:
    writer.close()
```

또는 context manager:

```python
with pq.ParquetWriter(tmp_path, table.schema, ...) as writer:
    writer.write_table(table)
```

(PyArrow ParquetWriter 는 `__enter__/__exit__` 지원.)

추가: `try/except` 로 exception 발생 시 `tmp_path` 정리 + lineage 미기록:

```python
try:
    with pq.ParquetWriter(tmp_path, table.schema, ...) as writer:
        writer.write_table(table)
    os.replace(tmp_path, final_path)  # atomic rename
    _write_lineage(final_path, sources, sha)
except Exception:
    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except OSError:
            log.exception("[l1] tmp cleanup failed %s", tmp_path)
    raise
```

- [ ] **Step 5: Run test to verify it passes**

```
pytest tests/compactor/test_l1_writer_close.py -v
```

Expected: PASS.

- [ ] **Step 6: 기존 테스트 회귀 확인**

```
pytest tests/compactor/ -v
```

Expected: 기존 `test_minio_uploader.py`, `test_runner_minio.py` PASS 유지 + 신규 PASS.

- [ ] **Step 7: Commit**

```bash
git add src/mctrader_data/compactor/l1.py tests/compactor/test_l1_writer_close.py
git commit -m "fix(mct-133): L1Compactor — try/finally close ParquetWriter + tmp cleanup on exception"
```

---

### Task 6 (α): ParquetWriter close audit — L2, L3 + gc.collect interval

이 task 는 Task 5 와 동일 패턴을 L2 / L3 에 반복 + runner.py 의 gc.collect interval.

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l2.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l3.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\runner.py`
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_l2_writer_close.py`
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_l3_writer_close.py`
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_runner_gc_interval.py`

- [ ] **Step 1: L2 — Task 5 와 동일 패턴**

`test_l2_writer_close.py` 작성 → run-fail → l2.py 수정 → run-pass → commit.

테스트 코드 패턴 (l1 와 동일, mock target 만 변경):

```python
# c:\workspace\mclayer\mctrader-data\tests\compactor\test_l2_writer_close.py
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mctrader_data.compactor.l2 import L2Compactor


def test_l2_closes_writer_on_exception(tmp_path: Path) -> None:
    """L2 compaction must close ParquetWriter even on exception."""
    # arrange — minimal L1 input
    l1_dir = tmp_path / "market" / "transactions" / "schema_version=ohlcv.v1" / "tier=L1" / "exchange=bithumb" / "symbol=KRW-BTC" / "date=2026-05-11" / "node=DEFAULT"
    l1_dir.mkdir(parents=True)
    (l1_dir / "part-x.parquet").write_bytes(b"\x00")  # dummy

    compactor = L2Compactor(tmp_path)

    fake_writer = MagicMock()
    fake_writer.__enter__ = MagicMock(return_value=fake_writer)
    fake_writer.__exit__ = MagicMock(return_value=False)
    fake_writer.write_table.side_effect = RuntimeError("boom")

    with patch("mctrader_data.compactor.l2.pq.ParquetWriter", return_value=fake_writer):
        with pytest.raises(RuntimeError, match="boom"):
            from datetime import datetime, timezone
            compactor.compact_hour(
                exchange="bithumb", symbol="KRW-BTC", channel="transactions",
                hour_utc=datetime(2026, 5, 11, 0, tzinfo=timezone.utc),
            )

    # __exit__ 가 호출되었음 → context manager close 보장
    fake_writer.__exit__.assert_called()
```

코드 수정: Task 5 와 동일 (try/finally 또는 `with`).

```bash
git add src/mctrader_data/compactor/l2.py tests/compactor/test_l2_writer_close.py
git commit -m "fix(mct-133): L2Compactor — try/finally close ParquetWriter"
```

- [ ] **Step 2: L3 — 동일 패턴**

`test_l3_writer_close.py` 동일 구조 (L2 → L3 으로 mock target / 호출 method 변경). l3.py 수정.

```bash
git add src/mctrader_data/compactor/l3.py tests/compactor/test_l3_writer_close.py
git commit -m "fix(mct-133): L3Compactor — try/finally close ParquetWriter"
```

- [ ] **Step 3: runner.py gc.collect interval — Write failing test**

```python
# c:\workspace\mclayer\mctrader-data\tests\compactor\test_runner_gc_interval.py
from __future__ import annotations

import asyncio
import gc as _gc
from pathlib import Path
from unittest.mock import patch

import pytest

from mctrader_data.compactor.runner import CompactorRunner


@pytest.mark.asyncio
async def test_gc_collect_called_at_interval(tmp_path: Path, monkeypatch) -> None:
    """`gc.collect()` should be called once per GC interval."""
    monkeypatch.setenv("MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS", "0.1")

    runner = CompactorRunner(root=tmp_path)

    with patch("mctrader_data.compactor.runner.gc.collect") as mock_collect:
        # 2 tick — interval 0.1s 이므로 2번째 tick 시 gc.collect 1회 호출
        await runner._tick()
        await asyncio.sleep(0.15)
        await runner._tick()

    assert mock_collect.call_count >= 1
```

- [ ] **Step 4: Run test to verify it fails**

```
pytest tests/compactor/test_runner_gc_interval.py -v
```

Expected: FAIL — `gc.collect` 가 호출되지 않음 (현재 runner.py 에 gc.collect 미존재).

- [ ] **Step 5: runner.py 수정 — gc.collect interval**

`c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\runner.py`:

```python
import gc
import os
import time

# 파일 상단 import 영역에 추가:

class CompactorRunner:
    def __init__(self, root: Path, minio_uploader=None) -> None:
        # 기존 ...
        self._last_gc = 0.0
        self._gc_interval_seconds = float(
            os.environ.get("MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS", "300")
        )

    async def _tick(self) -> None:
        now = time.time()

        # ... 기존 L1/L2/L3 처리 ...

        # gc.collect interval-driven
        if now - self._last_gc >= self._gc_interval_seconds:
            self._last_gc = now
            gc.collect()

        run_gc(self._root)  # filesystem GC — 기존 함수, 이름 충돌 주의
```

> **Naming 충돌 주의**: 기존 `from .gc import run_gc` 와 stdlib `gc` 충돌. 해결:
> ```python
> from . import gc as _filesystem_gc
> ...
> _filesystem_gc.run_gc(self._root)
> ```
> 또는 stdlib gc 를 `import gc as _stdlib_gc` 로 alias.

- [ ] **Step 6: Run test to verify it passes**

```
pytest tests/compactor/test_runner_gc_interval.py -v
```

Expected: PASS.

- [ ] **Step 7: 회귀 + Commit**

```
pytest tests/compactor/ -v
```

Expected: 전체 PASS.

```bash
git add src/mctrader_data/compactor/runner.py tests/compactor/test_runner_gc_interval.py
git commit -m "feat(mct-133): runner _tick — interval-driven gc.collect() + filesystem gc alias"
```

- [ ] **Step 8: Restart + 24h smoke**

```
cd c:\workspace\mclayer\mctrader-data
docker compose build compactor
docker compose up -d compactor
```

스모크: 30분 후 `docker stats mctrader-compactor` 확인. mem_limit 32GiB / RSS 비교적 안정 plateau 진입 여부.

---

### Task 7 (β): metrics 모듈 — full metric 추가 (MCT-134 A2 part-2)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\metrics.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\metrics_server.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l1.py` (writer_open Gauge inc/dec)
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l2.py` (동일)
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\l3.py` (동일)
- Test: `c:\workspace\mclayer\mctrader-data\tests\compactor\test_metrics_full.py`

- [ ] **Step 1: Write failing test**

```python
# c:\workspace\mclayer\mctrader-data\tests\compactor\test_metrics_full.py
"""Verify all 5 compactor metrics are exposed via /metrics."""
from __future__ import annotations

import urllib.request

import pytest

from mctrader_data.compactor.metrics_server import start_metrics_server, stop_metrics_server


REQUIRED_METRICS = [
    "compactor_process_rss_bytes",
    "compactor_pyarrow_total_allocated_bytes",
    "compactor_python_gc_gen_count",
    "compactor_tier_pending_segments",
    "compactor_writer_open_count",
]


@pytest.fixture
def metrics_port(unused_tcp_port):
    start_metrics_server(port=unused_tcp_port)
    yield unused_tcp_port
    stop_metrics_server()


def test_all_required_metrics_exposed(metrics_port):
    resp = urllib.request.urlopen(f"http://127.0.0.1:{metrics_port}/metrics", timeout=2)
    body = resp.read().decode("utf-8")
    missing = [m for m in REQUIRED_METRICS if m not in body]
    assert not missing, f"missing metrics: {missing}"
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/compactor/test_metrics_full.py -v
```

Expected: FAIL — 4 metric missing.

- [ ] **Step 3: metrics.py 에 4 metric 추가**

Append to `c:\workspace\mclayer\mctrader-data\src\mctrader_data\metrics.py`:

```python
compactor_pyarrow_total_allocated_bytes = Gauge(
    "compactor_pyarrow_total_allocated_bytes",
    "Bytes allocated by PyArrow default memory pool",
)

compactor_python_gc_gen_count = Gauge(
    "compactor_python_gc_gen_count",
    "Python GC collections count per generation",
    ["generation"],
)

compactor_tier_pending_segments = Gauge(
    "compactor_tier_pending_segments",
    "Pending sealed segments awaiting compaction per tier",
    ["tier"],
)

compactor_writer_open_count = Gauge(
    "compactor_writer_open_count",
    "Currently open ParquetWriter instances per tier",
    ["tier"],
)


def observe_compactor_runtime() -> None:
    """Sample pyarrow + Python gc stats. Called by metrics_server observer thread."""
    try:
        import pyarrow as pa
        pool = pa.default_memory_pool()
        compactor_pyarrow_total_allocated_bytes.set(pool.bytes_allocated())
    except Exception:
        pass

    import gc
    for gen, count in enumerate(gc.get_count()):
        compactor_python_gc_gen_count.labels(generation=str(gen)).set(count)
```

- [ ] **Step 4: metrics_server.py 의 observer 확장**

Edit `metrics_server.py` — `_observer_loop` 에서 `observe_compactor_runtime()` 도 호출:

```python
from mctrader_data.metrics import observe_compactor_rss, observe_compactor_runtime

def _observer_loop() -> None:
    while not _observer_stop.is_set():
        try:
            observe_compactor_rss()
            observe_compactor_runtime()
        except Exception:
            log.exception("[metrics_server] observer tick error")
        _observer_stop.wait(_OBSERVER_INTERVAL_SECONDS)
```

- [ ] **Step 5: L1/L2/L3 에 writer_open Gauge inc/dec 추가**

각 ParquetWriter context manager 진입 / 종료 시:

```python
# l1.py 예시 — Task 5 에서 try/finally 또는 with 로 wrap 했다면 다음 위치에 추가
from mctrader_data.metrics import compactor_writer_open_count

# ParquetWriter 진입:
compactor_writer_open_count.labels(tier="L1").inc()
try:
    with pq.ParquetWriter(...) as writer:
        ...
finally:
    compactor_writer_open_count.labels(tier="L1").dec()
```

L2 → `tier="L2"`, L3 → `tier="L3"`.

- [ ] **Step 6: tier_pending_segments 는 runner.py 에서 업데이트**

Edit `runner.py` `_tick()`:

```python
from mctrader_data.metrics import compactor_tier_pending_segments

async def _tick(self) -> None:
    sealed_list = list(scan_sealed(self._root))
    compactor_tier_pending_segments.labels(tier="L1").set(len(sealed_list))
    # L2 pending: tier=L1 Parquet 수 - 이미 처리된 hour
    # L3 pending: tier=L2 Parquet 수 - 이미 처리된 date
    # 정확한 계산은 복잡 — Phase 0 minimal 은 L1 만 정확, L2/L3 는 _last_*에 대한 stale 표시
    ...
```

> L2/L3 pending 의 정확한 계산은 별도 Story scope. Phase 1 에서는 L1 정확 + L2/L3 stale-seconds (last_processed 와 now 차이) 로 대체. 다음과 같이:

```python
compactor_tier_pending_segments.labels(tier="L1").set(len(sealed_list))
compactor_tier_pending_segments.labels(tier="L2").set(max(0, int((now - self._last_l2) / L2_INTERVAL_SECONDS)))
compactor_tier_pending_segments.labels(tier="L3").set(max(0, int((now - self._last_l3) / L3_INTERVAL_SECONDS)))
```

- [ ] **Step 7: Run test to verify it passes**

```
pytest tests/compactor/test_metrics_full.py -v
pytest tests/compactor/ -v
```

Expected: 신규 PASS + 기존 회귀 없음.

- [ ] **Step 8: Commit**

```bash
git add src/mctrader_data/metrics.py src/mctrader_data/compactor/metrics_server.py src/mctrader_data/compactor/l1.py src/mctrader_data/compactor/l2.py src/mctrader_data/compactor/l3.py src/mctrader_data/compactor/runner.py tests/compactor/test_metrics_full.py
git commit -m "feat(mct-134): expose 5 compactor metrics — pyarrow / gc gens / pending / writer_open"
```

---

### Task 8 (β): Grafana dashboard

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\monitoring\grafana\provisioning\dashboards\compactor.json`
- Verify: `c:\workspace\mclayer\mctrader-hub\monitoring\grafana\provisioning\dashboards\dashboard.yml` 가 폴더 단위 provisioning 인지 확인

- [ ] **Step 1: dashboard.yml 검증**

```
type c:\workspace\mclayer\mctrader-hub\monitoring\grafana\provisioning\dashboards\dashboard.yml
```

Expected: `path: /etc/grafana/provisioning/dashboards` 또는 `path: /var/lib/grafana/dashboards` 등 — 같은 디렉터리의 `.json` 파일을 auto-load 하는지 확인.

- [ ] **Step 2: compactor.json 작성 (5 패널)**

```json
{
  "annotations": {"list": []},
  "editable": true,
  "schemaVersion": 38,
  "tags": ["mctrader", "compactor", "memory"],
  "time": {"from": "now-6h", "to": "now"},
  "title": "Compactor Memory & Throughput",
  "uid": "mctrader-compactor",
  "panels": [
    {
      "type": "timeseries",
      "title": "Process RSS",
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "compactor_process_rss_bytes", "legendFormat": "RSS"}],
      "fieldConfig": {"defaults": {"unit": "bytes"}},
      "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
    },
    {
      "type": "timeseries",
      "title": "PyArrow Allocated",
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [{"expr": "compactor_pyarrow_total_allocated_bytes", "legendFormat": "pyarrow_total"}],
      "fieldConfig": {"defaults": {"unit": "bytes"}},
      "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}
    },
    {
      "type": "timeseries",
      "title": "Python GC Generations",
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [
        {"expr": "compactor_python_gc_gen_count{generation=\"0\"}", "legendFormat": "gen0"},
        {"expr": "compactor_python_gc_gen_count{generation=\"1\"}", "legendFormat": "gen1"},
        {"expr": "compactor_python_gc_gen_count{generation=\"2\"}", "legendFormat": "gen2"}
      ],
      "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8}
    },
    {
      "type": "timeseries",
      "title": "Tier Pending Segments",
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [
        {"expr": "compactor_tier_pending_segments{tier=\"L1\"}", "legendFormat": "L1"},
        {"expr": "compactor_tier_pending_segments{tier=\"L2\"}", "legendFormat": "L2"},
        {"expr": "compactor_tier_pending_segments{tier=\"L3\"}", "legendFormat": "L3"}
      ],
      "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8}
    },
    {
      "type": "timeseries",
      "title": "Open ParquetWriters",
      "datasource": {"type": "prometheus", "uid": "prometheus"},
      "targets": [
        {"expr": "compactor_writer_open_count{tier=\"L1\"}", "legendFormat": "L1"},
        {"expr": "compactor_writer_open_count{tier=\"L2\"}", "legendFormat": "L2"},
        {"expr": "compactor_writer_open_count{tier=\"L3\"}", "legendFormat": "L3"}
      ],
      "gridPos": {"x": 0, "y": 16, "w": 24, "h": 8}
    }
  ]
}
```

- [ ] **Step 3: Grafana provisioning reload**

```
cd c:\workspace\mclayer\mctrader-hub
docker compose restart grafana   # 또는 SIGHUP — provisioning auto-reload 설정에 따라
```

브라우저에서 `http://localhost:3000` (또는 grafana 포트) 접속 → "Compactor Memory & Throughput" dashboard 확인.

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-hub
git add monitoring/grafana/provisioning/dashboards/compactor.json
git commit -m "feat(mct-134): Grafana dashboard — Compactor Memory & Throughput (5 panels)"
```

---

### Task 9 (β): A1 효과 검증 — baseline vs after 비교 보고

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\docs\runbooks\compactor-a1-effect-<YYYY-MM-DD>.md`
- Modify: `c:\workspace\mclayer\mctrader-hub\CLAUDE.md` (Compactor 운영 / 관측 섹션)

이 task 는 Phase 1 의 효과 검증 게이트. Phase 1 land + 24h 운영 후.

- [ ] **Step 1: A1 적용 24h 후 tracemalloc 캡처**

```
docker cp tools/compactor-tracemalloc.py mctrader-compactor:/tmp/tracemalloc.py
docker exec -d mctrader-compactor python /tmp/tracemalloc.py \
    --duration-hours 12 --interval-min 10 \
    --out /var/lib/mctrader/data/_tracemalloc/after-a1
```

12 시간 대기 → 회수:

```
docker cp mctrader-compactor:/var/lib/mctrader/data/_tracemalloc/after-a1 \
    ./after-a1-2026-05-12   # 날짜는 실제 진행일로
```

- [ ] **Step 2: Prometheus query — A1 적용 전후 비교**

```promql
# RSS peak / mean — A1 적용 시점 기준 ±24h
max_over_time(compactor_process_rss_bytes[24h])
avg_over_time(compactor_process_rss_bytes[24h])
```

A1 적용 시점 (mem_limit 변경 commit 시각) 을 기준으로 before / after window 비교.

- [ ] **Step 3: 보고서 작성**

```markdown
# Compactor A1 stabilize 효과 보고 (YYYY-MM-DD)

## 적용 변경
- mem_limit: unlimited → 32G
- MALLOC_TRIM_THRESHOLD_: 128KB
- ARROW_DEFAULT_MEMORY_POOL: system
- MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS: 300
- ParquetWriter try/finally close (L1/L2/L3)

## RSS 변화
| | Before A1 | After A1 | 변화 |
|---|---|---|---|
| Peak (24h) | XX GiB | YY GiB | -Z% |
| Mean (24h) | XX GiB | YY GiB | -Z% |
| Var (24h) | XX | YY | -Z% |

## Tracemalloc top allocator 변화
- Before: ...
- After: ...

## OOM 발생
- Before: N건
- After: 0건 (또는 N건)

## 판정
- [ ] A1 으로 stabilize 충분 → Epic-B 진입 우선순위 낮춤
- [ ] A1 만으로 부족, B1 → B2 진입 필요

## 다음 단계
...
```

- [ ] **Step 4: CLAUDE.md 갱신**

Edit `c:\workspace\mclayer\mctrader-hub\CLAUDE.md` — 적절한 위치에 섹션 추가:

```markdown
## Compactor 운영 (MCT-132)

- mem_limit: 32G (호스트 62.73GiB 의 절반)
- 환경변수: MALLOC_TRIM_THRESHOLD_=131072, ARROW_DEFAULT_MEMORY_POOL=system, MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS=300
- mem_limit 초과 시 restart unless-stopped — A2 metric (compactor_process_rss_bytes) 으로 즉시 감지
- L1/L2/L3 ParquetWriter try/finally close + tmp 파일 정리

## Compactor 관측 (MCT-134)

- `/metrics`: http://mctrader-compactor:8080/metrics (8080 port host expose)
- Prometheus scrape job: `mctrader-data-compactor` (monitoring/prometheus.yml)
- Grafana dashboard: "Compactor Memory & Throughput" (uid: mctrader-compactor)
- 5 metric: process_rss / pyarrow_total / python_gc_gens / tier_pending / writer_open
- Baseline 캡처 runbook: docs/runbooks/compactor-baseline.md
- A1 효과 보고 runbook: docs/runbooks/compactor-a1-effect-*.md
- tracemalloc snapshot: tools/compactor-tracemalloc.py
```

- [ ] **Step 5: Commit**

```bash
cd c:\workspace\mclayer\mctrader-hub
git add docs/runbooks/compactor-a1-effect-*.md CLAUDE.md
git commit -m "docs(mct-134): A1 stabilize 효과 보고 + CLAUDE.md 운영/관측 섹션"
```

---

## Self-Review

### Spec coverage

| Spec 요구 (§2 Epic-A) | Task |
|---|---|
| A1: mem_limit=32g + restart | Task 4 |
| A1: MALLOC_TRIM_THRESHOLD_ + ARROW_DEFAULT_MEMORY_POOL + GC_INTERVAL | Task 4 + Task 6 |
| A1: ParquetWriter close audit (L1/L2/L3) | Task 5 + Task 6 |
| A1: 정기 gc.collect | Task 6 |
| A2 part-1: tracemalloc 스크립트 | Task 1 |
| A2 part-1: 1차 metric counter | Task 2 (RSS gauge) |
| A2 part-2: 5 metric full export | Task 7 |
| A2 part-2: Grafana dashboard | Task 8 |
| A2 part-2: 효과 비교 보고 | Task 9 |

### Placeholder scan

- "L2/L3 pending 의 정확한 계산은 별도 Story scope" — Phase 1 minimal 대체 정의 제공 (last_processed delta). OK.
- "정확한 위치는 grep 결과로 식별" (Task 2 Step 6) — cli.py 의 compact 명령 핸들러 위치 확정은 실행 시점 — OK (구체 명령 제공).
- "make_minimal_table 등" — 단순 fixture 추정 — 실제 fixture 명은 implementer 가 기존 test 파일에서 차용. **수정 필요**: Task 5 의 test 에서 `make_minimal_table` 참조 제거하고 dummy bytes 로 단순화.

### Type consistency

- `start_metrics_server(port: int)` / `stop_metrics_server()` — Task 2 와 Task 7 일치.
- `observe_compactor_rss()` / `observe_compactor_runtime()` — metrics.py 정의와 metrics_server.py 호출 일치.
- `compactor_*` metric 이름 — Task 2, Task 7, Task 8 (Grafana JSON), README 일치 확인 완료.
- `compactor_writer_open_count{tier=...}` — Task 7 inc/dec 와 Task 8 query 일치 (`tier="L1|L2|L3"`).

### Fix applied inline

Task 5 의 Step 2 test 에서 PyArrow Table 생성 라인을 dummy bytes 로 단순화 — 이미 위 코드에서 dummy `b"\x00"` 사용했음. OK.

---

## Out-of-scope (Epic-B 에서 다룸)

- 합성 WAL generator (B1)
- streaming compaction (B2)
- per-tier worker subprocess (B3 조건부)
- ADR-017 amendment + 50/100 sym 회귀 (B4)

별도 plan: `docs/superpowers/plans/2026-05-12-mct135-compactor-v2.md` (Phase 1 완료 + A1 효과 검증 후 작성)
