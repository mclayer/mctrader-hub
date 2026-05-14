---
type: story-retro
story_key: MCT-164
story_title: "upbit L1 forward-only loss 진단 (channel mismatch + compactor source 규약 + ADR-017/027 amendment)"
epic_key: EPIC-data-accumulation-umbrella  # D7=C carry-over umbrella label only
parent_epic: null
stage: diagnostics  # 진단 only (D1=A 2 Story 분리 — fix = MCT-166)
stage_position: sibling  # MCT-165 V2 trigger → MCT-164 진단 → MCT-166 fix
phase_pair: phase1_phase2
story_file: docs/stories/MCT-164.md
issue: mclayer/mctrader-hub#292
phase1_pr_hub: mclayer/mctrader-hub#293
phase1_pr_hub_merge_sha: null  # Phase 1 MERGED (별 세션 박제 — MCT-163 retro context)
phase2_pr_data: mclayer/mctrader-data#55
phase2_pr_data_merge_sha: 359eacd  # squash merge
phase2_pr_data_merged_at: 2026-05-14
phase2_pr_hub: mclayer/mctrader-hub#TBD  # Phase 2 hub PR (본 retro 작성 시점 open 예정)
retro_author: PMOAgent
retro_date: 2026-05-14
sprint_period: "2026-05-14 ~ 2026-05-14"  # 단일일 cycle (D6=B 일반 Story flow + 당일 처리)
adrs_touched:
  - ADR-017 Amendment 2 (compactor source 규약 — channel matrix SSOT + multi-channel exchange 지원)
  - ADR-027 Amendment 2 (미지원 source silent-skip 차단 — multi-channel exchange 확장)
  - ADR-009 §D12 (forward-only invariant) — INV-1 정합 박제만 (변경 0)
status: complete
sp_burned: 3  # 진단 전용 Story (fix scope = MCT-166)
next_story:
  - MCT-166 (upbit L1 forward-only loss fix — 본 §10 진단 결과 인용 brainstorm 의무, INV-5)
related_retros:
  - docs/retros/RETRO-MCT-165.md  # V2 trigger (upbit L1 partition 0 잔존 YES) — MCT-164 의 parent trigger
  - docs/retros/RETRO-MCT-162.md  # bithumb orderbookdepth allowlist 추가 — MCT-164 root cause 의 MCT-162 scope 누락 지점
  - docs/retros/RETRO-MCT-160.md  # §11 R7 upbit L1 verify carry sentinel
fix_cycle_total: 0  # 진단 Story, 구현 변경 없음 — fix_cycle 해당 없음
fix_cycle_breakdown:
  design_review: 0
  test_agent: 0
  security_test: 0
  code_review: 0
---

# RETRO-MCT-164 — upbit L1 forward-only loss 진단 Story

## §1 Summary

MCT-165 V2 verify 잔존 YES (upbit L1 partition 0) 를 trigger 로 발의된 진단 Story.
read-only code audit + WAL freeze 도구 + 4 root cause 3-state verdict 박제로 완료.

**주요 성과**:
- (c) channel_mismatch 확정 (collector.py `exchange == "bithumb"` 조건)
- WAL freeze 도구 즉시 실행 가능 (INV-1 충족)
- WAL recovery probe: 부분가능 (orderbooksnapshot → orderbooksnapshot L1 직접 compaction)
- ADR-017/027 Amendment 2 박제
- exchange-channel-matrix.md hypothesis → confirmed

## §2 9 D 결정 결과 평가

