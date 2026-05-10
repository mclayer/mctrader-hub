# RETRO — Data Collection Monitor 4-section dashboard (CoverageStatsWriter + Streamlit page)

**범위**: mctrader-data (CoverageStatsWriter + collector wiring) · mctrader-web (CoverageStatsAdapter + data_collection_helpers + 20_data_collection.py 4-section page) · mctrader-hub (spec + plan)
**기간**: 2026-05-09 (single calendar day, post-MCT-106 same-session)
**Trigger**: 50-symbol × 3-tier collector daemon 데이터 연속성 검증 UI 부재 → 신규 모니터 페이지 신설
**Status**: 3 repo 모두 origin/main 반영 (mctrader-data `a6ef500`, mctrader-web `27b6596`, mctrader-hub `f2dc061` 직전 spec/plan commit `862255a` + `4c31a4b`)

---

## 1. 결과 요약

### 1.1 산출물

**mctrader-data**:
- `src/mctrader_data/coverage_stats.py` — `TierStats` / `GapEvent` / `CoverageStatsWriter` (5분 atomic flush, asyncio run loop, CancelledError → final flush)
- `tests/test_coverage_stats.py` — 7 PASS (skeleton flush, atomic on fsync 실패, record_event 누적, multi-symbol 격리, record_gap, async run periodic, async run final flush)
- `src/mctrader_data/collector.py` — `CollectorDaemon._handle_event` + `MultiSymbolCollector.run()` 에 `coverage_stats_writer.record_event()` wiring + asyncio task spawn/cancel lifecycle (heartbeat_writer 미러 패턴)
- `src/mctrader_data/cli.py` — `_amain()` 에 `CoverageStatsWriter` 인스턴스화 + daemon/collector 주입

**mctrader-web**:
- `src/mctrader_web/dashboard/coverage_stats_adapter.py` — `CoverageStatsResult` + 5분 TTL 캐시 + graceful degraded
- `src/mctrader_web/dashboard/data_collection_helpers.py` — `heatmap_granularity_seconds` / `lag_color_class` / `compute_window_seconds` / `build_heatmap_matrix` (pure helpers, no Streamlit)
- `src/mctrader_web/dashboard/pages/20_data_collection.py` — 4 섹션 Streamlit 페이지 (§1 KPI 7개 / §2 노드 카드 / §3 tier 카드 + heatmap + incident table / §4 Candle/OB/Tick 탭)
- `tests/dashboard/test_coverage_stats_adapter.py` + `tests/dashboard/test_data_collection_helpers.py` — 8 + 14 PASS

**mctrader-hub**:
- `docs/superpowers/specs/2026-05-09-data-collection-monitor-design.md` — 9 섹션 설계 문서
- `docs/superpowers/plans/2026-05-09-data-collection-monitor.md` — 10 task TDD plan
- `.claude-work/` 작업 산출물 (commit history 만 잔존)

### 1.2 검증 상태

| Repo | Test 결과 | 원격 main 반영 |
|---|---|---|
| mctrader-data | `pytest tests/test_coverage_stats.py tests/test_collector.py` 전 PASS | `a6ef500` |
| mctrader-web | `pytest tests/dashboard/` 전 PASS | `27b6596` |
| mctrader-hub | (docs only, CI N/A) | `f2dc061` |

---

## 2. 잘된 점

### 2.1 Spec → Plan → TDD 단계 분리 견고성
설계(`spec`) → 구현 plan(`plan`) → task별 TDD 사이클(write failing test → run fail → implement → run pass → commit) 5-step 패턴 10 task 일관 적용. CoverageStatsWriter 의 **atomic write + fsync 실패 last-good 보존** 같은 비기능 요구도 plan Task 1 Step 1 fixture(monkeypatch `os.fsync` → OSError) 로 *코드 작성 전* 박제됨. TDD-by-spec 패턴 (RETRO-MCT-107-111 §2.1 에서 발의된 표준화 후보) 의 효과 재실증.

### 2.2 heartbeat_writer 미러 패턴 채택
신규 `CoverageStatsWriter` lifecycle (init → asyncio task spawn → CancelledError → final flush) 이 기존 `HeartbeatWriter` 와 동일 구조 차용. CollectorDaemon `_handle_event` 의 record_event 호출 위치도 heartbeat 와 같은 줄 옆에 추가 — **"신규 컴포넌트는 인접 동형 컴포넌트의 lifecycle 을 미러" 패턴**이 자연 강화. 신규 패턴 발명 0건, 기존 패턴 활용 100%.

