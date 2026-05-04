---
story_key: MCT-52
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-007
---

# MCT-52: RiskGate Operator Action Exposure — web button + CLI parity

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

ADR-007 D7 manual ack semantics 가 web 측 노출. 기존 `mctrader-cli risk ack` (MCT-29 도입) 와 동일 효과. 핵심 invariant = "risk_policy_hash unchanged + open-order reconciliation + position reconciliation + cooldown + actor 기록".

## 2. 도메인 해석

MCT-48 child #4. RiskGate hard-stop 발생 시 PaperExecutor 가 자동 재개 절대 금지 — operator manual ack 후에만 재개. CLI / web 양방향 parity.

핵심 difference vs MCT-46 (Live Engine Kill Switch):
- MCT-52 = Paper RiskGate ack flow 의 web 노출 (read-existing + button)
- MCT-46 = Live Engine 의 신규 kill switch + operator-action-v1 producer (Live Epic)

MCT-52 는 Paper 의 기존 PaperRiskGate (MCT-22, MAX_DAILY_LOSS + DRAWDOWN_LIMIT) + RecoveryManager (MCT-29, 3-tier) 가 이미 구현된 상태에서 control plane 노출만 추가.

## 3. 관련 ADR

- ADR-007 D7 (manual ack) — 본 Story 핵심
- ADR-007 D9 (RiskPolicy versioning + risk_policy_hash) — ack 시 hash 변경 거부

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── risk/
│   ├── enforcer.py (READ — PaperRiskGate)
│   ├── recovery.py (READ — RecoveryManager 3-tier, MCT-29)
│   └── ack.py (NEW or MODIFY — operator ack pure function)
├── cli.py (MODIFY — risk ack subcommand 가 OperatorActionEvent emit)
└── event_store/writer.py (MCT-51 reuse — OperatorActionEvent emit)

mctrader-web/src/mctrader_web/api/routes/
└── risk.py (NEW — POST /runs/{id}/risk/ack)
```

## 5-6. 요구사항

1. RiskGate hard-stop = 기존 동작 유지 (MCT-22+29). PaperExecutor pause loop 진입.
2. CLI: `mctrader-cli risk ack --run-id {id} --reason "{text}" --artifacts-dir {path}` (기존, MCT-29). MCT-52 변경 = OperatorActionEvent emit 추가 (event store wired).
3. FastAPI: `POST /runs/{run_id}/risk/ack` body `{actor, reason}`. 동일 ack 함수 호출 + OperatorActionEvent emit.
4. Invariant enforce:
   - `risk_policy_hash` 가 ack 시점 정책 과 일치 (불일치 = 422 / CLI exit 1)
   - 모든 open order = 명시 cancel or close (reconciliation pass) (Paper 기준 = simulated, 실제 cancel 발사 X)
   - position_qty = 명시 confirmed (zero or non-zero with reason)
   - cooldown ≥ 60초 (active hard-stop 후 60초 내 ack 거부)
   - actor field 의무 (CLI=`local-user-cli`, web=`local-user-web`)
5. ack 성공 → RecoveryManager downgrade event emit + PaperExecutor resume.
6. ack 실패 → 명시 reason (hash mismatch / open orders / cooldown / unconfirmed position) + RiskGate 상태 그대로 유지.
7. Test: ack happy path / hash mismatch / open orders / cooldown / web vs CLI parity (동일 effect).

## 7. 보안 설계 / 11. 데이터 영향

- 보안: actor 기록 의무 (operator action audit trail). reason text = required (length ≥ 5, not empty).
- 신규 file: `risk/ack.py` + `api/routes/risk.py` + tests.
- 수정 file: `cli.py risk ack` (event emit), `recovery.py` (downgrade event emit).
- version bump engine 0.14.0 → 0.15.0, web 0.2.0 → 0.3.0.
- DB schema: 변경 없음 (event store reuse).
- Reversible: yes.
