# RETRO-MCT-121 — Upbit 거래소 데이터 수집 지원

**범위**: MCT-121 (multi-repo Story · `mctrader-market-upbit` 신규 + `mctrader-data` 확장)
**기간**: 2026-05-09 ~ 2026-05-10 (cross-day, MCT-119/120 통합 PR #44 직후 동일 세션 연장)
**Trigger**: Upbit KRW+USDT 시장 OHLCV 백필 + 실시간 수집 지원, ADR-020 D1 자동 dispatch
**Status**: PR #28 MERGED (mctrader-data PR #28, 2026-05-09T21:14:44Z, admin merge) + mctrader-market-upbit v0.1.0 push 완료
**Story file**: `docs/stories/MCT-121.md`
**Repos**:
- `mctrader-market-upbit` (`c:\workspace\mclayer\mctrader-market-upbit`) — 신규 plugin repo, branch `main`
- `mctrader-data` (`c:\workspace\mclayer\mctrader-data`) — 멀티-exchange 확장, branch `feat/mct-120-121-122-123`

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 | 실제 | 비고 |
|---|---|---|---|
| **Phase 1 (mctrader-market-upbit)** | adapter / client / ws_client / ws_events / ws_mapping / ws_subscribe / ws_secret_guard / mapping / exceptions | 9 src + 9 test 파일 | 100% — first commit `30ec5f9` (scaffold) ~ `36ef9f0` (v0.1.0 complete) |
| Phase 1 테스트 | 46 pytest | 46/46 PASS | 100% |
| Phase 1 GitHub push | private repo 생성 + main push | 완료 (`origin/main` 동기) | 100% |
| **Phase 2 (mctrader-data)** | adapters.py 팩토리 신규 | `cd194892` 신규 + 6 unit test | 100% |
| Phase 2 collector 멀티-exchange | bithumb guard 제거 + kind-dispatch | `29e91e8a` refactor + `8d8971d4` adapter_version 복원 | 100% |
| Phase 2 cli `--exchange` | backfill/collect 옵션 | `d726123c` | 100% |
| Phase 2 compose 3-container | bithumb-ingester / upbit-ingester / compactor | `28d2e94e` | 100% |
| Phase 2 통합 테스트 | WAL 기록 검증 + orderbookdepth 미생성 검증 | `0e3aef18` | 100% |
| Phase 2 pytest | 310 회귀 0 | 310/310 PASS | 100% |

→ **양 repo 100% 완료, scope 누수 0**. RETRO-MCT-119-120 §3.1 의 web 미푸시 패턴 회피 성공.

### 1.2 PR #28 통계

- **+4015 / −76**, **22 파일**, **14 commit**
- commit 분포 (시간순):
  - 사전 정리 5 commit (ADR-018 D1/D2/D3 + ruff/pyright fix — MCT-115 finish-up)
  - spec/plans 2 commit (`be5e962b` Upbit 통합 설계 + `569d13af` 구현 계획)
  - 본 Phase 2 구현 6 commit (adapters / collector refactor / cli / compose / integration test / adapter_version 복원)
  - bithumb adapter_version regression fix 1 commit (`8d8971d4`)
- Squash merge `?` 2026-05-09T21:14:44Z (admin merge)

### 1.3 테스트 결과

| Repo | passed | failed | skipped |
|---|---|---|---|
| `mctrader-market-upbit` | **46** | **0** | 0 |
| `mctrader-data` | **310** | **0** | (확인 안 됨) |

→ 양 repo 회귀 0. 신규 4015 LoC + 신규 plugin repo 첫 PR 0 회귀.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 표준 적용)

| 카테고리 | commit 수 | 비중 | 카테고리 (Cat A vs B) |
|---|---|---|---|
| 사전 ADR-018 fix (MCT-115 finish) | 5 | 36% | Cat A (pre-existing — MCT-115 잔여) |
| 본 Phase 2 구현 | 6 | 43% | 본 fix |
| spec/plans 문서 | 2 | 14% | 본 fix (계획 문서) |
| **신규 코드 self-discovered fix** | **1** (`8d8971d4` bithumb adapter_version) | **7%** | **Cat B** |

