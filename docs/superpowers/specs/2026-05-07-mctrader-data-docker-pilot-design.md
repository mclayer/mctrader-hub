# mctrader-data Docker-first Containerization (Pilot) — Design Spec

> **Source**: brainstorming session 2026-05-07, Sonnet 4.6 (Claude Opus 4.7 1M context)
> **Trigger**: codeforge ADR-033 / CFP-128 Phase 2 wrapper PR Accepted (2026-05-07) — InfraEngineerAgent default 출력 = Docker-first. mctrader 6-repo가 grandfather + follow-on Epic 의무.
> **Channel**: codeforge consumer Story (story-init → phase-gate-mergeable). mctrader-hub Epic 하위 첫 Pilot Story.

## §0. 메타

| 항목 | 값 |
|------|-----|
| Story key (잠정) | **MCT-N** (mctrader-hub issues 신규 발급, Epic Story와 함께 결정) |
| Parent Epic (잠정) | **MCT-M — mctrader Containerization** (별도 Epic Story, Pilot은 Phase 1) |
| Title | mctrader-data Docker-first Containerization (Pilot) |
| 작업 채널 | codeforge 의무 (consumer adoption — phase-gate-mergeable) |
| In-scope repo | mctrader-data만 |
| Out (Epic 후속) | 5 sister rollout (engine / web / market / market-bithumb / hub) |
| Trigger ADR | codeforge ADR-033 (Docker-first Infra Engineering, CFP-128 Accepted 2026-05-07) |

## §1. Background (사용자 directive + 컨텍스트)

> "codeeforge의 변경에 따라 mctrader에서 작업해야할 내용이 있다. docker containerize에 관한 부분이다."
> "현재 systemd 작업은 수행하고 있지 않으니 편하게 stop해도 된다."

- ADR-033 (carrier_story CFP-128) — InfraEngineerAgent mandate 재정의: Docker-first (Dockerfile + compose.yml + .dockerignore). systemd / launchd / PaaS = legacy (consumer overlay opt-in only).
- mctrader 6-repo 모두 codeforge consumer (CFP-96 Phase 6, 2026-05-05 종료) — `.claude/_overlay/project.yaml` 보유. 6 repo 모두 `infra_strategy:` 미명시 → ADR-033 default `docker_first` 자동 적용 → 신규 Story 진입 시 `scripts/check-container-strategy.sh` lint fail trigger.
- mctrader-data 의 기존 자산: `deploy/mctrader-collector.service` (systemd unit, MCT-58 / MCT-94) + `deploy/README.md`. Production 미가동 (사용자 확인) — migration scope 단순.
- ADR-033 §결정 6: "follow-on Epic candidate: mctrader containerization" — consumer 워크스페이스에서 수행 의무.

## §2. Scope

### §2.1 Pilot 본 Story (in-scope)

mctrader-data repo의 Docker-first 전환 — **collector daemon** 1 service만 compose service. backfill은 동일 image의 ad-hoc `compose run`으로 처리.

### §2.2 Pilot 결정점 (이미 사용자 승인)

| Decision | 채택 | 거절 |
|---|---|---|
| D1 응답 경로 | Dockerization Epic 진입 | 방어적 선언만 (legacy_systemd) / 단계적 일부만 |
| D2 Epic sequencing | Pilot → Rollout (1 + 5) | Mode B Joint Epic / repo-by-repo |
| D3 Pilot 후보 | mctrader-data | mctrader-web / mctrader-engine |
| D4 systemd 처리 | Docker-only 전환 (unit 삭제) | Docker primary + systemd 보존 / Cutover plan parallel |
| D5 Compose surface | collector daemon 1 service | + backfill (profiles: tools) / + cold-archive sidecar |
| D6 Pilot depth | Approach 1 — baseline + lint-only CI | Approach 2 (ghcr publish + trivy image scan) / Approach 3 (distroless + cosign) |
| D7 Build target | linux/amd64 단일 | Multi-arch buildx (amd64 + arm64) |

