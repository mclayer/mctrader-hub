# MCT-173 upbit L1 backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** MCT-166 fix LAND (2026-05-14) 직후 frozen orderbooksnapshot WAL (t<LAND) → orderbooksnapshot L1 historical compaction. compactor.runner `--backfill` mode extend + `.compacted` rename idempotency + frontmatter manifest + MCT-165 V2=0 + 별 verify partial loss defense in depth.

**Architecture:** D7=C 1 Story + Phase 2 단계 분할 (entry scan → runner extend → backfill 실행 → verify). Phase 1 hub PR (docs only). Phase 2 mctrader-data PR (4 단계 multi-commit). Phase 2 hub PR (결과 박제 + channel matrix update + RETRO + Issue close).

**Tech Stack:** Python 3.13, pytest, pyarrow, mctrader_data CLI, Docker compose.

**Spec reference:** [docs/superpowers/specs/2026-05-14-MCT-173-upbit-l1-backfill-design.md](../specs/2026-05-14-MCT-173-upbit-l1-backfill-design.md)

**Trigger:** MCT-166 D3=B + MCT-164 D4=C 부분가능 verdict. Issue #298.

---

## File Structure

### mctrader-hub (governance)

- **Create**: `docs/stories/MCT-173.md` (§1-§12)
- **Create**: `docs/superpowers/specs/2026-05-14-MCT-173-upbit-l1-backfill-design.md` (이미 박제)
- **Create**: `docs/superpowers/plans/2026-05-14-mct-173-upbit-l1-backfill.md` (본 file)
- **Modify**: `.codeforge/counters.json` (MCT-173 title 확장)
- **Modify**: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` (backfill 결과, Phase 2 hub)
- **Modify**: `CLAUDE.md` (§backfill mode + §verify gate)
- **Create**: `docs/retros/RETRO-MCT-173.md` (PMO retro)

### mctrader-data (구현)

- **Modify**: `src/mctrader_data/compactor/runner.py` (`--backfill` mode 추가, D1=B)
- **Create**: `src/mctrader_data/compactor/backfill.py` (frozen WAL iterator + manifest writer, D5=B)
- **Create**: `scripts/backfill_entry_scan.py` (Phase 2.1 audit, D2=C/D9=C)
- **Create**: `scripts/verify_backfill_partial_loss.py` (별 verify, D8=C)
- **Create**: `tests/unit/compactor/test_backfill.py`
- **Create**: `tests/integration/test_backfill_upbit_l1.py`
- **Create**: `docs/audit/MCT-173-entry-scan.md` (Phase 2.1 결과)
- **Modify**: `CLAUDE.md` (§backfill mode)

---

## Task 1: Phase 1 hub PR

- [ ] **Step 1: branch + counters** (이미 완료, mct-173-phase-1 branch + MCT-173 title 확장)

- [ ] **Step 2: Story file MCT-173.md §1-§7 작성** — spec §1-§9 + Story 표준 frontmatter (status: IN_PROGRESS, depends_on: [MCT-164, MCT-165, MCT-166], related_adrs: [ADR-017 §D2 + Amendment 2 / ADR-009 §D12], created_at: 2026-05-14)

- [ ] **Step 3: commit + push + PR + label**

```bash
git add .codeforge/counters.json docs/stories/MCT-173.md docs/superpowers/specs/... docs/superpowers/plans/...
git commit -m "docs(MCT-173): Phase 1 — spec + plan + Story §1-§7 + counters title 확장"
git push -u origin mct-173-phase-1
gh pr create ...
gh pr edit <PR#> --add-label "type:story" --add-label "phase:설계"
```

- [ ] **Step 4: DesignReviewPLAgent dispatch → PASS → CI green → admin merge**

---

## Task 2: Phase 2.1 entry scan (mctrader-data, D2=C/D9=C)

**Files:**
- Create: `scripts/backfill_entry_scan.py`
- Create: `docs/audit/MCT-173-entry-scan.md`

- [ ] **Step 1: frozen WAL path 실측**

```bash
# MCT-164 wal_freeze.py 가 chmod 444 vs 별 디렉터리 이동인지 확인
find /var/lib/mctrader/data/wal/upbit -type f -name '*.ndjson*' 2>/dev/null | head -10
find /var/lib/mctrader/data/wal-frozen 2>/dev/null  # 별 디렉터리 후보 path
docker exec mctrader-collector ls -la /var/lib/mctrader/data/.wal-freeze/ 2>/dev/null  # freeze flag
```

- [ ] **Step 2: pre-existing L1 inventory**

```bash
find /var/lib/mctrader/data/market/orderbooksnapshot -path '*tier=L1*exchange=upbit*' -name '*.parquet' 2>/dev/null | head -20
# count + total size
```

- [ ] **Step 3: partial WAL date boundary 식별**

- frozen WAL segment 의 timestamp range (filename + mtime)
- frozen 시작 시각 ~ MCT-166 fix LAND (2026-05-14T04:04:29Z mctrader-data PR #56 merge) 까지 date range

- [ ] **Step 4: `docs/audit/MCT-173-entry-scan.md` 박제** — D2/D9 결정 박제 + Phase 2.2 runner extend 설계 입력

---

## Task 3: Phase 2.2 compactor.runner `--backfill` mode extend (D1=B/D4=A/D5=B)

**Files:**
- Modify: `src/mctrader_data/compactor/runner.py`
- Create: `src/mctrader_data/compactor/backfill.py`
- Create: `tests/unit/compactor/test_backfill.py`

- [ ] **Step 1: failing test 작성** — `test_backfill.py`:

```python
def test_backfill_iterator_yields_frozen_segments_only(tmp_path):
    # active segment + sealed + .compacted 3종 fixture
    # iterator 는 sealed (not .compacted) 만 yield
    ...

