# Change Plan — MCT-182 Layer 0 Contract Relocation → mctrader-market (EPIC-data-domain-decoupling Story-1)

- **Story**: MCT-182
- **Status**: design-review-ready (Iteration 1 — ArchitectPLAgent 통합 검수 PASS 2026-05-16)
- **Story file**: [`docs/stories/MCT-182.md`](../stories/MCT-182.md)
- **ADR**: [ADR-031](../adr/ADR-031-data-domain-decoupling.md) 신규 publish (Proposed) · ADR-029/027/030 amendment **예고 box** only (실 amend = MCT-183/184/185/186/188) · respects [ADR-025](../adr/ADR-025-aggregation-core-lib-contract.md) (aggregation SSOT 계보)
- **Target repo**: `mctrader-hub` (Phase 1 docs) + `mctrader-market` + `mctrader-data` + `mctrader-engine` (Phase 2 cross-repo code)
- **Epic**: EPIC-data-domain-decoupling — sequential_phase 1 (Epic entry, strangler-fig 1단계)

## 1. 입력 요약 (Story §1 verbatim, immutable)

> "data 영역은 mctrader와 아예 분리하고 싶다. 표준 mctrader에는 호출용 interface, data에는 그를
> 처리하는 REST API가 있는게 좋겠다. 프로젝트 구조는 mctrader-hub에서도 구현할 수 있고
> mctrader-data 단독으로도 필요사항을 반영할 수 있어야겠다."

EPIC-data-domain-decoupling Story-1 (Epic 진입 Story). Epic 종착점 = mctrader-engine 을 (1)
data-free + (2) exchange-agnostic pure consumer 로 전환. 본 Story = strangler-fig **1단계** —
Layer 0(mctrader-market = FOUNDATION) 확립. PURE-contract 3종 + CandleModel 경로 정리를 market
으로 이전·재지정, data/engine 호출부는 무중단 deprecation shim 전환 + ADR-031 publish (Proposed).

## 2. 현재 구조 (CodebaseMapperAgent 산출 — verified-via git grep/Read, working tree 2026-05-16)

### 2.1 핵심 자산 인벤토리

| 자산 | 경로 | verified fact | 본 Story 와 관계 |
|------|------|---------------|-------------------|
| `aggregation` 패키지 | `mctrader-data/src/mctrader_data/aggregation/{__init__,core,scaled_int,contract_metadata}.py` | 외부 의존 = stdlib + `mctrader_market.{protocols.information_bar(core.py:35),schemas.tick(core.py:36),types(core.py:37)}` 뿐. `mctrader_data.*` = self-package 내부 참조만 (`__init__.py:23-33`). **PURE** | **market 물리 이전 대상** — core/scaled_int/contract_metadata + `__init__` 8 심볼 |
| aggregation public API | `aggregation/__init__.py:35-44` `__all__` | `ContractMetadata`, `DollarBarAggregator`, `TickBarAggregator`, `TimeBarAggregator`, `VolumeBarAggregator`, `compute_contract_id`, `from_scaled`, `to_scaled` (8 심볼) | **contract pin SSOT** (Task2↔Task3 동일 유지) |
| `TickRecord` | `mctrader-data/src/mctrader_data/tick_storage.py:50-65` | `@dataclass`(line 50-51) 본문 = stdlib(datetime/Decimal) only. 8 field. `__post_init__` float-guard(line 61-65). pyarrow = 모듈 레벨 import(line 32-33) → dataclass 비결합 | **dataclass만 추출** → `market.records`. writer 잔류 |
| `OrderbookEventRecord` | `mctrader-data/src/mctrader_data/orderbook_storage.py:57-74` | `@dataclass`(line 57-58) 본문 = stdlib only. 10 field. `__post_init__` float-guard(line 70-74). pyarrow = 모듈 레벨(line 38-39) → 비결합 | **dataclass만 추출** → `market.records`. writer 잔류 |
| `paper_lineage` | `mctrader-data/src/mctrader_data/paper_lineage.py` | import = stdlib(hashlib:14/json:15) + pydantic(BaseModel,ConfigDict:19) + `mctrader_market.types.UTCDateTime`(line 21) 뿐. `PaperLineage`(BaseModel, line 24) + `canonical_jsonl_hash`(def, line 38). **PURE** | **market 물리 이전 대상** (2 심볼) |
| `CandleModel` | `mctrader-market/src/mctrader_market/candle.py:60` | `class CandleModel(BaseModel)`(line 60) + `ConfigDict(strict=True, frozen=True, arbitrary_types_allowed=True)`(line 67). **이미 존재** | **verify-only** (재구현 0) |
| engine CandleModel import | `mctrader-engine` (실측 4곳) | `from mctrader_data.cold.duckdb_resample import CandleModel` — backtest/data_source.py:17 + consumers/candle_view.py:33 + consumers/signal_provenance_log.py:31 + paper/data_source.py:22 (가설 5곳 정정 — candle_view.py:38 = docstring) | **import 경로 재지정** → `mctrader_market.candle` |
| engine market 직독 (무변경) | `mctrader-engine` reconciliation/strategy_reproducibility.py:40 + realtime/aggregator.py:9 | 이미 `from mctrader_market.candle import CandleModel` | **무변경** (D1 방향 정합 — 잔여 4곳 동일 정렬) |
| market src/ `git grep mctrader_data` | `mctrader-market/src/` | **0건** + pyproject mctrader-data 의존 0 | relocate 안전성 근거 (순환 영구 0) |

### 2.2 결합도 분석 (RefactorAgent + CodebaseMapper 협업)

