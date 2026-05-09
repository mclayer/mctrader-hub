# RETRO-MCT-107-111 — Codex 심층 리뷰 fix sweep (5 repo · 16 PR)

**범위**: MCT-107 (market) · MCT-108 (bithumb) · MCT-109 (data) · MCT-110 (engine) · MCT-111 (web)
**기간**: 2026-05-09 (single calendar day, fix sweep window 12:09~12:39 UTC)
**Trigger**: Codex 심층 리뷰 2026-05-09 — 5 repo 에서 CRITICAL 14건 / HIGH 22건 일괄 발견
**Status**: ALL MERGED (admin merge)

---

## 1. 결과 요약

| Story | Repo | Fix 브랜치 | PR | merged at (UTC) | follow-up |
|---|---|---|---|---|---|
| MCT-107 | mctrader-market | 2 | #5, #6 | 12:09:53 / 12:20:33 | — |
| MCT-108 | mctrader-market-bithumb | 2 | #8, #9 | 12:10:25 / 12:15:55 | — |
| MCT-109 | mctrader-data | 3 | #19, #20, #21 | 12:35:49~12:39:03 | heartbeat.py 1줄 |
| MCT-110 | mctrader-engine | 4 | #38, #39, #40, #41 | 12:35:59~12:36:16 | — |
| MCT-111 | mctrader-web | 5 | #28~#31 + 1 | 12:35:44~12:37:00 | rbac.py CreateTokenRequest |
| **합계** | **5 repo** | **16 fix branch** | **16 PR** | **30분 window** | **2 follow-up** |

**검증**: 각 repo main pytest green. mctrader-engine 기준 762→**769** (회귀 0, 신규 7 누락 테스트 추가).

---

## 2. 잘된 점

### 2.1 Story §4 누락 테스트 사전 박제
모든 5 Story 가 `## 4. 누락 테스트 (이 Story 내 추가)` 섹션을 코드 변경 *전* 명시 → QA 누락 0건. fix 브랜치 작성과 테스트 작성이 같은 PR 안에 묶여 evidence trail 분리 안 됨. **TDD-by-spec 패턴**으로 정착시킬 가치 있음.

### 2.2 Vertical slice per fix branch (PMO 분해 규칙 1 검증)
5 repo × 평균 3.2 fix branch 각각이 disjoint 파일 경로 → 병렬 작업 + merge 충돌 0건. PMO Epic 분해 자문 §1 규칙 1 (파일 경로 disjoint → 병렬) 의 효과 실증.

### 2.3 30분 admin merge sweep
CI green 즉시 16 PR 일괄 admin merge. MEMORY `feedback_admin_merge_autonomy.md` 적용으로 사용자 trigger 0회. CI watcher → admin merge → 다음 PR pipeline 자동 흐름.

### 2.4 ADR cross-ref accuracy
각 Story `related_adrs` frontmatter 가 실제 fix 가 위반/강화한 ADR (002, 004, 006, 007, 008, 009, 011, 013) 전부 정확히 인용. ADR 견인 retro 가능.

---

## 3. 발생한 이슈 — Cross-Story 공통 패턴

### Pattern A: Parallel agent branch race (Issue 1, 4)
- **재발**: MEMORY `feedback_parallel_session_branch_race.md`(2026-05-08 MCT-100/101/102 phase3~5) 와 동일 silent failure mode 가 mctrader-engine working dir 에서 재발.
- **원인**: 동일 git working tree 공유 + parallel agent → `git checkout` race + untracked file pollution.
- **5 repo 중 발생 repo**: engine (확인), data·web (잠재). hub 는 단일 작업이라 미발생.
- **해결안 후보**:
  1. parallel agent spawn 시 `git worktree add` 강제 (Orchestrator-level policy)
  2. 모든 commit 직전 `git branch --show-current` 검증 hook
  3. 6 repo 전체 working dir 에 worktree 정책 일괄 채택