### §2.3 Out-of-scope (Epic 후속 Story)

- ghcr.io publish workflow (별도 Story — `image-publish.yml` + multi-arch + image-ref 발급)
- trivy image-ref scan 활성화 (publish Story와 묶음 — Pilot은 hadolint job만 호출)
- distroless / digest pin / cosign signing (보안 강화 별도 Story)
- Multi-arch buildx (linux/arm64 — 후속 결정)
- 5 sister rollout (mctrader-engine / -web / -market / -market-bithumb / -hub) — Epic Phase 2+
- mctrader-hub governance Epic 문서 (별도 Story)
- ADR-009 amendment (forward-only invariant + volume DR backup 절차) — 별도 ADR 후보

## §3. 도입할 설계 (target)

### §3.1 Architecture overview

mctrader-data의 long-running collector daemon을 systemd unit에서 Docker container (single image, 2-stage Dockerfile, named volume, 자체 heartbeat-check)로 전환. ADR-033 §7.4 OpRiskArch 4 항목 (restart / volume DR / health check / network mode)을 compose.yml에 박제해 후속 5 sister rollout의 reference 패턴으로 만든다.

### §3.2 Components (file 단위 변경)

#### 신규 파일

| 파일 | 책임 |
|---|---|
| `Dockerfile` | python:3.12-slim 2-stage (deps → runner). uv로 의존 install (mctrader-market / mctrader-market-bithumb git+https). runtime은 wheel만, non-root user `mctrader` (UID 1001). HEALTHCHECK directive 포함. |
| `compose.yml` | 1 service `collector` (build: .). volumes: `mctrader_data:/var/lib/mctrader/data` named volume. restart: unless-stopped. networks: bridge default. healthcheck (compose-side, Dockerfile HEALTHCHECK 보강). env: `MCTRADER_DATA_ROOT=/var/lib/mctrader/data`. |
| `.dockerignore` | codeforge cli-tool-minimal 패턴 + `data/` 추가 (개발용 parquet 제외) |
| `src/mctrader_data/cli.py` (수정) | 신규 subcommand `mctrader-data heartbeat-check` 추가 — heartbeat 파일 mtime ≤ threshold 검증, 임계 초과 시 exit 1 |
| `src/mctrader_data/heartbeat.py` (수정) | `check_staleness(path, threshold_sec)` 함수 추가 — 기존 heartbeat write 로직 재사용 |
| `tests/test_heartbeat_check.py` | TDD 4 시나리오: 파일 부재 / mtime 신선 / mtime stale / env override threshold |
| `.github/workflows/image-lint.yml` | codeforge `templates/github-workflows/container-image-scan.yml` 패턴을 참조하여 hadolint job만 활성. invocation 방식 (file 내용 직접 작성 vs reusable `uses: mclayer/plugin-codeforge/.github/workflows/X.yml@main` 호출) 은 plan 단계에서 결정 (codeforge가 templates/에 둔 file이라 reusable 호출 가능 여부 확인 필요). trivy job은 image-ref 부재 → skip 또는 미포함. |
| `tests/integration/README.md` | manual smoke 절차 박제 (compose up + healthcheck wait + volume invariant + SIGTERM graceful) |

#### 수정 파일

| 파일 | 변경 |
|---|---|
| `.claude/_overlay/project.yaml` | `infra_strategy: docker_first` field 명시 (codeforge `check-container-strategy.sh` lint PASS 위해) |
| `README.md` | "Linux systemd deployment" 절 → "Docker deployment" 절로 전면 교체 (install / config / ops / health / DR section 모두 docker compose 명령으로) |
| `pyproject.toml` | version 0.8.0 → 0.9.0 (semver minor — CLI surface backward-compatible, deploy 자산만 breaking) |
| `CHANGELOG.md` | `[0.9.0]` entry 신설: "BREAKING: deploy/mctrader-collector.service removed. Migrate to Docker (see README)." |

#### 삭제 파일

