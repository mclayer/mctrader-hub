# MCT-165 Data Accumulation Health Framework + 3 follow-up Verify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MCT-103 / MCT-160 R7 / 50-sym 5d health 3 follow-up 을 단일 health framework (4 layer = volume / gap / file_count / lag) 로 결합 + 반복 실행 가능 CLI 산출. forward-only invariant (ADR-009 §D12) detective only 원칙 박제 + rolling baseline / SLO budget 후속 ADR 자리 예약.

**Architecture:** codeforge consumer 표준 1 Story = 2 PR pair (Phase 1 hub PR docs only + Phase 2 mctrader-data code + mctrader-hub Phase 2 docs). 신규 모듈 = `mctrader_data/health/` (격리), CLI = 기존 `cli.py` extend (subcommand `health-check`). Read-only (INV-1) — fs walk 만, write 없음. 정적 threshold ±20% + rolling stub `NotImplementedError`.

**Tech Stack:** Python 3.13, pytest, pyarrow (parquet metadata read), prometheus_client (exit code/metric 정합), Docker compose. codeforge plugins (codeforge-design / codeforge-develop / codeforge-test / codeforge-review / codeforge-pmo).

**Spec reference:** [docs/superpowers/specs/2026-05-14-MCT-165-data-accumulation-health-design.md](../specs/2026-05-14-MCT-165-data-accumulation-health-design.md)

---

## File Structure

### mctrader-hub (governance)

- **Create**: `docs/stories/MCT-165.md` — Story file (§1-§12)
- **Create**: `docs/adr/ADR-028-rolling-baseline-threshold.md` — Reserved status stub (Phase 1 PR)
- **Create**: `docs/domain-knowledge/domain/data-health/README.md` — 7 layer 분류 + forward-only detective + SLO budget
- **Create**: `docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md` — D+5 V1/V2/V3 실측 박제
- **Create**: `docs/domain-knowledge/domain/data-health/verify-d7-2026-05-16.md` — D+7 checkpoint
- **Create**: `scope_manifests/MCT-165.yaml` — scope_manifest IN_PROGRESS
- **Modify**: `.codeforge/counters.json` — MCT-165 reservation 추가
- **Modify**: `CLAUDE.md` — §데이터 헬스 프레임워크 신규 (Phase 2 PR)
- **Create**: `docs/retros/RETRO-MCT-165.md` — Phase 2 land 직후 PMOAgent dispatch

### mctrader-data (구현)

- **Create**: `src/mctrader_data/health/__init__.py`
- **Create**: `src/mctrader_data/health/volume.py` — volume layer measurement
- **Create**: `src/mctrader_data/health/gap.py` — gap layer measurement
- **Create**: `src/mctrader_data/health/file_count.py` — file_count layer measurement
- **Create**: `src/mctrader_data/health/lag.py` — collector lag measurement
- **Create**: `src/mctrader_data/health/thresholds.py` — 정적 ±20% + rolling stub
- **Create**: `src/mctrader_data/health/report.py` — JSON/CSV/markdown 생성
- **Modify**: `src/mctrader_data/cli.py` — `health-check` subcommand 추가 (entrypoint)
- **Create**: `tests/unit/health/test_thresholds.py`
- **Create**: `tests/unit/health/test_volume.py`
- **Create**: `tests/unit/health/test_gap.py`
- **Create**: `tests/unit/health/test_file_count.py`
- **Create**: `tests/unit/health/test_lag.py`
- **Create**: `tests/unit/health/test_report.py`
- **Create**: `tests/integration/health/test_cli_exit_code.py`
- **Modify**: `CLAUDE.md` — §health 모듈 신규 (Phase 2 PR)

---

## Task 1: Phase 1 사전 — counter / Issue / scope_manifest

**Files:**
- Modify: `mctrader-hub/.codeforge/counters.json`
- Create: `mctrader-hub/scope_manifests/MCT-165.yaml`
- GitHub: mctrader-hub Issue #MCT-165 (Phase 1 PR target)

- [ ] **Step 1: counters.json — MCT-165 reservation 추가**

