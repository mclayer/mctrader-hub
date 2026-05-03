---
story_key: MCT-20
status: phase:요구사항
component: data
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-009, ADR-010, ADR-011
---

# MCT-20: mctrader-data Paper mode write-side (mode=paper partition + lineage extension)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Paper-generated OHLCV separate partition + lineage extension"

## 2. 도메인 해석

`mctrader-data` 0.1.0 의 Paper write-side 확장. **ADR-009 v1 16-column schema 변경 X** — `mode` 정보는 partition path + lineage metadata 만 표현. canonical historical data 와 격리.

## 3. 관련 ADR

- ADR-009 (16-column schema immutable, Hive partition pattern amendment 필요)
- ADR-010 (Pydantic v2 boundary / Decimal canonical)
- ADR-011 (5 required check + Linux+Windows CI matrix)
- 의존: MCT-12 freeze (mctrader-data 0.1.0)

## 4. 관련 코드 경로

```
mctrader-data/src/mctrader_data/
├── paper_storage.py         # 별도 module (paper_storage.write_paper_candles)
├── paper_lineage.py         # WebSocket batch hash + adapter naming extension
└── path.py (extend)         # mode segment 추가 derive_partition_path

scan_candles signature extension (storage.py):
    scan_candles(*, exchange, symbol, timeframe, start, end, root,
                 mode: Literal["historical", "paper"] | Sequence[str] = "historical")

tests/
├── test_paper_storage.py
├── test_paper_lineage.py
├── test_scan_mode_filter.py    # legacy no-mode + historical + paper 격리
└── test_paper_partition_windows.py  # Windows lane Hive discovery
```

## 5-6. 요구사항 / 외부 지식

- ADR-009 v1 16-column 변경 X (Pydantic OhlcvRow 동일)
- DuckDB Hive partition discovery (`hive_partitioning=true`)
- Linux+Windows CI matrix (path safety)
- mctrader-market `>=0.1,<0.2` (Symbol + Timeframe + Decimal38_18)

## 7. 설계 서사 (Codex 합성)

### 7.1 Partition path = `schema_version=ohlcv.v1/mode=paper/exchange=...` (A1)

**채택**: option (a) `schema_version` 다음 위치.

```
{root}/market/ohlcv/schema_version=ohlcv.v1/mode={historical|paper}/exchange={ex}/symbol={sym}/timeframe={tf}/year=Y/month=M/date=D/*.parquet
```

**근거**:
- DuckDB Hive partition discovery 가 `mode` 를 명확한 partition column 으로 인식
- exchange/symbol/timeframe 이하 = historical/paper 공유 (logical dataset 일관)
- exchange 다음 (option b) = mode 가 exchange 뒤 숨어 default scan 실수 위험
- 별도 root (option c/d) = ADR-009 baseline path 와 멀어짐, dataset naming 산재

**Legacy 0.1.0 partition** = `mode=` segment 없음 → read time 에 "no-mode = historical legacy" 분류.

### 7.2 `paper_storage.write_paper_candles` 별도 module (A2)

**채택**: option (a) 별도 module.

```python
# paper_storage.py
def write_paper_candles(
    candles: Sequence[CandleLike],
    *,
    root: Path,
    run_id: str,
    snapshot_id: str | None = None,    # None = auto-generate per-flush
    lineage: PaperLineage,
) -> Path: ...
```

**근거**:
- canonical `write_candles` API 안정성 보존 (mode parameter 추가 시 default behavior 위험)
- separate concern (Paper-specific lineage / run lifecycle / WebSocket batch hash)
- 공통 helper (Parquet writing / schema validation / partition path) = 내부 share, public API 분리

**Live storage** (future) = 동일 패턴 (`live_storage.write_live_candles`).

### 7.3 Lineage extension (A3)

**ADR-009 lineage field 의미 확장** (REST 와 WebSocket 다름):

| Field | REST (0.1.0) | Paper WebSocket extension |
|---|---|---|
| `endpoint` | `/public/candlestick/...` | `wss://pubwss.bithumb.com/pub/ws` |
| `request_params_hash` | query params canonical hash | subscribe message canonical hash |
| `fetched_at_utc` | HTTP fetch time | **aggregation_finalized_at** (BarAggregator close time) |
| `response_hash` | HTTP response body sha256 | **order-preserving normalized JSONL batch sha256** |
| `adapter_name` | `mctrader-market-bithumb` | **`mctrader-market-bithumb-ws`** |
| `adapter_version` | 0.1.0 | 0.2.0 (WebSocket extension version) |
| `snapshot_id` | per-batch | per-flush (rolling buffer) |

**Canonical hash material** (option b 채택):
- order-preserving normalized JSONL (sorted keys, stable Decimal/string representation, original message order preserved)
- raw bytes sha256 (option a) = compression / framing / transport 민감 → cross-platform 약함
- candle batch hash (option c) = aggregation output 만, source provenance 손실

```python
class PaperLineage(BaseModel):
    snapshot_id: str
    exchange: str
    endpoint: str = "wss://pubwss.bithumb.com/pub/ws"
    request_params_hash: str
    fetched_at_utc: UTCDateTime    # aggregation_finalized_at
    response_hash: str             # order-preserving JSONL sha256
    adapter_name: Literal["mctrader-market-bithumb-ws"]
    adapter_version: str
    run_id: str                    # 새 field (run-level grouping)
```

ADR-009 amendment = 본 lineage extension documentation (schema 변경 X).

### 7.4 `scan_candles` mode parameter (A4)

**채택**: option (a) `mode: Literal["historical", "paper"] | Sequence = "historical"` default.

