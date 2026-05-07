# mctrader-data Docker-first Containerization (Pilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-data 의 collector daemon을 systemd unit에서 Docker container (single image, 2-stage Dockerfile, named volume, self-checked heartbeat)로 전환. ADR-033 §7.4 OpRiskArch 4 항목 (restart / volume DR / health check / network mode)을 compose.yml에 박제해 후속 5 sister rollout의 reference 패턴을 만든다.

**Architecture:** Python CLI 도구 (`mctrader-data`)에 `heartbeat-check` subcommand 추가 → Dockerfile에서 `HEALTHCHECK` directive로 호출. `compose.yml`이 single `collector` service + named volume `mctrader_data` + bridge network + `restart: unless-stopped`로 박제. `.claude/_overlay/project.yaml`에 `infra_strategy: docker_first` 명시해 codeforge `check-container-strategy.sh` lint 통과. systemd 자산 일괄 삭제 (production 미가동 확인됨).

**Tech Stack:** Python 3.12, uv, Docker Desktop (Windows host) + linux/amd64 image, Docker Compose, hadolint, codeforge plugin reusable workflows (`container-image-scan.yml`).

**Working repo**: `c:\workspace\mclayer\mctrader-data\` (모든 task가 본 repo 안에서 실행). plan doc 자체는 governance hub `c:\workspace\mclayer\mctrader-hub\docs\superpowers\plans\`에 저장.

**Spec reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-07-mctrader-data-docker-pilot-design.md` (commit `d12c219` on branch `feat/mctrader-data-docker-pilot-design`)

**Pre-task setup**: 본 plan 실행 전 mctrader-data repo에서 신규 branch 생성:

```powershell
cd c:\workspace\mclayer\mctrader-data
git checkout main
git pull origin main
git checkout -b feat/mctrader-data-docker-pilot
```

---

## File Structure (변경 매트릭스)

### Create (mctrader-data repo)

| 파일 | 책임 | 생성 task |
|---|---|---|
| `Dockerfile` | python:3.12-slim 2-stage build (deps → runner). non-root user `mctrader` UID 1001. `mctrader-data heartbeat-check` HEALTHCHECK. | Task 2 |
| `.dockerignore` | build context 축소 + secret leak 방지. codeforge cli-tool-minimal 패턴 + `data/` 추가. | Task 2 |
| `compose.yml` | 1 service `collector`, named volume `mctrader_data`, restart unless-stopped, bridge network, healthcheck (Dockerfile 보강). | Task 3 |
| `tests/test_heartbeat_check.py` | TDD 4 시나리오 (file 부재 / mtime 신선 / mtime stale / env override). | Task 1 |
| `tests/integration/README.md` | manual smoke 절차 박제 (compose up + healthcheck wait + volume invariant + SIGTERM graceful). | Task 7 |
| `.github/workflows/image-lint.yml` | hadolint job (codeforge `container-image-scan.yml` 참조 패턴). | Task 6 |

### Modify (mctrader-data repo)

| 파일 | 변경 | task |
|---|---|---|
| `src/mctrader_data/heartbeat.py` | `check_staleness(path: Path, threshold_sec: int) -> bool` 함수 + 관련 helper. | Task 1 |
| `src/mctrader_data/cli.py` | `heartbeat-check` subcommand 등록. | Task 1 |
| `.claude/_overlay/project.yaml` | `infra_strategy: docker_first` field 추가. | Task 4 |
| `README.md` | "Linux systemd deployment" → "Docker deployment" 절 전면 교체. | Task 5 |
| `pyproject.toml` | version `0.8.0` → `0.9.0`. | Task 8 |
| `CHANGELOG.md` (없으면 신설) | `[0.9.0]` BREAKING entry. | Task 8 |

### Delete (mctrader-data repo)

| 파일 | 이유 | task |
|---|---|---|
| `deploy/mctrader-collector.service` | systemd-only. Docker 전환. | Task 5 |
| `deploy/README.md` | systemd 가이드. README로 이전. | Task 5 |
| `deploy/` (디렉토리) | 비어있게 됨. | Task 5 |

---

## Task Ordering (TDD + dependency)

```
Task 1 (heartbeat-check CLI, RED→GREEN)
  ↓ (CLI subcommand 존재 → Dockerfile HEALTHCHECK 호출 가능)
Task 2 (Dockerfile + .dockerignore + hadolint smoke)
  ↓ (image build 가능)
Task 3 (compose.yml + docker compose config validate)
  ↓ (Docker artifact 모두 존재)
Task 4 (project.yaml infra_strategy + check-container-strategy.sh PASS)
  ↓ (codeforge lint 통과)
Task 5 (systemd 자산 삭제 + README 전면 교체)
  ↓
Task 6 (.github/workflows/image-lint.yml + actionlint)
  ↓
Task 7 (integration smoke README — manual)
  ↓
Task 8 (pyproject version bump + CHANGELOG)
  ↓
[PR open + Phase 1/2 review chain — plan 외]
```

각 task는 independent commit. 8 commit 후 PR open (또는 사용자 squash 결정).

---

## Task 1: `heartbeat-check` CLI subcommand (TDD)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\tests\test_heartbeat_check.py`
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\heartbeat.py` (function 추가)
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\cli.py` (subcommand 등록)

### Step 1.1: 기존 heartbeat.py 구조 확인

- [ ] **Step**: 기존 heartbeat 모듈을 읽어 어떤 path / threshold 패턴을 쓰고 있는지 확인.

```powershell
cd c:\workspace\mclayer\mctrader-data
Get-Content src\mctrader_data\heartbeat.py
```

Expected: 기존 heartbeat write 로직 (collector가 주기적으로 touch 하는 .heartbeat 파일 path 결정 로직). path는 `MCTRADER_DATA_ROOT/.heartbeat` 가정.

### Step 1.2: Failing test 작성

- [ ] **Step**: TDD 4 시나리오 작성.

`c:\workspace\mclayer\mctrader-data\tests\test_heartbeat_check.py`:

