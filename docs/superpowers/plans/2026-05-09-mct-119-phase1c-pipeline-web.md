# Strategy Set Pipeline — Phase 1-C: PipelineRunner + Web UI

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1-B 완료 후 전체 파이프라인을 조율하는 PipelineRunner와 EventStore를 구현하고, mctrader-web에 Strategy Set 관리 UI (FastAPI + Streamlit)를 추가한다.

**Architecture:** `pipeline/runner.py`가 7개 레이어를 순서대로 실행하고 PipelineFrame을 채움. EventStore는 각 레이어 완료 시 DB에 이벤트 기록. mctrader-web에 FastAPI 라우터와 Streamlit 페이지 3개를 추가.

**Tech Stack:** Python 3.12, SQLAlchemy async, FastAPI, Streamlit, pytest

**Repos:** `mctrader-engine` (PipelineRunner, EventStore), `mctrader-web` (API + UI)

**전제:** Phase 1-A + Phase 1-B 완료

---

## 파일 구조

```
[mctrader-engine]
src/mctrader_engine/pipeline/
    runner.py        PipelineRunner — 7-레이어 조율
    event_store.py   EventStore — pipeline_events 테이블 기록

tests/unit/pipeline/
    test_runner.py

[mctrader-web]
src/mctrader_web/api/routes/
    strategy_sets.py     FastAPI 라우터 (/api/v1/strategy-sets/)

src/mctrader_web/pages/
    04_strategy_sets.py     Strategy Set 목록 + 생성
    05_strategy_set_editor.py   편집 UI
    06_strategy_promotion.py    프로모션 워크플로우
```

---

### Task 1: EventStore

**Files:**
- Create: `src/mctrader_engine/pipeline/event_store.py`

- [ ] **Step 1: event_store.py 구현**

`src/mctrader_engine/pipeline/event_store.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from mctrader_engine.db.models.pipeline_event import PipelineEvent
from mctrader_engine.pipeline.types import (
    AggregatedSignal,
    ExecutionPlan,
    PipelineFrame,
    PortfolioPlan,
    RiskDecision,
    Signal,
)


class EventStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_signals_generated(self, frame: PipelineFrame) -> None:
        self._write(
            frame=frame,
            event_type="SignalGenerated",
            payload={"signals": [_signal_to_dict(s) for s in frame.signals]},
        )

    def record_aggregated(self, frame: PipelineFrame) -> None:
        self._write(
            frame=frame,
            event_type="AggregatedSignalCreated",
            payload={"aggregated": [_agg_to_dict(a) for a in frame.aggregated]},
        )

    def record_portfolio_plan(self, frame: PipelineFrame) -> None:
        if frame.portfolio_plan is None:
            return
        self._write(
            frame=frame,
            event_type="PortfolioPlanCreated",
            payload={
                "targets": [
                    {"symbol": t.symbol, "target_weight": str(t.target_weight)}
                    for t in frame.portfolio_plan.targets
                ]
            },
        )

    def record_risk_decision(self, frame: PipelineFrame) -> None:
        if frame.risk_decision is None:
            return
        self._write(
            frame=frame,
            event_type="RiskDecisionCreated",
            payload={
                "allowed": frame.risk_decision.allowed,
                "blocked_reasons": list(frame.risk_decision.blocked_reasons),
                "intents": [
                    {"symbol": i.symbol, "side": i.side, "qty": str(i.quantity)}
                    for i in frame.risk_decision.intents
                ],
            },
        )

    def record_execution_plans(self, frame: PipelineFrame) -> None:
        self._write(
            frame=frame,
            event_type="ExecutionPlanCreated",
            payload={
                "plans": [
                    {
                        "symbol": p.intent.symbol,
                        "side": p.intent.side,
                        "qty": str(p.intent.quantity),
                        "order_type": p.order_type,
                        "tif": p.time_in_force,
                    }
                    for p in frame.execution_plans
                ]
            },
        )

    def _write(self, *, frame: PipelineFrame, event_type: str, payload: dict[str, Any]) -> None:
        event = PipelineEvent(
            id=uuid4(),
            run_id=frame.run_id,
            strategy_set_version_id=frame.strategy_set_version_id,
            frame_id=frame.frame_id,
            event_type=event_type,
            payload=payload,
            idempotency_key=f"{frame.frame_id}:{event_type}",
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(event)


def _signal_to_dict(s: Signal) -> dict[str, Any]:
    return {
        "producer": s.producer_name,
        "symbol": s.symbol,
        "action": s.action,
        "side": s.side,
        "strength": str(s.strength),
        "confidence": str(s.confidence),
        "horizon": s.horizon,
        "reason": s.reason,
        "data_quality": str(s.data_quality_score),
    }


def _agg_to_dict(a: AggregatedSignal) -> dict[str, Any]:
    return {
        "symbol": a.symbol,
        "side": a.side,
        "score": str(a.score),
        "threshold": str(a.threshold),
        "conflict_level": str(a.conflict_level),
        "contributor_count": len(a.contributors),
    }
```

