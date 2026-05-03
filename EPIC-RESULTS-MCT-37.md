# Epic MCT-37 — ADR-005 Lookahead lint (L1 libcst static + L4 known-bias fixture)

**Closed**: 2026-05-04
**Status**: Phase 1 + Phase 2~4 (3 mctrader-engine PRs) merged + Phase 5 close.

mctrader 의 **다섯 번째 implementation Epic**. Codex 1순위 추천 채택 (Live mode 외부 prerequisite block / Lookahead = backtest 신뢰성 foundation, 외부 prerequisite 없음). ADR-005 D2 의 4-layer verification 중 **L1 (libcst static lint) + L4 (known-bias fixture)** 구체화. L2 (visible_window) + L3 (event log invariant) 은 MCT-12/16 시점 정착됨.

## 3 child Story summary

| Story | repo | bump | CI |
|---|---|---|:---:|
| MCT-38 (foundation) | mctrader-engine | 0.9.0 → 0.10.0 | ✅ |
| MCT-39 (suppression + L4 fixture) | mctrader-engine | 0.10.0 → 0.11.0 | ✅ |
| MCT-40 (sealing: CI + report + E2E) | mctrader-engine | 0.11.0 → 0.12.0 | ✅ |

## Phase decomposition

| Phase | PR | scope |
|---|---|---|
| Phase 1 | mctrader-hub#54 | Epic doc + 3 child Story stub + Codex 7-area review |
| Phase 2 | mctrader-engine#7 | MCT-38 L1 scanner core (libcst + 6 patterns + LookaheadFinding + CLI) |
| Phase 3 | mctrader-engine#8 | MCT-39 suppression annotation + TOML allowlist + L4 fixture 3종 |
| Phase 4 | mctrader-engine#9 | MCT-40 sealing — CI workflow + JSON report + ADR-006 hook + Epic E2E |
| Phase 5 | mctrader-hub#? (본 PR) | Epic close + EPIC-RESULTS + governance doc + memory state |

## Blocking AC (B1~B9)

| # | AC | 충족 |
|---|---|:---:|
| B1 | `mctrader-cli lookahead-lint <paths>` exit 0/1 | ✅ |
| B2 | libcst 6 base detection pattern (P1~P6) | ✅ (P1 shift/pct_change/diff, P2 rolling(center=True), P3 iloc[i+N], P4 bfill, P5 merge_asof(forward), P6 scaler.fit before split) |
| B3 | runtime path = error / research path = warning + allowlist | ✅ (SeverityProfile path-substring) |
| B4 | LookaheadFinding Pydantic v2 frozen + JSON serialization | ✅ |
| B5 | L4 fixture 3종 expected layer fail | ✅ (shift_minus_1 → L1.P1, future_feature → L1.P3, same_candle_fill → L3 audit_decisions raises) |
| B6 | Suppression annotation 4-field mandatory + expiry gate | ✅ (rule_id/reason/owner/expires + 1-line look-back + suppression-malformed + suppression-expired markers) |
| B7 | CI integration (engine repo `.github/workflows/lookahead-lint.yml`) | ✅ |
| B8 | JSON CI report artifact (`lookahead_lint_report.json`) | ✅ (LookaheadReport from_findings + summary aggregator) |
| B9 | ADR-005 §C3 align — pre-commit + CI gate | ✅ (CI workflow, pre-commit 은 Out-of-scope/backlog) |

## Calibration AC (C1~C2)

| # | metric | 의미 | 채택 |
|---|---|---|:---:|
| C1 | `lookahead_lint_baseline` | engine repo strategy/runner/executor baseline finding 0 | ✅ (validate_lookahead_baseline → in_range, error_count == 0) |
| C2 | `suppression_expiry_compliance` | expired suppression 0건 | ✅ (expired_count == 0 promotion gate) |

ADR-006 promotion gate hook: `validate_lookahead_baseline(report_path)` → `LookaheadBaselineCheck(in_range=...)`. MCT-25 의 `kill_switch_violations_count == 0` / MCT-32 의 `rate_limit_violations_count == 0` 와 동일 패턴.

## Demonstration AC (D1)

D1: known_bias_shift_minus_1 fixture raw scan → L1.P1 finding emit (CI report + Epic E2E test 첨부). ✅

## Codex review aggregate

| Story | 7-area 채택 | ADR conflict |
|---|---:|---:|
| MCT-37 (Epic) | 7/7 | 0/7 |
| Phase 2 priority sub-decision | 1순위 채택 | — |

Phase 2~4 implementation 시점에는 Codex 추가 review 없이 Sonnet decider 자율 결정.

## 자율 결정 요약 (Sonnet decider)