```python
"""TDD for `mctrader-data heartbeat-check` subcommand (MCT-N Pilot).

4 scenarios:
1. heartbeat file 부재 → exit 1, stderr "heartbeat file not found"
2. mtime <= threshold (default 90s) → exit 0
3. mtime > threshold → exit 1, stderr "heartbeat stale: <delta>s"
4. env MCTRADER_HEARTBEAT_STALENESS_SEC override 적용
"""
import os
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from mctrader_data.cli import main


def test_heartbeat_check_file_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCTRADER_DATA_ROOT", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(main, ["heartbeat-check"])
    assert result.exit_code == 1
    assert "heartbeat file not found" in result.output


def test_heartbeat_check_fresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCTRADER_DATA_ROOT", str(tmp_path))
    hb = tmp_path / ".heartbeat"
    hb.touch()  # mtime = now, fresh
    runner = CliRunner()
    result = runner.invoke(main, ["heartbeat-check"])
    assert result.exit_code == 0


def test_heartbeat_check_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCTRADER_DATA_ROOT", str(tmp_path))
    hb = tmp_path / ".heartbeat"
    hb.touch()
    # backdate mtime 200s (> default 90s threshold)
    old = time.time() - 200
    os.utime(hb, (old, old))
    runner = CliRunner()
    result = runner.invoke(main, ["heartbeat-check"])
    assert result.exit_code == 1
    assert "heartbeat stale" in result.output


def test_heartbeat_check_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """env override 30s threshold; mtime 60s 전 → stale."""
    monkeypatch.setenv("MCTRADER_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("MCTRADER_HEARTBEAT_STALENESS_SEC", "30")
    hb = tmp_path / ".heartbeat"
    hb.touch()
    old = time.time() - 60
    os.utime(hb, (old, old))
    runner = CliRunner()
    result = runner.invoke(main, ["heartbeat-check"])
    assert result.exit_code == 1
    assert "heartbeat stale" in result.output
```

### Step 1.3: Run failing test

- [ ] **Step**: 실패 검증.

```powershell
cd c:\workspace\mclayer\mctrader-data
uv run pytest tests/test_heartbeat_check.py -v
```

Expected: 4 fail (`heartbeat-check` subcommand 미등록 → click error)

### Step 1.4: heartbeat.py에 check_staleness 함수 추가

- [ ] **Step**: 기존 heartbeat.py에 다음 함수 추가 (file 끝).

```python
import os
import time
from pathlib import Path


HEARTBEAT_FILENAME = ".heartbeat"
DEFAULT_STALENESS_SEC = 90


def heartbeat_path(data_root: Path) -> Path:
    """Resolve heartbeat file path under MCTRADER_DATA_ROOT."""
    return data_root / HEARTBEAT_FILENAME


def check_staleness(data_root: Path, threshold_sec: int = DEFAULT_STALENESS_SEC) -> tuple[bool, str]:
    """Check heartbeat file freshness.

    Returns (is_fresh, message). is_fresh=False on missing file or stale mtime.
    """
    hb = heartbeat_path(data_root)
    if not hb.exists():
        return False, f"heartbeat file not found: {hb}"
    delta = time.time() - hb.stat().st_mtime
    if delta > threshold_sec:
        return False, f"heartbeat stale: {delta:.1f}s (threshold={threshold_sec}s)"
    return True, f"heartbeat fresh: {delta:.1f}s ago"


def resolve_threshold_sec() -> int:
    """Read MCTRADER_HEARTBEAT_STALENESS_SEC env, default 90."""
    raw = os.environ.get("MCTRADER_HEARTBEAT_STALENESS_SEC")
    if not raw:
        return DEFAULT_STALENESS_SEC
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_STALENESS_SEC
```

> **NOTE**: 기존 heartbeat.py에 import 가 이미 있으면 중복 line 제거. `from pathlib import Path` 등은 file 상단에 합쳐두세요.

### Step 1.5: cli.py에 subcommand 등록

- [ ] **Step**: cli.py의 main click group에 heartbeat-check subcommand 추가.

기존 cli.py에 다음 import 추가 (상단):

```python
import sys
from pathlib import Path

from mctrader_data.heartbeat import check_staleness, resolve_threshold_sec
```

main click group 안에 다음 subcommand 추가 (다른 subcommand 정의 옆):

```python
@main.command("heartbeat-check")
def heartbeat_check_cmd():
    """Check heartbeat file freshness for Docker HEALTHCHECK.

    Reads MCTRADER_DATA_ROOT (default /var/lib/mctrader/data) for .heartbeat file.
    Returns exit 0 if mtime within MCTRADER_HEARTBEAT_STALENESS_SEC (default 90).
    Returns exit 1 with stderr message otherwise.
    """
    data_root_str = os.environ.get("MCTRADER_DATA_ROOT", "/var/lib/mctrader/data")
    data_root = Path(data_root_str)
    threshold = resolve_threshold_sec()
    fresh, msg = check_staleness(data_root, threshold)
    if not fresh:
        click.echo(msg, err=True)
        sys.exit(1)
    click.echo(msg)
```

> **NOTE**: 기존 cli.py가 `import os` / `import click`를 이미 보유하면 중복 line 제거. `main`이 click group 이름인지 확인 — 기존 entrypoint `mctrader-data = "mctrader_data.cli:main"` (pyproject.toml).

### Step 1.6: Run test to verify pass

- [ ] **Step**: 4 시나리오 통과 검증.

```powershell
cd c:\workspace\mclayer\mctrader-data
uv run pytest tests/test_heartbeat_check.py -v
```

Expected: 4 passed.

### Step 1.7: 회귀 검증 — 기존 pytest 모두 PASS

- [ ] **Step**: 기존 182 pytest가 영향 없는지 확인.

```powershell
cd c:\workspace\mclayer\mctrader-data
uv run pytest -v 2>&1 | Select-String -Pattern "passed|failed" | Select-Object -Last 5
```

Expected: 모든 기존 테스트 + 신규 4 PASS, 0 fail.

### Step 1.8: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add tests/test_heartbeat_check.py src/mctrader_data/heartbeat.py src/mctrader_data/cli.py
git commit -m "feat(cli): add heartbeat-check subcommand for Docker HEALTHCHECK

mctrader-data heartbeat-check reads .heartbeat file mtime under
MCTRADER_DATA_ROOT, exits 1 if missing or older than
MCTRADER_HEARTBEAT_STALENESS_SEC (default 90s).

TDD 4 scenarios: missing / fresh / stale / env override.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 2: Dockerfile + .dockerignore + hadolint smoke

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\Dockerfile`
- Create: `c:\workspace\mclayer\mctrader-data\.dockerignore`

### Step 2.1: Dockerfile 작성

- [ ] **Step**: 2-stage Dockerfile 작성.

`c:\workspace\mclayer\mctrader-data\Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
# mctrader-data Pilot — Docker-first containerization (ADR-033 / CFP-128)
# 2-stage build: deps (uv install) → runner (slim + non-root)

#─── Stage 1: deps ───
FROM python:3.12-slim AS deps

# Install uv (pinned for reproducibility)
RUN pip install --no-cache-dir uv==0.5.11

WORKDIR /build
COPY pyproject.toml ./
COPY src/ ./src/

# uv pip install --system --no-cache (resolves git+https deps for mctrader-market / -bithumb)
RUN uv pip install --system --no-cache -e . \
    && rm -rf /root/.cache

#─── Stage 2: runner ───
FROM python:3.12-slim AS runner

# Non-root user (UID 1001)
RUN useradd --system --uid 1001 --no-create-home --shell /usr/sbin/nologin mctrader \
    && mkdir -p /var/lib/mctrader/data \
    && chown -R mctrader:mctrader /var/lib/mctrader

