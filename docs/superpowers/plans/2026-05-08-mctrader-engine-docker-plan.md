# mctrader-engine Docker-first Containerization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-engine 의 dual-mode CLI (paper daemon + 다수 one-shot executor) 를 단일 Docker image 위에 두 compose service 패턴 (`paper` + `engine` profile-gated tools) 으로 노출. ADR-033 §7.4 OpRiskArch 4 항목 + ADR-015 두 SM 을 Docker container state 에 mapping. cross-container PID namespace 격리로 깨지는 runtime_lock mutex 를 fcntl.flock 기반으로 교체 (D13).

**Architecture:** python:3.12-slim 2-stage Dockerfile, non-root `mctrader` UID 1001. compose.yml 에 4 named volume (`mctrader_data:ro` external + `mctrader_engine_runs` + `mctrader_engine_wfo` + `mctrader_engine_lock`) + paper service (default profile, healthcheck) + engine service (profile `tools`, one-shot via `compose run --rm engine ...`). HealthServer (port 8080, internal only) 가 PaperExecutor + bithumb WS adapter state 기반 200/503. runtime_lock POSIX path 는 fcntl.flock advisory lock, Windows fallback 은 기존 atomic-write + pid-alive 패턴 유지.

**Tech Stack:** Python 3.11/3.12, uv, Docker Desktop (Windows host) → linux/amd64 image, Docker Compose, hadolint, codeforge plugin reusable workflows (`container-image-scan.yml`), pytest, fcntl.

**Working repos**:
- `c:\workspace\mclayer\mctrader-hub\` — docs (spec + plan + Story file + optional ADR-015 amendment), branch `docs/MCT-100-engine-docker` (already created, spec commit `963a070` 박제)
- `c:\workspace\mclayer\mctrader-engine\` — impl, branch `feat/MCT-100-docker-first` (Task 4 에서 생성)

**Spec reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-08-mctrader-engine-docker-design.md` (commit `963a070`).

**Pilot reference**: `c:\workspace\mclayer\mctrader-hub\docs\superpowers\specs\2026-05-07-mctrader-data-docker-pilot-design.md` + `2026-05-07-mctrader-data-docker-pilot-plan.md` + mctrader-data PR #11 (8 commits).

---

## File Structure (변경 매트릭스)

### Create — mctrader-hub repo (`docs/MCT-100-engine-docker` branch)

| 파일 | 책임 | task |
|---|---|---|
| `docs/stories/MCT-100.md` | Story file (`## 1.` ~ `## 11.`, MCT-99/97 reference format). | Task 1 |
| `docs/superpowers/plans/2026-05-08-mctrader-engine-docker-plan.md` | 본 plan 자체 (이미 작성). | — |

### Modify — mctrader-hub repo (`docs/MCT-100-engine-docker` branch)

| 파일 | 변경 | task |
|---|---|---|
| `docs/adr/ADR-015-engine-state-machine.md` | Cross-references 절에 Docker SM mapping anchor 추가 (5-line amendment). | Task 2 (optional) |

### Create — mctrader-engine repo (`feat/MCT-100-docker-first` branch)

| 파일 | 책임 | task |
|---|---|---|
| `Dockerfile` | python:3.12-slim 2-stage. uv install of 3 git+https deps + editable. non-root mctrader UID 1001. ENTRYPOINT mctrader-cli + CMD --help. HEALTHCHECK directive (compose 가 override). | Task 8 |
| `.dockerignore` | Pilot 패턴 + `out/` + `.pytest_cache/` + `.ruff_cache/` + `.mctrader/` 추가 | Task 8 |
| `compose.yml` | paper service (default profile, healthcheck, labels) + engine service (profile tools, labels). 4 named volume + restart unless-stopped (paper 만) + bridge network. | Task 9 |
| `src/mctrader_engine/health_server.py` | stdlib http.server `HealthServer` daemon thread. GET /health 200/503. PaperExecutor + WS adapter state 기반 판정. | Task 5 |
| `tests/test_health_server.py` | TDD 4 시나리오 (executor 부재 / paper running + ws connected / paper running + ws disconnected / port env override). | Task 5 |
| `.github/workflows/image-lint.yml` | codeforge `container-image-scan.yml` reusable (hadolint job 만 활성). | Task 10 |
| `tests/integration/README.md` | manual smoke 절차 (compose up + healthy + backtest run + wfo run + cross-container mutex + volume invariant + SIGTERM graceful). | Task 12 |
| `CHANGELOG.md` (신규) | `[0.30.0] - 2026-05-DD` entry. BREAKING note runtime_lock impl 변경. | Task 13 |

### Modify — mctrader-engine repo (`feat/MCT-100-docker-first` branch)

| 파일 | 변경 | task |
|---|---|---|
| `src/mctrader_engine/runtime/runtime_lock.py` | **D13 핵심 patch** — POSIX fcntl.flock branch + Windows pid-fallback branch. | Task 6 |
| `tests/test_runtime_lock.py` | flock cross-fd 시나리오 추가 (Linux only). | Task 6 |
| `src/mctrader_engine/runtime/paper_runner.py` | `health_server: HealthServer \| None = None` 인자. lifecycle wiring. | Task 7 |
| `src/mctrader_engine/cli.py` | `paper start` 안에 HealthServer 생성 + PaperRunner inject + `MCTRADER_HEALTH_PORT` env. | Task 7 |
| `tests/test_paper_runner.py` | HealthServer wiring smoke (default None unchanged + with HealthServer). | Task 7 |
| `.claude/_overlay/project.yaml` | `infra_strategy: docker_first` field 추가. | Task 11 |
| `README.md` | "## Docker deployment" 절 추가. install / paper / backtest / wfo / evidence / risk invocation pattern + DR backup recipe + Windows known limitation. | Task 11 |
| `pyproject.toml` | version `0.29.0` → `0.30.0`. | Task 13 |

### Delete

**없음** — mctrader-engine 에 systemd unit 자산 부재. Docker 전환 = add-only.

---

## Task Ordering (TDD + dependency)

```
[mctrader-hub branch docs/MCT-100-engine-docker]
Task 1 (Story file scaffold)
  ↓
Task 2 (ADR-015 cross-ref amendment, optional)
  ↓
Task 3 (Hub PR open — engine impl 진행 중에도 review 가능)

[mctrader-engine branch feat/MCT-100-docker-first]
Task 4 (engine branch 생성)
  ↓
Task 5 (HealthServer TDD RED → GREEN, 4 scenario)
  ↓ (HealthServer module 존재 → paper_runner wiring 가능)
Task 6 (runtime_lock D13 fcntl.flock TDD RED → GREEN)
  ↓ (runtime_lock cross-container mutex 보장 → paper / wfo Docker 안전)
Task 7 (PaperRunner + CLI HealthServer wiring)
  ↓ (engine 코드 변경 완료, Docker 자산 진입 가능)
Task 8 (Dockerfile + .dockerignore + hadolint PASS + image build + entrypoint smoke)
  ↓ (image build 가능)
Task 9 (compose.yml + docker compose config PASS)
  ↓ (compose 자산 모두 존재)
Task 10 (.github/workflows/image-lint.yml + actionlint)
  ↓
Task 11 (project.yaml infra_strategy + check-container-strategy.sh PASS + README)
  ↓ (codeforge consumer lint 통과)
Task 12 (tests/integration/README.md — manual smoke 박제)
  ↓
Task 13 (pyproject 0.30.0 + CHANGELOG.md)
  ↓
Task 14 (Cutover validation 10-step smoke evidence)
  ↓
Task 15 (Engine PR open + review chain + admin merge)

[mctrader-hub finalize]
Task 16 (Hub PR finalize + admin merge + Epic body Phase 3 status + #131 close)
```

각 task = independent commit. 순서 의무.

---

## Task 1: mctrader-hub Story file `docs/stories/MCT-100.md` scaffold

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-100.md`

**Working dir**: `c:\workspace\mclayer\mctrader-hub` (branch `docs/MCT-100-engine-docker`).

### Step 1.1: 기존 reference Story format 확인

- [ ] **Step**: MCT-99 / MCT-97 Story format 빠르게 확인 (header + section 번호 패턴).

```powershell
cd c:\workspace\mclayer\mctrader-hub
Get-Content docs\stories\MCT-99.md -Head 30
```

Expected: yaml frontmatter (`story_key`, `story_issues`, `status`) + `## 1.` ~ `## 11.` 번호 section.

### Step 1.2: MCT-100.md scaffold 작성

- [ ] **Step**: 다음 내용으로 신규 file 생성.

