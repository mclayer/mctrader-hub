---
story_key: MCT-15
status: phase:요구사항
component: data
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-15: mctrader-data 7-day OHLCV backfill daemon

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-15: mctrader-data daemon 7일 백필"

## 2. 도메인 해석

`mctrader-data` repo 의 첫 commit. **ADR-009 OHLCV v1 16-column canonical schema 의 reference impl** + DuckDB/Parquet/pyarrow read+write + 7-day backfill CLI. **Windows 호환성 (R2 Med-High Fail-fast)** 가 본 Story 의 가장 큰 risk source — 첫 commit 부터 path 정책 명시.

`mctrader-market` (MCT-13) 과 logical `Candle` mapping 만 정렬되면 Phase 1 brainstorm 병렬 가능. 본 Story 는 Storage 의 책임 경계 (exchange-agnostic) 를 fix.

## 3. 관련 ADR

- ADR-008 D5 (Backtest = secret 금지 / public OHLCV endpoint 만)
- ADR-009 (OHLCV v1 16-column / Hive partition / KST 1d boundary / Halt/Skip/Quarantine / lineage)
- ADR-010 (Pydantic v2 boundary / Decimal canonical)
- ADR-011 (5 required check + Windows lane CI for mctrader-data)
- 의존: MCT-13 (CandleLike Protocol mapping), MCT-14 (raw response = input source)

## 4. 관련 코드 경로

