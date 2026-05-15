# ADR-031: Data Domain Decoupling — 4-Layer 다중거래소 확장 아키텍처 (engine = data-free + exchange-agnostic pure consumer)

## Status

**Proposed** (MCT-182 Phase 1 진입, 2026-05-16)

상태 transition (예정): Proposed (MCT-182 Phase 1) → Accepted (MCT-182 LAND — D1 contract relocation VERIFIED) → POLICY_FINALIZED (MCT-188 LAND — EPIC-data-domain-decoupling 7/7 COMPLETED, D1-D7 전수 VERIFIED + ADR-029/027/030 amend confirm)

> **본 ADR scope (D6 = ADR meta-decision)**: ADR-031 은 EPIC-data-domain-decoupling 의 4-Layer
> 의존 모델 + 7 결정(D1-D7)을 박제한다. MCT-182(본 Story)는 **D1(contract relocation) 실 LAND
> + D6(ADR-031 publish Proposed)** 만 수행한다. D2-D5/D7 은 후속 Story(MCT-183~188) owner —
> 본 ADR 에 결정 record 만 박제하고 실 구현·amendment 는 owner Story 가 수행한다 (Out-of-scope
> 표 명시). ADR-029/027/030 의 amendment 는 본 ADR 의 **예고 box** 로만 존재 — 실 amend 는
> 후속 owner Story (MCT-183/184/185/186/188) 가 수행.

## Context

`mctrader-engine` 이 `mctrader_data` 내부 모듈을 python 으로 직접 import 한다 (engine→data
14 import 줄). 사용자 지시: *"data 영역은 mctrader와 아예 분리하고 싶다. 표준 mctrader에는
호출용 interface, data에는 그를 처리하는 REST API가 있는게 좋겠다. 프로젝트 구조는
mctrader-hub에서도 구현할 수 있고 mctrader-data 단독으로도 필요사항을 반영할 수 있어야겠다."*

추출된 동기 4종:

| why | 내용 |
|---|---|
| 코드 결합도 감소 | engine 이 `mctrader_data` 내부 모듈을 직접 import 하는 구조를 끊고 안정된 계약 표면으로만 통신 |
| 독립 배포·버전 관리 | data 를 engine 릴리스와 무관하게 배포/롤백/스케일 |
| 외부·다중 consumer | engine 외 시스템도 data 를 표준 API 로 호출 |
| 다중거래소 확장 | 신규 거래소 추가가 **data 단독 변경**으로 끝나야 함 (사용자 핵심 지시) |

### Phase 0 deep-verify 사실 (모두 file:line 근거, verified-via — brainstorm + MCT-182 요구사항/설계 lane 재검증 2026-05-16)

1. **`CandleModel` 은 이미 `mctrader_market.candle` 에 존재** (`candle.py:60` `class CandleModel(BaseModel)`
   + `candle.py:67` `ConfigDict(strict=True, frozen=True, arbitrary_types_allowed=True)`). engine 의
   `from mctrader_data.cold.duckdb_resample import CandleModel` = **실측 4곳** (backtest/data_source.py:17,
   consumers/candle_view.py:33, consumers/signal_provenance_log.py:31, paper/data_source.py:22).
   brainstorm 가설 5곳은 candle_view.py:38 docstring 오집계 — MCT-182 정정. engine 2곳
   (reconciliation/strategy_reproducibility.py:40, realtime/aggregator.py:9) 은 이미
   `mctrader_market.candle` 직독 (D1 방향 부분 선진행, 무변경).
2. **`mctrader_data.aggregation` 은 PURE-CONTRACT** — 외부 의존 = `mctrader_market.{protocols.information_bar,
   schemas.tick, types}` + stdlib 뿐 (`mctrader_data.*` = self-package 내부 참조만). public API 8 심볼
   (`__init__.py:35-44` `__all__`).
3. **`paper_lineage` (`PaperLineage`/`canonical_jsonl_hash`) 도 PURE-CONTRACT** — stdlib(hashlib/json)
   + pydantic + `mctrader_market.types.UTCDateTime` 뿐.
4. **`TickRecord`(tick_storage.py:51)/`OrderbookEventRecord`(orderbook_storage.py:58) = MIXED** —
   dataclass 본문은 stdlib only (`__post_init__` float-guard) 이나 pyarrow import 모듈에 동거
   (tick:32-33, ob:38-39 모듈 레벨) → **dataclass만 추출** (모듈 이동 아님).
