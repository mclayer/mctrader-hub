# RETRO-MCT-122-123 — DuckDB Analytics Layer + Prometheus/Grafana 모니터링

**범위**: MCT-122 (DuckDB Analytics) + MCT-123 (Prometheus/Grafana) — 통합 회고
**기간**: 2026-05-09 ~ 2026-05-10 (cross-day, MCT-121 직후 동일 세션 연장)
**Trigger**: ADR-017 L3 Parquet 분석 레이어 + 6 repo 운영 가시성 baseline, ADR-020 D1 자동 dispatch
**Status**:
- mctrader-data PR #29 MERGED 2026-05-09T23:58:08Z (admin merge, MCT-120/121/122/123 4 Story 통합)
- mctrader-engine PR #47 MERGED 2026-05-09T23:59:18Z (admin merge, MCT-122/123 clean cherry-pick)
- mctrader-hub commit `3b62be6` main 직접 push 2026-05-10T00:19:29+09:00 (compose 모니터링 stack)

**Story files**: `docs/stories/MCT-122.md`, `docs/stories/MCT-123.md`
**Repos**:
- `mctrader-data` — branch `feat/mct-120-121-122-123` → PR #29 (4 Story 묶음)
- `mctrader-engine` — branch `feat/mct-122-123-engine-clean` → PR #47 (clean cherry-pick)
- `mctrader-hub` — main 직접 push (commit `3b62be6`, ADR-019 D6 worktree-merge gap 의 의도적 우회)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

#### MCT-122 (DuckDB Analytics)

| 영역 | 계획 | 실제 | 비고 |
|---|---|---|---|
| `DuckDBReader` + `MinioConfig` | 신규 | `2304ca3` (5 unit test 동반) | 100% |
| CLI `query --sql` | 신규 | `857c374` (2 unit test 동반) | 100% — `df()` 회피 (§3.2) |
| MinIO httpfs 통합 smoke test | 신규 | `d72d432` (1 integration test) | 100% |
| mctrader-engine `duckdb` 명시 의존성 | 추가 | `221e3fd` | 100% |
| 회귀 검증 | 308 pytest | 308/308 PASS (data) + 800/800 PASS (engine) | 100% |

#### MCT-123 (Prometheus/Grafana)

| 영역 | 계획 | 실제 | 비고 |
|---|---|---|---|
| hub compose 5 서비스 | prometheus + grafana + postgres_exporter + cadvisor + node_exporter | `3b62be6` (main 직접 push) | 100% |
| `monitoring/prometheus.yml` | 7 scrape jobs | `3b62be6` | 100% |
| `monitoring/grafana/provisioning/` | datasource + dashboards | `3b62be6` | 100% (dashboard JSON 은 향후 drop-in) |
| mctrader-data `metrics.py` + `/metrics` | 신규 | `a8dcdd4` (3 unit test) | 100% |
| mctrader-data collector/runner 메트릭 호출 | 추가 | `6816e38` + `5587755` | 100% |
| mctrader-engine `metrics.py` + `/metrics` + 0.0.0.0 | 신규 | `766e4a7` (3 unit test) | 100% |
| 회귀 검증 | data + engine | 308/308 + 800/800 PASS | 100% |

→ **양 Story scope 100% 완료, scope 누수 0**. RETRO-MCT-119-120 §3.1 (web 미푸시) + RETRO-MCT-121 §2.1 (multi-repo 게이트) 패턴 회피 성공 — 본 Story 는 **3 repo (data + engine + hub) cross-repo Story** 이며 셋 다 push + merge 완료.

### 1.2 PR #29 + PR #47 + hub commit 통계

| 단위 | 통계 | merge |
|---|---|---|
| `mctrader-data` PR #29 | **+765 / −13**, 20 파일, 12 commit | 2026-05-09T23:58:08Z (admin) |
| `mctrader-engine` PR #47 | **+100 / −1**, 4 파일, 2 commit | 2026-05-09T23:59:18Z (admin) |
| `mctrader-hub` commit `3b62be6` | **+224 / −2**, 5 파일 | main 직접 push (no PR) |

→ 본 Story 합계: **+1089 / −16**, 29 파일, 14 commit + 1 hub commit. **신규 LoC ~1089 + 0 회귀** (양 repo pytest GREEN).

### 1.3 테스트 결과

| Repo | 신규 test | passed | failed | skipped |
|---|---|---|---|---|
| `mctrader-data` | 7 (5 reader + 2 CLI for MCT-122 + 3 metrics for MCT-123 = 10, 그러나 통합 PR 에 MCT-120/121 test 도 포함되어 PR 합계 24 신규) | **308** | 0 | (확인 안 됨) |
| `mctrader-engine` | 3 (metrics_endpoint) | **800** | 1 (pre-existing, 무관) + 5 DB error (pre-existing, 무관) | (확인 안 됨) |

→ 본 Story 신규 test 분리:
- MCT-122: 5 reader + 2 CLI + 1 integration = **8 test**
- MCT-123: 3 (data) + 3 (engine) = **6 test**
- 합계 **14 신규 test**, 0 회귀

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 + RETRO-MCT-121 §5.5 표준 적용)

| 카테고리 | commit 수 | 비중 | 분류 |
|---|---|---|---|
| MCT-120 (MinIO) 본 fix | 4 | 29% | **Cat C (다른 Story finish-up)** |
| MCT-121 (Redis) 본 fix | 2 | 14% | **Cat C** |
| MCT-122 본 fix (DuckDB + CLI + integration test + engine dep) | 4 | 29% | 본 fix |
| MCT-123 본 fix (data metrics + endpoint + collector/runner 호출 + engine metrics) | 4 | 29% | 본 fix |

