---
story_key: MCT-65
status: phase:완료
component: data
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-009
---

# MCT-65: Forward-only collector daemon (RETROACTIVE SEAL)

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

mctrader-data PR #4 (commit 9f51fa0, label `[MCT-58]` stale) 의 retroactive sealing. Hub PR #74 (4664a4e, 22:31 KST) 가 WFO Execution Epic 으로 MCT-58 점유 → 본 Story = canonical Hub issue 로 collector daemon 구현 history sealing. MCT-12 retroactive sealing 패턴 동일.

## 2. 도메인 해석

MCT-63 child #2 = **이미 구현된 작업의 doc 기록**. 코드는 mctrader-data 0.4.0 에 merge 완료, 본 Story 는:

- 충돌 매핑표 (stale 라벨 ↔ canonical issue) 명시
- evidence file inventory inline (PR# / commit / 파일 / 테스트)
- F-21 추가 작업: collector run 마다 symbol manifest persist (replay reproducibility)

## 3. 충돌 매핑표 (Codex F-6 + F-20)

| | Stale | Canonical |
|---|---|---|
| Hub Story file | (none) | `docs/stories/MCT-65.md` (본 file) |
| Commit label | `[MCT-58]` | `MCT-65` |
| Commit hash | `9f51fa0` (mctrader-data) | (변경 없음) |
| PR# | mctrader-data#4 | (변경 없음) |
| WFO Epic 의 MCT-58 | `docs/stories/MCT-58.md` (OOS evaluator, MCT-55 child) | (별개, 본 Story 와 무관) |

**원인**: MCT-63 Phase 1 doc PR 진행 시점 (2026-05-04 22:30+ KST) 에 `MCT-58.md` 가 WFO Execution Epic 의 child 로 이미 존재 (Hub PR #74 = 22:31 KST, 본 PR 커밋 라벨 결정 = 22:28 KST, 3분 차이로 충돌). 사용자 사전 지시 "MCT-56으로 바꿔" 는 stale (MCT-56 도 WFO Epic 이 점유). 현재 rename 가능한 다음 free 번호 = MCT-63+.

**해결**: 커밋 history 변경 안 함 (admin merge 후 immutable). MCT-65 retroactive seal 로 사실 기록.

## 4. 관련 코드 경로 (mctrader-data PR #4 evidence inventory)

```
mctrader-data/src/mctrader_data/
├── tick_storage.py          (NEW — TickWriter, 185 line)
├── orderbook_storage.py     (NEW — OrderbookWriter, 210 line)
├── collector.py             (NEW — CollectorDaemon + MultiSymbolCollector + fetch_top_n_krw_symbols)
└── cli.py                   (MODIFY — `collect` command 추가)

mctrader-data/tests/
├── test_tick_storage.py            (NEW — 6 case)
├── test_orderbook_storage.py       (NEW — 6 case)
└── test_collector.py               (NEW — 5 case)

mctrader-data/deploy/
├── mctrader-collector.service      (NEW — systemd unit)
└── README.md                       (NEW — Linux ops runbook)
```

## 5. Schema (이미 sealed, ADR-009 §D10 / §D11 amendment 에서 정식 등재)

### tick.v1 (8 column)

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[ns, UTC] | no | 거래소 발생 시각 |
| received_at | timestamp[ns, UTC] | no | collector 도착 시각 (= available_from_ts) |
| exchange | string | no | "bithumb" |
| symbol | string | no | "KRW-BTC" |
| price | decimal128(38, 18) | no | trade price |
| quantity | decimal128(38, 18) | no | trade quantity |
| side | string | no | "buy" / "sell" |
| raw_json | string | yes | original WS frame for debug |

Hive partition: `market/ticks/schema_version=tick.v1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/part-{collector_run_id}.parquet`

### orderbook.v1 (10 column, flat events)

| Column | Type | Nullable | 의미 |
|---|---|---|---|
| ts_utc | timestamp[ns, UTC] | no | 거래소 발생 시각 |
| received_at | timestamp[ns, UTC] | no | collector 도착 시각 (= available_from_ts) |
| exchange | string | no | "bithumb" |
| symbol | string | no | "KRW-BTC" |
| event_type | string | no | "snapshot" / "delta" |
| side | string | no | "bid" / "ask" |
| level | int32 | no | 0..N-1 (snapshot) / -1 (delta) |
| price | decimal128(38, 18) | no | level price |
| quantity | decimal128(38, 18) | no | level quantity (delta 0 = remove) |
| raw_json | string | yes | original WS frame |

Hive partition: `market/orderbook/schema_version=orderbook.v1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/part-{collector_run_id}.parquet`

## 6. 추가 요구사항 (RETROACTIVE — F-21 symbol manifest)

기존 PR #4 이 누락한 1건 추가:

1. **`manifest.json` per collector run** — collector startup 시 `<root>/market/manifest/run-{collector_run_id}.json` 작성. content:
   ```json
   {
     "collector_run_id": "...",
     "started_at_utc": "...",
     "exchange": "bithumb",
     "selected_symbols": ["KRW-BTC", "KRW-ETH", ...],
     "channels": ["transaction", "orderbookdepth"],
     "selection_method": "top_n_volume" | "explicit",
     "top_n": 10 | null
   }
   ```
2. **단위 테스트 추가** — manifest 파일 작성 verify, JSON schema strict (Pydantic v2).
3. **버전 bump**: mctrader-data 0.4.0 → 0.4.1 (patch — additive manifest 만).
4. **MCT-66 (reconstruction) 가 manifest 의무 참조** — coverage report 의 `symbol_manifests` field 채움.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: collector = public WS data only, no order placement. systemd sandbox (PR #4 의 unit file) 유지. manifest = read-only 파일.
- **신규 file**: `mctrader-data/tests/test_collector_manifest.py` (1 case) + `manifest.json` runtime artifact.
- **수정 file**: `collector.py` (manifest write — 약 20 LOC). 버전 bump.
- **Reversible**: yes (manifest = additive, 미존재 시 MCT-66 측 None tolerant — Phase 2 설계 시 결정).

## 8. Sealing 검증 (Phase 1 doc 단계)

| # | Check | 결과 |
|---|---|---|
| S1 | mctrader-data PR #4 admin merged | 9f51fa0 (2026-05-04 22:28 KST) |
| S2 | CI green (ubuntu + windows lane) | yes (3 iter 후 final green) |
| S3 | 17 unit test pass | yes |
| S4 | systemd unit file present | yes (`deploy/mctrader-collector.service`) |
| S5 | Linux deployment 사용자 manual | 추후 (사용자 요청: "가동은 추후 하도록 하고") |
| S6 | manifest 추가 (본 Story 의 신규 작업) | Phase 2 PR (MCT-65 작업분) 에서 수행 |
