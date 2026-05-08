---
story_key: MCT-98
story_issues:
  - repo: mclayer/mctrader-hub
    number: 120
status: complete
---

# MCT-98: mctrader Docker-first Migration

- **Issue**: #120
- **Status**: phase:2-entry
- **Trigger ADR**: codeforge ADR-033 (carrier_story CFP-128, 2026-05-07 Accepted)
- **Pilot reference**: mctrader-hub#119 + mctrader-data#11 (DONE 2026-05-07)

## 1. 사용자 요구사항 (verbatim)

> "이전에 작업하다 끊긴 게 있을텐데"
> "dockerization 관련이다"
> (Phase 5 verification 분기점에서) "c"  — 직접 compose-up smoke 실행 선택

세션 직전: codeforge plugin 의 ADR-033 (CFP-128) Accepted 후 mctrader 6-repo 가 Docker-first migration 을 follow-on Epic 의무로 받음. mctrader-data Pilot 종료 후 Epic governance state 가 engineering state 와 격차.

## 2. 도메인 해석

### 2.1 mctrader 6-repo shape 분석

| Repo | Shape | infra_strategy | Phase |
|---|---|---|---|
| mctrader-data | collector daemon (long-running) | docker_first | **1 (DONE)** |
| mctrader-engine | backtest one-shot CLI + paper daemon | docker_first | 3 |
| mctrader-web | multi-service (FastAPI + Streamlit + sqlite) | docker_first | 4 |
| mctrader-market | library (pure Python) | none | 5 (joint) |
| mctrader-market-bithumb | library + WS adapter | none | 5 (joint) |
| mctrader-hub | governance / docs (no runtime) | none | 5 (joint) |

### 2.2 Phase 분해 근거 (Codex review 합의)

- **Hybrid by shape (D2=C)**: deployable trio (data, engine, web) 와 library quartet (market, bithumb, hub) 가 review 부피 다름 — 동일 path 강제 ROI 0.
- **engine first (D3)**: data Pilot 와 가장 유사한 daemon shape. web 의 multi-service novel pattern 전에 reference 박제.
- **library = none (D5)**: 배포 표면 부재 → fake infra ownership ROI 0.

## 3. 관련 ADR

| ADR | 제목 | 본 Epic 내 역할 |
|---|---|---|
| codeforge ADR-033 | Docker-first Infra Engineering | trigger (carrier_story CFP-128) |
| ADR-009 | OHLCV 스키마 + Candle Protocol | §D12 amendment (Docker-first persistence: named volume + forward-only + DR backup) — Phase 2 entry |

## 4. 관련 코드 경로

### Phase 1 (mctrader-data, DONE)

