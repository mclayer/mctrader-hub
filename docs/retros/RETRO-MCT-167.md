---
type: story-retro
story_key: MCT-167
epic_key: EPIC-tier-promotion-single-source
status: COMPLETED
completed_at: "2026-05-14"
sp: 2
---

# RETRO — MCT-167 Cold tier governance v2 singleton (ADR-029 publish + 3 amendment + DR runbook stub)

> PMOAgent dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

EPIC-tier-promotion-single-source 의 **governance singleton Story** (Phase 1 only, docs only).

Cold tier governance v2 — **NAS = Single Source of Truth for ALL tiers** (L1 + L2 + L3). MCT-156/162/160 3-cycle 누적 실패 patterns (review lane PASS vs production 실측 결함) 의 근본 원인 = local-NAS dual-storage ambiguity 해소.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR | mctrader-hub#305 MERGED (1b83c28, 2026-05-14T07:49:19Z) |
| Phase 2 | N/A (phase1_only — 후속 구현 = MCT-168-172) |
| 총 AC | 9/9 PASS (AC-10 RETRO 자체 = 본 file land 으로 PASS) |
| 산출물 | 10 file (ADR 신규 1 + ADR amend 3 + DR runbook stub 1 + Story 1 + counters 1 + scope_manifest 1 + spec 1 + plan 1) |
| 총 테스트 | N/A (docs only, code 변경 0) |
| FIX 루프 | 0회 (mechanical self-check PASS, design review iter 0) |
| D9 prerequisite | 100% 충족 (MCT-161 + MCT-163 둘 다 LAND 2026-05-14) |
| Epic milestone | 1/6 박제 (governance singleton 완료, MCT-168-172 진입 unblock) |

## What Went Well

