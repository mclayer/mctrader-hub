# Lookahead lint cross-repo policy (ADR-005 governance)

**Status**: Active — 2026-05-04 (mctrader-hub#? Epic MCT-37 close).

## Scope

ADR-005 D2 L1 (libcst static lint) 의 cross-repo scan 정책. 본 문서는 mctrader 6-repo 구조에서 lint tool 의 위치 + scan 대상 + 향후 확장 시점을 명시.

## 현 상태 (Epic MCT-37 종료 시점)

| Repo | Strategy / runtime 코드 보유 | Lookahead lint scan 대상 | Severity |
|---|---|---|---|
| mctrader-hub | ❌ (doc-only) | ❌ | — |
| mctrader-market | ❌ (Protocol) | ❌ | — |
| mctrader-market-bithumb | ❌ (adapter) | ❌ | — |
| mctrader-data | △ (storage + backfill, 향후 label/feature builder 가능성) | ❌ (현재) | future |
| mctrader-engine | ✅ (strategy + runner + executor) | ✅ | runtime=error / 외=warning |
| mctrader-web | △ (Streamlit research notebook 가능성) | ❌ (현재) | future |

**Lint tool 위치**: `mctrader-engine/src/mctrader_engine/lookahead/` — strategy + backtest + paper + risk 의 책임이 이미 engine 에 있어 lint 도 engine package.

**현재 scan 대상**: `mctrader-engine/src/mctrader_engine/strategy + runner + executor` 만 (CI workflow `lookahead-lint.yml`).

## 향후 확장 trigger

다음 시점에 cross-repo scan 추가 검토:

### mctrader-data 확장 trigger

- **Trigger**: feature engineering pipeline / label builder 추가 시 (예: ML strategy 의 supervised target 생성)
- **Severity profile**: `mctrader_data/feature/` = warning + allowlist (research path), `mctrader_data/storage/` = error 후보 (단, storage 는 strategy runtime 아님 — 검토 필요)
- **새 lookahead pattern 후보**: full-sample scaler fit before train/test split, label leakage from future bars, target column reference in feature builder

### mctrader-web 확장 trigger

- **Trigger**: Streamlit research notebook / dashboard 가 strategy decision 직접 영향 (예: 사용자 manual override) 시
- **Severity profile**: `mctrader_web/research/` = warning + allowlist, `mctrader_web/dashboard/` = warning (read-only 가시화만, runtime 영향 X 가정)

### Cross-repo scan 도입 절차

1. 본 governance doc 갱신 (해당 repo 의 scan 대상 + severity 정의 추가)
2. `mctrader-engine/src/mctrader_engine/lookahead/patterns.py` 의 `_DEFAULT_RUNTIME_SUBSTRINGS` 확장 검토
3. Cross-repo scan workflow = 각 repo 의 `.github/workflows/lookahead-lint.yml` 추가 (mctrader-engine 의 lookahead-lint CLI 를 install + run)
4. 별도 Epic Story 로 진입 (ADR-005 cross-repo amendment 가 필요할 수도)

## 책임 분담

| 책임 | 담당 |
|---|---|
| Lint tool implementation | mctrader-engine (`mctrader_engine/lookahead/`) |
| Pattern rule 정의 | mctrader-engine + ADR-005 amendment |
| Scan 대상 / severity profile | 각 consuming repo 의 CI workflow + 본 governance doc |
| Allowlist TOML 위치 | 각 repo 의 `tests/lookahead/lookahead_allowlist.toml` (또는 repo root) |
| Suppression annotation grammar | 동일 (`# mctrader-lookahead-allow: <rule_id> reason="..." owner=<bare> expires=YYYY-MM-DD`) |

## ADR-006 promotion gate hook

`validate_lookahead_baseline(report_path)` → `LookaheadBaselineCheck(in_range=...)` 가 Backtest → Paper / Paper → Live promotion 단계에서 호출. 검증 조건: `error_count == 0 AND expired_count == 0`.

본 hook 은 **생성된 ExecutionReport 의 SummaryStats** 도 포함하도록 향후 확장 검토 (`SummaryStats.lookahead_findings_count` 가 0 인지 검증).

## 관련 문서

- ADR-005 (Lookahead bias 4-layer verification)
- ADR-006 (WFO + OOS governance + Promotion gate)
- EPIC-RESULTS-MCT-37.md (본 Epic 결과)
- mctrader-engine/src/mctrader_engine/lookahead/ (구현 위치)
