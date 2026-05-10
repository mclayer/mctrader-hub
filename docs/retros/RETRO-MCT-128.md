# RETRO-MCT-128 — deprecated agent 잔존 참조 감사 + hub 정리

**범위**: MCT-128 (mctrader-hub `.claude/_overlay/run-tests.sh` / `run-perf.sh` / `CLAUDE.md` + Story file 작성)
**기간**: 2026-05-11 (MCT-127 직후 동일 세션 연장 — RETRO-MCT-127 §5 (HIGH) 후속 후보 직접 이행)
**Trigger**: RETRO-MCT-127 §5 (HIGH) "6-repo deprecated agent spawn 잔존 감사" 권고 이행. codeforge-test 1.0.0 (MAJOR bump) 에서 TestAgent / StatefulTestAgent spawn 불가 상태 — 6-repo 잠재 risk 감사. doc-only / hub-only.
**Status**:
- mctrader-hub 단일 commit `fac49e4 docs(mct-128)`
- AC 4/4 (100%) — fix-clean (FIX 0)
- doc-only fast-pass (ADR-027) 적용 — review/test/security lane skip

**Story file**: `docs/stories/MCT-128.md` (§11 PMO 회고 본 RETRO 와 동시 박제)
**Repos**: `mctrader-hub` 단일 (4 file: CLAUDE.md / run-tests.sh / run-perf.sh / Story file)
**선행**: MCT-127 (codeforge plugin 4종 업그레이드) RETRO §5 (HIGH) 권고
**후행**: MCT-129 (5 impl repo CLAUDE.md 갱신) — step 6 (6-repo 동기화) 첫 propagate cycle SSOT

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (4 AC) | 실제 | 비고 |
|---|---|---|---|
| AC1 — `run-tests.sh` line 4 주석: TestAgent → IntegrationTestAgent (codeforge-test 1.0.0, ADR-055) | 의무 | done | 1 line edit |
| AC2 — `run-perf.sh` line 4 주석: 동일 갱신 | 의무 | done | 1 line edit |
| AC3 — CLAUDE.md `codeforge 업그레이드 프로세스` step 5 (deprecated agent grep) + step 6 (6-repo 동기화) 추가 | 의무 | done | 2 step 신설 |
| AC4 — historical docs (MCT-97 / 과거 spec / plan) 보존 | 의무 | done | 변경 없음 (회고 무결성 합의 RETRO-MCT-127) |

→ **Story scope 4/4 AC 100% 완료**. 계획 외 추가 변경 없음. RETRO-MCT-127 의 1 commit / fix-clean / fast-pass 패턴 그대로 계승. doc-only Story 모범 template 2회 연속 적용.

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-hub` | 1 commit (`fac49e4`) | main 직접 push (ADR-019 D6) |
| `.claude/_overlay/run-tests.sh` | 1 line 갱신 | 동일 commit 포함 |
| `.claude/_overlay/run-perf.sh` | 1 line 갱신 | 동일 commit 포함 |
| `.claude/_overlay/CLAUDE.md` | 2 line 신설 (step 5·6) | 동일 commit 포함 |
| `docs/stories/MCT-128.md` | 신규 작성 (Story file) | 동일 commit 포함 |

→ **단일 commit / 단일 repo / fix-clean**. RETRO-MCT-127 (1 commit) 와 동일 단순도. doc-only fast-pass 로 CI cycle 0회.

### 1.3 테스트 결과

doc-only Story — unit test 없음. **grep 검증으로 대체** (§6 Story file 명시).

| 검증 항목 | 결과 |
|---|---|
| run-tests.sh line 4 "IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055)" grep | 통과 |
| run-perf.sh line 4 "IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055)" grep | 통과 |
| CLAUDE.md `codeforge 업그레이드 프로세스` step 5 / step 6 grep | 통과 |
| 6-repo grep 활성 spawn 호출 (TestAgent / StatefulTestAgent) — 본 Story 사전 감사 | 0건 (pre-confirmed) |

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 작업 (4 AC) | 4 | 100% | 본 작업 |
| Cat A (pre-existing) | 0 | 0% | — |
| Cat B (self-discovered) | 0 | 0% | — |
| Cat C (다른 Story finish-up) | 0 | 0% | — |

→ **부수 fix 0%** — RETRO-MCT-127 와 동일 lane. doc-only Story 모범 template 안정화.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-hub` | `main` (직접 push) | done | (없음, ADR-019 D6) | done |

→ **1-repo Story** — RETRO-MCT-127 와 동일 단순도. cross-repo 협업 cost 0. 단, 본 Story 가 step 6 신설로 MCT-129 propagate cycle trigger 함.

---

## 2. Sonnet decider (§4 박제)

3 결정점 박제 (Story file §4):

