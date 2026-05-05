---
story_key: MCT-89
status: phase:완료
component: epic
type: epic
parent_epic: null
related_adrs: ADR-009
---

# MCT-89 (Epic): Collector HA — Active-Active Multi-Node + Shared Storage

## 1. 사용자 요구사항 (verbatim, 2026-05-05)

> mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.

## 2. 도메인 해석

mctrader 10번째 implementation Epic (MCT-12 ~ MCT-87 의 후속). 직전 Epic MCT-70 (T2/T3 Backtest Lifecycle Integration) 종료 + cfp-108 phase-6a debut adoption main merge (`d0bedce`) 직후 시점. backtest data 수집의 reliability foundation.

핵심 framing (Sonnet decider brainstorm + 사용자 답변 stack 16 결정):

- **Bithumb single-source HA**: 양 node 가 같은 Bithumb endpoint 구독. Bithumb 측 outage 는 양 node 동시 영향 (본 Epic out-of-scope, 후속 Multi-network HA Epic).
- **Same-LAN 2-node active-active**: host failure / code deploy / process crash cover. Multi-network / different ISP 는 후속.
- **Per-node `node=` partition split**: write contention 0. read-side `scan_*` API 가 multi-node union + tier 별 logical key dedup (transparent — engine/web 변경 0).
- **공유 storage (NFS / SMB / Ceph)**: 단일 MCTRADER_DATA_ROOT mount.
- **systemd + simple Ansible**: rolling deploy `serial: 1` + heartbeat health gate. k8s / Nomad 거부 (over-engineering).
- **Storage-side heartbeat JSON**: HTTP /healthz endpoint 거부 (코드 침습 최소).
- **DuckDB single-writer invariant 유지**: collector storage = Parquet append-only / DuckDB read-only.
- **Backfill 변경 없음**: DataEngineerAgent 기존 의무 (Tick / Orderbook lossless) 유지.

본 Epic 은 MCT-41 (Live Mode) / MCT-55 (WFO closed) / MCT-70 (T2/T3 Backtest closed) 와 별도 lane. live mode prerequisite 는 아니지만 backtest data reliability 측면에서 도움.

## 3. Audit + Decider 결과 (Phase 1 prerequisite)

### Sonnet decider Phase 1 brainstorm (16 결정 stack, 2026-05-05)

| # | 결정 | 채택 |
|---|---|---|
| 1 | 배포 환경 / HA scope | Multi-host, same network (2+ Linux node) |
| 2 | 두 node 동작 모델 | Active-Active + dedup |
| 3 | Orchestration | systemd unit + Ansible/script rolling |
| 4 | Write 충돌 처리 | Per-node `node=` partition split + read-side merge |
| 5 | Storage 위치 | 공유 storage (NFS / SMB / Ceph) + 단일 MCTRADER_DATA_ROOT |
| 6 | Heartbeat 메커니즘 | storage-side atomic JSON writer (5s) |
| 7 | Read-side merge 위치 | scan_* API 내장 (transparent) |
| 8 | T1 candle dedup | logical key `(exchange, symbol, timeframe, ts_utc)` + §D5 late correction align |
| 9 | T2 tick dedup key | fallback tuple `(exchange, symbol, ts_utc, price, qty, side)` (Bithumb tx_id 부재 검증) |
| 10 | T3 orderbook dedup key | fallback tuple `(exchange, symbol, ts_utc, event_type, side, level, price, quantity)` (Bithumb sequence_id 부재 검증) — best-effort |
| 11 | Conflict resolution | T1 = late correction / T2/T3 = node priority (alphabetical) + `active-active mismatch` quarantine |
| 12 | DuckDB write path | 변경 없음 (Parquet append-only / DuckDB read-only invariant 유지) |
| 13 | Backfill 메커니즘 | 변경 없음 (DataEngineerAgent 기존 의무 유지) |
| 14 | Alert routing v1 | Streamlit `00_status` page + CLI `mctrader-data status` (passive observation) |
| 15 | Code deploy rollback | manual `git revert` + 재배포 |
| 16 | ops/scripts 위치 | mctrader-hub `scripts/ha/` (cross-repo orchestration) + collector heartbeat = mctrader-data 코드 |

16/16 escalation 0건. 사용자 사전 승인 4회 ("ok" trigger).

### Codex 7-area review

(Task 5 완료 후 본 절 채움 — Phase 1 PR 머지 직전 codex:rescue dispatch)

## 4. Child Story decomposition

| Story | Owner repo | Scope | Dependency |
|---|---|---|---|
| MCT-X2 | mctrader-data | `--node-id` CLI flag + partition writer `node=` 적용 + heartbeat writer (atomic + 5s loop) + lineage `node_id` | X1 (this) |
| MCT-X3 | mctrader-data | `scan_*` multi-node union + tier 별 logical key dedup + `dedup.py` 신규 module + quarantine `active-active mismatch` reason | X2 |
| MCT-X4 | mctrader-data | `tier_coverage` node 차원 + heartbeat-aware gap detection + CLI `mctrader-data status` | X2 |
| MCT-X5 | mctrader-hub `scripts/ha/` | systemd unit template + Ansible playbook (`serial: 1` rolling) + `heartbeat_health_check.sh` + README (host prereq) | X2 |
| MCT-X6 | mctrader-web | `pages/00_status.py` Streamlit page (heartbeat freshness / lag / quarantine + 임계 banner) | X2 (heartbeat schema freeze) |
| MCT-X7 | mctrader-hub | Epic close + Calibration (throughput / scan latency overhead) + 양 node 30분 E2E demo | X3 + X4 + X5 + X6 |

