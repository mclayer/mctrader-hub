---
adr_id: ADR-006
title: Walk-forward / OOS 검증 protocol + Promotion gate threshold
status: Accepted
date: 2026-05-02
related_story: MCT-6
category: backtest
---

# ADR-006: WFO + OOS governance + Promotion gate

## Status

Accepted — 2026-05-02. MCT-6 Phase 1 PR.

## Context

ADR-002 D7 / ADR-003 H8 / ADR-005 path (d) 의 구체화. WFO scheme + window default + parameter selection + OOS governance + promotion threshold + multiple testing correction.

핵심 invariant: \"OOS = 봉인된 증거. 성과 도구 아님\".

## Decision

### D1. WFO scheme = Rolling baseline

- **Rolling**: production default. Crypto regime 변화 빠름.
- **Anchored / Expanding**: 보조 진단.
- **Time-series K-fold (purged + embargo)**: 연구용 비교만.

### D2. Window default

| Candle | Training | Validation | OOS | Embargo |
|---|---:|---:|---:|---:|
| 5m | 90일 | 14일 | 14일 | 1-2일 |
| 15m | 120일 | 21일 | 21일 | 2일 |
| 1h | 180일 | 30일 | 30일 | 3-5일 |
| 4h | 365일 | 60일 | 60일 | 7일 |
| 1d | 730일 | 90일 | 90-180일 | 14-30일 |

기본 profile = 1h. 신규 상장 종목 = WFO promotion 금지. illiquid = 최소 6 OOS fold 미만 시 exploratory only.

Multi-timeframe = slowest TF warmup + holding period 기준 embargo. multi-asset/multi-strategy = split registry 의 calendar boundary 공유 + survivorship bias 방지 (당시 universe 보존).

### D3. Parameter selection = top-K rank consensus

```
Hard filter:
  trade count 부족 / MDD 초과 / risk violation / 비용 후 expectancy ≤ 0  → reject

Composite rank = rank aggregation (Sharpe / Sortino / Calmar / MDD inverse / turnover / slippage drift)

Top-K (default 5)
final param = median (연속형 trimmed mean / 범주형 majority vote / cluster centroid)
```

**Single best Sharpe selection 금지**. Weighted score = dashboard only.

### D4. Search budget per (strategy, symbol_group, timeframe)

- Random 100 trials = baseline
- Bayesian (TPE / GP) 50-100 trials = 제한적
- Grid 3-5 axes coarse only
- 1000 trials = stress test (multiple testing + untouched OOS registry 의무)

### D5. OOS governance

`SplitRegistry`:
```python
@dataclass(frozen=True)
class SplitRegistry:
    dataset_id: str
    symbol_universe: list[str]
    timeframe: str
    fold_boundaries: list[FoldBoundary]
    embargo: timedelta
    feature_warmup: timedelta
    label_horizon: timedelta
    code_version: str
    created_at: datetime
    registry_hash: str
    frozen_at: datetime | None  # freeze lifecycle marker
```

**Hash = audit, security boundary 아님**.

실질 방어:
- registry freeze (decision group 시작 전 1회 생성, 재생성 = 새 decision group)
- promotion report = strategy_family 의 모든 decision_group 나열
- monotonic run sequence + audit log append-only

Audit events: `split_registry_created` / `fold_materialized` / `train|validation|oos_segment_read` / `candidate_generated` / `candidate_selected` / `oos_evaluated` / `promotion_decision_created`.

OOS read 후 같은 decision group 내 selection event 발생 = violation. **selected_param_hash lineage 가 OOS-evaluated candidate 와 연결 시 fail** (ADR-005 L4 fixture mechanism).

### D6. Promotion gate Backtest → Paper

| Category | Metric | Threshold |
|---|---|---:|
| Reproducibility | manifest replay decision match | 100% (exact) |
| Reproducibility | scalar metric drift | 상대 오차 < 1% |
| Risk | 최근 3 OOS fold violation | 0 |
| Risk | OOS MDD | ≤ 20% (strategy budget) |
| Performance | OOS Sharpe | ≥ 0.8 (CI 하한 > 0 권장) |
| Performance | OOS Sortino | ≥ 1.0 |
| Performance | OOS Calmar | ≥ 0.5 |
| Robustness | profitable OOS folds | ≥ 60% |
| Robustness | val→OOS Sharpe decay | ≤ 50% |
| Trading | trade count / fold | ≥ 30 |
| Cost | 비용 포함 expectancy | > 0 |
| Stability | parameter fold variance | band 내 |

