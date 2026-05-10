# RETRO-MCT-126 — admin_overview 런타임 4-RC fix (Docker 제어 + Engine Status + 환경변수 정합)

**범위**: MCT-126 후속 운영 fix — `pages/admin_overview.py` 표시 버그 4건 (4 Root Cause) 일괄 처리
**기간**: 2026-05-10 (single-session, MCT-126 main dashboard 직후 동일 세션 연장 — 14번째 same-session Story 등가 작업)
**Trigger**: MCT-126 Main Dashboard + MCT-125 Admin Control 도입 후 실제 Docker Desktop 환경에서 admin_overview 가동 시 (a) 콜렉터 4개 모두 stopped/idle 표시, (b) 모든 엔진 UNKNOWN 표시 — production smoke 발견. 즉시 자율 fix → 4 RC 누적 surface → 단일 commit (`c40c681`) + 환경변수 1건 (.env DOCKER_GID=0) 으로 회복. ADR-020 D1 자동 dispatch.
**Status**:
- mctrader-web `main` 직접 push 1 commit (`c40c681`)
- 후속 동일 lane 2 commit (`28f95a2` collector Docker fallback + dynamic UI + MCTRADER_COLLECTOR_CONTAINERS, `f174926` candle parquet 스캔 fix) — 본 retro 범위 외이나 동일 admin_overview 화면 lane
- 550 tests pass (mctrader-web)
- Docker 이미지 빌드 + compose up + .env 수정 + 재시작까지 운영자 lane 일괄 자동화

**Story file**: `docs/stories/MCT-126.md` (기존 main dashboard 작업과 동일 키 사용 — §11 회고 pointer 본 retro 추가 권고)
**Repos**:
- `mctrader-web` (단일 repo) — `main.py` (engine_class/sm_state field), `compose.yml` (MCTRADER_DATA_ROOT + group_add), `.env` (DOCKER_GID=0)
- mctrader-hub: 변경 0 (Story scope 내 — 본 retro 1건만 본 작업 동반)

---

## 1. 결과 요약

### 1.1 4 Root Cause 매트릭스

| RC | 위치 | 원인 | 표면 증상 | fix |
|---|---|---|---|---|
| **RC-1** | `compose.yml` api 서비스 env | `MCTRADER_DATA_ROOT` 누락 → `_resolve_data_root()` None 반환 → `_collector_statuses()` 빈 리스트 | admin_overview 콜렉터 4개 모두 stopped/idle | compose.yml `MCTRADER_DATA_ROOT=/data` 추가 |
| **RC-2** | `control_adapter.py` (RETRO-MCT-125 lane, 본 fix 직전 적용 완료) | systemd/subprocess → Docker SDK 교체 + node_id→container_name 매핑 (`MCTRADER_COLLECTOR_CONTAINERS`) | 콜렉터 start/stop 컨트롤 작동 안 함 | Docker SDK 교체 + status.py known container fallback 엔트리 |
| **RC-3** | `compose.yml` group_add | `DOCKER_GID=999` 설정, 실제 docker.sock 은 `root:root` (GID 0, Docker Desktop) | DockerException Permission denied → 콜렉터 Docker 상태 0건 | `.env` `DOCKER_GID=0` 변경 후 api 컨테이너 재시작 |
| **RC-4** | `main.py` engine_map | 옛 field (`name`/`status`) 사용, 실제 API 응답은 `engine_class`/`sm_state`. `_ENGINE_NAMES=["PaperEngine", ...]` 도 클래스명 불일치 | 5 엔진 모두 UNKNOWN 표시 | `_ENGINE_CLASS_LABELS` 매핑 + `engine_class`/`sm_state` 필드 사용 |