### 2.3 Pure helper 분리로 Streamlit 미테스트 영역 축소
`data_collection_helpers.py` 가 모든 비Streamlit 계산 로직 (heatmap matrix 빌드, lag 색상 분류, window 계산) 을 분리 → 14 unit test 로 비주얼 페이지 대신 로직 검증. Streamlit 페이지 자체는 manual `streamlit run` smoke test 만 필요. **UI 와 비즈니스 로직 강제 분리 패턴** = ADR 후보군에 추가 가치 있음 (§4 참조).

### 2.4 Schema contract via JSON 으로 cross-package 타입 분리
`TierStats` / `GapEvent` 가 mctrader-data 와 mctrader-web 양쪽 *각각 정의*, `coverage_stats.v1` schema 가 SSOT. mctrader-data 가 `dataclasses.asdict()` → JSON, mctrader-web 가 JSON → 자체 dataclass 로 파싱. 두 repo 가 서로 import 하지 않음 → 패키지 결합도 0. **schema_version 필드로 진화 가능성 보존**.

### 2.5 fix(web) `step-style colorscale` 즉시 발견·교정
4-포인트 선형 보간 colorscale 이 Plotly 에서 "0=초록 / 0.34=노랑 / 0.67=빨강 / 1.0=회색" 의도와 달리 색상 번짐 → 7-포인트 step stops 로 1 commit 즉시 교정 (`11115d7`). 시각적 결함 자가 발견 → 동일 세션 내 fix → push 의 빠른 cycle. 사용자 trigger 없는 자율 정정.

---

## 3. 발견된 이슈 — 패턴 분석

### Pattern X1: 잘못된 브랜치에 작업한 이전 세션의 silent loss

**관측**:
이전 세션이 `fix/data-policy-wiring` 브랜치에 CoverageStatsWriter 초기 구현 5 commit (`1bf79eb`, `ceb1324`, `35c719d`, `4375204`, `1d3eda8`) 을 커밋. 그러나 이 브랜치는 main 에 머지되지 않은 채로, main 에는 별도 PR 로 **MCT-106 zero-loss WAL ingestion pipeline** (`306749f`) 가 직접 머지됨. WAL 도입으로 `CollectorDaemon._handle_event` 가 `_emit_to_wal` 패턴으로 리팩토링 (`663d2e3` 전후) → **`fix/data-policy-wiring` 의 CollectorDaemon wiring 코드는 새 main 의 코드와 충돌** = 머지 시도 시 conflict, 머지 없이 main 진행 시 silent stale.

본 세션은 main 의 WAL 아키텍처를 기반으로 **CoverageStatsWriter 를 재구현** — 즉 5 commit (160 lines 이상) 이 silent loss. fix/data-policy-wiring 의 작업은 history 에 잔존하나 main 에 통합되지 않음.

**근본 원인**:
1. 이전 세션이 `feat/...-coverage-stats` 같은 명시 브랜치 대신 **이미 존재하던 fix/data-policy-wiring 의 working tree 위에 작업** → 신규 작업이 기존 fix 브랜치의 untracked → committed 흐름으로 흡수.
2. main 에 진행 중인 **MCT-106 (대규모 아키텍처 변경)** 과 본 작업의 commit 토폴로지가 분리돼 있어, branching point 가 후행. `fix/data-policy-wiring` 이 main 으로부터 fork 된 시점이 MCT-106 직전이라, 머지 시 충돌 면적이 커짐.
3. Story 파일 부재 — 본 작업은 spec/plan 만 작성하고 **MCT-XXX Story 파일을 hub 에 생성하지 않음**. Story §8.5 Impl Manifest / §11 retro pointer 가 없어, 작업 진행 위치(어느 브랜치, 어느 PR) 가 SSOT 로 박제되지 않음.

**관련 선례**:
- MEMORY `feedback_parallel_session_branch_race.md` (2026-05-08) — 동일 working tree 공유 race 의 1세대 사례
- RETRO-MCT-107-111 §3 Pattern A — 2026-05-09 mctrader-engine 재발 사례
- ADR-019 — git worktree + Preflight 부트스트랩 contract (Accepted)
- MCT-118 — ADR-019 구현 Story (`scripts/agent-preflight.ps1` + `scripts/agent-worktree.ps1` 미실행, 신규 상태)