def test_backfill_idempotency_compacted_rename(tmp_path):
    # backfill 2회 실행 → 첫 회 sealed → .compacted rename
    # 두번째 회 .compacted skip (effective once)
    ...

def test_backfill_manifest_frontmatter_partial_boundary(tmp_path):
    # manifest YAML frontmatter 에 frozen 시작 ~ MCT-166 LAND date range
    ...

def test_backfill_schema_matches_mct166_path_b(tmp_path):
    # backfill L1 schema == _ob_snapshot_dicts_to_arrow() output (INV-3)
    ...
```

- [ ] **Step 2: fail 확인 + impl**

`src/mctrader_data/compactor/backfill.py`:
```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BackfillManifest:
    frozen_start: str  # ISO 8601
    fix_land: str
    segment_count: int
    pre_existing_l1_count: int
    partial_boundary_segments: list[str]


def iter_frozen_segments(wal_root: Path, exchange: str, channel: str):
    """sealed only, not .compacted. point-in-time snapshot (D3=A)."""
    for sealed in sorted(wal_root.rglob(f"{exchange}/{channel}/**/*.ndjson.sealed")):
        if sealed.with_suffix(".compacted").exists():
            continue  # idempotency (D4=A)
        yield sealed


def write_manifest(manifest: BackfillManifest, target: Path) -> None:
    """frontmatter manifest (D5=B)."""
    ...
```

`runner.py` `--backfill` 모드 추가 — `iter_frozen_segments` + 기존 `_ob_snapshot_dicts_to_arrow()` 재사용 + manifest emit.

- [ ] **Step 3: pass + commit**

---

## Task 4: Phase 2.3 backfill 실행

- [ ] **Step 1: dry-run** (test 환경, frozen WAL subset)

- [ ] **Step 2: production 실행**

```bash
docker exec mctrader-compactor python -m mctrader_data.compactor.runner \
  --backfill --exchange upbit --tier L1 --channel orderbooksnapshot
```

기대: L1 parquet 생성 (date range = entry scan 박제). sealed → .compacted rename.

- [ ] **Step 3: idempotency 검증** — 동일 명령 2번 실행, 두번째 = no-op.

- [ ] **Step 4: 결과 박제** — `docs/audit/MCT-173-entry-scan.md` append (Phase 2.3 결과 + manifest content).

---

## Task 5: Phase 2.4 verify (D8=C)

**Files:**
- Create: `scripts/verify_backfill_partial_loss.py`

- [ ] **Step 1: MCT-165 framework V2=0 verify (AC-5)**

```bash
docker exec mctrader-collector python -m mctrader_data.cli health-check \
  --target collector --window 5d --start-date 2026-05-09 \
  --symbols <upbit-50-sym-list> --output json | jq '.layers.gap'
```

기대: upbit L1 V2 (forward-only loss) = 0 (모든 date range coverage).

- [ ] **Step 2: 별 verify 스크립트 (AC-6)**

`scripts/verify_backfill_partial_loss.py`:
- frozen WAL row count (ndjson line count) per (date, symbol)
- L1 parquet row count per (date, symbol)
- ratio = L1 / frozen
- threshold (예: 90%) 미달 = partial loss indicator + log
- threshold 초과 = §10 FIX trigger

- [ ] **Step 3: 통합 test `tests/integration/test_backfill_upbit_l1.py`**

- [ ] **Step 4: commit + mctrader-data Phase 2 PR open + CI + admin merge**

---

## Task 6: Phase 2 hub PR — 박제 + channel matrix + RETRO + Issue close

**Files (mctrader-hub):**
- Modify: `docs/stories/MCT-173.md` (§8-§12)
- Modify: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` (backfill 결과 박제)
- Modify: `CLAUDE.md`
- Create: `docs/retros/RETRO-MCT-173.md`

- [ ] **Step 1: Story §8-§12 박제** (Test Contract / Operational Risk / FIX Ledger + entry scan 결과 + manifest content + partial loss verdict / Invariant cross-ref / PMO retro)

- [ ] **Step 2: channel matrix update** — MCT-166 fix Result 행 아래 "MCT-173 Backfill Result" 추가 (frozen date range + L1 row count + partial loss ratio)

- [ ] **Step 3: CLAUDE.md** — §backfill mode 사용법 + §verify gate

- [ ] **Step 4: RETRO-MCT-173.md** — PMOAgent dispatch (memory feedback_pmo_retro_mandatory)

- [ ] **Step 5: hub Phase 2 PR open + DesignReviewPL + CI + admin merge**

- [ ] **Step 6: Issue #298 close** (gate:retro-complete + summary comment)

- [ ] **Step 7: Story frontmatter status: COMPLETED + completed_at: 2026-05-14**

---

## Self-Review

- [x] Spec §1-§10 coverage: 각 D → Task 매핑
- [x] D7=C Phase 2 단계 분할 (Task 2/3/4/5)
- [x] D8=C 양쪽 verify (Task 5 Step 1/2)
- [x] historical materialization 정당성 (forward-only invariant 위반 0): D3=A PIT + D4=A `.compacted` idempotency

---

## Execution Handoff

Plan complete. Execution = Subagent-Driven.
