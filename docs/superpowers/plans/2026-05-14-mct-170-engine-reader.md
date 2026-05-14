---
plan_id: 2026-05-14-mct-170-engine-reader
story_key: MCT-170
spec_ref: 2026-05-14-MCT-170-engine-reader-design
phase: 4/6 (engine reader L1 확장, cross-repo phase1_phase2)
created: 2026-05-14
---

# Plan: MCT-170 — Engine reader L1 확장 + D7 NFR + D8 local fallback + dr_mode 신규

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`. memory `feedback_subagent_execution.md` 정합 (항상 subagent-driven). 본 plan checkbox 단위로 task-by-task.

**Goal:** mctrader-engine `io/` 측에 L1 tier 인지 + D7 cache NFR (95% hit / p99 <100ms) + D8 local fallback (forward-only migration window) + dr_mode 신규를 도입하여 ambiguity invariant 정합 + p99 회귀 차단.

**Architecture:** MCT-154 산출 (cold_reader / reader_cache / endpoint_router) preserve + facade pattern (TierReader = cache → NAS L1/L2/L3 → local fallback chain) + DR mode state machine (CLOSED/OPEN/HALF_OPEN) + byte-size budget enforcement.

**Tech Stack:** Python 3.11, boto3 (NAS MinIO), threading.Lock + OrderedDict (LRU), prometheus_client (NFR emit), pytest-benchmark (D7 측정).

---

## Step 0 — Prerequisite verify

- [ ] **0.1 main sync**: `git fetch origin main && git pull origin main` (mctrader-hub) — Already up to date ✓ (본 세션)
- [ ] **0.2 counters.json verify**: MCT-167/168/169 COMPLETED + MCT-170 reservation active ✓ (본 세션)
- [ ] **0.3 engine io/ verify**: `ls c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/io/` = cold_reader.py + reader_cache.py + endpoint_router.py + __init__.py (1058 lines, MCT-154 LAND) ✓
- [ ] **0.4 data NullReaderCache verify**: `c:/workspace/mclayer/mctrader-data/src/mctrader_data/compactor/reader_cache.py` = NullReaderCache + ReaderCache Protocol ✓

---

## PR#1 — mctrader-hub Phase 1 docs

**Repo**: `c:/workspace/mclayer/mctrader-hub`
**Branch**: `mct-170-phase-1` (from main)
**Files** (7 file 박제):

### Task 1.1 — Branch 생성

- [ ] **Step 1.1.1**: `git checkout -b mct-170-phase-1`
- [ ] **Step 1.1.2**: `git status` 확인 (clean working tree)

### Task 1.2 — Story file 작성

**File**: Create `docs/stories/MCT-170.md` §1-§12

- [ ] **Step 1.2.1**: frontmatter (story_scope=cross-repo, status=IN_PROGRESS, depends_on=[MCT-167, MCT-168, MCT-169], related_adrs=[ADR-029 §D8 amendment])
- [ ] **Step 1.2.2**: §1 동기 (ambiguity invariant 위반 방지 + p99 회귀 차단, MCT-154 산출 확장)
- [ ] **Step 1.2.3**: §2 Phase 0 Context (4 agent 결과 + Codex review + PMO 2nd pass 요약)
- [ ] **Step 1.2.4**: §3 10 D 결정 (D1-D10 표, spec §2 답습)
- [ ] **Step 1.2.5**: §4 산출물 매핑 (4 PR cross-repo, spec §4 답습)
- [ ] **Step 1.2.6**: §5 AC (7 AC, spec §3.3 답습)
- [ ] **Step 1.2.7**: §6 INV (INV-1 SoT exclusivity / INV-2 backward compat / INV-3 byte budget / INV-4 D7 NFR)
- [ ] **Step 1.2.8**: §7 Risk (R1 HIGH NFR / R2 MEDIUM PR race / R3 MEDIUM backward compat / R4 MEDIUM D10 exemption)
- [ ] **Step 1.2.9**: §8 Test Contract (Phase 2 PR#3 test 5종 박제)
- [ ] **Step 1.2.10**: §8.5 active state (reader_cache restart-aware, DR mode flag persistent)
- [ ] **Step 1.2.11**: §9 Phase 1 PR cycle + Phase 2 cross-repo cycle
- [ ] **Step 1.2.12**: §10 FIX Ledger (placeholder)
- [ ] **Step 1.2.13**: §11 Cross-ref (Plan + Spec + ADR-029 + scope_manifest + brainstorm prompt + EPIC-RESULTS)
- [ ] **Step 1.2.14**: §12 retro placeholder (Phase 2 PMOAgent dispatch 후 fill)

### Task 1.3 — ADR-029 §D8 amendment

**File**: Modify `docs/adr/ADR-029-tier-promotion-single-source.md`

- [ ] **Step 1.3.1**: Status Amendment Trail entry 추가 (2026-05-14 MCT-170 — §D8 sunset criterion 박제)
- [ ] **Step 1.3.2**: §D8 amendment box 삽입 — sunset criterion D6=D 박제:
  ```
  > **MCT-170 amendment (2026-05-14)** — D8 local fallback sunset criterion:
  > - 시점 cutoff: 2026-09-01 (hard sunset, MCT-172 Epic CLOSE gate)
  > - telemetry verification: local fallback hit 0건 연속 14일 → auto disable
  > - combined: cutoff OR (telemetry 0-hit AND MCT-172 close)
  > - dr_mode.UNKNOWN_TIER 상태 신규 — D10 ambiguity exemption scope (cutoff 판정 불가 legacy partition fallback 거부)
  ```
- [ ] **Step 1.3.3**: §D10 footnote 추가 — 30d exemption window + Prometheus `nas_reader_ambiguity_total` emit

### Task 1.4 — scope_manifest milestone 4/6 IN_PROGRESS

**File**: Modify `scope_manifests/EPIC-tier-promotion-single-source.yaml`

- [ ] **Step 1.4.1**: milestone 4 추가 (spec §9 YAML 답습) — status: IN_PROGRESS
- [ ] **Step 1.4.2**: 기존 milestone 3 (MCT-169) status: COMPLETED 유지 확인

### Task 1.5 — CLAUDE.md 3 section append

**File**: Modify `CLAUDE.md`

- [ ] **Step 1.5.1**: §"Engine reader L1 확장 (tier_reader facade + l1_reader + cold_reader preserve)" — MCT-170 진입 박제
- [ ] **Step 1.5.2**: §"DR mode state machine (CLOSED/OPEN/HALF_OPEN + explicit override)" — Phase 2 PR#3 박제
- [ ] **Step 1.5.3**: §"Reader cache byte budget (LRU+TTL + RSS bound)" — byte budget enforcement 박제

### Task 1.6 — counters.json retitle

**File**: Modify `.codeforge/counters.json`

- [ ] **Step 1.6.1**: MCT-170 title 변경 ("재구현" → "L1 확장 + DR mode + byte budget")
- [ ] **Step 1.6.2**: retitle_history append (rationale: "Phase 0 verify 발견 — MCT-154 LAND 3 module 존재, 신규 4 module 아닌 확장+wiring")

### Task 1.7 — Commit + Push + PR open

- [ ] **Step 1.7.1**: `git add docs/stories/MCT-170.md docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md docs/adr/ADR-029-tier-promotion-single-source.md scope_manifests/EPIC-tier-promotion-single-source.yaml CLAUDE.md .codeforge/counters.json`
- [ ] **Step 1.7.2**: Commit message:
  ```
  docs(MCT-170): Phase 1 — engine reader L1 확장 + D7 NFR + D8 fallback + dr_mode 설계 박제

  EPIC-tier-promotion-single-source Story-4. Phase 0 verify 발견 — MCT-154 LAND 3 module
  존재, 신규 4 module 아닌 확장+wiring.

  Spec §2 D1-D10 (Codex 권고 + PMO 2nd pass):
  - D1=C tier_reader facade + cold_reader L2/L3 specialized + l1_reader 신규
  - D2=C reader_cache 자체 구현 + byte-size budget enforcement
  - D3=C prometheus + pytest-benchmark hybrid 측정
  - D4=B facade orchestration (priority chain: cache → NAS → local)
  - D5=C state machine + explicit mode flag override + Prometheus
  - D6=D sunset criterion: cutoff 2026-09-01 + telemetry 0-hit 14d + MCT-172 gate
  - D7=C TTL configurable env (default ADR-029 권장 1h/24h/7d)
  - D8=C DR mode trigger: sliding window + consecutive failure hybrid
  - D9=A ColdReader 공개 API 유지 (backward compat)
  - D10=A ambiguity exemption: cutoff 이전 partition fallback + UNKNOWN_TIER 상태 신규

  ADR-029 §D8 amendment 박제 + scope_manifest milestone 4/6 IN_PROGRESS.

  prerequisite ALL LAND (2026-05-14):
  - MCT-167 (PR #305 + #306)
  - MCT-168 (PR #307 + data #59 + #308 + #309)
  - MCT-169 (PR #310 + data #60 + #311 + #312)
  ```
- [ ] **Step 1.7.3**: `git push -u origin mct-170-phase-1`
- [ ] **Step 1.7.4**: `gh pr create --title "docs(MCT-170): Phase 1 — engine reader L1 확장 설계 박제" --base main --body "..."` (body = §4 산출물 + AC 7 + INV 4 + Risk R1-R4 + prerequisite verify)

### Task 1.8 — DesignReviewPL dispatch

- [ ] **Step 1.8.1**: DesignReviewPLAgent dispatch — packet (spec + plan + ADR-029 amendment cross-ref + scope_manifest)
- [ ] **Step 1.8.2**: 검수 항목 — D1-D10 정합, ADR-029 §D8 amendment box format, scope_manifest YAML schema
- [ ] **Step 1.8.3**: FIX iter (max 3, mechanical fast-path 허용)

### Task 1.9 — CI + Admin merge

- [ ] **Step 1.9.1**: CI green 확인 (lint / link check / yaml validate)
- [ ] **Step 1.9.2**: Admin merge (memory `feedback_admin_merge_autonomy`)

---

## PR#2 — mctrader-data Phase 2 LRU 구현

**Repo**: `c:/workspace/mclayer/mctrader-data`
**Branch**: `mct-170-phase-2-data` (from main)
**Files** (1 file 변경 + 1 test 추가):

### Task 2.1 — Branch + main sync

- [ ] **Step 2.1.1**: `cd c:/workspace/mclayer/mctrader-data && git fetch origin main && git pull origin main`
- [ ] **Step 2.1.2**: `git checkout -b mct-170-phase-2-data`

### Task 2.2 — Failing test (TDD)

**File**: Create `tests/compactor/test_reader_cache_lru.py`

- [ ] **Step 2.2.1**: test_lru_cache_get_put_basic — Given LRUReaderCache(max_bytes=1024), When put(nas_key="k1", data=b"a"*100), Then get("k1") == b"a"*100
- [ ] **Step 2.2.2**: test_lru_cache_byte_eviction — Given max_bytes=200, put 3 entries (100 byte each, FIFO) → LRU eviction first
- [ ] **Step 2.2.3**: test_lru_cache_invalidate — Given put("k1", data), When invalidate("k1"), Then get("k1") is None
- [ ] **Step 2.2.4**: test_protocol_compliance — Given LRUReaderCache(), Then isinstance(cache, ReaderCache) ✓
- [ ] **Step 2.2.5**: Run: `pytest tests/compactor/test_reader_cache_lru.py -v` → Expected: FAIL (LRUReaderCache not defined)

### Task 2.3 — LRUReaderCache impl

**File**: Modify `src/mctrader_data/compactor/reader_cache.py`

- [ ] **Step 2.3.1**: NullReaderCache 제거 — `class LRUReaderCache` 신규
- [ ] **Step 2.3.2**: `__init__(max_bytes: int = 256 * 1024 * 1024)` — bytes budget
- [ ] **Step 2.3.3**: `_cache: OrderedDict[str, bytes]` + `_lock: threading.Lock` + `_current_bytes: int`
- [ ] **Step 2.3.4**: `get(nas_key) -> IO[bytes] | None` — cache hit 시 BytesIO wrap, move_to_end (LRU), miss None
- [ ] **Step 2.3.5**: `put(nas_key, data)` — bytes budget enforcement (popitem(last=False) while _current_bytes + len(data) > max_bytes)
- [ ] **Step 2.3.6**: `invalidate(nas_key)` — pop + _current_bytes 감소
- [ ] **Step 2.3.7**: `_DEFAULT_CACHE: ReaderCache = LRUReaderCache()` (NullReaderCache 자리)
- [ ] **Step 2.3.8**: Run: `pytest tests/compactor/test_reader_cache_lru.py -v` → Expected: PASS

### Task 2.4 — 기존 test green preserve

- [ ] **Step 2.4.1**: `grep -r "NullReaderCache" src/ tests/` — call site 0 verify (만약 잔존 시 LRUReaderCache import 변경)
- [ ] **Step 2.4.2**: `pytest tests/compactor/ -v` → Expected: ALL PASS (기존 test 회귀 0)

### Task 2.5 — Commit + Push + PR open

- [ ] **Step 2.5.1**: `git add src/mctrader_data/compactor/reader_cache.py tests/compactor/test_reader_cache_lru.py`
- [ ] **Step 2.5.2**: Commit message:
  ```
  feat(MCT-170): LRUReaderCache 구현 — NullReaderCache placeholder 제거

  D7=A 95% cache hit + <100ms p99 NFR 충족을 위한 LRU + byte-size budget.
  Protocol ReaderCache (get/put/invalidate) 충실.

  default _DEFAULT_CACHE = LRUReaderCache(max_bytes=256MB).
  engine 측 PR#3 (mctrader-engine) prerequisite — PR#3 진입 전 본 PR LAND 의무.

  Cross-ref: mctrader-hub PR#1 (Phase 1 docs).
  ```
- [ ] **Step 2.5.3**: `git push -u origin mct-170-phase-2-data`
- [ ] **Step 2.5.4**: `gh pr create --title "feat(MCT-170): LRUReaderCache 구현 — NullReaderCache 제거" --base main --body "..."`

### Task 2.6 — CI + Admin merge

- [ ] **Step 2.6.1**: CI green 확인 (pytest + mypy + ruff)
- [ ] **Step 2.6.2**: Admin merge

---

## PR#3 — mctrader-engine Phase 2 3 module 신규 + 1 module 확장

**Repo**: `c:/workspace/mclayer/mctrader-engine`
**Branch**: `mct-170-phase-2-engine` (from main)
**Files** (3 module new + 1 module modified + 5 test new + __init__.py modified):

**Prerequisite**: PR#1 + PR#2 MUST be merged first (data Protocol shape stable).

### Task 3.1 — Branch + main sync + prerequisite verify

- [ ] **Step 3.1.1**: `cd c:/workspace/mclayer/mctrader-engine && git fetch origin main && git pull origin main`
- [ ] **Step 3.1.2**: `git checkout -b mct-170-phase-2-engine`
- [ ] **Step 3.1.3**: 의존 verify — mctrader-data LAND 후 LRUReaderCache 사용 가능 확인

### Task 3.2 — reader_cache.py byte budget 확장 (TDD)

**File**: Modify `src/mctrader_engine/io/reader_cache.py`

- [ ] **Step 3.2.1**: Create `tests/io/test_reader_cache_budget.py` failing tests:
  - test_byte_budget_init — `ReaderCache(max_bytes=1024)` ok
  - test_byte_budget_eviction — put 3 entries 500B each, max_bytes=1024 → 1st evicted (LRU)
  - test_byte_budget_metric — `cache.current_bytes()` 정확
- [ ] **Step 3.2.2**: Run failing tests → FAIL (max_bytes param 부재)
- [ ] **Step 3.2.3**: `ReaderCache.__init__` 에 `max_bytes: int | None = None` 추가
- [ ] **Step 3.2.4**: put() 측 byte budget enforcement (max_bytes != None 시 OrderedDict.popitem(last=False) 반복 while _current_bytes + len(value) > max_bytes)
- [ ] **Step 3.2.5**: `current_bytes() -> int` method 추가
- [ ] **Step 3.2.6**: Run tests → PASS
- [ ] **Step 3.2.7**: 기존 MCT-154 test 회귀 0 verify — `pytest tests/io/test_reader_cache.py -v` ALL PASS

### Task 3.3 — l1_reader.py 신규 (TDD)

**File**: Create `src/mctrader_engine/io/l1_reader.py`

- [ ] **Step 3.3.1**: Create `tests/io/test_l1_reader.py` failing tests:
  - test_l1_read_prefix — `L1Reader.read(symbol="BTC", date="20260514", hour=14)` → NAS key = `tier=L1/symbol=BTC/date=20260514/hour=14/...parquet`
  - test_l1_read_etag_verify — NAS HEAD ETag 조회 후 cache invalidation
  - test_l1_read_not_found — 404 → ReadResult(status="not_found")
- [ ] **Step 3.3.2**: Run failing tests → FAIL
- [ ] **Step 3.3.3**: `class L1Reader` 구현 — endpoint_router (MCT-154) + reader_cache 통합 + L1 prefix 생성
- [ ] **Step 3.3.4**: ReadResult.status enum 활용 (hit_cache / hit_nas / not_found / nas_unreachable) — cold_reader 5종 답습
- [ ] **Step 3.3.5**: Run tests → PASS

### Task 3.4 — dr_mode.py 신규 (TDD)

**File**: Create `src/mctrader_engine/io/dr_mode.py`

- [ ] **Step 3.4.1**: Create `tests/io/test_dr_mode.py` failing tests:
  - test_state_machine_closed_to_open — 5 consecutive failure → OPEN 전이
  - test_state_machine_sliding_window — 60s 내 5xx 5회 → OPEN
  - test_state_machine_half_open_probe — OPEN 30s 후 → HALF_OPEN, probe success → CLOSED
  - test_manual_override — `set_mode("OPEN", reason="operator")` → state 강제 + override flag True
  - test_prometheus_emit — state 전이 시 `nas_reader_dr_state` metric emit
  - test_unknown_tier_state — D10 ambiguity exemption — `set_mode("UNKNOWN_TIER")` 진입 시 local fallback 거부
- [ ] **Step 3.4.2**: Run failing tests → FAIL
- [ ] **Step 3.4.3**: `class DRMode` 구현 — Literal["CLOSED", "OPEN", "HALF_OPEN", "UNKNOWN_TIER"] state + sliding window deque + consecutive failure counter + manual override flag + prometheus_client Counter/Gauge
- [ ] **Step 3.4.4**: `record_success()` / `record_failure(status_code, latency_ms)` / `current_state()` / `set_mode(state, reason)` API
- [ ] **Step 3.4.5**: Sliding window: deque(maxlen=N), append (timestamp, success_bool, latency_ms) — recent 60s 내 5xx count 또는 p99 >500ms 임계 검사
- [ ] **Step 3.4.6**: Consecutive failure: counter, 5회 연속 fail → OPEN
- [ ] **Step 3.4.7**: HALF_OPEN: OPEN 진입 30s 후 자동 전이, probe 1회 success → CLOSED
- [ ] **Step 3.4.8**: Run tests → PASS

### Task 3.5 — tier_reader.py 신규 (TDD)

**File**: Create `src/mctrader_engine/io/tier_reader.py`

- [ ] **Step 3.5.1**: Create `tests/io/test_tier_reader.py` failing tests:
  - test_priority_cache_hit — Given cache populated, When read() → hit_cache (NAS GET 0)
  - test_priority_nas_l1 — Given cache miss + L1 NAS object 존재, Then NAS GET → hit_nas
  - test_priority_nas_l2_l3 — Given L1 miss + L2 hit, Then cold_reader 위임 → hit_nas
  - test_local_fallback — Given NAS unreachable (dr_mode=OPEN) + cutoff 이전 partition local 존재, Then local Path read → ReadResult(status="local_fallback", is_legacy=True)
  - test_local_fallback_rejected_post_cutoff — Given cutoff 이후 partition + NAS unreachable, Then fallback 거부 → nas_unreachable
  - test_unknown_tier_fallback_rejected — Given dr_mode.UNKNOWN_TIER (D10 exemption) + NAS unreachable, Then fallback 거부 + ambiguity metric emit
  - test_backward_compat_cold_reader — Given TierReader(cold_reader=mock), Then cold_reader.read() 호출 정확 (MCT-154 API preserve)
- [ ] **Step 3.5.2**: Run failing tests → FAIL
- [ ] **Step 3.5.3**: `class TierReader` 구현 — DI (cold_reader: ColdReader, l1_reader: L1Reader, reader_cache: ReaderCache, dr_mode: DRMode, endpoint_router: EndpointRouter, local_path_base: Path, cutoff_timestamp: datetime)
- [ ] **Step 3.5.4**: `read(partition_path) -> ReadResult` — priority chain:
  1. reader_cache.get(key) → hit_cache 시 즉시 return
  2. dr_mode.current_state() != CLOSED 시 NAS GET skip → local fallback 분기
  3. tier 판정 (partition path 분석) → tier=L1 면 l1_reader.read(), tier=L2/L3 면 cold_reader.read()
  4. NAS GET success → reader_cache.put + return hit_nas
  5. NAS GET fail → dr_mode.record_failure(status, latency) → local fallback (cutoff 이전 partition only) → ReadResult(status="local_fallback")
  6. cutoff 이후 partition + NAS fail → ReadResult(status="nas_unreachable")
- [ ] **Step 3.5.5**: ReadResult status enum 확장 — "local_fallback" 추가 (cold_reader 5종 + 1종 = 6종)
- [ ] **Step 3.5.6**: cutoff_timestamp env config — `READER_LOCAL_FALLBACK_CUTOFF=2026-09-01T00:00:00Z` (env override 가능, D7=C)
- [ ] **Step 3.5.7**: Run tests → PASS

### Task 3.6 — test_reader_perf.py NFR 측정 (D7=A)

**File**: Create `tests/io/test_reader_perf.py`

- [ ] **Step 3.6.1**: pytest-benchmark fixture — 10k random partition read (50% hot + 50% cold)
- [ ] **Step 3.6.2**: test_d7_cache_hit_ratio — 10k read sample → hit_ratio >= 0.95 assertion
- [ ] **Step 3.6.3**: test_d7_p99_latency — benchmark stats.stats.p99 < 0.1s (100ms) assertion
- [ ] **Step 3.6.4**: Run: `pytest tests/io/test_reader_perf.py -v --benchmark-only`
- [ ] **Step 3.6.5**: 미달 시 FIX Ledger 박제 + cache budget +50% iter (max 3 iter)

### Task 3.7 — __init__.py 갱신

**File**: Modify `src/mctrader_engine/io/__init__.py`

- [ ] **Step 3.7.1**: TierReader / L1Reader / DRMode export 추가
- [ ] **Step 3.7.2**: docstring 갱신 — MCT-170 Phase 2 산출 박제

### Task 3.8 — Integration test (cross-module)

- [ ] **Step 3.8.1**: `pytest tests/io/ -v` ALL PASS
- [ ] **Step 3.8.2**: 기존 MCT-154 test 회귀 0 — `pytest tests/io/test_cold_reader.py tests/io/test_reader_cache.py tests/io/test_endpoint_router.py -v` ALL PASS

### Task 3.9 — Commit + Push + PR open

- [ ] **Step 3.9.1**: `git add src/mctrader_engine/io/*.py tests/io/test_*.py`
- [ ] **Step 3.9.2**: Commit message:
  ```
  feat(MCT-170): engine reader L1 확장 + D7 NFR + D8 fallback + dr_mode 신규

  EPIC-tier-promotion-single-source Story-4. MCT-154 산출물 (cold_reader / reader_cache /
  endpoint_router) preserve + 확장.

  신규 module 3종:
  - tier_reader.py: facade orchestration (priority chain: cache → NAS → local)
  - l1_reader.py: L1 tier specialized read (prefix tier=L1/)
  - dr_mode.py: state machine (CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER) + Prometheus emit

  확장 module 1종:
  - reader_cache.py: byte-size budget enforcement (max_bytes 추가, MCT-154 API preserve)

  Test 5종 신규:
  - test_tier_reader.py (priority chain + local fallback + backward compat)
  - test_l1_reader.py (L1 prefix + ETag verify)
  - test_reader_cache_budget.py (byte LRU eviction)
  - test_dr_mode.py (state machine + manual override + Prometheus)
  - test_reader_perf.py (D7 NFR 95% hit + p99 <100ms, pytest-benchmark)

  Cross-ref: mctrader-hub PR#1 (docs) + mctrader-data PR#2 (LRUReaderCache).
  ```
- [ ] **Step 3.9.3**: `git push -u origin mct-170-phase-2-engine`
- [ ] **Step 3.9.4**: `gh pr create --title "feat(MCT-170): engine reader L1 확장 + DR mode 신규" --base main --body "..."`

### Task 3.10 — DesignReview + CodeReview + SecurityTest dispatch

- [ ] **Step 3.10.1**: 4 review lane 병렬 dispatch (ArchitectPL design / DevPL impl / CodeReviewPL / SecurityTestPL)
- [ ] **Step 3.10.2**: FIX iter (max 3, mechanical fast-path)

### Task 3.11 — CI + Admin merge

- [ ] **Step 3.11.1**: CI green (pytest + mypy + ruff + benchmark gate)
- [ ] **Step 3.11.2**: Admin merge

---

## PR#4 — mctrader-hub Phase 2 박제

**Repo**: `c:/workspace/mclayer/mctrader-hub`
**Branch**: `mct-170-phase-2-hub` (from main)

**Prerequisite**: PR#3 MUST be merged first.

### Task 4.1 — Branch + main sync

- [ ] **Step 4.1.1**: `cd c:/workspace/mclayer/mctrader-hub && git fetch origin main && git pull origin main`
- [ ] **Step 4.1.2**: `git checkout -b mct-170-phase-2-hub`

### Task 4.2 — PMOAgent dispatch + RETRO author

- [ ] **Step 4.2.1**: PMOAgent dispatch — `docs/retros/RETRO-MCT-170.md` author 의무
- [ ] **Step 4.2.2**: RETRO 내용:
  - Phase 0 verify 발견 박제 (재구현 → 확장+wiring)
  - 4 PR cross-repo 진행 결과 (hub-P1 / data-P2 / engine-P2 / hub-P2)
  - D7 NFR 실측 결과 (cache hit ratio + p99)
  - dr_mode state machine 검증 결과
  - R1-R4 위험 해소 결과
  - cross-Story 패턴 (MCT-148 T2 baseline cross-ref, MCT-154 산출 preserve, MCT-169 NullReaderCache → LRUReaderCache 교체)
  - 후속 Story 권고 (MCT-171 DR runbook 본문)

### Task 4.3 — Story §11 retro_file + §12 측정 결과

**File**: Modify `docs/stories/MCT-170.md`

- [ ] **Step 4.3.1**: §11 retro_file: `docs/retros/RETRO-MCT-170.md` cross-ref
- [ ] **Step 4.3.2**: §12 측정 결과 박제 (D7 hit ratio %, p99 ms, dr_mode 검증, AC-1~AC-7 PASS 확인)

### Task 4.4 — scope_manifest milestone 4/6 COMPLETED

**File**: Modify `scope_manifests/EPIC-tier-promotion-single-source.yaml`

- [ ] **Step 4.4.1**: milestone 4 status: IN_PROGRESS → COMPLETED
- [ ] **Step 4.4.2**: completion_date: 2026-05-14 (또는 실 LAND 날짜)
- [ ] **Step 4.4.3**: ac_pass: AC-1 ~ AC-7 (verified result)

### Task 4.5 — CLAUDE.md 측정 결과 박제

**File**: Modify `CLAUDE.md`

- [ ] **Step 4.5.1**: §"Engine reader L1 확장" 섹션 update — D7 hit ratio + p99 실측 박제
- [ ] **Step 4.5.2**: §"DR mode state machine" 섹션 update — state machine 검증 결과 박제

### Task 4.6 — EPIC-RESULTS Story-4 추가

**File**: Modify `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`

- [ ] **Step 4.6.1**: Story-4 (MCT-170) 결과 추가 — milestone 4/6 박제

### Task 4.7 — counters.json reservation DELETE

**File**: Modify `.codeforge/counters.json`

- [ ] **Step 4.7.1**: MCT-170 reservation 삭제 (LAND 박제)

### Task 4.8 — Commit + Push + PR open

- [ ] **Step 4.8.1**: `git add docs/retros/RETRO-MCT-170.md docs/stories/MCT-170.md scope_manifests/EPIC-tier-promotion-single-source.yaml CLAUDE.md docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md .codeforge/counters.json`
- [ ] **Step 4.8.2**: Commit message:
  ```
  docs(MCT-170): Phase 2 박제 — RETRO + milestone 4/6 COMPLETED + 측정 결과

  EPIC-tier-promotion-single-source Story-4 LAND.

  D7 NFR 측정 결과: [hit_ratio %] cache hit + [p99 ms] p99 latency.
  dr_mode state machine 검증: CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER 전이 확인.

  AC-1 ~ AC-7 ALL PASS verified.

  scope_manifest milestone 4/6 COMPLETED.
  ```
- [ ] **Step 4.8.3**: `git push -u origin mct-170-phase-2-hub`
- [ ] **Step 4.8.4**: `gh pr create --title "docs(MCT-170): Phase 2 박제 — milestone 4/6 COMPLETED" --base main --body "..."`

### Task 4.9 — CI + Admin merge

- [ ] **Step 4.9.1**: CI green
- [ ] **Step 4.9.2**: Admin merge

---

## Step 5 — 다음 Story 권고

**MCT-171 (DR runbook 본문 + invariant 8종 + 4 layer capacity)** — 별 세션 권고.

- prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md` paste
- prerequisite: MCT-170 LAND 확인 후 진입
- scope: DR runbook 5 fail mode 본문 + invariant 8종 enforcement + 4 layer capacity 정책

---

## Self-Review (spec coverage)

- ✓ Spec §1 amendment (재구현 → 확장+wiring) — Task 1.2/1.6/4.5 박제
- ✓ Spec §2 D1-D10 — Task 1.2.4 + 1.3 + Task 3.5/3.4/3.2 impl
- ✓ Spec §3 Phase 0 Context — Task 1.2.3
- ✓ Spec §4 4 PR 산출물 매핑 — Task 1/2/3/4 1:1
- ✓ Spec §5 후속 Story chain (MCT-171) — Step 5
- ✓ Spec §6 prerequisite verify — Task 0
- ✓ Spec §8 위험 R1-R4 — Task 3.6 NFR 측정 (R1) / Task 2 + 3 sequential (R2) / Task 3.2 backward compat (R3) / Task 3.4 UNKNOWN_TIER (R4)
- ✓ Spec §9 scope_manifest YAML — Task 1.4 박제
- ✓ AC-1 ~ AC-7 — Task 3.5/3.6/3.4/3.2/3.4/3.8/2.4 박제

**Type consistency**: ReadResult 6종 status enum 일관 (hit_cache/hit_nas/legacy_node_default/not_found/nas_unreachable/local_fallback). DRMode state 4종 일관 (CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER).

**Placeholder scan**: 측정 결과 % / ms 는 Task 3.6 실측 후 fill, 본 plan 의도된 ("실 LAND 날짜" 등 dynamic placeholder).

---

## Execution mode

memory `feedback_subagent_execution.md` + `feedback_autonomous_execution.md` 정합 → **Subagent-Driven** (skill `superpowers:subagent-driven-development` 답습). 사용자 확인 없이 자율 진행.
