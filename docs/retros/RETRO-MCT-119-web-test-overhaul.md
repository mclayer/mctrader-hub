# RETRO-MCT-119-web-test-overhaul — mctrader-web 전체 테스트 보강 (Phase 1A 후속)

**범위**: MCT-119 follow-up — `mctrader-web` 측 테스트 인프라 및 커버리지 보강 (RETRO-MCT-119-120 §3.1 의 web 미푸시 패턴 회피 후 별도 PR 로 정상 진입)
**기간**: 2026-05-10 (single-day, signal-collector MCT-124 직후 동일 세션 연장)
**Trigger**: AppTest 5 페이지 + API gap 2 endpoint + Playwright E2E 4 flow 신규 — Strategy Set Pipeline (MCT-119 engine 측) 머지 후 web 측 테스트 백로그 청소, ADR-020 D1 자동 dispatch
**Status**: PR `mctrader-web#35` MERGED 2026-05-10T02:42:28Z (squash `6569f90`), 528 passed / 5 skipped / 12 deselected
**Story file**: `docs/stories/MCT-119.md` §11 (본 retro pointer 박제 — RETRO-MCT-119-120 와 동일 Story key 유지, "Phase 1A web overhaul" 후속 작업으로 트래킹)
**Repo**: `mctrader-web` (`c:\workspace\mclayer\mctrader-web`) 단일 — branch `feat/test-overhaul-mct-119`
**Plan**: `docs/superpowers/plans/2026-05-10-mctrader-web-test-overhaul.md`

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (7 Task) | 실제 | 비고 |
|---|---|---|---|
| Task 1 — pytest markers (`e2e`/`real`) + playwright dev dep + CI fixture JSON 3종 | 신규 | `f1a70d9` | 100% |
| Task 2 — AppTest 03_wfo_panel | 3 tests | `77810b1` + `c1e7fc2` (assertion robustness fix) | 100% |
| Task 3 — AppTest 04/05/06 strategy pages | 7 tests (3+2+2) | `666f225` | 100% |
| Task 4 — AppTest 20_data_collection | 4 tests, polling loop disable | `fd40cc8` | 100% (`session_state["dc_refresh"] = "수동"` 패턴 §2.2) |
| Task 5 — API gap (audit_query 10 + rbac_tokens 11) | 21 tests | `556c6c0` | 100% |
| Task 6 — Playwright E2E conftest + 4 flow tests | 12 tests, `@e2e` skip without server | `e6d6325` + `adbcfb0` (expect() auto-retry fix) | 100% |
| Task 7 — 전체 528 PASSED 검증 + PR + CI fix (e2e 제외) | green gate | `e3b160b` (CI marker 필터 fix) | 100% |

→ **7 Task 100% 완료**. 사용자 수동 의존 0. RETRO-MCT-124 §1.1 의 Task 8 PENDING (사용자 의존) 같은 case 없음 — 모든 작업이 자동화 lane 으로 종결.

### 1.2 PR #35 통계

- **+273 / −2**, **7 파일** (실제 PR `gh pr view` 기준 — `.github/workflows/ci.yml` 1 + `tests/e2e/` 6)
- **수정 영역 분포** (commit graph 기준 — apptest/api 신규 파일은 본 PR base branch 직전 commit `1aa5247` 이전에 stack 됐다가 squash 시점에 누적):
  - `tests/apptest/` 5 파일 (5 페이지 × 평균 2~7 test = 17 test 추가)
  - `tests/api/` 2 파일 (audit_query 10 + rbac_tokens 11 = 21 test 추가)
  - `tests/e2e/` 5 파일 (conftest + 4 flow = 12 test 추가, `@e2e` 마킹)
  - `tests/fixtures/` 3 JSON (coverage_stats / heartbeat / backtest_result sample)
  - `pyproject.toml` markers + playwright dev dep
  - `.github/workflows/ci.yml` `-m "not integration and not e2e"` 갱신 (CI fix)
- **commit 분포** (8 commit, 시간순):
  - 본 작업 6 commit: `f1a70d9` (Task 1) → `77810b1`/`c1e7fc2` (Task 2) → `666f225` (Task 3) → `fd40cc8` (Task 4) → `556c6c0` (Task 5) → `e6d6325` (Task 6)
  - 자체 발견 fix 2 commit: `adbcfb0` (Playwright `expect()` auto-retry — Task 6 직후), `e3b160b` (CI marker 필터 — Task 7 첫 CI 실패 후)
