---
story: MCT-165
title: Data Accumulation Health Verification — Framework + 3 follow-up Verify 통합
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents:
  - DomainAgent
  - ResearcherAgent
  - RequirementsAnalystAgent
  - PMOAgent
phase_1_decider: codex (GPT-5.4) 합성 → Sonnet 채택
status: spec
---

# MCT-165 — Data Accumulation Health Verification

## 1. Why (사용자 동기)

사용자 원문 (verbatim):

> "데이터 관련 제대로 쌓이는지에 대한 확인 작업이 예정되어 있는 것으로 안다. 모두 수행해야지 보니까 제대로 검증 못 하게 생겼는데 이 작업 세 개를 모두 결합하고 추가적으로 data 가 제대로 쌓고 있는지에 대한 확인을 제대로 수행할 수 있는 작업을 기획해서 수행해야해"

**근본 동기**:
- 3 개 산분된 follow-up (MCT-103 부피 / MCT-160 R7 upbit L1 / 50-sym × 5d health) 을 개별 실행 시 검증 누락·불일관 → 통합된 운영 framework 필요
- 일회성 점검이 아닌, 반복 실행 가능 + 명시적 판정 기준 + 운영 프로세스 정의
- forward-only invariant 환경 (ADR-009 §D12) 에서 손실 사후 인지 시 corrective 불가 → detective 검증 주기 ≤ 허용 손실 window 보장

## 2. Context 패킷 (Phase 0)

### DomainAgent
- `docs/domain-knowledge/` 에 data-health 도메인 페이지 부재 (contracts/ 2 파일만 존재)
- forward-only / L1·L2·L3 / hot·cold partition / retention / multi-exchange 사실은 ADR-009 / ADR-017 / ADR-027 박제만 존재
- → 본 Story 가 `docs/domain-knowledge/domain/data-health/` 신규 박제 후보

### Researcher
- **핵심 개념 3**:
  - Data Health 다층성 (7 층): presence → completeness → continuity → volume → schema → cross-exchange parity → collector lag. 단일 metric 검증 불가
  - Forward-only Invariant: no-backfill = 검증은 detective only, corrective 불가 → 검증 주기 ≤ 허용 손실 window
  - SLO-based Health Budget: 정상 = threshold 기반 (gap <1% / lag <60s / volume ±20%), threshold 미정의 시 noise
- **Unknown unknowns**:
  - 50-sym 전환 (2026-05-09) boundary crossing 시 동일 검증기가 10-sym / 50-sym 양쪽에서 false positive 폭발 가능
  - 정적 추산 (~870 MiB/day) vs rolling distribution baseline — 시장 이벤트 / outage 시 envelope 미정의면 정상 시장 이상을 alert

### Analyst (WHY 추출)
- **추정 동기**: 통합 health 운영화 (반복 실행 + 명시 판정 기준)
- **why 기반 확장 요구사항**:
  - 통합 health check 결과 리포팅 표준화
  - 이상 탐지 임계값 명시
  - 반복 실행 메커니즘 (CLI + 후속 schedule 기초)

### PMO (Phase 0 예비)
- 예상 4 Story → **사용자 최종 1 Story 통합 채택** (D2=B)
- 신규 Epic 발의 안 함 (D7=C — solo dev YAGNI)
- 위험: 7d/5d wall-clock 누적 차단 → Phase 2 내 단계 분할로 해결

## 3. Phase 1 — 9 결정점 (Codex 합성 → Sonnet 채택)

| D | 결정 | 핵심 |
|---|---|---|
| D1 | **B** | 운영화 health framework — 반복 실행 가능 CLI 가 핵심 산출물 |
| D2 | **B** | 1 Story 통합 (사용자 최종 선택, Phase 2 내 단계 분할로 wall-clock 차단 회피) |
| D3 | **A** | 즉시 부분 검증 (D+5, 2026-05-14) + D+7 (2026-05-16) / D+30 (2026-06-08) 후속 checkpoint |
| D4 | **C** | MVP scope = volume / gap / file count / collector lag (4 layer, 7 층 중 핵심) |
| D5 | **C** | 정적 ±20% 우선 + rolling baseline 자리 예약 + 후속 ADR 발의 |
| D6 | **B** | CLI + CSV/JSON + 자동 markdown 보고서 |
| D7 | **C** | carry-over umbrella label only (신규 Epic 발의 안 함) |
| D8 | **A** | 검증 시작점 = 2026-05-09 이후 (boundary crossing false positive 는 정적 임계값으로 흡수) |
| D9 | **A** | `docs/domain-knowledge/domain/data-health/` 신규 페이지 박제 (Story 산출물) |