→ Cat A 36% + Cat B 7%. **Cat A 가 본 Story 가 아닌 MCT-115 잔여 청소** — RETRO-MCT-119-120 §5.2 가 정의한 "두 카테고리 분리" 표준이 본 PR 에서 명확히 작동. PR scope 가 MCT-115 finish + MCT-121 본 작업으로 conflated 됐으나 retro 분석 시 분리 가능.

---

## 2. 잘된 점

### 2.1 multi-repo Story scope 누수 0 — RETRO-MCT-119-120 §3.1 패턴 회피

본 Story 는 RETRO-MCT-119-120 §3.1 ("engine PR merge 만으로 Story 완료 보고, web 미푸시 invisible") 의 직후 같은 세션에서 진행된 **첫 multi-repo Story**. 양 repo (`mctrader-market-upbit` 신규 + `mctrader-data` 확장) 모두 push + merge 완료:

| Repo | branch state | push | PR | merge |
|---|---|---|---|---|
| `mctrader-market-upbit` | `main` clean | ✅ | (private repo, PR 없이 main push) | ✅ |
| `mctrader-data` | `feat/mct-120-121-122-123` | ✅ | #28 | ✅ |

→ **closed-loop 작동 실증**: 직전 Story (MCT-119) 의 retro 권고가 다음 Story (MCT-121) 작성자에 자동 반영. PMOAgent §3 cross-Story 패턴 분석의 효과 두 번째 사례 (첫 사례: RETRO-MCT-117 §2.1 D1 sub-requirement 매트릭스).

### 2.2 Symbol 변환 zero-cost — Upbit market_code = `str(Symbol)`

설계 시 예상한 변환 로직 (`Symbol("BTC", "KRW") → "KRW-BTC"`) 이 **이미 `str(Symbol)` 의 기본 출력과 일치**. `mapping.py` 의 `symbol_to_market_code(s) = str(s)` 단 1줄로 구현 완료. **변환 코드 0건**:

```python
# mctrader-market-upbit/src/mctrader_market_upbit/mapping.py
def symbol_to_market_code(symbol: Symbol) -> str:
    return str(symbol)  # "KRW-BTC" 형식 일치
```

→ **사전 설계 시 도메인 모델 (Symbol class `__str__` 출력) 검증의 가치 재확인**. RETRO-MCT-119-120 §2.3 "사전 설계 (DTO/Protocol 명확)" 의 연장선. 본 사례는 추가 검증 단계 없이 **직관 적중**.

### 2.3 Orderbook snapshot-only 결정 — domain knowledge 기반 layer 분리

Upbit WebSocket 의 orderbook 채널이 **snapshot-only** (delta stream 미지원) 임을 사전 확인 → mctrader-data WAL ingester 의 `orderbookdepth` 채널 생성 **미수행**. 대신 `kind="orderbook_snapshot"` 으로 별도 dispatch:

| 거래소 | orderbook 데이터 | WAL 채널 |
|---|---|---|
| Bithumb | delta + snapshot | `orderbookdepth` (incremental) |
| Upbit | snapshot only | `orderbook_snapshot` (full snapshot per message) |

→ **거래소별 데이터 모델 차이를 추상화 layer 에서 흡수**. 단순 `s/Bithumb/Upbit/g` 가 아닌 도메인 차이 박제. ADR-019 D? Provider 적응 패턴 후보 가능 (1주 관측 후 결정).

### 2.4 Trade kind = `"transaction"` — WAL 채널 키 일치

Upbit WebSocket 의 `trade` 메시지를 mctrader-data WAL 의 `kind="transaction"` 으로 매핑. **상용 WAL 채널 키 (Bithumb 도 동일) 와 일치** → 멀티-exchange 환경에서 downstream consumer (compactor / ingester) 의 채널 dispatch 로직 변경 불필요.

→ **신규 거래소 추가 시 downstream layer 무영향 패턴**. 추후 Binance / Coinbase 등 추가 시 동일 패턴 적용 가능. RETRO-MCT-119-120 §2.4 "vertical slice 패턴" 의 horizontal 확장 사례.

### 2.5 admin merge autonomy + PMO 회고 자동 dispatch (ADR-020 D1) — 8번째 same-session 사례

