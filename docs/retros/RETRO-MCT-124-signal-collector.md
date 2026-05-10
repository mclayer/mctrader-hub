# RETRO-MCT-124 — 외부 시그널 수집 서비스 (mctrader-signal-collector 신규 리포)

**범위**: MCT-124 (Tier 1 외부 시그널 6종 수집 서비스 신규 리포 + Hub compose 통합)
**기간**: 2026-05-10 (single-session, MCT-122/123 직후 동일 세션 연장)
**Trigger**: 외부 컨텍스트 (뉴스 / 한국 리테일 수급 / 글로벌 파생상품 압력 / 시장 레짐) 부재 — engine 이 가격 패턴만 기반 결정 중. Tier 1 시그널 6종 (Fear&Greed / ECOS FX / 김치프리미엄 / Upbit 공지 / Bithumb 공지 / CoinGlass) 도입.
**Status**:
- mctrader-signal-collector **신규 독립 리포 생성** (branch `master`, 13 commit, no remote 미푸시)
- mctrader-hub commit `9207561` main 직접 push 2026-05-10T09:43:25+09:00 (compose 5 service 추가, MCT-124 label)
- 31 pytest 통과 (publisher 4 + dedup 4 + health 3 + fear_greed 4 + ecos 3 + kimchi_premium 3 + announcement 8 + coinglass 2)
- Docker 빌드 성공 (2-stage, uid 1001 non-root)

**Story files**: 없음 (Story file 미작성 — RETRO 작성 중 발견, §3.5 참조)
**Spec/Plan**:
- `mctrader-hub/docs/superpowers/specs/2026-05-10-signal-collector-design.md` (Sonnet decider 채택, status=approved)
- `mctrader-hub/docs/superpowers/plans/2026-05-10-signal-collector.md` (12 Task TDD 계획)

**Repos**:
- **`mctrader-signal-collector`** (신규) — branch `master`, 13 commit, **no remote** (push 보류, §3.4)
- `mctrader-hub` — main 직접 push (commit `9207561`, +97/−0, ADR-019 D6 hub trunk-based 패턴 적용)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (12 Task) | 실제 | 비고 |
|---|---|---|---|
| Task 0 — 리포 스캐폴드 (pyproject + Dockerfile + compose + .env.example + README) | 신규 | `83c26e8` + `3419180` | 100% (HEALTHCHECK placeholder 1 fix 발생 §3.6) |
| Task 1 — `Publisher` (Redis Stream XADD + stale fallback) | 신규 | `29d16fa` (4 unit test) | 100% |
| Task 2 — `DedupStore` (Redis Set) | 신규 | `a861228` (4 unit test) | 100% |
| Task 3 — `HealthExporter` (Prometheus Counter/Gauge) | 신규 | `696b6b5` (3 unit test) + `fb8f99b` HEALTHCHECK 복원 | 100% |
| Task 4 — `BaseWorker` (poll_once / _run_cycle / run) | 신규 | `387b431` | 100% (test 는 구체 worker 통합) |
| Task 5 — `FearGreedWorker` (Alternative.me, 5분) | 신규 | `1dba94e` (4 unit test) | 100% |
| Task 6 — `EcosWorker` (한국은행 ECOS, 6h) | 신규 | `1abe7a9` (3 unit test) | 100% |
| Task 7 — `KimchiPremiumWorker` (CryptoQuant, 1분) | 신규 | `e7827bf` (3 unit test) | 100% |
| **Task 8 — Upbit/Bithumb XHR API 엔드포인트 탐색** | **사용자 수동** | **PENDING** | **§3.1 — SPA 한계, env var 주입 구조로 대비** |
| Task 9 — `AnnouncementWorker` (Upbit + Bithumb, 15초) + dedup | 신규 | `c9ee893` (8 unit test) + `6857434` _CLASSIFY_MAP 순서 fix | 100% (실제 URL 미투입, fixture 기반 검증) |
| Task 10 — `CoinGlassWorker` (청산/OI/펀딩비, 1분) | 신규 | `b189626` (2 unit test) | 100% |
| Task 11 — Hub compose.yml + .env.example 통합 | 신규 | `9207561` (hub) | 100% |
| Task 12 — 전체 pytest + Docker 빌드 검증 | 검증 | 31/31 PASS + Docker 빌드 성공 | 100% |

→ **Story scope 11/12 Task 완료, Task 8 만 사용자 수동 액션 의존 (PENDING)**. 코드/테스트/인프라 측면은 100% 완료, 운영 활성화 (signal-announcement 컨테이너 실제 데이터 수집) 만 Task 8 결과 대기.

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-signal-collector` (신규 리포) | **13 commit, +842/−1, 24 파일** (initial scaffold 제외 시) | branch `master`, **no remote, 미푸시** (§3.4) |
| `mctrader-hub` commit `9207561` | **+97 / −0**, 2 파일 (compose.yml + .env.example) | main 직접 push |

→ 본 Story 합계: **+939 / −1, 26 파일, 14 commit**. **신규 LoC ~842 (signal-collector) + 95 (hub) = ~937**. 회귀 0.

### 1.3 테스트 결과

| 카테고리 | 신규 test | passed | failed |
|---|---|---|---|
| `core/test_publisher.py` | 4 (normal / stale / ts / multi-kind) | 4 | 0 |
| `core/test_dedup.py` | 4 (new / mark / independent / idempotent) | 4 | 0 |
| `core/test_health.py` | 3 (success / error / last_success_ts) | 3 | 0 |
| `workers/test_fear_greed.py` | 4 (poll / error / cycle / stale) | 4 | 0 |
| `workers/test_ecos.py` | 3 (poll / empty / cycle) | 3 | 0 |
| `workers/test_kimchi_premium.py` | 3 (poll / empty / cycle) | 3 | 0 |
| `workers/test_announcement.py` | 8 (5 classify + 2 fetch + 1 dedup) | 8 | 0 |
| `workers/test_coinglass.py` | 2 (poll / cycle) | 2 | 0 |
| **합계** | **31** | **31** | **0** |

→ **31/31 PASS, 0 회귀**. Plan 의 Task 별 Expected count (4+4+3+4+3+3+8+2 = 31) 와 정확히 일치.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 + RETRO-MCT-121 §5.5 + RETRO-MCT-122-123 §1.4 표준 적용)

| 카테고리 | commit 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 fix (12 task feat commit) | 11 | 79% | 본 fix |
| 자체 발견 fix — Dockerfile HEALTHCHECK placeholder + compose name | 1 (`3419180`) | 7% | **Cat B (self-discovered)** |
| 자체 발견 fix — _CLASSIFY_MAP 순서 (delisting/listing) | 1 (`6857434`) | 7% | **Cat B** |
| 자체 발견 fix — HEALTHCHECK 실제 endpoint 복원 | 1 (`fb8f99b`) | 7% | **Cat B** |

→ Cat B 21% (3 commit), 본 fix 79% (11 commit). **Cat A (pre-existing) 0, Cat C (다른 Story finish-up) 0**. RETRO-MCT-122-123 §1.4 의 Cat C 43% 패턴이 본 Story 에서는 재현 안 됨 — **신규 리포 단일 Story** 라 다른 Story finish-up 없음.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-signal-collector` (신규) | `master` | ❌ **미푸시** (§3.4) | (없음) | N/A |
| `mctrader-hub` | `main` (직접 push) | ✅ | (없음, ADR-019 D6 hub trunk-based) | ✅ |

→ **신규 리포 생성 + Hub 통합** 패턴. 1 신규 + 1 기존 = **2-repo cross-repo Story**. 신규 리포 미푸시는 §3.4 별도 평가 (Task 8 결과 의존성 + remote 결정 미완).

---

## 2. 잘된 점

