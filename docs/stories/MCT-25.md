---
story_key: MCT-25
status: phase:요구사항
component: hub
type: epic
related_stories: MCT-26, MCT-27, MCT-28, MCT-29, MCT-30
related_adrs: ADR-002, ADR-004, ADR-007, ADR-008
parent_epic: MCT-18 (predecessor)
---

# MCT-25: RiskGate full = ADR-007 5 kill-switch 완성 + Recovery 3-tier (Epic)

## 1. 사용자 요구사항 (verbatim)

> "그냥 이 세션 내에서 수행하는 모든 phase를 codex의 리뷰를 받아 sonnet decider가 채택하는 우선 순위에 의해 진행하고 phase마다는 compact를 한번씩 수행하라" — 6 후속 candidate 중 Codex 추천 1순위 = **RiskGate full** (Foundation dependency 강함, Reversibility 최고, Live mode 의 prerequisite).

## 2. 도메인 해석

mctrader 의 **세 번째 implementation Epic** (MCT-12 Backtest, MCT-18 Paper 다음). Paper mode 의 `PaperRiskGate` 가 ADR-007 5 kill-switch 중 2 (MAX_DAILY_LOSS + DRAWDOWN_LIMIT) 만 enforce 하는 minimal subset 상태. MCT-25 = 나머지 3 + D5 SL/TP guard + D7 Recovery 3-tier + D8 active_capital lock enforce + D9 RiskPolicy versioning 완성.

핵심 가치 = (a) **운영 안전성** — 5 kill-switch 모두 enforce 시 Paper run 의 risk-incompatible 행동 식별 가능. (b) **Live mode prerequisite** — ADR-006 promotion gate "risk violation 0" 을 5 kill-switch 모두로 검증. Live Epic 은 RiskGate full 통과 후 진입.

## 3. 관련 ADR (RiskGate full 핵심)

| ADR | RiskGate full 적용 |
|---|---|
| ADR-002 | RiskGate Protocol check-only interface 보존, internal stateful 확장 |
| ADR-004 | RiskGateEvent schema extension (5 kill-switch 공통 reason_code + ack_status + policy_hash) |
| ADR-007 D1 | 3 신규 kill-switch (CONSECUTIVE_LOSSES + UNUSUAL_ACTIVITY + EXTERNAL_SIGNAL) |
| ADR-007 D5 | catastrophic_stop / max_position_age / price_gap_guard / intended_stop_loss_pct |
| ADR-007 D6 | Daily KST reset 보존 (HWM / weekly drawdown reset 안 함) |
| ADR-007 D7 | Recovery 3-tier (soft_stop auto / hard_stop manual_ack / critical_stop manual + key_rotation) |
| ADR-007 D8 | active_capital lock enforce (현재 metric only → kill-switch trigger) |
| ADR-007 D9 | RiskPolicy versioning + canonical_json + hash + amendment_from + run-time freeze |
| ADR-008 D5 | Paper = secret 금지 보존 (EXTERNAL_SIGNAL 의 manual_kill 도 file/CLI sentinel 만, broker API X) |

## 4. 관련 코드 경로 (5 신규 child Story 분담)

```
mctrader-engine/                       # MCT-26 (foundation: policy versioning + active_capital lock)
└── src/mctrader_engine/risk/
    ├── policy.py (extend)              # canonical_json + hash + amendment_from + freeze
    ├── policy_snapshot.py (NEW)        # run-start lock + drift detection
    └── enforcer.py (extend)            # active_capital exposure check (D8)

mctrader-engine/                       # MCT-27 (CONSECUTIVE_LOSSES)
└── src/mctrader_engine/risk/
    ├── kill_switch.py (extend)         # evaluate_consecutive_losses (5 soft / 7 hard, min 10 closed)
    └── trade_ledger.py (NEW)           # closed trade tracking (FILLED + PARTIALLY_FILLED 종료)

mctrader-engine/                       # MCT-28 (UNUSUAL_ACTIVITY)
└── src/mctrader_engine/risk/
    ├── kill_switch.py (extend)         # evaluate_unusual_activity (reject_rate / data_stale / duplicate / opposite)
    └── activity_window.py (NEW)        # 5min rolling window + minimum sample guard

mctrader-engine/                       # MCT-29 (EXTERNAL_SIGNAL + Recovery 3-tier)
└── src/mctrader_engine/risk/
    ├── kill_switch.py (extend)         # evaluate_external_signal
    ├── external_signal.py (NEW)        # CLI/file-sentinel manual_kill (Paper 의 ADR-008 align)
    └── recovery.py (NEW)               # soft_stop auto cooldown / hard_stop manual_ack / critical_stop key_rotation

mctrader-engine/                       # MCT-30 (D5 SL/TP guards + Calibration AC + Epic E2E)
└── src/mctrader_engine/risk/
    ├── stop_loss_guard.py (NEW)        # catastrophic_stop / max_position_age / price_gap_guard
    └── tests/test_risk_full_e2e.py     # B1~B10 + C1 통합 acceptance

mctrader-data/                         # MCT-26 (RiskPolicy snapshot persistence)
└── src/mctrader_data/
    └── risk_snapshot.py (NEW)          # risk_policy_snapshot partition writer
```