- [ ] **Step 2: Commit**

```bash
cd c:\workspace\mclayer\mctrader-engine
git add src/mctrader_engine/pipeline/event_store.py
git commit -m "feat(pipeline): EventStore — pipeline_events 테이블에 7개 이벤트 타입 기록"
```

---

### Task 2: PipelineRunner

**Files:**
- Create: `src/mctrader_engine/pipeline/runner.py`
- Create: `tests/unit/pipeline/test_runner.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/unit/pipeline/test_runner.py`:

```python
from __future__ import annotations

from collections import namedtuple
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import uuid4

import pytest

from mctrader_engine.pipeline.layers.aggregators import WeightedSumAggregator
from mctrader_engine.pipeline.layers.constructors import EqualWeightConstructor
from mctrader_engine.pipeline.layers.execution_planner import DefaultExecutionPlanner
from mctrader_engine.pipeline.layers.position_manager import DefaultPositionManager
from mctrader_engine.pipeline.layers.risk_constraints import PositionSizeCap
from mctrader_engine.pipeline.runner import PipelineConfig, PipelineRunner
from mctrader_engine.pipeline.types import (
    AccountSnapshot,
    MarketSlice,
    PipelineFrame,
    Signal,
    SignalAction,
)

FakeBar = namedtuple("FakeBar", ["open", "high", "low", "close", "volume"])


def _bar(c):
    v = Decimal(str(c))
    return FakeBar(open=v, high=v + 1, low=v - 1, close=v, volume=Decimal("100"))


class BuyAlwaysProducer:
    name = "buy_always"
    from mctrader_engine.pipeline.protocols import CoveragePolicy, DataTier, TriggerPolicy
    required_data_tiers = frozenset({DataTier.CANDLE})
    trigger_policy = TriggerPolicy.CANDLE_CLOSE
    coverage_policy = CoveragePolicy.SPARSE

    def generate_signals(self, frame: PipelineFrame) -> Sequence[Signal]:
        from mctrader_engine.pipeline.helpers import emit_long
        return [emit_long(frame, producer_name=self.name)]


def _make_frame():
    now = datetime.now(timezone.utc)
    bars = [_bar(100 + i) for i in range(30)]
    return PipelineFrame(
        run_id=uuid4(), strategy_set_version_id=uuid4(), frame_id=uuid4(),
        as_of=now,
        market_slice=MarketSlice(
            as_of=now, symbol="BTCUSDT", symbols=frozenset({"BTCUSDT"}),
            bars={"BTCUSDT": bars}, ticks=None, orderbooks=None,
            freshness={}, watermark=now,
        ),
        account_snapshot=AccountSnapshot(
            ts=now, equity=Decimal("10000"), cash=Decimal("10000"), positions={},
        ),
        open_orders=(), recent_fills=(),
    )


def test_pipeline_runner_produces_execution_plans():
    config = PipelineConfig(
        producers=[BuyAlwaysProducer()],
        aggregator=WeightedSumAggregator(
            weights={"buy_always": Decimal("1.0")},
            threshold=Decimal("0.5"),
        ),
        constructor=EqualWeightConstructor(),
        position_manager=DefaultPositionManager(),
        risk_constraint=PositionSizeCap(max_weight_pct=Decimal("0.5")),
        execution_planner=DefaultExecutionPlanner(),
        event_store=None,
    )
    runner = PipelineRunner(config=config)
    frame = _make_frame()
    result = runner.run(frame)
    assert result.risk_decision is not None
    assert result.risk_decision.allowed


def test_pipeline_runner_blocked_by_risk():
    from mctrader_engine.pipeline.layers.risk_constraints import MaxDrawdownTrip
    from mctrader_engine.pipeline.types import AccountSnapshot

    config = PipelineConfig(
        producers=[BuyAlwaysProducer()],
        aggregator=WeightedSumAggregator(
            weights={"buy_always": Decimal("1.0")},
            threshold=Decimal("0.5"),
        ),
        constructor=EqualWeightConstructor(),
        position_manager=DefaultPositionManager(),
        risk_constraint=MaxDrawdownTrip(max_dd_pct=Decimal("0.05")),
        execution_planner=DefaultExecutionPlanner(),
        event_store=None,
    )
    runner = PipelineRunner(config=config)
    frame = _make_frame()
    # 대폭락 시뮬레이션
    frame.account_snapshot = AccountSnapshot(
        ts=frame.as_of,
        equity=Decimal("9000"),
        cash=Decimal("9000"),
        positions={},
        peak_equity=Decimal("10000"),
    )
    result = runner.run(frame)
    assert result.risk_decision is not None
    assert not result.risk_decision.allowed
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
uv run pytest tests/unit/pipeline/test_runner.py -v 2>&1 | head -20
```

