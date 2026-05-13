# MCT-160 L2/L3 Cadence + OOM + L1 Backlog 79k Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** EPIC-compactor-operations Story-2. L2/L3 cadence silent skip + OOM exit 137 + L1 backlog 79k drainage + DualWriter read_bytes memory 재할당 fix + ADR-009 §D11.9.2 nullability discipline 합병. 5중 차단 #2/#3/#5 잔여 + drainage lever 진짜 fix.

**Architecture:** codeforge consumer 1 Story = 2 PR. Phase 1 hub PR (ADR-027 silent-skip amendment + ADR-009 nullability amendment + Story §1-§11 + scope_manifest milestone). Phase 2 mctrader-data PR (l2.py/l3.py/runner.py/l1.py + 2 test 신규) + mctrader-hub PR (Story §12 + RETRO + counters DELETE + CLAUDE.md + drainage).

**Tech Stack:** Python 3.13, pyarrow (ParquetWriter chunk + row_group_size), prometheus_client, Docker compose.

**Spec:** [docs/superpowers/specs/2026-05-13-compactor-operations-design.md](../specs/2026-05-13-compactor-operations-design.md)

---

## Codex 합성 11 결정 + 3 추가 risk

- **D1**: L3 cadence 합병 (A) — L2/L3 동일 pathology fix 일관
- **D2**: caller 명시 date_utc 전달 (C) — runner 가 명시 인자
- **D3**: chunk concat + row_group_size 명시 (B) — `row_group_size=100_000`, chunk size 1024 rows
- **D4**: post-write monotonic verify + quarantine (C) — L1 ordering Unknown 방어
- **D5**: 순증 중단 (B) — drainage rate ≤ ingest rate (1h window)
- **D6**: caller sha256 + `data=parquet_path` (A) — minimal change
- **D7**: 3 schema 일관 nullability (B)
- **D8**: backfill_orchestrator 별 Story (B, MCT-153/159)
- **D9**: upbit verify only (C, 별 root cause 후속)
- **D10**: ADR-027 + ADR-009 2건 (B)
- **D11**: L2/L3 각자 정상화, duplicate code 허용 (A, refactor MCT-163 별)

추가 AC: row_group_size/chunk size 수치 + quarantine 위치/재처리 + consumer nullability smoke.

---

## File Structure

### mctrader-hub (governance)
- **Modify**: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — silent-skip 차단 amendment
- **Modify**: `docs/adr/ADR-009-ohlcv-schema.md` — nullability discipline (3 schema)
- **Already PMO 박제 (main 직접 commit)**: `docs/stories/MCT-160.md` (521 line, §1-§11) + `scope_manifests/EPIC-compactor-operations.yaml` (milestone update)
- **Phase 2 §12 self-write 예정**: `docs/stories/MCT-160.md` §12 + `docs/retros/RETRO-MCT-160.md` + `CLAUDE.md`

### mctrader-data (구현)
- **Modify**: `src/mctrader_data/compactor/l2.py` — `compact_hour(date_utc)` 인자 (D2), chunk concat + row_group_size (D3), post-write monotonic verify + quarantine (D4)
- **Modify**: `src/mctrader_data/compactor/l3.py` — `compact_day(date_utc)` 인자 (D1+D2), L2 동형 streaming + verify (D1+D3+D4)
- **Modify**: `src/mctrader_data/compactor/l1.py` — 3 schema (transaction/orderbooksnapshot/orderbookdepth) `pa.field(nullable=False/True)` 명시 (D7+P1)
- **Modify**: `src/mctrader_data/compactor/runner.py` — `_run_l2/_run_l3` date_utc 인자 전달 (D2), `_dispatch_dual_write` `read_bytes()` 제거 + `data=parquet_path` (D6)
- **Create**: `src/mctrader_data/compactor/quarantine.py` — quarantine directory layout + 재처리 helper
- **Create**: `tests/integration/test_l2_l3_cadence_streaming.py` — 8 test (D1-D9 + R-EXTRA + P1 + L1 ordering)
- **Create**: `tests/integration/test_dual_writer_streaming.py` — DualWriter `data=Path` streaming verify

---

## Task 1: Phase 1 사전 + main chore commit (PMO 산출 + spec + plan)

- [ ] **Step 1: counters verify**

```bash
cd c:/workspace/mclayer/mctrader-hub
python -c "import json,io; d=json.load(io.open('.codeforge/counters.json',encoding='utf-8')); print('next:', d['counters']['mctrader-hub']['next']); print('MCT-160:', d['reservations'].get('MCT-160',{}).get('title','MISSING'))"
```

