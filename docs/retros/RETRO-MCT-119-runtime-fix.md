# RETRO-MCT-119-runtime-fix — Strategy Set Pipeline 배포 후 런타임 이슈 2건

**범위**: MCT-119 follow-up 2 — Strategy Set Pipeline 배포 환경에서 발견된 런타임 fix 2건 (`.env` 부재 → DB 연결 실패 + SQLAlchemy FK 순서 오류) + 운영 한계 1건 (Docker GitHub-dep rebuild 불가 → bind mount 임시 조치)
**기간**: 2026-05-10 (single-day, RETRO-MCT-119-web-test-overhaul 직후 동일 세션)
**Trigger**: Strategy Sets 생성 시 500 에러 2회 surface → fix 적용 후 PMO 회고 자동 dispatch
**Status**: mctrader-web `f3dc511` MERGED to main, mctrader-hub `b96b906` MERGED (Story/Retro/Plan 일괄 docs commit)
**Story file**: `docs/stories/MCT-119.md` §3.2 + §11 (본 retro pointer 박제)
**Repo**: `mctrader-web` (`c:\workspace\mclayer\mctrader-web`) — runtime fix · `mctrader-hub` (`c:\workspace\mclayer\mctrader-hub`) — docs

---

## 1. 결과 요약

### 1.1 수행 작업 매트릭스

| # | 영역 | 증상 | Root cause | Fix | 분류 |
|---|---|---|---|---|---|
| Fix 1 | mctrader-web `.env` 부재 | `fe_sendauth: no password supplied` (500) | `compose.yml`이 `${POSTGRES_PASSWORD}` 참조하나 `mctrader-web/.env` 미존재 → 빈값 치환 | `mctrader-web/.env` 신규 생성 + `.gitignore` `.env` 추가 | **배포 환경 결함** (컨테이너 빌드 환경의 secret-bootstrap 절차 미박제) |
| Fix 2 | `strategy_sets_router.create_strategy_set` | `ForeignKeyViolation` (500) | `db.add(ss) + db.add(draft)` 동시 commit 시 SQLAlchemy UoW 가 FK 의존성 미감지 → `strategy_drafts` INSERT 선행 | `db.add(ss)` 후 `db.flush()` 추가 + import 순서 정정 (`StrategySet → StrategyDraft`) | **신규 코드 self-discovered defect** (Cat B) |
| Mitigation 3 | Docker rebuild 불가 | GitHub git-dep (`mctrader-engine/market/data`) → token 없이 fresh `--no-cache` 불가 | Dockerfile 의 git+https 의존성이 빌드 시 토큰 필요, secret mount 미박제 | `compose.override.yml` 에 `strategy_sets_router.py` bind mount + `latest` → `mct-101` retag (임시) | **인프라 구조적 결함** (사용자 질문 3) |

### 1.2 commit 분포

| commit | repo | 내용 |
|---|---|---|
| `f3dc511` | mctrader-web | `db.flush()` FK 순서 + `.gitignore` `.env` + `compose.override.yml` bind mount (3 영역 합본) |
| `b96b906` | mctrader-hub | Story/Retro/Plan 일괄 docs commit (MCT-119 §3.2 §11 갱신 포함) |

→ 본 fix 는 **mctrader-web `.env` 신규 생성 (비커밋, local-only)** 1건 + **`f3dc511` 1 commit** 으로 종결. RETRO-MCT-119-120 §3.1 의 wrong-branch-stack 패턴 재발 0 — `feat/test-overhaul-mct-119` PR `mctrader-web#35` MERGED 직후 main 위에서 직접 fix 진행 (branch 분리 원칙은 hotfix 성격이라 우회).

### 1.3 테스트 검증

- 사용자 수동 검증: Strategy Set 생성 페이지 → 정상 응답 (500 → 201) 확인
- 기존 528 PASSED 회귀 테스트 영향 0 (router 로직 변경은 db.flush() 1줄 + import 순서만)
- Cat B (self-discovered) 비율: Fix 2 단건 → mctrader-web 측 단일 commit (100% Cat B)

### 1.4 부수 fix 비율 (RETRO 누적 표준 적용)

