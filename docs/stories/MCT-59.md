---
story_key: MCT-59
status: closed
closed_at: 2026-05-05
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-006
results_doc: docs/EPIC-RESULTS-MCT-55.md
---

# MCT-59: Multiple testing correction full impl — deflated Sharpe + bootstrap reality check

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-006 D8 Layer 1 — deflated Sharpe (Bailey-López de Prado) + bootstrap reality check. Codex push-back: "F3 Both. FDR Benjamini-Hochberg 는 Layer 2 deferred (D8 명시 layering)".

MCT-57 의 `correction_hook.py` identity baseline 을 본격 구현으로 교체 + manifest layer integration.

## 2. 도메인 해석

MCT-55 child #4. MCT-58 의 fold metric 결과를 input → corrected metric → MCT-57 의 `correction_hook.apply_sharpe_correction()` body 채움.

핵심 invariant: "OOS = 봉인된 증거. 성과 도구 아님" (ADR-006 §Context). multiple testing correction = uncorrected ranking 결과를 신뢰성 검증 layer 로 변환.

## 3. 관련 ADR

- ADR-006 D8 (Layer 1: deflated Sharpe + bootstrap reality check / Layer 2: FDR / Layer 3: frozen registry untouched OOS)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/wfo/
├── correction/               (NEW submodule)
│   ├── __init__.py
│   ├── deflated_sharpe.py    (Bailey-López de Prado SR0)
│   ├── bootstrap_reality.py  (White's reality check)
│   └── search_space_hash.py  (manifest layer propagation)
├── search/correction_hook.py (MODIFY — identity → real impl)
└── cli.py                    (MODIFY — wfo evaluate option `--correction full`)
```

## 5-6. 요구사항

1. Deflated Sharpe (Bailey-López de Prado, 2014) — `SR0 = sqrt(2 ln(N))` baseline + skewness / kurtosis adjustment + sample size adjustment. v1 = formula 그대로, no new dep (numpy + scipy.stats 사용).
2. Bootstrap reality check (White, 2000) — N candidate 별 stationary block bootstrap (block_size = sqrt(T)) → max statistic distribution → p-value 계산.
3. `search_space_hash` propagation (D10) — `RunManifest.search_space_hash` 가 candidate count + parameter ranges + budget 모두 포함. correction 결과 에 manifest hash 첨부 (reproducibility).
4. `correction_hook.apply_sharpe_correction(trials, raw_sharpe) → adjusted_sharpe` body 채움. MCT-57 ranking 자동 적용.
5. `mctrader-cli wfo evaluate --correction full` flag — default OFF (MCT-58 기본 path 보존), flag 시 deflated Sharpe + bootstrap reality check + reported fold_report.json 에 `corrected_metrics` field 추가.
6. Unit test: deflated Sharpe formula 정확성 (Bailey 논문 reference value 비교) / bootstrap reality 결정성 (fixed seed) / search_space_hash determinism / correction_hook integration.
7. CI green.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: 적재 OHLCV only.
- 신규 file: `wfo/correction/` 4 file + tests.
- 수정 file: `cli.py` (--correction flag) / `wfo/search/correction_hook.py` body / `wfo/evaluator/fold_report.py` (corrected_metrics field), version bump engine 0.19.0 → 0.20.0.
- Reversible: yes.
