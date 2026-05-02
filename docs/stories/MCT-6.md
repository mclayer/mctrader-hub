---
story_key: MCT-6
status: phase:요구사항
component: backtest
type: brainstorm
related_adr: ADR-006
---

# MCT-6: Walk-forward / OOS 검증 protocol + Promotion gate threshold

## 1. 사용자 요구사항 (verbatim)

mctrader 의 Walk-forward / Out-of-sample 검증 protocol. ADR-002 D7 (\"replay + shadow + metric comparison + promotion gate\") + ADR-003 H8 (WFO runner = self-built) + ADR-005 path (d) (OOS optimization governance) 의 구체화.

## 2. 도메인 해석

ADR-002 / ADR-003 / ADR-005 의 baseline 위에 fold split scheme + window default + parameter selection + OOS governance + promotion gate threshold + multiple testing correction 박제.

핵심 invariant (Codex 강조): \"OOS 는 성과를 높이는 도구가 아니라 이미 정한 결정을 검증하는 봉인된 증거\".

## 3. 관련 ADR

- ADR-006 ([`../adr/ADR-006-walk-forward.md`](../adr/ADR-006-walk-forward.md))
- baseline: ADR-002 D7 / ADR-003 H8 / ADR-005 path (d)
- 향후: MCT-7 (Risk gate threshold — 본 ADR promotion gate 의 risk violation criterion 의존)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader/
├── runner/
│   ├── walk_forward.py       # WFO runner (self-built, fold 마다 backtest engine 호출)
│   ├── split_registry.py     # SplitRegistry + hash + freeze lifecycle
│   └── manifest.py           # run manifest schema (decision reproducibility)
├── selection/
│   ├── rank_aggregation.py   # top-K rank consensus
│   └── hard_filter.py        # trade count / MDD / risk / expectancy
├── governance/
│   ├── audit_log.py          # OOS read access audit
│   ├── promotion_gate.py     # Backtest→Paper / Paper→Live multi-metric AND
│   └── multiple_testing.py   # deflated Sharpe / FDR
└── reporting/
    └── fold_report.py        # fold table (median + IQR + worst + recent + CI)
```

## 5-6. 요구사항 / 외부 지식

학술 reference: Bailey & López de Prado (purging/embargo, deflated Sharpe), White's Reality Check, Hansen SPA, Lo modified Sharpe (autocorrelation), Bergstra & Bengio (random vs grid). Crypto 24/7 시장 = traditional WFO 와 다름 (no weekend gap).

## 7. 설계 서사 (요약)

### 7.1 WFO scheme = Rolling baseline

**Rolling**: 고정 길이 training window 앞으로 전진. Crypto regime 빠른 변화에 적응성. Production promotion default.

**Anchored / Expanding**: 보조 진단 (장기 사이클 / 추세 전략).

**Time-series K-fold (purged + embargo)**: 연구용 비교만.

### 7.2 Window default per timeframe

| Candle | Lookback | Training | Validation | OOS | Embargo |
|---|---:|---:|---:|---:|---:|
| 5m | 1-2년 | 90일 | 14일 | 14일 | 1-2일 |
| 15m | 1-3년 | 120일 | 21일 | 21일 | 2일 |
| 1h | 2-4년 | 180일 | 30일 | 30일 | 3-5일 |
| 4h | 3-5년 | 365일 | 60일 | 60일 | 7일 |
| 1d | 5년 이상 권장 | 730일 | 90일 | 90-180일 | 14-30일 |

Embargo = label overlap + 지표 warmup + order fill latency + selection contamination 방지. Multi-timeframe 전략 = 가장 느린 TF 의 warmup + holding period 기준.

신규 상장 종목 = WFO promotion 금지 (paper-only). 알트코인 illiquid = 최소 6 OOS fold 미만 = exploratory only.

### 7.3 Parameter selection = top-K rank consensus

```
Hard filter (제거):
  - trade count 부족
  - MDD 초과
  - risk violation 발생
  - 비용 포함 expectancy ≤ 0

Composite rank = rank aggregation:
  - validation Sharpe rank
  - Sortino rank
  - Calmar rank
  - MDD inverse rank
  - turnover penalty rank
  - slippage drift rank

Top-K = 5 (default). 최종 = median 또는 cluster centroid.
연속형 = trimmed mean / 범주형 = majority vote.
```

**Single best Sharpe selection 금지** (가장 흔한 overfitting). Weighted score = dashboard only, promotion 판정 금지.

### 7.4 Search budget per (strategy, symbol_group, timeframe)

- Random 100 trials = baseline
- Bayesian (TPE / GP) 50-100 trials = 제한적 사용
- Grid 3-5 핵심 축 coarse only
- 1000 trials = stress test only (multiple testing correction + untouched OOS registry 의무)

### 7.5 OOS governance = split registry + hash + audit + freeze

`SplitRegistry`: dataset_id + symbol_universe + timeframe + fold_boundary + train/val/OOS interval + embargo + feature_warmup + label_horizon + 생성 코드 버전 + registry_hash.

**Hash = audit / 사후 재현성, security boundary 아님**. 실질 방어:
- registry freeze (decision group 시작 전 1회만 생성, 재생성 = 새 decision group)
- promotion report = 같은 strategy_family 의 모든 decision_group nominate
- monotonic run sequence + audit log append-only

Audit log events:
```
split_registry_created / fold_materialized
train_segment_read / validation_segment_read / oos_segment_read
candidate_generated / candidate_selected
oos_evaluated / promotion_decision_created
```

각 event = run_id + actor + git_commit + data_snapshot_hash + code_hash + config_hash + split_registry_hash + fold_id + access_scope + timestamp.

ADR-005 D2 L4 fixture `known_bias_oos_selection_loop` fail mechanism = **lineage violation** (selected_param_hash 가 OOS-evaluated candidate 에 연결 시 fail).

### 7.6 Promotion gate Backtest → Paper

| Category | Metric | Threshold |
|---|---|---:|
| Reproducibility | manifest 재실행 decision match | 100% |
| Reproducibility | scalar metric drift (PnL/Sharpe/MDD) | 상대 오차 < 1% |
| Risk | 최근 3 OOS fold violation | 0 |
| Risk | OOS MDD | ≤ strategy budget (default 20%) |
| Performance | OOS Sharpe | ≥ 0.8 (CI 하한 > 0 권장) |
| Performance | OOS Sortino | ≥ 1.0 |
| Performance | OOS Calmar | ≥ 0.5 |
| Robustness | profitable OOS folds | ≥ 60% |
| Robustness | validation→OOS Sharpe decay | ≤ 50% |
| Trading | trade count / fold | ≥ 30 (또는 strategy 사전 기준) |
| Cost | 비용 포함 expectancy | > 0 |
| Stability | parameter fold variance | 사전 정의 band 내 |

**Multi-metric AND gate**. Risk + reproducibility = hard AND. Performance = AND with tolerance. Weighted score 금지.

### 7.7 Promotion gate Paper → Live

| Category | Metric | Threshold |
|---|---|---:|
| Duration | min period | 30일 OR 100 trades (later) |
| Reproducibility | paper vs replay decision | 100% (or explainable external diff) |
| Risk | 최근 30일 violation | 0 |
| Drift | slippage drift | median ≤ 5 bps, p95 ≤ 20 bps |
| Drift | fill rate drift | ≤ 10% degradation |
| Orders | rejection rate | < 1% |
| Orders | cancel/replace error | < 0.5% |
| Performance | Paper Sharpe | ≥ 50% of Backtest OOS Sharpe OR ≥ 0.5 |
| Drawdown | Paper MDD | ≤ 1.25× expected OOS MDD |
| Latency | signal-to-order | p95 ≤ strategy SLA |
| Shadow | live shadow comparison | 0 critical mismatch, < 1% non-critical |

Live 첫 진입 = 기본 allocation 의 10-25% (limited capital live + ramp-up gate).

### 7.8 Multiple testing correction

3 단계:
1. 동일 family candidate 수 기록 + deflated Sharpe / bootstrap reality check
2. Strategy family 간 병렬 테스트 = FDR (false discovery rate) 보고
3. 최종 promotion 후보 = frozen registry untouched OOS 또는 paper phase 재확인

**Bonferroni** 지나치게 보수적 — FDR 권장. Correction 은 나쁜 설계 구제 안 함 — manifest 에 hypothesis + search space 사전 freeze 가 우선.

### 7.9 Regime conditional = ex-ante rule only

허용:
- BTC 90일 realized volatility tercile
- BTC 200일 MA 대비 위치
- KRW premium z-score
- realized volatility / drawdown state / liquidity z-score

**금지**: \"이 구간은 FUD 였으니 제외\" (post-hoc narrative overfitting).

배포 전 deterministic calendar event (e.g. BTC halving 예정일) = regime metadata 허용.

### 7.10 Run manifest schema (decision reproducibility 계약)

```python
@dataclass(frozen=True)
class RunManifest:
    run_id: str
    decision_group_id: str
    strategy_id: str
    strategy_family_id: str
    git_commit: str
    code_hash: str
    container_hash: str
    data_snapshot_id: str
    data_hash: str
    exchange: str
    symbol_universe: list[str]
    timeframe: str
    fee_model: dict
    slippage_model: dict
    split_registry_hash: str
    fold_ids: list[str]
    embargo: timedelta
    feature_warmup: timedelta
    label_horizon: timedelta
    search_algorithm: str
    search_budget: int
    search_space_hash: str
    random_seed: int
    candidate_count: int
    selection_rule: str
    selected_param_hash: str
    metric_schema_version: str
    risk_policy_hash: str
    promotion_gate_version: str
    audit_log_hash: str
    created_at: datetime
    actor: str
```

이 manifest 없는 성과 = 연구 노트만, promotion 근거 아님.

### 7.11 Fold report

각 fold: train/val/OOS 기간 + selected_param_hash + validation rank + OOS Sharpe/Sortino/Calmar/MDD/hit rate/trade count/turnover/slippage + risk violation + parameter cluster id.

Aggregate: 평균 + **median + IQR + worst fold + recent N + probability of loss + confidence interval**. **평균 단독 보고 금지**.

### 7.12 Codex 적용 결과

채택률 16/16. Sonnet 거부 0.

## 8-11

(Phase 2 N/A — doc-only Story.)
