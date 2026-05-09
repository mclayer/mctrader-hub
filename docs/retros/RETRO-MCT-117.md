# RETRO-MCT-117 — ADR-018 소급 audit · mctrader-web

**범위**: MCT-117 (단일 Story · 단일 repo `mctrader-web`)
**기간**: 2026-05-09 (single-day, MCT-112/113/114/116 same-session sweep 의 마지막 audit)
**Trigger**: ADR-018 Accepted — MCT-111 fix sweep 이후 잔여 위반 소급 audit
**Status**: MERGED (mctrader-web PR #33, 2026-05-09 14:35 UTC, admin merge)
**Story file**: `docs/stories/MCT-117.md`
**Repo**: `mctrader-web` (`c:\workspace\mclayer\mctrader-web`)

---

## 1. 결과 요약

### 1.1 ADR-018 D1~D7 audit 매트릭스

| 패턴 | MCT-111 처리 | MCT-117 잔여 fix | 비고 |
|---|---|---|---|
| **D1** field_validator | 일부 수정 | **FIXED 7건** | 7개 request model에 `@field_validator(mode="before")` strip + empty-string 거부 추가 |
| **D2** frozen+tuple | 일부 수정 | CLEAN | MCT-111 sweep 으로 차단 완료 |
| **D3** model_validator | — | CLEAN | cross-field 비즈니스 불변식 부재 (request DTO 도메인) |
| **D4** asyncio.Lock | — | **FIXED 1건** | `rate_limit.py` `threading.Lock` → `asyncio.Lock` + `async with _lock:` |
| **D5** atomic write | — | **FIXED 3건** | `auth.py` (token), `control_adapter.py` (PID), `wfo_lifecycle.py` (search_space + terminal_state ×2) — tmp+rename |
| **D6** case-insensitive | 일부 수정 | CLEAN | MCT-111 forbidden header `.lower()` 차단 완료 |
| **D7** governance flag | RBAC silently-reject 수정 ✅ | CLEAN | MCT-111 처리 |

→ **fix 11건 (D1×7 + D4×1 + D5×3), CLEAN 4건. 최종 위반 0.**

### 1.2 PR #33 변경 범위

- **+222 / −105**, 16 파일 (src 10 + tests 6)
- 5 commit (D1/D4/D5 fix → unused import 제거 → ruff fix → 추가 ruff → pyright fix)
- Merged 2026-05-09T14:35:10Z

### 1.3 테스트 결과

| 시점 | passed | failed | skipped |
|---|---|---|---|
| 사전 (D1/D4/D5 fix 전) | 493 | 0 | 5 |
| 사후 (모든 fix + ruff/pyright fix 후) | **493** | **0** | 5 |

→ 회귀 0. ADR-018 fix 가 기존 test contract 와 충돌 없음.

### 1.4 부수 fix (CI green 확보 — 본 Story scope 외)

| 카테고리 | 건수 | 내용 |
|---|---|---|
| ruff | 19 + 1 | E501/SIM105/SIM108/F811/F401/B905/C408 — pre-existing on main + 1 new |
| pyright | 19 | `_tier_symbols_stats` 반환 타입 `object` → `TierStats`, fixture `-> None` annotation 정리 등 |

**핵심 발견**: CI 가 ruff fail 시 pyright step skip → pre-existing pyright 오류 19건이 main 에 silent 누적. ruff fix 가 pyright 오류를 surface 함. (§3.1 상술)

---

## 2. 잘된 점

### 2.1 ADR-018 D1 sub-requirement 매트릭스 사전 박제 적용 (MCT-114 §6.1 권고 반영)

본 Story 는 RETRO-MCT-114 §6.1 권고 ("MCT-115/116/117 audit 시 D1 sub-requirement 5개 매트릭스 사전 박제") 가 **실제 적용된 첫 사례**. 7개 request model 에 `@field_validator(mode="before")` 추가 시 strip + empty-string 거부 두 sub-requirement 를 동시에 박제 — `whitespace-only string` 거부 누락 사후 발견 cost 0. MCT-114 같은 retroactive whitespace patch 재발 없음.

→ **PMOAgent §3 cross-Story 패턴 분석의 효과 실증**: retro 권고가 다음 Story 에 자동 반영되는 closed loop 가 작동.

### 2.2 D5 atomic write 3건 일괄 적용 — 도메인 횡단 패턴 인식

`auth.py` (token) / `control_adapter.py` (PID) / `wfo_lifecycle.py` (WFO state) 3개 파일은 도메인이 다르나 **모두 "in-process state → disk persistence" 패턴**. 단일 sweep 에서 3건 동시 식별 + tmp+rename 적용 → 부분 fix 후 cascade 잔존 회피. RETRO-MCT-116 §1 "wfo/decision_group.py 가 이미 atomic write 패턴 보유" 발견과 합쳐 **mctrader 전체 도메인에서 atomic write 가 critical durability 요건** 임을 누적 확인.

### 2.3 D4 asyncio.Lock 변환 — async helper 일관성

`rate_limit.py` `threading.Lock` → `asyncio.Lock` 변환 시 helper 함수도 모두 `async def` + `async with _lock:` 로 변환. **부분 변환 (lock 만 변경하고 helper 는 sync) 회피** — ADR-018 D4 의 의도 (async context 에서 thread lock 사용 시 GIL 양보 점 silent 추가) 를 정확히 해결.

→ ADR-018 D4 의 enforcement 가 단순 `s/threading.Lock/asyncio.Lock/g` 가 아니라 surrounding async semantics 도 함께 변경해야 함을 실증. 향후 D4 audit Story 의 reference pattern.

### 2.4 admin merge autonomy 적용 (5번째 same-session 사례)

PR #33 CI green 즉시 admin merge. 본 세션 5건 (MCT-112 sweep 6 PR + MCT-113 #8 + MCT-114 #11 + MCT-116 #43 + MCT-117 #33) 누적 적용. MEMORY `feedback_admin_merge_autonomy.md` 패턴이 same-session 다중 Story 에서도 일관적으로 작동.

---

## 3. 발생한 이슈

### 3.1 [MEDIUM] CI fail-fast 가 pre-existing pyright 오류 19건을 silent 누적시킴

**관측**:
- D1/D4/D5 fix commit 후 CI 첫 실행: ruff fail (19건 pre-existing + 1 new) → pyright step **skip**
- ruff fix 후 두 번째 CI: pyright fail (19건 pre-existing) **surface**
- 즉 본 Story 가 fix 한 ruff 19건과 pyright 19건은 **사전부터 main 에 잠복**, 본 Story 는 이를 노출시켜 정리한 것

**근본 원인 분석**:
- `.github/workflows/*.yml` 의 quality job 이 ruff → pyright 순차 실행 + ruff fail 시 fail-fast
- pyright step 이 ruff 통과 후에만 실행 → ruff fail 상태 main 이라면 pyright 오류는 영구히 invisible
- mctrader-web main 이 어느 시점부터 ruff fail 상태로 진입했는지 확인 필요 (MCT-111 이후로 추정)

**의미**:
- **CI fail-fast 패턴의 silent debt 누적** — quality gate 가 fail-fast 면 첫 실패 이후 다른 검증은 영구히 검증 안 됨
- mctrader-web 만의 문제일 가능성 ↔ 다른 5 repo 도 동일 구조일 가능성 — 검증 필요
- MCT-111 fix sweep 시점에 ruff 가 broken 됐다면 그 시점부터 pyright debt 가 누적 silent
- main branch 가 quality gate 일부만 검증된 채로 머지 가능 → 본질적 ADR-011 (CI standard) 갭

**평가**:
- 신규 ADR 후보 발의 사유 충분 — **ADR-018 D9 후보 또는 ADR-011 amendment 후보**
- 핵심: quality gate 가 fail-fast (직렬) 가 아니라 **all-must-pass (병렬)** 이어야 함
- §4.1 ADR 후보 발의 참조

### 3.2 [LOW] Story scope 외 부수 fix 비중 (ruff 20 + pyright 19) 가 본 fix (D1×7 + D4×1 + D5×3) 와 비등

**관측**:
- 본 Story 본 scope: 11 fix (D1×7 + D4×1 + D5×3)
- CI green 확보 부수 fix: 39 fix (ruff 20 + pyright 19)
- 즉 부수 fix 가 본 fix 의 ~3.5배

**근본 원인 분석**:
- §3.1 의 결과 — pre-existing CI debt 가 본 Story PR 에서 갑자기 surface
- 본 Story 가 새로 도입한 violation 은 ruff 1건뿐, 나머지 38건은 pre-existing
- "내 PR 이 깨뜨렸다" 가 아니라 "내 PR 이 잠복 debt 를 노출시켰다"

**의미**:
- Story 비용 산정 misestimate — D1/D4/D5 fix 11건만 예상했으나 실제 비용 50건 fix
- 부수 fix 비용을 별도 Story 로 분리할지 vs 본 PR 에 포함할지 결정 기준 없음
- 본 Story 는 포함 결정했으나 (작업 흐름 끊지 않기 위해) → PR description 에 두 카테고리 분리 권장

**평가**:
- 본 Story 만의 문제가 아님 — CI debt 누적 패턴이 발견될 때마다 어느 Story 가 청소 부담을 질지가 임의적
- §4.2 PMO 권고 참조 (CI debt 청소 별도 Story 분리)

### 3.3 [LOW] threading.Lock 의 asyncio 환경 silent 사용 — ADR-018 D4 미적용 잠재 패턴

**관측**:
- `rate_limit.py` 의 `threading.Lock` 은 asyncio FastAPI 환경에서 **동작은 함**
- 그러나 ADR-018 D4 기준 위반 — async context 에서 thread lock 은 GIL 양보 점 silent 추가
- 즉 "동작하므로 OK" 가 아니라 "ADR D4 의 설계 의도 위반"

**근본 원인 분석**:
- async/await 패턴이 코드 전반에 적용된 repo 에서 일부 라이브러리 코드 (rate_limit.py) 가 sync 패턴 잔존
- 작성 당시 (MCT-111 sweep 이전) ADR-018 D4 부재 → 작성자가 thread lock 선택의 위험성 미인지

**의미**:
- ADR-018 D4 가 정의한 "async context 에서 thread lock = silent semantic violation" 가 mctrader-web 에서만 발견됐는가? 다른 5 repo 의 async 코드 (특히 mctrader-data 의 stream consumer, mctrader-engine 의 async runner) 에서 잠재적 미발견 가능

**평가**:
- 본 Story 에서는 1건 (rate_limit.py) 만 발견. 다른 repo 의 async 코드 추가 audit 가치 있음
- §5 cross-Story 인사이트 참조

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] ADR-018 D9 또는 ADR-011 amendment 후보 — CI quality gate fail-fast 폐지

