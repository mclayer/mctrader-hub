# Collector HA — Phase 1 (MCT-X1 Epic Doc + ADR-009 Amendment) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-hub 에 Collector HA Epic 의 Phase 1 doc PR 을 작성. Epic Story (MCT-X1) §1-7 본문 + ADR-009 amendment (§D2 `node=` partition / §D10 `tx_id` / §D11 `sequence_id` / dedup contract 절) + heartbeat JSON schema contract doc + 6 child Story decomposition table.

**Architecture:** doc-only PR. mctrader-hub `docs/stories/MCT-X1.md` (Epic) + `docs/adr/ADR-009-ohlcv-schema.md` (amendment) + `docs/domain-knowledge/contracts/heartbeat-schema.v1.md` (신규). codeforge story-init.yml workflow 는 `type:story` 만 trigger — `type:epic` 은 manual scaffold. child Story (X2~X7) 의 GitHub issue 등록 + scaffold 는 본 Phase 1 close 후 각 Phase 진입 시 별도 plan.

**Tech Stack:** Markdown (doc only). codeforge workflows: `story-section-schema.yml`, `phase-gate-mergeable.yml`, `phase-label-invariant.yml`. GitHub CLI (`gh`) for issue / PR 작업. Codex 7-area review (codex:rescue subagent + codex:gpt-5-4-prompting).

**Spec:** [docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md](../specs/2026-05-05-collector-ha-active-active-design.md)

**Working directory:** `c:\workspace\mclayer\mctrader-hub` (모든 작업 단일 repo)

**Branch convention:** `feat/MCT-X1-collector-ha-epic` (X1 = Phase 1 진입 시 부여될 실제 issue 번호로 치환)

**Phase 1 의 deliverables:**
1. GitHub issue (Epic, `type:epic` label)
2. `docs/stories/MCT-X1.md` (Epic Story §1-11 본문, doc-only)
3. `docs/adr/ADR-009-ohlcv-schema.md` amendment (3 section)
4. `docs/domain-knowledge/contracts/heartbeat-schema.v1.md` (신규)
5. PR + Codex 7-area review pass + admin merge

**Out-of-scope (Phase 1):**
- 6 child Story (X2~X7) 의 GitHub issue 등록 (각 Phase 진입 시 별도 작업)
- mctrader-data / mctrader-web 코드 변경 (Phase 2~5)
- 실제 collector 가동 (Phase 6 Calibration 후)

---

## File Structure

| File | Action | 책임 |
|---|---|---|
| `docs/stories/MCT-X1.md` | NEW | Epic Story §1-11 본문 (verbatim 요구사항 + 도메인 해석 + Codex review + child decomposition table) |
| `docs/adr/ADR-009-ohlcv-schema.md` | MODIFY | §D2 partition `node=` level 추가 / §D10 tick `tx_id` / §D11 orderbook `sequence_id` / §D2-D11 공통 dedup contract 절 신설 |
| `docs/domain-knowledge/contracts/heartbeat-schema.v1.md` | NEW | heartbeat JSON schema (node_id / collector_run_id / version / ws_state / last_event_ts_per_tier / metrics) + atomic write 규약 + path 규약 |

---

## Task 1: Bithumb public WebSocket schema 사전 검증

본 task 는 **ADR-009 amendment 의 tx_id / sequence_id 결정 전제**. Bithumb 공식 API doc 의 WS transaction stream + orderbook stream schema 확인.

**Files:** (검증만, 파일 변경 없음)

- [ ] **Step 1: WebFetch Bithumb 공식 WebSocket 문서**

```
Tool: WebFetch
URL: https://apidocs.bithumb.com/docs/websocket_public
Prompt: "Identify whether the WebSocket transaction (체결) stream includes a unique transaction id field per event, and whether the orderbook (호가) stream includes a sequence number / monotonically increasing identifier per snapshot or delta event. Report exact field names and JSON examples if available."
```

Expected: schema 의 transaction stream 과 orderbook stream 의 message envelope 구조 파악.

- [ ] **Step 2: 결과 분류**

3 가지 case:

| Case | 결과 | 적용 |
|---|---|---|
| **A** | 양 stream 모두 unique id 존재 (e.g., `cont_no`, `seq`) | ADR-009 §D10 `tx_id` + §D11 `sequence_id` 채택, fallback tuple = secondary |
| **B** | transaction 만 unique id 존재 | T2 = unique id, T3 = fallback tuple `(snapshot_ts, side, price, qty_delta)` 채택 |
| **C** | 둘 다 unique id 부재 | T2/T3 모두 fallback tuple, ADR-009 amendment 에 그 사실 + best-effort 명시 강화 |

- [ ] **Step 3: 결정 결과를 임시 메모로 기록**

다음 task 에서 ADR-009 amendment 작성 시 사용. **이 plan 의 후속 task 의 ADR amendment 본문은 case 별로 분기되므로, 본 step 의 결과를 명시적으로 working memory 에 기록 후 진행.**

`bithumb_ws_id_case = A | B | C` (text 메모 또는 후속 task 본문 작성 시 직접 반영)

