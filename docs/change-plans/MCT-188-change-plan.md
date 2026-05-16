# Change Plan — MCT-188 data-free done-criterion verify (grep0 quad gate) + Epic POLICY_FINALIZED 박제

- **Story**: MCT-188
- **Status**: design-review-ready
- **Story file**: [`docs/stories/MCT-188.md`](../stories/MCT-188.md)
- **ADR**: [ADR-031](../adr/ADR-031-data-domain-decoupling.md) §D7 VERIFIED + Status POLICY_FINALIZED (본 Story owner) · [ADR-029](../adr/ADR-029-tier-promotion-single-source.md) §D2 amend confirm · [ADR-027](../adr/ADR-027-cold-tier-object-storage-nas-minio.md) §D9 amend confirm · [ADR-030](../adr/ADR-030-docker-stack-governance.md) §compose amend confirm
- **Target repo**: `mctrader-hub` (Phase 1 docs + Phase 2 PR2) + `mctrader-engine` (Phase 2 PR1 code)
- **Epic**: EPIC-data-domain-decoupling — sequential_phase 7 (strangler-fig finalize, **Epic final**)

## 1. 입력 요약 (Story §1 verbatim, immutable)

> "data 영역은 mctrader와 아예 분리하고 싶다. 표준 mctrader에는 호출용 interface, data에는 그를
> 처리하는 REST API가 있는게 좋겠다. 프로젝트 구조는 mctrader-hub에서도 구현할 수 있고
> mctrader-data 단독으로도 필요사항을 반영할 수 있어야겠다."

EPIC-data-domain-decoupling Story-7 (Epic final). 본 Story = strangler-fig **finalize** —
D7 quad gate (engine src/pyproject 잔존 4건 제거 + CI gate 박제) + ADR-031 POLICY_FINALIZED
+ 3 ADR amend confirm. **MCT-187 COMPLETED (2026-05-17) — Gate 3 이미 PASS (MCT-186 LAND
bithumb 5곳 5파일 src 제거 완료). Gate 1/2/4 = 본 Story 구현 대상.**

## 2. 현재 구조 (CodebaseMapperAgent 산출 — verified-via git grep, origin/main HEAD 2026-05-17)

### 2.1 Gate 1 잔존 4곳 상세 (Phase 0 V1 실증)

| # | 파일 | 라인 | import 구문 | cutover 타겟 |
|---|------|------|-------------|-------------|
| G1-1 | `executor/tick_replay.py` | 28 | `from mctrader_data.orderbook_storage import OrderbookEventRecord` | `from mctrader_market.records import OrderbookEventRecord` |
| G1-2 | `executor/tick_replay.py` | 29 | `from mctrader_data.tick_storage import TickRecord` | `from mctrader_market.records import TickRecord` (G1-1과 1-line 병합 가능) |
| G1-3 | `hot/state_machine.py` | 33 | `from mctrader_data.aggregation import (DollarBarAggregator, TickBarAggregator, TimeBarAggregator, VolumeBarAggregator, from_scaled, to_scaled,)` | `from mctrader_market.aggregation import (...)` (동일 심볼) |
| G1-4 | `strategy/templates/tick_scalping.py` | 76 | `from mctrader_data.tick_storage import TickRecord  # local import to avoid cycle in lint` | `from mctrader_market.records import TickRecord` (function-local 유지) |

### 2.2 Gate 2 + Gate 4 잔존 (Phase 0 V2/V4 실증)

| Gate | pyproject.toml 라인 | 처리 |
|------|---------------------|------|
| Gate 2 | line 11: `"mctrader-data @ git+https://github.com/mclayer/mctrader-data.git@main"` | **제거** |
| Gate 4 | line 12: `"mctrader-market-bithumb @ git+https://github.com/mclayer/mctrader-market-bithumb.git@main"` | **제거** |

### 2.3 cutover byte-equivalence 근거 (Phase 0 V5~V10 실증)

