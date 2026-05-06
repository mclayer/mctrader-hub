---
story_key: MCT-93
story_issues:
  - repo: mclayer/mctrader-hub
    number: 101
status: phase:완료
---

# MCT-93: Collector HA — Status CLI + Coverage Node Breakdown + Heartbeat Sink Adapter (X4 of MCT-89)

- **Issue**: #101
- **Status**: phase:완료

## 1. 사용자 요구사항 (verbatim)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: mctrader-data 측 diagnostic surface. 부모 Epic = MCT-89. X3 (MCT-92, mctrader-data 0.7.0 main merged) 후속. Phase 1 spec/plan 의 X4 = `tier_coverage` node 차원 노출 + heartbeat-aware gap detection helper + CLI `mctrader-data status` (heartbeat + dedup metric 출력 + exit code) + DedupCounterSink → HeartbeatWriter adapter + quarantine artifact root manifest persistence. measurable hook freeze 의무.)

## 2. 도메인 해석

본 Story 는 부모 Epic **MCT-89** 의 **X4 child slice** 로, sister Story **MCT-92 (X3)** 가 freeze 한 *measurable hooks* (`heartbeat-schema.v1.metrics.{dup_skip_count, quarantine_count}` cumulative + `DedupResult.{dup_skip_count, quarantine_count, quarantine_records}` Generator return) 를 사용자/operator 가 **능동 관찰** 할 수 있도록 노출하는 *passive observation surface* 단계.

### 2.1 X4 의 도메인 위치 — "데이터 순단 0" 의 *가시성 layer*

X3 가 read-side dedup 으로 *데이터 순단 0* 자체를 **달성**한 시점에서, X4 는 그 달성을 사용자가 **확인**할 수단을 제공한다. backtest user 입장에서:

- "지금 양 node 가 살아 있는가?" → heartbeat freshness (`now - mtime(heartbeat-{node_id}.json)`)
- "최근 dedup 으로 얼마나 많은 row 가 skip 되었나?" → `metrics.dup_skip_count` cumulative
- "active-active mismatch 가 발생하고 있나?" → `metrics.quarantine_count` cumulative + `<root>/market/manifest/quarantine/` artifact 누적
- "어느 node 가 어떤 collector_run_id 로 어디까지 cover 했나?" → `tier_coverage.node_coverage[node_id]` per-node breakdown
- "이 gap 은 진짜 데이터 누락인가, 아니면 한쪽 node down 영향인가?" → `classify_gap(gap, heartbeats_now)` conservative classifier

부모 Epic 16-row decision stack `#14 Alert routing v1 = passive observation (Streamlit 00_status + CLI status)` 가 본 X4 의 anchor — proactive push (Slack / email) 는 v2 후속.

### 2.2 DataEngineerAgent invariant 와 X4 의 관계 — 모든 invariant 유지 (변경 0)

X4 는 X3 와 동일하게 *read-only diagnostic surface* — DataEngineerAgent 의 4 invariant 모두 변경 0:

| Invariant | X4 영향 | 근거 |
|---|---|---|
| Tick / Orderbook lossless (packet loss → backfill 의무) | **변경 0** | X4 는 dedup 결과 표시 / coverage report 만 — packet loss 자체를 cover 하지 않음 |
| DuckDB single-writer (multi-reader OK) | **변경 0** | X4 는 reader (heartbeat JSON read + scan_* 호출) 만 — writer path 영향 0 |
| Parquet append-only | **변경 0** | X4 는 read-only (quarantine artifact write 는 별도 manifest tree, parquet partition 영역 무관) |
| received_at lookahead 방어 (`available_from_ts`) | **변경 0** | X4 의 status CLI 는 cumulative metric 만 표시 — temporal filter 영향 surface 없음 |

