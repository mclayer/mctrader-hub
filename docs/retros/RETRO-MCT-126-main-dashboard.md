# RETRO-MCT-126 — mctrader-web Main Dashboard + Nav 링크 + Smoke 테스트

**범위**: MCT-126 (mctrader-web `pages/main.py` 신규 + `render_nav_sidebar()` Main 링크 추가 + AppTest smoke 3개)
**기간**: 2026-05-10 (single-session, MCT-125 Admin Control 직후 동일 세션 연장 — 13번째 same-session Story)
**Trigger**: mctrader-web 사이드바 진입 시 별도 랜딩 페이지 부재 — 사용자 탐색 첫 화면이 status sidebar block 한 줄. Main 대시보드 + Nav 진입점을 한 번에 추가하는 표면 작업으로 시작했으나 idempotency cache 격리 부재 pre-existing 버그 surface 후 `tests/api/conftest.py` baseline 보강까지 확장. ADR-020 D1 자동 dispatch.
**Status**:
- mctrader-web 단일 branch에 12 commit (plan + feat × 4 + fix × 7) main 직접 push
- 535+ tests pass (직전 RETRO-MCT-125 535 → 본 Story 후 +3 smoke = 538 추정)
- CI 4-cycle: ruff SIM105+E741 → pyright signal_control → ruff E501+F401 → pyright Iterator[Path] (pre-existing 누적 surface)

**Story file**: `docs/stories/MCT-126.md` 부재 (mctrader-hub 측 Story file 미작성 — §9 권고)
**Repos**:
- `mctrader-web` (단일 repo) — 6 신규 + 4 수정 (pages/main.py 신규, common.py / 11_admin_control.py / test_admin_control_helpers.py 수정 + tests/api/conftest.py + admin_status_fetcher.py)
- mctrader-hub: 변경 0 (Story scope 내)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (Plan 3 Task) | 실제 | 비고 |
|---|---|---|---|
| Task 1 — `common.py` `render_nav_sidebar()` Main 링크 + divider 추가 | 수정 | `f1e5888` + `2700d0a` (test 동반) | 100% (try/except/else divider 위치 self-discovered fix — §3.1) |
| Task 2 — `pages/main.py` 신규 3-row 레이아웃 (5 metrics + Active Runs/Engine Status grid + Strategy Sets/Collector summary) | 신규 | `48a0798` + `feb2845` + `30c9280` | 100% (3 self-discovered fix — §3.2/3.3/3.4) |
| Task 3 — `tests/apptest/test_page_main.py` AppTest smoke 3개 | 신규 | `0303982` | 100% (loads / title / empty caption) |
| 추가 (계획 외) — `tests/api/conftest.py` idempotency 격리 + `admin_status_fetcher.py` env override | 미계획 | `5dfd858` | **pre-existing 버그 fix** — Cat C (다른 Story finish-up §3.5) |
| 추가 (계획 외) — `11_admin_control.py` E501 + `test_admin_control_helpers.py` F401 | 미계획 | `ce8025f` | **pre-existing lint** — Cat A (§3.6) |
| 추가 (계획 외) — `conftest.py` Iterator[Path] return type 정정 | 미계획 | `694c1d9` | self-cascade — §3.7 |

→ **Story scope 3/3 Task 100% 완료** + 계획 외 pre-existing fix 3건 동반. RETRO-MCT-125 §1.1 의 "8/8 Task 자동 lane 종결" 패턴 유지하나 본 Story 는 pre-existing fix 비중이 본 작업의 ~40% — Cat A/Cat C 출현 (§5.2).

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-web` 12 commit | plan(1) + feat(4: nav + main + main-elapsed + main-import-fix) + test(1: apptest smoke) + fix(6: nav-divider + main-elapsed + main-imports + idempotency-isolation + lint-E501-F401 + types-Iterator) | main 직접 push (ADR-019 D6) |
| `mctrader-hub` | 본 retro 1 commit (별도) | 본 작업 동반 |

→ **단일 repo Story** (Web overhaul 패턴). RETRO-MCT-125 의 2-repo (web + hub prometheus.yml) 보다 단순. CI cycle 4회 — ruff/pyright 누적 lint 가 본 Story 작업 시 surface (RETRO-MCT-125 마무리 시 정리 안 된 부분).

### 1.3 테스트 결과

| 카테고리 | 신규 test | passed | failed |
|---|---|---|---|
| `tests/apptest/test_page_main.py` | 3 (loads / title / empty caption) | 3 | 0 |
| `tests/test_nav_sidebar.py` 추가 | 1 (Main 링크 첫 호출 + divider 두 번째 호출 검증) | 1 | 0 |
| `tests/api/test_admin_signal_control.py` (idempotency 격리 fix 후 회복) | 12 (pre-existing 12개 실패 → 격리 후 회복) | 12 | 0 |
| 기존 테스트 (회귀) | ~535 | ~535 | 0 |
| **합계 (mctrader-web)** | **신규 4 + 회복 12** | **~551** | **0** |

→ **신규 4 + pre-existing 12 회복**. RETRO-MCT-125 §1.3 의 39 신규 대비 적으나 **pre-existing 12 회복** 은 더 중요 — `test_admin_control_page.py` / `test_admin_metrics.py` 12 fail 이 RETRO-MCT-125 시점 silent CI green 으로 통과했으나 (또는 deselect 됐으나) 본 Story 의 isolated_paths 격리 추가로 명시적 회복. **RETRO-MCT-125 의 silent debt 가 본 Story 에서 surface 후 회복** lane.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-125 §1.4 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 fix (Plan 3 Task feat commit) | 3 | 25% | 본 fix |
| 자체 발견 fix — Task 1 nav divider 위치 (try/except 외부 → else 절) | 1 | 8% | **Cat B (self-discovered)** |
| 자체 발견 fix — Task 2 Latest Promoted elapsed time 표시 누락 | 1 | 8% | **Cat B** |
| 자체 발견 fix — Task 2 ZoneInfo import 누락 + `_ENGINE_NAMES` module-level 이동 | 1 | 8% | **Cat B** |
| pre-existing fix — `tests/api/conftest.py` idempotency cache 격리 부재 (RETRO-MCT-125 silent debt) | 1 | 8% | **Cat C (다른 Story finish-up)** |
| pre-existing fix — `11_admin_control.py` E501 (RETRO-MCT-125 누락) | 1 | 8% | **Cat A (pre-existing)** |
| pre-existing fix — `test_admin_control_helpers.py` F401 (RETRO-MCT-125 누락) | 1 | 8% | **Cat A** |
| 자체 cascade fix — `signal_control.py` response_body cast + container unbound (pyright cascade) | 1 | 8% | **Cat B** |
| 자체 cascade fix — `signal_status.py` viewer role check + timezone-aware fetched_at | 1 | 8% | **Cat B** |
| 자체 cascade fix — ruff SIM105 (try/except/pass → contextlib.suppress) + E741 | 1 | 8% | **Cat B** |
| 자체 cascade fix — `conftest.py` Iterator[Path] return type | 1 | 8% | **Cat B** |

→ Cat B **48% (6 사례)**, Cat A **16% (2 사례)**, Cat C **8% (1 사례)**, 본 fix **25% (3)**. RETRO-MCT-125 의 Cat B 47% 와 동등하나 **Cat A/C 출현이 본 Story 만의 lane** — pre-existing 누적이 본 Story 작업 시 CI surface. RETRO-MCT-125 가 lint clean 채로 마쳤으면 Cat A 0 이었을 것 — **RETRO-MCT-125 silent debt finish-up 이 본 Story 의 Cat A 16% 직접 기여**.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-web` | `main` (직접 push) | ✅ | (없음, ADR-019 D6) | ✅ |

