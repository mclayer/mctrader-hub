---
story_key: MCT-58
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-006
---

# MCT-58: OOS evaluator + 12-metric AND gate D6 + canonical fold report

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-006 D6 (12-metric AND promotion gate B→P) + D11 (fold report 6 field canonical) + D12 (Sharpe CI Newey-West / block bootstrap). Codex push-back: "D6/D7 gate computation should be implemented and tested in MCT-58 before promotion writes anything (MCT-62)".

## 2. 도메인 해석

MCT-55 child #3. MCT-57 가 생성한 selected_param 으로 OOS fold metric 평가 + gate 결과 산출 + canonical fold report.

```
mctrader-cli wfo evaluate \
  --decision-group {registry_hash}
```

→ fold-level metric × N folds + Sharpe CI (Newey-West HAC + block bootstrap) + 12-metric AND gate D6 결과 + `fold_report.json` (D11 canonical 6 field).

본 Story 종료 시 `fold_report.json.gate_d6.passed: bool` + `gate_d6.failed_metrics: list[str]` 명확.

## 3. 관련 ADR

- ADR-006 D6 (12-metric AND gate) / D11 (median + IQR + worst + recent N + probability of loss + CI) / D12 (Sharpe CI 의무) / amendment §D11 (fold_report.json canonical 6 field freeze)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/wfo/
├── evaluator/                (NEW submodule)
│   ├── __init__.py
│   ├── fold_metric.py        (fold-level metric 계산)
│   ├── sharpe_ci.py          (Newey-West HAC + block bootstrap)
│   ├── gate_d6.py            (12-metric AND gate 평가)
│   └── fold_report.py        (D11 canonical schema writer)
└── cli.py                    (MODIFY — wfo evaluate subcommand)
```

## 5-6. 요구사항

1. fold-level metric 계산 — N fold 각각: total_return / Sharpe / Sortino / Calmar / MDD / trade_count / cost-included expectancy / turnover / slippage drift.
2. Sharpe CI (E3-lite) — Newey-West HAC primary (lag = candle frequency 기반) + block bootstrap report-only (block size = sqrt(N)). 둘 차이가 threshold 초과 시 fail-fast.
3. 12-metric AND gate D6 (per ADR-006 D6 표):
   - manifest replay decision match = 100% exact
   - scalar metric drift < 1% relative
   - 최근 3 OOS fold violation = 0
   - OOS MDD ≤ 20% (strategy budget)
   - OOS Sharpe ≥ 0.8 (CI 하한 > 0 권장)
   - OOS Sortino ≥ 1.0 / Calmar ≥ 0.5
   - profitable OOS folds ≥ 60%
   - val→OOS Sharpe decay ≤ 50%
   - trade count / fold ≥ 30
   - 비용 포함 expectancy > 0
   - parameter fold variance band 내
4. canonical `fold_report.json` (D11 amendment §D11) — 6 field per metric: median / IQR / worst / recent N / probability of loss / CI. Mean-only 보고 코드에서 명시 거부.
5. `gate_d6` 결과 = `passed: bool` + `failed_metrics: list[str]` + `metric_values: dict[str, ...]` Pydantic v2 strict.
6. `oos_evaluated` audit event emit + `fold_report.json` save → `~/.mctrader/wfo/decision_groups/{hash}/fold_report.json`.
7. CLI: `mctrader-cli wfo evaluate --decision-group X` → fold_report.json + audit event.
8. Unit test: Sharpe CI determinism / gate D6 12-metric AND / canonical schema strict / D11 6 field 모두 populated / mean-only fail-fast.
9. CI green.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: 적재 OHLCV only.
- 신규 file: `wfo/evaluator/` 5 file + tests.
- 수정 file: `cli.py` wfo evaluate, version bump engine 0.18.0 → 0.19.0.
- Reversible: yes.
