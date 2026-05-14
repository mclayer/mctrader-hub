---
type: epic-results
epic_key: EPIC-tier-promotion-single-source
epic_title: "Cold tier governance v2 — NAS = single source of truth 전면 재설계"
parent_epic: EPIC-compactor-operations
status: IN_PROGRESS
created_at: 2026-05-14
total_stories: 6
completed_stories: 5
scope_manifest: scope_manifests/EPIC-tier-promotion-single-source.yaml
---

# EPIC-RESULTS — EPIC-tier-promotion-single-source (IN_PROGRESS, 5/6 완료)

> **Epic**: Cold tier governance v2 — NAS = single source of truth for ALL tiers (L1 + L2 + L3)
> **Parent**: EPIC-compactor-operations (sibling)
> **Status**: IN_PROGRESS (governance singleton + L1 wiring + local delete + engine reader + DR runbook 본문 LAND 2026-05-14, 1 Story 잔존 — MCT-172 Epic CLOSE)
> **Stories**: MCT-167-172 (5/6 완료)

## Epic Summary

MCT-156/162/160 3-cycle 누적 실패 patterns ("review lane PASS vs production 실측 결함") 의 근본 원인 = local-NAS dual-storage ambiguity 해소 Epic. NAS = single source of truth 전환으로 ambiguity 차단 + production evidence direct surface.

사용자 directive (2026-05-14): L1 도 NAS dual-write + tier promotion 후 local delete + ambiguity 차단 + WAL local 유지 + 4 layer capacity 제한.

## Story 완료 현황

| Story | Title | SP | 완료일 | PR | Status |
|-------|-------|-----|--------|-----------|--------|
| **MCT-167** | governance singleton (ADR-029 publish + ADR-017/027/009 amend 3건 + DR runbook stub) | 2 | **2026-05-14** | mctrader-hub#305 (1b83c28) MERGED | **COMPLETED** |
| **MCT-168** | L1 NAS DualWriter wiring (D1+D2) | 3 | **2026-05-14** | mctrader-hub#307 (4d16a26) + mctrader-data#59 (a99d4e5) MERGED | **COMPLETED** |
| **MCT-169** | L1 NAS verify + immediate local delete + tier promotion (D3+D10) | 4 | **2026-05-14** | mctrader-hub#310 (a353090) + mctrader-data#60 (d65545f) + mctrader-hub#311 (eb2c0cc) MERGED | **COMPLETED** |
| **MCT-170** | Engine reader L1 확장 + DR mode + reader cache byte budget (D7+D8+D10) | 5 | **2026-05-14** | mctrader-hub#314 (311b795) + mctrader-data#61 (9d26438) + mctrader-engine#53 (a00690bc) + mctrader-hub#315 (f1e04e6) MERGED | **COMPLETED** |
| **MCT-171** | DR runbook 본문 + invariant 8종 + 용량 제한 (D4+D5+D6+D11) | 5 | **2026-05-14** | mctrader-hub#317 (3399abd) + mctrader-data#62 (3fb9d60) + mctrader-hub#318 (0b25975) MERGED | **COMPLETED** |
| MCT-172 | Epic integration smoke + EPIC CLOSED (D9+D10 verify) | TBD | TBD | TBD | Reserved |
| **합계** | | **19 (5/6)** | | | |

## Story-4 결과 박제 (MCT-170, 2026-05-14)

### 4 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-14 (early) | mctrader-hub#314 | 311b795 | Phase 1 docs — Story §1-§12 + spec + plan + ADR-029 §D7/§D8/§D10 amendment + scope_manifest IN_PROGRESS + CLAUDE.md + counters retitle (7 file) |
| 2026-05-14 (mid) | mctrader-data#61 | 9d26438 | Phase 2 PR#1 — NullReaderCache 제거 + LRUReaderCache 구현 (20 신규 test + 53 test ALL PASS, AC-7 grep 0건) |
| 2026-05-14 (mid-late) | mctrader-engine#53 | a00690bc | Phase 2 PR#2 — tier_reader / l1_reader / dr_mode 3 module 신규 + reader_cache byte budget 확장 + 5 test 신규 (107 io/ test ALL PASS, MCT-154 회귀 0) |
| 2026-05-14 (late) | mctrader-hub#TBD | TBD | Phase 2 PR#3 — RETRO + Story §11/§12 fill + milestone 4/6 COMPLETED + EPIC-RESULTS Story-4 entry + counters DELETE (6 file) |

### D7 NFR 측정 결과

