---
type: pmo-cross-story-audit
epic_key: EPIC-mctrader-docker-stack
epic_status: POLICY_FINALIZED
milestone: "7/7"
audit_date: "2026-05-16"
author: PMOAgent
scope: cross-Story 패턴 분석 + ADR 후보 발의 + gate 준수 audit + 차기 Epic 입력
verified_sources:
  - scope_manifests/EPIC-mctrader-docker-stack.yaml
  - docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md
  - docs/retros/RETRO-MCT-175.md ~ RETRO-MCT-181.md (7건)
---

# PMO Cross-Story 감사 — EPIC-mctrader-docker-stack (POLICY_FINALIZED 7/7)

> PMOAgent cross-Story 횡단 감사 (Epic 완료 trigger, feedback_pmo_retro_mandatory 정합). 단일 Story 회고는 RETRO-MCT-175~181 + EPIC-RESULTS (ArchitectPL 박제) 가 SSOT — 본 문서는 **Story 간 횡단 패턴·트렌드·ADR 후보·gate 준수 audit·차기 Epic 입력** 만 다룬다 (PMO 책임 경계). 전 산출물 origin/main verify 완료 (28671dc).

## 1. Epic 개요 (verified)

| 항목 | 값 |
|------|-----|
| Epic | EPIC-mctrader-docker-stack |
| 상태 | POLICY_FINALIZED 2026-05-15 (milestone 7/7) |
| Story | MCT-175 ~ MCT-181 (7, sequential chain) |
| 결정점 | 19 D (3 pass Codex review) — 19/19 VERIFIED |
| PR | 7 Story × 평균 3~4 PR cross-repo (hub + data + engine + signal-collector) |
| ADR | ADR-030 신규 (MCT-175 publish → MCT-181 POLICY_FINALIZED transition) |
| Epic CLOSED | 별 PR carry (prod-1~4 production evidence 미완) |

## 2. Cross-Story 패턴 분석 (PMO 핵심 책임)

### 패턴 #1 — Phase 0 verify code lane gap **6회 재현** (CRITICAL 트렌드)

Epic 내 가장 강한 횡단 패턴. "설계가 sibling repo runtime 실상을 미검증한 채 박제 → code lane 진입 후 FIX/ESCALATE" 동형 6회:

| # | Story | 가설 (session/plan) | runtime 실상 (Phase 0 verify) | 결과 |
|---|-------|--------------------|------------------------------|------|
| 1 | MCT-170 (선행 Epic) | engine reader 재구현 4 module | io/ MCT-154 LAND 3 module 존재 | scope 재정의 |
| 2 | MCT-177 | data 동기 SIGTERM stub cross-repo 적용 | engine asyncio shutdown.py SSOT 존재 | 신규 daemon 코드 0 line |
| 3 | MCT-178 | signal-collector 5 worker 개별 SET | Publisher 단일 계층 | 첫 진입 repo design fast-fix |
| 4 | MCT-179 | `wal_capacity_bytes` 등 가공 metric | LAND registry 부재 → R2 alert 무력화 | code P1×2 설계 원인 fix |
| 5 | MCT-180 | paper daemon reader_cache producer | PaperRunner ReaderCache 미인스턴스화 | code FIX iter2 설계 원인 |
| 6 | MCT-180 | full-stack compose up CI gate | sibling image 미배포 + build.context 부재 | **FIX 3회 ESCALATE → 재설계** |

**PMO 판정**: 단발 사고 아님 = **구조적 gap**. 동형 = "설계 박제가 sibling repo runtime/실행 환경 제약을 grep 실증 없이 가설로 수용". design lane 은 MCT-179 전수 reconcile 1회 투자로 P0×0 누적 성공 (shift-left 검증) 했으나, **code lane 에는 동급 강제 게이트 부재** → 6회 재현. 비대칭 = 명확한 설계 지침 부재 신호 → **ADR 후보 발의 근거** (§3).

### 패턴 #2 — design lane 전수 reconcile ROI 비대칭 (긍정 패턴, 박제 권고)

| 방식 | 사례 | 결과 |
|------|------|------|
| Story별 **부분** reconcile (자기 D만) | MCT-178 F-001 (D11/D16 swap) + MCT-179 F-001 (D5/D8 swap) | stale 누적 → 4 Story 만에 surface 반복 |
| 1회 **전수** reconcile (D1-D19 SSOT 1:1) | MCT-179 c8e4b8e | MCT-180 P0×0 + MCT-181 P0×0 **연속** → ROI 회수 완결 |

