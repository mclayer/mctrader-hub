# RDB Phase 2-5: Engine + Web Schemas

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add engine schema (strategy_runs, backtest_results, alerts, engine_status, orders, fills, positions) and web schema (dashboard_configs, notification_channels, notification_dispatches) to the shared PostgreSQL. Wire CLI to record runs, results, alerts, orders, and position snapshots post-execution.

**Architecture:** mctrader-engine owns the `engine` schema via Alembic; mctrader-web owns the `web` schema. All DB writes are in the CLI layer (post-run), not in executor internals — this keeps trading logic DB-free and allows graceful degradation when `DATABASE_URL` is unset. SQLite paper ledger remains the append-only source of truth; PostgreSQL orders/fills are a read-model projection.

**Tech Stack:** SQLAlchemy 2.x, Alembic 1.13+, psycopg[binary] 3.x, PostgreSQL 16. **Prerequisite:** Phase 1 plan complete (postgres running, mctrader_net up, DATABASE_URL in engine/web compose).

**Key wiring files (engine):**
- `src/mctrader_engine/cli.py` — backtest() L101-141, paper_start() L189-296
- `src/mctrader_engine/report/schema.py` — ExecutionReport, SummaryStats, RiskGateEvent, OrderEvent
- `src/mctrader_engine/report/equity.py` — EquityRowModel (fields: ts_utc, equity, position_quantity, realized_pnl, unrealized_pnl, cash)

---

## File Map

### mctrader-engine (all new unless noted)
- MODIFY `pyproject.toml` — add sqlalchemy, alembic, psycopg, integration marker
- CREATE `src/mctrader_engine/db/__init__.py`
- CREATE `src/mctrader_engine/db/engine.py` — make_engine, make_session_factory
- CREATE `src/mctrader_engine/db/models/__init__.py` — Base
- CREATE `src/mctrader_engine/db/models/strategy_run.py` — StrategyRun
- CREATE `src/mctrader_engine/db/models/backtest_result.py` — BacktestResult
- CREATE `src/mctrader_engine/db/models/alert.py` — Alert
- CREATE `src/mctrader_engine/db/models/engine_status_rec.py` — EngineStatusRecord
- CREATE `src/mctrader_engine/db/models/order.py` — Order
- CREATE `src/mctrader_engine/db/models/fill.py` — Fill
- CREATE `src/mctrader_engine/db/models/position.py` — Position
- CREATE `src/mctrader_engine/db/run_store.py` — service-layer helpers for all DB writes
- CREATE `alembic.ini`
- CREATE `alembic/env.py`
- CREATE `alembic/versions/0001_engine_schema.py` — all 7 engine tables
- MODIFY `src/mctrader_engine/cli.py` — wire DB calls in backtest() and paper_start()
- CREATE `tests/test_engine_db.py` — integration tests

### mctrader-web (all new unless noted)
- MODIFY `pyproject.toml` — add sqlalchemy, alembic, psycopg, integration marker
- CREATE `src/mctrader_web/db/__init__.py`
- CREATE `src/mctrader_web/db/engine.py`
- CREATE `src/mctrader_web/db/models/__init__.py` — Base
- CREATE `src/mctrader_web/db/models/dashboard_config.py`
- CREATE `src/mctrader_web/db/models/notification_channel.py`
- CREATE `src/mctrader_web/db/models/notification_dispatch.py`
- CREATE `alembic.ini`
- CREATE `alembic/env.py`
- CREATE `alembic/versions/0001_web_schema.py` — 3 web tables
- CREATE `tests/test_web_db.py` — integration tests

---

## Task 1: mctrader-engine DB Dependencies

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-engine/pyproject.toml`

- [ ] **Step 1: Add dependencies**

```bash
cd c:/workspace/mclayer/mctrader-engine
uv add "sqlalchemy>=2.0,<3" "alembic>=1.13" "psycopg[binary]>=3.1"
```

- [ ] **Step 2: Add integration pytest marker to pyproject.toml**

Edit `[tool.pytest.ini_options]` to add:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers"
asyncio_mode = "auto"
markers = [
    "integration: tests requiring a running PostgreSQL instance (set TEST_DATABASE_URL)",
]
```

- [ ] **Step 3: Verify**

```bash
cd c:/workspace/mclayer/mctrader-engine
uv run python -c "import sqlalchemy, alembic, psycopg; print(sqlalchemy.__version__)"
```

Expected: prints `2.x.x`