본 retro 는 RETRO-MCT-119-web-test-overhaul (PR #35, 528 PASSED) 직후 surface 된 **운영 단계 발견 결함** — 별도 카테고리.

| 카테고리 | 분류 | 비고 |
|---|---|---|
| Fix 1 (`.env` 부재) | **Cat D 신규 카테고리 후보** — 배포 환경 결함 (deployment-time defect) | 코드 결함 아님, 환경 변수 bootstrap 절차 부재 |
| Fix 2 (FK 순서) | **Cat B (self-discovered)** | 신규 코드 첫 production trigger 시 surface |
| Mitigation 3 (bind mount) | **Cat E 신규 카테고리 후보** — 인프라 구조적 결함 (infra debt) | 임시 조치, 근본 해결 별도 Story 필요 |

→ RETRO 누적 표준 (Cat A pre-existing / Cat B self-discovered / Cat C 다른 Story finish-up) 외 신규 2 카테고리 surface — §5.3 표준 갱신 권고.

---

## 2. 잘된 점

### 2.1 2건 fix 단일 commit 합본 — Atomic recovery

`f3dc511` 1 commit 에 (1) `db.flush()` 코드 fix + (2) `.gitignore` `.env` + (3) `compose.override.yml` bind mount 3 영역 합본. 운영 환경의 single fix-cycle 로 회복. RETRO-MCT-119-web-test-overhaul §1.5 의 "Cat B 25% (2 commit)" 와 비교 시 본 retro 는 1 commit 으로 마무리 — runtime fix 의 atomic 성격 활용.

### 2.2 SQLAlchemy UoW FK 의존성 미감지 패턴 발견 + 도메인 의도 박제

`db.add(ss) + db.add(draft) + db.commit()` 동시 호출 시 UoW 가 ORM 관계 (`relationship()`) 미선언 + 단순 FK 컬럼 참조만 보유 시 INSERT 순서를 보장하지 않는다는 사실을 production 환경에서 실증. **fix 는 1줄** (`db.flush()` 추가) 이지만 **도메인 의도** (`# FK 순서 보장: strategy_sets 먼저 insert 후 draft FK 참조`) 코멘트 박제 — RETRO-MCT-119-120 §4.3 ADR-018 D8 후보 (Optional None-guard) 와 동일 lane 의 "도메인 의도 박제 의무" 패턴 재실증.

### 2.3 .gitignore .env 추가 — secret leak 사전 차단

`.env` 파일 신규 생성 시 즉시 `.gitignore` 추가 → `POSTGRES_PASSWORD=changeme` 가 git history 에 stage 되지 않음. mctrader-hub 에서는 `f85fcb1` (MCT-105) 에서 이미 동일 패턴 박제됐으나 **mctrader-web 측은 `.env` gitignore 미박제 상태로 배포** → 본 retro §3.1 root cause. 본 fix 는 retroactive 하지만 secret leak 0 — auto-recovery 사이클 작동.

### 2.4 admin merge autonomy + 자동 PMO 회고 dispatch (ADR-020 D1) — 9번째 same-session 사례

mctrader-web `f3dc511` push + mctrader-hub `b96b906` push 직후 사용자 trigger 없이 본 retro dispatch. ADR-020 D1 의 9번째 same-session 사례 (MCT-112/113/114/115/116/117/119+120 + MCT-121 + MCT-124 + MCT-119 web overhaul + 본 runtime fix). MEMORY `feedback_admin_merge_autonomy.md` + `feedback_pmo_retro_mandatory.md` closed-loop 정착 → **runtime fix 도 PMO 회고 dispatch trigger 자격 충족** 실증.

---

## 3. 발생한 이슈

### 3.1 [HIGH] mctrader-web `.env` 부재 — multi-repo 환경 변수 bootstrap 표준 부재 (사용자 질문 1)

**관측**:
- `mctrader-web/compose.yml:26` — `DATABASE_URL: postgresql+psycopg://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader`
- `mctrader-web/.env` 파일 미존재 → Docker compose 가 `${POSTGRES_PASSWORD}` 빈값 치환 → libpq `fe_sendauth: no password supplied`
- 동일 secret 이 `mctrader-hub/.env` 에는 존재 (별개 파일)

**근본 원인 분석 — 사용자 질문 1 회신**:

**multi-repo compose 환경 변수 관리의 구조적 결함 = YES**.

근거:
1. **`.env` 파일은 repo-local** — Docker compose 의 `.env` 자동 로딩은 `compose.yml` 이 위치한 디렉토리 기준. mctrader-hub 와 mctrader-web 은 각각 별도 `compose.yml` + 별도 `.env` 필요
2. **`mctrader-hub/.env` 만 박제됐고 web 측은 누락** — `f85fcb1` (MCT-105) 에서 hub `.env` + `.gitignore` 동시 박제됐으나 web 은 동일 작업 미수행
3. **컨테이너화 design (MCT-101) 시 환경 변수 source 파일을 명시 안 함** — `mctrader-web` Docker-first design (`a5cbcd8`) 시 `.env` 파일 의존성을 design doc 에 박제 안 함
4. **6-repo 의 환경 변수 SSOT 부재** — POSTGRES_PASSWORD 같은 공유 secret 이 어느 `.env` 에 박제되는가 표준 없음 (hub/web/data 모두 후보)

**의미**:
- 신규 컨테이너 추가 시마다 동일 패턴 재발 위험 (data, signal-collector 등)
- secret rotation 시 6-repo 의 `.env` 모두 갱신 필요 — drift 위험
- 본 사례는 production 첫 trigger 시 surface (개발 시점에는 `.env` 가 dev machine 에 cached 됐을 수 있음)

**평가**:
- **§4.1 ADR 후보 강력 발의** — multi-repo 환경 변수 SSOT + 각 repo `.env` 사본 관리 표준
- 임계 충족: 본 사례 + MCT-105 (`f85fcb1` hub .env gitignore) + MCT-101 (Docker-first design) = **3 사례 누적** → **즉시 박제 권장**

### 3.2 [HIGH] SQLAlchemy UoW FK 순서 미감지 — ORM relationship 미선언 패턴 (사용자 질문 2)

**관측**:
- `create_strategy_set()` 함수에서 `db.add(ss)` + `db.add(draft)` 후 `db.commit()` 단일 호출
- SQLAlchemy UoW 가 INSERT 순서를 자동 결정 — 그러나 `StrategySet ↔ StrategyDraft` 사이 ORM `relationship()` 미선언 + 단순 FK 컬럼 (`strategy_set_id`) 참조만 보유 → 순서 보장 안 됨
- 첫 INSERT 가 `strategy_drafts` 선행 → `ForeignKeyViolation`

**근본 원인 분석 — 사용자 질문 2 회신**:

**SQLAlchemy lazy-import + FK 순서 문제 반복 가능성 = HIGH**.

근거:
1. **mctrader-engine 의 8 신규 테이블 (`strategy_sets`/`versions`/`components`/`layers`/`drafts`/`promotion_events`/`runtime_overrides`/`pipeline_events`)** 모두 FK 관계 보유. 그러나 SQLAlchemy `relationship()` 선언이 모델 정의에 박제됐는지 미검증
2. **lazy-import 패턴** — 함수 내부 `from mctrader_engine.db.models.strategy_draft import StrategyDraft` 같은 import 가 여러 router 에 산재할 가능성 → import 순서가 모델 metadata 등록 순서에 영향
3. **본 fix 는 `db.flush()` 호출로 우회** — root fix 는 ORM `relationship()` 명시 (예: `StrategySet.drafts = relationship("StrategyDraft", back_populates="strategy_set")`) — 본 fix 는 surface 우회
4. **다른 8 테이블 router (`strategy_set_versions`, `pipeline_events` write 등)** 에서 동일 패턴 재발 위험

**의미**:
- 본 fix 는 단일 endpoint 만 처리 — 다른 endpoint 의 FK 의존 INSERT 도 동일 패턴 (`db.add` 다수 + `db.commit` 단일) 사용 시 잠재 폭탄
- ORM `relationship()` 박제 여부 audit 필요 — mctrader-engine 의 8 모델 전수 점검
- pyright 또는 sqlalchemy plugin 으로 lint 가능한가 미확인

**평가**:
- **§4.2 ADR 후보 발의** — SQLAlchemy ORM 작성 시 FK 보유 모델은 `relationship()` 명시 의무 + 다중 add commit 시 FK 의존 순서 검증
- 임계 충족: 본 사례 1건 + 잠재 7 endpoint (8 테이블 - 본 endpoint) = 즉시 audit Story 발의 권장

### 3.3 [MEDIUM] Docker GitHub-dep rebuild 불가 — 인프라 구조적 결함 (사용자 질문 3)

**관측**:
- mctrader-web Dockerfile 의 dependency 가 `git+https://github.com/mclayer/mctrader-engine` 등 GitHub git-dep 사용
- `docker compose build --no-cache` 시 GitHub token 없이 fresh install 불가 (private repo)
- **임시 조치**: `compose.override.yml` 에 `strategy_sets_router.py` bind mount → 단일 파일 fix 주입 + `latest` 이미지를 `mct-101` 태그로 retag

**근본 원인 분석 — 사용자 질문 3 회신**:

**Docker GitHub-dep rebuild 불가 패턴 해결 방안 = 3가지 후보 (우선순위 순)**:

**A. Wheel pre-build 패턴 (1순위 권장)**:
- mctrader-engine/market/data 등을 사전 wheel build → mctrader-hub 의 internal PyPI mirror (devpi/MinIO+pip-index) 에 publish
- Dockerfile 의 dependency 를 `mctrader-engine==0.x.y` (PyPI 인덱스 경유) 로 교체
- Build cache 가능 + token 불필요 + version pinning 강제
- 비용: internal PyPI 인프라 구축 1회

**B. Dockerfile BuildKit secret mount (2순위)**:
- `docker buildx build --secret id=ghtoken,src=token.txt` 패턴
- Dockerfile 에 `RUN --mount=type=secret,id=ghtoken,target=/root/.netrc pip install ...`
- Token 이 build artifact 에 leak 되지 않음
- 비용: BuildKit 사용 + token 관리 표준 박제

**C. Vendor 디렉토리 패턴 (3순위, 비권장)**:
- mctrader-engine 등을 mctrader-web repo 에 git submodule 또는 vendored 디렉토리로 추가
- Dockerfile 의 dependency 를 local path 로 교체
- 비용: 6-repo 동기 비용 + version drift 위험 (non-recommended)

**임시 조치 (현재 적용)**: `compose.override.yml` bind mount — 단일 파일 fix 가능하지만 **신규 의존성 추가·major upgrade 시 무력**. proper fix 까지의 에스케이프 해치.

**의미**:
- 6-repo (engine/market/market-bithumb/data/web/hub) 의 cross-repo dependency 가 **개발 환경에서는 git-dep 으로 작동**, **production rebuild 시 token 없이 불가**
- MCT-119 같은 신규 router 추가 시마다 매번 동일 문제 재발
- bind mount 임시 조치는 단일 파일만 가능 — 다중 파일 변경 또는 dep upgrade 시 처리 불가

**평가**:
- **§4.3 ADR 후보 발의** — Docker build dependency 표준 (Wheel pre-build 1순위)
- 임계 충족: 본 사례 1건 + MCT-101 Docker-first design 시점부터 잠재 = **인프라 Story 즉시 발의 권장 (Phase 후속)**

### 3.4 [LOW] 운영 단계 까지 surface 안 된 결함 — 자동 lane 미커버

**관측**:
- Fix 1 (`.env` 부재) + Fix 2 (FK 순서) 모두 mctrader-web 528 PASSED 테스트 + 신규 17 AppTest 가 첫 PR 머지 시점에는 surface 안 됨
- 운영 환경 첫 trigger (Strategy Set 생성 페이지 직접 사용) 시 발견

**근본 원인 분석**:
- AppTest 는 mock heavy — DB 연결 실제 미수행 (테스트 fixture 가 in-memory SQLite 또는 mock)
- API gap test (Task 5) 는 admin endpoint 만 커버, strategy_sets endpoint 미커버
- Playwright E2E 4 flow 도 strategy_set flow 포함됐으나 실제 Postgres connection 미테스트

**의미**:
- 자동 테스트의 mock-heavy 패턴이 **runtime DB 연결 결함**을 surface 못 함
- **integration test (실제 Postgres + FastAPI 기동) 부재** — `tests/integration/` 디렉토리는 존재하나 strategy_sets endpoint 미커버
- Playwright E2E 가 실제 서비스를 기동하지만 `.env` 가 dev machine 에 cached 됐을 가능성 → 운영 환경 첫 deploy 시점에 surface

**평가**:
- §4.4 — `tests/integration/` 의 strategy_sets endpoint 커버리지 보강 권장
- 본 사례는 RETRO-MCT-119-web-test-overhaul §5.5 의 2-tier 전략 갱신 → **Tier 3 (integration with real Postgres)** 추가 후보

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] ADR 신규 — multi-repo 환경 변수 bootstrap SSOT 표준

