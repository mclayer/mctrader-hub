# Strategy Set Pipeline — Phase 1-A: DB Schema Migration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-engine의 Alembic으로 Strategy Set Pipeline용 신규 DB 테이블 8개를 추가하고 SQLAlchemy ORM 모델을 생성한다.

**Architecture:** 기존 `engine` 스키마에 `strategy_sets`, `strategy_drafts`, `strategy_set_versions`, `strategy_set_components`, `strategy_set_layers`, `strategy_promotion_events`, `strategy_runtime_overrides`, `pipeline_events` 테이블을 추가. 기존 `strategy_runs` 테이블에 `strategy_set_version_id` FK 컬럼을 추가.

**Tech Stack:** SQLAlchemy 2.x (mapped_column), Alembic, PostgreSQL, UUID primary keys

**Repo:** `c:\workspace\mclayer\mctrader-engine`

**전제:** Phase 1-A Engine Core와 병렬 실행 가능 (의존 없음)

---

## 파일 구조

```
src/mctrader_engine/db/models/
    strategy_set.py              StrategySet 모델
    strategy_draft.py            StrategyDraft 모델
    strategy_set_version.py      StrategySetVersion 모델
    strategy_set_component.py    StrategySetComponent 모델
    strategy_set_layer.py        StrategySetLayer 모델
    strategy_promotion_event.py  StrategyPromotionEvent 모델
    strategy_runtime_override.py StrategyRuntimeOverride 모델
    pipeline_event.py            PipelineEvent 모델
    __init__.py                  (수정: 신규 모델 import 추가)
    strategy_run.py              (수정: strategy_set_version_id FK 추가)

alembic/env.py                   (수정: 신규 모델 import 추가)
alembic/versions/
    0002_strategy_set_pipeline.py  신규 마이그레이션
```

---

### Task 1: StrategySet + StrategyDraft 모델

**Files:**
- Create: `src/mctrader_engine/db/models/strategy_set.py`
- Create: `src/mctrader_engine/db/models/strategy_draft.py`

- [ ] **Step 1: strategy_set.py 구현**

`src/mctrader_engine/db/models/strategy_set.py`:

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class StrategySet(Base):
    __tablename__ = "strategy_sets"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    archived_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 2: strategy_draft.py 구현**

`src/mctrader_engine/db/models/strategy_draft.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class StrategyDraft(Base):
    __tablename__ = "strategy_drafts"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_sets.id"), nullable=False, unique=True
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    updated_by: Mapped[str | None] = mapped_column(String(128))
```

- [ ] **Step 3: Commit**

```bash
cd c:\workspace\mclayer\mctrader-engine
git add src/mctrader_engine/db/models/strategy_set.py src/mctrader_engine/db/models/strategy_draft.py
git commit -m "feat(db): StrategySet + StrategyDraft 모델 추가"
```

---

### Task 2: StrategySetVersion 모델

**Files:**
- Create: `src/mctrader_engine/db/models/strategy_set_version.py`

- [ ] **Step 1: strategy_set_version.py 구현**

`src/mctrader_engine/db/models/strategy_set_version.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, JSON, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"
_VALID_STAGES = ("backtest", "paper", "live", "archived")


class StrategySetVersion(Base):
    __tablename__ = "strategy_set_versions"
    __table_args__ = (
        UniqueConstraint("strategy_set_id", "version"),
        UniqueConstraint("config_hash"),
        CheckConstraint(
            f"lifecycle_stage IN {_VALID_STAGES}",
            name="ck_ssv_lifecycle_stage",
        ),
        {"schema": _SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_sets.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(16), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    config_canonical: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_from_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    created_by: Mapped[str | None] = mapped_column(String(128))
    locked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
```

- [ ] **Step 2: Commit**

```bash
git add src/mctrader_engine/db/models/strategy_set_version.py
git commit -m "feat(db): StrategySetVersion 모델 추가 (immutable, config_hash 기반)"
```

---

### Task 3: Component + Layer + PromotionEvent + RuntimeOverride 모델

**Files:**
- Create: `src/mctrader_engine/db/models/strategy_set_component.py`
- Create: `src/mctrader_engine/db/models/strategy_set_layer.py`
- Create: `src/mctrader_engine/db/models/strategy_promotion_event.py`
- Create: `src/mctrader_engine/db/models/strategy_runtime_override.py`

- [ ] **Step 1: strategy_set_component.py**

`src/mctrader_engine/db/models/strategy_set_component.py`:

```python
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class StrategySetComponent(Base):
    __tablename__ = "strategy_set_components"
    __table_args__ = (
        UniqueConstraint("strategy_set_version_id", "producer_name"),
        {"schema": _SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id", ondelete="CASCADE"), nullable=False
    )
    producer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

- [ ] **Step 2: strategy_set_layer.py**

`src/mctrader_engine/db/models/strategy_set_layer.py`:

```python
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"
_VALID_LAYER_TYPES = (
    "signal_aggregation", "portfolio_construction",
    "position_management", "risk_constraint", "execution_planning",
)


class StrategySetLayer(Base):
    __tablename__ = "strategy_set_layers"
    __table_args__ = (
        UniqueConstraint("strategy_set_version_id", "layer_type", "ordinal"),
        CheckConstraint(
            f"layer_type IN {_VALID_LAYER_TYPES}",
            name="ck_ssl_layer_type",
        ),
        {"schema": _SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id", ondelete="CASCADE"), nullable=False
    )
    layer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    implementation_name: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

- [ ] **Step 3: strategy_promotion_event.py**

`src/mctrader_engine/db/models/strategy_promotion_event.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class StrategyPromotionEvent(Base):
    __tablename__ = "strategy_promotion_events"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id"), nullable=False
    )
    from_stage: Mapped[str] = mapped_column(String(16), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(16), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_runs.id")
    )
    gate_result_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    operator: Mapped[str | None] = mapped_column(String(128))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
```

- [ ] **Step 4: strategy_runtime_override.py**

`src/mctrader_engine/db/models/strategy_runtime_override.py`:

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, ForeignKey, Numeric, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class StrategyRuntimeOverride(Base):
    __tablename__ = "strategy_runtime_overrides"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    strategy_set_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id"), nullable=False, unique=True
    )
    max_notional_cap: Mapped[Decimal | None] = mapped_column(Numeric)
    kill_switch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    symbol_denylist: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
    updated_by: Mapped[str | None] = mapped_column(String(128))
```

- [ ] **Step 5: Commit**

```bash
git add \
  src/mctrader_engine/db/models/strategy_set_component.py \
  src/mctrader_engine/db/models/strategy_set_layer.py \
  src/mctrader_engine/db/models/strategy_promotion_event.py \
  src/mctrader_engine/db/models/strategy_runtime_override.py
git commit -m "feat(db): Component/Layer/PromotionEvent/RuntimeOverride 모델 추가"
```

---

### Task 4: PipelineEvent 모델 + strategy_runs 수정

**Files:**
- Create: `src/mctrader_engine/db/models/pipeline_event.py`
- Modify: `src/mctrader_engine/db/models/strategy_run.py`

- [ ] **Step 1: pipeline_event.py**

`src/mctrader_engine/db/models/pipeline_event.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from mctrader_engine.db.models.base import Base

_SCHEMA = "engine"


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default="gen_random_uuid()")
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey(f"{_SCHEMA}.strategy_runs.id"))
    strategy_set_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{_SCHEMA}.strategy_set_versions.id")
    )
    frame_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )
```

- [ ] **Step 2: strategy_run.py에 strategy_set_version_id 추가**

기존 `strategy_run.py`를 열어 `engine_id` 컬럼 아래에 다음을 추가:

```python
    # strategy_set_version_id 추가 (NULL 허용 — 기존 단일 전략 실행과 호환)
    strategy_set_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("engine.strategy_set_versions.id")
    )
    engine_version: Mapped[str | None] = mapped_column(String(64))
    input_data_version: Mapped[str | None] = mapped_column(String(64))
    result_summary: Mapped[dict | None] = mapped_column(JSON)
