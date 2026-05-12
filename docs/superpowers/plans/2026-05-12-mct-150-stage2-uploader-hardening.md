# MCT-150 Stage 2 Uploader Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap EPIC-cold-tier-nas-minio Stage 2 (scope_manifest 갱신 + 6 placeholder Issues) + MCT-150 Phase 1+2 PR 완료 (uploader hardening + retry queue + Prometheus baseline + conditional write smoke + IP-allowlist 재확인) — 76GB cold L2 NAS 이관의 첫 정공법 단계.

**Architecture:** codeforge consumer 패턴 (RequirementsPL → ArchitectPL → DeveloperPL → CodeReviewPL → TestAgent → SecurityTestPL). MCT-150 은 mctrader-data primary, Phase 1 = Story file + Issue, Phase 2 = uploader/retry_queue/metrics impl + TDD. ADR-027 amendment 4건 후보 박제 (필수 2 / optional 2).

**Tech Stack:** Python (mctrader-data), boto3 (S3 client), Prometheus client, pytest, GitHub Actions CI, codeforge plugin (5.23.0).

---

## Pre-flight 확인

- [ ] **Step 0.1: 디렉토리 + git 상태 확인**

```bash
pwd  # c:\workspace\mclayer\mctrader-hub
git status  # main, .tmp/ untracked만 OK
git log -5 --oneline  # 2a93d2a docs codeforge upgrade 반영이 HEAD
```

- [ ] **Step 0.2: Stage 1 MERGED 상태 확인**

```bash
gh issue view 244 --repo mclayer/mctrader-hub --json state  # MCT-147 = closed
gh issue view 248 --repo mclayer/mctrader-hub --json state  # MCT-148 retro
gh issue view 250 --repo mclayer/mctrader-hub --json state  # MCT-149 closed
gh api repos/mclayer/mctrader-hub/milestones/4 --jq '{number, title, state}'  # Stage 2 milestone open
```

Expected: 3건 모두 closed, milestone #4 "Epic-cold-tier-stage-2-migration" open.

---

## Task 1: scope_manifest Stage 2 overhaul (12 결정 박제)

**Files:**
- Modify: `scope_manifests/EPIC-cold-tier-nas-minio.yaml:101-138, 152-214, 233-271`

기존 scope_manifest 의 MCT-152~155 분해 가 ADR-027 D4 cutover sequence 와 misaligned. Phase 2 PMO 2nd pass 출력으로 overhaul.

- [ ] **Step 1.1: 기존 planned_stories Stage 2 entries 교체**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml:101-138` (MCT-150 ~ MCT-155 entries) 를 다음으로 교체:

```yaml
  - key: MCT-150
    title: "uploader hardening + retry queue + Prometheus baseline + conditional write smoke + IP-allowlist 재확인"
    repo: mctrader-data
    phase_pair: phase1_phase2
    depends_on: []
    parallel_with: [MCT-151]
    stage: 2
    sp: 5
    addresses_decisions: [S4, S10, S11, S12]
  - key: MCT-151
    title: "dual-write atomic primitives + 7종 invariant harness + L1 compaction drain barrier"
    repo: mctrader-data
    phase_pair: phase1_phase2
    depends_on: [MCT-150]
    parallel_with: [MCT-150]
    stage: 2
    sp: 8
    addresses_decisions: [S2, S5, S8]
  - key: MCT-152
    title: "dual-write window 운영 (2-4주 drift + IOPS during + NAS unreachable SOP 실전)"
    repo: mctrader-data
    phase_pair: phase1_phase2
    depends_on: [MCT-151]
    parallel_with: [MCT-153]
    stage: 2
    sp: 5
    addresses_decisions: [S2, S10, S11]
  - key: MCT-153
    title: "backfill 76GB closed-day per-(symbol, day) tuple chunking, 10-symbol 병렬, node=DEFAULT"
    repo: mctrader-data
    phase_pair: phase1_phase2
    depends_on: [MCT-151]
    parallel_with: [MCT-152]
    stage: 2
    sp: 8
    addresses_decisions: [S1, S5, S6, S7]
  - key: MCT-154
    title: "reader endpoint cutover (cache flush + verify) + dual-write 7d 연장 + engine smoke"
    repo: mctrader-engine + mctrader-hub
    phase_pair: phase1_phase2
    depends_on: [MCT-152, MCT-153]
    parallel_with: []
    stage: 2
    sp: 5
    addresses_decisions: [S3, S6, S9]
  - key: MCT-155
    title: "local GC + secret rotation 첫 cycle + TLS 재검토 user confirm + RPO=0 검증 회고"
    repo: mctrader-data + mctrader-hub
    phase_pair: phase1_phase2
    depends_on: [MCT-154]
    parallel_with: []
    stage: 2
    sp: 5
    addresses_decisions: [S8, S9, S12]
