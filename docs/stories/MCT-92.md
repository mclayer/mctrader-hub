---
story_key: MCT-92
story_issues:
  - repo: mclayer/mctrader-hub
    number: 97
status: phase:요구사항
---

# MCT-92: Collector HA — Scan-side Merge + Dedup (X3 of MCT-89)

- **Issue**: #97
- **Status**: phase:요구사항

## 1. 사용자 요구사항 (verbatim — Phase 2 후속 CFP 까지 CODEOWNERS manual review 로 변경 차단)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: mctrader-data 측 scan-side merge + dedup. 부모 Epic = MCT-89. X2 (MCT-91, mctrader-data 0.6.0 main merged) 의 후속. Phase 1 spec/plan 의 X3 = `scan_*` multi-node union + tier 별 logical key dedup + `dedup.py` 신규 module + quarantine `active-active mismatch` reason. ADR-009 §D2.1 mixed legacy 영구 지원 enforce + §D10.7 T2 6-tuple + §D11.8 T3 8-tuple best-effort dedup target T2>99% / T3>95%. X2-X3 window 운영 caveat 해소 의무 — recursive partition glob `**/node=*/**/*.parquet` + legacy partition `node=DEFAULT` mapping + 양 file naming `part-*.parquet` / `{collector_run_id}-{batch_seq}.parquet` 호환.)

## 2. 도메인 해석

본 Story 는 부모 Epic **MCT-89** (Collector HA — Active-Active Multi-Node + Shared Storage) 의 **X3 child slice** 로, sister Story **MCT-91 (X2)** 가 freeze 한 **writer 측 contract** (partition `node=` Hive level / file naming `{collector_run_id}-{batch_seq}.parquet` / heartbeat-schema.v1 / lineage `node_id`) 위에 **read-side merge + dedup** 을 도입하여 backtest user 의 *데이터 순단 0* 보장을 X2-X3 window caveat 까지 포함해 완성 마감한다.

### 2.1 자동매매 도메인에서 본 child 의 위치 — read-side dedup = "데이터 순단 0" 의 *완성 지점*

mctrader 6-repo 분산형 자동매매 시스템에서 mctrader-data 는 backtest / WFO / Streamlit 의 **단일 데이터 source-of-truth (SoT)**. X2 가 *물리적 write contention 0* 을 달성한 시점부터 본 X3 진입까지의 window 는 **양 node partition 에 데이터가 분산된 채로 read-side 가 union/dedup 하지 못하는 transitional 상태** — X2 §8.4 운영 caveat 의 (a) `X3 도착 대기` / (b) `collector daemon 비활성화 + backfill 만` / (c) `--node-id=DEFAULT` 단일 node 로 active-active 효과 우회. 이 3 옵션 모두 사용자 수동 결정에 의존하는 임시 운영 지침이고, X3 가 main merge 되는 순간 옵션 (a) 가 자연 해소된다 — 즉 **X3 = X2-X3 window caveat 의 단일 termination event**.

부모 Epic 16-row decision stack (`#7 Read-side merge 위치 = scan_* API 내장 transparent`) 과 ADR-009 §D2.1 의 mixed legacy partition 영구 지원이 본 X3 의 implementation contract 의 anchor — engine / web / WFO 측 caller 변경 0 (transparent). X3 후 X4 (coverage + status CLI) / X5 (ops scripts) / X6 (web panel) / X7 (Calibration + E2E demo) 가 parallel 진행 가능 (Epic §6.2 dependency graph).

### 2.2 DataEngineerAgent invariant 와 X3 의 관계 — 모든 invariant 유지 (변경 0)

DataEngineerAgent (도메인 KB `docs/domain-knowledge/agent-overlays/data.md`) 의 핵심 책임 4 가지 모두 X3 가 **변경 0** — X3 는 read-side 의 transparent layer 이고 writer 측 invariant 에 영향을 미치지 않는다:

| Invariant | X3 영향 | 근거 |
|---|---|---|
| Tick / Orderbook lossless (packet loss → backfill 의무) | **변경 0** | dedup 은 양 node 가 *받은* event 의 중복 제거이지 packet loss 자체를 cover 하지 않음 (양 node 동시 packet loss 는 backfill 책임, Epic §2.2 동일) |
| DuckDB single-writer (multi-reader OK) | **변경 0** | X3 는 reader (DuckDB :memory: 또는 in-process pyarrow) 만 — writer path 변경 없음 |
| Parquet append-only | **변경 0** | X3 는 read-only — append-only 보장에 영향 없음 |
| received_at lookahead 방어 (`available_from_ts`) | **변경 0** | X3 의 dedup 은 `ts_utc` 기준 logical key. ADR-009 §D10.4 / §D11.4 의 `received_at <= simulated_clock` filter 는 dedup 후 단계 (orderbook_replay.py 의 `simulated_clock` 인자) 그대로 — dedup 은 그 filter 의 위 stage 에서 작동 |

**유일하게 의미 있는 영향**: §D11.6 의 "duplicate event with different hash = halt" 정책이 ADR-009 §D11.8 amendment 에 따라 **single-node 환경 (legacy 또는 `node=DEFAULT`) 에 한정 적용**. multi-node 환경 (`node=NODE_A` + `node=NODE_B`) 에서는 §D11.8 의 logical key + quarantine 정책이 우선 — halt 가 아닌 quarantine + 진행. 이는 X3 가 enforce 하는 도메인 정책의 *유일한 변경 surface* (writer 가 아니라 read-side reconstruction 의 fail-closed criterion 이 multi-node 에서 완화).

### 2.3 Bithumb single-source 특성 (X3 scope boundary 재확인)