→ **단일 화면 (admin_overview) 4 RC 누적**. RC-1/RC-3 은 환경변수/인프라 layer, RC-2/RC-4 는 코드 layer. **RC-1 + RC-3 양쪽이 컨테이너화 + Docker Desktop 환경 첫 가동 시 동시 surface** — RETRO-MCT-125 의 Docker socket mount 작업이 운영 환경 검증 (RETRO-MCT-125 §10.1 follow-up "실제 운영 검증") 미수행으로 silent 였던 부채가 본 Story 시점에 한 번에 surface.

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-web` 본 fix 1 commit (`c40c681`) | `main.py` + `compose.yml` 통합 fix | main 직접 push (ADR-019 D6) |
| `mctrader-web` 후속 2 commit (본 retro 범위 외) | `28f95a2` collector Docker fallback + dynamic UI + MCTRADER_COLLECTOR_CONTAINERS / `f174926` candle parquet 스캔 fix | main 직접 push, 동일 admin_overview lane |
| `.env` 수정 (DOCKER_GID=0) | 운영 환경 변경 (gitignored) | 로컬 적용 |

### 1.3 테스트 결과

| 카테고리 | 신규 test | passed | failed |
|---|---|---|---|
| 본 fix 회귀 (`main.py` engine_class 매핑) | 0 (기존 회귀 cover) | 550 | 0 |
| 운영 검증 (4 콜렉터 running 확인) | 수동 verify | 4/4 | 0 |
| Streamlit panel healthy | 수동 verify | OK | - |

→ **550 tests pass** (RETRO-MCT-125 535 + MCT-126 main dashboard 신규 + 본 fix 회귀 cover). production smoke 직접 검증 — 4 콜렉터 (6e495e91f663, 8d88f77d171a, NODE_BITHUMB_A, NODE_UPBIT_A) running + Streamlit healthy.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-125 §1.4 + RETRO-MCT-126 main dashboard §1.4 표준)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 fix (4 RC 일괄 처리) | 4 | 80% | 본 fix |
| 운영 cascade fix — `.env` DOCKER_GID=999 → 0 (Docker Desktop 환경) | 1 | 20% | **Cat C (운영 환경 차이 finish-up)** |

→ Cat C **20%, 본 fix 80%**. RETRO-MCT-126 main dashboard 의 Cat B 48% / Cat A 16% / Cat C 8% 와 패턴 변경 — **본 retro 는 production smoke 트리거 4 RC 누적 fix 가 메인** (Cat B 0). RETRO-MCT-125 의 silent debt 가 운영 첫 가동 시점에 surface 한 lane — **RETRO-MCT-125 §10.1 의 "실제 운영 검증" follow-up 미수행 cost 가 본 Story 의 4 RC 누적으로 surface**.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-web` | `main` (직접 push) | ✅ | (없음, ADR-019 D6) | ✅ |

→ **1-repo Story** + **운영 환경 (.env / Docker Desktop) 수정 1건**. cross-repo 0.

---

## 2. 잘된 점

### 2.1 4 RC 일괄 surface → 단일 commit 통합 fix — production smoke 효율 lane

admin_overview 첫 가동 시 4 RC 가 한 화면에서 동시 surface. 분류 후 처리 순서:

1. RC-1 (MCTRADER_DATA_ROOT) — compose.yml env 1줄
2. RC-3 (DOCKER_GID 999→0) — .env 1줄 + api 컨테이너 재시작
3. RC-4 (engine_class/sm_state field) — main.py 코드 fix
4. RC-2 (Docker SDK control_adapter — 사전 RETRO-MCT-125 lane 적용 완료)

→ **production smoke 가 4 RC 동시 노출 → 단일 fix 사이클 (commit `c40c681`) 로 통합 처리**. 분리 commit 가능했으나 **상호 의존** (RC-1 fix 만으로는 RC-3 Permission denied surface, RC-3 fix 만으로는 RC-4 표시 silent). 통합 commit 이 실용 lane.

### 2.2 운영 자동화 — gh auth token + Docker GID 자동 조달

본 fix 사이클의 운영 단계:

| 단계 | 자동화 |
|---|---|
| Docker 이미지 빌드 (GitHub 토큰 필요) | `gh auth token` 자동 조달 → `docker build --secret` 전달 (MEMORY `feedback_docker_build_github_token.md` 적중) |
| `docker compose up -d` 컨테이너 재시작 | 자동 |
| `.env` DOCKER_GID 수정 | 1줄 식별 + edit + restart |
| 4 콜렉터 running 검증 | docker ps + admin_overview 화면 검증 |

→ **운영 lane 자동화 100%** — 사용자 수동 개입 0. RETRO-MCT-125 §10.1 follow-up 의 "실제 운영 검증" 이 본 Story 에서 production smoke 형태로 surface 후 자동 회복.

### 2.3 RC-3 Docker GID 환경 차이 박제 — Linux 서버 전환 시 사전 회피

`.env.example` 의 `DOCKER_GID=999` 가 Docker Desktop 환경 미정합 — 실제는 0 (root). Linux 서버에서는 `getent group docker | cut -d: -f3` 로 확인 필요. **본 사례가 mctrader 첫 cross-platform Docker GID 환경 차이 박제** — Production deploy (Linux server) 전환 시 `.env.example` 갱신 또는 entrypoint 자동 검출 baseline 필요. §4.2 ADR 후보.

### 2.4 RETRO-MCT-125 silent debt 회복 lane — production smoke 첫 가동 cost