---

## Task 2: branch 분기 + heartbeat schema doc 작성

heartbeat 는 ADR-009 와 별개 operational artifact 이므로 별도 contract doc 으로 분리, ADR-009 에서 참조.

**Files:**
- Create: `docs/domain-knowledge/contracts/heartbeat-schema.v1.md`

- [ ] **Step 1: branch 분기 (current = main 가정)**

```powershell
git checkout main
git pull --ff-only origin main
git checkout -b feat/MCT-X1-collector-ha-epic
```

Expected: branch 가 main 의 latest 위에 분기, working tree clean.

- [ ] **Step 2: directory 생성 + heartbeat schema doc 작성**

`docs/domain-knowledge/contracts/` directory 가 없으면 생성. (Glob 으로 확인 — `docs/domain-knowledge/` 가 이미 존재하면 contracts/ 만 추가).

```powershell
# directory 확인
Test-Path docs/domain-knowledge/contracts
# 없으면
New-Item -ItemType Directory -Path docs/domain-knowledge/contracts -Force
```

- [ ] **Step 3: heartbeat-schema.v1.md 본문 작성**

Create `docs/domain-knowledge/contracts/heartbeat-schema.v1.md`:

````markdown
# Heartbeat Schema v1 — Collector HA Active-Active

## Purpose

Active-active multi-node collector 에서 각 node 의 liveness / lag / dedup 상태를 cross-host visible 하게 노출하는 storage-side artifact. Streamlit `00_status` page + CLI `mctrader-data status` + Ansible rolling deploy health gate 의 single source of truth.

## Path

```
<MCTRADER_DATA_ROOT>/market/manifest/heartbeat-{node_id}.json
```

- `node_id` = 호스트 식별자 (e.g., `NODE_A`, `NODE_B`). low cardinality (호스트 수 만큼).
- 각 node 가 **자기 file 만** write. cross-host write contention 0.

## Write 규약 (atomic)

1. write to temp file: `heartbeat-{node_id}.json.tmp`
2. `fsync` temp file
3. `rename` temp → `heartbeat-{node_id}.json` (POSIX atomic rename, NFS atomic rename within same directory)
4. write interval = 5 seconds (default, configurable via `--heartbeat-interval` CLI flag)

## JSON Schema (v1)

```json
{
  "schema_version": "heartbeat.v1",
  "node_id": "NODE_A",
  "collector_run_id": "A-2026-05-05T12:34:56Z",
  "version": "git-sha-abc1234",
  "started_at": "2026-05-05T00:00:00Z",
  "now": "2026-05-05T12:34:56Z",
  "uptime_seconds": 45296,
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

### Field 정의

| Field | Type | 설명 |
|---|---|---|
| `schema_version` | str literal | `"heartbeat.v1"` 고정 |
| `node_id` | str | 호스트 식별자 |
| `collector_run_id` | str | 현재 collector run 의 unique id (MCT-65 manifest 와 1:1 align) |
| `version` | str | git commit sha (deploy 추적) |
| `started_at` | ISO8601 UTC | collector process 기동 시각 |
| `now` | ISO8601 UTC | heartbeat write 시각 (freshness 판정 기준) |
| `uptime_seconds` | int | `now - started_at` (편의 derived field) |
| `ws_state` | enum | `"connected"` / `"reconnecting"` / `"disconnected"` |
| `last_event_ts_per_tier` | dict[str, ISO8601 UTC] | 각 tier (candle/tick/orderbook) 의 마지막 event 수신 시각 |
| `queue_depth` | int | 내부 buffer 의 미처리 event 수 |
| `metrics.events_per_sec` | float | 최근 5s window 평균 |
| `metrics.dup_skip_count` | int (cumulative) | 본 run 시작 이래 dup-hash skip 누적 |
| `metrics.quarantine_count` | int (cumulative) | 본 run 시작 이래 quarantine 누적 |
| `metrics.ws_reconnect_count` | int (cumulative) | 본 run 시작 이래 WS reconnect 횟수 |
| `metrics.backfill_pending_seconds` | int | 현재 backfill queue 의 가장 오래된 gap 길이 |

## Freshness 판정 (consumer 측)

`now - mtime(heartbeat-{node_id}.json) > 30s` → node liveness 위반. 다음 alert level:

- `< 10s`: green
- `10s ≤ Δ < 30s`: yellow (clock drift 가능)
- `≥ 30s`: red (node down 또는 restart 중)

## Lag 판정 (consumer 측)

`now - last_event_ts_per_tier[candle] > 2 * timeframe_seconds` → candle lag (T1 closed bar 기준 2-bar 이상 빠짐).

`now - last_event_ts_per_tier[tick] > 60s` → tick lag (default).

`now - last_event_ts_per_tier[orderbook] > 60s` → orderbook lag (default).

threshold 는 `mctrader-data` 의 status CLI 가 default 적용, 사용자 override 가능.

## 호환성

- **v1 → v2 (후속)**: 새 field 추가는 backward compatible (consumer 가 unknown field ignore). field 제거 / type 변경은 schema_version bump 의무.
- consumer 는 `schema_version` mismatch 시 warning + best-effort parse.

## 참조

- Spec: [collector-ha-active-active-design.md](../../superpowers/specs/2026-05-05-collector-ha-active-active-design.md) §4.2 / §5.1
- ADR-009 §D2 / §D10 / §D11 amendment (active-active dedup contract 절)
````

- [ ] **Step 4: file syntax 검증 (markdown 렌더링 확인)**

```powershell
# basic syntax check — JSON code block 이 valid JSON 인지 확인
# (markdown lint 없으면 skip 가능)
Test-Path docs/domain-knowledge/contracts/heartbeat-schema.v1.md
```

Expected: `True`. 파일 존재.

- [ ] **Step 5: commit**

```powershell
git add docs/domain-knowledge/contracts/heartbeat-schema.v1.md
git commit -m "docs(ha): heartbeat JSON schema v1 contract for collector HA active-active

