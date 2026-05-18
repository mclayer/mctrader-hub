# Rekey Migration — SILENT_ZERO_NO_CANDIDATES (exit 4) Runbook

> **Version pin**: 본 runbook 은 `RekeyOrchestrator` M-10 silent-zero guard v1 박제
> (mctrader-data HEAD `2946ffc6` 기준 — U3-FIX PR #131 LAND 시점, ADR-034 §결정 4 + ADR-027 §D5 4xx fail-fast 정합).
> **`_discover_l1_objects` 또는 keyspace 변경 시 본 runbook 우선 amendment 의무 (drift 차단).**

| Item | Value |
|---|---|
| Story | U3-MIGRATE post-merge FIX (mctrader-data#89 §10 ledger post-merge-1) |
| Issue | mctrader-data#89 |
| Module | `mctrader-data/src/mctrader_data/nas_migration/rekey.py` (M-10 gate at `run()`) |
| ADR | ADR-034 §결정 4 (3-step migration safety) + ADR-009 §D12 (forward-only invariant) |
| Related | [nas-minio-secret-rotation.md](./nas-minio-secret-rotation.md) · [nas-minio-unreachable-sop.md](./nas-minio-unreachable-sop.md) · [nas-credential-rotation-automation.md](./nas-credential-rotation-automation.md) |

---

## Overview

`RekeyOrchestrator.run()` 의 silent-zero guard (M-10) 는 `--execute --i-understand-this-is-irreversible` 플래그로 운영자가 마이그레이션을 실행했으나 `_discover_l1_objects()` 가 **0 candidates** 를 반환했을 때 발화한다 (`exit 4` SILENT_ZERO_NO_CANDIDATES).

```
--execute + 0 candidates
       │
       ├──► [INV-C carve-out] manifest 에 ≥1 status='done' 존재
       │         → "already-migrated" 로 판단, exit 0 (정상 idempotent re-run)
       │
       └──► [SILENT_ZERO_NO_CANDIDATES] manifest 에 done 0 (한 번도 마이그레이션 실행 안 됨)
                 → SystemExit(4) + Prometheus counter under-report 차단 + operator alert
```

**왜 필요한가**: U3-FIX (PR #131) 이전의 마이그레이션 도구는 잘못된 keyspace prefix (`l1/<exchange>/<channel>/`) 로 객체를 검색해 production 의 실제 keyspace (`l1/market/<channel>/.../tier=L1/exchange=<exchange>/`) 와 불일치, **0 객체 발견 + success-with-zero 보고 → 117GB / 4,608 객체 silent no-op migration** 위험을 안고 있었다. M-10 은 그 회귀 차단용 operator-visible backstop.

---

## 1. exit 4 발화 즉시 확인 사항 (5분 이내)

### 1.1 operator 콘솔 / 로그 확인

```
ERROR [rekey] ABORT: SILENT_ZERO_NO_CANDIDATES — _discover_l1_objects returned 0 candidates under --execute and no prior completion evidence (no manifest 'done' entry). Likely keyspace/credential defect. Run --dry-run first to confirm non-zero candidate count. exit 4
```

확인:
- `SystemExit(4)` 발화 직전 `discover` 단계의 로그 (`prefix=l1/market/<channel>/` + `total=<N>` 라인)
- manifest 파일 존재 여부: `<root>/audit/rekey-l1-manifest-<exchange>-<channel>.yaml`
- Prometheus counter `mctrader_l1_rekey_discovery_count_total{exchange,channel}` — 0 confirmed via metric

### 1.2 dry-run 우선 실행 의무 (재진단 첫 단계)

```bash
docker compose --profile migration run --rm rekey-migration \
  --root /var/lib/mctrader/data \
  --exchange <bithumb|upbit> \
  --channel <orderbooksnapshot|orderbookdepth|transaction> \
  --dry-run
```

기대 출력:
- 정상: `total=<positive integer>` (production 4,608 객체 기준)
- 비정상: `total=0` (계속) → §2 로 진행

---

## 2. 진단 시퀀스 (root cause 식별)

### 2.1 가설 #1: IAM/credential 권한 미설정 (가장 흔함)

`NAS_MINIO_REKEY_ACCESS_KEY` / `NAS_MINIO_REKEY_SECRET_KEY` 가 `l1/market/<channel>/` prefix 에 대한 `s3:ListBucket` 권한 누락.

**확인**:
```bash
# 임시 인증으로 list 시도
docker compose --profile migration run --rm \
  --entrypoint /bin/sh rekey-migration \
  -c 'aws --endpoint-url=$NAS_MINIO_ENDPOINT s3 ls s3://mctrader-market/l1/market/<channel>/ | head -5'
```

기대 출력:
- 정상: 객체 5건 이상 표시
- 비정상: `Access Denied` 또는 빈 출력 → IAM 정책 갱신 필요

**복구**:
- [nas-minio-secret-rotation.md](./nas-minio-secret-rotation.md) §3 IAM policy 갱신 절차 참조
- Required policy: `s3:ListBucket` + `s3:GetObject` + `s3:CopyObject` + `s3:DeleteObject` on `arn:aws:s3:::mctrader-market/l1/market/<channel>/*` (Option B per ADR-034 §결정 4 — blast radius 최소화)

### 2.2 가설 #2: keyspace drift (compactor 산출물 변경)

production compactor 가 더 이상 `l1/market/<channel>/` 에 객체를 생성하지 않음 (이미 평면 SSOT 로 cutover 완료된 상태일 수 있음).

**확인**:
```bash
# .compacted sentinel 객체 존재 여부
docker compose --profile migration run --rm \
  --entrypoint /bin/sh rekey-migration \
  -c 'aws --endpoint-url=$NAS_MINIO_ENDPOINT s3 ls s3://mctrader-market/l1/market/<channel>/ --recursive | grep ".compacted" | wc -l'
```

기대 출력:
- 0: cutover 이미 완료됨 (U5-VERIFY merge 후 가능 시나리오)
- ≥1: 마이그레이션 대상 존재함

**복구**:
- 0: 마이그레이션 자체가 불필요. EPIC #86 maintenance 단계 진입 (rekey.py + 3 preserved helpers + allowlist 정리)
- ≥1: 가설 #1 (IAM) 재확인 — discovery 가 객체 보지 못하는 IAM 이슈 가능성 높음

### 2.3 가설 #3: NAS endpoint 변경 (인프라 이동)

`NAS_MINIO_ENDPOINT` 환경 변수가 잘못된 endpoint 를 가리킴 (e.g. 인프라 마이그레이션 후 ConfigMap 미갱신).

**확인**:
```bash
docker compose --profile migration run --rm \
  --entrypoint /bin/sh rekey-migration \
  -c 'echo $NAS_MINIO_ENDPOINT && aws --endpoint-url=$NAS_MINIO_ENDPOINT s3 ls'
```

기대 출력:
- 정상: production endpoint + 버킷 목록 표시
- 비정상: endpoint mismatch / connection refused → ConfigMap/secret 갱신

### 2.4 가설 #4: --exchange / --channel 인자 오타

CLI 인자 typo 로 존재하지 않는 exchange/channel 조합 지시.

**확인**:
- mctrader-data CLAUDE.md `Collector channel allowlist 규약` 매트릭스 참조:
  - bithumb: orderbookdepth + orderbooksnapshot + transaction
  - upbit: orderbooksnapshot + transaction (orderbookdepth = BLOCKED)
- 4,608 객체는 production `upbit + orderbooksnapshot` 대표 (117GB)

---

## 3. INV-C carve-out 발화 (legitimate idempotent re-run, exit 0)

operator 가 마이그레이션 후 다시 `--execute` 를 실행한 경우:

```
INFO [rekey] already-migrated (manifest has 4608 done entries) — 0 candidates is expected for completed migration. exit 0
```

확인:
- Prometheus counter `mctrader_l1_rekey_skipped_already_migrated_total{exchange,channel}` += done_count (P2-NIT-1 시행 후, mctrader-data#171 LAND 시점부터)
- manifest 파일 `<root>/audit/rekey-l1-manifest-<exchange>-<channel>.yaml` 에 `status: done` entries 잔존

**조치**: 없음. 정상 동작. (참고: ADR-034 §결정 3 — dual-read 윈도우 + 30일 cool-down 종료 후 maintenance 회수 단계)

---

## 4. exit 코드 매트릭스 (참고)

| Exit | 원인 | 조치 |
|---|---|---|
| 0 | success (정상 완료 또는 INV-C carve-out idempotent re-run) | 없음 |
| 1 | insufficient disk space (O-R2) | `<root>` 파티션 ≥ 1GB 확보 |
| 2 | bucket versioning not Enabled (INV-E) **또는** concurrent pidfile lock (INV-I) | versioning 활성화 또는 pidfile 정리 후 재시도 |
| 3 | `--execute` 없이 `--i-understand-this-is-irreversible` 누락 (PL#9) | `--execute --i-understand-this-is-irreversible` 동시 지정 |
| **4** | **SILENT_ZERO_NO_CANDIDATES (M-10)** — `--execute` 시 0 candidates + manifest done 0 | **본 runbook §2 진단 시퀀스** |

---

## 5. P2-NIT-1 Prometheus counter (post-#171 LAND)

mctrader-data#171 LAND 후, INV-C carve-out (exit 0 정상 경로) 도 `_m_skipped.inc(done_count)` 호출 → `mctrader_l1_rekey_skipped_already_migrated_total` 이 정확히 `done_count` 만큼 증가. 이전 (pre-#171) 에는 결과 struct (`result.skipped_already_migrated`) 만 누적되어 Prometheus 메트릭이 under-report 되었음.

**Grafana 대시보드 영향**: `mctrader_l1_rekey_skipped_already_migrated_total` 차트가 정상 idempotent re-run 시점에 spike 표시 (이전: flat). 모니터링 alert rule 작성 시 본 변경 인지 의무.

---

## 6. 관련 문서

- ADR-034: NAS Object Key Unification (`mctrader-hub/docs/adr/ADR-034-nas-key-unification.md`)
- ADR-027 §D5: 4xx fail-fast (NAS PUT silent fallback 차단) + INCIDENT-2026-05-17 amendment
- mctrader-data CLAUDE.md `NAS l1/ re-key migration` 섹션
- U3-FIX §10 LAND ledger: https://github.com/mclayer/mctrader-data/issues/89#issuecomment-4474164733
- M-10 가드 코드: `src/mctrader_data/nas_migration/rekey.py` (`run()` 메서드, `partitions_total == 0` 분기)