# Copy installed packages + entry script from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin/mctrader-data /usr/local/bin/mctrader-data

ENV MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
    PYTHONUNBUFFERED=1

USER mctrader
WORKDIR /var/lib/mctrader

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD ["mctrader-data", "heartbeat-check"]

ENTRYPOINT ["mctrader-data"]
CMD ["collect", "--top-n", "10", "--include", "transactions,orderbook", "--log-level", "INFO"]
```

### Step 2.2: .dockerignore 작성

- [ ] **Step**: .dockerignore 작성.

`c:\workspace\mclayer\mctrader-data\.dockerignore`:

```gitignore
# CFP-128 / ADR-033 — mctrader-data .dockerignore
# build context 축소 + secret leak 방지

# Build artifacts
dist
build
*.egg-info
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.coverage
htmlcov

# Git / VCS
.git
.gitignore
.gitattributes

# CI / GitHub
.github

# Codeforge
.claude
.claude-work

# Docs / markdown
*.md
docs

# Env / secrets
.env
.env.*
*.pem
*.key
*.crt

# IDE
.vscode
.idea

# OS
.DS_Store
Thumbs.db

# Local data (Parquet outputs)
data
out

# uv lock (regenerated in build)
uv.lock

# Tests (production image excludes)
tests
```

### Step 2.3: hadolint 설치 확인 + 실행

- [ ] **Step**: hadolint 로컬 검증. (Windows에서는 docker run 가능)

```powershell
cd c:\workspace\mclayer\mctrader-data
docker run --rm -i hadolint/hadolint < Dockerfile
```

Expected: 출력 0 (또는 info-level 만, warning 0).

Issue 발견 시: 가장 흔한 fail 케이스 = `DL3008` (apt-get install pin 의무 — 본 Dockerfile은 apt-get 미사용이라 무관), `DL3013` (pip install pin) → uv는 이미 0.5.11 pin, 가능 issue 없음.

### Step 2.4: Docker build smoke

- [ ] **Step**: image build 가능 여부 검증.

```powershell
cd c:\workspace\mclayer\mctrader-data
docker build -t mctrader-data:pilot .
```

Expected: build 성공 + final image 약 200-300MB 안.

build fail 시 흔한 원인:
- git+https deps 의 SSH key 의존 (`mctrader-market`, `mctrader-bithumb` 가 private repo 일 시) → 본 case는 mclayer org public 이라 무관
- platform mismatch → Windows Docker Desktop은 default linux/amd64

### Step 2.5: image entrypoint smoke

- [ ] **Step**: image 안에서 mctrader-data CLI 실행 가능 확인.

```powershell
docker run --rm mctrader-data:pilot --help
docker run --rm mctrader-data:pilot heartbeat-check
```

Expected:
- `--help`: click help text 출력
- `heartbeat-check`: exit 1 + stderr "heartbeat file not found: /var/lib/mctrader/data/.heartbeat" (volume mount 안 했으니 file 없음)

### Step 2.6: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add Dockerfile .dockerignore
git commit -m "feat(docker): Dockerfile + .dockerignore (Pilot, ADR-033)

2-stage Dockerfile (python:3.12-slim deps → runner) with non-root
user mctrader (UID 1001) and HEALTHCHECK calling heartbeat-check.

.dockerignore excludes data/, secrets, .claude, tests, docs (build
context minimization + secret leak prevention).

hadolint clean. docker build + docker run smoke verified.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 3: compose.yml + compose config validate

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\compose.yml`

### Step 3.1: compose.yml 작성

- [ ] **Step**: compose.yml 작성.

`c:\workspace\mclayer\mctrader-data\compose.yml`:

```yaml
# mctrader-data Pilot — Docker-first compose (ADR-033 §7.4 mandate 4 항목)
# - restart policy: unless-stopped (forward-only, 데이터 누락 회피)
# - volume DR: named volume mctrader_data (host path leak 방지)
# - health check: heartbeat-check self-check (interval 30s, threshold 90s)
# - network mode: bridge default, inbound port 0

services:
  collector:
    build: .
    image: mctrader-data:pilot
    container_name: mctrader-collector
    restart: unless-stopped
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      PYTHONUNBUFFERED: "1"
      # Override staleness threshold if collector startup time exceeds default 90s
      # MCTRADER_HEARTBEAT_STALENESS_SEC: "120"
    volumes:
      - mctrader_data:/var/lib/mctrader/data
    healthcheck:
      test: ["CMD", "mctrader-data", "heartbeat-check"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - mctrader-net
    # Outbound only (Bithumb pubwss + api). No inbound ports.

volumes:
  mctrader_data:
    name: mctrader_data
    # Default driver = local. Backup: docker run --rm -v mctrader_data:/src
    #   -v $(pwd):/dst alpine tar czf /dst/mctrader_data-YYYYMMDD.tar.gz -C /src .
    # ADR-009 invariant: tick/orderbook = forward-only, backfill 불가 → 일 1회 backup 권장.

networks:
  mctrader-net:
    driver: bridge
```

### Step 3.2: compose config validation

- [ ] **Step**: compose syntax 검증.

```powershell
cd c:\workspace\mclayer\mctrader-data
docker compose config
```

Expected: rendered compose YAML 출력 (no error). 변수 치환 + reference resolution 모두 OK.

### Step 3.3: compose build smoke

- [ ] **Step**: compose 통한 build 동작.

```powershell
docker compose build
```

Expected: build 성공 (Task 2.4 cache hit 시 빠름).

### Step 3.4: compose up healthy 확인 (live Bithumb 의존)

- [ ] **Step**: compose up + 60초 wait + healthy 검증.

> **WARNING**: 본 step은 Bithumb live WebSocket 연결 의존. 네트워크 장애 시 healthcheck fail. 그 경우 `docker compose logs collector --tail=30`로 에러 확인.

```powershell
docker compose up -d collector
Start-Sleep -Seconds 65
docker compose ps
```

Expected: `STATUS` column에 `Up X seconds (healthy)` 표시.

healthy 검증 후 cleanup:

```powershell
docker compose down -v
```

Expected: collector container stop + mctrader_data volume 제거.

### Step 3.5: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add compose.yml
git commit -m "feat(docker): compose.yml — collector daemon service (Pilot, ADR-033)

Single-service compose with named volume mctrader_data, restart
unless-stopped, bridge network, healthcheck via heartbeat-check.

ADR-033 §7.4 OpRiskArch 4 항목 (restart policy / volume DR /
health check tuning / network mode boundary) all encoded.

