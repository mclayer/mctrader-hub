---
story_key: MCT-37
status: phase:요구사항
component: hub
type: epic
related_stories: MCT-38, MCT-39, MCT-40
related_adrs: ADR-002, ADR-005
parent_epic: MCT-32 (predecessor)
---

# MCT-37: ADR-005 Lookahead lint (L1 libcst static + L4 known-bias fixture) (Epic)

## 1. 사용자 요구사항 (verbatim)

> "후속 작업 진행" — Codex 1순위 추천 채택. Live mode 의 외부 prerequisite (1Password CLI / GitHub Environments / Bithumb live key) 미확인 → Live deferral. **Lookahead lint** = Backtest↔Paper calibration 신뢰성 foundation, 외부 prerequisite 없음, 즉시 진행 가능.

## 2. 도메인 해석

mctrader 의 **다섯 번째 implementation Epic** (MCT-12 Backtest, MCT-18 Paper, MCT-25 RiskGate full, MCT-32 Order rate limit 다음). ADR-005 의 4-layer verification 중 **L1 (libcst static lint) + L4 (known-bias fixture)** 구체화. L2 (visible_window) + L3 (event log invariant) 은 MCT-12/16 시점에 이미 정착.

핵심 가치 = (a) **Backtest 결과 신뢰성** — lookahead 가 backtest 성능을 인위적으로 부풀리는 가장 흔한 사고 차단 (ADR-005 §C5: lookahead 가 backtest 신뢰성 직접 손상). (b) **Strategy 추가의 안전망** — 향후 multi-strategy registry / WFO Epic 진입 시 strategy 가 lookahead-safe 인지 자동 검증. (c) **외부 prerequisite 없음** — libcst dev dependency 추가만으로 진행 가능, 사용자 manual setup 불필요.

## 3. 관련 ADR

| ADR | 적용 |
|---|---|
| ADR-002 | StrategyContext.visible_window 만 사용 (raw DataFrame 미노출, lint 가 직접 read 호출 차단) |
| ADR-005 D2 L1 | libcst AST scan — strategy runtime path = error / research+label = warning + allowlist |
| ADR-005 D2 L4 | known-bias fixture 4종 중 3종 (`shift_minus_1`, `same_candle_high_low_fill`, `future_feature_dataset`). `oos_selection_loop` = MCT-6 split registry dependency, 본 Epic out-of-scope |
| ADR-005 D7 | Runtime enforcement 한계 4-step — strategy 의 raw data path import 금지 (lint 가 강제) |
| ADR-005 §C3 | CI / pre-commit gate — L1 lint = pre-commit + CI gate / L4 fixture = test suite 의무 |

## 4. 관련 코드 경로 (3 신규 child Story 분담)

```
mctrader-engine/                       # MCT-38 (foundation: L1 scanner core)
├── pyproject.toml (extend)              # libcst dev dependency
└── src/mctrader_engine/lookahead/
    ├── __init__.py (NEW)
    ├── finding.py (NEW)                 # LookaheadFinding Pydantic v2 frozen
    ├── patterns.py (NEW)                # 6 base detection patterns + severity profile
    ├── scanner.py (NEW)                 # libcst MatchVisitor + scan(file_paths)
    └── cli.py (NEW)                     # mctrader-cli lookahead-lint <paths>

mctrader-engine/                       # MCT-39 (suppression + L4 fixture)
└── src/mctrader_engine/lookahead/
    ├── suppression.py (NEW)             # # mctrader-lookahead-allow: <rule_id> reason="..." owner=... expires=YYYY-MM-DD
    ├── allowlist.py (NEW)               # repo/path/pattern/reason/owner/expiry config (TOML)
    └── tests/lookahead/
        ├── fixtures/
        │   ├── known_bias_shift_minus_1.py        (L1 expected)
        │   ├── known_bias_same_candle_fill.py     (L3 expected, BacktestExecutor invariant fail)
        │   └── known_bias_future_feature.py       (L2 expected, raw DataFrame access)
        ├── test_l1_patterns.py
        ├── test_suppression_expiry.py
        └── test_l4_fixtures.py

mctrader-engine/                       # MCT-40 (sealing: CI integration + Epic E2E)
├── .github/workflows/lookahead-lint.yml (NEW)  # CI gate (engine repo)
├── src/mctrader_engine/lookahead/
│   └── report.py (NEW)                  # JSON CI artifact format + summary
└── src/mctrader_engine/calibration/
    └── lookahead_baseline.py (NEW)      # ADR-006 promotion gate hook (lookahead_findings_count == 0)

mctrader-hub/                          # Phase 5 Epic close
└── docs/governance/
    └── lookahead-cross-repo-policy.md (NEW)  # mctrader-data + mctrader-web 확장 시점 policy
```

