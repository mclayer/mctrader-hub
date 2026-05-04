---
epic_key: MCT-48
status: closed
closed_at: 2026-05-04
related_adrs: ADR-002, ADR-005, ADR-006, ADR-007, ADR-009
---

# Epic MCT-48 — Paper Runtime Operations + Web Management

## Trigger

사용자 발화 (2026-05-04): "paper를 굴려보면 좋겠는데 / cli로도 잘 되는게 좋지만 무엇보다 web으로 관리할 수 있어야 한다."

Sonnet 이 MCT-23 commit `4915029` 의 CLI runtime gap discrepancy 발견 → MCT-18 + MCT-23 retroactive sealing 동기.

## Phases (Phase 1~5, single-day Epic)

| Phase | PR | merge SHA | scope |
|---|---|---|---|
| Phase 1 | mctrader-hub#64 | 8058903 | Epic doc + 6 child Story stub + ADR-005/006 amendments |
| Phase 2 | mctrader-engine#10 | 6e428b5 | MCT-49 Paper CLI runtime sealing (0.13.0) — PaperRunner + paper_lock + ws_wrapper + mock_stream + cli wiring + register_signal_handlers flag |
| Phase 3 (parallel) | mctrader-engine#11 | 2be53c1 | MCT-51 SQLite event store + 11 Pydantic v2 events (0.14.0) — master + 11 detail tables (Codex push-back) |
| Phase 3 (parallel) | mctrader-web#1 | 42450b5 | MCT-50 FastAPI Local Runner Service (0.2.0) — 127.0.0.1:7821 + Bearer token + 1 active session enforce |
| Phase 3 (doc) | mctrader-hub#72 | 0025d64 | MCT-50/51 spec amendments (Codex push-back 6건) |
| Phase 4 | mctrader-engine#12 | 98b93d3 | MCT-52 ack core (0.15.0) — risk/ack.py shared by CLI + web |
| Phase 4 (hot-fix) | mctrader-engine#13 | 1070b46c | libcst optional → core dep (downstream consumer unblock) |
| Phase 4 | mctrader-web#2 | 1eb29f6 | MCT-52 web side (0.3.0) — POST /risk/ack + GET /risk |
| Phase 5 | mctrader-engine#14 | 958c4193 | MCT-53/54 engine — PaperRunner ↔ event_store integration + evidence bundle + paper group CLI (0.16.0) |
| Phase 5 | mctrader-web#3 | (merged) | MCT-53 Streamlit Paper Panel + /events wiring + /evidence endpoint + api_client (0.4.0) |
| Phase 5 (close) | mctrader-hub#? (this PR) | — | EPIC-RESULTS-MCT-48 + memory final + child issue close |

## Codex aggregate

| Phase | Codex review | decisions | escalation | push-back resolved |
|---|---|---|---|---|
| Phase 1 | 12-decision A~L | 12/12 picked | 0 | 7 user-Q resolved |
| Phase 2 (MCT-49) | 9-decision A~I | 9/9 picked | 0 | 4 spec/code discrepancy |
| Phase 3 (MCT-50) | 8-decision A~H | 8/8 picked | 0 | 3 spec amendments |
| Phase 3 (MCT-51) | 9-decision A~I | 9/9 picked | 0 | 3 spec amendments |
| Phase 4 (MCT-52) | 8-decision A~H | 8/8 picked | 0 | 4 implementation Qs |
| Phase 5 (MCT-53/54) | 12-decision A~L | 12/12 picked | 0 | 5 push-back absorbed |
| **Total** | **6 reviews** | **58/58 picked** | **0/58** | **26 resolved** |

## Sonnet decider key 자율 결정

- **Web 1차 UI 이지만 runtime owner = FastAPI local service** (F3+G3) — runtime authoritative
- **Artifact thinking → event sourcing** — ADR-002 D6 SQLite append-only = operational truth
- **Product 목적 = ADR-006 promotion evidence** — dashboard 는 evidence 표시 수단
- "11 tables" → master `events` + 11 detail (global monotonic seq 보장)
- libcst optional → core dep promotion (Phase 4 hot-fix)
- paper command → paper group + start/evidence subcommands (Phase 5 CLI restructure)
- Server-side policy_hash lookup (caller-injected at MCT-52 ack)
- `closed_bar_source_hash()` deterministic SHA-256 (timestamp proxy 금지)

## ADR amendments

| ADR | Section | Story trigger |
|---|---|---|
| ADR-005 | §D5 UI partial bar diagnostic label | MCT-53 (Streamlit lookahead UI trap 회피) |
| ADR-006 | §D7 Paper Promotion Evidence Bundle (8 threshold AND) | MCT-54 (calibration + risk_policy_hash invariant) |

