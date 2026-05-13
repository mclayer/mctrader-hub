---
date: 2026-05-13
epic_key: EPIC-cold-tier-stage-3-wiring
parent_dependency: EPIC-cold-tier-nas-minio
status: Proposed
related_adrs:
  - ADR-027 (amend D4/D5/D9)
  - ADR-009 (§D2.1 reader fallback 활용 — amend 0)
  - ADR-017 (§D5 hot path 무영향 invariant 유지 — amend 0)
related_stories:
  - MCT-156 (compactor NAS wiring + L2/L3 DualWriter injection)
  - MCT-157 (Prometheus layout label 분리 + observability)
  - MCT-158 (Stage 3 release gate smoke test + cutover runbook + EPIC CLOSED)
---

# Stage 3 — Hot Pipeline NAS Wiring (cold tier L2/L3 DualWriter injection)

## 0. 동기 (Why)

ADR-027 "Stage 2 ALL DONE / EPIC CLOSED 2026-05-13 (#277)" 박제와 실태 사이 gap 사용자 실측 발견:

- bucket `mctrader-market` = 4.2 GiB / 1370 obj 만 존재
- **`tier=L3/` prefix 0개** — L3 객체 NAS 진입 경로 부재
- **`tier=L2/` 안 `hour=HH/` partition 0개** — 신규 L2Compactor 산출물 NAS 진입 경로 부재
- 실측 객체는 MCT-153 backfill 1회 산출물 only (`tier=L2/.../date=D/node=MERGED/` legacy ADR-009 §D2.1 layout, hour 부재)

## 1. 루트 원인 4종

1. `compose.yml` compactor service env 에 `NAS_MINIO_*` 부재 — `MINIO_ENDPOINT: http://minio:9000` (compose network 내부 dev MinIO 만)
2. `cli.py compact_cmd` 가 `CompactorRunner(Path(root))` 호출 시 `minio_uploader` 인자 미전달 → `self._minio = None` → L3 → MinIO upload 분기 dead code
3. `DualWriter` / `NASUploader` primitive (MCT-150/151 land) 가 hot pipeline `compactor/runner.py` 에 inject 안 됨
4. L3 backfill = MCT-153 §5.4 Non-goal 명시 박제 (run_backfill.py `help="본 Story = L2 only"`)

## 2. 확정된 7 결정점 (사용자 OK 2026-05-13)

| # | 결정 | 핵심 근거 |
|---|------|----------|
| **S1** | legacy L2 (~4.2GiB / 1370 obj, hour-key 부재) **재이관 0** | ADR-009 §D2.1 + §D14 reader fallback 박제 (`node=` absent → `node=DEFAULT` treated, `tier=` absent → `tier=L1` treated) |
| **S2** | DualWriter (MCT-151 primitive) 를 `compactor/runner.py._run_l2/l3` 에 inject | retry queue + sha256 + 7종 invariant harness 자동 활용 |
| **S3** | L1 제외, L2/L3 만 NAS upload | ADR-027 §D1 cold tier 정의 + §D5 hot path 무영향 invariant |
| **S4** | 신규 Epic 발의 (`EPIC-cold-tier-stage-3-wiring`) | Stage 2 EPIC CLOSED retro + scope_manifest milestone 보존 |
| **S5** | ADR-027 **D4/D5/D9 amendment**, D6 (RPO=0) amendment 불필요 | D6 = invariant, wiring 변경 무관 |
| **S6** | legacy retroactive 재구조 **비권고** | S1 정합 |
| **S7** | L3 backfill 별 Story **불필요** — hot pipeline wiring 완료 후 forward-only 자연 누적 | MCT-153 §5.4 Non-goal 자연 해소 |

## 3. 추가 risks (Codex GPT-5)

- **R1** (release gate 의무): bucket prefix layout 검증 부재 시 silent miswiring → **6h 후 `tier=L2/.../hour=HH/` + `tier=L3/.../node=MERGED/` 출현 검증** smoke test
- **R2** (observability): legacy/new layout 혼재 → Prometheus metric label 분리 (`legacy_node_default` vs `new_node_merged`)

## 4. 기존 자산 (재사용)

- `mctrader_data.nas_storage.nas_uploader.NASUploader` — MCT-150 land
- `mctrader_data.nas_storage.dual_writer.DualWriter` — MCT-151 land (status 3종: committed/local_only/hard_floor_blocked)
- `mctrader_data.nas_storage.retry_queue` — MCT-150 land
- `mctrader_data.nas_migration.invariant_harness.InvariantHarness` — MCT-151 land (7종 invariant)

## 5. Deprecation

- `mctrader_data.compactor.minio_uploader.MinioUploader` — MCT-149 이전 legacy uploader. MCT-156 에서 deprecation 마킹, 호출처 제거 후 후속 Epic 에서 삭제.