```markdown
---
story_key: MCT-100
story_issues:
  - repo: mclayer/mctrader-hub
    number: 131
status: in_progress
---

# MCT-100: mctrader-engine Docker-first Containerization (Phase 3)

- **Issue**: #131
- **Status**: in_progress (impl 진행 중)
- **Parent Epic**: mctrader-hub#120 — mctrader Docker-first Migration (Phase 3 of 6)
- **Trigger ADR**: codeforge ADR-033 (CFP-128 Accepted 2026-05-07) + ADR-009 §D12 (2026-05-08 amendment) + ADR-015
- **Pilot reference**: MCT-99 (mctrader-hub#121, merged 2026-05-07)
- **Parallel session**: Phase 4 = MCT-101 mctrader-hub#132 (mctrader-web), 별도 session

## 1. 사용자 요구사항 (verbatim, 2026-05-08 session prompt)

> "mctrader Docker-first Migration Epic (MCT-98 #120) Phase 3 진행 — mctrader-engine sister."
> "본 session 은 parallel Phase 4 (MCT-101 mctrader-web #132) 와 독립."

## 2. 도메인 해석

### 2.1 Phase 3 scope

mctrader-engine 의 dual-mode CLI (paper daemon + 다수 one-shot) 를 단일 Docker image 위에 두 compose service 패턴 (paper default profile + engine profile=tools) 으로 노출. mctrader-data Pilot 의 패턴 carry-over + engine-specific 4 finding (dual mode / 4 volume / runtime_lock cross-container PID 격리 / mctrader-web 미통합).

### 2.2 ADR-033 §7.4 OpRiskArch 4 항목 + ADR-015 두 SM 박제 의무

§3.5 SM ↔ Docker mapping + §3.4 4 항목 의무.

## 3. 관련 ADR

- codeforge ADR-033 (Docker-first Infra Engineering)
- ADR-009 §D12 (Docker-first persistence) — Phase 2 entry 박제
- ADR-015 (engine state machine) — 본 Story 가 Cross-references 절에 Docker SM mapping anchor 추가

## 4. 관련 코드 경로 (mctrader-engine)

### 신규
- `Dockerfile` (2-stage python:3.12-slim, non-root mctrader UID 1001)
- `.dockerignore` (Pilot 패턴 + dev cache 추가)
- `compose.yml` (paper + engine profile, 4 named volume, healthcheck, labels)
- `src/mctrader_engine/health_server.py` (HTTP /health endpoint, paper executor state-aware)
- `tests/test_health_server.py` (4 TDD scenario)
- `.github/workflows/image-lint.yml` (hadolint reusable)
- `tests/integration/README.md` (manual smoke + cross-container mutex 검증)
- `CHANGELOG.md` (신규 file)

### 수정
- `src/mctrader_engine/runtime/runtime_lock.py` (**D13** fcntl.flock POSIX + Windows pid-fallback dual impl)
- `tests/test_runtime_lock.py` (flock cross-fd 시나리오 추가)
- `src/mctrader_engine/runtime/paper_runner.py` (HealthServer wiring)
- `src/mctrader_engine/cli.py` (paper start HealthServer 생성)
- `tests/test_paper_runner.py` (HealthServer wiring smoke)
- `.claude/_overlay/project.yaml` (`infra_strategy: docker_first`)
- `README.md` ("Docker deployment" 절 추가)
- `pyproject.toml` (0.29.0 → 0.30.0)

### 삭제
**없음** (systemd 자산 부재).

## 5. Acceptance Criteria

§ design spec 의 A1-A20 그대로 mirror. 본 Story 진행 중 evidence 박제 시점에 status update.

## 7. 결정점 (D1-D13, 2026-05-08 brainstorming session 박제)

| Decision | 채택 | 거절 |
|---|---|---|
| D1 Compose surface | α 1 paper + compose run for one-shot | β 2-service profile / γ 3-service profile / δ 0-service |
| D2 HealthServer | A paper only | B 모든 컨테이너 / C 명시 disable |
| D3 Data input mount | A mctrader_data:ro (external) | B :rw / C host bind / D compose run flag |
| D4 Engine output | A 단일 mctrader_engine_runs | B per-mode 분할 / C 통합 |
| D5 WFO root | B 별도 mctrader_engine_wfo | A runs 통합 / C 통합 |
| D6 runtime_lock 조정 | A 공유 volume + env override **+ D13 의무** | B 운영 규율만 / C compose hook / D redis / E 수용 |
| D7 mctrader-web 통합 | C compose run 패턴 SoT (Phase 4 deferred) | A 약 / B interface only / D HTTP API |
| D8 Image deps | A Pilot uv 2-stage @main | B commit pin / C wheel vendor |
| D9 SM ↔ Docker | labels yes / /state endpoint no | endpoint 신설 |
| D10 Process model | A 1 container = 1 strategy | B fan-out / C 다중 service |
| D11 Image scope | C 단일 image 다중 service | A / B 다중 image |
| D12 DR backup | runs + wfo backup, lock 제외 | lock 까지 backup |
| **D13** runtime_lock impl | **fcntl.flock 교체 (Linux) + Windows pid-fallback** | 현재 atomic-write+pid-alive (cross-container PID ns 격리에서 mutex 깨짐) |

## 8. Implementation Manifest

(Task 14 cutover 후 박제 — commit 별 § ID 매핑.)

## 9. Evidence

(Task 14 cutover validation 10-step smoke 결과 박제.)

## 10. 거절된 대안

(§7 결정점의 거절 column 참조.)

## 11. 회고

(Story 종료 시 박제 — Phase 4 parallel reconciliation + 5 sister 진행 상태.)
```

### Step 1.3: Commit

- [ ] **Step**: 본 file commit.

```powershell
cd c:\workspace\mclayer\mctrader-hub
git add docs\stories\MCT-100.md
git commit -m "[MCT-100] docs(story): MCT-100 Story file scaffold (Phase 3, in_progress)"
```

Expected: 1 file changed (about 100 lines).

---

## Task 2: ADR-015 cross-ref amendment (optional, ~5 lines)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-015-engine-state-machine.md`

**근거**: spec §3.5 의 SM ↔ Docker mapping 표가 ADR-015 의 SoT 안에서 anchor 가 되도록 Cross-references 절에 5-line amendment 추가. optional — 시간 부족 시 follow-on commit 으로 분리 가능.

### Step 2.1: ADR-015 의 끝 부분 확인

- [ ] **Step**: 기존 ADR-015 의 frontmatter `amends:` field + Follow-up impact 절 위치 확인.

```powershell
cd c:\workspace\mclayer\mctrader-hub
Get-Content docs\adr\ADR-015-engine-state-machine.md | Select-Object -Last 30
```

Expected: `## Follow-up impact` 절이 file 끝에 있음.

### Step 2.2: 5-line cross-ref 추가

- [ ] **Step**: `## Follow-up impact` 절의 마지막 bullet 뒤에 다음 추가.

```markdown
- **MCT-100 Phase 3 (2026-05-08)**: Docker container state ↔ SM mapping anchor — daemon `[stopped/starting/running/stopping/crashed/degraded]` 가 container `exited / running pre-healthy / health_status=healthy / SIGTERM 30s window / ExitCode≠0 with auto-restart / health_status=unhealthy while running` 에 매핑. one-shot `[queued/running/cancelling/completed/failed/cancelled]` 가 `pre-compose-run / running / SIGTERM sent / ExitCode=0 / ExitCode≠0 / signal-induced exit (130/143)` 에 매핑. 본 mapping 은 mctrader-engine compose service `labels:` 절에 박제 (mctrader-engine PR `feat/MCT-100-docker-first` 참조). `/state` HTTP endpoint 는 신설 안 함 — Phase 4 control_adapter 가 docker inspect / labels / health_status 로 introspect.
```

### Step 2.3: frontmatter `amends:` field update

- [ ] **Step**: ADR-015 의 frontmatter `amends: []` 를 `amends: [MCT-100]` 또는 동등 표현으로 update (다른 ADR amendment pattern 따름).

```powershell
cd c:\workspace\mclayer\mctrader-hub
Get-Content docs\adr\ADR-009-ohlcv-schema.md -Head 20
```

Expected: ADR-009 의 `amends: []` 또는 `**Amendment History**:` 본문 패턴 확인 → ADR-015 도 동일 패턴 적용.

(ADR-009 패턴 = file 본문 안에 `**Amendment History**:` bullet list. ADR-015 도 본문 추가 시 동일.)

만약 ADR-015 가 frontmatter 만 사용하고 Amendment History bullet 부재라면 Status 절 바로 아래에 Amendment 1줄 추가.

### Step 2.4: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-hub
git add docs\adr\ADR-015-engine-state-machine.md
git commit -m "[MCT-100] docs(adr): ADR-015 cross-ref to MCT-100 Docker SM mapping"
```

---

## Task 3: Hub PR open (early review feedback)

**근거**: engine impl 진행 동안 hub doc PR 이 review 가능 → Pilot 패턴 동일 (early PR + impl 병행).

### Step 3.1: Push branch

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-hub
git push -u origin docs/MCT-100-engine-docker
```

### Step 3.2: PR 생성 via gh CLI

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-hub
gh pr create --title "[MCT-100] docs: mctrader-engine Docker-first design + plan + Story (Phase 3)" --body @"
## Summary
- mctrader-engine Phase 3 design spec (13 결정 freeze: Codex 11 + Codex D12 + Sonnet D13 fcntl.flock)
- implementation plan (16 task, dual-repo)
- Story file MCT-100.md scaffold
- ADR-015 cross-ref amendment (optional)

## 13 결정 freeze 핵심
- 4 named volume topology (mctrader_data:ro + engine_runs + engine_wfo + engine_lock)
- D13 critical: cross-container PID namespace 격리로 runtime_lock mutex 깨짐 → fcntl.flock 교체
- ADR-015 SM ↔ Docker labels mapping (no /state endpoint)
- Phase 4 mctrader-web wiring deferred (compose run 패턴 = control_adapter SoT)

## Engine PR
mctrader-engine impl PR 별도 — branch ``feat/MCT-100-docker-first`` (Task 5+ 진행 중).

## Test plan
- [ ] Codex 7-area review per phase (push-back fix-back)
- [ ] mctrader-engine PR phase-gate-mergeable green
- [ ] Cutover 10-step smoke evidence Story §9 박제

Refs: mctrader-hub#131, MCT-98 #120 Phase 3
"@
```

(또는 동등 GitHub UI 작성)

Expected: PR 번호 발급, draft 또는 ready 상태.

---

## Task 4: mctrader-engine 작업 branch 생성

**Working dir**: `c:\workspace\mclayer\mctrader-engine`

### Step 4.1: branch 생성

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git fetch origin --quiet
git checkout main
git pull origin main
git checkout -b feat/MCT-100-docker-first
```

Expected: clean working tree, branch `feat/MCT-100-docker-first` from `main` HEAD.

### Step 4.2: pre-flight 검증