### Pattern B: Python 버전 충돌 (Issue 2)
- 시스템 default `python` = 3.14, 전 6 repo pyproject `<3.13,>=3.11` → agent 가 default `python` 호출 시 환경 자동 활성화 실패.
- **5 repo 모두 동일 제약** → 전 repo 공통 부트스트랩 contract 가 부재. ADR-010 보완 필요.
- **해결안**: agent Preflight 체크에 `py -3.12 --version` 검증 추가.

### Pattern C: Package editable mode 누락 (Issue 5)
- venv 내 패키지가 wheel install 상태 → 신규 코드 미반영 → pytest stale.
- 6 repo 공통 패턴 (mctrader-engine, mctrader-data 발견; market/bithumb/web 잠재).
- **해결안**: agent 부트스트랩 시 `pip install -e .` idempotent 명령 명시.

### Pattern D: Codex 심층 리뷰 결함 양상 (cross-repo)
5 repo 의 14 CRITICAL / 22 HIGH 결함을 분류:

| 결함 카테고리 | 발생 repo | 사례 |
|---|---|---|
| **시간 정합성** (time-travel, ordering) | engine | backtest equity time-travel, paper fill ts-order |
| **불변식 누락** (Pydantic validator, frozen) | market, engine | Order overfill, OrderBook list→tuple, virtual fund check |
| **거버넌스 bypass** (CLI flag override) | engine, web | WFO promote --gate-d6-passed flag, RBAC reject silently |
| **보안 case-sensitivity** | bithumb, web | WS forbidden header `.lower()` 누락, REST forbidden header |
| **데이터 fabrication** (silent default) | bithumb, data | Decimal("0") fill, side="buy" default |
| **schema 불일치** (DDL ↔ INSERT 컬럼) | data, web | ADR-009 16-col 미완, idempotency_cache schema |
| **원자성 결여** (rename, lock) | data, engine | Parquet write, rate_limiter TOCTOU |

→ **공통 근본 원인**: 6 repo 가 **타입 시스템·불변식·governance gate 강제 패턴**이 일관되지 않음. Pydantic validator + frozen dataclass + atomic file write + lock-based counter 4 가지가 부재한 곳마다 결함이 재생.

### Pattern E: micro-optimization → invariant test 회귀 (MCT-110 only)
bollinger float 최적화 1건이 exact equality 테스트 깨뜨림 → tolerance 추가 round-trip. cross-Story 보편 아님이지만, perf fix 와 invariant test 사전 검증 분리 패턴 후보.

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

PMO `pmo_output v1.adr_proposal` 필드로 Orchestrator 에 inline 반환:

### ADR-018 후보: Defensive coding patterns — 6-repo cross-cutting invariant baseline
```
category: Architecture
title: ADR-018: Defensive coding patterns — 6-repo cross-cutting invariant baseline
trigger: MCT-107~111 5 Story 14 CRITICAL / 22 HIGH 결함이 7개 동일 카테고리에 집중 발생
배경:
  - 6 repo 가 ad-hoc 한 validator/frozen/atomic write/lock 패턴 채택 → 결함 분포가 repo-uniform
  - Codex 심층 리뷰 1회로 36건 결함 한꺼번에 노출 = 패턴 부재로 인한 silent rot
문제:
  - Pydantic validator (raise on float/NaN/whitespace), frozen=True + tuple, Pydantic model_validator,
    lock-based atomic counter, .tmp_{uuid} + rename, case-insensitive header guard, governance flag 제거
    7가지 패턴이 SSOT 없음
제안 결정:
  - ADR-018 로 7개 패턴 baseline 박제
  - 신규 코드 PR 시 해당 패턴 적용 여부 reviewer 체크리스트 강제
예상 결과:
  - 차기 Codex 심층 리뷰 시 동일 카테고리 finding 0건
  - 신규 repo 추가 시 baseline 견인 가능
```

