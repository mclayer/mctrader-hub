---
type: pmo-story-retro-audit
story_key: MCT-183
epic_key: EPIC-data-domain-decoupling
epic_status: phase:구현-IN_PROGRESS
milestone: "2/7"
story_status: COMPLETED
story_completed_at: "2026-05-16"
audit_date: "2026-05-16"
author: PMOAgent
scope: |
  단일 Story 완료 회고 감사 (게이트 준수 + FIX 루프 정합 + cross-Story 패턴 5회 누적 분석
  + ADR escalation 결정 발의 + 다음 Story 진입 권고). 본 Story 회고는 RETRO-MCT-183.md
  (Orchestrator self-write, lesson 4건 + cross-document SSOT 5회 누적 + ADR escalation 결정
  박제) + EPIC-RESULTS §Story-2 (ArchitectPL 박제) 가 SSOT. 본 문서는 PMO 횡단 감사 영역
  (게이트 준수 audit + cross-Story 트렌드 정밀 분석 + codeforge upstream ADR escalation
  결정 발의 + 사전 PMO-AUDIT-MCT-182 §4 forcing function ADR 후보 실증 평가).
verified_sources:
  - docs/stories/MCT-183.md (frontmatter COMPLETED + §0 Phase0 V1-V7 + §9.1/§9.2 verdict + §10 FIX Ledger 6 row + §11 LAND 6 PR + §11.2 AC/INV)
  - docs/retros/RETRO-MCT-183.md (Orchestrator self-write, lesson 4건 + ADR escalation 결정)
  - docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md (§Story-2 박제)
  - docs/change-plans/MCT-183-change-plan.md (§3.5 채택안 A + §3.6.1 grep gate v2 + §12.1-§12.4 FIX 박제)
  - docs/retros/PMO-AUDIT-MCT-182.md (선행 PMO 감사 §4 forcing function ADR 후보 — 본 Story 동형 재발 평가 input)
  - scope_manifests/EPIC-data-domain-decoupling.yaml (milestone 2/7 + D2 partial VERIFIED + epic_status_history)
  - .codeforge/counters.json (MCT-183 COMPLETED + land_prs 6건 + MCT-189 신규 drift 발견 + ADR-032 PMO 발의 box)
  - docs/adr/ADR-031-data-domain-decoupling.md (§D2 partial VERIFIED, cutover MCT-185)
  - docs/adr/ADR-027 + ADR-029 (MCT-183 amendment box VERIFIED)
---

# PMO Story 완료 감사 — MCT-183 (Layer 2 read 도메인 relocation → mctrader-data)

> PMOAgent 단일 Story 완료 trigger 회고 감사 (feedback_pmo_retro_mandatory + feedback_escalate_to_codeforge 정합).
> 자체 회고 (RETRO-MCT-183) 는 Orchestrator self-write SSOT — 본 문서는 **PMO 횡단 감사** 영역만 다룬다:
> (1) 게이트 준수 audit (Preflight·FIX 카운터·§10 FIX Ledger·§11 LAND 박제 정합 + §3.6.1 gate v2 forcing function 실효 평가)
> (2) cross-Story 패턴 정밀 분석 (cross-document SSOT desync **5회 누적** 트렌드 분석 + 사전 PMO-AUDIT-MCT-182 §4 forcing function ADR 후보 본 Story 동형 재발 실증 + 수동 gate 자체 결함 5회째 추가 발견)
> (3) **codeforge upstream ADR escalation 결정 발의** (Option B "plugin-level mechanical gate" 채택 권고 — Option A self-discipline 5회 한계 실증)
> (4) cross-Epic governance 발견 평가 (MCT-189 ADR-029 §D3=C wiring 0건 drift + ADR-032 VERIFIED badge evidence triad PMO 발의 — cross-document SSOT forcing function pattern 3번째 cross-Epic 재현)
> (5) 다음 Story (MCT-184) 진입 권고

## 1. Story 개요 (verified)