- [ ] **Step 4: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-engine add pyproject.toml uv.lock
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(db): add sqlalchemy + alembic + psycopg dependencies [MCT-105]"
```

---

## Task 2: Engine SQLAlchemy Models

**Files:**
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/__init__.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/__init__.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/strategy_run.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/backtest_result.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/alert.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/engine_status_rec.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/order.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/fill.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/position.py`
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/engine.py`
- Create: `c:/workspace/mclayer/mctrader-engine/tests/test_engine_db.py`

- [ ] **Step 1: Write the failing test**

Create `c:/workspace/mclayer/mctrader-engine/tests/test_engine_db.py`:

```python
"""Integration tests for engine schema models — requires running postgres.

Run with:
    TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
    uv run pytest tests/test_engine_db.py -v -m integration
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test",
)


@pytest.fixture(scope="module")
def engine():
    from mctrader_engine.db.models import Base

    eng = create_engine(
        TEST_URL,
        connect_args={"options": "-csearch_path=engine,public"},
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def _run_id() -> str:
    return str(uuid.uuid4())


def test_strategy_run_insert_and_query(db: Session) -> None:
    from mctrader_engine.db.models.strategy_run import StrategyRun

    rid = _run_id()
    run = StrategyRun(
        id=rid,
        strategy_name="sma",
        mode="backtest",
        status="running",
        params={"fast": 5, "slow": 20},
        engine_id=f"backtest-{rid}",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()

    result = db.query(StrategyRun).filter_by(id=rid).first()
    assert result is not None
    assert result.strategy_name == "sma"
    assert result.mode == "backtest"
    assert result.params == {"fast": 5, "slow": 20}


def test_backtest_result_fk_to_run(db: Session) -> None:
    from mctrader_engine.db.models.backtest_result import BacktestResult
    from mctrader_engine.db.models.strategy_run import StrategyRun

    rid = _run_id()
    db.add(StrategyRun(
        id=rid, strategy_name="sma", mode="backtest", status="completed",
        params={}, started_at=datetime.now(timezone.utc),
    ))
    db.flush()

    result = BacktestResult(
        run_id=rid,
        total_pnl=Decimal("150000"),
        sharpe_ratio=Decimal("1.23"),
        max_drawdown=Decimal("0.08"),
        total_trades=42,
        win_rate=Decimal("0.55"),
    )
    db.add(result)
    db.flush()

    r = db.query(BacktestResult).filter_by(run_id=rid).first()
    assert r is not None
    assert r.sharpe_ratio == Decimal("1.23")
    assert r.total_trades == 42


def test_alert_nullable_run_id(db: Session) -> None:
    from mctrader_engine.db.models.alert import Alert

    alert = Alert(
        run_id=None,
        symbol="KRW-BTC",
        severity="critical",
        alert_type="kill_switch",
        message="Hard stop triggered: drawdown exceeded 10%",
        triggered_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    db.flush()

    r = db.query(Alert).filter_by(alert_type="kill_switch").first()
    assert r is not None
    assert r.acknowledged_at is None


def test_order_and_fill_relationship(db: Session) -> None:
    from mctrader_engine.db.models.fill import Fill
    from mctrader_engine.db.models.order import Order
    from mctrader_engine.db.models.strategy_run import StrategyRun

    rid = _run_id()
    oid = _run_id()
    fid = _run_id()
    db.add(StrategyRun(
        id=rid, strategy_name="sma", mode="paper", status="running",
        params={}, started_at=datetime.now(timezone.utc),
    ))
    db.flush()

    db.add(Order(
        id=oid, run_id=rid, exchange="bithumb", symbol="KRW-BTC",
        side="buy", order_type="market", quantity=Decimal("0.001"),
        status="filled", created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ))
    db.flush()

    db.add(Fill(
        id=fid, order_id=oid,
        price=Decimal("95000000"), quantity=Decimal("0.001"),
        fee=Decimal("380"), filled_at=datetime.now(timezone.utc),
    ))
    db.flush()

    o = db.query(Order).filter_by(id=oid).first()
    assert o is not None
    f = db.query(Fill).filter_by(order_id=oid).first()
    assert f is not None
    assert f.price == Decimal("95000000")


def test_position_nullable_avg_cost(db: Session) -> None:
    from mctrader_engine.db.models.position import Position
    from mctrader_engine.db.models.strategy_run import StrategyRun

    rid = _run_id()
    db.add(StrategyRun(
        id=rid, strategy_name="sma", mode="backtest", status="completed",
        params={}, started_at=datetime.now(timezone.utc),
    ))
    db.flush()

    pos = Position(
        run_id=rid,
        symbol="KRW-BTC",
        quantity=Decimal("0.005"),
        avg_cost=None,
        snapshot_at=datetime.now(timezone.utc),
    )
    db.add(pos)
    db.flush()

    r = db.query(Position).filter_by(run_id=rid).first()
    assert r is not None
    assert r.quantity == Decimal("0.005")
    assert r.avg_cost is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:/workspace/mclayer/mctrader-engine
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_engine_db.py -v -m integration
```

Expected: `ImportError` — db package doesn't exist yet.

- [ ] **Step 3: Write db/__init__.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/__init__.py`:

```python
"""PostgreSQL operational DB layer for mctrader-engine (engine schema)."""
```

- [ ] **Step 4: Write db/models/__init__.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/__init__.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 5: Write db/models/strategy_run.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/strategy_run.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import TIMESTAMP, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class StrategyRun(Base):
    __tablename__ = "strategy_runs"
    __table_args__ = {"schema": "engine"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String(128))
    mode: Mapped[str] = mapped_column(String(16))          # backtest/paper/live
    status: Mapped[str] = mapped_column(String(16))        # pending/running/completed/failed
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    engine_id: Mapped[Optional[str]] = mapped_column(String(128))
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    )
```

- [ ] **Step 6: Write db/models/backtest_result.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/backtest_result.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    __table_args__ = {"schema": "engine"}

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("engine.strategy_runs.id"), nullable=False
    )
    total_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    total_trades: Mapped[Optional[int]] = mapped_column(Integer)
    win_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    params_hash: Mapped[Optional[str]] = mapped_column(String(64))
    computed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 7: Write db/models/alert.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/alert.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "engine"}

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("engine.strategy_runs.id"), nullable=True
    )
    symbol: Mapped[Optional[str]] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))      # info/warning/critical
    alert_type: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 8: Write db/models/engine_status_rec.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/engine_status_rec.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class EngineStatusRecord(Base):
    __tablename__ = "engine_status"
    __table_args__ = {"schema": "engine"}

    engine_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 9: Write db/models/order.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/order.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "engine"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("engine.strategy_runs.id"), nullable=True
    )
    exchange: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(8))           # buy/sell
    order_type: Mapped[str] = mapped_column(String(16))    # limit/market
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    status: Mapped[str] = mapped_column(String(16))
    exchange_order_id: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 10: Write db/models/fill.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/fill.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Fill(Base):
    __tablename__ = "fills"
    __table_args__ = {"schema": "engine"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("engine.orders.id"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    fee: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=Decimal("0"))
    filled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 11: Write db/models/position.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/models/position.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = {"schema": "engine"}

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("engine.strategy_runs.id"), nullable=True
    )
    symbol: Mapped[str] = mapped_column(String(32))
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    avg_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    snapshot_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 12: Write db/engine.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/engine.py`:

```python
from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str | None = None, schema: str = "engine") -> Engine:
    resolved = url or os.environ["DATABASE_URL"]
    return create_engine(
        resolved,
        connect_args={"options": f"-csearch_path={schema},public"},
    )


def make_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine or make_engine())
```

- [ ] **Step 13: Run tests to verify they pass**

```bash
cd c:/workspace/mclayer/mctrader-engine
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_engine_db.py -v -m integration
```

Expected: 5 tests PASSED.

- [ ] **Step 14: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-engine add \
  src/mctrader_engine/db/ \
  tests/test_engine_db.py
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(db): SQLAlchemy models for engine schema (7 tables) [MCT-105]"
```

---

## Task 3: Engine run_store.py (Service Layer)

**Files:**
- Create: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/run_store.py`

- [ ] **Step 1: Write run_store.py**

Create `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/db/run_store.py`:

```python
"""Service-layer helpers for recording run lifecycle, results, alerts, orders, fills, positions.

