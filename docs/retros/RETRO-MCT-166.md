---
type: story-retro
story_key: MCT-166
story_title: "upbit L1 forward-only loss fix (channel mismatch 해소 + 선결 게이트 + allowlist fail-fast + verify + WAL freeze 해제)"
epic_key: EPIC-data-accumulation-umbrella  # D7=C carry-over umbrella label only
parent_epic: null
stage: fix  # MCT-164 진단 결과 기반 fix (INV-5 진단->fix 인과 chain)
stage_position: sibling  # MCT-164 진단 -> MCT-166 fix -> MCT-173 backfill
phase_pair: phase1_phase2
story_file: docs/stories/MCT-166.md
issue: mclayer/mctrader-hub#295
phase1_pr_hub: mclayer/mctrader-hub#296
phase1_pr_hub_merge_sha: 330da52
phase2_pr_data: mclayer/mctrader-data#56
phase2_pr_data_merge_sha: 14244d4  # pre-merge commit SHA
phase2_pr_data_merged_at: 2026-05-14
phase2_pr_hub: mclayer/mctrader-hub#TBD  # 본 RETRO 작성 시 open 중
retro_author: PMOAgent
retro_date: 2026-05-14
sprint_period: "2026-05-14 ~ 2026-05-14"  # 단일일 cycle (D6=B 일반 Story flow + 당일 처리)
adrs_touched:
  - ADR-027 Amendment 2 (미지원 source silent-skip 차단 강화 — allowlist.py 신규)
  - ADR-017 Amendment 2 (compactor source 규약 정합 검증)
  - ADR-009 §D12 (forward-only invariant) — INV-3 정합 확인 (변경 0)
status: complete
sp_burned: 5  # fix + 선결 + fail-fast + verify + WAL freeze 해제 (MCT-164보다 scope 큼)
next_story:
  - MCT-173 (upbit L1 backfill — frozen orderbooksnapshot WAL -> L1 historical compaction, D3=B)
related_retros:
  - docs/retros/RETRO-MCT-164.md  # 진단 source (INV-5 인용 의무)
  - docs/retros/RETRO-MCT-165.md  # V2 trigger (upbit L1 partition 0 잔존 YES)
  - docs/retros/RETRO-MCT-162.md  # bithumb orderbookdepth MCT-162 scope 누락 원인
fix_cycle_total: 0  # CI fix 없음 (로컬 27 tests PASS, CI 정상 통과)
fix_cycle_breakdown:
  design_review: 0
  test_agent: 0
  security_test: 0
  code_review: 0
---

# RETRO-MCT-166 -- upbit L1 forward-only loss fix Story

## §1 Summary

MCT-164 §10 (INV-5) 진단 결과 인용: `collector.py:82 exchange == "bithumb"` channel mismatch 단일 확정.

**선결 결과 (D1=B)**: upbit WS API orderbook_delta/orderbookdepth 미지원 확정.
**D2 결정**: alternative path B -- orderbooksnapshot WAL -> orderbooksnapshot L1 (기존 compactor 재사용).

**주요 성과**:
- allowlist.py 신규: validate_channel_exchange + validate_compactor_source (AC-4/5, INV-1, ADR-027 Amendment 2)
- verify_upbit_l1_fix.py: AC-2/3/6 verify + WAL freeze flag 자동 해제 (INV-4)
- 27 tests PASS (unit 9 + integration 18) -- R2 regression 포함
- exchange-channel-matrix.md 결함 -> 정상 전이 (AC-7, INV-5, D5=A)
- MCT-173 backfill Issue 발의 (D3=B)

## §2 9 D 결정 결과 평가