Expected: `ImportError`

- [ ] **Step 3: runner.py 구현**

`src/mctrader_engine/pipeline/runner.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mctrader_engine.pipeline.types import PipelineFrame


@dataclass
class PipelineConfig:
    producers: list[Any]
    aggregator: Any
    constructor: Any
    position_manager: Any
    risk_constraint: Any
    execution_planner: Any
    event_store: Any | None = None


class PipelineRunner:
    def __init__(self, *, config: PipelineConfig) -> None:
        self._config = config

    def run(self, frame: PipelineFrame) -> PipelineFrame:
        cfg = self._config

        # Layer 1: Signal Generation
        for producer in cfg.producers:
            sigs = producer.generate_signals(frame)
            frame.signals.extend(sigs)
        if cfg.event_store:
            cfg.event_store.record_signals_generated(frame)

        # Layer 2: Signal Aggregation
        frame.aggregated = list(cfg.aggregator.aggregate(frame))
        if cfg.event_store:
            cfg.event_store.record_aggregated(frame)

        # Layer 3: Portfolio Construction
        frame.portfolio_plan = cfg.constructor.construct(frame)
        if cfg.event_store:
            cfg.event_store.record_portfolio_plan(frame)

        # Layer 4: Position Management
        frame.rebalance_plans = list(cfg.position_manager.plan_rebalance(frame))

        # Layer 5: Risk Constraint
        frame.risk_decision = cfg.risk_constraint.apply(frame)
        if cfg.event_store:
            cfg.event_store.record_risk_decision(frame)

        # Layer 6: Execution Planning
        if frame.risk_decision and frame.risk_decision.allowed:
            frame.execution_plans = list(cfg.execution_planner.plan(frame))
            if cfg.event_store:
                cfg.event_store.record_execution_plans(frame)

        return frame
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/test_runner.py -v
```

Expected: `2 passed`

- [ ] **Step 5: 전체 pipeline 테스트 통과 확인**

```bash
uv run pytest tests/unit/pipeline/ -v
```

Expected: 전부 pass

- [ ] **Step 6: Commit**

```bash
git add src/mctrader_engine/pipeline/runner.py tests/unit/pipeline/test_runner.py
git commit -m "feat(pipeline): PipelineRunner — 7-레이어 순차 실행 + EventStore 연동"
```

