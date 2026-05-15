# ADR-030: Docker stack governance — single-host compose + dev/prod profile + image registry + observability

## Status

**Accepted** (MCT-175 LAND 2026-05-15 — hub#326 8c485ef Phase 1 docs + hub#327 daef9b3 Phase 2 PR1 code + hub#328 dbba327 Phase 2 PR2 박제)

이전 상태: Proposed (MCT-175 Phase 1 진입, 2026-05-15)

### Amendment box (MCT-175 LAND, 2026-05-15)

**MCT-175 D1/D3/D7/D13 VERIFIED**:
- D1 (WAL host bind mount): `compose.yml` collector stub 주석 박제 (실 활성화 = MCT-176 LAND)
- D3 (compose profiles dev/prod): `--profile dev|prod` + `.env.dev`/`.env.prod.example` env_file 분리 LAND. `docker compose --profile dev/prod config` exit 0 (AC-1 PASS)
- D7 (NAS DNS preflight): `scripts/preflight-nas-dns.sh` 신규 — exit 0/10/20/30/99 matrix 정합 (AC-3 PASS)
- D13 (cross-repo lock CI gate): `scripts/check_cross_repo_locks.py` (121 lines) + `.github/workflows/cross-repo-lock-check.yml` 신규. 14 unit test green (AC-5 PASS). **현 trigger = `workflow_dispatch` only** (secret 미등록 carry over → MCT-176 등록 후 PR auto trigger 복원 의무)

**MCT-176 carry over (defer 3건 + secret 등록 + workflow trigger 복원)**:

| 항목 | 사유 | 처리 시점 |
|------|------|----------|
| P1-2 (preflight DNS wildcard FP) | 실 위험 낮음 + logging 통합 시 fix | MCT-176 Phase 2 |
| P1-3 (mc alias trap race) | SIGINT race window security 위협 낮음 | MCT-176 cross-ref |
| P2-1 (shell error handling) | 실 위험 낮음 | MCT-176 carry over |
| NAS_MINIO_* secret 등록 | `cross-repo-lock-check.yml` PR auto trigger 복원 의존 | MCT-176 Phase 1 |
| `workflow_dispatch` only → `on: pull_request` 복원 | secret 등록 후 LAND | MCT-176 Phase 2 |

## Context

`mctrader-hub/compose.yml` 은 인프라 stack (postgres + minio + redis + mc-init + prometheus + grafana +
nginx + exporters + signal-collector 5종) 을 정의하나, **mctrader-data (collector) + mctrader-engine
(paper-engine / backtest-runner) 어플리케이션 서비스가 누락**.

추가 미결 사항:
- dev (hub MinIO) / prod (NAS MinIO, mcnas01.internal.mclayer.it) profile 분리 부재 — 환경별 endpoint
  전환 수동
- image registry tag 정책 모호 (latest 혼용)
- container resource limits 미정의 (capacity 4 layer — ADR-029 §D11 정합 필요)
- EPIC-tier-promotion-single-source R-CRITICAL (WAL 30G 가설 미측정) carry over → 본 Epic MCT-179 책임

배경 관련 ADR:
- ADR-027 §D2 Stage 1 HTTP-only gate (NAS MinIO HTTP 평문 운영, MCT-155 TLS cutover 미확정)
- ADR-029 §D4 WAL local-only 정책 + §D11 4 layer capacity
- ADR-009 §D12 forward-only invariant

## Decision

### §D1 WAL host disk 별도 mount + L1 named volume

> owner: MCT-176

collector container 의 WAL 디렉터리는 **host bind mount** 로 박제:

```yaml
volumes:
  - /var/lib/mctrader/wal:/var/lib/mctrader/data   # host bind mount (ADR-030 §D1)
```

- **근거**: WAL = forward-only invariant (ADR-029 §D4). host disk 손실 = 영구 손실 risk 명시 acceptance.
  container lifecycle 에 의존하면 restart 시 WAL 소실 위험.
- **L1 cold cache** = `mctrader_l1` named volume (compose lifecycle 정합, 재시작 후에도 유지).
- **host disk loss acceptance**: R4 MEDIUM — 사용자 explicit accept 의무 (MCT-175 plan §0 확인).
  1d max loss window (host disk replace 후 forward-only). external backup 도입 = op risk 증가 → reject.

### §D2 paper-engine daemon + backtest-runner [oneshot] 동일 image command override

> owner: MCT-177 (paper daemon) + MCT-178 (backtest profile)

`mctrader-engine` Dockerfile = 단일 image, command override 로 분기:

```yaml
# paper-engine — daemon mode
paper-engine:
  image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
  command: ["paper", "--daemon"]
  restart: unless-stopped

# backtest-runner — oneshot (profiles: [backtest])
backtest-runner:
  image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
  command: ["backtest", ...]
  profiles: ["backtest"]
  restart: "no"
```

- **근거**: image build 1회 → command 분기. dev/prod parity. backtest = profile trigger (별 invoke).

### §D3 compose profiles dev/prod + env_file 분리

> owner: MCT-175

```
Profile  │ MinIO endpoint         │ env_file
─────────┼────────────────────────┼──────────────
dev      │ http://minio:9000      │ .env.dev
prod     │ mcnas01.internal:9000  │ .env.prod
```

- `profiles: ["dev"]` — hub MinIO (minio, mc-init) service: dev profile 에서만 기동
- `profiles: ["prod"]` — NAS preflight only (스크립트 기동)
- `.env.dev` / `.env.prod` = `env_file:` 로 NAS_MINIO_* 변수 분기
- `.env.prod` = `.gitignore` 대상 (secret 포함)

**사용법**:
```bash
# dev
docker compose --profile dev --env-file .env.dev up

# prod
docker compose --profile prod --env-file .env.prod up
```

### §D7 NAS DNS 직접 해석 + preflight 검증

> owner: MCT-175 (preflight 도구) + MCT-176 (collector endpoint)

container 내부에서 `mcnas01.internal.mclayer.it:9000` DNS 직접 해석.

`scripts/preflight-nas-dns.sh` 가 `compose up` 전 3단계 검증:
1. DNS resolution (dig 또는 getent)
2. TCP connect (5s timeout)
3. S3 list bucket (mc client, optional)

exit code:
- `0` = ALL PASS
- `10` = DNS FAIL
- `20` = TCP FAIL
- `30` = S3 FAIL
- `99` = env parse FAIL

prod profile 진입 시 preflight exit 0 필수 gate.

### §D12 image registry pin — semver + sha + latest 병행

> owner: MCT-181

```
registry: ghcr.io/mclayer/{repo}:{tag}

prod  = ghcr.io/mclayer/mctrader-{repo}:sha-<7char>  (CI release 시 pin)
      + ghcr.io/mclayer/mctrader-{repo}:v{semver}    (release tag)
dev   = ghcr.io/mclayer/mctrader-{repo}:latest       (rapid iteration)
```

- **prod pin 의무**: `IMAGE_TAG=sha-xxxxxxx` .env.prod 에 박제, latest pull 금지
- **dev = latest** 허용 (local build fallback 포함)
- GitHub Actions `GITHUB_TOKEN` 사용 (ghcr.io write permission)

### §D13 각 repo 독립 uv.lock + cross-repo CI lock gate

> owner: MCT-175

- 6 repo 각자 `uv.lock` 유지 (monorepo lock 회피, 독립 lifecycle)
- `scripts/check_cross_repo_locks.py` — 핵심 lib (pyarrow / boto3 / pydantic / websockets) major version + python_version drift CI gate
- `.github/workflows/cross-repo-lock-check.yml` — hub PR push 마다 자동 실행
- drift = FAIL (merge 차단)

**Amendment (MCT-175 FIX iter 1, 2026-05-15)** — coverage gap + semantic precision:

- **allowed_missing repos** = `{mctrader-hub, mctrader-signal-collector}` (현 시점 uv 미도입 SSOT)
  - 그 외 4 repo (data / engine / web / market) uv.lock 부재 시 **exit 99 strict mode**
  - 기존 silent WARN+skip 동작은 D13 coverage gap (4/6 만 검사) → FIX iter 1 P0-2 fix
- **python_version semantic** = **distinct equality only** (절대 minimum 미정의)
  - docstring 기존 표기 `>=3.12` 약속과 실 검증 (`distinct count <= 1`) mismatch → FIX iter 1 P0-2 fix
  - drift detection 의미: "모든 required repo 가 동일 requires-python 문자열" (예: `>=3.12` 일관) — 절대 minimum 검증 미수행
  - 후속 강화 시 (예: `>=3.12` floor enforcement) 별 Story 발의 의무

### §D17 SIGTERM graceful + startup InvariantHarness scan (외부 backup 없이)

> owner: MCT-179

- **SIGTERM handler**: collector/paper-engine/backtest-runner 모두 SIGTERM 수신 시 graceful drain
  (WAL flush + sealed segment 완료 대기, 60s timeout)
- **startup scan**: 컨테이너 시작 시 InvariantHarness 8종 scan (MCT-171 SSOT). 위반 시 warn + continue.
- **외부 backup 없음**: ADR-029 §D4 WAL local-only 정합. external backup sidecar = invariant 위반 + op
  risk 증가 → reject. host disk 손실 risk = R4 MEDIUM 명시 acceptance.

### §D18 명시 resource limits + Prometheus alert (>80% warn)

> owner: MCT-180

모든 어플리케이션 service 에 `deploy.resources.limits` 명시:

```yaml
deploy:
  resources:
    limits:
      memory: <M>m
      cpus: "<N>"
```

ADR-029 §D11 4 layer capacity 정합:
- WAL host disk: 30G (hard_limit) → container mem limit 별도
- L1 named volume: 20G → NAS 의존
- 컨테이너 memory limit: collector 512M / paper-engine 1G (MCT-180 에서 측정 후 확정)

Prometheus alert:
- `container_memory_usage_bytes` / `container_spec_memory_limit_bytes` > 0.80 → WARN
- MCT-179/180 에서 alert rule yaml 박제

## Consequences

**긍정**:
- 단일 compose stack 으로 dev/prod 동일 entry → operational parity
- env_file 분기 + profile flag 로 endpoint 전환 명시 → 운영 혼선 감소
- CI lock gate 로 cross-repo Python/lib version drift 사전 차단
- startup InvariantHarness scan 으로 컨테이너 기동 시 integrity 조기 감지

**부정 / risk**:
- R1 HIGH: NAS HTTP-only 평문 노출 (ADR-027 D2 Stage 1 한정). 내부망 + NAS firewall + .env 0600 + 90d
  rotation 으로 mitigation. MCT-155 TLS cutover는 별 Story 백로그 (MCT-176 진입 전 사용자 결정 의무).
  R1 acceptance carrier: user_acknowledged_at=2026-05-15 by mclayer8865@gmail.com (cross-ref: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md §5 R1)
- R4 MEDIUM: host disk 손실 → WAL local segment 영구 손실 (1d max). 사용자 explicit accept 완료
  (plan §0, 2026-05-15).
  R4 acceptance carrier: user_acknowledged_at=2026-05-15 by mclayer8865@gmail.com (cross-ref: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md §5 R4)
- D17 startup scan overhead: 8 invariant 스캔 = 시작 시 I/O 증가. 60s graceful timeout 과의 균형 필요.

## Out of scope (manifest SSOT)

본 ADR 는 EPIC-mctrader-docker-stack 7 Story 범위 내 8 D 만 본문 박제. 아래 10 D 는 manifest 박제 후
별 Story 차원 결정/구현으로 defer. SSOT = `scope_manifests/EPIC-mctrader-docker-stack.yaml`.

| D | 내용 | Owner Story (manifest) |
|---|------|------------------------|
| D4 | container restart policy + healthcheck 표준 | MCT-177 / MCT-178 / MCT-180 |
| D5 | observability stack (prometheus + grafana + node-exporter) | MCT-179 |
| D8 | DR mode state machine 통합 (compose alert → dr_mode flip) | MCT-179 |
| D9 | NAS credential rotation (90d) automation | MCT-176 ✓ |
| D10 | universe override + Redis prefix isolation | MCT-177 / MCT-178 |
| D11 | compose config CI lint (yaml schema + service dep DAG) | MCT-178 |
| D14 | effective config stdout dump (collector entrypoint) | MCT-176 ✓ |
| D15 | paper-engine universe override env precedence | MCT-177 |
| D16 | backtest-runner oneshot artifact archive | MCT-178 / MCT-181 |
| D19 | backtest artifact NAS sync (별 prefix) | MCT-181 |

각 D 본문 박제 시점 = 해당 owner Story Phase 1 LAND (ADR-030 amendment box append).

### Amendment box (MCT-176 Phase 1, 2026-05-15)

#### §D9 amendment — NAS credential rotation 90d automation

**MCT-176 D9 LAND (Phase 1 박제)**:

- **rotation script path**: `scripts/rotate-nas-credentials.sh`
- **cycle**: 90d (cron schedule, 분기 1일 03:00 KST 기준)
- **automation flow**: openssl rand credential 생성 → `.env.prod` sed 갱신 (백업 포함)
  → compose down/up → Slack webhook 알림 → rotation log git commit
- **Slack send 실패 시**: `gh issue create` 로 GitHub Issue 자동 발의
  (repo: `mclayer/mctrader-hub`, label: `ops-alert`)
- **carrier runbook**: `docs/runbooks/nas-credential-rotation-automation.md`
- **cross-ref manual**: `docs/runbooks/nas-minio-secret-rotation.md` (emergency / NAS DSM UI 경유 절차 유효)
- **dry-run 지원**: `bash scripts/rotate-nas-credentials.sh --dry-run` exit 0

#### §D14 amendment — effective config stdout dump

**MCT-176 D14 LAND (Phase 1 박제)**:

- **CLI subcommand**: `mctrader-data effective-config --format {json,yaml}`
- **source order**: `env` > `YAML default` > `built-in default`
- **출력 항목**: `nas_endpoint`, `wal_path`, `universe_id`, `log_level`, 기타 설정값
  + 각 항목별 `_source` 필드 (`env | yaml | builtin`)
- **operator verify hook**: collector container 진입 후 즉시 실행:
  ```bash
  docker exec mctrader-collector mctrader-data effective-config --format json
  ```
- **구현 위치**: `mctrader-data/src/mctrader_data/cli.py` (MCT-176 Phase 2 PR1 LAND 시 신규 subcommand)
- **unit test**: `tests/unit/test_effective_config.py` (5 test, env/yaml/builtin 우선순위 검증)

### Amendment box (MCT-176 LAND confirm, 2026-05-15 Phase 2 PR2)

**MCT-176 D7/D9/D14 VERIFIED** (Phase 2 PR1 양측 LAND 후 박제):

- **D7 (NAS preflight collector wiring)**: `compose.yml` collector service 진입 시 preflight hook (depends_on +
  `scripts/preflight-nas-dns.sh` exit gate). MCT-175 LAND 도구 활용 (재구현 없음). P1-2 (sentinel IP `203.0.113.1`
  차단) + P1-3 (trap 순서 cleanup→ERR) + P2-1 (`bash -n` syntax check + `set -euo pipefail`) MCT-175 carry over fix 통합 (AC-4 PASS).
- **D9 (NAS credential rotation 90d automation)**: `scripts/rotate-nas-credentials.sh` 신규 LAND (hub#331 3498a8b).
  CodeReviewPL FIX iter 1 P1 fix 박제 — F-002 Slack reorder before revoke (rollback 가능) + F-003 `.env.prod.bak`
  trap cleanup (`rm -f $ENV_FILE.bak` on EXIT/INT/TERM) + `.gitignore` `.env.*.bak` pattern 등록. dry-run 모드 exit 0 (AC-3 PASS).
- **D14 (effective-config CLI subcommand)**: `mctrader-data effective-config --format {json,yaml}` 신규 LAND
  (data#64 e3141b6). **CodeReviewPL FIX iter 1 P1 amendment — `source_order` 다운그레이드** to `["env", "built_in"]`
  (YAML loader 미구현 false claim 차단, MCT-177 carry over). 8 신규 test ALL PASS (AC-2 PASS). docstring +
  TODO(MCT-177) 주석 박제.

**Phase 2 PR1 양측 LAND timeline**:

| repo | PR | LAND commit | merged_at |
|------|-----|-------------|-----------|
| mctrader-data | #64 | e3141b6 | 2026-05-15T08:00:41Z |
| mctrader-hub | #331 | 3498a8b | 2026-05-15T08:04:03Z |

**Operational carry over 처리 결과 (MCT-175 → MCT-176)**:

| 항목 | MCT-176 처리 |
|------|-------------|
| P1-2 (preflight DNS wildcard FP) | ✓ fix — sentinel IP `203.0.113.1` 차단 + DNS resolver verify |
| P1-3 (mc alias trap race) | ✓ fix — trap 순서 cleanup→ERR (race window 차단) |
| P2-1 (shell error handling) | ✓ fix — `set -euo pipefail` + `trap ERR` 박제 (`bash -n` syntax check 통과) |
| NAS_MINIO_* secret 등록 | ✓ 박제 — `MCTRADER_CROSS_REPO_TOKEN` GitHub Actions secret 등록 (hub 측 단방향) |
| `cross-repo-lock-check.yml` PR auto trigger 복원 | ✓ LAND — `on: pull_request` 복원 (workflow_dispatch + pull_request 양립) |

**MCT-177 carry over (3 항목)** — CodeReviewPL FIX iter 1 결과 박제:

| 항목 | 사유 | MCT-177 처리 |
|------|------|-------------|
| YAML config loader | Phase 2 PR1 = env + built-in only chain. YAML default 단계 미구현 (F-005 P1 fix option B = false claim 차단 위해 downgrade) | MCT-177 에서 YAML loader 신규 + `source_order` → `["env", "yaml_default", "built_in"]` 복원 + AC-2 + §8 test 3-tier chain 으로 amend |
| `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring | Phase 2 PR1 = stub (F-006 P2 fix = TODO 헤더 + docstring 확장 only) | MCT-177 에서 non-asyncio entry point (`backfill` / `compact` one-shot) 측 `signal.signal()` 등록 + collect loop chunk boundary 측 `_SHUTDOWN_REQUESTED` polling 통합 |
| cross-repo-lock-check secret 6 repo 측 secret read 검증 | 현 hub 측만 secret 등록 (단방향) | MCT-177 또는 별 Story 에서 6 repo (data/engine/web/market/signal-collector/hub) 측 secret read 의무 검증 후 LAND |

### Amendment box (MCT-177 Phase 1, 2026-05-15)

#### §D2 amendment — paper-engine daemon service (MCT-177 publish)

**MCT-177 D2 LAND (Phase 1 박제)**:

- **paper-engine service block** (`compose.yml` 신규):
  ```yaml
  paper-engine:
    image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
    container_name: mctrader-paper-engine
    profiles: ["dev", "prod"]
    command: ["paper", "--daemon"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    stop_grace_period: 60s
    depends_on:
      redis:
        condition: service_healthy
      collector:
        condition: service_healthy
  ```
- **backtest-runner** = MCT-178 carry over (별도 profile `backtest`, restart: "no", oneshot 완료 후 종료).
  MCT-177 scope 외 — MCT-178 Phase 1 박제 예정.

#### §D4 amendment — SIGTERM graceful + startup InvariantHarness scan (MCT-177 publish)

**MCT-177 D4 LAND (Phase 1 박제)**:

- **SIGTERM handler** (`mctrader-engine/src/mctrader_engine/cli.py` 신규):
  ```python
  import signal

  _SHUTDOWN_REQUESTED = False

  def _sigterm_handler(signum, frame):
      global _SHUTDOWN_REQUESTED
      _SHUTDOWN_REQUESTED = True
      logger.info("[paper-engine] SIGTERM received — graceful shutdown initiated")

  def _register_signal_handlers():
      signal.signal(signal.SIGTERM, _sigterm_handler)
      signal.signal(signal.SIGINT, _sigterm_handler)
  ```
- **60s grace period**: compose `stop_grace_period: 60s` 정합. paper daemon loop 내 chunk boundary
  에서 `if _SHUTDOWN_REQUESTED: _commit_open_positions(); break`. 60s 이내 exit 0 의무.
- **startup InvariantHarness scan**: 컨테이너 시작 시 `InvariantHarness` 8종 scan (MCT-171 SSOT).
  위반 시 warn + continue (hard abort 아님 — D17 정합). scan 완료 후 trading loop 진입.
- **owner**: mctrader-engine `src/mctrader_engine/cli.py` + compose `stop_grace_period: 60s`

#### §D10 amendment — universe override env + compose command (MCT-177 publish)

**MCT-177 D10 LAND (Phase 1 박제)**:

- **env default**: `UNIVERSE_TOP_N=50` — `.env.dev` + `.env.prod.example` 에 박제
- **compose command override**: paper daemon 측 `--universe-id <id>` CLI option 신규.
  backtest case = `--universe-id subset-30` 형태로 별 universe 지정 가능.
- **CLI 구현**:
  ```python
  @cli.command()
  @click.option("--universe-id", default=None, help="Universe override (default: env UNIVERSE_TOP_N)")
  @click.option("--daemon", is_flag=True, default=False)
  def paper(universe_id, daemon):
      if universe_id is None:
          universe_id = f"top-{os.environ.get('UNIVERSE_TOP_N', '50')}"
      if universe_id not in _UNIVERSE_REGISTRY:
          logger.error(f"Unknown universe-id: {universe_id}")
          sys.exit(1)
  ```
- **미등록 universe-id**: 즉시 exit 1 (R-MCT-177-3 mitigation).

#### §D15 amendment — Redis key prefix policy (MCT-177 publish, 신규)

**MCT-177 D15 LAND (Phase 1 박제)**:

- **Redis key prefix 3 namespace**:
  - `signal:*` — signal-collector 5종 (fear_greed / ecos / kimchi / announcement / coinglass)
  - `market:*` — mctrader-data tick + orderbook cache
  - `engine:*` — paper-engine position + strategy state
- **engine prefix env**: `REDIS_KEY_PREFIX_ENGINE=engine` (.env.dev / .env.prod 공통 default)
  ```python
  REDIS_KEY_PREFIX = os.environ.get("REDIS_KEY_PREFIX_ENGINE", "engine")
  def _engine_key(suffix: str) -> str:
      return f"{REDIS_KEY_PREFIX}:{suffix}"
  ```
- **migration (signal-collector 5종)**: 기존 unprefixed key → `signal:*` rename.
  1주일 dual write (legacy unprefixed + `signal:*` 동시 write) 후 legacy key cleanup (별 PR).
  Prometheus `redis_key_migration_dual_write_active` Gauge (1=활성) 박제.
- **cross-ref**: `docs/stories/MCT-177.md` §6 R-MCT-177-1 (dual write silent fail mitigation)

## References

- Spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- Plan: `docs/superpowers/plans/2026-05-15-mct-175-docker-stack-base.md`
- Plan (MCT-176): `docs/superpowers/plans/2026-05-15-mct-176-collector-container.md`
- Plan (MCT-177): `docs/superpowers/plans/2026-05-15-mct-177-paper-engine.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- 의존 ADR: ADR-029 (cold tier governance, §D4/§D11) / ADR-027 §D2 (HTTP Stage 1) / ADR-009 §D12
  (forward-only invariant)
- Owner Story: MCT-175 (ADR publish) / 후속 MCT-176 ~ MCT-181 (각 D 구현)
- Epic: EPIC-mctrader-docker-stack (2026-05-15 ~, 7 Story sequential)
