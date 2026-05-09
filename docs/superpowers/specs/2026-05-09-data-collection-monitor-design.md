# Data Collection Monitor — 설계 문서

**날짜**: 2026-05-09  
**담당 레포**: mctrader-web (대시보드 페이지 + adapter) · mctrader-data (캐시 writer)  
**관련 스토리**: MCT-TBD (신규)  
**관련 ADR**: ADR-009 (OHLCV schema) · heartbeat-schema.v1 · MCT-65 (manifest) · MCT-103 (50-symbol) · MCT-105 (RDB)

---

## 1. 배경 및 목적

50개 심볼 × 3 데이터 tier(candle / orderbook / transaction)를 24/7 수집 중인 collector 데몬이 **순단 없이 정상 적재하고 있는지** 실시간으로 확인할 수 있는 Web UI 대시보드.

기존 `00_status.py`는 heartbeat 기반 node liveness만 보여주며 데이터 레벨 커버리지(심볼별, tier별 공백 여부, 적재 현황)는 표시하지 않는다. 이 설계는 그 공백을 채우는 전용 모니터링 페이지다.

---

## 2. 아키텍처 개요

```
mctrader-data (collector 프로세스)
  └─ CoverageStatsWriter          ← 신규 (5분마다 in-memory → JSON flush)
       └─ coverage-stats.json     ← <root>/market/manifest/coverage-stats.json

mctrader-web (Streamlit dashboard)
  └─ pages/20_data_collection.py  ← 신규 (4-section 대시보드 페이지)
       ├─ status_adapter.py       ← 기존 (heartbeat 읽기, §2에 재사용)
       └─ coverage_stats_adapter.py ← 신규 (coverage-stats.json 읽기, TTL 캐시)
```

**데이터 흐름**:

```
CollectorDaemon (per symbol, in-memory counter)
  → CoverageStatsWriter.flush() every 5 min
    → coverage-stats.json (atomic write, same pattern as heartbeat)
      → CoverageStatsAdapter.fetch() with 5-min TTL cache
        → Streamlit page renders
```

---

## 3. 대시보드 구조 (4 섹션)

### §1 전체 수집 현황 요약

**목적**: 전체 상태를 한 눈에 파악하는 최상단 요약.

**표시 항목**:
- 전체 health banner: GREEN / YELLOW / RED (heartbeat worst_level 기준)
- collector_run_id, uptime, git-sha (heartbeat)
- KPI 7개:

| KPI | 소스 | 판정 기준 |
|---|---|---|
| 수집 중 심볼 수 | coverage-stats | 50/50 |
| 24h 커버리지 % | coverage-stats | tick tier 기준 |
| 공백 인시던트 수 + 총 공백 시간 | coverage-stats gap_events | 건수 + 합산 duration |
| Tick avg lag | heartbeat last_event_ts_per_tier["tick"] | now - last_ts |
| Orderbook avg lag | heartbeat last_event_ts_per_tier["orderbook"] | now - last_ts |
| 이벤트/분 | heartbeat metrics.events_per_sec × 60 | 전체 합산 |
| 오늘 저장량 | coverage-stats file_size_bytes 합산 | GB |

**갱신**: heartbeat TTL 5s (lag 지표) / coverage-stats TTL 5min (파일/커버리지 지표)

---

### §2 수집기 (Collector Daemon) 현황

**목적**: HA 노드별 daemon 건강 상태 + 현재 run 메타.

**표시 항목**:

**노드 카드** (NODE_A, NODE_B 각각):
- ws_state (connected / reconnecting / disconnected)
- heartbeat freshness (초)
- uptime
- ws_reconnect_count (cum)
- queue_depth
- tier별 lag (tick / orderbook / candle)
- dup_skip_count, quarantine_count, events_per_sec, backfill_pending_seconds

**Collector Run Manifest** (MCT-65):
- collector_run_id, selection_method, channels, started_at_utc, selected_symbols 수

**Quarantine / Exchange Metadata**:
- tick/orderbook quarantine 건수 (ACTIVE_ACTIVE_MISMATCH)
- Exchange Metadata 마지막 갱신 시각 + 다음 갱신 예정 (§D13 UTC midnight + 1min)

**소스**: heartbeat-{node_id}.json (기존 `status_adapter.py`) + manifest JSON (기존 `list_manifests()`)

---

### §3 전체 데이터 현황 (3-tier 크로스뷰)

**목적**: 3개 tier의 수집 커버리지를 심볼 × 시간 축으로 시각화.

#### 3-1. Tier 요약 카드 (3열)

| 항목 | Candle (ohlcv.v1) | Orderbook (orderbook.v1) | Transaction (tick.v1) |
|---|---|---|---|
| avg lag | heartbeat candle tier | heartbeat orderbook tier | heartbeat tick tier |
| 24h 커버리지 % | coverage-stats | coverage-stats | coverage-stats |
| 공백 건수 | coverage-stats gap_events | coverage-stats gap_events | coverage-stats gap_events |
| 이벤트량 | coverage-stats | delta/분 | 이벤트/분 |
| 오늘 크기 | coverage-stats file_size_bytes | coverage-stats | coverage-stats |

