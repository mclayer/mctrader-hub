# MCT-192 — Cross-repo Telemetry Counter Emit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. **trust-but-verify 강제 (MCT-190 Lesson 5 / plugin-codeforge#822 + 본 Story PMOAgent R1 false premise 재발)**: implementer subagent 는 Write/Edit/Create 후 자동 verify report (ls + line/grep + git status). **Orchestrator 는 모든 critical artifact + subagent BLOCKER 보고를 직접 ls/grep verify 의무** (PMOAgent 2nd pass R1 'ADR-033 부재' = false premise 재발 — subagent path 오류 가능, Orchestrator 직접 재verify 가 SSOT).

**Goal:** ADR-033 §2 quad v2 4번째 게이트 (runtime telemetry counter ≥1 over N days) 실 cross-repo wiring — ADR-029/030 기존 counter 재사용 (신규 emit 0) + ADR-031 data realtime_stream 신규 emit (no-op stub 해소).

**Architecture:** EPIC-evidence-quad-runtime-telemetry sub-2. cross-repo = mctrader-hub (governance) + mctrader-data (code, engine DROP — Phase 0 verify: engine pure consumer telemetry zero 정상). 3 PR sequential: PR-1 hub docs → PR-2 data code → PR-3 hub 박제 (MCT-185 류 2-repo 축소). ADR-031 publish_tick caller 0 = dead-in-data 정직 박제 (R2 가공 metric 7회째 차단).

**Tech Stack:** Markdown/YAML/JSON (hub governance), Python prometheus_client.Counter (data realtime_stream), pytest (counter ≥1 단발성 integration test), Git cross-repo workflow (hub worktree + data 별 worktree 격리).

**Worktree:** hub = `c:\workspace\mclayer\mctrader-hub\.claude\worktrees\mct-192-telemetry-emit`. data = `/c/workspace/mclayer/mctrader-data` 별 worktree 격리 의무 (memory feedback_parallel_session_branch_race tier-1 data).

**Spec reference:** `docs/superpowers/specs/2026-05-17-MCT-192-telemetry-emit-design.md` (§6 scope_manifest YAML SSOT)

---

## File Structure

### PR-1 (hub Phase 1 docs) — mctrader-hub worktree
| F | path | action |
|---|------|--------|
| F1 | `docs/stories/MCT-192.md` | create |
| F2 | `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` | amend (§본문 per-ADR counter mapping table + §9.1 sub-2 draft) |
| F3 | `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml` | amend (sub-2 + verify_evidence_telemetry_counter_schema 3 ADR) |
| F4 | `.codeforge/counters.json` | amend (MCT-192 RESERVED → IN_PROGRESS) |
| F5 | spec + plan (본 file) | create (자동 포함) |

### PR-2 (data Phase 2 PR1 code) — mctrader-data 별 worktree
| F | path | action |
|---|------|--------|
| F6 | `src/mctrader_data/api/realtime_stream.py` | modify (`_emit_failure_counter()` no-op stub line 147-154 → 실 Counter .inc() + Counter 정의 + 주석 MCT-186→MCT-192) |
| F7 | `tests/api/test_realtime_stream_counter.py` | create (XADD fail inject → counter ≥1 단발성) |

### PR-3 (hub Phase 2 PR2 박제) — mctrader-hub worktree
| F | path | action |
|---|------|--------|
| F8 | `docs/stories/MCT-192.md` | amend (§8.5 Impl Manifest + §11 LAND timeline) |
| F9 | `docs/retros/RETRO-MCT-192.md` | create (trust-but-verify 동형 재발 Lesson) |
| F10 | `docs/retros/PMO-AUDIT-MCT-192.md` | create (R1 false premise 기각 박제) |
| F11 | `docs/retros/EPIC-RESULTS-EPIC-evidence-quad-runtime-telemetry.md` | amend (§Story-2 milestone 2/3) |
| F12 | `.codeforge/counters.json` | amend (MCT-192 COMPLETED) |
| F13 | `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` | amend (§9.1 sub-2 VERIFIED) |
| F14 | `CLAUDE.md` | amend (§EPIC milestone 1/3 → 2/3) |

---

## Task Decomposition

### PR-1 (hub Phase 1 docs) — land_order 1

#### Task 1: Story MCT-192.md 신규 (F1)

**Files:** Create `docs/stories/MCT-192.md` (~280 lines)

**Reference:** spec §1-§7 + `docs/stories/MCT-191.md` (선례 doc Story 패턴).

- [ ] **Step 1: frontmatter + §0 Phase 0 Verify Gate**

