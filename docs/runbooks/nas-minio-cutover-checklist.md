# NAS MinIO — Reader Endpoint Cutover Checklist (MCT-154)

**Owner**: Operator (사용자)
**Story**: MCT-154 — Stage 2 Phase D singleton (reader endpoint cutover + cache barrier + dual-write 7d 연장)
**ADR refs**: ADR-027 D4 step 3 (reader endpoint 전환) + D9 (read-through cache)
**Prerequisite Stories**: MCT-150 / MCT-151 / MCT-152 / MCT-153 (ALL MERGED)
**Stage 2 종료 gate AC-2 의 single source**: 본 runbook 완료 = `nas_write_ratio == 1.0` for 7d grace evidence

## 핵심 원칙 (사용자 directive: "RPO=0 + 절대 유실 금지")

본 cutover = **3중 lock**:

1. **Cache flush + verify barrier** (S3, AC-2) — endpoint flip 전 stale cache 강제 무효화
2. **Dual-write 7d grace 연장** (S9, AC-3) — cutover 후 7일간 mctrader-data 측 dual-write 유지 (rollback 능력 보존)
3. **Engine smoke test** (AC-5) — 첫 NAS read 정상 동작 입증 (latency p99 ≤ MCT-148 T2 ±15%, sha256 identity, 16-col schema invariant 4종, cache hit ratio, legacy partition verify)

각 단계 실패 시 **즉시 Rollback procedure 진입** — RPO=0 보존이 진행 보다 우선.

---

## Phase 0 — Pre-cutover Gate

다음 모든 항목이 ✅ 일 때만 Phase 1 진입.

- [ ] **MCT-153 BackfillOrchestrator 실 운영 완료 verify**
  - command: `docker exec mctrader-data python -m scripts.migration.run_backfill --tier=L2 --execute` 실행 결과 = `BackfillResult.status="all_chunks_verified"`
  - evidence: `mctrader-data/.tmp/evidence-pack-MCT-153.md` §1 Overview 박제 + §3 per-invariant ALL PASS

- [ ] **7종 invariant ALL PASS evidence 확인**
  - MCT-151 InvariantHarness 7종 (sha256 / object_count / row_count / column_count / column_order / dtype / schema_version) per-chunk ALL PASS
  - evidence: MCT-153 evidence pack §3 Per-invariant FAIL Distribution = 0

- [ ] **Dual-write window invariant verify ALL PASS 7일 누적**
  - MCT-152 `dual_write_window_runner` cron 결과 = 7일 연속 invariant verify ALL PASS
  - evidence: Prometheus query `nas_invariant_verify_total{status="all_pass"}` 7일 누적 == cron invocation count

- [ ] **MCT-148 T2 latency baseline cross-reference 확인**
  - 50MB p99 = 2870.65ms (NFR-1 충족)
  - upper bound (±15%): 50MB p99 < ~3300ms

- [ ] **MCT-152 IOPS during baseline cross-reference 확인**
  - mctrader-data evidence pack §5 IOPS During Snapshot 측정값 확인
  - cutover 후 read IOPS 추가 부하 host disk I/O 한계 surface 검증 input

- [ ] **NTP 동기화 verify** (§7.4.3 mitigation)
  - command (mctrader 호스트): `timedatectl status` → "NTP synchronized: yes" 확인
  - drift > 5min 시 NTP 동기화 대기 후 재진입

- [ ] **NAS endpoint 가용성 사전 ping** (§7.4.2 mitigation)
  - command: `docker exec mctrader-engine python -c "import boto3; c=boto3.client('s3', endpoint_url='${MINIO_ENDPOINT_NEW}'); print(c.head_bucket(Bucket='mctrader-cold-tier'))"`
  - 정상 응답 시 진행 / 실패 시 Phase 0 차단

- [ ] **사용자 explicit confirm**
  - cutover 진행 결정 사용자 직접 confirm (chat / commit message 박제)

---

## Phase 1 — Cache Flush + Verify Barrier (S3 박제, AC-2)

