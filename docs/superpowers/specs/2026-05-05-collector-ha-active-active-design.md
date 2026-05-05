---
title: Collector HA — Active-Active Multi-Node + Shared Storage
date: 2026-05-05
status: brainstormed (pre-Phase-1)
author: Sonnet decider (mccho8865)
mctrader_epic_key: TBD (Phase 1 진입 직전 mctrader-hub 신규 issue 번호 부여)
upstream_dependency: cfp-108 phase-6a debut adoption (main merged d0bedce)
related_adr:
  - ADR-009 (OHLCV / tick / orderbook schema — §D2 / §D10 / §D11 amendment 대상)
  - ADR-002 (TradeExecutor 3 mode — 본 design 은 backtest data 측, executor 측 변경 0)
out_of_scope_epic_candidate:
  - Multi-network HA (different ISP, cloud + homelab mix)
  - Alert routing v2 (Slack / email webhook)
  - Storage tier separation (hot SSD + cold object store)
  - Live mode HA (별도 Epic, secret + kill switch coordination)
  - Backfill auto-trigger (heartbeat lag 감지 → REST history fetch 자동화)
---

# Collector HA — Active-Active Multi-Node + Shared Storage

## 0. 개요 (Why)

mctrader-data 의 collector daemon (Bithumb public WebSocket → Parquet append + DuckDB read) 을 backtest / WFO / Streamlit 의 **데이터 source-of-truth** 로 본격 가동하기 직전 시점이다. 단일 Linux node + 단일 process 로 운영하면 다음 failure 가 곧 데이터 순단 (gap) 이 된다:

- 단일 process crash / OOM
- 단일 host 재시작
- 코드 deploy 시 process restart window
- (cover 외 — 본 Epic 후속) Bithumb 측 outage, 같은 LAN ISP/전원 outage

본 Epic 은 **same-LAN 2+ Linux node active-active + 공유 storage + 1 MCTRADER_DATA_ROOT** 구성으로 위 4 가지 single-host failure 를 cover 한다. Bithumb 측 outage 와 ISP outage 는 본 Epic 의 cover 범위 외 (후속 Multi-network HA Epic 의 scope).

## 1. 결정 stack (Sonnet decider, 사용자 사전 승인)

| # | 결정 | 채택 | 거부 / 후속 |
|---|---|---|---|
| 1 | 배포 환경 / HA scope | **Multi-host, same network (2+ Linux node)** | Single host multi-process / Multi-network / k8s |
| 2 | 두 node 동작 모델 | **Active-Active + dedup** | Active-Passive / Sharded / Hybrid |
| 3 | Orchestration | **systemd unit + Ansible/script rolling** | Docker Compose / Nomad / IaC repo 신설 |
| 4 | Write 충돌 처리 | **Per-node `node=` partition split + read-side merge** | Shared partition byte-hash / Shared partition logical key / Single-writer lock |
| 5 | Storage 위치 | **공유 storage (NFS / SMB / Ceph)** + 단일 MCTRADER_DATA_ROOT | Local SSD cross-host read / Object storage / Primary+replication |
| 6 | Heartbeat 메커니즘 | **storage-side atomic JSON writer (5s)** | HTTP /healthz endpoint / Prometheus exporter |
| 7 | Read-side merge 위치 | **scan_* API 내장 (transparent)** | Background compaction job / 둘 다 |
| 8 | T1 candle dedup key | `(exchange, symbol, timeframe, ts)` | byte-hash only |
| 9 | T2 tick dedup key | `(exchange, symbol, tx_id)` (Bithumb tx_id 우선), fallback `(ts, price, qty, side)` | hash only |
| 10 | T3 orderbook dedup key | `(exchange, symbol, snapshot_ts, sequence_id)` (Bithumb seq 우선), fallback `(snapshot_ts, side, price, qty_delta)` — **best-effort 명시** | strict equality |
| 11 | Conflict resolution | logical key 동일 + content mismatch = **node priority (NODE_A 우선) + quarantine** | first-write-wins / last-write-wins |
| 12 | DuckDB write path | **변경 없음** (Parquet append-only / DuckDB read-only invariant 유지) | DuckDB direct write + multi-writer 락 |
| 13 | Backfill 메커니즘 | **변경 없음** (DataEngineerAgent 기존 의무 유지) | HA 전용 backfill 별도 path |
| 14 | Alert routing v1 | **Streamlit `00_status` page + CLI `mctrader-data status`** | Slack / email (v2 후속) |
| 15 | Code deploy rollback | **manual `git revert` + 재배포** | auto-rollback |
| 16 | ops/scripts 위치 | **mctrader-hub `scripts/ha/`** (cross-repo orchestration) + collector heartbeat writer = mctrader-data 코드 | 신규 mctrader-ops repo / mctrader-data 단독 |