```bash
python -c "
import json, pathlib
p = pathlib.Path('.codeforge/counters.json')
d = json.loads(p.read_text())
assert 'MCT-165' not in d['reservations'], 'MCT-165 already reserved'
d['counters']['mctrader-hub']['next'] = 166
d['reservations']['MCT-165'] = {
    'title': 'Data Accumulation Health Verification — Framework + 3 follow-up Verify',
    'reserved_at': '2026-05-14',
    'reserved_by': 'Orchestrator (codeforge-brainstorm Phase 2)',
    'cross_ref': ['MCT-103', 'MCT-160 R7', 'MCT-163 (F3+F6+F7 streaming reserved)', 'MCT-164 (upbit L1 root cause placeholder)']
}
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
print('counters.json updated')
"
```

기대 출력: `counters.json updated`.

- [ ] **Step 2: scope_manifest IN_PROGRESS 등록**

`scope_manifests/MCT-165.yaml` 생성. Content:

```yaml
story: MCT-165
status: IN_PROGRESS
title: Data Accumulation Health Verification — Framework + 3 follow-up Verify
brainstorm_spec: docs/superpowers/specs/2026-05-14-MCT-165-data-accumulation-health-design.md
plan: docs/superpowers/plans/2026-05-14-mct-165-data-accumulation-health.md

planned_adrs:
  reservation_only:
    - rolling-baseline-threshold
    - data-health-slo-budget
  amendment: []

planned_files:
  mctrader-hub:
    - docs/stories/MCT-165.md
    - docs/adr/ADR-028-rolling-baseline-threshold.md (stub Reserved)
    - docs/domain-knowledge/domain/data-health/README.md
    - docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md
    - docs/domain-knowledge/domain/data-health/verify-d7-2026-05-16.md
    - scope_manifests/MCT-165.yaml
    - .codeforge/counters.json (MCT-165 reservation)
    - CLAUDE.md (§데이터 헬스 프레임워크)
    - docs/retros/RETRO-MCT-165.md
  mctrader-data:
    - src/mctrader_data/health/__init__.py
    - src/mctrader_data/health/volume.py
    - src/mctrader_data/health/gap.py
    - src/mctrader_data/health/file_count.py
    - src/mctrader_data/health/lag.py
    - src/mctrader_data/health/thresholds.py
    - src/mctrader_data/health/report.py
    - src/mctrader_data/cli.py (health-check subcommand)
    - tests/unit/health/test_thresholds.py
    - tests/unit/health/test_volume.py
    - tests/unit/health/test_gap.py
    - tests/unit/health/test_file_count.py
    - tests/unit/health/test_lag.py
    - tests/unit/health/test_report.py
    - tests/integration/health/test_cli_exit_code.py
    - CLAUDE.md (§health 모듈)

planned_claude_md_sections:
  - mctrader-hub/CLAUDE.md §데이터 헬스 프레임워크
  - mctrader-data/CLAUDE.md §health 모듈
```

- [ ] **Step 3: GitHub Issue 생성**

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-165] Data Accumulation Health Verification — Framework + 3 follow-up Verify" \
  --label "type:story" \
  --label "epic:data-accumulation-umbrella" \
  --body-file - <<'EOF'
## Goal

MCT-103 / MCT-160 R7 / 50-sym 5d health 3 follow-up 을 단일 health framework (4 layer) 로 결합 + 반복 실행 가능 CLI 산출.

## Cross-ref

- MCT-103 (50-sym universe, MERGED 2026-05-09) — V1 부피 추산 베이스
- MCT-160 R7 (upbit L1 lost) — V2 partition 0 verdict
- MCT-164 (upbit L1 root cause, reserved) — V2 잔존 시 trigger

## Spec & Plan

- spec: `docs/superpowers/specs/2026-05-14-MCT-165-data-accumulation-health-design.md`
- plan: `docs/superpowers/plans/2026-05-14-mct-165-data-accumulation-health.md`
- scope_manifest: `scope_manifests/MCT-165.yaml`

## Phase 분할

| Phase | 산출물 | wall-clock |
|---|---|---|
| Phase 1 PR | docs only — spec / plan / Story file / ADR stub / domain-knowledge / scope_manifest | 즉시 |
| Phase 2 PR | framework CLI + D+5 verify (V1/V2/V3) + D+7 checkpoint | 2026-05-14 → 2026-05-16 |
| D+30 (out-of-PR) | framework merge 후 follow-up commit | 2026-06-08 |