**Multi-metric AND gate**. Order sequence / position state / risk violation = exact match (drift 허용 안 함).

### D7. Promotion gate Paper → Live

| Category | Metric | Threshold |
|---|---|---:|
| Duration | min period | 30일 OR 100 trades (later) |
| Reproducibility | paper vs replay | 100% (or explainable external diff) |
| Risk | 최근 30일 violation | 0 |
| Slippage drift | median / p95 | ≤ 5 / 20 bps |
| Fill rate drift | degradation | ≤ 10% |
| Order rejection rate | | < 1% |
| Cancel/replace error | | < 0.5% |
| Performance | Paper Sharpe | ≥ 50% of Backtest OOS OR ≥ 0.5 |
| Drawdown | Paper MDD | ≤ 1.25× expected |
| Latency p95 | | ≤ strategy SLA |
| Shadow | critical mismatch | 0 |
| Shadow | non-critical mismatch | < 1% |

Live 첫 진입 = 기본 allocation 10-25% (limited capital + ramp-up gate).

### D8. Multiple testing correction

```
Layer 1: 동일 family candidate count 기록 → deflated Sharpe / bootstrap reality check
Layer 2: family 간 병렬 = FDR (false discovery rate)
Layer 3: 최종 promotion = frozen registry untouched OOS OR paper phase 재확인
```

**FDR 권장 (Bonferroni 보수적). Correction 은 hypothesis freeze 의 보조**.

### D9. Regime conditional = ex-ante rule only

허용:
- realized volatility tercile / SMA position / KRW premium z-score / drawdown state / liquidity z-score
- deterministic calendar event (BTC halving 예정일) = metadata

**금지**: post-hoc narrative ("이 구간 FUD 였음").

### D10. Run manifest schema (decision reproducibility 계약)

`run_id` / `decision_group_id` / `strategy_id` / `strategy_family_id` / `git_commit` / `code_hash` / `container_hash` / `data_snapshot_id` / `data_hash` / `exchange` / `symbol_universe` / `timeframe` / `fee_model` / `slippage_model` / `split_registry_hash` / `fold_ids` / `embargo` / `feature_warmup` / `label_horizon` / `search_algorithm` / `search_budget` / `search_space_hash` / `random_seed` / `candidate_count` / `selection_rule` / `selected_param_hash` / `metric_schema_version` / `risk_policy_hash` / `promotion_gate_version` / `audit_log_hash` / `created_at` / `actor`

Manifest 없는 성과 = 연구 노트만, promotion 근거 아님.

### D11. Fold report

각 fold: train/val/OOS 기간 + selected_param_hash + rank + OOS metric set + risk violation + cluster id.

Aggregate: median + IQR + worst + recent N + probability of loss + CI. **평균 단독 보고 금지**.

### D12. Sharpe CI / autocorrelation

Crypto intraday = trade outcome 비-독립 + volatility clustering. Newey-West / block bootstrap CI 권장. naive annualized Sharpe 과장.

## Alternatives Considered

### A1. Single best validation Sharpe selection
- **기각**: 가장 흔한 overfitting. Top-K rank consensus 의무.

### A2. Anchored/Expanding WFO baseline
- **기각**: oldest regime 잔상 누적. Crypto 부적합. 보조 진단만.

### A3. Bonferroni correction
- **기각**: 지나치게 보수적. FDR 채택.

### A4. Post-hoc regime label
- **기각**: narrative overfitting.

### A5. Weighted score promotion gate
- **기각**: 치명적 risk metric 이 수익률에 묻힘. Multi-metric AND 의무.

### A6. Hash 보안 token (cherry-pick 방지)
- **기각**: hash 비밀성 = 만능 아님. 실질 방어 = freeze + decision group lifecycle.

### A7. 평균 metric 단독 보고
- **기각**: median / IQR / worst / CI 미보고 = sample variance 은닉.

## Consequences

### C1. SplitRegistry + audit log = backtest infra 일부
backtest engine 호출 시 fold_id + access_scope 필수.

### C2. Run manifest 없는 backtest = 연구 노트
promotion 근거로 사용 금지.

### C3. Live 첫 진입 = limited capital + ramp-up
ADR-007 (Risk gate threshold) 의 max exposure / position size 와 연계.

### C4. CI / pre-commit
manifest schema validate / split registry freeze validate / audit log invariant validate.