Outbound only (Bithumb pubwss + api). No inbound ports.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 4: project.yaml `infra_strategy` + check-container-strategy.sh PASS

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\.claude\_overlay\project.yaml`

### Step 4.1: 기존 project.yaml 확인

- [ ] **Step**: 기존 file의 `infra_strategy:` field 부재 확인.

```powershell
cd c:\workspace\mclayer\mctrader-data
Get-Content .claude\_overlay\project.yaml | Select-String -Pattern "infra_strategy"
```

Expected: 0 match (field 미명시 = ADR-033 default `docker_first` 자동 적용 상태).

### Step 4.2: infra_strategy field 추가

- [ ] **Step**: project.yaml의 `project:` block 다음에 `infra_strategy: docker_first` 명시.

`c:\workspace\mclayer\mctrader-data\.claude\_overlay\project.yaml`의 `project:` 블록 다음 line에 다음 추가:

```yaml
# CFP-128 / ADR-033 — Docker-first 채택 명시 (default와 동일하나 explicit)
infra_strategy: docker_first
```

> **NOTE**: 정확한 위치는 `project:` 와 `github:` 사이. yaml top-level 들여쓰기 주의 (들여쓰기 없음).

### Step 4.3: check-container-strategy.sh PASS 검증

- [ ] **Step**: codeforge plugin lint 실행.

```powershell
cd c:\workspace\mclayer\mctrader-data
bash $env:USERPROFILE\.claude\plugins\cache\claude-plugins-mclayer\codeforge\<latest>\scripts\check-container-strategy.sh
```

Plugin path 모를 시 alternative — codeforge plugin install path 검색:

```powershell
Get-ChildItem -Path $env:USERPROFILE\.claude\plugins\ -Recurse -Filter "check-container-strategy.sh" -ErrorAction SilentlyContinue
```

또는 직접 source repo에서 실행:

```powershell
bash c:\workspace\mclayer\plugin-codeforge\scripts\check-container-strategy.sh
```

Expected: `[check-container-strategy] PASS: docker_first artifacts present`.

### Step 4.4: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add .claude/_overlay/project.yaml
git commit -m "chore(codeforge): infra_strategy: docker_first explicit (ADR-033)

Make Docker-first adoption explicit in project.yaml (default
already applies, but explicit avoids ADR-033 drift).

bash scripts/check-container-strategy.sh PASS.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 5: systemd 자산 삭제 + README 전면 교체

**Files:**
- Delete: `c:\workspace\mclayer\mctrader-data\deploy\mctrader-collector.service`
- Delete: `c:\workspace\mclayer\mctrader-data\deploy\README.md`
- Delete: `c:\workspace\mclayer\mctrader-data\deploy\` (디렉토리)
- Modify: `c:\workspace\mclayer\mctrader-data\README.md`

### Step 5.1: deploy/ 자산 삭제

- [ ] **Step**: systemd unit + deploy README 삭제.

```powershell
cd c:\workspace\mclayer\mctrader-data
git rm deploy/mctrader-collector.service deploy/README.md
Remove-Item deploy -Force -Recurse -ErrorAction SilentlyContinue
```

Expected: 두 file `git rm` + 빈 디렉토리 제거.

### Step 5.2: README.md 의 "Linux systemd deployment" 절 식별

- [ ] **Step**: 기존 README의 deployment 절 위치 확인.

```powershell
cd c:\workspace\mclayer\mctrader-data
Get-Content README.md | Select-String -Pattern "^##" | Select-Object -First 10
```

Expected: `## Status`, `## Public API`, `## CLI`, `## Storage layout`, `## Related` 등의 H2 list (현재 README는 deployment 절 부재 — `deploy/README.md`에만 있었음).

### Step 5.3: README.md에 "Docker deployment" 절 추가

- [ ] **Step**: README.md 끝 (또는 `## Related` 직전)에 다음 절 append.

```markdown
## Docker deployment

`v0.9.0` — systemd unit removed. Docker-first deployment (ADR-033 / CFP-128).

### Prerequisites

- Docker Desktop (Windows dev) or Docker Engine 24+ (Linux prod)
- Docker Compose v2 (Compose plugin, included in Docker Desktop / `docker-compose-plugin` apt)
- Outbound HTTPS + WebSocket access to `pubwss.bithumb.com` and `api.bithumb.com`

### Quick start

```bash
git clone https://github.com/mclayer/mctrader-data.git
cd mctrader-data
docker compose up -d collector
docker compose ps           # STATUS = Up X seconds (healthy) after ~60s
docker compose logs -f collector
```

### Cross-platform parity (Windows dev → Linux prod)

- `docker compose build` produces a `linux/amd64` image regardless of host OS
  (Docker Desktop on Windows runs Linux containers in a managed VM)
- For Linux production hosts: clone the repo and run `docker compose build`
  on the prod host. No image push/pull needed in Pilot.

### Configuration

The container reads these env vars (override via compose `environment:`):

| Var | Default | Purpose |
|---|---|---|
| `MCTRADER_DATA_ROOT` | `/var/lib/mctrader/data` | Parquet output root inside container |
| `MCTRADER_HEARTBEAT_STALENESS_SEC` | `90` | Healthcheck staleness threshold (seconds) |

To change collector args, override `command:` in compose.yml or use:

```bash
docker compose run --rm collector collect \
  --symbols KRW-BTC,KRW-ETH,KRW-XRP \
  --include transactions,orderbook \
  --log-level INFO
```

### Backfill (one-shot)

```bash
docker compose run --rm collector backfill \
  --exchange bithumb --symbol KRW-BTC --tf 1h --days 7
```

The same image serves both `collect` (daemon) and `backfill` (one-shot) entrypoints.

### Volume DR (data persistence + backup)

Data lives in named volume `mctrader_data` (mounted at `/var/lib/mctrader/data`).

Backup (host-side, ad-hoc):

```bash
docker run --rm \
  -v mctrader_data:/src \
  -v "$(pwd)":/dst \
  alpine tar czf /dst/mctrader_data-$(date +%Y%m%d).tar.gz -C /src .
```

Cron recommendation: 1×/day, 7-day rolling retention. **ADR-009 invariant**: ticks
and orderbook are forward-only (Bithumb public API has no historical replay) →
collector outage = permanent data gap → off-host backup is mandatory.

### Operations

| Action | Command |
|---|---|
| Status | `docker compose ps` |
| Logs (tail) | `docker compose logs -f collector` |
| Healthcheck | `docker compose exec collector mctrader-data heartbeat-check` |
| Stop (graceful) | `docker compose stop collector` (SIGTERM + 30s drain) |
| Restart | `docker compose restart collector` |
| Disable autostart | `docker compose down` (stops + removes container, volume preserved) |
| Full cleanup (data loss!) | `docker compose down -v` |

### Disaster recovery

- All data forward-only. **No backfill for ticks/orderbook** — Bithumb public API
  does not expose historical tick data. Collector outage = permanent gap for that
  symbol/window.
- For multi-host redundancy, run the collector on 2+ hosts writing to separate
  volumes; reconcile/merge offline. Out of scope for v1.

### Rollback (Pilot only)

If Pilot validation fails:

```bash
git revert <commit-range>  # restores deploy/ + removes Dockerfile / compose.yml
docker compose down -v     # cleanup
```

systemd reinstall is not necessary (production not running on systemd).
```

