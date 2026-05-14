---
domain: data-health
created: 2026-05-14
story: MCT-164
related_adrs:
  - ADR-017 Amendment (compactor source 규약 + channel matrix SSOT)
  - ADR-027 Amendment (미지원 source silent-skip 차단)
status: hypothesis  # MCT-164 Phase 2 진단 결과 후 fact 로 update
---

# Exchange × Channel × Tier Matrix

mctrader-data 의 multi-exchange × multi-channel × multi-tier 매핑 SSOT. ADR-017 / ADR-027 amendment (MCT-164) 가 본 file 을 SSOT 로 인용.

## 추정 매트릭스 (2026-05-14 진단 전 hypothesis)

| Exchange | Collector Channel (WAL) | L1 Dataset | L2 Dataset | L3 Dataset | 상태 |
|---|---|---|---|---|---|
| bithumb | orderbookdepth | orderbookdepth | orderbooksnapshot | orderbooksnapshot | MCT-162 LAND 후 정상 (MCT-165 V1 PASS) |
| bithumb | transaction | transaction | transaction | transaction | 정상 |
| upbit | orderbooksnapshot | (미지원 ← MCT-164 진단 대상) | (미지원) | (미지원) | **MCT-164 root cause 영역** (MCT-165 V2 잔존 YES) |
| upbit | transaction | transaction | transaction | transaction | 추정 정상 (별 진단 필요, MCT-164 scope) |

## 변환 의무 (ADR-017 Amendment)

- **Collector channel ≠ L1 dataset 시 compactor 변환 의무**
- 예: upbit orderbooksnapshot WAL → L1 orderbookdepth 변환 가능성 = MCT-164 AC-5 D4=C 검증 대상 (`scripts/wal_recovery_probe.py`)

## 진단 후 update 의무

본 표는 hypothesis. MCT-164 Phase 2 진단 결과 (`docs/stories/MCT-164.md` §10) 박제 후 본 file 본문 갱신 의무 (Phase 2 PR 에서 update):
- "미지원" → 실제 root cause 확정 영역 ("collector channel mismatch" / "compactor source 처리 미구현" / "ingester partition key mismatch" / "discovery skip" 중 하나)
- 변환 가능성 = "가능 (WAL 복구)" / "불가 (forward-only acceptable)" 확정
- MCT-166 fix Story 의 scope 박제 cross-ref

## 7-layer 다층성 cross-ref (MCT-165 박제)

본 matrix = data-health 7-layer 중 **multi-exchange parity** layer (MCT-165 MVP 4-layer 외 후속) 의 SSOT. 후속 ADR 진입 시 본 matrix 가 parity 검증의 기준.

## Cross-ref

- [ADR-017 Amendment 2026-05-14 (MCT-164)](../../../../adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md#amendment--compactor-source-규약-channel-matrix-ssot--multi-channel-exchange-지원-new-mct-164-2026-05-14) (compactor source 규약)
- [ADR-027 MCT-164 amendment](../../../../adr/ADR-027-cold-tier-object-storage-nas-minio.md) (미지원 source silent-skip 차단)
- [MCT-164 Story](../../../../stories/MCT-164.md) (본 matrix SSOT 발의 Story)
- [MCT-165 verify-d5](verify-d5-2026-05-14.md) §V2 (upbit L1 partition 0 trigger)
- [MCT-166 placeholder](../../../../stories/) (fix Story, 본 matrix 정합 fix 의무)
- [domain-knowledge README](README.md) (7-layer + multi-exchange parity layer 후속 ADR 영역 박제)