| 파일 | 이유 |
|---|---|
| `deploy/mctrader-collector.service` | systemd-only 자산. Docker-only 전환. |
| `deploy/README.md` | systemd 가이드. Docker 가이드는 repo README로 이전. |
| `deploy/` 디렉토리 | 비어있게 됨 — 삭제. (향후 K8s preset 추가 시 `presets/k8s/`로 별도 디렉토리, ADR-033 §결정 2 패턴) |

### §3.3 Data flow / runtime

#### Build time

1. `docker compose build` 실행 → Dockerfile 처리
2. **Stage 1 (deps)**: `python:3.12-slim` + uv install → `uv pip install --system -e .` (wheel + git+https deps). git+https는 build 시점 outbound only.
3. **Stage 2 (runner)**: minimal slim base + Stage 1의 site-packages COPY + `mctrader-data` entrypoint, non-root user `mctrader` (UID 1001).

#### Runtime — collector daemon lifecycle

```
docker compose up -d
  ↓
container start → ENTRYPOINT [mctrader-data]
  CMD ["collect", "--top-n", "10", "--include", "transactions,orderbook", "--log-level", "INFO"]
  ↓
heartbeat.py가 /var/lib/mctrader/data/.heartbeat 주기 touch (기존 패턴 재사용)
  ↓
collector.py가 Bithumb pubwss.bithumb.com WebSocket 연결 → tick / orderbook stream
  ↓
storage.py가 schema_version=tick.v1 / orderbook.v1 / ohlcv.v1 partition으로 parquet write
  ↓ (volume: named volume mctrader_data)
docker compose stop
  ↓ SIGTERM → collector.py drain (in-flight write flush) → 30s timeout → SIGKILL fallback
```

#### Network boundary

- **Inbound**: 0개 (collector는 listening service 아님)
- **Outbound**: `pubwss.bithumb.com:443` (WebSocket TLS) + `api.bithumb.com:443` (HTTPS)
- **Network mode**: bridge (compose default). `network_mode: host` 미사용. `ports:` 절 부재 (inbound 0).

#### Volume / persistence

- Named volume `mctrader_data` mounted RW at `/var/lib/mctrader/data`
- Host bind mount는 README에 "개발용 alternative"로만 안내, default는 named volume
- 근거: 호스트 path leak 방지 + ADR-033 §7.4 volume DR mandate "host path leak 방지" 정합

#### 3 mode (backtest/paper/live) 와의 관계

collector는 mode-agnostic, 항상 24/7 forward-only 운영 (ADR-009 forward-only). 모든 mode (backtest / paper / live)의 단일 SoT data producer.

### §3.4 §7.4 OpRiskArch 4 항목 mapping

#### 1. Container restart policy
- `restart: unless-stopped` (compose-side)
- 근거: forward-only collector는 의도적 stop 외엔 항상 가동. 사용자 `docker compose stop` 시 재기동 안 함 (operational 의도 존중)
- systemd `Restart=on-failure + RestartSec=10s + StartLimitBurst=5` 매핑 → docker default exit policy로 충분

#### 2. Volume DR
- Named volume `mctrader_data`
- Backup 가이드 (README):
  - 즉시: `docker run --rm -v mctrader_data:/src -v $(pwd):/dst alpine tar czf /dst/mctrader_data-$(date +%Y%m%d).tar.gz -C /src .`
  - Cron 권장: 일 1회, retention 7-day rolling
- ADR-009 invariant: tick/orderbook은 backfill 불가 → 데이터 손실 = 영구 → 즉시 외부 backup 의무

#### 3. Health check tuning

| 파라미터 | 값 | 근거 |
|---|---|---|
| `test` | `["CMD", "mctrader-data", "heartbeat-check"]` | self-check, exec into container 불요 |
| `interval` | `30s` | webapp-minimal 패턴 차용 |
| `timeout` | `10s` | heartbeat 파일 read는 ms 단위 |
| `retries` | `3` | transient WebSocket reconnect 90초 윈도우 (3 × 30) |
| `start_period` | `60s` | collector 초기 connect + symbol subscribe 시간 |