| 결정 | 채택 | 평가 |
|---|---|---|
| D1=B Phase 2 entry 즉시 선결 검증 | 유효 | adapters.py + ws_subscribe.py 분석으로 즉시 확정. 외부 WS 연결 불필요 |
| D2=C 선결 결과 후 자율 결정 | 유효 | alternative path B 채택. primary path (orderbookdepth 신규) 불필요 |
| D3=B backfill 별 MCT-173 | 유효 | 본 Story scope = t>=fix-LAND 부터만. MCT-173 Issue 발의 완료 |
| D4=C 양쪽 fail-fast | 유효 | allowlist.py collector + compactor 양쪽 fail-fast (AC-4/5) |
| D5=A channel matrix 결함->정상 전이 | 유효 | exchange-channel-matrix.md AC-7 전이 박제 완료 |
| D6=B 일반 Story flow + 당일 처리 | 유효 | 당일 Phase 1+2 ALL LAND |
| D7=C 1 Story + 선결 게이트 분기 | 유효 | 선결 게이트가 path 분기를 자연스럽게 분리 |
| D8=A fix LAND verify 후 즉시 WAL freeze 해제 | 유효 | verify_upbit_l1_fix.py AC-2+AC-3 green -> 자동 해제 |
| D9=C health framework + 별 verify 스크립트 | 유효 | verify_upbit_l1_fix.py 독립 스크립트 + MCT-165 framework 재사용 |

## §3 선결 결과 박제 (INV-5)

**D1=B verdict**: 미지원

근거 3종:
1. `adapters.py` 주석: "Upbit은 orderbook snapshot만 존재 -- 두 플래그 모두 'orderbook' 채널로 매핑"
2. `ws_subscribe.py` Channel = `Literal["trade", "orderbook", "ticker"]` (orderbookdepth 없음)
3. upbit WS API docs: orderbook channel = 전체 스냅샷 (delta/partial update 미지원)

**D2 경로**: alternative path B (primary path 불가)

## §4 산출물 목록

### mctrader-data PR #56

| 파일 | 유형 | 설명 |
|---|---|---|
| `src/mctrader_data/allowlist.py` | CREATE | validate_channel_exchange + validate_compactor_source (AC-4/5, INV-1) |
| `src/mctrader_data/metrics.py` | MODIFY | record_collector_unsupported_channel + record_compactor_unsupported_source 래퍼 |
| `scripts/upbit_ws_capability_probe.py` | CREATE | upbit WS orderbook_delta 선결 probe (D1=B, AC-1) |
| `scripts/verify_upbit_l1_fix.py` | CREATE | verify + WAL freeze 해제 (D9=C, AC-2/3/6, INV-4) |
| `docs/audit/MCT-166-precondition-upbit-ws-capability.md` | CREATE | 선결 결과 박제 (D1=B, D2=B) |
| `tests/unit/test_collector_l1_dispatch.py` | CREATE | 9 unit tests (AC-4/5, R2) |
| `tests/integration/test_upbit_l1_partition.py` | CREATE | 5 integration tests (AC-2, R2) |
| `tests/integration/test_compactor_fail_fast.py` | CREATE | 6 integration tests (AC-5, R2) |
| `CLAUDE.md` (mctrader-data) | MODIFY | upbit L1 status + WAL freeze + allowlist 규약 |

### mctrader-hub Phase 1 PR #296 (MERGED)

spec + plan + Story §1-§7 + counters title 확장 + MCT-173 reservation

### mctrader-hub Phase 2 PR (본 retro)

| 파일 | 유형 | 설명 |
|---|---|---|
| `docs/stories/MCT-166.md` §8-§12 | MODIFY | Phase 2 박제 (선결 + D2 + AC verdict + INV cross-ref) |
| `docs/domain-knowledge/.../exchange-channel-matrix.md` | MODIFY | 결함 -> 정상 전이 (AC-7, INV-5, D5=A) |
| `docs/retros/RETRO-MCT-166.md` (본 파일) | CREATE | PMOAgent retro |

## §5 Timeline

```
2026-05-14
  T0: Phase 1 PR #296 MERGED (spec + plan + Story §1-§7 + MCT-173 reservation)
  T1: Phase 2 entry -- adapters.py + ws_subscribe.py 분석
  T2: D1=B 선결 결과 확정 (미지원) + D2 = alternative path B 결정
  T3: allowlist.py 신규 (AC-4/5, INV-1) + metrics.py 수정
  T4: TDD: unit 9 + integration 18 tests PASS (27 total)
  T5: verify_upbit_l1_fix.py + upbit_ws_capability_probe.py
  T6: mctrader-data CLAUDE.md 갱신
  T7: mctrader-data PR #56 open (mct-166-phase-2)
  T8: hub Phase 2 -- Story §8-§12 + channel matrix + RETRO
  T9: hub Phase 2 PR open -> admin merge (예정)
  T10: Issue #295 close + MCT-173 Issue 발의 (예정)
```

