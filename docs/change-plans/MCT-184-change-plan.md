---
story_key: MCT-184
epic_key: EPIC-data-domain-decoupling
type: change-plan
author: ArchitectPLAgent (chief author = ArchitectAgent + 6 deputy synthesis)
created: "2026-05-16"
status: design-lane-draft
decisions: [D3, D6]
related_adrs:
  - "ADR-031-data-domain-decoupling §D3 (fastapi-v1 + redis-stream — 본 Story = historical+reverse-write 절반)"
  - "ADR-030-docker-stack-governance (amendment box — data api service compose topology 예고. 실 compose = MCT-186)"
  - "ADR-029-tier-promotion-single-source (presigned-NAS-handoff 기각 정합 — NAS SoT 강화)"
  - "ADR-032 (PMO 발의 — VERIFIED badge evidence triad. MCT-184 §D3 dead-in-data 명시 박제 선제 reapply)"
  - "ADR-009 v1 16-col schema (reverse-write paper-candles schema 보존)"
  - "ADR-025 (paper_lineage.canonical_jsonl_hash — idempotency key 패턴 재사용, MCT-182 LAND market-core)"
---

# MCT-184 Change Plan — Layer 2 data REST API 신규 (historical + reverse-write)

> ArchitectAgent (chief author) + 6 deputy (CodebaseMapper / Refactor / SecurityArch
> primary 강함 / OperationalRiskArch CONDITIONAL 발동 / TestContractArch /
> DataMigrationArch) synthesis. ArchitectPLAgent 검수. MCT-183 Change Plan 형식 +
> §3.6.1 gate v2 패턴 SSOT 차용.

## 1. 목표 / 비목표

### 1.1 목표 (D3 + D6 — scope_manifest `§story_decision_matrix.MCT-184` 1:1)

- **D3 (REST boundary 절반)**: mctrader-data `src/mctrader_data/api/` FastAPI 신규 —
  `/v1` historical GET (Arrow IPC streaming, io/ reader wrap) + `/v1` reverse-write
  POST (paper-candles/backtest-artifact, idempotent) + OpenAPI emit (SSOT = data 단방향).
  `pyproject.toml` fastapi + uvicorn (ASGI) 의존 추가.
- **D3 (hub governance)**: hub `.codeforge/contracts/data-api-v1.openapi.json` schema
  snapshot + `scripts/cross-repo-contract-lock-check.sh` drift CI gate (ADR-030 §D13
  cross-repo lock 패턴 재사용).
- **D6 (ADR amendment box)**: ADR-030 amendment box (data api service compose topology
  예고 — 본문 19 D 무변경) + ADR-031 §D3 amendment box (REST boundary 부분 진행 —
  VERIFIED = MCT-185 후). D-row 1:1 reconcile + §3.6.1 gate v2 cross-Story reapply.

### 1.2 비목표 (out-of-scope — Story §2 비목표 표 1:1)

| 항목 | owner Story |
|------|-------------|
| realtime 정규화 stream (Redis Stream `api/realtime_stream.py`) | MCT-185 |
| engine `mctrader_engine/data_client/` thin/generated REST client | MCT-185 |
| engine cold-read 실경로 (`mctrader_data.storage.*` 직독) → data_client REST cutover | MCT-185 |
| data io/ reader production wiring (dead-in-data → live) | MCT-185 |
| ADR-029 실 amendment confirm (engine NAS 직독 폐기 LAND) | MCT-185 |
| ADR-030 실 compose wiring (data api service block + engine NAS cred drop) | MCT-186 |
| engine `mctrader_market_bithumb/upbit` 어댑터 import 제거 | MCT-186 |
| 다중거래소 확장 불변식 박제 | MCT-187 |
| data-free grep0 quad gate CI + Epic POLICY_FINALIZED | MCT-188 |

## 2. 배경 / AS-IS (CodebaseMapper 변호 — verified-via)

> **CodebaseMapper deputy perspective (보수/변호자)** — verified-via `git fetch
> origin` + `sed` + `ls` + `git grep` (2026-05-16, data origin/main HEAD `0e6f35b`
> = MCT-183 LAND).

### 2.1 AS-IS 사실 (file:line 근거)

| 사실 | file:line | 검증 |
|------|-----------|------|
| io/ 6 module 수령 (dead-in-data) | `src/mctrader_data/io/{cold_reader,dr_mode,endpoint_router,l1_reader,reader_cache,tier_reader}.py` + `__init__.py` | `ls src/mctrader_data/io/` = 6 module + __init__ ✓ (MCT-183 LAND) |
| historical read 진입점 (REST wrap target) | `cold_reader.py:106 def read(self, partition_path: str) -> ReadResult` / `l1_reader.py:85 def read(self, symbol: str, date: str, hour: int) -> L1ReadResult` / `tier_reader.py:147 def read(self, partition_path: str) -> TierReadResult` | sed 실측 ✓ — read-through cache pattern. cold_reader docstring 명시 "Idempotency (§11.6): read-only operation, 다중 호출 시 동일 결과" |
| reverse-write underlying | `paper_storage.py:18 def write_paper_candles(candles, *, root, run_id, snapshot_id, lineage) -> Path` | sed 실측 ✓ — ADR-009 v1 16-col schema 보존, JSON sidecar `_paper_lineage_{snapshot_id}.json` per snapshot. `from mctrader_market.candle import CandleLike` + `from mctrader_data.paper_lineage import PaperLineage` |
| health probe 별 프로세스/포트 경계 | `health_server.py:18 from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer` DEFAULT_PORT=8080 | sed 실측 ✓ — stdlib zero-dep daemon thread liveness probe. FastAPI app = 별 listener (port 분리 의무) |
| web framework 0 + api/ 부재 | `git grep -nE "import fastapi\|from fastapi\|..." 'src/*.py' 'src/**/*.py'` = EXIT 0 (no match) / `ls src/mctrader_data/api/` = ABSENT | git grep + ls 실측 ✓ — 신규 도입 충돌 0 |
| pyarrow/redis 가용 | `pyproject.toml:15 "pyarrow>=17"` / `:20 "redis[hiredis]>=5"` | grep 실측 ✓ — Arrow IPC 직렬화 + 향후 MCT-185 Redis Stream 신규 의존 0 |

### 2.2 CodebaseMapper 유지 근거 (보수 변호)

- io/ reader 6 module 동작·invariant (DR state machine / endpoint atomic flip / LRU
  byte budget / ETag verify) = MCT-183 LAND **byte-for-byte 보존**. 본 Story = REST
  **wrap only** (io/ 자체 변경 0). API signature 변경 0.