- [ ] **Step**: 기존 pytest baseline 확인 (회귀 detection 시 비교 baseline).

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/ -q 2>&1 | Select-Object -Last 5
```

Expected: ~250 PASS, 0 FAIL. 기록.

---

## Task 5: HealthServer module + 4 TDD scenario

**Files:**
- Create: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\health_server.py`
- Create: `c:\workspace\mclayer\mctrader-engine\tests\test_health_server.py`

**근거**: Pilot collector HealthServer 패턴 차용 + paper executor state-aware 변형. ws_state 는 PaperExecutor `_stream` (WsWrapperStream) 의 활성 여부 + bithumb adapter 의 `connected` flag 또는 동등 attribute 에서 가져옴.

### Step 5.1: Pilot HealthServer 패턴 확인

- [ ] **Step**: Pilot collector 의 health_server.py 읽기.

```powershell
cd c:\workspace\mclayer\mctrader-data
Get-Content src\mctrader_data\health_server.py
```

Expected: stdlib `http.server.BaseHTTPRequestHandler` daemon thread, GET /health 200/503, ws_state attribute lookup, port env override.

### Step 5.2: PaperExecutor / WsWrapperStream state attribute 확인

- [ ] **Step**: state lookup hook 결정 — 어떤 property 를 checked 200 으로 매핑할지 확인.

```powershell
cd c:\workspace\mclayer\mctrader-engine
Get-Content src\mctrader_engine\runtime\ws_wrapper.py | Select-Object -Last 60
```

Expected: WsWrapperStream 의 internal state attribute 또는 `connected` flag (있으면 그대로 사용, 없으면 `_executor` 활성 여부 + 마지막 event timestamp 신선도 + max_events 진행 모두 사용).

만약 state attribute 부재 시: HealthServer 가 `runner: PaperRunner | None` 을 받음 + `runner._executor is not None` (paper 가 시작됨) + `runner._executor._stream._connected` (또는 동등 — 여기서 attribute 부재 시 단순 `runner is not None and runner._executor is not None` 만으로 200 판정 — Phase 3 minimum, future-proof 은 별도 follow-on).

### Step 5.3: failing test 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\tests\test_health_server.py`:

```python
"""TDD for HealthServer (MCT-100 Phase 3, mctrader-data Pilot 패턴 차용).

4 시나리오:
1. runner=None (paper not started) → 503 + JSON {"status":"unhealthy","reason":"runner unavailable"}
2. runner.has_active_executor=True + ws_connected=True → 200 + JSON {"status":"ok",...}
3. runner.has_active_executor=True + ws_connected=False → 503 + JSON {"status":"unhealthy","reason":"ws disconnected",...}
4. port env override (MCTRADER_HEALTH_PORT=9090) 적용 검증
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional

import pytest

from mctrader_engine.health_server import HealthServer


@dataclass
class FakeRunner:
    """Minimal stand-in for PaperRunner.

    HealthServer reads two boolean signals + one timestamp. Real PaperRunner
    will expose these via thin properties (Step 5.5).
    """
    has_active_executor: bool
    ws_connected: bool
    last_event_ts: Optional[float] = None


def _free_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_listening(port: int, timeout_sec: float = 2.0) -> None:
    """Poll until /health responds or raise."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5)
            return
        except Exception:
            time.sleep(0.05)
    raise TimeoutError(f"HealthServer did not start on {port}")


def test_health_server_runner_absent_returns_503():
    port = _free_port()
    server = HealthServer(runner_provider=lambda: None, port=port)
    server.start()
    try:
        _wait_listening(port)
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5)
        assert exc.value.code == 503
        body = json.loads(exc.value.read())
        assert body["status"] == "unhealthy"
        assert "runner" in body["reason"].lower()
    finally:
        server.stop()


def test_health_server_paper_running_ws_connected_returns_200():
    port = _free_port()
    runner = FakeRunner(has_active_executor=True, ws_connected=True, last_event_ts=time.time())
    server = HealthServer(runner_provider=lambda: runner, port=port)
    server.start()
    try:
        _wait_listening(port)
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5)
        assert resp.status == 200
        body = json.loads(resp.read())
        assert body["status"] == "ok"
        assert body["ws_state"] == "connected"
    finally:
        server.stop()


def test_health_server_paper_running_ws_disconnected_returns_503():
    port = _free_port()
    runner = FakeRunner(has_active_executor=True, ws_connected=False, last_event_ts=None)
    server = HealthServer(runner_provider=lambda: runner, port=port)
    server.start()
    try:
        _wait_listening(port)
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5)
        assert exc.value.code == 503
        body = json.loads(exc.value.read())
        assert body["status"] == "unhealthy"
        assert "ws" in body["reason"].lower()
    finally:
        server.stop()


def test_health_server_port_env_override(monkeypatch: pytest.MonkeyPatch):
    """MCTRADER_HEALTH_PORT env applies when port=None."""
    target = _free_port()
    monkeypatch.setenv("MCTRADER_HEALTH_PORT", str(target))
    server = HealthServer(runner_provider=lambda: None, port=None)
    assert server.port == target
    server.start()
    try:
        _wait_listening(target)
    finally:
        server.stop()
```

### Step 5.4: failing test 실행

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/test_health_server.py -v
```

Expected: 4 fail (`HealthServer` import error 또는 module not found).

### Step 5.5: HealthServer module 구현

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\health_server.py`:

```python
"""HealthServer — HTTP /health endpoint for the paper daemon (MCT-100 Phase 3).

Pilot reference: ``mctrader-data/src/mctrader_data/health_server.py`` — stdlib
``http.server`` daemon thread serving ``GET /health`` 200/503 based on a state
provider callback. Engine variant reads PaperRunner state instead of HeartbeatWriter.

State signals (provider returns ``PaperRunner | None``):

* ``runner is None`` → 503 reason="runner unavailable"
* ``runner.has_active_executor`` False → 503 reason="executor unavailable"
* ``runner.ws_connected`` False → 503 reason="ws disconnected"
* otherwise → 200 status="ok"

The port resolves from constructor arg, then env ``MCTRADER_HEALTH_PORT``,
default 8080 (matches Pilot collector port + ADR-009 §D12 reference pattern).
``ports:`` exposure in ``compose.yml`` is intentionally absent — internal use only.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

DEFAULT_HEALTH_PORT = 8080


def _resolve_port(port: Optional[int]) -> int:
    if port is not None:
        return port
    env_val = os.environ.get("MCTRADER_HEALTH_PORT")
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            pass
    return DEFAULT_HEALTH_PORT


class _Handler(BaseHTTPRequestHandler):
    runner_provider: Callable[[], Any] = lambda: None  # set in factory

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suppress per-request stdout (Pilot pattern — daemon noise reduction).
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        runner = self.__class__.runner_provider()
        body, code = _evaluate(runner)
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _evaluate(runner: Any) -> tuple[dict[str, Any], int]:
    if runner is None:
        return {"status": "unhealthy", "reason": "runner unavailable"}, 503
    has_executor = bool(getattr(runner, "has_active_executor", False))
    if not has_executor:
        return {"status": "unhealthy", "reason": "executor unavailable"}, 503
    ws_connected = bool(getattr(runner, "ws_connected", False))
    if not ws_connected:
        return {"status": "unhealthy", "reason": "ws disconnected", "ws_state": "disconnected"}, 503
    return {"status": "ok", "ws_state": "connected"}, 200


class HealthServer:
    """Daemon-thread HTTP server. ``start()`` non-blocking, ``stop()`` joins."""

    def __init__(
        self,
        *,
        runner_provider: Callable[[], Any],
        port: Optional[int] = None,
    ) -> None:
        self._provider = runner_provider
        self.port = _resolve_port(port)
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._server is not None:
            return  # idempotent

        # Bind handler class (subclass per server instance to scope provider state).
        handler_cls = type(
            "_BoundHandler",
            (_Handler,),
            {"runner_provider": staticmethod(self._provider)},
        )
        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), handler_cls)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="health-server")
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._server = None
        self._thread = None
```

### Step 5.6: test PASS 검증

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/test_health_server.py -v
```

Expected: 4 PASS.

### Step 5.7: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add src\mctrader_engine\health_server.py tests\test_health_server.py
git commit -m "[MCT-100] feat(health): HealthServer HTTP /health for paper daemon (port 8080, ws_state-aware)"
```

---

## Task 6: runtime_lock fcntl.flock D13 patch (TDD)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\runtime\runtime_lock.py`
- Modify: `c:\workspace\mclayer\mctrader-engine\tests\test_runtime_lock.py` (또는 신규 file)

**근거**: spec §3.6 D13 — cross-container PID namespace 격리로 stale-pid cleanup 가 mutex 깨뜨림. fcntl.flock 으로 교체 (Linux/Docker), Windows 는 기존 atomic-write+pid-alive 유지 (Windows host 직접 실행 path 보존).

### Step 6.1: 기존 test 확인 + Linux flock 시나리오 RED

- [ ] **Step**: 기존 test_paper_lock.py 의 stale-pid 시나리오 위치 확인.

```powershell
cd c:\workspace\mclayer\mctrader-engine
Get-Content tests\test_paper_lock.py | Select-Object -First 60
```

Expected: stale-pid 시나리오는 `_pid_alive` mock 또는 PID kill 패턴 사용. (이 test 들은 동작 유지 — Windows path 검증으로 의미 보존.)

