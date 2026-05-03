---
adr_id: ADR-012
title: Live Rollout Policy — 4-stage gate + first KRW cap + 3-contract schema
status: Accepted
date: 2026-05-04
related_story: MCT-42 (carrier), MCT-41 (Epic)
category: live
supersedes: []
amends: []
---

# ADR-012: Live Rollout Policy — 4-stage gate + first KRW cap + 3-contract schema

## Status

**Accepted** — 2026-05-04. MCT-42 Phase 1 PR (carrier of Sonnet decider Phase 1 D3+D5+D6).

## Context

mctrader Live mode = first real KRW exposure. ADR-002 D9 (3-condition AND) + ADR-008 D4 (secret access) 는 boundary 만 정의 — rollout sequence / cap / runtime contract schema 부재.

Sonnet decider Phase 1 (MCT-41 Epic, 2026-05-04) 의 D3+D5+D6 sub-decision 통합:

- D3: First live KRW cap (3 options A/B/C, pick=A 10,000 KRW)
- D5: Rollout sequence (3 options, pick=A 4-stage)
- D6: Live contract set (3 options, pick=A 3종 동시 schema 정의)

Codex audit (gpt-5.5 high, 2026-05-04, 7-area + decomposition) + Sonnet decider (claude-sonnet-4-6) 합의.

## Decision

### D1. 4-stage rollout sequence (Sonnet decider D5=A)

```
Stage 1: paper-shadow
  ↓ pass criteria: 7-day sustained operation, signal calibration drift < 5%, ledger reconcile = 100%, kill switch test PASS
Stage 2: live-dry-run (real Bithumb API, real order calls, 거래소 측 reject)
  ↓ pass criteria: 3-day API path verify, rate-limit response correct, rejection mapping 100%, kill switch real trigger test PASS
Stage 3: tiny-live (real KRW, 10,000 KRW cap, 단일 round trip)
  ↓ pass criteria: first round trip 완료 + 즉시 reconcile + audit log 정합 + 24h grace cancel verify
Stage 4: full live
  ↓ ongoing operation under ADR-007 RiskGate full + ADR-008 D8 emergency response standby
```

각 stage 미충족 시 다음 stage 진입 금지 — 4-stage 직렬 강제.

### D2. First live KRW cap (Sonnet decider D3=A)

**10,000 KRW** (~7-8 USD).

근거:
- Bithumb 최소 주문 5,000 KRW (B option) 대비 2배 — fee/fill 검증 충분 신호
- 50,000 KRW (C option) 대비 real-loss 노출 제한 (D5 Stage 3 tiny-live 취지 정합)

Stage 3 진입 시 hard cap. 본 cap 위반 시 LiveExecutor 즉시 reject (engine call site enforcement).

### D3. Live contract set 3종 schema 정의 (Sonnet decider D6=A)

Phase 1 = schema 정의만. Producer impl = MCT-43~46 implementation.

**`live-trade-event-v1`**:
```yaml
kind: contract
contract_version: 1
event_types:
  - submit
  - accept
  - reject
  - partial_fill
  - fill
  - cancel
  - reconcile
fields:
  - event_type (enum)
  - order_id
  - exchange_order_id (nullable)
  - timestamp (UTC)
  - state (8-state lifecycle, ADR-002 H1)
  - reason (nullable, RejectionReason if state in [rejected, partial_fill_rejected])
  - quantity_total
  - quantity_filled
  - price_avg
  - fee_paid (KRW)
  - reconcile_status (engine_only / verified_match / drift_detected)
producer: mctrader-engine LiveExecutor
consumer: incident_log / monitoring / audit
```

**`risk-decision-v1`**:
```yaml
kind: contract
contract_version: 1
decision_types:
  - allow
  - deny
  - throttle
fields:
  - decision_type (enum)
  - timestamp (UTC)
  - category (drawdown / max_exposure / rate_limit / krw_drift / first_trade_cap / ...)
  - scope (per_order / per_symbol / per_account / per_strategy / global)
  - exposure_actual
  - exposure_limit
  - reason
  - policy_hash (ADR-007 D9 amendment trail)
  - policy_version
producer: mctrader-engine RiskGate
consumer: LiveExecutor / incident_log / audit
```

