# ADR-016: Audit log append-only with hash chain (Admin Engine Control Panel)

- **Status**: Accepted
- **Date**: 2026-05-06
- **Story**: MCT-97
- **Authors**: ArchitectAgent (chief) + DataMigrationArchitectAgent (deputy)
- **Reviewers**: ArchitectPLAgent

## 컨텍스트

MCT-97 AC-4 는 모든 control 명령에 대한 append-only audit log 와 forensic-grade tamper detection 을 요구한다. 후보:

- (a) JSONL — 단순, 그러나 query 부담 + tamper detection 수동
- (b) SQLite single file (WAL mode) + hash chain — query SQL 표준, 의존성 0 (Python `sqlite3`), backup 단순
- (c) mctrader-engine `event_store` 통합 — trading domain pollution
- (d) 외부 SIEM (Splunk / Datadog) — solo dev overkill

또한 mctrader-web `data/` 디렉토리 미존재 (현재 grep 결과). audit DB 위치 convention 결정 필요.

## 결정

**(b) SQLite (WAL) + hash chain** 채택. data/ 디렉토리 신규 생성.

### Storage 위치

`mctrader-web/data/admin_audit.sqlite`

- 신규 디렉토리 `mctrader-web/data/` (gitignore 처리). 운영 시 backup target.
- 환경변수 override: `MCTRADER_ADMIN_AUDIT_PATH` (테스트 / 다중 환경 격리).

### Schema (DDL)

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT    NOT NULL,           -- ISO8601 UTC, server clock
    actor        TEXT    NOT NULL,           -- token-derived user id
    role         TEXT    NOT NULL,           -- viewer | operator | admin
    engine_class TEXT    NOT NULL,           -- collector | paper_runner | backtest | wfo | market_gw
    engine_id    TEXT    NOT NULL,           -- engine-id-naming.v1.md SSOT
    action       TEXT    NOT NULL,           -- start | stop | restart | trigger | cancel | rbac_reject | sm_violation
    params_hash  TEXT    NOT NULL,           -- sha256(canonical_json(params))
    request_id   TEXT    NOT NULL,           -- Idempotency-Key value
    outcome      TEXT    NOT NULL,           -- ok | conflict | rbac_reject | sm_violation | timeout | error
    latency_ms   INTEGER NOT NULL,           -- request handling latency
    source_ip    TEXT    NOT NULL,           -- request.client.host
    prev_hash    TEXT    NOT NULL,           -- previous row's row_hash (genesis: "0"*64)
    row_hash     TEXT    NOT NULL,           -- sha256(prev_hash || canonical(row except row_hash))
    UNIQUE(request_id)                       -- Idempotency-Key dedupe at DB level
);

