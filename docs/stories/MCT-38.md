---
story_key: MCT-38
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-37
related_adrs: ADR-005, ADR-002
---

# MCT-38: Lookahead L1 scanner core (libcst + 6 patterns + LookaheadFinding + CLI) (foundation)

## 1. 사용자 요구사항 (verbatim, MCT-37 Epic)

> "MCT-37 foundation — libcst dev dependency + LookaheadFinding Pydantic schema + 6 base detection pattern (P1~P6) + mctrader-cli lookahead-lint CLI"

## 2. 도메인 해석

mctrader-engine 0.9.0 에 lookahead lint module 신규 추가. ADR-005 D2 L1 의 6 base detection pattern (shift(-n), pct_change(-n), diff(-n), rolling(center=True), iloc[i+N], bfill, merge_asof(direction="forward"), full-sample scaler fit) 을 libcst MatchVisitor 로 구현. CLI = `mctrader-cli lookahead-lint <paths>`. MCT-39 / MCT-40 모두 이 foundation 기반 동작.

## 3. 관련 ADR

- ADR-005 D2 L1 (libcst static lint, 6 base detection pattern)
- ADR-005 D7 (Strategy 의 raw data path import 금지)
- ADR-002 (StrategyContext.visible_window 만 노출)
- 의존: MCT-32 freeze (engine 0.9.0)

## 4. 관련 코드 경로

```
mctrader-engine/
├── pyproject.toml (extend)              # libcst dev dependency
└── src/mctrader_engine/lookahead/
    ├── __init__.py (NEW)
    ├── finding.py (NEW)                 # LookaheadFinding Pydantic v2 frozen
    ├── patterns.py (NEW)                # 6 detection patterns + severity profile
    ├── scanner.py (NEW)                 # libcst MatchVisitor + scan(file_paths)
    └── cli.py (NEW)                     # mctrader-cli lookahead-lint <paths>
```

## 5-6. 요구사항

**libcst dependency**:
- `libcst>=1.5,<2` (CST 변환 + formatting 보존 + comment attribution)
- dev only (runtime path 가 아니므로 production dependency 아님)

**LookaheadFinding** (Pydantic v2 frozen):
```python
class LookaheadFinding(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    rule_id: Literal["L1.P1", "L1.P2", "L1.P3", "L1.P4", "L1.P5", "L1.P6"]
    severity: Literal["error", "warning"]
    repo: str
    path: str
    line: int
    column: int
    symbol: str
    message: str
    layer: Literal["L1"]
    runtime_area: Literal["runtime", "research"]
    suppressed: bool = False
    suppression_id: str | None = None
    allowlist_id: str | None = None
    evidence: str  # 1-line code excerpt
```

**6 detection patterns**:

| Rule | libcst pattern | Trigger condition |
|---|---|---|
| L1.P1 | `Call(func=Attribute(attr=Name("shift" \| "pct_change" \| "diff")), args=[Arg(value=Integer(_, "-N") \| UnaryOperation(operator=Minus, expression=Integer))])` | negative integer literal 또는 unary minus |
| L1.P2 | `Call(func=Attribute(attr=Name("rolling")), args includes kw `center=True`)` | center=True kwarg present |
| L1.P3 | `Subscript(value=Attribute(attr=Name("iloc")), slice=BinaryOperation(operator=Add, right=Integer(value>0)))` | iloc[idx + positive] 형태 |
| L1.P4 | `Call(func=Attribute(attr=Name("bfill")))` 또는 `Call(func=Attribute(attr=Name("fillna")), kw=method="bfill")` | |
| L1.P5 | `Call(func=Attribute(attr=Name("merge_asof")), kw=direction="forward")` | |
| L1.P6 | `Call(func=Attribute(attr=Name("fit")))` 가 `train_test_split` 보다 textually 앞에 있는 경우 (file-level scope, basic ordering) | basic textual ordering — semantic dataflow 분석 X |

**Severity profile** (path glob):
- `runtime`: `mctrader_engine/strategy/**/*.py` + `mctrader_engine/runner/**/*.py` + `mctrader_engine/executor/**/*.py`
- `research`: 외 모두 → warning + allowlist 가능
- (참고) tests/lookahead/fixtures/ = research (의도적 known-bias fixture, allowlist 등록 — MCT-39 Story scope)