## 5-6. 요구사항 / 외부 지식

- ADR-007 5 kill-switch enforcement
- Closed trade ledger (FILLED + PARTIALLY_FILLED 종료 = "closed", cancel-only partial 도 손익 확정)
- 5min rolling window + minimum sample (paper simulated reject 부족 시 fixture replay)
- manual_kill = CLI flag (`mctrader-cli risk kill --reason ...`) + file sentinel (`<artifacts>/risk_kill.signal`) 둘 다 지원
- RiskPolicy hash = sha256 over canonical JSON (Pydantic `model_dump_json(sort_keys=True)` 후 Decimal canonical)
- Run start lock = `_policy_hash` snapshot, runtime drift 감지 시 critical event
- mctrader-engine pyright/ruff 완화 baseline 동일 (MCT-22 패턴)
- pytest + Linux CI (engine), Windows lane = mctrader-data 만

## 7. 설계 서사 (Codex 7-area + Sonnet 합성)

### 7.1 End-to-end acceptance (A1 — 2 layer)

**Blocking AC** (Epic 종료 의무):

| # | AC | 검증 |
|---|---|---|
| B1 | 5 kill-switch (MAX_DAILY_LOSS / DRAWDOWN_LIMIT / CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL) 모두 enforce | pytest 5 fixture |
| B2 | reason_code 일관 — `<TRIGGER_NAME>:<reason_subkey>` 형식 (5 trigger × N reason) | RiskGateEvent.reason_code regex |
| B3 | first_trigger_ts + hard latch 5 trigger 모두 적용 (kill_switch.py 공통 mechanism) | pytest |
| B4 | ADR-007 D7 Recovery 3-tier flow — soft_stop 15min cooldown auto / hard_stop manual_ack `mctrader-cli risk ack --run-id ...` / critical_stop key_rotation 의무 | CLI integration test |
| B5 | ADR-007 D8 active_capital lock enforce — `gross_exposure / active_capital ≤ 1.0` block | pytest |
| B6 | ADR-007 D9 RiskPolicy hash + amendment_from + run-start freeze + drift detection | snapshot + pytest |
| B7 | RiskPolicy snapshot persistence — `mctrader-data/risk_policy_snapshot/run_id=.../policy.json` partition + ExecutionReport.metadata.policy_hash | mctrader-data writer test |
| B8 | RiskGateEvent schema extension — 5 kill-switch 공통 payload (`kill_switch_type / severity / reason_code / observed_value / threshold_value / first_trigger_ts / policy_hash / ack_required / ack_status`) | pydantic validator |
| B9 | ADR-007 D5 SL/TP guard — strategy decision 에 `intended_stop_loss_pct` 또는 `max_loss_krw` 의무, 없으면 violation event (block X, MCT-25 = soft) | pytest fixture |
| B10 | ADR-002 RiskGate Protocol check-only 보존 — `update()` 추가 X, internal stateful only | pyright + interface test |

**Calibration AC** (Paper 의 5 kill-switch baseline 수집):

| # | metric | 의미 | gate threshold |
|---|---|---|---|
| C1 | `kill_switch_trigger_frequency` | 7d Paper run 의 kill-switch 별 trigger 횟수 + first_trigger_ts 분포 | baseline only (재튜닝 별도) |

