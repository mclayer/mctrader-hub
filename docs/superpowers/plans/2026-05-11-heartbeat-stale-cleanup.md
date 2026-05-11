# Heartbeat Stale Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 3-layer defense로 heartbeat stale 파일 누적 문제 영구 제거 (운영 장애 재발 방지)

**Architecture:** Layer 1 = cli.py `_resolve_node_id()` 1줄 수정(MCTRADER_NODE_ID env var 우선순위), Layer 2 = HeartbeatWriter `cleanup_stale_heartbeats()` 메서드 + `run()` 시작 시 자동 호출, Layer 3 = 00_status.py active/stale 분기 렌더링(UI 방어선)

**Tech Stack:** Python 3.12, pytest-asyncio, Streamlit AppTest, pytest tmp_path/monkeypatch

---

## File Map

| 파일 | 역할 | Story |
|------|------|-------|
| `mctrader-data/src/mctrader_data/cli.py` | `_resolve_node_id()` 추가, 모듈 import 추가 | MCT-129 |
| `mctrader-data/tests/test_cli_node_id.py` | `_resolve_node_id` 단위 테스트 3개 (신규) | MCT-129 |
| `mctrader-data/src/mctrader_data/heartbeat.py` | `import time` 추가, `cleanup_stale_heartbeats()` 메서드, `run()` 호출 | MCT-130 |
| `mctrader-data/tests/test_heartbeat.py` | `TestHeartbeatStaleCleanup` 클래스 6 테스트 추가 | MCT-130 |
| `mctrader-web/src/mctrader_web/dashboard/pages/00_status.py` | active/stale 분기 렌더링 교체 | MCT-131 |
| `mctrader-web/tests/test_apptest_status_panel.py` | stale 렌더링 3 AppTest 추가 | MCT-131 |
| `mctrader-hub/docs/stories/MCT-129.md` | Story file | – |
| `mctrader-hub/docs/stories/MCT-130.md` | Story file | – |
| `mctrader-hub/docs/stories/MCT-131.md` | Story file | – |

---

## Task 1: MCT-129 — cli.py node_id 우선순위 fix

**Files:**
- Modify: `mctrader-data/src/mctrader_data/cli.py`
- Create: `mctrader-data/tests/test_cli_node_id.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`mctrader-data/tests/test_cli_node_id.py` 신규 생성:

```python
"""Unit tests for _resolve_node_id priority: --node-id > env var > hostname. MCT-129."""
from __future__ import annotations

import pytest


def test_explicit_arg_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCTRADER_NODE_ID", "ENV_NODE")
    from mctrader_data.cli import _resolve_node_id
    assert _resolve_node_id("CLI_NODE") == "CLI_NODE"


def test_env_var_wins_over_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCTRADER_NODE_ID", "ENV_NODE")
    monkeypatch.delenv("MCTRADER_NODE_ID", raising=False)
    monkeypatch.setenv("MCTRADER_NODE_ID", "ENV_NODE")
    from mctrader_data.cli import _resolve_node_id
    assert _resolve_node_id(None) == "ENV_NODE"


def test_hostname_fallback_when_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket
    monkeypatch.delenv("MCTRADER_NODE_ID", raising=False)
    from mctrader_data.cli import _resolve_node_id
    assert _resolve_node_id(None) == socket.gethostname()
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```
cd c:/workspace/mclayer/mctrader-data
python -m pytest tests/test_cli_node_id.py -v
```

Expected: `ImportError: cannot import name '_resolve_node_id' from 'mctrader_data.cli'`

- [ ] **Step 3: cli.py 수정**

`mctrader-data/src/mctrader_data/cli.py` 수정:

**3a. 모듈 상단 imports에 `import os`와 `import socket` 추가** (line 5 근처, `import sys` 다음):

```python
import os
import socket
import sys
```

**3b. 첫 번째 `@main.command()` (line 51) 직전에 `_resolve_node_id` 함수 추가**:

```python
def _resolve_node_id(explicit: str | None) -> str:
    """Priority: --node-id CLI > MCTRADER_NODE_ID env var > socket.gethostname(). MCT-129."""
    return explicit or os.environ.get("MCTRADER_NODE_ID") or socket.gethostname()
```