> **NOTE**: 위 markdown 안의 내부 코드 블록은 ` ```bash ` (3 backtick)으로 표기됐습니다. file에 그대로 paste 시 nested-codeblock 처리 — top-level 4 backtick 으로 wrap 또는 escape 검토.

### Step 5.4: README markdown 검증

- [ ] **Step**: README.md를 markdown viewer로 확인 (VS Code preview or web preview).

```powershell
cd c:\workspace\mclayer\mctrader-data
code --reuse-window README.md
```

Expected: VS Code 열림. `Ctrl+Shift+V` 로 markdown preview, "Docker deployment" 절 정상 렌더링 확인.

### Step 5.5: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add README.md
git commit -m "docs(deploy): replace systemd guide with Docker deployment (BREAKING)

systemd unit removed (deploy/mctrader-collector.service +
deploy/README.md + deploy/ dir). Docker deployment guide added
to repo README: prerequisites / quick start / config / volume DR /
operations / rollback.

ADR-033 / CFP-128 Docker-first migration.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 6: `.github/workflows/image-lint.yml` + actionlint

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\.github\workflows\image-lint.yml`

### Step 6.1: codeforge container-image-scan.yml 위치 파악 (reusable 가능 여부)

- [ ] **Step**: codeforge 가 templates/ 안에 둔 file이 reusable workflow 호출 가능한지 확인.

```powershell
# Check whether codeforge has a reusable copy under .github/workflows/
git -C c:\workspace\mclayer\plugin-codeforge ls-files .github/workflows/ | Select-String -Pattern "container-image-scan"
```

Expected:
- (a) `.github/workflows/container-image-scan.yml` 존재 → reusable 호출 가능 (`uses: mclayer/plugin-codeforge/.github/workflows/container-image-scan.yml@main`)
- (b) `templates/github-workflows/container-image-scan.yml`만 존재 → reusable 호출 불가, consumer가 file 내용을 자기 `.github/workflows/`에 직접 복사

판정 결과로 Step 6.2 분기.

### Step 6.2a: Reusable 호출 가능 시 (case a)

- [ ] **Step**: workflow file을 reusable 호출 형태로 작성.

`c:\workspace\mclayer\mctrader-data\.github\workflows\image-lint.yml`:

```yaml
name: Image Lint (hadolint)

# ADR-033 / CFP-128 — Docker-first 1st-layer image lint (hadolint).
# trivy image scan은 ghcr publish Story 후속 (Pilot 외).

on:
  pull_request:
    paths:
      - 'Dockerfile'
      - '.dockerignore'
      - 'compose.yml'
      - '.github/workflows/image-lint.yml'
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - '.dockerignore'

jobs:
  hadolint:
    name: Dockerfile lint (hadolint)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          recursive: false
          failure-threshold: warning
          format: tty
          no-color: false
```

> **NOTE**: case (a) 의 reusable 호출은 mctrader-data 내부 trivy 가 image-ref 부재로 fail 할 수 있어 hadolint job만 직접 작성. 후속 ghcr publish Story에서 reusable 호출 + trivy 활성.

### Step 6.2b: Reusable 호출 불가 시 (case b — codeforge templates/ 만)

- [ ] **Step**: 동일하게 작성 (위 Step 6.2a 와 같은 yaml). codeforge templates/ 의 trivy job은 image-ref 의무라 publish 후속 Story.

> **결론**: case (a) / (b) 모두 mctrader-data 측 workflow 내용 동일. case (b)에서 codeforge가 향후 .github/workflows/ 로 이동 시 reusable 전환은 별도 follow-up.

### Step 6.3: actionlint 설치 + 실행

- [ ] **Step**: actionlint 검증.

```powershell
# actionlint via docker (no install needed)
cd c:\workspace\mclayer\mctrader-data
docker run --rm -v "${PWD}:/repo" -w /repo rhysd/actionlint:latest -color
```

Expected: 0 issue (또는 warning만, error 0).

Issue 발견 시: hadolint action version 문제 등 → version pin 확인.

### Step 6.4: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add .github/workflows/image-lint.yml
git commit -m "ci(workflows): image-lint.yml — hadolint Dockerfile lint (ADR-033)

PR / main push trigger. hadolint failure-threshold=warning.
trivy image scan deferred to ghcr publish follow-on Story.

actionlint clean.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 7: integration smoke README (manual)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\tests\integration\README.md`

### Step 7.1: tests/integration/ 디렉토리 + README 작성

- [ ] **Step**: manual smoke 절차 박제.

```powershell
cd c:\workspace\mclayer\mctrader-data
New-Item -ItemType Directory -Force -Path tests\integration | Out-Null
```

`c:\workspace\mclayer\mctrader-data\tests\integration\README.md`:

````markdown
# mctrader-data Integration Smoke (manual)

> **Why manual?** Bithumb live WebSocket dependency makes CI fragile.
> Run these smokes before/after major Docker / collector changes.
> Cross-platform: same procedure on Windows dev (Docker Desktop) and Linux prod.

## Prerequisites

- Docker Desktop (Windows) or Docker Engine 24+ (Linux)
- Network access to `pubwss.bithumb.com:443` + `api.bithumb.com:443`
- Free disk space ≥ 1GB for named volume

## Smoke 1: Build + healthy lifecycle

```bash
cd c:\workspace\mclayer\mctrader-data
docker compose build
docker compose up -d collector
sleep 65   # Windows PowerShell: Start-Sleep -Seconds 65
docker compose ps
```

**Pass criteria**: `STATUS` column shows `Up X seconds (healthy)`.

If `(unhealthy)` after start_period (60s) + 1 healthcheck cycle:

```bash
docker compose logs collector --tail=50
docker compose exec collector mctrader-data heartbeat-check
```

Common failures:
- WebSocket reach fail → check outbound network / DNS
- Symbol subscribe fail → check Bithumb API status
- heartbeat file not written → collector loop not yet running, wait another 60s

## Smoke 2: Heartbeat self-check from outside

```bash
docker compose exec collector mctrader-data heartbeat-check
```

**Pass criteria**: exit 0 + stdout `heartbeat fresh: <delta>s ago`.

## Smoke 3: Volume invariant (data preservation across restart)

```bash
docker compose ps  # collector running
# Wait 2-5 min so collector accumulates data
docker compose down                            # stop, keep volume
docker compose up -d collector                 # restart
sleep 65
docker compose exec collector ls /var/lib/mctrader/data/market/
```

**Pass criteria**: `ohlcv/`, `ticks/`, `orderbook/` directories present (data from previous run).

Cleanup if needed: `docker compose down -v` (NOTE: -v deletes the named volume).

## Smoke 4: SIGTERM graceful shutdown (30s drain)

```bash
docker compose up -d collector
sleep 90
time docker compose stop collector             # measure
```

**Pass criteria**: `docker compose stop` returns within 35s (collector flushes
in-flight writes within `TimeoutStopSec=30s`-equivalent default + 5s grace).

If stop hangs > 30s: SIGKILL fallback. Inspect `docker compose logs collector`
for "graceful shutdown complete" message. If absent, in-flight write may be lost
— investigate `collector.py` cleanup path.

## Smoke 5: Backfill (one-shot, optional)

```bash
docker compose run --rm collector backfill \
  --exchange bithumb --symbol KRW-BTC --tf 1h --days 1 --dry-run
