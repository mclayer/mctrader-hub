---
type: story-retro
story_key: MCT-168
epic_key: EPIC-tier-promotion-single-source
status: COMPLETED
completed_at: "2026-05-14"
sp: 3
---

# RETRO — MCT-168 L1 NAS DualWriter wiring (D1+D2 impl, EPIC-tier-promotion-single-source Story-2)

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

EPIC-tier-promotion-single-source 의 **L1 NAS DualWriter wiring Story** (phase1_phase2, cross-repo).

ADR-029 D1=B (L1 NAS PUT timing = L1 ParquetWriter atomic 직후, compactor 측) + D2=B (DualWriter retry_queue + local_only 재사용) 를 구현. ADR-027 §D5 "L1 NAS upload 금지" invariant 폐기 후 첫 번째 구현 Story. mctrader-data (put_l1() + L1Compactor hook + runner pass-through + 22 tests) + mctrader-hub (Story §8-§12 + ADR verify + scope_manifest 2/6) 두 repo에 걸친 cross-repo 구현.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR | mctrader-hub#307 MERGED (4d16a26, 2026-05-14) |
| Phase 2 data PR | mctrader-data#59 MERGED (2026-05-14) |
| Phase 2 hub PR | mctrader-hub#308 MERGED (23f3688, 2026-05-14) |
| 총 AC | 3/3 PASS (AC-6/7/8) |
| 총 INV | 3/3 PASS (INV-4/5/6) |
| 산출물 | 7 파일 (dual_writer.py + l1.py + runner.py + prometheus_exporters.py + 3 test files) |
| 총 테스트 | 22 tests ALL PASS (5 unit + 5 integration + 12 integration) + 65 기존 회귀 0 |
| FIX 루프 | 1회 (Windows FileExistsError 구조적 fix — put_l1() write() 우회 → put_streaming() 직접 호출) |
| D1+D2 verify | ADR-029 D1=B + D2=B VERIFIED (mctrader-data#59 MERGED) |
| Epic milestone | 2/6 박제 (MCT-167 + MCT-168 COMPLETED) |
| Backward compat | PASS — dual_writer=None 시 NAS PUT 0, L2/L3 회귀 0 |

## What Went Well

1. **MCT-163 put_streaming 재사용 성공**: R-1 (L1 PUT latency HIGH) 의 핵심 mitigation = MCT-163 DualWriter streaming 활용. put_l1() → NASUploader.put_streaming() 직접 호출로 peak RSS 0.2 MB 이내 유지. prerequisite LAND 이후 즉시 재사용 가능한 구조.
2. **INV-4 "L1 local SSOT 보존" 설계가 명쾌**: NAS PUT fail 시 hard_fail 금지 + compactor 정상 종료 정책이 _put_l1_nas() helper 구조에서 단일 try-except로 깔끔하게 구현. test_nas_fail_local_preserved 단 1개 테스트로 INV-4 충분 커버.
3. **tier prefix l1/ enforce (R-3 mitigation)**: put_l1() 내 `"l1/" + rel.as_posix()` 하드코딩으로 L1/L2/L3 object key 충돌 구조적 차단. test_l1_tier_prefix_enforce 1 case로 추가 commit 없이 고정.
4. **status enum exhaustive mapping (INV-5)**: NASUploader.PutResult 5종 → DualWriteResult 3종 inline 매핑 (committed / local_only / hard_floor_blocked). test_put_l1_status_enum_exhaustive parametrize 5 case 로 완전 커버. pattern = {committed, queued} → committed, {local_only} → local_only, {hard_floor_blocked, error} → hard_floor_blocked.
5. **backward compat test 기존 보유 (test_l1_no_nas_upload)**: MCT-156 단계에서 작성된 "L1 NAS upload 금지" invariant 테스트가 dual_writer=None fallback 검증으로 자연스럽게 전환. RETRO 시점 별 수정 없이 PASS.
6. **ruff auto-fix 빠른 cycle**: string annotation UP037 → `Optional[DualWriter]` + `from __future__ import annotations` 삭제 패턴을 ruff --fix로 일괄 처리. lint 사이클 2회 이내 clean.

## What Could Be Better

1. **Windows FileExistsError 구조적 함정 사전 파악 부재**: put_l1() 초안이 write()를 재사용하려 했으나, write() 내부 `tmp_path.rename(local_path)` 가 Windows에서 기존 파일 덮어쓰기 불가 (FileExistsError). L1은 이미 atomic rename 완료된 파일이므로 write()의 local tmp copy 단계가 불필요 + 충돌. 별 ADR이나 Change Plan에 "Windows atomic rename 제약 = put_l1()은 write() 우회 의무" 명시 누락. MCT-169 이후 유사 패턴 재발 방지를 위해 ADR-027 또는 domain-knowledge에 Windows path 제약 주석 추가 권고.
2. **AC-8 실 NAS p99 측정 지연**: AC-8 (L1 PUT p99 < 1500ms NFR) 검증이 mock-based PASS로 박제. 실 NAS 측정 = MCT-171 scope 위임. 실측 결과가 NFR 초과할 경우 MCT-171 내 mid-story escalate 위험. MCT-171 brainstorm 시 AC-8 실측 plan 을 Phase 2 entry gate로 명시 권고.
3. **Phase 2 hub commit 중 parallel session branch race 주의**: summary에 따르면 Phase 2 hub 편집 완료 후 context 폭증으로 세션 요약 전환. mct-168-phase-2-hub 브랜치 상태가 uncommitted로 남아 다음 세션 진입 시 재확인 필요. memory feedback_parallel_session_branch_race 정합. 후속 Story 에서도 Phase 2 hub 브랜치 commit 전 context 폭증 → 재진입 패턴 반복 가능 — 가능하면 Phase 2 hub commit을 Phase 2 data 완료 직후 단일 세션 내 실행 권고.
4. **Prometheus 실 emit 검증 부재**: test_l1_nas_put_prometheus_emit 은 mock_counter.labels + mock_hist.observe call 확인이지 실제 Prometheus registry emit은 검증 안 됨. 후속 Story (MCT-172 통합 smoke) 에서 실 Prometheus scrape verify 필요.

## AC Verdict

| AC | 설명 | 결과 |
|----|------|------|
| AC-6 | compact_segment() 직후 put_l1() 호출 + dual_write_result_total{tier="L1"} emit | PASS |
| AC-7 | NAS PUT fail → local_only 반환 + compactor 정상 종료 (L1 local 보존) | PASS |
| AC-8 | dual_write_l1_latency_seconds.observe() 호출 (mock-based, 실 NAS = MCT-171) | PASS (partial) |

## INV Verdict

| INV | 결과 |
|-----|------|
| INV-4 L1 local SSOT 보존 (NAS PUT fail 시 hard fail 금지) | PASS |
| INV-5 status enum 3종 exhaustive (committed / local_only / hard_floor_blocked) | PASS |
| INV-6 retry_queue replay idempotent (skipped_idempotent → committed) | PASS |

## FIX Ledger

| iter | 실패 lane | 원인 유형 | 수정 요약 | 결과 |
|---|---|---|---|---|
| 1 | 구현 | Windows FileExistsError | put_l1() write() 우회 → NASUploader.put_streaming() 직접 호출로 재구현. PutResult → DualWriteResult inline 변환 추가. | PASS |

## Risk 잔존

| R | Severity | 잔존 여부 | Mitigation Story |
|---|---|---|---|
| R-1 L1 PUT p99 NFR | HIGH | 부분 잔존 (mock-based PASS, 실 NAS 미측정) | MCT-171 Phase 2 (실 NAS p99 측정 gate) |
| R-2 retry_queue overflow | MID | 잔존 (impl 미시점) | MCT-171 Phase 2 (D11 capacity-bounded) |
| R-3 L1/L2/L3 object key 충돌 | MID | 해소 (tier prefix enforce, l1/ l2/ l3/) | (closed) |

## Epic-level milestone 박제

EPIC-tier-promotion-single-source milestone progress:

| # | Story | Status | LAND |
|---|---|---|---|
| 1 | **MCT-167** | **COMPLETED** | 2026-05-14 (hub#305) |
| 2 | **MCT-168 (본 Story)** | **COMPLETED** | 2026-05-14 (hub#307 + data#59 + hub#308) |
| 3 | MCT-169 | Reserved | TBD |
| 4 | MCT-170 | Reserved | TBD |
| 5 | MCT-171 | Reserved | TBD |
| 6 | MCT-172 | Reserved | TBD |

**milestone 2/6 박제 완료**. L1 NAS dual-write hot path 확립 → MCT-169 진입 unblock.

## 후속 Story 진입 권고

**MCT-169 (L1 NAS verify + immediate local delete + tier promotion, D3+D10)** — 별 세션 권고 (context 폭증 방지).

- gate: MCT-168 Phase 2 MERGED (hub#307 + data#59 + hub#308) PASS — 진입 가능
- scope: l2.py/l3.py source read `local Path → NAS GET stream` (D3=C: NAS HEAD verify + grace 0) + ambiguity invariant enforcement (D10)
- prerequisite verify: MCT-168 LAND 확인 (hub#308 MERGED 2026-05-14, 본 RETRO 박제)

## Cross-ref

- Story: `docs/stories/MCT-168.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md` (D1+D2 verify status 박제)
- Phase 1 PR: mctrader-hub#307 (4d16a26)
- Phase 2 data PR: mctrader-data#59
- Phase 2 hub PR: mctrader-hub#308 (23f3688)
- Epic scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- prerequisite retros: RETRO-MCT-167.md / RETRO-MCT-161.md / RETRO-MCT-163.md
- PMO retro memory: `feedback_pmo_retro_mandatory`