design lane FIX 추이: P0×1(175)→P0×1(176)→P0×0(177)→CONDITIONAL(178)→P0×1(179 전수 reconcile)→**P0×0(180)→P0×0(181)**. 전수 reconcile 1회 비용 → 후속 2 Story 연속 design FIX 0 으로 회수. **차기 Epic 권고**: ADR/scope_manifest SSOT 정합은 Epic 초중반 1회 전수 reconcile 의무화 (Story별 부분 reconcile 금지).

### 패턴 #3 — ESCALATE 안전판 1회 검증 (정상 동작, 트렌드 아님)

MCT-180 D11 = Epic 유일 ESCALATE. flow: CodeReview iter1 FIX → iter2 FIX → iter3 ESCALATE (3/3 max 소진) → ArchitectPL chief judge **설계 원인 최종 판정** → option b resolution (614033a) infra-only 3-layer 재설계 → ESCALATE-fix PASS. **PMO 판정**: ESCALATE 트렌드 아님 (1/7 Story, 정상 발동 1회). FIX 루프 max 소진 시 구현 무한 loop 방지 + 설계 재정의 경로로 안전 전환 = **설계 결함 안전판이 의도대로 작동**한 검증 사례. 축적만 (조치 불요).

### 패턴 #4 — cross-repo metric/contract desync carry-over 전파

MCT-179 hub#340 (`wal_capacity_bytes` 가공 metric → R2 alert 무력화) → MCT-180 engine#55 (reader_cache producer path 가정 오류) **동형 재현**. carry-over chain (선행 Story metric 정의를 후행 Story 가 무비판 승계) 에서 전파. 패턴 #1 의 sub-pattern (metric 계층 특화). 차기 Epic carry-over Story 의 metric/contract 무비판 승계 금지 룰 필요.

### 패턴 #5 — codeforge upstream 구조적 재발 (consumer escalate 후보)