```

**Pass criteria**: exit 0 + dry-run output showing planned partition writes.

## State invariants (§8.5 of design spec)

1. **Volume preservation**: Smoke 3 covers — restart preserves `mctrader_data` named volume.
2. **Graceful shutdown**: Smoke 4 covers — SIGTERM → in-flight write flush within 30s.

Run after every Docker-related change (Dockerfile / compose.yml / heartbeat /
collector.py cleanup logic edits).

## Cutover acceptance evidence (Pilot Story §9)

After all smokes pass, capture evidence into the Story file:

```bash
docker compose up -d collector
sleep 65
docker compose ps > /tmp/cutover-evidence.txt
docker compose exec collector mctrader-data heartbeat-check >> /tmp/cutover-evidence.txt
docker compose logs collector --tail=20 >> /tmp/cutover-evidence.txt
docker compose down -v
```

Attach `/tmp/cutover-evidence.txt` content to the Story §9 evidence table.
````

### Step 7.2: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add tests/integration/README.md
git commit -m "test(integration): manual smoke procedure (5 smokes + invariants)

Docker compose build / healthy lifecycle / heartbeat self-check /
volume preservation across restart / SIGTERM graceful shutdown /
backfill dry-run smoke.

§8.5 stateful invariants (volume + graceful shutdown) covered as
manual smoke (Bithumb live WS dependency unfit for CI).

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Task 8: pyproject version bump + CHANGELOG

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\pyproject.toml`
- Create or Modify: `c:\workspace\mclayer\mctrader-data\CHANGELOG.md`

### Step 8.1: pyproject.toml version bump

- [ ] **Step**: `version = "0.8.0"` → `version = "0.9.0"`.

```powershell
cd c:\workspace\mclayer\mctrader-data
(Get-Content pyproject.toml) -replace 'version = "0\.8\.0"', 'version = "0.9.0"' | Set-Content pyproject.toml
Get-Content pyproject.toml | Select-String -Pattern '^version'
```

Expected: `version = "0.9.0"` 출력.

### Step 8.2: CHANGELOG.md 확인 또는 신설

- [ ] **Step**: 기존 CHANGELOG.md 존재 여부 확인.

```powershell
cd c:\workspace\mclayer\mctrader-data
Test-Path CHANGELOG.md
```

If True (Step 8.3a) — entry append.
If False (Step 8.3b) — file 신설.

### Step 8.3a: 기존 CHANGELOG.md에 entry 추가

- [ ] **Step**: 파일 상단 (`# Changelog` 헤더 직후)에 다음 entry 추가.

```markdown
## [0.9.0] — 2026-05-07

### BREAKING
- `deploy/mctrader-collector.service` removed. systemd-based deployment is no longer
  supported. Migrate to Docker (see README §"Docker deployment").
- `deploy/README.md` removed; deployment guide consolidated into the repo README.

### Added
- `Dockerfile` (2-stage, python:3.12-slim, non-root user `mctrader` UID 1001).
- `compose.yml` (collector daemon, named volume `mctrader_data`, healthcheck via
  `heartbeat-check`).
- `.dockerignore` (build context minimization + secret leak prevention).
- `mctrader-data heartbeat-check` CLI subcommand for Docker `HEALTHCHECK` directive.
- `.claude/_overlay/project.yaml`: `infra_strategy: docker_first` (codeforge ADR-033).
- `.github/workflows/image-lint.yml` (hadolint).
- `tests/integration/README.md` (manual smoke procedure, 5 smokes).

### Removed
- `deploy/` directory and its contents.

### Changed
- `README.md` deployment section replaced (systemd → Docker).

References: codeforge ADR-033 (CFP-128), Pilot Story `MCT-N` (mctrader
Containerization Epic, Phase 1).
```

### Step 8.3b: CHANGELOG.md 신설 (Step 8.2가 False였을 시)

- [ ] **Step**: file 신설.

`c:\workspace\mclayer\mctrader-data\CHANGELOG.md`:

```markdown
# Changelog

All notable changes to mctrader-data are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] — 2026-05-07

### BREAKING
- `deploy/mctrader-collector.service` removed. systemd-based deployment is no longer
  supported. Migrate to Docker (see README §"Docker deployment").
- `deploy/README.md` removed; deployment guide consolidated into the repo README.

### Added
- `Dockerfile` (2-stage, python:3.12-slim, non-root user `mctrader` UID 1001).
- `compose.yml` (collector daemon, named volume `mctrader_data`, healthcheck via
  `heartbeat-check`).
- `.dockerignore` (build context minimization + secret leak prevention).
- `mctrader-data heartbeat-check` CLI subcommand for Docker `HEALTHCHECK` directive.
- `.claude/_overlay/project.yaml`: `infra_strategy: docker_first` (codeforge ADR-033).
- `.github/workflows/image-lint.yml` (hadolint).
- `tests/integration/README.md` (manual smoke procedure, 5 smokes).

### Removed
- `deploy/` directory and its contents.

### Changed
- `README.md` deployment section replaced (systemd → Docker).

References: codeforge ADR-033 (CFP-128), Pilot Story `MCT-N` (mctrader
Containerization Epic, Phase 1).
```

### Step 8.4: Final regression — full pytest

- [ ] **Step**: 모든 변경 통합 후 회귀 검증.

```powershell
cd c:\workspace\mclayer\mctrader-data
uv run pytest -v 2>&1 | Select-String -Pattern "passed|failed" | Select-Object -Last 5
```

Expected: 기존 + 신규 4 모두 PASS, 0 fail.

### Step 8.5: Commit

- [ ] **Step**: commit.

```powershell
cd c:\workspace\mclayer\mctrader-data
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): bump 0.8.0 → 0.9.0 (BREAKING: systemd → Docker)

Semver minor — Public Python API (scan_candles, OhlcvSchema,
BackfillRunner) backward-compatible. Only deploy/ assets break.

CHANGELOG entry follows Keep a Changelog format.

Pilot Story (mctrader Containerization Epic Phase 1)."
```

---

## Post-Plan: PR open + Phase 1/2 review chain (plan 외 — Story 단계)

본 plan 8 task 완료 후 mctrader-data branch `feat/mctrader-data-docker-pilot`에 8 commit이 누적됩니다. 그 다음:

1. `git push -u origin feat/mctrader-data-docker-pilot`
2. mctrader-hub의 Epic Story `MCT-M` + Pilot Story `MCT-N` GitHub issue 발급 (codeforge story-init workflow 또는 manual)
3. mctrader-data PR open with title `[MCT-N] feat: Docker-first containerization (Pilot)`
4. Phase 1 review (DesignReviewPL — spec 검증, ClaudeReview + CodexReview parallel)
5. Phase 2 review (CodeReviewPL + TestAgent + SecurityTestPL hadolint)
6. admin merge (CI green 또는 Sonnet decider 결정)
7. Story §9 evidence + §11 회고 (Epic Phase 2+ rollout sequencing 결정)

**CHANGELOG 의 `MCT-N` placeholder는 PR open 시 실 issue 번호로 치환** — pre-PR last commit으로 fix-up.

---

## Self-Review

### Spec coverage check

| Spec AC | Plan task | Status |
|---|---|---|
| AC #1 Dockerfile (2-stage, non-root, hadolint) | Task 2 | ✅ |
| AC #2 compose.yml (1 service, named vol, restart, healthcheck, bridge) | Task 3 | ✅ |
| AC #3 .dockerignore | Task 2 | ✅ |
| AC #4 heartbeat-check CLI + 4 TDD | Task 1 | ✅ |
| AC #5 project.yaml infra_strategy | Task 4 | ✅ |
| AC #6 check-container-strategy.sh PASS | Task 4.3 | ✅ |
| AC #7 image-lint.yml | Task 6 | ✅ |
| AC #8 deploy/ 자산 삭제 | Task 5.1 | ✅ |
| AC #9 README "Docker deployment" 절 | Task 5.3 | ✅ |
| AC #10 pyproject 0.9.0 + CHANGELOG | Task 8 | ✅ |
| AC #11 tests/integration/README.md | Task 7 | ✅ |
| AC #12 Cutover 7 step evidence | Task 7.1 §"Cutover acceptance evidence" + manual exec | ✅ |
| AC #13 기존 182 pytest 회귀 PASS | Task 1.7, Task 8.4 | ✅ |

### Placeholder scan

- `MCT-N`, `MCT-M` placeholder는 spec / commit message에 explicit (issue 발급 후 치환). 전부 명시적 placeholder, 가이드 "TBD" 류 미사용. ✅
- "Add appropriate error handling" / "implement later" — 0건. ✅
- "Similar to Task N" — 0건 (각 task 자체 완결). ✅
- 코드 step 모두 complete code block 보유. ✅

### Type / signature consistency

- `check_staleness(data_root: Path, threshold_sec: int = DEFAULT_STALENESS_SEC) -> tuple[bool, str]` — Task 1.4 정의 → Task 1.5 cli.py 의 호출 시그니처 일치 ✅
- `heartbeat_path(data_root: Path) -> Path` — Task 1.4 정의 → check_staleness 내부 사용 ✅
- `MCTRADER_DATA_ROOT` env var — Task 1.5 cli.py + Dockerfile (Task 2.1) + compose.yml (Task 3.1) 모두 동일 ✅
- `MCTRADER_HEARTBEAT_STALENESS_SEC` env var — Task 1.4 resolve_threshold_sec + compose.yml comment + README config table 일치 ✅
- HEALTHCHECK args (`["CMD", "mctrader-data", "heartbeat-check"]`) — Dockerfile (Task 2.1) + compose.yml (Task 3.1) 동일 ✅

### 보충 fix (self-review 결과)

- 없음 — 일관성 OK.

---

## Amendment 1 (2026-05-07) — HEALTHCHECK API endpoint

**Trigger**: Task 1 진입 시 기존 `heartbeat.py` 구조가 plan 가정과 다른 것 발견 (`<root>/.heartbeat` 단일 파일이 아니라 `<root>/market/manifest/heartbeat-<node_id>.json` HA active-active 패턴, MCT-91/93). 사용자 결정: heartbeat-check CLI 폐기 + HTTP `/health` API endpoint로 대체. webapp-minimal 패턴과 일관 + 5 sister rollout reference 강함.

### 변경 요약

- **신규 module**: `src/mctrader_data/health_server.py` (stdlib `http.server` + daemon thread `HealthServer`)
- **CLI subcommand `heartbeat-check`**: 폐기 (cli.py에 추가하지 않음)
- **HEALTHCHECK CMD**: `["CMD", "mctrader-data", "heartbeat-check"]` → `["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]`
- **port**: 8080 default, env `MCTRADER_HEALTH_PORT` override. compose `ports:` 절 부재 (host expose 안 함, internal only).
- **State source**: `HeartbeatWriter._ws_state` (collector.py에 이미 wired된 인스턴스 활용). 부재 → 503.
- **Library**: stdlib `http.server` + daemon threading (zero new dep, asyncio loop와 격리, `daemon=True`로 main loop 종료 시 자동 cleanup)

### Task 1 재정의 (HealthServer module + TDD)

**Files (변경)**:
- Create: `src/mctrader_data/health_server.py`
- Create: `tests/test_health_server.py`
- Modify: `src/mctrader_data/cli.py` (`collect` subcommand에서 HealthServer 생성 + MultiSymbolCollector wiring)
- Modify: `src/mctrader_data/collector.py` (`MultiSymbolCollector.__init__`에 `health_server: HealthServer | None = None` 인자 + run() lifecycle)

**Step 1.A: test_health_server.py 4 시나리오 작성** (TDD RED)

```python
"""TDD for HealthServer HTTP /health endpoint (Pilot, Amendment 1)."""
from __future__ import annotations

import json
import threading
import time
import urllib.request
from typing import Any

import pytest

from mctrader_data.health_server import HealthServer
from mctrader_data.heartbeat import HeartbeatWriter


def _free_port() -> int:
    """Allocate an ephemeral port for test isolation."""
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get_health(port: int) -> tuple[int, dict[str, Any]]:
    """GET /health, return (status_code, body_json). 503 returns body too."""
    req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_health_503_when_heartbeat_writer_missing(tmp_path):
    port = _free_port()
    server = HealthServer(heartbeat_writer=None, port=port)
    server.start()
    try:
        time.sleep(0.2)  # give server a moment to bind
        code, body = _get_health(port)
        assert code == 503
        assert body["status"] == "unhealthy"
        assert "heartbeat unavailable" in body["reason"]
    finally:
        server.stop()


def test_health_200_when_ws_connected(tmp_path):
    writer = HeartbeatWriter(root=tmp_path, node_id="test-node")
    writer.ws_state = "connected"
    port = _free_port()
    server = HealthServer(heartbeat_writer=writer, port=port)
    server.start()
    try:
        time.sleep(0.2)
        code, body = _get_health(port)
        assert code == 200
        assert body["status"] == "ok"
        assert body["ws_state"] == "connected"
        assert body["node_id"] == "test-node"
    finally:
        server.stop()


def test_health_503_when_ws_disconnected(tmp_path):
    writer = HeartbeatWriter(root=tmp_path, node_id="test-node")
    writer.ws_state = "disconnected"
    port = _free_port()
    server = HealthServer(heartbeat_writer=writer, port=port)
    server.start()
    try:
        time.sleep(0.2)
        code, body = _get_health(port)
        assert code == 503
        assert body["status"] == "unhealthy"
        assert "ws_state=disconnected" in body["reason"]
    finally:
        server.stop()


def test_health_port_env_override(tmp_path, monkeypatch):
    """Resolve port from MCTRADER_HEALTH_PORT env when caller passes None."""
    from mctrader_data.health_server import resolve_port

    monkeypatch.setenv("MCTRADER_HEALTH_PORT", "9090")
    assert resolve_port() == 9090
    monkeypatch.delenv("MCTRADER_HEALTH_PORT")
    assert resolve_port() == 8080
```

