# Stage 2 종료 운영 Runbook (MCT-155 — Stage 2 EPIC CLOSED gate)

**Authored**: 2026-05-13 (Stage 2 마지막 Story MCT-155)
**Author**: ArchitectPLAgent (chief synthesizer)
**Source**: `scope_manifests/EPIC-cold-tier-nas-minio.yaml` + Stage 2 brainstorm spec §4.4

본 runbook = Stage 2 EPIC CLOSED gate 의 운영 절차 + 6 AC 종합 verify checklist + GC/rotation/TLS 절차 박제.

---

## §1 Stage 2 EPIC CLOSED gate 6 AC 종합 verify checklist

본 checklist 통과 시 Epic milestone #4 CLOSED trigger:

### AC-1 (76GB cold L2 NAS 이관 + byte identity)

- [ ] MCT-153 BackfillOrchestrator 실 운영 완료 verify
- [ ] 7종 invariant ALL PASS evidence pack 박제 (`mctrader-data/.tmp/evidence-pack-MCT-153.md`)
- [ ] NAS 측 76GB object count + size sum verify
- [ ] backfill metric `nas_backfill_*` final value 박제

### AC-2 (신규 L2 100% NAS write — 7d grace 누적)

- [ ] MCT-152 dual_write_window_runner cron 결과 (7d 동안 daily verify ALL PASS)
- [ ] Prometheus metric `nas_write_ratio == 1.0` for 7d 누적 evidence
- [ ] MCT-154 endpoint_router 7d grace 만료 evidence (`engine_dual_write_grace_remaining_days == 0`)

### AC-3 (Local L2 GC 후 free disk > 50%) — **MCT-155 direct owner**

- [ ] CutoverVerifier `verify_rpo_zero()` status == `rpo_zero_verified` 박제
- [ ] GcRunner pre-check 3중 lock ALL PASS:
  - cutover RPO=0 verify evidence file = rpo_zero_verified
  - 7d grace 만료 evidence file = remaining_days == 0
  - invariant ALL PASS 7일 누적 evidence file = pass_days >= 7
- [ ] dry-run 결과 review (operator manual gate, 24h interval)
- [ ] 실 삭제 진입 (`gc_runner.gc(tier="L2", dry_run=False)` → status == `executed`)
- [ ] df -h before/after diff = free disk > 50% (목표 ~70%)
- [ ] deletion log file 박제 (sqlite-WAL persistent)

### AC-4 (7종 invariant ALL PASS §10 박제)

- [ ] MCT-151 InvariantHarness 7종 invariant 박제 verify
- [ ] MCT-153 backfill 측 7종 invariant ALL PASS evidence
- [ ] MCT-155 RPO=0 verify 측 7종 invariant ALL PASS evidence cross-reference
- [ ] ADR-027 D6 amendment commit (3종 → 7종 명시화) — 본 Story Phase 2 산출물

### AC-5 (backfill resumability — 50% 중단 → 재개 → 100%)

- [ ] MCT-153 chaos test report (RETRO-MCT-153.md)
- [ ] BackfillOrchestrator checkpoint resumability evidence
- [ ] retro 별 file (`docs/retros/2026-05-stage2.md`) cross-reference

### AC-6 (TLS 재검토 회고 박제) — **MCT-155 direct owner**

- [ ] `docs/runbooks/nas-minio-tls-review.md` 신규 land 확인
- [ ] 사용자 confirm = HTTP 유지 결정 verbatim 인용
- [ ] ADR-027 D2 amendment commit 확인
- [ ] scope_manifest `triggers_adr_amendment.adr=ADR-027.section=D2.status` = committed

---

## §2 GC 진입 절차 (AC-3 owner — MCT-155 GcRunner)

### §2.1 Pre-GC checklist (3중 lock unconditional)

```bash
# Step 1: cutover RPO=0 verify (S8)
python scripts/migration/verify_rpo_zero.py \
    --cutover-timestamp <CUTOVER_TIMESTAMP_ISO> \
    --output /tmp/rpo-zero-verify-MCT-155.md \
    --json-output /tmp/rpo-zero-verify-MCT-155.json

# Expected: exit code 0 (rpo_zero_verified)
# 만약 exit code 1 (drift_detected) → cutover rollback signal emit (operator manual gate)
# 만약 exit code 2 (verify_inconclusive) → NAS 복구 후 재시도
```

### §2.2 Dry-run (실 삭제 전 의무, D7 박제)

```bash
# Python CLI / programmatic invocation:
from mctrader_data.nas_migration.gc_runner import GcRunner
# ... (CutoverVerifier + InvariantHarness inject)

result = gc_runner.gc(tier="L2", dry_run=True)
print(f"status={result.status}")
print(f"deletion_targets count={len(result.deletion_targets)}")
print(f"target_size_bytes={result.target_size_bytes}")

# Expected: status='dry_run_complete'
# 만약 status='blocked_grace_period' → grace 만료 후 재시도
# 만약 status='blocked_invariant_fail' → invariant fix 후 재시도
```

### §2.3 24h batch delete window (operator manual gate)

**의무**: dry-run + 실 삭제 사이 **24h interval** 박제 (R5 mitigation):
- dry-run 결과 deletion_targets list 검토 (사용자 review)
- 24h 안에 실수 발견 시 deletion log 기반 NAS object download + local 복원 가능
- 24h 경과 후 실 삭제 진입 가능

### §2.4 실 삭제 진입

