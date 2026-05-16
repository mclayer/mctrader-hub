---
story_key: MCT-186
epic_key: EPIC-data-domain-decoupling
type: change-plan
author: ArchitectPLAgent (chief author = ArchitectAgent + 6 deputy + 2 CONDITIONAL deputy synthesis)
created: "2026-05-17"
status: design-lane-draft
decisions: [D4]
related_adrs:
  - "ADR-031-data-domain-decoupling §D4 (engine exchange-adapter 제거 — subscribe-normalized-stream. 본 Story = §D4 VERIFIED amendment box 박제. Status Accepted 유지)"
  - "ADR-030-docker-stack-governance (engine compose NAS cred drop — MCT-186 owner 확정. POLICY_FINALIZED 본문 19 D 무변경, amendment box 패턴)"
  - "ADR-029-tier-promotion-single-source (접촉 없음 — MCT-185 §D2 VERIFIED 완결, 본 Story NAS 직독 0 유지)"
  - "ADR-032 (VERIFIED badge evidence triad — ADR-031 §D4 VERIFIED amendment box 에 file:line + caller grep + integration test 3종 의무)"
---

# MCT-186 Change Plan — engine realtime cutover + exchange-adapter 제거

> ArchitectAgent (chief author) + 6 deputy (CodebaseMapper / Refactor / SecurityArch
> **primary** / OperationalRiskArch **primary CONDITIONAL §8.5 active** /
> TestContractArch / DataMigrationArch) + 2 CONDITIONAL deputy (LiveOps / LiveOrdering —
> R2 MCT-41 ZERO RISK 확인됨, CONDITIONAL 미발동) synthesis. ArchitectPLAgent 검수.
>
> **EPIC-data-domain-decoupling 7 Story sequential strangler-fig 5단계**. D4 단독.
> engine `mctrader_market_bithumb` 직접 import 5곳 5파일 전수 제거 → MCT-185 LAND
> Redis Stream `market:tick:{exchange}:{symbol}` XREAD 구독 전환. engine =
> exchange-adapter-free + 정규화 TickRowV1_1 소비. §0 V7/V8 Phase 0 정정 적용
> (engine-local `OrderbookSnapshot` dataclass 신규 정의 포함).

## 1. 목표 / 비목표

### 1.1 목표 (D4 — scope_manifest `§story_decision_matrix.MCT-186` 1:1)

- **D4 (engine exchange-adapter 제거 — `option_chosen: subscribe-normalized-stream`)**:
  engine src/ `mctrader_market_bithumb` import **5곳 5파일 전수 제거** (§0 V3 HEAD 실증치).
  MCT-185 publisher (`XADD market:tick:{exchange}:{symbol}`, payload=`TickRowV1_1.model_dump_json()`)
  구독 전환. engine = **정규화 `TickRowV1_1`** 소비 (bithumb-specific WS 이벤트 타입 폐기).

- **D4-1 [결정] Redis subscriber 위치**: `src/mctrader_engine/realtime/redis_subscriber.py` 신규
  (기존 `realtime/` 패키지 내 배치 — `MarketStream` Protocol 준수 유지, paper_runner 합류 최소화).
  `data_client/` 확장 기각 — HTTP client 와 Redis subscriber 는 도메인 분리 (HTTP = REST/cold,
  Redis = realtime/hot). 비동기 `redis.asyncio` (`redis[hiredis]>=5`, engine dev dep 신규 추가).

- **D4-2 [결정] orderbook 처리**: **engine-local `OrderbookSnapshot` dataclass 신규** +
  별도 Redis Stream key `market:orderbook:{exchange}:{symbol}` XREAD (data 측 추가 publisher
  는 MCT-186 scope-opt — data 측 orderbook publisher 미LAND 시 **최후 orderbook 캐시 유지
  모드** fallback). MCT-185 data realtime_stream.py 는 tick 전용 — orderbook publisher =
  별 Story(MCT-186 scope 판단). **본 Story 채택**: orderbook = Redis Stream tick payload
  내 포함 불가 (TickRowV1_1 스키마 변경 0 원칙) → engine 측 `_latest_orderbook` 초기화 후
  orderbook stream 가용 시 갱신, **미가용 시 SimulatedFillEngine 에 orderbook=None fallback**
  (paper mode = 검증 모드, VWAP 대신 market-price fill 폴백 허용).

