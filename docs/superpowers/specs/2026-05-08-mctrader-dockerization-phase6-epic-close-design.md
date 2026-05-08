# mctrader Docker-first Migration — Phase 6 Epic Close (EPIC-RESULTS-MCT-98) Design

**Status**: design  
**Author**: Sonnet decider (Codex review agentId `a63731290d7d25208`)  
**Date**: 2026-05-08  
**Story**: MCT-98 #120 Phase 6 (Epic close)  
**Parent Epic**: mctrader-hub#120 — mctrader Docker-first Migration  
**Phases preceding**: 1-5 ALL DONE 2026-05-08  

---

## §0. 메타

본 spec 은 Phase 6 (Epic close) 의 단일 산출물 — `EPIC-RESULTS-MCT-98.md` + 부수 governance update — 의 설계를 박제. 9 design 결정점 (D1-D9) Codex review 일괄 합의 + Sonnet 결정 박제.

---

## §1. Background

mctrader-hub#120 (MCT-98 "mctrader Docker-first Migration") 는 codeforge ADR-033 (CFP-128 Accepted 2026-05-07) trigger 6-phase Epic. Phase 1-5 모두 2026-05-08 완료 — 본 Phase 6 는 Epic close (acceptance criteria B5) 만 잔여.

### 1.1 Phase 1-5 종료 상태

| Phase | Story | Status | 핵심 산출 |
|---|---|---|---|
| 1 Pilot (data) | MCT-99 #121 | DONE 2026-05-07 | Dockerfile + compose + HealthServer + 7 D1-D7 |
| 2 Entry/bookkeeping | (Phase 2 scope of MCT-98) | DONE 2026-05-08 | Epic+Pilot Story retroactive + ADR-009 §D12 + Bithumb finding close |
| 3 Engine sister | MCT-100 #131 | DONE 2026-05-08 | 13 D + 4 named volume + paper/engine 2-service + D13 fcntl.flock |
| 4 Web sister | MCT-101 #132 | DONE 2026-05-08 | 13 D + 2-service compose + ADR-016 amendment + 5 fix-back |
| 5 Library batch | MCT-102 #134 | DONE 2026-05-08 | 3 PR joint sweep + `infra_strategy: none` × 3 |

### 1.2 Acceptance Criteria 현황

- [x] B1 6 repo `infra_strategy:` 명시 (DONE Phase 5)
- [x] B2 deployable trio Docker artifact + healthcheck (DONE Phase 1+3+4)
- [x] B3 library quartet `infra_strategy: none` lint pass (DONE Phase 5)
- [x] B4 Bithumb WS finding 처리 (DONE Phase 2 entry session)
- [ ] **B5 EPIC-RESULTS-MCT-98 작성** (본 Phase 6 의 유일 잔여)

---

## §2. Scope

### 2.1 In-scope

1. **`EPIC-RESULTS-MCT-98.md`** (root) — Epic 회고/결과 박제 단일 source of truth
2. **MCT-98 Story §8.6 + §11** — Phase 6 Implementation Manifest + 회고 fill-in
3. **Epic #120 body** — Phase 6 status DONE + B1-B5 final reconciliation + EPIC-RESULTS link
4. **F6 GitHub issue 신규 생성** — collector e2e Linux-only fix follow-up Story 후보
5. **memory file** `project_dockerization_epic.md` → Phase 1-6 ALL DONE

### 2.2 Out-of-scope (carry-over Story 후보)

- F1-F5/F7/F8 별도 Story 등록 (carry-over 표 박제만)
- F9 D13 fcntl.flock cross-container mutex ADR formalization (next reuse 시점에 수행)
- 3-stack live deploy smoke (F7 — deploy event 시점 ops 책임)
- ghcr.io publish + multi-arch buildx (F4)
- audit-cron sidecar 자동화 (F2)

---

## §3. 9 Design Decisions (Codex+Sonnet 합의)

