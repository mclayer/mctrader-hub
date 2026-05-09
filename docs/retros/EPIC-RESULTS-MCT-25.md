# Epic MCT-25 — RiskGate full (ADR-007 5 kill-switch + Recovery 3-tier)

**Closed**: 2026-05-03
**Status**: Phase 1 (1 doc PR) + Phase 2~4 (3 implementation PRs) merged, all CIs green.

mctrader 의 세 번째 implementation Epic. Codex 1순위 추천 채택 (Foundation dependency / Reversibility / Live mode prerequisite). ADR-007 의 5 kill-switch 모두 enforce + D7 Recovery 3-tier + D8 active_capital lock + D9 RiskPolicy versioning 완성. ADR-006 promotion gate "risk violation 0" 의 5/5 enforce 검증 가능.

## 5 child Story summary

| Story | repo | bump | CI |
|---|---|---|:---:|
| MCT-26 (foundation) | mclayer/mctrader-engine + mclayer/mctrader-data | engine 0.3.0→0.4.0, data 0.2.0→0.3.0 | ✅ |
| MCT-27 (CONSECUTIVE_LOSSES) | mclayer/mctrader-engine | merged with MCT-28+29 | ✅ |
| MCT-28 (UNUSUAL_ACTIVITY) | mclayer/mctrader-engine | merged with MCT-27+29 | ✅ |
| MCT-29 (EXTERNAL_SIGNAL + Recovery 3-tier) | mclayer/mctrader-engine | engine 0.4.0→0.5.0 (joint Phase 3) | ✅ |
| MCT-30 (D5 SL/TP guards + Calibration C1 + E2E) | mclayer/mctrader-engine | engine 0.5.0→0.6.0 (sealing) | ✅ |

## Phase decomposition

| Phase | PR | scope |
|---|---|---|
| Phase 1 | mctrader-hub#41 | Epic doc + 5 child Story stub registration + Codex 7-area review |
| Phase 2 | mctrader-data#1 + mctrader-engine#1 | MCT-26 foundation (RiskPolicy versioning + snapshot persistence + active_capital lock) |
| Phase 3 | mctrader-engine#2 | MCT-27 + MCT-28 + MCT-29 (3 신규 kill-switch + Recovery 3-tier + CLI risk subcommand) |
| Phase 4 | mctrader-engine#3 | MCT-30 sealing (D5 SL/TP guards + Calibration C1 KillSwitchTriggerFrequency + Epic E2E) |
| Phase 5 | mctrader-hub#? (본 PR) | Epic close + EPIC-RESULTS doc + memory state |

## Blocking AC (B1~B10)

| # | AC | 충족 |
|---|---|:---:|
| B1 | 5 kill-switch (MAX_DAILY_LOSS / DRAWDOWN_LIMIT / CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL) 모두 enforce | ✅ (test_risk_full_e2e 5 scenario) |
| B2 | reason_code 일관 — `<TRIGGER>:<reason_subkey>` 형식 | ✅ (PaperRiskGate._raise reason format) |
| B3 | first_trigger_ts + hard latch 5 trigger 모두 적용 | ✅ (_first_trigger_per_kind dict) |
| B4 | ADR-007 D7 Recovery 3-tier flow (soft auto / hard manual_ack / critical key_rotation) | ✅ (RecoveryManager + CLI risk ack) |
| B5 | ADR-007 D8 active_capital lock enforce | ✅ (evaluate_active_capital_lock) |
| B6 | ADR-007 D9 RiskPolicy hash + amendment_from + run-start freeze + drift detection | ✅ (RiskPolicySnapshot.verify_runtime + POLICY_DRIFT trigger) |
| B7 | RiskPolicy snapshot persistence — `mctrader-data/risk_policy_snapshot/run_id=...` | ✅ (write_risk_policy_snapshot + ExecutionReport.policy_hash) |
| B8 | RiskGateEvent v2 schema extension (5 kill-switch 공통 payload) | ✅ (severity/reason_code/observed/threshold/policy_hash/ack_status fields) |
| B9 | ADR-007 D5 SL/TP guard — intended_stop_loss_pct missing = soft (block X) | ✅ (evaluate_sl_tp_guards) |
| B10 | ADR-002 RiskGate Protocol check-only 보존 (update() 추가 X, internal stateful only) | ✅ (PaperRiskGate.check unchanged signature) |

## Calibration AC (C1)

| # | metric | 의미 | gate |
|---|---|---|---|
| C1 | `kill_switch_trigger_frequency` | 7 trigger × (soft_count / hard_count / critical_count + first_trigger_ts + triggers_per_day) | baseline only (재튜닝 별도 Epic) |

`KillSwitchFrequencyReport` (mctrader-engine/src/mctrader_engine/calibration/kill_switch_frequency.py) = ADR-006 promotion gate `risk_violation = total_hard + total_critical + total_soft == 0` 검증 가능.

## Demonstration AC (D1)

D1: Streamlit dashboard `RiskGateEvent` 시각화 = **MCT-31 분리** (MCT-25 = no UI change).

## Codex review aggregate

| Story | 7-area 채택 | ADR conflict |
|---|---:|---:|
| MCT-25 (Epic) | 7/7 | 0/7 |
| Phase 2 priority sub-decision | 1순위 채택 | — |

Phase 2~4 implementation 시점에는 Codex 추가 review 없이 Sonnet decider 자율 결정 (사용자 명시 "묻지말고 진행" + small implementation choices).