| 결정 | 선택 | 근거 |
|---|---|---|
| Story 분리 | MCT-128 hub + MCT-129 multi-repo | 책임 분리, fix-clean 가능. hub SSOT 우선 박제 후 5 repo propagate 표준 분리 패턴 적용 |
| 정책 문서화 | CLAUDE.md 기존 섹션 확장 | 기존 `codeforge 업그레이드 프로세스` 섹션에 step 5·6 추가 (YAGNI). 신규 섹션 분리 거부 |
| historical docs | 보존 | 회고 무결성 (RETRO-MCT-127 합의) — MCT-97 / 과거 spec / plan 의 deprecated agent reference 변경 금지 |

→ decider 박제 정합. 추후 plugin agent removal 패턴 발생 시 본 §4 가 결정 근거로 referenced 가능.

---

## 3. 잠재 risk 가 실제로는 zero exposure 였던 lane

본 Story 의 가장 중요한 lane 발견 — RETRO-MCT-127 §5 (HIGH) 가정의 실증 검증:

### 3.1 사전 가정 vs 실제

- **RETRO-MCT-127 §5 (HIGH) 가정**: codeforge-test 1.0.0 에서 spawn 불가가 된 TestAgent / StatefulTestAgent 가 6 sister repo 의 `.github/workflows/`, `scripts/`, `docs/stories/`, agent override, hook 어딘가에 활성 spawn 으로 잔존 → Story phase 진입 시 silent fail risk
- **MCT-128 실제 grep 결과**: 활성 spawn 호출 **0건**. mctrader-hub 의 `run-tests.sh` / `run-perf.sh` 주석 2개에만 historical reference 잔존 (실행 영향 0)

### 3.2 zero exposure 이유 분석

- **plugin loader 차단**: codeforge-test 1.0.0 plugin 의 `agents/` 경로에 TestAgent / StatefulTestAgent 가 존재하지 않음 → spawn 시도 자체가 plugin loader 단계에서 차단
- **consumer 의존 contract 단순**: mctrader 6-repo 가 plugin 의 agent contract 만 의존, plugin 내부 agent 명에 직접 binding 한 코드 부재
- **historical reference 의 격리**: 잔존 reference 는 모두 comment / docstring / prompt 내부에 있음 — 실행 contract 와 무관

### 3.3 MAJOR bump risk assessment lane 박제

본 결과는 향후 동일 패턴 (plugin agent removal / contract version bump / agent rename) 발생 시 **사전 risk 평가 단축** 가능:

1. plugin loader 차단 여부 확인 (plugin `agents/` 경로 grep)
2. consumer 잔존 risk = comment / docstring grep 만 필요 — 실행 contract 변경 없음
3. IDE/agent prompt 가 historical reference 보고 deprecated agent 호출 시도 시 사용자 confusion 가능 → 주석 갱신으로 차단

→ **lane 단축 effect**: 다음 plugin agent removal Story 는 ① + ② step 만 실행, 활성 spawn 잔존 가정의 conservative escalation 회피 가능. 단, 본 단축은 plugin loader 가 deprecated agent 를 제거하는 contract 가 보장될 때만 적용.

---

## 4. RETRO 권고 → 다음 Story 직접 이행 lane 입증

본 Story 가 RETRO-MCT-127 §5 (HIGH) "6-repo deprecated agent spawn 잔존 감사" 후속 후보의 **직접 이행**:

### 4.1 RETRO → 다음 Story 우선순위 결정 입력 lane

| 단계 | 시점 | 결과 |
|---|---|---|
| RETRO-MCT-127 §5 박제 | 2026-05-10 | (HIGH) 후속 후보 1개 발의 |
| MCT-128 trigger | 2026-05-11 | (HIGH) 후보 직접 이행 결정 |
| MCT-128 실행 | 2026-05-11 | hub-only Story + MCT-129 multi-repo Story 분리 |
| MCT-128 완료 | 2026-05-11 | fix-clean, governance step 5·6 박제 |

→ `feedback_pmo_retro_mandatory.md` 의 효용 입증. RETRO 가 단순 박제가 아닌 **다음 Story 의 우선순위 결정 입력**으로 작동. PMOAgent 자동 dispatch lane 의 ROI 가시화.

### 4.2 lane 표준화 권고

추후 RETRO 의 (HIGH) 후속 후보는 다음 Story trigger 시 우선 검토 의무화 권고:

- (HIGH) → 다음 Story trigger 자동 검토
- (MED) → 다음 2 Story 내 검토
- (LOW) → backlog 보관, scope match 시 trigger

→ 본 lane 이 자동 동작하면 RETRO 박제 cost 가 미래 우선순위 결정 cost 절감으로 회수.

---

## 5. step 5·6 추가의 governance 가치

CLAUDE.md `codeforge 업그레이드 프로세스` 섹션에 추가된 2 step 의 effect:

### 5.1 step 5 (deprecated agent grep)