## 2. Architecture overview

```
                          ┌──────────────────────────┐
                          │  Bithumb public WS API   │
                          │     (Korea endpoint)     │
                          └─────────┬────────┬───────┘
                                    │        │
                          identical stream (양 node 동시 구독)
                                    │        │
            ┌───────────────────────┘        └───────────────────────┐
            │                                                        │
   ┌────────▼────────┐                                      ┌────────▼────────┐
   │  Linux node A   │                                      │  Linux node B   │
   │  systemd unit   │                                      │  systemd unit   │
   │  collector      │                                      │  collector      │
   │  collector_run_ │                                      │  collector_run_ │
   │  id = A-{ts}    │                                      │  id = B-{ts}    │
   └────────┬────────┘                                      └────────┬────────┘
            │                                                        │
            │            mount: /mnt/mctrader-data (NFS)             │
            └───────────────────────┬────────────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Shared storage   │   single MCTRADER_DATA_ROOT
                          │  (NFS / SMB /     │   per-node partition split
                          │   Ceph)           │   (write contention 0)
                          └─────────┬─────────┘
                                    │
                                    │  read mount (동일 path)
                                    │
            ┌───────────────────────┼────────────────────────────────┐
            │                       │                                │
   ┌────────▼────────┐    ┌─────────▼────────┐             ┌────────▼────────┐
   │  Backtest CLI   │    │  WFO runner      │             │  Streamlit web  │
   │  (read+merge)   │    │  (read+merge)    │             │  (read+merge)   │
   └─────────────────┘    └──────────────────┘             └─────────────────┘
```

### 2.1 Invariant

- 양 node 가 **같은 source (Bithumb 단일 endpoint)** 를 구독 → Bithumb 측 outage 는 양 node 동시 영향 (본 Epic out-of-scope).
- 양 node 가 **다른 collector_run_id partition** 에 write → write contention 0 / parquet 파일 충돌 0.
- 모든 reader (backtest / WFO / web) 는 단일 `MCTRADER_DATA_ROOT` mount 에서 read, scan API 가 collector_run_id 차원을 자동 merge + dedup.

### 2.2 Failure category × cover-by-HA

| 카테고리 | 감지 신호 | HA cover | 잔여 action |
|---|---|---|---|
| Single process crash / OOM | systemd `Restart=always` (sub-sec) | ✅ 자동 | none |
| Single host down / reboot | `heartbeat-{node}.json` mtime > 30s | ✅ 다른 node 단독 | host 복구 후 backfill |
| WS reconnect (Bithumb 측) | `ws_state` 변동 + `events_per_sec` drop | ❌ 양 node 동시 | DataEngineerAgent reconnect invariant + backfill |
| 양 node packet loss (Bithumb outage) | `last_event_ts_per_tier` lag | ❌ | history REST API backfill (lossless 의무 유지) |
| Dedup mismatch spike | `quarantine_count` derivative | — | spec/clock drift 신호, alert |
| Code deploy 실패 | post-deploy 5min window heartbeat 끊김 | — | rolling 중단 + manual revert |

## 3. Partition layout + dedup contract (ADR-009 amendment 제안)

### 3.1 Partition path

현재 ADR-009 §D2 / §D10 / §D11:
```
market/{tier}/schema_version={tier}.v{N}/exchange=.../symbol=.../
       timeframe=.../year=.../month=.../date=.../*.parquet
```

→ 새 partition level `node=` 추가 (T1 / T2 / T3 모두 동일):
```
market/{tier}/schema_version={tier}.v{N}/exchange=.../symbol=.../
       timeframe=.../year=.../month=.../date=.../node=NODE_A/
       {collector_run_id}-{batch_seq}.parquet
```

- `node` = 호스트 식별자 (low cardinality, e.g., `NODE_A` / `NODE_B`)
- `collector_run_id` = file name 과 file metadata 양쪽 보존 (MCT-65 manifest 와 1:1 유지)
- DuckDB Hive partition pruning 으로 특정 node 의 데이터만 scan 가능 (lineage / debugging)