Path: <root>/market/manifest/heartbeat-{node_id}.json
Atomic write (write-temp + fsync + rename, 5s interval).
Field set: node_id / collector_run_id / version / ws_state /
last_event_ts_per_tier / queue_depth / metrics (events_per_sec /
dup_skip / quarantine / ws_reconnect / backfill_pending).
Consumer freshness/lag 판정 threshold default 명시.

References spec §4.2 / §5.1.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: ADR-009 amendment — §D2 partition `node=` level

**Files:**
- Modify: `docs/adr/ADR-009-ohlcv-schema.md`

- [ ] **Step 1: 현재 ADR-009 §D2 read**

```
Tool: Read
file_path: c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-009-ohlcv-schema.md
```

§D2 의 정확한 partition path 정의 위치 확인. (line 번호 메모)

- [ ] **Step 2: §D2 amendment 본문 작성 — partition path 에 `node=` level 추가**

기존 §D2 의 partition spec 직후 또는 D2 의 적절한 sub-section 에 다음 amendment 추가:

```markdown
### §D2.1 Amendment (2026-05-05) — Active-Active HA partition `node=` level

Collector HA Epic (MCT-X1) 도입에 따라 `ohlcv.v1` partition path 에 `node=` level 을 leaf 직전에 추가:

```
market/ohlcv/schema_version=ohlcv.v1/exchange=.../symbol=.../
       timeframe=.../year=.../month=.../date=.../node=NODE_A/
       {collector_run_id}-{batch_seq}.parquet
```

- `node` = 호스트 식별자 (low cardinality, e.g., `NODE_A` / `NODE_B`)
- file name = `{collector_run_id}-{batch_seq}.parquet`
- DuckDB Hive partition pruning 으로 특정 node 의 데이터만 scan 가능 (lineage / debugging)
- 단일 node 운영 시 `node=DEFAULT` (또는 hostname) 적용 — backward compat

**Active-Active dedup contract** (§D2-§D11 공통, 본 amendment 의 anchor 절):

- read-side `scan_*` API 가 multi-node partition union + tier 별 logical key dedup
- conflict resolution = **node priority (alphabetical / inventory 순)** + content mismatch 시 quarantine (§D? 의 dup different-hash quarantine 정책 확장 — `active-active mismatch` reason 신규)
- T1 candle: logical key = `(exchange, symbol, timeframe, ts)` — OHLCV byte-identical 기대
- T2 tick: logical key 는 §D10.1 amendment 참조
- T3 orderbook: logical key 는 §D11.1 amendment 참조
- Lineage `_lineage.json` + parquet file metadata 에 `node_id` 추가 (MCT-65 manifest 와 1:1 align)

References:
- Spec: [collector-ha-active-active-design.md](../superpowers/specs/2026-05-05-collector-ha-active-active-design.md)
- Heartbeat contract: [heartbeat-schema.v1.md](../domain-knowledge/contracts/heartbeat-schema.v1.md)
```

(주의: `§D? 의 dup different-hash quarantine 정책` 의 `?` 는 ADR-009 read 후 정확한 section 번호로 치환)

- [ ] **Step 3: tick.v1 §D10.1 amendment 작성**

§D10 직후에 다음 추가 (Task 1 의 case A/B/C 결과 반영):

```markdown
### §D10.1 Amendment (2026-05-05) — Active-Active dedup logical key for tick.v1

T2 tick stream 의 active-active dedup logical key:

- **Primary key**: `(exchange, symbol, tx_id)` — Bithumb WebSocket transaction stream 의 unique transaction id field. Bithumb 공식 doc 검증 결과 [Task 1 case A or B 인 경우]: field name = `cont_no` (또는 검증된 정확 field 명).
- **Fallback** (Task 1 case C 또는 tx_id 부재 record): `(exchange, symbol, ts, price, qty, side)` tuple.
- conflict resolution: 동일 primary key 의 content mismatch = `active-active mismatch` quarantine.
- `tx_id` field 는 tick.v1 schema 에 추가 (`Optional[str]` — Bithumb 부재 시 null).
```