5. **engine `io/` NAS reader 6 module 은 engine `src/` 호출자 0** (dead-in-prod) — MCT-183 owner.
6. **`mctrader-market` 는 `mctrader_data` 를 어디서도 import 안 함** (`git grep mctrader_data` src/ = 0건
   + pyproject 의존 0) → market↔data 순환 영구 0, market = DAG 최하위 FOUNDATION.
7. **market 에 이미 exchange-neutral Protocol 존재** (`providers.py` `CandleProvider`/`OrderBookProvider`)
   + `mctrader-market-upbit`(v0.1.0) 존재 + data `adapters.py` 다중거래소 ingestion 팩토리 가동.
8. **engine→market 표면 ~50+곳** (어휘 의존 — Symbol/Timeframe/Decimal38_18/CandleModel) = 데이터 결합이
   아니라 플랫폼 어휘. engine→market 은 정상·불가피.

## Decision

### §D1 Contract relocation → mctrader-market (Layer 0)

> owner: **MCT-182** (본 Story — 실 LAND)

PURE-contract 코드를 `mctrader-market` (Layer 0 FOUNDATION) 으로 물리 이전한다:

- `mctrader_data.aggregation` PURE 패키지(core/scaled_int/contract_metadata 서브모듈 + public API
  8 심볼) → `src/mctrader_market/aggregation/` 물리 이전
- `TickRecord`/`OrderbookEventRecord` **순수 dataclass 만** → `src/mctrader_market/records.py` 추출
  (pyarrow schema/Writer 는 `mctrader-data` 잔류 — dataclass 정의만 이동)
- `paper_lineage`(`PaperLineage`/`canonical_jsonl_hash`) → `src/mctrader_market/paper_lineage.py` 이전
- `CandleModel` = **재구현 0** — engine 의 `from mctrader_data.cold.duckdb_resample import CandleModel`
  실측 4곳을 `from mctrader_market.candle import CandleModel` 로 경로 재지정
- `mctrader-data` 호출부 = `mctrader-market` re-export shim + `DeprecationWarning` (무중단 back-compat —
  shim 경유 객체가 market 객체와 `is` 동일성 보존, SSOT 단일)

**근거**: 사실2/3/4/6 — aggregation/paper_lineage PURE + dataclass stdlib-only + market 순환 0 →
market 이전 시 data 결합 전파 0. 신규 중립 repo 2개(bar-core/contract-types) 기각 — contract 코드가
모두 PURE 라 market 통합 시 결합 전파 없음 (신규 CI/cross-repo lock 불필요).

### §D2 Read 도메인 relocation → mctrader-data (Layer 2)

> owner: **MCT-183** (io relocate) + **MCT-185** (cold-read cutover) — 본 ADR 결정 record only

engine `io/` 6 module(tier_reader/reader_cache/endpoint_router/dr_mode/cold_reader/l1_reader —
사실5 engine src caller 0, dead-in-prod) → `mctrader-data` 물리 이전. engine 실제 cold-read
(`mctrader_data.storage.scan_candles/orderbook_replay/path.resolve_data_root` 직독) → data REST
뒤로 cutover. **option: io-relocate + cold-read-behind-REST.**

### §D3 data REST API 신규 (Layer 2) — historical + reverse-write + realtime stream

> owner: **MCT-184** (historical+reverse-write) + **MCT-185** (realtime stream) — 본 ADR 결정 record only

data 에 `api/` FastAPI 신규. `/v1` = historical(Arrow IPC streaming) + 역방향 write POST
(paper-candles/backtest-artifact) + 실시간 정규화 stream(Redis Stream). OpenAPI SSOT = data repo
소유, engine = thin/generated client(`mctrader_engine/data_client/`). hub governance = schema
snapshot(`.codeforge/contracts`) + cross-repo lock gate(ADR-030 §D13 패턴 재사용).
**option: fastapi-v1 + redis-stream.**

### §D4 engine exchange-adapter 제거

> owner: **MCT-186** — 본 ADR 결정 record only

engine `mctrader_market_bithumb` 직접 import ~5곳(paper_runner/ws_wrapper/stream_consumer/fill/
mock_stream, realtime WS) 제거 → data 정규화 실시간 stream 구독 전환. engine 은 정규화
`TickRowV1_1`(market-core contract) 소비. **option: subscribe-normalized-stream.**

### §D5 다중거래소 확장 불변식

> owner: **MCT-187** — 본 ADR 결정 record only

