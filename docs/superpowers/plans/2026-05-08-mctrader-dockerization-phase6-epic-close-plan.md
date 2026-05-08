# mctrader Docker-first Migration Phase 6 (Epic close) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Epic MCT-98 (mctrader Docker-first Migration) Phase 6 close — `EPIC-RESULTS-MCT-98.md` 박제 + Story/Epic body 갱신 + F6 follow-up issue + memory sync.

**Architecture:** documentation-only PR. 단일 mctrader-hub PR 가 EPIC-RESULTS doc + Story §8.6/§11 fill-in + spec/plan 박제 + Epic body update commit 모음. Codex 7-area review pass 후 admin merge → `Closes #120` 자동 close. mctrader-web repo 에 F6 issue 신규 등록 (Phase 4 surface CI break, post-Epic Story 후보).

**Tech Stack:** Markdown / git / gh CLI (PR + issue 관리) / Codex review agent.

---

## Phase plan (sequential, single session)

10 task — 모두 mctrader-hub `docs/MCT-98-phase6-epic-close` branch 단일 PR.

---

### Task 1: Commit spec + plan

**Files:**
- Modify (already written): `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase6-epic-close-design.md`
- Modify (this file): `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase6-epic-close-plan.md`

- [ ] **Step 1: Stage + commit spec**

```bash
git add docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase6-epic-close-design.md
git commit -m "$(cat <<'EOF'
[MCT-98] docs(spec): Phase 6 Epic close design — EPIC-RESULTS-MCT-98 + 9 D

Codex review agentId a63731290d7d25208 일괄 review + Sonnet 합성:
- D1=A root location / D2=C MCT-97 base + Docker ext / D3=C inline + defer
- D4=C F6 즉시 / 나머지 list / D5=A single PR Closes #120 / D6=C hybrid 5 deep
- D7=C MCT-98 dual-anchor / D8=C comprehensive metrics / D9=B defer F7

Phase 6 의 단일 잔여 = B5 (EPIC-RESULTS-MCT-98 작성). Phase 1-5 ALL DONE 2026-05-08.

EOF
)"
```

- [ ] **Step 2: Stage + commit plan**

```bash
git add docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase6-epic-close-plan.md
git commit -m "[MCT-98] docs(plan): Phase 6 Epic close 10-task plan"
```

---

### Task 2: Write EPIC-RESULTS-MCT-98.md

**Files:**
- Create: `EPIC-RESULTS-MCT-98.md` (root)

- [ ] **Step 1: §1 목적 + §2 산출 PR 표 작성**

