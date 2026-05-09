# Strategy Set Pipeline — 설계 문서

**날짜:** 2026-05-09  
**상태:** 확정  
**관련 레포:** mctrader-engine · mctrader-web · mctrader-hub  
**대상 스토리:** MCT-119 (Phase 1) · MCT-120 (Phase 2)

---

## 1. 배경과 목적

현재 mctrader의 전략 시스템은 단일 `Strategy.on_bar(ctx) → Decision` 인터페이스로 고정되어 있어 다음 문제가 있다.

- 여러 전략의 신호를 조합할 수 없음 (단일 전략만 실행 가능)
- 파라미터·리스크 규칙이 전략 코드에 혼재 → 가시성 부족
- 어떤 전략이 어떤 조건에서 신호를 냈는지 추적 불가
- 손절/익절/포지션 비중을 전략 외부에서 독립적으로 제어할 방법 없음

이 문서는 **StrategySet Pipeline**으로의 전면 리팩터 설계를 정의한다. 기존 14개 전략 코드는 재사용되지 않으므로 하위 호환성 유지 불필요.

---

## 2. 전체 아키텍처

### 2.1 파이프라인 레이어 (실행 순서)

```
MarketSlice + AccountSnapshot (입력)
        │
        ▼
[1] SignalProducer[]          각 전략이 독립적으로 Signal 생성
        │  Signal(strength, confidence, side, horizon, valid_until)
        ▼
[2] SignalAggregator          신호를 결합 (weighted_sum / and / threshold)
        │  AggregatedSignal(score, side, contributors)
        ▼
[3] PortfolioConstructor      목표 비중 결정 (equal_weight / vol_parity / fixed)
        │  PortfolioPlan(symbol → target_weight)
        ▼
[4] PositionManager           현재 포지션 vs 목표 delta 계산, 리밸런싱 임계값 적용
        │  RebalancePlan(delta_qty, urgency, open_order_adjustment)
        ▼
[5] RiskConstraint            독립 리스크 규칙 적용 (SL/TP/ATR/max_drawdown)
        │  RiskDecision(allowed, OrderIntent[], blocked_reasons)
        ▼
[6] ExecutionPlanner          주문 방식 결정 (order_type, limit_price, ttl, post_only)
        │  ExecutionPlan(OrderIntent + 실행 파라미터)
        ▼
[7] Executor                  실행 (Backtest / Paper / Live)
        │
        ▼
[8] EventStore                모든 레이어 출력을 이벤트로 저장 (감사 추적)
```

### 2.2 레포 역할

| 레포 | 책임 |
|---|---|
| `mctrader-engine` | 레이어 1~8 구현, SignalProducer 전략 구현체 |
| `mctrader-hub` | DB 스키마 마이그레이션, StrategySet RDB 모델, Story |
| `mctrader-web` | Strategy Set 편집 UI (Streamlit), 프로모션 워크플로우 |

---

## 3. 핵심 데이터 모델

### 3.1 MarketSlice (파이프라인 입력)

```python
@dataclass(frozen=True)
class DataFreshness:
    lag_ms: int
    sequence_gap: bool
    is_stale: bool

@dataclass(frozen=True)
class MarketSlice:
    as_of: datetime
    symbol: str                                    # 주 심볼
    symbols: frozenset[str]                        # 관련 심볼 전체 (cross-symbol용)
    bars: Mapping[str, BarWindow]                  # symbol → OHLCV window
    ticks: Mapping[str, TickWindow] | None
    orderbooks: Mapping[str, OrderBookSnapshot] | None
    freshness: Mapping[str, DataFreshness]
    watermark: datetime                            # 가장 오래된 데이터 기준 시각
```

### 3.2 Signal

```python
class SignalAction(str, Enum):
    ENTER = "enter"
    INCREASE = "increase"
    DECREASE = "decrease"
    EXIT = "exit"
    HOLD = "hold"
    NO_VIEW = "no_view"       # 이 전략은 이 심볼에 의견 없음

@dataclass(frozen=True)
class Signal:
    producer_name: str
    symbol: str
    action: SignalAction
    side: Literal["buy", "sell", "flat"]
    strength: Decimal          # 0..1 정규화된 확신의 크기 (포지션 크기 아님)
    confidence: Decimal        # 0..1
    horizon: str               # "1m" | "5m" | "1h" | "1d"
    valid_until: datetime
    reason: str | None
    data_quality_score: Decimal  # 0..1, 데이터 신선도 반영
    execution_hint: ExecutionHint | None  # 선택적 실행 힌트
    metadata: Mapping[str, Any] | None
```