All functions accept an open Session and commit nothing — callers commit.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from .models.alert import Alert
from .models.backtest_result import BacktestResult
from .models.engine_status_rec import EngineStatusRecord
from .models.fill import Fill
from .models.order import Order
from .models.position import Position
from .models.strategy_run import StrategyRun


def record_run_start(
    session: Session,
    run_id: str,
    strategy_name: str,
    mode: str,
    params: dict[str, Any],
    engine_id: str | None = None,
) -> None:
    session.merge(
        StrategyRun(
            id=run_id,
            strategy_name=strategy_name,
            mode=mode,
            status="running",
            params=params,
            engine_id=engine_id,
            started_at=datetime.now(timezone.utc),
        )
    )


def update_run_completed(session: Session, run_id: str) -> None:
    run = session.query(StrategyRun).filter_by(id=run_id).first()
    if run is not None:
        run.status = "completed"
        run.ended_at = datetime.now(timezone.utc)


def update_run_failed(session: Session, run_id: str) -> None:
    run = session.query(StrategyRun).filter_by(id=run_id).first()
    if run is not None:
        run.status = "failed"
        run.ended_at = datetime.now(timezone.utc)


def record_backtest_result(
    session: Session,
    run_id: str,
    total_pnl: Decimal | None,
    sharpe_ratio: Decimal | None,
    max_drawdown: Decimal | None,
    total_trades: int,
    win_rate: Decimal | None,
    params_hash: str | None = None,
) -> None:
    session.add(
        BacktestResult(
            run_id=run_id,
            total_pnl=total_pnl,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            win_rate=win_rate,
            params_hash=params_hash,
        )
    )


def record_alert(
    session: Session,
    severity: str,
    alert_type: str,
    message: str,
    triggered_at: datetime,
    run_id: str | None = None,
    symbol: str | None = None,
) -> None:
    session.add(
        Alert(
            run_id=run_id,
            symbol=symbol,
            severity=severity,
            alert_type=alert_type,
            message=message,
            triggered_at=triggered_at,
        )
    )


