# mctrader-engine Docker-first Containerization (Phase 3) — Design Spec

> **Source**: brainstorming session 2026-05-08, Sonnet 4.6 decider + Codex (GPT-5) 13-decision dispatch.
> **Story**: `MCT-100`, mctrader-hub#131. Parent Epic = mctrader-hub#120 (MCT-98, Docker-first Migration).
> **Channel**: codeforge consumer Story (story-init → phase-gate-mergeable). Phase 3 of 6.
> **Pilot reference**: MCT-99 (mctrader-data Pilot, merged 2026-05-07). spec = `2026-05-07-mctrader-data-docker-pilot-design.md`.
> **Parallel Phase 4**: MCT-101 (mctrader-web), mctrader-hub#132 — independent session.

## §0. 메타

| 항목 | 값 |
|---|---|
| Story key | MCT-100 |
| Issue | mctrader-hub#131 |
| Epic | mctrader-hub#120 (MCT-98) — Phase 3 of 6 |
| Title | mctrader-engine Docker-first Containerization |
| 작업 채널 | codeforge consumer (phase-gate-mergeable) |
| In-scope repo | mctrader-engine (impl) + mctrader-hub (docs) |
| Shape | dual mode — paper daemon (long-running, bounded) + backtest/WFO one-shot CLI |
| Trigger ADR | codeforge ADR-033 (Docker-first Infra Engineering) + ADR-009 §D12 (Docker-first persistence) + ADR-015 (engine state machine) |
| Risk | medium (per Pilot §11.4) — dual mode + cross-container mutex + 4 named volume topology |

## §1. Background (사용자 directive + 컨텍스트)

> 본 Story 는 Pilot (MCT-99) 의 Phase 2 entry session (2026-05-08) 에서 freeze 된 5 sister rollout sequencing 에 따라 mctrader-engine 을 Phase 3 에서 Docker-first 전환. parallel 로 Phase 4 (mctrader-web) 가 다른 session 에서 진행.

### §1.1 Pilot 박제 패턴 (carry-over)

- python:3.12-slim 2-stage Dockerfile, non-root `mctrader` UID 1001
- HTTP `/health` (port 8080) on long-running daemon, ws_state 기반 200/503
- Named volume `mctrader_data` mounted at `/var/lib/mctrader/data` (collector-owned)
- compose `restart: unless-stopped`, healthcheck via stdlib `urllib.request` (slim image 에 curl/wget 부재)
- bridge network, host port mapping 0
- `.github/workflows/image-lint.yml` (hadolint, codeforge reusable workflow)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
- README "Docker deployment" 절 + tests/integration/README.md manual smoke 박제

### §1.2 mctrader-engine 의 Pilot 와 다른 점 (engine-specific findings)

1. **dual mode** — paper daemon (`paper start`, runtime_lock, SIGTERM graceful) + 5+ one-shot CLI subcommand (`backtest`, `wfo decision-group ...`, `wfo search`, `paper evidence`, `risk kill|ack`, `lookahead-lint`, `indicator list`).
2. **runtime_lock host-wide mutex** (`~/.mctrader/runtime.lock`) — paper / wfo 모드간 mutex. ADR-015 의 SM 기반.
3. **3 persistence directory** — input (`MCTRADER_DATA_ROOT`), output (`output_dir`), WFO root (`MCTRADER_WFO_ROOT`).
4. **3 cross-repo git+https deps** — mctrader-market, mctrader-data, mctrader-market-bithumb (모두 `@main`).
5. **No HTTP API** — engine 은 CLI only. mctrader-web 가 control_adapter abstraction 으로 invoke (Phase 4 책임).
6. **Cross-container PID namespace 격리** — Pilot 단일 데몬 시점에는 발견 못 한 새 위협. ADR-015 mutex invariant 가 Docker 환경에서 깨짐 → D13 의 의무.

## §2. Scope

### §2.1 In-scope (Phase 3 본 Story)