- Squash merge `6569f90` 2026-05-10T02:42:28Z (admin merge)

### 1.3 테스트 결과

| 카테고리 | passed | skipped | deselected | 비고 |
|---|---|---|---|---|
| AppTest 5 페이지 | 17 | 0 | 0 | 신규 |
| API gap 2 endpoint | 21 | 0 | 0 | 신규 |
| Playwright E2E 4 flow | 0 | 12 | 0 | `@e2e` 마킹 — 서버 없이 자동 skip |
| 기존 테스트 (회귀) | ~490 | ~5 | 12 | 0 회귀 |
| **합계** (`pytest tests/ -m "not e2e" --ignore=tests/integration -x -q`) | **528** | **5** | **12** | **105.45s** |

→ **528 PASSED, 0 회귀**. 신규 38 test (apptest 17 + api 21) + e2e 12 (skip-by-default) = **50 신규 test 추가**. RETRO-MCT-124 §1.3 의 31/31 PASS 와 비교 시 본 PR 은 더 많은 신규 test 추가에도 회귀 0.

### 1.4 CI 상태

| Check | 결과 |
|---|---|
| `ci` (CI workflow) | SUCCESS (1m13s) |
| CodeQL Analyze (actions / python) | SUCCESS / SUCCESS |
| `check-gate` (Phase Gate Mergeable cross-repo) | SUCCESS |
| `CodeQL` | SUCCESS |
| `phase-gate-mergeable` | FAIL (informational, non-blocking) |

→ 5 SUCCESS + 1 informational fail. **첫 시도 CI FAILURE → marker 필터 fix `e3b160b` 후 SUCCESS** — §3.1 참조.

### 1.5 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 + RETRO-MCT-121 §5.5 + RETRO-MCT-122-123 §1.4 + RETRO-MCT-124 §1.4 표준 적용)

| 카테고리 | commit 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 fix (7 task) | 6 | 75% | 본 fix |
| 자체 발견 fix — Playwright `expect()` auto-retry | 1 (`adbcfb0`) | 12.5% | **Cat B (self-discovered)** |
| 자체 발견 fix — CI marker 필터 e2e 제외 | 1 (`e3b160b`) | 12.5% | **Cat B** |

→ Cat B 25% (2 commit), 본 fix 75% (6 commit). **Cat A (pre-existing) 0, Cat C (다른 Story finish-up) 0**. RETRO-MCT-124 §1.4 의 Cat B 21% 와 유사 — **신규 테스트 인프라 단일 Story** 라 다른 카테고리 conflated 없음. 25% 는 "신규 코드 첫 CI 노출" 정상 범위 (RETRO-MCT-119-120 §5.2 의 17% 와 동일 lane).

---

## 2. 잘된 점

### 2.1 RETRO-MCT-119-120 §3.1 의 web 미푸시 scope 누수 패턴 회피 — branch 분리 원칙 적용

RETRO-MCT-119-120 §3.1 에서 web 측 Strategy Set UI/API 변경이 `feat/mct-117-adr018-audit-web` branch 위에 wrong-branch-stacked 됐던 패턴을 본 PR 에서는 `feat/test-overhaul-mct-119` 신규 branch 에서 시작 → cherry-pick 없이 자연스럽게 격리. **ADR-019 D1 의 worktree isolation 원칙이 branch 분리만으로도 부분 충족 가능 실증**. 본 PR base = `main` 직속, RETRO-MCT-119-120 §10.1 "follow-up Story 가칭 MCT-121" 권고와 다른 lane 으로 진행 (test 보강 = 별도 scope) 됐으나 branch 격리 원칙은 동일 적용.

### 2.2 Streamlit AppTest polling loop 무한루프 방지 패턴 발견

20_data_collection 페이지는 자동 갱신 polling loop (`time.sleep` 기반 streamlit `rerun`) 보유. AppTest 가 페이지 로드 후 polling loop 에 진입하면 timeout 까지 무한 대기. **해결**: AppTest setup 시 `at.session_state["dc_refresh"] = "수동"` 으로 자동갱신 비활성화 → 1회 render 후 즉시 assertion 가능. 본 패턴은 다른 Streamlit 페이지 (실시간 데이터 표시 dashboard 류) 에 일반화 가능 — §4.1 ADR 후보.

