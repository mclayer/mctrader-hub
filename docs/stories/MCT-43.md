---
story_key: MCT-43
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-41
related_adrs: ADR-002, ADR-008, ADR-012
---

# MCT-43: Engine LiveExecutor Safety Shell — `--mode live + --confirm-live + isolated runtime`

## 1. 사용자 요구사항 (verbatim, MCT-41 Epic Phase 1)

ADR-002 D9 (3-condition AND) + ADR-008 D4 의 mctrader-engine 측 enforcement. LiveExecutor 가 엄격 opt-in.

## 2. 도메인 해석

MCT-41 child #2. mctrader-engine 측 LiveExecutor 의 safety shell 구현. real Bithumb call site 직전 단계 — 실제 order 미발사. 본 Story = "Live executor 가 startup 시 3 condition verify, 미충족 시 graceful refuse".

Prerequisite: MCT-42 (ADR-012 + ADR-002/008 amendment) merge.

## 3. 관련 ADR

- ADR-002 D9, D11 (executor/live.py + components 분리)
- ADR-008 D4 (3-condition AND), D5 (CI fail-default)
- ADR-012 (Live Rollout Policy)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/executor/
├── live.py (NEW — LiveExecutor safety shell)
└── components/
    ├── runtime_isolation.py (NEW — isolation check)
    └── live_guard.py (NEW — 3-condition AND verify)
```

## 5-6. 요구사항

1. `LiveExecutor.__init__` 에서 3-condition verify (mode + confirm-live + isolated runtime)
2. CI guard: `MCTRADER_ALLOW_LIVE_TEST=1` 미설정 시 production entry 호출 즉시 raise
3. Real order 미발사 — placeholder mctrader-market-bithumb adapter 의존만 정의
4. Unit test: 3 condition 각 미충족 시 raise verify
5. Phase 2 PR (MCT-43 implementation) + Phase 1 PR (Story doc — 본 Story 의 §7 보안 + §11 ledger 확장 — 후속 Story-level Phase 1)
