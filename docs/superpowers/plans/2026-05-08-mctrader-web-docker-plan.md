# mctrader-web Docker-first Containerization (Phase 4) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-web 의 Docker-first 전환 — multi-service compose (api + panel) + sqlite hash chain integrity-aware DR + cross-stack volume RO + localhost-bind env override.

**Architecture:** 2 service compose (FastAPI api + Streamlit panel), single named volume `mctrader_web_data` (api RW only) + external `mctrader-data_mctrader_data` (RO), in-process asyncio.Task pattern (ADR-014 정합), D6 TLS env exempt path, D8 standalone fallback env, ADR-016 amendment 단독 (D12 γ).

**Tech Stack:** Python 3.12-slim, FastAPI uvicorn, Streamlit 1.28+, sqlite3 WAL, uv install, hadolint, docker compose v2, pytest TDD.

**Spec reference:** `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md` — 13 결정 freeze (D1-D13) + ADR-016 amendment 4 항목 + Phase 3 surface 4 항목.

**Branch strategy:**
- mctrader-hub spec/plan branch: `docs/MCT-101-web-docker` (이미 cherry-pick 으로 spec commit `a5cbcd8` 박제됨)
- mctrader-web impl branch: `feat/MCT-101-docker-first` (Phase 2 진입 시 create)

**Phase sequencing:**
- **Phase 1**: mctrader-hub doc PR (spec + plan + Story §1-§7 + ADR-016 amendment) — 본 plan 작성 + Story scaffold + ADR amend + PR
- **Phase 2**: mctrader-web impl PR (Dockerfile + compose + D6/D8 코드 + assets + tests) — TDD chain
- **Phase 3**: integration smoke + Codex 7-area review per phase
- **Phase 4**: PR merge + Story §8.5/§9/§11 + Epic #120 body update + reconciliation (Phase 3 race)

---

## Phase 1 — mctrader-hub doc PR

### Task 1.1: Story file MCT-101.md scaffold (§1-§7)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-hub/docs/stories/MCT-101.md`

**Reference format**: `docs/stories/MCT-99.md` (Pilot Story) + `docs/stories/MCT-97.md` (most recent feature Story). 11 section number (`## 1.` ~ `## 11.`).

- [ ] **Step 1: Write Story file with §1-§7 + §10/§11 placeholder**

```markdown
---
story_key: MCT-101
story_issues:
  - repo: mclayer/mctrader-hub
    number: 132
status: in_progress
---

# MCT-101: mctrader-web Docker-first Containerization (Phase 4 sister)

- **Issue**: #132
- **Status**: in_progress (Phase 4 entry 2026-05-08)
- **Parent Epic**: mctrader-hub#120 — mctrader Docker-first Migration
- **Trigger**: Pilot Story §11.4 high risk sister rollout (multi-service compose + sqlite hash chain DR)

## 1. 사용자 요구사항 (verbatim, 2026-05-08 Phase 4 session entry)

> "mctrader Docker-first Migration Epic (MCT-98 #120) Phase 4 진행 — mctrader-web sister (multi-service compose). 본 session 은 parallel Phase 3 (MCT-100 mctrader-engine #131) 와 독립. Pilot Story §11.4 기준 high risk."

## 2. 도메인 해석

### 2.1 Phase 4 scope

mctrader-web repo 의 Docker-first 전환. 2-service compose (api FastAPI + panel Streamlit), single named volume `mctrader_web_data` (api RW only) + external cross-stack volume `mctrader-data_mctrader_data` (RO), in-process asyncio.Task 패턴 유지 (ADR-014), D6 localhost-bind env override, D8 standalone fallback env, D12 ADR-016 amendment 단독.

### 2.2 ADR-033 §7.4 OpRiskArch 4 항목 박제 의무

- restart policy
- volume DR (sqlite hash chain integrity-aware)
- health check tuning (양 service)
- network mode (api host expose 0)

→ Pilot pattern 차용 + multi-service novel pattern + sqlite hash chain DR 특화.

## 3. 관련 ADR

- codeforge ADR-033 (carrier_story CFP-128) — Phase 4 trigger
- ADR-014 — control plane vs data plane separation (single FastAPI process invariant)
- ADR-016 — Audit log append-only with hash chain (본 Story 의 주 amendment 대상, D12 γ)
- ADR-009 §D12 — Pilot pattern reference 만 (추가 amend 0, Phase 3 race 회피)
- ADR-002 D6 — engine paper ledger (mctrader-engine repo, 본 Story 무관)

## 4. 관련 코드 경로 (mctrader-web)

### 신규
- `Dockerfile` (2-stage python:3.12-slim, non-root mctrader UID 1001)
- `compose.yml` (2 service api + panel, named volume + external volume + healthcheck per service)
- `.dockerignore` (D11 explicit list)
- `.github/workflows/image-lint.yml` (hadolint)
- `CHANGELOG.md` (신규 — `[0.14.0]` Docker-first BREAKING entry)
- `tests/integration/README.md` (manual smoke 절차)
- `tests/test_config_localhost_bind.py` (D6 TDD 4 시나리오)
- `tests/test_status_adapter_disable.py` (D8 TDD 2 시나리오)

### 수정
- `src/mctrader_web/api/config.py` (D6 env getter + validate_tls_for_host exempt path)
- `src/mctrader_web/api/cli.py` (MCTRADER_API_HOST env read)
- `src/mctrader_web/dashboard/status_adapter.py` (D8 MCTRADER_DISABLE_DATA_STATUS handler)
- `.claude/_overlay/project.yaml` (`infra_strategy: docker_first`)
- `README.md` (전면 재작성 — v0.1.0 placeholder → v0.14.0 actual + Docker deployment 절)
- `pyproject.toml` (0.13.0 → 0.14.0)
- `.gitignore` (`data/admin_audit.sqlite`, `*.sqlite-wal`, `*.sqlite-shm`)

### 삭제
(systemd 자산 0건 — Pilot 과 다름)

## 5. Acceptance Criteria

§"Acceptance Criteria (요약)" of spec — 14 항목 (Spec §11 참조).

## 7. 결정점 (D1-D13 brainstorming freeze)

§ 2.2 of spec — 13 항목 표 박제.

## 8. Phase 분해

- Phase 1: mctrader-hub doc PR (본 Story scaffold + plan + ADR-016 amend)
- Phase 2: mctrader-web impl PR (TDD chain)
- Phase 3: integration smoke + Codex review
- Phase 4: PR merge + §8.5/§9/§11 박제 + Epic #120 update

## 8.5 Implementation Manifest

(Phase 2 PR merge 후 commit-by-commit 박제)

## 9. Evidence

(Phase 3 smoke + Codex review 후 박제)

## 10. 거절된 대안

§ 10 of spec — 13 결정 rejected column.

## 11. 회고

(Phase 4 종료 후 박제 — Phase 3 reconciliation 책임 + cross-cutting findings 정리)
```

- [ ] **Step 2: Commit Story scaffold**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" add docs/stories/MCT-101.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(story): MCT-101 scaffold §1-§7 + §10 reference + §11 placeholder

Phase 4 sister Story scaffold. §8.5/§9/§11 후속 commit 으로 박제."
```

---

### Task 1.2: ADR-016 amendment (D12 γ)

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-hub/docs/adr/ADR-016-audit-log-immutability.md` — Amendment History entry + §"Backup + retention" 절 4 항목 추가

- [ ] **Step 1: Add Amendment History entry near top**

After "## Status" / "Accepted — 2026-05-06.":

```markdown
**Amendment History**:
- 2026-05-08 — §"Backup + retention" 절에 Docker named volume backup recipe + WAL checkpoint 사전 호출 + backup-then-verify invariant + restore genesis preservation + cross-platform NFS/SMB 금지 추가. MCT-101 Phase 4 (mctrader-web Docker-first containerization).
```

- [ ] **Step 2: Append 4 항목 to §"Backup + retention" 절 (다음 §"Data integrity invariant" 직전)**

```markdown
### Docker volume backup recipe (Amendment 2026-05-08, MCT-101 Phase 4)

mctrader-web Docker-first 전환에 따라 audit DB 가 named volume 안에 위치. 표준 backup 절차:

#### A1. Backup recipe (PowerShell + bash)

```powershell
# Windows / PowerShell
$timestamp = Get-Date -Format yyyyMMdd_HHmmss
docker compose exec api python -c "import sqlite3; c=sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite'); c.execute('PRAGMA wal_checkpoint(FULL)'); c.close()"
docker run --rm `
  -v mctrader_web_data:/source:ro `
  -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_web_audit_${timestamp}.tar.gz -C /source .
docker compose exec api mctrader-cli audit-verify
```

```bash
# Linux / bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec api python -c "import sqlite3; c=sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite'); c.execute('PRAGMA wal_checkpoint(FULL)'); c.close()"
docker run --rm \
  -v mctrader_web_data:/source:ro \
  -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_web_audit_${TIMESTAMP}.tar.gz -C /source .
docker compose exec api mctrader-cli audit-verify
```

#### A2. Backup-then-verify invariant

backup 직후 즉시 `mctrader-cli audit-verify` 실행 의무. 실패 시 backup file 삭제 + alert (operator 의무). WAL fsync 미보장 시 chain integrity 깨짐 가능 — 본 invariant 가 backup integrity 의 ground truth.

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

restore 후 chain re-verify FAIL 시 = backup corruption → restore 롤백 (이전 backup 시도 또는 manual chain forensics). genesis hash 보존 invariant — restore 가 backup 시점의 genesis row 까지 정확 복구해야 chain 무결성 유지.

#### A4. Cross-platform invariant

- Windows + Linux Docker Desktop 양쪽 동등 (named volume 의 underlying fs = local driver).
- **NFS / SMB / network filesystem 위 named volume 금지** — WAL fsync 보장 안 됨 → hash chain race 가능.
- production 환경에서 named volume 의 underlying directory 가 local fs 인지 확인 의무.
```

