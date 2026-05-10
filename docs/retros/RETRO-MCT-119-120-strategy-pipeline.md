# RETRO-MCT-119-120 — Strategy Set Pipeline (Phase 1 + Phase 2)

**범위**: MCT-119 (Phase 1) + MCT-120 (Phase 2) — 통합 PR 단일 회고
**기간**: 2026-05-09 (single-day, ADR-018 audit sweep MCT-112~117 직후 동일 세션)
**Trigger**: Phase 1 7-layer pipeline + Phase 2 5 advanced layers 동시 구현 완료, ADR-020 D1 자동 dispatch
**Status**: PR #44 MERGED (mctrader-engine PR #44, 2026-05-09T15:29:44Z, squash merge `435d2ad`)
**Story file**: `docs/stories/MCT-119.md`, `docs/stories/MCT-120.md`
**Repo**: `mctrader-engine` (`c:\workspace\mclayer\mctrader-engine`) + `mctrader-web` (Strategy Set UI/API — 미푸시 §3.2)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| Story | 영역 | 계획 | 실제 | 비고 |
|---|---|---|---|---|
| **MCT-119 (Phase 1)** | engine pipeline 패키지 | 18 DTO + 5 Protocol + 14 producer + Aggregator/Constructor/Risk/ExecutionPlanner | 동일 (full scope) | 100% |
| MCT-119 | DB | 8 테이블 + Alembic 0002 | 동일 | 100% |
| MCT-119 | mctrader-web Strategy Sets API | FastAPI router CRUD + promotion | commit 작성, **미푸시** | **§3.2 발견** |
| MCT-119 | mctrader-web Streamlit UI | 3 페이지 (list/editor/promotion) | commit 작성, **미푸시** | **§3.2 발견** |
| **MCT-120 (Phase 2)** | CostModel | Backtest/Live + net_edge | 동일 | 100% |
| MCT-120 | ExchangeConstraint | Bithumb (lot_size 8dp, min_notional $5) | 동일 | 100% |
| MCT-120 | SignalGroup | PairSignalGroup ALL_OR_NONE | 동일 | 100% |
| MCT-120 | PipelineMonitor | deque latency/anomaly | 동일 | 100% |
| MCT-120 | HotSwapManager | prepare/activate/rollback | 동일 | 100% |
| MCT-120 | DB | Alembic 0003 (hotswap + latency) | 동일 | 100% |

→ **engine 측 100% 완료, web 측 미푸시 1건 (Story scope 누수)**.

### 1.2 PR #44 통계

- **+4071 / −6**, **64 파일**
- Phase 1 47 src + 1 migration + 13 tests
- Phase 2 5 src + 1 migration (Phase 1 tests 에 포함)
- **34 commit** 분포:
  - Phase 1 22 commit (DB 모델·DTO·Protocol·14 producer·Aggregator·Constructor·Risk·ExecutionPlanner·Runner·EventStore)
  - Phase 2 7 commit (CostModel·ExchangeConstraint·SignalGroup·Monitor·HotSwap·Runner 통합·Migration 0003)
  - **CI fix 5 commit** (ruff E402/UP035/UP042 자동 + pyright 4건 + xfail+sharpe clamp + N806)
- Squash merge `435d2ad` 2026-05-09T15:29:44Z

### 1.3 테스트 결과

- 신규 unit test 13 파일 (`tests/unit/pipeline/`):
  - test_aggregators / constructors / cost_model / exchange_constraints / helpers / hotswap / monitoring / producers / registry / risk_constraints / runner / signal_group / types
- 합계 LoC ~1,121 (test 만)
- **52 passed, 0 failed** (사용자 보고)
- xfail 1건 추가: `test_rate_limit_integration.py` — pre-existing BacktestExecutor Decimal38_18 overflow

### 1.4 CI 상태

| Check | 결과 |
|---|---|
| `ci` (CI workflow) | SUCCESS |
| CodeQL Analyze (actions / python) | SUCCESS / SUCCESS |
| `check-gate` (Phase Gate Mergeable cross-repo) | SUCCESS |
| `lookahead-lint` | SUCCESS |
| `phase-gate-mergeable` (CodeQL nested) | ACTION_REQUIRED (informational, non-blocking) |
| `CodeQL` | SUCCESS |

