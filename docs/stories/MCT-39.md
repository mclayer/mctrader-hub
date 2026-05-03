---
story_key: MCT-39
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-37
related_adrs: ADR-005
---

# MCT-39: Suppression annotation + TOML allowlist + L4 known-bias fixture 3종

## 1. 사용자 요구사항 (verbatim, MCT-37 Epic)

> "MCT-37 Phase 3 — suppression annotation 4-field mandatory + expiry gate + TOML allowlist + L4 known-bias fixture 3종 (shift_minus_1 / same_candle / future_feature)"

## 2. 도메인 해석

MCT-38 의 LookaheadScanner 기반에 (a) suppression annotation parser (`# mctrader-lookahead-allow: <rule_id> reason="..." owner=... expires=YYYY-MM-DD`) + (b) TOML allowlist (research path 의 path/pattern/reason/owner/expiry) + (c) L4 known-bias fixture 3종 추가. ADR-005 D2 L4 의 4 fixture 중 3개 (oos_selection_loop = MCT-6 dependency, 본 Epic out-of-scope).

## 3. 관련 ADR

- ADR-005 D2 L4 (known-bias fixture 4종 중 3종)
- ADR-005 §C1 (Strategy code 작성 제약 — false positive 시 explicit suppression)
- ADR-005 §C3 (CI / pre-commit gate)
- 의존: MCT-38 freeze (LookaheadFinding API)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/lookahead/
├── suppression.py (NEW)             # 4-field annotation parser + expiry gate
└── allowlist.py (NEW)               # TOML allowlist (path/pattern/reason/owner/expiry)

mctrader-engine/tests/lookahead/
├── fixtures/
│   ├── known_bias_shift_minus_1.py        (L1.P1 trigger fixture)
│   ├── known_bias_same_candle_fill.py     (L3 invariant trigger — BacktestExecutor invocation)
│   └── known_bias_future_feature.py       (L2 / L1.P3 trigger — direct read API call from strategy)
├── lookahead_allowlist.toml         # research path 의 의도적 known-bias 등록
├── test_l1_patterns.py              # MCT-38 의 6 pattern 통합 테스트
├── test_suppression.py              # 4-field mandatory + expiry gate
└── test_l4_fixtures.py              # 3 fixture expected layer fail 검증
```

## 5-6. 요구사항

**Suppression annotation grammar**:
```
# mctrader-lookahead-allow: <rule_id> reason="<quoted>" owner=<bare> expires=<YYYY-MM-DD>
```

- 4 field 모두 mandatory (rule_id / reason / owner / expires)
- reason = double-quoted string (공백 포함 가능)
- owner = bare token (이메일 / GitHub handle, 공백 X)
- expires = ISO date YYYY-MM-DD
- 같은 line 또는 바로 이전 line 의 comment 가 적용 (libcst comment attribution)
- 1 annotation = 1 finding suppress
- expires < today (UTC) → suppression invalid → finding emit + suppression_expired flag (CI gate 가 그대로 실패)

**TOML allowlist** (`lookahead_allowlist.toml`):
```toml
[[entry]]
id = "research-feature-builder-v1"
path_glob = "tests/lookahead/fixtures/known_bias_*"
rule_ids = ["L1.P1", "L1.P3", "L1.P4"]
reason = "L4 known-bias fixture (intentional)"
owner = "mccho"
expires = "2027-12-31"
```

- runtime path (severity=error) 는 allowlist 적용 X — annotation 만 가능 (의도적 strict)
- research path (severity=warning) = allowlist 적용 가능
- 같은 expiry gate 적용

**L4 fixture 3종 spec**:

| Fixture | Trigger layer | 검증 mechanism |
|---|---|---|
| `known_bias_shift_minus_1.py` | L1.P1 | `predict_next(df) → df["close"].shift(-1)` 함수, `LookaheadScanner.scan` 가 L1.P1 finding emit |
| `known_bias_same_candle_fill.py` | L3 | `SameCandleFillStrategy` 가 BacktestExecutor 호출 시 ExecutionReport 생성 → invariant `fill_price_source_ts >= eligible_fill_ts` 위반 raise |
| `known_bias_future_feature.py` | L2 / L1.P3 | strategy 가 raw DataFrame 직접 read 시도 (visible_window 우회) — L1.P3 (iloc[i+N]) 또는 raw read API import 로 trigger |

**Expected fail layer test pattern**:
```python
def test_l4_shift_minus_1_caught_by_l1():
    findings = LookaheadScanner(severity_profile=DEFAULT_PROFILE).scan(
        [Path("tests/lookahead/fixtures/known_bias_shift_minus_1.py")]
    )
    p1_findings = [f for f in findings if f.rule_id == "L1.P1"]
    assert len(p1_findings) >= 1
    # severity = warning (research path) — but rule_id 가 detect 됨 = L4 충족
```

## 7. 설계 서사

### 7.1 Suppression parser (A1)

libcst 의 `Comment` node 에서 `mctrader-lookahead-allow:` prefix 추출. 정규식 + simple tokenizer:
```
^# mctrader-lookahead-allow: (?P<rule_id>L1\.P[1-6]) reason="(?P<reason>[^"]+)" owner=(?P<owner>\S+) expires=(?P<expires>\d{4}-\d{2}-\d{2})$
```

4 field 누락 = parse failure → annotation 무시 (또는 error 로 emit?)
**채택**: parse failure = warning emit (`L1.SUPPRESSION_MALFORMED` rule_id) + suppression 무효. CI 에서 user 가 조치하도록 가시화.

### 7.2 Expiry gate (A2)

```python
def is_active(self, *, today: date) -> bool:
    return self.expires >= today
