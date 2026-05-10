# RETRO-MCT-125 — Admin Control 페이지 강화 (Docker SDK + Prometheus + AppTest 헬퍼 분리)

**범위**: MCT-125 (mctrader-web `/admin_control` 페이지 + signal worker 제어 API + Prometheus `/metrics` 노출)
**기간**: 2026-05-10 (single-session, MCT-119 web overhaul + MCT-124 signal-collector 직후 동일 세션 연장)
**Trigger**: MCT-124 5 signal worker 컨테이너 도입 후 운영 가시성·제어 UI 부재 — `/admin_control` 페이지에 Docker SDK 기반 worker 상태 + start/stop/restart 컨트롤 + Prometheus exposition 일괄 도입. ADR-020 D1 자동 dispatch.
**Status**:
- mctrader-web 8 commit 단일 branch (PR/admin merge 정보 본 retro 시점에 별도 보고 — Story 본문 §5 nominal commit graph 기준)
- mctrader-hub commit (prometheus.yml scrape job) 1건
- 535 tests pass / 0 failures (mctrader-web)

**Story file**: `docs/stories/MCT-125.md` (작성됨, status=DONE)
**Repos**:
- `mctrader-web` (주) — 8 commit, +신규 7 파일 + 수정 5 파일 (대략)
- `mctrader-hub` — `monitoring/prometheus.yml` mctrader-web scrape job 1 commit

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (8 Task) | 실제 | 비고 |
|---|---|---|---|
| Task 1 — pyproject.toml: docker>=7 + prometheus-client>=0.20 + requires-python | 의존성 | `5dff1c0` | 100% (단, requires-python `>=3.11,<3.15` 광역 확장 후 `<3.13` 롤백 — §3.7) |
| Task 2 — `api/admin/signal_status.py` (신규) GET /admin/status/signal-workers | 신규 | `8058aef` (5 unit test 동반) | 100% (3 self-discovered fix — §3.1/3.2/3.3) |
| Task 3 — `api/admin/signal_control.py` (신규) POST /admin/signal/{worker_id}/{verb} | 신규 | `1a1e825` (8 unit test 동반) | 100% (3 self-discovered fix — §3.4/3.5/3.6) |
| Task 4 — `api/admin/metrics.py` (신규) GET /metrics Prometheus exposition | 신규 | `a26c99e` (2 unit test 동반) | 100% |
| Task 5 — admin/__init__.py + app.py 라우터 등록 | 통합 | `7971ef4` | 100% |
| Task 6 — compose.yml Docker socket mount + prometheus.yml scrape job | 인프라 | `55ae4a9` (web) + hub commit | 100% |
| Task 7 — `dashboard/admin_control_helpers.py` (신규) 순수 헬퍼 | 신규 | `bcff70f` (24 unit test 동반) | 100% |
| Task 8 — `dashboard/pages/11_admin_control.py` 전면 재구성 | 재구성 | `1319474` | 100% |

→ **Story scope 8/8 Task 100% 완료**. 사용자 수동 의존 0. RETRO-MCT-124 의 Task 8 PENDING (XHR endpoint 사용자 탐색) 같은 case 없음 — 모든 작업이 자동 lane 으로 종결. Cross-repo 게이트도 작동 (mctrader-web + mctrader-hub 양쪽 push).

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-web` 8 commit | 신규 4 파일 (signal_status / signal_control / metrics / admin_control_helpers) + 수정 4 파일 (pyproject / admin/__init__ / app / compose / 11_admin_control) | branch + PR 정보 본 retro 시점 별도 |
| `mctrader-hub` 1 commit | `monitoring/prometheus.yml` scrape job (mctrader-web port) | main 직접 push (ADR-019 D6 hub trunk-based) |

### 1.3 테스트 결과

| 카테고리 | 신규 test | passed | failed |
|---|---|---|---|
| `tests/api/test_admin_signal_status.py` | 5 (정상 / docker 미설치 / NotFound / 다중 worker / metrics fallback) | 5 | 0 |
| `tests/api/test_admin_signal_control.py` | 8 (start / stop / restart / not_found / state-machine reject / Idempotency dedupe / Idempotency-Key invalid / verb invalid) | 8 | 0 |
| `tests/api/test_admin_metrics.py` | 2 (200 OK + content-type / Gauge update on self-HTTP) | 2 | 0 |
| `tests/dashboard/test_admin_control_helpers.py` | 24 (verb gating × state matrix + state badge + uptime format) | 24 | 0 |
| 기존 테스트 (회귀) | ~496 | ~496 | 0 |
| **합계 (mctrader-web)** | **신규 39** | **535** | **0** |

→ **535 PASSED, 0 회귀**. 신규 39 test (api 15 + dashboard 24). RETRO-MCT-119 web overhaul 의 528 → 535 (+7) 는 신규 39 test 증가 vs 일부 deselect 변동 합산 결과로 정합. 헬퍼 모듈 분리가 24 unit test 견인 — `admin_control_helpers.py` 가 page 코드와 분리된 의도 적중.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 + RETRO-MCT-121 §5.5 + RETRO-MCT-122-123 §1.4 + RETRO-MCT-124 §1.4 + RETRO-MCT-119-web §1.5 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 fix (8 task feat commit) | 8 | 53% | 본 fix |
| 자체 발견 fix — Task 2 docker.errors mock 패턴 (`_docker_errors` alias) | 1 | 7% | **Cat B (self-discovered)** |
| 자체 발견 fix — Task 2 `require_role("viewer")` 누락 → 추가 | 1 | 7% | **Cat B** |
| 자체 발견 fix — Task 2 `datetime.utcnow()` deprecation → `datetime.now(timezone.utc)` | 1 | 7% | **Cat B** |
| 자체 발견 fix — Task 3 Idempotency dedupe 미구현 → check/store 추가 | 1 | 7% | **Cat B** |
| 자체 발견 fix — Task 3 stop verb / not_found 테스트 누락 → 추가 | 1 | 7% | **Cat B** |
| 자체 발견 fix — Task 3 Idempotency-Key fixture UUID4 regex 불통과 → 교체 | 1 | 7% | **Cat B** |
| 자체 발견 fix — Task 1 requires-python `<3.15` 광역 확장 → `<3.13` 롤백 | 1 | 7% | **Cat B** |

→ Cat B **47% (7 사례)**, 본 fix 53% (8). **Cat A 0, Cat C 0**. RETRO-MCT-119-web overhaul §5.2 의 25% → 본 Story 47% 로 약 2배. 단, 모두 single-Story scope 자체 발견 (Cat A pre-existing 0, Cat C 다른 Story finish-up 0). **신규 외부 의존 + 신규 endpoint 3종 + 신규 페이지 동시 도입의 첫 노출 비용**으로 정상 lane (RETRO-MCT-124 §1.4 의 21% 와 같은 카테고리 — 외부 의존 첫 노출). §3 항목 7개의 root cause 4가지 (외부 모듈 mock semantics / 횡단 cross-cutting 누락 / API contract 누락 / dependency range fabrication) 분석은 §3 + §5.2 참조.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-web` | feat branch | (확인 별도) | (확인 별도) | (확인 별도) |
| `mctrader-hub` | `main` (직접 push) | ✅ | (없음, ADR-019 D6 hub trunk-based) | ✅ |