**핵심 신호**: ADR-019 가 **Accepted 됐고** MCT-118 Story 까지 만들어졌으나 **본 세션의 시작 시점에는 아직 구현되지 않음**. 즉 ADR-019 의 부트스트랩 contract 가 SSOT 로만 존재 → 본 세션도 동일 race 결로 진입할 수 있었음. 다만 본 세션은 **단일 작업자 (parallel agent 미사용)** 라서 race 자체는 발생 안 했고, **stale-branch silent loss** 라는 인접 실패 모드로 발현.

**Pattern X1 의 Pattern A(branch race) 와의 차이**:
- Pattern A: parallel agent 가 동일 working tree 공유 → 동일 시점 race
- Pattern X1: serial 세션이지만 **stale branch context → main divergence → silent rework**

→ ADR-019 만으로는 X1 차단 불충분. 추가 게이트 필요 (§4 ADR 후보 참조).

### Pattern X2: Story 파일 없는 mid-size feature 작업

**관측**:
spec(`2026-05-09-data-collection-monitor-design.md`) 과 plan(`2026-05-09-data-collection-monitor.md`) 만 작성, **MCT-XXX Story 파일은 미생성**. 영향:
- Status tracking SSOT 부재 → "어느 브랜치, 어느 PR, AC pass 여부" 가 분산
- ADR-020 (Story 완료 게이트 → PMO 회고 자동 dispatch) 의 trigger 불발 — Story 가 없으므로 "완료" phase enumeration 자체가 적용 안 됨
- §8.5 Impl Manifest 부재 → 본 회고가 git log 추적으로 manifest 재구성

**근본 원인**:
- mctrader-hub `.claude/_overlay/CLAUDE.md` 가 "spec → plan → impl" 흐름과 "Story → 요구사항 → ... → 완료" 흐름 둘을 모두 지원하나, **언제 Story 파일이 의무인지** 의 게이트가 명확하지 않음.
- 본 작업은 "data collection monitor" 라는 명시적 범위가 있고 multi-repo 변경 + 새 컴포넌트 추가라 Story 격이지만, spec/plan 작성 완료 시점에 Story 생성 step 이 자연 포함되지 않음.

### Pattern X3: file_count_today dead field

**관측**:
`TierStats.file_count_today` 가 WAL 레이어에서 항상 0 — 본 작업의 record_event 호출은 row 단위만 추적. compactor 가 향후 파일 단위 통계 채울 예정. 본 세션 commit `a6ef500` 에서 주석으로 명시.

**근본 원인**:
- 설계 시 (spec §4-1) MCT-106 WAL 리팩토링과 본 작업의 cross-cut 을 충분히 검토하지 않음. `file_size_bytes_today` 는 record_event 의 `file_size_delta` 인자로 전달 가능하나, **파일 *수* 는 record_event 시점에 알 수 없음** (compactor 출력 시점에 결정).
- spec 이 "파일 수 = 오늘 생성된 Parquet 파일 수" 라는 의미를 plan 에 그대로 인계 → 구현 단계에서야 의미 미스매치 발견.

**현재 처리**: 주석으로 dead field 표시. 차기 compactor 의 stats sink 추가 시 채울 예정.

### Pattern X4: test_run_flushes_periodically 취약 assertion

**관측**:
plan Task 3 Step 1 의 `test_run_flushes_periodically` 가 `out.exists()` 만 체크 → final flush(CancelledError handler) 도 동일 결과를 만들 수 있어 *주기적 flush* 검증이 약함. fix `a6ef500` 에서 mock 으로 flush 호출 횟수 카운트로 강화.

**근본 원인**:
- TDD plan Step 1 의 *failing test* 가 "기능이 없을 때 fail" 만 보장 — *기능이 일부만 동작할 때 fail* 까지 검증하지 않음.
- 즉 plan 의 test design 단계에서 "양성 가짜(false positive)" 판정 시나리오가 충분히 enumerate 되지 않음.

**일반화 가능성**: 다른 async loop test 도 final-flush 와 periodic-flush 를 구분하지 않으면 동일 결함 가능. 본 fix 가 패턴 자체를 박제할 가치 있음.

### Pattern X5: Plotly colorscale 4-point 선형 보간 → 색상 번짐

**관측**:
`[[0.0, "#22c55e"], [0.34, "#eab308"], [0.67, "#ef4444"], [1.0, "#94a3b8"]]` colorscale 이 Plotly 의 default 보간 알고리즘에서 인접 색상 사이 그라디언트로 렌더 → "discrete 4 카테고리(ok/warn/gap/miss)" 의도와 다름. 7-point step stops `[[0.0, c1], [0.249, c1], [0.25, c2], [0.499, c2], ...]` 로 교정.