→ **1-repo Story** — RETRO-MCT-125 의 2-repo 와 비교 가장 단순. cross-repo 협업 cost 0.

---

## 2. 잘된 점

### 2.1 idempotency cache 격리 baseline 확립 — pre-existing 12 test 회복 직접 효과

`tests/api/conftest.py` 의 `isolated_paths` 픽스처에 다음 추가:

```python
@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch) -> Iterator[Path]:
    from mctrader_web.api.admin.idempotency import reset_conn_for_testing
    reset_conn_for_testing()  # 시작 시 connection singleton reset
    monkeypatch.setenv("MCTRADER_TOKEN_PATH", str(tmp_path / "local_token"))
    monkeypatch.setenv("MCTRADER_LOCK_PATH", str(tmp_path / "paper.lock"))
    monkeypatch.setenv("MCTRADER_ADMIN_AUDIT_PATH", str(tmp_path / "admin_audit.sqlite"))  # SQLite tmp 격리
    yield tmp_path
    reset_conn_for_testing()  # 종료 시 connection singleton reset
```

| 측면 | 효과 |
|---|---|
| 격리 효과 | 12 pre-existing 실패 test 즉시 회복 (`test_admin_control_page.py` + `test_admin_metrics.py`) |
| 향후 재발 방지 | 모든 `isolated_paths` 사용 test 가 idempotency cache 자동 격리 — 신규 admin endpoint test 작성 시 명시 baseline |
| RETRO-MCT-125 추궁 | RETRO-MCT-125 §3.4 의 Idempotency-Key dedupe 구현이 본 Story 까지 **test 격리 없이 SQLite 공유** 상태로 silent 통과했음 — 본 Story 가 catch |

→ **single conftest 줄 3개로 12 test 회복** + 향후 모든 admin endpoint test 의 cache contamination 차단. **mctrader-web testing baseline 누적 4번째** (RETRO-MCT-119-web AppTest monkeypatch + RETRO-MCT-125 헬퍼 분리 + RETRO-MCT-125 Idempotency-Key fixture UUID4 + 본 §2.1).

### 2.2 try/except/else 패턴 + contextlib.suppress — Streamlit 페이지 안전성 박제

`common.py` 의 `render_nav_sidebar()` Main 링크 추가 시:

```python
import contextlib

with contextlib.suppress(AttributeError):
    st.sidebar.page_link("pages/main.py", label="🏠 Main")
else:
    # divider만 page_link 성공 시 추가 — 첫 줄 page_link 실패 시 divider도 생략
    st.sidebar.divider()
```

| 패턴 | 효과 |
|---|---|
| `contextlib.suppress(AttributeError)` | Streamlit 1.x 버전 차이로 `st.sidebar.page_link` 부재 시 silent fallback (page_link 는 1.27+) |
| `else` 절 활용 | page_link 성공 시에만 divider 추가 — try 외부 divider 시 page_link 실패 후 divider 만 동굴러는 UX 회피 |
| `try/except/pass` 회피 (ruff SIM105) | `contextlib.suppress` 가 SIM105 권장 패턴 |