heartbeat-check staleness threshold = `90s` default, env `MCTRADER_HEARTBEAT_STALENESS_SEC`로 override.

#### 4. Network mode boundary

- compose default bridge network
- `network_mode: host` 금지
- inbound port 매핑 0 (collector listening 0)
- outbound: NAT로 Bithumb 도달

## §4. API 계약

**N/A — production runtime API 변경 0개.**

근거: CLI subcommand 1개 (`heartbeat-check`)만 추가. 기존 `collect` / `backfill` subcommand surface 무변. Public Python API (`scan_candles`, `OhlcvSchema`, `BackfillRunner`) 무변. mctrader-market / mctrader-market-bithumb 의존 schema 무변.

## §5. 보안 설계

### §5.1 Trust boundary

- **Container network boundary**: bridge default. internal service 가 host network로 노출 안 됨. inbound 0.
- **Image build context boundary**: `.dockerignore`가 `.env*`, `*.pem`, `*.key`, `*.crt`, `.git`, `.github`, `.claude`, `data/`, `*.md`, `docs/` 제외. `COPY . .` 패턴 시 build context에 sensitive file 미포함.
- **Layer cache boundary**: 2-stage Dockerfile의 deps / runner 분리. Stage 1만 git+https outbound. Stage 2는 wheel COPY만 (build secret 의존 0).

### §5.2 Threat model (STRIDE 발췌)

| 컴포넌트 | 위협 | 본 Pilot 완화 |
|----------|------|---------------|
| Container image | base image stale CVE | python:3.12-slim 사용. 후속 Story에서 trivy image scan 자동화 (Out-of-scope) |
| Container image | image layer 안 secret 누설 | collector scope에서 secret 0개 (public WebSocket만). `.dockerignore` strict로 sensitive file 제외. hadolint syntax 검증. |
| compose network | service-to-service spoofing | 1 service only — service-to-service 0 |
| compose network | host network 노출 | bridge default, host network 미사용, inbound port 매핑 0 |
| Volume | host path escape | named volume only. host bind mount는 dev 옵션. |
| Container secret mount | log/error 누설 | secret 0개 — N/A |

### §5.3 Auth/Authz

**N/A — collector는 공개 WebSocket만. Bithumb API key / token / credential 0개.**

### §5.4 §7.4 운영 리스크

§3.4의 4 항목 매핑 — restart policy / volume DR / health check tuning / network mode. ADR-033 §결정 5 deputy mandate 매트릭스 cell annotation 준수.

### §5.5 민감 데이터 분류

- collector는 public market data만 produce — 분류: Public
- log에 사용자 credential / PII 0개
- image layer에 secret 자체 미포함 → trivy scanners=secret 모드 불요 (단 후속 Story에서 활성화 시 false-positive 0 기대)

### §5.6 N/A 명시

본 Pilot의 §5.3 / §5.5 = N/A (credential / 민감 데이터 0). §5.1 / §5.2 / §5.4 = framework 가이드 준수.

## §6. 테스트 계획

### §6.1 Unit (pytest)

- `tests/test_heartbeat_check.py` (TDD, 4 시나리오):
  1. heartbeat 파일 부재 → exit 1, stderr "heartbeat file not found"
  2. mtime ≤ threshold (default 90s) → exit 0
  3. mtime > threshold → exit 1, stderr "heartbeat stale: <delta>s"
  4. env `MCTRADER_HEARTBEAT_STALENESS_SEC=30` override 적용 검증
- `tests/test_cli.py` (수정) — `mctrader-data heartbeat-check --help` 진입점 등록 확인
- 기존 182 pytest 회귀 PASS 유지 (CLI subcommand 추가만, production code path 무관)

### §6.2 Integration (compose smoke)

- `tests/integration/test_compose_up.sh` (manual, CI 부담 회피):
  1. `docker compose build` exit 0
  2. `docker compose up -d collector` exit 0
  3. 60초 대기 후 `docker compose ps` → `healthy`
  4. `docker compose exec collector mctrader-data heartbeat-check` exit 0
  5. `docker volume inspect mctrader-data_mctrader_data` 존재 확인
  6. `docker compose down -v` cleanup