- **D4-3 [결정] `MarketStream` Protocol 유지**: `redis_subscriber.py` 가 `MarketStream`
  Protocol 준수 (`__aenter__`/`__aexit__` + `messages() -> AsyncIterator[TickRowV1_1]`).
  `WsWrapperStream` = **제거 대상** (bithumb WS watchdog 용도 — Redis subscriber 는 자체
  reconnect 로직 보유, WsWrapperStream 의 timeout/exhaustion 정책 불필요). `PaperExecutor`
  는 `stream: MarketStream` 타입 어노테이션 유지, yield 타입만 교체.

- **D4-4 [결정] bithumb/upbit RealtimeStream Protocol conformance**: **본 Story opt-out**.
  MCT-187 (다중거래소 불변식) 에서 처리. 본 Story = engine 측 adapter 제거 집중.

- **D4-5 [결정] paper_runner `_build_upstream_stream()` 분기**: `MOCK_FEED` env / `--mock-feed`
  CLI flag = `MockMarketStream` (TickRowV1_1 기반) 유지. 기본 경로 = `RedisStreamSubscriber`
  (exchange, symbol, REDIS_URL env 기반). `BithumbWebSocketStream` lazy import 완전 제거.

### 1.2 비목표 (out-of-scope)

| 항목 | owner Story |
|------|-------------|
| engine `pyproject.toml` `mctrader-market-bithumb` 의존 line 제거 | MCT-188 (D7 quad gate final) |
| data 측 orderbook Redis Stream publisher 신규 (별도 `market:orderbook:` key XADD) | MCT-186 scope-opt → MCT-187 or 별 Story |
| bithumb/upbit RealtimeStream Protocol conformance | MCT-187 |
| 다중거래소 확장 불변식 invariant test + runbook | MCT-187 |
| data-free grep0 quad gate CI (.github/workflows/) | MCT-188 |
| ADR-031 POLICY_FINALIZED 전이 | MCT-188 |
| MCT-182 shim 잔존 4곳 (`tick_storage`/`orderbook_storage`/`aggregation`/`tick_scalping.py` shim) | MCT-188 |

## 2. 배경 / AS-IS (CodebaseMapper 변호 — verified-via)

> **CodebaseMapper deputy perspective** — verified-via `git fetch origin` + `Grep` + `Read`
> (2026-05-17, engine origin/main HEAD `1312195` MCT-185 LAND).

### 2.1 AS-IS 사실 (file:line — Phase 0 V3~V10 HEAD 실증치)

| 사실 | file:line |
|------|-----------|
| bithumb import 1 | `fill/simulated.py:18 from mctrader_market_bithumb.ws_events import OrderbookSnapshotEvent` |
| bithumb import 2 | `realtime/stream_consumer.py:8-12 from mctrader_market_bithumb.ws_events import (OrderbookSnapshotEvent, StreamEvent, TickerEvent, TransactionEvent,)` |
| bithumb import 3 | `runtime/mock_stream.py:19 from mctrader_market_bithumb.ws_events import StreamEvent, TickerEvent, TransactionEvent` |
| bithumb import 4 | `runtime/paper_runner.py:267 from mctrader_market_bithumb.ws_client import BithumbWebSocketStream` (function-local) |
| bithumb import 5 | `runtime/ws_wrapper.py:30 from mctrader_market_bithumb.ws_events import StreamEvent` |
| _latest_orderbook 타입 | `stream_consumer.py:36 _latest_orderbook: OrderbookSnapshotEvent \| None` |
| fill 파라미터 타입 | `fill/simulated.py:60 orderbook: OrderbookSnapshotEvent` — `.asks`/`.bids` `.price`/`.quantity` 접근 |
| mock bithumb 이벤트 생성 | `mock_stream.py:58-82 events: list[StreamEvent]` — `TransactionEvent(...)` + `TickerEvent(...)` 생성 |
| _build_upstream_stream | `paper_runner.py:264-269` — mock_feed 분기 + BithumbWebSocketStream lazy |
| PaperExecutor._consume loop | `executor/paper.py:124,132 async for event in source: closed = self._consumer.on_event(event)` |
| TickRowV1_1 기존 소비 | `hot/state_machine.py:42` + `hot/streaming_aggregator.py:55,109,140` — MCT-185 LAND 전부터 존재 |
| MCT-185 Redis publisher payload | `data/api/realtime_stream.py` — XADD key=`market:tick:{exchange}:{symbol}`, fields=`{"payload": TickRowV1_1.model_dump_json()}` |
| engine `data_client/` 5파일 | MCT-185 LAND — `base.py` + `historical.py` + `reverse_write.py` + `exceptions.py` + `__init__.py` |
| engine pyproject bithumb dep | `pyproject.toml:12 mctrader-market-bithumb @ git+...` — MCT-188 final 제거 owner |