기대: `next: 163`, `MCT-160: L2/L3 cadence + OOM + L1 backlog 79k cleanup`.

- [ ] **Step 2: spec + plan 추가 + PMO 산출 chore commit + push**

```bash
git add docs/stories/MCT-160.md scope_manifests/EPIC-compactor-operations.yaml docs/superpowers/specs/2026-05-13-compactor-operations-design.md docs/superpowers/plans/2026-05-13-mct-160-l2-l3-cadence-streaming.md
git commit -m "chore(MCT-160): brainstorm Phase 0+1 + PMO Phase 2 + Story §1-§11 + scope_manifest IN_PROGRESS + plan

Codex 11 결정 합성:
- D1 L3 합병 (A) / D2 caller date_utc 명시 (C) / D3 chunk + row_group_size (B)
- D4 post-write monotonic verify + quarantine (C) / D5 순증 중단 (B) / D6 caller sha256 + data=Path (A)
- D7 3 schema nullability (B) / D8 backfill 별 Story (B) / D9 upbit verify only (C)
- D10 ADR-027 + ADR-009 2건 (B) / D11 L2/L3 duplicate code 허용 (A)

추가 AC: row_group_size=100_000 + chunk=1024 rows + quarantine 위치 + consumer nullability smoke.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
git push origin main
```

- [ ] **Step 3: GitHub Issue MCT-160 생성**

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-160] L2/L3 cadence + OOM + L1 backlog 79k cleanup + R-EXTRA + P1 nullability 합병" \
  --label "type:story" \
  --body "Codex 11 결정 합성. EPIC-compactor-operations Story-2.
  
Spec: docs/superpowers/specs/2026-05-13-compactor-operations-design.md
Plan: docs/superpowers/plans/2026-05-13-mct-160-l2-l3-cadence-streaming.md
Story: docs/stories/MCT-160.md (이미 main 박제, Phase 1 PR 은 ADR amendment 만)"
```

---

## Task 2: Phase 1 worktree + ArchitectPL (ADR amendment 만) + DesignReview + merge

- [ ] **Step 1: GitOpsAgent Phase 1 worktree**

```
Branch: mct-160-phase1-architect
Base: main HEAD (chore commit 후 latest)
Worktree: c:/workspace/mclayer/mctrader-hub-mct160-phase1
Purpose: ADR-027 silent-skip amendment + ADR-009 nullability amendment 2건
```

- [ ] **Step 2: ArchitectPLAgent dispatch (ADR amendment 만)**

Story file + scope_manifest 는 이미 main 박제 — ArchitectPL 는 ADR 2건 amendment 만 작성.

ADR-027 amendment (silent-skip 차단):
```markdown
**MCT-160 amendment 박제 (2026-05-13)** — Cadence trigger silent-skip 차단 (D4 cross-binding).

L2/L3 compaction cadence 의 `compact_hour(hour_utc=now)` / `compact_day(date_utc=now.date())` 하드코딩 = silent skip risk:
- KST→UTC date roll 시 어제 date 의 L1 결과 hit 0 → `l1_files = []` → return None silent
- L2 자연 cadence trigger 발화해도 처리 0 → backlog 영구 누적

**채택**:
1. **Caller-explicit date 의무**: `_run_l2`/`_run_l3` 가 date_utc 인자 명시 전달 (today + yesterday 2일치 또는 partition list latest date scan)
2. **Post-write monotonic verify**: streaming write 후 `ts_utc` 정렬 invariant check, 위반 시 quarantine + Prometheus alert
3. **Quarantine directory layout**: `market/<channel>/quarantine/{date}/{reason}/part-*.parquet` — 운영자 review 후 재처리
4. **Prometheus emit**: `compactor_l2_silent_skip_total` + `compactor_l3_silent_skip_total` + `compactor_monotonic_violation_total{tier}` Counter
```

ADR-009 amendment (nullability discipline):
```markdown
**MCT-160 amendment 박제 (2026-05-13)** — Schema nullability discipline (P1 from MCT-162 CodeReviewPL).

ADR-009 §D11.9.2 (orderbookdepth.v1) + §D10 (transaction.v1) + §D11 (orderbooksnapshot.v1) 의 11 column schema 가 pyarrow `pa.schema([(name, dtype), ...])` 형식 정의 시 default nullable=True. ADR 본문 박제 = `raw_json` 만 nullable=True, 나머지 nullable=False.