- **aggregation → market 의존만** (PURE): `core.py` 가 `mctrader_market.{protocols.information_bar,
  schemas.tick, types}` 의존 — relocate 후 동일 repo 내부 참조로 단순화 가능. `mctrader_data.*` 외부
  의존 0 → market 이전 시 결합 전파 0
- **TickRecord/OrderbookEventRecord ↔ pyarrow 결합도: 0** — dataclass 본문은 stdlib only,
  pyarrow(`import pyarrow as pa`/`pq`)는 모듈 레벨이라 클래스 정의와 비결합. dataclass 정의만
  발췌 시 pyarrow import 동반 없음 (V4 정합)
- **paper_lineage ↔ data 결합도: 0** (PURE) — `mctrader_market.types.UTCDateTime` 만 외부 의존
- **shim 영향 data 내부 사용처**: `src/mctrader_data/__init__.py`, `cold/duckdb_resample.py`,
  `cold/polars_fallback.py`, `paper_storage.py` — shim 경유 무중단 동작 의무 (INV-4 is-동일성)

### 2.3 변경 영향 지도

| 영향 자산 | 영향 종류 | 보존/대체 |
|----------|----------|----------|
| `aggregation.core` 내부 `from mctrader_market...` | **단순화** | relocate 후 동일 repo 내부 참조 (public API `__all__` 8 심볼 동일 유지) |
| `aggregation/__init__.py` `__all__` 8 심볼 | **재사용 (SSOT)** | market 측 `__init__` 동일 export — Task2↔Task3 일치 |
| `tick_storage.py`/`orderbook_storage.py` pyarrow writer | **무변경 (잔류)** | dataclass import 만 `mctrader_market.records` 재지정 (INV-6 — writer 로직 0 변경) |
| `mctrader-data` aggregation/lineage/storage 테스트 | **회귀 0 + market 이식** | 동등성 테스트 market 측 이식, data 측 shim back-compat 회귀 |
| engine CandleModel 사용처 (전략·지표·consumer) | **회귀 0** | 객체 동일성 보존 (재구현 0) — import 경로만 변경 |
| engine market 직독 2곳 | **무변경** | 정합 상태 유지 |

## 3. 도입할 설계 (RefactorAgent 산출 + ArchitectAgent 통합)

### 3.1 4-Layer Layer 0 확립 (high-level)

```
 mctrader-market (Layer 0 FOUNDATION, 의존 0, DAG 최하위, data 비의존)
   src/mctrader_market/
   ├── aggregation/            ◀ NEW (← mctrader_data.aggregation PURE 패키지 이전)
   │   ├── __init__.py         public API 8 심볼 (__all__ 동일 유지 — contract pin)
   │   ├── core.py             4 Aggregator + per-symbol state machine
   │   ├── scaled_int.py       to_scaled / from_scaled (Decimal drift 방지)
   │   └── contract_metadata.py  ContractMetadata + compute_contract_id (SHA256)
   ├── records.py              ◀ NEW (← TickRecord/OrderbookEventRecord 순수 dataclass 추출)
   ├── paper_lineage.py        ◀ NEW (← mctrader_data.paper_lineage PURE 이전)
   └── candle.py               = CandleModel (기존 존재 — verify-only, 재구현 0)
        ▲ (market→누구도 의존 안 함 — 순환 영원히 0)
 mctrader-data (Layer 2 — shim 잔류, 무중단 back-compat)
   ├── aggregation/__init__.py → market re-export shim + DeprecationWarning
   ├── paper_lineage.py        → market re-export shim + DeprecationWarning
   └── tick_storage.py / orderbook_storage.py
        → TickRecord/OrderbookEventRecord 를 from mctrader_market.records import 재지정
          (pyarrow writer 로직 무변경 — INV-6)
 mctrader-engine (Layer 2' — PURE CONSUMER 진입)
   └── CandleModel import 4곳 → from mctrader_market.candle import CandleModel
        (backtest/data_source.py:17 + consumers/candle_view.py:33 +
         consumers/signal_provenance_log.py:31 + paper/data_source.py:22)
```

### 3.2 Contract pin (market Layer0 모듈 public API — SSOT 박제)

relocate 후 market 측이 노출할 public API contract (data shim ↔ market re-export 1:1 일치 의무):

**(a) `mctrader_market.aggregation` `__init__` export (8 심볼 — `__all__` 동일):**
```python
# src/mctrader_market/aggregation/__init__.py
__all__ = [
    "ContractMetadata", "DollarBarAggregator", "TickBarAggregator",
    "TimeBarAggregator", "VolumeBarAggregator",
    "compute_contract_id", "from_scaled", "to_scaled",
]
```
data 측 기존 `__init__.py:35-44` `__all__` 과 **byte-for-byte 동일** (심볼 추가/제거 0 — contract pin).

**(b) `mctrader_market.records` (TickRecord/OrderbookEventRecord 순수 dataclass):**
```python
# src/mctrader_market/records.py — stdlib only (pyarrow import 금지, INV-3)
@dataclass
class TickRecord:
    ts_utc: datetime; received_at: datetime; exchange: str; symbol: str
    price: Decimal; quantity: Decimal; side: str; raw_json: str | None = None
    def __post_init__(self) -> None:  # float-guard 보존 (INV-1 동작 동등)
        if isinstance(self.price, float): raise TypeError("float not allowed for price; use Decimal or str")
        if isinstance(self.quantity, float): raise TypeError("float not allowed for quantity; use Decimal or str")

@dataclass
class OrderbookEventRecord:
    ts_utc: datetime; received_at: datetime; exchange: str; symbol: str
    event_type: str; side: str; level: int
    price: Decimal; quantity: Decimal; raw_json: str | None = None
    def __post_init__(self) -> None:  # 동형 float-guard 보존
        ...
```
field 순서/이름/default/`__post_init__` 메시지 = data 원본(tick_storage.py:51-65 / orderbook_storage.py:58-74)
**byte-for-byte 보존** (pyarrow schema 가 field 순서 의존 — 변경 시 직렬화 깨짐).