```
target_adr: ADR-011 D-NN amendment OR ADR-018 D9 신규
amendment_type: behavior (CI workflow 변경)
trigger: MCT-117 §3.1 — ruff fail 시 pyright step skip → 19건 pre-existing pyright 오류 silent 누적
배경:
  - mctrader-web .github/workflows/*.yml quality job 이 ruff → pyright 순차 실행
  - ruff fail 시 fail-fast → pyright 영구 skip
  - 결과: main 이 ruff 통과 못 하는 기간 동안 pyright debt 가 누적 invisible
  - MCT-117 PR 이 ruff 청소 후 19건 pyright 오류 surface
문제:
  - quality gate 의 일부만 검증된 채로 main 머지 가능
  - debt 누적이 우연히 노출될 때까지 silent
  - "어느 Story 가 청소 부담을 질지" 가 임의적
제안 결정:
  a) quality job 의 ruff/pyright/pytest 를 병렬 step (각각 독립 실패 보고)
     - 각 도구별 별도 GitHub check
     - 한 도구 실패가 다른 도구 검증을 차단하지 않음
  b) 또는 fail-fast 유지 + 별도 daily quality audit workflow 추가
     - main 에 nightly 로 모든 도구 강제 실행 → debt 추적
     - debt 발견 시 자동 issue 생성
  c) 6 repo 전체 적용 — 본 갭이 mctrader-web 만의 문제인지 검증
예상 결과:
  - quality gate debt silent 누적 0
  - PR 작성자가 자신의 변경 범위와 무관한 debt 청소 부담 회피
  - debt 추적이 reactive (PR 노출) 가 아닌 proactive (nightly)
보류 사유:
  - 본 사례 1건 (mctrader-web 만 확인) → 다른 5 repo CI workflow 사전 점검 권장
  - Codex 또는 별도 audit Story (MCT-119 후보) 로 6 repo CI workflow 매트릭스 작성 후 ADR 박제
```