| # | 결정 | 채택 | 거절 |
|---|---|---|---|
| D1 | Document location | **A: root** `EPIC-RESULTS-MCT-98.md` | B docs/results/ — single instance / C docs/ — older |
| D2 | Document structure | **C: MCT-97 base + Docker extensions** | A pure mirror — Docker novel pattern 누락 / B MCT-90 — process trace 약 |
| D3 | D13 fcntl.flock ADR formalization | **C: inline 참조 + defer (F9 carry-over)** | A 지금 — scope creep / B separate Story — traceability 약 |
| D4 | F1-F8 carry-over Story 생성 | **C: F6 즉시 / 나머지 list-only** | A 모두 list — F6 CI break 누락 위험 / B 모두 issue — close phase remediation 화 |
| D5 | Epic close mechanic | **A: 단일 PR + `Closes #120`** | B two PR — closure ambiguity / C single + manual comment — link 누락 위험 |
| D6 | Findings 깊이 | **C: hybrid (표 + 5 deep dive)** | A 표만 — retrospective 약 / B 모두 deep — bloat |
| D7 | Phase 6 Story file | **C: MCT-98 §8.6/§11 dual-anchor + EPIC-RESULTS** | A no anchor — implicit / B MCT-103 신규 — process weight |
| D8 | Metrics 깊이 | **C: comprehensive (parallel ROI + Codex round + version)** | A 기계적 — process lesson 누락 / B 중간 — parallel ROI 누락 |
| D9 | F7 live deploy smoke | **B: 전적 defer** | A 인라인 실행 — scope creep / C partial — false confidence |

### 3.1 D6 Hybrid deep dive 5 후보

1. **F6 collector e2e Linux-only failure** (HIGH priority CI break, MCT-97 P6 era pre-existing, Phase 4 pyright fix 후 surface)
2. **D13 fcntl.flock cross-container mutex** (Phase 3 novel pattern — POSIX OFD-managed mutex 가 PID namespace 격리 cross-container 에서도 동작)
3. **Phase 3+4 parallel session race** (worktree isolation pattern, hub working dir branch race recovery)
4. **ADR-016 hash chain integrity-aware DR** (Phase 4 amendment — backup-then-verify + WAL race + NFS 금지)
5. **ADR-009 §D12 5-sister adoption verification** (Phase 2 박제 → Phase 3 4 volume + Phase 4 mctrader_web_data + cross-stack RO 모두 정합)

### 3.2 D8 Aggregate metrics 항목

- 총 PR 수 (mctrader-hub + 5 sister repo, merged)
- 총 commit 수 (per repo + per phase)
- 총 test 수 + Δ baseline → final
- 총 ADR amendment 수 (ADR-009 / ADR-015 / ADR-016)
- 총 Codex review round (per phase agentId)
- Phase 3+4 parallel session 시작-종료 timestamp delta (ROI 실측)
- Version bump 요약 (data 0.8→0.9, engine 0.29→0.30, web 0.13→0.14)
- carry-over 후보 수 (F1-F9)

---

## §4. EPIC-RESULTS-MCT-98 Document Structure

10 절 구성 — MCT-97 패턴 base + Docker-specific 확장 (§4 ADR / §5 Cross-cutting / §9 Aggregate Metrics 가 확장 절):

```
# EPIC-RESULTS-MCT-98 — mctrader Docker-first Migration

## §1 목적
codeforge ADR-033 trigger 후 mctrader 6-repo Docker-first 전환 + ADR-009 §D12 박제 + Phase 3+4 parallel sister rollout.

## §2 산출 PR 목록 (per phase, per repo)
표: # | Repo | PR | Phase | merged at | 핵심

## §3 6 Phase Milestone
표: Phase | Story | Issue | 완료일 | 핵심 산출

## §4 Architecture 결정 (ADR + 신규 pattern)
- ADR amendment: 009 §D12 / 015 cross-ref / 016 §A1-A4
- 신규 pattern: D13 fcntl.flock cross-container mutex (Phase 3, F9 carry-over for ADR formalization)
- 13 D × 3 phase (1 Pilot 7 + Phase 3 13 + Phase 4 13) summary

## §5 Cross-cutting Findings (5 deep dive + carry-over 표)
### 5.1 F6 collector e2e Linux-only (deep, HIGH)
### 5.2 D13 fcntl.flock cross-container mutex (deep)
### 5.3 Phase 3+4 parallel session race + worktree isolation (deep)
### 5.4 ADR-016 hash chain integrity-aware DR (deep)
### 5.5 ADR-009 §D12 5-sister adoption verification (deep)
### 5.6 Carry-over 표 (F1-F9)

## §6 Cross-repo Coordination
- 6 repo (data / engine / web / market / market-bithumb / hub) per-PR commit hash + status
- Phase 2 entry reconciliation pattern (Epic body update)
- Phase 4 reconciliation 책임 (last merge → status DONE)

## §7 Story Acceptance Verdict (B1-B5)
표: AC | 항목 | 결과 | 근거

## §8 codeforge Upstream Finding (PMOAgent 후속 등록 대상)
표: # | Finding | 영향
- CF-Docker-1 ~ CF-Docker-N (수: 후속 도출, 예: parallel session race 패턴 / `check-container-strategy.sh` lint UX / cross-stack volume namespacing)

## §9 Aggregate Metrics (Docker-specific)
- PR / commit / test 수
- ADR amendment / 신규 pattern 수
- Codex review round (per phase)
- Phase 3+4 parallel ROI 실측
- Version bump summary

## §10 다음 Epic 후보
- F6 collector e2e Linux fix (HIGH)
- F9 D13 ADR formalization (next reuse 시)
- F1-F5/F7/F8 list (priority 지정)
- live executor (MCT-12) Docker 통합 — Phase 6+ 후보
- ghcr.io publish multi-arch (F4)
```