**(c) `mctrader_market.paper_lineage` (PURE — 2 심볼):**
```python
# src/mctrader_market/paper_lineage.py — stdlib + pydantic + mctrader_market.types only
class PaperLineage(BaseModel): ...                          # pydantic BaseModel
def canonical_jsonl_hash(messages: Iterable[dict[str, Any]]) -> str: ...  # SHA256 byte-equivalence
```

### 3.3 shim 식별성 보존 패턴 (RefactorAgent 채택 — INV-4 SSOT 단일)

data 측 shim 은 **사본 생성 금지** — market 객체와 `is` 동일성 보존:

```python
# src/mctrader_data/aggregation/__init__.py (shim)
import warnings
from mctrader_market.aggregation import *           # noqa: F403 — re-export (동일 객체 식별성)
from mctrader_market.aggregation import __all__     # contract pin 동일 전파

warnings.warn(
    "mctrader_data.aggregation 은 mctrader-market(Layer0)로 이전됨. "
    "from mctrader_market.aggregation import ... 로 전환하세요 (MCT-182, ADR-031 §D1).",
    DeprecationWarning, stacklevel=2,
)
```
`from mctrader_market.X import *` (사본 X) → `mctrader_data.aggregation.TickBarAggregator is
mctrader_market.aggregation.TickBarAggregator` 보장 (INV-4). paper_lineage shim 동형.

tick_storage/orderbook_storage 는 shim 이 아닌 **import 재지정** (writer 로직 무변경):
```python
# tick_storage.py — TickRecord 정의 삭제, import 로 대체
from mctrader_market.records import TickRecord  # SSOT=market, writer 로직 그대로
# (pyarrow writer 클래스 TickWriter / _records_to_arrow / schema = 무변경, INV-6)
```

### 3.4 aggregation 내부 참조 단순화 (RefactorAgent)

relocate 후 `core.py:35-37` 의 `from mctrader_market.{protocols.information_bar, schemas.tick,
types} import ...` 는 **동일 repo 내부 참조**가 된다 (market 내부로 이동하므로). import path
문자열 자체는 동일 유지 가능 (`mctrader_market.` prefix 절대 import 유지 — 상대 import 강제 X,
기존 패턴 보존). `contract_metadata.py`/`scaled_int.py` 는 외부 의존 0 (stdlib only) — 무변경 이전.

## 4. 외부 인터페이스

### 4.1 import surface (변경 표)

| consumer | AS-IS import | TO-BE import | 마이그레이션 |
|----------|--------------|--------------|-------------|
| engine (4곳) | `from mctrader_data.cold.duckdb_resample import CandleModel` | `from mctrader_market.candle import CandleModel` | 경로 재지정 (재구현 0, 객체 동일) |
| engine (2곳, 무변경) | `from mctrader_market.candle import CandleModel` | (동일) | 없음 (정합 상태 유지) |
| data 내부 (`cold/`, `paper_storage`, `__init__`) | `from mctrader_data.aggregation import ...` / `paper_lineage` | (shim 경유 동작 보존) | 없음 (shim 무중단 — DeprecationWarning 만 emit) |
| 외부/신규 consumer | — | `from mctrader_market.{aggregation,records,paper_lineage} import ...` | Layer0 직접 import 권장 |

**부작용 변경 없음**: relocation = namespace 이동 + import 경로 재지정. 런타임 동작/직렬화/hash
출력 **byte-for-byte 동등** (INV-1). API signature 변경 0. CLI 변경 0.

### 4.2 패키지 layout 변화

- market: `src/mctrader_market/` 에 `aggregation/`(패키지) + `records.py` + `paper_lineage.py` 신규
  (candle.py 무변경)
- data: `aggregation/__init__.py`/`paper_lineage.py` = shim 전환. **`core`/`scaled_int`/
  `contract_metadata` 하위모듈은 deprecated 보존 (MCT-188 D7 finalize 까지)** — `__init__` shim 만
  public API 진입점 (사본 금지, market re-export). 하위모듈 즉시 삭제 금지 (cold path
  `.core` 직접 import 존재 — Option B ImportError 차단, 물리 삭제 = MCT-188 D7 owner).
  cold/ production path 의 `.core` 직접 import (`cold/duckdb_resample.py:53` +
  `cold/polars_fallback.py:36`, shim 우회 → INV-4 is-동일성 위반) 는 **data fix PR 에서
  `from mctrader_market.aggregation import ...` 직접 재지정** (MCT-182 owner — strangler-fig
  Layer0 1단계 무중단 명세 정합). 하위모듈 파일 물리 삭제 + grep0 quad gate = MCT-188 D7
  owner (scope 경계 — §6/§2.2/scope_manifest line 204 정합).
  tick_storage/orderbook_storage = dataclass import 재지정
- engine: 4 파일 import 1줄씩 재지정

## 5. 비기능 (perf / observability)

### 5.1 Performance Baseline — N/A 명시 (TestContractArch 산출)

- **Perf Baseline = N/A (불요)** — 본 Story 는 PURE-contract **relocation** (namespace 이동 +
  import 경로 재지정). 알고리즘/자료구조/호출 경로 무변경 → perf 무영향. 자동룰 SSOT 정합
  ("relocation/refactor-only Story → Perf Baseline N/A + 사유 1줄").