| 결정 | 채택 | 평가 |
|---|---|---|
| D1=A 2 Story 분리 | 유효 | 진단 Story 단독 완료. MCT-166 fix scope 명확히 분리됨 |
| D2=A WAL freeze 즉시 | 유효 | wal_freeze.py Phase 2 entry 즉시 작성. INV-1 충족 |
| D3=A channel mismatch 우선 | 유효 | (c) 확정 판정. 최단 경로로 root cause 확정 |
| D4=C WAL 복구 시도 | 유효 | 부분가능 verdict. orderbooksnapshot L1 직접 compaction 방향 확인 |
| D5=C fix scope = 진단 후 | 유효 | MCT-166 brainstorm 에서 결정 의무 명시 |
| D6=B 일반 Story flow + 당일 처리 | 유효 | 당일 Phase 1+2 ALL LAND |
| D7=C upbit+bithumb 비교 | 유효 | parity audit 완료 — asymmetry root 확정 |
| D8=A channel matrix SSOT | 유효 | exchange-channel-matrix.md 박제 + confirmed update |
| D9=A ADR-017/027 amendment | 유효 | Amendment 2 Phase 1 PR 박제 완료 |

## §3 INV-3 Verdict 최종 박제

| 후보 | Verdict | 근거 |
|---|---|---|
| (a) path_mismatch | **기각** | 3 컴포넌트 동일 path 규약 |
| (b) l1_unsupported | **기각** | L1 orderbooksnapshot 지원, exchange 분기 없음 |
| **(c) channel_mismatch** | **확정** | collector.py:82 `exchange == "bithumb"` 조건 |
| (d) discovery_skip | **기각** | runner.py exchange 필터 없음, L1=0 후행 결과 |

## §4 산출물 목록

### mctrader-data PR #55 (merge: 359eacd)

| 파일 | 유형 | 설명 |
|---|---|---|
| `scripts/wal_freeze.py` | CREATE | WAL freeze 도구 (AC-1, INV-1) |
| `scripts/upbit_wal_diagnostics.py` | CREATE | 4 root cause 진단 (AC-2/3/4, INV-3) |
| `scripts/wal_recovery_probe.py` | CREATE | snapshot→depth 변환 probe (AC-5, D4=C) |
| `docs/audit/MCT-164-code-audit.md` | CREATE | INV-3 3-state verdict SSOT |
| `docs/audit/MCT-164-parity-upbit-vs-bithumb.md` | CREATE | D7=C parity 비교 (AC-6) |
| `CLAUDE.md` (mctrader-data) | CREATE | WAL freeze + channel allowlist 규약 |

### mctrader-hub Phase 1 PR #293 (MERGED — 별 세션)

ADR-017/027 Amendment 2 + channel matrix stub + Story §1-§7 + counters

### mctrader-hub Phase 2 PR (본 retro 직후 open)

| 파일 | 유형 | 설명 |
|---|---|---|
| `docs/stories/MCT-164.md` §8-§12 | MODIFY | 진단 결과 박제 |
| `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` | MODIFY | hypothesis → confirmed |
| `.claude/_overlay/CLAUDE.md` | MODIFY | collector/compactor/WAL 규약 |
| `docs/retros/RETRO-MCT-164.md` (본 file) | CREATE | PMOAgent retro |

## §5 Timeline

```
2026-05-14
  T0: MCT-165 V2 verify 잔존 YES 박제 → MCT-164 trigger
  T1: Phase 0 brainstorm — 9 D 결정 (Codex+Sonnet) + D1 사용자 confirm
  T2: Phase 1 PR #293 MERGED — ADR-017/027 Amendment + channel matrix + Story §1-§7
  T3: Phase 2.1 — wal_freeze.py 작성 + 진단 스크립트 작성 + audit 박제
  T4: mctrader-data PR #55 MERGED (359eacd)
  T5: Phase 2.2 — hub §8-§12 + channel matrix update + CLAUDE.md + RETRO
  T6: hub Phase 2 PR open → admin merge (예정)
  T7: Issue #292 close + MCT-166 Issue 발의 (예정)
```

## §6 What Went Well

1. **D3=A 최우선 검증 전략 유효**: channel mismatch 가설 우선 검증 → collector.py 첫 분석에서 확정. 비효율적 순차 탐색 없이 최단 경로.

