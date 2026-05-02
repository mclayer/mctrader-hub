---
story_key: MCT-11
status: phase:요구사항
component: hub
type: brainstorm
related_adr: ADR-011
---

# MCT-11: Branch protection + CI trigger 표준 (6 repo)

## 1. 사용자 요구사항 (verbatim)

mctrader 의 branch protection + CI trigger 표준 (6 repo). Codeforge 데뷔 F5 finding (#122) solo-dev branch protection deadlock mitigation.

## 2. 도메인 해석

ADR-002 / ADR-009 / ADR-010 + ADR-008 D5 (live CI block) + F5 (#122). \"보호 유지하되 solo-dev 단계 deadlock 회피\". CODEOWNERS = 책임 지도 (미래) / branch protection = required CI 중심.

## 3. 관련 ADR

- ADR-011 ([`../adr/ADR-011-branch-protection-ci.md`](../adr/ADR-011-branch-protection-ci.md))
- baseline: ADR-002 / ADR-008 / ADR-009 / ADR-010 / F5 (#122)

## 4. 관련 코드 경로

각 repo:
```
.github/
├── workflows/
│   ├── ci.yml              # pull_request + push + schedule + workflow_dispatch
│   ├── phase-gate-mergeable.yml
│   ├── phase-label-invariant.yml
│   ├── release.yml         # tag-based
│   └── dependabot.yml
├── ISSUE_TEMPLATE/
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS
└── dependabot.yml
.pre-commit-config.yaml
```

## 5-6. 요구사항 / 외부 지식

GitHub branch protection settings + Conventional Commits + ruff + pyright + gitleaks + Dependabot.

## 7. 설계 서사 (요약)

### 7.1 Solo-dev 호환 branch protection (F5 mitigation)

`main` 보호 6 repo 공통:

| Setting | Value | 근거 |
|---|---|---|
| Pull request required | `true` | merge 흐름 보존 |
| Required approvals | **`0`** (solo-dev) | F5 mitigation. self-approve 불가 → deadlock 회피. Bot maintainer 또는 외부 collaborator 등장 시 `1` 로 상향 |
| Require CODEOWNERS review | **`false`** | F5 mitigation. CODEOWNERS = 문서 / 미래 책임 지도, hard gate 아님 |
| Dismiss stale approvals | `true` | head sha 변경 시 신규 approval 의무 |
| Require approval of most recent reviewable push | `true` | force push gaming 방지 |
| Require conversation resolution | `true` | 미해결 review thread 차단 |
| Require status checks | `true` | required CI 중심 보호 |
| Require branches up to date | `true` | merge 시점 main 동기화 |
| Require linear history | `true` | merge commit 히스토리 잡음 회피 |
| Allow force pushes | `false` | |
| Allow deletions | `false` | |
| Require signed commits | `false` (recommended) | Dependabot / automation friction 회피 |
| Include administrators | `false` (admin override 허용) | F5 emergency mitigation 보존 |
| Lock branch | `false` | |

**F5 finding 의 핵심 mitigation = `Require CODEOWNERS review = false` + `Required approvals = 0`**. CI gate 가 인간 review 의 빈자리 보완.

### 7.2 Required status checks (5)

| Check | 도구 | 근거 |
|---|---|---|
| `phase-gate-mergeable` | codeforge plugin | ADR / contract / repo invariant policy |
| `lint` | `ruff check` + `ruff format --check` | 코드 스타일 + obvious bug |
| `type` | `pyright` | static 안전성 |
| `test` | `pytest` (default-safe subset) | unit + integration (live path 차단 검증 포함) |
| `coverage` | `pytest-cov` | line coverage 60% baseline OR -2pp drop guard |

**Live test 정책 (ADR-008 D5)**: \"환경변수 없으니 skip\" = 보호 아님. **\"live path 차단을 assertion 으로 검증\"** = 보호. CI default = `MCTRADER_ALLOW_LIVE_TEST` 미설정 → live runner.start() 호출 시 즉시 fail 검증.

### 7.3 CI trigger 표준 (4)

| Trigger | 책임 | 비용 |
|---|---|---|
| `pull_request` | required heavy matrix (5 checks 모두) | 높음, merge 의사결정 |
| `push` | fast path (lint/type/unit) + `main` push 만 full | 낮음 |
| `schedule` | weekly compat (3.12) + slow integration + dependency freshness + contract drift + security scan | non-blocking signal |
| `workflow_dispatch` | manual 재검증 / pre-release 점검 | minimal input (`full=true` / `compat=true` / `coverage_strict=true`) |

`schedule`: 주 1회 (일/월 새벽 KST). 실패 = maintenance signal 만.

### 7.4 Cross-repo CI 정책

**기본 = 도입 안 함**. Repo-local CI required + Cross-repo 는 contract pin + scheduled compatibility 로 대체.

근거:
- 6 repo 개인 운영에서 `workflow_run` / `repository_dispatch` 깊은 연결 = 장애 지점 폭증
- ADR-009 Candle Protocol = repo 경계의 contract → 각 repo CI 가 pinned contract schema fixture 검증

도입 trigger (별도 ADR 필요):
- 공용 contract repo 또는 release artifact 안정화
- repository_dispatch token 관리 문서화
- 실패 알림 소유자 명확화
- required check 로 걸기 전 최소 2주 non-blocking 운영

### 7.5 Pre-commit standard

`.pre-commit-config.yaml` 표준 hooks:
- `ruff check --fix` + `ruff format`
- `pyright` 또는 lightweight type check
- `gitleaks` (mctrader = credential risk, 의무)
- File hygiene: trailing-whitespace / end-of-file-fixer / check-yaml / check-toml
- `uv lock --check` 또는 `uv sync --frozen` 검증

**gitleaks = pre-commit + CI 양쪽 의무** (ADR-008 D9 align).
- pre-commit = staged diff fast scan
- CI = full repo scan

### 7.6 Dependabot 정책

| Update type | Auto-merge | 근거 |
|---|---|---|
| patch (dev + runtime) | ✓ CI green | 안전성 높음 |
| security patch | ✓ CI green | 우선 처리 (단 runtime 핵심 라이브러리는 manual 확인) |
| minor (dev) | ✓ CI green | dev only impact |
| minor (runtime) | ✗ manual | trading engine breaking risk |
| major | ✗ manual | breaking 가능성 |
| lockfile-only | ✓ CI green | dependency 명시 변경 없음 |

Auto-merge 조건: required green + no requested changes + no unresolved conversations + `automerge` 라벨 또는 Dependabot patch/security PR.

### 7.7 Release CI (tag-based)

`vX.Y.Z` tag push → release workflow:

1. `uv sync --frozen`
2. lint / type / test / coverage 재실행
3. contract validation (ADR-009 Candle Protocol schema check)
4. package build (또는 artifact build)
5. SBOM 또는 dependency manifest 생성
6. GitHub Release draft 또는 publish
7. Provenance / signing (가능 시 첨부)

**Release branch 미사용** (개인 플랫폼). `main` = always releasable. 의사결정 = annotated/signed tag.

**Live deploy = 본 ADR scope 외 별도 ADR**. `tag → production` 직결 = 위험. GitHub environment protection 추가 의무.

### 7.8 Branch naming convention

| Prefix | 용도 |
|---|---|
| `feat/` | 신규 기능 (e.g. `feat/mct-11-ci-standard`) |
| `fix/` | 버그 수정 |
| `chore/` | 인프라 / dependency / 잡일 |
| `docs/` | 문서 |
| `hotfix/` | 긴급 수정 |
| (미사용) `release/` | 개인 플랫폼 = `main` 항상 releasable |

### 7.9 PR template

```md
## 변경 요약

## 관련 ADR / MCT

## 테스트 결과
- [ ] required CI green

## Live path 영향
- [ ] 영향 없음 / 있음 (상세)

## Contract / schema 영향
- [ ] ADR-009 Candle Protocol schema 변경 없음 / 있음

## Release 영향
- [ ] 일반 PR / Release tag 필요
```

### 7.10 Commit message

Conventional Commits 권장 (hard gate 아님).

```
feat: add phase gate check
fix: block live tests by default
ci: add uv frozen sync
docs: adr-011 branch protection
chore: dependabot uv.lock update
```

### 7.11 CODEOWNERS schema (per repo, 책임 지도)

| Repo | 책임 area |
|---|---|
| mctrader-hub | ADR / repo orchestration / governance / phase gate |
| mctrader-market | exchange-neutral market interface / Candle Protocol |
| mctrader-market-bithumb | Bithumb adapter / credentials boundary / dry-run guard |
| mctrader-data | Candle storage / schema / ingestion |
| mctrader-engine | strategy / simulation / execution planning |
| mctrader-web | UI / dashboard / API client boundary |

현재 single owner (`@mccho8865`). 미래 팀 확장 시 책임 area 별 분리.

### 7.12 Bot account 도입 trigger (향후)

CI gate 가 빈자리 보완 — Bot account 비용 (계정 보안 / token rotation / 감사) 합리적 시점:
1. 외부 contributor PR 정기 수신
2. Auto-merge 범위 확대
3. Release automation 이 production deploy 직결
4. CODEOWNERS review 가 실제 책임 분리 기능

### 7.13 Codex 적용

채택률 22/22.

## 8-11

(Phase 2 N/A — doc-only Story.)
