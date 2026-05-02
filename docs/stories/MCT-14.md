---
story_key: MCT-14
status: phase:요구사항
component: market-bithumb
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-001, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-14: mctrader-market-bithumb adapter (httpx + raw fixture + Bithumb mapping)

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-14: mctrader-market-bithumb adapter (`get_candles()`)"

## 2. 도메인 해석

`mctrader-market-bithumb` repo 의 첫 commit. ADR-001 의 첫 거래소 (Bithumb) public OHLCV endpoint adapter. **Public-only / Backtest-only** (ADR-008) — secret 도입 절대 금지.

ADR-009 D3 의 Bithumb-specific normalization (`BTC_KRW` → `KRW-BTC` / array order `[ts, open, close, high, low, volume]` / `value` 부재 quarantine) 의 reference impl.

MCT-13 freeze (CandleLike Protocol + Symbol value object + Timeframe StrEnum + Decimal38_18 + UTCDateTime) 후 시작.

## 3. 관련 ADR

- ADR-001 (거래소 = Bithumb#1)
- ADR-008 D5 (Backtest = secret 금지) + D9 (gitleaks 의무)
- ADR-009 D3 (Bithumb mapping) + D5 (Halt/Skip/Quarantine)
- ADR-010 (Pydantic v2 boundary / `aiohttp>=3.13,<4` OR `httpx>=0.27,<1`)
- ADR-011 (5 required check / Network test = mocked HTTP / replay fixture default / scheduled live job only)
- 의존: MCT-13 (이미 Phase 1 merge — `mctrader-market` 0.1.0)

## 4. 관련 코드 경로

```
mctrader-market-bithumb/
├── pyproject.toml
├── uv.lock
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # mocked HTTP only (default)
│   │   ├── ci-live.yml             # scheduled weekly + manual workflow_dispatch
│   │   ├── phase-gate-mergeable.yml
│   │   └── phase-label-invariant.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
├── src/mctrader_market_bithumb/
│   ├── __init__.py
│   ├── client.py                   # BithumbHttpClient (httpx.Client) + RateLimitConfig
│   ├── endpoints.py                # path allowlist + URL builder
│   ├── mapping.py                  # IDX_* constants + normalize_row() + symbol_to_path()
│   ├── adapter.py                  # BithumbCandleProvider impl (CandleProvider Protocol)
│   ├── exceptions.py               # BithumbApiError / RateLimitedError / SchemaMismatchError / InsufficientCoverageError / ValueAbsenceQuarantine
│   ├── secret_guard.py             # public-only enforcement (header + URL allowlist + import boundary)
│   └── _live_capture.py            # scheduled job 의 fixture 재캡처 helper
└── tests/
    ├── fixtures/bithumb/
    │   └── public_candlestick_BTC_KRW_1h.json    # raw endpoint response (raw symbol BTC_KRW)
    ├── test_mapping.py             # IDX 순서 + Decimal precision + symbol mapping
    ├── test_client_retry.py        # mock HTTP 5xx/timeout/429
    ├── test_adapter_contract.py    # CandleLike Protocol satisfaction
    ├── test_secret_guard.py        # forbidden header + URL allowlist + import boundary
    ├── test_value_absence.py       # quarantine signal
    ├── test_insufficient_coverage.py
    └── test_policy_imports.py      # repo lint policy: os.getenv/os.environ/Authorization
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ + httpx>=0.27,<1 (sync) + Pydantic v2 + decimal
- mctrader-market `>=0.1,<0.2` (CandleLike + Symbol + Timeframe + Decimal38_18 + UTCDateTime)
- Bithumb public endpoint: `GET https://api.bithumb.com/public/candlestick/{order_currency}_{payment_currency}/{chart_intervals}`
- Bithumb response: array of `[timestamp_ms, open, close, high, low, volume]` (close at index 2 — non-standard order)
- Bithumb rate limit (공식): public 90 calls/sec / 보수적 30 calls/sec 권장
- pyright strict + pytest + ADR-011 5 required check + gitleaks

## 7. 설계 서사 (요약)

### 7.1 HTTP library = httpx 0.27 sync (A1 결정)

**채택**: `httpx>=0.27,<1` sync client.

**근거**:
- MCT-12 = REST polling only / Backtest only → sync 충분
- mocked transport injection 단순 (`httpx.MockTransport`)
- async 전환 가능 구조 (`httpx.AsyncClient` 동일 API)
- aiohttp 는 future streaming Epic (Paper/Live realtime ingestion) 시 재검토
- requests = ADR-010 dependency set 밖 → 제외

**구조**:
```python
class BithumbHttpClient:
    def __init__(
        self,
        client: httpx.Client | None = None,    # mocked transport injection
        rate_limit: RateLimitConfig = RateLimitConfig(rate_per_second=30, burst=30),
        timeout: float = 10.0,
        retry_config: RetryConfig = RetryConfig(max_attempts=3),
    ): ...
```

### 7.2 Rate limit + retry 정책 (A2 결정)

**Rate limit** = process-local global token bucket, default `30 requests/sec` (Bithumb public 90/sec 의 33% 보수적):

```python
@dataclass
class RateLimitConfig:
    rate_per_second: int = 30
    burst: int = 30
```

Multi-process 보장 X (process-local). Solo dev / single CLI process 가정 충분.

**Retry classification** (책임 분리 — Adapter = transient / Storage = policy):

| HTTP / Error | Adapter retry? | Adapter classification |
|---|:-:|---|
| Timeout / Connection error | ✓ | transient |
| HTTP 5xx | ✓ | transient |
| HTTP 429 | ✗ | `RateLimitedError` (storage policy 결정) |
| HTTP 401 / 403 | ✗ | `BithumbApiError` (secret guard violation 의심) |
| HTTP 404 | ✗ | `BithumbApiError` (endpoint / symbol invalid) |
| 200 + JSON parse error | ✗ | `SchemaMismatchError` |

**Backoff**:
- max_attempts = 3
- exponential 0.25s / 0.5s / 1.0s
- jitter = ±20% (deterministic test 위해 random provider 주입 가능)

**MCT-15 와의 align**: MCT-15 의 backfill daemon 도 max 3 retry — adapter + storage 양쪽 retry = 중복 회피. 권장: adapter retry 만 적용, storage 는 typed exception 받아서 policy 결정 (no second retry layer).

### 7.3 Bithumb normalization (A3 결정)

**ADR-009 D3 explicit mapping table**:

```python
# Bithumb response array order — CRITICAL: close at index 2, NOT high
IDX_TS_MS = 0
IDX_OPEN = 1
IDX_CLOSE = 2     # NOTE: Bithumb position 2 = close, 표준 OHLCV 와 다름
IDX_HIGH = 3
IDX_LOW = 4
IDX_VOLUME = 5

ROW_LENGTH = 6

def normalize_row(row: list, *, exchange: str, symbol: Symbol, timeframe: Timeframe) -> CandleModel:
    if len(row) != ROW_LENGTH:
        raise SchemaMismatchError(f"expected {ROW_LENGTH} fields, got {len(row)}")
    return CandleModel(
        ts_utc=epoch_ms_to_utc(row[IDX_TS_MS]),
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        open=Decimal(str(row[IDX_OPEN])),    # str → Decimal38_18 보존 (float 우회)
        high=Decimal(str(row[IDX_HIGH])),
        low=Decimal(str(row[IDX_LOW])),
        close=Decimal(str(row[IDX_CLOSE])),
        volume=Decimal(str(row[IDX_VOLUME])),
        value=None,  # Bithumb response 부재 → quarantine signal (7.6)
        # source_ingested_at / data_snapshot_id / data_hash = MCT-15 Storage 책임
    )
```

**Symbol mapping** (pure function):
```python
def symbol_to_bithumb_path(symbol: Symbol) -> str:
    # Symbol(base="BTC", quote="KRW") → "BTC_KRW"
    return f"{symbol.base}_{symbol.quote}"

def bithumb_path_to_symbol(path: str) -> Symbol:
    # "BTC_KRW" → Symbol(base="BTC", quote="KRW")
    base, _, quote = path.partition("_")
    if not base or not quote:
        raise ValueError(f"invalid Bithumb path: {path}")
    return Symbol(base=base, quote=quote)
```

**Timeframe mapping** (Bithumb chart_intervals):
```python
TIMEFRAME_TO_BITHUMB = {
    Timeframe.M1: "1m",
    Timeframe.M5: "5m",
    Timeframe.M15: "15m",  # Bithumb 의 30m 은 mctrader 미지원
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",    # Bithumb 의 6h / 12h 는 mctrader 미지원
    Timeframe.D1: "24h",   # Bithumb 24h = KST close 기준 (verify 필요, MCT-15 boundary alignment)
}
```

`24h` (D1) 의 KST/UTC ambiguity = MCT-15 의 timeframe boundary alignment 가 검증.

**16-column 의무 분담**:
- Adapter (본 Story) = `ts_utc`, `exchange`, `symbol`, `timeframe`, `open/high/low/close`, `volume` (9 column)
- Storage (MCT-15) = `source_ingested_at`, `data_snapshot_id`, `data_hash` + 추가 메타 (=> 16 column)
- Adapter 가 invent 하지 않음

### 7.4 Raw fixture 위치 + 형식 (A4 결정)

**Format** = raw JSON (사람 diff 친화 + git 친화):

**Path**:
```
tests/fixtures/bithumb/public_candlestick_BTC_KRW_1h.json
```

**Filename convention** = `{endpoint_path_with_underscore}_{raw_symbol}_{timeframe}.json`. raw symbol = Bithumb path form (`BTC_KRW`, not canonical `KRW-BTC`).

**Content** = Bithumb response body 그대로 (raw array order 보존). Top-level envelope (status / data wrapper) 도 그대로 — adapter 가 parsing.

**Update workflow** (scheduled / manual only — ADR-011 D3):
1. weekly scheduled job (`ci-live.yml` workflow) 또는 manual `workflow_dispatch`
2. `_live_capture.py` 가 Bithumb 실제 endpoint 호출 → 새 raw JSON
3. 인간 reviewer 가 git diff 검토 (row 길이 / timestamp unit / status field shape 변화)
4. 새 fixture commit → CI default lane 의 mocked test 통과 확인

**CI default lane = 절대 live API call X** (모두 mocked transport + raw fixture replay).

**Top-level envelope** = `[VERIFY]` 첫 commit 시 실제 fixture 캡처로 확정 (예: `{"status": "0000", "data": [[ts, open, close, high, low, volume], ...]}`).

### 7.5 CandleProvider impl (A5 결정 — eager single-call)

**`get_candles()` impl**:

```python
class BithumbCandleProvider:
    def __init__(self, client: BithumbHttpClient | None = None):
        self._client = client or BithumbHttpClient()

    def get_candles(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: datetime,    # UTC inclusive
        end: datetime,      # UTC exclusive ([start, end))
    ) -> list[CandleModel]:
        path = symbol_to_bithumb_path(symbol)
        chart_interval = TIMEFRAME_TO_BITHUMB[timeframe]
        raw = self._client.get_candlestick(path, chart_interval)
        rows = self._parse_envelope(raw)
        candles = [
            normalize_row(row, exchange="bithumb", symbol=symbol, timeframe=timeframe)
            for row in rows
        ]
        candles.sort(key=lambda c: c.ts_utc)
        # filter to [start, end) half-open interval
        filtered = [c for c in candles if start <= c.ts_utc < end]
        # coverage check
        self._verify_coverage(filtered, start, end, timeframe)
        return filtered
```

**Coverage 검증** = response window < requested window 시:
```python
def _verify_coverage(candles, start, end, timeframe):
    if not candles:
        raise InsufficientCoverageError(f"empty result for [{start}, {end})")
    if candles[0].ts_utc > start + timeframe.delta:
        raise InsufficientCoverageError(f"first candle {candles[0].ts_utc} > start + {timeframe.delta}")
    if candles[-1].ts_utc < end - timeframe.delta:
        raise InsufficientCoverageError(f"last candle {candles[-1].ts_utc} < end - {timeframe.delta}")
```

**Pagination = 미구현** (defer). MCT-12 default 7-day 1h = 168 candle ≪ Bithumb 1500 single response. Bithumb `count` / `to` query param 지원 여부 = `[VERIFY]` (현재 facts 미명시).

**Interval semantics** = `[start, end)` half-open (MCT-13 7.8 align).

**Silent partial result 금지**: response 가 requested window 의 일부만 cover 시 `InsufficientCoverageError` raise — storage policy (Halt/Quarantine) 가 결정.

### 7.6 `value` 부재 quarantine signal (ADR-009 D3 align)

Bithumb response 에 거래대금 (`value`) field 부재. ADR-009 D3 = "value 부재 = quarantine".

**Adapter 책임**: `value=None` silently 가 아닌 typed quarantine signal:

```python
class CandleModel(BaseModel):
    # ...
    value: Decimal38_18 | None
    quarantine_reason: str | None = None  # adapter 가 set: "VALUE_ABSENCE" 등

# Bithumb adapter 의 normalize_row():
candle.value = None
candle.quarantine_reason = "VALUE_ABSENCE_BITHUMB"  # MCT-15 가 quarantine partition 에 격리
```

대안 (다른 path): `ValueAbsenceQuarantine` exception → caller (MCT-15) 가 catch + quarantine 처리. 본 Story 는 **field-level signal 채택** (response stream 처리 친화 — 일부 row 만 부재 가능).

### 7.7 Public-only enforcement (A6 결정 — 3 layer)

**Layer 1 — URL allowlist** (HTTP boundary):
```python
class BithumbHttpClient:
    BASE_URL = "https://api.bithumb.com/public"
    ALLOWED_PATHS = frozenset({"/candlestick/{order}_{payment}/{interval}"})

    def get_candlestick(self, path, interval):
        # 임의 URL 또는 private path 호출 generic API 미제공
        # path = candlestick endpoint 만
```

**Layer 2 — Runtime header guard** (request 직전):
```python
FORBIDDEN_HEADERS = frozenset({
    "Authorization", "Api-Key", "Api-Sign",
    "X-BITHUMB-Api-Key", "X-BITHUMB-Api-Sign", "X-BITHUMB-Api-Nonce",
})

def _assert_no_secret_headers(headers: dict):
    forbidden_present = set(headers.keys()) & FORBIDDEN_HEADERS
    if forbidden_present:
        raise PublicOnlyViolationError(
            f"forbidden header present: {forbidden_present} (ADR-008 D5: Backtest = secret 금지)"
        )
```

**Layer 3 — Repo policy lint test** (`tests/test_policy_imports.py`):
- source tree 검사: `os.getenv` / `os.environ` / `Authorization` 문자열 사용 X (allowlist 기반)
- import 검사: `onepassword` / `op` / `cryptography` (HMAC sign 의심) 의존 미설치
- gitleaks = pre-commit + CI 양쪽 의무

**1Password CLI dependency 절대 X** — 본 repo 는 public-only.

### 7.8 Test / contract validation (A7 결정 — 4 layer)

**Layer 1 — Static type** (pyright strict):
- `BithumbCandleProvider` 가 MCT-13 `CandleProvider` Protocol 만족

**Layer 2 — Runtime structural** (`isinstance(adapter, CandleProvider)`):
- runtime smoke

**Layer 3 — Boundary data** (Pydantic v2):
- `CandleModel(...)` validation = Decimal38_18 + UTCDateTime + non-empty
- `TypeAdapter(CandleModel).validate_python(raw_dict)` (downstream consume)

**Layer 4 — Bithumb-specific contract**:

| 검증 | 입력 | 기대 |
|---|---|---|
| IDX order | fixture row `[ts_ms, open, close, high, low, volume]` | canonical OHLC field 정확 매핑 (close at IDX 2, high at IDX 3) |
| Symbol mapping | `Symbol(base="BTC", quote="KRW")` ↔ `"BTC_KRW"` | roundtrip equality |
| Decimal precision | string `"50000000.123456789012345678"` → Decimal | precision = 18 보존, float 미사용 |
| Timezone | `timestamp_ms` (UTC epoch) → `datetime` | `tzinfo == timezone.utc` |
| Retry | mock HTTP 5xx → retry → 200 | success after 1~2 retry |
| Retry | mock HTTP 429 | `RateLimitedError` raise (no auto retry) |
| Schema mismatch | row 길이 != 6 | `SchemaMismatchError` raise |
| Coverage | response 의 ts_utc 범위 < requested | `InsufficientCoverageError` raise |
| Value absence | every row | `quarantine_reason="VALUE_ABSENCE_BITHUMB"` set |
| Secret guard | request with `Authorization` header | `PublicOnlyViolationError` raise |
| Policy import | `os.getenv` / `Authorization` 사용 | test fail (allowlist) |

**Scheduled live job** (`ci-live.yml` — required check 아님):
- weekly KST 새벽 1 회
- Bithumb live API 호출 → fixture 재캡처
- 새 fixture vs 기존 fixture diff
- diff 발견 시 GitHub issue auto-create (review trigger)

### 7.9 Pyproject + 첫 commit standard

```toml
[project]
name = "mctrader-market-bithumb"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
  "mctrader-market>=0.1,<0.2",
  "httpx>=0.27,<1",
  "pydantic>=2,<3",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "pyright>=1.1",
  "ruff>=0.6",
]
# 1Password CLI / cryptography 의존 절대 X (ADR-008)
```

**CI** (mocked default lane):
- ubuntu-latest + python 3.11
- 5 required check (phase-gate / lint / type / test / coverage 60%)
- network = mocked transport + raw fixture replay only

**CI live** (`ci-live.yml`):
- schedule: weekly KST 새벽
- workflow_dispatch (manual)
- non-required (signal only)

### 7.10 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| Authenticated endpoint (private API) | ✗ | ADR-008 D5 Backtest secret 금지 |
| 1Password CLI dependency | ✗ | 위 |
| WebSocket streaming | ✗ | MCT-12 REST polling only / future Paper/Live Epic |
| OrderClient / BrokerClient | ✗ | MCT-13 미정의 + ADR-002 engine TradeExecutor 책임 |
| Pagination | ✗ (defer) | MCT-12 7-day 1h = 168 candle ≪ 1500 single response |
| Bithumb 30m / 6h / 12h timeframe | ✗ | mctrader Timeframe StrEnum 미지원 |
| 한국 외 거래소 | ✗ | 본 repo = Bithumb only |
| Async client | ✗ (future) | sync 충분 / future streaming Epic 시 재검토 |

### 7.11 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | `pyproject.toml` `version = "0.1.0"` + httpx 0.27 + 1Password CLI 의존 X | uv sync --frozen + dependency tree |
| AC2 | 5 required check green (mocked default lane) | CI |
| AC3 | `BithumbCandleProvider` 가 MCT-13 `CandleProvider` Protocol 만족 (pyright + isinstance) | pytest |
| AC4 | IDX 순서 검증: fixture 1 row → `close` at IDX 2, `high` at IDX 3 정확 매핑 | pytest |
| AC5 | Symbol roundtrip: `Symbol("BTC","KRW") ↔ "BTC_KRW"` | pytest |
| AC6 | Decimal precision: `"50000000.123456789012345678"` → Decimal38_18 보존 (float 우회) | pytest |
| AC7 | Timezone: `timestamp_ms` UTC epoch → `datetime` with `tzinfo=timezone.utc` | pytest |
| AC8 | Retry classification: 5xx → retry / 429 → RateLimitedError / 4xx → BithumbApiError / parse error → SchemaMismatchError | pytest (mock HTTP) |
| AC9 | Rate limit token bucket = 30/sec (deterministic test with injected clock) | pytest |
| AC10 | Coverage check: response 일부 only → `InsufficientCoverageError` | pytest |
| AC11 | Value absence: every row → `quarantine_reason="VALUE_ABSENCE_BITHUMB"` | pytest |
| AC12 | Secret guard: forbidden header → `PublicOnlyViolationError` | pytest |
| AC13 | Policy import lint: `os.getenv` / `Authorization` source 사용 X | pytest (`test_policy_imports.py`) |
| AC14 | gitleaks (pre-commit + CI) green | CI |
| AC15 | scheduled live job (`ci-live.yml`) workflow 등록 (실행 의무 X) | repo settings |

### 7.12 Codex 적용

7/7 area 채택 (HTTP library / Rate limit + retry / Bithumb normalization / Raw fixture / CandleProvider impl / Public-only enforcement / Test 전략). ADR conflict 0/7.

## 8-11

(Phase 2 = `mctrader-market-bithumb` repo 생성 + 첫 commit + AC1~AC15 통과 PR. MCT-13 Phase 2 merge 후 시작.)