**`operator-action-v1`**:
```yaml
kind: contract
contract_version: 1
action_types:
  - confirm-live          # ADR-002 D9 --confirm-live
  - kill-switch-trigger   # manual kill (UI/CLI)
  - resume                # post-incident resume
  - key-rotation          # ADR-008 D7
  - incident-acknowledge  # ADR-008 D8 7-step
fields:
  - action_type (enum)
  - operator_id           # ADR-008 D10 single user
  - timestamp (UTC)
  - reason
  - evidence_ref          # incident log / audit trail link
  - approval_chain        # nullable — Phase 2+ multi-operator
producer: UI / CLI / incident response interface
consumer: mctrader-engine LiveExecutor (enforcement)
```

위치: `mctrader-hub/docs/inter-plugin-contracts/` (kind:contract). 별도 schema file (Phase 2 producer impl 시 backfill).

### D4. Engine-enforced kill switch (cross-ref ADR-002 amendment)

Sonnet decider D4=A — kill switch enforcement = `mctrader-engine/executor/components/kill_switch.py` 가 source. UI/web/monitoring = trigger only.

상세 = ADR-002 amendment (MCT-42 Phase 1 PR).

### D5. Hybrid workflow gate placement (Sonnet decider D7=A)

codeforge wrapper 측 reusable workflow template (live-test-guard / live-deploy-approval / live-secret-policy / kill-switch-integration-test) + mctrader 측 policy value (KRW cap 10,000 / Bithumb / 출금 비활성 / IP allowlist).

mctrader 측은 `.github/workflows/` 에서 codeforge wrapper template 호출. Wrapper 측 작업 = mclayer/plugin-codeforge#162~#165 (CFP-NN 별도 후속).

### D6. 1Password-only default + incident-only fallback (cross-ref ADR-008 amendment)

Sonnet decider D8=A. 상세 = ADR-008 amendment (MCT-42 Phase 1 PR).

## Alternatives Considered

### A1. Big-bang live (D5 reject — option C)
- **기각**: paper-shadow 없이 직접 real KRW 노출. ADR-008 D5 evidence quality 미충족.

### A2. 3-stage (skip paper-shadow, D5 reject — option B)
- **기각**: paper-shadow = real KRW 노출 없이 Live API 경로 + order book + fee 검증 unique 단계. evidence-gathering 손실.

### A3. 5,000 KRW cap (D3 reject — option B)
- **기각**: Bithumb 최소 단일 주문 — fee 가 수익률 잠식, validation signal 약함.

### A4. 50,000 KRW cap (D3 reject — option C)
- **기각**: tiny-live 단계에서 학습 비용 너무 높음. ADR-008 D5 real-loss containment 정합 결여.

### A5. Defer contract schema until implementation (D6 reject — option C)
- **기각**: 구현 후 schema 정의 = cross-plugin schema churn. Phase 1 doc-only 의 "구현 전 interface 고정" 가치 손실.

### A6. operator-action only first, defer trade-event + risk-decision (D6 reject — option B)
- **기각**: live order audit trail 공백 — ADR-008 D10 incident response 사후 분석 불가.

## Consequences

### C1. ADR-002 amendment 의무
D4 engine-enforced kill switch 명시 — ADR-002 D11 components 에 kill_switch.py 추가.

### C2. ADR-008 amendment 의무
D8 incident-only fallback exception process 명시.

### C3. Stage gate 강제
4-stage 각 미충족 시 다음 stage 진입 금지. CI gate 통합 = MCT-47.

### C4. 3 contract schema 정의 후 producer impl 의존
- live-trade-event-v1 producer = MCT-43 LiveExecutor
- risk-decision-v1 producer = MCT-43 RiskGate (ADR-007 fork)
- operator-action-v1 producer = MCT-46 KillSwitch + UI/CLI

### C5. KRW cap engine-enforced
- LiveExecutor 가 모든 order 직전 cap verify
- cap 위반 = order reject + incident log

### C6. cross-ref codeforge wrapper 작업 의무
Hybrid gate placement = wrapper template 의존. mclayer/plugin-codeforge#162~#165 처리 후 mctrader 측 통합 (MCT-47).

## Cross-references

- MCT-41 (Epic) / MCT-42 (carrier Story)
- ADR-002 amendment (D4 engine-enforced kill switch)
- ADR-008 amendment (D8 incident-only fallback)
- ADR-007 (RiskGate, MCT-32 D4 적용 완료)
- mclayer/plugin-codeforge#156-#167 (12 codeforge improvement candidates)
- Sonnet decision packet MCT-Live-Epic-Phase1-001 (D1-D8 batch)
- Codex audit (gpt-5.5 high, 2026-05-04) — 7-area + decomposition
