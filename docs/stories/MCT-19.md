---
story_key: MCT-19
status: phase:대기
component: market-bithumb
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-001, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-19: mctrader-market-bithumb WebSocket adapter (public ticker/orderbook/trade stream)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "Bithumb WebSocket adapter for Paper mode realtime stream"

## 2. 목표

`mctrader-market-bithumb` repo 에 WebSocket adapter 추가:
- `wss://pubwss.bithumb.com/pub/ws` public endpoint connection
- Subscribe: ticker / orderbook / transaction
- `MarketStream` Protocol impl (PaperExecutor 가 inject)
- Heartbeat + basic reconnect/backoff
- Public-only enforcement (Phase 2 secret_guard 와 동일)

## 3. 시작 조건

- ✅ MCT-12 freeze (mctrader-market 0.1.0)
- ✅ MCT-18 Phase 1 PR merge

## 4. 의존

- 상위: ADR-001 / ADR-008, mctrader-market `>=0.1,<0.2`
- 하위: MCT-21 PaperExecutor (stream consumer)

## 5. Acceptance (placeholder)

- TBD: WebSocket library (asyncio `websockets` vs aiohttp.WSClient)
- TBD: subscribe message format + heartbeat policy
- TBD: reconnection backoff
- TBD: message schema validation
- TBD: stream event Protocol shape (ticker / orderbook delta / trade)

## 6. Phase 1 brainstorm

MCT-18 Phase 1 merge 후 Codex 일괄 dispatch → Sonnet 합성 → docs/stories/MCT-19.md 본 brainstorm → Phase 1 PR.

## 7. CFP-60 debut-audit

Phase 2 merge 후 audit signal check + 7-카테고리 평가 (특히 workflow-invariant + contract-schema).
