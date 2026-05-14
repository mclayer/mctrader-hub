---
spec_id: 2026-05-14-MCT-170-engine-reader-design
story_key: MCT-170
epic_key: EPIC-tier-promotion-single-source
phase: 4/6 (engine reader L1 확장 + DR mode + reader cache byte budget)
phase_pair: phase1_phase2
created: 2026-05-14
brainstorm_session: 2026-05-14 (별 세션, MCT-170-session-prompt.md 답습)
phase0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
codex_review: 2026-05-14 (10 design decisions D1-D10 일괄 권고)
pmo_2nd_pass: 2026-05-14 (단일 Story 유지 + 4 PR sequential + R1-R4 재평가)
pre_lookup_evidence:
  - "git show origin/main:docs/adr/ADR-029-tier-promotion-single-source.md (D7/D8/D10 박제 verify)"
  - "ls c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/io/ (3 module MCT-154 LAND verify)"
  - "Read c:/workspace/mclayer/mctrader-data/src/mctrader_data/compactor/reader_cache.py (NullReaderCache Protocol verify)"
  - "Read .codeforge/counters.json MCT-170 reservation (title + phase_pair + repo)"
---

# Spec: MCT-170 — Engine reader L1 확장 + DR mode + reader cache byte budget

## §1 Spec 개요

EPIC-tier-promotion-single-source Story-4. ADR-029 D7+D8+D10 박제분 답습 + cross-repo (mctrader-engine + mctrader-data + mctrader-hub) 4 PR sequential.

**중대 amendment** (Phase 0 verify 발견):

session prompt 가 "engine reader 재구현 — 4 module 신규" 라고 명시했으나 verified-via `ls c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/io/` 결과:
- cold_reader.py (319 lines, MCT-154 LAND) — L2/L3 specialized
- reader_cache.py (269 lines, MCT-154 LAND) — LRU+TTL 자체 구현
- endpoint_router.py (442 lines, MCT-154 LAND) — env-based + atomic flip

→ MCT-170 = **확장 + wiring** (재구현 아님):
- L1 tier 인지 추가 (tier_reader facade 신규 + l1_reader specialized 신규)
- D7 NFR 측정 추가 (95% hit + p99 <100ms)
- D8 local fallback path 신규 (cold_reader 는 NAS-only)
- dr_mode.py 신규 (state machine + explicit mode flag override)
- reader_cache.py byte-size budget enforcement 추가
- cold_reader.py + endpoint_router.py = **수정 0** (backward compat preserve, D9=A)

## §2 핵심 결정 (D1-D10, Codex 권고 + PMO 2nd pass)

| D | 결정 영역 | Option | 근거 (압축) |
|---|---|---|---|
| D1 | L1 tier 인지 add 방식 | **C** | tier_reader.py facade 신규 + cold_reader L2/L3 specialized 유지 + l1_reader.py L1 specialized 신규 (separate concerns) |
| D2 | reader_cache 라이브러리 | **C** | 자체 구현 OrderedDict+Lock 유지 + byte-size getsizeof budget enforcement 추가 (RSS 회귀 차단) |
| D3 | D7 측정 방식 | **C** | hybrid — prometheus metric emit (production telemetry) + pytest-benchmark CI smoke (CI gate) |
| D4 | D8 local fallback 통합 위치 | **B** | tier_reader (facade) 측 fallback orchestration (priority chain: cache → NAS → local) |
| D5 | dr_mode.py 책임 | **C** | hybrid — state machine (CLOSED/OPEN/HALF_OPEN) + explicit mode flag operator override + Prometheus emit |
| D6 | D8 sunset criterion | **D** | hybrid — cutoff timestamp (2026-09-01 후보) + telemetry 0-hit 14d + MCT-172 Epic CLOSE gate (ADR-029 §D8 amendment 박제 의무) |
| D7 | per-tier TTL finalize | **C** | configurable env (`READER_CACHE_TTL_L1=3600` default), default = ADR-029 권장 (1h/24h/7d) |
| D8 | DR mode trigger threshold | **C** | hybrid — sliding window (60s 내 5xx 5회 또는 p99 >500ms 3회) + consecutive failure (5회 연속 → OPEN) |
| D9 | backward compat | **A** | ColdReader 공개 API 유지 + TierReader 신규 wrapper (deprecation warning ColdReader X, 그대로 caller 진입 허용) |
| D10 | ambiguity invariant exemption | **A** | cutoff timestamp 이전 partition 만 local fallback allow (D8/D10 정합) + cutoff 판정 불가 legacy = fallback 거부 + dr_mode.UNKNOWN_TIER 상태 신규 + Prometheus `nas_reader_ambiguity_total` emit |