EOF
```

- [ ] **Step 4: Commit Phase 1 사전**

```bash
git checkout -b mct-165-phase-1
git add .codeforge/counters.json scope_manifests/MCT-165.yaml
git commit -m "chore(MCT-165): counter reservation + scope_manifest IN_PROGRESS + Issue link"
```

---

## Task 2: Phase 1 — Story file + ADR stub + domain-knowledge 박제

**Files:**
- Create: `mctrader-hub/docs/stories/MCT-165.md`
- Create: `mctrader-hub/docs/adr/ADR-028-rolling-baseline-threshold.md` (ADR 번호는 Step 2 에서 확정)
- Create: `mctrader-hub/docs/domain-knowledge/domain/data-health/README.md`

- [ ] **Step 1: Story file §1-§7 작성 (Phase 1 land 본문)**

`docs/stories/MCT-165.md` 작성. spec §1-§9 의 내용 + Story file §1-§7 표준 구조 (Context / Why / D-결정 / AC / Invariant / Risk / Scope). MCT-162.md / MCT-160.md 패턴 답습. §8 Test Contract / §10 FIX Ledger / §11 PMO retro / §12 PMO self-write 는 Phase 2 에서 박제.

- [ ] **Step 2: ADR 번호 확보 + stub 작성**

```bash
ls docs/adr/ | grep -oE 'ADR-[0-9]+' | sort -V | tail -3
# 마지막 + 1 → 신규 ADR-NNN 번호 확정
```

`docs/adr/ADR-028-rolling-baseline-threshold.md`:

```markdown
---
adr: NNN
title: Rolling Distribution Baseline for Data Health Threshold
status: Reserved
date: 2026-05-14
story: MCT-165 (reservation only — content 후속 별 PR)
---

# ADR-NNN: Rolling Baseline Threshold

## Status

**Reserved** — 본 ADR 은 MCT-165 Phase 1 PR 에서 자리 예약만. 본문은 본 Story 종료 후 별 PR 발의.

## Context (placeholder)

MCT-165 framework 의 정적 ±20% 임계값 (volume layer) 이 50-sym universe 변동성에 over/under-fit 위험 (MCT-165 R1). rolling distribution baseline (예: 7d trailing mean ± 2σ) 도입 필요.

## Decision (예약)

본문 후속 박제.

## Cross-ref

- MCT-165 R1 (정적 임계값 false alert 누적 위험)
- MCT-103 (50-sym 전환 후 부피 변동성)
```

- [ ] **Step 3: domain-knowledge README 박제**

`docs/domain-knowledge/domain/data-health/README.md`:

```markdown
---
domain: data-health
created: 2026-05-14
story: MCT-165
---

# Data Health Domain Knowledge

## 1. Data Health 7 layer 다층성

forward-only invariant 환경 (ADR-009 §D12) 에서 "데이터가 제대로 쌓이고 있는가" 는 단일 metric 으로 판정 불가. 7 layer 로 분해:

| Layer | 정의 | MVP 채택 (MCT-165) |
|---|---|---|
| presence | 파일 존재 여부 | 후속 |
| completeness | 예상 row 수 대비 실측 | 후속 |
| continuity | time-gap 부재 | **채택 (gap layer)** |
| volume | 부피 분포 | **채택 (volume layer)** |
| schema | 컬럼 / 타입 일관성 | 후속 |
| cross-exchange parity | 동시각 sym 정합 | 후속 |
| collector lag | write → now 지연 | **채택 (lag layer)** |

추가: file count (continuity 의 sub-dimension, MVP 채택).

## 2. Forward-only Invariant — detective only

ADR-009 §D12: collect 시작 시점 = backtest history 시작 시점. 1d 지연 = 1d 영구 손실 (no backfill).

→ data health framework 는 **detective only**, corrective 불가. 검증 주기 ≤ 허용 손실 window 보장 의무.

## 3. SLO-based Health Budget

"정상" 정의 = binary 아닌 threshold 기반:
- volume: ±20% (정적 — MCT-165 R1 후속 ADR rolling baseline 진입 예정)
- gap: 0 strict (forward-only invariant 직접 반영)
- file_count: expected daily count 정확 일치
- lag: <60s (live 거래 가능 SLA)

threshold 미정의 = health check noise. SLO budget 부재 = alert fatigue.

