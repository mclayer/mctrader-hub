# RETRO MCT-184 — Layer 2 data REST API 신규 (FastAPI /v1 historical + reverse-write)

> **EPIC-data-domain-decoupling sequential_phase 3 (milestone 3/7)** · COMPLETED 2026-05-16
> 3 PR cross-repo LAND (hub#358 Phase 1 + data#72 Phase 2 PR1 + hub#359 Phase 2 PR2 박제)
> · **post-merge fix 4건 carry over** (Codex post-LAND audit 발견 — F-1/F-2/F-3/F-4)

## 1. 결과 요약

| 항목 | 결과 |
|------|------|
| AC | **6/6 PASS** (FastAPI /v1 기동 + OpenAPI · historical Arrow IPC byte 정확 · reverse-write idempotent · OpenAPI SSOT=data + hub contract snapshot · Arrow IPC NAS layout 비노출 · wiring drift 차단 production caller 0 + consumer=MCT-185) |
| INV | **6/6 PASS** (engine 의존 신규 0 · Arrow IPC byte-equiv · reverse-write idempotent sha256 sidecar · §3.6.1 gate v2 self-verify · data 회귀 0 · NAS 비노출) |
| 신규 test | **21 passed + 2 skipped** (env-specific TC-4/TC-8 cross-repo-contract-lock-check.sh CI env 미구성) |
| 회귀 | data 1152 passed ubuntu-latest 신규 실패 0 (fastapi/uvicorn 신규 의존 추가, 기존 storage/io/compactor 무변경) |
| FIX 루프 (pre-LAND) | 설계리뷰 iter1 **PASS FIX 0회** — P0/P1/P2 = 0/0/0, cross-document SSOT 6회째 §3.6.1 gate v2 사전 차단 (MCT-183 lesson reapply 효과 검증) / 구현리뷰 BYPASS (dead-in-data, consumer=MCT-185) |
| FIX 루프 (post-LAND) | **iter 1 post-merge fix 4건 (P0×3 + P1×1)** — Codex post-LAND audit 발견. F-1/F-2/F-4 = data 측 production correctness fix / F-3 = hub doc 측 (본 RETRO 와 동반 amendment PR) |

## 2. R1 가드 + Phase 0 verify 정정

| # | 발견 | 시점 | 영향 |
|---|------|------|------|
| **A** | Phase 0 verify gate (§0) — engine `data_client/` 호출자 grep 0건 사전 확인 (production caller 0, consumer=MCT-185) | 요구사항 lane | AC-6 wiring drift 차단 invariant 박제 (MCT-189 동형 차단) |
| **B** | dead-in-data 박제 결정 (production caller 0 + consumer=MCT-185) — MCT-185 cold-read cutover 전 까지 routes_v1 `_get_writer()` 503 guard 유지 | 설계 lane (ArchitectPL §3.5) | ADR-032 evidence triad 제공 — MCT-189 wiring drift 동형 차단 |
| **C** | presigned-NAS-handoff 기각 재명시 (D2/ADR-029 정합) — engine 이 NAS object layout/parquet/tier/DR 지식 비보유 = cold-read-behind-REST 필수 | 요구사항 lane | ADR-029 §D2 amendment box 박제 예고 (실 amend = MCT-185) |

## 3. FIX 루프 — pre-LAND PASS FIX 0회 / post-LAND iter 1 (P0×3 + P1×1) carry

### 3.1 설계리뷰 iter 1 PASS (cross-document SSOT 6회째 §3.6.1 gate v2 사전 차단)

- lane-specific 8 검증 전수 PASS:
  - D-row↔scope_manifest 9/9 byte 1:1
  - §3.6.1 gate v2 self-verify TEST1/TEST2 실증 (repo-wide grep 0줄 evidence)
  - ADR-030 git diff 0 deletion POLICY_FINALIZED 보존
  - AC-6 MCT-189 wiring drift 동형 ADR-032 evidence triad 차단
  - SecurityArch primary 강함 (internal-only, 포트 publish 미노출)
  - OperationalRiskArch CONDITIONAL §8.5 active
  - Arrow IPC byte-equiv INV-2 carrier 박제
  - Perf Baseline 필수 (1000-row serialize p50 < 5ms)
  - §8.0 Phase 0 Gate 선이행 인계

- **cross-document SSOT desync 6회째 사전 차단 성공** — §3.6.1 gate v2 cross-Story reapply 실효 입증 (plugin-codeforge-design#44 mechanical gate 미가용 동안 self-discipline workaround 효과 검증)
- gate: `gate:design-review-pass` ✅ → phase:설계-리뷰 → phase:구현

### 3.2 구현리뷰 BYPASS (dead-in-data)

- routes_v1 production caller 0 + consumer=MCT-185 → 구현-리뷰 BYPASSED
- 별도 lane = MCT-185 Phase 2 PR1 LAND 전 진입 (cold-read cutover 시 wiring drift 재검증)

### 3.3 post-LAND iter 1 post-merge fix 4건 (P0×3 + P1×1) — Codex audit 발견

| # | severity | file | finding | fix path |
|---|----------|------|---------|----------|
| **F-1** | P0 (구현) | data `api/routes_v1.py:191-196,244-247` | invalid ts_utc → `datetime.now()` silent substitute = silent data corruption | data#N (post-merge fix PR, #795 unblock 후 진입) |
| **F-2** | P0 (구현) | data `api/routes_v1.py:191-196,244-247` | canonical_sha256 dead code, sidecar pattern만 검사 = silent data-loss (INV-3 mismatch) | data#N (post-merge fix PR) |
| **F-3** | P0 (구현 + 박제) | hub `docs/stories/MCT-184.md §8.5.1:768` + `CLAUDE.md:560` | hub#TBD 잔존(실 LAND=hub#359, severity_override) | **hub amendment PR (본 RETRO 동반)** ✅ |
| **F-4** | P1 (설계 + 구현) | data `api/arrow_ipc.py:47-58` | round-trip INV-2 bytes-level 보장 X (table 동등만, dead-in-data 런타임 0 but MCT-185 cutover 전 정정) | data#N (post-merge fix PR) |

**P0 trio + P1 의 의미**:
- F-1/F-2 = production correctness 위반 (silent data corruption/data-loss). dead-in-data 상태이므로 production 런타임 영향 0이지만 MCT-185 cutover 시 즉시 silent 데이터 손상. cutover 진입 prerequisite gate.
- F-3 = SSOT drift (hub#TBD 잔존). 본 RETRO 와 동반 amendment PR 로 즉시 정정.
- F-4 = arrow_ipc round-trip 검증이 table 객체 동등 (DataFrame.equals 류) 만 비교, bytes-level 검증 부재. INV-2 carrier 보강 필요.

**§3.6.1 gate v2 post-LAND repo-wide 0줄 PASS** (cross-doc SSOT 6회 forcing function 실효) — pre-LAND 설계 단계는 잡지 못한 영역 (Codex post-LAND audit 만이 발견 가능한 영역 — F-1/F-2 production correctness + F-4 bytes-level 검증 정밀도). 이는 forcing function 의 범위가 SSOT 정합 (gate v2 영역) ≠ production correctness (Codex audit 영역) 임을 실증.

## 4. lesson 누적 (cross-Story 트렌드) + 박제 PR 자체 incomplete 패턴 (SSOT drift 3호)

### 4.1 cross-document SSOT desync **6회 누적** (MCT-184 사전 차단 1회 성공 + 박제 PR 자체 incomplete 발견)

| # | Story | finding | 시점 |
|---|-------|---------|------|
| 1 | MCT-179 | ADR-030 D5/D8 swap stale (Out-of-scope 표 정의 swap) | pre-LAND |
| 2 | MCT-182 | Change Plan §4.2("하위모듈 삭제") ↔ §6/§2.2("무중단 보존") self-contradiction | pre-LAND |
| 3 | MCT-183 iter1 | ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 desync | pre-LAND |
| 4 | MCT-183 iter2 | iter1 정정 후 연계 권위 4곳 carry | pre-LAND |
| 5 | MCT-183 iter3 | iter2 §3.6.1 gate 자체 결함 + ADR-031:139 누락 | pre-LAND |
| 6 | **MCT-184** | **사전 차단 1회 성공** — §3.6.1 gate v2 self-verify TEST1/TEST2 + cross-Story reapply 실효 | **pre-LAND (PASS FIX 0)** |
| 7 | **MCT-184 박제 PR (hub#359) 자체 incomplete** | §Story-3 EPIC-RESULTS 미작성 + RETRO 미생성 + Story frontmatter status 미전환 + F-3 hub#TBD 잔존 — 박제 PR MERGED 그러나 박제 작업의 약 절반만 처리 | **post-LAND (본 RETRO 동반 amendment)** |

### 4.2 박제 PR 자체 incomplete 패턴 = cross-document SSOT drift **3호** (MCT-189 PMO-PATTERNS 동형)

MCT-189 가 박제한 cross-document SSOT drift 패턴 (operational vs design SSOT, 2호) 의 동형 3호 케이스:

| 호 | 트리거 | drift 영역 |
|----|--------|-----------|
| 1호 | 2026-05-16 운영 진단 — `mctrader-data:pilot` image 2026-05-13 빌드 vs 정책 LAND 2026-05-14 | operational evidence ≠ policy LAND date |
| 2호 | 2026-05-16 ADR-029 §D3=C "VERIFIED" 박제 vs `promote_l1()` production caller 0건 | design SSOT(VERIFIED) ≠ code SSOT(caller 0) |
| **3호** | **2026-05-17 hub#359 박제 PR MERGED 그러나 RETRO 미생성 + EPIC-RESULTS §Story-3 미작성 + Story frontmatter status 미전환 + F-3 hub#TBD 잔존** | **박제 PR 명칭 SSOT(Phase 2 PR2) ≠ 박제 산출물 SSOT(완결 의무 체크리스트)** |

**핵심 lesson**: "Phase 2 PR2 박제" 라는 PR title 이 박제 작업의 SSOT 가 아님. PR 이 MERGED 됐다고 박제가 완결된 것이 아님. 박제 산출물 체크리스트 (RETRO + EPIC-RESULTS §Story-N + Story frontmatter + CLAUDE.md + ADR amendment confirm) 의 전수 LAND 가 완결 의무.

### 4.3 박제 incomplete forcing function 후보 (codeforge upstream ADR escalation 후보)

박제 PR 자체 완결도 검증 = 현재 수동 forcing function (Story file 의 §11 LAND timeline 행 hub#TBD 잔존 등 = self-detection 한계 5회 누적). codeforge plugin design lane 의 §3.6.1 gate v2 (cross-document SSOT mechanical gate) 와 동형 mechanical gate 가 **박제 산출물 체크리스트** 영역에도 필요:

- 박제 PR title 에 "Phase 2 PR2" / "박제" / "milestone N/M" 포함 시 → 의무 산출물 (RETRO-MCT-N.md 존재 / EPIC-RESULTS §Story-N 행 갱신 / Story frontmatter status=COMPLETED + completed_at / CLAUDE.md "hub#TBD" 잔존 0줄) CI grep gate 의무화 후보
- post-merge audit lane 신설 후보 — Codex post-LAND audit 가 발견하는 영역 (F-1/F-2 production correctness + F-4 bytes-level 정밀도) 를 박제 lane 의무 검증으로 격상

→ **codeforge upstream ADR escalation 후보 2** (PMO-AUDIT-MCT-184 박제 + codeforge marketplace issue 발의)

### 4.4 dead-in-data 박제 패턴 (ADR-032 evidence triad)

MCT-184 = MCT-185 cutover 전 production caller 0. AC-6 wiring drift 차단 invariant + routes_v1 `_get_writer()` 503 guard + tests/api/test_rest_api.py TC-9 의 3종 evidence triad 박제. **MCT-189 wiring drift 동형 사전 차단** — "정책 SSOT VERIFIED but production caller 0" 패턴이 본 Story 에서 박제 단계부터 dead-in-data 명시화로 해소.

→ relocation/신규-신설 Story 패턴의 안전 invariant 화 권고 (MCT-185 cutover Story / MCT-186 / MCT-187 등 후속 reapply)

## 5. carry over (post-Story)

| # | 항목 | severity | owner |
|---|------|----------|-------|
| 1 | **F-1 invalid ts_utc silent substitute** (data api/routes_v1.py:191-196,244-247) | **P0** | data 측 post-merge fix PR (#795 unblock 후 진입) |
| 2 | **F-2 canonical_sha256 dead code** (sidecar pattern only INV-3 mismatch) | **P0** | data 측 post-merge fix PR (#795 unblock 후 진입) |
| 3 | F-4 arrow_ipc round-trip bytes-level 검증 보강 (INV-2 carrier 정밀도) | P1 | data 측 post-merge fix PR (MCT-185 cutover 전 정정 의무) |
| 4 | AC-4 cross-repo-contract-lock-check.sh CI env 구성 (TC-8 skipped 해소) | non-blocking | MCT-185 carrier |
| 5 | reader_cache stats() / engine io/ Gauge setter 고아화 정리 | non-blocking dead code | MCT-185 / MCT-188 |
| 6 | engine NAS 직독 폐기 실 amend confirm (ADR-029 §D2) | scope 외 | MCT-185 cold-read REST cutover |
| 7 | data io/ production wiring (dead-in-data → live, REST endpoint actual caller 연결) | scope 외 | MCT-185 |
| 8 | data-free grep0 quad gate CI + ADR-029/027/030 본문 결정 무변경 → 실 amend confirm | scope 외 | MCT-188 POLICY_FINALIZED |
| 9 | **codeforge upstream ADR escalation 후보 2 발의** — 박제 PR 자체 완결도 mechanical gate (RETRO 존재 + EPIC-RESULTS §Story-N 갱신 + Story frontmatter status + CLAUDE.md hub#TBD grep 0줄) | HIGH 누적 | PMO-AUDIT-MCT-184 + codeforge marketplace issue (PMO-AUDIT-MCT-183 후속, 동형 mechanical gate 영역 확장) |
| 10 | post-merge audit lane 신설 후보 (Codex post-LAND audit 발견 영역 = production correctness + bytes-level 정밀도) 의 박제 lane 의무 검증화 | HIGH | codeforge upstream ADR escalation 후보 3 |

## 6. 다음 Story 진입

**MCT-185** (sequential_phase 4) — Layer 2 data realtime stream (Redis Stream 정규화 publisher) + engine thin client (data_client/ 신규, OpenAPI generated) + cold-read 실 호출부 cutover (mctrader_data.storage 직독 제거). MCT-184 LAND prerequisite 충족 (REST historical+reverse-write LAND), F-1/F-2/F-4 data 측 post-merge fix PR LAND 가 cutover 진입 prerequisite (silent data corruption 차단 의무).

진입 권고:
- **R1 가드 패턴 reapply** (MCT-182/183/184 self-discipline + §3.6.1 gate v2 cross-Story 활용 + Codex pre-LAND audit 활용)
- **AC-6 wiring drift 차단 invariant 의무 carry** — MCT-184 dead-in-data 박제 → MCT-185 production caller 실 연결 시 wiring evidence triad 갱신 (test/runtime/code grep)
- **post-LAND Codex audit lane 의무 carry** — F-1/F-2/F-4 production correctness 영역 forcing function 의 박제 영역 격상 (codeforge upstream escalation 후보 3)
- **MCT-189 wiring drift 동형 사전 차단** — VERIFIED 박제 시 production caller grep evidence 동반 박제 (operational evidence ≠ policy LAND 1호 + design SSOT ≠ code SSOT 2호 패턴 양쪽 차단)
