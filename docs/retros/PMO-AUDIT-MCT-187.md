---
type: pmo-story-retro-audit
story_key: MCT-187
epic_key: EPIC-data-domain-decoupling
epic_status: phase:IN_PROGRESS
milestone: "6/7"
story_status: COMPLETED
story_completed_at: "2026-05-17"
audit_date: "2026-05-17"
author: PMOAgent
scope: |
  단일 Story 완료 회고 감사 (게이트 준수 + FIX 루프 정합 + cross-Story 패턴 갱신 +
  code-change-zero Story 완결 검증 + windows-latest CI pre-existing regression 진단 +
  D5 invariant monkeypatch 패턴 박제 효과 검증 + 다음 Story 진입 권고).
  본 Story 회고는 RETRO-MCT-187.md (self-write SSOT, 9 sections) + EPIC-RESULTS §Story-6
  + Story §12 회고 (PMOAgent sub-dispatch) 가 SSOT. 본 문서는 PMO 횡단 감사 영역만 다룬다.
verified_sources:
  - "docs/stories/MCT-187.md (frontmatter COMPLETED 2026-05-17 + §0 Phase 0 Verify Gate V1-V7 + §8.5 Impl Manifest + §9/§10/§11 LAND 박제)"
  - "docs/retros/RETRO-MCT-187.md (self-write SSOT, 9 sections)"
  - "docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md (§Story-6 박제 + milestone 6/7)"
  - "docs/change-plans/MCT-187-change-plan.md (§3.4 TC-1~5 설계 + §3.6.1 gate v2)"
  - "docs/adr/ADR-031-data-domain-decoupling.md (§D5 VERIFIED amendment box 박제)"
  - "scope_manifests/EPIC-data-domain-decoupling.yaml (milestone 6/7 + D5 VERIFIED + epic_status_history)"
  - "git log: hub#374 (91a8bfa, 2026-05-16 Phase 1) + data#78 (6346b55, 2026-05-17 Phase 2 PR1) + hub#376 (7c806ef, 2026-05-17 Phase 2 PR2 박제)"
---

# PMO Story 완료 감사 — MCT-187 (다중거래소 확장 불변식 박제)

> PMOAgent 단일 Story 완료 trigger 회고 감사. 자체 회고 (RETRO-MCT-187) + Story §12 회고는
> self-write SSOT — 본 문서는 **PMO 횡단 감사** 영역만 다룬다:
> (1) 게이트 준수 audit (code-change-zero Story 검증 + FIX 1 iter ruff lint + §11 LAND 박제 정합)
> (2) cross-Story 패턴 분석 (windows CI pre-existing regression 진단 패턴 + monkeypatch invariant 박제)
> (3) codeforge upstream ADR escalation 후보 evidence row 갱신 누적
> (4) Epic 진행 트렌드 갱신 (milestone 6/7) + 다음 Story (MCT-188) 진입 권고

## 1. Story 개요 (verified)

| 항목 | 값 |
|------|-----|
| Story | MCT-187 (sequential_phase 6, milestone **6/7**) |
| 구분 | **code-change-zero Story** (adapters.py 변경 0 — INV-2 PASS) |
| 완료일 | 2026-05-17 |
| Phase 1 PR | hub#374 (91a8bfa MERGED 2026-05-16) |
| Phase 2 PR1 | data#78 (6346b55 MERGED 2026-05-17) |
| Phase 2 PR2 | hub#376 (7c806ef MERGED 2026-05-17) |
| AC PASS | 4/5 (AC-5 CONDITIONAL — ADR-030 NAS cred carry) |
| FIX 루프 | **1 iter** (ruff lint — F401×3+E721+F841, edda216) |
| ADR-031 §D5 | **VERIFIED** (Phase 2 PR2 박제, 본 감사 시점) |

## 2. 게이트 준수 audit

### 2.1 박제 PR 5 체크리스트 이행 (MCT-185/186 패턴 재사용)

