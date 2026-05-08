---
story_key: MCT-99
story_issues:
  - repo: mclayer/mctrader-hub
    number: 121
status: complete
---

# MCT-99: mctrader-data Docker-first Containerization (Pilot, P1 retroactive)

- **Issue**: #121
- **Status**: complete (Phase 1 DONE 2026-05-07)
- **Parent Epic**: mctrader-hub#120 — mctrader Docker-first Migration
- **Trigger**: codeforge ADR-033 (CFP-128 Accepted 2026-05-07)

> **Retroactive registration**: Pilot 구현 이미 merged. 본 Story file 은 governance anchor + §11 retrospection 박제용.

## 1. 사용자 요구사항 (verbatim, 2026-05-07 Pilot session)

> "codeeforge의 변경에 따라 mctrader에서 작업해야할 내용이 있다. docker containerize에 관한 부분이다."
> "현재 systemd 작업은 수행하고 있지 않으니 편하게 stop해도 된다."

## 2. 도메인 해석

### 2.1 Pilot scope

mctrader-data repo 의 Docker-first 전환. collector daemon 1 service compose. backfill 은 동일 image 의 ad-hoc `compose run` 처리. systemd 자산 일괄 삭제 (production 미가동 확인).

### 2.2 ADR-033 §7.4 OpRiskArch 4 항목 박제 의무

- restart policy
- volume DR
- health check tuning
- network mode

→ 5 sister rollout 의 reference 패턴 만들기.

## 3. 관련 ADR

- codeforge ADR-033 (carrier_story CFP-128) — Pilot trigger
- ADR-009 — OHLCV 스키마 (Pilot §11 회고에서 §D12 amendment 후보 박제 → Phase 2 entry 에서 land)

## 4. 관련 코드 경로 (mctrader-data)

### 신규
- `Dockerfile` (2-stage python:3.12-slim, non-root mctrader UID 1001)
- `.dockerignore` (codeforge cli-tool-minimal 패턴 + `data/` 추가)
- `compose.yml` (collector daemon 1 service, named volume `mctrader_data`, restart unless-stopped, healthcheck)
- `src/mctrader_data/health_server.py` (HTTP /health endpoint, ws_state 기반 200/503)
- `tests/test_health_server.py` (4 TDD scenario)
- `.github/workflows/image-lint.yml` (hadolint job)
- `tests/integration/README.md` (5 manual smoke 절차)

### 수정
- `src/mctrader_data/cli.py` (collect subcommand HealthServer wiring)
- `src/mctrader_data/collector.py` (HealthServer dependency injection)
- `.claude/_overlay/project.yaml` (`infra_strategy: docker_first`)
- `README.md` (systemd 절 → Docker 절 전면 교체)
- `pyproject.toml` (0.8.0 → 0.9.0)
- `CHANGELOG.md` (`[0.9.0]` BREAKING entry)

### 삭제
- `deploy/mctrader-collector.service`
- `deploy/README.md`
- `deploy/` 디렉터리

## 5. Acceptance Criteria (Pilot, met 2026-05-07)