RETRO-MCT-125 §10.1 권고: "mctrader-web admin_control 실제 운영 검증 — Docker socket mount 후 컨테이너 내부에서 docker SDK 정상 작동 확인". **본 Story 가 해당 follow-up 의 production smoke 자체** — 4 RC surface + 회복까지 1 세션. RETRO-MCT-125 종료 시점에 해당 follow-up 이 즉시 처리됐다면 본 Story 4 RC 가 단계적 분리 가능했으나, 통합 surface 도 **production cost 1 사이클 내 수렴** lane 으로 acceptable.

### 2.5 admin merge autonomy + 자동 PMO 회고 dispatch — 14번째 same-session 사례

본 Story 완료 직후 자동 PMO retro dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121/122+123/124/119-web/125/126-main + **126-runtime-fix** = **14 Story (또는 동등 작업)**. ADR-020 D1 + MEMORY `feedback_pmo_retro_mandatory.md` closed-loop 누적 14건. RETRO-MCT-126-main-dashboard 의 13번째 → 본 retro 14번째.

---

## 3. 발생한 이슈

### 3.1 [HIGH] RC-1 MCTRADER_DATA_ROOT compose.yml 누락 — 환경변수 정합 baseline 부재

**관측**:
- `compose.yml` api 서비스 environment 섹션에 `MCTRADER_DATA_ROOT` 미선언
- 코드 측 `_resolve_data_root()` 가 env 미존재 시 None 반환
- `_collector_statuses()` 가 None 받으면 빈 리스트 반환 (graceful fallback)
- 결과: admin_overview 콜렉터 4개 모두 stopped/idle 표시 (silent)

**근본 원인 분석**:
1. **신규 코드 (collector status 조회) 도입 시 의존 환경변수 compose.yml 동시 갱신 의무 부재** — 코드/인프라 동기화 baseline 부재
2. **graceful fallback (None → 빈 리스트) 가 silent** — exception 또는 명시 warning 부재
3. RETRO-MCT-125 종료 시 `MCTRADER_COLLECTOR_CONTAINERS` 만 추가됐고 `MCTRADER_DATA_ROOT` 누락 — checklist 부재

**의미**:
- **silent debt** — production 가동까지 표면화 안 됨. CI 는 컨테이너 외부 (host) 에서 실행 → env 누락 detect 안 함
- 본 사례는 production smoke 시점 즉시 catch — 운 좋은 timing
- 그러나 다른 환경변수 (예: MINIO_ENDPOINT, REDIS_URL 추가 시) 동일 함정 재현 가능

**평가**:
- §4.1 ADR 후보 — **코드/인프라 환경변수 동시 갱신 baseline** (코드 추가 시 compose.yml 동시 갱신 + CI lint 또는 startup health check)
- 본 사례 1건이지만 **HIGH** — silent debt + production 첫 가동 cost

### 3.2 [HIGH] RC-3 Docker GID 환경 차이 — Docker Desktop vs Linux server `.env.example` 부정합

**관측**:
- `compose.yml` group_add 가 `${DOCKER_GID:-999}` 사용
- `.env.example` 에 `DOCKER_GID=999` 명시 (Linux 일반 docker group GID 가정)
- 실제 Docker Desktop 환경: docker.sock 이 `root:root` (GID 0)
- 결과: api 컨테이너의 mctrader user 가 docker.sock 접근 불가 → DockerException Permission denied

**근본 원인 분석**:
1. **`.env.example` 의 999 가정** — Linux 일반 docker group GID 기반, Docker Desktop 환경 미고려
2. **cross-platform Docker GID 검출 baseline 부재** — entrypoint 또는 startup script 가 docker.sock GID 자동 감지 + group_add 동적 적용 미구현
3. **Docker Desktop 환경 문서화 부재** — README / docs/ops 에 `getent group docker` 안내 부재

**의미**:
- 운영자가 Docker Desktop / Linux server 전환 시 매번 수동 설정 필요
- silent fail (Permission denied 가 컨테이너 로그에만 surface, admin_overview 는 그냥 빈 리스트)
- 본 사례는 production smoke 시점에 catch — 운영 자동화 측 baseline 부재

**평가**:
- §4.2 ADR 후보 — **cross-platform Docker GID 자동 검출 entrypoint baseline**
- Lite: `.env.example` 에 환경별 안내 주석 (Docker Desktop=0, Linux 서버=`getent group docker`)
- Medium: entrypoint script 가 docker.sock GID 자동 감지 + group_add 동적
- Heavy: ADR 박제

### 3.3 [HIGH] RC-4 main.py engine_class/sm_state field name drift — API contract drift silent