### 4.2 [MEDIUM] PMO process 권고 — pre-existing CI debt 발견 시 별도 Story 분리 기준

```
target_adr: 신규 ADR 불필요 (PMOAgent.md §3 cross-Story 인사이트 영역)
amendment_type: PMOAgent.md retro 권고 표준화
trigger: MCT-117 §3.2 — 본 fix 11건 vs 부수 fix 39건 (3.5배)
배경:
  - 본 Story 는 부수 CI debt 청소를 PR 에 포함 결정 (작업 흐름 끊지 않기 위해)
  - 그러나 부수 fix 가 본 fix 를 압도 → Story 비용 산정 misestimate
  - 결정 기준 부재: 어느 비율부터 별도 Story 로 분리할지
문제:
  - 본 Story PR description 이 두 카테고리 (본 fix vs CI debt 청소) 를 분리해 명시했으나, retrospective 비용 분석 도구 부재
  - 다음 Story 가 동일 패턴 발견 시 분리 vs 포함 임의 결정
제안 결정:
  - PMO retro 에 "부수 fix 비율" 측정 표준화:
    a) 본 fix LoC vs 부수 fix LoC 측정
    b) 부수 fix > 본 fix 의 50% 시 retro 에 명시
    c) 부수 fix > 본 fix 의 200% 시 별도 follow-up Story 발의 권장
  - 본 사례는 350% → MCT-118 후속 또는 MCT-119 (CI quality gate amendment Story) 와 묶어 처리
예상 결과:
  - Story 비용 산정 정확도 향상
  - CI debt 누적 패턴 trace
```