- Bithumb live WebSocket 의존 → CI fragile → manual smoke + `tests/integration/README.md` 박제
- CI 자동화: `docker compose config` (compose.yml syntax validation)만 활성

### §6.3 Lint

- `hadolint Dockerfile` (codeforge `image-lint.yml` workflow가 호출, failure-threshold=warning)
- `actionlint .github/workflows/image-lint.yml` (codeforge 기존 lint 자동)
- `bash scripts/check-container-strategy.sh` (codeforge lint, `infra_strategy: docker_first` + Dockerfile + compose.yml 모두 존재 → exit 0 PASS)

### §6.4 §8.5 Stateful invariant tests (manual)

- collector = long-running daemon + state-aware → §8.5 적용 의무
- §8.5 invariant smoke (manual, `tests/integration/README.md` §"State invariants"):
  - **Volume 보존**: `up → write data → down → up → 같은 volume mount → data 존재` 검증
  - **SIGTERM graceful shutdown**: in-flight write가 30s timeout 내 flush. collector.py 기존 cleanup 로직 재사용 검증.

### §6.5 TDD 진입 순서

1. `test_heartbeat_check.py` 4 시나리오 RED
2. `cli.py` + `heartbeat.py`의 `check_staleness()` 추가 GREEN
3. Dockerfile 작성 (hadolint PASS)
4. compose.yml 작성 (`docker compose config` syntax PASS)
5. systemd 자산 삭제 + README 교체
6. `infra_strategy: docker_first` field 추가 → `check-container-strategy.sh` PASS
7. `.github/workflows/image-lint.yml` 작성

### §6.6 Coverage 목표

- heartbeat-check 신규 코드 100% line
- integration smoke = manual + CI는 syntax-only

## §7. Migration / Cross-platform parity

### §7.1 systemd 자산 삭제 (production 미가동)

- 기존 `deploy/mctrader-collector.service` + `deploy/README.md` 삭제만 수행 (사용자 host stop / 데이터 import / cutover orchestration 불요)
- README breaking note: "v0.9.0: deploy method changed from systemd to Docker. systemd reference removed."
- volume 마이그레이션 0건 — `/var/lib/mctrader/data` host 데이터 import 불필요

### §7.2 Cross-platform parity (Windows dev → Linux prod)

- **Build**: `docker compose build` → linux/amd64 image (Windows Docker Desktop default. FROM python:3.12-slim → 자동 platform). Dockerfile에 `--platform=linux/amd64` 명시 안 해도 default.
- **Dev cycle (Windows)**: Windows Docker Desktop 안에서 `docker compose up -d collector` → Linux VM 안 동작, heartbeat / log / volume 모두 Linux semantics.
- **Prod 배포 (Linux)**: image push 자동화는 Pilot 외 → Linux host에서 source clone + `docker compose build` 재실행 권장. README에 명시.
- 동일 Dockerfile + compose.yml이 두 환경에서 동일 동작 = parity 정의.

### §7.3 Rollback 경로 (Pilot 검증 실패 시)

- git revert PR로 commit 복구 (Dockerfile / compose.yml / .dockerignore / heartbeat-check 모두 제거)
- production 운영 중 아니므로 host cleanup 불요
- volume `mctrader_data`은 docker volume rm으로 삭제 OR 다음 시도 위해 보존 — 사용자 재량

### §7.4 Cutover 검증 (Story §10 acceptance evidence)

1. Windows dev에서 `docker compose build && docker compose up -d collector` → 60s 후 healthy
2. `docker compose exec collector mctrader-data heartbeat-check` exit 0
3. `docker compose logs collector --tail=20`에 `[collector] symbol=KRW-BTC channels=...` 라인 존재
4. `docker compose down -v && docker compose up -d collector` → healthy 회복 (volume 재마운트 invariant)
5. `hadolint Dockerfile` warning 0
6. `bash scripts/check-container-strategy.sh` PASS
7. `pytest tests/` 기존 + 신규 4 시나리오 모두 PASS

