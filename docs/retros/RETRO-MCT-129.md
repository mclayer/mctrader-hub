# RETRO-MCT-129 — 5 impl repo CLAUDE.md codeforge 4종 업그레이드 propagate

**범위**: MCT-129 (mctrader-market / market-bithumb / data / engine / web 5 repo `.claude/_overlay/CLAUDE.md` append + mctrader-hub Story file 작성)
**기간**: 2026-05-11 (MCT-127 → MCT-128 → MCT-129 동일 세션 3-Story 연쇄)
**Trigger**: MCT-128 step 6 (6-repo 동기화) 신설 후 첫 propagate cycle 이행. RETRO-MCT-127 §5 (HIGH) 후속 후보 + RETRO-MCT-128 §5.2 step 6 governance 박제의 직접 실행. multi-repo doc-only.
**Status**:
- 6 commit (5 impl repo 각 1 + hub 1)
- AC 5/5 (100%) — fix-clean (FIX 0)
- doc-only fast-pass (ADR-027) 적용 — review/test/security lane skip

**Story file**: `docs/stories/MCT-129.md` (§11 PMO 회고 본 RETRO 와 동시 박제)
**Repos**: 5 impl repo (market `84b5087` / market-bithumb `18ccf28` / data `6a34b6b` / engine `bf748d8` / web `4c5bd0a`) + hub `e381d06`
**선행**: MCT-127 (codeforge plugin 4종 hub 업그레이드) → MCT-128 (hub 감사 + step 6 신설) → MCT-129 (5 repo propagate)
**후행**: GitPython HIGH 취약점 fix (mctrader-web dependabot, 본 RETRO §7 발의)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (5 AC) | 실제 | 비고 |
|---|---|---|---|
| AC1 — mctrader-market CLAUDE.md: REVIVED / 통합테스트 / claude-haiku-4-5 / 체크리스트 포인터 | 의무 | done | 24 line append (`84b5087`) |
| AC2 — mctrader-market-bithumb CLAUDE.md: 동일 4 keyword | 의무 | done | 24 line append (`18ccf28`) |
| AC3 — mctrader-data CLAUDE.md: 동일 4 keyword | 의무 | done | 24 line append (`6a34b6b`) |
| AC4 — mctrader-engine CLAUDE.md: 동일 4 keyword | 의무 | done | 24 line append (`bf748d8`) |
| AC5 — mctrader-web CLAUDE.md: 동일 4 keyword | 의무 | done | 24 line append (`4c5bd0a`) |

→ **Story scope 5/5 AC 100% 완료**. 5 repo 동일 24-line block append (uniform diff). doc-only Story 모범 template 3회 연속 적용 (MCT-127 + MCT-128 + MCT-129).

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-market` | 1 commit (`84b5087`), 24 line | main 직접 push (ADR-019 D6) |
| `mctrader-market-bithumb` | 1 commit (`18ccf28`), 24 line | main 직접 push |
| `mctrader-data` | 1 commit (`6a34b6b`), 24 line | main 직접 push |
| `mctrader-engine` | 1 commit (`bf748d8`), 24 line | main 직접 push |
| `mctrader-web` | 1 commit (`4c5bd0a`), 24 line | main 직접 push |
| `mctrader-hub` | 1 commit (`e381d06`), 75 line (Story file) | main 직접 push |

→ **총 6 commit / 6 repo / fix-clean / 동일 24-line uniform block × 5**. RETRO-MCT-127 (1 commit) / RETRO-MCT-128 (1 commit) 의 hub-only single 과 대비, 본 Story 는 multi-repo propagate uniform batch 의 첫 사례.

### 1.3 테스트 결과

doc-only Story — unit test 없음. **grep 검증으로 대체** (§6 Story file 명시).

| 검증 항목 | 결과 |
|---|---|
| 5 repo `.claude/_overlay/CLAUDE.md` REVIVED grep count | 5/5 통과 |
| 5 repo IntegrationTestAgent grep | 5/5 통과 |
| 5 repo claude-haiku-4-5 grep | 5/5 통과 |
| 5 repo 체크리스트 포인터 (hub SSOT 참조) grep | 5/5 통과 |

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 작업 (5 AC) | 5 | 100% | 본 작업 |
| Cat A (pre-existing) | 0 | 0% | — |
| Cat B (self-discovered) | 0 | 0% | — |
| Cat C (다른 Story finish-up) | 0 | 0% | — |

→ **부수 fix 0%** — RETRO-MCT-127 / 128 와 동일 lane. doc-only Story 3회 연속 fix-clean 안정화.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-market` | `main` (직접 push) | done | (없음, ADR-019 D6) | done |
| `mctrader-market-bithumb` | `main` (직접 push) | done | (없음) | done |
| `mctrader-data` | `main` (직접 push) | done | (없음) | done |
| `mctrader-engine` | `main` (직접 push) | done | (없음) | done |
| `mctrader-web` | `main` (직접 push) | done | (없음) | done |
| `mctrader-hub` | `main` (직접 push) | done | (없음) | done |

