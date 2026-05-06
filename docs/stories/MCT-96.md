---
story_key: MCT-96
story_issues:
  - repo: mclayer/mctrader-hub
    number: 108
status: phase:완료
---

# MCT-96: Collector HA — Calibration + Epic Close (X7 of MCT-89, FINAL)

- **Issue**: #108
- **Status**: phase:완료

## 1. 사용자 요구사항 (verbatim)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: Calibration + Epic close. 부모 Epic = MCT-89. 모든 sister Story X2-X6 main merged. 본 X7 = C1 dedup overhead + C2 scan latency + 양 node 30분 E2E demo + EPIC-RESULTS-MCT-89.md + README capacity backfill + Epic 회고.)

## 2. 도메인 해석

X7 = Epic의 마지막 phase. 사용자 원래 요구사항의 세 축(코드 deploy / 2+ active node / 데이터 순단 0)이 모든 sister Story 에서 cover되었음을 *measurable* 하게 확인 + EPIC-RESULTS 로 기록.

## 3. 관련 ADR / Contract

신규 amendment 없음.

## 4. 외부 contract

신규 amendment 없음. C1/C2 측정 결과로 X5 README capacity 절 backfill만.

## 5. 요구사항 확장 해석 (Codex 6-area review fix 반영)

### 5.1 C1 methodology (F-1 SUGGEST 채택)

re-frame as "read-side dedup overhead" + ms/event 절대값 기준 verdict. Bithumb peak ~100 events/sec = 10ms/event budget → < 1 ms/event 절대 target (10× margin).

### 5.2 C2 methodology (F-2 SUGGEST 채택)

p50/p95/p99 + 절대 wall-clock + ms/event + partition row count + byte size 모두 보고. 7-day partition baseline (10k events/day = 70k total).

### 5.3 E2E done-bar (F-3 SUGGEST 채택)

single-host two-process simulation 채택. real 2-host shared-storage validation = operator deployment phase, X7 close blocker 아님. CI-runnable 10s default + manual 1800s (30 min) option.

### 5.4 Synthetic vs real (F-4 SUGGEST 채택)

synthetic = blocking. real Bithumb 30-min smoke = observational only (PR 가 Bithumb 운영 시간에 묶이지 않게 함).

### 5.5 EPIC-RESULTS schema (F-5 SUGGEST 채택)

`docs/results/EPIC-RESULTS-MCT-89.md` 작성:
- Story-by-story summary (Phase 1-7, PR/version/test count)
- C1/C2 measurement table
- 16-row decision stack outcome verification
- Codex review escalation log
- Out-of-scope post-Epic items
- Production readiness checklist

### 5.6 README capacity backfill (F-6 ADOPT-AS-IS)

X5 README §"Capacity" TBD → 측정값 backfill. RAM peak / disk growth / events/sec / p99 scan latency.

## 6. 외부 지식 배경

### 6.1 ms/event 절대값 방식의 calibration

상대 % overhead (multi_node=False vs True) 는 fast-path-skip vs full-work-done 비교로 misleading. 절대 ms/event 가 production realtime 부합성의 단일 지표.

### 6.2 single-host two-process simulation 의 한계

실제 NFS/SMB 의 atomic rename guarantee 검증 안됨 — 동일 host 내 local FS 의 atomic이 보장됨. 그러나 dedup contract / 양 node partition 분리 / scan transparent / 양 heartbeat 는 모두 검증.

## 7. 설계 서사

(Phase 7 plan: `docs/superpowers/plans/2026-05-06-collector-ha-phase-7.md`)

## 8. 개발 서사

### 8.1 구현 PR (X7)

본 PR (mctrader-hub) — Calibration scripts + EPIC-RESULTS + README backfill + Story §1-9 + §11 + Phase 7 plan + Epic close marker.

### 8.2 변경 surface (mctrader-hub)

| File | 변경 |
|---|---|
| `scripts/ha/calibration/c1_dedup_throughput.py` (NEW) | C1 throughput overhead measurement (ms/event 절대값) |
| `scripts/ha/calibration/c2_scan_latency.py` (NEW) | C2 scan latency p50/p95/p99 |
| `scripts/ha/calibration/c1_results.txt` (NEW) | C1 captured output |
| `scripts/ha/calibration/c2_results.txt` (NEW) | C2 captured output |
| `scripts/ha/e2e/two_process_simulation.py` (NEW) | single-host 2-process E2E demo |
| `scripts/ha/e2e/e2e_results.txt` (NEW) | E2E captured output |
| `scripts/ha/README.md` | §"Capacity" TBD → 측정값 backfill |
| `docs/results/EPIC-RESULTS-MCT-89.md` (NEW) | Epic close artifact (10 sections) |
| `docs/stories/MCT-96.md` (NEW) | Story §1-9 + §11 |
| `docs/superpowers/plans/2026-05-06-collector-ha-phase-7.md` (NEW) | Phase 7 plan |

