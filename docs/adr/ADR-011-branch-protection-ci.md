---
adr_id: ADR-011
title: Branch protection + CI trigger 표준 (6 repo, solo-dev F5 mitigation)
status: Accepted
date: 2026-05-02
related_story: MCT-11
category: hub
---

# ADR-011: Branch protection + CI trigger + Pre-commit + Dependabot + Release

## Status

Accepted — 2026-05-02. MCT-11 Phase 1 PR.

## Context

ADR-002 / ADR-008 D5 / ADR-009 / ADR-010 + 데뷔 F5 finding (#122). Solo-dev 단계 branch protection deadlock 회피 + required CI 중심 보호.

## Decision

### D1. `main` branch protection (6 repo 공통)

| Setting | Value |
|---|---|
| PR required | `true` |
| Required approvals | **`0`** (solo-dev) |
| Require CODEOWNERS review | **`false`** (F5) |
| Dismiss stale approvals | `true` |
| Require approval of most recent push | `true` |
| Require conversation resolution | `true` |
| Require status checks | `true` |
| Require branches up to date | `true` |
| Require linear history | `true` |
| Allow force pushes | `false` |
| Allow deletions | `false` |
| Require signed commits | `false` (recommended) |
| Include administrators | `false` (admin override 허용) |
| Lock branch | `false` |

**F5 mitigation 핵심**: required approvals = 0 + CODEOWNERS review false. CI gate 가 빈자리 보완.

### D2. Required status checks (5)

| Check | 도구 | Default value |
|---|---|---|
| phase-gate-mergeable | codeforge plugin | required |
| lint | `ruff check + ruff format --check` | required |
| type | `pyright` | required |
| test | `pytest` (default-safe subset, live path = guard assertion) | required |
| coverage | `pytest-cov` | line 60% OR baseline -2pp drop guard |

Compat lane (Python 3.12) = non-blocking until 안정화.

### D3. CI trigger 표준 (4)

| Trigger | 책임 |
|---|---|
| pull_request | required heavy matrix (5 checks) |
| push | fast (lint/type/unit), `main` = full |
| schedule (weekly KST 새벽) | compat 3.12 + slow integration + dep freshness + contract drift + security scan, non-blocking |
| workflow_dispatch | manual 재검증 / pre-release |

### D4. Live CI policy

ADR-008 D5 align. `MCTRADER_ALLOW_LIVE_TEST` 미설정 default = live runner.start() / SecretProvider.load_live_credentials() 호출 시 즉시 fail. **\"skip 이 아닌 guard assertion\"**.

### D5. Cross-repo CI 미도입 (default)

Repo-local CI + contract pin + scheduled compat 으로 대체. 6 repo workflow_run / repository_dispatch 깊은 연결 = 장애 지점 폭증.

도입 trigger (별도 ADR): 공용 contract release / token 관리 문서화 / 실패 알림 소유자 / 2주+ non-blocking 운영.

### D6. Pre-commit standard (`.pre-commit-config.yaml`)

```yaml
- ruff check --fix
- ruff format
- pyright (lightweight)
- gitleaks (의무 — credential risk)
- file hygiene: trailing-whitespace / end-of-file-fixer / check-yaml / check-toml
- uv lock --check or uv sync --frozen
```

gitleaks = pre-commit (staged diff fast) + CI (full repo) 양쪽 의무.

### D7. Dependabot policy

| Update | Auto-merge |
|---|---|
| patch (dev + runtime) | ✓ CI green |
| security patch | ✓ CI green (runtime 핵심 = manual 확인) |
| minor dev | ✓ CI green |
| minor runtime | ✗ manual |
| major | ✗ manual |
| lockfile-only | ✓ CI green |

Auto-merge 조건: required green + no requested changes + no unresolved + `automerge` label 또는 Dependabot patch/security PR.

### D8. Release CI (tag-based)

`vX.Y.Z` tag push:
1. uv sync --frozen
2. lint / type / test / coverage 재실행
3. ADR-009 Candle Protocol contract validation
4. Package / artifact build
5. SBOM / dependency manifest
6. GitHub Release draft 또는 publish
7. Provenance / signing (가능 시)

Release branch 미사용. `main` = always releasable. **Live deploy = 별도 ADR** (production environment protection 의무).

### D9. Branch naming + PR template + Commit message

Branch: `feat/ fix/ chore/ docs/ hotfix/`. `release/` 미사용.

PR template (강제 가능 항목만):
- 변경 요약
- 관련 ADR / MCT
- 테스트 결과
- Live path 영향
- Contract / schema 영향
- Release 영향

Commit message: Conventional Commits 권장 (hard gate 아님). `feat: / fix: / ci: / chore: / docs:`.

### D10. CODEOWNERS schema (per repo, 책임 지도)

| Repo | 책임 |
|---|---|
| mctrader-hub | ADR / governance / phase gate |
| mctrader-market | exchange-neutral / Candle Protocol |
| mctrader-market-bithumb | Bithumb adapter / credentials |
| mctrader-data | storage / schema / ingestion |
| mctrader-engine | strategy / simulation / execution |
| mctrader-web | UI / dashboard / API client |

Single owner 단계. 팀 확장 시 area 별 분리.

### D11. Bot account 미도입 (현재 단계)

CI gate 가 빈자리 보완. Bot account 비용 (계정 보안 / token / 감사) 합리적 시점 = 외부 contributor / Auto-merge 범위 확대 / Release production 직결 / CODEOWNERS 실제 책임 분리.

## Alternatives Considered

### A1. Required approvals = 1 (CODEOWNERS review = true)
- **기각**: F5 deadlock. solo-dev = self-approve 불가 = deadlock. Bot account 도입 = 비용 과다.

### A2. Coverage 80% 강제
- **기각**: 6 repo 일괄 = 숫자 맞추기. baseline -2pp drop guard 가 실제 보호.

### A3. Cross-repo workflow_run 표준
- **기각**: 6 repo 개인 운영 장애 지점 폭증. contract pin + scheduled compat 가 대체.

### A4. Signed commits 강제
- **기각**: Dependabot / automation friction. recommended only.

### A5. Live test = skip when no env var
- **기각**: skip ≠ 보호. **guard assertion** 의무.

### A6. Release branch (release/v1.x)
- **기각**: 개인 플랫폼 = `main` always releasable. tag 기반 충분.

### A7. Conventional Commits hard gate
- **기각**: small fix friction. recommended.

## Consequences

### C1. F5 mitigation 적용
solo-dev 단계 모든 PR merge 가능 (CI green + admin 또는 owner self-merge). Bot account 미필요.

### C2. CI gate 가 핵심 보호
required 5 checks 통과 의무. live path = guard assertion (skip 금지).

### C3. Cross-repo trigger 부재 = contract pin 의존
ADR-009 Candle Protocol schema 가 각 repo 의 fixture / pinned version 으로 검증.

### C4. Release CI = `main` always releasable
breaking change 도 `main` 진입 후 tag 시점에 release. 따라서 contract repo 우선 (ADR-010 D7) 이 핵심.

### C5. Live deploy = 별도 ADR 의존
tag → production 직결 = 위험. GitHub environment protection + manual approval 추가 의무.

### C6. CODEOWNERS = 미래 책임 지도
현재 single owner. 팀 확장 시 area 분리 (D10).

### C7. F5 → bot account 도입 trigger 박제 (D11)

## Cross-references

- ADR-002 (6-repo) / ADR-008 (live block) / ADR-009 (Candle Protocol) / ADR-010 (uv + 3.11)
- F5 finding ([mclayer/plugin-codeforge#122](https://github.com/mclayer/plugin-codeforge/issues/122))
- MCT-12 (예정 Epic) — 본 ADR 의 표준이 mctrader-engine + mctrader-market-bithumb + mctrader-data 의 첫 적용 대상