### 2.2 CodebaseMapper 유지 근거 (보수 변호)

- **`BarAggregator.on_transaction(ts_utc, price, quantity)` 시그니처 무변경** — TickRowV1_1
  `.ts_utc`/`.price`/`.quantity` 필드와 직접 매핑. StreamConsumer 교체 후 byte-equiv 보존.
- **`PaperExecutor._consume()` 루프 구조 무변경** — `async for event in source: consumer.on_event(event)`.
  yield 타입만 `StreamEvent` → `TickRowV1_1` 교체 (루프 제어 변경 0).
- **`MarketStream` Protocol 유지** — `ws_wrapper.py` 제거 후 `redis_subscriber.py` 가 동일
  Protocol 준수 → `_build_upstream_stream()` 교체 1곳으로 paper_runner 최소 변경.
- **MCT-185 `data_client/` 5파일 무변경** — 본 Story 는 HTTP REST 호출 경로 변경 0. realtime
  subscriber 는 Redis 직접 구독 (HTTP 경유 0).

## 3. 변경 계획 (engine repo — Phase 2 PR1)

### 3.1 신규 파일

#### 3.1.1 `src/mctrader_engine/realtime/types.py` (신규 — V7/V8 Phase 0 정정)

```python
"""Engine-local realtime event types — exchange-agnostic, bithumb 비결합.

MCT-186 D4 cutover: bithumb ws_events.OrderbookSnapshotEvent 제거 후
engine-local OrderbookSnapshot 으로 교체. SimulatedFillEngine 파라미터 타입 정합.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mctrader_market.types import Symbol


@dataclass(frozen=True, slots=True)
class _Level:
    """Exchange-agnostic orderbook level (price + quantity)."""
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class OrderbookSnapshot:
    """Exchange-agnostic orderbook snapshot (engine-local).

    bithumb ws_events.OrderbookSnapshotEvent 와 구조 동일하나 _BaseEvent 무관.
    D4 cutover: bithumb-specific 타입 → engine-local 타입 교체.
    """
    exchange: str
    symbol: Symbol
    ts_utc: datetime
    bids: tuple[_Level, ...]
    asks: tuple[_Level, ...]
```

#### 3.1.2 `src/mctrader_engine/realtime/redis_subscriber.py` (신규 — D4-1 결정)