- **사유**: aggregation 알고리즘 코드 byte-equivalence (동일 함수 본문 물리 이동), shim 은
  `import *` re-export (1회 import 시 DeprecationWarning emit 외 런타임 hot-path 비용 0),
  dataclass 추출은 정의 위치만 변경 (인스턴스화 비용 동일). perf 회귀 측정 대상 부재.
- **검증 대체**: byte-equivalence 동등성 테스트(§8 INV-1)가 perf 회귀를 간접 차단 (출력 동일 =
  연산 경로 동일).

### 5.2 Observability

- **N/A** — internal contract relocation, metric/alert/health 표면 무변경 (신규 observability
  surface 0). DeprecationWarning emit = pytest `-W error::DeprecationWarning` 게이트로 검출 가능
  (§8.3 shim 테스트).

## 6. 리팩터링 선행

- **선행 PR 없음** — Phase 0 verify(§8 Phase 0 절) 가 유일 선행 게이트
- aggregation/paper_lineage = data 내부 사용처(`__init__`/`cold/`/`paper_storage`) shim 경유 무중단
  → 사용처 사전 마이그레이션 불요 (DeprecationWarning 만 emit, MCT-188 D7 finalize 까지 deprecated 유지)
- engine 4곳 = import 1줄 재지정 (사전 리팩터링 불요)

## 7. 보안 / 운영 리스크 설계

### 7.1 Trust boundary (SecurityArchitectAgent 산출 — 간략 declare)

- **신규 trust boundary 0** — 본 Story = PURE-contract 코드 namespace 이동 + import 경로 재지정.
  네트워크 표면/IPC/직렬화 경계/외부 입력 처리 경로 **무변화**. attack surface delta = 0.
- relocate 대상(aggregation/records/paper_lineage)은 모두 in-process python 모듈 — 외부 입력
  파싱/네트워크/파일 I/O 미수반 (pyarrow writer 는 data 잔류, 본 Story 무변경).

### 7.2 Auth / authz

- **N/A** — auth/credential/secret 신규 0. ADR-008 변경 0.

### 7.3 데이터 보호

- **N/A** — PII/sensitive data 처리 경로 무변경. raw_json field = data writer 잔류 (본 Story
  dataclass 정의만 이동, 직렬화 경로 무변경).

### 7.4 운영 리스크 (OperationalRiskArchitectAgent 산출 — CONDITIONAL N/A)

| 항목 | 판정 | 사유 |
|------|------|------|
| DR / disconnect / clock / rate-limit / env-isolation | **N/A** | 본 Story 는 docs-only Phase 1 + PURE-contract relocate. 신규 service/daemon/connection/scheduler 도입 0. runtime topology 무변경 (compose/credential/network 무변경). |
| 유일 운영 risk = cross-repo land_order desync (R1) | **§9 Rollout/Backout 에서 다룸** | land_order(hub P1→market→data→engine→hub P2) 위반 시 import 실패 — Phase 0 verify 독립 게이트 + §9.3 backout 으로 완화 (운영 risk 아닌 release-ordering risk) |

> §8.5 spawn-time trigger 결정 (CFP-378 AC-5): §8.5 4 조건 (long-running connection /
> stateful in-memory cache / background worker / process restart-aware) **4개 모두 N** →
> **§8.5_active=false**. 근거: 본 Story 는 contract relocation (신규 connection/cache/worker/
> restart-aware system 도입 0). TestContractArch 는 본 결정 verbatim 반영.

### 7.5 Threat modeling (STRIDE 요약)

- Spoofing/Tampering/Repudiation/Information disclosure/DoS/Elevation = **전 N/A** — in-process
  모듈 namespace 이동, 외부 trust boundary delta 0. 신규 위협 벡터 부재.

### 7.6 보안 ack

SecurityArchitectAgent 채택 — author Architect agree. 본 변경은 외부 trust boundary 추가 0,
PURE-contract 코드 이동 only. attack surface 무변화.

### 7.7 N/A 영역 (박제)

- 외부 API 노출 0 / secret·credential 신규 0 / 네트워크 표면 0 / 신규 trust boundary 0
- §7.4 운영 리스크 5 항목 = CONDITIONAL N/A (relocation Story — runtime topology 무변경)

## 8. Test Contract (TestContractArchitectAgent 산출 + Architect 통합)

### 8.0 Phase 0 Verify Gate (조건 2 명문화 — market#N 착수 전 design/impl lane 의무, R1 가드)

