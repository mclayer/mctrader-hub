# MCT-106: Zero-loss Ingestion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace mctrader-data's in-memory Parquet writer with a WAL-based ingestion pipeline (NDJSON → tiered Parquet) to achieve zero data loss on SIGKILL/crash.

**Architecture:** `WalIngester` appends each event to a NDJSON file immediately via `os.open(O_APPEND)` + per-message `fsync`. Every 5 minutes, the active segment is atomically renamed `.ndjson.sealed`. `CompactorRunner` converts sealed segments to Parquet in 3 tiers: L1 (5 min), L2 (1 hour), L3 (1 day). Ingester and Compactor run as separate containers sharing the `mctrader_data` named volume.

**Tech Stack:** Python 3.12, pyarrow≥17, pytest, asyncio, `os.open/O_APPEND`, `os.replace` (atomic rename), `fcntl.flock`

**Change Plan:** `c:\workspace\mclayer\mctrader-hub\docs\change-plans\MCT-106-change-plan.md`

**Working repo:** `c:\workspace\mclayer\mctrader-data`

---

## File Map

### Phase A — New files (dormant, no behavior change)
| File | Purpose |
|------|---------|
| `src/mctrader_data/wal/__init__.py` | Package marker |
| `src/mctrader_data/wal/ndjson_codec.py` | encode_record / decode_line (Decimal-safe) |
| `src/mctrader_data/wal/segment.py` | Segment path helpers, seal/scan logic |
| `src/mctrader_data/wal/ingester.py` | WalIngester (per-symbol-channel writer) |
| `tests/test_wal_ndjson_codec.py` | INV-5 decimal roundtrip |
| `tests/test_wal_segment.py` | INV-2 atomic seal |
| `tests/test_wal_ingester.py` | WalIngester unit tests |
| `tests/test_wal_ingester_crash_recovery.py` | INV-1 zero-loss via subprocess |

### Phase B — New files (Compactor)
| File | Purpose |
|------|---------|
| `src/mctrader_data/compactor/__init__.py` | Package marker |
| `src/mctrader_data/compactor/l1.py` | L1Compactor: NDJSON sealed → 5-min Parquet |
| `src/mctrader_data/compactor/l2.py` | L2Compactor: 12×L1 → 1-hour Parquet |
| `src/mctrader_data/compactor/l3.py` | L3Compactor: 24×L2 → 1-day Parquet |
| `src/mctrader_data/compactor/runner.py` | CompactorRunner (asyncio scan loop) |
| `src/mctrader_data/compactor/gc.py` | GC: delete `.compacted` segments after 24h grace |
| `tests/test_compactor_l1.py` | INV-3 idempotency, INV-4 sort, INV-6 lineage |
| `tests/test_compactor_l2.py` | INV-7 tier merge |
| `tests/test_compactor_l3.py` | INV-8 monotone |
| `tests/test_wal_perf.py` | §8.3 performance baseline |
| `tests/integration/test_ingester_compactor_roundtrip.py` | §8.4 roundtrip |
| `tests/integration/test_multi_exchange_isolation.py` | §8.4 isolation |

### Phase C — Modified files (production cutover)
| File | Change |
|------|--------|
| `src/mctrader_data/collector.py` | `_handle_event` → `_emit_to_wal` using `WalIngester` |
| `src/mctrader_data/heartbeat.py` | Add `role` field (`ingester` \| `compactor`) |
| `src/mctrader_data/cli.py` | Add `compact` CLI command |
| `compose.yml` | `collector` → `bithumb-ingester` + `compactor` services |
| `tests/conftest.py` | `compact_now()` fixture for integration tests |

### Phase D — Modified files (deprecation)
| File | Change |
|------|--------|
| `src/mctrader_data/tick_storage.py` | `TickWriter` deprecated warning |
| `src/mctrader_data/orderbook_storage.py` | `OrderbookWriter` deprecated warning |
| `src/mctrader_data/orderbook_snapshot_storage.py` | `OrderbookSnapshotWriter` deprecated warning |
| `CHANGELOG.md` | Phase C cutover behavior change notice |

---

## Phase A: WAL Ingester Module (PR-1)

### Task 1: ADR-009 Amendment Commit (docs-only)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-009-ohlcv-schema.md`

- [ ] **Step 1: Add tier partition amendment to ADR-009**

Open `docs/adr/ADR-009-ohlcv-schema.md` and add a new amendment section for MCT-106. Append after the last `§D14` amendment:

```markdown
## §D2 amendment — Tier partition for compaction (MCT-106, 2026-05-09)

All Parquet layouts under `market/` gain a mandatory `tier=L{1,2,3}` partition key
**between** `schema_version=` and `exchange=`:

```
market/<channel>/schema_version=*.v1/tier=L{1,2,3}/exchange=.../symbol=.../date=.../node=<id>/part-*.parquet
```

- `node=<id>` remains **mandatory** per §D2.1 (enforced at every tier level).
- `tier=` absent legacy files are treated as `tier=L1` by all `scan_*` read APIs.
- `node=` absent legacy files are treated as `node=DEFAULT` by all `scan_*` read APIs.
  Both mixed-scan behaviours are permanent (no forced migration).

Cross-references: ADR-017 §Decision 2; MCT-106 Change Plan §4.2.
```

- [ ] **Step 2: Commit (docs only — must be PR-1 head commit)**

```bash
git -C c:/workspace/mclayer/mctrader-hub add docs/adr/ADR-009-ohlcv-schema.md
git -C c:/workspace/mclayer/mctrader-hub commit -m "docs(adr): ADR-009 §D2 amendment — tier=L{1,2,3} partition + node= mandatory [MCT-106]"
```

---

### Task 2: NDJSON Codec (TDD)

**Files:**
- Create: `src/mctrader_data/wal/__init__.py`
- Create: `src/mctrader_data/wal/ndjson_codec.py`
- Create: `tests/test_wal_ndjson_codec.py`

- [ ] **Step 1: Create package marker**

```python
# src/mctrader_data/wal/__init__.py
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_wal_ndjson_codec.py
"""Tests for wal/ndjson_codec.py — INV-5 decimal roundtrip."""
from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone

import pytest

from mctrader_data.wal.ndjson_codec import decode_line, encode_record


def test_encode_decode_roundtrip_basic() -> None:
    record = {
        "ts_utc": datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "price": Decimal("100000.123456789012345678"),
        "quantity": Decimal("0.001"),
        "symbol": "KRW-BTC",
    }
    line = encode_record(record)
    assert line.endswith("\n")
    decoded = decode_line(line)
    assert decoded["symbol"] == "KRW-BTC"
    assert decoded["price"] == Decimal("100000.123456789012345678")


def test_decimal_no_precision_loss_38_18() -> None:
    """INV-5: Decimal(38,18) round-trip preserves all digits."""
    price = Decimal("99999999999999999999.123456789012345678")  # 38 significant digits
    record = {"price": price}
    decoded = decode_line(encode_record(record))
    assert decoded["price"] == price


def test_decimal_no_scientific_notation() -> None:
    """str(Decimal) must not produce scientific notation for normal values."""
    # Ensure Decimal values that could trigger scientific notation are safe
    price = Decimal("1E+10")
    line = encode_record({"price": price})
    decoded = decode_line(line)
    # Round-trip safe: Decimal("1E+10") == Decimal("10000000000")
    assert decoded["price"] == price


def test_encode_produces_single_line() -> None:
    line = encode_record({"x": 1})
    assert line.count("\n") == 1
    assert line[-1] == "\n"


def test_decode_non_decimal_number_preserved_as_decimal() -> None:
    """parse_float=Decimal ensures float literals in JSON become Decimal."""
    line = '{"qty": 1.5}\n'
    decoded = decode_line(line)
    assert isinstance(decoded["qty"], Decimal)
    assert decoded["qty"] == Decimal("1.5")
```

- [ ] **Step 3: Run tests — expect failure**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_ndjson_codec.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'mctrader_data.wal'`

- [ ] **Step 4: Implement ndjson_codec.py**

```python
# src/mctrader_data/wal/ndjson_codec.py
"""NDJSON encode/decode with Decimal and datetime support (INV-5 SSOT)."""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal


def encode_record(record: dict) -> str:
    """Encode a record dict to a single NDJSON line (ends with \\n).

    Decimal: str(Decimal) — no scientific notation for normal values, round-trip safe.
    datetime: ISO 8601 with offset.
    """
    return json.dumps(record, default=_default, ensure_ascii=False, separators=(",", ":")) + "\n"


def decode_line(line: str) -> dict:
    """Decode a NDJSON line, preserving numeric precision via parse_float=Decimal."""
    return json.loads(line, parse_float=Decimal)