```

- [ ] **Step 1.2: design_decisions 에 S1~S12 추가 (D1~D11 다음)**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml` 의 `design_decisions` 리스트 (D11 다음 line 80) 에 12 결정 append:

```yaml
  # Stage 2 신규 결정 (12점) — Codex GPT-5 review + Sonnet decider + 사용자 confirm (S8/S12)
  - id: S1
    title: "Backfill partition close 기준"
    decision: "Collector flush barrier signal + closed-day scope (UTC midnight 이전 = backfill only, 당일 partition = dual-write 자연 수렴)"
    rationale: "라이브 append/backfill race 를 invariant 검증 전에 직접 차단"
    addressed_in: MCT-153
  - id: S2
    title: "L1 compaction quiesce 메커니즘"
    decision: "drain + barrier 필수 (dual-write toggle gate)"
    rationale: "toggle 이전 compaction output 이 local-only land 방지 — silent row loss 차단"
    addressed_in: [MCT-151, MCT-152]
  - id: S3
    title: "Reader cache invalidation barrier"
    decision: "explicit cache flush + verify before endpoint flip"
    rationale: "D4 reader cutover gate 와 가장 단순하게 부합. stale list/object cache → 404 spike 가 데이터 유실처럼 보이는 risk 차단"
    addressed_in: MCT-154
  - id: S4
    title: "PUT-If-None-Match / conditional write 지원"
    decision: "HEAD-then-PUT fallback + MCT-150 에서 MinIO conditional write smoke test 선행"
    rationale: "RELEASE.2025-04-08 정확한 동작은 smoke-test 선행 필요. 결정론적 D1 object key 동시 overwrite risk 차단"
    addressed_in: MCT-150
  - id: S5
    title: "Schema invariant 확장 (D6 보강)"
    decision: "D6 박제 3종 + column count + column name order + dtype identity + schema_version pin = 7종 invariant"
    rationale: "D6 PASS 이나 Parquet schema 차이로 read 파괴/오염 risk 차단 (reader-breaking drift 포착)"
    addressed_in: [MCT-151, MCT-153]
    triggers_adr_amendment:
      adr: ADR-027
      section: D6
      mandatory: true
  - id: S6
    title: "Legacy node= 부재 partition backfill 시 NAS PUT path"
    decision: "NAS PUT 시 node=DEFAULT 명시 기재"
    rationale: "ADR-009 §D2.1 read mapping (DEFAULT 의미론) 정합. 부재 보존 시 두 가지 물리 레이아웃 → cutover legacy partition 누락 risk 차단"
    addressed_in: [MCT-153, MCT-154]
  - id: S7
    title: "Backfill chunking 단위"
    decision: "Per-(symbol, day) tuple, 10-symbol 병렬. 76GB ~7분 추정 (50MB×1520 PUT × p99 2871ms ÷ 10)"
    rationale: "Invariant 범위 이하 분절 없이 최적 재개성 + 병렬성. 너무 거친 a/c 거부, 과분절 b 거부"
    addressed_in: MCT-153
  - id: S8
    title: "RPO 강도 해석 (사용자 \"절대 유실 금지\")"
    decision: "RPO=0 at cutover (cutover-1s 검증 L2 segment 모두 cutover+1s NAS 존재 의무)"
    rationale: "사용자 directive verbatim 정합 + ADR-027 D6 ALL-PASS invariant gate 정합. chunk-boundary loss 허용 (b) / session resync (c) 거부"
    addressed_in: [MCT-151, MCT-155]
    user_confirmed: true
    user_confirmed_at: 2026-05-12
  - id: S9
    title: "Cutover failure rollback 정책"
    decision: "Cutover 후 dual-write 7d 연장 (grace overlap, belt-and-suspenders)"
    rationale: "7d grace 동안 NAS 검증 유지 → 롤백 비용 최소화. NAS-only write window 발생 시 reverse sync 비용 차단"
    addressed_in: [MCT-154, MCT-155]
    triggers_adr_amendment:
      adr: ADR-027
      section: D4
      mandatory: false
  - id: S10
    title: "NAS unreachable 운영 SOP"
    decision: "Auto-resume + Prometheus alert (1000 segments OR 10GB backlog threshold) + ADR-017 archive failure 7d grace tie-in. >24h 지속 unreachable 시만 user manual gate"
    rationale: "D5 retry queue 구체화. WAL+L1 unaffected 유지 (hot path invariant). user-confirm recovery 는 일상적 transient 복구 지연 risk → 거부"
    addressed_in: [MCT-150, MCT-152]
    triggers_adr_amendment:
      adr: ADR-027
      section: D5
      mandatory: false
  - id: S11
    title: "dual-write disk I/O 정량 측정 baseline"
    decision: "Prometheus node_exporter + container metrics, MCT-150 pre + MCT-152 during"
    rationale: "비교 가능한 baseline + 활성화 delta 확보. iostat 단독은 story gate 로 취약"
    addressed_in: [MCT-150, MCT-152]
  - id: S12
    title: "Stage 2 TLS 재검토 timing (D2 escalation 의무)"
    decision: "HTTP 유지 (Stage 1 정책 연장) — Stage 2 cutover 후 MCT-155 재검토"
    rationale: "사용자 confirm — Stage 1 4중 mitigation (LAN-only + .env 0600 + 90d rotation + IP-allowlist firewall) 유지. cutover 중 TLS 활성화 = endpoint URL 변경 + dual-write invariant 재검증 강제 (disruptive)"
    addressed_in: [MCT-150, MCT-155]
    user_confirmed: true
    user_confirmed_at: 2026-05-12
    triggers_adr_amendment:
      adr: ADR-027
      section: D9
      mandatory: true
      trigger_story: MCT-155
```