### 3.2 Dedup 정책 (read-side merge, scan API 내장)

| Tier | Logical dedup key | Conflict resolution |
|---|---|---|
| **T1 candle** | `(exchange, symbol, timeframe, ts)` | OHLCV byte-identical 기대 → mismatch 시 ADR-009 기존 `quarantine` + node priority |
| **T2 tick** | `(exchange, symbol, tx_id)` (Bithumb tx_id 있을 시) <br> fallback: `(ts, price, qty, side)` tuple | 동일 tx_id mismatch = quarantine. tx_id 부재면 fallback tuple 일치만 dedup |
| **T3 orderbook** | `(exchange, symbol, snapshot_ts, sequence_id)` (Bithumb seq 있을 시) <br> fallback: `(snapshot_ts, side, price, qty_delta)` | **best-effort dedup** — node-local reconstruction 차이 인정. 정확 알고리즘은 child Story 의 실데이터 검증 단계에서 freeze |

### 3.3 ADR-009 amendment scope

- **§D2** `partition` 정의에 `node=` level 추가
- **§D10** `tick.v1` schema 에 `tx_id` field 명시
- **§D11** `orderbook.v1` schema 에 `sequence_id` field 명시
- **§D2 / §D10 / §D11** dedup 정책 절 신설: "active-active dedup contract — logical key per tier + node priority (alphabetical / inventory 순) + quarantine on content mismatch"

**Bithumb public WS schema 검증 의무 (Phase 1 / MCT-X1 의 task)**: Bithumb 공식 doc 의 transaction stream 에 tx_id (또는 동급 unique identifier) 가 있는지 / orderbook stream 에 sequence_id 가 있는지를 X1 Story 의 §6 Detail Investigation 에서 확인. 부재 시 fallback tuple 만 사용하고 ADR-009 amendment 에 그 사실 freeze.

**T3 best-effort 정확도 기대치**: node-local reconstruction 의 sequence_id divergence 가능성으로 dedup 정확도 < 100% 가능. 실데이터 기준 dedup ratio 측정 + 허용 범위 (e.g., > 95%) 는 MCT-X3 의 Calibration AC 에서 freeze.

## 4. Code rolling deployment (systemd + simple playbook)

### 4.1 systemd unit (양 host 동일)

```ini
[Unit]
Description=MCTrader collector (Bithumb)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/mctrader
EnvironmentFile=/etc/mctrader/collector.env
ExecStart=/opt/mctrader/.venv/bin/python -m mctrader_data.collector \
          --node-id=%H --root=/mnt/mctrader-data
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- `Restart=always` → single process OOM/exception 자동 cover (sub-second 복구).
- 한 node restart 동안 다른 node 가 단독 수집.

### 4.2 Heartbeat (storage-side atomic JSON writer)

`<root>/market/manifest/heartbeat-{node_id}.json` (5s interval, atomic write-temp → fsync → rename):

```json
{
  "node_id": "NODE_A",
  "collector_run_id": "A-2026-05-05T12:34:56Z",
  "version": "git-sha-...",
  "started_at": "2026-05-05T00:00:00Z",
  "now": "2026-05-05T12:34:56Z",
  "uptime_seconds": 3600,
  "ws_state": "connected",
  "last_event_ts_per_tier": {
    "candle": "2026-05-05T12:34:55Z",
    "tick": "2026-05-05T12:34:56.123Z",
    "orderbook": "2026-05-05T12:34:56.045Z"
  },
  "queue_depth": 0,
  "metrics": {
    "events_per_sec": 42.3,
    "dup_skip_count": 0,
    "quarantine_count": 0,
    "ws_reconnect_count": 0,
    "backfill_pending_seconds": 0
  }
}
```

- shared storage 기반 → cross-host check 자연 (mtime + content)
- 별도 HTTP / Prometheus endpoint 도입 거부 (코드 침습 최소)
- web / CLI 가 직접 read

### 4.3 Rolling deploy sequence (Ansible `serial: 1` 또는 `deploy.sh`)

```
for host in NODE_A NODE_B:
  ssh $host "cd /opt/mctrader && git fetch && git checkout $TAG && uv sync"
  ssh $host "sudo systemctl restart mctrader-collector"
  wait_until heartbeat-$host.json mtime < 30s   # health gate
  abort if 60s timeout                          # alert + halt rolling
