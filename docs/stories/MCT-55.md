---
story_key: MCT-55
status: closed
closed_at: 2026-05-05
component: epic
type: epic
parent_epic: null
related_adrs: ADR-002, ADR-005, ADR-006, ADR-007, ADR-009
results_doc: docs/EPIC-RESULTS-MCT-55.md
---

# MCT-55 (Epic): WFO Execution — ADR-006 자동 실행 도구 + Web Integration

## 1. 사용자 요구사항 (verbatim, 2026-05-04)

> "Live 말고 backtest or paper를 위한 작업은 없나. 순차적으로 정상화하며 Live를 올릴거다."
> "동시에 가자. 구동하는 법 먼저 알려줘 WFO는 뭐냐"
> "잘 돌아간다. 다음 작업 수행해라."
> "web에도 이 WFO를 활용가능하도록 하자."

선행 context: ADR-006 (Accepted 2026-05-02, MCT-6 doc story closed) 의 D1~D12 + amendment §D7 (MCT-48) 까지 governance 완성. **그러나 자동 실행 도구가 부재** — `SplitRegistry` / `audit log` / `run manifest` / fold report 모두 사람이 손으로 만들어야 promotion gate 평가 가능. ADR-006 = 정책 문서, MCT-55 = 정책의 자동 실행자.

직전 Epic MCT-48 종료 (2026-05-04, 11 PR single-day) 로 Paper 실 운영 가능 + Promotion Evidence Bundle (§D7) 생성 가능. **Backtest 측 promotion gate (§D6) 자동화 부재가 Live 진입의 weak link** — Live (MCT-41) Phase 2 prerequisite.

## 2. 도메인 해석

mctrader 7번째 implementation Epic = **Backtest 측 promotion gate (ADR-006 §D6) 자동 실행 + Web Integration**. 사용자 명시 "활용가능하도록" → CLI + Web 양 client. MCT-48 의 FastAPI runner + Streamlit client 패턴 재사용 (1 active session lock 확장, Paper 와 mutex).

핵심 framing (Codex 7-area review 채택, 2026-05-04):

- **자동 실행자 ≠ 연구 플랫폼.** ADR-006 D8 multiple testing 이 sprawl 가능, MCT-59 statistical correction 이 isolated 으로 늦게 들어가면 D3 Top-K consensus 가 uncorrected fold metric 으로 ranking → 결과 신뢰성 손상. Lock v1 to deterministic Random 100, immutable decision_group, lazy fold data, mandatory L4 contamination check, 보수적 JSON artifact.
- **D5 OOS contamination 방어 = release blocker.** L4 fixture (`oos_selection_loop`, MCT-37 carry-forward) 는 Epic close 직전 cleanup story 가 아니라 **MCT-56 에서 fixture skeleton 도입** + MCT-57~59 통합 후 MCT-60 sealing. defer 시 D5 lineage 무방어.
- **Eager fold materialization 위험.** 180/30/30 rolling 1h fold × KRW symbol 다수 = 메모리 폭발. boundaries eager + segment data lazy (H3) hard 채택.
- **MCT-48 web 패턴 재사용.** FastAPI 기존 mctrader-web 확장 + Streamlit 별도 page (sidebar nav) + 127.0.0.1 + token + host-wide 1 active session lock 확장 (`~/.mctrader/runtime.lock` mode field, paper|wfo mutex). WFO + Paper 동시 실행 불가 (단순성 + 결정성).
- **Promotion 자동화 거부.** I2 채택 — `mctrader-cli wfo promote` 는 사람 ack 필수. promotion = 운영 결정, multi-metric AND gate 결과는 input 일 뿐 authoritative 아님.

본 Epic 은 MCT-41 (Live Mode) 와 **별도 lane** 으로 진행 가능:
- MCT-41 Phase 2 는 사용자 manual prereq 5건으로 blocked.
- MCT-55 manual prereq 0건 (Backtest = 적재 data only). 즉시 진행 가능.
- MCT-41 Phase 2 진입 시 promotion_decision.json (B→P→L 의 B→P 측) 이 Live debut evidence 의 일부.

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Codex 7-area review (codex-rescue, gpt-5.5 high, 2026-05-04)