**3c. line 451-453 교체** (`# MCT-91 — HA active-active resolution` 블록):

기존:
```python
    # MCT-91 — HA active-active resolution
    import socket as _socket
    resolved_node_id = node_id if node_id is not None else _socket.gethostname()
```

수정 후:
```python
    # MCT-91 — HA active-active resolution (MCT-129: env var priority)
    resolved_node_id = _resolve_node_id(node_id)
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

```
cd c:/workspace/mclayer/mctrader-data
python -m pytest tests/test_cli_node_id.py -v
```

Expected: `3 passed`

- [ ] **Step 5: 전체 mctrader-data 테스트 회귀 확인**

```
cd c:/workspace/mclayer/mctrader-data
python -m pytest -x -q
```

Expected: all existing tests pass

- [ ] **Step 6: commit**

```bash
cd c:/workspace/mclayer/mctrader-data
git add src/mctrader_data/cli.py tests/test_cli_node_id.py
git commit -m "feat(mct-129): _resolve_node_id — MCTRADER_NODE_ID env var priority over hostname"
```

---

## Task 2: MCT-130 — HeartbeatWriter stale cleanup

**Files:**
- Modify: `mctrader-data/src/mctrader_data/heartbeat.py`
- Modify: `mctrader-data/tests/test_heartbeat.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`mctrader-data/tests/test_heartbeat.py` 에 `TestHeartbeatStaleCleanup` 클래스 추가 (파일 끝에 append):

```python


class TestHeartbeatStaleCleanup:
    def _make_stale(self, path: Path, age_seconds: float) -> None:
        import time
        path.write_text("{}", encoding="utf-8")
        mtime = time.time() - age_seconds
        import os
        os.utime(path, (mtime, mtime))

    def test_stale_file_deleted(self, tmp_path: Path) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A")
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        stale = manifest_dir / "heartbeat-NODE_ZOMBIE.json"
        self._make_stale(stale, age_seconds=400.0)

        writer.cleanup_stale_heartbeats(ttl_seconds=300.0)

        assert not stale.exists(), "stale file must be removed"

    def test_own_file_protected(self, tmp_path: Path) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A")
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        own = manifest_dir / "heartbeat-NODE_A.json"
        self._make_stale(own, age_seconds=400.0)

        writer.cleanup_stale_heartbeats(ttl_seconds=300.0)

        assert own.exists(), "own heartbeat file must never be deleted"

    def test_fresh_file_not_deleted(self, tmp_path: Path) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A")
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        fresh = manifest_dir / "heartbeat-NODE_FRESH.json"
        self._make_stale(fresh, age_seconds=10.0)

        writer.cleanup_stale_heartbeats(ttl_seconds=300.0)

        assert fresh.exists(), "fresh file (< TTL) must not be deleted"

    def test_missing_manifest_dir_no_error(self, tmp_path: Path) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A")
        # manifest_dir does not exist — should complete silently
        writer.cleanup_stale_heartbeats(ttl_seconds=300.0)  # no exception

    def test_oserror_on_stat_is_resilient(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A")
        manifest_dir = tmp_path / "market" / "manifest"
        manifest_dir.mkdir(parents=True)
        stale = manifest_dir / "heartbeat-NODE_ZOMBIE.json"
        stale.write_text("{}", encoding="utf-8")

        real_stat = Path.stat

        def patched_stat(self: Path, *, follow_symlinks: bool = True) -> object:
            if self.name == "heartbeat-NODE_ZOMBIE.json":
                raise OSError(13, "Permission denied")
            return real_stat(self, follow_symlinks=follow_symlinks)

        monkeypatch.setattr(Path, "stat", patched_stat)

        with caplog.at_level(logging.WARNING, logger="mctrader_data.heartbeat"):
            writer.cleanup_stale_heartbeats(ttl_seconds=300.0)

        assert any("stale cleanup failed" in r.message for r in caplog.records)
        assert stale.exists(), "file must remain when OSError occurs"

    @pytest.mark.asyncio
    async def test_run_calls_cleanup_at_startup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        writer = HeartbeatWriter(root=tmp_path, node_id="NODE_A", interval_seconds=10.0)
        calls: list[str] = []
        monkeypatch.setattr(writer, "cleanup_stale_heartbeats", lambda: calls.append("called"))

        task = asyncio.create_task(writer.run())
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert calls == ["called"], "run() must call cleanup_stale_heartbeats() exactly once at startup"
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```
cd c:/workspace/mclayer/mctrader-data
python -m pytest tests/test_heartbeat.py::TestHeartbeatStaleCleanup -v
```

Expected: `AttributeError: 'HeartbeatWriter' object has no attribute 'cleanup_stale_heartbeats'`

- [ ] **Step 3: heartbeat.py 수정**

**3a. `import time` 추가** (`mctrader-data/src/mctrader_data/heartbeat.py` 모듈 상단, `import os` 다음):

```python
import os
import time
import threading
```

**3b. `HeartbeatWriter` 클래스에 `cleanup_stale_heartbeats()` 메서드 추가** (`run()` 메서드 직전에 삽입):

```python
    def cleanup_stale_heartbeats(self, ttl_seconds: float | None = None) -> None:
        """One-shot: remove heartbeat files older than TTL. Own file is always preserved.

        Called at run() startup to clear files accumulated from prior container IDs.
        OSError on individual files → warn + continue (never blocks collector start).
        """
        _ttl = ttl_seconds if ttl_seconds is not None else float(
            os.environ.get("MCTRADER_HEARTBEAT_STALE_CLEANUP_SECONDS", "300")
        )
        manifest_dir = self.root / "market" / "manifest"
        if not manifest_dir.is_dir():
            return
        own_name = f"heartbeat-{self.node_id}.json"
        now = time.time()
        for hb_file in manifest_dir.glob("heartbeat-*.json"):
            if hb_file.name == own_name:
                continue
            try:
                age = now - hb_file.stat().st_mtime
                if age > _ttl:
                    if time.time() - hb_file.stat().st_mtime > _ttl:
                        hb_file.unlink(missing_ok=True)
                        logger.info(
                            "stale heartbeat removed: %s (age=%.0fs)", hb_file.name, age
                        )
            except OSError as exc:
                logger.warning(
                    "stale cleanup failed for %s: %s", hb_file.name, exc
                )
