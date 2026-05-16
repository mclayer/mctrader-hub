---
type: pmo-story-retro-audit
story_key: MCT-184
epic_key: EPIC-data-domain-decoupling
epic_status: phase:구현-IN_PROGRESS
milestone: "3/7"
story_status: COMPLETED
story_completed_at: "2026-05-16"
audit_date: "2026-05-17"
author: PMOAgent
scope: |
  단일 Story 완료 회고 감사 (게이트 준수 + FIX 루프 정합 + cross-Story 패턴 6회 누적 + 박제 PR
  자체 incomplete 패턴 3호 발견 + codeforge upstream ADR escalation 후보 2 + 후보 3 발의 +
  다음 Story 진입 권고). 본 Story 회고는 RETRO-MCT-184.md (self-write SSOT, post-LAND iter 1
  4건 박제 + dead-in-data 패턴 + SSOT drift 3호) + EPIC-RESULTS §Story-3 (ArchitectPL+PMO
  amendment 박제) 가 SSOT. 본 문서는 PMO 횡단 감사 영역 (게이트 준수 audit + cross-Story
  트렌드 정밀 분석 + codeforge upstream ADR escalation 결정 발의 + 사전 PMO-AUDIT-MCT-183 §4
  Option B forcing function ADR 후보 본 Story 동형 재발 평가 + 박제 lane 영역 확장).
verified_sources:
  - "docs/stories/MCT-184.md (frontmatter COMPLETED 2026-05-16 + §0 Phase 0 Verify Gate V1-V8 + §9.1 design iter1 PASS FIX 0회 + §9.2 BYPASS + §10 FIX Ledger 3 row + §11 LAND 4 행)"
  - "docs/retros/RETRO-MCT-184.md (self-write SSOT, 6 sections + post-LAND iter 1 F-1~F-4 박제 + dead-in-data 패턴 + SSOT drift 3호)"
  - "docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md (§Story-3 박제 + milestone 3/7 + D3 partial VERIFIED)"
  - "docs/change-plans/MCT-184-change-plan.md (§3.6.1 gate v2 reapply + Phase 0 Gate 선이행 인계)"
  - "docs/retros/PMO-AUDIT-MCT-182.md (선행 PMO 감사 §4 forcing function ADR 후보 1차 발의)"
  - "docs/retros/PMO-AUDIT-MCT-183.md §4 (codeforge upstream ADR escalation 결정 발의 — Option B 채택 권고)"
  - "docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md (1호+2호 자매 retro)"
  - "docs/retros/PMO-PATTERNS-2026-05-17-ssot-drift-3-archive-pr-incomplete.md (본 retro 동반 발의 — 3호)"
  - "scope_manifests/EPIC-data-domain-decoupling.yaml (milestone 3/7 + D3 partial VERIFIED + epic_status_history)"
  - "plugin-codeforge#795 (OPEN, phase:설계-리뷰, P0 priority): cross-document SSOT mechanical reconcile gate ADR escalation 1차 (MCT-183 PMO-AUDIT §4 발의)"
  - "plugin-codeforge#563 (OPEN, phase:요구사항): PMOAgent retro carrier 발의 시점 sibling open Story 자동 검색 forcing function"
  - "git log: hub#358 (1e96b47, 2026-05-16T14:09:50Z Phase 1) + data#72 (45e501c5, 2026-05-16T14:45:38Z) + hub#359 (4924b16, 2026-05-16T14:51:30Z 부분 박제) + hub#360 (fa7ea64, 2026-05-16T15:19:39Z amendment LAND)"
---

# PMO Story 완료 감사 — MCT-184 (Layer 2 data REST API 신규 — FastAPI /v1 historical + reverse-write)

> PMOAgent 단일 Story 완료 trigger 회고 감사 (feedback_pmo_retro_mandatory + feedback_escalate_to_codeforge
> + feedback_cross_plugin_drift_detection 정합). 자체 회고 (RETRO-MCT-184) 는 self-write SSOT —
> 본 문서는 **PMO 횡단 감사** 영역만 다룬다:
> (1) 게이트 준수 audit (Preflight·FIX 카운터·§10 FIX Ledger·§11 LAND 박제 정합 + §3.6.1 gate
>     v2 cross-Story reapply 실효 검증)
> (2) cross-Story 패턴 정밀 분석 (cross-document SSOT desync **6회 누적** + R1 가드 효과 8회째
>     누적 + dead-in-data evidence triad + SSOT drift 3호 신규 + Codex post-LAND audit 3회 연속)
> (3) **codeforge upstream ADR escalation 후보 2 + 후보 3 정식 발의** (박제 PR 자체 완결도
>     mechanical gate + post-merge audit lane 신설 — 사전 PMO-AUDIT-MCT-183 §4 Option B 후속)
> (4) cross-Epic governance 발견 평가 (MCT-189 wiring drift 동형 사전 차단 1회 실증)
> (5) 다음 Story (MCT-185) 진입 권고 (8 항목 reapply, 본 retro 신규 2 추가)

## 1. Story 개요 (verified)

