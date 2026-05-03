---
story_key: MCT-19
status: phase:요구사항
component: market-bithumb
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-001, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-19: mctrader-market-bithumb WebSocket adapter (public ticker/orderbook/transaction stream)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Bithumb WebSocket adapter for Paper mode realtime stream"

## 2. 도메인 해석

`mctrader-market-bithumb` 0.1.0 의 첫 async 확장. Bithumb public WebSocket (`wss://pubwss.bithumb.com/pub/ws`) → `MarketStream` Protocol impl (PaperExecutor injection 대상).

**ADR-009 invariant 보존**: adapter = raw stream event Protocol shape 만, OHLCV bar 조립 = mctrader-engine BarAggregator 책임.

## 3. 관련 ADR

- ADR-001 (Bithumb#1)
- ADR-008 D5 (public-only / Authorization 절대 X / 1Password 의존 X)
- ADR-009 (raw event Protocol)
- ADR-010 (Pydantic v2 boundary / Decimal canonical / async)
- ADR-011 (Network test = mocked / replay fixture default)
- 의존: MCT-12 freeze (mctrader-market 0.1.0)

## 4. 관련 코드 경로

```
mctrader-market-bithumb/src/mctrader_market_bithumb/
├── ws_client.py           # BithumbWebSocketStream (websockets lib)
├── ws_subscribe.py        # subscribe builder + type allowlist
├── ws_events.py           # TickerEvent / OrderbookSnapshotEvent / OrderbookDeltaEvent / TransactionEvent
├── ws_mapping.py          # raw dict → typed event
└── ws_secret_guard.py     # 4-layer enforcement extension

tests/
├── fixtures/bithumb/
│   ├── ws_ticker_BTC_KRW.jsonl
│   ├── ws_orderbook_BTC_KRW.jsonl
│   └── ws_transaction_BTC_KRW.jsonl
├── test_ws_mapping.py
├── test_ws_client.py
├── test_ws_secret_guard.py
└── test_ws_policy_imports.py
```

## 5-6. 요구사항 / 외부 지식

- Python 3.11+ asyncio + `websockets>=12,<14`
- Bithumb WebSocket public schemas (ticker / orderbookdepth / transaction)
- Server ping ~60s → client pong 의무
- mctrader-market `>=0.1,<0.2` (Symbol + Decimal38_18 + UTCDateTime)

## 7. 설계 서사 (Codex 합성)

### 7.1 Library = `websockets` (A1)

asyncio native, lifecycle/heartbeat/receive loop 가장 단순. `aiohttp`/`httpx-ws` 비채택 (REST httpx 와 client 철학 분리 + standard API stability).

### 7.2 Pure async (A2)

`BithumbWebSocketStream` async iterator. sync wrapper 비채택 (asyncio.run 중첩 / cancellation 복잡). MCT-21 PaperExecutor = async runtime 통합.

### 7.3 4 event types + Lightweight Protocol (A3)

```python
@runtime_checkable
class MarketStream(Protocol):
    async def __aenter__(self) -> "MarketStream": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    def messages(self) -> AsyncIterator[StreamEvent]: ...
```

| Event | 사용 |
|---|---|
| `TickerEvent` | diagnostics + market state |
| `OrderbookSnapshotEvent` | SimulatedFillEngine depth 초기화 |
| `OrderbookDeltaEvent` | depth update ([VERIFY] Bithumb support, snapshot-only fallback) |
| `TransactionEvent` | BarAggregator primary tick source |

각 event = Pydantic v2 strict + Decimal38_18 + UTCDateTime + `raw` field (replay/debug). `StreamEvent = Union[...]` discriminated on `kind` Literal.

### 7.4 Reconnection + heartbeat (A4)

| Mechanism | Default |
|---|---|
| Server ping → pong | `websockets` library 자동 |
| Stale detection | 90s message 없음 → reconnect |
| Backoff | exponential 1s/2s/4s/.../max 60s + jitter ±20% |
| Max attempts | indefinite (cancellation 까지) |
| Re-subscribe | last subscription set 자동 재전송 |

### 7.5 Subscribe lifecycle (A5)

내부 multi-symbol set, public API = single-symbol first (future-proof). subscribe = connection 직후 explicit message. reconnect = re-send 동일 set.

### 7.6 Replay fixture (A6)

JSONL primary (한 줄 = 한 message) + session JSON secondary (lifecycle test 만). mapping layer Pydantic boundary, 검증 실패 = `WebSocketSchemaError` raise (silent skip 금지).

### 7.7 Public-only = 4 layer (A7)

| Layer | 검증 |
|---|---|
| URL allowlist | `wss://pubwss.bithumb.com/pub/ws` only |
| Handshake header guard | Authorization / Api-Key / X-BITHUMB-* `extra_headers` 절대 X |
| Subscribe payload guard | type allowlist (`ticker` / `orderbookdepth` / `transaction` 만) + Authorization / API key 시사 field denylist |
| Policy lint extension | source 에서 `websockets.connect(extra_headers=...)` / `aiohttp` WS auth / `httpx-ws` auth 사용 X |

**가장 critical**: subscribe type allowlist (user account / order status 등 private stream = mechanical 차단).

### 7.8 Pyproject extension

```toml
dependencies = [
    "mctrader-market @ git+...",
    "httpx>=0.27,<1",
    "websockets>=12,<14",   # 새 dependency
    "pydantic>=2,<3",
]
```

### 7.9 Out-of-scope

Production reconnection (sequence num / message replay) / Multi-symbol routing public / Private endpoint / Async REST extension / sync wrapper / VCR cassette.

### 7.10 Acceptance (11 AC)

| # | AC |
|---|---|
| AC1 | dependency websockets + 1Password 의존 X |
| AC2 | 5 required check green |
| AC3 | `BithumbWebSocketStream` = `MarketStream` Protocol 만족 |
| AC4 | 4 event Pydantic boundary (Decimal38_18 + UTCDateTime) |
| AC5 | JSONL fixture replay roundtrip |
| AC6 | mock disconnect → backoff → re-subscribe |
| AC7 | Server ping/pong + stale detection 90s |
| AC8 | Layer 1 URL allowlist (다른 host reject) |
| AC9 | Layer 2 forbidden header guard |
| AC10 | Layer 3 subscribe type allowlist + payload denylist |
| AC11 | Layer 4 policy_imports lint |

### 7.11 Codex

7/7 채택. ADR conflict 0/7 (새 `websockets` dependency 추가는 ADR-010 의 async option 안).

## 8-11

(Phase 2 = ws_* module 추가 + AC1~AC11.)
