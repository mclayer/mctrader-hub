---
story_key: MCT-171
title: "DR runbook 본문 + invariant 8종 확장 + 4 layer capacity 제한 정책"
epic: EPIC-tier-promotion-single-source
phase_in_epic: 5
mode: parallel_with_170  # MCT-170 이미 LAND, 실질 sequential entry
repos: [mctrader-hub, mctrader-data]
phase_pair: phase1_phase2
status: brainstorm_complete_spec_authored
created_at: 2026-05-14
brainstorm_phase0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
codex_review: 2026-05-14 (9 결정점 단일 패스 합성)
pmo_2nd_pass: 2026-05-14 (단일 Story 확정 + 3 PR split)
pre_lookup_evidence:
  - "verified-via: Read docs/runbooks/nas-bucket-disaster-recovery.md (341 lines, line 275-328 anchor)"
  - "verified-via: Read mctrader-data/src/mctrader_data/nas_migration/invariant_harness.py (7종 SSOT + 8 fail variant)"
  - "verified-via: Glob mctrader-data/src/mctrader_data/collector.py (단일 468 lines)"
  - "verified-via: Bash ls mctrader-data/src/mctrader_data/wal/ (ingester / ndjson_codec / replay / segment)"
  - "verified-via: Grep ambiguity|UNKNOWN_TIER → compactor/promotion.py 단독 박제"
  - "verified-via: Bash df -h c:/ (476G total / 199G avail / 59% used)"
  - "verified-via: Read .codeforge/counters.json (MCT-174 reservation active, D6 cross-NAS owner)"
  - "verified-via: Read scope_manifests/EPIC-tier-promotion-single-source.yaml (story_sequence MCT-171 Reserved, milestone 4/6)"
---

# MCT-171 brainstorm spec — DR runbook 본문 + invariant 8종 확장 + 4 layer capacity 제한 정책

## §1 Brainstorm 배경

EPIC-tier-promotion-single-source Story-5. MCT-167 governance singleton publish 시 DR runbook **stub** 만 박제 (line 275-328, 3 section placeholder), 본 Story = stub → 운영 가능 runbook 격상 + invariant 8종 enforcement impl + 4 layer capacity probe + collector ingest block.

사용자 directive (ADR-029 박제분):
- D4=B WAL sealed local only (사용자 directive, RPO=0 D1 단독 의존)
- D5=A_modified capacity-bounded ingest block
- D6=B bucket versioning ✓ + cross-NAS replication (MCT-174 defer)
- D11 4 layer capacity (WAL 30G / L1 20G / NAS 500G target / Host 200G hard)

## §2 Phase 0 verify finding (8건)

§Story-MCT-171.md §1.2 박제분 동치. session prompt 가설 vs 실 코드 verify 결과:

1. ✅ DR runbook stub 341 lines, line 275-328 = 본 Story author 영역
2. ⚠️ InvariantHarness 실 위치 = `nas_migration/` (prompt 의 `nas_storage/` 정정)
3. ⚠️ collector = `collector.py` 단일 468 lines (prompt 의 `collector/dir` 정정)
4. ✅ WAL = `wal/` dir
5. ⚠️ Ambiguity invariant 분산 (`compactor/promotion.py` 단독, InvariantHarness 외부)
6. ❌ Production data dir 부재 (host-local), WAL/L1 baseline = runtime probe 의무
7. ✅ Host disk 476G / 199G avail
8. ✅ MCT-174 active (D6 cross-NAS defer)

## §3 Phase 0 4-agent burst 합성

§Story-MCT-171.md §2 박제분 동치.

- **Domain** 핵심 사실 5 (Hot path 무영향 / NAS retry_queue / Cold path INV-4 / Forward-only / sha256 SSOT)
- **Researcher** 핵심 개념 3 (Backpressure propagation / Invariant ordering & short-circuit / Capacity watermark hysteresis) + Unknown unknowns 2 (WAL 30G 산정 / InvariantHarness 통합 backward compat)
- **Analyst** 5 AC + Edge case 2 (NAS 장애 + WAL hard limit / clock drift mismatch)
- **PMO** 단일 Story 확정, 의존 epic 0, R2 HIGH = D6 cross-NAS MCT-174 defer