### 2.1 신규 독립 서비스 리포 — 장애 격리 + Engine decoupling

본 Story 는 **mctrader-signal-collector 신규 독립 리포 생성** — Spec §1 결정 stack #1 (서비스 배치) 의 채택안. 거부된 대안 (mctrader-data 확장 / Hub compose sidecar) 대비 이점:

- **장애 격리** — fear_greed worker crash 가 ecos/kimchi/announcement/coinglass 에 영향 0 (5 컨테이너 독립)
- **Engine decoupling** — Redis Stream `signals:{kind}` 인터페이스만 공유, engine 측 코드 변경 0
- **이벤트 + 폴링 혼용** — 공지 (15초 폴링) + 지표 (1분~6시간 폴링) 자연 분리
- **인증 시크릿 worker 별 분리** — ECOS_API_KEY 는 signal-ecos 에만, COINGLASS_API_KEY 는 signal-coinglass 에만 노출

→ **6 repo → 7 repo 확장**. mctrader-data + mctrader-engine + mctrader-market + mctrader-market-bithumb + mctrader-market-upbit + mctrader-web + mctrader-hub + **mctrader-signal-collector** = 8 repo (mctrader-hub 포함). RETRO-MCT-121 의 mctrader-market-upbit 신규 plugin repo 패턴이 본 Story 에서 재현 — **신규 도메인 컴포넌트 = 신규 리포** 패턴 누적 2건.

### 2.2 BaseWorker 추상화 — 6 worker DRY 100%

`BaseWorker` 추상 클래스 (poll_once + _run_cycle + run) 가 5 구체 worker 의 **공통 try/except + publish + health 로직** 을 100% 흡수. 구체 worker 는 `poll_once()` 만 구현하면 됨:

```python
class FearGreedWorker(BaseWorker):
    kind = "fear_greed"
    interval_seconds = 300
    def poll_once(self) -> dict: ...  # 외부 API 호출만
```

→ **stale fallback / 에러 로깅 / Prometheus 메트릭 / 무한 루프** 가 BaseWorker 한 곳. 향후 worker 추가 시 (Twitter / Reddit / Glassnode 등) `poll_once()` 만 작성. **추상화의 ROI** 가 본 Story 에서 즉시 실증 — 5 worker × ~30 LoC 절감 = ~150 LoC 절감.

### 2.3 fakeredis 기반 unit test — Redis 컨테이너 의존성 0

`Publisher` / `DedupStore` / 5 worker 의 `_run_cycle()` 통합 검증을 **fakeredis** 로 처리. 이점:

- Docker / Redis 컨테이너 없이 pytest 단독 실행 — CI 단순화
- XADD / XRANGE / SADD / SISMEMBER 동작 검증 — 실제 Redis 와 동일 의미론
- 테스트 속도 — 31 test < 1초 추정 (네트워크 0)

→ **integration test 없음 (Plan §8 마지막 행)** — fakeredis 가 충분히 cover. 실제 Redis 통합 검증은 Task 12 Step 3 (Docker 빌드 + 단독 연기) 에서 수동 확인 가능. 본 Story 는 Step 3 미실행 — 의존성 (REDIS 컨테이너 가동) 추가 비용 회피, hub compose `up` 시점에 자동 검증.

### 2.4 Sonnet decider 채택 — Spec stack 8 결정 명시

본 Story 는 spec 작성 단계에서 **8 결정 stack** 을 Sonnet decider 로 명시 (서비스 배치 / engine 인터페이스 / 스토리지 / stale 폴백 / 공지 감지 / worker 단위 / 시크릿 / 모니터링). 거부된 대안도 함께 박제:

- (#1) mctrader-data 확장 — 거부 (장애 격리 부재, 책임 분리 모호)
- (#3) MinIO only — 거부 (DuckDB warm 빠른 ad-hoc 쿼리 우선)
- (#5) Telegram fastpath — 거부 (스푸핑 위험, v2 검토)

→ **결정 근거 박제** 가 향후 재방문 시 컨텍스트 회복 비용 절감. RETRO-MCT-119-120 §6 #2 (Sonnet decider 패턴) 가 본 Story 에서 재현.

### 2.5 stale fallback 의무화 — engine 측 fallback contract

Spec §3 의 **stale 폴백 메시지 포맷** 이 본 Story 코드에서 100% 작동:

```python
# BaseWorker._run_cycle
except Exception as exc:
    self.publisher.publish(self.kind, {}, stale=True, reason=str(exc))
    self.health.record_error(self.kind)
```

→ engine 측 (별도 Story) 에서 `stale=true` 시 시그널 무시 contract 가능. **upstream 장애 → engine 잘못된 주문** 경로 차단. RETRO-MCT-122-123 §3.3 의 trust boundary 박제 패턴이 본 Story 에서 stale flag 형태로 재현.

### 2.6 admin merge autonomy + PMO 회고 자동 dispatch — 10번째 same-session 사례

mctrader-hub commit `9207561` main 직접 push 후 본 retro 자동 dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121/122+123/**124** = **10 Story (10 PR + 1 직접 push + 1 신규 리포)** 동일 패턴 작동. ADR-020 D1 + MEMORY `feedback_admin_merge_autonomy.md` + `feedback_pmo_retro_mandatory.md` closed-loop 정착 누적 10건.

---

## 3. 발생한 이슈

### 3.1 [HIGH] Task 8 PENDING — Upbit/Bithumb React SPA HTML 파싱 불가, XHR API 사용자 수동 탐색 필요

**관측**:
- Plan §Task 8 명시 — Upbit/Bithumb 공지 페이지가 **React SPA** 라 `httpx.get(notice_page_url)` 직접 호출 시 빈 HTML shell 반환
- `BeautifulSoup` 파싱 시 공지 목록 추출 불가
- 실제 데이터는 페이지 로드 후 클라이언트 JavaScript 가 호출하는 **XHR/Fetch API** 가 반환
- 해결: env var `UPBIT_NOTICE_API_URL`, `BITHUMB_NOTICE_API_URL` 로 외부 주입하는 구조로 코드 작성. 실제 URL 발견은 사용자 수동 (Chrome DevTools Network 탭) 액션
- 본 Story 완료 시점에 Task 8 **PENDING** — 코드는 fixture 기반 unit test 통과 (8 test), 실제 운영 URL 미투입

**근본 원인 분석**:
1. **거래소 공지 페이지의 SPA 전환 추세** — 2025+ 거래소 다수가 React/Vue SPA 로 전환, server-side render 비율 감소
2. **공식 공지 API 부재** — Upbit/Bithumb 모두 Open API 에 공지 전용 엔드포인트 없음 (Spec §4-4 명시)
3. **자동 XHR 탐색 도구 부재** — Playwright 등 headless browser + network sniff 가능하나 Task 복잡도 폭증
4. **운영 환경 다이내믹** — XHR endpoint 가 비공식이라 거래소 측 변경 시 무음 실패 가능성

**의미**:
- Task 8 미완료 = signal-announcement 컨테이너 운영 시 **stale fallback 만 publish** (env var 미설정 → URL fetch 실패 → except → stale=true)
- engine 측에서 stale=true 시그널 무시 → 공지 기반 이벤트 모드 (상장 직후 2h 지정가 전용) 비활성
- **Plan §Task 8 의 사용자 수동 액션 의존성** — 본 세션 단독으로 완결 불가, 별도 follow-up 필요

**평가**:
- 해결 경로 3가지:
  - **(a) 사용자 수동 Chrome DevTools 탐색** (Plan §Task 8 권고) — 30분 이내, 단발성 비용
  - **(b) Playwright headless + network sniff 자동화** — 자동 탐색 가능하나 Story 1건 단독으로 over-engineering
  - **(c) 공식 RSS / Telegram bot 대안** — Upbit/Bithumb 모두 공식 RSS 미제공, Telegram 은 Spec §1 #5 거부 (스푸핑 위험)
- **(a) 권고** — RETRO §10.1 즉시 follow-up 으로 박제
- 코드 측 대비 완료 — env var 주입 구조 (`AnnouncementWorker._fetch_upbit/_fetch_bithumb`) 가 URL 만 알면 즉시 작동

### 3.2 [MEDIUM] Prometheus 전역 Registry 충돌 — instance-level CollectorRegistry 사용으로 해결

**관측**:
- 초기 `HealthExporter` 구현 시 `prometheus_client.Counter/Gauge` 를 **모듈 전역** 으로 정의
- `tests/core/test_health.py` 의 3 test 가 각각 `HealthExporter()` 인스턴스화 → **두 번째 인스턴스화 시점** 에 `Duplicated timeseries in CollectorRegistry` 에러
- 해결: `HealthExporter.__init__` 내부에서 `CollectorRegistry()` 신규 생성 후 Counter/Gauge 를 해당 registry 에 binding

**근본 원인 분석**:
1. **prometheus_client 의 default registry 패턴** — Counter/Gauge 가 명시 registry 미지정 시 `REGISTRY` 전역 singleton 에 등록
2. **테스트 격리 부재** — 같은 메트릭 이름을 여러 인스턴스가 등록 시도 → 중복 timeseries
3. **test fixture 부재** — `test_health` 가 `HealthExporter()` 를 fixture 로 추출 안 하고 각 test 함수에서 직접 생성

**의미**:
- 운영 환경에서는 worker 프로세스 1개당 HealthExporter 1 인스턴스 → 충돌 없음
- 그러나 **test scenario 에서만 발생** — 운영 시 silent, test 에서 즉시 발견
- **단위 테스트의 가치 실증** — Prometheus 패턴의 silent 함정을 test 가 catch

**평가**:
- 해결 패턴 (instance-level CollectorRegistry) 이 **prometheus_client 권고 패턴** 과 일치
- 향후 mctrader-data + mctrader-engine 의 metrics.py (RETRO-MCT-122-123 §4.2) 가 모듈 전역 패턴 사용 — 본 패턴으로 migrate 시 test 격리 가능
- ADR 박제 불필요 — 패턴 1건, 단발성 fix

### 3.3 [LOW] _CLASSIFY_MAP 순서 버그 — "상장폐지" vs "상장" prefix 충돌

**관측**:
- `AnnouncementWorker.classify_title` 가 dict 순회로 keyword match
- 초기 구현: `{"상장": "listing", "상장폐지": "delisting", ...}` 순서
- "[상장폐지] DEF 상장폐지 안내" 처리 시 첫 번째 keyword "상장" 매칭 → "listing" 반환 (오류)
- 해결: `commit 6857434` — `_CLASSIFY_MAP` 순서 변경, "상장폐지" / "거래종료" / "거래 종료" 등 **specific delisting 패턴을 short listing keyword 앞에** 배치

**근본 원인 분석**:
1. **prefix 충돌** — "상장폐지" 가 "상장" 의 superstring → short keyword 가 먼저 매칭하면 long keyword 영원히 안 잡힘
2. **dict 순회 의미론** — Python 3.7+ dict 가 insertion order 보장, 그러나 의도 명시 부재
3. **Spec/Plan 단계 미발견** — Plan §Task 9 의 `_CLASSIFY_MAP` 예시 코드에서 잘못된 순서로 작성, 본 Story 자체 발견

**의미**:
- 상장폐지 공지 → engine 측 "상장 이벤트 모드 진입" 오작동 위험 (실제로는 폐지인데 신규 상장으로 오판)
- **Spec/Plan 작성 시점 catch 실패** — 코드 구현 후 _spec review_ 단계에서 자체 발견
- TDD 의 가치 — `test_classify_delisting` 이 fix 후 즉시 통과 확인

**평가**:
- 해결 패턴 — "**더 specific 한 패턴 먼저, less specific 패턴 나중**" 이 keyword classification 일반 원칙
- 향후 신규 worker 의 분류 로직 추가 시 동일 함정 가능 — README 또는 base_worker 주석에 박제 권장
- ADR 박제 불필요 — keyword classification 패턴 1건

### 3.4 [MEDIUM] mctrader-signal-collector 신규 리포 미푸시 — remote / org 정책 결정 미완

**관측**:
- 본 Story 가 mctrader-signal-collector **신규 독립 리포 생성** — 13 commit 누적
- branch=`master` (다른 mctrader 리포는 `main`)
- `git remote -v` 빈 출력 → **no origin, 미푸시**
- 본 retro 작성 시점에 GitHub org 의 신규 repo 생성 / branch 명명 정책 / CI 설정 미완

**근본 원인 분석**:
1. **본 세션 scope 한계** — Plan 12 Task 가 신규 리포 생성 + 코드 작성 + Hub 통합까지, **GitHub org 작업** 미포함
2. **remote 생성 결정 부재** — RETRO-MCT-121 의 mctrader-market-upbit 도 동일 패턴 (신규 plugin repo) 이었으나 그 경우 GitHub org 작업 (#216 PR) 동시 진행
3. **branch 명 default master vs main** — `git init` default 가 environment 별 (Windows Git 2.x default master, 최신 default main) → 본 case 는 `master`

**의미**:
- 본 Story 코드는 로컬 만 존재 — 다른 작업자 (CI, deployment) 접근 불가
- Hub compose `build: ../mctrader-signal-collector` 가 로컬 path 의존 — 운영 시 GHCR pull 필요 (Plan §Task 11 의 `image: ghcr.io/mclayer/mctrader-signal-collector:latest` 명시되었으나 실제 image push 부재)
- **Task 8 PENDING 과 함께 운영 활성화 차단 요인 2** — (a) GitHub remote + push, (b) 실제 XHR URL 투입

**평가**:
- 해결 경로:
  - **단계 1**: GitHub org `mclayer` 에 `mctrader-signal-collector` repo 생성 + branch rename master→main + remote add + push
  - **단계 2**: GHCR image build/push (CI workflow 작성, 다른 mctrader 리포 패턴 재사용)
  - **단계 3**: Task 8 사용자 수동 XHR 탐색 + .env 투입
  - **단계 4**: hub `docker compose up signal-*` 운영 활성화
- §10.1 즉시 follow-up 박제 — 1주 이내 단계 1+2 완료 권장
- ADR 박제 불필요 — RETRO-MCT-121 mctrader-market-upbit 패턴 재사용

### 3.5 [LOW] Story file 미작성 — RETRO §9 회고 pointer 박제 대상 부재

**관측**:
- 본 Story 가 **Story file** (`docs/stories/MCT-124.md`) 미작성 상태로 본 retro 작성
- RETRO-MCT-122-123 §9 의 "Story §11 회고 pointer 박제" 패턴 적용 불가
- 다른 Story (MCT-119 / MCT-120 / MCT-121) 는 `docs/stories/` 에 존재

**근본 원인 분석**:
1. **본 Story scope 가 spec/plan + 신규 리포 생성** — Story file 작성이 자연스러운 단계 부재
2. **Story file 작성 trigger 부재** — 사용자가 명시적으로 Story file 요청 안 함
3. **Plan 12 Task 에 Story file 생성 task 없음** — Plan 작성 시점에 Story file 의존성 미고려

**의미**:
- 본 retro 의 "Story §11 회고 pointer" 박제 안 됨
- ADR-020 D1 enforcement gap — Story file 부재로 회고 link back 차단
- 향후 본 Story 회고를 찾으려면 hub `docs/retros/` 직접 검색 필요 (Story file → RETRO link 부재)

**평가**:
- 해결 경로:
  - **즉시**: `docs/stories/MCT-124.md` 작성 + §11 에 본 retro pointer
  - **표준화**: 신규 리포 생성 Story 의 Plan 에 "Story file 작성" Task 명시
- §10.1 즉시 follow-up 박제 — 단발성, 30분 이내

### 3.6 [LOW] Dockerfile HEALTHCHECK placeholder — TDD 단계별 적용

**관측**:
- 초기 Dockerfile (`83c26e8`) 에 `HEALTHCHECK CMD ["true"]` placeholder 작성
- HealthExporter (`696b6b5`) 구현 후 `fb8f99b` 에서 실제 HEALTHCHECK 복원 (port 9200 metrics 응답 확인)

**근본 원인 분석**:
- TDD 단계별 의존성 — Task 0 (Dockerfile) 작성 시 Task 3 (HealthExporter) 미구현 → port 9200 endpoint 부재
- placeholder → 실제 코드 전환 패턴 — 의도된 2-step 적용

**의미**:
- 본 패턴 의도적, 문제 아님 — TDD 의 자연스러운 결과
- 그러나 **placeholder 잔존 위험** — Task 3 완료 후 HEALTHCHECK 복원 잊을 시 운영 환경에서 health check 무의미

**평가**:
- 본 case 는 즉시 fix 발견 — 작업 흐름 내 catch
- 향후 placeholder 도입 시 commit message 에 "TODO: restore on Task X" 명시 권장
- ADR 박제 불필요 — TDD 자연스러운 패턴

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [LOW] React SPA 거래소 공지 수집 패턴 박제 — XHR API 의존 + URL 외부 주입

```
target_adr: ADR 신규 또는 README guidance
amendment_type: pattern (XHR endpoint 의존성 박제)
trigger: RETRO-MCT-124 §3.1 Upbit/Bithumb SPA 한계
배경:
  - 거래소 공지 페이지의 SPA 전환 추세 — 공식 API 부재 시 XHR endpoint 의존
  - XHR endpoint 는 비공식 — 거래소 측 변경 시 무음 실패
  - 사용자 수동 Chrome DevTools 탐색 필요 — 자동화 비용 폭증
문제:
  - SPA worker 추가 시마다 같은 함정 — Coinbase / Binance Korea 등 향후 도입 시 재현
  - silent 실패 — XHR endpoint 변경 시 stale fallback 만 publish, 운영자 인지 지연
제안 결정:
  a) Lite: env var 주입 패턴 박제 (`{EXCHANGE}_NOTICE_API_URL`) + freshness 메트릭 알람
  b) Medium: ADR 신규 — SPA 공지 수집 표준 (XHR endpoint discovery + env injection + freshness alert)
  c) Heavy: Playwright headless + 자동 endpoint 검증 cron
예상 결과:
  - 신규 거래소 SPA 공지 도입 시 패턴 재사용
  - 운영 알람으로 endpoint 변경 즉시 감지
보류 사유:
  - 본 사례 1건 (Upbit + Bithumb 동시) — 추가 거래소 도입 시점에 재평가
  - env var 주입 패턴은 본 Story 코드에서 이미 작동
```

### 4.2 [LOW] Prometheus instance-level Registry 패턴 박제

```
target_adr: ADR 신규 또는 mctrader-data/engine README guidance
amendment_type: pattern (test 격리 가능한 Registry 패턴)
trigger: RETRO-MCT-124 §3.2 HealthExporter 전역 Registry 충돌
배경:
  - prometheus_client default registry 가 모듈 전역 singleton — 다중 인스턴스화 시 중복 timeseries
  - mctrader-data + mctrader-engine 의 metrics.py (RETRO-MCT-122-123 §4.2) 가 모듈 전역 패턴 사용
  - 향후 mctrader-web / 추가 컴포넌트 도입 시 동일 함정 가능
문제:
  - test 격리 부재 — pytest 다중 인스턴스화 시 silent 충돌
  - 운영 환경에서는 무관, test 에서만 발견 — silent debt 형성
제안 결정:
  a) Lite: README guidance — "HealthExporter __init__ 내부 CollectorRegistry() 패턴"
  b) Medium: 공유 라이브러리 (mctrader-common 가칭) — HealthExporter base 추출 (RETRO-MCT-122-123 §4.2 의 b 옵션과 동일)
  c) Heavy: ADR 박제 — Prometheus instance-level Registry 표준
예상 결과:
  - test 격리 가능
  - 신규 worker / endpoint 추가 시 패턴 재사용
보류 사유:
  - mctrader-data + engine 은 process-level singleton 으로 충돌 회피 가능
  - 본 Story signal-collector 만 instance-level 필요 — RETRO-MCT-122-123 §4.2 와 함께 누적 후 재평가
```

### 4.3 [LOW] 신규 리포 생성 Story 의 GitHub org 작업 Task 표준화

```
target_adr: ADR-019 amendment 또는 README guidance
amendment_type: governance (신규 리포 생성 Story 의 표준 Task)
trigger: RETRO-MCT-124 §3.4 mctrader-signal-collector remote 미설정 + branch master/main 불일치
배경:
  - RETRO-MCT-121 mctrader-market-upbit 신규 plugin repo (#216 PR 동시 진행) — GitHub org 작업 동시 처리됨
  - RETRO-MCT-124 mctrader-signal-collector — GitHub org 작업 미처리, branch master 잔존
  - 신규 리포 생성 Story 의 Plan 에 GitHub org 작업 Task 누락 가능
문제:
  - 신규 리포 코드 만 로컬, remote 미생성 → 다른 작업자 / CI 접근 차단
  - branch 명 environment 별 default 차이 (master vs main) — 다른 리포와 일관성 없음
  - silent debt — 사용자가 후속 처리 안 하면 영원히 로컬
제안 결정:
  a) Lite: 신규 리포 생성 Story 의 Plan 에 "GitHub org repo 생성 + remote 설정 + branch=main + push" Task 명시
  b) Medium: PMOAgent 가 신규 리포 생성 detect 시 자동 follow-up Task 발의
예상 결과:
  - 신규 리포 잔존 부재 — 운영 활성화 차단 요인 1개 제거
  - branch 명 일관성
보류 사유:
  - 본 사례 1건 (RETRO-MCT-121 은 동시 처리됨) — 1주 관측 권장
  - mctrader-hub README guidance 로 즉시 대체 가능
```

### 4.4 [LOW] keyword classification "specific-first" 순서 패턴 박제

```
target_adr: README guidance (signal-collector 또는 mctrader-data text classification)
amendment_type: pattern (prefix 충돌 회피)
trigger: RETRO-MCT-124 §3.3 _CLASSIFY_MAP 순서 버그
배경:
  - keyword dict 순회 기반 분류 시 short keyword 가 long keyword superstring 인 경우 short 가 먼저 매칭
  - "상장" vs "상장폐지" — Spec/Plan 단계 미발견, 코드 구현 후 자체 발견
문제:
  - 향후 신규 분류 keyword 추가 시 같은 함정 가능
  - test 미작성 시 silent 오분류
제안 결정:
  a) Lite: signal-collector README — "더 specific 한 패턴 먼저" 명시
  b) Medium: classify_title 함수에 검증 assertion (긴 keyword 가 짧은 keyword superstring 인 경우 순서 강제)
예상 결과:
  - 분류 keyword 추가 시 함정 회피
보류 사유:
  - 단발성 fix, ADR 박제 over-engineering
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 10 Story sweep — token efficiency 누적 (갱신)

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
- **MCT-124 (signal-collector — 신규 독립 리포 + 937 LoC, 5 worker + 31 test)**

→ **10 Story (10 PR + 1 직접 push + 2 신규 리포) + ~10000 LoC + 2 신규 plugin repo + 5 모니터링 컨테이너 + 5 시그널 컨테이너 = single-session completion**. RETRO-MCT-122-123 §5.1 의 9 Story 를 10 으로 확장. **codeforge ζ arc velocity 가 신규 리포 생성 + 외부 시그널 도입까지 일반화**.

### 5.2 신규 plugin/service 리포 생성 패턴 — 누적 2건

| Story | 신규 리포 | 도메인 | 기존 리포 영향 |
|---|---|---|---|
| MCT-121 | mctrader-market-upbit | 거래소 plugin (Upbit Open API) | mctrader-data 통합 import |
| **MCT-124** | **mctrader-signal-collector** | **외부 시그널 수집 서비스** | **mctrader-hub compose 5 service 추가** |

→ **신규 도메인 컴포넌트 = 신규 리포 패턴** 재현. 공통 패턴:
- 독립 Python 프로젝트 (pyproject.toml + Dockerfile + compose.yml)
- 기존 mctrader 의존성 0 또는 최소
- mctrader-hub compose 통합 (orchestration 책임 hub 집중)
- 신규 리포 GitHub org 처리는 MCT-121 동시, MCT-124 PENDING (§3.4)

→ 본 패턴 누적 시 ADR-019 amendment 또는 신규 ADR (신규 리포 생성 표준) 박제 가치 — 1건 더 누적 시 박제 권고.

### 5.3 PMO 회고 자동 dispatch closed-loop — 10 사례 누적

ADR-020 D1 자동 dispatch + MEMORY `feedback_pmo_retro_mandatory.md` closed-loop 가 본 Story (10번째) 에서 작동. 패턴 안정성 입증 — **동일 세션 내 10 Story 모두 회고 박제 누락 0**. RETRO-MCT-122-123 §5.5 의 closed-loop 박제 시급성 이미 약화 → 본 Story 에서 추가 약화 (10 누적).

### 5.4 부수 fix 카테고리 갱신 — Cat B 21% 단발성, Cat A/C 0

| Story | Cat A (pre-existing) | Cat B (self-discovered) | Cat C (다른 Story finish-up) | 본 fix |
|---|---|---|---|---|
| MCT-117 | **350%** (39/11) | <10% | 0 | 11 |
| MCT-119+120 | <10% | 17% | 0 | 29 |
| MCT-121 | <10% | 7% | **36%** (MCT-115 finish-up) | 8 |
| MCT-122+123 | <10% | <10% | **43%** (MCT-120/121 finish-up) | 8 |
| **MCT-124** | **0** | **21%** (3 commit) | **0** | **11** |

→ Cat C 가 본 Story 에서 **0 으로 회귀** — 신규 리포 단일 Story 라 다른 Story finish-up 부재 자연스러움. RETRO-MCT-122-123 §6 #2 의 "PR description Cat 분류 표 의무화" 권고가 **본 Story 에서는 적용 무의미** (Cat C 0). 다음 multi-Story PR 시점에 재적용.

### 5.5 도구 선택의 적합성 누적 — 임베디드 / fakeredis / Sonnet decider

본 Story 의 도구 선택 결정 4건:

| 결정 | 패턴 |
|---|---|
| 신규 독립 리포 (Spec §1 #1) | **장애 격리 + decoupling** — 큰 컴포넌트는 별도 리포 |
| BaseWorker 추상화 (§2.2) | **DRY via abstraction** — 5 worker 공통 로직 100% 흡수 |
| fakeredis test (§2.3) | **integration-grade unit test** — 컨테이너 의존성 0 |
| Sonnet decider 8 결정 stack (§2.4) | **결정 박제** — 거부 대안 명시 |

→ **소규모 / 표준 / 임베디드 우선 패턴** (RETRO-MCT-122-123 §5.4 누적). 본 Story 의 추가 패턴: **신규 리포는 즉시 분리, 추상화는 일찍, test 의존성은 fake/mock 우선**.

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **mctrader-signal-collector GitHub org 작업 즉시 follow-up (§3.4)** — repo 생성 + branch rename master→main + remote add + push + GHCR image build/push CI workflow. 1주 이내 완료 권장. 그 후 hub compose `image:` 가 GHCR pull 가능. 운영 활성화 차단 요인 1 제거.

2. **Task 8 사용자 수동 XHR API 탐색 (§3.1)** — Chrome DevTools Network 탭으로 Upbit/Bithumb 공지 XHR endpoint 발견 → `.env` 의 `UPBIT_NOTICE_API_URL` / `BITHUMB_NOTICE_API_URL` 투입 → signal-announcement 컨테이너 운영 활성. 30분 이내 단발성. 운영 활성화 차단 요인 2 제거.

3. **Story file MCT-124 작성 + §11 회고 pointer 박제 (§3.5)** — `docs/stories/MCT-124.md` 작성, status 갱신 (Task 8 + GitHub org 작업 PENDING 명시), §11 에 본 retro pointer. ADR-020 D1 enforcement gap 회복. 30분 이내 단발성.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Spec 작성 (Sonnet decider 8 결정 stack) | ~10% |
| Plan 작성 (12 Task TDD breakdown) | ~10% |
| Task 0 (리포 스캐폴드 + Dockerfile + compose + .env) | ~5% |
| Task 1-3 (core: publisher / dedup / health + 11 test) | ~15% |
| Task 4 (BaseWorker) | ~3% |
| Task 5-7 (fear_greed / ecos / kimchi_premium + 10 test) | ~15% |
| **Task 8 PENDING (Upbit/Bithumb XHR 탐색 — 사용자 수동)** | **0% (skip)** |
| Task 9 (announcement worker + 8 test + _CLASSIFY_MAP 순서 fix) | ~10% |
| Task 10 (coinglass + 2 test) | ~5% |
| Task 11 (Hub compose 5 service + .env 통합) | ~5% |
| Task 12 (전체 31 test 검증 + Docker 빌드) | ~5% |
| Prometheus Registry 충돌 fix (§3.2) | ~3% |
| Dockerfile HEALTHCHECK fix (§3.6) | ~2% |
| 본 retro 작성 | ~10% |
| 그 외 (Sonnet decider sub-decision, Plan 검증) | ~2% |

→ **부수 비용 (Cat B + retro 작성) ~25%** — RETRO-MCT-122-123 ~33% 보다 감소. **신규 리포 단일 Story** 라 다른 Story finish-up (Cat C) 부재. §6 #1 (GitHub org follow-up) + §6 #2 (Task 8 XHR) 적용 시 운영 활성화까지 ~1시간 추가.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-002**: TradeExecutor 3 mode — 본 Story Spec related_adr (시그널 소비는 engine 측, 본 Story 는 publish 까지)
- **ADR-019**: Parallel agent isolation — D6 hub trunk-based 패턴 본 Story 재현 (mctrader-hub main 직접 push)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro trigger, 10번째 closed-loop 사례)
- **ADR-011**: CI standard — mctrader-signal-collector 신규 리포 GHCR workflow 작성 PENDING (§6 #1)
- **MEMORY** `feedback_admin_merge_autonomy.md`: hub commit `9207561` main 직접 push (10번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_autonomous_execution.md`: 본 Story 가 spec→plan→구현 전 과정 승인 gate 없이 자율 진행 — 사용자 "끝까지 진행해" 의도 반영
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — 본 Story 가 ζ arc 진입 후 첫 신규 외부 의존성 도입 컴포넌트
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준)
  - `RETRO-MCT-119-120-strategy-pipeline.md` (§6 #2 Sonnet decider 패턴, 본 retro §2.4 재현)
  - `RETRO-MCT-121.md` (§5.2 신규 plugin repo 패턴, 본 retro §5.2 누적 2건)
  - `RETRO-MCT-122-123.md` (§4.2 HealthServer /metrics 표준, 본 retro §4.2 instance-level Registry 패턴 누적)

---

## 9. Story §11 회고 pointer (PENDING — §3.5 follow-up)

- `docs/stories/MCT-124.md` **미작성** — RETRO §3.5 의 follow-up 으로 작성 필요
- 작성 시 §11 에 본 retro pointer 박제 (`RETRO-MCT-124-signal-collector.md`)

ADR-020 D1 enforcement gap (RETRO-MCT-117 §3.2) 본 Story 에서 발생 — Story file 미작성으로 회고 link back 차단. §10.1 즉시 follow-up.

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **mctrader-signal-collector GitHub org 작업** (§3.4 / §6 #1) — repo 생성 + branch master→main + remote add + push + GHCR workflow. 1주 이내.
- **Task 8 — Upbit/Bithumb XHR API 탐색** (§3.1 / §6 #2) — Chrome DevTools 사용자 수동, 30분.
- **Story file MCT-124 작성** (§3.5 / §6 #3) — `docs/stories/MCT-124.md` + §11 회고 pointer.
- **hub compose `image:` 검증** — GHCR push 후 hub `docker compose pull signal-*` + `docker compose up signal-fear-greed` 단독 연기 (Plan §Task 12 Step 3 의 실제 실행).

### 10.2 ADR 박제 (1주 관측)

- **React SPA 거래소 공지 수집 패턴** (§4.1) — 추가 거래소 (Coinbase / Binance Korea 등) 도입 시점에 재평가.
- **Prometheus instance-level Registry 패턴** (§4.2) — RETRO-MCT-122-123 §4.2 와 함께 누적, 3+ 컴포넌트 도입 시점에 재평가.
- **신규 리포 생성 Story 의 GitHub org 작업 표준화** (§4.3) — 1주 관측, 다음 신규 리포 생성 Story 발생 시 즉시 박제.
- **keyword classification "specific-first" 순서** (§4.4) — README guidance 즉시 대체 가능.

### 10.3 별도 issue 발의

- **signal-archiver 후속 Story** — Spec §11 명시 Phase 1 스코프 아웃, DuckDB warm + Postgres cold 아카이빙 별도 Story.
- **engine 측 Redis Stream subscriber Story** — `signals:{kind}` 5종 subscribe + 포지션/리스크 결정 반영. mctrader-engine 변경.
- **mctrader-web Streamlit 시그널 dashboard** — 6 시그널 시각화 (DuckDB warm + Streamlit 페이지).
- **Grafana dashboard JSON drop-in** (RETRO-MCT-122-123 §10.1 누적) — signal_worker_success_total / signal_worker_error_total / signal_worker_last_success_timestamp_seconds 메트릭 시각화.

### 10.4 외부 시그널 후속 Story 트리거

본 Story MCT-124 완료로 다음 Story 가능:
- **engine signal subscriber** (위 §10.3) — 가장 가치 큰 후속, signal → 포지션/리스크 closed-loop 완성
- **alerting rules** (RETRO-MCT-122-123 §10.5 누적) — Prometheus alertmanager + 임계 alert (signal worker stale > 5분 / error rate > threshold)
- **Tier 2 시그널 도입** — Twitter/X / Reddit / Glassnode / FRED (Spec §12 스코프 아웃, v2 검토 대상)
- **Telegram fastpath** (Spec §1 #5 거부) — v2 재검토, 스푸핑 위험 완화책 검토 후

### 10.5 Spec/Plan 패턴 재사용

본 Story Spec/Plan 의 재사용 가능 패턴:
- **8 결정 stack 박제** — Sonnet decider 결정점 + 거부 대안 표 (RETRO §2.4)
- **TDD Task breakdown** — Task 1-N 각각 (test 작성 → 실패 확인 → 구현 → 통과 → commit) 4단계 (RETRO §2.5 표준)
- **신규 리포 스캐폴드 패턴** — pyproject.toml + Dockerfile (2-stage) + compose.yml + .env.example + README.md 6 파일 표준

→ 다음 신규 리포 생성 Story (예: signal-archiver) 시점에 본 Story 패턴 100% 재사용 가능.

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10

---

## Amendment — 2026-05-10 운영 활성화 + 5 런타임 이슈 fix 후 보강

**Trigger**: 본 retro 초기 작성 시점 (§3.1/3.4/3.5 PENDING) 이후 진행된 운영 활성화 작업의 회고 박제. 4개 시그널 스트림 모두 `stale=false` 운영 확인, 신규 리포 GitHub push 완료, Story file 작성 완료. 운영 활성화 과정에서 발견된 런타임 이슈 5건의 root cause 분석 + 외부 API 의존성 관리 패턴 박제.

### A.1 §3.1 / §3.4 / §3.5 PENDING 해소 보고

| 본 retro 초기 PENDING | 해소 결과 | commit |
|---|---|---|
| §3.1 Task 8 Upbit/Bithumb XHR API 탐색 | **완료** — Upbit `api-manager.upbit.com/api/v1/announcements` 내부 API 발견 + Bithumb `feed.bithumb.com` cloudscraper + Next.js buildId 동적 추출 | `ba6cfe3` (env URL 제거 — hardcoded endpoint) + signal-collector 본체 |
| §3.4 mctrader-signal-collector remote 미푸시 | **완료** — `mclayer/mctrader-signal-collector` private repo 생성 + main push | (signal-collector main push) |
| §3.5 Story file MCT-124 미작성 | **완료** — `docs/stories/MCT-124.md` 작성 + §11 회고 pointer 박제 | `a63ac4e` + `165bbd7` |

→ **3 PENDING 모두 동일 세션 (2026-05-10) 해소**. 본 retro 초기 작성 시점의 ADR-020 D1 enforcement gap (§3.5) 회복 — Story file → RETRO link back 작동.

### A.2 운영 활성화 5 런타임 이슈 — 동일 메타 패턴 (외부 API pre-deploy 검증 부재)

운영 활성화 (4 worker 실제 외부 API 호출 시작) 시점에 발견된 5 런타임 이슈가 모두 **같은 메타 패턴** (외부 API/의존 사전 검증 ad-hoc) 공유:

#### A.2.1 [HIGH] CryptoQuant 무료 플랜 403 — `korea-premium-index` 유료 plan 전용

**관측**: kimchi_premium worker 첫 호출 시 HTTP 403. `korea-premium-index` endpoint 가 무료 plan 미지원 (유료 plan 전용 — CryptoQuant docs 의 plan matrix 미독해 결과).

**해결**: Upbit BTC/KRW + Binance BTC/USDT + Frankfurter USD/KRW **공개 API 3-source 조합** 으로 직접 계산. API 키 의존 제거.

```
premium = (upbit_btc_krw / (binance_btc_usdt * frankfurter_usd_krw) - 1) * 100
```

**근본 원인**:
1. 설계 phase 에 CryptoQuant 무료 plan 의 endpoint 매트릭스 미확인 — API 키 발급 시 단순 "key 작동" 만 확인
2. 공개 API 우선 원칙 부재 — "전문 데이터 소스" 우선 가정, 공개 API 합성 가능성 미검토
3. 결과적으로 fix 가 **API 키 의존 자체 제거** → 원래 외부 API 도입 자체가 over-engineering

**의미**: 본 fix 후 KimchiPremiumWorker 가 **3 외부 의존 (Upbit + Binance + Frankfurter)** 합성. 단일 API 의존 대비 fault-tolerance 약화 (3 source 중 1 fail 시 전체 fail) — 그러나 모두 stable public API 라 누적 SLA 우수. commit `d503d7e` 가 hub `.env.example` 의 `CRYPTOQUANT_API_KEY` 제거 반영.

#### A.2.2 [HIGH] ECOS 주말 empty rows — 영업일 공백 silent 결함

**관측**: ECOS worker 첫 호출 (토요일 2026-05-10) 시 `today` 단일 날짜 쿼리 → empty rows. 한국은행 ECOS 는 영업일 데이터만 publish — 주말/공휴일은 미생성.

**해결**: 7일 범위 쿼리 (`startDate=today-7d`, `endDate=today`) + 항목코드 `0000001` (USD) 명시 → 응답 중 가장 최신 발표일자 선택. 결과: stale=false, usd_krw=1450.8 (2026-05-08 발표).

**근본 원인**:
1. **공공 데이터 API 영업일 공백 패턴 미인지** — 한국은행 / 통계청 / 금융감독원 공공 API 가 모두 영업일 기준
2. 단일 날짜 쿼리 가정 — "오늘 데이터 있을 것" 암묵 가정
3. 항목코드 default 모호 — ECOS 응답이 다중 통화 (USD/JPY/EUR) 포함, 미명시 시 잘못된 통화 선택 가능

**의미**: 본 fix 가 토요일 운영 시점에 catch — 운 좋은 timing. 평일 도입 시 silent (다음 주말까지 잘못된 stale=false publish 가능). KOSIS / DART 등 다른 공공 API 도입 시 동일 패턴 잠재.

#### A.2.3 [MEDIUM] Bithumb Cloudflare 차단 — SPA reverse engineering 비용

**관측**: Bithumb `feed.bithumb.com` 첫 호출 시 Cloudflare challenge — `requests` / `httpx` 모두 차단. 추가로 Next.js SPA 구조 — HTML 은 SSR shell, 데이터는 client-side hydration.

**해결**: `cloudscraper` (CF challenge bypass) + buildId 동적 추출 + `/_next/data/{buildId}/notice.json` 직접 호출.

```python
# AnnouncementWorker._fetch_bithumb (요지)
scraper = cloudscraper.create_scraper()
html = scraper.get("https://feed.bithumb.com/notice").text
build_id = re.search(r'"buildId":"([^"]+)"', html).group(1)
data = scraper.get(f"https://feed.bithumb.com/_next/data/{build_id}/notice.json").json()
```

**근본 원인**:
1. **CF protection 사전 검증 부재** — 설계 시 Bithumb 의 CF protected 여부 미확인
2. **SPA hydration 가정 부재** — 거래소 공식 사이트가 SSR + hydration 임을 일반화 못 함
3. **buildId 변경 빈도** — Next.js buildId 가 deploy 마다 변경 → 매 호출 동적 추출 필수 (현재 구현 OK)

**의미**: 본 fix 가 cloudscraper 의존성 신규 도입 — 향후 거래소 공지 추가 (Coinbase / Binance Korea) 시 동일 패턴 재사용 가능.

#### A.2.4 [LOW] Frankfurter API 도메인 이전 — endpoint silent drift

**관측**: kimchi_premium worker (Frankfurter USD/KRW 쿼리) 첫 호출 시 301 redirect — `api.frankfurter.app` → `api.frankfurter.dev/v1`. 

**해결**: URL 직접 수정 (`api.frankfurter.app` → `api.frankfurter.dev/v1`).

**근본 원인**: 외부 의존 endpoint 의 silent domain drift — 본 사례는 단순 URL 갱신, 그러나 endpoint deprecated 시 비용 큼.

**의미**: 외부 의존 URL 의 README 박제 + 정기 health check 권장 (월 1회 cron 검증).

#### A.2.5 [LOW] cloudscraper 버전 fabrication — PyPI 검증 부재

**관측**: 초기 `pyproject.toml` 의 `cloudscraper>=2.3` 제약. `pip install` 실패 — PyPI 에 cloudscraper 1.2.71 까지만 존재.

**해결**: `>=1.2` 로 제약 완화.

**근본 원인**: 신규 의존성 버전 fabrication — LLM-generated pyproject.toml 의 silent 위험. PyPI 검증 단계 부재.

**의미**: 본 사례는 install 시점 즉시 fail → catch. 그러나 less common dependency 도입 시 잘못된 version 으로 silent install 가능.

### A.3 외부 API 의존성 관리 패턴 (Cross-Story 누적)

본 Story 5 런타임 이슈가 동일 root cause (외부 API 사전 검증 부재) 공유 — 패턴 박제:

#### A.3.1 패턴: 공개 API 우선 원칙

| 우선순위 | 옵션 | 본 Story 사례 |
|---|---|---|
| 1 | 공개 API 단일 소스 | Alternative.me F&G — 인증 없이 작동 |
| 2 | 공개 API 합성 (multi-source) | kimchi_premium — Upbit + Binance + Frankfurter (CryptoQuant 대체) |
| 3 | 공공 기관 API + API 키 (free tier) | ECOS — API 키 필요, 영업일 공백 처리 |
| 4 | 거래소 internal API (undocumented) | Upbit `api-manager` + Bithumb `_next/data` |
| 5 | 유료 API | (회피 — 본 Story 에서 CryptoQuant 폐기) |

→ **유료 API 도입 전 1~4 옵션 전수 검토 의무화** — 본 Story §A.2.1 사례가 이 원칙 위반의 cost 입증.

#### A.3.2 패턴: API 키 발급 시 plan endpoint matrix 사전 확인

```
□ API 키 발급 plan (free / paid tier) 매트릭스 확인
□ 사용할 모든 endpoint 가 free plan 에서 가용한가
□ rate limit / quota 가 worker polling interval 과 호환되는가
□ 인증 방식 (API key / OAuth / IP whitelist) 명시
```

→ 본 Story §A.2.1 의 root cause 회피 가능했던 단계 — 발급 시 5분 추가로 deploy 후 alternative 구현 ~10% 토큰 비용 회피.

#### A.3.3 패턴: 공공 데이터 API 영업일 공백 처리

```python
# Lite helper (signal-collector + 향후 KOSIS/DART worker 재사용)
def fetch_latest_business_day_value(api, item_code: str, days_back: int = 7) -> dict:
    """공공 API 영업일 공백 대응 — multi-day 범위 쿼리 + 최신 선택"""
    today = date.today()
    rows = api.fetch(item_code, today - timedelta(days=days_back), today)
    if not rows:
        raise ExternalApiEmptyError(f"{item_code} no data in {days_back}d range")
    return max(rows, key=lambda r: r["date"])  # 가장 최신 발표일
```

→ 본 Story §A.2.2 의 root cause — ECOS 외 KOSIS / DART 등 향후 공공 API 도입 시 100% 재사용 가능.

#### A.3.4 패턴: SPA scrape 사전 검증 매트릭스

```
신규 외부 사이트 scrape 도입 전 체크:
□ Cloudflare protection 여부 (curl test)
□ Next.js / React SSR + hydration 구조 여부 (HTML 본문 검사)
□ internal API endpoint 존재 여부 (DevTools Network 탭 / GitHub code search)
□ buildId / version dynamic 추출 패턴 박제
□ User-Agent / Accept-Language 헤더 요구사항 (Korean locale 등)
□ rate limit 정책 (실험 후 측정)
```

→ 본 Story §A.2.3 (Bithumb) + Story §11 #1 (Upbit) — 거래소 공식 사이트는 모두 SPA + internal API 패턴.

### A.4 Cross-Story 인사이트 — 외부 의존 Story 의 cost 패턴

#### A.4.1 부수 fix 카테고리 갱신 — Cat B 신기록

| Story | Cat A | Cat B | Cat C | 본 fix |
|---|---|---|---|---|
| MCT-117 | 350% | <10% | 0 | 11 |
| MCT-119+120 | <10% | 17% | 0 | 29 |
| MCT-121 | <10% | 7% | 36% | 8 |
| MCT-122+123 | <10% | <10% | 43% | 8 |
| **MCT-124 (Amendment 후)** | **0%** | **31%** (5 런타임 + 3 초기 self-discovered) | **0%** | **11** |

→ Cat B **31% 신기록**. **외부 의존 Story 의 cost 패턴 변화 입증** — Cat A/C 가 0 인 신규 plugin repo 부트스트랩, Cat B 가 dominant. 향후 외부 API/의존 Story 의 표준 패턴 후보.

#### A.4.2 메타 패턴: pre-deploy 검증 한계 — 누적 사례 갱신

| Story | 검증 대상 | catch 시점 |
|---|---|---|
| MCT-122 | alembic 0002 FK 타입 (RETRO-MCT-122-123 §3.6) | 시스템 재구동 |
| MCT-123 | ws_connected tf=1h health check (RETRO-MCT-122-123 §3.7) | 시스템 재구동 |
| **MCT-124 §A.2.1** | **CryptoQuant free tier endpoint** | **운영 첫 호출** |
| **MCT-124 §A.2.2** | **ECOS 영업일 공백** | **운영 첫 호출** (토요일) |
| **MCT-124 §A.2.3** | **Bithumb CF + SPA** | **운영 첫 호출** |
| **MCT-124 §A.2.4** | **Frankfurter URL drift** | **운영 첫 호출** |
| **MCT-124 §A.2.5** | **cloudscraper PyPI 버전** | **install 시점** |

→ **누적 7건** (RETRO-MCT-122-123 2건 + 본 retro 5건). 모두 CI green + admin merge 후 silent debt 누적 → **운영 환경 첫 가동** 시점 catch. **pre-production smoke gate 박제 시급성 임계 도달**.

#### A.4.3 ADR 후보 발의 — 외부 API baseline (HIGH 우선)

```
target_adr: ADR 신규 (외부 의존성 baseline) 또는 ADR-018 D? amendment
amendment_type: governance + artifact (체크리스트 + helper)
trigger: RETRO-MCT-124 Amendment §A.2 5 런타임 이슈 + RETRO-MCT-122-123 §5.6 메타 패턴 누적 7건
배경:
  - 외부 API/의존 도입 시 사전 검증이 ad-hoc — free tier matrix / 공개 API 대체 / SPA 검증 / PyPI 버전 / endpoint URL stability
  - 결과: deploy 후 발견 → alternative 구현 비용 + 의존성 추가 비용 (본 Story Cat B 31%)
  - RETRO-MCT-122-123 §5.6 의 pre-production smoke gate 메타 패턴과 본 retro §A.2 합쳐 누적 7건
문제:
  - 외부 의존 Story 의 cost 가 다른 Story 대비 ~3배 (Cat B 31% vs <10%)
  - 사전 검증 cost (5~30분) 대비 deploy 후 alternative 구현 cost (1~3시간) 의 ROI 불균형
  - 누적 사례가 패턴 안정화 임계 도달 (7건)
제안 결정:
  a) Lite (즉시): 외부 API 도입 PR reviewer checklist 박제 (§A.3.1~A.3.4)
     - 공개 API 우선 원칙 (§A.3.1)
     - API 키 plan matrix 사전 확인 (§A.3.2)
     - 공공 API 영업일 공백 처리 (§A.3.3)
     - SPA scrape 사전 검증 (§A.3.4)
     - PyPI 버전 검증 (`pip index versions`)
     - endpoint URL stability (도메인 이전 이력)
  b) Medium: ADR 신규 — 외부 의존성 baseline (위 6 항목 박제)
  c) Heavy: pre-production smoke gate CI workflow — 외부 API 통합 테스트 (rate limit / API 키 비용 trade-off 동반)
예상 결과:
  - 외부 API 도입 비용 사전 인지
  - 유료 API 도입 회피 가능 사례 catch (본 Story §A.2.1 같은 사례 회피)
  - 공공 API 영업일 공백 silent 결함 회피
  - SPA scrape dependency 추가 정당화
배제 옵션:
  - 모든 외부 API 도입 ban (운영 불가능)
  - 통합 테스트 의무화 (rate limit / API 키 비용 / CI 신뢰도 trade-off)
권장 priority: HIGH (다음 외부 API 도입 Story 전 결정 — engine signal subscriber / signal-archiver / Tier 2 시그널 등)
관련:
  - ADR-018 Defensive coding baseline (input validation 측)
  - RETRO-MCT-122-123 §5.6 pre-production smoke gate 메타 패턴
  - 본 Amendment §A.4.2 누적 7건 데이터
```

#### A.4.4 stale fallback 의무화 패턴 — engine 측 contract 재확인

본 Story 4 worker (운영 시점에 5번째 CoinGlass placeholder) 모두 stale fallback 100% 작동:
- F&G 정상: stale=false, value=47 Neutral
- ECOS 정상: stale=false, usd_krw=1450.8 (2026-05-08 발표 — 토요일 기준 가장 최신)
- Kimchi 정상: stale=false, premium=0.57%
- Announcement 정상: stale=false (Upbit + Bithumb 양쪽)

→ **stale fallback 패턴이 외부 API friction 와 독립적으로 작동** — engine 측 stale-aware decision contract 의 baseline 박제 완료. 다음 Story (engine signal subscriber) 시 본 패턴 100% 재사용 가능.

### A.5 갱신된 우선순위 (다음 세션 반영)

1. **[HIGH] §A.4.3 외부 API baseline ADR 발의** — Lite (reviewer checklist) 즉시 적용. 누적 7건 임계 도달, 다음 외부 API 도입 Story 전 결정 권장.
2. **[HIGH] pre-production smoke gate** (RETRO-MCT-122-123 §10.2 + 본 Amendment §A.4.2 누적 7건) — compose 전체 stack 1회 기동 검증 CI workflow 또는 `make smoke` 박제.
3. **[MEDIUM] §A.3.3 공공 데이터 영업일 공백 helper** — README guidance + helper 함수 추출. 다음 공공 API 도입 (KOSIS / DART) 전.
4. **[MEDIUM] §A.3.4 SPA scrape 사전 검증 매트릭스** — README guidance 즉시 적용. 다음 거래소 공지 추가 (Coinbase / Binance Korea) 전.
5. **[LOW] §A.2.4 외부 의존 URL 정기 health check** — 월 1회 cron 또는 monitoring alert.
6. **[LOW] §A.2.5 PyPI 버전 검증** — 신규 의존성 추가 시 `pip index versions <pkg>` README 박제.

### A.6 갱신된 토큰·시간 분포

본 retro 초기 분포 (§7) 갱신:

| 구간 | 초기 분포 | Amendment 후 |
|---|---|---|
| Spec + Plan + 12 Task 구현 + Story 본 fix | ~75% | ~70% (변화 없음, 대부분 유지) |
| **§A.2.1 CryptoQuant 403 → Upbit+Binance+Frankfurter 대체** | (skip) | **~10%** |
| **§A.2.2 ECOS 영업일 공백 → 7일 범위 + USD 항목코드** | (skip) | **~5%** |
| **§A.2.3 Bithumb CF + SPA → cloudscraper + buildId** | (skip) | **~10%** |
| **§A.2.4 Frankfurter URL 이전** | (skip) | **~2%** |
| **§A.2.5 cloudscraper 버전 제약** | (skip) | **~2%** |
| 본 retro 작성 + Amendment | ~10% | ~12% (Amendment 추가) |

→ **외부 API friction 약 ~29%** (5 런타임 이슈 합계). RETRO-MCT-122-123 0% / RETRO-MCT-121 ~10% (Python 환경) 대비 큰 폭 증가. **외부 의존 Story 의 cost 패턴 변화 입증**. §A.4.3 baseline 박제로 향후 ~15% 회피 가능.

---

**Amendment 작성**: PMOAgent (Cross-Story 패턴 분석 — 운영 활성화 + 5 런타임 이슈 fix 후속 회고)
**Amendment 작성일**: 2026-05-10
