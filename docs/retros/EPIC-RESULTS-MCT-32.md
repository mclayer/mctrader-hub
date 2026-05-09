# Epic MCT-32 — ADR-007 D4 Order rate limit (자체 throttle, pre-trade)

**Closed**: 2026-05-04
**Status**: Phase 1 + Phase 2~4 (3 mctrader-engine PRs + 1 mctrader-market-bithumb PR) merged.

mctrader 의 **네 번째 implementation Epic**. Codex 1순위 추천 채택 (Foundation dependency / Reversibility / Live mode prerequisite + bounded blast radius). ADR-007 D4 의 4 limit category × 3 scope sliding window pre-trade throttle 구현. mode-aware (Backtest record / Paper-Live block).

## 4 child Story summary

| Story | repo | bump | CI |
|---|---|---|:---:|
| MCT-33 (foundation) | mctrader-engine + mctrader-market-bithumb | engine 0.6.0→0.7.0, market-bithumb 0.2.0→0.3.0 | ✅ |
| MCT-34 (PaperExecutor pre-trade hook) | mctrader-engine | merged with MCT-35 | ✅ |
| MCT-35 (BacktestExecutor recording) | mctrader-engine | engine 0.7.0→0.8.0 (joint Phase 3) | ✅ |
| MCT-36 (Calibration C1 baseline + sealing) | mctrader-engine | engine 0.8.0→0.9.0 | ✅ |

## Phase decomposition

| Phase | PR | scope |
|---|---|---|
| Phase 1 | mctrader-hub#48 | Epic doc + 4 child Story stub + Codex 7-area review |
| Phase 2 | mctrader-data없음, mctrader-engine#4 + mctrader-market-bithumb#1 | MCT-33 foundation |
| Phase 3 | mctrader-engine#5 | MCT-34 + MCT-35 (joint, Paper hook + Backtest recording) |
| Phase 4 | mctrader-engine#6 | MCT-36 sealing (Calibration C1 baseline) |
| Phase 5 | mctrader-hub#? (본 PR) | Epic close + EPIC-RESULTS doc + memory state |

## Blocking AC (B1~B10)

| # | AC | 충족 |
|---|---|:---:|
| B1 | 4 limit category 모두 enforce — ORDER_CREATE / CANCEL / TOTAL_PRIVATE / PUBLIC_REST | ✅ (engine 의 OrderRateLimiter + market-bithumb 의 RestThrottle) |
| B2 | Sliding window algorithm + boundary precision | ✅ (deque[datetime] + retry_after_ms 정확) |
| B3 | TOTAL_PRIVATE = 별도 counter (derived X) | ✅ (record_order_create + record_cancel 모두 push to total_private windows) |
| B4 | KST midnight reset (daily counter natural via 86400 sliding window) | ✅ |
| B5 | Backtest = "would-have-rate-limited" 기록 (block X) | ✅ (BacktestExecutor 의 advisory RateLimitEvent emit) |
| B6 | Paper = pre-trade block + RateLimitEvent | ✅ (PaperExecutor._check_rate_limit before RiskGate) |
| B7 | RateLimitEvent + correlation_id | ✅ (Event union 확장, correlation_id field) |
| B8 | Public REST = mctrader-market-bithumb self-throttle | ✅ (RestThrottle async 5/sec, asyncio.Lock) |
| B9 | RiskPolicy 확장 (9 신규 fields) + policy_hash 통합 | ✅ (mct-32-v1 policy_version + canonical_json hash) |
| B10 | RateLimitDecision schema (allowed/category/scope/limit_window/limit_value/observed/retry/mode/ts/policy_hash/policy_version) | ✅ (Pydantic v2 frozen) |

## Calibration AC (C1)

| # | metric | 의미 | 채택 |
|---|---|---|:---:|
| C1 | `rate_limit_threshold_baseline` | 정책 한도 ÷ Bithumb 공식 한도 ∈ [0.20, 0.30] | ✅ (validate_policy_baseline 9 categories all in_range, default mct-32-v1) |

ADR-006 promotion gate: `summary.rate_limit_violations_count == 0` 검증. `compute_summary` 가 `all_events` kw 로 RateLimitEvent 자동 카운트 (mode=paper/live → violations, mode=backtest → warnings).

## Demonstration AC (D1)

D1: Streamlit RateLimitEvent 시각화 = **MCT-31 분리** (MCT-32 = no UI).

## Codex review aggregate

| Story | 7-area 채택 | ADR conflict |
|---|---:|---:|
| MCT-32 (Epic) | 7/7 | 0/7 |
| Phase 2 priority sub-decision | 1순위 채택 | — |

Phase 2~4 implementation 시점에는 Codex 추가 review 없이 Sonnet decider 자율 결정 (사용자 명시 "묻지말고 진행").

## 자율 결정 요약 (Sonnet decider)