## §4 Codex review 9 결정점 합성

§Story-MCT-171.md §3 박제분 동치. 9 design point 채택 (D7-1=A / D7-2=A / D7-3=B / D7-4=C / D7-5=B / D7-6 cardinality 제한 / D7-7 priority 유지 + disk full mode2 / D7-8=C 80/95 hysteresis / D7-9 A+C bridge).

## §5 설계 결정

### 5.1 InvariantHarness 8종 통합 (D7-1=A)

**File**: `mctrader-data/src/mctrader_data/nas_migration/invariant_harness.py`

확장 항목:
- `_INVARIANT_NAMES` tuple: 7개 → 8개 (`"ambiguity"` 추가, 위치 = 마지막)
- `InvariantResult.status` enum: 8 variant → 9 variant (`"ambiguity_fail"` 추가)
- `ADR009_EXPECTED_*` 상수 SSOT 보존 (변경 0)
- `ADR009_CHANNEL_SCHEMA_MATRIX` SSOT 보존 (변경 0)
- 신규 method `_check_ambiguity(self, local_partition, nas_partition) -> PerInvariantResult`:
  - logic = compactor/promotion.py `verify_no_ambiguity` (MCT-169 LAND) 흡수
  - 동일 logical entity (schema_version × tier × exchange × symbol × date × hour × node) NAS + local XOR violation
  - 위반 시 mismatch_files 박제 + Prometheus `mctrader_invariant_violation_total{invariant_name=ambiguity}` Counter

`compactor/promotion.py` 측 `verify_no_ambiguity` 함수 = deprecate (caller 측 InvariantHarness 호출 변경 의무, MCT-169 D10 test 회귀 0 verify).

### 5.2 capacity_probe.py 신규 (D7-2=A + D7-4=C)

**File**: `mctrader-data/src/mctrader_data/capacity_probe.py` (collector.py sibling, 의존 0)

```python
class CapacityProbe:
    """4 layer capacity hybrid probe — 5min audit sample + threshold approach continuous.

    Layer: WAL_local / L1_local / NAS_bucket / Host_disk
    Threshold: warn 80% / critical 95% / hard limit 100%
    """
    def __init__(
        self,
        wal_root: Path,        # mctrader-data/data/wal/
        l1_root: Path,         # mctrader-data/data/l1/
        nas_uploader: NASUploader,  # NAS bucket size probe
        host_mount: Path,      # mctrader 할당 mount (LVM volume or fallback to host disk)
        thresholds: CapacityThresholds,  # SSOT 상수 (D11 ADR-029 정합)
        metrics: PrometheusExporter,
    ) -> None: ...

    def probe_once(self) -> CapacityReport:
        """4 layer probe 1회 실행 — Gauge emit."""
        ...

    def probe_loop(self) -> None:
        """hybrid loop: 5min default + 임의 layer >= 80% 근접 시 15s continuous 전이."""
        ...
```

상수 SSOT (ADR-029 D11 박제분):
```python
@dataclass(frozen=True)
class CapacityThresholds:
    wal_local_hard_gib: int = 30  # ADR-029 D11
    l1_local_hard_gib: int = 20   # ADR-029 D11
    nas_bucket_target_gib: int = 500  # ADR-029 D11
    nas_bucket_hard_gib: int = 1024   # ADR-029 D11
    host_disk_hard_gib: int = 200     # ADR-029 D11
    warn_ratio: float = 0.80
    critical_ratio: float = 0.95
```

### 5.3 ingest_blocker.py 신규 (D7-5=B + D7-8=C)

**File**: `mctrader-data/src/mctrader_data/ingest_blocker.py`

```python
class IngestBlocker:
    """Graceful drain ingest blocker — D5=A_modified + D7-8=C 80%/95% hysteresis.

    State machine:
        NORMAL → WARN_DRAIN (80% trigger) → BLOCKED (95% trigger) → NORMAL (75% unblock, 5% gap)
    """
    def __init__(
        self,
        probe: CapacityProbe,
        metrics: PrometheusExporter,
        hysteresis_gap: float = 0.05,  # 95% block → 90% unblock (block 75% candidate)
    ) -> None: ...

    def should_block(self, report: CapacityReport) -> bool:
        """현재 4 layer state 기준 block 결정."""
        ...

    def on_capacity_warn(self, layer: str, ratio: float) -> None:
        """80% threshold — aggressive L1 rotate trigger (compactor signal)."""
        ...

    def on_capacity_critical(self, layer: str, ratio: float) -> None:
        """95% threshold — graceful drain 후 ingest reject."""
        ...
```

