---
story: MCT-173
title: upbit L1 backfill — frozen orderbooksnapshot WAL → L1 historical compaction
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
phase_1_decider: codex (GPT-5.4) 합성 → Sonnet 채택
trigger: MCT-166 D3=B 별 Story 결정 + MCT-164 D4=C 부분가능 verdict (Issue #298)
related_stories: [MCT-164 (진단 source), MCT-165 (verify framework), MCT-166 (fix LAND, 본 Story prerequisite)]
status: spec
---

# MCT-173 — upbit L1 backfill Story

## 1. Why (사용자 동기)

사용자 원문: > "진행해"

MCT-166 ALL LAND 직후. MCT-164 D4=C WAL 복구 부분가능 verdict + MCT-166 D3=B 별 Story 결정 인용 = 본 Story trigger.

### 근본 동기 (Phase 0 Analyst)

MCT-166 fix LAND (2026-05-14) 후 t≥LAND 신규 정상 누적. t<LAND 기간 frozen orderbooksnapshot WAL 데이터 살아있으나 L1 미생성 → backtest history 가용 범위 축소 손실. 본 Story = t<LAND 기간 historical materialization → backtest 커버리지 확장.

**Researcher 박제** (forward-only invariant temporal scope): historical materialization ≠ backfill (Kafka log compaction 선례, KIP-280 sentinel pattern). `.compacted` rename idempotency 보장 → at-least-once → effectively-once.

## 2. Context 패킷 (Phase 0)

### DomainAgent
- forward-only detective only / MCT-164 D4=C 부분가능 / MCT-166 정상 전이 (channel matrix) / ADR-017 §D2 변환 의무 / boundary 2026-05-09
- 지식 공백 3: historical-materialization 박제 부재 / sealed segment scan idempotency / WAL freeze 도구 박제 부재

### ResearcherAgent
- **핵심 개념 3**:
  - WAL Replay Idempotency (Sentinel-based) — `.compacted` rename atomic POSIX rename(2). Kafka KIP-280 pattern
  - Active vs Sealed Segment Boundary — sealed only 처리, active race condition 회피 (ADR-017 §D2)
  - Partition Path Determinism — `tier=L1/exchange=upbit/symbol=*/date=*/` deterministic, backfill 산출물 + 신규 streaming 산출물 co-exist 가능
- **Unknowns 2**:
  - Partial WAL segment in date boundary — date 일부만 freeze 시 incomplete day silent hole 위험
  - Pre-existing L1 file from unrelated cause (dev/test artifact / 다른 issue 산출물 / corrupted) — overwrite vs skip 정책 미정

### RequirementsAnalystAgent
- WHY: t<LAND historical materialization → backtest 커버리지 확장
- 확장: frozen WAL scan / idempotency / health verify

### PMOAgent
- 1 Story (단일 vertical slice)
- EPIC-data-accumulation-umbrella sibling
- **risk**: 신규 incoming WAL + historical backfill 충돌 boundary 설계 P1

## 3. Phase 1 — 9 결정점 (Codex 합성 + Sonnet)

| D | 결정 | 핵심 |
|---|---|---|
| **D1** | **B** | compactor.runner `--backfill` mode extend (신규 도구 면적 최소) |
| **D2** | **C** | Phase 2 entry 실측 결정 (frozen WAL path / freeze flag) |
| **D3** | **A** | point-in-time snapshot (concurrent WAL 충돌 회피, static metadata) |
| **D4** | **A** | 기존 `.compacted` rename (ADR-017 §D2, Kafka KIP-280) |
| **D5** | **B** | frontmatter manifest (partial WAL boundary 박제) |
| **D6** | **B** | 일반 Story flow + 당일 처리 (MCT-164/166 답습) |
| **D7** | **C** | 1 Story + Phase 2 단계 분할 (entry scan → backfill → verify) |
| **D8** | **C** | MCT-165 V2=0 + 별 verify 스크립트 (defense in depth) |
| **D9** | **C** | Phase 2 entry inventory 후 결정 (pre-existing L1 file 정책) |

## 4. Acceptance Criteria (7 개, PMOAgent 2nd pass)

- **AC-1 (Phase 2 entry scan)**: Given MCT-166 fix LAND 직후, When Phase 2.1 entry scan 실행, Then frozen WAL path / freeze flag 상태 / pre-existing L1 inventory / partial WAL date boundary 가 audit 박제
- **AC-2 (`--backfill` mode)**: Given frozen WAL segment list 입력, When `compactor.runner --backfill --exchange upbit --tier L1 --channel orderbooksnapshot` 실행, Then point-in-time snapshot 출력 + frontmatter manifest partial boundary 박제
- **AC-3 (idempotency)**: Given 동일 backfill job 재실행, When 기존 L1 file 존재, Then `.compacted` rename 후 새 file 생성, source WAL 무변경 (ADR-017 §D2 정합)
- **AC-4 (backfill 실행)**: Given Phase 2.3 backfill trigger, When upbit orderbooksnapshot frozen WAL 전체 처리, Then L1 parquet row count > 0 + `_ob_snapshot_dicts_to_arrow()` 재사용 schema 정합 (MCT-166 path B 정합)
- **AC-5 (MCT-165 verify)**: Given Phase 2.4 verify 단계, When `data_health_check --tier L1 --exchange upbit --date <range>` 실행, Then V2 (L1 row count == 0 violation) = 0
- **AC-6 (별 verify partial loss)**: Given Phase 2.4 별 verify, When frozen WAL row count vs L1 row count 비교, Then partial loss ratio 박제, threshold 초과 시 §10 FIX trigger
- **AC-7 (hub 박제)**: Given Phase 2 완료, When hub PR merge, Then Story §8-§12 + channel matrix MCT-166 fix result update + RETRO 박제

## 5. Invariant (5 개)

- **INV-1**: Source WAL immutability — backfill 중 frozen WAL 무변경 (D3=A PIT)
- **INV-2**: Idempotency — 동일 backfill 반복 실행해도 final state 동일 (D4=A `.compacted` rename)
- **INV-3**: Schema 정합 — backfill L1 schema == MCT-166 path B L1 schema (`_ob_snapshot_dicts_to_arrow()` 재사용)
- **INV-4**: Partial boundary 박제 — frontmatter manifest 가 frozen 시작 ~ MCT-166 LAND 까지 date range 명시 (D5=B)
- **INV-5**: Verify gate — MCT-165 V2=0 AND 별 verify partial loss within threshold 양쪽 통과 후에만 §11 RETRO (D8=C)

## 6. Risk (3 개)

- **R1 (High)**: Phase 2.1 entry scan 결과 frozen WAL path 가 예상과 다름 (MCT-164 wal_freeze.py 실제 동작 미확인) → runner extend 설계 재작업. **완화**: D2=C entry 실측 + Phase 2 단계 분할 (D7=C)
- **R2 (Mid)**: Partial WAL boundary 가 freeze 시각 메타데이터 부재로 추정 불가 → manifest 박제 불완전. **완화**: D5=B manifest 의 best-effort 박제 + INV-4 명시
- **R3 (Mid)**: backfill L1 schema 가 MCT-166 path B 와 미세 차이 (timestamp precision / column order) → downstream MCT-12 backtest reader 호환성 break. **완화**: INV-3 schema 정합 + 단위/통합 test 의무

## 7. Phase 분할

| Phase | 산출물 | wall-clock | PR |
|---|---|---|---|
| Phase 1 | spec + plan + Story §1-§7 + counters title 확장 | 즉시 | mctrader-hub Phase 1 |
| Phase 2.1 (entry scan) | frozen WAL path + freeze flag + pre-existing L1 inventory + partial boundary audit | 즉시 | mctrader-data Phase 2 PR (audit commit) |
| Phase 2.2 (runner extend) | compactor.runner `--backfill` mode + manifest writer + 단위 test | 즉시 | mctrader-data Phase 2 PR (extend commit) |
| Phase 2.3 (backfill 실행) | frozen WAL → L1 parquet 생성 + idempotency 검증 | 즉시 | mctrader-data Phase 2 PR (execute commit) |
| Phase 2.4 (verify) | MCT-165 framework V2=0 + 별 verify partial loss | 즉시 | mctrader-data Phase 2 PR (verify commit) |
| Phase 2 hub | 결과 박제 + channel matrix update + Story §8-§12 + CLAUDE.md + RETRO + Issue close | 즉시 (당일) | mctrader-hub Phase 2 PR |

## 8. scope_manifest 초안

```yaml
planned_adrs:
  amendment: []
  reservation_only: []

planned_files:
  mctrader-data:
    - src/mctrader_data/compactor/runner.py: --backfill mode 추가 (D1=B)
    - src/mctrader_data/compactor/backfill.py: frozen WAL segment iterator + manifest writer (신규, D5=B)
    - scripts/backfill_entry_scan.py: Phase 2.1 entry audit (D2=C, D9=C)
    - scripts/verify_backfill_partial_loss.py: 별 verify 스크립트 (D8=C)
    - tests/unit/compactor/test_backfill.py: idempotency + schema 정합
    - tests/integration/test_backfill_upbit_l1.py: end-to-end backfill
    - docs/audit/MCT-173-entry-scan.md: Phase 2.1 audit 결과
    - CLAUDE.md: §backfill mode 사용법

  mctrader-hub:
    - docs/stories/MCT-173.md: §1-§12
    - docs/superpowers/specs/2026-05-14-MCT-173-upbit-l1-backfill-design.md: spec
    - docs/superpowers/plans/2026-05-14-mct-173-upbit-l1-backfill.md: plan
    - docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md: MCT-166 result update (backfill 결과 박제)
    - docs/retros/RETRO-MCT-173.md: PMO retro
    - CLAUDE.md: §backfill mode + §pending stories
    - .codeforge/counters.json: MCT-173 title 확장

planned_claude_md_sections:
  - mctrader-data CLAUDE.md §backfill mode (compactor.runner --backfill 사용법)
  - mctrader-hub CLAUDE.md §backfill mode + §verify gate (MCT-165 V2=0 + 별 verify 의무)

counters_reservation:
  current: MCT-173  # title 확장
  next_reservation: []  # 본 Story 가 EPIC-data-accumulation-umbrella 종료 후보
```

## 9. Cross-ref

- **MCT-164 §10** (D4=C WAL 복구 verdict 부분가능, source 인용)
- **MCT-165 V2** (verify framework, AC-5)
- **MCT-166 D3=B** (별 Story 분리 결정, 본 Story trigger), **D2=B alternative path B** (`_ob_snapshot_dicts_to_arrow()` 재사용, AC-4 정합)
- **ADR-017 §D2** (`.compacted` rename idempotency, INV-2/AC-3 정합)
- **ADR-017 Amendment 2 (MCT-164)** (compactor source 규약, channel matrix dispatch)
- **ADR-009 §D12** (forward-only invariant, historical materialization 정의)
- **Issue #298** (본 Story trigger)
- **EPIC-data-accumulation-umbrella** (MCT-164/165/166 sibling, 본 Story land 시 EPIC 종료 후보)
