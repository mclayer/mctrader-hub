---
adr_id: ADR-018
title: Defensive coding patterns — 6-repo cross-cutting invariant baseline
status: Accepted
date: 2026-05-09
related_story: MCT-110 (trigger), MCT-107, MCT-108, MCT-109, MCT-111
category: Architecture
---

# ADR-018: Defensive coding patterns — 6-repo cross-cutting invariant baseline

## Status

Accepted — 2026-05-09. MCT-107~111 code-review fix sweep trigger.

## Context

2026-05-09 Codex 심층 리뷰 (mctrader-market / mctrader-market-bithumb / mctrader-data /
mctrader-engine / mctrader-web 5 repo) 에서 **CRITICAL 14건 / HIGH 22건** 발견.
결함 분포 분석 결과 동일한 7개 패턴이 반복적으로 부재한 것이 근본 원인.

| 패턴 | 결함 사례 (발견 repo / Story) |
|---|---|
| Pydantic validator (float/NaN/whitespace/overflow 거부) | mctrader-market `Decimal38_18` float 입력 허용 (MCT-107) · mctrader-engine `virtual.fill()` fund check 부재 (MCT-110) |
| `frozen=True` + `tuple` (컬렉션 불변성) | mctrader-market `OrderBook.bids/asks` list → 외부 append 가능 (MCT-107) |
| `model_validator(mode="after")` (비즈니스 불변식) | mctrader-market limit order without price · overfill · qty≤0 허용 (MCT-107) |
| `threading.Lock` 원자 카운터 (TOCTOU) | mctrader-engine `rate_limiter` check-then-act (MCT-110) |
| `.tmp_{uuid} → rename()` 원자 파일 쓰기 | mctrader-data Parquet 비원자 쓰기 · `lineage.py` 비원자 쓰기 (MCT-109) |
| case-insensitive header guard | mctrader-market-bithumb forbidden header `.lower()` 비교 누락 (MCT-108) |
| governance flag → artifact-derive (CLI bypass 제거) | mctrader-engine WFO `--gate-d6-passed` bypass flag (MCT-110) |

ad-hoc 한 fix 만으로 끝내면 동일 패턴이 다음 신규 코드에서 또 등장. baseline 박제 필수.

## Decision

### D1. Pydantic validator baseline (입력 sanitization)

**모든 도메인 값 객체** (Decimal money/qty, 문자열 ID, percent, ratio) 는 `field_validator`
로 **타입 강제 + 경계 검증** 의무. float 우회 / NaN / 공백 trim / overflow 차단.

```python
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, field_validator

class Money(BaseModel):
    amount: Decimal

    @field_validator("amount", mode="before")
    @classmethod
    def _no_float(cls, v):
        if isinstance(v, float):
            raise TypeError("float 금지 — Decimal 또는 str 사용")
        try:
            d = Decimal(str(v))
        except InvalidOperation as e:
            raise ValueError(f"Decimal 변환 실패: {v!r}") from e
        if d.is_nan() or not d.is_finite():
            raise ValueError(f"NaN/Inf 금지: {v!r}")
        if d.adjusted() > 38:
            raise ValueError("overflow")
        return d

class SymbolId(BaseModel):
    value: str

    @field_validator("value", mode="before")
    @classmethod
    def _trim_nonempty(cls, v):
        if not isinstance(v, str):
            raise TypeError("str only")
        s = v.strip()
        if not s:
            raise ValueError("empty after strip")
        return s
```

**위반 시 결함 사례**:
- mctrader-market `Decimal38_18` 가 float 입력을 그대로 받아 IEEE 754 binary 오차 전파 (MCT-107)
- mctrader-engine `virtual.fill()` 가 NaN qty 통과 시 잔고 corruption (MCT-110)

### D2. `frozen=True` + `tuple` baseline (컬렉션 불변성)

**도메인 값 객체** (Order / Trade / Snapshot / OrderBook / Candle / Lineage) 는
`model_config = ConfigDict(frozen=True)` + 컬렉션 필드는 `tuple[T, ...]` 의무.
`list` / `dict` mutable 컬렉션 노출 금지.