### 3.3 AggregatedSignal → PortfolioPlan → RebalancePlan → RiskDecision → OrderIntent

```python
@dataclass(frozen=True)
class AggregatedSignal:
    symbol: str
    side: Literal["buy", "sell", "flat"]
    score: Decimal              # signed, 음수 = sell
    threshold: Decimal
    horizon_bucket: str
    conflict_level: Decimal     # 0..1, 신호 불일치 정도
    contributors: tuple[Signal, ...]

@dataclass(frozen=True)
class PortfolioTarget:
    symbol: str
    target_weight: Decimal      # NAV 대비 목표 비중
    target_notional: Decimal | None

@dataclass(frozen=True)
class PortfolioPlan:
    ts: datetime
    targets: tuple[PortfolioTarget, ...]

@dataclass(frozen=True)
class RebalancePlan:
    symbol: str
    current_qty: Decimal
    target_qty: Decimal
    delta_qty: Decimal
    urgency: Literal["immediate", "normal", "passive"]
    reason: str | None

@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: Decimal
    limit_price: Decimal | None
    valid_until: datetime
    generated_at: datetime
    reason: str | None

@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    intents: tuple[OrderIntent, ...]
    blocked_reasons: tuple[str, ...]
    adjusted_reasons: tuple[str, ...]
```

### 3.4 PipelineFrame (레이어 간 공유 컨텍스트)

```python
@dataclass
class PipelineFrame:
    run_id: UUID
    strategy_set_version_id: UUID
    frame_id: UUID
    as_of: datetime
    market_slice: MarketSlice
    account_snapshot: AccountSnapshot
    open_orders: tuple[OpenOrder, ...]
    recent_fills: tuple[Fill, ...]
    # 각 레이어가 결과를 여기에 추가
    signals: list[Signal] = field(default_factory=list)
    aggregated: list[AggregatedSignal] = field(default_factory=list)
    portfolio_plan: PortfolioPlan | None = None
    rebalance_plans: list[RebalancePlan] = field(default_factory=list)
    risk_decision: RiskDecision | None = None
    execution_plans: list[ExecutionPlan] = field(default_factory=list)
```

---

## 4. 레이어 프로토콜

```python
class SignalProducer(Protocol):
    name: ClassVar[str]
    required_data_tiers: ClassVar[frozenset[DataTier]]
    trigger_policy: ClassVar[TriggerPolicy]      # candle_close | tick_batch | orderbook_change
    coverage_policy: ClassVar[str]               # "sparse" | "full_universe" | "held_positions_only"

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]: ...


class SignalAggregator(Protocol):
    name: ClassVar[str]
    def aggregate(self, frame: PipelineFrame) -> Sequence[AggregatedSignal]: ...


class PortfolioConstructor(Protocol):
    name: ClassVar[str]
    def construct(self, frame: PipelineFrame) -> PortfolioPlan: ...


class PositionManagerProtocol(Protocol):
    name: ClassVar[str]
    def plan_rebalance(self, frame: PipelineFrame) -> Sequence[RebalancePlan]: ...


class RiskConstraint(Protocol):
    name: ClassVar[str]
    def apply(self, frame: PipelineFrame) -> RiskDecision: ...


class ExecutionPlannerProtocol(Protocol):
    name: ClassVar[str]
    def plan(self, frame: PipelineFrame) -> Sequence[ExecutionPlan]: ...
```

### 4.1 내장 SignalAggregator 구현체

| 이름 | 동작 | 파라미터 |
|---|---|---|
| `weighted_sum` | 각 Producer 신호를 가중합, 임계점 초과 시 통과 | `weights: {name: float}`, `threshold: float` |
| `and` | 지정된 Producer 모두 같은 방향일 때만 통과 | `required: [name, ...]` |
| `threshold_count` | N개 이상의 Producer가 같은 방향이면 통과 | `min_count: int` |

### 4.2 내장 PortfolioConstructor 구현체