---

## §5. MCT-98 Story §8.6 + §11 Update

### §8.6 Phase 6 Implementation Manifest

본 PR commit + Phase 6 산출 박제:

| # | commit | 내용 |
|---|---|---|
| 1 | spec commit | 본 spec |
| 2 | plan commit | 본 plan |
| 3 | EPIC-RESULTS commit | EPIC-RESULTS-MCT-98.md |
| 4 | Story update commit | MCT-98 §8.6/§11 fill-in |
| 5 | Epic body reconciliation commit (post-merge fill) | Phase 6 status DONE + B5 ✅ |

### §11 회고 fill-in (placeholder → final)

placeholder (line 209-219, "본 §11 은 Phase 6 (Epic close) 시점에 박제") 항목 모두 fill-in:

- 6 phase 별 실제 vs 계획 시간 비교
- Hybrid by shape sequencing 의 ROI 실측
- Pilot reference 가 sister rollout 들에 얼마나 reuse 됐는지
- ADR-009 §D12 amendment 의 5 sister 적용 정합성
- Phase 2 entry 의 Bithumb verification 가 Phase 5 entry 단순화에 미친 영향
- 후속 ADR 후보 (Phase 6 cross-cutting finding 정리)

---

## §6. Epic #120 Body Final Reconciliation

### 6.1 변경 항목

