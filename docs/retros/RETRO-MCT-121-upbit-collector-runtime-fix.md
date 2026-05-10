# RETRO-MCT-121-upbit-collector-runtime-fix — Upbit Collector 배포 후 런타임 이슈 2건 + Docker 빌드 인프라 1건

**범위**: MCT-121 follow-up — Upbit Collector 배포 후 발견된 런타임 fix 2건 (`UpbitTradeEvent.exchange` AttributeError + `WalIngester` closed restart loop) + Docker 빌드 인프라 fix 1건 (vendor wheel 패턴 도입)
**기간**: 2026-05-10 (single-day, RETRO-MCT-119-runtime-fix 직후 동일 세션)
**Trigger**: upbit-ingester 컨테이너 시작 즉시 모든 심볼에서 `AttributeError("'UpbitTradeEvent' object has no attribute 'exchange'")` 발생 → 사용자 surface → fix 적용 후 PMO 회고 자동 dispatch
**Status**: mctrader-data `32fe512` 커밋 완료 (단일 commit, 3 영역 합본), main 머지 직전
**Story file**: `docs/stories/MCT-121.md` §11 (본 retro pointer 박제 권고)
**Repo**: `mctrader-data` (`c:\workspace\mclayer\mctrader-data`) — runtime fix + Docker 인프라 · `mctrader-hub` (`c:\workspace\mclayer\mctrader-hub`) — docs

---

## 1. 결과 요약

### 1.1 수행 작업 매트릭스