신규 거래소 추가 = ① Layer1 어댑터 repo ② data `adapters.py` 등록(BithumbCandleProvider/
UpbitCandleProvider 팩토리 이미 존재) ③ data 수집/정규화 설정. **engine 변경 0, market-core
변경 0, ADR 0.** 사용자 첫 요구 "data 단독 반영" 의 다중거래소 일반화.
**option: data-only-extension-invariant.**

### §D6 ADR — ADR-031 신규 + ADR-029/027/030 amendment

> owner: **MCT-182** (ADR-031 publish Proposed — 본 Story) + **MCT-188** (POLICY_FINALIZED + amend confirm)

ADR-031 신규 publish(본 ADR). amendment **예고 box** 3건 (실 amend = 후속 owner Story):

| 대상 ADR | amendment 내용 | 실 amend owner | optional |
|----------|----------------|----------------|----------|
| ADR-029 (tier-promotion-single-source) | engine NAS 직독 폐기 + io reader relocated + NAS SoT 경로 data REST indirection | **MCT-183** (relocate) + **MCT-185** (cutover confirm) | false |
| ADR-027 (cold-tier-object-storage-nas-minio) | engine io/ endpoint_router + dr_mode = mctrader-data relocated (Layer2 소유) | **MCT-183** (endpoint_router/dr_mode relocate) | false |
| ADR-030 (docker-stack-governance) | compose topology — engine NAS cred drop + data api service(FastAPI) 추가 | **MCT-184** (data api service) + **MCT-186** (engine NAS cred drop) | false |

> 위 3 amendment 는 본 ADR-031 publish 시점(MCT-182)에는 **예고 box** 일 뿐 — ADR-029/027/030
> 본문은 본 Story 에서 무변경. 실 amendment commit 은 각 owner Story 가 LAND.

**option: new-adr-031 + 3-amend.** MCT-179 lesson 정합 = D-row ↔ scope_manifest §design_decisions
전수 1:1 reconcile (아래 §D-row reconcile 표).

### §D7 data-free done-criterion (grep0 quad gate)

> owner: **MCT-188** — 본 ADR 결정 record only

engine src/ `from/import mctrader_data` == 0 AND engine pyproject `mctrader-data` 제거 AND
engine src/ `mctrader_market_bithumb|upbit` == 0 AND engine pyproject 어댑터 의존 제거. CI gate
박제(MCT-172 grep0 strict 패턴 재사용). **option: ci-grep0-quad-gate.**

## 4-Layer 의존 모델 (TO-BE, spec §4 박제)

```
 Layer 0 ─ mctrader-market (FOUNDATION, 의존 0, 순수 pydantic/sqlalchemy, data 비의존)
   • 도메인 어휘: Symbol·Timeframe·Decimal38_18·UTCDateTime·OrderStatus·lifecycle
   • wire contract: TickRowV1_1·InformationBarModel·CandleModel/CandleLike·OrderBookLike
   • exchange-neutral Protocol: CandleProvider·OrderBookProvider(기존) + (신규)RealtimeStream
   • ◀ RELOCATE (MCT-182, D1): aggregation algo + TickRecord/OrderbookEventRecord dataclass + PaperLineage
        ▲                        ▲                         ▲                    ▲
 Layer 1 ─ 거래소 어댑터 (각각 → market 만, market Protocol 구현)
   mctrader-market-bithumb · mctrader-market-upbit · -<해외> · -<한국거래소> ... (무한 확장)
        ▲ (등록은 data adapters.py 한 곳)
 Layer 2 ─ mctrader-data (DATA-STORAGE 영역 단독 소유, → market + → 어댑터들)
   • adapters.py 팩토리: 모든 거래소 ingestion 단일 경계 (신규 거래소 = 여기만 등록)
   • storage: scan_candles·orderbook_replay·NAS·parquet + io reader(engine서 이전, MCT-183)
   • NEW api/(FastAPI): /v1 historical(Arrow IPC) + 역방향 POST + 정규화 stream(Redis Stream) (MCT-184/185)
        ▲ 런타임 REST/stream (python import 아님)
 Layer 2'─ mctrader-engine (PURE CONSUMER)
   • mctrader_data = 0 (pyproject 제거, MCT-188)
   • mctrader_market_bithumb/upbit/* = 0 (어댑터 직접 의존 제거, MCT-186)
   • 의존 = Layer 0(market 어휘/contract/algo) + data /v1(REST + 정규화 실시간 stream)

 핵심 확장성 불변식 (D5): 새 거래소 = ① 신규 Layer1 어댑터 repo ② data adapters.py 등록
   ③ data 수집/정규화 설정 → engine 변경 0, market-core 변경 0, ADR 0
 순환: 영원히 없음 (market→누구도 의존 안 함, data→market+어댑터, engine→market+REST)
```