## 6. Epic 분해 (3 Story vertical slice)

### Story MCT-156 — compactor NAS wiring + L2/L3 DualWriter injection (entrypoint)

**Phase 1 (Architect)**:
- ADR-027 D4/D5/D9 amendment 본문 작성
- compose.yml env 전환 설계 (`MINIO_*` → `NAS_MINIO_*`, endpoint NAS 192.168.50.200)
- runner `_run_l2` 신규 + `_run_l3_for_parquet` DualWriter 교체 Change Plan

**Phase 2 (Developer + QA)**:
- compose env 전환
- cli.compact_cmd 에 NASUploader/DualWriter lazy build inject
- runner `_run_l2` 신규 (L2 compaction 후 DualWriter put)
- `_run_l3_for_parquet` 의 MinioUploader → DualWriter 교체
- MinioUploader deprecation 마킹
- unit + integration test (DualWriter status 3종 + retry queue + 7종 invariant harness wiring)

### Story MCT-157 — Prometheus layout label 분리 + observability (병렬 가능)

**Phase 1 (Architect)**:
- `nas_metrics/prometheus_exporters.py` label schema 설계 (`legacy_node_default` vs `new_node_merged`)
- Grafana dashboard PromQL 갱신 plan

**Phase 2 (Developer + QA)**:
- exporter label 추가
- 기존 metric backward compat 검증 (metric name 불변)
- dashboard PromQL 갱신
- unit test (label cardinality + legacy/new 구분)

### Story MCT-158 — Stage 3 release gate smoke test + cutover runbook + EPIC CLOSED gate

**Phase 1 (Architect)**:
- 6h smoke test 절차 (R1)
- cutover runbook 5 Phase + rollback plan

**Phase 2 (Developer + QA)**:
- `scripts/stage3_smoke.sh` (또는 pytest integration test)
- `docs/runbooks/stage3-cutover.md` 신규
- `docs/runbooks/stage3-smoke-test.md` 신규
- 6h dry-run evidence pack
- EPIC CLOSED gate (3 PR MERGED + R1 PASS + ADR amendment LAND + EPIC-RESULTS doc + PMOAgent retro)

## 7. Story sequence

| Phase | Story | 판정 |
|-------|-------|------|
| 1 | MCT-156 | 순차 (vertical slice 진입점) |
| 2 | MCT-157 | MCT-156 land 후 병렬 가능 (단독 파일 disjoint) |
| 3 | MCT-158 | MCT-156 + MCT-157 land 후 순차 (통합 검증 + EPIC CLOSED gate) |

## 8. Test Contract 할당

### MCT-156
- DualWriter status 3종 (committed / local_only / hard_floor_blocked) compactor wiring
- retry queue replay on NAS unavailable
- 7종 invariant harness wiring (L2 + L3)
- compose env switch (MINIO_* → NAS_MINIO_*) smoke

### MCT-157
- Prometheus label cardinality (legacy_node_default vs new_node_merged)
- backward compat (기존 metric name 불변)

### MCT-158
- **R1 release gate** — 6h smoke test (bucket prefix `tier=L2/.../hour=HH/` + `tier=L3/.../node=MERGED/` 출현)
- cutover runbook 5 Phase dry-run
- rollback plan verify

## 9. Out of scope (명시적 비범위)

- legacy L2 객체 재구조 / 재이관 (S1+S6 결정)
- L1 NAS upload (S3 결정, ADR-017 hot path 무영향 invariant 유지)
- 별 L3 backfill Story (S7 결정, forward-only 자연 누적)
- MinioUploader 삭제 (MCT-156 에서 deprecation 마킹만, 삭제는 후속 Epic)

## 10. scope_manifest 초안 (Phase 1 PR Issue body 첨부용)

