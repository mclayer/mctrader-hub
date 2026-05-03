---
story_key: MCT-44
status: phase:요구사항
component: market-bithumb
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-002, ADR-007, ADR-008, ADR-012
---

# MCT-44: Bithumb Live API Adapter Hardening — KRW call site + rate-limit response + rejection mapping

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

mctrader-market-bithumb 측 Live API 경로 hardening. real Bithumb call (paper-shadow / dry-run only — MCT-43+45+46 전 까지 real order 금지).

## 2. 도메인 해석

MCT-41 child #3. mctrader-market-bithumb 의 live API call site. Order create / cancel / order status 의 Live 경로 + rate-limit error handling + exchange rejection mapping (ADR-002 H2 RejectionReason).

Prerequisite: MCT-42 merge. **MCT-43 + MCT-45 + MCT-46 PASS 전 까지 real order 금지** (paper-shadow / live-dry-run only, real KRW exposure 없음).

## 3. 관련 ADR

- ADR-002 H1 (8-state order lifecycle), H2 (RejectionReason)
- ADR-007 D4 (order rate limit, MCT-32 적용)
- ADR-008 D1-D3 (1Password vault + key permission)
- ADR-012 (Live Rollout 4-stage, stage 1-2 = paper-shadow + live-dry-run)

## 4. 관련 코드 경로

```
mctrader-market-bithumb/src/mctrader_market_bithumb/
├── live_client.py (NEW — Bithumb live REST + WS)
├── rejection_mapping.py (NEW — Bithumb error code → RejectionReason)
└── rate_limit_response.py (NEW — 429 retry-after / order rate limit handling)
```

## 5-6. 요구사항

1. Bithumb REST live order create / cancel / status — paper-shadow + live-dry-run mode 만 활성
2. Bithumb error code → RejectionReason mapping (ADR-002 H2)
3. Rate-limit response (ADR-007 D4 / MCT-32 sliding window 정합)
4. 1Password CLI 의존 — runtime injection (ADR-008 D1-D2)
5. **real order capability disabled** until MCT-43+45+46 PASS — flag-gated via `BithumbLiveClient(real_order_enabled: bool = False)`