CREATE INDEX IF NOT EXISTS idx_audit_ts        ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_engine_id ON audit_log(engine_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor     ON audit_log(actor);
```

PRAGMA: `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=OFF`, `busy_timeout=5000`.

### Append protocol

```python
def append_audit_row(conn, row: AuditRow) -> int:
    with conn:  # implicit BEGIN/COMMIT
        prev = conn.execute(
            "SELECT row_hash FROM audit_log ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev[0] if prev else "0" * 64
        row.prev_hash = prev_hash
        row.row_hash = compute_row_hash(prev_hash, row)
        conn.execute("INSERT INTO audit_log (...) VALUES (...)", row.as_tuple())
        return cur.lastrowid
```

- Hash 함수: `sha256( prev_hash || canonical_json(row except row_hash) )`. canonical_json = sorted keys + UTF-8 + no spaces.
- DB UPDATE / DELETE 차단:
  - 앱 가드: ORM-level write 함수는 `INSERT INTO audit_log` 만 허용 (별도 helper, 다른 connection 객체 미노출)
  - DB 가드: PRAGMA application_id 설정 + 검증 CLI 가 SQL `UPDATE audit_log` / `DELETE FROM audit_log` row count 0 invariant 검증

### Hash chain verification CLI

```
mctrader-web admin audit verify [--from SEQ] [--to SEQ]
```

- 동작: 각 row 의 `prev_hash` 가 직전 row 의 `row_hash` 와 동일한지, `row_hash` 가 재계산된 값과 동일한지 검증
- 출력: `OK seq=12345 (verified N rows)` 또는 `MISMATCH at seq=NNN (expected=..., got=...)`
- 사용 시점: 운영자 manual review trigger (panel 경고 시) + 일일 backup cron 후 검증
- panel runtime 검증 안 함 (성능 부담 회피, on-demand only)

### Backup + retention

- **Backup**: 일일 cron (POSIX `cron` / Windows Task Scheduler) → `data/backups/admin_audit_<YYYYMMDD>.sqlite` (SQLite `VACUUM INTO` 또는 `.backup` API). solo dev 책임 — Story §7.J Risk 항목으로 docs.
- **Retention**: 최소 90일 (Phase 6 default). 환경변수 `MCTRADER_AUDIT_RETENTION_DAYS` override.
- **Pruning policy**: hash chain invariant 보존 — old row 삭제 대신 **별도 archive DB 로 export** + main DB 의 genesis 를 archive 마지막 hash 로 reset (chain continuation). archive 자체는 read-only.
- Pruning 미구현 시 단일 SQLite 파일 무한 grow — solo dev 환경에서 1 년 < 100 MB 추정 (control 분당 30 회 × 365 일 ≈ 16 M row × 200 bytes 하한). 단일 파일 운용 가능. 본 ADR 은 pruning 미강제 (P6 retention cron 만).

### 데이터 무결성 invariant (DataMigrationArchitect 변호)

1. **Schema migration**: schema 변경 시 신규 column 은 `ALTER TABLE ADD COLUMN ... DEFAULT ...` 만 (NOT NULL 신규 column 은 default 필수). DROP COLUMN 금지 — 호환 유지.
2. **Idempotency**: `Idempotency-Key` 가 `request_id` UNIQUE column 에 매핑 → DB-level dedupe. 24h 후 cleanup 별도 cron (DELETE `WHERE ts < now - 24h AND outcome = 'ok'` — 단, hash chain 영향 — 본 ADR 은 idempotency cache 를 audit 와 분리: 별도 `idempotency_cache` table 추가 → audit row 는 영구).

   **수정**: idempotency dedupe 는 별도 table 분리.

   ```sql
   CREATE TABLE IF NOT EXISTS idempotency_cache (
       request_id  TEXT PRIMARY KEY,
       response    TEXT NOT NULL,
       created_at  TEXT NOT NULL
   );
   CREATE INDEX IF NOT EXISTS idx_idemp_created ON idempotency_cache(created_at);
   ```

   audit_log 의 `request_id` 는 non-unique index (filter용) 로 변경.

3. **Backup integrity**: backup 직후 hash chain CLI 자동 실행 — 실패 시 backup 롤백 + alert.
4. **Cross-platform**: SQLite WAL 은 Windows + Linux 동등. 단, network filesystem (NFS / SMB) 위 placement 금지 (WAL fsync 보장 안 됨) — 본 ADR 은 local fs 만 가정.
5. **Concurrent access**: WAL mode 로 다중 reader + 단일 writer 자연 지원. control plane append 와 panel query 동시 진행 안전.

## 대안 검토

| 대안 | Reject 사유 |
|------|-------------|
| (a) JSONL append | query SQL 부재, hash chain 검증 수동 |
| (c) event_store 통합 | trading domain (mctrader-engine) 와 admin 책임 경계 무너짐 |
| (d) 외부 SIEM | solo dev overkill, 의존성 + 비용 |
| Postgres / MySQL | solo dev 인프라 부담, SQLite 성능 충분 |

## 결과

- `mctrader-web/data/admin_audit.sqlite` (WAL) + 신규 `data/` 디렉토리 (gitignore)
- 두 table: `audit_log` (영구 hash chain) + `idempotency_cache` (24h cleanup)
- `mctrader-web/src/mctrader_web/api/admin/audit.py` append helper + query API
- `mctrader-web` CLI subcommand: `admin audit verify` + `admin audit backup`
- Story file §11.1-§11.5 의 마이그레이션 절차는 본 ADR 을 1차 reference 로 인용

## 후속 영향

- ADR-014 (plane 분리) 의 control-side 만 audit append (data plane 미적용)
- ADR-015 (SM) 의 모든 transition (성공 / 실패 / no-op / SM 위반 / RBAC 거부) audit row 발생
- AC-4 (audit) 4 항목 모두 충족
- engine-id-naming.v1.md 의 `engine_id` 와 `engine_class` 분리 보장