→ **2-repo cross-repo Story** (web 주, hub 인프라 1줄). RETRO-MCT-122-123 의 3-repo (data + engine + hub) 보다 단순. RETRO-MCT-124 의 2-repo (signal-collector + hub) 와 동일 lane.

---

## 2. 잘된 점

### 2.1 헬퍼 모듈 분리 → 24 unit test 견인 — Streamlit 페이지 testability 패턴 정착

`dashboard/admin_control_helpers.py` 신규 모듈에 verb gating + state badge + uptime format 등 **순수 함수** 추출. 결과:

| 측면 | 효과 |
|---|---|
| Test 수 | 페이지 직접 테스트 시 ~5 (AppTest 한계) → 헬퍼 분리 후 24 (4.8배) |
| 실행 속도 | unit test ms 레벨, AppTest 의 streamlit re-exec 비용 회피 |
| matrix 검증 | verb × current_state 조합 (start/stop/restart × running/exited/not_found 등) 을 parametrize 로 일괄 — page 만으로는 불가능 |

→ **순수 함수 추출 패턴** 이 Streamlit page 코드의 testability 한계 회피 표준. RETRO-MCT-119-web overhaul §2.3 의 "AppTest monkeypatch 가능" 발견과 직교 — AppTest 는 page 자체, 헬퍼 분리는 logic 추출 둘 다 필요. **mctrader-web testing 표준 박제 후보 (§4.4)**.

### 2.2 `import docker.errors as _docker_errors` alias — mock contamination 방지 패턴 첫 박제

테스트 작성 시 `monkeypatch.setattr(docker, "from_env", mock_func)` 패턴 사용 시 발견된 함정:

```python
# 함정 (alias 없이)
import docker
...
try:
    container = client.containers.get(name)
except docker.errors.NotFound:  # mock 시 docker.errors 가 MagicMock → NotFound 도 MagicMock
    ...
```

mock 시 `docker.errors.NotFound` 가 MagicMock 인스턴스 (BaseException 미상속) → except 절에서 `TypeError: catching classes that do not inherit from BaseException is not allowed` 발생. **fix 패턴**:

```python
import docker
import docker.errors as _docker_errors  # alias — mock 안전
...
except _docker_errors.NotFound:
    ...
```

`import docker.errors` 는 모듈 binding 이므로 mock 영향 없음. **본 패턴이 mctrader 전 repo 의 외부 모듈 mock 패턴 첫 박제 사례** — §4.1 ADR 후보 발의.

### 2.3 Idempotency-Key dedupe — `control.py` 패턴 재사용 → DRY 적중

`signal_control.py` 의 Idempotency-Key 처리는 처음 누락 (Cat B §3.4) 됐으나 수정 시 **기존 `control.py` 패턴 동일하게 적용** — 24h SQLite dedupe 헬퍼 (`check_idempotency` / `store_idempotency`) 그대로 재사용.

→ **engine control endpoint 의 Idempotency 패턴이 signal control 까지 generalize 가능 실증**. 향후 다른 admin control endpoint (예: data collector 제어) 도입 시 같은 패턴 100% 재사용 가능. 의존성: 24h dedupe 가 signal worker 제어 의도 (start 두 번 누름 dedupe) 와 정합 — 보존 기간 결정도 control endpoint 와 동일하게 inherit.

### 2.4 `CollectorRegistry()` instance-level 패턴 — RETRO-MCT-124 §3.2 패턴 재현

본 Story `metrics.py` 의 Prometheus Counter/Gauge 가 instance-level `CollectorRegistry()` 사용. RETRO-MCT-124 §3.2 의 HealthExporter 와 동일 패턴 — `engine_state` / `signal_worker_up` / `heartbeat_age` 메트릭이 hot reload 시 중복 등록 에러 회피.

→ **Prometheus instance-level Registry 패턴 누적 2건 도달** (signal-collector + mctrader-web). RETRO-MCT-122-123 §4.2 의 HealthServer `/metrics` 표준 후보가 본 Story 에서 다시 재현 — **3건 도달, ADR 박제 임계**. §4.2 에서 박제 권장.

### 2.5 admin merge autonomy + 자동 PMO 회고 dispatch — 11번째 same-session 사례

