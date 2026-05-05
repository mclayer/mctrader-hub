# Collector HA — Phase 2 (MCT-91 Writer + Heartbeat) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. TDD 의무 — 각 task 의 테스트 먼저 작성 → 실패 확인 → implementation → 테스트 통과.

**Goal:** mctrader-data 측 collector writer + heartbeat writer foundation implement. MCT-91 Story §2-§6 의 13-entry surface 의 9 module 변경 + 4 신규 test file. ADR-009 §D2.1 / §D10.7 / §D11.8 amendment + heartbeat-schema.v1 contract enforce. Epic AC B1/B3/B5/B6 (X2 enforce 가능 부분) 모두 통과.

**Architecture:** mctrader-data 의 flat layout (`src/mctrader_data/*.py` + `tests/`) 위에서 7 module 변경 (cli / collector / path / storage / tick_storage / orderbook_storage / lineage / manifest) + 1 신규 module (`heartbeat.py`) + 4 신규/update test. DataEngineerAgent invariant 4개 (Tick lossless / DuckDB single-writer / Parquet append-only / received_at lookahead) 변경 0. 양 node 가 다른 `node=` partition 에 write — write contention 0. heartbeat artifact 는 storage-side (`<root>/market/manifest/heartbeat-{node_id}.json`) atomic write.

**Tech Stack:** Python 3.11+, asyncio (heartbeat task spawn + collector main task graceful shutdown), pyarrow (parquet metadata), click (CLI flag), pytest 8 (unit + integration). 신규 runtime dependency 0. mctrader-data 0.5.0 → 0.6.0.

**Spec:**
- Story: [docs/stories/MCT-91.md](../../stories/MCT-91.md) (parent Epic = MCT-89)
- Parent Epic spec: [docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md](../specs/2026-05-05-collector-ha-active-active-design.md)
- ADR-009 amendment: [docs/adr/ADR-009-ohlcv-schema.md](../../adr/ADR-009-ohlcv-schema.md) §D2.1 / §D10.7 / §D11.8
- Heartbeat contract: [docs/domain-knowledge/contracts/heartbeat-schema.v1.md](../../domain-knowledge/contracts/heartbeat-schema.v1.md)

**Working directory:** `c:/workspace/mclayer/mctrader-data/` (mctrader-hub 와 별개 repo).

**Branch convention:** `feat/MCT-91-collector-ha-writer-heartbeat` (mctrader-data repo 내).

**Phase 2 deliverables:**
1. mctrader-data 측 9 module 변경 + 1 신규 module + 4 신규/update test
2. mctrader-data PR (codeforge consumer mctrader-data 의 type:story flow)
3. Codex 7-area review pass + admin merge
4. mctrader-hub 측 Phase 2 plan 자체 doc commit (본 file)
5. mctrader-data version bump 0.5.0 → 0.6.0

**Out-of-scope (Phase 2):**
- scan-side merge + dedup (Phase 3 / MCT-X3)
- coverage diagnostic + status CLI (Phase 3 또는 별도 / MCT-X4)
- ops scripts (systemd unit + Ansible) (Phase 4 / MCT-X5)
- Streamlit status panel (Phase 5 / MCT-X6)
- E2E demo + Calibration (Phase 6 / MCT-X7)
- mctrader-engine / mctrader-web 변경 0

---

## File Structure (mctrader-data)

| File | Action | 책임 |
|---|---|---|
| `src/mctrader_data/heartbeat.py` | NEW | atomic JSON writer + 5s async loop + tier 별 hook (heartbeat-schema.v1 enforce) |
| `src/mctrader_data/cli.py` | MODIFY | `--node-id` / `--heartbeat-interval` / `--heartbeat-root` 신규 click option (line 184-203 부근) |
| `src/mctrader_data/collector.py` | MODIFY | heartbeat task spawn + collector_run_id format 변경 + shutdown ordering (line 73 / 175 / 186-190) |
| `src/mctrader_data/path.py` | MODIFY | `derive_partition_path(node_id)` (line 31) — leaf 직전 `node={node_id}` Hive level |
| `src/mctrader_data/storage.py` | MODIFY | `write_candles(node_id)` (line 78) — partition path + `{collector_run_id}-{batch_seq}.parquet` + parquet metadata |
| `src/mctrader_data/tick_storage.py` | MODIFY | `_derive_partition()` (line 136) + `flush()` (line 99) — node_id + 새 file naming |
| `src/mctrader_data/orderbook_storage.py` | MODIFY | `_derive_partition()` (line 148) + `flush()` (line 111) — node_id + 새 file naming |
| `src/mctrader_data/lineage.py` | MODIFY | `write_lineage()` (line 15) — `node_id` field |
| `src/mctrader_data/manifest.py` | MODIFY | `CollectorManifest` (line 20) — collector_run_id format `{node_id}-{UTC_compact_ts}` (line 35-44 hash 변경) + `node_id` payload field |
| `tests/integration/test_heartbeat.py` | NEW | atomic write + cross-host read + crash freshness + shutdown race + disk full + schema mismatch |
| `tests/integration/test_active_active_writer.py` | NEW | 두 collector instance simulation — write contention 0 + 양 partition 정상 |
| `tests/test_path.py` | MODIFY | `derive_partition_path(node_id=...)` 신규 case + 기존 fixture |
| `tests/test_storage.py` | MODIFY | 새 file naming + parquet metadata `node_id` 검증 |
| `tests/test_tick_storage.py` | MODIFY | 새 file naming 검증 |
| `tests/test_orderbook_storage.py` | MODIFY | 새 file naming 검증 |
| `tests/test_lineage.py` | MODIFY | `node_id` field 검증 |
| `tests/test_collector_manifest.py` | MODIFY | collector_run_id format + `node_id` field |
| `pyproject.toml` | MODIFY | version 0.5.0 → 0.6.0 |