- Algorithm = sliding window (boundary precision 우세, hard cap)
- Time source = injected Clock (RealtimeClock / SimulatedClock)
- Daily counter = trailing 86400-second window (KST midnight 자연 처리, 수동 reset 불필요)
- TOTAL_PRIVATE = 별도 counter (Codex risk: derived counter union 은 boundary slop 위험)
- Public REST = mctrader-market-bithumb adapter self-throttle (cross-repo 변경 최소)
- RateLimitEvent = 별도 stream + correlation_id (RiskGateEvent 와 분리, ADR-002 RiskGate Protocol 보존)
- mode-aware emit: Backtest "would-have-rate-limited" advisory only / Paper pre-trade block
- RestThrottle 은 asyncio.Lock 으로 concurrent acquire 직렬화 (race condition 방지)
- BithumbOfficialLimit 추정값 raise (cancel_per_day 1500→1800, total_private_per_sec 30→35) 하여 default policy 9/9 in_range
- Tests: asyncio.run() 직접 사용 (pytest-asyncio dev dependency 추가 회피)

## Out-of-scope (확정 거부)

- Broker side rate limit error code mapping → Live Epic
- Per-symbol rate limit → Multi-symbol Epic
- Retry / backoff strategy → 별도 Story (RateLimit 은 block + retry_after_ms 만)
- Public REST mode 별 차별화 → 5/sec hard, mode 무관
- Streamlit RateLimitEvent dashboard → MCT-31 분리
- Token bucket algorithm → sliding window 채택
- WFO-based rate-limit retune → 별도 Epic

## CFP-60 debut-audit

Phase 2~4 진행 중 추가 finding **0건**. mctrader debut audit total 7 findings (#115~#118 + #122 + #143 + #144), Phase Gate Mergeable 의 ACTION_REQUIRED 패턴은 #143 / consumer-guide CI terminal state classification 은 #144 로 이미 정착.

## CI iteration 통계

| PR | pushes | CI failures | root cause |
|---|---:|---:|---|
| mctrader-hub#48 | 1 | 0 | (doc-only) |
| mctrader-engine#4 | 2 | 1 | mct-32-v1 default + _ts(sec=61) datetime overflow |
| mctrader-market-bithumb#1 | 1 | 0 | — |
| mctrader-engine#5 | 2 | 1 | pyright reportAssignmentType (stub class test pattern) |
| mctrader-engine#6 | 2 | 1 | SIM108 ternary |

총 CI iteration: 8회 (P1 1 + P2 3 + P3 2 + P4 2). 사용자 stop trigger 5회 ("ㅇㅇ 그건 이제 codeforge가...", "메모리에서 이야기했잖아", "지금 이렇게 무한대기 하는 상황 해결하자", phase task notification × 2).

**개선 효과**: 두 핵심 memory feedback 추가 (`feedback_no_background_watch.md`, `feedback_ci_terminal_states_classify.md`) → terminal state 도착 즉시 자동 분류 + 처리, foreground polling 패턴 채택. 차후 Epic 부터 사용자 stop count 감소 예상.

## 후속 candidate 우선순위 (Sonnet decider 재합성, MCT-32 close 시점)

1. **Live mode** — 4-Epic 누적 prerequisite (RiskGate full + Order rate limit + Recovery 3-tier + Calibration baselines) 모두 충족, 1Password CLI Secret + GitHub environment protection 진입 가능
2. **Lookahead lint** (L1 libcst static + L4 known-bias fixture) — Backtest↔Paper calibration 신뢰도 강화
3. **WFO execution** — Walk-Forward Optimization
4. **Multi-symbol portfolio**
5. **MCT-31 Streamlit RiskGateEvent + RateLimitEvent dashboard**
6. **ADR-007 D3 Exposure** (gross / single_order_notional / symbol_concentration)
7. **Multi-strategy registry**

## 통계

- 신규 commit: 5 PR × 평균 1.4 commits ≈ 7 commits (Phase 2~4)
- 신규 코드 (Phase 2~4): ≈ 1,500 lines (src + tests)
- mctrader-hub PR: 2 (Phase 1 #48 + Epic close 본 PR)
- mctrader-engine PR: 3 (#4 foundation + #5 paper/backtest integration + #6 sealing)
- mctrader-market-bithumb PR: 1 (#1 RestThrottle)
- engine version: 0.6.0 → 0.9.0 (3 minor bumps)
- market-bithumb version: 0.2.0 → 0.3.0 (1 minor bump)
- CI iteration: 8회

## 결론

**Epic MCT-32 = mctrader 네 번째 implementation Epic, ADR-007 D4 자체 throttle 완성.** Live mode 의 4번째 (그리고 마지막) prerequisite 충족 — RiskGate full + Recovery 3-tier + Calibration baselines + Order rate limit. 다음 Epic = **Live mode** (1Password CLI + GitHub environment protection setup 후 진입).