| 이름 | 동작 |
|---|---|
| `equal_weight` | 활성 신호 심볼을 균등 배분 |
| `fixed_weight` | 설정된 심볼별 고정 비중 사용 |
| `volatility_parity` | ATR 역수 기반 비중 결정 |

### 4.3 내장 RiskConstraint 구현체

| 이름 | 동작 | 파라미터 |
|---|---|---|
| `fixed_sl_tp` | 고정가 손절/익절 | `sl_pct`, `tp_pct` |
| `atr_sl` | ATR 배수 기반 손절 | `atr_multiplier`, `period` |
| `max_drawdown_trip` | 포트폴리오 DD 한도 초과 시 전체 차단 | `max_dd_pct` |
| `position_size_cap` | 심볼당 최대 비중 제한 | `max_weight_pct` |
| `composite` | 여러 RiskConstraint 순차 적용 | `constraints: [...]` |

---

## 5. StrategySet 라이프사이클

```
draft → backtest → paper → live → archived
```

- **draft**: Web UI에서 편집 중인 mutable 상태. `strategy_drafts` 테이블.
- **backtest**: WFO 또는 단순 백테스트 실행 완료. `strategy_set_versions` 생성.
- **paper**: 가상 포트폴리오로 실시간 실행 중.
- **live**: 실제 자금 운용 중. config_hash + promotion_event FK 필수.
- **archived**: 더 이상 사용하지 않음.

**불변성 규칙:** `strategy_set_versions` 행은 생성 후 수정 불가. 파라미터 변경 = 새 version 생성. 단, 운영 제한(`max_notional_cap`, `kill_switch`)은 `strategy_runtime_overrides` 테이블에서 mutable 관리.

---

## 6. DB 스키마

```sql
CREATE SCHEMA IF NOT EXISTS engine;

-- 전략 묶음 (논리 단위)
CREATE TABLE engine.strategy_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    owner VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ
);

-- UI 편집 중인 mutable draft
CREATE TABLE engine.strategy_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_id UUID NOT NULL REFERENCES engine.strategy_sets(id),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(128),
    UNIQUE (strategy_set_id)
);

-- 프로모션 후보 확정된 immutable 버전
CREATE TABLE engine.strategy_set_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_id UUID NOT NULL REFERENCES engine.strategy_sets(id),
    version INTEGER NOT NULL,
    lifecycle_stage VARCHAR(16) NOT NULL
        CHECK (lifecycle_stage IN ('backtest','paper','live','archived')),
    config_hash CHAR(64) NOT NULL,
    config_canonical JSONB NOT NULL,          -- hash 원본 보존
    created_from_version_id UUID REFERENCES engine.strategy_set_versions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by VARCHAR(128),
    locked_at TIMESTAMPTZ,
    UNIQUE (strategy_set_id, version),
    UNIQUE (config_hash)
);

-- 버전에 속한 SignalProducer 목록
CREATE TABLE engine.strategy_set_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_version_id UUID NOT NULL
        REFERENCES engine.strategy_set_versions(id) ON DELETE CASCADE,
    producer_name VARCHAR(128) NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    params_hash CHAR(64) NOT NULL,
    weight NUMERIC(20,10) NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT true,
    ordinal INTEGER NOT NULL DEFAULT 0,
    UNIQUE (strategy_set_version_id, producer_name)
);

-- 버전에 속한 레이어 설정 (Aggregator / Constructor / PositionManager / Risk / ExecutionPlanner)
CREATE TABLE engine.strategy_set_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_version_id UUID NOT NULL
        REFERENCES engine.strategy_set_versions(id) ON DELETE CASCADE,
    layer_type VARCHAR(32) NOT NULL
        CHECK (layer_type IN (
            'signal_aggregation','portfolio_construction',
            'position_management','risk_constraint','execution_planning'
        )),
    implementation_name VARCHAR(128) NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    params_hash CHAR(64) NOT NULL,
    ordinal INTEGER NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (strategy_set_version_id, layer_type, ordinal)
);

-- 실행 이력 (기존 strategy_runs 확장)
CREATE TABLE engine.strategy_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_version_id UUID
        REFERENCES engine.strategy_set_versions(id),
    mode VARCHAR(16) NOT NULL CHECK (mode IN ('backtest','paper','live')),
    status VARCHAR(16) NOT NULL
        CHECK (status IN ('pending','running','completed','failed','cancelled')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    engine_version VARCHAR(64),
    input_data_version VARCHAR(64),
    result_summary JSONB
);

-- 프로모션 이벤트 (감사 추적)
CREATE TABLE engine.strategy_promotion_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_version_id UUID NOT NULL
        REFERENCES engine.strategy_set_versions(id),
    from_stage VARCHAR(16) NOT NULL,
    to_stage VARCHAR(16) NOT NULL,
    approved BOOLEAN NOT NULL,
    evidence_run_id UUID REFERENCES engine.strategy_runs(id),
    gate_result_snapshot JSONB,
    operator VARCHAR(128),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 운영 제한 (mutable, alpha config와 분리)
CREATE TABLE engine.strategy_runtime_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_set_version_id UUID NOT NULL
        REFERENCES engine.strategy_set_versions(id),
    max_notional_cap NUMERIC,
    kill_switch BOOLEAN NOT NULL DEFAULT false,
    symbol_denylist TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(128),
    UNIQUE (strategy_set_version_id)
);

-- 파이프라인 이벤트 저장 (EventStore)
CREATE TABLE engine.pipeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES engine.strategy_runs(id),
    strategy_set_version_id UUID REFERENCES engine.strategy_set_versions(id),
    frame_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,   -- SignalGenerated | RiskDecisionCreated | OrderIntentCreated | ...
    payload JSONB NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 인덱스
CREATE INDEX ON engine.strategy_set_versions(strategy_set_id, lifecycle_stage);
CREATE INDEX ON engine.strategy_set_components(strategy_set_version_id);
CREATE INDEX ON engine.strategy_set_layers(strategy_set_version_id, layer_type);
CREATE INDEX ON engine.strategy_runs(strategy_set_version_id, mode, status);
CREATE INDEX ON engine.strategy_promotion_events(strategy_set_version_id, created_at DESC);
CREATE INDEX ON engine.pipeline_events(run_id, frame_id);
CREATE INDEX ON engine.pipeline_events(event_type, created_at DESC);
CREATE INDEX ON engine.strategy_set_components USING GIN (params);
CREATE INDEX ON engine.strategy_set_layers USING GIN (params);
```