```python
"""Redis Stream subscriber — MCT-186 D4 engine realtime cutover.

MarketStream Protocol 준수:
  __aenter__ / __aexit__ — Redis connection lifecycle
  messages() -> AsyncIterator[TickRowV1_1] — XREAD loop

Stream key: market:tick:{exchange}:{symbol}  (ADR-030 §D15 prefix 정합)
REDIS_URL env: REDIS_URL (default: redis://localhost:6379/0)
payload: TickRowV1_1.model_validate_json(fields["payload"])

DR: Redis disconnect → exponential backoff 5회 → StopAsyncIteration
(paper mode = 검증 모드, WS watchdog 미적용).
"""
from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from mctrader_market.schemas.tick import TickRowV1_1
from mctrader_market.types import Symbol

logger = logging.getLogger(__name__)

_REDIS_URL_ENV = "REDIS_URL"
_DEFAULT_REDIS_URL = "redis://localhost:6379/0"
_BLOCK_MS = 1000  # XREAD BLOCK milliseconds
_RETRY_MAX = 5
_RETRY_BASE_S = 0.5
_STREAM_KEY_PREFIX_ENV = "REDIS_KEY_PREFIX_MARKET"
_DEFAULT_PREFIX = "market"


def _stream_key(exchange: str, symbol: str) -> str:
    """ADR-030 §D15 key: market:tick:{exchange}:{symbol}."""
    prefix = os.environ.get(_STREAM_KEY_PREFIX_ENV, _DEFAULT_PREFIX)
    return f"{prefix}:tick:{exchange}:{symbol}"


class RedisStreamSubscriber:
    """XREAD subscriber — MarketStream Protocol 준수 + TickRowV1_1 역직렬화.

    Usage (paper_runner _build_upstream_stream 대체):
        subscriber = RedisStreamSubscriber(exchange="bithumb", symbol=symbol)
        async with subscriber:
            async for tick in subscriber.messages():
                await process(tick)
    """

    def __init__(self, *, exchange: str, symbol: Symbol) -> None:
        self._exchange = exchange
        self._symbol = symbol
        self._stream_key = _stream_key(exchange, str(symbol))
        self._redis: Any = None
        self._last_id = "$"  # 최신 entry 부터 구독 (backfill 0)

    async def __aenter__(self) -> "RedisStreamSubscriber":
        import redis.asyncio as aioredis  # noqa: PLC0415
        redis_url = os.environ.get(_REDIS_URL_ENV, _DEFAULT_REDIS_URL)
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("MCT-186 RedisStreamSubscriber: connected (%s key=%s)", redis_url, self._stream_key)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def messages(self) -> AsyncIterator[TickRowV1_1]:
        """XREAD loop — yield TickRowV1_1 역직렬화."""
        consecutive_errors = 0
        while True:
            try:
                results = await self._redis.xread(
                    {self._stream_key: self._last_id},
                    block=_BLOCK_MS,
                    count=100,
                )
                consecutive_errors = 0
                if not results:
                    continue
                for _key, entries in results:
                    for entry_id, fields in entries:
                        self._last_id = entry_id
                        payload_str = fields.get("payload", "")
                        if not payload_str:
                            continue
                        try:
                            tick = TickRowV1_1.model_validate_json(payload_str)
                            yield tick
                        except Exception as e:
                            logger.warning("MCT-186: TickRowV1_1 역직렬화 실패 (%s): %s", entry_id, e)
                            continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors > _RETRY_MAX:
                    logger.error("MCT-186: Redis XREAD %d 회 실패 — 구독 종료 (%s)", _RETRY_MAX, e)
                    return
                backoff = _RETRY_BASE_S * (2 ** (consecutive_errors - 1))
                logger.warning("MCT-186: Redis XREAD 실패 (retry %d/%d, backoff=%.1fs): %s",
                               consecutive_errors, _RETRY_MAX, backoff, e)
                await asyncio.sleep(backoff)

    @property
    def ticks_received(self) -> int:
        """HealthServer signal 호환 — 실제 count 는 caller 측 관리."""
        return 0  # best-effort stub (WsWrapperStream 제거 후 HealthServer probe 정합)
```

### 3.2 변경 파일

#### 3.2.1 `src/mctrader_engine/realtime/stream_consumer.py` (교체)

- bithumb `from mctrader_market_bithumb.ws_events import (...)` **제거**
- `MarketStream.messages()` yield 타입: `AsyncIterator[StreamEvent]` → `AsyncIterator[TickRowV1_1]`
- `StreamConsumer.on_event(event: StreamEvent)` → `on_event(event: TickRowV1_1)` 교체:
  - `isinstance(event, TransactionEvent)` 분기 → `BarAggregator.on_transaction(ts_utc=event.ts_utc, price=event.price, quantity=event.quantity)` 직접 (TransactionEvent 제거)
  - `isinstance(event, OrderbookSnapshotEvent)` 분기 → **제거** (orderbook = 별도 stream, D4-2)
  - `isinstance(event, TickerEvent)` 분기 → **제거** (diagnostics-only, TickRowV1_1 불포함)
  - `_latest_orderbook: OrderbookSnapshotEvent | None` → `_latest_orderbook: OrderbookSnapshot | None` (engine-local 타입)
- import 교체: `from mctrader_engine.realtime.types import OrderbookSnapshot` + `from mctrader_market.schemas.tick import TickRowV1_1`

**변경 후 `StreamConsumer.on_event()` 핵심 로직**:
```python
def on_event(self, tick: TickRowV1_1) -> ClosedBarEvent | None:
    return self._aggregator.on_transaction(
        ts_utc=tick.ts_utc,
        price=tick.price,
        quantity=tick.quantity,
    )
```

#### 3.2.2 `src/mctrader_engine/fill/simulated.py` (교체)

- `from mctrader_market_bithumb.ws_events import OrderbookSnapshotEvent` → `from mctrader_engine.realtime.types import OrderbookSnapshot`
- `fill(*, ..., orderbook: OrderbookSnapshotEvent, ...)` → `fill(*, ..., orderbook: OrderbookSnapshot, ...)`
- `orderbook.asks`/`orderbook.bids` → `orderbook.asks`/`orderbook.bids` (필드명 동일, `_OrderbookLevel` → `_Level` 내부 호환)
- `level.price`/`level.quantity` 접근 = 변경 0 (동일 필드명)