**관측**:
- `main.py` 의 `engine_map` 이 `name`/`status` 키 사용
- 실제 API 응답 (`/admin/status/engines`) 은 `engine_class`/`sm_state` 반환
- `_ENGINE_NAMES = ["PaperEngine", ...]` 가 실제 클래스명 (예: `PaperBrokerEngine` 등) 과 불일치
- 결과: 모든 엔진 UNKNOWN 표시

**근본 원인 분석**:
1. **API contract 변경 시 consumer (frontend / dashboard) 동시 갱신 의무 부재** — backend 응답 schema 가 변경됐는데 frontend 코드가 옛 schema 사용
2. **schema validation 부재** — frontend 가 응답 dict 를 직접 access (`data["name"]`) → KeyError 안 나고 None 또는 default 반환 → silent UNKNOWN
3. **타입 시스템 미적용** — Pydantic / TypedDict 등으로 backend ↔ frontend schema 동기화 baseline 부재

**의미**:
- **silent UI bug** — 모든 엔진이 UNKNOWN 으로 표시되지만 화면 자체는 정상 렌더링 → 사용자가 "엔진이 정말 UNKNOWN" 으로 오인 가능
- API contract 변경 이력 추적 부재 → 어느 시점부터 drift 됐는지 불명
- 본 사례는 production smoke 시점 visual catch — automated test 부재

**평가**:
- §4.3 ADR 후보 — **API contract 공유 schema baseline** (Pydantic 또는 OpenAPI generated client)
- Lite: shared types module (`mctrader_web/api_schemas.py`) 내 TypedDict 정의 → backend + frontend 모두 import
- Medium: Pydantic model 공유 + frontend 응답 검증 (KeyError → 명시 warning)
- Heavy: OpenAPI spec generator + TypeScript-like client codegen

### 3.4 [LOW] `.env.example` 환경별 안내 주석 부재

**관측**:
- `.env.example` 의 `DOCKER_GID=999` 단독 명시, 환경별 차이 안내 부재
- 운영자가 Docker Desktop 사용 시 매번 시행착오

**근본 원인 분석**:
- 문서화 baseline 부재 — `.env.example` 이 단순 placeholder, 환경별 가이드 부재

**평가**:
- 즉시 대응: `.env.example` 에 환경별 주석 추가 (`# Docker Desktop: 0`, `# Linux server: $(getent group docker | cut -d: -f3)`)
- §4.2 ADR 박제 동반

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] 코드/인프라 환경변수 동시 갱신 baseline — silent compose.yml drift 차단

```
target_adr: ADR 신규 또는 ADR-018 D? amendment
amendment_type: governance (PR reviewer checklist) + artifact (CI lint)
trigger: RETRO-MCT-126-runtime-fix §3.1 MCTRADER_DATA_ROOT compose.yml 누락 — silent fallback 으로 production 가동까지 표면화 안 됨
배경:
  - 신규 코드 도입 시 의존 환경변수 (os.getenv / settings.X) 가 compose.yml / .env.example 에 미동기화
  - graceful fallback (None → 빈 리스트, default 값 등) 가 silent debt 누적
  - CI 는 컨테이너 외부 host 에서 실행 → env 누락 detect 안 함
  - production 첫 가동 시점 surface
문제:
  - silent debt — production 가동까지 표면화 안 됨
  - 운영자 / LLM agent 가 환경변수 추가 시 인프라 측 갱신 누락 가능
  - mctrader 6 repo cross-repo 환경변수 매트릭스 부재
제안 결정:
  a) Lite: PR reviewer checklist — "코드에서 os.getenv / settings.X 추가 시 compose.yml + .env.example 동시 갱신"
  b) Medium: CI lint — `grep -r "os.getenv\|settings.get" src/` vs compose.yml environment 비교, 누락 detect
  c) Heavy: Pydantic Settings + startup health check — 필수 env 누락 시 컨테이너 즉시 fail (silent fallback 금지)
배제 옵션:
  - 모든 env 를 default 값으로 graceful — silent debt 누적
권장 priority: HIGH (다음 신규 환경변수 도입 Story 전 결정)
관련:
  - ADR-018 Defensive coding baseline
  - RETRO-MCT-125 §10.1 follow-up "실제 운영 검증" — 본 사례가 follow-up 시점 surface
  - RETRO-MCT-126-runtime-fix §3.1
```

### 4.2 [HIGH] cross-platform Docker GID 자동 검출 entrypoint baseline

