# Collector HA — Phase 3 (MCT-92 Scan-side Merge + Dedup) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking. TDD 의무.

**Goal:** mctrader-data 측 read-side `scan_*` API 가 multi-node partition union + tier 별 logical key dedup 을 transparent 하게 수행. ADR-009 §D2.1 mixed legacy 영구 지원 + §D10.7 T2 6-tuple + §D11.8 T3 8-tuple best-effort + §D5 T1 late correction multi-node 적용. Epic AC B2 (transparent scan merge) + B6 (dedup 자체) + B7 (`active-active mismatch` quarantine reason) enforce. **X2-X3 window 운영 caveat 의 termination event** — X3 main merge 후 사용자는 양 node active-active + read 측 dedup 동시 가용.

**Architecture:** mctrader-data 0.6.0 → 0.7.0 의 flat layout 위에서 1 신규 module (`dedup.py`) + 4 modify (storage.py / orderbook_replay.py / policy.py quarantine reason / pyproject) + 4 신규/update test. DataEngineerAgent invariant 4개 변경 0 (read-only layer transparent). engine / web / WFO 변경 0 (caller 측 transparent — 기존 scan API signature 유지).

**Tech Stack:** Python 3.11+, DuckDB (hive_partitioning + UNION ALL BY NAME), pyarrow (Decimal128 row equality), pytest 8. 신규 runtime dependency 0.