- `mctrader_market.records` — `TickRecord`/`OrderbookEventRecord` 실존 (MCT-182 LAND, records.py verified)
- `mctrader_market.aggregation` — `DollarBarAggregator`/`TickBarAggregator`/`TimeBarAggregator`/`VolumeBarAggregator`/`from_scaled`/`to_scaled` 실존 (MCT-182 LAND, aggregation/ verified)
- `mctrader_data.aggregation.__init__` = market re-export shim + DeprecationWarning (MCT-182 LAND). 직독 = shim 1-step 차감, 동일 객체 (MCT-182 INV-4 is-동일성 보존)
- `mctrader_data.tick_storage.TickRecord` = MCT-182 shim re-export from `mctrader_market.records`. 직독 = 동일 class object
- 결론: **byte-equivalence 자명** — semantic 무변경, runtime 동작 동일

### 2.4 변경 영향 지도

| 영향 자산 | 영향 종류 | 비고 |
|----------|----------|------|
| `tick_replay.py:28-29` | import 2줄 재지정 (1줄로 병합 가능) | `OrderbookEventRecord`/`TickRecord` → market.records 직독 |
| `state_machine.py:33-38` | import 블록(6심볼) 재지정 | `mctrader_data.aggregation` → `mctrader_market.aggregation` |
| `tick_scalping.py:76` | import 1줄 재지정 (function-local 유지) | `mctrader_data.tick_storage.TickRecord` → `mctrader_market.records.TickRecord` |
| `pyproject.toml` | 2 의존 line 제거 | Gate 2 (mctrader-data) + Gate 4 (mctrader-market-bithumb) |
| `data-free-grep0.yml` | 신규 CI workflow | 4 gate 영구 강제 (hub 소유) |
| engine shim (`mctrader_data.aggregation.__init__` 등) | **무변경** | MCT-188 D7까지 보존 (MCT-182 §4.2 정합) — 본 Story = engine 측 경로 재지정만 |

## 3. 도입할 설계

### 3.1 cutover 범위 확정 (RefactorAgent 산출)

```
mctrader-engine (Phase 2 PR1):
  src/mctrader_engine/executor/tick_replay.py
    line 28-29: 2줄 → 1줄 병합
      - from mctrader_data.orderbook_storage import OrderbookEventRecord   [삭제]
      - from mctrader_data.tick_storage import TickRecord                  [삭제]
      + from mctrader_market.records import OrderbookEventRecord, TickRecord [신규]

  src/mctrader_engine/hot/state_machine.py
    line 33-38: 블록 재지정
      - from mctrader_data.aggregation import (                            [삭제]
      -     DollarBarAggregator, TickBarAggregator,
      -     TimeBarAggregator, VolumeBarAggregator,
      -     from_scaled, to_scaled,
      - )
      + from mctrader_market.aggregation import (                          [신규]
      +     DollarBarAggregator, TickBarAggregator,
      +     TimeBarAggregator, VolumeBarAggregator,
      +     from_scaled, to_scaled,
      + )

  src/mctrader_engine/strategy/templates/tick_scalping.py
    line 76 (function-local): 재지정
      - from mctrader_data.tick_storage import TickRecord  # local import…  [삭제]
      + from mctrader_market.records import TickRecord  # local import…      [신규]

  pyproject.toml:
    - "mctrader-data @ git+..."       [line 11 제거, Gate 2]
    - "mctrader-market-bithumb @ git+..." [line 12 제거, Gate 4]
    uv.lock 재생성 의무 (uv lock)

mctrader-hub (Phase 1 docs PR):
  docs/stories/MCT-188.md — 본 Story (신규)
  docs/change-plans/MCT-188-change-plan.md — 본 Change Plan (신규)
  .github/workflows/data-free-grep0.yml — D7 quad gate CI (신규)
  docs/adr/ADR-031-data-domain-decoupling.md — §D7 draft box (Phase 1), POLICY_FINALIZED (Phase 2 PR2)
  docs/adr/ADR-029-tier-promotion-single-source.md — §D2 amend confirm box
  docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md — §D9 amend confirm box
  docs/adr/ADR-030-docker-stack-governance.md — §compose amend confirm box
  scope_manifests/EPIC-data-domain-decoupling.yaml — MCT-188 IN_PROGRESS (Phase 1) → COMPLETED (Phase 2 PR2)
  .codeforge/counters.json — MCT-188 started_at (Phase 1) → COMPLETED (Phase 2 PR2)
  CLAUDE.md — §EPIC-data-domain-decoupling POLICY_FINALIZED 섹션
  docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md — 신규 (Phase 2 PR2)
  docs/retros/RETRO-MCT-188.md — PMO 회고 (Phase 2 PR2)
```

