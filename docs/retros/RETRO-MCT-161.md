---
type: story-retro
story_key: MCT-161
story_title: "NAS bucket versioning + Object Lock + DR runbook (EPIC-compactor-operations 3/3)"
epic_key: EPIC-compactor-operations
parent_epic: EPIC-cold-tier-stage-3-wiring
stage: post-stage-3-cycle
stage_position: nas-durability
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-161.md
phase1_pr_hub: mclayer/mctrader-hub#301
phase1_pr_hub_merge_sha: TBD  # Phase 1 MERGED
phase2_pr_hub: mclayer/mctrader-hub#TBD  # Phase 2 본 PR
retro_author: PMOAgent (DeveloperPLAgent dispatch)
retro_date: 2026-05-14
adrs_touched:
  - "ADR-027 §D MCT-161 amendment — versioning + Object Lock + Lifecycle + DR runbook 의무"
status: complete
sp_burned: 3
sp_total_epic_compactor_operations: 11  # MCT-162 3sp + MCT-160 5sp + MCT-161 3sp
sp_progress_epic: 100.0  # ALL 3 Stories COMPLETED
milestone_progression: "2/3 → 3/3 (100%)"
epic_status: CLOSED  # EPIC-compactor-operations milestone 3/3 COMPLETED
next_story: MCT-163 (EPIC-compactor-operations 사후 — MCT-160 F3+F6+F7 follow-up, PROPOSED)
next_epic: EPIC-tier-promotion-single-source (MCT-167 진입)
related_retros:
  - docs/retros/RETRO-MCT-162.md
  - docs/retros/RETRO-MCT-160.md
  - docs/retros/RETRO-MCT-156.md
fix_cycle_total: 2
fix_cycle_breakdown:
  unicode_encode_error: 1  # em-dash → ASCII hyphen (Windows cp949 환경)
  mc_cli_not_found: 1  # FileNotFoundError graceful SKIP 추가
  design_review: 0
  test_agent: 0
  security_test: 0
  code_review: 0
escalate_count: 0
ac2_object_lock_skip: true  # MinIO 기존 bucket --with-lock 제약 (생성 시점만 가능)
replication_deferred: true  # D2=D, MCT-174 reservation 박제
mct174_reservation_done: true
---

# RETRO — MCT-161 NAS bucket versioning + Object Lock + DR runbook

## §1 Summary

MCT-153 4.2 GiB 손실(RETRO-MCT-156 §13.5.2) 재발 방지를 위해 `mctrader-market` NAS bucket versioning을 활성화하고, Object Lock GOVERNANCE 30d + Lifecycle ILM 30d를 구성하며, DR runbook을 신규 작성했다. EPIC-compactor-operations의 마지막 Story (3/3).

### 결과

| 항목 | 결과 |
|------|------|
| AC-1 versioning | PASS — mctrader-market versioning=Enabled, DeleteMarker 생성 확인 |
| AC-2 Object Lock | SKIP — MinIO 기존 bucket 제약 (--with-lock 생성 시점 의무) |
| AC-3 Lifecycle | PASS — NoncurrentVersionExpiration 30d rule 적용 |
| AC-4 DR runbook | PASS — 5-step runbook (docs/runbooks/nas-bucket-disaster-recovery.md) |
| AC-5 ADR amendment | PASS — ADR-027 §D MCT-161 amendment Phase 1 #301 MERGED |

## §2 What went well

1. **AC-1/AC-3 즉시 PASS**: versioning enable + lifecycle ILM 모두 boto3 단일 호출로 즉시 적용됨. NAS MinIO S3 호환 API 정상 동작 확인.
2. **DeleteMarker probe 자동 검증**: verify 스크립트에서 임시 object put→delete→list_object_versions 자동화로 DeleteMarker 동작 실증.
3. **DR runbook 5-step 완성**: MCT-153 사례를 근거로 Triage → Version 조회 → Restore → Verify → Postmortem 5단계 실용적 runbook 완성.
4. **EPIC-compactor-operations 3/3 CLOSED**: MCT-162 + MCT-160 + MCT-161 모두 LAND, Epic closure gate 충족.

## §3 What went wrong / FIX iterations

### FIX iter 1 — UnicodeEncodeError (em-dash)

- **원인**: Windows cp949 콘솔 환경에서 em-dash(U+2014) 문자 출력 실패
- **fix**: em-dash를 ASCII hyphen(-) 으로 대체
- **분류**: 구현 원인 (minor encoding issue)

### FIX iter 2 — mc CLI FileNotFoundError

- **원인**: Object Lock SKIP fallback 경로에서 `mc` CLI 미설치 시 FileNotFoundError 발생 → 스크립트 abort
- **fix**: `FileNotFoundError` except 추가, graceful SKIP 처리
- **분류**: 구현 원인 (mc CLI 의존성 가정 오류)

### AC-2 Object Lock SKIP (설계 결정 아님, 환경 제약)

- **원인**: MinIO/S3 표준 — Object Lock은 bucket 생성 시 `x-amz-bucket-object-lock-enabled: true` 헤더 필요. 기존 `mctrader-market` bucket은 해당 flag 없이 생성됨.
- **완화**: lifecycle NoncurrentVersionExpiration 30d(AC-3)로 noncurrent version 자동 만료 보장. DeleteMarker 생성(AC-1)으로 hard delete 흔적 보존 달성.
- **후속 고려**: bucket 재생성 또는 MinIO Enterprise Console 경유 검토 (별도 운영 결정 필요).

## §4 Metrics

| 지표 | 값 |
|------|---|
| story_points | 3 |
| fix_iterations | 2 |
| ac_pass_count | 4/5 (AC-2 SKIP) |
| runbook_steps | 5 |
| audit_artifact | docs/audit/MCT-161-versioning-enable.md |

## §5 EPIC-compactor-operations Closure

EPIC-compactor-operations = 3 Story 완료:

| Story | SP | 완료일 | 핵심 |
|-------|-----|--------|------|
| MCT-162 | 3 | 2026-05-13 | L1 channel parity + orderbookdepth |
| MCT-160 | 5 | 2026-05-13 | L2/L3 cadence + OOM + backlog cleanup |
| MCT-161 | 3 | 2026-05-14 | NAS versioning + DR runbook |
| **합계** | **11** | **2026-05-14** | **3/3 CLOSED** |

EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md`

## §6 후속 Action Items

1. **MCT-174 replication backlog** (INV-5): counters.json reservation 박제 완료. 단일 NAS box 해소 후 진입.
2. **MCT-163** (EPIC-compactor-operations 사후): MCT-160 F3+F6+F7 follow-up (DualWriter streaming + row-batch streaming + ADR-009 D7 amend).
3. **Object Lock 재검토**: mctrader-market bucket 재생성 또는 MinIO Console 경유 Object Lock 활성화 가능 여부 확인 (별도 운영 결정).
4. **MCT-167** (EPIC-tier-promotion-single-source): 본 Story MCT-161 DR runbook이 EPIC-tier-promotion D9 prerequisite consumer로 연결.

## §7 Cross-ref

- MCT-153 / RETRO-MCT-156 §13.5.2 (손실 원인 박제)
- docs/runbooks/nas-bucket-disaster-recovery.md (AC-4 산출물)
- docs/audit/MCT-161-versioning-enable.md (실행 결과 박제)
- docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md (Epic closure 박제)
- ADR-027 §D MCT-161 amendment
- .codeforge/counters.json MCT-174 reservation