```python
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class PriceLevel(BaseModel):
    model_config = ConfigDict(frozen=True)
    price: Decimal
    size: Decimal

class OrderBook(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    bids: tuple[PriceLevel, ...]   # NOT list[PriceLevel]
    asks: tuple[PriceLevel, ...]
    ts_utc: int
```

**위반 시 결함 사례**:
- mctrader-market `OrderBook.bids: list[PriceLevel]` → consumer 가 `book.bids.append(...)`
  로 도메인 객체 외부 변형 가능 (MCT-107)
- 동일 객체 cache 공유 시 race / mutation aliasing 결함 노출

### D3. `model_validator(mode="after")` baseline (비즈니스 불변식)

field-level 검증으로 표현 불가능한 **객체 단위 cross-field 불변식** 은
`@model_validator(mode="after")` 로 강제. 생성자 우회 금지.

```python
from pydantic import BaseModel, model_validator
from decimal import Decimal
from typing import Literal

class Order(BaseModel):
    side: Literal["buy", "sell"]
    type: Literal["market", "limit"]
    qty: Decimal
    price: Decimal | None = None
    filled_qty: Decimal = Decimal("0")

    @model_validator(mode="after")
    def _invariants(self):
        if self.qty <= 0:
            raise ValueError("qty must be > 0")
        if self.type == "limit" and self.price is None:
            raise ValueError("limit order requires price")
        if self.type == "market" and self.price is not None:
            raise ValueError("market order must not carry price")
        if self.filled_qty < 0 or self.filled_qty > self.qty:
            raise ValueError("0 <= filled_qty <= qty (overfill 금지)")
        return self
```

**위반 시 결함 사례**:
- mctrader-market `Order(type="limit", price=None)` 통과 / `qty=Decimal("-1")` 통과 /
  `filled_qty > qty` overfill 통과 (MCT-107)

### D4. `threading.Lock` 원자 카운터 (TOCTOU 방지)

check-then-act 패턴 (rate limit / quota / inventory / fund) 은 **단일 lock 안에서
조회 + 갱신 + 결정** 을 원자화. external `is_allowed()` → `consume()` 분리 금지.

```python
import threading
from collections import deque
from time import monotonic

class RateLimiter:
    def __init__(self, capacity: int, window_sec: float):
        self._capacity = capacity
        self._window = window_sec
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def try_consume(self) -> bool:
        now = monotonic()
        with self._lock:                                # 단일 critical section
            while self._events and now - self._events[0] > self._window:
                self._events.popleft()
            if len(self._events) >= self._capacity:
                return False                             # check
            self._events.append(now)                     # act
            return True
```

**위반 시 결함 사례**:
- mctrader-engine `rate_limiter` 에서 `if limiter.is_allowed(): limiter.consume()` 분리
  → concurrent caller 가 한도 초과 통과 (MCT-110)

### D5. 원자 파일 쓰기 (`.tmp_{uuid} → rename()`)

지속 파일 (Parquet / Lineage / Audit log / Manifest) 은 **임시 경로 write + fsync +
rename** 의무. partial-write 방지. crash recovery 안전.

```python
import os
import uuid
from pathlib import Path

def atomic_write_bytes(target: Path, data: bytes) -> None:
    tmp = target.with_suffix(target.suffix + f".tmp_{uuid.uuid4().hex}")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, target)                              # POSIX atomic rename
```

**위반 시 결함 사례**:
- mctrader-data Parquet writer 가 target path 직접 write → SIGKILL / disk-full 시 corrupt
  파일이 catalog 에 등록 (MCT-109)
- `lineage.py` 가 JSON 직접 overwrite → crash 시 빈 파일 남음 (MCT-109)

### D6. case-insensitive header guard

HTTP header / metadata key 비교는 **항상 lowercase normalize 후 비교**. 외부
서버는 case 임의 — `.lower()` 누락은 탐지 회피 결함.

