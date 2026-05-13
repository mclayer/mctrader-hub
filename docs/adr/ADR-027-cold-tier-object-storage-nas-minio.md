---
adr_id: ADR-027
title: Cold Tier Object Storage on NAS MinIO
status: Accepted
date: 2026-05-12
related_story: MCT-149
related_epic: EPIC-cold-tier-nas-minio
category: infra
is_transitional: false
successor_of:
  - ADR-017 (Zero-loss ingestion via WAL + tiered compaction)
complements:
  - ADR-016 (Audit log append-only with hash chain)
references:
  - ADR-008 (Secret management)
  - ADR-009 (OHLCV 16-col schema + forward-only invariant)
related_stories:
  - MCT-147 (NAS MinIO 컨테이너 deploy + bucket 초기화)
  - MCT-148 (Cold tier PoC spike — 5종 검증)
  - MCT-149 (본 ADR 본문 publish — Stage 1 종료 governance Story)
---

# ADR-027: Cold Tier Object Storage on NAS MinIO

## Status

Accepted — 2026-05-12. MCT-149 (EPIC-cold-tier-nas-minio Stage 1 종료 governance Story) 가 본 ADR 본문을 publish. 본 ADR 은 Epic Stage 1 (Feasibility Spike) 의 종료 gate — MCT-147 (NAS endpoint deploy MERGED, `mctrader-hub#246` 409d076) + MCT-148 (5 PoC PASS MERGED, `mctrader-data#40` d3e2af5) 의 누적 결과를 본문에 박제 (crystallize) 하여 status=Accepted 충족. Stage 2 (MCT-150~155 cold tier migration) 진입은 본 ADR merge 후 brainstorm Phase 0 재실행 권고.

## 해소 기준

**N/A — permanent policy**. 본 ADR 은 cold tier (L2/L3 compacted Parquet) 의 storage backend governance 정책 — 영구 운영. Stage 2 (MCT-155) 의 TLS 재검토 (D2 의 escalation 의무) 는 본 ADR 의 amendment 또는 supersede 로 처리 (해소 아님). cold tier storage backend 변경 (e.g., 외부 cloud object storage 로 전환) 시점은 별 ADR (successor) 로 처리 — 본 ADR 의 dormant 종결 정책 부재.

## Context

### WHY (호스트 디스크 용량 부족)

mctrader-data 의 `mctrader-collector` + `mctrader-compactor` 컨테이너가 forward-only Parquet 누적 (50 sym × ~6 month, 누적 ~수십 GB) + WAL segment + L1/L2/L3 tiered compaction 산출물 (ADR-017 §Decision D3) 을 단일 호스트 disk 에 저장. **호스트 disk 용량 압박** 이 cold tier 자산 (L2 1h Parquet + L3 1day Parquet, long-term archive 성격) 을 외부 storage backend 로 이관 동기.

### Stage 1 Feasibility Spike trail (MCT-147 + MCT-148)

본 ADR 의 Stage 1 종료 gate 충족 evidence:

- **MCT-147 (NAS endpoint deploy, MERGED 2026-05-12, `mctrader-hub#246` 409d076)**: Synology NAS DSM 7.2+ Container Manager 위 MinIO direct deploy (RELEASE.2025-04-08T15-41-24Z) + `mctrader-market` bucket bootstrap (idempotent) + 90일 credential rotation runbook + 4중 mitigation (.env 0600 / .gitignore / NAS 방화벽 ACL / IAM 분리) 박제.
- **MCT-148 (PoC spike, MERGED 2026-05-12, `mctrader-data#40` d3e2af5)**: 5 PoC PASS evidence pack (T1 HTTP health 2/2 / T2 latency baseline 4/4 / T3 large PUT 50MB 3/3 / T4 restart idempotency PASS / T5 partial visibility 1/1) — pytest 10 PASSED / 0 FAILED / 0 SKIPPED in 107.76s + T4 manual gate (recovery_ms=30.56). 본 ADR §Decision D8 evidence 직접 인용 source.

### WebDAV 우회 결정 (Synology Container Manager 위 MinIO direct deploy)

MinIO 의 `format.json` 등 atomic operation 은 **POSIX-compliant filesystem** 의무 (MinIO 공식 — `minio/minio#14060` 참조). NFS/SMB/WebDAV mount 위 MinIO data dir 배치는 unsupported — fsync semantic / atomic rename / file locking 미보장. 본 ADR 의 storage backend 결정:

- **A (rejected)**: 호스트 측에서 NAS WebDAV mount → mount path 를 MinIO data dir 로 지정. `minio/minio#14060` 의 unsupported 정책 + atomic op 실패 risk → 거부.
- **B (rejected)**: mctrader-data `cold_writer` 가 NAS WebDAV PUT 직접 수행 (MinIO 우회). S3 API 추상화 상실 → engine reader (ADR-017 D3 L2/L3 read) 측 분기 코드 폭증 → 거부.
- **C (chosen)**: NAS Synology Container Manager 위 MinIO 컨테이너 direct deploy + NAS local btrfs/ext4 volume 을 MinIO data dir 로 mount = application-layer S3 API 만 사용, POSIX semantic 의존 0. (§Alternatives 항목 상세)