- Tool = libcst (formatting 보존 + comment attribution + visit_<NodeName> 메타데이터 제공)
- Severity profile = path-substring (정확한 glob `**` 의 pathlib 한계 회피, Windows path 호환)
- Suppression annotation = 4-field mandatory (rule_id / reason / owner / expires) + 1-line look-back (same line OR previous line)
- Suppression abuse 방지 = expiry gate (expires < today → invalid + 별도 SUPPRESSION_EXPIRED marker)
- Malformed suppression = warning emit (`suppression-malformed` symbol) — 사용자가 조치하도록 가시화
- Allowlist = research path 만 적용 (runtime path = annotation only — 의도적 strict)
- L4 fixture 3종 = 실제 lint mechanism 가 catch 하는지 verify (oos_selection_loop = MCT-6 dependency 분리)
- LookaheadReport schema = Pydantic v2 frozen + `model_validate_json` 사용 (strict mode + JSON tuple/datetime 호환)
- ADR-006 promotion gate hook = `error_count == 0 AND expired_count == 0` (warning 은 not blocking — research path 의 의도적 leak 허용)
- libcst MetadataWrapper.visit() context = visit 시점에만 유효 — P6Visitor finalize 는 capture pattern 으로 대응
- ruff N802 per-file-ignore (libcst CSTVisitor 의 `visit_<NodeName>` camelCase 강제)

## Out-of-scope (확정 거부)

- `oos_selection_loop` fixture → MCT-6 split registry dependency (별도 Epic)
- 완전한 alias / dataflow 분석 → libcst static scope 한계, ADR-005 §C4 박제
- dynamic `getattr` / monkeypatch / runtime generated code → static scope 한계
- talib / pandas-ta rule pack → 라이브러리별 semantic model 부담, backlog
- Auto-fix codemod → suppression 추가만 권장, code rewrite 위험
- IDE plugin 통합 (VSCode / PyCharm) → CLI + CI 만, IDE backlog
- import-graph 기반 runtime detection → path glob 으로 충분, 추정 도구 도입 회피
- Column-name heuristic (target/label/future) 정확도 보장 → warning + allowlist 로 false positive 처리
- Cross-repo scan (mctrader-data / mctrader-web) → engine 만 (cross-repo governance doc 으로 향후 확장 시점 명시)
- L2 visible_window 재설계 / L3 event log schema 재설계 → 이미 정착, 본 Epic = L1 + L4 만
- Pre-commit hook installation → CI 만, local pre-commit 은 backlog
- Streamlit lookahead finding dashboard → MCT-31 분리

## CFP-60 debut-audit

Phase 2~4 진행 중 추가 finding **0건**. mctrader debut audit total 7 findings (#115~#118 + #122 + #143 + #144), Phase Gate Mergeable 의 ACTION_REQUIRED 패턴은 #143 / consumer-guide CI terminal state classification 은 #144 로 이미 정착.

## CI iteration 통계

| PR | pushes | CI failures | root cause |
|---|---:|---:|---|
| mctrader-hub#54 | 1 | 0 (phase-gate-mergeable doc-only fast-path) | — |
| mctrader-engine#7 | 4 | 3 | N802 libcst camelCase / pyright str/bytes / P6 metadata expiry |
| mctrader-engine#8 | 2 | 1 | UP036 outdated py3.10 fallback |
| mctrader-engine#9 | 2 | 1 | Pydantic strict + json.loads tuple/datetime → model_validate_json |

총 CI iteration: 9회 (P1 1 + P2 4 + P3 2 + P4 2). 사용자 stop trigger 0회 (직전 Epic MCT-32 의 `feedback_no_background_watch.md` + `feedback_ci_terminal_states_classify.md` 도입 후 첫 Epic — 패턴 안정화).

**개선 효과**: stop count 직전 Epic 5회 → 본 Epic 0회. foreground polling + terminal state 자동 분류 패턴 정착.

## 후속 candidate 우선순위 (Sonnet decider 재합성, MCT-37 close 시점)

1. **Live mode** — RiskGate full + Recovery 3-tier + Calibration baselines + Order rate limit + **Lookahead lint baseline** 모두 충족. 1Password CLI Secret + GitHub environment protection + Bithumb live API key 발급 (사용자 manual setup) 후 진입 가능
2. **WFO execution** — Walk-Forward Optimization (Lookahead lint 신뢰도 후 진입 가치 ↑)
3. **Multi-symbol portfolio**
4. **MCT-31 Streamlit RiskGateEvent + RateLimitEvent + LookaheadFinding dashboard**
5. **ADR-007 D3 Exposure** (gross / single_order_notional / symbol_concentration)
6. **Multi-strategy registry**
7. **Cross-repo lookahead scan 확장** (mctrader-data label builder + mctrader-web research path)

## 통계

- 신규 commit: 4 PR × 평균 1.7 commits ≈ 7 commits (Phase 2~4)
- 신규 코드 (Phase 2~4): ≈ 1,800 lines (src + tests)
- mctrader-hub PR: 2 (Phase 1 #54 + Epic close 본 PR)
- mctrader-engine PR: 3 (#7 foundation + #8 suppression+L4 + #9 sealing)
- engine version: 0.9.0 → 0.12.0 (3 minor bumps)
- CI iteration: 9회

## 결론

**Epic MCT-37 = mctrader 다섯 번째 implementation Epic, ADR-005 D2 L1+L4 구체화 완성.** Backtest 결과 신뢰성 foundation 정착 (lookahead 가 backtest 성능 부풀림 차단). Live mode 의 5번째 prerequisite (Lookahead lint baseline) 추가 충족 — RiskGate full + Recovery 3-tier + Calibration baselines + Order rate limit + Lookahead lint baseline 5개 모두. 다음 Epic = **Live mode** (1Password CLI + GitHub environment protection + Bithumb live key 발급 후 진입) 또는 **WFO execution** (lookahead 신뢰도 위에 build).
