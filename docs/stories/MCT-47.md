---
story_key: MCT-47
status: phase:요구사항
component: hub-cross-repo
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-008, ADR-011, ADR-012
---

# MCT-47: Live Rollout Gates + Evidence — CI fail-default + 4-stage pass criteria + first-trade runbook

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

Sonnet decider D7 pick=A (Hybrid) + ADR-012 의 4-stage rollout 의 verification + first-trade runbook 작성. real KRW 진입 마지막 gate.

## 2. 도메인 해석

MCT-41 child #6 (final). ADR-012 의 4-stage rollout pass criteria 검증 + Live workflow gate 강제 (CI fail-default / live-deploy-approval / live-secret-policy / kill-switch test) + first real trade runbook.

Sonnet decider D7 = Hybrid: codeforge wrapper 측 reusable workflow template + mctrader 측 policy value (KRW cap = 10,000 / Bithumb / 출금 비활성). codeforge wrapper 측 작업은 별도 CFP (mclayer/plugin-codeforge#157~#167 처리). 본 Story = consumer 측 통합.

Prerequisite: MCT-42 + MCT-43 + MCT-44 + MCT-45 + MCT-46 모두 PASS.

## 3. 관련 ADR

- ADR-008 D5 (CI fail-default)
- ADR-011 (branch-protection-ci) — Live workflow gate 통합
- ADR-012 (4-stage rollout pass criteria)

## 4. 관련 코드 경로

```
mctrader-hub/
├── docs/runbooks/
│   ├── live-first-trade-10000-krw.md (NEW)
│   ├── kill-switch-trigger.md (NEW)
│   └── incident-response-7step.md (NEW)
└── .github/workflows/
    ├── live-test-guard.yml (use codeforge wrapper template)
    ├── live-deploy-approval.yml (use codeforge wrapper template)
    ├── live-secret-policy.yml (use codeforge wrapper template)
    └── kill-switch-integration-test.yml (use codeforge wrapper template)

mctrader-engine + mctrader-market-bithumb:
└── 4-stage CI integration (각 stage pass criteria CI artifact 의무)
```

## 5-6. 요구사항

1. ADR-012 4-stage rollout pass criteria 별 CI gate 통합 (paper-shadow → dry-run → tiny-live → full)
2. Live workflow gate 4종 (codeforge wrapper template 사용 — Hybrid)
3. First-trade runbook (10,000 KRW cap, 즉시 reconcile, 24h grace cancel)
4. Kill switch trigger runbook (4 자동 trigger + 1 manual)
5. Incident response runbook (ADR-008 D8 7-step)
6. **본 Story PASS 후 진짜 first real KRW trade 가능** (단 사용자 직접 1Password 설정 + Bithumb live API 발급 + KRW 입금 + IP allowlist + 출금 비활성 prerequisite 완료 의무)