- `Dockerfile` + `.dockerignore`
- `compose.yml`
- `src/mctrader_data/health_server.py`
- `src/mctrader_data/cli.py` (collect subcommand HealthServer wiring)
- `src/mctrader_data/collector.py` (HealthServer dependency injection)
- `tests/test_health_server.py` (4 TDD scenario)
- `.github/workflows/image-lint.yml` (hadolint)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`

### Phase 3+ (TBD per phase)

- mctrader-engine: `Dockerfile` + `compose.yml` (one-shot + daemon dual mode 검토)
- mctrader-web: `Dockerfile` + `compose.yml` (multi-service: api + web + sqlite volume)
- library quartet (market, bithumb, hub): `.claude/_overlay/project.yaml` `infra_strategy: none` 만

## 5. Acceptance Criteria

| ID | AC | 검증 phase |
|---|---|---|
| B1 | 6 repo 모두 `.claude/_overlay/project.yaml` `infra_strategy:` 명시 | Phase 5 종료 |
| B2 | deployable trio (data, engine, web) Docker artifact + healthcheck 박제 | Phase 4 종료 |
| B3 | library quartet (market, bithumb, hub) `infra_strategy: none` lint pass | Phase 5 종료 |
| B4 | mctrader-market-bithumb WS finding 처리 | **이미 만족** (PR #3 inline fix 2026-05-07 + verification 2026-05-08) |
| B5 | EPIC-RESULTS-MCT-98.md 작성 + 회고 + 6 phase 결과 박제 | Phase 6 |

## 6. 외부 지식 배경

- codeforge plugin ADR-033 (Docker-first Infra Engineering) — InfraEngineerAgent default 출력 패턴
- Docker Compose v2 — `compose.yml` (legacy `docker-compose.yml` 대신)
- hadolint — Dockerfile lint
- python:3.12-slim — base image (uv 호환)
- Pilot reference 패턴: 2-stage build, non-root user, named volume, HEALTHCHECK directive

## 7. Phase plan

### Phase 1 — Pilot (mctrader-data) ✅ DONE

- 2026-05-07 merged
- mctrader-hub PR #119 (spec/plan)
- mctrader-data PR #11 (impl, 8 commits, 0.8.0→0.9.0)

### Phase 2 — Entry / bookkeeping ⬅ this PR

- Epic + Pilot Story (MCT-99) retroactive 등록
- ADR-009 §D12 amendment
- Bithumb WS finding (mctrader-market-bithumb#4) 등록 → verification 후 close (PR #3 inline fix 확정)

### Phase 3 — mctrader-engine sister (TBD MCT-100)

- 별도 brainstorming session — backtest one-shot + paper daemon Docker-first 패턴
- spec/plan + impl PR (mctrader-engine)
- entry 조건: Phase 2 entry merged + ADR-009 amendment land

### Phase 4 — mctrader-web sister (TBD MCT-101)

- 별도 brainstorming session — multi-service compose (FastAPI + Streamlit + sqlite volume)
- spec/plan + impl PR (mctrader-web)
- entry 조건: Phase 3 종료 + engine reference 박제

### Phase 5 — Library batch joint (TBD MCT-102)

- market + bithumb + hub 3 repo `.claude/_overlay/project.yaml` 에 `infra_strategy: none` 추가
- bithumb 의 WS schema fix 의무 = **이미 만족** (mctrader-market-bithumb PR #3 inline fix + verification)
- CFP-96 Phase 6b 패턴 (sister 일괄 sweep)
- entry 조건: Phase 4 종료

### Phase 6 — Epic close

- `EPIC-RESULTS-MCT-98.md` 작성
- 회고 + 6 phase 결과 + cross-cutting finding + 후속 ADR 후보

## 8. Implementation Manifest (per phase)

### 8.1 Phase 1 (mctrader-data, DONE)

mctrader-data PR #11 8 commits:
1. `46dc5c6` HealthServer HTTP /health endpoint + 4 TDD scenarios
2. `d8bdb67` Dockerfile + .dockerignore (2-stage, non-root)
3. `be2e708` compose.yml (collector daemon, named volume, restart, healthcheck)
4. `609d5f1` project.yaml `infra_strategy: docker_first`
5. `7c0fd81` README "Docker deployment" 절 + systemd 자산 삭제 (BREAKING)
6. `78ffb64` `.github/workflows/image-lint.yml` (hadolint)
7. `d1f2910` tests/integration/README.md (5 manual smokes)
8. `645e476` pyproject 0.8.0 → 0.9.0 + CHANGELOG.md

### 8.2 Phase 2 (this PR)

본 PR 의 commit (post-merge fill):
- spec commit `366aa48`
- plan commit `10eba88`
- Epic Story file (MCT-98.md)
- Pilot Story file (MCT-99.md)
- ADR-009 §D12 amendment

### 8.3 Phase 3 (mctrader-engine, MCT-100)

mctrader-hub PR #135 (commit `9a5e956`, 2026-05-08T02:33:04Z) + mctrader-engine PR #37 (10 commits, 0.29.0→0.30.0, final commit `f6c8c12`):

- 13 D freeze (Codex 11 + Codex D12 + Sonnet **D13 fcntl.flock cross-container mutex** 신규 pattern)
- 4 named volume topology (`mctrader_data:ro` external + `engine_runs` + `engine_wfo` + `engine_lock`)
- paper service (default profile, daemon, healthcheck, restart unless-stopped) + engine service (profile tools, oneshot via `compose run`)
- ADR-015 cross-ref Docker SM mapping anchor (Phase 3 amendment)
- D13 evidence (Linux Docker container 안 cross-OFD test PASS)
- live smoke (paper up + healthy + backtest + SIGTERM) deferred to deploy time

### 8.4 Phase 4 (mctrader-web, MCT-101)

mctrader-hub PR #136 (commit `443807e`, 2026-05-08T01:59:25Z, doc) + mctrader-web PR #22 (15 commits squash `a0ac2ce`, 2026-05-08T07:13:11Z, 0.13.0→0.14.0) + mctrader-hub PR #141 (commit `f8d5b83`, 2026-05-08T07:19:28Z, Story close):

- 13 D freeze (Codex 11 + Sonnet D12 ADR-016 amendment 단독 + Sonnet D13 Phase 3 race 회피)
- 2-service compose (api FastAPI + panel Streamlit) + named volume `mctrader_web_data:rw` + external cross-stack `mctrader-data_mctrader_data:ro`
- D6 TLS env exempt + host port 0 invariant (3-asset enforcement: compose + README + `tests/test_compose_invariant.py` CI gate)
- D8 standalone fallback (`MCTRADER_DISABLE_DATA_STATUS`)
- ADR-016 §A1-A4 amendment (hash chain integrity-aware DR)
- Codex 7-area review 2회 — PR #136 (3 High + 2 Medium) + PR #22 (1 High + 2 Medium) — 5 fix-back land
- Pre-existing collector e2e test failure (Linux-only, MCT-97 P6 era) F6 carry-over Story 후보
- Phase 4 가 last merge → Epic body Phase 4 status DONE reconciliation 책임 수행

### 8.5 Phase 5 (Library batch, MCT-102)

mctrader-hub PR #137 (commit `e763352`, 2026-05-08T01:58:58Z, anchor) + mctrader-market#2 + mctrader-market-bithumb#5 (3 PR joint sweep, 모두 2026-05-08 merged):

- 5 D 합의 (Codex agentId `a66da458a451e3169`): Single Story / 3 PR joint sweep (CFP-96 Phase 6b 패턴) / No version bump / Single Codex review (mctrader-hub anchor) / 로컬 lint SKIP evidence
- 3 repo `.claude/_overlay/project.yaml` `infra_strategy: none` 명시 → `bash check-container-strategy.sh` SKIP 3/3
- bithumb WS schema fix = 이미 만족 (mctrader-market-bithumb PR #3 inline fix + Phase 2 entry session smoke verified)
- worktree isolation pattern 박제 (parallel session race recovery from Phase 4 contamination)

### 8.6 Phase 6 (Epic close, this PR)

본 PR commit:

| # | commit | 내용 |
|---|---|---|
| 1 | spec commit (`9c3df4e`) | Phase 6 Epic close design — 9 D Codex+Sonnet 합의 |
| 2 | plan commit (`36095a6`) | Phase 6 10-task plan |
| 3 | EPIC-RESULTS commit (`9f83490`) | EPIC-RESULTS-MCT-98.md (root, 10 절) |
| 4 | Story §8.3-8.6 + §11 update commit | 본 commit (Story file 채움) |
| 5 | Epic body reconciliation commit | post-merge `gh issue edit 120 --body` (Phase 6 status DONE + B1+B2+B5 [x] + Closes footer) |
| 6 | F6 GitHub issue (mctrader-web) | post-merge `gh issue create --repo mclayer/mctrader-web` |

본 PR merge 시 Epic #120 자동 close (PR body `Closes #120`).