박제 PR(Phase 2 PR2)마다 `phase-gate-mergeable` 가 scope_manifests/** whitelist 누락으로 ACTION_REQUIRED 구조적 재발. MCT-177 발의 (plugin-codeforge#723). hub#332/#335/#338/#341/#344/#347 동일 패턴 6회. **PMO 판정**: consumer workaround 아닌 upstream escalate 정합 (memory feedback_escalate_to_codeforge). #723 미해소 carry — 차기 Epic 입력 registry 박제.

## 3. ADR 후보 발의 (PMO 핵심 책임)

패턴 #1 (Phase 0 verify code lane gap 6회 재현) = "반복 ESCALATE/FIX → 설계 지침 부재" 판정 기준 충족. ADR 후보 1건 발의 (Orchestrator 경유 codeforge ArchitectAgent author 대상 — `pmo_output v1.adr_proposal` inline 반환).

```markdown
---
category: Process / Quality Gate
title: "ADR-NNN: code lane Phase 0 verify 강제 게이트 — cross-repo runtime/metric producer path grep 실증 의무"
trigger: "EPIC-mctrader-docker-stack 7 Story 중 Phase 0 verify code lane gap 6회 재현 (MCT-170/177/178/179/180×2). design lane 은 전수 reconcile shift-left 로 P0×0 누적 성공한 반면 code lane 동급 게이트 부재 = 구조적 비대칭"
---

## 배경
- MCT-170: engine io/ 3 module MCT-154 LAND 존재 미인지 (재구현 가설)
- MCT-177: engine asyncio shutdown.py SSOT 존재 미인지 (data 동기 stub 적용 가설)
- MCT-178: signal-collector Publisher 단일 계층 (5 worker 개별 SET 가설)
- MCT-179: `wal_capacity_bytes` 가공 metric LAND 부재 → R2 CRITICAL alert silent 무력화
- MCT-180: paper daemon ReaderCache 미인스턴스화 (metric producer path 가정 오류)
- MCT-180: full-stack compose up CI 격리 구조적 불가 (sibling image 미배포) → FIX 3회 ESCALATE

## 문제
design lane = ArchitectPL 전수 reconcile (MCT-179 c8e4b8e) 로 shift-left 강제 → MCT-180/181 연속 P0×0.
code lane = 동급 Phase 0 verify 강제 게이트 부재 → cross-repo Story 마다 sibling repo runtime 실상
미검증으로 6회 재현. 설계 지침(언제·무엇을 grep 실증해야 하는가) 부재 = 매 Story 재발명.

## 제안 결정 (옵션)
1. **code lane Phase 0 verify 강제 게이트** — cross-repo Story 의 Phase 1 진입 전, 다음 3종 grep 실증 산출물을
   Story §8/§8.5 에 박제 의무화:
   (a) sibling repo 의 재사용 대상 API/계층 SSOT 존재 grep 결과
   (b) metric/alert producer path 의 실 runtime instantiation 경로 grep 결과
   (c) CI 실행 환경 제약 (sibling image 배포 여부 + build.context 경로 존재) 검증 결과
2. **TestContractArch deputy §8 검수 범위 확장** — §8 Test Contract 검수에 "metric/runtime
   producer path grep 실증" 항목 추가 (DesignReview lane shift-left)
3. **carry-over metric 무비판 승계 금지 룰** — 선행 Story metric 정의를 후행 Story 가
   재사용 시 producer/consumer path 각 repo 독립 재검증 의무 (패턴 #4)

## 예상 결과
- code lane FIX iter 감소 (Epic 누적 code FIX = 178:1 + 179:1 + 180:3+ESCALATE)
- cross-repo Epic 의 가공 metric 박제로 인한 CRITICAL deliverable silent 무력화 차단
- design lane 전수 reconcile 성공 패턴의 code lane 대칭 적용
```

**ADR 후보 발의처**: codeforge plugin 영역 (process/quality gate = 전 consumer 공통). hub repo 자체 ADR 아님. Orchestrator 경유 codeforge-design ArchitectAgent spawn 입력으로 전달 권고. 단 — 본 Epic 은 hub consumer 세션이므로 Orchestrator 가 codeforge upstream escalate (memory feedback_escalate_to_codeforge) 경로로 처리 판단 의무 (PMO 는 발의자, 결정자 아님).

## 4. Gate 준수 audit

### 4.1 FIX 통계 (7 Story × design/code lane)

| Story | design FIX | code FIX | ESCALATE |
|-------|-----------|----------|----------|
| MCT-175 | P0×1 | — (docs Epic entry) | 0 |
| MCT-176 | P0×1 | — (carry fix) | 0 |
| MCT-177 | P0×0 | — | 0 |
| MCT-178 | CONDITIONAL_PASS (fast-fix ba87b3c) | 1 iter | 0 |
| MCT-179 | P0×1 (전수 reconcile c8e4b8e) | 1 iter (metric desync) | 0 |
| MCT-180 | P0×0 (no FIX) | 3 iter | **1 (정상 안전판)** |
| MCT-181 | P0×0 | 0 iter | 0 |

- **design lane trend**: 상승 후 안정화 — 전수 reconcile (179) 변곡점 이후 P0×0 연속 (180/181). 차기 Epic 박제 권고 (패턴 #2).
- **code lane trend**: 178(1)→179(1)→180(3+ESC)→181(0). MCT-180 spike = D11 CI 격리 설계 결함 (패턴 #1 #6) — 단발 아닌 구조적 (ADR 후보 §3).
- **ESCALATE trend**: 1/7 (14%). 정상 안전판 동작 1회 — 트렌드 미형성, 축적만.

### 4.2 게이트 준수 (Preflight / Test Contract / Impl Manifest)

| 항목 | 결과 |
|------|------|
| Preflight 3체크 (레인별) | RETRO §1~§2 전수 박제 확인 — 누락 0 |
| §8 Test Contract ↔ 실제 test 매핑 | MCT-179 20 test / MCT-180 testcontainers 2-layer / MCT-181 9 test — 매핑 박제, 회귀 0 (846/954/969) |
| §8.5 Impl Manifest ↔ git diff | RETRO §1 산출물 단위 박제 ↔ scope_manifest planned_files 정합. N1 scope_files 정정 (MCT-178 F-001 precedent) 5건 — 사전 가설 파일명 실 LAND 정정 (정상 amendment) |
| FIX 원인 evidence pack | MCT-179/180 ArchitectPL 판정 = ADR-030 인용 + Change Plan + test 로그 코멘트 박제 완성 (chief judge 판정 근거 충실) |
| 토큰 예산 초과 | RETRO 미보고 — 임계 접근 이력 없음 |

### 4.3 scope_manifest ↔ RETRO ↔ EPIC-RESULTS 3-way 정합

verify 결과 **정합** — milestone 7/7, 19/19 D VERIFIED, epic_close_gate 7행, epic_closed_prerequisite prod-1~4 + 별(engine) 5건. RETRO-MCT-181 §Epic 종합 + EPIC-RESULTS 19 D 매트릭스 ↔ scope_manifest story_decision_matrix 1:1 일치. discrepancy 0.

## 5. 차기 Epic PMO 입력 registry

| # | 입력 | 유형 | Owner | gate |
|---|------|------|-------|------|
| C-1 | **code lane Phase 0 verify 강제 게이트화** (ADR 후보 §3) | 미해소 carry (process) | codeforge upstream escalate | ADR 채택 → 강제 게이트 LAND |
| C-2 | design lane 전수 reconcile 1회 의무화 (Story별 부분 reconcile 금지) | 긍정 패턴 박제 권고 | 차기 Epic Orchestrator | Epic 초중반 전수 reconcile preflight |
| C-3 | carry-over metric 무비판 승계 금지 룰 (패턴 #4) | 미해소 carry (process) | codeforge upstream escalate | ADR 후보 §3 옵션 3 |
| C-4 | plugin-codeforge#723 (phase-gate-mergeable scope_manifests whitelist) | 미해소 upstream escalate | codeforge maintainer | #723 close |
| C-5 | EPIC-tier-promotion prod-2 ↔ 본 Epic prod-3 (R2 WAL 30G production 측정) | cross-Epic 병행 carry | 별 PR (peak 09:00 KST 1h burst) | 30G 이하 verify or D11 amendment |
| C-6 | 본 Epic prod-1/prod-2/prod-4 (image pin 실적용 + full-stack production smoke + Epic CLOSED 박제) | production evidence carry | 별 PR (production deploy 후) | POLICY_FINALIZED → CLOSED |
| C-7 | engine#55 ci/lookahead-lint mctrader-market-upbit private-dep token | repo-local carry | mctrader-engine repo 별 처리 | engine CI infra 별 (본 Epic 범위 외) |

## 6. 사용자 보고 핵심 3줄

1. **EPIC-mctrader-docker-stack POLICY_FINALIZED 7/7 + 19 D 전수 VERIFIED** — single-host Docker stack 전 mode 운영 가능. design lane 은 MCT-179 전수 reconcile 1회 투자로 MCT-180/181 연속 FIX 0 ROI 회수 (shift-left 성공 완결), MCT-181 = Epic 최초 design+code 양 lane FIX 0 Story.
2. **최강 횡단 패턴 = Phase 0 verify code lane gap 6회 재현 (구조적 비대칭)** — design lane 은 전수 reconcile 게이트로 해소했으나 code lane 동급 강제 게이트 부재. ADR 후보 1건 발의 (code lane Phase 0 verify 강제 게이트 — cross-repo runtime/metric producer path grep 실증 의무, codeforge upstream escalate 대상).
3. **ESCALATE 안전판 1회 정상 검증 + Epic CLOSED 는 별 PR carry** — MCT-180 D11 CI 격리 설계 결함이 FIX 3회 소진 후 ArchitectPL chief judge → 설계 재정의로 안전 해소 (구현 무한 loop 방지 검증). production evidence (prod-1~4: image pin 실적용 + WAL 30G production 측정 + full-stack production smoke + Epic CLOSED 박제) 미완 → POLICY_FINALIZED 유지, CLOSED 는 production deploy 후 별 PR (EPIC-tier-promotion prod-2 cross-Epic 병행).

## 7. Cross-ref

- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (POLICY_FINALIZED 7/7)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (ArchitectPL 박제 SSOT)
- Story RETRO: `docs/retros/RETRO-MCT-175.md` ~ `RETRO-MCT-181.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (POLICY_FINALIZED transition)
- 선행 Epic (cross-Epic prod-2 병행): `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- codeforge upstream: plugin-codeforge#723 (phase-gate-mergeable scope_manifests whitelist)