### ADR-019 후보: Parallel agent isolation — git worktree 강제 + 부트스트랩 contract
```
category: Infrastructure
title: ADR-019: Parallel agent isolation — git worktree + Python/editable bootstrap contract
trigger: MCT-100/101/102 (2026-05-08) + MCT-110 (2026-05-09) parallel agent branch race 재발 + python/editable 부트스트랩 누락
배경:
  - mctrader-hub 에 이어 mctrader-engine 도 동일 silent failure mode 재현
  - python 3.14 default + non-editable install 두 부트스트랩 갭이 5 repo 공통
문제:
  - parallel agent 가 동일 working tree 공유 시 atomic 보장 없음
  - agent 환경 부트스트랩 SSOT 부재 → repo 마다 ad-hoc 발견
제안 결정:
  - 6 repo 전체에 git worktree 정책 + Orchestrator-level enforcement
  - Preflight 체크에 `py -3.12 --version` + `pip install -e .` idempotent 명령 표준화
예상 결과:
  - parallel agent silent failure 0건
  - 신규 agent spawn 시 환경 부트스트랩 결정성 확보
```

---

## 5. 개선 제안 3건 (다음 세션 반영)

1. **PMO Epic 분해 자문에 "TDD-by-spec" 섹션 표준화** — Story §4 누락 테스트 사전 박제 패턴을 분해 자문 template 에 명시. MCT-107~111 가 우연히 정착시킨 패턴을 SSOT 로 승격.
2. **6-repo cross-cutting Codex 리뷰를 정기화** — 1회로 36건 결함 노출 효과를 Epic 완료 시 trigger 로 박제 (예: Epic close 직전 cross-repo Codex sweep).
3. **agent 환경 부트스트랩 Preflight contract** — `py -3.12` + `pip install -e .` + `git worktree` 3 항목을 모든 agent spawn Preflight 에 강제.

---

## 6. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Codex 심층 리뷰 (5 repo 일괄) | ~30% |
| Story 작성 (MCT-107~111) | ~10% |
| Fix 브랜치 16건 작성 + commit | ~25% |
| 누락 테스트 7건 + tolerance fix | ~15% |
| Branch race / python / editable 정정 | ~10% |
| PR open + admin merge sweep | ~5% |
| 회고 (이 문서) | ~5% |

→ **정정 비용 10%** 가 worktree 정책으로 5%↓ 절감 가능 추정.

---

## 7. 관련 ADR · MEMORY

- ADR-009 (OHLCV 16-col), ADR-013 (Symbol/Order immutable), ADR-008 (secret guard), ADR-007 (RiskGate), ADR-006 (WFO promotion), ADR-004 (ExecutionReport), ADR-002 (TradeExecutor), ADR-011 (CI standard) — 7 ADR 견인
- MEMORY `feedback_parallel_session_branch_race.md` (2026-05-08) — Pattern A 의 선례
- MEMORY `feedback_admin_merge_autonomy.md` — admin merge sweep 정당성
- MEMORY `feedback_ci_failure_auto_recovery.md` — bollinger tolerance fix round-trip 패턴

---

**작성**: PMOAgent (cross-Story 회고 감사)
**Story §11 회고 pointer**: MCT-110 §11 (single Story retro), MCT-107~109/111 §11 본 retro 참조 (각 Story PMO 차기 감사 시 보완)

---

## 8. 프로세스 게이트 위반 — Story 완료 회고 자동 dispatch 누락 (2026-05-09 ESCALATE)

### 8.1 ESCALATE 트리거
사용자가 MCT-110 fix sweep 직후 "회고했나?" 라고 직접 질문 → Orchestrator(Sonnet) 가 그 시점에서야 PMOAgent dispatch. 즉 **Story AC 완료 → 회고** 가 자동 워크플로 단계로 묶여 있지 않았음.

### 8.2 정량 근거 (5 Story 감사)