**Step 1.B: health_server.py 구현** (GREEN)

```python
"""HTTP /health endpoint for Docker HEALTHCHECK (Pilot, Amendment 1).

Lightweight stdlib http.server in a daemon thread — zero dep, asyncio-loop-free.
Reads HeartbeatWriter._ws_state for liveness signal:
  - heartbeat_writer is None → 503 unhealthy ("heartbeat unavailable")
  - ws_state in {connected, reconnecting} → 200 ok
  - ws_state == disconnected → 503 unhealthy
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


DEFAULT_PORT = 8080
HEALTHY_WS_STATES = frozenset({"connected", "reconnecting"})


def resolve_port() -> int:
    """Read MCTRADER_HEALTH_PORT env, default 8080."""
    raw = os.environ.get("MCTRADER_HEALTH_PORT")
    if not raw:
        return DEFAULT_PORT
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_PORT


def _build_response(heartbeat_writer: Any) -> tuple[int, dict[str, Any]]:
    """Return (http_status, body) given the heartbeat writer state."""
    if heartbeat_writer is None:
        return 503, {"status": "unhealthy", "reason": "heartbeat unavailable"}
    ws_state = getattr(heartbeat_writer, "ws_state", "unknown")
    node_id = getattr(heartbeat_writer, "node_id", "unknown")
    started_at = getattr(heartbeat_writer, "started_at", None)
    uptime = (
        int((datetime.now(timezone.utc) - started_at).total_seconds())
        if started_at is not None else 0
    )
    body: dict[str, Any] = {
        "ws_state": ws_state,
        "node_id": node_id,
        "uptime_seconds": uptime,
    }
    if ws_state in HEALTHY_WS_STATES:
        body["status"] = "ok"
        return 200, body
    body["status"] = "unhealthy"
    body["reason"] = f"ws_state={ws_state}"
    return 503, body


class _HealthHandler(BaseHTTPRequestHandler):
    # set by HealthServer at start()
    heartbeat_writer: Any = None

    def do_GET(self) -> None:  # noqa: N802 (stdlib API)
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        status, body = _build_response(self.heartbeat_writer)
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default stderr access logs during normal operation.
        return


class HealthServer:
    """Daemon-thread HTTP server exposing GET /health.

    Lifecycle:
      server = HealthServer(heartbeat_writer=writer)  # bind in start()
      server.start()                                  # spawn daemon thread
      ...
      server.stop()                                   # graceful shutdown
    """

    def __init__(self, heartbeat_writer: Any | None, port: int | None = None):
        self._heartbeat_writer = heartbeat_writer
        self._port = port if port is not None else resolve_port()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._port

    def start(self) -> None:
        # Bind a fresh handler subclass so the writer is captured per server.
        writer = self._heartbeat_writer

        class _BoundHandler(_HealthHandler):
            heartbeat_writer = writer

        self._httpd = ThreadingHTTPServer(("0.0.0.0", self._port), _BoundHandler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="mctrader-health-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._httpd = None
        self._thread = None
```

**Step 1.C: cli.py wiring** — `collect` subcommand가 HealthServer를 생성해 `MultiSymbolCollector` 에 주입.

(상세 코드 = Task 진행 시 cli.py의 `collect` subcommand 위치 확인 후 결정. wiring은 HeartbeatWriter 패턴 그대로 — `MultiSymbolCollector(... health_server=HealthServer(heartbeat_writer=writer))`.)

**Step 1.D: collector.py wiring** — `MultiSymbolCollector.__init__`에 인자 추가 + run() 에서 `start()/stop()` 처리.

(상세 코드 = run()에서 heartbeat_task와 동일 패턴으로 lifecycle 관리. `try ... finally:` 안에 stop() 호출.)

**Step 1.E ~ 1.H**: 기존 plan의 Step 1.6 (run test pass) ~ Step 1.8 (commit) 그대로. commit message는 `feat: HealthServer HTTP /health endpoint for Docker HEALTHCHECK` 등.

### Task 2 (Dockerfile) HEALTHCHECK CMD 변경

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
```

### Task 2.5 entrypoint smoke 변경

```powershell
docker run --rm mctrader-data:pilot --help
# heartbeat-check 호출 안 함 (CLI 폐기)
# Health endpoint smoke = compose up 후 검증 (Task 3.4)
```

### Task 3 (compose.yml) healthcheck 변경

```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

`MCTRADER_HEARTBEAT_STALENESS_SEC` env 주석은 삭제. `MCTRADER_HEALTH_PORT` env (default 8080) 주석으로 대체. **`ports:` 절 부재 유지** — internal only.

### Task 5 README 변경

Operations table의 Healthcheck row:

```markdown
| Healthcheck | `docker compose ps` (STATUS column) or `docker compose exec collector python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"` |
```

config table은 `MCTRADER_HEARTBEAT_STALENESS_SEC` → `MCTRADER_HEALTH_PORT` (default 8080) 으로 교체.

### Task 7 integration smoke README — Smoke 2 변경

Smoke 2 = `docker compose exec collector python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"` exit 0 + 200 응답.

### Task 8 CHANGELOG 변경

`Added` 의 `mctrader-data heartbeat-check` line 삭제. 새 line 추가: `HealthServer HTTP /health endpoint (port 8080, internal only) for Docker HEALTHCHECK`.

### Type / signature consistency (re-checked)

- `HealthServer(heartbeat_writer, port=None) -> HealthServer` — Step 1.B 정의 → Step 1.C cli.py wiring 일치
- `resolve_port() -> int` — Step 1.B 정의 → port env 검사
- `MCTRADER_HEALTH_PORT` env var — health_server.py + compose.yml + README config table 일치
- HEALTHCHECK args — Dockerfile (Task 2) + compose.yml (Task 3) 둘 다 `python -c "..."` 동일
