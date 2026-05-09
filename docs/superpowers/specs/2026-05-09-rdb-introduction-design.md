# RDB 도입 설계: mctrader PostgreSQL 통합

**날짜**: 2026-05-09  
**상태**: 승인됨  
**결정**: 접근법 B — Per-Repo 스키마 소유권 + Hub 공유 PostgreSQL 인프라

---

## 1. 배경 및 목적

mctrader는 현재 5가지 스토리지 계층을 사용한다:

| 계층 | 기술 | 위치 |
|------|------|------|
| 시계열 대용량 데이터 | Parquet (Hive-partitioned) | mctrader-data |
| Paper trading 원장 | SQLite (append-only event log) | mctrader-engine |
| Admin 감사 로그 | SQLite (WAL + hash chain) | mctrader-web |
| Heartbeat | JSON (atomic rename) | mctrader-data |
| 거래소 메타데이터 T4 | Parquet (daily snapshot) | mctrader-data |

이 구조에서 누락된 것: **운영 메타데이터의 관계형 조회 계층**. 심볼 유니버스 관리, 전략 런 이력, 주문 통합 조회, 포지션 추적, 백테스트 결과 비교가 파일 시스템 산재로 어렵다.

**목표**: PostgreSQL을 공유 운영 DB로 도입하여 관계형 조회 가능 데이터를 통합 관리하고, 기존 Parquet/SQLite 계층은 각 용도에 맞게 유지한다.

---

## 2. 아키텍처 결정

### 2.1 선택: 접근법 B (Per-Repo 스키마 소유권 + Hub 인프라)

```
mctrader-hub/docker-compose.yml
  └─ postgres:16-alpine  (named volume: mctrader_postgres)
        ├─ schema: market  (소유: mctrader-market)
        ├─ schema: engine  (소유: mctrader-engine)
        └─ schema: web     (소유: mctrader-web)
```

- PostgreSQL 서비스는 **hub docker-compose**가 제공
- 각 repo가 자기 schema를 **독립 Alembic**으로 관리
- 연결: `DATABASE_URL` env var (`postgresql://mctrader:${POSTGRES_PASSWORD}@postgres:5432/mctrader`)
- 각 repo Alembic `env.py`: `search_path={schema},public`

### 2.2 기존 스토리지 유지 (변경 없음)

| 데이터 | 스토리지 | 유지 이유 |
|--------|---------|----------|
| OHLCV/Tick/Orderbook T1-T5 | Parquet | 대용량 시계열, 컬럼형 스캔 최적화 |
| Paper ledger | SQLite append-only | 감사 추적 무결성, 이관 위험 HIGH |
| Admin audit log | SQLite WAL + hash chain | hash chain 구조 보존 |
| Heartbeat | JSON | liveness 경로, DB 의존 금지 |

### 2.3 선택하지 않은 접근법

- **접근법 A (Hub 단일 Alembic)**: hub가 모든 도메인 스키마를 알아야 함 → 강한 결합
- **접근법 C (CQRS/Projection)**: 이중 쓰기 복잡성, 동기화 lag. Phase 4에서 paper ledger에만 제한적 적용

---

## 3. DB 스키마

### 3.1 market schema (mctrader-market 소유)

```sql
-- 심볼 유니버스 (50개 관리)
CREATE TABLE market.symbols (
    id          SERIAL PRIMARY KEY,
    exchange    VARCHAR(32) NOT NULL,
    symbol      VARCHAR(32) NOT NULL,        -- "KRW-BTC"
    base_asset  VARCHAR(16) NOT NULL,
    quote_asset VARCHAR(16) NOT NULL,
    status      VARCHAR(16) NOT NULL,        -- active/halted/delisted
    score       NUMERIC(6,4),               -- 유니버스 선정 점수
    included_at TIMESTAMPTZ NOT NULL,
    excluded_at TIMESTAMPTZ,                -- NULL = 현재 포함
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (exchange, symbol)
);

-- 거래소 현재 실효 메타데이터 (Parquet T4 현재값 projection)
CREATE TABLE market.exchange_capabilities (
    id                      SERIAL PRIMARY KEY,
    exchange                VARCHAR(32) NOT NULL,
    symbol                  VARCHAR(32) NOT NULL,
    tick_size               NUMERIC(38,18),          -- Phase 2 nullable (Bithumb)
    min_order_qty           NUMERIC(38,18),          -- Phase 2 nullable
    min_order_notional_krw  NUMERIC(38,18),          -- Phase 2 nullable
    fee_maker               NUMERIC(10,8),           -- Phase 2 nullable
    fee_taker               NUMERIC(10,8),           -- Phase 2 nullable
    fetched_at              TIMESTAMPTZ NOT NULL,
    UNIQUE (exchange, symbol)
);
```

### 3.2 engine schema (mctrader-engine 소유)

