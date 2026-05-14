---
story: MCT-161
title: NAS bucket versioning + Object Lock governance 30d + ADR-027 §D amendment + DR runbook
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
phase_1_decider: codex (GPT-5.4) 합성 → Sonnet 채택
trigger: MCT-153 4.2 GiB 손실 재발 방지 + EPIC-tier-promotion D9 prerequisite + EPIC-compactor-operations 3/3 closure gate
status: spec
---

# MCT-161 — NAS bucket versioning + Object Lock + DR runbook Story

## 1. Why

사용자 원문: > "MCT-161 + MCT-163 순차 + MCT-167 진입" (별 세션 prompt 자료 박제분 paste)

### 근본 동기 (Phase 0 Analyst)

MCT-153 손실 (4.2 GiB / 1370 obj, RETRO-MCT-156 §13.5.2) = bucket versioning 미활성으로 hard delete vs 미진입 식별 불가, 영구 복구 불가. 본 Story = prevention (versioning + Object Lock) + DR (NAS data loss 복구 path) 박제 + EPIC-compactor-operations milestone 3/3 closure gate.

## 2. Context (Phase 0)

### DomainAgent
- ADR-027 §D5 hot path 무영향 invariant / MCT-147 4중 mitigation / Synology mcnas01 HTTP LAN-only single NAS box
- 지식 공백 3: MinIO replication API / lifecycle 정책 SSOT / DR runbook 신규 패턴

### ResearcherAgent
- 핵심 3:
  - MinIO Bucket Replication (per-bucket, S3-compatible, granular)
  - Versioning storage cost append-only ~1.1x-1.3x (lifecycle ILM 으로 control)
  - RTO/RPO trade-off (sync 0 RPO vs async lag-tolerant)
- Unknowns 2:
  - btrfs/ext4 bit rot replication 전파 (MinIO bitrot HighwayHash + btrfs scrub 의무)
  - DeleteMarker paradox (async 중 source delete = target hidden, OFF 필요)
- 권장: Bucket Replication async + DeleteMarker OFF + Object Lock governance 30d + btrfs snapshot weekly

### RequirementsAnalystAgent
- WHY: MCT-153 prevention + DR. AC 5 / Edge 2

### PMOAgent
- 3 Story 예상 (versioning / replication / DR runbook) → 사용자 D9=A 1 Story 채택
- 주요 risk: single NAS box 환경 cross-NAS target 물리 부재

## 3. Phase 1 — 9 결정점 (Codex 합성 + Sonnet 채택)

| D | 결정 | 핵심 |
|---|---|---|
| D1 | A | Versioning retention 30d NoncurrentVersionExpiration |
| D2 | **D** | replication deferred (single NAS box, 후속 별 backlog Story) |
| D3 | C | N/A (D2=D 종속) |
| D4 | B | DeleteMarker replication OFF (logical delete attack 보호, 향후 적용 의무) |
| D5 | A | Object Lock governance 30d |
| D6 | B | btrfs snapshot runbook 박제만 (host cron 별 작업) |
| D7 | A | ADR-027 §D 신규 amendment |
| D8 | A | DR runbook = NAS data loss 복구 path 만 (Chaos/bit rot 후속) |
| D9 | A | 1 Story (사용자 명시, replication = 후속 별 backlog) |

## 4. Acceptance Criteria (5 개)

- **AC-1 (Bucket versioning enable)**: Given NAS MinIO endpoint, When `put_bucket_versioning(VersioningConfiguration={'Status': 'Enabled'})` 실행, Then `get_bucket_versioning()` = "Enabled" + delete 시 DeleteMarker 생성
- **AC-2 (Object Lock governance 30d)**: Given versioning enable 후, When `put_object_lock_configuration` governance 30d 적용, Then 30d 이내 version delete 시 GovernanceRetentionPolicy violation error
- **AC-3 (Lifecycle ILM)**: Given NoncurrentVersionExpiration 30d, When 30d 경과 version, Then 자동 expiration + storage cost 1.1x-1.3x 유지 (append-only)
- **AC-4 (DR runbook)**: Given NAS data loss 시나리오, When `docs/runbooks/nas-bucket-disaster-recovery.md` 단계 진행, Then version history 조회 → 손실 식별 → restore-from-version 실행 가능 (단계별 명시)
- **AC-5 (ADR-027 §D amendment)**: Given ADR-027 read, When MCT-161 amendment trail (D7 또는 D8 신규), Then versioning + Object Lock + lifecycle + replication backlog 박제 + MCT-153 evidence cross-ref

### Edge Case (2)
- **Edge-1 (Versioning enable 전 기존 obj)**: 기존 1884 L1 parquet 은 version "null". versioning enable 후부터 v1 부여. 처리: 기존 obj 보존 + 신규 부터 versioning (no migration)
- **Edge-2 (Object Lock + hot path latency)**: governance mode 가 hot path write 영향 0 검증. ADR-027 §D5 정합

## 5. Invariant (5 개)

