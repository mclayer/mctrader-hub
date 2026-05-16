---
type: pmo-patterns-analysis
session_date: "2026-05-17"
trigger: "MCT-184 박제 amendment LAND (hub PR #360, fa7ea64, 2026-05-16T15:19:39Z) post-completion 회고 — hub#359 박제 PR (4924b16, MERGED 2026-05-16T14:51:30Z) 자체가 박제 작업의 약 절반만 처리 = cross-document SSOT drift 3호 신규 발견. MCT-189 PMO-PATTERNS (1호 operational + 2호 design) 동형 확장."
author: PMOAgent
scope: |
  Cross-Story patterns analysis (MCT-184 post-LAND completion 산출물 + MCT-189 PMO-PATTERNS 후속).
  단일 Story 회고 (RETRO-MCT-184) 는 self-write SSOT — 본 문서는 PMOAgent 횡단 감사 영역만 다룬다:
  (1) SSOT drift 3호 (박제 PR 자체 incomplete 패턴) 정식 박제
  (2) MCT-189 1호+2호 와 cross-ref 일반화 (3 호 cross-Story 누적)
  (3) codeforge upstream ADR escalation 후보 2 + 후보 3 정식 발의 근거
  (4) escalate-and-fix standard path 정합 처리
  (5) carry over registry (PMO 측 trace)
verified_sources:
  - "docs/retros/RETRO-MCT-184.md (self-write SSOT, §4.1 6회 누적 표 + §4.2 SSOT drift 3호 표 + §4.3 forcing function 후보)"
  - "docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md (§Story-3 신규 + milestone 3/7)"
  - "docs/stories/MCT-184.md (frontmatter status=COMPLETED + §8.5.1 hub#359 정정 + §10 FIX Ledger iter1 post-merge + §11 행 4 박제 amendment PR)"
  - "git log: fa7ea64 (MCT-184 박제 amendment, PR #360, 2026-05-16T15:19:39Z) + 4924b16 (MCT-184 hub#359 부분 박제, 2026-05-16T14:51:30Z) + 45e501c5 (data#72, 2026-05-16T14:45:38Z) + 1e96b47 (hub#358 Phase 1, 2026-05-16T14:09:50Z)"
  - "docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md (MCT-189 1호+2호 자매 retro — 본 retro 의 직접 precedent)"
  - "docs/retros/PMO-AUDIT-MCT-183.md §4.4 cross-Epic governance 발견 + §4.2 ADR draft (cross-document SSOT mechanical gate, Option B 권고)"
  - "plugin-codeforge#795 (OPEN, phase:설계-리뷰) — 본 retro 와 연관 cross-document SSOT mechanical gate ADR escalation 진행 중 (mctrader consumer 5회 누적 evidence 기반)"
  - "plugin-codeforge#563 (OPEN, phase:요구사항) — sibling open Story 자동 검색 forcing function (PMO retro carrier 측면 — 본 retro 가 직접 carrier)"
related_patterns:
  - "MCT-179: ADR-030 Out-of-scope D1-D19 swap stale → cross-document SSOT 1번째 사례"
  - "MCT-182: PMOAgent Story 완료 감사 박제 (PMO-AUDIT-MCT-182 §4 forcing function 후보 일반화)"
  - "MCT-183: iter1+iter2+iter3 3회 추가 + §3.6.1 gate v1 자체 결함 → PMO-AUDIT-MCT-183 §4 codeforge upstream ADR escalation 결정 발의 (Option B)"
  - "MCT-189 (RESERVED): ADR-029 §D3=C wiring 0건 drift + mctrader-data:pilot image 2일 가동 — PMO-PATTERNS-2026-05-16 (1호+2호)"
  - "본 retro: MCT-184 박제 PR 자체 incomplete (3호)"
---

# PMO Patterns Analysis — Cross-Document SSOT Drift 3호 (박제 PR 자체 incomplete 패턴, 2026-05-17 MCT-184 post-completion)

> PMOAgent cross-Story patterns analysis. MCT-184 박제 amendment LAND (hub PR #360, fa7ea64,
> 2026-05-16T15:19:39Z) 의 사후 회고에서 발견된 **박제 PR 자체 incomplete 패턴** — 박제 PR title
> 이 "Phase 2 PR2 박제" 임에도 박제 작업의 약 절반만 처리되어 별 amendment PR 로 보강. MCT-189
> PMO-PATTERNS (1호 operational + 2호 design SSOT) 자매 retro 의 **3호 cross-Story 확장**.

## 1. 트리거 + 직접 발견 evidence

### 1.1 사후 회고 trigger

`Orchestrator (Claude Opus) → PMOAgent` 본 retro spawn. 입력:
- hub#359 (4924b16, 2026-05-16T14:51:30Z, "docs(MCT-184): §8.5 Impl Manifest + Phase 2 PR2 박제 — data#72 LAND + ADR-031 §D3 LAND confirm (milestone 3/7)") 가 박제 PR title 임에도 박제 작업 약 절반만 처리
- 본 PMO retro 시점 (2026-05-17) 에 hub PR #360 (fa7ea64) 로 박제 amendment LAND 완료 → 사후 회고 spawn