| ID | AC | 결과 |
|---|---|---|
| A1 | Dockerfile 2-stage build + non-root user | ✅ |
| A2 | compose.yml 1 service + named volume + restart + healthcheck | ✅ |
| A3 | HealthServer HTTP /health endpoint (ws_state 200/503) | ✅ (4 TDD test pass) |
| A4 | systemd 자산 삭제 (BREAKING) | ✅ |
| A5 | `infra_strategy: docker_first` lint pass | ✅ (`scripts/check-container-strategy.sh` PASS) |
| A6 | hadolint warning 0 | ✅ |
| A7 | `docker compose config` syntax PASS | ✅ |
| A8 | image entrypoint smoke (--help / collect / backfill / status) | ✅ |
| A9 | 186 pytest PASS (기존 182 + 신규 4) | ✅ |
| A10 | compose-up healthy convergence (live Bithumb WS dependent) | ✅ — Phase 2 entry verification 2026-05-08 (PR #3 inline fix 후) |

## 7. 결정점 (Pilot D1-D7, 모두 사용자 승인)

| Decision | 채택 | 거절 |
|---|---|---|
| D1 응답 경로 | Dockerization Epic 진입 | 방어적 선언 (legacy_systemd) / 단계적 일부 |
| D2 Epic sequencing | Pilot → Rollout (1 + 5) | Mode B Joint Epic / repo-by-repo |
| D3 Pilot 후보 | mctrader-data | mctrader-web / mctrader-engine |
| D4 systemd 처리 | Docker-only 전환 (unit 삭제) | Docker primary + systemd 보존 |
| D5 Compose surface | collector daemon 1 service | + backfill profiles / + cold-archive sidecar |
| D6 Pilot depth | Approach 1 — baseline + lint-only CI | Approach 2 (ghcr publish) / Approach 3 (distroless) |
| D7 Build target | linux/amd64 단일 | Multi-arch buildx |

### Amendment 1 (Pilot session 중)

Task 1 진입 시 기존 `heartbeat.py` 의 HA active-active 패턴 (`<root>/market/manifest/heartbeat-<node_id>.json`, MCT-91/93)이 plan 의 단순 `.heartbeat` mtime 가정과 불일치 발견. 사용자 결정: **HTTP `/health` API endpoint 채택** (webapp-minimal 패턴 정합 + 5 sister rollout reference 강화).

## 8.5 Implementation Manifest (mctrader-data PR #11, 8 commits)

| # | commit | 내용 |
|---|---|---|
| 1 | `46dc5c6` | HealthServer HTTP /health endpoint + TDD 4 시나리오 |
| 2 | `d8bdb67` | Dockerfile + .dockerignore (2-stage, python:3.12-slim, non-root mctrader UID 1001) |
| 3 | `be2e708` | compose.yml (collector daemon, named volume, restart unless-stopped, healthcheck) |
| 4 | `609d5f1` | project.yaml `infra_strategy: docker_first` (codeforge lint PASS) |
| 5 | `7c0fd81` | README "Docker deployment" 절 + systemd 자산 삭제 (BREAKING) |
| 6 | `78ffb64` | `.github/workflows/image-lint.yml` (hadolint) |
| 7 | `d1f2910` | tests/integration/README.md (5 manual smokes) |
| 8 | `645e476` | pyproject 0.8.0 → 0.9.0 + CHANGELOG.md |

## 9. Evidence

### 9.1 Pilot evidence (2026-05-07)

- 186 pytest PASS (기존 182 + 신규 4 test_health_server)
- hadolint Dockerfile = warning 0
- `docker compose config` syntax PASS
- `docker build` 성공 + image entrypoint smoke (--help / collect / backfill / status 모두 노출)
- `bash scripts/check-container-strategy.sh` PASS
- actionlint image-lint.yml clean
- ruff check PASS (health_server.py + 영향받은 file)
- mctrader-data PR #11 admin merge 2026-05-07T07:54:14Z

### 9.2 Bithumb integration verification (2026-05-08, Phase 2 entry session)

Pilot session 시점 healthy-state 미도달 (Bithumb WS schema mismatch). PR #3 inline fix (2026-05-07T12:02:24Z, ~4시간 후) 후 verification 미박제. 본 Phase 2 entry session 에서 직접 smoke 실행:

```
docker compose build --no-cache    → mctrader-data:pilot built (fresh main of bithumb dep)
docker compose up -d collector     → Up 27 seconds (healthy) at t+27s
docker compose ps (1 min later)    → Up About a minute (healthy)
HTTP GET http://localhost:8080/health (from inside container):
  STATUS: 200
  BODY: {"ws_state":"connected","node_id":"ea30588e13d4","uptime_seconds":35,"status":"ok"}
docker compose logs collector:
  - 10 KRW pairs subscribe (transaction + orderbookdepth) 정상
    [KRW-USDT, KRW-B3, KRW-BTC, KRW-D, KRW-ETH, KRW-XRP, KRW-TON, KRW-NIL, KRW-VIRTUAL, KRW-A8]
  - SchemaMismatchError / invalid grep = 0 hit
docker compose down -v             → cleanup OK
```

→ A10 만족 (compose-up healthy convergence). PR #3 fix 가 Pilot Docker stack 의 healthy state 를 완전히 unblock.

## 10. 거절된 대안

(§7 결정점 의 거절 column 참조 — Pilot session 박제 그대로)

## 11. 회고 (Phase 2+ entry 조건 + 5 sister 분석)

### 11.1 Pilot 성과 요약

- ADR-033 §7.4 4 항목 박제 성공:
  - **restart policy**: `unless-stopped` (forward-only, 데이터 누락 회피)
  - **volume DR**: named volume `mctrader_data` + backup recipe (ADR-009 §D12 박제 의무)
  - **health check**: HTTP /health endpoint, interval 30s, start_period 60s, retries 3
  - **network mode**: bridge default, 호스트 port 매핑 0
- HealthServer pattern = 5 sister rollout 의 reference. webapp-minimal 패턴과도 정합.
- BREAKING 변경 (systemd 자산 삭제) 사용자 사전 승인 — production 미가동 검증 후.

### 11.2 Pilot 발견 + 처리 timeline

#### 11.2.1 Bithumb WS schema mismatch — inline fix same-day (PR #3)

Pilot live test (2026-05-07T07:54Z PR #11 merge 직후) 진입 시 mctrader-market-bithumb WS adapter schema 결함 2건:
- `orderbookdepth missing symbol` (`ws_mapping.py:90`)
- `invalid event_time: '2026-05-07 16:38:49.198650'` (`ws_mapping.py:33`)

PR #11 본문 §11 finding "별도 issue 박제 예정" 명시.

**같은 날 inline fix** — mctrader-market-bithumb PR #3 (`fix(ws_mapping): align with live Bithumb envelope (3 bugs)`) 2026-05-07T12:02:24Z merged. PR #3 가 본 finding 의 2 bug + 1 bonus bug (content.datetime lookup) 모두 해결.

본 Phase 2 entry session 시점에 timeline 누락으로 mctrader-market-bithumb#4 issue 등록 → PR #3 fix 발견 → integration smoke verification 후 #4 close (resolved).

#### 11.2.2 ADR-009 §D12 amendment 의무

Pilot 의 named volume + forward-only invariant + DR backup recipe 가 ADR-009 amendment 후보 → Phase 2 entry 에서 land (sister rollout 진입 전 의무).

### 11.3 Phase 2+ entry 조건 (Codex 7-area review agentId `af61a4c87e9d7906c`)

| 결정 | 합의 | 근거 |
|---|---|---|
| D1 carry-over scope | C 4 artifact 묶음 | governance state 가 engineering state 뒤따라야 |
| D2 sequencing | C Hybrid by shape | deployable trio + library quartet 분리, review 부피 정합 |
| D3 first sister | engine | data Pilot 와 가장 유사한 daemon shape |
| D4 Bithumb 처리 (initial) | B issue + blocker | WS schema = correctness, containerization 분리 |
| D4-revised (실측 후) | **이미 fixed (PR #3) + verification done** | timeline 정확화 — issue close, Phase 5 entry condition 단순화 |
| D5 library infra_strategy | A `none` | 배포 표면 부재, fake infra ROI 0 |
| D6 ADR-009 amendment | A 지금 | sister rollout 들이 패턴 복사 전 박제 |
| D7 등록 mechanic | A 둘 다 retroactive | git history 외 governance anchor 의무 |
| D8 Epic 명칭 | "Docker-first Migration" | ADR-033 정책 어휘 정합 |

### 11.4 5 sister shape 분석

| Repo | Shape | infra_strategy | Phase | Risk |
|---|---|---|---|---|
| mctrader-engine | backtest one-shot CLI + paper daemon | docker_first | 3 | medium — one-shot + daemon 이중 mode 검토 의무 |
| mctrader-web | multi-service (FastAPI + Streamlit + sqlite volume) | docker_first | 4 | high — multi-service novel pattern, sqlite volume DR 분리 vs 통합 결정 |
| mctrader-market | library (pure Python, Candle Protocol) | none | 5 (joint) | low — `infra_strategy: none` lint pass 만 |
| mctrader-market-bithumb | library + WS adapter | none | 5 (joint) | low — WS schema fix 이미 완료 (PR #3 + smoke verified) |
| mctrader-hub | governance / docs (no runtime) | none | 5 (joint) | low — `infra_strategy: none` lint pass 만 |

### 11.5 본 §11 박제 시점

- Phase 2 entry PR (mctrader-hub `docs/MCT-98-MCT-99-phase-2-entry`) 안에 commit
- Pilot Story issue MCT-99 (mctrader-hub#121) close = Phase 2 entry PR merge 시점
- Epic Story issue MCT-98 (mctrader-hub#120) = Phase 6 close 시점까지 OPEN
- mctrader-market-bithumb#4 issue: stale registration → smoke verification 후 close as resolved 2026-05-08T00:36:49Z