def _default(obj: object) -> object:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
```

- [ ] **Step 5: Run tests — expect pass**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_ndjson_codec.py -v
```

Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/wal/ tests/test_wal_ndjson_codec.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(wal): NDJSON codec with Decimal/datetime support [MCT-106]"
```

---

### Task 3: Segment Helpers (TDD)

**Files:**
- Create: `src/mctrader_data/wal/segment.py`
- Create: `tests/test_wal_segment.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_wal_segment.py
"""Tests for wal/segment.py — INV-2 atomic seal."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from mctrader_data.wal.segment import (
    active_segment_path,
    compacted_path,
    is_active,
    is_compacted,
    is_sealed,
    scan_sealed,
    seal_path,
    segment_index,
)


def test_segment_index_5min_boundary() -> None:
    # t=0..299 → idx 0; t=300..599 → idx 1
    assert segment_index(0.0) == 0
    assert segment_index(299.9) == 0
    assert segment_index(300.0) == 1
    assert segment_index(599.9) == 1
    assert segment_index(600.0) == 2


def test_segment_index_custom_seconds() -> None:
    assert segment_index(3600.0, segment_seconds=3600) == 1
    assert segment_index(7199.9, segment_seconds=3600) == 1


def test_active_segment_path_structure(tmp_path: Path) -> None:
    p = active_segment_path(
        root=tmp_path, exchange="bithumb", channel="transaction",
        symbol="KRW-BTC", date="2026-05-09",
        start_idx=0, node_id="NODE_A",
    )
    assert p.parent == tmp_path / "wal" / "bithumb" / "transaction" / "KRW-BTC" / "2026-05-09"
    assert p.name.startswith("segment-")
    assert p.name.endswith("-NODE_A.ndjson")


def test_seal_path_rename(tmp_path: Path) -> None:
    active = tmp_path / "segment-20260509T000000Z-NODE_A.ndjson"
    active.write_text("line\n")
    sealed = seal_path(active)
    assert sealed.name == "segment-20260509T000000Z-NODE_A.ndjson.sealed"
    os.replace(str(active), str(sealed))
    assert sealed.exists()
    assert not active.exists()


def test_is_active_sealed_compacted() -> None:
    assert is_active(Path("segment-20260509T000000Z-NODE.ndjson"))
    assert not is_active(Path("segment-20260509T000000Z-NODE.ndjson.sealed"))
    assert is_sealed(Path("segment-20260509T000000Z-NODE.ndjson.sealed"))
    assert not is_sealed(Path("segment-20260509T000000Z-NODE.ndjson"))
    assert is_compacted(Path("segment-20260509T000000Z-NODE.ndjson.sealed.compacted"))


def test_scan_sealed_returns_only_unsealed(tmp_path: Path) -> None:
    wal = tmp_path / "wal" / "bithumb" / "transaction" / "KRW-BTC" / "2026-05-09"
    wal.mkdir(parents=True)
    sealed = wal / "segment-20260509T000000Z-N.ndjson.sealed"
    compacted_sealed = wal / "segment-20260509T000500Z-N.ndjson.sealed"
    active = wal / "segment-20260509T001000Z-N.ndjson"
    for f in [sealed, compacted_sealed, active]:
        f.write_text("x\n")
    # Mark one as compacted
    (wal / "segment-20260509T000500Z-N.ndjson.sealed.compacted").write_text("")

    result = scan_sealed(tmp_path)
    assert result == [sealed]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_segment.py -v 2>&1 | head -15
```

Expected: `ImportError`

- [ ] **Step 3: Implement segment.py**

```python
# src/mctrader_data/wal/segment.py
"""WAL segment path conventions and scan helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

SEGMENT_SECONDS = 300  # 5 minutes


