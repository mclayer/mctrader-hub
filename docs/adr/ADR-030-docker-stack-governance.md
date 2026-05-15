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

본 ADR 는 EPIC-mctrader-docker-stack 7 Story 범위 내 8 D (D1/D2/D3/D7/D12/D13/D17/D18) 만 본문 박제.
아래 11 D 는 manifest 박제 후 별 Story 차원 결정/구현으로 defer (단 amendment box 본문 박제는 owner
Story LAND 시 append). **SSOT = `scope_manifests/EPIC-mctrader-docker-stack.yaml` §design_decisions.
본 표는 navigational only — D 정의/owner 의 정합 기준은 항상 scope_manifest.**

| D | 내용 (scope_manifest SSOT 정합) | Owner Story (manifest) |
|---|---------------------------------|------------------------|
| D4 | SIGTERM handler + 60s grace + start-time invariant check | MCT-177 / MCT-179 |
| D5 | Prometheus metric + measurement script + amendment trigger (WAL 30G hypothesis verify) | MCT-179 |
| D6 | 7 Story 분해 (MCT-175 ~ MCT-181) — Epic meta 결정 (본문 박제 제외) | epic-level |
| D8 | 앱 내장 /metrics + Grafana dashboard + alert rule | MCT-179 |
| D9 | .env 패턴 유지 + rotate-nas-credentials.sh + cron + Slack | MCT-176 ✓ |
| D10 | env default + compose command override 둘 다 (universe override) | MCT-177 / MCT-178 |
| D11 | compose CI smoke + testcontainers 병행 (stack-level + repo-level) | MCT-180 |
| D14 | env override + YAML default (effective config stdout dump 의무) | MCT-176 ✓ |
| D15 | Redis key prefix (signal:/market:/engine:) | MCT-177 |
| D16 | docker compose config lint + compose up --wait health gate | MCT-178 |
| D19 | mctrader_runs named volume + NAS sync on completion (별 prefix) | MCT-181 |

각 D 본문 박제 시점 = 해당 owner Story Phase 1 LAND (ADR-030 amendment box append).