```

`today` injection (Clock 패턴 동일) — test 에서 expired suppression 강제 검증 가능.

### 7.3 TOML allowlist (A3)

```python
@dataclass(frozen=True, slots=True)
class AllowlistEntry:
    id: str
    path_glob: str
    rule_ids: frozenset[str]
    reason: str
    owner: str
    expires: date

class Allowlist:
    @classmethod
    def from_toml(cls, path: Path) -> "Allowlist": ...
    def find_match(self, *, finding: LookaheadFinding, today: date) -> AllowlistEntry | None: ...
```

`tomllib` (Python 3.11+ stdlib).

### 7.4 LookaheadScanner.scan_with_suppression (A4)

```python
class LookaheadScanner:
    def scan(
        self,
        file_paths: list[Path],
        *,
        allowlist: Allowlist | None = None,
        today: date | None = None,
    ) -> list[LookaheadFinding]:
        raw = self._scan_raw(file_paths)
        return self._apply_suppression(raw, allowlist=allowlist, today=today or date.today())
```

`_apply_suppression` 단계 = annotation match + allowlist match → `suppressed=True / suppression_id / allowlist_id` 채워서 finding 갱신. Expired = `suppressed=False` + 추가 finding (`L1.SUPPRESSION_EXPIRED`).

### 7.5 L4 fixture 3종 (A5)

**known_bias_shift_minus_1.py** (research path, allowlist):
```python
"""L4 fixture — L1.P1 trigger via shift(-1)."""
import pandas as pd

def predict_next_close(df: pd.DataFrame) -> pd.Series:
    return df["close"].shift(-1)  # mctrader-lookahead-allow: L1.P1 reason="L4 fixture intentional" owner=mccho expires=2027-12-31
```

**known_bias_same_candle_fill.py** (research path):
```python
"""L4 fixture — L3 invariant trigger via same-candle fill."""
class SameCandleFillStrategy:
    def on_bar(self, ctx):
        # 의도적으로 current candle 의 high 로 fill 가정
        return Decision.buy(target_quantity=Decimal("0.001"), fill_price_source="bar_high")  # 의도적
```

테스트 = `BacktestExecutor.run(strategy=SameCandleFillStrategy())` → `ExecutionReport` 생성 시 L3 invariant audit 가 raise (또는 strict 모드 violation 기록).

**known_bias_future_feature.py** (research path):
```python
"""L4 fixture — L1.P3 + L2 trigger via raw read."""
class FutureFeatureStrategy:
    def on_bar(self, ctx):
        full_df = ctx._raw_dataframe  # 의도적 private access (lint 가 catch — strategy import 차단 추정)
        next_close = full_df.iloc[ctx.current_index + 1]["close"]  # L1.P3 trigger
        return Decision.hold()
```

**Allowlist 항목**:
```toml
[[entry]]
id = "l4-known-bias-fixtures"
path_glob = "tests/lookahead/fixtures/known_bias_*"
rule_ids = ["L1.P1", "L1.P3"]
reason = "L4 known-bias fixtures intentional for regression test"
owner = "mccho"
expires = "2027-12-31"
```

### 7.6 Expected fail layer test (A6)

```python
def test_l4_shift_minus_1_l1_caught():
    findings = LookaheadScanner(severity_profile=DEFAULT_PROFILE).scan(
        [Path("tests/lookahead/fixtures/known_bias_shift_minus_1.py")]
    )
    assert any(f.rule_id == "L1.P1" for f in findings)

def test_l4_same_candle_fill_l3_caught():
    """BacktestExecutor 의 L3 invariant audit 가 same-candle fill 을 감지."""
    with pytest.raises(LookaheadInvariantError, match="fill_price_source_ts.*eligible_fill_ts"):
        BacktestExecutor(...).run(strategy=SameCandleFillStrategy())

def test_l4_future_feature_l1_caught():
    findings = LookaheadScanner(...).scan([...])
    assert any(f.rule_id == "L1.P3" for f in findings)
```

### 7.7 Acceptance (10 AC)

| # | AC |
|---|---|
| AC1 | Suppression annotation 4-field mandatory parser |
| AC2 | Expiry gate (today injected) — expired = invalid |
| AC3 | Malformed annotation = warning + L1.SUPPRESSION_MALFORMED |
| AC4 | TOML allowlist (path_glob + rule_ids + reason + owner + expires) |
| AC5 | runtime path = allowlist 적용 X (annotation only) |
| AC6 | research path = allowlist + annotation 둘 다 가능 |
| AC7 | L4 fixture: known_bias_shift_minus_1.py L1.P1 trigger detected |
| AC8 | L4 fixture: known_bias_same_candle_fill.py L3 invariant trigger detected (BacktestExecutor invocation) |
| AC9 | L4 fixture: known_bias_future_feature.py L1.P3 trigger detected |
| AC10 | 5 required check green |

### 7.8 Codex 적용

Phase 3 시점에 selective review (joint child Story 의 acceptance density 가 높음 → 6+ AC). ADR conflict 0/7.

## 8-11

(Phase 3 = suppression.py + allowlist.py + tests/lookahead/.)