12 design point (A~L) + web integration 4 추가 결정점 (M~Q, MCT-48 패턴 재사용). 핵심 push-back 5건 Sonnet 채택:

1. **Story decomposition 순서 재배치** — MCT-59 statistical correction 이 MCT-57 search 보다 늦으면 D8 correction 적용 못 함. correction interface 는 MCT-57 에 도입 + full impl 은 MCT-59 분리.
2. **Eager fold materialization 거부** — H1 rejected, H3 (boundaries eager + data lazy) 채택.
3. **L4 fixture defer 거부** — K2/K3 rejected. MCT-56 에서 fixture skeleton + MCT-60 에서 sealing.
4. **MCT-61 과적재 거부** — promote CLI 만 MCT-62, gate 계산은 MCT-58.
5. **ADR-006 amendment 3건 모두 mandatory** — §D5 (content-addressable storage 위치 freeze) / §D10 (`promotion_gate_version` default freeze) / §D11 (`fold_report.json` canonical schema 6 field freeze).

### Sonnet decider Phase 1 (16 sub-decision batch, 2026-05-04)

| # | Decision | Pick | 근거 |
|---|----------|------|------|
| A | WFO module 위치 | A2 — engine 내 `mctrader_engine.wfo` | 새 repo 는 audit trail 분산, ADR-002 D6 / D10 manifest provenance 손상 |
| B | SplitRegistry 저장 | B4 — content-addressable Pydantic v2 JSON + hash dir | D5 immutability + audit hash 정합 |
| C | Audit log 위치 | C1 (v1) — JSONL append-only per decision_group, C4 (future) DuckDB read model | 가장 단순, append-only enforcement 명확 |
| D | Search algorithm v1 | D1 — Random 100 only | Bayesian/TPE/optuna 새 dep 거부, ADR-006 D4 v1 baseline |
| E | Sharpe CI | E3-lite (NEW) — Newey-West HAC primary + block bootstrap report-only | 둘 다 보고하되 fail-fast 는 threshold 차이 시 만 |
| F | Multiple testing | F3 — deflated Sharpe + bootstrap reality check | FDR Benjamini-Hochberg 는 Layer 2 deferred (D8 의 명시 layering) |
| G | Run manifest 저장 | G1 — JSON per run | B4 와 일관, hashable, reviewable |
| H | Fold materialization | H3 — boundaries eager, data lazy | 메모리 폭발 회피 |
| I | Promotion 자동화 | I2 — manual `wfo promote` ack 필수 | promotion = 운영 결정, ADR-006 §D7 amendment "Bundle promotable=false 시 override 금지" 와 별개. ack 는 평가 input 인정의 운영 행위 |
| J | Search concurrency | J1 (Phase 1) — sequential single-thread, J2 후속 | 결정성 우선, multiproc 후속 candidate |
| K | L4 fixture | K1 — MCT-56 skeleton + MCT-60 sealing | defer 시 D5 contamination 방어 무효 |
| L | Decision group lifecycle | L3 — manual create 의무 + auto-create fail-fast | 우연한 grouping 방지 |
| M | Web integration depth | M3 — monitor + control 모두 | 사용자 명시 "활용가능하도록" |
| N | WFO FastAPI 위치 | N1 — 기존 mctrader-web FastAPI 확장 | MCT-48 token / 127.0.0.1 / lock 인프라 재사용 |
| O | Streamlit page 구조 | O2 — 별도 page (sidebar nav) | Paper panel 과 분리, mode 별 UX 명확 |
| P | WFO + Paper 동시성 | P1 — host-wide 1 active session lock 확장 (mode field, paper|wfo mutex) | 단순성 + 결정성. 분리는 후속 candidate |
| Q | Progress 통신 | Q1 — polling status endpoint | MCT-48 NDJSON event log 패턴 일관, SSE/WS 후속 |

16/16 escalation 0건. 사용자 사전 approval = "ㅇㅋ" (Sonnet 전체 채택).

## 4. Child Story decomposition

