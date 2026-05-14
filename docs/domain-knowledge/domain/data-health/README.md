---
domain: data-health
created: 2026-05-14
story: MCT-165
related_adrs:
  - ADR-009 (§D12 forward-only invariant)
  - ADR-017 / ADR-027 (L1/L2/L3 tiering)
  - ADR-028 Reserved (rolling baseline threshold — 본 Story 후속 발의)
---

# Data Health Domain Knowledge

mctrader 프로젝트의 forward-only 데이터 누적 health 검증 도메인. MCT-165 Story 산출물.

## 1. Data Health 7 layer 다층성

forward-only invariant 환경 (ADR-009 §D12) 에서 "데이터가 제대로 쌓이고 있는가" 는 단일 metric 으로 판정 불가. 7 layer 로 분해 (Researcher Phase 0 박제):

| Layer | 정의 | MCT-165 MVP 채택 |
|---|---|---|
| **presence** | 파일 존재 여부 | 후속 (continuity / file_count 와 일부 중복) |
| **completeness** | 예상 row 수 대비 실측 | 후속 |
| **continuity** | time-gap 부재 | **채택 (gap layer)** |
| **volume** | 부피 분포 | **채택 (volume layer)** |
| **schema** | 컬럼 / 타입 일관성 | 후속 |
| **cross-exchange parity** | 동시각 sym 정합 | 후속 |
| **collector lag** | write → now 지연 | **채택 (lag layer)** |
| (file_count) | continuity 의 sub-dimension — daily file count | **채택 (file_count layer)** |

MVP = 4 layer (volume / gap / file_count / lag). 후속 ADR 진입 전까지 추가 layer 금지 (MCT-165 INV-3).

## 2. Forward-only Invariant — detective only

ADR-009 §D12 박제: collect 시작 시점 = backtest history 시작 시점. 1 d 지연 = 1 d 영구 손실 (no backfill).

귀결:
- **data health framework 는 detective only**. corrective 불가.
- **검증 주기 ≤ 허용 손실 window** 보장 의무. 예: 1 d 손실 허용 불가면 daily verify.
- universe rebalance (monthly, MCT-103 §7 D4) 시 drop sym 데이터 보존 + add sym 신규 collect 시작 — boundary crossing 시 검증기 false positive 위험 (§4 참조).

## 3. SLO-based Health Budget

"정상" 정의 = binary 아닌 threshold 기반:

| Layer | 정적 threshold (MCT-165 D5=C) | 후속 rolling baseline (ADR-028 Reserved) |
|---|---|---|
| volume | ±20% (expected 대비) | 7d trailing mean ± 2σ |
| gap | 0 strict | 동일 (forward-only invariant 직접 반영) |
| file_count | expected daily count 정확 일치 | 동일 (cadence 결정 의존) |
| lag | <60 s | rolling p95 |

threshold 미정의 = health check noise. SLO budget 부재 = alert fatigue.

## 4. Boundary crossing (universe rotation)

2026-05-09 = 10-sym → 50-sym 전환 시점 (MCT-103). 동일 검증기가 양쪽 데이터 join 시 false positive 폭발:

- 10-sym 시기 부피 expected: ~174 MiB/day
- 50-sym 시기 부피 expected: ~870 MiB/day (5x)

→ MCT-165 INV-2: 검증 시작점 = 2026-05-09 이후 cut-in. boundary 이전 데이터 skip.

monthly rebalance (MCT-103 §7 D4) 시에도 동일 cut-in 정책 적용 의무 — universe rotation manifest 와 검증기 join 은 후속 ADR 영역.

## 5. CLI usage

```bash
python -m mctrader_data.cli health-check \
  --target collector \
  --window 7d \
  --start-date 2026-05-09 \
  --output markdown
```

Exit code contract (MCT-165 INV-4):
- `0` = ALL PASS
- `1` = any FAIL (CI integration)
- `2` = tool error (예: `--baseline rolling` 사용 시 NotImplementedError)

## 6. Cross-ref

- ADR-009 §D12 (forward-only invariant)
- ADR-017 / ADR-027 (L1/L2/L3 tiering — health 측정 대상)
- ADR-028 Reserved (rolling baseline threshold)
- MCT-103 (50-sym universe 전환 2026-05-09)
- MCT-160 §11 R7 (upbit L1 partition 0 verify only carry)
- MCT-165 (본 framework Story)
- MCT-164 placeholder (upbit L1 root cause — V2 잔존 시 발의)

## 7. Verify 산출물

본 디렉터리 하위에 D+5 / D+7 / D+30 verify 결과 박제:
- `verify-d5-2026-05-14.md` (V1/V2/V3 D+5 실측)
- `verify-d7-2026-05-16.md` (D+7 checkpoint)
- `verify-d30-2026-06-08.md` (D+30 framework merge 후 follow-up)