def upsert_engine_status(
    session: Session,
    engine_id: str,
    mode: str,
    status: str,
    config: dict[str, Any] | None = None,
) -> None:
    rec = session.query(EngineStatusRecord).filter_by(engine_id=engine_id).first()
    if rec is None:
        rec = EngineStatusRecord(engine_id=engine_id)
        session.add(rec)
    rec.mode = mode
    rec.status = status
    rec.config = config or {}
    rec.last_seen_at = datetime.now(timezone.utc)


def record_orders_from_events(
    session: Session,
    run_id: str,
    exchange: str,
    symbol: str,
    events: list,
) -> None:
    """Extract OrderEvents from ExecutionReport.events and insert orders + fills.

    Only processes events where status_to == OrderStatus.ACCEPTED (creates order record)
    and status_to == OrderStatus.FILLED (creates fill record).
    """
    from mctrader_engine.report.schema import OrderEvent

    order_ids_inserted: set[str] = set()
    for event in events:
        if not isinstance(event, OrderEvent):
            continue
        order_id_str = str(event.order_id)

        if str(event.status_to) in ("ACCEPTED", "OrderStatus.ACCEPTED"):
            if order_id_str not in order_ids_inserted:
                session.add(
                    Order(
                        id=order_id_str,
                        run_id=run_id,
                        exchange=exchange,
                        symbol=symbol,
                        side=str(getattr(event, "side", "")).lower() or "buy",
                        order_type="market",
                        quantity=event.fill_quantity or Decimal("0"),
                        price=event.fill_price,
                        status="accepted",
                        created_at=event.ts_utc,
                        updated_at=event.ts_utc,
                    )
                )
                order_ids_inserted.add(order_id_str)

        elif str(event.status_to) in ("FILLED", "OrderStatus.FILLED"):
            if event.fill_price is not None and event.fill_quantity is not None:
                # Update order status if it was created
                order = session.query(Order).filter_by(id=order_id_str).first()
                if order is not None:
                    order.status = "filled"
                    order.updated_at = event.ts_utc
                session.add(
                    Fill(
                        id=str(uuid.uuid4()),
                        order_id=order_id_str,
                        price=event.fill_price,
                        quantity=event.fill_quantity,
                        fee=event.fee or Decimal("0"),
                        filled_at=event.ts_utc,
                    )
                )


def record_final_position(
    session: Session,
    run_id: str,
    symbol: str,
    position_quantity: Decimal,
    snapshot_at: datetime,
    avg_cost: Decimal | None = None,
) -> None:
    session.add(
        Position(
            run_id=run_id,
            symbol=symbol,
            quantity=position_quantity,
            avg_cost=avg_cost,
            snapshot_at=snapshot_at,
        )
    )
```

- [ ] **Step 2: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-engine add src/mctrader_engine/db/run_store.py
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(db): run_store service layer for all engine DB writes [MCT-105]"
```

---

## Task 4: Engine Alembic Migration

**Files:**
- Create: `c:/workspace/mclayer/mctrader-engine/alembic.ini`
- Create: `c:/workspace/mclayer/mctrader-engine/alembic/env.py`
- Create: `c:/workspace/mclayer/mctrader-engine/alembic/versions/0001_engine_schema.py`

- [ ] **Step 1: Scaffold alembic**

```bash
cd c:/workspace/mclayer/mctrader-engine
uv run alembic init alembic
```

- [ ] **Step 2: Write alembic.ini** (overwrite generated)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Write alembic/env.py** (overwrite generated)