| Story | repo | scope | 의존 |
|---|---|---|---|
| **MCT-56** Foundation + L4 skeleton | mctrader-engine | SplitRegistry (B4) + AuditLog (C1) + run_manifest 31-field schema (D10) + decision_group lifecycle (L3) + L4 fixture **skeleton** (K1, fail-injection 점 정의 + MCT-57~59 통합 후 sealing) + `search_space_hash` + contamination semantics. `mctrader_engine.wfo` 모듈. `mctrader-cli wfo decision-group create` subcommand. | — |
| **MCT-57** Search engine + correction interface | mctrader-engine | Random 100 (D1) + Top-K rank consensus (D3) + composite rank (Sharpe/Sortino/Calmar/MDD inverse/turnover/slippage drift) + Hard filter (trade count / MDD / risk violation / 비용 후 expectancy ≤ 0) + **deflated Sharpe interface** ranking-time 적용. `mctrader-cli wfo search`. | MCT-56 |
| **MCT-58** OOS evaluator + gate D6 + fold report | mctrader-engine | fold-level metric + Sharpe CI E3-lite (Newey-West HAC + block bootstrap) + 12-metric AND gate D6 계산 (manifest replay 100% / scalar drift <1% / risk violation 0 / OOS MDD ≤20% / OOS Sharpe ≥0.8 / Sortino ≥1.0 / Calmar ≥0.5 / profitable folds ≥60% / val→OOS Sharpe decay ≤50% / trades/fold ≥30 / cost-included expectancy >0 / parameter fold variance band) + canonical `fold_report.json` (D11 median/IQR/worst/recent N/probability of loss/CI). `mctrader-cli wfo evaluate`. | MCT-57 |
| **MCT-59** Multiple testing correction full | mctrader-engine | deflated Sharpe (Bailey-López de Prado) full + bootstrap reality check (F3) + `search_space_hash` propagation full + manifest layer integration. | MCT-58 |
| **MCT-60** L4 fixture sealing | mctrader-engine | `oos_selection_loop` lineage check assertion — `selected_param_hash` ↔ OOS-evaluated candidate lineage fail injection + Lookahead lint integration (MCT-37 path) + CI fail-injection. | MCT-56~59 |
| **MCT-61** WFO Web Integration | mctrader-engine + mctrader-web | FastAPI WFO endpoints (POST /wfo/decision-groups / POST /wfo/runs / GET /wfo/runs/{id}/status / GET /wfo/runs/{id}/fold-report / POST /wfo/promote) + Streamlit WFO panel (sidebar nav 별 page, decision_group create + search progress monitor + fold report view + promote ack button) + 1 active session lock 확장 (`~/.mctrader/runtime.lock` mode field, paper|wfo mutex). | MCT-58 |
| **MCT-62** Promotion CLI + Epic close | mctrader-engine + mctrader-hub | `mctrader-cli wfo promote --decision-group X` (I2 manual ack, web ack 와 parity) + `promotion_decision.json` (promotable: bool + 12 reason list) + EPIC-RESULTS-MCT-55 + memory finalize. | MCT-58, MCT-60, MCT-61 |

### Ordering 의무

- **MCT-56 = serialized first** (immutable schema + lifecycle + L4 skeleton — 모든 후속 Story 의 ground)
- **MCT-57 = MCT-56 후** (search 가 schema 의무 사용)
- **MCT-58 = MCT-57 후** (gate 계산은 search 결과 의무)
- **MCT-59 = MCT-58 후** (correction interface 가 search 에 도입되었지만 full impl 은 evaluate 결과 의무)
- **MCT-60 = MCT-56~59 후** (L4 fixture sealing 은 모든 path reachable 이후)
- **MCT-61 = MCT-58 후** (web 은 fold report view 가능 시점 진입, MCT-59 / MCT-60 의무 아님)
- **MCT-62 = MCT-58 + MCT-60 + MCT-61 후** (promote CLI + web ack parity + Epic close)

## 5-6. 요구사항

### Blocking AC (B1~B12)

