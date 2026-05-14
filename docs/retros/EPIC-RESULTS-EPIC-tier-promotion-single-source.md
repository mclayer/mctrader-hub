---
type: epic-results
epic_key: EPIC-tier-promotion-single-source
epic_title: "Cold tier governance v2 — NAS = single source of truth 전면 재설계"
parent_epic: EPIC-compactor-operations
status: IN_PROGRESS
created_at: 2026-05-14
total_stories: 6
completed_stories: 1
scope_manifest: scope_manifests/EPIC-tier-promotion-single-source.yaml
---

# EPIC-RESULTS — EPIC-tier-promotion-single-source (placeholder, IN_PROGRESS)

> **Epic**: Cold tier governance v2 — NAS = single source of truth for ALL tiers (L1 + L2 + L3)
> **Parent**: EPIC-compactor-operations (sibling)
> **Status**: IN_PROGRESS (governance singleton land 2026-05-14, 5 Story 잔존)
> **Stories**: MCT-167-172 (1/6 완료)

## Epic Summary

MCT-156/162/160 3-cycle 누적 실패 patterns ("review lane PASS vs production 실측 결함") 의 근본 원인 = local-NAS dual-storage ambiguity 해소 Epic. NAS = single source of truth 전환으로 ambiguity 차단 + production evidence direct surface.

사용자 directive (2026-05-14): L1 도 NAS dual-write + tier promotion 후 local delete + ambiguity 차단 + WAL local 유지 + 4 layer capacity 제한.

## Story 완료 현황

| Story | Title | SP | 완료일 | PR | Status |
|-------|-------|-----|--------|-----------|--------|
| **MCT-167** | governance singleton (ADR-029 publish + ADR-017/027/009 amend 3건 + DR runbook stub) | 2 | **2026-05-14** | mctrader-hub#305 (1b83c28) MERGED | **COMPLETED** |
| MCT-168 | L1 NAS DualWriter wiring (D1+D2) | TBD | TBD | TBD | Reserved |
| MCT-169 | L1 NAS verify + immediate local delete + tier promotion (D3+D10) | TBD | TBD | TBD | Reserved |
| MCT-170 | engine reader 재구현 (D7+D8) | TBD | TBD | TBD | Reserved |
| MCT-171 | DR runbook 본문 + invariant 8종 + 용량 제한 (D4+D5+D6+D11) | TBD | TBD | TBD | Reserved |
| MCT-172 | Epic integration smoke + EPIC CLOSED (D9+D10 verify) | TBD | TBD | TBD | Reserved |
| **합계** | | **2 (1/6)** | | | |

## D1-D11 11 결정 박제

| D | 결정 | Option | Owner Story |
|---|---|---|---|
| D1 | L1 NAS PUT timing — ParquetWriter atomic 직후 (compactor) | B | MCT-168 |
| D2 | DualWriter retry_queue + local_only 재사용 | B | MCT-168 |
| D3 | Local delete — NAS HEAD verify + grace 0 | C | MCT-169 |
| D4 | WAL sealed local only 유지 (사용자 directive) | B | MCT-171 |
| D5 | Capacity-bounded collector ingest block | A_modified | MCT-171 |
| D6 | bucket versioning + cross-NAS replication | B | MCT-171 (MCT-161 prerequisite) |
| D7 | Reader cache 95% hit + p99 <100ms | A | MCT-170 |
| D8 | forward-only + local fallback migration | B | MCT-170 |
| D9 | MCT-161 + MCT-163 prerequisite sequential ✓ | A | epic-level (MCT-167 verify 완료) |
| D10 | Ambiguity invariant violation enforcement | A | MCT-169 + MCT-172 |
| D11 | 4 layer capacity 제한 | capacity_bounded | MCT-171 |

## ADR 산출물

- **ADR-029 (신규, MCT-167 publish 2026-05-14)** — Cold tier governance v2 — NAS = SoT for ALL tiers (D1-D11 박제)
- **ADR-017 §3 D3 amendment (MCT-167)** — L1 NAS PUT 의무
- **ADR-027 §D5+D7+D9 amendment (MCT-167)** — L1 invariant 폐기 + L1 grace 0 + SoT all-tier 격상
- **ADR-009 §D12.2 amendment (MCT-167)** — forward-only invariant NAS object SoT 격상

## Prerequisite

- **MCT-161** (LAND 2026-05-14, PR #301 + #302) — NAS bucket versioning + Object Lock + DR runbook stub
- **MCT-163** (LAND 2026-05-14, PR #303 + #304) — DualWriter put_streaming + L2/L3 iter_batches

## Epic 종료 gate (Phase 2-5)

| # | Story | Gate |
|---|---|---|
| 1 | MCT-167 ✓ | governance singleton land (2026-05-14) |
| 2 | MCT-168 | L1 NAS dual-write production 검증 (NAS bucket L1 prefix 출현) |
| 3 | MCT-169 | ambiguity invariant 위반 0 (1h production 측정) |
| 4 | MCT-170 | engine reader latency baseline ±15% gate PASS |
| 5 | MCT-171 | DR runbook smoke + invariant 8종 ALL PASS + 용량 제한 효과 verify |
| 6 | MCT-172 | Epic integration e2e PASS + production evidence quad (bucket + log + Prometheus + drainage) ALL PASS |

## 다음 Story 진입 권고

**MCT-168 (L1 NAS DualWriter wiring, D1+D2 impl)** — 별 세션 권고 (context 폭증 방지).

## Cross-ref

- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- governance singleton: `docs/stories/MCT-167.md` + `docs/retros/RETRO-MCT-167.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- brainstorm prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md`
- plugin reference: codeforge-plugin#620 Fix-1 (production evidence gate)