### Cross-decision 의존
- D1=B → D2=B / D6=B / D9=A 정합
- D3=A + D8=A → D5=C 정합 (정적 우선 + rolling 예약)
- D4=C → D6=B scope 정렬

## 4. Acceptance Criteria (7 개)

- **AC1**: Given 4 layer health 정의 (volume / gap / file count / lag), When `data_health_check --target collector --window 7d` 실행, Then JSON/CSV 산출물에 4 layer 측정값 + threshold 판정 (PASS/WARN/FAIL) 포함.
- **AC2**: Given 정적 임계값 ±20% (volume) / gap=0 strict / file count expected (5d × 50 sym = 250) / lag <60s, When 측정값이 임계값 외, Then exit code 1 + FAIL row 표시.
- **AC3**: Given D+5 verify (2026-05-14), When V1 (50-sym 누적 부피 ~4.35 GiB ±20%) 측정, Then 결과 markdown 보고서 `docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md` 박제.
- **AC4**: Given V2 (MCT-160 R7 upbit L1 partition 0 잔존), When framework 실행, Then verdict (잔존 yes/no) + 박제 (verify only, 수정 없음). 잔존 시 MCT-164 발의 trigger 명시.
- **AC5**: Given V3 (50-sym × 5d forward-only history per-sym 분포), When 실행, Then per-sym gap / file count / volume CSV + 분포 markdown.
- **AC6**: Given D+7 checkpoint (2026-05-16), When ~6 GiB ±20% 정합 판정 실행, Then 결과 박제 + framework 회귀 시 issue 발의.
- **AC7**: Given rolling baseline 미구현 (자리 예약), When `--baseline rolling` 플래그 사용, Then `NotImplementedError` + 후속 ADR 예약 메시지 surface.

## 5. Invariant (5 개)

- **INV-1**: Forward-only detection — framework 는 read-only, 데이터 수정 / 소급 보정 금지
- **INV-2**: 검증 시작점 = 2026-05-09 이후 (boundary crossing false positive 정적 임계값으로 흡수)
- **INV-3**: 4 layer MVP scope (volume / gap / file count / lag) — parity / schema / presence 후속 ADR 진입 전까지 추가 금지
- **INV-4**: Exit code contract — 0=ALL PASS, 1=any FAIL, 2=tool error (CI integration 호환)
- **INV-5**: 산출물 박제 경로 단일 — `docs/domain-knowledge/domain/data-health/` (multi-repo split 금지)

## 6. Risk (3 개)

- **R1** (High): 정적 ±20% 임계값이 50-sym universe 변동성에 over/under-fit → rolling baseline ADR 발의 지연 시 false alert 누적
- **R2** (Medium): D+5 / D+7 verify 시점에 collector lag spike (외부 거래소 API 장애) 발생 시 V1 부피 측정 noise → 재측정 protocol 미정의
- **R3** (Medium): mctrader-data CLI subcommand vs `scripts/data_health_check.py` 위치 결정 보류 → Phase 2 구현 단계에서 wall-clock 소모 가능

## 7. Phase 분할

| Phase | 산출물 | wall-clock |
|---|---|---|
| Phase 1 PR | spec + Story file + scope_manifest IN_PROGRESS + ADR 예약 명시 | 즉시 |
| Phase 2.1 | framework CLI 구현 (4 layer measure + threshold + JSON/CSV/markdown report) + 단위 테스트 | 즉시 |
| Phase 2.2 | D+5 verify 실행 (V1 / V2 / V3) + `verify-d5-2026-05-14.md` 박제 | 2026-05-14 |
| Phase 2.3 | D+7 checkpoint (~6 GiB 정합 판정) + `verify-d7-2026-05-16.md` 박제 | 2026-05-16 |
| Phase 2.4 (out-of-PR) | D+30 checkpoint = framework merge 후 follow-up commit + `verify-d30-2026-06-08.md` | 2026-06-08 |

**Phase 2 PR scope** = framework CLI + D+5 / D+7 실측. D+30 = framework 자체로 후속 single commit.

## 8. scope_manifest 초안