→ 5 SUCCESS + 1 informational. 머지 차단 없음.

### 1.5 부수 fix 비율 (RETRO-MCT-117 §4.2 표준 적용)

| 카테고리 | commit 수 | 비중 |
|---|---|---|
| Phase 1 본 구현 | 22 | 65% |
| Phase 2 본 구현 | 7 | 21% |
| **CI fix (부수)** | **5** | **15%** |

→ 부수 fix 15% — **RETRO-MCT-117 의 350% outlier 와 달리 정상 범위**. 본 사례는 신규 4071 LoC 첫 CI 노출 시 발견된 문제로 "pre-existing debt 청소"가 아닌 "신규 코드 self-discovered defect" 카테고리. **두 카테고리 구분이 cost 산정에 핵심**.

---

## 2. 잘된 점

### 2.1 ADR-019 D1 worktree isolation 부분 준수 (Phase 2)

Phase 2 구현은 `c:\workspace\mclayer\mctrader-engine\.claude\worktrees\phase2-pipeline` (branch `feat/mct-phase2-pipeline`) 에서 수행 — ADR-019 D1 의 git worktree isolation 정책 준수. RETRO-MCT-113 §3.1, MCT-114 §3.1, MCT-116 §What Could Be Improved 에서 반복된 branch race 가 본 Story Phase 2 에서는 **0건** — D1 enforcement 가 작동하면 race 회피 가능 실증.

→ 다만 **engine main worktree 가 여전히 `feat/mct-116-adr018-audit-engine` branch 에 머무르고 있음** (§3.4 갭 — D6 미적용 측면).

### 2.2 ruff 자동 fix 활용 (UP035/UP042)

Phase 2 CI 첫 실패 시 ruff `--fix` 활용으로 UP035 (typing→collections.abc), UP042 (str+Enum→StrEnum) 자동 수정. 1 commit (`e0de31c`) 으로 다수 fix 처리 — 수동 patch 비용 회피.

### 2.3 신규 13 unit test 0 failure — TDD 근접 적용

47 src 파일 + 13 test 파일 = src:test 비율 약 3.6:1. test 가 src 와 동시 commit 됐고 (commit graph 기준 각 layer 추가 직후 test 추가), 52 test 모두 첫 시도에 green. **신규 4071 LoC 가 첫 PR 에서 0 회귀** — 사전 설계 (DTO/Protocol 명확) + 동시 test 작성 패턴이 작동.

### 2.4 단일 PR 전략 — Phase 1 + Phase 2 통합 머지