**CLI**:
```
$ mctrader-cli lookahead-lint src/mctrader_engine
ERROR: src/mctrader_engine/strategy/sma.py:42:8 [L1.P1] shift(-1) detected
ERROR: src/mctrader_engine/strategy/foo.py:88:4 [L1.P3] iloc[i+5] detected
WARNING: notebook/research.ipynb.py:120:2 [L1.P2] rolling(center=True) detected (research path)
Summary: 2 errors, 1 warning
exit 1
```

## 7. 설계 서사

### 7.1 LookaheadFinding schema (A1)

frozen Pydantic v2 model. JSON serialization 가능 (CI artifact). `evidence` 필드 = 1-line code excerpt (디버깅 가독성).

### 7.2 Pattern matcher (A2)

각 P1~P6 별로 `libcst.matchers` 의 MatchVisitor subclass. visit method 에서 match → LookaheadFinding emit. Negative integer 처리 (libcst 는 unary minus + Integer 분리 표현 — `m.UnaryOperation(operator=m.Minus(), expression=m.Integer())` 로 매칭).

### 7.3 Scanner orchestration (A3)

```python
class LookaheadScanner:
    def __init__(self, *, severity_profile: SeverityProfile): ...
    
    def scan(self, file_paths: list[Path]) -> list[LookaheadFinding]:
        findings = []
        for path in file_paths:
            tree = cst.parse_module(path.read_text())
            wrapper = cst.MetadataWrapper(tree)
            for visitor_class in [P1Visitor, P2Visitor, P3Visitor, P4Visitor, P5Visitor, P6Visitor]:
                visitor = visitor_class(path=path, profile=self._profile)
                wrapper.visit(visitor)
                findings.extend(visitor.findings)
        return findings
```

`MetadataWrapper` 로 PositionProvider 추출 (line / column 정보).

### 7.4 Severity profile (A4)

```python
@dataclass(frozen=True, slots=True)
class SeverityProfile:
    runtime_globs: tuple[str, ...] = (
        "mctrader_engine/strategy/**/*.py",
        "mctrader_engine/runner/**/*.py",
        "mctrader_engine/executor/**/*.py",
    )
    
    def severity_for(self, path: Path) -> tuple[Literal["error", "warning"], Literal["runtime", "research"]]:
        if any(path.match(g) for g in self.runtime_globs):
            return ("error", "runtime")
        return ("warning", "research")
```

### 7.5 CLI (A5)

```python
import click

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--report-json", type=click.Path(path_type=Path), help="JSON report output")
@click.option("--severity", type=click.Choice(["all", "error", "warning"]), default="all")
def lookahead_lint(paths: tuple[Path, ...], report_json: Path | None, severity: str):
    scanner = LookaheadScanner(severity_profile=SeverityProfile())
    files = collect_python_files(paths)
    findings = scanner.scan(files)
    print_findings(findings, severity_filter=severity)
    if report_json:
        report_json.write_text(json.dumps([f.model_dump() for f in findings], default=str, indent=2))
    if any(f.severity == "error" and not f.suppressed for f in findings):
        sys.exit(1)
```

`mctrader-cli` Click group 에 `lookahead-lint` subcommand 추가.

### 7.6 Out-of-scope (MCT-39 / MCT-40 위임)

- Suppression annotation parser (MCT-39)
- TOML allowlist (MCT-39)
- L4 fixture (MCT-39)
- CI workflow (MCT-40)
- JSON CI report format detail (MCT-40)
- ADR-006 promotion gate hook (MCT-40)

### 7.7 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | `libcst>=1.5,<2` dev dependency 추가, pyproject.toml extras |
| AC2 | LookaheadFinding Pydantic v2 frozen, JSON 직렬화 가능 |
| AC3 | 6 detection pattern (P1~P6) 모두 micro-fixture 에서 trigger |
| AC4 | SeverityProfile path glob 분류 (strategy/runner/executor = error / 외 = warning) |
| AC5 | LookaheadScanner.scan(paths) → list[LookaheadFinding] |
| AC6 | mctrader-cli lookahead-lint CLI exit 0/1 + --report-json + --severity filter |
| AC7 | engine repo 자체 strategy/runner/executor scan 시 finding 0건 (ADR-005 §C3 baseline) |
| AC8 | 5 required check green (lint/test/pyright Linux, lint/test Windows) |

### 7.8 Codex 적용

Phase 2 시점에 micro task 단위, 추가 detail review 선택. ADR conflict 0/7.

## 8-11

(Phase 2 = lookahead/finding.py + patterns.py + scanner.py + cli.py.)
