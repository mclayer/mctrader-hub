---
adr_id: ADR-020
title: Story 완료 게이트 — PMO 회고 자동 dispatch 의무
status: Accepted
date: 2026-05-09
related_story: MCT-110 (trigger)
category: Process & Governance
---

# ADR-020: Story 완료 게이트 — PMO 회고 자동 dispatch 의무

## Status

Accepted — 2026-05-09. MCT-107~111 5-Story 연속 누락 (0/5) 이후 RETRO-MCT-107-111 §8 ESCALATE 결정을 수용한 즉각 시행 ADR.

## Context

MCT-107~111 5개 Story (mctrader-market / market-bithumb / data / engine / web 각 code-review fix) 에서 Story AC 통과 + admin merge 완료 후 PMO 회고가 한 번도 자동 수행되지 않았다.

### 위반 이력

| Story | Repo | AC 통과 | PMO 회고 자동 수행 | 누락 사유 |
|---|---|---|---|---|
| MCT-107 | mctrader-market | ✓ | ✗ | Orchestrator 단계 정의 누락 |
| MCT-108 | mctrader-market-bithumb | ✓ | ✗ | 동일 |
| MCT-109 | mctrader-data | ✓ | ✗ | 동일 |
| MCT-110 | mctrader-engine | ✓ | ✗ | 동일 |
| MCT-111 | mctrader-web | ✓ | ✗ | 동일 |
| **합계** | **5/5** | | **0/5 수행** | |

5 Story 연속 0/5 누락은 규칙 부재(rule gap)가 원인이며, 개별 실수가 아님이 확인되었다.

### 사전 조치 (ADR 작성 시점 이미 완료)

`.claude/_overlay/CLAUDE.md` Story workflow 섹션에 다음 내용이 이미 박제되었다:

1. **Phase enumeration 갱신**: `…→ CI 테스트 → 보안-테스트 → 완료 → PMO 회고 (의무)`
2. **"Story 완료 의무 — PMO 회고 자동 dispatch" 섹션 신규 추가** (RETRO-MCT-107-111 §8 ESCALATE 후속)
3. **트리거 조건 명시**: "AC 통과 + admin merge 완료 → 다음 Story 로 직진하기 전에 PMOAgent dispatch"

이 ADR 은 그 즉각 조치의 **거버넌스 문서 SSOT** 이며, 추가 결정(D3, D4) 을 포함한다.

## Decision

### D1. PMO 회고 자동 dispatch 의무

Story AC 통과 + `main` merge 완료 시, Orchestrator 는 사용자 trigger 없이 `codeforge-pmo:PMOAgent` 를 자동 dispatch 하여 §11 회고를 수행한다.

- 적용 범위: hub story (`mctrader-hub/docs/stories/MCT-N.md`) 및 repo story (각 impl repo `docs/stories/MCT-N.md`) 모두
- 자율 패턴: `feedback_admin_merge_autonomy.md` 와 동일 — 사용자 trigger 대기 금지
- 다음 Story 직진 조건: PMOAgent dispatch + §11 write 완료 후

트리거 순서:

```
AC 통과
  → admin merge (ADR-011 §D1 + feedback_admin_merge_autonomy.md)
    → PMOAgent dispatch (본 ADR D1)
      → §11 write 완료
        → 다음 Story 진입
```

### D2. §11 회고 섹션 의무

모든 Story `docs/stories/MCT-N.md` 는 완료 시 `## 11. 회고` 섹션을 보유한다.

| 항목 | 규칙 |
|---|---|
| 섹션 헤더 | `## 11. 회고` (정확한 헤더, CI D4 에서 검증 예정) |
| 작성 주체 | PMOAgent 직접 write (CFP-36 owner-direct write) |
| 작성 시점 | AC 통과 + main merge 완료 직후 |
| 내용 최소 요건 | 완료 요약 / 발견 패턴 / 개선 액션 (있을 경우) |
| 미작성 = 완료 불가 | §11 없는 Story = 게이트 미통과, 다음 Story 진입 불허 |

### D3. Cross-Story 묶음 retro 조건

3개 이상 Story 에서 동일 패턴이 발견될 경우, `docs/retros/RETRO-*.md` 를 추가 작성한다.

| 규칙 | 내용 |
|---|---|
| 트리거 | 동일 루트 코즈 / 프로세스 갭이 3+ Story 에 걸쳐 확인될 때 |
| 산출물 | `mctrader-hub/docs/retros/RETRO-<slug>.md` |
| 개별 §11 갈음 불가 | 묶음 retro 존재와 무관하게 각 Story §11 은 독립 작성 의무 |
| 참조 방식 | 개별 §11 에서 `See also: RETRO-<slug>.md` 로 상호 참조 허용 |