```yaml
---
key: MCT-192
title: "Cross-repo telemetry counter emit — ADR-029/030/031 quad evidence (기존 2 재사용 + realtime_stream 1 신규, engine DROP)"
status: COMPLETED  # post-LAND 전환
repo: "mctrader-hub + mctrader-data"
phase_pair: phase1_phase2
epic: EPIC-evidence-quad-runtime-telemetry
sequential_phase: 2
parent_dependency: "MCT-191 (sub-1 LAND hub#382/#383)"
created_at: "2026-05-17"
completed_at: "2026-05-17"
worktree: "c:\\workspace\\mclayer\\mctrader-hub\\.claude\\worktrees\\mct-192-telemetry-emit"
land_prs:
  - "mctrader-hub#TBD (PR-1 docs)"
  - "mctrader-data#TBD (PR-2 code)"
  - "mctrader-hub#TBD (PR-3 박제)"
---
```

§0 Phase 0 Verify Gate = spec §1.2 table (V1 worktree base / V2 PMOAgent R1 false premise 기각 / D3 ADR-029 anchor / D4 ADR-030 anchor / D5 ADR-031 anchor / D6 realtime_stream carry / ED engine drop PASS).

- [ ] **Step 2: §1-§5 (요구사항 + spec/plan cross-ref + AC-1~5 + 9 결정점 Q1-Q9)**

§1 사용자 요구사항 ("다음 작업 진행"). §2 spec cross-ref. §3 AC-1~5 (spec §4). §4 plan cross-ref. §5 Q1-Q9 table (Codex 9/9 정합 deviation 0).

- [ ] **Step 3: §6 risks (R1 RESOLVED false premise / R2 HIGH 가공 metric 7회째 / R3 LOW carry / R4 MEDIUM SSOT / R5 MEDIUM 박제 incomplete) + §7 cross-ref + §8 Test Contract**

§8 Test Contract = PR-2 data `test_realtime_stream_counter.py` (XADD fail inject → `mctrader_data_redis_stream_publish_failures_total` ≥1 단발성, Q8=C boundary). ADR-029/030 = 기존 counter (test 신규 0, MCT-189/179 evidence 재인용).

- [ ] **Step 4: §9 cross-Story carry + §10 FIX Ledger placeholder + §11 LAND timeline placeholder + §12 회고 placeholder**