### ADR Relationships (사전 박제, MCT-149 §3 정합)

- **ADR-017 후속 link (successor_of, 확장)**: ADR-017 §3 D3 (L1/L2/L3 tier layout) 의 cold tier (L2/L3) storage backend 를 local volume → 외부 NAS object storage 로 확장. ADR-017 의 hot path (collector WAL + L1 5min Parquet) 정책 = 유지 의무 (본 ADR §Decision D5 명시). ADR-017 의 zero-loss invariant + WAL durability 정책은 본 ADR 의 cold tier 정책에 영향 0.
- **ADR-016 complements (보완)**: ADR-016 §A4 "NFS/SMB/network filesystem 위 named volume 금지" 제약은 POSIX fsync 의존성 (admin_audit.sqlite WAL) 에 기반 — 본 ADR 의 NAS MinIO 는 **application-layer S3 API** (boto3 over HTTP, POSIX semantic 의존 0) → ADR-016 제약 정합 회피. admin_audit.sqlite cold archive (별 Epic) 는 본 ADR scope 외 (D11 명시).
- **ADR-008 references**: §D7 secret rotation cadence (반기 1회 / 분기 점검) + §D8 compromise emergency response. 본 ADR 의 90일 credential rotation runbook (MCT-147 산출물) 의 ADR-level 근거.
- **ADR-009 references**: §D12.1 `MCTRADER_DATA_ROOT` SSOT extension + 16-col schema 검증 invariant (본 ADR D6 의 parquet row count + sha256 + object count 3종 검증의 ADR-level 근거).

## Decision

### D1. Bucket layout — 단일 `mctrader-market` + Hive prefix

**단일 bucket `mctrader-market`** + 엄격한 Hive prefix 채택: `schema_version/exchange/node/tier/date/`. ADR-009 §D2 partition layout + ADR-017 §3 D3 (L1/L2/L3 tier layout) 정합.

- **Rationale**: 기존 `mctrader_data/compactor/minio_uploader.py` 의 `BUCKET_NAME='mctrader-market'` 하드코딩과 일치 → MCT-155 cutover 시 코드 변경 없이 endpoint swap. Hive prefix = ADR-009/ADR-017 partition layout 그대로 — schema migration / partition reorganization 0.
- **Alternative rejected**: bucket-per-tier (`mctrader-market-l1` / `mctrader-market-l2` / `mctrader-market-l3`) — bucket 수 증가 + IAM policy 분기 + reader 측 분기 → 거부.
- **Consequence**: MCT-155 cutover 시 endpoint swap (`MINIO_ENDPOINT` env → NAS endpoint) 단일 변경. Hive prefix invariant 보존.

### D2. TLS / auth — Stage 1 HTTP, Stage 2 HTTP 유지 (MCT-147 amend + MCT-155 amend)

**Stage 1** = **HTTP** (LAN 내부망 only, NAS 방화벽 port 9000/9001 = mctrader 호스트 IP only + `.env` 0600 + 90일 rotation runbook). **Stage 2** = **HTTP 유지** (사용자 confirm 2026-05-13, S12 user_confirmed: true) — 4중 mitigation Stage 2 후에도 그대로 유지. TLS 활성화 trigger = `docs/runbooks/nas-minio-tls-review.md` §4.2 4 조건 (외부 노출 / NAS hardware 교체 / Stage 3 발의 / Secret leak 의심).

- **Rationale (사용자 결정 — MCT-147 §11.1 박제, 2026-05-12)**:
  1. **운영 환경**: LAN 내부망 only — NAS 방화벽 port 9000/9001 = mctrader 호스트 IP 만 allow (외부 노출 0)
  2. **Stage 1 scope**: feasibility spike — TLS handshake 는 핵심 검증 항목 아님 (bucket bootstrap + idempotent restart 가 핵심)
  3. **Setup 비용**: self-signed cert client trust 박제 + Let's Encrypt public DNS 의존성 = Stage 1 의 spike 속도 저해
  4. **Stage 2 escalation 의무**: MCT-155 (mctrader-data endpoint cutover) 진입 시 D2 wording 재검토 의무 — Stage 2 TLS 옵션 (사용자 confirm 필요)
- **4중 Mitigation (SecurityArch §7.3 박제, MCT-147 §11.1)**:
  - `.env` 파일 0600 권한 + `.gitignore` 박제 (commit 차단)
  - 90일 credential rotation runbook (MCT-147 산출물 — `docs/runbooks/nas-minio-secret-rotation.md`)
  - NAS 측 방화벽 port 9000/9001 = mctrader 호스트 IP only
  - root account 외 별도 IAM user 분리 의무 (Stage 2 scope 명시)
