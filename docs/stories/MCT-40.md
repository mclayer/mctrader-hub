---
story_key: MCT-40
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-37
related_adrs: ADR-005, ADR-006
---

# MCT-40: Lookahead lint CI integration + JSON report + ADR-006 promotion gate hook + Epic E2E (sealing)

## 1. 사용자 요구사항 (verbatim, MCT-37 Epic)

> "MCT-37 Phase 4 sealing — JSON CI report format 정의 + .github/workflows/lookahead-lint.yml + ADR-006 promotion gate hook (lookahead_lint_baseline) + Epic E2E acceptance"

## 2. 도메인 해석

MCT-38 의 LookaheadScanner + MCT-39 의 suppression/allowlist + L4 fixture 의 sealing. CI workflow 통합 + JSON report artifact + ADR-006 promotion gate hook (Backtest 의 promotion gate 가 lookahead_findings_count == 0 검증) + Epic E2E.

## 3. 관련 ADR

- ADR-005 §C3 (CI / pre-commit gate)
- ADR-006 (Backtest → Paper → Live promotion gate)
- 의존: MCT-38 + MCT-39 freeze (LookaheadScanner + suppression + L4 fixture)

## 4. 관련 코드 경로

```
mctrader-engine/
├── .github/workflows/lookahead-lint.yml (NEW)
└── src/mctrader_engine/
    ├── lookahead/
    │   └── report.py (NEW)              # JSON CI artifact format + summary aggregator
    ├── calibration/
    │   └── lookahead_baseline.py (NEW)  # validate_lookahead_baseline (ADR-006 promotion gate hook)
    └── report/schema.py (extend)        # SummaryStats.lookahead_findings_count + lookahead_warnings_count
```

## 5-6. 요구사항

**JSON CI report format**:
```json
{
  "tool": "mct-lookahead-lint",
  "version": "0.1",
  "scan_paths": ["src/mctrader_engine/strategy", "src/mctrader_engine/runner"],
  "scanned_at_utc": "2026-05-04T12:34:56Z",
  "policy_version": "lookahead-lint-v1",
  "findings": [
    {
      "rule_id": "L1.P1",
      "severity": "error",
      "repo": "mctrader-engine",
      "path": "src/mctrader_engine/strategy/foo.py",
      "line": 42,
      "column": 8,
      "symbol": "shift",
      "message": "shift(-n) detected with negative arg = -1",
      "layer": "L1",
      "runtime_area": "runtime",
      "suppressed": false,
      "suppression_id": null,
      "allowlist_id": null,
      "evidence": "    return df['close'].shift(-1)"
    }
  ],
  "summary": {
    "error_count": 1,
    "warning_count": 0,
    "suppressed_count": 0,
    "expired_count": 0
  }
}
```

**ADR-006 promotion gate hook** (lookahead_lint_baseline):
```python
@dataclass(frozen=True, slots=True)
class LookaheadBaselineCheck:
    error_count: int
    warning_count: int
    expired_count: int
    in_range: bool  # error_count == 0 AND expired_count == 0

def validate_lookahead_baseline(report_path: Path) -> LookaheadBaselineCheck: ...
```

**SummaryStats 확장**:
```python
class SummaryStats(BaseModel):
    # ... existing fields ...
    lookahead_findings_count: int = 0
    lookahead_warnings_count: int = 0
    lookahead_expired_count: int = 0
```

`compute_summary` 가 ExecutionReport.events 에 LookaheadFinding 가 있다면 카운트 (현재 schema 에 LookaheadFinding 은 lint output 이지 event 아님 — 단지 promotion gate 가 ExecutionReport 와 lint report 둘 다 검증).

**CI workflow** (`mctrader-engine/.github/workflows/lookahead-lint.yml`):
```yaml
name: lookahead-lint
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
      - run: |
          mctrader-cli lookahead-lint \
            --report-json lookahead_lint_report.json \
            src/mctrader_engine/strategy \
            src/mctrader_engine/runner \
            src/mctrader_engine/executor
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: lookahead_lint_report
          path: lookahead_lint_report.json
```

**branch protection 추가 status check**: `lookahead-lint` 추가 (mctrader-hub/scripts/branch-protection.json 의 engine repo 설정 update — 단 별도 governance 변경 필요, 본 Story 는 workflow 추가만, branch protection 갱신은 Phase 5 hub Epic close PR 에서).

## 7. 설계 서사

