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
- **L1 local delete (Tier promote 없을 때)**: L1 NAS PUT 완료 + L1 NAS HEAD verify 후 즉시 local L1 file 삭제 (D11 L1 hard limit 20 GiB 도달 시점에만 trigger, 정상 운영 시 7-day FIFO grace).
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

### D11. 용량 제한 정책 — 4 layer 임계 (capacity_bounded 채택, 사용자 directive 1)

4 layer capacity 제한:

| Layer | Hard Limit | Threshold Action | Rationale |
|---|---|---|---|
| **WAL local** | 30 GiB | collector ingest block (D5 정합) | NAS 무한 장애 시에만 block, 정상 운영 시 hot path 영향 0 |
| **L1 local** | 20 GiB | oldest L1 FIFO delete after NAS verify (D3=C 정합, 7-day grace 기본) | raw_json large column 대형 (orderbooksnapshot 9.5 GiB/3day), 7-day rolling cleanup |
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