### 2.3 AppTest monkeypatch 타겟 — `from X import f` 모듈 속성 패치 작동 실증

페이지 코드에서 `from src.web.api_client import fetch_metrics` 형태의 import 를 사용해도 AppTest 가 페이지를 re-exec 하는 시점에 monkeypatch 가 모듈 속성에 적용돼 정상 작동. 일반적으로 `from X import f` 패턴은 import-by-value 라 직접 patch 가 불가하다는 잘못된 통념 해소 — **AppTest 의 re-exec 메커니즘이 import 시점 바인딩을 새로 만들기 때문**. 본 사실은 향후 Streamlit 측 mock-heavy 테스트 작성 비용을 낮춤.

### 2.4 Playwright `expect()` auto-retry 패턴 채택 — `assert locator.count() >= 1` 폐지

`adbcfb0` 에서 모든 4 flow test 의 `assert locator.count() >= 1` 를 `expect(locator).to_be_visible(timeout=10000)` 로 교체. **이유**: Streamlit 의 lazy render 와 WebSocket reconnect 가 첫 `count()` 호출 시점에 0 반환할 수 있음. Playwright 의 built-in auto-retry 가 timeout 안에서 polling → flake 차단. 본 결정은 향후 모든 E2E test 의 baseline 패턴으로 박제 권장.

### 2.5 admin merge autonomy + 자동 PMO 회고 dispatch (ADR-020 D1) — 8번째 same-session 사례

PR #35 CI green 즉시 admin merge → 사용자 trigger 없이 본 retro dispatch. ADR-020 D1 의 8번째 same-session 사례 (MCT-112/113/114/115/116/117/119+120 + MCT-121 + MCT-124 + 본 PR). MEMORY `feedback_admin_merge_autonomy.md` + `feedback_pmo_retro_mandatory.md` closed-loop 정착.

---

## 3. 발생한 이슈

### 3.1 [HIGH] CI marker 필터에서 `e2e` 제외 누락 — 신규 marker 도입 시 CI workflow 동시 갱신 누락

**관측**:
- 첫 CI run (`02:38:20Z`) FAILURE — `pytest -m "not integration"` 이 e2e 테스트를 실행 → Playwright 브라우저 미설치로 ERROR
- 수정 commit `e3b160b`: `.github/workflows/ci.yml` 에서 `-m "not integration and not e2e"` 로 갱신 → 두 번째 CI run (`02:40:50Z`) SUCCESS

**근본 원인 분석**:
- Task 1 에서 `pyproject.toml` 에 신규 marker `e2e`, `real` 등록 + Task 6 에서 4 flow test 가 `@pytest.mark.e2e` 사용
- **그러나 CI workflow 의 `-m` 필터는 갱신 누락** — pytest 가 수집된 e2e test 를 실행하려다 playwright 브라우저 미설치로 실패
- Plan Task 1 에 "CI workflow marker 필터 동시 갱신" 단계 부재
- **신규 pytest marker 도입 ↔ CI workflow 갱신 의존성 invisible**

**의미**:
- "신규 marker 도입 시 CI workflow `-m` 필터 자동 동기" 정책 부재
- 본 사례는 첫 CI 실행에서 즉시 surface 됐으나 (good — auto-recovery 사이클 1회로 회복), 더 복잡한 marker (예: `slow`, `gpu` 등) 추가 시 lateral effect 발견 지연 위험
- §4.1 ADR 후보 — pytest marker 도입 시 CI 워크플로 갱신 체크리스트

**평가**:
- 본 사례 1건 → 1주 관측 후 같은 패턴 재발 시 박제. 다만 root cause 명확 (marker 도입 → CI 필터 동기) 이므로 즉시 ADR 박제 가능.
- MEMORY `feedback_ci_failure_auto_recovery.md` 가 1 commit fix 로 회복 사이클 작동 — 비용 < 5분.

### 3.2 [MEDIUM] Streamlit AppTest polling loop 무한 대기 — 페이지 설계와 테스트 격리 사이 간격

**관측**:
- 20_data_collection 페이지가 자동 갱신 polling loop 보유 (`time.sleep` + streamlit `rerun`)
- AppTest 가 페이지 로드 후 loop 에 진입 → AppTest default timeout 까지 무한 대기
- 해결: `at.session_state["dc_refresh"] = "수동"` 으로 자동갱신 비활성화 후 AppTest 진행

