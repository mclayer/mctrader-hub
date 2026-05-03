---
story_key: MCT-41
status: phase:요구사항
component: epic
type: epic
parent_epic: null
related_adrs: ADR-002, ADR-007, ADR-008, ADR-012
---

# MCT-41 (Epic): Live Mode Debut — 5-stage rollout (paper-shadow → dry-run → tiny-live → full-live)

## 1. 사용자 요구사항 (verbatim, 2026-05-04)

> "mctrader 데뷔작 진행" → Live mode (1순위 후보, sonnet decider MCT-32 close 시점 ranking).
> "a" (option A 채택, sonnet decider Phase 1 D1-D8 모두 pick=A).

## 2. 도메인 해석

mctrader 5번째 implementation Epic = **first real KRW exposure**. 4 prior Epic (MCT-12 OHLCV→SMA backtest / MCT-18 ? / MCT-25 ? / MCT-32 order rate limit) 이 prerequisite 충족:

- RiskGate full (ADR-007 D1+D2+D3 reserved + D4=order rate limit)
- Calibration baselines (mct-32-v1 default 9/9 in_range)
- Paper mode = Live rehearsal (ADR-002 D6 SQLite event-sourced ledger)
- Recovery 3-tier 적용

Live 진입 = ADR-002 D9 "3-condition AND" (`mode==live + --confirm-live + isolated runtime`) + ADR-008 D4 secret access 강제. real loss containment = D5 4-stage rollout (10,000 KRW first cap).

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Codex 7-area audit (gpt-5.5 high, 2026-05-04, 5분)

12 P0/P1 codeforge improvement 도출 — mclayer/plugin-codeforge#156~#167 등록.

### Sonnet decider Phase 1 (8 sub-decision batch, 2026-05-04)

| # | Decision | Pick | Codex 동의 | 신뢰도 |
|---|------|------|---|---|
| D1 | LiveOpsDeputy 모델 | A — 단일 conditional deputy | 동의 | high |
| D2 | LiveOrdering ownership | A — LiveOrderingDeputy 조건부 | 동의 | high |
| D3 | First live KRW cap | A — 10,000 KRW (~7-8 USD) | 동의 | high |
| D4 | Kill switch location | A — engine-enforced (LiveExecutor) | 동의 | high |
| D5 | Rollout sequence | A — 4-stage (paper-shadow→dry-run→tiny-live→full) | 동의 | high |
| D6 | Live contract set | A — 3종 동시 schema 정의 (live-trade-event-v1 + risk-decision-v1 + operator-action-v1) | 동의 | high |
| D7 | Workflow gate placement | A — Hybrid (codeforge template + consumer policy value) | 동의 | high |
| D8 | Secret enforcement | A — 1Password-only default + incident-only fallback exception | 동의 | high |

8/8 escalation 없음. Phase 1 scope approved (large).

## 4. Child Story decomposition

| Story | repo | scope |
|---|---|---|
| **MCT-42** (Live Operational Discipline ADR) | mctrader-hub | ADR-012 신설 (D5 4-stage + D3 KRW cap + D6 contract schema) + ADR-002 amendment (D4 engine kill switch) + ADR-008 amendment (D8 incident-only fallback) |
| **MCT-43** (Engine LiveExecutor Safety Shell) | mctrader-engine | `executor/live.py` + `--mode live + --confirm-live + isolated runtime` enforcement + capabilities + rejection/order_state hooks |
| **MCT-44** (Bithumb Live API Adapter Hardening) | mctrader-market-bithumb | KRW live call site + rate-limit response handling + exchange rejection mapping + shadow/dry-run parity |
| **MCT-45** (Ledger / Reconciliation / KRW Position) | mctrader-engine | partial fill / fee / cancel / restart replay / KRW exposure reconciliation invariants (Story Live Operational Discipline 필수 충족) |
| **MCT-46** (Kill Switch + Operator Actions) | mctrader-engine | engine-enforced kill switch (D4) + operator-action-v1 producer + manual halt/resume + incident log |
| **MCT-47** (Live Rollout Gates + Evidence) | mctrader-hub + 5 repo | CI fail-default (D7 Hybrid) + live-deploy-approval gate + live-secret-policy gate + first-trade runbook + 4-stage pass criteria 검증 |

