---
story: MCT-164
title: upbit L1 forward-only loss 진단 (channel mismatch + compactor source 규약)
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents:
  - DomainAgent
  - ResearcherAgent
  - RequirementsAnalystAgent
  - PMOAgent
phase_1_decider: codex (GPT-5.4) 합성 → Sonnet 채택, D1 사용자 confirm
related_story: MCT-166 (fix Story, 본 진단 결과 후 별 brainstorm 진입)
trigger: MCT-165 V2 verify 잔존 YES (verify-d5-2026-05-14.md §V2)
status: spec
---

# MCT-164 — upbit L1 forward-only loss 진단 Story

## 1. Why (사용자 동기)

사용자 원문 (verbatim):
> "wlsdlqgo / 진입해"

MCT-164 = MCT-165 V2 trigger Issue [#292](https://github.com/mclayer/hub/issues/292). 본 brainstorm 진입.

### 근본 동기 (Phase 0 RequirementsAnalystAgent WHY 추출)

upbit L1 데이터가 compaction 후 영구 손실되는 중. MCT-165 V2 verify (2026-05-14) 잔존 YES verdict 박제. forward-only invariant (ADR-009 §D12) 환경 = 진단 지연 시 1d 당 추가 손실 누적 (1d × 50 sym × upbit). 즉시 root cause 파악 + fix Story (MCT-166) 발의 가능 상태로 만들 의무.

## 2. Context 패킷 (Phase 0)

### DomainAgent
- WAL 채널명 = `orderbooksnapshot`, L1 dataset 명 = `orderbookdepth` — 채널명 불일치 의심 영역
- bithumb L1 PASS (V1) / upbit WAL 정상 적재 (collector lag SLO PASS) → 단절 지점 = WAL → L1 compaction
- forward-only invariant (ADR-009 §D12) detective only, no backfill
- L1/L2/L3 tiering = ADR-017 / ADR-027 SSOT
- 지식 공백 3 영역: collector exchange path 상세 / L1 compactor source channel 매핑 규약 / upbit channel 정의 → 본 Story 박제 후보 (D8=A channel matrix)

### ResearcherAgent
- **핵심 개념 3**:
  - Channel-Partition Coupling: collector channel allowlist → ingester WAL partition key → L1 compactor partition discovery. 한 단계 mismatch 시 silent data hole
  - Forward-Only Loss Accumulation Rate: 매 1d × 50 sym × upbit, fix 지연 = 영구 면적 선형 증가
  - Multi-Exchange Parity Asymmetry: bithumb 정상 + upbit 누락 = exchange-specific code path 존재 증거 (공유 로직 가설 기각)
- **Unknown unknowns 2**:
  - **가장 유력 가설 = channel mismatch**: MCT-162 = bithumb 만 orderbookdepth allowlist 추가 → upbit collector 가 여전히 orderbooksnapshot 만 emit → ingester WAL partition key = snapshot → L1 compactor = depth 만 discovery → upbit L1 = 0
  - "exchange=upbit 디렉터리 부재" = (1) write 시도 안 함 (upstream channel/discovery) vs (2) write 후 cleanup (compactor lifecycle bug) — 진단 시작 전 분기 필요

### RequirementsAnalystAgent
- WHY: forward-only 환경 매일 손실 누적 → 즉시 root cause + fix (명시 ↔ 실제 일치)
- 확장 요구: WAL 복구 가능성 (snapshot → depth 변환), bithumb 정상 조건 역분석, 4 후보 실시간 추적
- AC 5 + Edge 2 (WAL 재사용 불가 시 forward-only acceptable / 의도된 skip 시 scope 재검토)

### PMOAgent (Phase 0 예비)
- 2 Story 권고 (진단 / fix 분리 — 진단 결과 fix scope 차이 큼) → **D1=A 사용자 confirm 채택**
- carry-over umbrella label only
- 주요 risk: 진단 자체가 forward-only 손실 못 막음 → Phase 1 또는 Phase 2 entry 에 **WAL freeze 묶음 의무**

## 3. Phase 1 — 9 결정점 (Codex 합성 + Sonnet 채택, D1 사용자 confirm)

| D | 결정 | 핵심 |
|---|---|---|
| **D1** | **A** | 2 Story 분리 (진단 = MCT-164 / fix = MCT-166, 사용자 confirm) |
| **D2** | **A** | WAL freeze + 진단 동시 (Phase 2 entry 즉시 — forward-only loss accumulation 차단) |
| **D3** | **A** | channel mismatch 가설 우선 진단 (Researcher 유력) |
| **D4** | **C** | WAL 복구 시도 (snapshot → depth 변환) → 실패 시 forward-only acceptable |
| **D5** | **C** | fix scope = 진단 후 결정 (MCT-166 별 brainstorm) |
| **D6** | **B** | 일반 Story flow + 당일 처리 (solo dev hotfix 병렬 추적 손실 risk) |
| **D7** | **C** | upbit + bithumb code path 비교 (parity asymmetry 원인 박제) |
| **D8** | **A** | channel matrix domain-knowledge 박제 (exchange × channel × tier) |
| **D9** | **A** | ADR-017 / ADR-027 amendment (compactor source 규약 + silent-skip 차단) |

## 4. Acceptance Criteria (PMOAgent 2nd pass — 7 개)

- **AC-1 (WAL freeze)**: Given mctrader-data 가동 중, When Phase 2 entry 시 freeze 도구 실행, Then 신규 snapshot 쓰기가 차단되고 기존 WAL 이 read-only 로 박제됨
- **AC-2 (path audit)**: Given collector · ingester · compactor 코드, When WAL path layout 추적, Then 4 컴포넌트가 동일 path 규약 사용 여부 박제 (불일치 시 위치 명시)
- **AC-3 (channel mismatch 진단 D3=A)**: Given upbit collector allowlist + ingester partition key + L1 discovery, When 채널 식별자 grep 추적, Then 3 계층 간 channel 명명 일치/불일치 박제
- **AC-4 (compactor source 처리)**: Given l1.py + l2.py, When upbit snapshot/depth source 분기 read, Then 미지원 source 존재 여부 박제 (지원 시 처리 경로, 미지원 시 silent skip 위치)
- **AC-5 (WAL 복구 검증 D4=C)**: Given freeze 된 upbit WAL, When snapshot → depth 변환 시도, Then 복구 가능성 박제 (가능 → 변환 절차, 불가 → forward-only 정당화)
- **AC-6 (parity D7=C)**: Given upbit + bithumb 동일 컴포넌트, When code path diff 비교, Then bithumb 정상 동작 원인 + upbit 결함 위치 박제 (asymmetry root)
- **AC-7 (산출물 박제)**: Given 진단 완료, When 결과를 hub §10/§11/§12 + channel matrix 도메인 페이지 + ADR-017/027 amendment 본문에 박제, Then MCT-166 fix Story scope 가 진단 결과 기반으로 명시되어 발의 가능 상태

## 5. Invariant (5 개)

- **INV-1**: WAL freeze 이후 upbit forward-only loss 누적 = 0 (신규 쓰기 차단 검증)
- **INV-2**: 진단 결과는 read-only 코드 audit + freeze 된 WAL 분석으로 도출, production data mutation 금지
- **INV-3**: 4 root cause 후보 (a path / b 미지원 / c channel mismatch / d discovery skip) 각각에 대해 "확정 / 기각 / 부분기여" 3-state 박제 의무 (미진단 state 금지)
- **INV-4**: compactor source 규약 (snapshot vs depth) 은 ADR-017 / ADR-027 amendment 로 SSOT 박제, 코드 주석 단독 의존 금지
- **INV-5**: MCT-166 fix Story 는 본 진단 §10 결과 인용 없이 발의 불가 (진단 → fix 인과 chain 강제)

## 6. Risk (3 개)

- **R1 (High)**: WAL 복구 실패 시 upbit 과거 데이터 영구 손실 — 영향: backtest 정합성 훼손, 50-symbol universe scoring 재계산 필요. **완화**: D4=C forward-only acceptable 명시 + 손실 구간 박제
- **R2 (Medium)**: 진단 중 root cause 가 4 후보 외 5번째로 판명 — 영향: MCT-166 scope 재산정 + brainstorm 재진입. **완화**: §10 FIX Ledger 에 "추가 후보 발견" surface, RESET 룰 적용
- **R3 (Medium)**: parity 비교 (D7) 결과 bithumb 도 잠재 결함 보유 판명 — 영향: fix scope 가 upbit 단독 → multi-exchange 확장. **완화**: 본 Story 는 진단 only 유지, bithumb 결함은 별 Story 발의 reservation

## 7. Phase 분할

| Phase | 산출물 | wall-clock | PR |
|---|---|---|---|
| Phase 1 | spec + plan + Story file + ADR-017/027 amendment 본문 + channel matrix stub + counters title 확장 + MCT-166 reservation | 즉시 | mctrader-hub Phase 1 PR (docs only) |
| Phase 2.1 | mctrader-data WAL freeze 도구 + 진단 스크립트 + 코드 audit | 즉시 | mctrader-data Phase 2 PR |
| Phase 2.2 | hub 박제 — 진단 결과 + channel matrix 본문 + Story §8-§12 + CLAUDE.md + RETRO | 즉시 (당일) | mctrader-hub Phase 2 PR |
| MCT-166 trigger | 진단 결과 기반 fix Story brainstorm 진입 | 별 세션 (본 Story 종료 후) | MCT-166 Phase 1 PR (별 발의) |

## 8. scope_manifest 초안 (PMOAgent 2nd pass)

```yaml
planned_adrs:
  amendment: [ADR-017, ADR-027]
  reservation_only: []

planned_files:
  mctrader-hub:
    - docs/stories/MCT-164.md: 진단 Story §1-§12
    - docs/adr/ADR-017-*.md: compactor source 규약 amendment (snapshot vs depth 분기 SSOT)
    - docs/adr/ADR-027-*.md: silent-skip 차단 amendment (미지원 source 감지 시 surface 의무)
    - docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md: channel matrix 신설 (exchange × channel × tier, D8=A)
    - docs/retros/RETRO-MCT-164.md: PMO 회고 (Phase 2 land 후)
    - CLAUDE.md: §collector + §compactor + §WAL 규약 갱신
    - .codeforge/counters.json: MCT-164 title 확장 + MCT-166 reservation, next=167

  mctrader-data:
    - scripts/wal_freeze.py: Phase 2 entry WAL freeze 도구 (read-only 전환)
    - scripts/upbit_wal_diagnostics.py: 4 root cause 후보 진단 스크립트
    - scripts/wal_recovery_probe.py: snapshot → depth 변환 가능성 검증 (D4=C)
    - docs/audit/MCT-164-code-audit.md: collector/ingester/compactor read 결과 박제
    - docs/audit/MCT-164-parity-upbit-vs-bithumb.md: D7=C parity 비교
    - CLAUDE.md: §health 모듈 cross-ref + §WAL freeze 도구

planned_claude_md_sections:
  mctrader-hub:
    - §collector channel allowlist 규약
    - §ingester partition key 규약
    - §compactor source 분기 규약 (ADR-017/027 amendment cross-ref)
    - §WAL path layout SSOT
    - §exchange-channel-matrix cross-ref
```

## 9. Cross-ref

- **MCT-160 §11 R7** (carry trigger source)
- **MCT-162** (channel parity Story, bithumb 만 orderbookdepth allowlist 추가 — Researcher 유력 가설 핵심)
- **MCT-165** (V2 verify trigger source, ALL LAND 2026-05-14)
- **MCT-166** (fix Story, 본 진단 결과 후 별 brainstorm — counters reservation 박제 의무)
- **ADR-009 §D12** (forward-only invariant — INV-1 정합)
- **ADR-017 / ADR-027** (compactor source 규약 — Phase 1 amendment 대상)
- **Issue [#292](https://github.com/mclayer/hub/issues/292)** (MCT-164 trigger)

## 10. Open Question Resolution (Sonnet decider 채택)

- **OQ-1 → ADR amendment 본문 작성 timing**: ADR-017 / ADR-027 amendment 본문 = Phase 1 PR 에 LAND. 본문 = 현재 규약 박제 + 향후 의무 명시 (silent-skip 차단). 진단 결과 (channel mismatch 확정 등) 는 별 §10 / §12 박제. MCT-160 패턴 답습.
- **OQ-2 → WAL freeze 실행 timing**: Phase 2 entry 즉시 (mctrader-data PR open 직후). 진단 진행 중 freeze 효력 = forward-only loss 차단.
- **OQ-3 → channel matrix domain-knowledge 위치**: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` (MCT-165 박제분 와 같은 디렉터리, 7-layer 후속 layer = multi-exchange parity 의 SSOT).

## 11. Phase 2 진입 시 별도 의무

- writing-plans skill 진입 → Story file `docs/stories/MCT-164.md` §1-§12 작성
- counters.json title 확장 (placeholder → 실제 scope) + MCT-166 reservation 추가
- Phase 1 PR open 시 DesignReviewPLAgent dispatch + §8 Test Contract 박제 의무
- Phase 2 entry 시 WAL freeze 즉시 + memory feedback_subagent_execution 정합 = subagent-driven
- Phase 2 PMOAgent retro 자동 dispatch (memory feedback_pmo_retro_mandatory)
- MCT-166 fix Story trigger = 본 Story land 후 별 brainstorm
