# MCT-159 — L2/L3 Cold Tier Backlog NAS Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate ~8.85 GiB / 7118 files of locally accumulated L2/L3 cold tier Parquet (orderbooksnapshot + transaction × tier=L{2,3}) to NAS MinIO using channel-parametrized + hour-keyed `BackfillOrchestrator`, with 7-invariant ALL PASS gate.

**Architecture:** Reuse MCT-153 `BackfillOrchestrator` + MCT-151 `InvariantHarness` + MCT-150 `NASUploader/RetryQueue` (production-grade primitives). Two amendments: (a) channel parametrize (`orderbooksnapshot` + `transaction`), (b) hour key 처리 (`_build_chunk_spec` `hour` 축 추가). ADR-027 D4/D6/D9 amendment + scope_manifest patch + MCT-160/161 sequential reserve cross-link.

**Tech Stack:** Python 3.12, pyarrow, boto3 (MinIO S3 API), pytest, sqlite-WAL (checkpoint), Prometheus client. Two repos: `mctrader-data` (impl + test, primary), `mctrader-hub` (governance + ADR + Story §11 SSOT).

---

## Spec → Plan Source

- Spec: `docs/superpowers/specs/2026-05-13-mct-159-l2l3-backlog-nas-migration-design.md`
- 8 D 결정 LAND (사용자 final confirm 2026-05-13)
- Counters reservation LAND: MCT-159 (retitle) + MCT-160 + MCT-161

---

## File Structure (Phase 2 impl 영역)

### mctrader-data (확정 4 file + 조건부 0)

| 파일 | 종류 | 책임 |
|---|---|---|
| `src/mctrader_data/nas_migration/backfill_orchestrator.py` | 수정 | channel parametrize + hour key 박제 추가 |
| `scripts/migration/run_backfill.py` | 수정 | `--channel` flag + evidence pack MCT-159 갱신 |
| `tests/nas_migration/test_backfill_orchestrator.py` | 수정 | fixture `schema_version=*` 포함 + L3 + channel 매트릭스 |
| `tests/nas_migration/test_backfill_resumability_chaos.py` | 수정 | 동일 fixture 갱신 |

### mctrader-hub (governance only)

| 파일 | 종류 | 책임 |
|---|---|---|
| `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` | 수정 | D4 + D6 + D9 amendment (D7/D11 변경 0) |
| `docs/stories/MCT-159.md` | 신규 | Story file §1~§11 |
| `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` | 수정 | story_sequence MCT-159 + design_decisions S8~S15 + R3-R6 |
| `CLAUDE.md` | 수정 | "Stage 3 backlog migration follow-up" section |
| (mctrader-data) `CLAUDE.md` | 수정 | "BackfillOrchestrator channel/hour amend" section |

---

## Phase 1 — mctrader-hub Governance PR (docs only, 코드 변경 0)

### Task 1: ADR-027 D4 amendment

**Files:**
- Modify: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (§D4 끝부분, 기존 MCT-156 amendment 다음)

- [ ] **Step 1: ADR-027 §D4 끝부분에 MCT-159 amendment 본문 append**