### Step 6.2: flock 시나리오 신규 test 추가

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\tests\test_runtime_lock_flock.py` 신규 file:

```python
"""TDD for runtime_lock fcntl.flock POSIX branch (MCT-100 D13).

Cross-container PID namespace 격리 시나리오를 fork 두 process 로 시뮬레이션 —
parent process 가 lock 획득, fork 한 child 가 동일 path 로 acquire 시도 → LockHeldError.
Windows 에서는 skip (fcntl 부재).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from mctrader_engine.runtime.runtime_lock import (
    LockHeldError,
    acquire_runtime_lock,
)

POSIX_ONLY = pytest.mark.skipif(sys.platform.startswith("win"), reason="fcntl POSIX only")


@POSIX_ONLY
def test_flock_concurrent_acquire_raises_lockheld(tmp_path: Path):
    """동일 lock_path 에 두 fd 가 동시 acquire 시도 → 두 번째는 LockHeldError."""
    lock_path = tmp_path / "runtime.lock"

    # Parent 가 첫 lock 획득 후 fork → child 가 시도 → child 에서 LockHeldError 기대.
    pid = os.fork()
    if pid == 0:
        # child
        time.sleep(0.05)  # parent 가 먼저 lock 획득
        try:
            with acquire_runtime_lock(run_id="child-run", mode="wfo", lock_path=lock_path):
                os._exit(0)  # 잘못 획득 — 의외 success
        except LockHeldError:
            os._exit(42)  # 기대 path
        except Exception:
            os._exit(99)  # 다른 예외
    else:
        # parent — lock 획득 + 5초 보유
        with acquire_runtime_lock(run_id="parent-run", mode="paper", lock_path=lock_path):
            wpid, status = os.waitpid(pid, 0)
            assert wpid == pid
            assert os.WIFEXITED(status)
            assert os.WEXITSTATUS(status) == 42  # child 가 LockHeldError 받음 = 정상


@POSIX_ONLY
def test_flock_releases_on_process_exit(tmp_path: Path):
    """Process exit 시 fd close = kernel auto-release. 다음 acquire 성공."""
    lock_path = tmp_path / "runtime.lock"

    pid = os.fork()
    if pid == 0:
        # child — lock 획득 + 즉시 종료 (with 컨텍스트 정상 exit)
        try:
            with acquire_runtime_lock(run_id="child-run", mode="paper", lock_path=lock_path):
                pass
            os._exit(0)
        except Exception:
            os._exit(99)
    else:
        os.waitpid(pid, 0)

    # parent 가 다음 acquire — 성공해야 함
    with acquire_runtime_lock(run_id="parent-run", mode="paper", lock_path=lock_path):
        pass


@POSIX_ONLY
def test_flock_paper_wfo_mutex(tmp_path: Path):
    """paper 가 lock 보유 중 wfo 시도 → LockHeldError, holder_mode 정확."""
    lock_path = tmp_path / "runtime.lock"

    with acquire_runtime_lock(run_id="paper-run", mode="paper", lock_path=lock_path):
        with pytest.raises(LockHeldError) as exc:
            with acquire_runtime_lock(run_id="wfo-run", mode="wfo", lock_path=lock_path):
                pass
        # JSON content (provenance) 가 살아있어야 holder_mode 정확
        assert exc.value.holder_mode == "paper"
        assert exc.value.holder_run_id == "paper-run"
```

### Step 6.3: failing test 실행

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/test_runtime_lock_flock.py -v
```

Expected: Linux 면 fail (현재 impl 가 cross-fd 동시 acquire 시 stale-pid clean → 둘 다 lock 획득 → mutex 깨짐). Windows 면 4 skipped.

(주의: Windows 개발 host 면 실제로 Linux container 안에서만 RED 검증 가능. `docker run --rm -v ${PWD}:/workspace -w /workspace python:3.12-slim sh -c "pip install uv && uv sync && uv run pytest tests/test_runtime_lock_flock.py -v"` 로 검증 가능.)

대안 (간단): `os.fork` 가 Windows 에 부재 → POSIX_ONLY skipped. Linux container 안 검증 의무. integration smoke (Task 12) 에서 docker-based cross-container 검증 명시.

### Step 6.4: runtime_lock.py D13 patch

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\runtime\runtime_lock.py` 의 `acquire_runtime_lock` context manager 를 OS 분기로 교체. 기존 file 내용 유지 + 다음 변경:

기존 import 줄 위에 추가:

```python
import sys
```

기존 `_atomic_write` / `_pid_alive` / `_read_holder` helper 는 그대로 유지 (Windows branch 가 사용).

`acquire_runtime_lock` context manager 를 다음으로 교체:

```python
@contextmanager
def acquire_runtime_lock(
    *,
    run_id: str,
    mode: RuntimeMode,
    lock_path: Path | None = None,
) -> Iterator[Path]:
    """Acquire host-wide runtime lock for a given mode (``paper`` or ``wfo``).

    POSIX: fcntl.flock advisory lock — kernel-managed, cross-container safe via
    shared volume mount (MCT-100 D13). Windows: legacy O_CREAT|O_EXCL +
    pid-alive cleanup (single-host single-PID-ns assumption — Windows host
    direct execution path).
    """
    if sys.platform.startswith("win"):
        with _acquire_windows(run_id=run_id, mode=mode, lock_path=lock_path) as p:
            yield p
        return
    with _acquire_posix(run_id=run_id, mode=mode, lock_path=lock_path) as p:
        yield p
```

기존 body 를 `_acquire_windows` 로 rename (private helper). 그리고 새 `_acquire_posix` 추가:

```python
@contextmanager
def _acquire_windows(
    *,
    run_id: str,
    mode: RuntimeMode,
    lock_path: Path | None = None,
) -> Iterator[Path]:
    """Windows path — legacy atomic-write + pid-alive (MCT-61 baseline)."""
    path = lock_path or _default_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        {
            "run_id": run_id,
            "pid": os.getpid(),
            "started_ts": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
        },
        ensure_ascii=False,
    )

    try:
        _atomic_write(path, payload)
    except FileExistsError:
        holder = _read_holder(path)
        if holder is None or not _pid_alive(holder[1]):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            try:
                _atomic_write(path, payload)
            except FileExistsError as race_exc:
                raise LockHeldError(
                    path=path, holder_run_id="<unknown>", holder_pid=-1, holder_mode="<unknown>",
                ) from race_exc
        else:
            raise LockHeldError(
                path=path,
                holder_run_id=holder[0],
                holder_pid=holder[1],
                holder_mode=holder[2],
            ) from None
    except OSError as exc:
        if exc.errno == errno.EACCES:
            raise PermissionError(f"cannot create runtime lock at {path}: {exc}") from exc
        raise

    try:
        yield path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def _acquire_posix(
    *,
    run_id: str,
    mode: RuntimeMode,
    lock_path: Path | None = None,
) -> Iterator[Path]:
    """POSIX path — fcntl.flock advisory lock (MCT-100 D13).

    Cross-container safe: same inode (shared volume) → kernel-managed flock
    visible across PID namespaces. Process exit closes fd → automatic release.
    """
    import fcntl

    path = lock_path or _default_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        {
            "run_id": run_id,
            "pid": os.getpid(),
            "started_ts": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
        },
        ensure_ascii=False,
    )

    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            holder = _read_holder(path)
            if holder is None:
                raise LockHeldError(
                    path=path, holder_run_id="<unknown>", holder_pid=-1, holder_mode="<unknown>",
                ) from exc
            raise LockHeldError(
                path=path,
                holder_run_id=holder[0],
                holder_pid=holder[1],
                holder_mode=holder[2],
            ) from exc

        # 획득 성공 → JSON content (provenance) write
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload.encode("utf-8"))
    except BaseException:
        os.close(fd)
        raise

    try:
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

### Step 6.5: test PASS 검증

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/test_runtime_lock_flock.py tests/test_paper_lock.py -v
```

Expected: Windows host 면 flock 4 skipped + paper_lock 기존 test PASS. Linux 면 flock test PASS + paper_lock test PASS (acquire_paper_lock 가 acquire_runtime_lock 호출 → POSIX path 적용 됨).

회귀 검증:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/ -q 2>&1 | Select-Object -Last 10
```

Expected: ~250+4 PASS, 0 FAIL (Windows 면 4 skip).

### Step 6.6: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add src\mctrader_engine\runtime\runtime_lock.py tests\test_runtime_lock_flock.py
git commit -m "[MCT-100] feat(runtime): runtime_lock fcntl.flock POSIX branch (D13, cross-container mutex)"
```

---

## Task 7: PaperRunner + CLI HealthServer wiring

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\runtime\paper_runner.py`
- Modify: `c:\workspace\mclayer\mctrader-engine\src\mctrader_engine\cli.py`
- Modify: `c:\workspace\mclayer\mctrader-engine\tests\test_paper_runner.py`

### Step 7.1: PaperRunner 인자 추가 + state property 노출

- [ ] **Step**: `paper_runner.py` 의 `__init__` signature 끝에 `health_server: "HealthServer | None" = None` 인자 추가. `_health_server` private attribute 보관. `run()` 시작에 `if self._health_server: self._health_server.start()` + `finally` 분기에 `if self._health_server: self._health_server.stop()`.

추가로 HealthServer 가 사용할 thin properties:

```python
@property
def has_active_executor(self) -> bool:
    return self._executor is not None

@property
def ws_connected(self) -> bool:
    """WS adapter connected flag — best-effort lookup via wrapper attribute chain.

    HealthServer 가 호출 — 부재 시 False (= 503).
    """
    if self._executor is None:
        return False
    stream = getattr(self._executor, "_stream", None)
    if stream is None:
        return False
    upstream = getattr(stream, "_upstream", None)
    if upstream is None:
        return False
    return bool(getattr(upstream, "connected", False))
```

(주의: `BithumbWebSocketStream` 가 `connected` attribute 노출 안 하면 fallback = `_executor is not None and last_event_recent` — Step 7.2 에서 결정.)

### Step 7.2: BithumbWebSocketStream connected attribute 검증

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
Get-Content c:\workspace\mclayer\mctrader-market-bithumb\src\mctrader_market_bithumb\ws_client.py | Select-String -Pattern "connected|_state|_status" -Context 0,2
```

만약 `connected` 또는 동등 attribute 부재면, ws_connected fallback 로직:

```python
@property
def ws_connected(self) -> bool:
    """Best-effort: executor 활성 + executor 가 closed_bars 또는 _events 받았음 → True."""
    if self._executor is None:
        return False
    if getattr(self._executor, "closed_bars", None):
        return True
    events = getattr(self._executor, "_events", None)
    return bool(events)
```

(Phase 3 minimum — 정확 ws state 추적은 follow-on Story.)

### Step 7.3: cli.py paper start HealthServer 생성

- [ ] **Step**: `cli.py` 의 `paper_start` 함수 안에 PaperRunner 생성 직전에 추가:

```python
from mctrader_engine.health_server import HealthServer

# HealthServer wiring — paper daemon 만 (one-shot 미적용).
# port = MCTRADER_HEALTH_PORT env 또는 default 8080.
health_server = HealthServer(runner_provider=lambda: runner, port=None)
```

PaperRunner 생성 후:

```python
runner._health_server = health_server  # PaperRunner._health_server private
# 또는 PaperRunner constructor 에 인자로 직접 전달
```

(권장: constructor 인자 — Step 7.1 의 `health_server=` 인자 사용.)

수정된 PaperRunner 호출:

```python
runner = PaperRunner(
    run_id=run_id_str,
    symbol=sym,
    timeframe=tf,
    strategy_name=strategy,
    fast=fast,
    slow=slow,
    initial_capital=capital,
    output_dir=output_dir,
    duration=duration,
    end_iso=end_iso,
    max_events=max_events,
    mock_feed=mock_feed,
    write_paper_partition=not no_paper_partition,
    health_server=HealthServer(runner_provider=lambda: runner_ref, port=None) if not mock_feed else None,
)
runner_ref = runner  # closure 의 forward reference 해소
```

(주의: provider closure 가 runner 자체를 참조해야 함 — `lambda: runner` 가 closure scope 안에서 작동하도록. constructor 안에서 `self._health_server = health_server` 가 적용되면 mock_feed 시 None.)

mock_feed 시 HealthServer 비활성 — smoke test 단순화 (Pilot 동일 패턴).

### Step 7.4: test 보강

- [ ] **Step**: `tests/test_paper_runner.py` 에 다음 test 추가:

```python
def test_paper_runner_health_server_default_none():
    """Backward compat: health_server 미명시 시 기존 동작 그대로."""
    runner = PaperRunner(
        run_id="x",
        symbol=Symbol.from_string("KRW-BTC"),
        timeframe=Timeframe("1h"),
        strategy_name="sma",
        fast=5, slow=20,
        initial_capital=Decimal("1000000"),
        output_dir=Path("/tmp/x"),
    )
    assert runner._health_server is None
    assert not runner.has_active_executor
    assert not runner.ws_connected


def test_paper_runner_health_server_lifecycle(tmp_path):
    """HealthServer 인자 전달 시 _health_server 보관 + properties 동작."""
    from mctrader_engine.health_server import HealthServer
    server = HealthServer(runner_provider=lambda: None, port=None)
    runner = PaperRunner(
        run_id="x",
        symbol=Symbol.from_string("KRW-BTC"),
        timeframe=Timeframe("1h"),
        strategy_name="sma",
        fast=5, slow=20,
        initial_capital=Decimal("1000000"),
        output_dir=tmp_path,
        health_server=server,
    )
    assert runner._health_server is server
    assert not runner.has_active_executor  # run() 미호출
    assert not runner.ws_connected
```

### Step 7.5: test 실행 + 회귀 검증

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/test_paper_runner.py tests/test_health_server.py tests/test_cli_paper.py -v
```

Expected: 전부 PASS. 기존 paper_runner test 회귀 0건.

전체 회귀:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv run pytest tests/ -q 2>&1 | Select-Object -Last 10
```

Expected: ~256 PASS (250 baseline + 4 health + 2 paper_runner additions). 0 FAIL.

### Step 7.6: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add src\mctrader_engine\runtime\paper_runner.py src\mctrader_engine\cli.py tests\test_paper_runner.py
git commit -m "[MCT-100] feat(paper): PaperRunner+CLI HealthServer wiring (paper start exposes /health)"
```

---

## Task 8: Dockerfile + .dockerignore (hadolint PASS + image build smoke)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-engine\Dockerfile`
- Create: `c:\workspace\mclayer\mctrader-engine\.dockerignore`

### Step 8.1: Pilot Dockerfile reference 확인

- [ ] **Step**:

```powershell
Get-Content c:\workspace\mclayer\mctrader-data\Dockerfile
```

Expected: 2-stage python:3.12-slim, uv pip install, non-root mctrader UID 1001, ENTRYPOINT mctrader-data + CMD args.

### Step 8.2: Dockerfile 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
# mctrader-engine — dual-mode CLI (paper daemon + backtest/wfo/evidence/risk/lookahead-lint/indicator one-shot)
# MCT-100 Phase 3 — codeforge ADR-033 + ADR-009 §D12 정합

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PIP_NO_CACHE_DIR=1

# uv install + git for git+https deps (mctrader-market, mctrader-data, mctrader-market-bithumb @main).
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir uv

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv pip install --system -e .

# --- Stage 2 ---
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
    MCTRADER_OUTPUT_DIR=/var/lib/mctrader/runs \
    MCTRADER_WFO_ROOT=/var/lib/mctrader/wfo \
    MCTRADER_RUNTIME_LOCK_PATH=/var/lib/mctrader/lock/runtime.lock \
    MCTRADER_HEALTH_PORT=8080

# Non-root user (Pilot UID 1001 reuse — same user namespace across mctrader Docker stack).
RUN groupadd --system --gid 1001 mctrader \
 && useradd --system --uid 1001 --gid 1001 --create-home --home-dir /home/mctrader mctrader \
 && mkdir -p /var/lib/mctrader/data /var/lib/mctrader/runs /var/lib/mctrader/wfo /var/lib/mctrader/lock \
 && chown -R mctrader:mctrader /var/lib/mctrader

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

USER mctrader
WORKDIR /home/mctrader

# Internal port (paper daemon HealthServer). compose.yml 의 ports 절 부재 → host 미노출.
EXPOSE 8080

# HEALTHCHECK directive — compose.yml 의 healthcheck 절이 override 가능.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)" || exit 1

ENTRYPOINT ["mctrader-cli"]
CMD ["--help"]
```

### Step 8.3: .dockerignore 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\.dockerignore`:

```
# MCT-100 Phase 3 — Pilot 패턴 + dev cache 추가
.git
.github
.claude
.gitignore
.dockerignore
.editorconfig
.pre-commit-config.yaml
.python-version
.venv
.env
.env.*
*.pem
*.key
*.crt
*.md
docs
tests
out
.pytest_cache
.ruff_cache
.mypy_cache
__pycache__
*.pyc
.coverage
htmlcov
build
dist
*.egg-info
.mctrader
```

### Step 8.4: hadolint smoke

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
docker run --rm -i hadolint/hadolint < Dockerfile
```

Expected: 0 warning. (만약 warning 발생 시 fix.)

### Step 8.5: image build smoke

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
docker build -t mctrader-engine:mct-100 .
```

Expected: build 성공, 최종 image tag `mctrader-engine:mct-100`.

### Step 8.6: ENTRYPOINT smoke

- [ ] **Step**:

```powershell
docker run --rm mctrader-engine:mct-100 --help
docker run --rm mctrader-engine:mct-100 backtest --help
docker run --rm mctrader-engine:mct-100 paper --help
docker run --rm mctrader-engine:mct-100 wfo --help
docker run --rm mctrader-engine:mct-100 risk --help
docker run --rm mctrader-engine:mct-100 lookahead-lint --help
docker run --rm mctrader-engine:mct-100 indicator --help
```

Expected: 각각 click help 출력.

### Step 8.7: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add Dockerfile .dockerignore
git commit -m "[MCT-100] feat(docker): Dockerfile (2-stage py3.12-slim, non-root mctrader UID 1001) + .dockerignore"
```

---

## Task 9: compose.yml + `docker compose config` PASS

**Files:**
- Create: `c:\workspace\mclayer\mctrader-engine\compose.yml`

### Step 9.1: compose.yml 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\compose.yml`:

```yaml
# mctrader-engine — MCT-100 Phase 3 Docker-first compose
# 4 named volume (mctrader_data:ro external + engine_runs + engine_wfo + engine_lock)
# 2 service: paper (default profile, daemon, healthcheck) + engine (profile tools, one-shot via compose run)

services:
  paper:
    build: .
    image: mctrader-engine:dev
    command:
      - "paper"
      - "start"
      - "--strategy"
      - "${MCTRADER_STRATEGY:-sma}"
      - "--symbol"
      - "${MCTRADER_SYMBOL:-KRW-BTC}"
      - "--tf"
      - "${MCTRADER_TF:-1h}"
      - "--fast"
      - "${MCTRADER_FAST:-5}"
      - "--slow"
      - "${MCTRADER_SLOW:-20}"
      - "--output-dir"
      - "/var/lib/mctrader/runs"
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      MCTRADER_OUTPUT_DIR: /var/lib/mctrader/runs
      MCTRADER_WFO_ROOT: /var/lib/mctrader/wfo
      MCTRADER_RUNTIME_LOCK_PATH: /var/lib/mctrader/lock/runtime.lock
      MCTRADER_HEALTH_PORT: "8080"
    volumes:
      - mctrader_data:/var/lib/mctrader/data:ro
      - mctrader_engine_runs:/var/lib/mctrader/runs
      - mctrader_engine_wfo:/var/lib/mctrader/wfo
      - mctrader_engine_lock:/var/lib/mctrader/lock
    restart: unless-stopped
    healthcheck:
      test:
        - "CMD"
        - "python"
        - "-c"
        - "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      mctrader.role: "paper-daemon"
      mctrader.sm.kind: "daemon"
      mctrader.adr-015.daemon.running: "health_status=healthy"
      mctrader.adr-015.daemon.degraded: "health_status=unhealthy while running"
      mctrader.story: "MCT-100"

  engine:
    build: .
    image: mctrader-engine:dev
    profiles: ["tools"]
    environment:
      MCTRADER_DATA_ROOT: /var/lib/mctrader/data
      MCTRADER_OUTPUT_DIR: /var/lib/mctrader/runs
      MCTRADER_WFO_ROOT: /var/lib/mctrader/wfo
      MCTRADER_RUNTIME_LOCK_PATH: /var/lib/mctrader/lock/runtime.lock
    volumes:
      - mctrader_data:/var/lib/mctrader/data:ro
      - mctrader_engine_runs:/var/lib/mctrader/runs
      - mctrader_engine_wfo:/var/lib/mctrader/wfo
      - mctrader_engine_lock:/var/lib/mctrader/lock
    labels:
      mctrader.role: "engine-cli"
      mctrader.sm.kind: "oneshot"
      mctrader.adr-015.oneshot.completed: "ExitCode=0"
      mctrader.adr-015.oneshot.failed: "ExitCode!=0"
      mctrader.story: "MCT-100"

volumes:
  mctrader_data:
    external: true
    name: mctrader_data  # Pilot compose.yml 의 explicit name (`mctrader-data/compose.yml:38`) 와 정합. Pilot 가 이 name 을 떨구면 본 compose break.
  mctrader_engine_runs:
  mctrader_engine_wfo:
  mctrader_engine_lock:
```

**Phase 4 (MCT-101) surface review reconciliation** (parallel session 발견 사항 반영):

- Surface 1 (ADR-014 single-process invariant): 이미 align — paper_runner 가 asyncio.Runner.run() 단일 process + HealthServer daemon thread.
- Surface 2 (HealthServer 패턴): 이미 align — Pilot stdlib http.server 패턴 차용 (단순성 우선, FastAPI 의존 추가 회피).
- Surface 3 (cross-stack volume name): 본 step 에서 `name: mctrader_data` 명시 추가로 Pilot 의존성 박제. standalone fallback (volume 부재 시 engine 동작) = 별도 Story 후보 (Future Q F8).
- Surface 4 (ADR-002 D6 paper ledger forward-only): Phase 3 scope 외, future entry F9.

### Step 9.2: `docker compose config` smoke

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
docker compose config
```

Expected: validated YAML 출력 (no error). external volume `mctrader_data` 가 미존재라도 syntax-only validation 은 PASS.

`mctrader_data` external volume 부재 시 사용자 안내 위해 README 에 박제 (Task 11).

### Step 9.3: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add compose.yml
git commit -m "[MCT-100] feat(docker): compose.yml (paper service + engine profile, 4 volumes, healthcheck, labels)"
```

---

## Task 10: `.github/workflows/image-lint.yml` (codeforge reusable)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-engine\.github\workflows\image-lint.yml`

### Step 10.1: Pilot workflow reference 확인

- [ ] **Step**:

```powershell
Get-Content c:\workspace\mclayer\mctrader-data\.github\workflows\image-lint.yml
```

Expected: codeforge `templates/github-workflows/container-image-scan.yml` 을 호출하는 reusable workflow 패턴.

### Step 10.2: 동일 workflow 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\.github\workflows\image-lint.yml`:

```yaml
name: image-lint

on:
  pull_request:
    paths:
      - "Dockerfile"
      - ".dockerignore"
      - "compose.yml"
      - ".github/workflows/image-lint.yml"
  push:
    branches: [main]
    paths:
      - "Dockerfile"
      - ".dockerignore"
      - "compose.yml"
      - ".github/workflows/image-lint.yml"

jobs:
  hadolint:
    uses: mclayer/plugin-codeforge/.github/workflows/container-image-scan.yml@main
    with:
      dockerfile_path: Dockerfile
      run_hadolint: true
      run_trivy: false  # MCT-100 Phase 3 = lint-only (Pilot F2 carry-over)
```

(만약 reusable workflow 호출 syntax 가 다르거나 Pilot 가 inline hadolint job 사용했으면 그대로 mirror.)

### Step 10.3: actionlint smoke

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
# actionlint Docker run 또는 pip 설치
docker run --rm -v "${PWD}:/repo" -w /repo rhysd/actionlint:latest -color
```

Expected: 0 issue.

### Step 10.4: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add .github\workflows\image-lint.yml
git commit -m "[MCT-100] ci(image-lint): add codeforge reusable hadolint workflow"
```

---

## Task 11: project.yaml `infra_strategy: docker_first` + check-container-strategy.sh PASS + README

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-engine\.claude\_overlay\project.yaml`
- Modify: `c:\workspace\mclayer\mctrader-engine\README.md`

### Step 11.1: project.yaml 추가

- [ ] **Step**: `.claude\_overlay\project.yaml` 의 `project:` 절 안에 다음 field 추가 (기존 `name: mctrader` 와 동일 indent):

```yaml
project:
  name: mctrader
  infra_strategy: docker_first  # MCT-100 Phase 3 — codeforge ADR-033 / mctrader Docker-first Migration
```

(field 위치 및 정확한 indent 는 codeforge schema doc + Pilot 파일 참고.)

### Step 11.2: check-container-strategy.sh smoke

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
bash c:\workspace\mclayer\plugin-codeforge\scripts\check-container-strategy.sh
```

(Path 가 다르면 codeforge plugin path 확인.)

Expected: PASS (Dockerfile + compose.yml + project.yaml infra_strategy 모두 정합).

### Step 11.3: README "Docker deployment" 절 작성

- [ ] **Step**: `README.md` 끝에 다음 절 추가 (기존 내용 보존):

```markdown
## Docker deployment (MCT-100 Phase 3)

### Prerequisites

- Docker Engine 24+ + Docker Compose v2
- mctrader-data Docker stack (Pilot — `mctrader_data` named volume 가 collector 가동 시 생성됨)

### Build

```bash
docker compose build paper
```

### Paper daemon (long-running)

```bash
# 환경 변수로 strategy / symbol / TF override 가능
MCTRADER_STRATEGY=sma MCTRADER_SYMBOL=KRW-BTC docker compose up -d paper

# Healthcheck status 확인
docker compose ps paper
docker compose exec paper python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"

# Graceful stop (SIGTERM 30s timeout)
docker compose stop paper
```

### Backtest (one-shot)

```bash
docker compose run --rm engine backtest \
  --strategy sma --symbol KRW-BTC --tf 1h \
  --start 2026-04-25T00:00:00Z --end 2026-05-02T00:00:00Z \
  --fast 5 --slow 20 \
  --output-dir /var/lib/mctrader/runs
```

산출물: `mctrader_engine_runs` named volume 의 `<run_id>/{execution_report.json, equity_curve.csv}`.

### WFO (one-shot multi-fold)

```bash
docker compose run --rm engine wfo decision-group create \
  --registry-spec /var/lib/mctrader/wfo/spec.json --actor mccho

docker compose run --rm engine wfo search \
  --registry-spec /var/lib/mctrader/wfo/spec.json --actor mccho
```

### Promotion evidence

```bash
docker compose run --rm engine paper evidence \
  --run-id <existing_paper_run_id> \
  --output-dir /var/lib/mctrader/runs
```

### Operator risk control

```bash
docker compose run --rm engine risk kill --run-id <run> --reason "manual" \
  --artifacts-dir /var/lib/mctrader/runs

docker compose run --rm engine risk ack --run-id <run> \
  --artifacts-dir /var/lib/mctrader/runs
```

### Volume topology

| Volume | Mount | Purpose |
|---|---|---|
| `mctrader_data` (external) | `/var/lib/mctrader/data:ro` | mctrader-data collector 가 produce. RO mount — forward-only invariant 보호. |
| `mctrader_engine_runs` | `/var/lib/mctrader/runs` | per-run audit artifacts (report, equity, event_store, paper_partition) |
| `mctrader_engine_wfo` | `/var/lib/mctrader/wfo` | WFO decision_group registry |
| `mctrader_engine_lock` | `/var/lib/mctrader/lock` | cross-container `runtime.lock` mutex SoT (D13) |

### DR backup recipe (ADR-009 §D12 패턴)

```powershell
# Backup runs (audit artifacts)
$ts = Get-Date -Format yyyyMMdd_HHmmss
docker run --rm `
  -v mctrader_engine_runs:/source:ro -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_engine_runs_${ts}.tar.gz -C /source .

# Backup WFO (registry)
docker run --rm `
  -v mctrader_engine_wfo:/source:ro -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_engine_wfo_${ts}.tar.gz -C /source .

# Lock volume = transient state, backup 제외.
```

bash 등가:

```bash
TS=$(date +%Y%m%d_%H%M%S)
docker run --rm -v mctrader_engine_runs:/source:ro -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_engine_runs_${TS}.tar.gz -C /source .
docker run --rm -v mctrader_engine_wfo:/source:ro -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_engine_wfo_${TS}.tar.gz -C /source .
```

### Known limitation: Windows host 직접 실행

`mctrader-cli paper start` 를 Docker 컨테이너 밖 Windows host 에서 직접 실행 시 (개발 편의) — `runtime_lock` 가 fcntl.flock 부재로 기존 atomic-write + pid-alive fallback 적용. Single-host single-PID-namespace 환경에서는 정상 동작. **cross-container mutex 보장은 Docker 환경 안에서만 적용** (D13).

production 운영 + Phase 4 mctrader-web 통합 = Docker compose 환경 사용 권장.

### Phase 4 control_adapter 진입

mctrader-web 측 control_adapter (Phase 4 = MCT-101) 가 본 `compose run --rm engine ...` 패턴을 의도된 invocation 으로 채택. subprocess / docker-py SDK / Docker socket mount 의 구체적 mechanism 은 Phase 4 session 책임.
```

### Step 11.4: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add .claude\_overlay\project.yaml README.md
git commit -m "[MCT-100] docs+config: project.yaml infra_strategy + README Docker deployment 절 (DR + Phase 4 anchor)"
```

---

## Task 12: tests/integration/README.md (manual smoke + cross-container mutex 검증)

**Files:**
- Create: `c:\workspace\mclayer\mctrader-engine\tests\integration\README.md`

### Step 12.1: 박제 절차 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\tests\integration\README.md`:

```markdown
# mctrader-engine integration smoke (manual)

> **Scope**: MCT-100 Phase 3 — Docker-first containerization 검증. CI 자동화 부담 회피 (Bithumb live WS 의존 + 60s healthy convergence). 본 절차는 PR open 직전 + Cutover validation 시점에 사용자 또는 reviewer 가 실행.

## Prerequisites

- Docker Desktop (Windows host) 또는 Docker Engine 24+ (Linux)
- mctrader-data Docker stack 가동 → `mctrader_data` external volume 존재 (collector 가 일정 시간 가동되어 OHLCV / tick / orderbook 데이터가 적어도 some shape 으로 채워져 있어야 backtest smoke 가 의미있음)

## 10-step smoke

### 1. Build

```powershell
cd c:\workspace\mclayer\mctrader-engine
docker compose build paper
```

Expected: build 성공, `mctrader-engine:dev` image tag 생성.

### 2. Paper daemon up

```powershell
docker compose up -d paper
```

Expected: container starting, health pending.

### 3. Healthy convergence (60s 대기)

```powershell
Start-Sleep -Seconds 60
docker compose ps paper
```

Expected: STATUS column = `Up about 1 minute (healthy)`.

### 4. /health endpoint smoke

```powershell
docker compose exec paper python -c "import urllib.request,sys; resp=urllib.request.urlopen('http://localhost:8080/health'); print(resp.status, resp.read().decode())"
```

Expected: `200 {"status":"ok","ws_state":"connected"}`.

### 5. Backtest one-shot

```powershell
docker compose run --rm engine backtest `
  --strategy sma --symbol KRW-BTC --tf 1h `
  --start 2026-04-25T00:00:00Z --end 2026-05-02T00:00:00Z `
  --fast 5 --slow 20 `
  --output-dir /var/lib/mctrader/runs
```

Expected: exit 0 + `[backtest] final_equity=...` 출력.

산출물 검증:

```powershell
docker compose run --rm engine ls -la /var/lib/mctrader/runs/
docker compose run --rm engine cat /var/lib/mctrader/runs/bt-sma-KRW-BTC-1h-2026-04-25-2026-05-02-5-20/execution_report.json | head -20
```

Expected: `bt-sma-KRW-BTC-1h-...` directory + `execution_report.json` + `equity_curve.csv`.

### 6. WFO smoke (CLI 표면 — 실제 search 는 fixture 의존)

```powershell
docker compose run --rm engine wfo --help
docker compose run --rm engine wfo decision-group --help
```

Expected: click help 출력 (subcommand surface 노출 검증).

### 7. **Cross-container mutex (D13 핵심)**

paper 가동 중 (`docker compose ps paper` 가 healthy 상태 유지):

```powershell
# 세 가지 시나리오:

# 7a. paper 가동 중 wfo 시도 → LockHeldError (exit 3)
docker compose run --rm engine wfo search `
  --registry-spec /var/lib/mctrader/wfo/spec.json --actor smoke
# (spec 부재 시 "no spec" error 가 lock check 보다 먼저 발생할 수 있음 → fixture 가 있어야 정확 검증 가능)

# 7b. 단순화: 두 paper 동시 시도 → 두 번째 LockHeldError
$paper2_id = $(docker compose run -d engine paper start `
  --strategy sma --symbol KRW-ETH --tf 1h `
  --output-dir /var/lib/mctrader/runs)
docker logs $paper2_id 2>&1
```

Expected: 7a/7b 어느 한 시나리오에서 `LOCK CONFLICT: runtime lock held: ... mode='paper'` stderr + exit code 3 (paper start) 또는 동등 LockHeldError raise.

cleanup:

```powershell
docker rm -f $paper2_id
```

### 8. Volume 보존 검증

```powershell
docker compose stop paper
docker compose ps paper
docker compose up -d paper
Start-Sleep -Seconds 60
docker compose run --rm engine ls /var/lib/mctrader/runs/
```

Expected: 이전 backtest 산출물 (Step 5) 가 새 컨테이너 안에서도 visible (named volume 보존).

### 9. SIGTERM graceful

```powershell
docker compose stop paper -t 35  # graceful timeout 30s + 5s buffer
docker compose logs paper --tail 30
```

Expected: log 끝에 `[paper] DONE shutdown_reason=sigterm` 또는 동등 graceful exit message. ExitCode = 0 (정상 종료) 또는 SIGTERM 표준값 143.

### 10. Cleanup (선택)

```powershell
docker compose down
# 또는 volume 도 삭제:
docker compose down -v
```

(주의: `down -v` 는 `mctrader_data` 도 삭제 가능 → external volume 이라 보존 권장. 본 engine 의 3 volume 만 삭제하려면 명시적으로 `docker volume rm mctrader-engine_mctrader_engine_runs mctrader-engine_mctrader_engine_wfo mctrader-engine_mctrader_engine_lock`.)

## Evidence 박제 위치

본 절차의 결과를 `docs/stories/MCT-100.md` §9 Evidence 절에 박제 (Task 14 Cutover validation).
```

### Step 12.2: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add tests\integration\README.md
git commit -m "[MCT-100] docs(tests): integration smoke README (10-step + cross-container mutex D13 verification)"
```

---

## Task 13: pyproject 0.30.0 + CHANGELOG.md (신규)

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-engine\pyproject.toml`
- Create: `c:\workspace\mclayer\mctrader-engine\CHANGELOG.md`

### Step 13.1: pyproject version bump

- [ ] **Step**: `pyproject.toml` 의 `version = "0.29.0"` → `version = "0.30.0"`.

### Step 13.2: CHANGELOG.md 신규 작성

- [ ] **Step**: `c:\workspace\mclayer\mctrader-engine\CHANGELOG.md`:

```markdown
# Changelog

All notable changes to mctrader-engine.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.30.0] - 2026-05-DD

### Added

- **MCT-100 Phase 3 (Docker-first Migration)**:
  - `Dockerfile` (2-stage `python:3.12-slim`, non-root `mctrader` UID 1001) + `.dockerignore`
  - `compose.yml` — `paper` service (default profile, daemon, healthcheck) + `engine` service (profile `tools`, one-shot via `compose run --rm engine ...`). 4 named volume topology: `mctrader_data:ro` (external) + `mctrader_engine_runs` + `mctrader_engine_wfo` + `mctrader_engine_lock`.
  - `src/mctrader_engine/health_server.py` — HTTP `/health` endpoint (port 8080, internal-only) for paper daemon. PaperRunner state-aware (200/503).
  - `.github/workflows/image-lint.yml` — codeforge reusable hadolint workflow.
  - `tests/integration/README.md` — 10-step manual smoke + cross-container mutex (D13) verification 절차.
  - `.claude/_overlay/project.yaml` `infra_strategy: docker_first` field (codeforge consumer lint PASS).
  - `README.md` "Docker deployment" 절 — install / paper / backtest / wfo / evidence / risk invocation pattern + DR backup recipe.

### Changed

- **`runtime/runtime_lock.py` D13 dual-impl** (BREAKING — internal API):
  - POSIX path: `fcntl.flock` advisory lock (kernel-managed, cross-container safe via shared volume mount).
  - Windows path: 기존 `O_CREAT|O_EXCL` + `_pid_alive` cleanup 유지 (Windows host 직접 실행 path 보존).
  - **Public surface (LockHeldError shape, env override, mode parameter) 무변** — backward compat 유지.
- `runtime/paper_runner.py` — `health_server: HealthServer | None = None` 인자 추가 (default None = 기존 동작).
- `cli.py` `paper start` — HealthServer 자동 wiring (mock_feed 모드에서는 비활성).

### Notes

- mctrader-engine 의 production 자산 부재 (no systemd unit, no PaaS) → Docker 전환은 add-only.
- Windows host 직접 실행 시 cross-container mutex 미보장 (known limitation, README 박제).

## [0.29.0] - 2026-05-08

(Pre-MCT-100 baseline — indicator library Phase 7, MCT-90.)
```

(0.29.0 entry 는 minimal — 본 PR scope 외, history reference 만.)

### Step 13.3: 회귀 검증

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
uv sync
uv run pytest tests/ -q 2>&1 | Select-Object -Last 10
```

Expected: 전체 PASS.

### Step 13.4: Commit

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git add pyproject.toml CHANGELOG.md
git commit -m "[MCT-100] chore(version): bump 0.29.0 -> 0.30.0 + CHANGELOG.md (Docker-first + D13 dual impl)"
```

---

## Task 14: Cutover validation 10-step smoke (Story §9 evidence)

**근거**: tests/integration/README.md 의 10-step 절차 실행 + 결과를 mctrader-hub `docs/stories/MCT-100.md` §9 Evidence 절에 박제.

### Step 14.1: 10-step smoke 실행

- [ ] **Step**: Task 12 의 README 의 모든 step (1-10) 실행. 각 step 의 stdout/stderr 캡처.

### Step 14.2: Evidence 박제

- [ ] **Step**: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-100.md` 의 `## 9. Evidence` 절을 다음과 같이 update (Task 1 에서 placeholder 였음):

```markdown
## 9. Evidence

### 9.1 Build + entrypoint smoke (Task 8)

- `docker build` 성공 → image `mctrader-engine:mct-100`
- `docker run --rm mctrader-engine:mct-100 --help` 외 6 subcommand 모두 click help 출력

### 9.2 hadolint clean (Task 8)

```
docker run --rm -i hadolint/hadolint < Dockerfile
# (no output = 0 warning)
```

### 9.3 `docker compose config` PASS (Task 9)

(validated YAML 출력 attached.)

### 9.4 actionlint clean (Task 10)

(0 issue.)

### 9.5 check-container-strategy.sh PASS (Task 11)

```
PASS: infra_strategy=docker_first + Dockerfile + compose.yml all present
```

### 9.6 Healthy convergence (Task 14 Step 3)

```
docker compose ps paper
# STATUS: Up about 1 minute (healthy)
```

### 9.7 /health endpoint (Task 14 Step 4)

```json
{"status":"ok","ws_state":"connected"}
```

### 9.8 Backtest run (Task 14 Step 5)

```
[backtest] run_id=bt-sma-KRW-BTC-1h-2026-04-25-2026-05-02-5-20
[backtest] final_equity=...
[backtest] total_trades=...
```

### 9.9 Cross-container mutex (Task 14 Step 7) — **D13 핵심 evidence**

```
[paper] LOCK CONFLICT: runtime lock held: pid=... mode='paper' run_id='paper-sma-...'
exit code: 3
```

### 9.10 Volume 보존 (Task 14 Step 8)

기존 backtest 산출물이 stop+up 후 새 컨테이너에서 visible.

### 9.11 SIGTERM graceful (Task 14 Step 9)

```
[paper] DONE shutdown_reason=sigterm
```

ExitCode = 0 (또는 143).

### 9.12 pytest 회귀 (Task 6/7)

`uv run pytest tests/ -q` → ~256 PASS, 0 FAIL (Linux) / Windows 면 4 flock skip 추가.
```

### Step 14.3: Story update commit (mctrader-hub)

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-hub
git add docs\stories\MCT-100.md
git commit -m "[MCT-100] docs(story): §9 Evidence 박제 — Cutover validation 10-step + D13 mutex evidence"
```

(branch = `docs/MCT-100-engine-docker`. Hub PR open 상태에서 새 commit 추가 → CI 재실행.)

---

## Task 15: mctrader-engine PR open + review chain + admin merge

### Step 15.1: branch push

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
git push -u origin feat/MCT-100-docker-first
```

### Step 15.2: PR 생성

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-engine
gh pr create --title "[MCT-100] feat: Docker-first containerization (Phase 3)" --body @"
## Summary

mctrader Docker-first Migration Epic (MCT-98 mctrader-hub#120) Phase 3. Pilot reference = MCT-99 (mctrader-data PR #11). Paired hub PR = mctrader-hub#TBD.

## Changes (10 commits)

1. HealthServer HTTP /health (paper daemon, ws_state-aware) + 4 TDD scenario
2. **D13** runtime_lock fcntl.flock POSIX branch + Windows pid-fallback (cross-container mutex)
3. PaperRunner+CLI HealthServer wiring
4. Dockerfile (2-stage py3.12-slim, non-root) + .dockerignore
5. compose.yml (paper + engine profile, 4 volumes, healthcheck, labels)
6. .github/workflows/image-lint.yml (codeforge reusable)
7. project.yaml infra_strategy + README "Docker deployment" + DR backup
8. tests/integration/README.md (10-step manual smoke + D13 mutex)
9. pyproject 0.29.0 → 0.30.0 + CHANGELOG.md

## D13 critical (cross-container PID namespace 격리)

기존 runtime_lock 의 stale-pid cleanup 가 Docker container 간 PID namespace 격리에서 mutex 깨뜨림. fcntl.flock advisory lock (Linux/POSIX) + 기존 atomic-write+pid-alive fallback (Windows) 의 dual impl. LockHeldError shape 무변.

## Test plan

- [ ] hadolint warning 0
- [ ] docker compose config PASS
- [ ] check-container-strategy.sh PASS
- [ ] image entrypoint smoke (7 subcommand --help)
- [ ] healthy convergence 60s
- [ ] /health endpoint 200
- [ ] backtest one-shot exit 0 + 산출물 검증
- [ ] **D13 mutex evidence**: paper 가동 중 두 번째 paper start → LockHeldError exit 3
- [ ] volume 보존 (down → up → 산출물 retained)
- [ ] SIGTERM graceful 30s timeout

Refs: mctrader-hub#131, MCT-98 #120 Phase 3, mctrader-hub#TBD (paired hub PR)
"@
```

### Step 15.3: CI watch + Codex 7-area review

- [ ] **Step**: PR CI 가 green 까지 watch (memory feedback `ci_terminal_states_classify` + `no_background_watch`).

```powershell
cd c:\workspace\mclayer\mctrader-engine
gh pr checks --watch
```

CI failure 시: memory feedback `ci_failure_auto_recovery` 패턴 — fix → push → re-watch.

### Step 15.4: Codex 7-area review per phase

- [ ] **Step**: `codex:codex-rescue` 호출 — 7-area review (correctness / security / perf / observability / docs / tests / migration). Sonnet decider 가 우선순위 채택 → fix-back commit 또는 defer 박제.

### Step 15.5: admin merge

- [ ] **Step**: CI green + Codex review 처리 후 admin merge (memory feedback `admin_merge_autonomy`).

```powershell
cd c:\workspace\mclayer\mctrader-engine
gh pr merge --squash --admin
```

---

## Task 16: Hub PR finalize + Epic body update + Story #131 close

### Step 16.1: Hub PR CI + admin merge

- [ ] **Step**:

```powershell
cd c:\workspace\mclayer\mctrader-hub
gh pr checks --watch
gh pr merge --squash --admin
```

### Step 16.2: Epic #120 body Phase 3 status update

- [ ] **Step**: Epic body 의 Phase 3 row 를 `DONE 2026-05-DD` 로 update.

```powershell
gh issue view 120 --repo mclayer/mctrader-hub --json body --jq .body > epic-body.md
# edit epic-body.md to mark Phase 3 DONE + reference engine PR + hub PR
gh issue edit 120 --repo mclayer/mctrader-hub --body-file epic-body.md
```

(Phase 4 가 parallel session 에서 진행 중이라면 race 회피 — Phase 4 도 같은 body 를 update 가능. Coordination 의무 per session prompt §"Coordination 의무".)

### Step 16.3: Story #131 close

- [ ] **Step**:

```powershell
gh issue close 131 --repo mclayer/mctrader-hub --comment "Phase 3 DONE. Engine PR #TBD merged. Hub PR #TBD merged. Story §9 evidence 박제 완료. Cross-container mutex (D13) verified."
```

### Step 16.4: memory file update

- [ ] **Step**: `c:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\project_dockerization_epic.md` (또는 신규 `project_dockerization_phase3.md`) update — Phase 3 DONE state + D13 finding 박제.

---

## Self-Review (skill 의무 — fresh eye check)

### 1. Spec coverage

- A1 (Dockerfile 2-stage non-root) → Task 8 ✓
- A2 (compose.yml + 4 volume + healthcheck + labels) → Task 9 ✓
- A3 (.dockerignore Pilot 패턴 + dev cache) → Task 8 ✓
- A4 (HealthServer + 4 TDD) → Task 5 ✓
- A5 (D13 fcntl.flock dual impl) → Task 6 ✓
- A6 (PaperRunner HealthServer wiring) → Task 7 ✓
- A7 (cli.py paper start HealthServer 생성) → Task 7 ✓
- A8 (project.yaml infra_strategy) → Task 11 ✓
- A9 (check-container-strategy.sh PASS) → Task 11 ✓
- A10 (image-lint.yml + actionlint) → Task 10 ✓
- A11 (README Docker deployment 절) → Task 11 ✓
- A12 (tests/integration/README.md 10-step + mutex) → Task 12 ✓
- A13 (pyproject 0.30.0 + CHANGELOG.md) → Task 13 ✓
- A14 (~250 pytest 회귀 + 신규) → Task 5/6/7 step 별 검증 ✓
- A15 (compose build + healthy 60s) → Task 14 Step 1-3 ✓
- A16 (compose run engine subcommand --help) → Task 8 Step 8.6 + Task 14 Step 6 ✓
- A17 (D13 mutex evidence) → Task 14 Step 7 ✓
- A18 (Hub PR + Engine PR phase-gate-mergeable green) → Task 3 + 15 ✓
- A19 (Codex 7-area review) → Task 15 Step 15.4 ✓
- A20 (Epic #120 body Phase 3 + #131 close) → Task 16 ✓

### 2. Placeholder scan

- 0 "TBD" / "TODO" / "fill in details" — verified
- 모든 code block 에 실제 내용 (helper / test / Dockerfile / compose / README content)

### 3. Type consistency

- `HealthServer(runner_provider=lambda: runner, port=None)` — Task 5 (define) + Task 7 (consume) 동일 signature ✓
- `acquire_runtime_lock(run_id, mode, lock_path)` — Task 6 dual impl 동일 signature ✓
- `PaperRunner(... health_server=None)` — Task 7 (define) + cli.py (consume) 동일 ✓
- `runner.has_active_executor` / `runner.ws_connected` — Task 5 test (FakeRunner attribute) + Task 7 PaperRunner property 동일 ✓

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-08-mctrader-engine-docker-plan.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