**근본 원인 분석**:
- Streamlit 페이지의 polling loop 는 production runtime 패턴 (대시보드 자동 갱신 UX)
- 그러나 AppTest 는 single-render 환경 — loop 가 testing 환경에서는 dead-end
- 페이지 코드와 테스트 코드 사이 "auto-refresh disable hook" interface 부재
- 수동 session_state 조작으로 우회 가능했으나, 다른 페이지가 다른 키 (`refresh_mode`, `auto_poll` 등) 를 쓰면 패턴 재사용 불가

**의미**:
- Streamlit 페이지 작성 시 testing-aware design pattern (예: `if at_test_mode(): disable_polling()`) 표준화 필요
- 본 사례 1건 → 다른 polling 페이지 (예: 실시간 dashboard) 추가 시 동일 문제 재발 예상
- §4.2 ADR 후보 또는 mctrader-web internal convention 박제

**평가**:
- 본 사례 1 페이지 surface — 다른 polling 페이지 추가 시 누적 ≥3 사례 시 박제
- §2.2 의 발견 패턴 자체는 잘된 점이나, 페이지 설계 단계에서 invisible — testing-aware design 원칙으로 fold

### 3.3 [LOW] StatusResult 생성자 인자 순서 plan vs 실제 mismatch

**관측**:
- AppTest 작성 시 mock 으로 `StatusResult(nodes=[...], worst_level="green")` 형태로 호출 (plan 에서 명시한 순서)
- 실제 dataclass 정의는 `StatusResult(worst_level, nodes)` (positional) — plan 이 stale
- 사용자가 수동 검증 후 plan 정정, code 는 정상 작동

**근본 원인 분석**:
- Plan 작성 시 `StatusResult` 시그니처를 mctrader-web 코드 기준이 아닌 추정으로 기재
- Plan 작성자 (Sonnet decider 또는 사용자) 가 실제 코드 inspect 없이 순서 추측
- Plan ↔ 실제 코드 sync 부재

**의미**:
- Plan 의 시그니처·인자 순서 명시 시 **실제 코드 grep 검증 의무화** 필요
- 본 사례는 사용자 수동 정정으로 회복 — 자동 lane 에서 발견되지 않음
- §4.3 plan-writing checklist 강화 — "API/dataclass 시그니처는 grep 결과 paste 의무"

**평가**:
- 본 사례 1건 → 누적 ≥3 시 plan-writing skill 갱신
- 자동 lane (TDD 우선) 에서는 시그니처 mismatch 가 첫 test 실행 시 즉시 surface — 본 사례는 plan-paste-then-execute 패턴이라 surface 지연

### 3.4 [LOW] `use_multi_token_auth=False` 환경에서 admin endpoint 테스트 fixture 갭

**관측**:
- 기본 fixture 는 `use_multi_token_auth=False` (single static token, no role) 가정
- admin-only endpoints (`/admin/audit`, `/admin/rbac/tokens`) 는 admin role 필수 → 401/403
- 별도 multi-token fixture 작성 필요 (admin/operator/viewer role 각각 token 발급)

**근본 원인 분석**:
- 기본 fixture 가 single-token mode 만 고려 — multi-token mode 는 production-only 가정
- admin endpoint test 작성 시 fixture 확장이 invisible cost
- API gap test (Task 5) 작성 시 첫 시도 401 발견 → fixture 추가

**의미**:
- "endpoint 의 auth requirement 별 fixture matrix" 표준화 필요
- 본 사례는 single Story scope 내 즉시 회복 (1 fixture 추가)
- §4.4 fixture-design checklist 후보

**평가**:
- 본 사례 1건 → endpoint 별 auth matrix 가 다양해질 때 (operator-only, viewer-readonly 등) 누적 시 박제
- Cat B (self-discovered) 로 분류 — 정상 비용 범위

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] ADR 신규 후보 — pytest marker 도입 시 CI workflow 동시 갱신 게이트