### Ordering 의무

- **MCT-42 = serialized first** (ADR 신설 + amendment, 모든 child Story 의 정합성 ground)
- **MCT-43 / MCT-45 / MCT-46 = before any Bithumb live-real order path** (engine guard + ledger + kill switch 가 prerequisite)
- **MCT-44 = parallel with MCT-45** (paper-shadow / live-dry-run only, real order 금지 until MCT-43 + MCT-45 + MCT-46 전부 PASS)
- **MCT-47 = after MCT-42, before live-real-but-tiny stage transition**

## 5-6. 요구사항

### Blocking AC (B1-B10)

| # | AC | 충족 시점 |
|---|----|----------|
| B1 | ADR-012 신설 (Live Rollout Policy + KRW cap + 4-stage + contract set) | MCT-42 |
| B2 | ADR-002 amendment (D4 engine-enforced kill switch) | MCT-42 |
| B3 | ADR-008 amendment (D8 incident-only fallback) | MCT-42 |
| B4 | LiveExecutor (`mctrader-engine/executor/live.py`) — 3-condition AND enforce | MCT-43 |
| B5 | Bithumb live API hardening (rate-limit response / rejection mapping) | MCT-44 |
| B6 | Engine-enforced kill switch (D4) + operator-action-v1 producer | MCT-46 |
| B7 | Live ledger reconciliation invariant (partial fill / fee / cancel / replay) | MCT-45 |
| B8 | live-trade-event-v1 + risk-decision-v1 + operator-action-v1 schema 정의 | MCT-42 (schema) + MCT-43~46 (producer impl) |
| B9 | 4-stage rollout pass criteria 명시 (paper-shadow → dry-run → tiny-live 10,000 KRW → full) | MCT-42 (criteria) + MCT-47 (verification) |
| B10 | First real KRW trade = 10,000 KRW + 즉시 reconcile + audit log | MCT-47 stage 3 |

### Calibration AC (C1)

| # | metric | 의미 | 채택 |
|---|--------|------|------|
| C1 | `live_first_trade_loss_max_krw <= 10000` | first tiny-live cap | MCT-47 |

### Demonstration AC (D1)

D1 = Streamlit Live event dashboard = **MCT-31 분리 / 별도 Epic** (MCT-41 = no UI).

## 7. 보안 설계

- §7.1 Trust boundary: Live secret = 1Password vault path (mctrader/live/bithumb/spot/main/) only — runtime injection. CI / log / shell history 누설 차단.
- §7.2 Threat model: real KRW loss / API key compromise / kill switch failure / partial fill drift.
- §7.3 Auth/authz: Bithumb live API = 출금 비활성 + IP allowlist + order create/cancel/read scope only.
- §7.4 OpRisk: rate limit (MCT-32 적용) + DR/disconnect (kill switch 자동 발동) + clock sync (RealtimeClock + Bithumb server time tolerance).
- §7.5 민감 데이터: API key (1Password) + KRW position (engine ledger) + order events (audit log).

## 11. 데이터 영향

- 신규 file: ADR-012 + ADR-002 amendment section + ADR-008 amendment section + Story file × 7 (Epic + 6 child)
- 수정 file: docs/adr/ADR-002-trade-executor.md / docs/adr/ADR-008-secret-management.md
- DB schema / migration: SQLite ledger schema 확장 (partial_fill / fee / KRW_position) — MCT-45
- Reversible: Phase 1 doc 단계 = yes. Phase 2+ live-real 단계 = forward-only (real KRW loss 비가역).

## 12. Sonnet Decision Log

| packet_id | trigger | options_count | decider_pick | override? | audit_result | timestamp |
|-----------|---------|---------------|--------------|-----------|--------------|-----------|
| MCT-Live-Epic-Phase1-001 | substantive-choice-a (option-formulation-batch) | 8 sub × 3 options | A × 8 | no | direct | 2026-05-04T08:00:00Z |

8/8 escalation 없음. Phase 1 large scope. Codex 7-area audit (gpt-5.5 high) + Sonnet (claude-sonnet-4-6) 합의.
