# Data Collection Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-section Streamlit dashboard for monitoring 50-symbol × 3-tier (candle/orderbook/transaction) data collection continuity, backed by a new `CoverageStatsWriter` in mctrader-data that flushes pre-aggregated stats every 5 minutes.

**Architecture:** mctrader-data gets `CoverageStatsWriter` (`coverage_stats.py`) — an in-memory counter that flushes `coverage-stats.json` every 5 minutes via atomic write (temp → fsync → os.replace), exactly mirroring the existing heartbeat.py pattern. mctrader-web gets `CoverageStatsAdapter` (`coverage_stats_adapter.py`) that reads the JSON file with a 5-min TTL cache, pure helper functions (`data_collection_helpers.py`) for heatmap computation and lag color classification, and `20_data_collection.py` — a new Streamlit page rendering §1 overall KPI summary, §2 collector daemon status, §3 3-tier cross view with heatmap and incident table, §4 tabbed per-tier dashboards.

**Tech Stack:** Python 3.11+, asyncio, dataclasses, Streamlit, Plotly >= 5 (heatmap), Pandas >= 2.2, pytest, pytest-asyncio, unittest.mock

---

## File Map

**mctrader-data** (`c:\workspace\mclayer\mctrader-data\`):
- Create: `src/mctrader_data/coverage_stats.py` — `TierStats`, `GapEvent`, `CoverageStatsWriter`
- Create: `tests/test_coverage_stats.py` — unit tests for coverage_stats.py
- Modify: `src/mctrader_data/collector.py:51-80` — add `coverage_stats_writer` kwarg to `CollectorDaemon.__init__`
- Modify: `src/mctrader_data/collector.py:133-156` — call `coverage_stats_writer.record_event()` in `_handle_event`
- Modify: `src/mctrader_data/collector.py:215-228` — add `coverage_stats_writer` kwarg to `MultiSymbolCollector.__init__`
- Modify: `src/mctrader_data/collector.py:241-306` — spawn/cancel coverage task in `MultiSymbolCollector.run()`
- Modify: `src/mctrader_data/cli.py:510-537` — create `CoverageStatsWriter`, pass to daemons + collector
- Modify: `tests/test_collector.py` — add wiring tests

**mctrader-web** (`c:\workspace\mclayer\mctrader-web\`):
- Create: `src/mctrader_web/dashboard/coverage_stats_adapter.py` — `CoverageStatsResult`, `TierStats`, `GapEvent`, `fetch_coverage_stats()`, TTL cache
- Create: `tests/dashboard/test_coverage_stats_adapter.py` — unit tests
- Create: `src/mctrader_web/dashboard/data_collection_helpers.py` — pure helper functions (no Streamlit)
- Create: `tests/dashboard/test_data_collection_helpers.py` — unit tests
- Create: `src/mctrader_web/dashboard/pages/20_data_collection.py` — 4-section Streamlit page

---

## Task 1: CoverageStatsWriter — dataclasses + `__init__` + `flush()`

**Files:**
- Create: `src/mctrader_data/coverage_stats.py`
- Create: `tests/test_coverage_stats.py`

Working directory for all mctrader-data tasks: `c:\workspace\mclayer\mctrader-data\`

- [ ] **Step 1: Write failing tests**

Create `tests/test_coverage_stats.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mctrader_data.coverage_stats import CoverageStatsWriter


def test_flush_creates_json_with_correct_schema(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(root=tmp_path, node_id="NODE_A", collector_run_id="NODE_A-test")
    writer.flush()
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["schema_version"] == "coverage_stats.v1"
    assert data["node_id"] == "NODE_A"
    assert data["collector_run_id"] == "NODE_A-test"
    assert data["stats"] == {}
    assert "generated_at" in data
    assert data["flush_interval_seconds"] == 300.0


def test_flush_atomic_on_fsync_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def bad_fsync(fd: int) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("os.fsync", bad_fsync)
    writer = CoverageStatsWriter(root=tmp_path, node_id="NODE_A", collector_run_id="test")
    writer.flush()  # must not raise
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    tmp = out.with_suffix(".json.tmp")
    assert not out.exists()   # nothing existed before, last-good = nothing
    assert not tmp.exists()   # tmp cleaned up
```

- [ ] **Step 2: Run to verify failure**

```
cd c:\workspace\mclayer\mctrader-data
pytest tests/test_coverage_stats.py -v
```
Expected: `FAIL` — `ModuleNotFoundError: No module named 'mctrader_data.coverage_stats'`

- [ ] **Step 3: Implement**

Create `src/mctrader_data/coverage_stats.py`:

```python
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

COVERAGE_STATS_VERSION = "coverage_stats.v1"


@dataclass
class GapEvent:
    symbol: str
    tier: str
    start_ts: str
    end_ts: str
    duration_seconds: float
    cause: str
    node_id: str | None
    ws_reconnect_count: int


@dataclass
class TierStats:
    row_count_today: int = 0
    file_count_today: int = 0
    file_size_bytes_today: int = 0
    last_event_ts: str | None = None
    gap_events: list[GapEvent] = field(default_factory=list)


class CoverageStatsWriter:
    FLUSH_INTERVAL_SECONDS: float = 300.0

    def __init__(self, root: Path | str, node_id: str, collector_run_id: str) -> None:
        self._root = Path(root)
        self._node_id = node_id
        self._collector_run_id = collector_run_id
        self._stats: dict[str, dict[str, TierStats]] = {}

    def _tier_stats(self, symbol: str, tier: str) -> TierStats:
        if symbol not in self._stats:
            self._stats[symbol] = {}
        if tier not in self._stats[symbol]:
            self._stats[symbol][tier] = TierStats()
        return self._stats[symbol][tier]

    def flush(self) -> None:
        out_dir = self._root / "market" / "manifest"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "coverage-stats.json"
        tmp_path = out_path.with_suffix(".json.tmp")
        payload = {
            "schema_version": COVERAGE_STATS_VERSION,
            "node_id": self._node_id,
            "collector_run_id": self._collector_run_id,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "flush_interval_seconds": self.FLUSH_INTERVAL_SECONDS,
            "stats": {
                sym: {tier: asdict(ts) for tier, ts in tiers.items()}
                for sym, tiers in self._stats.items()
            },
        }
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, out_path)
        except OSError:
            log.warning("coverage-stats flush failed; last-good file preserved")
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_coverage_stats.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_data/coverage_stats.py tests/test_coverage_stats.py
git commit -m "feat(data): add CoverageStatsWriter skeleton with flush()"
```

---

## Task 2: `record_event()` + `record_gap()`

**Files:**
- Modify: `src/mctrader_data/coverage_stats.py`
- Modify: `tests/test_coverage_stats.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_coverage_stats.py`:

```python
from datetime import datetime, timezone

from mctrader_data.coverage_stats import GapEvent


def test_record_event_increments_row_count(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(tmp_path, "NODE_A", "run-1")
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    writer.record_event("KRW-BTC", "tick", ts, file_size_delta=100)
    writer.record_event("KRW-BTC", "tick", ts, file_size_delta=200)
    writer.flush()
    data = json.loads((tmp_path / "market" / "manifest" / "coverage-stats.json").read_text())
    tier = data["stats"]["KRW-BTC"]["tick"]
    assert tier["row_count_today"] == 2
    assert tier["file_size_bytes_today"] == 300
    assert tier["last_event_ts"] == "2026-05-09T12:00:00Z"


def test_record_event_different_symbols_isolated(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(tmp_path, "NODE_A", "run-1")
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    writer.record_event("KRW-BTC", "tick", ts)
    writer.record_event("KRW-ETH", "tick", ts)
    writer.flush()
    data = json.loads((tmp_path / "market" / "manifest" / "coverage-stats.json").read_text())
    assert data["stats"]["KRW-BTC"]["tick"]["row_count_today"] == 1
    assert data["stats"]["KRW-ETH"]["tick"]["row_count_today"] == 1


def test_record_gap_appends_to_gap_events(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(tmp_path, "NODE_A", "run-1")
    gap = GapEvent(
        symbol="KRW-BTC", tier="tick",
        start_ts="2026-05-09T11:00:00Z", end_ts="2026-05-09T11:05:00Z",
        duration_seconds=300.0, cause="UNKNOWN", node_id="NODE_A", ws_reconnect_count=0,
    )
    writer.record_gap(gap)
    writer.flush()
    data = json.loads((tmp_path / "market" / "manifest" / "coverage-stats.json").read_text())
    gaps = data["stats"]["KRW-BTC"]["tick"]["gap_events"]
    assert len(gaps) == 1
    assert gaps[0]["cause"] == "UNKNOWN"
    assert gaps[0]["duration_seconds"] == 300.0
    assert gaps[0]["symbol"] == "KRW-BTC"
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_coverage_stats.py::test_record_event_increments_row_count -v
```
Expected: `FAIL` — `AttributeError: 'CoverageStatsWriter' object has no attribute 'record_event'`

- [ ] **Step 3: Add `record_event()` and `record_gap()`**

Add after `_tier_stats()` in `src/mctrader_data/coverage_stats.py`:

```python
    def record_event(
        self, symbol: str, tier: str, ts: datetime, file_size_delta: int = 0
    ) -> None:
        stats = self._tier_stats(symbol, tier)
        stats.row_count_today += 1
        stats.file_size_bytes_today += file_size_delta
        stats.last_event_ts = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    def record_gap(self, gap: GapEvent) -> None:
        stats = self._tier_stats(gap.symbol, gap.tier)
        stats.gap_events.append(gap)
```

- [ ] **Step 4: Run all tests**

```
pytest tests/test_coverage_stats.py -v
```
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_data/coverage_stats.py tests/test_coverage_stats.py
git commit -m "feat(data): add record_event() and record_gap() to CoverageStatsWriter"
```

---

## Task 3: `async run()` — 5-minute loop with `CancelledError` → final flush

**Files:**
- Modify: `src/mctrader_data/coverage_stats.py`
- Modify: `tests/test_coverage_stats.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_coverage_stats.py`:

```python
import asyncio

import pytest


@pytest.mark.asyncio
async def test_run_final_flush_on_cancel(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(tmp_path, "NODE_A", "run-1")
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    writer.record_event("KRW-BTC", "tick", ts)
    task = asyncio.create_task(writer.run())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["stats"]["KRW-BTC"]["tick"]["row_count_today"] == 1


@pytest.mark.asyncio
async def test_run_flushes_periodically(tmp_path: Path) -> None:
    writer = CoverageStatsWriter(tmp_path, "NODE_A", "run-1")
    writer.FLUSH_INTERVAL_SECONDS = 0.05
    task = asyncio.create_task(writer.run())
    await asyncio.sleep(0.15)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    assert out.exists()
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_coverage_stats.py::test_run_final_flush_on_cancel -v
```
Expected: `FAIL` — `AttributeError: 'CoverageStatsWriter' object has no attribute 'run'`

- [ ] **Step 3: Add `run()` to `CoverageStatsWriter`**

`asyncio` is already imported at the top. Add after `record_gap()`:

```python
    async def run(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.FLUSH_INTERVAL_SECONDS)
                self.flush()
        except asyncio.CancelledError:
            self.flush()
            raise
```

- [ ] **Step 4: Run all tests**

```
pytest tests/test_coverage_stats.py -v
```
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_data/coverage_stats.py tests/test_coverage_stats.py
git commit -m "feat(data): add async run() loop to CoverageStatsWriter"
```

---

## Task 4: Integrate CoverageStatsWriter into `CollectorDaemon` + `MultiSymbolCollector` + CLI

**Files:**
- Modify: `src/mctrader_data/collector.py`
- Modify: `src/mctrader_data/cli.py`
- Modify: `tests/test_collector.py`

**Context:** `CollectorDaemon._handle_event` (lines 133-157) processes 3 event types, each updating `self._heartbeat_writer`. We mirror each call with `self._coverage_stats_writer.record_event()`. `MultiSymbolCollector.run()` already spawns/cancels `heartbeat_task` (lines 241-301) — we add an identical pattern for `coverage_task`. The CLI's `_amain()` already creates `heartbeat` (lines 511-515) and passes it to daemons (line 529) and collector (line 535) — we do the same for `coverage_writer`.

- [ ] **Step 1: Write failing tests**

Add at the bottom of `tests/test_collector.py`:

```python
# --- CoverageStatsWriter integration tests ---

from unittest.mock import MagicMock


def test_collector_daemon_accepts_coverage_stats_writer(tmp_path: Path) -> None:
    from mctrader_data.coverage_stats import CoverageStatsWriter
    from mctrader_market.types import Symbol

    cov = CoverageStatsWriter(tmp_path, "NODE_A", "test")
    daemon = CollectorDaemon(
        root=tmp_path,
        exchange="bithumb",
        symbol=Symbol.from_string("KRW-BTC"),
        coverage_stats_writer=cov,
    )
    assert daemon._coverage_stats_writer is cov


def test_collector_daemon_calls_record_event_on_transaction(tmp_path: Path) -> None:
    from decimal import Decimal
    from datetime import datetime, timezone
    from mctrader_market.types import Symbol
    from mctrader_market_bithumb.ws_events import TransactionEvent
    from mctrader_data.tick_storage import TickWriter

    cov = MagicMock()
    daemon = CollectorDaemon(
        root=tmp_path,
        exchange="bithumb",
        symbol=Symbol.from_string("KRW-BTC"),
        coverage_stats_writer=cov,
    )
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    daemon._tick_writer = TickWriter(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        snapshot_id="test", node_id="NODE_A", collector_run_id="test",
    )
    event = TransactionEvent(
        exchange="bithumb",
        symbol=Symbol.from_string("KRW-BTC"),
        event_time=ts,
        received_at=ts,
        raw={},
        price=Decimal("100000000"),
        quantity=Decimal("0.001"),
        side="buy",
    )
    daemon._handle_event(event)
    cov.record_event.assert_called_once()
    call_args = cov.record_event.call_args[0]
    assert call_args[0] == "KRW-BTC"
    assert call_args[1] == "tick"


def test_multi_symbol_collector_accepts_coverage_stats_writer(tmp_path: Path) -> None:
    from mctrader_data.coverage_stats import CoverageStatsWriter
    from mctrader_data.collector import MultiSymbolCollector

    cov = CoverageStatsWriter(tmp_path, "NODE_A", "test")
    collector = MultiSymbolCollector(daemons=[], coverage_stats_writer=cov)
    assert collector._coverage_stats_writer is cov
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_collector.py::test_collector_daemon_accepts_coverage_stats_writer -v
```
Expected: `FAIL` — `TypeError: CollectorDaemon.__init__() got an unexpected keyword argument 'coverage_stats_writer'`

- [ ] **Step 3: Modify `CollectorDaemon.__init__` (lines 51-80)**

Add `coverage_stats_writer: object | None = None,` after `heartbeat_writer` kwarg (line 63), and store it:

```python
    def __init__(
        self,
        *,
        root: Path,
        exchange: str,
        symbol: Symbol,
        include_transactions: bool = True,
        include_orderbook: bool = True,
        include_orderbook_snapshot: bool = True,
        snapshot_id: str | None = None,
        node_id: str | None = None,
        collector_run_id: str | None = None,
        heartbeat_writer: object | None = None,
        coverage_stats_writer: object | None = None,
    ) -> None:
        if exchange != "bithumb":
            raise ValueError(f"only 'bithumb' exchange supported in v1, got {exchange!r}")
        self._root = root
        self._exchange = exchange
        self._symbol = symbol
        self._include_transactions = include_transactions
        self._include_orderbook = include_orderbook
        self._include_orderbook_snapshot = include_orderbook_snapshot
        self._snapshot_id = snapshot_id or _default_snapshot_id(exchange, symbol)
        self._node_id = node_id
        self._collector_run_id = collector_run_id
        self._heartbeat_writer = heartbeat_writer
        self._coverage_stats_writer = coverage_stats_writer
        self._tick_writer: TickWriter | None = None
        self._ob_writer: OrderbookWriter | None = None
        self._ob_snapshot_writer: OrderbookSnapshotWriter | None = None
        self._cancel_event = asyncio.Event()
```

- [ ] **Step 4: Modify `CollectorDaemon._handle_event` (lines 133-157)**

Add `coverage_stats_writer.record_event()` calls alongside each existing heartbeat call:

```python
    def _handle_event(self, event) -> None:  # type: ignore[no-untyped-def]
        if isinstance(event, TransactionEvent) and self._tick_writer is not None:
            record = transaction_event_to_record(event)
            self._tick_writer.append(record)
            if self._heartbeat_writer is not None:
                self._heartbeat_writer.update_tier_event_ts(  # type: ignore[attr-defined]
                    "tick", record.ts_utc
                )
            if self._coverage_stats_writer is not None:
                self._coverage_stats_writer.record_event(  # type: ignore[attr-defined]
                    str(self._symbol), "tick", record.ts_utc
                )
        elif isinstance(event, OrderbookSnapshotEvent) and self._ob_snapshot_writer is not None:
            accepted = self._ob_snapshot_writer.append_event(event)
            if accepted and self._heartbeat_writer is not None:
                self._heartbeat_writer.update_tier_event_ts(  # type: ignore[attr-defined]
                    "orderbook_snapshot", event.received_at
                )
            if accepted and self._coverage_stats_writer is not None:
                self._coverage_stats_writer.record_event(  # type: ignore[attr-defined]
                    str(self._symbol), "orderbook", event.received_at
                )
        elif isinstance(event, OrderbookDeltaEvent) and self._ob_writer is not None:
            records = delta_event_to_records(event)
            self._ob_writer.append_many(records)
            if self._heartbeat_writer is not None and records:
                self._heartbeat_writer.update_tier_event_ts(  # type: ignore[attr-defined]
                    "orderbook", records[0].ts_utc
                )
            if self._coverage_stats_writer is not None and records:
                self._coverage_stats_writer.record_event(  # type: ignore[attr-defined]
                    str(self._symbol), "orderbook", records[0].ts_utc
                )
        # TickerEvent ignored — diagnostic only, not persisted
```

- [ ] **Step 5: Modify `MultiSymbolCollector.__init__` (lines 215-228)**

Add `coverage_stats_writer: object | None = None,` after `health_server`, and store it:

```python
    def __init__(
        self,
        daemons: list[CollectorDaemon],
        *,
        manifest: CollectorManifest | None = None,
        manifest_root: Path | None = None,
        heartbeat_writer: object | None = None,
        health_server: object | None = None,
        coverage_stats_writer: object | None = None,
    ) -> None:
        self._daemons = daemons
        self._manifest = manifest
        self._manifest_root = manifest_root
        self._heartbeat_writer = heartbeat_writer
        self._health_server = health_server
        self._coverage_stats_writer = coverage_stats_writer
```

- [ ] **Step 6: Modify `MultiSymbolCollector.run()` — add coverage task spawn + shutdown**

After the existing heartbeat task spawn block (lines 241-251), add:

```python
        # Coverage stats task spawn (mirrors heartbeat_task pattern)
        coverage_task: asyncio.Task[None] | None = None
        if self._coverage_stats_writer is not None:
            coverage_task = asyncio.create_task(
                self._coverage_stats_writer.run()  # type: ignore[attr-defined]
            )
            log.info("[collector] coverage-stats task spawned")
```

In the `finally` block (after line 301 where heartbeat task shuts down), add:

```python
            # Coverage stats graceful shutdown (cancel + final flush)
            if coverage_task is not None:
                coverage_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await coverage_task
                log.info("[collector] coverage-stats task shutdown complete")
```

- [ ] **Step 7: Modify CLI `_amain()` (lines 510-537 in `cli.py`)**

After the `heartbeat = HeartbeatWriter(...)` block (line 515), add:

```python
        from mctrader_data.coverage_stats import CoverageStatsWriter
        coverage_writer = CoverageStatsWriter(
            root=root_resolved,
            node_id=resolved_node_id,
            collector_run_id=run_id,
        )
        log.info("[collector] coverage-stats writer initialized: %s", root_resolved / "market" / "manifest" / "coverage-stats.json")
```

In the `daemons` list comprehension (lines 522-531), add `coverage_stats_writer=coverage_writer,`:

```python
        daemons = [
            CollectorDaemon(
                root=root_resolved, exchange=exchange, symbol=sym,
                include_transactions=include_tx, include_orderbook=include_ob,
                include_orderbook_snapshot=include_ob_snapshot,
                snapshot_id=run_id,
                node_id=resolved_node_id, collector_run_id=run_id,
                heartbeat_writer=heartbeat,
                coverage_stats_writer=coverage_writer,
            )
            for sym in sym_list
        ]
```

In `MultiSymbolCollector(...)` (lines 533-537), add `coverage_stats_writer=coverage_writer,`:

```python
        collector = MultiSymbolCollector(
            daemons, manifest=manifest, manifest_root=root_resolved,
            heartbeat_writer=heartbeat,
            health_server=health,
            coverage_stats_writer=coverage_writer,
        )
```

- [ ] **Step 8: Run all tests**

```
pytest tests/test_collector.py -v
pytest tests/test_coverage_stats.py -v
```
Expected: all PASS (no regressions)

- [ ] **Step 9: Commit**

```bash
git add src/mctrader_data/coverage_stats.py src/mctrader_data/collector.py src/mctrader_data/cli.py tests/test_collector.py
git commit -m "feat(data): wire CoverageStatsWriter into CollectorDaemon + MultiSymbolCollector + CLI"
```

---

## Task 5: `CoverageStatsAdapter` (mctrader-web)

**Files:**
- Create: `src/mctrader_web/dashboard/coverage_stats_adapter.py`
- Create: `tests/dashboard/test_coverage_stats_adapter.py`

Working directory for all mctrader-web tasks: `c:\workspace\mclayer\mctrader-web\`

- [ ] **Step 1: Write failing tests**

Create `tests/dashboard/test_coverage_stats_adapter.py`:

```python
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from mctrader_web.dashboard.coverage_stats_adapter import (
    CoverageStatsResult,
    clear_cache,
    fetch_coverage_stats,
)


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    clear_cache()
    yield
    clear_cache()


def _write_fixture(tmp_path: Path, stats: dict | None = None) -> None:
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "coverage_stats.v1",
        "node_id": "NODE_A",
        "collector_run_id": "test",
        "generated_at": "2026-05-09T00:00:00Z",
        "flush_interval_seconds": 300,
        "stats": stats or {},
    }
    out.write_text(json.dumps(payload))


def test_fetch_returns_result(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    result = fetch_coverage_stats(tmp_path)
    assert not result.is_error
    assert result.node_id == "NODE_A"


def test_fetch_missing_file_is_graceful(tmp_path: Path) -> None:
    result = fetch_coverage_stats(tmp_path)
    assert result.is_error
    assert result.error is not None


def test_ttl_cache_returns_same_object(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    r1 = fetch_coverage_stats(tmp_path)
    r2 = fetch_coverage_stats(tmp_path)
    assert r1 is r2


def test_malformed_json_is_error(tmp_path: Path) -> None:
    out = tmp_path / "market" / "manifest" / "coverage-stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("not valid json {{")
    result = fetch_coverage_stats(tmp_path)
    assert result.is_error


def test_get_gap_events_flattens_all_tiers(tmp_path: Path) -> None:
    stats = {
        "KRW-BTC": {
            "tick": {
                "row_count_today": 1, "file_count_today": 0,
                "file_size_bytes_today": 0, "last_event_ts": "2026-05-09T00:00:00Z",
                "gap_events": [
                    {"symbol": "KRW-BTC", "tier": "tick",
                     "start_ts": "2026-05-09T11:00:00Z", "end_ts": "2026-05-09T11:05:00Z",
                     "duration_seconds": 300.0, "cause": "UNKNOWN",
                     "node_id": "NODE_A", "ws_reconnect_count": 0}
                ],
            },
            "orderbook": {
                "row_count_today": 0, "file_count_today": 0,
                "file_size_bytes_today": 0, "last_event_ts": None, "gap_events": [],
            },
        }
    }
    _write_fixture(tmp_path, stats)
    result = fetch_coverage_stats(tmp_path)
    gaps = result.get_gap_events()
    assert len(gaps) == 1
    assert gaps[0].symbol == "KRW-BTC"
    assert gaps[0].tier == "tick"


def test_coverage_pct_no_gaps_is_100(tmp_path: Path) -> None:
    stats = {
        "KRW-BTC": {
            "tick": {
                "row_count_today": 100, "file_count_today": 1,
                "file_size_bytes_today": 1000, "last_event_ts": "2026-05-09T00:00:00Z",
                "gap_events": [],
            }
        }
    }
    _write_fixture(tmp_path, stats)
    result = fetch_coverage_stats(tmp_path)
    pct = result.coverage_pct("tick", 3600.0)
    assert pct == 100.0


def test_coverage_pct_with_gap(tmp_path: Path) -> None:
    stats = {
        "KRW-BTC": {
            "tick": {
                "row_count_today": 100, "file_count_today": 1,
                "file_size_bytes_today": 1000, "last_event_ts": "2026-05-09T00:00:00Z",
                "gap_events": [
                    {"symbol": "KRW-BTC", "tier": "tick",
                     "start_ts": "2026-05-09T11:00:00Z", "end_ts": "2026-05-09T11:30:00Z",
                     "duration_seconds": 1800.0, "cause": "UNKNOWN",
                     "node_id": "NODE_A", "ws_reconnect_count": 0}
                ],
            }
        }
    }
    _write_fixture(tmp_path, stats)
    result = fetch_coverage_stats(tmp_path)
    # 1 symbol, 3600s window, 1800s gap → 50% covered
    pct = result.coverage_pct("tick", 3600.0)
    assert pct == 50.0
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/dashboard/test_coverage_stats_adapter.py -v
```
Expected: `FAIL` — `ModuleNotFoundError: No module named 'mctrader_web.dashboard.coverage_stats_adapter'`

- [ ] **Step 3: Implement**

Create `src/mctrader_web/dashboard/coverage_stats_adapter.py`:

```python
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_TTL_SECONDS = 300.0
_CACHE: dict[str, CoverageStatsResult] = {}


@dataclass
class GapEvent:
    symbol: str
    tier: str
    start_ts: str
    end_ts: str
    duration_seconds: float
    cause: str
    node_id: str | None
    ws_reconnect_count: int


@dataclass
class TierStats:
    row_count_today: int = 0
    file_count_today: int = 0
    file_size_bytes_today: int = 0
    last_event_ts: str | None = None
    gap_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CoverageStatsResult:
    stats: dict[str, dict[str, TierStats]]
    generated_at: float
    node_id: str | None
    error: str | None
    fetched_at: float

    @property
    def is_error(self) -> bool:
        return self.error is not None

    def get_gap_events(self) -> list[GapEvent]:
        events: list[GapEvent] = []
        for sym_tiers in self.stats.values():
            for ts in sym_tiers.values():
                for g in ts.gap_events:
                    events.append(GapEvent(**g))
        return events

    def coverage_pct(self, tier: str, window_seconds: float) -> float:
        if not self.stats or window_seconds <= 0:
            return 0.0
        total_gap = sum(
            g["duration_seconds"]
            for sym_tiers in self.stats.values()
            for t, ts in sym_tiers.items()
            if t == tier
            for g in ts.gap_events
        )
        total_possible = len(self.stats) * window_seconds
        covered = max(0.0, total_possible - total_gap)
        return min(100.0, covered / total_possible * 100)


def clear_cache() -> None:
    _CACHE.clear()


def fetch_coverage_stats(root: Path | str, *, use_cache: bool = True) -> CoverageStatsResult:
    root = Path(root)
    cache_key = str(root)
    now = time.time()

    if use_cache and cache_key in _CACHE:
        cached = _CACHE[cache_key]
        if now - cached.fetched_at < _TTL_SECONDS:
            return cached

    result = _load(root, fetched_at=now)
    _CACHE[cache_key] = result
    return result


def _load(root: Path, fetched_at: float) -> CoverageStatsResult:
    path = root / "market" / "manifest" / "coverage-stats.json"
    empty = CoverageStatsResult(
        stats={}, generated_at=0.0, node_id=None, error=None, fetched_at=fetched_at
    )

    if not path.exists():
        empty.error = "coverage-stats.json not found"
        return empty

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        empty.error = f"parse error: {e}"
        return empty

    if raw.get("schema_version") != "coverage_stats.v1":
        log.warning("coverage-stats schema mismatch: %s", raw.get("schema_version"))

    stats: dict[str, dict[str, TierStats]] = {}
    for sym, tiers in raw.get("stats", {}).items():
        stats[sym] = {}
        for tier, tsd in tiers.items():
            stats[sym][tier] = TierStats(
                row_count_today=tsd.get("row_count_today", 0),
                file_count_today=tsd.get("file_count_today", 0),
                file_size_bytes_today=tsd.get("file_size_bytes_today", 0),
                last_event_ts=tsd.get("last_event_ts"),
                gap_events=tsd.get("gap_events", []),
            )

    try:
        gen_ts = (
            datetime.fromisoformat(raw["generated_at"].rstrip("Z"))
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
    except (KeyError, ValueError):
        gen_ts = 0.0

    return CoverageStatsResult(
        stats=stats,
        generated_at=gen_ts,
        node_id=raw.get("node_id"),
        error=None,
        fetched_at=fetched_at,
    )
```

- [ ] **Step 4: Run all tests**

```
pytest tests/dashboard/test_coverage_stats_adapter.py -v
```
Expected: 8 PASS

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_web/dashboard/coverage_stats_adapter.py tests/dashboard/test_coverage_stats_adapter.py
git commit -m "feat(web): add CoverageStatsAdapter with TTL cache"
```

---

## Task 6: `data_collection_helpers.py` — pure helper functions

**Files:**
- Create: `src/mctrader_web/dashboard/data_collection_helpers.py`
- Create: `tests/dashboard/test_data_collection_helpers.py`

These helpers contain all computation logic for the dashboard page, making it testable without Streamlit.

- [ ] **Step 1: Write failing tests**

Create `tests/dashboard/test_data_collection_helpers.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mctrader_web.dashboard.data_collection_helpers import (
    build_heatmap_matrix,
    compute_window_seconds,
    heatmap_granularity_seconds,
    lag_color_class,
)
from mctrader_web.dashboard.coverage_stats_adapter import (
    CoverageStatsResult,
    TierStats,
    clear_cache,
    fetch_coverage_stats,
)


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    clear_cache()
    yield
    clear_cache()


# --- heatmap_granularity_seconds ---

def test_granularity_2h_or_less_is_5min() -> None:
    assert heatmap_granularity_seconds(3600) == 300
    assert heatmap_granularity_seconds(7200) == 300


def test_granularity_48h_or_less_is_1h() -> None:
    assert heatmap_granularity_seconds(7201) == 3600
    assert heatmap_granularity_seconds(172800) == 3600


def test_granularity_over_48h_is_6h() -> None:
    assert heatmap_granularity_seconds(172801) == 21600
    assert heatmap_granularity_seconds(604800) == 21600


# --- lag_color_class ---

def test_lag_candle_green() -> None:
    assert lag_color_class(100.0, "candle") == "green"


def test_lag_candle_yellow() -> None:
    assert lag_color_class(120.0, "candle") == "yellow"
    assert lag_color_class(239.9, "candle") == "yellow"


def test_lag_candle_red() -> None:
    assert lag_color_class(240.0, "candle") == "red"


def test_lag_tick_green() -> None:
    assert lag_color_class(30.0, "tick") == "green"


def test_lag_tick_yellow() -> None:
    assert lag_color_class(60.0, "tick") == "yellow"
    assert lag_color_class(299.9, "tick") == "yellow"


def test_lag_tick_red() -> None:
    assert lag_color_class(300.0, "tick") == "red"


def test_lag_orderbook_same_as_tick() -> None:
    assert lag_color_class(50.0, "orderbook") == "green"
    assert lag_color_class(60.0, "orderbook") == "yellow"
    assert lag_color_class(300.0, "orderbook") == "red"


# --- compute_window_seconds ---

def test_compute_window_preset_1h() -> None:
    assert compute_window_seconds("1h") == 3600.0


def test_compute_window_preset_7d() -> None:
    assert compute_window_seconds("7d") == 604800.0


def test_compute_window_today_is_positive() -> None:
    from datetime import datetime, timezone
    now = datetime(2026, 5, 9, 6, 0, 0, tzinfo=timezone.utc)
    w = compute_window_seconds("오늘", now=now)
    assert w == 6 * 3600


# --- build_heatmap_matrix ---

def _make_coverage(
    sym: str, tier: str, gaps: list[dict] | None = None, has_data: bool = True
) -> CoverageStatsResult:
    return CoverageStatsResult(
        stats={
            sym: {
                tier: TierStats(
                    row_count_today=10 if has_data else 0,
                    last_event_ts="2026-05-09T12:00:00Z" if has_data else None,
                    gap_events=gaps or [],
                )
            }
        },
        generated_at=0.0,
        node_id="NODE_A",
        error=None,
        fetched_at=0.0,
    )


def test_heatmap_matrix_no_gap_all_green() -> None:
    cov = _make_coverage("KRW-BTC", "tick")
    import time
    now_ts = 1746792000.0  # 2026-05-09 12:00:00 UTC
    x_labels, y_labels, matrix = build_heatmap_matrix(cov, ["KRW-BTC"], now_ts, 3600.0)
    assert y_labels == ["KRW-BTC"]
    assert all(cell == 0 for cell in matrix[0])


def test_heatmap_matrix_no_data_all_grey() -> None:
    cov = _make_coverage("KRW-BTC", "tick", has_data=False)
    now_ts = 1746792000.0
    x_labels, y_labels, matrix = build_heatmap_matrix(cov, ["KRW-BTC"], now_ts, 3600.0)
    assert all(cell == 3 for cell in matrix[0])


def test_heatmap_matrix_gap_detected() -> None:
    now_ts = 1746792000.0  # 2026-05-09 12:00:00 UTC
    gap_start = now_ts - 1800  # 30 min ago
    gap_end = now_ts - 1200    # 20 min ago
    from datetime import datetime, timezone

    def _ts(t: float) -> str:
        return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    gaps = [{"symbol": "KRW-BTC", "tier": "tick",
             "start_ts": _ts(gap_start), "end_ts": _ts(gap_end),
             "duration_seconds": 600.0, "cause": "UNKNOWN",
             "node_id": "NODE_A", "ws_reconnect_count": 0}]
    cov = _make_coverage("KRW-BTC", "tick", gaps=gaps)
    x_labels, y_labels, matrix = build_heatmap_matrix(cov, ["KRW-BTC"], now_ts, 3600.0)
    # At 5-min granularity, the bucket containing gap_start should be red (2)
    assert 2 in matrix[0]
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/dashboard/test_data_collection_helpers.py -v
```
Expected: `FAIL` — `ModuleNotFoundError: No module named 'mctrader_web.dashboard.data_collection_helpers'`

- [ ] **Step 3: Implement**

Create `src/mctrader_web/dashboard/data_collection_helpers.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mctrader_web.dashboard.coverage_stats_adapter import CoverageStatsResult


def heatmap_granularity_seconds(window_seconds: float) -> int:
    if window_seconds <= 7200:    # ≤ 2h
        return 300
    if window_seconds <= 172800:  # ≤ 48h
        return 3600
    return 21600


def lag_color_class(lag_seconds: float, tier: str) -> str:
    """Return 'green', 'yellow', or 'red' based on tier-specific thresholds."""
    if tier == "candle":
        if lag_seconds < 120:
            return "green"
        if lag_seconds < 240:
            return "yellow"
        return "red"
    # tick and orderbook
    if lag_seconds < 60:
        return "green"
    if lag_seconds < 300:
        return "yellow"
    return "red"


def compute_window_seconds(
    preset: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    now: datetime | None = None,
) -> float:
    _now = now or datetime.now(timezone.utc)
    presets: dict[str, float] = {
        "1h": 3600.0,
        "6h": 21600.0,
        "24h": 86400.0,
        "7d": 604800.0,
    }
    if preset in presets:
        return presets[preset]
    if preset == "오늘":
        start_of_day = datetime(_now.year, _now.month, _now.day, tzinfo=timezone.utc)
        return (_now - start_of_day).total_seconds()
    if preset == "직접 입력" and from_dt is not None and to_dt is not None:
        delta = (to_dt - from_dt).total_seconds()
        return max(300.0, delta)
    return 3600.0


def build_heatmap_matrix(
    coverage: CoverageStatsResult,
    symbols: list[str],
    now_ts: float,
    window_seconds: float,
) -> tuple[list[str], list[str], list[list[int]]]:
    """Return (x_labels, y_labels, matrix) for a Plotly Heatmap.

    Cell values: 0=ok (green), 2=gap (red), 3=miss (grey).
    """
    granularity = heatmap_granularity_seconds(window_seconds)
    start_ts = now_ts - window_seconds
    n_buckets = max(1, int(window_seconds / granularity))
    buckets = [start_ts + i * granularity for i in range(n_buckets)]

    x_labels: list[str] = []
    for b in buckets:
        dt = datetime.fromtimestamp(b, tz=timezone.utc)
        fmt = "%m/%d %H:%M" if window_seconds > 86400 else "%H:%M"
        x_labels.append(dt.strftime(fmt))

    # Flatten gap events indexed by "symbol|tier" for O(1) lookup per bucket
    gap_map: dict[str, list[tuple[float, float]]] = {}
    for gap in coverage.get_gap_events():
        key = f"{gap.symbol}|{gap.tier}"
        try:
            gs = datetime.fromisoformat(gap.start_ts.rstrip("Z")).replace(tzinfo=timezone.utc).timestamp()
            ge = datetime.fromisoformat(gap.end_ts.rstrip("Z")).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
        gap_map.setdefault(key, []).append((gs, ge))

    matrix: list[list[int]] = []
    for sym in symbols:
        sym_stats = coverage.stats.get(sym, {})
        has_data = any(ts.last_event_ts is not None for ts in sym_stats.values())

        row: list[int] = []
        for bucket_start in buckets:
            bucket_end = bucket_start + granularity
            if not has_data:
                row.append(3)
                continue
            cell = 0
            for tier in ("tick", "orderbook", "candle"):
                for gs, ge in gap_map.get(f"{sym}|{tier}", []):
                    if gs < bucket_end and ge > bucket_start:
                        cell = 2
                        break
                if cell == 2:
                    break
            row.append(cell)
        matrix.append(row)

    return x_labels, symbols, matrix
```

- [ ] **Step 4: Run all tests**

```
pytest tests/dashboard/test_data_collection_helpers.py -v
```
Expected: 14 PASS

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_web/dashboard/data_collection_helpers.py tests/dashboard/test_data_collection_helpers.py
git commit -m "feat(web): add data_collection_helpers for heatmap + lag color + window computation"
```

---

## Task 7: `20_data_collection.py` — scaffold + sidebar + §1 Overall Summary

**Files:**
- Create: `src/mctrader_web/dashboard/pages/20_data_collection.py`

No unit tests for the Streamlit page itself — all business logic is in helpers (Task 6) and the adapter (Task 5). Manual verification via `streamlit run`.

- [ ] **Step 1: Create the page scaffold with sidebar and §1**

Create `src/mctrader_web/dashboard/pages/20_data_collection.py`:

```python
"""Data Collection Monitor — 4-section continuity dashboard.

Spec: docs/superpowers/specs/2026-05-09-data-collection-monitor-design.md
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from mctrader_web.dashboard.common import format_ts
from mctrader_web.dashboard.coverage_stats_adapter import (
    CoverageStatsResult,
    clear_cache as clear_coverage_cache,
    fetch_coverage_stats,
)
from mctrader_web.dashboard.data_collection_helpers import (
    compute_window_seconds,
    heatmap_granularity_seconds,
    lag_color_class,
    build_heatmap_matrix,
)
from mctrader_web.dashboard.status_adapter import (
    StatusResult,
    clear_cache as clear_status_cache,
    fetch_status,
)

st.set_page_config(page_title="Data Collection Monitor", page_icon="📡", layout="wide")
st.title("📡 Data Collection Monitor")

_TZ_MAP = {"KST": "Asia/Seoul", "UTC": "UTC"}
_REFRESH_MAP = {"5s": 5, "10s": 10, "30s": 30, "수동": None}


def _default_data_root() -> Path:
    return Path(os.environ.get("MCTRADER_DATA_ROOT", "/mnt/shared/mctrader/data"))


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("⚙ 설정")
    data_root_str = st.text_input(
        "MCTRADER_DATA_ROOT",
        value=str(_default_data_root()),
        help="Heartbeat + coverage-stats JSON root.",
    )
    tz_label = st.selectbox("타임존", ["KST", "UTC"], key="dc_tz")
    tz_name = _TZ_MAP[tz_label]

    refresh_label = st.selectbox("자동 갱신", ["10s", "5s", "30s", "수동"], key="dc_refresh")

    range_preset = st.selectbox(
        "조회 범위",
        ["1h", "6h", "오늘", "24h", "7d", "직접 입력"],
        key="dc_range",
    )
    from_dt: datetime | None = None
    to_dt: datetime | None = None
    if range_preset == "직접 입력":
        import datetime as _dt
        col_a, col_b = st.columns(2)
        with col_a:
            fd = st.date_input("시작 날짜", value=_dt.date.today())
            ft = st.time_input("시작 시간", value=_dt.time(0, 0))
        with col_b:
            td = st.date_input("종료 날짜", value=_dt.date.today())
            tt = st.time_input("종료 시간", value=_dt.time(23, 59))
        from_dt = datetime(fd.year, fd.month, fd.day, ft.hour, ft.minute, tzinfo=ZoneInfo(tz_name))
        to_dt = datetime(td.year, td.month, td.day, tt.hour, tt.minute, tzinfo=ZoneInfo(tz_name))

    if st.button("Force refresh"):
        clear_status_cache()
        clear_coverage_cache()
        st.rerun()

    st.divider()
    st.caption(f"Updated: {datetime.now(ZoneInfo(tz_name)).strftime('%H:%M:%S')} {tz_label}")

data_root = Path(data_root_str)
now_utc = datetime.now(timezone.utc)
window_seconds = compute_window_seconds(range_preset, from_dt=from_dt, to_dt=to_dt, now=now_utc)

# ─── Fetch data ───────────────────────────────────────────────────────────────

status: StatusResult = fetch_status(data_root)
coverage: CoverageStatsResult = fetch_coverage_stats(data_root)

# ─── §1 전체 수집 현황 요약 ───────────────────────────────────────────────────

st.subheader("§1 전체 수집 현황")

_LEVEL_COLOR = {0: "🟢", 1: "🟡", 2: "🔴", 3: "⚪"}
level = status.worst_level if not status.is_error else 3
st.markdown(f"**전체 상태**: {_LEVEL_COLOR[level]} {'GREEN' if level == 0 else 'YELLOW' if level == 1 else 'RED' if level == 2 else 'ERROR'}")

if status.is_error:
    st.error(f"Status adapter error: {status.error}")

# KPI computation
def _node_lag(nodes: list[dict], tier: str) -> float | None:
    lags = []
    for node in nodes:
        ts_str = node.get("last_event_ts_per_tier", {}).get(tier)
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                lags.append((now_utc - ts).total_seconds())
            except ValueError:
                pass
    return sum(lags) / len(lags) if lags else None


nodes = status.nodes if not status.is_error else []
symbols_collecting = len(coverage.stats) if not coverage.is_error else 0
total_gap_seconds = sum(g.duration_seconds for g in coverage.get_gap_events()) if not coverage.is_error else 0.0
total_gap_events = len(coverage.get_gap_events()) if not coverage.is_error else 0
coverage_pct = coverage.coverage_pct("tick", window_seconds) if not coverage.is_error else 0.0
tick_lag = _node_lag(nodes, "tick")
ob_lag = _node_lag(nodes, "orderbook")
events_per_min = sum(
    node.get("metrics", {}).get("events_per_sec", 0.0) * 60
    for node in nodes
)
total_bytes = sum(
    ts.file_size_bytes_today
    for sym_tiers in coverage.stats.values()
    for ts in sym_tiers.values()
) if not coverage.is_error else 0

kpi_cols = st.columns(7)
kpi_cols[0].metric("수집 심볼", f"{symbols_collecting}/50")
kpi_cols[1].metric("24h 커버리지", f"{coverage_pct:.1f}%")
kpi_cols[2].metric("공백 인시던트", f"{total_gap_events}건 / {total_gap_seconds/60:.0f}분")
tick_lag_str = f"{tick_lag:.0f}s" if tick_lag is not None else "—"
ob_lag_str = f"{ob_lag:.0f}s" if ob_lag is not None else "—"
kpi_cols[3].metric("Tick avg lag", tick_lag_str)
kpi_cols[4].metric("OB avg lag", ob_lag_str)
kpi_cols[5].metric("이벤트/분", f"{events_per_min:.0f}")
kpi_cols[6].metric("오늘 저장량", f"{total_bytes / 1_073_741_824:.2f} GB")

st.divider()
```

- [ ] **Step 2: Verify page loads without error**

```
streamlit run src/mctrader_web/dashboard/app.py
```
Navigate to "20 Data Collection" in the sidebar. Expected: §1 section renders without Python errors (data may show zeros/dashes if no collector is running).

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_web/dashboard/pages/20_data_collection.py
git commit -m "feat(web): add 20_data_collection page scaffold + sidebar + §1 KPI summary"
```

---

## Task 8: §2 Collector Daemon Status + §3 Tier Summary Cards

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/20_data_collection.py`

- [ ] **Step 1: Add §2 after the §1 `st.divider()`**

Append to `20_data_collection.py` after the §1 divider:

```python
# ─── §2 수집기 (Collector Daemon) 현황 ───────────────────────────────────────

st.subheader("§2 수집기 현황")

if status.is_error:
    st.error("No active node heartbeats — collector may be offline.")
elif not nodes:
    st.warning("No nodes found in heartbeat status.")
else:
    node_cols = st.columns(len(nodes))
    for i, node in enumerate(nodes):
        with node_cols[i]:
            node_id = node.get("node_id", f"NODE_{i}")
            ws_state = node.get("ws_state", "unknown")
            freshness = node.get("freshness_seconds", 0.0)
            uptime = node.get("uptime_seconds", 0.0)
            metrics = node.get("metrics", {})

            state_icon = "🟢" if ws_state == "connected" else "🔴"
            st.markdown(f"**{node_id}** {state_icon} `{ws_state}`")
            st.caption(f"freshness: {freshness:.0f}s | uptime: {uptime/3600:.1f}h")

            tier_ts = node.get("last_event_ts_per_tier", {})
            for tier_key, tier_label in [("tick", "Tick"), ("orderbook", "OB"), ("candle", "Candle")]:
                ts_str = tier_ts.get(tier_key)
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                        lag = (now_utc - ts).total_seconds()
                        color = lag_color_class(lag, tier_key)
                        icon = "🟢" if color == "green" else "🟡" if color == "yellow" else "🔴"
                        st.caption(f"{icon} {tier_label} lag: {lag:.0f}s")
                    except ValueError:
                        st.caption(f"⚪ {tier_label} lag: —")
                else:
                    st.caption(f"⚪ {tier_label} lag: —")

            st.caption(f"reconnects: {metrics.get('ws_reconnect_count', 0)}")
            st.caption(f"dup_skip: {metrics.get('dup_skip_count', 0)} | quarantine: {metrics.get('quarantine_count', 0)}")
            st.caption(f"events/s: {metrics.get('events_per_sec', 0.0):.1f}")

st.divider()

# ─── §3 전체 데이터 현황 (3-tier 크로스뷰) ─────────────────────────────────────

st.subheader("§3 전체 데이터 현황")

# 3-1. Tier 요약 카드
tier_card_cols = st.columns(3)
tier_defs = [
    ("candle", "📊 Candle", "ohlcv.v1"),
    ("orderbook", "📖 Orderbook", "orderbook.v1"),
    ("tick", "⚡ Transaction", "tick.v1"),
]

for col, (tier_key, tier_label, schema) in zip(tier_card_cols, tier_defs):
    with col:
        st.markdown(f"**{tier_label}**")
        st.caption(f"schema: `{schema}`")

        # Lag from heartbeat
        lag_val = _node_lag(nodes, tier_key)
        if lag_val is not None:
            color = lag_color_class(lag_val, tier_key)
            icon = "🟢" if color == "green" else "🟡" if color == "yellow" else "🔴"
            st.metric("avg lag", f"{icon} {lag_val:.0f}s")
        else:
            st.metric("avg lag", "—")

        if not coverage.is_error:
            pct = coverage.coverage_pct(tier_key, window_seconds)
            tier_gaps = [g for g in coverage.get_gap_events() if g.tier == tier_key]
            total_rows = sum(
                ts.row_count_today
                for sym_tiers in coverage.stats.values()
                for t, ts in sym_tiers.items()
                if t == tier_key
            )
            tier_bytes = sum(
                ts.file_size_bytes_today
                for sym_tiers in coverage.stats.values()
                for t, ts in sym_tiers.items()
                if t == tier_key
            )
            st.metric("커버리지", f"{pct:.1f}%")
            st.metric("공백", f"{len(tier_gaps)}건")
            st.metric("오늘 행 수", f"{total_rows:,}")
            st.metric("오늘 크기", f"{tier_bytes / 1_048_576:.1f} MB")
        else:
            st.caption("coverage-stats 없음 (5분 후 생성)")
```

- [ ] **Step 2: Verify §2 and §3 cards render**

Reload the Streamlit page. Expected: §2 shows node cards (or error banner), §3 shows tier summary cards.

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_web/dashboard/pages/20_data_collection.py
git commit -m "feat(web): add §2 collector daemon status + §3 tier summary cards"
```

---

## Task 9: §3 Heatmap + Incident Table

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/20_data_collection.py`

- [ ] **Step 1: Add heatmap and incident table after the tier cards**

Append to `20_data_collection.py` after the tier summary card loop:

```python
st.divider()

# 3-2. Symbol × Time Heatmap
st.markdown("#### 심볼 × 시간 커버리지 히트맵")

if coverage.is_error:
    st.info("coverage-stats.json 아직 생성 안 됨 — collector 5분 후 자동 생성")
else:
    import plotly.graph_objects as go

    symbols_sorted = sorted(coverage.stats.keys())
    # Issue symbols (any gap) float to top
    syms_with_gaps = {g.symbol for g in coverage.get_gap_events()}
    symbols_display = sorted(syms_with_gaps) + sorted(set(symbols_sorted) - syms_with_gaps)

    x_labels, y_labels, matrix = build_heatmap_matrix(
        coverage, symbols_display, now_utc.timestamp(), window_seconds
    )

    colorscale = [
        [0.0, "#22c55e"],   # green — ok
        [0.34, "#eab308"],  # yellow — warn (not used in matrix but reserved)
        [0.67, "#ef4444"],  # red — gap
        [1.0, "#94a3b8"],   # grey — miss
    ]

    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            zmin=0,
            zmax=3,
            showscale=False,
            hoverongaps=False,
            xgap=1,
            ygap=1,
        )
    )
    fig.update_layout(
        height=max(300, len(symbols_display) * 18 + 80),
        margin=dict(l=100, r=20, t=20, b=60),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# 3-3. 공백 인시던트 테이블
st.markdown("#### 공백 인시던트")

if coverage.is_error:
    st.caption("coverage-stats 없음")
else:
    gaps = coverage.get_gap_events()
    if not gaps:
        st.success("조회 범위 내 공백 인시던트 없음")
    else:
        import pandas as pd

        _tz_info = ZoneInfo(tz_name)

        def _fmt_gap_ts(ts_str: str) -> str:
            try:
                dt = datetime.fromisoformat(ts_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                return dt.astimezone(_tz_info).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return ts_str

        rows = []
        for g in sorted(gaps, key=lambda x: x.start_ts, reverse=True):
            dur_min = g.duration_seconds / 60
            bar = "█" * min(20, max(1, int(dur_min / 5))) + f" {dur_min:.1f}m"
            rows.append({
                "심볼": g.symbol,
                "tier": g.tier,
                f"시작({tz_label})": _fmt_gap_ts(g.start_ts),
                f"종료({tz_label})": _fmt_gap_ts(g.end_ts),
                "공백 기간": bar,
                "원인": g.cause,
                "Node": g.node_id or "—",
                "WS reconn": g.ws_reconnect_count,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
```

- [ ] **Step 2: Verify heatmap and incident table render**

Reload the page. Expected: heatmap renders (empty/all-grey if no collector running), incident table shows or displays "없음".

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_web/dashboard/pages/20_data_collection.py
git commit -m "feat(web): add §3 heatmap + incident table"
```

---

## Task 10: §4 Tabbed Per-Data Dashboards + Polling Loop

**Files:**
- Modify: `src/mctrader_web/dashboard/pages/20_data_collection.py`

- [ ] **Step 1: Add §4 tabbed dashboards + polling loop**

Append to `20_data_collection.py` after the §3 final `st.divider()`:

```python
# ─── §4 데이터별 상세 대시보드 (탭) ──────────────────────────────────────────

st.subheader("§4 데이터별 상세")

tab_candle, tab_ob, tab_tick = st.tabs(["📊 Candle", "📖 Orderbook", "⚡ Transaction"])


def _tier_symbols_stats(tier: str) -> list[tuple[str, object]]:
    """Return [(symbol, TierStats)] for a given tier, sorted by symbol."""
    if coverage.is_error:
        return []
    result = []
    for sym, tiers in sorted(coverage.stats.items()):
        if tier in tiers:
            result.append((sym, tiers[tier]))
    return result


# ── §4-A Candle ────────────────────────────────────────────────────────────────
with tab_candle:
    if coverage.is_error:
        st.info("coverage-stats 없음")
    else:
        cov_syms = _tier_symbols_stats("candle")
        candle_lag = _node_lag(nodes, "candle")
        lag_icon = "—"
        if candle_lag is not None:
            color = lag_color_class(candle_lag, "candle")
            lag_icon = ("🟢" if color == "green" else "🟡" if color == "yellow" else "🔴") + f" {candle_lag:.0f}s"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("avg lag", lag_icon)
        c2.metric("심볼 커버리지", f"{len(cov_syms)}/50")
        total_candle_rows = sum(ts.row_count_today for _, ts in cov_syms)
        total_candle_bytes = sum(ts.file_size_bytes_today for _, ts in cov_syms)
        c3.metric("오늘 행 수", f"{total_candle_rows:,}")
        c4.metric("오늘 크기", f"{total_candle_bytes / 1_048_576:.1f} MB")

        st.caption("Parquet 경로: `market/candles/schema_version=ohlcv.v1/mode=historical/exchange=bithumb/symbol={sym}/date=YYYY-MM-DD/`")

        if cov_syms:
            import pandas as pd
            rows_df = [
                {
                    "심볼": sym,
                    "오늘 행 수": ts.row_count_today,
                    "마지막 이벤트": ts.last_event_ts or "—",
                    "공백 건수": len(ts.gap_events),
                }
                for sym, ts in cov_syms
            ]
            st.dataframe(pd.DataFrame(rows_df), use_container_width=True, hide_index=True)


# ── §4-B Orderbook ────────────────────────────────────────────────────────────
with tab_ob:
    if coverage.is_error:
        st.info("coverage-stats 없음")
    else:
        ob_syms = _tier_symbols_stats("orderbook")
        ob_lag = _node_lag(nodes, "orderbook")
        ob_lag_icon = "—"
        if ob_lag is not None:
            color = lag_color_class(ob_lag, "orderbook")
            ob_lag_icon = ("🟢" if color == "green" else "🟡" if color == "yellow" else "🔴") + f" {ob_lag:.0f}s"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("delta lag", ob_lag_icon)
        c2.metric("심볼 커버리지", f"{len(ob_syms)}/50")
        total_ob_rows = sum(ts.row_count_today for _, ts in ob_syms)
        total_ob_bytes = sum(ts.file_size_bytes_today for _, ts in ob_syms)
        c3.metric("오늘 행 수", f"{total_ob_rows:,}")
        c4.metric("오늘 크기", f"{total_ob_bytes / 1_048_576:.1f} MB")

        st.caption("Parquet 경로: `market/orderbook/schema_version=orderbook.v1/exchange=bithumb/symbol={sym}/date=YYYY-MM-DD/`")

        if ob_syms:
            import pandas as pd
            rows_df = [
                {
                    "심볼": sym,
                    "오늘 행 수": ts.row_count_today,
                    "마지막 이벤트": ts.last_event_ts or "—",
                    "공백 건수": len(ts.gap_events),
                }
                for sym, ts in ob_syms
            ]
            st.dataframe(pd.DataFrame(rows_df), use_container_width=True, hide_index=True)


# ── §4-C Transaction (Tick) ───────────────────────────────────────────────────
with tab_tick:
    if coverage.is_error:
        st.info("coverage-stats 없음")
    else:
        tick_syms = _tier_symbols_stats("tick")
        tick_lag_val = _node_lag(nodes, "tick")
        tick_lag_icon = "—"
        if tick_lag_val is not None:
            color = lag_color_class(tick_lag_val, "tick")
            tick_lag_icon = ("🟢" if color == "green" else "🟡" if color == "yellow" else "🔴") + f" {tick_lag_val:.0f}s"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("lag", tick_lag_icon)
        c2.metric("심볼 커버리지", f"{len(tick_syms)}/50")
        total_tick_rows = sum(ts.row_count_today for _, ts in tick_syms)
        total_tick_bytes = sum(ts.file_size_bytes_today for _, ts in tick_syms)
        c3.metric("오늘 행 수", f"{total_tick_rows:,}")
        c4.metric("오늘 크기", f"{total_tick_bytes / 1_048_576:.1f} MB")

        st.caption("Parquet 경로: `market/ticks/schema_version=tick.v1/exchange=bithumb/symbol={sym}/date=YYYY-MM-DD/`")

        if tick_syms:
            # Quarantine detail from heartbeat
            quarantine_count = sum(node.get("metrics", {}).get("quarantine_count", 0) for node in nodes)
            dup_skip_count = sum(node.get("metrics", {}).get("dup_skip_count", 0) for node in nodes)
            c1.metric("dup_skip (cum)", dup_skip_count)
            c2.metric("quarantine (cum)", quarantine_count)

            import pandas as pd
            rows_df = [
                {
                    "심볼": sym,
                    "오늘 행 수": ts.row_count_today,
                    "마지막 이벤트": ts.last_event_ts or "—",
                    "공백 건수": len(ts.gap_events),
                }
                for sym, ts in tick_syms
            ]
            st.dataframe(pd.DataFrame(rows_df), use_container_width=True, hide_index=True)


# ─── Polling loop ─────────────────────────────────────────────────────────────

interval = _REFRESH_MAP[refresh_label]
if interval is not None:
    time.sleep(interval)
    st.rerun()
```

- [ ] **Step 2: Run all mctrader-web tests to verify no regressions**

```
pytest tests/ -v --tb=short
```
Expected: all previously passing tests still PASS.

- [ ] **Step 3: Verify full page end-to-end in browser**

```
streamlit run src/mctrader_web/dashboard/app.py
```
Check:
- All 4 sections render without exceptions
- §4 tabs switch correctly between Candle / Orderbook / Transaction
- Sidebar settings (tz, refresh, range) update the display
- Force refresh button clears caches

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_web/dashboard/pages/20_data_collection.py
git commit -m "feat(web): add §4 tabbed per-data dashboards + polling loop"
```

---

## Self-Review Notes

**Spec coverage check:**
- §1 Overall summary: ✅ Task 7 (7 KPIs)
- §2 Collector daemon status (node cards + manifest): ✅ Task 8 (node cards + tier lags; manifest display deferred — `list_manifests()` call needed for collector_run_id display; add as v1.1 if desired)
- §3 Tier summary cards: ✅ Task 8
- §3 Heatmap (50 symbols, scrollable, issue symbols floated): ✅ Task 9
- §3 Incident table (start/end/duration bar): ✅ Task 9
- §4 Candle / Orderbook / Transaction tabs: ✅ Task 10
- Sidebar: KST/UTC, 5s/10s/30s/수동, 1h/6h/오늘/24h/7d/직접 입력: ✅ Task 7
- CoverageStatsWriter + flush + record_event + record_gap + run(): ✅ Tasks 1-3
- CollectorDaemon + MultiSymbolCollector wiring: ✅ Task 4
- CLI integration: ✅ Task 4
- TTL cache (5-min): ✅ Task 5
- Error handling (missing file / malformed JSON / heartbeat error): ✅ Task 5 + 7

**Manifest display (§2):** The spec calls for `collector_run_id, selection_method, started_at_utc` from the manifest. Task 8 renders node cards from heartbeat but does not call `list_manifests()`. To add: import `list_manifests` from `mctrader_data.manifest`, read them in `status_adapter` or as a direct file read, and render below the node cards. This is a straightforward addition at implementation time — the spec lists it but it doesn't change any architecture.

**Type consistency:** `TierStats` is defined independently in both `coverage_stats.py` (mctrader-data) and `coverage_stats_adapter.py` (mctrader-web). The JSON serialization in `asdict()` + JSON parsing in the adapter ensures they stay in sync via the `coverage_stats.v1` schema contract. No import of mctrader-data types into mctrader-web (they are separate packages).
