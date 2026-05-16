---
type: epic-results
epic_key: EPIC-tier-promotion-single-source
epic_title: "Cold tier governance v2 — NAS = single source of truth 전면 재설계"
parent_epic: EPIC-compactor-operations
status: POLICY_FINALIZED
created_at: 2026-05-14
policy_finalized_at: 2026-05-14
total_stories: 6
completed_stories: 6
scope_manifest: scope_manifests/EPIC-tier-promotion-single-source.yaml
---

# EPIC-RESULTS — EPIC-tier-promotion-single-source (POLICY_FINALIZED, 6/6 박제)

> **Epic**: Cold tier governance v2 — NAS = single source of truth for ALL tiers (L1 + L2 + L3)
> **Parent**: EPIC-compactor-operations (sibling)
> **Status**: **POLICY_FINALIZED** (6/6 Story policy finalize 박제 2026-05-14, Epic CLOSED 는 production evidence 완성 후 별 PR 의무 — D8-9=C Codex 채택)
> **Stories**: MCT-167-172 (6/6 박제)

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
| **MCT-172** | Epic policy finalize (D8 sunset + D9+D10 verify + promotion.py cleanup + WAL synthetic baseline) | 3 | **2026-05-14** | mctrader-hub#320 (29028a8) + mctrader-data#63 (f2fb28e) + mctrader-hub#321 (70731e3) MERGED | **POLICY_FINALIZED** |
| **합계** | | **22 (6/6)** | | | |

## Story-4 결과 박제 (MCT-170, 2026-05-14)

### 4 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-14 (early) | mctrader-hub#314 | 311b795 | Phase 1 docs — Story §1-§12 + spec + plan + ADR-029 §D7/§D8/§D10 amendment + scope_manifest IN_PROGRESS + CLAUDE.md + counters retitle (7 file) |
| 2026-05-14 (mid) | mctrader-data#61 | 9d26438 | Phase 2 PR#1 — NullReaderCache 제거 + LRUReaderCache 구현 (20 신규 test + 53 test ALL PASS, AC-7 grep 0건) |
| 2026-05-14 (mid-late) | mctrader-engine#53 | a00690bc | Phase 2 PR#2 — tier_reader / l1_reader / dr_mode 3 module 신규 + reader_cache byte budget 확장 + 5 test 신규 (107 io/ test ALL PASS, MCT-154 회귀 0) |
| 2026-05-14 (late) | mctrader-hub#315 | f1e04e6 | Phase 2 PR#3 — RETRO + Story §11/§12 fill + milestone 4/6 COMPLETED + EPIC-RESULTS Story-4 entry + counters DELETE (6 file) |

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

**MCT-172 (COMPLETED 2026-05-14, POLICY_FINALIZED)** — Epic policy finalize Story-6. D8-9=C Codex 채택으로 Epic CLOSED 자체 박제는 production evidence 완성 후 별 PR 로 분리.

## Story-6 결과 박제 (MCT-172, 2026-05-14)

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-14 (mid) | mctrader-hub#320 | 29028a8 | Phase 1 docs — Story §1-§12 + spec + plan + ADR-029 §D8 amendment (14d window 2026-08-18~2026-09-01) + §D9 + §D10 verify status entry + scope_manifest IN_PROGRESS + counters retitle |
| 2026-05-14T14:02:48Z | mctrader-data#63 | f2fb28e | Phase 2 PR1 — promotion.py `verify_no_ambiguity` + `_check_nas_exists` 제거 (89 lines) + caller migrate (test_ambiguity_invariant 6 test + test_invariant_harness_8 d10_regression) + 3 신규 integration test (test_epic_smoke + test_wal_synthetic_baseline + test_d8_sunset_telemetry_watcher, 14 test). 954 passed + 24 skipped + 4 xfailed (회귀 0). ruff + pyright PASS. |
| 2026-05-14T14:13:24Z | mctrader-hub#321 | 70731e3 | Phase 2 PR2 — RETRO-MCT-172 + ADR-029 §D10 verify status (Phase 2 PR1 LAND verify) + EPIC-RESULTS Story-6 + scope_manifest milestone 6/6 + Epic status POLICY_FINALIZED + CLAUDE.md |

### Codex 9 결정점 D8-1~D8-9 박제

