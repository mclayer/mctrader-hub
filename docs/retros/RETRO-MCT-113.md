# RETRO-MCT-113 — ADR-018 소급 audit (mctrader-market)

**범위**: MCT-113 (단일 Story · 단일 repo `mctrader-market`)
**기간**: 2026-05-09 (MCT-112 직후 same-day)
**Trigger**: ADR-018 Accepted — MCT-107 fix sweep 이후 잔여 위반 소급 audit
**Status**: MERGED (mctrader-market PR #8, 2026-05-09 14:02 UTC)
**Story file**: `docs/stories/MCT-113.md`

---

## 1. 결과 요약

| 패턴 | MCT-107 처리 | MCT-113 잔여 fix | 비고 |
|---|---|---|---|
| D1 field_validator Decimal | ✅ | 잔여 0건 | `Decimal38_18` 등 1차 sweep 이미 차단 |
| D2 frozen=True + tuple | ✅ | 잔여 0건 | `OrderBook` 등 1차 sweep 이미 차단 |
| **D3 model_validator cross-field** | ✅ Order | **❌ → ✅ CandleModel 1건** | OHLCV 6 불변식 신규 추가 |
| D4 threading.Lock | N/A | N/A | 공유 mutable state 없음 |
| D5 atomic write | N/A | N/A | 파일 쓰기 없음 |
| D6 case-insensitive header | N/A | N/A | HTTP 헤더 처리 없음 |
| D7 governance flag | N/A | N/A | CLI entry point 없음 |

**변경 범위 (PR #8 기준)**: +144 / -9, 4 파일.

| 파일 | 변경 |
|---|---|
| `src/mctrader_market/candle.py` | `@model_validator(mode="after")` + 6 OHLCV 불변식 |
| `tests/test_candle.py` | `TestCandleModelOHLCVInvariants` 7 테스트 |
| `src/mctrader_market/fixtures.py` | `make_valid_candle` partial override 안전성 (비례 스케일링) |
| (4번째 파일) | 부수 수정 |

**검증**: pytest 63/63 GREEN (기존 56 + 신규 7). 회귀 0.

---

## 2. 잘된 점

### 2.1 ADR-018 D3 OHLCV 불변식 — Doji edge case 포함 7 테스트
6 불변식(`high >= open/close/low`, `low <= open/close`, `volume >= 0`)을 cross-field validator로 강제하면서 **Doji 캔들(`open==high==low==close`) 통과** 케이스를 별도 테스트로 박제. 단일 패턴 fix가 boundary case로 회귀하는 것을 사전에 차단. ADR-018 D3 SSOT 의 reference impl로 가치.

### 2.2 fixtures.py partial override 안전성 — silent failure 사전 차단
`make_valid_candle` 헬퍼가 caller 가 일부 OHLCV 필드만 override 할 때 **비례 스케일링** 으로 불변식을 자동 보존하도록 개선. 신규 OHLCV validator 가 추가되면서 기존 테스트가 깨지는 cascade 를 차단 — D3 enforcement 가 test fixture 까지 침투해야 한다는 사실의 실증.

### 2.3 ADR-018 7패턴 N/A 사유 명시
PR #8 description 표가 D4~D7 4개 패턴에 대해 **N/A 사유** 를 명시 (공유 state 없음 / 파일 쓰기 없음 / HTTP 헤더 없음 / CLI entry 없음). 이는 MCT-112 RETRO §3.1 "D8 reviewer 수동 체크 의존 + N/A 사유 명시 강제 부재" 갭에 대한 **자발적 보강 사례** — D9 CI 검증 도입 전에도 patch 작성자 측에서 SSOT 화 가능함을 입증.

### 2.4 vertical slice 단일 PR 완주
1 fix branch · 1 PR · 1 admin merge · 회귀 0건. MCT-107~111 sweep (5 repo · 16 PR · 30분) 의 microcosm. 본 Story 는 그 정형 패턴이 단일 repo single fix 로도 동일하게 작동함을 재실증.

---

## 3. 발생한 이슈

### 3.1 [HIGH] 브랜치 Race 재발 — feat/mct-113 → feat/mct-112 오커밋

**관측**:
- 구현 서브에이전트가 `feat/mct-112` 브랜치에 본 Story (MCT-113) commit 작성
- cherry-pick 으로 MCT-113 branch 에 이전 + MCT-112 branch reset 으로 복구
- 사용자 trigger 없이 self-detect → recover (admin merge autonomy 와 유사 자율성)

**근본 원인 분석**:
- ADR-019 D1 (parallel agent 시 worktree 의무) **미적용 상태에서의 단일 working tree race**.
- MCT-113 은 단일 repo 단일 Story 라 **순차 실행** 으로 분류돼 ADR-019 D1 worktree 의무 면제(=D4 fallback 적용)에 해당. 그러나 D4 (`git branch --show-current` commit 직전 guard) **도 미적용**.
- 즉 ADR-019 D1/D4 둘 다 미적용 상태였으며, working dir 가 직전 작업 (MCT-112) 의 branch 잔존 → 새 구현 에이전트가 **branch 전환 누락** 한 채로 commit.

**ADR-019 와의 관계**:
- ADR-019 는 **2026-05-09 본 세션 도중** Accepted 됐으나, MCT-113 작업 시점에 D4 branch guard 가 actually 적용됐는지는 **확인되지 않음** (실제로는 미적용). 이는 RETRO-MCT-107-111 §8.6 "same-session ADR adoption gap" 의 **재발 증거**.
- 즉 ADR-019 D4 가 박제됐어도 본 세션 후속 Story (MCT-113) 에서 자동 적용 안 됨. workflow rule 류 ADR 의 same-session relapse 패턴이 ADR-018 D8 (artifact ADR)→ MCT-112 의 same-session 성공 사례와 **정확히 대조** 되는 또 한 건의 사례 누적.

**평가**:
- 본 사례는 **신규 ADR 후보 발의 사유 미충족** (ADR-019 가 이미 정확한 해결책 박제) — **enforcement gap** 임.
- ADR-019 D4 branch guard 의 enforcement 메커니즘이 부재 (Orchestrator self-discipline 의존 → silent skip).
- 향후 reviewer/CI 가 commit 직전 branch 검증을 **자동** 수행하는 경로가 필요 — 이는 ADR-019 후속 D6 "Orchestrator preflight checklist 자동 inject" 후보.

### 3.2 [LOW] 코드 리뷰어 false-positive — "install path 오류" Critical 오인

**관측**:
- 구현 도중 코드 리뷰 서브에이전트가 "editable install path 가 잘못돼 site-packages 의 wheel 이 import 됨" 을 Critical 결함으로 보고
- 실제 검증: `pip show mctrader_market` 의 `Editable project location` 이 working dir 정확히 가리킴, local src 가 정상 로드됨. **false-positive**.

**근본 원인 분석**:
- 코드 리뷰어가 ADR-019 D3 (editable install Preflight) 의 검증 명령 (`pip show ... | Select-String "Editable"`) 을 **실행하지 않고** import path 패턴만 보고 추론.
- ADR-019 D3 의 "사후 확인" 명령 자체는 ADR 에 박제됐으나 코드 리뷰어 prompt 에 그 명령이 진단 trigger 로 연동돼 있지 않음.

**평가**:
- false-positive 1건 → 작업 비용 손실 작음 (검증 5분).
- 그러나 패턴화 가능성 존재: 향후 환경 의심 신호가 발생할 때마다 코드 리뷰어가 **추론 대신 ADR-019 D3 명령 실행** 을 default 로 삼으면 false-positive cost 0 화.
- **개선 방향**: 코드 리뷰어가 "환경/install/import 의심" 카테고리 finding 을 raise 하기 전 ADR-019 D2/D3 검증 명령 1회 실행 의무. 이는 코드 리뷰어 SOP 보강 — ADR-018 D9 (CI 검증) 와 **동일 차원의 enforcement 보강** 이지만 reviewer agent 영역.

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

본 retro 의 두 issue 는 **신규 ADR 발의보다 기존 ADR enforcement 보강** 이 적합하다는 판정. 따라서 PMOAgent §4 inline ADR draft 발의 **0건**, 대신 **기존 ADR amendment 후보 2건** 을 Orchestrator 에 보고:

### 4.1 ADR-019 amendment 후보 — D4 branch guard enforcement (자동화)
```
target_adr: ADR-019
amendment_type: D6 신규 추가 (또는 D4 보강)
trigger: MCT-113 same-session relapse — ADR-019 박제 후에도 D4 미적용 상태 commit race 재발
배경:
  - ADR-019 D4 는 commit 직전 branch 검증을 명시하나 enforcement 가 Orchestrator self-discipline 의존
  - same-session relapse: ADR Accepted 후 동일 세션 후속 Story 에서 자동 적용 안 됨
문제:
  - Branch guard 미실행 → commit race silent. self-detect 의존
제안 결정 (D6 후보):
  - Orchestrator 가 구현 에이전트 spawn 직전 prompt 에 다음 inject 의무:
    "이 Story 의 expected branch = <feat/mct-N>. 모든 commit 직전 git branch --show-current 확인."
  - 또는 git pre-commit hook 으로 .codeforge/expected-branch 파일 vs 현재 branch 비교
  - phase-gate-mergeable.yml 에 "expected_branch frontmatter ↔ actual PR head ref" 검증 (장기)
보류 사유:
  - ADR-019 작성 후 1 Story 에서만 재발 — 1주 추가 관측 후 재검토 권장
```

### 4.2 코드 리뷰어 SOP 보강 후보 — ADR-019 D2/D3 명령 default 실행
```
target_adr: 신규 ADR 불필요 (코드 리뷰어 SOP 영역)
amendment_type: codeforge-review CLAUDE.md 또는 plugin overlay 보강
trigger: MCT-113 install path false-positive — 추론으로 Critical raise
문제:
  - 코드 리뷰어가 환경 의심 신호 시 ADR-019 D2/D3 검증 명령을 실행하지 않고 추론만으로 판정
제안 결정:
  - 코드 리뷰어가 install/import/환경 카테고리 finding 을 raise 하기 전 ADR-019 D2/D3 명령 1회 실행 의무
  - 결과 attach 후에만 finding raise 가능
예상 결과:
  - false-positive 0
  - 실제 결함은 검증 명령 결과로 즉시 evidence 동반
```

→ 두 후보 모두 **신규 ADR 발의 X**, 기존 ADR/SOP 의 enforcement 보강 권고. ADR governance 인플레이션 회피.

---

## 5. Cross-Story 인사이트

### 5.1 ADR-018 audit Story 패턴 — 단일 repo single fix vs sweep
| Story | repo | 잔여 fix 건수 | PR | 비고 |
|---|---|---|---|---|
| MCT-113 | mctrader-market | 1 (D3) | #8 | **본 Story** |
| MCT-114 | mctrader-market-bithumb | (확인 필요 — 완료 상태 표기) | — | |
| MCT-115 | mctrader-data | 신규 | — | |
| MCT-116 | mctrader-engine | (완료 상태 표기) | — | |
| MCT-117 | mctrader-web | 신규 | — | |
| MCT-118 | (ADR-019 forward) | 신규 | — | |

→ MCT-113 잔여 1건은 **MCT-107 1차 sweep 의 high coverage 를 입증**. 즉 Codex 심층 리뷰 → ADR-018 박제 → 1차 fix → 소급 audit 4-step chain 에서 **소급 audit 의 ROI 가 repo 마다 크게 다를 수 있음**. mctrader-market 은 1건 (low ROI), 아직 audit 미완료 repo 들은 별개 분포 가능.

### 5.2 same-session relapse 의 두 ADR 카테고리 대조 (RETRO-MCT-112 §4.4 재실증)

| 카테고리 | 사례 | 결과 |
|---|---|---|
| **artifact ADR** (template, code, config) | ADR-018 D8 → MCT-112 6 PR | same-session **성공** |
| **behavior ADR** (workflow, branch guard) | ADR-019 D4 → MCT-113 commit race | same-session **실패** (relapse) |

→ MCT-113 의 §3.1 commit race 는 RETRO-MCT-107-111 §8.6, RETRO-MCT-112 §4.4 에 이어 **3번째 same-session relapse 사례**. 패턴이 견고히 확인됨. ADR-021 (세션 종료 게이트, RETRO-MCT-107-111 §8.6 발의) 가 이 갭을 닫는 데 도움 될 수 있으나, behavior ADR 의 same-session 적용은 별도 메커니즘 (Orchestrator self-reminder injection) 이 필요.

### 5.3 PMO §4 enforcement gap analysis 정착
본 retro 가 신규 ADR 발의 0건 + 기존 ADR amendment 2건 으로 마무리되는 것은 PMOAgent §4 의 "ADR 후보 발의" 가 **신규 발의에 편향되지 않고 기존 ADR enforcement 갭을 우선 진단** 하는 패턴으로 진화하고 있음을 시사. ADR governance 인플레이션 (ADR 수만 늘어나고 enforcement 는 약화) 회피.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **ADR-019 D4 branch guard enforcement 자동화 (D6 후보)** — Orchestrator 가 구현 에이전트 spawn 직전 expected-branch reminder 를 prompt 에 inject. 1주 (~2026-05-16) 추가 관측 후 ADR-019 amendment 발의 결정.
2. **코드 리뷰어 환경 의심 finding 의 evidence 의무화** — ADR-019 D2/D3 명령 1회 실행 결과 attach 후에만 finding raise 가능. codeforge-review SOP 보강.
3. **PMO retro 에 "신규 ADR 발의 vs 기존 enforcement 보강" 결정 표준화** — 본 retro §4 처럼 두 옵션 명시 비교 후 선택. ADR 인플레이션 회피의 관행화.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| ADR-018 7패턴 mctrader-market 재스캔 | ~25% |
| CandleModel D3 fix + 7 테스트 작성 | ~30% |
| fixtures.py partial override 개선 | ~10% |
| **commit race 발견 + cherry-pick 복구** | **~10% (정정 비용)** |
| **코드 리뷰어 false-positive 검증** | **~5% (정정 비용)** |
| PR open + admin merge | ~5% |
| 회고 (이 문서) | ~15% |

→ **정정 비용 ~15%** (RETRO-MCT-107-111 의 ~10% 대비 증가). ADR-019 D4 enforcement 자동화 시 ~5% 절감 추정.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-018**: Defensive coding patterns (D3 = 본 Story 변경 패턴)
- **ADR-009**: OHLCV schema (CandleModel 의 16-col SSOT — D3 cross-field 불변식의 base)
- **ADR-013**: Indicator library contract (CandleModel 이 indicator input → 불변식 강화의 downstream 효과)
- **ADR-019**: Parallel agent isolation (D4 미적용 → §3.1 commit race)
- **MEMORY** `feedback_parallel_session_branch_race.md`: §3.1 재발 증거
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #8 admin merge 자율 패턴 적용
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **선행 retro**: `RETRO-MCT-107-111-code-review-fix.md` (MCT-107 1차 sweep), `RETRO-MCT-112.md` (D8 6-repo enforcement)

---

## 9. Story §11 회고 pointer

MCT-113.md §11 에 본 retro pointer 박제:
> §11 회고: `docs/retros/RETRO-MCT-113.md` 참조 (ADR-018 D3 CandleModel OHLCV 불변식 + same-session ADR-019 D4 relapse 1건).

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch)
**작성일**: 2026-05-09