| 항목 | 값 |
|------|-----|
| Story | MCT-184 (sequential_phase 3, milestone 3/7) |
| Epic | EPIC-data-domain-decoupling (4-Layer 다중거래소 확장 아키텍처) |
| 결정 | D3 (data REST API 신규 historical + reverse-write, partial — realtime stream + cold-read cutover = MCT-185 carrier) + D6 (ADR-031 amendment box LAND confirm) |
| 결과 | COMPLETED 2026-05-16. **AC 6/6 PASS / INV 6/6 PASS**. dead-in-data 신설 (production caller 0 + consumer=MCT-185, AC-6 wiring drift 차단 invariant) |
| 신규 test | 21 passed + 2 skipped (TC-4/TC-8 env-specific) |
| 회귀 | data 1152 passed ubuntu-latest 신규 실패 0 (fastapi/uvicorn 신규 의존 추가) |
| PR | 4 (hub#358 + data#72 + hub#359 + hub#360 박제 amendment) |
| ADR 산출물 | ADR-031 §D3 partial VERIFIED 박제 (cutover confirm = MCT-185) + ADR-030 amendment box (data api compose topology 예고, 실 amend = MCT-186) + ADR-029 §D2 접촉 (presigned-NAS-handoff 기각 재명시, 실 amend confirm = MCT-185) |
| FIX 루프 (pre-LAND) | **설계리뷰 iter 1 PASS FIX 0회** (P0/P1/P2 = 0/0/0, cross-document SSOT 6회째 §3.6.1 gate v2 사전 차단) + 구현리뷰 BYPASS (dead-in-data) |
| FIX 루프 (post-LAND) | **iter 1 post-merge fix 4건** (P0×3 + P1×1, Codex post-LAND audit 발견) — F-1/F-2/F-4 = data 측 production correctness fix (silent data corruption / INV-3 mismatch / bytes-level 정밀도) / F-3 = hub doc 측 (hub#360 amendment LAND ✅) |

## 2. 게이트 준수 audit (PMO 핵심 책임)

### 2.1 lane gate 전수 검증

| lane | gate verdict | iter | 비고 |
|------|--------------|------|------|
| 요구사항 | PASS | iter 1 | §0 Phase 0 Verify Gate V1-V8 박제 + PMO-AUDIT-MCT-183 §5 reapply 7항목 + ADR-032 evidence triad 선제 reapply (V8 = plugin-codeforge#795 OPEN + §3.6.1 gate v2 cross-Story reapply 의무) |
| 설계 | PASS | iter 1 | ArchitectPL Change Plan §3.6.1 gate v2 cross-Story reapply 박제 + dead-in-data 박제 결정 (D2/ADR-029 정합) + presigned-NAS-handoff 기각 재명시 |
| **설계-리뷰** | **PASS FIX 0회** | iter 1 | **lane-specific 8 검증 전수 PASS** — D-row↔scope_manifest 9/9 byte 1:1 + §3.6.1 gate v2 self-verify TEST1/TEST2 실증 + ADR-030 git diff 0 deletion POLICY_FINALIZED 보존 + AC-6 MCT-189 wiring drift 동형 ADR-032 evidence triad 차단 + SecurityArch primary (internal-only) + OperationalRiskArch CONDITIONAL §8.5 active + Arrow IPC byte-equiv INV-2 + Perf Baseline 필수 + §8.0 Phase 0 Gate. **cross-document SSOT desync 6회째 사전 차단 성공** (MCT-183 RESET path §3.6.1 gate v2 forcing function cross-Story reapply 실효 입증). `gate:design-review-pass` ✓ |
| 구현 | PASS | iter 1 | data#72 Phase 2 PR1 LAND (api/ 6 파일 + tests/api/ + pyproject), §8.5 Impl Manifest DeveloperPL self-write (hub#359). ubuntu CI 1152 passed 신규 실패 0 |
| **구현-리뷰** | **BYPASS (pre-LAND)** + **iter 1 post-merge fix 4건 (post-LAND)** | pre-LAND BYPASS + post-LAND 1 | **pre-LAND**: routes_v1 production caller 0 + consumer=MCT-185 → 구현-리뷰 BYPASS (별 lane = MCT-185 cutover 전 진입). **post-LAND (Codex audit 발견)**: F-1 (P0 invalid ts_utc silent substitute) + F-2 (P0 canonical_sha256 dead code INV-3 mismatch) + F-3 (P0 hub#TBD 잔존, hub#360 amendment LAND ✅) + F-4 (P1 arrow_ipc round-trip table 동등만 bytes-level X). **§3.6.1 gate v2 영역 ≠ Codex post-LAND audit 영역 실증** (gate v2 = SSOT 정합 / Codex = production correctness + bytes-level 정밀도) — codeforge upstream escalation 후보 3 직접 trigger |
| 통합테스트 | SKIP | — | Epic 7/7 후 1회 (MCT-188 owner) — 정상 |
| 보안테스트 | SKIP | — | lanes.security_ai default false — 정상. 단 SecurityArch primary 강함 (internal-only, T1 path traversal allowlist + T2 DoS bound 박제) |

**판정**: pre-LAND 6 lane 게이트 전수 PASS (설계리뷰 FIX 0회 = MCT-183 §3.6.1 gate v2 cross-Story
reapply 실효 검증). post-LAND iter 1 (Codex audit 발견 4건) = pre-LAND lane 영역 외 sentry 효과
실증 — production correctness + bytes-level 정밀도 영역의 박제 lane 의무 검증 부재 (codeforge
upstream escalation 후보 3 직접 trigger). 정상 처리 — F-3 hub 측 (본 audit 시점에 amendment LAND
✅) + F-1/F-2/F-4 data 측 별 post-merge fix PR carry (#795 unblock 후 진입).

### 2.2 §10 FIX Ledger Orchestrator 독점 append 정합

- §10 헤더 명시: "Orchestrator 독점 append (fix-event-v1 contract). 본 에이전트 직접 기록 금지." ✓
- 3 row 모두 정합:
  - 설계-리뷰 PASS FIX 0회 row (cross-document SSOT 6회째 §3.6.1 gate v2 사전 차단 evidence)
  - 구현 PASS row (data#72 ubuntu CI PASS + API 21 test PASS + ruff/pyright 0 error)
  - **iter 1 (구현-리뷰 post-merge)** row — error-handling × 2 (F-1/F-2) + impl-manifest × 2 (F-3/F-4) (P0×3 + P1×1). resolution 박제: F-3 = hub PR #360 amendment LAND ✅ / F-1+F-2+F-4 = data 측 post-merge fix PR carry (#795 unblock 후, MCT-185 cutover 진입 prerequisite gate)
- post-LAND iter 1 row 박제가 `lane` = "구현-리뷰 post-merge" 라벨링 = 신규 post-merge 분류 (codeforge fix-event-v1 schema 확장 후보 — 별 Story)

**판정**: §10 Orchestrator 독점 append 룰 위반 0. fix-event-v1 contract 정합. post-merge fix
별도 분류 (codeforge upstream 후보 3 lane 신설 시점 표준화 후보).

### 2.3 §11 LAND timeline 정합 (4 PR 박제)

| land_order | repo | PR | commit | git verify | 박제 내용 |
|-----------|------|----|--------|-----------|----------|
| 1 | hub Phase 1 | #358 | `1e96b47` | (MERGED 2026-05-16T14:09:50Z) | docs only — Story §1-§12 + ADR-031 §D3 amendment box + scope_manifest + CLAUDE.md MCT-184 IN_PROGRESS |
| 2 | data | #72 | `45e501c5` | (MERGED 2026-05-16T14:45:38Z, single repo) | Phase 2 PR1 — api/ FastAPI 6 파일 + tests/api/ + pyproject fastapi/uvicorn (21 API test PASS + ubuntu CI 1152 passed 신규 실패 0) |
| 3 | hub Phase 2 PR2 | #359 | `4924b16` | (MERGED 2026-05-16T14:51:30Z **부분 박제**) | Phase 2 PR2 hub — Story §8.5 Impl Manifest + ADR-031 §D3 LAND confirm + scope_manifest 3/7 + CLAUDE.md (RETRO + EPIC-RESULTS §Story-3 + frontmatter status + F-3 carry over) |
| 4 | hub 박제 amendment | #360 | `fa7ea64` | (MERGED 2026-05-16T15:19:39Z amendment LAND ✅) | **post-LAND completion** — RETRO-MCT-184.md 신규 + EPIC-RESULTS §Story-3 신규 + milestone 2/7→3/7 + D3 partial VERIFIED + Story frontmatter status COMPLETED 전환 + completed_at + §10 FIX Ledger post-merge iter 1 + F-3 hub#TBD→hub#359 정정 |

**판정**: land_order 4 PR sequential 엄수. **단 land_order 3 (hub#359) = 부분 박제 발견 (SSOT
drift 3호)** — PR title "Phase 2 PR2 박제 — milestone 3/7" 가 MERGED 됐으나 실 박제 산출물
carry-over ≈58% (RETRO 미생성 + EPIC-RESULTS §Story-3 미작성 + Story frontmatter status 미전환 +
F-3 hub#TBD 잔존). land_order 4 (hub#360, 약 28분 후) 가 박제 amendment 형태로 carry 해소 (본
audit 시점 LAND ✅). **§4 codeforge upstream escalation 후보 2 직접 trigger** (PR title SSOT ≠
박제 산출물 SSOT — mechanical gate 의무화 근거).

### 2.4 ADR-031 D-row ↔ scope_manifest §design_decisions 정합 (MCT-184 영역)

| D | option_chosen | owner_story | 상태 | 판정 |
|---|---------------|-------------|------|------|
| D3 | `fastapi-v1 + redis-stream` | `MCT-184 (historical+reverse-write) + MCT-185 (realtime stream + cold-read cutover)` | **partial VERIFIED 2026-05-16** (MCT-184 historical+reverse-write LAND, realtime stream + cold-read cutover pending MCT-185, F-1/F-2/F-4 post-merge fix carry) | ✓ 정합 |
| D6 | `new-adr-031 + 3-amend` | `MCT-182 (ADR-031 publish) + MCT-188 (POLICY_FINALIZED + amend confirm)` | publish/D1 VERIFIED (MCT-182) + D2 partial VERIFIED (MCT-183) + **D3 partial VERIFIED (MCT-184)** + amend confirm pending | ✓ MCT-184 ADR-031 §D3 amendment box LAND confirm + ADR-030 amendment box (data api topology 예고) + ADR-029 접촉 박제 (실 amend confirm = MCT-185/186/188) |

**판정**: D3 partial VERIFIED 상태 정확 (historical+reverse-write LAND, realtime stream + cold-
read cutover MCT-185 owner). D6 amendment box 박제 ↔ scope_manifest §epic_status_history 3 row
정합 (MCT-182 + MCT-183 + MCT-184). MCT-179 lesson reapply 효과 누적 (Epic publish 시점부터
D-row 7/7 reconcile 투자가 후속 Story design FIX P0 회수 보장 — MCT-182 P0×1 → MCT-183 P0×3
(max 3/3 + RESET) → **MCT-184 P0×0 FIX 0회** = §3.6.1 gate v2 cross-Story reapply 실효 + 회수
재증명).

### 2.5 §3.6.1 gate v2 cross-Story reapply 실효 평가 (MCT-184 핵심 forcing function 산출물)

MCT-183 RESET path 의 §3.6.1 gate v2 박제 (glob-scope + 변형포괄 + self-verify TEST1/TEST2) 가
MCT-184 에서 어떻게 reapply 됐는지 evidence 박제:

| 항목 | MCT-183 RESET 산출 gate v2 (Story 별 박제) | MCT-184 cross-Story reapply (본 Story) | 평가 |
|------|-----------------------------------------|-------------------------------------|------|
| glob-scope auto-discovery | `docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md scope_manifests/EPIC-data-domain-decoupling.yaml` | 동일 + `.codeforge/contracts/*.json` 추가 (MCT-184 OpenAPI snapshot 박제 영역 — V7 evidence) | ✓ reapply + 1 scope 확장 |
| canonical extraction | 5 산출물 manual list | Story §0 R1 가드 self-discipline 명문 (PMO-AUDIT-MCT-183 §5 reapply 7항목) | ✓ reapply |
| 변형포괄 grep pattern | `endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat\|이전)` (조사 optional + 따옴표 optional + 구분자 변형 + ko/en) | MCT-184 SSOT canonical string 박제 (Change Plan §3.6.1 owner) + 변형포괄 pattern reapply | ✓ reapply |
| self-verify TEST1/TEST2 | TEST1 (포착력) + TEST2 (false positive 0) | TC-11 INV-4 §3.6.1 gate v2 self-verify TEST1/TEST2 실증 + repo-wide grep 0줄 evidence | ✓ reapply + test 박제 |
| sibling Story scope | MCT-182 sibling canonical (MCT-183 박제) | **MCT-182 + MCT-183 sibling Story scope 자동 포함** (Story §0 PMO-AUDIT-MCT-183 §5 reapply 7항목 명문) | ✓ reapply + scope 확장 |
| 실효 입증 | post-LAND repo-wide grep 0줄 (rc=1) + canonical 18건 + 구현-리뷰 FIX 0회 | **post-LAND repo-wide grep 0줄 PASS** (cross-doc SSOT 6회 forcing function 실효) + **설계-리뷰 PASS FIX 0회** | ✓ reapply 효과 검증 |

**판정**: §3.6.1 gate v2 cross-Story reapply = **MCT-184 의 핵심 forcing function 효과**. MCT-183
RESET path 의 Story 별 박제 비용 (1회 투자) 이 MCT-184 = pre-LAND P0×0 FIX 0회 회수로 직접 실효
검증. **단** post-LAND Codex audit 발견 4건 (F-1/F-2/F-4 production correctness + bytes-level 정밀도)
은 gate v2 영역 외 — **§4 codeforge upstream escalation 후보 3 직접 trigger** (post-merge audit lane 신설).

### 2.6 게이트 준수 종합

pre-LAND 전수 PASS. post-LAND iter 1 (4건) = pre-LAND lane 영역 외 sentry 발견. PMO 감사 발견
차단 사항 **0건** (F-3 hub 측 amendment LAND 완료, F-1/F-2/F-4 data 측 별 PR carry — MCT-185
진입 prerequisite). 본 Story 의 운영 = **§3.6.1 gate v2 cross-Story reapply 실효 검증 + 박제 PR
자체 incomplete 패턴 신규 발견 + Codex post-LAND audit sentry 효과 3회 연속 실증**.

## 3. cross-Story 패턴 정밀 분석

### 패턴 #1 — Phase 0 verify R1 가드 효과 누적 (8회째 사전 차단)

docker-stack Epic 누적 6회 사후 발견 → MCT-182 2건 사전 차단 (7회째) → MCT-183 3건 사전 차단
(8회째) → **MCT-184 사전 차단 1회 (8회째 누적 확장)**:

| # | Story | 가설 / risk | 실상 / 정정 | 정정 시점 |
|---|-------|------------|------------|-----------|
| 1-6 | MCT-170/177/178/179/180 (docker-stack) | (전수 6회 사후 발견) | — | 코드 작업 후 |
| 7 | MCT-182 | engine CandleModel 5곳 import / scope_manifest aggregation flat | 4곳(docstring) / 패키지 | 요구사항 + 설계리뷰 iter1 ✓ |
| 8-A/B/C | MCT-183 | engine src/ io/ 호출자 가설 / reader_cache namespace / top-level grep only | HEAD 재검증 / V6 동명 risk → namespace 분리 + INV-6 / lazy import 잔존 발견 (`reader_cache.py:339-348`) | 요구사항 + 설계 lane ✓ |
| **9** | **MCT-184** | data web framework 0 + REST API 부재 + api/ namespace 부재 가설 (FastAPI 신규 도입 안전) | V1~V8 전수 HEAD 실증 = 정합 (data `git fetch origin` + grep + ls 직접 검증). **V6 lazy/conditional import grep 의무 reapply (MCT-183 8-C lesson)** = `git grep -nE "from mctrader_engine\|import mctrader_engine" -- 'src/mctrader_data/io/**/*.py'` = 0건 사전 확증 (MCT-183 채택안A no-op 치환 후 역의존 0 재검증) | **요구사항 lane (V1~V8 8 항목 전수)** ✓ |

**PMO 판정**: docker-stack 6회 사후 발견 → 본 Epic MCT-182 2건 + MCT-183 3건 + MCT-184 = **9회째
사전 차단 누적**. R1 가드 패턴 (§0 Phase 0 Verify Gate + V-체크 박제 + CodebaseMapper deep-
verify + sibling Story canonical + **lazy/conditional import grep 의무** MCT-183 신규) =
**압도적 shift-left 성과 누적 검증 완결**. 후속 Story (MCT-185~188) 동일 reapply **강제** (R1
가드 ROI 회수 핵심 KPI).

### 패턴 #2 — cross-document SSOT desync 6회 누적 (gate v2 cross-Story reapply 실효 + 박제 PR 자체 incomplete 신규)

**6회 누적 동형 표** (PMO-AUDIT-MCT-183 §3 패턴 #2 + 본 audit 갱신):

| # | Story | iter | finding | 근본 원인 | 정정 방식 |
|---|-------|------|---------|----------|----------|
| 1 | MCT-179 | 설계리뷰 iter1 | ADR-030 D5/D8 swap stale | scope_manifest SSOT desync | ArchitectPL 전수 reconcile (c8e4b8e) |
| 2 | MCT-182 | 구현리뷰 iter1 | Change Plan §4.2 ↔ §6/§2.2 self-contradiction | cross-document carry | ArchitectPL Option A + §4.2 정정 + data#69 fix |
| 3 | MCT-183 iter1 | 설계리뷰 | ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 desync | scope_manifest stale carry | ArchitectPL 4 산출물 동반 reconcile |
| 4 | MCT-183 iter2 | 설계리뷰 | iter1 정정 후 연계 권위 4곳 carry | 지정 5산출물 외 SSOT 누락 | ArchitectPL 6곳 canonical 통일 + §3.6.1 gate v1 박제 |
| 5 | MCT-183 iter3 (max) | 설계리뷰 | iter2 정정 후 ADR-031:139 reconcile scope 누락 + §3.6.1 gate v1 자체 결함 | 수동 forcing function 구조적 한계 | RESET path → ArchitectPL gate v2 (glob-scope + 변형포괄 + self-verify) |
| **6** | **MCT-184 (사전 차단)** | **설계-리뷰 PASS FIX 0회** | **§3.6.1 gate v2 cross-Story reapply 실효 검증** (lane-specific 8 검증 전수 PASS, repo-wide grep 0줄) | **MCT-183 RESET path forcing function effective** | **사전 차단 (gate v2 cross-Story reapply)** |
| **7** | **MCT-184 박제 PR 자체 incomplete (SSOT drift 3호 신규)** | **post-LAND** | hub#359 PR title "Phase 2 PR2 박제 — milestone 3/7" MERGED 그러나 RETRO 미생성 + EPIC-RESULTS §Story-3 미작성 + frontmatter status 미전환 + F-3 hub#TBD 잔존 (≈58% carry) | **PR title SSOT ≠ 박제 산출물 SSOT (forcing function 부재 영역 확장)** | hub PR #360 amendment LAND (fa7ea64, 약 28분 후) |

**PMO 판정 — 결정적 추가 실증**:

1. **gate v2 cross-Story reapply 실효 검증 (6회째 사전 차단)**: MCT-183 RESET path 의 §3.6.1
   gate v2 1회 투자가 MCT-184 = pre-LAND P0×0 FIX 0회 회수로 직접 실효 검증. **plugin-codeforge#795
   ADR escalation 의 추가 evidence row**.

2. **신규 발견 (SSOT drift 3호)**: gate v2 cover 영역 (Story-내 박제 SSOT 정합) 외 **박제 lane
   영역** (PR title SSOT ↔ 박제 산출물 완결도 SSOT) 에서 신규 drift 발견. PMO-PATTERNS-2026-05-17
   (본 retro 동반 발의) §2 SSOT drift 3호 정식 박제. **codeforge upstream ADR escalation 후보 2
   직접 trigger**.

3. **3호 root cause 동일**: 1호 (operational SSOT drift, MCT-189) + 2호 (design vs code SSOT drift,
   MCT-189) + 3호 (PR title vs artifact completeness SSOT drift, MCT-184) = 동일 root cause
   (badge SSOT ↔ 실 SSOT forcing function 부재) 의 3 layer 확장.

### 패턴 #3 — dead-in-data 박제 패턴 (ADR-032 evidence triad 선제 reapply, MCT-189 동형 사전 차단 1회 실증)

MCT-189 wiring drift (ADR-029 §D3=C VERIFIED 박제 vs `promote_l1()` production caller 0건) 동형
패턴이 MCT-184 = **dead-in-data 박제 + AC-6 wiring drift 차단 invariant** 로 사전 차단:

| 항목 | MCT-189 wiring drift (2호 SSOT drift) | **MCT-184 dead-in-data 박제 (사전 차단)** |
|------|----------------------------------------|-----------------------------------------|
| 박제 vs 실 wiring | ADR-029 §D3=C VERIFIED 박제 / 실 caller 0 | **AC-6 명시: "production caller 0 + consumer=MCT-185"** + routes_v1 `_get_writer()` 503 guard + TC-9 evidence triad |
| evidence triad | 부재 → 130GB legacy 누적 (HIGH severity) | **3종 evidence triad 박제**: file:line (routes_v1.py:191-196 / 244-247) + test (tests/api/test_rest_api.py TC-9) + dead-in-data 명시 (consumer=MCT-185 박제) |
| 정정 방향 | MCT-189 wiring 완결 + ADR-029 §D3 amendment + ADR-032 발의 | **사전 차단** — 박제 단계부터 dead-in-data 명시 + cutover Story (MCT-185) 진입 prerequisite gate |
| ADR-032 evidence triad 적용 | 발의 후 reapply 의무 | **선제 reapply** (Story §0 R1 가드 #7 항목 reapply) |

**PMO 판정**: MCT-184 = ADR-032 evidence triad 선제 reapply 1회 실증 — MCT-189 wiring drift
동형 패턴이 박제 단계부터 차단. **relocation / 신규 신설 Story 패턴의 안전 invariant 화 권고**
(MCT-185 cutover / MCT-186 / MCT-187 reapply 의무).

### 패턴 #4 — Codex post-LAND audit sentry 효과 3회 연속 실증 (post-merge audit lane 신설 trigger)

- MCT-182 cold path 동형 (data#69 fix1 carry) = 1회
- MCT-183 lint-revert 동형 (`6450cfd` post-merge) = 2회
- **MCT-184 F-1~F-4 post-LAND audit 4건** (P0×3 + P1×1) = **3회**

| Story | Codex 발견 영역 | severity |
|-------|---------------|---------|
| MCT-182 | cold path duckdb_resample.py + polars_fallback.py shim 우회 SSOT 이중화 | P1 (boundary) |
| MCT-183 | lint auto-fix INV-1 byte-equivalence 위반 (post-merge revert) | P1 (semantic boundary) |
| **MCT-184** | **F-1 invalid ts_utc silent substitute (production correctness)** + **F-2 canonical_sha256 dead code INV-3 mismatch (production correctness)** + **F-3 hub#TBD 잔존 (SSOT drift 3호)** + **F-4 arrow_ipc round-trip table 동등만 bytes-level X (정밀도)** | **P0×3 + P1×1** |

**일반화**: Codex post-LAND audit 가 production correctness + bytes-level 정밀도 영역의 sentry
역할 — **3회 연속 실증 = 의무 lane 화 trigger 충분**. 후속 Story 도 명시적 운용 의무 + **§4
codeforge upstream escalation 후보 3 직접 발의** (post-merge audit lane 신설 의무 lane 화).

### 패턴 #5 — design lane FIX shift-left ROI 회수 재증명 (Epic 트렌드 갱신)

PMO-AUDIT-MCT-183 §3 패턴 #5 baseline 갱신:

| Story | design lane FIX P0 | 비고 |
|-------|-------------------|------|
| MCT-179 (docker-stack) | 1회 (1 iter) | Out-of-scope D1-D19 전수 reconcile (c8e4b8e) — 선제 reapply baseline |
| MCT-180/181 (docker-stack) | 0회 (P0×0) | MCT-179 reconcile 회수 |
| MCT-182 (data-domain Epic entry) | 1회 (1 iter, P0×2) | D1-D7 전수 reconcile 박제 — 선제 reapply |
| MCT-183 | 3→2→2 (max 3/3 + RESET) | cross-document SSOT carry 5회 누적 — 부담 증가 |
| **MCT-184** | **0회 (P0×0, FIX 0회)** | **§3.6.1 gate v2 cross-Story reapply 실효 검증 (6회째 사전 차단) + MCT-179/182 D-row 전수 reconcile 회수 재증명** |

**판정**: MCT-179 lesson reapply (Epic 시점 D-row 전수 reconcile) + MCT-183 RESET path (§3.6.1
gate v2 박제) 의 **2단계 forcing function 투자가 MCT-184 = design FIX P0×0 으로 직접 회수
재증명**. 후속 Story (MCT-185~188) 도 design lane FIX P0 추이 모니터링 의무 — P0×2 이상 누적
시 ESCALATE trigger. **§4 codeforge upstream escalation 후 mechanical gate 가용 시점 = 회수
추이 가속 시점**.

## 4. 🔴 codeforge upstream ADR escalation 후보 2 + 후보 3 정식 발의 (PMO 핵심 책임 — 본 감사의 최상위 산출물)

본 Story 의 SSOT drift 3호 발견 + Codex post-LAND audit 3회 연속 실증 = **사전 PMO-AUDIT-MCT-183
§4 Option B mechanical gate ADR escalation (plugin-codeforge#795 OPEN) 의 enforcement layer
확장 + 후속 후보 2 + 후보 3 정식 발의 시점**. memory: feedback_escalate_to_codeforge (codeforge
사용 의무, consumer workaround 금지, upstream issue escalation) + feedback_cross_plugin_drift_detection
(escalate-and-fix standard path) 정합.

### 4.1 escalation 근거 (정량 박제 — PMO-AUDIT-MCT-183 §4.1 누적 갱신)

| # | 근거 항목 | 수치 | 근거 SSOT |
|---|----------|------|----------|
| 1 | cross-document SSOT desync 누적 (Story-내) | **5회** (MCT-179 + MCT-182 + MCT-183 iter1/iter2/iter3) | PMO-AUDIT-MCT-183 §4.1 |
| 2 | cross-document SSOT 사전 차단 누적 (gate v2 cross-Story reapply) | **1회** (MCT-184 pre-LAND P0×0 FIX 0회) | **본 audit §3 패턴 #2** |
| 3 | SSOT drift cross-Story layer 누적 (Story-내 + 박제 PR + operational + design vs code) | **3 layer** (MCT-189 1호+2호 + MCT-184 3호) | **본 audit + PMO-PATTERNS-2026-05-16 + PMO-PATTERNS-2026-05-17** |
| 4 | 박제 PR 자체 incomplete 발견 | **1회 (MCT-184 hub#359)** | **본 audit §2.3 + PMO-PATTERNS-2026-05-17 §1.2** |
| 5 | Codex post-LAND audit sentry 효과 연속 | **3회** (MCT-182 + MCT-183 + MCT-184) | **본 audit §3 패턴 #4** |
| 6 | Codex post-LAND audit P0 발견 | **MCT-184 F-1+F-2+F-3 = P0×3** (silent data corruption / INV-3 mismatch / SSOT drift) | **본 audit §3 패턴 #4** |
| 7 | pre-LAND gate v2 영역 외 발견 | **MCT-184 F-1/F-2/F-4** (production correctness + bytes-level 정밀도) | **본 audit §2.5 + 패턴 #4** |
| 8 | 박제 PR title vs 산출물 carry-over | **MCT-184 hub#359 ≈58% carry → hub#360 amendment** | **본 audit §2.3 + PMO-PATTERNS-2026-05-17 §1** |

### 4.2 후보 1 cross-ref — plugin-codeforge#795 추가 evidence row (cross-document SSOT mechanical gate)

`plugin-codeforge#795` (OPEN, phase:설계-리뷰) 의 1차 ADR escalation evidence 누적:

- **pre-LAND 영역 (gate v2 cover)**: MCT-179 + MCT-182 + MCT-183 5회 누적 → MCT-184 = **1회 사전 차단 (6회째)** = gate v2 cross-Story reapply 실효 1회 추가 실증
- **post-LAND 영역 (gate v2 cover 외)**: MCT-184 SSOT drift 3호 (박제 PR 자체 incomplete) 신규 발견 → **#795 ADR draft enforcement layer 확장 의견 첨부 권고** (PMO-PATTERNS-2026-05-17 §3.1 박제)

본 audit 시점 escalation 처리:
1. PMO-PATTERNS-2026-05-17 §3.1 의 enforcement layer 확장 의견을 **plugin-codeforge#795 first comment** 로 추가 (`gh issue comment 795 -R mclayer/plugin-codeforge`)
2. mctrader-hub MCT-184 PMO retro evidence row (2 issue 추가: gate v2 reapply 1회 실증 + 박제 PR 영역 신규 발견) 박제

### 4.3 후보 2 신규 발의 — 박제 PR 자체 완결도 mechanical gate

**`plugin-codeforge#NEW-A`** (또는 #795 의 amendment 형태 통합) — 상세 ADR draft = PMO-PATTERNS-2026-05-17 §3.2 박제. 핵심:

1. **trigger**: PMO-PATTERNS-2026-05-17 §2.1 의 SSOT drift 3호 (MCT-184 hub#359 부분 박제) 정량 evidence
2. **제안**: 박제 PR auto-classification (PR title 정규식 매칭 → `lane:archive` label 자동 부착) + 의무 산출물 5 grep gate (RETRO + EPIC-RESULTS §Story-N + frontmatter status + hub#TBD 잔존 0줄 + ADR amendment confirm)
3. **gate 결과**: 5 체크 전수 PASS → `gate:archive-complete` label 부착 + merge 가능 / 1+ FAIL → CI red + merge 차단

본 audit 시점 escalation 처리:
- `gh issue create -R mclayer/plugin-codeforge --title "[HIGH] 박제 PR 자체 완결도 mechanical gate (SSOT drift 3호 — MCT-184 mctrader consumer evidence)" --body ...` (PMO-PATTERNS-2026-05-17 §3.2 ADR draft 인용 + verified evidence)

### 4.4 후보 3 신규 발의 — post-merge audit lane 신설

**`plugin-codeforge#NEW-B`** — 상세 ADR draft = PMO-PATTERNS-2026-05-17 §3.3 박제. 핵심:

1. **trigger**: Codex post-LAND audit sentry 효과 3회 연속 실증 (MCT-182 + MCT-183 + MCT-184)
2. **제안**: `lane:post-merge-audit` 신설 — 박제 PR (lane:archive) MERGED 직후 자동 spawn → Codex 4 axis (production correctness + bytes-level 정밀도 + SSOT 재검증 + security) 의무 실행
3. **결과 처리**: finding 0 → `gate:post-merge-audit-pass` + Story COMPLETED 전환 가능 / finding P0/P1 → `lane:post-merge-fix` PR 자동 carry over (post-merge fix PR template 생성)
4. **non-blocking**: 박제 PR merge 차단 없음 (별 amendment PR 로 carry — SSOT 정합성 유지). dead-in-data Story 의 경우 cutover Story 진입 prerequisite gate 화

본 audit 시점 escalation 처리:
- `gh issue create -R mclayer/plugin-codeforge --title "[HIGH] post-merge audit lane 신설 — Codex sentry 3회 연속 실증 (MCT-182/183/184 mctrader consumer)" --body ...` (PMO-PATTERNS-2026-05-17 §3.3 ADR draft 인용 + Codex 4 axis finding evidence)

### 4.5 escalation 처리 방식 (escalate-and-fix standard path 정합 — PMO-AUDIT-MCT-183 §4.3 후속)

memory: feedback_escalate_to_codeforge + feedback_cross_plugin_drift_detection 정합 처리:

| 단계 | 처리 | 산출물 | 본 audit |
|------|------|--------|---------|
| (a) | **PMO retro 박제** | PMO-PATTERNS-2026-05-17-ssot-drift-3-archive-pr-incomplete.md + PMO-AUDIT-MCT-184.md (본 audit) | ✅ 본 retro 산출 |
| (b) | **codeforge marketplace issue 작성** | 후보 2 + 후보 3 2 issue 신규 발의 — `codeforge-improvement` + `priority:high` + `from-mctrader-debut` label. 후보 2 = [plugin-codeforge#804](https://github.com/mclayer/plugin-codeforge/issues/804) (박제 PR 자체 완결도 mechanical gate). 후보 3 = [plugin-codeforge#805](https://github.com/mclayer/plugin-codeforge/issues/805) (post-merge audit lane 신설) | ✅ LAND 2026-05-17 |
| (c) | **plugin-codeforge#795 first comment 추가** | 본 audit 의 3호 evidence row + design lane 영역 외 박제 lane 확장 의견 첨부 — [plugin-codeforge#795#issuecomment-4467280757](https://github.com/mclayer/plugin-codeforge/issues/795#issuecomment-4467280757) | ✅ LAND 2026-05-17 |
| (d) | **`pmo_output v1.adr_proposal` inline 반환** | 본 audit 의 ADR draft 2건 (PMO-PATTERNS-2026-05-17 §3.2 + §3.3) Orchestrator 경유 codeforge plugin ArchitectAgent author 후보 | PMO-PATTERNS-2026-05-17 §3 박제 |
| (e) | **mctrader-hub 측 self-discipline 유지** | mechanical gate plugin 가용 전 까지 MCT-185~188 owner 가 박제 산출물 5 체크리스트 self-discipline 의무 (Story §0 R1 가드 reapply 항목 #7 + #8 추가) | MCT-185~188 owner reapply 의무 |

### 4.6 cross-Epic governance 발견 평가 (PMO-AUDIT-MCT-183 §4.4 갱신)

PMO-AUDIT-MCT-183 §4.4 cross-Epic 발견 (MCT-189 + ADR-032 PMO 발의) baseline 갱신:

| 항목 | MCT-183 audit baseline | **MCT-184 audit 갱신** |
|------|----------------------|---------------------|
| cross-Epic 동형 재발 | 3 Epic (docker-stack MCT-179 + data-domain MCT-182/183 + tier-promotion MCT-189) | **4 layer 누적** (docker-stack + data-domain Story-내 + tier-promotion wiring + **data-domain 박제 PR 자체**) |
| ADR-032 evidence triad 적용 | PMO 발의 (MCT-189 LAND 시점 동시 후보) | **MCT-184 dead-in-data 박제로 선제 reapply 1회 실증** (사전 차단) |
| escalation priority | HIGH (cross-Epic 3 사례) | **HIGH 누적 4 layer + Codex sentry 3회 연속 = priority 강화** |

**PMO 판정**: 본 audit 의 cross-Epic governance 발견 = **ADR-032 evidence triad 의 선제 reapply
1회 실증 (사전 차단)** + **박제 PR 자체 incomplete 패턴 신규 발견 (4 layer 확장)**. PMO-AUDIT-
MCT-183 §4 ADR escalation 의 **enforcement layer 확장 충분 evidence + 추가 후보 2 + 후보 3
발의 정량 근거**.

## 5. carry-over registry (post-Story)

RETRO-MCT-184 §5 carry-over 10건 + PMO-PATTERNS-2026-05-17 §5 carry-over 5건 + 본 PMO 감사 추가
2건 = **통합 carry registry** (중복 제거):

| # | 항목 | severity | owner | 출처 |
|---|------|----------|-------|------|
| 1 | **F-1 invalid ts_utc silent substitute** (data api/routes_v1.py:191-196,244-247) | **P0** | data 측 post-merge fix PR (#795 unblock 후) | RETRO §5 + 본 audit §2.1 |
| 2 | **F-2 canonical_sha256 dead code** (sidecar pattern only INV-3 mismatch) | **P0** | data 측 post-merge fix PR (#795 unblock 후) | RETRO §5 + 본 audit §2.1 |
| 3 | F-4 arrow_ipc round-trip bytes-level 검증 보강 (INV-2 carrier 정밀도) | P1 | data 측 post-merge fix PR (MCT-185 cutover 전 정정 의무) | RETRO §5 + 본 audit §2.1 |
| 4 | AC-4 cross-repo-contract-lock-check.sh CI env 구성 (TC-8 skipped 해소) | non-blocking | MCT-185 carrier | RETRO §5 |
| 5 | reader_cache stats() / engine io/ Gauge setter 고아화 정리 | non-blocking dead code | MCT-185 / MCT-188 | RETRO §5 + PMO-AUDIT-MCT-183 §5 |
| 6 | engine NAS 직독 폐기 실 amend confirm (ADR-029 §D2) | scope 외 | MCT-185 cold-read REST cutover | RETRO §5 |
| 7 | data io/ production wiring (dead-in-data → live, REST endpoint actual caller 연결) | scope 외 | MCT-185 | RETRO §5 |
| 8 | data-free grep0 quad gate CI + ADR-029/027/030 본문 결정 무변경 → 실 amend confirm | scope 외 | MCT-188 POLICY_FINALIZED | RETRO §5 |
| 9 | **codeforge upstream ADR escalation 후보 1 cross-ref** — plugin-codeforge#795 first comment (3호 evidence row + design lane 영역 외 박제 lane 확장 의견) | **HIGH** | **PMOAgent 별 step** | RETRO §5 #9 + 본 audit §4.2 |
| 10 | **codeforge upstream ADR escalation 후보 2 발의** — 박제 PR 자체 완결도 mechanical gate (plugin-codeforge#NEW-A) | **HIGH 누적 3 layer** | **PMOAgent 별 step** | RETRO §5 #9 + 본 audit §4.3 |
| 11 | **codeforge upstream ADR escalation 후보 3 발의** — post-merge audit lane 신설 (plugin-codeforge#NEW-B) | **HIGH 3회 연속** | **PMOAgent 별 step** | RETRO §5 #10 + 본 audit §4.4 |
| 12 | **§3.6.1 gate v2 패턴 + 박제 PR 5 체크리스트 cross-Story reapply** (mechanical gate plugin 가용 전 까지 self-discipline) | process | **MCT-185~188 owner** | RETRO + PMO-AUDIT-MCT-183 §5 + 본 audit §4.5 (e) |
| 13 | **MCT-189 wiring drift 동형 차단 (ADR-032 evidence triad 선제 reapply)** | process | MCT-185 cutover Story | RETRO + 본 audit §3 패턴 #3 |
| 14 | **`feedback_pmo_retro_mandatory.md` memory 보강** — 박제 PR 자체 incomplete 패턴 감지 + amendment PR 발생 시 PMO retro 의무 spawn 룰 추가 | process | (사용자 결정) | PMO-PATTERNS-2026-05-17 §5 C4 |

## 6. 다음 Story 진입 권고 (MCT-185)

### 6.1 진입 prerequisite

| # | 항목 | 상태 |
|---|------|------|
| 1 | MCT-184 박제 amendment LAND (hub PR #360 fa7ea64) | ✅ 충족 (2026-05-16T15:19:39Z) |
| 2 | **F-1/F-2/F-4 data측 post-merge fix PR LAND** (silent data corruption + INV-3 mismatch + bytes-level 정밀도 차단) | **CARRY** — #795 unblock 후 별 세션 진입 (cutover 진입 prerequisite gate) |
| 3 | F-3 hub측 (Story §11 + §8.5.1 + CLAUDE.md hub#TBD → hub#359 정정) | ✅ 충족 (hub PR #360 LAND) |
| 4 | ADR-031 §D3 partial VERIFIED + ADR-030 amendment box LAND | ✅ 충족 (실 amend confirm = MCT-185/186/188) |
| 5 | scope_manifest milestone 3/7 + epic_status_history 3 row | ✅ 충족 |
| 6 | RETRO-MCT-184 + EPIC-RESULTS §Story-3 박제 | ✅ 충족 (hub PR #360 LAND) |
| 7 | 본 PMO 감사 (PMO-AUDIT-MCT-184) + PMO-PATTERNS-2026-05-17 박제 (별 후속 PR) | (본 작업 산출물) |

전수 충족 (F-1/F-2/F-4 data 측 post-merge fix PR 만 carry — cutover 진입 prerequisite gate).
MCT-185 진입 가능 단 F-1/F-2/F-4 LAND 후.

### 6.2 MCT-185 진입 권고 (MCT-182+183+184 lesson 누적 reapply 의무 — 8 항목 = 6 누적 + 2 신규)

**MCT-185** (sequential_phase 4, milestone 4/7) — Layer 2 data realtime stream (Redis Stream
정규화 publisher) + engine thin client (`data_client/` 신규, OpenAPI generated) + cold-read 실
호출부 cutover (mctrader_data.storage 직독 제거 + REST 경유). decisions: [D2 cold-read cutover,
D3 realtime stream]. cross_repo: hub + data + engine.

**필수 reapply 항목 — 8 항목** (MCT-182~184 lesson 누적 6 + 본 audit 신규 2):

| # | 항목 | 출처 | 본 Story 강조 |
|---|------|------|--------------|
| 1 | R1 가드 + §0 Phase 0 Verify Gate (V-체크) | MCT-182~184 lesson | engine `data_client/` 신규 namespace 부재 + Redis Stream publisher 신규 의존 영향 deep-verify (HEAD 재검증) |
| 2 | D-row 1:1 reconcile (scope_manifest D2/D3 ↔ ADR-031 amendment ↔ Change Plan) | MCT-179 lesson | D2 cold-read cutover (실 amend confirm) + D3 realtime stream (partial VERIFIED → VERIFIED 진전) — Epic ADR amendment 누적 4 layer 동반 reconcile 의무 |
| 3 | cross-document SSOT forcing function self-discipline (§3.6.1 gate v2 cross-Story reapply) | PMO-AUDIT-MCT-183 §4.3 + 본 audit §4.5 (e) | mechanical gate (#795) 미가용 전 까지 self-discipline 유지 + MCT-184 SSOT canonical 박제 sibling Story scope 포함 |
| 4 | Phase 0 lazy/conditional import grep | MCT-183 8-C | engine data_client/ 신규 시 lazy/conditional grep 의무 reapply |
| 5 | Codex pre-LAND audit + **post-LAND audit 의무** | MCT-182~184 lesson (3회 연속 효과) | data realtime stream + engine data_client/ 신규 시 pre-LAND 4 axis + **post-LAND 4 axis (production correctness + bytes-level 정밀도 + SSOT 재검증 + security)** 의무 운용 (codeforge upstream 후보 3 lane 미가용 전 self-discipline) |
| 6 | MCT-189 wiring drift 동형 차단 (ADR-032 evidence triad reapply) | MCT-184 AC-6 패턴 (1회 실증) | **dead-in-data → live cutover 전환 시 production caller grep evidence triad 갱신** (test/runtime/code 3종) — MCT-184 routes_v1 dead-in-data 박제가 MCT-185 cutover 시 live 전환 → evidence triad 갱신 의무 |
| **7** | **박제 PR 자체 완결도 self-discipline (mechanical gate #NEW-A 가용 전)** | **본 audit 신규 §4.3** | **박제 PR LAND 전 5 체크리스트 (RETRO 존재 + EPIC-RESULTS §Story-N + frontmatter status=COMPLETED + completed_at + CLAUDE.md hub#TBD 잔존 0줄 + ADR amendment confirm) self-discipline 의무** |
| **8** | **post-merge audit lane self-discipline (mechanical lane #NEW-B 가용 전)** | **본 audit 신규 §4.4** | **LAND 후 Codex post-LAND audit 4 axis 의무 운용** + finding 시 별 post-merge fix PR carry over template |

### 6.3 R2 (MCT-41 블락) 영향 평가

MCT-185 = data realtime stream + engine `data_client/` 신규 + cold-read cutover (hub + data +
engine 3 repo) → MCT-41 (Live Mode Debut) 와 engine 측 cross-cutting. **MCT-186 진입 전 MCT-43~47
IN_PROGRESS 파일 교차 검증 의무** (scope_manifest §dependency.parallel_safe_with 재평가 + R2
HIGH severity 완화 effective verify, Orchestrator ordering 결정 책임).

## 7. Epic 진행 트렌드 baseline 갱신 (후속 PMO 감사 reference)

PMO-AUDIT-MCT-183 §7 baseline 갱신:

| 항목 | MCT-182 baseline | MCT-183 갱신 | **MCT-184 갱신** | 트렌드 |
|------|------------------|------------------|------------------|--------|
| 설계리뷰 FIX P0 (pre-LAND) | 1회 (1 iter) | 3→2→2 (max 3/3 + RESET) | **0회 (PASS FIX 0회)** | ↓↓ (gate v2 cross-Story reapply 회수 실효) |
| 구현리뷰 FIX P0 (pre-LAND) | 0회 (P1×2 boundary) | 0회 (FIX 0회) | **BYPASS (dead-in-data)** | ↓ (dead-in-data 패턴) |
| **iter 1 (post-LAND Codex audit)** | 0회 (P1 hint cold path → fix1 carry) | 0회 (lint-revert) | **4건 (P0×3 + P1×1)** | **↑↑↑ (post-merge audit lane 필요성 결정적 실증)** |
| ESCALATE | 0회 | 0회 (RESET path 1회 정상 발동) | 0회 | — |
| Phase 0 verify gap | 0회 (사전 차단 2건) | 0회 (사전 차단 3건, 8-C lazy import 신규) | **0회 (사전 차단 1건 — V1-V8 전수 + lazy import grep reapply)** | (사전 차단 누적 9회) |
| 신규 test | 72 (회귀 0) | 8 (회귀 0) | 21 passed + 2 skipped (회귀 0) | (Story scope 차이) |
| ADR 산출물 | 1 신규 (ADR-031 Proposed→Accepted) | amendment box 2 (ADR-027/029) + §D2 partial | **§D3 partial VERIFIED + ADR-030 amendment box 박제 + ADR-029 접촉** | (D6 amendment 누적 진행) |
| cross-repo PR | 7 | 6 | **4 (single-repo data only)** | (Story scope 차이) |
| land_order 위반 | 0회 | 0회 | 0회 | — |
| **cross-document SSOT desync 누적 (Story-내)** | 1회 | 4회 (iter1+iter2+iter3) | **0회 (사전 차단)** | ↓↓ (gate v2 cross-Story reapply 회수) |
| **SSOT drift cross-Story layer 누적** | 0 | 0 | **3호 신규 (박제 PR 자체 incomplete)** | **↑ (新 layer 발견)** |
| RESET path 발동 | 0회 | 1회 정상 발동 | 0회 | — (정상 경로) |
| forcing function gate 영구 박제 | 0회 | 1회 (§3.6.1 gate v2) | **1회 cross-Story reapply 실효 검증** | (Story 별 비용 → cross-Story 회수) |
| **Codex post-LAND audit sentry** | 1회 (data#69 fix1) | 1회 (lint-revert) | **1회 (F-1~F-4 P0×3 + P1×1)** | **3회 연속 = 의무 lane 화 trigger** |

**후속 Story 모니터링 KPI 갱신**:

1. **design lane FIX P0 누적 추이 (pre-LAND)** = mechanical gate plugin 가용 전 self-discipline
   효과 측정 KPI. MCT-184 P0×0 = 회수 재증명. P0×2 이상 누적 발생 시 ESCALATE trigger (MCT-185~188 monitoring)

2. **post-LAND iter 1 Codex audit finding 추이** = post-merge audit lane 의무 lane 화 timeline
   monitoring. MCT-185 post-LAND finding ≥ 1건 시 lane #NEW-B 정량 evidence 강화

3. **Phase 0 verify gap 누적 0 유지** = R1 가드 ROI 회수 핵심 KPI (lazy/conditional import grep
   + V-체크 reapply 의무). MCT-184 = 9회 누적 사전 차단 유지

4. **SSOT drift cross-Story layer 추이** = mechanical gate #NEW-A 의무 lane 화 timeline. 4호
   발생 시 priority 가속

5. **codeforge ADR escalation 처리 timeline** = #795 LAND + 후보 2 + 후보 3 처리 = mctrader-
   hub self-discipline 회수 시점

## 8. 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | **pre-LAND 전수 PASS** (6 lane + 설계-리뷰 PASS FIX 0회 + 구현 PASS + 구현-리뷰 BYPASS) + **post-LAND iter 1 (4건 F-1~F-4 carry, F-3 hub LAND ✅ / F-1+F-2+F-4 data carry)** + §10 fix-event-v1 3 row + §11 LAND 4 행 정합 + D-row partial VERIFIED 정합 |
| §3.6.1 gate v2 cross-Story reapply | **실효 검증 완결** (Story 별 박제 1회 비용 → cross-Story 회수 1회 실증) |
| Codex post-LAND audit sentry | **3회 연속 실증** (MCT-182 + MCT-183 + MCT-184) + **MCT-184 P0×3 + P1×1 발견 = 의무 lane 화 trigger** |
| cross-Story 패턴 | **5건 박제** (R1 가드 효과 9회째 / cross-document SSOT 6회 누적 + 사전 차단 1회 / dead-in-data evidence triad 1회 실증 / SSOT drift 3호 신규 / Codex post-LAND 3회 연속) |
| 🔴 codeforge upstream ADR escalation | **후보 1 cross-ref (#795 first comment 추가) + 후보 2 신규 발의 (박제 PR 자체 완결도 mechanical gate, #NEW-A) + 후보 3 신규 발의 (post-merge audit lane 신설, #NEW-B)** |
| SSOT drift cross-Story 일반화 | **3 layer 정식 박제** (1호 operational + 2호 design vs code + 3호 PR title vs artifact completeness — 동일 root cause "badge SSOT ↔ 실 SSOT forcing function 부재") |
| carry-over | **14건 registry** (data 측 P0×2 + P1×1 + MCT-185 6 + MCT-188 1 + codeforge upstream 3 + self-discipline 2 + memory 보강 1) |
| 다음 Story | **MCT-185 진입 가능** (단 F-1/F-2/F-4 data 측 post-merge fix PR LAND prerequisite) — R1 가드 패턴 reapply 8 항목 (6 누적 + 본 audit 신규 2) |

**PMO 결론**:

MCT-184 = **§3.6.1 gate v2 cross-Story reapply 실효 검증 1회** (MCT-183 RESET path 의 Story 별
박제 비용 → cross-Story 회수 1회 실증) + **Codex post-LAND audit sentry 3회 연속 의무 lane 화
trigger** + **dead-in-data 박제 패턴 ADR-032 evidence triad 선제 reapply 1회 실증** (MCT-189
wiring drift 동형 사전 차단) + **박제 PR 자체 incomplete 패턴 SSOT drift 3호 신규 발견** (PR
title SSOT ≠ 박제 산출물 SSOT).

**가장 중요한 산출물 = codeforge upstream ADR escalation 후보 2 + 후보 3 정식 발의** (Option B
mechanical gate 영역 확장 — 박제 lane 영역 + post-merge audit lane 신설). 사전 PMO-AUDIT-MCT-183
§4 ADR escalation (cross-document SSOT mechanical gate, plugin-codeforge#795 OPEN) 의 enforcement
layer 확장 + 후속 후보 2 + 후보 3 정식 발의 정량 근거 = SSOT drift cross-Story 3 layer + Codex
post-LAND audit 3회 연속 + 박제 PR 자체 incomplete 1회 = 누적 결정적 실증.

**다음 Story MCT-185 진입 권고**: R1 가드 + cross-document SSOT self-discipline (§3.6.1 gate v2
cross-Story reapply) + Phase 0 lazy import grep + Codex pre-LAND + **post-LAND audit 의무 운용**
(lane #NEW-B 가용 전 self-discipline) + MCT-189 wiring drift 동형 차단 (evidence triad reapply)
+ **박제 PR 5 체크리스트 self-discipline** (mechanical gate #NEW-A 가용 전) **8 항목 의무**. 단
F-1/F-2/F-4 data 측 post-merge fix PR LAND 가 cutover 진입 prerequisite (silent data corruption +
INV-3 mismatch + bytes-level 정밀도 차단 의무 — #795 unblock 후 별 세션 진입).