본 Story 완료 직후 자동 PMO retro dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121/122+123/124/119-web/**125** = **12 Story (12+ PR + 2 신규 리포)** 동일 패턴 작동. ADR-020 D1 + MEMORY `feedback_admin_merge_autonomy.md` + `feedback_pmo_retro_mandatory.md` closed-loop 정착 누적 12건.

---

## 3. 발생한 이슈

### 3.1 [HIGH] docker.errors mock contamination — 외부 모듈 패치 시 except 절 TypeError

**관측**:
- `signal_status.py` 첫 구현에서 `except docker.errors.NotFound:` 사용
- `tests/api/test_admin_signal_status.py` 의 `monkeypatch.setattr("docker.from_env", mock_factory)` 패턴 적용 시 docker 모듈이 mock 화 — `docker.errors.NotFound` 가 MagicMock 인스턴스
- 첫 test 실행 시 `TypeError: catching classes that do not inherit from BaseException is not allowed`
- 해결: `import docker.errors as _docker_errors` alias 추가, except 절을 `_docker_errors.NotFound` 로 변경

**근본 원인 분석**:
1. **`import docker` 만 한 후 `docker.errors.X` 속성 접근 패턴** — mock 시점에 `docker` symbol 자체가 MagicMock 으로 교체되면 attribute access 가 MagicMock 반환
2. **`import docker.errors as _alias` 는 모듈 binding** — `_docker_errors` 가 실제 sub-module reference 보유, mock 영향 없음
3. **Python import semantics 미인지** — submodule import 와 attribute access 의 차이가 mock context 에서만 surface
4. ADR-018 (Defensive coding baseline) 은 application 입력 검증 측 — **mock-safe import 패턴 별개**

**의미**:
- 본 사례는 mctrader-web 첫 발견 — 그러나 **mctrader 전 repo 의 외부 모듈 (redis / boto3 / cloudscraper / ...) 패치 시 동일 함정** 잠재
- silent debt 위험 — 본 사례처럼 첫 test 실행 시 즉시 surface 되면 OK, 그러나 mock 사용 안 한 test path 에서는 production 첫 실행까지 silent 가능
- "alias 패턴 안전" 이 mctrader code 에 박제 부재 — 향후 작업자 (또는 LLM agent) 가 같은 함정 재현 위험

**평가**:
- §4.1 ADR 후보 발의 — **외부 모듈 import 시 alias 패턴 의무화** baseline
- 본 사례 1건이지만 **HIGH** — mctrader 전 repo 의 외부 의존성 (mctrader-data Redis / minio / boto3, mctrader-engine adapters / brokers, mctrader-web docker / streamlit, signal-collector cloudscraper / requests) 모두 잠재 — 즉시 박제 권장

### 3.2 [MEDIUM] `require_role("viewer")` cross-cutting concern 누락 — admin endpoint auth bypass 위험

**관측**:
- `signal_status.py` 첫 구현에 `require_role("viewer")` 의존성 미적용
- 다른 admin endpoint (e.g., `/admin/audit`, `/admin/rbac/tokens`) 는 모두 require_role 적용
- 자체 발견: 코드 리뷰 또는 spec/plan 재확인 시 catch
- 해결: `Depends(require_role("viewer"))` 추가

**근본 원인 분석**:
1. **신규 endpoint 작성 시 cross-cutting concern checklist 부재** — auth / rbac / idempotency / logging 등 횡단 관심사가 endpoint 별로 의식해야 함
2. **Plan 작성 시 "다른 admin endpoint 와 동일한 patterns" 명시 부재** — admin endpoint 작성 시 baseline (require_role + audit log + Idempotency-Key 등) 미박제
3. RETRO-MCT-119-web overhaul §3.4 의 fixture matrix (admin/operator/viewer) 가 본 endpoint 에서도 같은 갭으로 surface — fixture 추가 시점에 catch

**의미**:
- silent auth bypass — 운영 환경에서 unauthorized request 가 401/403 받지 못하고 200 받음
- 본 사례는 test 작성 시 multi-token fixture 사용 시점에 catch (RETRO-MCT-119-web §3.4 의 매트릭스 적용 효과)
- 그러나 single-token mode test 만 작성했다면 silent — production 첫 가동까지 발견 지연

**평가**:
- §4.2 ADR 후보 — **admin endpoint baseline checklist** (require_role + audit log + Idempotency-Key + rate limit 등)
- 본 사례 1건 + RETRO-MCT-119-web §3.4 fixture matrix gap 누적 — **ADR-018 D? 후보** 또는 mctrader-web internal convention 즉시 적용

### 3.3 [LOW] `datetime.utcnow()` deprecation — Python 3.12+ 경고

**관측**:
- `signal_status.py` 첫 구현에 `datetime.utcnow()` 사용 (현재 시각 측정용)
- Python 3.12 부터 `DeprecationWarning: datetime.datetime.utcnow() is deprecated`
- 해결: `datetime.now(timezone.utc)` 로 교체

**근본 원인 분석**:
1. **신규 코드 작성 시 Python 3.12+ deprecation 인지 부족** — 본 case 는 LLM-generated 코드의 stale knowledge
2. CI 가 deprecation 을 fail 로 분류 안 함 — silent debt
3. Python 3.13 에서 removal 예정 → 향후 hard fail

**의미**:
- 본 사례 1건 — 1개 줄 수정으로 회복
- 그러나 mctrader 전 repo 의 `datetime.utcnow()` grep 시 다수 잠재
- requires-python 가 `>=3.11,<3.13` 이라 3.12 만 지원 — deprecation warning 만 발생, 실제 fail 없음. 그러나 3.13 전환 시점에 collective surface

**평가**:
- 본 사례 1건 — `grep -r "datetime.utcnow" src/` 로 일괄 grep + 교체 가능
- ADR 박제 불필요 — ruff `DTZ005` rule 활성화로 lint level 검출 가능
- §6 #3 권고 — ruff DTZ rule 활성화

### 3.4 [HIGH] Idempotency-Key dedupe 미구현 — 헤더만 받고 dedup logic 없음

**관측**:
- `signal_control.py` 첫 구현이 `Idempotency-Key` 헤더를 함수 인자로 받지만 **`check_idempotency` / `store_idempotency` 호출 없음**
- 동일 key 로 두 번 호출 시 두 번 모두 docker 액션 실행 — 의도된 dedup 동작 위반
- 해결: 기존 `control.py` 의 dedupe 패턴 (24h SQLite store) 동일하게 적용

**근본 원인 분석**:
1. **API contract "선언" 과 "구현" 분리** — 함수 signature 에 `Idempotency-Key: str = Header(...)` 만 있으면 외형상 implements
2. **Plan 명세 불충분** — "Idempotency-Key 헤더 수용" 까지만, "dedupe behavior" 명시 부재
3. **테스트 누락** — 첫 test 작성 시 dedupe 동작 검증 case 부재 (§3.5 와 함께 catch)

**의미**:
- production 시 운영자가 "stop" 두 번 누름 → docker stop 두 번 실행 (idempotent) → OK?
- 그러나 race 조건 (start 후 stop 동시) 시 의도와 다른 final state 가능
- API consumer (UI / script / monitoring) 가 dedupe 신뢰 → 두 번째 응답 200 이지만 docker 액션 미실행 가정 — 신뢰 위반
- 본 사례는 test 보강 (§3.5) 시점에 catch — 운 좋은 timing

**평가**:
- §4.2 ADR 후보 (admin endpoint baseline checklist) 와 동일 — Idempotency-Key 처리는 **헤더 수용 + dedupe 호출 양쪽** 묶음 의무
- 본 사례 1건이지만 **HIGH** — silent contract 위반, production 직격 위험

### 3.5 [MEDIUM] stop verb / not_found 상태 테스트 누락 — state machine matrix 불완전

**관측**:
- `test_admin_signal_control.py` 첫 구현이 start / restart / state-machine reject 케이스만 cover
- stop verb test 누락 — `(verb=stop) × (current_state=running)` matrix 한 칸 비어있음
- not_found 케이스 누락 — `(verb=*, current_state=not_found)` 행 없음
- 해결: 누락 4 case 추가 (stop × running, stop × already_stopped, * × not_found 등)

**근본 원인 분석**:
1. **state machine matrix 작성 의무 부재** — verb (start/stop/restart) × current_state (running/exited/not_found 등) 표가 plan 에 없음
2. **TDD test-first 미적용** — 테스트가 코드 작성 후 작성됨 → matrix 누락 발견 지연
3. RETRO-MCT-119-120 §3.x state machine baseline 회고가 engine 측 — admin endpoint 에서도 동일 matrix 의무 미박제

**의미**:
- 누락된 path 가 silent buggy 가능 — `not_found` case 에 docker exception 처리 누락 시 500 반환 등
- 본 사례는 test 작성 시점에 self-review 로 catch — coverage 자동 분석 도구가 path 누락 surface 했으면 더 빨랐음

**평가**:
- §4.3 plan-writing checklist — "state machine 동작 endpoint 작성 시 verb × state matrix 표 의무"
- 본 사례 1건 + 다른 control endpoint 추가 시 동일 함정 → ADR 또는 superpowers:writing-plans skill 갱신

### 3.6 [LOW] Idempotency-Key fixture UUID4 regex 불통과

**관측**:
- 테스트 fixture 의 Idempotency-Key 가 `"00000000-0000-0000-0000-000000000001"` (UUID format 이지만 v4 아님)
- API 가 UUID4 regex 검증 — `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` 형태
- "0000...01" 의 13번째 문자가 `0` (4가 아님), 17번째 문자가 `0` (8/9/a/b 아님) → regex 불통과 → 422
- 해결: `"12345678-1234-4abc-89ab-123456789012"` (정규 UUID4 형식) 로 교체

**근본 원인 분석**:
1. **테스트 fixture data 의 형식 검증 부재** — UUID 처럼 보이는 placeholder 값이 실제 spec 미준수
2. **API regex strictness 가 테스트 환경에서도 active** — production strict + dev lenient 분리 안 됨 (정상 — 일관성 우선)
3. **uuid 모듈 사용 안 함** — fixture data 직접 hand-write, `uuid.uuid4()` 사용 시 자동 회피 가능

**의미**:
- 본 사례 1건 — fixture data correction 으로 회복
- 그러나 다른 정규식 검증 endpoint 에서 fixture data 조작 시 동일 함정 가능

**평가**:
- 즉시 대응: fixture 작성 시 `str(uuid.uuid4())` 표준 사용
- 박제 불필요 — pytest fixture 작성 표준 (auto-generated UUID) 권장 정도

### 3.7 [LOW] requires-python `>=3.11,<3.15` 광역 확장 → `<3.13` 롤백

**관측**:
- pyproject.toml 의 requires-python 이 `>=3.11,<3.15` 로 광역 확장됨 (LLM-generated)
- 그러나 upstream mctrader-* packages 모두 `<3.13` 요구 (mctrader-data / mctrader-engine 등)
- 광역 확장 시 dependency resolver 가 3.13/3.14 환경에서 mctrader-web 설치 시도 → upstream 설치 실패
- 해결: `<3.13` 롤백

**근본 원인 분석**:
1. **dependency range fabrication** — RETRO-MCT-124 §A.2.5 (cloudscraper>=2.3 fabrication) 와 동일 패턴
2. **upstream constraints 미확인** — mctrader-data / mctrader-engine 의 requires-python 미인지 상태로 mctrader-web 만 광역 확장
3. **6 repo cross-repo Python version constraint coordination** baseline 부재

**의미**:
- 광역 확장 자체가 install 시점 즉시 fail — silent debt 아님 (good)
- 그러나 cross-repo Python version constraint 가 implicit
- 향후 mctrader 전체 Python 3.13 전환 시 6 repo 동시 갱신 필요 — 별도 sweep Story

**평가**:
- 본 사례 1건 — 즉시 회복
- RETRO-MCT-124 §A.2.5 와 함께 누적 2건 — **dependency version range fabrication** 패턴 임계 도달
- §4.5 ADR 후보 — dependency range 도입 시 PyPI / upstream 검증 의무 (RETRO-MCT-124 §A.4.3 ADR 후보 와 통합 박제 가능)

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] 외부 모듈 import alias 패턴 baseline — mock-safe import 표준

```
target_adr: ADR 신규 또는 ADR-018 D? amendment
amendment_type: artifact (코드 패턴) + governance (lint rule)
trigger: RETRO-MCT-125 §3.1 docker.errors mock contamination — `import docker.errors as _docker_errors` alias 패턴 첫 박제
배경:
  - `import docker` 후 `docker.errors.NotFound` 속성 접근은 mock 시 MagicMock 반환 → except 절 TypeError
  - `import docker.errors as _docker_errors` 는 submodule binding → mock 안전
  - mctrader 전 repo 의 외부 모듈 (redis / boto3 / cloudscraper / minio / docker / requests / streamlit / ...) 모두 잠재
  - 본 사례는 첫 test 실행 시 즉시 surface — 그러나 mock 사용 안 한 path 는 production 까지 silent
문제:
  - 외부 모듈 import 패턴이 mock context 에서만 differentiate
  - silent debt — 작업자 / LLM agent 가 함정 재현 위험
  - ADR-018 D1~D7 (Defensive coding baseline) 은 input validation 측 — mock-safe import 미박제
제안 결정:
  a) Lite: mctrader CLAUDE.md / docs/code-conventions/imports.md 박제 — "외부 모듈 except 절 사용 시 submodule alias 의무"
  b) Medium: ADR 신규 — 외부 모듈 import 패턴 baseline (alias + lazy import + boundary 분리)
  c) Heavy: ruff custom rule (RUF) 또는 pyright config — `import X` 후 `except X.errors.Y` 패턴 자동 검출 ban
배제 옵션:
  - 외부 모듈 mock 자체 회피 (real container test 만 사용) — CI 비용 폭증
권장 priority: HIGH (다음 외부 모듈 도입 Story 전 결정)
관련:
  - ADR-018 Defensive coding baseline
  - RETRO-MCT-125 §3.1
  - 잠재 영향 repos: mctrader-web (docker), mctrader-data (redis/boto3/minio), mctrader-engine (adapters), signal-collector (cloudscraper/requests)
```

### 4.2 [HIGH] admin endpoint baseline checklist — cross-cutting concerns 의무화

```
target_adr: ADR 신규 또는 ADR-018 D? amendment
amendment_type: governance + artifact (endpoint 작성 checklist)
trigger: RETRO-MCT-125 §3.2 require_role 누락 + §3.4 Idempotency dedupe 미구현 — cross-cutting concerns 누락 누적 2건 단일 Story 내
배경:
  - admin endpoint 작성 시 cross-cutting concerns 산재:
    - require_role 의존성 (admin/operator/viewer)
    - audit log emission
    - Idempotency-Key dedupe (mutation endpoint)
    - rate limit (있다면)
    - request validation (Pydantic)
  - 신규 endpoint 작성 시 endpoint 별 의식 → 누락 silent
  - 본 Story 에서 require_role + Idempotency dedupe 양쪽 누락 → test 보강 시점에 catch
문제:
  - silent auth bypass / silent contract 위반 가능
  - 본 사례는 운 좋게 test 보강 시점에 catch — single-token mode 만 테스트했다면 production 까지 silent
  - admin endpoint baseline 명시 부재 → endpoint 별 재발명
제안 결정:
  a) Lite (즉시): docs/web/admin-endpoint-checklist.md 박제 — 5 항목 (require_role / audit log / Idempotency-Key / Pydantic validation / rate limit) 표준
  b) Medium: ADR-018 D? amendment — "admin endpoint baseline" 또는 신규 ADR
  c) Heavy: pytest fixture / lint — admin endpoint 자동 검증 (PoC: route registration 시 `Depends(require_role(...))` 누락 detect)
배제 옵션:
  - middleware-level rbac (mctrader-web 현재 endpoint-level 패턴 — 변경 비용 큼)
권장 priority: HIGH (다음 admin endpoint 추가 Story 전 결정)
관련:
  - ADR-018 Defensive coding baseline
  - RETRO-MCT-119-web §3.4 fixture matrix gap (관련 패턴)
  - RETRO-MCT-125 §3.2 + §3.4 (단일 Story 내 누적 2건)
```

### 4.3 [MEDIUM] state machine endpoint 작성 시 verb × state matrix 의무화

```
target: superpowers:writing-plans skill 또는 mctrader-web internal convention
amendment_type: process (plan-writing checklist)
trigger: RETRO-MCT-125 §3.5 stop verb / not_found 케이스 테스트 누락
배경:
  - signal_control endpoint 가 verb (start/stop/restart) × current_state (running/exited/not_found 등) state machine
  - plan 에 matrix 표 부재 → test 작성 시 누락 가능
  - RETRO-MCT-119-120 의 engine state machine baseline 회고와 동일 lane (admin endpoint 에서 재현)
문제:
  - state machine path 누락 → silent bug 가능
  - test 작성자가 cell 별 의식 → 횡단 cell 누락 가능
제안 결정:
  a) Lite: writing-plans skill 에 checklist — "state machine 동작 endpoint 작성 시 verb × state matrix 표 의무"
  b) Medium: pytest parametrize 표준 — `@pytest.mark.parametrize("verb,state,expected", matrix)` 자동 cover
예상 결과:
  - state machine path 누락 0
  - test coverage 자동 cover
보류 사유:
  - 본 사례 1건 → 누적 ≥3 시 박제
  - matrix 자체는 manual 작성 — 자동화 어려움
```

### 4.4 [MEDIUM] mctrader-web Streamlit 페이지 — 헬퍼 모듈 분리 패턴 표준

```
target_adr: ADR 신규 또는 mctrader-web internal convention
amendment_type: artifact (코드 패턴) + process (페이지 작성 표준)
trigger: RETRO-MCT-125 §2.1 admin_control_helpers.py 분리 → 24 unit test 견인
배경:
  - Streamlit 페이지 직접 테스트 (AppTest) 는 한계 — re-exec 비용 + matrix 검증 어려움
  - 순수 함수 (verb gating / state badge / format 등) 추출 → unit test 4~5배 증가 + 실행 ms
  - RETRO-MCT-119-web overhaul §2.3 AppTest monkeypatch 와 직교 — AppTest = page, 헬퍼 = logic
문제:
  - 페이지 작성 표준 부재 → 작업자가 직접 페이지에 logic 작성 vs 헬퍼 분리 결정 매번 재방문
  - testability 격차 — 헬퍼 분리 안 한 페이지는 coverage 낮음
제안 결정:
  a) Lite (즉시): docs/web/page-conventions.md — "page = render only, helper = pure logic" 표준
  b) Medium: AppTest base fixture 에 헬퍼 모듈 의무 명시
  c) Heavy: ADR 신규 — Streamlit 2-tier (helper unit + page AppTest + e2e Playwright) testing 표준
예상 결과:
  - 페이지 testability 균일화
  - 헬퍼 재사용 (다른 페이지에서 동일 verb gating 등)
보류 사유:
  - 본 사례 1건 → 누적 ≥2 (다른 페이지에 동일 패턴 적용) 시 박제
  - mctrader-web internal convention 으로 즉시 적용 가능
```

### 4.5 [LOW] dependency version range fabrication baseline — RETRO-MCT-124 §A.4.3 통합

```
target_adr: RETRO-MCT-124 §A.4.3 외부 API baseline ADR 와 통합 발의
amendment_type: governance (PR reviewer checklist 확장)
trigger: RETRO-MCT-125 §3.7 requires-python 광역 확장 + RETRO-MCT-124 §A.2.5 cloudscraper 버전 fabrication — 누적 2건
배경:
  - LLM-generated pyproject.toml 의 의존성 version range fabrication 위험
  - RETRO-MCT-124 §A.2.5 cloudscraper>=2.3 (PyPI 실제 1.2.71 까지) — install 시점 catch
  - RETRO-MCT-125 §3.7 requires-python <3.15 (upstream <3.13) — install 시점 catch
  - 양쪽 모두 install 시점 즉시 fail → silent debt 아님 (good)
  - 그러나 사전 검증 cost (5분) 대비 install 시점 회복 cost (10~30분) ROI 양호
문제:
  - dependency version range 가 LLM 추정 — PyPI / upstream 검증 부재
  - cross-repo Python version constraint coordination 부재
제안 결정 (RETRO-MCT-124 §A.4.3 통합):
  a) Lite: PR reviewer checklist — "dependency version range 도입 시 PyPI / upstream 검증"
     - `pip index versions <pkg>` (PyPI 실제 버전 확인)
     - `grep requires-python` (cross-repo upstream 매트릭스 확인)
  b) Medium: ADR-018 D? amendment — dependency baseline (외부 API + version range 통합)
  c) Heavy: CI lint — pyproject.toml 의 dependency 가 PyPI 실재성 자동 검증
배제 옵션:
  - dependency 자동 generate (poetry lock 등) — 본 case 와 무관 (range 자체가 인간 결정)
권장 priority: LOW (RETRO-MCT-124 §A.4.3 ADR 박제 시 함께 처리)
관련:
  - RETRO-MCT-124 §A.4.3 외부 API baseline ADR 후보
  - RETRO-MCT-125 §3.7 cross-repo Python version constraint
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 12 Story sweep — token efficiency 누적 신기록

본 세션 (2026-05-09 ~ 2026-05-10 cross-day) 처리 누적:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 mctrader-market audit)
- MCT-114 (D1/D2 market-bithumb audit)
- MCT-115 (D1/D2/D3 mctrader-data audit)
- MCT-116 (D2/D3/D5 mctrader-engine audit)
- MCT-117 (D1/D4/D5 mctrader-web audit)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2 — 4071 LoC)
- MCT-121 (Upbit 거래소 — 신규 plugin repo + 4015 LoC)
- MCT-122+123 (DuckDB + Prometheus/Grafana — 1089 LoC, 3 repo cross-repo)
- MCT-124 (signal-collector — 신규 독립 리포 + 937 LoC)
- MCT-119 web overhaul (test 보강 — 528 PASSED + 50 신규)
- **MCT-125 (Admin Control 페이지 강화 — 신규 4 endpoint + 헬퍼 분리, 535 PASSED + 39 신규)**

→ **12 Story (12+ PR + 1 hub 직접 push + 2 신규 리포) + ~11000 LoC + 2 신규 plugin repo + 5 모니터링 + 5 시그널 컨테이너 + 신규 admin control = single-session completion**. RETRO-MCT-119-web overhaul §5.1 의 11+ Story 를 12 로 확장. **codeforge ζ arc velocity 가 admin UI 측 신규 endpoint + cross-cutting concerns 도입까지 일반화**.

### 5.2 외부 모듈 mock contamination 패턴 — 본 Story 첫 박제, 이전 Story 재현 0

mock contamination 검색 결과 (RETRO-MCT-106 ~ MCT-124 + web overhaul):
- MagicMock except 절 TypeError 사례: **본 Story 가 첫 박제**
- 이전 Story 에서 외부 모듈 mock 사용 사례: redis (signal-collector — fakeredis 우선) / boto3 (data) / requests (signal-collector workers) / streamlit (web) 등
- 그러나 **submodule attribute except 패턴** 은 본 Story 의 docker.errors 가 첫 사례

→ **본 Story 가 mctrader 첫 sub-module except 패턴 발생 점** — 다른 외부 모듈 (e.g., `boto3.exceptions.S3Error`, `redis.exceptions.ConnectionError`) 도입 시 동일 함정 잠재. §4.1 ADR 박제 시 사전 차단.

이전 Story 의 mock 패턴 비교:
| Story | 외부 모듈 | 패치 패턴 | 함정 발생? |
|---|---|---|---|
| MCT-124 (signal-collector) | redis | fakeredis 사용 (mock 회피) | 0 |
| MCT-124 (signal-collector) | requests / cloudscraper | requests-mock / pytest fixture | 0 (단순 return value mock) |
| MCT-122 (data) | duckdb | 실 DuckDB embedded (mock 안 함) | 0 |
| MCT-117 (web audit) | (입력 검증) | 없음 | 0 |
| **MCT-125 (web admin)** | **docker** | **monkeypatch.setattr** | **발생 (§3.1)** |

→ **submodule attribute except 패턴이 mctrader 에서 본 Story 첫 발생** — 향후 boto3 / redis / minio 도입 시 동일 함정 잠재. 본 Story §3.1 의 `_docker_errors` alias 패턴이 baseline 박제.

### 5.3 cross-cutting concerns 누락 패턴 — RETRO-MCT-119-web §3.4 와 함께 누적 2건

| Story | 누락 cross-cutting concern | catch 시점 |
|---|---|---|
| MCT-119-web | use_multi_token_auth fixture matrix 부재 | test 작성 시 401 발견 (§3.4) |
| **MCT-125** | **require_role + Idempotency-Key dedupe 양쪽 누락** | **test 보강 + multi-token fixture 사용 시점** |

→ **admin endpoint cross-cutting concerns 누락 누적 2건 도달**. §4.2 ADR 박제 임계 — 다음 admin endpoint 추가 Story 전 결정 권장. RETRO-MCT-119-web §3.4 의 fixture matrix gap 이 본 Story §3.2 require_role 누락의 catch 매개체로 작동 — fixture matrix 가 선제 적용 시 본 Story 누락 즉시 surface.

### 5.4 Prometheus instance-level Registry 패턴 — 누적 3건 도달, ADR 박제 임계

| Story | 적용 사례 | Registry 사용 |
|---|---|---|
| MCT-122 | mctrader-data `metrics.py` | 모듈 전역 (process-level singleton) |
| MCT-123 | mctrader-engine `metrics.py` | 모듈 전역 |
| MCT-124 | signal-collector `HealthExporter` | **instance-level** (§3.2 fix) |
| **MCT-125** | **mctrader-web `metrics.py`** | **instance-level** |

→ **누적 4 컴포넌트** (data + engine + signal-collector + web). 그 중 instance-level 2건 (signal-collector + web) — RETRO-MCT-124 §3.2 의 ADR 박제 보류 사유 ("3+ 컴포넌트 도입 시점에 재평가") 가 본 Story 에서 임계 도달. **§4.4 (HealthServer `/metrics` 표준 + instance-level Registry) 통합 ADR 박제 권장**. RETRO-MCT-122-123 §4.2 + RETRO-MCT-124 §3.2 + 본 Story §2.4 통합 발의.

### 5.5 부수 fix 카테고리 갱신 — Cat B 47% 신기록 (RETRO-MCT-124 31% 갱신)

| Story | Cat A | Cat B | Cat C | 본 fix |
|---|---|---|---|---|
| MCT-117 | 350% | <10% | 0 | 11 |
| MCT-119+120 | <10% | 17% | 0 | 29 |
| MCT-121 | <10% | 7% | 36% | 8 |
| MCT-122+123 | <10% | <10% | 43% | 8 |
| MCT-124 (Amendment 후) | 0% | **31%** | 0% | 11 |
| MCT-119-web | 0% | 25% | 0% | 6 |
| **MCT-125** | **0%** | **47%** (7 사례) | **0%** | **8** |

→ Cat B **47% 신기록**. **외부 의존 + cross-cutting concerns + 신규 endpoint 3종 + Streamlit 페이지 동시 도입의 첫 노출** — 본 Story 가 mctrader-web 측 가장 multi-faceted 작업 1건. RETRO-MCT-124 31% (외부 API friction) → MCT-125 47% (외부 모듈 mock + cross-cutting concerns + dependency range) 누적 lane 변경. **single-Story scope 내 다중 root cause 누적 패턴**:
- 외부 모듈 mock semantics (1)
- cross-cutting concerns 누락 (2)
- API contract 누락 (1)
- dependency range fabrication (1)
- Python deprecation (1)
- fixture data 형식 (1)

→ **여러 root cause 가 single-Story 에 누적 시 Cat B 비율 폭증** 패턴 박제. 향후 multi-faceted Story 작성 시 §4.2 ADR (admin endpoint baseline checklist) + §4.1 ADR (mock-safe import) + §4.5 ADR (dependency baseline) 병합 적용 시 Cat B ~20% 회피 가능 추정.

### 5.6 도구 선택의 적합성 누적 — Streamlit 페이지 + Docker SDK + Prometheus

본 Story 의 도구 선택 결정 4건:

| 결정 | 패턴 |
|---|---|
| Docker SDK (`docker>=7`) | mctrader-web 첫 docker 의존 도입 — Docker socket mount + container API |
| Prometheus client (`prometheus-client>=0.20`) | RETRO-MCT-122-123 §4.2 패턴 4번째 적용 (data/engine/signal-collector/web) |
| 헬퍼 모듈 분리 | RETRO-MCT-119-web §2.3 AppTest 패턴과 직교 — 페이지 testability 표준 |
| Idempotency-Key dedupe | 기존 control.py 패턴 100% 재사용 |

→ **소규모 / 표준 / 임베디드 우선 패턴** + **재사용 우선 패턴**. RETRO-MCT-122-123 §5.4 / RETRO-MCT-124 §5.5 누적 — 본 Story 가 5번째.

### 5.7 admin endpoint baseline 누적 — 외부 의존 도입 cost lane

mctrader-web admin endpoint 누적:
- `/admin/audit` (audit log)
- `/admin/rbac/tokens` (RBAC management)
- `/admin/control` (engine control — Idempotency-Key 첫 적용)
- `/admin/status/signal-workers` (본 Story §Task 2)
- `/admin/signal/{worker_id}/{verb}` (본 Story §Task 3)
- `/metrics` (본 Story §Task 4)

→ **6 endpoint 누적**. cross-cutting concerns (require_role / Idempotency-Key / audit log / rate limit) 가 **endpoint 별 재구현** 패턴. §4.2 ADR (admin endpoint baseline checklist) 박제 시 endpoint 추가 cost ~20% 회피 가능.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **[HIGH] §4.1 외부 모듈 import alias 패턴 baseline ADR 박제** — `import docker.errors as _docker_errors` 패턴이 mctrader 첫 mock contamination fix 사례. mctrader 전 repo 의 외부 의존성 (boto3 / redis / minio / cloudscraper / requests) 잠재. Lite (CLAUDE.md / docs/code-conventions/imports.md) 즉시 박제 + Medium (ADR 신규) 1주 관측 후 결정.

2. **[HIGH] §4.2 admin endpoint baseline checklist ADR 박제** — RETRO-MCT-119-web §3.4 + 본 Story §3.2 + §3.4 누적 3건 (cross-cutting concerns 누락). 5 항목 (require_role / audit log / Idempotency-Key / Pydantic validation / rate limit) 표준 docs/web/admin-endpoint-checklist.md 즉시 박제. 다음 admin endpoint 추가 Story 전 결정.

3. **[HIGH] §5.4 HealthServer `/metrics` + instance-level Registry 통합 ADR 박제** — RETRO-MCT-122-123 §4.2 + RETRO-MCT-124 §3.2 + 본 Story §2.4 누적 4 컴포넌트. instance-level Registry 패턴 + 0.0.0.0 bind + name convention 통합. Medium (mctrader-common 가칭 공유 라이브러리) 또는 Heavy (ADR 박제) 결정. 다음 컴포넌트 (additional dashboard / web-data-explorer 등) 추가 전.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Task 1 의존성 추가 (docker + prometheus-client + requires-python) + §3.7 롤백 | ~5% |
| Task 2 signal_status.py + 5 unit test + §3.1/3.2/3.3 self-discovered fix 3건 | ~15% |
| Task 3 signal_control.py + 8 unit test + §3.4/3.5/3.6 self-discovered fix 3건 | ~15% |
| Task 4 metrics.py + 2 unit test (instance-level Registry) | ~5% |
| Task 5 라우터 등록 (admin/__init__ + app.py) | ~3% |
| Task 6 인프라 (compose.yml Docker socket mount + hub prometheus.yml scrape) | ~5% |
| Task 7 admin_control_helpers.py + **24 unit test** (verb × state matrix parametrize) | ~15% |
| Task 8 11_admin_control.py 전면 재구성 (헬퍼 호출 + 폴링 + 그리드) | ~15% |
| 부수 fix 7건 (§3.1 ~ §3.7 — Cat B 47%) — 자체 catch + 회복 | ~10% |
| 535 test 검증 + Story file MCT-125 작성 | ~5% |
| 본 retro 작성 | ~7% |

→ **부수 비용 ~17%** (Cat B fix 7건 + retro 작성). RETRO-MCT-124 ~25% 보다 감소 — 본 Story 는 외부 API friction 0 (Docker SDK 는 호환성 안정), 7 self-discovered fix 가 **single test run 첫 노출**시 즉시 surface 되어 회복 사이클 짧음. §4.1/4.2/4.4 ADR 박제 시 향후 ~10% 회피 가능 추정.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-014**: Engine state machine — 본 Story signal worker state machine (running/exited/not_found) 와 동일 lane
- **ADR-018**: Defensive coding patterns — D? 후보 (mock-safe import baseline §4.1, admin endpoint baseline §4.2)
- **ADR-019**: Parallel agent isolation — D6 hub trunk-based (hub commit 직접 push)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro 12번째 closed-loop)
- **ADR-011**: CI standard — 535 PASSED green gate
- **MEMORY** `feedback_admin_merge_autonomy.md`: 12번째 same-session 사례
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_subagent_execution.md`: subagent-driven implementation 본 Story 8 Task 적용
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — admin UI 측 신규 endpoint + cross-cutting concerns 첫 도입
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준)
  - `RETRO-MCT-119-web-test-overhaul.md` (§3.4 fixture matrix gap — 본 Story §3.2 catch 매개체)
  - `RETRO-MCT-122-123.md` (§4.2 HealthServer `/metrics` 표준 후보 — §5.4 누적 임계 도달)
  - `RETRO-MCT-124-signal-collector.md` (§3.2 instance-level Registry — §5.4 누적, §A.4.3 외부 API baseline — §4.5 통합)

---

## 9. Story §11 회고 pointer (PENDING — Story file 갱신 권장)

- `docs/stories/MCT-125.md` 가 작성됨 (status=DONE)
- §11 회고 pointer 박제 권장: `RETRO-MCT-125.md`

ADR-020 D1 enforcement gap (RETRO-MCT-117 §3.2) 회피를 위해 Story file §11 갱신 별도 작업 권장 (본 retro 작성 직후 수행 가능).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **Story §11 회고 pointer 박제** (§9) — `docs/stories/MCT-125.md` 에 본 retro pointer 1줄 추가. 5분 단발성.
- **`grep -r "datetime.utcnow" src/`** (§3.3) — mctrader-web 전체 deprecation 일괄 grep + 교체 sweep. 10분 이내. ruff `DTZ005` 활성화 동반.
- **mctrader-web admin_control 실제 운영 검증** — Docker socket mount 후 컨테이너 내부에서 docker SDK 정상 작동 확인. start/stop/restart 1회씩 수동 실행 후 prometheus `/metrics` 응답 검증.

### 10.2 ADR 박제 (1주 관측 또는 즉시 검토)

- **[HIGH] §4.1 외부 모듈 import alias 패턴 baseline** — root cause 명확 + mctrader 전 repo 잠재 → 즉시 박제 권장
- **[HIGH] §4.2 admin endpoint baseline checklist** — RETRO-MCT-119-web §3.4 + 본 Story 누적 3건 임계 도달 → 즉시 박제 권장
- **[HIGH] §5.4 HealthServer `/metrics` + instance-level Registry 통합** — 누적 4 컴포넌트 임계 도달 → 즉시 박제 권장
- **[MEDIUM] §4.3 state machine endpoint matrix 의무화** — 1주 관측 후 누적 ≥3 시 박제
- **[MEDIUM] §4.4 Streamlit 페이지 헬퍼 분리 표준** — mctrader-web internal convention 즉시 적용 + 1주 관측 후 ADR 박제 결정
- **[LOW] §4.5 dependency version range fabrication** — RETRO-MCT-124 §A.4.3 통합 박제

### 10.3 별도 issue 발의

- **mctrader-web 전체 datetime.utcnow() sweep** (§3.3) — Python 3.13 전환 대비 일괄 교체
- **admin endpoint baseline 적용 sweep** — 기존 6 endpoint (audit / rbac / control / status / signal / metrics) 의 baseline checklist 누락 항목 일괄 점검
- **mctrader 전 repo `import X` + `except X.errors.Y` grep** — §4.1 ADR 박제 후 일괄 alias 패턴 적용 sweep

### 10.4 Admin Control 후속 Story 트리거

본 Story MCT-125 완료로 다음 Story 가능:
- **alerting rules** (RETRO-MCT-122-123 §10.5 + RETRO-MCT-124 §10.4 누적) — Prometheus alertmanager + signal worker stale > 5분 / docker container down / heartbeat_age 임계 alert
- **Grafana dashboard JSON drop-in** (RETRO-MCT-122-123 §10.1 + RETRO-MCT-124 §10.4 누적) — admin control 의 metrics 시각화
- **engine control + signal control 통합 페이지** — `/admin_control` + `/admin_signal` 분리됐다면 통합 또는 sidebar 표준화
- **signal worker logs 페이지** — Docker SDK 의 `container.logs()` 사용 + Streamlit 표시 (실시간 tail)

### 10.5 외부 모듈 mock 패턴 후속

- §4.1 ADR 박제 후 mctrader 전 repo `import X` + `except X.errors.Y` grep sweep — boto3 / redis / minio / cloudscraper / requests / docker / streamlit 등
- mock-safe import 표준 적용 후 회귀 test 작성 — 각 외부 모듈 patch 시 except 절 동작 검증

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