- **Stage 2 escalation trigger (MCT-155, COMPLETED 2026-05-13)**: cutover 진입 후 (a) 외부 노출 검토 ✅ (NAS 방화벽 port 9000 mctrader IP only, 외부 노출 0) (b) TLS handshake cost / 운영 부담 / cert 관리 cadence 재평가 ✅ (`docs/runbooks/nas-minio-tls-review.md` §2-§3 박제) (c) 사용자 explicit confirm ✅ = **HTTP 유지** (Stage 1 정책 연장).
- **MCT-155 amendment 박제 (2026-05-13)**: 사용자 confirm = HTTP 유지 결정 (S12 user_confirmed: true). Future re-evaluation trigger = `docs/runbooks/nas-minio-tls-review.md` §4.2 4 조건 (외부 노출 / NAS hardware 교체 / Stage 3 발의 / Secret leak 의심).
- **Alternative rejected**: Stage 1 TLS 강제 — feasibility spike scope 초과 (위 rationale 1~3) → 거부.

### D3. ADR 형태 — 신규 ADR-027 (ADR-017 amendment 아님)

본 ADR 은 **신규 ADR-027** (ADR-017 successor, amendment 아님). ADR-017 본문 변경 0.

- **Rationale**: cold tier storage backend (NAS object storage) = ADR-017 의 hot path WAL 정책과 별 domain (storage layer). ADR-017 amendment 채택 시 (a) ADR-017 본문 비대화 (b) hot/cold tier 분리 가독성 손실 → 신규 ADR 채택.
- **Relationship**: `successor_of: [ADR-017]` (frontmatter) — ADR-017 의 cold tier 정의 확장. ADR-017 본문 §References 에 역방향 link append 는 본 ADR scope 외 (별 amendment Story 발의 가능).

### D4. Cutover 전략 — dual-write window → 검증 → reader 전환 → local GC

**4-step cutover** (MCT-150~155 scope):

1. **dual-write window** (MCT-150~152) — local volume write + NAS PUT 동시 수행. `mctrader_data.compactor.minio_uploader` 가 양쪽 PUT 후 sha256 비교.
2. **3종 invariant 검증** (D6) — sha256 + object count + parquet row count 3종 ALL PASS 의무.
3. **reader endpoint 전환** (MCT-154) — `mctrader-engine` 의 L2/L3 read source 를 local volume → NAS endpoint 로 swap. `MINIO_ENDPOINT` env 갱신 단일 변경.
4. **local GC** (MCT-155, D7 grace period 후) — 7일 grace + dry-run 선행 → 실 삭제.

- **MCT-150~155 scope 분담**:
  - MCT-150: `minio_uploader.py` hardening (retry queue + Prometheus metrics + alert)
  - MCT-151: dual-write atomic primitives + 3종 invariant 검증 harness
  - MCT-152: dual-write window 운영 (2-4주, drift 측정)
  - MCT-153: backfill (historic L2/L3 cold tier asset 이관)
  - MCT-154: reader endpoint cutover + engine smoke test
  - MCT-155: local GC + secret rotation 첫 cycle + Stage 2 TLS 재검토 사용자 confirm
- **Rationale**: forward-only invariant (ADR-009 §D12.2) + atomic switch (single endpoint swap) + 7일 grace (D7) = data loss 방지 3중 lock.
- **Alternative rejected**: big-bang cutover (dual-write 없이 endpoint swap 후 backfill) — backfill 실패 시 cold tier asset 영구 손실 risk → 거부.

**MCT-156 amendment 박제 (2026-05-13)** — Stage 3 wiring obligation. `compactor/runner.py` 의 L2/L3 compaction 산출물은 DualWriter (MCT-151 primitive) 를 통해 NAS MinIO 로 자동 dual-write 의무. legacy `MinioUploader` (MCT-149 이전, L3 only docstring) 는 deprecation 마킹, MCT-156 Phase 2 에서 호출처 제거. 본 amendment 의 trigger = Stage 2 EPIC CLOSED 후 사용자 bucket 실측에서 `tier=L3/` prefix 0개 + `tier=L2/.../hour=HH/` partition 0개 발견 (4.2 GiB / 1370 obj = MCT-153 backfill 1회 산출물 only). Stage 3 entrypoint vertical slice = MCT-156 (compactor NAS wiring + L2/L3 DualWriter injection), Prometheus layout label 분리 = MCT-157, release gate smoke test + EPIC CLOSED gate = MCT-158 (3 Story 분해). L1 hot path = 본 amendment scope 외 (ADR-027 §D5 + S3 결정 정합 — L1 NAS upload 0 invariant 유지). 신규 Epic = `EPIC-cold-tier-stage-3-wiring` (`scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` MCT-156 Phase 1 LAND).

### D5. Failure mode — compactor retry queue + alert, hot path 무영향

NAS unreachable 시:

- **compactor** = retry queue + backlog alert. NAS PUT 실패 → local tmp 보관 + exponential backoff retry. backlog 임계치 초과 시 Prometheus alert.
- **WAL / L1 / hot path** = 무영향. ADR-017 의 zero-loss invariant (collector WAL + L1 5min Parquet local) 정책 유지. NAS unreachable 이 hot path 에 propagate 0.

- **Rationale (OperationalRiskArch §7.4 박제, MCT-147 §11.5)**:
  - NAS 가용성 SLA 부재 (Synology 가정용, R1 잔존 위험)
  - cold tier 는 long-term archive 성격 → 단기 unreachable 허용 (hot path 영향 0 의무)
  - retry queue = MCT-150 scope (`minio_uploader.py` hardening)
