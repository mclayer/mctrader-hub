---
epic_key: MCT-55
status: closed
closed_at: 2026-05-05
related_adrs: ADR-005, ADR-006
---

# Epic MCT-55 — WFO Execution Automation + Web Integration

## Trigger

사용자 발화 (2026-05-05): "잘 돌아간다. 다음 작업 수행해라." → "web에도 이 WFO를 활용가능하도록 하자." → "codex 리뷰를 통한 sonnet-decider 검증 받고 끝까지 진행해."

ADR-006 (Walk-Forward Optimization) 자동 실행 도구 부재 → backtest 가 가능하지만 promotion gate 통과 evidence 가 manual 이라 B→P (backtest → paper) 승격 결정 불가능 한 상태였음. 본 Epic 이 WFO 의 자동화 + content-addressable 저장 + 12-metric AND gate D6 + L4 oos_selection_loop sealing + 다중 가설 보정 (Deflated Sharpe / Bootstrap reality) + paper|wfo 호스트 mutex + web 통합 + 운영자 ack 까지 7 Story 로 봉합.

## Phases (Phase 1~8, 1-day Epic)

| Phase | PR | merge SHA | scope |
|---|---|---|---|
| Phase 1 | mctrader-hub#74 | 4664a4e | Epic doc + 7 child Story stub + ADR-006 amendment §D5/§D10/§D11 |
| Phase 2 (MCT-56 Foundation) | mctrader-engine#16 | (squash) | SplitRegistry / RunManifest / 9 audit events / hashing / decision_group atomic create / wfo CLI subcommand 1 차 (0.18.0~0.19.0) |
| Phase 3 (MCT-57 Search) | mctrader-engine#18 | (squash) | search_space / random sampler / OOS boundary enforce / hard filter / composite rank / Top-K consensus / search coordinator + cli wfo search (0.20.0) |
| Phase 4 (MCT-58 Evaluator) | mctrader-engine#19 | (squash) | OOS data loader (search 와 격리) / fold_metric / Newey-West HAC / block bootstrap CI / 12-metric AND gate D6 / fold_report 6-field / manifest replay verify / cli wfo evaluate (0.21.0) |
| Phase 5 (MCT-59 Correction) | mctrader-engine#22 | 875a34d | normal_dist (stdlib CDF/PPF) / moments / Deflated Sharpe (Bailey-LdP 2014) / bootstrap reality stub (status=unavailable v1) / search_space_hash 검증 (0.23.0) |
| Phase 6 (MCT-60 L4 sealing) | mctrader-engine#23 | 79826a6 | wfo/lineage.py 본격 detect_oos_selection_loop / lookahead/oos_selection_loop.py + cli --audit / 골든 fixture 2종 (0.24.0) |
| Phase 7a (MCT-61a runtime_lock) | mctrader-engine#24 | ba30ece | runtime_lock paper\|wfo mode-aware mutex + paper_lock 후방호환 alias (0.25.0) |
| Phase 7b (MCT-61b web) | mctrader-web#8 | ea999c8 | FastAPI /wfo/* 5 endpoint + WfoLifecycleManager subprocess 격리 + Streamlit 03_wfo_panel + api_client (0.7.0) |
| Phase 8 (MCT-62 promote) | mctrader-engine#26 | 0172b53 | wfo/promote/ ack.py + decision.py + cli wfo promote (operator override 금지 구조) (0.27.0) |
| Phase 8 (MCT-62 web parity) | mctrader-web#9 | 3c11380 | POST /wfo/promote → engine apply_ack 호출 (CLI/web parity) + Streamlit promote UI (0.8.0) |
| Phase 8 (close) | mctrader-hub (this PR) | — | EPIC-RESULTS-MCT-55 + 7 child Story close + memory final |

## Codex aggregate