## §8. 영향 / 의존

### §8.1 codeforge 의존

- ADR-033 (CFP-128 Accepted 2026-05-07)
- `templates/github-workflows/container-image-scan.yml` (외부 reusable workflow, hadolint job 호출)
- `scripts/check-container-strategy.sh` (consumer-side lint)
- `examples/cli-tool-minimal/Dockerfile` + `examples/webapp-minimal/{Dockerfile,compose.yml}` (참조 패턴)

### §8.2 mctrader-hub Epic 후속

- Epic Story `MCT-M — mctrader Containerization` 신설 의무 (본 Pilot은 Epic Phase 1로 lodge)
- 본 Pilot 종료 후 §11 회고에 Epic Phase 2+ entry 조건 박제 (5 sister rollout)
- 5 sister 각자의 모양: mctrader-engine (backtest one-shot + paper daemon), mctrader-web (multi-service compose), mctrader-market / -bithumb (library = `infra_strategy: none`?), mctrader-hub (governance = `infra_strategy: none`?). Pilot에서 박제된 패턴이 reference.

### §8.3 ADR-009 amendment 후보 (별도 Story)

- forward-only invariant + volume DR backup 절차를 ADR-009에 명시 (mctrader-data ADR set의 일부) — 본 Pilot scope 외, 별도 ADR amend Story 또는 Epic 차원에서 처리.

## §9. Future work / Open questions

| ID | 항목 | 처리 방향 |
|---|---|---|
| F1 | ghcr.io publish workflow + multi-arch buildx | 별도 Story (Pilot 종료 후, Epic Phase 2 또는 별도) |
| F2 | trivy image-ref scan 활성화 | F1과 묶음 (publish 후 image-ref 발급) |
| F3 | distroless / digest pin / cosign signing | 보안 강화 별도 Story (필요 시) |
| F4 | 5 sister rollout | Epic Phase 2+ — 본 Pilot의 §11 회고에서 sequencing 결정 |
| F5 | mctrader-hub governance Epic 문서 (EPIC-RESULTS-MCT-M) | Epic 종료 시 |
| F6 | ADR-009 amendment (forward-only + volume DR) | 별도 ADR 후보 |
| O1 | mctrader-market / -bithumb의 `infra_strategy` (library = none?) | 5 sister rollout 진입 시 결정 |
| O2 | mctrader-hub의 `infra_strategy` (governance = none?) | 동상 |
| O3 | backfill subcommand의 compose-side 처리 (profile? 별도 service?) | Pilot 종료 후 운영 경험 기반 결정 |
| O4 | volume backup cron 자동화 | F4 sister rollout 시 통합 |

## §10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| 응답 경로 | Dockerization Epic 진입 | 방어적 선언 (legacy_systemd) — 후속 의무 회피, 사용자 의도 약 / 단계적 일부 — 결국 Epic 의무, scope 정합 약 |
| Sequencing | Pilot → Rollout | Mode B Joint Epic — 5 sister 모양이 다 달라 한 번에 risk 높음 / repo-by-repo — pilot reference 박제 약 |
| Pilot 후보 | mctrader-data | mctrader-web — 기존 systemd 자산 부재로 migration 경험 검증 약 / mctrader-engine — §7.4 mandate 검증 약 (one-shot 위주) |
| systemd 처리 | Docker-only 전환 | Docker primary + systemd 보존 — production 미가동, 보존 ROI 0 / Cutover plan parallel — 사용자 환경 미가동, 단순화 선호 |
| Compose surface | collector 1 service | + backfill profiles — 운영 빈도 낮아 ad-hoc compose run으로 충분 / + cold-archive sidecar — Pilot scope 외, 후속 결정점 |
| Pilot depth | Approach 1 baseline | Approach 2 ghcr publish — Pilot 명목 (검증) 흐림 / Approach 3 distroless — uv runtime 호환 까다, scope 초과 |
| Build target | linux/amd64 단일 | Multi-arch buildx — Pilot scope 외, ARM 대상 host 미확정 / 둘 다 의도 (parity 명시) — README parity 명시는 채택안에 포함 |