reader_cache 측 stale entry 강제 무효화 + verify probe gate.

- [ ] **`reader_cache.flush_all()` invoke**
  - command:
    ```bash
    docker exec mctrader-engine python -c "
    from mctrader_engine.io import ReaderCache
    cache = ReaderCache()
    result = cache.flush_all()
    print(result)
    assert result.status == 'flushed', f'flush failed: {result.status}'
    "
    ```
  - 결과: `CacheFlushResult(status='flushed', flushed_count=..., remaining_count=0, ...)`

- [ ] **flush retry budget 3회** (verify probe 실패 시)
  - `status="verify_probe_failed"` 또는 `status="partial_flush_failed"` 검출 시 즉시 재실행
  - 최대 3회 retry — 모두 fail 시 **Phase 1 차단 + 사용자 manual gate** (cache fresh process restart 권고)

- [ ] **`verify_flushed()` 추가 verify (defensive)**
  - command: `docker exec mctrader-engine python -c "from mctrader_engine.io import ReaderCache; print(ReaderCache().verify_flushed())"`
  - 결과: `True` 시 Phase 2 진입 / `False` 시 retry

**Phase 1 차단 시 Rollback**: cache flush 자체 차단 → endpoint flip 진입 전 단계 → 운영 영향 0 (read 측 local volume 유지). 사용자 manual gate 후 재시도.

---

## Phase 2 — Endpoint Flip + Atomicity Verify (AC-1)

`MINIO_ENDPOINT` env 단일 변경 + atomic flip mechanism.

- [ ] **mctrader-engine 컨테이너 `MINIO_ENDPOINT` env 갱신**
  - `.env` 파일 측 `MINIO_ENDPOINT=https://<NAS endpoint URL>` 갱신 (0600 + gitignored 정합)
  - docker compose restart or hot-reload (env 적용)

- [ ] **`endpoint_router.flip()` invoke**
  - command:
    ```bash
    docker exec mctrader-engine python -c "
    from mctrader_engine.io import EndpointRouter
    router = EndpointRouter(grace_state_path='/etc/mctrader/cutover_state.yaml')
    result = router.flip(new_endpoint='${MINIO_ENDPOINT}', activate_grace=True, grace_days=7)
    print(result)
    assert result.status == 'flipped', f'flip failed: {result.status}'
    "
    ```
  - 결과: `EndpointFlipResult(status='flipped', new_endpoint=..., previous_endpoint=..., grace_started_at_iso=...)`

- [ ] **flip atomicity violation 0 verify** (defensive)
  - Prometheus query: `engine_cold_reader_endpoint_flip_total{status="flip_blocked"} == 0`
  - 위반 검출 시 즉시 Rollback procedure 진입

- [ ] **structured log evidence 박제** (T6 mitigation)
  - mctrader-engine container log 측 "endpoint_router.flip status=flipped" entry 확인
  - endpoint URL credential masked verify (host:port 만 박제)

**Phase 2 차단 시 Rollback**: `endpoint_router.rollback(previous_endpoint=...)` invoke + Phase 1 cache flush 재실행 + 사용자 manual gate.

---

## Phase 3 — Smoke Test + Evidence Pack (AC-4 + AC-5)

5+ sample partition NAS read + 4종 schema invariant + cache hit ratio + legacy partition verify.

- [ ] **sample partition fixture 박제** (deterministic, legacy 1+개 의무 포함)
  - 권고 5+ samples (BTC_KRW / ETH_KRW / XRP_KRW / SOL_KRW + legacy 1)
  - fixture file: `mctrader-engine/tests/io/fixtures/smoke_test_partitions.yaml` (Phase 2 impl 시점 박제) 또는 inline list