## 4. Boundary crossing (universe rotation)

2026-05-09 = 10-sym → 50-sym 전환 시점 (MCT-103). 동일 검증기가 양쪽 데이터 join 시 false positive 폭발 → MCT-165 INV-2: 검증 시작점 = 2026-05-09 이후 cut-in.

## 5. Cross-ref

- ADR-009 §D12 (forward-only invariant)
- ADR-017 / ADR-027 (L1/L2/L3 tiering)
- MCT-103 (50-sym universe 전환)
- MCT-160 R7 (upbit L1 partition 0 잔존)
- MCT-165 (본 framework Story)
```

- [ ] **Step 4: Commit Phase 1 본문**

```bash
git add docs/stories/MCT-165.md docs/adr/ADR-NNN-*.md docs/domain-knowledge/domain/data-health/README.md
git commit -m "docs(MCT-165): Phase 1 — Story file §1-§7 + ADR-NNN stub Reserved + domain-knowledge README 박제"
```

---

## Task 3: Phase 1 PR open + 설계리뷰 lane

**Files:**
- GitHub: mctrader-hub PR (Phase 1)

- [ ] **Step 1: Phase 1 PR push + open**

```bash
git push -u origin mct-165-phase-1
gh pr create --repo mclayer/mctrader-hub \
  --title "[MCT-165] Phase 1 — spec + plan + Story file + ADR stub + domain-knowledge 박제" \
  --base main --head mct-165-phase-1 \
  --label "type:story" --label "phase:설계" \
  --body "MCT-165 Phase 1 (docs only). Closes step-1 of MCT-165 Issue.

## Scope
- docs/superpowers/specs/2026-05-14-MCT-165-data-accumulation-health-design.md
- docs/superpowers/plans/2026-05-14-mct-165-data-accumulation-health.md
- docs/stories/MCT-165.md §1-§7
- docs/adr/ADR-028-rolling-baseline-threshold.md (Reserved)
- docs/domain-knowledge/domain/data-health/README.md (7-layer 박제)
- scope_manifests/MCT-165.yaml (IN_PROGRESS)
- .codeforge/counters.json (MCT-165 reservation)

## Test plan
- [ ] CI: `dogfood-artifact-paths` PASS (Phase 1 docs only)
- [ ] DesignReviewPLAgent dispatch 후 §1-§7 검수
- [ ] codex review (mctrader consumer codeforge upgrade) 정합 확인"
```

- [ ] **Step 2: DesignReviewPLAgent dispatch (별 subagent)**

`codeforge-review:DesignReviewPLAgent` spawn — Phase 1 PR review. fail 시 issue fix → 별 commit.

- [ ] **Step 3: CI PASS + admin merge**

CI green → memory `feedback_admin_merge_autonomy` 따라 즉시 admin merge.

```bash
gh pr merge <PR#> --admin --squash --delete-branch
```

---

## Task 4: Phase 2 — health module skeleton + thresholds (TDD)

**Files (mctrader-data working dir):**
- Create: `src/mctrader_data/health/__init__.py`
- Create: `src/mctrader_data/health/thresholds.py`
- Create: `tests/unit/health/__init__.py`
- Create: `tests/unit/health/test_thresholds.py`

> **Working dir 전환**: 본 Task 부터 mctrader-data repo. parallel branch race 회피 — memory `feedback_parallel_session_branch_race` 참조. `git -C c:/workspace/mclayer/mctrader-data checkout -b mct-165-phase-2`.

- [ ] **Step 1: failing test 작성**

`tests/unit/health/test_thresholds.py`:

```python
import pytest
from mctrader_data.health.thresholds import (
    static_volume_threshold,
    static_lag_threshold,
    rolling_threshold,
)


def test_static_volume_threshold_within_20pct_pass():
    assert static_volume_threshold(actual=4.2, expected=4.35, tol=0.20).verdict == "PASS"


def test_static_volume_threshold_outside_20pct_fail():
    assert static_volume_threshold(actual=2.0, expected=4.35, tol=0.20).verdict == "FAIL"


def test_static_lag_threshold_under_60s_pass():
    assert static_lag_threshold(actual_seconds=30).verdict == "PASS"


def test_static_lag_threshold_over_60s_fail():
    assert static_lag_threshold(actual_seconds=90).verdict == "FAIL"