```yaml
planned_adrs:
  reservation_only:
    - rolling-baseline-threshold  # Story 후속 발의
    - data-health-slo-budget       # Story 후속 발의
  amendment: []

planned_files:
  - mctrader-hub/docs/stories/MCT-165.md: Story file (§1-11)
  - mctrader-hub/docs/domain-knowledge/domain/data-health/README.md: 7 layer health 분류 + forward-only detective 원칙 + SLO budget 개념
  - mctrader-hub/docs/domain-knowledge/domain/data-health/verify-d5-2026-05-14.md: D+5 V1/V2/V3 verify 결과 박제
  - mctrader-hub/docs/domain-knowledge/domain/data-health/verify-d7-2026-05-16.md: D+7 ~6 GiB 정합 checkpoint 박제
  - mctrader-data/src/mctrader_data/cli/health_check.py: CLI entrypoint (4 layer measure + threshold + exit code)
  - mctrader-data/src/mctrader_data/health/volume.py: volume layer measurement
  - mctrader-data/src/mctrader_data/health/gap.py: gap layer measurement
  - mctrader-data/src/mctrader_data/health/file_count.py: file count layer measurement
  - mctrader-data/src/mctrader_data/health/lag.py: collector lag measurement
  - mctrader-data/src/mctrader_data/health/report.py: JSON/CSV/markdown 보고서 생성
  - mctrader-data/src/mctrader_data/health/thresholds.py: 정적 ±20% + rolling 자리 예약 (NotImplementedError)
  - mctrader-data/tests/unit/health/test_volume.py: volume layer 단위 테스트
  - mctrader-data/tests/unit/health/test_gap.py: gap layer 단위 테스트
  - mctrader-data/tests/unit/health/test_file_count.py: file count layer 단위 테스트
  - mctrader-data/tests/unit/health/test_lag.py: lag layer 단위 테스트
  - mctrader-data/tests/unit/health/test_thresholds.py: rolling NotImplementedError 검증
  - mctrader-data/tests/integration/health/test_cli_exit_code.py: exit code contract (AC2/INV-4) 통합 테스트

planned_claude_md_sections:
  - mctrader-hub/CLAUDE.md §데이터 헬스 프레임워크: framework CLI 사용법 + 4 layer 정의 + 검증 시작점 + ADR 예약
  - mctrader-data/CLAUDE.md §health 모듈: 모듈 구조 + threshold 정책 + rolling baseline 자리 예약
```

## 9. Cross-ref (D7=C — Story label only)

- Label: `epic:data-accumulation-umbrella` (carry-over umbrella, 신규 Epic 발의 안 함)
- §1 Context cross-ref:
  - MCT-103 (50-sym universe, MERGED 2026-05-09) — V1 부피 추산 베이스
  - MCT-160 (R7 upbit L1 lost, Phase 2 verify pending) — V2 partition 0 verdict
  - MCT-163 (DualWriter / row-batch streaming + ADR-009 D7 spec amend, MCT-160 F3+F6+F7 follow-up, reserved) — 미연관
  - MCT-164 (upbit L1 root cause, 본 Phase 1 PR 에서 placeholder reservation) — V2 결과 잔존 시 발의 trigger

## 10. Open Question Resolution (Sonnet decider 채택)

- **OQ-1 → mctrader-data CLI subcommand**: `mctrader-data/src/mctrader_data/cli/health_check.py`. data 도메인 응집도 우월, console_scripts entrypoint 통합. cross-repo invocation 은 mctrader-hub `make health` 또는 `gh workflow` 래퍼로 후속 가능.
- **OQ-2 → 보수적 narrow 정의**: V2 partition 0 "잔존 yes" = `expected_daily_file_count > 0` ∧ `actual_daily_file_count == 0` 인 sym 이 1 개 이상 존재. 보수적 = 거짓 음성 0 가정 (잔존 못 잡으면 MCT-164 발의 누락 위험 큼 vs 거짓 양성 비용 작음).
- **OQ-3 → ADR stub placeholder + Story §10 발의 trigger**: Phase 1 PR 에 `docs/adr/ADR-028-rolling-baseline-threshold.md` 빈 stub (frontmatter + Status: Reserved) 추가. ADR 본문은 본 Story 종료 후 별 PR 발의 (3 차 OQ 가 발생하면 회피).

## 11. Phase 2 진입 시 별도 의무

- writing-plans skill 진입 → Story file (`docs/stories/MCT-165.md`) §1-§11 작성
- scope_manifest IN_PROGRESS 등록 (PMO §11 self-write 영역)
- Phase 1 PR open 시 §8 Test Contract Architect deputy spawn 필요