**근본 원인**:
- spec `§3-2` 가 색상 카테고리만 정의하고 *Plotly colorscale 파라미터의 의미* 는 plan 단계에서 결정 — 시각화 라이브러리 specifics 가 spec 단계에서 누락.
- TDD 가 적용되지 않는 시각 영역 (Streamlit 페이지) 의 결함은 manual smoke test 에 의존.

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

PMO `pmo_output v1.adr_proposal` 필드 inline 반환:

### ADR-022 후보: Stale-branch silent loss 차단 — 작업 시작 게이트

```
category: Process & Governance
title: ADR-022: 작업 시작 게이트 — main 진동성 검증 + Story 파일 의무
trigger: 2026-05-09 data collection monitor 작업이 fix/data-policy-wiring (MCT-106 분기점 이전 stale)
         위에서 진행돼 5 commit silent loss + 본 세션 재구현 발생. ADR-019 (parallel agent isolation)
         만으로는 serial 세션의 stale-branch race 차단 불충분.
배경:
  - MCT-100/101/102, MCT-110 → ADR-019 (parallel race) 채택
  - 본 사례는 serial session + 기존 fix 브랜치 inherit → main divergence → 재구현
  - Story 파일 부재 = 작업 위치 SSOT 부재 = silent skip 가능
문제:
  - 작업 시작 시 base branch 검증 step 부재 (현재 main 과의 divergence 거리 미체크)
  - mid-size feature 작업이 spec/plan 만 만들고 Story 미생성 → ADR-020 trigger 불발
  - 작업 종료 후 Impl Manifest (§8.5) 가 SSOT 로 박제되지 않으면 회고가 git log 재구성에 의존
제안 결정:
  - D1 — 작업 시작 시 Preflight 게이트 확장:
      a) 현재 working dir branch = main OR `git merge-base origin/main HEAD` 가 < N commit 뒤짐 검증
      b) 검증 실패 시 신규 worktree + 신규 feat/<key>-<slug> branch 강제 생성
  - D2 — Story 파일 의무 트리거: spec OR plan 작성 시 동시에 docs/stories/<KEY>.md 생성
      a) Story §8.5 Impl Manifest 가 commit hash + 수정 파일 목록을 PR 머지 직전 박제
      b) Story §11 retro pointer 가 ADR-020 게이트 점화 조건
  - D3 — Orchestrator 가 spec/plan 파일 write queue 처리 시 짝 Story 파일 부재 검출 → 자동 생성 제안
예상 결과:
  - stale-branch silent loss 0건
  - mid-size feature 의 Story-less 작업 0건
  - ADR-020 retro 게이트 trigger 신뢰성 확보 (Story 항상 존재 보장)
```

### ADR-023 후보: UI 와 비즈니스 로직 분리 — Pure helper module 표준

```
category: Architecture
title: ADR-023: Streamlit/UI 페이지의 비즈니스 로직 강제 분리 — pure helper module
trigger: 본 세션 data_collection_helpers.py 가 14 unit test 로 검증된 반면,
         20_data_collection.py 자체는 manual smoke test 만 필요 → 분리 패턴의 효과 재실증
배경:
  - mctrader-web 의 다수 페이지가 직접 Streamlit API + 비즈니스 로직 혼재
  - 본 세션이 helpers 분리로 테스트 표면적 ~10x 확보
문제:
  - Streamlit 직접 테스트는 streamlit-testing 의존 + 느림 + 실제 UI 결함 (colorscale 같은) 검출 불가
  - 페이지 단위 회귀 시 비즈니스 로직 결함이 시각 결함으로 위장
제안 결정:
  - 모든 신규 Streamlit 페이지는 `<page>_helpers.py` (pure functions, no streamlit import) 모듈 강제
  - 페이지 자체는 sidebar UI + helper 함수 호출 + render only 로 제한
  - helpers 의 unit test coverage 70% 이상 mandatory
예상 결과:
  - UI 결함 / 로직 결함 분리 진단 가능
  - Streamlit upgrade 충격 면적 축소
  - Plotly/colorscale 같은 시각 결함은 별도 visual-regression 게이트로 분리
```

---

## 5. 개선 제안 3건 (다음 세션 반영)