- **Alert metric (MCT-150 산출물)**: `cold_writer_backlog_segments` + `cold_writer_retry_count_total` (Prometheus) + Grafana dashboard `mctrader/Cold Writer Health`.
- **Hot path 무영향 invariant**: collector WAL append + L1 ParquetWriter 의 fsync / atomic rename 은 NAS unreachable 와 무관 — local filesystem only.

**MCT-156 amendment 박제 (2026-05-13)** — retry queue + Prometheus alert wiring obligation. MCT-150 land 의 NASUploader retry queue 가 hot pipeline `compactor/runner.py._run_l2/l3` 의 DualWriter inject 단계에 자동 활용. DualWriter status enum 3종 (`committed` / `local_only` / `hard_floor_blocked`) 의 caller contract: `committed` = 정상 (local + NAS atomic visible), `local_only` = retry_queue enqueue 후 backlog drain (정상 fallback 경로), `hard_floor_blocked` = retry_queue 1000seg/10GB threshold 초과 (S10 박제 정합) → log error + Prometheus alert + SOP MANUAL_GATE escalation 의무 (MCT-150 `nas_unreachable_sop.py` SOPRunner 재사용). Prometheus metric `mctrader_dual_write_result_total{status, tier}` Counter emit (Phase 2 `nas_metrics/prometheus_exporters.py` 신규 추가, MCT-156 Phase 2 AC-G). layout label (`legacy_node_default` vs `new_node_merged`) 분리 = MCT-157 별 Story scope. L1 hot path = 본 amendment scope 외 (DualWriter inject 0, ingester service `MINIO_*` env 변경 0 = L1 NAS upload 0 invariant 유지, ADR-027 §D5 + S3 결정 정합).

### D6. 이관 검증 invariant — 7종 ALL PASS (MCT-151 + MCT-155 amend, S5 박제)

**Amendment trail (2026-05-13, MCT-151 trigger / MCT-155 land)**: 본 D6 wording = 3종 → **7종** 으로 명시화. scope_manifest design_decisions S5 박제 정합 (`Codex review + Sonnet decider 합성, addressed_in: [MCT-151, MCT-153], triggers_adr_amendment.mandatory=true.trigger_story=MCT-151`).

dual-write window 의 cutover validation (D4 step 2) — **7종 invariant ALL PASS**:

**byte-level (1종)**:
1. **sha256**: local L2/L3 Parquet 의 sha256 == NAS object 의 sha256 (full byte-level identity)

**set-level (2종)**:
2. **object count**: local L2/L3 partition 의 file count == NAS bucket 의 object count (per partition)
3. **parquet row count**: local L2/L3 Parquet 의 row count == NAS object 다운로드 후 parquet row count (per file)

**schema-level (4종 — S5 amendment 신규)**:
4. **column count**: ADR-009 §D2.1 16-col 의무 (== 16, per file)
5. **column name order**: ADR-009 §D2 정의 정합 (per file)
6. **dtype identity**: pyarrow type-level identity (Decimal precision/scale 포함, EC-5 박제)
7. **schema_version pin**: partition prefix `schema_version=v1` 정합 (legacy schema 침범 차단)

**7종 ALL PASS 의무** — 1종이라도 FAIL 시 cutover 차단.

- **Rationale (3종 → 7종 확장 사유)**: MCT-148 T3 (large PUT 50MB, sha256 IDENTICAL 3/3 = 100%) + T5 (partial visibility, atomic_invariant=true) = byte-level + atomic visibility 의 PoC 사전 입증. **schema-level 4종 추가 사유 (S5 amendment)**: D6 본문 3종 PASS 이나 Parquet schema 차이 (column 순서/dtype mismatch 등) 로 reader 측 read 파괴/오염 risk 차단 (reader-breaking drift 포착) — MCT-151 InvariantHarness 가 7종 sequential unconditional verify (early return 0).
- **Alternative rejected**: object count only — sha256 차이 (compression 차이 등) 검출 불가 → 거부.
- **MCT-151 scope**: 7종 invariant 검증 harness 구현 (`mctrader_data/nas_migration/invariant_harness.py`).
- **MCT-155 amendment land 시점**: 2026-05-13 (Stage 2 마지막 Story Phase 2 PR — 본 amendment 박제).

### D7. Local GC — 7일 grace + dry-run 선행 + 디스크 압박 시 tier/date 순차

cutover 후 local volume 의 L2/L3 cold tier 자산 삭제 절차:

1. **7일 grace period** — reader endpoint cutover (D4 step 3) 후 7일 동안 local volume 유지. emergency fallback 가능.
2. **dry-run 선행** — `cold_gc --dry-run` 으로 삭제 대상 list 산출 + user review.
3. **실 삭제** — dry-run 결과 OK 시 `cold_gc --execute` 실행.
4. **디스크 압박 시 순차** — disk usage > 90% 시 tier (L3 → L2 순) + date (oldest first) 순차 GC.