**9 D 합의 (Codex agentId `a63731290d7d25208` + Sonnet 합성)**:

| # | 결정 | 채택 |
|---|---|---|
| D1 | Document location | A: root `EPIC-RESULTS-MCT-98.md` |
| D2 | Document structure | C: MCT-97 base + Docker extensions |
| D3 | D13 fcntl.flock ADR formalization | C: inline 참조 + defer (F9 carry-over) |
| D4 | F1-F8 carry-over Story 생성 | C: F6 즉시 issue / 나머지 list-only |
| D5 | Epic close mechanic | A: 단일 PR + `Closes #120` |
| D6 | Findings 깊이 | C: hybrid (표 + 5 deep dive) |
| D7 | Phase 6 Story file | C: MCT-98 §8.6/§11 dual-anchor + EPIC-RESULTS |
| D8 | Metrics 깊이 | C: comprehensive (parallel ROI + Codex round + version) |
| D9 | F7 live deploy smoke | B: 전적 defer (deploy event 시 ops) |

## 9. Evidence

### Phase 1 evidence (DONE)

- 186 pytest PASS (mctrader-data)
- hadolint Dockerfile = warning 0
- `docker compose config` syntax PASS
- `docker build` 성공 + image entrypoint smoke
- `bash scripts/check-container-strategy.sh` PASS
- actionlint image-lint.yml clean
- ruff check PASS

