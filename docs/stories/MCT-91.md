---
story_key: MCT-91
story_issues:
  - repo: mclayer/mctrader-hub
    number: 93
status: phase:요구사항
---

# MCT-91: Collector HA — Writer + Heartbeat (X2 of MCT-89, re-registered)

- **Issue**: #93
- **Status**: phase:요구사항

## 1. 사용자 요구사항 (verbatim — Phase 2 후속 CFP 까지 CODEOWNERS manual review 로 변경 차단)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: mctrader-data 측 collector writer + heartbeat writer. 부모 Epic = MCT-89 (PR #90 main merged). Phase 1 spec/plan 의 X2 = `--node-id` CLI flag + partition writer `node=` level 적용 + heartbeat writer (atomic + 5s loop) + lineage `node_id`. ADR-009 §D2.1 / §D10.7 / §D11.8 amendment + heartbeat-schema.v1 contract 준수.)
(re-registration: 직전 issue #91 / PR #92 는 MCT-90 KEY 가 indicator library Epic 과 충돌해 close. 본 issue 의 sequential KEY 는 MCT-91 예상.)
## 2. 도메인 해석

본 Story 는 부모 Epic **MCT-89** (Collector HA — Active-Active Multi-Node + Shared Storage) 의 **X2 child slice** 로, mctrader-data 측 **collector writer + heartbeat writer 의 foundation** 을 implement 한다. Epic 16-row decision stack + Codex 7-area review (6/7 ADOPT) freeze 상태에서 코드 진입.

### 2.1 자동매매 도메인에서 본 child 의 위치

mctrader 는 6-repo 분산형 자동매매 시스템 (MCT-12 Epic ~ 현재 MCT-89). mctrader-data 는 backtest / WFO / Streamlit 의 **단일 데이터 source-of-truth (SoT)**. 본 X2 가 도입하는 변경은 *데이터 평면* 의 reliability foundation — execution / strategy / risk 평면 (mctrader-engine / mctrader-strategy / mctrader-risk) 은 **변경 0** (transparent).

부모 Epic MCT-89 의 6-child 분해 (§4 of MCT-89.md) 에서 X2 가 **다른 모든 child 의 prerequisite**:

- **X3** (scan + dedup) — X2 의 `node=` partition layout 위에서 read-side merge
- **X4** (coverage + diagnostic) — X2 의 heartbeat schema freeze 후 status CLI
- **X5** (ops scripts) — X2 의 `--node-id` flag + heartbeat path 위에서 systemd unit + Ansible
- **X6** (web status panel) — X2 의 heartbeat JSON 을 read
- **X7** (Epic close + Calibration) — X2~X6 모두 합쳐 양 node 30분 E2E demo

따라서 X2 는 **schema · path · contract freeze** 의 책임 (X3-X6 의 input 이 X2 의 output). schema breaking change 는 X2 close 후 minor amendment 만 허용.

### 2.2 DataEngineerAgent invariant 와 X2 의 관계

DataEngineerAgent (도메인 KB `docs/domain-knowledge/agent-overlays/data.md`) 의 핵심 책임 4 가지에 X2 가 미치는 영향:

| Invariant | X2 영향 | 근거 |
|---|---|---|
| Tick / Orderbook lossless (packet loss → backfill 의무) | **변경 0** | 양 node packet loss 는 HA 가 cover 하지 않음 (Epic out-of-scope, backfill 이 last line of defense) |
| DuckDB single-writer (multi-reader OK) | **변경 0** | collector storage = Parquet append-only. DuckDB 는 reader (backtest/WFO/web) 만 사용. 양 node 가 다른 `node=` partition 에 write → DuckDB 관점 single-writer 유지 |
| Parquet append-only | **유지 + 강화** | per-node partition split 이 contention 을 0 으로 (양 node 가 같은 file 을 만지지 않음) |
| received_at lookahead 방어 (`available_from_ts`) | **변경 0** | T2/T3 의 `received_at` semantics (ADR-009 §D10.4 / §D11.4) 은 node-local 그대로. dedup 은 `ts_utc` 기준 logical key (read-side X3 책임) |

### 2.3 Bithumb single-source 특성 (X2 scope boundary 결정)

양 node 가 **identical Bithumb public WS endpoint** 를 구독하는 active-active 모델 (Epic decision #2) 의 함의:

- **Bithumb 측 outage** (서버 down / WS endpoint 응답 무) = 양 node 동시 영향 → X2 (또는 부모 Epic 전체) 가 **cover 하지 않음**. Multi-network HA Epic (mctrader-hub 후속 candidate) 의 scope.
- **single-host failure** (process crash / OOM / host reboot / code deploy restart) = 한 node 만 영향 → 다른 node 가 단독 수집 → X2 의 partition 분리 + heartbeat liveness 가 cover 의 1차 메커니즘.
- **양 node 동시 packet loss** (LAN 내 network blip 등) = HA 도 cover 하지 않음 → DataEngineerAgent 의 backfill (Bithumb history REST API) 이 last line of defense.

이 boundary 는 사용자 verbatim 의 *"코드 수정사항 배포 와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자"* 와 정합 — X2 가 cover 하는 카테고리 = single-host failure (deploy 포함). Bithumb-side outage 는 본 child / 본 Epic 의 명시적 out-of-scope.

### 2.4 "데이터 순단" 의 도메인 정의

backtest user 입장에서 "순단" = scan API 의 row 누락. Tier 별 정의 차등:

- **T1 candle (closed bar)**: read-side gap **0** 이 목표 (양 node 중 1개라도 살아 있으면 cover, ADR-009 §D5 late correction 으로 mismatch 해소)
- **T2 tick**: best-effort (dedup 정확도 > 99% target — 같은 Bithumb stream 이라 byte-identical 기대 매우 높음, MCT-X3 Calibration C2 측정)
- **T3 orderbook**: best-effort (dedup 정확도 > 95% target — node-local reconstruction divergence 인정, MCT-X3 Calibration C2 측정)

X2 는 *writer 측* 만 — 실제 read-side gap 측정은 X3 (scan + dedup) 도착 후 가능. **X2 단독 merge 시점에는 read-side gap 보장이 미작동** (각 node partition 만 단독 scan, X3 가 union scan 도입). 이는 의도된 phase boundary — §5 Edge case 에서 명시.

## 3. 관련 ADR

X2 의 contract 진입 prerequisite 는 부모 Epic Phase 1 에서 freeze 됨 (PR #90 main merged, `bd5dde5`).

### 3.1 강한 관련 (직접 제약)

#### ADR-009 §D2.1 — Active-Active HA `node=` partition level + dedup contract anchor

**X2 enforcement scope**:

- **Partition path** (T1 / T2 / T3 공통): `.../date=YYYY-MM-DD/node=NODE_A/{collector_run_id}-{batch_seq}.parquet`
  - `node` = low cardinality 호스트 식별자 (e.g., `NODE_A` / `NODE_B`)
  - file name = `{collector_run_id}-{batch_seq}.parquet` (X2 의 신규 naming convention)
  - 단일 node 운영 시 `node=DEFAULT` (또는 hostname) — backward compat
- **Mixed legacy partition layout 지원 (영구)**:
  - Pre-HA partition (`node=` level 없음, X2 main merge 전 기존 mctrader-data 가 쓴 데이터) → reader 가 `node=DEFAULT` 로 취급
  - Post-HA partition (`node=NODE_A` 등 explicit) → 그대로 read
  - X2 는 **writer 측** 만 — mixed scan 의 reader 측 enforce 는 X3 의 책임 이지만, X2 가 도입하는 file-name 변경 (`{collector_run_id}-{batch_seq}.parquet` vs 기존 `part-{snapshot_id}.parquet`) 이 mixed scan 의 input 일관성을 깨지 않도록 reader 호환성 검증 책임은 X3 로 위임. X2 가 깨면 안 되는 invariant: legacy `_lineage_{snapshot_id}.json` sidecar 의 위치 / 형식 (lineage.py 기존 contract).
- **Lineage**: `_lineage.json` + parquet file metadata 양쪽에 `node_id` field 추가 (MCT-65 manifest 와 1:1 align, manifest.py 의 `run-{collector_run_id}.json` 에도 동일 추가).

#### ADR-009 §D10.7 — T2 tick logical key (fallback tuple only)

X2 **enforcement 범위 외** (read-side X3 책임). 단 X2 의 writer 가 logical key 의 6 필드 (`exchange, symbol, ts_utc, price, quantity, side`) 를 정확히 보존해야 X3 dedup 가능 → X2 의 writer schema 검증 의무.

#### ADR-009 §D11.8 — T3 orderbook logical key (fallback tuple only, best-effort)

§D10.7 동일 구조. X2 는 logical key 8 필드 (`exchange, symbol, ts_utc, event_type, side, level, price, quantity`) 보존만, dedup 자체는 X3.

#### heartbeat-schema.v1 (`docs/domain-knowledge/contracts/heartbeat-schema.v1.md`)

X2 의 신규 module (heartbeat writer) 의 **directly enforced contract**:

- **Path**: `<root>/market/manifest/heartbeat-{node_id}.json` (각 node 가 자기 file 만 write — cross-host write contention 0)
- **Atomic write 규약**: write-temp → fsync → rename (POSIX `rename(2)` atomic, NFS atomic rename within same directory)
- **Interval**: 5 seconds default (configurable via `--heartbeat-interval`)
- **JSON schema (v1)**: 12 top-level field (`schema_version` / `node_id` / `collector_run_id` / `version` / `started_at` / `now` / `uptime_seconds` / `ws_state` / `last_event_ts_per_tier` / `queue_depth` / `metrics{events_per_sec, dup_skip_count, quarantine_count, ws_reconnect_count, backfill_pending_seconds}`)
- **v1→v2 호환**: 새 field 추가 backward compatible. field 제거 / type 변경은 schema_version bump 의무 → X2 가 v1 contract 를 freeze 하므로 X2 close 후 v2 까지 변경 금지.

### 3.2 약한 관련 (배경 / 영향 0 명시 필요)

- **ADR-002 (TradeExecutor 3 mode)**: backtest / paper / live 의 same OHLCV view invariant. X2 는 *데이터 평면 writer* 만 변경 → executor (mctrader-engine / paper / live) 측 **영향 0** 명시. mode 간 reproducibility 그대로 보장.
- **ADR-003 H1 / ADR-005 path (c) / ADR-006 D10**: ADR-009 의 baseline 이지만 X2 가 직접 enforce 하지 않음.
- **ADR-010 (deploy artifact = git commit hash, no PyPI)**: X2 가 신규 CLI flag 도입 시 deploy contract 영향 0 (사용자 host 측 git pull + uv sync 그대로).

### 3.3 향후 amendment 가능성 (X2 외부)

- **Bithumb API 가 unique tx_id 제공 시**: ADR-009 §D10.7 minor amendment (logical key primary key 채택, fallback 보조). X2 schema 변경 없음 (`tick.v1` 의 8-col schema 그대로, dedup module 만 X3 에서 변경).
- **Bithumb API 가 sequence_id 제공 시**: §D11.8 minor amendment 동일 구조.
- **Mixed legacy migration Epic** (별도): pre-HA partition 폐기 시점은 별도 migration Epic 의 scope. X2 가 영구 backward compat 책임을 짊어지지 않음 (read-side X3 책임).

## 4. 관련 코드 경로

mctrader-data repo (`c:/workspace/mclayer/mctrader-data/`) 측 X2 변경 surface. 부모 Epic spec doc §5.2 의 12-entry surface table 중 **X2 child 에 해당하는 7-entry** (X3 scan-side / X4 coverage / X5-X7 = 별도 child Story 의 scope).

> ⚠️ Spec doc §5.2 의 일부 module path (`mctrader_data/storage/writer.py`, `mctrader_data/collector/__main__.py`) 는 hypothetical naming. 실제 repo layout 은 flat (`mctrader_data/storage.py`, `mctrader_data/collector.py`) — 아래 표는 actual repo 기준.

| Module | 변경 책임 | 비고 |
|---|---|---|
| `src/mctrader_data/cli.py` | `--node-id` (default = `socket.gethostname()`), `--heartbeat-interval` (default 5s), `--heartbeat-root` 신규 click option 추가. `collector` subcommand (`@click.option` line 197 부근) 에 wiring | `%H` (systemd specifier) 는 unit file 측에서 expand → CLI 는 받기만 |
| `src/mctrader_data/collector.py` | `--node-id` 받아서 internal collector run 에 propagate. heartbeat writer task 를 async loop 에 attach (5s interval, tier 별 `last_event_ts` hook 제공). `collector_run_id` 생성 시 node_id prefix 포함 (`A-{ts}` / `B-{ts}` 형식) | 기존 `async def run()` (line 73 / 175) 위치에 heartbeat task spawn |
| `src/mctrader_data/path.py` | `derive_partition_path()` (line 31) 에 `node_id` 파라미터 추가, leaf 직전에 `node={node_id}` Hive level 삽입. T1/T2/T3 호출자 모두 update | ADR-009 §D2.1 enforcement 핵심 위치 |
| `src/mctrader_data/storage.py` | `write_candles()` (line 78) 가 `node_id` arg 받아 path 와 file name (`{collector_run_id}-{batch_seq}.parquet`) 생성. parquet metadata 에 `node_id` field 추가 (pyarrow `metadata` 인자) | T1 writer |
| `src/mctrader_data/tick_storage.py` | `_derive_partition()` (line 136) 가 `node_id` 사용. `flush()` (line 99) 가 새 file naming 적용 | T2 writer. 기존 `part-{snapshot_id}.parquet` → `{collector_run_id}-{batch_seq}.parquet` 전환 (legacy mixed scan 은 X3 read 측 책임이므로 X2 는 forward-only) |
| `src/mctrader_data/orderbook_storage.py` | `_derive_partition()` (line 148) 가 `node_id` 사용. `flush()` (line 111) 동일 | T3 writer |
| `src/mctrader_data/heartbeat.py` (**신규**) | atomic JSON writer (write-temp → fsync → rename) + 5s async loop + tier 별 `last_event_ts` 갱신 hook + WS state / queue_depth / metrics 수집 hook | heartbeat-schema.v1 contract enforcement. `<root>/market/manifest/heartbeat-{node_id}.json` 위치 |
| `src/mctrader_data/lineage.py` | `write_lineage()` (line 15) 의 dict payload 에 `node_id` field 추가. `_lineage_{snapshot_id}.json` sidecar 위치 / file name 은 변경 0 (mixed scan 호환) | MCT-65 manifest 1:1 align |
| `src/mctrader_data/manifest.py` | `run-{collector_run_id}.json` payload 에 `node_id` field 추가 (heartbeat collector_run_id 와 동일 cross-reference) | manifest 위치 / naming 변경 0 |
| `tests/test_path.py` | `derive_partition_path(node_id=...)` parameter 추가에 따른 기존 fixture 업데이트 + node= level 검증 신규 case | regression 방어 |
| `tests/test_storage.py` / `test_tick_storage.py` / `test_orderbook_storage.py` | 신규 파일 naming + parquet metadata `node_id` 검증 | 기존 fixture 의 `part-{snapshot_id}.parquet` assertion 모두 update |
| `tests/test_lineage.py` / `test_collector_manifest.py` | `node_id` field 검증 추가 | |
| `tests/integration/test_heartbeat.py` (**신규**) | atomic write (write-temp → fsync → rename) 검증 + cross-host read simulation (tmpdir 두 process) + crash freshness (heartbeat 멈춤 → mtime 검증) | NFS 정확 emulation 불가 → tmpdir + os.replace + mtime 검증 |
| `tests/integration/test_active_active_writer.py` (**신규**) | 두 collector instance simulation (다른 `--node-id`) → 같은 root 에 write contention 0 + 양 partition 모두 정상 row | T1/T2/T3 모두 |

**X2 scope 외** (다른 child 책임):

- `scan.py` 신규 module + scan_*` API multi-node union → **X3** 책임
- `dedup.py` 신규 module + tier 별 logical key extractor + node priority + quarantine `active-active mismatch` reason → **X3** 책임
- `coverage.py` `tier_coverage` node 차원 + heartbeat-aware gap detection → **X4** 책임
- `cli.py status` 신규 subcommand (heartbeat + dedup metric 출력 + exit code) → **X4** 책임
- `tests/integration/test_active_active_dedup.py` (read-side dedup 검증) → **X3** 책임
- `tests/integration/test_rolling_deploy.py` → **X5** Story 또는 X7 E2E demo

## 5. 요구사항 확장 해석

### 5.1 사용자 verbatim 의 X2 sub-slice mapping

사용자 verbatim (Story §1):

> mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.

→ X2 가 직접 implement 하는 sub-slice (X2 외 슬라이스 는 별도 child Story):

| 사용자 어구 | X2 implicit assumption | 검증 위치 |
|---|---|---|
| "HA구성" | per-node `node=` partition split 이 multi-writer 를 가능하게 하는 *물리* 메커니즘 (write contention 0 의 prerequisite) | 신규 integration test `test_active_active_writer.py` |
| "코드 수정사항 배포" | rolling restart `serial: 1` 동안 한 node 가 down 일 때 **write 평면이 깨지지 않도록 file naming 이 collision-free** (`{collector_run_id}-{batch_seq}.parquet` — restart 마다 새 collector_run_id 발급, batch_seq 재시작 0 으로 reset 해도 collector_run_id 가 다르므로 collision 0) | file naming convention freeze (X2 scope), 실제 rolling 검증은 X5 + X7 E2E |
| "2개 이상의 Active Node 관리" | heartbeat liveness 가 *관리 도구* 의 input 제공 (cross-host visible artifact). X2 는 artifact write 만, 시각화 / alert 는 X4 (CLI) + X6 (web) | `test_heartbeat.py` cross-host read |
| "데이터 순단을 줄이고자" | T1 closed candle 기준 gap 0 의 *prerequisite* (양 node 가 동시에 write 가능). 실제 read-side gap 검증은 X3 의 scan API 도착 후 X7 E2E demo | X2 단독 검증 불가 — phase boundary, §5.5 사용자 확인 필요 |

### 5.2 Acceptance Criteria 도출 (X2 child slice)

Epic Story §6.3 의 8 blocking AC 중 **X2 child 가 enforce 가능한 4 entry**:

- **B1**: 두 node 동시 수집 — per-node partition write contention 0 + 양 partition 모두 정상 row → `test_active_active_writer.py`
- **B3**: heartbeat JSON atomic write (write-temp → fsync → rename) + cross-host read + 30s freshness gate → `test_heartbeat.py` (cross-host = tmpdir 2개 process simulation)
- **B5**: ADR-009 §D2 / §D10 / §D11 amendment 적용 + `_lineage.json` + parquet metadata 에 `node_id` → `test_path.py` / `test_lineage.py` / `test_collector_manifest.py`
- **B6 (X2 부분)**: T1 / T2 / T3 *writer schema* 가 logical key 6 / 8 필드 모두 보존 (dedup 자체는 X3) → `test_storage.py` / `test_tick_storage.py` / `test_orderbook_storage.py`

**X2 단독 enforce 불가** (X3-X7 책임):

- B2 (scan_* multi-node merge transparent) — X3
- B4 (rolling deploy read-side gap 0) — X5 + X7 E2E
- B6 dedup 자체 (T1 late correction / T2 quarantine / T3 best-effort) — X3
- B7 (quarantine `active-active mismatch` reason) — X3
- B8 (Streamlit `00_status` page) — X6

### 5.3 Edge cases 식별

1. **Hostname collision**: 양 node 가 `--node-id` 명시 안 하고 systemd unit 의 `--node-id=%H` 도 fallback 처럼 사용 시, hostname 이 동일하면 (e.g., 두 VM 이 같은 hostname) `node=NODE_A` / `node=NODE_B` 분기 실패 → write 충돌. **mitigation**: CLI 에서 `--node-id` resolution 시 hostname uniqueness 검증 또는 X5 의 systemd unit 이 `--node-id` 명시 의무 (host-side prereq). X2 는 default 만 제공, uniqueness 의무는 X5 README 로 위임.
2. **Heartbeat partial write (atomic 미작동)**: write-temp 까지 성공 후 fsync 이전 process kill → temp file 만 남고 main file 변경 없음 (consumer 입장 stale 한 last good state 유지). **OK** (atomic rename 의 의도).
3. **Heartbeat 무한 stale (process hang, write 자체 멈춤)**: file mtime 만 30s 초과 → consumer 가 yellow → red 단계로 escalate (heartbeat-schema.v1 의 freshness 판정). X2 는 mtime 만 노출, escalation 은 X4 (CLI) + X6 (web) 책임.
4. **Single-node 운영 backward compat**: 기존 사용자 (X2 도입 전 mctrader-data 사용자) 가 X2 신규 CLI 호출 시 `--node-id` 미지정 → default 가 `socket.gethostname()` → 단일 host 운영도 자연스럽게 `node=hostname` partition 으로 신규 write. legacy partition (`node=` 없음) 은 read 측 X3 의 `node=DEFAULT` 로 fallback. **X2 가 깨면 안 되는 것**: legacy partition 의 read 호환성을 X2 의 신규 file naming 이 깨지 않을 것 (X3 read 측 책임 이지만, X2 가 새로 쓰는 file 의 lineage sidecar 위치 / 형식이 legacy reader 호환).
5. **양 node clock drift**: NTP (chrony) 권장이지만 host-side prereq (X5 README). X2 의 heartbeat `now` field 가 양 node 에서 drift > 1s 면 freshness 판정 오류 가능. X2 는 단순 `datetime.now(UTC)` 만, drift 검증 의무 없음 (host-side prereq 위임).
6. **X2 단독 main merge 후 X3 도착 전 window**: read 측 (backtest user) 이 단일 node partition 만 보고 다른 node partition 을 못 봄 (scan API 가 multi-node union 미지원, X3 책임). 이 window 동안 backtest user 는 effectively single-node 데이터만 → **데이터 순단 보장 미작동**. → §5.5 escalation.

### 5.4 사용자 확인 필요 (blocking — Architect 진입 전)

**없음** — 모든 X2 scope 결정은 부모 Epic Phase 1 의 16-row decision stack 에서 사전 승인 완료, ADR-009 amendment freeze, heartbeat-schema.v1 freeze. X2 는 그 contract 의 enforcement 만.

### 5.5 사용자 정보 제공 (non-blocking — design lane 진입 가능)

- **X2 단독 main merge 후 X3 도착 전 window 의 데이터 순단 미작동**: 부모 Epic 의 phase 분해 의도된 boundary. 사용자가 X2 main merge 후 운영 환경에서 양 node 가동 시 *write contention 0 은 보장되지만 read 측 dedup 미작동* — 즉 backtest user 가 현재 어느 node 의 partition 을 보는지 명시적 결정 필요 (e.g., `--root` 으로 단일 node partition 만 가리키거나 X3 도착 대기). X3 는 부모 Epic Phase 3 일정 — 본 Story 의 PMO lane 이 cadence 결정.

## 6. 외부 지식 배경

본 절은 X2 implementation 의 외부 기술 / 표준 / OS-level 보장 의 배경. 부모 Epic §6 의 외부 지식 (Bithumb WS schema 검증 / NFS atomic / systemd / DuckDB Hive) 와 중복되는 항목은 **부모로 위임** 하고 X2 child specific 항목만 본 §6 에서 다룸.

### 6.1 POSIX `rename(2)` semantics (heartbeat atomic write)

heartbeat-schema.v1 의 atomic write 규약 (write-temp → fsync → rename) 의 OS-level 보장:

- **POSIX `rename(2)`**: same-directory 내 atomic. 동시 reader 는 old file 또는 new file 의 *어느 한쪽* 만 보고 결코 partial state 를 보지 않음 (모든 file system 의무).
- **NFSv4**: rename 자체 atomic (server-side). NFSv3 + close-to-open consistency 도 OK (consumer 가 mtime 으로 freshness 판정 시 close 후 mtime 갱신 보장).
- **NFSv2**: atomic rename 미보장 → host-side prereq (X5 README) 에서 NFSv4 권장 의무.
- **SMB / CIFS**: SMBv2+ 의 `FileRenameInformation` atomic. SMBv1 거부.
- **Ceph (CephFS)**: same-pool 내 rename atomic.

### 6.2 Python `os.replace()` cross-platform atomic

- `os.replace(src, dst)`: POSIX `rename(2)` + Windows `MoveFileEx(MOVEFILE_REPLACE_EXISTING)` wrapper. Windows 에서도 same-directory atomic 보장 (NTFS).
- `os.rename(src, dst)` 와 차이: `os.rename` 은 Windows 에서 `dst` 존재 시 OSError, `os.replace` 는 overwrite. heartbeat writer 는 매 5s 마다 overwrite 의무 → **`os.replace` 채택** (X2 implementation 의무).
- Python 3.3+ guaranteed.

### 6.3 `fsync` cost vs durability tradeoff (heartbeat 5s loop)

- `fsync(fd)` cost: typical NFS environment 에서 sub-ms (kernel buffer + NFS COMMIT operation). 5s loop 에서 한 번 호출 → CPU / IO 부담 무시 가능 (per-second overhead < 0.1%).
- **durability semantics**: fsync 가 호출된 시점까지의 write 가 storage 측 commit. fsync 미호출 시 OS crash → temp file 손실 가능 (단, atomic rename 의 atomicity 자체는 손상 없음 — 이전 main file 이 그대로 유지).
- **5s loop 에서 fsync 의 의미**: heartbeat freshness 판정 (mtime > 30s = red) 의 **lower bound** 가 5s + fsync time + rename time. fsync 없이 rename 만 하면 mtime 갱신은 즉시지만 **content 가 storage 에 commit 되지 않은 상태에서 consumer 가 read 하면 stale content 가능** (NFS client 측 cache). → fsync 필수.

### 6.4 systemd `Restart=always` + `RestartSec` semantics (X2 의 CLI 정합)

X2 의 CLI flag (`--node-id`, `--heartbeat-interval`, `--heartbeat-root`) 는 systemd unit 의 `ExecStart` line 에서 expand 됨 (X5 책임). systemd 측 보장:

- `Restart=always`: process exit (정상 / 비정상 무관) 시 `RestartSec` 후 재시작.
- `RestartSec=5`: 본 design 의 default. process crash → 5s 후 재시작 → heartbeat freshness 30s gate 안에 회복.
- `StartLimitBurst` / `StartLimitIntervalSec` default = 5 회 / 10 초 (폭주 방지). 본 collector 처럼 5s restart loop 가 정상 cycle 인 경우 default 가 trigger 가능 → host-side prereq (X5 README) 에서 `StartLimitBurst=20` 등 override 권장.
- systemd unit specifier `%H` (hostname) 는 systemd 측에서 expand → X2 의 CLI 는 그냥 string 으로 받음.

### 6.5 DuckDB Hive partition pruning + `node=` low-cardinality column

- DuckDB 0.9+ 가 Hive partitioning 자동 인식 (`SELECT * FROM '*.parquet' WHERE node='NODE_A'` → `node=NODE_A` partition 만 scan).
- `node` column = low cardinality (호스트 수 만큼, typical 2~3) → partition pruning 효율 매우 높음.
- X2 는 **writer 측** 만 — DuckDB pruning 자체는 X3 의 scan API 가 leverage. 단 X2 의 partition layout 이 Hive convention (`key=value` directory) 을 정확히 따라야 X3 가 무수정 leverage 가능 → X2 의 `derive_partition_path()` 변경에서 검증 의무.

### 6.6 pyarrow Decimal128 + Parquet write performance (T1 byte-identical 양 node 기대)

- Decimal(38,18) (ADR-009 §D1) → pyarrow `decimal128(38, 18)` native type. byte-level deterministic encoding (RFC 8259 / Parquet spec 기준).
- 양 node 가 같은 Bithumb stream 을 받으면 T1 candle (closed bar, OHLCV) 은 **byte-identical Parquet row** 기대 → ADR-009 §D5 의 late correction 정책 (append-only + serving view 최신 win) 이 mismatch 시에만 발동, 양 node 정상 시는 idempotent skip.
- X2 의 `write_candles()` 가 pyarrow `metadata` 인자에 `node_id` 추가해도 row data 자체 byte-identical (metadata 는 file footer, dedup 의 logical key scope 외).

### 6.7 Bithumb WS schema — X2 writer 측 검증 의무 (부모 Epic 검증 결과 활용)

부모 Epic §6 + ADR-009 §D2.1 amendment 의 검증 결과:

- **transaction stream**: `cont_no` / `tx_id` / `seq` 부재 (`mctrader-market-bithumb` `ws_mapping.py` `TransactionEvent` 검증) → T2 logical key = fallback 6-tuple (`exchange, symbol, ts_utc, price, quantity, side`)
- **orderbook stream**: sequence_id / version 부재 → T3 logical key = fallback 8-tuple

X2 writer 가 보존해야 할 schema field (= dedup module X3 의 input):

| Tier | 보존 의무 column | nullable |
|---|---|---|
| T1 candle | `exchange, symbol, timeframe, ts_utc, open, high, low, close, volume, value` (ADR-009 §D1 16-col 중 logical key 영향 column) | none |
| T2 tick | `exchange, symbol, ts_utc, price, quantity, side` (`raw_json` 은 dedup 제외, ADR-009 §D10.7) | side / price / quantity / ts_utc 모두 non-null |
| T3 orderbook | `exchange, symbol, ts_utc, event_type, side, level, price, quantity` (`raw_json` 제외, ADR-009 §D11.8) | 모두 non-null (delta 의 `level=-1` 고정) |

X2 의 writer schema 검증 책임 = 위 column 이 모두 정확히 write 되는지 unit test. logical key 의 실제 dedup 알고리즘은 X3 책임.

### 6.8 Out-of-scope 외부 지식 (부모 Epic 또는 후속 Epic 위임)

- **NFS / SMB / Ceph 의 atomic rename 자세한 비교** → 부모 Epic §6 (Bithumb WS schema 검증 결과 절 다음)
- **systemd unit template detail** → X5 (mctrader-hub `scripts/ha/`) Story
- **Streamlit `00_status` page rendering** → X6 Story
- **Multi-network HA / cloud + homelab mix** → 후속 Epic candidate

## 7. 설계 서사

*(Architect 작성 예정 — placeholder)*

## 8. 개발 서사

*(DeveloperPL 작성 예정 — Phase 2 PR에서)*

## 9. 품질 게이트 이력

*(Review/Test PL 작성 예정 — Phase 2 PR에서)*

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

*(FIX 발생 시 append)*

## 11. 회고

*(PMOAgent 작성 예정 — Story 완료 시)*