양 node 가 **identical Bithumb public WS endpoint** 를 구독하는 active-active 모델 (Epic decision #2). X2 의 도메인 해석 §2.3 과 동일 boundary, X3 가 도입하는 *추가 boundary*:

- **양 node 동시 outage** (Bithumb 측 / LAN 전체 / 양 host 동시 down) = X3 도 cover 하지 않음. dedup 은 *양 node 가 모두 정상으로 받은 event 의 중복 제거*이므로, 둘 다 못 받은 event 를 살리지 못한다. backfill (DataEngineerAgent 책임) 이 last line of defense.
- **single-host failure 동안의 부분 cover** = X3 의 핵심 가치. NODE_A 가 down 일 때 NODE_B partition 만 scan → row 누락 0. 양 node 정상일 때 dedup 후 중복 제거 → row 중복 0.
- **양 node divergence (T2/T3 best-effort)** = node-local `received_at` fallback / Bithumb frame split / reconnect 직후 baseline 차이 (ADR-009 §D11.8 명시). X3 는 dedup 정확도 < 100% 인정하고 T2 > 99% / T3 > 95% target 으로 운영 — 미달 row 는 quarantine reason `active-active mismatch` 로 isolation (audit trail 보존).

### 2.4 "데이터 순단 0" 의 X3 시점 도메인 정의

backtest user 입장에서 "순단" = scan API 의 row 누락. X2 시점에는 **의도된 phase boundary 로 보장 미작동** (X2 §2.4 § 5.5 에서 명시). X3 main merge 이후 tier 별 정의 활성화:

- **T1 candle (closed bar)**: read-side gap **0** 활성화 — 양 node 중 1개라도 살아 있으면 cover. logical key `(exchange, symbol, timeframe, ts_utc)` 4-tuple, content mismatch 시 ADR-009 §D5 late correction (append-only + serving view 최신 win) 으로 해소 — quarantine emit 하지 않음 (T1 의 special-case)
- **T2 tick**: dedup 정확도 > 99% target 활성화 — same Bithumb stream 이라 byte-identical 기대 매우 높음. logical key `(exchange, symbol, ts_utc, price, quantity, side)` 6-tuple. content mismatch (raw_json 제외 7-col) → `active-active mismatch` quarantine
- **T3 orderbook**: dedup 정확도 > 95% target 활성화 — node-local reconstruction divergence 인정 (frame split / received_at fallback / reconnect baseline). logical key `(exchange, symbol, ts_utc, event_type, side, level, price, quantity)` 8-tuple, level=-1 fixed for delta. content mismatch → quarantine

**Calibration C2 (X7 Story scope)** 가 위 target 의 실데이터 측정 — X3 자체 AC 는 *measurable hooks 노출* (dup_skip_count / quarantine_count cumulative metric 을 heartbeat-schema.v1 `metrics` field 에 emit) 까지.

### 2.5 X2-X3 window caveat 의 X3 측 termination 책임

X2 §8.4 (Codex F-7 PUSH-BACK) 의 운영 옵션 (a) `X3 도착 대기` 가 본 X3 main merge 시점에 자연 해소되려면, X3 의 reader API 가 다음 prerequisite 모두 enforce 의무 (X2 §8.4 X3 prerequisite checklist 와 일치):

1. **recursive partition glob** `**/node=*/**/*.parquet` — 모든 `node=` partition 을 scan candidate 로 발견
2. **legacy partition** (`node=` level 없음, X2 main merge 전 데이터) → `node=DEFAULT` 로 mapping (ADR-009 §D2.1 mixed legacy 영구 지원)
3. **legacy file naming** (`part-{snapshot_id}.parquet`) + 신규 (`{collector_run_id}-{batch_seq}.parquet`) **양쪽 read** — file name pattern 두 가지 모두 인식

이 3 prerequisite 을 X3 가 enforce 하는 시점이 X2-X3 window 의 단일 termination event. **X3 가 깨면 안 되는 invariant**: paper mode (`mode=paper`) partition (paper_storage.py) 은 X2 의 `node=` level 도입 외부 — `node=` 미적용 paper partition 도 read-side 에서 자연스럽게 처리되어야 함 (paper_storage.py 가 derive_partition_path 호출 시 `node_id=None` 사용 = 기존 동작 그대로). 즉 `node=DEFAULT` mapping 은 historical mode 의 legacy 에만 적용, paper mode 는 별도 layout 으로 영향 0.

## 3. 관련 ADR

X3 의 contract 진입 prerequisite 는 부모 Epic Phase 1 에서 freeze 됨 (PR #90 main merged, `bd5dde5`) + sister X2 (PR #8) 가 writer 측 enforcement 완료. X3 는 **read-side enforcement** 와 **§D11.6 fail-closed multi-node 완화** 의 양 축에서 영향.

### 3.1 강한 관련 (직접 제약)

> ⚠️ **Spec ↔ ADR supersedence note** (Codex F-1 escalation 1): parent spec doc `docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md` §3.2 line 134 의 "T1 conflict = quarantine + node priority" 표현은 ADR-009 §D2.1 / §D5 의 "T1 = late correction + no quarantine" 으로 **superseded**. ADR amendment 가 freeze 된 contract — Spec doc 의 해당 line 은 outdated. 본 Story 의 §3.1 / §3.2 / §5.2 / §6.4 모두 ADR 본문 기준 작성.

#### ADR-009 §D2.1 — Mixed legacy partition 영구 지원 + Active-Active dedup contract anchor

**X3 enforcement scope** (writer X2 가 path level 만 enforce 했고, **read-side mixed scan transparent + dedup 알고리즘 자체 = X3 책임**):

- **Mixed legacy partition 영구 지원 (X3 의 핵심 의무)**:
  - **Pre-HA partition** (`node=` level 없음) → reader 가 `node=DEFAULT` 로 *매핑* (file system 에 실제 `node=DEFAULT` directory 가 없어도 scan 결과에서는 그렇게 보이도록). partition pruning 적용 가능 — Hive partitioning 이 `node=` 없는 directory 를 자연스럽게 처리하도록 DuckDB `hive_partitioning=true` 의 missing-key handling + caller 측 `WHERE node='NODE_A' OR node IS NULL` 등의 explicit filter 처리 둘 중 하나 선택 (Architect 결정).
  - **Post-HA partition** (`node=NODE_A` / `node=NODE_B` 등 explicit) → 그대로 read.
  - **caller 변경 0** (engine / web / WFO 측 transparent — 기존 scan API signature 유지). 이는 §D2.1 amendment 본문 명시 의무.
- **Active-Active dedup contract** (T1/T2/T3 공통, §D2.1 anchor 절):
  - read-side `scan_*` API 가 multi-node partition union + tier 별 logical key dedup
  - **node priority**: alphabetical / inventory 순 (deterministic). `NODE_A > NODE_B > ... > NODE_DEFAULT` (uppercase ASCII order 의 자연 결과).
  - **content mismatch handling**:
    - **T1 candle**: §D5 의 기존 late correction policy 와 align — append-only + serving view 가 최신 값 win. quarantine emit 하지 않음 (T1 special-case).
    - **T2 tick / T3 orderbook**: 신규 `active-active mismatch` quarantine reason emit. §D10.7 / §D11.8 의 logical key 정의 참조.
- **Lineage**: X2 가 이미 `_lineage.json` + parquet metadata 에 `node_id` 추가 완료. X3 는 *읽는 쪽* — quarantine artifact 의 audit trail 에 양 node 의 `node_id` 모두 포함 의무.

#### ADR-009 §D5 — T1 late correction policy alignment (T1 dedup 의 conflict resolution)

X3 의 T1 dedup 은 **새로운 정책 도입이 아니라 §D5 기존 정책의 multi-node 확장 적용**:

- 기존 §D5: "Duplicate (`exchange, symbol, timeframe, ts_utc`): 동일 hash = idempotent / 다른 값 = late correction (append-only + serving view)"
- X3 multi-node 적용: 같은 logical key 4-tuple 로 양 node 의 row 발견 시:
  - byte-identical (모든 OHLCV column 동일) → idempotent skip (X2 §6.6 의 byte-identical 기대 정합)
  - mismatch → late correction = serving view 의 "최신 값" 정의를 multi-node 에 어떻게 적용? **Architect 결정 필요** — 후보:
    - (i) `received_at` MAX (양 node 의 row 중 더 늦게 도착한 쪽이 win) — late correction 의도와 가장 정합
    - (ii) node priority alphabetical (NODE_A win) — §D2.1 의 T2/T3 정책과 동형, 단순
    - (iii) ADR-009 §D5 의 "serving view" 가 dedup output stream 자체이므로 ts_utc per logical key 에 대해 ASC iter 시 node priority 만으로 결정 (ii 와 동일)

#### ADR-009 §D10.7 — T2 tick logical key (X3 의 핵심 enforcement target)

X3 가 **directly enforce**:

- **Logical key**: `(exchange, symbol, ts_utc, price, quantity, side)` 6-tuple
- **dedup procedure** (§D10.7 본문, X3 의 `dedup.py` 신규 module 의 spec):
  1. multi-node partition union scan (Hive `node=` partition pruning 후 모든 node 순회)
  2. 동일 logical key tuple 발견 시 **node priority** alphabetical 적용
  3. content (raw_json 제외 7-col) 일치 → idempotent skip
  4. content mismatch → **`active-active mismatch` quarantine** emit (signal: tier=tick / node_a / node_b / logical_key / diff_summary)
- **Timestamp tolerance**: server-side `contDtm` 인 row 는 strict equality 기대. message ts 부재로 `received_at` fallback 채워진 row 는 ms-tolerance (default ±100ms). **정확 threshold 는 X7 Calibration C2 freeze** — X3 는 default ±100ms 로 implement, configurable parameter 노출.
- **Dedup 정확도 목표**: > 99% (X7 Calibration C2 측정 의무, X3 자체 AC 는 metric 노출 hook까지)
- **raw_json 정책**: dedup output 의 raw_json 은 node priority 우선 row 의 값 채택 (X3 가 enforce)

#### ADR-009 §D11.8 — T3 orderbook logical key (X3 best-effort enforcement)

§D10.7 동일 구조 + best-effort 명시:

- **Logical key**: `(exchange, symbol, ts_utc, event_type, side, level, price, quantity)` 8-tuple. delta event = `level=-1` 고정.
- **Best-effort divergence source 인정** (§D11.8 본문):
  - Snapshot frame split (Bithumb snapshot 을 multiple frame 으로 split → 양 node 의 frame 분할 경계 차이)
  - Reconnect 직후 baseline (양 node reconnect 시점 다름)
  - received_at fallback (server-side ts 부재)
- **Dedup 정확도 목표**: > 95% (X7 Calibration C2 측정)
- **§D11.6 와의 관계 (X3 의 enforcement 핵심 분기)**:
  - **single-node 환경** (legacy 또는 `node=DEFAULT` 단독) → §D11.6 의 기존 fail-closed (duplicate event with different hash = halt) 그대로 적용
  - **multi-node 환경** (`node=NODE_A` + `node=NODE_B`) → §D11.8 의 logical key + quarantine 정책이 우선 — halt 가 아닌 quarantine + 진행
  - **이 분기 자체가 X3 의 implementation 책임** — multi-node 감지는 scan 단계에서 partition tree 의 distinct `node=` 값 개수 ≥ 2 또는 explicit caller hint 로 결정 (Architect spec 결정)

#### Quarantine 정책 확장 — `active-active mismatch` reason 신규 (X3 의 신규 enforcement)

X2 의 §3 / §4 에는 quarantine reason 신규가 X3 책임이라 명시 됨. X3 의 `quarantine.py` 확장:

- 기존 reason: `dup-different-hash` (§D11.6) / 기타 schema 위반
- **신규 reason** `active-active mismatch` (X3 도입):
  - tier (`tick` / `orderbook` / 미사용 `candle`)
  - logical_key (tuple 직렬화)
  - node_a / node_b (alphabetical 순서)
  - diff_summary (어느 column 이 다른지 — 향후 root cause analysis 용 audit data)
  - **artifact location** (Architect 결정): `<root>/market/manifest/quarantine/active-active-mismatch/...` 또는 기존 quarantine sidecar 패턴 확장

### 3.2 약한 관련 (배경 / 영향 0 명시 필요)

- **ADR-002 (TradeExecutor 3 mode)**: backtest / paper / live 의 same OHLCV view invariant. X3 는 *read-side transparent* — paper mode (paper_storage.py) 는 `node=` level 외부 영향 0, executor 측 (mctrader-engine / paper / live) 변경 0.
- **ADR-003 H1 / ADR-005 path (c) / ADR-006 D10**: ADR-009 baseline. X3 가 직접 enforce 하지 않음.
- **ADR-010 (deploy artifact = git commit hash)**: X3 가 mctrader-data minor bump (0.6.0 → 0.7.0) 만 — deploy contract 영향 0.
- **heartbeat-schema.v1**: X3 가 `metrics.dup_skip_count` / `metrics.quarantine_count` cumulative counter 를 emit. schema 변경 없음 (X2 가 이미 v1 contract 의 11 top-level + 5 nested freeze 완료) — X3 는 그 5 nested 중 2 개 (dup_skip_count / quarantine_count) 의 *의미 있는 값* 을 처음으로 produce. 0 → non-zero 시점이 X3 main merge.

### 3.3 향후 amendment 가능성 (X3 외부)

- **Bithumb API 가 unique tx_id / sequence_id 제공 시**: §D10.7 / §D11.8 minor amendment (logical key primary key 채택, fallback 보조). X3 의 `dedup.py` module signature 만 확장 — backward compat.
- **Mixed legacy migration Epic** (별도): pre-HA partition 폐기 시점은 별도 migration Epic. X3 가 영구 backward compat 책임을 짊어진 것은 §D2.1 freeze.
- **ms-tolerance threshold final value**: X7 Calibration C2 의 task. X3 는 default ±100ms + configurable parameter 노출까지.
- **T2 → T1 candle aggregation ordering** (Codex F-3 escalation 3, **explicit out-of-scope**): backtest engine 또는 collector 측 candle close 가 T2 tick 을 aggregate 해 T1 candle 을 구성하는 path — 본 X3 의 scope 외. X3 는 *각 tier 의 read-side dedup* 만, cross-tier aggregation 은 별도 lane (mctrader-engine candle aggregation 또는 backtest engine 의 candle close 로직) 의 의무. 본 amendment 를 explicit 하게 명시함으로써 caller (engine / WFO) 가 X3 dedup 후 결과를 입력으로 받아 candle aggregation 시 ordering / dedup 책임 분리 명확.

## 4. 관련 코드 경로

mctrader-data repo (`c:/workspace/mclayer/mctrader-data/`) 측 X3 변경 surface. 본 §4 = X3 의 code/test surface **약 12-entry** (spec §5.2 의 12-entry surface 중 X3 구현 대상 5 + 신규 test 5 + X3 영향 받지만 변경 0 인 wrapper 2 의 합).

> ⚠️ Spec doc §5.2 의 일부 module path (`mctrader_data/storage/scan.py`, `mctrader_data/storage/dedup.py`) 는 hypothetical naming. 실제 repo layout 은 flat (`mctrader_data/storage.py`, neo `mctrader_data/dedup.py`) — 아래 표는 actual repo 기준. dedup module 을 *신규 flat module* 로 둘지 *기존 storage.py 안에 함수* 로 둘지 = Architect 결정 (§7).

| Module | 변경 책임 | 비고 |
|---|---|---|
| `src/mctrader_data/dedup.py` (**신규**) | tier 별 logical key extractor (`tick_logical_key()` / `orderbook_logical_key()` / `candle_logical_key()`) + node priority alphabetical resolver + content mismatch detector (raw_json 제외 column hash 또는 row equality) + ms-tolerance helper (default ±100ms, configurable) + `active-active mismatch` quarantine emit hook | X3 의 핵심 신규 module. T1/T2/T3 차등 정책 (§D5 align / §D10.7 / §D11.8 + best-effort). 단일 node 환경 vs multi-node 환경 분기 (§D11.6 vs §D11.8) 결정 함수도 본 module 에 포함 |
| `src/mctrader_data/storage.py` | `scan_candles()` (line 172) 가 multi-node partition union 지원. 기존 `_resolve_scan_paths()` (line 139) 의 glob 이 `**/*.parquet` 이라 leaf 의 `node=` Hive level 자동 인식 (DuckDB `hive_partitioning=true` 옵션 line 208 이미 enabled — partition column 으로 자연 노출). 신규 의무: T1 candle dedup (§D5 align + late correction multi-node 적용) — `dedup.py` 의 `candle_logical_key()` 호출 | T1 reader 측. 기존 DuckDB `UNION ALL BY NAME` (line 207) 패턴이 multi-glob union 지원 — partition pruning 은 DuckDB hive 자동. SQL `WHERE` clause 또는 후처리 dedup loop |
| `src/mctrader_data/orderbook_replay.py` | `scan_ticks()` (line 154) / `scan_orderbook_events()` (line 186) / `tier_coverage()` (line 340) — pyarrow 기반 read 패턴 (DuckDB 미사용). **`_read_parquet_rows()` (line 137)** 의 `part_dir.glob("*.parquet")` (line 145) 가 leaf directory 단일 level 만 scan — **X3 의 enforcement 핵심 변경 위치**: leaf 가 `date=YYYY-MM-DD/` 인 경우 (legacy / `node_id=None`) 와 `date=YYYY-MM-DD/node=NODE_A/*.parquet` 인 경우 양립 대응. recursive `**/*.parquet` glob 또는 `node=*` 명시 walk 후 union | T2/T3 reader 측. **`tier_coverage()` 의 `collector_run_ids` harvest (line 394-398)** 가 `part-*.parquet` pattern 만 인식 — X2 의 신규 file naming `{collector_run_id}-{batch_seq}.parquet` 도 인식하도록 pattern 확장 의무 (X2 §8.4 Codex F-7 명시 prereq). dedup 적용은 `scan_ticks` / `scan_orderbook_events` 내 sort 직후 또는 별도 함수 |
| `src/mctrader_data/quarantine.py` (**확장 또는 신규** — repo 에 별도 module 존재 여부 X2 에서 명시 없음) | `active-active mismatch` reason 신규 추가. 기존 reason 패턴 (`dup-different-hash` 등) 과 동일 구조. signal field: `tier` / `node_a` / `node_b` / `logical_key` / `diff_summary` / `received_at_a` / `received_at_b` (audit trail). artifact location = `<root>/market/manifest/quarantine/active-active-mismatch/<date>/<symbol>-<run-id>.json` 또는 sidecar 패턴 — Architect 결정 | 기존 quarantine 정책이 mctrader-data repo 에 존재하는지 X3 Phase 2 진입 시 확인 의무 (현재 X3 lane 에서는 read-only — Mapper 수준 분석 외부). 미존재 시 X3 가 quarantine.py 신규 module 도입 책임 |
| `src/mctrader_data/path.py` | **변경 0** — X2 가 `derive_partition_path(node_id=None)` (line 31, 39) 도입 완료, default `None` 으로 legacy compat 유지. X3 read-side 는 `node_id` 기반 path build 가 아니라 **glob walk** 으로 모든 node 발견 — path.py 의 build helper 는 호출 안 함 | reader 의 inverse — path build 가 아닌 path discover. line 60-70 의 leaf assembly 이해는 필요하지만 변경 없음 |
| `src/mctrader_data/storage.py:_resolve_scan_paths` | 기존 glob `**/*.parquet` (line 154) 이 이미 recursive — `node=` level 도 자동 포함. **변경 0** 또는 minor (legacy `node=` 없는 partition 의 row 도 hive_partitioning 이 자연 처리하는지 검증). DuckDB hive partitioning 이 missing key 를 어떻게 처리하는지 = §6 Researcher 외부 지식 영역 | T1 reader 의 path resolution. legacy partition (no `node=`) 에서 hive column 이 NULL 로 노출되는지 / 별도 `node=DEFAULT` mapping 이 caller 측 책임인지 결정 |
| `tests/test_dedup.py` (**신규**) | `dedup.py` 의 logical key extractor unit test (T1 4-tuple / T2 6-tuple / T3 8-tuple). node priority alphabetical 검증. content mismatch detector (byte-identical row vs 1-column diff). ms-tolerance ±100ms 경계 검증 (boundary value test). raw_json 제외 column hash 검증. T1 late correction (§D5 align) vs T2/T3 quarantine 의 분기 검증 | X3 신규 module 의 unit test. mock data 만 사용 (file system 미사용) |
| `tests/test_storage.py` | 기존 `test_storage.py` 에 multi-node `scan_candles` 검증 추가: 두 partition (`node=NODE_A` + `node=NODE_B`) 에 같은 logical key 4-tuple 의 row write 후 scan → dedup 결과 1-row only. legacy partition (`node=` 없음) + post-HA partition (`node=NODE_A`) mixed scan → 양쪽 모두 read | T1 integration. 기존 test 는 single-node 만 검증 |
| `tests/test_orderbook_replay.py` 또는 신규 split | `scan_ticks()` / `scan_orderbook_events()` multi-node + dedup 검증. T2 byte-identical row dedup → 1 row. T3 mismatch row → quarantine emit + 살아남은 row = node priority NODE_A. `tier_coverage()` 의 `collector_run_ids` harvest 가 신규 file naming `{collector_run_id}-{batch_seq}.parquet` 인식 검증 (X2 §8.4 prereq) | T2/T3 integration |
| `tests/integration/test_active_active_dedup.py` (**신규**) | 두 collector instance simulation (X2 의 `test_active_active_writer.py` 패턴 재사용) → write → X3 의 scan API 로 read → dedup 결과 검증 + quarantine artifact 존재 검증. T1/T2/T3 모두 (T1 = late correction align / T2 = byte-identical dedup / T3 = best-effort dedup + mismatch quarantine) | X3 의 핵심 E2E test (X2 §3 / §4 명시 surface) |
| `tests/integration/test_legacy_partition_compat.py` (**신규**) | mixed legacy partition (`node=` 없음) + post-HA partition 같은 root 안 공존 시 read transparent 검증. paper mode partition (`mode=paper`) 영향 0 검증 (`node=` level 외부). file naming `part-{snapshot_id}.parquet` (legacy) + `{collector_run_id}-{batch_seq}.parquet` (HA) 혼재 시 read 양쪽 모두 | ADR-009 §D2.1 mixed legacy 영구 지원 enforcement test |
| `tests/integration/test_quarantine_active_active.py` (**신규** 또는 기존 quarantine test 확장) | T2 mismatch row → `active-active mismatch` quarantine artifact 생성 + counter 증가 검증. T3 same. T1 = late correction align 으로 quarantine 미발생 (negative test) | quarantine reason 신규의 enforcement test |

**X3 scope 외** (다른 child 책임):

- `coverage.py` `tier_coverage` node 차원 + heartbeat-aware gap detection → **X4** 책임
- `cli.py status` 신규 subcommand (heartbeat + dedup metric 출력 + exit code) → **X4** 책임
- ops scripts (systemd unit + Ansible) → **X5** 책임
- web panel `pages/00_status.py` → **X6** 책임
- Calibration C2 (dedup 정확도 측정) + 양 node 30분 E2E demo → **X7** 책임

**version bump**: mctrader-data 0.6.0 → 0.7.0 (minor — read-side capability 추가, breaking change 0).

## 5. 요구사항 확장 해석

### 5.1 사용자 verbatim 의 X3 sub-slice mapping

사용자 verbatim (Story §1):

> mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.

→ X3 가 직접 implement 하는 sub-slice (X3 외 슬라이스 는 별도 child Story):

| 사용자 어구 | X3 implicit assumption | 검증 위치 |
|---|---|---|
| "HA구성" | per-node `node=` partition write 위에서 read-side 가 transparent merge — engine/web/WFO 측 caller 변경 0. 즉 X3 가 *HA 구성을 데이터 평면 reader 까지 완성* | `test_active_active_dedup.py` E2E (caller signature 무변경 검증) |
| "코드 수정사항 배포" | rolling restart `serial: 1` 동안 한 node 의 partition 만 살아 있을 때도 read-side 가 단일 node partition 에서 정상 row yield (legacy partition `node=DEFAULT` mapping 과 동일 메커니즘) | `test_legacy_partition_compat.py` (single-node 환경 read 검증) |
| "2개 이상의 Active Node 관리" | dedup metric (dup_skip_count / quarantine_count cumulative) 를 heartbeat-schema.v1 `metrics` 5-nested 중 2 개에 emit — 관리 도구 (X4 status CLI / X6 web panel) 의 input 제공. **X3 자체는 metric 노출 hook까지** — 시각화 / alert 는 X4/X6 책임 | `dedup.py` metric counter API + heartbeat producer 측 hook (X2 가 이미 producer freeze, X3 는 counter increment 만) |
| "데이터 순단을 줄이고자" | T1 closed candle 기준 read-side gap **0** 활성화 (X2 단독에서는 미작동, X3 가 termination event). T2 > 99% / T3 > 95% best-effort dedup 정확도 활성화. **X2-X3 window caveat 의 단일 termination event 이 곧 X3 main merge** | `test_active_active_dedup.py` T1 gap 0 + T2/T3 dedup ratio + `test_legacy_partition_compat.py` X2-X3 window 시 단일 node partition fallback 검증 |

### 5.2 Acceptance Criteria 도출 (X3 child slice)

Epic Story §6.3 의 8 blocking AC 중 **X3 child 가 enforce 가능한 4 entry**:

- **B2 (X3 의 핵심 AC)**: `scan_*` 가 multi-node partition merge + logical key dedup transparent (engine/web 변경 0) → `test_active_active_dedup.py` (caller signature 무변경) + `test_legacy_partition_compat.py` (mixed legacy 영구 지원)
- **B6 dedup 자체 (X3 부분)**: T1 / T2 / T3 dedup contract 모두 unit + integration test (T3 = best-effort 명시) → `test_dedup.py` (logical key extractor unit) + `test_active_active_dedup.py` (T1 late correction align / T2 byte-identical / T3 best-effort + quarantine emit)
- **B6 (X2 부분 보완)**: T1 / T2 / T3 *writer schema* 가 logical key 6 / 8 / 4 필드 모두 보존했음을 read 측에서도 *재확인* (X2 가 이미 enforce, X3 가 read 단계에서 dedup 적용 시 자연 검증)
- **B7**: quarantine `active-active mismatch` reason 신규 + counter 노출 → `test_quarantine_active_active.py` (artifact 생성) + `dedup.py` 의 quarantine_count counter API + heartbeat `metrics.quarantine_count` emit 검증

**X3 단독 enforce 불가** (X2/X4-X7 책임):

- B1 (write contention 0) — X2 enforced (X3 read 측 자연 inheritance)
- B3 (heartbeat freshness gate) — X2 producer + X4 consumer (X3 의 metric counter 는 X4 가 read)
- B4 (rolling deploy read-side gap 0) — X3 + X5 + X7 E2E. X3 자체는 single-node partition fallback 의 read 가능성만 검증
- B5 (ADR-009 amendment 적용 + node_id metadata) — X2 enforced
- B7 web banner — X6 책임 (X3 는 quarantine artifact 생성까지)
- B8 (Streamlit `00_status` page) — X6
- C1 (write throughput per node) — X7 Calibration
- C2 (scan + dedup latency overhead) — X7 Calibration (X3 는 dedup 알고리즘 implementation **+ measurable hooks** (dup_skip_count / quarantine_count counter API + dedup latency timer hook) 까지, 실측은 X7). **X3 implementation must be measurable for C2** (Codex F-4 NIT) — dedup 알고리즘이 single-pass / 메모리 bounded / latency profileable 의무.

### 5.3 Edge cases 식별

1. **content mismatch 식별 임계** (T2/T3 의 핵심 design decision): 두 node 의 row 가 logical key tuple 동일 + 비-key column (T2 의 raw_json 제외 0 column, T3 의 raw_json 제외 0 column — logical key 가 모든 비-raw_json field 포함) 일치 여부 검증. T2 의 경우 logical key 가 6-tuple 인데 schema 가 8 col (ts_utc + received_at + 6 key field + raw_json — 즉 raw_json 외 received_at 만 비-key) → **received_at 차이는 mismatch 인가?** **답**: received_at 은 node-local fallback 가능 (server-side ts 부재 시) → **mismatch 로 판정 안 함** (양 node received_at 자연 차이 인정). 즉 T2 의 mismatch 판정은 *raw_json 제외 + received_at 제외 = logical key 외 사실상 0 column* — logical key 일치 자체가 byte-identical 의미. T3 동일 — logical key 가 8 col 모두 (raw_json/received_at 제외 모든 비-key) 포함하므로 mismatch 가 row 동일성과 일치. **이 분석이 §D10.7 / §D11.8 본문의 "content (raw_json 제외 7-col / 9-col 의 비-key field) 일치 → idempotent skip" 의미** — T2/T3 모두 사실상 received_at 도 제외한 logical-key-only 비교 = byte-identical of dedup-relevant content.

2. **late correction race (T1)**: 같은 logical key 4-tuple 의 row 가 양 node 에 도착하는 시간 차이 (양 node 동시 receive 후 partition 에 write 까지의 미세 차이). **byte-identical 기대** (X2 §6.6) — Bithumb 이 closed bar 만 broadcast 하므로 OHLCV row 가 양 node 에서 deterministic byte-identical. mismatch 발생 시 §D5 late correction 정책: append-only + serving view 최신 win — multi-node 적용은 §3.1 의 후보 (i) `received_at` MAX 또는 (ii) node priority alphabetical. **Architect 결정 필요** — §3.1 명시.

3. **late-arriving event order (T2/T3)**: 양 node 의 같은 ts_utc event 가 partition 에 different file_offset 으로 도착. 기존 sort key `(ts_utc ASC, received_at ASC, file_offset ASC)` (orderbook_replay.py line 181 / 209) 가 dedup 직전 stage 의 결정성 보장. dedup 단계에서 logical key 동일 row 를 만나면 node priority 적용. **결정성**: scan 결과 stream 의 row order 가 deterministic (same input → same output). file_offset 이 양 node 의 다른 partition file 이므로 양 node 가 같은 alphabetical node priority 만 enforce 하면 deterministic.

4. **single-node 환경에서 multi-node 정책 오작동 방지**: legacy partition (`node=` 없음) 또는 `--node-id=DEFAULT` 단일 node 운영 시 X3 의 dedup 이 발동하면 안 됨 (자기 자신의 row 를 dup 으로 판정 가능). **mitigation**: scan 단계에서 distinct `node=` 값 개수 ≥ 2 일 때만 multi-node mode 활성화. legacy partition 의 hive `node` column = NULL or `DEFAULT` 단일 → single-node mode → §D11.6 fail-closed 그대로 적용 (halt on dup-different-hash).

5. **mixed legacy + post-HA 의 single-node window**: X2 main merge 직후 한 node 만 새 file naming + `node=` partition 쓰고 다른 node 는 아직 legacy 사용 (rolling deploy 진행 중) → root 안에 legacy partition (no `node=`) + `node=NODE_A` 같이 존재. distinct `node=` 값 개수 = 1 (only NODE_A explicit + legacy 가 DEFAULT mapping) 또는 2 (NODE_A + DEFAULT). **mitigation**: legacy 를 `DEFAULT` 로 mapping 한 후 distinct count ≥ 2 면 multi-node mode 활성. NODE_A vs DEFAULT 의 row 는 정상 dedup (DEFAULT 가 alphabetical 로 lower → NODE_A win).

6. **paper mode partition 영향 0 검증**: paper_storage.py (`mode=paper`) 가 `node=` level 외부 — paper_storage 의 `derive_partition_path` 호출은 `node_id=None` (line 51 명시 시그니처 미사용 + path.py default `None`). X3 의 multi-node mode 가 paper mode partition 을 잘못 multi-node 로 판정하면 안 됨. **mitigation**: scan 시 mode 차원 별도 (mode=historical scan 과 mode=paper scan 이 별 root path) — 자연 isolated.

7. **quarantine artifact 위치 (Architect 결정)**: X3 가 quarantine 을 어디 write? 후보:
   - (a) `<root>/market/manifest/quarantine/active-active-mismatch/<date>/<symbol>.json` — sidecar 위치
   - (b) 기존 quarantine.py 의 artifact 패턴 재사용 (X3 Phase 2 진입 시 mctrader-data repo 의 quarantine module 존재 여부 확인 의무)
   - (c) parquet sidecar `_quarantine_{collector_run_id}.json` per partition leaf

8. **DuckDB Hive partitioning 의 missing-key handling** (storage.py 의 T1 reader 측): `hive_partitioning=true` 옵션 (line 208) 이 partition tree 에서 어떤 node 는 `node=NODE_A` 가 있고 어떤 node 는 없는 mixed 상태를 어떻게 처리하는지 = 외부 지식 영역 (§6 Researcher). 후보:
   - DuckDB 가 `node` column 을 NULL 로 노출 → caller 측 `WHERE node='NODE_A' OR node IS NULL` 로 explicit filter
   - DuckDB 가 missing key 를 string `''` 또는 sentinel 로 노출

9. **NODE_A / NODE_B / NODE_DEFAULT 의 alphabetical 순서 의도성 검증**: ASCII order = `A < B < DEFAULT` (uppercase ASCII 가 다음 letter 보다 앞, 하지만 D 는 A/B 다음). **결과**: legacy DEFAULT 가 alphabetical 로 NODE_A 보다 *뒤* → NODE_A win (post-HA 가 우선). 이는 §D2.1 의 의도 (post-HA partition 우선)와 정합. 단 `NODE_DEFAULT` 가 아니라 그냥 `DEFAULT` 라면 ASCII order 에서 D 는 N 보다 앞 → DEFAULT win — **bug risk**. **mitigation**: legacy partition 의 mapping 을 `DEFAULT` 가 아니라 `~DEFAULT` 또는 `zzz_DEFAULT` 등 ASCII order 에서 뒤로 가도록 prefix 결정 (Architect 확정).

10. **dedup 결과의 streaming vs materialization** (메모리/latency 결정): T1 candle scan 은 DuckDB 에서 한 번에 SQL 실행 (storage.py line ~226 fetchall) — 전체 결과 (메모리 high, latency 단일 query). T2/T3 는 pyarrow 기반 + sort 후 yield (orderbook_replay.py line 170-182) — 전체 row materialize 후 sort. dedup 도입 시 메모리 추가 부담 (양 node 의 동일 logical key row 를 buffer 에 모아 비교) — **streaming dedup**: ts_utc ASC sort 후 동일 ts_utc group 내에서 logical key 비교 (sliding window). 이 alg 가 자연 streaming 이지만 received_at fallback 의 ms-tolerance ±100ms 가 ts_utc 차이를 만들 수 있어 group 경계가 흐려짐 → window-based dedup, window size = ms-tolerance ×2 = 200ms safety margin (Architect 결정).

11. **Quarantine 폭주 시 backpressure / IO 보호** (Codex F-2 escalation, Architect 결정): content mismatch 발생률이 abnormal spike 시 quarantine artifact 무한 write → disk 폭주 / scan latency degrade 가능. 후보 정책:
    - (a) drop 금지 (모든 mismatch 기록, IO 폭주 risk 감수)
    - (b) rate-limit (per-second cap, 초과분 dup_skip_count metric 만 증가)
    - (c) batching (mismatch 가 N 개 모이면 single artifact 에 묶어 write)
    - (d) cap (per-day artifact 갯수 cap, 초과 시 fail-closed scan halt)
    Architect 결정 필요 (§5.4).

12. **T2 → T1 candle aggregation ordering** (Codex F-3 escalation, X3 scope 외 명시): backtest engine 또는 collector 측 candle close 가 T2 tick 을 aggregate 해 T1 candle 을 구성하는 path — 본 X3 의 scope 외. X3 는 *각 tier 의 read-side dedup* 만, cross-tier aggregation 은 별도 lane (mctrader-engine candle aggregation 또는 backtest engine 의 candle close 로직). **명시적 out-of-scope** + §"향후 amendment" 에 추가.

### 5.4 사용자 확인 필요 (blocking — Architect 진입 전)

**없음** — 모든 X3 scope 결정은 부모 Epic Phase 1 의 16-row decision stack + ADR-009 §D2.1 / §D10.7 / §D11.8 amendment + sister X2 freeze 에서 사전 승인 완료. X3 는 그 contract 의 read-side enforcement 만.

단 **Architect 결정 필요 항목** (Story §7 설계 서사 의 input — blocking 아니라 design lane scope):

1. T1 multi-node late correction conflict resolution: §3.1 후보 (i) received_at MAX / (ii) node priority alphabetical / (iii) hybrid (received_at MAX + tie-break node priority) — 셋 중 하나 freeze
2. legacy `DEFAULT` mapping sentinel 명칭 (ASCII alphabetical priority 의도 정합) — 후보 `DEFAULT` (current ADR-009 §D2.1) / `NODE_DEFAULT` / `zzz_DEFAULT` (Codex F-5 escalation 5)
3. quarantine artifact 위치 (sidecar vs root manifest `<root>/market/manifest/quarantine/active-active-mismatch/...`) — §5.3 edge 7
4. multi-node mode activation criterion (distinct `node=` 값 개수 ≥ 2 자동 감지 vs caller hint `scan_*(active_active=True)` parameter) — §5.3 edge 4
5. streaming vs materialization dedup alg (window size + ms-tolerance ±100ms 처리) — §5.3 edge 10
6. DuckDB hive_partitioning missing-key behavior 검증 결과 따른 caller-side filter spec — §5.3 edge 8
7. **`dedup.py` 신규 module 위치** (Codex F-6 escalation 4): flat `src/mctrader_data/dedup.py` (단일 책임 + test isolation) vs `storage.py` 안 helper function — Architect freeze 의무.
8. **Quarantine 폭주 시 backpressure / IO 보호 정책** (Codex F-2 escalation 2): drop 금지 / rate-limit / batching / cap / fail-open vs fail-closed 중 결정. 본 §3.1 의 "B7 quarantine reason 신규" 의 운영 안정성 enforce.

### 5.5 사용자 정보 제공 (non-blocking — design lane 진입 가능)

- **X2-X3 window 의 종료 시점**: X3 main merge 가 곧 X2 §8.4 운영 caveat 의 (a) `X3 도착 대기` 옵션 자연 해소. X3 main merge 후 사용자는 양 node 동시 가동 + read 측 transparent dedup 를 동시에 누릴 수 있음. (b) `collector daemon 비활성화 + backfill 만` / (c) `--node-id=DEFAULT` 단일 node 옵션은 X3 후 *불필요* (단 backward compat 으로 영구 지원 — legacy partition 호환 의무).

- **X4 status CLI 도착 전까지 quarantine 시각화 부재**: X3 가 quarantine artifact 생성 + counter 증가는 enforce 하지만, *사용자가 quarantine 발생을 인지하는 채널* 은 X4 (CLI status) + X6 (web panel) 의 의무 — X3 단독 main merge 시점에는 사용자가 artifact 를 직접 grep 해야 발견 가능. 이는 의도된 phase boundary.

- **C2 Calibration target 의 측정은 X7**: T2 > 99% / T3 > 95% dedup 정확도 target 의 *실데이터 검증*은 X7 의 30분 E2E demo + Calibration AC. X3 는 *measurable hooks* (dup_skip_count / quarantine_count counter API) 까지.

## 6. 외부 지식 배경

본 절은 X3 implementation 의 외부 기술 / 표준 / library-level 보장 의 배경. 부모 Epic §6 + sister X2 §6 의 외부 지식 (Bithumb WS schema 검증 / NFS atomic / systemd / DuckDB Hive base) 와 중복되는 항목은 **부모 또는 X2 로 위임** 하고 X3 child specific 항목만 본 §6 에서 다룸.

### 6.1 DuckDB Hive partition pruning + UNION ALL BY NAME (X3 의 T1 reader 핵심)

X3 의 T1 reader (storage.py `scan_candles`) 는 DuckDB 의 `read_parquet(..., hive_partitioning=true)` + `UNION ALL BY NAME` (line 207-209) 패턴 활용:

- **Hive partition pruning**: DuckDB 0.9+ 가 path 의 `key=value` directory 자동 인식 → `WHERE node='NODE_A'` predicate push-down → `node=NODE_B` partition 의 file 을 scan 자체에서 skip. 본 X3 의 dedup 알고리즘은 양 node 모두 read 가 input 이므로 pruning 없이 union 이지만, debugging / lineage 용 single-node scan 시 효율 제공.
- **UNION ALL BY NAME**: column 순서 다른 schema 도 column name 기준 union — 양 node 의 parquet schema 가 metadata `node_id` field 차이 외 row column 동일 (X2 §6.6 byte-identical 기대) → UNION ALL BY NAME 가 자연 처리. legacy partition 의 schema 는 `node` column 이 hive 차원 부재 → BY NAME 적용 시 NULL 로 채워짐 (검증 필요).
- **missing key handling** (§5.3 edge 8): DuckDB 의 `hive_partitioning=true` 가 partition tree 에서 어떤 leaf 는 `node=` 가 있고 어떤 leaf 는 없는 mixed 상태에서 column 을 NULL 로 노출하는지 / 별도 sentinel 로 노출하는지 = X3 implementation 진입 시 검증 의무. DuckDB doc: hive partitioning 자동 인식이 partition column 을 missing 인 file 에서 NULL 로 처리하는 것이 default (multiple partition tree depth mixed scan 시).

### 6.2 pyarrow row equality + Decimal128 비교 (X3 의 T2/T3 dedup 핵심)

X3 의 T2/T3 reader (orderbook_replay.py) 는 pyarrow 기반 (DuckDB 미사용) — `_read_parquet_rows()` 가 `table.to_pylist()` (line 149) 로 dict 화 후 row 단위 비교:

- **Decimal(38,18) row equality**: ADR-009 §D1 의 Decimal native type. Python `Decimal` 객체는 `==` 가 numeric equality (string 표현 차이는 normalize). 양 node 의 byte-identical 기대 (X2 §6.6) 가 만족하면 dict comparison 자연 동작. **단 Decimal scale 차이** (e.g., `Decimal('1.00')` vs `Decimal('1')`) → numeric equal 이지만 hash 또는 string 표현 다름 — dedup 의 logical key tuple 비교에서 Decimal numeric equality 보장 필요.
- **timestamp[ns, UTC] equality**: pyarrow timestamp ns precision. 양 node received_at 은 ns 차이 가능 (clock drift) — logical key 의 ts_utc 는 server-side `contDtm` 또는 `received_at` fallback. fallback row 의 ms-tolerance ±100ms (§D10.7) 처리 시 **timestamp diff < 100ms 면 dedup 후보**, 아니면 별도 row.
- **string equality for raw_json**: §D10.1 / §D11.1 nullable. dedup 의 비교 제외 column (§D10.7 / §D11.8 본문 명시). row equality 비교 시 raw_json 명시 제외 의무.

### 6.3 quarantine artifact 의 audit trail 패턴 (X3 의 신규 reason `active-active mismatch`)

quarantine artifact 의 신규 reason 도입 시 audit trail 보존 표준:

- **artifact 가 보존해야 할 audit field** (root cause analysis input):
  - `tier` (tick / orderbook)
  - `logical_key` (직렬화 — tuple stringify)
  - `node_a_value` / `node_b_value` (mismatch 발생한 row 의 실제 값 — JSON dict)
  - `node_a_id` / `node_b_id` (alphabetical 순)
  - `diff_summary` (어느 column 다른지 — column name list)
  - `received_at_a` / `received_at_b` (clock drift 분석용)
  - `partition_path_a` / `partition_path_b` (file 위치 — file_offset 까지 가능하면)
  - `detected_at_utc` (quarantine emit 시각)
- **artifact format**: JSON sidecar (heartbeat-schema.v1 와 동형 — atomic write/fsync/rename 권장). per-incident file = `<root>/market/manifest/quarantine/active-active-mismatch/<YYYY-MM-DD>/<symbol>-<incident-id>.json`. incident-id 는 `<run_id>-<seq>` format.
- **retention**: Calibration C2 의 root cause analysis 에 참조되므로 30일 default retention 권장 (Architect 결정). audit trail 자체는 인접 row 의 raw_json 보존 (debug 가능)
- **참조 패턴**: ADR-009 §D5 quarantine ("일부 row 실패 + payload 보존") + §D11.6 fail-closed reconstruction error mode 와 동형 — quarantine 은 silent skip 거부 의 결과물.

### 6.4 late correction semantics (T1 candle 의 §D5 multi-node 적용 근거)

ADR-009 §D5 의 late correction 정책:

> "Duplicate (`exchange, symbol, timeframe, ts_utc`): 동일 hash = idempotent / 다른 값 = late correction (append-only + serving view)"

이 정책의 도메인 의도 (single-node 시점):

- **append-only**: file system 에 row 가 누적되어 무엇도 erase 되지 않음 (audit trail 보존)
- **serving view**: scan API 가 caller 에게 노출하는 stream 은 "최신 값" 이지만, 어떤 row 가 *최신* 인지의 정의는 single-node 시점에는 단순 — *나중에 도착한 row* (received_at 또는 file_offset 기준 last-write-wins).

**multi-node 적용** (X3 의 도전):

- 양 node 가 같은 candle 을 같은 ts_utc 에 close 하면 양 node 가 동시 write — `received_at` 은 양 node 마다 별개 시각.
- "최신 값" 의 multi-node 정의:
  - 후보 (i) `received_at` MAX (양 node 의 row 중 더 늦게 도착한 쪽이 win) — late correction 의도와 가장 정합. *시간 축* 으로 "최신" 직관 유지. 단 양 node clock drift 가 received_at MAX 의 결정성을 흔들 가능 (NTP chrony 권장 host prereq).
  - 후보 (ii) **node priority alphabetical** — §D2.1 의 T2/T3 정책과 동형. clock drift 영향 0 (deterministic). 단 의도가 *시간 축 최신* 보다 *node 순서* 인 점에서 §D5 의 "late correction" 어휘와 약간 mismatch.
  - 후보 (iii) ASCII order based first node win = (ii) 와 동일.

**Architect 결정 권장 (i)** — late correction 의도 정합. 단 clock drift 의 결정성 위협 mitigation 으로 received_at tie-break 시 node priority alphabetical (e.g., 둘이 ms 단위에서 같으면 NODE_A win). 또는 권장 (ii) — clock drift 영향 0 + 단순 + T2/T3 정책 동형 (도메인 일관성). 본 PL 합성 시점 결론 = §3.1 / §5.4 에서 Architect 에 위임.

### 6.5 dedup ratio measurement methodology (X7 Calibration C2 의 준비)

X3 자체는 metric counter 노출만, X7 Calibration C2 가 실측 — X3 단계에서 measurable hook 의 spec:

- **dup_skip_count cumulative counter**: heartbeat-schema.v1 `metrics.dup_skip_count` (이미 freeze). X3 의 `dedup.py` 가 logical key match → idempotent skip 시 increment. 본 run 시작 이래 누적. heartbeat 5s loop 가 read.
- **quarantine_count cumulative counter**: heartbeat-schema.v1 `metrics.quarantine_count` (이미 freeze). X3 의 `dedup.py` 가 content mismatch → quarantine emit 시 increment. **active-active mismatch 외 다른 quarantine reason 도 같은 counter 사용** (§D5 / §D11.6 의 기존 quarantine 도 합산) — X4 status CLI 가 reason 차원 별도 노출 의무.
- **dedup ratio 계산식**: `dup_skip_count / (dup_skip_count + emit_count)` per tier. 양 node 가 같은 stream 받으면 emit ≈ skip → ratio ≈ 50%. T2 byte-identical 기대 시 raw event 의 양 node 합 = 2x → emit + skip = 1x raw → ratio = 50% 자연. **C2 의 측정 의도**: ratio 가 50% 에서 멀어지면 (dedup 누락) 또는 quarantine 비율이 high 면 root cause analysis. T2 > 99% target = "양 node 의 같은 logical key row 중 99% 가 dedup 으로 idempotent 처리됨".

### 6.6 X2-X3 window 운영 caveat 의 X3 측 termination semantics

X2 §8.4 (Codex F-7 PUSH-BACK) 의 X3 prerequisite checklist 가 X3 main merge 시점에 자연 해소되는 메커니즘:

- **recursive partition glob** (`**/node=*/**/*.parquet`): pyarrow `Path.glob` 또는 DuckDB hive_partitioning recursive 로 enforce. 기존 storage.py `_resolve_scan_paths` 의 `**/*.parquet` (line 154) 이 이미 recursive — DuckDB hive_partitioning 자동 인식이 `node=` level 도 자연 노출. orderbook_replay.py 의 `_read_parquet_rows` (line 145) 의 `part_dir.glob("*.parquet")` 가 single-level — **변경 의무** (X3 §4 에서 명시).
- **legacy partition `node=DEFAULT` mapping**: §3.1 `DEFAULT` ASCII prefix 결정 후 read 단계에서 hive `node` column NULL → `DEFAULT` 변환.
- **legacy file naming + 신규 file naming 양쪽 read**: orderbook_replay.py `tier_coverage` 의 `part-*.parquet` glob (line 394) → `part-*.parquet` + `*-*.parquet` (HA file naming 의 `{collector_run_id}-{batch_seq}.parquet` 매칭) 양쪽 union. parquet read 자체는 file naming 무관 — `tier_coverage` 의 collector_run_id harvest 단계만 영향.

X3 main merge 가 위 3 prerequisite 모두 enforce → X2-X3 window caveat 의 운영 옵션 (a) `X3 도착 대기` 자동 해소 → 사용자가 양 node 동시 가동 + read 측 transparent dedup 동시 활성화.

### 6.7 Out-of-scope 외부 지식 (부모 Epic 또는 후속 Story 위임)

- **NFS / SMB / Ceph 의 atomic rename 자세한 비교** → 부모 Epic §6 + X2 §6.1
- **POSIX `rename(2)` semantics + `os.replace` cross-platform** → X2 §6.1 / §6.2
- **fsync cost vs durability tradeoff** → X2 §6.3
- **systemd `Restart=always` semantics** → X2 §6.4 + X5 README
- **pyarrow Decimal128 + Parquet write performance** → X2 §6.6 (writer 측)
- **Bithumb WS schema 검증 (cont_no / sequence_id 부재)** → 부모 Epic §6 + ADR-009 §D2.1 amendment 본문
- **Streamlit `00_status` page rendering** → X6 Story
- **CLI status subcommand exit code semantics** → X4 Story
- **Multi-network HA / cloud + homelab mix** → 후속 Epic candidate
- **30분 양 node E2E demo + Calibration C1/C2 측정** → X7 Story

## 7. 설계 서사

*(Architect 작성 예정 — placeholder)*

## 8. 개발 서사

Phase 3 implementation = `mclayer/mctrader-data` PR #9 (main merged, branch squash-deleted). mctrader-data 0.6.0 → 0.7.0.

### 8.1 Implementation summary

7 Task (Task 0 Preflight + Task 1-5 TDD + Task 6 Release):

| Task | 산출물 | 핵심 |
|---|---|---|
| 0 | pyproject 0.6.0→0.7.0 | chore commit |
| 1 | `dedup.py` (NEW, 410 LOC) + `test_dedup.py` (22 test) | tier 별 logical key extractor (T1 4-key / T2 6-tuple / T3 8-tuple) + node priority alphabetical (NODE_A < NODE_B < zzz_DEFAULT) + T1 hybrid late correction (received_at MAX + tie-break) + T2/T3 mismatch quarantine + DedupCounterSink protocol + _BackpressureLimiter (100/sec rate-limit + batching + monotonic clock) |
| 2 | `policy.py` `QuarantineReason.ACTIVE_ACTIVE_MISMATCH` + 3 test | ADR-009 §D2.1 dedup contract + default decision = QUARANTINE |
| 3 | `storage.py` `scan_candles()` multi-node 자동 감지 + 5 test | DuckDB hive_partitioning + caller-side regex (`r"[/\\]node=([^/\\]+)[/\\]"`) + zzz_DEFAULT mapping + `union_by_name=true` mixed legacy 호환 |
| 4 | `orderbook_replay.py` `scan_ticks` / `scan_orderbook_events` / `tier_coverage` + 3 test | recursive `rglob("*.parquet")` + multi-node dedup + 신규 `{run_id}-{seq}.parquet` collector_run_id harvest |
| 5 | (Task 5 skip — dedup sink wiring 는 test_dedup, scan API multi-node 는 test_storage + test_orderbook_replay 가 cover) | — |
| 6 | PR #9 + Codex 7-area review + admin merge | 148 pytest PASS / 0 regression / 0 ruff lint warning |

### 8.2 Architect 결정 8항 freeze (Sonnet decider, plan §"Architect 결정")

1. **T1 hybrid late correction**: `received_at` MAX + tie-break node priority alphabetical. **scan path limitation** (Codex F-4 acknowledged): candle parquet schema 에 `received_at` column 부재 → 사실상 tie-break (node priority alphabetical) 만 작동. dedup module 자체는 hybrid 지원 (test_dedup 검증) — 향후 candle schema 확장 시 자동 적용.
2. **DEFAULT sentinel**: `zzz_DEFAULT` (ASCII order 끝, post-HA partition 우선)
3. **Quarantine artifact 위치**: root manifest `<root>/market/manifest/quarantine/active-active-mismatch/...` (caller 책임 위임 — X4 가 write)
4. **Multi-node mode 자동 감지**: distinct `node=` ≥ 2 (caller transparent)
5. **Streaming dedup window**: 200ms safety margin
6. **DuckDB hive_partitioning**: caller-side regex extraction (DuckDB version 의존 0)
7. **dedup.py flat module 위치**: 단일 책임 + test isolation
8. **Quarantine backpressure**: 100/sec rate-limit + batching + 모든 mismatch counter 증가

### 8.3 Codex review escalation 모두 ADOPT

본 PR review (codex:rescue/gpt-5.4): needs-fix → 4/4 ADOPT 후 pass.

- F-1+F-4 (PUSH-BACK, root cause 동일): scan_candles T1 hybrid 한계 명시 + node priority test 추가 (storage.py inline comment + `test_scan_candles_multi_node_mismatch_node_priority_wins`)
- F-6 (NIT): `_BackpressureLimiter` unit test 추가 (monotonic mock + window rollover + final flush)
- F-3 minor (NIT): test_dedup pytest import 추가
- 기타 (Area 2/3/5/7): ADOPT-AS-IS

### 8.4 Caller transparency 검증

`scan_candles` / `scan_ticks` / `scan_orderbook_events` 모두 signature 변경 0. dedup import 는 함수 내부 — module-level import path 변경 0. engine / web / WFO 사용처 정적 grep 결과 — 변경 의무 0 (별도 검증 시 조치).

### 8.5 X2-X3 window caveat — RESOLVED

X2 의 MCT-91 §8.4 운영 caveat (a)~(c) 모두 본 PR merge 후 transparent dedup 으로 자연 해소:
- 사용자 옵션 (a) `X3 도착 대기` → X3 main merged ⇒ 양 node 동시 가동 + read 측 transparent dedup 동시 가용
- 옵션 (b) `collector daemon 비활성화 + backfill` / 옵션 (c) `--node-id=DEFAULT` 단일 node → 더 이상 필요 X (단 backward compat 영구 유지)

**남은 phase boundary**:
- X4 (mctrader-data status CLI) 도착 전까지 quarantine artifact 는 dedup module 의 `quarantine_records` list 만 — root manifest write 는 X4 책임
- X4 status CLI + heartbeat metric wiring (`HeartbeatWriter` 가 `DedupCounterSink` adapter 추가) → Phase 4 Story
- X5 ops scripts (systemd + Ansible rolling deploy) → Phase 5 / X6 Streamlit panel → Phase 6 / X7 Calibration → Phase 7

## 9. 품질 게이트 이력

### 9.1 Test results (mctrader-data PR #9)

- **148 pytest PASS** (33 신규 X3 + 115 기존 X2 regression 0):
  - dedup.py 전용: 22 test (logical key 3 + node priority 3 + T1 hybrid 4 + T2/T3 mismatch 3 + counter sink 2 + backpressure 2 + window 1 + limiter unit 4)
  - storage.py 확장: 5 신규 (multi-node auto / legacy only / legacy + node mixed / signature unchanged / mismatch node priority win)
  - orderbook_replay.py 확장: 3 신규 (multi-node ticks / 신규 file naming harvest / legacy part- harvest)
  - policy.py 확장: 3 신규 (ACTIVE_ACTIVE_MISMATCH reason / default decision / halt policy)
  - 기존 test 0 regression

- **CI**:
  - Windows: pass (44s)
  - Ubuntu: pass (17s, ruff 0 warning)
  - check-gate: pass
  - phase-gate-mergeable: ACTION_REQUIRED (codeforge phase label sequencing — admin merge autonomy 적용)

### 9.2 Codex review 결과

- Phase 1 PR #98 review (Story §2-§6): 5/5 ADOPT
- Phase 3 plan PR #99 review: 6/6 ADOPT (1 PUSH-BACK + 5 NIT)
- Phase 3 PR #9 review: 4/4 ADOPT (2 PUSH-BACK + 3 NIT, scan T1 hybrid limitation 명시)

### 9.3 ADR-009 enforcement 검증

- §D2.1 mixed legacy 영구 지원: `test_scan_candles_legacy_partition_only_no_dedup` + `test_scan_candles_legacy_plus_node_a_dedup`
- §D5 T1 late correction (no quarantine): `TestT1HybridLateCorrection.test_t1_no_quarantine_on_value_mismatch`
- §D10.7 T2 6-tuple: `TestLogicalKey.test_t2_tick_6_tuple` + `TestT2T3ContentMismatch.test_t2_logical_key_match_value_mismatch_quarantines`
- §D11.8 T3 8-tuple: `TestLogicalKey.test_t3_orderbook_8_tuple` + `test_t3_logical_key_match_value_mismatch_quarantines`

### 9.4 Phase 3 close marker

- mctrader-data 0.7.0 main merged (commit 0d263a7)
- mctrader-hub Phase 1 PR #98 + Phase 3 plan PR #99 main merged
- 다음 child Story 후보: MCT-X4 (status CLI + heartbeat metric wiring) / MCT-X5 (ops scripts) / MCT-X6 (web panel) / MCT-X7 (Calibration)

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

*(FIX 발생 시 append)*

## 11. 회고

*(PMOAgent 작성 예정 — Story 완료 시)*