| Story | §11 회고 섹션 보유 | dispatch 시점 | 자동성 |
|---|---|---|---|
| MCT-107 | 없음 | 사용자 지적 후 묶음 retro 합류 | NO |
| MCT-108 | 없음 | 사용자 지적 후 묶음 retro 합류 | NO |
| MCT-109 | 없음 | 사용자 지적 후 묶음 retro 합류 | NO |
| **MCT-110** | **있음** (line 87) | 사용자 지적 직후 작성 | NO (수동) |
| MCT-111 | 없음 | 사용자 지적 후 묶음 retro 합류 | NO |

**5/5 모두 자동 dispatch 0건**. MCT-110 만 §11 헤더가 있으나 그것도 사용자 지적 이후 작성 — 즉 5 Story 묶음 sweep 어디에도 "AC 완료 → PMOAgent" 자동 트리거가 발화하지 않음.

### 8.3 구조적 누락 진단
- mctrader-hub `.claude/_overlay/CLAUDE.md` 의 codeforge Story workflow 섹션 (`Story workflow (codeforge ζ arc)`) 에 phase enumeration 은 있으나 (`요구사항 → 설계 → ... → 완료`), **"완료" phase 진입 직후 PMOAgent dispatch 의무** 가 명시 텍스트로 박제돼 있지 않음.
- codeforge-pmo `PMOAgent.md` 의 호출 시점 표는 `Story 완료 시 → 회고 감사` 를 적시하나, 이는 PMOAgent 본인의 책임 정의일 뿐 **Orchestrator 의 dispatch trigger 의무** 는 별도 명시 없음.
- 결과: Sonnet Orchestrator 가 AC 통과 + admin merge 직후 다음 Story 로 직진하는 흐름이 자연스러워, 회고 단계가 silent skip 됨.

### 8.4 단기 조치 (본 ESCALATE 직접 수행)
1. 본 retro §8 에 위반 사실 박제 (이 섹션).
2. `.claude/_overlay/CLAUDE.md` `Story workflow` 섹션에 "Story 완료 의무" 규칙 추가 — `요구사항 → ... → 완료 → **PMO 회고 (의무)**` 로 phase enumeration 확장, Orchestrator 의무화.

### 8.5 중기 조치 (ADR 후보 + Cross-Story 패턴)
- 본 누락은 단순 1회 실수가 아니라 **5 Story 연속 0/5 누락** = 워크플로 SSOT 결함. ADR 후보 발의 사유 충족 (PMOAgent.md §4 "패턴 분석 결과 반복되는 이슈가 있으면").
- ADR-018 (defensive coding), ADR-019 (parallel agent isolation) 와 함께 **ADR-020 후보: Story 완료 게이트 — PMO 회고 자동 dispatch** 추가 발의 (§9 참조).

### 8.6 ADR-020 작성 당일 재발 (2026-05-09 후속 ESCALATE — same-session relapse)

**관측**: ADR-020 (Story 완료 PMO 회고 자동 dispatch 의무) 를 **2026-05-09 동일 세션 내** 작성하고 `.claude/_overlay/CLAUDE.md` line 142~149 에 "Story 완료 의무 — PMO 회고 자동 dispatch" 섹션을 박제했음에도, **같은 세션** 후반부 (MCT-112~118 7 Story 신규 생성 + ADR 3건 작성 작업) 종료 시점에 회고가 자동 dispatch 되지 않았다. 사용자가 "회고했나?" 라고 명시적 trigger 한 후에야 PMOAgent dispatch 발화.

**정량**:

| 시점 | 이벤트 | 회고 자동 dispatch |
|---|---|---|
| 2026-05-09 12:35Z | MCT-110 fix sweep 완료 (4 PR merge) | ✗ (사용자 지적 후) |
| 2026-05-09 13:??Z | ADR-020 + overlay CLAUDE.md 박제 | (해당 없음 — Story 아님) |
| 2026-05-09 14:??Z | MCT-112~118 7 Story 생성 + ADR-018/019 완성 | ✗ (사용자 지적 후 본 §8.6 작성) |

**진단**: ADR-020 은 *작성됐고* CLAUDE.md 도 *갱신됐으나*, **같은 세션 내 LLM 컨텍스트가 ADR-020 정착 이후 turn 들에서 자동 적용되지 않음**. 가능한 원인:

1. **Context window 위치 효과** — overlay CLAUDE.md line 142~149 가 SessionStart 시점 system prompt 에 inject 됐다면 즉시 적용됐을 것이나, **세션 도중 file edit 후에는 새 Edit 결과가 system prompt 로 re-inject 되지 않음**. 즉 ADR-020 박제는 *다음 세션* 부터 발화하는 SSOT.
2. **Phase enumeration 인식 갭** — overlay CLAUDE.md line 139 phase enumeration 끝의 "→ PMO 회고 (의무)" 가 hub Story (MCT-112~118 = 신규 생성, AC 미통과) 에는 즉시 적용 안 됨. 본 세션 마지막 hub Story 작업은 MCT-110 이며, 그 retro 는 이미 RETRO-MCT-107-111 묶음 + MCT-110 §11 로 작성 완료. **MCT-112~118 은 신규 단계** 이므로 retro 가 아니라 *세션 회고* 가 필요했음 — 이는 PMOAgent §5 "세션 회고 synthesize" 영역으로, ADR-020 의 "Story 완료 retro" 와는 구분되는 별도 게이트.

**즉 ADR-020 단독으로는 본 세션 종료 시 회고 누락을 막지 못한다** — ADR-020 은 Story-level 게이트이고, 본 세션 종료 시 필요했던 것은 **세션-level 회고** (PMOAgent §5).

**단기 조치**:

1. 본 §8.6 박제 (이 섹션).
2. ADR-020 D5 신규 추가 후보: **세션 종료 게이트** — Orchestrator 가 세션 종료 직전 PMOAgent §5 (세션 회고 synthesize) 를 자동 dispatch. trigger 는 "사용자가 세션 종료 의도를 표명" 또는 "다수 Story·ADR 작업 후 자연 종료점 도달". (별도 ADR-021 후보 가능.)
3. **same-session relapse 관측**: ADR/CLAUDE.md 박제는 *다음 세션 system prompt re-inject* 시 발화. 세션 도중 박제한 규칙을 본인 세션에 재귀 적용하려면 **Orchestrator 가 박제 직후 명시적으로 "다음부터 X 적용" 자기 reminder** 를 컨텍스트에 inject 해야 함 — 이는 hook (SessionStart 가 아니라 PostFileEdit 패턴) 또는 Orchestrator self-prompt 패턴 후보.

### 8.7 패턴 분석 — same-session rule adoption gap

**핵심 관측**: 본 세션은 회고 누락이 **두 차원** 에서 발생:

| 차원 | 누락 이벤트 | ADR-020 적용 여부 |
|---|---|---|
| **Story-level** (MCT-110 완료 직후) | ✗ 자동 dispatch 안 됨 | ADR-020 작성 *전* 발생 — 박제 후 사후 처리 |
| **Session-level** (세션 종료 시점) | ✗ 자동 dispatch 안 됨 | ADR-020 작성 *후* 발생 — **same-session relapse** |

**Same-session relapse 의 구조적 원인**:
- LLM 의 system prompt 는 SessionStart 시점에 한 번 고정. 세션 도중 file edit 으로 SSOT 가 갱신돼도 LLM 컨텍스트의 system prompt 영역에는 반영되지 않음. 갱신된 SSOT 가 *어쩌다 Read 됐을 때* 만 컨텍스트에 진입.
- 따라서 "이 세션 도중 박제한 규칙을 이 세션 후반부에 적용" 은 **자기 reminder + 신규 사실의 반복 노출** 없이는 보장 안 됨.

**단기 조치 제안**:

1. **Orchestrator self-reminder 패턴**: ADR/CLAUDE.md/overlay 박제 직후 Orchestrator 가 "본 세션 남은 turn 부터 X 규칙 적용" 라는 self-message 를 컨텍스트에 명시 inject. (메시지 wording 표준화 가치 있음.)
2. **세션 종료 점검 checklist 의 SSOT 화**: 본 §8.6 의 진단을 ADR-021 (세션 종료 게이트) 후보로 발의. PMOAgent §5 자동 dispatch trigger 를 명시.
3. **MEMORY 갱신 후보**: `feedback_session_end_pmo_retro.md` 신규 추가 — "세션 종료 시 사용자 trigger 없이 PMOAgent 세션 회고 자동 수행". admin merge autonomy 와 동일 자율 패턴 확장.

**중기 조치 (ADR-021 후보)**:

```
category: Process & Governance
title: ADR-021: 세션 종료 게이트 — PMOAgent 세션 회고 자동 dispatch
trigger: ADR-020 작성 당일 same-session relapse — 세션 종료 회고가 사용자 trigger 의존
배경:
  - ADR-020 은 Story-level 회고 게이트만 정의. 세션-level 회고 (PMOAgent §5) 는 별도 trigger 없음
  - 본 세션 종료 시 사용자 "회고했나?" 직접 질문 후 dispatch — 자율 수행 0건
  - same-session relapse 패턴: 세션 도중 박제한 규칙은 system prompt re-inject 가 없으면 본 세션에 자동 적용 안 됨
문제:
  - 세션 종료 시점 = 다수 Story/ADR 작업 누적 → 회고 가치 최대. 그러나 자동 trigger 부재
  - 사용자 의존 = 규칙 부재 (ADR-020 §A1 기각 사유와 동일)
제안 결정:
  - Orchestrator 가 다음 trigger 중 하나 검출 시 PMOAgent §5 자동 dispatch:
    a) 사용자가 세션 종료 의도 표명 ("그만", "여기까지" 등)
    b) 동일 세션 내 3+ Story/ADR 작업 누적 + 자연 종료점 (사용자 다음 지시 부재)
    c) /compact 직전
  - same-session 박제 규칙 즉시 적용 보강: Orchestrator self-reminder 패턴 표준화
예상 결과:
  - 세션 회고 누락 0건
  - same-session relapse 차단
```

---

## 9. ADR-020 후보 (추가 발의) — Story 완료 게이트 PMO 회고 자동 dispatch

```
category: Process & Governance
title: ADR-020: Story 완료 게이트 — PMO 회고 자동 dispatch 의무
trigger: MCT-107~111 5 Story 연속 (0/5) §11 회고 자동 수행 누락 — 사용자 지적 후에야 묶음 처리
배경:
  - codeforge ζ arc Story workflow 의 "완료" phase 가 phase enumeration 끝점으로만 정의돼,
    완료 직후 회고 dispatch 가 명시 게이트 없음
  - PMOAgent.md 는 PMO 본인 책임만 적시 — Orchestrator 의 dispatch 의무 명시 부재
  - 결과: 5 Story 묶음 sweep 동안 회고 0건 자동, 1건 수동 (사용자 지적 직후), 4건 사후 묶음 합류
문제:
  - Cross-Story 패턴 (Pattern A~E) 발견이 5 Story 누적 후에야 일괄 발생 →
    개별 Story 완료 시점에 잡혔으면 후속 Story 에 즉시 반영 가능했을 신호가 지연
  - retro 누락이 silent → 사용자 지적 없으면 영구 skip 가능
제안 결정:
  - .claude/_overlay/CLAUDE.md `Story workflow` phase enumeration 에 "완료 → PMO 회고" 로 회고를
    phase 의 일부로 박제 (skip 시 phase 미완)
  - Orchestrator 가 AC pass 직후 PMOAgent 자동 dispatch (사용자 trigger 불필요, MEMORY admin_merge_autonomy
    와 동일 자율 패턴)
  - phase-gate-mergeable.yml workflow 에 §11 헤더 존재 검증 추가 (장기)
예상 결과:
  - Cross-Story 패턴 발견 lag 최소화 (n+1 Story 시작 전 n 의 retro 가용)
  - silent skip 0건
  - retro 누락 검출이 사용자 의존 → CI 의존으로 전환
```