def test_rolling_threshold_not_implemented():
    with pytest.raises(NotImplementedError, match="rolling baseline reserved.*ADR"):
        rolling_threshold(actual=4.2, window_days=7)
```

- [ ] **Step 2: 테스트 fail 확인**

```bash
cd c:/workspace/mclayer/mctrader-data
pytest tests/unit/health/test_thresholds.py -v
```

Expected: 5 tests FAIL (ImportError).

- [ ] **Step 3: minimal impl**

`src/mctrader_data/health/__init__.py`: empty.

`src/mctrader_data/health/thresholds.py`:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ThresholdResult:
    actual: float
    expected: float | None
    verdict: Literal["PASS", "WARN", "FAIL"]
    detail: str


def static_volume_threshold(actual: float, expected: float, tol: float = 0.20) -> ThresholdResult:
    """정적 ±tol 임계값 — MCT-165 D5=C (rolling baseline reserved)."""
    deviation = abs(actual - expected) / expected if expected else float("inf")
    if deviation <= tol:
        return ThresholdResult(actual, expected, "PASS", f"deviation={deviation:.2%} <= ±{tol:.0%}")
    return ThresholdResult(actual, expected, "FAIL", f"deviation={deviation:.2%} > ±{tol:.0%}")


def static_lag_threshold(actual_seconds: float, slo_seconds: float = 60) -> ThresholdResult:
    """collector lag SLA — MCT-165 D5=C."""
    verdict: Literal["PASS", "FAIL"] = "PASS" if actual_seconds <= slo_seconds else "FAIL"
    return ThresholdResult(actual_seconds, slo_seconds, verdict, f"lag={actual_seconds:.0f}s SLO={slo_seconds:.0f}s")


def rolling_threshold(actual: float, window_days: int = 7) -> ThresholdResult:
    """rolling distribution baseline — MCT-165 D5=C 자리 예약. 후속 ADR-028 (rolling-baseline-threshold) 진입."""
    raise NotImplementedError(
        "rolling baseline reserved for follow-up ADR — see docs/adr/ADR-028-rolling-baseline-threshold.md"
    )
```

- [ ] **Step 4: pass 확인**

```bash
pytest tests/unit/health/test_thresholds.py -v
```

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mctrader_data/health/__init__.py src/mctrader_data/health/thresholds.py tests/unit/health/
git commit -m "feat(MCT-165): health.thresholds — 정적 ±20% + rolling stub (NotImplementedError)"
```

---

## Task 5: volume layer (TDD)

**Files:**
- Create: `src/mctrader_data/health/volume.py`
- Create: `tests/unit/health/test_volume.py`

- [ ] **Step 1: failing test 작성**

`tests/unit/health/test_volume.py`:

```python
from pathlib import Path
from datetime import date

from mctrader_data.health.volume import measure_volume


def test_measure_volume_sums_parquet_sizes(tmp_path: Path):
    # Setup: 3 parquet files for 1 sym × 1 day
    sym_dir = tmp_path / "BTC" / "2026-05-10"
    sym_dir.mkdir(parents=True)
    (sym_dir / "00.parquet").write_bytes(b"x" * 1024 * 1024)  # 1 MiB
    (sym_dir / "01.parquet").write_bytes(b"x" * 2 * 1024 * 1024)  # 2 MiB
    (sym_dir / "02.parquet").write_bytes(b"x" * 3 * 1024 * 1024)  # 3 MiB

    result = measure_volume(
        root=tmp_path,
        symbols=["BTC"],
        start_date=date(2026, 5, 10),
        end_date=date(2026, 5, 10),
    )
    assert result.total_bytes == 6 * 1024 * 1024
    assert result.per_sym["BTC"] == 6 * 1024 * 1024
    assert result.per_day[date(2026, 5, 10)] == 6 * 1024 * 1024


def test_measure_volume_respects_cutin_2026_05_09(tmp_path: Path):
    """INV-2: 검증 시작점 = 2026-05-09 이후 cut-in."""
    sym_dir = tmp_path / "BTC" / "2026-05-08"
    sym_dir.mkdir(parents=True)
    (sym_dir / "00.parquet").write_bytes(b"x" * 1024 * 1024)

    result = measure_volume(
        root=tmp_path,
        symbols=["BTC"],
        start_date=date(2026, 5, 9),
        end_date=date(2026, 5, 14),
    )
    assert result.total_bytes == 0  # 05-08 데이터 cut off
