---
story_key: MCT-42
status: phase:요구사항
component: hub
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-012, ADR-002, ADR-007, ADR-008
---

# MCT-42: Live Operational Discipline ADR 신설 + ADR-002/008 amendment

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

> "Live mode Epic Phase 1 = doc-only. ADR 정합성 ground first." Sonnet decider Phase 1 D1-D8 모두 pick=A 의 doc 화.

## 2. 도메인 해석

MCT-41 Epic 의 **serialized first** Story. 모든 implementation child (MCT-43~46) 의 ADR ground. 본 Story merge 전 다른 child 진행 금지.

## 3. 관련 ADR

- ADR-012 (신설) — Live Rollout Policy:
  - D3 First live KRW cap = 10,000 KRW
  - D5 4-stage rollout (paper-shadow → dry-run → tiny-live → full)
  - D6 Live contract set 3종 (live-trade-event-v1 + risk-decision-v1 + operator-action-v1) schema 정의
- ADR-002 amendment — D4 engine-enforced kill switch
- ADR-008 amendment — D8 incident-only fallback exception process

## 4. 관련 코드 경로

doc-only:
- `docs/adr/ADR-012-live-rollout-policy.md` (NEW)
- `docs/adr/ADR-002-trade-executor.md` (amendment section)
- `docs/adr/ADR-008-secret-management.md` (amendment section)

## 5-6. 요구사항

1. ADR-012 신설 (D3 + D5 + D6 통합)
2. ADR-002 § "Live Mode Kill Switch (D4 engine-enforced)" amendment
3. ADR-008 § "Incident-only fallback exception process (D8)" amendment
4. Phase 1 PR open + admin merge
5. MCT-43~47 prerequisite 충족 (본 Story merge 후 implementation 진행 가능)
