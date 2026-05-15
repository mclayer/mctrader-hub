# EPIC-data-domain-decoupling — Design Spec

> Brainstorm session: 2026-05-16 · codeforge-brainstorm (Phase 0 deep-verify + Codex review) · Opus 4.7
> Status: 설계 확정 (Phase 1 dialog 합의 + Phase 2 PMO 분해 완료) → writing-plans 진입
> scope_manifest: `scope_manifests/EPIC-data-domain-decoupling.yaml` (7 Story MCT-182~188 RESERVED)

## 1. 문제 정의 (why-first)

사용자 원문: "data 영역은 mctrader와 아예 분리하고 싶다. 표준 mctrader에는 호출용 interface, data에는 그를 처리하는 REST API가 있는게 좋겠다. 프로젝트 구조는 mctrader-hub에서도 구현할 수 있고 mctrader-data 단독으로도 필요사항을 반영할 수 있어야겠다."

### 추출된 동기 (확정)

| why | 내용 |
|---|---|
| 코드 결합도 감소 | engine 이 `mctrader_data` 내부 모듈을 직접 import 하는 구조를 끊고 안정된 계약 표면으로만 통신 |
| 독립 배포·버전 관리 | data 를 engine 릴리스와 무관하게 배포/롤백/스케일 |
| 외부·다중 consumer | engine 외 시스템도 data 를 표준 API 로 호출 |
| 다중거래소 확장 | market 이 bithumb 외 upbit/해외/한국거래소로 분화 — 신규 거래소 추가가 **data 단독 변경**으로 끝나야 함 (사용자 핵심 지시) |

### 사용자 확정 결정 (Phase 1 dialog)

- **β 채택**: engine 을 진짜 data-free 로. Read 도메인 전체(tier_reader/reader_cache/DR/NAS client/parquet)를 mctrader-data 로 이전. engine = 얇은 client. ("hot path in-proc 유지" 타협안 명시 거부.)
- **engine→market(core) 도 직접 의존 끊기 + market 은 data 에만 의존**: 검증 결과 교정 — market(core)은 data 영역이 아니라 플랫폼 도메인 어휘(engine 50+곳 의존, DAG 최하위). engine→market 은 *어휘* 의존이라 정상·불가피. 진짜 분리 대상이던 data-storage/거래소-어댑터 결합만 제거.
- **다중거래소 확장성 반영해 4-layer 재설계** + **전체 종착점 1 Epic, 단계적 sequential Story**.

## 2. Phase 0 deep-verify 사실 (모두 file:line 근거, verified-via)

1. **`CandleModel`은 이미 `mctrader_market.candle`에 존재.** engine 의 `from mctrader_data.cold.duckdb_resample import CandleModel`(**실측 4곳** — backtest/data_source.py:17, consumers/candle_view.py:33, consumers/signal_provenance_log.py:31, paper/data_source.py:22; brainstorm 가설 5곳은 candle_view.py:38 docstring 오집계, MCT-182 요구사항 lane 정정 2026-05-16)은 단순 경로 re-export → 추출 0, 경로 재지정만. (engine 2곳 reconciliation/strategy_reproducibility.py:40 + realtime/aggregator.py:9 은 이미 mctrader_market.candle 직독 — D1 방향 부분 선진행 정합.)
2. **`mctrader_data.aggregation`은 PURE-CONTRACT.** `mctrader_data.*` import 0. 의존은 `mctrader_market.{information_bar,tick,types}` + stdlib 뿐 → market 이전 시 data 결합 전파 없음.
3. **`paper_lineage`(PaperLineage/canonical_jsonl_hash)도 PURE-CONTRACT.** stdlib+pydantic+`mctrader_market.types` 뿐.
4. **`TickRecord`/`OrderbookEventRecord` = MIXED.** dataclass 자체는 순수(stdlib) 이나 pyarrow import 모듈(`tick_storage.py`/`orderbook_storage.py`)에 동거 → **dataclass만 추출**(모듈 이동 아님).
5. **engine `io/` NAS reader 6 module(tier_reader/reader_cache/endpoint_router/dr_mode/cold_reader/l1_reader)은 engine `src/` 호출자 0** (테스트 `tests/io/`만). MCT-170 자산이 production 미배선(dead-in-prod). engine 실제 cold-read = `mctrader_data.storage.scan_candles`/`orderbook_replay`/`path.resolve_data_root` 직독.
6. **`mctrader-market`는 `mctrader_data`를 어디서도 import 안 함, pyproject 의존 0** → market↔data 순환 0, market = DAG 최하위 FOUNDATION.
7. **market 에 이미 exchange-neutral Protocol 존재** (`providers.py` `CandleProvider`/`OrderBookProvider` `@runtime_checkable`). **`mctrader-market-upbit`(v0.1.0) 존재**. **data `adapters.py`가 이미 다중거래소 ingestion 팩토리** (Bithumb/Upbit CandleProvider+WS) — 다중거래소 어댑터 패턴 가동 중.
8. **engine→market 표면 ~50+곳** (CandleModel/CandleLike 전략·지표 25+, types Symbol/Timeframe/Decimal38_18 거의 전 모듈, order/lifecycle, information_bar/tick) — data 결합이 아니라 플랫폼 어휘. **`mctrader-market-bithumb` 자체가 `mctrader-market`에 의존** (engine realtime WS 경로).