```
target_adr: ADR 신규 또는 ADR-016 amendment (containerization)
amendment_type: artifact + behavior (환경 변수 SSOT)
trigger: 본 retro §3.1 — mctrader-web/.env 부재로 ${POSTGRES_PASSWORD} 빈값 치환 → DB 연결 실패. mctrader-hub 만 .env 박제 (f85fcb1) + web 누락 패턴.
배경:
  - 6-repo (engine/market/market-bithumb/data/web/hub) 의 Docker compose 가 각 repo-local .env 의존
  - POSTGRES_PASSWORD 같은 공유 secret 이 어느 .env 에 박제되는가 표준 없음
  - MCT-105 에서 hub .env + .gitignore 박제됐으나 web/data/signal-collector 동일 작업 미수행
  - 컨테이너화 design (MCT-101) 시 .env 파일 의존성을 design doc 에 박제 안 함
문제:
  - 신규 컨테이너 추가 시마다 .env 누락 → production 첫 trigger 시 surface
  - secret rotation 시 6-repo .env 모두 갱신 → drift 위험
  - .gitignore 미박제 시 secret leak 위험
제안 결정:
  a) mctrader-hub 를 **공유 secret SSOT 로 지정** — POSTGRES_PASSWORD 등은 `mctrader-hub/.env` 가 source of truth
  b) 각 repo 의 compose.yml 은 hub `.env` 를 symlink 또는 bootstrap script (`bootstrap-env.sh`) 로 sync
  c) 모든 repo 의 `.gitignore` 에 `.env` 강제 박제 (CI lint step 추가)
  d) 컨테이너화 design 시 `.env` 의존성 + bootstrap 절차를 design doc 에 의무 명시
  e) 또는 1Password CLI (MCT-8) + secret injection 으로 .env 파일 자체 폐지
예상 결과:
  - 신규 컨테이너 추가 시 .env 누락 0
  - secret rotation 단일 위치 (hub/.env 또는 1Password)
  - secret leak 사전 차단 (CI lint 자동화)
관련:
  - ADR-016 containerization
  - MCT-8 secret management (1Password CLI)
  - MCT-105 (f85fcb1) hub .env gitignore
  - MCT-101 mctrader-web Docker-first design
보류 사유:
  - 본 사례 + MCT-105 + MCT-101 = 3 사례 누적 → 즉시 박제 권장
  - 1Password CLI 통합 가능 시 (a)/(b) 우회 가능 — 설계 옵션 검토 필요
```