- `paper_storage.write_paper_candles` = MCT-20 LAND 안정 API — reverse-write POST 가
  wrap (직접 호출 == REST 경유 결과 동등). ADR-009 v1 16-col schema 보존.
- `health_server.py` stdlib = MCT-Pilot LAND. FastAPI app 추가가 health probe 동작
  무영향 (별 포트 `:8080` ≠ FastAPI `:8000`) — **보수 변호: 기존 자산 무변경 보존**.

## 3. 설계 결정 (Refactor 혁신 + SecurityArch 위협 + chief author synthesis)

### 3.1 api/ 패키지 구조 (Refactor — to-be 구조 + 최소 변경 경로)

> **Refactor deputy perspective (혁신/옹호자)** — io/ reader wrap 인터페이스 + OpenAPI
> emit 패턴 최소 변경 경로.

```
src/mctrader_data/api/
  __init__.py        ── public surface (app factory export)
  app.py             ── FastAPI app factory (create_app() — lifespan hook: io/ reader
                          singleton + SIGTERM graceful drain)
  routes_v1.py       ── /v1 APIRouter — historical GET + reverse-write POST
  arrow_ipc.py       ── Arrow IPC streaming serializer (io/ reader 출력 → IPC stream,
                          byte-equivalence INV-2)
  schemas.py         ── Pydantic strict request/response models (input validation 경계)
  deps.py            ── DI: io/ reader (tier_reader/cold_reader/l1_reader) provider
```

- **최소 변경 경로 (Refactor 옹호)**: io/ reader wrap = `deps.py` DI provider 가
  `mctrader_data.io.tier_reader.TierReader` 인스턴스 주입 (io/ 자체 변경 0 — Layer2
  자족, §0 V6 lazy import 0 → api/ → io/ = data 내부 import only, 역의존 신규 0).
- **OpenAPI emit 패턴**: FastAPI 자동 OpenAPI 3.x (route decorator + Pydantic schema
  → `/openapi.json`). 별도 emit 코드 0 (FastAPI 내장 — 최소 변경).
- **별 프로세스/포트 분리 (Refactor + CodebaseMapper 합치)**: FastAPI app = uvicorn
  ASGI `:8000` (entry: `python -m uvicorn mctrader_data.api.app:app`). `health_server.py`
  stdlib `:8080` 무변경 (별 listener). 두 프로세스 독립 — health probe / Prometheus
  `:8080/metrics` 동작 무영향.

### 3.2 historical endpoint 시그니처 + io/ reader wrap (chief author)

```
GET /v1/historical/candles
  query params:
    symbol: str         (allowlist regex ^[A-Z0-9_-]+$ — path traversal 차단)
    date: str           (ISO date ^\d{4}-\d{2}-\d{2}$ strict)
    partition_path: str (io/ reader 진입점 매핑 — ../  reject, allowlist)
  → io/ reader wrap:
    tier_reader.TierReader.read(partition_path)  [primary — priority chain]
    cold_reader.ColdReader.read(partition_path)  [L2/L3 직접]
    l1_reader.L1Reader.read(symbol, date, hour)  [L1 ETag]
  → response: StreamingResponse
    media_type: application/vnd.apache.arrow.stream
    body: Arrow IPC stream (io/ reader 출력 table → pyarrow.ipc.new_stream)
```