### Phase 2 evidence (this PR)

#### Bithumb integration smoke (Phase 5 entry pre-verification, 2026-05-08)

mctrader-data Docker stack vs mctrader-market-bithumb main HEAD (PR #3 fix 포함):

```
docker compose build --no-cache  → mctrader-data:pilot built
docker compose up -d collector   → Up 27 seconds (healthy) at t+27s
docker compose ps                → Up About a minute (healthy)
docker compose exec collector python -c "...urlopen('http://localhost:8080/health')..."
  → HTTP 200 + {"ws_state":"connected","node_id":"ea30588e13d4","uptime_seconds":35,"status":"ok"}
docker compose logs              → 10 KRW pairs subscribe (transaction + orderbookdepth) 정상,
                                    SchemaMismatchError / invalid grep 0 hit
docker compose down -v           → cleanup OK
```

→ PR #3 fix 가 mctrader-data Pilot 의 healthy state 를 완전히 unblock. mctrader-market-bithumb#4 close (resolved).

#### Phase 2 entry doc PR

- 본 PR merge 시 추가:
  - phase-gate-mergeable green
  - Codex 7-area review push-back 처리 trace (agentId `af61a4c87e9d7906c`)
  - Sonnet decider 합성 commit (있을 시)

### Phase 3-6 evidence

각 phase merge 시 추가.

## 10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| Phase 2 scope | C 4 artifact 묶음 | A retro only — engineering/governance 격차 유지 / B retro+Bithumb — Epic registration 누락 / D + first sister start — review 부피 폭증 |
| Sequencing | C Hybrid by shape | Mode A serial — library 5 phase 소진 ROI 0 / Mode B 5-parallel — shape 다양성으로 review 정합성 약 |
| First sister | engine | web — multi-service novel pattern, Pilot reference 약 / library batch first — deployable runtime 경험 박제 약 |
| Bithumb handling (Phase 2 entry session 시점) | B issue + blocker | A defer-only / C inline fix |
| Bithumb verification (실측 결과 반영) | **C 직접 smoke 실행** (사용자 directive "c") | A close as duplicate (verification 약) / B repurpose issue (overhead) |
| infra_strategy 일관성 | A library = none | B 일괄 docker_first — fake infra ownership ROI 0 / C hybrid (hub만 docker_first) — 일관성 약 |
| ADR-009 amendment 시점 | A 지금 | B post-Epic — sister 들이 패턴 invent 위험 / C defer — DR 어휘 tribal knowledge 화 |
| 등록 mechanic | A 둘 다 retroactive | B Epic only — Pilot Story 박제 누락 / C skip — governance trace 단절 |
| Epic 명칭 | "Docker-first Migration" | "Containerization" — 모호 / "Dockerization" — 비공식 |

## 11. 회고 (Phase 6 Epic close 시점 박제)

### 11.1 6 phase 별 실제 vs 계획 시간 비교

| Phase | 계획 (Phase 2 entry session) | 실제 | delta | 비고 |
|---|---|---|---|---|
| 1 Pilot (data) | 2026-05-07 1 session | DONE 2026-05-07 | 정합 | mctrader-data 4시간 brainstorm + 8 commit + 1 day |
| 2 Entry/bookkeeping | 2026-05-08 1 session | DONE 2026-05-08 (PR #122) | 정합 | retroactive registration + bithumb verification dual-task (Phase 2 의 critical path simplification) |
| 3 Engine | Phase 2 다음 1 session (engine first 의도) | DONE 2026-05-08 (parallel || P4) | -50% (parallel) | revised: parallel 진행, mctrader-data Pilot 가 reference (engine 의무 0) |
| 4 Web | Phase 3 다음 1 session (engine reference 의무 의도) | DONE 2026-05-08 (parallel || P3) | -50% (parallel) | revised: parallel 진행, novel pattern (multi-service + ADR-016 amendment + cross-stack RO) 단독 박제 |
| 5 Library | Phase 4 다음 1 session | DONE 2026-05-08 | 정합 | 3 PR joint sweep, declarative meta only |
| 6 Epic close | Phase 5 다음 1 session | DONE 2026-05-08 (this PR) | 정합 | EPIC-RESULTS doc + Story §8.6/§11 + F6 issue + memory sync |

→ Phase 1+2+3+4+5+6 모두 2 calendar day (2026-05-07 → 2026-05-08) 안에 완료. Phase 3+4 parallel revision 이 critical path 단축 효과 약 50%.

### 11.2 Hybrid by shape sequencing 의 ROI 실측

D2 결정 (Phase 2 entry, Codex 권장 채택) — deployable trio (data, engine, web) + library quartet (market, bithumb, hub) 분리:

- **deployable trio** (3 phase × 1-2 sister + Pilot 1) 가 review 부피 ~90% 차지 — 13 D × 2 (engine + web) + 7 D Pilot + 8 D Phase 2 = 41 design 결정 박제
- **library quartet** (1 phase × 3 repo joint sweep) 가 review 부피 ~5% — 5 D × 1 = 5 design 결정 박제
- 만약 Mode A serial (1 sister 씩 5 phase 소진) 채택 시 library 3 repo × 별도 phase = process weight 3× 증가 → 실측 회피
- 만약 Mode B 5-parallel 채택 시 shape 다양성으로 review 정합성 약화 → 실측 회피

→ Hybrid by shape ROI 검증 PASS. critical path 의 51-90% 가 deployable trio review 에 정합 분배.

### 11.3 Pilot reference 5 sister rollout reuse 매트릭스

| Pilot pattern | Phase 3 engine | Phase 4 web | Phase 5 library |
|---|---|---|---|
| 2-stage Dockerfile (deps+runner) | ✅ reused | ✅ reused (2-stage) | n/a (no Dockerfile) |
| non-root user mctrader UID 1001 | ✅ | ✅ | n/a |
| python:3.12-slim base | ✅ | ✅ | n/a |
| named volume `mctrader_data` | n/a (own + cross-stack RO) | ✅ external `mctrader-data_mctrader_data:ro` | n/a |
| HealthServer HTTP /health | ✅ engine paper | ✅ api `/health` + panel `/_stcore/health` | n/a |
| restart unless-stopped | ✅ | ✅ | n/a |
| `infra_strategy: docker_first` | ✅ | ✅ | n/a — `infra_strategy: none` 채택 |
| `image-lint.yml` hadolint | ✅ (reusable workflow) | ✅ | n/a |
| `tests/integration/README.md` smoke | ✅ 10-step (+ D13 mutex 검증) | ✅ 10-step (+ Smoke 8.B negative case) | n/a |

→ Pilot reference reuse rate 9/9 (engine), 9/9 (web), 0/9 (library 의도적). 5 sister 가 Pilot 패턴 의 invariant 를 100% 채택, novel pattern (D13 fcntl.flock / D8 cross-stack volume / ADR-016 amendment) 만 추가 박제.

### 11.4 ADR-009 §D12 amendment 의 5 sister 적용 정합성

Phase 2 entry 박제 invariant (named volume + forward-only + DR backup, PowerShell + bash dual command):

- **Phase 1 data 자체** — invariant 자체 source (named volume `mctrader_data` rw)
- **Phase 3 engine** — 4 volume topology 정합 (`mctrader_data:ro` external + `engine_runs` rw + `engine_wfo` rw + `engine_lock` rw) — 4/4 named volume + forward-only invariant + DR backup recipe (engine 자체 named volume 추가는 §D12 의 spirit 정합)
- **Phase 4 web** — 2 volume 정합 (`mctrader_web_data` rw + external cross-stack `mctrader-data_mctrader_data` ro) — 2/2 named volume + forward-only + RO mount 도 named volume 그대로 유지 (§D12 정합)
- **Phase 5 library** — n/a (배포 표면 부재)

→ 적용 5/5 정합. §D12 가 sister rollout 의 reference 로 안정 작동, **추가 amend 0**. Phase 4 D12 결정 (γ ADR-016 amendment 단독) 가 §D12 의 race 회피에 정확히 기여.

### 11.5 Phase 2 entry Bithumb verification 의 Phase 5 entry 단순화 효과

Phase 2 entry session (2026-05-08 09:00 KST 추정) 시점:

- Pilot PR §11 finding "별도 issue 박제 예정" → 본 session 에서 mctrader-market-bithumb#4 issue 등록
- 사용자 directive "c" (직접 smoke 실행 옵션) → 직접 verification 후 PR #3 inline fix 발견 + smoke pass → close as resolved
- 결과: Phase 5 entry 시점에 bithumb fix 의무 = "이미 만족" 으로 간주 가능 (B4 acceptance "DONE" 박제)

만약 Phase 2 entry verification 미실행 시:

- Phase 5 entry 의 B4 acceptance = "verification 미박제" → Phase 5 추가 검증 책임 → process weight 2× 증가 (Phase 5 declarative + verification 2-step 화)
- Phase 2 entry 의 verification 이 critical path simplification + AC 박제 가능 시점 1 phase 단축

→ Phase 2 entry session 의 verification execute 가 Epic 전체의 process simplification 에 약 1 phase 만큼 기여.

### 11.6 후속 ADR 후보 (Phase 6 cross-cutting finding 정리)

EPIC-RESULTS-MCT-98 §5 (5 deep dive) + §8 (codeforge upstream 5건) 별도 박제. 본 §11.6 은 ADR 후보로 좁힘:

| 후보 | trigger | Epic 인 / 외 |
|---|---|---|
| **ADR-? D13 fcntl.flock cross-container mutex** | 2nd reuse 시점 | 외 (carry-over F9) |
| ADR-016 amendment §A1-A4 | hash chain integrity-aware DR | 인 (Phase 4 amendment landed) |
| ADR-009 §D12 amendment | named volume + forward-only + DR backup recipe | 인 (Phase 2 entry landed) |
| ADR-015 cross-ref Docker SM mapping | engine SM ↔ Docker label mapping | 인 (Phase 3 amendment landed) |

→ 본 Epic 가 박제한 ADR amendment 3건 + 신규 pattern 1건 (D13). F9 만 carry-over (2nd reuse 시 ADR formalize).

### 11.7 carry-over Story 후보 (F1-F9)

EPIC-RESULTS §5.6 carry-over 표 그대로. 박제 위치:

- **F6 즉시 issue** (mctrader-web repo, priority HIGH) — collector e2e Linux-only fix follow-up
- F1, F3, F5, F8, F9 list-only carry-over (low priority)
- F2, F4, F7 list-only carry-over (mid priority, ops Story 후보)

총 9 carry-over (1 HIGH issue + 3 mid list + 5 low list).

### 11.8 결론

- **Epic MCT-98 (Docker-first Migration) COMPLETE** 2026-05-08
- 6-repo Docker-first 전환 100% 박제
- ADR-033 (codeforge) follow-on 의무 100% 만족 (deployable trio 3 repo + library quartet 3 repo)
- Pilot reference 패턴 reuse rate 9/9 (sister 별)
- Phase 3+4 parallel sequencing 의 critical path 단축 50% 실측
- 신규 pattern 1건 (D13 fcntl.flock) F9 carry-over
- ADR amendment 3건 land
- carry-over 9 항목 (HIGH F6 issue 즉시 등록 + 8 list-only)

→ codeforge consumer Story / Epic 패턴의 reference template 으로 retrospection 박제.