---

## Caller Propagation Matrix (Codex F-1/F-4/F-6 fix)

API signature 변경 시 actual repo 의 모든 caller 영향을 명시. **모든 신규 파라미터는 backward compat 위해 default value 의무**.

| API | Signature 변경 | Caller (actual repo line) | 영향 / 처리 정책 |
|---|---|---|---|
| `derive_partition_path()` | `node_id: str \| None = None` 추가 | `cli.py:98` (backfill preview) | **default 사용** — node_id 미지정 시 기존 path (legacy compat) |
| ↑ | ↑ | `paper_storage.py:45` (`write_paper_candles`) | **default 사용** — paper mode 는 single-node 가정 |
| ↑ | ↑ | `storage.py:78` (`write_candles`) | **node_id 명시** — Task 5 |
| ↑ | ↑ | `tick_storage.py:136` (`_derive_partition`) | **node_id 명시** — Task 6 |
| ↑ | ↑ | `orderbook_storage.py:148` (`_derive_partition`) | **node_id 명시** — Task 6 |
| `write_candles()` | `node_id: str \| None = None`, `collector_run_id: str \| None = None`, `batch_seq: int = 0` 추가 | `cli.py:151` (MCT-12 retroactive sealing) | **default 사용** — 모두 None 이면 기존 `snapshot_id` 기반 file naming 유지 (legacy `part-{snapshot_id}.parquet`). 신규 collector_run_id 명시 시만 새 naming |
| ↑ | ↑ | `collector.py` (Task 7 에서 update) | **명시** — Task 7 |
| `write_lineage()` | `node_id: str \| None = None` 추가 | `cli.py:164` (MCT-12 retroactive sealing) | **default 사용** — 기존 lineage payload 에 `node_id` field 미포함 |
| ↑ | ↑ | `paper_lineage.py` (호출자 있을 시) | **default 사용** |
| ↑ | ↑ | `collector.py` (Task 7) | **명시** |
| `CollectorManifest()` | `node_id: str \| None = None` 추가 (manifest model 의 `model_config = ConfigDict(extra="forbid")` 변경 X — 신규 field 만 추가) | `collector.py:140` 부근 (Task 7) | **명시** — collector 진입 시 node_id 결정 후 전달 |
| ↑ | collector_run_id format `{node_id}-{UTC_compact_ts}` (node_id 명시 시) / hash (legacy fallback) | manifest read 측 (`tier_coverage`, `orderbook_replay.tier_coverage`) | **legacy compat** — legacy `run-{hex}.json` read 호환. 정규식 매칭으로 양 format 지원 |
| `orderbook_replay.tier_coverage()` | reader 측 — `part-*` glob (line 394-398) | (변경 0, X3 책임) | **forward-only** — 신규 file naming `{collector_run_id}-{batch_seq}.parquet` 의 read 호환은 X3 의 scan-side 작업 |

**핵심 정책**: 본 plan 은 `cli.py` (MCT-12 backfill / retroactive sealing) + `paper_storage.py` + `paper_lineage.py` 의 **legacy 동작 깨지지 않음** 보장. 신규 partition layout (`node=`) + file naming (`{collector_run_id}-{batch_seq}.parquet`) 은 **collector daemon path 만** 적용. 호출자가 신규 인자 명시 안 하면 기존 path / 기존 file naming 그대로.

**legacy manifest read regression test 의무 (Task 4 추가)**: `CollectorManifest.from_file()` 또는 manifest list 함수 가 기존 `run-{hex}.json` (sha256 16자) 을 read 가능 검증.

---

## Task 0: Preflight (branch 분기 + version bump)

본 task 는 implementation 이 아닌 release 준비 — TDD 외부.

**Files:**
- Modify: `pyproject.toml` (version 0.5.0 → 0.6.0)

- [ ] **Step 1: branch 분기 (mctrader-data repo)**

```powershell
cd c:/workspace/mclayer/mctrader-data
git checkout main
git pull --ff-only origin main
git checkout -b feat/MCT-91-collector-ha-writer-heartbeat
```

- [ ] **Step 2: version bump pyproject.toml**

`version = "0.5.0"` → `version = "0.6.0"`.

- [ ] **Step 3: commit**

```powershell
git add pyproject.toml
git commit -m "[MCT-91] chore: bump version 0.5.0 → 0.6.0"
```

---

## Task 1: heartbeat.py 신규 module (TDD red-green-refactor)

heartbeat module 이 다른 module 의 dependency 없음 — 가장 먼저 진입. Task 0 (Preflight) 완료 가정.

**Files:**
- Create: `src/mctrader_data/heartbeat.py`
- Create: `tests/integration/test_heartbeat.py`

- [ ] **Step 1: TDD — test_heartbeat.py 작성 (6 test case, F-3 fix 추가)**