- [ ] **Step 1.3: planned_files MCT-150~155 entries 갱신**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml:172-214` (planned_files MCT-150~155) 를 다음 신규 file list 로 교체:

```yaml
  MCT-150:
    mctrader-data:
      - "src/mctrader_data/storage/nas_uploader.py"
      - "src/mctrader_data/storage/retry_queue.py"
      - "src/mctrader_data/metrics/prometheus_exporters.py"
      - "src/mctrader_data/ops/nas_unreachable_sop.py"
      - "tests/storage/test_nas_uploader.py"
      - "tests/storage/test_retry_queue.py"
      - "tests/storage/test_conditional_write_smoke.py"
      - "tests/metrics/test_prometheus_exporters.py"
      - "configs/prometheus/nas_uploader_rules.yml"
      # FIX#1 F4 (2026-05-13): docs/stories/MCT-150.md 제거 — mctrader-hub block 에만 박제 (hub SSOT)
    mctrader-hub:
      - "docs/stories/MCT-150.md"  # cross-repo Story header (hub SSOT)
  MCT-151:
    mctrader-data:
      - "src/mctrader_data/storage/dual_writer.py"
      - "src/mctrader_data/storage/compaction_barrier.py"
      - "src/mctrader_data/migration/invariant_harness.py"
      - "tests/storage/test_dual_writer.py"
      - "tests/storage/test_compaction_barrier.py"
      - "tests/migration/test_invariant_harness.py"
      - "docs/stories/MCT-151.md"
    mctrader-hub:
      - "docs/stories/MCT-151.md"
  MCT-152:
    mctrader-data:
      - "src/mctrader_data/ops/dual_write_window_runner.py"
      - "tests/ops/test_dual_write_window.py"
      - "docs/stories/MCT-152.md"
    mctrader-hub:
      - "docs/stories/MCT-152.md"
      - "docs/runbooks/nas-minio-unreachable-sop.md"
  MCT-153:
    mctrader-data:
      - "src/mctrader_data/migration/backfill_orchestrator.py"
      - "scripts/migration/run_backfill.py"
      - "tests/migration/test_backfill_orchestrator.py"
      - "tests/migration/test_backfill_resumability_chaos.py"
      - "docs/stories/MCT-153.md"
    mctrader-hub:
      - "docs/stories/MCT-153.md"
  MCT-154:
    mctrader-engine:
      - "src/mctrader_engine/io/cold_reader.py"
      - "src/mctrader_engine/io/reader_cache.py"
      - "src/mctrader_engine/io/endpoint_router.py"
      - "tests/io/test_endpoint_cutover.py"
      - "tests/io/test_reader_cache_flush.py"
      - "docs/stories/MCT-154.md"
    mctrader-hub:
      - "docs/stories/MCT-154.md"
      - "docs/runbooks/nas-minio-cutover-checklist.md"
  MCT-155:
    mctrader-data:
      - "src/mctrader_data/migration/cutover_verifier.py"
      - "src/mctrader_data/migration/gc_runner.py"
      - "scripts/migration/verify_rpo_zero.py"
      - "scripts/ops/rotate_minio_secret.py"
      - "tests/migration/test_cutover_verifier.py"
      - "tests/migration/test_gc_runner.py"
      - "docs/stories/MCT-155.md"
    mctrader-hub:
      - "docs/stories/MCT-155.md"
      - "docs/runbooks/nas-minio-tls-review.md"
      - "docs/runbooks/nas-minio-stage2-runbook.md"
      - "docs/retros/2026-05-stage2.md"
```

- [ ] **Step 1.4: parallelism_decision Stage 2 갱신**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml:252-271` (stage_2 sequence) 를 다음으로 교체:

```yaml
  stage_2:
    - phase: 2A
      parallel: [MCT-150, MCT-151]
      mode: parallel_with_handoff
      reason: "파일 disjoint (nas_uploader/retry_queue ↔ dual_writer/compaction_barrier/invariant_harness). MCT-151 invariant harness 가 MCT-150 Prometheus metric naming 참조 → MCT-150 metric schema freeze 후 MCT-151 본격 진입 (handoff)"
      isolation: "별도 worktree 의무 (memory feedback_parallel_session_branch_race)"
    - phase: 2B
      sequence: [MCT-151]
      mode: serial
      reason: "atomic primitive + 7종 invariant harness vertical slice"
    - phase: 2C
      parallel: [MCT-152, MCT-153]
      mode: parallel
      reason: "MCT-152 dual-write window 운영 (시간축) + MCT-153 backfill 병행 정당 (S7 closed-day scope 는 dual-write 당일 partition 과 disjoint). IOPS budget 만 S11 baseline 으로 사전 검증 조건"
      isolation: "별도 worktree 의무"
    - phase: 2D
      sequence: [MCT-154]
      mode: serial
      reason: "cutover singleton — dual-write window 종료 시점이 cutover. MCT-152+MCT-153 완료 + 7종 invariant ALL PASS 의존"
    - phase: 2E
      sequence: [MCT-155]
      mode: serial
      reason: "GC = cutover + 7d grace 만료 의존. secret rotation + TLS 재검토 는 user-blocking confirm 필요"
```

- [ ] **Step 1.5: risk_register R11~R13 추가 (Stage 2 신규 위험)**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml:351` 다음에 append:

```yaml
  - id: R11
    title: "Cutover 시점 RPO=0 위반 (S8 미달)"
    likelihood: medium
    impact: critical
    mitigation:
      - "MCT-151 cutover barrier (L1 compaction drain + dual-write toggle + collector flush 3-step gate)"
      - "MCT-155 verify_rpo_zero.py 스크립트 의무 (cutover-1s/+1s diff 검증)"
      - "실패 시 즉시 rollback (dual-write 유지 + endpoint flip 되돌림)"
    added_in: Stage 2 brainstorm
    added_at: 2026-05-12
  - id: R12
    title: "Backfill 76GB 중 NAS unreachable → stall 또는 중복 PUT"
    likelihood: medium
    impact: high
    mitigation:
      - "MCT-150 HEAD-then-PUT idempotency + conditional write smoke test 선행 (S4)"
      - "MCT-153 per-(symbol, day) checkpoint resumability + AC-5 chaos test"
      - "MCT-152 NAS unreachable SOP 실전 (S10 1000seg/10GB threshold)"
      - "MCT-150 S11 baseline 으로 사전 capacity plan (IOPS budget)"
    added_in: Stage 2 brainstorm
    added_at: 2026-05-12
  - id: R13
    title: "Dual-write 7d grace 중 drift 누적 → cutover 후 reader inconsistency"
    likelihood: low
    impact: critical
    mitigation:
      - "MCT-152 7종 invariant harness 매일 cron 실행 (MCT-151 harness 재사용)"
      - "drift>0 시 즉시 alert + MCT-154 cutover 차단"
      - "MCT-155 GC = grace 만료 + invariant ALL PASS 7일 연속 누적 후만 진입"
    added_in: Stage 2 brainstorm
    added_at: 2026-05-12
```

- [ ] **Step 1.6: references 갱신**

`scope_manifests/EPIC-cold-tier-nas-minio.yaml:361-363`:

```yaml
references:
  brainstorm_spec: ".tmp/brainstorm-cold-tier-nas-minio.md"
  stage2_brainstorm_spec: ".tmp/brainstorm-cold-tier-nas-minio-stage2.md"
  plan: ".tmp/plan-cold-tier-nas-minio.md"
  stage2_plan: "docs/superpowers/plans/2026-05-12-mct-150-stage2-uploader-hardening.md"
  adr: "docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md"
  related_adrs: [ADR-008, ADR-009, ADR-016, ADR-017]
```

(adr_reservation 줄 제거 — MCT-149 land 시 marker DELETE 됨)

- [ ] **Step 1.7: scope_manifest validate + commit (branch 분기 전 main 직접 commit 금지 — Step 2 branch 분기 후 commit)**

scope_manifest 변경은 MCT-150 Phase 1 PR 에 포함 → Step 2 의 branch 분기 후 commit.

---

## Task 2: MCT-150 Issue + branch 분기

**Files:**
- Create: GitHub Issue `mclayer/mctrader-hub#TBD` (MCT-150)
- Create: branch `mct-150/stage2-uploader-hardening`