lag 판정 기준 (heartbeat-schema.v1):
- candle: `now - last_ts > 120s` (= 2 × 1m 기준) → yellow; `> 240s` → red
- tick: `> 60s` → yellow; `> 300s` → red
- orderbook: `> 60s` → yellow; `> 300s` → red

#### 3-2. 심볼 × 시간 커버리지 히트맵

- Y축: 50개 심볼 (스크롤, 이슈 심볼 상단 고정)
- X축: 조회 범위 기준 1h 단위 격자
- 색상: `c-ok` (정상) / `c-warn` (lag 경고) / `c-gap` (공백) / `c-miss` (데이터 없음)
- 판정: 3 tier 중 최악 상태를 해당 셀에 표시
- 소스: coverage-stats gap_events (5분 캐시), heartbeat lag (5s 캐시)

히트맵 시간 단위는 조회 범위에 따라 자동 조정:
- 1h → 5분 단위
- 24h → 1h 단위
- 7d → 6h 단위

#### 3-3. 공백 인시던트 테이블

컬럼: 심볼 / tier / 시작 시각 / 종료 시각 / 공백 기간 (바 + 숫자) / 원인 분류 / Node / WS reconn / 상태

원인 분류 (`diagnostic.py` GapCause 재사용):
- `LIKELY_NODE_DOWN`: heartbeat ws_state=disconnected 또는 freshness ≥ 30s
- `UNKNOWN`: heartbeat 정상, Bithumb WS 일시 중단 가능성

소스: coverage-stats gap_events (start_ts, end_ts, duration_seconds, symbol, tier, cause, node_id, ws_reconnect_count)

---

### §4 데이터별 상세 대시보드 (탭)

탭: 📊 Candle | 📖 Orderbook | ⚡ Transaction

#### §4-A Candle

- timeframe별 카드 (1m / 5m / 1h):
  - lag, 심볼 커버리지 (50/50), is_complete=true 비율, 최근 바 시각, 오늘 파일 수/크기
  - 커버리지 fill bar
- Parquet 파티션 경로 표시:
  `market/candles/schema_version=ohlcv.v1/mode=historical/exchange=bithumb/symbol={sym}/date=YYYY-MM-DD/`
- 7일 저장량 트렌드

#### §4-B Orderbook

- delta lag, snapshot 주기 (마지막 snapshot 시각), snapshot 건수/분
- delta 이벤트/분, level depth 평균
- 재구성 가능 여부: 마지막 snapshot 이후 delta chain 연속성 체크
- 파티션 경로: `market/orderbook/schema_version=orderbook.v1/...`

#### §4-C Transaction (Tick)

- lag, 이벤트/분 추이
- buy/sell 비율 (비율 바)
- dup_skip_count 트렌드, quarantine 상세 목록
- 파티션 경로: `market/ticks/schema_version=tick.v1/...`

---

## 4. 신규 컴포넌트 설계

### 4-1. `mctrader-data`: CoverageStatsWriter

**파일**: `src/mctrader_data/coverage_stats.py`

**역할**: CollectorDaemon이 이벤트를 처리할 때마다 in-memory 카운터를 업데이트하고, 5분마다 `coverage-stats.json`으로 원자적으로 flush.

```python
@dataclass
class TierStats:
    row_count_today: int = 0
    file_count_today: int = 0
    file_size_bytes_today: int = 0
    last_event_ts: str | None = None    # ISO8601 UTC
    gap_events: list[GapEvent] = field(default_factory=list)

@dataclass
class GapEvent:
    symbol: str
    tier: str                           # "tick" | "orderbook" | "candle"
    start_ts: str                       # ISO8601 UTC
    end_ts: str                         # ISO8601 UTC
    duration_seconds: float
    cause: str                          # "LIKELY_NODE_DOWN" | "UNKNOWN"
    node_id: str | None
    ws_reconnect_count: int

class CoverageStatsWriter:
    FLUSH_INTERVAL_SECONDS: float = 300.0   # 5분

    def __init__(self, root: Path, node_id: str, collector_run_id: str) -> None: ...
    def record_event(self, symbol: str, tier: str, ts: datetime, file_size_delta: int = 0) -> None: ...
    def record_gap(self, gap: GapEvent) -> None: ...
    async def run(self) -> None: ...   # 5min loop, CancelledError → final flush
    def flush(self) -> None: ...       # atomic write (temp → fsync → os.replace)
```

**파일 경로**: `<root>/market/manifest/coverage-stats.json`

**JSON 스키마**:
```json
{
  "schema_version": "coverage_stats.v1",
  "node_id": "NODE_A",
  "collector_run_id": "NODE_A-20260509T071041Z",
  "generated_at": "2026-05-09T00:23:00Z",
  "flush_interval_seconds": 300,
  "stats": {
    "KRW-BTC": {
      "tick": { "row_count_today": 12400, "file_count_today": 1, "file_size_bytes_today": 1234567, "last_event_ts": "...", "gap_events": [] },
      "orderbook": { ... },
      "candle": { ... }
    },
    ...
  }
}
```

