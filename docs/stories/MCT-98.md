---
story_key: MCT-98
story_issues:
  - repo: mclayer/mctrader-hub
    number: 120
status: phase:2-entry
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

### 8.3-8.6 Phase 3-6 (TBD)

각 phase merge 시 commit hash + PR # 추가.

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

## 11. 회고

본 §11 은 Phase 6 (Epic close) 시점에 박제. 항목:

- 6 phase 별 실제 vs 계획 시간 비교
- Hybrid by shape sequencing 의 ROI 실측
- Pilot reference 가 sister rollout 들에 얼마나 reuse 됐는지
- ADR-009 §D12 amendment 의 5 sister 적용 정합성
- Phase 2 entry 의 Bithumb verification (PR #3 fix + smoke pass) 가 Phase 5 entry 단순화에 미친 영향
- 후속 ADR 후보 (Phase 6 cross-cutting finding 정리)

(Phase 2 entry 시점 placeholder — Phase 6 시 보강.)