#### 3.2.3 `src/mctrader_engine/runtime/mock_stream.py` (교체)

- `from mctrader_market_bithumb.ws_events import StreamEvent, TickerEvent, TransactionEvent` **제거**
- `MockMarketStream` yield 타입: `list[StreamEvent]` → `list[TickRowV1_1]`
- `load_mock_stream_from_json()` 내부:
  - `"transaction"` kind → `TickRowV1_1(ts_utc=..., exchange="bithumb", symbol=symbol, trade_id=str(uuid.uuid4()), price=..., quantity=..., side="BUY" | "SELL", is_taker=True)` 직접 생성
  - `"ticker"` kind → **skip** (TickRowV1_1 불포함, diagnostics-only 제거)
  - fixture `ws_mock_smoke.json` 재사용 (kind/event_time/price/quantity/side 필드 재매핑)
- import 추가: `import uuid`, `from mctrader_market.schemas.tick import TickRowV1_1`

**`load_mock_stream_from_json()` 변환 핵심**:
```python
if row.get("kind") == "transaction":
    events.append(TickRowV1_1(
        ts_utc=datetime.fromisoformat(row["event_time"]).replace(tzinfo=timezone.utc),
        exchange="bithumb",
        symbol=symbol,
        trade_id=str(uuid.uuid4()),
        price=Decimal(row["price"]),
        quantity=Decimal(row["quantity"]),
        side="BUY" if row.get("side", "buy").lower() == "buy" else "SELL",
        is_taker=True,
    ))
```

#### 3.2.4 `src/mctrader_engine/runtime/ws_wrapper.py` (대폭 축소 또는 제거)

- **채택 방향**: `WsWrapperStream` = bithumb WS 전용 watchdog (reconnect 횟수 budget +
  per-event timeout). `RedisStreamSubscriber` 는 자체 retry 보유 → `WsWrapperStream` 불필요.
- **결정**: `ws_wrapper.py` 파일 **제거** (MCT-186 D4-3 결정). `paper_runner.py` 에서
  `from mctrader_engine.runtime.ws_wrapper import WsWrapperStream` import 제거 + 래핑 코드 제거.
- `bithumb import:30 from mctrader_market_bithumb.ws_events import StreamEvent` **파일 자체 제거**로 해소.
- `tests/test_paper_runner.py` 에서 `WsWrapperStream` 관련 테스트 = mock-feed 모드만 사용 (WsWrapperStream 미사용) → 영향 0.
- **[설계리뷰 P0 수정]** `cli.py:442 from mctrader_engine.runtime.ws_wrapper import StreamExhaustedError` + `:597 except StreamExhaustedError` 발견 — ws_wrapper.py 제거 시 cli.py 추가 수정 의무 (§3.2.4b 신규)

#### 3.2.4b `src/mctrader_engine/cli.py` (변경 — ws_wrapper 제거 연쇄)

- `from mctrader_engine.runtime.ws_wrapper import StreamExhaustedError` (line:442) **제거**
- `StreamExhaustedError` = Redis subscriber 기반 연결 실패는 `StopAsyncIteration` 또는 내부 retry 소진 후 함수 반환 (예외 raise 없음) → `except StreamExhaustedError` 블록 **제거 + DB 상태 업데이트 대체 경로 통합**
- **채택**: `except StreamExhaustedError` 블록 내 DB run_store.update_run_failed 로직을 
  `finally` 블록 또는 `except Exception` 범위로 흡수 (Redis subscriber 실패 = graceful return → `run()` 종료 후 정상 finalise 경로)
- **연쇄 파일**: `src/mctrader_engine/cli.py` = 6번째 변경 파일 (5곳 5파일 + cli.py 1파일 = **6파일 수정**)

#### 3.2.5 `src/mctrader_engine/runtime/paper_runner.py` (변경)

- `from mctrader_market_bithumb.ws_client import BithumbWebSocketStream` lazy import **제거** (line:267)
- `from mctrader_engine.runtime.ws_wrapper import WsWrapperStream` import **제거**
- `_build_upstream_stream()` 교체:
  ```python
  def _build_upstream_stream(self):
      if self._mock_feed is not None:
          return load_mock_stream_from_json(self._mock_feed, symbol=self._symbol)
      from mctrader_engine.realtime.redis_subscriber import RedisStreamSubscriber  # noqa: PLC0415
      return RedisStreamSubscriber(exchange="bithumb", symbol=self._symbol)
  ```