```python
FORBIDDEN_REQUEST_HEADERS: frozenset[str] = frozenset({
    "authorization", "x-api-key", "cookie", "x-secret",
})

def assert_no_forbidden_headers(headers: dict[str, str]) -> None:
    leaked = [
        k for k in headers
        if k.lower() in FORBIDDEN_REQUEST_HEADERS         # NOT k in FORBIDDEN
    ]
    if leaked:
        raise ValueError(f"forbidden headers leaked: {leaked}")
```

**위반 시 결함 사례**:
- mctrader-market-bithumb 가 `if "Authorization" in headers` 식 case-sensitive 비교 →
  exchange 가 `authorization` (lowercase) 로 응답 시 leak guard 우회 (MCT-108)

### D7. governance flag → artifact-derive (CLI bypass 금지)

WFO promote / risk gate / contract validate 등 **governance decision** 은
CLI flag (`--gate-d6-passed`) 로 우회 불가. **아티팩트 파일에서 결정 derive**.

```python
import json
from pathlib import Path

def can_promote(run_dir: Path) -> bool:
    gate = json.loads((run_dir / "gate_d6_result.json").read_text())
    metrics = json.loads((run_dir / "corrected_metrics.json").read_text())
    audit_lines = (run_dir / "audit.log").read_text().splitlines()

    return (
        gate.get("passed") is True
        and gate.get("l4_clean") is True
        and metrics.get("dsr_significant") is True
        and any("EVALUATE_COMPLETE" in line for line in audit_lines)
    )

# CLI 는 flag 받지 않음
@cli.command()
@click.argument("run_dir", type=click.Path(exists=True, path_type=Path))
def promote(run_dir: Path) -> None:
    if not can_promote(run_dir):
        raise click.ClickException("promote 조건 미충족 (artifact-derived)")
    ...
```

**위반 시 결함 사례**:
- mctrader-engine WFO `promote --gate-d6-passed --l4-clean --dsr-significant` flag 가
  artifact 검증 없이 통과 → governance bypass (MCT-110)

### D8. PR 체크리스트 강제 (reviewer 의무)

신규 / 수정 PR 의 **PR template** 에 다음 체크리스트 항목 추가. reviewer 는 각 항목을
명시적으로 확인.

```markdown
## Defensive coding checklist (ADR-018)

- [ ] D1: Decimal/문자열 입력 객체에 `field_validator` 적용 (float/NaN/whitespace/overflow 거부)
- [ ] D2: 도메인 값 객체에 `model_config = ConfigDict(frozen=True)` + 컬렉션은 `tuple[T, ...]`
- [ ] D3: cross-field 불변식이 `@model_validator(mode="after")` 로 강제됨
- [ ] D4: check-then-act 카운터/quota 가 단일 `threading.Lock` 안에서 원자화됨
- [ ] D5: 지속 파일 쓰기가 `.tmp_{uuid} → fsync → rename` 패턴 사용
- [ ] D6: HTTP header / metadata key 비교가 `.lower()` normalize 후 수행
- [ ] D7: governance decision (promote / gate) 이 artifact 에서 derive 되며 CLI flag bypass 불가
- [ ] N/A 표시한 항목은 사유 명시 (예: "이 PR 은 docs only", "외부 의존성 추가만")
```

PR template (`.github/PULL_REQUEST_TEMPLATE.md`) 에 ADR-011 D9 PR template 위에 추가.
N/A 표시 + 사유 없는 PR 은 reviewer 가 changes-requested. 각 repo `.github/`
디렉터리에 동일 체크리스트 복사 (6 repo).

## Alternatives Considered

### A1. ad-hoc 패턴 유지 (case-by-case fix, baseline 미박제)
- **기각**: MCT-107~111 sweep 자체가 ad-hoc 누적의 결과. 동일 패턴이 미래 신규 코드에서
  반복 등장 → 동일 sweep 재발. baseline 박제 + PR 체크리스트 강제 = 신규 코드 차단점.