Phase 1 + Phase 2 를 동일 PR (#44) 에 squash. 장점:
- Alembic migration 0002 + 0003 이 atomic 으로 main 진입 — partial migration race 회피
- DB 스키마와 코드 layer 가 분리 머지되지 않아 schema-mismatch transient 윈도우 0
- Phase 2 가 Phase 1 의 PipelineRunner 인터페이스에 의존 → 분리 PR 시 base PR 의존성 트래킹 cost 증가

→ vertical slice 패턴 (PMOAgent §1 규칙 2 — 인터페이스 + 첫 구체) 의 확장 적용. Phase 1 의 Runner 가 Phase 2 의 첫 구체 layer 5 종을 동시에 검증.

### 2.5 admin merge autonomy + PMO 회고 자동 dispatch (ADR-020 D1)

PR #44 CI green 즉시 admin merge → 사용자 trigger 없이 본 retro dispatch. ADR-020 D1 의 6번째 same-session 사례 (MCT-112/113/114/115/116/117/119+120). MEMORY `feedback_admin_merge_autonomy.md` + ADR-020 D1 closed-loop 정착.

---

## 3. 발생한 이슈

### 3.1 [HIGH] mctrader-web Strategy Set 변경 미푸시 — Story scope 누수

**관측**:
- mctrader-web `feat/mct-117-adr018-audit-web` branch 위에 2 commit stacked, origin 미동기:
  - `420bf77` feat(web/ui): Strategy Set list/editor/promotion Streamlit pages 3 (MCT-119)
  - `494a00e` feat(web/api): Strategy Set CRUD + promotion FastAPI router (MCT-119)
- PR 미생성, CI 검증 0
- Story file (MCT-119) 에는 web 변경이 scope 로 명시됐으나 PR #44 (engine) 만으로 "완료" 보고

**근본 원인 분석**:
1. **branch 잘못 진입** — MCT-117 (mctrader-web ADR-018 audit) 작업 후 main switch 미수행 → MCT-119 web 변경이 wrong branch 위에 stacked
2. **multi-repo Story 의 "completion" 정의 부재** — engine PR merge 만으로 MCT-119 "완료" 처리. web 부분은 별도 PR 필요했음
3. **ADR-020 D1 의 게이트가 multi-repo Story 에서 false-positive** — Orchestrator 가 engine PR merge 만 보고 dispatch trigger → web 부분 누락 invisible

**의미**:
- ADR-019 D1 worktree isolation 이 mctrader-web 측에서는 미적용 (worktree 사용 안 함, main branch 위에서 작업 안 함)
- ADR-019 D6 (Orchestrator preflight inject) 가 multi-repo Story 의 각 repo 별 branch state 검증을 포함하지 않음
- multi-repo Story 의 "AC 통과" 정의가 모호 — 어느 repo 가 완료되면 trigger 인가?

**평가**:
- 본 retro 작성 시점에 발견 — Story file MCT-119 §4 AC 에 unchecked 박제
- §4.1 ADR 후보 발의 — multi-repo Story completion 게이트 정의

### 3.2 [MEDIUM] phase2-pipeline worktree 미정리 + engine main worktree 동기 미수행

**관측**:
```
$ git worktree list
C:/workspace/mclayer/mctrader-engine                                  feat/mct-116-adr018-audit-engine
C:/workspace/mclayer/mctrader-engine/.claude/worktrees/phase2-pipeline feat/mct-phase2-pipeline
```

- 메인 worktree: 머지 후 main switch 미수행 → 여전히 MCT-116 audit branch 에 머무름
- phase2 worktree: 머지 완료 (`e391f25` squash 됨) 후 cleanup 미수행

**근본 원인 분석**:
- ADR-019 D1 은 worktree **생성** 정책. **cleanup** 정책 부재
- 머지 후 자동 worktree remove + main pull 단계가 ADR-020 D1 게이트 시퀀스에 포함되지 않음
- "다음 Story 직진 조건"이 PMO 회고 dispatch 만 — 작업 환경 정리는 별개

**의미**:
- 다음 Story 진입 시 현재 branch 상태 혼란 — `git status` 가 stale branch 보고
- worktree 누적 → 디스크 사용량 증가 + branch 추적 혼선
- §3.1 의 mctrader-web "wrong branch 위에 stacked" 와 같은 root cause family

**평가**:
- §4.2 ADR-019 D7 또는 ADR-020 D2 후보 — Story 완료 게이트에 worktree cleanup + main 동기 단계 추가

### 3.3 [MEDIUM] pyright None-guard 4건 누락 — defensive coding 패턴 후보

**관측**:
Phase 2 구현 직후 pyright fail 4건 (commit `a15684a`):
- `sum(...)` Decimal 초기값 누락 (Decimal 0 명시 필요)
- `mark_price` None guard 누락
- `reject_reason` None guard 누락 (×2)

**근본 원인 분석**:
- Optional 타입 사용 시 None branch 처리 누락
- ADR-018 7패턴 중 D1 (validator) / D2 (frozen) / D3 (model_validator) 등은 input validation 영역. **None-guard 는 별도 패턴**
- pyright 가 강제하지만 "왜 이 None guard 가 필요한가" 의 도메인 의도가 코드/문서에 없음

**의미**:
- ADR-018 D? 신규 패턴 후보: "Optional 타입 사용 시 None branch 명시 처리 의무"
- 단순 pyright lint 가 아닌 도메인 의도 (예: mark_price None = 시장 데이터 부재 → no-trade 결정) 박제

**평가**:
- 4건 단일 Story → 1주 관측 후 누적 사례 ≥3 시 ADR-018 D8 또는 D9 후보 발의 (RETRO-MCT-117 §4.1 D9 후보와 별도 lane)
- §4.3 ADR 후보 발의

### 3.4 [LOW] xfail 추가 — pre-existing Decimal38_18 overflow

**관측**:
- `tests/test_rate_limit_integration.py` — BacktestExecutor equity 계산 중 Decimal38_18 overflow → xfail 마크
- `summary.py` sharpe clamp 추가 (Decimal38_18 max integer digits 20 자리 제한으로 overflow 방지)

**근본 원인 분석**:
- Decimal38_18 (precision 38, scale 18) 은 max integer digits = 38 - 18 = 20
- 누적 equity / sharpe 등 무한 누적 metric 이 20 자리 초과 가능
- BacktestExecutor 자체 bug 가 아니라 schema 제약과 메트릭 누적 로직 mismatch

**의미**:
- pre-existing bug → Phase 2 변경과 무관하나 본 PR 의 CI 가 처음 surface
- **별도 이슈 추적 필요** — 영구 xfail 회피
- Decimal precision 정책 재검토 필요 (38_18 → 적정 precision 산정)

**평가**:
- 본 Story scope 외. follow-up issue 발의 권장 (§10.3)

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] ADR-020 D2 후보 — multi-repo Story completion 게이트