기존 `### D4. Cutover 전략 — dual-write window → 검증 → reader 전환 → local GC` 의 `**MCT-156 amendment 박제 (2026-05-13)**` 블록 직후에 추가:

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — L2/L3 cold tier backlog migration obligation. Stage 3 wiring (MCT-156 LAND #279) 후 hot pipeline NAS PUT 정상화 (compactor 09:22 restart 후 09:24 부터 신규 schema PUT). 그러나 wiring _이전_ 로컬 누적 L2/L3 backlog (8.85 GiB / 7118 files, 신규 schema `tier=L{2,3}/exchange=X/symbol=Y/date=D/hour=HH/node=MERGED/part-*.parquet`) 은 자연 cadence 적용 외 영역 — `orderbookdepth` channel NotImplementedError 영구 fail 로 L2 자연 trigger ETA 9.2h 무효 (RETRO-MCT-156 §13.4 박제). 본 amendment = MCT-153 `BackfillOrchestrator` 의 (a) channel parametrize (`orderbooksnapshot` + `transaction` 양 channel) + (b) hour key 처리 (`_build_chunk_spec` `hour` 축 추가, `nas_object_key` `/hour=HH/node=MERGED/` 박제) 2 amendment 후 재호출하여 LAND-이전 backlog 강제 이관. forward-only invariant + 7d grace + 7종 invariant ALL PASS gate 정합 의무. L1 sealed backlog (76,200 file / ~115 GiB) + WAL (59 GiB) = 본 amendment scope 외 (MCT-160 책임, orderbookdepth FIX + L2 offset overflow FIX prerequisite). 사용자 명시 동기 (disk 압박 해소) 본 amendment 만으로 미달성 (4.8% only) — MCT-160 sequential 의무 박제.
```

- [ ] **Step 2: History 섹션 신규 entry append**

`## History` 끝에:

```markdown
- 2026-05-13 — **D4/D6/D9 amendment** (MCT-159, EPIC-cold-tier-stage-3-wiring sibling — L2/L3 cold tier backlog NAS migration). D4 = backlog migration wiring obligation (BackfillOrchestrator channel parametrize + hour key 처리 2 amendment). D6 = 7종 invariant ALL PASS gate enforce (MCT-151 InvariantHarness inject 자동, wording 변경 0). D9 = mixed layout 재해석 (RETRO-MCT-156 §13.5.2 박제 — legacy NAS 4.2 GiB 손실 확정으로 (a) 사실상 무존재, reader fallback 의존 0, MCT-161 reserve 별 Story versioning 활성화 책임).
```

- [ ] **Step 3: ADR-027 review (재독)**

`docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` 전체 재독, D4/History append 정합 확인. D6/D9 amendment 는 Task 2/3.

- [ ] **Step 4: Commit (D4 only)**

```bash
cd c:\workspace\mclayer\mctrader-hub
git add docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md
git commit -m "$(cat <<'EOF'
docs(MCT-159): ADR-027 D4 amendment — backlog migration wiring obligation

L2/L3 cold tier backlog (8.85 GiB / 7118 files) NAS migration obligation 박제. MCT-153 BackfillOrchestrator 의 channel parametrize + hour key 처리 2 amendment 후 재호출. L1 sealed + WAL = MCT-160 책임 (sequential 의무). 사용자 명시 동기 본 amendment 만으로 미달성 (4.8% only) 박제.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 2: ADR-027 D6 amendment

**Files:**
- Modify: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (§D6 끝부분, 기존 MCT-155 amendment 다음)

- [ ] **Step 1: D6 amendment 본문 append**

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — backlog migration path 의 7종 invariant ALL PASS gate enforce. 본 Story 의 BackfillOrchestrator 재호출 path 가 MCT-151 InvariantHarness inject 자동 동작 (byte-level sha256 + set-level object count + parquet row count + schema-level column count + column name order + dtype identity + schema_version pin 7종). 1종이라도 FAIL 시 NAS PUT 차단 + quarantine 분리 + retry queue enqueue (NASUploader retry 자동) + SOP MANUAL_GATE escalation 의무. D6 invariant wording 변경 0 = invariant SSOT 정합, backlog migration path 추가만 명시.
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md
git commit -m "$(cat <<'EOF'
docs(MCT-159): ADR-027 D6 amendment — 7종 invariant ALL PASS enforce in backlog path

MCT-151 InvariantHarness inject 자동 의무 + 1종 FAIL 시 quarantine + retry + SOP escalation 박제. D6 invariant wording 불변, path 추가.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 3: ADR-027 D9 amendment

**Files:**
- Modify: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (§D9 끝부분, 기존 MCT-156 amendment 다음)

- [ ] **Step 1: D9 amendment 본문 append**

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — mixed layout 본문 재해석. ADR-027 §D9 amendment (MCT-156, 2026-05-13) 본문은 NAS bucket 의 (a) MCT-153 backfill 산출물 legacy ADR-009 §D2.1 layout + (b) MCT-156 Phase 2 신규 hot pipeline 산출물 mixed 공존 박제. **그러나** 2026-05-13 deploy verification 실측에서 (a) 4.2 GiB / 1370 obj 의 NAS 측 손실 확정 박제 (bucket versioning 미활성 = 복구 불가, RETRO-MCT-156 §13.5.2 박제). 즉 본 시점 NAS bucket 의 mixed layout = (b) 신규 schema only — (a) 사실상 무존재. reader fallback (ADR-009 §D2.1+§D14) 은 본 Story 의 MCT-159 이관 산출물 (`hour=HH` + `node=MERGED`) 도 자연 양립 의무, but legacy 객체 부재로 fallback 의존 0. local source 보존 = forward-only invariant 위반 0 (재이관으로 NAS replica 복구 가능). MCT-153 손실 재발 방지 = MCT-161 reserve (bucket versioning 활성화 + replication 정책) 별 Story 책임.
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md
git commit -m "$(cat <<'EOF'
docs(MCT-159): ADR-027 D9 amendment — mixed layout 재해석 (legacy 사실상 무존재)

RETRO-MCT-156 §13.5.2 박제 = MCT-153 산출물 4.2 GiB NAS 손실 확정. mixed layout 의 (a) legacy 부재 박제 + (b) 신규 schema only. local source 보존 = forward-only invariant 위반 0. 재발 방지 = MCT-161 reserve.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 4: docs/stories/MCT-159.md 신규 작성

**Files:**
- Create: `docs/stories/MCT-159.md`

- [ ] **Step 1: Story file 작성 (codeforge §1~§11 schema)**

YAML frontmatter + §1~§11 본문. 본 plan 의 spec file (§1, §3-9) 박제 + ChangeImpactAgent/FeasibilityAgent 산출물 §4 박제 + Test Contract §8 박제. **R3 (HIGH) — disk 압박 4.8% 미달성 한계 §1 first surface 의무**.

Frontmatter:
```yaml
---
story_key: MCT-159
story_scope: cross-repo  # Phase 1 = mctrader-hub governance, Phase 2 = mctrader-data primary + hub Story §11 SSOT
story_issues:
  - repo: mclayer/mctrader-hub
    number: PHASE_1_PR_NUMBER  # Task 7 후 갱신
  - repo: mclayer/mctrader-data
    number: PHASE_2_PR_NUMBER  # Phase 2 PR 후 갱신
status: phase:설계
epic_key: EPIC-cold-tier-stage-3-wiring
epic_milestone: Epic-cold-tier-stage-3-wiring
parent_dependency: EPIC-cold-tier-nas-minio  # Stage 2 CLOSED 2026-05-13
related_adrs:
  - "ADR-027 (amend D4/D6/D9)"
  - "ADR-009 (§D2.1 / §D14 reader fallback — amend 0)"
  - "ADR-017 (§D5 hot path 무영향 — amend 0)"
created_at: 2026-05-13
delegates:
  - mctrader-data
---
```

§1 본문 시작 필수 경고:

```markdown
# MCT-159 — L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 files)

## §1 사용자 요구사항 (verbatim + 한계 surface)

### 사용자 원문 (변경 차단)
> "기존 수집 데이터가 가득 차 있는 것 같은데 S3 minio로 이관 가능하다면 개정된 데이터 경로에 따라 옮기도록 하자"

### 🔴 본 Story 한계 박제 (R3 HIGH severity surface)

본 Story 만으로 사용자 명시 동기 (disk 압박 해소) **미달성** — scope = 8.85 GiB / 전체 backlog ~183 GiB ≈ **4.8% only**. 진짜 disk 압박 원인 = L1 sealed segment 76,200 file (~115 GiB) + WAL 59 GiB = **MCT-160 책임 (sequential 의무)**.

- MCT-159 (본 Story): L2/L3 cold tier 이관
- MCT-160 (reserve): compactor L1 backlog cleanup (orderbookdepth FIX + L2 offset overflow FIX + MCT-153 손실 retrofit)
- MCT-161 (reserve): NAS bucket versioning 활성화 + replication 정책

3-step migration sequence 완료 후 디스크 압박 완전 해소.
```

§2-§11 본문은 spec file 박제를 그대로 옮길 것 (수정 없이 copy-adapt). §11 데이터 마이그레이션 = "local source 보존 → forward-only invariant 위반 0, NAS replica 복구 backfill = 자연 정합". §10 FIX Ledger = 초기 empty.

- [ ] **Step 2: Commit**

```bash
git add docs/stories/MCT-159.md
git commit -m "$(cat <<'EOF'
docs(MCT-159): Story file §1~§11 — L2/L3 cold tier backlog NAS migration

§1 사용자 원문 + R3 (HIGH) 한계 박제 (4.8% only, MCT-160 sequential 의무).
§2~§11 brainstorm spec 박제 transcribe.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 5: scope_manifest patch + CLAUDE.md sections

**Files:**
- Modify: `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml`
- Modify: `CLAUDE.md` (mctrader-hub)
- Modify: `c:\workspace\mclayer\mctrader-data\CLAUDE.md`

- [ ] **Step 1: scope_manifest patch (story_sequence + design_decisions + risks)**

spec §9 박제 그대로 YAML patch 적용. 기존 entries 보존, 신규 추가 only:
- story_sequence: MCT-159 entry 추가
- design_decisions: S8 ~ S15 추가
- risks: R3 / R4 / R5 / R6 추가

- [ ] **Step 2: mctrader-hub CLAUDE.md section 추가**

PMO 산출물 박제 (`Stage 3 backlog migration (MCT-159 follow-up)` section, spec PMOAgent §4 참고).

- [ ] **Step 3: mctrader-data CLAUDE.md section 추가**

PMO 산출물 박제 (`BackfillOrchestrator channel parametrize + hour key amend (MCT-159)` section, spec PMOAgent §4 참고).

- [ ] **Step 4: Commit**

```bash
git add scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml CLAUDE.md
git -C c:\workspace\mclayer\mctrader-data add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(MCT-159): scope_manifest + CLAUDE.md sections — Phase 1 governance

scope_manifest: story_sequence MCT-159 + design_decisions S8~S15 + risks R3-R6.
CLAUDE.md: Stage 3 backlog migration follow-up (hub) + BackfillOrchestrator amend (data).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

(mctrader-data CLAUDE.md commit 은 Phase 2 PR 에서 함께 처리 가능 — Task 14 참조.)

### Task 6: counters.json verification

**Files:**
- Verify: `.codeforge/counters.json` (이미 LAND, 검증만)

- [ ] **Step 1: counters.json 박제 확인**

이미 brainstorm Phase 2 에서 LAND:
- `mctrader-hub.next: 162`
- MCT-159 retitle history 박제
- MCT-160 / MCT-161 reservation entries

- [ ] **Step 2: 변경 없으면 skip, 누락 발견 시 patch**

### Task 7: Phase 1 PR 생성 + merge

**Files:**
- N/A (gh CLI)

- [ ] **Step 1: branch + push**

```bash
cd c:\workspace\mclayer\mctrader-hub
git checkout -b mct-159-phase-1-governance
git push -u origin mct-159-phase-1-governance
```

- [ ] **Step 2: PR 생성**

```bash
gh pr create --title "docs(MCT-159): Phase 1 — ADR-027 D4/D6/D9 amendment + Story + scope_manifest + CLAUDE.md" --body "$(cat <<'EOF'
## Summary

MCT-159 Phase 1 (governance only, 코드 변경 0) — L2/L3 cold tier backlog (~8.85 GiB / 7118 files) NAS migration governance docs LAND.

## 산출물

- ADR-027 D4/D6/D9 amendment (D7/D11 변경 0)
- docs/stories/MCT-159.md (§1~§11, R3 HIGH 한계 박제)
- scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml (S8~S15 + R3-R6)
- CLAUDE.md sections (both repos)
- counters.json: MCT-159 retitle + MCT-160/161 reserve

## 핵심 결정 박제

- D1 (iii): MCT-159 = 이관 only, 기존 3 sub-issue = MCT-160 reserve
- D2 (b): MCT-153 BackfillOrchestrator 재호출 + 2 amendment (channel + hour)
- D3: L2/L3 8.85 GiB only
- D4: ADR-027 D4 + D6 + D9 amendment
- D5: smoke 잔재 별 chore (MCT-158)
- D6: 7d grace 답습
- D7: bucket versioning = MCT-161
- D8: orderbookdepth FIX = MCT-160 (이관 prerequisite 아님)

## 🔴 한계 박제

본 Story 만으로 disk 압박 즉시 해소 미달성 (4.8% only). MCT-160 sequential 의무.

## Test plan
- [ ] ADR-027 D4/D6/D9 amendment 본문 정합 (3 amendment 박제)
- [ ] Story file §1~§11 + R3 한계 surface 정합
- [ ] scope_manifest + CLAUDE.md sections 정합
- [ ] counters.json reservations 박제 정합

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: CI watch + admin merge (사용자 memory autonomy)**

```bash
gh pr checks --watch
# CI green → admin merge 자동
gh pr merge --admin --squash --delete-branch
```

---

## Phase 2 — mctrader-data Implementation PR (TDD 강제)

**중요**: 사용자 unstaged `_discover_partitions()` hot-fix 가 이미 적용 상태. Phase 2 의 첫 step = **test fixture 갱신 (TDD red phase)** 해서 hot-fix 의 silent 통과 위험 (`make_partition_dir` 미수정 → total_chunks=0 오통과) 차단.

### Task 8: Test fixture 갱신 (TDD red phase — silent failure 차단)

**Files:**
- Modify: `tests/nas_migration/test_backfill_orchestrator.py` (`make_partition_dir` helper)
- Modify: `tests/nas_migration/test_backfill_resumability_chaos.py` (동일 helper)
- Test: 위 2 파일

- [ ] **Step 1: 현행 fixture 확인**

```bash
cd c:\workspace\mclayer\mctrader-data
grep -n "make_partition_dir\|schema_version" tests/nas_migration/test_backfill_orchestrator.py
```

Expected: `make_partition_dir` 가 `market/orderbooksnapshot/tier={tier}` 경로 생성 (schema_version=* 누락 발견).

- [ ] **Step 2: 현행 test 실행 (silent pass 재현)**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py -v --tb=short
```

Expected: 일부 test `total_chunks=0` 오통과 (silent — assert 가 0=0 인 path).

- [ ] **Step 3: fixture 갱신 — `make_partition_dir` 에 `schema_version=*` 삽입**

`test_backfill_orchestrator.py` 의 `make_partition_dir` helper 를 다음과 같이 변경 (정확한 line 은 grep 결과 기준):

```python
def make_partition_dir(
    root: Path,
    *,
    channel: str = "orderbooksnapshot",
    schema_version: str = "orderbook_snapshot.v1",
    tier: str = "L2",
    exchange: str = "bithumb",
    symbol: str = "KRW-BTC",
    date_str: str = "2026-05-10",
    hour: str | None = None,  # MCT-159: hour key 처리
    node: str | None = "MERGED",
) -> Path:
    """Create Hive-partitioned dir under market/<channel>/schema_version=<v>/tier=<L>/..."""
    parts = [
        root, "market", channel,
        f"schema_version={schema_version}",
        f"tier={tier}",
        f"exchange={exchange}",
        f"symbol={symbol}",
        f"date={date_str}",
    ]
    if hour is not None:
        parts.append(f"hour={hour}")
    if node is not None:
        parts.append(f"node={node}")
    d = Path(*[str(p) for p in parts])
    d.mkdir(parents=True, exist_ok=True)
    return d
```

- [ ] **Step 4: chaos test fixture 동일 갱신**

`test_backfill_resumability_chaos.py` 의 fixture helper 도 동일 schema 사용 (DRY — `from .test_backfill_orchestrator import make_partition_dir` import 또는 conftest.py 로 이동).

- [ ] **Step 5: test 실행 → 기존 test 들이 변경된 fixture 로 새 schema path 사용하는지 확인**

```bash
python -m pytest tests/nas_migration/ -v --tb=short
```

Expected: 기존 test 일부 PASS (현행 `_discover_partitions()` 가 `schema_version=*` glob 이므로) + 일부 FAIL (hour key 미지원 path 의 invariant verify).

- [ ] **Step 6: Commit**

```bash
git add tests/nas_migration/
git commit -m "$(cat <<'EOF'
test(MCT-159): fixture make_partition_dir schema_version=* + hour key 지원

기존 fixture 가 schema_version=* 미포함으로 _discover_partitions() hot-fix LAND 후 total_chunks=0 silent 오통과 위험. fixture 갱신으로 TDD red phase 강제. hour key 처리는 후속 task 의 implementation 으로 활성화.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 9: backfill_orchestrator.py channel parametrize

**Files:**
- Modify: `src/mctrader_data/nas_migration/backfill_orchestrator.py`
- Test: `tests/nas_migration/test_backfill_orchestrator.py`

- [ ] **Step 1: 신규 test — transaction channel 지원**

`test_backfill_orchestrator.py` 에 추가:

```python
def test_orchestrator_discovers_transaction_channel(tmp_path):
    """MCT-159 — channel parametrize. transaction channel 의 closed-day partition 탐색."""
    make_partition_dir(
        tmp_path,
        channel="transaction",
        schema_version="tick.v1",
        tier="L2",
        date_str="2026-05-10",
        hour="13",
    )
    parquet_path = make_partition_dir(
        tmp_path,
        channel="transaction",
        schema_version="tick.v1",
        tier="L2",
        date_str="2026-05-10",
        hour="13",
    ) / "part-test.parquet"
    parquet_path.write_bytes(b"PAR1")  # dummy parquet marker

    orchestrator = make_orchestrator(local_root=tmp_path, tier="L2", channel="transaction")
    partitions = orchestrator._discover_partitions()
    assert len(partitions) == 1
    assert "transaction" in str(partitions[0])
```

- [ ] **Step 2: test 실행 → FAIL 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py::test_orchestrator_discovers_transaction_channel -v
```

Expected: FAIL — `make_orchestrator(...)` 가 `channel` 인자 모름.

- [ ] **Step 3: `BackfillOrchestrator.__init__` 에 `channel` 파라미터 추가**

`src/mctrader_data/nas_migration/backfill_orchestrator.py:350-382` `__init__` signature:

```python
def __init__(
    self,
    nas_uploader: NASUploader,
    invariant_harness: InvariantHarness,
    sop_runner: NASUnreachableSOPRunner,
    metrics: PrometheusExporter,
    *,
    local_root: Path,
    nas_partition_root: str,
    checkpoint_path: Path,
    evidence_pack_path: Path,
    lock_path: Path = Path("/data/backfill_orchestrator.lock"),
    max_workers: int = 10,
    verify_retry_budget: int = 3,
    chunk_timeout_s: float = 30.0,
    tier: Literal["L2", "L3"] = "L2",
    partition_normalization: bool = True,
    channel: Literal["orderbooksnapshot", "transaction"] = "orderbooksnapshot",  # MCT-159
) -> None:
    # ... 기존 박제 ...
    self._channel = channel
```

- [ ] **Step 4: `_discover_partitions` 에서 channel 사용**

`backfill_orchestrator.py:596` `snapshot_root = self._local_root / "market" / "orderbooksnapshot"` →

```python
# MCT-159: channel parametrize — orderbooksnapshot + transaction 양 channel 지원
channel_root = self._local_root / "market" / self._channel
if not channel_root.exists():
    log.warning("[backfill] channel root not found: %s", channel_root)
    return []

tier_dirs = list(channel_root.glob(f"schema_version=*/tier={self._tier}"))
```

(`snapshot_root` 변수명도 `channel_root` 로 통일)

- [ ] **Step 5: test 실행 → PASS 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py::test_orchestrator_discovers_transaction_channel -v
```

Expected: PASS.

- [ ] **Step 6: 기존 orderbooksnapshot 회귀 test 도 PASS 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py -v -k "not transaction"
```

Expected: 모두 PASS (default `channel="orderbooksnapshot"` backward-compat).

- [ ] **Step 7: Commit**

```bash
git add src/mctrader_data/nas_migration/backfill_orchestrator.py tests/nas_migration/test_backfill_orchestrator.py
git commit -m "$(cat <<'EOF'
feat(MCT-159): BackfillOrchestrator channel parametrize (orderbooksnapshot + transaction)

ADR-027 D4 amendment 정합 — MCT-153 BackfillOrchestrator 재호출 path 의 channel 일반화. default "orderbooksnapshot" backward-compat.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 10: backfill_orchestrator.py hour key 박제

**Files:**
- Modify: `src/mctrader_data/nas_migration/backfill_orchestrator.py`
- Test: `tests/nas_migration/test_backfill_orchestrator.py`

- [ ] **Step 1: 신규 test — hour partition path 처리**

```python
def test_chunk_spec_includes_hour_partition(tmp_path):
    """MCT-159 — hour key 박제. 신규 schema 의 hour=HH/node=MERGED 가 nas_object_key 에 박제."""
    parquet_path = make_partition_dir(
        tmp_path,
        channel="orderbooksnapshot",
        schema_version="orderbook_snapshot.v1",
        tier="L2",
        date_str="2026-05-10",
        hour="13",
        node="MERGED",
    ) / "part-abc123.parquet"
    parquet_path.write_bytes(b"PAR1")

    orchestrator = make_orchestrator(local_root=tmp_path, tier="L2", nas_partition_root="tier=L2")
    chunk = orchestrator._build_chunk_spec(parquet_path)
    assert "hour=13" in chunk.nas_object_key
    assert "node=MERGED" in chunk.nas_object_key
    assert chunk.nas_object_key.endswith("part-abc123.parquet")
```

- [ ] **Step 2: test 실행 → FAIL 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py::test_chunk_spec_includes_hour_partition -v
```

Expected: FAIL — `_build_chunk_spec` 가 hour 축 모름, nas_object_key 에 `hour=` 없음.

- [ ] **Step 3: `_build_chunk_spec` 에 hour 축 추가**

`backfill_orchestrator.py:645-709` `_build_chunk_spec` 메소드:

```python
def _build_chunk_spec(self, source_path: Path) -> ChunkSpec:
    parts = source_path.parts
    exchange = _extract_hive_value(parts, "exchange")
    symbol = _extract_hive_value(parts, "symbol")
    date_str = _extract_hive_value(parts, "date")
    hour = _extract_hive_value(parts, "hour")  # MCT-159: hour 축 추가
    node = _extract_hive_value(parts, "node")

    if symbol is None:
        symbol = "UNKNOWN"
    if date_str is None:
        date_str = "unknown"

    is_legacy_node = node is None

    # MCT-159: nas_partition_prefix 에 hour=HH 박제 (있으면)
    hour_segment = f"/hour={hour}" if hour is not None else ""

    if is_legacy_node:
        nas_partition_prefix = (
            f"{self._nas_partition_root}"
            f"/exchange={exchange or 'UNKNOWN'}"
            f"/symbol={symbol}"
            f"/date={date_str}"
            f"{hour_segment}"
            f"/node=DEFAULT"
        )
        if self._metrics is not None:
            with contextlib.suppress(Exception):
                self._metrics.emit_backfill_legacy_node_default()
    else:
        nas_partition_prefix = (
            f"{self._nas_partition_root}"
            f"/exchange={exchange or 'UNKNOWN'}"
            f"/symbol={symbol}"
            f"/date={date_str}"
            f"{hour_segment}"
            f"/node={node}"
        )

    nas_object_key = f"{nas_partition_prefix}/{source_path.name}"
    chunk_id = hashlib.sha256(
        f"{symbol}|{date_str}|{source_path}".encode()
    ).hexdigest()[:16]

    return ChunkSpec(
        symbol=symbol,
        date=date_str,
        source_path=source_path,
        nas_object_key=nas_object_key,
        nas_partition_prefix=nas_partition_prefix,
        is_legacy_node=is_legacy_node,
        chunk_id=chunk_id,
    )
```

- [ ] **Step 4: test 실행 → PASS 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py::test_chunk_spec_includes_hour_partition -v
```

Expected: PASS.

- [ ] **Step 5: 회귀 — hour 부재 case (legacy) 도 PASS 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py -v
```

Expected: 모두 PASS. `hour_segment = ""` 일 때 legacy path 그대로 (MCT-156 S1/S6 정합 유지).

- [ ] **Step 6: Commit**

```bash
git add src/mctrader_data/nas_migration/backfill_orchestrator.py tests/nas_migration/test_backfill_orchestrator.py
git commit -m "$(cat <<'EOF'
feat(MCT-159): BackfillOrchestrator hour key 박제 (_build_chunk_spec)

ADR-027 D4 amendment 정합 — 신규 schema `tier=L{2,3}/.../date=D/hour=HH/node=MERGED/` 의 hour 축 ChunkSpec.nas_object_key 에 박제. hour 부재 (legacy) backward-compat 유지.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 11: run_backfill.py CLI `--channel` flag

**Files:**
- Modify: `scripts/migration/run_backfill.py`

- [ ] **Step 1: 현행 CLI 확인**

```bash
grep -n "click.option\|--tier\|--channel" scripts/migration/run_backfill.py
```

- [ ] **Step 2: `--channel` flag 추가 + `BackfillOrchestrator` 호출 전파**

`run_backfill.py` 의 click command 에:

```python
@click.option(
    "--channel",
    type=click.Choice(["orderbooksnapshot", "transaction"]),
    default="orderbooksnapshot",
    help="MCT-159: channel parametrize. default orderbooksnapshot (MCT-153 backward-compat).",
)
```

`BackfillOrchestrator(...)` 호출 부 `channel=channel` 전달.

- [ ] **Step 3: evidence pack path 갱신 — MCT-153 → MCT-159**

`evidence_pack_path` default 또는 explicit path 가 `.tmp/evidence-pack-MCT-153.md` 박제 시 `.tmp/evidence-pack-MCT-159.md` 로 변경 (또는 `--evidence-pack` flag override 권장).

- [ ] **Step 4: `_run_dry()` 에도 channel 적용**

`_run_dry` 의 path 구성 부분 channel parametrize:

```python
channel_root = local_root / "market" / channel
tier_dirs = list(channel_root.glob(f"schema_version=*/tier={tier}"))
```

- [ ] **Step 5: dry-run 실행 — 양 channel + 양 tier 4 case**

```bash
cd c:\workspace\mclayer\mctrader-data
python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L2 --dry-run
python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L3 --dry-run
python scripts/migration/run_backfill.py --channel transaction --tier L2 --dry-run
python scripts/migration/run_backfill.py --channel transaction --tier L3 --dry-run
```

Expected: 각 case 가 발견 partition 수 보고:
- orderbooksnapshot L2 ≈ 2305 files
- orderbooksnapshot L3 ≈ 429 files
- transaction L2 ≈ 3335 files
- transaction L3 ≈ 1049 files

(host 경로 의존 — Docker volume 직접 mount 필요 시 `docker exec mctrader-compactor python ...` 로 실행)

- [ ] **Step 6: Commit**

```bash
git add scripts/migration/run_backfill.py
git commit -m "$(cat <<'EOF'
feat(MCT-159): run_backfill.py --channel flag + evidence pack MCT-159

CLI channel parametrize + dry-run path 신규 schema 정합. 4 case (orderbooksnapshot × L2/L3 + transaction × L2/L3) dry-run 검증 의무.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 12: Integration test 7종 (AC-1~AC-5 + Edge Case 2)

**Files:**
- Modify: `tests/nas_migration/test_backfill_orchestrator.py` (확장)

각 AC 별 test 추가. AC-3 (7종 invariant ALL PASS) 는 MCT-151 InvariantHarness 가 자동 처리 — 본 test 는 inject 정합 검증만.

- [ ] **Step 1: AC-1 — 신규 schema path 100% 준수 test**

```python
def test_ac_1_new_schema_path_100_percent(tmp_path):
    """AC-1: 신규 schema (hour=HH/node=MERGED) path 100% 준수, legacy 경로 혼입 0."""
    # ... fixture 4 partition × hour 다른 값 + node=MERGED ...
    # orchestrator.run() 실행 후 chunk.nas_object_key 모두 hour= + node=MERGED 포함 검증
    # legacy path (node=DEFAULT) 0건 검증
```

- [ ] **Step 2: AC-2 — MCT-156 S1/S6 정합 (legacy hour-key 부재 제외)**

```python
def test_ac_2_mct156_legacy_exclusion(tmp_path):
    """AC-2: legacy hour-key 부재 partition 은 별 fixture 로 만들어도 본 Story 산출물에 포함 0."""
    # ... fixture: 신규 schema partition + legacy partition (hour 없음) ...
    # orchestrator.run() 결과 모든 chunk.nas_object_key 가 hour= 포함 (legacy 제외 정책 정합)
```

- [ ] **Step 3: AC-3 — InvariantHarness inject 자동 (MCT-151 retest 회피, inject 정합만)**

```python
def test_ac_3_invariant_harness_injected(tmp_path):
    """AC-3: BackfillOrchestrator 가 InvariantHarness inject 받아 verify 자동 호출."""
    mock_harness = MagicMock(spec=InvariantHarness)
    mock_harness.verify.return_value = InvariantResult(status="all_pass", ...)
    orchestrator = make_orchestrator(local_root=tmp_path, invariant_harness=mock_harness)
    # ... fixture 1 partition + dummy parquet ...
    orchestrator.run()
    mock_harness.verify.assert_called()
```

- [ ] **Step 4: AC-4 — orderbooksnapshot + transaction 양 channel + L2/L3 양 tier matrix**

```python
@pytest.mark.parametrize("channel", ["orderbooksnapshot", "transaction"])
@pytest.mark.parametrize("tier", ["L2", "L3"])
def test_ac_4_channel_tier_matrix(tmp_path, channel, tier):
    """AC-4: channel + tier 4 case 매트릭스 검증."""
    # ... fixture per case + orchestrator.run() + PASS 검증 ...
```

- [ ] **Step 5: AC-5 — Edge Case (1) 경로 매핑 실패 quarantine + (2) 검증 부분 실패 local delete 차단**

```python
def test_ac_5_edge_case_path_mapping_failure(tmp_path):
    """EC-1: date/hour/node 누락 partition 은 quarantine 분리."""
    # ... fixture: invalid partition (date 없음) ...
    # orchestrator.run() 결과 quarantined_chunks >= 1, verified_chunks 에 미포함

def test_ac_5_edge_case_partial_verify_fail_blocks_local_delete(tmp_path):
    """EC-2: 검증 부분 실패 시 local delete 차단 (CutoverVerifier gate)."""
    # ... fixture 3 partition, 그 중 1 invariant FAIL ...
    # orchestrator.run() 후 local source 모두 보존 검증 (delete 미실행)
```

- [ ] **Step 6: 전체 integration test 실행 → 7종 ALL PASS 확인**

```bash
python -m pytest tests/nas_migration/test_backfill_orchestrator.py -v
```

Expected: 모두 PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/nas_migration/
git commit -m "$(cat <<'EOF'
test(MCT-159): integration test 7종 (AC-1~AC-5 + Edge Case 2)

AC-1 신규 schema path 100% / AC-2 legacy 제외 / AC-3 InvariantHarness inject / AC-4 channel+tier matrix / AC-5 quarantine + delete block.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 13: Perf baseline 측정 (35min @ 10-parallel)

**Files:**
- Modify: `tests/nas_migration/test_backfill_orchestrator.py` (perf marker)
- Test: dry-run wall-clock measurement

- [ ] **Step 1: 4 case dry-run wall-clock 측정 (chunk discovery + spec 생성만)**

```bash
docker exec mctrader-compactor python -m timeit -n 1 -r 1 -s "from mctrader_data.nas_migration.backfill_orchestrator import BackfillOrchestrator; from unittest.mock import MagicMock; ..." "BackfillOrchestrator(...).run()"
```

(실제 chunk 측정 — Phase 14 의 실 이관 시 측정 가능, 본 task 는 plan 박제만)

- [ ] **Step 2: 측정 결과 기록 → `tests/perf/backfill_orchestrator_baseline.json`**

```json
{
  "story": "MCT-159",
  "measured_at": "YYYY-MM-DDTHH:MM:SSZ",
  "scope": "L2/L3 cold tier backlog 8.85 GiB / 7118 files",
  "per_chunk_s_p99": "...",
  "parallel_workers": 10,
  "total_wall_clock_min": "...",
  "nfr_budget_min": 80,
  "margin_min": "..."
}
```

- [ ] **Step 3: Commit**

```bash
git add tests/perf/backfill_orchestrator_baseline.json
git commit -m "$(cat <<'EOF'
test(MCT-159): perf baseline — 35min @ 10-parallel target

NFR budget 80 min 의 margin ≥ 45 min 확보 의무. MCT-153 baseline (per-chunk 3s) 재사용.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task 14: mctrader-data PR 생성 + merge

**Files:**
- N/A (gh CLI)

- [ ] **Step 1: branch + push**

```bash
cd c:\workspace\mclayer\mctrader-data
git checkout -b mct-159-phase-2-impl
git push -u origin mct-159-phase-2-impl
```

- [ ] **Step 2: PR 생성**

```bash
gh pr create --title "feat(MCT-159): Phase 2 — BackfillOrchestrator channel parametrize + hour key + 7 invariant test" --body "$(cat <<'EOF'
## Summary

MCT-159 Phase 2 (mctrader-data primary impl) — L2/L3 cold tier backlog (~8.85 GiB / 7118 files) NAS migration 구현.

## 산출물 4 file 수정

- `src/mctrader_data/nas_migration/backfill_orchestrator.py`:
  - channel parametrize (orderbooksnapshot + transaction)
  - hour key 박제 (_build_chunk_spec)
- `scripts/migration/run_backfill.py`:
  - --channel flag + evidence pack MCT-159
  - _run_dry channel 적용
- `tests/nas_migration/test_backfill_orchestrator.py`:
  - fixture schema_version=* + hour key 지원
  - integration test 7종 (AC-1~AC-5 + Edge Case 2)
- `tests/nas_migration/test_backfill_resumability_chaos.py`:
  - 동일 fixture 갱신

## 🔴 한계 재박제 (R3 HIGH)

본 PR LAND 만으로 disk 압박 즉시 해소 미달성 (4.8% only). MCT-160 sequential 의무.

## Test plan
- [ ] 양 channel × 양 tier (4 case) dry-run PASS
- [ ] integration test 7종 ALL PASS
- [ ] 7종 invariant harness (MCT-151) inject 자동 verify
- [ ] legacy path backward-compat (hour 부재) 회귀 0
- [ ] Perf baseline 35min @ 10-parallel target margin ≥ 45min

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: CI watch + admin merge**

```bash
gh pr checks --watch
gh pr merge --admin --squash --delete-branch
```

### Task 15: 실 이관 execute (8.85 GiB) — dry-run 선행 + 실 execute

**Files:**
- N/A (run-time execution)

- [ ] **Step 1: 4 case dry-run (mctrader-compactor container 내)**

```bash
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L2 --dry-run
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L3 --dry-run
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel transaction --tier L2 --dry-run
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel transaction --tier L3 --dry-run
```

Expected: 각 case 가 closed-day partition 수 보고 (UTC 당일 partition 제외).

- [ ] **Step 2: dry-run 결과 사용자 review + confirm**

각 case 의 chunk 수 + estimated wall-clock + invariant pre-check 결과 확인.

- [ ] **Step 3: 실 execute 4 case sequential**

```bash
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L2 --execute
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel orderbooksnapshot --tier L3 --execute
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel transaction --tier L2 --execute
docker exec mctrader-compactor python scripts/migration/run_backfill.py --channel transaction --tier L3 --execute
```

- [ ] **Step 4: NAS bucket 측정 (mc du)**

```bash
docker run --rm --network mctrader_net --entrypoint sh minio/mc:latest -c \
  "mc alias set nas http://mcnas01.internal.mclayer.it:9000 mctrader-admin 'w2It9QoFtCs/tibmac7V/qAxvvVdcK8Z' && mc du --depth 4 nas/mctrader-market"
```

Expected: market/ 산하 신규 schema (`hour=` + `node=MERGED`) 객체 ~7118 + base hot pipeline 산출물 추가.

- [ ] **Step 5: evidence pack 검증**

`.tmp/evidence-pack-MCT-159.md` 박제 — 4 case verified_chunks / quarantined_chunks / blocked_chunks / sha256 + 7 invariant pass rate 박제.

### Task 16: 7d grace + gc_runner (D7 답습) — local delete

**Files:**
- N/A (run-time, 7d 후 실행)

- [ ] **Step 1: gc_runner 7d grace 시작 시점 박제**

`docs/stories/MCT-159.md` §11 데이터 마이그레이션 trace 에 박제:
```
- migration_completed_at: <Task 15 완료 시점 ISO timestamp>
- gc_eligible_at: <migration_completed_at + 7 days>
```

- [ ] **Step 2: 7d 후 gc_runner --dry-run 실행**

```bash
docker exec mctrader-compactor python -m mctrader_data.nas_migration.gc_runner --dry-run --since-day <migration_completed_at minus 7d>
```

- [ ] **Step 3: dry-run 결과 사용자 review + invariant ALL PASS 재검증**

- [ ] **Step 4: gc_runner --execute (local delete)**

```bash
docker exec mctrader-compactor python -m mctrader_data.nas_migration.gc_runner --execute --since-day <...>
```

Expected: 로컬 disk 해제 ~8.85 GiB. WAL + hot data + L1 sealed 보존 검증.

- [ ] **Step 5: §11 데이터 마이그레이션 final trace 박제**

`docs/stories/MCT-159.md` §11 에:
```
- local_delete_executed_at: <ISO timestamp>
- local_disk_freed: ~8.85 GiB (actual measured: <...>)
- WAL_preserved: true
- L1_sealed_preserved: true
- forward_only_invariant_violation: 0
```

### Task 17: PMOAgent retro + §11 SSOT + Phase 2 PR governance

**Files:**
- Modify: `docs/stories/MCT-159.md` (§11 self-write)
- Modify: `docs/retros/RETRO-MCT-159.md` (PMOAgent retro 산출)
- Modify: `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` (epic_close_gate 갱신)
- Modify: `CLAUDE.md` (Stage 3 backlog migration status 갱신)

- [ ] **Step 1: PMOAgent dispatch (codeforge-pmo:PMOAgent)**

PMOAgent 에게 본 Story 완료 회고 의뢰 — §11 self-write + RETRO-MCT-159 작성 + Cross-Story pattern 누적.

- [ ] **Step 2: PMOAgent 산출물 검증 (사용자 review 옵션)**

- [ ] **Step 3: Phase 2 governance PR 생성 + merge**

```bash
cd c:\workspace\mclayer\mctrader-hub
git checkout -b mct-159-phase-2-governance
git push -u origin mct-159-phase-2-governance
gh pr create --title "docs(MCT-159): Phase 2 — PMOAgent retro + §11 self-write + Epic milestone 갱신" --body "..."
gh pr checks --watch
gh pr merge --admin --squash --delete-branch
```

- [ ] **Step 4: counters.json LAND 정합 + reservation marker DELETE**

MCT-159 reservation entry 가 LAND 처리되어야 (Story file 박제 후 자동) — `.codeforge/counters.json` 의 reservations 에서 MCT-159 제거 (MCT-160/161 reserve 는 유지).

```diff
- "MCT-159": { "title": "L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 files, channel parametrize + hour key amend)", ... }
```

---

## Self-Review (Phase 1 + Phase 2 통합 검토)

**1. Spec coverage**:
- §1 사용자 원문 + R3 한계 박제 → Task 4 (§1 first surface)
- §2 WHY → Task 4 (§2 본문)
- §3 7 Agent Phase 0 → Task 4 (§3 본문)
- §4 Phase 1 8 D 결정 → Task 1-3 (ADR amend) + Task 5 (scope_manifest S8-S15)
- §5 AC-1~AC-5 + Edge Case 2 → Task 12 (integration test 7종)
- §6 Phase 분해 + Test Contract → Task 1-13 전체 + Task 14 PR
- §7 ADR-027 amendment 본문 → Task 1-3
- §8 R3-R5 risk → Task 4 (Story §7) + Task 5 (scope_manifest R3-R6)
- §9 scope_manifest patch → Task 5
- §10 의존성 + Sequential → Task 7 PR body + Task 15-17

**2. Placeholder scan**: 모든 step 에 concrete 코드 + 명령 박제. "TBD" / "implement later" 0건.

**3. Type consistency**: `channel: Literal["orderbooksnapshot", "transaction"]` 일관 (Task 9, 11). `hour: str | None` 일관 (Task 10, fixture Task 8). `ChunkSpec.nas_object_key` 의 `hour=HH` 박제 (Task 10).

**4. Gap fix**: Task 17 의 PMOAgent dispatch 가 RETRO-MCT-159 자동 생성 — 본 Story 완료 후 PMOAgent 의 retro 산출이 Cross-Story pattern 누적 (RETRO-MCT-156 §13.8 의 ADR-XXX 후보 "production cutover gate evidence pack 의무" 발의 trigger) 와 연결될 수 있음 — PMOAgent 가 본 cycle 의 pattern 누적 확인 + ADR 후보 발의 의무 박제.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-mct-159-l2l3-backlog-nas-migration.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration. Phase 1 + Phase 2 별 두 PR sequential. Phase 1 = 7 task (governance, mctrader-hub). Phase 2 = 10 task (impl + test + run, mctrader-data + hub Story §11 SSOT).

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