## D-row ↔ scope_manifest §design_decisions 전수 1:1 reconcile (MCT-179 lesson reapply)

> docker-stack Epic 의 Phase 0 verify desync 6회 누적(MCT-170/177/178/179/180) → 본 Epic 은
> subtractive/relocate 라 위험 ↑ (R1 HIGH, 7회째). MCT-179 가 ADR-030 Out-of-scope D1-D19 전수
> reconcile 1회 투자로 MCT-180/181 연속 design P0×0 회수 실증 → 본 ADR 도 publish 시점부터
> D1-D7 ↔ scope_manifest 전수 1:1 정합 (stale 누적 사전 차단).

| D | decision | option_chosen | owner Story (scope_manifest annotated) | ADR-031 §절 | reconcile |
|---|----------|---------------|------------------------------|-------------|-----------|
| D1 | Contract relocation → mctrader-market (Layer 0) | relocate-to-market-core | MCT-182 | §D1 | ✅ 1:1 |
| D2 | Read 도메인 relocation → mctrader-data (Layer 2) | io-relocate + cold-read-behind-REST | MCT-183 (io relocate) + MCT-185 (cold-read cutover) | §D2 | ✅ 1:1 |
| D3 | data REST API 신규 — historical + reverse-write + realtime stream | fastapi-v1 + redis-stream | MCT-184 (historical+reverse-write) + MCT-185 (realtime stream) | §D3 | ✅ 1:1 |
| D4 | engine exchange-adapter 제거 | subscribe-normalized-stream | MCT-186 | §D4 | ✅ 1:1 |
| D5 | 다중거래소 확장 불변식 | data-only-extension-invariant | MCT-187 | §D5 | ✅ 1:1 |
| D6 | ADR — ADR-031 신규 + ADR-029/027/030 amendment | new-adr-031 + 3-amend | MCT-182 (ADR-031 publish) + MCT-188 (POLICY_FINALIZED + amend confirm) | §D6 | ✅ 1:1 |
| D7 | data-free done-criterion (grep0 gate) | ci-grep0-quad-gate | MCT-188 | §D7 | ✅ 1:1 |

> owner_story column = scope_manifest `design_decisions.D{N}.owner_story` 와 **byte 동일**
> (annotated 통일, F-4). option_chosen 7/7 byte 동일 (disputed_claims 정합 — owner 표기 정규화는
> reconcile verdict 무영향).

**reconcile verdict**: ADR-031 §D1-§D7 ↔ `scope_manifests/EPIC-data-domain-decoupling.yaml`
`design_decisions.D1~D7` (option_chosen / owner_story) **전수 1:1 정합** (7/7 row). MCT-179
Out-of-scope stale 사전 차단 lesson reapply.

## Out-of-scope (본 Story MCT-182 = D1+D6 실 수행만 — D2-D5/D7 = owner Story)

| 항목 | 본 Story 범위 외 사유 | owner Story |
|------|----------------------|-------------|
| engine `io/` 6 module relocate → data | Layer2 read 도메인 (D2) — Layer0 contract 안정화 후 | **MCT-183** |
| data REST API(`api/` FastAPI) 신설 | D3 — REST boundary 신설은 contract relocate 완료 후 | **MCT-184** |
| realtime stream + engine thin client + cold-read cutover | D2/D3 — REST 신설 전제 | **MCT-185** |
| engine `mctrader_market_bithumb` 어댑터 직접 import ~5곳 제거 | D4 — engine realtime cutover | **MCT-186** |
| 다중거래소 확장 불변식 박제(`add-new-exchange.md` + adapters.py invariant test) | D5 | **MCT-187** |
| data-free grep0 quad gate CI + engine pyproject `mctrader-data` 의존 제거 | D7 — finalize | **MCT-188** |
| ADR-029/027/030 **실 amendment** | 본 Story 는 ADR-031 publish + amendment **예고 box** only | **MCT-183/184/185/186/188** |

## Codex 리뷰 합성 (채택/기각 박제)

- **채택**: D1 contract 별도 위치 추출, D2 io relocate, strangler-fig 7 Story(Codex 5 → 검증 후 7),
  D7 grep0 quad gate, OpenAPI SSOT + hub governance snapshot, ADR-031 신규 + 3 amend.