(Task 1 결과에 따라 본문 분기 — case A/B 는 정확한 field 명 채택, case C 는 fallback tuple 만 명시)

- [ ] **Step 4: orderbook.v1 §D11.1 amendment 작성**

§D11 직후에 다음 추가 (Task 1 의 case A/B/C 결과 반영):

```markdown
### §D11.1 Amendment (2026-05-05) — Active-Active dedup logical key for orderbook.v1

T3 orderbook event stream 의 active-active dedup logical key:

- **Primary key**: `(exchange, symbol, snapshot_ts, sequence_id)` — Bithumb WebSocket orderbook stream 의 sequence number field. Bithumb 공식 doc 검증 결과 [Task 1 case A 인 경우]: field name = `seq` (또는 검증된 정확 field 명).
- **Fallback** (Task 1 case B/C 또는 sequence_id 부재 record): `(snapshot_ts, side, price, qty_delta)` tuple.
- **Best-effort dedup**: node-local reconstruction 의 sequence_id divergence 가능성 → dedup 정확도 < 100% 가능. 실데이터 기준 dedup ratio 측정 + 허용 범위 (target > 95%) 는 MCT-X3 의 Calibration AC 에서 freeze.
- conflict resolution: 동일 primary key 의 content mismatch = `active-active mismatch` quarantine.
- `sequence_id` field 는 orderbook.v1 schema 에 추가 (`Optional[int]` — Bithumb 부재 시 null).
```

- [ ] **Step 5: file content 일관성 검증**

```
Tool: Read
file_path: c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-009-ohlcv-schema.md
```

확인 항목:
- §D2.1 / §D10.1 / §D11.1 모두 추가됨
- 기존 §D2 / §D10 / §D11 본문은 변경 없음 (additive only)
- ADR 의 "Status" 또는 "History" 섹션이 있다면 amendment 일자 + 사유 추가

- [ ] **Step 6: commit**

```powershell
git add docs/adr/ADR-009-ohlcv-schema.md
git commit -m "docs(adr-009): amendment §D2.1/§D10.1/§D11.1 — active-active HA dedup contract

§D2.1: partition path 에 node= level 추가 + active-active dedup contract anchor
§D10.1: tick.v1 의 dedup logical key (primary tx_id + fallback tuple)
§D11.1: orderbook.v1 의 dedup logical key (primary sequence_id + fallback tuple, best-effort 명시)

Bithumb public WS schema 검증 결과 (Task 1) 반영. MCT-X1 Phase 1 의 amendment.

References:
- Spec: docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md
- Heartbeat: docs/domain-knowledge/contracts/heartbeat-schema.v1.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Epic issue (X1) GitHub 등록 + Story 본문 §1-7 작성

**Files:**
- Create: `docs/stories/MCT-X1.md` (X1 = 실제 issue 번호 부여 후 file rename)

- [ ] **Step 1: 다음 issue 번호 확인 + Epic issue 생성**

```powershell
gh issue list --repo mclayer/mctrader-hub --state all --limit 1 --json number --jq '.[0].number'
```

Expected: 직전 max issue 번호 (e.g., 87 — MCT-70 Epic close PR). 다음 = 88 또는 그 이상 (PR 도 같은 number space).

```powershell
gh issue create --repo mclayer/mctrader-hub `
  --title "[EPIC] Collector HA — Active-Active Multi-Node + Shared Storage" `
  --label "type:epic" `
  --body @"
## Epic 목적

mctrader-data collector daemon 을 backtest / WFO / Streamlit 의 데이터 source-of-truth 로 본격 가동하기 직전 시점에서, **same-LAN 2+ Linux node active-active + 공유 storage + 1 MCTRADER_DATA_ROOT** 구성으로 single-host failure (process crash / host down / code deploy downtime) 를 cover.

## 사용자 요구사항 (verbatim, 2026-05-05)

> mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.

## Spec

[docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md](../blob/main/docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md)

## Phase 1 deliverables

- Epic Story \`docs/stories/MCT-{ISSUE_NUMBER}.md\` (§1-11)
- ADR-009 amendment §D2.1 / §D10.1 / §D11.1
- Heartbeat JSON schema contract \`docs/domain-knowledge/contracts/heartbeat-schema.v1.md\`

## 6 Child Story (Phase 2~6 별도 issue 등록)

| Story | Owner repo | Scope |
|---|---|---|
| MCT-X2 | mctrader-data | Collector writer + heartbeat |
| MCT-X3 | mctrader-data | Scan-side merge + dedup |
| MCT-X4 | mctrader-data | Coverage + diagnostic surface (CLI status) |
| MCT-X5 | mctrader-hub | Ops / deployment (systemd + Ansible) |
| MCT-X6 | mctrader-web | Streamlit 00_status panel |
| MCT-X7 | mctrader-hub | Epic close + Calibration |
"@
```

Expected: GitHub issue 번호 출력 (e.g., `https://github.com/mclayer/mctrader-hub/issues/88`).

issue 번호 메모: `EPIC_ISSUE_NUMBER=88` (이하 X1 placeholder 모두 88 로 치환).