**Demonstration AC**:

| # | AC | 검증 |
|---|---|---|
| D1 | mctrader-web Streamlit dashboard 가 RiskGateEvent 5 kill-switch 시각화 = **MCT-31 분리** (MCT-25 = no UI) | manual review (defer) |

### 7.2 5 child Story 분해

```
              MCT-26 (foundation: policy versioning + active_capital lock)
              ┌────────┬────────┬────────┐
              ↓        ↓        ↓        ↓
          MCT-27   MCT-28   MCT-29   (MCT-26 후행, parallel 가능)
          (CONSEC.) (UNUSUAL) (EXT_SIG + Recovery)
              └────────┴────────┘
                       ↓
                   MCT-30 (D5 SL/TP + Calibration + E2E, 통합)
```

| Story | repo | 의존 |
|---|---|---|
| MCT-26 | mctrader-engine + mctrader-data | MCT-23 freeze (engine 0.3.0) |
| MCT-27 | mctrader-engine | MCT-26 freeze (RiskPolicy snapshot) |
| MCT-28 | mctrader-engine | MCT-26 freeze (parallel with 27) |
| MCT-29 | mctrader-engine | MCT-26 freeze (parallel with 27/28) |
| MCT-30 | mctrader-engine | MCT-27 + MCT-28 + MCT-29 freeze (E2E) |

**Parallel start 후보** = MCT-27 + MCT-28 + MCT-29 (MCT-26 freeze 후 동시 가능). MCT-30 = 통합 sealing.

### 7.3 RiskPolicy versioning + snapshot persistence (A1, MCT-26)

**채택**: canonical_json (Pydantic `model_dump_json(by_alias=False)` 후 Decimal string 표준 정렬) + sha256 hash + amendment_from chain.

```python
class RiskPolicy(BaseModel):
    # 기존 필드 보존 (MCT-22)
    max_daily_loss_hard_pct: Decimal
    drawdown_limit_hard_pct: Decimal
    active_capital_pct: Decimal
    active_capital_cap_krw: Decimal
    # 신규 (MCT-25)
    consecutive_losses_soft: int = 5
    consecutive_losses_hard: int = 7
    consecutive_losses_min_closed: int = 10
    unusual_reject_rate_soft: Decimal = Decimal("0.20")
    unusual_reject_rate_hard: Decimal = Decimal("0.40")
    unusual_data_stale_soft_seconds: int = 3
    unusual_data_stale_hard_seconds: int = 10
    unusual_window_minutes: int = 5
    unusual_min_sample: int = 20
    external_data_outage_soft_seconds: int = 30
    catastrophic_stop_pct: Decimal = Decimal("0.03")
    max_position_age_hours: int = 24
    price_gap_guard_pct: Decimal = Decimal("0.01")
    policy_version: str = "mct-25-v1"
    amendment_from: str | None = None  # 이전 policy_version (chain)

    def canonical_json(self) -> str: ...
    def hash(self) -> str: ...  # sha256(canonical_json)
```

**Snapshot persistence** (mctrader-data):
- `{root}/risk_policy_snapshot/run_id=.../policy.json` (canonical JSON + hash)
- ExecutionReport.metadata.policy_hash = run start 시 frozen value
- Drift detection = runtime check 가 hash mismatch → critical_stop event

**Run-time freeze**:
- run start 시 RiskPolicy.hash() = `_locked_hash` 저장
- check() 호출 시마다 현재 policy.hash() != _locked_hash → critical_stop emit + RiskGateBlocked
- amendment 는 신규 run_id 의무 (D9)

### 7.4 CONSECUTIVE_LOSSES (A2, MCT-27)

**채택**: closed trade ledger 기반.

```python
class ClosedTrade:
    entry_ts_utc: datetime
    exit_ts_utc: datetime
    realized_pnl_krw: Decimal
    is_loss: bool  # realized_pnl < 0

def evaluate_consecutive_losses(
    *, recent_closed_trades: list[ClosedTrade],
    soft: int, hard: int, min_closed: int
) -> SwitchEvaluation:
    if len(recent_closed_trades) < min_closed:
        return pass
    streak = count_trailing_losses(recent_closed_trades)
    if streak >= hard: return hard
    if streak >= soft: return soft
    return pass
```