| 항목 | 값 |
|------|-----|
| Story | MCT-183 (sequential_phase 2, milestone 2/7) |
| Epic | EPIC-data-domain-decoupling (4-Layer 다중거래소 확장 아키텍처) |
| 결정 | D2 (read 도메인 relocation, partial — io relocate 완료) + D6 (ADR-029/027 amendment box) |
| 결과 | COMPLETED 2026-05-16. **AC 5/5 PASS / INV 6/6 PASS** (cross-repo, INV-6 compactor Protocol 무변경 V6 동명 risk 해소) |
| 신규 test | 8 (data tests/io/ 7 이전 + test_io_stats_no_engine_dep 1 신규) ALL PASS |
| 회귀 | cross-repo 신규 실패 0 (data 1020 / engine 879) |
| PR | 6 (hub#353 + data#70 + engine#58 + hub#354 + data 6450cfd lint-revert + hub Phase2 PR2) |
| ADR 산출물 | ADR-027 §D9 amendment box + ADR-029 io reader relocated 박제 (cutover confirm = MCT-185) + ADR-031 §D2 partial VERIFIED |
| FIX 루프 | **설계리뷰 iter1→2→3 max 3/3 → RESET path → post-RESET PASS** (3 trigger 0 충족 사용자 escalation 생략) + **구현리뷰 iter1 PASS FIX 0회** (MCT-182 lesson reapply 효과 검증) |

## 2. 게이트 준수 audit (PMO 핵심 책임)

### 2.1 lane gate 전수 검증

| lane | gate verdict | iter | 비고 |
|------|--------------|------|------|
| 요구사항 | PASS | iter1 | §0 Phase 0 Verify Gate V1-V7 박제 + V6 동명 risk (compactor.reader_cache.ReaderCache Protocol) 사전 발견 → namespace 분리 + INV-6 신설 |
| 설계 | PASS | iter1 | ArchitectPL Change Plan §12.1 1차 검수 + reader_cache.py:339-348 stats() lazy import (CodebaseMapper R1 가드 7회째 사전 차단) → 채택안 A internal no-op |
| **설계-리뷰** | **PASS (post-RESET)** | iter1→3 max → RESET → post-RESET 1 | P0×3(iter1)→×2(iter2)→×2(iter3, **max 3/3 도달**) → fix-ledger-schema 3 trigger 0 충족 → **Orchestrator RESET path 채택** → ArchitectPL 수렴 회귀(지정목록 탈피 + sibling MCT-182 canonical + §3.6.1 gate v2) → **Orchestrator 독립 verify PASS** (DesignReviewPL rate-limit 백그라운드 미완 대신 git/grep 직접 TEST1/TEST2 실증). `gate:design-review-pass` ✓ |
| 구현 | PASS | iter1 | 2 repo Phase 2 PR1 LAND (data#70 → engine#58 land_order 엄수), §8.5 Impl Manifest DeveloperPL self-write (hub#354) |
| **구현-리뷰** | **PASS FIX 0회** | iter1 | P0=0, P1=0, blocking 0. AC-1~5/INV-1~6 양 peer 독립 PASS. **§3.6.1 gate v2 post-LAND repo-wide grep 0줄 forcing function 실효 입증** → cross-document SSOT carry 사전 차단 (MCT-182 lesson reapply 효과 검증). `gate:code-review-pass` ✓ |
| 통합테스트 | SKIP | — | Epic 7/7 후 1회 (MCT-188 owner) — 정상 |
| 보안테스트 | SKIP | — | lanes.security_ai default false — 정상 |

**판정**: 6 lane 게이트 전수 PASS. 설계리뷰 **max 3/3 도달 → RESET path** (codeforge fix-ledger-schema 3 trigger 0 충족 path 적격 — 설계 수렴/INV 정합/PL divergence 없음 + 수렴 경로 명확 = 사용자 escalation 생략 정당). 구현리뷰 FIX 0회 = MCT-182 lesson reapply 효과 검증. 정상.

### 2.2 §10 FIX Ledger Orchestrator 독점 append 정합

- §10 헤더 명시: "Orchestrator 독점 append (fix-event-v1 contract). 본 에이전트 직접 기록 금지." ✓
- 6 row 모두 fix-event-v1 schema 준수 (iter / lane / category / mechanical_category / file / suggestion / resolution 7 column 충족) ✓
- 설계리뷰 iter1/2/3 + **RESET marker row** + **post-RESET 1 (설계-리뷰)** + **post-RESET 1 (구현-리뷰)** = 6 row append 정합 ✓
- iter3 resolution 에 RESET path 채택 근거 명시(3 trigger 0 충족 + 수렴 경로 명확) ✓
- post-RESET 설계-리뷰 row resolution 에 Orchestrator 독립 verify 근거 명시 (DesignReviewPL rate-limit 백그라운드 미완 대신 git/grep 직접 TEST1/TEST2 실증) ✓
- post-RESET 구현-리뷰 row resolution 에 §3.6.1 gate v2 forcing function 실효 입증 명시 (post-LAND repo-wide grep 0줄) ✓
- 잔여 carry (skipped test 본문 mctrader_engine.metrics import + engine setter 고아화) **명시적 carry-over** = MCT-185/188 owner 박제 ✓

**판정**: §10 Orchestrator 독점 append 룰 위반 0. fix-event-v1 contract 정합. RESET marker row 박제 = codeforge fix-ledger-schema RESET path 표준 충족.

### 2.3 §11 LAND timeline 정합 (6 PR 박제)

| land_order | repo | PR | commit | git verify |
|-----------|------|----|--------|-----------|
| 0 | hub Phase 1 | #353 | `29e9c0d` | (cross-repo, Phase 1 docs LAND) |
| 1 | data | #70 | `0e6f35b0` | (cross-repo, io/ 6 module 수령) |
| 2 | engine | #58 | `18275737` | (cross-repo, io/ 6 module + tests/io/ 7 삭제) |
| 3 | hub §8.5 | #354 | `d2f48fb` | (cross-repo, DeveloperPL CFP-39 self-write) |
| post-merge | data lint-revert | (in #70 후속) | `6450cfd` | (Codex pre-LAND audit → INV-1 byte-equivalence lint auto-fix 정정 흡수, MCT-182 cold path 동형 2회째) |
| 4 | hub Phase 2 PR2 | TBD (본 PR) | — | 박제 영역 |

**판정**: land_order hub P1→data→engine→hub §8.5→data lint-revert→hub P2 sequential 엄수. 역순 backout 보존 (Change Plan §9.3). post-merge `6450cfd` 가 Codex pre-LAND audit → 구현-리뷰 FIX 진입 사전 흡수 패턴(MCT-182 cold path 동형 2회째 — Codex sentry 역할 3회 연속 실증).

### 2.4 ADR-031 D-row ↔ scope_manifest §design_decisions 정합 (MCT-183 영역)

| D | option_chosen | owner_story | 상태 | 판정 |
|---|---------------|-------------|------|------|
| D2 | `io-relocate + cold-read-behind-REST` | `MCT-183 (io relocate) + MCT-185 (cold-read cutover)` | **partial VERIFIED 2026-05-16** (MCT-183 io relocate 완료, cutover pending MCT-185) | ✓ 정합 |
| D6 | `new-adr-031 + 3-amend` | `MCT-182 (ADR-031 publish) + MCT-188 (POLICY_FINALIZED + amend confirm)` | publish/D1 VERIFIED, amend pending | ✓ MCT-183 ADR-027/029 amendment box 박제 (실 amend confirm = MCT-185/188) |

**판정**: D2 partial VERIFIED 상태 정확 (io relocate 완료, cutover MCT-185 owner). D6 amendment box 박제 ↔ scope_manifest §epic_status_history 2 row 정합. MCT-179 lesson reapply 효과 누적 (Epic publish 시점부터 D-row 7/7 reconcile 투자가 후속 Story design FIX P0 회수 보장 — MCT-182 + MCT-183 2회 연속 검증).

### 2.5 §3.6.1 gate v2 forcing function 실효 평가 (RESET path 핵심 산출물)

| 항목 | gate v1 (iter2 박제) | gate v2 (RESET post-iter3) | 평가 |
|------|---------------------|---------------------------|------|
| scope | 5 산출물 지정 목록 | glob `docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md scope_manifests/EPIC-data-domain-decoupling.yaml` | gate v1 = ADR-031:139 미cover (iter3 P0-1-residual-2 carry 근본 원인) → gate v2 = 본 Epic 권위 SSOT 전수 + 차후 누락 방지 |
| pattern | `endpoint_router ?/ ?dr_mode relocated\|..로 relocated\(Layer2 소유\)\"` (조사 `로`/따옴표 고정) | `endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat\|이전)` (조사 optional + 따옴표 optional + 구분자 변형 + ko/en 동시 포괄) | gate v1 = ADR-031:139 변형(조사·따옴표 없음) NO MATCH (iter3 P0-2-gate 근본 원인) → gate v2 = 변형포괄 |
| self-verify | 없음 | TEST1 (포착력 — 구 pattern NO MATCH vs 신 pattern MATCH 실증) + TEST2 (false positive 0 — canonical NO MATCH 실증) | gate v1 자체 결함 탐지 불가 → gate v2 = self-verifying forcing function |
| sibling Story scope | MCT-183 산출물만 (지정목록 한계) | `docs/stories/MCT-18*.md` glob 으로 MCT-182 sibling Story 포함 → frontmatter+Continuity 표 owner-scope 박제 통일 | gate v1 = sibling SSOT 미고려 → gate v2 = repo-wide 전수성 |
| 실효 입증 | iter1→2→3 매 iter 1개 누락 발견 (5회 누적) | post-LAND **repo-wide grep 0줄 (rc=1)** + canonical 18건 + 구현-리뷰 FIX 0회 | gate v1 = 한계 명백 → gate v2 = **영구 차단 검증 완결** |

**판정**: §3.6.1 gate v2 = MCT-183 RESET path 의 핵심 산출물. 수동 gate v1 의 구조적 결함 (scope 지정목록 한계 + pattern 변형 미매치 + self-verify 부재 + sibling SSOT 누락) 4개 동시 해소. 구현-리뷰 lane 에서 PASS FIX 0회 실효 입증. **단**, 본 forcing function 은 Story 별 수동 박제 (매 Story 재구축 비용 + 누락 risk 잔존) — **§4 codeforge upstream ADR escalation 결정 발의의 직접 근거**.

### 2.6 게이트 준수 종합

전수 PASS. PMO 감사 발견 차단 사항 **0건**. 본 Story 의 운영 = **RESET path 첫 정상 발동 사례** (3 trigger 0 충족 path 적격 입증) + **forcing function gate v2 영구 차단 박제 1회 투자**. RESET path = 사용자 escalation 없이 수렴 가능한 정상 경로의 codeforge fix-ledger-schema 설계 의도 실증.

## 3. cross-Story 패턴 정밀 분석 (cross-document SSOT desync 5회 누적 + 사전 ADR 후보 실증 평가)

### 패턴 #1 — Phase 0 verify R1 가드 효과 검증 (긍정 패턴 누적, 7회째 사전 차단 + 8회째 사전 차단)

**docker-stack Epic 누적 6회 사후 발견** → **MCT-182 = 2건 사전 차단 (7회째)** → **MCT-183 = 3건 사전 차단 (8회째 누적)**:

| # | Story | 가설 / risk | 실상 / 정정 | 정정 시점 |
|---|-------|------------|------------|-----------|
| 1-6 | MCT-170/177/178/179/180 (선행 Epic) | (전수 6회 사후 발견 — PMO-AUDIT-MCT-182 §3 패턴 #1 참조) | — | 코드 작업 후 |
| 7 | MCT-182 | engine CandleModel 5곳 import | 4곳(docstring 오집계) | 요구사항 lane (코드 영향 0) ✓ |
| 7 | MCT-182 | scope_manifest aggregation flat | 패키지(core/scaled_int/contract_metadata) | 설계리뷰 FIX iter1 ✓ |
| **8-A** | **MCT-183** | engine src/ io/ 호출자 0 (dead-in-prod) 가정 | HEAD 재검증으로 사전 확증 (요구사항 lane 분리 grep) | **요구사항 lane (코드 영향 0)** ✓ |
| **8-B** | **MCT-183** | reader_cache 단일 namespace 가정 | V6 동명 risk — compactor.reader_cache.ReaderCache Protocol 동명 기존 → namespace `mctrader_data.io.*` 분리 + INV-6 신설 | **요구사항 lane** ✓ |
| **8-C** | **MCT-183** | reader_cache.py top-level import only 가정 (V5 grep) | `reader_cache.py:339-348` stats() lazy `from mctrader_engine.metrics import ...` (V5 top-level grep 미포착) → 채택안 A internal no-op 사전 정정 | **설계 lane (CodebaseMapper)** ✓ |

**PMO 판정**: docker-stack 6회 사후 발견 → 본 Epic MCT-182 2건 + MCT-183 3건 = **누적 5건 사전 차단**. R1 가드 패턴 (§0 Phase 0 Verify Gate + V-체크 박제 + CodebaseMapper deep-verify + sibling Story canonical) = **압도적 shift-left 성과 누적 검증 완결**. 후속 Story (MCT-184~188) 동일 reapply **강제** (Phase 0 verify gap 7회째 재현 0 유지 = R1 가드 ROI 회수 핵심 KPI).

**특기 사항 (MCT-183 의 진보)**: 8-C (lazy import) = V5 top-level grep 만으로는 미포착되는 **lazy/conditional import 패턴까지 CodebaseMapper deep-verify 가 사전 차단** — Phase 0 verify 의 깊이가 grep top-level → lazy import 까지 확장된 사례 첫 박제. 후속 Story 의 Phase 0 verify checklist 에 "lazy/conditional import grep" 의무 추가 권고.

### 패턴 #2 — cross-document SSOT desync 5회 누적 (수동 forcing function 구조적 한계 결정적 실증)

**5회 누적 동형 표** (RETRO §4.1 + 본 PMO 감사 정밀 분석):

| # | Story | iter | finding | 근본 원인 | 정정 방식 |
|---|-------|------|---------|----------|----------|
| 1 | MCT-179 | 설계리뷰 iter1 | ADR-030 D5/D8 swap stale (Out-of-scope 표 정의 swap) | scope_manifest SSOT desync 누적 (MCT-178 F-001 carry) | ADR-030 D1-D19 전수 reconcile (c8e4b8e) 1회 투자 |
| 2 | MCT-182 | 구현리뷰 iter1 | Change Plan §4.2("하위모듈 삭제") ↔ §6/§2.2("무중단 보존") self-contradiction | 설계리뷰 iter1 F-2 가 scope_manifest 만 정정, Change Plan §4.2 동반 정정 누락 (cross-document carry) | ArchitectPL Option A + §4.2 정정 + data#69 fix (4 산출물 수렴) |
| 3 | **MCT-183 iter1** | 설계리뷰 | ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 desync | scope_manifest §planned_adrs.amendments ADR-027 stale carry | ArchitectPL 4 산출물 동반 reconcile |
| 4 | **MCT-183 iter2** | 설계리뷰 | iter1 정정 후 연계 권위 4곳(D6 rationale + cross_repo + ADR-029:107-109 + Story §2) 2-module 축약 carry | 지정 5산출물 외 연계 권위 SSOT 누락 | ArchitectPL 6곳 canonical 통일 + §3.6.1 gate v1 박제 |
| 5 | **MCT-183 iter3 (max)** | 설계리뷰 | iter2 정정 후 ADR-031:139 reconcile scope 누락 + **§3.6.1 gate v1 자체 결함** (scope ADR-031 미cover + pattern 변형 NO MATCH) | **수동 forcing function 자체가 불완전 — 지정목록 + pattern 고정의 구조적 한계** | RESET path → ArchitectPL gate v2 (glob-scope + 변형포괄 + self-verify) + sibling MCT-182 canonical |

**PMO 판정 — 결정적 실증**:

1. **5회 누적 = 가설 검증 완결**: PMO-AUDIT-MCT-182 §4 forcing function ADR 후보 가설 ("cross-document SSOT 정합 부족 = 반복 패턴") 의 본 Story 동형 재발 **3회 추가 (iter1/iter2/iter3)** — 가설 검증 완결.

2. **수동 forcing function 자체 결함 실증 (iter3 P0-2-gate)**: ArchitectPL 이 iter2 에 박제한 §3.6.1 gate v1 자체가 iter3 에서 결함 발견 (scope ADR-031 미cover + pattern 변형 NO MATCH). 이는 PMO-AUDIT-MCT-182 §4 의 Option A (forcing function self-discipline) 자체의 **구조적 한계** 실증 — **수동 reconcile + 수동 gate 모두 "지정 목록" 의존 = 매 iter 1개 누락 발견 패턴**.

3. **RESET path + gate v2 = 임시 해결 (Story 별 비용)**: §3.6.1 gate v2 (glob-scope + 변형포괄 + self-verify TEST1/TEST2) = MCT-183 RESET path 의 핵심 산출물로 영구 차단 박제. **그러나 Story 별 수동 박제 = 매 Story 재구축 비용 + 누락 risk 잔존** → **plugin-level mechanical gate 일반화 = 일반해**.

4. **결론**: **§4 codeforge upstream ADR escalation 결정 발의** — Option B "plugin-level mechanical gate" 채택 권고 (Option A self-discipline 5회 한계 실증).

### 패턴 #3 — byte-equivalence + V-pin source = relocation Story 안전 invariant 일반화 검증 (2회 연속 효과)

- MCT-182 (contract relocate) + MCT-183 (read 도메인 relocate) 2회 모두 byte-equivalence 보존 → 회귀 0 (각 871/1020 PASS, 990/879 PASS)
- V-pin engine origin/main hash 박제 = engine#N 삭제 후 비교 source 영구 재현 가능 (MCT-182 source pin 부재 lesson reapply 효과 — MCT-183 §8.0 Phase 0 V-pin gate 박제)
- **일반화**: relocation/refactor-only Story 패턴의 안전 invariant 화 = **2회 연속 검증 완결**. 후속 MCT-185 (cold-read cutover) + MCT-186 (engine realtime cutover) reapply 의무 — Test Contract §8 INV-byte-equiv + Phase 0 V-pin gate 표준화 권고.

### 패턴 #4 — Codex pre-LAND audit → post-merge fix 흡수 패턴 (3회 연속 실증)

- MCT-182 cold path 동형 (data#69 fix1 carry) + MCT-183 lint-revert 동형 (`6450cfd` post-merge) = **2회 연속**
- 추가로 MCT-183 RESET path post-RESET 재검증에서 Orchestrator 독립 verify (DesignReviewPL rate-limit 백그라운드 미완 대신 git/grep 직접 TEST1/TEST2) = Codex sentry 역할의 일종 = **3회째 실증**
- **일반화**: Codex 독립 peer 의 넓은 검증 scope 가 구현-리뷰 FIX 진입 사전 흡수 sentry 역할 — R1 가드 보강 (3회 연속 실증). 후속 Story 도 Codex pre-LAND audit 명시적 운용 권고.

### 패턴 #5 — design lane FIX shift-left ROI baseline 갱신 (Epic 트렌드)

MCT-179 (docker-stack) Out-of-scope D1-D19 전수 reconcile 1회 투자 → MCT-180/181 연속 design P0×0 회수 패턴의 본 Epic reapply 추이:

| Story | design lane FIX P0 | 비고 |
|-------|-------------------|------|
| MCT-182 (Epic entry) | **P0×1** (2 finding, 1 iter) | Epic publish 시점부터 D1-D7 전수 reconcile 박제 — 선제 reapply |
| **MCT-183** | **P0×3→×2 (max 3/3 + RESET)** | cross-document SSOT carry 5회 누적 — design lane 핵심 부담 |

**판정**: MCT-179 lesson reapply 가 MCT-182 = P0×1 (모범 baseline) 으로 회수했으나, MCT-183 = P0×3→×2 max → RESET 로 **design lane 부담 증가 (회수 감퇴)**. 원인 = cross-document SSOT 산출물 개수 증가 (Epic 진행 누적 ADR-027/029/031 amendment box + sibling Story SSOT) → 수동 reconcile 한계 도달. **§4 codeforge upstream ADR escalation 으로 mechanical gate 일반화 시 회수 가능**. 후속 Story (MCT-184~188) 도 design lane FIX P0 추이 모니터링 의무 — P0×2 이상 누적 발생 시 ESCALATE trigger.

## 4. 🔴 codeforge upstream ADR escalation 결정 발의 (PMO 핵심 책임 — 본 감사의 최상위 산출물)

본 Story 의 FIX 루프 5회 누적 + 사전 PMO-AUDIT-MCT-182 §4 forcing function ADR 후보 의 본 Story **동형 재발 3회 추가** + §3.6.1 gate v1 (Option A self-discipline 형태) 자체 결함 1회 = **누적 6회 동형 패턴**. memory: feedback_escalate_to_codeforge (codeforge 사용 의무, consumer workaround 금지, upstream issue escalation) + feedback_cross_plugin_drift_detection (escalate-and-fix standard path: consumer 진단 → marketplace bulk fix PR + PMOAgent retro + ADR Amendment 후보 발의) 정합.

### 4.1 escalation 근거 (정량 박제)

| # | 근거 항목 | 수치 | 근거 SSOT |
|---|----------|------|----------|
| 1 | cross-document SSOT desync 누적 횟수 | **5회** (MCT-179 + MCT-182 + MCT-183 iter1+iter2+iter3) | RETRO-MCT-183 §4.1 + 본 PMO 감사 §3 패턴 #2 |
| 2 | 사전 PMO ADR 후보 동형 재발 횟수 | **3회 추가** (MCT-183 iter1+iter2+iter3 모두 동형) | PMO-AUDIT-MCT-182 §4 + 본 PMO 감사 §3 패턴 #2 |
| 3 | 수동 forcing function 자체 결함 횟수 | **1회 결정적 실증** (§3.6.1 gate v1 → iter3 P0-2-gate 자체 NO MATCH) | RETRO-MCT-183 §3.1 + Change Plan §3.6.1 self-verify TEST1/TEST2 |
| 4 | Story 별 수동 박제 비용 | **매 Story 재구축 + 누락 risk** (gate v2 박제 = MCT-183 RESET path 1회 비용, MCT-184~188 reapply 의무) | §3.6.1 gate v2 박제 + RESET path 비용 |
| 5 | RESET path 발동 횟수 | **1회 정상 발동** (3 trigger 0 충족 path 첫 사례) | §10 FIX Ledger RESET marker row |

### 4.2 ADR escalation draft (`pmo_output v1.adr_proposal` inline 반환 + codeforge marketplace issue 작성 권고)

```markdown
---
category: Process / Quality Gate / Cross-Document SSOT / Plugin-Level Forcing Function
title: "ADR-NNN: cross-document SSOT 정합 plugin-level mechanical gate — Option A self-discipline 5회 한계 실증 → Option B 채택 권고"
trigger: |
  EPIC-mctrader-docker-stack MCT-179 (SSOT desync 1회) + EPIC-data-domain-decoupling MCT-182 (1회) +
  MCT-183 iter1+iter2+iter3 (각 1회씩 3회 추가) = **누적 5회 동형 재발**. 사전 PMO-AUDIT-MCT-182 §4
  forcing function ADR 후보 (Option A self-discipline) 의 MCT-183 동형 재발 3회 + §3.6.1 gate v1
  (Option A 실 구현체) 자체 결함 1회 = **Option A 구조적 한계 결정적 실증**. 수동 forcing function +
  수동 gate 모두 "지정 목록" 의존 = 매 iter 1개 누락 발견 패턴.
---

## 배경

cross-document SSOT (Story spec / scope_manifest / ADR (다수) / Change Plan + sibling Story SSOT + 권위
이력 박제) 가 동일 결정/사실을 다른 layer 에서 박제할 때, **1차 정정 시 일부만 정정** 또는 **forcing
function gate 자체가 변형/sibling/scope 누락** → 후행 iter 또는 후행 lane (구현/구현리뷰) 에서 stale
산출물 발견 → carry FIX 발생.

### 사례 (verified, 누적 5회):

- **MCT-179** (EPIC-mctrader-docker-stack): ADR-030 Out-of-scope 표 D5/D8 정의 swap stale → MCT-179 ArchitectPL 전수 reconcile (c8e4b8e) 1회 투자
- **MCT-182** (EPIC-data-domain-decoupling): Change Plan §4.2 ↔ §6/§2.2 self-contradiction → ArchitectPL Option A + §4.2 정정 + data#69 fix
- **MCT-183 iter1**: ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 desync → ArchitectPL 4 산출물 동반 reconcile
- **MCT-183 iter2**: iter1 정정 후 연계 권위 4곳 2-module 축약 carry → ArchitectPL 6곳 canonical 통일 + §3.6.1 gate v1 박제 (Option A 실 구현체)
- **MCT-183 iter3 (max)**: iter2 정정 후 ADR-031:139 reconcile scope 누락 + **§3.6.1 gate v1 자체 결함** (scope ADR-031 미cover + pattern 조사/따옴표 변형 NO MATCH) → **Option A self-discipline 구조적 한계 결정적 실증** → RESET path + gate v2 (glob-scope + 변형포괄 + self-verify) 박제

## 문제

PMO-AUDIT-MCT-182 §4 ADR 후보 (Option A forcing function self-discipline) 의 본 Story 동형 재발
3회 + §3.6.1 gate v1 자체 결함 1회 = **Option A 구조적 한계 결정적 실증**:

1. **지정 목록 의존 한계**: ArchitectPL 이 지정한 산출물 목록 외 SSOT (sibling Story / 연계 권위 / 신규 추가 ADR) 누락 → 매 iter 1개 발견 패턴 (iter1→2→3, 매 iter 1개 누락)
2. **pattern 변형 사각**: 조사/따옴표/구분자/ko-en 변형이 수동 pattern 작성 시 누락 → 가장 흔한 변형이 NO MATCH (iter3 ADR-031:139 변형)
3. **self-verify 부재**: gate 자체의 포착력/false positive 자기검증 없음 → iter3 까지 결함 미발견
4. **Story 별 수동 박제 비용**: gate v2 가 영구 차단 박제됐으나 매 Story 재구축 + 누락 risk 잔존

수동 forcing function 의 구조적 한계 = **plugin-level mechanical gate** 일반화 필요.

## 제안 결정

**Option B (plugin-level mechanical gate, 채택 권고)**: codeforge plugin design lane (DesignReviewPL
또는 별도 deputy) 에 cross-document SSOT mechanical reconcile gate 신설:

1. **glob-scope auto-discovery**: `docs/adr/ADR-*.md docs/stories/<PREFIX>-*.md docs/change-plans/<PREFIX>-*.md scope_manifests/*.yaml` 자동 scope (Story 별 지정 목록 박제 불요)
2. **canonical extraction**: amendment box / D-row / 결정 record 의 canonical string 자동 추출 (Story §본문 amendment marker 박제 시 자동 인식)
3. **변형포괄 grep pattern auto-generation**: canonical string 에서 핵심 token (예: `endpoint_router`, `dr_mode`) + 거리/구분자/조사/ko-en 변형포괄 regex 자동 생성
4. **self-verify TEST1/TEST2 의무 산출물**: pattern 포착력(TEST1) + false positive 0(TEST2) 자기검증 결과 박제 의무
5. **sibling Story scope 자동 포함**: 동일 Epic 내 sibling Story SSOT 자동 scope 포함 (frontmatter related_adrs + Continuity 표 owner-scope)
6. **DesignReview lane verdict 직전 의무 실행 + post-LAND 회귀 grep gate**: 매 lane verdict 직전 + post-LAND 양 시점 mechanical gate 실 실행 + 결과 evidence 박제 (수동 박제 불요)

**Option A (self-discipline) 기각 근거**: PMO-AUDIT-MCT-182 §4 발의 + 본 Story 동형 재발 3회 + gate v1 자체 결함 = 5회 한계 결정적 실증.

## 예상 결과

- cross-document SSOT carry-over FIX **0회** (현 base 5/3 Epic 평균 → 0)
- design/code lane verdict 정합도 ↑ (1차 PASS 후 후행 carry FIX 발현률 ↓)
- Story 별 수동 박제 비용 0 (plugin auto-discovery + auto-pattern + auto-verify)
- RESET path 발동 빈도 ↓ (5회 누적 iter1→3 max 패턴의 근본 차단)
- sibling Story SSOT 자동 통합 = MCT-179 lesson 자동 reapply

## Out of scope

- Phase 0 verify gap (별 ADR 후보 — PMO-AUDIT-MCT-182 §3 ADR 후보 1건과 별건)
- mechanical gate plugin 구현 (본 ADR 은 정책 박제만, 구현은 codeforge plugin 별 Story)
- VERIFIED badge evidence triad (별 ADR-032 — PMO 발의, §4.4 참조)
```

### 4.3 escalation 처리 방식 (escalate-and-fix standard path 정합)

본 PMO 감사는 mctrader-hub 소비자 측. memory: feedback_escalate_to_codeforge (codeforge 사용 의무, consumer workaround 금지) + feedback_cross_plugin_drift_detection (escalate-and-fix standard path) 정합 처리:

| 단계 | 처리 | 산출물 |
|------|------|--------|
| (a) | **codeforge marketplace issue 작성** | 제목: "Cross-document SSOT desync forcing function — design lane mechanical reconcile gate 필요. 5회 누적 동형 재발 실증". 본문 = 본 §4.1 정량 박제 + §4.2 ADR draft 인용 + 5 사례 verified link (Story file:line + commit sha) |
| (b) | **`pmo_output v1.adr_proposal` inline 반환** | Orchestrator 경유 codeforge plugin ArchitectAgent author. 본 §4.2 ADR draft content 입력 |
| (c) | **본 PMO 감사 박제** | `docs/retros/PMO-AUDIT-MCT-183.md` §4 박제 = 차후 Story Phase 0 입력 의무 (mechanical gate 가용 시 활용 / 가용 전이라도 §3.6.1 gate v2 패턴 reapply) |
| (d) | **mctrader-hub 측 self-discipline 유지** | mechanical gate plugin 가용 전 까지 §3.6.1 gate v2 패턴 cross-Story reapply (MCT-184~188) |

### 4.4 cross-Epic governance 동형 재발 발견 (counters.json 검출) — 본 PMO 감사 정밀 분석의 결정적 산출물

**MCT-189 (2026-05-16 신규 reservation)** + **ADR-032 PMO 발의 (2026-05-16)** = cross-document SSOT forcing function pattern **3번째 cross-Epic 재현** (counters.json line 282-313 검증):

| 항목 | 발견 | severity |
|------|------|---------|
| **MCT-189** | ADR-029 §D3=C "NAS HEAD verify → grace-0 local delete" 가 MCT-169 D3 VERIFIED + EPIC-tier-promotion-single-source POLICY_FINALIZED 박제됐으나 `promote_l1()` production caller = **0건** (f233952 + HEAD main 동일 grep). DualWriter/l1.py/l2.py/l3.py 어디서도 NAS PUT commit 후 source local unlink 없음. 결과: **130GB legacy Parquet 영구 누적** | **HIGH (production 디스크 압박)** |
| **ADR-032** | PMO 발의 — VERIFIED badge evidence triad (file:line + production caller grep ≥1 + integration test result 3종 evidence 의무). 2026-05-16 운영 진단 세션에서 cross-document SSOT drift **2건 동시 발견** (1번째 = mctrader-data:pilot 이미지 2일 가동 / 2번째 = ADR-029 §D3=C wiring 0건). MCT-179 ADR-030 Out-of-scope reconcile + MCT-182 PMO 발의 cross-document SSOT forcing function pattern 의 **3번째 재현** → 일반화 룰 발의 | **process governance** |

**PMO 판정 — 본 §4 escalation 의 결정적 추가 근거**:

1. **cross-Epic 동형 재발**: 본 PMO 감사가 다루는 MCT-183 cross-document SSOT desync (Story-내 박제 ↔ ADR/scope_manifest 산출물 desync) 와 MCT-189 wiring drift (VERIFIED 박제 ↔ 실 production wiring 0건) 는 **동형 패턴** — "박제된 사실 ↔ 실 상태 의 desync". docker-stack MCT-179 (ADR-030 swap) → data-domain MCT-182/183 (산출물 5회 desync) → tier-promotion MCT-189 (wiring 0건 drift) = **3 Epic cross-Epic 누적**.

2. **ADR-032 = 본 ADR escalation 의 자매 후보**: 본 §4.2 ADR draft 는 "결정/사실 박제 시점 forcing function" (design lane), ADR-032 는 "VERIFIED 박제 evidence triad 의무" (post-VERIFIED enforcement layer). 두 ADR 후보 = **cross-document SSOT forcing function pattern 의 2 layer 일반화** — codeforge upstream escalation 시 양 ADR 동시 발의 권고 (또는 단일 ADR 통합 — codeforge ArchitectAgent 판단).

3. **escalation 우선순위 ↑**: 본 §4 escalation 의 정량 근거가 cross-Epic 3 사례로 확장 → **codeforge marketplace issue HIGH priority** 권고.

## 5. carry-over registry (post-Story)

RETRO-MCT-183 §5 carry-over 7건 + 본 PMO 감사 추가 1건:

| # | 항목 | severity | owner | 출처 |
|---|------|----------|-------|------|
| 1 | data tests/io/test_reader_cache_flush.py:215+221 skipped test 본문 mctrader_engine.metrics import 잔존 | non-blocking | MCT-185 | RETRO §5 |
| 2 | reader_cache.py stats() Gauge 실 emit 재배선 (data 측 동등 Gauge 신설 + producer wiring) | scope 외 | MCT-185 | RETRO §5 |
| 3 | engine `mctrader_engine.metrics.set_reader_cache_hit_ratio`/`set_reader_p99_ms` setter 고아화 | non-blocking dead code | MCT-185/188 | RETRO §5 |
| 4 | engine NAS 직독 폐기 실 amend confirm (ADR-029 §D2) | scope 외 | MCT-185 | RETRO §5 |
| 5 | data io/ production wiring (dead-in-data → live) | scope 외 | MCT-185 | RETRO §5 |
| 6 | data-free grep0 quad gate CI + ADR-029/027 본문 결정 무변경 → 실 amend confirm | scope 외 | MCT-188 POLICY_FINALIZED | RETRO §5 |
| 7 | **codeforge upstream ADR escalation 발의** (cross-document SSOT mechanical gate plugin-level + Option B 채택) | **HIGH 누적 6회** | **codeforge marketplace issue + PMO 발의** | RETRO §5 + 본 PMO §4 |
| **8** | **§3.6.1 gate v2 패턴 cross-Story reapply** (mechanical gate plugin 가용 전 까지 mctrader-hub self-discipline) | **process** | **MCT-184~188 owner** | **본 PMO §4.3** |

## 6. 다음 Story 진입 권고 (MCT-184)

### 6.1 진입 prerequisite

| # | 항목 | 상태 |
|---|------|------|
| 1 | MCT-183 Phase 2 PR2 MERGED (hub#TBD) | ✓ (본 PR LAND 시점) |
| 2 | ADR-031 §D2 partial VERIFIED + ADR-027/029 amendment box LAND | ✓ (cutover confirm = MCT-185 owner, MCT-184 영향 없음) |
| 3 | scope_manifest milestone 2/7 + epic_status_history 2 row | ✓ |
| 4 | counters.json MCT-183 COMPLETED + land_prs 6건 박제 | ✓ |
| 5 | RETRO-MCT-183 + EPIC-RESULTS §Story-2 박제 | ✓ |
| 6 | 본 PMO 감사 (PMO-AUDIT-MCT-183) 박제 (별 후속 PR 권고) | (본 작업 산출물) |

전수 충족. MCT-184 진입 가능.

### 6.2 MCT-184 진입 권고 (MCT-182+183 lesson 누적 reapply 의무 — 5 항목 + 추가 2 항목)

**MCT-184** (sequential_phase 3, milestone 3/7) — Layer 2 data REST API 신규 (FastAPI /v1 historical Arrow IPC + reverse-write POST). decisions: [D3, D6]. cross_repo: hub + data.

**필수 reapply 항목** (MCT-182+183 lesson 누적):

| # | 항목 | 출처 | 본 Story 추가 강조 |
|---|------|------|------------------|
| 1 | **R1 가드 + §0 Phase 0 Verify Gate (V-체크)** | MCT-182 lesson | data 측 web framework 0 (stdlib health_server 만) 가설 HEAD 재검증 + FastAPI 의존 도입 영향 deep-verify |
| 2 | **D-row 1:1 reconcile** (scope_manifest D3 ↔ ADR-031 amendment ↔ Change Plan §3) | MCT-179 lesson | D3 = REST boundary (실 신규 코드 도입 = 가장 큰 영향) → ADR-030 amendment box (data api service topology) 동반 reconcile 의무 |
| 3 | **cross-document SSOT forcing function self-discipline** (mechanical gate plugin 가용 전 까지) | 본 PMO §4.3 | **§3.6.1 gate v2 패턴 cross-Story reapply** (glob-scope + 변형포괄 + self-verify TEST1/TEST2). MCT-184 SSOT canonical string 박제 + gate 박제 의무 |
| 4 | **byte-equivalence 안전 invariant 검토** | MCT-182+183 lesson | 본 Story = **신규 REST 신설 (relocation 아님)** → byte-equiv N/A, Perf Baseline 필수 (TestContractArch) |
| 5 | **Phase 0 lazy/conditional import grep** | **MCT-183 8-C 신규 발견** | top-level grep + lazy/conditional import grep 의무 (MCT-183 reader_cache.py:339-348 lesson) |
| 6 | **Codex pre-LAND audit 명시적 운용** | MCT-182+183 lesson (3회 연속 효과) | data api/ 신규 시 lint/typing/test/security 4 axis Codex review 의무 |
| 7 | **MCT-189 wiring drift 동형 차단** | **본 PMO §4.4 신규 발견** | REST API 신설 시 endpoint ↔ production caller grep ≥1 확증 의무 (ADR-032 evidence triad 패턴 선제 reapply — production drift 사전 차단) |

### 6.3 R2 (MCT-41 블락) 영향 평가

MCT-184 = data api/ FastAPI 신규 (hub + data, **engine 비참여**) → MCT-41 파일 disjoint 병렬 안전 (scope_manifest §dependency.parallel_safe_with 정합). R2 위험 = MCT-186 owner (engine realtime cutover 시점에서 Phase 0 교차 검증, Orchestrator ordering 결정 책임).

## 7. Epic 진행 트렌드 baseline 갱신 (후속 PMO 감사 reference)

PMO-AUDIT-MCT-182 §7 baseline 갱신:

| 항목 | MCT-182 baseline | **MCT-183 갱신** | 트렌드 |
|------|------------------|------------------|--------|
| 설계리뷰 FIX P0 | 1회 (1 iter) | **3→2→2 (max 3/3 + RESET)** | ↑ (cross-document SSOT 부담 증가) |
| 구현리뷰 FIX P0 | 0회 (P1×2 boundary) | **0회 (FIX 0회)** | ↓ (gate v2 forcing function 효과) |
| ESCALATE | 0회 | 0회 (RESET path 1회 정상 발동) | — |
| Phase 0 verify gap | 0회 (사전 차단 2건) | **0회 (사전 차단 3건, 누적 8-C lazy import 신규)** | ↑ (Phase 0 deep-verify 깊이 확장) |
| 신규 test | 72 (회귀 0) | 8 (회귀 0) | (Story scope 차이 — relocation refactor-only) |
| ADR 산출물 | 1 신규 (ADR-031 Proposed→Accepted) | amendment box 2 (ADR-027/029) + ADR-031 §D2 partial VERIFIED | (D6 amendment 진행) |
| cross-repo PR | 7 | 6 | (Story scope 차이) |
| land_order 위반 | 0회 | 0회 | — |
| **cross-document SSOT desync 누적** | **1회** (Epic 내) | **누적 4회** (iter1+iter2+iter3, 본 Story) | **↑↑↑ (수동 forcing function 한계 결정적 실증)** |
| RESET path 발동 | 0회 | **1회 정상 발동** (3 trigger 0 충족 path 첫 사례) | — (정상 경로) |
| forcing function gate 영구 박제 | 0회 | **1회 (§3.6.1 gate v2 RESET path 산출)** | ↑ (Story 별 비용) |

**후속 Story 모니터링 KPI**:
1. **design lane FIX P0 누적 추이** = mechanical gate plugin 가용 전 까지 Story 별 cross-document SSOT 부담 측정 핵심 지표 (P0×2 이상 누적 시 ESCALATE trigger)
2. **Phase 0 verify gap 누적 0 유지** = R1 가드 ROI 회수 핵심 KPI (lazy/conditional import grep 의무 reapply)
3. **codeforge ADR escalation 처리 timeline** = mechanical gate plugin 가용 시점 = design lane FIX P0 회복 시점

## 8. 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | **전수 PASS** (6 lane + RESET path 1회 정상 발동 + post-RESET PASS + §10 fix-event-v1 6 row + §11 LAND 6 PR 정합 + D-row partial VERIFIED 정합) |
| §3.6.1 gate v2 forcing function | **영구 차단 박제 완결** (Story 별 수동 박제 = 1회 비용 + Story 비용 잔존) |
| cross-Story 패턴 | **5건 박제** (R1 가드 효과 8회째 누적 / cross-document SSOT 5회 누적 결정적 실증 / byte-equiv 안전 invariant 2회 연속 / Codex pre-LAND audit 3회 연속 / design lane FIX shift-left ROI 회수 감퇴) |
| 🔴 codeforge upstream ADR escalation | **결정 발의 (Option B 채택 권고 — Option A self-discipline 5회 한계 결정적 실증)** + **cross-Epic 3 사례 (MCT-179 + MCT-182 + MCT-183 + MCT-189) → HIGH priority 권고** |
| ADR-032 자매 발의 | **검출 + 권고** (VERIFIED badge evidence triad — cross-document SSOT forcing function pattern 의 2 layer 일반화 / codeforge upstream escalation 시 양 ADR 동시 발의 권고) |
| carry-over | **8건 registry** (MCT-185 owner 4건 + MCT-188 owner 2건 + codeforge upstream 1건 + MCT-184~188 self-discipline 1건) |
| 다음 Story | **MCT-184 진입 가능** (R1 가드 패턴 reapply 7 항목 의무 — 5 누적 + 2 신규 항목 lazy import grep + MCT-189 wiring drift 동형 차단) |

**PMO 결론**:

MCT-183 = **RESET path 첫 정상 발동 사례** + **§3.6.1 gate v2 forcing function 영구 차단 박제** 의 모범 운영 — codeforge fix-ledger-schema RESET path 설계 의도 실증 + 수동 forcing function 한계 결정적 실증 동시 달성.

**가장 중요한 산출물 = codeforge upstream ADR escalation 결정 발의** (Option B mechanical gate plugin-level 일반화). 사전 PMO-AUDIT-MCT-182 §4 가설 (Option A self-discipline) 의 본 Story 동형 재발 3회 + §3.6.1 gate v1 자체 결함 + cross-Epic 3 사례 = **누적 6회 결정적 실증** = escalation 정량 근거 충분. memory: feedback_escalate_to_codeforge + feedback_cross_plugin_drift_detection 정합 처리 (marketplace issue 작성 + `pmo_output v1.adr_proposal` inline 반환 + 본 PMO 감사 박제 + mctrader-hub self-discipline 유지).

**다음 Story MCT-184 진입 권고**: R1 가드 + cross-document SSOT self-discipline (§3.6.1 gate v2 패턴 reapply) + Phase 0 lazy import grep (MCT-183 신규) + Codex pre-LAND audit + **MCT-189 wiring drift 동형 차단 (REST endpoint ↔ production caller grep ≥1 확증 의무 — ADR-032 evidence triad 선제 reapply)** 7 항목 의무.
