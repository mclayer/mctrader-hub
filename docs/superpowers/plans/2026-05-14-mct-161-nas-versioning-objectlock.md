# MCT-161 NAS bucket versioning + Object Lock + DR runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** MCT-153 4.2 GiB 손실 재발 방지 + EPIC-compactor-operations milestone 3/3 closure gate. NAS bucket `mctrader-market` versioning enable + Object Lock governance 30d + Lifecycle ILM 30d + DR runbook 신규 author + ADR-027 §D amendment.

**Architecture:** D9=A 1 Story (사용자 명시), D2=D replication deferred (single NAS box). 1 PR pair (Phase 1 hub docs only + Phase 2 hub multi-commit). hot path 무영향 (ADR-027 §D5 INV-1).

**Tech Stack:** Python boto3, MinIO admin client, gh CLI.

**Spec:** [docs/superpowers/specs/2026-05-14-MCT-161-nas-versioning-objectlock-design.md](../specs/2026-05-14-MCT-161-nas-versioning-objectlock-design.md)

---

## File Structure

### mctrader-hub
- **Create**: `docs/stories/MCT-161.md` (§1-§12)
- **Modify**: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (§D amendment)
- **Create**: `docs/runbooks/nas-bucket-disaster-recovery.md` (DR runbook 신규)
- **Create**: `scripts/enable_nas_versioning.py` (Phase 2 enable script)
- **Create**: `scripts/verify_nas_versioning.py` (Phase 2 verify)
- **Modify**: `.codeforge/counters.json` (MCT-161 title 확장)
- **Modify**: `CLAUDE.md` (§NAS versioning + §DR runbook + §pending stories)
- **Create**: `docs/retros/RETRO-MCT-161.md`

---

## Task 1: Phase 1 hub PR

- [ ] **Step 1**: branch + counters (이미 완료)

- [ ] **Step 2**: ADR-027 §D amendment 본문 작성

ADR-027 의 line 174 직후 (MCT-164 amendment 직후) 에 새 amendment 박제:

```markdown
**MCT-161 amendment 박제 (2026-05-14)** — NAS bucket versioning + Object Lock governance 30d + Lifecycle ILM. EPIC-compactor-operations milestone 3/3 closure gate.

**Background**: MCT-153 손실 (4.2 GiB / 1370 obj, RETRO-MCT-156 §13.5.2) = bucket versioning 미활성으로 hard delete 식별 불가. 본 amendment = prevention + DR.

**Decision**:
1. **Bucket versioning enable**: `mctrader-market` bucket `Status: Enabled` (MinIO admin API).
2. **Object Lock governance 30d**: GovernanceRetention 30d, hard delete 시 DeleteMarker 만 추가, version 보존.
3. **Lifecycle ILM**: `NoncurrentVersionExpiration 30d` 자동 expiration (storage cost 1.5x 미만 보장, append-only 특성 1.1x-1.3x).
4. **DeleteMarker replication OFF** (향후 replication 도입 시 적용 의무, MCT-153 재발 방지 핵심).
5. **Hot path 무영향**: collector WAL + L1 ParquetWriter latency 영향 0 (ADR-027 §D5 정합).
6. **Replication = 후속 별 backlog Story** (D2=D, single NAS box mcnas02 물리 부재): 본 amendment scope 외 명시.

**DR runbook**: `docs/runbooks/nas-bucket-disaster-recovery.md` (MCT-161 산출, AC-4) — restore-from-version 단계별 명시.

**Cross-ref**: MCT-153 (손실 source) / MCT-159 D7 (versioning 미활성 식별) / MCT-167 (EPIC-tier-promotion governance prerequisite consumer)
```

ADR-027 History section 에 1 줄 추가.

- [ ] **Step 3**: Story file MCT-161.md §1-§7 작성

- [ ] **Step 4**: commit + push + PR + label

```bash
git add .codeforge/counters.json docs/adr/ADR-027-*.md docs/stories/MCT-161.md docs/superpowers/specs/2026-05-14-MCT-161-*.md docs/superpowers/plans/2026-05-14-mct-161-*.md
git commit -m "docs(MCT-161): Phase 1 — spec + plan + Story §1-§7 + ADR-027 §D amendment (versioning + Object Lock + DR runbook 의무 박제) + counters"
git push -u origin mct-161-phase-1
gh pr create ...
```

- [ ] **Step 5**: DesignReviewPL → label transition → CI green → admin merge

---

## Task 2: Phase 2.1 NAS bucket versioning enable (AC-1, INV-2)

**Files:** `scripts/enable_nas_versioning.py`

