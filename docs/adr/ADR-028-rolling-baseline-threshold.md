---
adr: ADR-028
title: Rolling Distribution Baseline for Data Health Threshold
status: Reserved
date: 2026-05-14
story: MCT-165 (reservation only — 본문은 MCT-165 종료 후 별 PR 발의)
supersedes: null
amends: null
---

# ADR-028: Rolling Distribution Baseline for Data Health Threshold

## Status

**Reserved** — 본 ADR 은 MCT-165 Phase 1 PR 에서 자리 예약만. 본문은 본 Story 종료 후 별 PR 발의.

근거: MCT-165 brainstorm Phase 1 D5=C 결정 — "정적 ±20% 우선 + rolling baseline 자리 예약 + 후속 ADR 발의". OQ-3 채택 = "Phase 1 PR 에 stub placeholder + Story §10 발의 trigger 박제".

## Context (placeholder)

MCT-165 framework 의 volume layer 정적 ±20% 임계값이 50-sym universe 변동성에 over/under-fit 위험 (MCT-165 §6 R1 HIGH). 시장 이벤트 (급변동 시 tick 폭증) 또는 거래소 outage (tick 0) 시 정적 envelope 는 정상 시장 이상을 alert → alert fatigue 누적.

Researcher Phase 0 Unknown unknown 박제: "추산 ~870 MiB/day 는 평균 변동성 가정. ±N σ envelope 미정의 시 검증기가 정상 시장 이상을 alert. volume 검증 baseline 은 정적 추산 아닌 rolling distribution 이어야 함."

## Decision (예약 — 본문 후속)

후보 candidate (확정 X, 후속 PR 에서 결정):

- **D1**: rolling window = 7d trailing mean ± 2σ (Researcher 권고). 단 50-sym 전환 이후 7d 누적 시점 (= 2026-05-16 이후) 부터 사용 가능. boundary crossing 처리 = MCT-165 INV-2 cut-in 2026-05-09 적용 후 rolling 누적.
- **D2**: rolling baseline 미달성 (window < 7d) 시 정적 ±20% fallback. framework `--baseline rolling` 옵션 으로 명시.
- **D3**: SLO budget 정의 (data-health-slo-budget ADR 분리 후보) — burn rate 기반 alert.

## Consequences (예약)

본문 후속 박제.

## Cross-ref

- MCT-165 (본 framework Story)
- MCT-165 §6 R1 HIGH (정적 ±20% over/under-fit 위험)
- MCT-165 §6 D5=C (rolling 자리 예약 + 후속 ADR 발의 결정)
- ADR-009 §D12 (forward-only invariant — detective only 원칙)
- ADR-027 (L1/L2/L3 tiering — health 측정 대상 layer)
- docs/domain-knowledge/domain/data-health/README.md (7-layer + SLO budget 박제)

## Trigger 조건

본 ADR 본문 발의 = MCT-165 Phase 2 PR LAND + V1 D+5/D+7 verify 결과 박제 후. trigger 시점에 본 ADR file 의 Status 를 Proposed 로 transition + 별 PR.
