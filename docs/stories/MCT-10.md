---
story_key: MCT-10
status: phase:요구사항
component: hub
type: brainstorm
related_adr: ADR-010
---

# MCT-10: Python 버전 + 6 repo install / package management 정책

## 1. 사용자 요구사항 (verbatim)

mctrader 의 Python 버전 + 6 repo install 정책.

## 2. 도메인 해석

6 repo invariant (ADR-002) 보존 + reproducible cross-repo development. \"최신성\" 보다 \"Candle Protocol 계약 + 6 repo invariant 미파괴 + 재현 가능\" 우선.

## 3. 관련 ADR

- ADR-010 ([`../adr/ADR-010-python-install.md`](../adr/ADR-010-python-install.md))
- baseline: ADR-002 6-repo / ADR-009 Candle Protocol contract source

## 4. 관련 코드 경로

```
각 repo/
├── pyproject.toml          # PEP 621 metadata, requires-python, deps
├── uv.lock                 # commit 의무
├── .python-version         # patch fixed
├── README.md
└── src/<package>/...
```

Local dev parent dir:
```
C:\workspace\mclayer\
  mctrader-hub\
  mctrader-market\
  mctrader-market-bithumb\
  mctrader-data\
  mctrader-engine\
  mctrader-web\
```

## 5-6. 요구사항 / 외부 지식

`uv` (Astral) / `pdm` / `poetry` / `pip+venv` / `hatch` / `Conda` 비교. PEP 621 / PEP 751 (`pylock.toml`).

## 7. 설계 서사 (요약)

### 7.1 Python version

```toml
[project]
requires-python = ">=3.11,<3.13"
```

- **Primary runtime**: Python 3.11 latest patch (운영 / CI primary)
- **Compatibility lane**: 3.12.x (CI 보조)
- 3.12 → primary 승격 = 6 repo 모두 통과 후 별도 ADR
- `.python-version` / Docker base / deployment runtime 에서 patch 또는 minor 고정. patch 보안 업데이트 차단 금지.

근거: trading/data 의존성 (numpy / pandas / pyarrow / duckdb / pydantic-core) wheel 호환성 보수적 우선.

### 7.2 Package manager = `uv`

| Manager | 평가 | 채택 |
|---|---|---|
| pip + venv | 보편적, 디버깅 쉬움. lock/sync/workspace 수동 정책 많음 | 기본 X |
| Poetry | 성숙. 속도/표준 친화 = uv 보다 무거움 | X |
| PDM | PEP 582 / PEP 751 친화. install 속도 = uv 우위 | optional |
| Hatch | build backend 강함. daily manager 부적합 | build only |
| Conda | 과학계 binary 강함. 6 repo PyPI/git dep 과 부조합 | X |
| **uv** | project + lock + workspace + cross-platform universal lockfile + cache 빠름 | **Default** |

**`uv` 종속 핵심 = `uv.lock` + 일부 `[tool.uv]` 만**. Package metadata = PEP 621 표준 → 최악 시 pip/pdm 이탈 가능.

### 7.3 Lockfile policy

- `uv.lock` = **commit 의무** (모든 repo, library 포함)
- application/service repo (engine / web / market-bithumb) 은 lock 강제
- library repo (market / data) 도 6 repo 가 함께 움직이는 private/product codebase 이므로 commit
- Compat = 별도 minimal-deps lane 으로 검증

### 7.4 6 repo dependency wiring

ADR-002 6-repo invariant 보존. **monorepo workspace 미사용** (hub = doc-only).

Dependency direction:
```
mctrader-market           (Candle Protocol source, ADR-009)
  ↑
mctrader-market-bithumb   (adapter, market 의존)
mctrader-data             (storage, market protocol 의존)
  ↑
mctrader-engine           (market + data 의존)
  ↑
mctrader-web              (engine 또는 별도 API client 의존, market 직접 의존 회피)
```

**Version pin (SemVer 0.x = 엄격)**:
```toml
# mctrader-engine pyproject.toml
[project]
dependencies = [
  "mctrader-market>=0.2,<0.3",
  "mctrader-data>=0.2,<0.3",
]
```