---

## 7. Web UI (mctrader-web)

Streamlit 기반. 기존 패널 구조(`pages/`) 확장.

### 추가 페이지

| 파일 | 내용 |
|---|---|
| `pages/04_strategy_sets.py` | Strategy Set 목록, 생성/편집/삭제 |
| `pages/05_strategy_set_editor.py` | Producer 추가·가중치, Aggregator 선택, Risk 규칙 설정 |
| `pages/06_strategy_promotion.py` | draft → backtest → paper → live 프로모션 워크플로우 |

### API 엔드포인트 (FastAPI, `/api/v1/strategy-sets/`)

```
GET    /strategy-sets                    목록
POST   /strategy-sets                    생성
GET    /strategy-sets/{id}/draft         draft 조회
PUT    /strategy-sets/{id}/draft         draft 수정 (자동저장)
POST   /strategy-sets/{id}/versions      draft → version 확정
GET    /strategy-sets/{id}/versions      version 목록
POST   /strategy-sets/{id}/versions/{vid}/promote   프로모션 요청
GET    /strategy-sets/{id}/versions/{vid}/runs       실행 이력
GET    /signal-producers                 사용 가능한 Producer 목록 (name, params_schema)
GET    /aggregators                      사용 가능한 Aggregator 목록
GET    /risk-constraints                 사용 가능한 RiskConstraint 목록
```

### UI 핵심 기능

1. **Producer 카탈로그** — 등록된 SignalProducer 목록, 파라미터 JSON Schema 기반 폼
2. **Aggregator 선택** — `weighted_sum` / `and` / `threshold_count`, 파라미터 인라인 편집
3. **Risk 규칙 빌더** — 여러 constraint 순서대로 적층, 각 규칙 파라미터 편집
4. **전략 조건 투명성** — 선택된 Producer의 entry/exit 조건 텍스트 설명 표시 (`__doc__` + `CONDITION_DESCRIPTION` 클래스 변수)
5. **프로모션 워크플로우** — 단계별 게이트 결과 표시, 승인 버튼