mctrader-engine repo 의 Docker-first 전환:
1. Dockerfile + compose.yml + .dockerignore (codeforge ADR-033 정합)
2. paper service (long-running daemon, healthcheck via HealthServer)
3. engine profile-gated tools service (one-shot, `compose run --rm engine ...`)
4. 4 named volume topology (mctrader_data RO + mctrader_engine_runs + mctrader_engine_wfo + mctrader_engine_lock)
5. **runtime_lock fcntl.flock 교체** (D13) — cross-container mutex 보장
6. HealthServer module (mctrader-data 의 health_server.py 패턴 차용 + paper executor state 매핑)
7. README "Docker deployment" 절 + tests/integration/README.md
8. `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
9. `.github/workflows/image-lint.yml` (hadolint reusable)
10. pyproject 0.29.0 → 0.30.0 + CHANGELOG.md (신규 file)
11. ADR-015 cross-reference amendment (Docker SM mapping anchor)

### §2.2 Out-of-scope (Epic 후속 또는 follow-on Story)

- mctrader-web ↔ engine wiring (Phase 4 = MCT-101 mctrader-hub#132 별도 session)
- ghcr.io image publish + multi-arch buildx (Pilot F1 carry-over)
- trivy image scan 활성화 (Pilot F2 carry-over)
- distroless / digest pin / cosign signing (Pilot F3 carry-over)
- per-strategy paper fan-out (현재 single-strategy paper, runtime_lock host=1 매핑)
- WFO scheduled cron / batch automation (별도 ops Story)
- mctrader-engine PR open 후 Phase 4 / Phase 5 진입 (Epic governance, Phase 6 close 까지)

### §2.3 ADR-009 §D12 amendment 필요 여부

**불필요** — Phase 2 entry (mctrader-hub#122) 가 이미 §D12 박제 완료. mctrader-engine 의 별도 amendment 0건.

다만 ADR-015 Cross-references 절에 Docker SM mapping (D9) 의 anchor 가 추가될 수 있음 → ADR-015 amendment 1건 (소규모, optional — Phase 3 PR 안에 포함).

## §3. 도입할 설계

### §3.1 Architecture overview

mctrader-engine 의 dual-mode CLI (paper daemon + 다수 one-shot) 를 단일 Docker image (`mctrader-engine:0.30.0`) 위에 두 가지 compose 패턴으로 노출:

- **paper service** = long-running daemon. `restart: unless-stopped`, HealthServer `/health` (port 8080, internal only), 4 volume mount 모두 적용.
- **engine service** (profile `tools`) = one-shot 다용도. `compose run --rm engine <subcommand> ...` 형태. 동일 image, 동일 volume mount, healthcheck 무, 외부 호출자가 ExitCode 로 판정.

ADR-033 §7.4 OpRiskArch 4 항목 (restart / volume DR / health check / network mode) + ADR-015 두 SM (daemon + one-shot) 을 Docker container state 에 mapping. cross-container runtime_lock 은 fcntl.flock 기반으로 교체 (D13) → ADR-015 mutex invariant 보장.

### §3.2 Components (file 단위 변경)

#### 신규 파일

| 파일 | 책임 |
|---|---|
| `Dockerfile` | python:3.12-slim 2-stage. Stage 1 (deps) = uv 로 git+https 3 deps + editable install. Stage 2 (runner) = wheel + non-root `mctrader` UID 1001. `ENTRYPOINT ["mctrader-cli"]` + `CMD ["--help"]`. HEALTHCHECK directive (paper service 가 compose 측 healthcheck 로 override). |
| `compose.yml` | `paper` (default profile) + `engine` (profile `tools`). 4 named volume + healthcheck (paper 만) + restart unless-stopped (paper 만) + bridge network. labels (D9 SM mapping). |
| `.dockerignore` | Pilot 패턴 + `out/` + `.pytest_cache/` + `.ruff_cache/` 등 dev artifact 추가 |
| `src/mctrader_engine/health_server.py` | stdlib http.server `HealthServer` daemon thread. `GET /health` 200/503. PaperExecutor state + WS adapter 활성도 기반 판정 (heartbeat-fresh + ws connected → 200). |
| `tests/test_health_server.py` | TDD scenario: executor 부재 → 503 / paper running + ws connected → 200 / paper running + ws disconnected → 503 / port env override |
| `.github/workflows/image-lint.yml` | codeforge `templates/github-workflows/container-image-scan.yml` reusable, hadolint job 만 활성. Pilot 패턴 동일. |
| `tests/integration/README.md` | manual smoke 절차 — paper compose-up + healthy / backtest compose run / wfo compose run / runtime_lock cross-container mutex 검증 / volume invariant |
| `CHANGELOG.md` (신규) | `[0.30.0] - 2026-05-DD` entry. BREAKING note: runtime_lock impl 변경 (POSIX fcntl.flock) + Docker-first deploy. |

#### 수정 파일

| 파일 | 변경 |
|---|---|
| `src/mctrader_engine/runtime/runtime_lock.py` | **D13 핵심 patch** — fcntl.flock advisory lock 으로 교체. POSIX path: `os.open + fcntl.flock(LOCK_EX\|LOCK_NB)`. Windows fallback: 기존 `O_CREAT\|O_EXCL` + pid-alive 패턴 유지 (Windows dev 호환). LockHeldError shape 무변. JSON content (provenance) 보존 — flock 획득 후 ftruncate + write. |
| `src/mctrader_engine/runtime/paper_lock.py` | re-export thin wrapper (이미 그러한 상태) — 변경 없음 (acquire_runtime_lock(mode="paper") 동일 호출) |
| `src/mctrader_engine/runtime/paper_runner.py` | `health_server: HealthServer \| None = None` 인자 추가. `run()` 안에서 lifecycle (start before WS connect, stop after executor close). 기존 cancel/SIGTERM hook 무변. |
| `src/mctrader_engine/cli.py` | `paper start` 안에 HealthServer 생성 + PaperRunner 에 wiring (Pilot collector wiring 패턴 차용). env `MCTRADER_HEALTH_PORT` 지원. |
| `tests/test_runtime_lock.py` | flock 기반 동작 시나리오 추가 (POSIX 만, Linux Docker container 안에서 실행). Windows 기존 tests 유지. |
| `tests/test_paper_runner.py` | HealthServer wiring smoke (init/lifecycle 확인) — `register_signal_handlers=False` 모드와 동일 패턴 |
| `.claude/_overlay/project.yaml` | `infra_strategy: docker_first` field 추가 |
| `README.md` | "## Docker deployment" 절 추가 — install / config / 4 mode invocation pattern (paper / backtest / wfo / evidence) / DR backup / known limitation (Windows host 직접 실행 시 flock 미적용 fallback) |
| `pyproject.toml` | version 0.29.0 → 0.30.0 |

#### 삭제 파일

**없음** — Pilot 과 달리 mctrader-engine 에는 systemd unit 자산 부재. Docker 전환은 add-only.

### §3.3 Data flow / runtime

#### Build time

```
docker compose build paper
  ↓ Dockerfile