collector.py 측 hook: 신규 ingest 시작 직전 `IngestBlocker.should_block()` 호출, True 시 reject + Counter emit. **collector.py 코드 변경 최소화** (hook 1 callsite + import 1 line, 기존 hot path 영향 0).

### 5.4 Prometheus exporters 확장 (D7-6)

**File**: `mctrader-data/src/mctrader_data/nas_metrics/prometheus_exporters.py`

신규 4 metric:
```python
mctrader_capacity_usage_bytes = Gauge(
    'mctrader_capacity_usage_bytes',
    '4 layer capacity usage (bytes)',
    ['layer'],  # 4 enum: WAL_local / L1_local / NAS_bucket / Host_disk
)

mctrader_capacity_threshold_ratio = Gauge(
    'mctrader_capacity_threshold_ratio',
    '4 layer threshold ratio (0.0-1.0)',
    ['layer'],
)

mctrader_invariant_violation_total = Counter(
    'mctrader_invariant_violation_total',
    'Invariant violation count by name',
    ['invariant_name'],  # 8 enum: sha256/object_count/row_count/column_count/column_order/dtype/schema_version/ambiguity
)

mctrader_invariant_check_latency_ms = Histogram(
    'mctrader_invariant_check_latency_ms',
    'Invariant check latency (ms)',
    buckets=[1, 5, 10, 50, 100, 500, 1000, 5000, 30000],
)

mctrader_ingest_blocked_total = Counter(
    'mctrader_ingest_blocked_total',
    'Ingest block count by reason',
    ['reason'],  # 3 enum: wal_full / l1_full / nas_unreachable
)
```

Cardinality 제한 = label hardcoded enum + free-form label 검출 시 fail-fast (assertion or validation decorator).

### 5.5 DR runbook 본문 확장 (D7-7)

**File**: `docs/runbooks/nas-bucket-disaster-recovery.md` (line 275-328 anchor)

추가 본문 (line 328 뒤):
1. **Quick triage flowchart** (runbook 시작 page 후 첫 page) — 5 fail mode 분기
2. **5 fail mode step-by-step** (검출 / 진단 / 복구 / verify / postmortem)
3. **invariant 8종 본문** (각 invariant 별 violation 시 escalate)
4. **4 layer capacity step-by-step** (WAL/L1/NAS/Host 별 measure + action)
5. **Slack notification template** (fail mode 별 첨부 format)

Priority (D7-7 채택): **(2) NAS unreachable > (1) L1 NAS PUT fail > (4) Rate-limit > (3) Clock drift > (5) Replication failover**. Codex 보완:
- disk full → mode (2) 하위 명시
- mode (3) clock drift 설명에 "ambiguity invariant 트리거 가능" 명시

## §6 ADR amendment 의무

**신규 ADR 0**. ADR-029 amendment only:

- ADR-029 §D4 verify status entry: WAL local only 정합 박제 (Phase 2 PR2)
- ADR-029 §D5 verify status entry: A_modified graceful drain 채택 (D7-5=B) 박제
- ADR-029 §D11 verify status entry: 80%/95% hysteresis 채택 (D7-8=C) 박제

Phase 2 PR2 timing 박제 (RETRO 동행).

## §7 scope_manifest 초안

§Story-MCT-171.md §6 박제분 동치. PMO 2nd pass 산출분 100% 채택.

## §8 PR 분리

§Story-MCT-171.md §8 박제분 동치. 3 PR cross-repo sequential (Phase 1 hub docs → Phase 2 PR1 data code → Phase 2 PR2 hub 박제).

## §9 verified-via 박제 (frontmatter pre_lookup_evidence)

ADR-073 §결정 1 + §결정 6 mandate. spec 헤더 박제분.

## §10 plan link

`docs/superpowers/plans/2026-05-14-mct-171-dr-runbook-capacity.md` 참조.