`X` = Phase 2~6 진입 시 각 child issue 번호 부여 (본 Epic close 전에는 placeholder).

## 5. 요구사항 확장 해석

본 Epic = backtest data reliability foundation. paper / live mode 는 별도 prereq.

확장 해석 — Sonnet decider 도출:

- "데이터 순단을 줄이고자" = active-active 의 자동 cover (single-host failure) + heartbeat 기반 잔여 failure 의 fallback observation.
- "코드 수정사항 배포" = rolling restart `serial: 1` + heartbeat health gate. zero-downtime 까지는 보장 안하지만 read-side gap 0 (T1 closed candle 기준).
- "2개 이상의 Active Node 관리" = active-active (active-passive 거부). dedup 의 부담은 read-side 가 짊어짐 (write contention 0 보장).

## 6. 외부 지식 배경

### Bithumb public WebSocket schema 검증 결과 (Case C)

`mctrader-market-bithumb` `ws_mapping.py` (current main, MCT-19 PR #20 merged) 검증:

- **Subscription channels**: `ticker` / `transaction` / `orderbookdepth` (+ `orderbook_snapshot` deprecated path)
- **Transaction message fields**: `symbol / contPrice / contQty / contDtm / buySellGb` — **unique transaction id (cont_no / tx_id / seq) 부재**
- **Orderbook message fields**: `symbol / orderType / price / quantity` (delta) + `bids[] / asks[]` (snapshot) — **sequence_id / version 부재**
- **Timestamp fallback**: message 에 ts 부재 시 node-local `received_at` 사용 (ws_mapping.py:24-33) → 양 node divergence 가능

→ **Case C 적용**: ADR-009 §D10.7 / §D11.8 의 logical key 는 **fallback tuple only** + best-effort dedup (T2 > 99% target / T3 > 95% target). Bithumb API 가 향후 unique id 제공 시 minor amendment 로 primary key 채택 가능 (backward compat).

### NFS / SMB / Ceph 의 atomic rename 보장

- POSIX `rename(2)` 는 same-directory 내 atomic. NFS server 측 atomic rename 지원 가정 (대부분 서버 OK, NFSv3 with close-to-open 또는 NFSv4 권장).
- heartbeat write 패턴 (write-temp + fsync + rename) 이 NFS 환경에서 안전.
- Ceph 의 경우 same-pool 내 rename atomic.

### systemd `Restart=always` semantics

- process exit (정상 / 비정상 무관) 시 RestartSec 후 재시작.
- `StartLimitBurst` / `StartLimitIntervalSec` default 적용 (5 회 / 10 초 — 폭주 방지). 본 collector 의 경우 제한 환경 변수 `StartLimitBurst=20` 등 host prerequisite README 에서 권장.

### DuckDB Hive partition pruning

- `node={value}` partition column 으로 read-side scan 시 특정 node partition 만 scan 가능 (`WHERE node='NODE_A'`).
- DuckDB 0.9+ Hive partitioning 자동 인식.

## 7. 설계 서사

(Spec doc 의 §2 Architecture overview 참조)

핵심 invariant:

- 양 node 가 같은 source 구독 → Bithumb outage 는 양 node 동시 영향 (out-of-scope)
- 양 node 가 다른 collector_run_id partition 에 write → write contention 0
- 모든 reader 가 단일 MCTRADER_DATA_ROOT mount 에서 read

failure category × cover-by-HA: spec §2.2 참조.

Architecture diagram + partition/dedup contract + rolling deploy + monitoring + mctrader-data implementation surface 모두 spec doc:

- [`docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md`](../superpowers/specs/2026-05-05-collector-ha-active-active-design.md)

본 Phase 1 의 ADR-009 amendment 3 절 (§D2.1 / §D10.7 / §D11.8) 이 design 의 contract enforcement 위치:

- [`docs/adr/ADR-009-ohlcv-schema.md`](../adr/ADR-009-ohlcv-schema.md)

Heartbeat JSON schema:

- [`docs/domain-knowledge/contracts/heartbeat-schema.v1.md`](../domain-knowledge/contracts/heartbeat-schema.v1.md)

## 8. 개발 서사

*(DeveloperPL 작성 예정 — Phase 2 PR 에서)*

## 9. 품질 게이트 이력

*(Review/Test PL 작성 예정 — Phase 2 PR 에서)*

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

*(FIX 발생 시 append)*

## 11. 회고

*(PMOAgent 작성 예정 — Story 완료 시)*