### 3.2 data-free-grep0.yml CI workflow 명세 (AC-5 carrier)

```yaml
name: Data-Free Grep0 Quad Gate (ADR-031 §D7)
on:
  pull_request:
  push:
    branches: [main]

jobs:
  quad-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Clone mctrader-engine
        env:
          GH_TOKEN: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
        run: gh repo clone mclayer/mctrader-engine engine

      - name: Gate 1 — engine src no mctrader_data import
        run: |
          if grep -rnE "^(from|import) mctrader_data" engine/src --include="*.py"; then
            echo "GATE 1 FAIL: engine src/ contains mctrader_data imports"
            exit 1
          fi
          echo "Gate 1 PASS: engine src/ mctrader_data import == 0"

      - name: Gate 2 — engine pyproject no mctrader-data dep
        run: |
          if grep -E "mctrader-data" engine/pyproject.toml; then
            echo "GATE 2 FAIL: engine pyproject.toml contains mctrader-data dependency"
            exit 1
          fi
          echo "Gate 2 PASS: engine pyproject mctrader-data == 0"

      - name: Gate 3 — engine src no mctrader_market_bithumb|upbit import
        run: |
          if grep -rnE "^(from|import) mctrader_market_(bithumb|upbit)" engine/src --include="*.py"; then
            echo "GATE 3 FAIL: engine src/ contains mctrader_market_bithumb/upbit imports"
            exit 1
          fi
          echo "Gate 3 PASS: engine src/ mctrader_market_bithumb|upbit import == 0"

      - name: Gate 4 — engine pyproject no exchange adapter dep
        run: |
          if grep -E "mctrader-market-(bithumb|upbit)" engine/pyproject.toml; then
            echo "GATE 4 FAIL: engine pyproject.toml contains exchange adapter dependency"
            exit 1
          fi
          echo "Gate 4 PASS: engine pyproject adapter dep == 0"
```

### 3.3 state_machine.py docstring 처리 규칙

`hot/state_machine.py` docstring line 5/17/89/50 = `mctrader_data.aggregation` 텍스트 참조 (comment/docstring — grep pattern `^(from|import)` 에 걸리지 않음). **변경 불필요** — Gate 1 pattern = `^(from|import) mctrader_data` start-of-line 한정. docstring 내 텍스트 참조는 gate 적용 외. 단 line 33 실 import 구문만 재지정.

### 3.4 uv.lock 재생성 의무

pyproject.toml 2 의존 제거 후 `uv lock` 실행 → `uv.lock` commit 포함. engine 기존 test suite
의존 (mctrader_data test fixture 등) 영향 여부 = Phase 2 PR1 전 검증 의무.

### 3.5 pyproject.toml 제거 순서

1. `mctrader-data` 의존 제거 (line 11)
2. `mctrader-market-bithumb` 의존 제거 (line 12)
3. `uv lock` 재생성
4. `uv run pytest` 로컬 검증 (또는 CI 위임)

의존 제거 전 src/ import 교체 선행 의무 (import 교체 → pyproject 제거 순서 — 역순 불가).

### 3.6 설계 Self-Discipline 3중 적용 (plugin-codeforge-design#44 + #795/#804/#805 OPEN)

#### §3.6.1 gate v2 — cross-document SSOT 동기화 (MCT-182~187 계승)

**gate v2 glob-scope + 변형포괄 + self-verify 3-check (MCT-183 RESET path 박제)**:

**TEST1** (SSOT 후보 도출): 본 Change Plan §3/§5/§6 핵심 수치·심볼 목록 작성:
- Gate 1 cutover 4곳: `tick_replay.py:28-29`(G1-1/2), `state_machine.py:33`(G1-3), `tick_scalping.py:76`(G1-4)
- Gate 2 제거: pyproject `mctrader-data` line 11
- Gate 4 제거: pyproject `mctrader-market-bithumb` line 12
- CI workflow: `.github/workflows/data-free-grep0.yml` 4 gate
- ADR-031 Status: Accepted → POLICY_FINALIZED (MCT-188 owner)
- D7 option_chosen: `ci-grep0-quad-gate`
- ADR amend confirm 3건: ADR-029 §D2 / ADR-027 §D9 / ADR-030 §compose