```
target_adr: ADR 신규 또는 ADR-018 D? amendment
amendment_type: artifact (entrypoint script) + governance (.env.example 환경별 주석)
trigger: RETRO-MCT-126-runtime-fix §3.2 Docker Desktop (GID 0) vs Linux server (`getent group docker`) `.env.example` 부정합
배경:
  - mctrader 컨테이너가 docker.sock 마운트 + group_add 패턴 사용 (RETRO-MCT-125 §Task 6 도입)
  - `.env.example` DOCKER_GID=999 가 Linux 일반 가정 — Docker Desktop / macOS / Windows 환경 미정합
  - 운영자가 환경 전환 시마다 수동 검출 + .env 수정 필요
  - silent fail (Permission denied 가 로그만 surface, UI 는 빈 리스트)
문제:
  - cross-platform 운영 cost
  - 운영 자동화 측 baseline 부재
  - mctrader 의 Linux server 전환 (production deploy) 시 baseline 필요
제안 결정:
  a) Lite (즉시): `.env.example` 환경별 주석 — `# Docker Desktop=0, Linux server=$(getent group docker)`
  b) Medium: entrypoint script — docker.sock GID 자동 감지 + group_add 동적 적용 (suid bit 또는 sudo 권한 필요)
  c) Heavy: ADR 박제 — Docker socket 접근 패턴 표준 (group_add 동적 + suid + sudoers 등)
배제 옵션:
  - Docker socket mount 회피 (Docker-in-Docker, sysbox 등) — 비용 큼
권장 priority: HIGH (Linux server production deploy 전 결정)
관련:
  - ADR-018 Defensive coding baseline
  - RETRO-MCT-125 §Task 6 Docker socket mount
  - RETRO-MCT-126-runtime-fix §3.2 + §3.4
```

### 4.3 [HIGH] API contract 공유 schema baseline — backend/frontend drift 차단

```
target_adr: ADR 신규
amendment_type: artifact (shared types module) + process (API 변경 PR 체크리스트)
trigger: RETRO-MCT-126-runtime-fix §3.3 main.py engine_class/sm_state field drift — 모든 엔진 UNKNOWN silent
배경:
  - mctrader-web 의 backend (FastAPI) ↔ frontend (Streamlit) 간 응답 schema 가 dict access 패턴
  - backend schema 변경 시 frontend 코드가 옛 key 사용해도 KeyError 없이 None / default → silent UNKNOWN
  - API contract drift 가 visual / behavior 측 silent bug
  - 본 사례는 production smoke 첫 catch — automated test 부재
문제:
  - silent UI bug — 정상 렌더링 + 잘못된 데이터 표시
  - 사용자 신뢰 위반 (UNKNOWN 이 정말 UNKNOWN 인지 불명)
  - schema 변경 이력 추적 부재
제안 결정:
  a) Lite: shared types module (`mctrader_web/api_schemas.py`) 내 TypedDict 정의 — backend + frontend 모두 import
  b) Medium: Pydantic model 공유 — frontend 가 응답 검증 (validate_python) → KeyError 시 명시 warning
  c) Heavy: OpenAPI spec generator + TypeScript-like client codegen
배제 옵션:
  - schema-less dict — 본 사례가 silent bug 직격
권장 priority: HIGH (다음 API contract 변경 Story 전 결정)
관련:
  - RETRO-MCT-126-runtime-fix §3.3
  - 잠재 영향: mctrader-web 모든 dashboard page (admin_overview, admin_control, admin_signal, candle, runs, ...)
