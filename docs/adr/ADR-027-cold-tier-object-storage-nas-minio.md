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

**Amendment Trail**:
- 2026-05-13 — §D5 (MCT-156) retry queue + Prometheus alert wiring obligation
- 2026-05-13 — §D6 (MCT-151 + MCT-155) 3종 → 7종 invariant 확장
- 2026-05-13 — §D6 (MCT-159 FIX Iter 1) column_count invariant channel-aware resolve
- 2026-05-13 — §D9 (MCT-156 + MCT-159) reader read-through cache mixed layout 책임 경계
- 2026-05-14 — §D MCT-161 amendment (bucket versioning + Object Lock + Lifecycle ILM)
- 2026-05-14 — **§D5 + §D7 + §D9 major amendment (MCT-167, EPIC-tier-promotion-single-source, ADR-029 publish)**:
  - **§D5 amendment** — L1 NAS upload 금지 invariant **폐기** (ADR-029 D1=B 채택). L1 ParquetWriter atomic 직후 compactor 측 DualWriter 호출 의무 박제. capacity-bounded ingest block 도입 (WAL 30 GiB + L1 20 GiB hard limit).
  - **§D7 amendment** — L1 tier grace 정책 = **grace 0** (ADR-029 D3=C). L1 NAS PUT 완료 + version/etag exact match + sha256 verify 후 즉시 local L1 file 삭제. L2/L3 = 7일 grace 유지.
  - **§D9 amendment** — SoT scope = **all-tier (L1 + L2 + L3) 격상**. NAS = SoT for ALL tiers, local = ephemeral cache only. ambiguity 차단 invariant (ADR-029 D10) 박제.
- 2026-05-17 — **§D1 amendment box (U1-ADR, EPIC-nas-key-unification Phase 2, ADR-034 publish)**:
  - **§D1 cross-ref 박제** — ADR-034 §결정 1 채택. NAS object key 의 `l1/` sub-namespace 제거 (전 tier 단일 평면 layout). 단일 bucket `mctrader-market` + Hive prefix layout 정책 자체 무변경 — `l1/` prefix sub-namespace 만 제거 (tier 구분 = Hive partition `tier=L{1,2,3}/` 컴포넌트로 충분). ADR-027 §D1 의 Hive prefix layout (`schema_version/exchange/node/tier/date/`) invariant 보존.
  - **상세**: 본 amendment 는 ADR-034 § Context "Ground Truth — 4 SSOT 분산점" 표 + § Decision §결정 1 verbatim 박제. Phase 2 cutover sequence = U2-HELPER (단일 helper SSOT) → U3-MIGRATE (1회성 멱등 re-key 마이그레이션) → U5-VERIFY (Phase 1 helper 회수 + forward-only invariant 박제). dual-read 윈도우 = U2 land ~ U5 land. carrier ADR: `docs/adr/ADR-034-nas-key-unification.md`.

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

**MCT-159 amendment 박제 (2026-05-13)** — L2/L3 cold tier backlog migration obligation. Stage 3 wiring (MCT-156 LAND `mctrader-data#47` + `mctrader-hub#279`) 후 hot pipeline NAS PUT 정상화 (compactor 09:22 restart 후 09:24 부터 신규 schema `tier=L{2,3}/.../date=D/hour=HH/node=MERGED/` 로 PUT 시작). 그러나 wiring _이전_ 로컬 누적 L2/L3 backlog (orderbooksnapshot L2 6.1 GiB / 2305 file + L3 2.4 GiB / 429 file + transaction L2 186 MiB / 3335 file + L3 154 MiB / 1049 file = 총 **8.85 GiB / 7118 file**) 은 자연 cadence 적용 외 영역 — `orderbookdepth` channel NotImplementedError 영구 fail 로 L2 자연 trigger ETA 9.2h 무효 (RETRO-MCT-156 §13.4 박제). 본 amendment = MCT-153 `BackfillOrchestrator` 의 (a) channel parametrize (`orderbooksnapshot` + `transaction` 양 channel) + (b) hour key 처리 (`_build_chunk_spec` `hour` 축 추가, `nas_object_key` 에 `/hour=HH/node=MERGED/` 박제) 2 amendment 후 재호출하여 LAND-이전 backlog 강제 이관. forward-only invariant + 7d grace + 7종 invariant ALL PASS gate 정합 의무. L1 sealed backlog (76,200 file / ~115 GiB) + WAL (59 GiB) = 본 amendment scope 외 (MCT-160 책임, orderbookdepth FIX + L2 offset overflow FIX prerequisite). 사용자 명시 동기 (disk 압박 해소) 본 amendment 만으로 미달성 (4.8% only, 8.85 GiB / 전체 ~183 GiB) — MCT-160 sequential 의무 박제. MCT-153 손실 재발 방지 = MCT-161 reserve (bucket versioning 활성화 + replication 정책) 별 Story 책임 (D9 amendment 정합).

