---
story_key: MCT-177
plan_title: "paper-engine daemon + SIGTERM graceful + universe override + Redis prefix + carry over 3건"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 3
depends_on: MCT-176 (LAND 2026-05-15, hub#330+#331+#332 + data#64)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D2_paper, D4_paper, D10, D15]
carry_over_from_mct176:
  - "YAML config loader (option A) — mctrader-data source_order 3-tier 복원"
  - "_register_signal_handlers + _SHUTDOWN_REQUESTED collect loop wiring (data)"
  - "cross-repo-lock-check secret 6 repo 측 secret read 검증"
---

# MCT-177 Implementation Plan — paper-engine daemon

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** mctrader-hub/compose.yml 의 paper-engine service 추가 (D2 daemon, restart unless-stopped) + mctrader-engine CLI SIGTERM graceful + Redis key prefix (D15) + universe override (D10) + MCT-176 carry over 3건 (data YAML loader + signal wiring + secret 6 repo read).

**Architecture:**
- **D2 paper daemon**: compose.yml `paper-engine` service 신규 (image: ghcr.io/mclayer/mctrader-engine, command: `paper --daemon`, restart unless-stopped, healthcheck 8080). backtest-runner = MCT-178.
- **D4 SIGTERM graceful**: mctrader-engine cli.py 측 signal.SIGTERM handler + 60s grace 박제. paper daemon position state graceful close (open position commit 후 exit).
- **D10 universe override**: env `UNIVERSE_TOP_N=50` default (.env.dev/.env.prod) + compose command `--universe-id <id>` override 가능. paper daemon 측 50-sym universe.
- **D15 Redis prefix**: Redis key prefix `signal:` (signal-collector) / `market:` (mctrader-data) / `engine:` (paper-engine). signal-collector 5종 기존 prefix migration 또는 신규 적용.
- **MCT-176 carry over 3건**:
  - **YAML loader**: data repo cli.py `effective-config` 의 source_order 3-tier 복원. `/etc/mctrader/config.yaml` optional read.
  - **signal wiring**: data repo `collect` command 측 `_register_signal_handlers()` 호출 + collect loop chunk boundary `while not _SHUTDOWN_REQUESTED` 적용.
  - **secret 6 repo**: 6 repo (data/engine/web/market/signal-collector/hub) 측 `MCTRADER_CROSS_REPO_TOKEN` secret read 검증. 등록 부재 repo 식별 + 박제.

**Tech Stack:** Docker Compose v2 (paper-engine service) / Python 3.12 (engine CLI + signal handler) / Redis 7 (key prefix) / YAML config

**PR Split:**
- **Phase 1 PR** (hub, docs only): Story + ADR-030 §D2/§D4/§D10/§D15 amendment box + CLAUDE.md
- **Phase 2 PR1** (cross-repo: hub + engine + data):
  - **hub PR**: compose.yml paper-engine service + .env.dev/.env.prod UNIVERSE_TOP_N + Redis prefix env
  - **engine PR**: cli.py SIGTERM handler + universe-id override + Redis key prefix + startup invariant scan
  - **data PR**: YAML loader 복원 (option A) + collect signal wiring + secret read verify script
- **Phase 2 PR2** (hub, 박제): Story §11 retro + ADR-030 amend confirm + Epic milestone 3/7 + RETRO + EPIC-RESULTS §Story-3

---

## §1 Phase 1 PR (mctrader-hub, docs only)

### 1.1 Story MCT-177.md 작성

**Files:** Create `docs/stories/MCT-177.md`

- [ ] §1-§6: 동기 / Epic context / Risk acceptance / AC 5건 / INV / Risk
  - AC-1 (D2): `docker compose --profile dev/prod up paper-engine` healthcheck 8080 PASS
  - AC-2 (D4): paper daemon SIGTERM → 60s grace 내 open position close + WAL flush + exit 0
  - AC-3 (D10): UNIVERSE_TOP_N=50 .env.dev 적용 verify + compose command `--universe-id alt-30` override 가능
  - AC-4 (D15): Redis key prefix `signal:` / `market:` / `engine:` 3 namespace 분리 verify (redis-cli SCAN)
  - AC-5 (carry over): data YAML loader 복원 + signal wiring + 6 repo secret read 검증 결과 박제

- [ ] §6.5 Change Plan §7/§11 N/A 박제 (MCT-175 P0 lesson 패턴)
  - §7 security: paper daemon = trust boundary (NAS read + position state write). Redis key prefix = data consumer 분리. SecurityArch carrier MCT-176 §D9 정합.
  - §7.4 op-risk: SIGTERM graceful (60s grace) + restart unless-stopped + 5xx alert. ADR-030 §D17 정합.
  - §11 data-migration: Redis prefix migration = signal-collector 5종 기존 key namespace 변경 (legacy unprefixed → `signal:*` 일괄 rename). rollback = legacy key parallel write (1주일 dual write).
  - §11.6 idempotency: paper daemon restart = state recovery from Redis `engine:position:*` (idempotent). YAML loader = read-only.

- [ ] §7-§10: Dependencies / Test contract / Plan reference / FIX Ledger 빈 표
- [ ] §11/§12: placeholder

### 1.2 ADR-030 amendment

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] §D2 amendment box (MCT-177 publish):
  - paper-engine service: image + command + restart + healthcheck + stop_grace 60s
  - backtest-runner = MCT-178 (separate profile)