```

- 한 번에 한 host (다른 host 는 단독 수집 — short window 동안 active-passive)
- health gate 실패 → rolling 중단 + alert (자동 rollback X — `git revert` 가 더 안전)

### 4.4 Deploy artifact + rollback

- artifact = git commit hash. uv `pyproject.toml` + `uv.lock` 기준 reproducible install.
- PyPI publish 불요 (ADR-010 align).
- rollback contract = manual `git revert` + 동일 playbook 재실행.
- post-deploy 5분 window 안에 heartbeat 끊김 또는 quarantine 비율 spike → alert.

### 4.5 Host prerequisite (X5 Story README 의무)

본 design 은 다음 host-side prerequisite 를 가정 — 실제 설정 절차는 MCT-X5 Story (`scripts/ha/`) 의 README 에서 상세화:

- **OS** Linux (systemd 기반, Ubuntu 22.04+ / Debian 12+ / RHEL 9+ 가정)
- **Python 3.11+** + `uv` 설치
- **NFS / SMB / Ceph client** + `/mnt/mctrader-data` mount (fstab 등록 + auto-mount + 양 host 동일 path / uid/gid)
- **NTP** (chrony 권장) — heartbeat / received_at 비교에 필수, clock drift < 1s
- **SSH key 배포** (deploy host → collector host A/B, key 없는 password 인증 거부)
- **sudoers** — deploy 사용자가 `systemctl restart mctrader-collector` NOPASSWD
- **firewall** — collector host 가 Bithumb WS endpoint outbound 허용, shared storage inbound 허용

## 5. Monitoring + failure detection + mctrader-data implementation surface

### 5.1 Alert routing (v1 minimal — passive observation only)

- **v1 (MVP) = passive observation**: 사용자가 Streamlit `pages/00_status.py` 또는 CLI `mctrader-data status` 를 능동적으로 확인하면 heartbeat freshness / tier 별 lag / quarantine_count 가 보임. 임계 초과 시 Streamlit banner 빨강 + CLI exit code 비-0. **proactive push (사용자 부재 시 자동 알림) 는 v2 후속**.
- **v2 (deferred, 후속 candidate Epic)**: Slack / email / Telegram webhook + threshold rules + 사용자 부재 시 push. 본 Epic out-of-scope.

v1 의 한계: 사용자가 panel 을 안 열면 failure 인지 지연. 이 한계는 v1 = "데이터 순단 자체를 줄이는" 본 Epic 목표 (active-active 가 자동 cover) 와 align — alert 는 active-active 가 못 막는 잔여 failure 의 fallback 신호용.

### 5.2 mctrader-data implementation surface (DataEngineerAgent 책임 범위 내)

내(Sonnet)가 implement 할 때 mctrader-data 에 들어갈 변경 list — codeforge develop phase 의 §8.5 Impl Manifest input:

| Module | 변경 | 비고 |
|---|---|---|
| `mctrader_data/cli.py` (또는 `collector/__main__.py`) | `--node-id`, `--heartbeat-interval`, `--heartbeat-root` 신규 flag | `%H` (hostname) default |
| `mctrader_data/collector/heartbeat.py` (신규) | atomic JSON writer (write-temp → fsync → rename) + 5s loop task | tier 별 last_event_ts 갱신 hook 제공 |
| `mctrader_data/storage/writer.py` | partition path 에 `node={node_id}` 추가, file name = `{collector_run_id}-{batch_seq}.parquet` | ADR-009 §D2 amendment 준수 |
| `mctrader_data/storage/scan.py` | `scan_candles/ticks/orderbook_events` 가 multi-node partition union + logical key dedup + quarantine emit | transparent — engine/web 변경 0 |
| `mctrader_data/storage/dedup.py` (신규) | tier 별 logical key extractor + node priority + mismatch handler | T1/T2/T3 차등 |
| `mctrader_data/storage/quarantine.py` (확장) | `active-active mismatch quarantine` 신규 reason | ADR-009 quarantine 정책 절 amendment |
| `mctrader_data/lineage.py` (확장) | `_lineage.json` + parquet metadata 에 `node_id` 추가 | MCT-65 manifest 와 1:1 align |
| `mctrader_data/coverage.py` | `tier_coverage` 가 node 차원 노출 (debugging) | gap 식별 시 어느 node 관련인지 |
| `mctrader_data/cli.py status` (신규 subcommand) | heartbeat + dedup metric 출력 + exit code | CLI alert 채널 |
| `tests/integration/test_active_active_dedup.py` (신규) | 두 collector instance simulation + dedup 검증 | T1/T2/T3 모두 |
| `tests/integration/test_heartbeat.py` (신규) | atomic write + cross-host read + crash freshness | NFS-emulation tmpdir |
| `tests/integration/test_rolling_deploy.py` (신규) | 한 collector restart 동안 다른 single-node 단독 수집 unbroken | systemd 외부 simulation |

### 5.3 DuckDB single-writer invariant 유지

DataEngineerAgent 핵심 책임: "DuckDB file lock — single-writer + multi-reader". HA active-active = multi-writer 처럼 보이지만, **collector 의 storage path 는 Parquet append-only** (per-node partition split → 두 node 가 같은 파일을 만지지 않음). DuckDB 는 reader (backtest/WFO/web) 만 사용. 본 design 은 이 invariant 를 그대로 유지 (변경 0).

### 5.4 Backfill integration

DataEngineerAgent 기존 의무: "Tick / Orderbook lossless — packet loss 시 backfill 의무". HA 도입 후에도 동일 의무. **양 node 동시 packet loss 는 HA 로 cover 안됨** → backfill 이 last line of defense. heartbeat metric (`last_event_ts_per_tier` lag > N min, threshold tier 별 차등) 이 backfill trigger 로도 사용. backfill 자체 메커니즘 변경 없음 (Bithumb history REST API).

## 6. Story decomposition (codeforge Phase 분해)

### 6.1 Epic / 7-child 구조 (MCT-48 / MCT-55 / MCT-70 패턴 동일)

가칭 **"Collector HA — Active-Active Multi-Node + Shared Storage"** Epic. KEY = Phase 1 진입 직전 mctrader-hub 신규 issue 번호 부여 (이하 X1~X7 placeholder).

| Story | Owner repo | Scope |
|---|---|---|
| **MCT-X1 (Epic + Foundation)** | mctrader-hub | Epic doc + 6 child stub + **ADR-009 amendment** (§D2 `node=` partition / §D10 tick logical key / §D11 orderbook logical key + active-active dedup contract 절) + heartbeat JSON schema freeze |
| **MCT-X2 (Collector writer side)** | mctrader-data | `--node-id` CLI flag + partition writer `node=` 적용 + `collector_run_id-batch_seq.parquet` naming + heartbeat writer (atomic + 5s loop) + lineage `node_id` |
| **MCT-X3 (Scan-side merge + dedup)** | mctrader-data | `scan_candles/ticks/orderbook_events` multi-node union + tier 별 logical key dedup + `dedup.py` 신규 module + quarantine `active-active mismatch` reason 확장 + node priority |
| **MCT-X4 (Coverage + diagnostic surface)** | mctrader-data | `tier_coverage` node 차원 노출 + heartbeat-aware gap detection helper + CLI `mctrader-data status` (heartbeat + dedup metric 출력 + exit code) |
| **MCT-X5 (Ops / deployment)** | mctrader-hub `scripts/ha/` | systemd unit template + EnvironmentFile template + Ansible playbook (`serial: 1` rolling) + `heartbeat_health_check.sh` + README |
| **MCT-X6 (Web status panel)** | mctrader-web | `pages/00_status.py` Streamlit page — heartbeat freshness / lag per tier / quarantine count / dedup ratio + 임계 초과 빨간 banner |
| **MCT-X7 (Epic close + Calibration)** | mctrader-hub | EPIC-RESULTS-MCT-X1 + Calibration metric (throughput / scan latency overhead) + 양 node 30분 E2E demo + child Story close |

### 6.2 Dependency graph

```
MCT-X1 (foundation, ADR amendment freeze)
   │
   ├─→ MCT-X2 (writer + heartbeat)
   │      │
   │      ├─→ MCT-X3 (scan + dedup) ─┐
   │      ├─→ MCT-X4 (coverage)  ────┤
   │      └─→ MCT-X5 (ops)       ────┤
   │                                 │
   │                MCT-X6 (web status, X2 heartbeat schema freeze 후 가능)
   │                                 │
   └────────────────────────────────→ MCT-X7 (Epic close)
