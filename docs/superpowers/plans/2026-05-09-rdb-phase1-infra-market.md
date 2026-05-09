# RDB Phase 1: Hub PostgreSQL Infra + Market Schema

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Launch a shared PostgreSQL instance in mctrader-hub and add `market.symbols` + `market.exchange_capabilities` tables with Alembic migrations, seed scripts, and compose network wiring for engine/web.

**Architecture:** Per-repo schema ownership — mctrader-hub provides the PostgreSQL service on `mctrader_net`; mctrader-market owns the `market` schema and manages it via Alembic. Engine and web compose files join the shared network so Phase 2 wiring can start immediately after this plan.

**Tech Stack:** PostgreSQL 16-alpine, SQLAlchemy 2.x, Alembic 1.13+, psycopg 3.x (psycopg[binary]), pyarrow (migration scripts only), Docker Compose.

---

## File Map

### mctrader-hub (all new)
- CREATE `compose.yml` — postgres:16-alpine + shared `mctrader_net` bridge network
- CREATE `scripts/init-db.sh` — CREATE SCHEMA for market/engine/web in both main and test DBs
- CREATE `.env.example` — POSTGRES_PASSWORD placeholder

### mctrader-market (modify + new)
- MODIFY `pyproject.toml` — add sqlalchemy, alembic, psycopg, pyarrow[optional]
- MODIFY `pyproject.toml` — add `integration` pytest marker
- CREATE `src/mctrader_market/models/__init__.py` — DeclarativeBase
- CREATE `src/mctrader_market/models/symbol.py` — Symbol ORM model (market.symbols)
- CREATE `src/mctrader_market/models/exchange_capability.py` — ExchangeCapability ORM model
- CREATE `src/mctrader_market/db.py` — make_engine + make_session_factory
- CREATE `alembic.ini` — Alembic config (URL from DATABASE_URL env)
- CREATE `alembic/env.py` — migration runner with market schema search_path
- CREATE `alembic/script.py.mako` — template (from `alembic init`)
- CREATE `alembic/versions/0001_market_tables.py` — symbols + exchange_capabilities DDL
- CREATE `scripts/parquet_utils.py` — find_latest_t4_date + read_t4_rows
- CREATE `scripts/seed_symbols.py` — INSERT 50 symbols from T4 Parquet
- CREATE `scripts/migrate_t4_to_pg.py` — UPSERT exchange_capabilities from T4 Parquet
- CREATE `tests/test_market_db.py` — integration tests (require postgres)

### mctrader-engine (modify)
- MODIFY `compose.yml` — join `mctrader_net`, add `DATABASE_URL` env var to services

### mctrader-web (modify)
- MODIFY `compose.yml` — join `mctrader_net`, add `DATABASE_URL` env var to `api` service

---

## Task 1: Hub PostgreSQL Docker Compose

**Files:**
- Create: `c:/workspace/mclayer/mctrader-hub/compose.yml`
- Create: `c:/workspace/mclayer/mctrader-hub/scripts/init-db.sh`
- Create: `c:/workspace/mclayer/mctrader-hub/.env.example`

- [ ] **Step 1: Write compose.yml**

Create `c:/workspace/mclayer/mctrader-hub/compose.yml`:

```yaml
# mctrader-hub/compose.yml — Shared infrastructure: PostgreSQL + mctrader_net
# Provides postgres service for all mctrader repos via external mctrader_net network.
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mctrader
      POSTGRES_USER: mctrader
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - mctrader_postgres:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/01-init-db.sh
    ports:
      - "5432:5432"
    networks:
      - mctrader_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mctrader"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    labels:
      mctrader.role: "postgres"
      mctrader.story: "MCT-105"

networks:
  mctrader_net:
    name: mctrader_net
    driver: bridge

volumes:
  mctrader_postgres:
```

- [ ] **Step 2: Write scripts/init-db.sh**

Create `c:/workspace/mclayer/mctrader-hub/scripts/init-db.sh`:

```bash
#!/bin/bash
set -e

# Create schemas in main DB (mctrader)
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS market;
    CREATE SCHEMA IF NOT EXISTS engine;
    CREATE SCHEMA IF NOT EXISTS web;
EOSQL

# Create test DB and schemas (used by pytest integration tests)
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE mctrader_test;
EOSQL

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d mctrader_test <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS market;
    CREATE SCHEMA IF NOT EXISTS engine;
    CREATE SCHEMA IF NOT EXISTS web;
EOSQL
```