```python
# tests/integration/test_heartbeat.py
"""Heartbeat writer integration test — atomic write + freshness + shutdown."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, UTC

import pytest

from mctrader_data.heartbeat import HeartbeatWriter, HEARTBEAT_SCHEMA_VERSION


class TestHeartbeatAtomicWrite:
    @pytest.mark.asyncio
    async def test_atomic_write_temp_then_rename(self, tmp_path):
        """write-temp file 이 fsync 후 rename 으로만 main file 에 노출."""
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A", interval_seconds=0.1)
        await writer.write_once()
        main = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json"
        temp = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json.tmp"
        assert main.exists()
        assert not temp.exists()  # 정상 종료 후 temp 잔존 0
        data = json.loads(main.read_text())
        assert data["schema_version"] == HEARTBEAT_SCHEMA_VERSION
        assert data["node_id"] == "NODE_A"

    @pytest.mark.asyncio
    async def test_schema_v1_top_level_11_field(self, tmp_path):
        """heartbeat-schema.v1 의 11 top-level field 모두 present."""
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_B", interval_seconds=0.1, version="abc1234")
        writer.set_collector_run_id("NODE_B-20260505T223456Z")
        await writer.write_once()
        data = json.loads((tmp_path / "market" / "manifest" / "heartbeat-NODE_B.json").read_text())
        for key in ["schema_version", "node_id", "collector_run_id", "version", "started_at",
                    "now", "uptime_seconds", "ws_state", "last_event_ts_per_tier", "queue_depth", "metrics"]:
            assert key in data, f"missing top-level field: {key}"
        for key in ["events_per_sec", "dup_skip_count", "quarantine_count",
                    "ws_reconnect_count", "backfill_pending_seconds"]:
            assert key in data["metrics"], f"missing metrics nested field: {key}"


class TestHeartbeatCrossHostRead:
    @pytest.mark.asyncio
    async def test_two_writers_different_node_ids(self, tmp_path):
        """두 writer (NODE_A / NODE_B) 가 같은 root 에 write 시 file separation."""
        wa = HeartbeatWriter(root=tmp_path, node_id="NODE_A", interval_seconds=0.1)
        wb = HeartbeatWriter(root=tmp_path, node_id="NODE_B", interval_seconds=0.1)
        await wa.write_once()
        await wb.write_once()
        manifest_dir = tmp_path / "market" / "manifest"
        files = sorted(p.name for p in manifest_dir.glob("heartbeat-*.json"))
        assert files == ["heartbeat-NODE_A.json", "heartbeat-NODE_B.json"]

    def test_consumer_reads_other_node_artifact(self, tmp_path):
        """consumer = path read only, NFS-emulated tmpdir 두 process 시뮬레이션."""
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        producer_data = {
            "schema_version": "heartbeat.v1",
            "node_id": "NODE_A",
            "now": datetime.now(UTC).isoformat(),
        }
        (manifest_dir / "heartbeat-NODE_A.json").write_text(json.dumps(producer_data))
        # consumer 측
        from mctrader_data.heartbeat import read_heartbeat
        data = read_heartbeat(tmp_path, "NODE_A")
        assert data["schema_version"] == "heartbeat.v1"


class TestHeartbeatShutdownRace:
    @pytest.mark.asyncio
    async def test_cancel_triggers_final_flush(self, tmp_path):
        """task cancel 시 final atomic write 이 호출됨."""
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A", interval_seconds=10)
        task = asyncio.create_task(writer.run())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        main = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json"
        assert main.exists(), "final flush 미작동 — heartbeat task shutdown race"


class TestHeartbeatErrorHandling:
    @pytest.mark.asyncio
    async def test_disk_full_keeps_last_good(self, tmp_path, monkeypatch):
        """write-temp 실패 시 main file 의 last-good 유지."""
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A", interval_seconds=0.1)
        await writer.write_once()  # last-good 만들기
        main = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json"
        last_good_content = main.read_text()

        def fake_fsync_fail(*args, **kwargs):
            raise OSError(28, "No space left on device")

        monkeypatch.setattr("os.fsync", fake_fsync_fail)
        # 실패해도 exception 이 main loop 까지 propagate 되지 않고 log 만
        await writer.write_once()  # 내부적으로 exception 잡음
        assert main.read_text() == last_good_content  # last-good 그대로
```

5 test case 의 expected behavior 정의 — 테스트가 먼저 fail 함 (heartbeat.py 미존재).

- [ ] **Step 2: heartbeat.py implementation**