- Phase 6 status: TBD → DONE (PR # + commit + EPIC-RESULTS link)
- Acceptance Criteria 표: B1-B5 모두 [x] checked
- 본문 끝에 "Closes" footer + EPIC-RESULTS link

### 6.2 Closes mechanic

PR body 에 `Closes #120` 명시 → admin merge 시 자동 close.

---

## §7. F6 GitHub Issue 신규 생성

### 7.1 Title

`[mctrader-web] collector e2e test failure (Linux-only) — pyright AsyncGenerator fix 후 surface (MCT-97 P6 era pre-existing)`

### 7.2 Body 구조

```markdown
## Background
MCT-101 Phase 4 (mctrader-web Docker-first containerization) 작업 중 pyright 4 fixture root fix (`AsyncGenerator[AsyncClient, None]`) 후 collector e2e 테스트 1건이 Linux 전용으로 실패하는 현상이 surface 되었습니다.

## 증상
- `tests/api/test_admin_engines_e2e_linux.py::test_linux_systemd_collector_start - assert 500 == 200`
- Linux 전용 (Windows 미발생)
- MCT-97 P6 era pre-existing (Phase 4 가 노출, Phase 4 책임 0)

## Origin
MCT-97 (Admin Engine Control Panel) P6 era. Phase 4 의 admin 4 fixture pyright fix 가 surfacing trigger.

## Priority
HIGH — CI 정상화 의무.

## 진단 단서
- e2e 가 collector subprocess 시작 시 500 응답
- _USE_SUBPROCESS=True 모드 cross-platform 차이 의심
- Phase 4 admin merge bypass evidence: mctrader-web PR #22 (commit a0ac2ce, 2026-05-08T07:13:11Z)

## Acceptance
- [ ] root cause identified
- [ ] fix landed in mctrader-web
- [ ] test re-enabled or quarantined with explicit issue link

## 관련
- Epic MCT-98 #120 EPIC-RESULTS §5.1
- Story MCT-101 #132 §11 finding F6
- Story MCT-97 #110 follow-up (priority HIGH)
```

### 7.3 Labels

- `priority:high`
- `bug`
- `area:test-ci`
- `inherited-pre-existing`

(repo `mclayer/mctrader-web` 가 등록 대상 — 근본 원인이 mctrader-web 코드 + e2e test)

---

## §8. 영향 / 의존

### 8.1 영향

- mctrader-hub: Story file 갱신 + Epic close + EPIC-RESULTS 박제
- mctrader-web: F6 issue 신규 등록만, 코드 변경 없음
- 다른 5 repo: 영향 없음

### 8.2 의존

- 선행: Phase 1-5 모두 DONE (만족 2026-05-08)
- F9 D13 ADR formalization: 본 Epic close 후 별도 trigger (next reuse 시점)
- F6 fix: 본 Epic close 후 별도 Story (post-Epic, CI 정상화 priority HIGH)

---

## §9. Test plan

본 Phase 6 는 documentation-only — 코드 변경 0 → 단위 test 의무 0. CI 검증:

| # | 검증 | 의무 |
|---|---|---|
| 1 | phase-gate-mergeable green | `gh pr checks <pr#>` |
| 2 | story_uri marker 포함 | PR body 에 `story_uri:` line |
| 3 | EPIC-RESULTS link 유효 | merge 후 raw URL fetch |
| 4 | F6 issue 생성 + label 적용 | `gh issue view <#> --json labels` |
| 5 | Epic #120 close 자동 | PR merge 후 `gh issue view 120 --json state` = `CLOSED` |

---

## §10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| 산출 형식 | EPIC-RESULTS doc + Story §8.6/§11 dual-anchor | A doc-only — Story trace 약 / B Story-only — discoverability 약 |
| Phase 6 Story 파일 | MCT-98 reuse | MCT-103 신규 — process weight, 단일 방향 close phase 에 부적절 |
| F6 등록 위치 | mctrader-web repo | mctrader-hub — close-domain mismatch |
| F9 D13 ADR formalization | defer (next reuse) | 지금 — single reuse, 일반화 데이터 부족 |
| live deploy smoke | defer | inline — Phase 6 scope creep / partial — false confidence |
| ADR formalization 모음 (D13) | F9 carry-over만 | 지금 인라인 — 일반화 데이터 부족 |

---

## §11. 참고 / 관련 파일

### 11.1 Stories

- `docs/stories/MCT-98.md` — Epic Story (이번 Phase 6 가 §8.6 + §11 채움)
- `docs/stories/MCT-99.md` — Pilot Story (Phase 1 retroactive)
- `docs/stories/MCT-100.md` — Phase 3 mctrader-engine
- `docs/stories/MCT-101.md` — Phase 4 mctrader-web
- `docs/stories/MCT-102.md` — Phase 5 library batch

### 11.2 Per-phase specs

- `docs/superpowers/specs/2026-05-07-mctrader-data-docker-pilot-design.md`
- `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase2-entry-design.md`
- `docs/superpowers/specs/2026-05-08-mctrader-engine-docker-design.md`
- `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md`
- `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase5-library-design.md` (있다면)

### 11.3 Per-phase plans

- `docs/superpowers/plans/2026-05-07-mctrader-data-docker-pilot-plan.md`
- `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase2-entry-plan.md`
- `docs/superpowers/plans/2026-05-08-mctrader-engine-docker-plan.md`
- `docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md`
- `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase5-library-plan.md`

### 11.4 ADR

- `docs/adr/ADR-009-ohlcv-schema.md` (§D12 amendment 2026-05-08)
- `docs/adr/ADR-015-engine-state-machine.md` (cross-ref Docker SM mapping anchor)
- `docs/adr/ADR-016-audit-log-immutability.md` (§A1-A4 amendment 2026-05-08)

### 11.5 codeforge upstream

- ADR-033 (carrier_story CFP-128) Accepted 2026-05-07
- `check-container-strategy.sh` lint script
- InfraEngineerAgent default = Docker-first

### 11.6 Codex review trace (per phase)

- Phase 2 entry initial design: agentId `af61a4c87e9d7906c`
- Phase 2 PR #122 7-area review: agentId `a5ff38a167380b3d8` (3 MEDIUM fix-back commit `6e40b18`)
- Phase 5 mctrader-hub#137 7-area review: agentId `a66da458a451e3169`
- Phase 6 design review (본 spec): agentId `a63731290d7d25208`

(Phase 3 / Phase 4 agentId 는 EPIC-RESULTS §9 Codex round 절에서 박제)

---

## §12. self-review 결과

자체 점검 (writing-plans skill 의 spec self-review 절차):

1. **Placeholder scan**: TBD/TODO 무 — 모든 항목 구체화. (단 §11.6 Phase 3/4 agentId 는 Story 에서 lookup 의무)
2. **Internal consistency**: D1-D9 결정 ↔ §4 EPIC-RESULTS structure ↔ §10 거절된 대안 일치 확인
3. **Scope check**: in-scope 5 + out-of-scope 명시 → 단일 PR 의 적절한 범위
4. **Ambiguity check**: §3 9 결정 모두 채택 옵션 명시, 거절 옵션 의 risk 까지 박제

self-review 통과 — plan 작성 단계로 진행.