- [ ] §D4 amendment box (MCT-177 publish):
  - SIGTERM handler: signal.signal(SIGTERM, _handler)
  - 60s grace: docker compose stop_grace_period 60s
  - startup invariant: InvariantHarness 8종 scan (MCT-171 LAND)
- [ ] §D10 amendment box (MCT-177 publish):
  - env default `UNIVERSE_TOP_N=50` (.env.dev/.env.prod)
  - compose command override `--universe-id <id>` (backtest case)
- [ ] §D15 amendment box (MCT-177 publish):
  - Redis key prefix policy:
    - `signal:*` (signal-collector 5종 — fear_greed/ecos/kimchi/announcement/coinglass)
    - `market:*` (mctrader-data tick + orderbook cache)
    - `engine:*` (paper-engine position + strategy state)
  - migration: signal-collector 5종 기존 unprefixed key → `signal:*` rename (1주일 dual write 후 cutover)

### 1.3 CLAUDE.md update

- [ ] §"Docker stack 확장" 7 Story chain 표 MCT-177 PLANNED → IN_PROGRESS
- [ ] §MCT-177 IN_PROGRESS 신규 섹션

### 1.4 scope_manifest + counters status sync

- [ ] scope_manifest stories[MCT-177].status: Reserved → IN_PROGRESS + started_date
- [ ] counters.json reservations.MCT-177.status update

### 1.5 Phase 1 PR Gate

- [ ] DesignReviewPL dispatch + iter PASS + admin merge

---

## §2 Phase 2 PR1 (cross-repo: hub + engine + data, code)

### 2.1 mctrader-hub PR

**Files:**
- Modify: `compose.yml` (paper-engine service 신규 + Redis prefix env + UNIVERSE_TOP_N env)
- Modify: `.env.dev` / `.env.prod.example` (UNIVERSE_TOP_N=50 + REDIS_KEY_PREFIX_* env)

- [ ] paper-engine service block:

```yaml
paper-engine:
  image: ghcr.io/mclayer/mctrader-engine:latest
  container_name: mctrader-paper-engine
  profiles: ["dev", "prod"]
  build:
    context: ../mctrader-engine
  command: ["paper", "--daemon"]
  env_file:
    - .env.${COMPOSE_PROFILES:-dev}
  volumes:
    - mctrader_engine_runs:/var/lib/mctrader/runs
    - mctrader_l1:/var/lib/mctrader/data/l1:ro  # L1 cache read-only
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
  stop_grace_period: 60s
  restart: unless-stopped
  depends_on:
    redis:
      condition: service_healthy
    collector:
      condition: service_healthy
  networks:
    - mctrader_net
  labels:
    mctrader.role: "paper-engine"
    mctrader.story: "MCT-177"

volumes:
  mctrader_engine_runs:
```

- [ ] .env.dev / .env.prod.example UNIVERSE_TOP_N=50 + REDIS_KEY_PREFIX_ENGINE=engine + REDIS_KEY_PREFIX_MARKET=market + REDIS_KEY_PREFIX_SIGNAL=signal

### 2.2 mctrader-engine PR

**Files:**
- Modify: `src/mctrader_engine/cli.py` (SIGTERM handler + universe-id override + Redis key prefix)
- Create: `tests/test_sigterm_paper_daemon.py`
- Create: `tests/test_redis_prefix.py`