### A2. lint rule (ruff custom) 로 자동 강제
- **부분 채택 (장기)**: D1 (float 입력) / D2 (`list` 필드) 일부는 AST 기반 ruff plugin
  으로 자동 탐지 가능. 단, D3 (비즈니스 불변식) / D4 (lock semantics) / D7 (artifact
  derive) 는 의도 의존 → 자동화 불가. **현재 단계 = D8 PR 체크리스트 우선**, ruff plugin
  은 별도 Story.

### A3. dataclass(frozen=True) 사용 (Pydantic 회피)
- **기각**: dataclass 는 validation 부재. D1 (float/NaN/overflow 거부) / D3 (cross-field
  불변식) 강제 불가. Pydantic v2 가 single SSOT.

### A4. shared-mutex (multiprocessing) 도입
- **기각**: 현재 6 repo 는 single-process asyncio + thread. 다중 프로세스 quota 가 필요한
  시점 (실거래 multi-node) 은 별도 ADR (Redis / etcd 기반 distributed quota).

### A5. fsync 생략 (성능 우선)
- **기각**: ADR-016 (audit log immutability) / ADR-017 (zero-loss ingestion) 와 충돌.
  ingest path 는 fsync 의무. hot path 영향은 batched write 로 완화.

### A6. governance flag 유지 (운영 편의)
- **기각**: MCT-110 결함의 정확한 재발 경로. flag 를 통한 bypass 가능 = governance 부재
  와 동치. artifact-derive 가 단일 SSOT.

### A7. 신규 코드 + 기존 코드 동시 일괄 소급
- **기각**: 6 repo × 7 패턴 일괄 소급 = scope 폭증 + regression risk. **신규 코드 우선
  강제** (PR 체크리스트), 기존 코드 소급은 별도 Story (per-repo phased migration).
  단, 신규 PR 이 **기존 결함 라인을 touch 하면 같은 PR 에서 fix 의무**.

## Consequences

### C1. 신규 코드 결함 차단점 확보
PR template D8 체크리스트 = 6 repo 공통 1-line gate. reviewer 가 명시적으로 확인.

### C2. 기존 코드 소급 = 별도 Story
6 repo 전체 소급은 phased migration. **신규 PR 이 결함 라인 touch 시 fix 의무** = 점진적
수렴. 별도 Epic 으로 6 repo audit Story 생성 예정.

### C3. Pydantic v2 SSOT 강화
D1 / D2 / D3 모두 Pydantic v2 의존. dataclass / namedtuple / TypedDict 도메인 객체 금지
(외부 SDK 인터페이스는 예외). ADR-009 Candle Protocol 과 정합.

### C4. fsync 비용
D5 가 ingest hot path 의 IOPS 증가. ADR-017 tiered compaction 의 batched write 로 완화.
benchmark 는 별도 Story.

### C5. governance flag 전면 제거
D7 적용으로 WFO / risk gate / contract validate CLI 는 모두 artifact-only. 운영 편의는
artifact prep helper script 로 대체.

### C6. lint plugin 후속 Story
A2 부분 채택 — D1 (float 입력) / D2 (`list` 필드) ruff plugin 별도 Story 로 추적.

### C7. 6 repo PR template 일괄 갱신
mctrader-hub / mctrader-market / mctrader-market-bithumb / mctrader-data /
mctrader-engine / mctrader-web 의 `.github/PULL_REQUEST_TEMPLATE.md` 일괄 갱신 의무.
ADR-011 D9 PR template 와 병합.

## Cross-references

- ADR-009 (Candle Protocol — Pydantic v2 SSOT)
- ADR-011 D9 (PR template — D8 체크리스트가 본 template 에 합류)
- ADR-016 (audit log immutability — D5 atomic write 의 motivation)
- ADR-017 (zero-loss ingestion — D5 fsync + rename 의 정합)
- MCT-107 (mctrader-market fix — D1 / D2 / D3 trigger)
- MCT-108 (mctrader-market-bithumb fix — D6 trigger)
- MCT-109 (mctrader-data fix — D5 trigger)
- MCT-110 (mctrader-engine fix — D1 / D4 / D7 trigger, **본 ADR 의 primary trigger**)
- MCT-111 (mctrader-web fix — D1 / D2 trigger)