본문 박제 = `docs/adr/ADR-029-tier-promotion-single-source.md §D8 amendment` + Story `MCT-170.md §2 핵심 결정`.

## §3 Phase 0 Context 박제

### 3.1 DomainAgent

- ADR-029 D7 권장 TTL: 1h L1 / 24h L2 / 7d L3 (MCT-170 impl 시 finalize 의무) → D7=C configurable env 채택
- D10 ambiguity invariant (MCT-169 LAND): NAS+local 동시 존재 = violation → reader INV-1 SoT exclusivity (XOR) 전제
- cache invalidation = NAS HEAD ETag/VersionId verify pattern (MCT-169 promotion.py 답습)
- sha256 SSOT caller-side (MCT-163 INV-3), multipart ETag ≠ sha256 → reader 측 cache invalidation 시 NAS Metadata sha256 활용
- DR mode = MCT-152 NASUnreachableSOPRunner primitive 답습 + dr_mode.py 신규 (ADR-027 §D9 line 455 명시)

**중요 사실 정정**: DomainAgent 가 "mctrader_engine/io/ 부재" 보고했으나 Claude 직접 verify 결과 3 module MCT-154 LAND. spec 작성 시 정정 반영.

### 3.2 ResearcherAgent

- LRU byte-budget 필수 (entry-count 폭발 위험) → D2=C 자체 구현 + getsizeof 추가
- cache coherence: NAS object version (MCT-161 versioning) + If-None-Match ETag conditional GET 가 TTL-fixed 보다 staleness window 0
- circuit breaker state machine 권고 → D5=C, D8=C hybrid (sliding window 60s + recovery 30s)
- D8 sunset criterion ADR-029 §D8 명시 누락 → MCT-170 박제 의무 → D6=D 채택

### 3.3 RequirementsAnalystAgent

**WHY 추출**: ambiguity invariant 위반 방지 + p99 회귀 차단 + D8 migration window 추적.

**명시된 요구 ↔ 실제 필요 불일치**: 사용자 "4 module 신규" 명시했으나 실제 필요는 "기존 3 module L1 확장 + DR mode 신규 + byte budget + ambiguity exemption scope 박제" 4 component → spec §1 amendment 반영.

**AC 6종** (Story §2 본문 박제):
- AC-1: tier_reader priority chain (cache → NAS L1/L2/L3 → local fallback) 단위테스트 PASS
- AC-2: D7 NFR — 95% cache hit + p99 <100ms (10k read benchmark)
- AC-3: D8 local fallback — NAS endpoint 차단 시 dr_mode=OPEN + local path 응답
- AC-4: reader_cache byte budget — RSS delta ≤ 256 MB (10k entry 100 KB avg)
- AC-5: dr_mode state machine — CLOSED→OPEN→HALF_OPEN→CLOSED 전이 + manual override + Prometheus emit
- AC-6: cold_reader backward compat — MCT-154 기존 test 100% PASS preserve
- AC-7: data reader_cache LRU — NullReaderCache 호출지 0건 (grep verify)

**Edge case 3종**: NAS partial outage + cache miss / cache poisoning during migration / migration window boundary race.

### 3.4 PMOAgent (1st + 2nd pass)

- 1 Story 단일 진행 (분할 비권장 — tier_reader facade + dr_mode + reader_cache 가 vertical slice)
- 4 PR sequential: hub-Phase1 docs → data-Phase2 LRU 구현 → engine-Phase2 3 module → hub-Phase2 박제
- 위험 재평가: R1 HIGH (D7 NFR 측정) / R2 MEDIUM (3-repo PR race) / R3 MEDIUM (backward compat) / R4 NEW MEDIUM (D10 ambiguity exemption scope, dr_mode.UNKNOWN_TIER 신규)

## §4 산출물 매핑 (cross-repo 4 PR)