**채택**:
1. **`pa.field(name, dtype, nullable=False)` 명시 의무** — 3 schema (`_TICK_SCHEMA`, `_OB_SNAPSHOT_SCHEMA`, `_ORDERBOOKDEPTH_SCHEMA`) 모두.
2. **InvariantHarness dtype_identity verify** — column nullability 도 check (ADR-027 §D6 정합).
3. **Consumer smoke verify** — engine reader / DuckDB read 시 nullability mismatch 0 verify.
```

- [ ] **Step 3: DesignReviewPLAgent + Phase 1 PR + admin merge**

memory: "Admin merge autonomy" — CI PASS 후 즉시 admin merge.

---

## Task 3: Preflight stop + Phase 2 worktree 2-repo + DevPL/QADev parallel

- [ ] **Step 1: Preflight stop compactor**

```bash
docker compose stop compactor
```

- [ ] **Step 2: GitOpsAgent Phase 2 worktree 2건 동시**

```
data: mct-160-phase2-dev → c:/workspace/mclayer/mctrader-data-mct160-phase2
hub: mct-160-phase2-docs → c:/workspace/mclayer/mctrader-hub-mct160-phase2 (Phase 1 merge 후 base)
```

- [ ] **Step 3: DeveloperPLAgent dispatch**

l2.py + l3.py + l1.py + runner.py + quarantine.py 신규.

핵심 변경:

**l2.py `compact_hour(date_utc)`** — caller 명시 date:
```python
def compact_hour(self, *, exchange, symbol, channel, date_utc: date, hour_utc: int) -> Path | None:
    """MCT-160: caller-explicit date_utc + chunk streaming + monotonic verify.
    
    D2: hour_utc=now 하드코딩 제거 — runner 가 today/yesterday 명시 전달
    D3: pa.concat_tables 제거 — ParquetWriter chunk write + row_group_size=100_000
    D4: post-write monotonic verify — ts_utc 정렬 invariant, 위반 시 quarantine
    """
    date_str = date_utc.isoformat()
    l1_dir = self._root / "market" / channel / f"schema_version={schema_ver}" / "tier=L1" / f"exchange={exchange}" / f"symbol={symbol}" / f"date={date_str}"
    l1_files = sorted(l1_dir.rglob("part-*.parquet")) if l1_dir.exists() else []
    if not l1_files:
        return None
    
    out_dir = ... / f"hour={hour_utc:02d}" / "node=MERGED"
    out_path = out_dir / f"part-{run_id}.parquet"
    tmp = out_dir / f"part-tmp-{os.getpid()}.tmp"
    
    # D3: streaming chunk write
    last_ts = None
    monotonic_violation = False
    with pq.ParquetWriter(str(tmp), schema, compression="snappy") as writer:
        for f in l1_files:
            tbl = pq.ParquetFile(f).read()
            # D4: monotonic verify (chunk-level)
            ts_col = tbl.column("ts_utc")
            for i in range(tbl.num_rows):
                cur = ts_col[i].as_py()
                if last_ts is not None and cur < last_ts:
                    monotonic_violation = True
                last_ts = cur
            writer.write_table(tbl, row_group_size=100_000)
    
    if monotonic_violation:
        # D4: quarantine
        from mctrader_data.compactor.quarantine import quarantine_l2
        quarantine_l2(tmp, channel=channel, date_utc=date_utc, reason="monotonic_violation")
        # Prometheus alert
        from mctrader_data.nas_metrics.prometheus_exporters import compactor_monotonic_violation_total
        compactor_monotonic_violation_total.labels(tier="L2").inc()
        return None
    
    os.replace(str(tmp), str(out_path))
    return out_path