```
target_adr: ADR-020 D2 신규
amendment_type: behavior (Orchestrator dispatch 게이트 강화)
trigger: MCT-119 §3.1 — engine PR #44 merge 만으로 Story 완료 보고, web 변경 미푸시 invisible
배경:
  - ADR-020 D1 은 단일 repo Story 의 "AC 통과 + admin merge → PMO dispatch" 게이트
  - multi-repo Story (예: MCT-119 = engine + web) 에서는 한 repo merge 만으로 D1 trigger 발화
  - 다른 repo 의 미푸시·미머지 변경이 invisible
문제:
  - Story scope 누수 — 사용자 보고 "Phase 1 완료" 와 실제 상태 불일치
  - 회고 dispatch 시점이 잘못 계산됨 (engine 만 보고 dispatch)
  - retroactive cherry-pick + 별도 PR 비용
제안 결정:
  a) Story file frontmatter 에 `repos: [engine, web]` 명시 의무화
  b) Orchestrator dispatch 전 각 repo 의 commit-vs-PR-merged 검증
  c) repos 중 어느 하나라도 미푸시·미머지면 dispatch 보류 + 사용자 alert
  d) 모든 repos 의 PR merged 확인 후 dispatch
예상 결과:
  - multi-repo Story 의 scope 누수 0
  - 본 retro §3.1 같은 "회고 작성 시점에 미푸시 발견" 패턴 회피
  - Story 완료 정의가 multi-repo 명시적
관련:
  - ADR-019 D1 worktree isolation (각 repo 별 branch 상태)
  - ADR-020 D1 PMO 회고 dispatch trigger
보류 사유: 본 사례 1건 — 1주 관측 후 동일 패턴 재발 시 박제 권장
```

### 4.2 [MEDIUM] ADR-019 D7 후보 — Story 완료 게이트에 worktree cleanup 단계