→ **6-repo Story** — 본 세션 첫 multi-repo doc-only 병렬 batch. 각 repo independent (shared state 없음, sequential dependency 없음) 으로 한 commit pattern 5회 반복. cross-repo 협업 cost = uniform diff 적용 cost (block 1회 작성 후 5 repo 분배).

---

## 2. Sonnet decider (§4 박제)

3 결정점 박제 (Story file §4):

| 결정 | 선택 | 근거 |
|---|---|---|
| 변경 방식 | append (공통 블록) | 5 repo 구조 동일, YAGNI. 각 repo 별 차별화 / per-repo 맞춤 거부 |
| 체크리스트 위치 | hub SSOT 포인터 | 중복 방지, MCT-128 체크리스트 단일 관리. 5 repo 별 inline 체크리스트 거부 |
| Story 분리 | MCT-128 + MCT-129 | hub 정리 선행 → 포인터 대상 확보 후 propagate. 단일 Story 통합 거부 (RETRO-MCT-128 §1.1 분리 표준화 반영) |

→ decider 박제 정합. 추후 multi-repo doc-only propagate 시 본 §4 가 결정 근거로 referenced 가능.

---

## 3. 3-Story 연쇄 완결 lane (MCT-127 → 128 → 129)

본 세션의 핵심 패턴 — codeforge plugin upgrade governance 의 단일 배포 사이클 완성:

### 3.1 연쇄 단계별 책임 분해

| 단계 | Story | 단일 trigger | 결과 |
|---|---|---|---|
| 1 | MCT-127 (hub) | 2026-05-10 codeforge 4종 동시 release | hub installed_plugins.json + CLAUDE.md 7섹션 갱신 |
| 2 | MCT-128 (hub) | RETRO-MCT-127 §5 (HIGH) 후속 후보 | hub run-tests.sh / run-perf.sh 주석 갱신 + step 5·6 신설 |
| 3 | MCT-129 (5 impl repo) | RETRO-MCT-128 §5.2 step 6 첫 propagate cycle | 5 repo CLAUDE.md uniform append |

→ **단일 plugin release 가 3 Story 분해되는 lane 박제**. 각 Story 책임 분리 정합:
- MCT-127: SSOT 정합 (hub 의 plugin 메타데이터 / 통합테스트 phase / Agent tier)
- MCT-128: hub 자체 governance step 신설 (감사 lane + propagate trigger)
- MCT-129: SSOT propagate (5 repo 에 동일 정보 분배)

### 3.2 process integrity 검증

본 Story 가 step 6 첫 propagate cycle — process 정합성 lane 검증:

| 검증 항목 | 결과 |
|---|---|
| step 6 명시 의무 (5 repo CLAUDE.md propagate) | done — 5/5 적용 |
| step 6 의 SSOT pointer 패턴 (hub 체크리스트 단일 관리) | done — 5 repo 모두 hub 참조 형태 |
| step 6 trigger 자동 동작 (hub-only Story 후 propagate Story 자동 발의) | done — RETRO-MCT-128 §5.2 가 본 Story trigger |
| step 6 propagate cost 측정 | 약 5 repo × 1 commit = 6 commit (hub 포함), uniform block 1 작성 후 분배 |

→ **process integrity 5/5 검증 완료**. step 6 governance 가 MCT-128 박제 → MCT-129 첫 cycle 에서 그대로 작동. RETRO-MCT-128 §5.3 governance 박제 우선 ROI 권고 정합 — 자동화 script 없이도 cognitive trigger 만으로 정합 propagate 작동.

### 3.3 lane 표준화 권고