PR #28 CI green 즉시 admin merge → 본 retro 자동 dispatch. 본 세션 누적: MCT-112/113/114/115/116/117/119+120/121 = **8 Story** 동일 패턴 작동. ADR-020 D1 + MEMORY `feedback_admin_merge_autonomy.md` closed-loop 정착 누적 8건.

---

## 3. 발생한 이슈

### 3.1 [MEDIUM] Python 3.14 환경 friction — `requires-python = ">=3.11,<3.13"` 위반

**관측**:
- 개발 머신 기본 Python 이 3.14 (Windows store 기본값으로 진입)
- mctrader-market-upbit `pyproject.toml` `requires-python = ">=3.11,<3.13"` 위반
- 첫 `pip install -e .` 시도 시 의존성 해결 실패 또는 silent 진행 후 import 시점에 실패
- 해결: `py -3.12` 명시적 호출로 신규 venv 생성

**근본 원인 분석**:
1. **신규 repo 부트스트랩 시 Python interpreter 검증 단계 부재** — venv 생성 시 사용자가 어느 Python 을 사용할지 결정해야 함
2. Windows 환경에서 `python` 명령이 가리키는 interpreter 가 user PATH 에 따라 다름 — Microsoft Store 의 Python 3.14 가 기본 진입 경로
3. mctrader 6 repo 의 `requires-python` 표준 (3.11~3.12) 이 README / 부트스트랩 스크립트에 박제 안 됨

**의미**:
- 향후 신규 plugin repo 생성 시 동일 friction 재발 가능
- 본 Story 는 ~30분 친크 — 1주 내 mctrader-market-coinbase / -binance 등 추가 plugin repo 발의 시 누적 비용
- README 또는 `bootstrap.ps1` 같은 setup 스크립트로 박제 가능 영역

**평가**:
- §4.3 ADR-019 또는 ADR-011 amendment 후보 — 신규 repo 부트스트랩 표준
- 단순 README guidance 로도 해결 가능 — ADR 박제는 over-engineering 위험

### 3.2 [MEDIUM] site-packages 구버전 우선 로딩 — editable install 함정

**관측**:
- `mctrader-data` 에서 `pip install -e ../mctrader-market-upbit` 실행 후에도 import 시 **5월 9일자 구버전** 디렉토리가 우선 로드
- `import mctrader_market_upbit; mctrader_market_upbit.__file__` 출력이 site-packages 의 stale 디렉토리 가리킴
- 해결: 수동 `rm -rf site-packages/mctrader_market_upbit/` 후 재설치

**근본 원인 분석**:
- pip 의 editable install 이 site-packages 에 `.pth` 파일을 추가하나, **기존 non-editable install 디렉토리가 잔존하면 sys.path 순서상 그것이 우선**
- 본 Story 는 mctrader-market-upbit 을 **같은 날 같은 venv 에서 두 번 설치**:
  1. 첫 번째: 일반 `pip install ../mctrader-market-upbit` (또는 `pip install mctrader-market-upbit @ git+...`)
  2. 두 번째: editable `pip install -e ../mctrader-market-upbit`
- 첫 번째가 site-packages 에 디렉토리를 생성, 두 번째가 `.pth` 만 추가 → import 시 디렉토리 우선

**의미**:
- editable install 전환 시 site-packages 잔존 디렉토리 수동 정리 필요
- 본 Story 는 `~30분` 디버깅 — silent stale import 가 잘못된 코드 실행으로 이어질 위험
- 다른 5 plugin repo (Bithumb / 기존 market) 도 동일 함정 잠재 가능

**평가**:
- pip 의 known limitation — `pip install -e` 전 `pip uninstall <pkg> -y` 명시 권장
- 프로젝트별 `dev-setup.ps1` 같은 idempotent setup 스크립트 가치 누적

### 3.3 [LOW] `decimal.InvalidOperation` 누락 — defensive coding 패턴 후보

**관측**:
- `mctrader-market-upbit/adapter.py` `_normalize_row` 의 `try/except` 절이 `(ValueError, KeyError, TypeError)` catch
- Upbit API 가 빈 문자열 또는 비정상 숫자 반환 시 `Decimal("")` 호출 → `decimal.InvalidOperation` 발생
- `InvalidOperation` 이 except tuple 에 미포함 → 비정상 row 가 traceback 으로 전파되어 백필 전체 abort
- 테스트가 잡아냄: `test_adapter.py` 의 edge-case test 에서 fail → except tuple 에 `InvalidOperation` 추가 fix