- **Rationale**: data loss 방지 3중 lock (grace + dry-run + 순차). 7일 grace = engine reader cutover 후 정상 운영 검증 buffer.
- **Alternative rejected**: immediate GC (cutover 직후) — emergency fallback 불가 → 거부.

### D8. Spike scope — 5 PoC (MCT-148 evidence 직접 인용)

Stage 1 Feasibility Spike 의 5 PoC 항목 + MCT-148 evidence transcribe:

| PoC | Test ID | 결과 | 측정값 | NFR 충족 |
|-----|---------|------|--------|----------|
| 1 | T1 HTTP health (live + ready) | **2 PASSED** | HTTP 200 OK (`/minio/health/live` + `/minio/health/ready`) | D2 amend 정합 (HTTP 200 base) |
| 2 | T2 Latency baseline (4 size × 30 reps) | **4 PASSED** | p99: 1KB=465.53ms / 1MB=441.34ms / 10MB=971.99ms / 50MB=2870.65ms | NFR-1 충족 (1KB < 500ms / 1MB < 1000ms / 10MB < 3000ms / 50MB < 10000ms) |
| 3 | T3 Large PUT 50MB (3 iter) | **3 PASSED** | sha256 IDENTICAL 3/3 = 100% | NFR-2 충족 (byte-level identity) |
| 4 | T4 Restart idempotency | **PASSED (manual gate)** | recovery_ms=30.56 / sha_match=true / manual_gate_timeout_fallback=false | NFR-3 충족 (≤ 5min) |
| 5 | T5 Partial visibility | **1 PASSED** | atomic_invariant=true (n_get_attempts=35, 34 NoSuchKey + 1 SIZE_50MB only) | NFR-4 충족 (S3 atomic 보존) |

**Pytest 통계**: 10 PASSED / 0 FAILED / 0 SKIPPED in 107.76s + T4 manual gate 1 PASSED. NFR-5 (< 15min wall-clock) 충족 (margin 800s 이상).

#### T3 sha256 IDENTICAL evidence (raw json snippet — 3 iter 대표)

```json
{
  "test": "large_put_50mb",
  "iteration": 0,
  "size_bytes": 52428800,
  "sha_local": "ad0f71ef493d1a566073432a428a9c8e2076877a603c02d40f61eefa0b225fec",
  "sha_remote": "ad0f71ef493d1a566073432a428a9c8e2076877a603c02d40f61eefa0b225fec",
  "match": true
}
```

3 iter 모두 `sha_local == sha_remote` (3/3) — D6 sha256 invariant 의 PoC 사전 입증.

#### T2 Latency baseline (4 size — 50MB 대표)

```json
{
  "test": "latency_baseline",
  "size": "50MB",
  "n_reps": 30,
  "p50_ms": 2012.15,
  "p95_ms": 2481.41,
  "p99_ms": 2870.65,
  "min_ms": 1874.87,
  "max_ms": 2654.06
}
```

50MB p99 = 2870.65ms (NFR limit 10000ms 내, margin 7000ms+). 1KB / 1MB / 10MB 도 모두 NFR limit 내.

#### T5 atomic_invariant evidence

```json
{
  "test": "partial_visibility",
  "n_get_attempts": 35,
  "atomic_invariant": true,
  "size_50mb": 52428800
}
```

35 GET 시도 중 34건 = `NoSuchKey` (object 미존재 visible 0), 1건 = `SIZE_50MB only` (atomic visible) → S3 atomic visibility 보존. partial bytes (e.g., 25MB) visible = 0 → D6 invariant 정합.

#### T4 Restart idempotency (manual gate)

```json
{
  "test": "restart_idempotency",
  "recovery_ms": 30.56,
  "sha_match": true,
  "manual_gate_timeout_fallback": false
}
```

NAS DSM UI 의 Container Manager STOP/START 후 recovery time = 30.56ms (NFR-3 limit 5min = 300000ms 의 0.01%). sha256 match = true (restart 전후 object 무변경). `manual_gate_timeout_fallback=false` = 사용자 manual gate timeout 없이 정상 recovery.

**Evidence pack 원본 경로**: `mctrader-data/.tmp/evidence-pack-MCT-148.md` (gitignored, 426 line) — MCT-148 retro `docs/retros/RETRO-MCT-148.md` 의 §3.1 evidence pack pointer 도 cross-reference.

### D9. Reader — engine read-through cache (NAS = SoT, local = LRU/TTL cache)

`mctrader-engine` 의 cold tier read 모델 (MCT-154 cutover scope):

- **NAS = Source of Truth (SoT)** — L2/L3 cold tier 의 authoritative read source.
- **local = LRU/TTL cache** — engine 호스트 측 read cache (LRU + TTL). NAS GET latency (MCT-148 T2 p99 측정값 base) 의 hot read amortize.
- **partition path 호환 invariant**: 기존 `tier=L1/L2/L3` Hive partition layout 보존 — reader 측 path schema 변경 0.

- **Rationale**: NAS = SoT 채택 = forward-only invariant (ADR-009 §D12.2) + immutable cold tier 의 자연 정합. local cache = read latency optimization, write authority 0.
- **Alternative rejected**: local = SoT + NAS = backup — write amplification + cutover 시 trust model 분기 → 거부.
- **MCT-154 scope**: engine read-through cache 구현 + smoke test.

