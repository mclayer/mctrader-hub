---
adr_id: ADR-010
title: Python 3.11 + uv + 6 repo install / package management 정책
status: Accepted
date: 2026-05-02
related_story: MCT-10
category: hub
---

# ADR-010: Python 3.11 + uv + 6 repo install policy

## Status

Accepted — 2026-05-02. MCT-10 Phase 1 PR.

## Context

ADR-002 6-repo invariant + ADR-009 Candle Protocol 계약 보존 + reproducible cross-repo dev.

## Decision

### D1. Python `>=3.11,<3.13`, primary 3.11

```toml
requires-python = ">=3.11,<3.13"
```

- Primary runtime / CI = 3.11 latest patch
- Compat lane = 3.12.x
- patch 보안 업데이트 차단 금지

### D2. Package manager = `uv`

`uv.lock` = commit 의무 (모든 repo). PEP 621 metadata 유지 → ejection 가능 (pip/pdm).

### D3. 6 repo dependency wiring

```
mctrader-market (Candle Protocol)
  ↑
mctrader-market-bithumb / mctrader-data
  ↑
mctrader-engine
  ↑
mctrader-web
```

SemVer 0.x = `>=0.2,<0.3` 엄격. `1.0.0` 후 = `>=1.0,<2.0`. **Workspace 미사용** (hub = doc-only).

### D4. PyPI publish (default for personal)

- Open contract package (mctrader-market) = PyPI OK
- Credential / 전략 / config 섞이는 repo = secret scan + package data audit 후만
- git+ssh = personal friction → 회피
- `main` branch dependency = 금지

### D5. Local dev = editable + parent dir

```
C:\workspace\mclayer\{mctrader-hub, mctrader-market, ..., mctrader-web}
```

```powershell
uv pip install -e ../mctrader-market -e ../mctrader-data -e .
```

Release `pyproject.toml` dependency 가 path 로 오염 금지.

### D6. CI workflow

`uv sync --frozen` + 3-tier cache (uv pkg / .venv / artifact). Primary 3.11 + Compat 3.12. Network test = mocked default.

### D7. Cross-repo upgrade procedure

Contract repo 우선:
1. backward-compat 추가 (기존 미제거)
2. DeprecationWarning + minor bump + publish
3. downstream 순차 PR
4. 다음 minor/major 에서 old API 제거

**Lock refresh PR ↔ Contract PR 분리**.

### D8. Pydantic v2 정책

- 경계 (public model / API I/O / config / adapter normalization) = Pydantic v2
- Hot path (bulk load / indicator) = dataclass / TypedDict / NumPy / Pandas 허용

### D9. Decimal 정책

- 가격 / 수량 / 수수료 / 주문 금액 = `decimal.Decimal` canonical
- Hot path = integer scaling / float / NumPy. 주문/정산 경계 Decimal 복귀
- 외부 `python-decimal` 미사용

### D10. Per-repo deps

| Repo | Core |
|---|---|
| market | pydantic>=2,<3 + typing-extensions |
| market-bithumb | aiohttp 또는 httpx |
| data | duckdb / pyarrow / pandas (+optional polars) |
| engine | numpy / pandas / pydantic |
| web | fastapi + uvicorn + pydantic-settings (+streamlit optional group) |

## Alternatives Considered

### A1. Python 3.12 primary
- **기각**: trading/data wheel 호환성 보수적 우선. 3.12 = compat lane only.

### A2. Poetry / PDM
- **기각**: install 속도 / lockfile / cross-platform universal = uv 우위. ejection path = PEP 621.

### A3. Conda environment
- **기각**: 6 repo PyPI/git dep workflow 와 부조합.

### A4. Monorepo workspace (hub = root)
- **기각**: 6-repo invariant 손실.

### A5. git+ssh dependency
- **기각**: personal CI deploy key friction.

### A6. main branch dependency
- **기각**: reproducibility 손실.

### A7. Pydantic 전체 (hot path 포함)
- **기각**: bulk load / indicator 비용. 경계 + hot path 분리 의무.

### A8. Float for price (Decimal 미적용)
- **기각**: backtest 누적 정확도. ADR-009 D1 invariant.

## Consequences

### C1. uv migration cost
모든 repo `pyproject.toml` + `uv.lock` 작성 + CI 갱신. 1회 비용.

### C2. SemVer 0.x = 엄격 dependency pin
breaking change cascading 어려움. contract repo 우선 + downstream 순차 PR.

### C3. PyPI publish boundary
publish 전 secret scan + package data audit 의무 (ADR-008 D9 와 align).

### C4. cross-repo dev = parent dir 표준
team 확장 시 standard layout 의무.

### C5. Pydantic v2 lock-in
v3 출시 시 별도 ADR amend.

## Cross-references

- ADR-002 6-repo / ADR-009 Candle Protocol / ADR-008 secret scan
- MCT-11 (예정) — branch protection / CI trigger 표준
