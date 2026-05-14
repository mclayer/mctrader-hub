# mctrader-hub CLAUDE.md

mctrader 자동매매 platform governance hub. Story / ADR / Epic / cross-repo 조정. codeforge consumer.

## 프로젝트 구조

- `docs/stories/` — Story 파일 (MCT-NNN.md)
- `docs/adr/` — ADR (ADR-NNN-title.md)
- `docs/runbooks/` — 운영 runbook
- `docs/retros/` — RETRO + EPIC-RESULTS
- `docs/audit/` — 실행 결과 박제 artifact
- `docs/superpowers/specs/` — brainstorm spec
- `docs/superpowers/plans/` — implementation plan
- `scope_manifests/` — Epic scope_manifest YAML
- `scripts/` — NAS admin + 운영 스크립트
- `.codeforge/counters.json` — Story key reservation SSOT

## NAS versioning + Object Lock 현황 (MCT-161)

> Phase 2 land: 2026-05-14

### 설정 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| bucket versioning | **Enabled** | AC-1 PASS (2026-05-14T06:38Z) |
| Object Lock GOVERNANCE 30d | **SKIP** | 기존 bucket MinIO 제약 (--with-lock 생성 시점 의무) |
| Lifecycle NoncurrentVersionExpiration 30d | **Enabled** | AC-3 PASS |
| DR runbook | `docs/runbooks/nas-bucket-disaster-recovery.md` | AC-4 PASS |

### 운영 스크립트

- `scripts/enable_nas_versioning.py` — versioning + Object Lock + Lifecycle enable
- `scripts/verify_nas_versioning.py` — AC-1/2/3 verify (exit code 0=PASS)

```bash
# 환경변수 설정 후 실행
export NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
export NAS_MINIO_ACCESS_KEY=<access_key>
export NAS_MINIO_SECRET_KEY=<secret_key>
python scripts/verify_nas_versioning.py
```

### 제약 사항

- Object Lock은 bucket 생성 시(`--with-lock`) 활성화 의무. 기존 `mctrader-market`에는 적용 불가.
- NoncurrentVersionExpiration 30d — versioning 활성화(2026-05-14) 이전 null version은 복원 불가 (Edge-1).

## DR runbook (MCT-161 AC-4)

NAS data loss / hard delete 복원 절차:
- `docs/runbooks/nas-bucket-disaster-recovery.md` — 5-step (Triage / Version 조회 / Restore / Verify / Postmortem)
- 복원 가능 window: versioning 활성화 이후 + 30d NoncurrentVersionExpiration 이내

## Pending Stories (Replication Backlog)

| Story | 상태 | 내용 |
|-------|------|------|
| MCT-174 | RESERVED | NAS replication (D2=D 결정, single NAS box mcnas02 물리 부재 해소 후 진입) |

MCT-174 근거: ADR-027 §D MCT-161 amendment D2=D (replication deferred). INV-5 의무 = 후속 별 Story 예약 완료.

## Streaming refactor cross-ref (MCT-163, 2026-05-14)

### F3 DualWriter streaming

- `mctrader-data/src/mctrader_data/nas_storage/nas_uploader.py`: `put_streaming(Path|IO, key, sha256)` 신규
- `mctrader-data/src/mctrader_data/nas_storage/dual_writer.py`: `write(Path)` read_bytes 0 (streaming)
- INV-4: DualWriter peak RSS+TM delta ≤ 50 MB (105 MiB 실측: 0.2 MB / 0.0 MB)
- INV-3: sha256 SSOT caller-side (multipart ETag ≠ sha256)

### F6 L2/L3 iter_batches

- `mctrader-data/src/mctrader_data/compactor/l2.py`: `pq.ParquetFile.read()` → `iter_batches(1024)` + `write_batch`
- `mctrader-data/src/mctrader_data/compactor/l3.py`: 동형
- INV-4: L2/L3 peak RSS+TM delta ≤ 256 MB (300k rows 실측: 0.0 MB / 0.3 MB)
- INV-5: iter_batches per-batch write schema == 기존 L2/L3 schema

### EPIC-tier-promotion D9 prerequisite