```
target_adr: ADR 신규 또는 ADR-011 amendment (CI standard)
amendment_type: behavior (CI workflow ↔ pytest marker 동기)
trigger: 본 retro §3.1 — Task 1 의 e2e marker 등록 + Task 6 의 e2e test 추가에도 .github/workflows/ci.yml 의 -m 필터 미갱신 → 첫 CI FAILURE
배경:
  - pytest marker 는 pyproject.toml 에 등록 + test 파일에 데코레이터 부착
  - CI workflow 의 -m "not X" 필터는 별도 파일 (.github/workflows/ci.yml) 에 박제
  - 두 위치 사이 의존성 invisible — 한 쪽만 갱신 시 silent skip 또는 lateral failure
문제:
  - 본 PR 첫 CI 실패 — 1 commit fix 로 회복했으나, 더 복잡한 marker (slow/gpu/manual 등) 도입 시 발견 지연
  - "marker 도입 = CI 필터 동기" 의무가 plan/skill 에 부재
  - subagent-driven-development 에서도 marker Task 와 CI Task 분리 시 동기 누락 위험
제안 결정:
  a) pytest marker 신규 등록 시 plan 에 "CI workflow -m 필터 갱신" Task 의무 추가
  b) skill `superpowers:writing-plans` 에 marker checklist 추가
  c) (선택) CI 자체에 lint step — "registered markers vs workflow filter coverage" 검증
예상 결과:
  - marker 도입 시 CI 필터 동기 누락 0
  - 신규 marker 카테고리 (slow/gpu 등) 도입 시 lateral 비용 사전 차단
관련:
  - ADR-011 CI standard
  - MEMORY feedback_ci_failure_auto_recovery.md (recovery 사이클은 작동 — fix 비용 minimize 효과만 추가)
보류 사유: 본 사례 1건 — 1주 관측 후 동일 패턴 재발 시 박제 (root cause 명확 → 즉시 박제 가능)
```

### 4.2 [MEDIUM] ADR 신규 후보 — Streamlit 페이지의 testing-aware design 원칙

```
target_adr: ADR 신규 (mctrader-web 내부 convention) 또는 ADR-018 D? 패턴
amendment_type: artifact (코드 패턴)
trigger: 본 retro §3.2 — 20_data_collection 의 polling loop 가 AppTest 환경에서 무한 대기, session_state 수동 조작으로 우회
배경:
  - Streamlit 페이지의 자동갱신 polling loop 는 production runtime UX 패턴
  - 그러나 AppTest 는 single-render 환경 — loop 가 dead-end
  - 페이지 코드와 테스트 코드 사이 "auto-refresh disable hook" interface 부재
  - 본 사례는 session_state["dc_refresh"] = "수동" 으로 우회 가능했으나, 다른 페이지가 다른 키 (refresh_mode 등) 사용 시 패턴 재사용 불가
문제:
  - polling 페이지 추가 시 마다 testing 친화 hook 별도 설계 비용
  - 페이지 ↔ 테스트 사이 contract 미박제
  - testing-aware design 원칙 부재
제안 결정 (1주 관측 후):
  a) mctrader-web 내부 convention: polling 페이지는 표준 session_state key (예: f"{page_id}_auto_refresh") 사용 의무
  b) AppTest base fixture 에 "disable_polling(page_id)" 헬퍼 추가
  c) 페이지 작성 가이드 (CLAUDE.md 또는 docs/web/conventions.md) 에 박제
예상 결과:
  - polling 페이지 ↔ AppTest 호환성 보장
  - 신규 polling 페이지 추가 시 AppTest 무한 대기 문제 0
보류 사유:
  - 본 사례 1 페이지 — 다른 polling 페이지 surface 시 누적 ≥3 후 박제
  - 또는 mctrader-web 내부 convention (ADR 미박제) 으로 즉시 적용 가능
```

### 4.3 [LOW] superpowers:writing-plans 갱신 — API/dataclass 시그니처 grep 의무