- [ ] **Step 2: issue 번호 확정 후 docs/stories/MCT-{N}.md 작성**

```powershell
$N = 88  # Step 1 의 실제 번호로 치환
$path = "docs/stories/MCT-$N.md"
```

`docs/stories/MCT-88.md` (예시 — 실제 번호로 치환) 작성:

(직전 MCT-70 패턴 그대로 — frontmatter + §1-11)

```markdown
---
story_key: MCT-88
status: phase:완료
component: epic
type: epic
parent_epic: null
related_adrs: ADR-009
---

# MCT-88 (Epic): Collector HA — Active-Active Multi-Node + Shared Storage

## 1. 사용자 요구사항 (verbatim, 2026-05-05)

> mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.

## 2. 도메인 해석

mctrader 10번째 implementation Epic (MCT-12 ~ MCT-87 의 후속). 직전 Epic MCT-70 (T2/T3 Backtest Lifecycle Integration) 종료 시점 + cfp-108 phase-6a debut adoption main merge (`d0bedce`) 직후. backtest data 수집의 reliability foundation.

핵심 framing (Sonnet decider brainstorm + 사용자 답변 stack 16 결정):

- **Bithumb single-source HA**: 양 node 가 같은 Bithumb endpoint 구독. Bithumb 측 outage 는 양 node 동시 영향 (본 Epic out-of-scope, 후속 Multi-network HA Epic).
- **same-LAN 2-node active-active**: host failure / code deploy / process crash cover. Multi-network / different ISP 는 후속.
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
| 8 | T1 candle dedup key | `(exchange, symbol, timeframe, ts)` |
| 9 | T2 tick dedup key | `(exchange, symbol, tx_id)` (Bithumb tx_id 우선), fallback `(ts, price, qty, side)` |
| 10 | T3 orderbook dedup key | `(exchange, symbol, snapshot_ts, sequence_id)` (Bithumb seq 우선), fallback `(snapshot_ts, side, price, qty_delta)` — best-effort 명시 |
| 11 | Conflict resolution | logical key 동일 + content mismatch = node priority + quarantine |
| 12 | DuckDB write path | 변경 없음 (Parquet append-only / DuckDB read-only invariant 유지) |
| 13 | Backfill 메커니즘 | 변경 없음 (DataEngineerAgent 기존 의무 유지) |
| 14 | Alert routing v1 | Streamlit `00_status` page + CLI `mctrader-data status` (passive observation) |
| 15 | Code deploy rollback | manual `git revert` + 재배포 |
| 16 | ops/scripts 위치 | mctrader-hub `scripts/ha/` (cross-repo orchestration) + collector heartbeat = mctrader-data 코드 |

16/16 escalation 0건. 사용자 사전 승인 4회 ("ok" trigger).

### Codex 7-area review (Phase 1 PR 머지 직전 / Task 5 에서 수행)

(Task 5 완료 후 본 절 채움)

## 4. Child Story decomposition

| Story | Owner repo | Scope | Dependency |
|---|---|---|---|
| MCT-X2 | mctrader-data | `--node-id` CLI flag + partition writer `node=` 적용 + heartbeat writer (atomic + 5s loop) + lineage `node_id` | X1 (this) |
| MCT-X3 | mctrader-data | `scan_*` multi-node union + tier 별 logical key dedup + `dedup.py` 신규 module + quarantine `active-active mismatch` reason | X2 |
| MCT-X4 | mctrader-data | `tier_coverage` node 차원 + heartbeat-aware gap detection + CLI `mctrader-data status` | X2 |
| MCT-X5 | mctrader-hub `scripts/ha/` | systemd unit template + Ansible playbook (`serial: 1` rolling) + `heartbeat_health_check.sh` + README (host prereq) | X2 |
| MCT-X6 | mctrader-web | `pages/00_status.py` Streamlit page (heartbeat freshness / lag / quarantine + 임계 banner) | X2 (heartbeat schema freeze) |
| MCT-X7 | mctrader-hub | Epic close + Calibration (throughput / scan latency overhead) + 양 node 30분 E2E demo | X3 + X4 + X5 + X6 |

`X` = Phase 2~6 진입 시 각 child issue 번호 부여.

## 5. 요구사항 확장 해석

본 Epic = backtest data reliability foundation. paper / live mode 는 별도 prereq.

확장 해석 — Sonnet decider 도출:

- "데이터 순단을 줄이고자" = active-active 의 자동 cover (single-host failure) + heartbeat 기반 잔여 failure 의 fallback observation.
- "코드 수정사항 배포" = rolling restart `serial: 1` + heartbeat health gate. zero-downtime 까지는 보장 안하지만 read-side gap 0 (T1 closed candle 기준).
- "2개 이상의 Active Node 관리" = active-active (active-passive 거부). dedup 의 부담은 read-side 가 짊어짐 (write contention 0 보장).

## 6. 외부 지식 배경

### Bithumb public WebSocket schema 검증

(Task 1 결과 반영 — case A / B / C 별로 본 절 분기)

- Transaction stream unique id: [Task 1 결과 기재 — e.g., `cont_no` 존재]
- Orderbook stream sequence id: [Task 1 결과 기재]
- 부재 field 의 fallback tuple 적용 결정

### NFS / SMB / Ceph 의 atomic rename 보장

- POSIX `rename(2)` 는 same-directory 내 atomic. NFS server 측 atomic rename 지원 가정 (대부분 서버 OK).
- heartbeat write 패턴 (write-temp + fsync + rename) 이 NFS 환경에서도 안전.
- Ceph 의 경우 same-pool 내 rename atomic.

### systemd `Restart=always` semantics

- process exit (정상 / 비정상 무관) 시 RestartSec 후 재시작.
- `StartLimitBurst` / `StartLimitIntervalSec` default 적용 (5 회 / 10 초 — 폭주 방지).

## 7. 설계 서사

(Spec doc 의 §2 Architecture overview 그대로 인용)

[Architecture diagram 은 spec doc 참조 — 본 Story 는 link 만]

핵심 invariant:
- 양 node 가 같은 source 구독 → Bithumb outage 는 양 node 동시 영향 (out-of-scope)
- 양 node 가 다른 collector_run_id partition 에 write → write contention 0
- 모든 reader 가 단일 MCTRADER_DATA_ROOT mount 에서 read

failure category × cover-by-HA: spec §2.2 참조.

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
```