```
mctrader-data/
├── pyproject.toml
├── uv.lock
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml             # ubuntu-latest + windows-latest matrix
│   │   ├── phase-gate-mergeable.yml
│   │   └── phase-label-invariant.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
├── src/mctrader_data/
│   ├── __init__.py
│   ├── schema.py              # ADR-009 v1 16-column Pydantic + PyArrow schema
│   ├── path.py                # resolve_data_root() + partition path derivation
│   ├── storage.py             # write/read API (Parquet/DuckDB)
│   ├── policy.py              # Halt/Skip/Quarantine + trigger detection
│   ├── lineage.py             # _lineage.json + Parquet file-level metadata
│   ├── backfill.py            # one-shot backfill orchestration
│   ├── cli.py                 # `mctrader-data backfill ...`
│   └── fixtures.py            # canonical OHLCV fixture (Linux + Windows)
└── tests/
    ├── test_schema.py
    ├── test_path_normalization.py    # Linux + Windows
    ├── test_roundtrip.py             # Parquet write→read equality
    ├── test_partition_discovery.py   # Hive partition scan (Windows lane critical)
    ├── test_policy.py                # Halt/Skip/Quarantine per trigger
    ├── test_lineage.py
    ├── test_idempotency.py
    └── test_cli_dry_run.py
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ + Pydantic v2 + DuckDB + PyArrow + pyarrow.parquet
- mctrader-market `>=0.1,<0.2` (CandleLike Protocol + Symbol + Timeframe)
- **`Path.resolve(strict=False).as_posix()`** = forward-slash normalize (Windows)
- DuckDB `read_parquet(..., hive_partitioning=true)`
- ISO-8601 UTC datetime
- pyright strict + pytest + Windows lane CI (ADR-011)

## 7. 설계 서사 (요약)

### 7.1 Storage path layout (A1 결정)

**ADR-009 D2 authoritative form**:
```
{root}/market/ohlcv/schema_version=ohlcv.v1/exchange={ex}/symbol={sym}/timeframe={tf}/year={Y}/month={M}/date={D}/*.parquet
```

**Root resolution priority** (`path.py::resolve_data_root()`):
1. CLI `--root` flag (highest)
2. ENV `MCTRADER_DATA_ROOT`
3. Repo-local `data/parquet/` (fallback default)

**Path normalization rules** (Windows 호환):
- 모든 path = `pathlib.Path(...).resolve(strict=False)`
- DuckDB scan path = `Path.as_posix()` (forward-slash, Windows drive letter `C:` 보존)
- Hive `key=value` segment 의 `=` 는 DuckDB / PyArrow native 지원 (escape 불필요)
- partition file naming = `part-{snapshot_id}.parquet` — short name (long path 회피)
- Long path > 260 chars 회피 — root path 절대 길이 제한 docs

**File locking 정책**:
- Write = single writer process (CLI 1 instance only)
- Read = DuckDB read-only connection (`read_only=True`)
- DuckDB `.wal` lock 분리: dataset (Parquet files) ≠ catalog (`.duckdb` 별도)

**`.gitignore` 의무**: `data/parquet/` (repo-local fallback 사용 시 데이터 commit 회피).

### 7.2 DuckDB query interface (A2 결정)

**Public read API** = `Iterable[CandleLike]`:

```python
from mctrader_market.candle import CandleLike
from mctrader_market.types import Symbol, Timeframe

def scan_candles(
    *,
    exchange: str,
    symbol: Symbol,
    timeframe: Timeframe,
    start: datetime,         # UTC inclusive
    end: datetime,            # UTC exclusive
    snapshot_id: str | None = None,
    root: Path | None = None,
) -> Iterable[CandleLike]: ...
```

**내부 구현**:
- DuckDB `read_parquet({root_glob}, hive_partitioning=true)`
- WHERE filter pushdown (timeframe / exchange / symbol / ts_utc range)
- ORDER BY ts_utc ASC (ADR-009 의무)
- materialize → `CandleModel` instance (boundary validation)

**보조 API** (diagnostic, non-public-contract):
- `to_arrow() → pyarrow.Table`
- `to_dataframe() → pd.DataFrame` (mctrader-engine 측 변환 권장)

**Snapshot 정책**:
- `snapshot_id=None` → 동일 timestamp 의 latest hash 만 serve (duplicate same-hash idempotent)
- `snapshot_id="..."` → 특정 snapshot 만 (replay / audit)

### 7.3 Halt / Skip / Quarantine 정책 (A3 결정)

**Trigger 별 default policy**:

| Trigger | Default policy | 이유 |
|---|---|---|
| timestamp gap (1h 단위 missing) | **Halt** | 첫 commit AC 에서 gap 즉시 surface |
| duplicate same-hash | **Skip** (idempotent, internal) | re-run 안전 |
| duplicate different-hash | **Quarantine** + non-zero exit | closed bar revision / exchange correction 가능성 |
| value out of range (negative price/volume, low > high, open 범위 벗어남) | **Quarantine** | 일부 row 보존 + 분석 가능 |
| schema mismatch | **Halt** | adapter version drift 방지 |
| exchange API error (rate limit / 5xx) | bounded retry → **Halt** | 재시도 후 surface |

**CLI surface**:
- `--policy halt` (default — 보수적)
- `--policy quarantine` (gap + value out of range = quarantine 으로)
- `--policy skip` = test-only hidden option (duplicate same-hash 의 internal action 만 사용)

**Quarantine layout**:
```
{root}/market/_quarantine/ohlcv/schema_version=ohlcv.v1/exchange={ex}/symbol={sym}/timeframe={tf}/year={Y}/month={M}/date={D}/snapshot_id={snap}/
```

각 quarantine record = JSONL 또는 Parquet:
- `original_payload` (raw)
- `normalized_candidate` (adapter output)
- `reason_code` (HALT_GAP / VALUE_OUT_OF_RANGE / DUP_DIFFERENT_HASH / ...)
- `fetched_at_utc`
- `response_hash`
- `adapter_name + adapter_version`

**Lifecycle**: first commit = manual cleanup only (no auto-expire / no auto-promote).

### 7.4 Lineage 메타데이터 (A4 결정)

**ADR-009 16-column canonical = freeze** (lineage column 추가 X). Lineage = sidecar / file metadata 로 분리.

**Per-batch granularity** (per-candle = bloat, per-file = batch alignment 자연):

**Layer 1 — Parquet file-level metadata** (PyArrow `Table.replace_schema_metadata`):
- `mctrader.lineage.snapshot_id`
- `exchange`
- `endpoint`
- `request_params_hash`
- `fetched_at_utc`
- `response_hash`
- `adapter_name`
- `adapter_version`

**Layer 2 — `_lineage.json` per snapshot directory**:
```
{root}/market/ohlcv/.../date={D}/_lineage.json
```
- snapshot_id immutable
- 사람이 읽기 쉬운 JSON
- 동일 partition 의 multiple snapshot 별 file
- idempotency 검증 = snapshot_id 비교

**Layer 3 (defer)** — DuckDB `lineage_log` table: 검색 성능이 필요할 때 추가. 첫 commit 미포함.

### 7.5 Backfill CLI (A5 결정)

**Base command**:
```
mctrader-data backfill --exchange bithumb --symbol KRW-BTC --tf 1h --days 7
```

**Option set**:

| Option | 의무 | Default | 설명 |
|---|---|---|---|
| `--exchange` | 필수 | — | bithumb (현재) — Symbol.from_string 검증 |
| `--symbol` | 필수 | — | "KRW-BTC" (canonical "{quote}-{base}") |
| `--tf` | 필수 | — | Timeframe StrEnum |
| `--days` | 둘 중 1 | — | `--start/--end` 와 mutually exclusive |
| `--start` | 둘 중 1 | — | ISO 8601 UTC inclusive |
| `--end` | option | last closed candle boundary | ISO 8601 UTC exclusive. 생략 = 1h → UTC hour boundary / 1d → KST close boundary |
| `--policy` | option | `halt` | `halt` 또는 `quarantine`. `skip` = hidden test-only |
| `--dry-run` | flag | False | fetch X, plan + expected partition path 출력 |
| `--resume` | flag | False | 이전 부분 실패 batch 재시작 (snapshot_id 기준 idempotent) |
| `--root` | option | — | storage root override (resolve_data_root priority 1) |

**`--days` + `--start/--end` 동시** = error (deterministic window 1 source only).

**`--end` 생략 시 last closed boundary**:
- `1h` → `now_utc - now_utc % 1h` (현재 시간 직전 hour 경계)
- `1d` → KST 자정 (`now_kst.date() at 00:00 KST → ts_utc`)
- 부분 candle (current bar) 미포함

**Idempotency**:
- Key = `(exchange, symbol, timeframe, ts_utc)`
- 동일 hash → skip (idempotent, exit 0)
- 다른 hash → quarantine + non-zero exit
- `--resume` = 마지막 successful batch 의 snapshot_id 부터 재시작

**Rate limit / retry**:
- Bounded exponential backoff + jitter (max 3 retries)
- 모두 실패 = halt (CLI 종료 코드 비-0)

### 7.6 Normalization owner — Hybrid (A6 결정)

**Adapter (MCT-14) 책임**:
- raw HTTP endpoint call + retry classification
- raw response fixture 보관
- Bithumb symbol `BTC_KRW` → `Symbol(base="BTC", quote="KRW")` (ADR-009 D3)
- timezone 해석 + UTC 변환
- Decimal parse (string → Decimal38_18)
- column rename (Bithumb mapping → 16-column canonical)
- `value` 부재 = adapter 가 quarantine 표시 (ADR-009 D3 Bithumb)
- output = `CandleLike` instance (Pydantic CandleModel validation 통과)

**Storage (MCT-15) 책임**:
- `schema_version == "ohlcv.v1"` 검증
- 16 column 존재 + Decimal precision/scale (Decimal38_18) 검증
- UTC-aware `ts_utc` 검증 (naive reject + non-UTC reject)
- Timeframe boundary alignment (1h → UTC hour boundary, 1d → KST close)
- OHLC range validation (low ≤ open/close ≤ high, volume ≥ 0)
- Duplicate detection
- Partition path derivation
- Lineage persistence (Parquet metadata + `_lineage.json`)

**경계 원칙**: Storage 는 raw Bithumb JSON 모름. Quarantine 에 raw payload 저장 시 = adapter-provided raw hash + raw payload reference (string blob), 단 raw schema parsing X.

### 7.7 Test / contract validation 전략 (A7 결정)

**Both lane (Linux + Windows)**:
- Schema validation (16-column, Decimal38_18, UTCDateTime)
- DuckDB / Parquet roundtrip (write → read → equality, Decimal exactness 보장)
- Halt/Skip/Quarantine trigger unit test (per trigger × per policy)
- Backfill idempotency (same command 2 회 = same snapshot)
- Lineage sidecar read/write (Parquet file-level + `_lineage.json`)
- CLI `--dry-run` parsing
- MCT-13 CandleLike Protocol contract test (pyright + runtime isinstance)

**Windows lane only** (R2 Fail-fast):
- Path root `C:\...` 형태 → DuckDB scan path forward-slash normalize
- Hive `key=value` glob discovery (Windows path separator vs DuckDB)
- Long-ish path smoke (≥ 200 chars)
- Concurrent read-only DuckDB connection smoke

**Defer**:
- Hypothesis property-based test (random Decimal / timestamp) → 후속 Story
- Pure mocked unit only test → R2 Fail-fast 만족 X (실제 file 의무)

**MCT-14 raw fixture 의존**: storage→adapter 양방향 contract test 는 별도 optional test (recorded MCT-14 fixture). 본 Story 의 의무 = MCT-13 CandleLike 만 의존.

### 7.8 Pyproject + 첫 commit standard

```toml
[project]
name = "mctrader-data"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
  "mctrader-market>=0.1,<0.2",
  "pydantic>=2,<3",
  "duckdb>=1,<2",
  "pyarrow>=17",
  "click>=8",  # CLI
]

[project.scripts]
mctrader-data = "mctrader_data.cli:main"
```

**CI matrix** (ADR-011 D2 + Windows lane):
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python: ["3.11"]
  fail-fast: false
```

5 required check (phase-gate / lint / type / test / coverage 60%) + Windows lane = 의무 (R2 Fail-fast).

### 7.9 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| WebSocket / streaming ingestion | ✗ | MCT-12 = REST polling only / future Epic |
| 다중 거래소 (Upbit / Binance / ...) | ✗ | MCT-12 Bithumb only / future Epic 시 adapter 추가 + storage 변경 X (Hybrid normalization) |
| Live mode realtime ingestion | ✗ | Backtest only (ADR-002 / MCT-12 out-of-scope) |
| Streamlit live concurrent DuckDB read | ✗ | finalized equity_curve.csv read only (MCT-12 out-of-scope, MCT-17) |
| DuckDB `lineage_log` table | ✗ (defer) | 검색 성능 필요 시 후속 |
| Hypothesis property-based test | ✗ (defer) | 첫 commit 비용 |
| Auto-cleanup quarantine | ✗ | manual cleanup only |
| Multi-strategy / Multi-symbol portfolio | ✗ | 본 Story = single (exchange, symbol, timeframe) backfill |

### 7.10 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | `pyproject.toml` `version = "0.1.0"` + Python 3.11+ + mctrader-market `>=0.1,<0.2` | uv sync --frozen |
| AC2 | 5 required check green (Linux + Windows lane) | CI matrix |
| AC3 | `scan_candles(exchange="bithumb", symbol=Symbol("BTC","KRW"), tf=H1, start=T-7d, end=T)` 가 168 candle 반환 + `Iterable[CandleLike]` 타입 | pytest |
| AC4 | DuckDB / Parquet roundtrip = `ts_utc` + Decimal38_18 exactness 보장 | pytest |
| AC5 | Hive partition discovery: `{root}/market/ohlcv/schema_version=ohlcv.v1/exchange=bithumb/symbol=KRW-BTC/timeframe=1h/year=2026/month=05/date=01/*.parquet` 가 Linux + Windows 모두 발견 | pytest (Windows lane critical) |
| AC6 | timestamp gap → halt / duplicate same-hash → skip / duplicate different-hash → quarantine + non-zero / value out of range → quarantine / schema mismatch → halt | pytest (per trigger × per policy) |
| AC7 | Backfill 2 회 실행 = 같은 snapshot_id (idempotent) | pytest |
| AC8 | Lineage = Parquet file-level metadata 읽기 + `_lineage.json` 읽기 모두 동일 8 field | pytest |
| AC9 | CLI `--dry-run` 가 expected partition path + plan 출력 (실제 fetch X) | pytest |
| AC10 | naive datetime / non-UTC datetime input = boundary reject | pytest |

### 7.11 Codex 적용

7/7 area 채택 (Storage path / DuckDB interface / 부분 실패 정책 / Lineage / CLI / Hybrid normalization / Test 전략). ADR-009 partition layout 의 authoritative form 으로 freeze (year/month/**date** 3단, `day` 아님). ADR conflict 0/7.

## 8-11

(Phase 2 = `mctrader-data` repo 생성 + 첫 commit + AC1~AC10 통과 PR. MCT-13 Phase 2 merge 의 logical Candle mapping 정렬 후 시작.)