## 3. AS-IS 의존 그래프 (검증)

```
engine ──pyproject git@main(whole pkg)──▶ data ──git@main──▶ market
   │                                                          ▲
   ├── market(어휘 ~50곳) ────────────────────────────────────┤
   └── mctrader_market_bithumb (realtime WS 직접 ~5곳) ───────▶ market

 engine→data import 줄: CandleModel×4(market re-export, verified 2026-05-16) / aggregation algo×1(PURE) /
   TickRecord×2·OrderbookEventRecord×1(순수 dataclass) / storage.scan_candles+path×3(STORAGE) /
   orderbook_replay scan+_partition_dir×2(STORAGE) / paper_lineage×1(PURE) /
   paper_storage.write_paper_candles×1·nas_uploader×1(STORAGE 역방향 write)
 engine io/ : stdlib-only, mctrader_data 0, engine src/ caller 0 → 미배선
 문제: ① engine→data(python) ② engine→bithumb(realtime WS 직접) → 새 거래소마다 engine 수정
```

## 4. TO-BE 의존 그래프 (4-Layer, 다중거래소 확장)

```
 Layer 0 ─ mctrader-market (FOUNDATION, 의존 0, 순수 pydantic/sqlalchemy, data 비의존)
   • 도메인 어휘: Symbol·Timeframe·Decimal38_18·UTCDateTime·OrderStatus·lifecycle
   • wire contract: TickRowV1_1·InformationBarModel·CandleModel/CandleLike·OrderBookLike
   • exchange-neutral Protocol: CandleProvider·OrderBookProvider(기존) + (신규)RealtimeStream
   • ◀ RELOCATE: aggregation algo + TickRecord/OrderbookEventRecord dataclass + PaperLineage
        ▲                        ▲                         ▲                    ▲
 Layer 1 ─ 거래소 어댑터 (각각 → market 만, market Protocol 구현)
   mctrader-market-bithumb · mctrader-market-upbit · -<해외> · -<한국거래소> ... (무한 확장)
        ▲                        ▲   ▲   ▲ (등록은 data adapters.py 한 곳)
 Layer 2 ─ mctrader-data (DATA-STORAGE 영역 단독 소유, → market + → 어댑터들)
   • adapters.py 팩토리: 모든 거래소 ingestion 단일 경계 (신규 거래소 = 여기만 등록)
   • 정규화: 거래소별 raw → TickRowV1_1 SSOT
   • storage: scan_candles·orderbook_replay·NAS·parquet + io reader(engine서 이전)
   • NEW api/(FastAPI): /v1 historical(Arrow IPC) + 역방향 POST + 실시간 정규화 stream(Redis Stream)
        ▲ 런타임 REST/stream (python import 아님)
 Layer 2'─ mctrader-engine (PURE CONSUMER)
   • mctrader_data = 0 (pyproject 제거)
   • mctrader_market_bithumb/upbit/* = 0 (어댑터 직접 의존 제거)
   • 의존 = Layer 0(market 어휘/contract/algo) + data /v1(REST historical + 정규화 실시간 stream)
   • data_client/ : historical fetch + realtime subscribe (거래소 무관)

 핵심 확장성 불변식 (D5): 새 거래소 추가 = ① 신규 Layer1 어댑터 repo ② data adapters.py 등록
   ③ data 수집/정규화 설정 → engine 변경 0, market-core 변경 0, ADR 0
 순환: 영원히 없음 (market→누구도 의존 안 함, data→market+어댑터, engine→market+REST)
```

## 5. 확정 설계 결정 D1–D7