- **INV-2 byte-equivalence** *(F-4 contract amend, 2026-05-17 data#74 LAND)*:
  `ReadResult.data` = raw Arrow IPC bytes (io/ reader 가 직접 직렬화한 bytes — contract).
  `arrow_ipc.read_result_to_ipc_bytes()` = schema validation only (`reader.schema` parse)
  + `return data` unchanged (re-serialize 0). re-serialize 는 RecordBatch boundary /
  dictionary dedup / alignment 차이로 bytes-identical 보장 불가 (pyarrow 버전 의존).
  Option A: validation + pass-through → bytes-level INV-2 달성. 이전 설계 (pyarrow Table
  재직렬화 = table 동등 but bytes 비보장) 정정.
- **presigned-NAS-handoff 기각 (SecurityArch + chief author 합치)**: REST 응답 = Arrow
  IPC stream **only** — NAS object key/parquet tier/ETag/endpoint resolution **응답
  비노출** (engine NAS 비인지 — D2/ADR-029 정합). io/ reader 내부에서 NAS 접근, REST
  표면은 Arrow stream 만.

### 3.3 reverse-write POST + idempotency (SecurityArch 위협 + DataMigrationArch §11.6)

```
POST /v1/reverse-write/paper-candles
  body: PaperCandlesRequest (Pydantic strict)
    candles: list[CandleSchema]   (max_length bound — DoS 차단)
    run_id: str
    snapshot_id: str
    lineage: PaperLineageSchema
  → idempotency: canonical sha256 sidecar SSOT *(F-2 contract amend, 2026-05-17 data#74 LAND)*
    (paper_lineage.canonical_jsonl_hash 패턴 재사용 — MCT-182 LAND market-core)
    request_sha256 = PaperCandlesRequest.canonical_sha256() [always called — dead code 해소]
    sidecar _paper_lineage_{snapshot_id}.json 존재 + sha256 field 검사 3-case:
      (a) sidecar 존재 + sha256 match → idempotent no-op 200 {idempotent_skip: True}
      (b) sidecar 존재 + sha256 mismatch → 409 Conflict (INV-3 violation, 다른 payload)
      (c) sidecar 미존재 → write + sidecar에 sha256 persist (재시작 후 재검사 안전)
    [이전 설계 = sidecar 존재 검사만 (sha256 검증 0) → different payload silent skip 버그 정정]
  → response: 200 {written: bool, path: str, idempotent_skip: bool} | 409 Conflict

POST /v1/reverse-write/backtest-artifact
  body: BacktestArtifactRequest (Pydantic strict)
    run_id: str
    artifact: bytes  (Arrow IPC or tar — size bound)
  → backtest-artifact NAS sync wrap (idempotent: .done sentinel 검사 —
     ADR-030 §D19 MCT-181 LAND nas_sync 패턴 정합)
  → response: 200 {synced: bool, idempotent_skip: bool}
```

- **idempotency key 전략 (DataMigrationArch §11.6 primary + OperationalRiskArch
  consult)**: canonical payload sha256 (paper-candles: `canonical_jsonl_hash` 패턴 /
  backtest: `.done` sentinel). 동일 hash 재POST = no-op (중복 write 0, 동일 응답).
  INV-3 검증.
- **input validation 경계 (SecurityArch primary 강함)**: Pydantic strict (extra
  forbid + type strict) + Arrow IPC deserialize size bound (대용량/zip-bomb payload
  DoS 차단) + paper/backtest namespace 한정 write (market data SoT tier 경로 write
  불가 — ADR-029 XOR invariant 무충돌).

### 3.4 OpenAPI SSOT 단방향 + hub snapshot drift gate (chief author)

- **OpenAPI emit (SSOT = data 단방향)**: FastAPI 자동 OpenAPI 3.x. engine 측 OpenAPI
  정의 0 (generated client = MCT-185 owner, 본 Story 비참여 → 단방향 자연 성립, INV-1).
- **hub snapshot**: `.codeforge/contracts/data-api-v1.openapi.json` = data OpenAPI
  emit 의 governance copy. hub Phase1 = data#N **예상** emit 박제 → data#N LAND 후
  Phase2 PR2 에서 **실 emit 대조 reconcile** (hub Phase1 snapshot ↔ data#N 실 emit
  byte 1:1).
- **`scripts/cross-repo-contract-lock-check.sh` (드리프트 CI gate)**: ADR-030 §D13
  `check_cross_repo_locks.py` + `cross-repo-lock-check.yml` 패턴 재사용. data#N
  CI 에서 `python -m mctrader_data.api.app --emit-openapi | diff - <(hub snapshot)`
  → drift 시 exit 1 (snapshot ≠ emit 차단).

### 3.5 AC-6 wiring drift 차단 (MCT-189 동형 + ADR-032 evidence triad — chief author)

본 Story = REST boundary **신설** = "endpoint 박제 ↔ 실 production caller 0건" drift
위험 (MCT-189 ADR-029 §D3=C "VERIFIED 박제 ↔ promote_l1() caller 0건" 동형). 차단:

- REST endpoint production caller grep = **0건** (engine `data_client/` = MCT-185 owner,
  본 Story 비참여) — verified-via grep evidence.
- **consumer=MCT-185 (engine data_client REST 경유 cold-read cutover) 명시 박제** =
  의도된 dead-in-data SSOT (ADR-032 evidence triad: caller grep 0건 + 명시적 consumer
  박제 = drift 아닌 의도된 미배선 evidence).
- ADR-031 §D3 amendment box = **VERIFIED 아님 (부분 진행)** + consumer=MCT-185 명시.
  Phase2 PR2 carry-over registry 에 "MCT-185 owner — REST endpoint production wiring +
  engine cutover" 명시.

### 3.6 D-row ↔ scope_manifest 전수 1:1 reconcile (MCT-179 lesson reapply)

| 항목 | scope_manifest SSOT | 본 Change Plan / ADR amendment box | reconcile |
|------|---------------------|-----------------------------------|-----------|
| D3 option_chosen | `§design_decisions.D3.option_chosen: fastapi-v1 + redis-stream` | §1.1 = fastapi-v1 historical+reverse-write 절반 (realtime stream = MCT-185) | ✅ 1:1 |
| D3 owner_story | `§design_decisions.D3.owner_story: MCT-184 (historical+reverse-write) + MCT-185 (realtime stream)` | §3.5 consumer=MCT-185 명시 / ADR-031 §D3 amendment box | ✅ 1:1 |
| MCT-184 decisions | `§story_decision_matrix.MCT-184.decisions: [D3, D6]` | frontmatter `decisions: [D3, D6]` | ✅ 1:1 |
| MCT-184 cross_repo | `§story_decision_matrix.MCT-184.cross_repo` (hub/data 2 entry) | §9.1 land_order (hub P1 → data#N → hub P2) | ✅ 1:1 |
| land_order | `§story_decision_matrix.MCT-184.land_order: hub Phase1 → data#N → hub Phase2 PR2` | §9.1 | ✅ 1:1 (engine 비참여 2 repo) |
| ADR-030 amendment | `§planned_adrs.amendments[2]` ADR-030 `owner_story: MCT-184 (data api service) + MCT-186 (engine NAS cred drop)` | ADR-030 amendment box (MCT-184 Phase 1) = data api service 예고 / engine NAS cred drop = MCT-186 | ✅ 1:1 |
| ADR-031 §D3 | `§design_decisions.D3` | ADR-031 §D3 amendment box (부분 진행, VERIFIED=MCT-185) | ✅ 1:1 |
| .codeforge/contracts | `§planned_files.mctrader-hub` `data-api-v1.openapi.json owner: MCT-184` | §3.4 hub snapshot SSOT | ✅ 1:1 |
| pyproject fastapi | `§planned_files.mctrader-data` `pyproject.toml owner: MCT-184 change: fastapi 의존 추가` | §1.1 + §5 (uvicorn ASGI 동반) | ✅ 1:1 |

**reconcile verdict**: 본 Change Plan §3 ↔ scope_manifest `§design_decisions.D3` +
`§story_decision_matrix.MCT-184` + `§planned_adrs.amendments` ADR-030 +
`§planned_files` ↔ ADR-030 amendment box (MCT-184 Phase 1) ↔ ADR-031 §D3 amendment
box ↔ Story §2/§4 DELTA **전수 1:1 정합** (9/9 row). MCT-182/183 D-row reconcile
패턴 계승. 1차 FIX 발생 시 정정 산출물 list ↔ 전 산출물 동반 reconcile 체크리스트
의무 (cross-document desync 5회 누적 동형 사전 차단).

### 3.6.1 §3.6.1 gate v2 cross-Story reapply 박제 (MCT-179/182/183 desync 동형 영구 차단 forcing function)

> **PMO-AUDIT-MCT-183 §4.3 carry #8 + Story §0 reapply #3 의무** — plugin-codeforge-design#44
> OPEN (cross-document SSOT mechanical gate 미가용) → mctrader-hub self-discipline
> 유지. MCT-183 §3.6.1 gate v2 패턴 SSOT 차용 (glob-scope + 변형포괄 + self-verify
> TEST1/TEST2). cross-document SSOT desync 5회 누적 (MCT-179 + MCT-182 + MCT-183
> iter1/2/3) 동형의 영구 차단.

**canonical string (MCT-184 ADR-030/031 amendment box SSOT — byte 동일 의무)**:

ADR-030 amendment box canonical (data api service compose topology 예고):
```
data api service compose topology 예고
```
ADR-031 §D3 amendment box canonical (REST boundary 부분 진행 — VERIFIED 시점):
```
§D3 VERIFIED 는 MCT-185 realtime stream + engine thin client cutover 후
```
ADR-030 본문 정책 무변경 canonical (POLICY_FINALIZED 보존):
```
본문 19 D 정책 무변경
```

**MCT-184 cross-document SSOT desync grep gate v2 (glob-scope + 변형포괄 — data#N
착수 전 + DesignReview/CodeReview lane verdict 직전 의무 검증, 실 stale != 0 시 P0 차단)**:

```bash
# scope = glob 기반 (지정 목록 탈피 — 본 Epic 권위 SSOT 전수 + 차후 누락 방지):
#   docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md
#   scope_manifests/EPIC-data-domain-decoupling.yaml .codeforge/contracts/*.json
# pattern = 변형포괄 regex. ADR-031 §D3 의 VERIFIED 시점 축약/잘못된 owner 표기
#   == 0 검증 (§D3 VERIFIED = MCT-184 만 으로 축약된 stale 차단 — VERIFIED 는 MCT-185
#   realtime stream + cutover 후가 canonical). MCT-184 단독 VERIFIED 축약 carry 차단.
grep -rnE "§D3[^\n]{0,30}(VERIFIED|verified)[^\n]{0,40}MCT-184" \
  docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md \
  scope_manifests/EPIC-data-domain-decoupling.yaml .codeforge/contracts/*.json 2>/dev/null \
  | grep -ivE "VERIFIED = MCT-185|VERIFIED 는 MCT-185|VERIFIED 아님|부분 진행|amendment box only|FIX Ledger|grep gate|gate 패턴|grep -rnE|canonical string|TEST[12]|consumer=MCT-185|dead-in-data|§3\.6\.1|self-verify"
# 예외 필터: "§D3 VERIFIED = MCT-185 ..." canonical (정상) / "§D3 ... VERIFIED 아님 ...
#   부분 진행" (정상 — 본 Story 부분 진행 박제) / gate정의/이력/canonical 인용 차단.
# 추가 gate — ADR-030 본문 정책 변경 carry 차단 (POLICY_FINALIZED 무변경 위반 검출):
grep -rnE "ADR-030[^\n]{0,40}(19 D|본문)[^\n]{0,30}(변경|수정|amend 본문)" \
  docs/adr/ADR-031-data-domain-decoupling.md docs/stories/MCT-184.md \
  docs/change-plans/MCT-184-change-plan.md scope_manifests/EPIC-data-domain-decoupling.yaml 2>/dev/null \
  | grep -ivE "본문 19 D 정책 무변경|무변경 \(POLICY_FINALIZED|정책 무변경|예고 박제 only|amendment box only"
# 기대: 양 grep 0줄 (실 stale 0). 매치 발생 = (1) §D3 MCT-184 단독 VERIFIED 축약 carry
#   OR (2) ADR-030 본문 정책 변경 carry → P0 차단
```

> **gate self-verify (pattern 유효성 실증 — 매 gate 변경 시 의무, MCT-183 §3.6.1
> 패턴 SSOT 차용)**:
> - **TEST1 (포착력)**: stale 변형 `ADR-031 §D3 VERIFIED (MCT-184 LAND 박제)` (잘못된
>   단독 VERIFIED 축약 — VERIFIED 는 MCT-185 후가 canonical) → 신 pattern
>   `§D3[^\n]{0,30}(VERIFIED|verified)[^\n]{0,40}MCT-184` **MATCH ✓** (예외 필터
>   `VERIFIED = MCT-185|부분 진행` 미동반 → 검출). canonical `§D3 VERIFIED = MCT-185
>   realtime stream + engine thin client cutover 후` 는 예외 필터로 제외 = false
>   positive 0.
> - **TEST2 (false positive 0)**: canonical string `§D3 amendment box = REST boundary
>   (historical + reverse-write) LAND 박제 (§D3 VERIFIED = MCT-185 realtime stream +
>   engine thin client cutover 후)` → 신 pattern + 예외 필터 `VERIFIED = MCT-185|
>   VERIFIED 는 MCT-185|부분 진행|amendment box only` **NO MATCH ✓** (canonical 은
>   예외 필터에 전부 포착 — false positive 0). ADR-030 본문 무변경 canonical `본문
>   19 D 정책 무변경` 도 예외 필터 `본문 19 D 정책 무변경|정책 무변경` 로 NO MATCH ✓.

> **예외 (정상 잔존, gate 무위반 — `grep -ivE` 필터 명문)**:
> - `§D3 VERIFIED = MCT-185 ...` / `§D3 VERIFIED 는 MCT-185 ...` canonical (정상 —
>   VERIFIED 시점 박제)
> - `§D3 ... VERIFIED 아님 ... 부분 진행` / `amendment box only` (정상 — 본 Story
>   부분 진행 박제)
> - `consumer=MCT-185` / `dead-in-data` 동반 (AC-6 의도된 미배선 evidence)
> - `본문 19 D 정책 무변경` / `정책 무변경 (POLICY_FINALIZED` (ADR-030 무변경 박제)
> - FIX Ledger iter row / gate 패턴 정의 자체 / canonical string 인용 / §3.6.1 /
>   self-verify TEST1/TEST2 설명 (필터 제외)
> - `docs/retros/*` 과거 Story 회고 = glob scope 미포함 (gate scope 외)

> **sibling Story 산출물 canonical 정정 의무 (MCT-183 §3.6.1 패턴 계승 — 전수성
> 절대 보장)**: glob scope `docs/stories/MCT-18*.md` = MCT-182/183 sibling 포함.
> sibling Story frontmatter related_adrs + Continuity 표 의 ADR-031 §D3 owner-scope
> 기술 (`§D3 VERIFIED = MCT-185 후`) = canonical 통일 대상. owner-scope 를 기술하는
> 모든 Epic 권위 SSOT (Story frontmatter/cross_repo/Continuity 표) sibling 라도
> canonical 통일 의무.

**전수성 절대 보장 명령 (지정 목록 탈피 — repo-wide grep, post-LAND 의무)**:
```bash
grep -rn "§D3" docs/ scope_manifests/ .codeforge/contracts/ 2>/dev/null \
  | grep -iE "VERIFIED|verified" \
  | grep -ivE "VERIFIED = MCT-185\|VERIFIED 는 MCT-185\|VERIFIED 아님\|부분 진행\|amendment box only\|FIX Ledger\|gate 패턴\|grep gate\|canonical\|TEST[12]\|self-verify\|consumer=MCT-185\|dead-in-data"
# 기대: §D3 MCT-184 단독 VERIFIED 축약 0줄 (canonical/이력/gate정의/retros 외 —
#   실 stale 0 확인. post-LAND evidence 첨부 의무)
```

본 gate v2 = MCT-179 (ADR-030 D5/D8 swap) + MCT-182 (§4.2 self-contradiction) +
MCT-183 iter1→3 (ADR-027 amendment 축약) **cross-document SSOT desync 5회 누적 동형의
영구 차단 forcing function** (PMO-AUDIT-MCT-183 §4 Option A self-discipline 자기검증
박제 — glob-scope + 변형포괄 + self-verify TEST1/TEST2). 수동 reconcile 한계 자체 =
codeforge upstream ADR escalation 후보 (plugin-codeforge-design#44 OPEN — mechanical
gate 가용 전 까지 self-discipline 유지).

## 4. 외부 인터페이스

### 4.1 REST API surface (신규)

| method | path | 입력 | 출력 | wrap target |
|--------|------|------|------|-------------|
| GET | `/v1/historical/candles` | symbol/date/partition_path (Pydantic strict, allowlist) | Arrow IPC stream (`application/vnd.apache.arrow.stream`) | `tier_reader.read(partition_path)` :147 / `cold_reader.read(partition_path)` :106 / `l1_reader.read(symbol,date,hour)` :85 |
| POST | `/v1/reverse-write/paper-candles` | PaperCandlesRequest (Pydantic strict, max_length bound) | 200 {written, path, idempotent_skip} | `paper_storage.write_paper_candles(...)` :18 |
| POST | `/v1/reverse-write/backtest-artifact` | BacktestArtifactRequest | 200 {synced, idempotent_skip} | backtest-artifact NAS sync (ADR-030 §D19 nas_sync 패턴) |
| GET | `/openapi.json` | — | OpenAPI 3.x document (SSOT = data) | FastAPI 내장 |
| GET | `/health` | — | 200/503 (FastAPI app readiness — `:8080` stdlib probe 와 별) | (internal-only) |

- **OpenAPI SSOT 단방향**: engine 측 OpenAPI 정의 0 (generated client = MCT-185).
  hub `.codeforge/contracts/data-api-v1.openapi.json` = governance copy (drift detection).

### 4.2 import surface (변경 표)

| consumer | AS-IS | TO-BE | 마이그레이션 |
|----------|-------|-------|-------------|
| data api/ (신규) | — | `from mctrader_data.io import TierReader, ColdReader, L1Reader` + `from mctrader_data.paper_storage import write_paper_candles` | data 내부 import only (§0 V6 lazy import 0 — 역의존 신규 0) |
| engine src/ | (REST endpoint caller 0 — 본 Story 비참여) | (caller 0 — consumer=MCT-185 dead-in-data) | 없음 (MCT-185 owner — engine data_client cutover) |
| data full suite (1020+ test) | — | (fastapi/uvicorn 신규 의존 추가 — 기존 로직 무변경) | INV-5 회귀 0 (pyproject 의존 추가 ≠ 기존 storage/io/compactor 변경) |

**부작용 변경 없음**: REST 신설 = io/ reader wrap (read-only) + paper_storage wrap
(append-only, ADR-009 schema 보존). io/ reader / paper_storage 자체 변경 0. API
signature 변경 0. health_server.py 무변경 (별 포트).

## 5. pyproject 의존 추가 (Refactor + TestContractArch INV-5)

```toml
# pyproject.toml dependencies 추가:
"fastapi>=0.110",
"uvicorn[standard]>=0.27",   # ASGI 서버 (entry: python -m uvicorn ...)
```

- **INV-5 회귀 0 (TestContractArch)**: fastapi/uvicorn = 신규 의존 추가만 (기존
  storage/io/compactor/nas_storage 로직 무변경). data full suite 1020+ test 무영향
  검증 의무 (의존 추가 ≠ import 경로 변경). pydantic = fastapi 전이 의존 (data 기존
  pydantic 사용 — version conflict 검증 의무, 코드 lane).

## 6. 마이그레이션 / 배포 (DataMigrationArch §11 — 데이터 마이그레이션 N/A)

본 Story = **신규 REST 신설 (relocation/schema 변경 아님)** → §11 참조.

## 7. 보안 설계 (SecurityArch primary 강함 — §7.1-§7.7)

> **SecurityArch deputy perspective (위협/보안 변호자)** — 신규 REST network attack
> surface delta > 0 분석.

### 7.1 Trust boundary

- data api `:8000` = **internal-only** (compose internal network only, `ports:`
  publish 미노출 — ADR-030 single-host loopback 정합). 외부 인터넷 노출 0.
- trust boundary = engine↔data 내부 통신 only (consumer = MCT-185). attack surface =
  compose internal network 한정 (외부 abuse 표면 0).
- `/openapi.json` + `/docs` (Swagger UI) = internal-only 한정 노출. prod profile =
  `/docs` disable 검토 (§7.4 env-isolation).

### 7.2 Threat model (위협↔완화 매핑)

| # | 위협 | 완화 |
|---|------|------|
| T1 | path traversal (historical partition_path param) | allowlist regex (`^[A-Z0-9_/=.-]+$`) + `../` reject (Pydantic validator) |
| T2 | payload DoS (reverse-write 대용량/zip-bomb) | Pydantic `max_length` bound + Arrow IPC deserialize size guard (max bytes) |
| T3 | market data SoT 오염 (reverse-write 가 tier 경로 write) | paper/backtest namespace 한정 write (`paper_storage.write_paper_candles` = `schema_version=ohlcv.v1/mode=paper/` path — market SoT tier 경로 write 불가, ADR-029 XOR invariant 무충돌) |
| T4 | idempotency 우회 (중복 write) | canonical payload sha256 hash key (INV-3 — 동일 hash 재POST no-op) |
| T5 | Arrow IPC deserialize 취약점 (reverse-write artifact) | pyarrow >= 17 (보안 패치 baseline) + schema strict validation + size bound |
| T6 | 정보 노출 (NAS object layout via REST) | presigned-NAS-handoff 기각 — 응답 = Arrow IPC stream only (NAS key/parquet tier/ETag/endpoint resolution 비노출 — D2/ADR-029 정합) |

### 7.3 Auth / authz

- engine↔data internal auth: 본 Story = internal-only network 격리 → **인증 토큰
  미도입** (dead-in-data + consumer=MCT-185). MCT-185 cutover 시 internal service
  auth (shared secret header / mTLS) 검토 = **carry-over** (MCT-185 owner).
- reverse-write authz: paper/backtest namespace 한정 write + idempotent hash key.
- **잔여 risk accept 근거**: internal-only network 격리 (외부 노출 0) + dead-in-data
  (production caller 0) → 본 Story scope auth 생략 정당. MCT-185 cutover 시 production
  wiring 동반 auth 강화 carry.

### 7.4 DR / disconnect / rate-limit / env-isolation (OperationalRiskArch primary)

> **OperationalRiskArch deputy perspective (운영 리스크/production-readiness 변호자)**
> — §8.5 active = true (ArchitectPL 결정, CFP-378 AC-5. 4 조건: long-running
> connection Y / stateful cache Y / background worker N / restart-aware Y → 1+ Y).

| 운영 리스크 | 설계 결정 | CONDITIONAL N/A 사유 |
|-------------|-----------|---------------------|
| DR (data api down → engine 영향) | 본 Story = dead-in-data → production 영향 0. MCT-185 cutover 시 engine `data_client/` retry/circuit-breaker/local-fallback = carry-over (MCT-185 owner) | 본 Story scope DR N/A (dead-in-data, caller 0) — MCT-185 owner |
| disconnect (in-flight Arrow IPC streaming) | `StreamingResponse` SIGTERM graceful drain (ASGI lifespan shutdown hook — in-flight stream 완료 후 종료). uvicorn `--timeout-graceful-shutdown=60` | — (설계 확정) |
| rate-limit | internal-only network → 외부 abuse 표면 0. engine client 호출 = cold-read 패턴 (low-freq batch). 본 Story scope rate-limit 미도입 | internal-only 격리로 rate-limit N/A 정당 (외부 0). MCT-185 호출 패턴 측정 후 carry |
| env-isolation (dev/prod) | ADR-030 §D3 `--profile dev/prod` + `.env.dev`/`.env.prod` 정합. prod profile = `/docs` disable + DEBUG=0. 실 compose wiring = MCT-186 | — (설계 확정, 실 compose = MCT-186) |
| restart policy | `restart: unless-stopped` 예고 (long-running ASGI, §D2 paper-engine daemon 패턴) — 실 compose wiring = MCT-186 | 실 compose = MCT-186 owner (예고 박제) |
| clock sync (CONDITIONAL) | **N/A** — REST historical/reverse-write 는 시각 동기 비의존 (io/ reader read-only + paper_storage append, 시계 ordering 없음) | clock sync N/A (read/append only — 시각 동기 비의존) |
| §8.5 stateful/restart invariant | io/ reader_cache LRU+TTL+byte budget = MCT-183 LAND 보존 (api/ wrap = cache 자체 변경 0). ASGI restart 시 cache 휘발 (in-memory) — cold start 시 NAS re-read (정합, byte-equiv INV-2 유지) | — (설계 확정 — TestContractArch §8 검증) |

### 7.5 민감 데이터 분류

- reverse-write payload = paper-candles (OHLCV — 시장 데이터 파생, 민감도 LOW) +
  backtest-artifact (전략 결과 — 민감도 MEDIUM). NAS credential = data api 내부
  (io/ reader 가 NAS 접근) — REST 표면 비노출 (T6). engine NAS cred = 본 Story 무관
  (engine 비참여, drop = MCT-186).
- secret mount: data api service = collector service 와 동일 image (NAS cred env
  재사용, 실 compose = MCT-186). 본 Story = 코드 신설만 (secret 신규 0).

### 7.6 위협↔완화 매핑 종합

§7.2 T1-T6 = 신규 attack surface delta 전수 완화 매핑. 잔여 = internal auth +
rate-limit (MCT-185 carry — internal-only 격리로 본 Story accept).

### 7.7 보안 설계 종합 verdict

- **attack surface delta > 0** → 완화 = internal-only (외부 0) + Pydantic strict +
  Arrow size guard + paper/backtest namespace 한정.
- **잔여 risk (accept)**: internal auth 미도입 (MCT-185 carry) + rate-limit 미도입
  (internal-only) — 두 항목 MCT-185 cutover 시 production wiring 동반 강화.
- **SecurityArch verdict**: 신규 REST = internal-only + strict input validation +
  namespace 한정 으로 본 Story scope 위협 전수 완화. presigned 기각 = 정보 노출(T6)
  근본 차단. **설계 lane 진입 가능** (잔여 = MCT-185 carry, accept).

## 8. Test Contract (TestContractArch — §8.0 Phase 0 Gate + Perf Baseline 필수)

> **TestContractArch deputy perspective (QA perspective contributor)** — §8 커버리지
> + 경계 + invariant + Perf Baseline 타당성. §8.5 active = true.

### 8.0 Phase 0 Gate (코드 작업 data#N 착수 전 의무 — MCT-170/183 lesson reapply)

```bash
# V1: data/hub git fetch origin (working tree stale ≠ origin HEAD 차단)
cd mctrader-data && git fetch origin && git log -1 --oneline origin/main
#   기대: 0e6f35b (MCT-183 LAND) — 불일치 시 ArchitectPL escalate
cd mctrader-hub && git fetch origin
# V2: data web framework 0 재grep (HEAD 재대조)
cd mctrader-data && git grep -nE "import fastapi|from fastapi|import flask|from flask|import starlette|import uvicorn|import aiohttp" -- 'src/*.py' 'src/**/*.py'
#   기대: EXIT≠0 (no match — 신규 도입 충돌 0)
# V6: io/ lazy/conditional import 0 재grep (PMO-AUDIT-MCT-183 §5-5 의무)
git grep -nE "from mctrader_engine|import mctrader_engine" -- 'src/mctrader_data/io/**/*.py'
#   기대: EXIT≠0 (no match — io/ Layer2 자족, api/ → io/ 역의존 신규 0)
# 불일치 시 = 가설↔실상 괴리 → ArchitectPL escalate (코드 작업 중단)
```

### 8.1 Test 커버리지 후보 (TestContractArch — chief author 통합)

| # | test | 경계/invariant | 검증 |
|---|------|---------------|------|
| TC-1 | FastAPI app import + `/v1` route 등록 + `/openapi.json` 200 valid OpenAPI 3.x | AC-1 | app factory `create_app()` import 성공 + paths `/v1/...` 포함 |
| TC-2 | health probe 별 프로세스/포트 분리 — FastAPI `:8000` ≠ stdlib `:8080` | AC-1 | FastAPI app 기동이 `health_server.py` 동작 무영향 |
| TC-3 | historical Arrow IPC byte-equivalence — REST 응답 table == io/ reader 직접 출력 table | INV-2 / AC-2 | `/v1/historical/candles` Arrow IPC deserialize → table == `tier_reader.read()` / `cold_reader.read()` / `l1_reader.read()` 직접 출력 table (schema + 행 byte 동일) |
| TC-4 | historical 응답 = Arrow IPC stream only (NAS object layout 비노출) | AC-2 / T6 | 응답 header/body 에 NAS key/parquet tier/ETag/endpoint 미포함 |
| TC-5 | reverse-write paper-candles wrap 정확성 — REST 경유 == 직접 호출 결과 | AC-3 | `paper_storage.write_paper_candles` 직접 호출 결과 == REST POST 결과 (path + sidecar 동일) |
| TC-6 | reverse-write idempotent — 동일 hash payload 재POST = no-op | INV-3 / AC-3 | 2회 POST → 2회차 idempotent_skip=true + 중복 write 0 + 동일 200 |
| TC-7 | input validation — path traversal/대용량 payload reject | T1/T2 / AC-3 | `../` partition_path → 422 / max_length 초과 payload → 422 |
| TC-8 | OpenAPI SSOT + hub snapshot drift gate | AC-4 / INV-1 | `cross-repo-contract-lock-check.sh` — data emit ↔ hub snapshot 동일 시 exit 0, drift 시 exit 1 |
| TC-9 | AC-6 wiring evidence — REST endpoint production caller grep 0건 + consumer=MCT-185 박제 | AC-6 / INV-6 | engine `data_client/` 경유 caller grep = 0건 (verified-via) + consumer=MCT-185 명시 박제 확인 |
| TC-10 | data full suite 회귀 0 (fastapi/uvicorn 신규 의존) | INV-5 | data#N 후 full suite 신규 실패 0 (storage/io/compactor/nas_storage 무영향) |
| TC-11 | §3.6.1 gate v2 self-verify TEST1/TEST2 + repo-wide grep 0줄 | INV-4 | gate v2 pattern 포착력(TEST1) + false positive 0(TEST2) + post-LAND repo-wide grep 0줄 evidence |

### 8.2 Perf Baseline (필수 — 신규 REST 신설 = relocation 아님, PMO-AUDIT-MCT-183 §5-4)

> 본 Story = 신규 REST 신설 (relocation 아님) → byte-equiv N/A 가 아니라 **wrap 출력
> 정확성 invariant (INV-2) + Perf Baseline 필수**.

| 측정 | baseline 박제 | gate |
|------|---------------|------|
| historical Arrow IPC latency (single partition read) | io/ reader 직접 호출 latency 대비 REST wrap overhead 측정 (serialize + ASGI overhead) | baseline 박제 (production deploy 후 회귀 비교 reference. 회귀 gate = MCT-185 cutover Story) |
| historical Arrow IPC throughput (rows/sec stream) | Arrow IPC streaming 처리량 baseline | baseline 박제 |
| reverse-write idempotent skip latency (hash 검사 → no-op) | 재POST 시 hash 검사 overhead | baseline 박제 (idempotent path 가 full write 대비 빠름 확인) |

Perf Baseline = 박제 (본 Story = dead-in-data 신설 → 회귀 gate 적용 = MCT-185 cutover
시점. 본 Story 는 baseline 수립 의무).

## 9. 위험 / 롤백 / land_order

### 9.1 land_order (scope_manifest 1:1 — engine 비참여 2 repo)

```
hub Phase1 (docs — Story §0-§11 + ADR-030/031 amendment box + .codeforge/contracts/
  data-api-v1.openapi.json + scripts/cross-repo-contract-lock-check.sh + scope_manifest
  + CLAUDE.md)
  → data#N (land_order 1 — src/mctrader_data/api/ FastAPI /v1 historical+reverse-write
     + OpenAPI emit + pyproject fastapi/uvicorn)
  → hub Phase2 PR2 (박제 — Story §9/§10/§11 + ADR amendment box VERIFIED-부분진행
     confirm + scope_manifest milestone 3/7 + CLAUDE.md COMPLETED + RETRO)
```

각 PR CI green 후 admin merge → 다음 PR. **engine 비참여** (MCT-183 3 repo 대비
단순화). hub Phase1 snapshot = data#N **예상** emit 박제 → data#N LAND 후 Phase2 PR2
실 emit 대조 reconcile (`cross-repo-contract-lock-check.sh`).

### 9.2 위험

| risk | severity | 완화 |
|------|----------|------|
| R1 cross-repo Phase0 desync 7회째 | HIGH | §8.0 Phase 0 Gate (V1/V2/V6 HEAD 재대조) + D-row 1:1 reconcile (§3.6) + §3.6.1 gate v2 cross-Story reapply. engine 비참여 (2 repo) = 단순화 |
| MCT-189 wiring drift 동형 | MEDIUM | AC-6 (ADR-032 evidence triad — endpoint ↔ caller grep 0건 + consumer=MCT-185 명시 박제 = 의도된 dead-in-data SSOT) |
| cross-document SSOT desync 6회 누적 가능 | MEDIUM | §3.6.1 gate v2 (glob-scope + 변형포괄 + self-verify) — MCT-183 패턴 SSOT 차용. 1차 FIX 시 전 산출물 동반 reconcile 의무 |
| FastAPI 의존 도입 회귀 | LOW | INV-5 (data full suite 1020+ test 무영향 — pyproject 의존 추가 ≠ 기존 로직 변경). pydantic version conflict 검증 (코드 lane) |
| presigned 기각 → 성능 우려 | LOW | ADR-030 single-host loopback (latency 무시 가능) + Arrow IPC streaming (zero-copy) — presigned 성능 이점 비실재 (ADR-031 §Codex 기각 1 정합) |

### 9.3 롤백 (역순 backout 보존)

land_order 역순 backout: hub Phase2 PR2 revert → data#N revert (api/ 삭제 + pyproject
복원) → hub Phase1 revert. data#N = api/ 신규 패키지 (기존 코드 무변경 → 삭제 시
import 깨짐 0, dead-in-data caller 0). 안전 backout.