Cross-Story 패턴 발견 lag 최소화를 위해, PMOAgent 는 §11 작성 시점에 직전 N Story 의 패턴을 스캔하고 묶음 retro 트리거 여부를 판단한다.

### D4. CI 검증 (장기 로드맵)

`phase-gate-mergeable.yml` 에 `## 11. 회고` 헤더 존재 검증을 추가한다. 이는 미래 구현 항목이며, 현재 단계는 Orchestrator 자율 의무(D1)와 CLAUDE.md 박제(사전 조치)가 게이트 역할을 대신한다.

| 단계 | 내용 |
|---|---|
| 현재 (즉시) | Orchestrator 자율 dispatch + CLAUDE.md SSOT |
| 중기 | `phase-gate-mergeable.yml` Story 완료 job 에 `## 11. 회고` 헤더 grep 추가 |
| 장기 | Story 완료 PR merge 조건에 §11 헤더 CI check 편입 |

## Alternatives Considered

### A1. 사용자가 수동 trigger — 기각

- **제안**: "PMO 회고가 필요하면 사용자가 직접 'PMO 회고해줘' 라고 요청한다."
- **기각 사유**: MCT-107~111 5/5 누락이 이 방식의 한계를 실증했다. Story 흐름에 집중하는 Orchestrator 와 사용자 모두 체계적으로 회고를 빠뜨릴 수 있다. 사용자 trigger 의존 = 규칙 부재와 동일.

### A2. §11 존재 여부를 PR 리뷰 체크리스트로 처리 — 기각

- **제안**: "PR template 에 '§11 회고 작성 여부' 체크박스 추가."
- **기각 사유**: 체크박스는 human oversight 를 요구하며, solo-dev 환경에서 다음 Story 진입 속도 압박 시 누락 가능성이 높다. CI + Orchestrator 자율 dispatch 조합이 더 강건하다.

### A3. 회고를 별도 후속 Story 로 분리 — 기각

- **제안**: "MCT-N-retro 형태의 별도 Story 를 생성하여 회고를 수행."
- **기각 사유**: Story 완료와 회고 사이의 gap 이 커지면 맥락이 희석된다. 회고는 Story 종료 직후 동일 문서에 박제해야 가치가 있다.

### A4. 묶음 retro 가 개별 §11 을 대체 — 기각

- **제안**: "3+ Story 패턴이 있으면 묶음 RETRO 파일만 작성하고 개별 §11 은 생략."
- **기각 사유**: 개별 §11 은 Story-level 완료 증거이며, 묶음 retro 는 cross-Story 분석의 별도 산출물이다. 두 목적이 다르므로 대체 불가.

## Consequences

### C1. PMO 회고 누락 0% 목표

D1 + CLAUDE.md 박제로 Orchestrator 자율 dispatch 가 보장된다. MCT-107~111 에서 관찰된 0/5 누락 패턴의 재발을 구조적으로 차단한다.

### C2. Cross-Story 패턴 발견 lag 최소화

D3 에 따라 PMOAgent 가 §11 작성 시 직전 Story 패턴을 스캔한다. 동일 루트 코즈가 3+ Story 에 걸칠 경우 즉시 묶음 retro 를 생성하므로, 패턴 발견 지연이 최소화된다. MCT-107~111 의 "PMO 회고 미수행" 패턴 자체가 5 Story 지속된 것도 이 게이트로 조기 감지되었을 것이다.

### C3. Story 완료 정의 강화

"AC 통과 + main merge = 완료" 에서 "AC 통과 + main merge + §11 작성 = 완료" 로 Story 완료 정의가 강화된다. §11 없는 Story 는 형식상 미완료 상태이다.

### C4. PMOAgent write 자율성 (CFP-36 전제)

D2 의 PMOAgent 직접 write 는 CFP-36 owner-direct write 기능 전제이다. CFP-36 미적용 상태에서는 Orchestrator 가 PMOAgent 지시에 따라 §11 을 write 한다.

### C5. CI gate 보완 (D4 장기)

현재 단계는 Orchestrator 자율 의무가 유일한 게이트이다. D4 CI 검증이 구현되면 인간-루프와 CI-루프 이중 보호가 달성된다.

## Cross-references

- `.claude/_overlay/CLAUDE.md` § "Story 완료 의무 — PMO 회고 자동 dispatch" (SSOT)
- `feedback_admin_merge_autonomy.md` (동일 자율 패턴 선례)
- `docs/retros/RETRO-MCT-107-111.md` (trigger 이벤트, §8 ESCALATE)
- ADR-011 (branch protection + CI — §D1 admin merge 조건)
- MCT-110 (trigger Story — 누락 패턴이 최초 표면화된 Story)
- `codeforge-pmo:PMOAgent` (dispatch 대상 plugin)
- CFP-36 (owner-direct write — D2 PMOAgent write 자율성 전제)
