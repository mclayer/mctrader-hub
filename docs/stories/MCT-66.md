---
story_key: MCT-66
status: phase:요구사항
component: data
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-005, ADR-009
---

# MCT-66: Orderbook reconstruction utility — scan_ticks / scan_orderbook_events / get_orderbook_at + tier_coverage

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

T2/T3 forward-only event stream 의 read-side. MCT-67 TickReplayExecutor 가 의무 의존. Codex F-3/F-10/F-11/F-12/F-18 push-back 반영: `available_from_ts := received_at` lookahead 방어 + bounded LRU 캐시 + fail-closed gap policy + 결정적 sort key + coverage API.

## 2. 도메인 해석

MCT-63 child #3 = **read-side API**. mctrader-data PR #4 (MCT-65) 의 partition 을 backtest 가 안전하게 읽도록 wrap.

핵심 design:

- **available_from_ts** = `received_at` (Codex F-3) — collector 가 server-side 도착 시각을 기록한 컬럼이 이미 schema 에 있음 (§D10/§D11 의 `received_at`). Backtest reader 는 `received_at <= simulated_clock` 인 event 만 dispatch. ADR-005 lookahead 방어와 정합.
- **fail-closed gap policy** (Codex F-11) — research-grade reproducibility 우선. silent skip 거부.
- **bounded cache** (F-10) — per-symbol-day-session LRU max N=1 reconstructed snapshot, checkpoint every 1000 deltas. 메모리 폭발 방어.
- **결정적 sort key** (F-18) — `(ts_utc ASC, received_at ASC, file_offset ASC)`. 동일 ts_utc 다중 event 순서 deterministic.
- **coverage API** (F-12 + F-21) — `tier_coverage` 가 symbol manifest 를 의무 참조 (MCT-65 의 manifest.json).

## 3. 관련 ADR

- **ADR-005 amendment** (Phase 1 PR 에서 추가) — T2/T3 lookahead = `received_at`. 본 모듈이 enforcement point.
- **ADR-009 §D10 / §D11** — 본 모듈이 read API. partition layout / column schema / sort 의무 채택.

## 4. 관련 코드 경로

```
mctrader-data/src/mctrader_data/
├── orderbook_replay.py     (NEW — 본 Story core)
├── coverage.py             (NEW — tier_coverage helper)
└── exceptions.py           (NEW — GapDetectedError + ReconstructionError)

mctrader-data/tests/
├── test_orderbook_replay.py    (NEW — replay 결정성 + fail-closed)
└── test_coverage.py            (NEW — coverage edge cases)
```

## 5-6. 요구사항

### Read API (3종)

1. **`scan_ticks(symbol, start, end, *, snapshot_id=None) -> Iterable[TickRecord]`**
   - half-open `[start, end)` 반환.
   - `received_at <= simulated_clock` filter 의무 (caller 가 simulated_clock 주입; 미주입 시 = `end`).
   - sort: `(ts_utc ASC, received_at ASC, file_offset ASC)`.
   - 다중 partition (date 다중) 자동 merge.
2. **`scan_orderbook_events(symbol, start, end, *, snapshot_id=None) -> Iterable[OrderbookEventRecord]`**
   - 동일 contract (above).
3. **`get_orderbook_at(symbol, ts_utc, *, simulated_clock=None) -> OrderbookSnapshot`**
   - 시작점 baseline (해당 일 첫 snapshot event) 부터 fold delta forward → ts_utc 시점 state 반환.
   - `received_at <= simulated_clock` filter 의무.
   - LRU 캐시 (per (symbol, date, snapshot_id)): max N=1 snapshot, checkpoint every 1000 deltas.

### Coverage API

4. **`tier_coverage(symbol, tier, start, end) -> CoverageReport`**
   - `tier ∈ {tick, orderbook}` (T2/T3 only; T1 candle 은 기존 `scan_candles` 사용).
   - report Pydantic v2 strict:
     ```
     {
       "symbol": str,
       "tier": "tick" | "orderbook",
       "min_ts_utc": datetime | null,
       "max_ts_utc": datetime | null,
       "gaps": list[Gap],          # ts gap > threshold (e.g., 5min)
       "collector_run_ids": list[str],
       "symbol_manifests": list[ManifestRef]  # MCT-65 manifest.json 참조
     }
     ```
   - threshold = configurable (default 5분 = WS reconnect grace).

### Fail-closed error mode (F-11)

5. **`GapDetectedError`** — gap > threshold 시 `get_orderbook_at` halt.
6. **`ReconstructionError`** — 다음 cases halt:
   - missing baseline (시작 일 첫 snapshot event 부재)
   - non-monotonic ts (스트림 내 `(ts_utc, received_at, file_offset)` 역순)
   - duplicate event with different hash (동일 hash = idempotent skip)
   - schema mismatch (`schema_version` 불일치)
7. `scan_ticks` / `scan_orderbook_events` 는 fail-closed default = ON. caller 가 `strict_gap=False` 로 disable 가능 (research-mode only, log warn).

### Bounded cache (F-10)

8. LRU max N=1 reconstructed snapshot per (symbol, date, snapshot_id). 새 ts 요청 시 기존 snapshot 위 fold or 재시작.
9. checkpoint = 1000 delta 마다 (in-memory partial result, 디스크 저장 안 함).
10. 캐시 디버그 statistics: `replay_cache_hits`, `replay_cache_misses`, `replay_baseline_loads`.

### 결정성 (F-18)

11. `scan_*` 출력 = strict ascending `(ts_utc, received_at, file_offset)`. 동일 ts_utc 다중 event 도 deterministic.
12. `file_offset` = parquet row group + row index 조합 (안정성). 다중 partition 시 file path lex order 추가.

### Tests

13. **결정성 unit test** (3 case): 동일 fixture 다중 호출 = 동일 sequence.
14. **fail-closed unit test** (4 case): gap / non-monotonic / missing baseline / schema mismatch.
15. **coverage edge** (3 case): empty partition / single partition / gap detection.
16. **bounded cache** (2 case): max N=1 enforce, checkpoint hit.
17. **available_from_ts filter** (2 case): simulated_clock 주입 시 후속 event filter out 명시.

### 18. CLI 보조 (optional, Phase 3 결정)

- `mctrader-data tier-coverage --symbol KRW-BTC --tier tick --start ... --end ...` (CoverageReport JSON dump). MCT-69 web UI 도 동일 정보 사용 가능.

19. **버전 bump**: mctrader-data 0.4.1 → 0.5.0.

20. **CI green** (ubuntu + windows lane).

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: read-only API, 신규 secret 없음.
- **신규 file**: `orderbook_replay.py` / `coverage.py` / `exceptions.py` + tests.
- **수정 file**: 없음 (모두 신규).
- **Reversible**: yes (read-only 추가, 기존 데이터 불변).
- **Performance budget**: top-1 symbol 1일 = 약 50만 tick + 200만 orderbook delta event 추정. `scan_*` 스트림 = O(read I/O). `get_orderbook_at` ts 1개 = O(deltas before ts) (캐시 hit 시 O(1)).