`1.0.0` 안정화 후 = `>=1.0,<2.0`.

### 7.5 PyPI publish vs git+ssh vs workspace

- **PyPI publish (default for personal)**: open contract (mctrader-market) = OK. credential / 전략 / config 섞이는 repo = secret scan + package data audit 후만 publish.
- **git+ssh**: 팀 비공개에는 valid 하나 personal 단계 friction (CI deploy key / known_hosts / SSH agent). 회피.
- **uv workspace**: hub 가 monorepo root 화 = 6-repo invariant 흐림. **미채택**. local dev convenience 만 (parent dir + editable).

### 7.6 Local dev cross-repo install

```powershell
uv pip install -e ../mctrader-market -e ../mctrader-data -e .
```

**Release `pyproject.toml` dependency 가 path 로 오염되면 안 됨**. path/editable = local dev 전용.

### 7.7 CI workflow

GitHub Actions 표준:
1. checkout
2. Python 3.11 setup
3. uv install
4. uv cache restore
5. `uv sync --frozen` (lockfile resolution 강제)
6. lint / type / test 실행

CI matrix:
- **Primary**: Python 3.11, latest OS (Ubuntu 또는 Windows per repo)
- **Compatibility**: Python 3.12 필수 테스트만
- mctrader-data: Windows lane 추가 (file path / DuckDB / Parquet 차이)
- mctrader-market-bithumb: network test = mocked HTTP / replay fixture default. 실제 Bithumb API call = scheduled / manual job only.

Cache 3-tier:
1. uv package cache (필수)
2. `.venv` (lock hash match 시만, 초반 보류)
3. build artifact (보수적)

### 7.8 Cross-repo upgrade procedure

**Contract repo 우선 원칙**:
1. `mctrader-market` 에 backward-compatible 추가 (기존 field/method 미제거, 새 추가)
2. `DeprecationWarning` 또는 doc deprecated marker
3. minor version bump + publish
4. downstream (data / market-bithumb / engine) 순차 PR 로 새 API consume
5. 모든 downstream 이동 후 다음 minor 또는 major 에서 old API 제거

**ADR-009 Candle Protocol breaking change = engine 에서 시작 금지**. 변경 소유권 = contract repo.

**Lock refresh PR ↔ Contract PR 분리**:
- Lock refresh = behavior 변경 없음, dependency 만 갱신
- Contract PR = version bump + changelog + migration note + downstream compat test

### 7.9 Release CI = tag 기반

`v0.2.0` tag push:
- build
- twine 또는 uv publish
- smoke install 테스트

`main` branch dependency = **금지** (재현성 손실).

### 7.10 권장 라이브러리 set

| Repo | Core deps |
|---|---|
| mctrader-market | `pydantic>=2,<3`, typing-extensions (lightweight protocol package) |
| mctrader-market-bithumb | `aiohttp>=3.13,<4` OR `httpx>=0.27,<1` (async streaming + REST = aiohttp 자연) |
| mctrader-data | `duckdb`, `pyarrow`, `pandas`, optional `polars` |
| mctrader-engine | `numpy`, `pandas`, `pydantic` (numba = 후속 측정 후 결정) |
| mctrader-web | `fastapi`, `uvicorn`, `pydantic-settings` (API). `streamlit` = optional dep group (`[dependency-groups] dashboard`) |

**Pydantic v2 정책**:
- 외부 경계 (Candle Protocol public model, API I/O, config, adapter normalization) = Pydantic v2 의무
- 내부 hot path (tick/candle bulk load, indicator 계산) = dataclass / TypedDict / NumPy / Pandas 허용

**Decimal 정책**:
- 가격 / 수량 / 수수료 / 주문 금액 = `decimal.Decimal` canonical (Python 표준)
- 성능 필요 hot path = integer scaling 또는 float/NumPy. 주문/정산 경계에서 Decimal 복귀
- `python-decimal` 같은 외부 lib 미사용

### 7.11 Codex 적용

채택률 18/18.

## 8-11

(Phase 2 N/A — doc-only Story.)