**유일하게 추가되는 write surface** = quarantine artifact (`<root>/market/manifest/quarantine/{tier}-{detected_at_iso}-{batch_seq}.json`). DataEngineerAgent invariant 가 *parquet partition* 영역의 append-only 만 다루므로, manifest tree 의 신규 file 생성은 invariant 위배 아님. atomic write (temp → fsync → rename) 으로 reader 가 partial-write file 을 보지 않음.

### 2.3 X3-X4 dependency boundary

X3 의 freeze 된 measurable hook 만 사용 (X3 에서 추가 surface 신규 도입 안 함):

| X3 freeze 된 surface | X4 사용처 |
|---|---|
| `dedup.DedupCounterSink` Protocol | X4 의 `HeartbeatCounterSink` concrete adapter (Codex F-4 SUGGEST 채택 — composition + threading.Lock) |
| `dedup.QuarantineRecord` dataclass | X4 의 `persist_quarantine_records(root, records)` helper input |
| `dedup.DedupResult.quarantine_records` Generator return | scan caller (storage.py / orderbook_replay.py) 가 X4 helper 호출 시 input |
| `heartbeat-schema.v1.metrics.dup_skip_count / quarantine_count` cumulative | status CLI 의 표시 source |
| `heartbeat-schema.v1.last_event_ts_per_tier` per-tier ts | status CLI lag 계산 + `classify_gap` heartbeat input |
| `CoverageReport` (Pydantic, extra="forbid") | X4 의 `node_coverage: dict[str, NodeCoverage]` 신규 field 확장 |

## 3. 관련 ADR