(주의: 위 본문의 `MCT-88` / `X1~X7` 은 실제 issue 번호로 치환 의무. plan 작성 시점에는 placeholder)

- [ ] **Step 3: file 작성 후 schema 검증 (codeforge story-section-schema.yml workflow 가 enforce — local 미리 확인)**

다음 항목 self-check:
- frontmatter 의 `story_key` / `status` / `component` / `type` / `parent_epic` / `related_adrs` 모두 존재
- §1 ~ §11 헤더 모두 존재
- §1 verbatim 요구사항이 사용자 message 와 일치 (manual diff)

```powershell
Test-Path docs/stories/MCT-88.md
Get-Content docs/stories/MCT-88.md -TotalCount 10  # frontmatter 확인
```

Expected: file 존재 + frontmatter 정상.

- [ ] **Step 4: commit**

```powershell
git add docs/stories/MCT-88.md
git commit -m "[MCT-88] Epic Story §1-7 — Collector HA active-active multi-node

§1: 사용자 요구사항 verbatim
§2: 도메인 해석 (Sonnet decider 16 결정 stack 요약)
§3: Sonnet decider Phase 1 brainstorm 결과 + Codex review placeholder (Task 5 채움)
§4: 6-child decomposition table (X2~X7)
§5: 요구사항 확장 해석
§6: 외부 지식 배경 (Bithumb WS schema 검증 / NFS atomic rename / systemd Restart)
§7: 설계 서사 (spec link)
§8-11: placeholder (Phase 2 이후)

References:
- Spec: docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md
- ADR: docs/adr/ADR-009-ohlcv-schema.md (§D2.1/§D10.1/§D11.1 amendment)
- Heartbeat contract: docs/domain-knowledge/contracts/heartbeat-schema.v1.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Codex 7-area review of Phase 1 PR

codeforge 패턴 의무 — Phase 1 doc PR 머지 직전 Codex 7-area review.

**Files:** (수정 없음, review only — 결과는 Task 4 의 Story §3 에 후속 update)

- [ ] **Step 1: codex:rescue subagent dispatch**

```
Tool: Agent
subagent_type: codex:codex-rescue
description: "Phase 1 doc PR Codex 7-area review"
prompt:
"Review the following Phase 1 doc PR for Collector HA Epic (MCT-88). 7-area:

1. **Spec coverage** — Does the Story §1-7 match the spec doc requirements?
2. **ADR amendment correctness** — §D2.1 / §D10.1 / §D11.1 are additive (no breaking change) and reference Bithumb WS schema correctly?
3. **Dedup contract clarity** — Is the logical key per tier (T1 / T2 / T3) + node priority + quarantine on mismatch unambiguous? Any edge case missed?
4. **Heartbeat schema completeness** — All consumer use cases (Streamlit / CLI / Ansible health gate) covered? Atomic write + freshness + lag threshold defaults reasonable?
5. **Backward compat** — Single-node operation (legacy) still works without migration? `node=DEFAULT` partition path 도입 영향?
6. **Out-of-scope clarity** — Multi-network / Slack alert / Live mode HA 명시 거부, 후속 candidate Epic 으로 분리 — clear?
7. **Phase 2 readiness** — Child Story X2~X6 decomposition 이 codeforge story-init.yml workflow + DataEngineerAgent overlay 와 align 되는가?

Files to review:
- docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md
- docs/superpowers/plans/2026-05-05-collector-ha-phase-1.md
- docs/stories/MCT-88.md
- docs/adr/ADR-009-ohlcv-schema.md (amendment §D2.1 / §D10.1 / §D11.1)
- docs/domain-knowledge/contracts/heartbeat-schema.v1.md