**MCT-156 amendment 박제 (2026-05-13)** — reader read-through cache 의 mixed layout 책임 경계. NAS bucket 에는 (a) MCT-153 backfill 산출물 = legacy ADR-009 §D2.1 layout (`tier=L2/.../date=D/[node=N/]file.parquet`, hour 부재) + (b) MCT-156 Phase 2 이후 신규 hot pipeline 산출물 = 신규 schema (`tier=L2/.../date=D/hour=HH/node=MERGED/part-*.parquet`) 가 mixed 공존. reader 호환은 ADR-009 §D2.1 (`node=` absent → `node=DEFAULT` treated) + §D14 (`tier=` absent → `tier=L1` treated) fallback 박제로 자연 보장 — engine `scan_*` API 의 partition pruning 이 양쪽 layout mixed scan 자연 양립. legacy 객체 retroactive 재구조 비권고 (S6 결정, MCT-156 §3 박제) — 변경 시 forward-only invariant (ADR-009 §D12.2) 위반 + reader fallback 박제 redundant. MCT-154 land 의 `endpoint_router.py` / `reader_cache.py` / `cold_reader.py` 모두 본 amendment 영향 0 (변경 0). 신규 hot pipeline 산출물 = forward-only 자연 누적 (S2 결정 정합 — DualWriter inject), L3 backfill 별 Story 불필요 (S7 결정 정합 — hot pipeline wiring 완료 후 자연 누적).

### D10. 영향 repo — mctrader-data + mctrader-engine + mctrader-hub

본 ADR 의 영향 repo:

- **mctrader-data**: `compactor/minio_uploader.py` hardening (MCT-150) + cold writer module (MCT-151~153)
- **mctrader-engine**: cold tier reader cutover (MCT-154) + read-through cache
- **mctrader-hub**: governance (본 ADR-027 + Story MCT-149)

**제외 repo**: mctrader-market / mctrader-market-bithumb / mctrader-web — cold tier storage backend 와 무관.

- **Rationale**: mctrader-market\* = exchange interface only (storage layer 무관). mctrader-web = UI / Streamlit only (cold tier read 는 engine 경유).

### D11. admin_audit.sqlite — 본 epic 제외, 별 epic (ADR-016 complement)

`mctrader-web` 의 `admin_audit.sqlite` (ADR-016 immutable audit log) cold archive 정책은 **본 ADR scope 외**, 별 Epic.

- **Rationale**: admin_audit.sqlite = sqlite WAL + POSIX fsync 의존 (ADR-016 §A4 의 named volume 제약 적용). cold tier parquet (S3 API, application-layer) 과 storage backend semantic 상이 → 별 Epic 으로 분리.
- **별 Epic scope**: admin_audit.sqlite 의 immutable archive 운영 모델 (sqlite WAL → parquet cold archive 변환 / 또는 sqlite snapshot cold tier 저장) — 본 ADR-027 의 cold tier 정책 (parquet only) 과 정합 의무, but 별도 ADR 발의.

## Consequences

### Pros

- **호스트 disk 용량 압박 해소** — cold tier (L2/L3, 누적 ~수십 GB) 외부 storage backend 이관 → 호스트 disk 는 hot path (WAL + L1) 만 사용.
- **forward-only invariant 보존** (ADR-009 §D12.2) — 3종 invariant 검증 (D6) + 7일 grace GC (D7) 의 3중 lock.
- **ADR-017 hot path 정책 무영향** (D5) — collector WAL + L1 ParquetWriter 의 zero-loss invariant 보존. NAS unreachable 이 hot path 에 propagate 0.
- **단일 endpoint swap cutover** (D4) — `MINIO_ENDPOINT` env 갱신 단일 변경 + Hive partition layout 보존 → 코드 변경 최소.
- **S3 API 추상화** (§Alternatives C 채택) — engine reader 측 분기 0, MCT-154 cutover 시 코드 변경 최소.

### Cons

- **NAS 가용성 SLA 부재** (R1 잔존) — Synology 가정용, 99.x% uptime SLA 부재. compactor retry queue + backlog alert (D5) 로 mitigation.
- **NFR-1 latency overhead** — NAS GET p99 (50MB = 2870.65ms) 는 local volume 대비 증가. engine read-through cache (D9 LRU/TTL) 로 amortize.
- **NAS 방화벽 룰 drift risk** (R10 신규) — 방화벽 ACL (port 9000/9001 = mctrader 호스트 IP only) drift 시 (a) 외부 노출 risk (b) endpoint unreachable. 90일 rotation runbook step 6 에 audit 의무 박제 (MCT-147 §11.5).
- **Stage 1 HTTP 운영 (D2 amend)** — TLS 부재 → LAN 내부망 전제 + 4중 mitigation. Stage 2 (MCT-155) TLS 재검토 의무 escalation 박제.
- **dual-write 기간 운영 부담** (D4 step 1) — 2-4주 dual-write 기간 동안 local volume + NAS PUT 양쪽 운영. disk I/O 증가 + 3종 invariant 측정 daily report 부담.