Stage 1 (deps): python:3.12-slim + uv
  uv pip install --system -e .
    ↓ resolves git+https for 3 cross-repo deps (@main):
      mctrader-market, mctrader-data, mctrader-market-bithumb
    ↓ install Click, libcst, pydantic, etc.
Stage 2 (runner): minimal slim base + Stage 1의 site-packages COPY
  + non-root user mctrader UID 1001
  + ENTRYPOINT ["mctrader-cli"]
  + CMD ["--help"]
```

#### Runtime — paper daemon

```
docker compose up -d paper
  ↓
container start → ENTRYPOINT [mctrader-cli]
  CMD = ["paper", "start", "--strategy", "${MCTRADER_STRATEGY}", ...]
  ↓
acquire_runtime_lock(mode="paper") via fcntl.flock on /var/lib/mctrader/lock/runtime.lock
  ↓ (cross-container mutex 보장)
HealthServer thread start → port 8080 listen
  ↓
PaperRunner.run() → bithumb WS connect → strategy loop
  ↓ (output: /var/lib/mctrader/runs/{run_id}/{report.json, equity.csv, event_store.sqlite, paper_partition/})
  ↓
SIGTERM (compose stop) → PaperRunner.cancel() → 30s timeout → SIGKILL fallback
```

#### Runtime — one-shot

```
docker compose run --rm engine backtest --strategy sma --symbol KRW-BTC --tf 1h \
  --start 2026-04-25T00:00:00Z --end 2026-05-02T00:00:00Z --fast 5 --slow 20 \
  --output-dir /var/lib/mctrader/runs
  ↓
container created (transient, --rm) → ENTRYPOINT [mctrader-cli]
  args = backtest, ...
  ↓
read /var/lib/mctrader/data/... via scan_candles (RO mount)
  ↓ (no lock needed for backtest)
BacktestExecutor.run() synchronous
  ↓ (output: /var/lib/mctrader/runs/{run_id}/{report.json, equity.csv})
  ↓
exit 0 (success) or 1+ (failure)
container removed
```

WFO 동일 패턴 + 추가로 `mctrader_engine_wfo:/var/lib/mctrader/wfo` mount + `acquire_runtime_lock(mode="wfo")`.

`paper evidence`, `risk kill|ack`, `lookahead-lint`, `indicator list` 도 동일 one-shot 패턴.

#### Network boundary

- **Inbound**: paper service container 내부 port 8080 (HealthServer `/health`). compose `ports:` 절 부재 → host expose 0.
- **Outbound** (paper only): `pubwss.bithumb.com:443` (WS TLS).
- **Outbound** (build only): pypi + github (3 git+https deps).
- bridge default network. `network_mode: host` 미사용.

#### Volume topology

```yaml
volumes:
  mctrader_data:        # external — collector-owned (mctrader-data Pilot)
    external: true
  mctrader_engine_runs:  # per-run audit artifacts
  mctrader_engine_wfo:   # WFO registry (decision_groups, manifests)
  mctrader_engine_lock:  # cross-container runtime_lock SoT

services:
  paper:
    build: .
    command: ["paper", "start", "--strategy", "${MCTRADER_STRATEGY:-sma}",
              "--symbol", "${MCTRADER_SYMBOL:-KRW-BTC}",
              "--tf", "${MCTRADER_TF:-1h}", "--fast", "${MCTRADER_FAST:-5}",
              "--slow", "${MCTRADER_SLOW:-20}",
              "--output-dir", "/var/lib/mctrader/runs"]
    volumes:
      - mctrader_data:/var/lib/mctrader/data:ro
      - mctrader_engine_runs:/var/lib/mctrader/runs
      - mctrader_engine_wfo:/var/lib/mctrader/wfo
      - mctrader_engine_lock:/var/lib/mctrader/lock
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      MCTRADER_OUTPUT_DIR: /var/lib/mctrader/runs    # consumed by README invocation, also future plumbing
      MCTRADER_WFO_ROOT: /var/lib/mctrader/wfo
      MCTRADER_RUNTIME_LOCK_PATH: /var/lib/mctrader/lock/runtime.lock
      MCTRADER_HEALTH_PORT: "8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      mctrader.role: "paper-daemon"
      mctrader.sm.kind: "daemon"
      mctrader.adr-015.daemon.running: "health_status=healthy"
      mctrader.adr-015.daemon.degraded: "health_status=unhealthy while running"

  engine:
    build: .
    profiles: ["tools"]
    volumes:
      - mctrader_data:/var/lib/mctrader/data:ro
      - mctrader_engine_runs:/var/lib/mctrader/runs
      - mctrader_engine_wfo:/var/lib/mctrader/wfo
      - mctrader_engine_lock:/var/lib/mctrader/lock
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      MCTRADER_OUTPUT_DIR: /var/lib/mctrader/runs
      MCTRADER_WFO_ROOT: /var/lib/mctrader/wfo
      MCTRADER_RUNTIME_LOCK_PATH: /var/lib/mctrader/lock/runtime.lock
    labels:
      mctrader.role: "engine-cli"
      mctrader.sm.kind: "oneshot"
      mctrader.adr-015.oneshot.completed: "ExitCode=0"
      mctrader.adr-015.oneshot.failed: "ExitCode!=0"
```

`profiles: ["tools"]` 덕에 `compose up` 만 호출하면 paper 만 가동, `compose run --rm engine ...` 시점에만 engine 컨테이너 생성.

### §3.4 ADR-033 §7.4 OpRiskArch 4 항목 mapping

#### 1. Container restart policy

- paper: `restart: unless-stopped`. SIGTERM stop 의도 존중, crash → 자동 재시작.
- engine (one-shot): restart 없음. ExitCode 만 외부 호출자에게 신호.

#### 2. Volume DR (D12)

```powershell
# Backup runs (audit artifacts)
docker run --rm -v mctrader_engine_runs:/source:ro -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_engine_runs_$(Get-Date -Format yyyyMMdd_HHmmss).tar.gz -C /source .