| # | AC | 충족 시점 |
|---|-----|----------|
| B1 | `mctrader-cli wfo decision-group create --strategy-family X --symbol Y --timeframe Z` 가 immutable `SplitRegistry` JSON + audit log JSONL 생성. content-addressable hash dir 저장. | MCT-56 |
| B2 | `mctrader-cli wfo search --decision-group X --budget 100` 가 Random 100 trials 실행 + Top-K rank consensus (D3) + composite rank + Hard filter + deflated Sharpe interface ranking 적용 → `candidate_selected` audit event. | MCT-57 |
| B3 | `mctrader-cli wfo evaluate --decision-group X` 가 OOS fold metric + Sharpe CI (Newey-West + block bootstrap) + 12-metric AND gate D6 계산 + canonical `fold_report.json` (D11 6 field) 생성. | MCT-58 |
| B4 | deflated Sharpe + bootstrap reality check (F3) full impl + `search_space_hash` propagation 검증 (manifest reload 시 동일 hash). | MCT-59 |
| B5 | L4 fixture `oos_selection_loop` = `selected_param_hash` lineage 가 OOS-evaluated candidate 와 연결 시 lookahead-lint detect + CI fail-injection 통과. | MCT-60 |
| B6 | FastAPI WFO endpoints (5종: decision-groups POST / runs POST / runs/{id}/status GET / runs/{id}/fold-report GET / promote POST) + 127.0.0.1 bind + token auth (`~/.mctrader/local_token` 재사용). | MCT-61 |
| B7 | Streamlit WFO panel (sidebar nav 별 page) = decision_group create + search start + progress monitor (polling) + fold report view + promote ack button. FastAPI client only. | MCT-61 |
| B8 | 1 active session lock 확장: `~/.mctrader/runtime.lock` JSON `{run_id, pid, started_ts, mode: "paper"|"wfo"}` host-wide enforce. paper + wfo 동시 실행 거부 (mutex). | MCT-61 |
| B9 | `mctrader-cli wfo promote --decision-group X` 가 사람 ack 입력 받고 `promotion_decision.json` 작성 (`promotable: bool` + 12 reason list). web `POST /wfo/promote` 와 parity (동일 결과). | MCT-62 |
| B10 | ADR-006 amendment §D5 + §D10 + §D11 PR merge (Phase 1). | Phase 1 (이 PR) |
| B11 | mctrader-engine 0.16.0 → 0.21.0 (5 bump 예상, MCT-56~60+62) / mctrader-web 0.4.0 → 0.5.0 (MCT-61) / cross-repo CI green + import smoke pass. | MCT-56~62 점진 |
| B12 | EPIC-RESULTS-MCT-55.md = WFO 자동 실행 도구 완성 + Live (MCT-41) Phase 2 prerequisite (Backtest promotion automation) 충족 명시. | MCT-62 (Epic close) |

### Calibration AC (C1~C5)

| # | metric | 의미 | 채택 |
|---|--------|------|------|
| C1 | `audit_log_event_count >= 8 per decision_group` | 8종 audit event (D5) 발생 verify | MCT-56~62 |
| C2 | `oos_segment_read AND candidate_selected in same decision_group` 발생 시 lookahead-lint fail | D5 contamination 방어 | MCT-60 |
| C3 | `fold_report.json` deserialize 후 `model_validate_json` strict pass | D11 canonical schema freeze | MCT-58 |
| C4 | `promotable: bool` non-null AND `blocking_reasons: list[str]` ([] OR populated) | I2 ack 결과 명확성 | MCT-62 |
| C5 | `wfo_e2e_smoke_duration_seconds < 300` (300초 smoke, 1h profile + 30일 fixture) | E2E 회귀 방지 | MCT-62 |

### Demonstration AC (D1)

D1 = Streamlit WFO panel (sidebar nav 별 page) = **MCT-61 의 deliverable**. MCT-31 (Live event dashboard) 과 별도, MCT-55 = WFO UI 만.

## 7. 보안 설계