| 항목 | MCT-187 이행 |
|------|-------------|
| RETRO-MCT-187.md 존재 | ✅ (docs/retros/RETRO-MCT-187.md — 9 sections) |
| EPIC-RESULTS §Story-6 박제 | ✅ (hub#376 포함) |
| Story frontmatter status=COMPLETED + completed_at | ✅ (2026-05-17) |
| ADR-031 §D5 VERIFIED amendment box LAND confirm | ✅ (hub#376 포함) |
| scope_manifest 6/7 + epic_status_history | ✅ (hub#376 포함) |

### 2.2 FIX Ledger §10 정합

| iter | lane | severity | 내용 | 상태 |
|------|------|----------|------|------|
| 1 | 구현 | P2 | ruff F401×3 + E721 + F841 (test_multi_exchange_invariant.py 초안) | FIXED (edda216) |

FIX 루프 1회 = **ruff lint 자동/수동 fix**, code logic 변경 0. design lane FIX 0.

### 2.3 windows-latest CI pre-existing regression 진단

**사실 확인**:
- MCT-187 신규 test 파일 = 1183 ubuntu-latest passed 포함 완전 PASS
- `X Test` 실패 = `test_promote_l1_post_put_unlink.py` (7 error) + `test_runner_retroactive_cleanup.py` (5 error)
- 실패 원인 = testcontainers ryuk `docker.errors.APIError: 500 ... /var/run/docker.sock Windows 불호환`
- main branch 동일 실패 확인 (pre-existing regression, MCT-187 scope 외)
- `phase-gate-mergeable` = PASS (ubuntu-latest PASS 기준) → admin merge 정당

**PMO 판정**: MCT-187 scope 외 — admin merge 정당 (ubuntu-latest PASS + phase-gate 충족). windows testcontainers 별 Story 또는 CI 개선 권고 (carry over).

## 3. cross-Story 패턴 분석

### 3.1 code-change-zero Story 완결 검증 패턴

MCT-187 = EPIC-data-domain-decoupling 첫 **code-change-zero Story** (adapters.py 변경 0).
MCT-172 (MCT-172 = Epic POLICY_FINALIZED 박제 only, promotion.py 89 lines deleted = 제거만) 이후
순수 test 박제 + runbook + ADR VERIFIED 조합 패턴.

**성공 요인**:
1. Phase 0 verify 에서 "adapters.py 팩토리 이미 완비 (V1-V2)" 실증 → 코드 변경 0 확정
2. invariant test = monkeypatch 패턴 (adapters.py 변경 0 원칙 SSOT 정합)
3. FIX = ruff lint 1 iter (code logic 변경 0)

**MCT-188 권고**: D7 quad gate CI = code 신규 (workflow 신설 + pyproject 수정) + engine 제거 혼합 — Phase 0 verify 의무 (engine pyproject 의존 현황 grep 실측).

### 3.2 D5 invariant monkeypatch 패턴 박제 (ADR-032 evidence triad 2회 연속 PASS)

MCT-186 ADR-031 §D4 evidence triad (file:line + caller grep + integration test) 이어
MCT-187 ADR-031 §D5 evidence triad (5 TC table + adapters.py diff 0 + ubuntu-latest suite) 박제.

| Story | ADR 섹션 | evidence triad | 패턴 |
|-------|----------|----------------|------|
| MCT-186 | §D4 | file:line + caller grep0 + testcontainers 4 test | 구현 evidence |
| MCT-187 | §D5 | 5 TC table + diff 0 + 1183 passed | 불변식 evidence |

ADR-032 evidence triad 2회 연속 선제 reapply = **MCT-185 LAND 이후 3회 누적**. cross-Story 자기규율 정착 확인.

### 3.3 §3.6.1 gate v2 cross-Story reapply (MCT-182~187 = 6회 연속)

| Story | P0 D-row desync | gate v2 결과 |
|-------|----------------|-------------|
| MCT-182 | 2건 사전차단 | PASS (재조정) |
| MCT-183 | RESET path 3/3 | PASS (post-RESET) |
| MCT-184 | 6회째 사전차단 | PASS (FIX 0) |
| MCT-185 | 7회째 성공 | PASS (FIX 0) |
| MCT-186 | cli.py scope P0 | CONDITIONAL_PASS |
| **MCT-187** | **desync 0** | **PASS (FIX 0, design)** |

MCT-187 = design lane FIX 0 (P0=0). §3.6.1 gate v2 누적 자기규율 + Phase 0 verify 독립 + ADR-032 evidence triad reapply 3종 복합 효과 = **design code FIX 0 4회 누적** (MCT-184/185/187 design P0=0 + MCT-185 code FIX 0).

### 3.4 Epic 진행 트렌드 (milestone 6/7)

| Story | design FIX | code FIX | 패턴 |
|-------|------------|----------|------|
| MCT-182 | P0×3 iter3 | P0×2 iter2 | 초기 cross-repo 정착 |
| MCT-183 | P0×3 RESET | 0 | RESET path 박제 |
| MCT-184 | 0 | P1×2 (F-1~F-4) | REST 신설 wire drift |
| MCT-185 | 0 | 0 | ADR-032 첫 적용 |
| MCT-186 | P0×1 §3.2.4b | 0 | file-delete downstream |
| **MCT-187** | **0** | **P2 ruff (1 iter)** | **code-change-zero** |

전체 6 Story = design FIX 누적 감소 추세 (MCT-182 P0×3 → MCT-187 P0×0). code FIX = ruff lint 1 iter 만 (logic 변경 0). **MCT-188 예측**: D7 quad gate CI = new workflow + pyproject remove = code 신규. Phase 0 verify 충실 시 design FIX 0 지속 가능.

## 4. codeforge upstream ADR escalation 후보 갱신

| 후보 | issue | MCT-187 evidence |
|------|-------|-----------------|
| #795 cross-document SSOT mechanical gate | OPEN | MCT-187 = 수동 §3.6.1 gate v2 (gate v2 reconcile 테이블 6회 누적) |
| #804 박제 PR 자체 완결도 mechanical gate | OPEN | MCT-187 Phase 2 PR2 5 체크리스트 수동 이행 (6회 누적) |
| #805 post-merge audit lane 신설 | OPEN | MCT-187 windows CI pre-existing regression = post-merge audit 유용성 증거 |

**신규 escalation 후보** (MCT-187 발견):
- windows testcontainers CI fix = PR 차단 방지 (`pytest -m "not requires_docker"` 마커 또는 CI workflow 개선) — codeforge #805-2 후보 또는 별 GitHub issue

## 5. Story §12 회고 (4-field schema)

| field | 내용 |
|-------|------|
| 완료 여부 | ✅ COMPLETED (2026-05-17, milestone 6/7) |
| 핵심 lesson | code-change-zero Story = Phase 0 verify 충실 (팩토리 완비 실증) + monkeypatch 불변식 패턴 = 설계/코드 FIX 0 달성. ruff lint = test 파일 초안 자동 생성 시 사전 실행 의무 |
| carry over | (1) engine compose.yml `NAS_MINIO_*` env 제거 별 PR / (2) engine pyproject bithumb dep 제거 MCT-188 owner / (3) windows testcontainers CI fix 별 Story |
| 다음 Story | **MCT-188** (data-free grep0 quad gate + Epic POLICY_FINALIZED, D7+D6) — engine src/ grep0 quad gate CI + pyproject mctrader-data 의존 제거 + ADR-031 POLICY_FINALIZED |

## 6. 다음 Story 진입 권고 (MCT-188)

**MCT-188** (sequential_phase 7, EPIC 마지막) — data-free grep0 quad gate + Epic POLICY_FINALIZED.

진입 prerequisite:
1. MCT-187 Phase 2 PR2 MERGED ✓ (hub#376 7c806ef)
2. carry over 확인: engine compose.yml NAS env (별 PR or MCT-188 scope) + pyproject bithumb dep (MCT-188 D7 quad gate final)

진입 권고:
- **Phase 0 verify 독립**: engine src/ `mctrader_data` import 현황 + pyproject 의존 현황 grep 실측 (D7 quad gate baseline)
- **D7 quad gate CI** = `.github/workflows/data-free-grep0.yml` 신규 (MCT-172 grep0 strict 패턴 재사용)
- **ADR-031 POLICY_FINALIZED** + ADR-029/027/030 amend confirm 전수 박제 의무
- **EPIC-RESULTS 최종 박제** (§Story-7 + milestone 7/7 + ADR 산출물 갱신)