**MultiSymbolCollector 통합**: heartbeat_writer와 동일하게 별도 asyncio task로 spawn, main task 종료 시 cancel + final flush.

**성능**: 50심볼 × 3 tier = 150 counter 업데이트/이벤트. 모두 in-memory, I/O는 5분에 한 번만.

---

### 4-2. `mctrader-web`: CoverageStatsAdapter

**파일**: `src/mctrader_web/dashboard/coverage_stats_adapter.py`

`status_adapter.py`와 동일 패턴:
- `fetch_coverage_stats(root, use_cache=True)` → `CoverageStatsResult`
- TTL: 5분 (= flush interval에 맞춤)
- 파일 없음 → graceful degraded (heartbeat-only 모드로 fallback)
- JSON schema_version mismatch → warning + best-effort parse

```python
@dataclass
class CoverageStatsResult:
    stats: dict[str, dict[str, TierStats]]  # symbol → tier → TierStats
    generated_at: float                     # unix timestamp
    node_id: str | None
    error: str | None
    fetched_at: float

    @property
    def is_error(self) -> bool: ...
    def get_gap_events(self) -> list[GapEvent]: ...    # 전체 gap 이벤트 평탄화
    def coverage_pct(self, tier: str, window_seconds: float) -> float: ...
```

---

### 4-3. `mctrader-web`: 20_data_collection.py

**파일**: `src/mctrader_web/dashboard/pages/20_data_collection.py`

**설정 UI** (Streamlit sidebar):
- 타임존: KST / UTC (선택 → `st.session_state["tz"]`)
- 자동 갱신 간격: 5s / 10s / 30s / 수동
- 조회 범위: 1h / 6h / 오늘 / 24h / 7d / 직접 입력 (`datetime_input` 2개)

**섹션 렌더링 순서**: §1 → §2 → §3 → §4 (탭)

**폴링**: `time.sleep(interval); st.rerun()` (기존 `10_admin_overview.py` 패턴)

---

## 5. 설정 UI 명세

### 타임존
- 선택: KST (UTC+9) / UTC
- 적용 범위: 모든 시각 표시 (heartbeat now, 인시던트 시각, 최근 바 시각 등)
- 세션 상태: `st.session_state["tz"]` = `"KST"` | `"UTC"` (기본: KST)

### 자동 갱신 간격
- 선택: 5s / 10s / 30s / 수동
- heartbeat(§1,§2) 갱신: 선택 간격
- coverage-stats(§3,§4) 갱신: max(선택 간격, 300s) — 5분 캐시 TTL 이하로 갱신해도 의미 없으므로

### 조회 범위
- 프리셋: 1h / 6h / 오늘(당일 00:00~now) / 24h / 7d
- 직접 입력: `st.date_input` + `st.time_input` × 2 (from / to)
- 히트맵 X축 단위 자동 조정:
  - ≤ 2h → 5분
  - ≤ 48h → 1h
  - > 48h → 6h

---

## 6. 에러 처리

| 상황 | 동작 |
|---|---|
| heartbeat 파일 없음 | §2 RED banner "No active node heartbeats" |
| coverage-stats.json 없음 | §3,§4 info: "coverage-stats 아직 생성 안 됨 (collector 5분 후 생성)" |
| coverage-stats schema mismatch | warning + best-effort parse |
| mctrader-data CLI not found | status_adapter 기존 동작 유지 |
| CoverageStatsWriter flush 실패 | log.warning + last-good 파일 유지 (heartbeat 동일 패턴) |

---

## 7. 테스트 계약

### mctrader-data

- `CoverageStatsWriter.flush()` → 파일 원자적 생성, JSON 유효성
- `record_event()` → row_count_today 증가 확인
- `record_gap()` → gap_events 리스트 누적 확인
- flush 실패 시 last-good 파일 유지 (OSError 주입)
- 5분 루프 cancel → final flush 실행 확인

### mctrader-web

- `CoverageStatsAdapter.fetch()` → 파일 있음/없음/malformed JSON 각 케이스
- TTL 캐시 동작 (fetch 두 번 → 파일 읽기 한 번)
- `coverage_pct()` 계산 정확도
- `get_gap_events()` 평탄화 (multi-symbol, multi-tier)

---

## 8. 기존 파일과의 관계

| 파일 | 관계 |
|---|---|
| `00_status.py` | 유지 (node liveness 전용 단순 뷰). 새 페이지는 별도 번호(20) |
| `status_adapter.py` | §2에서 그대로 재사용 |
| `heartbeat.py` | 변경 없음 |
| `collector.py` → `MultiSymbolCollector` | `coverage_stats_writer` 인자 추가 (heartbeat_writer와 동일 패턴) |
| `cli.py` (mctrader-data) | `--coverage-stats` 플래그 추가 (기본 on) |

---

## 9. 구현 범위 (Out of Scope)

- Slack/email 알림 (Epic decision #14 deferred to v2)
- Parquet 직접 DuckDB 스캔 트리거 버튼 (v2)
- PostgreSQL 기반 coverage 저장 (MCT-105 이후 v2 검토)
- 심볼 tier별 드릴다운 상세 페이지 (v2)
