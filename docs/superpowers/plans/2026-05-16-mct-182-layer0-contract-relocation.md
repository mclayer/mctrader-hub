# MCT-182 — Layer 0 Contract Relocation → mctrader-market — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **codeforge consumer note:** MCT-182 is a cross-repo codeforge Story. It executes via the codeforge Story flow (1 Story = Phase 1 hub docs PR → Phase 2 cross-repo code PRs sequential LAND → Phase 2 PR2 hub 박제), through the codeforge design lane (ArchitectPLAgent Change Plan §1-§11) and implementation lane. This plan is the **brainstorm→Story bridge**: it locks scope, the Phase 0 verify gate, and the cross-repo sequencing. Per-task bite-sized TDD detail for production code is authored by the codeforge design lane within the Story flow.

**Goal:** mctrader-engine 의 `mctrader_data` 직접 의존 중 PURE-contract 부분(aggregation 알고리즘 + TickRecord/OrderbookEventRecord dataclass + paper_lineage)을 mctrader-market(Layer 0 FOUNDATION)으로 이전하고, engine 의 CandleModel import 4곳 (verified 2026-05-16, brainstorm 가설 5곳 정정)을 `mctrader_market.candle` 로 재지정한다. (EPIC-data-domain-decoupling strangler-fig 1단계.)

**Architecture:** 4-Layer 의존 모델의 Layer 0 확립. market = data 비의존 DAG 최하위. data/engine 호출부는 deprecation re-export shim 으로 무중단 전환. ADR-031 publish (Proposed).

**Tech Stack:** Python 3.11, pydantic v2, dataclasses, pytest, ruff, pyright, uv. codeforge Story flow (gh PR, cross-repo sequential LAND).

---

## Phase 0 Verify Gate (R1 — 진입 전 의무, 가설 금지)

MCT-182 코드 작업 시작 전, 아래를 **실제 코드로 재검증**한다. session/brainstorm 표현은 가설로만 수용 (docker-stack Epic Phase 0 verify gap 6회 누적 → 7회째 사전 차단).

- [ ] **V1** `git -C c:/workspace/mclayer/mctrader-data fetch origin && git -C c:/workspace/mclayer/mctrader-engine fetch origin && git -C c:/workspace/mclayer/mctrader-market fetch origin` (working tree stale 차단)
- [ ] **V2** `mctrader_data/aggregation/` 전 서브모듈 import 재확인 — `mctrader_data.*` import 0건, 의존 = `mctrader_market.{protocols.information_bar,schemas.tick,types}` + stdlib 뿐임을 grep 으로 실증 (PURE 판정 재확인). 불일치 시 STOP → ArchitectPL escalate.
- [ ] **V3** `mctrader_data/paper_lineage.py` import 재확인 — stdlib+pydantic+`mctrader_market.types` 뿐, `mctrader_data.*` 0건 (PURE 재확인).
- [ ] **V4** `TickRecord`(`tick_storage.py`) / `OrderbookEventRecord`(`orderbook_storage.py`) — dataclass 본문이 stdlib-only 임을 Read 로 재확인 (pyarrow 는 모듈 레벨, 클래스 비결합 → dataclass만 추출 가능 재확인).
- [ ] **V5** `mctrader_market.candle.CandleModel` 존재 + pydantic v2 재확인. engine `from mctrader_data.cold.duckdb_resample import CandleModel` 정확히 몇 곳인지 재grep (brainstorm = 5곳; 실수치 확정). 호출부 목록 박제.
- [ ] **V6** market `pyproject.toml` + `git grep mctrader_data` 재확인 — market→data 의존/순환 0 (relocate 안전성).
- [ ] **V7** `.codeforge/counters.json` MCT-182 + ADR-031 RESERVED 상태 확인 (이미 예약됨).

Phase 0 결과는 MCT-182 Story §0 / Change Plan Phase 0 섹션에 verified-via annotation 으로 박제. V2~V6 중 하나라도 brainstorm 가설과 불일치 시 → 설계 escalate (ArchitectPL chief author 재판정), plan 진행 보류.

---

## Cross-Repo 실행 순서 (codeforge Story flow, land_order)

```
hub Phase 1 (docs)  →  market#N  →  data#N  →  engine#N  →  hub Phase 2 PR2 (박제)
```

각 PR CI green 후 admin merge → 다음 PR (memory: admin merge autonomy). Phase 0 verify 불일치/FIX 루프는 codeforge fix-ledger-schema + root-cause-decision 경유.

---

## Task 1: hub Phase 1 — Story file + ADR-031 publish + docs