- **INV-1**: Hot path 무영향 (ADR-027 §D5 정합) — versioning + Object Lock 도입이 collector WAL append / L1 ParquetWriter latency 영향 0
- **INV-2**: DeleteMarker 30d 보존 (Object Lock governance) — hard delete 시 version + DeleteMarker 모두 보존, MCT-153 재발 방지
- **INV-3**: Lifecycle ILM — NoncurrentVersionExpiration 30d 자동 적용, storage cost 1.5x 미만 (append-only)
- **INV-4**: DR runbook SSOT — restore-from-version 절차 단일 (수동 boto3 직접 호출 금지, runbook 단계 의무)
- **INV-5**: replication 후속 별 Story (D2=D) — 본 Story 종료 후 별 backlog Story 발의 의무 (single NAS box 한계 명시)

## 6. Risk (3 개)

- **R1 (Mid)**: governance 30d + lifecycle 30d 정합 mismatch → DeleteMarker 30d 보존 못 함. **완화**: AC-2 + AC-3 양쪽 30d 명시 + INV-2 정합 검증
- **R2 (Low)**: 기존 1884 L1 parquet "null" version 처리 → MCT-153 evidence 박제 불가. **완화**: Edge-1 명시, audit 시 evidence = list_object_versions 결과 (null version 무 + 신규 v1+)
- **R3 (Mid)**: single NAS box 환경 = replication target 물리 부재 → D2=D deferred 정당화 부담. **완화**: ADR-027 §D amendment 에 replication backlog 명시 + 후속 Story reservation

## 7. Phase 분할

| Phase | 산출물 | wall-clock | PR |
|---|---|---|---|
| Phase 1 | spec + plan + Story §1-§7 + ADR-027 §D amendment 본문 + counters title 확장 | 즉시 | mctrader-hub Phase 1 PR |
| Phase 2.1 | NAS bucket versioning enable script + AC-1 verify | 즉시 | mctrader-hub Phase 2 PR (commit 1) |
| Phase 2.2 | Object Lock governance 30d + Lifecycle ILM + AC-2/3 verify | 즉시 | mctrader-hub Phase 2 PR (commit 2) |
| Phase 2.3 | DR runbook 신규 author (`docs/runbooks/nas-bucket-disaster-recovery.md`) + AC-4 단계별 박제 | 즉시 | mctrader-hub Phase 2 PR (commit 3) |
| Phase 2.4 | Story §8-§12 + CLAUDE.md + RETRO + EPIC-compactor-operations milestone 3/3 → CLOSED + EPIC-RESULTS 박제 + replication 후속 Story reservation | 즉시 | mctrader-hub Phase 2 PR (commit 4) |

## 8. scope_manifest 초안

```yaml
planned_adrs:
  amendment: [ADR-027]  # §D amendment (versioning + Object Lock + lifecycle + replication backlog)
  reservation_only: []

planned_files:
  mctrader-hub:
    - docs/stories/MCT-161.md: §1-§12
    - docs/superpowers/specs/2026-05-14-MCT-161-nas-versioning-objectlock-design.md: spec
    - docs/superpowers/plans/2026-05-14-mct-161-nas-versioning-objectlock.md: plan
    - docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md: §D amendment (versioning + Object Lock)
    - docs/runbooks/nas-bucket-disaster-recovery.md: DR runbook 신규 author (D8=A)
    - scripts/enable_nas_versioning.py: bucket versioning + Object Lock + Lifecycle enable script (Phase 2)
    - scripts/verify_nas_versioning.py: AC-1/2/3 verify script (Phase 2)
    - docs/retros/RETRO-MCT-161.md: PMO retro
    - CLAUDE.md: §NAS versioning + §DR runbook + §pending stories (replication backlog)
    - .codeforge/counters.json: MCT-161 title 확장 + (Phase 2 retro 시 replication backlog Story reservation)

planned_claude_md_sections:
  - mctrader-hub CLAUDE.md §NAS versioning + Object Lock governance
  - mctrader-hub CLAUDE.md §DR runbook (restore-from-version)
  - mctrader-hub CLAUDE.md §pending stories (replication backlog, D2=D)

counters_reservation:
  current: MCT-161  # title 확장 박제
  next_reservation: []  # replication backlog Story = Phase 2 retro 시 결정 (MCT-174 후보)
```

## 9. Cross-ref

- **MCT-153** (4.2 GiB 손실 source, RETRO-MCT-156 §13.5.2)
- **MCT-147** (NAS deployment fact, 4중 mitigation)
- **MCT-159** Phase 1 D7 (bucket versioning 미활성 식별, 본 Story trigger source)
- **MCT-163** (sibling EPIC Story, prerequisite parallel)
- **MCT-167** (EPIC-tier-promotion governance, 본 Story prerequisite consumer)
- **ADR-027 §D5** (hot path 무영향, INV-1 정합)
- **EPIC-compactor-operations** (milestone 3/3 closure gate, 본 Story land 시 EPIC CLOSED)
- **EPIC-tier-promotion-single-source** (D9=A MCT-161+163 prerequisite, 본 Story land 시 D9 partial 충족)