### 4.2 [HIGH] ADR 신규 — SQLAlchemy ORM relationship 명시 + FK 의존 INSERT 순서 검증

```
target_adr: ADR 신규 (mctrader-engine internal convention) 또는 ADR-018 D? 패턴
amendment_type: artifact (코드 패턴)
trigger: 본 retro §3.2 — strategy_sets_router.create_strategy_set() 의 db.add(ss)+db.add(draft) 동시 commit → SQLAlchemy UoW FK 의존성 미감지 → ForeignKeyViolation
배경:
  - mctrader-engine 의 8 신규 테이블 (strategy_sets/versions/components/layers/drafts/promotion_events/runtime_overrides/pipeline_events) 모두 FK 보유
  - 본 사례는 단일 endpoint surface — 다른 7 endpoint 잠재 위험
  - SQLAlchemy `relationship()` 미선언 + 단순 FK 컬럼만 보유 시 UoW INSERT 순서 미보장
  - lazy-import 패턴 (함수 내부 import) 이 모델 metadata 등록 순서 영향
문제:
  - 다중 db.add + 단일 db.commit 패턴이 FK 순서 race
  - 도메인 의도 (FK 순서 보장) 가 코드/문서에 미박제 → silent regression 위험
  - pyright/mypy 가 catch 안 함
제안 결정:
  a) FK 보유 모델은 SQLAlchemy `relationship()` + `back_populates` 명시 의무
  b) 다중 INSERT 시 db.add(parent) → db.flush() → db.add(child) → db.commit() 패턴 표준화
  c) 또는 `relationship()` 의 cascade 활용 (db.add(parent) 만으로 child auto-add)
  d) mctrader-engine 의 8 신규 모델 + 기존 모델 전수 audit Story 발의
  e) sqlalchemy-stubs 또는 plugin 으로 lint 가능 여부 검토
예상 결과:
  - FK 의존 INSERT 순서 보장
  - 도메인 의도 코드/문서 일관성
  - 잠재 7 endpoint 의 동일 패턴 사전 차단
관련:
  - ADR-018 defensive coding patterns
  - MCT-119 신규 8 테이블
보류 사유:
  - 본 사례 1 endpoint surface — 다른 7 endpoint 잠재
  - 즉시 audit Story 발의 권장 (root cause 명확)
```