- `wrapper = WsWrapperStream(upstream, max_events=self._max_events)` → **제거** 후
  `upstream = self._build_upstream_stream()` → `executor(..., stream=upstream, ...)` 직접 전달.
  `max_events` 파라미터 = `MockMarketStream` 에서 처리 (fixture 기반, Redis subscriber 무관).
- `ws_connected` property: `self._wrapper.ticks_received > 0` → `RedisStreamSubscriber.ticks_received` 또는 `False` fallback (HealthServer best-effort)

### 3.3 테스트 파일 변경

#### 3.3.1 `tests/test_simulated_fill.py` (교체 — V8 Phase 0 정정)

- `from mctrader_market_bithumb.ws_events import OrderbookSnapshotEvent, _OrderbookLevel` **제거**
- `from mctrader_engine.realtime.types import OrderbookSnapshot, _Level` 추가
- `_build_book()` 팩토리 함수: `OrderbookSnapshotEvent(...)` → `OrderbookSnapshot(exchange="bithumb", symbol=..., ts_utc=..., bids=(...), asks=(...))`
- `_OrderbookLevel(price=..., quantity=...)` → `_Level(price=..., quantity=...)`
- **논리 변경 0** — bithumb 타입만 engine-local 타입으로 교체 (fill 계산 무변경)

#### 3.3.2 `tests/test_realtime_subscriber.py` (신규 — QADeveloperAgent owner)

- `testcontainers[redis]` (MCT-180 `test_paper_redis_boundary.py` 패턴 재사용)
- Redis container 시작 → XADD `market:tick:bithumb:KRW-BTC` payload=`TickRowV1_1.model_dump_json()`
- `RedisStreamSubscriber.__aenter__` → `messages()` XREAD → `TickRowV1_1` 역직렬화 round-trip
- 최소 3 assertions: (a) tick.price/quantity 값 동일 (b) tick.ts_utc timezone-aware (c) tick.exchange/symbol 정합

### 3.4 ADR/compose 변경 (hub Phase 1 + Phase 2 PR2)

#### 3.4.1 `docs/adr/ADR-031-data-domain-decoupling.md` (§D4 VERIFIED amendment box)

```markdown
### §D4 VERIFIED amendment box (MCT-186 LAND 박제, 2026-05-17)

D4 (engine exchange-adapter 제거 — subscribe-normalized-stream) **VERIFIED**:
- engine `src/` `from mctrader_market_bithumb` = **0건** (AC-1 grep0, engine#N TBD)
- `realtime/types.py` 신규 — engine-local `OrderbookSnapshot` + `_Level` dataclass (bithumb 비결합)
- `realtime/redis_subscriber.py` 신규 — XREAD `market:tick:{exchange}:{symbol}`, TickRowV1_1.model_validate_json() 역직렬화
- `realtime/stream_consumer.py` 교체 — `on_event(tick: TickRowV1_1)` 직접 BarAggregator.on_transaction() 위임 (bithumb 이벤트 Union 제거)
- `runtime/ws_wrapper.py` 제거 — WsWrapperStream (bithumb WS watchdog) 폐기, RedisStreamSubscriber 자체 retry 대체
- paper mode byte-equiv 보존 (BarAggregator.on_transaction 시그니처 변경 0 — ts_utc/price/quantity 직접 매핑)
- ADR-032 evidence triad: file:line (5곳 5파일 제거 commit sha) + caller grep = 0 + integration test (test_realtime_subscriber.py PASS)
- ADR-030 §D15 Redis prefix 정합 (market:tick: namespace 유지)
- Status `Accepted` 유지 (POLICY_FINALIZED 전이 = MCT-188)
```

#### 3.4.2 `docs/adr/ADR-030-docker-stack-governance.md` (engine NAS cred drop amendment box)