### Neutral

- **bucket layout 변경 0** (D1) — 기존 `mctrader-market` bucket + Hive prefix 보존. schema migration 0.
- **counters.json reservation +1** (`mctrader-hub.next: 156` reservations 9건) — 본 ADR publish 후 reservation marker DELETE (Story §9 산출물).
- **ADR-026 immutable invariant 정합** — cold tier immutable (legacy candle = forward-only) 와 정합. Stage 2 versioning (S3 bucket versioning) 정책 결정 시 ADR-026 의 immutable invariant 와 정합 의무 (Stage 2 brainstorm 재실행 input).

## Alternatives Considered

### A. MinIO + WebDAV mount (rejected)

- **제안**: 호스트 측에서 NAS WebDAV mount → mount path 를 MinIO data dir 로 지정.
- **거부 사유**: MinIO 공식 정책 (`minio/minio#14060`) — NFS/SMB/WebDAV mount 위 MinIO data dir 는 **unsupported**. `format.json` 등 atomic operation 의 POSIX fsync semantic / atomic rename / file locking 미보장. `IO error` 또는 silent data corruption risk.
- **재고려 trigger**: 없음 — MinIO 공식 정책 변경 시 (현재 unsupported policy 유지) 만 재고려.

### B. cold_writer direct WebDAV PUT (rejected)

- **제안**: mctrader-data `cold_writer` 모듈이 MinIO 우회, NAS WebDAV endpoint 에 직접 PUT (HTTP `PUT /<webdav-path>`).
- **거부 사유**: S3 API 추상화 상실 → engine reader (ADR-017 D3 L2/L3 read) 측 분기 코드 폭증. (a) cold tier read = WebDAV GET 분기 (b) local L2/L3 read = filesystem read 분기 (c) cutover 시 양쪽 분기 코드 동시 운영. S3 API 통일 (boto3) 의 cutover 단순성 이득 손실.
- **재고려 trigger**: 없음 — S3 API 추상화의 cutover 단순성이 본 ADR 의 핵심 design lever.

### C. NAS Synology Container Manager + MinIO direct deploy (chosen)

- **제안**: NAS DSM 7.2+ 의 Container Manager 패키지로 MinIO 컨테이너 직접 deploy + NAS local btrfs/ext4 volume 을 MinIO data dir 로 mount.
- **채택 사유**: application-layer S3 API 만 사용, POSIX semantic 의존 0 (MinIO 내부 atomic op 은 NAS local volume = POSIX-compliant btrfs/ext4 위에서 정상). S3 API 통일 (boto3) → engine reader 분기 0. 호스트 측 mount 부담 0 (NAS 가 container 내부에서 local volume 사용).
- **MCT-147 산출물 검증**: NAS DSM Container Manager UI 로 compose import + bucket bootstrap 정상 동작 (MCT-147 MERGED). MCT-148 5 PoC 검증 (T1~T5 ALL PASS) — application-layer S3 API 정상 동작 + atomic invariant 보존 입증.

## Migration

### Stage 1 종료 gate (본 ADR merge)

본 ADR status=Accepted + 11 결정점 본문 박제 + MCT-148 evidence transcribe + ADR-017/016 cross-link + Stage 2 escalation trail (D2) = **Stage 1 종료**. 

### Stage 2 진입 조건 (MCT-150~155 sequence)

본 ADR merge 후 brainstorm Phase 0 재실행 권고 (PoC 결과 + ADR-027 본문 박제 후 brainstorm 컨텍스트 갱신). Stage 2 cold tier migration 의 MCT-150~155 sequence:

| Story | scope | dependency |
|-------|-------|------------|
| MCT-150 | `minio_uploader.py` hardening (retry queue + Prometheus metrics + alert, D5 산출물) | 본 ADR merge |
| MCT-151 | dual-write atomic primitives + 3종 invariant 검증 harness (D6 산출물) | MCT-150 |
| MCT-152 | dual-write window 운영 (2-4주, drift 측정, D4 step 1~2 실행) | MCT-151 |
| MCT-153 | backfill (historic L2/L3 cold tier asset 이관) | MCT-152 PASS |
| MCT-154 | reader endpoint cutover + engine smoke test (D4 step 3, D9 read-through cache) | MCT-153 |
| MCT-155 | local GC + secret rotation 첫 cycle + Stage 2 TLS 재검토 사용자 confirm (D4 step 4, D2 escalation) | MCT-154 |

### Forward-only invariant (ADR-009 §D12.2)

본 ADR 의 cutover 절차 (D4) 는 forward-only invariant 정합:

- 기존 cold tier asset 의 row 변경 / 삭제 0 — dual-write 기간 동안 양쪽 write, cutover 후 local GC (7일 grace + dry-run).
- 3종 invariant 검증 (D6) = byte-level identity 보장 → forward-only invariant 의 measurable 측면 입증.

## References

### ADR cross-link