## 5-6. 요구사항 / 외부 지식

ADR-005 D2 L1 detection patterns (6 base):

| # | Pattern | Detection method | Severity (runtime) | Severity (research) |
|---|---|---|---|---|
| P1 | `shift(-n)` / `pct_change(-n)` / `diff(-n)` (negative arg) | libcst Call + Arg negative integer literal | error | warning |
| P2 | `rolling(center=True)` | libcst Call + kw `center=True` | error | warning |
| P3 | `iloc[i+N]` / `iloc[idx + N]` (positive offset on positional indexer) | libcst Subscript + BinaryOp + positive integer | error | warning |
| P4 | `bfill()` / `fillna(method="bfill")` | libcst Call name + kw method | error | warning |
| P5 | `merge_asof(direction="forward")` | libcst Call + kw direction | error | warning |
| P6 | full-sample scaler fit before split (sklearn `*Scaler.fit(X)` before `train_test_split`) | libcst Call + ordered name resolution | error | warning |

ADR-005 D2 L4 known-bias fixture (Epic out-of-scope = `oos_selection_loop`):

| Fixture | Expected fail layer | Verification |
|---|---|---|
| `known_bias_shift_minus_1_strategy` | L1 | scanner finds rule_id=L1.P1 with severity=error |
| `known_bias_same_candle_high_low_fill` | L3 | BacktestExecutor invariant (`fill_price_source_ts >= eligible_fill_ts`) raises |
| `known_bias_future_feature_dataset` | L2 | StrategyContext.visible_window violation — strategy import direct read API → lint catches at L1, runtime catches at L2 |

**라이브러리 채택**: libcst (formatting 보존 + suppression annotation parse 가능, ADR-005 D2 L1 명시).

**Severity profile mechanism**:
- `runtime_path` = `mctrader_engine/strategy/**/*.py` + `mctrader_engine/runner/**/*.py` (engine runtime — error)
- `research_path` = `**/notebook/**` + `**/research/**` + `**/label/**` (warning, allowlist 가능)
- 결정 = path glob 기반 (import-graph 기반은 추정, MCT-37 out-of-scope)

**Suppression annotation**:
```python
df["x"] = df["close"].shift(-1)  # mctrader-lookahead-allow: L1.P1 reason="label gen, not strategy runtime" owner=mccho expires=2026-08-01
```
- 4 field 모두 mandatory (`rule_id`, `reason`, `owner`, `expires`)
- expires 가 today 이전 = error (suppression abuse 방지)
- expires 미래 + reason 빈 문자열 = error

## 7. 설계 서사 (Codex 7-area + Sonnet 합성)

### 7.1 End-to-end acceptance (B / C / D)

**Blocking AC** (Epic 종료 의무):

| # | AC | 검증 |
|---|---|---|
| B1 | `mctrader-cli lookahead-lint <paths>` exit 0 (no findings) / exit 1 (findings present) | CLI smoke test |
| B2 | libcst 기반 6 base detection pattern (P1~P6) 모두 fixture 에서 trigger | 6 unit fixture |
| B3 | runtime path = error / research path = warning + allowlist | severity profile test (path glob 기반) |
| B4 | `LookaheadFinding` Pydantic v2 frozen + JSON serialization | schema validation |
| B5 | known-bias fixture 3종 (shift_minus_1, same_candle, future_feature) 각 expected layer 에서 fail | L4 fixture test |
| B6 | suppression annotation 4-field mandatory + expiry gate | suppression abuse test |
| B7 | CI integration — engine repo `.github/workflows/lookahead-lint.yml` (push + PR trigger) | CI green E2E |
| B8 | JSON CI report artifact (`lookahead_lint_report.json`) — findings + summary | artifact upload |
| B9 | ADR-005 §C3 align — pre-commit + CI gate (engine repo strategy/runner runtime path scan) | docs cross-ref |

**Calibration AC**:

