---
adr_id: ADR-029
title: Cold tier governance v2 — NAS = Single Source of Truth for ALL tiers
status: Accepted
date: 2026-05-14
related_story: MCT-167
related_epic: EPIC-tier-promotion-single-source
category: data
is_transitional: false
successor_of:
  - ADR-017 (Zero-loss ingestion via WAL + tiered compaction — D3 L1 NAS PUT invariant 확장)
  - ADR-027 (Cold Tier Object Storage on NAS MinIO — §D5 L1 NAS upload 금지 invariant 폐기, §D9 reader SoT 확장)
complements:
  - ADR-016 (Audit log append-only with hash chain)
amends:
  - ADR-017 §3 D3 (L1 NAS PUT 의무 박제)
  - ADR-027 §D5 (L1 upload 정책) + §D7 (local GC grace) + §D9 (reader SoT 확장)
  - ADR-009 §D12.2 (forward-only invariant — NAS object SoT 격상)
references:
  - ADR-008 (Secret management)
  - ADR-009 (OHLCV 16-col schema)
  - ADR-026 (Legacy candle provenance retirement)
  - ADR-027 (Cold tier object storage)
related_stories:
  - MCT-167 (governance singleton — 본 ADR + 3 amendment 박제)
  - MCT-168 (L1 NAS DualWriter wiring — D1 + D2 impl, LAND 2026-05-14, mctrader-data#59)
  - MCT-169 (L1 NAS verify + immediate local delete + tier promotion — D3 + D10 impl)
  - MCT-170 (engine reader 재구현 — D7 + D8 impl)
  - MCT-171 (DR runbook + invariant 8종 + 용량 제한 — D4 + D5 + D6 + D11 impl)
  - MCT-172 (Epic integration smoke + EPIC CLOSED — D9 + D10 verify)
prerequisite_stories:
  - MCT-161 (NAS bucket versioning + Object Lock — D6 prerequisite, LAND 2026-05-14)
  - MCT-163 (DualWriter streaming + L2/L3 iter_batches — R1 mitigation, LAND 2026-05-14)
---

# ADR-029: Cold tier governance v2 — NAS = Single Source of Truth for ALL tiers

## Status

Accepted — 2026-05-14. MCT-167 (EPIC-tier-promotion-single-source governance singleton Story) 가 본 ADR 본문을 publish.

### D1+D2 verify status (MCT-168 LAND, 2026-05-14)

- **D1=B VERIFIED** (mctrader-data#59): L1Compactor.compact_segment() 내 _write_parquet_atomic() 직후 DualWriter.put_l1() 호출 확인. compactor 측 timing 정합 (22 tests PASS).
- **D2=B VERIFIED** (mctrader-data#59): DualWriter.put_l1() → NASUploader.put_streaming() + queued → local_only 경로 확인. retry_queue + local_only 재사용 정합 (INV-5 status enum 3종 exhaustive PASS).

### §D2 VERIFIED amendment box (MCT-185 LAND 박제, 2026-05-17, EPIC-data-domain-decoupling Story-4 — engine NAS 직독 폐기 LAND confirm)

> **MCT-185 amendment (2026-05-17, Phase 2 PR2 VERIFIED)**: MCT-183
> amendment box "engine NAS 직독 폐기 예고" 의 **LAND confirm** 단계. 3 PR cross-repo
> sequential LAND 완결: hub#366 (67bcc1c, Phase 1 docs) → data#76 (9473665, land_order 1
> realtime_stream + historical/orderbook 2 endpoint) → engine#59 (1312195, land_order 2
> data_client/ 신설 + cold-read 8곳 + reverse-write 3곳 cutover) → hub Phase 2 PR2 박제.
> ADR-029 **본문 11 D 정책 무변경 (POLICY_FINALIZED 보존)** — MCT-181 LAND Status Amendment
> box 패턴 정합. 본 §D2 VERIFIED 가 engine NAS 직독 폐기의 invariant carrier (D2 cold-read
> cutover 완결).
>
> **§D2 cold-read cutover LAND 박제 (MCT-185 Phase 1 draft, EPIC-data-domain-decoupling
> §D2 `io-relocate + cold-read-behind-REST` 의 cold-read-behind-REST 절반 — io-relocate
> MCT-183 LAND 정합)**:
>
> - **engine cold-read 8곳 cutover** = engine src/ `from mctrader_data.(storage|path|orderbook_replay)`
>   import = **0건 grep** 충족 예정 (engine#N LAND 시점, Phase 0 V2 식별 8곳: `cli.py:279,280`
>   `resolve_data_root + scan_candles` + `executor/tick_replay.py:26,559` `orderbook_replay`
>   top-level + function-local + `wfo/evaluator/data_loader.py:43,44` `resolve_data_root +
>   scan_candles` + `wfo/search/data_loader.py:81,82` 동형) → engine `data_client.historical`
>   REST 경유 cutover (MCT-184 routes_v1.py LAND `/v1/historical/candles` + `/v1/historical/candles/l1`
>   + 본 Story 신설 `/v1/historical/orderbook/snapshots` + `/v1/historical/orderbook/ticks`)
> - **engine reverse-write carrier 3곳 cutover** = `from mctrader_data.paper_storage import
>   write_paper_candles` 0건 grep + `from mctrader_data.nas_storage.nas_uploader import` 0건
>   grep + paper_runner.py:290 paper_lineage market-core 직독 변경 (MCT-185 Change Plan §3.5
>   본 Story 포함 채택) → engine `data_client.reverse_write` REST 경유 cutover (MCT-184
>   routes_v1.py LAND `/v1/reverse-write/paper-candles` + `/v1/reverse-write/backtest-artifact`)
> - **engine 측 NAS object layout / parquet tier / ETag / endpoint resolution = 비인지**
>   (D2/ADR-029 정합 — REST 응답 = Arrow IPC stream only, presigned-NAS-handoff 기각 효력
>   실증). io reader 6 module = mctrader-data Layer 2 자족 (MCT-183 LAND 정합)
> - **§D8 forward-only + local fallback 정합**: engine `data_client.base` retry/circuit-breaker
>   에 **local-fallback 없음** (fallback 도입 시 D2 invariant 위반 — ADR-029 §D8 cutoff
>   2026-09-01 sunset 가속화 가능, MCT-170 D8 amendment 정합). data api down → engine cold-read
>   503 propagate (graceful + alert) = D2 invariant strict 유지

**§D9 NAS = SoT for ALL tiers 정합 (MCT-167 amendment box 재명시)**:

- 본 ADR §D9 (MCT-167 amendment) "NAS = SoT for ALL tiers" 의 engine read carrier =
  MCT-185 LAND 후 **data REST API indirection 으로 전환 완결**. "engine read-through cache"
  모델 = engine 측 cache 없음 (engine `data_client.base` = stateless HTTP client + circuit-breaker
  in-memory state only) + data 측 io/ reader cache (MCT-183 LAND `reader_cache.py` LRU+TTL+byte
  budget) = Layer 2 자족 cache.
- **engine NAS credential drop** = MCT-186 owner (engine 컨테이너 NAS credential env drop —
  ADR-030 §D2 amendment box "engine NAS cred drop" 정합). 본 Story = engine import 0건 grep
  목표 (AC-3 D2 cutover grep0), engine pyproject `mctrader-data @ git+` 의존 line 유지 (MCT-188
  D7 final 제거 owner)

**D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply — R1 가드)**:

scope_manifest `§design_decisions.D2` (`option_chosen: io-relocate + cold-read-behind-REST`
/ `owner_story: MCT-183 (io relocate) + MCT-185 (cold-read cutover)`) ↔ `§planned_adrs.amendments`
ADR-029 (`section: engine NAS 직독 폐기 + io reader relocated + NAS SoT 경로 data REST
indirection` / `owner_story: MCT-183 (relocate) + MCT-185 (cutover confirm)`) ↔
`§story_decision_matrix.MCT-185` (`decisions: [D2, D3]`) ↔ 본 §D2 VERIFIED amendment box
**전수 1:1 정합** (MCT-182/183/184 D-row reconcile 패턴 계승, cross-document SSOT desync
사전 차단).

cross-ref: `docs/stories/MCT-185.md` §0/§4.3/§4.4/§5/§6 + `docs/change-plans/MCT-185-change-plan.md`
§3/§7/§8.0/§10/§11 + `docs/adr/ADR-031-data-domain-decoupling.md` §D2+§D3 VERIFIED amendment
box (MCT-185 LAND 박제, Phase 2 PR2 VERIFIED — hub#366 + data#76 + engine#59 LAND 완결).

### §D2 amend confirm — MCT-188 final (2026-05-17, EPIC-data-domain-decoupling Story-7, Epic final)

> **MCT-188 amend confirm**: engine `mctrader_data.*` 직독 전면 제거 완결 (D7 quad gate
> Gate 1 + Gate 2 충족). 본 amend confirm = MCT-183 (io-relocate) + MCT-185 (cold-read
> cutover) + MCT-188 (shim import 4곳 최종 제거 + pyproject mctrader-data 의존 제거)
> 3단계 완결. ADR-029 §D2 `io-relocate + cold-read-behind-REST` = **전수 VERIFIED 확정**.

- **Gate 1 final grep0** (MCT-188 engine#N LAND 후): `grep -rn "from mctrader_data|import mctrader_data" engine/src/` = **0건** (4곳 잔존 → cutover 완결: `executor/tick_replay.py:28-29` + `hot/state_machine.py:33` + `strategy/templates/tick_scalping.py:76`)
- **Gate 2 pyproject 제거** (MCT-188 engine#N LAND 후): `grep "mctrader-data" engine/pyproject.toml` = **0건** (line 11 제거)
- **engine data-free 완전 달성**: python 의존 그래프에서 `mctrader_data` 제거 완결 — engine = mctrader_data python 의존 0 (D2 `io-relocate + cold-read-behind-REST` 완결 final confirm)
- **ADR-029 본문 정책 무변경 (POLICY_FINALIZED 보존)** — 11 D 정책 유효. 본 amend confirm = MCT-188 D7 quad gate 충족 evidence 박제만.

cross-ref: `docs/stories/MCT-188.md` §0/§4/§5 + `docs/change-plans/MCT-188-change-plan.md` §3.1 + `docs/adr/ADR-031-data-domain-decoupling.md` §D7 VERIFIED + Status POLICY_FINALIZED (MCT-188 LAND).

### MCT-189 amendment box (2026-05-16, EPIC-tier-promotion-single-source carry over — §D3=C grace-0 로컬삭제 wiring 완결, Phase 1 draft → Phase 2 PR3 VERIFIED)

> **MCT-189 amendment (2026-05-17, Phase 2 PR3 VERIFIED — LANDed)**: 2026-05-16 운영 진단에서 `promote_l1()` production caller = 0건 발견 (MCT-169 D3=C 정의만 LAND, caller wiring 부재 = cross-document SSOT drift 2호). 본 Story = wiring 완결: (a) DualWriter `status=committed` branch self-delete via `_promote_after_nas_put` helper (D-2 A) — caller 0건 재발 차단, (b) 4중 HEAD verify primitive (ETag+VersionId+sha256 metadata+ContentLength, D-4 C), (c) pre-delete HEAD guard (D-8 B, race window 차단), (d) fd-consistent sha256+size 단일 fd 스냅샷 (`_compute_local_sha256_and_size`, code-quality FIX iter3 — TOCTOU 축소), (e) NASUploader.enqueue_retry() public method (private getattr fragility 제거), (f) verify-fail → retry_queue enqueue + status="local_only" (committed 거짓 신호 제거, P0 fix iter1), (g) legacy 130GB retroactive cleanup `scan_and_cleanup_legacy` + batch_limit=500 (PR #75, 첫 sweep stall 회피 점진 회수 ~52h). §D3 line 246 grace 0 일관 amend (D-1 A unconditional). §D11 표 L1 local 행 "DualWriter status=committed self-delete (grace 0)" 정정. §D10 production evidence gate 강화 (post-LAND 14d 0 violation, ADR-032 evidence triad 형식 차용). Migration §Forward-only invariant 격상 (local fallback 제거, NAS versioning 30d window 의존, D-5 A). **POLICY_FINALIZED 유지** (강등 없음 — 11/11 D 정상, D3 wiring carry over → **resolved**). LAND: hub #357 (3f138a6) + data #73 (de12f43) + data #75 (a1a8ccf) + hub #TBD Phase 2 PR3. Phase 2 PR1 진행 중 cross-Story contamination 발견 (data #71 MCT-184 commit 45e501c 가 partial MCT-189 wiring squash 포함 — FIX iter1-3 부재 결함 상태로 main 일시 도달, PR1 rebase --strategy-option=theirs 로 FIX iter 적용 버전 덮어쓰기) — 정직 박제: `docs/stories/MCT-189.md` §9 + RETRO-MCT-189.md.

### MCT-183 amendment box (2026-05-16, EPIC-data-domain-decoupling Story-2 — io reader relocated to mctrader-data + engine NAS 직독 폐기 **예고**)

본 amendment box = EPIC-data-domain-decoupling Story-2 (MCT-183, sequential_phase 2) Phase 1 박제분.
**relocate 박제 + 예고** — io reader 6 module 의 거주 repo 가 `mctrader-engine` → `mctrader-data`
(Layer2 단독 소유) 로 이전됨. **io reader 6 module 의 동작·invariant 는 무변경** (거주 repo 만
이전 — relocate ≠ 재구현). 실 NAS 직독 폐기 confirm 은 **MCT-185 (cold-read cutover) owner**.

**io reader 6 module relocated 박제 (D2 io-relocate 절반, ADR-031 §D2)**:

- 본 ADR §D7 (MCT-170 amendment) impl scope 박제 `mctrader_engine/io/tier_reader.py` /
  `l1_reader.py` / `dr_mode.py` / `reader_cache.py` + §D8 amendment `cold_reader.py` /
  `endpoint_router.py` = engine `src/mctrader_engine/io/` 6 module 전체 → mctrader-data
  `src/mctrader_data/io/` 서브패키지로 **물리 이전** (byte-equivalence — 코드 본문 무변경,
  import path cross-reference 재지정만).
- 이전 근거: engine `src/` io/ 6 module production 호출자 = **0** (verified-via git grep
  origin/main HEAD 2026-05-16, 3-modal: `from/import mctrader_engine.io` io/제외 0건 + bare
  심볼 0건 + io/__init__.py 내부 6 self-import 만). MCT-170 자산이 production 미배선
  (dead-in-prod) — 삭제 후 engine import 깨짐 0.
- **io reader 6 module 의 D7=A (reader cache 95% hit + p99 <100ms) / D8=C (DR mode +
  local fallback) / D1=C / D4=B / D5=C 동작·invariant 는 거주 이전 후에도 무변경 보존**
  (DR state machine CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER / endpoint atomic flip / LRU byte
  budget / ETag verify / mixed layout 호환 전수 byte-equivalence). MCT-170 amendment 박제분
  (dr_mode.UNKNOWN_TIER 신규 + cutoff enforcement + READER_CACHE_TTL env) = invariant
  보존 거주 이전.
- **Phase 0 verify 발견 (MCT-183 설계 lane, R1 가드 — 코드 작업 전 사전 차단. 설계리뷰
  iter1 P0-3 executable hunk 재실측 정정)**: `mctrader_engine/io/reader_cache.py` `stats()`
  메서드 본문 내 producer-wiring **블록 line 339-348** (주석 1줄 + `from
  mctrader_engine.metrics import set_reader_cache_hit_ratio, set_reader_p99_ms` lazy
  import 6줄 multi-line + 빈줄 + `_set_hit_ratio`/`_set_p99_ms` 호출 2줄. FIX-MCT-180
  engine#55 P1 producer wiring, MCT-180 LAND 자산) 존재. Story §0 V5 top-level grep 가
  미포착한 io/ → engine 비-io 의존 1건. byte-equivalence relocate 시 mctrader-data →
  mctrader-engine 역의존 발생 (Layer2 자족 INV-2 위반 + 순환 위험) → **MCT-183 Change
  Plan §3.5 채택안 A 확정** = data 측 외부 import 없는 내부 no-op 블록 치환 (Prometheus
  Gauge producer wiring 의 data 측 처리 — relocate scope 경계, Gauge 실 emit 재배선 =
  MCT-185 cutover owner). docker-stack Phase 0 verify gap 6회 + MCT-179→180 metric/
  producer-path desync 동형의 **7회째 사전 차단** (MCT-182 R1 가드 패턴 계승 — 코드
  영구 영향 전 설계 lane 발견).

**engine NAS 직독 폐기 예고 (실 amend confirm = MCT-185)**:

- engine 실제 cold-read 경로 (`mctrader_data.storage.scan_candles` ×3 /
  `orderbook_replay` ×2 / `path.resolve_data_root` ×3 직독) = 본 ADR §D9 (MCT-167
  amendment) "NAS = SoT for ALL tiers" 의 engine read carrier. MCT-185 (cold-read
  cutover) 이 engine 의 mctrader_data.storage 직독 → data REST API indirection 전환
  예정 — 이 시점에 본 ADR §D9 의 "engine read-through cache" 모델이 data REST
  뒤로 indirection 됨. **본 MCT-183 amendment box 는 예고만 박제** — §D9 본문 +
  cross-ref 의 실 amend confirm 은 **MCT-185 owner** (scope_manifest
  `§planned_adrs.amendments` ADR-029 owner `MCT-183 (relocate) + MCT-185 (cutover
  confirm)` 1:1 정합).

**D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply — R1 가드)**:

scope_manifest `§design_decisions.D2` (`option_chosen: io-relocate + cold-read-behind-REST`
/ `owner_story: MCT-183 (io relocate) + MCT-185 (cold-read cutover)`) ↔
`§planned_adrs.amendments` ADR-029 (`section: engine NAS 직독 폐기 + io reader relocated +
NAS SoT 경로 data REST indirection` / `owner_story: MCT-183 (relocate) + MCT-185 (cutover
confirm)`) ↔ `§story_decision_matrix.MCT-183` (`decisions: [D2, D6]`) ↔ 본 amendment box
**전수 1:1 정합** (MCT-182 D-row 7/7 reconcile 패턴 계승, cross-document SSOT desync
사전 차단).

cross-ref: `docs/stories/MCT-183.md` §0/§4.3 + `docs/change-plans/MCT-183-change-plan.md`
§3/§8.0 + `docs/adr/ADR-031-data-domain-decoupling.md` §D2 (io-relocate 절반 진행, §D2
VERIFIED = MCT-185 cutover 후) + ADR-027 MCT-183 amendment box (io reader 6 module
(endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to
mctrader-data Layer2).

### MCT-172 amendment (2026-05-14) — D8 sunset policy finalize + D9 + D10 verify status

본 amendment = EPIC-tier-promotion-single-source Story-6 (MCT-172) Phase 1 박제분. Epic 의 **policy finalize Story**.

**D8 sunset policy finalize (D8-3=A + D8-4=C Codex 채택)**:

- **시점 cutoff**: 2026-09-01T00:00:00Z (MCT-170 amendment 박제분 유지)
- **telemetry 14d window**: **2026-08-18T00:00:00Z ~ 2026-09-01T00:00:00Z** (cutoff 직전 14d, D8-4=C Codex 채택). MCT-170 amendment 의 "0-hit 연속 14d" 의 기준점 = cutoff 직전 14d 로 명시 finalize.
- **rolling 0-hit metric**: `nas_reader_ambiguity_total` Counter 14d rolling rate = 0/min 의무 (Prometheus alert rule 박제)
- **combined criterion (AND)**: cutoff timestamp 도달 **AND** 14d window 내 telemetry rate = 0 충족 → D8 local fallback 영구 disable
- **실 sunset 실행**: 2026-09-01 별 Story or scheduled cron (telemetry watcher 측 alert rule trigger 시 별 PR 발의)
- **본 Story (MCT-172) scope**: policy finalize + telemetry watcher 박제 only. 실 sunset 실행은 후속.

**D9 verify status (MCT-172, 2026-05-14)**:

- **D9=A VERIFIED**: MCT-161 (NAS bucket versioning, 2026-05-14 LAND) + MCT-163 (DualWriter streaming, 2026-05-14 LAND) ALL LAND prerequisite 충족. Epic 진입 sequential gate PASS. EPIC-tier-promotion-single-source MCT-167~171 LAND 박제분.

**D10 verify status (MCT-172, 2026-05-14)**:

- **D10=A VERIFIED**: ambiguity invariant SSOT = `mctrader-data/src/mctrader_data/nas_migration/invariant_harness.py:140` `_INVARIANT_NAMES` tuple + `_check_ambiguity` method (MCT-171 LAND, 8번째 invariant 통합).
- **MCT-172 cleanup VERIFIED** (mctrader-data#63 f2fb28e, 2026-05-14T14:02:48Z): `compactor/promotion.py` 측 `verify_no_ambiguity` + `_check_nas_exists` 함수 **제거** (89 lines deleted) + caller migrate (D8-5=A Codex 채택). `grep -rn "verify_no_ambiguity" src/` = **0건** (AC-4 strict). caller migrate: `tests/integration/compactor/test_ambiguity_invariant.py` 6 test + `tests/integration/test_invariant_harness_8.py::test_mct169_d10_regression` → `InvariantHarness._check_ambiguity()` SSOT 경유. `AmbiguityViolation` exception class 는 보존 (외부 caller backward compat 가능성). SSOT 단일 보존 invariant.
- **telemetry watcher VERIFIED**: `tests/integration/test_d8_sunset_telemetry_watcher.py` 신규 + 8 test ALL PASS — `nas_reader_ambiguity_total` Counter 14d rolling rate 측정 mock + Prometheus alert rule format verify + AND condition verify + Epic CLOSED prerequisite list 박제.

**Epic CLOSED prerequisite (D8-9=C Codex 채택)**:

본 MCT-172 LAND 후 Epic CLOSED 박제는 별 PR/Story 의무:

1. **production deploy 후 14d 0-hit telemetry** (2026-08-18 ~ 2026-09-01)
2. **WAL 30G production measurement** (R-CRITICAL carry over from MCT-171, peak market open 09:00 KST burst, 30G 초과 시 D11 hard_limit amendment 발의)
3. **production evidence quad 동일 1h window** (bucket + log + Prometheus + drainage, D8-8=A Codex 채택, codeforge-plugin#620 Fix-1 정합)
4. **Epic CLOSED 박제 PR or scope_manifest amend** (POLICY_FINALIZED → CLOSED transition)

본 amendment 박제 시점 Epic status: **POLICY_FINALIZED** (Epic CLOSED 아님).

### D4+D5+D11 verify status (MCT-171 LAND, 2026-05-14)

- **D4=B VERIFIED** (mctrader-data#62, 3fb9d60): WAL sealed segment NAS PUT 경로 부재 확인. `compactor/promotion.py` DEPRECATED 주석 박제. `wal/` module 내 NAS 업로드 호출 0 (grep verify). RPO=0 보장 = D1 (L1 ParquetWriter atomic NAS PUT) 단독 의존 구조 확인.
- **D5=A_modified VERIFIED** (mctrader-data#62): `ingest_blocker.py` 신규 — WAL/L1 95% threshold 도달 시 graceful drain 후 신규 ingest reject. `collector.py` IngestBlocker hook 통합. 80% warn + 95% block + 90% unblock hysteresis (D7-8=C Codex 채택). 15 tests PASS.
- **D6=B partial** (MCT-161 prerequisite VERIFIED, MCT-174 defer): bucket versioning ✓ (MCT-161 LAND, 2026-05-14). cross-NAS replication = MCT-174 defer (mcnas02 물리 미설치). D6=B 완전 달성 = MCT-174 진입 후.
- **D11=capacity_bounded VERIFIED** (mctrader-data#62): `capacity_probe.py` 신규 — 4 layer hybrid probe (WAL 30G / L1 20G / NAS 1TB hard / Host 200G). `CapacityThresholds` SSOT 상수. `prometheus_exporters.py` +5 metric 확장 (capacity Gauge × 2 + violation Counter + latency Histogram + ingest blocked Counter). 15 tests PASS.

### MCT-170 amendment (2026-05-14) — D8 sunset criterion 박제 + D10 exemption scope 명시

본 amendment = EPIC-tier-promotion-single-source Story-4 (MCT-170) Phase 1 박제분. 본 ADR §D8 + §D10 의 implementation gap (sunset criterion 미명시 + cutoff 판정 불가 legacy partition 처리 미명시) 해소.

**D6=D 결정 박제 (D8 sunset criterion)**:

- **시점 cutoff**: 2026-09-01T00:00:00Z (hard sunset, MCT-172 Epic CLOSE gate)
- **telemetry verification**: local fallback hit 0건 연속 14d → auto disable trigger
- **combined criterion**: cutoff timestamp 도달 **AND** telemetry 0-hit 14d 충족 → D8 local fallback 영구 disable. MCT-172 Epic CLOSED gate 의무.
- **env override**: `READER_LOCAL_FALLBACK_CUTOFF` env (default = 2026-09-01T00:00:00Z, 운영 재조정 가능)

**D10 exemption scope (cutoff 판정 불가 legacy)**:

- **dr_mode.UNKNOWN_TIER 상태 신규** — partition path 분석 시 tier 판정 불가 (manifest 부재 + filename schema 부적합) 검출 시 진입.
- **fallback 거부 정책**: UNKNOWN_TIER 진입 시 local fallback 자동 거부. INV-1 SoT exclusivity (XOR) preserve.
- **Prometheus emit**: `nas_reader_ambiguity_total` counter — UNKNOWN_TIER 진입 빈도 추적.
- **30d exemption window**: 본 amendment 박제 시점 (2026-05-14) 기준 30d 동안 (~2026-06-13) UNKNOWN_TIER 진입 허용 + 운영자 alert. window 종료 후 enforcement strict (UNKNOWN_TIER 진입 = invariant violation 검출).

**implementation scope (MCT-170 Phase 2)**:

- `mctrader_engine/io/tier_reader.py` 신규 — facade orchestration (priority chain: cache → NAS L1/L2/L3 → local fallback)
- `mctrader_engine/io/l1_reader.py` 신규 — L1 tier specialized read (prefix `tier=L1/`)
- `mctrader_engine/io/dr_mode.py` 신규 — state machine (CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER) + explicit mode flag override + Prometheus
- `mctrader_engine/io/reader_cache.py` 갱신 — byte-size LRU budget enforcement (max_bytes 추가, MCT-154 API preserve)
- `mctrader_engine/io/cold_reader.py` + `endpoint_router.py` = **수정 0** (backward compat preserve, D9=A)

cross-ref: `docs/stories/MCT-170.md` + `docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md` + `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`. 본 ADR 은 ADR-017 (hot path WAL/L1) + ADR-027 (cold tier L2/L3) 의 누적 운영 evidence (MCT-156/162/160 3-cycle 누적 실패 patterns) 를 근거로 cold tier governance 의 **single source of truth 모델 격상** 을 박제. ADR-017 의 zero-loss invariant + ADR-027 의 cold tier S3 abstraction 은 본 ADR 의 입력 정합 — 본 ADR 의 D1 (L1 NAS PUT 의무) + D3 (immediate local delete after verify) + D10 (ambiguity invariant) 가 새로운 cross-tier governance 의 anchor.

## 해소 기준

**N/A — permanent governance policy**. 본 ADR 은 NAS = single source of truth 전면 재설계 의 anchor governance. cold tier storage backend 변경 (e.g., 외부 cloud object storage 전환) 시점은 별 ADR (successor) 로 처리. 본 ADR scope = NAS MinIO + on-prem 운영 의 영구 정책.

## Context

### WHY (3-cycle 누적 실패 patterns)

MCT-156 (Stage 3 wiring deploy) / MCT-162 (channel parity) / MCT-160 (cold-path memory invariant) 3 Story cycle 누적 실패 pattern:

- **review lane PASS vs production 실측 결함** — 리뷰 시 모든 invariant PASS but production 실측 에서 (a) 4.2 GiB / 1370 obj NAS 측 손실 (MCT-153, MCT-161 verify) (b) 48,629 sealed segment silent skip (MCT-162) (c) raw memory OOM risk (MCT-160 F6) 발견.
- **근본 원인 = local-NAS dual-storage ambiguity** — 현재 cold tier (L2/L3) 만 NAS 격상 + hot tier (WAL/L1) = local only. read path 측 "어디까지가 진실의 source 인지" 모호 → review evidence 가 production 실측을 lag.
- **fix 방향** — NAS = single source of truth 전환으로 ambiguity 차단 + production evidence direct surface. (codeforge-plugin#620 post-mortem Fix-1 production evidence gate 의 mctrader-consumer 측 implementation 정합).

### 사용자 directive (autonomous, 2026-05-14)

1. **L1 도 NAS dual-write** — collector WAL → L1 ParquetWriter atomic 직후 NAS PUT 의무. ADR-027 §D5 "L1 NAS upload 금지" invariant 폐기.
2. **상위 tier promotion 후 local delete** — L1 → L2 promote 시 L1 local 삭제, L2 → L3 promote 시 L2 local 삭제. NAS = single source of truth, local = ephemeral cache only.
3. **ambiguity 차단** — 현재 dual-storage (local + NAS) 의 "어디까지가 진실의 source 인지" 모호 차단.
4. **WAL Local 유지** — WAL = local only (hot path zero-loss, ADR-017 정합).
5. **로컬 용량 제한** — WAL 30 GiB + L1 20 GiB + NAS 500 GiB target + host 200 GiB hard limit. 임계 도달 시 (D5 capacity-bounded) collector ingest block.

### Cross-Epic prerequisite trail (D9 정합)

- **MCT-161 (LAND 2026-05-14, PR #301 + #302)** — NAS bucket versioning Enabled + Object Lock governance 30d + ADR-027 §D MCT-161 amendment + DR runbook stub. D6 cross-NAS replication 의 versioning prerequisite 충족.
- **MCT-163 (LAND 2026-05-14, PR #303 + #304)** — DualWriter put_streaming + L2/L3 iter_batches per-batch write + ADR-009 §D2.7 amend. R1 (L1 NAS PUT latency) mitigation prerequisite 충족 — streaming 모드 enable.

### ADR Relationships (사전 박제)

- **ADR-017 successor_of (확장)**: ADR-017 §3 D3 의 cold tier (L2/L3) NAS 격상 + 본 ADR 에서 hot tier (L1) NAS dual-write 의무 확장. ADR-017 의 zero-loss invariant (WAL per-message fsync) = 본 ADR 의 D1 (L1 NAS PUT) 와 직교 (L1 NAS PUT fail 이 hot path WAL 에 propagate 0, retry_queue 흡수).
- **ADR-027 successor_of (확장)**: ADR-027 §D5 "L1 NAS upload 금지" invariant **폐기** (D1=B). ADR-027 §D7 local GC 7일 grace 정책 = L1 tier 에 대해 grace 0 (D3=C, NAS HEAD verify 후 immediate delete) 로 확장. ADR-027 §D9 reader SoT = cold tier only → all-tier 격상 (D8 정합).
- **ADR-009 amends (확장)**: §D12.2 forward-only invariant 의 enforcement layer = local file system → NAS object SoT (versioning 기반, MCT-161 박제) 격상. tier promotion 후 local delete = forward-only 위반 0 (D3=C ambiguity 차단).
- **ADR-016 complements**: admin_audit.sqlite cold archive = 본 ADR scope 외 (ADR-027 §D11 정합).
- **ADR-026 references**: legacy candle provenance immutable invariant = 본 ADR 의 forward-only 확장과 정합.

## Decision

### D1. L1 NAS PUT timing — L1 ParquetWriter atomic 직후 (B 채택)

L1 NAS PUT 의 trigger 위치 = **L1 ParquetWriter atomic rename 직후, compactor 측** (sealed → L1 compaction completion path):

- **위치**: `mctrader_data/compactor/l1.py` 의 ParquetWriter close + fsync + atomic rename `tmp/<target>.parquet.tmp` → `<target>.parquet` 직후 호출.
- **호출 primitive**: `DualWriter.put_streaming(path)` (MCT-163 LAND 산출물 재사용) — local L1 file 을 streaming 으로 NAS PUT.
- **Rationale**: 파일 단위 정합성 + hot path 지연 균형. compactor 가 sealed WAL → L1 derive 의 atomic boundary 이므로 본 timing 이 NAS replica 의 atomic 보장 anchor. WAL sealed segment 가 D4 (WAL local only) 의 mitigation (sealed → L1 derive fail 시 sealed 재처리 가능).
- **Alternative rejected** (A — collector 측 L1 ParquetWriter inline NAS PUT): collector hot path 측 NAS PUT 의 latency / NAS unreachable 영향 직접 propagate → 거부. compactor = async / batched path 라서 R1 mitigation 자연 정합.
- **Consequence**: compactor L1 path 가 D2 (DualWriter retry_queue) + D5 (capacity-bounded ingest block) 의 cross-cut anchor.

### D2. NAS PUT 동기/비동기 — DualWriter retry_queue + local_only 재사용 (B 채택)

NAS PUT 의 동기/비동기 모델 = **기존 DualWriter retry_queue + local_only 모드 재사용** (MCT-150/151 primitive 답습):

- **logical sync** = caller (compactor L1 path) 측에서 보면 동기 호출. NAS PUT fail 시 DualWriter 내부 retry_queue 에 enqueue + caller 에는 success return (local file 보존 = retry source).
- **NAS unreachable 시** = `local_only` mode 전이 (NASUnreachableSOPRunner, MCT-152 primitive). hot path block 0 — local L1 file 보존, retry_queue 가 NAS 복구 시 PUT 재시도.
- **D5 capacity-bounded 조건**: WAL 30 GiB / L1 20 GiB hard limit 도달 시점에만 collector ingest block (D11 정합). 정상 운영 시 hot path 영향 0.
- **Rationale**: MCT-150/151 primitive (NASUploader + DualWriter + RetryQueue + InvariantHarness) 재사용 → 신규 코드 최소 + 이미 prod 검증된 path. caller 동기 호출 model 이 compactor pipeline 의 단순성 보존.
- **Alternative rejected** (A — fully async fire-and-forget): caller 측 retry semantic 부재 → NAS PUT loss 의 visibility 0. D10 (ambiguity invariant) 위반 risk → 거부.
- **Consequence**: MCT-168 impl scope = `mctrader_data/compactor/l1.py` 에 DualWriter inject + `mctrader_data/nas_storage/dual_writer.py` 에 L1 mode 추가 (필요 시).

### D3. Local delete = NAS HEAD verify + grace 0 (C 채택, Researcher↔PMO 충돌 해소)

Tier promotion 후 local file delete 정책 = **NAS HEAD verify + grace 0 (immediate after verify)**:

- **L1 → L2 promotion** 시: L2 NAS PUT 완료 + L2 NAS HEAD verify (version/etag exact match + sha256 verify) 후 즉시 local L1 file 삭제.
- **L2 → L3 promotion** 시: L3 NAS PUT 완료 + L3 NAS HEAD verify 후 즉시 local L2 file 삭제.
- **L1 local delete (Tier promote 없을 때)**: L1 NAS PUT 완료 + L1 NAS HEAD verify (4중: ETag+VersionId+sha256 metadata+ContentLength, D-4 C) + pre-delete HEAD guard (D-8 B) 후 즉시 local L1 file 삭제 — **grace 0 unconditional** (promotion path 와 동일, terminal path 7-day FIFO grace 표현 폐기, MCT-189 amendment 2026-05-16 D-1 A). 20 GiB hard limit 도달 시 추가 graceful drain (`nas_uploader.head_object` retry 강화), unlink trigger 자체는 NAS verify pass 시점 무조건.
- **verify primitive**: `NASUploader.head_verify(key, expected_etag, expected_sha256)` (MCT-150 primitive 확장). version/etag exact match + sha256 verify 가 false delete risk mitigation.
- **Rationale (Researcher↔PMO 충돌 해소)**: Researcher 원안 = "24h grace + dry-run" (ADR-027 §D7 답습) 였으나 PMO 측 "ambiguity 즉시 차단" directive 우선. version/etag 검증으로 24h grace 대체 = 강한 invariant 보증 + ambiguity 차단.
- **Alternative rejected** (A — 24h grace): ambiguity window 24h 잔존 → D10 invariant 약화 → 거부. (B — sha256 verify only without version): version 부재 시 race condition (overwrite 도중 verify) 발생 가능 → 거부.
- **Consequence**: MCT-169 impl scope = `mctrader_data/compactor/promotion.py` 신규 module + `tests/integration/test_l1_local_delete.py` 신규.

### D4. WAL sealed segment — local only 유지 (B 채택, 사용자 directive 3)

WAL sealed segment 의 NAS PUT 정책 = **local only 유지** (사용자 directive 우선):

- WAL sealed segment (`*.ndjson.sealed`) = local volume only, NAS PUT 부재. ADR-017 의 hot path zero-loss invariant 보존.
- **RPO=0 보장 의존 chain**: D1 (L1 ParquetWriter atomic 직후 NAS PUT) 단독 의존. WAL sealed → L1 derive 완료 + L1 NAS PUT 완료 시점에 NAS 측 RPO=0 도달.
- **Rationale**: 사용자 directive 2026-05-14 명시 — WAL local 유지. Codex 원 권고 = C (sealed NAS PUT) 였으나 사용자 directive 가 B 채택. WAL local fail 시 sealed → L1 derive fail risk = D11 용량 제한 (WAL 30 GiB hard limit) + D5 collector ingest block 으로 mitigation.
- **Trade-off**: WAL local disk corruption 시 last seal 이후 unsealed 구간 = 손실 (sealed 까지는 atomic rename 보존). 본 risk 는 ADR-017 D4 (per-message fsync) 의 통상 risk 와 동일 — 신규 risk 0.
- **Alternative rejected** (C — sealed NAS PUT, Codex 원 권고): WAL sealed 의 NAS PUT 추가 = hot path 추가 NAS 의존 → 사용자 directive 위반 → 거부.
- **Consequence**: MCT-171 impl scope = WAL local hard limit 30 GiB invariant 박제 + Grafana alert (WAL local 80% / 95% threshold).

### D5. NAS unreachable 시 collector ingest block — capacity-bounded (A_modified 채택)

NAS unreachable 동안의 collector ingest 정책 = **capacity-bounded ingest block**:

- **정상 NAS 운영 시** = collector hot path 영향 0. NAS PUT fail 은 DualWriter retry_queue 흡수 (D2 정합).
- **NAS unreachable 시** = local_only mode 전이 (MCT-152 NASUnreachableSOPRunner). collector ingest 지속 — WAL local persist, L1 local persist.
- **D11 hard limit 도달 시** = collector ingest block. 임계 trigger:
  - WAL local volume usage >= 30 GiB → collector SIGTERM-like soft stop (graceful + alert)
  - L1 local volume usage >= 20 GiB → L1 compactor pause (NAS verify 까지 대기, 새 L1 derive 차단)
- **alert chain**: NAS unreachable 검출 + capacity 80% threshold + 95% threshold + hard limit → Grafana alert + Slack notification (D11 의무).
- **Rationale**: 사용자 directive 5 (RPO=0 우선) + 정상 운영 시 hot path 영향 0 의 balance. capacity 임계 trigger 가 forward-only data loss 의 fail-safe (block 이 ingest loss 보다 우선).
- **Alternative rejected** (A 원안 — NAS unreachable 즉시 block): hot path 영향 직접 propagate, 정상 운영 시 false positive → A_modified 로 변경 (capacity-bounded only). (B — block 부재): WAL 무한 누적 → host disk overflow → 거부.
- **Consequence**: MCT-171 impl scope = capacity monitor + ingest block trigger + alert chain.

### D6. NAS replication — bucket versioning + cross-NAS replication (B 채택)

NAS 데이터 보호 정책 = **bucket versioning + cross-NAS replication** (2nd NAS box mcnas02):

- **bucket versioning** = MCT-161 LAND 완료 (Enabled + Object Lock governance 30d + NoncurrentVersionExpiration 30d). 본 ADR 의 prerequisite 충족.
- **cross-NAS replication** = mcnas01 (primary) → mcnas02 (replica) async replication. MCT-161 D2=D 결정 (replication deferred) 의 follow-up = **MCT-174 별 backlog Story** (현재 mcnas02 NAS box 물리 부재). 본 Epic 의 D6 = "replication 의 정책 박제" only, 실 deploy 는 MCT-174 의무.
- **DeleteMarker replication** = OFF (MCT-161 D4 결정 답습). 향후 replication 도입 시 적용 의무.
- **Rationale**: single NAS 장애 + overwrite/delete 실수 동시 완화 의 dual mitigation. versioning = 의도치 않은 delete/overwrite 복원 + replication = NAS 하드웨어 장애 복원.
- **Alternative rejected** (A — versioning only): single NAS 하드웨어 장애 시 복원 불가 → 거부. (C — replication only): 의도치 않은 delete 복원 불가 (replica 에도 동기 propagate) → 거부.
- **Consequence**: 본 ADR 에서는 정책 박제 only. mcnas02 도입 + replication 활성화 = MCT-174 의무.

### D7. Reader cache — 95% hit + <100ms p99 (A 채택)

Reader read-through cache 정책 = **aggressive cache (95% hit + p99 <100ms 목표)**:

- **cache backend**: engine 호스트 측 LRU/TTL cache (ADR-027 §D9 read-through pattern 답습). NAS = SoT, local cache = read latency optimization only.
- **target metric**: cache hit ratio >= 95%, p99 latency < 100ms (hot read 기준, MCT-148 T2 baseline 50MB p99 2870.65ms 대비 28x 단축).
- **eviction policy**: LRU + TTL (1h L1 / 24h L2 / 7d L3 권장 — MCT-170 impl 시 finalize).
- **Rationale**: NAS 우선 reader 의 hot path 체감 지연 억제. 95% hit / p99 <100ms 가 engine strategy/backtest 의 latency budget 정합.
- **Alternative rejected** (B — passive cache, 75% hit): hot read miss 빈도 증가 → p99 latency 5-10x 악화 → 거부. (C — no cache): NAS GET 매번 → 거부.
- **Consequence**: MCT-170 impl scope = `mctrader_engine/io/reader_cache.py` LRU L1 추가 + `tier_reader.py` 신규 + cache hit metric Prometheus export.

> **MCT-170 amendment (2026-05-14) — D7=C env configurable 채택 박제**: TTL per-tier 권장값 (1h L1 / 24h L2 / 7d L3) 은 **default**, env override 가능. `READER_CACHE_TTL_L1` / `_L2` / `_L3` env (seconds). production hit ratio + p99 측정 후 운영 tuning 허용. effective config Prometheus emit 의무.

### D8. 기존 local data migration — forward-only + local fallback (B 채택)

Migration 전략 = **forward-only + local fallback (migration window 동안)**:

- **새 데이터 (cutover 이후)** = D1 정합 (L1 NAS PUT 의무). forward-only invariant 자연 적용.
- **기존 local data (cutover 이전)** = local 보존, NAS migration 의무 0. engine reader 가 local fallback (NAS GET miss 시 local Path read) 박제.
- **bulk migration** = 권고 부재. 점진적 자연 누적 (legacy data 는 query 시 local fallback, 새 query 는 NAS-first).
- **migration window 종료** = local data lifecycle 자연 expiry (L1 7-day rolling FIFO, L2/L3 30-day archive promote 등) 시점.
- **Rationale**: bulk 전환 risk 회피 + ADR-027 §D9 MCT-159 amendment (mixed layout 본문 재해석) 답습. forward-only invariant 보존 + emergency fallback 보존.
- **Alternative rejected** (A — bulk migration up-front): migration 일관성 risk + 시간 소요 → 거부. (C — local data 폐기): backward read 불가 → 거부.
- **Consequence**: MCT-170 impl scope = `endpoint_router.py` NAS-first + local fallback path + `cold_reader.py` mixed layout 지속 지원.

> **MCT-170 amendment (2026-05-14) — D6=D sunset criterion 박제**: 본 ADR Status 섹션 §"MCT-170 amendment" 박제분 참조. 시점 cutoff (2026-09-01T00:00:00Z) + telemetry 0-hit 14d + MCT-172 Epic CLOSE gate combined. `READER_LOCAL_FALLBACK_CUTOFF` env override 가능. MCT-170 impl scope 확장: `tier_reader.py` 측 cutoff_timestamp 인지 + cutoff 이후 partition fallback 거부 enforcement.

### D9. MCT-161 + MCT-163 prerequisite — sequential ✓ (A 채택)

본 Epic 진입 = **MCT-161 + MCT-163 둘 다 LAND 후 sequential 진입**:

- **MCT-161 LAND** = 2026-05-14 (PR #301 + #302). NAS bucket versioning + Object Lock + DR runbook stub.
- **MCT-163 LAND** = 2026-05-14 (PR #303 + #304). DualWriter put_streaming + L2/L3 iter_batches.
- **본 Story (MCT-167) 진입** = 2026-05-14 (본 ADR publish 시점).
- **Rationale**: versioning + streaming 전제 완성 후 시작 = 재설계 비용 < 일정 cost. cross-Epic prerequisite 자연 정합.
- **Alternative rejected** (B — parallel 진입): MCT-161 versioning 미 LAND 시 D6 prerequisite 위반 + MCT-163 streaming 미 LAND 시 R1 mitigation 부재 → 거부.
- **Consequence**: 본 ADR publish = MCT-161 + MCT-163 ALL LAND 시점에만 진입 (prerequisite verify gate). 충족 확인 완료.

### D10. Ambiguity 차단 — invariant violation enforcement (A 채택)

NAS+local 동시 존재 ambiguity 차단 = **invariant violation enforcement**:

- **invariant 정의** = "tier promotion 완료 후 동일 logical entity (schema_version × tier × exchange × symbol × date × hour × node) 가 NAS + local 양쪽 동시 존재 시 violation".
- **enforcement layer** = MCT-169 (`mctrader_data/compactor/promotion.py`) impl 시 invariant test 박제 (`tests/integration/test_ambiguity_invariant.py`).
- **violation 검출 시** = (a) immediate alert (b) local file 즉시 GC (NAS verify 완료 기준) (c) production evidence log 박제.
- **production evidence gate** = codeforge-plugin#620 Fix-1 production evidence gate 의 mctrader-consumer 측 implementation. review lane PASS 만으로는 불충분, production 실측 0 violation 의무.
- **Rationale**: 차단이 설계가 아닌 보증 — "현재 dual-storage (local + NAS) 의 어디까지가 진실의 source 인지 모호함 차단" 의 enforcement 보장.
- **Alternative rejected** (B — design-only 차단 (test 부재)): production drift risk → 거부.
- **Consequence**: MCT-169 impl scope = invariant test + MCT-172 impl scope = cross-Story verify (1h production 측정 0 violation 의무).

> **MCT-170 amendment (2026-05-14) — D10 exemption scope footnote**: cutoff 판정 불가 legacy partition (manifest 부재 + filename schema 부적합) 처리 정책 명시. dr_mode.UNKNOWN_TIER 상태 신규 + local fallback 자동 거부 + Prometheus `nas_reader_ambiguity_total` emit. 30d exemption window (2026-05-14 ~ 2026-06-13) 동안 alert + 운영자 검토, window 종료 후 enforcement strict (UNKNOWN_TIER 진입 = invariant violation). 본 ADR Status §"MCT-170 amendment" 박제분 참조.

> **MCT-189 amendment (2026-05-16) — D10 production evidence gate 강화 (D-6 A)**: `promote_l1()` caller wiring LAND 후 production evidence gate = ADR-032 evidence triad 형식 차용 ((1) file:line + (2) production caller `git grep` ≥1 + (3) integration test PASS). post-LAND 14d rolling `nas_reader_ambiguity_total` Counter = 0 의무 (Epic CLOSED prereq prod-5, 2026-05-16 LAND → 2026-05-30 verify gate). Phase 2 PR3 박제 시 Story §8.5 Impl Manifest 에 evidence triad 박제. decision-defined (MCT-169 promote_l1 정의) ≠ caller-wired (MCT-189) — VERIFIED badge 는 3 evidence 모두 충족 시에만.

### D11. 용량 제한 정책 — 4 layer 임계 (capacity_bounded 채택, 사용자 directive 1)

4 layer capacity 제한:

| Layer | Hard Limit | Threshold Action | Rationale |
|---|---|---|---|
| **WAL local** | 30 GiB | collector ingest block (D5 정합) | NAS 무한 장애 시에만 block, 정상 운영 시 hot path 영향 0 |
| **L1 local** | 20 GiB | DualWriter `status=committed` branch self-delete (D-2 A, grace 0) — NAS verify 4중 + pre-delete guard 후 즉시 unlink | NAS PUT commit boundary 안 즉시 unlink (D-1 A unconditional, MCT-189 amendment 2026-05-16 — "7-day grace 기본" 표현 폐기). 20 GiB 도달 시 graceful drain 추가 |
| **NAS bucket** | target 500 GiB / hard 1 TiB | L3 (oldest 30day+) cold archive 이전 (별 Story or 외부 cloud) | L3 daily archive forward 누적, 30day+ archive tier 후보 |
| **Host disk** | 200 GiB (사용자 환경 — Host C: 476 GiB 의 ~42%) | alert + manual cleanup | host disk pressure mitigation, mctrader 외 다른 영역과 공유 |

- **WAL 30 GiB** 도달 시 = collector ingest soft stop (graceful + alert). NAS 무한 장애 가정.
- **L1 20 GiB** 도달 시 = L1 oldest FIFO delete (NAS verify 후, D3 정합). 정상 운영 시 7-day rolling cleanup.
- **NAS bucket 500 GiB target** = L3 30day+ archive tier 이전 후보. hard 1 TiB 도달 시 별 Story 발의.
- **Host disk 200 GiB** = host 전체 mctrader 영역 hard limit. alert + manual cleanup (자동 GC 부재).
- **Rationale**: 사용자 directive 1번 (4 layer 임계) + D5 capacity-bounded ingest block 의 mitigation. 4 layer 분리가 layer 별 trigger 독립성 보장.
- **Alternative rejected** (A — single global limit): layer 별 trigger 부재 → fail mode 분기 곤란 → 거부.
- **Consequence**: MCT-171 impl scope = 4 layer capacity monitor + Grafana alert + WAL/L1 hard limit invariant.

## Migration

### Forward-only invariant (ADR-009 §D12.2 확장)

Tier promotion 후 local delete = forward-only 위반 0 (D3=C ambiguity 차단). NAS = single source of truth, local = ephemeral cache only. forward-only invariant 의 enforcement layer = local file system → NAS object SoT (versioning 기반, MCT-161 박제) 격상.

> **MCT-189 amendment (2026-05-16, D-5 A)**: local fallback 제거 격상. MCT-170 D8=B local fallback (cutoff 2026-09-01 sunset) 정합 + grace-0 wiring 정합 — local 부재 = NAS-only 정상 상태. NAS bucket versioning Enabled (MCT-161) + NoncurrentVersionExpiration 30d window = PITR/operational recovery 단일 보증 (ADR-027 §D7 7-day local grace motivation 흡수). host 200G hard limit 정합 (ADR-029 §D11). Researcher unknown #2 (backup window 손실) 해소 = versioning 30d 가 backup carrier.

### Phase 진입 순서 (MCT-167 → MCT-172 sequential)

| Phase | Story | Scope | Mode |
|---|---|---|---|
| 1 | **MCT-167 (본 ADR publish)** | governance singleton — ADR-029 신규 + ADR-017/027/009 amend 3건 + DR runbook stub | Phase 1 only (hub) |
| 2 | MCT-168 | L1 NAS DualWriter wiring (D1 + D2) | Phase 1+2 (data) |
| 3 | MCT-169 | L1 NAS verify + immediate local delete + tier promotion (D3 + D10) | Phase 1+2 (data) |
| 4 | MCT-170 ∥ MCT-171 | engine reader 재구현 (D7 + D8) ∥ DR runbook + invariant 8종 + 용량 제한 (D4 + D5 + D6 + D11) | Phase 1+2 (engine ∥ hub+data) |
| 5 | MCT-172 | EPIC 통합 smoke + ambiguity invariant verify + EPIC CLOSED (D9 + D10) | Phase 1+2 (hub+data+engine) |

## Consequences

### Pros

- **Ambiguity 차단** (D10) — NAS = single source of truth, local = ephemeral cache only. 3-cycle 실패 patterns 의 근본 원인 해소.
- **Forward-only invariant 보존** (ADR-009 §D12.2 확장) — NAS object SoT (versioning) 기반 enforcement, tier promotion 후 local delete = invariant 위반 0.
- **Hot path zero-loss 보존** (D4 WAL local only) — ADR-017 의 zero-loss invariant 보존, NAS unreachable 의 hot path propagate 0.
- **MCT-150/151 primitive 재사용** (D2) — NASUploader + DualWriter + RetryQueue + InvariantHarness 의 prod-검증 path 재사용 → 신규 코드 최소.
- **Production evidence gate** (D10, codeforge-plugin#620 Fix-1) — review lane PASS + production 실측 0 violation 의무, review-vs-production drift 차단.

### Cons

- **L1 NAS PUT latency overhead** (R1) — 50 sym × 3 channel × 12 seg/h ≈ 30 PUT/min compactor throughput 영향. MCT-163 streaming + MCT-148 T2 baseline ±15% gate 로 mitigation.
- **NAS unreachable 시 ingest block risk** (R2) — D5 capacity-bounded (WAL 30 GiB 도달 시) trigger 만, 정상 운영 시 hot path 영향 0. D6 cross-NAS replication (MCT-174) 의무.
- **WAL local only — sealed → L1 derive fail 시 RPO ≠ 0** (R3) — D4=B 사용자 directive trade-off. D5 ingest block + WAL 30 GiB hard limit + Grafana alert 로 mitigation.
- **Local delete false delete risk** (R4) — version/etag eventual consistency. etag exact match + sha256 verify + retry on NoSuchKey 로 mitigation.
- **MCT-154 engine reader 재구현 (MCT-170) — latency baseline 재측정 의무** (R5) — MCT-148 T2 baseline ±15% gate.

### Neutral

- **NAS bucket layout 변경 0** — 기존 `mctrader-market` bucket + Hive prefix 보존. schema migration 0.
- **MCT-167 reservation** — `.codeforge/counters.json` 의 MCT-167 reservation = 본 Story publish 후 PMOAgent retro 시 DELETE.
- **ADR-026 immutable invariant 정합** — legacy candle = forward-only, 본 ADR 의 NAS = SoT 격상과 자연 정합.

## Alternatives Considered

본 Decision 의 D1-D11 각 항목에 Alternative rejected 박제. 추가 high-level alternative:

### A. Local = SoT + NAS = backup (rejected)

NAS 를 backup-only 로 유지하고 local = SoT 모델. → ambiguity 잔존 (현재 ADR-027 §D5 와 본질 동일) + cross-Epic prerequisite (MCT-161 versioning) 의 의미 약화 → 거부.

### B. cold tier (L2/L3) only NAS = SoT, hot tier (L1) local only (현재 ADR-027 답습, rejected)

현재 ADR-027 의 status quo. MCT-156/162/160 3-cycle 실패 patterns 의 근본 원인. → 거부.

### C. Full NAS migration (WAL 포함, rejected)

WAL 도 NAS PUT 의무. → 사용자 directive 4 (WAL local 유지) 위반 + hot path zero-loss invariant (ADR-017) 약화 → 거부.

## References

### ADR cross-link

- ADR-017 (Zero-loss ingestion WAL + tiered compaction) — §3 D3 amend (L1 NAS PUT 의무)
- ADR-027 (Cold Tier Object Storage on NAS MinIO) — §D5 폐기 + §D7 grace 0 (L1) + §D9 SoT 확장
- ADR-009 (OHLCV schema) — §D12.2 forward-only invariant NAS object SoT 격상
- ADR-016 (Audit log immutability) — admin_audit.sqlite 별 Epic
- ADR-026 (Legacy candle provenance retirement) — immutable invariant 정합

### Story / Epic

- **EPIC-tier-promotion-single-source** (`scope_manifests/EPIC-tier-promotion-single-source.yaml`)
- **MCT-167** (governance singleton, 본 ADR publish) — `docs/stories/MCT-167.md`
- **MCT-168** (L1 NAS DualWriter wiring) — reserved
- **MCT-169** (L1 NAS verify + immediate local delete + tier promotion) — reserved
- **MCT-170** (engine reader 재구현) — reserved
- **MCT-171** (DR runbook 본문 + invariant 8종 + 용량 제한) — reserved
- **MCT-172** (Epic integration smoke + EPIC CLOSED) — reserved

### Prerequisite

- **MCT-161** (LAND 2026-05-14) — NAS bucket versioning + Object Lock + DR runbook stub. D6 prerequisite.
- **MCT-163** (LAND 2026-05-14) — DualWriter put_streaming + L2/L3 iter_batches. R1 mitigation.

### Plugin reference

- **codeforge-plugin#620 Fix-1** — production evidence gate. 본 ADR D10 의 mctrader-consumer 측 implementation.