- [ ] **Step 3: Write .env.example**

Create `c:/workspace/mclayer/mctrader-hub/.env.example`:

```
POSTGRES_PASSWORD=changeme
```

- [ ] **Step 4: Start postgres and verify schemas**

```bash
cd c:/workspace/mclayer/mctrader-hub
cp .env.example .env
docker compose up -d postgres
```

Wait ~20 seconds for healthcheck, then:

```bash
docker compose ps
```

Expected: `postgres` Status=`Up (healthy)`

```bash
docker compose exec postgres psql -U mctrader -c "\dn"
```

Expected output includes `market`, `engine`, `web` in the schema list.

```bash
docker compose exec postgres psql -U mctrader -d mctrader_test -c "\dn"
```

Expected: same schemas in `mctrader_test` DB.

- [ ] **Step 5: Commit hub changes**

```bash
git -C c:/workspace/mclayer/mctrader-hub add compose.yml scripts/init-db.sh .env.example
git -C c:/workspace/mclayer/mctrader-hub commit -m "feat(infra): add PostgreSQL shared compose + schema init [MCT-105]"
```

---

## Task 2: mctrader-market Dependencies

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-market/pyproject.toml`

- [ ] **Step 1: Add DB + test dependencies via uv**

```bash
cd c:/workspace/mclayer/mctrader-market
uv add "sqlalchemy>=2.0,<3" "alembic>=1.13" "psycopg[binary]>=3.1"
uv add --optional migration "pyarrow>=15"
```

- [ ] **Step 2: Add integration pytest marker to pyproject.toml**

Edit `pyproject.toml` `[tool.pytest.ini_options]` section to add:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers"
markers = [
    "integration: tests requiring a running PostgreSQL instance (set TEST_DATABASE_URL)",
]
```

- [ ] **Step 3: Verify imports**

```bash
cd c:/workspace/mclayer/mctrader-market
uv run python -c "import sqlalchemy, alembic, psycopg; print(sqlalchemy.__version__)"
```

Expected: prints `2.x.x`

- [ ] **Step 4: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-market add pyproject.toml uv.lock
git -C c:/workspace/mclayer/mctrader-market commit -m "feat(db): add sqlalchemy + alembic + psycopg dependencies [MCT-105]"
```

---

## Task 3: SQLAlchemy Models + db.py

**Files:**
- Create: `c:/workspace/mclayer/mctrader-market/tests/test_market_db.py`
- Create: `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/__init__.py`
- Create: `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/symbol.py`
- Create: `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/exchange_capability.py`
- Create: `c:/workspace/mclayer/mctrader-market/src/mctrader_market/db.py`

- [ ] **Step 1: Write the failing test**

Create `c:/workspace/mclayer/mctrader-market/tests/test_market_db.py`:

```python
"""Integration tests for market schema models — requires running postgres.

Run with:
    TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
    uv run pytest tests/test_market_db.py -v -m integration
"""
from __future__ import annotations