### 7.1 JSON report aggregator (A1)

```python
@dataclass(frozen=True, slots=True)
class LookaheadReport:
    tool: str = "mct-lookahead-lint"
    version: str = "0.1"
    scan_paths: tuple[str, ...]
    scanned_at_utc: datetime
    policy_version: str = "lookahead-lint-v1"
    findings: tuple[LookaheadFinding, ...]
    
    @property
    def summary(self) -> LookaheadSummary: ...
    
    def to_json(self) -> str: ...
    
    @classmethod
    def from_findings(
        cls,
        findings: list[LookaheadFinding],
        *,
        scan_paths: list[Path],
        scanned_at_utc: datetime,
    ) -> "LookaheadReport": ...
```

### 7.2 ADR-006 promotion gate hook (A2)

`validate_lookahead_baseline(report_path)` 가 read JSON → `error_count == 0 AND expired_count == 0` 검증. ADR-006 의 promotion 단계 (Backtest → Paper) 에서 호출.

향후 Live mode Epic 진입 시 (Paper → Live promotion gate) 도 동일 호출. MCT-25 의 `summary.kill_switch_violations_count == 0` / MCT-32 의 `summary.rate_limit_violations_count == 0` 와 동일 패턴.

### 7.3 CI workflow (A3)

scan path = `src/mctrader_engine/strategy + runner + executor` (runtime path glob 정의와 일치). other paths 는 default = research → warning + allowlist.

`if: always()` upload-artifact = lint fail 시에도 report 확인 가능.

### 7.4 Engine repo strategy/runner/executor scan = baseline 0 (A4)

현재 SMA strategy 1개 만 → manual review = lookahead 미발견. CI 도입 시 baseline 0 finding 보장 의무.

### 7.5 Epic E2E acceptance (A5)

```python
def test_epic_e2e_lookahead_baseline():
    """Engine repo 자체 strategy/runner/executor scan 시 finding 0건."""
    scanner = LookaheadScanner(severity_profile=DEFAULT_PROFILE)
    findings = scanner.scan_dir([
        Path("src/mctrader_engine/strategy"),
        Path("src/mctrader_engine/runner"),
        Path("src/mctrader_engine/executor"),
    ])
    errors = [f for f in findings if f.severity == "error" and not f.suppressed]
    assert errors == [], f"baseline lookahead findings: {errors}"

def test_epic_e2e_l4_fixture_demo_log():
    """known_bias_shift_minus_1 fixture 가 CI report 에 error 로 나타남 (allowlist 미적용 raw 결과)."""
    raw = LookaheadScanner(...).scan(
        [Path("tests/lookahead/fixtures/known_bias_shift_minus_1.py")],
        allowlist=None,  # raw scan
    )
    p1 = [f for f in raw if f.rule_id == "L1.P1"]
    assert len(p1) >= 1
```

### 7.6 Out-of-scope

- branch protection JSON 갱신 (Phase 5 hub Epic close PR 으로 분리 — cross-repo)
- mctrader-data / mctrader-web cross-repo scan (Phase 5 hub governance doc)
- pre-commit hook installation (CI 에서만 충분, local pre-commit 은 backlog)
- Streamlit lookahead finding dashboard (MCT-31 분리)
- Auto-fix codemod (out-of-scope MCT-37 Epic)

### 7.7 Acceptance (8 AC)

| # | AC |
|---|---|
| AC1 | LookaheadReport JSON aggregator + summary computation |
| AC2 | validate_lookahead_baseline (ADR-006 promotion gate hook) |
| AC3 | SummaryStats 확장 (lookahead_findings_count + warnings_count + expired_count) |
| AC4 | mctrader-engine .github/workflows/lookahead-lint.yml (push + PR trigger + artifact upload) |
| AC5 | CI workflow exit 1 if error_count > 0 OR expired_count > 0 |
| AC6 | Epic E2E test: engine repo strategy/runner/executor baseline = 0 errors |
| AC7 | Epic E2E test: known_bias_shift_minus_1 fixture raw scan = L1.P1 finding present |
| AC8 | 5 required check green + lookahead-lint check green |

### 7.8 Codex 적용

Phase 4 시점에 selective review (E2E + ADR-006 hook → cross-Epic concerns). ADR conflict 0/7.

## 8-11

(Phase 4 = lookahead/report.py + calibration/lookahead_baseline.py + .github/workflows/lookahead-lint.yml + tests/test_lookahead_e2e.py.)