- [ ] **`cold_reader.run_smoke_test()` invoke**
  - command:
    ```bash
    docker exec mctrader-engine python -c "
    from mctrader_engine.io import ColdReader, EndpointRouter, ReaderCache
    router = EndpointRouter(grace_state_path='/etc/mctrader/cutover_state.yaml')
    cache = ReaderCache()
    reader = ColdReader(router, cache, bucket='mctrader-cold-tier')
    samples = [
      'tier=L2/exchange=BITHUMB/symbol=BTC_KRW/date=2025-11-01/node=ID1/data.parquet',
      'tier=L2/exchange=BITHUMB/symbol=ETH_KRW/date=2025-11-01/node=ID1/data.parquet',
      'tier=L2/exchange=BITHUMB/symbol=XRP_KRW/date=2025-11-01/node=ID1/data.parquet',
      'tier=L2/exchange=BITHUMB/symbol=SOL_KRW/date=2025-11-01/node=ID1/data.parquet',
      'tier=L2/exchange=BITHUMB/symbol=BTC_KRW/date=2024-12-01/data.parquet',  # legacy
    ]
    summary = reader.run_smoke_test(samples)
    print(summary['aggregated'])
    assert summary['aggregated']['fail_count'] == 0
    "
    ```
  - 결과: `aggregated.fail_count == 0` + 5/5 PASS

- [ ] **read latency p99 gate verify** (MCT-148 T2 ±15%)
  - per-sample read_latency_ms ≤ 3300ms (50MB upper bound) verify
  - drift 검출 시 즉시 Rollback procedure 진입

- [ ] **sha256 byte-level identity verify**
  - per-sample sha256 vs local 측 sample sha256 동일 verify (MCT-148 T3 PoC 패턴 정합)

- [ ] **16-col schema invariant 4종 ALL PASS verify**
  - MCT-151 InvariantHarness `verify_schema_only()` inject 시 column_count + column_order + dtype + schema_version pin ALL PASS

- [ ] **cache hit ratio > 0 verify**
  - smoke test 진행 중 동일 partition 재read 발생 시 cache hit ratio 측정
  - `cache_hit_ratio > 0` verify (LRU+TTL 정상 동작 evidence)

- [ ] **legacy `node=` 부재 partition 1+개 read 정상 verify** (S6 cross-check, AC-4)
  - sample 중 legacy 1+개 → `status="legacy_node_default"` + `is_legacy_node=True` + `nas_object_key` 에 `node=DEFAULT/` 명시 verify
  - MCT-153 backfill metric `nas_backfill_legacy_node_default_count` ↔ engine metric `engine_cold_reader_legacy_node_default_read_count` cross-reference

- [ ] **evidence pack 박제**
  - location: `mctrader-engine/.tmp/evidence-pack-MCT-154.md` (gitignored)
  - 구조 (10 sub-section, §6.6 박제):
    1. §1 Overview (cutover timestamp + endpoint masked + sample list + smoke status)
    2. §2 Per-sample Read Latency
    3. §3 Per-sample sha256 Identity
    4. §4 Per-sample 16-col Schema Invariant
    5. §5 Cache Hit Ratio
    6. §6 Legacy `node=` Partition Verify
    7. §7 Cutover Endpoint Flip Evidence
    8. §8 7d Grace Mode Activation Evidence
    9. §9 Cross-references (MCT-148 T2 / MCT-152 IOPS / MCT-153 backfill metric)
    10. §10 Anomaly Log

**Phase 3 차단 시 Rollback**: 1+ FAIL 검출 (latency p99 / sha256 / schema invariant / cache hit ratio / legacy partition not_found) → 즉시 `endpoint_router.rollback()` invoke + Phase 1 cache flush 재실행 + 사용자 manual gate.

---

## Phase 4 — 7d Grace Activation + Monitoring (AC-3 / S9)

cutover 직후 dual-write 7d 연장 운영 + daily invariant verify.

- [ ] **mctrader-data 측 dual_write_window_runner grace mode 활성화**
  - mctrader-data 측 config flag 갱신 (operator manual gate, MCT-152 dual_write_window_runner consume)
  - 양쪽 컨테이너 (mctrader-engine + mctrader-data) 의 grace mode 동기화 의무