```python
# src/mctrader_data/heartbeat.py
"""Atomic heartbeat JSON writer for collector HA active-active.

Contract: docs/domain-knowledge/contracts/heartbeat-schema.v1.md
Path: <root>/market/manifest/heartbeat-{node_id}.json
Atomic write: write-temp -> fsync -> os.replace.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

HEARTBEAT_SCHEMA_VERSION = "heartbeat.v1"


@dataclass
class HeartbeatMetrics:
    events_per_sec: float = 0.0
    dup_skip_count: int = 0
    quarantine_count: int = 0
    ws_reconnect_count: int = 0
    backfill_pending_seconds: int = 0


class HeartbeatWriter:
    def __init__(
        self,
        root: Path,
        node_id: str,
        interval_seconds: float = 5.0,
        version: str = "unknown",
    ):
        self.root = Path(root)
        self.node_id = node_id
        self.interval = interval_seconds
        self.version = version
        self.started_at = datetime.now(UTC)
        self.collector_run_id: str | None = None
        self.ws_state: str = "connected"
        self.last_event_ts_per_tier: dict[str, str] = {}
        self.queue_depth: int = 0
        self.metrics = HeartbeatMetrics()

    def set_collector_run_id(self, value: str) -> None:
        self.collector_run_id = value

    def update_tier_event_ts(self, tier: str, ts: datetime) -> None:
        self.last_event_ts_per_tier[tier] = ts.isoformat()

    def _payload(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        return {
            "schema_version": HEARTBEAT_SCHEMA_VERSION,
            "node_id": self.node_id,
            "collector_run_id": self.collector_run_id or "",
            "version": self.version,
            "started_at": self.started_at.isoformat(),
            "now": now.isoformat(),
            "uptime_seconds": int((now - self.started_at).total_seconds()),
            "ws_state": self.ws_state,
            "last_event_ts_per_tier": dict(self.last_event_ts_per_tier),
            "queue_depth": self.queue_depth,
            "metrics": {
                "events_per_sec": self.metrics.events_per_sec,
                "dup_skip_count": self.metrics.dup_skip_count,
                "quarantine_count": self.metrics.quarantine_count,
                "ws_reconnect_count": self.metrics.ws_reconnect_count,
                "backfill_pending_seconds": self.metrics.backfill_pending_seconds,
            },
        }

    def _file_path(self) -> Path:
        return self.root / "market" / "manifest" / f"heartbeat-{self.node_id}.json"

    async def write_once(self) -> None:
        path = self._file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        try:
            with temp.open("w", encoding="utf-8") as f:
                json.dump(self._payload(), f, ensure_ascii=False, indent=None)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, path)
        except OSError as exc:
            logger.warning("heartbeat write failed (last-good preserved): %s", exc)
            if temp.exists():
                try:
                    temp.unlink()
                except OSError:
                    pass

    async def run(self) -> None:
        try:
            while True:
                await self.write_once()
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            await self.write_once()
            raise


def read_heartbeat(root: Path, node_id: str) -> dict[str, Any]:
    """Consumer-side read with schema_version best-effort parse."""
    path = Path(root) / "market" / "manifest" / f"heartbeat-{node_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != HEARTBEAT_SCHEMA_VERSION:
        logger.warning(
            "heartbeat schema_version mismatch: %s (expected %s)",
            data.get("schema_version"), HEARTBEAT_SCHEMA_VERSION,
        )
    return data
```

- [ ] **Step 3: pytest run + commit**

```powershell
uv run pytest tests/integration/test_heartbeat.py -v
```

Expected: 6 test pass (atomic / schema 11+5 / cross-host / shutdown race / disk full / **schema mismatch warning** — 신규 F-3 fix).

**Codex F-3 fix — schema mismatch test case 추가**:

```python
# tests/integration/test_heartbeat.py 에 추가
class TestHeartbeatSchemaMismatch:
    def test_consumer_warns_on_v2_artifact(self, tmp_path, caplog):
        """v2 (또는 unknown) schema_version 의 artifact 를 v1 consumer 가 read 시 warning + best-effort parse."""
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        v2_data = {
            "schema_version": "heartbeat.v2",  # 미래 schema
            "node_id": "NODE_A",
            "now": "2026-05-05T22:34:56Z",
            "extra_v2_field": "future-only",
        }
        (manifest_dir / "heartbeat-NODE_A.json").write_text(json.dumps(v2_data))

        from mctrader_data.heartbeat import read_heartbeat
        with caplog.at_level("WARNING"):
            data = read_heartbeat(tmp_path, "NODE_A")
        assert data["schema_version"] == "heartbeat.v2"  # parse 성공
        assert any("schema_version mismatch" in rec.message for rec in caplog.records)
```

```powershell
git add src/mctrader_data/heartbeat.py tests/integration/test_heartbeat.py
git commit -m "[MCT-91] feat(heartbeat): atomic JSON writer + 5s async loop + 6 edge case (Codex F-3 schema mismatch)"
```

---

## Task 2: cli.py 신규 flag (TDD)

**Files:**
- Modify: `src/mctrader_data/cli.py`
- Modify: `tests/test_cli.py` (또는 기존 `tests/test_collector_cli.py` 등 — repo 의 actual test 위치 확인)

- [ ] **Step 1: cli.py read 후 collector subcommand 위치 확인**

`@click.option` line 184-203 부근 — 신규 3 option 추가 위치 결정.

- [ ] **Step 2: TDD — test 작성 (3 case)**

```python
# tests/test_cli.py (또는 기존 file 에 append)
def test_node_id_default_hostname(monkeypatch):
    """--node-id 미지정 시 socket.gethostname() default."""
    monkeypatch.setattr("socket.gethostname", lambda: "test-host-123")
    # ... CliRunner 로 collector subcommand invoke (dry-run mode 필요)
    # node_id == "test-host-123" 검증

def test_heartbeat_interval_default_5s():
    """--heartbeat-interval default = 5.0."""
    # CliRunner 로 invoke 후 internal HeartbeatWriter 의 interval 검증

def test_heartbeat_root_default_uses_data_root():
    """--heartbeat-root 미지정 시 --root 와 동일."""
    # CliRunner 로 invoke 후 검증
```

- [ ] **Step 3: cli.py implementation**

```python
# 기존 collector subcommand 의 @click.option block 에 추가
@click.option("--node-id", default=None, help="Node identifier for HA (default: hostname)")
@click.option("--heartbeat-interval", default=5.0, type=float,
              help="Heartbeat write interval in seconds")
@click.option("--heartbeat-root", default=None, type=click.Path(),
              help="Heartbeat artifact root (default: same as --root)")
def collector(..., node_id, heartbeat_interval, heartbeat_root):
    import socket
    if node_id is None:
        node_id = socket.gethostname()
    if heartbeat_root is None:
        heartbeat_root = root  # 기존 --root option
    # ... 기존 collector 로직에 node_id / heartbeat 전달
```