- MCT-161 + MCT-163 모두 COMPLETED (2026-05-14)
- **MCT-167 (EPIC-tier-promotion governance singleton)** COMPLETED 2026-05-14 (PR #305, 1b83c28)
- **MCT-168 (L1 NAS DualWriter wiring — D1+D2 impl)** COMPLETED 2026-05-14 (hub PR #307 + data PR #59)
  - put_l1() 신규 + l1.py inject + runner pass-through + 22 tests ALL PASS
  - ADR-029 D1=B + D2=B VERIFIED (mctrader-data#59)
- cross-ref: `docs/retros/RETRO-MCT-163.md` + `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md`

## EPIC-tier-promotion-single-source (MCT-170 engine reader L1 확장 + DR mode LAND 2026-05-14)

> milestone 4/6 박제 (MCT-167 + MCT-168 + MCT-169 + MCT-170 COMPLETED)

### ADR 산출물

- **ADR-029** (신규, MCT-167 publish) — Cold tier governance v2 — NAS = SoT for ALL tiers (D1-D11 박제)
- **ADR-017 §3 D3 amendment** — L1 NAS PUT 의무 박제
- **ADR-027 §D5+D7+D9 amendment** — L1 NAS upload 금지 invariant 폐기 + L1 grace 0 + SoT all-tier 격상
- **ADR-009 §D12.2 amendment** — forward-only invariant NAS object SoT 격상

### 핵심 결정 (D1-D11)

| D | 결정 | Option | Owner Story |
|---|---|---|---|
| D1 | L1 NAS PUT timing — ParquetWriter atomic 직후 | B | MCT-168 |
| D2 | DualWriter retry_queue + local_only 재사용 | B | MCT-168 |
| D3 | Local delete — NAS HEAD verify + grace 0 | C | MCT-169 |
| D4 | WAL sealed local only 유지 | B | MCT-171 |
| D5 | Capacity-bounded ingest block | A_modified | MCT-171 |
| D6 | bucket versioning + cross-NAS replication | B | MCT-171 (MCT-161 ✓) |
| D7 | Reader cache 95% hit + p99 <100ms | A | MCT-170 |
| D8 | forward-only + local fallback migration | B | MCT-170 |
| D9 | MCT-161 + MCT-163 prerequisite sequential ✓ | A | epic-level ✓ |
| D10 | Ambiguity invariant violation enforcement | A | MCT-169 + MCT-172 |
| D11 | 4 layer capacity 제한 (WAL 30G / L1 20G / NAS 500G / Host 200G) | capacity_bounded | MCT-171 |

### DR runbook stub 확장

- `docs/runbooks/nas-bucket-disaster-recovery.md` — Epic-level scope (5 fail mode + invariant 8종 + 용량 4 layer placeholder)
- **본문 step-by-step = MCT-171 의무**

### 다음 Story (sequential)

- **MCT-168** COMPLETED 2026-05-14 (hub#307 + data#59) — D1+D2 VERIFIED
- **MCT-169** COMPLETED 2026-05-14 (hub#310 + data#60 + hub#311) — D3+D10 VERIFIED
- **MCT-170** COMPLETED 2026-05-14 (hub#314 + data#61 + engine#53 + hub#TBD) — D7+D8+D10 VERIFIED (hit_ratio=0.95 ✓ + p99=0.016ms ✓)
- **MCT-171** (DR runbook 본문, 진입 가능 — 별 세션 권고 + brainstorm 추가 의무) — D4+D5+D6+D11 owner
- MCT-172 (Epic CLOSED, D9+D10 verify + D8 sunset finalize)

## MCT-170 COMPLETED (2026-05-14) — Engine reader L1 확장 + DR mode + reader cache byte budget

> 4 PR cross-repo sequential LAND, D7 NFR 측정 PASS

### 측정 결과 (D7 NFR)

| 항목 | 결과 | gate | verdict |
|------|------|------|---------|
| hit_ratio (10k read benchmark) | 0.95 | ≥ 0.95 | PASS |
| p99 latency | 0.016 ms | < 100 ms | PASS (대폭 마진) |
| benchmark mean | 1.99 μs | — | ~503k OPS |

R4 mitigation iter 1 적용 (n_rounds 10→20 + cache max_bytes +50%, FIX-MCT-170-001).

### 4 PR LAND timeline

- mctrader-hub#314 (311b795) — Phase 1 docs (7 file)
- mctrader-data#61 (9d26438) — Phase 2 PR#1 LRU 구현 (20 신규 test)
- mctrader-engine#53 (a00690bc) — Phase 2 PR#2 3 module 신규 + 1 확장 (107 io/ test ALL PASS)
- mctrader-hub#TBD (본 PR) — Phase 2 PR#3 박제

### AC-1 ~ AC-7 PASS / INV-1 ~ INV-4 PASS

ALL PASS. MCT-154 backward compat 회귀 0 (cold_reader + reader_cache MCT-154 API + endpoint_router 전수 green).

### Phase 0 verify 발견 (중대 amendment)

session prompt 의 "engine reader 재구현 — 4 module 신규" 표현이 부정확. verified-via 결과 mctrader-engine `io/` 측 **MCT-154 LAND 3 module 존재** (1058 lines):
- `cold_reader.py` (319 lines) — L2/L3 specialized
- `reader_cache.py` (269 lines) — LRU+TTL 자체 구현
- `endpoint_router.py` (442 lines) — env-based + atomic flip + 7d grace mode

→ MCT-170 = **확장 + wiring** (재구현 아님): tier_reader facade + l1_reader + dr_mode 신규 + reader_cache byte budget 확장. cold_reader + endpoint_router = 수정 0 (backward compat preserve, D9=A).

counters.json + scope_manifest 모두 retitle 박제.

### §Engine reader L1 확장 (tier_reader facade + l1_reader + cold_reader preserve)

- `mctrader_engine/io/tier_reader.py` 신규 (Phase 2 PR#3) — facade orchestration (priority chain: cache → NAS L1/L2/L3 → local fallback)
- `mctrader_engine/io/l1_reader.py` 신규 — L1 specialized read (prefix `tier=L1/`, ETag verify)
- `mctrader_engine/io/cold_reader.py` 유지 — L2/L3 specialized (MCT-154 LAND preserve)
- `mctrader_engine/io/__init__.py` export 갱신 — TierReader / L1Reader / DRMode 추가
- D9=A backward compat: ColdReader 공개 API 유지, TierReader 신규 wrapper

### §DR mode state machine (CLOSED/OPEN/HALF_OPEN + explicit override + UNKNOWN_TIER)

- `mctrader_engine/io/dr_mode.py` 신규 (Phase 2 PR#3) — state machine + explicit mode flag override + Prometheus emit
- 4 state: CLOSED (정상) / OPEN (NAS 차단) / HALF_OPEN (probe) / UNKNOWN_TIER (D10 exemption)
- D8=C trigger hybrid: sliding window 60s 내 5xx 5회 OR p99 >500ms 3회 + consecutive failure 5회
- HALF_OPEN: OPEN 30s 후 자동 전이, probe 1회 success → CLOSED
- manual override: `set_mode(state, reason)` API (operator gate)
- Prometheus `nas_reader_dr_state` Gauge + `nas_reader_ambiguity_total` Counter

### §Reader cache byte budget (LRU+TTL + RSS bound)

- `mctrader_engine/io/reader_cache.py` 갱신 (Phase 2 PR#3) — byte-size budget enforcement 추가 (D2=C)
- `mctrader_data/compactor/reader_cache.py` 갱신 (Phase 2 PR#2) — NullReaderCache 제거 + LRUReaderCache 구현 (Protocol get/put/invalidate)
- `max_bytes` constructor param (default 256 MB)
- `current_bytes() -> int` method 신규 (Prometheus metric input)
- put() 측 enforcement: OrderedDict.popitem(last=False) 반복 while _current_bytes + len(value) > max_bytes
- D7=C TTL configurable env (`READER_CACHE_TTL_L1=3600` default), MCT-154 API preserve

### ADR-029 amendment (MCT-170 박제분, 2026-05-14)

- **Status section "MCT-170 amendment"** — D6=D sunset criterion + D10 exemption scope 명시 박제
- **§D7 amendment box** — D7=C TTL configurable env (default 1h/24h/7d, env override 가능)
- **§D8 amendment box** — D6=D sunset criterion (cutoff 2026-09-01 + telemetry 0-hit 14d + MCT-172 gate)
- **§D10 footnote** — dr_mode.UNKNOWN_TIER 상태 신규 + 30d exemption window (2026-05-14 ~ 2026-06-13) + Prometheus `nas_reader_ambiguity_total` emit

### 다음 Story 진입 권고

**MCT-171** (DR runbook 본문 + invariant 8종 + 용량 제한, D4+D5+D6+D11) — 별 세션 권고. brainstorm 추가 의무 (Phase 0 4 agent + Codex review). prompt path: `docs/superpowers/prompts/MCT-171-session-prompt.md` (작성 의무).

## Key References

- ADR-027 §D MCT-161 amendment: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
- **ADR-029 (신규, MCT-167 2026-05-14)**: `docs/adr/ADR-029-tier-promotion-single-source.md`
- EPIC-compactor-operations scope_manifest: `scope_manifests/EPIC-compactor-operations.yaml` (CLOSED 2026-05-14)
- **EPIC-tier-promotion-single-source scope_manifest**: `scope_manifests/EPIC-tier-promotion-single-source.yaml` (IN_PROGRESS, 4/6 milestone completed)
- **MCT-170 spec**: `docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md`
- **MCT-170 plan**: `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`
- **MCT-170 retro**: `docs/retros/RETRO-MCT-170.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md`
- **EPIC-RESULTS (tier-promotion, IN_PROGRESS)**: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- MCT-174 reservation: `.codeforge/counters.json`
