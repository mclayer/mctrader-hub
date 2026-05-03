---
story_key: MCT-29
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-25
related_adrs: ADR-007, ADR-008, ADR-002, ADR-004
---

# MCT-29: EXTERNAL_SIGNAL kill-switch + Recovery 3-tier (D7)

## 1. 사용자 요구사항 (verbatim, MCT-25 Epic)

> "ADR-007 D1 EXTERNAL_SIGNAL — soft data_outage 30s+; hard manual_kill / API_ban / key_compromise (manual ack 의무) + ADR-007 D7 Recovery 3-tier (soft auto / hard manual_ack / critical key_rotation)"

## 2. 도메인 해석

mctrader-engine 의 외부 신호 trigger + 3-tier recovery state machine. ADR-008 D5 (Paper = secret 금지) align — manual_kill / API_ban / key_compromise 모두 file/CLI sentinel 또는 fixture 로만 simulate. data_outage 30s = WebSocket 연결 단절 측정. Recovery 3-tier = soft_stop auto cooldown 15min / hard_stop CLI ack + reconcile / critical_stop key_rotation 의무.

## 3. 관련 ADR

- ADR-007 D1 EXTERNAL_SIGNAL (data_outage 30s soft / manual_kill API_ban key_compromise hard)
- ADR-007 D7 Recovery 3-tier (soft auto / hard manual_ack / critical key_rotation)
- ADR-008 D5 (Paper secret 금지 — broker API X)
- ADR-002 (RiskGate Protocol check-only)
- ADR-004 (RiskGateEvent v2 ack_status field)
- 의존: MCT-26 freeze (RiskPolicy.external_data_outage_*)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── kill_switch.py (extend)         # evaluate_external_signal
├── external_signal.py (NEW)        # CLI/file-sentinel manual_kill (ADR-008 align)
├── recovery.py (NEW)               # 3-tier state machine
└── enforcer.py (extend)            # EXTERNAL_SIGNAL + recovery 통합

mctrader-engine/src/mctrader_engine/cli.py (extend)
                                    # mctrader-cli risk kill / risk ack subcommand
```

## 5-6. 요구사항

- file sentinel: `<artifacts>/risk_kill.signal` (JSON: ts_utc, reason, trigger)
- CLI: `mctrader-cli risk kill --run-id <id> --reason <txt>` (write file)
- CLI: `mctrader-cli risk ack --run-id <id>` (acknowledge hard_stop)
- data_outage = MarketStream.last_message_ts 추적 (BithumbWebSocketStream extension)
- 3-tier state: pass → soft_stop → hard_stop → critical_stop (one-way escalation, downgrade X)

## 7. 설계 서사 (Codex 합성)

### 7.1 ExternalSignal sentinel (A1)

```python
class ExternalSignalSentinel:
    def __init__(self, *, signal_path: Path): ...
    def check(self, *, now: datetime) -> SignalKind | None: ...  # manual_kill / api_ban / key_compromise / None
    def write_kill(self, *, reason: str): ...  # CLI 가 호출
    def clear(self): ...  # ack 시 (hard_stop only, critical_stop 은 별도 run 의무)
```

JSON schema:
```json
{
  "ts_utc": "2026-05-03T12:00:00Z",
  "reason": "manual operator kill — strategy bug suspected",
  "trigger": "manual_kill" | "api_ban" | "key_compromise"
}
```

### 7.2 evaluate_external_signal (A2)

```python
def evaluate_external_signal(
    *, signal_kind: SignalKind | None,
    last_market_data_ts: datetime, now: datetime,
    data_outage_soft_seconds: int
) -> SwitchEvaluation:
    if signal_kind == "manual_kill": return hard
    if signal_kind == "api_ban": return hard
    if signal_kind == "key_compromise": return critical  # 신규 severity tier
    outage = (now - last_market_data_ts).total_seconds()
    if outage >= data_outage_soft_seconds: return soft
    return pass
```

**Severity 확장**: 기존 `pass / soft / hard` → `pass / soft / hard / critical`. critical = key_compromise / mismatch>2% / unknown_position / withdrawal_anomaly (ADR-007 D7 critical_stop tier 와 align).

### 7.3 Recovery 3-tier state machine (A3)

```python
class RecoveryState(StrEnum):
    PASS = "pass"
    SOFT_STOP = "soft_stop"      # 15min cooldown + health check
    HARD_STOP = "hard_stop"      # manual ack 의무
    CRITICAL_STOP = "critical_stop"  # key_rotation 의무, run 종료

class RecoveryManager:
    def __init__(self, *, policy: RiskPolicy, clock: Clock): ...
    def transition(self, *, current_severity: Severity, ts: datetime) -> RecoveryState: ...
    def can_resume_soft(self, *, ts: datetime) -> bool: ...  # 15min cooldown + 5min health
    def request_ack(self, *, run_id: str): ...
    def confirm_ack(self, *, run_id: str, snapshot_reconciled: bool, orders_reconciled: bool, positions_reconciled: bool): ...
```

**같은 날 hard_stop 2회** = `_hard_stop_count_today` ≥ 2 → 다음 daily reset 후 manual override 의무 (state field).

**Recovery 첫 1h reduced mode** = stub field `recovery_reduced_mode_until_ts` (Live Epic 에서 본격 enforce, paper = report only).

### 7.4 CLI integration (A4)

```
mctrader-cli risk kill --run-id <id> --reason <txt>
   → write <artifacts>/risk_kill.signal (manual_kill trigger)

mctrader-cli risk ack --run-id <id>
   → 1) load RiskPolicySnapshot (verify hash unchanged)
     2) reconcile open orders (Paper = cancel all)
     3) reconcile positions (VirtualPortfolio invariant)
     4) check ≥30min cooldown
     5) clear risk_kill.signal
     6) RecoveryManager.confirm_ack
```

critical_stop 은 ack subcommand 거부 — 별도 run_id 의무 (D7 tier 3).

### 7.5 ADR-008 D5 align (A5)

EXTERNAL_SIGNAL 의 4 sub-trigger 모두 broker API X:
- manual_kill = file sentinel 만
- api_ban = config flag (test fixture) 또는 향후 Live Epic 에서 broker error code 매핑
- key_compromise = config flag (test fixture)
- data_outage = MarketStream timestamp 만 (REST ping X)

### 7.6 Out-of-scope

- 자동 critical_stop recovery (key rotation 자동화) = manual 의무
- web ack UI (CLI ack 만)
- multi-operator authority (D9 의 operator field 는 single)

### 7.7 Acceptance (10 AC)

| # | AC |
|---|---|
| AC1 | ExternalSignalSentinel file sentinel read/write |
| AC2 | CLI `risk kill` subcommand |
| AC3 | data_outage detection (last_market_data_ts) |
| AC4 | severity 확장 (pass/soft/hard/critical) |
| AC5 | RecoveryManager 3-tier state machine |
| AC6 | soft_stop auto resume (15min cooldown + health check) |
| AC7 | hard_stop manual ack flow (CLI risk ack + 4 reconcile) |
| AC8 | critical_stop block (별도 run_id 의무, ack 거부) |
| AC9 | hard_stop 2회/day → 다음 reset 후 manual override |
| AC10 | 5 required check green |

### 7.8 Codex 적용

7/7 채택. ADR conflict 0/7 (ADR-008 D5 align 명시).

## 8-11

(Phase 2 = risk/external_signal.py + recovery.py + kill_switch.py + cli.py extension.)