import os
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
    from mctrader_market.models import Base

    eng = create_engine(
        TEST_URL,
        connect_args={"options": "-csearch_path=market,public"},
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


def test_symbol_insert_and_query(db: Session) -> None:
    from mctrader_market.models.symbol import Symbol

    sym = Symbol(
        exchange="bithumb",
        symbol="KRW-BTC",
        base_asset="BTC",
        quote_asset="KRW",
        status="active",
        included_at=datetime.now(timezone.utc),
    )
    db.add(sym)
    db.flush()

    result = db.query(Symbol).filter_by(exchange="bithumb", symbol="KRW-BTC").first()
    assert result is not None
    assert result.symbol == "KRW-BTC"
    assert result.status == "active"
    assert result.excluded_at is None
    assert result.updated_at is not None


def test_symbol_unique_constraint_raises(db: Session) -> None:
    from sqlalchemy.exc import IntegrityError

    from mctrader_market.models.symbol import Symbol

    db.add(
        Symbol(
            exchange="bithumb",
            symbol="KRW-ETH",
            base_asset="ETH",
            quote_asset="KRW",
            status="active",
            included_at=datetime.now(timezone.utc),
        )
    )
    db.flush()
    db.add(
        Symbol(
            exchange="bithumb",
            symbol="KRW-ETH",
            base_asset="ETH",
            quote_asset="KRW",
            status="active",
            included_at=datetime.now(timezone.utc),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_exchange_capability_nullable_phase2_fields(db: Session) -> None:
    from mctrader_market.models.exchange_capability import ExchangeCapability

    cap = ExchangeCapability(
        exchange="bithumb",
        symbol="KRW-XRP",
        fetched_at=datetime.now(timezone.utc),
        # All nullable fields omitted — Bithumb Phase 2 nullables per ADR-009 §D13
    )
    db.add(cap)
    db.flush()

    result = db.query(ExchangeCapability).filter_by(symbol="KRW-XRP").first()
    assert result is not None
    assert result.tick_size is None
    assert result.fee_taker is None


def test_exchange_capability_full_precision(db: Session) -> None:
    from mctrader_market.models.exchange_capability import ExchangeCapability

    cap = ExchangeCapability(
        exchange="bithumb",
        symbol="KRW-ADA",
        tick_size=Decimal("1"),
        min_order_qty=Decimal("1"),
        min_order_notional_krw=Decimal("5000"),
        fee_maker=Decimal("0.004"),
        fee_taker=Decimal("0.004"),
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(cap)
    db.flush()

    result = db.query(ExchangeCapability).filter_by(symbol="KRW-ADA").first()
    assert result is not None
    assert result.fee_taker == Decimal("0.004")
    assert result.min_order_notional_krw == Decimal("5000")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd c:/workspace/mclayer/mctrader-market
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_market_db.py -v -m integration
```

Expected: `ImportError` or `ModuleNotFoundError` — models don't exist yet.

- [ ] **Step 3: Write models/__init__.py**

Create `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/__init__.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 4: Write models/symbol.py**

Create `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/symbol.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_symbols_exchange_symbol"),
        {"schema": "market"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32))
    base_asset: Mapped[str] = mapped_column(String(16))
    quote_asset: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    included_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    excluded_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
```

- [ ] **Step 5: Write models/exchange_capability.py**

Create `c:/workspace/mclayer/mctrader-market/src/mctrader_market/models/exchange_capability.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ExchangeCapability(Base):
    __tablename__ = "exchange_capabilities"
    __table_args__ = (
        UniqueConstraint(
            "exchange", "symbol", name="uq_exchange_cap_exchange_symbol"
        ),
        {"schema": "market"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32))
    tick_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    min_order_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    min_order_notional_krw: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    fee_maker: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    fee_taker: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    fetched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 6: Write db.py**

Create `c:/workspace/mclayer/mctrader-market/src/mctrader_market/db.py`:

```python
from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str | None = None, schema: str = "market") -> Engine:
    resolved = url or os.environ["DATABASE_URL"]
    return create_engine(
        resolved,
        connect_args={"options": f"-csearch_path={schema},public"},
    )


def make_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine or make_engine())
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd c:/workspace/mclayer/mctrader-market
TEST_DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
uv run pytest tests/test_market_db.py -v -m integration
```

Expected: 4 tests PASSED.

- [ ] **Step 8: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-market add \
  src/mctrader_market/models/ \
  src/mctrader_market/db.py \
  tests/test_market_db.py
git -C c:/workspace/mclayer/mctrader-market commit -m "feat(db): SQLAlchemy models for market.symbols + exchange_capabilities [MCT-105]"
```

---

## Task 4: Alembic Migration

**Files:**
- Create: `c:/workspace/mclayer/mctrader-market/alembic.ini`
- Create: `c:/workspace/mclayer/mctrader-market/alembic/env.py`
- Create: `c:/workspace/mclayer/mctrader-market/alembic/versions/0001_market_tables.py`

- [ ] **Step 1: Scaffold alembic directory**

```bash
cd c:/workspace/mclayer/mctrader-market
uv run alembic init alembic
```

This creates `alembic/` with a template `env.py` and `script.py.mako`. Overwrite `alembic/env.py` and `alembic.ini` with the versions below.

- [ ] **Step 2: Write alembic.ini** (overwrite the generated file)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
# URL is overridden in env.py from DATABASE_URL environment variable
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

- [ ] **Step 3: Write alembic/env.py** (overwrite the generated file)

```python
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so Alembic discovers their metadata
from mctrader_market.models import Base  # noqa: E402
from mctrader_market.models.exchange_capability import ExchangeCapability  # noqa: E402, F401
from mctrader_market.models.symbol import Symbol  # noqa: E402, F401

target_metadata = Base.metadata
_SCHEMA = os.environ.get("DATABASE_SCHEMA", "market")


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

- [ ] **Step 4: Write alembic/versions/0001_market_tables.py**

Create `c:/workspace/mclayer/mctrader-market/alembic/versions/0001_market_tables.py`:

```python
"""create market schema tables

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
        "symbols",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("base_asset", sa.String(16), nullable=False),
        sa.Column("quote_asset", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("score", sa.Numeric(6, 4), nullable=True),
        sa.Column("included_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("excluded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("exchange", "symbol", name="uq_symbols_exchange_symbol"),
        schema="market",
    )
    op.create_table(
        "exchange_capabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("tick_size", sa.Numeric(38, 18), nullable=True),
        sa.Column("min_order_qty", sa.Numeric(38, 18), nullable=True),
        sa.Column("min_order_notional_krw", sa.Numeric(38, 18), nullable=True),
        sa.Column("fee_maker", sa.Numeric(10, 8), nullable=True),
        sa.Column("fee_taker", sa.Numeric(10, 8), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "exchange", "symbol", name="uq_exchange_cap_exchange_symbol"
        ),
        schema="market",
    )


def downgrade() -> None:
    op.drop_table("exchange_capabilities", schema="market")
    op.drop_table("symbols", schema="market")
```

- [ ] **Step 5: Run migration against test DB**

```bash
cd c:/workspace/mclayer/mctrader-market
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader_test \
DATABASE_SCHEMA=market \
uv run alembic upgrade head
```

Expected:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, create market schema tables
```

- [ ] **Step 6: Verify tables exist in test DB**

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader_test -c "\dt market.*"
```

Expected output: `symbols`, `exchange_capabilities`, `alembic_version` tables in `market` schema.

- [ ] **Step 7: Run migration against main DB**

```bash
cd c:/workspace/mclayer/mctrader-market
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
DATABASE_SCHEMA=market \
uv run alembic upgrade head
```

- [ ] **Step 8: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-market add alembic.ini alembic/
git -C c:/workspace/mclayer/mctrader-market commit -m "feat(db): Alembic 0001 — market.symbols + exchange_capabilities DDL [MCT-105]"
```

---

## Task 5: Seed + Migration Scripts

**Files:**
- Create: `c:/workspace/mclayer/mctrader-market/scripts/parquet_utils.py`
- Create: `c:/workspace/mclayer/mctrader-market/scripts/seed_symbols.py`
- Create: `c:/workspace/mclayer/mctrader-market/scripts/migrate_t4_to_pg.py`

- [ ] **Step 1: Write scripts/parquet_utils.py**

Create `c:/workspace/mclayer/mctrader-market/scripts/parquet_utils.py`:

```python
"""Shared utilities for reading T4 exchange_metadata Parquet (ADR-009 §D13)."""
from __future__ import annotations

import glob


def find_latest_t4_date(data_root: str, exchange: str) -> str:
    pattern = (
        f"{data_root}/market/exchange_metadata"
        f"/schema_version=exchange_metadata.v1"
        f"/exchange={exchange}/fetched_date=*/node=*/*.parquet"
    )
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(
            f"No T4 Parquet found for exchange={exchange!r} under {data_root!r}. "
            "Run mctrader-data collector first."
        )
    dates = sorted({f.split("fetched_date=")[1].split("/")[0] for f in files})
    return dates[-1]


def read_t4_rows(data_root: str, exchange: str, fetched_date: str) -> list[dict]:
    import pyarrow.parquet as pq

    pattern = (
        f"{data_root}/market/exchange_metadata"
        f"/schema_version=exchange_metadata.v1"
        f"/exchange={exchange}/fetched_date={fetched_date}/node=*/*.parquet"
    )
    files = glob.glob(pattern)
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for f in files:
        for row in pq.read_table(f).to_pylist():
            key = (row["exchange"], row["symbol"])
            if key not in seen:
                seen.add(key)
                rows.append(row)
    return rows
```

- [ ] **Step 2: Write scripts/seed_symbols.py**

Create `c:/workspace/mclayer/mctrader-market/scripts/seed_symbols.py`:

```python
"""Seed market.symbols from latest T4 exchange_metadata Parquet.

Usage:
    MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
    DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
    uv run --with pyarrow python scripts/seed_symbols.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from parquet_utils import find_latest_t4_date, read_t4_rows

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mctrader_market.models.symbol import Symbol


def seed(session: Session, exchange: str, data_root: str) -> int:
    latest = find_latest_t4_date(data_root, exchange)
    print(f"Using T4 date: {latest}")
    rows = read_t4_rows(data_root, exchange, latest)

    inserted = 0
    for row in rows:
        existing = (
            session.query(Symbol)
            .filter_by(exchange=row["exchange"], symbol=row["symbol"])
            .first()
        )
        if existing:
            continue
        session.add(
            Symbol(
                exchange=row["exchange"],
                symbol=row["symbol"],
                base_asset=row["base_asset"],
                quote_asset=row["quote_asset"],
                status=row.get("asset_status") or "active",
                included_at=datetime.now(timezone.utc),
            )
        )
        inserted += 1

    session.commit()
    return inserted


if __name__ == "__main__":
    data_root = os.environ.get("MCTRADER_DATA_ROOT", "./data")
    db_url = os.environ["DATABASE_URL"]
    exchange = os.environ.get("MCTRADER_EXCHANGE", "bithumb")
    engine = create_engine(db_url, connect_args={"options": "-csearch_path=market,public"})
    with Session(engine) as session:
        n = seed(session, exchange, data_root)
    print(f"Inserted {n} symbols for exchange={exchange}")
```

- [ ] **Step 3: Write scripts/migrate_t4_to_pg.py**

Create `c:/workspace/mclayer/mctrader-market/scripts/migrate_t4_to_pg.py`:

```python
"""UPSERT latest T4 exchange_metadata Parquet into market.exchange_capabilities.

Usage:
    MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
    DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
    uv run --with pyarrow python scripts/migrate_t4_to_pg.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))
from parquet_utils import find_latest_t4_date, read_t4_rows

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mctrader_market.models.exchange_capability import ExchangeCapability


def _to_decimal(v: object) -> Decimal | None:
    return Decimal(str(v)) if v is not None else None


def migrate(session: Session, exchange: str, data_root: str) -> int:
    latest = find_latest_t4_date(data_root, exchange)
    print(f"Using T4 date: {latest}")
    rows = read_t4_rows(data_root, exchange, latest)

    upserted = 0
    for row in rows:
        cap = (
            session.query(ExchangeCapability)
            .filter_by(exchange=row["exchange"], symbol=row["symbol"])
            .first()
        )
        raw_fetched = row.get("fetched_at")
        fetched_at: datetime = (
            raw_fetched
            if isinstance(raw_fetched, datetime) and raw_fetched.tzinfo is not None
            else datetime.now(timezone.utc)
        )
        if cap is None:
            cap = ExchangeCapability(exchange=row["exchange"], symbol=row["symbol"])
            session.add(cap)

        cap.tick_size = _to_decimal(row.get("tick_size"))
        cap.min_order_qty = _to_decimal(row.get("min_order_qty"))
        cap.min_order_notional_krw = _to_decimal(row.get("min_order_notional_krw"))
        cap.fee_maker = _to_decimal(row.get("fee_maker"))
        cap.fee_taker = _to_decimal(row.get("fee_taker"))
        cap.fetched_at = fetched_at
        upserted += 1

    session.commit()
    return upserted


if __name__ == "__main__":
    data_root = os.environ.get("MCTRADER_DATA_ROOT", "./data")
    db_url = os.environ["DATABASE_URL"]
    exchange = os.environ.get("MCTRADER_EXCHANGE", "bithumb")
    engine = create_engine(db_url, connect_args={"options": "-csearch_path=market,public"})
    with Session(engine) as session:
        n = migrate(session, exchange, data_root)
    print(f"Upserted {n} exchange_capabilities rows for exchange={exchange}")
```

- [ ] **Step 4: Run seed script (requires T4 Parquet data on host)**

```bash
cd c:/workspace/mclayer/mctrader-market
MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
MCTRADER_EXCHANGE=bithumb \
uv run --with pyarrow python scripts/seed_symbols.py
```

Expected: `Inserted 50 symbols for exchange=bithumb`

If T4 Parquet is in Docker volume, mount it first:
```bash
docker run --rm -v mctrader_data:/var/lib/mctrader/data:ro alpine ls /var/lib/mctrader/data/market/exchange_metadata/
```

- [ ] **Step 5: Verify symbol count**

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader -c "SELECT COUNT(*) FROM market.symbols;"
```

Expected: `count = 50`

- [ ] **Step 6: Run T4 migration script**

```bash
cd c:/workspace/mclayer/mctrader-market
MCTRADER_DATA_ROOT=/var/lib/mctrader/data \
DATABASE_URL=postgresql+psycopg://mctrader:changeme@localhost:5432/mctrader \
MCTRADER_EXCHANGE=bithumb \
uv run --with pyarrow python scripts/migrate_t4_to_pg.py
```

Expected: `Upserted 50 exchange_capabilities rows for exchange=bithumb`

- [ ] **Step 7: Verify capabilities count**

```bash
docker exec mctrader-hub-postgres-1 \
  psql -U mctrader -d mctrader -c "SELECT COUNT(*) FROM market.exchange_capabilities;"
```

Expected: `count = 50`

- [ ] **Step 8: Commit**

```bash
git -C c:/workspace/mclayer/mctrader-market add scripts/
git -C c:/workspace/mclayer/mctrader-market commit -m "feat(db): seed + T4 Parquet migration scripts for market schema [MCT-105]"
```

---

## Task 6: Engine + Web Compose Network Extension

**Files:**
- Modify: `c:/workspace/mclayer/mctrader-engine/compose.yml`
- Modify: `c:/workspace/mclayer/mctrader-web/compose.yml`
- Create: `c:/workspace/mclayer/mctrader-engine/.env.example`
- Create: `c:/workspace/mclayer/mctrader-web/.env.example`

- [ ] **Step 1: Modify mctrader-engine/compose.yml**

Add to `paper` service `environment:` block:
```yaml
      DATABASE_URL: postgresql+psycopg://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader
```

Add new `networks:` block to `paper` service:
```yaml
    networks:
      - mctrader_net
```

Add to `engine` service `environment:` block:
```yaml
      DATABASE_URL: postgresql+psycopg://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader
```

Add new `networks:` block to `engine` service:
```yaml
    networks:
      - mctrader_net
```

Add to the bottom of the file (after `volumes:` section):
```yaml
networks:
  mctrader_net:
    external: true
    name: mctrader_net
```

- [ ] **Step 2: Verify engine compose is valid**

```bash
cd c:/workspace/mclayer/mctrader-engine
POSTGRES_PASSWORD=changeme docker compose config --quiet
```

Expected: no errors printed.

- [ ] **Step 3: Modify mctrader-web/compose.yml**

Add to `api` service `environment:` block:
```yaml
      DATABASE_URL: postgresql+psycopg://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader
```

The `api` service already has `networks: [mctrader-web-net]`. Extend it:
```yaml
    networks:
      - mctrader-web-net
      - mctrader_net
```

Add to the `networks:` section at the bottom (alongside existing `mctrader-web-net`):
```yaml
  mctrader_net:
    external: true
    name: mctrader_net
```

- [ ] **Step 4: Verify web compose is valid**

```bash
cd c:/workspace/mclayer/mctrader-web
POSTGRES_PASSWORD=changeme docker compose config --quiet
```

Expected: no errors printed.

- [ ] **Step 5: Create .env.example files**

Create `c:/workspace/mclayer/mctrader-engine/.env.example`:
```
POSTGRES_PASSWORD=changeme
MCTRADER_STRATEGY=sma
MCTRADER_SYMBOL=KRW-BTC
MCTRADER_TF=1h
MCTRADER_FAST=5
MCTRADER_SLOW=20
```

Create `c:/workspace/mclayer/mctrader-web/.env.example`:
```
POSTGRES_PASSWORD=changeme
MCTRADER_ADMIN_TOKEN_SECRET=change-this-in-production
```

- [ ] **Step 6: Commit engine and web changes**

```bash
git -C c:/workspace/mclayer/mctrader-engine add compose.yml .env.example
git -C c:/workspace/mclayer/mctrader-engine commit -m "feat(infra): join mctrader_net + DATABASE_URL env for postgres [MCT-105]"

git -C c:/workspace/mclayer/mctrader-web add compose.yml .env.example
git -C c:/workspace/mclayer/mctrader-web commit -m "feat(infra): join mctrader_net + DATABASE_URL env for postgres [MCT-105]"
```

---

## Phase 1 Completion Checklist

- [ ] `docker compose ps` in hub shows postgres `healthy`
- [ ] `SELECT COUNT(*) FROM market.symbols` = 50
- [ ] `SELECT COUNT(*) FROM market.exchange_capabilities` = 50
- [ ] `uv run pytest tests/test_market_db.py -m integration` → 4 PASSED
- [ ] `docker compose config --quiet` passes for engine and web repos
- [ ] All 6 tasks committed (hub, market ×4, engine, web)

**Next:** Proceed to `2026-05-09-rdb-phase2-5-engine-web.md` for engine schema (strategy_runs, orders, alerts, positions) and web schema.