## Repo bumps (final)

| repo | from | to | bumps |
|---|---|---|---|
| mctrader-engine | 0.12.0 | 0.16.0 | 4 (MCT-49, MCT-51, MCT-52, MCT-53/54 통합) |
| mctrader-web | 0.1.0 | 0.4.0 | 3 (MCT-50, MCT-52, MCT-53) |
| mctrader-data | 0.3.0 | 0.4.0 | 1 (MCT-51 paper_event_store reader path 미수정 — engine-only event store, hub-counted but no actual data bump in Phase 3) |
| mctrader-hub | doc-only | doc-only | — |

## MCT-18 + MCT-23 retroactive scope acknowledgment

MCT-18 Epic + MCT-23 Story 가 **operationally incomplete** 으로 close 되었음 (CLI runtime gap: cli.py paper command 가 MCT-21 skeleton 그대로 + library helpers 만 추가). MCT-48 Phase 2 (MCT-49) 가 retroactive sealing.

memory 갱신: `project_mctrader.md` 의 "MCT-23 = cli paper 완성" 표현은 부정확. 정정된 내용 = "MCT-23 = library helpers 완성, runtime CLI wiring 미완 → MCT-49 에서 봉합".

## Out-of-scope deferred to follow-up

- MCT-29 sentinel-based `risk ack` ↔ MCT-52 ack core 통합 (CLI sentinel path 와 in-process RecoveryManager path 의 통합)
- MarketDataFreshnessEvent producer wrapper (BithumbWebSocketStream observer)
- Live mode (MCT-41 별도 Epic, manual prereq blocked)
- Multi-session concurrent paper run
- WebSocket push from FastAPI to Streamlit (NDJSON polling v1)
- ExecutionReport.json deprecation (현재 derivative, 추후 removable)
- Streamlit AppTest harness (코드 path 검증, F3 권고는 두 가지 수단 권고이나 v1 = httpx unit only)

## 다음 후속 candidate (Sonnet 자율 ranking)

1. **Live mode (MCT-41)** — 5 prerequisite (RiskGate full + Recovery 3-tier + Calibration baselines + Order rate limit + Lookahead lint baseline) + **Paper runtime + evidence bundle (MCT-48)** 모두 충족. 사용자 manual prereq 5건 (1Password / Bithumb live API / KRW 입금 / age backup / gitleaks) 후 진입.
2. WFO execution
3. Multi-symbol portfolio
4. Multi-strategy registry
5. MCT-29 ↔ MCT-52 ack 통합 (small follow-up)
6. MarketDataFreshnessEvent producer wrapper
7. Streamlit AppTest smoke harness (test 보강)
8. ADR-007 D3 Exposure / D10 Personal-platform threshold catalog (별도 Epic)

## 총 stop count

**Phase 1~5 통합 = 4회**: "go" / "머지함" / "머지" / "모두 머지하라. 앞으로 admin merge 요구하지말고 무조건 승인하여 진행하라" — 전적인 sub-decision 0건. admin merge autonomy 패턴 도입 (memory feedback `admin_merge_autonomy.md`).

## Diff vs spec (Codex L3 권고)

| Spec said | Implementation | Reason |
|---|---|---|
| MCT-50 RunStatus = lifecycle/equity/orders/risk_state | minimal v1 (lifecycle/run_id/shutdown_reason/timestamps only) | Codex push-back: equity/orders/risk_state 는 MCT-51 event store wire 후 후속 Story |
| MCT-51 "11 tables" | master `events` + 11 detail | Codex push-back: global monotonic seq 보장 |
| MCT-49 \_lineage.json | 실제 `_paper_lineage_{snapshot_id}.json` | paper_storage 기존 filename 일치 |
| MCT-52 PaperRunner attribute exposure | Phase 5 implementation 시 wire | Codex deferred → Phase 5 흡수 |
| MCT-53 /events FastAPI wiring scope | Phase 5 implementation 시 wire | Codex C1 — MCT-53 absorption |
| MCT-54 paper command | paper group + start/evidence subcommands | Codex push-back: Click group 필요 |
| MCT-49 lookahead lint libcst transitive | engine core dep promotion (hot-fix) | Phase 4 CI auto-recovery |

## Cross-references

- Epic doc: docs/stories/MCT-48.md
- 6 child Stories: docs/stories/MCT-{49,50,51,52,53,54}.md
- ADR amendments: docs/adr/ADR-005-lookahead-verification.md (§D5), docs/adr/ADR-006-walk-forward.md (§D7)
- Memory: feedback_admin_merge_autonomy.md (신규), project_mctrader.md (Phase 1~5 진행 갱신)