| # | 영역 | 증상 | Root cause | Fix | 분류 |
|---|---|---|---|---|---|
| Fix 1 | `collector._emit_to_wal` (Upbit) | upbit-ingester 시작 즉시 `AttributeError("'UpbitTradeEvent' object has no attribute 'exchange'")` (attempt=0, 모든 심볼) | `_emit_to_wal` 5곳에서 `event.exchange` 접근. Bithumb 이벤트(`_BaseEvent` 상속)는 `exchange` 필드 보유, `UpbitTradeEvent`는 미보유 — 인터페이스 계약 불일치 | 5곳 모두 `event.exchange` → `self._exchange` 치환 | **Cat B (self-discovered defect)** — 신규 Upbit 통합 첫 production trigger |
| Fix 2 | `CollectorDaemon._run_with_restart` | Fix 1 surface 후 attempt=1, 2, 3, ... 모두 `RuntimeError('WalIngester is closed')` 즉시 실패. attempt=102까지 누적 재시도 | `run()` finally 블록이 WalIngester를 close하는데 `_run_with_restart`가 **같은 daemon 인스턴스 재사용** → closed ingester 에 write 시도 | `_build_ingesters()` 메서드 추출, `run()` 시작 시 closed 감지하면 재생성 | **Cat F (cascading defect, 신규 카테고리 후보)** — Fix 1 surface 후 부수 발견된 daemon 재시작 불가 결함 |
| Fix 3 | Dockerfile 빌드 | `docker compose build` 실패 — `/usr/local/bin/mctrader-data: not found` → 이후 `No module named 'mctrader_data'` | git+https private deps (mctrader-market 패밀리) 가 GITHUB_TOKEN 없이 빌드 불가 + 기존 `mctrader-data` 스크립트 entrypoint 가 deps stage 에 존재하지 않음 | **vendor wheel 패턴 도입** (vendor/*.whl + pip --no-deps + sed 로 git+https 제거 + uv 가 PyPI deps 만 해석) + ENTRYPOINT 를 `python -m mctrader_data.cli` 로 변경 | **Cat E (infra debt)** — RETRO-MCT-119-runtime-fix §3.3 (Docker GitHub-dep rebuild 불가) 와 동일 root cause family, 본 retro 가 해결 1순위 (Wheel pre-build) 의 변형 (vendor 디렉토리) 채택 |

### 1.2 commit 분포

| commit | repo | 내용 |
|---|---|---|
| `32fe512` | mctrader-data | (1) collector.py 5곳 `event.exchange` → `self._exchange` (Fix 1) + (2) `_build_ingesters()` 추출 + run() 재생성 가드 (Fix 2) + (3) Dockerfile vendor wheel + python -m entrypoint (Fix 3) + vendor/*.whl 3개 (mctrader-market 패밀리 pre-built) |

→ **3 영역 단일 commit 합본**. RETRO-MCT-119-runtime-fix 의 `f3dc511` (3 영역 합본) 패턴 재실증 — runtime fix 의 atomic recovery 이점.

### 1.3 테스트 검증

- 사용자 수동 검증: upbit-ingester 20개 심볼 모두 정상 수집, WAL 파일 80개+ 생성
- Docker image `mctrader-data:pilot` 재빌드 성공
- 기존 16 pytest 통과 (회귀 0)
- **자동 테스트 surface 실패** — Fix 1 (`UpbitTradeEvent.exchange`) 는 `tests/test_adapters.py` (6 unit) + `tests/integration/test_upbit_collector.py` (MCT-121 §1.4 박제) 가 surface 못 함. WAL append flow 의 Upbit 경로가 mock 되거나 `_emit_to_wal` 5곳 모두 커버 안 됨

### 1.4 부수 fix 비율 (RETRO 누적 표준 적용)

| 카테고리 | 분류 | 비고 |
|---|---|---|
| Fix 1 (`UpbitTradeEvent.exchange`) | **Cat B (self-discovered)** | MCT-121 신규 Upbit 통합 첫 production trigger 시 surface |
| Fix 2 (`WalIngester closed restart loop`) | **Cat F (cascading defect, 신규 카테고리 후보)** | Fix 1 surface 직후 부수 발견 — single-fault 가정의 daemon restart 설계가 Fix 1 multi-fault 노출 시 무력화 |
| Fix 3 (Dockerfile vendor wheel) | **Cat E (infra debt)** | RETRO-MCT-119-runtime-fix §3.3 와 동일 root cause family — 본 retro 가 해결 (vendor 디렉토리 = §3.3 "C 옵션" 의 변형, mctrader-data 단일 컨테이너 적용) |

→ **3 fix 모두 다른 카테고리** — RETRO 누적 표준의 Cat B/E 외 신규 Cat F surface. §5.2 박제 권고.

---

## 2. 잘된 점

### 2.1 Fix 1+2 cascading 진단 — single-fault 가정 한계 surface

attempt=0 의 AttributeError 만 보고 fix 했다면 attempt=1+의 `WalIngester is closed` 가 후속 production trigger 에서 재 surface — **두 fault 가 cascading 임을 진단**. 실제 atomic recovery: Fix 1 만 적용 시 이미 daemon 1회 close 됐으므로 restart 시 Fix 2 까지 동시 노출. 진단 cost 추가 ~25% 였으나 production rollout 1회로 종결.

### 2.2 Docker 빌드 인프라 정면 돌파 — vendor wheel 패턴 도입

RETRO-MCT-119-runtime-fix §3.3 에서 surface 된 "GitHub git-dep rebuild 불가" 문제를 **본 retro 가 정면 해결**. Wheel pre-build (1순위 권장) 의 변형 (internal PyPI 인프라 없이 vendor 디렉토리 사용) 채택:
- `vendor/*.whl` 3개 pre-build (mctrader-market 패밀리)
- `vendor/.gitignore` 의 `*.whl` 허용
- Dockerfile `pip install --no-deps ./vendor/*.whl` + `sed -i '/mctrader-market.*git+/d' pyproject.toml` + `uv pip install --system .` (PyPI deps 만 해석)
- `BuildKit secret mount` 패턴 (RETRO-MCT-119-runtime-fix §3.3 2순위) 폐지 — `--mount=type=secret,id=github_token` 코드 제거

→ **6-repo 컨테이너 중 1개 (mctrader-data) 부분 적용** — 나머지 5 repo (engine/web/market 패밀리/hub) 동일 패턴 확장 권장 (§4.3).

### 2.3 16 pytest 회귀 0 + 사용자 수동 검증 정상 — atomic recovery 사이클

`32fe512` 단일 commit 으로 (1) collector.py 5곳 + (2) `_build_ingesters()` 추출 + (3) Dockerfile + (4) vendor wheels 동시 적용. 운영 환경 1회 deploy 로 회복:
- upbit-ingester 20개 심볼 모두 정상 수집
- WAL 파일 80개+ 생성
- Docker image 재빌드 성공
- 기존 16 pytest 통과

→ RETRO-MCT-119-runtime-fix §2.1 의 atomic recovery 패턴 재현 — runtime fix 의 single fix-cycle 회복 효율 실증.

### 2.4 자동 PMO 회고 dispatch — 10번째 same-session 사례

`32fe512` 커밋 후 사용자 trigger 없이 본 retro dispatch. ADR-020 D1 의 10번째 same-session 사례 (이전 9번 + 본 retro). MEMORY `feedback_pmo_retro_mandatory.md` closed-loop 정착 → **runtime fix + 인프라 fix 합본 commit 도 PMO 회고 dispatch 자격** 실증 (RETRO-MCT-119-runtime-fix §2.4 의 9번째 사례 갱신).

---

## 3. 발생한 이슈

### 3.1 [HIGH] 인터페이스 계약 불일치 — Bithumb/Upbit 이벤트 타입 분기 미박제 (사용자 패턴 분석 1)

**관측**:
- `mctrader-market-upbit/ws_events.py`: `UpbitTradeEvent`, `UpbitOrderbookEvent`, `UpbitTickerEvent` (모두 `exchange` 필드 미보유)
- `mctrader-market-bithumb/ws_events.py`: `_BaseEvent` 보유 (`exchange` 필드 포함) → Bithumb 이벤트 모두 상속
- `mctrader-data/collector.py:_emit_to_wal` 5곳에서 `event.exchange` 접근 — Bithumb 이벤트만 통과, Upbit 이벤트는 AttributeError

**근본 원인 분석**:

**인터페이스 계약 불일치 = HIGH risk 패턴**:

근거:
1. **mctrader-market-upbit / mctrader-market-bithumb 이 별도 repo** — 공통 base 이벤트 인터페이스 미정의. 각 repo 독립 진화 시 필드 drift 자연 발생
2. **collector.py 가 두 exchange 의 이벤트를 통일 가정** — `event.exchange` 같은 공통 필드 가정이 단방향 (Bithumb → Upbit) 일치 검증 없이 진행
3. **MCT-121 §3 (`pyproject.toml` mctrader-market-upbit git dependency 추가)** 시점에 **이벤트 타입 호환성 audit 미수행** — collector 가 Upbit 이벤트를 처리하는 부분이 dispatch 추가만 됐고 필드 일치 검증 누락
4. **adapter 계층 (`tests/test_adapters.py` 6 unit)** 은 dispatch 만 검증, 이벤트 필드 호환성 미검증

**의미**:
- 신규 exchange (예: Binance, Coinbase) 추가 시마다 동일 패턴 재발 risk
- 이벤트 타입 필드 drift 가 production 첫 trigger 시 surface — pre-deploy lint 미가능 (pyright 가 `Union[BithumbEvent, UpbitEvent]` 의 attribute 접근 catch 못 함, 사용자 보고 미확인)
- 현재 fix 는 `event.exchange` → `self._exchange` 우회 — **근본 fix 는 공통 이벤트 protocol 정의** (`exchange`, `symbol`, `event_time` 같은 공통 필드 protocol)

**평가**:
- **§4.1 ADR 후보 발의** — exchange 이벤트 공통 protocol 정의 + collector 의 이벤트 필드 접근 시 protocol 명시
- 임계 충족: 본 사례 1건 + 향후 exchange 추가 잠재 = **즉시 박제 권장 (Phase 후속)**

### 3.2 [HIGH] daemon restartable 미설계 — single-fault 가정의 한계 (사용자 패턴 분석 2)

**관측**:
- `CollectorDaemon.run()` finally 블록이 WalIngester close
- `_run_with_restart` 가 **같은 daemon 인스턴스 재사용** → 두 번째 attempt 부터 closed ingester write 시도 → 즉시 RuntimeError
- attempt=102까지 누적 재시도 (지수 백오프 패턴) — 단일 fault 가정 시 backoff 가 회복 기회 제공한다는 설계 철학이 closed-resource case 에서 무력화

**근본 원인 분석**:

**daemon restartable design 부재 = HIGH risk 패턴**:

근거:
1. **CollectorDaemon `__init__`** 에서 WalIngester 인스턴스 생성 — 생성 비용을 daemon 생명주기에 1회 한정
2. **`run()` finally** 가 close — restart 시 재생성 책임이 어디에도 박제 안 됨
3. **`_run_with_restart`** 가 daemon 인스턴스 재사용 — restart 의미가 "daemon 재사용 + run() 재호출" 로 굳어짐
4. **테스트 부재** — restart cycle (run → close → run again) 검증 케이스 없음. 16 pytest 가 모두 single-run 가정

**의미**:
- Fix 1 같은 single fault 가 production trigger 시 backoff retry 가 회복 기회 제공해야 하나, daemon restart 자체가 깨짐 → **fault 1개가 fault 102개로 증폭**
- 향후 다른 transient fault (네트워크 단절, exchange 장애) 시 동일 증폭 risk
- 현재 fix 는 `_build_ingesters()` 추출 + closed 감지 후 재생성 — **근본 fix 는 daemon 의 restartable lifecycle 명시** (e.g. `__aenter__/__aexit__` context manager + factory 함수로 daemon 매 회 신규 인스턴스)

**평가**:
- **§4.2 ADR 후보 발의** — daemon restartable lifecycle 표준 + restart cycle 테스트 의무화
- 임계 충족: 본 사례 1건 + 향후 transient fault 잠재 = **즉시 박제 권장**

### 3.3 [MEDIUM] Docker 빌드 인프라 의존성 미박제 — 로컬 재현성 부재 (사용자 패턴 분석 3)

**관측**:
- 기존 Dockerfile 이 git+https private deps (mctrader-market 패밀리) + GITHUB_TOKEN BuildKit secret 의존
- 로컬 빌드 시 token 없으면 `--no-cache` 빌드 불가 — RETRO-MCT-119-runtime-fix §3.3 와 동일 root cause family
- `mctrader-data` 스크립트 entrypoint 가 deps stage 에 존재하지 않음 (uv 설치 후 미생성) → runner stage `COPY --from=deps /usr/local/bin/mctrader-data` 실패

**근본 원인 분석**:

**Docker 빌드 의존성 + entrypoint 패턴 미박제**:

근거:
1. **MCT-101 (mctrader-web Docker-first design) 시점에 6-repo 빌드 표준 미박제** — 각 repo 가 개별 Dockerfile 작성, GitHub git-dep + BuildKit secret 패턴 ad-hoc 채택
2. **로컬 빌드 재현성 검증 누락** — CI 에서는 PAT 보유 가능, 개발자 머신에서는 `gh auth token` 또는 1Password 의존 → 문서화 안 됨
3. **entrypoint 검증 누락** — `mctrader-data` 스크립트가 어느 stage 에 생성되는지 명시 안 됨. uv 의 `--no-cache` 가 console_scripts 생성 step skip 가능성
4. **vendor wheel 패턴 부재** — mctrader-market 패밀리가 자주 변경되지 않음에도 매 빌드마다 git resolve 비용 지불

**의미**:
- 6-repo 컨테이너의 production rebuild 신뢰성 부재 — RETRO-MCT-119-runtime-fix §3.3 와 동일 risk
- 본 retro 의 vendor wheel 패턴이 mctrader-data 단일 적용 — 나머지 5 repo (engine/web/market 패밀리/hub) 미적용
- entrypoint 패턴 (`python -m <module>.cli`) 이 mctrader-data 만 채택 — 나머지 컨테이너 표준 미박제

**평가**:
- **§4.3 ADR 후보 발의** — Docker 빌드 표준 (vendor wheel + python -m entrypoint + 로컬 재현 절차) — RETRO-MCT-119-runtime-fix §4.3 (Docker build dependency 표준) 와 통합 박제 권장
- 임계 충족: 본 사례 1건 + RETRO-MCT-119-runtime-fix §3.3 1건 = **2건 누적, 즉시 박제 권장**

### 3.4 [LOW] 자동 테스트 surface 실패 — _emit_to_wal Upbit 경로 미커버

**관측**:
- MCT-121 §1.4 박제: `tests/test_adapters.py` 6 unit + `tests/integration/test_upbit_collector.py` (WAL 기록 확인) — 본 fix 의 `_emit_to_wal` 5곳 `event.exchange` 접근을 surface 못 함
- 16 pytest 회귀 0 — 본 fix 는 자동 lane 외부에서 진단·적용

**근본 원인 분석**:
- `tests/test_adapters.py` 는 dispatch 검증 (kind="transaction" 등) 만 — 이벤트 필드 접근 미검증
- `tests/integration/test_upbit_collector.py` 는 WAL 기록 확인 — fixture 가 mock event 사용하거나 `_emit_to_wal` 5곳 중 일부만 커버 (사용자 보고 unconfirmed)
- `_run_with_restart` cycle test 부재 — Fix 2 도 자동 surface 불가

**의미**:
- 자동 테스트의 mock-heavy 패턴 + restart cycle 미검증 → **runtime defect 가 자동 lane 에서 invisible**
- RETRO-MCT-119-runtime-fix §3.4 (deployment-time defect 자동 lane 미커버) 와 동일 패턴 재발 — 본 retro 는 코드 결함 (Cat B) 인데도 동일 lane 에서 invisible

**평가**:
- §4.4 — `tests/integration/test_upbit_collector.py` 보강 + restart cycle 테스트 추가 권장
- RETRO-MCT-119-runtime-fix §4.4 의 "integration test Tier 3" 와 통합 권고

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH] ADR 신규 — exchange 이벤트 공통 protocol 정의

```
target_adr: ADR 신규 (mctrader-data adapter 계약) 또는 ADR-018 D? 패턴
amendment_type: artifact (이벤트 인터페이스 계약)
trigger: 본 retro §3.1 — collector._emit_to_wal 5곳 event.exchange 접근 시 UpbitTradeEvent 가 필드 미보유 → AttributeError. Bithumb/Upbit 별도 repo 진화로 인한 인터페이스 drift.
배경:
  - mctrader-market-bithumb / mctrader-market-upbit 이 별도 repo
  - 각 repo 의 이벤트 타입이 공통 base 인터페이스 없이 독립 정의
  - collector.py 가 두 exchange 이벤트를 통일 가정 (event.exchange/symbol/event_time)
  - MCT-121 통합 시 필드 호환성 audit 누락
문제:
  - 신규 exchange 추가 시마다 동일 drift 재발 risk
  - pyright 가 Union 타입의 attribute 접근 catch 못 함
  - production 첫 trigger 시 surface
제안 결정:
  a) exchange 이벤트 공통 Protocol 정의 — `ExchangeTradeEvent`, `ExchangeOrderbookEvent`, `ExchangeTickerEvent` (typing.Protocol) 에 공통 필드 (`exchange`, `symbol`, `event_time`) 명시
  b) 각 repo 의 이벤트 타입은 Protocol 준수 의무 — runtime_checkable 또는 mypy plugin 검증
  c) collector.py 는 이벤트 필드 접근 시 Protocol 변수로 type-narrow — 또는 self._exchange 같은 daemon-scoped 변수 사용
  d) 신규 exchange 추가 시 PR 게이트로 Protocol 준수 검증
예상 결과:
  - 인터페이스 drift 사전 차단
  - pyright/mypy 가 catch 가능
  - 신규 exchange 통합 cost 감소
관련:
  - ADR-018 defensive coding patterns
  - MCT-121 Upbit 통합
보류 사유:
  - 본 사례 1건 + 향후 exchange 추가 잠재 = 즉시 박제 권장
```

### 4.2 [HIGH] ADR 신규 — daemon restartable lifecycle 표준

```
target_adr: ADR 신규 (mctrader-data daemon 패턴)
amendment_type: artifact + behavior (daemon lifecycle)
trigger: 본 retro §3.2 — CollectorDaemon._run_with_restart 가 closed WalIngester 보유 daemon 재사용 → RuntimeError 102회. single-fault 가정의 backoff retry 가 closed-resource case 에서 무력화.
배경:
  - CollectorDaemon `__init__` 에서 WalIngester 1회 생성
  - `run()` finally 가 close — restart 시 재생성 책임 미박제
  - `_run_with_restart` 의 restart 의미가 "daemon 재사용 + run() 재호출" 로 굳어짐
  - 16 pytest 가 모두 single-run 가정
문제:
  - 단일 fault 가 daemon 무한 fault 로 증폭
  - 향후 transient fault (네트워크, exchange 장애) 시 동일 증폭 risk
  - restart cycle 검증 부재
제안 결정:
  a) daemon 의 restartable lifecycle 명시 — `__aenter__/__aexit__` context manager 또는 factory 함수로 매 restart 시 신규 인스턴스
  b) 또는 본 fix 패턴 (`_build_ingesters()` factory + closed 감지 재생성) 표준화
  c) restart cycle 테스트 의무화 — `test_daemon_restart_after_close.py` 같은 케이스
  d) WalIngester 같은 closeable resource 의 lifecycle 을 daemon scope 보다 짧게 (per-run scope) 박제
예상 결과:
  - transient fault 시 backoff retry 정상 작동
  - daemon 재시작 신뢰성 보장
  - restart cycle 자동 검증
관련:
  - ADR-018 defensive coding patterns
  - MCT-121 Upbit collector
보류 사유:
  - 본 사례 1건 + 향후 transient fault 잠재 = 즉시 박제 권장
```

### 4.3 [HIGH] ADR 통합 — Docker 빌드 표준 (vendor wheel + python -m entrypoint + 로컬 재현)

```
target_adr: RETRO-MCT-119-runtime-fix §4.3 (Docker build dependency 표준) 와 통합 — ADR 신규 또는 ADR-016 amendment
amendment_type: behavior + artifact (build pipeline)
trigger: 본 retro §3.3 — mctrader-data Dockerfile 의 git+https private deps + GITHUB_TOKEN BuildKit secret 의존 → 로컬 빌드 재현 불가, mctrader-data 스크립트 entrypoint deps stage 미생성. RETRO-MCT-119-runtime-fix §3.3 와 동일 root cause family.
배경:
  - 6-repo 의 cross-repo dependency 가 git+https 패턴
  - MCT-101 시점 6-repo 빌드 표준 미박제
  - mctrader-market 패밀리가 자주 변경되지 않음에도 매 빌드 git resolve 비용
  - console_scripts entrypoint 의 deps stage 생성 여부 검증 누락
문제:
  - 로컬 빌드 재현성 부재 (token 없으면 --no-cache 불가)
  - production rebuild 신뢰성 부재
  - 6-repo 컨테이너 빌드 패턴 ad-hoc — drift risk
제안 결정 (RETRO-MCT-119-runtime-fix §4.3 통합):
  a) **vendor wheel 패턴 표준화 (1순위, 본 retro 채택)**:
     - 각 repo 의 cross-repo deps 를 vendor/*.whl 로 pre-build (mctrader-market 패밀리 등)
     - vendor/.gitignore 의 *.whl 허용
     - Dockerfile: `pip install --no-deps ./vendor/*.whl` + sed 로 git+https 제거 + uv 가 PyPI deps 만 해석
  b) **internal PyPI mirror (2순위, 장기)**:
     - devpi/MinIO+pip-index 인프라 구축
     - vendor 디렉토리 → PyPI 인덱스 경유로 마이그레이션
  c) **BuildKit secret mount (3순위, 비권장)**:
     - 본 retro 가 폐지 결정 — 로컬 재현성 부재
  d) **entrypoint 표준**: `python -m <module>.cli` 일관 채택 (console_scripts 의 stage 의존성 우회)
  e) **로컬 빌드 재현 절차**: README 또는 hub 의 build-runbook.md 박제 — vendor wheel 생성 명령 + 빌드 검증
예상 결과:
  - 6-repo 컨테이너 production rebuild 항상 가능
  - GitHub token 의존성 0
  - entrypoint 패턴 일관
  - 로컬 빌드 재현성 100%
관련:
  - ADR-016 containerization
  - MCT-98 dockerization Epic
  - RETRO-MCT-119-runtime-fix §3.3, §4.3
  - MCT-101 mctrader-web Docker-first design
보류 사유:
  - 본 사례 + RETRO-MCT-119-runtime-fix §3.3 = 2건 누적 → 즉시 박제 권장
  - 6-repo 전체 vendor wheel 마이그레이션 Story 동반 발의 (Phase 후속)
```

### 4.4 [MEDIUM] integration test 보강 — _emit_to_wal Upbit 경로 + restart cycle 커버리지

```
target: mctrader-data tests/ 보강 또는 RETRO-MCT-119-runtime-fix §4.4 통합
amendment_type: artifact (테스트 인프라)
trigger: 본 retro §3.4 — 16 pytest + 6 adapters unit + integration upbit collector 가 _emit_to_wal Upbit 경로 + daemon restart cycle 미커버
배경:
  - tests/test_adapters.py: dispatch 검증만 (필드 호환성 미검증)
  - tests/integration/test_upbit_collector.py: WAL 기록 확인 (5곳 중 일부만 커버)
  - _run_with_restart cycle test 부재
문제:
  - runtime defect 가 자동 lane 에서 invisible (Cat B 인데도)
  - daemon restart 신뢰성 자동 검증 부재
제안 결정:
  a) tests/integration/test_upbit_collector.py 보강 — _emit_to_wal 5곳 모두 통과하는 mock event 시나리오
  b) tests/integration/test_daemon_restart.py 신규 — run → close → run again 검증
  c) RETRO-MCT-119-runtime-fix §4.4 (integration test Tier 3) 와 통합 — 실제 WAL filesystem 기동 + collector daemon E2E
예상 결과:
  - runtime defect 자동 lane surface
  - daemon restart 신뢰성 자동 보장
보류 사유:
  - 본 사례 1건 + RETRO-MCT-119-runtime-fix §4.4 = 2건 누적 → 즉시 보강 권장
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 13+ Story sweep — 신기록 갱신

본 세션 (2026-05-09 ~ 2026-05-10) 누적:
- MCT-112 ~ MCT-117 (audit sweep 6 Story)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2)
- MCT-121 (Upbit 통합) ← 본 retro 의 fix 대상
- MCT-122/123 (관측됨)
- MCT-124 (signal-collector)
- MCT-119 web overhaul (PR #35)
- MCT-119 runtime fix
- **MCT-121 runtime fix (본 retro)**

→ **13+ Story sweep**. RETRO-MCT-119-runtime-fix §5.1 의 "12+" 갱신. **다중 repo (data + web + hub) 를 가로지르는 runtime fix lane 안정 작동** 실증.

### 5.2 신규 결함 카테고리 surface — Cat F (cascading defect)

기존 Cat A/B/C/D/E (RETRO-MCT-119-runtime-fix §5.2) 외 본 retro 에서 신규 surface:

| 신규 Cat | 정의 | 본 사례 | 평가 |
|---|---|---|---|
| **Cat F — cascading defect** | Cat B 같은 primary fault surface 후 부수 발견된 인접 결함. primary fix 만으로는 회복 불가 | Fix 2 (`WalIngester closed restart loop`) | 신규 카테고리 — RETRO 누적 표준 갱신 권고 |

→ Cat F 의 정성 의미: **single-fault 가정의 회복 메커니즘 (backoff, retry, restart) 이 multi-fault 노출 시 무력화** 패턴. 진단 시 "primary fault fix 후 회복 검증 필수" 게이트 박제 권장. 본 retro §2.1 (cascading 진단) 이 Cat F 의 우수 사례.

### 5.3 인터페이스 drift 패턴 — multi-repo dependency family

RETRO-MCT-124-signal-collector §3 의 "외부 API 의존성 패턴 4건" + 본 retro §3.1 의 "exchange 이벤트 인터페이스 drift" 는 모두 **multi-repo dependency 의 인터페이스 계약 부재** 패턴 family. 공통 root cause:
- 각 repo 가 독립 진화하는 인터페이스 (외부 API or 내부 이벤트 타입)
- consumer 측이 통일 가정으로 통합
- pre-deploy 인터페이스 호환성 lint 부재

→ ADR 후보 §4.1 (exchange 이벤트 protocol) 은 RETRO-MCT-124 의 ADR 후보 (외부 API 의존성 패턴) 와 통합 박제 권장 — "multi-repo 인터페이스 계약 표준" Phase 후속.

### 5.4 Docker 빌드 인프라 fix 누적 2건 — 6-repo 마이그레이션 임계 충족

| Retro | Fix | 패턴 |
|---|---|---|
| RETRO-MCT-119-runtime-fix §3.3 | mctrader-web bind mount 임시 조치 | escape hatch (Cat E) |
| RETRO-MCT-121 §3.3 (본) | mctrader-data vendor wheel 정식 도입 | proper fix (Cat E 해결) |

→ 2건 누적 + 6-repo 잠재 = **6-repo Docker 빌드 표준 마이그레이션 Story 즉시 발의 권장** (§6 제안 3). vendor wheel 패턴이 mctrader-data 에서 검증됐으므로 나머지 5 repo (engine/web/market-bithumb/market-upbit/hub) 일괄 적용 가능.

### 5.5 ADR 후보 누적 — N=15+ (1주 관측 sprint 임계 초과 지속)

RETRO-MCT-119-runtime-fix §5.4 의 "12+ 후보" 에서 본 retro 추가:
- **ADR 신규 (exchange 이벤트 공통 protocol — 본 §4.1)**
- **ADR 신규 (daemon restartable lifecycle — 본 §4.2)**
- **ADR 통합 (Docker 빌드 표준 vendor wheel — 본 §4.3 + RETRO-MCT-119-runtime-fix §4.3)**
- **ADR amendment (integration test Tier 3 — 본 §4.4 + RETRO-MCT-119-runtime-fix §4.4)**

→ **15+ 후보**. 1주 관측 임계 (2026-05-16) 충족 항목 즉시 박제 sprint 강력 권장. **다음 세션 시작 시 ArchitectAgent dispatch 1순위 (RETRO-MCT-119-runtime-fix §5.4 권고 누적)**.

### 5.6 자동 테스트 surface 실패 — 2 retro 연속 surface

| Retro | 자동 lane 미커버 결함 | 카테고리 |
|---|---|---|
| RETRO-MCT-119-runtime-fix §3.4 | `.env` 부재 + FK 순서 | Cat D (deployment-time) + Cat B (FK 순서) |
| RETRO-MCT-121 §3.4 (본) | `event.exchange` + restart cycle | Cat B + Cat F |

→ **자동 테스트가 production-trigger 결함의 핵심 surface 책임 미수행**. 테스트의 mock-heavy 패턴이 runtime defect 의 실제 코드 경로 미커버. integration test Tier 3 도입 (§4.4) 필수.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **ADR 박제 sprint 즉시 실행 (15+ 후보)** (§5.5) — 본 retro §4.1 (exchange 이벤트 protocol) + §4.2 (daemon restartable lifecycle) + §4.3 (Docker 빌드 표준 통합) 모두 root cause 명확 → **즉시 박제 권장**. 다음 세션 시작 시 ArchitectAgent dispatch 1순위. RETRO-MCT-117/119-120/119-web-test-overhaul/119-runtime-fix 누적 권고와 통합.

2. **mctrader-data 인터페이스·daemon 보강 Story 즉시 발의** (§3.1 + §3.2 + §4.1 + §4.2) — (a) exchange 이벤트 Protocol 정의 + 6-repo 적용 + (b) CollectorDaemon restartable lifecycle 리팩터 + restart cycle 테스트. 가칭 MCT-128 또는 MCT-129. 본 retro 의 fix 는 surface 우회 — root fix 별도 Story.

3. **6-repo Docker 빌드 표준 마이그레이션 Story 즉시 발의** (§3.3 + §4.3 + §5.4) — vendor wheel 패턴 + python -m entrypoint + 로컬 재현 runbook 박제. 6-repo 컨테이너 production rebuild 보장. 가칭 MCT-130 또는 ADR-016 amendment 1 + 후속 Phase Story. RETRO-MCT-119-runtime-fix §6 제안 3 와 통합.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Fix 1 root cause 진단 (`UpbitTradeEvent.exchange` AttributeError) | ~15% |
| Fix 1 적용 (5곳 `event.exchange` → `self._exchange`) | ~5% |
| Fix 2 cascading 진단 (`WalIngester closed restart loop`) | ~20% |
| Fix 2 적용 (`_build_ingesters()` 추출 + closed 감지 재생성) | ~10% |
| Fix 3 Docker 빌드 진단 (`mctrader-data: not found` → `No module named`) | ~15% |
| Fix 3 적용 (vendor wheel + sed + python -m entrypoint + vendor/*.whl 3개 빌드) | ~15% |
| 사용자 수동 검증 (upbit-ingester 20 심볼 + WAL 80개+) | ~5% |
| 본 retro 작성 + Story §11 갱신 | ~15% |

→ **Fix 진단 비용 50%, 적용 비용 30%, 검증·문서화 20%**. RETRO-MCT-119-runtime-fix 의 "진단 55% / 적용 25% / 문서화 20%" 와 유사 — runtime fix + 인프라 fix 합본의 진단 비용 비중 과반 패턴 재현. **§5.6 의 자동 테스트 한계** 실증 (자동 surface 됐다면 진단 비중 감소했을 것).

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-016**: Containerization — 본 retro §4.3 (Docker 빌드 표준 vendor wheel) amendment 후보
- **ADR-018**: Defensive coding patterns — 본 retro §4.1 (exchange 이벤트 protocol) + §4.2 (daemon restartable lifecycle) D? 후보
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch 10번째 same-session 사례
- **ADR-011**: CI standard — 본 retro §4.4 integration test Tier 3 amendment 후보 (RETRO-MCT-119-runtime-fix §4.4 통합)
- **MEMORY** `feedback_admin_merge_autonomy.md`: `32fe512` push 자율 (10번째 same-session)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_codeforge_upgrade_process.md`: vendor wheel 패턴이 codeforge 영역 외이지만 6-repo 표준 박제 시 동일 lane
- **MEMORY** `project_dockerization_epic.md`: MCT-98 #120 dockerization Epic 완료 후 surface 된 후속 결함 — Phase 후속 Story 트리거 (RETRO-MCT-119-runtime-fix §8 누적)
- **선행 retro**:
  - `RETRO-MCT-119-runtime-fix.md` (§3.3 Docker GitHub-dep rebuild 불가 → 본 retro §3.3 가 vendor wheel 로 정면 해결, §4.3 통합)
  - `RETRO-MCT-124-signal-collector.md` (외부 API 의존성 패턴 4건 → 본 retro §3.1 multi-repo 인터페이스 drift family)
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준 → 본 retro §5.2 Cat F 신규 카테고리 추가)
  - `RETRO-MCT-119-web-test-overhaul.md` (§5.5 2-tier 테스트 → 본 retro §4.4 integration test 보강 통합)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-121.md` §11 (본 retro pointer 박제 권고) — 별도 commit 또는 본 retro 와 동일 commit 으로 처리. 박제 형식:

```
## §11 회고
- runtime fix 1차 (배포 후 발견): RETRO-MCT-121-upbit-collector-runtime-fix.md
  - Fix 1: UpbitTradeEvent.exchange AttributeError (5곳 self._exchange 치환)
  - Fix 2: WalIngester closed restart loop (_build_ingesters() 추출)
  - Fix 3: Dockerfile vendor wheel 패턴 도입 (Docker 빌드 인프라)
  - commit: mctrader-data 32fe512
```

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up

- **본 fix 자체 follow-up 없음** — Fix 1+2+3 모두 현재 운영 가능 상태 (upbit-ingester 20 심볼 정상, Docker rebuild 성공)
- 다만 §4.3 의 vendor wheel 패턴은 **mctrader-data 단일 적용** — 6-repo 일괄 마이그레이션 Story 트리거 필요

### 10.2 ADR 박제 (즉시 검토)

- **ADR 신규 (§4.1)** — exchange 이벤트 공통 protocol — root cause 명확, 즉시 박제 권장
- **ADR 신규 (§4.2)** — daemon restartable lifecycle 표준 — root cause 명확, 즉시 박제 권장
- **ADR 통합 (§4.3)** — Docker 빌드 표준 (vendor wheel + python -m entrypoint + 로컬 재현) — RETRO-MCT-119-runtime-fix §4.3 와 통합, 2건 누적 즉시 박제
- ADR-011 amendment (§4.4) — integration test 보강 — 1주 관측 후 통합

### 10.3 후속 Story 발의

- **mctrader-data 인터페이스·daemon 보강 Story** (가칭 MCT-128/129) — §6 제안 2
- **6-repo Docker 빌드 표준 마이그레이션 Story** (가칭 MCT-130) — §6 제안 3
- **mctrader-data integration test 보강 Story** (가칭 MCT-131) — §4.4 (RETRO-MCT-119-runtime-fix §4.4 통합)

### 10.4 Upbit 통합 후속 Story 트리거 (MCT-121 §11 누적)

- Upbit USDT 시장 확장 (현재 KRW 만)
- Upbit orderbook depth WAL 활성 (현재 미생성 확인)
- Upbit ↔ Bithumb cross-exchange arbitrage 데이터 분석

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