- [ ] **Step 3: Commit ADR amendment**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" add docs/adr/ADR-016-audit-log-immutability.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(adr): ADR-016 amendment — Docker volume backup + hash chain integrity

Amendment 2026-05-08 (Phase 4 MCT-101). §\"Backup + retention\" 절에:
- A1 Docker named volume backup recipe (PowerShell + bash, WAL checkpoint 사전)
- A2 Backup-then-verify invariant (audit-verify 자동 실행)
- A3 Restore safety + genesis preservation (chain re-verify 의무)
- A4 Cross-platform NFS/SMB 금지 (WAL fsync 미보장)

D12 γ 채택 (Codex + Sonnet decider). ADR-009 §D12 추가 amend 0 (Phase 3 race 회피)."
```

---

### Task 1.3: Plan file commit

**Files:**
- Create: `c:/workspace/mclayer/mctrader-hub/docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md` (본 file)

- [ ] **Step 1: Verify plan file exists + commit**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" add docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(plan): mctrader-web Docker-first impl plan

Phase 1-4 sequencing + bite-sized TDD tasks per phase. Spec §11
\"다음 단계\" 박제 + Pilot pattern 차용 + Phase 3 race 회피 의무."
```

---

### Task 1.4: Phase 1 PR push + Codex 7-area review + admin merge

- [ ] **Step 1: Push branch to origin**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" push -u origin docs/MCT-101-web-docker
```

- [ ] **Step 2: Create Phase 1 PR (mctrader-hub)**

```bash
gh pr create --repo mclayer/mctrader-hub \
  --base main \
  --head docs/MCT-101-web-docker \
  --title "[MCT-101] docs: mctrader-web Docker-first design + plan + Story scaffold + ADR-016 amendment" \
  --body "$(cat <<'EOF'
## Summary

Phase 4 (mctrader-web sister) doc PR — Pilot Story §11.4 high risk multi-service novel pattern + sqlite hash chain DR.

- Spec: `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md` (666 lines, 11 sections + 14 AC)
- Plan: `docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md` (bite-sized TDD)
- Story: `docs/stories/MCT-101.md` (§1-§7 + §10/§11 placeholder)
- ADR-016 amendment: §"Backup + retention" 절에 Docker volume backup + hash chain verify 4 항목 추가 (D12 γ)

13 결정 freeze (D1-D13) — Codex agentId `a9897ebe62347932a` + Sonnet decider 합성. Pilot ADR-009 §D12 추가 amend 0 (Phase 3 race 회피).