```python
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from mctrader_engine.db.models import Base  # noqa: E402
from mctrader_engine.db.models.alert import Alert  # noqa: E402, F401
from mctrader_engine.db.models.backtest_result import BacktestResult  # noqa: E402, F401
from mctrader_engine.db.models.engine_status_rec import EngineStatusRecord  # noqa: E402, F401
from mctrader_engine.db.models.fill import Fill  # noqa: E402, F401
from mctrader_engine.db.models.order import Order  # noqa: E402, F401
from mctrader_engine.db.models.position import Position  # noqa: E402, F401
from mctrader_engine.db.models.strategy_run import StrategyRun  # noqa: E402, F401

target_metadata = Base.metadata
_SCHEMA = os.environ.get("DATABASE_SCHEMA", "engine")


def run_migrations_offline() -> None:
    url = os.environ["DATABASE_URL"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema=_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = os.environ["DATABASE_URL"]
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.execute(text(f"SET search_path TO {_SCHEMA},public"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Write alembic/versions/0001_engine_schema.py**

Create `c:/workspace/mclayer/mctrader-engine/alembic/versions/0001_engine_schema.py`:

```python
"""create engine schema tables

Revision ID: 0001
Revises:
Create Date: 2026-05-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("strategy_name", sa.String(128), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("engine_id", sa.String(128), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="engine",
    )
    op.create_table(
        "backtest_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(64),
            sa.ForeignKey("engine.strategy_runs.id"),
            nullable=False,
        ),
        sa.Column("total_pnl", sa.Numeric(38, 18), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(10, 6), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(10, 6), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=True),
        sa.Column("win_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("params_hash", sa.String(64), nullable=True),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="engine",
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(64),
            sa.ForeignKey("engine.strategy_runs.id"),
            nullable=True,
        ),
        sa.Column("symbol", sa.String(32), nullable=True),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "triggered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema="engine",
    )
    op.create_table(
        "engine_status",
        sa.Column("engine_id", sa.String(128), primary_key=True),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "last_seen_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="engine",
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(64),
            sa.ForeignKey("engine.strategy_runs.id"),
            nullable=True,
        ),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("price", sa.Numeric(38, 18), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("exchange_order_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        schema="engine",
    )
    op.create_table(
        "fills",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(64),
            sa.ForeignKey("engine.orders.id"),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(38, 18), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("fee", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("filled_at", sa.TIMESTAMP(timezone=True), nullable=False),
        schema="engine",
    )
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(64),
            sa.ForeignKey("engine.strategy_runs.id"),
            nullable=True,
        ),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("avg_cost", sa.Numeric(38, 18), nullable=True),
        sa.Column("snapshot_at", sa.TIMESTAMP(timezone=True), nullable=False),
        schema="engine",
    )


def downgrade() -> None:
    op.drop_table("positions", schema="engine")
    op.drop_table("fills", schema="engine")
    op.drop_table("orders", schema="engine")
    op.drop_table("engine_status", schema="engine")
    op.drop_table("alerts", schema="engine")
    op.drop_table("backtest_results", schema="engine")
    op.drop_table("strategy_runs", schema="engine")
```

- [ ] **Step 5: Run migration against test DB**

```bash
cd c:/workspace/mclayer/mctrader-engine
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
DATABASE_SCHEMA=engine \
uv run alembic upgrade head
```

Expected:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, create engine schema tables
```

- [ ] **Step 6: Verify tables in test DB**

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader_test -c "\dt engine.*"
```

Expected: 7 tables — `strategy_runs`, `backtest_results`, `alerts`, `engine_status`, `orders`, `fills`, `positions`, `alembic_version`.

- [ ] **Step 7: Run migration against main DB**

```bash
cd c:/workspace/mclayer/mctrader-engine
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
DATABASE_SCHEMA=engine \
uv run alembic upgrade head
```

- [ ] **Step 8: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-engine add alembic.ini alembic/
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(db): Alembic 0001 — engine schema 7 tables DDL [MCT-105]"
```

---

## Task 5: Wire CLI — strategy_runs + backtest_results + alerts + orders + positions

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-engine/src/mctrader_engine/cli.py`

This task adds DB writes to `backtest()` and `paper_start()` in cli.py.
All DB operations are wrapped in `try/except` so trading continues if postgres is unavailable.
`DATABASE_URL` absence = DB skipped entirely (graceful degradation).

- [ ] **Step 1: Read current cli.py to locate insertion points**

```bash
cd c:/workspace/mclayer/mctrader-engine
# Lines 85-155: backtest() function
# Lines 189-296: paper_start() function
```

Key lines in `backtest()`:
- L101-103: `run_id_str` generated
- L127: `report = executor.run()`
- L129: `run_dir = output_dir / run_id_str`

Key lines in `paper_start()`:
- L236: `run_id_str` generated
- L277-278: `asyncio_runner.run(runner.run())`

- [ ] **Step 2: Add `_try_record_run` helper at top of cli.py (after existing imports)**

Add these imports at the top of cli.py, after the existing imports block:

```python
# DB layer — optional; skipped if DATABASE_URL not set
import os as _os
```

Add this helper function before the `@cli.command()` decorators (after the existing helper functions like `_parse_iso_utc`, `_default_run_id`, `_load_candles`):

```python
def _db_session():
    """Return an open SQLAlchemy Session if DATABASE_URL is set, else None."""
    url = _os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        from mctrader_engine.db.engine import make_engine
        from sqlalchemy.orm import Session
        return Session(make_engine(url))
    except Exception as exc:
        click.echo(f"[db] warning: could not open DB session: {exc}", err=True)
        return None
```

- [ ] **Step 3: Wire backtest() in cli.py**

In `backtest()`, after the line `run_id_str = run_id_override or _default_run_id(...)` (L101-103), add:

```python
    # DB: record run start (no-op if DATABASE_URL not set)
    _db = _db_session()
    if _db is not None:
        try:
            from mctrader_engine.db import run_store
            run_store.record_run_start(
                session=_db,
                run_id=run_id_str,
                strategy_name=strategy,
                mode="backtest",
                params={"fast": fast, "slow": slow, "symbol": symbol, "tf": tf.value},
                engine_id=f"backtest-{run_id_str}",
            )
            _db.commit()
        except Exception as exc:
            click.echo(f"[db] warning: record_run_start failed: {exc}", err=True)
            _db.close()
            _db = None
```

Then replace `report = executor.run()` (L127) with:

```python
    try:
        report = executor.run()
    except Exception:
        if _db is not None:
            try:
                from mctrader_engine.db import run_store
                run_store.update_run_failed(_db, run_id_str)
                _db.commit()
            except Exception as exc2:
                click.echo(f"[db] warning: update_run_failed: {exc2}", err=True)
            finally:
                _db.close()
        raise

    # DB: record results, alerts, orders, position (all post-run from ExecutionReport)
    if _db is not None:
        try:
            from mctrader_engine.db import run_store
            from mctrader_engine.report.schema import RiskGateEvent

            run_store.update_run_completed(_db, run_id_str)
            run_store.record_backtest_result(
                session=_db,
                run_id=run_id_str,
                total_pnl=report.summary.final_equity - capital,
                sharpe_ratio=report.summary.sharpe,
                max_drawdown=report.summary.max_drawdown,
                total_trades=report.summary.total_trades,
                win_rate=report.summary.win_rate,
                params_hash=report.policy_hash,
            )
            # Record risk gate events as alerts
            for event in report.events:
                if isinstance(event, RiskGateEvent) and event.blocked:
                    run_store.record_alert(
                        session=_db,
                        run_id=run_id_str,
                        symbol=str(report.symbol),
                        severity="critical",
                        alert_type=str(event.trigger),
                        message=str(event.reason),
                        triggered_at=event.ts_utc,
                    )
            # Record orders and fills from event stream (Phase 4 dual-write)
            run_store.record_orders_from_events(
                session=_db,
                run_id=run_id_str,
                exchange="bithumb",
                symbol=str(report.symbol),
                events=report.events,
            )
            # Record final position snapshot (Phase 5)
            if report.equity_rows:
                last = report.equity_rows[-1]
                run_store.record_final_position(
                    session=_db,
                    run_id=run_id_str,
                    symbol=str(report.symbol),
                    position_quantity=last.position_quantity,
                    snapshot_at=last.ts_utc,
                )
            _db.commit()
        except Exception as exc:
            click.echo(f"[db] warning: post-run DB writes failed: {exc}", err=True)
        finally:
            _db.close()
```

- [ ] **Step 4: Wire paper_start() in cli.py**

In `paper_start()`, after the line `run_id_str = run_id_override or f"paper-{strategy}-..."` (L236), add the engine_status upsert alongside run_start:

```python
    # DB: record paper run start + engine status
    _db = _db_session()
    if _db is not None:
        try:
            from mctrader_engine.db import run_store
            run_store.record_run_start(
                session=_db,
                run_id=run_id_str,
                strategy_name=strategy,
                mode="paper",
                params={"fast": fast, "slow": slow, "symbol": symbol, "tf": tf.value},
                engine_id=f"paper_runner-{run_id_str}",
            )
            run_store.upsert_engine_status(
                session=_db,
                engine_id=f"paper_runner-{run_id_str}",
                mode="paper",
                status="running",
                config={"strategy": strategy, "symbol": symbol, "tf": tf.value},
            )
            _db.commit()
        except Exception as exc:
            click.echo(f"[db] warning: record_run_start failed: {exc}", err=True)
            _db.close()
            _db = None
```

After `report = asyncio_runner.run(runner.run())` (L278), add (inside the `try:` block after the report is assigned):

```python
        # DB: record paper run results
        if _db is not None:
            try:
                from mctrader_engine.db import run_store
                from mctrader_engine.report.schema import RiskGateEvent

                run_store.update_run_completed(_db, run_id_str)
                run_store.upsert_engine_status(
                    session=_db,
                    engine_id=f"paper_runner-{run_id_str}",
                    mode="paper",
                    status="stopped",
                )
                for event in report.events:
                    if isinstance(event, RiskGateEvent) and event.blocked:
                        run_store.record_alert(
                            session=_db,
                            run_id=run_id_str,
                            symbol=str(report.symbol),
                            severity="critical",
                            alert_type=str(event.trigger),
                            message=str(event.reason),
                            triggered_at=event.ts_utc,
                        )
                run_store.record_orders_from_events(
                    session=_db,
                    run_id=run_id_str,
                    exchange="bithumb",
                    symbol=str(report.symbol),
                    events=report.events,
                )
                if report.equity_rows:
                    last = report.equity_rows[-1]
                    run_store.record_final_position(
                        session=_db,
                        run_id=run_id_str,
                        symbol=str(report.symbol),
                        position_quantity=last.position_quantity,
                        snapshot_at=last.ts_utc,
                    )
                _db.commit()
            except Exception as exc:
                click.echo(f"[db] warning: post-run DB writes failed: {exc}", err=True)
            finally:
                _db.close()
```

- [ ] **Step 5: Run existing tests to ensure no regression**

```bash
cd c:/workspace/mclayer/mctrader-engine
uv run pytest tests/test_backtest_executor.py tests/test_cli.py -v
```

Expected: all existing tests PASS (DATABASE_URL not set → DB skipped).

- [ ] **Step 6: Run an end-to-end backtest with DB wiring**

```bash
cd c:/workspace/mclayer/mctrader-engine
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
uv run mctrader-cli backtest \
  --strategy sma --symbol KRW-BTC --tf 1h \
  --start 2026-01-01T00:00:00Z --end 2026-02-01T00:00:00Z \
  --fast 5 --slow 20 --output-dir ./out
```

After run completes, verify:

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader -c \
  "SELECT id, strategy_name, mode, status FROM engine.strategy_runs ORDER BY created_at DESC LIMIT 3;"
```

Expected: row with `mode=backtest`, `status=completed`.

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader -c \
  "SELECT total_trades, sharpe_ratio, max_drawdown FROM engine.backtest_results ORDER BY computed_at DESC LIMIT 1;"
```

Expected: non-null numeric values.

- [ ] **Step 7: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-engine add src/mctrader_engine/cli.py
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(db): wire CLI to record strategy_runs, results, alerts, orders, positions [MCT-105]"
```

---

## Task 6: mctrader-web DB Layer + Web Schema

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-web/pyproject.toml`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/__init__.py`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/engine.py`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/__init__.py`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/dashboard_config.py`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/notification_channel.py`
- Create: `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/notification_dispatch.py`
- Create: `c:/workspace/mclayer/mctrader-web/alembic.ini`
- Create: `c:/workspace/mclayer/mctrader-web/alembic/env.py`
- Create: `c:/workspace/mclayer/mctrader-web/alembic/versions/0001_web_schema.py`
- Create: `c:/workspace/mclayer/mctrader-web/tests/test_web_db.py`

- [ ] **Step 1: Add dependencies to mctrader-web**

```bash
cd c:/workspace/mclayer/mctrader-web
uv add "sqlalchemy>=2.0,<3" "alembic>=1.13" "psycopg[binary]>=3.1"
```

Add integration marker to `[tool.pytest.ini_options]` in `pyproject.toml`:

```toml
markers = [
    "integration: tests requiring a running PostgreSQL instance (set TEST_DATABASE_URL)",
]
```

- [ ] **Step 2: Write the failing test**

Create `c:/workspace/mclayer/mctrader-web/tests/test_web_db.py`:

```python
"""Integration tests for web schema models — requires running postgres.