### 1.2 hub#359 가 처리한 것 vs 처리하지 못한 것

| 박제 산출물 | hub#359 처리 | hub#360 amendment (post-LAND completion) |
|------------|-------------|-------------------------------------|
| Story §8.5 Impl Manifest 작성 | ✅ 처리 | — |
| ADR-031 §D3 amendment box LAND confirm | ✅ 처리 | — |
| scope_manifest milestone 3/7 | ✅ 처리 | — |
| CLAUDE.md MCT-184 RESERVED→COMPLETED 전환 | ✅ 처리 (line 560 hub#TBD 잔존 except) | — |
| **RETRO-MCT-184.md 신규 생성** | ❌ 미처리 | ✅ amendment PR 처리 |
| **EPIC-RESULTS §Story-3 (MCT-184) 신규 작성** | ❌ 미처리 | ✅ amendment PR 처리 |
| **EPIC-RESULTS milestone 2/7 → 3/7 갱신** | ❌ 미처리 | ✅ amendment PR 처리 |
| **EPIC-RESULTS Row 3 RESERVED → COMPLETED 전환** | ❌ 미처리 | ✅ amendment PR 처리 |
| **EPIC-RESULTS D3 status reserved → partial VERIFIED 2026-05-16** | ❌ 미처리 | ✅ amendment PR 처리 |
| **Story frontmatter status: phase:구현 → COMPLETED 전환** | ❌ 미처리 | ✅ amendment PR 처리 |
| **Story frontmatter completed_at 입력** | ❌ 미처리 | ✅ amendment PR 처리 |
| **F-3 hub#TBD 잔존 정정** (Story §11 + §8.5.1 + CLAUDE.md line 560) | ❌ 미처리 (잔존) | ✅ amendment PR 처리 |
| **§10 FIX Ledger post-merge fix iter 1 박제** (F-1~F-4 Codex post-LAND audit 결과) | ❌ 미처리 | ✅ amendment PR 처리 |

**드러난 결손**: hub#359 박제 PR title 이 "Phase 2 PR2 박제" + "milestone 3/7" 이지만 실제 처리된 박제 산출물은 약 5/12 = 42%. 나머지 약 58% 는 별 amendment PR (hub#360) 로 carry.

### 1.3 PR title SSOT ≠ 박제 산출물 SSOT 의 결정적 evidence

- hub#359 PR title: `docs(MCT-184): §8.5 Impl Manifest + Phase 2 PR2 박제 — data#72 LAND + ADR-031 §D3 LAND confirm (milestone 3/7)`
- hub#359 LAND 시점 (4924b16, 2026-05-16T14:51:30Z): RETRO-MCT-184.md = file 부재 / EPIC-RESULTS = milestone 2/7 + §Story-3 행 RESERVED / Story frontmatter `status: phase:구현` 잔존
- hub#360 PR title (fa7ea64, 2026-05-16T15:19:39Z, 약 28분 후): `docs(MCT-184): 박제 amendment — RETRO + EPIC-RESULTS §Story-3 + frontmatter status + F-3 정정 (post-LAND completion)`

→ **hub#359 의 PR title 이 박제 작업의 SSOT 가 아니었다**. PR title 자체가 "박제 완결"을 주장했으나 실 산출물 carry-over 가 약 58%.

## 2. SSOT drift 3호 정식 박제

### 2.1 cross-Story 3호 누적 (MCT-189 PMO-PATTERNS 동형 확장)

MCT-189 RESERVED 시점 (2026-05-16) 의 운영 진단 세션에서 발견된 cross-document SSOT drift 2건 (PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md) 의 본 retro 3호 확장:

| 호 | 트리거 | drift 영역 | SSOT type A | SSOT type B | resolution |
|----|--------|-----------|------------|------------|-----------|
| **1호** (MCT-189) | 2026-05-16 운영 진단 — `trader@mclayer.it` 디스크 압박 보고 → systematic-debugging Phase 1~3 | `mctrader-data:pilot` image **created 2026-05-13T15:51:28Z** (pkg 0.9.0, MCT-167 이전) 가 production 7 컨테이너에서 2026-05-13 ~ 2026-05-16 (2일+) 가동 — EPIC-tier-promotion-single-source POLICY_FINALIZED (2026-05-14) + EPIC-mctrader-docker-stack POLICY_FINALIZED (2026-05-15) 양쪽 정책 적용 무의 image | **policy LAND date** (Story §11 박제 SSOT) | **operational evidence** (production image inspect — 실 컨테이너 가동 image 의 build timestamp) | 본 세션 응급 재배포 (f233952 단일소스 빌드 + backfill stop + capacity_probe/ingest_blocker LAND) |
| **2호** (MCT-189) | 2026-05-16 동일 세션 — ADR-029 §D3=C "Local delete = NAS HEAD verify + grace 0" 박제 vs `promote_l1()` production caller 0건 grep evidence | ADR-029 §D3=C "VERIFIED" 박제 + MCT-169 §11 VERIFIED + EPIC-tier-promotion-single-source POLICY_FINALIZED 박제 — 그러나 `git grep -nE "promote_l1\(|from mctrader_data\.compactor\.promotion import" -- 'src/**'` = 0건 | **design SSOT (VERIFIED badge)** (ADR + Story §11 + EPIC-RESULTS 박제) | **code SSOT (caller grep ≥1)** (production runtime 실 호출 site grep evidence) | MCT-189 RESERVED — wiring 완결 + ADR-029 §D3 amendment box 박제 + ADR-032 발의 (evidence triad 의무화) |
| **3호** (본 retro, MCT-184) | 2026-05-17 MCT-184 박제 amendment LAND 사후 회고 (hub PR #360, fa7ea64) | hub#359 (4924b16, 2026-05-16T14:51:30Z) 박제 PR title "Phase 2 PR2 박제 — data#72 LAND + ADR-031 §D3 LAND confirm (milestone 3/7)" 가 MERGED — 그러나 RETRO 미생성 + EPIC-RESULTS §Story-3 미작성 + milestone 2/7→3/7 미반영 + Story frontmatter status 미전환 + F-3 hub#TBD 잔존 (≈58% carry) | **PR title SSOT** (commit message + label + PR description) | **박제 산출물 완결도 SSOT** (의무 산출물 체크리스트 — RETRO 존재 + EPIC-RESULTS §Story-N 갱신 + Story frontmatter status=COMPLETED + completed_at + CLAUDE.md "hub#TBD" 잔존 0줄 + ADR amendment confirm) | hub PR #360 (fa7ea64, 2026-05-16T15:19:39Z, 약 28분 후) amendment LAND — RETRO + EPIC-RESULTS + Story frontmatter + F-3 hub#TBD→hub#359 정정 |

### 2.2 3호 모두 동일 root cause

**"박제된 사실 (badge SSOT) ↔ 실 상태 (operational / code / artifact completeness SSOT) 사이의 forcing function 부재"** 의 동일 root cause 3 layer:

| layer | 1호 (operational) | 2호 (design vs code) | 3호 (PR title vs artifact completeness) |
|-------|------------------|--------------------|--------------------------------------|
| 박제 SSOT (badge) | Story §11 LAND timeline + ADR Status: POLICY_FINALIZED | ADR D-row VERIFIED + Story §11 VERIFIED | PR title + PR description ("Phase 2 PR2 박제") |
| 실 SSOT (forcing function 부재 영역) | production deploy image 의 build timestamp / commit base | production code 의 caller grep ≥1 | 박제 의무 산출물 체크리스트 (RETRO + EPIC-RESULTS §Story-N + Story frontmatter status + CLAUDE.md hub#TBD 잔존 0) |
| 결과 | 정책 LAND 후 2일+ 적용 무의 production runtime | 정책 LAND 후 wiring 부재 — 130GB legacy parquet 누적 | 박제 PR MERGED 후 별 amendment PR 의무 (carry-over ≈58%) |
| 해소 PR | (operational) f233952 base 재빌드 + force-recreate | (별 Story) MCT-189 wiring 완결 + ADR-032 발의 | (별 amendment PR) hub PR #360 박제 보강 |

→ **3 layer 의 forcing function 부재가 동일 root cause** — cross-document SSOT pattern 의 일반화 룰 발의 의무.

## 3. codeforge upstream ADR escalation 후보 2 + 후보 3 정식 발의

### 3.1 후보 1 (MCT-183 PMO-AUDIT 에서 발의된 1차 ADR escalation, 본 retro 와 직접 자매)

`plugin-codeforge#795` OPEN (phase:설계-리뷰, P0 priority, mctrader consumer 5회 누적 evidence) — cross-document SSOT mechanical reconcile gate (design lane plugin-level forcing function). 본 retro 의 3호 발견이 **#795 의 추가 evidence row** — drift layer 가 design lane (Story-내 박제 desync) 뿐 아니라 **박제 PR 자체 incomplete (Story 외 박제 lane desync)** 까지 확장됨을 실증. #795 ADR draft 의 **"§3 enforcement layer"** 범위 확장 의견 첨부 권고:

```markdown
## §3 enforcement layer (확장 — MCT-184 PMO 발견 3호 carrier)

기존 §3 = scope_manifest + Story §11 박제 + design lane gate. 본 retro 가 발견한 3호 (박제 PR
자체 incomplete) 는 design lane 의 영역 밖 — **박제 lane 의 의무 산출물 검증** 까지 확장 필요:

- 박제 PR title 에 다음 token 중 하나 이상 포함 시 (= 박제 lane PR 식별):
  - "Phase 2 PR2"
  - "박제"
  - "milestone N/M"
  - "COMPLETED"

- 의무 산출물 체크리스트 grep gate (CI):
  - `RETRO-<STORY_KEY>.md` 존재 (file exists)
  - `EPIC-RESULTS-<EPIC_KEY>.md` 내 `§Story-N` section 존재 + milestone N/M 정합
  - Story file frontmatter: `status: COMPLETED` (or `status: phase:박제-amendment`) + `completed_at: YYYY-MM-DD` 미공란
  - CLAUDE.md / Story file `hub#TBD` 잔존 0줄 (grep)
  - ADR amendment box LAND confirm 박제 (관련 ADR 의 amendment marker 존재)

- 위 5 항목 중 하나라도 결손 시 박제 PR merge 차단 (gate:archive-complete label 부재)
```

### 3.2 후보 2 신규 발의 — 박제 PR 자체 완결도 mechanical gate

**`plugin-codeforge#NEW-A` 발의 권고** (또는 #795 의 amendment 형태 통합):

```markdown
---
category: Process / Quality Gate / Archive Lane Forcing Function
title: "박제 PR 자체 완결도 mechanical gate — PR title SSOT ≠ 박제 산출물 SSOT (MCT-184 3호 누적 실증)"
trigger: |
  MCT-189 PMO-PATTERNS (2026-05-16) operational SSOT drift 1호 + design SSOT drift 2호 + 본
  retro (2026-05-17) PR title vs artifact completeness SSOT drift 3호 = cross-Story 3 layer
  동일 root cause 누적. MCT-183 PMO-AUDIT §4 (cross-document SSOT mechanical gate, plugin-
  codeforge#795 OPEN) 의 enforcement layer 확장 — design lane 범위 외 박제 lane 영역 까지
  forcing function 의무.
---

## 배경

박제 lane (Phase 2 PR2 박제 또는 후속 amendment PR) 이 PR title 에 "Phase 2 PR2 박제" /
"milestone N/M" / "COMPLETED" 명시함에도 실 박제 산출물 carry-over 가 약 58% 발생 (MCT-184
hub#359 사례). 결과: 별 amendment PR (hub#360) 의무 → 박제 SSOT divergence 28분 동안 존재.

### 사례 (verified):

- **MCT-184 hub#359 (4924b16, 2026-05-16T14:51:30Z)**: PR title "Phase 2 PR2 박제 — data#72
  LAND + ADR-031 §D3 LAND confirm (milestone 3/7)" 가 MERGED. 그러나:
  - RETRO-MCT-184.md = 미생성
  - EPIC-RESULTS-EPIC-data-domain-decoupling.md §Story-3 = 미작성 + milestone 2/7 잔존
  - docs/stories/MCT-184.md frontmatter `status: phase:구현` 잔존 + `completed_at: ~` 미입력
  - CLAUDE.md line 560 `hub#TBD` 잔존 (실 LAND hub#359 미정정)
  - Story §10 FIX Ledger Codex post-LAND audit 결과 미박제 (F-1~F-4)

- 별 amendment PR (hub#360, fa7ea64, 2026-05-16T15:19:39Z, 약 28분 후) LAND 로 carry 해소

## 문제

박제 PR 자체 완결도 검증 부재 — PR title 만으로는 박제 산출물 의무 카운트 보장 불가. self-
detection 한계 (작성자가 산출물 카운트 누락 인지 시점이 별 amendment PR 작성 시점) →
하루 + 28분 박제 SSOT divergence window 발생.

## 제안 결정

**박제 PR auto-classification + 의무 산출물 grep gate (CI)**:

1. **박제 PR 자동 분류** — PR title 정규식:
   - `(Phase 2 PR2|박제|milestone \d+/\d+|COMPLETED|post-LAND completion)` 매칭 시 `lane:archive` label 자동 부착
   - merge 전 CI step 추가 (archive-completeness-gate.yml)

2. **의무 산출물 grep gate** (5 체크):
   - **C1**: `docs/retros/RETRO-<STORY_KEY>.md` 존재
   - **C2**: `docs/retros/EPIC-RESULTS-<EPIC_KEY>.md` 내 `^## §Story-N \(<STORY_KEY>\)` section 존재 + milestone `\*\*N/M\*\*` 정합
   - **C3**: `docs/stories/<STORY_KEY>.md` frontmatter `status: COMPLETED` OR `status: phase:박제-amendment` + `completed_at: \d{4}-\d{2}-\d{2}` 미공란
   - **C4**: `git grep -n "hub#TBD" -- docs/stories/<STORY_KEY>.md CLAUDE.md` = 0건 (실 LAND PR# 박제 완결)
   - **C5**: 관련 ADR amendment box LAND confirm 박제 — `git grep "Status Amendment box (<STORY_KEY>" -- docs/adr/` ≥ 1건 (해당 ADR 존재 시)

3. **gate 결과**:
   - 5 체크 전수 PASS → `gate:archive-complete` label 부착 + merge 가능
   - 1+ FAIL → CI red + merge 차단 + 결손 항목 PR comment 자동 출력

4. **exemption** — 박제 PR 이 사전에 "split into N PRs" 명시 박제 시 (PR description 에
   `Archive splits: 1/N`, `Archive splits: 2/N`) gate scope 분할 적용 가능

## 예상 결과

- 박제 PR title ↔ 산출물 carry-over divergence window **0** (28분+ → 0)
- self-detection 한계 해소 — CI 가 누락 자동 감지
- amendment PR 발생 빈도 감소 (carry over 인지 시점 = PR 작성 시점 → merge 시점)
- cross-Story SSOT drift 3호 패턴 근본 차단

## Out of scope

- Story-내 박제 desync (별 ADR — plugin-codeforge#795 cross-document SSOT mechanical gate)
- design lane gate (별 ADR — 동일)
- VERIFIED badge evidence triad (별 ADR — ADR-032 PMO 발의, 2호 carrier)
```

### 3.3 후보 3 신규 발의 — post-merge audit lane 의무 박제 검증화

**`plugin-codeforge#NEW-B` 발의 권고**:

```markdown
---
category: Process / Quality Gate / Post-Merge Audit Lane
title: "post-merge audit lane 신설 — Codex post-LAND audit 가 발견하는 production correctness + bytes-level 정밀도 영역의 박제 lane 의무 검증화 (MCT-182 + MCT-183 + MCT-184 3회 누적 실증)"
trigger: |
  MCT-182 cold path data#69 fix1 + MCT-183 data 6450cfd lint-revert + MCT-184 F-1/F-2/F-3/F-4
  (Codex post-LAND audit 발견 P0×3 + P1×1) = **3회 연속 동일 lesson**. pre-LAND lane (요구사항/
  설계/설계-리뷰/구현/구현-리뷰) 가 cover 하지 못하는 영역 — production correctness (invalid
  ts_utc silent substitute + canonical_sha256 dead code) + bytes-level 정밀도 (arrow_ipc
  round-trip table 동등만, bytes-level X) — 가 Codex post-LAND audit 만이 발견 가능 영역으로
  실증. cross-document SSOT mechanical gate (#795) 영역과 별 (gate v2 는 SSOT 정합 영역).
---

## 배경

Codex (mctrader consumer 측 superpower) post-LAND audit 가 발견하는 영역:

| audit 영역 | gate v2 cover? | Codex post-LAND cover? | 발견 사례 |
|-----------|--------------|---------------------|---------|
| cross-document SSOT 정합 (Story/ADR/scope_manifest/Change Plan canonical) | ✅ (gate v2 post-LAND repo-wide grep) | (cross-check) | MCT-179/182/183 5회 누적 → gate v2 영구 박제 |
| production correctness (silent data corruption / silent data-loss) | ❌ | ✅ | MCT-184 F-1 (invalid ts_utc → `datetime.now()` silent substitute) + F-2 (canonical_sha256 dead code, INV-3 mismatch) |
| bytes-level 정밀도 (round-trip 등) | ❌ | ✅ | MCT-184 F-4 (arrow_ipc table 동등만, bytes-level X) |
| dead code (lint-revert 류) | ❌ (lint pass 시점) | ✅ (semantic 검토) | MCT-183 data 6450cfd lint-revert + MCT-182 data#69 fix1 cold path |

**3회 누적 (MCT-182/183/184)**: Codex post-LAND audit 가 production correctness + bytes-level
정밀도 영역의 sentry 역할 — 단 **현재 ad-hoc 운용** (Story 별 사용자가 명시적으로 Codex review
명령). 박제 lane 의무 lane 화 부재 → self-discipline 한계 (3회 모두 사용자 explicit trigger).

## 문제

1. **self-discipline 한계**: Codex post-LAND audit 의 운용이 ad-hoc → Story 별 사용자가 명시적
   trigger 시에만 발견. 의무 lane 부재 → 다음 Story 누락 위험.

2. **pre-LAND lane 영역 외**: production correctness + bytes-level 정밀도는 pre-LAND lane
   (설계 + 구현 + 구현-리뷰) 이 cover 하지 못함 — 설계 lane 은 정책 박제, 구현-리뷰 lane 은
   AC 검증 + lint/typing/test 중심. semantic boundary (silent substitute / dead code) 는
   별 audit 영역.

3. **gate v2 영역 외**: cross-document SSOT mechanical gate (gate v2 post-LAND repo-wide
   grep) 는 SSOT 정합 영역만 cover — production correctness 부분 외.

## 제안 결정

**post-merge audit lane 신설 (`lane:post-merge-audit`)** — codeforge plugin lane 추가:

1. **trigger**: 박제 PR (lane:archive) MERGED 직후 자동 spawn (`post-merge-audit.yml`
   workflow)

2. **검증 axis (Codex sentry 자동 실행)**:
   - **axis-1 (production correctness)**: silent substitute / silent data-loss / dead code
     검출 (semantic boundary review — invalid input → fallback substitute 패턴 grep)
   - **axis-2 (bytes-level 정밀도)**: round-trip / serialize-deserialize / encoding
     boundary 검토 (table 동등만 ≠ bytes 동등 차이)
   - **axis-3 (cross-document SSOT 정합 재검증)**: gate v2 post-LAND repo-wide grep 0줄
     evidence 재검증 (cross-check)
   - **axis-4 (security boundary)**: T1 path traversal / T2 DoS bound / T3 auth + auth-z
     재검증

3. **결과 처리**:
   - finding 0 → `gate:post-merge-audit-pass` label 부착 + Story COMPLETED 전환 가능
   - finding P0 / P1 → `lane:post-merge-fix` PR 자동 carry over (post-merge fix PR template
     생성)

4. **non-blocking 정책**: post-merge audit 는 박제 PR merge 를 차단하지 않음 (별 amendment
   PR 로 carry — 박제 SSOT 정합성 유지). dead-in-data Story 의 경우 cutover Story 진입
   prerequisite gate 화 (예: MCT-184 F-1/F-2/F-4 → MCT-185 cutover 진입 prerequisite).

## 예상 결과

- production correctness + bytes-level 정밀도 영역 sentry 의무 lane 화 (ad-hoc 한계 해소)
- MCT-184 류 F-1/F-2/F-4 post-merge fix carry 의 의무 발의 lane (Story owner 의 self-
  discipline 의존 없음)
- cutover Story 진입 prerequisite gate forcing function 강화 (dead-in-data → live 전환 시점
  silent corruption 차단)

## Out of scope

- gate v2 영역 (cross-document SSOT mechanical gate, plugin-codeforge#795)
- 박제 PR 자체 완결도 gate (post 후보 2, plugin-codeforge#NEW-A)
- pre-LAND lane 확장 (별 Story)
```

## 4. escalate-and-fix standard path 정합 처리

memory: `feedback_escalate_to_codeforge` (codeforge 사용 의무, consumer workaround 금지, upstream
issue escalation) + `feedback_cross_plugin_drift_detection` (escalate-and-fix standard path) 정합:

| 단계 | 처리 | 결과 |
|------|------|------|
| **(a) PMO retro 박제** | `docs/retros/PMO-PATTERNS-2026-05-17-ssot-drift-3-archive-pr-incomplete.md` 신규 (본 file) — SSOT drift 3호 정식 박제 + 후보 2 + 후보 3 ADR draft 박제 | 본 retro |
| **(b) codeforge marketplace issue 작성** | `plugin-codeforge` repo 에 후보 2 + 후보 3 신규 issue 발의 (2 issue 또는 1 통합 issue) — `codeforge-improvement` + `priority:high` + `from-mctrader-debut` label | 별 step (§5) |
| **(c) plugin-codeforge#795 cross-ref** | 본 retro 의 3호 발견을 #795 의 추가 evidence row 로 first comment 추가 — design lane 영역 외 박제 lane 확장 의견 첨부 | 별 step (§5) |
| **(d) `pmo_output v1.adr_proposal` inline 반환** | Orchestrator 경유 codeforge plugin ArchitectAgent author 후보 — 본 §3.2 + §3.3 ADR draft content 입력 | 본 retro §3.2 + §3.3 |
| **(e) mctrader-hub 측 self-discipline 유지** | mechanical gate 가용 전 까지 mctrader-hub Story owner 가 박제 산출물 5 체크리스트 self-discipline 의무 (Story §11 박제 시 RETRO + EPIC-RESULTS + frontmatter + hub#TBD grep + ADR amendment 5 항목 전수 LAND 검증) | MCT-185~188 owner reapply 의무 |

## 5. carry over registry (PMO 측 trace)

| # | 항목 | severity | owner | timing |
|---|------|----------|-------|--------|
| C1 | **codeforge marketplace issue 발의** — 후보 2 (박제 PR 완결도 mechanical gate) + 후보 3 (post-merge audit lane) 2 issue 또는 1 통합 issue | **HIGH 누적 3 사례** | PMOAgent (별 step) | 본 retro LAND 직후 |
| C2 | **plugin-codeforge#795 first comment 추가** — 3호 evidence row 첨부 + design lane 영역 외 박제 lane 확장 의견 | **HIGH** | PMOAgent (별 step) | 본 retro LAND 직후 |
| C3 | **mctrader-hub self-discipline 5 체크리스트 명문화** — MCT-185~188 owner reapply 의무 (Story §0 R1 가드 항목에 추가) | process | MCT-185~188 owner | 각 Story 진입 시 |
| C4 | **`feedback_pmo_retro_mandatory.md` memory 보강** — Story 박제 PR 자체 incomplete 패턴 감지 + amendment PR 발생 시 PMO retro 의무 spawn 룰 추가 | process | (사용자 결정) | 별 step |
| C5 | **F-1/F-2/F-4 data측 post-merge fix PR LAND** — MCT-185 cutover 진입 prerequisite (silent data corruption + INV-3 mismatch + bytes-level 정밀도 차단 의무) | **P0×2 + P1×1** | data 측 post-merge fix PR (#795 unblock 후 진입) | MCT-185 진입 전 |

## 6. Epic milestone audit + 다음 Story 진입 권고

### 6.1 EPIC-data-domain-decoupling milestone 3/7 박제 정합 검증

| 항목 | 박제 SSOT | 실 상태 | 정합 |
|------|----------|--------|------|
| EPIC-RESULTS milestone 표기 | **3/7** (Status section + Row 3 COMPLETED 2026-05-16) | hub PR #360 LAND 후 ✅ | ✅ |
| Row 3 MCT-184 상태 | COMPLETED 2026-05-16 (post-merge fix 4건 carry — F-1/F-2/F-4 data측 + F-3 hub측 amendment) | ✅ | ✅ |
| §Story-3 (MCT-184) section 존재 | ✅ (159 lines, F-1~F-4 박제 + dead-in-data pattern + 박제 PR incomplete 발견 SSOT drift 3호 + ADR-032 evidence triad) | ✅ | ✅ |
| D3 status | partial VERIFIED 2026-05-16 (MCT-184 historical+reverse-write LAND, realtime stream + cold-read cutover pending MCT-185, F-1/F-2/F-4 post-merge fix carry) | ✅ | ✅ |
| Row 4 MCT-185 prerequisite | F-1/F-2/F-4 data측 post-merge fix PR LAND 의무 (#795 unblock 후) | RESERVED | ✅ |

→ Epic milestone audit **전수 PASS**. Row 3 박제 정합. 3/7 milestone 정확.

### 6.2 다음 Story (MCT-185) 진입 권고

**MCT-185** (sequential_phase 4) — Layer 2 data realtime stream (Redis Stream 정규화 publisher) +
engine thin client (`data_client/` 신규, OpenAPI generated) + cold-read 실 호출부 cutover.

**진입 prerequisite**:

| # | 항목 | 상태 |
|---|------|------|
| 1 | MCT-184 박제 amendment LAND (hub PR #360 fa7ea64) | ✅ 충족 (2026-05-16T15:19:39Z) |
| 2 | **F-1/F-2/F-4 data측 post-merge fix PR LAND** (silent data corruption + INV-3 mismatch + bytes-level 정밀도 차단) | **CARRY** — #795 unblock 후 별 세션 진입 |
| 3 | F-3 hub측 (Story §11 + §8.5.1 + CLAUDE.md hub#TBD → hub#359 정정) | ✅ 충족 (hub PR #360 LAND) |
| 4 | ADR-031 §D3 partial VERIFIED 박제 | ✅ 충족 |
| 5 | EPIC-RESULTS milestone 3/7 + §Story-3 박제 | ✅ 충족 (hub PR #360 LAND) |
| 6 | 본 PMO retro 박제 (PMO-PATTERNS-2026-05-17 + 후보 2 + 후보 3 ADR draft) | (본 작업 산출물) |

**MCT-185 진입 권고 — reapply 8 항목** (MCT-184 lesson 누적 + 본 retro 신규 2 항목):

| # | 항목 | 출처 | 본 Story 강조 |
|---|------|------|--------------|
| 1 | R1 가드 + §0 Phase 0 Verify Gate (V-체크) | MCT-182~184 lesson | engine `data_client/` 신규 namespace 0 가설 HEAD 재검증 + Redis Stream publisher 신규 의존 영향 |
| 2 | D-row 1:1 reconcile (scope_manifest D2/D3 ↔ ADR-031 amendment ↔ Change Plan) | MCT-179 lesson | D2 cold-read cutover (실 amend confirm) + D3 realtime stream (partial VERIFIED → VERIFIED 진전) |
| 3 | cross-document SSOT forcing function self-discipline (mechanical gate 미가용) | MCT-183 PMO §4.3 | §3.6.1 gate v2 cross-Story reapply (glob-scope + 변형포괄 + self-verify TEST1/TEST2) — plugin-codeforge#795 OPEN 동안 |
| 4 | Phase 0 lazy/conditional import grep | MCT-183 8-C | top-level grep + lazy/conditional import grep 의무 |
| 5 | Codex pre-LAND audit 명시적 운용 | MCT-182~184 lesson (3회 연속 효과) | data realtime stream + engine data_client/ 신규 시 4 axis Codex review 의무 |
| 6 | MCT-189 wiring drift 동형 차단 (ADR-032 evidence triad 선제 reapply) | MCT-184 AC-6 패턴 | dead-in-data → live cutover 전환 시 production caller grep evidence triad 갱신 (test/runtime/code 3종) |
| 7 | **박제 PR 자체 완결도 self-discipline** (mechanical gate #NEW-A 가용 전) | **본 retro 신규** | 박제 PR LAND 전 5 체크리스트 (RETRO 존재 + EPIC-RESULTS §Story-N + frontmatter status + hub#TBD grep + ADR amendment) self-discipline |
| 8 | **post-merge audit lane self-discipline** (mechanical lane #NEW-B 가용 전) | **본 retro 신규** | LAND 후 Codex post-LAND audit 4 axis (production correctness + bytes-level 정밀도 + SSOT 재검증 + security) 의무 운용 |

## 7. 종합 판정

| 항목 | 결과 |
|------|------|
| SSOT drift 3호 정식 박제 | ✅ **본 retro** (MCT-189 PMO-PATTERNS 1호+2호 자매 retro 동형 확장) |
| codeforge upstream ADR escalation 후보 발의 | ✅ **후보 1 (#795 cross-ref) + 후보 2 신규 + 후보 3 신규** = 3 routes |
| escalate-and-fix standard path 정합 | ✅ (a) PMO retro 박제 + (b) marketplace issue 발의 + (c) #795 first comment + (d) ADR draft inline + (e) self-discipline 유지 |
| Epic milestone audit | ✅ EPIC-data-domain-decoupling 3/7 전수 PASS |
| 다음 Story (MCT-185) 진입 권고 | ✅ reapply 8 항목 (MCT-182~184 lesson 6 + 본 retro 신규 2) + F-1/F-2/F-4 data 측 post-merge fix PR LAND prerequisite carry |

**PMO 결론**:

MCT-184 = **박제 PR 자체 incomplete 패턴 발견의 모범 retro** — MCT-189 PMO-PATTERNS (1호 operational +
2호 design vs code) 의 자매 retro 3호 확장 + codeforge upstream ADR escalation 후보 2 + 후보 3
신규 발의 + #795 cross-ref evidence row 첨부.

**핵심 lesson**: PR title SSOT ≠ 박제 산출물 SSOT. PR MERGED ≠ 박제 완결. 박제 산출물 의무
체크리스트 (RETRO + EPIC-RESULTS §Story-N + Story frontmatter status + CLAUDE.md hub#TBD 잔존
0줄 + ADR amendment confirm) 의 전수 LAND 가 완결 의무.

**일반화**: cross-document SSOT forcing function pattern 의 3 layer 모두 동일 root cause (badge
SSOT ↔ 실 SSOT 사이 forcing function 부재) — codeforge upstream ADR escalation 후 mechanical
gate 일반화 가능 시점 까지 mctrader-hub self-discipline 유지 의무.

## Cross-ref

- 본 retro: `docs/retros/PMO-PATTERNS-2026-05-17-ssot-drift-3-archive-pr-incomplete.md`
- 자매 retro (1호+2호): `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- self-write SSOT (RETRO-MCT-184): `docs/retros/RETRO-MCT-184.md`
- EPIC-RESULTS §Story-3: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` (§Story-3 MCT-184)
- Story file: `docs/stories/MCT-184.md` (frontmatter COMPLETED + §10 FIX Ledger iter1 post-merge + §11 행 4 박제 amendment PR)
- 선행 PMO 감사: `docs/retros/PMO-AUDIT-MCT-183.md` (§4 cross-document SSOT mechanical gate ADR escalation 1차 발의 — plugin-codeforge#795)
- plugin-codeforge#795 (OPEN, phase:설계-리뷰): cross-document SSOT mechanical reconcile gate ADR escalation 1차 (mctrader consumer 5회 누적)
- 신규 발의 carrier 후보 2: [plugin-codeforge#804](https://github.com/mclayer/plugin-codeforge/issues/804) (박제 PR 자체 완결도 mechanical gate — LAND 2026-05-17)
- 신규 발의 carrier 후보 3: [plugin-codeforge#805](https://github.com/mclayer/plugin-codeforge/issues/805) (post-merge audit lane 신설 — LAND 2026-05-17)
- 후보 1 cross-ref 첨부: [plugin-codeforge#795#issuecomment-4467280757](https://github.com/mclayer/plugin-codeforge/issues/795#issuecomment-4467280757) (MCT-184 evidence row 첨부 — LAND 2026-05-17)
- 1호 retro precedent: `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` §2 Drift A (operational layer)
- 2호 retro precedent: `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` §3 Drift B (architecture layer)
- F-1/F-2/F-4 carry: data 측 post-merge fix PR (#795 unblock 후 진입 — 별 세션)
- F-3 amendment LAND: hub PR #360 (fa7ea64, 2026-05-16T15:19:39Z)
