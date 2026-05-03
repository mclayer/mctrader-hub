---
story_key: MCT-22
status: phase:대기
component: engine
type: brainstorm
parent_epic: MCT-18
related_adrs: ADR-007, ADR-002, ADR-004
---

# MCT-22: RiskGate minimal Paper enforcement (MAX_DAILY_LOSS + DRAWDOWN_LIMIT)

## 1. 사용자 요구사항 (verbatim, MCT-18 Epic)

> "RiskGate minimal Paper enforcement — 5 kill switch 중 2 critical (MAX_DAILY_LOSS + DRAWDOWN_LIMIT)"

## 2. 목표

`mctrader-engine` repo 확장:
- `risk/kill_switch.py` — MAX_DAILY_LOSS / DRAWDOWN_LIMIT trigger
- `risk/enforcer.py` — PaperExecutor 의 `_submit_and_fill` hook 통합
- `RiskGateBlocked` raise 시 order block + RiskGateEvent ExecutionReport stream 기록
- Continue (terminate X) — Paper run 자체 종료 trigger 별도

## 3. 시작 조건

- ✅ MCT-21 freeze (PaperExecutor + VirtualPortfolio)
- ✅ MCT-18 Phase 1 PR merge

## 4. 의존

- 상위: ADR-007 (5 kill switch 중 2)
- 하위: MCT-23 calibration metric (RiskGateEvent stream read)

## 5. Acceptance (placeholder)

- TBD: MAX_DAILY_LOSS threshold 표현 (절대값 KRW vs initial_capital % vs configurable)
- TBD: DRAWDOWN_LIMIT 의 peak 정의 (rolling vs all-time within run)
- TBD: VirtualPortfolio metric 누적 frequency (per bar / per fill / per second)
- TBD: RiskGateEvent ExecutionReport stream 의 emit 정책 (blocked 만 vs configured every check)
- TBD: 5 kill switch 중 나머지 3 (CONSECUTIVE_LOSSES / UNUSUAL_ACTIVITY / EXTERNAL_SIGNAL) = future Epic 명시

## 6. Phase 1 brainstorm

MCT-21 freeze 후 Codex 일괄 dispatch → Sonnet 합성 → docs/stories/MCT-22.md 본 brainstorm → Phase 1 PR.

## 7. CFP-60 debut-audit

Phase 2 merge 후 audit signal check (특히 lane-progression = B→P enforcement evidence).