## 10. ADR 판단

- **ADR-031 §D3 amendment box (MCT-184 Phase 1)**: REST boundary historical+reverse-write
  부분 진행 박제 (VERIFIED = MCT-185 realtime stream + engine thin client cutover 후).
  consumer=MCT-185 dead-in-data 명시 (MCT-189 wiring drift 동형 차단).
- **ADR-030 amendment box (MCT-184 Phase 1)**: data api service compose topology 예고
  (본문 19 D 정책 무변경 — POLICY_FINALIZED 보존). 실 compose wiring + engine NAS
  cred drop = MCT-186 owner.
- **ADR-029 (NAS SoT) 강화**: presigned-NAS-handoff 기각 → REST 응답 = Arrow IPC
  stream only. 실 amend confirm = MCT-185 (cold-read cutover owner).
- **ADR-032 선제 reapply**: VERIFIED badge evidence triad — 본 Story §D3 amendment
  box = VERIFIED 아님 (부분 진행) + consumer=MCT-185 박제 = "dead-in-data 의도"
  evidence (plugin upstream escalation 중 미LAND — 선제 reapply).
- **ADR 신규 불요**: 본 Story = ADR-031 §D3 의 owner Story 절반 (REST boundary 신설).
  신규 ADR 발의 0 (ADR-031 §D3 가 결정 record SSOT).