# Backup WFO (registry)
docker run --rm -v mctrader_engine_wfo:/source:ro -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_engine_wfo_$(Get-Date -Format yyyyMMdd_HHmmss).tar.gz -C /source .

# Lock volume = transient, backup 제외
```

bash 등가 (README 에 박제). Pilot ADR-009 §D12 패턴 reuse.

#### 3. Health check tuning

| 파라미터 | 값 | 근거 |
|---|---|---|
| test | `python -c urllib /health` | slim image curl 부재. Pilot 동일 |
| interval | 30s | Pilot 동일 |
| timeout | 10s | HealthServer state lookup ms |
| retries | 3 | WS reconnect transient 대응 (3 × 30) |
| start_period | 60s | WS connect + symbol subscribe |

HealthServer state source = PaperExecutor 의 `_executor` 활성 여부 + bithumb WS adapter 의 ws_state.

#### 4. Network mode boundary

- bridge default. host network 미사용.
- 호스트 port 매핑 0 (HealthServer 8080 = container 내부 only).
- outbound = WS TLS 단방향 (paper only).

### §3.5 ADR-015 SM ↔ Docker state alignment (D9)

| ADR-015 state | Docker state mapping | Compose label |
|---|---|---|
| daemon `[stopped]` | container exited / removed | `mctrader.adr-015.daemon.stopped` |
| daemon `[starting]` | container running, healthcheck pending | (start_period window) |
| daemon `[running]` | `health_status=healthy` | `mctrader.adr-015.daemon.running` |
| daemon `[stopping]` | SIGTERM in 30s window | (transient) |
| daemon `[crashed]` | container ExitCode≠0 (auto-restart by `unless-stopped`) | (event log) |
| daemon `[degraded]` | `health_status=unhealthy` while running | `mctrader.adr-015.daemon.degraded` |
| one-shot `[queued]` | pre-`compose run` | (out of container scope) |
| one-shot `[running]` | container running | (transient) |
| one-shot `[completed]` | ExitCode=0 | `mctrader.adr-015.oneshot.completed` |
| one-shot `[failed]` | ExitCode≠0 | `mctrader.adr-015.oneshot.failed` |
| one-shot `[cancelling]` | SIGTERM sent | (transient) |
| one-shot `[cancelled]` | ExitCode = SIGTERM-induced (130 / 143) | (Phase 4 가 SIGTERM-induced 추적) |

`/state` endpoint 미신설 — Phase 4 (mctrader-web control_adapter) 가 docker inspect / labels / health_status 로 introspect 충분. paper `/health` 외 신규 HTTP surface 0.

### §3.6 D13 — runtime_lock fcntl.flock 교체

#### 문제 (Sonnet 검증 발견)

기존 `runtime_lock.py` 의 stale-pid cleanup (`os.kill(pid, 0)`) 은 PID namespace 격리 때문에 cross-container 환경에서 **항상 ProcessLookupError 발생** → stale 판정 → unlink + 재 acquire → mutex 깨짐.

증명 시나리오:
1. paper 컨테이너 (PID ns A) 가 lock 획득 → `{"pid":7,"mode":"paper"}` write
2. `compose run --rm engine wfo search` (PID ns B) 시도 → file 존재 → `_pid_alive(7)` 호출
3. PID ns B 에서 PID 7 = 자기 init 또는 부재 → ProcessLookupError → stale → unlink → re-acquire 성공
4. **결과: paper [running] + wfo [running] 동시 진행 → ADR-015 mutex 위반**

#### 해결 — fcntl.flock advisory lock

POSIX `fcntl.flock(fd, LOCK_EX|LOCK_NB)` 은 inode 기반 kernel-managed → 같은 file (공유 volume) 면 cross-container 동작. process exit 시 fd close = 자동 release (crash-safe).

```python
# runtime_lock.py POSIX path
import fcntl
@contextmanager
def acquire_runtime_lock(*, run_id, mode, lock_path=None):
    path = lock_path or _default_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            holder = _read_holder(path)  # 기존 helper reuse for provenance
            raise LockHeldError(
                path=path,
                holder_run_id=holder[0] if holder else "<unknown>",
                holder_pid=holder[1] if holder else -1,
                holder_mode=holder[2] if holder else "<unknown>",
            ) from exc
        # 획득 성공 → JSON content (provenance) write
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload.encode("utf-8"))
        yield path
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
```

#### Cross-platform parity

Windows host 는 `fcntl` module 부재. Windows dev 가 `mctrader-cli paper start` 를 직접 실행하는 path 가 살아있음 → `sys.platform.startswith("win")` 분기로 기존 `O_CREAT|O_EXCL` + `_pid_alive` 패턴 유지. Linux (Docker) 만 flock.

```python
@contextmanager
def acquire_runtime_lock(*, run_id, mode, lock_path=None):
    if sys.platform.startswith("win"):
        # Windows: legacy atomic-write + pid-alive (single-host single-PID-ns 가정 OK)
        with _acquire_windows(...) as p:
            yield p
        return
    # Linux/POSIX: flock-based (Docker container 호환)
    with _acquire_posix(...) as p:
        yield p
