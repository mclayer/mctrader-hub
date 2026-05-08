# mctrader Docker-first Migration — Phase 2 Entry Design Spec

> **Source**: brainstorming session 2026-05-08, Claude Sonnet 4.6 (Opus 4.7 1M) + Codex 7-area review (agentId `af61a4c87e9d7906c`)
> **Trigger**: mctrader-data Docker-first Pilot merged 2026-05-07 (mctrader-hub PR #119 + mctrader-data#11). 본 spec = Pilot 종료 후 Epic governance state 정렬 + 5 sister rollout sequencing 결정 (Phase 2 entry).
> **Channel**: codeforge consumer phase-gate-mergeable. mctrader-hub doc PR 1개 + GitHub issue 3개 (mctrader-hub × 2 Story, mctrader-market-bithumb × 1 finding).

## §0. 메타

| 항목 | 값 |
|------|-----|
| Epic Story key | **MCT-98** — mctrader Docker-first Migration |
| Pilot Story key (retroactive) | **MCT-99** — mctrader-data Docker-first Containerization (Pilot, P1 done) |
| 본 Phase | **Phase 2 entry** — bookkeeping + governance docs + ADR-009 amendment + Bithumb finding |
| 작업 채널 | codeforge consumer (phase-gate-mergeable, doc-only fast-pass 적용) |
| In-scope repo | mctrader-hub (doc PR) + mctrader-market-bithumb (issue 등록) |
| Trigger ADR | codeforge ADR-033 (Docker-first Infra Engineering, CFP-128) |
| Pilot reference | mctrader-hub PR #119 + mctrader-data PR #11 (8 commits, 0.8.0→0.9.0) |

## §1. Background (사용자 directive + Pilot 결과)

### §1.1 사용자 directive

> "이전에 작업하다 끊긴 게 있을텐데"
> "dockerization 관련이다"

### §1.2 Pilot 결과 (mctrader-data, 2026-05-07 merged)

- Dockerfile (2-stage python:3.12-slim, non-root mctrader UID 1001)
- compose.yml (collector daemon 1 service, named volume `mctrader_data`, restart unless-stopped, healthcheck via HTTP /health)
- HealthServer HTTP /health endpoint (4 TDD test, ws_state 기반 200/503 판정)
- `.github/workflows/image-lint.yml` (hadolint job)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
- systemd 자산 일괄 삭제 (BREAKING, deploy/mctrader-collector.service + deploy/README.md + deploy/ 디렉터리 제거)
- 186 pytest PASS, hadolint clean

### §1.3 Pilot leftover finding (PR #11 본문 §11)

mctrader-market-bithumb WS schema mismatch 미fix:
- `orderbookdepth missing symbol` (line 90 ws_mapping.py)
- `invalid event_time: '2026-05-07 16:38:49.198650'` (line 33 ws_mapping.py)

Pilot Docker artifact 동작 검증됨 (image build / container start / module import / HealthServer listen / Docker HEALTHCHECK 정확 호출 / unhealthy mark 정확 — 503 + ws_state=disconnected 응답). healthy-state 도달은 mctrader-market-bithumb schema fix 후. PR 본문 "별도 issue 박제 예정" 명시되었으나 **미등록**.

### §1.4 Bookkeeping 미반영

| 항목 | 기대 | 실제 |
|---|---|---|
| Pilot Story issue (mctrader-hub `MCT-N`) | OPEN issue + retroactive close | **미등록**, spec L11 placeholder 그대로 |
| Epic Story (mctrader-hub `MCT-M`) | OPEN issue + Phase 1-6 plan | **미등록**, spec L12 placeholder 그대로 |
| Story §11 회고 | mctrader-hub `docs/stories/` | **미작성** (PR 본문 §11 ≠ Story §11) |
| Bithumb finding | mctrader-market-bithumb issue | **미등록** |
| Phase 2 sequencing 결정 | §11 회고에 박제 | **미결정** |

## §2. Scope

### §2.1 본 Phase (Phase 2 entry, in-scope)

mctrader Docker-first Migration Epic 의 governance state 를 engineering state (Pilot 결과)와 동기화. 5 sister rollout 진입 전 박제 의무.

3 doc artifact + 3 GitHub issue + 1 cross-repo finding registration.

### §2.2 결정점 (Codex 7-area review 합의)

| ID | Decision | 채택 | 거절 |
|---|---|---|---|
| **D1** | Phase 2 entry scope | **C — 4 artifact 묶음** (Epic + Pilot Story + §11 retro + Bithumb finding) | A only retro / B retro+Bithumb / D + first sister start |
| **D2** | 5 sister rollout sequencing | **C — Hybrid by shape** (deployable trio engine→web; library quartet market+bithumb+hub joint with `infra_strategy: none`) | Mode A serial / Mode B 5-parallel |
| **D3** | First sister target | **mctrader-engine** | web (multi-service novel) / library batch first |
| **D4** | Bithumb finding handling | **B — issue 등록 + bithumb sister rollout blocker** (Epic inline fix 안 함) | A defer-only / C inline fix |
| **D5** | infra_strategy for library/governance | **A — market / bithumb / hub = `infra_strategy: none`** | B docker_first 일괄 / C hybrid |
| **D6** | ADR-009 amendment 시점 | **A — Phase 2 entry 안에서 지금** | B post-Epic 별도 / C 무한 defer |
| **D7** | Pilot/Epic issue 등록 | **A — 둘 다 retroactive 등록** | B Epic only / C skip |
| **D8** | Epic title | **"mctrader Docker-first Migration"** | "mctrader Containerization" / "mctrader Dockerization" |

### §2.3 Out-of-scope (Phase 3+ 후속)

- mctrader-engine Docker-first impl (Phase 3 — 별도 spec/plan)
- mctrader-web multi-service compose impl (Phase 4 — 별도 spec/plan)
- market + bithumb + hub `infra_strategy: none` 일괄 batch (Phase 5 — joint)
- Bithumb WS schema fix 본 fix 작업 (mctrader-market-bithumb 별도 Story, Phase 5 의 bithumb sister rollout blocker)
- ghcr.io publish workflow + multi-arch + trivy image-ref scan (Pilot Out-of-scope F1-F3 그대로 carry-over)
- EPIC-RESULTS-MCT-98 final retrospection (Phase 6, Epic close)

## §3. 도입할 설계

### §3.1 Architecture overview

본 Phase 는 doc + issue 만 변경. code change 0. 산출:
- mctrader-hub `docs/stories/MCT-98.md` (Epic Story file 신설) — 6 phase 분해, child Story link, AC, retrospection placeholder
- mctrader-hub `docs/stories/MCT-99.md` (Pilot Story file 신설) — Pilot done 박제, §11 회고 (Phase 2+ entry 조건 + 5 sister 분석 + Bithumb leftover finding link)
- mctrader-hub `docs/adr/ADR-009-ohlcv-schema.md` (수정) — Amendment §X 신설 (named volume `mctrader_data` 영속화 + forward-only invariant + DR backup recipe)
- mctrader-hub GitHub issue MCT-98 (Epic 등록)
- mctrader-hub GitHub issue MCT-99 (Pilot Story 등록, retroactive)
- mctrader-market-bithumb GitHub issue #1 (WS schema finding)

### §3.2 Components (artifact 단위 변경)

#### 신규 파일 (mctrader-hub)

| 파일 | 책임 | 상세 |
|---|---|---|
| `docs/stories/MCT-98.md` | Epic Story — mctrader Docker-first Migration | mctrader-hub Story format (`## 1.` ~ `## 11.` 번호 section, MCT-97 reference), Phase 1-6 분해, child Story (MCT-99 + Phase 3-5 candidate key) link, AC (B1-B5), Out-of-scope, retrospection placeholder |
| `docs/stories/MCT-99.md` | Pilot Story (retroactive) — mctrader-data Docker-first Containerization (Pilot, P1) | 동일 numbered section format, §8 Implementation Manifest (mctrader-data PR #11 8 commit reference), §9 Evidence (186 pytest pass, hadolint clean), §11 회고 (Phase 2+ entry 조건 + 5 sister shape 분석 + Bithumb leftover finding link) |

#### 수정 파일 (mctrader-hub)

| 파일 | 변경 |
|---|---|
| `docs/adr/ADR-009-ohlcv-schema.md` | Amendment §D12 (Docker-first persistence) — 기존 Amendment History 패턴 (2026-05-04 §D10/D11, 2026-05-05 §D2.1/D10.7/D11.8) 확장. 2026-05-08 entry: named volume `mctrader_data` 영속화 패턴 (codeforge ADR-033 reference) + forward-only invariant 명시 (Bithumb public API has no historical replay for ticks/orderbook) + DR backup recipe (`docker run --rm -v mctrader_data:/source -v $(pwd):/backup ...` snapshot/restore 표준) |

#### 신규 GitHub issue

| Repo | Issue | 책임 |
|---|---|---|
| mctrader-hub | **MCT-98** Epic | Epic body — Phase 1-6 plan, child Story link (MCT-99 P1 done + Phase 3-5 placeholder), trigger ADR-033 link, Codex review 합의 8 결정 reference |
| mctrader-hub | **MCT-99** Pilot Story (retroactive) | Story body — `docs/stories/MCT-99.md` link, mctrader-hub PR #119 + mctrader-data#11 link, Epic #98 parent link, "P1 DONE" badge, Bithumb finding cross-repo link |
| mctrader-market-bithumb | **#1** Bithumb WS schema mismatch | finding body — 2 schema 결함 (orderbookdepth missing symbol ws_mapping.py:90, invalid event_time ws_mapping.py:33), MCT-99 §11 link, "blocks Phase 5 bithumb sister rollout" 명시, expected fix scope (별도 Story) |

### §3.3 Data flow / 작업 순서

#### Build time (single 세션)

1. **GitHub issue 3개 등록**:
   - mctrader-hub: MCT-98 Epic (먼저 — parent first)
   - mctrader-hub: MCT-99 Pilot Story (Epic #98 link 포함)
   - mctrader-market-bithumb: #1 WS finding (MCT-99 link 포함)

2. **mctrader-hub doc PR open**:
   - branch `docs/MCT-98-MCT-99-phase-2-entry` (doc-only PR 패턴, mctrader-hub 선례 정합)
   - commit 분리 (atomic):
     - commit 1: `[MCT-98] docs(story): Epic Story file + Phase 1-6 plan`
     - commit 2: `[MCT-99] docs(story): Pilot Story file + §11 retrospective`
     - commit 3: `[MCT-98] docs(adr): ADR-009 amendment — named volume + forward-only + DR`
   - PR title: `[MCT-98/99] docs: Phase 2 entry — Epic + Pilot Story + ADR-009 amendment`
   - PR body: Pilot 결과 요약, 8 결정 reference, AC checklist, child Story link, Bithumb issue link

3. **Codex 7-area review** (Phase 2 entry doc PR scope, doc-only — 가중치 governance 정합 + ADR amendment correctness + retrospection 완전성)

4. **Sonnet decider 합성** (push-back 항목 fix-back 또는 defer 결정)

5. **phase-gate-mergeable green 후 admin merge** (memory feedback `admin merge autonomy`)

#### Runtime (Phase 2 entry 종료 후 Epic state)

- Epic MCT-98 (#120) OPEN, Phase 1 = DONE, Phase 2 entry = DONE, Phase 3-6 = TODO
- Pilot Story MCT-99 (#121) OPEN (retroactive) — Phase 1 done badge, §11 retrospection complete
- Bithumb finding (mctrader-market-bithumb#4) **CLOSED 2026-05-08** — resolved by PR #3 inline fix + integration smoke verification (post-discovery during Phase 2 entry execution; original spec assumed open-and-blocking, actual state = pre-satisfied)
- ADR-009 amended — sister rollout 들이 named volume + forward-only + DR pattern reference

### §3.4 Phase 2 entry 종료 후 Phase 3+ 진입 조건

| Phase | Entry 조건 | Story key 후보 |
|---|---|---|
| **Phase 3** (mctrader-engine) | Phase 2 entry merged + ADR-009 amendment land | MCT-100 |
| **Phase 4** (mctrader-web) | Phase 3 종료 + engine reference 박제 + retrospection | MCT-101 |
| **Phase 5** (library batch joint: market + bithumb + hub) | Phase 4 종료 + bithumb finding fixed (#1 close) | MCT-102 (joint), 또는 3 sub-Story (MCT-102/103/104) |
| **Phase 6** (Epic close) | Phase 5 종료 + 6 repo 모두 codeforge `check-container-strategy.sh` PASS | EPIC-RESULTS-MCT-98.md |

## §4. Acceptance Criteria

### §4.1 Phase 2 entry 본 PR

| ID | AC | 검증 |
|---|---|---|
| **B1** | Epic Story file MCT-98 작성 + Phase 1-6 plan + child link 5개 (MCT-99 + Phase 3-5 placeholder) | `docs/stories/MCT-98.md` 존재 + grep "Phase 1\|Phase 2\|Phase 3\|Phase 4\|Phase 5\|Phase 6" |
| **B2** | Pilot Story file MCT-99 작성 + §11 회고 완성 (Pilot 성과 + Phase 2+ 조건 + 5 sister shape 분석 + Bithumb finding link) | `docs/stories/MCT-99.md` 존재 + §11 section 확인 |
| **B3** | ADR-009 amendment §X 추가 (named volume + forward-only + DR backup recipe) | `docs/adr/ADR-009-ohlcv-schema.md` diff 확인 |
| **B4** | mctrader-hub Epic issue MCT-98 OPEN + body 에 Phase 1-6 plan | `gh issue view 120 --repo mclayer/mctrader-hub` |
| **B5** | mctrader-hub Pilot Story issue MCT-99 OPEN + retroactive close 가능 표시 (Phase 1 DONE) | `gh issue view 121 --repo mclayer/mctrader-hub` |
| **B6** | mctrader-market-bithumb issue #1 OPEN + 2 schema finding 명시 + MCT-99 link + 본문/title 에 "blocks Phase 5 bithumb rollout" marker (codeforge label 미bootstrap 상태 — label 의존 없이 본문 marker 로 충분) | `gh issue view 1 --repo mclayer/mctrader-market-bithumb` |
| **B7** | mctrader-hub doc PR phase-gate-mergeable green | `gh pr checks` |
| **B8** | Codex 7-area review push-back 모두 fix-back 또는 deferred 명시 | review 응답 + Sonnet decider 합성 commit |

### §4.2 (out-of-scope, Phase 3+ entry 시 검증)

- C1: mctrader-engine Phase 3 spec/plan 작성 (별도 brainstorming session)
- C2: mctrader-web Phase 4 spec/plan 작성
- C3: library batch Phase 5 joint spec/plan 작성 (3 repo `infra_strategy: none` 일괄)
- C4: bithumb finding fix Story (Phase 5 의 bithumb sister rollout blocker 해소)

## §5. Threat Model / Risk

본 Phase = doc only, code change 0 → security threat 부재. governance risk 만 분석.

| Risk | 영향 | 완화 |
|---|---|---|
| Story key collision (MCT-98 / MCT-99 — 본 conversation 외부에서 점유 가능성 낮으나) | issue 등록 fail | 등록 시 `gh issue list --repo mclayer/mctrader-hub --state all --search "MCT-98 in:title"` 로 확인, 충돌 시 next available 로 shift + spec/Story file rename |
| mctrader-market-bithumb codeforge label 부재 | label 기반 filter / Phase 5 blocker tracking 약 | issue 본문 + title 에 explicit marker ("blocks Phase 5 bithumb rollout"), Phase 5 entry 시 codeforge `bootstrap-labels.sh` 실행 후 label 부착 |
| ADR-009 amendment scope creep | review 부피 증가 | amendment 범위 = named volume + forward-only + DR 3 항목 strict 한정, 다른 schema 변경 거절 |
| Bithumb finding 의 cross-repo link 깨짐 | Phase 5 entry 시 blocker tracking 실패 | issue body 에 explicit URL link + label `blocks-phase-5-rollout` |
| Pilot retroactive 등록 vs 신규 Story 패턴 충돌 | reviewer 혼동 | MCT-99 Story file 의 §0 메타에 "retroactive 등록 (PR #119 + mctrader-data#11 이미 merged)" 명시 |
| 5 sister shape 분석 정확도 부족 | Phase 3-5 spec 진입 시 재분석 필요 | §11 회고에 5 sister 별 surface 분석 (deploy artifact / runtime / dependency) detail 박제 |

## §6. Tech / Dependency

- mctrader-hub doc PR — codeforge consumer phase-gate-mergeable workflow
- ADR-009 = mctrader-hub `docs/adr/ADR-009-ohlcv-schema.md` (mctrader-data ADR set 의 일부, 파일 자체는 governance hub 에 보관)
- Pilot 결과 reference — mctrader-data PR #11 (already merged, no further code change)
- Codex review = `codex:codex-rescue` agent (7-area review per phase, memory feedback `phase_codex_review_loop` 정합)
- 외부 의존 — codeforge plugin ADR-033 (carrier_story CFP-128, 2026-05-07 Accepted)

## §7. Operational

### §7.1 mctrader-hub PR open

```powershell
cd c:\workspace\mclayer\mctrader-hub
git checkout main
git pull origin main
git checkout -b docs/MCT-98-MCT-99-phase-2-entry
```

### §7.2 commit 분할

각 commit atomic — 1 artifact 1 commit.

### §7.3 Rollback (만약 phase-gate-mergeable fail)

- doc-only PR, code change 0 → rollback impact 0
- issue 등록 (Epic + Pilot Story + Bithumb finding) 은 PR 와 독립 — PR fail 해도 issue 유지 가능
- ADR-009 amendment 만 fail 시 revert 단순 (file 복구)

### §7.4 OpRiskArch (codeforge ADR-033 §7.4 정합)

본 Phase = doc only — restart policy / volume DR / health check / network mode 모두 N/A. Pilot 의 박제 패턴 reference (mctrader-data compose.yml) → ADR-009 amendment 가 sister rollout 들에 forward.

## §8. mctrader-hub Epic governance 후속

### §8.1 Epic close 조건 (Phase 6)

- 6 repo (1 hub + 5 sister) 모두 `.claude/_overlay/project.yaml` 에 `infra_strategy:` 명시 (docker_first or none)
- 2 repo (data, engine) 또는 3 repo (data, engine, web) Docker artifact 보유 + healthcheck pattern 박제
- 3 repo (market, bithumb, hub) `infra_strategy: none` lint pass
- `mctrader-market-bithumb#4` (WS finding) **이미 CLOSED 2026-05-08** (resolved by PR #3 + integration smoke verification, Phase 5 entry pre-satisfied)
- EPIC-RESULTS-MCT-98.md 작성 (회고 + 6 phase 결과 요약 + cross-cutting finding + 후속 ADR 후보)

### §8.2 EPIC-RESULTS file 위치

mctrader-hub root level (`EPIC-RESULTS-MCT-98.md`) — 기존 패턴 (`EPIC-RESULTS-MCT-90.md`, `EPIC-RESULTS-MCT-97.md` 동일 위치).

## §9. Future work / Open questions

| ID | 항목 | 처리 방향 |
|---|---|---|
| F1 | Phase 3 (mctrader-engine) spec/plan | 본 Phase 종료 후 별도 brainstorming session |
| F2 | Phase 4 (mctrader-web) multi-service compose 패턴 | Phase 3 reference 박제 후 |
| F3 | Phase 5 library batch joint spec | CFP-96 Phase 6b 패턴 (5 sister 일괄) 참조 |
| F4 | Bithumb WS schema fix Story | mctrader-market-bithumb 별도 Story, Phase 5 bithumb sister entry blocker |
| F5 | ADR-009 amendment 의 backup cron 자동화 (volume snapshot scheduled) | Phase 6 또는 별도 ops Story |
| F6 | ghcr.io publish workflow + multi-arch + trivy (Pilot F1-F3 carry-over) | Epic 외 별도 후속 |
| O1 | Phase 5 library batch 의 single Story vs 3 sub-Story | Phase 5 entry 시 결정 |
| O2 | Phase 4 (web) multi-service compose 의 sqlite volume DR 분리 vs 통합 | Phase 4 entry 시 결정 |

## §10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| Phase 2 scope | C 4 artifact 묶음 | A retro only — engineering state 와 governance 격차 유지 / B retro+Bithumb — Epic registration 누락, ADR amendment defer 위험 / D + first sister start — review 부피 폭증, Phase 분리 명료성 약화 |
| Sequencing | C Hybrid by shape | Mode A serial — library/governance 5 phase 소진 ROI 0 / Mode B 5-parallel — shape 다양성으로 review 정합성 약 |
| First sister | engine | web — multi-service novel pattern, Pilot reference 약 / library batch first — deployable runtime 경험 박제 약 |
| Bithumb handling | B issue + blocker | A defer-only — Phase 5 진입 시 healthy signal 부정직 / C inline fix — Epic scope creep, containerization 본질 흐림 |
| infra_strategy 일관성 | A library = none | B 일괄 docker_first — fake infra ownership ROI 0 / C hybrid (hub만 docker_first) — 일관성 약 |
| ADR-009 amendment 시점 | A 지금 | B post-Epic — sister 들이 패턴 invent 위험 / C defer — DR 어휘 tribal knowledge 화 |
| 등록 mechanic | A 둘 다 retroactive | B Epic only — Pilot Story 박제 누락, retrospection anchor 부재 / C skip — governance trace 단절 |
| Epic 명칭 | "Docker-first Migration" | "Containerization" — 모호 / "Dockerization" — 비공식 어휘 |

## §11. 참고 / 관련 파일

### Pilot reference (이미 merged)
- mctrader-hub PR #119 — `docs(spec/plan): mctrader-data Docker-first Pilot design + plan + Amendment 1`
- mctrader-data PR #11 — `feat: Docker-first containerization Pilot (CFP-128/ADR-033)`
- mctrader-hub `docs/superpowers/specs/2026-05-07-mctrader-data-docker-pilot-design.md`
- mctrader-hub `docs/superpowers/plans/2026-05-07-mctrader-data-docker-pilot-plan.md`

### codeforge (외부 의존, mclayer/plugin-codeforge)
- `docs/adr/ADR-033-docker-first-infra-engineering.md` — Pilot trigger ADR
- `templates/github-workflows/container-image-scan.yml` — hadolint reusable workflow
- `scripts/check-container-strategy.sh` — consumer lint (sister rollout PASS 의무)
- carrier_story CFP-128 (2026-05-07 Accepted)

### mctrader-hub governance
- `docs/adr/ADR-009-ohlcv-schema.md` (수정 대상)
- `docs/stories/MCT-97.md` (가장 최근 Story, format 참조)
- `EPIC-RESULTS-MCT-97.md` (가장 최근 EPIC-RESULTS, format 참조)

### Codex review trace
- agentId `af61a4c87e9d7906c` (8 결정 + top 5 risk + 7 sequencing nit)

---

**Status**: brainstorming 완료, design spec drafted. user review gate 대기 → writing-plans skill 으로 transition 예정.