**근본 원인 분석**:
- Decimal 변환 시 `InvalidOperation` 은 ValueError 의 subclass 가 아닌 **별도 hierarchy** (decimal 모듈 자체 exception)
- Python 의 numeric parse error 가 type 별로 hierarchy 가 다름:
  - `int("")` → `ValueError`
  - `float("")` → `ValueError`
  - `Decimal("")` → `decimal.InvalidOperation` (← ValueError 아님)
- ADR-018 D1~D7 또는 RETRO-MCT-119-120 §4.3 의 None-guard 패턴과 별개 — **parse-error catch tuple 누락 패턴**

**의미**:
- 본 Story 만 1건 — RETRO-MCT-119-120 §4.3 의 None-guard 4건 (1주 관측 누적 권장) 과 합치면 **defensive coding 신규 패턴 후보 누적 5건**
- 다른 5 repo 의 `Decimal(...)` 호출 부위 audit 가능 (단순 grep)
- ADR-018 D8 후보 발의 시 두 패턴 (None-guard + parse-error tuple) 통합 박제 가능

**평가**:
- §4.2 ADR-018 신규 패턴 후보 — 1주 관측 후 결정

### 3.4 [LOW] MetadataRefreshScheduler Upbit 제외 — Phase 2 연기 결정의 박제 미흡

**관측**:
- `cli.py` 의 MetadataRefreshScheduler 가 `exchange == "bithumb"` guard 로 Upbit 비활성
- 본 Story scope 에서 Upbit metadata refresh 미구현 결정 → Phase 2 연기
- 그러나 이 결정이 Story file MCT-121 §3 "핵심 설계 결정" 외에 **GitHub issue / TODO 트래킹 부재**

**근본 원인 분석**:
- "Phase 2 연기" 가 Story file 만 박제 → 후속 Story 발의 시 invisible
- mctrader-data 의 `cli.py` 코드에 `# TODO(MCT-???): Upbit metadata refresh` 같은 marker 부재
- 발견 경로: 향후 Upbit metadata 가 stale 인지 사용자 / 모니터링이 알아챌 때까지 silent

**의미**:
- 본 Story 의 "Phase 2 연기" 결정이 후속 Story 트리거로 자동 연결되지 않음
- ADR-020 D? 후보: Story 의 deferred work 가 후속 Story 로 자동 발의되는 게이트
- 또는 단순 GitHub issue 발의 (MCT-?? Upbit metadata refresh) 로 해결 가능

**평가**:
- §10.3 follow-up issue 발의 권장 — 단순 운영 개선 영역, ADR 박제 불필요

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

### 4.1 [HIGH 갱신] ADR-018 D8 후보 — Optional None-guard + parse-error tuple 통합 박제

```
target_adr: ADR-018 D8 신규 (RETRO-MCT-119-120 §4.3 갱신)
amendment_type: artifact (코드 패턴)
trigger: 누적 5건
  - RETRO-MCT-119-120 §4.3: None-guard 4건 (Decimal sum init / mark_price / reject_reason ×2)
  - RETRO-MCT-121 §3.3: decimal.InvalidOperation parse-error 1건
배경:
  - ADR-018 D1~D7 은 input validation / state mutation / file I/O / async / header / governance 영역
  - 본 두 패턴은 공통적으로 **silent-pass via type system** 카테고리:
    a) Optional[T] 타입의 None branch 처리 누락 (silent NoneType 전파)
    b) parse-error exception hierarchy 누락 (silent traceback abort)
  - pyright 가 (a) 일부 catch, mypy 가 (b) 일부 catch — 그러나 **도메인 의도 박제 없음**
문제:
  - 단순 lint pass 가 아닌 도메인 의도 (예: mark_price None = 시장 데이터 부재 → no-trade) 명시 필요
  - parse-error 의 hierarchy 가 type 별로 다름 (int/float = ValueError, Decimal = InvalidOperation, json = JSONDecodeError)
  - 누락 시 silent abort 또는 silent NoneType propagation
제안 결정:
  a) ADR-018 D8 신규: "Optional 타입 None branch 명시 + parse-error catch tuple 표준화"
  b) D8 sub-requirement 매트릭스:
     D8.1: Optional[T] 함수 인자/return 시 None branch 명시 처리
     D8.2: None branch 의 도메인 의도 docstring 박제
     D8.3: numeric parse 시 (ValueError, InvalidOperation) 또는 (ValueError, TypeError, InvalidOperation) catch 표준
     D8.4: json/yaml parse 시 (JSONDecodeError 또는 YAMLError) catch + 도메인 fallback 박제
  c) 6 repo audit Story 발의 (MCT-114~117 패턴 재적용)
예상 결과:
  - silent None propagation 회피
  - silent parse-error abort 회피
  - 도메인 의도 코드-문서 일관성
보류 사유: 
  - 본 Story 1건 추가 → 누적 5건. RETRO-MCT-119-120 §4.3 의 "1주 관측 후 결정" 임계 도달
  - 즉시 ArchitectAgent dispatch 권장 — root cause 명확, 사례 충분
```