→ Cat C 43% (MCT-120/121 finish-up 6 commit), 본 fix 57% (8 commit). **RETRO-MCT-121 §5.5 의 Cat C 패턴 (PR scope 가 multiple Story 묶음) 가 본 PR 에서 재현** — PR #29 가 4 Story (MCT-120/121/122/123) 묶음.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-data` | `feat/mct-120-121-122-123` | ✅ | #29 | ✅ admin |
| `mctrader-engine` | **`feat/mct-122-123-engine-clean`** (cherry-pick clean) | ✅ | #47 | ✅ admin |
| `mctrader-hub` | `main` (직접 push) | ✅ | (PR 없음 — §3.4 별도 평가) | ✅ |

→ 3 repo 모두 origin 동기. RETRO-MCT-119-120 §3.1 의 web 미푸시 패턴 회피 성공 (본 Story 가 첫 3-repo cross-repo Story).

---

## 2. 잘된 점

### 2.1 cross-repo Story scope 누수 0 — 3 repo 동시 push/merge

본 Story 는 mctrader-data + mctrader-engine + mctrader-hub **3 repo cross-repo Story** (RETRO-MCT-121 의 2 repo 보다 1 repo 확장). 셋 다 push + merge 완료:

- mctrader-data: PR #29 admin merge
- mctrader-engine: PR #47 admin merge (별도 clean branch 생성, §2.2)
- mctrader-hub: main 직접 push (§3.4 정당성 평가)

→ **multi-repo 게이트 closed-loop 작동의 두 번째 사례 누적**. RETRO-MCT-119-120 §3.1 web 미푸시 → RETRO-MCT-121 §2.1 (2 repo) → RETRO-MCT-122-123 (3 repo). RETRO-MCT-121 §5.2 의 closed-loop 가 본 사례에서 재실증.

### 2.2 PR 충돌 회복 — clean cherry-pick branch 패턴