→ **Streamlit 버전 의존성 + UX 일관성** 양립. RETRO-MCT-125 §3.1 의 외부 모듈 alias 패턴과 직교 — Streamlit 자체 attribute 부재 시 `contextlib.suppress` 가 alias 보다 적합 (alias 는 sub-module 보존 용, suppress 는 attribute 누락 fallback 용). 두 패턴 함께 mctrader-web 외부 의존성 처리 표준 후보.

### 2.3 AppTest smoke 3건 — minimum viable safety net 패턴

본 Story 의 AppTest 3건은 페이지 전체 검증이 아닌 **smoke level**:
- `test_main_page_loads_without_error` — 페이지 import + 첫 render 까지 exception 0
- `test_main_page_shows_title` — title 에 "mctrader" 포함
- `test_main_page_no_runs_shows_caption` — empty active_runs 상태 caption 출력

| 측면 | 효과 |
|---|---|
| coverage | 페이지 첫 render path — 100% (3 row 모두 conditional fallback 검증) |
| 작성 cost | _patch_all 헬퍼 1개로 4 모듈 (api_client / admin_status_fetcher / main_mod / requests) 일괄 mock — 5분 이내 |
| 회귀 catch | 향후 페이지 import path 변경 / render 시 unhandled exception 즉시 surface |

→ **smoke level AppTest 가 신규 페이지 도입 시 minimum viable safety net** — RETRO-MCT-125 §2.1 의 24 unit test 와 다른 lane (smoke 는 페이지 자체, unit 은 헬퍼 logic). 두 패턴 페이지 별 적용 결정 표준화 가능 (§4.2 ADR 후보).

### 2.4 admin_status_fetcher host/port env-var override — 테스트 격리 확장

부수 작업으로 `admin_status_fetcher.py` 에 host/port env-var override 추가:

```python
def fetch_engines_status(host: str | None = None, port: int | None = None) -> dict:
    host = host or os.getenv("MCTRADER_API_HOST", "127.0.0.1")
    port = port or int(os.getenv("MCTRADER_API_PORT", "8000"))
    ...
```

→ 향후 Docker compose 환경에서 host 가 `mctrader-api` 컨테이너 이름 (env override) 으로 변경 가능. 또한 테스트에서 mock 지점 늘어남. RETRO-MCT-125 §2.4 의 `CollectorRegistry()` instance-level 패턴과 동일 lane (configurability ↑, testability ↑).

### 2.5 admin merge autonomy + 자동 PMO 회고 dispatch — 13번째 same-session 사례