**MCT-162 amendment 박제 (2026-05-13)** — channel parity 정책 + fail-fast invariant. EPIC-compactor-operations Story-1 (post-MCT-156 deploy 5중 차단 #1+#4 cycle).

**Background — silent skip catastrophe**: MCT-156 (Stage 3 wiring) production deploy 후 사용자 NAS bucket 실측에서 L1Compactor 의 `_schema_version` allowlist (`("transaction", "orderbooksnapshot")` 만) 와 bithumb collector emit channel `orderbookdepth` mismatch 발견. L1Compactor 가 sealed segment 마다 `NotImplementedError` 100% throw → **`compact_segment` outer try/except 가 catch 후 silent skip** → 48,629 sealed segment 가 sealed lifecycle stuck (delete 0, L1 partition 0, NAS upload 0). Prometheus alert 0 (channel-blind path 의 invariant 부재) → operator 인지 0 → ingester emission 분당 ~12 sealed 추가 → backlog 영구 monotonic 증가 (MCT-156 deploy 2026-05-13 09:22 ~ MCT-159 deploy 11:40 도착 시점 +3,227 file = 76,200 → 79,427). RETRO-MCT-156 §13.4 cross-ref.

**Channel parity 정책 박제**:

1. **모든 collector emit channel 은 L1/L2/L3 layer parity 의무** — 신규 channel 추가 시 ADR-009 §D11 (또는 §D10 / §D14 / §D11.9 등) amendment + L1Compactor converter dispatch 함수 추가 + integration test 동시 land 의무. 본 의무는 ADR-009 §D2.6 `ADR009_CHANNEL_SCHEMA_MATRIX` SSOT amendment 와 dual-binding (MCT-159 FIX Iter 1 amendment 정합 — 신규 schema_version row 의무 추가).
2. **Unsupported channel = fail-fast invariant** — `_schema_version(channel)` 의 unsupported branch 가 `NotImplementedError` raise (silent skip 금지) + Prometheus counter `compactor_unsupported_channel_total{channel}` Counter +1 emit. silent skip 차단 invariant.
3. **Cardinality risk 검토 (SecurityArch + OperationalRiskArch deputy 통합 박제)**: counter label `channel` cardinality = collector emit channel 종류만 (bithumb `transaction` / `orderbooksnapshot` / `orderbookdepth`, upbit `transaction` / `orderbooksnapshot` + future exchange) → bounded low cardinality. attacker-controlled label injection 0 (collector code path 만 emit source). Prometheus high-cardinality risk = N/A.
4. **신규 channel 추가 절차 (3-step ALL 의무)**:
   - (a) **ADR-009 schema 정의 amendment** — column count/order/dtype 박제 + §D2.6 `ADR009_CHANNEL_SCHEMA_MATRIX` row 추가 (CFP-26 sibling sync 정합)
   - (b) **L1Compactor `_CHANNEL_SCHEMA_VERSION` allowlist 추가** + converter dispatch 함수 추가 + path derive 정합 (`market/{channel}/schema_version=*/tier=L1/...` partition root 정합)
   - (c) **integration test 의무** — `tests/integration/test_l1_compactor_channel_parity.py` 에 신규 channel converter PASS + fail-fast unsupported channel + Prometheus emit + parquet schema 정합 의무 4 test 추가
5. **fail-fast 의도 (silent skip 사례 재발 방지)**: backlog 영구 monotonic 누적 차단. operator 가 Prometheus `compactor_unsupported_channel_total{channel}` Counter spike 즉시 감지 가능 (Grafana alert 임계 1+ 추가 의무 — Phase 2 또는 후속 ops Story scope). MCT-156 silent skip catastrophe 재발 차단 invariant.
6. **MCT-162 Phase 2 scope (구현 land 의무)**: `orderbookdepth → orderbook_depth.v1` allowlist 추가 + WAL delta `changes` payload → per-level flatten converter (ADR-009 §D11.9 정합) + `raw_json` column `large_string` cast 의무. L1 hot path = 본 amendment scope 정합 (ADR-027 §D5 L1 NAS upload 0 invariant 유지 — compactor local write 단계 변경, NAS PUT 영역 무관).

**Out-of-scope (본 amendment 한계)**:

- **upbit L1 partition 0 별 root cause** = upbit collector WAL sample 실측 결과 (`/var/lib/mctrader/data/wal/upbit/` = `orderbooksnapshot` / `transaction` only, **`orderbookdepth` 0**) → upbit ingester 가 emit 한 `transaction` / `orderbooksnapshot` sealed segment (4,749 today + 13,810 모든 date) 가 있음에도 L1 partition 0 = **별 진단 의무** (MCT-160 또는 별 Story scope). orderbookdepth allowlist 와 무관 사실 명시 박제.
- **L1 backlog 79,427 file natural drainage** = MCT-162 Phase 2 land 후 자연 drainage 의존 (D5 MCT-160 scope). 본 amendment = root cause 차단 invariant 박제만, 기존 누적 backlog 의 active cleanup 의무 0.
- **L2 `pa.concat_tables` OOM exit 137 fix** = MCT-160 Phase 1 scope (D3 streaming `ParquetWriter.write_table` per-file loop). 본 amendment 의 `large_string` cast 의무 (§D11.9.6) 는 OOM root cause 의 일부 (raw_json column i32 offset overflow) 차단 — MCT-160 의 streaming write 와 결합 시 단일 buffer 누적 0 보장.

**MCT-160 amendment 박제 (2026-05-13)** — Cadence trigger silent-skip 차단 + post-write monotonic verify + quarantine 정책. EPIC-compactor-operations Story-2 (post-MCT-156 deploy 5중 차단 cycle #2 transaction L2 자연 cadence 0 + #3 bucket 463 obj bithumb orderbooksnapshot only + #5 orderbooksnapshot manual L2 OOM exit 137 fix).

**Background**: MCT-156 deploy (2026-05-13 09:22) 후 L2/L3 cadence 가 silent skip 으로 backlog 영구 monotonic 누적. MCT-162 LAND (channel parity + fail-fast invariant + orderbookdepth allowlist) 후 drainage rate **+11/min net positive** 측정 — L2 자연 cadence trigger 부재 박제. Root cause = `runner._run_l2` 의 `compact_hour(hour_utc=datetime.utcnow())` 하드코딩 → `_run_l3` 의 `compact_day(date_utc=datetime.utcnow().date())` 동형 pathology (silent KST→UTC date roll edge case). MCT-162 amendment 의 fail-fast invariant 박제만으로 cadence path 의 silent skip 미해소 — caller-explicit date 전달 의무 박제 필요.

**Channel parity 정책 확장 (MCT-162 D4 amendment 답습 + cadence 차원 추가)**:

1. **Caller-explicit date 의무 (D2)**: `_run_l2` / `_run_l3` 가 `compact_hour(date_utc=...)` / `compact_day(date_utc=...)` 인자 명시 전달 의무. caller 측 partition lookup (glob `tier=L1/exchange={ex}/symbol={sym}/date=*/`) 후 latest date discover. KST→UTC date roll edge 시점 (now=KST 00:00~09:00) 의 silent skip 차단 invariant. system clock 의존 0.
2. **Post-write monotonic verify (D4)**: L2/L3 streaming write 후 `ts_utc` column monotonic non-decreasing invariant check 의무. 위반 시 산출물을 quarantine 경로로 isolate + Prometheus `compactor_quarantine_total{tier,reason}` Counter +1 emit + WARN log (운영자 grep gate) + 다음 segment 진행 (fail-closed isolate, raise 0). ADR-009 §D12.2 forward-only invariant 강화.
3. **Quarantine directory layout** (SSOT, Story `MCT-160.md` §11 박제 cross-ref):
   ```
   /var/lib/mctrader/data/quarantine/{tier}/{reason}/{original_relative_path}
   ```
   예시: `quarantine/l2/non_monotonic_ts/market/transaction/schema_version=tick.v1.1/tier=L2/exchange=bithumb/symbol=KRW-BTC/date=2026-05-13/hour=14/node=MERGED/part-{run_id}.parquet`. 운영자 manual review 의무 + 자동 retry 0 (Phase 2 scope) + 재처리 도구 = post-mortem 시점 별 Story 발의 결정 (e.g., `tools/quarantine_review.py`).
4. **Streaming write 의무 (D3)**: `pa.concat_tables(tables).sort_by("ts_utc")` 단일 buffer 호출 패턴 금지. chunk-based concat (chunk size = 1024 rows) + `ParquetWriter.write_table(chunk, row_group_size=100_000)` per-chunk loop. memory peak ≤ 1 GB (현재 OOM exit 137 32GB 임계 차단) + raw_json column `large_string` i32 offset 4 GB overflow 차단 (§D11.9.6 cross-bind). L2/L3 동형 패턴 의무.
5. **DualWriter `data=Path` streaming (D6 / R-EXTRA)**: caller (`compactor.runner._dispatch_dual_write`) 가 `parquet_path.read_bytes()` 호출 횟수 2회 → 1회 압축. sha256 = caller streaming hash 산출 (단일 read), DualWriter 호출 = `dual_writer.write(data=parquet_path, sha256=<hex>)` (data=bytes 전달 폐기). DualWriter 변경 0 (MCT-151 land `data: Path | bytes` accept signature 유지, `data=Path` 시 NAS PUT 시점 자체 read). memory 재할당 OOM 차단.
6. **Prometheus emit (cadence + quarantine 관측)**:
   - `compactor_quarantine_total{tier,reason}` Counter (D4 violation surface, tier ∈ {l2, l3}, reason ∈ {non_monotonic_ts, …} bounded low cardinality)
   - `compactor_malformed_frame_total{channel,exchange}` Counter (D7 P1 nullability finding surface, channel ∈ {transaction, orderbooksnapshot, orderbookdepth}, exchange ∈ collector emit 종류 bounded low)
   - Grafana alert 임계 1+ 추가 의무 (Phase 2 또는 후속 ops Story scope, MCT-160 retro 시 surface)

**채택 효과**:
- L1 backlog 자연 drainage 가속 (D5 verify — Phase 2 land 후 1h drainage rate ≤ ingest rate 박제 의무)
- L2/L3 NAS upload 정상 (#3 bucket bithumb-only 차단 자연 해소 — transaction / upbit 등 다른 channel/exchange 도 자연 누적)
- L2 OOM exit 137 차단 (#5 manual L2 OOM 차단, streaming write 32GB → ≤1GB 99.97% 감소)
- DualWriter memory 재할당 OOM 재발 차단 (R-EXTRA, `read_bytes()` 호출 2회 → 1회)
- forward-only invariant 강화 (post-write verify 의무 박제, silent corruption 차단)

**Out-of-scope (본 amendment 한계)**:
- **backfill_orchestrator silent skip** (MCT-153) = 동일 silent skip pathology 가능 → MCT-159 또는 별 Story scope (D8 OUT OF SCOPE, MCT-160 §6 D8 결정 정합)
- **upbit L1 partition 0 별 root cause** = MCT-160 의 D2 fix 후 verify only (D9 verify only). 별 fix 필요 시 후속 Story (e.g., MCT-164 upbit-specific path discovery 또는 ingester WAL path layout 진단)
- **L2/L3 cadence resolver 공통화 refactor** = MCT-163 별 Story scope (D11 — duplicate code 허용, MCT-160 = L2/L3 각자 cadence 정상화)
- **MCT-153 손실 재발 방지 (bucket versioning)** = MCT-161 reserve 별 Story 책임 (D9 amendment 정합, 본 MCT-160 영향 0)

Cross-references: Story `docs/stories/MCT-160.md` §1-§11 + scope_manifest `EPIC-compactor-operations.yaml` MCT-160 design_decisions + Plan `docs/superpowers/plans/2026-05-13-mct-160-l2-l3-cadence-streaming.md` + Spec `docs/superpowers/specs/2026-05-13-compactor-operations-design.md` + ADR-009 §D2.7 nullability discipline amendment (sibling).

**MCT-164 amendment 박제 (2026-05-14)** — 미지원 source channel silent-skip 차단 (multi-channel exchange 영역 확장). MCT-165 V2 verify 잔존 YES (upbit L1 partition 0) trigger.

**Background**: ADR-027 Amendment 1 (MCT-160) 의 silent-skip 차단 정책이 cadence path 영역. 본 amendment = **multi-channel exchange source** 영역으로 확장. upbit WAL = orderbooksnapshot 만 emit, L1 dataset = orderbookdepth 인데 compactor 가 orderbooksnapshot source 처리 미구현 → silent skip 위험 (정확한 root cause = MCT-164 §10 진단 결과 후 박제).

**Decision**:

1. **미지원 Source Silent-skip 차단**: L1 / L2 / L3 compactor 가 미지원 source channel 발견 시 silent skip 금지 → **fail-fast + surface 의무**.
2. **Prometheus emit**: `compactor_unsupported_source_total{tier, exchange, channel}` Counter +1.
3. **ADR-017 Amendment (MCT-164 sibling)** 의 channel matrix SSOT dispatch 의무.
4. **변환 미구현 시 ValueError**: `ValueError(f"compactor: unsupported source {channel} for {exchange}/{tier} — see exchange-channel-matrix")` raise.

**검증 의무**:

- MCT-166 fix Story = 본 amendment 정합 검증 의무 (compactor source 분기 코드에 fail-fast 적용)
- Phase 2 회귀 test = upbit orderbooksnapshot source 주입 → ValueError + Prometheus emit 확인
- channel matrix 진단 결과 (`docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md`) 와 정합 검증

**Cross-ref**:

- ADR-017 Amendment (MCT-164 sibling — compactor source 규약 + channel matrix SSOT)
- MCT-165 V2 (upbit L1 trigger source — verify-d5-2026-05-14.md §V2)
- MCT-164 (본 amendment 발의 Story)
- MCT-166 (fix Story, 본 amendment 정합 fix 의무)
- Cross-references: Story `docs/stories/MCT-164.md` §1-§12 + ADR-027 Amendment 1 (MCT-160 cadence path silent-skip) sibling

**MCT-161 amendment 박제 (2026-05-14)** — NAS bucket versioning + Object Lock governance 30d + Lifecycle ILM + DR runbook. EPIC-compactor-operations milestone 3/3 closure gate.

**Background**: MCT-153 손실 (4.2 GiB / 1370 obj, RETRO-MCT-156 §13.5.2) = bucket versioning 미활성으로 hard delete vs 미진입 식별 불가, 영구 복구 불가. 본 amendment = prevention + DR. EPIC-tier-promotion-single-source D9 prerequisite (sequential, MCT-161+163).

**Decision (Codex 합성 + Sonnet 채택)**:

1. **Bucket versioning enable** (D1=A 30d retention): `mctrader-market` bucket `Status: Enabled` (MinIO admin API `put_bucket_versioning`). hard delete 시 DeleteMarker 만 추가, version history 보존.
2. **Object Lock governance 30d** (D5=A): GovernanceRetention 30d. 30d 이내 version delete 시 GovernanceRetentionPolicy violation error (사용자 명시 override 가능). MCT-153 같은 hard delete 실수 30d 복구 window 보장.
3. **Lifecycle ILM** (D1=A): `NoncurrentVersionExpiration 30d` 자동 expiration. storage cost 1.5x 미만 (append-only 특성 1.1x-1.3x 예상).
4. **DeleteMarker replication OFF** (D4=B, 향후 replication 도입 시 적용): logical delete attack (실수 또는 악의) 보호 의무. 본 amendment scope 의 default 박제.
5. **Hot path 무영향** (D7=A, INV-1): collector WAL append + L1 ParquetWriter latency 영향 0. ADR-027 §D5 정합. Integration Test 5 (MCT-156 박제) 회귀 검증 의무.
6. **DR runbook** (D8=A): `docs/runbooks/nas-bucket-disaster-recovery.md` 신규 author. NAS data loss / hard delete / restore-from-version 5-step 단계별 명시. Chaos/bit rot scenario = 후속 Story (D8=A scope 제한).
7. **Replication 후속 별 backlog Story** (D2=D, single NAS box 환경): mcnas02 물리 부재 + cloud replication cost/credential 부담 cumulative — 본 amendment scope 외 명시. Phase 2 retro 시 별 Story reservation (예: MCT-174 placeholder).
8. **btrfs snapshot weekly** (D6=B): runbook 박제만 (host cron 별 작업), Story scope 외.

**검증 의무**:

- AC-1 `get_bucket_versioning() == "Enabled"` + delete 시 DeleteMarker
- AC-2 `get_object_lock_configuration` GOVERNANCE 30d
- AC-3 `get_bucket_lifecycle_configuration` NoncurrentVersionExpiration 30d
- AC-4 DR runbook 5-step 실행 가능
- INV-1 hot path latency 회귀 0 (Integration Test 5 통과 재검증)

**Cross-ref**:

- MCT-153 손실 evidence (RETRO-MCT-156 §13.5.2)
- MCT-159 D7 (versioning 미활성 식별, 본 amendment trigger source)
- MCT-147 (NAS deployment fact + 4중 mitigation)
- MCT-167 (EPIC-tier-promotion governance, 본 amendment prerequisite consumer)
- EPIC-compactor-operations milestone 3/3 closure gate
- ADR-027 §D5 (hot path 무영향, INV-1 정합)

### D5. Failure mode — compactor retry queue + alert, hot path 무영향 (MCT-167 amend: L1 NAS dual-write 도입 + capacity-bounded ingest block)

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

**MCT-167 amendment 박제 (2026-05-14, EPIC-tier-promotion-single-source, ADR-029 publish)** — D5 의 두 변경.

1. **L1 NAS upload 금지 invariant 폐기** (ADR-029 D1=B 채택) — ADR-027 원안 D5 본문 "L1 hot path = 본 amendment scope 외 (DualWriter inject 0, ingester service `MINIO_*` env 변경 0 = L1 NAS upload 0 invariant 유지)" 는 **무효화**. L1 ParquetWriter atomic 직후 (compactor 측) DualWriter 호출 의무 박제 (ADR-029 D1). 본 amendment 후 DualWriter status enum 3종 정책은 L1 tier 에도 동일 적용 — `committed` = 정상 / `local_only` = retry_queue enqueue / `hard_floor_blocked` = SOP MANUAL_GATE.

2. **capacity-bounded ingest block 도입** (ADR-029 D5 + D11) — NAS unreachable 시 정상 운영 시 hot path 영향 0 의 invariant **유지** but 다음 capacity threshold 도달 시점에만 collector ingest block:
   - **WAL local volume usage >= 30 GiB** → collector SIGTERM-like soft stop (graceful + alert) (ADR-029 D11 WAL hard limit)
   - **L1 local volume usage >= 20 GiB** → L1 compactor pause (NAS verify 까지 대기, 새 L1 derive 차단) (ADR-029 D11 L1 hard limit)
   - **alert chain**: NAS unreachable 검출 + capacity 80% threshold + 95% threshold + hard limit → Grafana alert + Slack notification

본 amendment 후 hot path 무영향 invariant 의 정확한 의미 = **NAS 가용성 정상 운영 시 hot path 영향 0** (NAS unreachable 단기 시점 + WAL/L1 hard limit 미도달 시점). NAS 무한 장애 + capacity hard limit 도달 시점에는 collector ingest block (fail-safe, ingest loss 보다 block 우선).

cross-ref: ADR-029 D1 (L1 NAS PUT timing) + D2 (DualWriter retry_queue 재사용) + D5 (capacity-bounded ingest block) + D11 (4 layer capacity 제한 정책).

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

**MCT-159 amendment 박제 (2026-05-13)** — backlog migration path 의 7종 invariant ALL PASS gate enforce. 본 Story 의 `BackfillOrchestrator` 재호출 path (channel parametrize + hour key 처리 2 amendment 후) 가 MCT-151 InvariantHarness inject 자동 동작 — byte-level sha256 + set-level object count + parquet row count + schema-level column count + column name order + dtype identity + schema_version pin **7종 sequential unconditional verify**. 1종이라도 FAIL 시 NAS PUT 차단 + quarantine 분리 + retry queue enqueue (NASUploader retry 자동) + SOP MANUAL_GATE escalation 의무. D6 invariant wording 변경 0 = invariant SSOT 정합, backlog migration path 의 자동 적용 명시만.

**MCT-159 FIX Iter 1 amendment 박제 (2026-05-13T11:40:44Z, Story §10 FIX Ledger Iter 1 trigger)** — D6 의 column_count invariant 의 **channel-aware** resolve.

D6 본문 line 149 "**column count**: ADR-009 §D2.1 16-col 의무 (== 16, per file)" 의 **OHLCV channel 가정** 박제 = 본 amendment 로 channel-aware 확장. Production deploy verification 시 `column_count_fail` 빈발 surface — InvariantHarness `_expected_column_count=16` fixed enforce vs 실 schema (orderbook_snapshot.v1=11 / tick.v1=8) cardinal mismatch.

**Amended D6 column_count invariant wording**:

> 4. **column count** (channel-aware, ADR-009 §D2.6 `ADR009_CHANNEL_SCHEMA_MATRIX` SSOT 정합):
>    - **Primary**: partition prefix `schema_version=*` extraction → matrix lookup (`{orderbook_snapshot.v1=11, tick.v1=8, tick.v1.1=11, ohlcv.v1=16}`)
>    - **Fallback**: caller 측 `expected_column_count` explicit injection (backward-compat — OHLCV cutover path 회귀 0)
>    - **Miss**: unknown schema_version → `column_count_fail` with diagnostic `unknown_schema_version` (schema evolution detection)

D6 7종 enum wording 변경 0 (`column_count_fail` enum 보존, resolve 방식만 channel-aware 확장).

### §D6.1 chunk_unit ↔ verify_unit contract (MCT-159 FIX Iter 1 신규)

**Amendment trigger**: MCT-159 production deploy verification 의 `object_count_fail` 빈발 surface — chunk_spec (per-file PUT) vs `_check_object_count` (per-partition glob) **단위 mismatch**: single chunk PUT 후 verify 시점 local 12 file vs NAS 1 object → 즉시 fail.

**Contract 박제** (양 단위 일치, per-file basis):

- **chunk_unit**: per-file PUT (1 .parquet file = 1 chunk_id, MCT-153 `BackfillOrchestrator.ChunkSpec` 박제 보존)
- **verify_unit**: per-file (post amend)
- **invariant_scope_per_file** (7종 ALL PASS gate 의 per-file 적용 영역):
  - byte-level: sha256
  - schema-level: column_count + column_order + dtype + schema_version
  - row-level: parquet row_count (per file, NOT cross-file aggregation)
- **invariant_scope_per_partition** (optional Phase 3 후속 verify cycle):
  - set-level: total file count (partition aggregation) — 적용 시점 = partition 전체 PUT 완료 confirmation 후 별 verify pass (현 amendment scope 외)

본 §D6.1 contract = MCT-153/156/159 `BackfillOrchestrator` 의 chunk 단위 박제 보존 + InvariantHarness verify 단위 일치. 본 amendment 의 MCT-151 InvariantHarness 적용 = MCT-159 FIX Iter 1 **Phase 2 follow-up PR** (mctrader-data) scope.

Cross-references: ADR-009 §D2.6 (`ADR009_CHANNEL_SCHEMA_MATRIX` SSOT, MCT-159 FIX Iter 1) + Story `MCT-159.md` §10 FIX Ledger Iter 1.

### D7. Local GC — 7일 grace + dry-run 선행 + 디스크 압박 시 tier/date 순차 (MCT-167 amend: L1 tier grace 0)

cutover 후 local volume 의 L2/L3 cold tier 자산 삭제 절차:

1. **7일 grace period** — reader endpoint cutover (D4 step 3) 후 7일 동안 local volume 유지. emergency fallback 가능.
2. **dry-run 선행** — `cold_gc --dry-run` 으로 삭제 대상 list 산출 + user review.
3. **실 삭제** — dry-run 결과 OK 시 `cold_gc --execute` 실행.
4. **디스크 압박 시 순차** — disk usage > 90% 시 tier (L3 → L2 순) + date (oldest first) 순차 GC.

- **Rationale**: data loss 방지 3중 lock (grace + dry-run + 순차). 7일 grace = engine reader cutover 후 정상 운영 검증 buffer.
- **Alternative rejected**: immediate GC (cutover 직후) — emergency fallback 불가 → 거부.

**MCT-167 amendment 박제 (2026-05-14, EPIC-tier-promotion-single-source, ADR-029 publish)** — D7 의 L1 vs L2/L3 grace 정책 분리.

- **L2/L3 tier (cold tier)** = 본 D7 wording 답습. 7일 grace + dry-run + 순차 GC 정책 = **변경 0**.
- **L1 tier (hot tier, MCT-167 신규 NAS 격상)** = **grace 0** (ADR-029 D3=C 채택). L1 NAS PUT 완료 + NAS HEAD verify (version/etag exact match + sha256 verify) 후 즉시 local L1 file 삭제. tier promotion (L1 → L2 / L2 → L3) 시 동일 정책 적용.
- **L1 grace 0 rationale**: ambiguity 차단 invariant (ADR-029 D10) — "tier promotion 완료 후 동일 logical entity 가 NAS + local 양쪽 동시 존재 시 violation" 의 enforce. version/etag exact match + sha256 verify 가 false delete risk mitigation (ADR-029 R4).
- **L1 trigger 조건**: ADR-029 D11 4 layer capacity 제한 (L1 hard limit 20 GiB) 도달 시점에 oldest L1 FIFO delete (NAS verify 후, 정상 운영 시 7-day rolling cleanup).
- **dry-run 의무 (L1)**: L1 grace 0 정책에도 production deploy 의 production evidence gate 의무 (ADR-029 D10 + codeforge-plugin#620 Fix-1) — 1h production 측정 0 ambiguity violation evidence 박제 의무.

cross-ref: ADR-029 D3 (L1 immediate delete) + D10 (ambiguity invariant) + D11 (L1 hard limit 20 GiB).

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

**MCT-159 amendment 박제 (2026-05-13)** — mixed layout 본문 재해석 (legacy 사실상 무존재 박제). ADR-027 §D9 의 MCT-156 amendment 본문은 NAS bucket 의 (a) MCT-153 backfill 산출물 legacy ADR-009 §D2.1 layout + (b) MCT-156 Phase 2 신규 hot pipeline 산출물 mixed 공존 박제. **그러나** 2026-05-13 Stage 3 wiring deploy verification 실측에서 (a) 4.2 GiB / 1370 obj 의 NAS 측 손실 확정 박제 (`mctrader-market` bucket versioning 미활성 = 복구 불가, RETRO-MCT-156 §13.5.2 박제). 즉 본 시점 NAS bucket 의 mixed layout 구성 = (b) 신규 schema only — (a) 사실상 무존재. reader fallback (ADR-009 §D2.1+§D14) 은 본 Story 의 MCT-159 이관 산출물 (`hour=HH` + `node=MERGED`) 도 자연 양립 의무 (engine `scan_*` API partition pruning 변경 0) but legacy 객체 부재로 fallback 의존도 = 0. local source (`/var/lib/mctrader/data/market/`) 보존 = forward-only invariant (ADR-009 §D12.2) 위반 0 — MCT-159 의 `BackfillOrchestrator` 재호출 = NAS replica 복구 backfill (재이관) 자연 정합. MCT-153 손실 재발 방지 = MCT-161 reserve (bucket versioning 활성화 + replication 정책 + sequential 의무) 별 Story 책임 — 본 amendment scope 외.

**MCT-167 amendment 박제 (2026-05-14, EPIC-tier-promotion-single-source, ADR-029 publish)** — D9 SoT scope 전면 격상.

ADR-027 §D9 원안 = "**NAS = Source of Truth (SoT) — L2/L3 cold tier 의 authoritative read source**". 본 amendment 박제 후 SoT scope = **all-tier (L1 + L2 + L3) 확장**:

- **NAS = SoT for ALL tiers** — L1 (hot path, 5min Parquet) + L2 (warm, 1h Parquet) + L3 (cold, 1day Parquet) 모두 NAS = authoritative read source.
- **local = ephemeral cache only** — engine 호스트 측 + compactor 호스트 측 모두 local = LRU/TTL cache (read latency optimization). write authority 0.
- **ambiguity 차단 (ADR-029 D10)** — "tier promotion 완료 후 동일 logical entity 가 NAS + local 양쪽 동시 존재 시 violation" invariant 박제.
- **reader read-through cache 정책** = ADR-029 D7 (95% hit + p99 <100ms aggressive cache 목표) 답습. MCT-170 impl scope.
- **forward-only invariant 정합** (ADR-009 §D12.2 amendment 박제) — tier promotion 후 local delete = forward-only 위반 0. NAS object SoT 격상 (versioning 기반, MCT-161 박제) 으로 enforcement layer 격상.
- **local fallback (migration window)** = ADR-029 D8 답습. 새 데이터 (cutover 이후) = NAS-first, 기존 local data (cutover 이전) = local fallback 지원. point-in-time mixed layout 호환 (MCT-156/159 amendment 본문 답습).
- **MCT-170 impl scope** = `mctrader_engine/io/tier_reader.py` 신규 (cold_reader rename + L1 확장) + `reader_cache.py` LRU L1 추가 + `endpoint_router.py` NAS-first + DR mode degradation.

cross-ref: ADR-029 D7 (cache 95% hit) + D8 (forward-only + local fallback) + D10 (ambiguity invariant) + ADR-017 §3 D3 amendment (L1 NAS PUT 의무) + ADR-009 §D12.2 amendment (NAS object SoT 격상).

**MCT-183 amendment box 박제 (2026-05-16, EPIC-data-domain-decoupling Story-2 — io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2 소유)** — D9 reader 거주 repo 이전.

ADR-027 §D9 + 본 §D9 의 MCT-156/159/167 amendment 본문은 reader read-through cache 의
impl carrier 를 `mctrader_engine/io/` (`endpoint_router.py` / `reader_cache.py` /
`cold_reader.py` + MCT-167 amendment §D9 의 `tier_reader.py` / `l1_reader.py` /
`dr_mode.py`) 로 박제했다. **본 amendment 박제 후 io reader 6 module 의 거주 repo =
`mctrader-engine` → `mctrader-data` (`src/mctrader_data/io/` 서브패키지, Layer2 단독
소유)** 로 이전됨:

- **endpoint_router + dr_mode + reader_cache + cold_reader + tier_reader + l1_reader
  6 module = mctrader-data relocated** (byte-equivalence — 코드 본문 무변경, import
  path cross-reference 재지정만). 거주 repo 만 engine → data, **동작·invariant 전수
  무변경**.
- **MCT-156 amendment "io/ 3 module 영향 0" = 거주 이전 후에도 동작 영향 0 정합 명시**
  — MCT-156 amendment 박제분 ("MCT-154 land 의 `endpoint_router.py` / `reader_cache.py`
  / `cold_reader.py` 모두 본 amendment 영향 0 (변경 0)") 의 mixed layout 호환
  (ADR-009 §D2.1 `node=DEFAULT` + §D14 `tier=L1` fallback) 은 거주 repo 가
  mctrader-data 로 이전된 후에도 동일 보존 (engine `scan_*` API partition pruning
  변경 0 = data 측 io reader 도 동일 fallback 박제 의무 — 동작 byte-equivalence).
- **이전 근거 (Layer2 read 도메인 단독 소유, ADR-031 §D2)**: read 도메인은 storage
  지식 (NAS object layout / parquet tier / ETag verify / endpoint resolution) 을
  내포 → Layer2 (mctrader-data = DATA-STORAGE 영역 단독 소유) 거주가 EPIC-data-
  domain-decoupling 4-layer 목표 정합. engine io/ src caller 0 (dead-in-prod, MCT-183
  §0 V3 HEAD 실증) → production 무중단 물리 이전.
- **endpoint_router atomic flip (immutable swap) + 7d grace mode + dr_mode state
  machine (CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER, MCT-170 amendment) + UNKNOWN_TIER
  30d exemption window enforcement = 거주 이전 후에도 무변경 보존** (Story MCT-183
  INV-5 — 동작·invariant 무변경 SSOT 격리).
- **본 amendment scope** = io reader 거주 repo 이전 박제 only. ADR-027 §D9 본문 +
  MCT-156/159/167 amendment 의 SoT 모델·mixed layout 호환·forward-only invariant
  자체는 **무변경** (relocate ≠ 정책 변경). engine cold-read 실경로 data REST
  indirection 은 본 amendment scope 외 — **MCT-185 (cold-read cutover) owner**
  (ADR-029 MCT-183 amendment box 정합).

**D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply)**: scope_manifest
`§planned_adrs.amendments` ADR-027 (`section: io reader 6 module (endpoint_router/
dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data
Layer2` / `change: engine io/ 측 io reader 6 module (endpoint_router + dr_mode +
reader_cache + cold_reader + tier_reader + l1_reader) = mctrader-data 로 relocated
(Layer2 소유). endpoint_router/dr_mode = ADR-027 §D9 명시 module, 나머지 4 = io/
묶음 relocate (ADR-027 box 본문 정합)` / `owner_story: MCT-183 (io reader 6 module
relocate)`) ↔ `§design_decisions.D2` (`io-relocate + cold-read-behind-REST`) ↔
`§story_decision_matrix.MCT-183` (`decisions: [D2, D6]`) ↔ 본 amendment box **전수
1:1 정합** (MCT-182 D-row 7/7 reconcile 패턴 계승). endpoint_router/dr_mode 는
ADR-027 §D9 (MCT-156/167 amendment) 명시 module, 나머지 4 (reader_cache/cold_reader/
tier_reader/l1_reader) 는 io/ 6 module 묶음 relocate — scope_manifest section/change
↔ ADR-027 box 본문 6-module 전체 동일 (P0-1 reconcile, MCT-179/182 cross-document
desync 동형 재발 차단).

cross-ref: ADR-029 MCT-183 amendment box (io reader 6 module relocated + engine NAS
직독 폐기 예고) + ADR-031 §D2 (io-relocate 절반 진행, §D2 VERIFIED = MCT-185 cutover
후) + `docs/stories/MCT-183.md` §0/§4.3 + `docs/change-plans/MCT-183-change-plan.md`
§3/§11.

**§D9 amend confirm — MCT-188 final (2026-05-17, EPIC-data-domain-decoupling Story-7)**:
MCT-183 LAND (io reader 6 module relocated to mctrader-data) + MCT-185 LAND (engine
cold-read cutover 완결 + engine NAS 직독 폐기) + MCT-188 (engine pyproject mctrader-data
의존 제거 + shim import 4곳 최종 제거) 3단계로 ADR-027 §D9 reader 재배치 완결.
**engine io/ 6 module = mctrader-data Layer2 소유 영구 확정** (engine 측 io/ 전무 — dead-in-prod
삭제 MCT-183, engine import 전면 제거 MCT-188). ADR-027 본문 무변경 (POLICY_FINALIZED 보존).
cross-ref: `docs/adr/ADR-031-data-domain-decoupling.md` §D7 VERIFIED (MCT-188 LAND).

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
- 2026-05-13 — **D4/D6/D9 amendment** (MCT-159, EPIC-cold-tier-stage-3-wiring sibling — L2/L3 cold tier backlog NAS migration). Stage 3 wiring (MCT-156 LAND) 후 hot pipeline NAS PUT 정상화되었으나 wiring 이전 로컬 누적 L2/L3 backlog (8.85 GiB / 7118 file, orderbooksnapshot + transaction × L2/L3) 의 자연 cadence 적용 외 영역 (orderbookdepth channel NotImplementedError 영구 fail, L2 자연 trigger ETA 9.2h 무효). D4 = backlog migration wiring obligation 박제 (MCT-153 BackfillOrchestrator channel parametrize + hour key 처리 2 amendment 후 재호출). D6 = 7종 invariant ALL PASS gate backlog path 자동 적용 명시 (MCT-151 InvariantHarness inject, wording 변경 0). D9 = mixed layout 재해석 (RETRO-MCT-156 §13.5.2 박제 — legacy NAS 4.2 GiB 손실 확정으로 (a) 사실상 무존재, reader fallback 의존 0, local source 보존 = forward-only invariant 위반 0, MCT-161 reserve 별 Story versioning 활성화 책임).
- 2026-05-14 — **MCT-164 amendment** (multi-channel exchange silent-skip 차단). ADR-027 Amendment 1 (MCT-160 cadence path) sibling — multi-channel source 영역 확장. L1/L2/L3 compactor 의 미지원 source channel = fail-fast + `compactor_unsupported_source_total{tier,exchange,channel}` Counter emit + channel matrix SSOT dispatch 의무. MCT-165 V2 verify 잔존 YES (upbit L1 partition 0) trigger. ADR-017 Amendment (channel matrix SSOT) sibling.
- 2026-05-14 — **MCT-161 amendment** (NAS bucket versioning + Object Lock governance 30d + Lifecycle ILM + DR runbook). EPIC-compactor-operations milestone 3/3 closure gate. MCT-153 4.2 GiB 손실 prevention + DR. Decision 8 (versioning Enable / Object Lock 30d / NoncurrentVersionExpiration 30d / DeleteMarker replication OFF / hot path 무영향 INV-1 / DR runbook 5-step / replication 후속 별 backlog Story D2=D / btrfs snapshot runbook 박제만 D6=B). EPIC-tier-promotion-single-source D9 prerequisite (MCT-161+163 sequential, MCT-167 governance prerequisite consumer).