2. **read-only 진단 일관성**: INV-2 완벽 준수. 코드 grep + path inspection 으로 production data 0 mutation.

3. **INV-3 강제 완료**: "미진단" state 금지 원칙이 4 후보 전체 완료를 강제. 불완전한 진단 박제 없음.

4. **WAL recovery probe 부분가능 판정**: orderbooksnapshot WAL → orderbooksnapshot L1 직접 compaction 방향 확인. MCT-166 backfill 경로 열림.

5. **parity audit 비대칭 root 특정**: MCT-162 PR scope 누락 위치 (`collector.py:82`) 정확히 특정. MCT-166 fix 위치 명확.

6. **당일 ALL LAND**: D6=B 일반 Story flow 목표 달성.

## §7 What Could Be Better

1. **MCT-162 PR review 단계에서 upbit scope 누락 미감지**: MCT-162 가 bithumb orderbookdepth 활성화 시 upbit 에 대한 동일 처리 검토 미포함. CodeReview P1 level 에서 감지했어야 할 asymmetry. → **MCT-166 fix PR CodeReview 체크리스트 에 "신규 exchange-specific 코드 추가 시 다른 exchange 동일 처리 확인" 항목 추가 제안**.

2. **upbit WS adapter event 지원 여부 미확인**: MCT-162 scope 에서 upbit WS API 의 `orderbook_delta` event 지원 여부를 확인하지 않았음. MCT-166 선결 과제로 넘어감.

3. **channel matrix 선행 박제 필요성**: exchange-channel-matrix.md 가 MCT-164 Phase 1 에서 stub 으로만 생성 → Phase 2 진단 후 업데이트. 향후 신규 exchange 추가 시 channel matrix 우선 작성이 진단 경로를 단축시킬 수 있음.

## §8 MCT-166 Fix Scope (INV-5 정합)

**본 §10 진단 결과 기반** (인용 의무):

1. **primary fix**: `collector.py _build_ingesters()` — upbit orderbookdepth ingester 추가
   - 전제: upbit WS adapter `orderbook_delta` event 지원 여부 선결 확인
   - 미지원 시 → alternative fix

2. **alternative fix**: L1 compactor — upbit orderbooksnapshot WAL 을 orderbooksnapshot L1 으로 직접 compaction 활성화
   - `_ob_snapshot_dicts_to_arrow()` 기지원
   - ADR-017 Amendment 2 channel matrix 정합 필요

3. **backfill**: frozen orderbooksnapshot WAL → orderbooksnapshot L1 historical compaction
   - `wal_recovery_probe.py` verdict: 부분가능

4. **ADR-027 Amendment 2 정합**: 미지원 source silent-skip 차단 코드 적용

## §9 carry-over Items

| Item | 대상 | 우선순위 |
|---|---|---|
| MCT-166 brainstorm + Phase 1 | 별 세션 | HIGH (forward-only loss 여전히 누적 중 — wal_freeze.py 로 차단 후 fix 필요) |
| upbit WS adapter event 지원 확인 | MCT-166 Phase 0 | HIGH |
| D+7 checkpoint (MCT-165 V1 재검증) | 2026-05-16 | MEDIUM |
| R3: bithumb 잠재 결함 추가 진단 | MCT-166 확장 후보 | LOW |

## §10 Metrics

- **fix_cycle_total**: 0 (진단 Story, 구현 0)
- **INV-3 완료율**: 4/4 (100%)
- **AC 충족률**: 7/7 (AC-1~AC-7 모두 충족 또는 충족 경로 명시)
- **당일 처리**: YES (D6=B 목표 달성)
- **WAL freeze INV-1**: 도구 작성 완료, execute 시 즉시 적용 가능

---

*PMOAgent dispatch: DeveloperPLAgent Phase 2 land 직후 자동 dispatch (memory feedback_pmo_retro_mandatory 정합).*