### 4.2 [MEDIUM] ADR-019 D? 또는 ADR-011 amendment 후보 — 신규 repo 부트스트랩 표준

```
target_adr: ADR-019 D? 신규 또는 ADR-011 amendment 또는 README guidance
amendment_type: behavior (부트스트랩 환경 검증)
trigger: 
  - RETRO-MCT-121 §3.1: Python 3.14 환경 friction (~30분)
  - RETRO-MCT-121 §3.2: site-packages stale 디렉토리 우선 로딩 (~30분)
배경:
  - 본 Story 가 신규 plugin repo (mctrader-market-upbit) 첫 부트스트랩
  - mctrader 6 repo `requires-python = ">=3.11,<3.13"` 표준이 README / 스크립트에 박제 안 됨
  - editable install 전 기존 디렉토리 정리 표준 없음
  - 향후 mctrader-market-binance / -coinbase 등 신규 plugin repo 발의 시 동일 friction 재발 보장
문제:
  - 신규 repo 부트스트랩 비용 매번 ~1시간 (Python 검증 + venv + editable install + stale 정리)
  - 누적 friction → 신규 plugin repo 발의 자체에 부담
제안 결정:
  a) Lite: 6 repo README 에 "부트스트랩" 섹션 표준화 (`py -3.12 -m venv` 명시 + `pip uninstall <pkg> -y && pip install -e ...` 패턴)
  b) Medium: `bootstrap.ps1` / `bootstrap.sh` idempotent 스크립트 — Python 검증 + venv 생성 + editable install
  c) Heavy: ADR 박제 — 6 repo 표준 + plugin repo 템플릿 (cookiecutter 등)
예상 결과:
  - 신규 plugin repo 부트스트랩 비용 ~10분
  - silent stale import 회피
  - Windows / Linux / macOS 환경 표준화
보류 사유:
  - 본 사례 1건 — 1주 관측 권장 (mctrader-market-binance 등 신규 plugin repo 추가 발의 시 누적 검증)
  - Lite 옵션 (README 갱신) 은 즉시 적용 가능 — ADR 박제 없이도 해결
```

### 4.3 [LOW] ADR-020 D? 또는 PMO process 권고 — Story deferred work 후속 Story 자동 발의 게이트

```
target_adr: ADR-020 D3 신규 (또는 PMOAgent.md §3 권고 표준화)
amendment_type: behavior (deferred work tracking)
trigger: RETRO-MCT-121 §3.4: MetadataRefreshScheduler Upbit Phase 2 연기 결정의 박제 미흡
배경:
  - Story 의 "Phase 2 연기" 결정이 Story file 만 박제 — 후속 Story 발의 시 invisible
  - 본 Story 외 같은 패턴 재발 가능: MCT-119+120 의 Phase 3 후보 (RETRO-MCT-119-120 §10.4) 도 GitHub issue 발의 안 됨
  - 코드에 `# TODO(MCT-???)` marker 부재 시 silent debt
문제:
  - deferred work 가 PMO retro 작성 시점 외에 surface 안 됨
  - 후속 Story 발의 임의적 — 사용자 / 모니터링이 발견할 때까지 silent
