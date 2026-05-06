# Collector HA Phase 7 — Calibration + Epic Close (FINAL)

**Date**: 2026-05-06
**Story**: MCT-96 (#108) — X7 child of MCT-89
**Sister Stories MERGED**: MCT-91 (X2) + MCT-92 (X3) + MCT-93 (X4) + MCT-94 (X5) + MCT-95 (X6)

## 0. Codex Phase 7 design review (6/6 ADOPT 합)

| F | Codex | Sonnet | Action |
|---|---|---|---|
| F-1 C1 methodology | SUGGEST | 채택 | ms/event 절대값 verdict (1ms target) + 100k as manual benchmark |
| F-2 C2 methodology | SUGGEST | 채택 | p50/p95/p99 + wall-clock + ms/event + row count + bytes |
| F-3 E2E done-bar | SUGGEST | 채택 | single-host two-process simulation (real 2-host = operator deployment) |
| F-4 synthetic vs real | SUGGEST | 채택 | synthetic blocking + real-Bithumb observational only |
| F-5 EPIC-RESULTS schema | SUGGEST | 채택 | 10-section schema (story summary + C1/C2 + 16-decision outcome + ...) |
| F-6 README backfill | ADOPT-AS-IS | 채택 | — |

Escalation 0.

## 1. Step plan

1. `scripts/ha/calibration/c1_dedup_throughput.py` — C1 measurement script
2. `scripts/ha/calibration/c2_scan_latency.py` — C2 measurement script
3. Run C1 + C2 → capture output → commit `*_results.txt`
4. `scripts/ha/e2e/two_process_simulation.py` — E2E demo
5. Run E2E → capture output → commit `e2e_results.txt`
6. `docs/results/EPIC-RESULTS-MCT-89.md` — 10-section Epic close artifact
7. `scripts/ha/README.md` §"Capacity" TBD → measured values backfill
8. `docs/stories/MCT-96.md` — Story §1-9 + §11 (Epic-level 회고)
9. PR open + admin merge + Memory update + Epic close marker

## 2. Acceptance Criteria

- [x] C1 PASS (ms/event 절대값 < 1ms target)
- [x] C2 PASS (informational baseline)
- [x] E2E PASS (양 heartbeat + scan no crash + restart simulated)
- [x] EPIC-RESULTS-MCT-89.md committed (10 sections)
- [x] README capacity 측정값 backfill
- [x] Story §1-9 + §11 + Phase 7 plan committed
- [x] Epic MCT-89 status: ✅ CLOSED

## 3. Out-of-scope (post-Epic / v2)

(All deferred items captured in EPIC-RESULTS-MCT-89.md §7.)

- heartbeat history ring-buffer (X4 후속 minor)
- HeartbeatMetrics.events_total cumulative
- Slack/email proactive alerting (v2)
- k8s/Nomad orchestration (영구 거부)
- Auto-rollback on health gate failure (영구 거부)
- Multi-network HA (후속 Epic)
- Real 2-host shared-storage E2E validation (operator deployment phase)
