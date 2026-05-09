# RETRO-MCT-112 — ADR-018 D8 PR template 방어 코딩 체크리스트 6-repo 적용

**범위**: MCT-112 (단일 Story · 6 repo 횡단)
**기간**: 2026-05-09 (single-day, parallel dispatch ~1.5분)
**Trigger**: ADR-018 D8 Accepted — defensive coding checklist를 6 repo `.github/PULL_REQUEST_TEMPLATE.md`에 강제
**Status**: ALL MERGED (admin merge)
**Story file**: `docs/stories/MCT-112.md`

---

## 1. 결과 요약

| Repo | PR | 처리 유형 | 비고 |
|---|---|---|---|
| mctrader-hub | #214 | 기존 template append | ADR-011 D9와 병합 |
| mctrader-market | #7 | 신규 생성 | template 없던 repo |
| mctrader-market-bithumb | #10 | 신규 생성 | 동상 |
| mctrader-data | #25 | 신규 생성 | 동상 |
| mctrader-engine | #42 | 신규 생성 | 동상 |
| mctrader-web | #32 | 신규 생성 | 동상 |
| **합계** | **6 PR** | **1 append + 5 신규** | **모두 MERGED** |

**검증**: 6 repo 각각 `.github/PULL_REQUEST_TEMPLATE.md` 에 ADR-018 D1~D7 + N/A 사유 8 체크박스 존재 확인.

---

## 2. 잘된 점

### 2.1 Parallel agent dispatch — 6 repo / ~1.5분
6개 병렬 에이전트를 단일 dispatch turn 으로 spawn → 6 repo 동시 PR 작성 + open. RETRO-MCT-107-111 §3 Pattern A (parallel agent branch race) 가 본 작업에서는 재발하지 않음. 근거:
- 작업 단위가 **각 repo 별 독립 working dir** (`mctrader-hub`, `mctrader-market`, ...) → branch race 구조적으로 불가능
- 단일 파일 (`.github/PULL_REQUEST_TEMPLATE.md`) 만 touch → file conflict 0
- 즉 PMOAgent.md §1 분해 규칙 1 (파일 경로 disjoint → 병렬) 의 가장 깨끗한 사례

### 2.2 ADR-011 D9 와 충돌 없는 구조적 append
mctrader-hub 만 기존 PR template 보유 (ADR-011 D9 CI standard checklist). ADR-018 섹션을 별도 H2 (`## Defensive coding checklist (ADR-018)`) 로 append → 기존 ADR-011 섹션 zero-touch. **두 ADR 의 PR template 결정이 horizontally compose 가능함이 실증**. 이는 향후 ADR-NN 가 PR template 에 새 섹션을 추가할 때 reference pattern.

### 2.3 ADR-018 → MCT-112 governance loop closure (single-day)
2026-05-09 same-day 에 다음 chain 이 완주:
1. RETRO-MCT-107-111 §4 ADR-018 후보 발의
2. ADR-018 Accepted (D1~D7 + D8 PR template 강제)
3. **MCT-112 D8 6-repo 적용 (본 Story)**
4. MCT-113~117 ADR-018 소급 audit Story 5건 신규 생성

→ "결함 발견 → ADR 박제 → governance enforcement → 소급 audit" 4-step loop 가 single calendar day 에 닫힘. ADR governance velocity 의 좋은 예.

### 2.4 30분 admin merge sweep (RETRO-MCT-107-111 §2.3 패턴 재실증)
6 PR CI green 즉시 admin merge. MEMORY `feedback_admin_merge_autonomy.md` 적용. 전 sweep (16 PR / 30분) 대비 본 sweep (6 PR / ~10분 추정) 도 동일 자율 패턴.

---

## 3. 발생한 이슈

본 Story 는 **결함 0건**. 단, 다음 cross-Story 관찰사항 식별:

### 3.1 D8 체크리스트 자동 검증 미존재 (잠재적 갭)
ADR-018 D8 은 PR reviewer 가 **수동으로** 체크박스를 표시하도록 설계. CI level 강제 (PR body 에 `[x]` 가 모두 채워졌는가 검증) 는 없음. 가능한 미래 갭:
- reviewer 가 체크 없이 LGTM → defensive pattern 누락 silent 통과
- N/A 사유 명시 없이 N/A 표시 가능

→ ADR-018 후속으로 **D9 (PR body 체크리스트 CI 검증) 후보** 발의 가치 있음. 단, MCT-112 시점에서는 reviewer 행동 변화 관측 데이터 부족 → 1주 정도 PR 흐름 관측 후 결정 권장.

### 3.2 Story §11 회고 섹션 본 Story file 미작성
MCT-112.md 본문에 `## 11. 회고` 헤더 부재 (확인: line 71 까지 §1~§4 만). ADR-020 D1 (Story 완료 시 PMO 회고 자동 dispatch) 적용 시점 직후 Story 임에도 §11 헤더 사전 박제가 안 됨. 본 retro 작성으로 사후 보강 필요 — `MCT-112.md §11` 에 본 retro pointer 추가 권장.