```sql
-- 전략 실행 런
CREATE TABLE engine.strategy_runs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_name VARCHAR(128) NOT NULL,
    mode          VARCHAR(16) NOT NULL CHECK (mode IN ('backtest','paper','live')),
    status        VARCHAR(16) NOT NULL CHECK (status IN ('pending','running','completed','failed')),
    params        JSONB NOT NULL DEFAULT '{}',
    engine_id     VARCHAR(128),
    started_at    TIMESTAMPTZ,
    ended_at      TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 주문 이력 (신규 런부터; paper ledger SQLite는 계속 유지)
CREATE TABLE engine.orders (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            UUID REFERENCES engine.strategy_runs(id),
    exchange          VARCHAR(32) NOT NULL,
    symbol            VARCHAR(32) NOT NULL,
    side              VARCHAR(8) NOT NULL CHECK (side IN ('buy','sell')),
    order_type        VARCHAR(16) NOT NULL CHECK (order_type IN ('limit','market')),
    quantity          NUMERIC(38,18) NOT NULL,
    price             NUMERIC(38,18),
    status            VARCHAR(16) NOT NULL,
    exchange_order_id VARCHAR(128),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 체결 이력
CREATE TABLE engine.fills (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id  UUID NOT NULL REFERENCES engine.orders(id),
    price     NUMERIC(38,18) NOT NULL,
    quantity  NUMERIC(38,18) NOT NULL,
    fee       NUMERIC(38,18) NOT NULL DEFAULT 0,
    filled_at TIMESTAMPTZ NOT NULL
);

-- 포지션 스냅샷
CREATE TABLE engine.positions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID REFERENCES engine.strategy_runs(id),
    symbol      VARCHAR(32) NOT NULL,
    quantity    NUMERIC(38,18) NOT NULL,
    avg_cost    NUMERIC(38,18) NOT NULL,
    snapshot_at TIMESTAMPTZ NOT NULL
);

-- 백테스트 결과 요약
CREATE TABLE engine.backtest_results (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       UUID NOT NULL REFERENCES engine.strategy_runs(id),
    total_pnl    NUMERIC(38,18),
    sharpe_ratio NUMERIC(10,6),
    max_drawdown NUMERIC(10,6),
    total_trades INTEGER,
    win_rate     NUMERIC(6,4),
    params_hash  VARCHAR(64),
    computed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 알림/리스크 이벤트 로그
CREATE TABLE engine.alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID REFERENCES engine.strategy_runs(id),
    symbol          VARCHAR(32),
    severity        VARCHAR(16) NOT NULL CHECK (severity IN ('info','warning','critical')),
    alert_type      VARCHAR(64) NOT NULL,
    message         TEXT NOT NULL,
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

-- 엔진 상태
CREATE TABLE engine.engine_status (
    engine_id    VARCHAR(128) PRIMARY KEY,
    mode         VARCHAR(16) NOT NULL,
    status       VARCHAR(16) NOT NULL,
    config       JSONB NOT NULL DEFAULT '{}',
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.3 web schema (mctrader-web 소유)

```sql
-- 대시보드 설정
CREATE TABLE web.dashboard_configs (
    id         SERIAL PRIMARY KEY,
    config_key VARCHAR(128) NOT NULL UNIQUE,
    config     JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 알림 수신 채널
CREATE TABLE web.notification_channels (
    id           SERIAL PRIMARY KEY,
    channel_type VARCHAR(32) NOT NULL,          -- telegram/email/webhook
    target       VARCHAR(256) NOT NULL,         -- chat_id / email / URL
    severity_min VARCHAR(16) NOT NULL DEFAULT 'warning',
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 알림 발송 이력 (engine.alerts 참조는 앱 레이어에서 관리)
CREATE TABLE web.notification_dispatches (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id     UUID NOT NULL,
    channel_id   INTEGER NOT NULL REFERENCES web.notification_channels(id),
    status       VARCHAR(16) NOT NULL CHECK (status IN ('sent','failed','skipped')),
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

> **참고**: `engine.alerts` → `web.notification_dispatches` cross-schema 참조는 앱 레이어에서 참조 무결성 관리 (PostgreSQL cross-schema FK는 가능하나 독립 Alembic 관리와 충돌).

---

## 4. 마이그레이션 전략

### 4.1 기존 데이터 이관

| 데이터 | 현재 위치 | 이관 방식 | 위험도 |
|--------|----------|----------|--------|
| Exchange metadata T4 Parquet | mctrader-data | 일회성 배치 스크립트: 최신 `fetched_date` 레코드만 `market.exchange_capabilities`에 INSERT | LOW |
| Symbol universe (50개) | 코드/설정 분산 | 초기 INSERT 스크립트 (`market.symbols`) | LOW |
| Strategy runs (신규) | 없음 | Day-1부터 PostgreSQL 직접 저장 | N/A |
| Orders/fills (신규) | 없음 | Day-1부터 PostgreSQL 직접 저장 | N/A |
| Paper ledger SQLite | mctrader-engine | **미이관** — append-only 원본 보존 | HIGH → 유지 |
| Admin audit log SQLite | mctrader-web | **미이관** — hash chain 구조 보존 | HIGH → 유지 |

### 4.2 연결 패턴 (공통)

```yaml
# hub/docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mctrader
      POSTGRES_USER: mctrader
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - mctrader_postgres:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mctrader"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mctrader_postgres:
```

```bash
# scripts/init-db.sh
psql -v ON_ERROR_STOP=1 -U mctrader -d mctrader <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS market;
  CREATE SCHEMA IF NOT EXISTS engine;
  CREATE SCHEMA IF NOT EXISTS web;
EOSQL
```

```python
# 각 repo Alembic env.py 패턴
import os
from alembic import context

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

def run_migrations_online():
    schema = os.environ.get("DATABASE_SCHEMA", "public")
    connectable = engine_from_config(...)
    with connectable.connect() as connection:
        connection.execute(text(f"SET search_path TO {schema},public"))
        context.configure(connection=connection, ...)
        with context.begin_transaction():
            context.run_migrations()
```

---

## 5. Phase 실행 계획

### Phase 1: 기반 인프라 + 심볼/메타데이터 (기준선)

**작업**:
- hub `docker-compose.yml`에 `postgres:16-alpine` 서비스 추가
- hub `scripts/init-db.sh`: market/engine/web 스키마 생성
- mctrader-market: Alembic 초기화, `symbols` + `exchange_capabilities` 마이그레이션
- 이관 스크립트: T4 Parquet 최신 레코드 → `market.exchange_capabilities`
- 이관 스크립트: 50 심볼 → `market.symbols`

**완료 기준**: `SELECT COUNT(*) FROM market.symbols` = 50, `exchange_capabilities` 레코드 존재

### Phase 2: 전략 런 + 백테스트 결과

**작업**:
- mctrader-engine: Alembic 초기화, `strategy_runs` + `backtest_results` 마이그레이션
- engine: 새 런 생성 시 `strategy_runs` INSERT
- engine: 백테스트 완료 시 `backtest_results` INSERT

**완료 기준**: 웹 대시보드에서 런 목록 조회 및 Sharpe 기준 정렬 가능

### Phase 3: 알림 + 엔진 상태

**작업**:
- mctrader-engine: `alerts` + `engine_status` 마이그레이션
- mctrader-web: `notification_channels` + `dispatches` + `dashboard_configs` 마이그레이션
- engine: 리스크 게이트 이벤트 → `alerts` INSERT
- engine: heartbeat 수신 → `engine_status` UPSERT
- web: 알림 채널 설정 → `notification_channels`, 발송 후 `dispatches` INSERT

**완료 기준**: 리스크 게이트 발동 시 `alerts` 레코드 생성 + Telegram 발송 이력 기록

### Phase 4: 주문 이력 Projection

**작업**:
- mctrader-engine: `orders` + `fills` 마이그레이션
- 신규 paper/live 주문 → PostgreSQL 직접 기록 **+ SQLite ledger 이중 쓰기 유지** (SQLite는 source of truth, PostgreSQL은 조회 전용 read model)
- 검증 스크립트: SQLite 주문 이벤트 수 ↔ PostgreSQL orders 수 일치 확인 (불일치 시 SQLite 기준으로 재동기화)

**완료 기준**: 검증 스크립트 green, cross-mode 주문 조회 가능

### Phase 5: 포지션 스냅샷

**작업**:
- mctrader-engine: `positions` 마이그레이션
- 각 런 종료 시 포지션 스냅샷 저장
- PnL 계산과 positions 일치 검증

**완료 기준**: 런별 포지션 히스토리 조회 가능, PnL 수치 일치

### Phase 6: Paper Ledger 평가 (선택)

**의사결정 기준**:
- PostgreSQL orders/fills가 6개월 이상 안정적이면 SQLite ledger 이관 검토
- 이관 시: 이벤트 로그 replay → PostgreSQL + 해시 검증
- 미이관 시: SQLite source of truth 유지, PostgreSQL = read model 확정

---

## 6. 기술 선택 근거

| 결정 | 선택 | 이유 |
|------|------|------|
| RDB 엔진 | PostgreSQL 16 | 검증된 운영 안정성, JSONB params, Docker-friendly, TimescaleDB 불필요 (시계열은 Parquet) |
| ORM | SQLAlchemy 2.x | Python 생태계 표준, async 지원 |
| 마이그레이션 | Alembic | SQLAlchemy 공식 마이그레이션 도구 |
| 배포 | Docker named volume | 기존 `mctrader_data` 패턴 일관성 |
| 스키마 분리 | PostgreSQL schema namespace | repo별 독립 마이그레이션, 단일 DB 인스턴스 운영 |

---

## 7. 위험 및 완화

| 위험 | 수준 | 완화 |
|------|------|------|
| PostgreSQL 서비스 장애 시 거래 중단 | HIGH | paper ledger SQLite 유지 (fallback write path) |
| 스키마 마이그레이션 순서 충돌 | MEDIUM | init-db.sh가 스키마만 생성, 테이블은 각 repo Alembic |
| cross-schema FK 무결성 | MEDIUM | 앱 레이어에서 관리, 문서화 |
| 기존 exchange_capabilities nullable | LOW | Phase 2 nullable 필드 그대로 유지 |
| 백업 누락 | MEDIUM | `docker run ... pg_dump` 일일 크론 추가 (ADR-016 패턴 참조) |