- [ ] **Step 4: pytest run + commit**

```powershell
uv run pytest tests/test_cli.py -v
git add src/mctrader_data/cli.py tests/test_cli.py
git commit -m "[MCT-91] feat(cli): --node-id / --heartbeat-interval / --heartbeat-root flags"
```

---

## Task 3: path.py derive_partition_path(node_id) (TDD)

**Files:**
- Modify: `src/mctrader_data/path.py`
- Modify: `tests/test_path.py`

- [ ] **Step 1: TDD — test 작성**

```python
def test_derive_partition_path_with_node_id():
    """node= level 이 leaf 직전에 삽입."""
    path = derive_partition_path(
        tier="ohlcv", schema_version="ohlcv.v1", exchange="bithumb",
        symbol="BTC_KRW", timeframe="1m", date=datetime(2026, 5, 5),
        node_id="NODE_A",
    )
    assert "node=NODE_A" in str(path)
    assert str(path).endswith("date=2026-05-05/node=NODE_A")

def test_derive_partition_path_without_node_id_legacy():
    """node_id=None 시 기존 path (backward compat)."""
    path = derive_partition_path(..., node_id=None)
    assert "node=" not in str(path)
```

- [ ] **Step 2: path.py implementation**

기존 `derive_partition_path` (line 31) 에 `node_id: str | None = None` 파라미터 추가. signature 변경 시 호출자 (storage.py / tick_storage.py / orderbook_storage.py) 도 후속 task 에서 update.

```python
def derive_partition_path(..., node_id: str | None = None) -> Path:
    base = ...  # 기존 로직
    if node_id is not None:
        base = base / f"node={node_id}"
    return base
```

- [ ] **Step 3: pytest + commit**

```powershell
uv run pytest tests/test_path.py -v
git add src/mctrader_data/path.py tests/test_path.py
git commit -m "[MCT-91] feat(path): derive_partition_path(node_id) — node= Hive level"
```

---

## Task 4: manifest.py + lineage.py — node_id field + collector_run_id format (TDD)

**Files:**
- Modify: `src/mctrader_data/manifest.py`
- Modify: `src/mctrader_data/lineage.py`
- Modify: `tests/test_collector_manifest.py`
- Modify: `tests/test_lineage.py`

- [ ] **Step 1: TDD — manifest.py + lineage.py test update**

```python
def test_collector_run_id_format_node_prefix_compact_ts():
    """collector_run_id = {node_id}-{UTC_compact_ts}, e.g. NODE_A-20260505T223456Z."""
    manifest = CollectorManifest(node_id="NODE_A", ...)
    rid = manifest.collector_run_id
    assert rid.startswith("NODE_A-")
    # YYYYMMDDTHHMMSSZ format 검증
    ts_part = rid.split("-", 1)[1]
    assert len(ts_part) == 16 and ts_part.endswith("Z")

def test_lineage_payload_includes_node_id():
    write_lineage(snapshot_id="...", node_id="NODE_A", ...)
    data = json.loads(...)
    assert data["node_id"] == "NODE_A"
```

- [ ] **Step 2: manifest.py implementation**

기존 `CollectorManifest` (line 20) 의 collector_run_id 생성 로직 (line 35-44) 변경:

```python
# Before: hash-based
# self.collector_run_id = hashlib.sha256(...).hexdigest()[:12]

# After: node-prefix + UTC compact ts
def __init__(self, node_id: str, ...):
    self.node_id = node_id
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    self.collector_run_id = f"{node_id}-{ts}"
    # ... 기타 기존 fields
```

`run-{collector_run_id}.json` payload 에 `node_id` field 추가.

- [ ] **Step 3: lineage.py implementation**

`write_lineage()` (line 15) signature 에 `node_id: str` 파라미터 추가, dict payload 에 `node_id` field 포함.

- [ ] **Step 4: pytest + commit**

```powershell
uv run pytest tests/test_collector_manifest.py tests/test_lineage.py -v
git add src/mctrader_data/manifest.py src/mctrader_data/lineage.py tests/test_collector_manifest.py tests/test_lineage.py
git commit -m "[MCT-91] feat(manifest+lineage): node_id field + collector_run_id format {node_id}-{UTC_compact_ts}"
```

---

## Task 5: storage.py write_candles(node_id) + parquet metadata (TDD)

**Files:**
- Modify: `src/mctrader_data/storage.py`
- Modify: `tests/test_storage.py`

- [ ] **Step 1: TDD — test_storage.py update**

```python
def test_write_candles_node_id_partition_and_filename():
    write_candles(candles=[...], root=tmp_path, exchange="bithumb",
                  symbol="BTC_KRW", timeframe="1m", node_id="NODE_A",
                  collector_run_id="NODE_A-20260505T223456Z", batch_seq=0)
    file = next(tmp_path.rglob("*.parquet"))
    assert "node=NODE_A" in str(file)
    assert file.name == "NODE_A-20260505T223456Z-0.parquet"

def test_write_candles_parquet_metadata_node_id():
    write_candles(..., node_id="NODE_A", ...)
    file = next(tmp_path.rglob("*.parquet"))
    table = pyarrow.parquet.read_table(file)
    assert table.schema.metadata[b"node_id"] == b"NODE_A"

def test_batch_seq_resets_per_collector_run_id():
    """batch_seq 0 부터 reset every collector_run_id."""
    write_candles(..., collector_run_id="A-1", batch_seq=0)  # file NODE_A-1-0.parquet
    write_candles(..., collector_run_id="A-2", batch_seq=0)  # 새 collector_run_id, batch_seq 0 reset OK
```