| Phase | Codex review | decisions | escalation | push-back resolved |
|---|---|---|---|---|
| Phase 1 (Epic + 7 stub) | 16-decision Q-by-Q | 16/16 picked | 0 | 사용자 stop 0 (autonomous brainstorm) |
| Phase 2 (MCT-56) | 7-area review | 7/7 absorbed | 0 | content-addressable §D5 amendment |
| Phase 3 (MCT-57) | 7-area review | 7/7 absorbed | 0 | OOS boundary enforce at scan_candles call site |
| Phase 4 (MCT-58) | 7-area review | 7/7 absorbed | 0 | fold-local equity baseline + per-fold-CV variance check |
| Phase 5 (MCT-59) | 7-area review | 7/7 absorbed | 1 (semantic K REJECT) | DSR returns probability ∈ [0,1], not Sharpe |
| Phase 6 (MCT-60) | 7-area review | 7/7 absorbed | 1 (semantic K REJECT) | L4 = hard pre-gate, NOT 13th D6 metric |
| Phase 7a (MCT-61a) | 7-area review | 7/7 absorbed | 0 | mode-aware mutex + paper_lock backward-compat alias |
| Phase 7b (MCT-61b) | 7-area review | 7/7 absorbed | 1 (C OVERRIDE) | subprocess.Popen isolation for CPU-bound search (not asyncio.to_thread) |
| Phase 8 (MCT-62) | 7-area review | 7/7 absorbed | 0 | operator override structurally prohibited (apply_ack derives promotable) |
| **Total** | **9 reviews** | **78/78 picked** | **3 K REJECTs absorbed** | **Sonnet decider final on all** |

## Sonnet decider key 자율 결정

- **content-addressable storage** (ADR-006 §D5 amendment) — `~/.mctrader/wfo/decision_groups/{registry_hash}/` immutable directory, `O_CREAT|O_EXCL` 으로 atomic create, audit log 단일 writer (runtime_lock 보장)
- **promotion_gate_version frozen v1.0** (§D10 amendment) — gate D6 12-metric thresholds 가 v1.0 baseline 으로 고정. v2 변경 시 schema_version bump + new gate version + decision_group invalid
- **fold_report 6-field schema** (§D11 amendment) — point estimate / CI lower / CI upper / IQR / RecentN / pass_d6 standard 강제
- **OOS boundary enforce at data_loader call site** (MCT-57) — search 가 OOS 윈도우를 절대 못 읽도록 `load_train_val_candles` 내부에서 `requested_end > val_end` 검사 → MCT-60 lineage check 까지 deferral 거부
- **DSR 의미 정정** (MCT-59) — Bailey-LdP 2014 Deflated Sharpe 는 *probability of true Sharpe > threshold*, NOT a corrected Sharpe value. `status` enum (significant / marginal / not_significant) 필수
- **L4 hard pre-gate** (MCT-60) — D6 12-metric AND 와 동격이 아니라 D6 *이전* 의 lineage clean 검사 (selection-after-OOS-read=violation). `lineage.detect_oos_selection_loop` 는 `list[CandidateSelected]` (offender list) 반환
- **subprocess isolation for CPU-bound search** (MCT-61b, Codex C OVERRIDE) — FastAPI event loop 보호 + 크래시 격리. `subprocess.Popen` + `terminal_state.json` persistence + stdout 파싱
- **operator override structural prohibition** (MCT-62) — `apply_ack` 가 `promotable` 을 booleans 에서 직접 derive. 호출자는 `promotable=True` 를 payload 로 통과시킬 path 가 코드 상 없음. 동일 함수 single source for CLI + web
- **isolated branch pattern** — Phase 3 / Phase 5 / Phase 7~8 모두 `git checkout main && git pull && git checkout -b feat/mct-NN-isolated && git checkout SHA -- specific_files` 로 cross-conversation 간섭 회피 (사용자 명시 feedback)

## ADR amendments (3건, Phase 1)