---

### Task 3: pipeline/__init__.py에 Runner + EventStore 추가

**Files:**
- Modify: `src/mctrader_engine/pipeline/__init__.py`

- [ ] **Step 1: 공개 인터페이스에 추가**

기존 `__init__.py` 맨 아래에 추가:

```python
from mctrader_engine.pipeline.runner import PipelineConfig, PipelineRunner
from mctrader_engine.pipeline.event_store import EventStore
```

`__all__`에도 추가:
```python
"PipelineConfig", "PipelineRunner", "EventStore",
```

- [ ] **Step 2: Commit**

```bash
git add src/mctrader_engine/pipeline/__init__.py
git commit -m "chore(pipeline): Runner + EventStore를 공개 인터페이스에 추가"
```

---

### Task 4: mctrader-web FastAPI Strategy Set 라우터

**Files:**
- Create: `src/mctrader_web/api/routes/strategy_sets.py`
- Modify: `src/mctrader_web/api/routes.py` (라우터 등록)

- [ ] **Step 1: strategy_sets.py 구현**

`src/mctrader_web/api/routes/strategy_sets.py`:

```python
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from mctrader_engine.db.models.strategy_set import StrategySet
from mctrader_engine.db.models.strategy_draft import StrategyDraft
from mctrader_engine.db.models.strategy_set_version import StrategySetVersion
from mctrader_engine.db.models.strategy_set_component import StrategySetComponent
from mctrader_engine.db.models.strategy_set_layer import StrategySetLayer
from mctrader_engine.db.models.strategy_promotion_event import StrategyPromotionEvent
from mctrader_engine.pipeline.registry import list_producers

router = APIRouter(prefix="/api/v1/strategy-sets", tags=["strategy-sets"])


# --- Pydantic 모델 ---

class StrategySetCreate(BaseModel):
    name: str
    description: str | None = None
    owner: str | None = None


class DraftUpdate(BaseModel):
    config: dict[str, Any]


class PromotionRequest(BaseModel):
    to_stage: str
    reason: str | None = None
    operator: str | None = None


# --- 엔드포인트 ---

@router.get("")
def list_strategy_sets(db: Session = Depends(get_db)):
    sets = db.query(StrategySet).filter(StrategySet.archived_at.is_(None)).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "owner": s.owner,
            "created_at": s.created_at.isoformat(),
        }
        for s in sets
    ]


@router.post("", status_code=201)
def create_strategy_set(body: StrategySetCreate, db: Session = Depends(get_db)):
    ss = StrategySet(id=uuid4(), name=body.name, description=body.description, owner=body.owner)
    draft = StrategyDraft(
        id=uuid4(), strategy_set_id=ss.id,
        config={"components": [], "layers": []},
    )
    db.add(ss)
    db.add(draft)
    db.commit()
    return {"id": str(ss.id), "name": ss.name}


@router.get("/{set_id}/draft")
def get_draft(set_id: UUID, db: Session = Depends(get_db)):
    draft = db.query(StrategyDraft).filter(StrategyDraft.strategy_set_id == set_id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")
    return {"id": str(draft.id), "config": draft.config, "updated_at": draft.updated_at.isoformat()}


@router.put("/{set_id}/draft")
def update_draft(set_id: UUID, body: DraftUpdate, db: Session = Depends(get_db)):
    draft = db.query(StrategyDraft).filter(StrategyDraft.strategy_set_id == set_id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")
    draft.config = body.config
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"updated": True}


@router.post("/{set_id}/versions", status_code=201)
def create_version(set_id: UUID, db: Session = Depends(get_db)):
    draft = db.query(StrategyDraft).filter(StrategyDraft.strategy_set_id == set_id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")

    canonical = json.dumps(draft.config, sort_keys=True, ensure_ascii=False)
    config_hash = hashlib.sha256(canonical.encode()).hexdigest()

    existing = db.query(StrategySetVersion).filter(
        StrategySetVersion.config_hash == config_hash
    ).first()
    if existing:
        return {"id": str(existing.id), "version": existing.version, "existing": True}

    last = (
        db.query(StrategySetVersion)
        .filter(StrategySetVersion.strategy_set_id == set_id)
        .order_by(StrategySetVersion.version.desc())
        .first()
    )
    next_version = (last.version + 1) if last else 1

    version = StrategySetVersion(
        id=uuid4(),
        strategy_set_id=set_id,
        version=next_version,
        lifecycle_stage="backtest",
        config_hash=config_hash,
        config_canonical=draft.config,
    )
    db.add(version)
    db.commit()
    return {"id": str(version.id), "version": version.version, "existing": False}


@router.get("/{set_id}/versions")
def list_versions(set_id: UUID, db: Session = Depends(get_db)):
    versions = (
        db.query(StrategySetVersion)
        .filter(StrategySetVersion.strategy_set_id == set_id)
        .order_by(StrategySetVersion.version.desc())
        .all()
    )
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "lifecycle_stage": v.lifecycle_stage,
            "config_hash": v.config_hash[:12] + "...",
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/{set_id}/versions/{version_id}/promote", status_code=200)
def promote_version(
    set_id: UUID, version_id: UUID, body: PromotionRequest, db: Session = Depends(get_db)
):
    _STAGE_ORDER = ["backtest", "paper", "live", "archived"]
    version = db.query(StrategySetVersion).filter(StrategySetVersion.id == version_id).first()
    if not version:
        raise HTTPException(404, "Version not found")

    current_idx = _STAGE_ORDER.index(version.lifecycle_stage) if version.lifecycle_stage in _STAGE_ORDER else -1
    target_idx = _STAGE_ORDER.index(body.to_stage) if body.to_stage in _STAGE_ORDER else -1

    if target_idx != current_idx + 1:
        raise HTTPException(400, f"Invalid promotion: {version.lifecycle_stage} → {body.to_stage}")

    event = StrategyPromotionEvent(
        id=uuid4(),
        strategy_set_version_id=version_id,
        from_stage=version.lifecycle_stage,
        to_stage=body.to_stage,
        approved=True,
        operator=body.operator,
        reason=body.reason,
    )
    version.lifecycle_stage = body.to_stage
    db.add(event)
    db.commit()
    return {"promoted": True, "new_stage": body.to_stage}


@router.get("/signal-producers")
def get_signal_producers():
    return [
        {
            "name": p.name,
            "required_data_tiers": list(p.required_data_tiers),
            "trigger_policy": p.trigger_policy,
            "coverage_policy": p.coverage_policy,
            "description": p.docstring,
        }
        for p in list_producers()
    ]


def get_db():
    # mctrader-web의 기존 DB session 주입 패턴에 맞게 연결
    # 기존 코드의 get_db dependency를 import해서 사용
    from mctrader_web.db import get_session
    yield from get_session()
```