### PR#1 mctrader-hub Phase 1 docs (진입점)

1. `docs/stories/MCT-170.md` §1-§12 신규
2. `docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md` (본 file)
3. `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md` 신규
4. `docs/adr/ADR-029-tier-promotion-single-source.md` §D8 amendment (sunset criterion 박제 D6=D)
5. `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 3/6 → 4/6 IN_PROGRESS
6. `CLAUDE.md` §engine reader L1 확장 + §DR mode + §reader cache byte budget (3 section append)
7. `.codeforge/counters.json` MCT-170 title 확장 + retitle_history (재구현 → L1 확장+wiring)

### PR#2 mctrader-data Phase 2 LRU 구현

1. `src/mctrader_data/compactor/reader_cache.py` 갱신 — NullReaderCache 제거 + LRUReaderCache 구현 (Protocol get/put/invalidate 충실, byte budget)
2. 기존 test green preserve

### PR#3 mctrader-engine Phase 2 신규 3 module + 확장 1 module

1. `src/mctrader_engine/io/tier_reader.py` 신규 — facade orchestration (D1=C, D4=B)
2. `src/mctrader_engine/io/l1_reader.py` 신규 — L1 specialized read (prefix `tier=L1/`)
3. `src/mctrader_engine/io/dr_mode.py` 신규 — state machine + explicit mode flag + Prometheus (D5=C, D8=C)
4. `src/mctrader_engine/io/reader_cache.py` 갱신 — byte-size budget enforcement 추가 (D2=C)
5. `tests/io/test_tier_reader.py` 신규 — priority chain
6. `tests/io/test_l1_reader.py` 신규 — L1 prefix read + ETag verify
7. `tests/io/test_reader_cache_budget.py` 신규 — byte-size LRU eviction + RSS budget
8. `tests/io/test_dr_mode.py` 신규 — state machine 전이 + manual override
9. `tests/io/test_reader_perf.py` 신규 — pytest-benchmark D7 NFR (95% hit + p99 <100ms)
10. `src/mctrader_engine/io/__init__.py` 갱신 — TierReader / L1Reader / DRMode export

### PR#4 mctrader-hub Phase 2 박제 (RETRO + milestone COMPLETED)

1. `docs/retros/RETRO-MCT-170.md` 신규 (PMOAgent dispatch)
2. `docs/stories/MCT-170.md` §11 retro_file + §12 측정 결과 박제
3. `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 4/6 COMPLETED
4. `CLAUDE.md` §engine reader 측정 결과 박제 (D7 hit ratio + p99 실측)
5. `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` Story-4 결과 추가
6. `.codeforge/counters.json` MCT-170 reservation DELETE

## §5 후속 Story chain

- **MCT-171** (DR runbook 본문 + invariant 8종 + 4 layer capacity) — 본 Story LAND 후 진입 (scope_manifest 명시 parallel_with_171 이나 hub docs/runbook 충돌 회피 위해 sequential 권고)
- **MCT-172** (Epic CLOSED, D9+D10 verify + D8 sunset finalize)

## §6 prerequisite verify (2026-05-14 본 세션)