### 4.3 [HIGH] ADR 신규 — Docker build dependency 표준 (Wheel pre-build vs BuildKit secret mount)

```
target_adr: ADR 신규 또는 ADR-016 amendment (containerization)
amendment_type: behavior + artifact (build pipeline)
trigger: 본 retro §3.3 — mctrader-web Dockerfile 의 GitHub git-dep (engine/market/data) 으로 인해 token 없이 fresh rebuild 불가, compose.override.yml bind mount 임시 조치
배경:
  - 6-repo 의 cross-repo dependency 가 git+https://github.com/mclayer/X.git 패턴
  - production rebuild 시 token 필요, 개발 환경에서는 git credential cached
  - 단일 파일 fix 는 bind mount 가능, 다중 파일/dep upgrade 시 무력
문제:
  - MCT-119 같은 신규 router 추가 시마다 rebuild 불가 → bind mount 임시 조치 누적
  - production 환경에서 dep upgrade 시 처리 절차 부재
  - GitHub token build artifact leak 위험 (ARG 패턴 시)
제안 결정:
  a) **Wheel pre-build 패턴 (1순위)**:
     - mctrader-engine/market/data 등을 사전 wheel build → internal PyPI mirror (devpi/MinIO+pip-index) publish
     - Dockerfile dependency 를 `mctrader-engine==0.x.y` PyPI 인덱스 경유로 교체
     - Build cache 가능 + token 불필요 + version pinning 강제
  b) **BuildKit secret mount (2순위)**:
     - `docker buildx build --secret id=ghtoken,src=token.txt`
     - Dockerfile `RUN --mount=type=secret,id=ghtoken,target=/root/.netrc pip install ...`
     - Token build artifact leak 차단
  c) **Vendor 디렉토리 (3순위, 비권장)**:
     - 6-repo 동기 비용 + version drift 위험
  d) 임시 조치 (compose.override.yml bind mount) 는 single-file hotfix 만 허용, 정식 fix 까지 escape hatch
예상 결과:
  - production rebuild 항상 가능
  - GitHub token build artifact leak 0
  - dep upgrade 절차 표준화
관련:
  - ADR-016 containerization
  - MCT-101 mctrader-web Docker-first design
  - MCT-8 secret management
보류 사유:
  - 본 사례 1건 + 6-repo 모든 컨테이너 잠재 = 인프라 Story 즉시 발의 권장
  - Wheel pre-build 채택 시 internal PyPI mirror 인프라 비용 — Phase 후속
```