- [ ] **Step 2: 기존 routes.py에 라우터 등록**

`src/mctrader_web/api/routes.py`에서 기존 라우터 등록 패턴을 찾아 추가:

```python
from mctrader_web.api.routes.strategy_sets import router as strategy_sets_router

# 기존 include_router 호출들 아래에 추가:
router.include_router(strategy_sets_router)
```

- [ ] **Step 3: 라우터 import 검증**

```bash
cd c:\workspace\mclayer\mctrader-web
uv run python -c "from mctrader_web.api.routes.strategy_sets import router; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_web/api/routes/strategy_sets.py src/mctrader_web/api/routes.py
git commit -m "feat(web/api): Strategy Set CRUD + 프로모션 FastAPI 라우터 추가"
```

---

### Task 5: Streamlit 페이지 3개

**Files:**
- Create: `src/mctrader_web/pages/04_strategy_sets.py`
- Create: `src/mctrader_web/pages/05_strategy_set_editor.py`
- Create: `src/mctrader_web/pages/06_strategy_promotion.py`

- [ ] **Step 1: 04_strategy_sets.py — 목록 + 생성**

`src/mctrader_web/pages/04_strategy_sets.py`:

```python
import streamlit as st
import requests

API = "http://localhost:8000/api/v1"

st.title("Strategy Sets")

# 신규 생성 폼
with st.expander("새 Strategy Set 생성"):
    name = st.text_input("이름")
    description = st.text_area("설명")
    owner = st.text_input("소유자")
    if st.button("생성"):
        resp = requests.post(f"{API}/strategy-sets", json={"name": name, "description": description, "owner": owner})
        if resp.ok:
            st.success(f"생성 완료: {resp.json()['id']}")
            st.rerun()
        else:
            st.error(resp.text)

# 목록
st.subheader("전략 목록")
resp = requests.get(f"{API}/strategy-sets")
if resp.ok:
    sets = resp.json()
    if not sets:
        st.info("등록된 Strategy Set이 없습니다.")
    for s in sets:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{s['name']}** — {s.get('description', '')}")
        col2.write(s.get("owner", ""))
        if col3.button("편집", key=s["id"]):
            st.session_state["editing_set_id"] = s["id"]
            st.switch_page("pages/05_strategy_set_editor.py")
else:
    st.error("API 연결 실패")
```