---

## 8. mctrader-engine 전략 마이그레이션

기존 14개 전략을 `SignalProducer.generate_signals(frame) → Signal[]` 인터페이스로 재작성.

### 전략별 trigger_policy

| 전략 | trigger_policy |
|---|---|
| sma_v1, ema_cross_v1, macd_cross_v1, donchian_breakout_v1, rsi_bounds_v1, bollinger_reversion_v1, zscore_reversion_v1, atr_breakout_v1, keltner_breakout_v1, roc_threshold_v1, vwap_cross_v1 | `candle_close` |
| market_making_v1, tick_scalping_v1 | `tick_batch` |
| book_imbalance_breakout_v1 | `orderbook_change` |

### helper API (전략 작성자용)

```python
# 단순 전략 작성 시 사용하는 헬퍼
def emit_long(frame, strength=1.0, confidence=0.8, horizon="1h", reason=None) -> Signal
def emit_short(frame, strength=1.0, confidence=0.8, horizon="1h", reason=None) -> Signal
def emit_flat(frame, reason=None) -> Signal
def emit_no_view(frame) -> Signal
```

### CONDITION_DESCRIPTION 규약

각 SignalProducer 클래스에 조건 투명성을 위한 클래스 변수 선언:

```python
class EMACrossProducer:
    name = "ema_cross_v1"
    CONDITION_DESCRIPTION = {
        "entry_long": "fast EMA crosses above slow EMA",
        "entry_short": "fast EMA crosses below slow EMA",
        "exit": "cross reverses or signal expires",
    }
```

---

## 9. Phase 2 — 추가 레이어 (다음 스펙)

| 레이어 | 설명 |
|---|---|
| `CostModel` | maker/taker fee, funding fee, spread 추정. PortfolioConstructor가 cost-adjusted net edge 기반 결정 |
| `ExchangeConstraintValidator` | min qty, tick size, lot size, leverage cap 검증. RiskDecision 후 재검증 |
| `Monitoring / Alert` | pipeline latency, signal anomaly, paper/live divergence 추적 |
| `HotSwap / Handover` | 24/7 환경에서 version 전환 시 `prepare → shadow → compare → handover → activate → retire` |
| `SignalGroup` | 페어트레이딩 등 atomic multi-leg 신호 (`atomicity: all_or_none`) |

---

## 10. 테스트 전략

| 레이어 | 테스트 방법 |
|---|---|
| SignalProducer | 각 전략 unit test: 알려진 OHLCV 입력 → 예상 Signal 검증 |
| SignalAggregator | weighted_sum / and / threshold_count 결합 로직 unit test |
| PortfolioConstructor | equal_weight / vol_parity 비중 계산 unit test |
| PositionManager | delta 계산, 리밸런싱 임계값 unit test |
| RiskConstraint | SL/TP/ATR/drawdown 각각 unit test, composite 순서 검증 |
| Pipeline (통합) | 전체 파이프라인 backtest mode 통합 테스트 (기존 WFO 테스트 대체) |
| Web API | FastAPI TestClient로 CRUD + 프로모션 엔드포인트 검증 |
| DB 마이그레이션 | Alembic migration up/down 멱등성 검증 |

---

## 11. 구현 순서

```
Phase 1-A (병렬 가능):
  ├── mctrader-hub:  DB 스키마 마이그레이션 (Alembic)
  ├── mctrader-engine: 핵심 데이터 모델 + 레이어 Protocol 정의
  └── mctrader-web:  FastAPI 엔드포인트 스켈레톤

Phase 1-B (1-A 완료 후):
  ├── mctrader-engine: 14개 전략 → SignalProducer 재구현
  ├── mctrader-engine: 내장 Aggregator / Constructor / PositionManager / Risk / ExecutionPlanner 구현
  └── mctrader-engine: PipelineRunner (전체 레이어 조합 실행)

Phase 1-C (1-B 완료 후):
  ├── mctrader-engine: Backtest / Paper / Live Executor를 새 파이프라인에 연결
  ├── mctrader-web:  Strategy Set 편집 UI + 프로모션 워크플로우 UI
  └── 통합 테스트

Phase 2:
  CostModel → ExchangeConstraintValidator → Monitoring → HotSwap → SignalGroup
```