Run with:
    TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
    uv run pytest tests/test_web_db.py -v -m integration
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test",
)


@pytest.fixture(scope="module")
def engine():
    from mctrader_web.db.models import Base

    eng = create_engine(
        TEST_URL,
        connect_args={"options": "-csearch_path=web,public"},
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def test_dashboard_config_insert(db: Session) -> None:
    from mctrader_web.db.models.dashboard_config import DashboardConfig

    cfg = DashboardConfig(
        config_key="default",
        config={"symbols": ["KRW-BTC", "KRW-ETH"], "refresh_seconds": 30},
    )
    db.add(cfg)
    db.flush()

    result = db.query(DashboardConfig).filter_by(config_key="default").first()
    assert result is not None
    assert result.config["refresh_seconds"] == 30


def test_notification_channel_and_dispatch(db: Session) -> None:
    from mctrader_web.db.models.notification_channel import NotificationChannel
    from mctrader_web.db.models.notification_dispatch import NotificationDispatch

    ch = NotificationChannel(
        channel_type="telegram",
        target="123456789",
        severity_min="warning",
        is_active=True,
    )
    db.add(ch)
    db.flush()

    dispatch = NotificationDispatch(
        id=str(uuid.uuid4()),
        alert_id=str(uuid.uuid4()),
        channel_id=ch.id,
        status="sent",
    )
    db.add(dispatch)
    db.flush()

    r = db.query(NotificationDispatch).filter_by(channel_id=ch.id).first()
    assert r is not None
    assert r.status == "sent"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd c:/workspace/mclayer/mctrader-web
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_web_db.py -v -m integration
```

Expected: `ImportError` — db package doesn't exist.

- [ ] **Step 4: Write db/__init__.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/__init__.py`:

```python
"""PostgreSQL DB layer for mctrader-web (web schema)."""
```

- [ ] **Step 5: Write db/models/__init__.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/__init__.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 6: Write db/models/dashboard_config.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/dashboard_config.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class DashboardConfig(Base):
    __tablename__ = "dashboard_configs"
    __table_args__ = {"schema": "web"}

    id: Mapped[int] = mapped_column(primary_key=True)
    config_key: Mapped[str] = mapped_column(String(128), unique=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 7: Write db/models/notification_channel.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/notification_channel.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    __table_args__ = {"schema": "web"}

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_type: Mapped[str] = mapped_column(String(32))    # telegram/email/webhook
    target: Mapped[str] = mapped_column(String(256))         # chat_id / email / URL
    severity_min: Mapped[str] = mapped_column(String(16), default="warning")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 8: Write db/models/notification_dispatch.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/models/notification_dispatch.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NotificationDispatch(Base):
    __tablename__ = "notification_dispatches"
    __table_args__ = {"schema": "web"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64))        # engine.alerts ref (app-layer)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("web.notification_channels.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16))          # sent/failed/skipped
    dispatched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 9: Write db/engine.py**

Create `c:/workspace/mclayer/mctrader-web/src/mctrader_web/db/engine.py`:

```python
from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str | None = None, schema: str = "web") -> Engine:
    resolved = url or os.environ["DATABASE_URL"]
    return create_engine(
        resolved,
        connect_args={"options": f"-csearch_path={schema},public"},
    )


def make_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine or make_engine())
```

- [ ] **Step 10: Run tests to verify they pass**

```bash
cd c:/workspace/mclayer/mctrader-web
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_web_db.py -v -m integration
```

Expected: 2 tests PASSED.

- [ ] **Step 11: Scaffold alembic and write alembic.ini**

```bash
cd c:/workspace/mclayer/mctrader-web
uv run alembic init alembic
```

Overwrite `alembic.ini` with:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 12: Write alembic/env.py**

Overwrite `alembic/env.py`:

```python
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from mctrader_web.db.models import Base  # noqa: E402
from mctrader_web.db.models.dashboard_config import DashboardConfig  # noqa: E402, F401
from mctrader_web.db.models.notification_channel import NotificationChannel  # noqa: E402, F401
from mctrader_web.db.models.notification_dispatch import NotificationDispatch  # noqa: E402, F401

target_metadata = Base.metadata
_SCHEMA = os.environ.get("DATABASE_SCHEMA", "web")


def run_migrations_offline() -> None:
    url = os.environ["DATABASE_URL"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema=_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = os.environ["DATABASE_URL"]
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.execute(text(f"SET search_path TO {_SCHEMA},public"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 13: Write alembic/versions/0001_web_schema.py**

Create `c:/workspace/mclayer/mctrader-web/alembic/versions/0001_web_schema.py`:

```python
"""create web schema tables

Revision ID: 0001
Revises:
Create Date: 2026-05-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dashboard_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("config_key", sa.String(128), nullable=False, unique=True),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="web",
    )
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("channel_type", sa.String(32), nullable=False),
        sa.Column("target", sa.String(256), nullable=False),
        sa.Column("severity_min", sa.String(16), nullable=False, server_default="warning"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="web",
    )
    op.create_table(
        "notification_dispatches",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("alert_id", sa.String(64), nullable=False),
        sa.Column(
            "channel_id",
            sa.Integer(),
            sa.ForeignKey("web.notification_channels.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "dispatched_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="web",
    )


def downgrade() -> None:
    op.drop_table("notification_dispatches", schema="web")
    op.drop_table("notification_channels", schema="web")
    op.drop_table("dashboard_configs", schema="web")
```

- [ ] **Step 14: Run migration against test + main DB**

```bash
cd c:/workspace/mclayer/mctrader-web

# Test DB
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
DATABASE_SCHEMA=web \
uv run alembic upgrade head

# Main DB
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
DATABASE_SCHEMA=web \
uv run alembic upgrade head
```

Expected for both: `INFO [alembic.runtime.migration] Running upgrade  -> 0001, create web schema tables`

- [ ] **Step 15: Verify tables in main DB**

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader -c "\dt web.*"
```

Expected: `dashboard_configs`, `notification_channels`, `notification_dispatches`, `alembic_version`.

- [ ] **Step 16: Commit all web changes**

```bash
git -C c:/workspace/mclayer/mctrader-web add \
  pyproject.toml uv.lock \
  src/mctrader_web/db/ \
  alembic.ini alembic/ \
  tests/test_web_db.py
git -C c:/workspace/mclayer/mctrader-web commit -m "feat(db): web schema — dashboard_configs, notification_channels, dispatches + Alembic [MCT-105]"
```

---

## Phase 2-5 Completion Checklist

- [ ] Engine integration tests: `uv run pytest tests/test_engine_db.py -m integration` → 5 PASSED
- [ ] Web integration tests: `uv run pytest tests/test_web_db.py -m integration` → 2 PASSED
- [ ] Engine existing tests still pass: `uv run pytest tests/test_backtest_executor.py tests/test_cli.py -v` → no regressions
- [ ] After a backtest run with `DATABASE_URL` set: `SELECT COUNT(*) FROM engine.strategy_runs` ≥ 1
- [ ] After a backtest run: `SELECT COUNT(*) FROM engine.backtest_results` ≥ 1
- [ ] All 7 engine tables exist in `engine.*`: `\dt engine.*`
- [ ] All 3 web tables exist in `web.*`: `\dt web.*`
- [ ] All engine DB changes committed (deps, models, run_store, alembic, cli)
- [ ] All web DB changes committed (deps, models, alembic)

**Phase 6 (Paper Ledger evaluation)** is a documented decision point — no code required until Phase 4 dual-write has been stable for 6+ months.