> **AMEND (CodeReviewPL FIX iter 1, 2026-05-15) — engine = asyncio SSOT, mctrader-data 동기 패턴 carry over 취소**
>
> 본 §2.2 초안은 mctrader-data 의 **동기 signal 패턴** (`signal.signal()` + global
> `_SHUTDOWN_REQUESTED` flag + collect loop busy-wait polling) 을 mctrader-engine 으로
> carry over 했으나, 이는 **설계 결함** 이었다 (FIX-1, root-cause = 구현 원인 +
> 설계 원인 동반). mctrader-engine 은 asyncio `paper_runner` 아키텍처로,
> SIGTERM graceful shutdown 의 **production SSOT 가 이미 존재** 한다 (MCT-23/48/53/100 LAND):
>
> - `src/mctrader_engine/shutdown.py:66 install_signal_handlers(loop, on_shutdown)` —
>   asyncio loop 기반, Windows SIGBREAK fallback 포함
> - `src/mctrader_engine/health_server.py HealthServer` — :8080 PaperRunner state
>   provider (`/health` + `/metrics`)
> - `src/mctrader_engine/runtime/paper_runner.py:53 PaperRunner.run()` —
>   `install_signal_handlers` 를 loop 에 wire + `_on_shutdown` → `executor.cancel()`
>   cooperative cancel → open position commit → finally `health_server.stop()`
>
> 동기 `signal.signal` + global flag 패턴은 engine asyncio event loop 와 **결합
> 불가** (busy-wait polling loop 가 paper_runner 에 부재). 따라서:
>
> 1. **신규 dead `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` +
>    `_sigterm_handler` 제거** (RefactorAgent 판정: 최소 변경 경로 = dead path 제거 +
>    `paper start` core 재사용; 신규 통합 코드 작성 = DRY 위반 + 결합도 증가로 기각).
> 2. **`paper --daemon` group callback 을 `paper start` core 위임으로 재구현** —
>    `ctx.invoke(paper_start, strategy=, symbol=, timeframe=, universe_id=)`
>    (env 기본값 `PAPER_STRATEGY`/`PAPER_SYMBOL`/`PAPER_TIMEFRAME` + D10 universe-id).
>    duration/end = None → run-until-cancel = SIGTERM 까지 blocking daemon.
>    SystemExit propagate (0 graceful / 1 ws / 2 risk / 3 lock / 5 unexpected).
> 3. **D4 graceful = `shutdown.install_signal_handlers` (asyncio loop SSOT)**.
>    SIGTERM → `_on_shutdown(ShutdownReason.SIGTERM)` → `executor.cancel()` →
>    open position commit → exit 0 (AC-2 정확 충족; dead flag polling 으로는 불가).
> 4. **HealthServer :8080** = `paper start` core 가 이미 wire (mock_feed=None 시
>    `HealthServer(runner_provider=lambda: runner_holder.get("runner"))` →
>    `PaperRunner(... health_server=health_server)`). compose healthcheck 정합.
>
> 결과: engine#54 신규 cli.py 코드 = daemon group callback 위임 로직만
> (신규 daemon loop 코드 0 line, PaperRunner/HealthServer/shutdown.py = 검증된
> MCT-48~100 LAND 자산 재사용). data 동기 signal 패턴 carry over = **취소**.

- [ ] universe-id override 옵션 추가:

```python
@cli.command()
@click.option("--universe-id", default=None, help="Universe override (default: env UNIVERSE_TOP_N)")
@click.option("--daemon", is_flag=True, default=False)
def paper(universe_id, daemon):
    if universe_id is None:
        universe_id = f"top-{os.environ.get('UNIVERSE_TOP_N', '50')}"
    # ...
```

- [ ] Redis key prefix 적용:

```python
REDIS_KEY_PREFIX = os.environ.get("REDIS_KEY_PREFIX_ENGINE", "engine")
def _engine_key(suffix: str) -> str:
    return f"{REDIS_KEY_PREFIX}:{suffix}"
# Usage: redis.set(_engine_key("position:BTC-USD"), state_json)
```

- [ ] 신규 2 test (FIX iter 1 amend — dead flag test → 실 daemon 위임 검증):
  - `tests/test_sigterm_paper_daemon.py`:
    - `test_no_dead_sync_signal_stub_remains` (dead 동기 패턴 제거 guard)
    - `test_paper_daemon_delegates_to_paper_start_core` (env-default 위임 검증)
    - `test_paper_daemon_universe_id_explicit_override` (D10 override)
    - `test_paper_subcommand_not_shadowed_by_daemon_group` (group invoke 안전)
    - `test_shutdown_ssot_is_asyncio_install_signal_handlers` (asyncio SSOT guard)
  - `tests/test_redis_prefix.py` (D15 `_engine_key` — review PASS, 보존): 5 test

### 2.3 mctrader-data PR (carry over)

**Files:**
- Modify: `src/mctrader_data/cli.py` (YAML loader 복원 + collect signal wiring)
- Create: `tests/test_yaml_config_loader.py`
- Modify: `tests/test_effective_config.py` (source_order 3-tier 복원)

- [ ] YAML loader 신규 (option A 채택):

