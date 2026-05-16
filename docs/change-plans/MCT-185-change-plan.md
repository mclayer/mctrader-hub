---
story_key: MCT-185
epic_key: EPIC-data-domain-decoupling
type: change-plan
author: ArchitectPLAgent (chief author = ArchitectAgent + 6 deputy + 2 CONDITIONAL deputy synthesis)
created: "2026-05-17"
status: design-lane-draft
decisions: [D2, D3]
related_adrs:
  - "ADR-031-data-domain-decoupling §D2 (io-relocate + cold-read-behind-REST — 본 Story = cold-read cutover 절반 = VERIFIED 진전) + §D3 (fastapi-v1 + redis-stream — 본 Story = realtime stream + reverse-write wiring 절반 = VERIFIED 진전). Status Accepted 유지 (POLICY_FINALIZED 전이 = MCT-188)"
  - "ADR-029-tier-promotion-single-source §D2 VERIFIED amendment box (engine NAS 직독 폐기 LAND confirm — cold-read 8곳 = data REST indirection 실 적용 박제. 본문 11 D 정책 무변경, POLICY_FINALIZED 보존)"
  - "ADR-030-docker-stack-governance §D15 Redis prefix cross-ref (Redis Stream loopback 정합 재명시 — data 기존 redis[hiredis] 의존 재사용, 신규 service 추가 0. 본문 19 D 무변경, POLICY_FINALIZED 보존)"
  - "ADR-032 (PMO 발의 — VERIFIED badge evidence triad). MCT-184 = 선제 reapply (의도된 dead-in-data 박제 + consumer=MCT-185 명시) → 본 Story = production wiring 전환 evidence triad 갱신 = 선제 reapply 효력 1회 실증 시점"
  - "ADR-009 v1 16-col schema (reverse-write paper-candles schema 보존 — MCT-184 LAND 정합)"
  - "ADR-025 (paper_lineage.canonical_jsonl_hash — idempotency key 패턴, MCT-182 LAND market-core 정합)"
  - "MCT-184 §D3 amendment box (REST boundary historical+reverse-write 부분 진행, dead-in-data) + post-merge fix e612296 (F-1/F-2/F-4 data correctness) — 본 Story production wiring 전환 prerequisite 충족"
---

# MCT-185 Change Plan — data realtime stream + engine thin client + cold-read cutover

> ArchitectAgent (chief author) + 6 deputy (CodebaseMapper / Refactor / SecurityArch
> **primary 강함** / OperationalRiskArch **primary 강함 CONDITIONAL §8.5 active=true** /
> TestContractArch / DataMigrationArch) + 2 CONDITIONAL deputy (LiveOps / LiveOrdering —
> R2 MCT-41 cross-cutting 평가) synthesis. ArchitectPLAgent 검수.
>
> **EPIC-data-domain-decoupling 7 Story sequential strangler-fig 4단계 (가장 복잡 Story)**.
> 3 repo + production wiring 전환 (MCT-184 dead-in-data → MCT-185 live cutover) + ADR-029
> §D2 VERIFIED amendment confirm = D2+D3 동시 충족. MCT-184 Change Plan 형식 + §3.6.1
> gate v2 패턴 SSOT 차용 + PMO-AUDIT-MCT-184 §6 박제 PR 5 체크리스트 + §post-LAND audit
> 4 axis self-discipline 인계.

## 1. 목표 / 비목표

### 1.1 목표 (D2 + D3 — scope_manifest `§story_decision_matrix.MCT-185` 1:1)

- **D2 (cold-read cutover 절반 — `option_chosen: io-relocate + cold-read-behind-REST`
  중 cold-read-behind-REST 절반)**: engine cold-read 8곳 4파일 (§0 V2 정확 식별 — `cli.py:279,280`
  + `executor/tick_replay.py:26,559` + `wfo/evaluator/data_loader.py:43,44` + `wfo/search/data_loader.py:81,82`)
  를 engine `data_client/historical` REST 경유 cutover. ADR-029 §D2 VERIFIED amendment
  confirm (engine NAS 직독 폐기 LAND).
- **D3 (realtime stream + reverse-write wiring 절반 — `option_chosen: fastapi-v1 +
  redis-stream` 중 redis-stream + reverse-write client 절반)**: data `src/mctrader_data/api/realtime_stream.py`
  신규 (Redis Stream `XADD market:tick:{exchange}:{symbol}` publisher, tick.v1.1 정규화
  schema 정합 — `mctrader_market.schemas.tick.TickRowV1_1` SSOT 소비). engine reverse-write
  carrier 3곳 2파일 (§0 V3: `runtime/paper_runner.py:290,291` + `backtest/nas_sync.py:36`)
  를 engine `data_client/reverse_write` REST 경유 cutover. engine `data_client/` 신규
  서브패키지 신설 (`httpx>=0.27` 신규 의존 + MCT-184 OpenAPI SSOT hand-written thin client).
- **D3 (historical/orderbook endpoint 신설)**: MCT-184 routes_v1.py 4 endpoint
  (candles + candles/l1 + reverse-write × 2) 만 LAND — executor/tick_replay.py:26,559 cutover
  대상 historical/orderbook endpoint **미LAND** (V6 추가 사실). 본 Story data#N 에
  `/v1/historical/orderbook` 신규 endpoint 추가 의무 (MCT-184 amendment 분리 시 lock-step
  의존 증가 — 본 Story 포함 채택).
- **D6 (ADR amendment box 박제)**: ADR-029 §D2 VERIFIED amendment box (engine NAS 직독
  폐기 LAND confirm, POLICY_FINALIZED 본문 무변경) + ADR-031 §D2 VERIFIED amendment box
  (cold-read cutover 완결) + §D3 VERIFIED amendment box (realtime stream + reverse-write
  wiring 완결, Status Accepted 유지) + ADR-030 cross-ref only (정책 무변경). D-row 1:1
  reconcile + §3.6.1 gate v2 cross-Story reapply + 박제 PR 5 체크리스트 inline 박제
  (self-discipline carrier 2번째).

### 1.2 비목표 (out-of-scope — Story §2 비목표 표 1:1)