→ **ADR-020 D1 enforcement gap**: 새 Story template 자체에 `## 11. 회고` 헤더가 default 로 박제돼 있어야 회고 누락이 구조적으로 차단됨. 현재 일부 Story file 은 §11 헤더 부재 → 사후 추가 의존. ADR-020 D2~D4 보완 후보.

---

## 4. Cross-Story 인사이트

### 4.1 ADR-018 governance chain 의 single-day 완주 의미
| Step | 결과 | 누적 시간 |
|---|---|---|
| Codex 5-repo 심층 리뷰 (36 finding) | RETRO-MCT-107-111 §3 Pattern D | ~12:00 UTC |
| ADR-018 후보 발의 | RETRO-MCT-107-111 §4 | ~13:00 UTC |
| ADR-018 Accepted (D1~D8) | `docs/adr/ADR-018-...md` | ~13:30 UTC |
| **MCT-112 D8 6-repo 적용** | **본 Story 6 PR MERGED** | **~14:00 UTC** |
| MCT-113~117 소급 audit Story 발의 | 5 신규 Story | ~14:30 UTC |

→ "결함 발견부터 governance 박제 + 적용까지 ~2.5시간." codeforge ζ arc 의 ADR velocity 가 매우 빠르게 작동한 사례. **단점**: 이렇게 빠른 ADR adopt 는 D8 enforcement 효과 데이터 (실제 reviewer 행동 변화) 누적 전에 다음 ADR 후보를 발의하게 만듦. §3.1 D9 후보 검토를 1주 데이터 수집 후로 미루는 이유.

### 4.2 Cross-Story 패턴 — governance enforcement Story 의 분류
MCT-112 와 유사한 "ADR enforcement / template / config 6-repo 일괄 적용" Story 의 특성:

| 특성 | MCT-112 사례 |
|---|---|
| 파일 경로 disjoint (repo 별 isolated) | YES — 병렬 agent ideal |
| 단일 파일 touch | YES — `.github/PULL_REQUEST_TEMPLATE.md` |
| 기존 코드 변경 없음 | YES — pure addition |
| 비즈니스 로직 영향 0 | YES — process-level only |
| 회귀 위험 0 | YES — pytest 영향 zero |

→ 이런 Story 는 **PMOAgent §1 병렬 판정 규칙 1 의 canonical 사례**. 향후 유사 Story (예: ADR-019 worktree 정책 6-repo 적용 = MCT-118) 도 동일 패턴으로 처리 가능.

### 4.3 ADR-018 소급 audit Story 5건 (MCT-113~117) 과의 연계
MCT-112 가 D8 (PR template, 신규 코드 강제) 을 처리했다면, MCT-113~117 은 D1~D7 의 **기존 코드 소급 audit** 을 5 repo 별로 처리. 즉 ADR-018 적용은:
- **신규 코드 방향 (forward enforcement)**: D8 = MCT-112 (✅ MERGED)
- **기존 코드 방향 (retrospective audit)**: D1~D7 = MCT-113~117 (📋 신규 발의)

이 forward/backward 분리는 **ADR adoption template** 으로 가치 있음. 향후 cross-cutting ADR (예: ADR-019 = parallel agent isolation) 도:
- forward: 신규 agent spawn 시 worktree 강제 (MCT-118 예정)
- backward: 기존 working dir 정리 (별도 Story 후보)
로 분리해 발의하는 패턴 재사용 가능.

### 4.4 Same-session ADR adoption — RETRO-MCT-107-111 §8.6 relapse 와의 대조
RETRO-MCT-107-111 §8.6 은 ADR-020 작성 same-session 에서도 회고 자동 dispatch 가 발화 안 됐다고 진단 (system prompt re-inject 부재). **본 MCT-112 는 ADR-018 작성 same-session 에서 D8 enforcement 가 즉시 작동한 대조 사례**:
- ADR-020: workflow rule (LLM 의 procedural 행동 변경 필요) → same-session 적용 실패
- ADR-018 D8: artifact change (파일 작성 task) → same-session 적용 성공

→ **same-session ADR adoption 가능성은 ADR 의 종류에 따라 다름**:
- **Artifact-producing ADR** (template 작성, code refactor, config 변경): same-session 즉시 실행 가능 — Orchestrator 가 task 로 dispatch 하면 됨
- **Behavior-modifying ADR** (workflow rule, dispatch trigger, retro gate): system prompt re-inject 의존 → next-session 부터 적용

이 구분은 **PMOAgent §4 ADR 후보 발의 시 ADR 유형 명시** 의 가치를 시사. ADR draft `category` 필드에 "artifact" vs "behavior" 구분 가능 (예: `category: Architecture (artifact)` vs `category: Process & Governance (behavior)`).