## 자율 결정 요약 (Sonnet decider, 사용자 stop count 5 = "그냥 진행하라" / "묻지말고 진행" / "됐나" / "이렇게 진행이 안되는 내용에 대해 리뷰하고 개선" / "진행이 안되는데" / "묻지말고 진행해라 제발")

- `RiskPolicy.compute_hash()` = sha256(canonical_json), `canonical_json()` = `model_dump(mode=json) + sort_keys + compact separators` (deterministic)
- `RiskPolicySnapshot` = run-start lock + `verify_runtime` (hash mismatch 시 PolicyDriftError → critical_stop)
- `Severity` 확장: `pass / soft / hard / critical` (D7 critical_stop tier)
- `TriggerName` 확장: 5 D1 + ACTIVE_CAPITAL_LOCK + SL_TP_GUARD + POLICY_DRIFT (총 8)
- `PortfolioState.gross_exposure` + `mark_price` optional fields (backward compat)
- `RiskGateEvent v2` additive fields (severity/reason_code/observed/threshold/policy_hash/ack_status), v1 reader 호환
- `ExecutionReport.policy_hash + policy_version + policy_amendment_from` optional metadata
- `TradeLedger` FIFO matching (spot LONG only, cancel-only = no closed trade)
- `ActivityWindow` 5min rolling deque + min_sample 20 (paper simulated reject 부족 보완)
- `ExternalSignalSentinel` file/CLI dual interface (ADR-008 D5 align — broker API X)
- `RecoveryManager` 3-tier escalation only (soft auto cooldown / hard ack reconcile / critical key_rotation)
- `evaluate_sl_tp_guards`: catastrophic_stop + max_position_age + missing_sl soft. **price_gap_guard deferred to Live Epic** (orderbook injection scope)
- `KillSwitchTriggerFrequency` per-trigger histogram + first_trigger + per_day, sorted output
- CLI: `mctrader-cli risk kill --run-id --reason --trigger` + `risk ack --run-id`
- ruff/pyright 추가 완화 없음 (UP031 → f-string 으로 정정, scope creep 없음)

## Out-of-scope (확정 거부)

ADR-007 D3 Exposure (gross / single_order_notional / symbol_concentration / KRW_cash_min / per-side bias) / ADR-007 D4 Order rate limit (2/sec, 20/min, 300/day 등) / ADR-007 D10 Personal-platform threshold catalog 전체 / strategy peak axis + rolling 24h drawdown / WFO-based threshold 재튜닝 / Streamlit RiskGateEvent dashboard (MCT-31 분리) / Multi-symbol portfolio risk / Live mode integration / Production-grade operator console (web ack UI) / RiskPolicy migration script / **price_gap_guard** (Live Epic).

## CFP-60 debut-audit

Phase 2~4 진행 중 추가 finding **0건**. 5 setup-time finding (#115~#118 + #122) 만 존재 (모두 mctrader-hub setup 시점). plugin-codeforge 의 doc-only consumer 세 번째 사례 검증.

## CI iteration 통계

| PR | pushes | CI failures | root cause |
|---|---:|---:|---|
| mctrader-hub#41 | 1 | 0 | (doc-only) |
| mctrader-data#1 | 1 | 0 | — |
| mctrader-engine#1 | 1 | 0 | — |
| mctrader-engine#2 | 2 | 1 | UP031 (% format → f-string) |
| mctrader-engine#3 | 2 | 1 | test scenario isolation (drawdown vs max_daily_loss) + legacy helper SL metadata |

총 CI iteration: 7회 (P1 1 + P2 2 + P3 2 + P4 2). 사용자 stop trigger 6회.

## 후속 candidate 우선순위 (Sonnet decider 채택)

1. **Live mode** — 1Password CLI Secret + GitHub environment protection 의무, RiskGate full prerequisite 통과로 진입 가능
2. **Lookahead lint** (L1 libcst static + L4 known-bias fixture) — Backtest↔Paper calibration 신뢰도 강화
3. **WFO execution** — Walk-Forward Optimization, promotion 통계 기반 확장
4. **Multi-symbol portfolio** — single-symbol → portfolio mechanics (correlation / per-symbol RiskGate)
5. **Multi-strategy registry** — strategy registry + orchestration + per-strategy attribution
6. **Streamlit RiskGateEvent dashboard** (MCT-31, 별도 Epic)
7. **ADR-007 D3 Exposure** (gross_exposure / single_order_notional / symbol_concentration / KRW_cash_min) — 별도 Epic
8. **ADR-007 D4 Order rate limit** (2/sec, 20/min, 300/day) — 별도 Epic

## 통계

- 신규 commit: 4 PR × 평균 1.5 commits ≈ 6 commits (Phase 2~4)
- 신규 코드 (Phase 2~4): ≈ 2,200 lines (src + tests, mctrader-engine + mctrader-data)
- mctrader-hub PR: 2 (Phase 1 #41 + Epic close 본 PR)
- mctrader-engine PR: 3 (#1 foundation + #2 3 kill-switch + #3 sealing)
- mctrader-data PR: 1 (#1 risk_snapshot partition)
- engine version: 0.3.0 → 0.6.0 (3 minor bumps)
- data version: 0.2.0 → 0.3.0 (1 minor bump)
- CI iteration: 7회

## 결론

**Epic MCT-25 = mctrader 세 번째 implementation Epic, ADR-007 5 kill-switch + Recovery 3-tier + RiskPolicy versioning 완성.** Live mode 의 prerequisite 인 "RiskGate full enforcement" 충족. ADR-006 promotion gate "risk violation 0" 검증 가능. price_gap_guard 만 Live Epic 으로 deferred (orderbook injection 의무).