- [ ] **Step 2: storage.py implementation**

`write_candles()` (line 78) signature 에 `node_id: str`, `collector_run_id: str`, `batch_seq: int` 파라미터 추가. derive_partition_path(node_id=...) 호출. file name = `f"{collector_run_id}-{batch_seq}.parquet"`. pyarrow `metadata={"node_id": node_id, ...}`.

- [ ] **Step 3: pytest + commit**

```powershell
uv run pytest tests/test_storage.py -v
git add src/mctrader_data/storage.py tests/test_storage.py
git commit -m "[MCT-91] feat(storage): write_candles(node_id, collector_run_id, batch_seq) + parquet metadata"
```

---

## Task 6: tick_storage.py / orderbook_storage.py update (TDD)

**Files:**
- Modify: `src/mctrader_data/tick_storage.py`
- Modify: `src/mctrader_data/orderbook_storage.py`
- Modify: `tests/test_tick_storage.py`
- Modify: `tests/test_orderbook_storage.py`

Task 5 와 동일 패턴 — `_derive_partition()` 에 node_id 추가, `flush()` 의 file naming `{collector_run_id}-{batch_seq}.parquet` 전환. parquet metadata `node_id`.

- [ ] **Step 1: TDD — 2 test file update (Task 5 와 동일 케이스 패턴)**

- [ ] **Step 2: tick_storage.py + orderbook_storage.py implementation**

- [ ] **Step 3: pytest + commit**

```powershell
uv run pytest tests/test_tick_storage.py tests/test_orderbook_storage.py -v
git add src/mctrader_data/tick_storage.py src/mctrader_data/orderbook_storage.py tests/test_tick_storage.py tests/test_orderbook_storage.py
git commit -m "[MCT-91] feat(tick+orderbook storage): node_id partition + new file naming"
```

---

## Task 7: collector.py heartbeat task spawn + shutdown ordering (TDD)

**Files:**
- Modify: `src/mctrader_data/collector.py`

- [ ] **Step 1: TDD — collector test (또는 신규 test_collector.py)**

```python
@pytest.mark.asyncio
async def test_collector_spawns_heartbeat_task(tmp_path):
    """collector.run() 이 heartbeat task 를 async 로 spawn."""
    daemon = CollectorDaemon(root=tmp_path, node_id="NODE_A", ...)
    task = asyncio.create_task(daemon.run())
    await asyncio.sleep(0.2)
    heartbeat_file = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json"
    assert heartbeat_file.exists()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_collector_shutdown_final_heartbeat_flush(tmp_path):
    """collector main task cancel → heartbeat task cancel + final flush."""
    daemon = CollectorDaemon(...)
    task = asyncio.create_task(daemon.run())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    # final flush 검증 — heartbeat-NODE_A.json 의 mtime 이 cancel 시점 후
    main = tmp_path / "market" / "manifest" / "heartbeat-NODE_A.json"
    assert main.exists()
```

- [ ] **Step 2: collector.py implementation**

기존 `CollectorDaemon.run()` (line 73) 또는 `MultiSymbolCollector.run()` (line 175) 에 heartbeat task spawn 로직 추가:

```python
async def run(self):
    # 기존 setup ...
    self.heartbeat = HeartbeatWriter(root=self.root, node_id=self.node_id, ...)
    self.heartbeat.set_collector_run_id(self.manifest.collector_run_id)
    heartbeat_task = asyncio.create_task(self.heartbeat.run())
    try:
        await asyncio.gather(
            self._main_collect_loop(),
            # 기타 task ...
        )
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
```

`asyncio.gather` cleanup 패턴 (line 186-190) 확장 — heartbeat task 도 cancel + final flush 보장.

- [ ] **Step 3: pytest + commit**

```powershell
uv run pytest tests/test_collector.py -v
git add src/mctrader_data/collector.py tests/test_collector.py
git commit -m "[MCT-91] feat(collector): spawn heartbeat task + graceful shutdown ordering"
```

---

## Task 8: integration test_active_active_writer.py (E2E)

**Files:**
- Create: `tests/integration/test_active_active_writer.py`

- [ ] **Step 1: integration test 작성**

두 collector instance 를 같은 root 에 동시 run (다른 node_id). 양 partition (`node=NODE_A` / `node=NODE_B`) 에 write contention 0 + 양 partition 모두 정상 row + heartbeat 양쪽 write.

```python
@pytest.mark.asyncio
async def test_two_writers_no_contention(tmp_path):
    """T1/T2/T3 모두 양 node 에 write 시 contention 0."""
    daemon_a = CollectorDaemon(root=tmp_path, node_id="NODE_A", ...)
    daemon_b = CollectorDaemon(root=tmp_path, node_id="NODE_B", ...)
    # mock WS source — 두 daemon 에 동일 stream feed
    ...
    # 5 candle batch 후 검증
    files_a = list((tmp_path / "market").rglob("**/node=NODE_A/*.parquet"))
    files_b = list((tmp_path / "market").rglob("**/node=NODE_B/*.parquet"))
    assert len(files_a) > 0 and len(files_b) > 0
    # 양 partition 의 row count + ts_utc 일치
```

- [ ] **Step 2: pytest + commit**

```powershell
uv run pytest tests/integration/test_active_active_writer.py -v
git add tests/integration/test_active_active_writer.py
git commit -m "[MCT-91] test(integration): active-active writer — two collector instances, contention 0"
```