**Closed trade 정의** (Codex risk pitfall):
- FILLED → exit (full close 또는 partial close 시 each fill)
- PARTIALLY_FILLED → cancel = 잔량 종료 시점 = closed
- cancel-only (no fill) = closed 아님 (no realized pnl)

**Why 신규 module `trade_ledger.py`**: VirtualPortfolio 는 cash + position state 만 추적 (realized_pnl 누적). 트레이드 단위 ledger 가 별도 의무 (FIFO matching).

### 7.5 UNUSUAL_ACTIVITY (A3, MCT-28)

**채택**: 5min rolling window + minimum sample.

```python
class ActivityWindow:
    window_minutes: int
    min_sample: int
    decisions: deque[DecisionRecord]
    fills: deque[FillRecord]
    rejects: deque[RejectRecord]
    
    def reject_rate(self, now: datetime) -> Decimal:
        sample = self._in_window(now)
        if len(sample) < min_sample:
            return Decimal("0")  # insufficient sample = pass
        return Decimal(reject_count) / Decimal(len(sample))
```

**5 sub-trigger** (ADR-007 D1):
- reject_rate > 20% (soft) / > 40% (hard)
- data_stale > 3s (soft) / > 10s (hard) — last_market_data_ts vs now
- duplicate client_order_id (hard, 1회)
- opposite orders/1s ≥ 3 (hard)
- balance_mismatch > 0.5% (hard) — paper 에서는 VirtualPortfolio invariant 검증으로 stub

**Paper-specific note**: paper 의 simulated reject 가 적음 → minimum sample 20 + fixture replay (test_unusual_activity.py 가 reject sequence injection).

### 7.6 EXTERNAL_SIGNAL + Recovery 3-tier (A4, MCT-29)

**채택**: dual interface (CLI flag + file sentinel) + 3-tier transition state machine.

**EXTERNAL_SIGNAL trigger**:
- CLI: `mctrader-cli risk kill --run-id <id> --reason <txt>` → write `<artifacts>/risk_kill.signal` (JSON: {ts, reason, trigger="manual"})
- File sentinel watch: enforcer 가 매 check() 시 `risk_kill.signal` 존재 확인
- data_outage 30s = MarketStream 의 last_message_ts vs now > 30s (Paper 환경 = WebSocket disconnect duration)
- API ban / key compromise = Paper 에서는 simulation 가능 (config flag 또는 fixture inject), Live Epic 에서 broker error code 매핑

**ADR-008 D5 align**: Paper 에서는 broker API 호출 X. EXTERNAL_SIGNAL 의 manual_kill / API_ban / key_compromise 모두 file/config sentinel 또는 fixture 만.

**Recovery 3-tier**:
```
soft_stop  → 15min cooldown + health_check pass 5min → auto resume (D7 tier 1)
hard_stop  → operator_ack (CLI: mctrader-cli risk ack --run-id X)
              + risk_snapshot_reconciled
              + open_orders_reconciled (Paper = 모든 open simulated order cancel)
              + positions_reconciled (VirtualPortfolio invariant pass)
              + ≥30min cooldown
              + risk_policy_hash unchanged
              → manual resume (D7 tier 2)
critical_stop → manual ack + key_rotation (Paper 에서는 stub: --confirm-key-rotation flag)
              → 별도 key_rotation 후 신규 run (D7 tier 3)
```

**같은 날 hard_stop 2회** = 다음 daily reset 후 manual override 의무 = state field `_hard_stop_count_today`.

**Recovery 첫 1h reduced mode** (Paper 에서는 stub field — Live Epic 에서 본격 enforce):
- ExecutionReport summary 에 `recovery_reduced_mode_until_ts` 기록만

### 7.7 ADR-007 D5 SL/TP guards (A5, MCT-30)

**RiskGate 의무**:
- `intended_stop_loss_pct` 또는 `max_loss_krw` strategy decision metadata 의무 (없으면 soft severity, MCT-25 = soft only — strategy migration 부담 회피)
- `catastrophic_stop` = entry -3% 또는 position notional -1.0× active_capital → hard event
- `max_position_age` = 24h → hard event (position age 추적)
- `price_gap_guard` = mid 대비 1.0% 이상 불리 → hard event (orderbook mid_price vs intended order price)

