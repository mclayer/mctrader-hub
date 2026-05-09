# RETRO-MCT-114 — ADR-018 소급 audit · mctrader-market-bithumb

**범위**: MCT-114 (단일 Story · single repo)
**기간**: 2026-05-09 (single-day)
**Trigger**: ADR-018 Accepted (2026-05-09) — 기존 코드 D1~D7 7패턴 소급 audit. MCT-108 fix sweep 잔존 위반 탐지.
**Status**: MERGED (PR #11, admin merge)
**Story file**: `docs/stories/MCT-114.md`
**Repo**: `mctrader-market-bithumb`

---

## 1. 결과 요약

### 1.1 ADR-018 D1~D7 audit 매트릭스

| 패턴 | 판정 | 처리 내용 |
|---|---|---|
| **D1** field_validator | **FIXED (1건)** | `TickerEvent.chg_rate` Decimal\|None 필드에 `field_validator(mode="before")` 추가 — float/bool/int → Decimal 변환, whitespace-only / NaN / Inf / overflow 거부 |
| **D2** frozen=True + tuple | **FIXED (3건)** | (a) `adapter._parse_orderbook_levels` list → tuple, (b) `ws_events.OrderbookSnapshotEvent.bids/asks` list → tuple, (c) `OrderbookDeltaEvent.changes` list → tuple, (d) `ws_mapping` `tuple()` 변환 |
| **D3** model_validator | **N/A** | cross-field 비즈니스 불변식 부재 (orderbook 도메인 특성) |
| **D4** threading.Lock | **COMPLIANT** | `_TokenBucket` 가 이미 `threading.Lock()` 으로 check-then-decrement 원자화 |
| **D5** atomic write | **N/A** | 파일 쓰기 경로 부재 (REST/WS in-memory consumer only) |
| **D6** case-insensitive | **COMPLIANT** | MCT-108 forbidden header `.lower()` 수정 완료 — REST/WS 양쪽 검증 완료 |
| **D7** governance flag | **N/A** | CLI bypass flag 부재 |

→ **fix 4건, compliant 2건, N/A 3건. 최종 위반 0.**

### 1.2 테스트 결과

| 시점 | passed | failed | 비고 |
|---|---|---|---|
| 사전 (D2 fix 전) | 85 | 1 | `OrderBookModel` tuple 기대 실패 (active failure) |
| 사후 (D2 fix 후) | **86** | **0** | ✅ |

→ ADR-018 D2 (frozen+tuple) 적용이 **기존 active test failure 도 함께 해결**. 별도 fix 불필요.

### 1.3 PR

`mclayer/mctrader-market-bithumb#11` — MERGED to main (admin merge, 2026-05-09).

---

## 2. 잘된 점

### 2.1 subagent-driven-development 패턴 활용

ADR-018 7패턴 sweep 을 single subagent dispatch 로 처리. 입력: ADR-018 spec + repo 전체 source. 산출: 위반 항목 매트릭스 + fix patch + pytest log. **PMOAgent §1 분해 규칙 1 의 single-repo single-pattern audit 변형** — Story 단위는 작지만 sweep 범위가 명확해 subagent 가 deterministic 하게 완주.

### 2.2 스펙 컴플라이언스 리뷰에서 D1 whitespace 누락 발견

초기 D1 fix patch 가 `chg_rate` Decimal 변환만 처리, **whitespace-only string 거부** (`.strip() == ""`) 은 누락. 스펙 컴플라이언스 리뷰 단계에서 ADR-018 D1 spec 의 "공백 trim" 요구를 대조해 누락 발견 → 재패치 후 commit. 이 패턴은:
- ADR spec ↔ patch diff 의 line-by-line 매핑이 D1~D7 enforcement 의 필수 단계
- 단순 "Decimal validator 있음 → OK" 가 아니라 ADR D1 의 **5개 sub-requirement** (float 금지 / NaN / Inf / overflow / whitespace) 모두 검증

→ 향후 ADR-018 소급 audit Story (MCT-113, 115, 116, 117) 도 동일 sub-requirement 5개 별도 체크 권장.

### 2.3 ADR-018 D2 적용이 active failure 도 같이 fix

`OrderBookModel` tuple 기대 test 가 사전부터 1건 failing. ADR-018 D2 (list → tuple) 적용 시 **자동으로 green** 전환. 즉:
- D2 적용 = 외부 mutation 차단 (ADR 의도) + 기존 test contract 정렬 (부수 효과)
- 만약 ADR-018 없이 별도 fix 로 처리했다면 "test 만 맞추는 patch" → 외부에서 여전히 list 변형 가능
- ADR-018 D2 가 **structural fix** 임을 실증 (테스트 통과 ≠ 불변성 보장)

이는 ADR-018 의 가치 사례로 ADR-018 evidence section 에 추가 가능.

### 2.4 ws_events.py chg_rate 가 plain Decimal 인 점 식별

`Decimal38_18` 표준 타입이 아닌 plain Decimal 사용 필드도 ADR-018 D1 범위에 포함됨을 식별. 향후 cross-Story 시사:
- `Decimal38_18` 만 audit 하면 plain Decimal 필드 누락 → silent gap
- D1 audit 는 **Decimal 모든 변종** (Decimal38_18 / plain Decimal / Optional[Decimal]) 을 grep target 으로 잡아야 함

→ MCT-115, 116, 117 audit 시 grep pattern 에 `Decimal\b` 까지 포함 권장.

### 2.5 admin merge autonomy 적용

PR #11 CI green 즉시 admin merge. MEMORY `feedback_admin_merge_autonomy.md` 적용. 사용자 확인 wait 0.

---

## 3. 발생한 이슈

### 3.1 Branch race — PowerShell ↔ Bash shell cwd 불일치 (NEW pattern)

**증상**: 동일 hub 세션에서 PowerShell 과 Bash 두 shell 이 사용됐는데, `git` 명령이 어느 shell 에서 실행됐는지에 따라 **다른 cwd / 다른 branch** 에 위치. 결과:
- D1/D2 fix commit 이 **잘못된 branch** 에 land
- 발견 후 cherry-pick 으로 올바른 branch 로 이전 → 정상 PR open

**근본 원인 (가설)**:
- PowerShell 세션 cwd: `c:\workspace\mclayer\mctrader-hub` (hub repo)
- Bash 세션 cwd: shell 초기화에 따라 다른 working dir 가능
- claude 세션 내 두 shell 이 독립 cwd 를 유지 → user 가 의도한 `mctrader-market-bithumb` repo 가 아닌 곳에서 git 명령 실행

**MEMORY `feedback_parallel_session_branch_race.md` 와의 차이**:
- 기존 MEMORY: parallel session 들이 동일 working dir 공유 → branch checkout race
- 본 사례: **single session 내** 두 shell (PowerShell + Bash) 의 cwd 불일치 → branch state divergence
- 즉 새로운 sub-pattern. MEMORY 보강 필요.

**완화책**:
- shell 명령 직전 `pwd` (Bash) 또는 `Get-Location` (PowerShell) 로 cwd 검증
- 또는 모든 git 명령에 `-C <repo-path>` 명시 (cwd 비의존)
- **선호**: ADR-019 (parallel agent isolation = git worktree) 의 single-session 변형 — 작업 시작 시 worktree 확정 후 모든 명령이 worktree path 명시

### 3.2 Cross-shell branch state 검증 자동화 부재

본 Story 는 cherry-pick 으로 수동 복구. 그러나 만약 cherry-pick 단계에서 conflict / loss 가 발생했다면 silent commit loss 가능. 미래 갭:
- pre-commit hook 으로 "현재 branch 가 의도한 branch 와 일치하는가" 검증 (단, 의도가 무엇인지 hook 이 어떻게 알지가 문제)
- 또는 각 shell 명령 이전 brand+cwd assertion 를 작업 표준화

→ **ADR-019 D-NN 후보** (§5 참조).

---

## 4. Cross-Story 인사이트

### 4.1 ADR-018 소급 audit 시 list → tuple 변환의 active test failure 연쇄

본 Story 의 핵심 발견: **D2 적용이 기존 active test failure 도 함께 해결**. 일반화하면:

| 현상 | 의미 |
|---|---|
| ADR-018 소급 audit 시 D2 fix 가 active failure 도 같이 green 전환 | test contract 가 **이미 immutability 를 기대** 하고 있었으나 source 가 mutable 이라 불일치 |
| 즉 test ↔ source mismatch 가 ADR-018 발의 **이전부터** 잠복 | code review 가 "test 통과" 만 본 결과 silent skip |
| ADR-018 가 이를 surface | structural ADR 의 회귀 검출 효과 |

→ **MCT-113, 115, 116, 117 도 동일 패턴 가능성**. 각 repo 에서 ADR-018 D2 적용 시 사전 1건 이상 active failure 가 동반 해결될 가능성 ≥ 50% (가설). retro 에서 추적 권장.

### 4.2 Decimal validator audit 의 grep pattern 표준화

§2.4 발견 → ADR-018 D1 audit 의 **표준 grep pattern**:

```python
# 1차 grep: Decimal 타입 필드
^.*: (Decimal|Optional\[Decimal\]|Decimal\|None|Decimal38_18)
# 2차 grep: 해당 필드의 field_validator 부재 검증
field_validator\("<field_name>"
```

향후 MCT-115/116/117 (mctrader-data / engine / web) audit 시 동일 pattern 적용. PMOAgent §3 Cross-Story 패턴 분석 시 grep coverage 를 표준 산출물로.

### 4.3 ADR-018 enforcement 의 Story 단위 분포 (MCT-113~117 비교 시점)

본 retro 시점에서 MCT-114 만 완료. 그러나 5개 repo 별 D1~D7 위반 분포 가설:

| Repo | D1 예상 | D2 예상 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|---|
| market-bithumb (MCT-114) ✅ | 1건 | 3건 | N/A | OK | N/A | OK | N/A |
| market (MCT-113 예정) | ? | ? | ? | ? | ? | ? | ? |
| data (MCT-115 예정) | ? (Parquet) | ? | ? | ? | 다수 (lineage) | OK | ? |
| engine (MCT-116 예정) | ? (virtual.fill) | ? | ? (limit/overfill/qty) | ? (rate_limiter) | ? | OK | 1건 (--gate-d6-passed) |
| web (MCT-117 예정) | ? | ? | ? | ? | ? | OK | ? |

→ MCT-113~117 완료 후 Cross-Story retro 에서 위 매트릭스 채워 ADR-018 enforcement 효과 정량화.

### 4.4 PR #11 = MCT-112 PR template 이전 stage

본 Story PR #11 가 mctrader-market-bithumb 에 생성될 때, MCT-112 PR template (ADR-018 D8 6-repo 적용) 가 같은 repo 에 있었는지 확인 필요:
- MCT-112 commit 시점 (~14:00 UTC) vs MCT-114 PR 시점
- 만약 MCT-112 가 먼저 merge 됐다면 MCT-114 PR description 에 ADR-018 D1~D7 체크리스트 자동 첨부됨 → reviewer 가 D1 whitespace 누락을 더 빨리 발견 가능
- 만약 MCT-114 가 먼저 PR open 됐다면 체크리스트 없이 PR → 본 retro §2.2 처럼 사후 발견

→ **PR template enforcement timing 의 중요성**: ADR-018 D8 (PR template) 와 D1~D7 (소급 audit) 는 **D8 먼저, D1~D7 나중** 순서가 이상적. 본 케이스는 MCT-112 (D8) 와 MCT-114 (D1~D7 audit) 가 같은 날 동시 진행되어 dependency 가 명확하지 않았음. MCT-113/115/116/117 시점에서는 D8 가 이미 land 됐을 것이므로 PR template 효과 측정 가능.

---

## 5. ADR 후보 발의 (Orchestrator 회신용)

### ADR-019 D-NN 후보 — Single-session multi-shell cwd assertion

```
category: Infrastructure (artifact + behavior)
title: ADR-019 D-NN: Single-session multi-shell cwd/branch assertion
trigger: MCT-114 PowerShell ↔ Bash cwd 불일치로 인한 잘못된 branch commit + cherry-pick 복구
배경:
  - MEMORY feedback_parallel_session_branch_race 는 multi-session race 만 다룸
  - 본 Story 에서 single-session 내 PowerShell + Bash 두 shell 의 cwd 가 독립 → branch state divergence 발생
  - cherry-pick 으로 복구했으나 silent loss 가능성 잔존
문제:
  - 사용자 의도 repo (mctrader-market-bithumb) 와 실제 git 명령 실행 cwd 불일치 silent
  - cwd 검증 자동화 부재 → 사후 발견 의존
제안 결정:
  a) git 명령 실행 직전 cwd 검증 표준화:
     - Bash: `pwd | grep -q "<expected-repo>" || exit 1`
     - PowerShell: `if ((Get-Location).Path -notlike "*<expected-repo>*") { exit 1 }`
  b) 또는 모든 git 명령에 -C <abs-path> 명시 (cwd 비의존)
  c) 또는 ADR-019 worktree 정책의 single-session 변형 — 작업 시작 시 git worktree add 후 모든 명령이 worktree-abs-path 명시
보류 사유:
  - 본 사례 1건 → ADR 박제 전 추가 재발 관측 필요
  - MCT-115/116/117 진행 시 동일 패턴 재발 빈도 측정 후 결정
예상 결과:
  - branch state silent divergence 0건
  - cherry-pick 복구 의존 제거
```

### ADR-018 D1 audit grep pattern 표준화 (artifact ADR)

```
category: Process & Governance (artifact)
title: ADR-018 D-NN: 소급 audit 표준 grep pattern + sub-requirement 매트릭스
trigger: MCT-114 D1 whitespace 누락 발견 + ws_events.py chg_rate plain Decimal 식별
배경:
  - ADR-018 D1 은 5개 sub-requirement (float 금지 / NaN / Inf / overflow / whitespace)
  - 단순 "field_validator 있음 = OK" audit 시 sub-requirement 누락 silent
  - Decimal38_18 외 plain Decimal / Optional[Decimal] 필드도 audit 대상이나 grep miss 가능
문제:
  - 소급 audit 의 coverage 가 audit 수행자 grep skill 에 의존
  - sub-requirement 별 별도 검증 없이 통과 가능
제안 결정:
  a) ADR-018 본문에 표준 grep pattern 부록 추가:
     - Decimal 필드: `(Decimal|Optional\[Decimal\]|Decimal\|None|Decimal38_18)\b`
     - field_validator 매핑: 각 필드별 mode="before" + 5 sub-req 체크
  b) PMOAgent 회고 audit 에서 grep pattern coverage 를 표준 산출물로 요구
  c) MCT-115/116/117 Story 발의 시 D1~D7 별 sub-req 매트릭스 사전 박제
예상 결과:
  - 소급 audit miss 율 감소
  - sub-requirement 누락 silent 차단
```

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **MCT-113/115/116/117 audit 시 D1 sub-requirement 5개 매트릭스 사전 박제** — Story file §3 수행 절차에 "각 D-N 패턴별 sub-req 체크" 명시. 본 Story 의 §2.2 발견 재발 방지.
2. **single-session multi-shell cwd assertion 표준화** — git 명령 직전 cwd 검증 또는 `-C <abs-path>` 명시. §3.1 재발 방지.
3. **ADR-018 D2 적용 시 active test failure 동반 해결 여부 추적** — MCT-115/116/117 retro 에 `D2 fix 가 사전 failing test 를 같이 green 전환` 데이터 누적. ADR-018 의 structural value 정량화.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| ADR-018 spec 학습 + 7패턴 매트릭스 준비 | ~10% |
| repo 전체 sweep (grep + Read) | ~25% |
| D1/D2 fix patch 작성 + 스펙 컴플라이언스 리뷰 (whitespace 누락 발견 + 재패치) | ~25% |
| pytest 사전/사후 비교 | ~10% |
| Branch race 발견 + cherry-pick 복구 | ~10% |
| PR open + admin merge | ~5% |
| Story file §1-4 갱신 | ~5% |
| 본 retro 작성 | ~10% |

→ 본 Story 는 **§3.1 cherry-pick 복구 ~10%** 가 정정 비용. ADR-019 D-NN 박제로 회피 가능.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-018**: Defensive coding patterns (D1~D7 본 Story trigger)
- **ADR-008**: 관련 (Story frontmatter `related_adrs` 명시 — bithumb adapter 도메인 규약)
- **ADR-019**: Parallel agent isolation (§3.1 single-session 변형 후보)
- **ADR-020**: Story 완료 PMO 회고 게이트 (D1 본 retro 자동 dispatch trigger)
- **MEMORY** `feedback_parallel_session_branch_race.md`: §3.1 sub-pattern (single-session multi-shell) 보강 필요
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #11 admin merge 적용
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch
- **선행 retro**: `RETRO-MCT-107-111-code-review-fix.md` (ADR-018 발의 기원), `RETRO-MCT-112.md` (ADR-018 D8 forward enforcement)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-114.md` 에 §11 헤더 부재 (RETRO-MCT-112 §3.2 와 동일 ADR-020 D1 enforcement gap). 사후 §11 추가 시 본 retro pointer 박제:

> §11 회고: `docs/retros/RETRO-MCT-114.md` 참조 (ADR-018 D1~D7 audit, D1 1건 + D2 3건 fix, pytest 86 passed, PR #11 MERGED, branch race cherry-pick 복구).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 적용 (MCT-113 / 115 / 116 / 117)

- **D1 sub-requirement 5개 매트릭스 사전 박제** (§6.1)
- **Decimal grep pattern 확장** (`Decimal\b` 까지 — Decimal38_18 외 plain 포함, §4.2)
- **ADR-018 D2 적용 시 active failure 동반 해결 추적** (§4.1 가설 검증)
- **PR template ↔ audit timing 확인** (MCT-112 #11 merge 시점 vs 본 Story PR 시점, §4.4)

### 10.2 ADR 후보 (1주 관측 후)

- ADR-019 D-NN single-session multi-shell cwd assertion (§5) — 본 사례 1건이라 추가 재발 관측 후 결정
- ADR-018 D-NN 소급 audit 표준 grep pattern (§5)

### 10.3 MCT-113~117 완료 후 Cross-Story retro

- §4.3 매트릭스 채우기 (5 repo × 7 패턴 위반 분포)
- ADR-018 enforcement 효과 정량화
- §4.1 active failure 동반 해결 빈도 측정

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-09