```

#### Test impact

- 기존 `test_paper_lock.py` 일부 test = pid-alive 패턴 검증. Linux 에서는 flock 동작 검증으로 대체. Windows 에서는 그대로.
- 신규 test: cross-fd flock 동작 검증 (Linux only — `pytest.mark.skipif(sys.platform.startswith('win'))` 또는 `os.fork` 기반)
- 신규 test: integration smoke `tests/integration/test_runtime_lock_cross_container.sh` (Docker compose 두 컨테이너 동시 시도 → 한 쪽 LockHeldError 검증)

#### Behavioral compat

- `LockHeldError` exception shape 무변
- env override `MCTRADER_RUNTIME_LOCK_PATH` 무변
- mode parameter 무변
- mctrader-cli paper / wfo 호출 path 무변

## §4. API 계약

**Public API 변경 0건.**

근거:
- mctrader-cli console_script entrypoint 무변 (subcommand surface 모두 보존)
- `runtime_lock.acquire_runtime_lock` signature 무변 (impl swap 만)
- `LockHeldError` shape 무변
- `PaperRunner` constructor `health_server` 인자 추가 = optional + default None → backward compat
- HealthServer `/health` endpoint = internal-only (compose ports 절 부재) → public 아님
- mctrader-market / -data / -bithumb 의존 무변

## §5. 보안 설계

### §5.1 Trust boundary

- **Container network**: bridge default. host network 노출 0. service-to-service 0 (paper 와 engine 은 별도 lifecycle, intra-compose 통신 없음).
- **Image build context**: `.dockerignore` strict — `.env*`, `*.pem`, `*.key`, `*.crt`, `.git`, `.github`, `.claude`, `out/`, `*.md`, `docs/`, dev cache. `COPY . .` 시 sensitive file 미포함.
- **Layer cache**: 2-stage Dockerfile, Stage 1 만 git+https outbound. Stage 2 wheel COPY only.
- **Cross-container**: 4 named volume = mount point 단위 격리. lock volume 은 mutex 용도만, secret 미포함.

### §5.2 Threat model (STRIDE 발췌)

| 컴포넌트 | 위협 | 본 Story 완화 |
|---|---|---|
| Image | base CVE | python:3.12-slim. 후속 trivy automation (Pilot F2) |
| Image | secret 누설 | engine scope = secret 0개 (public WS only). hadolint syntax 검증. |
| compose network | service-to-service spoofing | paper / engine 의 intra-compose 통신 0 |
| compose network | host expose | bridge default, 호스트 port 매핑 0 |
| Volume | host path escape | named volume 4종 모두. host bind 미적용 (dev README alternative 만 안내) |
| Volume mctrader_data | engine 이 collector 데이터 mutate | `:ro` mount 강제. collector forward-only invariant 보호. |
| runtime_lock | paper+wfo 동시 실행 | **D13 fcntl.flock** = inode 기반 kernel-managed mutex. cross-container 동작 보장. |
| runtime_lock | crashed-without-cleanup | flock fd close = kernel auto-release. stale 처리 무관. |

### §5.3 Auth/Authz

**N/A** — engine 은 public WS (Bithumb) 만. credential / API key 0개. risk 명령은 sentinel file write 만 (operator local FS).

### §5.4 §7.4 운영 리스크

§3.4 의 4 항목 매핑 + §3.6 D13 mutex 보강. ADR-033 §결정 5 deputy mandate 매트릭스 cell annotation 준수.

### §5.5 민감 데이터 분류

- engine 처리 데이터 = public market data + audit artifact (execution_report.json + equity_curve.csv)
- audit artifact 안에 사용자 PII 0개
- event_store.sqlite = run lifecycle event 만, secret 0개
- 분류: Public + Audit (internal)

### §5.6 N/A 명시

§5.3 = N/A. §5.1 / §5.2 / §5.4 / §5.5 = framework 가이드 준수.

## §6. 테스트 계획

### §6.1 Unit (pytest)

- `tests/test_health_server.py` (신규, TDD 4 시나리오):
  1. executor 부재 → 503 (paper 미시작)
  2. executor 활성 + ws_state="connected" → 200
  3. executor 활성 + ws_state="disconnected" → 503
  4. port env override 적용 검증
- `tests/test_runtime_lock.py` (수정):
  - 기존 atomic-write + stale-pid 시나리오 → Windows 분기 한정으로 유지
  - 신규: Linux flock 시나리오 (subprocess fork or os.fork mark) — fd 두 개 동시 시도 → 한 쪽 LockHeldError
  - 기존 test_paper_lock.py 유지 (paper_lock = thin wrapper 그대로)
- `tests/test_paper_runner.py` (수정):
  - `health_server=None` (default) → 기존 동작 변화 0
  - `health_server=HealthServer(...)` → lifecycle (start before WS / stop after executor close) 검증
- 기존 ~250 pytest 회귀 PASS

### §6.2 Integration (compose smoke, manual)

`tests/integration/README.md` 박제 절차 (CI 자동화 부담 회피, Pilot 패턴):

1. `docker compose build paper` exit 0
2. `docker compose up -d paper` exit 0
3. 60초 대기 후 `docker compose ps` → `healthy`
4. `docker compose exec paper python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"` exit 0
5. `docker compose run --rm engine backtest --strategy sma --symbol KRW-BTC --tf 1h --start ... --end ... --fast 5 --slow 20` exit 0 + `/var/lib/mctrader/runs/{run_id}/execution_report.json` 생성
6. `docker compose run --rm engine wfo decision-group --help` exit 0
7. **Cross-container mutex (D13)**: paper 가동 중 `docker compose run --rm engine wfo search ...` → exit 3 (LockHeldError) 또는 동등한 lock conflict signal
8. `docker compose run --rm engine paper evidence --run-id <existing_run>` exit 0 (또는 3 if no run)
9. `docker volume inspect mctrader-engine_mctrader_engine_runs` 존재 + content survive `compose down` (without `-v`)
10. SIGTERM graceful: `docker compose stop paper` → 30s 내 종료 + `_executor.cancel()` 호출 흔적 (event_store)