- [ ] **Step 2.1: MCT-150 GitHub Issue 생성**

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-150] Stage 2 — uploader hardening + retry queue + Prometheus baseline + conditional write smoke + IP-allowlist 재확인" \
  --milestone 4 \
  --label "type:story,phase:요구사항,epic:cold-tier-nas-minio,stage:2" \
  --body "$(cat <<'EOF'
## Epic
[EPIC-cold-tier-nas-minio](https://github.com/mclayer/mctrader-hub/milestone/4) Stage 2 (Cold Tier Migration)

## Stage 2 첫 Story
Stage 1 (MCT-147/148/149) MERGED 2026-05-12. ADR-027 Accepted, D1~D11 박제. 본 Story = Stage 2 첫 진입 — uploader hardening primary.

## Goal
mctrader-data 의 `minio_uploader` 를 production-grade 로 hardening:
1. retry queue (NAS unreachable 시 segments backlog 보존)
2. Prometheus metrics (success/fail/latency/queue_depth/IOPS baseline)
3. conditional write smoke test (S4 HEAD-then-PUT fallback 검증)
4. IP-allowlist 재확인 (MCT-147 NAS 방화벽 rule audit)
5. NAS unreachable SOP (S10 auto-resume + 1000seg/10GB threshold + 24h manual gate)

## Addresses Decisions (Stage 2 결정 12점 중 4점)
- **S4**: HEAD-then-PUT fallback + MCT-150 에서 MinIO conditional write smoke test 선행
- **S10**: NAS unreachable SOP — auto-resume + Prometheus alert (1000seg/10GB threshold) + ADR-017 archive failure 7d grace tie-in. >24h 지속 unreachable 만 user manual gate
- **S11**: Prometheus node_exporter + container metrics, MCT-150 pre-baseline 측정
- **S12**: HTTP 유지 (Stage 1 정책 연장) — endpoint config 확정

## Phase pair
phase1_phase2 (Phase 1 = Story file + design author / Phase 2 = impl + TDD)

## Repo
mctrader-data (primary) — cross-repo Story header in mctrader-hub `docs/stories/MCT-150.md`

## SP / parallel
- SP: 5
- parallel_with: MCT-151 (file disjoint, metric schema freeze 후 handoff)

## Acceptance Criteria
- AC-1: `nas_uploader.put()` HEAD-then-PUT idempotency 검증 PASS (MinIO conditional write smoke)
- AC-2: retry queue persistent (process restart 후 resume) + bounded backlog
- AC-3: Prometheus metrics 4종 export (success_count / fail_count / latency_histogram / queue_depth_gauge) + IOPS baseline (node_exporter)
- AC-4: NAS unreachable SOP — auto-resume + 1000seg/10GB threshold alert + Grafana dashboard `mctrader/Cold Writer Health`
- AC-5: IP-allowlist re-audit runbook + NAS 측 firewall rule 명세 박제

## scope_manifest
`scope_manifests/EPIC-cold-tier-nas-minio.yaml` (Task 1 에서 Stage 2 overhaul, MCT-150 entries 박제)

## Stage 2 brainstorm spec
[.tmp/brainstorm-cold-tier-nas-minio-stage2.md](https://github.com/mclayer/mctrader-hub/blob/main/.tmp/brainstorm-cold-tier-nas-minio-stage2.md)

## Plan
[docs/superpowers/plans/2026-05-12-mct-150-stage2-uploader-hardening.md](https://github.com/mclayer/mctrader-hub/blob/main/docs/superpowers/plans/2026-05-12-mct-150-stage2-uploader-hardening.md)

## 의존
- upstream: Stage 1 ALL MERGED (MCT-147+148+149) ✅
- downstream: MCT-151 (metric schema 의존)

## ADR amendment 후보 (optional)
- ADR-027 D5 (NAS unreachable SOP) — S10 박제 (1000seg/10GB threshold) — mandatory: false
EOF
)"
```

Expected: Issue 번호 출력 (예: `#251` 또는 다음 번호). 이 번호를 다음 Step 에 사용.

- [ ] **Step 2.2: branch 분기**

```bash
git fetch origin main
git checkout -b mct-150/stage2-uploader-hardening origin/main
git status  # On branch mct-150/stage2-uploader-hardening, clean (.tmp/ untracked OK)
```

- [ ] **Step 2.3: Step 1 의 scope_manifest 변경을 branch 에 commit**

Step 1.1~1.6 의 변경을 모두 staging 후 commit:

```bash
git add scope_manifests/EPIC-cold-tier-nas-minio.yaml
git add .tmp/brainstorm-cold-tier-nas-minio-stage2.md
git add docs/superpowers/plans/2026-05-12-mct-150-stage2-uploader-hardening.md
git status
git commit -m "$(cat <<'EOF'
[MCT-150] scope_manifest Stage 2 overhaul + brainstorm spec + plan

- scope_manifest Stage 2 stories[] 12 결정 반영 overhaul
- design_decisions S1~S12 추가 (Codex review + Sonnet decider + 사용자 confirm)
- planned_files MCT-150~155 갱신 (Phase 2 PMO 2nd pass)
- parallelism_decision Stage 2 phase 2A~2E 박제
- risk_register R11~R13 신규 (Stage 2 위험)
- Stage 2 brainstorm spec land (.tmp/brainstorm-cold-tier-nas-minio-stage2.md)
- MCT-150 plan land (docs/superpowers/plans/)

사용자 confirm:
- S8 RPO=0 at cutover
- S12 HTTP 유지 (Stage 1 정책 연장)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: MCT-150 Story file Phase 1 (codeforge requirements + architect lanes)

**Files:**
- Create: `docs/stories/MCT-150.md` (hub SSOT)

codeforge consumer 패턴 — Story file 은 RequirementsPL §1~§5 + ArchitectPL §6~§11 author. 본 Task 는 codeforge agent lanes 로 위임.

- [ ] **Step 3.1: RequirementsPLAgent dispatch (Story §1~§5)**

```
Agent (codeforge-requirements:RequirementsPLAgent)
prompt: "MCT-150 Story file Phase 1 §1~§5 author. Issue #<TBD from Step 2.1>. Stage 2 첫 Story. Inputs:
- Stage 2 brainstorm spec: .tmp/brainstorm-cold-tier-nas-minio-stage2.md
- scope_manifest: scope_manifests/EPIC-cold-tier-nas-minio.yaml (MCT-150 entry)
- ADR-027: docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md (D5 SOP context)
- Addresses 결정: S4 / S10 / S11 / S12
- Previous Story pattern: docs/stories/MCT-149.md (Stage 1 종료 governance Story)

§1 사용자 요구사항 (verbatim — Stage 2 brainstorm spec §1)
§2 도메인 해석 (DomainAgent — Stage 2 brainstorm §2)
§3 관련 ADR / 코드 경로 (ADR-008/009/017/027 + MCT-147/148/149 trail)
§4 Change Impact (ChangeImpact + Feasibility + Continuity)
§5 통합 요구사항 명세
출력 = docs/stories/MCT-150.md frontmatter + §1~§5"
```

- [ ] **Step 3.2: ArchitectPLAgent dispatch (Story §6~§11)**

```
Agent (codeforge-design:ArchitectPLAgent)
prompt: "MCT-150 Story file Phase 1 §6~§11 author (RequirementsPL §1~§5 land 후). Inputs:
- Story §1~§5 (RequirementsPL Step 3.1 출력)
- Stage 2 brainstorm spec
- ADR-027 D5 (NAS unreachable SOP) + amendment 후보

deputy 6 + chief author 표준 흐름:
- CodebaseMapperAgent: 기존 minio_uploader.py 파악
- RefactorAgent: 분리 인터페이스 설계 (nas_uploader / retry_queue / metrics)
- SecurityArchitectAgent: HTTP credential leak surface (S12 4중 mitigation 재확인)
- TestContractArchitectAgent: §8 Test Contract (conditional write smoke / retry queue chaos / Prometheus metric assertion)
- DataMigrationArchitectAgent: invariant scope (Stage 2 backfill 의 사전 Hardening — direct migration scope 외이지만 forward-compat 의무)
- OperationalRiskArchitectAgent: S10 1000seg/10GB threshold + 24h gate + ADR-017 archive 7d grace tie-in
- ArchitectAgent (chief author): §6 Change Plan + ADR-027 amendment candidate (D5 optional) + §8 Test Contract + §11 data migration (N/A here)

출력 = docs/stories/MCT-150.md §6~§11 append"
```

- [ ] **Step 3.3: Phase 1 PR 작성**

```bash
git status  # docs/stories/MCT-150.md 신규
git add docs/stories/MCT-150.md
git commit -m "$(cat <<'EOF'
[MCT-150] Phase 1 — Story file §1~§11 author (RequirementsPL + ArchitectPL)

§1 사용자 요구사항 (Stage 2 brainstorm §1)
§2 도메인 해석 (ADR-017 hot path scope + ADR-009 forward-only + ADR-027 D5)
§3 관련 ADR / 코드 경로 (ADR-008/009/017/027)
§4 Change Impact (uploader hardening + retry queue + metrics)
§5 통합 요구사항 명세 (S4 / S10 / S11 / S12 addresses)
§6 Change Plan (deputy 6 통합)
§7 Test Contract (conditional write smoke + retry queue chaos)
§8 Operational Risk (S10 SOP)
§9~§11 (codeforge agent author)

Addresses: S4 / S10 / S11 / S12
Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"

git push origin mct-150/stage2-uploader-hardening
gh pr create --repo mclayer/mctrader-hub \
  --title "[MCT-150] Phase 1 — Stage 2 uploader hardening Story §1~§11" \
  --milestone 4 \
  --base main \
  --body "$(cat <<'EOF'
## Phase 1 PR

MCT-150 Stage 2 첫 Story — uploader hardening Phase 1 (Story file §1~§11 author + scope_manifest Stage 2 overhaul).

Resolves #<Issue from Step 2.1>

## §1~§11 Story file land
- §1~§5 RequirementsPL (요구사항 lane)
- §6~§11 ArchitectPL (설계 lane, deputy 6 + chief author)

## scope_manifest changes
- Stage 2 stories[] 12 결정 반영 overhaul
- design_decisions S1~S12 추가
- planned_files MCT-150~155 갱신
- parallelism_decision phase 2A~2E 박제
- risk_register R11~R13 신규

## addresses decisions
- S4 (conditional write smoke)
- S10 (NAS unreachable SOP)
- S11 (Prometheus baseline)
- S12 (HTTP 유지)

## Next
- Phase 2 = uploader impl + retry queue + Prometheus exporter + smoke test (TDD)
EOF
)"
```

- [ ] **Step 3.4: Phase 1 PR CI green + merge**

```bash
gh pr checks --repo mclayer/mctrader-hub  # CI 결과 monitor
# CI green 후
gh pr merge --repo mclayer/mctrader-hub --admin --squash --delete-branch
# main 동기화
git checkout main
git pull origin main
```

---

## Task 4: MCT-150 Phase 2 (mctrader-data impl + TDD)

**Files (mctrader-data repo):**
- Create: `src/mctrader_data/storage/nas_uploader.py`
- Create: `src/mctrader_data/storage/retry_queue.py`
- Create: `src/mctrader_data/metrics/prometheus_exporters.py`
- Create: `src/mctrader_data/ops/nas_unreachable_sop.py`
- Create: `tests/storage/test_nas_uploader.py`
- Create: `tests/storage/test_retry_queue.py`
- Create: `tests/storage/test_conditional_write_smoke.py`
- Create: `tests/metrics/test_prometheus_exporters.py`
- Create: `configs/prometheus/nas_uploader_rules.yml`

cross-repo Phase 2 — mctrader-data 에서 작업.

- [ ] **Step 4.1: mctrader-data branch 분기**

```bash
cd c:/workspace/mclayer/mctrader-data
git fetch origin main
git checkout -b mct-150/stage2-uploader-hardening origin/main
```

- [ ] **Step 4.2: DeveloperPLAgent dispatch (codeforge develop lane)**

```
Agent (codeforge-develop:DeveloperPLAgent)
prompt: "MCT-150 Phase 2 impl. Inputs:
- Story §6~§11 (hub `docs/stories/MCT-150.md` MERGED in Phase 1)
- Change Plan §6 + Test Contract §8 직접 인용
- repo: mctrader-data
- planned_files (scope_manifest MCT-150 entries)

TDD 의무 (QADeveloperAgent first):
1. conditional write smoke test (S4 HEAD-then-PUT fallback)
2. retry queue chaos test (NAS unreachable → resume)
3. Prometheus metric assertion (4종 export)
4. NAS unreachable SOP integration test (1000seg/10GB threshold)

DeveloperAgent / DataEngineerAgent / InfraEngineerAgent dynamic roster.
구현 후 pytest ALL PASS + mypy + lint clean.
Story §10 FIX Ledger 박제 의무 (FIX 발생 시)."
```

- [ ] **Step 4.3: Test lane (codeforge-test)**

```
Agent (codeforge-test:TestAgent)
prompt: "MCT-150 Phase 2 test gate.
- 기능 테스트 (pytest tests/ ALL PASS)
- 성능 테스트 (latency baseline measure — MCT-148 T2 baseline 과 정합)
PASS/FAIL 구조화 보고. FAIL 시 DeveloperPL FIX 루프 trigger."
```

- [ ] **Step 4.4: Review lanes (codeforge-review)**

```
parallel agents:
- DesignReviewPLAgent (Claude + Codex review of Change Plan §6)
- CodeReviewPLAgent (Claude + Codex review of impl)
- SecurityTestPLAgent (GitHub native + Claude/Codex review)
```

- [ ] **Step 4.5: Phase 2 PR + merge**

```bash
git status
git add src/ tests/ configs/
git commit -m "$(cat <<'EOF'
[MCT-150] Phase 2 — uploader hardening impl + TDD

Impl:
- src/mctrader_data/storage/nas_uploader.py (HEAD-then-PUT idempotency)
- src/mctrader_data/storage/retry_queue.py (persistent backlog + resume)
- src/mctrader_data/metrics/prometheus_exporters.py (4종 metric)
- src/mctrader_data/ops/nas_unreachable_sop.py (S10 SOP)

Tests (TDD):
- tests/storage/test_nas_uploader.py
- tests/storage/test_retry_queue.py
- tests/storage/test_conditional_write_smoke.py
- tests/metrics/test_prometheus_exporters.py

Prometheus:
- configs/prometheus/nas_uploader_rules.yml

Addresses: S4 / S10 / S11 / S12
Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"

git push origin mct-150/stage2-uploader-hardening
gh pr create --repo mclayer/mctrader-data \
  --title "[MCT-150] Phase 2 — uploader hardening impl + TDD" \
  --base main \
  --body "MCT-150 Phase 2 — hub Story file MERGED in Phase 1.

## Impl
- HEAD-then-PUT idempotency (S4)
- retry queue + resume (S10)
- Prometheus 4종 metric + IOPS baseline (S11)
- NAS unreachable SOP 1000seg/10GB threshold (S10)

## TDD
- conditional write smoke test (real MinIO smoke)
- retry queue chaos (NAS down → resume)
- Prometheus assertion (4종)
- SOP integration (threshold trigger)

## Addresses
S4 / S10 / S11 / S12

## Related
- hub Story file: mclayer/mctrader-hub#<Issue from Step 2.1>
- ADR-027: docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md"
```

- [ ] **Step 4.6: CI green + admin merge**

```bash
gh pr checks --repo mclayer/mctrader-data
# CI green 후
gh pr merge --repo mclayer/mctrader-data --admin --squash --delete-branch
git checkout main
git pull origin main
```

---

## Task 5: MCT-150 회고 + Stage 2 Phase A 종료 + 다음 Story (MCT-151) 진입 준비

- [ ] **Step 5.1: PMOAgent retro dispatch (자동 — memory feedback_pmo_retro_mandatory)**

```
Agent (codeforge-pmo:PMOAgent)
prompt: "MCT-150 Story 완료 회고. Stage 2 첫 Story 결과 박제.
- Story §11 retro append (cross-Story 패턴 + cross-Story 위험)
- Stage 2 milestone #4 갱신
- Cross-Story 패턴 분석 (Stage 1 trail 과 cross-link)
- ADR-027 D5 amendment 필요 여부 판단 (S10 박제 완성도)
- 다음 Story (MCT-151) handoff context 박제 (metric schema freeze 확인)"
```

- [ ] **Step 5.2: MCT-151 Issue + Phase A → B handoff**

MCT-150 metric schema freeze 후 MCT-151 본격 진입.

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-151] Stage 2 — dual-write atomic primitives + 7종 invariant harness + L1 compaction drain barrier" \
  --milestone 4 \
  --label "type:story,phase:요구사항,epic:cold-tier-nas-minio,stage:2"
# Issue body — scope_manifest MCT-151 entry 참조 (S2/S5/S8 addresses)
```

이후 MCT-151 Story 의 별도 plan 생성 (`docs/superpowers/plans/2026-05-XX-mct-151-dual-write-invariant.md`) — 본 plan scope 외.

---

## Self-Review

**1. Spec coverage check:**
- Stage 2 brainstorm spec §1 (사용자 요청) → Task 0 Pre-flight + Task 1 scope_manifest
- §2 Phase 0 context packet → scope_manifest design_decisions S1~S12 박제 + risk_register R11~R13
- §3 Phase 1 12-decision review → Task 1.2 design_decisions S1~S12
- §4 Phase 2 PMO 2nd pass → Task 1 (전체 scope_manifest overhaul)
- §5 다음 단계 → Task 3 (codeforge agent dispatch) + Task 4 (Phase 2 impl) + Task 5 (다음 Story)

**2. Placeholder scan:**
- "TBD" 사용 — Step 2.1 의 Issue 번호만 (실제 gh 출력 후 채워짐). 다른 placeholder 없음.
- 모든 step 에 실제 명령 + 예상 output 명시.

**3. Type consistency:**
- `nas_uploader.put()` API 는 Task 4.2 에서 DeveloperPL 이 결정. Phase 1 Change Plan §6 (Task 3.2) 에서 박제 의무.
- Prometheus metric name (success_count / fail_count / latency_histogram / queue_depth_gauge) Task 3.3 PR body + Task 4.2 impl 정합.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-12-mct-150-stage2-uploader-hardening.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration. codeforge agent lanes (RequirementsPL / ArchitectPL / DeveloperPL / TestAgent / Review / PMO) 자연 mapping.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review.

**Which approach?**