**TEST2** (비교 대상 SSOT 열거): Story §4 DELTA ↔ scope_manifest `§story_decision_matrix.MCT-188`
+ `§design_decisions.D7` ↔ ADR-031 §D7 VERIFIED box ↔ ADR-031 Status ↔ counters.json ADR-031
↔ EPIC-RESULTS ↔ CLAUDE.md POLICY_FINALIZED 섹션

**TEST3** (불일치 해소): Phase 1 PR commit 전 TEST1 수치 ↔ TEST2 전수 1:1 대조. 불일치 발견 시
해당 파일 동반 수정 후 커밋.

**self-verify 체크리스트** (Phase 1 PR merge 전):
- [ ] Story §4 DELTA ↔ Change Plan §3.1 일치 (파일/라인 수치)
- [ ] scope_manifest `§story_decision_matrix.MCT-188` ↔ Story §4/§5 일치
- [ ] scope_manifest `§design_decisions.D7` option_chosen = `ci-grep0-quad-gate` 유지
- [ ] ADR-031 Status = POLICY_FINALIZED (Phase 2 PR2 시점)
- [ ] counters.json ADR-031 status = POLICY_FINALIZED (Phase 2 PR2 시점)
- [ ] CLAUDE.md §EPIC-data-domain-decoupling POLICY_FINALIZED 섹션 갱신

#### §3.6.2 박제 PR 5 체크리스트

Phase 2 PR2 (박제 PR) commit 전:
1. [ ] AC-1~7 전수 PASS 확인 (grep0 4 gate + CI workflow + ADR-031 POLICY_FINALIZED + EPIC-RESULTS)
2. [ ] INV-1~4 전수 PASS (CI gate green + pyproject 의존 제거 확인 + §3.6.1 reconcile + engine 회귀 0)
3. [ ] §8.5 Impl Manifest 매핑표 완성 (파일 단위 — DeveloperPL CFP-39 self-write)
4. [ ] EPIC-RESULTS-EPIC-data-domain-decoupling.md POLICY_FINALIZED 섹션 전수 박제
5. [ ] CLAUDE.md MCT-188 COMPLETED + EPIC-data-domain-decoupling POLICY_FINALIZED 갱신

#### §3.6.3 Codex post-LAND 4 axis audit (MCT-188 LAND 후)

1. Gate 1 grep0 재확인: `grep -rn "from mctrader_data\|import mctrader_data" engine/src/` = 0건
2. Gate 2 grep0 재확인: `grep "mctrader-data" engine/pyproject.toml` = 0건
3. Gate 3 grep0 재확인 (MCT-186 LAND 유지): `grep -rn "^(from|import) mctrader_market_(bithumb|upbit)" engine/src/` = 0건
4. Gate 4 grep0 재확인: `grep "mctrader-market-(bithumb|upbit)" engine/pyproject.toml` = 0건

## 4. 파일별 변경 명세

### 4.1 engine (Phase 2 PR1, mct-188-phase2-engine-data-free branch)

| 파일 | 변경 유형 | 구체 내용 |
|------|----------|----------|
| `src/mctrader_engine/executor/tick_replay.py` | EDIT | line 28-29: 2줄 → 1줄 병합 (`from mctrader_market.records import OrderbookEventRecord, TickRecord`). MCT-185 comment (line 24) 유지 (Gate 1 pattern 비적용 — comment line) |
| `src/mctrader_engine/hot/state_machine.py` | EDIT | line 33-38: `from mctrader_data.aggregation import (...)` → `from mctrader_market.aggregation import (...)` (6 심볼 동일) |
| `src/mctrader_engine/strategy/templates/tick_scalping.py` | EDIT | line 76: `from mctrader_data.tick_storage import TickRecord` → `from mctrader_market.records import TickRecord` (comment `# local import...` 유지) |
| `pyproject.toml` | EDIT | line 11 `mctrader-data` 의존 제거 + line 12 `mctrader-market-bithumb` 의존 제거 |
| `uv.lock` | REGEN | `uv lock` 재생성 commit |