### §6.3 Lint

- `hadolint Dockerfile` (codeforge `image-lint.yml` reusable)
- `actionlint .github/workflows/image-lint.yml`
- `bash scripts/check-container-strategy.sh` (codeforge consumer lint, `infra_strategy: docker_first` + Dockerfile + compose.yml 모두 PASS)
- `ruff check src/ tests/` (수정된 module)
- `pyright src/mctrader_engine/runtime/runtime_lock.py src/mctrader_engine/health_server.py` (변경 module 만)

### §6.4 §8.5 Stateful invariant (manual, integration README)

- **Paper daemon**:
  - Volume 보존: `up → run → down (no -v) → up → 같은 mctrader_engine_runs mount → 이전 run dir 존재` 검증
  - SIGTERM graceful: in-flight executor.run() 가 30s timeout 안에 cancel → event_store 에 `lifecycle.phase=stopped` event 박제
- **Cross-container mutex (D13)**:
  - paper 가동 → `compose run wfo` 시 LockHeldError → wfo 컨테이너 exit 3
  - paper 가동 → `compose run backtest` → backtest 는 lock 획득 안 함 → exit 0 (mutex 적용 대상 = paper / wfo 만)

### §6.5 TDD 진입 순서

1. `test_health_server.py` 4 시나리오 RED
2. `health_server.py` GREEN (Pilot collector 패턴 차용 + paper executor state hook)
3. `test_runtime_lock.py` Linux flock 시나리오 RED
4. `runtime_lock.py` flock 분기 patch GREEN (Windows path 무변)
5. `test_paper_runner.py` HealthServer wiring smoke
6. `paper_runner.py` + `cli.py` (paper start) wiring patch
7. Dockerfile (2-stage, hadolint PASS)
8. compose.yml (paper + engine profile, 4 volume, healthcheck, labels) — `docker compose config` PASS
9. `.dockerignore`
10. `infra_strategy: docker_first` + check-container-strategy.sh PASS
11. `.github/workflows/image-lint.yml`
12. README "Docker deployment" 절
13. tests/integration/README.md
14. pyproject 0.30.0 + CHANGELOG.md

### §6.6 Coverage 목표

- HealthServer 신규 module 100% line
- runtime_lock POSIX flock branch 100% (Linux 분기)
- Windows pid-fallback branch 기존 cov 유지
- integration smoke = manual + CI = `docker compose config` syntax + hadolint

## §7. Migration / Cross-platform parity

### §7.1 production state

mctrader-engine 의 production 운영 자산 부재 (no systemd unit, no PaaS deployment). Docker 전환 = add-only — 기존 `mctrader-cli` 직접 호출 path 도 보존 (Windows dev / Linux dev 모두 무변).

### §7.2 Cross-platform parity

- **Build**: `docker compose build` → linux/amd64 single (Windows Docker Desktop default).
- **Dev cycle (Windows)**: Windows Docker Desktop 안에서 paper / engine 컨테이너 가동 = Linux semantics. fcntl.flock 정상 동작 (Linux container 안).
- **Dev cycle (Windows direct)**: 사용자가 `mctrader-cli paper start` 를 Windows host 에서 직접 실행 시 = `sys.platform=="win32"` 분기 → 기존 atomic-write + pid-alive lock impl. Single-host single-PID-ns 가정 OK.
- **Prod (Linux host + Docker)**: `compose up -d paper` + `compose run --rm engine ...`. flock 기반 cross-container mutex.
- 동일 Dockerfile + compose.yml 가 모든 환경에서 동일 동작.

### §7.3 Rollback 경로

Phase 3 검증 실패 시:
- mctrader-hub PR (docs) revert
- mctrader-engine PR revert (Dockerfile + compose + health_server.py + runtime_lock.py patch + project.yaml + workflow + tests + README + CHANGELOG)
- production 미가동 → host cleanup 0
- 4 named volume 은 사용자 재량 (`docker volume rm` 또는 보존)

D13 의 runtime_lock patch 만 별도 revert 가능 — Linux flock branch 만 제거 + 기존 atomic-write 패턴 복원. 단 cross-container mutex invariant 깨짐 (D13 의 motivation).

### §7.4 Cutover 검증 (Story §10 acceptance evidence)

§6.2 의 10-step manual smoke 모두 PASS evidence Story §9 에 박제.

## §8. 영향 / 의존

### §8.1 codeforge 의존

- ADR-033 (CFP-128 Accepted 2026-05-07) — Pilot 동일
- `templates/github-workflows/container-image-scan.yml` (reusable workflow)
- `scripts/check-container-strategy.sh` (consumer-side lint)
- `examples/cli-tool-minimal/Dockerfile` + `examples/webapp-minimal/{Dockerfile,compose.yml}` (참조 패턴)

### §8.2 mctrader-data Pilot (이미 merged)

- 4 volume 중 `mctrader_data` 는 Pilot 의 collector-owned volume 을 RO 로 share.
- engine 이 mctrader-data Python package 를 pip git+https `@main` 으로 import (`scan_candles`, `paper_storage`, `paper_lineage`).

