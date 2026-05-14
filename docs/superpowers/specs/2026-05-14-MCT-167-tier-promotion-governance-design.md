---
spec_id: 2026-05-14-MCT-167-tier-promotion-governance-design
story_key: MCT-167
epic_key: EPIC-tier-promotion-single-source
phase: 1 (governance singleton, docs only)
created: 2026-05-14
brainstorm_session: 2026-05-14 (별 세션, EPIC-tier-promotion-single-source-session-prompt.md 답습)
phase0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
codex_review: 2026-05-14 (D1-D11 11 결정점 + Researcher↔PMO 충돌 1건 해소)
---

# Spec: MCT-167 — Cold tier governance v2 singleton

## §1 Spec 개요

EPIC-tier-promotion-single-source 의 **governance singleton Story** — Cold tier governance v2 의 anchor ADR (ADR-029) 신규 publish + 3 ADR amendment + DR runbook stub.

본 spec = brainstorm 결과 (별 세션 Phase 0+1) 답습. scope_manifests/EPIC-tier-promotion-single-source.yaml D1-D11 박제와 정합.

## §2 핵심 결정 (D1-D11)

| D | 결정 | Option |
|---|---|---|
| D1 | L1 NAS PUT timing — L1 ParquetWriter atomic 직후 (compactor 측) | **B** |
| D2 | NAS PUT 동기/비동기 — DualWriter retry_queue + local_only 재사용 | **B** |
| D3 | Local delete — NAS HEAD verify + grace 0 (immediate) | **C** (Researcher↔PMO 충돌 해소) |
| D4 | WAL sealed segment — local only 유지 (사용자 directive) | **B** |
| D5 | NAS unreachable 시 collector ingest block (capacity-bounded) | **A_modified** |
| D6 | NAS replication — bucket versioning + cross-NAS replication | **B** |
| D7 | Reader cache — 95% hit + <100ms p99 (aggressive cache) | **A** |
| D8 | 기존 local data migration — forward-only + local fallback | **B** |
| D9 | MCT-161 + MCT-163 prerequisite — sequential ✓ | **A** |
| D10 | Ambiguity 차단 — invariant violation enforcement | **A** |
| D11 | 용량 제한 — 4 layer 임계 | **capacity_bounded** |

본문 = `docs/adr/ADR-029-tier-promotion-single-source.md` Decision 섹션.

## §3 Phase 0 Context 박제

### 3.1 DomainAgent

MCT-156/162/160 3-cycle 누적 실패 patterns. 모두 review lane PASS but production 실측 결함. 근본 원인 = local-NAS dual-storage ambiguity. NAS = single source of truth 전환으로 ambiguity 차단.

### 3.2 ResearcherAgent

- AWS S3 best practice (versioning + Object Lock + cross-region replication) NAS MinIO 측 적용 가능
- streaming PUT (boto3 upload_fileobj + TransferConfig) = MCT-163 LAND 산출물 활용
- read-through cache (LRU/TTL) = ADR-027 §D9 답습 + L1 tier 확장 자연 정합

### 3.3 RequirementsAnalystAgent

- 사용자 directive 5 (4 layer capacity 제한) 의 정량 spec 박제
- AC 의무 5건 + INV 의무 (phase1_only)

### 3.4 PMOAgent

- 본 Story = governance singleton, 후속 Story chain anchor
- Researcher↔PMO 충돌 1건 = D3 (24h grace vs 즉시 차단). 사용자 directive 우선 → C 채택
- prerequisite verify gate: MCT-161 + MCT-163 둘 다 LAND 후 진입 의무

## §4 산출물 매핑

10 file:
1. ADR-029 신규
2. ADR-017 §3 D3 amend
3. ADR-027 §D5+D7+D9 amend
4. ADR-009 §D12.2 amend
5. DR runbook stub 확장
6. Story file §1-§11
7. counters.json (title 확장)
8. scope_manifest yaml (Phase 2 retro 시 status COMPLETED)
9. 본 spec
10. plan file

## §5 후속 Story chain

MCT-168 (L1 NAS DualWriter wiring) → MCT-169 (immediate local delete + tier promotion) → MCT-170 ∥ MCT-171 (engine reader + DR runbook 본문) → MCT-172 (Epic CLOSED).

## §6 prerequisite verify (2026-05-14 본 세션)

- MCT-161 LAND 확인 (PR #301 + #302, RETRO-MCT-161.md 박제)
- MCT-163 LAND 확인 (PR #303 + #304, RETRO-MCT-163.md 박제)
- D9 prerequisite 100% 충족

## §7 Cross-ref

- Story file: `docs/stories/MCT-167.md`
- Plan: `docs/superpowers/plans/2026-05-14-mct-167-tier-promotion-governance.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- brainstorm prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md`