**Strategy 위임** (RiskGate 미강제):
- TP 부재 = violation 아님
- SL trailing / time-based = strategy 책임. catastrophic_stop = floor.

### 7.8 RiskGateEvent schema extension (A6)

**현재 ADR-004 RiskGateEvent**:
```python
class RiskGateEvent(BaseModel):
    ts_utc: datetime
    trigger: str
    severity: Severity
    reason: str
```

**MCT-25 extension**:
```python
class RiskGateEvent(BaseModel):
    ts_utc: datetime
    kill_switch_type: TriggerName  # 5 enum
    severity: Severity  # pass/soft/hard/critical (D7 추가)
    reason_code: str  # "<TRIGGER>:<subkey>" 형식
    observed_value: Decimal | str | None
    threshold_value: Decimal | str | None
    first_trigger_ts_utc: datetime | None
    policy_hash: str
    policy_version: str
    ack_required: bool
    ack_status: Literal["none", "pending", "acked", "rotated"] | None
```

**Backward compat**: ADR-004 RiskGateEvent v1 → v2 migration. v1 fields (`trigger`, `reason`) = computed property (legacy reader compat). Pydantic field alias.

### 7.9 Out-of-scope (확정 거부)

| 항목 | MCT-25 미포함 | 이유 |
|---|---|---|
| ADR-007 D3 Exposure (gross / single_order_notional / symbol_concentration / KRW_cash_min / per-side bias) | ✗ | kill-switch 가 아니라 별도 risk domain. 별도 Epic |
| ADR-007 D4 Order rate limit (2/sec, 20/min, 300/day 등) | ✗ | pre-trade throttle, kill-switch 아님. 별도 Epic |
| ADR-007 D10 Personal-platform threshold table 전체 catalog | ✗ | MCT-25 = PaperRiskGate threshold 만 고정 |
| Strategy peak (D2 strategy axis) + rolling 24h drawdown | ✗ | portfolio peak 만 enforce (MCT-22 baseline 보존) |
| WFO-based threshold 재튜닝 | ✗ | C1 baseline 수집만, 재튜닝 별도 Epic |
| Streamlit RiskGateEvent dashboard | ✗ | MCT-31 분리 |
| Multi-symbol portfolio risk (correlation / concentration) | ✗ | single-symbol baseline 보존 |
| Live mode integration | ✗ | 별도 Epic (1Password CLI Secret + GitHub environment protection 의무) |
| Production-grade operator console (web ack UI) | ✗ | CLI ack 만 |
| RiskPolicy migration script (legacy v1 → v2) | ✗ | run-id 단위 신규 lock, 기존 run 영향 X |

### 7.10 CFP-60 debut-audit checklist

각 child Phase 2 merge 직후:
- **lane-progression** (B→P→L 의 RiskGate 5/5 enforce evidence)
- **decision-table** (5 kill-switch threshold 결정 표 + amendment chain)
- **workflow-invariant** (ADR-008 D5 secret 금지 — EXTERNAL_SIGNAL manual_kill 도 file sentinel)
- **contract-schema** (RiskGateEvent v2 migration + RiskPolicy snapshot partition)

### 7.11 Phase 1 / Phase 2 분담

**Phase 1** (본 Epic Story):
- 본 Epic doc + 5 child stub (MCT-26 ~ MCT-30) registration
- AC freeze (B1~B10 + C1 + D1)
- Out-of-scope 명시
- reason_code taxonomy 결정 (`<TRIGGER>:<subkey>` 형식)
- Recovery 3-tier state transition diagram
- Cross-repo source of truth (RiskPolicy snapshot = mctrader-data)
- CFP-60 debut-audit checklist
- Phase 1 PR

**Phase 2** (child Story PR):
- 5 신규 issue Phase 1 brainstorm + Phase 2 implementation
- 각 child = Codex 7-area review → Sonnet 합성 → Story doc → PR

### 7.12 Codex 적용

7/7 area 채택. ADR conflict 0/7 (D3 Exposure / D4 Order rate / D10 catalog 전체 deferred = no ADR-007 conflict, 향후 별도 Epic 으로 보완).

## 8-11

(Phase 2 = 5 child Story PR 분담. 본 Epic Story 자체는 doc-only.)