- MCT-167 LAND 확인 (PR #305 + #306) ✓
- MCT-168 LAND 확인 (PR #307 + data #59 + #308 + #309) ✓
- MCT-169 LAND 확인 (PR #310 + data #60 + #311 + #312) ✓
- MCT-170 reservation active in counters.json ✓
- mctrader-engine io/ 3 module verify (MCT-154 LAND, 1058 lines) ✓
- mctrader-data NullReaderCache placeholder verify ✓
- 모든 prerequisite 충족 → 진입 허용

## §7 Cross-ref

- Story file: `docs/stories/MCT-170.md`
- Plan: `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`
- ADR-029 §D8 amendment: `docs/adr/ADR-029-tier-promotion-single-source.md`
- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- brainstorm prompt: `docs/superpowers/prompts/MCT-170-session-prompt.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`

## §8 위험 (R1-R4)

| ID | 위험 | 등급 | 완화 |
|----|------|------|------|
| **R1** | D7 NFR 측정 미달 (95% hit / p99 <100ms) | **HIGH** | tests/io/test_reader_perf.py pytest-benchmark CI gate + 미달 시 cache budget +50% 자동 escalate 후 재측정 (Story 내 max 3 iter, FIX Ledger 박제) |
| **R2** | Cross-repo 3 PR sequential race (data Protocol → engine import) | **MEDIUM** | PR#2 admin merge 후 PR#3 진입 강제. 사용자 admin merge autonomy (MEMORY) 활용 |
| **R3** | cold_reader backward compat preservation (MCT-154 test 100%) | **MEDIUM** | tier_reader facade 가 cold_reader 호출 wrapping → 기존 caller path 무변경. CI gate = MCT-154 test 전수 green |
| **R4 NEW** | Ambiguity invariant exemption scope (D10=A) — legacy L2/L3 object 중 manifest 없는 record 의 tier 판정 불가 | **MEDIUM** | dr_mode.UNKNOWN_TIER 상태 신규 + local fallback 자동 진입 + Prometheus `nas_reader_ambiguity_total` emit. ADR-029 §D10 footnote 박제 (exemption window 30d) |

## §9 scope_manifest 초안 (Phase 1 PR 박제용)

```yaml
- id: 4
  story: MCT-170
  title: "Engine reader L1 확장 + DR mode + reader cache byte budget (D7+D8 박제)"
  status: IN_PROGRESS
  phase_pair: phase1_phase2
  prerequisite_milestones: [2, 3]  # MCT-168 + MCT-169 LAND
  planned_adrs:
    - file: docs/adr/ADR-029-tier-promotion-single-source.md
      change_type: amendment
      section: "§D8 sunset criterion + D6=D dr_mode state machine 박제"
      decisions_referenced: [D5, D6, D7, D8, D10]
  planned_files:
    mctrader-engine:
      new:
        - src/mctrader_engine/io/tier_reader.py
        - src/mctrader_engine/io/l1_reader.py
        - src/mctrader_engine/io/dr_mode.py
        - tests/io/test_tier_reader.py
        - tests/io/test_l1_reader.py
        - tests/io/test_reader_cache_budget.py
        - tests/io/test_dr_mode.py
        - tests/io/test_reader_perf.py
      modified:
        - src/mctrader_engine/io/reader_cache.py  # byte-size LRU budget 추가
        - src/mctrader_engine/io/__init__.py       # TierReader / L1Reader / DRMode export
      preserved:
        - src/mctrader_engine/io/cold_reader.py    # backward compat (D9=A)
        - src/mctrader_engine/io/endpoint_router.py # MCT-154 산출 유지
    mctrader-data:
      modified:
        - src/mctrader_data/compactor/reader_cache.py  # NullReaderCache → LRUReaderCache
    mctrader-hub:
      new:
        - docs/stories/MCT-170.md
        - docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md
        - docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md
        - docs/retros/RETRO-MCT-170.md
      modified:
        - docs/adr/ADR-029-tier-promotion-single-source.md
        - scope_manifests/EPIC-tier-promotion-single-source.yaml
        - CLAUDE.md
        - .codeforge/counters.json
  planned_claude_md_sections:
    - "§Engine reader L1 확장 (tier_reader facade + l1_reader + cold_reader preserve)"
    - "§DR mode state machine (CLOSED/OPEN/HALF_OPEN + explicit override)"
    - "§Reader cache byte budget (LRU+TTL + RSS bound)"
  acceptance_criteria:
    AC-1: "tier_reader priority chain (cache → NAS L1/L2/L3 → local fallback) 단위테스트 PASS"
    AC-2: "D7 NFR 측정 — 95% cache hit + p99 <100ms (10k read benchmark)"
    AC-3: "D8 local fallback — NAS endpoint 차단 시 dr_mode=OPEN + local path 응답"
    AC-4: "reader_cache byte budget — RSS delta ≤ 256 MB (10k entry 100 KB avg)"
    AC-5: "dr_mode state machine — CLOSED→OPEN→HALF_OPEN→CLOSED 전이 + manual override + Prometheus emit"
    AC-6: "cold_reader backward compat — MCT-154 기존 test 100% PASS preserve"
    AC-7: "data reader_cache LRU — NullReaderCache 호출지 0건 (grep verify)"
```

## §10 본 spec 완성 후 다음 step

`superpowers:writing-plans` skill 호출 → plan file 작성 (`docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`).