```

- [ ] **Step 2: fail 확인 → impl**

`src/mctrader_data/health/volume.py`:

```python
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


@dataclass
class VolumeResult:
    total_bytes: int
    per_sym: dict[str, int] = field(default_factory=dict)
    per_day: dict[date, int] = field(default_factory=dict)


def measure_volume(
    root: Path,
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> VolumeResult:
    """parquet 부피 측정 — read-only fs walk (INV-1 detective only).

    Layout 가정: <root>/<symbol>/<YYYY-MM-DD>/*.parquet
    실제 collector layout 은 Step 4 에서 path.py 확인 후 reconcile.
    """
    result = VolumeResult(total_bytes=0)
    cur = start_date
    while cur <= end_date:
        day_total = 0
        for sym in symbols:
            sym_day = root / sym / cur.isoformat()
            if not sym_day.is_dir():
                continue
            sym_total = sum(f.stat().st_size for f in sym_day.glob("*.parquet"))
            result.per_sym[sym] = result.per_sym.get(sym, 0) + sym_total
            day_total += sym_total
        if day_total > 0:
            result.per_day[cur] = day_total
        result.total_bytes += day_total
        cur += timedelta(days=1)
    return result
```

- [ ] **Step 3: pass + reconcile path layout**

```bash
pytest tests/unit/health/test_volume.py -v
# PASS 확인 후
python -c "from mctrader_data.path import *; help(...)"  # 실제 collector layout 확인
```

실제 mctrader-data collector layout (storage.py / orderbook_storage.py / path.py) 와 reconcile 의무. layout 다르면 `volume.py` 의 `root / sym / cur.isoformat()` 부분 수정 + 테스트 fixture 도 갱신.

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_data/health/volume.py tests/unit/health/test_volume.py
git commit -m "feat(MCT-165): health.volume — parquet 부피 fs walk (INV-1 read-only, INV-2 2026-05-09 cut-in)"
```

---

## Task 6: gap / file_count / lag layer (TDD, 3 sub-task 통합)

> 각 layer 는 volume 과 동일 패턴 (TDD failing test → minimal impl → pass → commit). 본 Task 는 3 layer 동시 진행 group.

**Files:**
- Create: `src/mctrader_data/health/{gap,file_count,lag}.py`
- Create: `tests/unit/health/test_{gap,file_count,lag}.py`

- [ ] **Step 1: gap layer**
  - test: 50-sym × 5d expected = 250 partition. 1 sym × 1 day 누락 시 verdict=FAIL + 누락 location 표시.
  - impl: 각 sym 마다 expected daily partition 존재 여부 walk → `MissingPartition` list.
  - INV-2 (cut-in 2026-05-09) 적용.

- [ ] **Step 2: file_count layer**
  - test: 1 day 당 expected file count (예: tick = 24h × N files/h). actual 실측 vs expected 비율.
  - impl: `sum(1 for f in sym_day.glob("*.parquet"))`. expected = collector cadence 파라미터 (config 에서 read).

- [ ] **Step 3: lag layer**
  - test: collector last write time vs now. `lag = now - max(file.mtime)` 초 단위.
  - impl: `Path.stat().st_mtime` 의 sym 별 max. lag > 60s → FAIL (정적 SLO).

- [ ] **Step 4: 통합 commit**

```bash
git add src/mctrader_data/health/{gap,file_count,lag}.py tests/unit/health/test_{gap,file_count,lag}.py
git commit -m "feat(MCT-165): health.{gap,file_count,lag} — 3 layer measurement (TDD)"
```

---

## Task 7: report module + CLI entrypoint (TDD)

**Files:**
- Create: `src/mctrader_data/health/report.py`
- Modify: `src/mctrader_data/cli.py` — `health-check` subcommand
- Create: `tests/unit/health/test_report.py`
- Create: `tests/integration/health/test_cli_exit_code.py`

- [ ] **Step 1: report module — JSON/CSV/markdown 생성**

test: 4 layer 결과 dict → markdown 보고서 string 생성. JSON serializable. CSV header = [layer, metric, actual, expected, verdict].

impl: `health/report.py`. dataclass `HealthReport` + `to_json() / to_csv() / to_markdown()` methods.

- [ ] **Step 2: CLI subcommand — `health-check`**

`src/mctrader_data/cli.py` extend (기존 `cli.py` 에 subparser 추가). 신규 subcommand:

```python
def add_health_check_subcommand(subparsers):
    p = subparsers.add_parser("health-check", help="Data accumulation health verification (MCT-165)")
    p.add_argument("--target", choices=["collector"], required=True)
    p.add_argument("--window", default="7d", help="검증 window (e.g., 5d, 7d, 30d)")
    p.add_argument("--symbols", nargs="+", help="대상 symbols (omit = universe 전체)")
    p.add_argument("--start-date", default="2026-05-09", help="INV-2 cut-in (default 2026-05-09)")
    p.add_argument("--output", choices=["json", "csv", "markdown"], default="markdown")
    p.add_argument("--baseline", choices=["static", "rolling"], default="static",
                   help="rolling 은 NotImplementedError — ADR-NNN reserved")
    p.set_defaults(func=health_check_command)


def health_check_command(args):
    from datetime import date, timedelta
    from mctrader_data.health import volume, gap, file_count, lag, report, thresholds

    # window parse → start/end date
    # 4 layer measure
    # threshold apply (static)
    # report 생성
    # exit code: 0=ALL PASS, 1=any FAIL, 2=tool error
    ...  # 실제 wiring 은 Step 4 에서 reconcile
```

- [ ] **Step 3: integration test — exit code contract (AC2/INV-4)**

`tests/integration/health/test_cli_exit_code.py`:

```python
import subprocess
from pathlib import Path


def test_cli_exit_0_when_all_pass(tmp_path: Path, monkeypatch):
    # Setup: synthetic data matching threshold expectations
    ...
    result = subprocess.run(
        ["python", "-m", "mctrader_data.cli", "health-check",
         "--target", "collector", "--window", "5d"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_cli_exit_1_when_any_fail(tmp_path: Path, monkeypatch):
    # Setup: missing partition → gap FAIL
    ...
    result = subprocess.run([...])
    assert result.returncode == 1


def test_cli_exit_2_on_rolling_baseline_request(tmp_path: Path):
    result = subprocess.run(
        ["python", "-m", "mctrader_data.cli", "health-check",
         "--target", "collector", "--baseline", "rolling"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "rolling baseline reserved" in result.stderr.lower()
```

- [ ] **Step 4: 모든 테스트 pass + commit**

```bash
pytest tests/unit/health/ tests/integration/health/ -v
git add src/mctrader_data/health/report.py src/mctrader_data/cli.py tests/
git commit -m "feat(MCT-165): health.report + CLI health-check subcommand (AC1/AC2/AC7 + INV-4 exit code)"
```

---

## Task 8: V1 / V2 / V3 D+5 verify 실행 + 박제

**Files:**
- Modify (mctrader-hub): `docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md`

- [ ] **Step 1: V1 — 50-sym 누적 부피 (D+5)**

mctrader-data 실측 컨테이너에서 framework 실행:

```bash
docker exec mctrader-collector python -m mctrader_data.cli health-check \
  --target collector --window 5d --start-date 2026-05-09 \
  --output markdown > /tmp/v1-d5.md
```

기대: 50-sym × 5d (2026-05-09 → 2026-05-13) volume 측정. expected ~4.35 GiB ±20% = [3.48, 5.22] GiB.

- [ ] **Step 2: V2 — upbit L1 partition 0 verdict (MCT-160 R7)**

```bash
docker exec mctrader-collector python -m mctrader_data.cli health-check \
  --target collector --window 5d --start-date 2026-05-09 \
  --symbols <upbit-50-sym-list> --output json > /tmp/v2-upbit-d5.json
```

후처리: gap layer 의 missing_partition 중 upbit exchange path 만 추출. OQ-2 정의 = "expected_daily_file_count > 0 ∧ actual_daily_file_count == 0 인 sym 이 1 개 이상" → verdict.

잔존 = yes → MCT-164 (upbit L1 root cause) 별 Story 발의 trigger.
잔존 = no → MCT-160 R7 verify only PASS, MCT-164 보류.

- [ ] **Step 3: V3 — 50-sym × 5d per-sym 분포**

```bash
docker exec mctrader-collector python -m mctrader_data.cli health-check \
  --target collector --window 5d --start-date 2026-05-09 \
  --output csv > /tmp/v3-per-sym.csv
```

per-sym gap / file_count / volume 의 분포 (median / p10 / p90) markdown 박제.

- [ ] **Step 4: `verify-d5-2026-05-14.md` 박제**

`docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md`:

```markdown
---
verify_date: 2026-05-14
window: 5d (2026-05-09 → 2026-05-13)
story: MCT-165
artifact_v1: V1 부피 추산 정합
artifact_v2: V2 upbit L1 partition 0 verdict
artifact_v3: V3 per-sym 분포
---

# D+5 Verify Result (2026-05-14)

## V1 — 50-sym 누적 부피

- 측정: <RESULT> GiB
- 추산: 4.35 GiB ±20% = [3.48, 5.22] GiB
- Verdict: PASS / FAIL
- ...

## V2 — upbit L1 partition 0 (MCT-160 R7)

- 잔존: yes / no
- 잔존 sym (있으면): <LIST>
- MCT-164 발의 trigger: yes (잔존 시) / no (PASS 시)

## V3 — 50-sym × 5d per-sym 분포

- (median / p10 / p90 표)
- outlier sym (있으면): <LIST>

## Follow-up

- (V2 잔존 시) MCT-164 Issue 발의 trigger
- (V1 FAIL 시) collector 운영 review
- (V3 outlier) sym 별 cause 조사
```

- [ ] **Step 5: hub commit (별 branch — mctrader-hub working dir)**

```bash
cd c:/workspace/mclayer/mctrader-hub
git checkout -b mct-165-phase-2-hub
git add docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md
git commit -m "docs(MCT-165): D+5 verify — V1/V2/V3 박제"
```

---

## Task 9: D+7 checkpoint (2026-05-16, wall-clock)

- [ ] **Step 1**: 2026-05-16 가 되면 (D+7) 동일 framework 실행 with `--window 7d`. 기대 ~6 GiB ±20%.
- [ ] **Step 2**: `verify-d7-2026-05-16.md` 박제 (V1 부피 7d 정합 + V2/V3 회귀 확인).
- [ ] **Step 3**: commit + Phase 2 PR 에 add (이미 open 상태) 또는 별 follow-up PR.

D+30 (2026-06-08) checkpoint = framework merge 후 별 single commit + `verify-d30-2026-06-08.md` (PR scope 외).

---

## Task 10: Phase 2 PR open + Story §8.5 Impl Manifest + CLAUDE.md

- [ ] **Step 1**: mctrader-data Phase 2 PR open (code).
- [ ] **Step 2**: mctrader-hub Phase 2 PR open (verify-d5 / verify-d7 박제 + CLAUDE.md §데이터 헬스 프레임워크 + Story §8.5 Impl Manifest + §11 Invariant 박제 + §12 Phase 2 보고).
- [ ] **Step 3**: CodeReviewPLAgent + SecurityTestPLAgent dispatch (mctrader-data) + DesignReviewPLAgent (hub).
- [ ] **Step 4**: CI green → admin merge (memory `feedback_admin_merge_autonomy`).
- [ ] **Step 5**: PMOAgent dispatch — RETRO-MCT-165 작성 (memory `feedback_pmo_retro_mandatory`).

---

## Self-Review

- [x] Spec §1-§10 coverage: 각 결정 D1-D9 + OQ-1/2/3 → Task 매핑 명시
- [x] Placeholder scan: 가정 reconcile 부분 (Task 5 Step 3, Task 7 Step 2 wiring) 에 명시적 reconcile 의무 surface — silent placeholder 아님
- [x] Type consistency: ThresholdResult dataclass 의 verdict Literal, VolumeResult per_sym dict 등 cross-task 일관
- [x] Cross-repo handling: hub / data working dir 명시 + branch race 회피 (memory `feedback_parallel_session_branch_race`)

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-14-mct-165-data-accumulation-health.md`.

Execution options:
1. **Subagent-Driven (recommended)** — fresh subagent per task, 두 단계 review
2. **Inline Execution** — executing-plans skill 으로 batch + checkpoint

사용자 명시 = "기획해서 수행해야해" → memory `feedback_subagent_execution` 정합 = **Subagent-Driven default**.