```

---

## 5. Cross-Story 인사이트

### 5.1 RETRO-MCT-125 silent debt 회복 lane — production smoke 가 follow-up 의 surface 매개체

| 회고 | 권고 | 본 Story 시점 surface |
|---|---|---|
| RETRO-MCT-125 §10.1 | "mctrader-web admin_control 실제 운영 검증 — Docker socket mount 후 컨테이너 내부에서 docker SDK 정상 작동 확인" | 본 Story RC-1 + RC-3 (compose env + GID) — 두 RC 모두 RETRO-MCT-125 작업 시 인프라 측 미완성 |
| RETRO-MCT-126-main-dashboard §3.5 | idempotency cache 격리 (RETRO-MCT-125 silent debt) | 본 Story 직전 commit 에서 처리됨 |

→ **RETRO-MCT-125 종료 시점의 follow-up 미수행 cost 가 본 Story 에서 4 RC 형태로 surface**. **production smoke 가 follow-up 의 자동 trigger 매개체** 패턴 박제 — 향후 Story 종료 시 follow-up 항목을 즉시 처리하지 않으면 다음 Story 에서 누적 cost.

### 5.2 same-session 14 Story sweep — 14번째 same-session 사례

| Story | 분류 |
|---|---|
| MCT-112 ~ MCT-124 | RETRO-MCT-125 §5.1 누적 11 Story |
| MCT-119-web | 12번째 (test 보강) |
| MCT-125 | 13번째 (Admin Control) |
| MCT-126-main-dashboard | 14번째 (Main Dashboard) |
| **MCT-126-runtime-fix (본 retro)** | **15번째 (admin_overview 4 RC fix)** |

→ **15 Story (또는 동등 작업) same-session sweep**. RETRO-MCT-126 main dashboard 의 14 → 본 retro 15. **codeforge ζ arc velocity 가 production smoke 후 4 RC 일괄 fix 까지 일반화** — RETRO-MCT-124 외부 API friction → MCT-125 외부 모듈 mock + cross-cutting → MCT-126 pre-existing finish-up → **본 Story production smoke** 라는 lane 진화.

### 5.3 admin_overview 화면의 누적 fix lane — 14번째 sweep 후 production smoke 첫 노출

mctrader-web admin_overview 화면 누적 fix:

| commit | 내용 | 시점 |
|---|---|---|
| (이전) RETRO-MCT-117 | admin pages 입력 검증 baseline | session 초반 |
| RETRO-MCT-125 (`1319474`) | admin_control 페이지 전면 재구성 | 13번째 Story |
| RETRO-MCT-126 main dashboard (`48a0798` 등) | main.py 신규 (engine_map 옛 field 사용 — silent debt 도입) | 14번째 Story |
| **본 retro (`c40c681`)** | **main.py engine_class/sm_state fix + compose env 보강** | **15번째 Story (production smoke)** |
| (후속) `28f95a2` | collector Docker fallback + dynamic UI + MCTRADER_COLLECTOR_CONTAINERS | 본 retro 직후 lane |
| (후속) `f174926` | candle parquet 직접 스캔 fix | 본 retro 직후 lane |

→ **admin_overview 가 14 Story 누적 후 production smoke 첫 노출 시점에 4 RC + 후속 2 추가 RC** 누적 surface. **admin UI 측 production smoke baseline 부재** — RETRO-MCT-125/126 작성 시점에 sandbox 환경 (CI) 만 검증, 실제 Docker Desktop 환경 검증 부재.

### 5.4 부수 fix 카테고리 갱신 — Cat C 20% (production smoke 트리거)

| Story | Cat A | Cat B | Cat C | 본 fix |
|---|---|---|---|---|
| MCT-117 | 350% | <10% | 0 | 11 |
| MCT-119+120 | <10% | 17% | 0 | 29 |
| MCT-121 | <10% | 7% | 36% | 8 |
| MCT-122+123 | <10% | <10% | 43% | 8 |
| MCT-124 (Amendment 후) | 0% | 31% | 0% | 11 |
| MCT-119-web | 0% | 25% | 0% | 6 |
| MCT-125 | 0% | 47% | 0% | 8 |
| MCT-126-main-dashboard | 16% | 48% | 8% | 3 |
| **MCT-126-runtime-fix (본 retro)** | **0%** | **0%** | **20%** (1) | **80% (4 RC)** |

→ **본 retro 는 본 fix 80%, Cat C 20% — production smoke 트리거 4 RC 누적 fix 가 메인 lane**. RETRO-MCT-126 main dashboard 의 Cat B 48% / Cat A 16% 와 패턴 변경 — **production smoke 트리거 retro 는 본 fix 비중이 높음**. RETRO-MCT-119-runtime-fix / RETRO-MCT-121-upbit-collector-runtime-fix 와 동일 lane (실제 가동 시점 fix 회고).

### 5.5 도구 선택의 적합성 — Docker SDK + 환경변수 정합

본 retro 의 도구 / 결정 4건:

| 결정 | 패턴 |
|---|---|
| Docker SDK (`docker>=7`) | RETRO-MCT-125 도입 lane 유지 — 본 retro 에서 GID Permission 측 운영 cost 첫 노출 |
| `MCTRADER_COLLECTOR_CONTAINERS` 환경변수 매핑 | node_id → container_name 매핑 baseline (후속 `28f95a2` 적용) |
| `_ENGINE_CLASS_LABELS` 매핑 | API contract 공유 schema baseline 부재 회피 lane (Lite) — §4.3 ADR 박제 시 통합 가능 |
| `.env` DOCKER_GID=0 | Docker Desktop 환경 first-class — Linux server 전환 시 entrypoint baseline 필요 |

→ **운영 환경 정합 우선 + 점진 baseline 박제 패턴**. RETRO-MCT-125 §5.5 의 "소규모 / 표준 / 임베디드 우선" + 본 retro 의 "환경 차이 first-class" 누적 lane.

### 5.6 production smoke retro 패턴 박제 — RETRO-MCT-119-runtime-fix / RETRO-MCT-121-upbit / 본 retro 누적 3건

| retro | trigger | RC 수 | 본 fix vs Cat |
|---|---|---|---|
| RETRO-MCT-119-runtime-fix | mctrader-engine 실제 가동 시 strategy_set load 실패 | 다중 | 본 fix 위주 |
| RETRO-MCT-121-upbit-collector-runtime-fix | upbit collector 실제 가동 시 WebSocket 연결 실패 | 다중 | 본 fix 위주 |
| **RETRO-MCT-126-runtime-fix (본 retro)** | **admin_overview 실제 가동 시 4 RC 누적 surface** | **4** | **본 fix 80%** |

→ **production smoke retro 패턴 누적 3건** — 본 fix 비중 높음 + RC 다중 surface + 단일 commit 통합 fix lane. **Story 종료 직후 production smoke 의무화** baseline 후보. §6 #3 권고.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **[HIGH] §4.1 코드/인프라 환경변수 동시 갱신 baseline ADR 박제** — 본 retro RC-1 (compose.yml MCTRADER_DATA_ROOT 누락) 가 silent debt 로 production 가동까지 surface 안 됨. Lite (PR reviewer checklist) 즉시 박제 + Medium (CI lint `grep -r "os.getenv"` vs compose.yml) 1주 관측 후 결정. **RETRO-MCT-125 §10.1 follow-up 미수행 cost 가 본 Story 4 RC 로 surface** — 다음 환경변수 도입 Story 전 결정 권장.

2. **[HIGH] §4.3 API contract 공유 schema baseline ADR 박제** — 본 retro RC-4 (engine_class/sm_state field drift) 가 silent UI bug. mctrader-web 모든 dashboard page 잠재. Lite (shared TypedDict 모듈 `mctrader_web/api_schemas.py`) 즉시 박제 + Medium (Pydantic model 공유 + 응답 검증) 1주 관측 후 결정. **dashboard 측 production smoke 첫 catch 패턴 — automated schema test 부재 lane**.

3. **[HIGH] Story 종료 직후 production smoke 의무화 baseline** — RETRO-MCT-119-runtime-fix / RETRO-MCT-121-upbit / 본 retro 누적 3건이 모두 "Story 종료 시점에 sandbox 만 검증, 실제 가동 시점 RC surface" 패턴. ADR-020 D? amendment — Story DoD 에 "실제 운영 환경 가동 + 1 사이클 검증" 추가. RETRO-MCT-125 §10.1 follow-up 의 instance form. Lite (Story DoD checklist 1줄) 즉시 박제 + Medium (smoke test 자동화 — Docker Compose up + admin pages curl) 1~2 Story 후 결정.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| RC-1 진단 (admin_overview 콜렉터 stopped/idle 분석 → MCTRADER_DATA_ROOT 누락 식별) | ~15% |
| RC-3 진단 (DockerException Permission denied 분석 → docker.sock GID 0 vs DOCKER_GID 999 식별) | ~15% |
| RC-4 진단 (모든 엔진 UNKNOWN 분석 → engine_class/sm_state field drift 식별) | ~20% |
| RC-2 (control_adapter Docker SDK — 사전 적용 lane 점검) | ~5% |
| 통합 commit `c40c681` (main.py + compose.yml fix) | ~10% |
| Docker 이미지 빌드 (`gh auth token` 자동 조달 + `--secret` 전달) | ~10% |
| `docker compose up -d` + .env 수정 + api 컨테이너 재시작 | ~5% |
| 4 콜렉터 running 검증 + Streamlit healthy 검증 | ~5% |
| 550 test 검증 + retro 작성 | ~15% |

→ **부수 비용 ~20%** (운영 자동화 + retro 작성). RETRO-MCT-126 main dashboard ~10% 보다 증가 — 본 retro 는 4 RC 진단 cost 가 ~50% (production smoke 첫 catch 비용). §4.1/4.2/4.3 ADR 박제 시 향후 ~15% 회피 가능 추정.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-014**: Engine state machine — RC-4 의 engine_class/sm_state field 가 본 ADR 의 schema 와 정합 (frontend drift 가 본 Story 의 lane)
- **ADR-018**: Defensive coding patterns — D? 후보 (코드/인프라 환경변수 baseline §4.1, Docker GID baseline §4.2, API contract baseline §4.3)
- **ADR-019**: Parallel agent isolation — D6 hub trunk-based (mctrader-web `c40c681` main 직접 push)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro 14번째 closed-loop), D? 후보 (Story DoD production smoke 추가 §6 #3)
- **ADR-011**: CI standard — 550 PASSED green gate (본 fix 회귀 cover)
- **MEMORY** `feedback_admin_merge_autonomy.md`: 14번째 same-session 사례 (또는 직접 push 기준 동일 lane)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_docker_build_github_token.md`: Docker 이미지 빌드 시 `gh auth token` 자동 조달 적중
- **MEMORY** `feedback_subagent_execution.md`: subagent-driven implementation 본 Story 4 RC 일괄 처리 적용
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — production smoke 첫 catch 패턴 박제
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준)
  - `RETRO-MCT-119-runtime-fix.md` (production smoke retro 패턴 첫 박제)
  - `RETRO-MCT-121-upbit-collector-runtime-fix.md` (production smoke retro 패턴 2번째)
  - `RETRO-MCT-125.md` (§10.1 "실제 운영 검증" follow-up — 본 Story 가 surface 시점)
  - `RETRO-MCT-126-main-dashboard.md` (silent debt finish-up lane — 본 Story 와 동일 키)