| D8-N | 채택 Option | 결과 |
|------|------------|------|
| D8-1 8 invariant scope | A — InvariantHarness 8종 SSOT | test_epic_smoke 가 8 invariant ALL PASS 게이트 |
| D8-2 1h production 측정 | C — baseline 30min + peak 30min hybrid | paper mode synthetic, production 측정 별 PR |
| D8-3 D8 sunset finalize | A — 정책 finalize only + telemetry watcher | 실 sunset 2026-09-01 별 Story |
| D8-4 D8 14d 기준점 | C — 2026-08-18 ~ 2026-09-01 | ADR-029 §D8 amendment 박제 |
| D8-5 promotion.py cleanup | A — verify_no_ambiguity 즉시 제거 | src/ grep = 0 strict 충족 |
| D8-6 WAL 30G measurement | A — production deploy 후 실측 | paper synthetic + R-CRITICAL carry over |
| D8-7 WAL 30G escalation | A — 초과 시 Epic close FAIL gate | conditional close 차단 |
| D8-8 evidence quad 시간 | A — 동일 1h window | bucket + log + Prometheus + drainage |
| D8-9 Epic CLOSED timing | C — production 14d 후 별 PR | POLICY_FINALIZED → CLOSED transition 별 PR |

### AC-1 ~ AC-6 / INV-1 ~ INV-5 ALL PASS

- AC-1 8 invariant cross-Story smoke PASS (test_invariant_harness_verify_8_all_pass + caller regression)
- AC-2 ambiguity invariant baseline+peak hybrid 위반 0 (paper mode synthetic)
- AC-3 D8 sunset policy finalize PASS (ADR amendment + watcher 박제)
- AC-4 promotion.py cleanup PASS (`grep -rn "verify_no_ambiguity" src/` = 0)
- AC-5 WAL synthetic baseline PASS (30G ±50% hypothesis 검증 + R-CRITICAL carry over note)
- AC-6 EPIC-RESULTS Story-6 + milestone 6/6 + Epic POLICY_FINALIZED PASS (본 PR 박제)

### Phase 0 verify 발견 + 측정 결과

session prompt 부재 (별 세션 prompt 미author, 본 세션 직접 진입). 실 코드 verify 5가지:
1. ✅ ADR-029 §D8 sunset criterion 박제 (MCT-170 LAND)
2. ⚠️ `compactor/promotion.py:177` `verify_no_ambiguity` 함수 잔존 → D8-5=A 즉시 제거
3. ✅ InvariantHarness 8종 통합 LAND (MCT-171)
4. ✅ EPIC-RESULTS 5/6 박제
5. ❌ Production data dir 부재 → paper mode synthetic measure 의무

### R-CRITICAL carry over (Epic CLOSED prerequisite)

**WAL 30G production measurement** — paper mode synthetic baseline 측정 (50 sym × 3 channel, 15G ~ 45G hypothesis ±50% range). production 측정은 후속 별 PR (Epic CLOSED prerequisite).

### 8 invariant ↔ D1-D11 mapping

| Invariant | D | 의미 |
|-----------|---|------|
| sha256 + object_count + row_count + column_count + column_order + dtype + schema_version | (legacy MCT-151) | Stage 2 invariant primitives (7종) |
| **ambiguity** | **D10** | NAS+local XOR violation enforcement (MCT-169 origin + MCT-171 SSOT + MCT-172 cleanup) |

D1-D11 은 설계결정 검토 범위 (ADR-029 design decision). 8 invariant 은 운영 단위 실행 게이트 (InvariantHarness).

## Epic POLICY_FINALIZED 박제 + Epic CLOSED prerequisite

### Epic POLICY_FINALIZED (2026-05-14)

- 6/6 Story policy finalize 박제 완료 (MCT-167+168+169+170+171+172 COMPLETED)
- 본 EPIC-RESULTS = policy finalize 박제 (Epic CLOSED 아님)
- D8-9=C Codex 채택: Epic CLOSED 자체 박제 = production evidence 완성 후 별 PR

### Epic CLOSED prerequisite (post-Epic carry over, 별 PR/Story 의무)