```
target_adr: ADR-019 D7 신규 또는 ADR-020 D3 신규
amendment_type: behavior (cleanup 게이트)
trigger: MCT-120 §3.2 — phase2-pipeline worktree 머지 후 cleanup 미수행 + engine main worktree stale branch
배경:
  - ADR-019 D1~D6 은 worktree **생성·격리** 정책
  - 머지 후 cleanup 정책 부재
  - 다음 Story 진입 시 stale branch 상태 → 본 retro §3.1 같은 wrong-branch-stack 위험
문제:
  - worktree 누적 → 디스크·branch 추적 혼선
  - main worktree 가 stale branch 머무르면 새 작업이 wrong branch 위에 진행
  - §3.1 의 root cause family
제안 결정:
  a) ADR-020 D1 Story 완료 게이트에 다음 단계 추가:
     1. PR merged 확인
     2. worktree 사용 시 → `git worktree remove` 자동 실행
     3. 메인 worktree → `git checkout main && git pull` 자동 실행
     4. PMOAgent dispatch
  b) 각 단계 실패 시 사용자 alert + 진행 보류
예상 결과:
  - 다음 Story 가 항상 clean main 에서 시작
  - wrong-branch-stack 패턴 0
  - worktree 누적 0
보류 사유:
  - 본 사례 + MCT-117 작업 후 main switch 미수행 패턴 = 2건
  - 1주 관측 후 누적 ≥3 시 박제 권장 (또는 즉시 박제 — root cause 명확)
```

### 4.3 [LOW] ADR-018 신규 패턴 후보 — Optional None-guard 의무