### 4.3 [LOW] mctrader 전 repo async lock audit 후보 — D4 silent 잠재 위반

```
target: 신규 audit Story 후보 (예: MCT-120)
trigger: MCT-117 §3.3 — rate_limit.py threading.Lock 잠재 위반 패턴
배경:
  - mctrader-data (stream consumer), mctrader-engine (async runner) 도 async 코드 다수 보유
  - threading.Lock 사용 잠재 가능성 (sync 코드와 async 코드가 layer 별로 섞임)
  - ADR-018 D4 enforcement 가 본 5 audit Story (MCT-113~117) 만으로 충분한가?
문제:
  - threading.Lock 은 grep 패턴이 단순 (`threading.Lock\(\)`) 하므로 6 repo 사전 sweep 가능
  - sweep 결과에 따라 추가 audit Story 발의 또는 skip
제안 결정:
  - PMOAgent §3 cross-Story 분석 시 6 repo 전체 `threading.Lock` grep
  - 발견 0건이면 skip, 발견 ≥1건이면 audit Story 발의
예상 결과:
  - D4 enforcement 6 repo coverage 보장
보류 사유:
  - 본 retro §5 cross-Story 인사이트로 추적, 다음 PMO sweep 시 결정
```

---

## 5. Cross-Story 인사이트

### 5.1 ADR-018 5 audit Story 매트릭스 갱신 (RETRO-MCT-114 §4.3 채움)

RETRO-MCT-114 §4.3 의 "MCT-113~117 완료 후 채워질 매트릭스" 를 본 시점 (MCT-115 미완료 추정, MCT-117 완료) 까지 누적:

| Repo | Story | D1 | D2 | D3 | D4 | D5 | D6 | D7 | 잔여 fix 합 | PR |
|---|---|---|---|---|---|---|---|---|---|---|
| market-bithumb | MCT-114 ✅ | 1 | 3 | N/A | OK | N/A | OK | N/A | 4 | #11 |
| market | MCT-113 ✅ | OK | OK | **1** | N/A | N/A | N/A | N/A | 1 | #8 |
| data | MCT-115 (미확인) | ? | ? | ? | ? | ? | ? | ? | ? | — |
| engine | MCT-116 ✅ | OK | **다수** | **다수** | OK | **다수** | OK | OK | (RETRO 참조) | #43 |
| **web** | **MCT-117 ✅** | **7** | OK | OK | **1** | **3** | OK | OK | **11** | **#33** |

→ **누적 인사이트**:
- mctrader-web (본 Story) 가 D1 잔여 fix 7건 으로 단일 repo 최대 — request DTO 가 web 에 집중되는 도메인 특성
- D5 (atomic write) 위반은 web (3건) + engine (다수) — file persistence 가 있는 모든 repo 에 분포
- D4 (asyncio.Lock) 는 web 만 — asyncio FastAPI 가 web repo 의 핵심 패턴이라 surface 됨
- D2 (frozen+tuple) 위반은 market-bithumb + engine — domain model 보유 repo 에 집중
- D3 (cross-field validator) 는 market + engine — 복잡 비즈니스 불변식 보유 repo