- **ADR-017** (`docs/adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md`) — **successor_of**. §3 D3 (L1/L2/L3 tier layout) 의 cold tier storage backend 를 외부 NAS object storage 로 확장. hot path 정책 유지 의무 (D5).
- **ADR-016** (`docs/adr/ADR-016-audit-log-immutability.md`) — **complements**. §A4 network filesystem 금지 제약 정합 회피 (application-layer S3 API). admin_audit.sqlite = 별 Epic (D11).
- **ADR-008** (`docs/adr/ADR-008-secret-management.md`) — **references**. §D7 rotation cadence (90일) + §D8 compromise emergency response. 본 ADR cold-tier-specific rotation runbook (MCT-147 산출물) 의 ADR-level 근거.
- **ADR-009** (`docs/adr/ADR-009-ohlcv-schema.md`) — **references**. §D12.1 `MCTRADER_DATA_ROOT` SSOT extension + 16-col schema 검증 invariant (D6 source). §D12.2 forward-only invariant 정합.
- **ADR-026** (`docs/adr/ADR-026-legacy-candle-provenance-retirement-policy.md`) — 배경 link (cold tier immutable invariant 정합). 본 ADR scope 외 — Stage 2 versioning 정책 결정 시 cross-reference.
- **ADR-033** (codeforge plugin — Docker-first named volume DR) — 배경 link (cross-plugin reference, hub `docs/adr/` 부재). NAS Container Manager 위 docker compose 배치 정합 (MCT-147 산출물).

### Story / Epic

- **MCT-149** (본 Story, hub) — ADR-027 본문 publish + Stage 1 종료 governance Story.
- **MCT-147** (`docs/stories/MCT-147.md`) — NAS MinIO 컨테이너 deploy + bucket 초기화 + D2 amend 박제 + 4중 mitigation runbook (MERGED 2026-05-12, `mctrader-hub#246` 409d076).
- **MCT-148** (`mctrader-data/docs/stories/MCT-148.md`) — 5 PoC PASS evidence pack (MERGED 2026-05-12, `mctrader-data#40` d3e2af5). evidence pack: `mctrader-data/.tmp/evidence-pack-MCT-148.md` (gitignored).
- **MCT-148 retro** (`docs/retros/RETRO-MCT-148.md`) — 5 PoC PASS + T4 manual gate 박제, hub repo 박제 SSOT.
- **EPIC-cold-tier-nas-minio** — `scope_manifests/EPIC-cold-tier-nas-minio.yaml` (D1~D11 + D2/D8 amend + R10 신규 + R7 재서술 박제).

### MCT-148 PoC Test ID → ADR-027 Decision mapping

| Test ID | PoC | ADR-027 §Decision 인용 |
|---------|-----|------------------------|
| T1 | HTTP health (live + ready) | D2 (HTTP 200 base 정합) |
| T2 | Latency baseline (4 size × 30) | D8 (5 PoC), Cons (NFR-1 latency overhead) |
| T3 | Large PUT 50MB (sha256 IDENTICAL 3/3) | D6 (3종 invariant 중 sha256 PoC 입증) |
| T4 | Restart idempotency (recovery_ms=30.56) | D5 (failure mode — restart 후 recovery), D8 PoC |
| T5 | Partial visibility (atomic_invariant=true) | D6 (3종 invariant 중 atomic visibility), D9 (S3 API 추상화 정합) |

## History

- 2026-05-12 — ADR-027 본문 publish (MCT-149, Stage 1 종료 governance Story). D1~D11 본문 + Stage 1 evidence transcribe (MCT-148 PoC 5종 PASS) + ADR-017/016 cross-link + Stage 2 escalation trail (D2). status=Accepted.
- 2026-05-13 — **D2 amendment** (MCT-155, Stage 2 마지막 Story Phase 2 PR — `mctrader-hub#276` MERGED). Stage 2 TLS 재검토 결과 박제 — HTTP 유지 (Stage 1 정책 연장, 사용자 confirm 박제, S12 user_confirmed=true). Future re-evaluation trigger = `docs/runbooks/nas-minio-tls-review.md` §4.2 4 조건.
- 2026-05-13 — **D6 amendment** (MCT-155, Stage 2 마지막 Story Phase 2 PR — `mctrader-hub#276` MERGED). 3종 → 7종 invariant 명시화 (S5 박제, MCT-151 InvariantHarness 정합). byte-level (1) + set-level (2) + schema-level (4) = 7종 ALL PASS 의무.
- 2026-05-13 — **D4/D5/D9 amendment** (MCT-156, EPIC-cold-tier-stage-3-wiring Stage 3 wiring entrypoint — 본 PR). Stage 2 EPIC CLOSED 후 사용자 NAS bucket 실측에서 발견된 hot pipeline NAS wiring gap 해소. D4 = Stage 3 wiring obligation 박제 (`compactor/runner.py` L2/L3 DualWriter inject 의무 + legacy MinioUploader deprecation 마킹). D5 = retry queue + Prometheus alert wiring obligation (DualWriter status enum 3종 caller contract + `mctrader_dual_write_result_total{status, tier}` Counter emit). D9 = reader read-through cache 의 mixed layout 책임 경계 (legacy + 신규 mixed scan = ADR-009 §D2.1+§D14 fallback 자연 양립). D6 (RPO=0) amend 0 = invariant, wiring 변경 무관.