| ADR | Section | Story trigger |
|---|---|---|
| ADR-006 | §D5 amendment — content-addressable decision_group storage | MCT-56 Foundation |
| ADR-006 | §D10 amendment — promotion_gate_version frozen v1.0 | MCT-58 evaluator gate D6 |
| ADR-006 | §D11 amendment — fold_report 6-field schema | MCT-58 fold_report |

## Repo bumps (final)

| repo | from | to | bumps |
|---|---|---|---|
| mctrader-engine | 0.17.0 | 0.27.0 | 6 (MCT-56 / MCT-57 / MCT-58 / MCT-59 / MCT-60 / MCT-61a / Phase 2B parallel / MCT-62) |
| mctrader-web | 0.5.0 | 0.8.0 | 3 (MCT-61b WFO panel / MCT-62 promote parity / 중간 sync) |
| mctrader-hub | doc-only | doc-only | — |

## 다음 후속 candidate (Sonnet 자율 ranking)

1. **Live mode (MCT-41)** — 5 prerequisite 모두 충족 + 본 Epic 으로 B→P promotion evidence 확보. paper-mode 로 충분히 운용 후 manual prereq (1Password / Bithumb live API / KRW 입금 / age backup / gitleaks) 진입.
2. **MCT-12 paper deploy automation** — CFP-60 dependency 충족 시.
3. **bootstrap reality v2 (White 2000 정식)** — MCT-59 v1 status=unavailable stub 의 후속.
4. **MCT-29 sentinel-based risk ack** — MCT-52 ack core 와 통합 (small follow-up).
5. **WebSocket push from FastAPI to Streamlit** — NDJSON polling v1 → push 전환.
6. **WFO multi-strategy / multi-symbol** — 현재 SMA + KRW-BTC fixed.
7. **Multi-objective Pareto search** — 현재 composite rank single-objective.
8. **CI fold_report schema fixture lock** — schema v1 freeze 의 외부 검증.

## 총 stop count

**Phase 1~8 통합 = 1회 (autonomous)**. 사용자 trigger 만 6회 ("그대로 진행" / "전에 이야기했던 것처럼 브랜치를 나누면 되었을텐데?" / "진행합시다" 등). admin merge autonomy 패턴 + isolated branch 패턴 + Codex review→Sonnet decider 무한 absorb 패턴 모두 동시 적용된 첫 1-day Epic.

## Diff vs spec (Codex 권고 absorbed)

| Spec said | Implementation | Reason |
|---|---|---|
| RunManifest 31 field stub | promotion_gate_version 추가 → 32 field | §D10 amendment |
| fold_report flat 12 metric | 6-field schema (point/CI lo/CI hi/IQR/RecentN/pass) | §D11 amendment |
| DSR returns "corrected Sharpe" | DSR returns probability + status enum | Bailey-LdP 2014 의미 정정 |
| L4 = D6 13th metric | L4 = hard pre-gate (D6 외부) | Codex K REJECT semantic |
| /wfo/runs = asyncio.to_thread | /wfo/runs = subprocess.Popen | Codex C OVERRIDE (CPU-bound, FastAPI loop 보호) |
| paper_lock dedicated | runtime_lock mode-aware mutex + paper_lock alias | MCT-61a (paper|wfo 동시 호스트 운영 차단) |
| promote ack = optional override | operator override structurally prohibited | apply_ack derives promotable inside engine |
| `wfo/promote/web.py` separate | web /wfo/promote → engine apply_ack 직접 호출 | parity = single source |

## Cross-references

- Epic doc: docs/stories/MCT-55.md
- 7 child Stories: docs/stories/MCT-{56,57,58,59,60,61,62}.md
- ADR amendments: docs/adr/ADR-006-walk-forward.md (§D5, §D10, §D11)
- Memory: project_mctrader.md (Epic close section), feedback_brainstorm_codex_review_pattern.md (autonomous Q-by-Q), feedback_phase_codex_review_loop.md (per-phase loop)