### C5. MCT-7 / MCT-9 dependency
- MCT-7: risk violation criterion (D6 / D7 의 \"risk violation 0\")
- MCT-9: data_snapshot_id + data_hash schema

## Cross-references

- ADR-002 D7 / ADR-003 H8 / ADR-005 path (d)
- MCT-7 (risk gate) / MCT-9 (OHLCV schema)

---

## Amendment §D7 — Paper Promotion Evidence Bundle (MCT-48, 2026-05-04)

**Trigger**: MCT-48 (Paper Runtime Operations + Web Management) 가 Paper 의 product 목적을 명시 — "B→P→L 승격 evidence 생성". MCT-23 의 Calibration metric (`build_calibration_metrics`) 이 dashboard 표시 만 되었던 약점 정정 — calibration 결과가 promotion gate 의 mandatory input 으로 격상.

### D7. Paper Promotion Evidence Bundle 정의

Paper run 종료 시 또는 명령 시 (`mctrader-cli paper evidence --run-id {id}`) 생성되는 단일 JSON deliverable. P→L 승격 평가의 **유일한 authoritative input**.

#### Bundle schema (canonical)

```json
{
  "run_id": "string",
  "evaluation_window": {
    "start_ts": "ISO8601 UTC",
    "end_ts": "ISO8601 UTC",
    "duration_days": "Decimal"
  },
  "trade_count": "int",
  "violation_count": "int",
  "calibration": {
    "fill_price_deviation_p95_bps": "Decimal",
    "realized_slippage_p95_bps": "Decimal",
    "decision_to_fill_delay_p95_ms": "int",
    "market_data_latency_p95_ms": "int",
    "trade_count_delta_pct": "Decimal",
    "max_drawdown_delta_abs": "Decimal"
  },
  "risk_policy_hash": "string (sha256)",
  "promotable": "bool",
  "blocking_reasons": "list[string]"
}
```

#### Promotability threshold (AND)

| Threshold | 값 | source |
|---|---|---|
| `duration_days >= 30` OR `trade_count >= 100` | min sample | ADR-006 D2 (1h profile baseline) |
| `violation_count == 0` | RiskDecisionEvent severity in {hard, critical} = 0 | ADR-007 D1 |
| `calibration.fill_price_deviation_p95_bps < 20` | bps | MCT-32 v1 baseline |
| `calibration.realized_slippage_p95_bps < 15` | bps | ADR-004 D5 |
| `calibration.decision_to_fill_delay_p95_ms < 1000` | ms | ADR-008 latency naming |
| `calibration.market_data_latency_p95_ms < 3000` | ms | ADR-008 latency naming |
| `calibration.trade_count_delta_pct <= 0.10` | ratio (Paper vs Backtest replay) | MCT-23 C4 |
| `calibration.max_drawdown_delta_abs <= 0.02` | abs | MCT-23 C5 |

모든 threshold AND → `promotable: true`. 하나라도 fail → `promotable: false` + `blocking_reasons` list 명시.

#### Risk policy hash 고정 의무

평가 window 내 모든 RiskDecisionEvent 의 `risk_policy_hash` 가 동일해야 함. 변경 발견 시:
- `promotable: false`
- `blocking_reasons += ["risk_policy_hash_changed_during_window"]`

이 의무 = ADR-007 D9 RiskPolicy versioning 의 P→L 승격 측 강제.

### D8. Bundle 의 정책적 위치

- **Bundle 부재 = 승격 불가**. dashboard 표시 / CLI summary 등 derivative 표시는 bundle 의 input 또는 view 일 뿐, 승격 결정의 authoritative source 아님.
- **Bundle 의 `promotable: false` = 승격 불가**. operator override 절대 금지 (ADR-007 D7 manual ack 와 별개 — ack 는 RiskGate 재개, 승격 ≠ ack).
- **Bundle 재생성 가능**. event store (ADR-002 D6 SQLite append-only) 가 source-of-truth → 동일 input → 동일 output (deterministic).

### Cross-reference

- MCT-48 (Epic) / MCT-54 (Promotion Evidence Bundle 구현) — 본 amendment 의 검증 deliverable
- ADR-002 D6 (SQLite event store) — bundle 의 input source
- ADR-007 D9 (RiskPolicy hash) — bundle 의 hash 고정 dependency

---

## Amendment §D5 — SplitRegistry content-addressable storage 위치 freeze (MCT-55, 2026-05-04)

**Trigger**: MCT-55 (WFO Execution Epic) Phase 1 brainstorm 에서 Codex 7-area review push-back 채택. D5 의 SplitRegistry 가 immutable + audit hash 정합 의무이지만 ADR 본문 D5 에 저장 위치 freeze 부재 → 구현 별 분산 위험.

### 결정

`SplitRegistry` JSON 저장 위치 = **content-addressable hash directory**:

```
~/.mctrader/wfo/decision_groups/{registry_hash}/
├── registry.json           (SplitRegistry frozen Pydantic v2 model_dump_json)
├── audit_log.jsonl         (AuditEvent 8종 append-only)
├── manifests/              (per-run RunManifest JSON)
├── candidates/             (per-trial candidate metric snapshots)
├── fold_report.json        (MCT-58, D11 canonical 6 field)
├── correction_report.json  (MCT-59, deflated Sharpe + bootstrap reality)
└── promotion_decision.json (MCT-62, I2 manual ack 결과)
```

`registry_hash` = `sha256(canonical_json(SplitRegistry.model_dump_json + sort_keys + compact separators))`.

### 의무

- 동일 registry content → 동일 hash → 동일 directory (content-addressable 정합)
- registry 변경 = 새 hash = 새 directory = 새 decision_group (immutable enforce)
- 파일 권한 = 700 (`~/.mctrader/` family policy 일관, MCT-48 align)
- `~/.mctrader/wfo/` directory 미존재 시 첫 `wfo decision-group create` 진입 시 mode 0700 으로 자동 생성

### Cross-reference

- MCT-55 (Epic) / MCT-56 (Foundation Story) — 본 amendment 의 검증 deliverable

---

## Amendment §D10 — `promotion_gate_version` default value freeze (MCT-55, 2026-05-04)

**Trigger**: MCT-55 Phase 1 Codex push-back 채택. D10 run manifest 31-field 중 `promotion_gate_version` field 가 default value 없으면 promotion gate 변경 시 비교 불가 → "다른 gate 로 평가된 결과를 같은 metric 으로 비교" hazard.

### 결정

`promotion_gate_version` field default = **`"v1.0"`** (frozen).

### 의무

- 신규 RunManifest 작성 시 `promotion_gate_version` 명시 안 하면 default `"v1.0"` 적용
- D6 (B→P) gate threshold 변경 시 → 새 version (예: `"v1.1"`) 채택. 비교 시 동일 version 만 valid
- `promotion_decision.json` 에도 동일 field 기록 (MCT-62 PromotionDecision Pydantic v2)
- `v1.0` = ADR-006 D6 표 (12-metric AND, 2026-05-02 Accepted) snapshot. 이 표 변경 = 새 version

### Cross-reference

- MCT-55 (Epic) / MCT-58 (gate D6 evaluator) / MCT-62 (promotion CLI) — 본 amendment 의 검증 deliverable

---

## Amendment §D11 — `fold_report.json` canonical schema 6 field freeze (MCT-55, 2026-05-04)

**Trigger**: MCT-55 Phase 1 Codex push-back 채택. D11 본문 = "median + IQR + worst + recent N + probability of loss + CI" 권고. 그러나 canonical schema field name freeze 부재 → 구현 별 다른 field name 으로 보고 시 reproducibility 손상.

### 결정

`fold_report.json` canonical schema = **6 mandatory field per metric**:

```json
{
  "decision_group_hash": "string",
  "metric_name": "string",
  "median": "Decimal",
  "iqr": {"q1": "Decimal", "q3": "Decimal"},
  "worst": "Decimal",
  "recent_n": {"n": "int", "values": ["Decimal"]},
  "probability_of_loss": "Decimal",
  "confidence_interval": {"lower": "Decimal", "upper": "Decimal", "method": "newey_west"|"block_bootstrap"}
}
```

### 의무

- 6 field 모두 populated (null 금지). 한 metric 이라도 missing 시 schema validation fail.
- Mean-only 보고 = 코드 가드 함수에서 명시 거부 (MCT-58 code).
- `confidence_interval.method` = `"newey_west"` (primary) OR `"block_bootstrap"` (secondary), 양쪽 모두 보고 권장 (MCT-58 E3-lite Sharpe CI).
- D11 본문 "평균 단독 보고 금지" 의 코드 enforce.

### Cross-reference

- MCT-55 (Epic) / MCT-58 (fold report writer) — 본 amendment 의 검증 deliverable