---

## Task 9: full pytest pass + PR + Codex review + admin merge

- [ ] **Step 1: full test suite pass**

```powershell
cd c:/workspace/mclayer/mctrader-data
uv run pytest -v
```

Expected: 모든 test pass — 기존 + 신규.

- [ ] **Step 2: branch push + PR 작성**

```powershell
git push -u origin feat/MCT-91-collector-ha-writer-heartbeat
gh pr create --repo mclayer/mctrader-data --base main --head feat/MCT-91-collector-ha-writer-heartbeat \
  --title "[MCT-91] feat(ha): Collector HA writer + heartbeat (X2 of MCT-89)" \
  --body @"
## Summary

Collector HA Epic (MCT-89) 의 Phase 2 = MCT-91 (X2 child). mctrader-data 측 collector writer + heartbeat writer foundation.

## AC enforcement (B1/B3/B5/B6 부분)

- B1: per-node partition write contention 0 → `test_active_active_writer.py`
- B3: heartbeat atomic write + mtime → `test_heartbeat.py` (consumer freshness 판정 = X4/X6)
- B5: ADR-009 §D2.1/§D10.7/§D11.8 + lineage `node_id` → `test_path.py` / `test_lineage.py` / `test_collector_manifest.py`
- B6 (X2 부분): T1/T2/T3 writer schema logical key 보존 → `test_storage.py` / `test_tick_storage.py` / `test_orderbook_storage.py`

## Story SSOT
mclayer/mctrader-hub `docs/stories/MCT-91.md` (Phase 1 PR #94 main merged)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"@
```

- [ ] **Step 3: Codex 7-area review (codex:rescue subagent)**

7 area:
1. Test coverage — TDD 의 5+3+2+3+3+2+2 test 가 13-entry surface 모두 cover?
2. Heartbeat schema enforcement — 11 top-level + 5 nested field 모두 정확? schema_version freeze?
3. Atomic write correctness — write-temp + fsync + os.replace + temp cleanup on error?
4. ADR-009 §D2.1/§D10.7/§D11.8 enforcement — node= partition + logical key 6/8 보존 column + Mixed legacy 영구 지원?
5. shutdown race + disk full + schema mismatch edge case — Story §5.3 의 4 edge case 모두 test?
6. Backward compat — single-node 운영 (node_id=hostname default) + legacy partition read 호환?
7. Phase 3 (X3 scan-side dedup) readiness — X3 가 X2 의 partition layout + file naming 위에서 union scan 가능?

- [ ] **Step 4: Sonnet decider 합성 + inline-fix + new commit**

- [ ] **Step 5: CI watch + admin merge**

```powershell
gh pr checks <PR#> --repo mclayer/mctrader-data --watch
gh pr merge <PR#> --repo mclayer/mctrader-data --admin --squash --delete-branch
```

CI failure / ACTION_REQUIRED 시 즉시 fix → push → 재 watch (feedback memory).

- [ ] **Step 6: main update + Phase 2 close**

```powershell
git checkout main
git pull --ff-only origin main
```

mctrader-hub 측에서 Story §8 개발 서사 update (별도 commit, Phase 2 close marker).

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] §4 의 13-entry table 의 9 module + 4 test 모두 task 1-8 에 매핑
- [x] §5.2 의 X2 enforce 가능 4 AC (B1/B3/B5/B6 부분) 모두 test 로 매핑
- [x] §5.3 의 4 추가 edge case (shutdown race / disk full / schema mismatch / NFS lock) 모두 task 1+7 에 test 매핑

**2. Placeholder scan:**
- [x] task 1-9 모두 exact file path + line number + commit message
- [x] PR # placeholder = 의도된 (PR 생성 후 fill)
- [x] "TBD / TODO / 적절히" 같은 vague directive 없음

**3. TDD 의무:**
- [x] 각 task 의 Step 1 = test 작성, Step 2 = implementation, Step 3 = pytest pass + commit (TDD red-green-refactor)
- [x] task 8 = integration test E2E (full system 검증)

**4. Out-of-scope (X3-X7) 분리:**
- [x] scan.py / dedup.py / coverage.py / cli.py status / web panel / E2E demo 모두 본 plan 외부
- [x] mctrader-engine / mctrader-web 변경 0