Format: per-area finding (ADOPT / REJECT / OVERRIDE / PUSH-BACK) + escalation list. Sonnet decider 가 후속 채택."
```

Expected: per-area finding list + push-back list.

- [ ] **Step 2: Sonnet decider — Codex finding 일괄 채택 / push-back 응답**

각 finding 마다:
- ADOPT: Story §3 의 Codex review 절에 기록 + 필요 시 Story / ADR / heartbeat doc inline 수정
- REJECT (semantic): 근거 명시 후 §3 에 기록
- OVERRIDE: 사용자 escalation (사용자 stop 동안 결정 보류)
- PUSH-BACK: design 의도 강화 후 §3 에 기록

직전 Epic (MCT-70) Codex review = 22/22 ADOPT, escalation 0. 동일 수준 기대.

- [ ] **Step 3: Story §3 의 Codex review 절 update commit**

```powershell
# Story file 의 §3 section 만 수정 (다른 section 변경 X)
# Edit tool 사용 — placeholder "(Task 5 완료 후 본 절 채움)" 을 실제 review 결과로 대체

git add docs/stories/MCT-88.md
git commit -m "[MCT-88] §3 Codex 7-area review 결과 반영 (escalation 0/N ADOPT N/N)

7-area finding (Codex F-1 ~ F-N) ADOPT/REJECT/PUSH-BACK 결과 정리.
Sonnet decider 합성 후 Story / ADR / heartbeat doc inline 수정 동반.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: PR 작성 + admin merge

**Files:** (수정 없음, GitHub 작업)

- [ ] **Step 1: branch push**

```powershell
git push -u origin feat/MCT-88-collector-ha-epic
```

Expected: push 성공, GitHub URL 출력.

- [ ] **Step 2: PR 작성**

```powershell
gh pr create --repo mclayer/mctrader-hub `
  --base main `
  --head feat/MCT-88-collector-ha-epic `
  --title "[MCT-88] feat: Collector HA Epic Phase 1 — Story + ADR-009 amendment + heartbeat contract" `
  --body @"
## Summary

Collector HA Epic (MCT-88) Phase 1 doc PR.

- ``docs/stories/MCT-88.md`` — Epic Story §1-7 (§8-11 placeholder for Phase 2+)
- ``docs/adr/ADR-009-ohlcv-schema.md`` — §D2.1 / §D10.1 / §D11.1 amendment (active-active dedup contract)
- ``docs/domain-knowledge/contracts/heartbeat-schema.v1.md`` — heartbeat JSON schema v1 (NEW)

## Decision Stack

Sonnet decider brainstorm: 16/16 escalation 0건 (사용자 사전 승인 4회 ``ok`` trigger).
Codex 7-area review: N/N ADOPT, escalation 0건.

Spec: ``docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md``
Plan: ``docs/superpowers/plans/2026-05-05-collector-ha-phase-1.md``

## Phase 2 진입 prerequisite

본 PR merge 후 child issue (X2~X7) 등록 가능.

Closes (Phase 1 only): #88

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"@ `
  --label "type:epic,phase:완료"
```

Expected: PR URL 출력 (e.g., `https://github.com/mclayer/mctrader-hub/pull/89`).

- [ ] **Step 3: CI watch (foreground polling, no background — feedback memory)**

```powershell
$pr = gh pr view --repo mclayer/mctrader-hub --json number --jq '.number' 89
gh pr checks --repo mclayer/mctrader-hub $pr --watch
```

