---
story_key: MCT-46
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-002, ADR-008, ADR-012
---

# MCT-46: Kill Switch + Operator Actions — engine-enforced + manual halt/resume + incident log

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

Sonnet decider D4 pick=A — kill switch = **engine-enforced** (LiveExecutor 가 enforcement source, UI/monitor 는 trigger only). UI 장애 시에도 kill 가능 boundary.

## 2. 도메인 해석

MCT-41 child #5. ADR-002 amendment (MCT-42) 의 D4 engine-enforced kill switch 구현. operator-action-v1 contract producer impl. incident log + manual halt/resume + 자동 발동 trigger 통합.

자동 trigger (engine 내):
- ADR-007 D1+D2 critical_stop (drawdown / max exposure)
- ADR-007 D4 rate limit hard violation (실제 발동)
- KRW position reconciliation 실패 (MCT-45 invariant)
- Bithumb API key compromise 의심 (ADR-008 D8)

Manual trigger (UI/CLI/incident response):
- operator-action-v1 schema (kill / resume / acknowledge)

Prerequisite: MCT-42 + MCT-45 (ledger reconcile invariant 의존).

## 3. 관련 ADR

- ADR-002 amendment D4 (engine-enforced kill switch)
- ADR-008 D8 (compromise emergency response 7-step), D10 (OperationEvent)
- ADR-012 (operator-action-v1 schema)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── executor/components/
│   ├── kill_switch.py (NEW — engine enforcement source)
│   ├── operator_action.py (NEW — operator-action-v1 producer)
│   └── incident_log.py (NEW — emergency response audit trail)
└── tests/integration/
    ├── test_kill_switch_auto_trigger.py
    ├── test_kill_switch_manual_override.py
    └── test_kill_switch_engine_enforcement.py
```

## 5-6. 요구사항

1. KillSwitch class — engine LiveExecutor 가 모든 order call 직전 본 class verify (call site enforcement)
2. 자동 trigger 4종 통합 (drawdown / max_exposure / rate_limit / KRW_drift)
3. Manual trigger interface — operator-action-v1 producer (kill / resume / ack)
4. Incident log = SQLite append-only + audit trail (ADR-008 D10 OperationEvent)
5. UI 장애 시 engine kill 가능 verify (CLI / direct API call)