> **본 절은 코드 작업(market#N) 착수 전 design/impl lane 이 선이행 의무.** session/brainstorm/
> Story §0 박제(4곳)는 가설로 수용 — working tree HEAD 기준 재검증 의무 (docker-stack Phase 0
> verify gap 6회 누적 → 7회째 사전 차단).

| Gate | 명령 | 기대 | 불일치 시 |
|------|------|------|-----------|
| **V1 (git fetch 3 repo)** | `git -C c:/workspace/mclayer/mctrader-data fetch origin && git -C c:/workspace/mclayer/mctrader-engine fetch origin && git -C c:/workspace/mclayer/mctrader-market fetch origin` | working tree stale 차단 (HEAD 기준 재grep 전제) | — |
| **V5 재grep (HEAD 기준)** | `git -C c:/workspace/mclayer/mctrader-engine grep -n "from mctrader_data.cold.duckdb_resample import CandleModel" -- 'src/*'` | **정확히 4곳** = backtest/data_source.py:17 + consumers/candle_view.py:33 + consumers/signal_provenance_log.py:31 + paper/data_source.py:22 (§0 박제와 재대조) | **STOP → ArchitectPL escalate** (R1 desync) |
| **V2/V3 PURE 재확인** | `git -C .../mctrader-data grep -n "mctrader_data" -- 'src/mctrader_data/aggregation/*.py' 'src/mctrader_data/paper_lineage.py'` | self-package 내부 참조만 (외부 = stdlib + `mctrader_market.*`) | STOP → escalate |
| **V4 dataclass 재확인** | tick_storage.py:50-65 / orderbook_storage.py:57-74 Read | dataclass 본문 stdlib only, pyarrow 모듈 레벨 | STOP → escalate |
| **V6 순환 재확인** | `git -C .../mctrader-market grep -n "mctrader_data" -- 'src/*'` | **0건** | STOP → escalate |

> design lane 박제(2026-05-16 working tree): V5 = 정확히 4곳 (verified). V2/V3/V4/V6 = 정합.
> market#N 착수 시점에 V1 fetch 후 위 gate 전수 재실행 — §0 4곳과 재대조, 불일치 시 escalate.

### 8.1 Invariant (byte-equivalence + 무중단)

- **INV-1 [byte-equivalence]**: contract 이전 후 입출력 byte-for-byte 동등
  - `canonical_jsonl_hash(messages)` 출력 SHA256 = 이전 `mctrader_data.paper_lineage` 출력과 동일
    - 테스트: `tests/test_paper_lineage_relocated.py::test_canonical_jsonl_hash_byte_equivalence`
  - scaled-int round-trip: `from_scaled(to_scaled(d)) == d` (Decimal drift 0)
    - 테스트: `tests/test_aggregation_relocated.py::test_scaled_int_roundtrip_no_drift`
  - 4 Aggregator(TimeBar/Volume/Tick/Dollar) 동일 입력 tick 시퀀스 → 출력 bar byte-for-byte 동등
    - 테스트: `tests/test_aggregation_relocated.py::test_four_aggregators_output_equivalence`
  - `compute_contract_id` SHA256 = 이전과 동일 hash
    - 테스트: `tests/test_aggregation_relocated.py::test_contract_id_hash_unchanged`
- **INV-2 [market→data 순환 영구 0]**: relocate 후 market `src/` `git grep mctrader_data` == 0건
  - 테스트: `tests/test_layer0_no_data_dep.py::test_market_src_grep_mctrader_data_zero`
- **INV-3 [pyarrow 비결합]**: `import mctrader_market.records` 후 `sys.modules` 에 `pyarrow` 부재
  - 테스트: `tests/test_records.py::test_records_import_does_not_load_pyarrow`
    (`import mctrader_market.records; assert "pyarrow" not in sys.modules` — clean subprocess)
- **INV-4 [shim is-동일성]**: data shim 경유 객체 = market 객체 `is` 동일 (사본 금지, SSOT 단일).
  **cold path `.core` 직접 import 우회도 market SSOT 와 `is` 동일 의무** (구현 리뷰 iter1 F-2 —
  data fix PR 재지정 후 cold path 가 `from mctrader_market.aggregation import ...` 경유)
  - 테스트: `tests/test_shim_backcompat.py::test_shim_object_identity`
    (`from mctrader_data.aggregation import TickBarAggregator as A; from mctrader_market.aggregation
    import TickBarAggregator as B; assert A is B`)
  - 테스트 (data fix PR 보강): `tests/test_shim_backcompat.py::test_cold_path_uses_market_sot`
    — `mctrader_data.cold.duckdb_resample.TimeBarAggregator is mctrader_market.aggregation.TimeBarAggregator`
    + `mctrader_data.cold.polars_fallback.TimeBarAggregator is mctrader_market.aggregation.TimeBarAggregator`
    (cold path `.core` 직접 import 사각지대 해소 — 잔존 data 원본 클래스 우회 사용 0 검증)
- **INV-5 [CandleModel 재구현 0]**: engine import 경로만 재지정 (객체·schema 무변경)
  - grep gate: engine `git grep -n "from mctrader_data.cold.duckdb_resample import CandleModel"
    -- 'src/*'` == **0건** AND `mctrader_data.*CandleModel` import == 0
    - 테스트: `tests/test_candlemodel_import_source.py::test_no_mctrader_data_candlemodel_import`
  - CandleModel 사용처(전략·지표·consumer) 신규 실패 0 (객체 동일성 보존)
- **INV-6 [pyarrow writer 무변경]**: data tick_storage/orderbook_storage writer 로직 0 변경
  (dataclass SSOT 만 market 이동) — writer 테스트 회귀 신규 실패 0
  - 테스트: 기존 `tests/test_tick_storage.py` / `tests/test_orderbook_storage.py` green 유지

### 8.2 동등성 회귀 (이전 data 측 테스트 market 이식)

| 이식 원본 (data) | market 이식 대상 | 검증 |
|------------------|------------------|------|
| `tests/` aggregation 테스트 (4 Aggregator + scaled_int + contract_id) | `mctrader-market/tests/test_aggregation_relocated.py` | 입출력 byte-for-byte 동등 (INV-1) |
| `tests/` paper_lineage 테스트 (canonical_jsonl_hash + PaperLineage 직렬화) | `mctrader-market/tests/test_paper_lineage_relocated.py` | 동일 hash + 직렬화 동등 (INV-1) |
| (신규) records dataclass | `mctrader-market/tests/test_records.py` | float-guard 동작 보존 + pyarrow 비결합 (INV-3) |

### 8.3 shim back-compat 테스트 (data#N)

- `tests/test_shim_backcompat.py`:
  - `from mctrader_data.aggregation import <8 심볼>` 각각 `is` market 객체 (INV-4)
  - `from mctrader_data.paper_lineage import PaperLineage, canonical_jsonl_hash` `is` 동일
  - import 시 `DeprecationWarning` emit (`pytest.warns(DeprecationWarning)`)
  - data full suite 회귀 신규 실패 0 (aggregation/lineage/storage 테스트 green 유지)

### 8.4 engine grep gate 테스트 (engine#N)

- `tests/test_candlemodel_import_source.py::test_grep_gate`:
  `git grep -n "mctrader_data.*CandleModel\|from mctrader_data.cold.duckdb_resample import
  CandleModel" -- 'src/*'` == 0 assert (INV-5)
- engine full suite 회귀 — CandleModel 사용처(전략·지표·consumer) 신규 실패 0
- engine 직독 2곳(strategy_reproducibility/realtime aggregator) 무변경 회귀 0

### 8.5 채택/반박

- TestContractArch 6 invariant + Phase 0 Gate + 동등성 회귀 모두 chief author 채택
- Perf Baseline = N/A (§5.1 — relocation, perf 무영향) chief author 채택 (§8.5_active=false 정합)
- market full suite 회귀 신규 실패 0 + data full suite 회귀 신규 실패 0 = DesignReview evidence

## 9. Rollout / Backout

### 9.1 Rollout (cross-repo sequential LAND — land_order 엄수)

```
hub Phase 1 (docs)  →  market#N  →  data#N  →  engine#N  →  hub Phase 2 PR2 (박제)
   (land_order 1)      (order 1)   (order 2)  (order 3)    (박제)
```

1. **hub Phase 1**: Story §1-§11 + ADR-031 publish(Proposed) + scope_manifest + CLAUDE.md +
   counters.json reserve→IN_PROGRESS. CI green 후 admin merge
2. **market#N (order 1)**: aggregation/records/paper_lineage 신규 + candle.py verify-only +
   동등성 테스트. CI green 후 admin merge → 다음 PR
3. **data#N (order 2)**: aggregation/paper_lineage shim + tick_storage/orderbook_storage import
   재지정 + shim back-compat 테스트 + data full suite 회귀 0. CI green 후 admin merge
4. **engine#N (order 3)**: CandleModel import 4곳 재지정 + grep gate 테스트 + engine full suite
   회귀 0. CI green 후 admin merge
5. **hub Phase 2 PR2**: Story §10/§11 박제 + ADR-031 §D1 VERIFIED + scope_manifest milestone 1/7
   + CLAUDE.md COMPLETED + RETRO + EPIC-RESULTS

### 9.2 Cutover 전략

- **무중단** — data shim 이 무중단 back-compat 보장 (기존 data caller 무변경 동작, `is` 동일성).
  market#N LAND 후 data#N shim 이 market 을 re-export → data 내부 사용처 정상 동작
- 각 PR 은 독립 CI green 후 admin merge — land_order 위반 시 import 실패 (data#N 이 market#N
  미LAND 상태에서 merge 되면 `from mctrader_market.aggregation import *` ImportError)

### 9.3 Backout 조건 / 절차

| 시점 | backout |
|------|---------|
| market#N LAND 후 data#N 전 | market revert (신규 모듈 삭제) — data 측 영향 0 (아직 shim 미적용, 기존 data.aggregation 원본 잔존) |
| data#N LAND 후 engine#N 전 | data revert (shim → 원본 복구). market 신규 모듈은 무해 잔존 (아무도 import 안 함 — 순환 0 정합) |
| engine#N LAND 후 | engine revert (import 4곳 원복 → `mctrader_data.cold.duckdb_resample`). data shim 잔존 무해 |
| Phase 0 verify 불일치 (V5 ≠ 4곳) | market#N 착수 전 STOP → ArchitectPL escalate (코드 작업 진입 차단, R1 desync 사전 차단) |

- **rollback 경로 (market revert 시 data shim fallback)**: data#N 가 LAND 된 상태에서 market#N
  revert 필요 시 → data shim 도 동시 revert (shim 원본 복구) 의무. shim 단독 잔존 시
  `from mctrader_market.aggregation import *` ImportError → data 전체 깨짐. **backout 은
  land_order 역순** (engine → data → market) 강제.

## 10. ADR 판단

- **ADR-031 신규 publish (Proposed)** — `docs/adr/ADR-031-data-domain-decoupling.md`. D1-D7 본문
  박제 + 4-Layer 의존 모델 + D-row ↔ scope_manifest 전수 1:1 reconcile 표 + Out-of-scope
  (D2-D5/D7 = MCT-183~188 owner) + Codex 기각 2건(presigned-NAS-handoff / 신규 중립 repo 2개)
- **ADR-029/027/030 amendment = 예고 box only** — 본 Story 는 ADR-031 §D6 amendment 표에 예고만
  박제. ADR-029/027/030 본문 **무변경** (실 amend = MCT-183/184/185/186/188 owner Story)
- **ADR-025 (aggregation-core-lib-contract) 정합** — aggregation SSOT 계보. relocate 는 위치
  이동 + import 경로 재지정이며 ADR-025 의 4 Aggregator/scaled-int/contract_id contract 자체는
  byte-equivalence 보존 (INV-1) — ADR-025 amendment 불요 (위치만 변경, contract 무변경)

## 11. 데이터 마이그레이션 (DataMigrationArchitectAgent 산출)

### 11.1 마이그레이션 분류 (contract relocation = code-level, persisted-data migration 0)

| 분류 | 본 Story | 처리 |
|------|----------|------|
| persisted data (Parquet/DB/NAS object) schema 변경 | **없음** | dataclass 정의 위치만 이동 — pyarrow schema/writer(data 잔류) 무변경. 기존 Parquet/object 무영향 |
| wire/serialization format 변경 | **없음** | `canonical_jsonl_hash` byte-equivalence (INV-1) — 직렬화 출력 동일 |
| code-level contract relocation | **본 Story 본질** | namespace 이동 — §11.2 무결성 invariant |

### 11.2 Integrity invariant (byte-equivalence 무결성 — DataMigrationArch primary)

- **byte-equivalence**: relocate 전후 `canonical_jsonl_hash` 동일 hash + scaled-int round-trip
  (`from_scaled(to_scaled(d))==d`, Decimal drift 0) + 4 Aggregator 출력 byte-for-byte (INV-1).
  relocate ≠ 동작 변경 — 동일 함수 본문 물리 이동이므로 출력 무변경이 무결성 SSOT
- **dataclass field 순서 보존**: TickRecord(8 field)/OrderbookEventRecord(10 field) field
  순서/이름/default = data 원본 byte-for-byte 보존 (pyarrow schema 가 field 순서 의존 —
  순서 변경 시 기존 Parquet 직렬화/역직렬화 깨짐, INV-6). market.records 추출 시 순서 불변 의무
- **shim 무중단 무결성**: shim 경유 객체 `is` market 객체 (INV-4) — 사본 생성 시 SSOT 이중화
  (동일성 깨짐 → 직렬화 hash drift 위험). `from X import *` re-export 강제 (사본 금지)

### 11.3 Cutover 무결성 (cross-repo land_order)

- market#N LAND → data#N shim → engine#N 재지정 순서 엄수 (§9.1). 역순 LAND 시 ImportError
  (data shim 이 미LAND market 참조) — land_order = 무결성 게이트
- data full suite 회귀 신규 실패 0 + market full suite 회귀 신규 실패 0 = 무결성 PASS 기준

### 11.4 Rollback 무결성 (market revert 시 data shim fallback)

- backout 은 **land_order 역순** (engine → data → market) 강제 (§9.3). data#N LAND 후
  market#N 단독 revert 금지 — data shim 이 market re-export 이므로 shim 동시 revert 의무
  (shim 단독 잔존 = ImportError, data 전체 깨짐). DataMigrationArch 무결성 정합 = "shim ↔
  market 원본 동시성 보존"

### 11.5 Idempotency

- **N/A (해당 없음)** — contract relocation 은 1회성 code-level 이동 (재실행 가능한 data
  migration job 아님). cross-repo PR sequential LAND = git merge idempotency (동일 PR 재merge
  = no-op). persisted-data 재처리 경로 부재.

> §11.6 (idempotency CONDITIONAL — DataMigrationArch primary + OperationalRiskArchitect consult):
> 본 Story 는 idempotent 재처리 대상 (background job / data migration job / queue consumer)
> 도입 0 → §11.6 = **N/A**. OperationalRiskArchitect consult 결과 = consult 대상 부재 (relocation
> Story, runtime job 무도입).

### 11.7 N/A (박제)

- persisted-data schema breaking change 0 (pyarrow schema/writer = data 잔류, 무변경)
- RDB 마이그레이션 0 / NAS object layout 변경 0 / wire format 변경 0
- idempotency(§11.5/11.6) = N/A (1회성 code relocation, runtime job 무도입)

## 12. PL 검수 결과

### 12.1 ArchitectPL 1차 검수 (2026-05-16, Iteration 1)

**§섹션별 deputy author input 통합 정합성 (메타-규칙)**:

| §절 | deputy | 통합 정합성 | 판정 |
|-----|--------|-------------|------|
| §2 | CodebaseMapperAgent | verified-via git grep/Read fact (가설 0) — aggregation PURE / dataclass stdlib-only / paper_lineage PURE / engine 4곳 / 순환 0 변호 근거 채택 | ✅ PASS |
| §3·§6 | RefactorAgent | dataclass 추출(pyarrow 비결합) + shim `import *` re-export(is-동일성) + 내부 참조 단순화 — 제안 범위 준수 | ✅ PASS |
| §7 (§7.1-§7.3, §7.5-§7.6) | SecurityArchitectAgent | 신규 trust boundary 0 / attack surface delta 0 간략 declare (relocation Story 약함 정합) | ✅ PASS |
| §7.4 | OperationalRiskArchitectAgent | DR/disconnect/clock/rate-limit/env 5 항목 CONDITIONAL N/A + 사유 박제 + §8.5_active=false 결정 verbatim | ✅ PASS |
| §8 | TestContractArchitectAgent | 6 invariant(byte-equivalence/순환0/pyarrow비결합/is-동일성/CandleModel재구현0/writer무변경) + Phase 0 Gate(조건2) + grep0 gate + Perf N/A — 커버리지 후보 통합 | ✅ PASS |
| §11 (§11.1-§11.5, §11.7) | DataMigrationArchitectAgent | byte-equivalence 무결성 + field 순서 보존 + shim 무중단 + rollback 역순(market revert→data shim fallback) 매핑 반영 | ✅ PASS |
| §11.6 | DataMigrationArch primary + OperationalRiskArch consult | idempotency CONDITIONAL N/A (runtime job 무도입) — consult 대상 부재 박제 | ✅ PASS |

**§섹션 누락 차단**: §7 ✓ §7.4 ✓ §8 ✓ §10 ✓ §11 ✓ — 전 present (DesignReview P0 차단 대상 0)

**조건부 3건 반영 확인 (요구사항 lane verdict)**:
1. engine CandleModel 실측 4곳 SSOT — §2.1/§4.1/§8.0/INV-5 전수 4곳 (가설 5곳 기각 박제) ✓
2. market#N 착수 전 V1 fetch + V5 HEAD 재grep gate — **§8.0 Phase 0 Verify Gate 절 명문화** ✓
3. ADR-031 D1-D7 ↔ scope_manifest 전수 1:1 reconcile — ADR-031 §D-row reconcile 표(7/7) +
   Out-of-scope(D2-D5/D7 owner 명시) ✓

**Deputy 재spawn 이력**: 0회 (6 deputy 1-pass — Phase 0 fact 사전 정합으로 clarification 불요)

- **VERDICT (1차)**: **PASS** → DesignReview lane 진입 요청
- **잔여 risk**: R1 (cross-repo desync 7회째, HIGH) — §8.0 Phase 0 Gate + ADR-031 D-row
  reconcile 로 완화 (V5 사전 정정으로 desync 1건 선제 차단). R2 (MCT-41 블락, HIGH) = MCT-186
  owner (본 Story 파일 disjoint — 병렬 안전, 본 Story 무관)

### 12.2 ArchitectPL 구현 리뷰 FIX 최종 판정 (2026-05-16, 구현 리뷰 iter 1/3)

DeveloperPL 1차 진단 → Orchestrator 경유 → ArchitectPL 최종 판정 (chief judge). evidence pack
독립 검증 (review findings + Change Plan/scope_manifest 정합성, DeveloperPL 진단 미수신 독립 판정):

| finding | severity | 최종 판정 | 근거 |
|---------|----------|-----------|------|
| F-1 (하위모듈 미삭제 — §4.2↔§6/§2.2 self-contradiction) | P1 boundary | **설계 원인** | Change Plan §4.2 "삭제" 단독 stale ↔ §6/§2.2/scope_manifest line 204/ADR-031 line 230 = "MCT-188 D7까지 deprecated 보존" 4개 산출물 수렴. FIX iter1 F-2 가 scope_manifest 만 정정·§4.2 동반 정정 누락 = 설계 lane cross-document 정합 실패 (MCT-179 lesson 동형) |
| F-2 (cold path .core 직접 import — INV-4 위반) | P1 boundary | **설계 원인** | §2.2 가 cold path "shim 경유 무중단 의무" 명세했으나 실제 cold path 는 `.core` 직접 import 상태 (실증: duckdb_resample.py:53 + polars_fallback.py:36). 설계가 §6 "사전 마이그레이션 불요" 로 cold path 예외 미검출 일반화 = Phase 0 verify gap 동형 |
| F-3 (candle_view.py:38 docstring) | P2 비차단 | (downgrade 유지) | docstring noise — fix PR scope 외 |

- **root-cause-decision table 적용**: Code review P1 boundary → 설계 default. DeveloperPL 1차
  가정(설계) = table 정합. **수용 — 반론 없음. 설계 원인 확정.**
- **Option A 채택** (Option B 기각): Option B(하위모듈 즉시 삭제) = cold path ImportError
  (production 파손) + MCT-183/188 owner 경계 침범 (scope creep) 2중 결함 → 사용자 directive
  2026-05-13 (타협 어려운 부분 보수적 평가) 정합, 보수적 기각. Option A = §6/§2.2/scope_manifest/
  ADR-031 무중단 명세 정합 + MCT-182 strangler-fig Layer0 1단계 scope 준수.
- **scope 경계 확정**: MCT-182 owner = cold path 2곳 market 직접 재지정 + test 보강 (INV-4
  is-동일성 위반 즉시 해소). MCT-188 D7 owner = 하위모듈 파일 물리 삭제 + grep0 quad gate.
  MCT-183 owner = 여타 cold path cleanup.
- **Change Plan 정정 (ArchitectAgent 권한)**: §4.2 line 183-184 "하위모듈 삭제" →
  "하위모듈 deprecated 보존 (MCT-188 D7까지) — __init__ shim 만 public API 진입점, cold/
  `.core` 직접 import 는 data fix PR 에서 market 직접 재지정" 정정 완료. §8 INV-4 테스트
  `test_cold_path_uses_market_sot` 보강. §6/§2.2/scope_manifest line 204/ADR-031 line 230
  정합 확인 (cross-document desync 해소). ADR-031 본문 = D1 결정 무변경 (정합 — line 230 이미
  "MCT-188 D7 까지 deprecated 경로 유지" 명세, amend 불요). Story §11 = data 측 shim 기술
  정합 (amend 불요).
- **post-merge fix PR scope 최종안** (data repo 신규 PR, DeveloperPL 스폰 대상):
  1. `src/mctrader_data/cold/duckdb_resample.py:53` — `from mctrader_data.aggregation.core
     import (...)` → `from mctrader_market.aggregation import (...)` 재지정
  2. `src/mctrader_data/cold/polars_fallback.py:36` — `from mctrader_data.aggregation.core
     import TimeBarAggregator` → `from mctrader_market.aggregation import TimeBarAggregator`
  3. `tests/test_shim_backcompat.py` — `test_cold_path_uses_market_sot` 보강 (cold path
     2곳 `is mctrader_market.aggregation.*` SSOT is-동일성 검증, 사각지대 해소)
  - **scope 외 (MCT-188 D7)**: 하위모듈 파일 물리 삭제 / grep0 quad gate
  - **scope 외 (MCT-183)**: paper_storage 등 여타 사용처 (단 — 검증상 paper_storage 는 `__init__`
    shim 경유, 우회 0 — cold/ 2곳만 `.core` 직접 import 실증)
- **VERDICT (구현 리뷰 iter1)**: 설계 원인 → Change Plan 정정 완료 → **post-merge fix PR
  스폰 가능** (Orchestrator → DeveloperPL data fix PR → 구현 리뷰 재검증). 설계 리뷰 레인
  재실행 불요 (Change Plan §4.2 정정 = §6/§2.2 와의 self-contradiction 해소, 신규 설계 결정 0)