X4 는 **신규 ADR amendment 없음**. Phase 1 (PR #90 main merged, `bd5dde5`) 의 ADR-009 §D2.1 / §D10.7 / §D11.8 amendment + X3 의 dedup contract 그대로.

### 3.1 강한 관련 (직접 제약, 변경 없음 — 그대로 enforce)

- **ADR-009 §D2.1** — Mixed legacy partition 영구 지원 + active-active dedup contract anchor. X4 의 `tier_coverage.node_coverage` 가 `node=DEFAULT` legacy partition 도 별도 entry 로 노출 (existing behavior 보존).
- **ADR-009 §D5** — T1 candle late correction. X4 의 status CLI 표시 영향 없음 (T1 은 quarantine emit 안 함, dup_skip_count 만 증가).
- **ADR-009 §D10.7 / §D11.8** — T2/T3 fallback 6-tuple / 8-tuple. X4 의 quarantine artifact 가 audit trail 보존 의무 — `logical_key` 포함.

### 3.2 약한 관련 (간접 영향)

- **ADR-008** Backfill policy — X4 의 status CLI 가 `metrics.backfill_pending_seconds` 표시 (heartbeat schema v1 field). backfill 자체 정책 변경 없음.

## 4. 외부 contract amendment — heartbeat-schema.v1.md §Related Manifest Artifacts

### 4.1 amendment scope

`docs/domain-knowledge/contracts/heartbeat-schema.v1.md` 에 신규 subsection 추가:

```markdown
## Related Manifest Artifacts (MCT-93 X4 amendment)

Active-active mismatch quarantine artifacts:

`<MCTRADER_DATA_ROOT>/market/manifest/quarantine/{tier}-{detected_at_iso}-{batch_seq}.json`

- `tier`: `"tick"` / `"orderbook"` (T1 candle 은 §D5 late correction policy 로 quarantine emit 안 함)
- `detected_at_iso`: ISO8601 UTC compact (`20260506T123456Z`), `_BackpressureLimiter` flush 시각
- `batch_seq`: per-second batch index (per-second 100 mismatch cap 의 backpressure batching 결과)
- payload: `{tier, count, records: [{logical_key, rows: [...], detected_at}]}`
- atomic write (temp → fsync → rename), append-only

`heartbeat-schema.v1.metrics.quarantine_count` 는 cumulative mismatch count (artifact file 개수와 다름 — backpressure batching 의 영향).
```

### 4.2 backward compat

heartbeat-schema.v1.metrics 의 4 field (`events_per_sec / dup_skip_count / quarantine_count / ws_reconnect_count / backfill_pending_seconds`) 모두 unchanged. 신규 subsection 만 추가 — schema 자체 변경 0, consumer 영향 0.

## 5. 요구사항 확장 해석 (Codex 6-area review fix 반영)

### 5.1 Status CLI surface (F-1 SUGGEST 채택, modified)

Codex SUGGEST: dedup ratio 표시 시 denominator (`HeartbeatMetrics.events_total` cumulative) 부재. Sonnet decider 채택 — **dedup ratio omit X4 scope** (denominator 추가는 collector daemon hot path 변경 → X4 scope 외, 후속 minor). X4 status CLI 는 cumulative `dup_skip_count` + `quarantine_count` 만 emit (ratio 없이도 "0 인가, 늘어나고 있나" 인사이트 충분).

CLI signature freeze:

```bash
mctrader-data status \
  [--root PATH]  # default: $MCTRADER_DATA_ROOT or ~/.local/share/mctrader/data
  [--fresh-yellow-seconds 10.0]
  [--fresh-red-seconds 30.0]
  [--lag-yellow-seconds 60.0]
  [--lag-red-seconds 300.0]
  [--format human|json]  # default human
```

exit code: `0` (all green) / `1` (any yellow) / `2` (any red or no heartbeat files)

### 5.2 tier_coverage node 차원 (F-2 SUGGEST 채택)

`CoverageReport` 에 신규 optional field `node_coverage: dict[str, NodeCoverage]` 추가:

```python
class NodeCoverage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    min_ts_utc: datetime | None = None
    max_ts_utc: datetime | None = None
    gaps: list[GapEntry] = Field(default_factory=list)
    collector_run_ids: list[str] = Field(default_factory=list)


class CoverageReport(BaseModel):
    # ... existing 7 fields unchanged ...
    node_coverage: dict[str, NodeCoverage] = Field(default_factory=dict)
```

backward compat: 기존 7 field signature 보존, `node_coverage` default empty dict — caller 변경 0.

### 5.3 Heartbeat-aware gap classifier (F-3 PUSH-BACK fix)

Codex PUSH-BACK: 현재 heartbeat artifact 가 latest-state-only (history 없음) 이라 "node was disconnected during gap window" 판정 불가. Sonnet decider fix:

- X4 helper 는 **conservative current-state-only**: `classify_gap(gap, heartbeats_now)` signature
- 분류:
  - `LIKELY_NODE_DOWN`: 현재 시점 *어느 한 node* 의 `heartbeat-{node_id}.json` 가 `freshness >= red_threshold` 또는 `ws_state == "disconnected"`
  - `UNKNOWN`: 위에 해당 안 됨 (heartbeat 만으로 단정 불가)
- `LIKELY_BITHUMB_OUTAGE` 분류는 **X4 미도입** (cumulative `ws_reconnect_count` 한 시점 sample 만으로 판정 불가, history ring-buffer 가 후속 minor 도착 시 추가)

이 conservative 정책으로 false positive 회피. status CLI 는 gap 발견 시 `classify_gap` 결과를 부가 정보로 표시 ("gap 700s after 2026-05-06T12:00:00Z, cause=LIKELY_NODE_DOWN (NODE_B disconnected)").

### 5.4 DedupCounterSink → HeartbeatWriter adapter (F-4 SUGGEST 채택)

Codex Option B 채택 — composition + `threading.Lock`. asyncio.Lock 거부 (dedup 호출 caller 가 sync, asyncio context 외부에서도 호출 가능):

```python
class HeartbeatCounterSink:
    """DedupCounterSink Protocol concrete impl, wrapping HeartbeatWriter.

    Cross-thread safe: dedup runs sync in scan caller thread,
    heartbeat run loop runs in collector asyncio event loop.
    threading.Lock chosen (not asyncio.Lock) for sync-context support.
    """
    def __init__(self, writer: HeartbeatWriter):
        self._writer = writer
        self._lock = threading.Lock()

    def increment_dup_skip(self, n: int = 1) -> None:
        with self._lock:
            self._writer.metrics.dup_skip_count += n

    def increment_quarantine(self, n: int = 1) -> None:
        with self._lock:
            self._writer.metrics.quarantine_count += n
```

X4 collector daemon 측 wiring (`MultiSymbolCollector` 또는 `CollectorDaemon`) 은 X3 와 동일 — sink 객체 생성하여 dedup 호출 site 에 주입. **이 wiring 자체는 X4 scope** — collector 가 dedup 을 호출하는 site 가 현재 없으므로 (X3 의 dedup 은 read-side scan caller 에서만 호출), X4 는 단지 **adapter class 만 freeze** 하고 실제 wiring 은 X6 (web panel 의 read-call) 또는 후속 collector daemon 변경에서 사용.

### 5.5 Quarantine artifact persistence (F-5 ADOPT-AS-IS 채택)

`dedup.persist_quarantine_records(root, records)` 신규 helper:

```python
def persist_quarantine_records(
    root: Path | str,
    records: list[QuarantineRecord],
) -> list[Path]:
    """Atomic write quarantine artifacts under <root>/market/manifest/quarantine/.

    Path format: {tier}-{detected_at_iso}-{batch_seq}.json
    - tier: records[0].tier (모두 동일 batch 가정)
    - detected_at_iso: records[0].detected_at, ISO compact (e.g. 20260506T123456Z)
    - batch_seq: 0-padded 6-digit seq, file collision 방지 (mkstemp suffix)

    Atomic: temp → fsync → os.replace. Append-only (existing 파일 덮어쓰지 않음).

    Returns: written file paths.
    """
```

caller (X3 scan_ticks / scan_orderbook_events) 는 `DedupResult.quarantine_records` 를 받아 helper 호출. dedup module 의 pure-function 성격 유지 (I/O 침투 0).

### 5.6 후속 escalation (X4 scope 외)

- **heartbeat history ring-buffer**: `<root>/market/manifest/heartbeat-{node_id}-history.jsonl` (append-only, 1h window). full gap classifier 알고리즘 (LIKELY_BITHUMB_OUTAGE / dual-node window correlation) 의 prerequisite.
- **`HeartbeatMetrics.events_total` cumulative**: dedup ratio denominator. collector daemon hot path 변경 — `MultiSymbolCollector._handle_event` 에 counter increment 추가.
- 둘 다 X4 종료 후 후속 minor 또는 X6 web panel observability 단계에서 도입 검토.

## 6. 외부 지식 배경 (이미 Phase 1 / X2 / X3 에서 freeze 된 항목 재인용 only — 신규 외부 지식 없음)

### 6.1 POSIX `rename(2)` atomic — heartbeat write 와 동일 패턴

quarantine artifact write 도 `temp → fsync → os.replace` 사용. NFS / SMB / Ceph 의 same-directory atomic rename 보장. Phase 1 spec §3.4 + heartbeat-schema.v1.md §"Write 규약" 에서 freeze.

### 6.2 Click `--format` choice + `sys.exit` exit code

Click 의 `click.Choice(["human","json"])` + `sys.exit(0/1/2)` 패턴은 mctrader-data 의 `backfill` subcommand 에서 이미 사용 중 (cli.py:181). status subcommand 는 동일 패턴 따름.

### 6.3 `threading.Lock` vs `asyncio.Lock` 선택 근거

`HeartbeatWriter.run()` 은 collector asyncio event loop 의 task. `DedupCounterSink` callers 는 `scan_ticks` / `scan_orderbook_events` Generator 호출 site (sync). Python `asyncio.Lock` 은 같은 event loop 내에서만 안전 — sync caller 가 acquire 하면 deadlock 위험. `threading.Lock` 은 sync caller / async task 양쪽에서 contention-free acquire.

### 6.4 Pydantic v2 `extra="forbid"` + default_factory

`CoverageReport.node_coverage: dict[str, NodeCoverage] = Field(default_factory=dict)` 는 backward compat 보장 (기존 caller 가 `node_coverage` 인자 안 넘겨도 OK). `extra="forbid"` 는 unknown field rejection — caller 가 typo 한 field 도착 시 ValidationError.

## 7. 설계 서사

(Phase 4 plan: `docs/superpowers/plans/2026-05-06-collector-ha-phase-4.md` 에서 freeze)

핵심 invariant:

- X4 는 read-only diagnostic surface (writer path 영향 0)
- ADR-009 추가 amendment 없음
- heartbeat-schema.v1.md §Related Manifest Artifacts subsection 만 amendment
- backward compat: CoverageReport 기존 7 field / heartbeat schema 4 metric / dedup module signature 모두 보존

architecture diagram + step-by-step TDD plan 모두 plan doc 참조:

- [`docs/superpowers/plans/2026-05-06-collector-ha-phase-4.md`](../superpowers/plans/2026-05-06-collector-ha-phase-4.md)

## 8. 개발 서사

### 8.1 구현 PR

- **mctrader-data PR #10** (MERGED, 2026-05-06) — `[MCT-93] feat(ha): Status CLI + Coverage Node Breakdown + Heartbeat Sink Adapter (X4 of MCT-89, mctrader-data 0.8.0)`
- **mctrader-hub PR #102** (MERGED, 2026-05-06) — Story §1-7 + Phase 4 plan + heartbeat-schema.v1.md `§Related Manifest Artifacts` amendment

### 8.2 mctrader-data 0.7.0 → 0.8.0 변경 surface

| Module | 변경 | LOC |
|---|---|---|
| `dedup.py` | `persist_quarantine_records` helper + `_serialize_value` (atomic O_EXCL seq + per-writer unique temp + Decimal/datetime str fallback) | +75 |
| `heartbeat.py` | `HeartbeatCounterSink` class (composition + threading.Lock) | +25 |
| `orderbook_replay.py` | `NodeCoverage` Pydantic submodel + `CoverageReport.node_coverage` field + `tier_coverage` per-node ts envelope | +60 |
| `diagnostic.py` (NEW) | `classify_gap` + `GapCause` (StrEnum, conservative current-state-only) | +57 |
| `cli.py` | `status` subcommand (`--format human\|json` + threshold flags + exit code 0/1/2) | +110 |
| Tests (5 new) | persist_quarantine (8) / heartbeat_sink (5) / diagnostic (6) / cli_status (10) / node_coverage (5) = 34 new | +650 |

### 8.3 Codex 2-tier review (Phase 4 design + implementation)

#### Phase 4 design review (6/6 ADOPT, escalation 0)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 status CLI surface | SUGGEST | 채택 (modified, dedup ratio omit X4) |
| F-2 tier_coverage breakdown | SUGGEST | 채택 (NodeCoverage Pydantic + default_factory=dict) |
| F-3 heartbeat-aware gap | PUSH-BACK | conservative current-state-only fix (history ring-buffer 후속) |
| F-4 sink adapter | SUGGEST | 채택 (Option B composition + threading.Lock) |
| F-5 quarantine persist | ADOPT-AS-IS | 채택 (persist_quarantine_records helper) |
| F-6 contract amendment | SUGGEST | 채택 (heartbeat-schema.v1.md §Related Manifest Artifacts) |

#### Implementation review (5/6 ADOPT, 1 PUSH-BACK fix 적용)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 code quality | SUGGEST | 채택 — exception narrowing (OSError / json.JSONDecodeError / pa.ArrowException) |
| F-2 contract enforcement | ADOPT-AS-IS | — |
| F-3 test coverage | SUGGEST | 채택 — concurrent / no_temp_residue / lag_yellow / malformed_json / direct_construction tests 추가 |
| F-4 backward compat | ADOPT-AS-IS | — |
| **F-5 cross-thread safety** | **PUSH-BACK** | **fix 적용** — atomic O_EXCL seq allocation + per-writer unique temp suffix (pid + tid + monotonic_ns) |
| F-6 scope creep | ADOPT-AS-IS | — |

총 escalation 0 (디자인 + 구현 12/12 in-Phase 채택). 후속 minor: heartbeat history ring-buffer / `HeartbeatMetrics.events_total` cumulative.

## 9. 품질 게이트 이력

| Gate | Result | Evidence |
|---|---|---|
| Codex Phase 4 design 6/6 review | ADOPT 합 (escalation 0) | Story §3 Codex review summary table + plan §0 |
| Codex implementation 6/6 review | ADOPT 5 + PUSH-BACK 1 fix 적용 | F-5 atomic O_EXCL fix + concurrent test 채택 |
| 신규 contract amendment | heartbeat-schema.v1.md `§Related Manifest Artifacts` (PR #102) | additive only, schema_version unchanged |
| pytest mctrader-data | **182 PASS** (148 prior + 34 new) | regression 0 vs 0.7.0 |
| ruff lint | clean | F-1 narrow exception 적용 후 |
| Backward compatibility | 100% | CoverageReport 기존 7 field + dedup public API + heartbeat schema field 모두 보존 |
| Concurrent shared-storage safety | proven | test_persist_quarantine_records_concurrent_no_collision (10-thread × 1 record = 10 distinct artifacts, 0 .tmp residue) |

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

*(FIX 발생 시 append)*

## 11. 회고

### 11.1 Phase 4 종료 marker (2026-05-06)

X4 deliverable 5개 (status CLI + node_coverage + classify_gap + HeartbeatCounterSink + persist_quarantine_records) 모두 main merged. 사용자 원래 요구사항 ("코드 수정사항 배포 + 2개 이상 Active Node 관리 + 데이터 순단을 줄이고자") 의 *diagnostic surface* 가 노출되어, 양 node 의 freshness/lag/dedup metric 이 CLI 한 줄 (`mctrader-data status`) 로 관찰 가능.

### 11.2 X4 기술 부채 surface (후속 Phase 또는 minor)

- **heartbeat history ring-buffer**: `classify_gap` 이 `LIKELY_BITHUMB_OUTAGE` 분류를 활성화하려면 양 node의 ws_reconnect_count delta 비교 필요 — 현재 single sample 구조에서 불가. 후속 minor에서 `<root>/market/manifest/heartbeat-{node_id}-history.jsonl` append-only 1h window 추가 검토.
- **`HeartbeatMetrics.events_total` cumulative**: dedup ratio denominator 부재. collector daemon hot path 에 `_handle_event` counter increment 추가 필요. 후속 minor.
- **Streamlit 00_status panel** (X6): `mctrader-data status --format json` output 을 consume 하는 web UI. mctrader-web 측 별도 PR 예정.

### 11.3 Epic MCT-89 진행도 (X4 종료 시점)

| Phase | Story | 상태 |
|---|---|---|
| 1 | MCT-89 (Epic) | CLOSED ✅ |
| 2 | MCT-91 (X2) | MERGED ✅ |
| 3 | MCT-92 (X3) | MERGED ✅ |
| **4** | **MCT-93 (X4)** | **MERGED ✅ (이번 Phase)** |
| 5 | (X5 mctrader-hub `scripts/ha/`) | PENDING |
| 6 | (X6 mctrader-web `00_status` panel) | PENDING |
| 7 | (X7 Calibration C1/C2 + 양 node 30분 E2E demo) | PENDING |

### 11.4 X4 의 단일 가치 한 줄

X4 = X3 가 freeze 한 measurable hook 의 **사용자 visible surface** 도입. 데이터 순단 0 의 *발생 여부* 를 사용자가 처음으로 능동 확인 가능하게 됨. (active-active mismatch quarantine artifact 도 root manifest tree 에 appendix 형태로 누적)