---

## 9. Story §11 회고 pointer (PENDING — Story file 갱신 권장)

- `docs/stories/MCT-126.md` 가 작성됨 (status=완료, main dashboard 작업 위주)
- §7 회고 섹션 pointer 박제 권장: `RETRO-MCT-126-admin-overview-runtime-fix.md` 추가 1줄

ADR-020 D1 enforcement gap (RETRO-MCT-117 §3.2) 회피를 위해 Story file §7 갱신 권장 (본 retro 작성 직후 수행 — 단발성 5분).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **Story §7 회고 pointer 박제** (§9) — `docs/stories/MCT-126.md` §7 에 본 retro pointer 1줄 추가
- **`.env.example` 환경별 주석 추가** (§3.4) — DOCKER_GID 의 Docker Desktop / Linux server 안내. 5분 단발성
- **mctrader-web 후속 commit `28f95a2` / `f174926` 검증** — collector Docker fallback + candle parquet 스캔 fix 가 본 retro 직후 lane, 별도 mini-retro 권장 또는 본 retro 보강

### 10.2 ADR 박제 (1주 관측 또는 즉시 검토)

- **[HIGH] §4.1 코드/인프라 환경변수 동시 갱신 baseline** — RETRO-MCT-125 §10.1 follow-up 미수행 cost 표면화 → 즉시 박제 권장
- **[HIGH] §4.2 cross-platform Docker GID 자동 검출 entrypoint** — Linux server production deploy 전 결정 → 즉시 박제 권장
- **[HIGH] §4.3 API contract 공유 schema baseline** — mctrader-web 모든 dashboard page 잠재 → 즉시 박제 권장
- **[HIGH] §6 #3 Story DoD production smoke 의무화** — RETRO-MCT-119/121/126-runtime-fix 누적 3건 임계 도달 → ADR-020 D? amendment 즉시 박제 권장