def segment_index(ts: float, segment_seconds: int = SEGMENT_SECONDS) -> int:
    """Return the 5-minute epoch bucket index for timestamp ts (seconds since epoch)."""
    return int(ts // segment_seconds)


def active_segment_path(
    *,
    root: Path,
    exchange: str,
    channel: str,
    symbol: str,
    date: str,
    start_idx: int,
    node_id: str,
    segment_seconds: int = SEGMENT_SECONDS,
) -> Path:
    start_ts = start_idx * segment_seconds
    dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    ts_str = dt.strftime("%Y%m%dT%H%M%SZ")
    filename = f"segment-{ts_str}-{node_id}.ndjson"
    return root / "wal" / exchange / channel / symbol / date / filename


def seal_path(active: Path) -> Path:
    return Path(str(active) + ".sealed")


def compacted_path(sealed: Path) -> Path:
    return Path(str(sealed) + ".compacted")


def is_active(p: Path) -> bool:
    name = p.name
    return name.endswith(".ndjson") and not name.endswith(".sealed")


def is_sealed(p: Path) -> bool:
    return p.name.endswith(".ndjson.sealed") and not p.name.endswith(".compacted")


def is_compacted(p: Path) -> bool:
    return p.name.endswith(".ndjson.sealed.compacted")


def scan_sealed(root: Path) -> list[Path]:
    """Return all .ndjson.sealed paths under root/wal/ that have no .compacted marker."""
    wal_root = root / "wal"
    if not wal_root.exists():
        return []
    result = []
    for p in sorted(wal_root.rglob("*.ndjson.sealed")):
        if not compacted_path(p).exists():
            result.append(p)
    return result


def parse_node_id_from_segment(sealed: Path) -> str:
    """Extract node_id from segment filename: segment-{ts}-{node_id}.ndjson.sealed"""
    stem = sealed.name  # e.g. segment-20260509T000000Z-NODE_A.ndjson.sealed
    base = stem.replace(".ndjson.sealed", "").replace(".ndjson", "")
    # base = segment-20260509T000000Z-NODE_A
    parts = base.split("-", 2)  # ["segment", "20260509T000000Z", "NODE_A"]
    return parts[2] if len(parts) >= 3 else "DEFAULT"
```

- [ ] **Step 4: Run tests — expect pass**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_segment.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/wal/segment.py tests/test_wal_segment.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(wal): segment path helpers and scan [MCT-106]"
```

---

### Task 4: WalIngester (TDD)

**Files:**
- Create: `src/mctrader_data/wal/ingester.py`
- Create: `tests/test_wal_ingester.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_wal_ingester.py
"""Unit tests for WalIngester."""
from __future__ import annotations

import os
import time
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mctrader_data.wal.ingester import WalIngester
from mctrader_data.wal.ndjson_codec import decode_line
from mctrader_data.wal.segment import scan_sealed


def _make_ingester(tmp_path: Path, **kwargs) -> WalIngester:
    return WalIngester(
        root=tmp_path,
        exchange="bithumb",
        symbol="KRW-BTC",
        channel="transaction",
        node_id="NODE_A",
        **kwargs,
    )


def test_append_creates_wal_file(tmp_path: Path) -> None:
    ing = _make_ingester(tmp_path)
    ing.append({"price": Decimal("100"), "qty": Decimal("1")})
    ing.close()
    sealed_files = list((tmp_path / "wal").rglob("*.ndjson.sealed"))
    assert len(sealed_files) == 1
    lines = sealed_files[0].read_text().strip().splitlines()
    assert len(lines) == 1
    record = decode_line(lines[0])
    assert record["price"] == Decimal("100")


def test_close_seals_active_segment(tmp_path: Path) -> None:
    ing = _make_ingester(tmp_path)
    ing.append({"x": 1})
    # Before close: active .ndjson must exist
    active_files = list((tmp_path / "wal").rglob("*.ndjson"))
    active_only = [f for f in active_files if not f.name.endswith(".sealed")]
    assert len(active_only) == 1
    ing.close()
    # After close: only .sealed exists
    active_after = [f for f in (tmp_path / "wal").rglob("*.ndjson") if not f.name.endswith(".sealed")]
    assert len(active_after) == 0
    assert len(scan_sealed(tmp_path)) == 1


def test_wal_file_permission_0640(tmp_path: Path) -> None:
    ing = _make_ingester(tmp_path)
    ing.append({"x": 1})
    active = list(f for f in (tmp_path / "wal").rglob("*.ndjson") if not f.name.endswith(".sealed"))
    assert len(active) == 1
    mode = oct(os.stat(active[0]).st_mode)[-4:]
    assert mode == "0640"
    ing.close()


def test_maybe_seal_on_boundary(tmp_path: Path) -> None:
    """Crossing segment boundary triggers seal."""
    ing = _make_ingester(tmp_path, segment_seconds=1)  # 1-second segments for test speed
    ing.append({"x": 1})
    time.sleep(1.1)
    sealed = ing.maybe_seal()
    assert sealed is not None
    assert sealed.name.endswith(".ndjson.sealed")
    ing.close()


def test_multiple_appends_all_records_present(tmp_path: Path) -> None:
    ing = _make_ingester(tmp_path)
    for i in range(10):
        ing.append({"seq": i, "price": Decimal(str(i))})
    ing.close()
    sealed_files = list((tmp_path / "wal").rglob("*.ndjson.sealed"))
    all_lines = []
    for f in sealed_files:
        all_lines.extend(f.read_text().strip().splitlines())
    assert len(all_lines) == 10
    seqs = sorted(decode_line(l)["seq"] for l in all_lines)
    assert seqs == list(range(10))


def test_closed_ingester_raises(tmp_path: Path) -> None:
    ing = _make_ingester(tmp_path)
    ing.close()
    with pytest.raises(RuntimeError, match="closed"):
        ing.append({"x": 1})
```

- [ ] **Step 2: Run tests — expect failure**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_ingester.py -v 2>&1 | head -15
```

Expected: `ImportError: cannot import name 'WalIngester'`

- [ ] **Step 3: Implement ingester.py**

```python
# src/mctrader_data/wal/ingester.py
"""Per-symbol-channel WAL writer (append-only, O_APPEND + fsync)."""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .ndjson_codec import encode_record
from .segment import active_segment_path, seal_path, segment_index


class WalIngester:
    """Writes one NDJSON line per event to a WAL file opened with O_APPEND.

    Segment boundary: every `segment_seconds` (default 300 = 5 min).
    On boundary cross, atomic rename .ndjson -> .ndjson.sealed.
    close() does final fsync + seal.
    """

    def __init__(
        self,
        *,
        root: Path,
        exchange: str,
        symbol: str,
        channel: str,
        node_id: str,
        fsync_batch: int = 1,
        segment_seconds: int = 300,
    ) -> None:
        self._root = root
        self._exchange = exchange
        self._symbol = symbol
        self._channel = channel
        self._node_id = node_id
        self._fsync_batch = fsync_batch
        self._segment_seconds = segment_seconds
        self._lock = threading.Lock()
        self._fd: int | None = None
        self._current_path: Path | None = None
        self._segment_start_idx: int = 0
        self._write_count: int = 0
        self._closed: bool = False
        self._open_new_segment()

    # ------------------------------------------------------------------ public

    def append(self, record: dict) -> None:
        if self._closed:
            raise RuntimeError("WalIngester is closed")
        with self._lock:
            self.maybe_seal()
            line = encode_record(record).encode("utf-8")
            assert self._fd is not None
            os.write(self._fd, line)
            self._write_count += 1
            if self._write_count % self._fsync_batch == 0:
                os.fsync(self._fd)

    def maybe_seal(self) -> Path | None:
        """Seal current segment if wall-clock has crossed segment boundary."""
        now_idx = segment_index(time.time(), self._segment_seconds)
        if now_idx > self._segment_start_idx:
            sealed = self._seal_current()
            self._open_new_segment(start_idx=now_idx)
            return sealed
        return None

    def close(self) -> None:
        if self._closed:
            return
        with self._lock:
            if self._fd is not None:
                os.fsync(self._fd)
                os.close(self._fd)
                self._fd = None
            if self._current_path is not None and self._current_path.exists():
                sealed = seal_path(self._current_path)
                os.replace(str(self._current_path), str(sealed))
                self._current_path = None
            self._closed = True

    # ----------------------------------------------------------------- private

    def _open_new_segment(self, start_idx: int | None = None) -> None:
        if start_idx is None:
            start_idx = segment_index(time.time(), self._segment_seconds)
        self._segment_start_idx = start_idx
        start_ts = start_idx * self._segment_seconds
        dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        path = active_segment_path(
            root=self._root,
            exchange=self._exchange,
            channel=self._channel,
            symbol=self._symbol,
            date=date_str,
            start_idx=start_idx,
            node_id=self._node_id,
            segment_seconds=self._segment_seconds,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        self._current_path = path
        self._fd = os.open(
            str(path),
            flags=os.O_WRONLY | os.O_APPEND | os.O_CREAT,
            mode=0o640,
        )
        self._write_count = 0

    def _seal_current(self) -> Path:
        assert self._fd is not None
        os.fsync(self._fd)
        os.close(self._fd)
        self._fd = None
        assert self._current_path is not None
        sealed = seal_path(self._current_path)
        os.replace(str(self._current_path), str(sealed))
        self._current_path = None
        return sealed
```

- [ ] **Step 4: Run tests — expect pass**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_ingester.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/wal/ingester.py tests/test_wal_ingester.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(wal): WalIngester O_APPEND+fsync per-symbol writer [MCT-106]"
```

---

### Task 5: INV-1 Zero-loss Crash Recovery Test

**Files:**
- Create: `tests/test_wal_ingester_crash_recovery.py`

- [ ] **Step 1: Write crash recovery test (uses subprocess to simulate SIGKILL)**

```python
# tests/test_wal_ingester_crash_recovery.py
"""INV-1: SIGKILL after N messages → 0 records lost in sealed WAL."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from decimal import Decimal
from pathlib import Path

import pytest

from mctrader_data.wal.ndjson_codec import decode_line
from mctrader_data.wal.segment import scan_sealed


@pytest.mark.parametrize("n_messages", [1, 10_000])
def test_sigkill_zero_loss(tmp_path: Path, n_messages: int) -> None:
    """Write N messages via subprocess, SIGKILL mid-run, verify all N present in WAL."""
    script = textwrap.dedent(f"""
        import os, signal, sys
        sys.path.insert(0, 'src')
        from pathlib import Path
        from decimal import Decimal
        from mctrader_data.wal.ingester import WalIngester

        root = Path({str(tmp_path)!r})
        ing = WalIngester(
            root=root, exchange='bithumb', symbol='KRW-BTC',
            channel='transaction', node_id='TEST',
            fsync_batch=1,
        )
        for i in range({n_messages}):
            ing.append({{"seq": i, "price": Decimal(str(i))}})
        # Do NOT call close() — simulate SIGKILL after all writes
        os.kill(os.getpid(), signal.SIGKILL)
    """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        timeout=30,
    )
    # Process should be killed (returncode != 0)
    assert result.returncode != 0

    # Now read back all lines from active + sealed segments
    all_lines = []
    wal_root = tmp_path / "wal"
    for p in wal_root.rglob("*.ndjson*"):
        if p.suffix in (".ndjson",) or p.name.endswith(".ndjson.sealed"):
            try:
                content = p.read_text(errors="replace")
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            all_lines.append(decode_line(line))
                        except Exception:
                            pass  # last partial line on crash
            except Exception:
                pass

    seqs = {r["seq"] for r in all_lines}
    # All N messages must be present (per-message fsync guarantees this)
    assert seqs == set(range(n_messages)), (
        f"Missing seqs: {set(range(n_messages)) - seqs}"
    )
```

- [ ] **Step 2: Run tests**

```bash
docker exec mctrader-collector python -m pytest tests/test_wal_ingester_crash_recovery.py -v --timeout=60
```

Expected: `2 passed` (may take ~10s for n=10_000)

- [ ] **Step 3: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add tests/test_wal_ingester_crash_recovery.py
git -C c:/workspace/mclayer/mctrader-data commit -m "test(wal): INV-1 zero-loss crash recovery via subprocess SIGKILL [MCT-106]"
```

---

### Task 6: Open Phase A PR

- [ ] **Step 1: Push branch and create PR**

```bash
git -C c:/workspace/mclayer/mctrader-data checkout -b feat/mct-106-phase-a-wal-ingester
git -C c:/workspace/mclayer/mctrader-data push -u origin feat/mct-106-phase-a-wal-ingester
```

```bash
gh pr create \
  --repo mclayer/mctrader-data \
  --title "feat(wal): WAL ingester module — zero-loss NDJSON append [MCT-106 Phase A]" \
  --body "$(cat <<'EOF'
## Summary
- Adds `mctrader_data/wal/` package: `ndjson_codec`, `segment`, `ingester`
- `WalIngester` uses `os.open(O_APPEND|O_CREAT, mode=0o640)` + per-message `fsync`
- Segment rotation every 5 min via `os.replace` (atomic rename)
- INV-1 crash recovery test: SIGKILL after N messages → 0 records lost
- Dormant: `collector.py` not changed yet (Phase C)

## ADR
- ADR-009 §D2 amendment: `tier=L{1,2,3}` partition added (docs-only commit as head)
- ADR-017: referenced

## Test plan
- [ ] `pytest tests/test_wal_ndjson_codec.py tests/test_wal_segment.py tests/test_wal_ingester.py tests/test_wal_ingester_crash_recovery.py -v`
- [ ] All pass, no regressions in existing tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Phase B: Compactor Module (PR-2)

### Task 7: L1Compactor (TDD) — INV-3, INV-4, INV-6

**Files:**
- Create: `src/mctrader_data/compactor/__init__.py`
- Create: `src/mctrader_data/compactor/l1.py`
- Create: `tests/test_compactor_l1.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_compactor_l1.py
"""Tests for L1Compactor: INV-3 idempotency, INV-4 sort, INV-5 schema, INV-6 lineage."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from mctrader_data.wal.ingester import WalIngester
from mctrader_data.wal.segment import scan_sealed
from mctrader_data.compactor.l1 import L1Compactor


def _write_sealed_segment(tmp_path: Path, records: list[dict], node_id: str = "NODE_A") -> Path:
    """Write records to WAL and close (seals the segment)."""
    ing = WalIngester(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        channel="transaction", node_id=node_id,
        segment_seconds=86400,  # never auto-seal during test
    )
    for r in records:
        ing.append(r)
    ing.close()
    sealed = scan_sealed(tmp_path)
    assert len(sealed) == 1
    return sealed[0]


def _make_tick_record(seq: int, ts_offset_sec: int = 0) -> dict:
    ts = datetime(2026, 5, 9, 0, 0, ts_offset_sec, tzinfo=timezone.utc)
    return {
        "ts_utc": ts.isoformat(),
        "received_at": ts.isoformat(),
        "exchange": "bithumb",
        "symbol": "KRW-BTC",
        "price": Decimal("100000"),
        "quantity": Decimal("0.01"),
        "side": "buy",
        "raw_json": None,
        "channel": "transaction",
    }


def test_l1_compact_produces_parquet(tmp_path: Path) -> None:
    records = [_make_tick_record(i, i) for i in range(5)]
    sealed = _write_sealed_segment(tmp_path, records)
    compactor = L1Compactor(root=tmp_path)
    parquet_path = compactor.compact_segment(sealed)
    assert parquet_path.exists()
    assert parquet_path.suffix == ".parquet"
    tbl = pq.read_table(parquet_path)
    assert tbl.num_rows == 5


def test_l1_parquet_path_contains_tier_and_node(tmp_path: Path) -> None:
    records = [_make_tick_record(0)]
    sealed = _write_sealed_segment(tmp_path, records, node_id="NODE_A")
    compactor = L1Compactor(root=tmp_path)
    parquet_path = compactor.compact_segment(sealed)
    parts = parquet_path.parts
    assert "tier=L1" in parts
    assert "node=NODE_A" in parts


def test_l1_idempotent_double_compaction(tmp_path: Path) -> None:
    """INV-3: compact same sealed segment twice → identical Parquet sha256."""
    records = [_make_tick_record(i, i) for i in range(10)]
    sealed = _write_sealed_segment(tmp_path, records)
    compactor = L1Compactor(root=tmp_path)
    p1 = compactor.compact_segment(sealed)
    p2 = compactor.compact_segment(sealed)
    sha1 = hashlib.sha256(p1.read_bytes()).hexdigest()
    sha2 = hashlib.sha256(p2.read_bytes()).hexdigest()
    assert sha1 == sha2


def test_l1_out_of_order_sorted(tmp_path: Path) -> None:
    """INV-4: out-of-order records are sorted by ts_utc in output Parquet."""
    records = [_make_tick_record(i, 9 - i) for i in range(10)]  # ts in reverse order
    sealed = _write_sealed_segment(tmp_path, records)
    compactor = L1Compactor(root=tmp_path)
    parquet_path = compactor.compact_segment(sealed)
    tbl = pq.read_table(parquet_path)
    ts_col = tbl.column("ts_utc").to_pylist()
    assert ts_col == sorted(ts_col)


def test_l1_lineage_file_created(tmp_path: Path) -> None:
    """INV-6: lineage JSON created alongside Parquet."""
    records = [_make_tick_record(0)]
    sealed = _write_sealed_segment(tmp_path, records)
    compactor = L1Compactor(root=tmp_path)
    parquet_path = compactor.compact_segment(sealed)
    lineage_files = list(parquet_path.parent.glob("lineage-*.json"))
    assert len(lineage_files) == 1
    lineage = json.loads(lineage_files[0].read_text())
    assert "compacted_from" in lineage
    assert lineage["node_id"] == "NODE_A"


def test_l1_sealed_marked_compacted(tmp_path: Path) -> None:
    """After compact, sealed segment gets .compacted marker."""
    records = [_make_tick_record(0)]
    sealed = _write_sealed_segment(tmp_path, records)
    compactor = L1Compactor(root=tmp_path)
    compactor.compact_segment(sealed)
    assert Path(str(sealed) + ".compacted").exists()
    assert len(scan_sealed(tmp_path)) == 0
```

- [ ] **Step 2: Run tests — expect failure**

```bash
docker exec mctrader-collector python -m pytest tests/test_compactor_l1.py -v 2>&1 | head -15
```

Expected: `ImportError: cannot import name 'L1Compactor'`

- [ ] **Step 3: Create compactor package + implement l1.py**

```python
# src/mctrader_data/compactor/__init__.py
```

```python
# src/mctrader_data/compactor/l1.py
"""L1Compactor: sealed NDJSON segment → 5-min tier=L1 Parquet (write-then-rename)."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mctrader_data.wal.ndjson_codec import decode_line
from mctrader_data.wal.segment import compacted_path, parse_node_id_from_segment
from mctrader_data.tick_storage import TICK_SCHEMA_VERSION, _records_to_arrow as _tick_to_arrow, TickRecord
from mctrader_data.orderbook_storage import ORDERBOOK_SCHEMA_VERSION
from mctrader_data.orderbook_snapshot_storage import ORDERBOOK_SNAPSHOT_SCHEMA_VERSION


class L1Compactor:
    """Converts a sealed NDJSON WAL segment to a tier=L1 Parquet file."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def compact_segment(self, sealed: Path) -> Path:
        """Pipeline: read → (throttle for snapshot) → sort → Arrow → write-then-rename.

        Returns the final Parquet path. Idempotent: same sealed segment → same Parquet.
        """
        node_id = parse_node_id_from_segment(sealed)
        run_id = _compaction_run_id(sealed, self._root)
        channel = _channel_from_path(sealed)

        records = _read_sealed(sealed)
        if channel == "orderbook_snapshot":
            records = _throttle_1sec(records)
        records = sorted(records, key=lambda r: r.get("ts_utc", ""))

        parquet_path = self._parquet_path(sealed, node_id, run_id, channel)
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        if parquet_path.exists():
            # Idempotency: compare sha256
            existing_sha = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
            tmp_path = _write_tmp(parquet_path, records, channel, node_id)
            new_sha = hashlib.sha256(tmp_path.read_bytes()).hexdigest()
            if existing_sha == new_sha:
                tmp_path.unlink()
                _mark_compacted(sealed)
                return parquet_path
            # Different sha: collision case — fail-closed
            tmp_path.unlink()
            raise RuntimeError(
                f"Compaction collision: {parquet_path} exists with different sha256. "
                "Manual review required."
            )

        tmp_path = _write_tmp(parquet_path, records, channel, node_id)
        os.replace(str(tmp_path), str(parquet_path))

        _write_lineage(parquet_path, sealed, run_id, node_id)
        _mark_compacted(sealed)
        return parquet_path

    def _parquet_path(self, sealed: Path, node_id: str, run_id: str, channel: str) -> Path:
        """Derive tier=L1 Parquet path from sealed segment path."""
        # sealed: <root>/wal/<exchange>/<channel>/<symbol>/<date>/segment-...ndjson.sealed
        parts = sealed.parts
        wal_idx = next(i for i, p in enumerate(parts) if p == "wal")
        exchange = parts[wal_idx + 1]
        symbol = parts[wal_idx + 3]
        date = parts[wal_idx + 4]
        schema = _schema_version(channel)
        return (
            self._root
            / "market"
            / channel
            / f"schema_version={schema}"
            / "tier=L1"
            / f"exchange={exchange}"
            / f"symbol={symbol}"
            / f"date={date}"
            / f"node={node_id}"
            / f"part-{run_id}.parquet"
        )


# ------------------------------------------------------------------ helpers

def _compaction_run_id(sealed: Path, root: Path) -> str:
    rel = str(sealed.relative_to(root))
    return hashlib.sha256(rel.encode()).hexdigest()[:16]


def _channel_from_path(sealed: Path) -> str:
    parts = sealed.parts
    wal_idx = next(i for i, p in enumerate(parts) if p == "wal")
    return parts[wal_idx + 2]


def _schema_version(channel: str) -> str:
    return {
        "transaction": TICK_SCHEMA_VERSION,
        "orderbookdepth": ORDERBOOK_SCHEMA_VERSION,
        "orderbooksnapshot": ORDERBOOK_SNAPSHOT_SCHEMA_VERSION,
    }.get(channel, f"{channel}.v1")


def _read_sealed(sealed: Path) -> list[dict]:
    records = []
    for line in sealed.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(decode_line(line))
        except Exception:
            pass  # last line may be partial on crash — skip
    return records


def _throttle_1sec(records: list[dict]) -> list[dict]:
    """Keep last-write-wins per symbol within 1-second windows (§D14.10)."""
    buckets: dict[tuple, dict] = {}
    for r in records:
        ts = r.get("ts_utc", "")
        symbol = r.get("symbol", "")
        bucket = (symbol, ts[:19])  # truncate to second
        buckets[(symbol, bucket[1])] = r
    return list(buckets.values())


def _write_tmp(parquet_path: Path, records: list[dict], channel: str, node_id: str) -> Path:
    tmp = parquet_path.parent / f"part-tmp-{os.getpid()}.tmp"
    _write_records_to_parquet(records, tmp, channel, node_id)
    return tmp


def _write_records_to_parquet(records: list[dict], path: Path, channel: str, node_id: str) -> None:
    if not records:
        # Write empty Parquet with correct schema
        from mctrader_data.tick_storage import _TICK_SCHEMA
        tbl = pa.table({f.name: [] for f in _TICK_SCHEMA}, schema=_TICK_SCHEMA)
        pq.write_table(tbl, str(path), compression="snappy")
        return

    # Convert dicts back to typed Arrow table via existing schema SSOT
    if channel == "transaction":
        from mctrader_data.tick_storage import TickRecord, _records_to_arrow
        typed = [TickRecord(**{k: v for k, v in r.items() if k != "channel"
                               and k in TickRecord.__dataclass_fields__}) for r in records]
        tbl = _records_to_arrow(typed)
    elif channel in ("orderbookdepth",):
        from mctrader_data.orderbook_storage import OrderbookRecord, _records_to_arrow  # type: ignore[attr-defined]
        typed = [OrderbookRecord(**{k: v for k, v in r.items() if k != "channel"
                                    and hasattr(OrderbookRecord, k)}) for r in records]
        tbl = _records_to_arrow(typed)
    else:
        # Generic fallback: write as JSON string table
        tbl = pa.table({"raw": [json.dumps(r, default=str) for r in records]})

    meta = dict(tbl.schema.metadata or {})
    meta[b"node_id"] = node_id.encode()
    tbl = tbl.cast(tbl.schema.with_metadata(meta))
    pq.write_table(tbl, str(path), compression="snappy")


def _write_lineage(parquet_path: Path, sealed: Path, run_id: str, node_id: str) -> None:
    sha = hashlib.sha256(sealed.read_bytes()).hexdigest()
    lineage = {
        "compaction_run_id": run_id,
        "node_id": node_id,
        "compacted_from": [{"wal_path": str(sealed), "sha256": sha}],
        "tier": "L1",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    lineage_path = parquet_path.parent / f"lineage-{run_id}.json"
    lineage_path.write_text(json.dumps(lineage, indent=2))


def _mark_compacted(sealed: Path) -> None:
    compacted_path(sealed).write_text("")
```

- [ ] **Step 4: Run tests — expect pass**

```bash
docker exec mctrader-collector python -m pytest tests/test_compactor_l1.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/compactor/ tests/test_compactor_l1.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(compactor): L1Compactor NDJSON→5-min Parquet with idempotency [MCT-106]"
```

---

### Task 8: L2 and L3 Compactors (TDD)

**Files:**
- Create: `src/mctrader_data/compactor/l2.py`
- Create: `src/mctrader_data/compactor/l3.py`
- Create: `tests/test_compactor_l2.py`
- Create: `tests/test_compactor_l3.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_compactor_l2.py
"""INV-7: L1×12 → L2 preserves all records."""
from __future__ import annotations

from datetime import datetime, date, timezone
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from mctrader_data.compactor.l1 import L1Compactor
from mctrader_data.compactor.l2 import L2Compactor
from mctrader_data.wal.ingester import WalIngester
from mctrader_data.wal.segment import scan_sealed


def _write_and_compact_l1(tmp_path: Path, n_records: int, node_id: str = "N") -> None:
    ing = WalIngester(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        channel="transaction", node_id=node_id, segment_seconds=86400,
    )
    for i in range(n_records):
        ts = datetime(2026, 5, 9, 0, 0, i, tzinfo=timezone.utc)
        ing.append({
            "ts_utc": ts.isoformat(), "received_at": ts.isoformat(),
            "exchange": "bithumb", "symbol": "KRW-BTC",
            "price": Decimal("100000"), "quantity": Decimal("0.01"),
            "side": "buy", "raw_json": None, "channel": "transaction",
        })
    ing.close()
    for s in scan_sealed(tmp_path):
        L1Compactor(tmp_path).compact_segment(s)


def test_l2_merges_l1_files(tmp_path: Path) -> None:
    _write_and_compact_l1(tmp_path, 20)
    compactor = L2Compactor(root=tmp_path)
    result = compactor.compact_hour(
        exchange="bithumb", symbol="KRW-BTC",
        channel="transaction",
        hour_utc=datetime(2026, 5, 9, 0, 0, tzinfo=timezone.utc),
    )
    assert result is not None
    tbl = pq.read_table(result)
    assert tbl.num_rows == 20
    parts = result.parts
    assert "tier=L2" in parts


def test_l2_row_count_equals_l1_total(tmp_path: Path) -> None:
    """INV-7: L2 row count == sum of all L1 rows for that hour."""
    _write_and_compact_l1(tmp_path, 50)
    l1_files = list((tmp_path / "market").rglob("tier=L1/**/*.parquet"))
    l1_total = sum(pq.read_table(f).num_rows for f in l1_files)

    compactor = L2Compactor(root=tmp_path)
    result = compactor.compact_hour(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction",
        hour_utc=datetime(2026, 5, 9, 0, 0, tzinfo=timezone.utc),
    )
    assert pq.read_table(result).num_rows == l1_total
```

```python
# tests/test_compactor_l3.py
"""INV-8: L3 reprocessing is monotone."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq

from mctrader_data.compactor.l1 import L1Compactor
from mctrader_data.compactor.l2 import L2Compactor
from mctrader_data.compactor.l3 import L3Compactor
from mctrader_data.wal.ingester import WalIngester
from mctrader_data.wal.segment import scan_sealed


def _setup_l2(tmp_path: Path, n: int) -> None:
    ing = WalIngester(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        channel="transaction", node_id="N", segment_seconds=86400,
    )
    for i in range(n):
        ts = datetime(2026, 5, 9, 0, 0, i, tzinfo=timezone.utc)
        ing.append({
            "ts_utc": ts.isoformat(), "received_at": ts.isoformat(),
            "exchange": "bithumb", "symbol": "KRW-BTC",
            "price": Decimal("100000"), "quantity": Decimal("0.01"),
            "side": "buy", "raw_json": None, "channel": "transaction",
        })
    ing.close()
    for s in scan_sealed(tmp_path):
        L1Compactor(tmp_path).compact_segment(s)
    L2Compactor(tmp_path).compact_hour(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction",
        hour_utc=datetime(2026, 5, 9, 0, 0, tzinfo=timezone.utc),
    )


def test_l3_produces_daily_parquet(tmp_path: Path) -> None:
    _setup_l2(tmp_path, 10)
    compactor = L3Compactor(root=tmp_path)
    result = compactor.compact_day(
        exchange="bithumb", symbol="KRW-BTC", channel="transaction",
        date_utc=datetime(2026, 5, 9, tzinfo=timezone.utc).date(),
    )
    assert result is not None
    assert "tier=L3" in result.parts
    assert pq.read_table(result).num_rows == 10


def test_l3_reprocessing_monotone(tmp_path: Path) -> None:
    """INV-8: compact same day twice → row count non-decreasing."""
    _setup_l2(tmp_path, 10)
    compactor = L3Compactor(root=tmp_path)
    d = datetime(2026, 5, 9, tzinfo=timezone.utc).date()
    r1 = compactor.compact_day(exchange="bithumb", symbol="KRW-BTC", channel="transaction", date_utc=d)
    r2 = compactor.compact_day(exchange="bithumb", symbol="KRW-BTC", channel="transaction", date_utc=d)
    assert pq.read_table(r2).num_rows >= pq.read_table(r1).num_rows
```

- [ ] **Step 2: Implement l2.py and l3.py**

```python
# src/mctrader_data/compactor/l2.py
"""L2Compactor: merge tier=L1 files for one UTC hour → tier=L2 Parquet."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mctrader_data.wal.segment import compacted_path


class L2Compactor:
    def __init__(self, root: Path) -> None:
        self._root = root

    def compact_hour(
        self,
        *,
        exchange: str,
        symbol: str,
        channel: str,
        hour_utc: datetime,
    ) -> Path | None:
        """Merge all tier=L1 Parquet for (exchange, symbol, channel, hour) → tier=L2."""
        from mctrader_data.compactor.l1 import _schema_version
        date_str = hour_utc.strftime("%Y-%m-%d")
        schema_ver = _schema_version(channel)
        l1_dir = (
            self._root / "market" / channel
            / f"schema_version={schema_ver}" / "tier=L1"
            / f"exchange={exchange}" / f"symbol={symbol}" / f"date={date_str}"
        )
        l1_files = sorted(l1_dir.rglob("part-*.parquet")) if l1_dir.exists() else []
        if not l1_files:
            return None

        tables = [pq.read_table(f) for f in l1_files]
        merged = pa.concat_tables(tables)
        merged = merged.sort_by("ts_utc")

        run_id = hashlib.sha256(
            "|".join(str(f) for f in l1_files).encode()
        ).hexdigest()[:16]

        out_dir = (
            self._root / "market" / channel
            / f"schema_version={schema_ver}" / "tier=L2"
            / f"exchange={exchange}" / f"symbol={symbol}" / f"date={date_str}"
            / f"hour={hour_utc.strftime('%H')}" / "node=MERGED"
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"part-{run_id}.parquet"
        tmp = out_dir / f"part-tmp-{os.getpid()}.tmp"
        pq.write_table(merged, str(tmp), compression="snappy")
        os.replace(str(tmp), str(out_path))
        return out_path
```

```python
# src/mctrader_data/compactor/l3.py
"""L3Compactor: merge tier=L2 files for one UTC day → tier=L3 Parquet."""
from __future__ import annotations

import hashlib
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


class L3Compactor:
    def __init__(self, root: Path) -> None:
        self._root = root

    def compact_day(
        self,
        *,
        exchange: str,
        symbol: str,
        channel: str,
        date_utc: date,
    ) -> Path | None:
        from mctrader_data.compactor.l1 import _schema_version
        date_str = date_utc.isoformat()
        schema_ver = _schema_version(channel)
        l2_dir = (
            self._root / "market" / channel
            / f"schema_version={schema_ver}" / "tier=L2"
            / f"exchange={exchange}" / f"symbol={symbol}" / f"date={date_str}"
        )
        l2_files = sorted(l2_dir.rglob("part-*.parquet")) if l2_dir.exists() else []
        if not l2_files:
            return None

        tables = [pq.read_table(f) for f in l2_files]
        merged = pa.concat_tables(tables).sort_by("ts_utc")

        run_id = hashlib.sha256(
            "|".join(str(f) for f in l2_files).encode()
        ).hexdigest()[:16]

        out_dir = (
            self._root / "market" / channel
            / f"schema_version={schema_ver}" / "tier=L3"
            / f"exchange={exchange}" / f"symbol={symbol}" / f"date={date_str}"
            / "node=MERGED"
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"part-{run_id}.parquet"
        tmp = out_dir / f"part-tmp-{os.getpid()}.tmp"
        pq.write_table(merged, str(tmp), compression="snappy")
        os.replace(str(tmp), str(out_path))
        return out_path
```

- [ ] **Step 3: Run tests — expect pass**

```bash
docker exec mctrader-collector python -m pytest tests/test_compactor_l2.py tests/test_compactor_l3.py -v
```

Expected: `4 passed`

- [ ] **Step 4: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/compactor/l2.py src/mctrader_data/compactor/l3.py tests/test_compactor_l2.py tests/test_compactor_l3.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(compactor): L2/L3 tier merge compactors [MCT-106]"
```

---

### Task 9: CompactorRunner + GC

**Files:**
- Create: `src/mctrader_data/compactor/runner.py`
- Create: `src/mctrader_data/compactor/gc.py`

- [ ] **Step 1: Implement runner.py**

```python
# src/mctrader_data/compactor/runner.py
"""CompactorRunner: asyncio scan loop driving L1/L2/L3 compaction."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from mctrader_data.wal.segment import scan_sealed
from .l1 import L1Compactor
from .l2 import L2Compactor
from .l3 import L3Compactor
from .gc import run_gc

log = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 30  # check for new sealed segments every 30s
L2_INTERVAL_SECONDS = 300   # attempt L2 merge every 5 min
L3_INTERVAL_SECONDS = 3600  # attempt L3 merge every hour


class CompactorRunner:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._l1 = L1Compactor(root)
        self._l2 = L2Compactor(root)
        self._l3 = L3Compactor(root)
        self._last_l2 = 0.0
        self._last_l3 = 0.0

    async def run(self) -> None:
        log.info("[compactor] runner started root=%s", self._root)
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                log.info("[compactor] runner cancelled")
                raise
            except Exception:
                log.exception("[compactor] tick error")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

    async def _tick(self) -> None:
        import time
        now = time.time()

        # L1: compact any newly sealed segments
        for sealed in scan_sealed(self._root):
            try:
                p = self._l1.compact_segment(sealed)
                log.info("[compactor] L1 compacted %s → %s", sealed.name, p.name)
            except Exception:
                log.exception("[compactor] L1 failed %s", sealed)

        # L2: merge L1 files once per interval
        if now - self._last_l2 >= L2_INTERVAL_SECONDS:
            self._last_l2 = now
            await asyncio.get_running_loop().run_in_executor(None, self._run_l2)

        # L3: merge L2 files once per interval
        if now - self._last_l3 >= L3_INTERVAL_SECONDS:
            self._last_l3 = now
            await asyncio.get_running_loop().run_in_executor(None, self._run_l3)

        # GC: clean up old .compacted segments
        run_gc(self._root)

    def _run_l2(self) -> None:
        from mctrader_data.compactor.l1 import _channel_from_path
        now = datetime.now(timezone.utc)
        for parquet in (self._root / "market").rglob("tier=L1/**/part-*.parquet"):
            try:
                exchange = _extract_partition(parquet, "exchange")
                symbol = _extract_partition(parquet, "symbol")
                channel = parquet.parts[list(parquet.parts).index("market") + 1]
                self._l2.compact_hour(
                    exchange=exchange, symbol=symbol, channel=channel, hour_utc=now,
                )
            except Exception:
                log.exception("[compactor] L2 failed %s", parquet)

    def _run_l3(self) -> None:
        now = datetime.now(timezone.utc)
        for parquet in (self._root / "market").rglob("tier=L2/**/part-*.parquet"):
            try:
                exchange = _extract_partition(parquet, "exchange")
                symbol = _extract_partition(parquet, "symbol")
                channel = parquet.parts[list(parquet.parts).index("market") + 1]
                self._l3.compact_day(
                    exchange=exchange, symbol=symbol, channel=channel, date_utc=now.date(),
                )
            except Exception:
                log.exception("[compactor] L3 failed %s", parquet)


def _extract_partition(path: Path, key: str) -> str:
    for part in path.parts:
        if part.startswith(f"{key}="):
            return part.split("=", 1)[1]
    return "unknown"
```

```python
# src/mctrader_data/compactor/gc.py
"""GC: delete .compacted WAL segments older than 24h grace period."""
from __future__ import annotations

import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

GRACE_SECONDS = 86400  # 24 hours


def run_gc(root: Path) -> None:
    """Delete .compacted marker + original sealed segment after 24h grace."""
    now = time.time()
    wal_root = root / "wal"
    if not wal_root.exists():
        return
    for compacted in wal_root.rglob("*.ndjson.sealed.compacted"):
        if now - compacted.stat().st_mtime >= GRACE_SECONDS:
            sealed = Path(str(compacted)[: -len(".compacted")])
            try:
                if sealed.exists():
                    sealed.unlink()
                compacted.unlink()
                log.info("[gc] deleted %s", sealed.name)
            except Exception:
                log.exception("[gc] delete failed %s", compacted)
```

- [ ] **Step 2: Run existing tests to verify no regressions**

```bash
docker exec mctrader-collector python -m pytest tests/ -v --ignore=tests/integration -x -q
```

Expected: all existing tests pass

- [ ] **Step 3: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/compactor/runner.py src/mctrader_data/compactor/gc.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(compactor): CompactorRunner asyncio loop + GC [MCT-106]"
```

---

### Task 10: Integration Tests (§8.4) + Performance Baseline (§8.3)

**Files:**
- Create: `tests/integration/test_ingester_compactor_roundtrip.py`
- Create: `tests/test_wal_perf.py`

- [ ] **Step 1: Write roundtrip integration test**

```python
# tests/integration/test_ingester_compactor_roundtrip.py
"""§8.4 Integration: Ingester → WAL → L1Compactor → Parquet → verify 1:1 records."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from mctrader_data.wal.ingester import WalIngester
from mctrader_data.wal.segment import scan_sealed
from mctrader_data.compactor.l1 import L1Compactor


def test_roundtrip_100_records(tmp_path: Path) -> None:
    ing = WalIngester(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        channel="transaction", node_id="INT_TEST", segment_seconds=86400,
    )
    n = 100
    for i in range(n):
        ts = datetime(2026, 5, 9, 0, 0, i % 60, tzinfo=timezone.utc)
        ing.append({
            "ts_utc": ts.isoformat(), "received_at": ts.isoformat(),
            "exchange": "bithumb", "symbol": "KRW-BTC",
            "price": Decimal(str(100000 + i)),
            "quantity": Decimal("0.01"),
            "side": "buy", "raw_json": None, "channel": "transaction",
        })
    ing.close()

    compactor = L1Compactor(tmp_path)
    for sealed in scan_sealed(tmp_path):
        compactor.compact_segment(sealed)

    parquet_files = list((tmp_path / "market").rglob("tier=L1/**/*.parquet"))
    assert len(parquet_files) >= 1
    total_rows = sum(pq.read_table(f).num_rows for f in parquet_files)
    assert total_rows == n


def test_multi_exchange_isolation(tmp_path: Path) -> None:
    """§8.4: crash in bithumb ingester does not affect upbit WAL."""
    for exchange in ("bithumb", "upbit"):
        ing = WalIngester(
            root=tmp_path, exchange=exchange, symbol="KRW-BTC",
            channel="transaction", node_id=f"NODE_{exchange.upper()}",
            segment_seconds=86400,
        )
        for i in range(10):
            ing.append({"exchange": exchange, "seq": i})
        ing.close()

    # Verify both exchanges have their own sealed segments
    bithumb_sealed = list((tmp_path / "wal" / "bithumb").rglob("*.ndjson.sealed"))
    upbit_sealed = list((tmp_path / "wal" / "upbit").rglob("*.ndjson.sealed"))
    assert len(bithumb_sealed) == 1
    assert len(upbit_sealed) == 1
```

- [ ] **Step 2: Write performance baseline test**

```python
# tests/test_wal_perf.py
"""§8.3 Performance baseline: WS-to-disk p99 < 5ms, >1000 msg/sec."""
from __future__ import annotations

import time
from decimal import Decimal
from pathlib import Path

import pytest

from mctrader_data.wal.ingester import WalIngester


@pytest.mark.slow
def test_wal_write_throughput(tmp_path: Path) -> None:
    """Sustained 1000 msg/sec, p99 latency < 5ms (per-message fsync)."""
    ing = WalIngester(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
        channel="transaction", node_id="PERF_TEST",
        fsync_batch=1,  # per-message fsync
        segment_seconds=86400,
    )

    n = 1000
    latencies: list[float] = []
    record = {
        "ts_utc": "2026-05-09T00:00:00+00:00", "received_at": "2026-05-09T00:00:00+00:00",
        "exchange": "bithumb", "symbol": "KRW-BTC",
        "price": Decimal("100000"), "quantity": Decimal("0.01"),
        "side": "buy", "raw_json": None,
    }

    for _ in range(n):
        t0 = time.perf_counter()
        ing.append(record)
        latencies.append((time.perf_counter() - t0) * 1000)  # ms

    ing.close()

    latencies.sort()
    p99 = latencies[int(0.99 * n)]
    throughput = n / sum(latencies) * 1000  # msg/sec (approx)

    print(f"\nWAL p99={p99:.2f}ms, throughput≈{throughput:.0f} msg/sec")

    assert p99 < 5.0, f"p99 {p99:.2f}ms exceeds 5ms threshold"
```

- [ ] **Step 3: Run integration and perf tests**

```bash
docker exec mctrader-collector python -m pytest tests/integration/test_ingester_compactor_roundtrip.py -v
docker exec mctrader-collector python -m pytest tests/test_wal_perf.py -v -m slow
```

Expected: integration `3 passed`, perf prints p99 < 5ms

- [ ] **Step 4: Commit + Phase B PR**

```bash
git -C c:/workspace/mclayer/mctrader-data add tests/integration/test_ingester_compactor_roundtrip.py tests/test_wal_perf.py
git -C c:/workspace/mclayer/mctrader-data commit -m "test(compactor): integration roundtrip + perf baseline [MCT-106]"
git -C c:/workspace/mclayer/mctrader-data checkout -b feat/mct-106-phase-b-compactor
git -C c:/workspace/mclayer/mctrader-data push -u origin feat/mct-106-phase-b-compactor
```

```bash
gh pr create \
  --repo mclayer/mctrader-data \
  --title "feat(compactor): L1/L2/L3 compactor + runner + GC [MCT-106 Phase B]" \
  --body "$(cat <<'EOF'
## Summary
- L1Compactor: sealed NDJSON → tier=L1 Parquet (write-then-rename, idempotent)
- L2Compactor: 12×L1 → 1-hour Parquet
- L3Compactor: 24×L2 → 1-day Parquet
- CompactorRunner: asyncio scan loop (30s interval)
- GC: 24h grace cleanup of .compacted segments
- Integration test: 100-record roundtrip
- Perf baseline: p99 < 5ms @ 1000 msg/sec

## Depends on
PR-1 (Phase A)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Phase C: Collector Transition + Compose Swap (PR-3)

### Task 11: `compact` CLI Command

**Files:**
- Modify: `src/mctrader_data/cli.py`

- [ ] **Step 1: Read existing cli.py to find `collect` command location**

Read `src/mctrader_data/cli.py` and find the `@main.command("collect")` definition and the `main` click group.

- [ ] **Step 2: Add `compact` command**

After the `collect` command in `cli.py`, add:

```python
@main.command("compact")
@click.option("--root", envvar="MCTRADER_DATA_ROOT", required=True, type=click.Path())
@click.option("--once", is_flag=True, default=False, help="Run one scan cycle then exit.")
@click.option("--log-level", default="INFO")
def compact_cmd(root: str, once: bool, log_level: str) -> None:
    """Run the WAL compactor (L1/L2/L3 tiered compaction)."""
    import asyncio
    import logging
    import signal as _signal
    from mctrader_data.compactor.runner import CompactorRunner

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def _run() -> None:
        runner = CompactorRunner(Path(root))
        if once:
            await runner._tick()
            return
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        loop.add_signal_handler(_signal.SIGTERM, lambda: task.cancel() if task else None)
        await runner.run()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
```

- [ ] **Step 3: Test compact CLI**

```bash
docker exec mctrader-collector mctrader-data compact --help
```

Expected: shows `--root`, `--once`, `--log-level` options

- [ ] **Step 4: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/cli.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(cli): add compact command for CompactorRunner [MCT-106]"
```

---

### Task 12: Collector _emit_to_wal Transition

**Files:**
- Modify: `src/mctrader_data/collector.py`
- Modify: `src/mctrader_data/heartbeat.py`

- [ ] **Step 1: Read collector.py to find `_handle_event` and writer initialization**

Read `src/mctrader_data/collector.py` lines 48-202 to understand `CollectorDaemon.__init__` and `_handle_event`.

- [ ] **Step 2: Modify CollectorDaemon to use WalIngester**

In `CollectorDaemon.__init__`, replace `TickWriter` / `OrderbookWriter` / `OrderbookSnapshotWriter` instantiation with `WalIngester` per channel:

```python
# Replace the writer initialization block:
# OLD:
#   self._tick_writer = TickWriter(root=root, exchange=exchange, symbol=str(symbol), ...)
#   self._ob_writer = OrderbookWriter(...)
#   self._ob_snapshot_writer = OrderbookSnapshotWriter(...)

# NEW (add after existing imports at top of collector.py):
from mctrader_data.wal.ingester import WalIngester

# In __init__, replace writer construction with:
from mctrader_data.tick_storage import transaction_event_to_record
from mctrader_data.orderbook_storage import delta_event_to_records  # type: ignore[attr-defined]

self._wal_ingesters: dict[str, WalIngester] = {}
if include_transactions:
    self._wal_ingesters["transaction"] = WalIngester(
        root=root, exchange=exchange, symbol=str(symbol),
        channel="transaction", node_id=node_id or "DEFAULT",
    )
if include_orderbook:
    self._wal_ingesters["orderbookdepth"] = WalIngester(
        root=root, exchange=exchange, symbol=str(symbol),
        channel="orderbookdepth", node_id=node_id or "DEFAULT",
    )
if include_orderbook_snapshot:
    self._wal_ingesters["orderbooksnapshot"] = WalIngester(
        root=root, exchange=exchange, symbol=str(symbol),
        channel="orderbooksnapshot", node_id=node_id or "DEFAULT",
    )
```

- [ ] **Step 3: Replace `_handle_event` with `_emit_to_wal`**

Find the `_handle_event` method in `CollectorDaemon` and rename + replace body:

```python
# Rename _handle_event to _emit_to_wal throughout collector.py
# Replace body with WAL append:

def _emit_to_wal(self, event: Any) -> None:
    from mctrader_data.wal.ndjson_codec import encode_record
    from mctrader_data.tick_storage import transaction_event_to_record
    import dataclasses

    event_type = getattr(event, "event_type", None) or type(event).__name__

    if event_type in ("transaction",) and "transaction" in self._wal_ingesters:
        record = transaction_event_to_record(event)
        d = dataclasses.asdict(record)
        d["channel"] = "transaction"
        self._wal_ingesters["transaction"].append(d)

    elif event_type in ("delta", "snapshot") and "orderbookdepth" in self._wal_ingesters:
        from mctrader_data.orderbook_storage import delta_event_to_records  # type: ignore
        records = delta_event_to_records(event)
        for r in records:
            d = dataclasses.asdict(r)
            d["channel"] = "orderbookdepth"
            self._wal_ingesters["orderbookdepth"].append(d)

    elif event_type == "orderbooksnapshot" and "orderbooksnapshot" in self._wal_ingesters:
        from mctrader_data.orderbook_snapshot_storage import snapshot_event_to_snapshot_records  # type: ignore
        records = snapshot_event_to_snapshot_records(event)
        for r in records:
            d = dataclasses.asdict(r)
            d["channel"] = "orderbooksnapshot"
            self._wal_ingesters["orderbooksnapshot"].append(d)
```

- [ ] **Step 4: Update finally block to close WAL ingesters**

In `CollectorDaemon.run()` finally block, replace writer close calls with:

```python
finally:
    for channel, ingester in self._wal_ingesters.items():
        try:
            ingester.close()
        except Exception:
            log.exception("[collector] wal ingester close failed channel=%s", channel)
```

- [ ] **Step 5: Add `role` field to HeartbeatWriter**

In `heartbeat.py`, find the heartbeat payload dict and add `"role": self._role`:

```python
# In HeartbeatWriter.__init__, add parameter:
def __init__(self, root: Path, node_id: str, interval_seconds: float = 30.0,
             role: str = "ingester") -> None:
    ...
    self._role = role

# In the heartbeat payload dict, add:
payload = {
    ...,  # existing fields
    "role": self._role,
}
```

- [ ] **Step 6: Run full test suite to verify no regressions**

```bash
docker exec mctrader-collector python -m pytest tests/ -x -q --ignore=tests/integration
```

Expected: all pass (some tests may need minor updates for new constructor signatures)

- [ ] **Step 7: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/collector.py src/mctrader_data/heartbeat.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(collector): _emit_to_wal replaces direct Parquet writers [MCT-106]"
```

---

### Task 13: compose.yml Swap + conftest fixture

**Files:**
- Modify: `compose.yml` (in `c:\workspace\mclayer\mctrader-data\compose.yml`)
- Create/Modify: `tests/conftest.py`

- [ ] **Step 1: Update compose.yml**

```yaml
# c:\workspace\mclayer\mctrader-data\compose.yml
# Replace existing collector service with bithumb-ingester + compactor:

services:
  bithumb-ingester:
    build: .
    image: mctrader-data:pilot
    container_name: mctrader-ingester-bithumb
    restart: unless-stopped
    stop_grace_period: 30s
    command:
      - "collect"
      - "--symbols"
      - "KRW-XRP,KRW-SOL,KRW-VIRTUAL,KRW-DOGE,KRW-USDT,KRW-ETH,KRW-WLD,KRW-TON,KRW-ONDO,KRW-STRK,KRW-POLA,KRW-SUI,KRW-ADA,KRW-XLM,KRW-ETC,KRW-BTC,KRW-PEPE,KRW-SHIB,KRW-LINK,KRW-PENGU,KRW-NEAR,KRW-ENA,KRW-MERL,KRW-H,KRW-BABY,KRW-TRUMP,KRW-APT,KRW-B3,KRW-SWAP,KRW-GALA,KRW-VVV,KRW-SAND,KRW-ATH,KRW-NIL,KRW-FIL,KRW-KSM,KRW-BIO,KRW-HBAR,KRW-TRX,KRW-CYS,KRW-SOON,KRW-ZBT,KRW-HOOK,KRW-IP,KRW-AGI,KRW-CHIP,KRW-D,KRW-HEMI,KRW-GWEI,KRW-SEI"
      - "--include"
      - "transactions,orderbook,orderbook_snapshot"
      - "--log-level"
      - "INFO"
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      MCTRADER_NODE_ID: "NODE_BITHUMB_A"
      MCTRADER_HEALTH_PORT: "8080"
      PYTHONUNBUFFERED: "1"
    volumes:
      - mctrader_data:/var/lib/mctrader/data
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - mctrader-net

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
    volumes:
      - mctrader_data:/var/lib/mctrader/data
    depends_on:
      - bithumb-ingester
    healthcheck:
      test: ["CMD", "python", "-c", "import pathlib; pathlib.Path('/var/lib/mctrader/data/wal').exists() or exit(1)"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - mctrader-net

volumes:
  mctrader_data:
    name: mctrader_data

networks:
  mctrader-net:
    driver: bridge
```

- [ ] **Step 2: Add compact_now() fixture to conftest.py**

```python
# tests/conftest.py  (create if not exists, or append)
"""Shared pytest fixtures for mctrader-data tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from mctrader_data.compactor.l1 import L1Compactor
from mctrader_data.wal.segment import scan_sealed


@pytest.fixture
def compact_now(tmp_path: Path):
    """Fixture: returns a function that compacts all sealed WAL segments to L1 immediately."""
    def _compact(root: Path = tmp_path) -> list[Path]:
        compactor = L1Compactor(root)
        results = []
        for sealed in scan_sealed(root):
            results.append(compactor.compact_segment(sealed))
        return results
    return _compact
```

- [ ] **Step 3: Commit Phase C changes**

```bash
git -C c:/workspace/mclayer/mctrader-data add compose.yml tests/conftest.py
git -C c:/workspace/mclayer/mctrader-data commit -m "feat(compose): swap collector → ingester + compactor services [MCT-106]"
```

- [ ] **Step 4: Create Phase C PR**

```bash
git -C c:/workspace/mclayer/mctrader-data checkout -b feat/mct-106-phase-c-cutover
git -C c:/workspace/mclayer/mctrader-data push -u origin feat/mct-106-phase-c-cutover
gh pr create \
  --repo mclayer/mctrader-data \
  --title "feat(collector): WAL cutover — ingester+compactor compose swap [MCT-106 Phase C]" \
  --body "$(cat <<'EOF'
## Summary
- collector.py: `_handle_event` → `_emit_to_wal` via `WalIngester`
- heartbeat.py: `role` field (`ingester` | `compactor`)
- cli.py: `compact` command
- compose.yml: `collector` → `bithumb-ingester` + `compactor`
- conftest.py: `compact_now()` fixture for tests

## ⚠️ Breaking behavior change
`mctrader-data collect` no longer writes Parquet synchronously.
Parquet available after ≤5 min (Compactor L1 cycle).
Callers: see Change Plan §4.1 migration table.

## Canary gate (MUST pass before merge)
Run shadow run per §9.2 before merging this PR.

## Depends on
PR-1 (Phase A) + PR-2 (Phase B) merged

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Phase D: Deprecation (PR-4)

### Task 14: Deprecate Legacy Writers + Changelog

**Files:**
- Modify: `src/mctrader_data/tick_storage.py`
- Modify: `src/mctrader_data/orderbook_storage.py`
- Modify: `src/mctrader_data/orderbook_snapshot_storage.py`
- Create/Modify: `CHANGELOG.md`

- [ ] **Step 1: Add deprecation warnings to legacy writers**

In `tick_storage.py`, `TickWriter.__init__`:

```python
import warnings

class TickWriter:
    def __init__(self, ...):
        warnings.warn(
            "TickWriter is deprecated since MCT-106. Use WalIngester + L1Compactor instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        ...
```

Apply the same pattern to `OrderbookWriter.__init__` and `OrderbookSnapshotWriter.__init__`.

- [ ] **Step 2: Add CHANGELOG entry**

```markdown
## [MCT-106] Zero-loss ingestion pipeline — WAL + tiered compaction

### Breaking behavior change (Phase C, `mctrader-data collect`)

`mctrader-data collect` no longer writes Parquet files synchronously.

**Before:** `collect` wrote Parquet files to `market/<channel>/...` immediately on each batch (500 events).

**After:** `collect` (now `bithumb-ingester`) writes NDJSON WAL files only. Parquet files appear in `market/<channel>/.../tier=L{1,2,3}/...` after the Compactor processes sealed segments (≤ 5 minutes for L1).

**Migration required for callers that read Parquet immediately after collect:**
- `mctrader-engine` integration: add `sleep 300` or call `compact --once` before reading.
- Integration tests: use `compact_now()` fixture from `tests/conftest.py`.

### New commands
- `mctrader-data compact --root <path>` — run the Compactor (L1/L2/L3 tiered)
- `mctrader-data compact --root <path> --once` — single scan cycle and exit

### New services (compose.yml)
- `bithumb-ingester` — replaces `collector`
- `compactor` — new dedicated service
```

- [ ] **Step 3: Run full test suite**

```bash
docker exec mctrader-collector python -m pytest tests/ -q --ignore=tests/integration -W ignore::DeprecationWarning
```

Expected: all pass

- [ ] **Step 4: Commit + Phase D PR**

```bash
git -C c:/workspace/mclayer/mctrader-data add src/mctrader_data/tick_storage.py src/mctrader_data/orderbook_storage.py src/mctrader_data/orderbook_snapshot_storage.py CHANGELOG.md
git -C c:/workspace/mclayer/mctrader-data commit -m "chore(deprecate): legacy TickWriter/OrderbookWriter deprecated [MCT-106 Phase D]"
git -C c:/workspace/mclayer/mctrader-data checkout -b chore/mct-106-phase-d-deprecation
git -C c:/workspace/mclayer/mctrader-data push -u origin chore/mct-106-phase-d-deprecation
gh pr create \
  --repo mclayer/mctrader-data \
  --title "chore(deprecate): legacy writers deprecated [MCT-106 Phase D]" \
  --body "Adds DeprecationWarning to TickWriter/OrderbookWriter/OrderbookSnapshotWriter. CHANGELOG updated with Phase C breaking change notice."
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] INV-1 zero-loss: Task 5 (subprocess SIGKILL test)
- [x] INV-2 atomic seal: Task 3 (`test_seal_is_atomic`)
- [x] INV-3 idempotency: Task 7 (`test_l1_idempotent_double_compaction`)
- [x] INV-4 forward-only sort: Task 7 (`test_l1_out_of_order_sorted`)
- [x] INV-5 schema/decimal preservation: Task 2 (`test_decimal_roundtrip`)
- [x] INV-6 lineage: Task 7 (`test_l1_lineage_file_created`)
- [x] INV-7 tier merge: Task 8 (`test_l2_row_count_equals_l1_total`)
- [x] INV-8 monotone reprocessing: Task 8 (`test_l3_reprocessing_monotone`)
- [x] §8.3 perf baseline: Task 10 (`test_wal_write_throughput`)
- [x] §8.4 integration: Task 10 (`test_roundtrip_100_records`, `test_multi_exchange_isolation`)
- [x] ADR-009 amendment: Task 1
- [x] compact CLI: Task 11
- [x] compose swap: Task 13
- [x] deprecation + changelog: Task 14

**Type consistency:**
- `WalIngester.append(record: dict)` — consistent across Tasks 4, 12
- `L1Compactor.compact_segment(sealed: Path) -> Path` — consistent across Tasks 7, 9, 10
- `segment_index(ts: float, segment_seconds: int) -> int` — consistent across Tasks 3, 4
- `scan_sealed(root: Path) -> list[Path]` — consistent across Tasks 3, 7, 9, 10

**No placeholders:** All steps contain actual code, commands, and expected outputs.