| 항목 | owner Story |
|------|-------------|
| engine `mctrader_market_bithumb/upbit` 어댑터 직접 import ~5곳 제거 (D4 — realtime WS adapter 제거) | MCT-186 |
| engine 측 Redis Stream subscriber (`XREAD market:tick:{...}` consumer wiring) | MCT-186 |
| MCT-182 shim 잔존 5곳 cleanup (`tick_storage`/`orderbook_storage`/`aggregation`/`paper_lineage` shim re-export → market-core 직독 변경. engine src/ grep 5곳: `executor/tick_replay.py:31,32` + `hot/state_machine.py:33` + `runtime/paper_runner.py:290 paper_lineage` + `strategy/templates/tick_scalping.py:76`) — **본 Story `paper_runner.py:290 paper_lineage` cutover 포함 결정 (§3.5)** → MCT-188 owner shim 잔존 4곳으로 축소 | MCT-188 |
| engine `pyproject.toml` `mctrader-data @ git+` 의존 제거 + `mctrader_market_bithumb/upbit` 어댑터 의존 제거 | MCT-188 |
| 다중거래소 확장 불변식 박제 (`add-new-exchange.md` runbook + adapters.py invariant test) | MCT-187 |
| data-free grep0 quad gate CI + Epic POLICY_FINALIZED | MCT-188 |
| ADR-030 **실 compose wiring** (data api service compose topology 실 적용 + engine NAS credential env drop) | MCT-186 (engine NAS cred drop) |
| ADR-031 Status `Accepted` → `POLICY_FINALIZED` 전이 | MCT-188 |
| Codex post-LAND audit lane 신설 (plugin-codeforge#805) + 박제 PR 5 체크 mechanical gate (plugin-codeforge#804) | codeforge upstream (PMO-AUDIT-MCT-184 §4 carry) |

## 2. 배경 / AS-IS (CodebaseMapper 변호 — verified-via)

> **CodebaseMapper deputy perspective (보수/변호자)** — verified-via `git fetch origin`
> + `Grep` + `Read` + `Test-Path` (2026-05-17, engine origin/main HEAD `18275737` + data
> origin/main HEAD `a1a8ccf` + hub origin/main HEAD `330c124` (F-1 정정: draft 시점 `863fe73` → MCT-189 PMO-AUDIT LAND 후 `330c124`, sibling 무영향). 모두 Story §0 V1 정합.

### 2.1 AS-IS 사실 (file:line 근거 — Phase 0 HEAD 재대조 실증)

| 사실 | file:line | 검증 |
|------|-----------|------|
| engine cold-read 8곳 4파일 (D2 cutover 대상) | `cli.py:279 from mctrader_data.path import resolve_data_root` + `cli.py:280 from mctrader_data.storage import scan_candles` + `executor/tick_replay.py:26 from mctrader_data.orderbook_replay import (OrderbookSnapshot, scan_orderbook_events, scan_ticks)` (top-level) + `executor/tick_replay.py:559 from mctrader_data.orderbook_replay import (_orderbook_partition_dir, _tick_partition_dir)` (function-local) + `wfo/evaluator/data_loader.py:43 from mctrader_data.path import resolve_data_root` + `wfo/evaluator/data_loader.py:44 from mctrader_data.storage import scan_candles` + `wfo/search/data_loader.py:81-82` 동형 | Grep 실측 ✓ — Story §0 V2 + Change Plan §2 1:1 정합 |
| engine reverse-write 3곳 2파일 (D3 cutover 대상) | `runtime/paper_runner.py:290 from mctrader_data.paper_lineage import PaperLineage, canonical_jsonl_hash` (lazy import 내부 — `_write_paper_partition_safe` best-effort + ImportError graceful skip 패턴) + `runtime/paper_runner.py:291 from mctrader_data.paper_storage import write_paper_candles` (동일 lazy import 블록) + `backtest/nas_sync.py:36 from mctrader_data.nas_storage.nas_uploader import NASUploader  # type: ignore[import]  # noqa: F401` (module-level lazy import + test patch 의존 — `patch("mctrader_engine.backtest.nas_sync.NASUploader")`) | Grep + Read 실측 ✓ — Story §0 V3 정합. **paper_runner.py:290,291 = lazy import + graceful skip 패턴** = REST cutover 시 동일 graceful skip 정합 의무 (httpx ImportError 또는 REST 5xx → return). **nas_sync.py:36 = module-level + test patch 의존** = cutover 시 test patch target 변경 필요 (`mctrader_engine.backtest.nas_sync.NASUploader` → `data_client.reverse_write` 또는 wrapper) |
| MCT-184 routes_v1.py LAND surface | `src/mctrader_data/api/routes_v1.py` 372 lines (post-merge fix `e612296` 적용 후 — Story 박제 307 lines 는 LAND 시점 박제. 본 Change Plan 박제 = 372 lines 정정). 5 endpoint: `:45 @router.get` historical/candles + `:110 @router.get` historical/candles/l1 + `:160 @router.post` reverse-write/paper-candles + `:326 @router.post` reverse-write/backtest-artifact + `:365 @router.get` /health | Bash `grep -nE` 실측 ✓ — **historical/orderbook endpoint = 미LAND 확정** (V6 추가 사실, executor/tick_replay.py:26,559 cutover scope 대상이 MCT-184 routes_v1.py 에 부재 → 본 Story data#N 에 신규 endpoint 추가 의무 = §3.3) |
| data realtime_stream.py + redis client 사용 | `src/mctrader_data/api/realtime_stream.py` = **ABSENT** (V4) + `pyproject.toml:20 "redis[hiredis]>=5"` 기존 가용 + data 측 `XADD market:tick`/`REDIS_KEY_PREFIX` grep = **0건** (신규 도입 — 본 Story 가 첫 Redis Stream publisher) | Test-Path + Grep 실측 ✓ — 신규 배치 충돌 0 + 신규 의존 0 |
| engine data_client/ + httpx 의존 | `src/mctrader_engine/data_client/` = **ABSENT** (V5) + engine `pyproject.toml` `httpx`/`requests` grep = **0건** (신규 의존 추가 필요 — 본 Story 가 첫 HTTP client 도입) | Bash 실측 ✓ — 신규 서브패키지 배치 충돌 0 + httpx 신규 의존 추가 의무 |
| TickRowV1_1 SSOT (market-core) + data aggregation 사용 | `mctrader-market/src/mctrader_market/schemas/tick.py:62 class TickRowV1_1(BaseModel)` + `mctrader-data/src/mctrader_data/aggregation/core.py:36 from mctrader_market.schemas.tick import TickRowV1_1` (MCT-182 LAND 정합) + `mctrader-market/src/mctrader_market/aggregation/core.py:39` 동형 (Layer 0 contract) | Bash 실측 ✓ — Milestone-2 tick.v1.1 정규화 schema SSOT = market-core Layer 0. data realtime_stream.py publisher = 동일 SSOT 재사용 (Layer 0 contract) |
| ADR-030 §D15 Redis prefix SSOT | `docs/adr/ADR-030-docker-stack-governance.md:439-449` 3 namespace 박제 (`signal:*` signal-collector + `market:*` data tick+orderbook + `engine:*` paper-engine position+state) + `REDIS_KEY_PREFIX_ENGINE=engine` env 박제 + signal-collector 5종 dual write 패턴 박제 | grep 실측 ✓ — **`market:*` prefix** = mctrader-data Redis namespace (본 Story Redis Stream publisher = `market:` prefix 정합) + `REDIS_KEY_PREFIX_MARKET` env 미정의 (본 Story 도입 가능 = 설계 §3.2) |
| R2 MCT-43~47 active branch | engine repo `git branch -a` MCT-43~47 named branch = **0건** + `git log` MCT-43~47 commit = **0건** (활성 진행 0건 발견 — Story §7.1 R2 mitigation 정합) | Bash 실측 ✓ — R2 cross-cutting risk **LOW** (paper_runner.py + executor/tick_replay.py 공유 모듈 위험 가설은 유효 but 활성 MCT-43~47 진행 0 — Phase 0 evidence baseline 확보) |

### 2.2 CodebaseMapper 유지 근거 (보수 변호)

- **MCT-184 routes_v1.py 4 endpoint = byte-for-byte 보존** (post-merge fix `e612296` LAND
  후 372 lines, F-1/F-2/F-4 data correctness 차단 + INV-3 sha256 + bytes-level 정밀도 정합).
  본 Story = endpoint **확장 + 신규 historical/orderbook 추가만** (기존 4 endpoint 무변경
  + /health 무변경).
- **MCT-183 io/ 6 module = mctrader-data Layer 2 자족 보존** (engine 역의존 0). 본 Story
  cold-read cutover = io/ reader wrap REST endpoint 소비 (io/ 자체 변경 0).
- **paper_runner.py:290,291 lazy import + graceful skip 패턴 보존** (best-effort `_write_paper_partition_safe`
  + ImportError graceful skip). REST cutover 시 동일 패턴 유지 (`httpx.HTTPError` 또는 `ImportError`
  → graceful skip 의무) — 기존 동작 contract 보존.
- **nas_sync.py:36 module-level lazy import + test patch target 보존 의무**. 본 Story
  cutover = test patch target 변경 (data_client wrapper 경유) 정합. **보수 변호: 기존 test
  자산 무변경 보존 — patch target 만 변경**.

## 3. 설계 결정 (Refactor 혁신 + SecurityArch 위협 + OperationalRiskArch 운영 + chief author synthesis)

### 3.1 data realtime_stream.py 신설 (Refactor — to-be 구조 + 최소 변경 경로)

> **Refactor deputy perspective (혁신/옹호자)** — Redis Stream publisher 최소 변경 경로
> + tick.v1.1 정규화 schema 정합 (Layer 0 contract SSOT 재사용).

```
src/mctrader_data/api/
  __init__.py              ── 기존 (MCT-184 LAND, public surface export 갱신)
  app.py                   ── 기존 (MCT-184 LAND, lifespan hook 에 realtime publisher 라이프사이클 통합 = §3.2.3 — 신규 publisher 가 ASGI startup/shutdown 정합)
  routes_v1.py             ── 기존 + MODIFY (§3.3 — historical/orderbook endpoint 신설)
  realtime_stream.py       ── NEW (Redis Stream publisher — RealtimeStreamPublisher class
                                + tick.v1.1 정규화 schema (TickRowV1_1 market-core SSOT)
                                + XADD market:tick:{exchange}:{symbol} (ADR-030 §D15 prefix 정합)
                                + 거래소별 raw → 정규화 변환 (data 단독 책임, market-core
                                  CandleProvider/OrderBookProvider Protocol 활용))
  deps.py                  ── 기존 + MODIFY (RealtimeStreamPublisher DI provider 추가)
  arrow_ipc.py + schemas.py ── 기존 (MCT-184 LAND, 변경 0)
```

- **최소 변경 경로 (Refactor 옹호)**: realtime_stream.py = MCT-184 api/ 패키지 내 신규
  추가 (api/ 자체 구조 변경 0 — 기존 6 파일 무변경 + 1 파일 추가). 기존 redis[hiredis]
  의존 재사용 (신규 의존 0 — pyproject 변경 0). tick.v1.1 정규화 = market-core `TickRowV1_1`
  Layer 0 SSOT 재사용 (재구현 0 — `from mctrader_market.schemas.tick import TickRowV1_1`
  data aggregation/core.py:36 패턴 답습).
- **OpenAPI 무영향 (Refactor + chief author 합치)**: Redis Stream publisher = REST endpoint
  **아님** (FastAPI route 0 — `routes_v1.py` 변경은 historical/orderbook endpoint 만,
  realtime_stream.py 는 routes_v1.py 미등록). OpenAPI snapshot drift = 0 (cross-repo-contract-lock-check
  무영향).
- **lifespan 통합**: `app.py` lifespan hook 에 `RealtimeStreamPublisher.startup()` /
  `.shutdown()` 통합 (ASGI uvicorn `--timeout-graceful-shutdown=60` 정합 — XADD in-flight
  drain 후 Redis connection close). MCT-184 패턴 답습.

### 3.2 Redis Stream key naming + tick.v1.1 정규화 schema 정합 (chief author + Refactor)

```
Redis Stream key naming SSOT (ADR-030 §D15 prefix 정합):
  XADD market:tick:{exchange}:{symbol}  *  <field-value pairs>
  e.g. XADD market:tick:bithumb:BTC_KRW * ts_utc 2026-05-17T... price 100000000 ...
       XADD market:tick:upbit:KRW-BTC * ts_utc ... price ... ...

env override (default = market):
  REDIS_KEY_PREFIX_MARKET = os.environ.get("REDIS_KEY_PREFIX_MARKET", "market")
  stream_key = f"{REDIS_KEY_PREFIX_MARKET}:tick:{exchange}:{symbol}"

payload fields (TickRowV1_1 market-core contract — Milestone-2 LAND SSOT 정합):
  ts_utc (UTCDateTime ISO8601), price (Decimal str), quantity (Decimal str),
  side (Literal["buy","sell"]), trade_id (str), exchange (str), symbol (Symbol str)
  → Redis field-value = TickRowV1_1.model_dump_json() 직렬화 (Pydantic strict)

MAXLEN ~= 100_000 (approximate trim, 메모리 bound — ~10MB upper budget)
  XADD market:tick:{exchange}:{symbol} MAXLEN '~' 100000 * <fields>
```

- **tick.v1.1 정규화 schema 정합 (INV-3)**: payload = `TickRowV1_1` (Layer 0 contract SSOT,
  market-core `schemas/tick.py:62`). 거래소별 raw → 정규화 변환 = data 단독 책임 (이미 MCT-182 LAND market-core protocols
  `CandleProvider/OrderBookProvider` Layer 0 Protocol — data `aggregation/core.py:36` 패턴
  답습 = data adapters.py 정규화 layer 가 raw → TickRowV1_1 변환 후 publisher 호출).
- **ADR-030 §D15 정합**: `market:` prefix namespace (`signal:`/`market:`/`engine:` 3
  namespace 박제, mctrader-data tick+orderbook = `market:*` SSOT). `REDIS_KEY_PREFIX_MARKET`
  env 도입 (default `market`, signal-collector dual write 패턴 답습 — 본 Story 는 신규
  publisher 라 dual write 불필요, default prefix only).
- **MAXLEN trim**: Redis Stream 자연 GC (approximate `~` flag = MAXLEN soft bound). 100_000
  entry × tick payload (~100 bytes) = ~10MB upper budget per stream key. consumer 측
  (MCT-186) `XREAD` 또는 `XREADGROUP` 진입 후 ack 정합 (consumer group = MCT-186 owner).

### 3.3 historical/orderbook endpoint 신설 (MCT-184 amendment 분리 vs 본 Story 포함 판단)

> **V6 추가 사실** — MCT-184 routes_v1.py = candles + candles/l1 + reverse-write × 2 +
> /health (5 endpoint) LAND. `executor/tick_replay.py:26,559 from mctrader_data.orderbook_replay
> import (...)` cutover scope 대상 historical/orderbook endpoint = **미LAND 확정**. cutover
> 완결을 위해서는 endpoint 신설 의무.

**판단 (chief author + Refactor + OperationalRiskArch consult)**: **본 Story data#N 에
endpoint 추가 채택** (MCT-184 amendment 분리 기각).

**근거**:
- **lock-step 의존 증가 차단**: MCT-184 amendment 분리 시 = MCT-184 post-merge amendment
  PR 추가 + 본 Story land_order 의존 추가 (amendment LAND → engine cutover 가능). 이미
  MCT-184 hub#360 amendment + post-merge fix `e612296` 가 carry 누적 — PMO-AUDIT-MCT-184
  §3 패턴 #3 (분리된 post-merge amendment 누적 위험) 동형 차단.
- **cutover 완결 의무**: D2 cold-read cutover 의 8곳 중 2곳 (executor/tick_replay.py:26,559)
  이 endpoint 부재로 cutover 불가 시 D2 VERIFIED amendment box 박제 불가 (부분 cutover =
  ADR-031 §D2 VERIFIED 박제 자체 무효화).
- **OpenAPI SSOT 단방향 강제**: 본 Story = endpoint 신설 + OpenAPI emit 갱신 + hub
  `.codeforge/contracts/data-api-v1.openapi.json` snapshot 동반 갱신 + `cross-repo-contract-lock-check.sh`
  drift gate (MCT-184 LAND 자산 재사용 — script 변경 0).

**endpoint 시그니처**:

```
GET /v1/historical/orderbook/snapshots
  query params:
    exchange: str (allowlist regex ^[a-z0-9_-]+$ — path traversal 차단)
    symbol: str (allowlist regex ^[A-Z0-9_/-]+$)
    date: str (ISO date ^\d{4}-\d{2}-\d{2}$)
    start_ts: datetime (ISO8601 UTC)
    end_ts: datetime (ISO8601 UTC, max range 24h)
  → io/ reader wrap: orderbook_replay.scan_orderbook_events (cold_reader/tier_reader 경유)
  → response: StreamingResponse (Arrow IPC stream — application/vnd.apache.arrow.stream)

GET /v1/historical/orderbook/ticks
  query params: (동일)
  → io/ reader wrap: orderbook_replay.scan_ticks
  → response: StreamingResponse (Arrow IPC stream)
```

- engine `executor/tick_replay.py:26,559` 의 `OrderbookSnapshot` + `scan_orderbook_events`
  + `scan_ticks` + `_orderbook_partition_dir` + `_tick_partition_dir` symbol cutover →
  `data_client.historical.fetch_orderbook_snapshots` + `.fetch_orderbook_ticks` + (partition
  dir resolve 는 client-side path 산출 함수 신규 — `data_client.historical.compute_partition_dir`)
  정합. **engine 측 _orderbook_partition_dir / _tick_partition_dir 의 path 산출 로직 = data
  측 `mctrader_data.orderbook_replay` 의 내부 helper** → cutover 시 client-side reimplementation
  (path 산출 ≠ NAS object layout — engine 이 NAS 알면 안 됨 D2/ADR-029 정합. partition
  dir 산출은 Hive layout 기반 deterministic 함수, data import 없이 client-side 가능).

### 3.4 engine data_client/ 신설 (Refactor — thin hand-written client)

```
src/mctrader_engine/data_client/
  __init__.py            ── public surface (HistoricalClient + ReverseWriteClient export)
  base.py                ── 공통 httpx Client lifecycle + retry/timeout/circuit-breaker
                            + base URL env (DATA_API_BASE_URL default http://data-api:8000)
                            + auth (None → MCT-184 carry, MCT-186 owner internal auth)
  historical.py          ── fetch_candles(exchange, symbol, timeframe, start, end, root)
                            + fetch_candles_l1(symbol, date, hour)
                            + fetch_orderbook_snapshots(...) + fetch_orderbook_ticks(...)
                            → Arrow IPC stream deserialize → TickRecord/OrderbookEventRecord
                              /CandleModel (market-core SSOT 정합)
                            + compute_partition_dir(...) — client-side path 산출 helper
  reverse_write.py       ── post_paper_candles(candles, run_id, snapshot_id, lineage)
                            + post_backtest_artifact(run_dir, run_id)
                            → idempotent sha256 client-side (canonical_jsonl_hash 재사용
                              from mctrader_market.paper_lineage — MCT-182 LAND SSOT
                              정합) + INV-3 정합 (MCT-184 post-merge fix e612296 F-2 정합)
  exceptions.py          ── DataClientError + DataClientTimeoutError + DataClientServerError
                            (retry/circuit-breaker → 마지막 fallback exception)
```

- **OpenAPI generator vs hand-written 결정 = hand-written thin client 채택 (Refactor 옹호)**:
  근거 = (1) MCT-184 routes_v1.py = 4 endpoint (+ 본 Story 추가 2 = 6 endpoint) 소규모
  surface — generator 도구 도입 overhead (`openapi-python-client` 신규 의존 + 빌드 step)
  vs hand-written 단순성 (httpx + Pydantic 만으로 충분) trade-off → hand-written 우위.
  (2) Pydantic schema = market-core SSOT 재사용 (TickRecord/OrderbookEventRecord/CandleModel/PaperLineage),
  generator 가 만들어내는 별도 client-side schema 클래스 = SSOT 단일 위반 (Layer 0 contract
  re-define 위험) — hand-written 이 SSOT 단일 정합.
  (3) OpenAPI SSOT 단방향 (INV-1) 정합 — engine 측 OpenAPI 정의 0 (hand-written 가
  generator 의 단방향 가정 만족 — 단방향 자연 성립).
- **httpx 의존 신규 추가 (`httpx>=0.27`)**: engine `pyproject.toml` dependencies 추가.
  async/sync 둘 다 가능 (engine 기존 코드 = sync — `cli.py`/`wfo` 동기 path, `executor/tick_replay.py`/`runtime/paper_runner.py`
  = sync). **sync httpx Client 채택** (engine 기존 동기 호출 패턴 정합 — async 도입 = 호출부
  asyncio 통합 의무 발생, 본 Story scope 외 = §3.5 paper_lineage cutover 와 동일 분리 원칙).
- **base URL env**: `DATA_API_BASE_URL` (default `http://data-api:8000` — ADR-030 §D14
  collector pattern 답습 + ADR-030 single-host loopback 정합). 실 compose wiring = MCT-186
  (engine NAS cred drop) owner.
- **retry/timeout 패턴**: `httpx.Client(timeout=httpx.Timeout(connect=5, read=30, write=30, pool=5))`
  + retry (exponential backoff 3 회, 429/503/504 retryable) + circuit-breaker
  (window 60s 내 5xx 5회 OR p99 >5s 3회 = OPEN, 30s 후 HALF_OPEN — MCT-170 dr_mode 패턴
  답습 = §7.4 OperationalRiskArch primary). MCT-184 carry-over (auth) = MCT-186 owner.

### 3.5 paper_runner.py:290 paper_lineage market-core 직독 변경 분리 판단

> **요구사항 §7.2 인계 항목 5 — 본 Story cutover 포함 vs MCT-188 cleanup 분리**.

**판단 (chief author + CodebaseMapper consult)**: **본 Story cutover 포함 채택** (MCT-188
shim cleanup 분리 기각).

**근거**:
- **D7 grep0 quad gate (MCT-188) 부담 감소**: paper_runner.py:290 paper_lineage 는 본
  Story reverse-write cutover (`runtime/paper_runner.py:290,291`) 와 **동일 lazy import
  블록 내** 위치 (line 290-291 = 2 import 동시) — cutover 시 동일 hunk 수정. MCT-188 분리
  시 = 동일 hunk 재방문 비용 + diff 복잡도 증가 + post-merge audit risk.
- **paper_lineage market-core 직독 변경 = MCT-182 LAND 후 안전**: market-core
  `mctrader_market.paper_lineage` SSOT = `PaperLineage` + `canonical_jsonl_hash` 둘 다
  보존 (MCT-182 LAND 정합). engine 측 shim re-export 동작 정상 → market-core 직독 변경 =
  `from mctrader_market.paper_lineage import PaperLineage, canonical_jsonl_hash` 단순
  import path 변경 (재구현 0).
- **MCT-188 shim 잔존 4곳으로 축소**: 본 Story cutover 후 MCT-188 owner = `tick_storage`/`orderbook_storage`/`aggregation`
  shim re-export 5곳 → 4곳 (paper_lineage 1곳 본 Story 포함) = `executor/tick_replay.py:31,32`
  + `hot/state_machine.py:33` + `strategy/templates/tick_scalping.py:76`. MCT-188 D7
  grep0 quad gate scope 축소.

**변경 hunk** (paper_runner.py:290-291):
```python
# AS-IS (lazy import 내부 — _write_paper_partition_safe best-effort):
from mctrader_data.paper_lineage import PaperLineage, canonical_jsonl_hash
from mctrader_data.paper_storage import write_paper_candles

# TO-BE (cutover):
from mctrader_market.paper_lineage import PaperLineage, canonical_jsonl_hash  # market-core 직독 (MCT-182 LAND SSOT)
from mctrader_engine.data_client.reverse_write import ReverseWriteClient  # REST cutover
# ... (write_paper_candles 호출 부분 ReverseWriteClient.post_paper_candles 로 wrap, lazy + graceful skip 패턴 보존)
```

### 3.6 D-row ↔ scope_manifest 전수 1:1 reconcile (MCT-179 lesson reapply)

| 항목 | scope_manifest SSOT | 본 Change Plan / ADR amendment box | reconcile |
|------|---------------------|-----------------------------------|-----------|
| D2 option_chosen | `§design_decisions.D2.option_chosen: io-relocate + cold-read-behind-REST` | §1.1 = cold-read-behind-REST 절반 (cold-read 8곳 cutover 완결 + io-relocate = MCT-183 LAND) | ✅ 1:1 |
| D2 owner_story | `§design_decisions.D2.owner_story: MCT-183 (io relocate) + MCT-185 (cold-read cutover)` | §3.3-3.4 cold-read 8곳 cutover + §10 ADR-031 §D2 VERIFIED amendment box (MCT-185 cutover 절반 완결) | ✅ 1:1 |
| D3 option_chosen | `§design_decisions.D3.option_chosen: fastapi-v1 + redis-stream` | §1.1 = redis-stream + reverse-write client 절반 (fastapi-v1 = MCT-184 LAND historical+reverse-write 절반) | ✅ 1:1 |
| D3 owner_story | `§design_decisions.D3.owner_story: MCT-184 (historical+reverse-write) + MCT-185 (realtime stream)` | §3.1-3.2 realtime stream publisher 신설 + §3.4 reverse-write client cutover (engine 측 wiring 완결) + §10 ADR-031 §D3 VERIFIED amendment box | ✅ 1:1 |
| MCT-185 decisions | `§story_decision_matrix.MCT-185.decisions: [D2, D3]` | frontmatter `decisions: [D2, D3]` | ✅ 1:1 |
| MCT-185 cross_repo | `§story_decision_matrix.MCT-185.cross_repo` (hub/data/engine 3 entry) | §9.1 land_order (hub P1 → data#N → engine#N → hub P2) | ✅ 1:1 (3 repo — MCT-184 2 repo 대비 가장 복잡) |
| land_order | `§story_decision_matrix.MCT-185.land_order: hub Phase1 → data#N → engine#N → hub Phase2 PR2` | §9.1 | ✅ 1:1 |
| ADR-029 amendment | `§planned_adrs.amendments[0]` ADR-029 `owner_story: MCT-183 (relocate) + MCT-185 (cutover confirm)` | ADR-029 §D2 VERIFIED amendment box (MCT-185 cutover confirm 절반 — cold-read 8곳 REST indirection 실 적용 박제, POLICY_FINALIZED 본문 무변경) | ✅ 1:1 |
| ADR-027 amendment | `§planned_adrs.amendments[1]` ADR-027 `owner_story: MCT-183 (io reader 6 module relocate)` | 본 Story 비참여 (MCT-183 LAND 완결 — io reader 6 module relocated 박제 = MCT-183 owner) | ✅ 1:1 (owner 분리 명시) |
| ADR-030 amendment | `§planned_adrs.amendments[2]` ADR-030 `owner_story: MCT-184 (data api service) + MCT-186 (engine NAS cred drop)` | 본 Story = cross-ref only (Redis Stream loopback 정합 재명시 — 정책 무변경. 실 compose wiring + NAS cred drop = MCT-186 owner) | ✅ 1:1 (cross-ref 명시) |
| ADR-031 §D2 | `§design_decisions.D2` | ADR-031 §D2 VERIFIED amendment box (cold-read cutover 완결) — Status `Accepted` 유지 (POLICY_FINALIZED = MCT-188) | ✅ 1:1 |
| ADR-031 §D3 | `§design_decisions.D3` | ADR-031 §D3 VERIFIED amendment box (realtime stream + reverse-write wiring 완결) — Status `Accepted` 유지 | ✅ 1:1 |
| historical/orderbook endpoint 신설 | scope_manifest 미명시 (MCT-184 LAND surface = candles+candles/l1+reverse-write × 2) | §3.3 본 Story data#N 에 신규 endpoint 추가 (cutover 완결 의무) + OpenAPI snapshot 갱신 + cross-repo-contract-lock-check.sh 정합 | ✅ 1:1 (scope_manifest §planned_files.mctrader-hub `.codeforge/contracts/data-api-v1.openapi.json` MCT-184 owner 의 본 Story 확장 — MCT-188 final POLICY_FINALIZED 까지 amendment 누적 패턴 정합) |
| paper_runner.py:290 paper_lineage cutover | scope_manifest `§planned_files.mctrader-engine` MCT-188 owner shim cleanup | §3.5 본 Story cutover 포함 채택 = MCT-188 owner shim 잔존 5곳 → 4곳 축소 (D7 grep0 quad gate scope 사전 축소) | ✅ 1:1 (MCT-188 owner 축소 명시) |

**reconcile verdict**: 본 Change Plan §3 ↔ scope_manifest `§design_decisions.D2/D3` +
`§story_decision_matrix.MCT-185` + `§planned_adrs.amendments` ADR-029/027/030 ↔
ADR-029 §D2 amendment box ↔ ADR-031 §D2/§D3 amendment box ↔ Story §2/§4 DELTA **전수 1:1
정합** (13/13 row). MCT-182/183/184 D-row reconcile 패턴 계승. 1차 FIX 발생 시 정정 산출물
list ↔ 전 산출물 동반 reconcile 체크리스트 의무 (cross-document desync 6회 누적 동형 사전
차단).

### 3.6.1 §3.6.1 gate v2 cross-Story reapply 박제 (MCT-179/182/183/184 desync 동형 영구 차단 forcing function)

> **PMO-AUDIT-MCT-184 §4.5 (e) + §6.2 reapply #3 의무** — plugin-codeforge#795 OPEN
> (cross-document SSOT mechanical gate 미가용) → mctrader-hub self-discipline 유지.
> MCT-184 §3.6.1 gate v2 패턴 SSOT 차용 (glob-scope + 변형포괄 + self-verify TEST1/TEST2).
> cross-document SSOT desync 6회 누적 (MCT-179 + MCT-182 §4.2 + MCT-183 iter1/2/3 + MCT-184
> ADR-031 §D3 amendment box stale) 동형의 영구 차단.

**canonical string (MCT-185 ADR-029/031/030 amendment box SSOT — byte 동일 의무)**:

ADR-029 §D2 VERIFIED amendment box canonical (POLICY_FINALIZED 본문 무변경 박제):
```
§D2 VERIFIED amendment box (MCT-185 LAND 박제)
```
ADR-031 §D2 + §D3 VERIFIED amendment box canonical (Status Accepted 유지):
```
§D2 VERIFIED (cold-read cutover 완결) + §D3 VERIFIED (realtime stream + reverse-write wiring 완결)
```
ADR-031 Status canonical (POLICY_FINALIZED 전이 = MCT-188 owner 명시):
```
Status Accepted 유지 (POLICY_FINALIZED 전이 = MCT-188)
```
ADR-030 cross-ref canonical (정책 무변경 + 본문 19 D 무변경):
```
Redis Stream loopback 정합 cross-ref (본문 19 D 무변경, POLICY_FINALIZED 보존)
```

**MCT-185 cross-document SSOT desync grep gate v2 (glob-scope + 변형포괄 — data#N + engine#N
착수 전 + DesignReview/CodeReview lane verdict 직전 의무 검증, 실 stale != 0 시 P0 차단)**:

```bash
# scope = glob 기반 (지정 목록 탈피 — 본 Epic 권위 SSOT 전수 + 차후 누락 방지):
#   docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md
#   scope_manifests/EPIC-data-domain-decoupling.yaml .codeforge/contracts/*.json
#
# pattern 1 = ADR-031 §D2/§D3 VERIFIED 표기 vs Status POLICY_FINALIZED 축약 stale 차단
#   (ADR-031 Status 는 본 Story = Accepted 유지 canonical, POLICY_FINALIZED 축약 표기는
#   MCT-188 owner 시점 — Stale 검출)
grep -rnE "ADR-031[^\n]{0,40}(Status|status)[^\n]{0,30}POLICY_FINALIZED" \
  docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md \
  scope_manifests/EPIC-data-domain-decoupling.yaml .codeforge/contracts/*.json 2>/dev/null \
  | grep -ivE "POLICY_FINALIZED 전이 = MCT-188|POLICY_FINALIZED = MCT-188|MCT-188 owner|Status Accepted 유지|amendment box only|FIX Ledger|grep gate|gate 패턴|grep -rnE|canonical string|TEST[12]|§3\.6\.1|self-verify|→ \`POLICY_FINALIZED\` 전이|MCT-188 \|$|owner = MCT-188|stale 차단|단독 축약|기대:"
# 예외 필터 보강 (gate self-verify TEST2 false positive 0 조건 충족):
#   - `→ \`POLICY_FINALIZED\` 전이` = "Status `Accepted` → `POLICY_FINALIZED` 전이" canonical (정상 — 전이 시점 박제, 비목표 표 행 형식)
#   - `MCT-188 \|$` = 비목표 표 행 마지막 column "| MCT-188 |" 형식 (정상 — owner 분리 명시)
#   - `owner = MCT-188` = ADR-031 §D2/§D3 amendment box canonical (정상 — POLICY_FINALIZED owner)
#   - `stale 차단` / `단독 축약` / `기대:` = gate 정의 본문 comment line 차단 (정상 — gate 자체 인용)

# pattern 2 = ADR-029 본문 정책 변경 carry 차단 (POLICY_FINALIZED 무변경 위반 검출)
grep -rnE "ADR-029[^\n]{0,40}(11 D|본문)[^\n]{0,30}(변경|수정|amend 본문)" \
  docs/adr/ADR-029-tier-promotion-single-source.md docs/adr/ADR-031-data-domain-decoupling.md \
  docs/stories/MCT-185.md docs/change-plans/MCT-185-change-plan.md \
  scope_manifests/EPIC-data-domain-decoupling.yaml 2>/dev/null \
  | grep -ivE "본문 11 D 정책 무변경|무변경 \(POLICY_FINALIZED|정책 무변경|amendment box only|VERIFIED amendment box only"

# pattern 3 = ADR-030 본문 정책 변경 carry 차단 (POLICY_FINALIZED 본문 19 D 무변경)
grep -rnE "ADR-030[^\n]{0,40}(19 D|본문)[^\n]{0,30}(변경|수정|amend 본문)" \
  docs/adr/ADR-030-docker-stack-governance.md docs/adr/ADR-031-data-domain-decoupling.md \
  docs/stories/MCT-185.md docs/change-plans/MCT-185-change-plan.md \
  scope_manifests/EPIC-data-domain-decoupling.yaml 2>/dev/null \
  | grep -ivE "본문 19 D 정책 무변경|무변경 \(POLICY_FINALIZED|정책 무변경|amendment box only|cross-ref only|정책을 무변경|D 정책을 무변경|stale 차단|단독 축약|기대:|grep -rnE"
# 예외 필터 보강 (gate self-verify TEST2 false positive 0 조건 충족):
#   - `정책을 무변경` = "ADR-030 본문 19 D 정책을 무변경한다" canonical (정상 — 명시 무변경 박제)
#   - `stale 차단` / `단독 축약` / `기대:` / `grep -rnE` = gate 정의 본문 comment line 차단 (정상 — gate 자체 인용)

# 기대: 3 grep 모두 0줄 (실 stale 0). 매치 발생 = (1) ADR-031 Status POLICY_FINALIZED 축약
#   carry OR (2) ADR-029 본문 정책 변경 carry OR (3) ADR-030 본문 정책 변경 carry → P0 차단
```

> **gate self-verify (pattern 유효성 실증 — 매 gate 변경 시 의무, MCT-184 §3.6.1 패턴
> SSOT 차용)**:
>
> - **TEST1 (포착력)**: stale 변형 `ADR-031 Status POLICY_FINALIZED (MCT-185 LAND 박제)`
>   (잘못된 단독 POLICY_FINALIZED 축약 — 본 Story 는 Status `Accepted` 유지가 canonical,
>   POLICY_FINALIZED 전이는 MCT-188 owner) → pattern 1 `ADR-031[^\n]{0,40}(Status|status)[^\n]{0,30}POLICY_FINALIZED`
>   **MATCH ✓** (예외 필터 `POLICY_FINALIZED 전이 = MCT-188|Status Accepted 유지` 미동반
>   → 검출). canonical `Status Accepted 유지 (POLICY_FINALIZED 전이 = MCT-188)` 는 예외
>   필터로 제외 = false positive 0.
> - **TEST2 (false positive 0)**: canonical string `ADR-031 §D2/§D3 VERIFIED amendment
>   box (Status Accepted 유지, POLICY_FINALIZED 전이 = MCT-188)` → pattern 1 + 예외 필터
>   `POLICY_FINALIZED 전이 = MCT-188|Status Accepted 유지` **NO MATCH ✓**. ADR-029/030
>   본문 무변경 canonical 도 pattern 2/3 + 예외 필터로 NO MATCH ✓.

> **예외 (정상 잔존, gate 무위반 — `grep -ivE` 필터 명문)**:
> - `POLICY_FINALIZED 전이 = MCT-188` / `POLICY_FINALIZED = MCT-188` / `MCT-188 owner`
>   (ADR-031 Status 전이 시점 박제 — 정상)
> - `Status Accepted 유지` / `amendment box only` / `VERIFIED amendment box only` (정상 —
>   본 Story Status 유지 박제)
> - `본문 11 D 정책 무변경` / `정책 무변경 (POLICY_FINALIZED` (ADR-029 무변경 박제)
> - `본문 19 D 정책 무변경` / `cross-ref only` (ADR-030 무변경 박제)
> - FIX Ledger iter row / gate 패턴 정의 자체 / canonical string 인용 / §3.6.1 / self-verify
>   TEST1/TEST2 설명 (필터 제외)
> - `docs/retros/*` 과거 Story 회고 = glob scope 미포함 (gate scope 외)

> **sibling Story 산출물 canonical 정정 의무 (MCT-184 §3.6.1 패턴 계승 — 전수성 절대
> 보장)**: glob scope `docs/stories/MCT-18*.md` = MCT-182/183/184 sibling 포함. sibling
> Story frontmatter `related_adrs` + Continuity 표 의 ADR-031 Status 기술 (`Status Accepted
> 유지` + `POLICY_FINALIZED 전이 = MCT-188`) = canonical 통일 대상. owner-scope 를 기술하는
> 모든 Epic 권위 SSOT (Story frontmatter/cross_repo/Continuity 표) sibling 라도 canonical
> 통일 의무.

**전수성 절대 보장 명령 (지정 목록 탈피 — repo-wide grep, post-LAND 의무)**:
```bash
grep -rn "ADR-031" docs/ scope_manifests/ .codeforge/contracts/ 2>/dev/null \
  | grep -iE "Status|status" \
  | grep -ivE "Status Accepted 유지\|POLICY_FINALIZED 전이 = MCT-188\|POLICY_FINALIZED = MCT-188\|MCT-188 owner\|amendment box only\|FIX Ledger\|gate 패턴\|grep gate\|canonical\|TEST[12]\|self-verify"
# 기대: ADR-031 Status POLICY_FINALIZED 단독 축약 0줄 (canonical/이력/gate정의/retros 외 —
#   실 stale 0 확인. post-LAND evidence 첨부 의무)
```

본 gate v2 = MCT-179 (ADR-030 D5/D8 swap) + MCT-182 (§4.2 self-contradiction) + MCT-183
iter1→3 (ADR-027 amendment 축약) + MCT-184 (ADR-031 §D3 amendment box stale) **cross-document
SSOT desync 6회 누적 동형의 영구 차단 forcing function** (PMO-AUDIT-MCT-184 §4.5 (e) +
§6.2 reapply #3 Option A self-discipline 자기검증 박제 — glob-scope + 변형포괄 + self-verify
TEST1/TEST2). 수동 reconcile 한계 자체 = codeforge upstream ADR escalation 후보
(plugin-codeforge#795 OPEN — mechanical gate 가용 전 까지 self-discipline 유지).

### 3.6.2 박제 PR self-discipline (plugin-codeforge#804 OPEN) — 5 체크리스트 inline 박제

> **PMO-AUDIT-MCT-184 §4.3 + §6.2 reapply #7 의무 — self-discipline carrier 2번째 (MCT-184
> 첫 번째 ↔ 본 Story 두 번째 = 1회 실증 효력 검증)**. Phase 2 PR2 박제 LAND 전 5 체크
> 전수 PASS 의무. MCT-184 hub#359 부분 박제 (≈58% carry) + hub#360 amendment 동형 재발
> 사전 차단.

| # | 체크 | 검증 방법 | LAND 차단 조건 |
|---|------|----------|---------------|
| 1 | RETRO-MCT-185.md 존재 | `ls docs/retros/RETRO-MCT-185.md` exit 0 | 부재 시 차단 (PMOAgent sub-dispatch 산출 의무) |
| 2 | EPIC-RESULTS §Story-4 박제 (milestone 4/7 + D2/D3 VERIFIED) | `grep "§Story-4" docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` exit 0 + milestone 3/7→4/7 + D2/D3 VERIFIED 박제 본문 | 부재/매치 0 시 차단 |
| 3 | Story frontmatter `status: COMPLETED` 전환 + `completed_at` 박제 | `grep -E "^status: phase:박제-COMPLETED\|^completed_at:" docs/stories/MCT-185.md` 양쪽 매치 | 부재 시 차단 |
| 4 | CLAUDE.md `hub#TBD` 잔존 0줄 (모든 cross-ref hub#NNN 정합) | `grep -nE "hub#TBD" CLAUDE.md` exit 1 (no match) | 매치 ≥1 시 차단 |
| 5 | ADR-029 §D2 + ADR-031 §D2/§D3 VERIFIED amendment box LAND confirm | `grep -E "§D2 VERIFIED amendment box \(MCT-185 LAND" docs/adr/ADR-029-tier-promotion-single-source.md` + `grep -E "§D[23] VERIFIED" docs/adr/ADR-031-data-domain-decoupling.md` 양쪽 매치 | 부재 시 차단 |

### 3.6.3 Codex post-LAND audit 4 axis self-discipline (plugin-codeforge#805 OPEN)

> **PMO-AUDIT-MCT-184 §4.4 + §6.2 reapply #8 의무**. LAND 후 Codex post-LAND audit 4 axis
> 의무 운용. **cutover Story 특수성 = silent data corruption + INV-3 mismatch + bytes-level
> 정밀도 영역 sentinel sentry 의무 강화** (MCT-184 F-1/F-2/F-4 = data correctness 영역
> 4건 동형 재발 사전 차단 priority).

| axis | 검사 항목 | finding 처리 |
|------|----------|-------------|
| 1. production correctness | cutover 11곳 production 동작 정확성 (silent data corruption 차단) — engine backtest/WFO scenario 결과 cutover 전/후 byte-equivalence 확인 (INV-2 정합) | finding 시 별 post-merge fix PR carry over (MCT-184 hub#360 amendment 패턴) |
| 2. bytes-level 정밀도 | Arrow IPC byte-equivalence (MCT-184 INV-2 정합) + reverse-write idempotent sha256 정확성 (MCT-184 post-merge fix `e612296` F-2 정합) — paper_lineage canonical_jsonl_hash 호환성 확인 | finding 시 client-side sha256 hash key fix 별 PR |
| 3. SSOT 재검증 | §3.6.1 gate v2 post-LAND repo-wide grep 0줄 evidence + D-row 1:1 reconcile 확인 | drift 검출 시 정정 산출물 list ↔ 전 산출물 동반 reconcile 별 PR |
| 4. security | internal-only network (engine↔data compose internal) + Pydantic strict 유지 + R2 MCT-41 cross-cutting 후처리 (post-LAND MCT-43~47 진입 시 본 Story 11곳 5파일 grep + 충돌 발견 시 ordering 결정) | finding 시 R2 escalation Orchestrator ordering 결정 |

## 4. 외부 인터페이스

### 4.1 REST API surface (MCT-184 LAND + 본 Story 신설)

| method | path | 입력 | 출력 | wrap target | LAND |
|--------|------|------|------|-------------|------|
| GET | `/v1/historical/candles` | exchange/symbol/timeframe/start/end (MCT-184 LAND) | Arrow IPC stream | `tier_reader.read` / `cold_reader.read` (mctrader-data io/ Layer 2) | MCT-184 |
| GET | `/v1/historical/candles/l1` | symbol/date/hour (MCT-184 LAND) | Arrow IPC stream | `l1_reader.read` | MCT-184 |
| POST | `/v1/reverse-write/paper-candles` | PaperCandlesRequest + canonical sha256 idempotent (MCT-184 LAND + post-merge fix `e612296` F-2 정합) | 200 {written, path, idempotent_skip} | `paper_storage.write_paper_candles` | MCT-184 |
| POST | `/v1/reverse-write/backtest-artifact` | BacktestArtifactRequest (.done sentinel idempotent) | 200 {synced, idempotent_skip} | backtest-artifact NAS sync | MCT-184 |
| GET | `/v1/historical/orderbook/snapshots` (**신규**) | exchange/symbol/date/start_ts/end_ts (24h max range) | Arrow IPC stream | `orderbook_replay.scan_orderbook_events` (io/ reader wrap) | **MCT-185** |
| GET | `/v1/historical/orderbook/ticks` (**신규**) | exchange/symbol/date/start_ts/end_ts (24h max range) | Arrow IPC stream | `orderbook_replay.scan_ticks` | **MCT-185** |
| GET | `/openapi.json` | — | OpenAPI 3.x (SSOT = data, 본 Story 갱신) | FastAPI 내장 | MCT-184 |

### 4.2 Redis Stream surface (신규 — Layer 2 publisher only)

| stream key | producer | payload | consumer |
|------------|----------|---------|----------|
| `market:tick:{exchange}:{symbol}` | mctrader-data realtime_stream.RealtimeStreamPublisher (XADD MAXLEN ~ 100000) | TickRowV1_1 model_dump_json() (market-core SSOT) | MCT-186 engine subscriber (`XREAD` 또는 `XREADGROUP`) + 외부 consumer (다중 subscriber) |

- **OpenAPI SSOT 무영향**: Redis Stream = REST endpoint 아님 (FastAPI route 0 — OpenAPI
  snapshot drift 0).
- **ADR-030 §D15 정합**: `market:` prefix namespace (signal:/market:/engine: 3 namespace SSOT).
- **ADR-030 single-host loopback 정합**: data 측 publisher + consumer 측 = compose internal
  network only (외부 노출 0).

### 4.3 import surface (변경 표)

| consumer | AS-IS | TO-BE | 마이그레이션 |
|----------|-------|-------|-------------|
| engine `cli.py:279,280` | `from mctrader_data.path import resolve_data_root` + `from mctrader_data.storage import scan_candles` | `from mctrader_engine.data_client.historical import HistoricalClient` + `client.fetch_candles(...)` | D2 cold-read cutover (2/8) |
| engine `executor/tick_replay.py:26,559` | `from mctrader_data.orderbook_replay import (...)` (top-level + function-local) | `from mctrader_engine.data_client.historical import HistoricalClient` + `client.fetch_orderbook_snapshots(...)` / `.fetch_orderbook_ticks(...)` + client-side `compute_partition_dir(...)` helper | D2 cold-read cutover (2/8) + historical/orderbook endpoint 신설 의존 (§3.3) |
| engine `wfo/evaluator/data_loader.py:43,44` + `wfo/search/data_loader.py:81,82` | `from mctrader_data.path import resolve_data_root` + `from mctrader_data.storage import scan_candles` (× 2 파일) | `from mctrader_engine.data_client.historical import HistoricalClient` (동일 패턴) | D2 cold-read cutover (4/8) |
| engine `runtime/paper_runner.py:290,291` | (lazy import 내부) `from mctrader_data.paper_lineage import PaperLineage, canonical_jsonl_hash` + `from mctrader_data.paper_storage import write_paper_candles` | `from mctrader_market.paper_lineage import PaperLineage, canonical_jsonl_hash` (market-core 직독 cutover 포함, §3.5) + `from mctrader_engine.data_client.reverse_write import ReverseWriteClient` + `client.post_paper_candles(...)` (lazy + graceful skip 패턴 보존) | D3 reverse-write cutover (2/3) + paper_lineage market-core 직독 변경 |
| engine `backtest/nas_sync.py:36` | (module-level lazy) `from mctrader_data.nas_storage.nas_uploader import NASUploader  # type: ignore  # noqa: F401` | `from mctrader_engine.data_client.reverse_write import ReverseWriteClient` (module-level 또는 lazy 유지) + `client.post_backtest_artifact(run_dir, run_id)` | D3 reverse-write cutover (1/3) + **test patch target 변경 의무** (`patch("mctrader_engine.backtest.nas_sync.NASUploader")` → `patch("mctrader_engine.backtest.nas_sync.ReverseWriteClient")` 또는 wrapper) |
| engine src/ (전체) | (cold-read 8 + reverse-write 3 = 11곳 잔존) | **grep0** = engine src/ `from mctrader_data.(storage|path|orderbook_replay|paper_storage|nas_storage)` import == 0 (cutover 완결 — AC-3) | MCT-182 shim 5곳 잔존 → 본 Story `paper_runner.py:290 paper_lineage` cutover 포함 후 4곳 (MCT-188 owner) |
| data api/ (신규) | (MCT-184 LAND 6 파일) | + `realtime_stream.py` 신규 1 파일 (api/ 패키지 내 추가, deps.py DI provider 추가, app.py lifespan 통합) + `routes_v1.py` MODIFY (historical/orderbook 2 endpoint 추가) | INV-5 회귀 0 (data full suite 1152+ test 무영향) |
| engine `pyproject.toml` | (mctrader-data @ git+ 의존 잔존) | + `httpx>=0.27` 신규 의존 추가 (mctrader-data 의존 line 유지 — MCT-188 D7 final 제거 owner) | INV-5 회귀 0 |

**부작용 변경 없음**: cutover = wrap-only (REST/Redis Stream 경유) + 데이터 변형 0 (Arrow
IPC byte-equivalence + idempotent sha256 정합). engine production behavior 회귀 0 (INV-2
byte-equivalence). data api/ 6 파일 + io/ + storage 자체 변경 0 (api/ realtime_stream.py
+ routes_v1.py 만 신설/MODIFY).

## 5. pyproject 의존 추가 (Refactor + TestContractArch INV-5)

```toml
# mctrader-engine/pyproject.toml dependencies 추가:
"httpx>=0.27",
# (mctrader-data @ git+ 의존 line 잔존 — MCT-188 D7 final 제거 owner)

# mctrader-data/pyproject.toml = 신규 의존 0 (redis[hiredis]>=5 + fastapi/uvicorn = MCT-184 LAND 기존)
```

- **INV-5 회귀 0 (TestContractArch)**: httpx = engine 신규 의존 추가만 (기존 backtest/wfo/executor/cli/paper_runner
  /runtime 로직 무변경). data realtime_stream.py 신규 추가 = 기존 api/io/storage/compactor
  무영향. engine full suite (test_io/ 107 test + backtest/WFO suite) 회귀 0 + data full
  suite (1152+ test) 회귀 0 검증 의무 (의존 추가 ≠ import 경로 변경).

## 6. 마이그레이션 / 배포 (DataMigrationArch §11 — 데이터 마이그레이션 N/A — cutover wrap-only)

본 Story = **cutover (wrap-only) + 신설 (realtime_stream + data_client + historical/orderbook
endpoint)** → §11 참조. 데이터 변형 0 (persisted-data 무변경, Arrow IPC byte-equivalence
+ idempotent sha256 정합).

## 7. 보안 설계 (SecurityArch primary 강함 — §7.1-§7.7)

> **SecurityArch deputy perspective (위협/보안 변호자)** — 신규 trust boundary 영역 =
> engine `data_client/` HTTP client (internal-only network → data api `:8000`) + data
> `realtime_stream.py` Redis Stream publisher (loopback only). 외부 노출 0 + Pydantic
> strict input validation 재사용 (MCT-184 routes_v1.py LAND 패턴) + sha256 idempotent
> 재사용 (MCT-184 INV-3 + post-merge fix `e612296` F-2 정합).

### 7.1 Trust boundary

- **engine ↔ data**: internal-only compose network only (`http://data-api:8000`, ADR-030
  single-host loopback 정합). engine pyproject `httpx>=0.27` HTTP client = internal call
  only (외부 인터넷 노출 0).
- **engine ↔ Redis Stream** (MCT-186 owner): 본 Story = data publisher only. engine
  consumer = MCT-186 — 본 Story trust boundary 외 (cross-ref only).
- **data ↔ Redis Stream**: data 내부 publisher → loopback Redis (compose internal network).
  외부 publisher 0 (single-source publisher, data 단독 책임).
- attack surface delta = 0 추가 (engine 측 신규 HTTP client + data 측 신규 Redis publisher
  모두 internal-only 격리).

### 7.2 Threat model (위협↔완화 매핑)

| # | 위협 | 완화 |
|---|------|------|
| T1 | engine→data REST path traversal (engine data_client query param) | client-side allowlist regex (`exchange ^[a-z0-9_-]+$` / `symbol ^[A-Z0-9_/-]+$` / `date ^\d{4}-\d{2}-\d{2}$` / `partition_path ../` reject) — MCT-184 routes_v1.py 패턴 정합 (server-side Pydantic + client-side defense in depth) |
| T2 | engine→data REST payload DoS (reverse-write 대용량) | client-side `max_length` enforcement (paper-candles `len(candles) <= 1000` + backtest-artifact `<= 100MB` — MCT-184 LAND bound 정합) |
| T3 | data Redis Stream payload DoS | MAXLEN `~ 100000` (approximate trim, 메모리 bound ~10MB per stream key) + payload schema Pydantic strict (TickRowV1_1 model_validate) |
| T4 | idempotency 우회 (engine 재호출 시 중복 write) | client-side canonical sha256 hash key (paper-candles `canonical_jsonl_hash` market-core SSOT 재사용 + MCT-184 INV-3 정합 + post-merge fix `e612296` F-2 정합) — 동일 hash 재POST = idempotent_skip |
| T5 | Redis Stream replay attack (악의적 consumer 가 stream 변조) | Redis ACL (compose internal network 격리 — external Redis access 0) + payload Pydantic strict validation (consumer 측 = MCT-186 owner) |
| T6 | NAS 정보 노출 (engine 측 NAS 알면 안 됨 — D2/ADR-029 정합) | REST 응답 = Arrow IPC stream only (NAS key/parquet tier/ETag/endpoint resolution 비노출 — MCT-184 LAND 패턴 정합). 본 Story historical/orderbook endpoint 신설 도 동일 (Arrow IPC only) |
| T7 | TLS 0 (compose internal HTTP plain) | internal-only network 격리 (외부 노출 0) → TLS 미도입 정당. MCT-186 cutover 시 internal mTLS 검토 = carry-over |

### 7.3 Auth / authz

- engine ↔ data internal auth: 본 Story = internal-only network 격리 → **인증 토큰 미도입**
  (MCT-184 LAND 정합). MCT-186 cutover 시 internal service auth (shared secret header / mTLS)
  검토 = **carry-over** (MCT-186 owner).
- reverse-write authz: paper/backtest namespace 한정 write + idempotent hash key (MCT-184
  LAND 패턴 정합).
- Redis Stream authz: data 단독 publisher (single-source). consumer ACL = MCT-186 owner.
- **잔여 risk accept 근거**: internal-only network 격리 (외부 노출 0) + production wiring
  활성화 시점에도 internal auth carry (MCT-186 owner) → 본 Story scope auth 생략 정당.
  PMO-AUDIT-MCT-184 §6.2 reapply 의무 = MCT-186 진입 시 auth 강화 carry track.

### 7.4 DR / disconnect / rate-limit / env-isolation (OperationalRiskArch primary 강함 CONDITIONAL §8.5 active=true)

> **OperationalRiskArch deputy perspective (운영 리스크/production-readiness 변호자)** —
> §8.5 active = **true** (ArchitectPL 결정, CFP-378 AC-5. 4 조건 평가: long-running
> connection Y + stateful cache Y + background worker Y + restart-aware Y → 4/4 Y).
> **production wiring 전환 = engine 11곳 production caller 활성화** = MCT-184 dead-in-data
> 대비 운영 리스크 영역 큼.

| 운영 리스크 | 설계 결정 | CONDITIONAL N/A 사유 |
|-------------|-----------|---------------------|
| DR (data api down → engine cold-read failure) | engine `data_client.base.HttpClient` 측 retry (exponential backoff 3 회, 429/503/504 retryable) + circuit-breaker (window 60s 내 5xx 5회 OR p99 >5s 3회 = OPEN, 30s 후 HALF_OPEN — MCT-170 dr_mode 패턴 답습) + **local-fallback 없음** (engine 측 NAS 직독 폐기 cutover = ADR-029 §D2 VERIFIED 정합 — fallback 도입 시 D2 invariant 위반). data api down 시 = engine cold-read 503 propagate (graceful + alert) | — (설계 확정) |
| DR (Redis Stream down → data publisher failure) | data `realtime_stream.RealtimeStreamPublisher` 측 retry (`redis.exceptions.ConnectionError` exponential backoff 5 회) + local-only mode 전이 (in-memory queue 100 entry bound + DROP-OLDEST eviction) + Prometheus alert (`mctrader_data_redis_stream_publish_failures_total` Counter). consumer 측 = MCT-186 owner (subscriber DR = 별 설계) | — (설계 확정 — Redis Stream 자체 down = consumer 영향 0, publisher 측 graceful) |
| disconnect (in-flight Arrow IPC streaming) | MCT-184 LAND uvicorn `--timeout-graceful-shutdown=60` 재사용 (in-flight stream 완료 후 종료). 본 Story 신규 historical/orderbook endpoint 동일 패턴 (StreamingResponse) | — (MCT-184 패턴 재사용) |
| rate-limit | internal-only network → 외부 abuse 표면 0. engine client 호출 패턴 = (a) cold-read = backtest/WFO 시작 시점 burst (수십 회/min) (b) reverse-write = paper run 종료 시점 single call (run 당 1회). **본 Story rate-limit 미도입** (internal-only + low-freq batch). MCT-186 cutover 후 burst 증가 시 rate-limit 도입 carry | internal-only 격리 + low-freq batch → rate-limit N/A 정당 (외부 0) |
| env-isolation (dev/prod) | ADR-030 §D3 `--profile dev/prod` + `.env.dev`/`.env.prod` 정합. `DATA_API_BASE_URL` env (dev = `http://data-api:8000` / prod = compose internal hostname). 실 compose wiring = MCT-186 (engine NAS cred drop) | — (설계 확정, 실 compose = MCT-186) |
| restart policy | data api `restart: unless-stopped` (MCT-184 LAND 정합 ADR-030 §D2 paper-engine pattern). engine `data_client` = stateless HTTP client (httpx.Client lifecycle = process bound, restart 시 graceful close + reconnect). **realtime_stream publisher = ASGI lifespan startup/shutdown 통합** (`RealtimeStreamPublisher.startup()` Redis connection pool 생성 / `.shutdown()` in-flight XADD drain + connection close) | — (설계 확정 — restart-safe by design) |
| clock sync | Redis Stream entry ID = Redis server 측 timestamp (ms precision) — server-side single source (publisher 측 timestamp 의존성 0). consumer 측 = entry ID 순서 신뢰 (Redis Stream FIFO 보증). engine httpx Client = request timestamp 비의존 (REST stateless). **clock sync N/A** (Redis server-side timestamp + REST stateless) | clock sync N/A (Redis server-side timestamp single source + REST stateless) |
| §8.5 stateful/restart invariant | engine `data_client.base` circuit-breaker state = in-memory (restart 시 휘발 — CLOSED 초기값으로 시작, NAS re-probe 정합). data realtime_stream publisher in-memory queue = restart 시 휘발 (DROP-OLDEST eviction 의도 = 동일 동작) — both restart-safe (in-memory state 휘발 정합) | — (설계 확정 — TestContractArch §8 검증) |
| §8.5 background worker | data realtime_stream publisher = ASGI background task (asyncio loop + Redis connection pool, lifespan hook 관리). engine data_client = sync HTTP call (background worker 없음). publisher 측 restart-aware = ASGI lifespan 정합 | — (publisher only background, restart-safe) |

### 7.5 민감 데이터 분류

- engine→data REST payload = (a) historical query = exchange/symbol/date (민감도 LOW —
  market data identifier) (b) reverse-write payload = paper-candles (OHLCV — 민감도 LOW)
  + backtest-artifact (전략 결과 — 민감도 MEDIUM)
- Redis Stream payload = TickRowV1_1 (정규화 tick — 민감도 LOW, market data 파생)
- NAS credential = data api 내부 (io/ reader 가 NAS 접근) — REST 표면 + Redis Stream 표면
  비노출 (T6). engine NAS cred = 본 Story 무관 (engine `data_client/` 가 NAS 직접 접근
  안 함 — MCT-186 owner engine NAS cred drop)
- secret mount: data realtime_stream publisher = data api service 동일 image (Redis
  connection env 재사용, 실 compose = MCT-186). 본 Story = 코드 신설만 (secret 신규 0)

### 7.6 위협↔완화 매핑 종합

§7.2 T1-T7 = 신규 attack surface delta 전수 완화 매핑. 잔여 = internal auth + rate-limit
+ TLS (MCT-186 carry — internal-only 격리 + low-freq batch 로 본 Story accept).

### 7.7 보안 설계 종합 verdict

- **attack surface delta = 0 추가** → 신규 HTTP client + Redis Stream publisher 모두
  internal-only 격리 + MCT-184 routes_v1.py 패턴 (Pydantic strict + namespace 한정 + size
  bound) 재사용 + canonical sha256 idempotent client-side 재사용.
- **잔여 risk (accept)**: internal auth + rate-limit + TLS 미도입 (MCT-186 carry) — 3
  항목 MCT-186 cutover 시 production wiring 동반 강화.
- **SecurityArch verdict**: 신규 HTTP client + Redis Stream publisher = internal-only +
  strict input validation + namespace 한정 + idempotent sha256 로 본 Story scope 위협
  전수 완화. T6 (NAS 정보 노출) = Arrow IPC stream only 박제 (MCT-184 LAND 패턴 정합 +
  본 Story historical/orderbook endpoint 신설 동일 패턴). **설계 lane 진입 가능** (잔여
  = MCT-186 carry, accept).

## 8. Test Contract (TestContractArch — §8.0 Phase 0 Gate + Perf Baseline 필수 + AC-6 wiring evidence triad)

> **TestContractArch deputy perspective (QA perspective contributor)** — §8 커버리지 +
> 경계 + invariant + Perf Baseline 타당성. **§8.5 active = true** (ArchitectPL 결정 verbatim).

### 8.0 Phase 0 Gate (코드 작업 data#N + engine#N 착수 전 의무 — MCT-170/183/184 lesson reapply)

```bash
# V1: data/engine/hub git fetch origin (working tree stale ≠ origin HEAD 차단)
cd mctrader-engine && git fetch origin && git log -1 --oneline origin/main
#   기대: 18275737 (MCT-183 io removal LAND) — 불일치 시 ArchitectPL escalate
cd mctrader-data && git fetch origin && git log -1 --oneline origin/main
#   기대: a1a8ccf (MCT-189 Phase 2 PR2 LAND, MCT-184 fix e612296 포함)
cd mctrader-hub && git fetch origin && git log -1 --oneline origin/main
#   기대: 330c124 (MCT-189 PMOAgent 박제) 또는 그 이후

# V2: engine cold-read 8곳 4파일 재grep (HEAD 재대조)
cd mctrader-engine && git grep -nE "from mctrader_data\.(storage|path|orderbook_replay)" -- 'src/**/*.py'
#   기대: 8곳 4파일 정확 (cli.py:279,280 + executor/tick_replay.py:26,559 + wfo/evaluator/data_loader.py:43,44 + wfo/search/data_loader.py:81,82)

# V3: engine 전체 `from mctrader_data|import mctrader_data` grep (Phase 0 lazy import 의무)
git grep -nE "from mctrader_data|import mctrader_data" -- 'src/**/*.py'
#   기대: 14곳 7파일 (cold-read 8 + 부수 6 — paper_runner/nas_sync/tick_replay shim/state_machine/tick_scalping)
#   본 Story cutover scope = 11곳 5파일 (cold-read 8 + reverse-write 3 + paper_lineage 1) — paper_runner.py:290 paper_lineage 본 Story 포함 결정 (§3.5)

# V4: data api/realtime_stream.py 부재 + redis 가용 재grep
cd mctrader-data && test ! -f src/mctrader_data/api/realtime_stream.py && echo "ABSENT ✓"
grep -nE "redis|hiredis" pyproject.toml
#   기대: ABSENT + redis[hiredis]>=5 줄 매치

# V5: engine data_client/ 부재 + httpx 의존 검증
cd mctrader-engine && test ! -d src/mctrader_engine/data_client && echo "ABSENT ✓"
grep -nE "httpx|requests" pyproject.toml
#   기대: ABSENT + httpx 매치 0 (신규 의존 추가 예정)

# V6: MCT-184 routes_v1.py LAND surface 재확인 (historical/orderbook endpoint 부재 검증)
cd mctrader-data && grep -nE "^@(router|app)\.(get|post)" src/mctrader_data/api/routes_v1.py
#   기대: 5 line match (candles + candles/l1 + reverse-write × 2 + /health)
#   본 Story = historical/orderbook 2 endpoint 신설 의무 (§3.3)

# 불일치 시 = 가설↔실상 괴리 → ArchitectPL escalate (코드 작업 중단)
```

### 8.1 Test 커버리지 후보 (TestContractArch — chief author 통합)

| # | test | 경계/invariant | 검증 |
|---|------|---------------|------|
| TC-1 | data `realtime_stream.RealtimeStreamPublisher` import + Redis connection pool startup + tick.v1.1 정규화 schema 정합 (TickRowV1_1 market-core SSOT 소비) | AC-1 / INV-3 | `from mctrader_data.api.realtime_stream import RealtimeStreamPublisher` import 성공 + `RealtimeStreamPublisher.startup()` Redis ping 200 + payload `TickRowV1_1.model_dump_json()` 직렬화 정합 |
| TC-2 | Redis Stream XADD `market:tick:{exchange}:{symbol}` key naming 정합 + MAXLEN ~ 100000 trim 동작 | AC-1 / ADR-030 §D15 | `XADD market:tick:bithumb:BTC_KRW MAXLEN '~' 100000 * <fields>` 호출 정상 + `XLEN` 호출 후 ≈ 100000 (approximate trim 검증). `REDIS_KEY_PREFIX_MARKET` env override 동작 (default `market`) |
| TC-3 | engine `data_client.HistoricalClient.fetch_candles` REST → Arrow IPC stream deserialize → CandleModel byte-equivalence (cutover 전/후 동등) | AC-2 / AC-4 / INV-2 | engine cutover 전 `scan_candles(...)` 결과 == REST 경유 `client.fetch_candles(...)` 결과 byte-equivalence (MCT-184 INV-2 Arrow IPC byte-level 정합) |
| TC-4 | engine `data_client.HistoricalClient.fetch_orderbook_snapshots` + `.fetch_orderbook_ticks` REST cutover (executor/tick_replay.py:26,559 scope) | AC-2 / AC-3 / AC-4 | historical/orderbook 신규 endpoint (§3.3) cutover 검증 — Arrow IPC stream → OrderbookEventRecord/TickRecord deserialize 정합 + `compute_partition_dir(...)` client-side path 산출 정확성 (data import 없이 partition dir 식별) |
| TC-5 | engine `data_client.ReverseWriteClient.post_paper_candles` idempotent sha256 client-side 정합 (canonical_jsonl_hash market-core SSOT 재사용) | AC-3 / INV-3 | 동일 sha256 hash payload 재POST → idempotent_skip=true + 중복 write 0 + 동일 200 (MCT-184 post-merge fix `e612296` F-2 정합) |
| TC-6 | engine `data_client.ReverseWriteClient.post_backtest_artifact` `.done` sentinel idempotent | AC-3 / INV-3 | 동일 run_id `.done` sentinel 존재 시 재POST → idempotent_skip=true (MCT-184 LAND 정합) |
| TC-7 | engine cold-read 8곳 grep0 + reverse-write 3곳 grep0 (AC-3 grep0 strict) | AC-3 / INV-1 | engine src/ `from mctrader_data.(storage|path|orderbook_replay)` import == 0 + `from mctrader_data.paper_storage import write_paper_candles` == 0 + `from mctrader_data.nas_storage.nas_uploader import` == 0 (cutover 완결 grep0) |
| TC-8 | MCT-182 shim 잔존 4곳 (paper_lineage 본 Story 포함 후) 명시 — 본 Story 비대상 SSOT 박제 | AC-3 (negative — MCT-188 owner 분리 SSOT) | engine src/ `from mctrader_data.tick_storage|from mctrader_data.orderbook_storage|from mctrader_data.aggregation` grep — 4곳 잔존 = MCT-188 owner 명시 (`executor/tick_replay.py:31,32` + `hot/state_machine.py:33` + `strategy/templates/tick_scalping.py:76`) |
| TC-9 | cutover byte-equivalence — engine backtest/WFO scenario cutover 전/후 출력 동일 | INV-2 / AC-4 | TestContractArch baseline scenario (cli.py + wfo/evaluator + wfo/search + executor/tick_replay + paper_runner) cutover 전 baseline 박제 → cutover 후 동일 input 동일 output byte-equivalence 검증 (Arrow IPC byte-level + Decimal 정밀도 + TickRecord/OrderbookEventRecord/CandleModel 정합) |
| TC-10 | engine `data_client.base` retry/circuit-breaker (5xx 5회 → OPEN, 30s → HALF_OPEN) | §7.4 DR / AC-2 | mock httpx 5xx response 5회 → circuit-breaker OPEN 검증 + 30s sleep 후 HALF_OPEN probe 1회 success → CLOSED 전이 (MCT-170 dr_mode 패턴 답습) |
| TC-11 | data `realtime_stream` publisher DR (Redis disconnect → retry + local-only queue + Prometheus emit) | §7.4 DR / AC-1 | mock Redis disconnect → exponential backoff 5회 retry + local-only mode 전이 + in-memory queue 100 entry bound + DROP-OLDEST eviction + `mctrader_data_redis_stream_publish_failures_total` Counter 증가 |
| TC-12 | AC-6 wiring evidence triad — engine `from mctrader_engine.data_client` import grep ≥11곳 + integration testcontainers (engine→data REST round-trip smoke PASS) + file:line evidence | AC-6 / INV-6 | engine src/ `from mctrader_engine.data_client` import grep ≥11 (cold-read 8 + reverse-write 3 cutover scope 전수) + testcontainers (data api LAND + engine cutover 실 production wiring 검증 PASS) + file:line evidence 박제 (cold-read 8 + reverse-write 3 cutover 카운터) |
| TC-13 | data full suite 1152+ test + engine full suite (test_io/ 107 + backtest/WFO suite) 회귀 0 | INV-5 | data#N 후 data full suite + engine#N 후 engine full suite 신규 실패 0 (httpx + realtime_stream 신규 의존이 기존 로직 무변경) |
| TC-14 | §3.6.1 gate v2 self-verify TEST1/TEST2 + repo-wide grep 0줄 + §3.6.2 박제 PR 5 체크리스트 self-verify + §3.6.3 Codex post-LAND audit 4 axis | INV-4 + §3.6.2 + §3.6.3 | gate v2 pattern 1/2/3 포착력(TEST1) + false positive 0(TEST2) + post-LAND repo-wide grep 0줄 evidence + 박제 PR 5 체크 전수 PASS + post-LAND audit 4 axis 운용 evidence |

### 8.2 Perf Baseline (필수 — cutover 추가 latency 측정 production 영향 detection)

> 본 Story = cutover (wrap-only, REST + Redis Stream 경유) → **REST wrap overhead 측정
> + Redis Stream publish latency 측정 의무** (production 영향 detection — MCT-184 Perf
> Baseline 1000-row serialize p50 < 5ms 정합 + 본 Story cutover 추가 latency).

| 측정 | baseline 박제 | gate |
|------|---------------|------|
| engine cold-read REST wrap overhead (`scan_candles` 직접 호출 → REST 경유 latency 차이) | MCT-184 LAND historical Arrow IPC latency baseline (1000-row serialize p50 < 5ms) 대비 engine 측 deserialize 추가 overhead 측정 | baseline 박제 (production deploy 후 회귀 비교 reference. p99 < 100ms gate — MCT-170 D7=A reader cache hit 95% + p99 <100ms 정합) |
| engine reverse-write REST wrap overhead (paper-candles + backtest-artifact direct call vs REST 경유) | MCT-184 LAND idempotent skip latency 정합 | baseline 박제 (재POST 시 idempotent_skip < 50ms 확인) |
| data Redis Stream XADD publish latency (p50 + p99) | 신규 측정 (Milestone-2 tick.v1.1 pattern 정합) | baseline 박제 (p99 < 10ms gate — Redis loopback local latency) |
| data realtime_stream publisher throughput (ticks/sec per stream key) | 신규 측정 | baseline 박제 (50 sym × 3 channel × 100 tick/s = 15000 tick/s upper budget — MCT-103 50-symbol universe 정합) |
| engine `data_client` circuit-breaker overhead (CLOSED state 정상 호출 latency 추가) | 신규 측정 | baseline 박제 (CLOSED state overhead < 1ms gate — in-memory state check only) |

Perf Baseline = 박제 (본 Story = production wiring 활성화 → 회귀 gate 적용 = 본 Story
post-LAND 14d window. MCT-184 Perf Baseline 박제 패턴 정합).

## 9. 위험 / 롤백 / land_order

### 9.1 land_order (scope_manifest 1:1 — 3 repo 가장 복잡 cross-repo 순서)

```
hub Phase1 (docs — Story §0-§11 + ADR-029 §D2 VERIFIED amendment box + ADR-031 §D2/§D3
  VERIFIED amendment box + ADR-030 cross-ref + .codeforge/contracts/data-api-v1.openapi.json
  pre-update (data#N 예상 emit) + scope_manifest + CLAUDE.md)
  → data#N (land_order 1 — src/mctrader_data/api/realtime_stream.py 신설 +
     routes_v1.py historical/orderbook 2 endpoint 추가 + OpenAPI emit 갱신 +
     api/deps.py + api/app.py lifespan 통합. pyproject 변경 0)
  → engine#N (land_order 2 — src/mctrader_engine/data_client/ 신설 (base/historical/
     reverse_write/exceptions/__init__) + cold-read 8곳 cutover + reverse-write 3곳
     cutover + paper_runner.py:290 paper_lineage market-core 직독 변경 + pyproject
     httpx>=0.27 추가 + AC-6 wiring evidence triad 박제 (caller grep ≥11 + integration
     testcontainers + file:line evidence))
  → hub Phase2 PR2 (박제 — Story §9/§10/§11 + ADR-029 §D2 + ADR-031 §D2/§D3 VERIFIED
     amendment box LAND confirm + .codeforge/contracts/data-api-v1.openapi.json 실 emit
     대조 reconcile + scope_manifest milestone 4/7 + CLAUDE.md COMPLETED + RETRO + §Story-4
     EPIC-RESULTS + 박제 PR 5 체크리스트 self-discipline (§3.6.2) + Codex post-LAND audit
     4 axis self-discipline (§3.6.3))
```

각 PR CI green 후 admin merge → 다음 PR. **engine 참여 (3 repo) = MCT-184 (2 repo) 대비
가장 복잡 cross-repo 순서**. data#N 의 realtime_stream.py + historical/orderbook endpoint
신설 = engine#N data_client/ 신설 prerequisite (OpenAPI SSOT 단방향 강제). hub Phase1
snapshot = data#N **예상** emit 박제 → data#N LAND 후 Phase2 PR2 실 emit 대조 reconcile
(`cross-repo-contract-lock-check.sh` MCT-184 LAND script 재사용).

### 9.2 위험

| risk | severity | 완화 |
|------|----------|------|
| R1 cross-repo Phase0 desync 7회째 (3 repo 가장 복잡) | HIGH | §8.0 Phase 0 Gate (V1-V6 HEAD 재대조) + D-row 13/13 reconcile (§3.6) + §3.6.1 gate v2 cross-Story reapply (glob-scope + 변형포괄 + self-verify TEST1/TEST2). 3 repo = data 신설 → engine cutover 후행 sequential lock-step (MCT-184 = 2 repo 대비 cross-repo desync risk 1.5x) |
| R2 MCT-41 Live Mode Debut cross-cutting | MEDIUM-HIGH (Phase 0 활성 진행 0 — baseline confirm) | Phase 0 V8 추가 cross-check (`git branch -a MCT-43~47` + `git log MCT-43~47 commit`) = engine repo 활성 진행 **0건 발견** (Phase 0 evidence baseline). 본 Story 11곳 5파일 중 `runtime/paper_runner.py` + `executor/tick_replay.py` = live mode WS/주문 경로 공유 모듈 위험 가설 유효 but 활성 MCT-43~47 진행 0 → engine#N 진입 직전 재cross-check 의무 (Orchestrator ordering 결정). 발견 시 (a) MCT-185 engine#N land_order 재조정 or (b) 공유 모듈 부분만 별 sub-Story 분리 |
| MCT-184 dead-in-data → production wiring 전환 wiring drift 동형 | LOW (MCT-189 cleanup LAND baseline + AC-6 evidence triad 선제 reapply) | MCT-189 Phase 2 PR2 LAND (`a1a8ccf` 130GB legacy cleanup) = baseline drift 0. MCT-184 AC-6 의도된 dead-in-data SSOT → 본 Story AC-6 의도된 production wiring SSOT 박제 (evidence triad 갱신 — file:line + caller grep ≥11 + integration test PASS). ADR-032 evidence triad 선제 reapply 효력 1회 실증 시점 |
| cross-document SSOT desync 7회 누적 가능 | MEDIUM | §3.6.1 gate v2 (glob-scope + 변형포괄 + self-verify) — MCT-184 패턴 SSOT 차용. 1차 FIX 시 전 산출물 동반 reconcile 의무. 박제 PR 5 체크리스트 inline 박제 (§3.6.2 self-discipline carrier 2번째 — 1회 실증 효력 검증) |
| httpx 의존 도입 회귀 | LOW | INV-5 (engine full suite + data full suite 무영향 — pyproject 의존 추가 ≠ 기존 로직 변경). httpx 신규 의존이 engine backtest/WFO/cli/executor/runtime 무변경 정합 |
| historical/orderbook endpoint 신설 = MCT-184 amendment 분리 vs 본 Story 포함 trade-off | LOW (본 Story 포함 채택) | §3.3 본 Story 포함 채택 (MCT-184 amendment 분리 시 lock-step 의존 증가 차단). OpenAPI snapshot 갱신 + `cross-repo-contract-lock-check.sh` MCT-184 LAND script 재사용 |
| Redis Stream payload schema drift (tick.v1.1 정규화 schema vs distributor side change) | LOW | TickRowV1_1 SSOT = market-core Layer 0 (`mctrader_market.schemas.tick:62`, MCT-182 LAND). data realtime_stream publisher = SSOT 재사용 (재구현 0) + consumer 측 = MCT-186 owner 동일 SSOT 소비 정합 (INV-3 정합) |
| cutover Story 특수성 — silent data corruption + INV-3 mismatch + bytes-level 정밀도 영역 sentinel sentry 의무 강화 | MEDIUM | §3.6.3 Codex post-LAND audit 4 axis self-discipline (production correctness + bytes-level 정밀도 + SSOT 재검증 + security). MCT-184 F-1/F-2/F-4 동형 4건 재발 사전 차단 priority. cutover lane sentinel sentry = 1 axis (production correctness) sentinel sentry 강화 |

### 9.3 롤백 (역순 backout 보존)

land_order 역순 backout: hub Phase2 PR2 revert → engine#N revert (data_client/ 삭제 +
cold-read 8곳 + reverse-write 3곳 import 복원 + pyproject httpx 제거) → data#N revert
(realtime_stream.py 삭제 + routes_v1.py historical/orderbook endpoint 제거 + OpenAPI emit
복원) → hub Phase1 revert. engine cutover = wrap-only (import path 변경만, 로직 변경 0) →
revert 시 import 복원 = engine production behavior 회귀 (cutover 전 동작) 자연 복원. data
신설 = api/realtime_stream.py + routes_v1.py 2 endpoint 추가 (api/ 기존 4 endpoint 무변경)
→ revert 시 신규 신설만 삭제, 기존 caller 0건 (consumer = MCT-185 본 Story = 본 Story
revert 자체 = caller 0 보존). 안전 backout.

**cutover Story 특수 backout 검증**: engine production wiring 전환 revert 시 = engine
production caller `from mctrader_data.(storage|path|orderbook_replay)` import 복원 + httpx
제거 = engine production behavior cutover 전과 동등 (byte-equivalence INV-2 보장). data
신설 revert 시 = realtime_stream.py + historical/orderbook endpoint 삭제 만 (api/ 기존 5
endpoint 무변경) — backward compat preserve.

## 10. ADR 판단

- **ADR-029 §D2 VERIFIED amendment box (MCT-185 LAND 박제)**: engine NAS 직독 폐기 LAND
  confirm + cold-read 8곳 = data REST indirection 실 적용 박제 + io reader 6 module =
  mctrader-data Layer 2 (MCT-183 LAND 정합) + presigned-NAS-handoff 기각 효력 실증 (REST
  응답 = Arrow IPC stream only, NAS object layout 비노출). ADR-029 **본문 11 D 정책 무변경**
  (POLICY_FINALIZED 보존 — MCT-181 LAND Status Amendment box 패턴 정합).
- **ADR-031 §D2 VERIFIED amendment box (MCT-185 LAND 박제)**: cold-read cutover 완결 —
  engine src/ `from mctrader_data.(storage|path|orderbook_replay)` 0건 grep + cold-read 8곳
  cutover 박제. Status `Accepted` 유지 (POLICY_FINALIZED 전이 = MCT-188).
- **ADR-031 §D3 VERIFIED amendment box (MCT-185 LAND 박제)**: realtime stream + reverse-write
  wiring 완결 — realtime_stream.py LAND + engine data_client/ LAND + reverse-write 3곳
  cutover + paper_lineage market-core 직독 변경 + historical/orderbook endpoint 신설 박제.
  Status `Accepted` 유지.
- **ADR-030 cross-ref only**: Redis Stream loopback 정합 재명시 (data 기존 redis 의존 재사용
  + 신규 service 추가 0 — 실 compose wiring + engine NAS cred drop = MCT-186 owner). 본문
  19 D 무변경 (POLICY_FINALIZED 보존).
- **ADR-032 선제 reapply 효력 실증 시점**: MCT-184 AC-6 의도된 dead-in-data SSOT → 본
  Story AC-6 의도된 production wiring SSOT 박제 = ADR-032 evidence triad (file:line +
  caller grep ≥11 + integration test result) 선제 reapply 효력 **1회 실증**. PMO-AUDIT-MCT-184
  §3 패턴 #3 — relocation/신규 신설 Story 안전 invariant 화 권고의 MCT-185 실 검증 시점.
- **ADR 신규 불요**: 본 Story = ADR-031 §D2 + §D3 의 owner Story 절반 + ADR-029 §D2
  VERIFIED amendment confirm. 신규 ADR 발의 0 (ADR-031 §D2/§D3 가 결정 record SSOT +
  ADR-029 §D2 가 NAS SoT SSOT).
- 신규 ADR 후보 (PMO retro 입력): cross-document SSOT mechanical gate (plugin-codeforge#795
  OPEN — §3.6.1 gate v2 self-discipline 7회 누적 가능) + 박제 PR 5 체크리스트 mechanical
  gate (plugin-codeforge#804 OPEN — §3.6.2 self-discipline carrier 2번째) + post-LAND
  audit lane (plugin-codeforge#805 OPEN — §3.6.3 self-discipline 첫 실증).

## 11. 데이터 마이그레이션 (DataMigrationArch — cutover wrap-only N/A 명시 + §11.6 idempotency 강화)

> **DataMigrationArch deputy perspective (데이터 무결성 변호자)** — cutover (wrap-only)
> = persisted-data 무변경. 신설 (realtime_stream + data_client + historical/orderbook
> endpoint) = read-only wrap + Redis Stream append-only.

### 11.1-11.5 Schema / Migration / Rollback — **N/A (명시)**

본 Story = **cutover (wrap-only) + 신설 (read-only/append-only wrap)** → 데이터 마이그레이션
**N/A**:

- engine cold-read cutover = `scan_candles`/`orderbook_replay` 직접 호출 → `data_client.historical`
  REST 경유 (Arrow IPC byte-equivalence INV-2 — persisted Parquet/NAS object 무변경).
  schema/migration/rollback 무관.
- engine reverse-write cutover = `write_paper_candles`/`NASUploader` 직접 호출 → `data_client.reverse_write`
  REST 경유 (MCT-184 LAND routes_v1.py wrap — ADR-009 v1 16-col schema 보존). 신규 schema
  도입 0.
- data realtime_stream.py 신설 = Redis Stream `XADD market:tick:{...}` publish (in-memory
  + Redis 저장만, persisted-data 무변경). tick.v1.1 정규화 schema = market-core Layer 0
  SSOT 재사용 (재구현 0).
- historical/orderbook endpoint 신설 = `orderbook_replay.scan_orderbook_events` + `scan_ticks`
  read-only wrap (persisted Parquet 무변경).
- pyproject httpx 의존 추가 ≠ 데이터 변경 (INV-5).

### 11.6 Idempotency (DataMigrationArch primary + OperationalRiskArch consult — MCT-184 F-2 lesson reapply 강화)

> **CONDITIONAL idempotency — DataMigrationArch primary + OperationalRiskArch consult
> (N줄 memo input)**. MCT-184 post-merge fix `e612296` F-2 (canonical_sha256 mismatch
> + INV-3 정밀도) lesson reapply = **client-side sha256 정밀도 의무 강화**.

- **engine reverse-write client-side idempotent (INV-3 정합)**: `data_client.reverse_write.post_paper_candles`
  = client-side `canonical_jsonl_hash(candles + lineage)` 산출 (market-core SSOT 재사용
  — `from mctrader_market.paper_lineage import canonical_jsonl_hash` MCT-182 LAND 정합)
  → server (MCT-184 routes_v1.py LAND) 동일 hash 산출 → match 확인 (server-side INV-3
  정합). 동일 hash 재POST → server idempotent_skip=true (중복 write 0).
- **MCT-184 F-2 lesson reapply (bytes-level 정밀도)**: post-merge fix `e612296` F-2 =
  canonical_sha256 산출 시 candles + lineage byte-level 정밀도 보장 (Decimal str 정밀도
  + UTCDateTime isoformat 정합). 본 Story client-side = 동일 alphabet/whitespace/sort key
  정합 (`sort_keys=True, separators=(",", ":")` JSON canonical pattern 보장). client-server
  hash mismatch = INV-3 violation P0 차단 (TC-5 검증).
- **engine reverse-write backtest-artifact `.done` sentinel idempotent (INV-3)**:
  `data_client.reverse_write.post_backtest_artifact` = server (MCT-184 LAND) `.done`
  sentinel 검사 → 존재 시 idempotent_skip=true (ADR-030 §D19 MCT-181 LAND nas_sync 패턴
  정합).
- **engine cold-read client read idempotency**: inherently idempotent (REST GET = read-only,
  multiple call → 동일 결과). REST response cache (engine client-side optional, 본 Story
  scope 외 — MCT-186 owner 검토 carry).
- **data Redis Stream publish idempotency**: Redis Stream XADD = single-source publisher
  (data 단독, single-source). MAXLEN `~` trim = approximate (entry duplicate 시 consumer
  측 entry ID 신뢰 — server-side timestamp single source). publisher 재호출 시 = 새 entry
  ID 발급 (duplicate entry 가능, consumer 측 deduplication 의무 = MCT-186 owner).
- **OperationalRiskArch consult (N줄 memo)**: ASGI restart 시 in-memory idempotency state
  휘발 없음 (idempotency = server-side sidecar/`.done` sentinel = persisted, in-memory
  state 비의존 → restart-safe). engine `data_client` retry 시 sha256 hash key 동일 →
  server idempotent_skip 정합 (retry-safe). cutover lane sentinel sentry 강화 = MCT-184
  F-2 동형 재발 사전 차단 priority (§3.6.3 axis 2).

### 11.7 데이터 무결성 종합 verdict

cutover (wrap-only) + 신설 = persisted-data 무변경 (read-only wrap + append-only paper/backtest
namespace + Redis Stream in-memory + Redis 저장 only). idempotency = persisted sidecar/sentinel
+ client-side canonical sha256 (MCT-184 INV-3 + post-merge fix `e612296` F-2 정합 +
market-core SSOT 재사용). market data SoT XOR invariant 무충돌 (ADR-029). Arrow IPC
byte-equivalence (INV-2) — engine production behavior cutover 전/후 동등. **DataMigrationArch
verdict: 데이터 무결성 risk LOW — 설계 lane 진입 가능** (N/A 명시 + §11.6 idempotency
강화 + cutover sentinel sentry 의무 강화 §3.6.3).

## 12. 검수 체크리스트 (ArchitectPL Phase 3 — §섹션별 deputy input 통합 정합성)

| § | deputy author | 통합 정합성 |
|---|---------------|-------------|
| §2 | CodebaseMapper (보수 변호) | verified-via file:line 근거 — cold-read 8곳 + reverse-write 3곳 + MCT-184 routes_v1.py 372 lines + historical/orderbook endpoint 부재 (V6 추가 사실) + TickRowV1_1 SSOT market-core + ADR-030 §D15 prefix + R2 MCT-43~47 활성 진행 0 ✓ |
| §3·§6 | Refactor (혁신 옹호) | realtime_stream.py 신설 + data_client/ thin hand-written client + paper_runner.py:290 paper_lineage market-core 직독 변경 + historical/orderbook endpoint 본 Story 포함 채택. io/ + storage 자체 변경 0 ✓ |
| §7 (§7.1-§7.3/§7.5-§7.7) | SecurityArch (primary 강함) | T1-T7 위협↔완화 전수 매핑 + internal-only trust boundary + namespace 한정 + presigned 기각 (T6) + client-side allowlist + idempotent sha256 client-side ✓ |
| §7.4 | OperationalRiskArch (primary 강함 CONDITIONAL §8.5 active=true) | 운영 리스크 7+1 항목 (DR data api + DR Redis + disconnect + rate-limit + env-isolation + restart + clock + §8.5 stateful/background) — production wiring 활성화 = engine 11곳 production caller 활성화 영역 큼. retry/circuit-breaker (MCT-170 dr_mode 패턴) + local-only (Redis publisher) + ASGI lifespan ✓ |
| §8 | TestContractArch | TC-1~14 커버리지 + §8.0 Phase 0 Gate V1-V6 + Perf Baseline 필수 (cutover 추가 latency + REST wrap overhead + Redis Stream publish latency + circuit-breaker overhead) ✓ |
| §11 (§11.1-§11.5/§11.7) | DataMigrationArch | cutover (wrap-only) + 신설 = persisted-data 무변경 N/A 명시 ✓ |
| §11.6 | DataMigrationArch primary + OperationalRiskArch consult | client-side canonical hash idempotency + market-core SSOT 재사용 + MCT-184 F-2 bytes-level 정밀도 lesson reapply + restart-safe (persisted sidecar/sentinel) ✓ |
| (LiveOps/LiveOrdering CONDITIONAL) | R2 MCT-41 cross-cutting consult | engine `runtime/paper_runner.py` + `executor/tick_replay.py` 공유 모듈 위험 가설 유효 but Phase 0 V8 활성 MCT-43~47 진행 0 발견 → R2 risk **MEDIUM-HIGH (Phase 0 활성 진행 0 — baseline confirm)** + engine#N 진입 직전 재cross-check 의무 ✓ |

**§섹션 누락 차단 검증**: §7 보안 설계 ✓ / §7.4 운영 리스크 ✓ / §8 Test Contract ✓ /
§10 ADR 판단 ✓ / §11 데이터 마이그레이션 ✓ — 누락 0 (DesignReview P0 차단 회피).

**ArchitectPL 검수 verdict**: 6 deputy + 2 CONDITIONAL deputy perspective 전수 통합 +
chief author synthesis 정합. §3.6.1 gate v2 cross-Story reapply 박제 완료 + §3.6.2 박제
PR 5 체크리스트 inline 박제 (self-discipline carrier 2번째 — 1회 실증 효력 검증) + §3.6.3
Codex post-LAND audit 4 axis self-discipline (cutover lane sentinel sentry 의무 강화).
D-row 13/13 reconcile. **설계리뷰 lane 진입 가능** (잔여 risk = MCT-186 carry-over 명시
+ R2 engine#N 진입 직전 재cross-check 의무 — accept).