추후 plugin family upgrade 발생 시 본 3-Story 연쇄 template 그대로 적용:
1. **hub Story** — installed_plugins.json + CLAUDE.md core annotation 갱신
2. **hub governance Story** — RETRO-1 의 (HIGH) 후속 후보 검토 + 신규 governance step 박제 if needed
3. **propagate Story** — 5 impl repo CLAUDE.md uniform block append

→ MAJOR bump 1개 + MINOR bump 0~3개 동시 release 시 본 template 직접 적용 가능. MAJOR 2개 이상 동시 시 RETRO-MCT-127 §4 권고 (commit 분리) 와 함께 검토.

---

## 4. multi-repo doc-only 병렬 batch 패턴 박제

본 세션 첫 multi-repo doc-only Story — 6-repo 병렬 batch lane 박제:

### 4.1 uniform diff 패턴 적용 조건

본 Story 가 uniform 24-line block × 5 repo 적용 — 다음 조건 만족 시 동일 패턴 적용 권고:
- 5 repo 의 CLAUDE.md 구조 동일 (헤더 / plugin list / Story workflow / Agent tier 섹션 포지션 같음)
- propagate 정보가 hub SSOT 의 단일 entity (예: plugin 버전 메모) — per-repo 차별화 없음
- 체크리스트 / detail 정보는 hub SSOT 포인터로 단축

### 4.2 병렬 batch 의 risk 점검

| risk | 발생 여부 | mitigation |
|---|---|---|
| 5 repo 간 block 내용 drift | 0 (uniform 24-line × 5) | 1회 block 작성 → 5 repo 분배, 직접 edit 금지 |
| 일부 repo 에만 적용된 partial state | 0 (5/5 commit 박제) | grep 검증 (§1.3) 으로 5/5 count 검증 |
| 같은 PR / merge cycle 강제 의무 | n/a — main 직접 push (ADR-019 D6) | doc-only fast-pass + ADR-019 D6 |

→ **risk zero exposure**. doc-only multi-repo batch 의 uniform diff 패턴은 RETRO-MCT-128 §3 의 zero exposure lane 과 동일 — 사전 risk 가정 vs 실제 zero 의 직접 검증.

### 4.3 multi-repo non-doc Story 와 비교 의의

본 Story 의 uniform pattern 은 **doc-only 에 특화** — 추후 multi-repo non-doc Story (예: MCT-12 6-repo codeforge 본격 적용) 진입 시 본 패턴 직접 적용 불가. non-doc Story 는 per-repo 차별화 / per-repo 테스트 / per-repo CI cycle 필요. 본 Story 는 doc-only 에 한정한 uniform batch template 으로 박제.

---

## 5. RETRO-MCT-127 / 128 대비 lane 비교

| 항목 | RETRO-MCT-127 | RETRO-MCT-128 | RETRO-MCT-129 |
|---|---|---|---|
| commit 수 | 1 (hub 1) | 1 (hub 1) | 6 (impl 5 + hub 1) |
| repo 수 | 1 | 1 | 6 |
| AC 충족률 | 4/4 (100%) | 4/4 (100%) | 5/5 (100%) |
| Cat A/B/C fix 비율 | 0% / 0% / 0% | 0% / 0% / 0% | 0% / 0% / 0% |
| CI cycle | 0 (doc-only fast-pass) | 0 (doc-only fast-pass) | 0 (doc-only fast-pass) |
| Sonnet decider 결정점 | 3 | 3 | 3 |
| 자동 dispatch 게이트 충족 | done | done | done |
| 패턴 분류 | hub SSOT 정합 | hub governance 박제 | multi-repo SSOT propagate |

→ **doc-only Story 모범 template 3회 연속 적용**. 단일 trigger / single purpose / decider 박제 / fix-clean / fast-pass 안정화. 본 Story 는 추가로 multi-repo uniform batch 패턴 박제. 추후 doc-only Story 는 본 3개 RETRO 를 reference template 로 사용 가능.

---

## 6. 위반 / 개선 사항

**위반 없음**:
- AC 100% 충족 (5/5)
- fix-clean (FIX 0)
- §11 회고 자동 dispatch (`feedback_pmo_retro_mandatory.md`) 게이트 충족 — 3 Story 연속 (MCT-127 + MCT-128 + MCT-129) 자동 dispatch lane 유지