```
target: skill superpowers:writing-plans
amendment_type: process (plan-writing checklist)
trigger: 본 retro §3.3 — StatusResult 인자 순서 plan vs 실제 mismatch (positional 순서 추정)
배경:
  - Plan 작성 시 외부 dataclass/function 시그니처 paste 시 코드 grep 없이 추정
  - 실제 코드와 mismatch 시 first execution 에서 surface — TDD 우선 lane 에서는 자동 회복
  - 그러나 plan-paste-then-execute 패턴 (subagent 가 plan 그대로 실행) 에서는 surface 지연
문제:
  - Plan 의 신뢰도 저하 — "plan 의 시그니처는 검증됐는가" 의문
  - subagent 가 plan 의 잘못된 시그니처를 그대로 사용 시 첫 test 실패까지 비용 누적
제안 결정:
  a) writing-plans skill 에 checklist 추가: "외부 API/dataclass 시그니처 명시 시 grep 결과 paste 의무"
  b) plan 검토 단계에서 reviewer 가 시그니처 grep 검증
예상 결과:
  - plan ↔ 실제 코드 시그니처 mismatch 0
  - subagent 의 plan 신뢰도 향상
보류 사유:
  - 본 사례 1건 → 누적 ≥3 시 박제
```

### 4.4 [LOW] mctrader-web fixture-design checklist — endpoint auth matrix

