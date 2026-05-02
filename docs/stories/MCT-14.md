---
story_key: MCT-14
status: phase:대기
component: market-bithumb
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-001, ADR-008, ADR-009, ADR-010, ADR-011
---

# MCT-14: mctrader-market-bithumb adapter (get_candles + raw fixture)

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-14: mctrader-market-bithumb adapter (`get_candles()`)"

## 2. 목표

`mctrader-market-bithumb` repo:
- HTTP client (httpx 또는 aiohttp — Phase 1 결정)
- Bithumb public OHLCV endpoint 호출 (Secret 미사용 / ADR-008 — Backtest = secret 금지)
- `CandleProvider` Protocol impl (MCT-13 freeze 후)
- raw response fixture 저장 (deterministic test 의 input)
- ADR-009 거래소 normalization 의무 (timezone, decimal precision, symbol naming)

## 3. 시작 조건

- MCT-13 Phase 2 merge — `Candle` Protocol freeze 완료
- 첫 publish version = `0.1.0`

## 4. 의존

- 상위 의존: MCT-13 (Candle Protocol freeze)
- 하위 의존자: MCT-15 daemon (raw fixture / live response 양쪽 source)

## 5. Acceptance (placeholder — Phase 1 brainstorm 에서 확정)

- TBD: HTTP library 선정 (httpx vs aiohttp)
- TBD: rate limit / retry / backoff policy
- TBD: normalization 규칙 (Bithumb response → ADR-009 v1 schema)
- TBD: fixture 저장 위치 / 형식 (raw JSON 또는 recorded HTTP)

## 6. Phase 1 brainstorm 진행

MCT-13 Phase 2 merge 후 Codex 일괄 dispatch → Sonnet 합성 → Story doc → Phase 1 PR.

## 7. CFP-60 debut-audit

Phase 2 merge 직후 audit signal check + 7-카테고리 평가.
