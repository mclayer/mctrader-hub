---
adr_id: ADR-019
title: Parallel agent isolation — git worktree + Python/editable bootstrap contract
status: Accepted
date: 2026-05-09
related_story: MCT-110 (trigger)
category: Infrastructure
---

# ADR-019: Parallel agent isolation — git worktree + Python/editable bootstrap contract

## Status

Accepted — 2026-05-09. MCT-110 trigger. MCT-100/101/102 (2026-05-08) 재발 이력 포함.

## Context

2026-05-08 MCT-100/101/102 세 스토리와 2026-05-09 MCT-110에서 동일한 silent failure
mode가 반복 발생하였다. 각 사건은 독립적으로 보였으나 공통된 근본 원인 4개를 공유한다.

### 재발 이력

| 날짜 | 스토리 | 실패 모드 |
|---|---|---|
| 2026-05-08 | MCT-100 | 병렬 에이전트 `git checkout` race → test 오염 |
| 2026-05-08 | MCT-101 | 동일 working tree 공유 → stale branch 커밋 |
| 2026-05-08 | MCT-102 | untracked test file이 다른 branch pytest에 노출 |
| 2026-05-09 | MCT-110 | venv stale wheel + python 버전 불일치 → 신규 코드 미반영 |

### 근본 원인 분석

**C1. Git working tree 공유 (branch switch race)**
복수의 에이전트가 동일 `git` working directory에서 병렬 실행될 때, 에이전트 A의
`git checkout feat/foo` 직후 에이전트 B가 `git checkout feat/bar`를 실행하면
에이전트 A가 읽는 파일 시스템 상태가 feat/bar 기준으로 변경된다.
MEMORY `feedback_parallel_session_branch_race.md` (2026-05-08)가 최초 기록.

**C2. Untracked 파일 오염 (branch 경계 미존재)**
untracked/unstaged 파일은 `git checkout`이 삭제하지 않는다. 에이전트 A가
feat/foo에서 생성한 test fixture가 feat/bar의 pytest에 그대로 노출된다.
mctrader-engine, mctrader-data 양쪽에서 확인.

**C3. Python 버전 mismatch (`python` vs `py -3.12`)**
시스템 default `python` = 3.14 (Windows PATH 우선). `pyproject.toml`은
`requires-python = ">=3.11,<3.13"` 제약이지만 bare `python` 명령은 3.14를 실행해
`uv` / `venv` 활성화가 자동으로 실패하거나 잘못된 인터프리터를 사용한다.

**C4. Non-editable wheel stale (editable install 미실행)**
`pip install .` (비 editable)로 설치된 wheel이 venv에 남아있으면 소스 변경이
반영되지 않는다. mctrader-engine, mctrader-data 코드 수정 후 pytest가 구버전
동작을 검증하는 silent pass 현상이 MCT-110에서 확인되었다.

## Decision

### D1. git worktree 의무 (parallel agent)

**정책**: 2+ 에이전트가 동일 repository working directory를 동시에 사용하는 경우
반드시 `git worktree`로 격리한다. Orchestrator-level 의무이며 에이전트별
선택사항이 아니다.

**Worktree 생성 / 사용 / 정리 시퀀스**:

```powershell
# 1. Worktree 생성 (branch가 이미 존재하는 경우)
git worktree add .worktrees/feat-foo origin/feat/foo

# 1b. 신규 branch와 함께 생성
git worktree add -b feat/bar .worktrees/feat-bar main

# 2. 에이전트는 worktree 경로를 절대 경로로 사용
#    예: C:\workspace\mclayer\mctrader-hub\.worktrees\feat-foo
Set-Location "C:\workspace\mclayer\mctrader-hub\.worktrees\feat-foo"
# ... 작업 수행 ...

# 3. 완료 후 즉시 정리
git worktree remove .worktrees/feat-foo
# 강제 제거 필요 시 (수정사항 없는 경우):
git worktree remove --force .worktrees/feat-foo

# 4. 고아 worktree 확인 및 일괄 정리
git worktree list
git worktree prune
```

**Worktree 생성 규칙**:
- worktree 경로: `.worktrees/<branch-name-sanitized>` (슬래시는 하이픈 치환)
  - 예: `feat/foo` → `.worktrees/feat-foo`
- `.worktrees/` 디렉토리는 `.gitignore`에 등록 (각 repo)
- worktree 내 Python venv는 worktree 로컬 (`.worktrees/<name>/.venv`) — 주 repo venv와 독립

**단일 에이전트 순차 실행** 시에는 worktree 불필요. 단, D4 branch 검증 guard를
대신 적용한다.

### D2. Python 버전 부트스트랩 contract

**정책**: 모든 에이전트 Preflight에서 Python 버전을 명시적으로 검증하고,
bare `python` 명령을 금지한다.

**Preflight 명령 (Windows — PowerShell)**:

```powershell
# 1. Python 3.12 존재 확인
py -3.12 --version
# 기대 출력: Python 3.12.x
# 실패 시: py -3.12 not found → 에이전트 abort, 사용자에게 보고

# 2. venv 생성 (없는 경우)
py -3.12 -m venv .venv

# 3. venv 활성화
.venv\Scripts\Activate.ps1

# 4. 올바른 인터프리터 검증
python --version   # venv 활성화 후에만 허용
py -3.12 --version # venv 없는 컨텍스트에서 사용
```

**pytest 실행 표준**:

```powershell
# 명시적 인터프리터 지정 (venv 활성화 없이도 안전)
py -3.12 -m pytest tests/ -v

# venv 활성화 후 실행 (D3 editable install 완료 후)
.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

**금지 패턴**:
- `python pytest` (모듈 모드 미사용)
- bare `python` (venv 활성화 전)
- `python3` (Windows에서 미보장)

**6 repo 공통 pyproject.toml SSOT**:

```toml
[project]
requires-python = ">=3.11,<3.13"
```

6개 repo (mctrader-hub, mctrader-market, mctrader-market-bithumb, mctrader-data,
mctrader-engine, mctrader-web) 모두 동일 제약 적용. 이탈 시 PR CI 에서 `pyright`
Python version gate가 경고.

### D3. Editable install Preflight

**정책**: 모든 에이전트 Preflight에서 `pip install -e .`를 항상 실행한다.
idempotent이므로 무해하며, stale wheel 문제를 원천 차단한다.

**Preflight 명령**:

```powershell
# venv 활성화 후 editable install (항상 실행)
.venv\Scripts\Activate.ps1
py -3.12 -m pip install -e . --quiet

# 의존성 포함 전체 설치 (신규 venv 또는 pyproject.toml 변경 후)
py -3.12 -m pip install -e ".[dev]" --quiet

# 설치 확인
py -3.12 -m pip show <package-name>
# 기대: Location = <worktree 또는 repo 경로> (site-packages X)
```

**stale wheel 감지 (사후 확인)**:

```powershell
# editable 여부 확인 — "Editable project location" 항목이 있어야 함
py -3.12 -m pip show mctrader-engine | Select-String "Editable"
```

**적용 대상**: mctrader-engine, mctrader-data (MCT-110 확인), 예방적으로 6 repo
전체 의무화. worktree별 독립 venv에서 각각 실행.

### D4. Branch 검증 guard (fallback — worktree 미사용 시)

**정책**: worktree를 사용하지 않고 단일 working tree에서 에이전트가 작업할 때,
모든 커밋 직전에 현재 branch를 검증하고 불일치 시 즉시 abort한다.

**커밋 직전 guard 명령**:

```powershell
# 현재 branch 확인
$currentBranch = git branch --show-current
$expectedBranch = "feat/foo"   # 에이전트 초기화 시점에 기록한 branch명

if ($currentBranch -ne $expectedBranch) {
    Write-Error "BRANCH MISMATCH: expected=$expectedBranch, current=$currentBranch — aborting commit"
    exit 1
}

# 검증 통과 후 커밋
git add <files>
git commit -m "..."
```

**적용 시점**: `git commit` / `git push` 직전 매번 실행. `git add` 후에도 확인.

**MEMORY 선례**: `feedback_parallel_session_branch_race.md` (2026-05-08) —
병렬 세션이 동일 hub working dir를 공유할 때 branch switch race 발생 기록.
D1 worktree가 근본 해결, D4는 단일 에이전트 세션의 안전망.

### D5. 6 repo 적용 범위

| Repo | D1 worktree | D2 Python 검증 | D3 Editable | D4 Branch guard |
|---|---|---|---|---|
| mctrader-hub | 의무 | 의무 | N/A (코드 없음) | 의무 |
| mctrader-market | 의무 | 의무 | 의무 | 의무 |
| mctrader-market-bithumb | 의무 | 의무 | 의무 | 의무 |
| mctrader-data | 의무 | 의무 | **HIGH** (MCT-110 확인) | 의무 |
| mctrader-engine | 의무 | 의무 | **HIGH** (MCT-110 확인) | 의무 |
| mctrader-web | 의무 | 의무 | 의무 | 의무 |

**mctrader-data, mctrader-engine**: MCT-110에서 stale wheel 문제가 직접 확인되어
D3 우선순위 HIGH.

**Preflight 전체 시퀀스 (6 repo 표준)**:

```powershell
# === Agent Preflight Checklist ===

# Step 1: Python 버전 검증 (D2)
py -3.12 --version

# Step 2: Worktree 생성 (D1) — 병렬 에이전트인 경우
git worktree add .worktrees/feat-foo origin/feat/foo

# Step 3: Worktree 경로로 이동
Set-Location "C:\workspace\mclayer\<repo>\.worktrees\feat-foo"

# Step 4: Venv 생성 및 활성화
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Step 5: Editable install (D3)
py -3.12 -m pip install -e ".[dev]" --quiet

# Step 6: Branch 검증 (D4) — 단일 에이전트인 경우
$currentBranch = git branch --show-current
# ... guard logic ...

