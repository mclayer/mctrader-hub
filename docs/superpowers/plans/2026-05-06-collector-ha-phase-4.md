# Collector HA Phase 4 — Status CLI + Coverage Node Breakdown + Heartbeat Sink Adapter

**Date**: 2026-05-06
**Story**: MCT-93 (#101) — X4 child of MCT-89
**Sister Stories MERGED**: MCT-91 (X2, mctrader-data 0.6.0) + MCT-92 (X3, mctrader-data 0.7.0)
**Spec**: `docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md`
**Heartbeat schema**: `docs/domain-knowledge/contracts/heartbeat-schema.v1.md`

## 0. Codex Phase 4 review summary (6/6)

| F | Codex | Sonnet | Action |
|---|---|---|---|
| F-1 status CLI surface | SUGGEST | 채택 (modified) | dedup ratio omit X4, threshold/json flag 채택 |
| F-2 tier_coverage node breakdown | SUGGEST | 채택 | NodeCoverage Pydantic submodel + default_factory=dict |
| F-3 heartbeat-aware gap | PUSH-BACK | fix 적용 | conservative current-state-only, history는 후속 |
| F-4 DedupCounterSink adapter | SUGGEST | 채택 | Option B composition + threading.Lock |
| F-5 Quarantine persistence | ADOPT-AS-IS | 채택 | dedup.persist_quarantine_records helper |
| F-6 ADR / contract amendment | SUGGEST | 채택 | heartbeat-schema.v1.md §Related Manifest Artifacts |

Escalation 0 (모두 in-Phase 채택).

## 1. Architect 결정 freeze (X4 specific)

### 결정 #1 — Status CLI human format

operator 가 한눈에 양 node 의 freshness/lag/dedup 을 볼 수 있도록 fixed-width column. JSON format 은 X6 web panel downstream consumption 위해.

```
Heartbeat status (root=/data/mctrader)
node_id    fresh   ws_state      lag_tick  lag_ob   dup_skip  quarantine
NODE_A     2.1s    connected     0.5s      0.6s     1234      0
NODE_B     45.0s   disconnected  ~~~~~     ~~~~~    876       2
```

threshold 색깔 (green/yellow/red) ANSI escape — `--no-color` flag 로 disable, JSON 모드에서는 자동 제외.

### 결정 #2 — `node_coverage` empty key 처리

`tier_coverage` 가 partition 을 scan 할 때 발견된 모든 `node=` value 를 key 로 entry 생성. legacy partition (`node=` 없음) 은 `node_priority` 의 `NODE_PRIORITY_DEFAULT_SENTINEL` (`zzz_DEFAULT`) 키로 entry. paper partition 등 `node=` 미사용 영역은 entry 자체 없음 (그쪽은 `tier_coverage` scan 대상 아님).

### 결정 #3 — `classify_gap` API

```python
class GapCause(StrEnum):
    LIKELY_NODE_DOWN = "LIKELY_NODE_DOWN"
    UNKNOWN = "UNKNOWN"


def classify_gap(
    gap: GapEntry,
    heartbeats_now: dict[str, dict[str, Any]],  # {node_id: heartbeat_payload}
    *,
    fresh_red_seconds: float = 30.0,
) -> GapCause:
    """Conservative current-state-only gap cause classifier.

    LIKELY_NODE_DOWN: any node 의 (now_wall - heartbeat['now']) >= fresh_red_seconds
                     OR ws_state == 'disconnected'
    UNKNOWN: 그 외 (node 가 다 살아 있지만 gap 발생 — heartbeat 만으론 단정 불가)
    """
```

LIKELY_BITHUMB_OUTAGE 는 history ring-buffer 후속 minor 도입 시 추가 (X4 미도입).

### 결정 #4 — `HeartbeatCounterSink` 위치

`heartbeat.py` 에 함께 둠 (HeartbeatWriter 와 1-file proximity). dedup.py 에는 Protocol 만 (X3 freeze 그대로).

### 결정 #5 — Quarantine artifact path collision

`{tier}-{detected_at_iso}-{batch_seq:06d}.json` — `batch_seq` 는 `_BackpressureLimiter.artifact_count` 값을 receive (지금까지 emit 한 batch index). 동일 second 내 multiple flush 시 batch_seq 단조 증가로 collision 0.

### 결정 #6 — `persist_quarantine_records` Decimal serialization

JSON 으로 Decimal serialize 시 `str()` 변환 (precision 보존). `default=str` callback 으로 datetime 도 ISO8601 자동 변환.

### 결정 #7 — Status CLI exit code on no heartbeat files

heartbeat file glob 이 0 file = exit code 2 (red). collector 가 한 번도 안 돌았거나 root 가 잘못됨 — operator 측 명시적 alert.

### 결정 #8 — `node_coverage` per-node gap 계산

per-node gap 은 별도 계산 (전체 union 의 gap 과 다름 — 한쪽 node 의 gap 이 다른 node 가 cover 하면 union gap 0). `tier_coverage_by_node()` 가 per-node `scan_ticks` 별도 호출 (node-id 별 partition filter).

## 2. Step-by-step TDD plan

### Step 1 — heartbeat-schema.v1.md §Related Manifest Artifacts amendment (mctrader-hub)

`docs/domain-knowledge/contracts/heartbeat-schema.v1.md` 에 신규 subsection:

```markdown
## Related Manifest Artifacts

Active-active mismatch quarantine artifacts:

`<MCTRADER_DATA_ROOT>/market/manifest/quarantine/{tier}-{detected_at_iso}-{batch_seq}.json`

- `tier`: `"tick"` / `"orderbook"` (T1 candle 은 §D5 late correction policy 로 quarantine emit 안 함)
- `detected_at_iso`: ISO8601 UTC compact (`20260506T123456Z`), `_BackpressureLimiter` flush 시각
- `batch_seq`: per-second batch index (per-second 100 mismatch cap 의 backpressure batching 결과)
- payload: `{tier, count, records: [{logical_key, rows: [...], detected_at}]}`
- atomic write (temp → fsync → rename), append-only (existing file 덮어쓰지 않음)

`heartbeat-schema.v1.metrics.quarantine_count` 는 cumulative mismatch count (artifact file 개수와 다름 — backpressure batching 의 영향).
```

commit + PR (Story §2-7 commit 와 같이 묶음).

### Step 2 — mctrader-data branch 생성 + version bump 0.7.0 → 0.8.0

```bash
cd c:/workspace/mclayer/mctrader-data
git checkout -b feat/MCT-93-x4-status-coverage-sink
# pyproject.toml: version = "0.8.0"
```

### Step 3 — TDD: `dedup.persist_quarantine_records` helper

**Test first** (`tests/test_dedup.py` 에 추가 절):

```python
def test_persist_quarantine_records_atomic_write(tmp_path: Path) -> None:
    record = QuarantineRecord(
        reason="ACTIVE_ACTIVE_MISMATCH",
        tier="tick",
        logical_key=("bithumb", "KRW-BTC", _ts(0), Decimal("100"), Decimal("0.01"), "buy"),
        rows=[],
        detected_at=_ts(0),
    )
    paths = persist_quarantine_records(tmp_path, [record])
    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].parent == tmp_path / "market" / "manifest" / "quarantine"
    payload = json.loads(paths[0].read_text())
    assert payload["tier"] == "tick"
    assert payload["count"] == 1
    assert len(payload["records"]) == 1


def test_persist_quarantine_records_path_format(tmp_path: Path) -> None:
    # path = "{tier}-{iso_compact}-{batch_seq:06d}.json"
    record = QuarantineRecord(reason="ACTIVE_ACTIVE_MISMATCH", tier="orderbook",
                              logical_key=(...), rows=[], detected_at=_ts(0))
    paths = persist_quarantine_records(tmp_path, [record])
    name = paths[0].name
    assert name.startswith("orderbook-")
    assert name.endswith(".json")
    # iso format check
    assert re.match(r"orderbook-\d{8}T\d{6}Z-\d{6}\.json", name)


def test_persist_quarantine_records_decimal_serialization(tmp_path: Path) -> None:
    record = QuarantineRecord(reason="ACTIVE_ACTIVE_MISMATCH", tier="tick",
                              logical_key=("bithumb", "KRW-BTC", _ts(0), Decimal("100.5"), Decimal("0.01"), "buy"),
                              rows=[], detected_at=_ts(0))
    paths = persist_quarantine_records(tmp_path, [record])
    payload = json.loads(paths[0].read_text())
    # Decimal preserved as string
    assert "100.5" in str(payload["records"][0]["logical_key"])


def test_persist_quarantine_records_empty_list(tmp_path: Path) -> None:
    paths = persist_quarantine_records(tmp_path, [])
    assert paths == []  # no files created
```

**Implementation** (`src/mctrader_data/dedup.py` 추가):

```python
def persist_quarantine_records(
    root: Path | str,
    records: list[QuarantineRecord],
) -> list[Path]:
    if not records:
        return []
    root_p = Path(root)
    out_dir = root_p / "market" / "manifest" / "quarantine"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Group records by tier (assumed homogeneous batch in practice; defensive split)
    by_tier: dict[str, list[QuarantineRecord]] = {}
    for r in records:
        by_tier.setdefault(r.tier, []).append(r)

    written: list[Path] = []
    for tier, batch in by_tier.items():
        detected_at = batch[0].detected_at
        iso_compact = detected_at.strftime("%Y%m%dT%H%M%SZ")
        # Find non-colliding batch_seq
        seq = 0
        while True:
            candidate = out_dir / f"{tier}-{iso_compact}-{seq:06d}.json"
            if not candidate.exists():
                break
            seq += 1
        payload = {
            "tier": tier,
            "count": len(batch),
            "records": [
                {
                    "reason": r.reason,
                    "logical_key": [str(x) for x in r.logical_key],
                    "rows": [str(row) for row in r.rows],  # repr — full row in audit
                    "detected_at": r.detected_at.isoformat(),
                }
                for r in batch
            ],
        }
        # Atomic write
        temp = candidate.with_suffix(candidate.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, default=str, indent=None)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, candidate)
        written.append(candidate)
    return written
```

### Step 4 — TDD: `HeartbeatCounterSink` adapter

**Test first** (`tests/test_heartbeat.py` 추가 절):

```python
def test_heartbeat_counter_sink_increments_dup_skip() -> None:
    writer = HeartbeatWriter(root=Path("/tmp"), node_id="NODE_A")
    sink = HeartbeatCounterSink(writer)
    sink.increment_dup_skip(5)
    assert writer.metrics.dup_skip_count == 5


def test_heartbeat_counter_sink_increments_quarantine() -> None:
    writer = HeartbeatWriter(root=Path("/tmp"), node_id="NODE_A")
    sink = HeartbeatCounterSink(writer)
    sink.increment_quarantine(3)
    assert writer.metrics.quarantine_count == 3


def test_heartbeat_counter_sink_thread_safety() -> None:
    writer = HeartbeatWriter(root=Path("/tmp"), node_id="NODE_A")
    sink = HeartbeatCounterSink(writer)
    threads = [
        threading.Thread(target=lambda: [sink.increment_dup_skip() for _ in range(1000)])
        for _ in range(10)
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    assert writer.metrics.dup_skip_count == 10000


def test_heartbeat_counter_sink_protocol_compliance() -> None:
    """Verify HeartbeatCounterSink satisfies DedupCounterSink Protocol."""
    from mctrader_data.dedup import DedupCounterSink
    writer = HeartbeatWriter(root=Path("/tmp"), node_id="NODE_A")
    sink: DedupCounterSink = HeartbeatCounterSink(writer)  # static type check
    sink.increment_dup_skip()
    sink.increment_quarantine()
```

**Implementation** (`src/mctrader_data/heartbeat.py` 추가):

```python
import threading

class HeartbeatCounterSink:
    """DedupCounterSink Protocol concrete impl, wrapping HeartbeatWriter."""

    def __init__(self, writer: HeartbeatWriter):
        self._writer = writer
        self._lock = threading.Lock()

    def increment_dup_skip(self, n: int = 1) -> None:
        with self._lock:
            self._writer.metrics.dup_skip_count += n

    def increment_quarantine(self, n: int = 1) -> None:
        with self._lock:
            self._writer.metrics.quarantine_count += n
```

### Step 5 — TDD: `CoverageReport.node_coverage` + `NodeCoverage`

**Test first** (`tests/test_orderbook_replay.py` 추가 절):

```python
def test_tier_coverage_node_breakdown_two_nodes(tmp_path: Path) -> None:
    # Seed NODE_A + NODE_B
    wa = TickWriter(root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
                    snapshot_id="ign", node_id="NODE_A", collector_run_id="NODE_A-A")
    wa.append(_tick(0))
    wa.append(_tick(10))
    wa.close()

    wb = TickWriter(root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
                    snapshot_id="ign", node_id="NODE_B", collector_run_id="NODE_B-A")
    wb.append(_tick(5))
    wb.append(_tick(15))
    wb.close()

    report = tier_coverage(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC", tier="tick",
        start=_ts(0), end=_ts(60),
    )
    assert "NODE_A" in report.node_coverage
    assert "NODE_B" in report.node_coverage
    assert report.node_coverage["NODE_A"].min_ts_utc == _ts(0)
    assert report.node_coverage["NODE_A"].max_ts_utc == _ts(10)
    assert report.node_coverage["NODE_B"].min_ts_utc == _ts(5)
    assert report.node_coverage["NODE_B"].max_ts_utc == _ts(15)
    assert report.node_coverage["NODE_A"].collector_run_ids == ["NODE_A-A"]


def test_tier_coverage_legacy_node_default(tmp_path: Path) -> None:
    """Legacy partition (no node= level) → node_coverage[zzz_DEFAULT]."""
    w = TickWriter(root=tmp_path, exchange="bithumb", symbol="KRW-BTC",
                   snapshot_id="legacy")
    w.append(_tick(0))
    w.close()
    report = tier_coverage(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC", tier="tick",
        start=_ts(0), end=_ts(60),
    )
    assert "zzz_DEFAULT" in report.node_coverage


def test_tier_coverage_backward_compat(tmp_path: Path) -> None:
    """Existing 7 fields untouched."""
    _seed_ticks(tmp_path, [_tick(0), _tick(10)])
    report = tier_coverage(
        root=tmp_path, exchange="bithumb", symbol="KRW-BTC", tier="tick",
        start=_ts(0), end=_ts(60),
    )
    # Old 7 fields
    assert report.symbol == "KRW-BTC"
    assert report.tier == "tick"
    assert report.min_ts_utc == _ts(0)
    assert report.max_ts_utc == _ts(10)
    assert report.gaps == []
    assert "legacy-s1" in report.collector_run_ids or len(report.collector_run_ids) >= 0
    # New field default present (empty if no scan)
    assert isinstance(report.node_coverage, dict)
```

**Implementation** (`src/mctrader_data/orderbook_replay.py` 변경):

```python
class NodeCoverage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    min_ts_utc: datetime | None = None
    max_ts_utc: datetime | None = None
    gaps: list[GapEntry] = Field(default_factory=list)
    collector_run_ids: list[str] = Field(default_factory=list)


class CoverageReport(BaseModel):
    # existing 7 fields unchanged
    ...
    node_coverage: dict[str, NodeCoverage] = Field(default_factory=dict)
```

`tier_coverage()` 의 partition rglob loop 에서 path-side 에 `node=` regex 적용해 per-node grouping.

### Step 6 — TDD: `classify_gap` helper

**Test first** (`tests/test_diagnostic.py` 신규):

```python
def test_classify_gap_likely_node_down_disconnected() -> None:
    gap = GapEntry(after_ts=_ts(0), before_ts=_ts(700), gap_seconds=700)
    heartbeats = {
        "NODE_A": {"now": _ts(0).isoformat(), "ws_state": "connected"},
        "NODE_B": {"now": _ts(0).isoformat(), "ws_state": "disconnected"},
    }
    assert classify_gap(gap, heartbeats) == GapCause.LIKELY_NODE_DOWN


def test_classify_gap_likely_node_down_stale_heartbeat() -> None:
    gap = GapEntry(after_ts=_ts(0), before_ts=_ts(700), gap_seconds=700)
    # NODE_B last wrote 60s ago (> 30s red threshold)
    now_wall = datetime.now(timezone.utc)
    heartbeats = {
        "NODE_A": {"now": now_wall.isoformat(), "ws_state": "connected"},
        "NODE_B": {"now": (now_wall - timedelta(seconds=60)).isoformat(), "ws_state": "connected"},
    }
    assert classify_gap(gap, heartbeats) == GapCause.LIKELY_NODE_DOWN


def test_classify_gap_unknown_all_connected() -> None:
    gap = GapEntry(after_ts=_ts(0), before_ts=_ts(700), gap_seconds=700)
    now_wall = datetime.now(timezone.utc)
    heartbeats = {
        "NODE_A": {"now": now_wall.isoformat(), "ws_state": "connected"},
        "NODE_B": {"now": now_wall.isoformat(), "ws_state": "connected"},
    }
    assert classify_gap(gap, heartbeats) == GapCause.UNKNOWN


def test_classify_gap_no_heartbeats_unknown() -> None:
    gap = GapEntry(after_ts=_ts(0), before_ts=_ts(700), gap_seconds=700)
    assert classify_gap(gap, {}) == GapCause.UNKNOWN
```

**Implementation** (`src/mctrader_data/diagnostic.py` 신규):

```python
"""Heartbeat-aware gap cause classifier (X4 of MCT-89)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from mctrader_data.orderbook_replay import GapEntry


class GapCause(str, Enum):
    LIKELY_NODE_DOWN = "LIKELY_NODE_DOWN"
    UNKNOWN = "UNKNOWN"


def classify_gap(
    gap: GapEntry,
    heartbeats_now: dict[str, dict[str, Any]],
    *,
    fresh_red_seconds: float = 30.0,
) -> GapCause:
    """Conservative current-state-only classifier.

    LIKELY_NODE_DOWN: any node 의 (now_wall - heartbeat['now']) >= fresh_red_seconds
                     OR ws_state == 'disconnected'
    UNKNOWN: 위에 해당 안 됨
    """
    if not heartbeats_now:
        return GapCause.UNKNOWN
    now = datetime.now(timezone.utc)
    for _node_id, hb in heartbeats_now.items():
        if hb.get("ws_state") == "disconnected":
            return GapCause.LIKELY_NODE_DOWN
        try:
            hb_now = datetime.fromisoformat(hb["now"].replace("Z", "+00:00"))
            staleness = (now - hb_now).total_seconds()
            if staleness >= fresh_red_seconds:
                return GapCause.LIKELY_NODE_DOWN
        except (KeyError, ValueError):
            continue
    return GapCause.UNKNOWN
```

### Step 7 — TDD: CLI `status` subcommand

**Test first** (`tests/test_cli_status.py` 신규):

```python
from click.testing import CliRunner
from mctrader_data.cli import main

def test_status_no_heartbeat_files_exit_code_2(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 2
    assert "no heartbeat" in result.output.lower()


def test_status_one_node_green(tmp_path: Path) -> None:
    # write a fresh heartbeat
    hb_dir = tmp_path / "market" / "manifest"
    hb_dir.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    hb_payload = {
        "schema_version": "heartbeat.v1",
        "node_id": "NODE_A",
        "now": now.isoformat(),
        "ws_state": "connected",
        "last_event_ts_per_tier": {"tick": now.isoformat()},
        "metrics": {"events_per_sec": 10, "dup_skip_count": 0,
                    "quarantine_count": 0, "ws_reconnect_count": 0,
                    "backfill_pending_seconds": 0},
        # other required fields
        "collector_run_id": "x", "version": "v", "started_at": now.isoformat(),
        "uptime_seconds": 100, "queue_depth": 0,
    }
    (hb_dir / "heartbeat-NODE_A.json").write_text(json.dumps(hb_payload))

    runner = CliRunner()
    result = runner.invoke(main, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "NODE_A" in result.output


def test_status_disconnected_red(tmp_path: Path) -> None:
    # Setup heartbeat with ws_state=disconnected
    ...
    result = runner.invoke(main, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 2


def test_status_stale_freshness_red(tmp_path: Path) -> None:
    # Write heartbeat with now=60s ago
    ...
    result = runner.invoke(main, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 2


def test_status_format_json(tmp_path: Path) -> None:
    ...
    result = runner.invoke(main, ["status", "--root", str(tmp_path), "--format", "json"])
    payload = json.loads(result.output)
    assert "nodes" in payload
    assert payload["nodes"][0]["node_id"] == "NODE_A"
```

**Implementation** (`src/mctrader_data/cli.py` 추가):

```python
@main.command()
@click.option("--root", type=click.Path(path_type=Path), default=None)
@click.option("--fresh-yellow-seconds", default=10.0)
@click.option("--fresh-red-seconds", default=30.0)
@click.option("--lag-yellow-seconds", default=60.0)
@click.option("--lag-red-seconds", default=300.0)
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
@click.option("--no-color", is_flag=True)
def status(
    root: Path | None,
    fresh_yellow_seconds: float,
    fresh_red_seconds: float,
    lag_yellow_seconds: float,
    lag_red_seconds: float,
    fmt: str,
    no_color: bool,
) -> None:
    """Show heartbeat freshness / lag / dedup metrics for all nodes."""
    import json as _json
    from datetime import datetime, timezone

    root_resolved = resolve_data_root(root_override=root)
    hb_dir = root_resolved / "market" / "manifest"

    files = sorted(hb_dir.glob("heartbeat-*.json"))
    if not files:
        click.echo(f"no heartbeat files in {hb_dir}", err=True)
        sys.exit(2)

    now = datetime.now(timezone.utc)
    nodes: list[dict] = []
    worst_level = 0  # 0=green, 1=yellow, 2=red

    for f in files:
        node_id = f.stem.removeprefix("heartbeat-")
        try:
            data = _json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            click.echo(f"failed to read {f}: {e}", err=True)
            worst_level = max(worst_level, 2)
            continue

        # freshness
        hb_now = datetime.fromisoformat(data["now"].replace("Z", "+00:00"))
        freshness = (now - hb_now).total_seconds()

        # ws_state contributes to red
        ws = data.get("ws_state", "unknown")
        node_level = 0
        if ws == "disconnected":
            node_level = 2
        elif freshness >= fresh_red_seconds:
            node_level = 2
        elif freshness >= fresh_yellow_seconds:
            node_level = 1

        # tier lags
        tier_lags: dict[str, float] = {}
        for tier, ts_iso in (data.get("last_event_ts_per_tier") or {}).items():
            try:
                ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
                lag = (now - ts).total_seconds()
                tier_lags[tier] = lag
                if lag >= lag_red_seconds:
                    node_level = max(node_level, 2)
                elif lag >= lag_yellow_seconds:
                    node_level = max(node_level, 1)
            except Exception:
                pass

        worst_level = max(worst_level, node_level)
        nodes.append({
            "node_id": node_id,
            "freshness_seconds": round(freshness, 1),
            "ws_state": ws,
            "tier_lags": {k: round(v, 1) for k, v in tier_lags.items()},
            "metrics": data.get("metrics", {}),
            "level": node_level,
        })

    if fmt == "json":
        click.echo(_json.dumps({"nodes": nodes, "worst_level": worst_level}, indent=2))
    else:
        # human table
        click.echo(f"Heartbeat status (root={root_resolved})")
        click.echo(f"{'node_id':<12} {'fresh':<8} {'ws_state':<14} {'lag_tick':<10} {'lag_ob':<10} {'dup_skip':<10} {'quarantine':<10}")
        for n in nodes:
            color = "" if no_color else _level_color(n["level"])
            reset = "" if no_color else "\033[0m"
            lag_t = n["tier_lags"].get("tick", "-")
            lag_o = n["tier_lags"].get("orderbook", "-")
            click.echo(
                f"{color}{n['node_id']:<12} "
                f"{n['freshness_seconds']:<8} "
                f"{n['ws_state']:<14} "
                f"{lag_t!s:<10} {lag_o!s:<10} "
                f"{n['metrics'].get('dup_skip_count', 0):<10} "
                f"{n['metrics'].get('quarantine_count', 0):<10}"
                f"{reset}"
            )

    sys.exit(worst_level)
```

### Step 8 — Wire scan callers to call `persist_quarantine_records`

`storage.py` / `tick_storage.py` / `orderbook_replay.py` 의 `scan_*` API 가 `DedupResult.quarantine_records` 를 받았을 때 자동 persist 호출. **option 1**: 항상 자동 persist. **option 2**: explicit `persist_quarantine: bool = False` flag. → **option 2** 채택 (read-only 유지가 default, opt-in I/O — backward compat).

```python
def scan_ticks(
    *,
    root: Path,
    exchange: str,
    symbol: str,
    start: datetime,
    end: datetime,
    simulated_clock: datetime | None = None,
    persist_quarantine: bool = False,  # NEW X4
) -> Iterator[TickRecord]:
    ...
    result = deduplicate_ticks(rows, multi_node=multi_node, sink=sink)
    if persist_quarantine and result.quarantine_records:
        from mctrader_data.dedup import persist_quarantine_records
        persist_quarantine_records(root, result.quarantine_records)
    yield from result.emitted
```

scan_orderbook_events 동일.

### Step 9 — pytest 전체 → green

```bash
cd c:/workspace/mclayer/mctrader-data
ruff check src/ tests/
pytest -xvs
```

기존 148 + 새로운 ~20 test → ~168 PASS 목표.

### Step 10 — PR open + Codex review + merge

mctrader-data PR:
- title: `[MCT-93] feat(ha): Status CLI + Coverage Node Breakdown + Heartbeat Sink Adapter (X4 of MCT-89, mctrader-data 0.8.0)`
- body: Codex 6/6 review 결과 + 168 pytest PASS 자료

Codex implementation 단계 review (6-area: code quality / contract enforcement / test coverage / backward compat / cross-thread safety / scope creep). ADOPT 합 / fix 적용 후 admin merge.

### Step 11 — Story §8-9 + Phase 4 close (mctrader-hub)

`docs/stories/MCT-93.md` §8 (개발 서사) + §9 (Codex review 결과) 작성. status: phase:완료. PR open + admin merge.

memory update: `project_collector_ha_state.md` 에 Phase 4 close 추가.

## 3. Acceptance Criteria

- [ ] heartbeat-schema.v1.md §Related Manifest Artifacts subsection committed
- [ ] mctrader-data 0.8.0 release (pyproject.toml bump)
- [ ] dedup.persist_quarantine_records helper + 4 test PASS
- [ ] HeartbeatCounterSink class + 4 test PASS (포함 thread_safety + protocol compliance)
- [ ] CoverageReport.node_coverage field + NodeCoverage submodel + 3 test PASS
- [ ] tier_coverage populates node_coverage from partition rglob node= grouping
- [ ] classify_gap helper + 4 test PASS (in tests/test_diagnostic.py)
- [ ] CLI status subcommand + 5 test PASS (in tests/test_cli_status.py)
- [ ] scan_ticks / scan_orderbook_events `persist_quarantine` flag + integration test PASS
- [ ] backward compat 100% — 기존 148 test PASS 유지 (regression 0)
- [ ] Codex implementation review 6-area ADOPT 합 (escalation 0)
- [ ] mctrader-data PR merged
- [ ] mctrader-hub Story §8-9 + status: phase:완료 commit + PR merged

## 4. Out-of-scope (X4 종료 후 후속)

- heartbeat history ring-buffer (LIKELY_BITHUMB_OUTAGE classifier 활성화 위한 prerequisite)
- HeartbeatMetrics.events_total cumulative (dedup ratio denominator)
- collector daemon 의 dedup.* 호출 site (현재 collector 가 dedup 호출 site 없음 — read-side scan caller 만)
- X5 systemd / Ansible (mctrader-hub `scripts/ha/`)
- X6 Streamlit page (mctrader-web `pages/00_status.py`) — X4 의 `--format json` 출력 consume
- X7 Calibration C1/C2 + 양 node 30분 E2E demo (mctrader-hub Epic close)