§9 = trust-but-verify 동형 재발 (PMOAgent R1 false premise, plugin-codeforge#822 self-discipline gate v1 적용에도 PMOAgent path 오류 — RETRO Lesson carrier). engine drop 정합. §11 3 PR placeholder (#TBD).

- [ ] **Step 5: verify (ls + line ~280 + grep `§8.5|Q1-Q9|engine DROP|dead-in-data|trust-but-verify` + git status). verify report 의무.**

#### Task 2: ADR-033 §본문 mapping table amend (F2)

**Files:** Modify `docs/adr/ADR-033-evidence-quad-enforcement-layer.md` (~+30 lines)

**Reference:** spec §6 verify_evidence_telemetry_counter_schema (3 ADR). 기존 ADR-033 §본문 (Grep `## §| per-ADR| mapping| §9`).

- [ ] **Step 1: §본문 per-ADR counter mapping table 추가 (Q5=C governance 중앙 reference)**

ADR-033 §본문 (적절 § — §3 class taxonomy 또는 §본문 신규 §) 에 table:
```markdown
### per-ADR Telemetry Counter Mapping (governance 중앙 reference, drift 시 scope_manifest verify_evidence 우선)

| ADR | counter | labels | quad_query | emit_location | traffic_class |
|-----|---------|--------|-----------|---------------|---------------|
| ADR-029 | `mctrader_dual_write_result_total` | {status,tier} | `increase(...{status="success"}[14d]) >= 1` | data compactor/runner.py:285 (MCT-189 재사용, 신규 0) | production-wired 14d |
| ADR-030 | `mctrader_collector_ticks_total` | {exchange,symbol} | `increase(...[14d]) >= 1` | data collector.py:189 record_collector_tick (MCT-180/179 재사용, 신규 0) | trading-hot market-open rolling |
| ADR-031 | `mctrader_data_redis_stream_publish_failures_total` | [] | `increase(...[14d]) >= 0` | data realtime_stream.py:147-154 (MCT-192 신규 emit, no-op stub 해소) | test-injected only (publish_tick caller=0 dead-in-data — MCT-193 rolling gate prerequisite) |

SSOT precedence: scope_manifest `verify_evidence_telemetry_counter_schema` (per-Epic 실행 SSOT) > 본 table (governance reference). drift 시 scope_manifest 우선 (Q5=C).
```

- [ ] **Step 2: §9.1 sub-2 LAND confirm draft 추가**

§9 future-work 의 sub-2 항목에 "MCT-192 PR-1 docs LAND (counter mapping table + scope_manifest schema). PR-2 data realtime_stream emit + PR-3 박제 후 §9.1 sub-2 VERIFIED (PR-3 amend)." draft 박제.

- [ ] **Step 3: verify (Read amended §본문 + §9.1, Grep `per-ADR Telemetry Counter Mapping|sub-2`, 기존 §1-§9 본문 보존 confirm, git status). verify report 의무.**

#### Task 3: scope_manifest amend (F3)

**Files:** Modify `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`

**Reference:** spec §6 YAML 완전체 (sub-2 + verify_evidence_telemetry_counter_schema 3 ADR + planned_files + risks + pr_completeness_checklist).

- [ ] **Step 1: spec §6 YAML 의 sub-2 MCT-192 + verify_evidence_telemetry_counter_schema 직접 carry**

기존 scope_manifest 의 sub_stories MCT-192 entry 정밀화 + `verify_evidence_telemetry_counter_schema` 3 ADR block + planned_files (hub+data) + risks R1-R5 + pr_completeness_checklist 3 PR. 기존 sub-1 MCT-191 entry + 기타 보존 (amend only).

- [ ] **Step 2: verify (Read full + YAML lint python yaml.safe_load + Grep `verify_evidence_telemetry_counter_schema|sub-2|MCT-192`, git status). verify report 의무.**

#### Task 4: counters.json MCT-192 IN_PROGRESS (F4)

**Files:** Modify `.codeforge/counters.json`

- [ ] **Step 1: MCT-192 entry RESERVED → IN_PROGRESS + started_at + worktree**

기존 MCT-192 entry (status RESERVED) → `"started_at": "2026-05-17"` + `"status": "IN_PROGRESS"` + `"worktree": "...mct-192-telemetry-emit"` 추가. 기존 title/epic/sequential_phase/depends_on/rationale 보존. (post-merge PR-3 = COMPLETED + land_prs + completed_at.)

- [ ] **Step 2: verify (python json.load valid + Grep MCT-192 status IN_PROGRESS + 기존 entry 보존, git status). verify report 의무.**

#### Task PR-1-LAND: hub Phase 1 docs commit + push + PR open + admin merge (Orchestrator direct)

- [ ] git status verify (Orchestrator 직접 — 5 file: Story/ADR-033/scope_manifest/counters/spec+plan). critical artifact ls/grep verify (PMOAgent R1 false premise 재발 차단).
- [ ] message file 방식 commit (PowerShell quote escaping 회피) + push + PR open (body file) + CI status + `gh pr merge --admin --squash`. PR# 기록 (PR-2 입력).

---

### PR-2 (data Phase 2 PR1 code) — mctrader-data 별 worktree, land_order 2

> **PR-1 MERGED 후 진입** (counter name SSOT = hub ADR-033/scope_manifest 박제 후). data repo 별 worktree 격리 의무.

#### Task 5: realtime_stream.py counter emit (F6)

**Files:** Modify `src/mctrader_data/api/realtime_stream.py` (mctrader-data repo)

**Reference (verified-via 실측):** `realtime_stream.py:52` docstring counter name / `:103` publish_tick / `:145` `self._emit_failure_counter()` 호출 / `:147-154` `_emit_failure_counter()` no-op stub. `metrics.py` 의 Counter 정의 패턴 정합 (prometheus_client.Counter).

- [ ] **Step 1: data 별 worktree 격리 진입**

```bash
cd /c/workspace/mclayer/mctrader-data && git fetch origin && git worktree add .claude/worktrees/mct-192-data -b worktree-mct-192-data origin/main
```
(또는 EnterWorktree 불가 시 git worktree add 직접 — memory feedback_parallel_session_branch_race tier-1 data 의무)

- [ ] **Step 2: failing test 먼저 (TDD)**

`tests/api/test_realtime_stream_counter.py` 신규 — XADD 실패 inject → `mctrader_data_redis_stream_publish_failures_total` counter ≥1 assert:
```python
import pytest
from prometheus_client import REGISTRY
from mctrader_data.api.realtime_stream import RealtimeStreamPublisher

@pytest.mark.asyncio
async def test_publish_failure_increments_counter(monkeypatch):
    pub = RealtimeStreamPublisher(redis_client=_FakeRedisRaising())
    before = _counter_value("mctrader_data_redis_stream_publish_failures_total")
    await pub.publish_tick(_sample_tick())  # XADD raises → _emit_failure_counter()
    after = _counter_value("mctrader_data_redis_stream_publish_failures_total")
    assert after >= before + 1, "counter must increment on publish failure (ADR-031 quad evidence)"
```
(실 fake/fixture 구조는 기존 tests/api/ 패턴 정합 — Read tests/api/ 후 동형 작성)

- [ ] **Step 3: test fail 확인** — `pytest tests/api/test_realtime_stream_counter.py -v` → FAIL (`_emit_failure_counter` no-op, counter unregistered)

- [ ] **Step 4: Counter 정의 + `_emit_failure_counter()` no-op stub 해소**

`realtime_stream.py` 상단 (metrics.py 패턴 정합):
```python
from prometheus_client import Counter
_publish_failures_total = Counter(
    "mctrader_data_redis_stream_publish_failures_total",
    "Redis Stream XADD publish failures (ADR-031 realtime contract producer, MCT-192 quad evidence)",
)
```
`_emit_failure_counter()` (line 147-154) no-op `pass` → `self.__class__` 또는 module-level counter `.inc()`:
```python
def _emit_failure_counter(self) -> None:
    """mctrader_data_redis_stream_publish_failures_total Counter emit (best-effort).
    ADR-031 realtime contract producer quad evidence (MCT-192, no-op stub 해소).
    """
    try:
        _publish_failures_total.inc()
    except Exception:  # noqa: BLE001 — telemetry best-effort, never break publish path
        pass
```
주석 line ~150 `MCT-186 owner` → `MCT-192` 정정 (D6).

- [ ] **Step 5: test pass 확인** — `pytest tests/api/test_realtime_stream_counter.py -v` → PASS

- [ ] **Step 6: counter-emit triad v1 reapply 자체 verify (Q7=B 신규 emit = 새 triad)**

```bash
# (1) file:line — realtime_stream.py:147-154 _emit_failure_counter + Counter 정의 line
# (2) caller grep ≥1 — _emit_failure_counter 호출 site
git grep -n "_emit_failure_counter" -- src/   # → line 145 publish_tick 내부 호출 confirm ≥1
# (3) integration test — test_realtime_stream_counter.py PASS
```
counter-emit triad v1 3종 verify report. `publish_tick` producer caller 0 = dead-in-data → test-injected only (scope_manifest caveat 정합, R2 차단).

- [ ] **Step 7: 회귀 0 verify** — `pytest tests/ -q` (data full suite) → 신규 실패 0 (기존 baseline 대비)

- [ ] **Step 8: commit (data worktree)** — message file 방식. Co-Authored-By.

#### Task PR-2-LAND: data push + PR open + admin merge (Orchestrator direct)

- [ ] Orchestrator git status verify (data worktree — realtime_stream.py M + test_realtime_stream_counter.py ??). git diff --stat.
- [ ] push + `gh pr create --repo mclayer/mctrader-data` + CI status + `gh pr merge --admin --squash`. PR# 기록 (PR-3 §11 입력). data worktree cleanup.

---

### PR-3 (hub Phase 2 PR2 박제) — mctrader-hub worktree, land_order 3

> **PR-2 MERGED 후 진입**. hub worktree (mct-192-telemetry-emit 또는 별 mct-192-post-merge).

#### Task 6: Story §8.5 + §11 + counters COMPLETED + ADR-033 §9.1 VERIFIED + CLAUDE.md (F8/F12/F13/F14)

- [ ] **Step 1: Story MCT-192.md §8.5 Impl Manifest amend**

3 ADR quad evidence 박제:
- ADR-029: `mctrader_dual_write_result_total{status,tier}` (재사용, runner.py:285, MCT-189 triad 재인용)
- ADR-030: `mctrader_collector_ticks_total{exchange,symbol}` (재사용, collector.py:189, MCT-180/179 triad 재인용)
- ADR-031: `mctrader_data_redis_stream_publish_failures_total` (신규 emit, realtime_stream.py:147-154, MCT-192 신규 triad v1: file:line + caller grep ≥1 + integration test PASS + dead-in-data caveat)

§11 LAND timeline = PR-1/PR-2/PR-3 실 PR# + sha.

- [ ] **Step 2: counters.json MCT-192 COMPLETED + ADR-033 §9.1 sub-2 VERIFIED + CLAUDE.md §EPIC milestone 1/3 → 2/3 + EPIC-RESULTS §Story-2**

counters MCT-192 = COMPLETED + completed_at + land_prs 3 PR. ADR-033 §9.1 sub-2 = VERIFIED (PR-2 LAND confirm). CLAUDE.md §EPIC-evidence-quad-runtime-telemetry milestone 1/3 → 2/3. EPIC-RESULTS §Story-2 추가.

- [ ] **Step 3: verify (각 file Read + Grep + git status). verify report 의무.**

#### Task 7: RETRO-MCT-192 + PMO-AUDIT-MCT-192 (F9/F10) — subagent dispatch (병렬)

- [ ] **RETRO-MCT-192.md** (~180 lines) — CFP-138/ADR-045 4-field. Lesson 핵심 = **trust-but-verify 동형 재발 (PMOAgent 2nd pass R1 'ADR-033 부재' false premise — plugin-codeforge#822 self-discipline gate v1 적용에도 PMOAgent path 오류, Orchestrator 직접 ls/grep verify 가 SSOT)**. + ADR-029/030 기존 counter 재사용 (신규 emit 최소화) + ADR-031 dead-in-data 정직 박제 (R2 가공 metric 7회째 차단) + engine drop 정합.

- [ ] **PMO-AUDIT-MCT-192.md** (~250 lines) — §lane gate 전수 + cross-Story 패턴 + R1 false premise 기각 박제 + KPI 갱신 (trust-but-verify 동형: MCT-191 0회 → MCT-192 1회 PMOAgent 2nd pass 재발 / Codex deviation 0 연속 / escalation consumer reapply 누적). plugin-codeforge#822 escalation evidence row 추가 권고 (subagent path 오류 = self-report verify gate 범위 확장 후보).

#### Task PR-3-LAND: hub 박제 commit + push + PR open + admin merge + gate:retro-complete + PMO retro final dispatch (Orchestrator direct)

- [ ] Orchestrator git status verify. commit (message file) + push + PR open + admin merge. PR# §11 박제. PR-1 gate:retro-complete label. PMOAgent retro final dispatch (memory feedback_pmo_retro_mandatory).

---

## Self-Review

### Spec coverage
| spec §N | task | covered |
|---------|------|---------|
| §1 Trigger V1-V2/D3-D6/ED | Task 1 §0 | ✓ |
| §2 Q1-Q9 | Task 1 §5 + Task 2 + Task 5 | ✓ |
| §4 AC-1~5 | Task 1 §3 + Task 5 + Task 6 §1 | ✓ |
| §5 INV-1~3 | Task 5 (INV-1/2) + Task 1 §6 (INV-3 engine drop) | ✓ |
| §6 scope_manifest | Task 3 (direct carry) | ✓ |
| §7 next lane | PR-1/2/3 LAND tasks | ✓ |

14 file 전수 task assign. cross-repo 3 PR sequential.

### Placeholder scan
- "#TBD" = PR open 전 정상 (PR-LAND task 실 PR# carry)
- 다른 placeholder 없음

### Type consistency
- counter name 일관: `mctrader_dual_write_result_total` / `mctrader_collector_ticks_total` / `mctrader_data_redis_stream_publish_failures_total` (Task 2/3/5/6 정합, spec §6 SSOT)
- `dead-in-data` / `test-injected only` 일관 (Task 1/2/5/6)
- `trust-but-verify 동형 재발` 일관 (Task 1 §9 / Task 7 RETRO/PMO-AUDIT)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-17-mct-192-telemetry-emit.md`.**

Execution = **Subagent-Driven** (memory feedback_subagent_execution + feedback_autonomous_execution 정합).

**dispatch plan** (cross-repo 3 PR sequential):
- **PR-1 hub docs**: batch (Task 1 Story + Task 2 ADR-033 + Task 3 scope_manifest + Task 4 counters — file disjoint parallel) → Orchestrator PR-1 LAND
- **PR-2 data code**: data 별 worktree → Task 5 (TDD: test fail → emit → pass → triad v1 verify → 회귀 0) → Orchestrator PR-2 LAND
- **PR-3 hub 박제**: Task 6 (Story §8.5/§11/counters/ADR-033 §9.1/CLAUDE.md) + Task 7 (RETRO + PMO-AUDIT parallel) → Orchestrator PR-3 LAND + label + PMO retro

**trust-but-verify 강제**: 각 implementer verify report 의무 + **Orchestrator 모든 BLOCKER 보고 직접 ls/grep 재verify** (PMOAgent R1 false premise 재발 차단 — subagent SSOT 신뢰 금지, Orchestrator git/file 직접 확인이 SSOT).

REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`.
