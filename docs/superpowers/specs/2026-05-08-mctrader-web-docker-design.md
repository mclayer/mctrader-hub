# mctrader-web Docker-first Containerization (Phase 4 sister) — Design Spec

> **Source**: brainstorming session 2026-05-08, Sonnet 4.6 decider + Codex agentId `a9897ebe62347932a` 13 결정점 채택 + 4 sub-decision adjustment.
> **Trigger**: mctrader Docker-first Migration Epic MCT-98 #120 Phase 4 — Pilot Story §11.4 high risk sister rollout (multi-service compose + sqlite hash chain DR).
> **Channel**: codeforge consumer Story (story-init → phase-gate-mergeable). mctrader-hub Epic 하위 Phase 4 sister Story.

## §0. 메타

| 항목 | 값 |
|------|-----|
| Story key | **MCT-101** |
| Story issue | mctrader-hub#132 (stub 등록) |
| Parent Epic | MCT-98 / mctrader-hub#120 (Phase 6 close 까지 OPEN) |
| Title | mctrader-web Docker-first Containerization (Phase 4 sister) |
| 작업 채널 | codeforge consumer (phase-gate-mergeable) |
| In-scope repo | mctrader-web (impl) + mctrader-hub (spec/plan/Story/ADR amendment) |
| Out (Epic 후속) | Phase 3 (engine MCT-100) parallel — 다른 session, 본 Story 와 독립 |
| Reference Pilot | mctrader-data Phase 1 (MCT-99, PR #11 merged 2026-05-07) + Phase 2 entry (PR #122 merged 2026-05-08) |
| Risk classification | **HIGH** (Pilot Story §11.4 — multi-service novel pattern + sqlite hash chain DR) |

## §1. Background (Phase 4 trigger + 컨텍스트)

mctrader Docker-first Migration Epic (MCT-98 #120) Phase 4 — mctrader-web sister rollout. Pilot Story §11.4 5-sister 분석에서 다음과 같이 분류:

> mctrader-web | multi-service (FastAPI + Streamlit + sqlite volume) | docker_first | 4 | high — multi-service novel pattern, sqlite volume DR 분리 vs 통합 결정

기존 mctrader-web (v0.13.0) 의 실태 (코드 reading):

- **Components**: FastAPI service (`api/`) + Streamlit dashboard (`dashboard/`) + admin sub-router (`api/admin/` MCT-97 P1-P6) + api_client (`api_client/`).
- **Persistence**: 단일 sqlite at `data/admin_audit.sqlite` — ADR-016 audit_log + idempotency_cache (hash chain, append-only, WAL mode 이미 활성). 별도 paper ledger 없음 (Paper ledger = mctrader-engine ADR-002 D6 — engine repo).
- **Runtime**: cli.py 가 `uvicorn.run(host=127.0.0.1, port=7821)` hard-bind. LifecycleManager / BacktestLifecycleManager / WfoLifecycleManager 가 PaperRunner / BacktestRunner / WfoRunner 를 **uvicorn event loop 안 asyncio.Task 로 in-process 실행** (ADR-014 "다중 process 분리는 solo dev scope 외" 정합).
- **External dep**: `mctrader-data` CLI on PATH (status_adapter X6 → `subprocess.run("mctrader-data status --format json")`). pyproject git+https core dep — image 안에 install 시 console script 자동 wiring.
- **Existing infra assets**: deploy/ 디렉토리 0건 (Pilot 과 다름 — systemd 자산 없음, 삭제 대상 0). Dockerfile / compose.yml / .dockerignore 0. CHANGELOG.md 0. `.claude/_overlay/project.yaml` 의 `infra_strategy:` 미명시 (codeforge ADR-033 default = docker_first → lint trigger).

본 Story 의 핵심 challenge:

1. multi-service compose pattern (api + panel) novel — Pilot 의 1-service 와 다름.
2. sqlite hash chain integrity — ADR-016 backup invariant 가 단순 tar 보다 strict (backup 후 verify, restore 후 chain re-verify).
3. localhost-bind invariant (config.py `validate_tls_for_host`) 와 Docker `0.0.0.0` bind 충돌.
4. cross-stack volume — status_adapter 가 mctrader-data Pilot named volume 의 데이터에 의존.

## §2. Scope

### §2.1 Phase 4 본 Story (in-scope)

mctrader-web repo Docker-first 전환. multi-service compose (api + panel), single named volume `mctrader_web_data` (api RW only), 양 service healthcheck (FastAPI `/health` + Streamlit `/_stcore/health`), in-process asyncio.Task 패턴 유지 (ADR-014), localhost-bind env override path, cross-stack volume RO mount + standalone fallback env, ADR-016 amendment (Docker volume backup + WAL-aware tar + hash chain verify integration + restore genesis preservation).

### §2.2 본 Story 결정점 (D1-D13, brainstorming freeze)

Codex 의견 + Sonnet decider 합성 결과 13 항목. 본 §2.2 가 결정 박제:

| Decision | 채택 | Rejected |
|---|---|---|
| **D1 Compose service** | α 2 service (api: FastAPI / panel: Streamlit) | β 1-service multi-process (supervisord) / γ 1-service api only / δ 2-service + audit-cron sidecar |
| **D2 Volume sharing** | α single named volume `mctrader_web_data` (api RW only, panel API-only) + env override for `~/.mctrader` paths (`MCTRADER_TOKEN_PATH=/var/lib/mctrader/web/token` 등) | β both services mount / γ separated volumes (audit + token) / δ host bind for token |
| **D3 SQLite DR** | γ backup-then-verify + restore safety (ADR-016 hash chain integrity-aware) | α Pilot tar 단순 / β backup-then-verify only / δ read replica volume |
| **D4 Healthcheck** | α both services (api `/health`, panel `/_stcore/health`) | β api only / γ 별도 health_server.py 신규 (Pilot 처럼 — but FastAPI 가 이미 endpoint 보유 → 불요) |
| **D5 Engine integration** | α in-process asyncio.Task (current 유지, ADR-014 정합) | β subprocess / γ separate container |
| **D6 Localhost-bind** | α 0.0.0.0 in container + host port 미노출 (`ports:` 미명시) + env override `MCTRADER_API_HOST` (default 127.0.0.1) + `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1` (compose 안에서만 set, validate_tls_for_host exempt) | Option1 localhost set 확장 / Option3 self-signed cert auto-gen / Option4 nginx sidecar |
| **D7 mctrader-data CLI in-image** | α git+https install (이미 pyproject core dep, `@main` 유지 — pinning Story 별도) | β Python API refactor / γ separate sidecar |
| **D8 Cross-stack volume** | α external volume `mctrader-data_mctrader_data` RO mount (compose `external: true`) + fallback `MCTRADER_DISABLE_DATA_STATUS=1` env (standalone deployment 시 status_adapter mock yellow) | β mctrader-data 를 mctrader-web compose 에 통합 / γ status_adapter disable / δ host manual cross-mount |
| **D9 Audit retention cron** | α host cron only (README docs `docker exec` 패턴) | β audit-cron sidecar (P6+ Story 후보) / γ in-process apscheduler |
| **D10 Streamlit healthcheck** | α `/_stcore/health` + python urllib | β custom Streamlit page route / γ panel sidecar |
| **D11 .dockerignore** | explicit list — `data/`, `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `*.ps1` (win-only), `*.sqlite-wal`, `*.sqlite-shm`, `.git`, `.github`, `.claude`, `*.md`, `docs/` | — |
| **D12 ADR amendment** | γ ADR-016 amendment 단독 (§"Backup + retention" 절에 Docker volume backup + WAL checkpoint + hash chain verify + restore genesis preservation 추가) | α 추가 amend 0 / β ADR-009 §D12 amend / δ ADR-014 amend |
| **D13 Phase 3 coordination** | ADR-009 §D12 = common Docker pattern only / ADR-016 = audit-DB-specific (본 Story) / engine paper daemon Phase 3 = 별도 ADR (ADR-002 D6 amend 또는 신규) 후보 | — |

### §2.3 Out-of-scope (Epic 후속 Story 또는 별도)

- mctrader-data CLI dep version pinning (D7 — `@main` 유지, semver pinning 별도 Story)
- audit-cron sidecar 자동화 (D9 β — P6+ ops 자동화 Story)
- ghcr.io publish workflow + multi-arch buildx (Pilot Out-of-scope F1-F2 carry-over)
- trivy image-ref scan 활성화 (publish 후 — Pilot F2)
- distroless / digest pin / cosign signing (Pilot F3)
- TLS production cert 자동화 (gen_dev_cert.{ps1,sh} 유지 — production 별도 ops)
- Phase 5 bithumb sister rollout (Phase 5 entry 조건 만족 — 별도 Story)

## §3. 도입할 설계 (target)

### §3.1 Architecture overview

mctrader-web 을 2 service compose 로 전환:

- **`api` service**: FastAPI uvicorn, internal 0.0.0.0:7821 bind (compose-internal network only — host port 미노출). env override 로 `validate_tls_for_host` exempt.
- **`panel` service**: Streamlit, internal 0.0.0.0:8501 bind (host port 노출 — 사용자 browser 접근). api_client 이 service name `api:7821` 호출.
- **shared named volume `mctrader_web_data`**: api 만 RW mount. panel = API-only (ADR-014 control vs data plane separation 정합 — panel 은 status read 만).
- **external named volume `mctrader-data_mctrader_data`** (RO mount on api only) — Pilot stack volume 차용. status_adapter 가 OHLCV/heartbeat data path read.
- ADR-014 in-process invariant 유지: PaperRunner / BacktestRunner / WfoRunner 가 uvicorn event loop 안 asyncio.Task. process boundary 추가 0.

### §3.2 Components (file 단위 변경)

#### 신규 파일 (mctrader-web)

| 파일 | 책임 |
|---|---|
| `Dockerfile` | python:3.12-slim 2-stage (deps → runner). uv install (mctrader-market / mctrader-engine / mctrader-data git+https). runtime non-root user `mctrader` (UID 1001). HEALTHCHECK directive 포함 (`/health`). |
| `compose.yml` | 2 service (api + panel). volumes: `mctrader_web_data` (named, api RW) + `mctrader-data_mctrader_data` (external, api RO). networks: bridge default. api `ports:` 미명시 (host expose 0). panel `ports: 8501:8501` (host browser). depends_on api healthcheck. env: D6 override (`MCTRADER_API_HOST=0.0.0.0`, `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1`), D2 path override (`MCTRADER_TOKEN_PATH=/var/lib/mctrader/web/token`, `MCTRADER_ADMIN_AUDIT_PATH=/var/lib/mctrader/web/admin_audit.sqlite`, `MCTRADER_LOCK_PATH=/var/lib/mctrader/web/paper.lock`, `MCTRADER_ADMIN_TOKEN_SECRET=...`), D8 fallback (`MCTRADER_DISABLE_DATA_STATUS=` default unset, standalone 시 set). healthcheck per service. restart unless-stopped. |
| `.dockerignore` | D11 explicit list (Pilot 패턴 + mctrader-web 특화) |
| `.github/workflows/image-lint.yml` | hadolint job (codeforge `templates/github-workflows/container-image-scan.yml` reusable 또는 inline) |
| `CHANGELOG.md` | 신규 — `[0.14.0]` Docker-first BREAKING entry (mctrader-web 의 첫 CHANGELOG) |
| `tests/integration/README.md` | manual smoke 절차 — multi-service healthy + sqlite WAL+hash chain backup verify + cross-stack volume RO read + restart preservation |
| `tests/test_config_localhost_bind.py` (신규 또는 수정) | D6 env override TDD — `validate_tls_for_host("0.0.0.0")` with `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1` → exempt PASS |
| `tests/test_status_adapter_disable.py` (신규) | D8 fallback TDD — `MCTRADER_DISABLE_DATA_STATUS=1` 시 status_adapter mock yellow return |

#### 수정 파일 (mctrader-web)

| 파일 | 변경 |
|---|---|
| `src/mctrader_web/api/config.py` | D6 env support — `MCTRADER_API_HOST` (default `DEFAULT_HOST=127.0.0.1`) + `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS` (default false). `validate_tls_for_host()` 가 NO_TLS env true 시 exempt + warning log emit. |
| `src/mctrader_web/api/cli.py` | `MCTRADER_API_HOST` env read (override DEFAULT_HOST), `validate_tls_for_host()` 호출 후 uvicorn start. |
| `src/mctrader_web/dashboard/status_adapter.py` | D8 fallback — `MCTRADER_DISABLE_DATA_STATUS=1` 시 mock yellow `StatusResult(worst_level=1, error="data status disabled")` return (subprocess call skip). |
| `.claude/_overlay/project.yaml` | `infra_strategy: docker_first` field 추가 (codeforge `check-container-strategy.sh` lint PASS) |
| `README.md` | 전면 재작성 (v0.1.0 placeholder → v0.14.0 actual). "Docker deployment" 절 (multi-service 명시 + 양 service healthcheck + cross-stack volume 의존 + standalone fallback env). install / config / ops / health / DR section. ADR-016 audit DR recipe (Docker 특화) 박제. |
| `pyproject.toml` | version 0.13.0 → 0.14.0 (semver minor — feature add, deploy 자산 추가만 — no API surface change) |
| `.gitignore` | `data/admin_audit.sqlite` + `*.sqlite-wal` + `*.sqlite-shm` 명시 (이미 dev artifact 존재 — git history 정리는 본 Story scope 외) |

#### 삭제 파일

(Pilot 과 다름 — systemd 자산 0, 삭제 대상 0)

#### 신규 파일 (mctrader-hub — spec/plan/Story/ADR)

| 파일 | 책임 |
|---|---|
| `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md` | 본 spec 파일 |
| `docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md` | impl plan (writing-plans skill 산출) |
| `docs/stories/MCT-101.md` | Story file (`## 1.` ~ `## 11.` 번호 section, MCT-99/97 reference format) |

#### 수정 파일 (mctrader-hub — ADR amendment)

| 파일 | 변경 |
|---|---|
| `docs/adr/ADR-016-audit-log-immutability.md` | §"Backup + retention" 절에 4 항목 amendment (D12 γ): Docker named volume backup recipe (alpine tar + WAL checkpoint 사전 호출) / backup 직후 hash chain verify CLI 자동 실행 / Restore 시 genesis hash preservation invariant + restore 후 chain re-verify / NFS/SMB volume 금지 cross-platform invariant. Amendment History entry 추가 (2026-05-08 — MCT-101 Phase 4). |

ADR-009 §D12 추가 amendment 0 (D12 채택 — Phase 3 race 회피).

### §3.3 Data flow / runtime

#### Build time

1. `docker compose build` → 두 service 가 같은 Dockerfile build (다른 CMD / entrypoint).
2. **Stage 1 (deps)**: python:3.12-slim + uv install (mctrader-market / mctrader-engine / mctrader-data git+https core deps + dashboard extra streamlit/plotly/pandas). Stage 1 만 outbound (git+https).
3. **Stage 2 (runner)**: minimal slim base + Stage 1 site-packages COPY + 양 entry script (`mctrader-web-api`, `mctrader-dashboard`). non-root mctrader UID 1001. HEALTHCHECK directive 미포함 (compose-side healthcheck 가 service 별로 다름).

#### Runtime — api service

```
docker compose up -d api
  ↓
container start → ENTRYPOINT [mctrader-web-api]
  reads MCTRADER_API_HOST=0.0.0.0 (compose env)
  reads MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1 (compose env)
  validate_tls_for_host("0.0.0.0") → NO_TLS env true → exempt + warning log
  uvicorn.run("mctrader_web.api.app:app", host="0.0.0.0", port=7821)
  ↓
FastAPI lifespan startup
  ↓ LifecycleManager / BacktestLifecycleManager / WfoLifecycleManager init
  ↓ MultiTokenAuth (DB-backed, 3-role RBAC) — audit_db.py 가 /var/lib/mctrader/web/admin_audit.sqlite open + WAL + DDL bootstrap
  ↓ Token loaded from /var/lib/mctrader/web/token (env override path)
  ↓ Token secret loaded from MCTRADER_ADMIN_TOKEN_SECRET env
  ↓ /health + /admin/health 양쪽 200 OK
  ↓
healthcheck 30s interval — python urllib http://localhost:7821/health → 200 → healthy
  ↓
panel container 안에서 api_client httpx GET http://api:7821/admin/* → MultiTokenAuth pass
  ↓ 사용자 panel UI 에서 paper run / backtest / WFO start → api 가 asyncio.Task spawn (in-process)
  ↓
docker compose stop
  ↓ SIGTERM → FastAPI lifespan shutdown → LifecycleManager.shutdown() → in-flight asyncio.Task cancel + drain → uvicorn graceful shutdown
```

#### Runtime — panel service

```
docker compose up -d panel
  ↓
depends_on api healthcheck → wait until api healthy
  ↓
container start → ENTRYPOINT [streamlit run src/mctrader_web/dashboard/app.py --server.address=0.0.0.0 --server.port=8501]
  ↓
Streamlit boots / `/_stcore/health` 200 OK
  ↓
healthcheck 30s — python urllib http://localhost:8501/_stcore/health → 200 → healthy
  ↓
사용자 browser → http://localhost:8501 (host port mapping)
  ↓
panel app 안에서 api_client.MctraderApiClient(host="api", port=7821) → cross-container HTTP
  ↓
status_adapter 가 mctrader-data CLI subprocess.run (image 안 PATH 에 mctrader-data 있음) — but read 대상 file path = /var/lib/mctrader/data (mctrader-data Pilot named volume, RO mount on api only)
  ↓ 만약 MCTRADER_DISABLE_DATA_STATUS=1 (standalone deployment) → mock yellow
```

#### Network boundary

- **api**: compose-internal bridge network. `0.0.0.0:7821` listen (compose `ports:` 미명시 → host expose 0). panel container 만 `api:7821` 도달.
- **panel**: compose-internal bridge + host port mapping `8501:8501` (host browser 접근).
- **api outbound**: PaperRunner / BacktestRunner 가 mctrader-engine code path 통해 mctrader-market-* (Bithumb Public WS / API) outbound — Pilot mctrader-data 와 동일.
- **Network mode**: bridge default. host network 미사용.

#### Volume / persistence

| Volume | Mount | RW/RO | 책임 |
|---|---|---|---|
| `mctrader_web_data` (named) | api: `/var/lib/mctrader/web` | RW | admin_audit.sqlite, token, token_secret, paper.lock |
| `mctrader-data_mctrader_data` (external — Pilot stack volume) | api: `/var/lib/mctrader/data` | RO | OHLCV / tick / orderbook / heartbeat data (status_adapter read) |

panel 은 어떤 volume 도 mount 안 함 — API-only access.

#### 3 mode (backtest/paper/live) 와의 관계

- backtest one-shot = BacktestRunner asyncio.Task (api 안)
- paper daemon = PaperRunner asyncio.Task (api 안, single-active enforcement via paper.lock)
- live = 본 Story scope 외 (Phase 5+ — engine repo + secret management)

### §3.4 D6 TLS env override 메커니즘 상세

`config.py` 신규 env:

```python
def get_api_host() -> str:
    return os.environ.get("MCTRADER_API_HOST", DEFAULT_HOST)  # default 127.0.0.1

def is_non_localhost_no_tls_allowed() -> bool:
    return os.environ.get("MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS", "").lower() in ("1", "true", "yes")

def validate_tls_for_host(host: str) -> None:
    if is_localhost_binding(host):
        return
    if is_non_localhost_no_tls_allowed():
        # Docker compose-internal network exempt — host port 미노출 invariant 가 보안 보장
        warnings.warn("TLS validation bypassed via MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS — assumed compose-internal network with host port not mapped")
        return
    cert = get_tls_cert_path()
    key = get_tls_key_path()
    if cert is None or key is None:
        raise ValueError(...)  # 기존 invariant
```

**보안 invariant**: env true 시 host port mapping 0 의무 (compose `ports:` 미명시 의무 → host network 노출 0 → TLS 부재 위험 0). README + compose.yml 의 양쪽 자산이 invariant 표현.

### §3.5 D8 Cross-stack volume + standalone fallback

compose.yml:

```yaml
services:
  api:
    volumes:
      - mctrader_web_data:/var/lib/mctrader/web:rw
      - mctrader-data_mctrader_data:/var/lib/mctrader/data:ro

volumes:
  mctrader_web_data:
    # local driver default
  mctrader-data_mctrader_data:
    external: true
    # name = mctrader-data Pilot stack 의 named volume (Pilot project name = "mctrader-data" → volume = "mctrader-data_mctrader_data")
```

**standalone deployment** (mctrader-data peer 미가동):

```bash
# .env or compose env
MCTRADER_DISABLE_DATA_STATUS=1
```

`status_adapter.fetch_status()` 가 첫 line 에서 env check → mock `StatusResult(worst_level=1, error="data status disabled (MCTRADER_DISABLE_DATA_STATUS=1)")` return. panel admin status section "yellow" 표시 + 메시지.

**volume 이름 invariant**: Pilot project name = `mctrader-data` (mctrader-data repo directory). volume namespace = `<project>_<volume>` = `mctrader-data_mctrader_data`. Pilot Story §9.2 evidence 박제 (`docker volume inspect mctrader-data_mctrader_data` 명시).

### §3.6 D12 ADR-016 amendment — Docker volume backup + hash chain integrity

ADR-016 §"Backup + retention" 절에 4 항목 추가:

#### A1. Docker named volume backup recipe (PowerShell + bash)

```powershell
# Backup (api container running)
$timestamp = Get-Date -Format yyyyMMdd_HHmmss
docker compose exec api python -c "
import sqlite3
conn = sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite')
conn.execute('PRAGMA wal_checkpoint(FULL)')
conn.close()
"
docker run --rm `
  -v mctrader_web_data:/source:ro `
  -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_web_audit_${timestamp}.tar.gz -C /source .

# Verify hash chain immediately after backup
docker compose exec api mctrader-cli audit-verify
```

```bash
# Backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec api python -c "import sqlite3; c=sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite'); c.execute('PRAGMA wal_checkpoint(FULL)'); c.close()"
docker run --rm \
  -v mctrader_web_data:/source:ro \
  -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_web_audit_${TIMESTAMP}.tar.gz -C /source .
docker compose exec api mctrader-cli audit-verify
```

#### A2. Backup-then-verify invariant

backup 직후 즉시 `mctrader-cli audit-verify` 실행 의무. 실패 시 backup file 삭제 + alert (operator 의무).

#### A3. Restore safety + genesis preservation

```bash
# Stop api service before restore (volume detach 회피)
docker compose stop api
# Restore archive
docker run --rm \
  -v mctrader_web_data:/dest \
  -v "$(pwd):/backup" \
  alpine tar xzf /backup/mctrader_web_audit_<TIMESTAMP>.tar.gz -C /dest
# Restart + immediate chain re-verify
docker compose start api
docker compose exec api mctrader-cli audit-verify
```

restore 후 chain re-verify FAIL 시 = backup corruption → restore 롤백 (이전 backup 시도 또는 manual chain forensics).

#### A4. Cross-platform invariant

- Windows + Linux Docker Desktop 양쪽 동등 (named volume 의 underlying fs = local driver).
- **NFS / SMB / network filesystem 위 named volume 금지** — WAL fsync 보장 안 됨 → hash chain race 가능.

### §3.7 §7.4 OpRiskArch 4 항목 mapping (Pilot 패턴 차용)

#### 1. Container restart policy

- 양 service `restart: unless-stopped` (compose-side)
- 근거: Pilot 동일. operator stop 외엔 항상 가동.

#### 2. Volume DR

- `mctrader_web_data` named volume + ADR-016 amendment 의 4 항목 backup invariant 적용 (Pilot 의 OHLCV tar 와 다른 strict pattern)
- `mctrader-data_mctrader_data` external = mctrader-data stack 의 own DR (본 Story scope 외)

#### 3. Health check tuning

| Service | test | interval | timeout | retries | start_period |
|---|---|---|---|---|---|
| api | python urllib http://localhost:7821/health | 30s | 10s | 3 | 60s |
| panel | python urllib http://localhost:8501/_stcore/health | 30s | 10s | 3 | 60s |

api start_period = uvicorn boot + LifecycleManager init + MultiTokenAuth DB DDL bootstrap. panel start_period = Streamlit boot + first page load (60s 충분).

#### 4. Network mode boundary

- compose default bridge network
- `network_mode: host` 금지
- api `ports:` 미명시 (host expose 0). panel `ports: 8501:8501` (host browser 의 의도적 expose).
- outbound: NAT 로 Bithumb 도달 (api 안 mctrader-engine code path 가 mctrader-market-* 호출).

## §4. API 계약

**N/A — production runtime API 변경 0개.**

근거: 본 Story 는 deploy 자산 + env override 추가만. FastAPI route surface 변경 0. Streamlit page 변경 0. api_client.MctraderApiClient signature 변경 0 (host parameter 만 default 변경 — 이미 keyword arg).

단 다음 신규 env semantics 추가 (config.py):

| Env | Default | 의미 |
|---|---|---|
| `MCTRADER_API_HOST` | `127.0.0.1` | uvicorn bind host. compose-internal 시 `0.0.0.0`. |
| `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS` | unset (false) | non-localhost bind 시 TLS validate exempt. compose-internal network only — host expose 0 의무. |
| `MCTRADER_TOKEN_PATH` | `~/.mctrader/local_token` | token file path. compose 시 named volume path. |
| `MCTRADER_ADMIN_AUDIT_PATH` | `<package>/data/admin_audit.sqlite` | audit DB path. compose 시 named volume path. |
| `MCTRADER_ADMIN_TOKEN_SECRET` | `~/.mctrader/token_secret` 파일 또는 dev fallback | HMAC secret. compose 시 explicit env value. |
| `MCTRADER_LOCK_PATH` | None (engine default) | paper.lock path. compose 시 named volume path. |
| `MCTRADER_DISABLE_DATA_STATUS` | unset (false) | standalone deployment 시 status_adapter mock yellow. |

위 env 는 기존 `MCTRADER_TOKEN_PATH` / `MCTRADER_ADMIN_AUDIT_PATH` / `MCTRADER_ADMIN_TOKEN_SECRET` 와 일관된 naming convention.

## §5. 보안 설계

### §5.1 Trust boundary

- **Host network boundary**: compose `ports:` 절 — api 미명시 (expose 0), panel 8501 만 expose. 사용자 browser 외 host network 노출 0.
- **Compose-internal network boundary**: api ↔ panel = bridge default network. 양 service 동일 compose project — service name resolution.
- **Image build context boundary**: `.dockerignore` strict — `data/`, `*.sqlite*`, `.git`, `.github`, `.claude`, `.coverage`, `.pytest_cache`, `.ruff_cache`, `.venv`, `*.ps1`, `*.md`, `docs/` 모두 제외. dev sqlite + git history + CI tokens 누설 0.
- **Layer cache boundary**: 2-stage Dockerfile (deps / runner). Stage 1 만 git+https outbound. Stage 2 wheel COPY only.

### §5.2 Threat model (STRIDE 발췌)

| 컴포넌트 | 위협 | 본 Story 완화 |
|---|---|---|
| Container image | base image stale CVE | python:3.12-slim. trivy = Out-of-scope (publish Story 후) |
| Container image | image layer 안 secret 누설 | `.dockerignore` strict. token / token_secret 모두 named volume path (image 미포함). hadolint syntax 검증. |
| compose network | service-to-service spoofing | api ↔ panel 양 service. api 가 MultiTokenAuth (Bearer) 로 panel 의 모든 호출 검증. service-to-service trust 자체는 compose-internal bridge network — 동일 compose project 내부 spoofing 없음. |
| compose network | host network 노출 | api `ports:` 미명시 (host expose 0). panel 만 8501 expose (사용자 browser intent). |
| TLS bypass | compose-internal network 의 비-localhost bind 시 TLS 부재 | `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1` env 시 exempt — but host port mapping 0 의무 (compose.yml `ports:` 미명시 + README 의 invariant 박제). 외부 network 노출 0 보장 시 TLS 부재 안전. |
| Volume | host path escape | named volume only. host bind mount 미사용. |
| Audit DB | hash chain tamper | append-only invariant (audit_db.py 의 ORM-level 가드 + DB UPDATE/DELETE 차단). Docker volume backup 시 ADR-016 amendment 의 backup-then-verify invariant 적용. |
| Cross-stack volume | mctrader-data Pilot volume mutate | RO mount on api (`:ro` flag). api 의 status_adapter 는 read 만. |
| Standalone deployment | status_adapter 의 fake green return | `MCTRADER_DISABLE_DATA_STATUS=1` 시 explicit yellow + error message. silent green 0. |

### §5.3 Auth/Authz

본 Story 는 기존 ADR-014 (control vs data plane separation) + ADR-016 (audit hash chain) 의 RBAC 그대로 적용. compose 환경에서 변경 0:

- MultiTokenAuth (DB-backed, 3 role: viewer / operator / admin)
- /admin/control/* → operator | admin + Idempotency-Key
- /admin/status/* → viewer 이상
- audit_log append-only (control plane only, data plane 미적용)

### §5.4 §7.4 운영 리스크

§3.7 의 4 항목 매핑 (restart policy / volume DR / health check / network mode). ADR-033 §결정 5 deputy mandate 매트릭스 cell annotation 준수. Pilot Story §11.4 의 "high risk" 분류는 multi-service novelty + sqlite hash chain DR — 양쪽 모두 §3.5 + §3.6 박제로 mitigation.

### §5.5 민감 데이터 분류

- audit_log = forensic record (operator action history). 분류: Internal (organizational scope).
- token / token_secret = HMAC secret + auth token. 분류: Confidential.
- 둘 다 named volume 안에서만 보관. image layer 미포함. host network 노출 0 (api ports 미명시).
- mctrader-data RO mount = public market data — Pilot 동일.
- log / error 에 token / secret 누설 0 (기존 코드 정합).

### §5.6 N/A 명시

- §5.3 Auth/Authz = 기존 ADR-014/016 그대로.
- §5.5 = 본 Story 의 주요 risk = audit DB integrity (§5.2 + §3.6 박제).

## §6. 테스트 계획

### §6.1 Unit (pytest)

- `tests/test_config_localhost_bind.py` (D6 TDD, 4 시나리오):
  1. `is_localhost_binding("127.0.0.1")` → True (기존 정합)
  2. `validate_tls_for_host("0.0.0.0")` + NO_TLS env 미설정 → ValueError raise (기존 invariant)
  3. `validate_tls_for_host("0.0.0.0")` + `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1` → exempt + warning emit
  4. `get_api_host()` env override (`MCTRADER_API_HOST=0.0.0.0`) 적용 검증
- `tests/test_status_adapter_disable.py` (D8 TDD, 2 시나리오):
  1. `MCTRADER_DISABLE_DATA_STATUS` 미설정 → 기존 subprocess.run path
  2. `MCTRADER_DISABLE_DATA_STATUS=1` → mock `StatusResult(worst_level=1, error=...)` return, subprocess.run 호출 0
- 기존 pytest 회귀 PASS 유지 (D6/D8 추가만, production code path 무관).

### §6.2 Integration (compose smoke)

- `tests/integration/test_compose_up.sh` (manual, CI 부담 회피):
  1. `docker compose build` exit 0
  2. `docker compose up -d` exit 0
  3. 90초 대기 (api start_period 60s + panel 30s) 후 `docker compose ps` → 양 service `healthy`
  4. `docker compose exec api python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:7821/health').status==200 else 1)"` exit 0
  5. `docker compose exec panel python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"` exit 0
  6. `docker volume inspect mctrader-web_mctrader_web_data` 존재 확인
  7. external volume 존재 시 (`docker volume inspect mctrader-data_mctrader_data`) → api status_adapter live data return / 부재 시 → standalone fallback env 추가 후 mock yellow 검증
  8. `docker compose down` (volume 보존) → `docker compose up -d` → audit DB 재마운트 후 schema 보존 검증 (sqlite SELECT count(*) FROM audit_log)
  9. ADR-016 amendment §A2 backup-then-verify smoke: `docker compose exec api ...wal_checkpoint... + alpine tar + audit-verify` exit 0
- Bithumb live WS 의존 부분 (status_adapter) 은 manual + CI 는 syntax-only (`docker compose config`).

### §6.3 Lint

- `hadolint Dockerfile` (image-lint.yml workflow 호출, failure-threshold=warning)
- `actionlint .github/workflows/image-lint.yml`
- `bash scripts/check-container-strategy.sh` (codeforge lint, `infra_strategy: docker_first` + Dockerfile + compose.yml 모두 존재 → exit 0 PASS)
- `docker compose config` (compose.yml syntax + external volume reference validation)

### §6.4 §8.5 Stateful invariant tests (manual)

mctrader-web 은 long-running multi-service + state-aware → §8.5 적용 의무:

- **Volume 보존 (audit_log)**: `up → admin control 명령 N회 → down → up → audit_log row count == N + hash chain verify PASS`
- **Volume 보존 (token)**: `up → token rotate → down → up → 새 token 인증 PASS`
- **Cross-stack volume RO**: `up (data peer 가동) → status_adapter green/yellow live → down → standalone env set → up → mock yellow`
- **Restart policy**: `kill api container → docker auto-restart → 60s 후 healthy → audit_log SELECT 보존`
- **paper.lock invariant**: `up → paper run start → kill api → restart → paper.lock 회수 + 재시작 가능 (mctrader-engine paper_lock invariant 정합)`
- **SIGTERM graceful shutdown**: `up + paper run active → docker compose stop → in-flight task drain (LifecycleManager.shutdown()) → audit_log 마지막 row 정상 commit`

### §6.5 TDD 진입 순서

1. D6 `tests/test_config_localhost_bind.py` 4 시나리오 RED
2. `config.py` env getter + `validate_tls_for_host` exempt path GREEN
3. `cli.py` `MCTRADER_API_HOST` env read GREEN
4. D8 `tests/test_status_adapter_disable.py` 2 시나리오 RED
5. `status_adapter.py` env check GREEN
6. Dockerfile 작성 (양 entry script wiring, hadolint PASS)
7. compose.yml 작성 (2 service + named + external volume + healthcheck + ports + env, `docker compose config` PASS)
8. `infra_strategy: docker_first` field 추가 → `check-container-strategy.sh` PASS
9. `.dockerignore` 작성
10. `.github/workflows/image-lint.yml` 작성
11. README 전면 재작성 (v0.1.0 → v0.14.0)
12. CHANGELOG.md 신규 작성
13. ADR-016 amendment commit (mctrader-hub side)

### §6.6 Coverage 목표

- D6 + D8 신규 코드 100% line
- integration smoke = manual + CI = syntax-only

## §7. Migration / Cross-platform parity

### §7.1 systemd 자산 처리

mctrader-web 은 systemd 자산 0건 (`deploy/` 디렉토리 부재). 삭제 대상 0. Pilot 과 다름.

### §7.2 기존 dev artifact 처리

- `data/admin_audit.sqlite` 이미 repo 안에 commit 됨 (dev artifact, hash chain commitment).
- `.gitignore` 에 `data/admin_audit.sqlite` + `*.sqlite-wal` + `*.sqlite-shm` 추가 (forward-only — 본 Story 가 git history 에서 sqlite 제거 안 함).
- `.dockerignore` 가 `data/` 전체 제외 → image 안 dev sqlite 누설 0.
- 첫 컨테이너 부팅 시 named volume 안에서 audit_db.py 가 idempotent `_create_audit_tables()` 자동 schema bootstrap (genesis row 없음 → 첫 control 명령 시 first row).

### §7.3 Cross-platform parity (Windows dev → Linux prod)

- Windows Docker Desktop + Linux host 양쪽 동등 (Pilot 동일).
- `gen_dev_cert.{ps1,sh}` 양쪽 plat script 유지 (TLS production 별도 ops).
- ADR-016 amendment §A4 의 NFS/SMB volume 금지 invariant.

### §7.4 Rollback 경로 (Phase 4 검증 실패 시)

- git revert PR 로 commit 복구 (Dockerfile / compose.yml / .dockerignore / config.py / status_adapter.py 변경 모두 제거).
- production 운영 중 아니므로 host cleanup 불요.
- volume `mctrader_web_data` = `docker volume rm` 으로 삭제 OR 다음 시도 위해 보존 — 사용자 재량.
- audit_log hash chain 보존 의무 시 `mctrader-cli audit-verify` 후 backup 보관.

### §7.5 Cutover 검증 (Story §10 acceptance evidence)

1. Windows / Linux 어느 host 에서든 `docker compose build && docker compose up -d` → 90s 후 양 service healthy.
2. `docker compose exec api .../health` → 200 + `docker compose exec panel .../_stcore/health` → 200.
3. browser http://localhost:8501 → Streamlit page load + admin login → status panel green (data peer 가동) 또는 yellow (standalone).
4. admin control 명령 1 회 (예: paper run start/stop) → audit_log row +1 + hash chain verify PASS.
5. `docker compose down && docker compose up -d` → audit_log row 보존 + hash chain verify PASS.
6. ADR-016 amendment §A1 backup recipe 실행 → tar.gz 생성 + verify-after-backup PASS.
7. ADR-016 amendment §A3 restore drill — backup 후 audit DB 변경 → restore → verify PASS (genesis preservation invariant).
8. `hadolint Dockerfile` warning 0.
9. `bash scripts/check-container-strategy.sh` PASS.
10. `pytest tests/` 기존 + 신규 D6/D8 시나리오 모두 PASS.

## §8. 영향 / 의존

### §8.1 codeforge 의존

- ADR-033 (CFP-128 Accepted 2026-05-07)
- `templates/github-workflows/container-image-scan.yml` (hadolint reusable)
- `scripts/check-container-strategy.sh` (consumer lint)
- `examples/webapp-minimal/{Dockerfile,compose.yml}` — 패턴 참조 (multi-service / healthcheck / named volume — but mctrader-web 은 sqlite-only stack 이라 webapp-minimal 의 postgres+redis 는 직접 차용 안 함, 패턴만)
- `examples/cli-tool-minimal/Dockerfile` + `.dockerignore` — Pilot 과 동일 reference

### §8.2 mctrader-hub Epic 후속

- Epic Story MCT-98 (mctrader-hub#120) Phase 4 status update 의무 (본 Story PR merge 후)
- Phase 3 (engine MCT-100) parallel — 양 PR merged 후 마지막 merge session 이 reconciliation commit (Phase 3+4 status 동시 박제). 본 Story 가 마지막 merge 인 경우 reconciliation 책임.

### §8.3 ADR amendment

- **ADR-016 amendment 단독** (D12 채택). Amendment History 2026-05-08 entry. mctrader-hub doc PR 안에 commit.
- **ADR-009 §D12 추가 amendment 0** (Phase 3 race 회피).
- **ADR-014 변경 0** (single-process invariant 그대로).

### §8.4 Phase 3 (engine MCT-100) cross-cutting surface

memory file `project_dockerization_phase4.md` 박제 (이미 작성). 4 항목:

1. ADR-014 single-process invariant 재사용 — engine paper daemon 도 in-process asyncio.Task 패턴 검토 권장
2. HealthServer 패턴 차용 — engine 도 HTTP `/health` endpoint, web 의 `/admin/health` 패턴이 daemon shape 에 더 가까움
3. Cross-stack volume RO mount 패턴 — engine paper daemon 도 mctrader-data named volume RO mount + standalone fallback env 차용
4. ADR-009 §D12 추가 amendment 회피 — Phase 3 가 §D12 자유 또는 ADR-002 D6 amend / 신규 ADR 후보

## §9. Future work / Open questions

| ID | 항목 | 처리 방향 |
|---|---|---|
| F1 | mctrader-data CLI dep version pinning (D7) | Pilot Out-of-scope F1-F2 carry-over + 본 Story 도 carry-over (Phase 6+ semver Story) |
| F2 | audit-cron sidecar 자동화 (D9 β) | P6+ ops 자동화 별도 Story |
| F3 | TLS production cert 자동화 | gen_dev_cert.{ps1,sh} 유지, production = 별도 ops Story |
| F4 | Phase 5 bithumb sister rollout | Phase 5 entry 조건 만족, 별도 Story (mctrader-market-bithumb infra_strategy: none + smoke verified) |
| F5 | webapp-minimal codeforge example update | mctrader-web 패턴이 webapp-minimal 의 postgres+redis 와 다름 — codeforge 측 example update 후보 (별도 codeforge Story) |
| O1 | ADR-002 D6 (engine paper ledger) Docker 처리 | Phase 3 (engine MCT-100) session 결정 — 본 Story scope 외 |
| O2 | mctrader-engine 의 paper daemon shape | Phase 3 결정 (1-service vs multi-service 선택, web 패턴 surface 권장) |
| O3 | mctrader-data + web volume 통합 vs 분리 | 양 stack 따로 운영 (현 채택). 통합 = compose 단일화 후보 — 별도 ops Story |
| O4 | Streamlit 1.28+ 의존성 (`/_stcore/health`) | pyproject `streamlit>=1.28` 이미 만족. 호환성 향후 Streamlit 2.0 시 검증 |

## §10. 거절된 대안

§2.2 의 13 결정 의 rejected column 박제. 추가 reasoning:

| 결정 | 채택 | 거절 + 근거 |
|---|---|---|
| D1 Compose service | α 2 service | β supervisord 1-service — 격리 약, debugging 비용. γ api only — panel 이 production 자산이므로 dev tool 격하 부적절. δ 2-service + sidecar — D9 결정과 합쳐서 P6+ Story |
| D2 Volume sharing | α single + api RW only | β both mount — panel 이 RW 가 ADR-014 plane separation 위반. γ split volumes — operational 복잡도 추가. δ host bind for token — Pilot pattern 일탈 |
| D3 SQLite DR | γ backup-then-verify + restore safety | α Pilot tar 만 — ADR-016 hash chain integrity 검증 부재. β verify only — restore safety 부재. δ read replica — solo dev overkill |
| D4 Healthcheck | α both | β api only — panel daemon 가동 검증 약. γ health_server.py 신규 — FastAPI 가 endpoint 보유 → 불요 |
| D5 Engine integration | α in-process | β subprocess — ADR-014 충돌. γ separate container — solo dev overkill |
| D6 Localhost-bind | α env override | Option1 localhost set 확장 — "localhost" 의미 흐림. Option3 self-signed — 첫 부팅 복잡. Option4 nginx — overkill |
| D7 mctrader-data CLI | α git+https install | β API refactor — 본 Story scope 외. γ sidecar — overkill |
| D8 Cross-stack volume | α external + fallback env | β mctrader-data 통합 — 양 stack 분리 운영 (Pilot 유지). γ disable — operational 정보 손실. δ host manual — convention 부재 |
| D9 Audit retention | α host cron | β sidecar — P6+. γ apscheduler — single-instance 가정 약 |
| D10 Streamlit healthcheck | α `/_stcore/health` | β custom route — Streamlit limit. γ sidecar — overkill |
| D11 .dockerignore | explicit list | — |
| D12 ADR amendment | γ ADR-016 단독 | α amend 0 — Pilot pattern 만으로 hash chain integrity 부족. β ADR-009 amend — Phase 3 race. δ ADR-014 amend — single-process invariant 변경 0 |
| D13 Phase 3 coordination | ADR-016 audit-DB-specific | — |

## §11. 참고 / 관련 파일

### codeforge (외부 의존, mclayer/plugin-codeforge)

- `docs/adr/ADR-033-docker-first-infra-engineering.md` — Phase 4 trigger
- `templates/github-workflows/container-image-scan.yml` — hadolint reusable
- `scripts/check-container-strategy.sh` — consumer lint
- `examples/cli-tool-minimal/Dockerfile` + `.dockerignore` — 패턴 참조 (Pilot 동일)
- `examples/webapp-minimal/{Dockerfile,compose.yml}` — multi-service 패턴 reference (postgres+redis 는 차용 안 함)

### mctrader (관련 cross-repo 자산)

- `mctrader-data/compose.yml` — Pilot 의 named volume `mctrader_data` (mctrader-web 의 D8 external reference)
- `mctrader-data/Dockerfile` — Pilot 패턴 (2-stage / non-root / HEALTHCHECK / mctrader UID 1001)
- `mctrader-engine/src/mctrader_engine/runtime/paper_runner.py` — LifecycleManager 가 in-process import 의무 (D5)
- `mctrader-engine/src/mctrader_engine/runtime/paper_lock.py` — paper.lock host-wide invariant
- `mctrader-hub/EPIC-RESULTS-MCT-97.md` — Admin Engine Control Panel reference (MultiTokenAuth + RBAC)
- `mctrader-hub/docs/superpowers/specs/2026-05-07-mctrader-data-docker-pilot-design.md` — Pilot reference
- `mctrader-hub/docs/stories/MCT-99.md` — Pilot Story §11.4 risk classification

### mctrader-web 본 repo

- `pyproject.toml` — version bump 0.13.0 → 0.14.0
- `README.md` — 전면 재작성 (v0.1.0 placeholder → v0.14.0 actual + Docker deployment 절)
- `.claude/_overlay/project.yaml` — `infra_strategy: docker_first` 추가
- `src/mctrader_web/api/config.py` — D6 env getter 추가
- `src/mctrader_web/api/cli.py` — `MCTRADER_API_HOST` env read
- `src/mctrader_web/dashboard/status_adapter.py` — D8 `MCTRADER_DISABLE_DATA_STATUS` env handler
- `src/mctrader_web/api/admin/audit_db.py` — env-driven path (이미 보유 — 변경 0, compose env value 만 새로)

### mctrader-hub spec/plan/Story/ADR

- `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md` — 본 spec
- `docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md` — impl plan (writing-plans 산출)
- `docs/stories/MCT-101.md` — Story file (`## 1.` ~ `## 11.` section format)
- `docs/adr/ADR-016-audit-log-immutability.md` — D12 amendment commit

---

## Acceptance Criteria (요약)

1. `Dockerfile` (2-stage, python:3.12-slim, non-root mctrader UID 1001) — hadolint warning 0
2. `compose.yml` (2 service api + panel, named volume `mctrader_web_data` api RW only, external volume `mctrader-data_mctrader_data` api RO, healthcheck per service, restart unless-stopped, bridge network, api `ports:` 미명시 / panel `ports: 8501:8501`) — `docker compose config` PASS
3. `.dockerignore` — D11 explicit list
4. `config.py` D6 env override (`MCTRADER_API_HOST`, `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS`) + `validate_tls_for_host` exempt path + 4 TDD pytest PASS
5. `status_adapter.py` D8 `MCTRADER_DISABLE_DATA_STATUS` env handler + 2 TDD pytest PASS
6. `.claude/_overlay/project.yaml` `infra_strategy: docker_first` 추가
7. `bash scripts/check-container-strategy.sh` PASS
8. `.github/workflows/image-lint.yml` (hadolint job)
9. `README.md` 전면 재작성 (v0.14.0 actual + Docker deployment 절 multi-service)
10. `pyproject.toml` 0.13.0 → 0.14.0, `CHANGELOG.md` 신규 작성 `[0.14.0]` BREAKING entry
11. `tests/integration/README.md` manual smoke 절차 (multi-service healthy + sqlite WAL+hash chain backup verify + cross-stack volume RO read + restart preservation)
12. ADR-016 amendment (mctrader-hub side) — Docker volume backup + WAL checkpoint + backup-then-verify + restore genesis preservation + NFS 금지
13. Cutover 검증 10-step (§7.5) 모두 PASS evidence Story §9 에 박제
14. 기존 mctrader-web pytest 회귀 PASS 유지 (D6/D8 추가만)

---

## 다음 단계

1. 본 spec 파일 사용자 review
2. 사용자 approve 후 `superpowers:writing-plans` skill 호출 → implementation plan 작성
3. plan 작성 후 `MCT-101` Story file scaffold (`docs/stories/MCT-101.md`)
4. Phase 1 PR (mctrader-hub `docs/MCT-101-web-docker` — spec + plan + Story §1-§7 + ADR-016 amendment)
5. Phase 2 PR (mctrader-web `feat/MCT-101-docker-first` — Dockerfile + compose + config.py D6 + status_adapter.py D8 + .dockerignore + image-lint.yml + project.yaml + README + CHANGELOG + tests)
6. Phase 2 PR review chain (CodeReview + TestAgent + SecurityTest 1st-layer hadolint) + admin merge
7. Codex 7-area review per phase → fix-back commit
8. Story §11 회고 — Phase 3 reconciliation 책임 (마지막 merge 인 경우)