- [ ] **Step 2: 05_strategy_set_editor.py — 편집 UI**

`src/mctrader_web/pages/05_strategy_set_editor.py`:

```python
import streamlit as st
import requests

API = "http://localhost:8000/api/v1"

st.title("Strategy Set Editor")

set_id = st.session_state.get("editing_set_id")
if not set_id:
    st.warning("Strategy Set을 먼저 선택하세요.")
    st.stop()

# draft 로드
draft_resp = requests.get(f"{API}/strategy-sets/{set_id}/draft")
if not draft_resp.ok:
    st.error("Draft 로드 실패")
    st.stop()

draft = draft_resp.json()
config = draft["config"]

st.subheader("Signal Producers (전략 컴포넌트)")

# 사용 가능한 Producer 목록
producers_resp = requests.get(f"{API}/strategy-sets/signal-producers")
available_producers = producers_resp.json() if producers_resp.ok else []
producer_names = [p["name"] for p in available_producers]

components = config.get("components", [])
updated_components = []
for i, comp in enumerate(components):
    with st.expander(f"Producer: {comp.get('producer_name', '?')}", expanded=True):
        col1, col2 = st.columns([2, 1])
        prod_name = col1.selectbox("전략", producer_names, index=producer_names.index(comp.get("producer_name", producer_names[0])) if comp.get("producer_name") in producer_names else 0, key=f"prod_{i}")
        weight = col2.number_input("가중치", value=float(comp.get("weight", 1.0)), min_value=0.0, key=f"weight_{i}")

        # 선택된 Producer의 CONDITION_DESCRIPTION 표시
        selected = next((p for p in available_producers if p["name"] == prod_name), None)
        if selected and selected.get("description"):
            st.caption(f"설명: {selected['description']}")

        params_str = st.text_area("파라미터 (JSON)", value=str(comp.get("params", {})), key=f"params_{i}")
        enabled = st.checkbox("활성화", value=comp.get("enabled", True), key=f"enabled_{i}")

        updated_components.append({
            "producer_name": prod_name,
            "weight": weight,
            "params": {},
            "enabled": enabled,
        })

if st.button("Producer 추가"):
    updated_components.append({"producer_name": producer_names[0] if producer_names else "", "weight": 1.0, "params": {}, "enabled": True})

st.subheader("Aggregator 설정")
aggregator_type = st.selectbox("방식", ["weighted_sum", "and", "threshold_count"],
                                 index=["weighted_sum", "and", "threshold_count"].index(
                                     config.get("layers", [{}])[0].get("implementation_name", "weighted_sum")
                                     if config.get("layers") else "weighted_sum"
                                 ))

agg_threshold = st.number_input("임계값 (weighted_sum용)", value=1.0, min_value=0.0)

st.subheader("Risk 규칙")
risk_type = st.selectbox("리스크 방식", ["composite", "fixed_sl_tp", "max_drawdown_trip", "position_size_cap"])
sl_pct = st.number_input("손절 % (fixed_sl_tp용)", value=5.0, min_value=0.0) / 100
tp_pct = st.number_input("익절 % (fixed_sl_tp용)", value=10.0, min_value=0.0) / 100
max_dd = st.number_input("최대 드로다운 % (max_drawdown_trip용)", value=15.0, min_value=0.0) / 100

if st.button("저장", type="primary"):
    new_config = {
        "components": updated_components,
        "layers": [
            {
                "layer_type": "signal_aggregation",
                "implementation_name": aggregator_type,
                "params": {"threshold": agg_threshold},
                "ordinal": 0,
            },
            {
                "layer_type": "portfolio_construction",
                "implementation_name": "equal_weight",
                "params": {},
                "ordinal": 0,
            },
            {
                "layer_type": "risk_constraint",
                "implementation_name": risk_type,
                "params": {"sl_pct": sl_pct, "tp_pct": tp_pct, "max_dd_pct": max_dd},
                "ordinal": 0,
            },
        ],
    }
    resp = requests.put(f"{API}/strategy-sets/{set_id}/draft", json={"config": new_config})
    if resp.ok:
        st.success("저장 완료")
    else:
        st.error(resp.text)
```