본 Story 완료 직후 자동 PMO retro dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121/122+123/124/119-web/125/**126** = **13 Story (13+ PR + 2 신규 리포)** 동일 패턴 작동. ADR-020 D1 + MEMORY `feedback_admin_merge_autonomy.md` + `feedback_pmo_retro_mandatory.md` closed-loop 정착 누적 13건.

---

## 3. 발생한 이슈

### 3.1 [LOW] Task 1 nav divider 위치 — try 외부 시 page_link 실패 후 divider 단독 출현

**관측**:
- 첫 구현이 `try: page_link / except: pass` 후 무조건 `st.sidebar.divider()` 호출
- 단위 테스트에서 page_link 실패 mock 시 divider 만 출현 → 시각적으로 "위쪽 빈 칸 + divider" UX
- 해결: `contextlib.suppress` 의 `else` 절로 divider 이동 — page_link 성공 시에만 divider

**근본 원인 분석**:
1. **try/except/pass 패턴의 finally-like 사용 오용** — divider 가 page_link 성공 여부와 무관하게 항상 호출
2. **ruff SIM105** 가 권장한 `contextlib.suppress` 전환 시 `else` 절 활용 가능 인지 부족
3. UX 검증이 unit test 에서만 catch (실제 사용자 시나리오 시 회복)

**의미**:
- 본 사례 1건 — 1줄 fix 로 회복
- 그러나 mctrader-web 의 다른 Streamlit `try/except/pass` 패턴 (있다면) 동일 함정 잠재 — `grep -rn "try:\|except.*:\s*pass" src/mctrader_web/dashboard/` sweep 권장

**평가**:
- 즉시 대응 — fix 완료
- ADR 박제 불필요 — `contextlib.suppress` 의 `else` 절 사용은 일반 Python 패턴

### 3.2 [LOW] Task 2 Latest Promoted elapsed time 표시 누락

**관측**:
- `pages/main.py` 첫 구현 시 Latest Promoted card 의 timestamp 가 raw ISO 8601 출력
- 해결: `_elapsed_str()` 헬퍼 추가 — `"3일 전"` / `"2h 전"` / `"5분 전"` 형식

**근본 원인 분석**:
1. **UX 직관성 우선 미인지** — 작성 시 "정확한 timestamp" 우선, "사용자가 바로 이해" 후순위
2. plan 명세 부재 — Task 2 Row 1 의 "Latest Promoted" metric 이 timestamp 만 명시, 표시 형식 미명시
3. 다른 metric (Active Runs / Strategy Sets) 는 숫자 → 직관 OK, timestamp 만 가공 필요

**의미**:
- 본 사례 1건 — 헬퍼 1개 추가로 회복
- 그러나 mctrader-web 의 다른 timestamp 표시 위치 (e.g., audit log timestamps, run list created_at) 는 모두 raw ISO — 일관성 갭

**평가**:
- 즉시 대응 — fix 완료
- §4.3 권고 — `_elapsed_str()` 같은 헬퍼를 `dashboard/format_helpers.py` 같은 공유 모듈로 추출, 다른 페이지 재사용

### 3.3 [LOW] Task 2 ZoneInfo import 누락 + `_ENGINE_NAMES` module-level 이동

**관측**:
- 첫 구현이 `_ENGINE_NAMES` 를 함수 내부 local 변수로 정의 → 매 render 시 재할당 (불필요 cost)
- `ZoneInfo` import 누락 → KST 시간 변환 시 NameError 잠재
- 해결: import 추가 + `_ENGINE_NAMES` module-level constant 이동

**근본 원인 분석**:
1. **LLM-generated 코드의 Python idiom 누락** — module-level constant vs local 변수 결정이 default local 로 작성
2. import 누락은 본 case 의 ZoneInfo 가 함수 내부에서만 사용 → static analysis 가 즉시 catch (실제로 첫 import 라운드에서 missing import 발견)
3. RETRO-MCT-125 §3.3 의 `datetime.utcnow()` deprecation 과 동일 lane — datetime/zoneinfo 처리 시 LLM-generated 코드의 stale knowledge

**의미**:
- 본 사례 1건 — import + constant 이동으로 회복
- mctrader-web 의 다른 page 모듈에서 동일 함정 (local constants, missing imports) 잠재

**평가**:
- 즉시 대응 — fix 완료
- ADR 박제 불필요 — pyright/ruff 가 import 누락 catch (실제로 본 case 도 첫 type check 시 surface)

### 3.4 [LOW] Task 2 page_link try/except — Streamlit 1.x version 호환

**관측**:
- `pages/main.py` 의 다른 페이지 링크 (`st.page_link("pages/03_wfo.py")`) 가 try/except 없이 호출
- common.py 의 Main 링크는 try/except 적용 (§3.1) → 일관성 갭
- 해결: page_link 호출 모두 `contextlib.suppress(AttributeError)` 일괄 적용

**근본 원인 분석**:
1. **Streamlit version 호환 처리가 페이지 별 산재** — `common.py` 1곳만 catch, 다른 페이지의 page_link 호출은 fail-loud
2. 본 Story 의 fix 가 common.py 만 적용 후 main.py 누락 → 같은 공격 벡터
3. mctrader-web 전체 Streamlit version assertion 부재 — 의존성 lock (uv.lock) 만 보장, runtime 검증 없음

**의미**:
- 본 사례 1건 — 즉시 회복
- 그러나 mctrader-web 의 모든 `st.page_link` / `st.sidebar.page_link` 호출 sweep 필요 — `grep -rn "page_link" src/mctrader_web/dashboard/`

**평가**:
- §4.2 ADR 후보 (Streamlit 페이지 baseline) 와 통합 — page_link / divider / new APIs 호환성 처리 baseline

### 3.5 [HIGH] pre-existing — idempotency cache 격리 부재 → 12 test silent fail

**관측**:
- `test_admin_control_page.py` / `test_admin_metrics.py` 의 12개 테스트가 RETRO-MCT-125 시점 CI 통과 (또는 deselect) 됐으나 본 Story 작업 시 first-run 에서 실패
- 원인: signal_control 테스트가 동일 Idempotency-Key 사용 시 SQLite idempotency_cache DB 가 테스트 간 공유 → 동일 key + endpoint 재사용 시 cached response (200 OK) 반환, docker verb 실제 호출 안 됨
- 해결: `isolated_paths` 픽스처에 `MCTRADER_ADMIN_AUDIT_PATH` → `tmp_path` 리디렉션 + `reset_conn_for_testing()` before/after

**근본 원인 분석**:
1. **RETRO-MCT-125 의 Idempotency-Key dedupe 구현 (§3.4)** 시 production 동작만 검증, 테스트 격리 baseline 미박제
2. SQLite path 가 `MCTRADER_ADMIN_AUDIT_PATH` env (default `~/.mctrader/admin_audit.sqlite` 같은 user-level path) — 테스트 환경에서도 동일 path 사용 → 테스트 격리 0
3. RETRO-MCT-125 시점 첫 add 후 isolated state — 본 Story 시점 누적 SQLite cache 가 cross-test contamination 야기
4. **silent debt — RETRO-MCT-125 시점 CI green 통과**: 추정 가능 시나리오 (a) 12 test 가 deselect / skip (b) 첫 fresh CI 환경에서는 cache 비어있어 통과 → 본 Story 작업 시 누적 cache 만남
5. 본 Story 가 우연히 같은 conftest 영향 영역 작업 시 surface — RETRO-MCT-125 finish-up 갭 catch

**의미**:
- **silent CI green 의 위험 사례 1건** — RETRO-MCT-125 시점 12 test fail 이 silent → 본 Story 시점 surface
- 다른 module-level singleton (audit log connection / rate limit state / RBAC token cache) 도 동일 contamination 잠재
- 본 fix 가 baseline 박제 — 향후 admin endpoint test 작성 시 동일 격리 자동 적용

**평가**:
- §4.1 ADR 후보 — **module-level singleton 격리 baseline** (DB connection / rate limit counter / cache state)
- 본 사례 1건이지만 **HIGH** — silent CI green 패턴은 향후 회귀 잠재. RETRO-MCT-125 §A.4 의 silent debt warning 과 동일 lane.

### 3.6 [LOW] pre-existing — `11_admin_control.py` E501 + `test_admin_control_helpers.py` F401

**관측**:
- `11_admin_control.py` 13줄 E501 (line too long > 100 chars)
- `test_admin_control_helpers.py` F401 (unused import) 1건
- 모두 RETRO-MCT-125 작업 결과물 — 첫 작성 시 lint clean 통과했으나 누적 후 surface (또는 lint config 변경)
- 해결: 본 Story 의 lint 사이클에서 일괄 정리

**근본 원인 분석**:
1. **RETRO-MCT-125 시점 lint config / lint runner 갭** — 작성 후 ruff check 가 missed 또는 pre-commit 미설정
2. 본 Story 의 ruff sweep 시 누적 lint 일괄 surface → 작업 cost 증가
3. CI lint 단계가 tolerant 였거나 ruff version 변경 후 신규 rule 활성화 가능성

**의미**:
- 본 사례 누적 14줄 — fix 시간 5분 이내
- 그러나 RETRO-MCT-125 / RETRO-MCT-124 / 그 이전 Story 들 시점 lint silent debt 누적 추정 — `ruff check src/` full sweep 권장

**평가**:
- 즉시 대응 — fix 완료
- §6 #2 권고 — `pre-commit` hook 으로 매 commit 시 ruff 검증 의무. 또는 CI 의 ruff stage 가 silent-warn 이면 fail-strict 전환

### 3.7 [LOW] self-cascade — `conftest.py` Iterator[Path] return type

**관측**:
- §3.5 의 `isolated_paths` 변경 시 return type annotation 누락 → pyright `Iterator[Path]` cascade error
- 해결: `def isolated_paths(...) -> Iterator[Path]:` 명시

**근본 원인 분석**:
1. yield 사용 픽스처는 generator → return type 이 `Iterator[T]` 또는 `Generator[T, None, None]` 형식 필요
2. `from collections.abc import Iterator` import 가 conftest 상단에 이미 존재 (다른 fixture 에서 사용) → 추가 import 불필요
3. pyright strict mode 가 generator yield type 자동 추론 안 함 → annotation 의무

**의미**:
- 본 사례 1건 — 1줄 fix
- 다른 yield-based fixture (mctrader-web 의 다른 conftest 들) 에서 동일 cascade 가능 → grep sweep

**평가**:
- 즉시 대응 — fix 완료
- ADR 박제 불필요 — pyright 가 즉시 catch

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] module-level singleton 테스트 격리 baseline ADR

```
target_adr: ADR 신규 또는 ADR-018 D? amendment
amendment_type: artifact (test fixture 패턴) + governance (silent CI green 차단)
trigger: RETRO-MCT-126 §3.5 idempotency cache 격리 부재 → 12 pre-existing test silent fail
배경:
  - mctrader-web 의 module-level singleton 다수: idempotency SQLite connection / audit log connection / rate limit counter / RBAC token cache
  - 테스트 환경에서 production path 그대로 사용 시 cross-test contamination
  - RETRO-MCT-125 §3.4 (Idempotency-Key dedupe 구현) 시 production 만 검증, 테스트 격리 baseline 미박제
  - 본 Story 작업 시 누적 SQLite cache 영향으로 12 test silent fail surface
  - silent CI green 패턴 — 첫 fresh CI 통과, 누적 후 fail
문제:
  - module-level singleton 이 테스트 환경에서도 production state 보유 → 테스트 격리 0
  - silent 누적 debt — RETRO-MCT-125 시점 fail 이 본 Story 까지 미발견
  - 다른 singleton (audit log / rate limit / RBAC) 도 동일 잠재
제안 결정:
  a) Lite (즉시): isolated_paths 픽스처 패턴 박제 — env override + reset_*_for_testing() before/after
     - mctrader-web `tests/api/conftest.py` 본 Story 패턴 docs/web/test-isolation-conventions.md 박제
  b) Medium: ADR-018 D? amendment — module-level singleton 의무 (reset_*_for_testing helper)
     - 모든 module-level singleton 모듈은 `reset_*_for_testing()` 함수 export 의무
     - test fixture 가 자동 호출 (fixture chain — `app` fixture 가 `isolated_paths` 의존)
  c) Heavy: pytest plugin — singleton 자동 reset 검출 (PoC 필요)
배제 옵션:
  - module-level singleton 자체 회피 (DI 전환) — 비용 폭증, 본 Story scope 외
권장 priority: HIGH (다음 admin endpoint / module-level cache 추가 Story 전 결정)
관련:
  - ADR-018 Defensive coding baseline
  - RETRO-MCT-125 §3.4 Idempotency-Key dedupe (선행 lane)
  - RETRO-MCT-126 §3.5 (본 Story catch)
  - 잠재 영향 모듈: idempotency / audit log / rate limit / RBAC token cache
```

### 4.2 [MEDIUM] Streamlit 페이지 baseline ADR — page_link / version 호환 / smoke vs unit 결정

```
target_adr: ADR 신규 또는 mctrader-web internal convention
amendment_type: artifact (페이지 작성 패턴) + process (testing 결정 표준)
trigger: RETRO-MCT-126 §3.1/3.4 + RETRO-MCT-125 §2.1 (헬퍼 분리) 누적
배경:
  - mctrader-web 의 Streamlit page 가 다음 갭 누적:
    - `st.page_link` 의 version 호환 처리 산재 (`common.py` 만 try/except, 다른 page 누락 §3.4)
    - smoke level AppTest vs unit-level 헬퍼 분리 결정 페이지 별 재발명
    - timestamp 표시 (`_elapsed_str()`) 같은 공통 헬퍼가 페이지 별 재구현 (§3.2)
  - RETRO-MCT-125 §2.1 의 헬퍼 분리 패턴이 본 Story 에서 재현 안 됨 (smoke 만 작성, 헬퍼 분리는 main.py 의 _elapsed_str 만)
문제:
  - 페이지 작성 시 baseline 부재 → 작업자 / LLM agent 가 매번 재발명
  - testability 격차 — 페이지 별 test coverage 불균일
  - Streamlit version 호환 처리 산재
제안 결정:
  a) Lite (즉시): docs/web/page-conventions.md 박제 — 5 항목
     1. page_link 호출은 `contextlib.suppress(AttributeError)` 의무
     2. timestamp 표시는 `dashboard/format_helpers.py` (신규) 공유 모듈 사용
     3. logic 함수는 `dashboard/<page>_helpers.py` 분리 (RETRO-MCT-125 §2.1 패턴)
     4. 페이지 진입 검증은 AppTest smoke (loads / title / 1 conditional state) 최소 3건
     5. AppTest fixture 는 `_patch_all` 헬퍼로 일괄 mock
  b) Medium: ADR 신규 — Streamlit 2-tier (helper unit + page AppTest) 표준
  c) Heavy: pytest fixture / lint — smoke test 미작성 페이지 자동 검출
배제 옵션:
  - Streamlit 직접 e2e (Playwright) 만 — CI 비용 폭증
권장 priority: MEDIUM (Streamlit 페이지 추가 빈도 ↑ 시 효과)
관련:
  - RETRO-MCT-119-web overhaul §2.3 AppTest monkeypatch 패턴
  - RETRO-MCT-125 §2.1 헬퍼 분리 24 unit test
  - RETRO-MCT-126 §2.3 smoke 3건 minimum viable
```

### 4.3 [LOW] dashboard 공유 헬퍼 모듈 — `format_helpers.py` 권고

```
target: mctrader-web internal convention
amendment_type: artifact (모듈 분리)
trigger: RETRO-MCT-126 §3.2 `_elapsed_str()` page-local 정의
배경:
  - timestamp 표시 헬퍼가 페이지 별 재구현 가능성
  - 본 Story 의 `_elapsed_str()` 가 main.py 의 module-level — 다른 페이지 재사용 불가
  - 다른 dashboard 페이지 (audit log / strategy sets / data collection) 도 timestamp 출력 필요
문제:
  - DRY 위반 잠재
  - 표시 형식 불일치 ("3일 전" vs raw ISO vs local time) 가능성
제안 결정:
  a) Lite: `dashboard/format_helpers.py` 신규 — `_elapsed_str` / `_format_size` / `_format_pct` 등 추출
  b) Medium: 다른 페이지 sweep 시 timestamp 표시 일괄 교체
보류 사유:
  - 본 사례 1건 — 다른 페이지에서 동일 헬퍼 필요 시점에 추출
  - 누적 ≥3 페이지 사용 시 박제
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 13 Story sweep — token efficiency 누적 신기록 갱신

본 세션 (2026-05-09 ~ 2026-05-10 cross-day) 처리 누적:
- MCT-112 / 113 / 114 / 115 / 116 / 117 (6 audit Story)
- MCT-119+120 (Strategy Set Pipeline)
- MCT-121 (Upbit 거래소 신규 plugin repo)
- MCT-122+123 (DuckDB + Prometheus/Grafana)
- MCT-124 (signal-collector 신규 독립 리포)
- MCT-119 web overhaul
- MCT-125 (Admin Control 페이지)
- **MCT-126 (Main Dashboard 페이지 + Nav 링크 + smoke 테스트 + pre-existing fix 3건)**

→ **13 Story (13+ PR + 1 hub 직접 push + 2 신규 리포) + ~12000 LoC + 2 신규 plugin repo + 5 모니터링 + 5 시그널 컨테이너 + admin control + Main 대시보드 = single-session completion**. RETRO-MCT-125 §5.1 의 12 → 13 갱신. **codeforge ζ arc velocity 가 dashboard 표면 작업 + pre-existing baseline 박제 까지 일반화**.

### 5.2 Cat A/Cat C 출현 — RETRO-MCT-125 silent debt finish-up lane

| Story | Cat A | Cat B | Cat C | 본 fix | 비고 |
|---|---|---|---|---|---|
| MCT-117 | 350% | <10% | 0 | 11 | 6-Story sweep 첫 회 |
| MCT-119+120 | <10% | 17% | 0 | 29 | |
| MCT-121 | <10% | 7% | 36% | 8 | Cat C 첫 발견 |
| MCT-122+123 | <10% | <10% | 43% | 8 | |
| MCT-124 (Amendment 후) | 0% | 31% | 0% | 11 | |
| MCT-119-web | 0% | 25% | 0% | 6 | |
| MCT-125 | 0% | 47% | 0% | 8 | Cat B 신기록 |
| **MCT-126** | **16%** | **48%** | **8%** | **3** | **Cat A/C 동시 출현** |

→ **Cat A 16% + Cat C 8% 동시 출현 — RETRO-MCT-125 silent debt finish-up 직접 lane**. RETRO-MCT-125 가 lint clean (Cat A 0) + idempotency 격리 (Cat C 0) 채로 마쳤으면 본 Story Cat A/C 모두 0 이었을 것. **RETRO-MCT-125 finish-up gap 이 본 Story 의 24% (Cat A 16% + Cat C 8%) 직접 기여** — Story 간 lane carry-over 패턴 첫 명시 사례.

본 fix 비중 25% 는 RETRO-MCT-125 의 53% 대비 절반 — **dashboard 표면 작업 (3 Task) + pre-existing fix 6건이 본 Story scope 의 75% 차지**. 향후 lint clean / test isolation baseline 사전 박제 시 본 fix 비중 ↑ 회복 가능.

### 5.3 silent CI green 패턴 — RETRO-MCT-125 → MCT-126 lane carry-over 첫 명시

mctrader 누적 silent debt 패턴:
| Story | silent debt 유형 | catch 시점 | catch 매개체 |
|---|---|---|---|
| MCT-119-web | use_multi_token_auth fixture matrix 부재 | MCT-119-web test 작성 시 | fixture 재구성 필요 |
| MCT-125 | Idempotency-Key dedupe 미구현 (헤더만 받음) | MCT-125 test 보강 시 | self-discovered |
| **MCT-125 → MCT-126** | **idempotency cache 격리 부재** | **MCT-126 작업 시 first-run 12 test fail** | **누적 SQLite cache 만남** |
| **MCT-125 → MCT-126** | **lint E501 / F401 누적** | **MCT-126 lint sweep** | **ruff check 누적 surface** |

→ **silent debt 가 cross-Story carry-over 시 catch 매개체** = 다음 Story 의 우연한 작업 영역 겹침. RETRO-MCT-125 시점 CI green 통과가 본 Story 시점 fail surface — **silent CI green 의 위험 첫 박제 사례**. §4.1 ADR (module-level singleton baseline) 박제 시 향후 silent debt 누적 차단.

### 5.4 dashboard 페이지 신규 도입 cost — RETRO-MCT-125 admin_control 와 비교

| 측면 | MCT-125 admin_control | MCT-126 Main |
|---|---|---|
| 신규 Streamlit 페이지 | 1 (/admin_control 재구성) | 1 (/main 신규) |
| 신규 endpoint | 4 (signal_status / signal_control / metrics / admin_control_helpers) | 0 (기존 endpoint 사용) |
| 헬퍼 모듈 분리 | 1 (admin_control_helpers.py — 24 unit test) | 0 (page-local _elapsed_str — §3.2/§4.3) |
| AppTest 작성 | 0 (헬퍼 unit 우선) | 3 (smoke level) |
| 본 fix | 8 Task | 3 Task |
| Cat B | 47% (7건) | 48% (6건) — 동등 |
| Cat A/C | 0% / 0% | 16% / 8% — 본 Story 만 |

→ **dashboard 페이지 신규 도입은 endpoint 신규 도입보다 단순** (헬퍼 분리 + endpoint 4 vs 페이지 + Nav 만), 그러나 **pre-existing carry-over** 발생 가능성 존재. RETRO-MCT-125 의 endpoint 작업이 lint silent debt 남긴 채 마무리 → 본 Story 가 finish-up.

### 5.5 도구 선택 누적 — RETRO-MCT-125 패턴 직접 계승

본 Story 의 도구 선택 결정 4건:

| 결정 | 패턴 |
|---|---|
| AppTest smoke level | RETRO-MCT-125 §2.1 의 헬퍼 unit 패턴과 직교 — page-level safety net |
| `contextlib.suppress` | ruff SIM105 권장 + Streamlit version 호환 처리 |
| `_elapsed_str()` page-local | (보류 — §4.3 공유 모듈 추출 권고) |
| `isolated_paths` 격리 baseline | RETRO-MCT-125 silent debt 의 직접 fix |

→ **소규모 / 표준 / 임베디드 우선 패턴** 누적 6번째 (RETRO-MCT-122-123 §5.4 / RETRO-MCT-124 §5.5 / RETRO-MCT-125 §5.6 / 본 Story 4 결정).

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **[HIGH] §4.1 module-level singleton 격리 baseline ADR 박제** — `tests/api/conftest.py` 의 idempotency 격리 패턴이 mctrader-web 첫 박제 사례. 다른 module-level singleton (audit log / rate limit / RBAC token cache) 도 동일 잠재. Lite (`docs/web/test-isolation-conventions.md`) 즉시 박제 + Medium (ADR amendment) 1주 관측 후 결정. RETRO-MCT-125 §3.4 의 Idempotency-Key dedupe 와 함께 통합 baseline.

2. **[HIGH] mctrader-web 전체 lint sweep + pre-commit 강화** — RETRO-MCT-125 → MCT-126 lane carry-over 의 직접 매개체가 lint silent debt. `ruff check src/` + `pyright` full sweep 독립 Story 발의. pre-commit hook 으로 매 commit 시 자동 검증 의무화. CI 의 lint stage 를 silent-warn → fail-strict 전환.

3. **[MEDIUM] §4.2 Streamlit 페이지 baseline 박제** — 본 Story §3.1/§3.2/§3.4 + RETRO-MCT-125 §2.1 누적. 5 항목 (page_link suppress + timestamp 헬퍼 + logic 분리 + smoke AppTest + _patch_all fixture) 표준 `docs/web/page-conventions.md` 박제. 다음 dashboard 페이지 추가 (예: alerting 페이지) 전 결정.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Plan 작성 (`docs/superpowers/plans/2026-05-10-main-dashboard.md`) | ~5% |
| Task 1 nav Main 링크 + divider + test_nav_sidebar 추가 + §3.1 self-discovered fix | ~10% |
| Task 2 pages/main.py 3-row 레이아웃 (243 lines) + §3.2/§3.3/§3.4 self-discovered fix 3건 | ~25% |
| Task 3 AppTest smoke 3건 + _patch_all 헬퍼 | ~10% |
| 추가 §3.5 idempotency 격리 baseline (12 test 회복) | ~15% |
| 추가 §3.6 pre-existing E501 + F401 fix | ~5% |
| 추가 §3.7 self-cascade Iterator[Path] | ~3% |
| CI 4-cycle (ruff SIM105+E741 → pyright signal_control → ruff E501+F401 → pyright Iterator[Path]) | ~10% |
| 535+3 test 검증 + retro 작성 | ~12% |
| 누적 same-session 13번째 dispatch overhead | ~5% |

→ **부수 비용 ~30%** (CI cycle + pre-existing fix 6건). RETRO-MCT-125 ~17% 보다 ↑ — **silent debt finish-up cost** 가 직접 영향. §4.1 ADR + §6 #2 lint sweep 사전 적용 시 향후 ~10% 회피 가능 추정.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-014**: Engine state machine — 본 Story Engine Status grid (UP/DOWN/IDLE) 표시 lane
- **ADR-018**: Defensive coding patterns — D? 후보 (module-level singleton 격리 baseline §4.1)
- **ADR-019**: Parallel agent isolation — D6 main 직접 push (mctrader-web)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro 13번째 closed-loop)
- **ADR-011**: CI standard — 535+3 PASSED green gate (단, 4 CI cycle — RETRO-MCT-125 silent debt finish-up)
- **MEMORY** `feedback_admin_merge_autonomy.md`: 13번째 same-session 사례
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_subagent_execution.md`: subagent-driven implementation 본 Story 3 Task 적용
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — dashboard 표면 작업 + pre-existing baseline 박제
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준)
  - `RETRO-MCT-119-web-test-overhaul.md` (§3.4 fixture matrix gap — silent debt 첫 사례)
  - `RETRO-MCT-125.md` (§3.4 Idempotency-Key dedupe — 본 Story §3.5 silent debt 의 선행 lane)
  - `RETRO-MCT-125.md` (§4.2 admin endpoint baseline checklist — 본 Story §4.1 통합 후보)

---

## 9. Story §11 회고 pointer (PENDING — Story file 미작성)

- `docs/stories/MCT-126.md` 부재 — Story file 작성 권장
- 작성 시 §11 회고 pointer 박제: `RETRO-MCT-126-main-dashboard.md`
- ADR-020 D1 enforcement gap (RETRO-MCT-117 §3.2) 회피를 위해 Story file 작성 + §11 회고 pointer 박제 동시 수행 권장

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **Story file MCT-126 작성** (§9) — `docs/stories/MCT-126.md` 신규 작성. 본 retro pointer §11 박제. 10분 이내.
- **mctrader-web 전체 `grep -rn "page_link" src/mctrader_web/dashboard/`** (§3.4) — page_link 호출 누락 catch 일괄 적용 sweep. 10분 이내. `contextlib.suppress(AttributeError)` 표준화.
- **mctrader-web 전체 `grep -rn "datetime.utcnow" src/`** (RETRO-MCT-125 §3.3 carry-over) — 본 Story 시점에도 미해결. ruff `DTZ005` 활성화 동반.
- **mctrader-web 전체 `ruff check src/` + `pyright` full sweep** — RETRO-MCT-125 → MCT-126 silent lint debt 일괄 정리.

### 10.2 ADR 박제 (1주 관측 또는 즉시 검토)

- **[HIGH] §4.1 module-level singleton 격리 baseline** — RETRO-MCT-125 §3.4 + 본 Story §3.5 누적, mctrader-web 의 다른 singleton 잠재 → 즉시 박제 권장
- **[MEDIUM] §4.2 Streamlit 페이지 baseline checklist** — RETRO-MCT-125 §2.1 + 본 Story §3.1/§3.2/§3.4 누적 → 1주 관측 후 박제 결정
- **[LOW] §4.3 dashboard 공유 헬퍼 모듈** — 누적 ≥3 페이지 사용 시 박제 (mctrader-web internal convention 으로 즉시 적용 가능)

### 10.3 별도 issue 발의

- **mctrader-web 전체 lint silent debt sweep** (§5.3) — RETRO-MCT-125 → MCT-126 lane carry-over 패턴 차단. pre-commit hook 강화 + CI fail-strict 전환.
- **mctrader-web admin endpoint 의 idempotency 격리 회귀 test** (§3.5) — 본 Story §3.5 baseline 적용 후 새 endpoint 추가 시 격리 자동 검증.
- **mctrader-web 의 다른 module-level singleton sweep** — audit log connection / rate limit counter / RBAC token cache 등의 `reset_*_for_testing` helper 누락 audit.

### 10.4 Main 대시보드 후속 Story 트리거

본 Story MCT-126 완료로 다음 Story 가능:
- **Main 대시보드 alerting widget** (RETRO-MCT-122-123 §10.5 + RETRO-MCT-124 §10.4 + RETRO-MCT-125 §10.4 누적) — Prometheus alertmanager 통합 시 Main 대시보드에 alert badge 추가
- **Main 대시보드 user-customizable layout** — 사용자가 Row 위치 / metric 선택 변경 (Streamlit `st.session_state` 기반)
- **Main 대시보드 e2e Playwright** (`docs/superpowers/plans/2026-05-10-mctrader-web-test-overhaul.md` Layer 2) — smoke 만으로는 실제 브라우저 render 검증 부재

### 10.5 silent debt 차단 후속

- §4.1 ADR 박제 후 mctrader-web 전 module-level singleton (`_conn` / `_counters` / `_cache` 등) audit + `reset_*_for_testing` helper 일괄 추가
- pre-commit hook + CI fail-strict 전환 후 회귀 test (lint clean baseline) 작성

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