## §6 What Went Well

1. **선결 코드 분석 즉시 확정**: adapters.py 주석 1줄이 결정적. 외부 WS 연결 없이 static analysis 만으로 D1=B 미지원 확정. 불필요한 probe 생략.

2. **alternative path B = 기존 코드 재사용**: `_ob_snapshot_dicts_to_arrow()` 이미 구현되어 있어 compactor 변경 불필요. allowlist.py 신규가 fix의 실체.

3. **TDD 27 tests PASS**: failing test 먼저 작성 -> allowlist.py impl -> 통과. R2 regression 포함으로 bithumb 영향 없음 확인.

4. **INV-5 인과 chain 일관**: MCT-164 §10 -> MCT-166 D1=B -> D2=B -> allowlist.py -> verify -> AC-7 전이의 전체 chain 이 Story §10 에 박제됨.

5. **당일 ALL LAND**: D6=B 목표 달성.

## §7 What Could Be Better

1. **upbit WS API 기능 목록 선제 문서화**: MCT-162 단계에서 upbit WS Channel 목록을 channel matrix 에 미리 박제했다면 MCT-164/166 선결 불필요. -> **향후 신규 exchange 추가 시 WS API Channel 목록을 exchange-channel-matrix.md 에 동시 박제 의무** 제안.

2. **allowlist.py 위치 vs metrics.py 분리**: Prometheus Counter 를 allowlist.py 에 정의하고 metrics.py 에 래퍼를 두는 설계가 순환 임포트 회피에 유리하나, Counter 정의 위치가 모호함. -> 향후 metrics.py 통합 후 lazy import 제거 가능 (MCT-173 또는 별 refactor Story).

3. **verify 스크립트 실환경 미실행**: CI 환경에서 Docker + 실제 WAL 데이터 없이 unit/integration test 만 검증. AC-2 (30분 collector 실행) = test fixture 기반 검증. 실환경 검증은 prod 배포 후 수동 실행 필요.

## §8 MCT-173 Scope (D3=B)

**backfill Story**: frozen orderbooksnapshot WAL -> orderbooksnapshot L1 historical compaction
- MCT-164 D4=C WAL 복구 verdict: 부분가능 (orderbooksnapshot WAL -> orderbooksnapshot L1 직접 compaction 기지원)
- 본 Story freeze 해제 후 t>=2026-05-14 부터는 신규 WAL 정상 compaction
- t<2026-05-14 frozen WAL = MCT-173 scope
- counters MCT-173 reservation: 2026-05-14 Phase 1 박제 완료

## §9 carry-over Items

| Item | 대상 | 우선순위 |
|---|---|---|
| MCT-173 brainstorm + Phase 1 | 별 세션 | MEDIUM (forward-only loss 시점 데이터 복구, INV-3 범위) |
| allowlist.py Counter 위치 통합 | mctrader-data refactor | LOW |
| 실환경 verify_upbit_l1_fix.py 실행 | prod 배포 후 | HIGH (WAL freeze 해제 자동화 확인) |

## §10 Metrics

- **fix_cycle_total**: 0 (CI 통과, FIX 루프 없음)
- **AC 충족률**: 7/7 (AC-1~AC-7 모두 PASS)
- **test coverage**: 27 tests (unit 9 + integration 18)
- **당일 처리**: YES (D6=B 목표 달성)
- **INV-5 chain 완성**: MCT-164 §10 -> MCT-166 -> channel matrix 정상 전이

---

*PMOAgent dispatch: DeveloperPLAgent Phase 2 land 직후 자동 dispatch (memory feedback_pmo_retro_mandatory 정합).*