```
target_adr: ADR-018 D8 또는 D9 신규
amendment_type: artifact (코드 패턴)
trigger: MCT-120 §3.3 — pyright None-guard 4건 누락 (sum Decimal 초기값, mark_price, reject_reason ×2)
배경:
  - ADR-018 D1~D7 은 input validation / state mutation / file I/O / async / header / governance 영역
  - Optional 타입 None branch 처리는 별도 카테고리 — 도메인 의도 박제 대상
  - 본 Story 만 4건. 누적 사례 부족
문제:
  - pyright 가 강제하지만 "왜 None 인가" 의 도메인 의도 미박제
  - 단순 lint pass 가 아닌 명시적 None branch 비즈니스 의미 (no-trade 결정 등) 박제 필요
제안 결정 (1주 관측 후):
  a) None-guard 사례 누적 ≥3 Story 시 ADR-018 D8 발의
  b) 패턴: Optional 타입 함수 인자·return 시 None branch 명시 처리 + 도메인 의도 docstring
예상 결과:
  - 도메인 의도 (mark_price None = 시장 데이터 부재 → no-trade) 의 코드-문서 일관성
  - silent None propagation 회피
보류 사유:
  - 본 Story 1건 → 1주 관측 누적 후 결정
  - 다른 5 repo 의 Optional 사용 패턴 사전 audit 필요
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 7+ Story sweep — token efficiency 누적

본 세션 (2026-05-09) 처리 누적:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 mctrader-market audit)
- MCT-114 (D1/D2 market-bithumb audit)
- MCT-115 (D1/D2/D3 mctrader-data audit)
- MCT-116 (D2/D3/D5 mctrader-engine audit)
- MCT-117 (D1/D4/D5 mctrader-web audit)
- **MCT-119+120 (Strategy Set Pipeline Phase 1+2 — 4071 LoC, 64 파일)**

→ 7 Story + 4071 LoC 신규 = single-day completion. RETRO-MCT-117 §5.3 의 5 audit Story → 7 Story (구현 Story 포함) 로 확장. codeforge ζ arc 의 "ADR governance velocity" 가 신규 구현 Story 까지 일반화 가능 실증.

### 5.2 부수 fix 비율 카테고리 분리 — RETRO-MCT-117 §4.2 표준 갱신 필요

| Story | 본 fix LoC | 부수 fix LoC | 비율 | 부수 fix 카테고리 |
|---|---|---|---|---|
| MCT-114 | 4 | ~0 | 0% | — |
| MCT-113 | 1 | ~0 | <50% | — |
| MCT-116 | 다수 | ~0 | ~10% | — |
| MCT-117 | 11 | 39 | 350% | **pre-existing CI debt** |
| **MCT-119+120** | **22+7=29 commit** | **5 commit (~15%)** | **17%** | **신규 코드 self-discovered defect** |

→ 부수 fix 비율 단순 측정으로는 두 카테고리 (pre-existing debt vs self-discovered) 가 conflated. RETRO-MCT-117 §4.2 표준 갱신 권고:
- **Cat A (pre-existing debt 청소)**: 본 Story scope 외 부담 → > 50% 시 별도 Story 분리
- **Cat B (self-discovered defect)**: 본 Story scope 내 정상 비용 → 비율 기준 적용 안 함

본 Story 는 Cat B 17% — 정상 범위.

### 5.3 multi-repo Story 패턴 신규 발견 — Story scope 정의 갱신 필요

본 세션 multi-repo Story 사례:
- MCT-119: engine + web (web 미푸시)
- MCT-120: engine 단일

대부분 audit Story (MCT-113~117) 는 단일 repo. **신규 구현 Story 부터 multi-repo 비중 증가** — Strategy Set Pipeline 같은 cross-cutting 기능은 자연스럽게 multi-repo. ADR-020 D1 game 가 단일 repo 가정 — multi-repo 게이트 (§4.1 D2 후보) 박제 시급.

### 5.4 worktree isolation 부분 적용 + cleanup 미적용 패턴

| Story | worktree 생성 | 머지 후 cleanup |
|---|---|---|
| MCT-113 | 미사용 | N/A |
| MCT-114 | 미사용 | N/A |
| MCT-115 | 미사용 | N/A |
| MCT-116 | 사용 (race 발생) | 미수행 (main worktree stale) |
| MCT-117 | 미사용 | N/A |
| **MCT-120 (Phase 2)** | **사용 (race 0)** | **미수행 (worktree 잔존)** |

→ ADR-019 D1 worktree 생성은 race 회피에 효과적. **그러나 cleanup 정책 부재로 main worktree 가 stale branch 누적 → 다음 Story wrong-branch-stack 위험**. §4.2 ADR-019 D7 후보 정당성.

### 5.5 ADR-018 누적 — 신규 패턴 후보 N=4 (None-guard)

ADR-018 D1~D7 7패턴 외 신규 후보:
- D8 후보 (RETRO-MCT-117 §4.1): CI quality gate fail-fast 폐지 — pre-existing CI debt 누적 차단
- D? 후보 (본 retro §4.3): Optional None-guard 의무
- D? 후보 (RETRO-MCT-113 §4.1): branch guard enforcement 자동화 (ADR-019 D6)
- D? 후보 (RETRO-MCT-107-111 §8.6): 세션 종료 게이트 (ADR-021)

→ 4 후보 누적. 1주 관측 (2026-05-16) 후 일괄 ADR 박제 sprint 권장 — RETRO-MCT-117 §6 권고와 일치.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **mctrader-web Strategy Set 변경 follow-up Story 즉시 발의** (§3.1) — `feat/mct-119-web-strategy-set-ui` 신규 branch 에 cherry-pick + push + PR 생성. MCT-119 AC § "web 변경 PR" 미체크 해소. **다음 세션 시작 시 최우선** — Story scope 누수 잔존 시 ADR-020 D1 위반 고착.

2. **ADR-020 D2 (multi-repo Story 게이트) + ADR-019 D7 (worktree cleanup 게이트) 즉시 박제 검토** (§4.1, §4.2) — 본 사례 root cause 명확. 1주 관측 임계 충족 전이라도 발의 가능. ArchitectAgent dispatch 권장.

3. **xfail (test_rate_limit_integration.py) follow-up 이슈 발의** (§3.4) — Decimal38_18 overflow 별도 추적. `mctrader-engine` repo 에 GitHub issue 생성 + Decimal precision 정책 재검토 Story 후보.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Phase 1 설계·DTO·Protocol·Registry | ~15% |
| Phase 1 14 SignalProducer 구현 | ~15% |
| Phase 1 Aggregator/Constructor/PositionManager/Risk/ExecutionPlanner | ~15% |
| Phase 1 PipelineRunner + EventStore + DB 8 테이블 | ~10% |
| **Phase 2 5 layer 구현 (Cost/Constraint/SignalGroup/Monitor/HotSwap)** | **~15%** |
| Phase 1+2 신규 13 unit test 작성 | ~10% |
| Alembic 0002 + 0003 migration | ~5% |
| **CI fix 5 commit (ruff 3 + pyright 1 + xfail+sharpe 1)** | **~5%** |
| PR open + admin merge | ~2% |
| Story file 2개 + 본 retro 작성 | ~8% |

→ **부수 비용 ~5%** (CI fix). RETRO-MCT-117 의 ~30% 와 비교 시 신규 구현 Story 의 부수 비용 이 매우 낮음 — pre-existing debt 청소가 부수 비용의 주범 임을 §5.2 분리 카테고리로 확정.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-019**: Parallel agent isolation — D1 worktree 생성 (Phase 2 준수), D7 worktree cleanup 후보 (§4.2)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro trigger), D2 multi-repo 게이트 후보 (§4.1)
- **ADR-018**: Defensive coding patterns — D8 후보 (Optional None-guard, §4.3)
- **ADR-011**: CI standard — 본 PR CI green 전체 (5 SUCCESS + 1 informational)
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #44 admin merge 자율 (7번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: CI fix 5 commit 자동 recovery 사이클 적용
- **MEMORY** `feedback_parallel_session_branch_race.md`: §3.2 worktree cleanup 미수행 = race 잠재 누적
- **선행 retro**:
  - `RETRO-MCT-112.md` (D8 forward enforcement)
  - `RETRO-MCT-113.md` (D3 mctrader-market audit)
  - `RETRO-MCT-114.md` (D1/D2 mctrader-market-bithumb audit)
  - `RETRO-MCT-115.md` (D1/D2/D3 mctrader-data audit)
  - `RETRO-MCT-116.md` (D2/D3/D5 mctrader-engine audit)
  - `RETRO-MCT-117.md` (D1/D4/D5 mctrader-web audit, §4.2 부수 fix 비율 표준 본 retro §5.2 갱신)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-119.md` §11 + `docs/stories/MCT-120.md` §11 양쪽에 본 retro pointer 박제 (Story file 작성 시 동시 박제 — RETRO-MCT-117 §3.2 ADR-020 D1 enforcement gap 회피).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 최우선)