```

**3c. `run()` 메서드 첫 줄에 cleanup 호출 추가**:

기존:
```python
    async def run(self) -> None:
        """5s loop until cancelled. Final atomic write on cancel."""
        try:
            while True:
```

수정 후:
```python
    async def run(self) -> None:
        """5s loop until cancelled. Final atomic write on cancel."""
        self.cleanup_stale_heartbeats()
        try:
            while True:
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

```
cd c:/workspace/mclayer/mctrader-data
python -m pytest tests/test_heartbeat.py -v
```

Expected: all existing tests + `TestHeartbeatStaleCleanup` 6 tests pass

- [ ] **Step 5: commit**

```bash
cd c:/workspace/mclayer/mctrader-data
git add src/mctrader_data/heartbeat.py tests/test_heartbeat.py
git commit -m "feat(mct-130): HeartbeatWriter.cleanup_stale_heartbeats() — TTL 300s stale file removal on run() startup"
```

---

## Task 3: MCT-131 — 00_status.py 방어적 렌더링

**Files:**
- Modify: `mctrader-web/src/mctrader_web/dashboard/pages/00_status.py`
- Modify: `mctrader-web/tests/test_apptest_status_panel.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`mctrader-web/tests/test_apptest_status_panel.py` 파일 끝에 3개 테스트 추가:

```python


def test_status_panel_stale_node_in_expander() -> None:
    """active 노드는 카드 렌더링, stale 노드는 expander에 격리."""
    payload = json.dumps({
        "nodes": [
            {
                "node_id": "NODE_BITHUMB_A", "level": 0, "ws_state": "connected",
                "freshness_seconds": 2.0,
                "tier_lags": {"tick": 0.5},
                "metrics": {"dup_skip_count": 0, "quarantine_count": 0,
                           "ws_reconnect_count": 0, "backfill_pending_seconds": 0},
            },
            {
                "node_id": "6e495e91f663", "level": 2, "ws_state": "disconnected",
                "freshness_seconds": 36000.0,
            },
        ],
        "worst_level": 2,
    })
    at = _run_app_with_mocked_status(2, payload)
    assert not at.exception
    # active node rendered in main card area
    markdown = " ".join(m.value for m in at.markdown)
    assert "NODE_BITHUMB_A" in markdown
    # stale node in expander (not in main cards)
    expanders = at.expander
    assert len(expanders) > 0, "stale node must be in an expander"
    expander_labels = " ".join(e.label for e in expanders)
    assert "6e495e91f663" in expander_labels
    # stale node must NOT appear in main markdown cards
    assert "6e495e91f663" not in markdown