| # | metric | 의미 | gate |
|---|---|---|---|
| C1 | `lookahead_lint_baseline` | engine repo strategy runtime path 의 baseline finding 수 0 | `summary.error_count == 0` 강제 |
| C2 | `suppression_expiry_compliance` | expired suppression 0건 | CI 매 run 마다 검증 |

**Demonstration AC**:

| # | AC | 검증 |
|---|---|---|
| D1 | known_bias_shift_minus_1 fixture 가 CI report 에 error 로 출력되는 demo log | CI log 첨부 |

### 7.2 3 child Story 분해

```
              MCT-38 (foundation: L1 scanner core)
                          ↓
              MCT-39 (suppression + L4 fixture)
                          ↓
              MCT-40 (sealing: CI integration + Epic E2E)
```

| Story | repo | bump (예상) | 의존 |
|---|---|---|---|
| MCT-38 | mctrader-engine | 0.9.0 → 0.10.0 | MCT-32 freeze (engine 0.9.0) |
| MCT-39 | mctrader-engine | 0.10.0 → 0.11.0 | MCT-38 freeze (LookaheadFinding API) |
| MCT-40 | mctrader-engine | 0.11.0 → 0.12.0 | MCT-38 + MCT-39 freeze (E2E) |

**Joint 후보 검토**: MCT-39 (suppression + L4 fixture) joint = O. L4 fixture 검증에 suppression mechanism 이 내포됨 (allowlist 가 있어야 known-bias fixture 가 CI 에 안 잡힘). MCT-32 의 MCT-34+35 joint pattern 동일.

### 7.3 libcst scanner 구조 (A1, MCT-38)

```python
class LookaheadFinding(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    rule_id: Literal["L1.P1", "L1.P2", "L1.P3", "L1.P4", "L1.P5", "L1.P6"]
    severity: Literal["error", "warning"]
    repo: str          # 'mctrader-engine'
    path: str          # relative path
    line: int
    column: int
    symbol: str        # affected name (function / variable)
    message: str
    layer: Literal["L1"]
    runtime_area: Literal["runtime", "research", "label"]
    suppressed: bool
    suppression_id: str | None
    allowlist_id: str | None
    evidence: str      # 1-line code excerpt

class LookaheadScanner:
    def __init__(self, *, severity_profile: SeverityProfile): ...
    def scan(self, file_paths: list[Path]) -> list[LookaheadFinding]: ...
```

**libcst MatchVisitor**: 각 P1~P6 별로 visit method 분리. `m.matches()` 로 pattern match 후 finding emit.

### 7.4 Severity profile (path glob, A2, MCT-38)

```python
DEFAULT_PROFILE = SeverityProfile(
    runtime_globs=["mctrader_engine/strategy/**/*.py", "mctrader_engine/runner/**/*.py"],
    research_globs=["**/notebook/**", "**/research/**", "**/label/**"],
    # default = research (warning) for unmatched paths
)
```

**비채택 (out-of-scope)**: import-graph 기반 runtime detection (libcst 외 type checker 필요, 추정).

### 7.5 Suppression annotation + expiry (A3, MCT-39)

```python
# mctrader-lookahead-allow: L1.P1 reason="label gen" owner=mccho expires=2026-08-01
df["target"] = df["close"].shift(-1)
```

Parser:
- Comment 의 `mctrader-lookahead-allow: <rule_id> reason="..." owner=<name> expires=<YYYY-MM-DD>` 파싱
- 4 field 모두 mandatory
- expires < today (UTC) → suppression invalid → finding 그대로 emit + suppression_expired flag
- 같은 line + 다음 line 모두 적용 (libcst comment attribution)

### 7.6 L4 fixture 3종 (A4, MCT-39)

```python
# fixtures/known_bias_shift_minus_1.py — L1 expected
def predict_next(df):
    return df["close"].shift(-1)  # leak: future close
```

Test:
```python
def test_l4_shift_minus_1_caught_by_l1():
    findings = scan_file("fixtures/known_bias_shift_minus_1.py")
    assert any(f.rule_id == "L1.P1" and f.severity == "error" for f in findings)
```

**같은 candle high/low fill** = BacktestExecutor invariant 호출 — fixture 가 BacktestExecutor 를 invoke 하면 ExecutionReport 생성 시 L3 invariant 위반 raise. fixture infrastructure = mctrader-engine/tests/lookahead/.

### 7.7 CI integration (A5, MCT-40)