### §8.3 mctrader-hub Phase 4 parallel (MCT-101 #132)

- **Phase 4 와 race 회피**:
  1. Epic #120 body update — Phase 3 + 4 양쪽 PR merge 후 별도 reconciliation commit (둘 중 마지막 merge session 이 책임). 본 Phase 3 session 은 PR merge 시점에 Epic body 직접 update.
  2. Cross-cutting finding — 본 Story 의 D7 (control_adapter 패턴) 가 Phase 4 의 mctrader-web ↔ engine wiring 의 SoT. README 에 박제.
  3. ADR amendment 충돌 회피 — 본 Story 는 ADR-009 amendment 0건. ADR-015 cross-ref optional. Phase 4 가 다른 ADR amend 시 별도.

### §8.4 mctrader-web Phase 4 (별도 session)

- D7-C 결정에 따라 본 Story 의 `compose run --rm engine ...` 패턴 = Phase 4 control_adapter 의 SoT.
- Phase 4 가 채택 가능한 옵션:
  - subprocess + `docker compose run` 호출
  - Docker SDK Python (`docker-py`) 으로 image API 호출
  - Docker socket mount (보안 trade-off — Phase 4 의무)
- Phase 3 는 위 옵션 미결정 — Phase 4 session 책임.

### §8.5 ADR-015 cross-ref (optional amendment)

§3.5 의 SM ↔ Docker mapping 표는 ADR-015 의 Cross-references 절에 anchor 추가 후보. mctrader-hub Phase 3 PR 에 포함 (1 commit).

## §9. Future work / Open questions

| ID | 항목 | 처리 방향 |
|---|---|---|
| F1 | ghcr.io publish workflow + multi-arch | Pilot F1 carry-over — Phase 6 또는 별도 |
| F2 | trivy image scan 활성화 | F1 묶음 |
| F3 | distroless / digest pin / cosign | 보안 강화 별도 |
| F4 | per-strategy paper fan-out | 별도 Story (runtime_lock 모델 redesign 필요) |
| F5 | git+https @main → commit pin (D8-B) | Phase 4 entry 시점 재평가 (build reproducibility) |
| F6 | WFO scheduled cron / batch automation | 별도 ops Story |
| F7 | ADR-015 cross-ref amendment land | mctrader-hub Phase 3 PR 안 또는 별도 ADR PR |
| O1 | mctrader-web ↔ engine 의 control_adapter 구현 옵션 (subprocess / docker-py / docker socket) | Phase 4 (MCT-101) 책임 |
| O2 | Windows host 직접 실행 시 flock 미적용 = mutex 보장 약화 | README "known limitation" 명시. Docker 환경에서만 cross-container mutex 보장. |
| O3 | volume backup cron 자동화 (engine_runs + engine_wfo) | 별도 ops Story (Pilot O4 carry-over) |
| O4 | 4 volume 의 volume size estimation + retention policy | 운영 경험 기반 — Phase 6 epic close 시 결정 |

## §10. 거절된 대안

| 결정점 | 채택 | 거절 + 근거 |
|---|---|---|
| D1 Compose surface | α (1 paper + compose run for one-shot) | β 2 service profile / γ 3 service profile — one-shot 을 service 로 표현 = 의미 mismatch (즉시 종료). δ 0 service — paper daemon 의 long-running affordance 손실 |
| D2 HealthServer 적용 | A (paper only) | B 모든 컨테이너 — one-shot 즉시 종료 무의미. C 명시 disable — `compose run` 에 healthcheck 자체 무의미 |
| D3 Data input | A (mctrader_data RO) | B RW — collector forward-only invariant 위반. C host bind / D compose run flag — Docker-first default 약화, Pilot precedent 불일치 |
| D4 Engine output | A (단일 mctrader_engine_runs) | B per-mode 분할 — audit cross-mode 어려움. C runs+wfo+lock 통합 — lifecycle 경계 모호 |
| D5 WFO root | B (별도 mctrader_engine_wfo) | A runs 통합 — registry vs per-run lifecycle 경계 모호. C 통합 — D4 거절 근거 동일 |
| D6 runtime_lock 조정 | A (공유 volume + env override) **+ D13 의무** | B 운영 규율 — 강제력 0. C compose hook — 과도. D redis/sqlite — scope 초과. E 수용 — ADR-015 위반 |
| D7 mctrader-web 통합 | C (compose run 패턴 명시 + README SoT) | A 약 — Phase 4 의 contract 불명확. B interface only — executable 패턴 부재. D HTTP API 신설 — Pilot precedent 위반 + scope 폭발 |
| D8 Image deps | A (Pilot uv 2-stage @main) | B commit pin — Phase 4 entry 시 재평가. C wheel vendor — 유지비 ↑ |
| D9 SM ↔ Docker | labels yes / `/state` no | endpoint 신설 — paper `/health` 외 신규 HTTP surface 회피 |
| D10 Process model | A (1 container = 1 strategy) | B 다중 strategy fan-out — runtime_lock 모델 redesign 필요. C 명시적 다중 service — F4 carry-over |
| D11 Image scope | C (단일 image 다중 service) | A 단일 service — paper daemon 만으로 부족. B 다중 image — 빌드 중복 |
| D12 DR backup | runs + wfo backup, lock 제외 | (Codex 추가) lock 까지 backup — transient state 의 무의미 backup |
| D13 runtime_lock impl | fcntl.flock 교체 (Linux) + Windows pid-fallback | 현재 atomic-write + pid-alive — cross-container PID ns 격리에서 mutex 깨짐 (Sonnet 검증) |

