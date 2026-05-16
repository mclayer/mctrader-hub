# ADR-031: Data Domain Decoupling — 4-Layer 다중거래소 확장 아키텍처 (engine = data-free + exchange-agnostic pure consumer)

## Status

**Accepted** (MCT-182 LAND — D1 contract relocation VERIFIED, 2026-05-15)

상태 transition: Proposed (MCT-182 Phase 1, 2026-05-16) → **Accepted (MCT-182 LAND, 2026-05-15)** → POLICY_FINALIZED (MCT-188 LAND — EPIC 7/7 COMPLETED, D1-D7 전수 VERIFIED + ADR-029/027/030 amend confirm)

### §D1 VERIFIED amendment box (MCT-182 LAND 박제, 2026-05-15)

D1 (Contract relocation → mctrader-market Layer 0) **VERIFIED**:
- `mctrader_data.aggregation` PURE 패키지 → `mctrader-market` 이전 (market#11 `4902b53c`, 156/156 PASS)
- `TickRecord`/`OrderbookEventRecord` 순수 dataclass 추출 → `mctrader_market.records` (pyarrow 비결합 INV-3 충족)
- `paper_lineage` (PaperLineage/canonical_jsonl_hash) → `mctrader_market.paper_lineage`
- `CandleModel` engine 4곳(verified, 가설 5곳=docstring 오집계) → `mctrader_market.candle` 재지정 (engine#57 `c6249fa6`, 990/990 PASS)
- data shim: aggregation/__init__.py + paper_lineage.py = market re-export + DeprecationWarning. tick/orderbook_storage TickRecord/OrderbookEventRecord import 재지정 (writer 무변경 INV-6) — data#68 `4451f28d`, 884/884 PASS
- INV-1 byte-equivalence + INV-2 market→data 0 영구 + INV-4 SSOT 단일(is-동일성) 전수 충족
- **FIX iter1 회귀** (data#69 `5f00fc6e`): cold/duckdb_resample.py:53 + cold/polars_fallback.py:36 → mctrader_market.aggregation 직접 재지정 (shim 우회 SSOT 이중화 해소). `test_cold_path_uses_market_sot` 5 신규 test PASS. Change Plan §4.2 동반 정정("MCT-188 D7까지 deprecated 보존")으로 cross-document desync 해소 (4 산출물 §4.2/§6/§2.2/scope_manifest/ADR-031 수렴)

D6 (ADR meta) **VERIFIED**: 본 ADR-031 publish + D-row↔scope_manifest 7/7 byte 1:1 reconcile 정합. ADR-029/027/030 amendment 예고 box 유지 (실 amend = MCT-183/184/185/186 owner).

D2-D5/D7 = 후속 Story owner (MCT-183~188) — 본 LAND 무관.

### §D2 partial VERIFIED amendment box (MCT-183 LAND 박제, 2026-05-16)

D2 (Read 도메인 relocation → mctrader-data Layer 2) **partial VERIFIED** (io relocate 완료,
cold-read cutover pending MCT-185):
- engine `io/` 6 module (tier_reader/reader_cache/endpoint_router/dr_mode/cold_reader/l1_reader)
  → `src/mctrader_data/io/` 물리 이전 (data#70 `0e6f35b0`, engine#58 `18275737`, src caller 0
  dead-in-prod 안전 제거). tests/io/ 7 test 동반 이전
- reader_cache.py:339-348 stats() producer-wiring 블록 = 외부 import 없는 내부 no-op 치환
  (채택안 A — engine 역의존 0, Layer2 자족)
- ADR-027 §D9 amendment box + ADR-029 io reader relocated 박제 (engine NAS 직독 폐기 cutover
  confirm = MCT-185 owner)
- §3.6.1 gate v2 (glob-scope + 변형포괄 + self-verify TEST1/TEST2) cross-document SSOT desync
  forcing function 영구 박제 — RESET path post-LAND repo-wide grep 0줄 evidence
- cold-read 실경로 cutover (engine `mctrader_data.storage.scan_candles/orderbook_replay/
  path.resolve_data_root` 직독 → data REST 경유) = **MCT-185 owner** (§D2 VERIFIED = MCT-185 후)

### §D2 + §D3 VERIFIED amendment box (MCT-185 LAND 박제, 2026-05-17, EPIC-data-domain-decoupling Story-4 — cold-read cutover 완결 + realtime stream + reverse-write wiring 완결)

> **MCT-185 amendment (2026-05-17, Phase 1 draft → Phase 2 PR2 VERIFIED)**: EPIC-data-domain-decoupling
> Story-4 (가장 복잡 Story — 3 repo + production wiring 전환) Phase 1 박제분. **§D2 cold-read
> cutover 완결 + §D3 realtime stream + reverse-write wiring 완결** 동시 충족 (D2+D3 owner
> Story 절반 + 절반). 본 amendment box 박제 시점 = Phase 1 draft. 실 LAND confirm = Phase
> 2 PR2 박제 시점 (data#N LAND + engine#N LAND + AC-6 evidence triad PASS 후 confirm 박제
> 갱신).
>
> **Status `Accepted` 유지 (POLICY_FINALIZED 전이 = MCT-188 owner)** — 본 Story = D2+D3
> 진전 (VERIFIED amendment box 박제), POLICY_FINALIZED transition 은 MCT-188 (data-free
> grep0 quad gate + EPIC 7/7 finalize) 시점.

#### §D2 cold-read cutover 완결 박제 (D2 owner 절반 — MCT-183 io-relocate 완결 후 cold-read-behind-REST 절반)

- **engine cold-read 8곳 cutover LAND** (engine#N Phase 2 PR1) — engine src/ `from mctrader_data.(storage|path|orderbook_replay)`
  import = **0건 grep** 충족 (Phase 0 V2 식별 8곳 4파일: `cli.py:279,280` + `executor/tick_replay.py:26,559`
  + `wfo/evaluator/data_loader.py:43,44` + `wfo/search/data_loader.py:81,82`)
- **engine `data_client/` 신설** (engine#N Phase 2 PR1) = `src/mctrader_engine/data_client/`
  서브패키지 (`base.py` + `historical.py` + `reverse_write.py` + `exceptions.py` + `__init__.py`
  5 파일). hand-written thin client 채택 (MCT-184 OpenAPI SSOT 단방향 소비 + Pydantic schema
  market-core SSOT 재사용 = SSOT 단일 정합). `httpx>=0.27` 신규 의존 추가 (sync httpx Client
  — engine 기존 동기 호출 패턴 정합)
- **historical/orderbook endpoint 신설** (data#N Phase 2 PR1) = `/v1/historical/orderbook/snapshots`
  + `/v1/historical/orderbook/ticks` 2 endpoint 신설 (MCT-184 routes_v1.py 372 lines LAND 후
  본 Story 확장 — executor/tick_replay.py:26,559 cutover 완결 의무). OpenAPI snapshot 갱신 +
  hub `.codeforge/contracts/data-api-v1.openapi.json` 동반 갱신
- **ADR-029 §D2 VERIFIED amendment confirm** (`docs/adr/ADR-029-tier-promotion-single-source.md`
  §D2 VERIFIED amendment box, MCT-185 LAND 박제) — engine NAS 직독 폐기 LAND confirm + io
  reader 6 module = mctrader-data Layer 2 (MCT-183 LAND 정합) + cold-read 8곳 = data REST
  indirection 실 적용 박제. ADR-029 본문 11 D 정책 무변경 (POLICY_FINALIZED 보존)

#### §D3 realtime stream + reverse-write wiring 완결 박제 (D3 owner 절반 — MCT-184 historical+reverse-write 완결 후 redis-stream + reverse-write client 절반)

- **data `src/mctrader_data/api/realtime_stream.py` 신설** (data#N Phase 2 PR1) = Redis Stream
  `XADD market:tick:{exchange}:{symbol}` publisher (`REDIS_KEY_PREFIX_MARKET` env 도입, ADR-030
  §D15 prefix 정합). tick.v1.1 정규화 schema = `mctrader_market.schemas.tick.TickRowV1_1`
  SSOT 재사용 (market-core Layer 0 contract). data 기존 `redis[hiredis]>=5` 의존 재사용 (신규
  의존 0). MAXLEN `~ 100000` approximate trim
- **ASGI lifespan 통합** = `api/app.py` lifespan hook 에 `RealtimeStreamPublisher.startup()` /
  `.shutdown()` 통합 (uvicorn `--timeout-graceful-shutdown=60` 정합 — XADD in-flight drain
  + Redis connection close)
- **engine reverse-write 3곳 cutover LAND** (engine#N Phase 2 PR1) = `runtime/paper_runner.py:290,291`
  + `backtest/nas_sync.py:36` 3곳 2파일 → `data_client.reverse_write.post_paper_candles` +
  `.post_backtest_artifact` REST 경유 cutover. canonical sha256 client-side 정합 (market-core
  `canonical_jsonl_hash` SSOT 재사용 + MCT-184 post-merge fix `e612296` F-2 정합 — bytes-level
  정밀도 lesson reapply)
- **paper_runner.py:290 paper_lineage market-core 직독 변경** (Change Plan §3.5 본 Story
  포함 채택) = `from mctrader_data.paper_lineage import ...` → `from mctrader_market.paper_lineage
  import PaperLineage, canonical_jsonl_hash` (MCT-182 LAND market-core SSOT 정합). MCT-188 shim
  잔존 5곳 → 4곳 축소 (D7 grep0 quad gate scope 사전 축소)
- **MCT-184 dead-in-data → production wiring 전환** = MCT-184 routes_v1.py 4 endpoint (production
  caller 0 → ≥11곳 cutover scope 활성화) + 본 Story 신설 historical/orderbook 2 endpoint (production
  caller 신규 활성화). MCT-184 AC-6 의도된 dead-in-data SSOT → **본 Story AC-6 의도된 production
  wiring SSOT 박제** = ADR-032 evidence triad (file:line + caller grep ≥11 + integration test
  result) **선제 reapply 효력 1회 실증**

#### ADR-029/030/032 정합

- **ADR-029 §D2 VERIFIED amendment confirm**: 위 §D2 cold-read cutover 박제 정합. ADR-029
  본문 11 D 정책 무변경 (POLICY_FINALIZED 보존)
- **ADR-030 cross-ref only**: Redis Stream loopback 정합 재명시 (data 기존 `redis[hiredis]`
  의존 재사용 + 신규 service 추가 0 — 실 compose wiring + engine NAS cred drop = MCT-186 owner).
  본문 19 D 무변경 (POLICY_FINALIZED 보존)
- **ADR-032 선제 reapply 효력 실증 시점**: MCT-184 AC-6 의도된 dead-in-data SSOT → 본 Story
  AC-6 의도된 production wiring SSOT 박제 = evidence triad 갱신 (caller grep 0 → ≥11) =
  선제 reapply 효력 **1회 실증** (PMO-AUDIT-MCT-184 §3 패턴 #3 relocation/신규 신설 Story 안전
  invariant 화 권고의 MCT-185 실 검증)

#### D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply — §3.6.1 gate v2 cross-Story)

| 항목 | scope_manifest SSOT | 본 §D2+§D3 VERIFIED amendment box | reconcile |
|------|---------------------|-----------------------------------|-----------|
| D2 option_chosen | `§design_decisions.D2.option_chosen: io-relocate + cold-read-behind-REST` | 본 Story = cold-read-behind-REST 절반 (cold-read 8곳 cutover 완결 + io-relocate MCT-183 LAND 정합) | ✅ 1:1 |
| D2 owner_story | `§design_decisions.D2.owner_story: MCT-183 (io relocate) + MCT-185 (cold-read cutover)` | 본 amendment box = MCT-185 cutover 절반 LAND 박제 | ✅ 1:1 |
| D3 option_chosen | `§design_decisions.D3.option_chosen: fastapi-v1 + redis-stream` | 본 Story = redis-stream + reverse-write client 절반 (fastapi-v1 MCT-184 LAND 정합) | ✅ 1:1 |
| D3 owner_story | `§design_decisions.D3.owner_story: MCT-184 (historical+reverse-write) + MCT-185 (realtime stream)` | 본 amendment box = MCT-185 realtime stream + reverse-write wiring 절반 LAND 박제 | ✅ 1:1 |
| MCT-185 decisions | `§story_decision_matrix.MCT-185.decisions: [D2, D3]` | 본 Story = D2 (cold-read cutover) + D3 (realtime stream + reverse-write wiring) | ✅ 1:1 |
| ADR-029 amendment | `§planned_adrs.amendments[0]` ADR-029 `owner_story: MCT-183 (relocate) + MCT-185 (cutover confirm)` | ADR-029 §D2 VERIFIED amendment box (MCT-185 LAND 박제) = engine NAS 직독 폐기 LAND confirm | ✅ 1:1 |
| Status 전이 | (POLICY_FINALIZED 전이 = MCT-188 owner) | 본 Story = Status `Accepted` 유지 (POLICY_FINALIZED = MCT-188) | ✅ 1:1 |
| historical/orderbook endpoint | (scope_manifest 미명시 — MCT-184 LAND surface 4 endpoint) | 본 Story = data#N 에 신규 2 endpoint 추가 (cutover 완결 의무) + OpenAPI snapshot 갱신 | ✅ 1:1 (MCT-184 LAND surface 의 본 Story 확장 — final POLICY_FINALIZED 까지 amendment 누적 패턴 정합) |

**reconcile verdict**: ADR-031 §D2+§D3 VERIFIED amendment box ↔ `scope_manifests/EPIC-data-domain-decoupling.yaml`
`§design_decisions.D2/D3` + `§story_decision_matrix.MCT-185` + `§planned_adrs.amendments`
ADR-029 ↔ ADR-029 §D2 VERIFIED amendment box ↔ ADR-030 cross-ref ↔ MCT-185 Story §2/§4
DELTA ↔ `.codeforge/contracts/data-api-v1.openapi.json` snapshot (historical/orderbook 2
endpoint 신설 갱신) **전수 1:1 정합** (MCT-179 lesson reapply — MCT-182/183/184 D-row reconcile
패턴 계승. §3.6.1 gate v2 cross-Story reapply — Change Plan §3.6.1 SSOT, plugin-codeforge#795
mechanical gate 미가용).

### §D3 amendment box (MCT-184 Phase 2 LAND confirm — data#72 MERGED 45e501c, 2026-05-16)

> **§D3 부분 진행 LAND 확정** — data#72 (45e501c5) Phase 2 PR1 MERGED (2026-05-16).
> `src/mctrader_data/api/` FastAPI 6 파일 신규 LAND. 21 API test PASS. ruff + pyright 0 error.
> ubuntu CI PASS (1152 passed 신규 실패 0). §D3 VERIFIED 는 MCT-185 realtime stream 후.

- **LAND commit**: data#72 45e501c5 (squash merge — MCT-184 api/ + MCT-189 testcontainers)
- **MCT-184 api/ 파일**: `api/__init__.py` + `api/app.py` + `api/arrow_ipc.py` + `api/deps.py` + `api/routes_v1.py` + `api/schemas.py` (6 CREATE)
- **test**: `tests/api/test_rest_api.py` TC-1~11 + Perf Baseline (21 passed + 2 skipped)
- **dead-in-data 유지**: production caller 0건 확정 (AC-6 wiring drift 차단 — consumer=MCT-185)
- **§8.5 Impl Manifest**: `docs/stories/MCT-184.md §8.5` (DeveloperPL CFP-39 self-write)

### §D3 amendment box (MCT-184 Phase 1 — REST boundary 부분 진행 박제, 2026-05-16)

> **§D3 VERIFIED 아님 — 부분 진행 (amendment box only)**. §D3 `fastapi-v1 + redis-stream`
> 의 owner 는 **MCT-184 (historical + reverse-write 절반) + MCT-185 (realtime stream 절반 +
> engine thin client cutover)** 다 (scope_manifest `§design_decisions.D3.owner_story` 1:1
> 정합). 본 Story (MCT-184) = §D3 **historical + reverse-write REST boundary 신설**만 LAND.
> **§D3 VERIFIED 는 MCT-185 realtime stream (Redis Stream) + engine `data_client/` thin
> client cutover LAND 후**. 본 amendment box 는 §D3 부분 진행 record 박제 (VERIFIED badge
> 아님 — MCT-189 wiring drift 동형 차단 정합, 아래 dead-in-data 명시 박제).

#### MCT-184 LAND 박제 (REST boundary historical + reverse-write)

- **data `src/mctrader_data/api/` FastAPI 신규** (Phase 0 V2/V3/V4 실증 — web framework 0 +
  stdlib health_server only + api/ 부재 → 신규 배치 충돌 0). `pyproject.toml` fastapi +
  uvicorn (ASGI) 의존 추가 (INV-5 — data 1020+ test 회귀 0)
- **`/v1` historical GET** — Arrow IPC streaming 응답. MCT-183 LAND io/ reader wrap
  (`mctrader_data.io.tier_reader.TierReader.read(partition_path)` :147 /
  `cold_reader.ColdReader.read(partition_path)` :106 / `l1_reader.L1Reader.read(symbol,
  date, hour)` :85 — Phase 0 V5 read 진입점). **presigned-NAS-handoff 기각** (engine NAS
  object layout/parquet tier/ETag/endpoint resolution 비인지 — D2/ADR-029 정합. REST 응답 =
  Arrow IPC stream only). INV-2 byte-equivalence (REST 응답 Arrow table == io/ reader 직접
  출력 Arrow table)
- **`/v1` reverse-write POST** — paper-candles (`paper_storage.write_paper_candles(candles,
  *, root, run_id, snapshot_id, lineage)` :18 wrap) + backtest-artifact NAS sync wrap.
  **idempotent** — 동일 hash payload 재POST = no-op (INV-3, idempotency key/hash 전략 =
  Change Plan §7 SecurityArch + §11.6 DataMigrationArch 확정)
- **OpenAPI emit (SSOT = data repo 단방향)** — FastAPI 자동 OpenAPI 3.x. engine generated
  client = MCT-185 owner (본 Story 비참여 → 단방향 자연 성립, INV-1). hub
  `.codeforge/contracts/data-api-v1.openapi.json` = governance snapshot (SSOT = data emit,
  hub = drift detection copy) + `scripts/cross-repo-contract-lock-check.sh` drift CI gate
  (ADR-030 §D13 cross-repo lock 패턴 재사용)

#### dead-in-data 명시 박제 (MCT-189 wiring drift 동형 차단 — ADR-032 evidence triad 선제 reapply)

본 Story = REST boundary **신설**이며 production caller wiring 은 **의도된 dead-in-data**
다. REST endpoint production caller grep = **0건** (engine `data_client/` 경유 호출 =
MCT-185 owner — 본 Story 비참여). 이는 MCT-189 (ADR-029 §D3=C "VERIFIED 박제 ↔
`promote_l1()` production caller 0건" wiring drift) 동형 위험 영역이나, 본 §D3 amendment
box 가 **VERIFIED 아님 (부분 진행)** + `consumer=MCT-185 (engine data_client REST 경유
cold-read cutover)` 명시 박제 = **drift 아닌 의도된 미배선 evidence** (ADR-032 evidence
triad: caller grep 0건 + 명시적 consumer 박제). MCT-185 cold-read cutover LAND 시 engine
`data_client/` → `/v1` historical REST 경유 wiring 으로 §D3 VERIFIED transition.

#### ADR-029/030 정합

- **ADR-029 (NAS SoT = data 단독 소유) 강화**: presigned-NAS-handoff 기각 → REST 응답 =
  Arrow IPC stream only (NAS object layout/parquet tier/ETag/endpoint resolution 비노출).
  engine NAS 직독 폐기의 선행 토대 (실 amend confirm = MCT-185 cold-read cutover owner)
- **ADR-030 amendment box (MCT-184 Phase 1)**: data api service compose topology 예고
  (`docs/adr/ADR-030-docker-stack-governance.md` "Amendment box (MCT-184 Phase 1)"). 실
  compose wiring + engine NAS cred drop = MCT-186 owner. 본문 19 D 정책 무변경
  (POLICY_FINALIZED 보존)

#### D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply — §3.6.1 gate v2 cross-Story)

| 항목 | scope_manifest SSOT | 본 §D3 amendment box | reconcile |
|------|---------------------|----------------------|-----------|
| D3 option_chosen | `§design_decisions.D3.option_chosen: fastapi-v1 + redis-stream` | 본 Story = fastapi-v1 historical+reverse-write 절반 (realtime stream = MCT-185) | ✅ 1:1 |
| D3 owner_story | `§design_decisions.D3.owner_story: MCT-184 (historical+reverse-write) + MCT-185 (realtime stream)` | 본 amendment box = MCT-184 historical+reverse-write LAND 박제 / realtime stream = MCT-185 명시 | ✅ 1:1 |
| MCT-184 decisions | `§story_decision_matrix.MCT-184.decisions: [D3, D6]` | 본 Story = D3 (REST boundary) + D6 (ADR amendment box) | ✅ 1:1 |
| ADR-030 amendment | `§planned_adrs.amendments[2]` ADR-030 `owner_story: MCT-184 (data api service) + MCT-186 (engine NAS cred drop)` | ADR-030 amendment box (MCT-184 Phase 1) = data api service 예고 박제 / engine NAS cred drop = MCT-186 | ✅ 1:1 |
| §D3 VERIFIED 시점 | (MCT-185 realtime stream + engine thin client cutover 후) | 본 amendment box = 부분 진행 (VERIFIED 아님 — consumer=MCT-185 dead-in-data 명시) | ✅ 1:1 |

**reconcile verdict**: ADR-031 §D3 amendment box ↔ `scope_manifests/EPIC-data-domain-decoupling.yaml`
`§design_decisions.D3` + `§story_decision_matrix.MCT-184` + `§planned_adrs.amendments`
ADR-030 ↔ ADR-030 amendment box (MCT-184 Phase 1) ↔ MCT-184 Story §2/§4 DELTA ↔
`.codeforge/contracts/data-api-v1.openapi.json` snapshot **전수 1:1 정합** (MCT-179 lesson
reapply — Out-of-scope/D-row stale 사전 차단. MCT-182/183 D-row reconcile 패턴 계승. §3.6.1
gate v2 cross-Story reapply — Change Plan §3.6.1 SSOT, plugin-codeforge-design#44 mechanical
gate 미가용).

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
| ADR-027 (cold-tier-object-storage-nas-minio) | io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2 | **MCT-183** (io reader 6 module relocate) | false |
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
  ADR-025 (aggregation-core-lib-contract — aggregation SSOT 계보) /
  ADR-032 (PMO 발의 — VERIFIED badge evidence triad, MCT-184 §D3 dead-in-data 명시 박제 선제 reapply)
- **§D2 partial VERIFIED (MCT-183 LAND, 2026-05-16)**: io/ 6 module relocated to mctrader-data
  Layer2 (cutover confirm = MCT-185). `docs/stories/MCT-183.md` + `docs/change-plans/MCT-183-change-plan.md`
- **§D3 amendment box (MCT-184 Phase 1, 2026-05-16)**: REST boundary historical+reverse-write
  부분 진행 (§D3 VERIFIED = MCT-185 realtime stream + engine thin client cutover 후). consumer=MCT-185
  dead-in-data 명시 박제 (MCT-189 wiring drift 동형 차단). `docs/stories/MCT-184.md` +
  `docs/change-plans/MCT-184-change-plan.md` + ADR-030 amendment box (MCT-184 Phase 1)
- **ADR-025 amendment 불요 근거** (Change Plan §10 정합): D1 relocate 는 aggregation 의 위치
  이동 + import 경로 재지정이며 ADR-025 의 4 Aggregator/scaled-int/contract_id contract 자체는
  byte-equivalence 보존 (Change Plan INV-1 — `from_scaled(to_scaled(d))==d` / 4 Aggregator 출력
  byte-for-byte / contract_id SHA256 동일). contract 무변경 + 위치만 변경 → ADR-025 amendment
  불요 (본 ADR-031 §D1 이 relocate 결정 record, ADR-025 는 algorithm contract SSOT 유지).