```
target: mctrader-web internal convention 또는 ADR-018 D? 패턴
amendment_type: artifact (fixture 표준)
trigger: 본 retro §3.4 — admin endpoint test 작성 시 use_multi_token_auth=False 기본 fixture 로 401 발견 → multi-token fixture 추가
배경:
  - 기본 fixture 는 single-token mode 가정 (no role)
  - admin/operator/viewer role 별 endpoint test 시 fixture matrix 필요
  - endpoint 의 auth requirement 별 fixture 매핑 표준 부재
문제:
  - endpoint 추가 시 fixture matrix 확장 invisible cost
  - test 작성 시 첫 시도 401 발견 → fixture 추가 회복 사이클
제안 결정 (누적 후):
  a) mctrader-web tests/conftest.py 에 표준 fixture matrix:
     - client_no_auth, client_single_token, client_admin, client_operator, client_viewer
  b) endpoint 별 auth requirement 를 path → fixture 매핑 표 (docs/web/test-fixtures.md) 박제
  c) 신규 endpoint 추가 시 fixture matrix 갱신 의무
예상 결과:
  - endpoint test 작성 시 첫 시도 auth 실패 0
  - fixture 재사용성 향상
보류 사유:
  - 본 사례 1건 → endpoint auth matrix 다양화 시 (operator-only, viewer-readonly 등) 누적 후 박제
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 9+ Story sweep — token efficiency 누적 신기록

본 세션 (2026-05-09 ~ 2026-05-10 cross-day) 처리 누적:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 mctrader-market audit)
- MCT-114 (D1/D2 market-bithumb audit)
- MCT-115 (D1/D2/D3 mctrader-data audit)
- MCT-116 (D2/D3/D5 mctrader-engine audit)
- MCT-117 (D1/D4/D5 mctrader-web audit)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2 — 4071 LoC)
- MCT-121 (Upbit 거래소 데이터 수집)
- MCT-122/123 (관측됨)
- MCT-124 (signal-collector 신규 리포)
- **MCT-119 web overhaul (본 PR — 528 PASSED 신규 38 test + e2e 12)**

→ 11+ Story + Strategy Set Pipeline + 신규 plugin repo 2개 + 테스트 인프라 보강 = single-session sweep. RETRO-MCT-124 §5.x 의 "9 Story sweep" 신기록 갱신 — codeforge ζ arc 의 ADR governance velocity + admin merge autonomy + 자동 PMO retro dispatch 가 누적적으로 작동.

### 5.2 부수 fix 비율 카테고리 표준 — Cat B 본 사례 25%, RETRO 누적 평균 안정화

| Story | 본 fix LoC | Cat A | Cat B | Cat C | 비율 합산 |
|---|---|---|---|---|---|
| MCT-117 | 11 | 350% (pre-existing CI debt) | 0 | 0 | 350% |
| MCT-119+120 | 22+7 commit | 0 | 17% | 0 | 17% |
| MCT-121 | 14 commit | 36% (MCT-115 잔여) | 7% | 0 | 43% |
| MCT-124 | 14 commit | 0 | 21% | 0 | 21% |
| **MCT-119 web overhaul** | **8 commit** | **0** | **25%** | **0** | **25%** |

→ Cat B 만의 비율 (신규 코드 self-discovered defect): **17% → 21% → 25%** 안정 범위 (15~25%). RETRO-MCT-119-120 §5.2 의 "Cat B 정상 범위" 가설이 누적 4 Story 에 걸쳐 검증. **Cat A 가 0 인 단일-scope Story 의 Cat B 비율 ~20% 가 baseline** 으로 박제 가능.

### 5.3 multi-repo Story 의 sub-Story 분리 패턴 — RETRO-MCT-119-120 §3.1 회피 성공

RETRO-MCT-119-120 §10.1 권고: "mctrader-web Strategy Set follow-up Story 가칭 MCT-121" — 본 PR 은 그 권고와 다른 lane (test 보강) 으로 진행됐으나 **branch 분리 + base = main 직속** 원칙은 동일 적용. 결과: scope 누수 0, wrong-branch-stack 0. **multi-repo Story 의 기본 전략 = "각 repo 별 별도 PR + base = main"** 패턴이 RETRO-MCT-121 (mctrader-market-upbit + mctrader-data 양 repo 모두 push) → 본 PR (web 단독 PR) 까지 3회 연속 성공. 다음 multi-repo Story 부터 이 패턴 default 채택 권장.

### 5.4 ADR 후보 누적 — N=8 (1주 관측 sprint 일괄 박제 후보)

ADR-018 D1~D7 외 + ADR-019 D1~D6 외 + ADR-020 D1 외 신규 후보 누적:
- D8 후보 (RETRO-MCT-117 §4.1): CI quality gate fail-fast 폐지
- D? 후보 (RETRO-MCT-119-120 §4.3): Optional None-guard 의무
- D? 후보 (RETRO-MCT-113 §4.1): branch guard enforcement 자동화
- D? 후보 (RETRO-MCT-107-111 §8.6): 세션 종료 게이트
- ADR-020 D2 후보 (RETRO-MCT-119-120 §4.1): multi-repo Story completion 게이트
- ADR-019 D7 후보 (RETRO-MCT-119-120 §4.2): worktree cleanup 게이트
- ADR-018 신규 (RETRO-MCT-121 §4.2): decimal.InvalidOperation 같은 ParseError 계열 catch
- ADR-019 D? (RETRO-MCT-121 §4.3): 신규 repo Python interpreter 검증
- **ADR 신규 (본 retro §4.1): pytest marker ↔ CI workflow 동기 게이트**
- **ADR 신규 (본 retro §4.2): Streamlit testing-aware design**

→ **누적 10+ 후보**. 1주 관측 (2026-05-16) 후 일괄 ADR 박제 sprint 강력 권장. RETRO-MCT-117 §6 + RETRO-MCT-119-120 §6 권고 누적 — 더 이상 미루면 박제 비용 폭증 위험.

### 5.5 Streamlit AppTest + Playwright 2-tier 테스트 전략 첫 실증

본 PR 이 mctrader-web 측 첫 2-tier 테스트 인프라 도입:
- **Tier 1 (CI 빠름)**: Streamlit AppTest — 격리 + mock, ~수십 ms/test, CI default
- **Tier 2 (선택 실행)**: Playwright E2E — 실제 브라우저 + localhost:8501, `@e2e` skip, manual `pytest -m e2e`

→ Layer 분리로 CI 속도 유지 + 실제 사용자 플로우 회귀 검증 양립. RETRO-MCT-124 의 "워커 단위 + 통합" 2-tier 패턴과 유사 lane. mctrader 전 repo 의 testing 표준 후보 — **CLAUDE.md 또는 docs/testing/strategy.md 박제 권장**.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **ADR 박제 sprint 즉시 실행** (§5.4) — 누적 10+ ADR 후보 1주 관측 임계 충족 (또는 root cause 명확 항목 즉시 박제). 다음 세션 시작 시 ArchitectAgent dispatch 로 일괄 처리. 본 retro §4.1 pytest marker ↔ CI 동기 + §4.2 Streamlit testing-aware design 우선 후보.

2. **multi-repo Story default 전략 박제** (§5.3) — "각 repo 별 별도 PR + base = main" 패턴이 3회 연속 성공. RETRO-MCT-119-120 §4.1 ADR-020 D2 후보 박제 시 본 패턴 default 명시 권장. 또는 superpowers:writing-plans skill 에 multi-repo Story checklist 추가.

3. **mctrader-web 2-tier 테스트 전략 표준 박제** (§5.5) — Streamlit AppTest + Playwright E2E 2-tier 가 본 PR 에서 첫 실증. mctrader 전 repo 의 web/UI 테스트 표준 후보. `docs/testing/web-strategy.md` 또는 mctrader-web `CLAUDE.md` 에 박제 권장.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Task 1 인프라 (markers + playwright dep + CI fixture JSON 3종) | ~10% |
| Task 2 AppTest 03_wfo_panel + assertion robustness fix | ~10% |
| Task 3 AppTest 04/05/06 strategy pages | ~15% |
| Task 4 AppTest 20_data_collection (polling loop disable 패턴 발견) | ~15% |
| Task 5 API gap (audit_query 10 + rbac_tokens 11 + multi-token fixture) | ~20% |
| Task 6 Playwright E2E conftest + 4 flow + expect() auto-retry fix | ~20% |
| Task 7 검증 + PR + CI marker 필터 fix | ~5% |
| Story §11 회고 pointer + 본 retro 작성 | ~5% |

→ **부수 비용 ~10%** (CI marker fix + expect() auto-retry fix). RETRO-MCT-119-120 의 ~5% (CI fix only) 보다 약간 높음 — 신규 인프라 도입 (playwright) 의 첫 노출이라 정상 범위.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-019**: Parallel agent isolation — D1 branch 분리 (본 PR `feat/test-overhaul-mct-119` 신규 branch 적용), D7 worktree cleanup 후보 (RETRO-MCT-119-120 §4.2) 미적용
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro 8번째 same-session trigger), D2 multi-repo 게이트 후보 (RETRO-MCT-119-120 §4.1)
- **ADR-018**: Defensive coding patterns — D8 후보 + Optional None-guard 후보 + decimal.InvalidOperation 후보 (누적)
- **ADR-011**: CI standard — 본 PR CI green 5 SUCCESS + 1 informational, marker 필터 갱신 ADR 후보 §4.1
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #35 admin merge 자율 (8번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: CI marker fix 1 commit 자동 recovery 사이클 적용 (~5분)
- **선행 retro**:
  - `RETRO-MCT-119-120-strategy-pipeline.md` (§3.1 web 미푸시 패턴 → 본 PR 에서 branch 분리로 회피 성공)
  - `RETRO-MCT-121.md` (§5.5 부수 fix 카테고리 표준)
  - `RETRO-MCT-122-123.md` (§1.4 Cat C 패턴)
  - `RETRO-MCT-124-signal-collector.md` (§1.4 Cat B 21% baseline)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-119.md` §11 에 본 retro pointer 박제 (RETRO-MCT-119-120 와 별도 후속 작업 표기).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up