- **의무**: plugin upgrade 시 CHANGELOG 의 deprecated agent / contract / hook 명을 6-repo 에 grep
- **trigger**: 본 Story 가 ad-hoc 으로 실행한 lane 을 표준 step 으로 박제
- **effect**: 추후 plugin upgrade Story 진입 시 즉시 grep 검토 trigger 작동. RETRO-MCT-127 §6 의 개선 제안 ("CHANGELOG → CLAUDE.md 반영 grep 자동화 script 부재") 의 부분 이행 — script 자동화는 defer, governance step 으로 박제

### 5.2 step 6 (6-repo 동기화)

- **의무**: hub CLAUDE.md SSOT 갱신 후 5 impl repo (MCT-129) 으로 propagate
- **trigger**: RETRO-MCT-126 / 127 에서 hub-only Story 와 multi-repo Story 분리 패턴 반복 → step 으로 박제
- **effect**: hub-only doc Story 후 자동으로 propagate Story trigger. MCT-129 가 첫 propagate cycle 실행

### 5.3 governance 박제 우선 ROI

| lane | cost | benefit |
|---|---|---|
| governance step 박제 (본 Story) | 2 line CLAUDE.md edit | upgrade Story 진입 시 cognitive trigger 작동 |
| 자동화 script (defer) | script 작성 + 유지보수 | grep 자동 실행, but plugin upgrade 빈도 낮음 |

→ **결론**: 자동화 script 보다 governance step 박제가 ROI 우선. plugin MAJOR bump 빈도가 분기당 2회 이상 발생 시 자동화 재검토 (현재 분기 1회 빈도).

---

## 6. RETRO-MCT-127 대비 lane 비교

| 항목 | RETRO-MCT-127 | RETRO-MCT-128 |
|---|---|---|
| commit 수 | 1 (hub 1) | 1 (hub 1) |
| AC 충족률 | 4/4 (100%) | 4/4 (100%) |
| Cat A/B/C fix 비율 | 0% / 0% / 0% | 0% / 0% / 0% |
| CI cycle | 0 (doc-only fast-pass) | 0 (doc-only fast-pass) |
| Sonnet decider 결정점 | 3 | 3 |
| 자동 dispatch 게이트 충족 | done | done |
| RETRO 권고 → Story 이행 | (HIGH) 발의 | (HIGH) 직접 이행 ← 본 Story |

→ **doc-only Story 모범 template 2회 연속 적용**. 단일 trigger / single purpose / decider 박제 / fix-clean / fast-pass / 1 commit. 추후 doc-only Story 는 본 template 2 사례 (MCT-127 + MCT-128) 를 reference 로 사용 가능.

---

## 7. 위반 / 개선 사항

**위반 없음**:
- AC 100% 충족
- fix-clean (FIX 0)
- §11 회고 자동 dispatch (`feedback_pmo_retro_mandatory.md`) 게이트 충족 — 2 Story 연속 (MCT-127 + MCT-128) 자동 dispatch lane 유지

**개선 제안 1건**:
- **5 impl repo CLAUDE.md propagate 자동화 script 부재** — step 6 신설로 governance 의무화 됐으나, 5 repo 의 CLAUDE.md 동시 갱신은 여전히 수동. `scripts/claude-md-propagate.ps1` (hub CLAUDE.md 변경분을 5 repo 에 patch 적용) 신규 lane 검토. 단, MCT-129 실행 후 ROI 재평가 — 1회 propagate cost vs script 작성 cost 임계 확인 필요.

---

## 8. Cross-Story 패턴 메모 (PMO 횡단 감사용)

본 RETRO 가 향후 cross-Story 패턴 분석 (PMOAgent §3 책임) 시 referenced 될 항목:

- **doc-only Story 모범 template 2회 연속 적용 (MCT-127 + MCT-128)** — 추후 plugin upgrade / governance Story reference template
- **잠재 risk 가 zero exposure 였던 lane 박제** — plugin agent removal 의 risk assessment 단축 가능 (§3.3 3-step lane)
- **RETRO 권고 → 다음 Story 직접 이행 입증** — `feedback_pmo_retro_mandatory.md` ROI 가시화. (HIGH) 후속 후보의 자동 우선 검토 lane 표준화 권고
- **governance step 박제가 자동화 script 보다 우선 ROI** — plugin MAJOR bump 분기당 2회 이상 시점에서만 자동화 재검토
- **hub-only + multi-repo SSOT propagate 분리 표준화** — MCT-128 (hub) + MCT-129 (5 impl repo) 패턴이 step 6 신설로 박제됨. 추후 동일 패턴 자동 분리 trigger

---

**Status**: done — 본 RETRO 박제로 §11 PMO 회고 자동 dispatch 게이트 충족 (`feedback_pmo_retro_mandatory.md`). MCT-129 (5 impl repo CLAUDE.md 갱신, step 6 첫 propagate cycle) 즉시 우선 진행 권고.