def test_status_panel_all_stale_no_crash() -> None:
    """active 노드 0개 시 st.columns(max(1,0))=st.columns(1) — 크래시 없음."""
    payload = json.dumps({
        "nodes": [
            {"node_id": "6e495e91f663", "level": 2, "ws_state": "disconnected",
             "freshness_seconds": 36000.0},
            {"node_id": "8d88f77d171a", "level": 2, "ws_state": "disconnected",
             "freshness_seconds": 10000.0},
        ],
        "worst_level": 2,
    })
    at = _run_app_with_mocked_status(2, payload)
    assert not at.exception, f"all-stale must not crash: {at.exception}"
    expanders = at.expander
    assert len(expanders) == 2, "both stale nodes must be in expanders"


def test_status_panel_active_only_no_expander() -> None:
    """stale 노드 없을 때 expander 미생성."""
    payload = json.dumps({
        "nodes": [
            {"node_id": "NODE_BITHUMB_A", "level": 0, "ws_state": "connected",
             "freshness_seconds": 2.0,
             "tier_lags": {"tick": 0.5},
             "metrics": {"dup_skip_count": 0, "quarantine_count": 0,
                        "ws_reconnect_count": 0, "backfill_pending_seconds": 0}},
            {"node_id": "NODE_UPBIT_A", "level": 0, "ws_state": "connected",
             "freshness_seconds": 1.5,
             "tier_lags": {"tick": 0.3},
             "metrics": {"dup_skip_count": 0, "quarantine_count": 0,
                        "ws_reconnect_count": 0, "backfill_pending_seconds": 0}},
        ],
        "worst_level": 0,
    })
    at = _run_app_with_mocked_status(0, payload)
    assert not at.exception
    markdown = " ".join(m.value for m in at.markdown)
    assert "NODE_BITHUMB_A" in markdown
    assert "NODE_UPBIT_A" in markdown
    expanders = at.expander
    assert len(expanders) == 0, "no stale nodes → no expanders"
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```
cd c:/workspace/mclayer/mctrader-web
python -m pytest tests/test_apptest_status_panel.py::test_status_panel_stale_node_in_expander tests/test_apptest_status_panel.py::test_status_panel_all_stale_no_crash tests/test_apptest_status_panel.py::test_status_panel_active_only_no_expander -v
```

Expected:
- `test_status_panel_stale_node_in_expander`: FAIL — `AssertionError: stale node must be in an expander` (stale node 6e495e91f663이 현재 main card에 렌더링됨)
- `test_status_panel_all_stale_no_crash`: FAIL — `streamlit.errors.StreamlitAPIException: st.columns(0)` 크래시
- `test_status_panel_active_only_no_expander`: PASS (우연히 통과할 수도 있음)

- [ ] **Step 3: 00_status.py 렌더링 블록 교체**

`mctrader-web/src/mctrader_web/dashboard/pages/00_status.py` 수정:

기존 (line 144-148):
```python
else:
    cols = st.columns(len(result.nodes))
    for col, node in zip(cols, result.nodes, strict=False):
        with col:
            _render_node_card(node)
```