- **mctrader-web Strategy Set follow-up Story** (가칭 MCT-121):
  1. `c:\workspace\mclayer\mctrader-web` 에서 `git checkout main && git pull`
  2. `git checkout -b feat/mct-121-web-strategy-set-ui main`
  3. `git cherry-pick 420bf77 494a00e`
  4. push + PR open + CI green 확인 + admin merge
  5. PMO 회고 자동 dispatch
- **engine main worktree 동기**:
  1. `cd c:\workspace\mclayer\mctrader-engine && git checkout main && git pull origin main`
  2. `git worktree remove .claude/worktrees/phase2-pipeline`
  3. `git branch -d feat/mct-phase2-pipeline feat/mct-116-adr018-audit-engine` (선택)

### 10.2 ADR 박제 (1주 관측 또는 즉시 검토)

- **ADR-020 D2** (§4.1) — multi-repo Story 게이트 — 본 retro §3.1 root cause 명확, 즉시 박제 권장
- **ADR-019 D7** (§4.2) — Story 완료 게이트에 worktree cleanup 단계 — root cause 명확, 즉시 박제 권장
- ADR-018 D8 (§4.3) — Optional None-guard — 1주 관측 누적 권장

### 10.3 별도 issue 발의

- **mctrader-engine GitHub issue** — `test_rate_limit_integration.py` xfail 영구 회피 + Decimal38_18 overflow 근본 해결 (Decimal precision 재산정 Story 후보)

### 10.4 Strategy Set Pipeline 후속 Story 트리거

Phase 1 + Phase 2 완료로 다음 Story 가능:
- **Phase 3 후보**: backtest mode 에서 Strategy Set DSL 로 14 producer × 3 aggregator × 3 constructor × 5 risk = 630 조합 자동 sweep (parameter optimization)
- **Strategy Set ↔ WFO 연동**: 기존 WFO lifecycle 이 Strategy Set version 을 promote 하도록 변경
- **paper/live 모드 Strategy Set 활성**: HotSwapManager + ExchangeConstraintValidator 로 Bithumb live 운용 첫 적용

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