- 신규 ADR 후보 (PMO retro 입력): cross-document SSOT mechanical gate
  (plugin-codeforge-design#44 OPEN — §3.6.1 gate v2 self-discipline 6회 누적 가능).

## 11. 데이터 마이그레이션 (DataMigrationArch — REST 신설 = N/A 명시)

> **DataMigrationArch deputy perspective (데이터 무결성 변호자)** — REST 신설 =
> persisted-data 무변경.

### 11.1-11.5 Schema / Migration / Rollback — **N/A (명시)**

본 Story = **신규 REST 신설 (relocation/schema 변경 아님)** → 데이터 마이그레이션
**N/A**:

- historical GET = io/ reader **read-only** wrap (persisted Parquet/NAS object
  무변경). schema/migration/rollback 무관.
- reverse-write POST = `paper_storage.write_paper_candles` wrap — **ADR-009 v1 16-col
  schema 보존** (paper provenance = path + lineage sidecar, row schema 무변경). 신규
  schema 도입 0. paper/backtest namespace append-only (market data SoT tier 경로 write
  불가 — ADR-029 XOR invariant 무충돌).
- pyproject fastapi 의존 추가 ≠ 데이터 변경 (INV-5).

### 11.6 Idempotency (DataMigrationArch primary + OperationalRiskArch consult)

> **CONDITIONAL idempotency — DataMigrationArch primary + OperationalRiskArch consult
> (N줄 memo input).**

- **reverse-write 무결성 (INV-3)**: canonical payload sha256 hash key. paper-candles
  = `paper_lineage.canonical_jsonl_hash` 패턴 재사용 (MCT-182 LAND market-core —
  `from mctrader_market.paper_lineage import canonical_jsonl_hash` 또는 동등). 동일
  hash 재POST → sidecar `_paper_lineage_{snapshot_id}.json` 존재 검사 → write skip +
  동일 200 (no-op, 중복 write 0). backtest-artifact = `.done` sentinel 검사 (ADR-030
  §D19 MCT-181 LAND nas_sync 패턴 정합).
- **io/ reader read idempotency**: inherently idempotent (`cold_reader.py:106`
  docstring 명시 "Idempotency (§11.6): read-only operation, 다중 호출 시 동일 결과"
  — verified-via). read-through cache 가 동일 partition 다중 read 시 동일 결과.
- **OperationalRiskArch consult (N줄 memo)**: ASGI restart 시 in-memory idempotency
  state 휘발 없음 (idempotency = sidecar/`.done` sentinel = persisted, in-memory
  state 비의존 → restart-safe). reverse-write 재POST after restart = sidecar 존재
  검사로 여전히 idempotent (restart invariant 정합).

### 11.7 데이터 무결성 종합 verdict

REST 신설 = persisted-data 무변경 (read-only wrap + append-only paper/backtest
namespace). idempotency = persisted sidecar/sentinel 기반 (restart-safe). market data
SoT XOR invariant 무충돌 (ADR-029). **DataMigrationArch verdict: 데이터 무결성
risk 0 — 설계 lane 진입 가능** (N/A 명시 + §11.6 idempotency 확정).

## 12. 검수 체크리스트 (ArchitectPL Phase 3 — §섹션별 deputy input 통합 정합성)

| § | deputy author | 통합 정합성 |
|---|---------------|-------------|
| §2 | CodebaseMapper (보수 변호) | verified-via file:line 근거 — io/ read 진입점 :106/:85/:147 + paper_storage:18 + health_server:18 별 포트 + web framework 0 ✓ |
| §3·§6 | Refactor (혁신 옹호) | api/ 패키지 구조 + io/ reader wrap DI + OpenAPI 내장 emit 최소 변경 경로. io/ 자체 변경 0 (Layer2 자족) ✓ |
| §7 (§7.1-§7.3/§7.5-§7.7) | SecurityArch (primary 강함) | T1-T6 위협↔완화 전수 매핑 + internal-only trust boundary + namespace 한정 + presigned 기각 (T6) ✓ |
| §7.4 | OperationalRiskArch (CONDITIONAL 발동) | 운영 리스크 5+1 항목 (DR/disconnect/rate-limit/env-isolation/restart/clock) — CONDITIONAL N/A 사유 명시 (dead-in-data DR / internal-only rate-limit / clock 비의존) ✓ |
| §8 | TestContractArch | TC-1~11 커버리지 + §8.0 Phase 0 Gate + Perf Baseline 필수 (신규 REST = relocation 아님) ✓ |
| §11 (§11.1-§11.5/§11.7) | DataMigrationArch | REST 신설 = persisted-data 무변경 N/A 명시 ✓ |
| §11.6 | DataMigrationArch primary + OperationalRiskArch consult | canonical hash idempotency + restart-safe (persisted sidecar/sentinel) ✓ |

**§섹션 누락 차단 검증**: §7 보안 설계 ✓ / §7.4 운영 리스크 ✓ / §8 Test Contract ✓ /
§10 ADR 판단 ✓ / §11 데이터 마이그레이션 ✓ — 누락 0 (DesignReview P0 차단 회피).

**ArchitectPL 검수 verdict**: 6 deputy perspective 전수 통합 + chief author synthesis
정합. §3.6.1 gate v2 cross-Story reapply 박제 완료. D-row 9/9 reconcile. **설계리뷰
lane 진입 가능** (잔여 risk = MCT-185 carry-over 명시 — accept).