수정 후:
```python
else:
    active_nodes = [n for n in result.nodes if n.get("level", 2) < 2]
    stale_nodes = [n for n in result.nodes if n.get("level", 2) >= 2]

    cols = st.columns(max(1, len(active_nodes)))
    for col, node in zip(cols, active_nodes, strict=False):
        with col:
            _render_node_card(node)

    if stale_nodes:
        st.divider()
        st.caption("⛔ Stale nodes (inactive)")
        for node in stale_nodes:
            node_id = node.get("node_id", "?")
            fresh = node.get("freshness_seconds")
            ws_state = node.get("ws_state", "unknown")
            fresh_label = f"{fresh:.0f}s 전" if isinstance(fresh, (int, float)) else "—"
            with st.expander(f"⛔ {node_id} — {fresh_label}", expanded=False):
                st.write(f"ws_state: {ws_state}")
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

```
cd c:/workspace/mclayer/mctrader-web
python -m pytest tests/test_apptest_status_panel.py -v
```

Expected: all existing tests (5개) + 새 3개 = 8 passed

- [ ] **Step 5: commit**

```bash
cd c:/workspace/mclayer/mctrader-web
git add src/mctrader_web/dashboard/pages/00_status.py tests/test_apptest_status_panel.py
git commit -m "feat(mct-131): 00_status.py — active/stale split rendering, stale nodes in expander"
```

---

## Task 4: Story 파일 생성 (mctrader-hub)

**Files:**
- Create: `mctrader-hub/docs/stories/MCT-129.md`
- Create: `mctrader-hub/docs/stories/MCT-130.md`
- Create: `mctrader-hub/docs/stories/MCT-131.md`

- [ ] **Step 1: MCT-129.md 생성**

`mctrader-hub/docs/stories/MCT-129.md`:

```markdown
---
story_key: MCT-129
story_scope: mctrader-data
status: done
created_at: 2026-05-11
completed_at: 2026-05-11
---

# MCT-129: cli.py MCTRADER_NODE_ID env var 우선순위 fix

## §1 배경

`cli.py` line 453이 `socket.gethostname()`(= Docker container short ID)만 사용.
`collector.py:71`이 이미 `node_id or os.environ.get("MCTRADER_NODE_ID") or socket.gethostname()` 패턴 사용 중.
`mctrader-data/compose.yml`에 이미 `MCTRADER_NODE_ID: "NODE_BITHUMB_A"` / `"NODE_UPBIT_A"` 설정됨.

## §2 목표 및 범위

- `cli.py`에 모듈 레벨 `_resolve_node_id(explicit)` 헬퍼 추가
- `os`, `socket` 모듈 레벨 import 추가
- `resolved_node_id` 1줄 교체 (`_resolve_node_id(node_id)`)
- 단위 테스트 3개 (`tests/test_cli_node_id.py` 신규)

## §3 Acceptance Criteria

- [x] `--node-id` CLI 인자 > `MCTRADER_NODE_ID` env var > `socket.gethostname()` 우선순위
- [x] `_resolve_node_id` 단위 테스트 3개 PASS

## §4 설계 결정

spec: docs/superpowers/specs/2026-05-11-heartbeat-stale-cleanup-design.md §2 레이어 1

## §5 구현 노트

plan: docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md Task 1

## §6 테스트 전략

`tests/test_cli_node_id.py` — 3 우선순위 케이스 monkeypatch

## §7 Change Plan

N/A (spec §2 레이어 1 참조)

## §8 Test Contract

단위 테스트 3개: explicit > env > hostname 순서

## §9 Review

`docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md` Task 1

## §10 FIX Ledger

없음

## §11 PMO 회고

(PMOAgent dispatch 대기)
```

- [ ] **Step 2: MCT-130.md 생성**

`mctrader-hub/docs/stories/MCT-130.md`:

```markdown
---
story_key: MCT-130
story_scope: mctrader-data
status: done
created_at: 2026-05-11
completed_at: 2026-05-11
---

# MCT-130: HeartbeatWriter TTL stale 정리

## §1 배경

MCT-129(레이어 1) 이전 누적된 파일 + 설정 오류 안전망.
`HeartbeatWriter.run()` 시작 시 300s TTL 초과 파일 자동 삭제.

## §2 목표 및 범위

- `heartbeat.py`에 `import time` 추가
- `cleanup_stale_heartbeats(ttl_seconds=None)` 메서드 추가
- `run()` 첫 줄에 `self.cleanup_stale_heartbeats()` 추가
- 단위 테스트 6개 (`TestHeartbeatStaleCleanup`)

## §3 Acceptance Criteria