---

## 5. ADR 후보 발의 (Orchestrator 회신용)

### ADR-018 D9 후보 (보류 — 1주 관측 후 재검토)
```
category: Process & Governance (behavior)
title: ADR-018 D9: PR body 체크리스트 CI 검증
trigger: D8 reviewer 수동 체크 의존 → silent skip 가능성
배경:
  - MCT-112 로 6 repo PR template 에 D1~D7 체크리스트 박제
  - 그러나 reviewer 가 체크 없이 LGTM 시 defensive pattern 누락 silent 통과
  - N/A 표시 시 사유 명시 강제 없음
문제:
  - 체크리스트 enforcement 가 reviewer 양심에 의존 → human-error 잔존
제안 결정:
  - phase-gate-mergeable.yml 또는 신규 .github/workflows/pr-body-check.yml 에서:
    a) PR body 에 `## Defensive coding checklist (ADR-018)` 섹션 존재 검증
    b) 모든 체크박스 `[x]` 또는 `[N/A]` 채워짐 검증
    c) `[N/A]` 인 경우 사유 텍스트 (≥10자) 동반 검증
  - 위반 시 PR check fail
보류 사유:
  - MCT-112 시점에서 reviewer 행동 데이터 0 → 실제 체크 누락률 측정 후 결정
  - 1주 정도 (예: 2026-05-16 회고) PR 흐름 관측 후 재검토 권장
예상 결과:
  - 체크리스트 enforcement 가 human → CI 의존으로 전환
  - silent skip 0건
```

### ADR-020 D2 후보 — Story template default §11 헤더 박제
```
category: Process & Governance (artifact)
title: ADR-020 D2: Story file template 에 §11 회고 헤더 default 박제
trigger: MCT-112 §11 헤더 부재 → ADR-020 D1 enforcement gap
배경:
  - ADR-020 D1 은 PMO 회고 자동 dispatch 의무화
  - 그러나 Story file template 자체에 `## 11. 회고` 헤더 default 부재
  - 결과: Story 작성 시 §11 헤더 누락 → PMO 가 사후 §11 추가 의존
문제:
  - 회고 누락 검출이 PMO 사후 audit 의존 → silent skip 잠재
제안 결정:
  - codeforge-pmo 또는 hub overlay 의 Story template (또는 Story 생성 자동화 스크립트) 에:
    a) `## 11. 회고 (PMO)` 헤더 default 박제
    b) 헤더 아래 "PMOAgent 가 채움 — Story 완료 시 자동 dispatch" placeholder
  - phase-gate workflow 에서 PR description / Story file 에 §11 헤더 존재 검증 (장기)
예상 결과:
  - 신규 Story 100% §11 헤더 사전 박제
  - PMO 회고 작성 시 헤더 추가 작업 0
```

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **Story file template 에 `## 11. 회고` 헤더 default 박제** — ADR-020 D1 의 enforcement gap 차단. MCT-112 사후 §11 추가 작업 회피.
2. **ADR 유형 분류 (artifact vs behavior) 표준화** — §4.4 same-session adoption 가능성과 직결. PMO ADR 후보 발의 시 `category` 필드에 명시.
3. **D8 enforcement 효과 1주 후 측정** — 2026-05-16 retro 시점에 6 repo 의 PR body 체크박스 체크율 / N/A 사유 명시율 측정 → ADR-018 D9 발의 결정 데이터.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Parallel agent dispatch (6 repo PR 작성) | ~40% |
| PR open + admin merge sweep | ~15% |
| Story file 작성 (MCT-112.md) | ~10% |
| ADR-018 reading + D8 spec 준비 | ~10% |
| 6 repo PR template 변경 검토 | ~10% |
| 회고 (이 문서) | ~15% |

→ 본 Story 는 **task execution 비율이 매우 높은 깨끗한 사례**. 정정 비용 0.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-018**: Defensive coding patterns (D8 = 본 Story trigger)
- **ADR-011**: CI standard (D9 PR template — 본 Story 가 horizontally compose)
- **ADR-020**: Story 완료 PMO 회고 게이트 (D1 enforcement gap = §3.2)
- **MEMORY** `feedback_admin_merge_autonomy.md`: 본 Story 6 PR sweep 자율 패턴 적용
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **선행 retro**: `RETRO-MCT-107-111-code-review-fix.md` — ADR-018 발의 → 본 Story enforcement → 본 retro 까지의 chain

---

## 9. Story §11 회고 pointer

MCT-112.md §11 (사후 추가 권장) 에 본 retro pointer 박제:
> §11 회고: `docs/retros/RETRO-MCT-112.md` 참조 (ADR-018 D8 6-repo enforcement, parallel dispatch 1.5분, ADR governance loop 2.5h closure).

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch)
**작성일**: 2026-05-09