```bash
# After 24h batch delete window:
result = gc_runner.gc(tier="L2", dry_run=False)
print(f"status={result.status}")
print(f"deleted_count={result.deleted_count}")
print(f"freed_bytes={result.freed_bytes}")
print(f"free_disk_pct_after={result.free_disk_pct_after:.2f}%")

# Expected: status='executed' + free_disk_pct_after > 50%
```

### §2.5 GC 완료 evidence 박제

- evidence pack: `mctrader-data/.tmp/gc-evidence-MCT-155.md` (gitignored)
- df -h before/after diff 박제
- deletion log file 보존 (sqlite-WAL `mctrader-data/.tmp/gc-deletion-log-MCT-155.db`)

---

## §3 Secret Rotation 절차 (AC-3 — 90d 첫 cycle)

### §3.1 Normal rotation cycle

```bash
# 양측 컨테이너 .env path 환경변수 설정:
export MCTRADER_DATA_ENV=/etc/mctrader/data.env
export MCTRADER_ENGINE_ENV=/etc/mctrader/engine.env

# Rotation cycle 진입:
python scripts/ops/rotate_minio_secret.py \
    --output /tmp/secret-rotation-MCT-155-cycle-1.md \
    --backup /tmp/secret-backup-MCT-155-cycle-1/

# Expected: exit code 0 (success)
# Sequential update steps:
#   1. MinIO IAM API: 신규 access_key + secret_key 생성
#   2. .env backup (양측 컨테이너, 0600)
#   3. .env 갱신 (data 먼저)
#   4. mctrader-data 컨테이너 restart 또는 hot-reload  ← OPERATOR MANUAL GATE
#   5. sample PUT 1회 verify  ← OPERATOR MANUAL GATE
#   6. .env 갱신 (engine 다음)
#   7. mctrader-engine 컨테이너 restart 또는 hot-reload  ← OPERATOR MANUAL GATE
#   8. sample GET 1회 verify  ← OPERATOR MANUAL GATE
#   9. old credential revoke (MinIO IAM API)  ← OPERATOR MANUAL GATE
#   10. audit log 박제
```

### §3.2 Emergency rollback (인증 실패 시)

```bash
python scripts/ops/rotate_minio_secret.py \
    --emergency-rollback \
    --backup /tmp/secret-backup-MCT-155-cycle-1/

# Restores .env files from backup (B5 trust boundary)
# 인증 실패 발견 즉시 진입 (cycle 진행 중 step 4-8 시점)
```

### §3.3 Rotation 완료 verify

- audit log file 박제 (`/tmp/secret-rotation-MCT-155-cycle-1.md`)
- Prometheus metric `nas_secret_rotation_cycle_count_total{result="success"}` increase
- Prometheus metric `nas_secret_rotation_age_days` reset to 0
- 다음 cycle = 90d 후 (Stage 3 또는 Stage 2 정책 amendment 시점)

---

## §4 TLS 재검토 절차 (AC-6 — MCT-155 direct owner)

### §4.1 사용자 confirm (Stage 2 종료 시점)

**결정**: HTTP 유지 (Stage 1 정책 연장) — `docs/runbooks/nas-minio-tls-review.md` §1 verbatim 인용.

### §4.2 ADR-027 D2 amendment commit

본 PR (`mctrader-hub` Phase 2 PR) 측 hub 산출물:
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` D2 wording 갱신
- scope_manifest `triggers_adr_amendment.adr=ADR-027.section=D2.status: pending → committed` (PMOAgent retro 시점)

### §4.3 Future re-evaluation trigger

`docs/runbooks/nas-minio-tls-review.md` §4.2 + §5 박제 4 trigger 정합 (외부 노출 / NAS hardware 교체 / Stage 3 / Secret leak).

---

## §5 Epic milestone #4 CLOSED trigger 절차

### §5.1 PMOAgent dispatch (Phase 2 PR merge 후)

PMOAgent 가 본 Story 종료 후 자동 dispatch:
- Story §12 작성 (RETRO-MCT-155.md)
- Stage 2 Epic-final retro 별 file (`docs/retros/2026-05-stage2.md`)
- scope_manifest `epic_milestones.stage_2_complete.progress` update (6/6 stories, 36/36 SP, 100%)
- §1 6 AC 종합 verify checklist ALL PASS verify

### §5.2 milestone close (PMOAgent retro 후)

```bash
# milestone #4 close (Epic-cold-tier-stage-2-migration):
gh api -X PATCH /repos/mclayer/mctrader-hub/milestones/4 -f state=closed

# Issue #274 close:
gh issue close 274 --repo mclayer/mctrader-hub --comment "Stage 2 EPIC CLOSED ..."
```

### §5.3 codeforge #525 amendment 권고 통보 (PMOAgent retro 후)

`mclayer/plugin-codeforge#525` PR comment 또는 issue comment 통보:
- MCT-150~155 누적 효과 박제
- lesson 4+1+sub invariants 효과 측정 결과 (FIX cycle ~80% ↓)
- lesson #5 sub-invariant 공식 채택 권고

---

## References

- `scope_manifests/EPIC-cold-tier-nas-minio.yaml`
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
- `docs/stories/MCT-150~155.md`
- `docs/runbooks/nas-minio-cutover-checklist.md` (MCT-154 land)
- `docs/runbooks/nas-minio-unreachable-sop.md` (MCT-152 land)
- `docs/runbooks/nas-minio-secret-rotation.md` (MCT-147 land)
- `docs/runbooks/nas-minio-tls-review.md` (MCT-155 land — 본 PR)
- `mclayer/plugin-codeforge#525` (lesson 4+1+sub invariants)