Phase 3 (engine MCT-100, mctrader-hub#131) parallel — cross-cutting surface 4 항목 박제 (`memory/project_dockerization_phase4.md`).

## Test plan

- [ ] mctrader-hub schema lint workflows pass
- [ ] phase-gate-mergeable green
- [ ] Codex 7-area review (Architecture / Security / Test / DataMigration / OperationalRisk / Performance / Refactor) push-back 후 fix-back 또는 defer 박제
- [ ] admin merge → Phase 2 (mctrader-web impl PR) 진입

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Codex 7-area review dispatch**

Use Agent({subagent_type: "codex:codex-rescue", ...}):

```
Review PR mclayer/mctrader-hub PR #N (Phase 4 doc PR). 7-area:
1. Architecture/Boundary
2. Security/Threat
3. Test Contract
4. Data Migration / Schema (ADR-016 amendment)
5. Operational Risk (volume DR + WAL + cross-platform)
6. Performance
7. Refactor / Code Smell

Spec: docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md
Plan: docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md
ADR amendment: docs/adr/ADR-016-audit-log-immutability.md (Amendment History 2026-05-08)

Output: per-area finding (Severity Critical/High/Medium/Low) + accept/reject/defer recommendation.
```

- [ ] **Step 4: Process Codex push-back**

Per `phase_codex_review_loop` memory feedback — Sonnet decider 우선순위 채택. Critical/High = fix-back commit 의무. Medium/Low = defer 박제 (Story §11 회고 또는 Out-of-scope).

- [ ] **Step 5: CI watch + admin merge**

Per `admin_merge_autonomy` + `ci_terminal_states_classify` memory feedback. CI green 후 즉시 admin merge:

```bash
gh pr merge --repo mclayer/mctrader-hub <PR-N> --admin --squash --delete-branch
```

---

## Phase 2 — mctrader-web impl PR (TDD chain)

### Task 2.0: Branch setup on mctrader-web

**Files:**
- mctrader-web repo working tree

- [ ] **Step 1: Switch to mctrader-web repo + verify clean main**

```bash
cd "c:/workspace/mclayer/mctrader-web"
git status
git checkout main
git pull --ff-only
```

Expected: clean working tree on main, up-to-date with origin.

- [ ] **Step 2: Create impl branch**

```bash
git checkout -b feat/MCT-101-docker-first
```

---

### Task 2.1: D6 — `get_api_host()` env getter TDD

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/tests/test_config_localhost_bind.py`
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/api/config.py` — add `get_api_host()`

- [ ] **Step 1: Write failing test**

```python
# tests/test_config_localhost_bind.py
"""TDD for D6 — localhost-bind env override (MCT-101 Phase 4)."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from mctrader_web.api.config import (
    DEFAULT_HOST,
    get_api_host,
    is_localhost_binding,
    is_non_localhost_no_tls_allowed,
    validate_tls_for_host,
)


class TestGetApiHost:
    def test_default_returns_default_host(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCTRADER_API_HOST", None)
            assert get_api_host() == DEFAULT_HOST

    def test_env_override_applied(self) -> None:
        with mock.patch.dict(os.environ, {"MCTRADER_API_HOST": "0.0.0.0"}):
            assert get_api_host() == "0.0.0.0"
```

- [ ] **Step 2: Run test → verify FAIL**

```
pytest tests/test_config_localhost_bind.py::TestGetApiHost -v
```

Expected: ImportError or AttributeError ("get_api_host not defined" / "is_non_localhost_no_tls_allowed not defined")

- [ ] **Step 3: Add `get_api_host()` to config.py**

In `src/mctrader_web/api/config.py`, after `DEFAULT_CORS_ORIGIN = "..."` line:

```python
def get_api_host() -> str:
    """Return API uvicorn bind host. Default DEFAULT_HOST=127.0.0.1.

    Env override: MCTRADER_API_HOST (e.g., '0.0.0.0' for compose-internal network).
    Combined with MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1, allows non-localhost bind
    inside Docker compose network without TLS (host port mapping 0 의무).
    """
    return os.environ.get("MCTRADER_API_HOST", DEFAULT_HOST)
```

- [ ] **Step 4: Run test → verify PASS for `TestGetApiHost`**

```
pytest tests/test_config_localhost_bind.py::TestGetApiHost -v
```

Expected: 2 PASS (one will still fail on import — wait until Task 2.2 done).

---

### Task 2.2: D6 — `is_non_localhost_no_tls_allowed()` env getter TDD

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/tests/test_config_localhost_bind.py`
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/api/config.py`

- [ ] **Step 1: Append failing test class**

```python
class TestIsNonLocalhostNoTlsAllowed:
    def test_default_returns_false(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS", None)
            assert is_non_localhost_no_tls_allowed() is False

    @pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE", "Yes"])
    def test_truthy_values_return_true(self, value: str) -> None:
        with mock.patch.dict(os.environ, {"MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS": value}):
            assert is_non_localhost_no_tls_allowed() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", ""])
    def test_falsy_values_return_false(self, value: str) -> None:
        with mock.patch.dict(os.environ, {"MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS": value}):
            assert is_non_localhost_no_tls_allowed() is False
```

- [ ] **Step 2: Run test → verify FAIL**

```
pytest tests/test_config_localhost_bind.py::TestIsNonLocalhostNoTlsAllowed -v
```

Expected: ImportError on `is_non_localhost_no_tls_allowed`.

- [ ] **Step 3: Add `is_non_localhost_no_tls_allowed()` to config.py**

```python
def is_non_localhost_no_tls_allowed() -> bool:
    """Return True if env opt-in to bypass TLS validation for non-localhost binding.

    Env: MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS = '1' / 'true' / 'yes' (case-insensitive).
    Use ONLY when host port mapping is 0 (compose `ports:` 미명시) — host network
    노출 부재 시 안전. README + compose.yml 의 양쪽 자산이 invariant 표현.
    """
    raw = os.environ.get("MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS", "").strip().lower()
    return raw in ("1", "true", "yes")
```

- [ ] **Step 4: Run test → verify PASS**

```
pytest tests/test_config_localhost_bind.py::TestIsNonLocalhostNoTlsAllowed -v
```

Expected: all parametrize cases PASS.

---

### Task 2.3: D6 — `validate_tls_for_host()` exempt path TDD

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/tests/test_config_localhost_bind.py`
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/api/config.py`

- [ ] **Step 1: Append failing test class**

```python
class TestValidateTlsForHostExemptPath:
    def test_localhost_exempt(self) -> None:
        # 기존 invariant 보존 — localhost binding 은 항상 exempt
        validate_tls_for_host("127.0.0.1")  # raises 없음

    def test_non_localhost_no_env_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS", None)
            os.environ.pop("MCTRADER_TLS_CERT_PATH", None)
            os.environ.pop("MCTRADER_TLS_KEY_PATH", None)
            with pytest.raises(ValueError, match="requires TLS"):
                validate_tls_for_host("0.0.0.0")

    def test_non_localhost_with_no_tls_env_exempts(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS": "1"},
        ):
            os.environ.pop("MCTRADER_TLS_CERT_PATH", None)
            os.environ.pop("MCTRADER_TLS_KEY_PATH", None)
            with pytest.warns(UserWarning, match="TLS validation bypassed"):
                validate_tls_for_host("0.0.0.0")  # 통과
```

- [ ] **Step 2: Run test → verify FAIL**

```
pytest tests/test_config_localhost_bind.py::TestValidateTlsForHostExemptPath -v
```

Expected: 1 PASS (localhost), 2 FAIL (env exempt path not yet wired).

- [ ] **Step 3: Modify `validate_tls_for_host()` in config.py**

```python
def validate_tls_for_host(host: str) -> None:
    """Raise ValueError if host is non-localhost and TLS cert+key are not set.

    Exemption (MCT-101 Phase 4):
      MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1 → bypass with warning. Use ONLY in
      compose-internal network with host port mapping 0 (compose `ports:` 미명시).
    """
    import warnings

    if is_localhost_binding(host):
        return  # localhost — TLS optional

    if is_non_localhost_no_tls_allowed():
        warnings.warn(
            "TLS validation bypassed via MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1 — "
            "assumed compose-internal network with host port mapping 0",
            UserWarning,
            stacklevel=2,
        )
        return

    cert = get_tls_cert_path()
    key = get_tls_key_path()
    if cert is None or key is None:
        raise ValueError(
            f"Non-localhost binding host={host!r} requires TLS. "
            "Set MCTRADER_TLS_CERT_PATH and MCTRADER_TLS_KEY_PATH, "
            "or use scripts/gen_dev_cert.ps1 to generate a self-signed cert. "
            "For Docker compose-internal network, set MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1 "
            "(host port mapping 0 의무)."
        )
```

- [ ] **Step 4: Run test → verify PASS**

```
pytest tests/test_config_localhost_bind.py -v
```

Expected: all 9 cases PASS (3 classes).

- [ ] **Step 5: Commit D6 implementation**

```bash
git add tests/test_config_localhost_bind.py src/mctrader_web/api/config.py
git commit -m "[MCT-101] feat(config): D6 localhost-bind env override + TLS exempt path

D6 brainstorming freeze. 신규 env:
- MCTRADER_API_HOST (default 127.0.0.1) — uvicorn bind host
- MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS (default false) — TLS validation exempt
  for compose-internal network. Use ONLY when host port mapping 0
  (compose \`ports:\` 미명시).

3 test class, 9 시나리오 PASS."
```

---

### Task 2.4: D6 — `cli.py` env-aware host wiring

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/api/cli.py`

- [ ] **Step 1: Update `cli.py` main() to use env getter**

```python
"""``mctrader-web-api`` console script (MCT-50, MCT-101 Phase 4 D6 env-aware host)."""

from __future__ import annotations

import uvicorn

from mctrader_web.api.config import (
    DEFAULT_PORT,
    get_api_host,
    validate_tls_for_host,
)


def main() -> None:
    """Run the FastAPI local runner service.

    Default: hard-binds to ``127.0.0.1`` — Bearer token + Paper-only
    enforce localhost-only invariant.
    
    MCT-101 Phase 4: env override MCTRADER_API_HOST allows non-localhost bind
    (e.g., '0.0.0.0' for Docker compose-internal network). Combined with
    MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1, bypasses TLS validation when host
    port mapping is 0 (compose `ports:` 미명시).
    """
    host = get_api_host()
    validate_tls_for_host(host)
    uvicorn.run(
        "mctrader_web.api.app:app",
        host=host,
        port=DEFAULT_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run regression pytest**

```
pytest tests/ -v --tb=short -x
```

Expected: 기존 tests + 9 신규 D6 PASS. tests/test_api_client_active_runs.py 등 cli.py 호출 안 함 → 회귀 0.

- [ ] **Step 3: Commit cli.py update**

```bash
git add src/mctrader_web/api/cli.py
git commit -m "[MCT-101] feat(cli): wire MCTRADER_API_HOST env override

D6 cli.py 가 get_api_host() + validate_tls_for_host() 호출. compose
환경에서 MCTRADER_API_HOST=0.0.0.0 + MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1
적용 시 exempt path 통과."
```

---

### Task 2.5: D8 — status_adapter `MCTRADER_DISABLE_DATA_STATUS` env handler TDD

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/tests/test_status_adapter_disable.py`
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/dashboard/status_adapter.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_status_adapter_disable.py
"""TDD for D8 — MCTRADER_DISABLE_DATA_STATUS standalone fallback (MCT-101)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from mctrader_web.dashboard.status_adapter import StatusResult, fetch_status


class TestStatusAdapterDisable:
    def test_disabled_env_returns_mock_yellow(self, tmp_path: Path) -> None:
        with mock.patch.dict(os.environ, {"MCTRADER_DISABLE_DATA_STATUS": "1"}):
            result = fetch_status(root=tmp_path, use_cache=False)
        assert isinstance(result, StatusResult)
        assert result.worst_level == 1  # yellow
        assert result.error is not None
        assert "disabled" in result.error.lower()
        assert result.nodes == []

    def test_disabled_env_skips_subprocess(self, tmp_path: Path) -> None:
        with mock.patch.dict(os.environ, {"MCTRADER_DISABLE_DATA_STATUS": "1"}):
            with mock.patch("subprocess.run") as mock_run:
                fetch_status(root=tmp_path, use_cache=False)
            mock_run.assert_not_called()
```

- [ ] **Step 2: Run test → verify FAIL**

```
pytest tests/test_status_adapter_disable.py -v
```

Expected: 2 FAIL (env handler not yet wired — subprocess.run is called or different result format).

- [ ] **Step 3: Add env handler to status_adapter.py `fetch_status()`**

In `src/mctrader_web/dashboard/status_adapter.py`, near top of `fetch_status()`:

```python
def _is_data_status_disabled() -> bool:
    """Return True if MCTRADER_DISABLE_DATA_STATUS env opts out of mctrader-data CLI.

    MCT-101 Phase 4 D8 — standalone deployment (mctrader-data peer 미가동) 시
    status_adapter 가 mock yellow return. compose 안에서 MCTRADER_DISABLE_DATA_STATUS=1
    set 하면 subprocess.run("mctrader-data ...") skip.
    """
    raw = os.environ.get("MCTRADER_DISABLE_DATA_STATUS", "").strip().lower()
    return raw in ("1", "true", "yes")


def fetch_status(
    root: Path | str,
    *,
    cli_path: str = "mctrader-data",
    timeout_seconds: float = 10.0,
    fresh_yellow_seconds: float = 10.0,
    fresh_red_seconds: float = 30.0,
    lag_yellow_seconds: float = 60.0,
    lag_red_seconds: float = 300.0,
    use_cache: bool = True,
) -> StatusResult:
    """..."""
    # MCT-101 D8: standalone fallback — mctrader-data peer 미가동 시 mock yellow
    if _is_data_status_disabled():
        return StatusResult(
            worst_level=1,
            nodes=[],
            error=(
                "data status disabled (MCTRADER_DISABLE_DATA_STATUS=1) — "
                "standalone mctrader-web deployment, mctrader-data peer not co-located"
            ),
            fetched_at=time.time(),
        )

    # ... 기존 implementation (cache + subprocess.run) ...
```

(기존 implementation 의 cache + subprocess block 은 변경 0 — 위 early return 만 추가.)

- [ ] **Step 4: Add `import os` if missing**

Verify `os` import 가 status_adapter.py top 에 있음 (이미 있을 가능성 — `os.path` 등). 없으면 추가:

```python
import os
```

- [ ] **Step 5: Run test → verify PASS**

```
pytest tests/test_status_adapter_disable.py -v
pytest tests/test_status_adapter.py -v  # 기존 회귀
```

Expected: 신규 2 PASS + 기존 PASS.

- [ ] **Step 6: Commit D8**

```bash
git add tests/test_status_adapter_disable.py src/mctrader_web/dashboard/status_adapter.py
git commit -m "[MCT-101] feat(status_adapter): D8 MCTRADER_DISABLE_DATA_STATUS env handler

D8 brainstorming freeze. standalone deployment (mctrader-data peer 미가동)
시 mock yellow return — silent green 0 보장. subprocess.run skip.

2 신규 시나리오 PASS + 기존 회귀 PASS."
```

---

### Task 2.6: `.dockerignore` (D11)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/.dockerignore`

- [ ] **Step 1: Write `.dockerignore`**

```
# .dockerignore — MCT-101 Phase 4 (D11 explicit list)
# codeforge cli-tool-minimal 패턴 + mctrader-web 특화

# git
.git/
.github/

# claude
.claude/

# Python venv + cache
.venv/
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.ruff_cache/
.coverage
.coverage.*
htmlcov/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Build artifacts
dist/
build/
*.egg-info/

# Docs
*.md
docs/
CHANGELOG.md
README.md

# Existing data artifacts (named volume mount 시 새로 생성)
data/
*.sqlite
*.sqlite-wal
*.sqlite-shm

# Windows-only scripts (image = linux)
scripts/*.ps1

# Test artifacts
test-results/
.tox/
```

- [ ] **Step 2: Commit**

```bash
git add .dockerignore
git commit -m "[MCT-101] feat(docker): .dockerignore (D11 explicit list)

git/.github/.claude/.venv/__pycache__/.pytest_cache/.ruff_cache/.coverage/
docs/*.md/data/*.sqlite*/.ps1 모두 제외. image build context 안 sensitive
file 누설 0."
```

---

### Task 2.7: `Dockerfile` (2-stage, non-root, no HEALTHCHECK directive)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/Dockerfile`

- [ ] **Step 1: Write Dockerfile (Pilot 패턴 차용 + dashboard extra 추가)**

```dockerfile
# syntax=docker/dockerfile:1.7
# MCT-101 Phase 4 — mctrader-web Docker-first (multi-service compose)
# 2-stage build (deps / runner). non-root user mctrader UID 1001.
# HEALTHCHECK directive 미포함 — compose-side healthcheck per service (api / panel).

#─── Stage 1: deps ───
FROM python:3.12-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build tools + git (git+https deps need git)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /build

# Copy project metadata + source for editable install
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install with dashboard extra (Streamlit + plotly + pandas)
RUN uv pip install --system --no-cache ".[dashboard]"

#─── Stage 2: runner ───
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd --gid 1001 mctrader && \
    useradd --uid 1001 --gid mctrader --shell /bin/bash --create-home mctrader

# Copy site-packages + console scripts from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Create writable dirs for named volume mount points
RUN mkdir -p /var/lib/mctrader/web /var/lib/mctrader/data && \
    chown -R mctrader:mctrader /var/lib/mctrader

USER mctrader
WORKDIR /home/mctrader

# Default CMD = api service (compose overrides for panel)
CMD ["mctrader-web-api"]
```

- [ ] **Step 2: hadolint local check**

```bash
docker run --rm -i hadolint/hadolint < Dockerfile
```

Expected: 0 warning. 만약 warning 발생 시 fix (예: `apt-get install -y --no-install-recommends`, `pin version` 등).

- [ ] **Step 3: Local docker build verify**

```bash
docker build -t mctrader-web:mct-101-local .
```

Expected: build success. image size 합리적 (< 800MB).

- [ ] **Step 4: image entrypoint smoke**

```bash
docker run --rm mctrader-web:mct-101-local mctrader-web-api --help 2>&1 | head -5
```

(uvicorn 실행되므로 actual smoke 는 compose 시점에. --help 미지원 시 그냥 import smoke):

```bash
docker run --rm mctrader-web:mct-101-local python -c "from mctrader_web.api.app import app; print('app imported OK')"
```

Expected: "app imported OK".

- [ ] **Step 5: Commit Dockerfile**

```bash
git add Dockerfile
git commit -m "[MCT-101] feat(docker): Dockerfile 2-stage python:3.12-slim non-root

Pilot mctrader-data 패턴 차용 + dashboard extra (Streamlit/plotly/pandas)
포함. mctrader UID 1001. /var/lib/mctrader/{web,data} mkdir + chown
(named volume mount points). HEALTHCHECK directive 미포함 (compose-side
per service). hadolint warning 0."
```

---

### Task 2.8: `compose.yml` (2-service + named + external volume + healthcheck + env)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/compose.yml`

- [ ] **Step 1: Write compose.yml**

```yaml
# compose.yml — MCT-101 Phase 4 (mctrader-web Docker-first)
# 2-service compose: api (FastAPI) + panel (Streamlit).
# Single named volume mctrader_web_data (api RW only).
# External cross-stack volume mctrader-data_mctrader_data (api RO).

services:
  api:
    build: .
    image: mctrader-web:mct-101
    command: ["mctrader-web-api"]
    environment:
      # D6: 0.0.0.0 bind in compose-internal network + TLS exempt + host port 0
      MCTRADER_API_HOST: "0.0.0.0"
      MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS: "1"
      # D2: env override paths (named volume)
      MCTRADER_TOKEN_PATH: "/var/lib/mctrader/web/token"
      MCTRADER_ADMIN_AUDIT_PATH: "/var/lib/mctrader/web/admin_audit.sqlite"
      MCTRADER_LOCK_PATH: "/var/lib/mctrader/web/paper.lock"
      # D2: HMAC secret (operator override 의무 — dev fallback insecure)
      # MCTRADER_ADMIN_TOKEN_SECRET: "<set in .env file or shell>"
      # D8: standalone fallback — mctrader-data peer 미가동 시 1 로 set
      # MCTRADER_DISABLE_DATA_STATUS: "1"
      # ADR-014 admin CORS — panel container origin
      MCTRADER_ADMIN_CORS_ORIGINS: "http://localhost:8501,http://panel:8501"
    volumes:
      - mctrader_web_data:/var/lib/mctrader/web:rw
      - mctrader-data_mctrader_data:/var/lib/mctrader/data:ro
    # D6: api host port 미노출 (compose-internal only — panel container 만 접근)
    # ports: 절 미명시
    healthcheck:
      test:
        ["CMD", "python", "-c",
         "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:7821/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - mctrader-web-net

  panel:
    build: .
    image: mctrader-web:mct-101
    command:
      - "streamlit"
      - "run"
      - "/usr/local/lib/python3.12/site-packages/mctrader_web/dashboard/app.py"
      - "--server.address=0.0.0.0"
      - "--server.port=8501"
      - "--server.headless=true"
      - "--browser.gatherUsageStats=false"
    environment:
      # api_client 가 cross-container HTTP — service name "api"
      MCTRADER_API_HOST_FOR_CLIENT: "api"
      MCTRADER_API_PORT_FOR_CLIENT: "7821"
      # Streamlit 기본 host
      STREAMLIT_SERVER_ADDRESS: "0.0.0.0"
    ports:
      # 사용자 browser 가 host:8501 → panel container:8501
      - "8501:8501"
    healthcheck:
      test:
        ["CMD", "python", "-c",
         "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - mctrader-web-net
    depends_on:
      api:
        condition: service_healthy

volumes:
  mctrader_web_data:
    # local driver default — Windows + Linux 양쪽 동등
  mctrader-data_mctrader_data:
    # External — Pilot mctrader-data stack 의 named volume
    # standalone deployment 시 본 volume 부재 → MCTRADER_DISABLE_DATA_STATUS=1 의무
    external: true

networks:
  mctrader-web-net:
    driver: bridge
```

- [ ] **Step 2: `docker compose config` syntax PASS**

```bash
docker compose config
```

Expected: compose.yml parsed + rendered output. external volume reference (`mctrader-data_mctrader_data`) 가 `volume not found` warning 시점은 `docker compose up` 시 (config 자체는 PASS).

만약 standalone smoke 시 external volume 부재로 fail 시 — 본 plan §"Phase 3 standalone smoke" 에서 `docker volume create mctrader-data_mctrader_data` 임시 생성 후 검증.

- [ ] **Step 3: Verify api_client port consistency**

`src/mctrader_web/api_client/client.py` 의 default `port=DEFAULT_PORT=7821` 그대로. panel container 가 client 사용 시 `host="api"` keyword 로 override 가능 (이미 코드 지원).

panel 의 dashboard/app.py 가 `MctraderApiClient()` 생성 시 host 를 어떻게 지정하는지 확인. default 가 `127.0.0.1` 이면 compose 환경에서 변경 의무.

```bash
grep -n "MctraderApiClient" src/mctrader_web/dashboard/*.py
```

Expected: instantiation site 식별. 만약 host hard-code 면 env override 필요 (Task 2.9 추가).

- [ ] **Step 4: Commit compose.yml**

```bash
git add compose.yml
git commit -m "[MCT-101] feat(docker): compose.yml 2-service (api + panel)

D1-D11 박제. named volume mctrader_web_data (api RW only) + external
mctrader-data_mctrader_data (api RO). 양 service healthcheck (api /health,
panel /_stcore/health). api host port 미노출 (D6 compose-internal only).
panel host:8501 expose. depends_on api healthy.

D6 env (MCTRADER_API_HOST=0.0.0.0 + MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1)
+ D2 path env (TOKEN/AUDIT/LOCK 모두 named volume) + D8 fallback env
(commented placeholder for standalone)."
```

---

### Task 2.9 (conditional): panel api_client host env wiring

**조건**: Task 2.8 Step 3 의 grep 결과 panel 측에서 `MctraderApiClient()` 가 default host 사용 시.

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/api_client/client.py` (env-aware default)
- 또는: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/dashboard/<page>.py` (env read at instantiation)

- [ ] **Step 1: Identify default host strategy**

api_client 가 env-aware default 가 자연스러운지 (cleaner) vs page 별 instantiation site 가 env read (더 explicit) 비교.

- [ ] **Step 2: Modify api_client/client.py**

```python
def __init__(
    self,
    *,
    host: str | None = None,
    port: int | None = None,
    token_path: Path | None = None,
) -> None:
    # MCT-101 Phase 4 D6: env-aware default for compose deployment
    if host is None:
        host = os.environ.get("MCTRADER_API_HOST_FOR_CLIENT", DEFAULT_HOST)
    if port is None:
        port_raw = os.environ.get("MCTRADER_API_PORT_FOR_CLIENT")
        port = int(port_raw) if port_raw else DEFAULT_PORT
    self._base_url = f"http://{host}:{port}"
    self._token_path = token_path or default_token_path()
```

- [ ] **Step 3: Add `import os` if missing**

- [ ] **Step 4: Run regression pytest (api_client tests)**

```
pytest tests/api -v
```

Expected: 기존 PASS (env unset → default 와 동일).

- [ ] **Step 5: Commit (if needed)**

```bash
git add src/mctrader_web/api_client/client.py
git commit -m "[MCT-101] feat(api_client): env-aware host/port default for compose

MCTRADER_API_HOST_FOR_CLIENT / MCTRADER_API_PORT_FOR_CLIENT env read.
panel container 안 \"api:7821\" cross-container HTTP. backward compat —
env unset 시 기존 DEFAULT_HOST/DEFAULT_PORT."
```

---

### Task 2.10: `.claude/_overlay/project.yaml` infra_strategy

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/.claude/_overlay/project.yaml`

- [ ] **Step 1: Add infra_strategy field**

After `project.name: mctrader` line:

```yaml
project:
  name: mctrader

# CFP-128 / ADR-033 — Docker-first infra (MCT-101 Phase 4)
infra_strategy: docker_first

github:
  ...
```

- [ ] **Step 2: Run codeforge lint**

```bash
bash scripts/check-container-strategy.sh
```

(또는 plugin path 의 script. exit code 0 PASS.)

Expected: PASS — infra_strategy: docker_first + Dockerfile + compose.yml 모두 존재.

- [ ] **Step 3: Commit**

```bash
git add .claude/_overlay/project.yaml
git commit -m "[MCT-101] feat(overlay): infra_strategy: docker_first

codeforge ADR-033 / CFP-128 정합. check-container-strategy.sh PASS
의무 (Dockerfile + compose.yml + infra_strategy 모두 존재)."
```

---

### Task 2.11: `.github/workflows/image-lint.yml`

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/.github/workflows/image-lint.yml`

- [ ] **Step 1: Write image-lint.yml**

(Pilot mctrader-data 패턴 그대로 차용)

```yaml
name: image-lint

on:
  pull_request:
    paths:
      - 'Dockerfile'
      - 'compose.yml'
      - '.dockerignore'
      - '.github/workflows/image-lint.yml'
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - 'compose.yml'
      - '.dockerignore'

jobs:
  hadolint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run hadolint
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          failure-threshold: warning
          format: tty

  compose-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: docker compose config syntax
        run: |
          # External volume creation (config 단계만 — actual mount 안 함)
          docker volume create mctrader-data_mctrader_data || true
          docker compose config
```

- [ ] **Step 2: actionlint local check**

```bash
# Optional — actionlint 가 설치된 경우
actionlint .github/workflows/image-lint.yml
```

Expected: 0 error.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/image-lint.yml
git commit -m "[MCT-101] ci: image-lint workflow (hadolint + compose config)

PR-trigger workflow 가 Dockerfile / compose.yml / .dockerignore 변경
시 hadolint failure-threshold=warning + docker compose config syntax
PASS 검증. push to main 도 trigger."
```

---

### Task 2.12: `pyproject.toml` version bump + `CHANGELOG.md` 신규

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/pyproject.toml` (0.13.0 → 0.14.0)
- Create: `c:/workspace/mclayer/mctrader-web/CHANGELOG.md`

- [ ] **Step 1: Bump version**

```python
[project]
name = "mctrader-web"
version = "0.14.0"
```

- [ ] **Step 2: Update description**

```python
description = "FastAPI Local Runner Service + Streamlit + Tick backtest + WFO + Promote + polymorphic dispatch + manifest persistence + /tick_detail wired + tick result viewer + Docker-first multi-service deployment - mctrader platform"
```

- [ ] **Step 3: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to mctrader-web will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.14.0] — 2026-05-08

### Added — MCT-101 Phase 4 Docker-first multi-service deployment

- `Dockerfile` 2-stage (python:3.12-slim, non-root mctrader UID 1001) + dashboard extra
- `compose.yml` 2-service (api + panel) + named volume `mctrader_web_data` + external `mctrader-data_mctrader_data` RO
- `.dockerignore` strict list (D11)
- `.github/workflows/image-lint.yml` hadolint + compose config syntax
- `tests/integration/README.md` manual smoke 절차 (multi-service healthy + sqlite WAL+hash chain backup verify + cross-stack volume RO)

### Changed — D6 env override + D8 standalone fallback

- `src/mctrader_web/api/config.py`:
  - 신규 `get_api_host()` (env `MCTRADER_API_HOST`, default `127.0.0.1`)
  - 신규 `is_non_localhost_no_tls_allowed()` (env `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS`)
  - `validate_tls_for_host()` 가 NO_TLS env 시 exempt + warning emit
- `src/mctrader_web/api/cli.py`: `MCTRADER_API_HOST` env read + `validate_tls_for_host()` 호출 후 uvicorn start
- `src/mctrader_web/dashboard/status_adapter.py`: `MCTRADER_DISABLE_DATA_STATUS=1` 시 mock yellow return
- `src/mctrader_web/api_client/client.py`: env-aware default host/port (`MCTRADER_API_HOST_FOR_CLIENT` / `MCTRADER_API_PORT_FOR_CLIENT`)
- `.claude/_overlay/project.yaml`: `infra_strategy: docker_first`
- `README.md`: 전면 재작성 (v0.1.0 placeholder → v0.14.0 actual + Docker deployment 절)
- `.gitignore`: `data/admin_audit.sqlite`, `*.sqlite-wal`, `*.sqlite-shm`

### Reference

- Spec: `mctrader-hub/docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md`
- Story: `mctrader-hub/docs/stories/MCT-101.md`
- ADR-016 amendment: `mctrader-hub/docs/adr/ADR-016-audit-log-immutability.md` (Amendment History 2026-05-08)
- Pilot reference: mctrader-data PR #11 (2026-05-07)

### Breaking changes

- compose 환경에서 `MCTRADER_ADMIN_TOKEN_SECRET` env explicit 의무 (dev fallback `dev-insecure-key-change-in-production` 그대로 작동하지만 production 시 set 의무).
- standalone deployment (mctrader-data peer 미가동) 시 `MCTRADER_DISABLE_DATA_STATUS=1` env set 의무 (panel admin status section yellow).

## [0.13.0] — 2026-05-06

(MCT-97 Admin Engine Control Panel — P3/P4/P5/P6 — multi-token RBAC + audit + idempotency + rate limit + admin CORS)

(이전 version 박제는 git history 참조)
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "[MCT-101] feat(release): bump 0.13.0 → 0.14.0 + CHANGELOG

Docker-first multi-service deployment release. semver minor (additive
features + env env override paths backward-compat). description 갱신
(\"Docker-first multi-service deployment\" 추가).

CHANGELOG.md 신규 — [0.14.0] entry + [0.13.0] historical reference."
```

---

### Task 2.13: `.gitignore` additions

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/.gitignore`

- [ ] **Step 1: Append entries**

```
# MCT-101 Phase 4 (Docker volume mount target)
data/admin_audit.sqlite
*.sqlite-wal
*.sqlite-shm
```

- [ ] **Step 2: Verify existing dev sqlite is still tracked**

```bash
git status data/admin_audit.sqlite
```

Expected: `data/admin_audit.sqlite` 가 tracked (이미 commit 됨 — `.gitignore` 가 forward-only 적용). git history 에서 제거는 본 Story scope 외.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "[MCT-101] chore(gitignore): exclude sqlite-wal/-shm + future audit DB

forward-only .gitignore. 기존 data/admin_audit.sqlite 는 tracked
(history 정리 별도 Story). sqlite-wal/-shm 은 새로 생성될 때 미tracked."
```

---

### Task 2.14: `README.md` 전면 재작성

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/README.md`

- [ ] **Step 1: Rewrite README**

```markdown
# mctrader-web

FastAPI local runner service + Streamlit dashboard + admin engine control panel for mctrader platform.

## Status

`v0.14.0` — Docker-first multi-service deployment (MCT-101 Phase 4, 2026-05-08).

## Quick start (Docker, recommended)

### Prerequisites

- Docker + docker compose v2 (Linux / Windows Docker Desktop)
- mctrader-data Pilot stack 가동 OR `MCTRADER_DISABLE_DATA_STATUS=1` env set (standalone)

### Boot

```bash
# Set HMAC secret (production 의무)
export MCTRADER_ADMIN_TOKEN_SECRET="$(openssl rand -hex 32)"

# Build + start
docker compose build
docker compose up -d

# Wait until both services healthy (~90s)
docker compose ps
# 양 service "Up X seconds (healthy)" 표시 의무

# Browser:
# http://localhost:8501  (Streamlit panel)
```

### Token bootstrap

(첫 부팅 시 `MultiTokenAuth` 가 admin token 자동 생성):

```bash
# View admin token (one-time grab)
docker compose exec api cat /var/lib/mctrader/web/local_token

# Use Bearer header in API calls
curl -H "Authorization: Bearer <token>" http://localhost:8501/...
```

### Standalone deployment (mctrader-data peer 미가동)

```bash
# .env file or shell env
export MCTRADER_DISABLE_DATA_STATUS=1

docker compose up -d
# panel admin status section = yellow (mock)
```

## Docker deployment

### Architecture

- **api service**: FastAPI uvicorn, internal `0.0.0.0:7821` bind (host port 미노출 — compose-internal network only). MultiTokenAuth (3-role RBAC). LifecycleManager / BacktestLifecycleManager / WfoLifecycleManager — in-process asyncio.Task pattern (ADR-014 정합).
- **panel service**: Streamlit, `0.0.0.0:8501` bind (host `8501:8501` mapped). api_client httpx → cross-container `api:7821`.
- **named volume `mctrader_web_data`**: api RW only. admin_audit.sqlite (ADR-016 hash chain) + token + token_secret + paper.lock.
- **external volume `mctrader-data_mctrader_data`** (RO on api): mctrader-data Pilot stack 의 OHLCV/tick/orderbook data — status_adapter read.

### Env reference

| Env | Default | Purpose |
|---|---|---|
| `MCTRADER_API_HOST` | `127.0.0.1` | uvicorn bind host. compose 시 `0.0.0.0`. |
| `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS` | unset | non-localhost bind 시 TLS exempt. compose-internal only — host port 미노출 의무. |
| `MCTRADER_TOKEN_PATH` | `~/.mctrader/local_token` | token file. compose 시 named volume path. |
| `MCTRADER_ADMIN_AUDIT_PATH` | `<package>/data/admin_audit.sqlite` | audit DB. compose 시 named volume path. |
| `MCTRADER_ADMIN_TOKEN_SECRET` | dev fallback | HMAC secret (production 의무 set). |
| `MCTRADER_LOCK_PATH` | engine default | paper.lock file. compose 시 named volume path. |
| `MCTRADER_DISABLE_DATA_STATUS` | unset | standalone fallback — status_adapter mock yellow. |
| `MCTRADER_ADMIN_CORS_ORIGINS` | `http://localhost:8501` | admin CORS allowlist (panel container origin). |

### Audit DR (ADR-016 amendment 2026-05-08)

#### Backup (PowerShell)

```powershell
$timestamp = Get-Date -Format yyyyMMdd_HHmmss
docker compose exec api python -c "import sqlite3; c=sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite'); c.execute('PRAGMA wal_checkpoint(FULL)'); c.close()"
docker run --rm `
  -v mctrader_web_data:/source:ro `
  -v ${PWD}:/backup `
  alpine tar czf /backup/mctrader_web_audit_${timestamp}.tar.gz -C /source .
docker compose exec api mctrader-cli audit-verify
```

#### Restore

```bash
docker compose stop api
docker run --rm \
  -v mctrader_web_data:/dest \
  -v "$(pwd):/backup" \
  alpine tar xzf /backup/mctrader_web_audit_<TIMESTAMP>.tar.gz -C /dest
docker compose start api
docker compose exec api mctrader-cli audit-verify
```

#### Backup invariant

- WAL checkpoint 사전 호출 의무 (-wal/-shm fsync race 회피)
- backup 직후 `mctrader-cli audit-verify` 실행 (실패 시 backup 삭제 + alert)
- restore 후 chain re-verify FAIL 시 backup corruption — 이전 backup 시도
- NFS / SMB volume 금지 (WAL fsync 미보장)

### Operations

```bash
# Stop
docker compose stop

# Start
docker compose start

# Logs
docker compose logs -f api
docker compose logs -f panel

# Restart api only
docker compose restart api

# Down (volume 보존)
docker compose down

# Down + volume 삭제 (DESTRUCTIVE)
docker compose down -v
```

### Manual integration smoke

`tests/integration/README.md` 참조.

## Development (non-Docker, legacy)

```bash
uv sync --extra dashboard --extra dev
uv run mctrader-web-api  # FastAPI on 127.0.0.1:7821
# 별도 터미널:
uv run streamlit run src/mctrader_web/dashboard/app.py  # Streamlit on 127.0.0.1:8501
```

(non-Docker 가동 시 `MCTRADER_API_HOST` env 미설정 = `127.0.0.1` default. status_adapter 가 host PATH 의 `mctrader-data` CLI 호출.)

## Public Python API

```python
from mctrader_web.api_client import MctraderApiClient
from mctrader_web.dashboard import (
    discover_runs,
    load_equity_curve,
    load_execution_report,
    parse_decimal_columns,
    format_krw,
    build_summary_metrics,
    build_equity_chart,
)
```

## Related

- [mctrader-engine](https://github.com/mclayer/mctrader-engine) — produces ExecutionReport + paper_runner
- [mctrader-data](https://github.com/mclayer/mctrader-data) — collector + status CLI (cross-stack volume source)
- [mctrader-hub](https://github.com/mclayer/mctrader-hub) — governance / spec / plan / Story
- ADR-014 (control plane separation), ADR-016 (audit hash chain), ADR-033 (Docker-first infra)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "[MCT-101] docs(readme): full rewrite — v0.1.0 placeholder → v0.14.0

Docker deployment 절 (multi-service architecture + env reference table
+ audit DR PowerShell/bash recipes + WAL invariant + NFS 금지). Standalone
fallback 가이드. Operations 절. Development legacy 절 (non-Docker)."
```

---

### Task 2.15: `tests/integration/README.md` (manual smoke procedure)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-web/tests/integration/README.md`

(이미 `tests/integration/` directory 있음 — Task 2.0 step 1 의 ls 결과 확인 의무. 부재 시 `mkdir -p tests/integration` 추가.)

- [ ] **Step 1: Write smoke procedure README**

```markdown
# Integration smoke (manual) — MCT-101 Phase 4

mctrader-web Docker-first multi-service compose 의 manual integration smoke 절차.

## Prerequisites

- Docker + docker compose v2
- mctrader-data Pilot stack 가동 OR standalone smoke 시 `MCTRADER_DISABLE_DATA_STATUS=1`

## Smoke 1: 양 service healthy convergence

```bash
docker compose build
docker compose up -d

# Wait 90s
sleep 90

docker compose ps
# Expected: api + panel "Up X seconds (healthy)"
```

## Smoke 2: api /health endpoint

```bash
docker compose exec api python -c "
import urllib.request, sys
sys.exit(0 if urllib.request.urlopen('http://localhost:7821/health').status == 200 else 1)
"
echo $?  # Expected: 0
```

## Smoke 3: panel /_stcore/health endpoint

```bash
docker compose exec panel python -c "
import urllib.request, sys
sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status == 200 else 1)
"
echo $?  # Expected: 0
```

## Smoke 4: Cross-container HTTP (panel → api)

```bash
docker compose exec panel python -c "
import urllib.request
r = urllib.request.urlopen('http://api:7821/health')
print(f'status={r.status}, body={r.read().decode()}')
"
# Expected: status=200, body=... (no auth required for /health)
```

## Smoke 5: Volume invariant (admin_audit persistence)

```bash
# Trigger 1 audit row (admin login or any control op)
# (manual via Streamlit panel or curl)

# Down + up — volume 재마운트 검증
docker compose down
docker compose up -d
sleep 90

# Verify audit_log row 보존
docker compose exec api python -c "
import sqlite3
c = sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite')
n = c.execute('SELECT count(*) FROM audit_log').fetchone()[0]
print(f'audit_log rows: {n}')
"
# Expected: rows >= 1 (down/up 후에도 보존)

# Verify hash chain
docker compose exec api mctrader-cli audit-verify
# Expected: "OK seq=N (verified N rows)"
```

## Smoke 6: ADR-016 amendment §A1 backup

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# WAL checkpoint
docker compose exec api python -c "
import sqlite3
c = sqlite3.connect('/var/lib/mctrader/web/admin_audit.sqlite')
c.execute('PRAGMA wal_checkpoint(FULL)')
c.close()
"

# Tar backup
docker run --rm \
  -v mctrader-web_mctrader_web_data:/source:ro \
  -v "$(pwd):/backup" \
  alpine tar czf /backup/mctrader_web_audit_${TIMESTAMP}.tar.gz -C /source .

# Verify chain immediately
docker compose exec api mctrader-cli audit-verify
# Expected: "OK seq=N (verified N rows)"
```

## Smoke 7: ADR-016 amendment §A3 restore drill

```bash
# Take baseline backup
TIMESTAMP1=$(date +%Y%m%d_%H%M%S)
# (smoke 6 commands)

# Trigger more rows (further audit ops)

# Restore 시점
docker compose stop api
docker run --rm \
  -v mctrader-web_mctrader_web_data:/dest \
  -v "$(pwd):/backup" \
  alpine tar xzf /backup/mctrader_web_audit_${TIMESTAMP1}.tar.gz -C /dest
docker compose start api
sleep 60

# Re-verify chain after restore
docker compose exec api mctrader-cli audit-verify
# Expected: "OK seq=N (verified N rows)" — N = baseline 시점 row count
```

## Smoke 8: Cross-stack volume RO read (mctrader-data peer 가동 시)

```bash
# Verify external volume mounted RO on api
docker compose exec api ls -la /var/lib/mctrader/data/
# Expected: Pilot mctrader-data 가 쓴 OHLCV/tick/orderbook 디렉토리 표시

# Verify api can read but cannot write
docker compose exec api touch /var/lib/mctrader/data/test 2>&1 | grep -q "Read-only"
echo $?  # Expected: 0 (Read-only file system)

# status_adapter read 검증
docker compose exec api python -c "
from mctrader_web.dashboard.status_adapter import fetch_status
result = fetch_status('/var/lib/mctrader/data', use_cache=False)
print(f'worst_level={result.worst_level}, error={result.error}, nodes={len(result.nodes)}')
"
# Expected: worst_level=0~2 (live data) / error=None
```

## Smoke 9: Standalone fallback (mctrader-data peer 미가동)

```bash
# .env or compose env
echo "MCTRADER_DISABLE_DATA_STATUS=1" >> .env

# Down + up
docker compose down
docker compose up -d
sleep 90

# Verify mock yellow
docker compose exec api python -c "
from mctrader_web.dashboard.status_adapter import fetch_status
result = fetch_status('/var/lib/mctrader/data', use_cache=False)
print(f'worst_level={result.worst_level}, error={result.error}')
"
# Expected: worst_level=1 (yellow), error="data status disabled..."
```

## Smoke 10: SIGTERM graceful shutdown

```bash
# 양 service running 상태에서
docker compose stop  # SIGTERM → graceful
# Expected: 양 service 30s 안에 "Exited (0)"

# audit_log 마지막 row 정상 commit 확인
docker compose up -d
sleep 90
docker compose exec api mctrader-cli audit-verify
# Expected: "OK seq=N" — chain integrity 깨짐 없음
```

## Cleanup

```bash
docker compose down                            # volume 보존
docker compose down -v                         # volume 삭제 (DESTRUCTIVE — audit history 손실)
docker volume rm mctrader-web_mctrader_web_data  # 명시적 삭제
```
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/README.md
git commit -m "[MCT-101] docs(test): tests/integration/README.md (10 manual smoke)

Multi-service healthy convergence + cross-container HTTP + sqlite WAL +
hash chain backup-then-verify + restore drill + cross-stack volume RO
+ standalone fallback + SIGTERM graceful. ADR-016 amendment §A1-A3
smoke procedure 박제."
```

---

### Task 2.16: pyproject regression pytest

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: 모든 PASS (기존 + D6 9 시나리오 + D8 2 시나리오).

- [ ] **Step 2: ruff check**

```bash
uv run ruff check src/ tests/
```

Expected: 0 error.

- [ ] **Step 3: pyright (optional)**

```bash
uv run pyright src/
```

Expected: 0 error (existing baseline 정합).

- [ ] **Step 4: 만약 fail 시 fix-then-commit**

Step 1-3 중 하나라도 fail 시 root cause 진단 후 fix commit. 기존 회귀 0 보장.

---

### Task 2.17: Phase 2 PR push + Codex review + admin merge

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/MCT-101-docker-first
```

- [ ] **Step 2: Create Phase 2 PR (mctrader-web)**

```bash
gh pr create --repo mclayer/mctrader-web \
  --base main \
  --head feat/MCT-101-docker-first \
  --title "[MCT-101] feat: Docker-first multi-service containerization" \
  --body "$(cat <<'EOF'
## Summary

Phase 4 (mctrader-web sister) impl PR — multi-service compose (api + panel) Docker-first 전환.

### Major changes

- 신규 `Dockerfile` (2-stage python:3.12-slim, non-root mctrader UID 1001)
- 신규 `compose.yml` (2-service + named volume + external cross-stack volume + healthcheck per service)
- 신규 `.dockerignore` (D11 explicit list)
- 신규 `.github/workflows/image-lint.yml` (hadolint + compose config syntax)
- 신규 `tests/test_config_localhost_bind.py` (D6 TDD 9 시나리오)
- 신규 `tests/test_status_adapter_disable.py` (D8 TDD 2 시나리오)
- 신규 `tests/integration/README.md` (10 manual smoke)
- 신규 `CHANGELOG.md` (`[0.14.0]` BREAKING entry)

### Behavior changes

- D6 env override: `MCTRADER_API_HOST` + `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS` for compose-internal bind
- D8 standalone fallback: `MCTRADER_DISABLE_DATA_STATUS=1` → status_adapter mock yellow
- api_client env-aware default host/port (cross-container HTTP)
- `.claude/_overlay/project.yaml` `infra_strategy: docker_first`
- `pyproject.toml` 0.13.0 → 0.14.0
- `.gitignore` sqlite-wal/-shm exclusion

### Spec / Story / ADR reference

- Spec: mctrader-hub `docs/superpowers/specs/2026-05-08-mctrader-web-docker-design.md`
- Plan: mctrader-hub `docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md`
- Story: mctrader-hub#132 (MCT-101)
- ADR-016 amendment: mctrader-hub `docs/adr/ADR-016-audit-log-immutability.md` (Amendment 2026-05-08)

13 결정 (D1-D13) freeze + Codex agentId `a9897ebe62347932a` 의견 채택.

## Test plan

- [x] D6 TDD 9 시나리오 PASS
- [x] D8 TDD 2 시나리오 PASS
- [x] 기존 pytest 회귀 PASS
- [x] ruff check 0 error
- [x] hadolint Dockerfile 0 warning (local)
- [x] `docker compose config` syntax PASS (local)
- [x] `docker build` 성공 + image entrypoint smoke (local)
- [ ] image-lint workflow CI green
- [ ] phase-gate-mergeable green
- [ ] Codex 7-area review per phase + fix-back / defer
- [ ] manual integration smoke (10 항목, tests/integration/README.md)
- [ ] admin merge

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Codex 7-area review dispatch**

Use Agent({subagent_type: "codex:codex-rescue", ...}) — `phase_codex_review_loop` memory feedback 적용.

```
Review PR mclayer/mctrader-web PR #N (Phase 4 impl PR). 7-area:
1. Architecture/Boundary — multi-service compose pattern 정합성, ADR-014 single-process invariant 보존
2. Security/Threat — D6 TLS exempt env 의 보안 우회 가능성, host port 미노출 invariant
3. Test Contract — D6/D8 TDD coverage, manual smoke 절차 완성도
4. Data Migration / Schema — ADR-016 hash chain integrity Docker volume 정합
5. Operational Risk — restart/healthcheck/volume/network mode (Pilot ADR-033 §7.4)
6. Performance — image size, startup time, healthcheck interval
7. Refactor / Code Smell — env handling, fallback paths

Output: per-area finding (Severity Critical/High/Medium/Low) + accept/reject/defer.
```

- [ ] **Step 4: CI watch + fix-back loop**

Per `ci_failure_auto_recovery` + `ci_terminal_states_classify` + `no_background_watch` memory feedback. Foreground polling. Codex Critical/High = fix-back commit. CI green 후:

- [ ] **Step 5: Manual integration smoke 10 항목 실행 (tests/integration/README.md)**

각 smoke 결과 PR comment 박제 (Story §9 evidence).

- [ ] **Step 6: Admin merge**

Per `admin_merge_autonomy` memory feedback:

```bash
gh pr merge --repo mclayer/mctrader-web <PR-N> --admin --squash --delete-branch
```

---

## Phase 3 — Story §8.5/§9/§11 박제 + Epic body update

### Task 3.1: Story §8.5 Implementation Manifest commit

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-hub/docs/stories/MCT-101.md`

- [ ] **Step 1: Append §8.5 commit-by-commit manifest**

mctrader-web PR 의 commit list (admin merge 시 squash 되므로 squash commit hash + 사전 commit history):

```markdown
## 8.5 Implementation Manifest (mctrader-web PR #N, M commits)

| # | commit | 내용 |
|---|---|---|
| 1 | `<hash>` | D6 config.py env getter + validate_tls_for_host exempt + 9 TDD |
| 2 | `<hash>` | D6 cli.py env-aware host wiring |
| 3 | `<hash>` | D8 status_adapter MCTRADER_DISABLE_DATA_STATUS handler + 2 TDD |
| 4 | `<hash>` | (conditional) api_client env-aware default host/port |
| 5 | `<hash>` | .dockerignore D11 list |
| 6 | `<hash>` | Dockerfile 2-stage non-root |
| 7 | `<hash>` | compose.yml 2-service multi-service |
| 8 | `<hash>` | .claude/_overlay/project.yaml infra_strategy |
| 9 | `<hash>` | image-lint.yml workflow |
| 10 | `<hash>` | pyproject 0.13.0 → 0.14.0 + CHANGELOG |
| 11 | `<hash>` | .gitignore sqlite-wal/-shm |
| 12 | `<hash>` | README full rewrite |
| 13 | `<hash>` | tests/integration/README.md 10 smoke |
```

(squash merge 시 단일 commit hash 만 박제 + 위 manifest 가 PR description 기록 reference.)

- [ ] **Step 2: Commit**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" checkout -b docs/MCT-101-story-close
git -C "c:/workspace/mclayer/mctrader-hub" add docs/stories/MCT-101.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(story): §8.5 Implementation Manifest (impl PR commit list)"
```

---

### Task 3.2: Story §9 Evidence

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-hub/docs/stories/MCT-101.md`

- [ ] **Step 1: Append §9.1 + §9.2**

```markdown
## 9. Evidence

### 9.1 Phase 2 impl PR evidence (2026-05-DD)

- D6 config TDD 9 시나리오 PASS
- D8 status_adapter TDD 2 시나리오 PASS
- 기존 mctrader-web pytest 회귀 PASS (M tests)
- hadolint Dockerfile = warning 0
- `docker compose config` syntax PASS
- `docker build` 성공 + image entrypoint smoke (`mctrader-web-api` import OK)
- ruff check 0 error
- actionlint image-lint.yml clean
- mctrader-web PR #N admin merge YYYY-MM-DDTHH:MM:SSZ

### 9.2 Manual integration smoke (10 항목, tests/integration/README.md)

| # | Smoke | Result |
|---|---|---|
| 1 | 양 service healthy convergence (90s) | ✅ |
| 2 | api /health endpoint | ✅ |
| 3 | panel /_stcore/health endpoint | ✅ |
| 4 | Cross-container HTTP (panel → api) | ✅ |
| 5 | Volume invariant (audit_log persistence) | ✅ |
| 6 | ADR-016 §A1 backup recipe + verify | ✅ |
| 7 | ADR-016 §A3 restore drill + re-verify | ✅ |
| 8 | Cross-stack volume RO read (mctrader-data peer) | ✅ / ⏸ (조건부) |
| 9 | Standalone fallback (MCTRADER_DISABLE_DATA_STATUS=1) | ✅ |
| 10 | SIGTERM graceful shutdown | ✅ |
```

- [ ] **Step 2: Commit**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" add docs/stories/MCT-101.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(story): §9 Evidence (Phase 2 impl + 10 smoke)"
```

---

### Task 3.3: Story §11 회고 + Phase 3 reconciliation

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-hub/docs/stories/MCT-101.md`

- [ ] **Step 1: Append §11**

```markdown
## 11. 회고

### 11.1 Phase 4 성과 요약

- multi-service compose pattern (api + panel) novel 도입 — Pilot 1-service 와 차별
- ADR-014 single-process invariant 보존 — in-process asyncio.Task 패턴 (LifecycleManager / BacktestLifecycleManager / WfoLifecycleManager) 그대로
- D6 localhost-bind env override + D8 standalone fallback env — backward compat 100%
- ADR-016 amendment 단독 land (D12 γ) — Pilot ADR-009 §D12 추가 amend 0 (Phase 3 race 회피)
- 13 결정 (D1-D13) Codex agentId `a9897ebe62347932a` + Sonnet decider 채택률 100%

### 11.2 Phase 4 발견 + 처리

#### 11.2.1 ADR-002 D6 reference correction

Phase 4 entry session prompt 에 "sqlite (event store, ADR-002 D6)" 명시 → 코드 reading 후 mctrader-web 의 sqlite = ADR-016 audit_log + idempotency_cache (NOT ADR-002 D6 paper ledger). ADR-002 D6 = mctrader-engine repo 의 paper ledger. brainstorming 시점에 정정 → ADR amendment path 도 ADR-016 단독 (D12 γ) 으로 결정.

#### 11.2.2 TLS localhost vs Docker bind 충돌

config.py `validate_tls_for_host()` 가 non-localhost binding 시 TLS cert/key 의무. compose-internal `0.0.0.0` bind → TLS 부재 → 기존 invariant 위반. D6 채택 = env exempt path (`MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS=1`) + host port 미노출 의무. 보안 review 시 host port 0 확인 의무 — README + compose.yml 양 자산이 invariant 표현.

#### 11.2.3 Cross-stack volume namespacing

compose project name = directory name → mctrader-data Pilot stack 의 volume = `mctrader-data_mctrader_data`. mctrader-web compose 가 `external: true` reference. Pilot project name 변경 시 양 stack break — 본 invariant Story §9 evidence 박제 (`docker volume inspect mctrader-data_mctrader_data`).

### 11.3 Phase 3 (engine MCT-100) reconciliation 책임

Phase 3 + Phase 4 양쪽 PR merged 시점에 본 Story 가 마지막 merge 인 경우 reconciliation commit 의무:
- Epic mctrader-hub#120 body 의 Phase 3+4 status 동시 박제
- ADR-009 §D12 추가 amendment 충돌 0 검증 (본 Story = ADR-016 단독)
- memory file `project_dockerization_phase4.md` 의 Phase 3 surface 4 항목 — engine session 채택 여부 추적

### 11.4 Phase 5+ entry 조건

- Phase 5 (bithumb sister rollout): 이미 entry 조건 만족 (mctrader-market-bithumb PR #3 inline fix + smoke verified, Pilot Story §11.3 D4-revised 박제). 별도 Story.
- Phase 6 (Epic close): Phase 3 + 4 + 5 모두 done + EPIC-RESULTS-MCT-98 작성 시점.

### 11.5 Phase 4 carry-over (Out-of-scope)

- F1 mctrader-data CLI dep semver pinning — 별도 Story
- F2 audit-cron sidecar 자동화 — P6+ ops Story
- F3 TLS production cert 자동화 — 별도 ops Story
- F4 ghcr.io publish + multi-arch buildx — Pilot F1-F2 carry-over
- F5 webapp-minimal codeforge example update — codeforge 측 별도 Story
```

- [ ] **Step 2: Update frontmatter `status: complete`**

```yaml
---
story_key: MCT-101
story_issues:
  - repo: mclayer/mctrader-hub
    number: 132
status: complete
---
```

- [ ] **Step 3: Commit**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" add docs/stories/MCT-101.md
git -C "c:/workspace/mclayer/mctrader-hub" commit -m "[MCT-101] docs(story): §11 회고 + status complete

Phase 4 finding 3 항목 (ADR-002 D6 correction, TLS localhost, volume
namespacing) + Phase 3 reconciliation 책임 + Phase 5+ entry + Phase 4
carry-over 5 항목 박제."
```

---

### Task 3.4: Epic mctrader-hub#120 body update + reconciliation

- [ ] **Step 1: Read current Epic body**

```bash
gh issue view --repo mclayer/mctrader-hub 120 --json body --jq '.body' > /tmp/epic-body.md
```

- [ ] **Step 2: Update Phase 4 status (Phase 3 race 의무)**

만약 Phase 3 (MCT-100) 가 먼저 merged → Epic body 에 Phase 3 status 이미 update 됨. Phase 4 추가 update.

만약 Phase 4 가 마지막 merge → Phase 3+4 동시 reconciliation:

```markdown
- [x] Phase 3: mctrader-engine sister (MCT-100, mctrader-hub#131) — DONE 2026-05-DD
- [x] Phase 4: mctrader-web sister (MCT-101, mctrader-hub#132) — DONE 2026-05-DD
```

- [ ] **Step 3: Update Epic via gh issue edit**

```bash
gh issue edit --repo mclayer/mctrader-hub 120 --body-file /tmp/epic-body-updated.md
```

- [ ] **Step 4: Push Story close branch + create PR**

```bash
git -C "c:/workspace/mclayer/mctrader-hub" push -u origin docs/MCT-101-story-close

gh pr create --repo mclayer/mctrader-hub \
  --base main \
  --head docs/MCT-101-story-close \
  --title "[MCT-101] docs: P4 story close + §8.5 + §9 + §11 + Epic body" \
  --body "..."
```

- [ ] **Step 5: CI watch + admin merge**

```bash
gh pr merge --repo mclayer/mctrader-hub <PR-N> --admin --squash --delete-branch
```

- [ ] **Step 6: Close Story issue**

```bash
gh issue close --repo mclayer/mctrader-hub 132 --comment "Phase 4 DONE. mctrader-web Docker-first multi-service deployment merged. Story §11 회고 박제. Epic mctrader-hub#120 body Phase 4 status updated."
```

---

## Self-review

### Spec coverage check

각 spec section / requirement 가 plan task 에 매핑:

| Spec section | Plan task |
|---|---|
| §3.2 신규 Dockerfile | Task 2.7 |
| §3.2 신규 compose.yml | Task 2.8 |
| §3.2 신규 .dockerignore | Task 2.6 |
| §3.2 신규 image-lint.yml | Task 2.11 |
| §3.2 신규 CHANGELOG.md | Task 2.12 |
| §3.2 신규 tests/integration/README.md | Task 2.15 |
| §3.2 신규 test_config_localhost_bind.py | Task 2.1 + 2.2 + 2.3 |
| §3.2 신규 test_status_adapter_disable.py | Task 2.5 |
| §3.2 수정 config.py | Task 2.1 + 2.2 + 2.3 |
| §3.2 수정 cli.py | Task 2.4 |
| §3.2 수정 status_adapter.py | Task 2.5 |
| §3.2 수정 project.yaml | Task 2.10 |
| §3.2 수정 README.md | Task 2.14 |
| §3.2 수정 pyproject.toml | Task 2.12 |
| §3.2 수정 .gitignore | Task 2.13 |
| §3.2 수정 ADR-016 (mctrader-hub side) | Task 1.2 |
| §11 다음 단계 1-7 | Task 1.1-3.4 |
| Acceptance Criteria 14 항목 | 분산 across all tasks |

**Gap**: api_client/client.py env-aware host/port (Task 2.9) 가 spec §4 의 신규 env "MCTRADER_API_HOST_FOR_CLIENT / MCTRADER_API_PORT_FOR_CLIENT" 와 매핑 — 추가됨. spec §4 의 env table 도 업데이트 의무 (이미 spec 에 박제됨? 확인). 

→ Spec §4 Env table 에 MCTRADER_API_HOST_FOR_CLIENT / MCTRADER_API_PORT_FOR_CLIENT 미명시 발견. spec patch 또는 plan amendment 의무 — Task 2.9 이 conditional 이므로 grep 결과에 따라 결정.

### Placeholder scan

- "TBD" / "TODO" / "implement later" — 0건
- "Add appropriate error handling" / "handle edge cases" — 0건
- "Similar to Task N" — 0건 (모든 task code 직접 표기)
- 빈 step — 0건
- `<hash>` placeholder = §8.5 Implementation Manifest 에서 squash merge 후 채워질 commit hash (의도적 placeholder, Task 3.1 step 시 채움)
- `<TIMESTAMP>` 도 사용자 input 예시 (의도적)
- `<PR-N>` = PR number placeholder, gh CLI 실행 후 채움 (의도적)
- `<hash>` / `<PR-N>` / `<TIMESTAMP>` 외 placeholder 0

### Type consistency

- `get_api_host()` / `is_non_localhost_no_tls_allowed()` / `validate_tls_for_host()` — config.py 전반 일관
- `StatusResult(worst_level, nodes, error, fetched_at)` — status_adapter.py 와 test 일관
- `MctraderApiClient(host=..., port=..., token_path=...)` — api_client/client.py 와 panel 호출 일관
- env naming: `MCTRADER_*` prefix 통일 (`MCTRADER_API_HOST` / `MCTRADER_ALLOW_NON_LOCALHOST_NO_TLS` / `MCTRADER_TOKEN_PATH` / `MCTRADER_ADMIN_AUDIT_PATH` / `MCTRADER_LOCK_PATH` / `MCTRADER_ADMIN_TOKEN_SECRET` / `MCTRADER_ADMIN_CORS_ORIGINS` / `MCTRADER_DISABLE_DATA_STATUS` / `MCTRADER_API_HOST_FOR_CLIENT` / `MCTRADER_API_PORT_FOR_CLIENT`)
- branch name consistency — `docs/MCT-101-web-docker` / `feat/MCT-101-docker-first` / `docs/MCT-101-story-close`

### Spec patch 의무 (gap fix)

Task 2.9 conditional 이지만 만약 wiring 의무 시 spec §4 env table 갱신 필요. 본 plan task 추가:

### Task 1.5 (conditional): Spec §4 env table 갱신

Task 2.9 wiring 의무 결정 후 spec patch:

```markdown
| `MCTRADER_API_HOST_FOR_CLIENT` | `127.0.0.1` | api_client default host. compose 시 service name `api`. |
| `MCTRADER_API_PORT_FOR_CLIENT` | `7821` | api_client default port. |
```

commit 으로 spec amendment.

---

## Plan complete

Plan saved to `c:/workspace/mclayer/mctrader-hub/docs/superpowers/plans/2026-05-08-mctrader-web-docker-plan.md`.

**Total tasks**: 22 (Phase 1: 5 + Phase 2: 17 + Phase 3: 4)
**Estimated commits**: ~20 (excluding squash merges)
**Estimated PR count**: 3 (Phase 1 doc PR + Phase 2 impl PR + Phase 3 story-close PR)

**Execution mode** (next step):
- Subagent-Driven (recommended) — fresh subagent per task, two-stage review
- Inline Execution — batch with checkpoints
