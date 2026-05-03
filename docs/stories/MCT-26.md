---
story_key: MCT-26
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-25
related_adrs: ADR-007, ADR-002, ADR-004, ADR-009
---

# MCT-26: RiskPolicy versioning + snapshot persistence + active_capital lock enforce (foundation)

## 1. 사용자 요구사항 (verbatim, MCT-25 Epic)

> "MCT-25 foundation — D9 RiskPolicy versioning (canonical_json + hash + amendment_from + run-time freeze) + D8 active_capital lock enforce + RiskPolicy snapshot persistence (mctrader-data partition)"

## 2. 도메인 해석

mctrader-engine 0.3.0 RiskPolicy (MCT-22 도입) 의 D9 versioning 정식화. 현재는 `policy_version: str = "mct-22-v1"` 만 존재하고 hash / amendment_from / run-time freeze / snapshot persistence 없음. MCT-25 의 5 child Story 모두가 이 freeze + snapshot 기반으로 동작해야 하므로 foundation 위치.

## 3. 관련 ADR

- ADR-007 D8 (active_capital lock enforce, 현재 metric only)
- ADR-007 D9 (Risk policy versioning, canonical_json + hash + amendment_from)
- ADR-002 (RiskGate Protocol check-only 보존)
- ADR-004 (ExecutionReport.metadata.policy_hash + RiskGateEvent v2 schema)
- ADR-009 (mctrader-data partition extension — risk_policy_snapshot/run_id=...)
- 의존: MCT-23 freeze (engine 0.3.0)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/risk/
├── policy.py (extend)              # canonical_json + hash + amendment_from
├── policy_snapshot.py (NEW)        # run-start lock + drift detection
└── enforcer.py (extend)            # active_capital exposure check (D8)

mctrader-data/src/mctrader_data/
└── risk_snapshot.py (NEW)          # snapshot partition writer
```

## 5-6. 요구사항

- canonical_json = Pydantic `model_dump_json` + Decimal string 표준 정렬 + sort_keys
- hash = sha256(canonical_json.encode("utf-8"))
- run-start lock: `_locked_hash` 저장, runtime drift 감지 시 critical_stop event
- snapshot partition: `{root}/risk_policy_snapshot/run_id=.../policy.json`
- D8 active_capital exposure: `gross_exposure = sum(position_notional)` ≤ `active_capital` block

## 7. 설계 서사 (Codex 합성 — Phase 2 시점에 구체화)

### 7.1 RiskPolicy.canonical_json + hash (A1)

Decimal field 의 canonical 표현 = `str(Decimal("0.03"))` ("0.03"). Pydantic `model_dump_json` 의 Decimal serialization 이 quantize 결정 의존하므로 명시 quantize 의무. sort_keys 강제.

### 7.2 RiskPolicySnapshot (A2)

```python
@dataclass(frozen=True)
class RiskPolicySnapshot:
    run_id: str
    policy_version: str
    policy_hash: str
    canonical_json: str
    locked_at_utc: datetime
    amendment_from: str | None

    def verify_runtime(self, current_policy: RiskPolicy) -> None:
        if current_policy.hash() != self.policy_hash:
            raise PolicyDriftError(...)
```

### 7.3 active_capital lock enforce (A3)

PaperRiskGate.check() 에 추가:
```python
gross_exposure = portfolio_state.gross_exposure  # NEW field, sum of position notional
if gross_exposure > active_capital:
    raise RiskGateBlocked(
        trigger="ACTIVE_CAPITAL_LOCK",
        reason=f"gross_exposure={gross_exposure} > active_capital={active_capital}"
    )
```

PortfolioState extension: `gross_exposure: Decimal` 추가 (mark_to_market 시 계산).

### 7.4 mctrader-data risk_snapshot.py (A4)

```python
def write_risk_policy_snapshot(
    snapshot: RiskPolicySnapshot, *, root: Path
) -> Path:
    target = root / "risk_policy_snapshot" / f"run_id={snapshot.run_id}" / "policy.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({...}, sort_keys=True))
    return target
```

ADR-009 16-column 무관 (별도 partition). Hive-style.

### 7.5 ExecutionReport metadata 확장 (A5)

`ExecutionReport.metadata.policy_hash` + `policy_version` + `amendment_from` 추가. Backward compat = optional fields.

### 7.6 Out-of-scope

- D9 amendment lifecycle automation (manual ack 의무)
- migration script (legacy run-id 영향 X)

### 7.7 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | RiskPolicy.canonical_json + hash deterministic |
| AC2 | RiskPolicySnapshot run-start lock |
| AC3 | runtime drift 감지 → PolicyDriftError + critical_stop event |
| AC4 | active_capital lock enforce — gross_exposure > active_capital block |
| AC5 | PortfolioState.gross_exposure 계산 (mark_to_market) |
| AC6 | mctrader-data risk_policy_snapshot partition writer |
| AC7 | ExecutionReport.metadata.policy_hash + policy_version + amendment_from |
| AC8 | 5 required check green |

### 7.8 Codex 적용

7/7 채택 (Phase 2 시점에 detail review). ADR conflict 0/7.

## 8-11

(Phase 2 = risk/policy.py + policy_snapshot.py + enforcer.py + mctrader-data risk_snapshot.py.)