# === 이후 작업 수행 ===
py -3.12 -m pytest tests/ -v

# === Cleanup ===
deactivate
Set-Location "C:\workspace\mclayer\<repo>"
git worktree remove .worktrees/feat-foo
```

## Alternatives Considered

### A1. Branch 검증만으로 충분 (D4 only, worktree 미사용)

**기각 사유**:
- `git branch --show-current` 검증은 커밋 직전만 보호. 에이전트 실행 중간
  다른 에이전트의 `git checkout`이 파일 시스템을 변경하는 것을 막지 못함.
- untracked 파일 오염 (C2)은 branch 검증으로 탐지 불가. 다른 에이전트가
  생성한 test fixture가 현재 branch pytest에 노출되는 문제는 branch guard
  통과 후에도 발생.
- MCT-100/101/102 세 사건 모두 "branch는 맞는데 파일이 오염된" 케이스.
  근본 격리(worktree 물리적 분리)만이 해결책.

### A2. Sequential execution (병렬 실행 금지)

**기각 사유**:
- 병렬 에이전트는 독립적인 repo/branch 작업 시 유효한 속도 향상 수단.
  MCT-107~111 (5 repo 병렬 code-review)이 대표 사례.
- 병렬 금지는 과도한 제약. worktree로 격리하면 병렬성을 유지하면서
  안전 보장 가능.

### A3. Docker container per agent

**기각 사유**:
- 컨테이너 스핀업 오버헤드 (수십 초) + volume mount 설정 복잡도.
- git worktree는 초 단위 생성, 동일 host에서 filesystem 공유,
  git object store 공유로 디스크 효율적. 단계에 맞는 해결책.

### A4. `pyenv` / `asdf` 자동 버전 전환

**기각 사유**:
- Windows 환경에서 `pyenv-win` 지원이 불완전. `py` launcher (PEP 514)가
  Windows 표준 솔루션.
- 6 repo 모두 `py -3.12` 명시 패턴으로 통일하면 별도 도구 없이 일관성 확보.

### A5. Editable install을 CI에서만 강제

**기각 사유**:
- MCT-110의 stale wheel 문제는 에이전트 로컬 실행 중 발생. CI pass ≠
  로컬 에이전트 pass. 에이전트 Preflight에 포함해야 silent pass 방지.
- idempotent이므로 매번 실행해도 추가 비용 미미 (이미 설치된 경우 <1초).

## Consequences

### C1. Parallel agent 실행 안전성 확보

git worktree로 branch별 독립 파일 시스템 보장. 에이전트 A의 파일 변경이
에이전트 B의 working tree에 영향을 주지 않음. untracked 파일 오염 원천 차단.

### C2. Python 환경 결정론 확보

`py -3.12` 명시로 시스템 default Python 버전에 관계없이 동일 인터프리터
사용 보장. `pyproject.toml` 제약과 실행 인터프리터 일치.

### C3. Code-change 반영 보장

`pip install -e .` Preflight로 소스 변경이 즉시 pytest에 반영됨.
stale wheel에 의한 silent pass 제거.

### C4. 정정 비용 절감 추정

재발 이력 4건 (MCT-100/101/102/110)의 평균 정정 비용: ~2h/건 (branch 복구 +
overkill 재실행). 본 ADR 적용 후:
- **정정 비용 ~10% → ~5% 절감 추정** (parallel agent 작업 기준 session 당)
- worktree 생성/정리 오버헤드: ~5초 (net 양수)
- D3 editable install 오버헤드: <1초 (이미 설치된 경우)

### C5. .worktrees/ gitignore 필요

6 repo 각각 `.gitignore`에 `.worktrees/` 추가 필요. 미추가 시 worktree
메타데이터가 git status에 노출. 별도 PR로 처리.

### C6. Worktree 고아 관리

에이전트 crash 시 `.worktrees/` 하위 디렉토리가 잔류. 정기적으로
`git worktree prune`을 실행하거나, 에이전트 Preflight에 prune 포함 권장.

```powershell
# 세션 시작 시 고아 worktree 정리
git worktree prune
git worktree list
```

### C7. 단일 에이전트 세션은 영향 미미

순차 실행 단일 에이전트는 D1 불필요. D2/D3/D4만 적용. 현행 대비 Preflight
30초 미만 추가.

## Cross-references

- MEMORY: `feedback_parallel_session_branch_race.md` (2026-05-08) — D4 선례
- ADR-010 (Python install — uv + 3.11/3.12 표준)
- ADR-011 (branch protection CI — required status checks)
- MCT-100, MCT-101, MCT-102 (2026-05-08 — parallel agent branch race 최초 확인)
- MCT-110 (2026-05-09 — stale wheel + Python 버전 불일치 재발, 본 ADR trigger)
- [git-worktree documentation](https://git-scm.com/docs/git-worktree)
- [PEP 514 — Python registration in the Windows registry](https://peps.python.org/pep-0514/)