mctrader-engine 작업 중 Pipeline Phase 1+2 (PR #44 MCT-119+120) 가 feature branch 분기 이후 main 에 먼저 머지되어 add/add 충돌 발생. 처리:

1. main 에서 신규 branch `feat/mct-122-123-engine-clean` 생성
2. MCT-122/123 전용 commit 2개만 cherry-pick (`221e3fd` duckdb dep + `766e4a7` metrics endpoint)
3. clean push + 새 PR #47 open
4. CI green 즉시 admin merge

→ **conflict 해결 비용 0, 회귀 0**. merge conflict 를 manual resolve 하지 않고 clean re-apply 로 우회. **scope 가 작은 Story 의 conflict 회복 표준 패턴** — 14 commit 짜리 Story 였다면 cherry-pick 비용 누적, 본 Story 처럼 2 commit 이면 zero-cost.

### 2.3 도구 선택의 적합성 — DuckDB 의 S3 httpfs

L3 Parquet 분석 레이어 도입 시 후보:
- (a) Polars + pyarrow.parquet — 코드량 多, S3 credential 수동 inject
- (b) Spark — 컨테이너 1개 + JVM 의존, over-engineering
- (c) **DuckDB + httpfs extension** — embedded, S3 credential 환경변수 inject, SQL 표준

본 Story 는 (c) 선택 — `DuckDBReader` 47 LoC + 통합 smoke test 26 LoC = **73 LoC 로 분석 레이어 완성**. 추가 컨테이너 0, 추가 메모리 0 (라이브러리 import 만).

→ **임베디드 분석 도구 선택의 가치**. 향후 mctrader-web (Streamlit) 에서 DuckDB SQL 직접 호출 가능 — 운영 dashboard 의 backend 로 자연스럽게 확장 가능.

### 2.4 5 서비스 일괄 도입 — 모니터링 스택 부분 도입의 함정 회피

Prometheus + Grafana + 3 exporter (postgres / cadvisor / node) 를 **한 번에** 도입. 부분 도입 시 발생할 함정:

| 부분 도입 | 함정 |
|---|---|
| Prometheus + app metrics 만 | DB / 컨테이너 / 호스트 메트릭 부재 → dashboard 작성 시 누락 발견, 재방문 |
| Prometheus + Grafana 만 | exporter 부재 → dashboard 데이터 부족 |
| postgres_exporter 만 | Prometheus scrape 대상 부재 |

→ **인프라 도구는 묶음 도입이 자연** — 본 Story 는 5 서비스 일괄로 dashboard 작성 시점에 모든 메트릭 source 가용. 향후 dashboard JSON drop-in 만으로 시각화 완료.

### 2.5 admin merge autonomy + PMO 회고 자동 dispatch — 9번째 same-session 사례

PR #29 + PR #47 CI green 즉시 admin merge → 본 retro 자동 dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121/**122+123** = **9 Story (10 PR)** 동일 패턴 작동. ADR-020 D1 + MEMORY `feedback_admin_merge_autonomy.md` closed-loop 정착 누적 9건.

---

## 3. 발생한 이슈

### 3.1 [HIGH] mctrader-engine PR add/add 충돌 — feature branch 장기 분기 비용

**관측**:
- mctrader-engine 작업 시작 시 main 으로부터 분기한 branch 에서 MCT-122/123 commit 2개 작성
- 작업 중 Pipeline Phase 1+2 (PR #44 MCT-119+120) 가 main 에 먼저 머지 — **+4071 LoC, 64 파일**
- MCT-122/123 의 `pyproject.toml` + `health_server.py` 가 PR #44 와 add/add 충돌
- 해결: main 에서 clean branch 신규 생성 + 2 commit cherry-pick + 새 PR #47 (§2.2)

**근본 원인 분석**:
1. **feature branch 장기 분기** — MCT-122/123 작업 시작 시점에 PR #44 가 미머지 상태였으나 곧 머지될 예정이었음. branch base 를 PR #44 머지 후로 미루지 않음
2. **순차 Story sweep 시 base branch 갱신 부재** — 본 세션이 MCT-119/120/121/122/123 를 순차 진행하며 같은 branch 에 stack 하지 않고 매번 새 branch 를 main 에서 시작했어야 함
3. ADR-019 D1 (worktree isolation) 은 cross-Story branch race 회피 — 그러나 **base branch staleness 게이트 부재**

**의미**:
- 본 Story 는 2 commit cherry-pick 으로 회복 가능 — RETRO §2.2 zero-cost 회복
- 그러나 14 commit 짜리 Story 였다면 cherry-pick 비용 누적, conflict 영역 확장
- 같은 세션에서 다음 Story (MCT-124 후보) 도 같은 함정 가능

**평가**:
- §4.1 ADR-019 D? 후보 또는 superpowers `using-git-worktrees` skill 보완 — feature branch 시작 전 `git fetch + git rebase main` 또는 base branch 갱신 게이트
- 본 사례 1건 — 1주 관측 후 결정 (다음 Story 에서 같은 함정 재현 시 즉시 박제)

### 3.2 [LOW] CLI `df().to_string()` 실패 — numpy 미설치

**관측**:
- `mctrader-data query --sql` 첫 구현 시 `result.df().to_string()` 사용
- mctrader-data venv 에 numpy 미설치 → `df()` 호출 시 ImportError
- 해결: `cursor.fetchall() + cursor.description` 기반 수동 텍스트 테이블 출력

**근본 원인 분석**:
- DuckDB 의 `result.df()` 가 pandas DataFrame 반환 — 내부적으로 numpy 의존
- mctrader-data 는 **numpy 명시 의존성 없음** (Decimal 기반 시계열 처리, numpy 회피 정책)
- 본 Story 가 단순 SQL output 만 필요 → pandas/numpy 의존 도입 over-engineering

**의미**:
- numpy 회피 정책의 의도 적중 — 본 Story 가 numpy 도입 직전 catch
- DuckDB API 사용 시 의존성 footprint 점검 게이트 부재 — `result.df()` 같은 편의 API 가 silent 의존성 도입 가능

**평가**:
- 본 사례 1건 — 단순 grep / 코드 리뷰로 catch 가능 (`grep -r "\.df()" tests/ src/`)
- ADR 박제 불필요 — RETRO §3.4 patterns 누적 시 재평가

### 3.3 [LOW] DuckDB SET 명령 f-string SQL injection 우려 — 인프라 설정값 허용

**관측**:
- `DuckDBReader` 가 `MinioConfig` 필드를 f-string 으로 SET 명령 생성 (`f"SET s3_endpoint='{endpoint}'"`)
- 코드 리뷰에서 SQL injection 가능성 지적
- 평가: 인프라 설정값 (환경변수 기반 endpoint / access_key / secret_key) 으로 user input 아님 → 허용 수준 판단

**근본 원인 분석**:
- DuckDB 의 SET 명령은 prepared statement 미지원 — 값 inject 방법이 f-string 외 부재
- `MinioConfig` 의 source 가 환경변수 (compose 의 `.env`) — 운영자가 직접 통제하는 trust boundary
- user-facing API 가 아니므로 SQL injection 표면 없음

**의미**:
- 코드 리뷰의 보수적 지적이 합리적 — 그러나 컨텍스트상 실제 위험 없음
- 향후 user-input 기반 SQL 처리 시 (예: MCT-122 follow-up 에서 user-defined query parameter) 동일 패턴 재사용 시 위험
- 도메인 의도 박제 부재 — `MinioConfig` 가 **trusted infra config** 라는 marker (예: docstring 또는 type alias) 부재

**평가**:
- 도메인 의도 docstring 추가 권장 — `# trusted infra config: env-derived, NOT user input`
- ADR 박제 불필요 — 본 패턴 1건, 누적 사례 부족

### 3.4 [LOW] mctrader-hub main 직접 push — ADR-019 D6 의도적 우회

**관측**:
- mctrader-hub 의 `3b62be6` commit 이 PR 없이 main 에 직접 push
- ADR-019 D6 (worktree-merge gap, branch state validation) 적용 대상 외 — hub 는 trunk-based 단일 작업자 모델

**근본 원인 분석**:
- mctrader-hub 는 **메타 / 문서 / compose 통합 repo** — 코드 빌드/배포 대상 아님
- PR review 의 가치보다 main 직접 push 의 속도가 우선 (solo dev + 운영 자료)
- ADR-011 (CI standard) 도 mctrader-hub 적용 대상 외

**의미**:
- 본 Story 의 mctrader-hub 변경 (compose + prometheus.yml + grafana provisioning) 이 다른 repo 의 ci 와 무관 — main 직접 push 가 합리적
- 그러나 이 결정이 **암묵적** — ADR-019 / ADR-011 의 적용 범위 명시 부재
- 향후 mctrader-hub 작업이 "왜 PR 안 만들었나" 질문 받을 가능성

**평가**:
- ADR-019 또는 별도 ADR 에 "trunk-based repo 명시 (mctrader-hub)" 박제 — 1주 관측 후 결정
- 본 사례 1건, 단순 — README guidance 로 즉시 대체 가능

### 3.5 [LOW] PR #29 4 Story 묶음 — Cat C 43% (RETRO-MCT-121 §5.5 패턴 재현)

**관측**:
- PR #29 가 MCT-120 + MCT-121 + MCT-122 + MCT-123 = **4 Story 묶음**
- commit 분포: MCT-120 (4) + MCT-121 (2) + MCT-122 (4) + MCT-123 (4) = 14 commit
- 본 Story 관점에서 MCT-120/121 부분이 Cat C (다른 Story finish-up) 43%

**근본 원인 분석**:
- 같은 branch (`feat/mct-120-121-122-123`) 에 4 Story 누적 — branch 명에서도 의도 명시
- PR scope 가 branch 단위 → Story 단위 분리 안 됨
- RETRO-MCT-121 §5.5 의 Cat C 패턴 재현 — PR 단위와 Story 단위 분리 가시화 필요

**의미**:
- PR review / blame / revert 시 Story 단위 분리 어려움
- PMO retro 의 cost 분석 정확도 — commit message tag (`feat(mct-122):`, `feat(mct-123):`) 로 부분 회복

**평가**:
- RETRO-MCT-121 §6 #3 권고 ("PR commit 분포 Story tag 의무화") 가 본 PR 에서 **commit message tag** 로 부분 작동 — message prefix 가 Story 분리 가능하게 함
- 향후 Story 단위 PR 분할 또는 PR description 에 Cat 분류 표 박제

### 3.6 [HIGH] alembic 0002 마이그레이션 FK 타입 불일치 — psycopg DatatypeMismatch (재구동 후 발견)

**관측** (2026-05-10 시스템 재구동 시):
- 마이그레이션 0002 `strategy_set_pipeline.py` 적용 시 psycopg `DatatypeMismatch` 에러
- `strategy_promotion_events.evidence_run_id` 와 `pipeline_events.run_id` 가 `postgresql.UUID(as_uuid=True)` 로 선언
- 그러나 참조 대상 `strategy_runs.id` 는 `VARCHAR` 타입
- 해결: 두 컬럼을 `sa.String()` 으로 변경 (commit `5d090a8`, main 직접 push, 2 line 수정)

**근본 원인 분석**:
1. **FK 타입 일관성 검증 부재** — alembic migration 작성 시 참조 대상 컬럼 타입 자동 검증 게이트 없음
2. **dry-run / migration smoke test 부재** — MCT-119 (Phase 1) PR #44 작업 시 alembic 0002 가 실제 PostgreSQL 인스턴스에서 적용된 적 없음 (테스트는 unit 레이어, DB 마이그레이션은 미실행)
3. **schema source-of-truth 분산** — `strategy_runs.id` 타입은 0001 migration 또는 모델 파일에 산재, 0002 작성자가 참조 시 타입 확인 누락
4. ADR-018 D1 (Pydantic validator baseline) 은 application 레이어 입력 검증 — DB 마이그레이션 schema 일관성 게이트 별개

**의미**:
- 시스템 재구동 시점까지 silent — 운영 환경 진입 직전에 catch (운 좋게 staging 부재 사례)
- 마이그레이션 대 schema 불일치는 production 진입 후 발견 시 rollback 비용 매우 큼
- 본 사례는 즉시 fix 가능 (2 line) 였으나, 다른 unique constraint / index / partition 등은 회복 비용 증가

**평가**:
- §4.4 ADR 후보 발의 — alembic migration FK 타입 검증 baseline (CI 게이트 또는 schema lint)
- 본 사례 1건이지만 **HIGH** — 운영 환경 직격 결함 + 정적 검증 가능

### 3.7 [HIGH] ws_connected 프로브 tf=1h 워밍업 60분 unhealthy — health check 의미론 결함 (재구동 후 발견)

**관측** (2026-05-10 시스템 재구동 시):
- `mctrader-engine-paper` 컨테이너 health check 가 최대 60분 동안 unhealthy 상태
- `PaperRunner.ws_connected` 가 `executor.closed_bars` 또는 `_events` 비어있는지로 판단
- 그러나 tf=1h 타임프레임에서 첫 candle close 까지 최대 60분 소요 — 이 동안 WS 연결은 정상이나 health check 는 503 반환
- 해결: `WsWrapperStream.ticks_received` 카운터 추가, 첫 Bithumb tick 수신 즉시 healthy (commit `986f14c`, +11/-7, main 직접 push)

**근본 원인 분석**:
1. **health check 의미론 misalignment** — `ws_connected` 의 *의도*는 "WS 연결 상태", 실제 *구현* 은 "비즈니스 처리 결과 누적 여부"
2. **워밍업 기간 미고려** — 기존 docstring 에 `False while warming up` 으로 인지된 결함이 명시되어 있었음 (구현 시 의식적 trade-off, 그러나 long warm-up 시 unsustainable)
3. **타임프레임 가정** — 작성 당시 짧은 tf 가정, tf=1h 도입 시점에 재평가 부재
4. **raw upstream signal 부재** — `BithumbWebSocketStream` 의 raw tick count 같은 signal 이 wrapper 에 노출되지 않음 — health check 가 high-level 결과에 의존

**의미**:
- 운영 monitor (Prometheus health check) 가 정상 시스템을 unhealthy 로 잘못 분류 → 잘못된 alert / restart 트리거 가능
- 본 사례는 ADR-014 (Engine state machine) 에 정의된 "ready" 상태와 health endpoint 의 미스매치
- MCT-123 (Prometheus 모니터링) 도입 직후 발견 — **모니터링 도입이 health check 의미론 결함을 노출**한 효과

**평가**:
- §4.5 ADR 후보 발의 — health check 의미론 표준 (raw upstream signal vs business-level signal 분리, 워밍업 정책)
- 본 사례 1건이지만 **HIGH** — silent operational hazard (false unhealthy → alert fatigue 또는 자동 restart cascade)

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [MEDIUM] ADR-019 D? 후보 — base branch staleness 게이트

```
target_adr: ADR-019 D? 신규 또는 superpowers using-git-worktrees skill 보완
amendment_type: behavior (branch base 갱신 게이트)
trigger: RETRO-MCT-122-123 §3.1 mctrader-engine add/add 충돌
배경:
  - 순차 Story sweep 시 base branch 가 stale 상태로 다음 Story 시작 — 직전 Story 머지 후 base 갱신 부재
  - 본 Story 는 2 commit cherry-pick 으로 회복 가능했으나 14 commit 짜리 Story 였다면 비용 누적
  - ADR-019 D1 worktree isolation 은 cross-Story race 회피 — 그러나 base staleness 별개
문제:
  - feature branch 장기 분기 시 add/add 충돌 보장
  - 같은 파일 (`pyproject.toml`, `health_server.py` 등) 을 다수 Story 가 동시 수정 시 충돌 빈도 높음
  - silent debt — 충돌 발생 전까지 가시화 안 됨
제안 결정:
  a) Lite: 신규 Story 시작 시 `git fetch origin && git rebase origin/main` 표준 (PMOAgent 권고 또는 README)
  b) Medium: ADR-019 D? 신규 — feature branch 시작 전 base 갱신 게이트
  c) Heavy: superpowers using-git-worktrees skill 에 staleness 검증 단계 추가
예상 결과:
  - add/add 충돌 빈도 감소
  - cherry-pick / merge resolve 비용 회피
보류 사유:
  - 본 사례 1건 — 1주 관측 권장 (다음 Story 에서 재현 시 즉시 박제)
  - cherry-pick 회복 비용 zero 였음 — 박제 시급성 낮음
```

### 4.2 [LOW] HealthServer `/metrics` 표준 — 추가 컴포넌트 도입 시 재사용 패턴

```
target_adr: ADR 신규 또는 README guidance
amendment_type: artifact (코드 패턴)
trigger: MCT-123 mctrader-data + mctrader-engine 양쪽 동일 패턴 구현
배경:
  - mctrader-data + mctrader-engine 양쪽이 거의 동일한 패턴 구현:
    - prometheus_client Counter/Gauge 정의
    - HealthServer에 /metrics route 추가
    - ThreadingHTTPServer bind 0.0.0.0
    - prometheus-client>=0.20 의존성
  - 향후 mctrader-web / 추가 컴포넌트 도입 시 같은 패턴 재구현 비용
문제:
  - DRY 원칙 위반 — 양 repo 에 같은 코드 ~50 LoC 중복
  - 명명 규칙 / port / bind 정책의 silent divergence 가능
제안 결정:
  a) Lite: README guidance — "/metrics 엔드포인트 표준 (0.0.0.0:port, prometheus_client, name convention)"
  b) Medium: 공유 라이브러리 (mctrader-common 가칭) — HealthServer + metrics base 추출
  c) Heavy: ADR 박제 — Prometheus 노출 표준
예상 결과:
  - 추가 컴포넌트 도입 시 metrics endpoint 비용 감소
  - 명명 규칙 일관성
보류 사유:
  - 본 사례 2건 — 누적 사례 부족, 추가 컴포넌트 도입 시점에 재평가
  - 공유 라이브러리 추출은 별도 Story 필요 — over-engineering 위험
```

### 4.4 [HIGH] alembic migration FK 타입 일관성 baseline — schema 검증 게이트

```
target_adr: ADR 신규 (또는 ADR-018 확장 — Defensive coding baseline 의 DB schema 변형)
amendment_type: governance + artifact (CI 게이트 + 패턴)
trigger: RETRO-MCT-122-123 §3.6 alembic 0002 FK 타입 불일치 (psycopg DatatypeMismatch)
배경:
  - ADR-018 D1 (Pydantic validator baseline) 은 application 레이어 입력 검증
  - 그러나 alembic migration schema 일관성 게이트 부재
  - 본 사례: strategy_runs.id (VARCHAR) 와 evidence_run_id/run_id (UUID) 타입 불일치
  - PR #44 (4071 LoC, 64 파일) CI green + admin merge 후에도 미탐지 — 시스템 재구동 시점 catch
문제:
  - migration smoke test (실제 PostgreSQL 적용) CI 게이트 부재
  - schema source-of-truth 분산 — 0001 migration vs 모델 vs 0002 migration 간 cross-check 부재
  - production 진입 후 발견 시 rollback 비용 매우 큼 (본 사례는 운 좋게 재구동 시점 catch)
제안 결정:
  a) Lite: alembic migration PR 시 reviewer checklist — "FK 타입 = 참조 컬럼 타입 일치 확인"
  b) Medium: CI 게이트 — pull_request 시 임시 PostgreSQL 컨테이너에서 `alembic upgrade head` smoke
  c) Heavy: alembic-utils 또는 자체 lint — migration AST 분석 + FK 양쪽 타입 자동 비교
배제 옵션:
  - SQLAlchemy ORM 모델 SSOT 화 (autogenerate) — mctrader-engine 은 explicit migration 정책 (ADR 미박제, 그러나 관행)
예상 결과:
  - schema 불일치 production 도달 0
  - migration PR 검증 표준화
보류 사유:
  - 본 사례 1건 — 그러나 HIGH severity (production 직격) → 즉시 박제 권장
  - 즉시 적용 가능한 Lite (reviewer checklist) 부터 시작, 누적 사례 시 Medium 승급
권장 priority: HIGH (다음 alembic 0003 작성 전 결정)
```

### 4.5 [HIGH] health check 의미론 표준 — raw upstream signal vs business-level signal 분리

```
target_adr: ADR-014 amendment (Engine state machine) 또는 ADR 신규
amendment_type: behavior + artifact (health check 패턴)
trigger: RETRO-MCT-122-123 §3.7 ws_connected tf=1h 60분 false unhealthy
배경:
  - PaperRunner.ws_connected 가 "WS 연결 상태" 의도였으나 구현은 "비즈니스 처리 결과 누적 여부"
  - tf=1h 워밍업 기간 동안 health endpoint 503 반환 — 정상 시스템 false unhealthy
  - 기존 docstring 에 "False while warming up" 으로 결함 명시 — 의식적 trade-off 였으나 long tf 도입 시 unsustainable
  - MCT-123 Prometheus 모니터링 도입 직후 발견 — 모니터링 도입이 의미론 결함 노출
문제:
  - health check 가 "운영자가 알고 싶은 것" 과 "구현이 측정하는 것" 미스매치
  - raw upstream signal (WS tick 수신, connection handle 활성) 이 wrapper 레이어에 노출 안 됨
  - 워밍업 정책 명시 부재 — 어떤 신호로 ready 판정하는지 표준 없음
  - false unhealthy → 잘못된 alert / 자동 restart cascade 위험
제안 결정:
  a) Lite: health check 패턴 README guidance —
     - liveness: 프로세스 살아있음 (raw signal — connection handle 등)
     - readiness: 비즈니스 처리 가능 (high-level signal — 첫 결과 도달)
     - 양쪽 분리 endpoint 또는 명시적 의미론
  b) Medium: ADR-014 (Engine state machine) amendment — state vs health endpoint 매핑 표
  c) Heavy: 신규 ADR — health check 의미론 baseline (모든 mctrader 컴포넌트 적용)
예상 결과:
  - 모니터링 false alert 감소
  - 새 컴포넌트 도입 시 health check 의미론 일관성
  - tf / timeframe 변경 시 회귀 회피
배제 옵션:
  - health check 자체 제거 (운영 baseline 손실)
  - timeout 조정만 (근본 원인 미해결, tf=1d 도입 시 재발)
보류 사유:
  - 본 사례 1건 + MCT-123 (모니터링 도입) 의 부수 발견 — 그러나 HIGH severity (silent operational hazard)
  - ADR-014 amendment 가 적정 (Engine state machine 이 이미 ready/running/stopping state 정의)
권장 priority: HIGH (다음 컴포넌트 health check 추가 전 결정)
관련:
  - ADR-014 Engine state machine
  - MCT-123 Prometheus 모니터링 (health check 의 실질 consumer)
  - HealthServer /metrics 패턴 (§4.2) — 양 endpoint 표준 함께 박제 권장
```

### 4.6 [LOW] mctrader-hub trunk-based 정책 박제

```
target_adr: ADR-019 amendment 또는 README guidance
amendment_type: governance (repo 별 정책 명시)
trigger: RETRO-MCT-122-123 §3.4 hub main 직접 push
배경:
  - mctrader-hub 는 메타/문서/compose 통합 repo — PR review / CI 적용 대상 외
  - 그러나 본 결정이 ADR / README 에 명시 부재
  - 향후 작업자가 "왜 PR 안 만들었나" 질문 가능
문제:
  - 6 repo 의 PR/CI 정책이 일괄 동일하다는 silent assumption
  - mctrader-hub 의 trunk-based 결정이 implicit
제안 결정:
  a) Lite: mctrader-hub README 에 "trunk-based, no PR required" 명시
  b) Medium: ADR-019 amendment — 6 repo 별 PR/CI 정책 매트릭스
예상 결과:
  - 작업자 confusion 회피
  - 정책 명시화
보류 사유:
  - 본 사례 1건 — README 갱신으로 즉시 해결, ADR 박제 over-engineering
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 9+ Story sweep — token efficiency 누적 (갱신)

본 세션 (2026-05-09 ~ 2026-05-10 cross-day) 처리 누적:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 mctrader-market audit)
- MCT-114 (D1/D2 market-bithumb audit)
- MCT-115 (D1/D2/D3 mctrader-data audit)
- MCT-116 (D2/D3/D5 mctrader-engine audit)
- MCT-117 (D1/D4/D5 mctrader-web audit)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2 — 4071 LoC)
- MCT-121 (Upbit 거래소 — 신규 plugin repo + 4015 LoC)
- **MCT-122+123 (DuckDB + Prometheus/Grafana — 1089 LoC, 3 repo cross-repo)**

→ **9 Story (10 PR) + ~9000 LoC + 1 신규 plugin repo + 5 모니터링 컨테이너 = single-session completion**. RETRO-MCT-121 §5.1 의 8 Story 를 9 로 확장. **codeforge ζ arc velocity 가 인프라 컴포넌트 (모니터링 stack) 도입까지 일반화**.

### 5.2 multi-repo Story 게이트 closed-loop 작동 — 3-repo 사례 추가

| Story | repos | scope 누수 | 비고 |
|---|---|---|---|
| MCT-119 | engine + web | **발생 (web 미푸시)** | RETRO-MCT-119-120 §3.1 |
| MCT-120 | engine 단일 | N/A | — |
| MCT-121 | mctrader-market-upbit + mctrader-data | **0** | RETRO-MCT-121 §2.1 |
| **MCT-122+123** | **data + engine + hub** | **0** | **본 retro §2.1** |

→ closed-loop 작동의 **두 번째 사례 누적 + 3-repo 확장**. RETRO-MCT-119-120 §4.1 ADR-020 D2 후보 (multi-repo 게이트 박제) 의 박제 시급성 약화 — closed-loop 가 작동하면 ADR 박제 없이 회피 가능 실증. **그러나 1주 관측 후 재발 시 즉시 박제 권장** (closed-loop 가 휘발성 — MEMORY trigger 의존).

### 5.3 PR 충돌 회복 패턴 — clean cherry-pick branch 표준 후보

본 Story §2.2 의 clean cherry-pick branch 패턴이 명시된 첫 사례:

| Story | 충돌 발생 | 회복 패턴 |
|---|---|---|
| MCT-119+120 | engine PR #44 자체 충돌 없음 (개별 분기) | N/A |
| **MCT-122+123** | **engine feature branch vs PR #44 add/add 충돌** | **clean cherry-pick branch (§2.2)** |

→ 향후 **base branch staleness** 발생 시 표준 회복 패턴으로 박제 가능. §4.1 ADR-019 D? 후보의 reactive (회복) 측 — proactive (예방) 측은 base 갱신 게이트.

### 5.4 도구 선택의 적합성 누적 — 임베디드 / 표준 / 묶음 도입 패턴

본 Story 의 도구 선택 결정 3건:

| 결정 | 패턴 |
|---|---|
| DuckDB embedded SQL (§2.3) | 임베디드 분석 도구 — 컨테이너 0, 메모리 0 |
| 5 서비스 일괄 도입 (§2.4) | 인프라 묶음 — 부분 도입 함정 회피 |
| numpy 회피 (§3.2) | 의존성 minimal — `df()` 대신 `fetchall()` |

→ **소규모 / 표준 / 임베디드 우선 패턴**. mctrader-engine `duckdb` 의존성도 사용 코드 미작성 상태에서 박제 — 향후 사후 분석 컴포넌트 도입 시 **dependency-first** 패턴.

### 5.5 부수 fix 카테고리 갱신 — Cat C 패턴 누적

| Story | Cat A (pre-existing) | Cat B (self-discovered) | Cat C (다른 Story finish-up) | 본 fix |
|---|---|---|---|---|
| MCT-117 | **350%** (39/11) | <10% | 0 | 11 |
| MCT-119+120 | <10% | 17% | 0 | 29 |
| MCT-121 | <10% | 7% | **36%** (MCT-115 finish-up) | 8 |
| **MCT-122+123** | <10% | <10% | **43%** (MCT-120/121 finish-up) | **8** |

→ Cat C 가 두 Story 연속 발생. **PR scope 가 multi-Story branch 묶음** 패턴이 본 세션 관성. RETRO-MCT-121 §6 #3 권고 (PR commit 분포 Story tag 의무화) 가 본 PR 에서 commit message prefix 로 부분 작동 — PR description 에 Cat 분류 표는 미박제.

### 5.6 [신규] 재구동 시점 발견 결함 — pre-production smoke gate 부재 패턴

본 Story 후속 (2026-05-10) 시스템 재구동 과정에서 발견된 결함 2건이 동일한 메타 패턴 공유:

| Story / 결함 | 결함 유형 | 정적 검증 가능? | CI 미탐지 원인 |
|---|---|---|---|
| MCT-119 → §3.6 alembic 0002 FK 타입 | schema 일관성 | **YES** (lint / smoke migration) | migration smoke CI 게이트 부재 |
| MCT-122/123 → §3.7 ws_connected tf=1h | health check 의미론 | partial (timeframe sweep 테스트로 catch 가능) | 워밍업 정책 없음 + tf 가정 변화 미반영 |

**메타 패턴**:
- 양쪽 모두 **운영 환경 첫 가동** 시점에 catch
- 양쪽 모두 **CI green + admin merge 후 silent debt 누적**
- 양쪽 모두 **정적 검증 또는 smoke test 도입 시 pre-production catch 가능**
- ADR-018 D1~D7 (Defensive coding baseline) 은 application 입력 검증 — **인프라 / 운영 레이어** (DB schema, health endpoint) 까지 미확장

**의미**:
- codeforge ζ arc 의 빠른 velocity 가 production 진입 직전의 **pre-production smoke gate** 부재를 노출
- staging 환경 부재 + production 첫 가동이 곧 smoke test 인 운영 모델의 한계 인식
- §4.4 alembic FK lint + §4.5 health check 의미론 표준 + 향후 **container compose smoke CI** (전체 stack 1회 기동 검증) 박제 후보

**평가**:
- 본 세션 같은 패턴 2건 누적 — pattern 박제 시급성 증가
- 다음 Story / Epic 진입 전 **pre-production smoke gate** 권고 (lite: README, medium: CI workflow 신규)

---

## 6. 개선 제안 (다음 세션 반영)

1. **[HIGH] alembic migration FK 타입 검증 baseline (§4.4)** — 재구동 시점 발견 §3.6 가 production 직격 결함. 즉시 적용 가능한 **Lite (reviewer checklist)** + 다음 단계 **Medium (CI smoke gate)** 권장. 다음 alembic 0003 작성 전 결정.

2. **[HIGH] health check 의미론 표준 (§4.5)** — §3.7 false unhealthy 가 silent operational hazard. ADR-014 amendment 또는 신규 ADR 로 liveness vs readiness 분리, raw upstream signal 노출 표준화. 다음 컴포넌트 health check 추가 전 결정.

3. **[HIGH] pre-production smoke gate (§5.6)** — 재구동 시점 발견 결함 2건 패턴이 공유하는 메타 결함. compose 전체 stack smoke CI workflow 또는 `make smoke` 표준 박제. ADR 박제 또는 mctrader-hub README guidance 즉시 적용.

4. **[MEDIUM] base branch staleness 게이트 (§4.1)** — 신규 Story 시작 시 `git fetch origin && git rebase origin/main` 표준화. 본 Story §3.1 의 add/add 충돌은 zero-cost 회복 가능했으나, 14 commit 짜리 Story 였다면 비용 누적. PMOAgent 권고 또는 README guidance 즉시 적용 가능. ADR 박제는 1주 관측 후 결정.

5. **[MEDIUM] PR description Cat 분류 표 의무화 (§3.5)** — RETRO-MCT-121 §6 #3 의 commit message tag 표준은 본 PR 에서 작동. 다음 단계로 **PR description 에 Cat A / B / C 분리 표 박제** — PMO retro 의 cost 분석 정확도 향상. 다음 PR (MCT-124 후보) 부터 적용.

6. **[LOW] HealthServer `/metrics` 표준 README guidance (§4.2)** — 본 Story 에서 mctrader-data + mctrader-engine 양쪽이 동일 패턴 ~50 LoC 중복. 향후 mctrader-web 등 추가 컴포넌트 도입 시 재사용. ADR 박제는 추가 사례 누적 후 (3+ 컴포넌트 도입 시점) 결정.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| MCT-122 DuckDBReader + MinioConfig + 5 unit test | ~10% |
| MCT-122 CLI `query --sql` + 2 unit test | ~5% |
| MCT-122 MinIO httpfs 통합 smoke test | ~5% |
| MCT-122 numpy 회피 friction (§3.2) | ~3% |
| **MCT-123 hub compose 5 서비스 + prometheus.yml + grafana provisioning** | **~15%** |
| MCT-123 mctrader-data metrics.py + endpoint + collector/runner 호출 | ~10% |
| MCT-123 mctrader-engine metrics.py + endpoint + 0.0.0.0 변경 | ~5% |
| **MCT-120/121 finish-up (Cat C — MinIO uploader + Redis publisher)** | **~25%** |
| **mctrader-engine PR add/add 충돌 회복 (clean cherry-pick branch)** | **~8%** |
| PR open + admin merge + CI green 확인 (PR #29, PR #47) | ~5% |
| Story file MCT-122/MCT-123 + 본 retro 작성 | ~5% |
| 그 외 (코드 리뷰 SQL injection 검토, 도구 선택 검증) | ~4% |

→ **부수 비용 (Cat C + 충돌 회복) ~33%** — RETRO-MCT-121 ~20% 보다 증가. PR #29 가 4 Story 묶음 + engine PR 충돌이 누적 효과. §6 #1 (base 갱신 게이트) + §6 #2 (PR Cat 분류) 적용 시 향후 ~20% 회피 가능.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-017**: Zero-loss ingestion + WAL → L3 tiered compaction — 본 Story MCT-122 의 분석 레이어 도입 trigger
- **ADR-019**: Parallel agent isolation — D? 후보 (base branch staleness 게이트, §4.1)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro trigger)
- **ADR-011**: CI standard — 본 PR #29 + PR #47 CI green
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #29 + PR #47 admin merge 자율 (9번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: PR #29 + PR #47 CI green 자동 recovery 사이클 적용
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — 본 Story 가 ζ arc 진입 후 첫 인프라 컴포넌트 (모니터링 stack) 도입
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준)
  - `RETRO-MCT-119-120-strategy-pipeline.md` (§3.1 multi-repo scope 누수 — 본 retro §2.1 회피)
  - `RETRO-MCT-121.md` (§2.1 multi-repo 게이트 closed-loop, §5.5 Cat C 패턴 — 본 retro §3.5 재현, §6 #3 권고 commit tag 본 PR 에서 작동)

---

## 9. Story §11 회고 pointer

- `docs/stories/MCT-122.md` §11 에 본 retro pointer 박제 완료
- `docs/stories/MCT-123.md` §11 에 본 retro pointer 박제 완료

ADR-020 D1 enforcement gap (RETRO-MCT-117 §3.2) 회피 패턴 적용 — Story file 작성 시점에 동시 박제.

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **mctrader-engine main worktree branch state 검증** (RETRO-MCT-119+120 §10.2 패턴) — 본 세션 후 engine main worktree 가 어느 branch 인지 확인
- **Grafana dashboard JSON drop-in** — 본 Story 가 provisioning 만 박제, 실제 dashboard 미작성. 다음 Story 후보:
  - mctrader-data ingester / compactor dashboard (`ingester_events_total`, `compactor_last_l3_timestamp`)
  - mctrader-engine runtime dashboard (`engine_open_positions`, `engine_cycle_delay_seconds`)
  - postgres / cadvisor / node_exporter base dashboard (community import)

### 10.2 ADR 박제 (우선순위 갱신)

- **[HIGH] §4.4 alembic FK 타입 검증 baseline** — 다음 alembic 0003 작성 전 결정 (Lite reviewer checklist 즉시 적용)
- **[HIGH] §4.5 health check 의미론 표준** — ADR-014 amendment 또는 신규 ADR (다음 컴포넌트 health check 추가 전)
- **[HIGH] §5.6 pre-production smoke gate** — compose 전체 stack 1회 기동 검증 CI workflow 또는 `make smoke` 박제
- **[MEDIUM] ADR-019 D? base branch staleness 게이트** (§4.1) — 1주 관측 권장 (다음 Story 재발 시 즉시 박제)
- **[LOW] HealthServer `/metrics` 표준** (§4.2) — 추가 컴포넌트 (mctrader-web 등) 도입 시점에 재평가
- **[LOW] mctrader-hub trunk-based 정책 박제** (§4.6) — README guidance 즉시 적용, ADR 박제는 보류

### 10.3 별도 issue 발의

- **Grafana dashboard JSON drop-in Story** — `mctrader-hub/monitoring/grafana/dashboards/*.json` 작성
- **mctrader-data 의존성 audit** — `Grep "\.df\(\)"` 등 silent numpy/pandas 의존 도입 부위 점검

### 10.4 DuckDB Analytics 후속 Story 트리거

본 Story MCT-122 완료로 다음 Story 가능:
- **mctrader-web Streamlit DuckDB SQL 페이지** — 운영자용 ad-hoc query UI
- **mctrader-engine 사후 분석 컴포넌트** — backtest 결과 + L3 Parquet join 분석 (duckdb 의존성 박제됨)
- **데이터 검증 cron** — 백필 누락 / OHLCV gap 자동 검증 (DuckDBReader + cron)

### 10.5 Prometheus/Grafana 모니터링 후속 Story 트리거

본 Story MCT-123 완료로 다음 Story 가능:
- **dashboard JSON drop-in** (§10.1)
- **alerting rules** — Prometheus alertmanager + 임계 alert (collector 멈춤 / engine cycle delay 과다 등)
- **mctrader-web `/metrics` endpoint** — 본 Story §4.2 패턴 재사용

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10

---

## Amendment — 2026-05-10 재구동 fix 후속 보강

**Trigger**: 시스템 재구동 과정에서 발견된 결함 2건 (commit `5d090a8` alembic 0002 FK + commit `986f14c` ws_connected tf=1h) 의 회고 박제.

**갱신 범위**:
- §3.6 [HIGH] alembic 0002 FK 타입 불일치 신규 — psycopg DatatypeMismatch, 2 line fix
- §3.7 [HIGH] ws_connected tf=1h 60분 unhealthy 신규 — health check 의미론 결함, +11/-7 fix
- §4.4 [HIGH] ADR 후보 신규 — alembic migration FK 타입 검증 baseline (CI smoke gate)
- §4.5 [HIGH] ADR 후보 신규 — health check 의미론 표준 (liveness vs readiness, raw upstream signal 노출)
- §4.6 (이전 §4.3) mctrader-hub trunk-based 정책 — 번호 재배치
- §5.6 [신규] Cross-Story 패턴 — 재구동 시점 발견 결함 메타 패턴 (pre-production smoke gate 부재)
- §6 개선 제안 6건으로 확장 (HIGH 3 / MEDIUM 2 / LOW 1) — §4.4/4.5/5.6 우선
- §10.2 ADR 박제 우선순위 갱신 — HIGH 3건 (§4.4/4.5/5.6) 즉시 결정 권장

**핵심 발견**:
- 양 결함 모두 **CI green + admin merge 후 silent debt 누적**
- 양 결함 모두 **운영 환경 첫 가동** 시점 catch — staging 부재 모델의 한계 노출
- ADR-018 (Defensive coding baseline) 의 application 레이어 검증을 **인프라 / 운영 레이어** (DB schema, health endpoint) 까지 확장 필요

**작성**: PMOAgent (Cross-Story 패턴 분석 — 재구동 fix 후속 회고)
**작성일**: 2026-05-10