```yaml
# mctrader-engine/.github/workflows/lookahead-lint.yml
on: [push, pull_request]
jobs:
  lookahead-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: mctrader-cli lookahead-lint src/mctrader_engine
      - uses: actions/upload-artifact@v4
        with:
          name: lookahead_lint_report
          path: lookahead_lint_report.json
```

CI gate = `summary.error_count == 0` (warning 은 not blocking).

### 7.8 Out-of-scope (확정 거부)

| 항목 | MCT-37 미포함 | 이유 |
|---|---|---|
| `oos_selection_loop` fixture | ✗ | MCT-6 split registry dependency (별도 Epic) |
| 완전한 alias / dataflow 분석 | ✗ | libcst static scope 한계, ADR-005 §C4 박제 |
| dynamic `getattr` / monkeypatch / runtime generated code | ✗ | static scope 한계 |
| talib / pandas-ta rule pack | ✗ | 라이브러리별 semantic model 부담, backlog |
| Auto-fix codemod | ✗ | suppression 추가만 권장, code rewrite 위험 |
| IDE plugin 통합 (VSCode / PyCharm) | ✗ | CLI + CI 만, IDE 는 backlog |
| import-graph 기반 runtime detection | ✗ | path glob 으로 충분, 추정 도구 도입 회피 |
| Column-name heuristic (target/label/future) 정확도 보장 | ✗ | warning + allowlist 로 false positive 처리 |
| Cross-repo scan (mctrader-data / mctrader-web) | ✗ | engine 만 (Phase 5 governance doc 으로 향후 확장 시점 명시) |
| L2 visible_window 재설계 / L3 event log schema 재설계 | ✗ | 이미 정착, 본 Epic = L1 + L4 만 |

### 7.9 CFP-60 debut-audit checklist

각 child Phase 2 merge 직후:
- **lane-progression** (lookahead lint 의 strategy runtime / research path 분리 evidence)
- **decision-table** (6 detection pattern × 2 severity profile = 12 결정)
- **workflow-invariant** (ADR-005 D2 L1+L4 강제, D7 4-step, §C3 CI gate)
- **contract-schema** (LookaheadFinding + JSON CI report)

### 7.10 Phase 1 / Phase 2~5 분담

**Phase 1** (본 Epic Story):
- 본 Epic doc + 3 child stub (MCT-38 ~ MCT-40) registration
- AC freeze (B1~B9 + C1~C2 + D1)
- Decomposition freeze: 3 child + Epic close
- libcst dev dep 결정
- 6 base detection pattern (P1~P6) freeze
- Severity profile (path glob 기반) freeze
- Suppression annotation 4-field mandatory + expiry gate freeze
- L4 fixture 3종 (oos_selection_loop 제외) freeze
- Phase 1 PR

**Phase 2** (MCT-38 implementation, mctrader-engine):
- libcst dependency 추가 (pyproject.toml dev)
- mctrader_engine/lookahead/ module skeleton
- LookaheadFinding Pydantic schema
- 6 base detection pattern 구현
- mctrader-cli lookahead-lint CLI 추가

**Phase 3** (MCT-39 implementation, mctrader-engine):
- suppression annotation parser (4-field + expiry gate)
- allowlist TOML config
- L4 fixture 3종 + pytest CI

**Phase 4** (MCT-40 sealing, mctrader-engine):
- JSON CI report format
- `.github/workflows/lookahead-lint.yml`
- ADR-006 promotion gate hook (`lookahead_lint_baseline`)
- Epic E2E acceptance (CLI + CI + report 통합)

**Phase 5** (Epic close PR, mctrader-hub):
- governance doc (`docs/governance/lookahead-cross-repo-policy.md`)
- EPIC-RESULTS-MCT-37.md
- memory state update

### 7.11 Codex 적용

7/7 area 채택. ADR conflict 0/7 (ADR-005 D2 L1+L4 의 구체화, 충돌 없음).

추가 surface (Codex dig_deeper):
- helper function wrap (`future_returns(df, n)`) → known limitation 박제 (§C1)
- groupby-apply nested → libcst nested visitor 가 lambda body 까지 scan (P1~P3 적용)
- multi-index `xs` / `groupby(level=...)` 주변 positive offset → P3 의 확장 (`iloc[i+N]` 계열)
- suppression abuse → expiry gate + 4-field mandatory

## 8-11

(Phase 2 ~ 5 = 3 child Story PR + Epic close PR. 본 Epic Story 자체는 doc-only.)