**Files (mctrader-hub):**
- Create: `docs/stories/MCT-182.md` (Story §1-§11, codeforge Story 템플릿)
- Create: `docs/adr/ADR-031-data-domain-decoupling.md` (Status: Proposed; D1-D7 본문 박제; D-row ↔ scope_manifest §design_decisions 1:1 전수 reconcile — MCT-179 lesson reapply)
- Modify: `CLAUDE.md` (## EPIC-data-domain-decoupling (4-layer) 섹션 신규 — IN_PROGRESS MCT-182)
- Reference: `scope_manifests/EPIC-data-domain-decoupling.yaml` (이미 작성됨), `.codeforge/counters.json` (MCT-182 status RESERVED→IN_PROGRESS), `docs/superpowers/specs/2026-05-16-EPIC-data-domain-decoupling-design.md`

- [ ] **Step 1: Story §0 에 Phase 0 Verify Gate 결과 박제** (위 V1~V7, verified-via annotation 의무)
- [ ] **Step 2: ADR-031 작성** — D1-D7 + Status Proposed + ADR-029/027/030 amendment 예고 box. D-row 를 scope_manifest §design_decisions 와 1:1 전수 정합 (Out-of-scope stale 사전 차단, docker-stack MCT-179 lesson)
- [ ] **Step 3: Story §1-§11 작성** — scope_manifest `story_decision_matrix.MCT-182` 기준 (cross_repo/land_order/decisions D1,D6)
- [ ] **Step 4: CLAUDE.md ## EPIC-data-domain-decoupling 섹션 신규** (4-layer 그래프 + MCT-182 IN_PROGRESS + Key References)
- [ ] **Step 5: counters.json MCT-182 status RESERVED→IN_PROGRESS, started_at 추가**
- [ ] **Step 6: hub Phase 1 PR 생성** — Issue body 에 scope_manifest 첨부. CI green 후 admin merge

> 본 Task 의 §1-§11 / ADR 본문 / Change Plan §1-§11 detail 은 codeforge 설계 lane(ArchitectPLAgent + deputy)이 Story flow 내에서 산출. 본 plan 은 scope·gate·순서 SSOT.

---

## Task 2: market#N — Layer 0 contract 신규 (aggregation + records + paper_lineage)

**Files (mctrader-market):**
- Create: `src/mctrader_market/aggregation/` (mctrader_data.aggregation PURE 패키지 이전 — core/scaled_int/contract_metadata 서브모듈 + `__init__` public API: TimeBar/Volume/Tick/DollarBarAggregator, ContractMetadata, compute_contract_id, to_scaled, from_scaled)
- Create: `src/mctrader_market/records.py` (TickRecord/OrderbookEventRecord 순수 dataclass 추출 — pyarrow 비결합)
- Create: `src/mctrader_market/paper_lineage.py` (PaperLineage/canonical_jsonl_hash 이전 — PURE)
- Verify-only: `src/mctrader_market/candle.py` (CandleModel 기존 존재 재확인, 재구현 0)
- Test: `tests/test_aggregation_relocated.py`, `tests/test_records.py`, `tests/test_paper_lineage_relocated.py`

- [ ] **Step 1 (TDD): 회귀 동등성 테스트 작성** — mctrader-data 측 기존 aggregation/paper_lineage 테스트를 market 측으로 이식. 입출력 동등(byte-for-byte: canonical_jsonl_hash, scaled int round-trip, 4 Aggregator 동작) 검증 테스트 먼저 작성, 실패 확인
- [ ] **Step 2: aggregation 패키지 물리 이전** — `mctrader_data.aggregation.core` 의 `from mctrader_market...` import 는 동일 repo 내부 참조로 단순화 (core.py 가 market 내부가 되므로). public API `__init__` 동일 유지
- [ ] **Step 3: records.py — TickRecord/OrderbookEventRecord dataclass만 추출** (pyarrow schema/Writer 는 data 잔류, dataclass 정의만 이동). `__post_init__` float-guard 보존
- [ ] **Step 4: paper_lineage.py 이전** — `mctrader_market.types.UTCDateTime` 참조는 동일 repo 내부화
- [ ] **Step 5: 테스트 통과 확인 + ruff + pyright**
- [ ] **Step 6: market#N PR — CI green 후 admin merge**

---

## Task 3: data#N — deprecation re-export shim

**Files (mctrader-data):**
- Modify: `src/mctrader_data/aggregation/__init__.py` → market-core re-export + `DeprecationWarning`
- Modify: `src/mctrader_data/paper_lineage.py` → market-core re-export + `DeprecationWarning`
- Modify: `src/mctrader_data/tick_storage.py` / `orderbook_storage.py` → `TickRecord`/`OrderbookEventRecord` 를 `from mctrader_market.records import ...` 로 재지정 (data 자체 writer 는 그대로, 타입 SSOT 만 market)
- Modify: `pyproject.toml` (mctrader-market 의존은 이미 존재 — 버전 핀 확인만)
- Test: `tests/test_shim_backcompat.py` (shim 경유 import 가 market 객체와 동일 식별성 + DeprecationWarning emit)

- [ ] **Step 1 (TDD): shim back-compat 테스트 작성** — `from mctrader_data.aggregation import TickBarAggregator` 가 `mctrader_market.aggregation.TickBarAggregator` 와 `is` 동일, `DeprecationWarning` 발생. 실패 확인
- [ ] **Step 2: aggregation/paper_lineage shim 구현** (`from mctrader_market.X import *` + `warnings.warn(DeprecationWarning)`)
- [ ] **Step 3: tick_storage/orderbook_storage TickRecord/OrderbookEventRecord import 재지정** (SSOT=market.records, data writer 로직 무변경)
- [ ] **Step 4: data full suite 회귀** — 신규 실패 0 (기존 aggregation/lineage/storage 테스트 green 유지). ruff+pyright
- [ ] **Step 5: data#N PR — CI green 후 admin merge**

---

## Task 4: engine#N — CandleModel import 4곳 (verified 2026-05-16, brainstorm 가설 5곳 정정) 재지정

**Files (mctrader-engine):**
- Modify (V5 에서 확정된 정확한 호출부): `backtest/data_source.py`, `consumers/candle_view.py`, `consumers/signal_provenance_log.py`, `paper/data_source.py` 외 V5 grep 결과 전수 — `from mctrader_data.cold.duckdb_resample import CandleModel` → `from mctrader_market.candle import CandleModel`
- Test: `tests/test_candlemodel_import_source.py` (grep-gate: engine src/ 에 `mctrader_data.*CandleModel` import 0)

- [ ] **Step 1 (TDD): import-source gate 테스트 작성** — `grep -rn "mctrader_data.*CandleModel\|from mctrader_data.cold.duckdb_resample import CandleModel" src/` == 0 을 assert. 현재 실패 확인
- [ ] **Step 2: V5 확정 호출부 전수 재지정** (재구현 0 — import 경로만. CandleModel 객체 동일)
- [ ] **Step 3: engine full suite 회귀** — CandleModel 사용처(전략·지표·consumer) 신규 실패 0. ruff+pyright
- [ ] **Step 4: import-source gate 테스트 통과 확인**
- [ ] **Step 5: engine#N PR — CI green 후 admin merge**

---

## Task 5: hub Phase 2 PR2 — 박제

**Files (mctrader-hub):**
- Modify: `docs/stories/MCT-182.md` (§10/§11/§12 결과 + cross-repo LAND timeline + AC PASS)
- Modify: `docs/adr/ADR-031-data-domain-decoupling.md` (D1 VERIFIED amendment box + LAND PR 링크)
- Modify: `scope_manifests/EPIC-data-domain-decoupling.yaml` (MCT-182 status COMPLETED, milestone 1/7)
- Modify: `.codeforge/counters.json` (MCT-182 COMPLETED + land_prs)
- Modify: `CLAUDE.md` (MCT-182 COMPLETED 박제)
- Create: `docs/retros/RETRO-MCT-182.md`
- Create: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` (§Story-1 박제, milestone 1/7)

- [ ] **Step 1: cross-repo LAND timeline 박제** (market#N → data#N → engine#N commit + 시각)
- [ ] **Step 2: ADR-031 §D1 VERIFIED amendment box**
- [ ] **Step 3: scope_manifest + counters.json + CLAUDE.md COMPLETED 갱신** (milestone 1/7)
- [ ] **Step 4: RETRO-MCT-182 + EPIC-RESULTS §Story-1 작성**
- [ ] **Step 5: hub Phase 2 PR2 — CI green 후 admin merge**
- [ ] **Step 6: PMOAgent 자동 dispatch** (memory: feedback_pmo_retro_mandatory — Story 완료 후 세션 종료 전 의무)

---

## 다음 Story 진입 (sequential gate)

MCT-182 Phase 2 PR2 MERGED 후 → **MCT-183** (Layer 2 io/ relocation) 진입. MCT-183 는 자체 Phase 0 verify(engine io/ src caller 0 = MCT-170 io/ lesson 재확인) 기반으로 자체 plan 생성 (본 plan에 미선계획 — R1 verified-not-hypothesized 의무).

## Self-Review

- **Spec coverage**: spec §5 D1(MCT-182 owner) + D6(ADR-031 publish) → Task 1(ADR/Story) + Task 2(contract relocate) + Task 3(shim) + Task 4(engine repoint) + Task 5(박제) 전 커버. D2-D5/D7 = MCT-183~188 (본 plan scope 외, 명시).
- **Placeholder scan**: production 코드 bite-step 은 codeforge 설계 lane(ArchitectPL Change Plan §1-§11)이 Story flow 내 산출 — 본 plan 은 codeforge consumer bridge plan 으로 scope/gate/순서/TDD 골격 SSOT (의도된 위임, placeholder 아님).
- **Type consistency**: aggregation public API(`TimeBar/Volume/Tick/DollarBarAggregator`, `to_scaled/from_scaled`, `ContractMetadata`) Task2↔Task3 일치. `CandleModel`/`TickRecord`/`OrderbookEventRecord`/`PaperLineage` 명칭 Task 전반 일치.
- **R1 gate**: Phase 0 Verify Gate(V1-V7) 가 모든 Task 선행 — 가설↔실상 불일치 시 escalate 명시.