제안 결정:
  a) PMO retro §10.3 "별도 issue 발의" 가 권고 → 의무로 격상
  b) Story 완료 게이트에 "deferred work GitHub issue 발의" 단계 추가
  c) 또는 Story file frontmatter `deferred: [...]` 필드 — 후속 Story 발의 시 자동 link
예상 결과:
  - deferred work 추적 게이트 명시
  - 후속 Story 발의 트리거 자동화
보류 사유:
  - 본 사례 1건 — 1주 관측 권장
  - 단순 issue 발의로 즉시 해결 가능 — ADR 박제 over-engineering 위험
```

---

## 5. Cross-Story 인사이트

### 5.1 same-session 8+ Story sweep — token efficiency 누적 (갱신)

본 세션 (2026-05-09 ~ 2026-05-10 cross-day) 처리 누적:
- MCT-112 (D8 6 PR sweep)
- MCT-113 (D3 mctrader-market audit)
- MCT-114 (D1/D2 market-bithumb audit)
- MCT-115 (D1/D2/D3 mctrader-data audit) — 본 PR #28 에 finish-up 5 commit 포함
- MCT-116 (D2/D3/D5 mctrader-engine audit)
- MCT-117 (D1/D4/D5 mctrader-web audit)
- MCT-119+120 (Strategy Set Pipeline Phase 1+2 — 4071 LoC)
- **MCT-121 (Upbit 거래소 데이터 수집 — 신규 plugin repo + 4015 LoC)**

→ **8 Story + ~8000 LoC 신규 + 1 신규 plugin repo = single-session completion**. RETRO-MCT-119-120 §5.1 의 7 Story 를 8 로 확장. **codeforge ζ arc velocity 가 신규 plugin repo 부트스트랩까지 일반화**.

### 5.2 multi-repo Story 게이트 closed-loop 작동 — RETRO-MCT-119-120 §3.1 회피

| Story | repos | scope 누수 | 비고 |
|---|---|---|---|
| MCT-119 | engine + web | **발생 (web 미푸시)** | RETRO-MCT-119-120 §3.1 |
| MCT-120 | engine 단일 | N/A | — |
| **MCT-121** | **mctrader-market-upbit + mctrader-data** | **0** | **본 retro §2.1** |

→ RETRO-MCT-119-120 §3.1 권고 ("multi-repo Story 의 각 repo 별 push 검증") 가 본 Story 에 자동 반영. ADR-020 D2 후보 (RETRO-MCT-119-120 §4.1) 의 박제 시급성은 본 사례로 약화 — closed-loop 가 작동하면 ADR 박제 없이도 회피 가능 실증. **그러나 1주 관측 후 재발 시 즉시 박제 권장** (closed-loop 가 휘발성 — MEMORY trigger 의존).

### 5.3 ADR-018 D8 후보 누적 — 임계 도달 (5건)

ADR-018 D8 후보 (Optional None-guard + parse-error tuple 통합 박제) 누적 사례:

| Story | 사례 | 카테고리 |
|---|---|---|
| MCT-119+120 (RETRO §4.3) | sum Decimal 초기값 누락 | a) None-guard |
| MCT-119+120 | mark_price None guard | a) None-guard |
| MCT-119+120 | reject_reason None guard ×2 | a) None-guard |
| **MCT-121 (본 retro §3.3)** | **decimal.InvalidOperation 누락** | **b) parse-error tuple** |

→ **5건 누적, 임계 (≥3) 도달**. RETRO-MCT-119-120 §4.3 의 "1주 관측 후 결정" 임계 충족. §4.1 ADR-018 D8 후보 즉시 ArchitectAgent dispatch 권장.

### 5.4 신규 plugin repo 부트스트랩 패턴 — 첫 사례 박제

본 Story 가 mctrader 프로젝트의 **첫 신규 plugin repo 부트스트랩** (mctrader-market-bithumb 은 codeforge consumer debut 시 inception, 본 사례는 ζ arc 진입 후 첫 신규).

| 단계 | 비용 | 핵심 friction |
|---|---|---|
| GitHub repo 생성 + scaffold | ~10분 | 표준화 부재 |
| 9 src + 9 test 파일 작성 | ~3시간 | 도메인 모델 (Symbol/Timeframe) 인지 |
| 46 pytest GREEN | ~30분 | TDD 패턴 |
| **Python 환경 friction** (3.14) | **~30분** | **§3.1** |
| **site-packages stale** | **~30분** | **§3.2** |
| `pip install -e ../mctrader-market-upbit` 통합 | ~15분 | dependency resolution |
| mctrader-data 통합 (adapters / collector / cli / compose) | ~2시간 | 본 fix |

→ 신규 plugin repo 부트스트랩 총 ~7시간. 향후 신규 plugin repo (mctrader-market-binance 등) 추가 시 §4.2 표준 박제로 ~2시간 단축 가능.

### 5.5 부수 fix 카테고리 갱신 — Cat A pre-existing debt 비중 증가 패턴

| Story | Cat A (pre-existing) | Cat B (self-discovered) | 본 fix |
|---|---|---|---|
| MCT-117 | **350%** (39/11) | <10% | 11 |
| MCT-119+120 | <10% | 17% (5/29) | 29 |
| **MCT-121** | **36%** (5/8) — MCT-115 finish | **7%** (1/8) | **8** |

→ Cat A 비중이 **0% → 350% → <10% → 36% 패턴**. **현재 PR scope 가 multiple Story 잔여 청소를 흡수하는 패턴이 누적됨** — MCT-121 PR #28 이 MCT-115 ADR-018 D1/D2/D3 finish-up 5 commit 을 포함. PR 단위와 Story 단위 분리 가시화 필요.

→ RETRO-MCT-117 §4.2 + RETRO-MCT-119-120 §5.2 표준 갱신 권고:
- **Cat C 신규**: 다른 Story 의 finish-up — 본 사례 mctrader-data MCT-115 잔여
- PR 단위 commit 분포에 Story tag (예: `[MCT-115]`, `[MCT-121]`) 박제 의무화
- PR description 에 Cat A / B / C 분리 표 필수

---

## 6. 개선 제안 3건 (다음 세션 반영)

1. **ADR-018 D8 즉시 발의 (§4.1)** — None-guard + parse-error tuple 통합 박제. 누적 5건, 임계 도달, root cause 명확. ArchitectAgent dispatch 즉시 권장. RETRO-MCT-119-120 §10.2 의 "1주 관측 후 박제" 권고가 본 Story 1건 추가로 즉시 박제로 갱신.

2. **신규 plugin repo 부트스트랩 README 표준 (§4.2 Lite 옵션)** — 6 repo README 에 "부트스트랩" 섹션 표준화 (`py -3.12 -m venv`, `pip uninstall && pip install -e`, `requires-python` 명시). ADR 박제 없이 즉시 적용 가능. 다음 신규 plugin repo (mctrader-market-binance 후보) 발의 전 완료 권장.

3. **PR commit 분포 Story tag 의무화 (§5.5)** — PR description 에 commit 단위 Story 분류 표 (Cat A / B / C) 박제. PMO retro 의 cost 분석 정확도 향상. 다음 PR (MCT-122 후보) 부터 적용.

---

## 7. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| Upbit 통합 설계 (`docs/spec/`) + 구현 계획 (`docs/superpowers/plans/`) | ~10% |
| **Phase 1: mctrader-market-upbit scaffold + 9 src 작성** | **~30%** |
| Phase 1: 9 test 작성 + 46 pytest GREEN 확인 | ~10% |
| Phase 1: GitHub repo 생성 + main push | ~3% |
| Phase 2: mctrader-data adapters / collector refactor / cli / compose | ~15% |
| Phase 2: 통합 test (test_upbit_collector.py) | ~5% |
| **MCT-115 finish-up 5 commit (Cat A pre-existing)** | **~10%** |
| **Python 3.14 + site-packages 환경 friction** | **~10%** |
| PR open + admin merge + CI green 확인 | ~3% |
| Story file MCT-121.md + 본 retro 작성 | ~4% |

→ **부수 비용 (Cat A + 환경 friction) ~20%** — RETRO-MCT-119-120 ~5% 의 4배. 신규 plugin repo 부트스트랩 + 직전 Story finish-up 흡수가 비용 증폭. §4.2 README 표준 박제로 환경 friction ~10% 회피 가능.

---

## 8. 관련 ADR · MEMORY · 선행 retro

- **ADR-018**: Defensive coding patterns — D8 후보 (Optional None-guard + parse-error tuple, §4.1, 누적 5건 임계 도달)
- **ADR-019**: Parallel agent isolation — D? 후보 (신규 repo 부트스트랩 표준, §4.2)
- **ADR-020**: Story 완료 PMO 회고 게이트 — D1 자동 dispatch (본 retro trigger), D3 후보 (deferred work tracking, §4.3)
- **ADR-011**: CI standard — 본 PR #28 CI green
- **MEMORY** `feedback_admin_merge_autonomy.md`: PR #28 admin merge 자율 (8번째 same-session 사례)
- **MEMORY** `feedback_pmo_retro_mandatory.md`: 본 retro 자동 dispatch trigger
- **MEMORY** `feedback_ci_failure_auto_recovery.md`: PR #28 CI green 자동 recovery 사이클 적용
- **MEMORY** `project_codeforge_debut.md`: codeforge consumer ζ arc — 본 Story 가 ζ arc 진입 후 첫 신규 plugin repo 부트스트랩 사례
- **선행 retro**:
  - `RETRO-MCT-117.md` (§4.2 부수 fix 비율 표준 본 retro §5.5 Cat C 추가)
  - `RETRO-MCT-119-120-strategy-pipeline.md` (§3.1 multi-repo scope 누수 본 retro §2.1 회피, §4.3 None-guard 본 retro §3.3 누적)

---

## 9. Story §11 회고 pointer

`docs/stories/MCT-121.md` §11 에 본 retro pointer 박제 완료 — Story file 작성 시점에 동시 박제 (RETRO-MCT-117 §3.2 ADR-020 D1 enforcement gap 회피 패턴 적용).

---

## 10. 다음 Story 권고사항

### 10.1 즉시 follow-up (다음 세션 우선)

- **ADR-018 D8 발의 Story (가칭 MCT-122 또는 MCT-124)**:
  - ArchitectAgent dispatch — Optional None-guard + parse-error tuple 통합 박제 (§4.1)
  - 6 repo audit Story 발의 (MCT-114~117 패턴 재적용)
- **MetadataRefreshScheduler Upbit GitHub issue 발의** (§3.4):
  - mctrader-data repo 에 issue 생성 — Phase 2 Upbit metadata refresh 트래킹
  - 후속 Story 트리거로 자동 연결
- **mctrader-market-upbit README 갱신** (§4.2 Lite):
  - 부트스트랩 섹션 표준화 (`py -3.12`, editable install 패턴)
  - 6 repo 일괄 적용 권장

### 10.2 ADR 박제 (즉시 또는 1주 관측)

- **ADR-018 D8** (§4.1) — None-guard + parse-error tuple — **즉시 박제 권장** (누적 5건 임계 도달)
- ADR-019 D? 또는 ADR-011 amendment (§4.2) — 신규 repo 부트스트랩 표준 — 1주 관측 권장 (mctrader-market-binance 등 추가 사례 검증)
- ADR-020 D3 (§4.3) — Story deferred work tracking — 1주 관측 권장

### 10.3 별도 issue 발의

- **mctrader-data GitHub issue** — Upbit MetadataRefreshScheduler Phase 2 (§3.4)
- **6 repo `Decimal(...)` parse audit** — `Grep "Decimal\(" --type py` 6 repo sweep → InvalidOperation catch 누락 사례 추가 식별

### 10.4 Upbit 데이터 수집 후속 Story 트리거

본 Story Phase 1+2 완료로 다음 Story 가능:
- **Phase 3 후보**: Upbit MetadataRefreshScheduler 활성 (§3.4 deferred work)
- **Upbit OHLCV 백필 운용**: KRW+USDT 50 symbol 백필 (MCT-103 50-symbol universe 와 연동)
- **mctrader-engine Upbit 운용 테스트**: backtest mode 에서 Upbit 데이터 사용
- **추가 거래소 plugin repo**: mctrader-market-binance / -coinbase (본 Story 의 부트스트랩 패턴 horizontal 확장)

---

**작성**: PMOAgent (Story 완료 회고 감사 — ADR-020 D1 자동 dispatch · MEMORY `feedback_pmo_retro_mandatory.md`)
**작성일**: 2026-05-10