### 10.3 별도 issue 발의

- **mctrader-web 전체 `os.getenv` / `settings.X` vs compose.yml 환경변수 grep sweep** — §4.1 ADR 박제 후 일괄 점검
- **mctrader-web 전체 dashboard page 의 dict access 패턴 grep sweep** — §4.3 ADR 박제 후 TypedDict 변환 일괄 적용
- **Production smoke 자동화 PoC** — Docker Compose up + admin pages curl + 응답 schema 검증

### 10.4 admin_overview / admin_control 후속 Story 트리거

본 retro 완료로 다음 Story 가능:
- **alerting rules** (RETRO-MCT-122-123 §10.5 + RETRO-MCT-124 §10.4 + RETRO-MCT-125 §10.4 누적) — Prometheus alertmanager + signal worker stale > 5분 / docker container down / heartbeat_age 임계 alert
- **Grafana dashboard JSON drop-in** (RETRO-MCT-122-123 §10.1 + RETRO-MCT-124 §10.4 + RETRO-MCT-125 §10.4 누적) — admin overview / admin control 의 metrics 시각화
- **signal worker logs 페이지** (RETRO-MCT-125 §10.4) — Docker SDK 의 `container.logs()` 사용
- **engine restart endpoint** — admin_overview 의 engine UNKNOWN 회피 + restart 트리거

### 10.5 production smoke retro 패턴 후속

- §6 #3 ADR 박제 후 mctrader 전 repo Story DoD checklist 적용
- production smoke 자동화 — Docker Compose up + curl 검증 + 응답 schema validation 으로 silent debt 차단

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