```python
import os
import boto3

def enable_versioning():
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ['NAS_MINIO_ENDPOINT'],
        aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'],
        aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'],
    )
    s3.put_bucket_versioning(
        Bucket='mctrader-market',
        VersioningConfiguration={'Status': 'Enabled'},
    )
    result = s3.get_bucket_versioning(Bucket='mctrader-market')
    assert result.get('Status') == 'Enabled', f"versioning 미활성: {result}"
    print('AC-1 PASS: bucket versioning Enabled')

if __name__ == '__main__':
    enable_versioning()
```

---

## Task 3: Phase 2.2 Object Lock governance 30d + Lifecycle (AC-2, AC-3, INV-2, INV-3)

**Files:** `scripts/enable_nas_versioning.py` extend

Object Lock + Lifecycle ILM 추가:

```python
def enable_object_lock():
    # Object Lock = bucket 생성 시점만 가능. 기존 bucket 은 별 mc admin 명령 필요.
    # MinIO 의 경우: `mc admin bucket retention set mctrader-market 30d --mode GOVERNANCE`
    # 또는 boto3:
    s3.put_object_lock_configuration(
        Bucket='mctrader-market',
        ObjectLockConfiguration={
            'ObjectLockEnabled': 'Enabled',
            'Rule': {
                'DefaultRetention': {
                    'Mode': 'GOVERNANCE',
                    'Days': 30,
                }
            }
        }
    )

def enable_lifecycle():
    s3.put_bucket_lifecycle_configuration(
        Bucket='mctrader-market',
        LifecycleConfiguration={
            'Rules': [{
                'ID': 'NoncurrentVersionExpiration-30d',
                'Status': 'Enabled',
                'Filter': {'Prefix': ''},
                'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
            }]
        }
    )
```

verify (`scripts/verify_nas_versioning.py`):
- AC-2: `s3.get_object_lock_configuration` = ENABLED + GOVERNANCE 30d
- AC-3: `s3.get_bucket_lifecycle_configuration` = NoncurrentVersionExpiration 30d

---

## Task 4: Phase 2.3 DR runbook 신규 (AC-4, INV-4)

**Files:** `docs/runbooks/nas-bucket-disaster-recovery.md`

frontmatter + 단계별 명시 (mctrader-hub 기존 runbook 패턴 답습):

```markdown
---
runbook: nas-bucket-disaster-recovery
created: 2026-05-14
story: MCT-161
related_adrs: [ADR-027 §D amendment MCT-161]
trigger: NAS data loss / hard delete / version restoration 필요
owner: Operations
cadence: ad-hoc (incident response)
---

# NAS Bucket Disaster Recovery Runbook

## Trigger 조건
- NAS data loss event 감지
- hard delete 실수 발견
- MCT-153 같은 잠재 손실 확인 필요

## Step 1 — Triage (5 min)
- ...

## Step 2 — Version history 조회
- `aws s3api list-object-versions --bucket mctrader-market --prefix <path> ...`
- DeleteMarker 식별 + 가장 최근 정상 version 식별

## Step 3 — Restore-from-version
- `aws s3 cp s3://mctrader-market/<key>?versionId=<id> s3://mctrader-market/<key>`
- 또는 `boto3.client('s3').copy_object(CopySource={'Bucket':..., 'Key':..., 'VersionId':...}, ...)`

## Step 4 — Verify
- 복구된 obj 의 md5 / size / metadata 검증
- audit log 박제 (`docs/audit/incident-YYYY-MM-DD-restore.md`)

## Step 5 — Postmortem
- RETRO 작성 (root cause + prevention 추가)
- Cross-ref: MCT-153 evidence (RETRO-MCT-156 §13.5.2)

## 완료 기준 (Story AC-4)
- Step 1~5 단계별 실행 가능
- restore success rate ≥ 95% (DeleteMarker 보존된 version 한정)
- audit log 박제 완료
```

---

## Task 5: Phase 2.4 박제 + retro + EPIC closure

- [ ] **Step 1**: Story §8-§12 박제 (Test Contract / Operational Risk / FIX Ledger + verify 결과 + AC-1~5 verdict / Invariant cross-ref / PMO retro)
- [ ] **Step 2**: CLAUDE.md §NAS versioning + §DR runbook + §pending stories
- [ ] **Step 3**: RETRO-MCT-161.md PMOAgent dispatch
- [ ] **Step 4**: EPIC-compactor-operations scope_manifest milestone 3/3 → COMPLETED
- [ ] **Step 5**: EPIC-RESULTS-EPIC-compactor-operations.md 신규 박제 (Epic CLOSED gate)
- [ ] **Step 6**: replication 후속 Story reservation (counters 추가, 예: MCT-174 placeholder)
- [ ] **Step 7**: hub Phase 2 PR open + DesignReviewPL + CI green → admin merge
- [ ] **Step 8**: Issue close (MCT-161 trigger Issue 가 별도 있는지 확인, gate:retro-complete)

---

## Execution: Subagent-Driven