| 항목 | 결과 | gate | verdict |
|------|------|------|---------|
| hit_ratio (10k read benchmark) | **0.95** | ≥ 0.95 | **PASS** |
| p99 latency | **0.016 ms** | < 100 ms | **PASS (대폭 마진)** |
| benchmark mean | ≈ 1.99 μs | — | (~503k OPS) |

R4 mitigation iter 1 적용 (n_rounds 10→20 + cache max_bytes +50%, FIX-MCT-170-001).

### ADR-029 amendment 박제 (MCT-170)

- **§D7 amendment box** — D7=C TTL configurable env (default 1h L1 / 24h L2 / 7d L3, env override)
- **§D8 amendment box** — D6=D sunset criterion (cutoff 2026-09-01 + telemetry 0-hit 14d + MCT-172 gate)
- **§D10 footnote** — dr_mode.UNKNOWN_TIER 상태 신규 + 30d exemption window (2026-05-14 ~ 2026-06-13) + Prometheus `nas_reader_ambiguity_total` emit

### AC-1 ~ AC-7 / INV-1 ~ INV-4 ALL PASS

MCT-154 backward compat 회귀 0 (cold_reader + reader_cache MCT-154 API + endpoint_router 전수 green). FIX 루프 1회 (D7 NFR R4 mitigation).

### 다음 Story chain

**MCT-171** (DR runbook 본문 + invariant 8종 + 용량 제한, D4+D5+D6+D11) — COMPLETED 2026-05-14 (3 PR cross-repo sequential LAND).

## Story-5 결과 박제 (MCT-171, 2026-05-14)

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-14T11:41Z | mctrader-hub#317 | 3399abd | Phase 1 docs — Story §1-§12 + spec + plan + DR runbook 본문 707 lines + scope_manifest IN_PROGRESS + counters retitle |
| 2026-05-14T12:20Z | mctrader-data#62 | 3fb9d60 | Phase 2 PR1 — capacity_probe + ingest_blocker + invariant 8종 통합 + Prometheus +5 metric + collector hook + 38 신규 test (931 회귀 ALL PASS) |
| 2026-05-14T12:30Z | mctrader-hub#318 | 0b25975 | Phase 2 PR2 — RETRO-MCT-171 + ADR-029 D4+D5+D11 verify + scope_manifest 5/6 + CLAUDE.md MCT-171 COMPLETED |

### D4+D5+D11 verify 결과

- **D4=B VERIFIED**: WAL sealed segment NAS PUT 0 (grep `wal/` NAS 호출 verify), `promotion.py` DEPRECATED 주석 박제
- **D5=A_modified VERIFIED**: `ingest_blocker.py` + collector hook. 95% block + 90% unblock 5% gap hysteresis. graceful drain test PASS
- **D6=B partial**: bucket versioning ✓ (MCT-161 LAND), cross-NAS = MCT-174 defer (mcnas02 물리 부재)
- **D11=capacity_bounded VERIFIED**: 4 layer `CapacityThresholds` SSOT (WAL 30G / L1 20G / NAS 1TB hard / Host 200G), 5 Prometheus metric 확장

### AC-1 ~ AC-5 / INV-1 ~ INV-6 ALL PASS

신규 test 38 (test_invariant_harness_8: 8 + test_capacity_probe: 15 + test_ingest_blocker: 15) + 931 회귀 0 (MCT-152/153/155/169 backward compat 모두 PASS). FIX 루프 3회 (ruff lint 2-pass + pyright type 1-pass — 구현 lane lint/type drift, MCT-175 ESCALATE 후보 아님).

### R-CRITICAL carry over → MCT-172

**WAL 30G 산정 근거 미검증** — Production data dir 부재 → MCT-172 Epic CLOSE 전 collector runtime probe baseline 측정 의무. 측정 결과 30G 초과 risk 검출 시 D11 WAL hard_limit 갱신 amendment 발의.

### 다음 Story chain

**MCT-172** (Epic CLOSED, D9+D10 verify + D8 sunset finalize + promotion.py cleanup + WAL 30G production measurement carry over + EPIC-RESULTS author) — 진입 가능. 별 세션 권고.

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

**MCT-171** (DR runbook 본문 + invariant 8종 확장 + 용량 제한 정책, D4=B WAL local + D5 + D6 + D11) — 진입 gate 충족 (MCT-167-170 ALL LAND). 별 세션 권고 (brainstorm 추가 의무 — Phase 0 4 agent + Codex review).

prompt path: `docs/superpowers/prompts/MCT-171-session-prompt.md` (작성 의무).

## Cross-ref

- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- governance singleton: `docs/stories/MCT-167.md` + `docs/retros/RETRO-MCT-167.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- brainstorm prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md`
- plugin reference: codeforge-plugin#620 Fix-1 (production evidence gate)