| D | 결정 | option | owner Story |
|---|---|---|---|
| D1 | Contract relocation → mctrader-market (Layer 0) | relocate-to-market-core | MCT-182 |
| D2 | Read 도메인 relocation → mctrader-data (Layer 2) | io-relocate + cold-read-behind-REST | MCT-183 + MCT-185 |
| D3 | data REST API 신규 — historical + reverse-write + realtime stream | fastapi-v1 + redis-stream | MCT-184 + MCT-185 |
| D4 | engine exchange-adapter 제거 | subscribe-normalized-stream | MCT-186 |
| D5 | 다중거래소 확장 불변식 | data-only-extension-invariant | MCT-187 |
| D6 | ADR-031 신규 + ADR-029/027/030 amendment | new-adr-031 + 3-amend | MCT-182 + MCT-188 |
| D7 | data-free done-criterion (grep0 quad gate) | ci-grep0-quad-gate | MCT-188 |

### Codex 리뷰 합성 (채택/기각)

- **채택**: D1 contract 별도 위치 추출, D2 io relocate, D6 strangler-fig 7 Story(Codex 5 → 검증 후 7), D7 grep0 gate, OpenAPI SSOT + hub governance snapshot, ADR-031 신규 + 3 amend.
- **기각 1 — presigned NAS handoff (Codex D3/D5 권장)**: "code import만 0" 으로 data-free 재정의 → engine 이 NAS 객체 레이아웃·parquet·tier·DR 지식 보유 잔존. 사용자 의도("데이터 전부 제거" + 외부 consumer) + β 위반. 검증상 io/ 미배선 + 실시간 hot-path data 비의존(거래소 WS) + ADR-030 single-host loopback → presigned 가 풀려던 성능 문제 비실재. **Arrow IPC over REST** 채택.
- **기각 2 — 신규 중립 repo 2개 (bar-core/contract-types, Codex D1/D2 권장)**: 검증상 contract 코드가 모두 PURE(market+stdlib) → market 통합 시 결합 전파 없음. 신규 CI/cross-repo lock 2개 불필요.
- **교정 — market 통합 → market(core) = 플랫폼 어휘**: 사용자 "market 도 끊어야" 직관 검증 → market 은 DAG 최하위 FOUNDATION, engine→market 은 어휘 의존(50+곳)이라 정상·불가피. 진짜 분리 대상(data-storage/거래소-어댑터)만 제거. 4-layer 재설계로 수렴.

## 6. Story 분해 (7, sequential strangler-fig)

| phase | Story | 제목 | D | repos | land_order |
|---|---|---|---|---|---|
| 1 | MCT-182 | Layer0 contract relocation → market | D1,D6 | hub→market→data→engine | hub P1→market→data→engine→hub P2 |
| 2 | MCT-183 | Layer2 read 도메인 relocation → data | D2,D6 | hub→data→engine | hub P1→data→engine→hub P2 |
| 3 | MCT-184 | data REST API 신규(historical+reverse-write) | D3,D6 | hub→data | hub P1→data→hub P2 |
| 4 | MCT-185 | realtime stream + engine thin client + cold-read cutover | D2,D3 | hub→data→engine | hub P1→data→engine→hub P2 |
| 5 | MCT-186 | engine realtime cutover + adapter 제거 | D4 | hub→engine→(bithumb/upbit opt) | hub P1→engine→hub P2 |
| 6 | MCT-187 | 다중거래소 확장 불변식 박제 | D5,D6 | hub→data | hub P1→data→hub P2 |
| 7 | MCT-188 | data-free grep0 quad gate + Epic POLICY_FINALIZED | D7,D6 | hub→engine | hub P1→engine→hub P2 |

## 7. 위험

- **R1 (HIGH) — cross-repo contract/Phase0 desync 7회째**: docker-stack 6회 누적 + 본 Epic 은 subtractive/relocate 라 위험 ↑. 완화 = Story별 Phase 0 deep-verify 독립 게이트 강제 + ADR-031 D-row ↔ scope_manifest 전수 1:1 reconcile (MCT-179 lesson reapply).
- **R2 (HIGH) — MCT-41 Live Mode Debut 블락**: MCT-186 engine realtime cutover 가 live mode WS/주문 경로 모듈 공유 가능. 완화 = MCT-182~185 파일 disjoint 병렬 안전, MCT-186 진입 전 Phase 0 에서 MCT-43~47 IN_PROGRESS 파일 교차 검증 의무 → 공유 시 land_order 재조정 or sub-Story 분리 (Orchestrator ordering 결정).

## 8. scope_manifest

전체 분해/planned_files/planned_adrs/risks/story_sequence 는 `scope_manifests/EPIC-data-domain-decoupling.yaml` 박제 (Phase 1 PR Issue body 첨부용). counters.json MCT-182~188 + ADR-031 RESERVED 완료.