### 5.2 ADR-018 audit Story 의 부수 비용 패턴 — MCT-117 가 outlier

| Story | 본 fix | 부수 fix | 비율 |
|---|---|---|---|
| MCT-114 | 4 (D1×1+D2×3) | ~0 | 0% |
| MCT-113 | 1 (D3) | ~0 (fixtures.py 개선만) | <50% |
| MCT-116 | 다수 (D2/D3/D5) | ~0 (fsync 보강만) | ~10% |
| **MCT-117** | **11** | **39 (ruff/pyright)** | **350%** |

→ MCT-117 만 부수 비용 outlier. 원인은 §3.1 CI fail-fast 로 mctrader-web 에 누적된 pre-existing debt. 다른 4 repo 는 동일 패턴 잠재 가능 — §4.1 ADR 후보 발의 근거.

### 5.3 same-session 5 Story sweep 의 token 효율

본 세션 (2026-05-09) 에서 처리:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 1건 fix)
- MCT-114 (D1/D2 4건 fix)
- MCT-116 (D2/D3/D5 다수 fix)
- MCT-117 (D1/D4/D5 11건 fix + 부수 39건)

→ **5 audit Story + D8 forward enforcement = single-day completion**. RETRO-MCT-112 §4.1 의 "ADR governance 2.5h closure" 가 5 audit Story 까지 확장돼 ~6h 내 완주 추정. codeforge ζ arc 의 ADR velocity 가 same-session multi-repo audit sweep 에도 작동.

### 5.4 Branch race re-test — 본 Story 는 발생 0

RETRO-MCT-113 §3.1, RETRO-MCT-114 §3.1, RETRO-MCT-116 §What Could Be Improved 에서 모두 branch race 발생. **본 MCT-117 는 발생 0**:
- 본 Story 는 mctrader-web repo 단일 working dir 에서 작업
- MCT-114 와 같은 multi-shell cwd 불일치 없음
- ADR-019 D4 branch guard 미적용은 동일하나 우연히 race 회피

→ branch race 는 **2-3 Story 에 1번 빈도** (3/5 sweep). ADR-019 D4 enforcement 자동화 가치 누적 확인. RETRO-MCT-113 §4.1 의 ADR-019 D6 후보 발의 정당성 강화.

### 5.5 same-session ADR adoption — artifact vs behavior 재실증

RETRO-MCT-112 §4.4, RETRO-MCT-113 §5.2 의 "artifact ADR same-session 성공 / behavior ADR same-session 실패" 패턴이 본 Story 에서도 유지:

- ADR-018 D1~D7 (artifact: 코드 패턴) → MCT-114/116/117 same-session 적용 **성공**
- ADR-019 D4 (behavior: branch guard) → MCT-113/114/116 same-session 적용 **실패** (race 발생)
- ADR-020 D1 (behavior: PMO 회고 dispatch) → 본 retro 작성으로 적용 (MEMORY trigger 의존)

→ 4건 누적 사례. **behavior ADR 의 enforcement 메커니즘 (Orchestrator self-reminder injection 등) 이 별도 ADR 또는 plugin overlay 로 박제 필요** — RETRO-MCT-113 §4.1 의 ADR-019 D6 후보 + RETRO-MCT-107-111 §8.6 의 ADR-021 후보 둘 다 1주 (2026-05-16) 추가 관측 후 결정 권장.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **CI quality gate fail-fast 6 repo 매트릭스 사전 점검** — §4.1 ADR 후보의 전제. mctrader-data / engine / market 등 다른 repo 의 `.github/workflows/*.yml` 점검 → fail-fast 패턴 확인 → ADR-011 amendment 또는 ADR-018 D9 발의 결정. 1주 내 (2026-05-16 이전) 완료 권장.

2. **6 repo `threading.Lock` grep sweep 자동화** — §4.3 D4 silent 위반 잠재 audit. 단순 grep 명령 (`Grep "threading.Lock\(\)" --type py` × 6 repo) 으로 5분 내 결정. 발견 0 이면 skip, ≥1 이면 audit Story 발의.