```markdown
### MCT-186 engine NAS cred drop amendment (2026-05-17)

MCT-184 amendment box 예고 (engine NAS cred drop — 본 Story 확정):
- engine compose service 에서 `NAS_MINIO_ENDPOINT`/`NAS_MINIO_ACCESS_KEY`/`NAS_MINIO_SECRET_KEY` env **제거**
- 근거: MCT-185 §D2 VERIFIED — engine src/ `from mctrader_data.nas_storage` = 0 (grep0) + NAS 직독 경로 완전 폐기
- engine 은 data REST API (`DATA_API_BASE_URL`) 경유 + Redis Stream XREAD (`REDIS_URL`) 경유만 접근
- ADR-030 본문 19 D 정책 무변경 (POLICY_FINALIZED 보존)
```

### 3.5 scope_manifest 변경 (hub Phase 1)

`scope_manifests/EPIC-data-domain-decoupling.yaml`:
- `story_sequence[MCT-186].status` : `RESERVED` → `IN_PROGRESS`
- `milestone_progress.completed` : 4 → (진행 중)

### 3.6 self-discipline (§3.6.1 gate v2 cross-Story reapply)

#### 3.6.1 cross-document SSOT gate v2

**glob-scope** (변형 포괄):
```
docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md
scope_manifests/EPIC-data-domain-decoupling.yaml
```

**변형 포괄 pattern** (MCT-183 lesson — 대소문자/하이픈/언더스코어 변형 + lazy import 포함):
```
mctrader.market.bithumb | mctrader_market_bithumb | bithumb.ws_events | BithumbWebSocketStream
OrderbookSnapshotEvent | StreamEvent | TransactionEvent | TickerEvent
```

**self-verify TEST1**: Change Plan §3 전수 항목 ↔ Story §4 Delta 표 1:1 대조 (누락 0)
**self-verify TEST2**: post-LAND engine repo-wide grep `from mctrader_market_bithumb` = 0줄

#### 3.6.2 박제 PR 5 체크리스트 (Phase 2 PR2 LAND 전)

- [ ] RETRO-MCT-186.md 존재
- [ ] EPIC-RESULTS-EPIC-data-domain-decoupling.md §Story-5 추가
- [ ] Story frontmatter `status: COMPLETED` + `completed_at` 기재
- [ ] CLAUDE.md hub#TBD 잔존 0줄
- [ ] ADR-031 §D4 VERIFIED amendment box + ADR-030 NAS cred drop amendment box 전수 LAND 확인

#### 3.6.3 Codex post-LAND 4 axis audit

- (1) bithumb grep 0 확인 (AC-1)
- (2) paper mode mock-feed smoke PASS (AC-2/AC-4)
- (3) SSOT 재검증 (TickRowV1_1 market-core SSOT 단일 사용 확인)
- (4) security: redis subscriber payload validation (TickRowV1_1.model_validate_json — Pydantic strict 보장)

## 4. §0 Phase 0 Verify Gate (Change Plan 재확인)

Story §0 V1~V10 수치를 Change Plan §2.1 AS-IS 표로 1:1 재인용. 추가 정정 없음.

**D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson)**:

| D-row | scope_manifest `§design_decisions` | Change Plan §1 | Story §5 AC | 정합 |
|-------|--------------------------------------|----------------|-------------|------|
| D4 | `option_chosen: subscribe-normalized-stream` `owner_story: MCT-186` | §1.1 목표 D4 | AC-1~AC-7 | ✅ |
| D6 | `option_chosen: new-adr-031 + 3-amend` | §3.4 ADR 변경 | AC-5/AC-6 | ✅ |

## 5. 비기능 요구사항 (NFR)

| NFR | 기준 | gate |
|-----|------|------|
| NFR-1 | AC-4 paper mode mock-feed run < 60s (MCT-49 Calibration C5 SLO) | `test_paper_runner_smoke_writes_outputs` PASS |
| NFR-2 | Redis XREAD latency (local Redis) < 10ms p99 (synthetic) | `test_realtime_subscriber.py` round-trip assert |
| NFR-3 | bithumb import grep0 영구 (D7 quad gate 진입 조건) | post-LAND CI 확인 |

## 6. 구현 순서 (land_order)

```
hub Phase 1 PR (mct-186-phase1-engine-realtime-cutover)
  → Story §0-§11 + ADR-031 §D4 draft + ADR-030 NAS cred drop box + scope_manifest + CLAUDE.md

engine#N Phase 2 PR1 (mct-186-phase2-engine-realtime-cutover)
  → 5파일 bithumb import 제거 + realtime/types.py + realtime/redis_subscriber.py 신규
  → stream_consumer/fill/mock_stream/paper_runner 교체 + ws_wrapper.py 제거
  → tests/test_simulated_fill.py 교체 + tests/test_realtime_subscriber.py 신규

hub Phase 2 PR2 (mct-186-phase2-pr2-bagje)
  → Story §8.5 Impl Manifest + §9/§10 LAND 확정 + ADR-031 §D4 VERIFIED + ADR-030 NAS cred drop LAND
  → scope_manifest milestone 5/7 + counters.json COMPLETED + CLAUDE.md + RETRO + EPIC-RESULTS §Story-5
```