- [x] TTL(기본 300s) 초과 파일 삭제
- [x] 자기 파일(`heartbeat-{node_id}.json`) 보호
- [x] TTL 미만 활성 파일 보호
- [x] manifest_dir 부재 시 스킵
- [x] OSError 내성 (warn 로그, 수집 계속)
- [x] `run()` 시작 시 cleanup 1회 호출

## §4 설계 결정

spec: docs/superpowers/specs/2026-05-11-heartbeat-stale-cleanup-design.md §2 레이어 2

TTL env var: `MCTRADER_HEARTBEAT_STALE_CLEANUP_SECONDS` (기본 300s)

## §5 구현 노트

plan: docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md Task 2

## §6 테스트 전략

`TestHeartbeatStaleCleanup` 6 케이스: `os.utime` mtime 조작, monkeypatch stat, monkeypatch cleanup 호출 확인

## §7 Change Plan

N/A (spec §2 레이어 2 참조)

## §8 Test Contract

6 단위 테스트 (stale 삭제 / 자기 보호 / 신선 보호 / 디렉터리 부재 / OSError / run 호출)

## §9 Review

`docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md` Task 2

## §10 FIX Ledger

없음

## §11 PMO 회고

(PMOAgent dispatch 대기)
```

- [ ] **Step 3: MCT-131.md 생성**

`mctrader-hub/docs/stories/MCT-131.md`:

```markdown
---
story_key: MCT-131
story_scope: mctrader-web
status: done
created_at: 2026-05-11
completed_at: 2026-05-11
---

# MCT-131: 00_status.py active/stale 분기 방어적 렌더링

## §1 배경

레이어 1·2 미적용 환경 또는 미래 edge case 대비 최후 방어선.
`st.columns(len(result.nodes))` — 11개 노드 시 레이아웃 파괴 재발 방지.

## §2 목표 및 범위

- `active_nodes` (level 0/1) → `st.columns(max(1, len(active_nodes)))` + 기존 카드
- `stale_nodes` (level 2) → `st.expander(expanded=False)` 격리
- AppTest 3 케이스

## §3 Acceptance Criteria

- [x] active 노드만 컬럼 렌더링 (stale 제외)
- [x] stale 노드 expander에 격리 (접힘 기본)
- [x] active 0개 시 `st.columns(1)` — 크래시 없음
- [x] AppTest 3 케이스 PASS

## §4 설계 결정

spec: docs/superpowers/specs/2026-05-11-heartbeat-stale-cleanup-design.md §2 레이어 3

## §5 구현 노트

plan: docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md Task 3

## §6 테스트 전략

AppTest: mixed active+stale / all-stale / active-only 3 케이스

## §7 Change Plan

N/A (spec §2 레이어 3 참조)

## §8 Test Contract

3 AppTest: expander 격리 / all-stale 무충돌 / active-only 무 expander

## §9 Review

`docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md` Task 3

## §10 FIX Ledger

없음

## §11 PMO 회고

(PMOAgent dispatch 대기)
```

- [ ] **Step 4: commit**

```bash
cd c:/workspace/mclayer/mctrader-hub
git add docs/stories/MCT-129.md docs/stories/MCT-130.md docs/stories/MCT-131.md
git commit -m "docs(mct-129/130/131): Story files — heartbeat stale 3-layer defense"
```

---

## Self-Review

**Spec coverage 점검:**
- §2 레이어 1 (cli.py 1줄 수정) → Task 1 ✓
- §2 레이어 2 (HeartbeatWriter TTL 정리) → Task 2 ✓
- §2 레이어 3 (00_status.py 방어 렌더링) → Task 3 ✓
- §3 테스트 케이스 전체 → Task 1/2/3 테스트로 커버 ✓
- §6 scope_manifest `planned_files` 전체 → Task 1-4 파일 목록과 일치 ✓
- Story 파일 MCT-129/130/131 → Task 4 ✓

**Placeholder 없음** — 모든 step에 실제 코드 포함.

**타입 일관성:**
- `HeartbeatWriter(root=tmp_path, node_id="NODE_A")` — Task 2 전체 통일 ✓
- `_resolve_node_id(explicit: str | None) -> str` — Task 1 전체 통일 ✓
- `at.expander` — Streamlit AppTest API, Task 3 전체 통일 ✓