```python
def scan_candles(
    *,
    exchange: str,
    symbol: Symbol,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
    root: Path,
    mode: Literal["historical", "paper"] | Sequence[str] = "historical",
) -> Iterable[CandleModel]:
    """Default = historical (legacy no-mode + mode=historical 모두 read, mode=paper 제외).
    
    명시 ``mode="paper"`` 또는 ``mode=["historical", "paper"]`` 만 paper 포함.
    """
```

**Default 의 의미**:
- `mode="historical"` (default) → `mode=historical` partition + legacy no-mode partition 모두 read
- `mode="paper"` → `mode=paper` partition 만
- `mode=["historical", "paper"]` → 명시 multi (전체 read)
- `mode=None` 도입 X (혼동 회피)

mctrader-engine BacktestExecutor 의 default = historical (paper 자동 제외).

### 7.5 Run lifecycle + rolling buffer (A5)

**채택**: option (c) rolling buffer + flush.

| Mechanism | Default |
|---|---|
| Flush trigger | closed bar 수 (`flush_every_n_bars=1` per-bar 시작) 또는 interval (`flush_interval_seconds=300`) |
| SIGTERM | best-effort final flush |
| `run_id` | 실행 lifecycle 식별자 (1 run = N flush) |
| `snapshot_id` | 각 flush unit (1 flush = 1 parquet file) |

**Per-bar snapshot 시작** (MCT-21 integration 단순), public design = rolling flush 허용 (long-run file explosion 회피).

**Failure model**:
- Per-bar = 이미 닫힌 bar 보존 (장애 시 손실 = 진행 중 partial bar 만)
- Rolling = SIGTERM 시 final flush 시도 (보장 X)
- `run_id` Pydantic field (lineage) → row schema X (ADR-009 보존)

### 7.6 ADR-009 invariant + Linux+Windows CI (A6)

**4-layer 검증**:

1. **Schema-level**: Pydantic `OhlcvRow` 16-column 변경 X assert
2. **Path-level**: `mode=paper` segment Windows 안전 (`pathlib.Path.as_posix()`)
3. **DuckDB scan-level**: `hive_partitioning=true` 가 `mode` 인식 + filter 정상
4. **Cross-platform fixture-level**: Linux + Windows 동일 partition path generate + read

기존 storage roundtrip test 영향 X (default `mode="historical"` legacy 호환).

### 7.7 Migration policy = dual-write transition (A7)

**채택**: option (c) dual-write.

| Phase | Historical write | Historical read | Paper write |
|---|---|---|---|
| 0.1.0 (legacy) | no-mode partition | no-mode partition | — |
| 0.2.0+ (MCT-20) | `mode=historical/` 직접 | no-mode legacy + `mode=historical` 둘 다 read | `mode=paper/` |
| Future | (option) explicit migration script | `mode=historical` only | `mode=paper/` |

**중복 정책**:
- 같은 `(exchange, symbol, timeframe, ts_utc)` 가 legacy 와 `mode=historical` 양쪽 = duplicate detection
- 보수적: `ValidationError` raise (silent merge 금지) 또는 deterministic precedence (`mode=historical` 우선)
- 본 Story = `ValidationError` 권장 (사용자 명시 migration 의무)

### 7.8 Out-of-scope

| 항목 | 미포함 | 이유 |
|---|---|---|
| Live storage (`live_storage`) | ✗ | future Epic |
| Explicit migration script (legacy → mode=historical) | ✗ | dual-write transition 만 |
| Multi-mode aggregate query helper | ✗ | scan_candles `mode=[...]` sequence 로 충분 |
| ADR-009 v2 schema (column 추가) | ✗ | v1 immutable |

### 7.9 Acceptance (Phase 2)

| # | AC | 검증 |
|---|---|---|
| AC1 | dependency = mctrader-market `>=0.1,<0.2` (변경 X) | uv sync |
| AC2 | 5 required check green (Linux + Windows matrix) | CI |
| AC3 | `OhlcvRow` Pydantic 16-column 변경 X | pytest schema assert |
| AC4 | `paper_storage.write_paper_candles` Parquet 산출 + `mode=paper/...` partition path | pytest |
| AC5 | `PaperLineage` Pydantic boundary (8+1 field, run_id 포함) | pytest |
| AC6 | response_hash = order-preserving normalized JSONL sha256 deterministic (Linux+Windows 동일) | pytest |
| AC7 | `scan_candles(..., mode="historical")` default = legacy no-mode + mode=historical 모두 read, mode=paper 제외 | pytest |
| AC8 | `scan_candles(..., mode="paper")` = mode=paper 만 | pytest |
| AC9 | `scan_candles(..., mode=["historical", "paper"])` = 전체 | pytest |
| AC10 | DuckDB Hive partition discovery 가 `mode` 인식 (Linux+Windows) | pytest |
| AC11 | 같은 ts_utc duplicate (legacy + mode=historical) = `ValidationError` | pytest |
| AC12 | rolling buffer flush (per-bar + SIGTERM final flush) | pytest |
| AC13 | Decimal precision / UTC timezone 보존 (ADR-009/010) | pytest |
| AC14 | Backward compat = 기존 0.1.0 storage roundtrip test 모두 통과 | pytest (regression) |

### 7.10 Codex 적용

7/7 area 채택. ADR-009 partition pattern amendment 권장 (schema 변경 X — pattern 만). ADR conflict 0/7.

## 8-11

(Phase 2 = paper_storage + paper_lineage 추가 + scan_candles extension + AC1~AC14.)