Expected: `phase-gate-mergeable.yml` (CFP-106 fast-pass — type:epic + doc-only 자동 success), `story-section-schema.yml`, `phase-label-invariant.yml` 모두 green. 또는 ACTION_REQUIRED (codeforge plugin known defect #143 fallback — admin merge autonomy 적용).

CI 분류 (feedback memory):
- SUCCESS = green merge 가능
- FAILURE = 즉시 fix → push → 재 watch
- ACTION_REQUIRED = doc-only PR 의 phase-gate fast-pass mismatch — admin merge 진행

- [ ] **Step 4: admin merge (autonomy 적용 — feedback memory)**

```powershell
gh pr merge --repo mclayer/mctrader-hub $pr --admin --squash --delete-branch
```

Expected: PR merged, branch 삭제, main 업데이트.

- [ ] **Step 5: main 업데이트 + Epic issue close**

```powershell
git checkout main
git pull --ff-only origin main
gh issue close 88 --repo mclayer/mctrader-hub --comment "Phase 1 doc PR (#89) merged. Phase 2 (MCT-X2 implementation) 진입 가능."
```

Expected: main 이 PR squash merge commit 으로 업데이트, issue closed.

---

## Task 7: Phase 1 close + Phase 2 plan kickoff

**Files:** (수정 없음, 후속 plan 준비)

- [ ] **Step 1: memory update (Sonnet auto-memory)**

```
Tool: Write
file_path: C:\Users\mccho\.claude\projects\c--workspace-mclayer-mctrader-hub\memory\project_mctrader.md
```

기존 `project_mctrader.md` 끝에 다음 section 추가 (memory 의 evolving log 패턴):

```markdown
## Epic MCT-88 Phase 1 진입 (2026-05-05, mctrader-hub#89 merged)

Collector HA Active-Active Multi-Node + Shared Storage. 사용자 발화 = "mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다."

**Phase 1 deliverables**:
- Epic Story (MCT-88, §1-7) + 6-child decomposition (X2~X7)
- ADR-009 amendment §D2.1 / §D10.1 / §D11.1 (active-active dedup contract)
- Heartbeat JSON schema contract v1 (`docs/domain-knowledge/contracts/heartbeat-schema.v1.md`)

**Sonnet decider brainstorm**: 16/16 escalation 0, 사용자 사전 승인 4회 "ok" trigger.

**Codex 7-area review**: N/N ADOPT, escalation 0.

**다음 step**: Phase 2 = MCT-X2 implementation (mctrader-data, collector writer + heartbeat writer). 별도 plan 작성 예정.
```

- [ ] **Step 2: Phase 2 plan kickoff 준비**

다음 plan file path:

`docs/superpowers/plans/YYYY-MM-DD-collector-ha-phase-2.md` (mctrader-data 측 implementation, MCT-X2 = collector writer + heartbeat).

본 Phase 1 close 후 사용자 trigger 시 신규 brainstorming 또는 directly writing-plans skill 진입.

---

## Self-Review Checklist

본 plan 의 self-review (skill 명시 의무):

**1. Spec coverage:**
- [x] Spec §1 결정 stack 16개 → Task 4 Story §3 의 16-row table 에 모두 매핑
- [x] Spec §2 Architecture overview → Story §7 (link to spec)
- [x] Spec §3 Partition layout + dedup contract → Task 3 ADR-009 §D2.1 / §D10.1 / §D11.1
- [x] Spec §4 Code rolling deployment → Phase 4 (MCT-X5) 의 별도 plan 으로 deferred
- [x] Spec §5 Monitoring + mctrader-data implementation surface → Phase 2~3 (MCT-X2/X3/X4) 별도 plan
- [x] Spec §6 Story decomposition → Task 4 Story §4 의 6-row child table
- [x] Spec §7 Implementation 진입 흐름 → Task 7 의 Phase 2 kickoff

**2. Placeholder scan:**
- [x] `MCT-X1 ~ X7` placeholder = 의도된 (issue 번호 부여 직전) — Task 4 Step 1 에서 실제 번호로 치환 명시
- [x] Task 1 case A/B/C 분기 = 의도된 (Bithumb WS 검증 결과 의존) — Task 3 의 §D10.1 / §D11.1 본문에서 case 별 분기 명시
- [x] Task 5 Codex review N/N 의 N = 의도된 (실제 finding 수 의존)
- [x] "TBD / TODO / 적절히" 같은 vague directive 없음 — 모든 step 이 exact command + file path

**3. Type consistency:**
- [x] heartbeat schema field 명 (Task 2 의 schema doc) ↔ Story §6 외부 지식 배경 ↔ ADR-009 §D2.1 의 lineage `node_id` 모두 일관
- [x] partition path `node=NODE_A` ↔ file name `{collector_run_id}-{batch_seq}.parquet` ↔ MCT-65 manifest 1:1 align 모두 spec 와 일관
- [x] tier 명 (T1 candle / T2 tick / T3 orderbook) plan 전체 일관

**4. Scope check:**
- [x] Phase 1 doc-only PR scope 만 — Phase 2~6 implementation 은 별도 plan
- [x] X1 PR 안에 child issue 등록 포함 X (Phase 2 진입 직전 별도 task)
- [x] codeforge workflow trigger (story-init.yml) = type:story 만 — type:epic 은 manual scaffold (Task 4 본문 명시)

**5. Verification step (TDD 대체 — doc-only PR):**
- [x] Task 2 Step 4: heartbeat doc 존재 + JSON code block valid
- [x] Task 3 Step 5: ADR-009 file 일관성 (additive only)
- [x] Task 4 Step 3: Story file frontmatter 정상
- [x] Task 6 Step 3: CI green (phase-gate / story-section-schema / phase-label-invariant)
- [x] Task 6 Step 4: admin merge (CFP defect #143 fallback)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-05-collector-ha-phase-1.md`.**

**Phase 1 의 task 7 + step 30 합계는 doc-only 기준으로 약 60 ~ 90분 소요 예상** (Bithumb WS schema fetch + Story 본문 작성 + ADR amendment + heartbeat contract + Codex review iteration).

두 execution 옵션:

**1. Subagent-Driven (recommended for codeforge workflow)** — 각 Task 별 fresh subagent dispatch + Sonnet 이 review. codeforge develop phase 의 multi-agent 패턴 (DataEngineerAgent / DomainAgent / Architect) 와 align.

**2. Inline Execution** — 본 session 에서 Task 1~7 sequential 실행 + checkpoint review. 사용자가 매 task 완료 시 "ok" trigger.

**어느 쪽?**