- **§7.1 Trust boundary**: FastAPI bind = `127.0.0.1` only (MCT-48 enforcement 동일). token = MCT-48 의 `~/.mctrader/local_token` 재사용 (Paper 와 token sharing). Streamlit / CLI 가 동일 token 으로 attach.
- **§7.2 Threat model**: WFO = 적재 OHLCV data only (no live API). 위협 surface 작음. operator action 추적 = audit log JSONL append-only.
- **§7.3 Auth/authz**: localhost token (single user "local-user"). `POST /wfo/promote` mutation 은 ack event 로 audit log 기록. read-only (status / fold-report) 도 token 의무.
- **§7.4 OpRisk**: WFO + Paper 동시 실행 = `runtime.lock` mutex 거부 (B8). search CPU-bound 가 paper WS 처리 영향 회피. WFO search 중 Ctrl+C → audit log finalize + decision_group 재진입 가능 (immutable, append-only).
- **§7.5 민감 데이터**: 없음 (WFO = simulated, Backtest scope). Live mode (MCT-41) 진입 시 동일 control plane 재사용 시 secret 누설 위험 → MCT-41 별도 검토.

## 8. 테스트 / 11. 데이터 영향

### 신규 file (Phase 1)

- `docs/adr/ADR-006-walk-forward.md` amendment §D5 + §D10 + §D11
- `docs/stories/MCT-55.md` (Epic, 본 file)
- `docs/stories/MCT-56.md` ~ `MCT-62.md` (7 child Story stub)

### 수정 file (Phase 2+)

- `mctrader-engine/src/mctrader_engine/wfo/` (NEW module — registry / audit / manifest / search / evaluator / correction / fixture / cli) — MCT-56~60+62
- `mctrader-engine/src/mctrader_engine/cli.py` (`wfo` group 추가) — MCT-56~62
- `mctrader-engine/src/mctrader_engine/runtime/runtime_lock.py` (NEW or paper_lock.py rename) — MCT-61
- `mctrader-engine/src/mctrader_engine/lookahead/patterns/oos_selection_loop.py` (NEW L4 fixture) — MCT-60
- `mctrader-web/src/mctrader_web/api/wfo.py` (NEW FastAPI endpoint module) — MCT-61
- `mctrader-web/src/mctrader_web/dashboard/pages/wfo.py` (NEW Streamlit page, sidebar nav) — MCT-61

### DB schema / migration

- 신규 SQLite schema: 없음 (audit log = JSONL append-only file per decision_group, C1 채택).
- `mctrader-data` Parquet/DuckDB 호출은 기존 `scan_candles()` 재사용 (read-side only, 신규 partition 없음).

### Reversible

- Phase 1 doc 단계 = yes.
- Phase 2-7 implementation = yes (file revert + 0 cost rollback, WFO = simulated).

## 12. Sonnet Decision Log

| packet_id | trigger | options_count | decider_pick | override? | audit_result | timestamp |
|-----------|---------|---------------|--------------|-----------|--------------|-----------|
| MCT-55-Phase1-16dec | substantive-multi-decision-batch | 16 sub × 2~4 options | A2/B4/C1/D1/E3-lite/F3/G1/H3/I2/J1/K1/L3/M3/N1/O2/P1+Q1 | no | direct | 2026-05-04Z (Codex review + Sonnet 합성 + 사용자 approve "ㅇㅋ") |

16/16 escalation 0건. Phase 1 large scope (Epic + 7 child + 3 ADR amendment). Codex 7-area review (codex-rescue gpt-5.5 high) + Sonnet (claude-opus-4-7) 합의.

## 13. Out-of-scope (확정 거부)

- Live mode (MCT-41 별도 lane, manual prereq blocked)
- Bayesian/TPE/optuna/scikit-optimize 새 dep (D1 random only)
- FDR Benjamini-Hochberg correction (D8 Layer 2 deferred)
- Multi-strategy registry (별도 후속 Epic)
- Multi-symbol portfolio (별도 후속 Epic)
- WFO + Paper concurrent 실행 (P1 mutex)
- WFO CI auto-trigger (manual CLI v1)
- Real-time WFO during paper run (offline only)
- WebSocket / SSE push for progress (Q1 polling)
- Multi-user / OAuth (MCT-48 single-user pattern 유지)
- ADR-007 D3 Exposure / D10 Personal-platform threshold (별도 Epic)
- Streamlit WFO advanced analytics (fold heatmap / parameter surface plot — 후속)
- DuckDB audit log read model (C1 v1 JSONL, C4 후속)
- Multi-process search (J1 sequential, J2 후속)
