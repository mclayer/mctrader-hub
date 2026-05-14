# MCT-161 별 세션 prompt — NAS bucket versioning + cross-NAS replication

> **사용법**: 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 에서 본 파일 전체 내용을 paste. Claude 가 자동으로 brainstorm Phase 0 → spec/plan → Phase 1 → Phase 2 → PMO retro cycle 진행.

---

## 작업 instruction (paste 시작)

MCT-161 cycle 자율 진행. EPIC-compactor-operations Story-3.

### 사용자 directive (autonomous)

본 Story 는 EPIC-tier-promotion-single-source (별 Epic) 의 prerequisite. 본 cycle 만 자율 진행 + 종료 보고. 시간 압박, 적극 병렬 진행.

### Story scope (counters.json 박제 정합)

`.codeforge/counters.json` 의 MCT-161 reservation:

> "NAS bucket versioning 활성화 + replication 정책 + MCT-153 손실 재발 방지"
> rationale: "MCT-159 brainstorm Phase 1 D7 (Codex 권고) — bucket versioning 미활성으로 MCT-153 4.2 GiB 복구 불가 확정. 본 Story 가 versioning 정책 + replication + 손실 재발 방지 영역."

### Background

- MCT-153 backfill 산출물 4.2 GiB / 1370 obj 손실 (bucket versioning 미활성, hard delete 또는 처음부터 NAS 미진입). RETRO-MCT-156 §13.5.2 박제.
- 후속 EPIC-tier-promotion-single-source 의 D6 결정 = bucket versioning + cross-NAS replication 의무 (single NAS 장애 + overwrite/delete 실수 완화).
- NAS host = mcnas01.internal.mclayer.it (192.168.50.200), bucket = mctrader-market.

### 작업 흐름 (codeforge 표준 cycle)

#### Phase 0: brainstorm 자동 진입

```
codeforge:codeforge-brainstorm 호출 시 ARGUMENTS:

MCT-161 — NAS bucket versioning + cross-NAS replication + MCT-153 손실 재발 방지

## Scope
- NAS bucket `mctrader-market` 의 versioning 활성화 (현재 미활성, list_object_versions = 0/0)
- Cross-NAS replication 정책 — 2nd NAS box 또는 cloud 대상
- MCT-153 4.2 GiB 손실 사례 prevention runbook
- Disaster Recovery (DR) runbook 신규 author (NAS data loss 시 복구 path)

## 핵심 결정점 (예상)
1. Versioning retention 정책 (예: 30일 또는 무제한)
2. Replication target = (a) 별 NAS box, (b) cloud (S3/GCS/Azure), (c) 둘 다
3. Replication mode = sync vs async (cross-NAS latency)
4. Versioning storage cost 영향 (1.5x ~ 3x bucket size)
5. MCT-153 사례 retrospective evidence 박제 (NAS bucket lifecycle audit)
6. ADR amendment scope = ADR-027 §D 신규 또는 별 ADR

## 참고 자료
- RETRO-MCT-156.md §13.5.2 (MCT-153 손실 확정)
- docs/runbooks/nas-minio-secret-rotation.md (90일 rotation 정책)
- ADR-027 §D5 (hot path 무영향 invariant — versioning 도입이 hot path 영향 0)

## Cross-Epic 의존
- 본 Story 는 EPIC-tier-promotion-single-source 의 prerequisite (D6 결정 박제). 본 Story LAND 후 MCT-167 (governance singleton) 진입 가능.

## 의무
- Phase 0 4-agent burst → Codex review → Sonnet 합성 → 사용자 final OK → PMO 2nd pass → spec/plan → Phase 1 worktree + ArchitectPL + DesignReview + merge → Phase 2 worktree + DevPL + QADev + Test + Security + CodeReview + merge → PMOAgent retro
- 사용자 명시 "시간 없다 + 적극 병렬" + "Always subagent-driven execution" + "Admin merge autonomy" + "CI failure auto-recovery" 정합
- Issue 생성 + counters.json reservations.MCT-161 DELETE (Phase 2 §11) + scope_manifests/EPIC-compactor-operations.yaml milestone 2/3 → 3/3 + RETRO-MCT-161.md 신규 + CLAUDE.md Stage 3 wiring 후속 섹션 추가
- Codex 권고 일괄 dispatch 패턴 (Q-by-Q 사용자 stop 금지)
```

#### Phase 1: ArchitectPL dispatch (worktree mct-161-phase1-architect)

ADR amendment (ADR-027 §D 또는 신규 ADR) + Story §1-§11 + 신규 DR runbook stub (`docs/runbooks/nas-bucket-disaster-recovery.md`).

#### Phase 2: DevPL + QADev parallel dispatch

mctrader-hub Phase 2 (governance + compose.yml 수정 + 신규 NAS versioning enable script).

NAS bucket versioning enable 명령 (참고):
```bash
docker exec mctrader-compactor python -c "
import boto3, os
s3 = boto3.client('s3', endpoint_url=os.environ['NAS_MINIO_ENDPOINT'], aws_access_key_id=os.environ['NAS_MINIO_ACCESS_KEY'], aws_secret_access_key=os.environ['NAS_MINIO_SECRET_KEY'])
s3.put_bucket_versioning(Bucket='mctrader-market', VersioningConfiguration={'Status': 'Enabled'})
v = s3.get_bucket_versioning(Bucket='mctrader-market')
print(v.get('Status'))  # 기대: Enabled
"
```

#### Phase 2 PMOAgent retro

RETRO-MCT-161.md 신규 + Story §12 + counters DELETE + scope_manifest milestone 3/3 → COMPLETED (EPIC-compactor-operations 종결 gate) + CLAUDE.md.

EPIC-compactor-operations milestone 3/3 (100%) 도달 = Epic CLOSED + EPIC-RESULTS-EPIC-compactor-operations.md 신규 박제 + PMOAgent ADR-XXX `post-cutover-wiring-gap-prevention` 정식 발의 (Cross-Story pattern 누적 4회 = trigger 강제).

### 진행 메모

- 사용자 명시 "시간 없다 + 적극 병렬" — DesignReviewPL + preflight + worktree 생성 + DevPL/QADev parallel + TestAgent + Security/CodeReview parallel + 2 PR merge 모두 가능한 한 병렬 dispatch.
- counters.json 박제 시 사용자가 직접 수정한 reservations 보존 의무 (사용자 박제 신뢰).
- 본 Story LAND 후 사용자에게 보고 + EPIC-compactor-operations CLOSED 박제 + 다음 진입 권고 (MCT-163 또는 MCT-167 governance).

### 산출 후 보고 의무

(a) Phase 1 + Phase 2 PR # + merge commit
(b) 4 review lane 결과
(c) bucket versioning enable verify (`list_object_versions` 결과)
(d) replication target 결정 + 적용 결과
(e) DR runbook 본문 위치
(f) EPIC-compactor-operations CLOSED gate 충족 여부 + EPIC-RESULTS 박제

---

## paste 끝 — 별 세션에서 Claude 가 자동 진행

본 prompt 가 self-contained. 사용자가 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 열고 paste 만 하면 cycle 자율 진행 가능.

소요 시간 추정: brainstorm 30min + spec/plan 30min + Phase 1 1-2h + Phase 2 2-4h + PMO retro 30min = **~4-7h 총 소요**.