- **본 PR 직후 follow-up 없음** — 7 Task 100% 완료, scope 누수 0, CI green
- 다만 §3 의 Cat B fix 2건 (CI marker + expect() auto-retry) 은 "인프라 도입 첫 노출 비용" — 향후 신규 marker/E2E framework 도입 시 사전 checklist 적용 권장

### 10.2 ADR 박제 (1주 관측 또는 즉시 검토)

- **ADR 신규 (§4.1)** — pytest marker ↔ CI workflow 동기 게이트 — root cause 명확, 즉시 박제 권장
- **ADR 신규 (§4.2)** — Streamlit testing-aware design 원칙 — mctrader-web internal convention 으로 즉시 적용 가능 (ADR 미경유)
- §4.3 writing-plans skill 갱신 — 누적 후
- §4.4 mctrader-web fixture-design checklist — 누적 후
- **§5.4 누적 10+ ADR 후보 일괄 박제 sprint** — 1주 관측 임계 충족 항목 우선

### 10.3 별도 issue 발의

- 본 PR scope 외 발견 0 — 후속 issue 없음

### 10.4 mctrader-web 후속 Story 트리거

본 PR 로 mctrader-web 측 테스트 인프라 baseline 확립:
- AppTest 5 페이지 커버리지 — 나머지 미커버 페이지 (예: 01/02/07~19/21+) 에 동일 패턴 확장 가능
- API gap 2 endpoint 추가 — 다른 admin endpoint (예: `/admin/system`, `/admin/metrics`) 동일 fixture 재사용 가능
- Playwright E2E 4 flow — 다른 사용자 플로우 (예: monitoring, alerting, settings) 추가 시 base conftest 재사용
- **Strategy Set UI/API (RETRO-MCT-119-120 §3.1 미푸시 follow-up)** 에 본 PR 의 AppTest + E2E 패턴 적용 시 회귀 안전망 강화

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