```python
def _load_yaml_config() -> dict[str, Any]:
    yaml_path = os.environ.get("MCTRADER_CONFIG_PATH", "/etc/mctrader/config.yaml")
    if not Path(yaml_path).exists():
        return {}
    return yaml.safe_load(Path(yaml_path).read_text()) or {}
```

`effective-config` 의 source_order 를 `["env", "yaml_default", "built_in"]` 복원. env > yaml > built-in.

- [ ] collect command 측 signal wiring:

```python
@cli.command()
def collect(...):
    _register_signal_handlers()
    while not _SHUTDOWN_REQUESTED:
        # chunk 처리
        ...
    _commit_pending_wal()
    sys.exit(0)
```

- [ ] 신규 test: `test_yaml_config_loader.py` (3-tier merge verify)
- [ ] Update: `test_effective_config.py` (source_order 3-tier 복원 + yaml_overrides_builtin 실 YAML load 케이스)

### 2.4 cross-repo secret 6 repo read 검증

- [ ] `scripts/verify_cross_repo_secret.py` (mctrader-hub repo) — 6 repo gh CLI 로 secret list 조회 + `MCTRADER_CROSS_REPO_TOKEN` 존재 verify (없으면 등록 가이드 박제)

### 2.5 cross-repo LAND 순서

1. data PR (YAML loader + signal wiring) LAND 먼저
2. engine PR (SIGTERM + universe + Redis prefix) LAND
3. hub PR (compose paper-engine service) LAND

### 2.6 Phase 2 PR1 Gate

- AC-1 ~ AC-5 verify
- 신규 test 4종 PASS (engine 2 + data 1 + 6 repo secret verify)
- CodeReviewPL dispatch + iter PASS + admin merge

---

## §3 Phase 2 PR2 (hub, 박제)

- Story §10 FIX Ledger + §11 retro + §12 측정 + status COMPLETED
- ADR-030 §D2 + §D4 + §D10 + §D15 amendment LAND confirm
- scope_manifest milestone 2/7 → 3/7
- CLAUDE.md MCT-177 COMPLETED
- RETRO-MCT-177.md 신규 (PMOAgent)
- EPIC-RESULTS §Story-3 박제

---

## §4 다음 Story

MCT-177 COMPLETED → **MCT-178** (backtest-runner profile + oneshot + compose config CI lint, D2 backtest portion + D4 oneshot completion + D10 universe + D16 compose validate).

---

## §5 Self-Review

- D2 paper daemon: §2.1.1 + §2.2 ✓ (FIX iter 1: `paper --daemon` → `paper start` core 위임)
- D4 SIGTERM graceful: §2.2 ✓ (FIX iter 1 AMEND: asyncio `shutdown.install_signal_handlers` SSOT — data 동기 패턴 carry over 취소)
- D10 universe override: §2.2 + §2.1 ✓
- D15 Redis prefix: §2.2 ✓ (`_engine_key` review PASS, 보존)
- carry over 3건: §2.3 + §2.4 ✓ (CO-3 verify script owner = hub, data#65 중복 삭제)
- §6.5 N/A 박제: §1.1 ✓
- §11 Redis migration rollback: §1.1 ✓ (dual write 1주일)

### §5.1 CodeReviewPL FIX iter 1 결과 (2026-05-15)

| Finding | Repo | Severity | Root cause | 처리 |
|---------|------|----------|------------|------|
| FIX-1 | engine#54 | P0 | **구현 + 설계 동반** (plan §2.2 data 동기 패턴 오적용) | dead `_register_signal_handlers`/`_SHUTDOWN_REQUESTED` 제거 + `paper --daemon` → `paper start` core 위임 (HealthServer + PaperRunner + shutdown.py asyncio SSOT 재사용) + test 5종 재작성 + §2.2 amend |
| FIX-2 | data#65 | P0 | 구현 (단순) | `tmp_path: pytest.TempPathFactory` → `Path` 8건 + `from pathlib import Path` 2 file. pyright 8 errors → 0 |
| FIX-3 | data#65 + hub#334 | P1 | 구현 (위치 오배치, plan §2.4 hub owner 명확) | data#65 verify script 삭제 + hub#334 placeholder → full impl(106 lines) 포팅 |
| FIX-4 | hub#334 | P0 | engine#54 FIX-1 의존 (hub compose 자체 설계 정합) | hub compose 수정 0. engine#54 FIX-1 LAND 후 cross-repo 재검증 |
| F-003 | hub | P2 non-blocking | 기존 관행 정합 (advisory) | image `:latest` 하드코딩 — ADR-030 §D2 `${IMAGE_TAG}` 전 service 일괄 도입 = MCT-181 별 Story |