## 7. 리스크

| Risk | Severity | 완화 |
|------|----------|------|
| R1 MockMarketStream fixture 호환성 | MEDIUM | `ws_mock_smoke.json` kind/event_time/price/quantity/side 필드 재매핑 → `TickRowV1_1` (side: buy→BUY, event_time→ts_utc). fixture 구조 변경 0. `test_paper_runner_smoke_writes_outputs` 회귀로 검증 |
| R2 MCT-41 live mode 충돌 | HIGH | Phase 0 V2 = **ZERO RISK** (MCT-43~47 active branch 0건). engine#N 진입 직전 R2 재재cross-check 의무 |
| R3 WsWrapperStream 제거 시 HealthServer `ws_connected` probe 파손 | LOW | `paper_runner.ws_connected` = `self._wrapper.ticks_received > 0` 로직 → RedisStreamSubscriber 기반 `ticks_received` stub 0 fallback + HealthServer best-effort 패턴 유지 (MCT-49 AC 재확인) |
| R4 Redis 미기동 시 paper mode 시작 실패 | LOW | mock-feed 모드 = Redis 미사용 (테스트/개발 환경 영향 0). production = data compose service + Redis 동시 기동 (ADR-030 single-host) |

## 8. 테스트 계약 (TestContractArch deputy — QADeveloperAgent 인계)

| 테스트 | 파일 | 타입 | gate |
|--------|------|------|------|
| `test_paper_runner_smoke_writes_outputs` | `tests/test_paper_runner.py` | unit | AC-2/AC-4 (byte-equiv 회귀 0) |
| `test_paper_runner_invalid_strategy_raises` | `tests/test_paper_runner.py` | unit | 회귀 0 |
| `test_simulated_fill_*` (전체) | `tests/test_simulated_fill.py` | unit | AC-7 (engine-local 타입 교체 후 ALL PASS) |
| `test_realtime_subscriber_round_trip` | `tests/test_realtime_subscriber.py` (신규) | integration (testcontainers[redis]) | AC-3 (XADD → XREAD → TickRowV1_1 round-trip) |
| bithumb import grep0 | `grep -rn "from mctrader_market_bithumb" src/` | CI gate | AC-1 (0줄) |
| engine full suite | `pytest tests/` | 회귀 | INV-5 (MCT-185 baseline 회귀 0) |

### §8.5 Perf Baseline

| 항목 | MCT-185 baseline | MCT-186 gate |
|------|-----------------|--------------|
| mock-feed smoke (10 events) | < 60s | < 60s (unchanged) |
| bithumb import grep0 (AS-IS) | 5건 | **0건** |
| test_simulated_fill ALL PASS | ✅ | ✅ |

## 9. 보안 (SecurityArch deputy)

- Redis Stream XREAD payload = `TickRowV1_1.model_validate_json()` — Pydantic strict 역직렬화
  (arbitrary JSON injection 차단 — MCT-184 CodeQL CWE-22 path traversal fix 동형 사전 방지)
- `REDIS_URL` env = 신뢰 환경 (ADR-030 single-host loopback) — TLS 미적용 (R1 HIGH 사용자
  accept 패턴, MCT-155 TLS cutover 별 Story 백로그 정합)
- engine-local `OrderbookSnapshot` = bithumb `_BaseEvent` 미상속 → INV-3 영구 (exchange-agnostic)

## 10. 운영 리스크 (OperationalRiskArch deputy §8.5 active)

- **paper mode fallback**: Redis 미기동 시 mock-feed 모드 강제 (production 영향 0 in dev)
- **orderbook stream 미LAND 시**: `_latest_orderbook = None` 초기화 유지 → fill 엔진이
  `orderbook=None` 수신 시 `InsufficientLiquidityError` raise (paper mode 허용 — 실 주문 0)
- **engine compose NAS env drop**: AC-6 — production deploy 시 compose.yml 수동 확인 의무
  (ADR-030 amendment box 박제 후 engineer alert)
