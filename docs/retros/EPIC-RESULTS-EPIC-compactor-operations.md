---
type: epic-results
epic_key: EPIC-compactor-operations
epic_title: "compactor operations — L1 channel parity + L2 cadence + NAS durability"
parent_epic: EPIC-cold-tier-stage-3-wiring
status: CLOSED
closed_at: 2026-05-14
total_stories: 3
total_sp: 11
scope_manifest: scope_manifests/EPIC-compactor-operations.yaml
---

# EPIC-RESULTS — EPIC-compactor-operations

> **Epic**: compactor operations — L1 channel parity + L2 cadence + NAS durability (post-MCT-156 deploy 5중 차단 cycle)
> **Parent**: EPIC-cold-tier-stage-3-wiring
> **Status**: CLOSED (2026-05-14)
> **Stories**: MCT-162 + MCT-160 + MCT-161 (3/3 완료)

## Epic Summary

MCT-156 (EPIC-cold-tier-stage-3-wiring entrypoint) production deploy (2026-05-13) 직후 발견된 5중 차단 cycle을 해소한 Epic. 3 Story sequential 분해:

1. **MCT-162** — L1 channel parity + orderbookdepth schema 정의
2. **MCT-160** — L2/L3 cadence + OOM + L1 backlog cleanup
3. **MCT-161** — NAS bucket versioning + Object Lock + DR runbook

## Story 완료 현황

| Story | Title | SP | 완료일 | Phase 1 PR | Phase 2 PR | Root Cause |
|-------|-------|-----|--------|-----------|-----------|-----------|
| MCT-162 | L1 channel parity + orderbookdepth | 3 | 2026-05-13 | mctrader-hub#284 (895bd77) | mctrader-data#52 (338c4b6) + mctrader-hub#TBD | upbit L1 today=0 (#1 #4) |
| MCT-160 | L2/L3 cadence + OOM + backlog cleanup | 5 | 2026-05-13 | mctrader-hub#287 (cad60d2) | mctrader-data#53 (c96a9ef) + mctrader-hub#TBD | cadence silent-skip + OOM (#2 #3 #5) |
| MCT-161 | NAS versioning + Object Lock + DR runbook | 3 | 2026-05-14 | mctrader-hub#301 MERGED | mctrader-hub#TBD | MCT-153 4.2 GiB 손실 재발 방지 |
| **합계** | | **11** | **2026-05-14** | | | |

## 5중 차단 cycle 해소 결과

| 차단 | 원인 | 해소 Story | 결과 |
|------|------|-----------|------|
| upbit L1 today=0 | orderbookdepth channel NotImplementedError stuck | MCT-162 | RESOLVED — orderbookdepth allowlist + converter 추가 |
| transaction L2 silent skip | KST→UTC date roll 시 caller date 미전달 | MCT-160 | RESOLVED — caller-explicit date + monotonic verify |
| bucket 463 obj (bithumb only) | L1/L2/L3 orderbookdepth + upbit 미생성 | MCT-162 + MCT-160 | RESOLVED — channel parity + cadence fix |
| L1 backlog 79k+ | orderbookdepth 48k NotImplementedError stuck | MCT-162 | RESOLVED — backlog t=0: 82,456 → 4,319 (95% 감소) |
| L2 OOM exit 137 | pa.concat_tables 32GB + i32 offset overflow | MCT-160 | RESOLVED — chunk-based streaming + row_group_size=100k |

## NAS Durability 결과 (MCT-161)

| AC | Verdict | 비고 |
|----|---------|------|
| AC-1 versioning | PASS | mctrader-market versioning=Enabled, DeleteMarker 생성 확인 |
| AC-2 Object Lock | SKIP | 기존 bucket MinIO 제약 (--with-lock 생성 시점 의무) |
| AC-3 Lifecycle | PASS | NoncurrentVersionExpiration 30d |
| AC-4 DR runbook | PASS | 5-step runbook 신규 |
| AC-5 ADR amendment | PASS | ADR-027 §D MCT-161 amendment Phase 1 #301 MERGED |

## ADR 개정 현황

| ADR | Amendment | Story |
|-----|-----------|-------|
| ADR-009 | §D11.9 신규 + §D2.6 matrix row + nullability 3 schema | MCT-162 + MCT-160 |
| ADR-027 | D4 channel parity fail-fast + silent-skip 차단 + MCT-161 §D amendment | MCT-162 + MCT-160 + MCT-161 |

## Backlog 상태 (Epic 종료 시점)

| Item | 상태 | 후속 |
|------|------|------|
| MCT-163 | PROPOSED | MCT-160 F3+F6+F7 follow-up (DualWriter streaming + row-batch + ADR-009 D7 amend) |
| MCT-174 | RESERVED | NAS replication backlog (D2=D deferred, single NAS box 환경) |
| Object Lock 재검토 | 후속 운영 결정 | bucket 재생성 또는 MinIO Console 경유 |

## 산출물 목록

| 산출물 | 위치 | Story |
|--------|------|-------|
| enable_nas_versioning.py | scripts/enable_nas_versioning.py | MCT-161 |
| verify_nas_versioning.py | scripts/verify_nas_versioning.py | MCT-161 |
| DR runbook | docs/runbooks/nas-bucket-disaster-recovery.md | MCT-161 |
| enable audit | docs/audit/MCT-161-versioning-enable.md | MCT-161 |
| CLAUDE.md §NAS versioning | CLAUDE.md | MCT-161 |
| scope_manifest COMPLETED | scope_manifests/EPIC-compactor-operations.yaml | MCT-161 |
| MCT-174 reservation | .codeforge/counters.json | MCT-161 |

## Replication Backlog Cross-ref (INV-5)

MCT-174 (NAS replication — single NAS box mcnas02 물리 부재 해소 후 진입):
- D2=D 결정: replication deferred (본 Epic scope 외)
- INV-5: replication 후속 별 Story reservation 의무 = **DONE** (.codeforge/counters.json MCT-174)
- DeleteMarker replication OFF 정책 박제 (ADR-027 §D MCT-161 amendment D4)

## Cross-ref

- docs/retros/RETRO-MCT-161.md (Story 3/3 retro)
- docs/retros/RETRO-MCT-160.md (Story 2/3 retro)
- docs/retros/RETRO-MCT-162.md (Story 1/3 retro)
- scope_manifests/EPIC-compactor-operations.yaml (milestone 3/3 COMPLETED)
- EPIC-cold-tier-stage-3-wiring (parent Epic)
- EPIC-tier-promotion-single-source (후속 Epic, MCT-161 DR runbook prerequisite consumer)