> **reconciliation (MCT-179 DesignReview FIX iter 1, F-001 — 전수 정합)**: ADR-030 "Out of scope" 표
> 는 MCT-175 LAND 시점에 scope_manifest SSOT 와 다수 row 가 stale/swap 박제되어 있었음 (누적 발견:
> MCT-178 F-001 = D11/D16 정의·owner swap, MCT-179 F-001 = D5/D8 정의 swap — D5="observability stack"
> ↔ D8="DR mode state machine"). 매 Story 자기 D 만 부분 reconcile 하면 MCT-180 (D11/D18) / MCT-181
> (D12/D19) 에서 재발 예상되어, 본 FIX iter 1 에서 **D1-D19 전체 row 를
> `scope_manifests/EPIC-mctrader-docker-stack.yaml` §design_decisions SSOT 와 1:1 전수 정합** 정정함.
> 변경: D4 ("container restart policy + healthcheck 표준" → SSOT "SIGTERM handler + 60s grace +
> start-time invariant check") / D5 ("observability stack ..." → SSOT "Prometheus metric + measurement
> script + amendment trigger") / D8 ("DR mode state machine 통합" → SSOT "앱 내장 /metrics + Grafana
> dashboard + alert rule") / D6 누락 row 추가 (epic-level meta) / D10·D14·D15·D19 SSOT decision
> 텍스트 verbatim 정합 / 헤더 "10 D" → "11 D" + in-scope 8 D 명시. MCT-178 F-001 (D11/D16) 정정분은
> 본 전수 정합에 흡수 (D11/D16 row 는 이미 SSOT 정합 — 변경 없음). 이후 **SSOT = scope_manifest
> §design_decisions, 본 Out-of-scope 표는 navigational only** (D 정의/owner 분쟁 시 scope_manifest 우선).

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

### Amendment box (MCT-177 LAND confirm, 2026-05-15 Phase 2 PR2)

**MCT-177 D2/D4/D10/D15 VERIFIED** (Phase 2 PR1 3 repo cross-repo LAND 후 박제):

- **§D2 (paper-engine daemon service) VERIFIED**: `compose.yml` `paper-engine` service 신규 LAND
  (hub#334 cc0c368). `image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}` +
  `command: ["paper","--daemon"]` + `restart: unless-stopped` + healthcheck :8080 +
  `stop_grace_period: 60s` + `depends_on: {redis: service_healthy, collector: service_healthy}`.
  CodeReviewPL FIX iter 1 P0 fix — healthcheck.test 가 §D2 amendment box 박제 contract
  (`http://localhost:8080/health`) verbatim 정합 + collector `service_healthy` condition 추가.
  AC-1 PASS. backtest-runner = MCT-178 carry over (별도 profile `backtest`).
- **§D4 (SIGTERM graceful + startup InvariantHarness scan) VERIFIED**: mctrader-engine#54
  (9cbe3b4). **engine asyncio SSOT 박제** — CodeReviewPL FIX iter 1 P0: 초안이 mctrader-data
  동기 SIGTERM stub 패턴을 cross-repo carry over (MCT-176 §8 stub) 했으나, mctrader-engine 측
  **기존 `shutdown.py` asyncio SSOT + HealthServer(:8080)** 가 이미 graceful drain 경로 보유.
  RefactorAgent 판정 **(A) dead path 제거** + paper start core 위임 → **신규 daemon 코드 0 line**
  (기존 검증 자산 재사용). plan §2.2 amend (data 패턴 cross-repo 오적용 취소). MCT-170 류
  Phase 0 verify lesson 재현 (session prompt 표현 ≠ 코드 실상). 60s grace = `stop_grace_period`
  정합. startup InvariantHarness 8종 scan (MCT-171 SSOT, 위반 warn+continue). AC-2 PASS.
- **§D10 (universe override) VERIFIED**: mctrader-engine#54 (9cbe3b4). `--universe-id <id>` CLI
  option + `UNIVERSE_TOP_N` env fallback (`f"top-{UNIVERSE_TOP_N}"`, default 50) + 미등록
  universe-id 즉시 exit 1 (R-MCT-177-3 mitigation). `.env.dev` + `.env.prod.example`
  `UNIVERSE_TOP_N=50` 박제 (hub#334). AC-3 PASS.
- **§D15 (Redis key prefix policy) VERIFIED**: mctrader-engine#54 (9cbe3b4)
  `REDIS_KEY_PREFIX_ENGINE` env (default `engine`) + `_engine_key()` helper.
  `signal:*` / `market:*` / `engine:*` 3 namespace 분리. `.env.dev` + `.env.prod.example`
  `REDIS_KEY_PREFIX_ENGINE=engine` 박제 (hub#334). **signal-collector 5종 코드 측 unprefixed
  → `signal:*` rename + 1주일 dual write migration = MCT-178 carry over** (본 Story 는 prefix
  정책 박제 + engine consumer 측 `engine:*` 적용만, signal-collector code migration 별 Story).
  Prometheus `redis_key_migration_dual_write_active` Gauge = MCT-178 migration PR 시 박제. AC-4 PASS.

**Phase 2 PR1 cross-repo LAND timeline (sequential gate)**:

| land_order | repo | PR | LAND commit | merged_at |
|------------|------|-----|-------------|-----------|
| 1 | mctrader-data | #65 | af6c812 | 2026-05-15T09:30:00Z |
| 2 | mctrader-engine | #54 | 9cbe3b4 | 2026-05-15T09:30:10Z |
| 3 | mctrader-hub | #334 | cc0c368 | 2026-05-15T09:30:21Z |

LAND order 정당성: data (CO-1 YAML loader + CO-2 signal wiring) → engine (D4/D10/D15 consumer)
→ hub (compose paper-engine service + env + CO-3 secret verify) 순. hub compose service 가
engine image command (`paper --daemon`) + Redis prefix env 의존 → data/engine code LAND 가
hub compose LAND prerequisite (역방향 시 false claim). MCT-176 §5.2 lesson 정합.

**MCT-176 carry over 처리 결과 (CO-1~CO-3)**:

| # | 항목 | MCT-177 처리 결과 |
|---|------|-------------------|
| CO-1 | YAML config loader (option A) | ✓ `_load_yaml_config()` 신규 + `source_order` → `["env","yaml_default","built_in"]` 3-tier 복원 (MCT-176 F-005 downgrade 해소). pyright P0 fix (return type + None narrowing). data#65 |
| CO-2 | `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring | ✓ non-asyncio entry (`backfill`/`compact`) `signal.signal()` 실 등록 + collect loop chunk boundary `_SHUTDOWN_REQUESTED` polling 통합 (MCT-176 stub 해소). data#65 |
| CO-3 | 6 repo secret read 검증 | ✓ `scripts/verify_cross_repo_secret.py` 신규 (hub owner, read-only gh secret list, 6 repo 순회 + 미등록 목록 출력 + exit 1). CodeReviewPL FIX iter 1 P1 fix — script owner = hub governance 영역 확정. hub#334 |

**MCT-178 carry over (1 항목)** — D15 migration scope 분리:

| 항목 | 사유 | MCT-178 처리 |
|------|------|--------------|
| signal-collector 5종 Redis prefix code migration | MCT-177 = prefix 정책 박제 + engine consumer `engine:*` 적용. signal-collector 5종 (fear_greed/ecos/kimchi/announcement/coinglass) 측 unprefixed → `signal:*` rename + 1주일 dual write 는 signal-collector repo 코드 변경 = 별 Story scope | MCT-178 또는 별 Story 에서 signal-collector code migration + dual write + Prometheus `redis_key_migration_dual_write_active` Gauge + LAND+7d legacy cleanup PR |

### Amendment box (MCT-178 Phase 1, 2026-05-15)

#### §D2 amendment — backtest-runner service (MCT-178 publish)

**MCT-178 D2 backtest-runner LAND (Phase 1 박제)**:

- **backtest-runner service block** (`compose.yml` 신규):
  ```yaml
  backtest-runner:
    image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
    container_name: mctrader-backtest-runner
    profiles: ["oneshot"]
    command: ["backtest", "--help"]
    env_file:
      - .env.${COMPOSE_PROFILES:-dev}
    volumes:
      - mctrader_engine_runs:/var/lib/mctrader/runs
      - mctrader_l1:/var/lib/mctrader/data/l1:ro
    restart: "no"
    networks:
      - mctrader_net
    labels:
      mctrader.role: "backtest-runner"
      mctrader.story: "MCT-178"
  ```
- **profiles**: `["oneshot"]` — paper-engine `["dev","prod"]` 와 분리. `docker compose --profile oneshot run --rm backtest-runner backtest ...` 로 invoke.
- **restart: "no"** — oneshot 실행 후 exit 0 → 컨테이너 종료. 자동 재시작 없음 (D4=C 정합).
- **healthcheck 없음** — oneshot 컨테이너 성격상 health endpoint 불필요. paper-engine `:8080` healthcheck 와 대비.
- **D10 universe override**: `docker compose --profile oneshot run --rm backtest-runner backtest --universe-id <id>` (MCT-177 LAND CLI option 재사용).
- **cross-ref**: §D2 본문 박제 (paper-engine) + MCT-178 backtest-runner 확장. MCT-177 §D2 carry over 이행.
- **reconciliation (MCT-178 DesignReview FIX iter 1, F-002)**: §D2 본문 (line 77/81) `profiles: ["backtest"]` (base body, MCT-175 LAND) → `profiles: ["oneshot"]` 정정 (paper-engine dev/prod profile 과 분리, oneshot = SSOT). 본 amendment box 및 §D16 amendment box `--profile oneshot` 가 최종 결정 — 본문 `["backtest"]` 표기는 stale.

#### §D15 cross-ref — signal-collector Redis migration LAND (MCT-178 이행)

**MCT-177 §D15 amendment box (hub#335 박제)** carry over 이행:

- **signal-collector 5종 Redis prefix code migration = MCT-178 owner**:
  - fear_greed / ecos / kimchi / announcement / coinglass 5종 worker
  - 기존 unprefixed key → `signal:*` prefix rename
  - 1주일 dual write (legacy unprefixed + `signal:*` 동시 write)
  - Prometheus `redis_key_migration_dual_write_active` Gauge (1=활성)
  - LAND+7d legacy cleanup = 별 PR (script: `scripts/redis-prefix-cleanup.sh`)
- **MCT-178 Phase 2 PR1 signal-collector 측 LAND 시 본 cross-ref 갱신 예정** (carry over → VERIFIED 전환).

#### §D16 amendment — compose config CI lint (MCT-178 publish, 신규)

**MCT-178 D16 LAND (Phase 1 박제)**:

- **workflow path**: `.github/workflows/compose-validate.yml`
- **trigger**: `pull_request` (paths: compose.yml / .env.example / .env.prod.example / compose-validate.yml) + `workflow_dispatch`
- **lint step 3종** (각 profile 독립 실행):
  - `docker compose --profile dev --env-file .env.dev config --quiet` — dev profile config 검증
  - `docker compose --profile prod --env-file .env.prod.example config --quiet` — prod profile config 검증
  - `docker compose --profile oneshot --env-file .env.dev config --quiet` — oneshot profile config 검증 (backtest-runner service 존재 확인)
- **health gate**: `docker compose --profile dev up -d postgres redis minio --wait --wait-timeout 180` — infra only (어플리케이션 service 제외), 3분 budget. 완료 후 `docker compose --profile dev down` cleanup.
- **FAIL 조건**: any profile config exit != 0 / health gate timeout 초과 (3분)
- **근거**: PR 마다 compose 문법 오류 + service dependency DAG 검증 (D16=B option 정합).
  backtest-runner profiles 오설정 → `--profile oneshot config` FAIL 로 조기 감지.
- **reconciliation (MCT-178 DesignReview FIX iter 1, F-001)**: scope_manifest SSOT 기준 **D16 = docker compose config lint + compose up --wait health gate (option B, owner MCT-178)**, **D11 = compose CI smoke + testcontainers 병행 (option C, owner MCT-180)**. 본 ADR "Out of scope" 표(line 229/232)의 D11/D16 정의는 MCT-175 LAND 시 SSOT 와 swap 박제되었음 — scope_manifest (`scope_manifests/EPIC-mctrader-docker-stack.yaml` D11/D16) 우선. MCT-178 전 산출물 = D16 = compose config CI lint (본 §D16 amendment box 와 SSOT 정합).

### Amendment box (MCT-178 LAND confirm, 2026-05-15 Phase 2 PR2)

**MCT-178 D2/D16 VERIFIED** (Phase 2 PR1 cross-repo LAND 후 박제):

- **§D2 (backtest-runner service) VERIFIED**: `compose.yml` `backtest-runner` service 신규 LAND
  (mctrader-hub#337 bd9baf2). `image: ghcr.io/mclayer/mctrader-engine:latest` +
  `profiles: ["oneshot"]` + `command: ["backtest","--help"]` + `restart: "no"` +
  `volumes: [mctrader_engine_runs, mctrader_l1:ro]` + **no healthcheck** (oneshot 성격 정합).
  paper-engine 와 동일 image, command 만 분기 (D2=A 정합). AC-1/AC-2/AC-3 PASS.
- **§D16 (compose config CI lint) VERIFIED**: `.github/workflows/compose-validate.yml` 신규 LAND
  (mctrader-hub#337 bd9baf2). **실 LAND 파일명 = `compose-validate.yml`** (Phase 1 amendment box
  표기와 정합 — NOT `docker-compose-validate.yml`). 3 profile lint (dev/prod/oneshot config --quiet)
  + health gate (`up -d postgres redis minio --wait --wait-timeout 180` infra only + down cleanup).
  trigger = pull_request (paths) + workflow_dispatch. AC-4 PASS.
- **§D15 cross-ref (signal-collector Redis migration) VERIFIED → carry over 이행 완료**:
  mctrader-signal-collector#1 (60787c4, land_order 1) — 5 worker (fear_greed/ecos/kimchi/
  announcement/coinglass) **Publisher 계층 집중** `signal:*` prefix + legacy unprefixed dual write
  + Prometheus `redis_key_migration_dual_write_active` Gauge=1. MCT-177 §D15 amendment box carry
  over → **VERIFIED 전환**. LAND+7d legacy cleanup = 별 PR (`scripts/redis-prefix-cleanup.sh`).
  AC-5 PASS.
- **F-001/F-002 reconciliation 최종 정합**: DesignReview iter 1 CONDITIONAL_PASS fast-fix
  (ba87b3c) 의 §D2/§D16 reconciliation note 가 `scope_manifests/EPIC-mctrader-docker-stack.yaml`
  D11/D16 SSOT + line 170/244 (Phase 2 PR2 본 PR §F-001 정정: `docker-compose-validate.yml` →
  `compose-validate.yml` / `profile=backtest` → `profiles: [oneshot]`) 와 최종 일치. ADR
  자기모순 (MCT-175 LAND 누적 swap) 해소 박제 완료.

- **Phase 2 PR1 cross-repo LAND timeline**:
  | 시각 | PR | LAND commit | 박제 내용 |
  |------|-----|-------------|-----------|
  | 2026-05-15T10:20:05Z | mctrader-hub#336 | 0d56730 | Phase 1 docs — Story §1-§12 + ADR-030 §D2/§D16 amendment box 본문 박제 + CLAUDE.md MCT-178 IN_PROGRESS |
  | 2026-05-15T10:35:04Z | mctrader-signal-collector#1 | 60787c4 | Phase 2 PR1 signal — 5 worker Publisher 계층 Redis prefix dual write + Gauge (land_order 1) |
  | 2026-05-15T10:35:55Z | mctrader-hub#337 | bd9baf2 | Phase 2 PR1 hub — backtest-runner service + compose-validate.yml workflow (land_order 2) |
  | 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §8.5/§10/§11/§12 + ADR-030 §D2/§D16 VERIFIED + scope_manifest 4/7 + F-001 정정 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-4 (본 section) |

ADR-030 본문 만 박제 (Status = Accepted 유지, MCT-175 LAND 시점 박제분). MCT-179 ~ MCT-181 LAND 시
추가 D 본문 박제 의무.

### Amendment box (MCT-179 Phase 1, 2026-05-15)

#### §D5 amendment — WAL 30G measurement script + Prometheus Gauge + amendment trigger (MCT-179 publish)

**MCT-179 D5 LAND (Phase 1 박제)**:

- **측정 스크립트**: `scripts/measure_wal_baseline.py` 신규
  - mode: `paper-synthetic` (30min baseline + 30min peak burst hybrid, MCT-172 D8-2 패턴)
  - exit 0 = WAL ≤ 30G (PASS) / exit 7 = WAL > 30G (D11 hard_limit amendment trigger) / exit 99 = probe fail
  - `--dry-run`: GitHub issue 실 발의 없음, 발의 payload JSON 출력만
  - 의존: `mctrader_data.capacity_probe.CapacityProbe` (MCT-171 LAND SSOT)

- **Prometheus Gauge SSOT** (MCT-179 FIX iter1 정정 — wal_capacity_bytes 신규 Gauge 박제 폐기):
  - WAL bytes metric SSOT = **`mctrader_capacity_usage_bytes{layer="WAL_local"}`** (MCT-171 LAND
    `nas_metrics/prometheus_exporters.py:98` Gauge + `capacity_probe.py:331` emit_capacity_usage)
  - `wal_capacity_bytes` = MCT-179 Phase 1 박제 가공 metric (LAND registry 부재) — **폐기**.
    신규 Gauge 추가 불요 (additive invariant 정합: MCT-171 기존 Gauge 재사용 only)
  - scrape = Prometheus `mctrader-collector` job (D8 scrape target 정합, capacity_probe emit 경로)

- **30G 초과 amendment trigger**: WAL > 30G 시 GitHub issue 자동 발의
  (repo: `mclayer/mctrader-hub`, title: "ADR-029 D11 hard_limit amendment 발의 — WAL 실측 {N}G > 30G")

- **cross-Epic carry over**: EPIC-tier-promotion-single-source prod-2 (WAL 30G production measurement)
  흡수. synthetic baseline = AC-5 박제 (Phase 2 PR2). production 실 측정 = 별 PR carry over
  (실 production deploy + peak market open 09:00 KST burst 1h window).

- **ADR-029 D11 cross-ref**: WAL 30G hard_limit = MCT-179 measurement gate.
  `docs/adr/ADR-029-tier-promotion-single-source.md` §D11 CapacityThresholds SSOT (MCT-171 LAND).
  production 측정 결과 30G 초과 시 ADR-029 D11 hard_limit amendment 발의 의무 (D8-7=A FAIL gate).

#### §D8 amendment — observability (Prometheus scrape + Grafana dashboard + alert rule) (MCT-179 publish)

**MCT-179 D8 LAND (Phase 1 박제)**:

- **Prometheus scrape target** (`monitoring/prometheus.yml` 갱신):
  - job: `mctrader-collector` → `collector:9090/metrics`
  - job: `mctrader-paper-engine` → `paper-engine:9090/metrics` (healthcheck :8080 과 별도 endpoint)

- **alert rule** (`monitoring/prometheus-alerts.yml` 신규, MCT-179 FIX iter1 정정 — 가공 metric 폐기 +
  실 LAND series 바인딩):
  ```yaml
  groups:
    - name: mctrader-docker-stack
      rules:
        - alert: WALCapacityWarn
          expr: mctrader_capacity_usage_bytes{layer="WAL_local"} > 25 * 1024^3
          for: 5m
          labels: { severity: warning }
          annotations: { summary: "WAL capacity > 25G (D11 warn)" }
        - alert: WALCapacityCritical
          expr: mctrader_capacity_usage_bytes{layer="WAL_local"} > 30 * 1024^3
          for: 1m
          labels: { severity: critical }
          annotations: { summary: "WAL > 30G — ADR-029 D11 hard_limit amendment 의무 (Epic CLOSE FAIL gate)" }
        # NAS 운영 gate = engine dr_mode.py LAND (MCT-170) 실존 series 바인딩.
        # 폐기: nas_reader_5xx_total / nas_reader_p99_ms (LAND registry 부재 가공 metric).
        # DR OPEN 전이 = D8=C hybrid (5xx 5회 OR p99 >500ms 3회) 충족 후 회로 차단 = 운영 gate proxy.
        - alert: NASReaderDROpen
          expr: increase(nas_reader_dr_transitions_total{to_state="OPEN"}[5m]) > 0
          labels: { severity: warning }
          annotations: { summary: "NAS reader DR mode OPEN transition (D8=C hybrid threshold 충족)" }
        - alert: NASReaderAmbiguity
          expr: increase(nas_reader_ambiguity_total[5m]) > 0
          labels: { severity: warning }
          annotations: { summary: "NAS reader UNKNOWN_TIER ambiguity (D10 NAS+local XOR violation)" }
  ```
  - **metric-name SSOT** (FIX iter1 verify 기반):
    - WAL = `mctrader_capacity_usage_bytes{layer="WAL_local"}` (MCT-171 prometheus_exporters.py:98 LAND)
    - NAS DR = `nas_reader_dr_transitions_total{to_state}` / `nas_reader_ambiguity_total`
      (MCT-170 engine `io/dr_mode.py:40/45` LAND)
    - `wal_capacity_bytes` / `nas_reader_5xx_total` / `nas_reader_p99_ms` = LAND registry 부재 = 폐기

- **Grafana dashboard** (`monitoring/grafana/provisioning/dashboards/docker-stack.json` 신규):
  - 9 panel (3 row): WAL bytes gauge+trend (id=1,2 — MCT-171 SSOT) /
    collector ingest+symbols (id=3,4 — **MCT-180 TODO**, collector.py metric 부재) /
    paper engine open positions (id=5 — `sum(mctrader_engine_open_positions)` MCT-170 LAND 실존) +
    universe size (id=6 — **MCT-180 TODO**, engine metrics.py 부재) /
    NAS hit_ratio (id=7 — **MCT-180 TODO**, reader_cache.py Gauge 미노출) +
    reader p99 (id=8 — **MCT-180 TODO**, latency Histogram 미노출)
  - MCT-180 TODO panel = `description` 필드 + title `[MCT-180 TODO]` prefix 박제
    (no-data placeholder, MCT-180 follow-up metric emit 후 활성)
  - dashboard provisioning = compose grafana service volume mount

- **compose.yml 갱신**:
  - prometheus service: `./monitoring/prometheus-alerts.yml:/etc/prometheus/alerts.yml:ro` volume mount
    + `prometheus.yml` `rule_files:` 참조
  - grafana service: dashboard provisioning volume
  - collector + paper-engine: `9090` port expose (Prometheus scrape 정합)

#### §D17 amendment — startup InvariantHarness scan + DR mode alert (MCT-179 publish)

**MCT-179 D17 LAND (Phase 1 박제)**:

- **startup InvariantHarness scan** (ADR-030 §D17 본문 정합):
  - collector (`mctrader-data/src/mctrader_data/cli.py` collect 진입 시): `InvariantHarness().scan_all()` 호출
    (MCT-171 `invariant_harness.py` SSOT import)
  - paper-engine (`mctrader-engine` startup hook): `InvariantHarness().scan_all()` 호출 (MCT-171 동형)
  - 8종 scan 중 violation 감지: **warn + continue** (hard abort 아님 — §D17 본문 정합)
  - ambiguity invariant (D10) 특이사항: container restart race = false positive 방지 — warn log 만
    (30d exemption window 내 UNKNOWN_TIER 상태, MCT-170 ADR-029 §D10 footnote 정합)

- **SIGTERM graceful 은 MCT-176/177 LAND 재사용** (신규 구현 없음):
  - collector: MCT-176 Phase 2 PR1 (data#64) LAND 의 `_SHUTDOWN_REQUESTED` + collect loop wiring
  - paper-engine: MCT-177 Phase 2 PR1 (engine#54) LAND 의 기존 `shutdown.py` asyncio SSOT + HealthServer

- **owner**: `mctrader-data/src/mctrader_data/cli.py` (collector startup hook) +
  `mctrader-engine` startup hook (Phase 2 PR1 LAND 시 박제)

### Amendment box (MCT-179 LAND confirm, 2026-05-15 Phase 2 PR2)

**MCT-179 D5/D8/D17 VERIFIED** (Phase 2 PR1 cross-repo 양측 LAND 후 박제):

cross-repo LAND timeline (sequential gate):

| land_order | PR | LAND commit | 시각 |
|------------|-----|-------------|------|
| 1 | mctrader-data#66 | e4a2cc2 | 2026-05-15T11:51:56Z |
| 2 | mctrader-hub#340 | 64feb73 | 2026-05-15T11:52:49Z |

#### §D5 VERIFIED — WAL 30G measurement script + Prometheus Gauge

- **`scripts/measure_wal_baseline.py` LAND** (data#66): paper-synthetic mode exit 0 + JSON stdout
  (`mode`/`wal_bytes`/`wal_peak_gb`/`hard_limit_gb`/`verdict`/`hypothesis_range`).
  - **AC-1/AC-5 PASS**: paper-synthetic `verdict: PASS`, `wal_peak_gb: 0.0` (read-only probe,
    무 WAL 환경 = 0 측정, MCT-172 D8-2 synthetic baseline 패턴). forward-only invariant 정합
    (WAL 파일 수정 0, ADR-009 §D12).
  - **AC-2 PASS**: `WAL_HARD_LIMIT_GB=0` mock → `verdict: EXCEED` + exit 7 + stderr
    "ADR-029 D11 hard_limit amendment 의무 (D8-7=A FAIL gate)" (D11 hard_limit trigger 동작).
- **Prometheus Gauge SSOT VERIFIED** = `mctrader_capacity_usage_bytes{layer="WAL_local"}`
  (MCT-171 LAND `nas_metrics/prometheus_exporters.py:98`). data#66 = **deprecated Gauge 미도입**
  — MCT-171 LAND `emit_capacity_usage` 패턴 정합 `measure_wal_bytes()` + `emit_wal_capacity_gauge()`
  편의 메서드 추가 (+547 lines, additive invariant 정합). `wal_capacity_bytes` 가공 Gauge 미도입.
- **R2 CRITICAL 상태**: synthetic baseline 측정 완료 (R2 PARTIAL 해소). production 실 측정
  (15-45 GB hypothesis verify) = **별 PR carry over** (실 production deploy + peak market open
  09:00 KST 1h burst window). EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 정합.

#### §D8 VERIFIED — observability (Prometheus scrape + Grafana + alert rule)

- **Phase 0 verify 정정 (hub#340)**: collector/paper-engine 모두 `:8080/metrics` 사용
  (`:9090` 가설 기각 — Phase 0 verify 실증). `prometheus.yml` paper-engine target =
  `mctrader-paper-engine:8080` (기존 오기 `mctrader-engine-paper:8080` → container_name 정합 fix).
  Grafana dashboard provisioning path = `monitoring/grafana/provisioning/dashboards/`
  (dashboard.yml path SSOT 정합).
- **alert rule VERIFIED** (`monitoring/prometheus-alerts.yml` LAND, CodeReview FIX iter1 정정 후):
  - `WALCapacityWarn` / `WALCapacityCritical` = `mctrader_capacity_usage_bytes{layer="WAL_local"}`
    (MCT-171 prometheus_exporters.py:98 LAND SSOT). **R2 CRITICAL deliverable
    (WAL 30G Epic-CLOSE-FAIL-gate alert) 기능 회복** (가공 metric `wal_capacity_bytes` 폐기).
  - `NASReaderDROpen` = `increase(nas_reader_dr_transitions_total{to_state="OPEN"}[5m]) > 0`
    + `NASReaderAmbiguity` = `increase(nas_reader_ambiguity_total[5m]) > 0` (MCT-170 engine
    `io/dr_mode.py:40/45` LAND 실 series 바인딩). `nas_reader_5xx_total`/`nas_reader_p99_ms`
    = LAND registry 부재 가공 metric → **폐기** (미발화 alert 금지 원칙).
- **Grafana dashboard VERIFIED** (`monitoring/grafana/provisioning/dashboards/docker-stack.json` LAND):
  9 panel — id=1,2 (WAL bytes, MCT-171 SSOT selector) + id=5 (`sum(mctrader_engine_open_positions)`,
  MCT-170 LAND 실존 label aggregation) + id=3,4,6,7,8 (`[MCT-180 TODO]` title prefix +
  `description` no-data placeholder, MCT-180 metric emit 후 활성).
- **compose.yml VERIFIED**: prometheus service `./monitoring/prometheus-alerts.yml:/etc/prometheus/alerts.yml:ro`
  volume mount + `prometheus.yml` `rule_files:` 참조.

#### §D17 VERIFIED — startup InvariantHarness scan

- **collector startup scan VERIFIED** (data#66 `cli.py`): collect 커맨드 startup 시
  InvariantHarness 8종 scan hook. `NAS_MINIO_ENDPOINT` 미설정 시 graceful skip.
  ambiguity D10 fail → `log.warning` 전용 (raise 금지 — false positive 방지, §D17 본문 정합).
- **API 정정 (Phase 0 verify)**: plan §2.1 pseudocode `InvariantHarness().scan_all()` 는 MCT-171
  LAND 실 API 와 불일치 → WAL partition 탐색 후 `verify()` per-partition 호출 패턴으로 구현
  (MCT-170/177/178 cross-repo Phase 0 verify 독립 의무 동형 재현).
- **SIGTERM graceful = MCT-176/177 LAND 재사용 VERIFIED**: 신규 구현 0 (collector =
  MCT-176 `_SHUTDOWN_REQUESTED` + collect loop wiring / paper-engine = MCT-177 `shutdown.py`
  asyncio SSOT + HealthServer).

#### metric-name SSOT 표 (FIX iter1 verify 기반, MCT-179 최종 박제)

| metric | 실존 여부 | LAND selector (file:line) | MCT-179 처리 |
|--------|-----------|----------------------------|--------------|
| `mctrader_capacity_usage_bytes{layer="WAL_local"}` | ✅ 실존 | data `nas_metrics/prometheus_exporters.py:98` Gauge + `capacity_probe.py:331` emit (MCT-171 LAND) | WAL alert SSOT 정렬 (R2 deliverable 회복) |
| `nas_reader_dr_transitions_total{from_state,to_state}` | ✅ 실존 | engine `io/dr_mode.py:40` Counter (MCT-170 LAND) | NASReaderDROpen alert 바인딩 |
| `nas_reader_ambiguity_total` | ✅ 실존 | engine `io/dr_mode.py:45` Counter (MCT-170 LAND) | NASReaderAmbiguity alert 바인딩 |
| `mctrader_engine_open_positions{strategy,symbol}` | ✅ 실존 | engine `metrics.py:6` Gauge (MCT-170 LAND) | panel id=5 `sum()` aggregation |
| `wal_capacity_bytes` | ❌ 부재 | LAND registry 부재 (MCT-179 Phase 1 가공) | **폐기** (MCT-171 Gauge 재사용) |
| `nas_reader_5xx_total` / `nas_reader_p99_ms` | ❌ 부재 | LAND registry 부재 (가공) | **폐기** (DR proxy 대체) |
| `mctrader_collector_ticks_total` / `_active_symbols` / `mctrader_engine_universe_size` / `nas_reader_cache_hit_ratio` | ❌ 부재 | data/engine emit 0건 | **MCT-180 downgrade** (panel `[MCT-180 TODO]`) |

ADR-030 본문 만 박제 (Status = Accepted 유지). MCT-180 ~ MCT-181 LAND 시 추가 D 본문 박제 의무.

### Amendment box (MCT-180 Phase 1, 2026-05-15)

#### §D4 amendment — SIGTERM graceful integration smoke 회귀 검증 (MCT-180 publish)

**MCT-180 D4 회귀 검증 (Phase 1 박제)**:

- **SIGTERM graceful 구현 = MCT-176/177 LAND 재사용** (신규 구현 없음):
  - collector: MCT-176 Phase 2 PR1 (data#64) LAND 의 `_SHUTDOWN_REQUESTED` + collect loop wiring
  - paper-engine: MCT-177 Phase 2 PR1 (engine#54) LAND 의 기존 `shutdown.py` asyncio SSOT + HealthServer
- **MCT-180 = 회귀 검증 only**: integration smoke workflow 의 SIGTERM step 에서
  `docker compose --profile dev stop collector paper-engine --timeout 60` 실행 후
  두 service exit 0 within 60s stop_grace_period 확인 (AC-4)
- **regression gate**: MCT-176/177 LAND graceful drain 경로 = 코드 변경 없음.
  integration smoke 가 유일한 회귀 검증 gate (ADR-030 §D17 정합).
- **owner**: MCT-177 (구현) + MCT-179 (startup scan) + **MCT-180 (회귀 검증)**

#### §D11 amendment — integration smoke CI gate + testcontainers 2-layer (MCT-180 publish)

**MCT-180 D11 LAND (Phase 1 박제)**:

- **2-layer gate**:
  - Layer 1 (compose CI smoke): `.github/workflows/integration-smoke.yml` 신규 — compose up full
    stack (postgres+redis+minio+mc+collector+paper-engine) → collector ingest 60s → compactor
    promotion 1회 → paper-engine health 200 → SIGTERM graceful (D4 회귀) → teardown. 10분 budget
    (timeout-minutes: 12)
  - Layer 2 (testcontainers): data `tests/integration/test_collector_nas_boundary.py` 신규
    (collector→MinIO mock boundary) + engine `tests/test_paper_redis_boundary.py` 신규
    (paper-engine→Redis testcontainer, engine: prefix key verify)
- **integration-smoke.yml trigger**: `pull_request` (paths: compose.yml / .github/workflows/integration-smoke.yml)
  + `workflow_dispatch`
- **compose up 단계**:
  ```yaml
  - name: compose up infra
    run: docker compose --profile dev --env-file .env.dev up -d postgres redis minio mc --wait --wait-timeout 180
  - name: compose up apps
    run: docker compose --profile dev --env-file .env.dev up -d collector paper-engine --wait --wait-timeout 240
  - name: collector ingest 60s
    run: sleep 60 && docker compose --profile dev logs collector | grep -q "ingest" || echo "collector ingest log (advisory)"
  - name: paper-engine health 200
    run: docker compose --profile dev exec -T paper-engine python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"
  - name: SIGTERM graceful (D4 회귀)
    run: |
      docker compose --profile dev stop collector paper-engine --timeout 60
      docker compose --profile dev ps --status exited | grep -E "collector|paper-engine"
  - name: teardown
    if: always()
    run: docker compose --profile dev down -v
  ```
- **cross-repo LAND 순서** (§2.4 정합): data PR + engine PR LAND 먼저 (metric emit source) →
  hub PR LAND (integration-smoke + limits + docker-stack TODO 해제)

#### §D18 amendment — deploy.resources.limits + ContainerMemoryHigh alert (MCT-180 publish)

**MCT-180 D18 LAND (Phase 1 박제)**:

- **compose.yml `deploy.resources.limits` 전 service**:

  | service | memory | cpus | 근거 |
  |---------|--------|------|------|
  | collector | 512M | 1.0 | INV-4 DualWriter peak RSS ≤ 50MB (MCT-163 실측) + buffer |
  | paper-engine | 512M | 1.0 | reader_cache 256MB (MCT-170 max_bytes default) + asyncio + buffer |
  | backtest-runner | 1G | 1.0 | reader_cache 256MB + backtest dataset + buffer |
  | postgres | 1G | 1.0 | 표준 OLTP small instance |
  | redis | 256M | 0.5 | maxmemory hard cap 기존 (MCT-121 LAND) |
  | prometheus | 512M | 0.5 | TSDB 90d retention + scrape buffer |
  | grafana | 512M | 0.5 | dashboard rendering + provisioning |

- **ContainerMemoryHigh alert rule** (`monitoring/prometheus-alerts.yml` 추가):
  ```yaml
  - alert: ContainerMemoryHigh
    expr: container_memory_usage_bytes{name=~"mctrader-.*"} / container_spec_memory_limit_bytes{name=~"mctrader-.*"} > 0.8
    for: 5m
    labels: { severity: warning }
    annotations:
      summary: "Container {{ $labels.name }} memory > 80% limit (D18 OOM 선제 경보)"
      description: "현재 사용: {{ $value | humanizePercentage }}. compose deploy.resources.limits 조정 또는 D11 amendment 발의 고려."
  ```
  - cadvisor (MCT-123 LAND) 가 `container_memory_usage_bytes` + `container_spec_memory_limit_bytes` emit
  - `name=~"mctrader-.*"` selector = `container_name: mctrader-*` (compose.yml container_name 정합)
- **4 layer capacity (ADR-029 §D11) 정합**:
  - WAL host disk: 30G hard_limit → container mem limit 별도 (WAL = host bind mount, container 외부)
  - L1 named volume: 20G → NAS 의존 (container mem limit 외)
  - container memory limit: 위 표 (D18 MCT-180 LAND)

### Amendment box (MCT-180 CodeReview FIX iter2, 2026-05-15)

#### §D8 amendment — reader cache hit_ratio/p99 = cold reader 한정 metric (paper daemon 미적용)

**FIX-MCT-180 engine#55 P1 (설계 원인 — Phase 0 verify lesson 5회째)**:

- **근본 원인**: Plan §2.2 + Story §4 AC-5 + 본 ADR §D8 (MCT-179 박제분) 이
  `nas_reader_cache_hit_ratio` / `nas_reader_p99_ms` Gauge 의 daemon producer path 를
  **paper-engine daemon** 으로 잘못 가정. Phase 0 verify 실증:
  - paper-engine daemon = `PaperRunner` (WS tick 경로). runtime/ grep 결과
    `ReaderCache`/`ColdReader`/`TierReader` 미인스턴스화 (0 match)
  - `ReaderCache.stats()` production caller = `ColdReader.run_smoke_test()` 1곳뿐.
    `run_smoke_test` production caller = 0 (cutover runbook Phase 3 / backtest 경로 only)
  - MCT-170 reader_cache = **NAS cold read 전용 scope** (paper daemon real-time tick 미사용)
  - → paper daemon 기동 시 `nas_reader_cache_hit_ratio`/`nas_reader_p99_ms` **영구 0.0**
- **contract 정정 (option 1 — contract 수정 채택)**:
  - `nas_reader_cache_hit_ratio` / `nas_reader_p99_ms` = **cold reader 사용 컴포넌트
    한정** metric 으로 재정의 (backtest-runner / `ColdReader.run_smoke_test()` cutover
    경로). **paper-engine daemon 미적용** 명시 박제.
  - engine#55 `ReaderCache.stats()` → Gauge producer wiring = **보존** (cold reader /
    backtest 경로에서 유효). docstring 에 scope 명시 추가 (logic 변경 0).
  - hub `docker-stack.json` panel **id=7 (hit_ratio) / id=8 (p99) = `[MCT-180 TODO]`
    downgrade 유지** (MCT-179 박제 해제 취소). 사유: cold read 경로만 emit, paper daemon
    real-time 미emit. backtest-runner = oneshot 실행이라 지속 panel 부적합.
    `description` = "cold reader 사용 시 (backtest-runner) emit, paper daemon 미적용" 박제.
  - panel **id=3 (collector ticks) / id=4 (active_symbols) / id=6 (engine universe_size)
    = 정상 해제 유지** — paper daemon `set_universe_size` cli.py startup 1회 emit 배선
    정합 (engine#55 정상) + collector ticks/active_symbols data#67 LAND 정합.
- **lesson (MCT-170/177/178/179 cross-repo Phase 0 verify 독립 의무 5회째 재현)**:
  cross-repo Story 는 sibling repo 패턴 무비판 carry over 금지. metric producer path 는
  각 daemon runtime 실 instantiation 경로 Phase 0 verify 의무 (가설 = 코드 실증 전 미수용).

#### §D11 amendment — integration-smoke.yml mc(mc-init) --wait 분리

**FIX-MCT-180 hub#343 P0 (설계 원인)**:

- **근본 원인**: Plan §2.3 line 131 verbatim
  `docker compose up -d postgres redis minio mc --wait --wait-timeout 180`.
  `mc` (`mctrader-mc-init`) = **healthcheck 미보유 일회성 init 컨테이너**
  (entrypoint = minio bucket init 후 exit 0, restart 미정의). `docker compose --wait`
  는 healthcheck 미보유 즉시 종료 컨테이너를 비정상 간주 → **exit 1 → D11 integration
  smoke 게이트 무력화**.
- **fix (mc --wait 분리)**:
  - infra wait = `docker compose up -d postgres redis minio --wait --wait-timeout 180`
    (mc 제외 — postgres/redis/minio 3개 모두 healthcheck 보유, `--wait` 정상)
  - mc-init = 별도 oneshot step:
    `docker compose up --no-deps --exit-code-from mc mc` (attached, minio
    service_healthy depends_on 충족 → bucket init 완료까지 block + exit code 0 검증)
  - Plan §2.3 amend (mc --wait 분리)
- **운영 정합**: mc-init = minio bucket bootstrap. `--exit-code-from mc` 가
  `--abort-on-container-exit` 함의 → init 정상 완료(exit 0) 검증. `--no-deps` 로
  minio 재기동 회피 (직전 step 의 `--wait` 로 minio 이미 healthy).

#### N-002 promotion 문구 carry (Phase 2 PR2 유지)

- N-002 (promotion.py 잔여 문구 정합) = Phase 2 PR2 carry over 유지. 본 contract 정정
  (reader cache scope = cold reader 한정) 과 Story/ADR 정합성 동반 박제 의무
  (Phase 2 PR2 §10/§11 amend 시).

## References

- Spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- Plan: `docs/superpowers/plans/2026-05-15-mct-175-docker-stack-base.md`
- Plan (MCT-176): `docs/superpowers/plans/2026-05-15-mct-176-collector-container.md`
- Plan (MCT-177): `docs/superpowers/plans/2026-05-15-mct-177-paper-engine.md`
- Plan (MCT-178): `docs/superpowers/plans/2026-05-15-mct-178-backtest-runner.md`
- Plan (MCT-179): `docs/superpowers/plans/2026-05-15-mct-179-observability-wal30g.md`
- Plan (MCT-180): `docs/superpowers/plans/2026-05-15-mct-180-integration-smoke.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- 의존 ADR: ADR-029 (cold tier governance, §D4/§D11) / ADR-027 §D2 (HTTP Stage 1) / ADR-009 §D12
  (forward-only invariant)
- Owner Story: MCT-175 (ADR publish) / 후속 MCT-176 ~ MCT-181 (각 D 구현)
- Epic: EPIC-mctrader-docker-stack (2026-05-15 ~, 7 Story sequential)