- **기각 1 — presigned NAS handoff (Codex D3/D5 권장)**: "code import만 0" 으로 data-free 재정의 →
  engine 이 NAS 객체 레이아웃·parquet·tier·DR 지식 보유 잔존. 사용자 의도("데이터 전부 제거" +
  외부 consumer) + β 위반. 검증상 io/ 미배선 + 실시간 hot-path data 비의존(거래소 WS) + ADR-030
  single-host loopback → presigned 가 풀려던 성능 문제 비실재. **Arrow IPC over REST** 채택.
- **기각 2 — 신규 중립 repo 2개 (bar-core/contract-types, Codex D1/D2 권장)**: 검증상 contract 코드가
  모두 PURE(market+stdlib) → market 통합 시 결합 전파 없음. 신규 CI/cross-repo lock 2개 불필요.
- **교정 — market 통합 → market(core) = 플랫폼 어휘**: 사용자 "market 도 끊어야" 직관 검증 →
  market 은 DAG 최하위 FOUNDATION, engine→market 은 어휘 의존(50+곳)이라 정상·불가피. 진짜 분리
  대상(data-storage/거래소-어댑터)만 제거. 4-layer 재설계로 수렴.

## Consequences

### 긍정

- engine→data PURE-contract 결합 제거 (strangler-fig 1단계) — 안정된 Layer0 위에 후속 Story 진행
- market = DAG 최하위 FOUNDATION 확립 — 순환 영구 0 (사실6 검증)
- 무중단 back-compat — shim 경유 `is` 동일성 보존 (기존 data caller 무변경 동작)
- CandleModel 재구현 0 (사실1) — engine import 경로 재지정만 (객체·schema 무변경)

### 부정 / trade-off

- data 측 shim 잔류 (DeprecationWarning) — MCT-188 D7 finalize 까지 deprecated 경로 유지
- cross-repo 4 PR sequential LAND 의무 (hub P1→market→data→engine→hub P2) — land_order 위반 시
  import 실패 (R1 — Phase 0 verify 독립 게이트로 완화)

### 위험

- **R1 (HIGH) — cross-repo contract/Phase0 desync 7회째**: docker-stack 6회 누적 + 본 Epic 은
  subtractive/relocate 라 위험 ↑. 완화 = Story별 Phase 0 deep-verify 독립 게이트 강제 +
  D-row ↔ scope_manifest 전수 1:1 reconcile (위 표 — MCT-179 lesson reapply). MCT-182 =
  V5 가설(5곳)↔실상(4곳) 요구사항/설계 lane 사전 정정으로 desync 1건 선제 차단.
- **R2 (HIGH) — MCT-41 Live Mode Debut 블락**: MCT-186 engine realtime cutover 가 live mode WS/주문
  경로 모듈 공유 가능. MCT-182~185 = 파일 disjoint 병렬 안전. MCT-186 진입 전 Phase 0 에서
  MCT-43~47 IN_PROGRESS 파일 교차 검증 의무 (owner = MCT-186, Orchestrator ordering 결정).

## References

- spec: `docs/superpowers/specs/2026-05-16-EPIC-data-domain-decoupling-design.md`
- scope_manifest: `scope_manifests/EPIC-data-domain-decoupling.yaml` (§design_decisions D1-D7 SSOT)
- Story (본 Story Phase 1 owner): `docs/stories/MCT-182.md`
- Change Plan: `docs/change-plans/MCT-182-change-plan.md`
- plan: `docs/superpowers/plans/2026-05-16-mct-182-layer0-contract-relocation.md`
- 관련 ADR: ADR-029 (tier-promotion-single-source) / ADR-027 (cold-tier-object-storage-nas-minio) /
  ADR-030 (docker-stack-governance) — amendment 예고 box (실 amend = 후속 owner Story) /
  ADR-025 (aggregation-core-lib-contract — aggregation SSOT 계보)
- **ADR-025 amendment 불요 근거** (Change Plan §10 정합): D1 relocate 는 aggregation 의 위치
  이동 + import 경로 재지정이며 ADR-025 의 4 Aggregator/scaled-int/contract_id contract 자체는
  byte-equivalence 보존 (Change Plan INV-1 — `from_scaled(to_scaled(d))==d` / 4 Aggregator 출력
  byte-for-byte / contract_id SHA256 동일). contract 무변경 + 위치만 변경 → ADR-025 amendment
  불요 (본 ADR-031 §D1 이 relocate 결정 record, ADR-025 는 algorithm contract SSOT 유지).
