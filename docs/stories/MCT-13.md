---
story_key: MCT-13
status: phase:대기
component: market
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-002, ADR-009, ADR-010, ADR-011
---

# MCT-13: mctrader-market interface (Candle/OrderBook/Order Protocol)

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-13: mctrader-market interface (Candle/OrderBook/Order Protocol)"

## 2. 목표

`mctrader-market` repo 의 첫 commit 으로 exchange-neutral interface 를 정의:
- `Candle` Protocol (PEP 544) — ADR-009 OHLCV v1 의 logical view
- `OrderBook` Protocol — bids/asks snapshot
- `Order` Protocol + 8-state lifecycle (ADR-002)
- Decimal-based types (가격 / 수량 / 수수료)
- symbol / timeframe enum

## 3. 시작 조건

- MCT-12 Phase 1 PR merge 완료
- 다음 의 결정 적용:
  - Python `>=3.11,<3.13`, uv, pyproject.toml, ruff/pyright/pytest/pre-commit (ADR-010 / ADR-011)
  - Branch protection F5 mitigation set (required approvals = 0, CODEOWNERS off)
  - 첫 publish version = `0.1.0`

## 4. 의존

- 상위 의존: ADR-002, ADR-009 (Candle Protocol contract)
- 하위 의존자: MCT-14 (Bithumb adapter), MCT-15 (data — logical Candle mapping), MCT-16 (engine consume)

## 5. Acceptance (placeholder — Phase 1 brainstorm 에서 확정)

- TBD: Protocol definition 의 method set 범위 (read-only `get_candles` 만 vs full read+order)
- TBD: Decimal scale (38,18) 의 type hint 표현
- TBD: timezone 표현 (`datetime` UTC 또는 별도 type)
- TBD: ID type — `OrderId` newtype 또는 plain str

## 6. Phase 1 brainstorm 진행

Phase 1 = Codex 일괄 dispatch (7-area design review) → Sonnet 합성 → Story doc 완성 → Phase 1 PR. 본 stub 은 MCT-12 Phase 1 merge 후 elaborate.

## 7. CFP-60 debut-audit

Phase 2 merge 직후 `scripts/check-debut-audit-signals.sh` 실행 + Codex 7-카테고리 평가 + finding 시 `audit:from-mctrader-debut + category:*` 등록.