**Spec:**
- Story: [docs/stories/MCT-92.md](../../stories/MCT-92.md) (PR #98 main merged, Codex 5/5 ADOPT)
- Sister X2: [docs/stories/MCT-91.md](../../stories/MCT-91.md) (mctrader-data 0.6.0 main merged)
- Parent Epic spec: [docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md](../specs/2026-05-05-collector-ha-active-active-design.md)
- ADR-009 amendment: [docs/adr/ADR-009-ohlcv-schema.md](../../adr/ADR-009-ohlcv-schema.md) §D2.1 / §D10.7 / §D11.8 / §D5
- Heartbeat contract: [docs/domain-knowledge/contracts/heartbeat-schema.v1.md](../../domain-knowledge/contracts/heartbeat-schema.v1.md)

**Working directory:** `c:/workspace/mclayer/mctrader-data/`

**Branch convention:** `feat/MCT-92-collector-ha-scan-dedup`

---

## Architect 결정 freeze (Sonnet decider, MCT-92 Story §5.4 의 8 결정)

본 plan 진입 전 design lane Architect 가 freeze 할 8 결정 — Sonnet decider 가 자율 채택:

| # | 결정점 | 채택 | 근거 |
|---|---|---|---|
| 1 | T1 multi-node late correction conflict resolution | **hybrid** = `received_at` MAX 우선 + tie-break 시 node priority alphabetical | clock drift mitigation 정합 (received_at 신뢰도 첫 시도) + 결정성 보장 (tie 시 alphabetical fallback) |
| 2 | legacy DEFAULT sentinel 명칭 | **`zzz_DEFAULT`** | ASCII order 끝 (NODE_A 보다 뒤). post-HA partition 우선 의도 정합 — uppercase 'N' (78) < lowercase 'z' (122) |
| 3 | Quarantine artifact 위치 | **root manifest** `<root>/market/manifest/quarantine/active-active-mismatch/<date>/<symbol>.json` | heartbeat 와 동형 location, X4 status CLI 가 read 하기 쉬움. parquet sidecar 패턴은 partition 폭주 시 IO 분산 어려움 |
| 4 | Multi-node mode activation criterion | **자동 감지** (distinct `node=` 값 ≥ 2) | transparent caller 의도 정합 — engine/web/WFO 의 scan API signature 변경 0 |
| 5 | Streaming dedup window size | **200ms** (ms-tolerance ±100ms × 2 safety margin) | received_at fallback 의 ms-drift + 안전 margin |
| 6 | DuckDB hive_partitioning missing-key handling | **legacy partition 의 sentinel substitution** — read 시 file system 의 legacy partition (no `node=` directory) 을 caller code 에서 `node=zzz_DEFAULT` 로 mapping (DuckDB 의 hive_partitioning behavior 의존 0) | DuckDB version 호환성 의존 제거 + explicit caller-side filter 가능 |
| 7 | `dedup.py` module 위치 | **flat `src/mctrader_data/dedup.py`** | 단일 책임 + test isolation + storage.py 폭증 방지 |
| 8 | Quarantine backpressure 정책 | **batching + rate-limit hybrid** — per-second cap = 100 mismatch (rate-limit), 100 초과 시 single artifact 에 100 mismatch batch (drop 방지) + `metrics.quarantine_count` 는 모든 mismatch count | disk 폭주 방지 + audit trail 무결성 + heartbeat metric integrity |

**escalation 0건** (사용자 사전 승인 = MCT-89 Epic Phase 1 의 16-row decision stack).

---

## Phase 3 deliverables

1. mctrader-data 0.6.0 → 0.7.0
2. 1 신규 module (`dedup.py`) + 4 modify (storage.py / orderbook_replay.py / policy.py / pyproject)
3. 4 신규/update test
4. PR #X (mctrader-data) + Codex 7-area review pass + admin merge
5. mctrader-hub plan doc commit (본 file)
6. mctrader-hub Story §8-9 update + Phase 3 close PR

## Out-of-scope (Phase 3)

- writer 측 (X2 완료, mctrader-data 0.6.0)
- coverage diagnostic + status CLI → X4 (mctrader-data, 별도 Story)
- ops scripts (systemd + Ansible) → X5 (mctrader-hub `scripts/ha/`)
- Streamlit status panel → X6 (mctrader-web)
- E2E demo + Calibration measurement → X7
- mctrader-engine / mctrader-web 변경 0 (caller transparent)
- T2 → T1 candle aggregation ordering (cross-tier, MCT-92 §3.3 explicit out-of-scope)

---

## Caller Propagation Matrix

| API | Signature 변경 | Caller (actual repo) | 영향 / 처리 정책 |
|---|---|---|---|
| `storage.scan_candles()` | **없음** (signature 유지) | `mctrader_engine.backtest` / `mctrader_web` / `mctrader_data.cli backfill_preview` 등 | **transparent** — caller 변경 0. multi-node 자동 감지로 dedup 적용 |
| `orderbook_replay.scan_ticks()` | **없음** | `mctrader_engine.tick_backtest` / 기타 | **transparent** |
| `orderbook_replay.scan_orderbook_events()` | **없음** | `mctrader_engine.orderbook_backtest` / 기타 | **transparent** |
| `orderbook_replay.tier_coverage()` | **없음** (recursive glob 으로 변경) | `mctrader_data.cli status` / 기타 | **forward + backward compat** — 신규 file naming + legacy `part-*.parquet` 양쪽 read |
| `dedup.deduplicate_candles()` 등 신규 | NEW | scan_candles / scan_ticks / scan_orderbook_events 의 internal | flat module, 단일 책임 |
| `policy.QuarantineReason` enum | `ACTIVE_ACTIVE_MISMATCH` 신규 추가 | quarantine emit 코드 (X3 신규) | enum 확장만, 기존 reason 영향 0 |

**핵심 정책**: 본 plan 의 모든 API 변경은 **caller-transparent**. engine / web / WFO 코드 변경 0 검증 의무.

---

## File Structure

| File | Action | 책임 |
|---|---|---|
| `src/mctrader_data/dedup.py` | NEW | tier 별 logical key extractor + node priority + content mismatch detector + quarantine emitter |
| `src/mctrader_data/storage.py` | MODIFY | `scan_candles()` (line ~146) — multi-node mode 자동 감지 + dedup 적용. `_resolve_scan_paths()` (line ~113) — legacy partition `zzz_DEFAULT` mapping |
| `src/mctrader_data/orderbook_replay.py` | MODIFY | `scan_ticks()` / `scan_orderbook_events()` / `tier_coverage()` — recursive partition glob (`**/node=*/**/*.parquet` + legacy `**/*.parquet`) + multi-node dedup + part-* / new naming 양쪽 read |
| `src/mctrader_data/policy.py` | MODIFY | `QuarantineReason` enum 에 `ACTIVE_ACTIVE_MISMATCH` 추가 |
| `pyproject.toml` | MODIFY | version 0.6.0 → 0.7.0 |
| `tests/test_dedup.py` | NEW | tier 별 logical key + node priority + mismatch detection unit test |
| `tests/test_active_active_dedup.py` | NEW | E2E — write 양 node + scan 단일 결과 dedup 검증 (T1 byte-identical / T2 best-effort / T3 best-effort + quarantine artifact 검증) |
| `tests/test_storage.py` / `test_orderbook_replay.py` | MODIFY | multi-node mode 자동 감지 + legacy partition `zzz_DEFAULT` mapping + recursive glob 검증 case 추가 |

---

## Task 0: Preflight (branch + version bump)

- [ ] **Step 1: branch 분기**

```powershell
cd c:/workspace/mclayer/mctrader-data
git checkout main && git pull --ff-only origin main
git checkout -b feat/MCT-92-collector-ha-scan-dedup
```

- [ ] **Step 2: version bump**

`pyproject.toml`: `version = "0.6.0"` → `"0.7.0"`

- [ ] **Step 3: commit**

```powershell
git add pyproject.toml
git commit -m "[MCT-92] chore: bump version 0.6.0 -> 0.7.0 for Phase 3 (collector HA scan + dedup)"
```

---

## Task 1: dedup.py 신규 module (TDD)

**Files:**
- Create: `src/mctrader_data/dedup.py`
- Create: `tests/test_dedup.py`

- [ ] **Step 1: TDD test 작성** (8+ test case)

```python
# tests/test_dedup.py
"""Tier별 logical key extractor + node priority + mismatch detector."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from mctrader_data.dedup import (
    candle_logical_key, tick_logical_key, orderbook_logical_key,
    NODE_PRIORITY_DEFAULT_SENTINEL,  # = "zzz_DEFAULT"
    deduplicate_candles, deduplicate_ticks, deduplicate_orderbook_events,
    DedupResult,
)

class TestLogicalKey:
    def test_t1_candle_4_key(self): ...  # (exchange, symbol, timeframe, ts_utc)
    def test_t2_tick_6_tuple(self): ...  # (exchange, symbol, ts_utc, price, quantity, side)
    def test_t3_orderbook_8_tuple(self): ...  # (exchange, symbol, ts_utc, event_type, side, level, price, quantity)

class TestNodePriority:
    def test_alphabetical_node_a_wins_over_node_b(self): ...
    def test_explicit_node_wins_over_zzz_default(self): ...

class TestT1LateCorrection:
    def test_hybrid_received_at_max_first(self):
        """동일 logical key (4-tuple) → received_at MAX 의 row win."""
    def test_hybrid_tie_breaks_to_node_priority(self):
        """received_at 동일 → node alphabetical 우선."""

class TestT2T3ContentMismatch:
    def test_t2_logical_key_match_no_mismatch(self):
        """received_at 다르지만 logical key 6-tuple + price/qty/side 일치 → idempotent skip."""
    def test_t2_logical_key_match_value_mismatch_quarantines(self):
        """logical key 동일 but price 다름 (실제로 발생 불가, byte-identical 위반) → quarantine."""

class TestQuarantineBackpressure:
    def test_per_second_rate_limit_100(self):
        """100 mismatch/sec 까지 individual artifact, 그 이상은 batch."""
```

- [ ] **Step 2: dedup.py implementation**

```python
# src/mctrader_data/dedup.py
"""Tier-별 logical key extractor + node priority + mismatch detector.

Per MCT-92 Phase 3 (X3 of MCT-89). Transparent read-side dedup.

Architect 결정 freeze (plan §"Architect 결정"):
- T1 hybrid late correction: received_at MAX + tie-break node priority alphabetical
- DEFAULT sentinel: zzz_DEFAULT (ASCII end, post-HA win)
- Quarantine: root manifest <root>/market/manifest/quarantine/.../*.json
- Backpressure: per-second 100 mismatch cap → batching
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, NamedTuple

NODE_PRIORITY_DEFAULT_SENTINEL = "zzz_DEFAULT"
QUARANTINE_RATE_LIMIT_PER_SEC = 100
DEDUP_WINDOW_MS = 200  # ms-tolerance ±100ms × 2 safety margin


def candle_logical_key(row) -> tuple[str, str, str, datetime]:
    """ADR-009 §D5 T1 — (exchange, symbol, timeframe, ts_utc)."""
    return (row.exchange, str(row.symbol), row.timeframe, row.ts_utc)


def tick_logical_key(row) -> tuple[str, str, datetime, Decimal, Decimal, str]:
    """ADR-009 §D10.7 T2 — fallback 6-tuple."""
    return (row.exchange, str(row.symbol), row.ts_utc, row.price, row.quantity, row.side)


def orderbook_logical_key(row) -> tuple:
    """ADR-009 §D11.8 T3 — fallback 8-tuple."""
    return (row.exchange, str(row.symbol), row.ts_utc, row.event_type,
            row.side, row.level, row.price, row.quantity)


def _node_priority(node_id: str | None) -> str:
    """ASCII alphabetical priority. None → zzz_DEFAULT (legacy)."""
    return node_id or NODE_PRIORITY_DEFAULT_SENTINEL


@dataclass
class DedupResult:
    emitted: list  # row 들 (deduplicated)
    dup_skip_count: int
    quarantine_count: int
    quarantine_records: list


def deduplicate_candles(rows: Iterable, *, multi_node: bool) -> DedupResult:
    """T1 hybrid late correction: received_at MAX + tie-break node priority."""
    if not multi_node:
        return DedupResult(emitted=list(rows), dup_skip_count=0,
                           quarantine_count=0, quarantine_records=[])
    # Group by logical key 4-tuple, choose row with MAX received_at, tie-break node priority
    by_key: dict = {}
    dup_skip = 0
    for row in rows:
        key = candle_logical_key(row)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = row
            continue
        # Compare: received_at MAX
        if row.received_at > existing.received_at:
            by_key[key] = row
            dup_skip += 1
        elif row.received_at < existing.received_at:
            dup_skip += 1
        else:
            # Tie: node priority alphabetical (lower = win)
            new_pri = _node_priority(getattr(row, 'node_id', None))
            old_pri = _node_priority(getattr(existing, 'node_id', None))
            if new_pri < old_pri:
                by_key[key] = row
            dup_skip += 1
    return DedupResult(emitted=sorted(by_key.values(), key=lambda r: r.ts_utc),
                       dup_skip_count=dup_skip, quarantine_count=0, quarantine_records=[])


def deduplicate_ticks(rows: Iterable, *, multi_node: bool) -> DedupResult:
    """T2 6-tuple dedup. mismatch on non-key value → quarantine."""
    # ... 비슷한 패턴 (logical key tuple 동일 → 첫 row 만 emit, value mismatch 시 quarantine)
    # see implementation 본문


def deduplicate_orderbook_events(rows: Iterable, *, multi_node: bool) -> DedupResult:
    """T3 8-tuple best-effort dedup."""
    # ...
```

- [ ] **Step 3: pytest pass + commit**

```powershell
uv run pytest tests/test_dedup.py -v
git add src/mctrader_data/dedup.py tests/test_dedup.py
git commit -m "[MCT-92] feat(dedup): tier별 logical key + node priority + T1 hybrid late correction"
```

---

## Task 2: policy.py — QuarantineReason 확장

- [ ] **Step 1: TDD test_policy.py 신규 case**

```python
def test_quarantine_reason_active_active_mismatch():
    from mctrader_data.policy import QuarantineReason
    assert QuarantineReason.ACTIVE_ACTIVE_MISMATCH.value == "active_active_mismatch"
```

- [ ] **Step 2: policy.py implementation**

```python
class QuarantineReason(StrEnum):
    # ... 기존 reason
    ACTIVE_ACTIVE_MISMATCH = "active_active_mismatch"
```

- [ ] **Step 3: commit**

---

## Task 3: storage.py:scan_candles 확장 (TDD)

multi-node mode 자동 감지 + dedup 적용. 기존 caller transparent.

- [ ] **Step 1: TDD test_storage.py 신규 case**

```python
def test_scan_candles_single_node_legacy_no_dedup(tmp_path):
    """legacy partition (node= 없음) 단일 → dedup off."""

def test_scan_candles_two_nodes_auto_dedup(tmp_path):
    """양 node partition → 자동 multi-node mode + dedup."""

def test_scan_candles_legacy_plus_node_a_dedup(tmp_path):
    """legacy (zzz_DEFAULT) + NODE_A 둘 다 있으면 NODE_A win (alphabetical)."""

def test_scan_candles_caller_signature_unchanged(tmp_path):
    """기존 caller 가 node_id 없이 호출 → 결과 동일 (transparent)."""
```

- [ ] **Step 2: storage.py modify — `_resolve_scan_paths` 에 `**/node=*/**/*.parquet` recursive glob + legacy mapping**

```python
def _resolve_scan_paths(...) -> list[str]:
    # 기존 + node= recursive glob
    # legacy partition 의 mapping 은 read 후 row level 에서 처리
    ...

def scan_candles(...) -> Iterable[CandleModel]:
    # 1. _resolve_scan_paths 로 union scan
    # 2. distinct node= 값 검증 → multi_node = (count >= 2)
    # 3. dedup.deduplicate_candles(rows, multi_node=multi_node)
    # 4. yield emit_rows
    ...
```

- [ ] **Step 3: pytest pass + commit**

---

## Task 4: orderbook_replay.py — scan_ticks / scan_orderbook_events / tier_coverage 확장 (TDD)

- [ ] **Step 1: TDD test_orderbook_replay.py 확장**

multi-node tick scan / multi-node orderbook scan / tier_coverage 의 recursive glob (legacy `part-*.parquet` + 신규 `{collector_run_id}-{batch_seq}.parquet` 양쪽).

- [ ] **Step 2: orderbook_replay.py modify**

`_read_parquet_rows` (line ~137) — recursive glob, `tier_coverage` (line ~340) — `**/*.parquet` recursive 로 확장. dedup 적용.

- [ ] **Step 3: pytest pass + commit**

---

## Task 5: integration test_active_active_dedup.py (E2E)

X2 의 `test_active_active_writer.py` 의 후속 — write 후 scan 했을 때 dedup 결과 검증.

- [ ] **Step 1: integration test 작성**

```python
@pytest.mark.asyncio
async def test_t1_byte_identical_dedup_single_emission(tmp_path):
    """양 node 가 같은 candle write → scan 결과 1 row (양 node 중 1개만)."""

def test_t2_best_effort_dedup_target(tmp_path):
    """양 node tick write → scan 결과 dedup_skip_count > 0 + emit count = 한 node 의 row count."""

def test_t3_best_effort_dedup_within_window(tmp_path):
    """T3 의 ms-tolerance ±100ms window 내 동일 logical key → dedup."""

def test_quarantine_artifact_root_manifest(tmp_path):
    """value mismatch 발생 시 quarantine artifact 가 root manifest 에 atomic write."""

def test_quarantine_backpressure_rate_limit(tmp_path):
    """100 mismatch/sec 초과 시 batching."""

def test_legacy_partition_zzz_default_mapping(tmp_path):
    """legacy partition (no node=) read 시 node=zzz_DEFAULT 로 mapping. NODE_A 와 같이 있으면 NODE_A win."""
```

- [ ] **Step 2: pytest pass + commit**

---

## Task 6: PR + Codex 7-area review + admin merge

- [ ] **Step 1: full pytest pass + branch push**

```powershell
uv run pytest -v  # 130+ test 모두 PASS
git push -u origin feat/MCT-92-collector-ha-scan-dedup
```

- [ ] **Step 2: PR 작성**

PR title: `[MCT-92] feat(ha): Scan-side merge + dedup (X3 of MCT-89, mctrader-data 0.7.0)`

PR body 의무 항목:
- AC enforcement (B2 / B6 / B7)
- Architect 결정 8항 (Sonnet decider freeze) 명시
- X2-X3 window caveat 의 termination event 명시 (운영 옵션 (a)~(c) 모두 X3 후 transparent)
- Out-of-scope (X4-X7)
- Test results

- [ ] **Step 3: Codex 7-area review (codex:rescue subagent)**

7 area:
1. Test coverage (B2/B6/B7 + 12 edge case 모두 cover)
2. dedup module correctness (T1 hybrid / T2/T3 best-effort / node priority alphabetical / zzz_DEFAULT sentinel)
3. Caller transparency (engine / web / WFO 변경 0)
4. ADR-009 §D2.1/§D5/§D10.7/§D11.8 enforcement
5. Backpressure 정책 정확성 (rate-limit 100/sec + batching)
6. mixed legacy + post-HA scan 정합성
7. X4 (status CLI) prerequisite (counter API + quarantine artifact format)

- [ ] **Step 4: Sonnet decider 합성 + inline-fix + new commit**

- [ ] **Step 5: CI watch + admin merge**

```powershell
gh pr checks <PR#> --repo mclayer/mctrader-data --watch
gh pr merge <PR#> --repo mclayer/mctrader-data --admin --squash --delete-branch
```

CI failure (ruff lint 등) 시 자동 fix → push → 재 watch.

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Architect 결정 8항 (§"Architect 결정") 모두 plan 에서 freeze
- [x] Caller Propagation Matrix (engine/web/WFO transparent) 명시
- [x] AC B2/B6/B7 매핑 명확 (Task 3+4+5)

**2. TDD discipline:**
- [x] Task 1, 3, 4, 5 모두 Step 1=test → Step 2=impl → Step 3=pass+commit

**3. Backward compat:**
- [x] storage.scan_candles / orderbook_replay.scan_* / tier_coverage 모두 signature 변경 0
- [x] legacy `part-{snapshot_id}.parquet` + 신규 `{collector_run_id}-{batch_seq}.parquet` 양쪽 read
- [x] legacy partition (no node=) → zzz_DEFAULT 자동 mapping

**4. Out-of-scope (X4-X7):**
- [x] coverage diagnostic / status CLI / ops scripts / web panel / E2E demo / cross-tier T2→T1 모두 분리

**5. X2-X3 window termination:**
- [x] X3 main merge 후 사용자 옵션 (a)~(c) 모두 transparent dedup 으로 자연 해소
- [x] X4 status CLI 도착 전까지 quarantine artifact 가시성 = 사용자가 grep 의무 (의도된 phase boundary)

---

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-05-06-collector-ha-phase-3.md`. Phase 3 의 task 0-6 + step ~25 합계는 dedup algorithm + integration test 기준 약 5-7시간 소요 예상.

Inline execution 권장 — Task 0~6 sequential + checkpoint review. TDD red-green-refactor 강제.

---

## Codex Review Fix Log (Phase 3 plan 진입 직전 review, 2026-05-06)

Codex 7-area review 결과: needs-fix (1 PUSH-BACK + 5 NIT). Sonnet decider 6/6 ADOPT.

**F-1 (Area 1 NIT) — Architect override**: Architect override 가능 지점은 X7 Calibration 의 tolerance 조정 (ms-tolerance ±100ms / dedup window 200ms / target T2>99% T3>95%) 뿐. 본 plan §"Architect 결정" 의 8항 freeze 는 design lane 진입 후 변경 시 별도 minor amendment + Story §10 FIX Ledger 기록 의무.

**F-2 (Area 2 PUSH-BACK) — heartbeat metrics emit hook wiring**: dedup module 의 `dup_skip_count` / `quarantine_count` cumulative counter 가 heartbeat-schema.v1 의 `metrics.dup_skip_count` / `metrics.quarantine_count` field 로 emit 되어야 (X4/X6 가 read 의무, Story §3.1 line 152). Task 1 의 `dedup.py` 가 callback 또는 metric registry 노출 + Task 3/4 의 `scan_*` API 가 heartbeat writer 에 inject 가능 path. 단 X3 자체는 *mctrader-data 단독* 이라 collector daemon (X2 의 `MultiSymbolCollector`) 의 heartbeat writer 와 wiring 은 별도 추후 — X3 의 책임은 **counter 노출 API + 호출자가 heartbeat writer 를 inject 받을 수 있는 hook**. **Task 1 에 추가 subtask**: `DedupCounterSink` protocol 정의 + Task 5 E2E 에 "heartbeat metrics 와 dedup counter 일치" assertion test.

**F-3 (Area 3 NIT) — Task 1 T3 mismatch test**: Task 1 의 `TestT2T3ContentMismatch` class 에 `test_t3_logical_key_match_value_mismatch_quarantines` 추가 — T3 8-tuple logical key 동일 + 비-key value mismatch (best-effort scenario) 시 quarantine 동작.

**F-4 (Area 4 ADOPT-AS-IS)** — 변경 없음.

**F-5 (Area 5 NIT) — file path de-dup**: recursive glob `**/node=*/**/*.parquet` + legacy `**/*.parquet` 사용 시 같은 file 이 양 glob 에 중복 매칭 가능. **mitigation**: `_resolve_scan_paths` 가 `set` 으로 path 모음 후 sorted list 반환 — 단일 glob 결과 union 후 deduplicate.

**F-6 (Area 6 NIT) — backpressure 구현 세부**:
- **monotonic clock 사용** (`time.monotonic()`) — wall clock skew 영향 0
- **per-scan single-thread assumption** 명시 — scan_* API 는 사용자 호출 시점에 생성된 generator, 동일 scan 내에서 single-threaded 의무. multi-thread caller 는 별도 dedup instance 사용 의무.
- **artifact count vs `quarantine_count` 분리 검증**: artifact write 는 100/sec batching 적용, counter 는 모든 mismatch count. test_dedup.py 에 `test_quarantine_count_includes_batched_mismatches` 추가.

**F-7 (Area 7 NIT) — Task 3 첫 step DuckDB regression test**: Task 3 Step 1 에 추가:
- legacy partition (`node=` directory 없음) + post-HA partition (`node=NODE_A` directory 있음) mixed fixture 작성
- DuckDB `hive_partitioning=true` 의 `node` column behavior 실측 검증 (NULL / sentinel string / error)
- caller-side `zzz_DEFAULT` substitution 정합 검증

**Sonnet decider 합성 결과**: 6/6 ADOPT, REJECT 0건, 사용자 escalation 0건. parent X2 Phase 2 plan review (1 REJECT + 4 PUSH-BACK + 2 NIT) 보다 REJECT 0 — grounding density 향상.