```

X3 / X4 / X5 = MCT-X2 후 parallel 가능. X6 = X2 의 heartbeat schema freeze 후 X3 / X4 와 parallel.

### 6.3 Acceptance criteria

**Blocking (B1–B8)**:

- B1: 두 node 동시 수집 — per-node partition write contention 0 + 양 partition 모두 정상 row
- B2: scan_* 가 multi-node partition merge + logical key dedup transparent (engine/web 변경 0 검증)
- B3: heartbeat JSON atomic write (write-temp → fsync → rename) + cross-host read + 30s freshness gate
- B4: rolling deploy — 한 node restart 동안 다른 node 단독 수집 / read-side gap 0 (T1 closed candle 기준)
- B5: ADR-009 §D2 / §D10 / §D11 amendment 적용 + `_lineage.json` + parquet metadata 에 `node_id`
- B6: T1 / T2 / T3 dedup contract 모두 unit + integration test (T3 = best-effort 명시)
- B7: quarantine `active-active mismatch` reason 신규 + counter 노출 + Streamlit visible
- B8: Streamlit `00_status` page = heartbeat 양 node 시각화 + tier 별 lag + 임계 초과 banner + AppTest smoke

**Calibration (C1–C2)**:

- C1: write throughput per node (records/sec) — single vs HA 비교, **per-node slowdown < 10%** (Bithumb stream rate 가 같으니 사실상 동일해야 함)
- C2: scan + dedup latency overhead — single-root vs multi-root × N nodes, **slowdown < 30%** (read 비용 ~2x 가 worst case)

**Demonstration (D1)**:

- 양 node 30분 동시 수집 + heartbeat green 유지 + 중간에 NODE_A 1회 restart + read-side gap 0 + dedup ratio 보고서

### 6.4 Out-of-scope (확정)

- Multi-network / different ISP (다음 Epic candidate — same network 가정)
- Slack / email alert (v1 = Streamlit + CLI status only)
- Object storage / S3 / R2 (NFS / SMB / Ceph 만)
- Active-passive failover (active-active 채택)
- Bithumb history REST backfill 메커니즘 변경 (DataEngineerAgent 기존 책임 유지)
- DuckDB write path 변경 (Parquet only invariant 유지)
- Live mode HA (별도 Epic — secret / kill switch / 1Password CLI 영향)
- Storage backend 자체 redundancy (NAS RAID / Ceph EC = storage layer 외부 책임)
- Multi-exchange (현재 Bithumb 단일)
- Auto-rollback (manual `git revert` + 재배포)

### 6.5 후속 Epic candidate (out-of-scope 와 별개)

1. **Multi-network HA** — homelab + cloud VPS, different ISP, Bithumb endpoint 다중화 (있을 시)
2. **Alert routing v2** — Slack / email webhook + threshold rules
3. **Storage tier separation** — hot SSD (recent N-day) + cold object store (history)
4. **Live mode HA** — secret distribution (1Password CLI per host) + kill switch coordination + leader election (live = single writer 의무)
5. **Backfill auto-trigger** — heartbeat lag detection → history REST API auto-fetch (현재 manual)

## 7. Implementation 진입 흐름 (codeforge Story-flow)

cfp-108 phase-6a debut adoption (main `d0bedce` merged) 으로 mctrader-hub 가 codeforge full consumer 상태. 본 Epic 도 동일 패턴:

1. **Phase 1 doc PR** (mctrader-hub) — Epic Story stub `docs/stories/MCT-X1.md` (`story-init.yml` workflow 자동 scaffold) + 6 child stub + ADR-009 amendment commit
2. **Phase 2** (mctrader-data) — MCT-X2 implementation
3. **Phase 3** (mctrader-data) — MCT-X3 / X4 (또는 분리)
4. **Phase 4** (mctrader-hub) — MCT-X5 (ops scripts)
5. **Phase 5** (mctrader-web) — MCT-X6 (status panel)
6. **Phase 6** (mctrader-hub) — MCT-X7 Epic close + EPIC-RESULTS doc + memory

각 Phase 마다 Codex 7-area review → Sonnet decider 우선순위 채택 → admin merge autonomy → /compact 1회 (사용자 패턴 반영). DataEngineerAgent (mctrader-data 변경) + DomainAgent (도메인 KB) overlay 가 develop phase 에서 spawn.