3. **PMO retro 표준 매트릭스 — 본 fix vs 부수 fix LoC 비율 측정** — §4.2 권고 표준화. RETRO-MCT-118 부터 적용. 부수 fix > 50% 시 retro 명시, > 200% 시 별도 Story 분리 권장.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| ADR-018 7패턴 mctrader-web 재스캔 (D1~D7 grep + Read) | ~20% |
| D1 7건 + D4 1건 + D5 3건 fix patch 작성 | ~25% |
| **부수 ruff 19건 fix (pre-existing CI debt 청소)** | **~15%** |
| **부수 pyright 19건 fix (ruff fix 후 surface)** | **~15%** |
| pytest 사전/사후 비교 + spec compliance review | ~10% |
| PR open + 5 commit iteration + admin merge | ~5% |
| Story file 갱신 (MCT-117.md) | ~5% |
| 본 retro 작성 | ~5% |

→ **부수 비용 ~30%** (RETRO-MCT-113 ~15% 의 2배). §3.1 CI fail-fast debt 누적이 본 Story 의 토큰 비용 ~30% 를 좌우. §4.1 ADR 박제 시 다음 audit Story 의 부수 비용 0 화 가능.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-018**: Defensive coding patterns (D1/D4/D5 = 본 Story 변경 패턴)
- **ADR-011**: CI standard (D9 quality gate fail-fast = §3.1 갭, §4.1 amendment 후보)
- **ADR-019**: Parallel agent isolation (D4 branch guard 미적용 — 본 Story 는 우연히 race 회피, §5.4)
- **ADR-020**: Story 완료 PMO 회고 게이트 (D1 본 retro 자동 dispatch trigger)
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #33 admin merge 자율 패턴 (5번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: §3.1 ruff/pyright 부수 fix 자동 recovery 사이클 적용
- **MEMORY** `feedback_ci_terminal_states_classify.md`: PR #33 CI 상태 자동 분류 (ruff fail → pyright skip surface)
- **선행 retro**:
  - `RETRO-MCT-107-111-code-review-fix.md` (ADR-018 발의 기원)
  - `RETRO-MCT-112.md` (D8 forward enforcement)
  - `RETRO-MCT-113.md` (D3 mctrader-market audit)
  - `RETRO-MCT-114.md` (D1/D2 mctrader-market-bithumb audit, §6.1 권고 본 Story 적용)
  - `RETRO-MCT-116.md` (D2/D3/D5 mctrader-engine audit)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-117.md` 에 §11 헤더 부재 (RETRO-MCT-112 §3.2 와 동일 ADR-020 D1 enforcement gap). 사후 §11 추가 시 본 retro pointer 박제:

> §11 회고: `docs/retros/RETRO-MCT-117.md` 참조 (ADR-018 D1×7 + D4×1 + D5×3 fix, pytest 493 green, PR #33 MERGED, 부수 ruff 20 + pyright 19 CI debt 청소, §3.1 CI fail-fast silent debt 누적 발견 → ADR-011 amendment 후보 §4.1).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 적용 (MCT-118 이후)

- **CI workflow 6 repo 매트릭스 점검** (§6.1) — fail-fast 패턴 확인
- **`threading.Lock` 6 repo grep sweep** (§6.2) — D4 잠재 위반 audit
- **PMO retro 본 fix vs 부수 fix LoC 측정 표준화** (§6.3)

### 10.2 ADR 후보 (1주 관측 후 결정 — 2026-05-16)

- ADR-011 amendment 또는 ADR-018 D9: CI quality gate fail-fast 폐지 (§4.1)
- ADR-019 D6: branch guard enforcement 자동화 (RETRO-MCT-113 §4.1 + 본 §5.4 누적)
- ADR-021: 세션 종료 게이트 (RETRO-MCT-107-111 §8.6 발의, 본 §5.5 누적)

### 10.3 MCT-115 회고 누락 보강

본 시점에서 MCT-115 (mctrader-data audit) retro 미확인. 만약 MCT-115 가 완료됐는데 retro 가 작성 안 됐다면 ADR-020 D1 enforcement gap. PMOAgent 가 MCT-115 상태 확인 후 누락 시 별도 dispatch 권장.

### 10.4 MCT-117 같은 부수 debt 청소 패턴 — 별도 Story 분리 검토

본 Story 처럼 부수 fix 가 본 fix 를 압도하는 패턴 재발 시 §4.2 기준 적용. 청소 부담을 본 Story 가 떠안기보다 별도 quality debt 청소 Story (예: MCT-119 후보) 로 분리해 비용 trace 가능하게.

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-09