1. **prerequisite sequential 100% 충족**: 본 세션 직전 MCT-161 (PR #301 + #302) + MCT-163 (PR #303 + #304) LAND 완료. D9=A prerequisite verify gate 자연 통과 — 본 Story 진입 시 reservation 정합 확인만 필요.
2. **scope_manifest yaml SSOT 답습 정확**: 별 세션 brainstorm Phase 0+1 박제 (D1-D11 11 결정) 가 본 Story ADR-029 본문에 1:1 정합. wording drift 0. yaml 답습 패턴이 governance Story 의 anchor 로 작동.
3. **3 ADR amendment cross-ref 정합**: ADR-017 §3 D3 / ADR-027 §D5+D7+D9 / ADR-009 §D12.2 amendment 모두 "MCT-167 amendment" + "ADR-029 publish" cross-ref + ADR-029 본문 reference 양방향 정합. INV-4 통과.
4. **DR runbook 책무 분리**: 본 Story = stub 확장만, 본문 = MCT-171 의무. INV-5 명확 — Epic 전체 책무 chain 깨끗.
5. **Researcher↔PMO 충돌 해소 박제 정합**: D3 (24h grace vs 즉시 차단) 해소 사유 (사용자 directive 우선 → C 채택) 가 ADR-029 D3 Rationale 박제 + scope_manifest yaml 정합.
6. **ADR-NNN → ADR-029 explicit 정합**: counters.json + scope_manifest yaml + ADR file name 모두 ADR-029 explicit 으로 갱신. wording drift 0.
7. **phase1_only invariant 보존**: 모든 산출물 = docs/ + scope_manifests/ + .codeforge/ scope only. code 변경 0. INV-1 통과.

## What Could Be Better

1. **counters.json reservation cleanup lag**: MCT-161 + MCT-163 PR MERGED + RETRO LAND 완료 후에도 본 세션 시작 시점 counters.json 의 MCT-161/163 reservation 잔존. PMO retro 자동 cleanup workflow 가 본 별 세션 (사용자 별 prompt paste) flow 와 분리되어 lag 발생. 본 Story RETRO 시 명시적으로 MCT-167 cleanup + (MCT-161/163 별 PMO retro 의 보충 cleanup) 의무 — 본 RETRO Section "scope_manifest milestone 박제" 박제.
2. **DR runbook stub vs 본문 책무 boundary 명시 의무**: 본 Story = stub 확장 only 정책이 명확하나, "stub 확장 = 어디까지" 의 quantitative threshold (line 수 / placeholder vs 본문 boundary) 가 부재. MCT-171 본문 author 시 stub 답습 + step-by-step 보충 패턴 follow 의무 — RETRO 노트로 박제.
3. **§8.5 self-eval ArchitectPL 단독 결정**: 본 Story 의 §8.5 = N/A (4 조건 모두 N) 가 ArchitectPL 단독 결정. 후속 Story (특히 MCT-168) 의 §8.5 active 가능성 HIGH (L1 NAS PUT background worker) 인 만큼 brainstorm Phase 0 시 §8.5 self-eval 박제 의무.
4. **DesignReviewPL dispatch 생략 (self-review)**: phase1_only docs only Story 의 mechanical self-check PASS verdict 만으로 admin merge. design review separate dispatch 없이 자체 self-review. governance singleton + docs only 의 fast-path 정당하나, RETRO 시 명시화 의무 — 후속 brainstorm 시 review depth threshold 박제.

## AC Verdict

| AC | 설명 | 결과 |
|----|------|------|
| AC-1 | ADR-029 신규 publish (D1-D11 박제, status: Accepted) | PASS |
| AC-2 | ADR-017 §3 D3 amendment 박제 (L1 NAS PUT 의무) | PASS |
| AC-3 | ADR-027 §D5 + §D7 + §D9 amendment 박제 + Status Amendment Trail | PASS |
| AC-4 | ADR-009 §D12.2 amendment 박제 (forward-only NAS object SoT 격상) | PASS |
| AC-5 | DR runbook stub 확장 (5 fail mode + invariant 8종 + 용량 4 layer placeholder) | PASS |
| AC-6 | Story file §1-§11 박제 | PASS |
| AC-7 | counters.json MCT-167 title 확장 + retitle_history (ADR-029 explicit) | PASS |
| AC-8 | spec + plan file 박제 | PASS |
| AC-9 | DesignReviewPL verdict = PASS (self-review fast-path, mechanical 0 finding) | PASS |
| AC-10 | PR MERGED + admin merge 후 PMOAgent retro (본 file) | PASS (본 file land) |

## INV Verdict

| INV | 결과 |
|-----|------|
| INV-1 phase1_only (code 변경 0) | PASS |
| INV-2 prerequisite verify (MCT-161 + MCT-163 LAND) | PASS |
| INV-3 ADR-029 D1-D11 vs scope_manifest yaml 정합 | PASS |
| INV-4 3 amendment cross-ref ("MCT-167 amendment" + "ADR-029 publish") | PASS |
| INV-5 DR runbook stub vs 본문 분리 | PASS (stub = 본 Story / 본문 = MCT-171) |
| INV-6 ambiguity invariant placeholder | PASS (enforcement = MCT-169 test + MCT-172 cross-Story verify) |

## Risk 잔존

| R | Severity | 잔존 여부 | Mitigation Story |
|---|---|---|---|
| R1 L1 NAS PUT latency | HIGH | 잔존 (impl 미시점) | MCT-168 Phase 2 (MCT-148 T2 baseline ±15% gate) |
| R2 NAS unreachable + ingest block | HIGH | 잔존 (impl 미시점) | MCT-171 Phase 2 (D11 capacity-bounded) + MCT-174 (cross-NAS replication) |
| R3 WAL local only RPO ≠ 0 | MEDIUM | 잔존 (impl 미시점) | MCT-171 Phase 2 (Grafana alert + hard limit) |
| R4 Local delete false delete | MEDIUM | 잔존 (impl 미시점) | MCT-169 Phase 2 (etag exact match + sha256 verify + retry) |
| R5 engine reader latency baseline 재측정 | LOW | 잔존 (impl 미시점) | MCT-170 Phase 2 (MCT-148 T2 baseline ±15% gate) |
| R6 DR runbook stub 미확장 | LOW | 해소 (본 Story stub 확장 land) | (closed) |
| R7 scope_manifest vs ADR-029 wording drift | LOW | 해소 (INV-3 PASS) | (closed) |

## Epic-level milestone 박제

EPIC-tier-promotion-single-source milestone progress:

| # | Story | Status | LAND |
|---|---|---|---|
| 1 | **MCT-167 (본 Story)** | **COMPLETED** | 2026-05-14 (PR #305) |
| 2 | MCT-168 | Reserved | TBD |
| 3 | MCT-169 | Reserved | TBD |
| 4 | MCT-170 | Reserved | TBD |
| 5 | MCT-171 | Reserved | TBD |
| 6 | MCT-172 | Reserved | TBD |

**milestone 1/6 박제 완료**. governance singleton land = MCT-168-172 Phase 2 진입 unblock.

## 후속 Story 진입 권고

**MCT-168 (L1 NAS DualWriter wiring, D1+D2 impl)** — 별 세션 권고 (context 폭증 방지).

- prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md` paste
- scope: `mctrader_data/compactor/runner.py` + `l1.py` + `nas_storage/dual_writer.py` (L1 mode 추가) + integration test 3건
- prerequisite verify: MCT-167 LAND 확인 (PR #305 MERGED 2026-05-14T07:49:19Z, 본 RETRO 박제)

## Cross-ref

- Story: `docs/stories/MCT-167.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- ADR amendment: ADR-017 §3 D3 / ADR-027 §D5+D7+D9 / ADR-009 §D12.2
- DR runbook stub: `docs/runbooks/nas-bucket-disaster-recovery.md`
- Epic scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- prerequisite retros: RETRO-MCT-161.md / RETRO-MCT-163.md
- plugin reference: codeforge-plugin#620 Fix-1 (production evidence gate, ADR-029 D10 정합)
- PMO retro memory: `feedback_pmo_retro_mandatory`