1. **작업 시작 1분 게이트** — 신규 작업 진입 시 Orchestrator 가 (a) `git status` (b) `git log origin/main..HEAD --oneline` 으로 base divergence 확인, divergence ≥ 1 commit 이면 warn 후 worktree 분기 제안. ADR-022 D1 의 운영 즉시 채택 가능 부분.
2. **spec/plan 짝 Story 자동 생성 hook** — `docs/superpowers/specs/<date>-<slug>.md` write 직후 `docs/stories/MCT-XXX.md` 부재 검출 시 Orchestrator self-prompt "Story 파일 함께 생성하시겠습니까" 발화. ADR-022 D2 의 즉시 채택 부분.
3. **TDD plan test design 강화 체크리스트** — Step 1 의 failing test 가 "기능 없음" 외 "기능 부분 동작" / "주변 invariant 위반" 시나리오를 enumerate 하는지 plan template 에 명시. Pattern X4 (취약 assertion) 직접 차단.

---

## 6. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Spec 작성 (4c31a4b) | ~10% |
| Plan 작성 (862255a) | ~15% |
| mctrader-data CoverageStatsWriter 구현 (Tasks 1~4, 7458c33) | ~20% |
| mctrader-web Adapter + helpers (Tasks 5~6, d995505 + bee30eb) | ~15% |
| mctrader-web 페이지 §1~§4 (Tasks 7~10, cef5d8d~edb8384) | ~20% |
| 결함 발견·교정 (Plotly colorscale + dead field + 취약 assertion) | ~10% |
| **잘못된 브랜치 재발견 + 재구현 비용** | **~5%** |
| 회고 (이 문서) | ~5% |

→ **stale-branch silent loss** 가 명시 비용 5% — ADR-022 D1 채택 시 0% 로 감축 가능 추정.

---

## 7. 관련 ADR · MEMORY · 회고

- **ADR**:
  - ADR-009 (OHLCV 16-col schema) — coverage-stats v1 의 row_count_today 의 의미 기반
  - ADR-017 (Zero-loss ingestion WAL) — 본 세션 wiring 의 base 아키텍처
  - ADR-019 (parallel agent isolation) — Pattern X1 의 인접 패턴, X1 차단 불충분
  - ADR-020 (Story 완료 PMO 회고) — Story 파일 부재로 trigger 불발 (Pattern X2)
- **MEMORY**:
  - `feedback_parallel_session_branch_race.md` — Pattern X1 의 1세대 선례
  - `feedback_pmo_retro_mandatory.md` — 본 회고 자동 dispatch trigger
  - `feedback_admin_merge_autonomy.md` — 동일 자율 패턴 확장 후보
- **선행 회고**:
  - `RETRO-MCT-107-111-code-review-fix.md` — Pattern A/B/C/D/E 와 본 retro Pattern X1~X5 의 cross-trace 가능
  - `EPIC-RESULTS-MCT-98.md` — Dockerization Epic 종료, MCT-106 의 base 환경
- **후속 회고** (2026-05-10):
  - `RETRO-data-collection-candle-tab-fix-2026-05-10.md` — 본 RETRO 의 §3 Pattern X3 (file_count_today dead field) 의 sibling 결함 후속.
    Pattern X6 (Coverage 측정 SSOT 가 partition 레이아웃과 불일치 — coverage-stats.json 이 OHLCV cover 안 함) +
    Pattern X7 (묵시 가정의 사양 박제 — "캔들 미수집" 안내문이 결함 박제) +
    Pattern X8 (1차 fix 의 ADR 정합 검증 누락 — `node=*/` 서브디렉 미처리) 신규 발의.
    ADR-024 후보 (Coverage SSOT cover 범위 audit) origin.

---

## 8. Story §11 회고 pointer 보정 권고

본 작업은 Story 파일이 미생성되어 §11 retro pointer 박제 대상 부재. 차선 조치:
- (즉시) 본 retro 파일을 hub 의 `docs/retros/` 에 land — 완료
- (제안) 차기 Orchestrator 가 본 작업 회고용 retroactive Story 파일 (`MCT-119` 등) 생성 → §11 에 본 retro 파일 경로 link. ADR-022 D2 채택 시 자동 게이트로 전환.
- (대안) MCT-106 §11 에 본 retro 의 "WAL 아키텍처 위에서 CoverageStatsWriter 재구현 완료" pointer 추가 — 본 세션이 MCT-106 의 실질 후속 작업이므로 의미 정합.

---

**작성**: PMOAgent (Story 완료 회고 감사 + Cross-Story 패턴 분석)
**작성일**: 2026-05-09
**관련 commit**:
  - mctrader-data: `7458c33` + `a6ef500`
  - mctrader-web: `d995505` `bee30eb` `cef5d8d` `3faf0bf` `e539d49` `9c525be` `11115d7` `edb8384` `8ed0351` `27b6596`
  - mctrader-hub: `4c31a4b` (spec) `862255a` (plan)