**개선 제안 1건** (RETRO-MCT-128 §7 의 후속 평가):
- **5 impl repo CLAUDE.md propagate 자동화 script 부재** — RETRO-MCT-128 §7 에서 ROI 재평가 의무가 본 Story 실행 후로 정의됨. **본 Story 실측 propagate cost = 5 repo × uniform 24-line append (cognitive cost: block 1회 작성, mechanical cost: 5 repo 분배 + 5 commit + 5 grep 검증)**. script 작성 cost 와 비교:
  - 자동화 ROI 임계 = plugin MAJOR bump 분기당 2회 이상 (RETRO-MCT-128 §5.3 박제)
  - 현재 빈도 = 분기당 1회 (codeforge family 첫 동시 release)
  - **결론**: 자동화 script defer 유지. 다음 plugin family upgrade 발생 시 (RETRO-MCT-129 권고로) 빈도 재산정. 단, 5 repo → 10 repo 확장 (예: ADR-001 6-repo → mclayer scope 확장) 시 즉시 자동화 trigger.

---

## 7. 후속 Story 후보

| 후보 | 우선순위 | 근거 | 추정 Story key |
|---|---|---|---|
| **mctrader-web GitPython HIGH 취약점 fix** | **HIGH** | 본 Story commit push 직후 GitHub dependabot HIGH 알림 1건 (`GitPython` newline injection RCE, CVE-2026-42215 패치 우회). mctrader-web requirements 에서 직접/간접 의존성 grep + 안전 버전 bump. 본 Story 는 doc-only 였으나 push side-effect 로 alert surface — finish-up Story trigger. | MCT-130 후보 |
| codeforge MINOR/PATCH bump 시 step 6 자동 trigger 검증 | MED | 본 Story 가 MAJOR + MINOR 동시 (codeforge 4종) 의 첫 propagate cycle. MINOR/PATCH only 시 step 6 propagate Story 가 자동으로 발의되는지 검증 lane 식별 — propagate scope 축소 가능 (annotation 변경 없으면 propagate 불요). | TBD |
| 6-repo CLAUDE.md drift 감사 (분기 1회) | LOW | uniform block append 후 시간 경과 시 per-repo edit 발생 가능. hub SSOT 변경 시 5 impl drift grep 자동 검증 lane. 본 Story 직후는 drift 0 — 분기 1회 LOW priority backlog. | TBD |
| docker-compose.test.yml MCT-41 통합 (RETRO-127 §5 carry-over) | MED | RETRO-MCT-127 §5 MED 후보 carry-over. codeforge-develop 0.4.0 `presets/docker-compose.test.yml` 의 6-repo 적용. MCT-41 진입 시 trigger. | MCT-41 amendment |

---

## 8. Cross-Story 패턴 메모 (PMO 횡단 감사용)

본 RETRO 가 향후 cross-Story 패턴 분석 (PMOAgent §3 책임) 시 referenced 될 항목:

- **doc-only Story 모범 template 3회 연속 적용 (MCT-127 + MCT-128 + MCT-129)** — 추후 plugin upgrade / governance / propagate Story reference template
- **3-Story 연쇄 완결 lane (hub SSOT → hub governance → multi-repo propagate)** — 단일 plugin family release 의 표준 분해 패턴 박제
- **multi-repo doc-only uniform batch 패턴** — 5 repo × 24-line append 의 risk-zero lane (§4)
- **step 6 (6-repo 동기화) governance 자동 trigger 입증** — RETRO-MCT-128 §5.2 박제가 MCT-129 trigger 로 자동 작동, 자동화 script 없이도 cognitive trigger 정합
- **자동화 ROI 임계 박제** — plugin MAJOR bump 분기당 2회 이상 또는 6-repo → 10-repo 확장 시점에서만 propagate script 자동화 trigger
- **commit push side-effect surface (dependabot alert)** — multi-repo push 시 GitHub side-effect 로 surface 되는 alert 의 finish-up Story trigger lane (MCT-130 후보)

---

**Status**: done — 본 RETRO 박제로 §11 PMO 회고 자동 dispatch 게이트 충족 (`feedback_pmo_retro_mandatory.md`). MCT-130 (mctrader-web GitPython HIGH 취약점 fix) 즉시 우선 진행 권고.