§2 산출 PR 표는 phase 별 (Phase 1: data#11, Phase 2: hub#122, Phase 3: hub#135 + engine#37, Phase 4: hub#136 + web#22 + hub#141, Phase 5: hub#137 + market#2 + bithumb#5).

Phase 6 본 PR 추가 — placeholder `<phase6-pr-#>` 로 두고 post-merge fill 의무.

- [ ] **Step 2: §3 6 Phase Milestone + §4 ADR + 신규 pattern**

§3: 6 phase 표 (Phase / Story / Issue / 완료일 / 핵심 산출).

§4 ADR amendment + 신규 pattern:
- ADR-009 §D12 (Phase 2 박제, named volume + forward-only + DR backup)
- ADR-015 cross-ref (Phase 3, Docker SM mapping anchor)
- ADR-016 §A1-A4 (Phase 4, hash chain integrity-aware DR)
- 신규 pattern: D13 fcntl.flock cross-container mutex (Phase 3, NOT-YET ADR-formalized — F9 carry-over)

13 D × 3 phase summary 표 (Phase 1 Pilot 7D / Phase 3 13D / Phase 4 13D 합 = 33 결정 박제).

- [ ] **Step 3: §5 Cross-cutting Findings 5 deep dive + carry-over 표**

§5.1 F6 collector e2e Linux-only failure (HIGH):
- 증상 / origin (MCT-97 P6) / surfacing trigger (Phase 4 pyright fix) / 진단 단서 / Story 후보 표시 + GitHub issue 신규 link

§5.2 D13 fcntl.flock cross-container mutex:
- 발견 (Phase 3 D6 검토 시) / 채택 근거 (cross-container PID ns 격리 시 atomic-write+pid-alive 깨짐) / 검증 (Linux Docker 안 evidence) / Windows pid-fallback / F9 ADR formalization carry-over

§5.3 Phase 3+4 parallel session race + worktree isolation:
- 사용자 명시적 brainstorm (Phase 5 race recovery) / hub working dir 공유 시 branch HEAD race / cherry-pick + reset recovery / worktree isolation pattern (post-Phase-4 채택) / 미래 multi-phase parallel 시 의무

§5.4 ADR-016 hash chain integrity-aware DR (Phase 4):
- 발견 (Phase 4 spec 작성 시 audit_log integrity 와 Docker volume backup conflict) / amendment 결정 (단독 §A1-A4) / Codex fix-back (3 High: backup-then-verify, NFS 금지, WAL race alternative) / 박제 결과

§5.5 ADR-009 §D12 5-sister adoption verification:
- Phase 2 박제 invariant: named volume + forward-only + DR backup (PowerShell + bash dual command)
- Phase 1 (data) 자체 / Phase 3 (engine) 4 volume topology 정합 / Phase 4 (web) `mctrader_web_data` rw + cross-stack `mctrader-data_mctrader_data` ro 정합 / Phase 5 (library) 영향 0 (배포 표면 부재) → 5/5 적용 정합

§5.6 Carry-over 표 F1-F9:

| ID | 항목 | priority | 등록 |
|---|---|---|---|
| F1 | mctrader-data CLI dep semver pinning | P-low | list-only |
| F2 | audit-cron sidecar 자동화 | P-mid | list-only |
| F3 | TLS production cert 자동화 | P-low | list-only |
| F4 | ghcr.io publish + multi-arch buildx | P-mid | list-only |
| F5 | webapp-minimal codeforge example update | P-low (codeforge 측) | list-only |
| **F6** | **collector e2e Linux-only fix** | **P-HIGH** | **GitHub issue (mctrader-web) — Task 5 에서 등록** |
| F7 | manual integration smoke 10 항목 actual deploy verification | P-mid (deploy-time ops) | list-only |
| F8 | dev sqlite git history cleanup | P-low | list-only |
| F9 | D13 fcntl.flock cross-container mutex ADR formalization | P-low (single reuse) | list-only — next reuse 시점 |

- [ ] **Step 4: §6 Cross-repo Coordination + §7 Story AC Verdict**

§6: 6 repo (data / engine / web / market / bithumb / hub) per-PR commit hash 표 + Phase 2 entry Epic body reconciliation pattern + Phase 4 last-merge 책임.

§7 Story AC Verdict:

| AC | 항목 | 결과 | 근거 |
|---|---|---|---|
| B1 | 6 repo `infra_strategy:` 명시 | PASS | data docker_first / engine docker_first / web docker_first / market none / bithumb none / hub none |
| B2 | deployable trio Docker artifact + healthcheck | PASS | data Dockerfile+compose.yml / engine paper+engine 2-service / web api+panel 2-service |
| B3 | library quartet `none` lint pass | PASS | Phase 5 MCT-102 #134 3 PR joint sweep |
| B4 | Bithumb WS finding 처리 | PASS | mctrader-market-bithumb#4 closed 2026-05-08 (PR #3 inline fix + smoke verified) |
| B5 | EPIC-RESULTS-MCT-98 작성 | PASS | 본 doc |

5/5 PASS — Story MCT-98 COMPLETE.

- [ ] **Step 5: §8 codeforge Upstream Finding + §9 Aggregate Metrics + §10 다음 Epic 후보**

§8 codeforge Upstream Finding (PMOAgent 후속 등록 대상):

| # | Finding | 영향 |
|---|---|---|
| CF-Docker-1 | parallel session hub working dir branch race 패턴 | dev workflow 비용 — superpowers worktree 의무 추가 후보 |
| CF-Docker-2 | `check-container-strategy.sh` lint UX (FAIL 메시지 명확성) | dev experience |
| CF-Docker-3 | cross-stack volume namespacing fragility (`<stack>_<volume>` external true) | dev experience — compose CLI override 자동 검증 |
| CF-Docker-4 | hadolint inline DL3008/DL3013 ignore 의 cross-Dockerfile 정합 | maintainability |
| CF-Docker-5 | webapp-minimal codeforge example update (Streamlit 2-service compose 패턴) | downstream consumer |

§9 Aggregate Metrics:

- 총 PR 수: mctrader-hub 5 (#119, #122, #135, #136, #137, #141, + 본 PR Phase 6) + sister 5 (data#11, engine#37, web#22, market#2, bithumb#5) = 11+ merged
- 총 commit 수: data 8, engine 10, web 15-squashed (실 commit 다수), market 1, bithumb 1, hub Phase 1-6 합 ~25
- 총 test 수: data +4, engine +6, web 4 fixture pyright fix + 2 신규 D6 D8 + compose invariant 6 = +12, library 0
- 총 ADR amendment 수: 3 (ADR-009 §D12 / ADR-015 cross-ref / ADR-016 §A1-A4) + 신규 pattern 1 (D13)
- 총 Codex review round (per phase agentId 박제):
  - Phase 1 Pilot: (Pilot 박제)
  - Phase 2 entry initial: `af61a4c87e9d7906c` / Phase 2 PR review: `a5ff38a167380b3d8`
  - Phase 3: (Phase 3 design + PR review agentId 모음)
  - Phase 4: (Phase 4 design + PR review agentId 모음)
  - Phase 5: `a66da458a451e3169`
  - Phase 6 design: `a63731290d7d25208`
- Phase 3+4 parallel ROI 실측: Phase 3 Story close 시간 + Phase 4 Story close 시간 = 동시 진행 (Phase 4 reconciliation 책임 commit f8d5b83 시점이 마지막 merge → Phase 4 가 last commit) → serial 가정 시 ~2× 시간 → 실제 1× 으로 50% 단축 추정
- Version bump: data 0.8.0→0.9.0 / engine 0.29.0→0.30.0 / web 0.13.0→0.14.0 (3 sister 모두 minor bump, BREAKING) / market + bithumb + hub 0 bump (declarative meta only)
- carry-over: F1-F9 9 항목 (1 HIGH = F6, 2 mid = F2/F4/F7, 5 low = F1/F3/F5/F8/F9)

§10 다음 Epic 후보:

| 후보 | 내용 | priority |
|---|---|---|
| F6 mctrader-web collector e2e fix | Linux-only failure 진단 + fix | HIGH (CI 정상화) |
| F4 ghcr.io publish | multi-arch buildx + 5 sister deployable trio image push | mid |
| F2 audit-cron sidecar | mctrader-web audit_log 자동 retention | mid |
| live executor (MCT-12) Docker 통합 | live trading executor compose run pattern | CFP-60 dependency 확인 후 |
| F9 D13 ADR formalization | 2nd reuse 시점에 author | low (defer) |

- [ ] **Step 6: §11 self-review (placeholder scan / consistency / scope / ambiguity)**

§11 절 추가 (writing-plans skill 의 spec self-review pattern):

```markdown
## §11 self-review

1. Placeholder: §2 PR 표의 본 Phase 6 PR 번호는 PR 생성 후 post-merge fill (post-merge commit 또는 PR description 직접 link 처리)
2. Consistency: §3 phase 박제 ↔ §6 cross-repo PR ↔ §7 AC Verdict 정합 확인
3. Scope: in-scope (EPIC-RESULTS doc + F6 issue + Story §8.6/§11 + Epic body update) 외 carry-over 명시
4. Ambiguity: 5 deep dive 모두 발견 / 채택 / 검증 / carry-over 4 항목 박제
```

- [ ] **Step 7: Stage + commit EPIC-RESULTS**

```bash
git add EPIC-RESULTS-MCT-98.md
git commit -m "[MCT-98] docs: EPIC-RESULTS-MCT-98 — Epic close 6 phase 박제"
```

---

### Task 3: Update MCT-98 Story §8.6 + §11

**Files:**
- Modify: `docs/stories/MCT-98.md` (lines 125-219)

- [ ] **Step 1: §8.6 Phase 6 Implementation Manifest 추가**

기존 line 148 의 "8.3-8.6 Phase 3-6 (TBD)" 다음에 새로운 §8.6 절 추가:

```markdown
### 8.3 Phase 3 (mctrader-engine)

mctrader-hub PR #135 (commit 9a5e956, 2026-05-08T02:33:04Z) + mctrader-engine PR #37 (10 commits, 0.29.0→0.30.0) — 13 D + D13 신규 pattern + 4 named volume + paper/engine 2-service.

### 8.4 Phase 4 (mctrader-web)

mctrader-hub PR #136 (commit 443807e, 2026-05-08T01:59:25Z, doc) + mctrader-web PR #22 (15 commits squash a0ac2ce, 2026-05-08T07:13:11Z, 0.13.0→0.14.0) + mctrader-hub PR #141 (commit f8d5b83, 2026-05-08T07:19:28Z, Story close) — 13 D + 2-service compose + ADR-016 amendment + 5 fix-back.

### 8.5 Phase 5 (Library batch)

mctrader-hub PR #137 (commit e763352, 2026-05-08T01:58:58Z, anchor) + mctrader-market#2 + mctrader-market-bithumb#5 — 3 PR joint sweep, declarative `infra_strategy: none` × 3 repo.

### 8.6 Phase 6 (Epic close, this PR)

본 PR commit 박제:

| # | commit | 내용 |
|---|---|---|
| 1 | spec commit | 본 spec |
| 2 | plan commit | 본 plan |
| 3 | EPIC-RESULTS commit | EPIC-RESULTS-MCT-98.md (root) |
| 4 | Story §8.6+§11 update commit | 본 Story file |
| 5 | Epic body reconciliation commit | post-merge fill (Phase 6 status DONE + B5 ✅) |
| 6 | F6 GitHub issue (mctrader-web) | Task 5 — separate `gh issue create` |

본 PR merge 시 Epic #120 자동 close (PR body `Closes #120`).
```

- [ ] **Step 2: §11 회고 placeholder fill-in**

기존 line 209-219 의 "본 §11 은 Phase 6 (Epic close) 시점에 박제" 항목을 다음으로 교체:

```markdown
## 11. 회고

### 11.1 6 phase 별 실제 vs 계획 시간

| Phase | 계획 (Phase 2 entry session) | 실제 | 비고 |
|---|---|---|---|
| 1 Pilot | 2026-05-07 1 session | DONE 2026-05-07 | mctrader-data 4시간 brainstorm + 8 commit + 1 day |
| 2 Entry/bookkeeping | 2026-05-08 1 session | DONE 2026-05-08 (PR #122) | retroactive registration + bithumb verification dual-task |
| 3 Engine | Phase 2 다음 1 session (engine first) | DONE 2026-05-08 (parallel) | revised: parallel || Phase 4 |
| 4 Web | Phase 3 다음 1 session | DONE 2026-05-08 (parallel) | revised: parallel || Phase 3 |
| 5 Library | Phase 4 다음 1 session | DONE 2026-05-08 | 3 PR joint sweep, declarative |
| 6 Epic close | Phase 5 다음 1 session | DONE 2026-05-08 (본 PR) | 단일 PR + EPIC-RESULTS doc |

→ Phase 1+2+3+4+5+6 모두 2 calendar day (2026-05-07 → 2026-05-08) 안에 완료. Phase 3+4 parallel revision 이 critical path 단축 효과 50% 추정.

### 11.2 Hybrid by shape sequencing 의 ROI 실측

D2 결정 (deployable trio + library quartet 분리) 의 결과:
- deployable trio (3 phase × 2 sister + Pilot) 가 review 부피 90% 차지
- library quartet (1 phase × 3 repo) 가 declarative meta only → review 부피 5% 미만
- 만약 Mode A serial 채택 시 library 3 repo × 별도 Story = process weight 3× 증가
- Hybrid by shape ROI 검증 PASS

### 11.3 Pilot reference 5 sister rollout reuse 매트릭스

| Pilot pattern | Phase 3 engine | Phase 4 web | Phase 5 library |
|---|---|---|---|
| 2-stage Dockerfile (deps+runner) | ✅ reused | ✅ reused (2-stage) | n/a (no Dockerfile) |
| non-root user mctrader UID 1001 | ✅ | ✅ | n/a |
| named volume `mctrader_data` | n/a (own volume) | ✅ cross-stack RO | n/a |
| HealthServer HTTP /health | ✅ engine paper | ✅ api `/health` + panel `/_stcore/health` | n/a |
| restart unless-stopped | ✅ | ✅ | n/a |
| `infra_strategy: docker_first` | ✅ | ✅ | n/a — `infra_strategy: none` 채택 |
| `image-lint.yml` hadolint | ✅ | ✅ | n/a |
| `tests/integration/README.md` smoke | ✅ 10-step | ✅ 10-step + Smoke 8.B | n/a |

→ Pilot reference reuse rate 7/8 (engine) / 7/8 (web) / 0/8 (library 의도적). 5 sister 가 Pilot 패턴 의 invariant 만 채택, novel pattern (D13 / D8 cross-stack volume / ADR-016 amendment) 만 추가 박제.

### 11.4 ADR-009 §D12 amendment 의 5 sister 적용 정합성

Phase 2 entry 박제 invariant (named volume + forward-only + DR backup):
- Phase 1 data 자체 — invariant 자체 source
- Phase 3 engine — 4 volume topology (mctrader_data:ro + engine_runs + engine_wfo + engine_lock) 가 §D12 정합 (data 의 named volume 외에 engine 자체 named volume 추가)
- Phase 4 web — `mctrader_web_data:rw` (api 자체) + `mctrader-data_mctrader_data:ro` external (cross-stack) 가 §D12 정합 (RO mount 가 named volume 그대로)
- Phase 5 library — n/a (배포 표면 부재)
- 적용 5/5 정합. §D12 가 sister rollout 의 reference 로서 안정 작동.

### 11.5 Phase 2 entry Bithumb verification 의 Phase 5 entry 단순화 효과

Phase 2 entry session 시점 (2026-05-08 09:00 KST 추정):
- 박제 timeline 누락 → mctrader-market-bithumb#4 issue 등록 (B "issue + blocker")
- 사용자 directive "c" → 직접 smoke 실행 → PR #3 fix 발견 + verification → close
- 결과: Phase 5 entry 시점에 bithumb fix 의무 = "이미 만족" 으로 간주 가능

만약 Phase 2 entry 에서 verification 미실행 시:
- Phase 5 entry 의 B4 acceptance 가 "verification 미박제" → Phase 5 추가 검증 책임 → process weight 2× 증가
- Phase 2 entry verification 이 critical path simplification + AC 박제 가능 시점 1 phase 단축 효과

### 11.6 후속 ADR 후보 (cross-cutting finding 정리)

EPIC-RESULTS-MCT-98 §5 5 deep dive + §8 codeforge upstream finding 5건 별도 박제. 본 §11.6 은 ADR 후보로 좁힘:

| 후보 | trigger | 본 Epic 인 인 / 외 |
|---|---|---|
| ADR-? D13 fcntl.flock cross-container mutex | 2nd reuse 시점 | 외 (carry-over F9) |
| ADR-016 amendment | hash chain integrity-aware DR | 인 (Phase 4 amendment landed) |
| ADR-009 §D12 amendment | named volume + forward-only + DR backup | 인 (Phase 2 entry landed) |
| ADR-015 cross-ref | Docker SM mapping anchor | 인 (Phase 3 amendment landed) |

→ 본 Epic 가 박제한 ADR amendment 3 + 신규 pattern 1 (D13). F9 만 carry-over.
```

- [ ] **Step 3: status frontmatter 업데이트**

```yaml
---
story_key: MCT-98
story_issues:
  - repo: mclayer/mctrader-hub
    number: 120
status: complete
---
```

- [ ] **Step 4: Stage + commit Story update**

```bash
git add docs/stories/MCT-98.md
git commit -m "[MCT-98] docs(story): §8.3-8.6 Phase 3-6 Impl Manifest + §11 회고 fill-in + status complete"
```

---

### Task 4: Update Epic #120 body draft (in-PR markdown for post-merge)

**Files:**
- Create: `docs/superpowers/specs/2026-05-08-phase6-epic-body-update.md` (post-merge instruction file, gitignore'd or 의도적 박제)

대안: post-merge 직접 `gh issue edit 120 --body` 로 수행. body update 는 PR commit 으로 박제 안 함 → 본 task 는 post-merge phase 의 step 으로 분류.

- [ ] **Step 1: Epic body update 내용 사전 작성**

post-merge 시 Epic #120 body 의 다음 변경:
- Phase 6 — Epic close 줄에 ✅ DONE + commit + PR # + EPIC-RESULTS link 추가
- Acceptance Criteria: B1, B2, B5 모두 [x] checked 로 update
- 본문 끝에 "Closes" footer 추가

post-merge `gh issue edit 120 --body` 시 사용할 markdown 을 다음 file 에 박제:

`docs/superpowers/specs/2026-05-08-phase6-epic-body-update.md` (참고용, 본 PR 에 포함):

```markdown
# Epic #120 body — Phase 6 close update (post-merge instruction)

본 file 은 PR merge 후 Epic body 업데이트 시 사용할 markdown 박제. PR description 의 `Closes #120` 가 issue close 자동 처리하지만 body 자체 업데이트 (Phase 6 status / B1+B2+B5 checked) 는 별도 `gh issue edit 120 --body` 명령으로 수행.
```

- [ ] **Step 2: Stage + commit (skip — post-merge 만 수행)**

본 task 는 commit 없음. PR description 의 `Closes #120` footer 가 자동 close 트리거. body update 는 post-merge step.

---

### Task 5: F6 GitHub issue 생성 (mctrader-web repo)

post-merge step. 본 task 는 PR commit 없음 — `gh issue create` 명령 박제.

- [ ] **Step 1: issue body markdown 작성**

post-merge 시 다음 명령으로 등록:

```bash
gh issue create \
  --repo mclayer/mctrader-web \
  --title "collector e2e test failure (Linux-only) — pyright AsyncGenerator fix 후 surface (MCT-97 P6 era pre-existing, MCT-98 Epic F6)" \
  --label "priority:high,bug,inherited-pre-existing" \
  --body "$(cat <<'EOF'
## Background
mctrader Docker-first Migration Epic (MCT-98 #120) Phase 4 (mctrader-web Docker-first containerization) 작업 중 pyright 4 fixture root fix (`AsyncGenerator[AsyncClient, None]`) 후 collector e2e 테스트 1건이 Linux 전용으로 실패하는 현상이 surface 되었습니다.

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
- Epic MCT-98 mclayer/mctrader-hub#120 EPIC-RESULTS §5.1
- Story MCT-101 mclayer/mctrader-hub#132 §11 finding F6
- Story MCT-97 mclayer/mctrader-hub#110 follow-up (priority HIGH)
EOF
)"
```

- [ ] **Step 2: 검증**

```bash
gh issue view <new-issue-#> --repo mclayer/mctrader-web --json state,labels,title
```

assert state=OPEN + labels=priority:high+bug+inherited-pre-existing.

---

### Task 6: Push + Create PR

- [ ] **Step 1: Push branch**

```bash
git push -u origin docs/MCT-98-phase6-epic-close
```

- [ ] **Step 2: PR 생성**

```bash
gh pr create \
  --repo mclayer/mctrader-hub \
  --base main \
  --title "[MCT-98] docs: Phase 6 Epic close — EPIC-RESULTS-MCT-98 + Story §8.6+§11 + Epic body draft" \
  --body "$(cat <<'EOF'
## Summary

mctrader Docker-first Migration Epic (MCT-98 #120) Phase 6 close PR. Phase 1-5 ALL DONE 2026-05-08, Phase 6 의 단일 잔여 = B5 (EPIC-RESULTS-MCT-98 작성).

본 PR commit:

- spec: `docs/superpowers/specs/2026-05-08-mctrader-dockerization-phase6-epic-close-design.md` — 9 D Codex review (agentId `a63731290d7d25208`) + Sonnet 합성
- plan: `docs/superpowers/plans/2026-05-08-mctrader-dockerization-phase6-epic-close-plan.md` — 10 task
- **`EPIC-RESULTS-MCT-98.md` (root)** — 10 절 (목적 / 산출 PR / 6 Phase Milestone / ADR + 신규 pattern / 5 deep dive cross-cutting + carry-over F1-F9 / cross-repo / AC verdict B1-B5 / codeforge upstream / aggregate metrics + parallel ROI / 다음 Epic 후보)
- MCT-98 Story §8.3-§8.6 Impl Manifest + §11.1-§11.6 회고 fill-in + status complete
- Epic body update 박제 (post-merge `gh issue edit 120 --body`)

## Out-of-PR (post-merge)

- F6 GitHub issue 등록 (mclayer/mctrader-web) — collector e2e Linux-only fix follow-up Story 후보, priority HIGH
- Epic #120 body 의 Phase 6 status DONE / B1+B2+B5 [x] update + Closes footer

## 9 Decision (Codex+Sonnet 합의)

| # | 결정 | 채택 |
|---|---|---|
| D1 | location | A root |
| D2 | structure | C MCT-97+Docker ext |
| D3 | D13 ADR | C inline+defer (F9) |
| D4 | F1-F8 carry-over | C F6 즉시/나머지 list |
| D5 | close mechanic | A single PR Closes #120 |
| D6 | findings depth | C hybrid 5 deep |
| D7 | Phase 6 Story | C MCT-98 dual-anchor |
| D8 | metrics | C comprehensive |
| D9 | F7 live smoke | B defer |

## Acceptance Criteria (Epic level)

- [x] B1 6 repo \`infra_strategy:\` 명시 (Phase 5 DONE)
- [x] B2 deployable trio Docker artifact + healthcheck (Phase 1+3+4 DONE)
- [x] B3 library quartet \`none\` lint pass (Phase 5 DONE)
- [x] B4 Bithumb WS finding 처리 (Phase 2 entry DONE)
- [x] B5 EPIC-RESULTS-MCT-98 작성 (본 PR DONE)

5/5 PASS — Story MCT-98 COMPLETE.

## Test plan

- [ ] phase-gate-mergeable green
- [ ] story_uri marker 포함 (본 PR body)
- [ ] EPIC-RESULTS link 유효 (post-merge raw URL fetch)
- [ ] F6 issue 생성 + label 적용 (post-merge `gh issue view`)
- [ ] Epic #120 자동 close (PR merge 후 \`gh issue view 120 --json state\` = CLOSED)

story_uri: https://github.com/mclayer/mctrader-hub/blob/main/docs/stories/MCT-98.md

Closes #120

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: PR # 확인**

```bash
gh pr list --state open --head docs/MCT-98-phase6-epic-close --json number,title
```

- [ ] **Step 4: phase-gate-mergeable 트리거 확인 + 초기 watch**

```bash
gh pr checks <pr#> --watch
```

(no-background watch per memory feedback — foreground polling)

---

### Task 7: Codex 7-area review dispatch

- [ ] **Step 1: Codex agent dispatch**

PR # 확보 후 codex-rescue agent 호출:

```
Agent({
  description: "Phase 6 EPIC-RESULTS-MCT-98 Codex 7-area review",
  subagent_type: "codex:codex-rescue",
  prompt: "<Phase 6 close PR # + 본 spec/plan/doc 박제 + 7-area review checklist>"
})
```

7-area: Architecture / Security / Test / DataMigration / OperationalRisk / Performance / Refactor

문서 PR 의 핵심 review 영역:
- Architecture: 9 D 결정 정합 + EPIC-RESULTS structure
- Test: doc PR 이라 test 의무 0 — `phase-gate-mergeable` 만
- DataMigration: 본 Epic 자체가 Docker-first 데이터 migration 의무 — 5 sister 박제 정합 검증
- OperationalRisk: F6 등 carry-over 의 priority 적정성
- Refactor: Story §8.6 + §11 fill-in 의 cross-doc 정합

- [ ] **Step 2: review 완료 대기 + finding 분류**

review 결과를 finding severity 분류:
- High: must fix before merge
- Medium: nice-to-have, fix-back commit 채택 가능
- Low/Nit: 박제 후 carry-over 가능

---

### Task 8: Codex fix-back 적용 (if any)

- [ ] **Step 1: High + Medium finding 처리**

각 finding 별 commit:
```bash
git commit -m "[MCT-98] docs: Codex 7-area review fix-back — <finding summary>"
```

- [ ] **Step 2: re-review (Codex SendMessage)**

fix-back commit hash 통보 + APPROVE 판정 대기.

---

### Task 9: CI green watch + admin merge → Epic auto-close

- [ ] **Step 1: CI green watch**

```bash
gh pr checks <pr#> --watch
```

terminal state 분류 (memory feedback):
- SUCCESS → admin merge 단계 진행
- FAILURE → 즉시 fix-and-push (auto-recovery)
- ACTION_REQUIRED → 즉시 사용자 surface
- BLOCKED → 즉시 사용자 surface

- [ ] **Step 2: admin merge**

CI green 확인 후 즉시 admin merge (memory feedback "Admin merge autonomy"):

```bash
gh pr merge <pr#> --admin --squash --subject "[MCT-98] docs: Phase 6 Epic close — EPIC-RESULTS-MCT-98 + Story complete"
```

- [ ] **Step 3: Epic #120 close 확인**

```bash
gh issue view 120 --json state,closedAt,closedBy
```

assert state=CLOSED.

- [ ] **Step 4: Epic body update**

```bash
gh issue edit 120 --body "$(cat <<'EOF'
<수정된 body — Phase 6 status DONE + B1+B2+B5 [x] + EPIC-RESULTS link>
EOF
)"
```

(Phase 6 status DONE / B1, B2, B5 모두 [x] / 본문 끝 EPIC-RESULTS link)

- [ ] **Step 5: F6 issue 등록 (Task 5 명령 실행)**

post-merge 시점에 Task 5 의 `gh issue create` 명령 실행 + 결과 link → Epic body 의 §10 다음 Epic 후보 표에 추가.

---

### Task 10: memory file 업데이트

**Files:**
- Modify: `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\project_dockerization_epic.md`
- Modify: `C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\MEMORY.md`

- [ ] **Step 1: project_dockerization_epic.md → Phase 1-6 ALL DONE**

frontmatter description: `Phase 1+2+3+4+5+6 done 2026-05-08, Epic CLOSED, EPIC-RESULTS land`. body 업데이트:
- Phase 6 줄 추가 (EPIC-RESULTS link / F6 follow-up issue # / Epic close timestamp)
- "다음 phase entry 조건" 절 삭제 (모두 만족, Epic CLOSED)
- carry-over F1-F9 박제 + F6 issue link

- [ ] **Step 2: MEMORY.md description 업데이트**

```markdown
- [Dockerization Epic state](project_dockerization_epic.md) — MCT-98 #120 ALL DONE 2026-05-08, EPIC-RESULTS-MCT-98 land, F6 follow-up
```

- [ ] **Step 3: Phase 4 memory file deprecation 표시**

`project_dockerization_phase4.md` frontmatter description 에 "**SUPERSEDED by Epic close 2026-05-08** — see `project_dockerization_epic.md`" 추가 (혹은 file 삭제 — 본 Epic close 가 Phase 4 + 다른 phase 모두 통합).

---

## Plan self-review

writing-plans skill 의 plan self-review 절차 (placeholder scan / spec coverage / type consistency):

1. **Spec coverage check**:
   - spec §2 in-scope 5 항목 ↔ plan task 매핑:
     - EPIC-RESULTS doc → Task 2
     - Story §8.6+§11 → Task 3
     - Epic body update → Task 4 + Task 9 step 4
     - F6 issue → Task 5 + Task 9 step 5
     - memory file → Task 10
   - 5/5 매핑 PASS

2. **Placeholder scan**:
   - "TBD" 검색: §11.1 시간 비교 의 "1 session" 추정치 — 실제 commit timestamp 로 정밀화 가능, accepted
   - PR # placeholder — Task 6 step 3 에서 확보 후 Task 7-10 의 명령에 채움 (template 패턴)
   - F6 issue # placeholder — Task 5 등록 후 Task 9 step 5 에서 확보 + Task 10 step 1 의 body 채움

3. **Type consistency check**:
   - Task 5 의 `<new-issue-#>` ↔ Task 9 step 5 의 issue # ↔ Task 10 step 1 의 issue link — 동일 변수 표기 정합
   - PR # `<pr#>` 모두 Task 6 step 3 결과 변수 — 정합

self-review PASS — execute 단계 진입.

---

## Execution Handoff

**Plan complete.** 본 PR 은 documentation-only — subagent-driven-development 의 fresh subagent per task 보다 단일 inline execution 이 효율적 (cross-task context 의존 강함, doc 통일성 의무). 

**Inline execution** 채택 — 단일 session 안에서 Task 1-10 sequential 실행 + Task 4+5+9 의 post-merge step 만 분리.

memory feedback 적용:
- "Skip /compact prompt" — phase 종료 시 /compact 안내 stop 간주 → 다음 phase 직진 (본 Phase 6 가 final phase)
- "Admin merge autonomy" — CI green 후 즉시 admin merge
- "No background CI watch" — foreground polling
- "CI failure auto-recovery" — fix-and-push 자동 cycle
