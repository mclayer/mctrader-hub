---
domain: data-health
created: 2026-05-14
story: MCT-164
related_adrs:
  - ADR-017 Amendment (compactor source 규약 + channel matrix SSOT)
  - ADR-027 Amendment (미지원 source silent-skip 차단)
status: confirmed  # MCT-164 Phase 2 진단 완료 (2026-05-14) — hypothesis → fact
---

# Exchange × Channel × Tier Matrix

mctrader-data 의 multi-exchange × multi-channel × multi-tier 매핑 SSOT. ADR-017 / ADR-027 amendment (MCT-164) 가 본 file 을 SSOT 로 인용.

## 확정 매트릭스 (2026-05-14 MCT-164 Phase 2 진단 결과 기반)

| Exchange | Collector Channel (WAL) | L1 Dataset | L2 Dataset | L3 Dataset | 상태 | Root Cause |
|---|---|---|---|---|---|---|
| bithumb | orderbookdepth | orderbookdepth | orderbooksnapshot | orderbooksnapshot | **정상** (MCT-162 LAND, MCT-165 V1 PASS) | N/A |
| bithumb | transaction | transaction | transaction | transaction | **정상** | N/A |
| upbit | orderbooksnapshot | orderbooksnapshot (WAL 있음) | — | — | **결함** (WAL 있음, L1 compaction 미실행) | **(c) channel_mismatch** — MCT-164 확정 |
| upbit | orderbookdepth | — | — | — | **결함** (WAL 없음 = collector 미생성) | **(c) channel_mismatch** — collector exchange=="bithumb" 조건 |
| upbit | transaction | transaction | transaction | transaction | **정상** (추정) | N/A |

### Root Cause 요약 (MCT-164 §10 인용)

**확정 원인: collector.py `_build_ingesters()` exchange == "bithumb" 조건**

```
collector.py:82
if self._include_orderbook and self._exchange == "bithumb":
    ingesters["orderbookdepth"] = WalIngester(channel="orderbookdepth", ...)
```

- MCT-162 (2026-05-13) bithumb orderbookdepth 활성화 시 upbit scope 미포함
- upbit = orderbooksnapshot WAL 만 생성
- L1 compactor 입력 없음 → upbit L1 = 0 → MCT-165 V2 잔존 YES

### WAL 복구 가능성 (MCT-164 §10 인용, D4=C)

- **verdict**: 부분가능
- orderbooksnapshot WAL → orderbooksnapshot L1 직접 compaction: 가능 (L1 기지원)
- MCT-166 에서 backfill 방향 결정

## 변환 의무 (ADR-017 Amendment 2)

- **Collector channel ≠ L1 dataset 시 compactor 변환 의무**
- upbit orderbooksnapshot WAL → orderbooksnapshot L1: L1 compactor `_ob_snapshot_dicts_to_arrow()` 기지원
- MCT-166 fix scope: collector 수정 또는 compactor orderbooksnapshot L1 활성화 결정 의무

## MCT-166 Fix Obligation (INV-5)

본 matrix 상태가 "결함" 인 행은 MCT-166 fix Story 의 fix scope 에 포함 의무.
MCT-166 brainstorm 진입 시 본 matrix §Root Cause 요약 인용 의무.

## 7-layer 다층성 cross-ref (MCT-165 박제)

본 matrix = data-health 7-layer 중 **multi-exchange parity** layer (MCT-165 MVP 4-layer 외 후속) 의 SSOT. 후속 ADR 진입 시 본 matrix 가 parity 검증의 기준.

## Cross-ref

- [ADR-017 Amendment 2026-05-14 (MCT-164)](../../../../adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md#amendment--compactor-source-규약-channel-matrix-ssot--multi-channel-exchange-지원-new-mct-164-2026-05-14) (compactor source 규약)
- [ADR-027 MCT-164 amendment](../../../../adr/ADR-027-cold-tier-object-storage-nas-minio.md) (미지원 source silent-skip 차단)
- [MCT-164 Story](../../../../stories/MCT-164.md) (본 matrix SSOT 발의 Story)
- [MCT-165 verify-d5](verify-d5-2026-05-14.md) §V2 (upbit L1 partition 0 trigger)
- [MCT-166 placeholder](../../../../stories/) (fix Story, 본 matrix 정합 fix 의무)
- [domain-knowledge README](README.md) (7-layer + multi-exchange parity layer 후속 ADR 영역 박제)
