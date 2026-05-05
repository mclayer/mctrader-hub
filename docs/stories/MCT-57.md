---
story_key: MCT-57
status: closed
closed_at: 2026-05-05
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-006
results_doc: docs/EPIC-RESULTS-MCT-55.md
---

# MCT-57: Search engine + correction interface — Random 100 + Top-K rank consensus + deflated Sharpe ranking

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-006 D3 / D4 — Random 100 baseline (D4) + Top-K rank consensus (D3, single-best Sharpe selection 금지). Codex push-back: "deflated Sharpe interface 가 ranking-time 에 적용되어야 함, MCT-59 으로 미루면 uncorrected fold metric 으로 ranking → D3/D8 violation".

## 2. 도메인 해석

MCT-55 child #2. MCT-56 schema 의무 사용 (`SplitRegistry` + `RunManifest` + audit log). 본 Story 종료 시 사용자가:

```
mctrader-cli wfo search \
  --decision-group {registry_hash} \
  --budget 100 \
  --search-space ./params.yaml
```

→ Random 100 trials 실행 + Hard filter + composite rank + Top-K (default 5) + median selection + `candidate_selected` audit event.

deflated Sharpe interface = MCT-59 의 full impl 도입 전, ranking 함수에 sharpe_correction(trials, raw_sharpe) → adjusted_sharpe API hook. MCT-59 가 이 hook 내부 채움.

## 3. 관련 ADR

- ADR-006 D3 (Top-K rank consensus, single-best Sharpe 금지) / D4 (Random 100 baseline) / D8 (multiple testing layer 1)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/wfo/
├── search/                   (NEW submodule)
│   ├── __init__.py
│   ├── random_search.py      (Random 100 sampler)
│   ├── hard_filter.py        (trade count / MDD / risk violation / expectancy)
│   ├── composite_rank.py     (Sharpe/Sortino/Calmar/MDD inverse/turnover/slippage drift)
│   ├── top_k.py              (rank aggregation + median selection)
│   └── correction_hook.py    (deflated Sharpe interface, MCT-59 fills)
└── cli.py                    (MODIFY — wfo search subcommand)
```

## 5-6. 요구사항

1. Random 100 sampler — fixed seed (`RunManifest.random_seed`) + parameter space spec (yaml or pydantic).
2. Hard filter (D3): trade count < threshold / MDD > strategy budget / risk violation > 0 / cost-included expectancy ≤ 0 → reject (no rank participation).
3. Composite rank (D3): 6 metric (Sharpe/Sortino/Calmar/MDD inverse/turnover/slippage drift) rank aggregation. continuous = trimmed mean, categorical = majority vote, cluster = centroid.
4. Top-K (default K=5) + final param selection (median for continuous / majority for categorical / centroid for cluster).
5. Single-best Sharpe selection = code 에서 명시 거부 (가드 함수, weighted score = dashboard only).
6. deflated Sharpe interface — `correction_hook.py` 에 `apply_sharpe_correction(trials: list[Trial], raw_sharpe: float) → float` 정의. v1 = identity (MCT-59 가 본격 구현). hook 미적용 시 ranking warning emit.
7. CLI: `mctrader-cli wfo search --decision-group X --budget 100 --search-space FILE` → audit event `candidate_generated` × 100 + `candidate_selected` × 1.
8. Unit test: random sampler 결정성 / hard filter / composite rank 정합성 / Top-K median / correction_hook identity baseline.
9. CI green.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: search 는 적재 OHLCV only, no live API.
- 신규 file: `wfo/search/` 5 file + tests.
- 수정 file: `cli.py` wfo search, version bump engine 0.17.0 → 0.18.0.
- Reversible: yes.