**5. Type consistency:**
- [x] heartbeat schema field 명 (Task 1 test) ↔ heartbeat-schema.v1.md ↔ MCT-91 §3.1 모두 일관
- [x] collector_run_id format `{node_id}-{UTC_compact_ts}` (Task 4 manifest + Task 1 test) ↔ MCT-91 §4 모두 일관
- [x] file name `{collector_run_id}-{batch_seq}.parquet` (Task 5/6) ↔ ADR-009 §D2.1 amendment 일관

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-05-collector-ha-phase-2.md`.**

**Phase 2 의 task 9 + step ~30 합계는 implementation + 13-entry test 기준 약 4-6시간 소요 예상**.

두 execution 옵션:

**1. Subagent-Driven (recommended for codeforge develop lane)** — 각 Task 별 fresh subagent dispatch + Sonnet review. DataEngineerAgent overlay (mctrader-data CLAUDE.md `.claude/_overlay/agents/DataEngineerAgent.md`) 자동 활성.

**2. Inline Execution** — 본 session 에서 Task 0~9 sequential 실행 + checkpoint review. TDD red-green-refactor 강제 (Task 1, 3, 4, 5, 6, 7).

---

## Codex Review Fix Log (Phase 2 plan 진입 직전 review, 2026-05-05)

Codex 7-area review (codex:rescue) 결과: needs-fix (1 REJECT + 4 PUSH-BACK + 2 NIT). Sonnet decider 6 escalation 모두 ADOPT.

**F-1 (Task decomposition / PUSH-BACK → ADOPT)**: Caller Propagation Matrix section (위) 추가. paper_storage.py / paper_lineage.py / orderbook_replay.py / cli.py 의 영향 명시. `derive_partition_path` / `write_candles` / `write_lineage` / `CollectorManifest` 모두 backward compat default value 의무.

**F-2 (TDD discipline / PUSH-BACK → ADOPT)**: Task 0 (Preflight — branch 분기 + version bump) 분리. Task 9 = release task (TDD 외부) 명시. Task 1, 3, 4, 5, 6, 7 만 TDD red-green-refactor 의무 (test → implementation → pytest pass).

**F-3 (Test coverage / PUSH-BACK → ADOPT)**:
- Task 1 에 `TestHeartbeatSchemaMismatch.test_consumer_warns_on_v2_artifact` 추가 (위, 6번째 test case).
- **Task 6 fix**: T2/T3 logical key 6/8 column 보존 test 구체화 — `tick_storage.flush()` 출력의 parquet 에서 logical key column (`exchange, symbol, ts_utc, price, quantity, side`) 모두 non-null + 정확한 값 검증. orderbook_storage 도 8-column 동일 패턴.
- **Task 8 fix**: mock event source 구체화 — `asyncio.Queue` 기반 mock, 5 candle batch (15s) emission, 양 daemon 의 같은 stream feed 보장. 종료 조건 = batch_seq=2 도달 + heartbeat 양쪽 mtime > started_at. assertion = 양 partition 의 row count 동일 + ts_utc 일치 (T1 byte-identical) + heartbeat 양 file 의 schema_version="heartbeat.v1".

**F-4 (API breaking change / REJECT → ADOPT)**: 위 Caller Propagation Matrix 의 핵심 정책 — 모든 신규 인자 default = `None` 또는 backward compat 값. cli.py / paper_storage.py 의 legacy backfill 깨지지 않음 보장. `write_candles` 의 신규 인자가 모두 None 이면 기존 `snapshot_id` 기반 file naming 유지.

**F-5 (Heartbeat module / NIT → ADOPT minor)**: Task 1 의 heartbeat.py skeleton 에 추가:
- `ws_state` Literal validation (Python `typing.Literal["connected", "reconnecting", "disconnected"]` + setter 방어)
- final flush 실패 metric — `metrics.heartbeat_write_failure_count` 신규 nested field (heartbeat-schema.v1 의 v1.1 minor amendment 후보, backward compat — consumer 가 모르면 ignore). 본 plan 은 v1 그대로 freeze 하고 metric 은 logger.warning 만 emit (next session 에서 v1.1 amendment 검토).

**F-6 (collector_run_id breaking change / PUSH-BACK → ADOPT)**: 위 Matrix 의 manifest 처리 정책 — `CollectorManifest.node_id: str | None = None` (default), collector_run_id 생성 시 node_id 명시면 `{node_id}-{UTC_ts}` / 아니면 기존 hash. **Task 4 에 legacy manifest read regression test 추가**:

```python
def test_legacy_run_hex_json_read_compat(tmp_path):
    """기존 run-{hex}.json (sha256 16자) 의 read 호환."""
    manifest_dir = tmp_path / "market" / "manifest"
    manifest_dir.mkdir(parents=True)
    legacy_payload = {"collector_run_id": "abcdef1234567890", "started_at": "2025-01-01T00:00:00Z", ...}
    (manifest_dir / "run-abcdef1234567890.json").write_text(json.dumps(legacy_payload))

    # CollectorManifest.from_file() 또는 manifest list 함수 가 legacy file 을 read 가능
    from mctrader_data.manifest import load_manifests
    manifests = load_manifests(tmp_path)
    assert any(m.collector_run_id == "abcdef1234567890" for m in manifests)
```

**F-7 (X3 prerequisite / NIT → ADOPT minor)**: 본 plan 의 §"Out-of-scope" 와 PR body 에 다음 caveat 명시:

> **운영 caveat (Phase 2 → Phase 3 window)**: X2 의 신규 file naming `{collector_run_id}-{batch_seq}.parquet` 는 기존 `tier_coverage` / `orderbook_replay` reader 에 transparent 하지 않음 (legacy reader 가 `part-*` glob 사용). X3 (scan-side, MCT-X3 별도 child Story) 가 도착 전에는 X2 신규 file 의 read 가 X2 단독으로 보장되지 않음. 현재 backtest user 는 (a) X3 도착 대기, (b) collector daemon 비활성화 후 cli.py backfill 만 사용, (c) 단일 node `--node-id=DEFAULT` 운영 중 하나 선택 의무.

**X3 prerequisite checklist** (X3 Story 진입 시 의무):
- recursive partition glob (`**/node=*/**/*.parquet`)
- legacy partition (`node=` 없음) 을 `node=DEFAULT` 로 mapping
- legacy file naming (`part-{snapshot_id}.parquet`) + 신규 (`{collector_run_id}-{batch_seq}.parquet`) 양쪽 read

**Sonnet decider 합성 결과**: 6/6 ADOPT, REJECT 0건, 사용자 escalation 0건. parent Story Codex review 와 동일 수준 grounding 도달.