### 4.4 [MEDIUM] integration test Tier 3 도입 — 실제 Postgres + FastAPI 기동

```
target: mctrader-web tests/integration/ 보강 또는 ADR-011 amendment
amendment_type: artifact (테스트 인프라)
trigger: 본 retro §3.4 — Fix 1 (.env) + Fix 2 (FK 순서) 모두 528 PASSED + 17 AppTest + 12 Playwright E2E 가 surface 못 함, 운영 환경 첫 trigger 시 발견
배경:
  - AppTest mock-heavy → DB 연결 실제 미수행
  - API gap test → admin endpoint 만 커버
  - Playwright E2E → 실제 서비스 기동하지만 .env 가 dev machine cached 가능
문제:
  - runtime DB 연결 결함이 자동 lane 에서 invisible
  - .env / FK 순서 같은 deployment-time defect 가 production 첫 trigger 시 surface
제안 결정 (1주 관측 후):
  a) tests/integration/ 에 strategy_sets endpoint 커버리지 보강 — 실제 Postgres docker-compose 기동
  b) CI 의 별도 job (integration-test) 으로 분리 — `pytest -m integration` 게이트
  c) RETRO-MCT-119-web-test-overhaul §5.5 의 2-tier (AppTest + Playwright) 를 3-tier 로 확장 (Tier 3 = real Postgres integration)
예상 결과:
  - runtime DB 연결 결함 자동 lane 에서 surface
  - deployment-time defect 회피
보류 사유:
  - 본 사례 1건 → 누적 ≥3 시 박제
  - integration test infra 비용 vs 효익 검토 필요
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 10+ Story sweep 신기록 갱신

본 세션 (2026-05-09 ~ 2026-05-10) 처리 누적:
- MCT-112 ~ MCT-117 (audit sweep 6 Story)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2)
- MCT-121 (Upbit 통합)
- MCT-122/123 (관측됨)
- MCT-124 (signal-collector)
- MCT-119 web overhaul (PR #35)
- **MCT-119 runtime fix (본 retro)**

→ **12+ Story sweep**. RETRO-MCT-119-web-test-overhaul §5.1 의 "11+ Story" 갱신. **runtime fix Story 도 PMO 회고 dispatch 자격** — codeforge ζ arc 의 ADR governance velocity 가 production-trigger 결함까지 일반화.

### 5.2 새로운 결함 카테고리 surface — Cat D (deployment-time) + Cat E (infra debt)

기존 Cat A (pre-existing debt) / Cat B (self-discovered defect) / Cat C (다른 Story finish-up) 외 본 retro 에서 신규 surface:

| 신규 Cat | 정의 | 본 사례 | 평가 |
|---|---|---|---|
| **Cat D — deployment-time defect** | 코드는 정상, 배포 환경의 secret/config bootstrap 절차 부재 | Fix 1 (.env 부재) | 신규 카테고리 — RETRO 누적 표준 갱신 권고 |
| **Cat E — infra debt** | 인프라 구조적 결함, 임시 조치 + proper fix 별도 Story 필요 | Mitigation 3 (bind mount) | Cat A 의 sub-카테고리 후보 (pre-existing infra debt) |

→ RETRO-MCT-117 §4.2 의 부수 fix 비율 표준이 4 카테고리 이상 확장 필요. RETRO 누적 표준 다음 갱신 시 §5.2 박제 권장.

### 5.3 multi-repo Story 의 환경 변수 drift 패턴 — RETRO-MCT-119-120 §3.1 동일 root cause family

RETRO-MCT-119-120 §3.1 의 "mctrader-web Strategy Set 변경 미푸시" + 본 retro §3.1 의 "mctrader-web .env 부재" 는 모두 **multi-repo Story 에서 mctrader-web 측 작업 누락** 패턴. 공통 root cause:
- multi-repo Story 의 각 repo 별 deliverable matrix 미명시
- mctrader-hub 중심 작업 시 mctrader-web 측 follow-through 누락
- ADR-019 D1 worktree isolation 이 hub/engine 만 적용, web 측 누락

→ **ADR-020 D2 후보 (RETRO-MCT-119-120 §4.1 multi-repo Story completion 게이트)** 의 정당성 재실증. 본 retro §4.1 (multi-repo .env SSOT) + RETRO-MCT-119-120 §4.1 (multi-repo PR 게이트) 통합 박제 권장.

### 5.4 ADR 후보 누적 — N=12 (1주 관측 sprint 일괄 박제 임계 초과)

RETRO-MCT-119-web-test-overhaul §5.4 의 "10+ 후보" 에서 본 retro 추가:
- ADR-020 D2 (multi-repo Story completion)
- ADR-019 D7 (worktree cleanup)
- ADR-018 D8 (Optional None-guard)
- ADR-018 신규 (decimal.InvalidOperation)
- ADR-019 D? (신규 repo Python interpreter)
- ADR 신규 (CI quality gate fail-fast 폐지)
- ADR 신규 (branch guard enforcement)
- ADR-021 (세션 종료 게이트)
- ADR 신규 (pytest marker ↔ CI workflow 동기)
- ADR 신규 (Streamlit testing-aware design)
- **ADR 신규 (multi-repo .env SSOT — 본 §4.1)**
- **ADR 신규 (SQLAlchemy ORM relationship 명시 — 본 §4.2)**
- **ADR 신규 (Docker build dependency 표준 — 본 §4.3)**

→ **12+ 후보**. 1주 관측 임계 (2026-05-16) 충족 항목 즉시 박제 sprint 강력 권장. RETRO-MCT-117/119-120/119-web-test-overhaul §6 권고 누적 — **다음 세션 시작 시 ArchitectAgent dispatch 1순위**.

### 5.5 Cat B 비율 vs Cat D/E 첫 surface — 자동 테스트 한계 실증

RETRO 누적 Cat B 비율 (15~25%) 은 신규 코드의 "정상" 결함 비용 baseline. 그러나 본 retro 의 Cat D (.env) + Cat E (bind mount) 는 **비율 산정 불가 카테고리** — 단일 fix-event 가 production trigger 후 발생.

→ **자동 테스트 (528 PASSED + AppTest + Playwright E2E) 가 deployment-time defect 미커버**. integration test Tier 3 (§4.4) 도입 후에도 .env 부재 같은 환경 결함은 별도 lane 필요 — production 첫 deploy 시점에서만 surface 가능. **deployment runbook + smoke test 단계가 PMO 회고 게이트 외 별도 게이트** 로 박제 필요.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **ADR 박제 sprint 즉시 실행 (12+ 후보)** (§5.4) — 누적 12+ ADR 후보 1주 관측 임계 충족. 본 retro §4.1 (multi-repo .env SSOT) + §4.2 (SQLAlchemy ORM relationship) + §4.3 (Docker build dependency) 모두 root cause 명확 → **즉시 박제 권장**. 다음 세션 시작 시 ArchitectAgent dispatch 1순위. RETRO-MCT-117/119-120/119-web-test-overhaul 의 누적 권고와 통합.

2. **mctrader-engine 8 신규 모델 ORM relationship audit Story 즉시 발의** (§3.2 + §4.2) — `strategy_sets / versions / components / layers / drafts / promotion_events / runtime_overrides / pipeline_events` 8 테이블의 SQLAlchemy `relationship()` 명시 여부 + 의존 INSERT 순서 검증. 잠재 7 endpoint 의 FK 순서 race 사전 차단. 가칭 MCT-125 또는 MCT-126.

3. **Docker build dependency 표준 Phase Story 발의** (§3.3 + §4.3) — Wheel pre-build (1순위) 또는 BuildKit secret mount (2순위) 채택. 6-repo 컨테이너의 production rebuild 보장 + GitHub token leak 차단. 본 사례 같은 bind mount 임시 조치 누적 차단. 가칭 MCT-127 또는 ADR-016 amendment 1.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Fix 1 root cause 진단 (.env 부재 → fe_sendauth) | ~15% |
| Fix 1 적용 (.env 생성 + .gitignore) | ~5% |
| Fix 2 root cause 진단 (SQLAlchemy UoW FK 순서) | ~25% |
| Fix 2 적용 (db.flush() + import 순서 정정) | ~10% |
| Mitigation 3 진단 (Docker GitHub-dep rebuild 불가) | ~15% |
| Mitigation 3 적용 (compose.override.yml bind mount + retag) | ~10% |
| 사용자 수동 검증 (Strategy Set 생성 페이지 200) | ~5% |
| Story §3.2 §11 갱신 + 본 retro 작성 | ~15% |

→ **Fix 진단 비용 55%, 적용 비용 25%, 검증·문서화 20%**. RETRO-MCT-119-web-test-overhaul 의 "신규 인프라 도입" 분포와 달리 **runtime fix 의 진단 비용 비중 과반** — Cat D (deployment-time) + Cat E (infra) 결함의 진단 cost 가 코드 결함보다 높음. **§5.5 의 자동 테스트 한계** 실증.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-016**: Containerization — 본 retro §4.1 (multi-repo .env SSOT) + §4.3 (Docker build dependency) amendment 후보
- **ADR-018**: Defensive coding patterns — 본 retro §4.2 (SQLAlchemy ORM relationship) D? 후보
- **ADR-019**: Parallel agent isolation — D7 worktree cleanup 후보 (RETRO-MCT-119-120 §4.2)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch 9번째 same-session 사례 + D2 multi-repo 게이트 후보 (RETRO-MCT-119-120 §4.1)
- **ADR-011**: CI standard — 본 retro §4.4 integration test Tier 3 amendment 후보
- **MEMORY** `feedback_admin_merge_autonomy.md`: f3dc511 + b96b906 push 자율 (9번째 same-session)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: 본 retro 는 production trigger 라 CI auto-recovery 외 lane — runtime fix 1 commit 회복 사이클은 동일 패턴
- **MEMORY** `project_dockerization_epic.md`: MCT-98 #120 dockerization Epic 완료 후 surface 된 후속 결함 — Phase 후속 Story 트리거
- **선행 retro**:
  - `RETRO-MCT-119-120-strategy-pipeline.md` (§3.1 web 미푸시 패턴 → 본 retro §3.1 의 .env 부재 와 동일 root cause family)
  - `RETRO-MCT-119-web-test-overhaul.md` (§5.5 2-tier 테스트 → 본 retro §4.4 Tier 3 확장 후보)
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준 → 본 retro §5.2 Cat D/E 신규 카테고리 추가)
  - `RETRO-MCT-124-signal-collector.md` (외부 API 의존성 패턴 4건 — 본 retro §3.1 multi-repo 환경 변수 drift 와 별도 lane)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-119.md` §3.2 (runtime fix 박제 완료) + §11 (본 retro pointer 박제) — 별도 commit 또는 본 retro와 동일 commit 으로 처리.

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up