## §11. 참고 / 관련 파일

### codeforge (외부 의존, mclayer/plugin-codeforge)

- `docs/adr/ADR-033-docker-first-infra-engineering.md`
- `templates/github-workflows/container-image-scan.yml`
- `scripts/check-container-strategy.sh`
- `examples/cli-tool-minimal/Dockerfile` + `.dockerignore`
- `examples/webapp-minimal/{Dockerfile,compose.yml}`

### mctrader-data Pilot (이미 merged, 본 Story reference)

- `mctrader-data/Dockerfile`
- `mctrader-data/compose.yml`
- `mctrader-data/src/mctrader_data/health_server.py`
- `mctrader-data/.github/workflows/image-lint.yml`
- `mctrader-data/tests/integration/README.md`
- `mctrader-hub/docs/superpowers/specs/2026-05-07-mctrader-data-docker-pilot-design.md`
- `mctrader-hub/docs/superpowers/plans/2026-05-07-mctrader-data-docker-pilot-plan.md`
- `mctrader-hub/docs/stories/MCT-99.md`

### mctrader-hub ADR

- `docs/adr/ADR-009-ohlcv-schema.md` §D12 (이미 박제)
- `docs/adr/ADR-015-engine-state-machine.md` (Phase 3 cross-ref amendment 후보)
- `docs/adr/ADR-033-docker-first-infra-engineering.md` (codeforge ADR, hub mirror)

### mctrader-engine 본 repo (변경 대상)

- `pyproject.toml` (0.29.0 → 0.30.0)
- `README.md` (Docker deployment 절 추가)
- `src/mctrader_engine/runtime/runtime_lock.py` (D13 patch)
- `src/mctrader_engine/runtime/paper_runner.py` (HealthServer wiring)
- `src/mctrader_engine/cli.py` (paper start HealthServer 생성)
- `.claude/_overlay/project.yaml` (`infra_strategy: docker_first`)

---

## Acceptance Criteria (요약)

| ID | AC |
|---|---|
| A1 | Dockerfile 2-stage python:3.12-slim non-root mctrader UID 1001 — hadolint warning 0 |
| A2 | compose.yml — paper service (default profile, healthcheck, restart unless-stopped, 4 volume, labels) + engine service (profile tools, 4 volume, labels) — `docker compose config` PASS |
| A3 | .dockerignore — Pilot 패턴 + `out/` + dev cache 추가 |
| A4 | `health_server.py` HTTP `/health` (port 8080, env override) + 4 TDD scenario PASS |
| A5 | **D13** `runtime_lock.py` fcntl.flock POSIX branch + Windows pid-fallback branch + LockHeldError shape 무변 + cross-container mutex test PASS |
| A6 | `paper_runner.py` HealthServer wiring (lifecycle start/stop) — 기존 test 회귀 PASS |
| A7 | `cli.py` `paper start` 가 HealthServer 생성 + PaperRunner 에 inject |
| A8 | `.claude/_overlay/project.yaml` `infra_strategy: docker_first` 추가 |
| A9 | `bash scripts/check-container-strategy.sh` PASS |
| A10 | `.github/workflows/image-lint.yml` (codeforge reusable, hadolint job) — actionlint clean |
| A11 | README "Docker deployment" 절 — install / paper / backtest / wfo / evidence / risk invocation pattern + DR backup recipe + Windows known limitation |
| A12 | `tests/integration/README.md` — 10-step manual smoke + cross-container mutex 검증 절차 박제 |
| A13 | pyproject 0.29.0 → 0.30.0 + `CHANGELOG.md` `[0.30.0]` entry |
| A14 | 기존 ~250 pytest 회귀 PASS + 신규 health_server 4 + runtime_lock flock test |
| A15 | `docker compose build paper` 성공 + `docker compose up -d paper` healthy convergence (60s 내) |
| A16 | `docker compose run --rm engine backtest --help` 외 5+ subcommand exit 0 |
| A17 | Cross-container mutex evidence: paper 가동 중 `compose run --rm engine wfo search` → exit 3 (LockHeldError) |
| A18 | mctrader-hub doc PR + mctrader-engine impl PR 모두 phase-gate-mergeable green |
| A19 | Codex 7-area review push-back fix-back 또는 defer 박제 |
| A20 | Epic #120 body Phase 3 status update (parallel reconciliation) + mctrader-hub#131 close |

---

## 다음 단계

1. 본 spec 파일 사용자 review
2. 사용자 approve 후 `superpowers:writing-plans` skill 호출 → implementation plan 작성 (Pilot 8-task 구조 reference)
3. plan 작성 후 `MCT-100` Story file scaffold (mctrader-hub `docs/stories/MCT-100.md`, MCT-99 format reference)
4. mctrader-hub Phase 3 PR (docs/MCT-100-engine-docker branch — design + plan + Story file + ADR-015 cross-ref optional commit)
5. mctrader-engine Phase 3 PR (feat/MCT-100-docker-first branch — Dockerfile + compose + health_server + runtime_lock D13 + paper_runner wiring + project.yaml + workflow + README + CHANGELOG + tests)
6. mctrader-engine PR review chain (CodeReview + TestAgent + SecurityTest hadolint) + admin merge
7. mctrader-hub PR Codex 7-area review per phase + admin merge
8. Epic #120 body Phase 3 status reconciliation commit (Phase 4 parallel session 과 ordering 협의)
9. Story §11 회고 — 5 sister rollout sequencing 진행 박제 (Phase 5 bithumb sister entry condition 이미 만족, library quartet 처리 방향)