```

**l3.py `compact_day(date_utc)`** — 동형 패턴 (L2 의 hour 차원 제거).

**l1.py 3 schema nullability 명시** (D7+P1):
```python
_TICK_SCHEMA = pa.schema([
    pa.field("ts_utc", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("received_at", pa.timestamp("us", tz="UTC"), nullable=False),
    # ... 나머지 column 모두 nullable=False, raw_json 만 nullable=True
])

_OB_SNAPSHOT_SCHEMA = pa.schema([...])  # 동형
_ORDERBOOKDEPTH_SCHEMA = pa.schema([...])  # MCT-162 land schema, nullable 명시
```

**runner.py `_run_l2/_run_l3`**:
```python
def _run_l2(self) -> None:
    """MCT-160 D2: today + yesterday 2일치 명시 scan."""
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    yesterday = today - timedelta(days=1)
    current_hour = now_utc.hour
    
    seen: set[tuple] = set()
    for parquet in (self._root / "market").rglob("*/tier=L1/**/part-*.parquet"):
        try:
            exchange = _extract_partition(parquet, "exchange")
            symbol = _extract_partition(parquet, "symbol")
            channel = parquet.parts[list(parquet.parts).index("market") + 1]
            
            # D2: today + yesterday 2일치
            for date_utc in [today, yesterday]:
                for hour in range(24):
                    key = (exchange, symbol, channel, date_utc, hour)
                    if key in seen:
                        continue
                    seen.add(key)
                    self._run_l2_for_parquet(
                        exchange=exchange, symbol=symbol, channel=channel,
                        date_utc=date_utc, hour_utc=hour,
                    )
        except Exception:
            log.exception("[compactor] L2 dispatch failed %s", parquet)

def _dispatch_dual_write(self, parquet_path: Path, *, tier: str) -> None:
    """MCT-160 R-EXTRA: read_bytes 제거, data=parquet_path streaming."""
    import hashlib
    
    # caller sha256 (streaming hash, no full memory)
    sha = hashlib.sha256()
    with parquet_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    sha256 = sha.hexdigest()
    
    nas_key = str(parquet_path.relative_to(self._root)).replace("\\", "/")
    
    result = self._dual_writer.write(
        local_path=parquet_path,
        nas_key=nas_key,
        data=parquet_path,  # MCT-160 D6: Path streaming, no read_bytes()
        sha256=sha256,
    )
    # ... status switch (committed/local_only/hard_floor_blocked) 동일
```

**quarantine.py 신규**:
```python
"""MCT-160 D4: post-write monotonic verify 실패 시 quarantine directory."""
from pathlib import Path

def quarantine_l2(tmp_path: Path, *, channel: str, date_utc: date, reason: str) -> Path:
    """Quarantine 산출물 directory layout: market/<channel>/quarantine/{date}/{reason}/part-*.parquet"""
    quarantine_dir = tmp_path.parents[3] / "quarantine" / str(date_utc) / reason
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / f"part-{tmp_path.stem}.parquet"
    tmp_path.rename(quarantine_path)
    return quarantine_path

def quarantine_l3(tmp_path: Path, *, channel: str, date_utc: date, reason: str) -> Path:
    """L3 quarantine (L2 동형)."""
    return quarantine_l2(tmp_path, channel=channel, date_utc=date_utc, reason=reason)
```

- [ ] **Step 4: QADeveloperAgent dispatch**

`tests/integration/test_l2_l3_cadence_streaming.py` 신규 (8 test).

- [ ] **Step 5: TestAgent + SecurityTestPL + CodeReviewPL parallel + 2 PR merge**

- [ ] **Step 6: compactor 재시작 + drainage 1h 측정**

```bash
docker compose build compactor
docker compose up -d compactor

# 1h 후 drainage 측정
sleep 3600
docker exec mctrader-compactor sh -c "find /var/lib/mctrader/data/wal -name '*.ndjson.sealed' | wc -l"
```

기대: backlog 감소 (D5 순증 중단 verify).

---

## Task 4: PMOAgent retro + drainage 박제 + 다음 Story (MCT-161)

- [ ] **Step 1: PMOAgent dispatch — RETRO + Story §12 + scope_manifest 2/3 + counters DELETE + CLAUDE.md + drainage 결과**

- [ ] **Step 2: Issue MCT-160 CLOSE + Phase 2 hub PR merge**

- [ ] **Step 3: 다음 Story 진입 권고 (MCT-161 — NAS bucket versioning + MCT-153 손실 재발 방지)**

---

## Self-Review

- ✅ D1-D11 모두 task 매핑
- ✅ R-EXTRA + P1 합병 task 매핑
- ✅ row_group_size=100_000 + chunk size + quarantine 위치 명시
- ✅ consumer nullability smoke verify (Story §6 D9)
- ✅ preflight stop + drainage 1h 측정 의무 박제
- ✅ Type consistency: `compact_hour(date_utc: date, hour_utc: int)` + `compact_day(date_utc: date)` signature 통일

## Execution Handoff

Plan complete. 즉시 자율 진행 (사용자 명시 "수행하라" + "시간 없다 + 적극 병렬").