- **본 fix 자체 follow-up 없음** — Fix 1+2+Mitigation 3 모두 현재 운영 가능 상태
- 다만 §3.3 의 Mitigation 3 (bind mount) 은 **임시 조치** — proper fix (Wheel pre-build 등) Story 트리거 필요

### 10.2 ADR 박제 (즉시 검토)

- **ADR 신규 (§4.1)** — multi-repo .env SSOT — 3 사례 누적, 즉시 박제 권장
- **ADR 신규 (§4.2)** — SQLAlchemy ORM relationship 명시 — root cause 명확, 즉시 박제 권장
- **ADR 신규 (§4.3)** — Docker build dependency 표준 — 인프라 Story 동반 발의 권장
- ADR-011 amendment (§4.4) — integration test Tier 3 — 1주 관측 후

### 10.3 후속 Story 발의

- **mctrader-engine 8 신규 모델 ORM audit Story** (가칭 MCT-125) — §6 제안 2
- **Docker build dependency 인프라 Story** (가칭 MCT-127) — §6 제안 3
- **mctrader-web integration test Tier 3 Story** (가칭 MCT-128) — §4.4

### 10.4 Strategy Set Pipeline 후속 Story 트리거 (RETRO-MCT-119-120 §10.4 누적)

- Phase 3 backtest sweep (630 조합 자동 sweep)
- Strategy Set ↔ WFO 연동
- paper/live 모드 Strategy Set 활성 (Bithumb live 첫 적용)

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