## §11. 참고 / 관련 파일

### codeforge (외부 의존, mclayer/plugin-codeforge)
- `docs/adr/ADR-033-docker-first-infra-engineering.md` — 본 Pilot의 trigger
- `templates/github-workflows/container-image-scan.yml` — hadolint + trivy reusable workflow
- `scripts/check-container-strategy.sh` — consumer lint (Pilot이 PASS 의무)
- `examples/cli-tool-minimal/Dockerfile` + `.dockerignore` — 참조 패턴
- `examples/webapp-minimal/Dockerfile` + `compose.yml` — 참조 패턴 (multi-service이지만 healthcheck / restart / volume 패턴 차용)

### mctrader (관련 cross-repo 자산)
- `mctrader-data/deploy/mctrader-collector.service` — 본 Pilot에서 삭제 대상
- `mctrader-data/src/mctrader_data/heartbeat.py` — 기존 heartbeat write 로직, `check_staleness()` 함수 추가 대상
- `mctrader-hub/EPIC-RESULTS-MCT-89.md` — collector HA reference (systemd 박제)
- `mctrader-hub/EPIC-RESULTS-MCT-94.md` — Ops Scripts (systemd + Ansible) reference
- `mctrader-hub/EPIC-RESULTS-MCT-97.md` — Admin Engine Control Panel (5 engine SM, Pilot의 web admin과 후속 연결점)

### mctrader-data 본 repo
- `pyproject.toml` — version bump 대상
- `README.md` — 전면 교체 대상
- `.claude/_overlay/project.yaml` — `infra_strategy: docker_first` 추가 대상

---

## Acceptance Criteria (요약)

1. `Dockerfile` (2-stage, python:3.12-slim, non-root user) — hadolint warning 0
2. `compose.yml` (collector 1 service, named volume, restart unless-stopped, healthcheck, bridge network) — `docker compose config` PASS
3. `.dockerignore` — codeforge cli-tool-minimal 패턴 + `data/` 추가
4. `mctrader-data heartbeat-check` CLI subcommand + 4 TDD 시나리오 pytest PASS
5. `.claude/_overlay/project.yaml`에 `infra_strategy: docker_first` 추가
6. `bash scripts/check-container-strategy.sh` PASS (codeforge lint)
7. `.github/workflows/image-lint.yml` (codeforge `container-image-scan.yml` reusable, hadolint job 활성)
8. `deploy/mctrader-collector.service` + `deploy/README.md` + `deploy/` 디렉토리 삭제
9. `README.md` "Docker deployment" 절 — install / config / ops / health / DR 모두 docker compose 명령
10. `pyproject.toml` 0.8.0 → 0.9.0, `CHANGELOG.md` `[0.9.0]` BREAKING entry
11. `tests/integration/README.md` manual smoke 절차 박제 (compose up + heartbeat + volume invariant + SIGTERM graceful)
12. Cutover 검증 7-step (§7.4) 모두 PASS evidence Story §9에 박제
13. 기존 182 pytest 회귀 PASS 유지

---

## 다음 단계

1. 본 spec 파일 사용자 review
2. 사용자 approve 후 `superpowers:writing-plans` skill 호출 → implementation plan 작성
3. plan 작성 후 `MCT-M` Epic Story + `MCT-N` Pilot Story file scaffold (codeforge story-init workflow)
4. Phase 1 PR (design freeze + Story §1-§7 + Codex review archive)
5. Phase 2 PR (impl: Dockerfile + compose + heartbeat-check + README + systemd 삭제 + project.yaml + image-lint.yml)
6. Phase 2 PR review chain (CodeReview + TestAgent + SecurityTest 1st-layer hadolint) + admin merge
7. Story §11 회고 — Epic Phase 2+ rollout sequencing 결정점 박제