### 4.2 hub (Phase 1 docs PR, mct-188-phase1-data-free-finalize branch)

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `docs/stories/MCT-188.md` | CREATE | 본 Story |
| `docs/change-plans/MCT-188-change-plan.md` | CREATE | 본 Change Plan |
| `.github/workflows/data-free-grep0.yml` | CREATE | D7 quad gate CI (§3.2 명세) |
| `docs/adr/ADR-031-data-domain-decoupling.md` | AMEND | §D7 draft amendment box (Phase 1) |
| `docs/adr/ADR-029-tier-promotion-single-source.md` | AMEND | §D2 amend confirm box (engine NAS 직독 폐기 완결 확인) |
| `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` | AMEND | §D9 amend confirm box (io reader 6 module relocated 완결 확인) |
| `docs/adr/ADR-030-docker-stack-governance.md` | AMEND | §compose amend confirm box (engine NAS cred drop carry over 완결 확인) |
| `scope_manifests/EPIC-data-domain-decoupling.yaml` | UPDATE | MCT-188 IN_PROGRESS + story_sequence MCT-188 status update |
| `.codeforge/counters.json` | UPDATE | MCT-188 started_at |
| `CLAUDE.md` | UPDATE | §EPIC-data-domain-decoupling POLICY_FINALIZED 섹션 초안 |

### 4.3 hub (Phase 2 PR2 박제, mct-188-phase2-pr2-bagje branch)

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `docs/stories/MCT-188.md` | UPDATE | §8.5 Impl Manifest + §9/§10/§11/§12 완성 + frontmatter status=COMPLETED |
| `docs/adr/ADR-031-data-domain-decoupling.md` | UPDATE | §D7 VERIFIED amendment box 확정 + Status POLICY_FINALIZED |
| `scope_manifests/EPIC-data-domain-decoupling.yaml` | UPDATE | milestone 7/7 + MCT-188 COMPLETED + epic_status POLICY_FINALIZED |
| `.codeforge/counters.json` | UPDATE | MCT-188 COMPLETED + ADR-031 status=POLICY_FINALIZED |
| `CLAUDE.md` | UPDATE | MCT-188 COMPLETED + Epic POLICY_FINALIZED 최종 박제 |
| `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` | CREATE | Epic 전체 POLICY_FINALIZED 박제 |
| `docs/retros/RETRO-MCT-188.md` | CREATE | PMO 회고 |

## 5. 인터페이스 / 계약 변경 명세

**외부 계약 변경 없음** — 본 Story = engine 내부 import 경로 재지정 + pyproject 의존 제거.
- `mctrader_market.records.TickRecord` / `OrderbookEventRecord` = MCT-182 LAND 기존 공개 API (변경 0)
- `mctrader_market.aggregation.*` = MCT-182 LAND 기존 공개 API (변경 0)
- engine public API (Strategy callback, AC, INV 등) = 무변경 (cutover 내부 구현 detail만)

## 6. 테스트 전략

### §8.1 Test Contract (QADeveloperAgent 전담)

> **QADeveloperAgent 범위 — 본 Change Plan은 설계 명세만 기록**

| TC | 유형 | 내용 | 담당 |
|----|------|------|------|
| TC-1 | CI workflow | `.github/workflows/data-free-grep0.yml` — 4 gate 모두 green (hub CI) | CI auto |
| TC-2 | grep0 post-cutover | `grep -rn "from mctrader_data\|import mctrader_data" engine/src/` = 0건 (Gate 1 AC-1) | CI gate |
| TC-3 | pyproject verify | `grep "mctrader-data" engine/pyproject.toml` = 0건 (Gate 2 AC-2) | CI gate |
| TC-4 | Gate 3 유지 | `grep -rn "^(from\|import) mctrader_market_(bithumb\|upbit)" engine/src/` = 0건 (AC-3) | CI gate |
| TC-5 | pyproject verify | `grep "mctrader-market-(bithumb\|upbit)" engine/pyproject.toml` = 0건 (Gate 4 AC-4) | CI gate |
| TC-6 | engine full suite | `uv run pytest` — 신규 실패 0 (INV-4 byte-equiv 확인) | CI auto |

**Perf Baseline**: N/A — import 경로 재지정 only (runtime 성능 무변경)

## 7. 위험 분석 및 완화