### 8.3 Codex Phase 7 design review (6/6 ADOPT 합)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 C1 methodology | SUGGEST | re-frame as ms/event 절대값 + 1ms target |
| F-2 C2 methodology | SUGGEST | wall-clock + ms/event + row count + byte size |
| F-3 E2E done-bar | SUGGEST | single-host 2-process simulation |
| F-4 synthetic vs real | SUGGEST | synthetic blocking + real-Bithumb observational |
| F-5 EPIC-RESULTS schema | SUGGEST | 10-section schema 채택 |
| F-6 README backfill | ADOPT-AS-IS | — |

Escalation 0.

## 9. 품질 게이트 이력

| Gate | Result | Evidence |
|---|---|---|
| Codex Phase 7 design 6/6 review | ADOPT 합 | Story §5 + plan §0 |
| C1 throughput target | PASS | ms/event 절대값 < 1ms (T2 0.0009 / T3 0.0007) |
| C2 latency baseline | PASS (informational) | 7-day p99 = 1.4s |
| E2E single-host 2-process | PASS | 양 heartbeat + scan no crash + restart simulated |
| EPIC-RESULTS-MCT-89.md | committed | 10 sections + decision stack 16/16 Held |
| README capacity backfill | done | scripts/ha/README.md §Capacity 측정값 |

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|
| 1 | 2026-05-06 | calibration | C1 verdict misleading (relative % overhead apples-to-oranges) | single-node fast path skips all dedup work, % regression 의미 없음 | re-frame as ms/event 절대값, target 1ms | NO |

## 11. 회고 (Epic-level)

### 11.1 Epic MCT-89 종료 marker (2026-05-06)

8 PR + 7 phase + 78 Codex finding + 16 decision stack + 0 escalation + 4 사용자 trigger = 2일 (2026-05-05 → 2026-05-06) 으로 완주.

### 11.2 가장 큰 가치

사용자 원래 요구사항의 세 축 모두 *measurable* 하게 cover:
- "코드 수정사항 배포" → Ansible rolling `serial: 1` + heartbeat gate (X5)
- "2개 이상 Active Node 관리" → `node=` partition + read-side dedup transparent (X2+X3)
- "데이터 순단을 줄이고자" → scan API multi-node union + tier dedup + visibility (X2+X3+X4+X6)

### 11.3 가장 큰 기술 부채 발견 + 해결

Codex impl F-5 (X4) atomic O_EXCL seq allocation race — concurrent shared-storage 환경에서 quarantine artifact 손실 가능. fix 즉시 적용 (per-writer unique temp + O_CREAT|O_EXCL).

### 11.4 가장 효율적 패턴

Codex 2-tier review (design + implementation) + Sonnet decider 일괄 합성 + 사용자 stop minimization. 4 사용자 trigger 만으로 7 phase 완주.

### 11.5 후속 Epic 후보

| Epic 후보 | scope | priority |
|---|---|---|
| Multi-network HA | 다른 ISP / region 의 active-active (Bithumb 외 다른 거래소 고려 시 prerequisite) | low |
| heartbeat history ring-buffer + LIKELY_BITHUMB_OUTAGE 분류 | full gap classifier 활성화 | medium |
| Proactive alerting (Slack/email) v2 | passive observation 한계 해소 | medium-high |
| ansible-lint / shellcheck CI workflow | 후속 minor | low |

### 11.6 Epic MCT-89 진행도 (FINAL)

| Phase | Story | 상태 |
|---|---|---|
| 1 | MCT-89 (Epic) | CLOSED ✅ |
| 2 | MCT-91 (X2) | MERGED ✅ |
| 3 | MCT-92 (X3) | MERGED ✅ |
| 4 | MCT-93 (X4) | MERGED ✅ |
| 5 | MCT-94 (X5) | MERGED ✅ |
| 6 | MCT-95 (X6) | MERGED ✅ |
| **7** | **MCT-96 (X7)** | **MERGED ✅ (이번 PR — Epic FINAL)** |

**Epic MCT-89 = ✅ COMPLETE**.
