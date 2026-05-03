---
story_key: MCT-45
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-002, ADR-007, ADR-012
---

# MCT-45: Ledger / Reconciliation / KRW Position — partial fill / fee / cancel / replay invariants

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

Live 진입 prerequisite 의 핵심 — partial fill / fee handling / cancel race / restart replay / KRW position reconciliation invariant. ADR-002 D6 (SQLite event log) extended.

## 2. 도메인 해석

MCT-41 child #4. ADR-002 D6 의 Paper SQLite event log 를 Live ledger 로 확장. 4 reconciliation invariant 강제:
- Partial fill (8-state H1 PARTIALLY_FILLED → FILLED 전환 시 fee + balance 정합)
- Fee handling (Bithumb fee 0.04% taker / 0.04% maker)
- Cancel race (CANCEL_REQUESTED + 일부 체결 동시)
- Restart replay (engine 종료 후 재시작 = ledger 복원 = exchange 측 truth 와 일치 verify)
- KRW position reconciliation (engine ledger KRW position = Bithumb account balance)

Prerequisite: MCT-42 merge.

## 3. 관련 ADR

- ADR-002 D6 (SQLite event log), H1 (8-state lifecycle)
- ADR-007 D2 (max exposure, CONDITIONAL active in Live)
- ADR-012 (Live Rollout — first KRW cap 10,000)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── executor/components/
│   ├── live_ledger.py (NEW — extends paper ledger)
│   ├── reconciliation.py (NEW — engine ↔ Bithumb truth verify)
│   └── krw_position.py (NEW — KRW exposure tracking)
└── tests/integration/
    ├── test_live_ledger_partial_fill.py (NEW)
    ├── test_live_ledger_cancel_race.py (NEW)
    ├── test_live_ledger_restart_replay.py (NEW)
    └── test_live_reconciliation.py (NEW)
```

## 5-6. 요구사항

1. Live ledger SQLite schema 확장 (paper schema + KRW_position + fee_actual + reconcile_status fields)
2. Partial fill invariant: PARTIALLY_FILLED event → fee + balance update + remaining quantity 정합
3. Cancel race invariant: CANCEL_REQUESTED 후 부분 체결 시 ledger = "취소 + 일부 체결" composite state 기록
4. Restart replay: process kill → restart → ledger 재구축 → Bithumb account balance 와 일치 verify
5. KRW position invariant: Live KRW position = Bithumb KRW account balance (drift < 1 KRW = OK, ≥ 1 KRW = critical_stop)