- [ ] **`mctrader-hub/configs/cutover_state.yaml` git commit + push**
  ```yaml
  active: true
  started_at_iso: "2026-XX-XXT00:00:00+00:00"
  grace_days: 7
  last_invariant_verify_iso: ""
  last_invariant_status: ""
  ```
  - commit message: `[MCT-154] activate 7d grace post-cutover (Phase 4)`
  - PR or direct push (사용자 결정)

- [ ] **양쪽 컨테이너 redeploy or hot-reload**
  - mctrader-engine 측 `/etc/mctrader/cutover_state.yaml` re-read (process restart or file watch)
  - mctrader-data 측 동일

- [ ] **Prometheus monitoring 설정**
  - `engine_dual_write_grace_remaining_days` countdown query
  - `engine_dual_write_grace_active == 1` verify
  - daily 03:00 KST `dual_write_window_runner` cron 결과 monitoring

- [ ] **7d 동안 daily invariant verify ALL PASS gate**
  - MCT-152 dual_write_window_runner cron 결과 = ALL PASS (FAIL 시 즉시 alert + 사용자 결정 — grace reset 또는 endpoint rollback)
  - 7d 누적 PASS = MCT-155 GC 진입 prerequisite 충족

- [ ] **7d 만료 시점 evidence 박제**
  - `engine_dual_write_grace_expired_at` Prometheus metric 박제
  - evidence pack §8 7d Grace Mode Activation Evidence 갱신
  - **Stage 2 종료 gate AC-2 single source 박제 완료**

---

## Rollback Procedure (cutover 차단 또는 7d grace 중 trigger)

다음 조건 발생 시 즉시 진입:
- Phase 1 cache flush retry 3회 모두 fail
- Phase 2 flip atomicity violation 검출
- Phase 3 smoke test 1+ FAIL (latency / sha256 / schema / cache / legacy)
- Phase 4 grace 중 NAS endpoint 단절 또는 invariant FAIL

### Rollback steps

1. **`endpoint_router.rollback(previous_endpoint=...)` invoke**
   ```bash
   docker exec mctrader-engine python -c "
   from mctrader_engine.io import EndpointRouter
   router = EndpointRouter(grace_state_path='/etc/mctrader/cutover_state.yaml')
   result = router.rollback(previous_endpoint='https://local-volume-placeholder:9000')
   print(result)
   "
   ```

2. **`reader_cache.flush_all()` 재실행** (rollback 후 cache 보존 시 stale risk)

3. **sample 재read smoke** (local volume 측 read 정상 동작 verify)

4. **`mctrader-hub/configs/cutover_state.yaml` 갱신**
   - `active: false` + `started_at_iso: ""` 박제 (grace mode reset)
   - commit message: `[MCT-154] rollback — grace mode reset`

5. **mctrader-data 측 dual_write_window_runner grace mode 비활성화** (operator manual gate)

6. **alert escalation**
   - `EngineColdReaderRollback` metric emit (`engine_cold_reader_rollback_total`)
   - 사용자 manual gate — root cause 분석 후 재cutover 결정

### Rollback 능력 보존 prerequisite

- dual-write window (MCT-150/151/152) 가 cutover 후에도 7d 동안 유지되어야 rollback 가능 (S9 박제)
- local volume 측 데이터 미삭제 (MCT-155 GC 진입 전까지 보존)
- cutover_state.yaml git history audit trail 박제

---

## References

- ADR-027 D4 step 3 (reader endpoint 전환) + D9 (read-through cache "MCT-154 scope")
- Story file: `docs/stories/MCT-154.md` §6 Change Plan + §7 보안/운영 + §11 데이터 마이그레이션
- MCT-148 evidence pack (T2 latency baseline)
- MCT-152 dual_write_window_runner runbook (`docs/runbooks/nas-minio-unreachable-sop.md` 패턴 정합)
- MCT-153 BackfillOrchestrator (S6 `node=DEFAULT/` 명시 PUT enforcement)
- scope_manifest design_decisions S3 + S6 + S9