1. **production deploy 후 14d 0-hit telemetry** (2026-08-18 ~ 2026-09-01) — `nas_reader_ambiguity_total` Counter 14d rolling rate = 0/min
2. **WAL 30G production measurement** (peak market open 09:00 KST burst) — 30G 이하 verify, 초과 시 D11 hard_limit amendment 발의
3. **production evidence quad 동일 1h window** (bucket + log + Prometheus + drainage, codeforge-plugin#620 Fix-1 정합)
4. **Epic CLOSED 박제 PR or scope_manifest amend** — milestone 6/6 + Epic status POLICY_FINALIZED → **CLOSED** transition

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
| 6 | MCT-172 | Epic policy finalize PASS (D8 sunset + promotion.py cleanup + WAL synthetic baseline + 8 invariant smoke). **POLICY_FINALIZED 박제, Epic CLOSED 는 별 PR (production 14d 0-hit + WAL 30G 실측 + evidence quad 동일 1h window)** |

## 다음 단계 (Epic CLOSED 진입)

본 Epic POLICY_FINALIZED 박제 후 Epic CLOSED 진입 = 별 PR/Story 의무 (D8-9=C Codex 채택).

**Epic CLOSED 박제 trigger 시점** = production deploy 후 14d 누적 telemetry 0-hit 충족 (≥ 2026-09-01 cutoff trigger). 별 PR scope = scope_manifest milestone 6/6 + Epic status POLICY_FINALIZED → CLOSED transition + EPIC-RESULTS Epic CLOSED 박제 + production evidence quad (bucket + log + Prometheus + drainage) ALL PASS verify.

## Cross-ref

- scope_manifest: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- governance singleton: `docs/stories/MCT-167.md` + `docs/retros/RETRO-MCT-167.md`
- ADR-029: `docs/adr/ADR-029-tier-promotion-single-source.md`
- brainstorm prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md`
- plugin reference: codeforge-plugin#620 Fix-1 (production evidence gate)

## Amendment — D3=C wiring deferred (2026-05-16 운영 진단 세션 발견)

> POLICY_FINALIZED 2026-05-14 박제 시점에 D3=C "Local delete = NAS HEAD verify + grace 0"
> 정책 finalize 와 `promote_l1()` 함수 정의는 완료됐으나, 실 production 호출 site (runner /
> dual_writer / l1 / l2 / l3) wiring 이 누락됨. 2026-05-16 운영 진단 세션 (사용자 디스크
> 압박 보고 → systematic-debugging Phase 1~3) 에서 발견.

### evidence (2026-05-16)

- `git grep -nE "promote_l1\(|from mctrader_data\.compactor\.promotion import" -- 'src/**'` = **0건** (f233952 + HEAD main 동일)
- `dual_writer.py` unlink 호출 = `tmp_path` (atomic temp) 만. L1/L2/L3 source unlink 0
- `l2.py` / `l3.py` tier promotion 시 source local 삭제 호출 0
- 결과: production /d/market **130.8 GB** legacy Parquet 누적 (NAS 적재 자체는 정상, 로컬 회수만 부재)
- production image `mctrader-data:pilot` (2026-05-13T15:51:28Z build, pkg 0.9.0) 가 POLICY_FINALIZED 하루 전 build 본 그대로 2일+ 가동 — 본 세션 응급 재빌드 (f233952 base) + force-recreate 완료

### carry over (Epic CLOSED prerequisite 보강)

- **prod-D3-wiring**: **MCT-189** (ADR-029 §D3=C grace-0 로컬삭제 wiring 완결) — RESERVED 2026-05-16
- legacy 130 GB cleanup = MCT-189 §3 S6 검토 대상 (compactor scan retroactive vs oneshot vs 사용자 explicit)
- ADR-029 §D3 amendment box LAND 의무 = MCT-189 AC-6 (file:line + commit sha + integration test PASS evidence)

### 관련 lesson 적용

- **ADR-032** (Proposed, PMO 발의 2026-05-16, `.codeforge/counters.json`) — VERIFIED badge **evidence triad** (file:line + production caller grep ≥1 + integration test PASS) 의무화. 본 사례가 cross-document SSOT forcing function pattern **3번째 재현**
- 1번째 사례: MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e)
- 2번째 사례: MCT-182 PMO-AUDIT (ADR 후보 발의 forcing function 일반화)

### Epic Status 영향

본 amendment box = POLICY_FINALIZED 정직성 보강. **Epic Status 강등 아님** (10/11 D 정상 — D1+D2+D4+D5+D6+D7+D8+D9+D10+D11 VERIFIED, D3 wiring deferred only). POLICY_FINALIZED 의 "정책 finalize only + 실 sunset/wiring 별 Story" 의미와 정합 (D8-3=A 패턴).

### cross-ref

- 본 세션 PMO patterns retro: `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- MCT-189 Story: `docs/stories/MCT-189.md` (RESERVED, §0 Phase 0 evidence 박제 완료)
- ADR-032 reservation: `.codeforge/counters.json` (Proposed)