| 위험 | 심각도 | 완화 |
|------|--------|------|
| pyproject 제거 후 engine test suite 의존 파손 | MEDIUM | import 재지정 선행 → uv lock → pytest 순서 강제 (§3.5). mctrader_data test fixture 의존 확인 필요 |
| state_machine.py docstring 내 `mctrader_data.aggregation` 참조 → Gate 1 false alarm | LOW | Gate 1 pattern = `^(from\|import)` start-of-line 한정 → docstring 비적용 (§3.3 확인) |
| uv.lock 재생성 실패 | LOW | `uv lock` 명령 실행 + CI 검증 |
| cross-document SSOT drift (MCT-182~187 7회 재현) | HIGH | §3.6.1 gate v2 self-verify 3-check + §3.6.2 박제 PR 5 체크리스트 의무 |

## 8. 변경 계획 (land_order 의존성)

```
Phase 1 (hub docs PR):
  branch: mct-188-phase1-data-free-finalize (이미 존재)
  content: Story + Change Plan + data-free-grep0.yml + ADR 3종 amend confirm + scope_manifest + counters + CLAUDE.md
  CI: hub CI green
  → admin merge

Phase 2 PR1 (engine code PR):
  branch: mct-188-phase2-engine-data-free (신규)
  land_order: 1 (단일 PR — engine repo)
  content: 4곳 cutover + pyproject 2 제거 + uv.lock 재생성
  CI: engine CI green (pytest all pass)
  → admin merge

Phase 2 PR2 (hub 박제):
  branch: mct-188-phase2-pr2-bagje (신규)
  content: Story §8.5~§12 완성 + ADR-031 POLICY_FINALIZED + scope_manifest 7/7 + counters COMPLETED + CLAUDE.md POLICY_FINALIZED + EPIC-RESULTS + RETRO
  CI: hub CI green
  → admin merge
```

**순서 의존**: Phase 1 → Phase 2 PR1 (engine LAND 후 grep0 confirm) → Phase 2 PR2 (박제)

## 9. 사전 조건 / 완료 기준

**사전 조건**: MCT-187 Phase 2 PR2 MERGED ✓ (6/7 milestone COMPLETED)

**완료 기준**:
- AC-1~7 전수 PASS
- INV-1~4 전수 PASS
- engine Phase 2 PR1 MERGED (grep0 4 gate 충족)
- hub Phase 2 PR2 MERGED (Epic POLICY_FINALIZED 박제)
- ADR-031 Status = POLICY_FINALIZED
- scope_manifest milestone = 7/7

## 10. §10 FIX Ledger (Orchestrator §10 append 독점)

| iter | lane | severity | finding | origin | fix | status |
|------|------|----------|---------|--------|-----|--------|
| (없음) | — | — | — | — | — | — |

## 11. Land timeline (Phase 2 PR2 박제 후 갱신)

> Phase 2 PR LAND 후 DeveloperPL 갱신

## 12. §3.6.1 gate v2 reconcile 완료 확인 (Change Plan 자기 검증)

| 항목 | 본 Change Plan §3.1 | scope_manifest SSOT | reconcile |
|------|---------------------|---------------------|-----------|
| D7 option_chosen | `ci-grep0-quad-gate` | `§design_decisions.D7.option_chosen: ci-grep0-quad-gate` | ✅ 1:1 |
| D7 owner_story | MCT-188 | `§design_decisions.D7.owner_story: MCT-188` | ✅ 1:1 |
| MCT-188 decisions | [D7, D6] | `§story_decision_matrix.MCT-188.decisions: [D7, D6]` | ✅ 1:1 |
| Gate 1 cutover | 4곳 (tick_replay:28-29, state_machine:33, tick_scalping:76) | Phase 0 V1 실증 정합 | ✅ 1:1 |
| Gate 2 제거 | pyproject line 11 mctrader-data | Phase 0 V2 실증 정합 | ✅ 1:1 |
| Gate 4 제거 | pyproject line 12 mctrader-market-bithumb | Phase 0 V4 실증 정합 | ✅ 1:1 |
| ADR-031 Status | Accepted → POLICY_FINALIZED (MCT-188 owner) | counters.json ADR-031 finalized_by_story=MCT-188 | ✅ 1:1 |
| ADR amend confirm | ADR-029 §D2 / ADR-027 §D9 / ADR-030 §compose | scope_manifest §planned_adrs.amendments 3건 | ✅ 1:1 |