```yaml
epic_key: EPIC-cold-tier-stage-3-wiring
epic_title: "Stage 3 — hot pipeline NAS wiring (compactor L2/L3 DualWriter injection)"
parent_dependency: EPIC-cold-tier-nas-minio  # post-closure follow-up
status: Proposed
created: 2026-05-13

planned_adrs:
  amendments:
    - adr: ADR-027-cold-tier-object-storage-nas-minio
      sections: [D4, D5, D9]
      owner_story: MCT-156
      rationale: |
        D4 (cold tier wiring) — compactor L2/L3 DualWriter injection 명문화
        D5 (L1 제외 invariant) — hot path 무영향 보장
        D9 (legacy retroactive 비권고) — S1 결정 박제
  new_proposals: []

planned_files:
  mctrader-data:
    modified:
      - compose.yml
      - src/mctrader_data/cli.py
      - src/mctrader_data/compactor/runner.py
      - src/mctrader_data/compactor/minio_uploader.py  # deprecation 마킹
      - src/mctrader_data/nas_metrics/prometheus_exporters.py
    new:
      - tests/integration/test_compactor_nas_wiring.py
      - tests/integration/test_prometheus_layout_label.py
      - scripts/stage3_smoke.sh
  mctrader-hub:
    modified:
      - docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md
    new:
      - docs/runbooks/stage3-cutover.md
      - docs/runbooks/stage3-smoke-test.md

planned_claude_md_sections:
  mctrader-hub:
    - "Stage 3 wiring Epic state (post-MCT-155 follow-up)"
    - "Stage 3 release gate (R1 smoke test 의무)"
  mctrader-data:
    - "compactor NAS wiring (MINIO_* → NAS_MINIO_* env 전환)"
    - "DualWriter injection (compactor/runner.py L2/L3)"
    - "Prometheus layout label (legacy_node_default vs new_node_merged)"

design_decisions:
  S1: { decision: "legacy L2 재이관 0", rationale: "ADR-009 §D2.1+§D14 reader fallback", owner_story: MCT-156 }
  S2: { decision: "DualWriter inject", rationale: "MCT-151 primitive 재사용", owner_story: MCT-156 }
  S3: { decision: "L1 제외", rationale: "ADR-027 §D1/§D5", owner_story: MCT-156 }
  S4: { decision: "신규 Epic", rationale: "Stage 2 EPIC CLOSED retro 보존", owner_story: epic-level }
  S5: { decision: "ADR-027 D4/D5/D9 amend, D6 불변", rationale: "D6 invariant", owner_story: MCT-156 }
  S6: { decision: "legacy retroactive 재구조 비권고", rationale: "S1 정합", owner_story: MCT-156 }
  S7: { decision: "L3 backfill 별 Story 불필요", rationale: "forward-only 자연 누적", owner_story: MCT-156 }

risks:
  R1:
    risk: "bucket prefix layout 검증 부재 시 silent miswiring"
    mitigation: "6h 후 tier=L2/.../hour=HH/ + tier=L3/.../node=MERGED/ 출현 smoke"
    owner_story: MCT-158
    gate_type: release_gate_mandatory
  R2:
    risk: "Prometheus metric legacy/new layout 혼재 시 observability 혼동"
    mitigation: "label 분리 (legacy_node_default vs new_node_merged)"
    owner_story: MCT-157

dependency:
  blocks: []
  blocked_by:
    - EPIC-cold-tier-nas-minio  # Stage 2 CLOSED 2026-05-13 (#277)
  reuses:
    - mctrader_data.nas_storage.nas_uploader.NASUploader  # MCT-150
    - mctrader_data.nas_storage.dual_writer.DualWriter  # MCT-151
    - mctrader_data.nas_storage.retry_queue  # MCT-150
    - mctrader_data.nas_migration.invariant_harness.InvariantHarness  # MCT-151
  deprecates:
    - mctrader_data.compactor.minio_uploader.MinioUploader  # MCT-149 이전

story_sequence:
  - { story: MCT-156, mode: sequential, reason: "vertical slice entrypoint" }
  - { story: MCT-157, mode: parallel_after_156, reason: "prometheus_exporters.py 단독" }
  - { story: MCT-158, mode: sequential_after_156_157, reason: "통합 검증 + EPIC CLOSED gate" }

epic_close_gate:
  - MCT-156 PR MERGED
  - MCT-157 PR MERGED
  - MCT-158 PR MERGED + R1 smoke test 6h PASS evidence pack
  - ADR-027 D4/D5/D9 amendment LAND
  - EPIC-RESULTS doc LAND
  - PMOAgent retro dispatch
```

## 11. 합성 trail

- **Phase 0 4-agent burst** (2026-05-13): DomainAgent (domain-knowledge cold tier 부재 surface) + ResearcherAgent (3 핵심 개념 + 2 unknown unknowns) + RequirementsAnalystAgent (WHY 추출: ADR 박제↔실태 gap, "구조 복구" 명시 vs reader fallback 실제 필요 불일치 가능성) + PMOAgent (4 Story 예비 → 3 Story vertical slice 묶음 권고, 신규 Epic 권고)
- **Codex GPT-5 review** (2026-05-13): 7 결정점 일괄 dispatch, 응답 (D1=A, D2=B, D3=A, D4=A, D5=D4/D5/D9 amend, D6=재구조 비권고, D7=B) + 2 추가 risk (R1 release gate, R2 metric label)
- **Sonnet 합성** (2026-05-13): 사용자 원문 vs 권고 불일치 3건 surface ("구조 복구" → 재이관 0 / "L3 backfill 별 Story" → 불필요 / "L1/L2/L3 다" → L1 제외) + 사용자 final OK
- **PMOAgent 2nd pass** (2026-05-13): 확정 설계 분해 → 3 Story (MCT-156/157/158) + scope_manifest 초안 + R1 release gate 할당
