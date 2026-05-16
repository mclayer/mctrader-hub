# RETRO-MCT-189 — ADR-029 §D3=C grace-0 로컬삭제 wiring 완결

> **Story**: MCT-189. **Epic**: EPIC-tier-promotion-single-source carry over (POLICY_FINALIZED 유지, D3 wiring deferred → resolved).
> **Land window**: 2026-05-16 (Phase 1 hub #357 + Phase 2 PR1 data #73) ~ 2026-05-17 (PR2 data #75 + PR3 hub #TBD).

## Outcome

ADR-029 §D3=C "NAS HEAD verify → grace-0 local delete" 정책의 production wiring 완결:

- `promote_l1()` caller 0건 → 3+ caller (DualWriter helper `_promote_after_nas_put` + runner `scan_and_cleanup_legacy` + promotion.py self)
- 4중 HEAD verify (ETag + VersionId + sha256 metadata + ContentLength) + pre-delete guard (race window 차단) + fd-consistent sha256+size (TOCTOU 축소) — silent corruption + race attack surface 4-layer 방어
- DualWriter `status=committed` boundary 안 self-delete + verify-fail → `enqueue_retry()` public method 경유 retry_queue + status="local_only" (caller 0건 재발 + "committed" 거짓 신호 양쪽 차단)
- legacy 130GB retroactive cleanup: `scan_and_cleanup_legacy` + `batch_limit=500` cap + cycle hook (12 tick × 30s ≈ 6분 cadence) → 점진 회수 ~52h (첫 sweep L1 compaction stall 회피)
- ADR-029 §D3 amendment box VERIFIED 박제 (POLICY_FINALIZED 유지, 11/11 D 정상)

## Lessons

### 1. Phase 0 verify lesson **7회째 누적**

MCT-189 §0 Phase 0 evidence — `promote_l1()` 정의 LAND(MCT-169 2026-05-14) vs production caller `git grep src/** = 0건` 의 SSOT drift 가 본 Story trigger. Phase 0 deep-verify 의 **production caller grep ≥1 evidence** 가 정의-only LAND 와 운영 LAND 사이 gap 의 단일 결정적 신호. MCT-170/177/178/179/180/182 lesson 누적 → ADR-032 (Proposed, VERIFIED badge evidence triad) 발의 trigger 정합.

### 2. **decision-defined ≠ caller-wired** — VERIFIED badge 의 evidence triad 의무

ADR-029 §D3 정책 박제(decision-defined) + `promote_l1()` 함수 정의(implementation defined) + `tests/integration/test_l1_local_delete.py` integration test PASS — 3 evidence 만 충족하고 **caller-wired** 가 부재 → "VERIFIED" badge 가 운영 실상과 불일치. ADR-032 evidence triad **(1) file:line + (2) production caller grep ≥1 + (3) integration test PASS** 강제 정합. 본 Story §8.5 Impl Manifest 가 ADR-032 첫 적용 사례.

### 3. **cross-Story PR contamination 패턴 (data #71 MCT-184 ↔ MCT-189)**

본 Story Phase 2 PR1 (#73) 진행 중 mctrader-data origin/main `45e501c feat(MCT-184): data REST API 신규` commit 이 **partial MCT-189 단위 A/B/C/D squash 포함**해 LAND 한 사실 사후 발견. spec/code-quality FIX iter1-3 (retry_queue enqueue P0 + head_5xx 시나리오 + fd-consistent + helper extraction 등) **전부 부재 상태**로 결함 wiring 이 main 일시 도달.

**근본 원인 후보**:
- parallel session 이 동일 working tree (`c:\workspace\mclayer\mctrader-data`) 공유 + branch race (`mct-184-fix1-data-correctness` ↔ `mct-189-phase2-wiring`) — memory `feedback_parallel_session_branch_race` 패턴 3번째 재현. 본 Story 는 hub 측 worktree 격리(`feedback_parallel_session_branch_race` 메모리 정합)했으나 data 측 implementer subagent 가 동일 working tree 공유로 contamination 노출.
- MCT-184 PR review 가 squash 내용물의 cross-Story scope 검증 부재 — D3 wiring 코드(promotion.py/dual_writer.py/nas_uploader.py/integration test)가 MCT-184 PR title("data REST API 신규") 과 무관함에도 통과. PR scope guard 부재.

**처리**:
- mctrader-data 측에도 worktree 격리 (`.claude/worktrees/mct-189-merge`) 신규 + `git rebase origin/main --strategy-option=theirs` 로 FIX iter1-3 적용 버전을 MCT-184 partial 위에 덮어쓰기 + `git push --force-with-lease`
- PR #73 squash merge (de12f43) = production 정합 회복

**ADR-032 self-reference**: 본 사건이 ADR-032 (VERIFIED badge evidence triad) 의 trigger 강화 사례. squash 가 cross-Story commit 을 결함 상태로 옮길 때 evidence triad **(2) production caller grep ≥1** 만으로는 caller 존재 여부만 검증 (call-site 가 spec FIX iter 통과한 정합 코드인지 무판단). caller code 의 spec FIX iter compliance 까지 evidence triad 확장 필요 — ADR-032 §5 expected_sections 보강 권고 (별 governance Story MCT-190 영역).

## ADR 후보 carry / 발의

- **ADR-032** (이미 Proposed, .codeforge/counters.json) — VERIFIED badge evidence triad. owner Story 권고 = MCT-190 (next reservation). 본 Story Phase 2 PR3 §8.5 가 첫 적용 사례.
- (carry) **cross-Story PR scope guard**: PR review 가 commit squash 내 cross-Story 파일 감지 + 별 Story scope 위반 alert. ADR-032 amendment 또는 별 ADR 후보.
- (carry) **parallel session data working tree 공유 race**: memory `feedback_parallel_session_branch_race` 가 hub 만 명시. data/engine/market 측에도 동일 worktree 격리 의무 명시 — PMO 메모리 amendment 후보.

## Carry over to MCT-190 / 후속

- **ADR-032 owner Story 발의** (next reservation MCT-190 권고, status: RESERVED). evidence triad rule + cross-Story PR scope guard 추가.
- **vendor wheel 갱신** (mctrader_market post-market#11 wheel — mctrader-data:pilot Docker build 가능화). 별 follow-up.
- **engine-paper crash loop + signal-announcement/fear-greed Exited(255)** — 본 세션 응급 진단 시 발견, 별 ops chore.
- **WAL 38GB 자연 드레인 monitoring** — backfill stop + ingest_blocker 활성 후 24h gc grace 로 자연 감소 예상. 별 ops chore.

## Pre-LAND vs Post-LAND 검증

| 항목 | pre-LAND | post-LAND |
|------|----------|-----------|
| integration test | testcontainers MinIO 13 시나리오 PASS | ✓ (PR #73 + #75) |
| unit test | 22 신규 PASS | ✓ (PR #73) |
| 회귀 | main baseline 21 failed+3 error → branch 동일 (reviewer 직접 worktree 분리 측정) | ✓ |
| ruff + pyright | 0 violation | ✓ |
| **production 14d 0 violation gate** | LAND 후 시작 | **carry over (2026-05-31 verify)** |
| **legacy 130GB sweep evidence** | LAND 후 자동 trigger | **carry over (~52h 점진, mctrader-data 운영 모니터링)** |

## Key References

- Story: `docs/stories/MCT-189.md`
- spec: `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md`
- plan: `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md`
- domain-knowledge: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`
- PMO retro (SSOT drift 2호 trigger): `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- ADR-029 §MCT-189 amendment box VERIFIED: `docs/adr/ADR-029-tier-promotion-single-source.md`
- EPIC-RESULTS-EPIC-tier-promotion-single-source amendment: §MCT-189 행 + Epic CLOSED prereq prod-5
- LAND: hub #357 (3f138a6) Phase 1 docs / data #73 (de12f43) Phase 2 PR1 / data #75 (a1a8ccf) Phase 2 PR2 / hub #TBD Phase 2 PR3