- [ ] **Step 3: 06_strategy_promotion.py — 프로모션 워크플로우**

`src/mctrader_web/pages/06_strategy_promotion.py`:

```python
import streamlit as st
import requests

API = "http://localhost:8000/api/v1"
STAGE_LABELS = {"backtest": "백테스트", "paper": "페이퍼", "live": "라이브", "archived": "보관"}
STAGE_ORDER = ["backtest", "paper", "live"]

st.title("Strategy Set 프로모션")

set_id = st.session_state.get("editing_set_id")
if not set_id:
    st.warning("Strategy Set을 먼저 선택하세요.")
    st.stop()

st.subheader("버전 목록")
versions_resp = requests.get(f"{API}/strategy-sets/{set_id}/versions")
if not versions_resp.ok:
    st.error("버전 목록 로드 실패")
    st.stop()

versions = versions_resp.json()
if not versions:
    # draft → version 생성
    if st.button("현재 Draft를 버전으로 확정"):
        resp = requests.post(f"{API}/strategy-sets/{set_id}/versions")
        if resp.ok:
            st.success("버전 생성 완료")
            st.rerun()
        else:
            st.error(resp.text)
else:
    for v in versions:
        stage = v["lifecycle_stage"]
        stage_label = STAGE_LABELS.get(stage, stage)
        next_stage = STAGE_ORDER[STAGE_ORDER.index(stage) + 1] if stage in STAGE_ORDER and STAGE_ORDER.index(stage) < len(STAGE_ORDER) - 1 else None

        with st.expander(f"v{v['version']} — {stage_label} ({v['config_hash']})", expanded=(v == versions[0])):
            st.json(v)

            if next_stage:
                next_label = STAGE_LABELS.get(next_stage, next_stage)
                col1, col2 = st.columns([3, 1])
                reason = col1.text_input("사유", key=f"reason_{v['id']}")
                if col2.button(f"→ {next_label}", key=f"promote_{v['id']}"):
                    resp = requests.post(
                        f"{API}/strategy-sets/{set_id}/versions/{v['id']}/promote",
                        json={"to_stage": next_stage, "reason": reason},
                    )
                    if resp.ok:
                        st.success(f"{stage_label} → {next_label} 프로모션 완료")
                        st.rerun()
                    else:
                        st.error(resp.text)
            else:
                st.info("최고 단계 (Live) 또는 보관됨")
```

- [ ] **Step 4: Commit**

```bash
cd c:\workspace\mclayer\mctrader-web
git add src/mctrader_web/pages/04_strategy_sets.py \
        src/mctrader_web/pages/05_strategy_set_editor.py \
        src/mctrader_web/pages/06_strategy_promotion.py
git commit -m "feat(web/ui): Strategy Set 목록/편집/프로모션 Streamlit 페이지 3개 추가"
```