```

또한 파일 상단 import에 `from uuid import UUID`가 없으면 추가.

- [ ] **Step 3: Commit**

```bash
git add src/mctrader_engine/db/models/pipeline_event.py src/mctrader_engine/db/models/strategy_run.py
git commit -m "feat(db): PipelineEvent 모델 추가, strategy_runs에 version_id/result_summary 컬럼 추가"
```

---

### Task 5: __init__.py + alembic/env.py 업데이트

**Files:**
- Modify: `src/mctrader_engine/db/models/__init__.py`
- Modify: `alembic/env.py`

- [ ] **Step 1: __init__.py에 신규 모델 import 추가**

기존 `__init__.py`에 아래를 추가 (기존 import 유지):

```python
from mctrader_engine.db.models.strategy_set import StrategySet  # noqa: F401
from mctrader_engine.db.models.strategy_draft import StrategyDraft  # noqa: F401
from mctrader_engine.db.models.strategy_set_version import StrategySetVersion  # noqa: F401
from mctrader_engine.db.models.strategy_set_component import StrategySetComponent  # noqa: F401
from mctrader_engine.db.models.strategy_set_layer import StrategySetLayer  # noqa: F401
from mctrader_engine.db.models.strategy_promotion_event import StrategyPromotionEvent  # noqa: F401
from mctrader_engine.db.models.strategy_runtime_override import StrategyRuntimeOverride  # noqa: F401
from mctrader_engine.db.models.pipeline_event import PipelineEvent  # noqa: F401
```

- [ ] **Step 2: alembic/env.py에 신규 모델 import 추가**

기존 import 블록 아래에 추가:

```python
from mctrader_engine.db.models.strategy_set import StrategySet  # noqa: E402, F401
from mctrader_engine.db.models.strategy_draft import StrategyDraft  # noqa: E402, F401
from mctrader_engine.db.models.strategy_set_version import StrategySetVersion  # noqa: E402, F401
from mctrader_engine.db.models.strategy_set_component import StrategySetComponent  # noqa: E402, F401
from mctrader_engine.db.models.strategy_set_layer import StrategySetLayer  # noqa: E402, F401
from mctrader_engine.db.models.strategy_promotion_event import StrategyPromotionEvent  # noqa: E402, F401
from mctrader_engine.db.models.strategy_runtime_override import StrategyRuntimeOverride  # noqa: E402, F401
from mctrader_engine.db.models.pipeline_event import PipelineEvent  # noqa: E402, F401
```

- [ ] **Step 3: Python import 검증**

```bash
cd c:\workspace\mclayer\mctrader-engine
uv run python -c "from mctrader_engine.db.models import StrategySet, StrategySetVersion, PipelineEvent; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/mctrader_engine/db/models/__init__.py alembic/env.py
git commit -m "chore(db): 신규 Strategy Set 모델들을 __init__ + alembic/env 에 등록"
```

---

### Task 6: Alembic 마이그레이션 작성

**Files:**
- Create: `alembic/versions/0002_strategy_set_pipeline.py`

- [ ] **Step 1: 마이그레이션 파일 생성**

`alembic/versions/0002_strategy_set_pipeline.py`:

```python
"""strategy_set_pipeline

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_SCHEMA = "engine"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "strategy_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("owner", sa.String(128)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(128)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_set_id"),
        sa.ForeignKeyConstraint(["strategy_set_id"], [f"{_SCHEMA}.strategy_sets.id"]),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_set_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("lifecycle_stage", sa.String(16), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("config_canonical", postgresql.JSONB, nullable=False),
        sa.Column("created_from_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(128)),
        sa.Column("locked_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_set_id", "version"),
        sa.UniqueConstraint("config_hash"),
        sa.ForeignKeyConstraint(["strategy_set_id"], [f"{_SCHEMA}.strategy_sets.id"]),
        sa.ForeignKeyConstraint(["created_from_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"]),
        sa.CheckConstraint("lifecycle_stage IN ('backtest','paper','live','archived')", name="ck_ssv_lifecycle_stage"),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_set_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("producer_name", sa.String(128), nullable=False),
        sa.Column("params", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("params_hash", sa.String(64), nullable=False),
        sa.Column("weight", sa.Numeric(20, 10), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_set_version_id", "producer_name"),
        sa.ForeignKeyConstraint(["strategy_set_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"], ondelete="CASCADE"),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_set_layers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("layer_type", sa.String(32), nullable=False),
        sa.Column("implementation_name", sa.String(128), nullable=False),
        sa.Column("params", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("params_hash", sa.String(64), nullable=False),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_set_version_id", "layer_type", "ordinal"),
        sa.ForeignKeyConstraint(["strategy_set_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "layer_type IN ('signal_aggregation','portfolio_construction','position_management','risk_constraint','execution_planning')",
            name="ck_ssl_layer_type",
        ),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_promotion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_stage", sa.String(16), nullable=False),
        sa.Column("to_stage", sa.String(16), nullable=False),
        sa.Column("approved", sa.Boolean, nullable=False),
        sa.Column("evidence_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("gate_result_snapshot", postgresql.JSONB),
        sa.Column("operator", sa.String(128)),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["strategy_set_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"]),
        sa.ForeignKeyConstraint(["evidence_run_id"], [f"{_SCHEMA}.strategy_runs.id"]),
        schema=_SCHEMA,
    )

    op.create_table(
        "strategy_runtime_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_notional_cap", sa.Numeric),
        sa.Column("kill_switch", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("symbol_denylist", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(128)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_set_version_id"),
        sa.ForeignKeyConstraint(["strategy_set_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"]),
        schema=_SCHEMA,
    )

    op.create_table(
        "pipeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("frame_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("idempotency_key", sa.String(128), unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["run_id"], [f"{_SCHEMA}.strategy_runs.id"]),
        sa.ForeignKeyConstraint(["strategy_set_version_id"], [f"{_SCHEMA}.strategy_set_versions.id"]),
        schema=_SCHEMA,
    )

    # strategy_runs에 신규 컬럼 추가
    op.add_column("strategy_runs", sa.Column("strategy_set_version_id", postgresql.UUID(as_uuid=True)), schema=_SCHEMA)
    op.add_column("strategy_runs", sa.Column("engine_version", sa.String(64)), schema=_SCHEMA)
    op.add_column("strategy_runs", sa.Column("input_data_version", sa.String(64)), schema=_SCHEMA)
    op.add_column("strategy_runs", sa.Column("result_summary", postgresql.JSONB), schema=_SCHEMA)
    op.create_foreign_key(
        "fk_strategy_runs_set_version",
        "strategy_runs", "strategy_set_versions",
        ["strategy_set_version_id"], ["id"],
        source_schema=_SCHEMA, referent_schema=_SCHEMA,
    )

    # 인덱스
    op.create_index("idx_ssv_set_stage", "strategy_set_versions", ["strategy_set_id", "lifecycle_stage"], schema=_SCHEMA)
    op.create_index("idx_ssc_version", "strategy_set_components", ["strategy_set_version_id"], schema=_SCHEMA)
    op.create_index("idx_ssl_version_type", "strategy_set_layers", ["strategy_set_version_id", "layer_type"], schema=_SCHEMA)
    op.create_index("idx_sr_set_version", "strategy_runs", ["strategy_set_version_id"], schema=_SCHEMA)
    op.create_index("idx_spe_version_created", "strategy_promotion_events", ["strategy_set_version_id", "created_at"], schema=_SCHEMA)
    op.create_index("idx_pe_run_frame", "pipeline_events", ["run_id", "frame_id"], schema=_SCHEMA)
    op.create_index("idx_pe_event_type", "pipeline_events", ["event_type", "created_at"], schema=_SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_pe_event_type", "pipeline_events", schema=_SCHEMA)
    op.drop_index("idx_pe_run_frame", "pipeline_events", schema=_SCHEMA)
    op.drop_index("idx_spe_version_created", "strategy_promotion_events", schema=_SCHEMA)
    op.drop_index("idx_sr_set_version", "strategy_runs", schema=_SCHEMA)
    op.drop_index("idx_ssl_version_type", "strategy_set_layers", schema=_SCHEMA)
    op.drop_index("idx_ssc_version", "strategy_set_components", schema=_SCHEMA)
    op.drop_index("idx_ssv_set_stage", "strategy_set_versions", schema=_SCHEMA)

    op.drop_constraint("fk_strategy_runs_set_version", "strategy_runs", schema=_SCHEMA, type_="foreignkey")
    op.drop_column("strategy_runs", "result_summary", schema=_SCHEMA)
    op.drop_column("strategy_runs", "input_data_version", schema=_SCHEMA)
    op.drop_column("strategy_runs", "engine_version", schema=_SCHEMA)
    op.drop_column("strategy_runs", "strategy_set_version_id", schema=_SCHEMA)

    op.drop_table("pipeline_events", schema=_SCHEMA)
    op.drop_table("strategy_runtime_overrides", schema=_SCHEMA)
    op.drop_table("strategy_promotion_events", schema=_SCHEMA)
    op.drop_table("strategy_set_layers", schema=_SCHEMA)
    op.drop_table("strategy_set_components", schema=_SCHEMA)
    op.drop_table("strategy_set_versions", schema=_SCHEMA)
    op.drop_table("strategy_drafts", schema=_SCHEMA)
    op.drop_table("strategy_sets", schema=_SCHEMA)
```

- [ ] **Step 2: 마이그레이션 문법 검증 (offline)**

```bash
cd c:\workspace\mclayer\mctrader-engine
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mctrader" uv run alembic upgrade head --sql 2>&1 | tail -20
```

Expected: SQL 출력 (오류 없음). DB 연결 없이 SQL만 출력.

- [ ] **Step 3: Commit**

```bash
git add alembic/versions/0002_strategy_set_pipeline.py
git commit -m "feat(db/migration): 0002 Strategy Set Pipeline 테이블 8개 + strategy_runs 컬럼 추가"
```
