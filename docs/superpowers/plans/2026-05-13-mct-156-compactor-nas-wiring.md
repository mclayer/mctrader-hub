# MCT-156 Compactor NAS Wiring + L2/L3 DualWriter Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** EPIC-cold-tier-stage-3-wiring 의 entrypoint vertical slice. 신규 hot pipeline compactor (L2/L3) 가 DualWriter (MCT-151 primitive) 를 통해 NAS MinIO 로 자동 upload 하도록 wiring. ADR-027 D4/D5/D9 amendment 박제.

**Architecture:** codeforge consumer 표준 1 Story = 2 PR 흐름. Phase 1 PR = Architect lane (Story file §1-§11 + ADR-027 amendment + Change Plan), Phase 2 PR = Developer + QA lane (compose env 전환 + cli inject + runner._run_l2 신규 + _run_l3 DualWriter 교체 + integration test). DualWriter 의 status enum 3종 (committed / local_only / hard_floor_blocked) + retry queue + 7종 invariant harness 재사용. legacy `MinioUploader` deprecation 마킹 (삭제는 후속 Epic).

**Tech Stack:** Python 3.13, pytest, boto3 (S3 API), prometheus_client, Docker compose. codeforge plugins (codeforge-design / codeforge-develop / codeforge-test / codeforge-review / codeforge-pmo).

**Spec reference:** [docs/superpowers/specs/2026-05-13-cold-tier-stage-3-wiring-design.md](../specs/2026-05-13-cold-tier-stage-3-wiring-design.md)

---

## File Structure

### mctrader-hub (governance)
- **Modify**: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — D4/D5/D9 amendment (Phase 1 land)
- **Create**: `docs/stories/MCT-156.md` — Story file (§1-§12) (Phase 1/2 incremental)
- **Modify**: `CLAUDE.md` — Stage 3 wiring 섹션 신규 (Phase 2 §11 산출물)
- **Modify**: `scope_manifests/EPIC-cold-tier-nas-minio.yaml` — Stage 3 follow-up note OR 신규 `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` 발의 (Phase 1)
- **Create**: `docs/retros/RETRO-MCT-156.md` — Phase 2 land 직후 PMOAgent dispatch

### mctrader-data (구현)
- **Modify**: `compose.yml` — compactor service env `MINIO_*` → `NAS_MINIO_*` 전환, endpoint NAS 192.168.50.200
- **Modify**: `src/mctrader_data/cli.py:619-658` (`compact_cmd`) — NASUploader + DualWriter lazy build inject
- **Modify**: `src/mctrader_data/compactor/runner.py` — `_run_l2_for_parquet` 신규 (현재 부재) + `_run_l3_for_parquet` 의 MinioUploader → DualWriter 교체
- **Modify**: `src/mctrader_data/compactor/minio_uploader.py:1` — deprecation docstring 마킹
- **Modify**: `src/mctrader_data/nas_metrics/prometheus_exporters.py` — DualWriter status 3종 metric label (예: `dual_write_result_total{status="committed|local_only|hard_floor_blocked", tier="L2|L3"}`)
- **Create**: `tests/integration/test_compactor_nas_wiring.py` — DualWriter status 3종 + retry queue + 7종 invariant harness wiring smoke
- **Modify**: `CLAUDE.md` — compactor NAS wiring 섹션 신규 (Phase 2 §11 산출물)

---

## Task 1: Phase 1 사전 준비 (counter reservation + Issue 생성)

**Files:**
- Modify: `mctrader-hub/scope_manifests/counters.json` — `MCT.next` 156 reservation
- GitHub: mctrader-hub Issue #MCT-156 (Phase 1 PR target)

- [ ] **Step 1: counters.json reservation**

```bash
cd /c/workspace/mclayer/mctrader-hub
python -c "import json; p='scope_manifests/counters.json'; d=json.load(open(p)); print('current next:', d['MCT']['next'])"
```

`MCT.next` 가 156 이면 OK. 아니면 인접 Story 와 collision 확인 후 156 reserve.

- [ ] **Step 2: GitHub Issue 생성 (mctrader-hub)**

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-156] compactor NAS wiring + L2/L3 DualWriter injection (Stage 3 entrypoint)" \
  --label "type:story,phase:설계" \
  --body "$(cat <<'EOF'
## Story 요약
EPIC-cold-tier-stage-3-wiring 의 entrypoint vertical slice. ADR-027 Stage 2 EPIC CLOSED 후 발견된 hot pipeline NAS wiring gap 해소.

## 7 결정점 박제 (spec §2)
- S1: legacy L2 재이관 0 (ADR-009 §D2.1/§D14 reader fallback)
- S2: DualWriter (MCT-151) inject
- S3: L1 제외, L2/L3 만 NAS upload
- S4: 신규 Epic (EPIC-cold-tier-stage-3-wiring)
- S5: ADR-027 D4/D5/D9 amendment, D6 불변
- S6: legacy retroactive 재구조 비권고
- S7: L3 backfill 별 Story 불필요

## 산출물
- Phase 1 PR: docs/stories/MCT-156.md §1-§11 + docs/adr/ADR-027.md D4/D5/D9 amendment + scope_manifest
- Phase 2 PR: compose.yml + cli.py + runner.py + minio_uploader deprecation + prometheus_exporters + integration test

## Spec
docs/superpowers/specs/2026-05-13-cold-tier-stage-3-wiring-design.md
EOF
)"
```

생성된 Issue 번호 기록 (예: #279 — 다음 task 에서 PR body cross-link 에 사용).

- [ ] **Step 3: Commit counters.json**

```bash
git add scope_manifests/counters.json
git commit -m "chore(MCT-156): reserve counter 156 for Stage 3 wiring entrypoint Story"
```

---

## Task 2: Phase 1 worktree + ArchitectPLAgent dispatch

**Files:**
- Worktree: `mctrader-hub` branch `mct-156-phase1-architect` (별 디렉토리, parallel session 충돌 회피)
- Modify: `docs/stories/MCT-156.md` (신규, §1-§11)
- Modify: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (D4/D5/D9 amendment)
- Modify: `scope_manifests/` (Stage 3 분기 결정 반영)

- [ ] **Step 1: GitOpsAgent dispatch — Phase 1 worktree 생성**

GitOpsAgent (codeforge-pmo) 호출:

```
Task: mctrader-hub Phase 1 worktree 생성

Branch: mct-156-phase1-architect (base: main)
Worktree path: c:/workspace/mclayer/mctrader-hub-mct156-phase1
Purpose: ADR-027 D4/D5/D9 amendment + Story file MCT-156 §1-§11 + scope_manifest 작성

memory feedback: "Parallel hub session branch race" — 동일 hub working dir 공유 시 branch switch race 회피 의무. worktree 채택.
```

- [ ] **Step 2: ArchitectPLAgent dispatch (worktree 내부)**

ArchitectPLAgent (codeforge-design) 호출. 6+2 deputy 자동 spawn:

```
Story: MCT-156 (Phase 1 PR — Architect lane)
Spec: docs/superpowers/specs/2026-05-13-cold-tier-stage-3-wiring-design.md
Worktree: c:/workspace/mclayer/mctrader-hub-mct156-phase1

산출물 의무:
1. docs/stories/MCT-156.md §1-§11 작성 (codeforge Story file 표준)
   - frontmatter: epic_key=EPIC-cold-tier-stage-3-wiring, parent_dep=EPIC-cold-tier-nas-minio
   - §1 동기 (spec §0 cross-reference)
   - §2 루트 원인 4종 (spec §1 cross-reference)
   - §3 결정점 7건 + design_decisions (spec §2 cross-reference)
   - §4 ADR-027 amendment plan (D4/D5/D9)
   - §5 Out of scope 명시 (spec §9)
   - §6 Change Plan (D1~D11):
     * D1 영향 repo 매핑
     * D2 영향 파일 (spec §10 planned_files)
     * D3 신규 모듈 (runner._run_l2_for_parquet 메소드)
     * D4 인터페이스 변경 (CompactorRunner.__init__ signature: NASUploader/DualWriter 추가)
     * D5 호환성 (legacy MinioUploader deprecation 마킹 only, 호출처 제거는 Phase 2)
     * D6 마이그레이션 (compose env 전환 = atomic, in-place)
     * D7 트레이스 (Story #279 → ADR-027 amendment trail)
     * D8 Test Contract (spec §8 MCT-156 항목 4종)
     * D9 운영 risk (R2 mitigation — Phase 2 의 prometheus label)
     * D10 보안 risk (NAS credential masking obligation, ADR-008 정합)
     * D11 데이터 마이그레이션 (NONE — S1 결정 정합, retroactive 0)
   - §7 deputy 산출 박제 (Mapper/Refactor/SecurityArch/TestContractArch/DataMigrationArch/OperationalRiskArch + LiveOps/LiveOrdering 조건부)
   - §8 Test Contract (spec §8 MCT-156 4종 — Phase 2 QADeveloperAgent 가 구현)
   - §9 reservation marker DELETE 의무 (Phase 2 §11 land 직후)
   - §10 FIX Ledger (초기 empty — Phase 2 진입 시 채워짐)
   - §11 산출물 self-write (Phase 2 §11 PMOAgent dispatch 후 작성)

2. docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md 갱신:
   - D4 amendment: "Stage 3 wiring obligation — compactor/runner.py L2/L3 DualWriter inject 의무 박제. legacy MinioUploader (MCT-149 이전) deprecation, MCT-156 Phase 2 에서 호출처 제거."
   - D5 amendment: "retry queue + Prometheus alert wiring obligation — MCT-150 NASUploader retry queue 가 hot pipeline runner 의 L2/L3 compaction 후 dual-write 단계에 inject 의무. hard_floor_blocked → SOP MANUAL_GATE escalation."
   - D9 amendment: "reader read-through cache 의 mixed layout 책임 경계 — ADR-009 §D2.1 (node=DEFAULT fallback) + §D14 (tier=absent → L1 treated) 가 legacy L2 객체 (hour-key 부재) 의 reader 호환을 보장. 신규 L2 (hour=HH/node=MERGED) 와 legacy L2 (node=DEFAULT) mixed scan = scan_* API 의 partition pruning 자연 양립."
   - D6 amend 0 (RPO=0 invariant 유지)
   - History 섹션 append: "2026-05-13 — D4/D5/D9 amendment (MCT-156 Stage 3 wiring)"

3. scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml 신규 (spec §10 YAML 박제)

deputy 6+2 자동 spawn:
- CodebaseMapperAgent: 영향 파일 fact-only 매핑 (spec §10 planned_files cross-verify)
- RefactorAgent: DualWriter inject 패턴 권고 (decoupling/pattern)
- SecurityArchitectAgent: NAS credential masking + threat model (ADR-008 정합)
- TestContractArchitectAgent: §8 Test Contract 4종 invariant 후보
- DataMigrationArchitectAgent: D11 NONE 변호 (S1 retroactive 0)
- OperationalRiskArchitectAgent: D9 risk + retry queue invariant
- LiveOpsDeputyAgent: 조건부 spawn 결정 (live mode 무관 → skip)
- LiveOrderingDeputyAgent: 조건부 spawn 결정 (live mode 무관 → skip)
```

- [ ] **Step 3: DesignReview lane (Phase 1 PR 직전)**

DesignReviewPLAgent (codeforge-review) 호출 — Claude + Codex peer review:

```
Story: MCT-156 Phase 1 PR design review
Worktree: c:/workspace/mclayer/mctrader-hub-mct156-phase1
Target: docs/stories/MCT-156.md + docs/adr/ADR-027.md amendment + scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml

Lane: 설계리뷰 (Change Plan 품질 게이트)
Peer reviewers: ClaudeReviewAgent + CodexReviewAgent (lane-agnostic, packet domain injection)
```

FAIL 시 ArchitectPLAgent FIX iteration (memory: "CI failure auto-recovery" 정합, root-cause-decision 의무 + fix-ledger §10 append).

- [ ] **Step 4: Phase 1 PR 생성**

```bash
cd c:/workspace/mclayer/mctrader-hub-mct156-phase1
gh pr create --repo mclayer/mctrader-hub \
  --title "[MCT-156] Phase 1 — ADR-027 D4/D5/D9 amendment + Stage 3 wiring Story" \
  --body "$(cat <<'EOF'
## Summary
- ADR-027 D4/D5/D9 amendment (Stage 3 wiring obligation + retry queue + mixed layout reader 책임 경계)
- Story file docs/stories/MCT-156.md §1-§11 박제
- 신규 scope_manifest EPIC-cold-tier-stage-3-wiring.yaml (Stage 2 retro 보존, 신규 milestone)
- 코드 변경 0 (Phase 1 = docs only)

## 7 결정점 (spec §2)
[S1~S7 박제 표 — Story §3 참조]

## ADR-027 amendment trail
- D4: compactor L2/L3 DualWriter inject 의무
- D5: retry queue + Prometheus alert wiring obligation
- D9: mixed layout reader 책임 경계 (legacy + 신규)

## Closes
#279

## Spec
docs/superpowers/specs/2026-05-13-cold-tier-stage-3-wiring-design.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 5: CI watch + admin merge**

memory feedback: "CI failure auto-recovery" + "No background CI watch" + "Admin merge autonomy" + "CI watch terminal states" 정합.

```bash
PR_NUMBER=$(gh pr list --repo mclayer/mctrader-hub --head mct-156-phase1-architect --json number --jq '.[0].number')
gh pr checks $PR_NUMBER --repo mclayer/mctrader-hub --watch
```

- SUCCESS → 즉시 `gh pr merge $PR_NUMBER --repo mclayer/mctrader-hub --admin --squash`
- FAILURE / ACTION_REQUIRED / BLOCKED → 자동 fix→push→re-watch cycle (사용자 trigger 0)

- [ ] **Step 6: Worktree cleanup**

GitOpsAgent dispatch — Phase 1 worktree 삭제 (branch 보존, merge commit 추적용).

---

## Task 3: Phase 2 worktree + DeveloperPLAgent + QADeveloperAgent parallel dispatch

**Files:**
- Worktree 1: `mctrader-data` branch `mct-156-phase2-dev` (구현 본체)
- Worktree 2: `mctrader-hub` branch `mct-156-phase2-docs` (Story §11 산출물 self-write + CLAUDE.md 갱신)
- Modify: 위 File Structure §mctrader-data 전체
- Modify: 위 File Structure §mctrader-hub (CLAUDE.md, scope_manifest milestone)

- [ ] **Step 1: GitOpsAgent dispatch — 2 repo Phase 2 worktree 동시 생성**

```
Task: MCT-156 Phase 2 worktree 2개 동시 생성

repo 1: mctrader-data
  branch: mct-156-phase2-dev
  base: main
  worktree: c:/workspace/mclayer/mctrader-data-mct156-phase2

repo 2: mctrader-hub
  branch: mct-156-phase2-docs
  base: main (Phase 1 merge 후)
  worktree: c:/workspace/mclayer/mctrader-hub-mct156-phase2

Cross-repo Epic centralization: mctrader-hub 가 governance 중심.
```

- [ ] **Step 2: DeveloperPLAgent dispatch (mctrader-data worktree)**

DeveloperPLAgent (codeforge-develop) 호출. 동적 roster: DeveloperAgent + InfraEngineerAgent (compose) + 필요 시 DataEngineerAgent. QADeveloperAgent 병렬:

```
Story: MCT-156 Phase 2 PR (구현 lane)
Worktree: c:/workspace/mclayer/mctrader-data-mct156-phase2
Change Plan source: mctrader-hub#279 Phase 1 PR merged Story §6

산출 의무:

### 변경 1: compose.yml compactor service env 전환
파일: compose.yml
변경:
  compactor:
    environment:
      # MINIO_ENDPOINT: http://minio:9000  # legacy, 삭제
      NAS_MINIO_ENDPOINT: ${NAS_MINIO_ENDPOINT:-http://192.168.50.200:9000}
      NAS_MINIO_ACCESS_KEY: ${NAS_MINIO_ACCESS_KEY}
      NAS_MINIO_SECRET_KEY: ${NAS_MINIO_SECRET_KEY}
      NAS_MINIO_BUCKET: ${NAS_MINIO_BUCKET:-mctrader-market}
      # ... 기존 env (MCTRADER_DATA_ROOT, PYTHONUNBUFFERED, MCTRADER_COMPACTOR_METRICS_PORT 등) 유지

근거: ADR-027 D4 amendment + spec §10 planned_files. ingester service (bithumb-ingester, upbit-ingester) 의 MINIO_* env 는 변경 0 (L1 hot path 무영향, ADR-027 §D5 invariant).

### 변경 2: cli.py compact_cmd 에 NASUploader + DualWriter lazy build inject
파일: src/mctrader_data/cli.py
변경 위치: compact_cmd 함수 (line 619-658)
구현:
  - NAS_MINIO_ENDPOINT env 가 set 되어 있으면 NASUploader + DualWriter build
  - 아니면 None (test/local dev mode)
  - CompactorRunner(root, dual_writer=...) 로 inject

예시 (정확한 wiring 은 ArchitectPLAgent §6 Change Plan §D3/D4 따름):
```python
from mctrader_data.nas_storage.nas_uploader import NASUploader
from mctrader_data.nas_storage.dual_writer import DualWriter
from mctrader_data.nas_storage.retry_queue import RetryQueue

dual_writer = None
if os.environ.get("NAS_MINIO_ENDPOINT"):
    retry_queue = RetryQueue(...)  # ADR-027 D5 retry queue
    nas_uploader = NASUploader(
        endpoint=os.environ["NAS_MINIO_ENDPOINT"],
        access_key=os.environ["NAS_MINIO_ACCESS_KEY"],
        secret_key=os.environ["NAS_MINIO_SECRET_KEY"],
        bucket=os.environ.get("NAS_MINIO_BUCKET", "mctrader-market"),
        retry_queue=retry_queue,
    )
    dual_writer = DualWriter(nas_uploader=nas_uploader)

runner = CompactorRunner(Path(root), dual_writer=dual_writer)
```

### 변경 3: runner.py — _run_l2_for_parquet 신규 + _run_l3 DualWriter 교체
파일: src/mctrader_data/compactor/runner.py
변경 위치:
  - __init__: minio_uploader 인자 → dual_writer 인자 (legacy MinioUploader 제거)
  - _run_l2: 신규 메소드 (현재 부재) — L2 compaction 후 DualWriter.put 호출
  - _run_l3_for_parquet (line 142-161): MinioUploader.upload → DualWriter.put 교체
  - _tick (line 118+): L2 처리 후 _run_l2 호출 추가

DualWriter.put(local_path, nas_key, sha256) status enum 3종 처리:
  - "committed" → 정상 (local + NAS atomic visible)
  - "local_only" → retry_queue 에 enqueue 됨, log info
  - "hard_floor_blocked" → log error + Prometheus alert + SOP MANUAL_GATE escalation

### 변경 4: minio_uploader.py deprecation 마킹
파일: src/mctrader_data/compactor/minio_uploader.py
변경: docstring 1줄 위 deprecation 박제

```python
"""MinIO uploader — uploads completed L3 Parquet files to S3-compatible object storage.

.. deprecated:: MCT-156 (Stage 3 wiring)
   Replaced by DualWriter (MCT-151 primitive) for L2/L3 NAS dual-write.
   Call sites removed in MCT-156 Phase 2. Module file removal scheduled
   for post-EPIC-cold-tier-stage-3-wiring Epic.
"""
```

### 변경 5: prometheus_exporters.py — DualWriter status 3종 metric (R2 mitigation 일부)
파일: src/mctrader_data/nas_metrics/prometheus_exporters.py
변경: 신규 Counter
```python
dual_write_result_total = Counter(
    "mctrader_dual_write_result_total",
    "DualWriter put() result count by status and tier",
    ["status", "tier"],  # status ∈ {committed, local_only, hard_floor_blocked}, tier ∈ {L2, L3}
)
```
(layout label legacy_node_default vs new_node_merged 분리 = R2 후속 = MCT-157 scope, 본 Story 는 status 3종 + tier 만)

병렬 dispatch: QADeveloperAgent (codeforge-develop) — 테스트 작성:

산출 의무: tests/integration/test_compactor_nas_wiring.py (신규)
- test 1: DualWriter committed → bucket prefix `tier=L2/.../hour=HH/node=MERGED/` 출현 (mock NAS)
- test 2: DualWriter committed → bucket prefix `tier=L3/.../node=MERGED/` 출현 (mock NAS)
- test 3: NAS unreachable → DualWriter local_only → retry_queue enqueue 검증
- test 4: retry_queue hard floor → DualWriter hard_floor_blocked → SOP MANUAL_GATE escalation 검증
- test 5: L1 NAS upload 0 (S3 결정 invariant — L1 compaction 후 dual_writer 호출 absence 검증)
- test 6: legacy MinioUploader 호출처 0 (grep 검증, deprecation 정합)
- test 7: prometheus_exporters dual_write_result_total Counter emit (status=committed, tier=L2 sample)

ADR-027 §8 Test Contract 4종 (compose env switch / DualWriter status 3종 / retry queue replay / 7종 invariant harness wiring) ALL PASS 의무.
```

- [ ] **Step 3: TestAgent dispatch — 실 test 실행 게이트**

TestAgent (codeforge-test) 호출:

```
Worktree: c:/workspace/mclayer/mctrader-data-mct156-phase2
Test runner: pytest (configs 표준)

Functional: pytest tests/integration/test_compactor_nas_wiring.py -v --tb=short
Perf baseline: compactor L2 compact_hour latency 측정 (MCT-148 T2 NFR-1 정합, 1h 분량 < 3000ms)

PASS/FAIL 구조화 보고. FAIL 시 root-cause-decision (codeforge skill) + fix-ledger §10 append + DeveloperPLAgent FIX iteration.
```

- [ ] **Step 4: SecurityTestPLAgent dispatch — 보안 게이트**

SecurityTestPLAgent (codeforge-review) 호출:

```
Worktree: c:/workspace/mclayer/mctrader-data-mct156-phase2
1차: GitHub native (secret scanning, dependabot)
2차: Claude/Codex peer review

집중 검토:
- NAS credential masking (log/exception/Prometheus label 0 노출, ADR-008 정합)
- compose env 변경의 .env / .gitignore 영향
- DualWriter inject 의 thread safety (concurrent compactor tick)
- retry queue persisted data 의 credential 0 의무
```

- [ ] **Step 5: CodeReviewPLAgent dispatch — 구현 리뷰**

CodeReviewPLAgent (codeforge-review) 호출:

```
Worktree: c:/workspace/mclayer/mctrader-data-mct156-phase2
Peer: ClaudeReviewAgent + CodexReviewAgent

집중 검토:
- DualWriter inject pattern 정합 (RefactorAgent §7.2 박제 vs 구현 일치)
- runner._run_l2 신규 메소드의 idempotence (compaction tick 재실행 안전)
- legacy MinioUploader 호출처 grep = 0 확인
- compose env switch 의 backward compat (test mode = dual_writer None 경로)
```

- [ ] **Step 6: Phase 2 PR 생성 (mctrader-data + mctrader-hub 2 PR)**

mctrader-data Phase 2 PR:

```bash
cd c:/workspace/mclayer/mctrader-data-mct156-phase2
gh pr create --repo mclayer/mctrader-data \
  --title "[MCT-156] Phase 2 — compactor NAS wiring + L2/L3 DualWriter injection" \
  --body "$(cat <<'EOF'
## Summary
- compose.yml compactor service env 전환 (MINIO_* → NAS_MINIO_*, endpoint 192.168.50.200)
- cli.compact_cmd 에 NASUploader/DualWriter lazy build inject
- runner._run_l2_for_parquet 신규 (L2 compaction 후 DualWriter.put)
- runner._run_l3_for_parquet 의 MinioUploader → DualWriter 교체
- minio_uploader.py deprecation 마킹 (호출처 0)
- prometheus_exporters DualWriter status 3종 Counter 추가
- tests/integration/test_compactor_nas_wiring.py 신규 (7 test, ALL PASS)

## ADR
ADR-027 D4/D5/D9 amendment (mctrader-hub#279 Phase 1 land)

## Closes
mctrader-hub#279 (Phase 2)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

mctrader-hub Phase 2 PR (Story §11 self-write + CLAUDE.md 갱신):

```bash
cd c:/workspace/mclayer/mctrader-hub-mct156-phase2
# 산출물: docs/stories/MCT-156.md §11 (산출물 박제) + CLAUDE.md "compactor NAS wiring" 섹션
# + scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml milestone update (1/3 Story done)

gh pr create --repo mclayer/mctrader-hub \
  --title "[MCT-156] Phase 2 — Story §11 산출물 + CLAUDE.md compactor NAS wiring 섹션" \
  --body "$(cat <<'EOF'
## Summary
- docs/stories/MCT-156.md §11 산출물 self-write (mctrader-data#XXX Phase 2 PR cross-link)
- CLAUDE.md "compactor NAS wiring" 섹션 신규 (DualWriter inject + env 전환 운영 가이드)
- scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml milestone 1/3 (MCT-156 done)

## Closes
#279 (Phase 2)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 7: CI watch + admin merge (2 PR sequential)**

memory: "CI watch terminal states" + "No background CI watch" 정합. mctrader-data 먼저 merge → mctrader-hub merge (Story §11 cross-link 정합).

```bash
# mctrader-data first
DATA_PR=$(gh pr list --repo mclayer/mctrader-data --head mct-156-phase2-dev --json number --jq '.[0].number')
gh pr checks $DATA_PR --repo mclayer/mctrader-data --watch
gh pr merge $DATA_PR --repo mclayer/mctrader-data --admin --squash

# mctrader-hub after
HUB_PR=$(gh pr list --repo mclayer/mctrader-hub --head mct-156-phase2-docs --json number --jq '.[0].number')
gh pr checks $HUB_PR --repo mclayer/mctrader-hub --watch
gh pr merge $HUB_PR --repo mclayer/mctrader-hub --admin --squash
```

---

## Task 4: PMOAgent retro dispatch

**Files:**
- Create: `mctrader-hub/docs/retros/RETRO-MCT-156.md`
- Modify: `mctrader-hub/docs/stories/MCT-156.md` §12 (PMOAgent self-write 영역)
- Modify: `mctrader-hub/scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` (milestone 1/3 → 박제)

- [ ] **Step 1: PMOAgent dispatch**

memory: "PMO 회고 자동 dispatch 의무" — Story fix/ADR/Story 생성 후 세션 종료 전 PMOAgent 자동 dispatch.

```
Task: MCT-156 retro

Story: MCT-156 (Phase 1 + Phase 2 ALL MERGED)
Phase 1 PR: mctrader-hub#XXX (ADR-027 D4/D5/D9 amendment + Story §1-§11)
Phase 2 PR: mctrader-data#XXX + mctrader-hub#XXX (구현 + Story §11)

산출 의무:
1. docs/retros/RETRO-MCT-156.md 신규 작성:
   - 시작/종료 timestamp
   - 7 결정점 ↔ 실제 구현 정합 검증
   - Codex review (Phase 0 dispatch) ↔ 최종 구현 차이 박제 (있으면)
   - FIX iteration 발생 시 root-cause + fix-ledger §10 발췌
   - R1 (release gate smoke) 가 MCT-158 에 할당된 trail 박제
   - Stage 2 EPIC CLOSED 와의 traceability link
2. docs/stories/MCT-156.md §12 self-write (codeforge Story file 표준)
3. scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml milestone 1/3 박제 (MCT-156 done, MCT-157/158 pending)
4. Cross-Story 패턴 분석 (있으면) — Stage 2 → Stage 3 transition gap 학습 박제
5. ESCALATE 트렌드 누적 → ADR 후보 발의 (있으면)
```

- [ ] **Step 2: retro PR merge (또는 main 직접 push, 사용자 정책 따름)**

mctrader-hub 의 retro 파일은 보통 직접 commit (PR 없이) 또는 작은 PR. memory: "Admin merge autonomy" + "codeforge usage mandatory" 정합 — codeforge 의 PMOAgent 가 자체 write boundary 따라 처리.

---

## Task 5: 다음 Story 진입 준비 (MCT-157 / MCT-158)

- [ ] **Step 1: MCT-157 GitHub Issue + Story file scaffold**

MCT-157 (Prometheus layout label 분리) = MCT-156 land 후 병렬 가능 (단독 file disjoint). 별 plan 발의:

```bash
# 별 plan 파일 — docs/superpowers/plans/2026-05-13-mct-157-prometheus-layout-label.md (후속)
```

- [ ] **Step 2: MCT-158 진입 조건 확인**

MCT-158 (Stage 3 release gate smoke test) 진입 조건:
- MCT-156 + MCT-157 둘 다 MERGED + 6h 운영 evidence (R1 release gate 자체)

- [ ] **Step 3: spec milestone 갱신**

```bash
cd /c/workspace/mclayer/mctrader-hub
# scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml milestone 갱신
# MCT-156: COMPLETED (date, PR links)
# MCT-157: PROPOSED
# MCT-158: PROPOSED (depends_on: MCT-156, MCT-157)
```

---

## Self-Review

**1. Spec coverage check:**
- ✅ S1 (legacy 재이관 0) → Phase 1 ADR-027 D9 amendment + Phase 2 grep 0 검증
- ✅ S2 (DualWriter inject) → Phase 2 변경 2/3 + test 1-4
- ✅ S3 (L1 제외) → Phase 2 변경 3 (runner.py L1 처리부 dual_writer 호출 0 invariant) + test 5
- ✅ S4 (신규 Epic) → Phase 1 scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml 신규
- ✅ S5 (ADR-027 D4/D5/D9) → Phase 1 ADR amendment
- ✅ S6 (legacy 재구조 비권고) → Phase 1 ADR D9 + Phase 2 D11=NONE
- ✅ S7 (L3 backfill 별 Story 불필요) → Phase 2 forward-only (L3 compaction 후 자연 NAS upload)
- ✅ R1 (release gate) → MCT-158 할당 (out of scope for MCT-156, Task 5 Step 2)
- ✅ R2 (Prometheus label) → MCT-156 = status/tier label, MCT-157 = layout label (별 Story)
- ✅ ADR-009 §D2.1 fallback 활용 → Phase 1 ADR-027 D9 amendment 본문 박제
- ✅ ADR-017 hot path 무영향 invariant → Phase 2 test 5 (L1 NAS upload 0)
- ✅ deprecation (legacy MinioUploader) → Phase 2 변경 4

**2. Placeholder scan:** placeholder 없음 — 모든 env / 파일 / 함수 / test 명 명시.

**3. Type consistency:**
- `DualWriter.put(local_path, nas_key, sha256) → DualWriteResult(status enum 3종)` — Phase 2 변경 2/3/test 통일
- `dual_writer` 인자 이름 — cli.py / CompactorRunner.__init__ / DualWriter 클래스 통일
- env 이름 `NAS_MINIO_ENDPOINT` / `NAS_MINIO_ACCESS_KEY` / `NAS_MINIO_SECRET_KEY` / `NAS_MINIO_BUCKET` — compose / cli / test 통일 (MCT-150 NASUploader 와 정합)
- Prometheus metric 이름 `mctrader_dual_write_result_total{status, tier}` — Phase 2 변경 5 + test 7 통일

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-mct-156-compactor-nas-wiring.md`. Two execution options:

1. **Subagent-Driven (recommended)** — codeforge agent 표준. ArchitectPLAgent / DeveloperPLAgent / QADeveloperAgent / TestAgent / SecurityTestPLAgent / CodeReviewPLAgent / PMOAgent / GitOpsAgent dispatch sequence, 각 단계 사이 review checkpoint.
2. **Inline Execution** — 직접 코드 작성 (codeforge agent dispatch 우회). memory: "Always subagent-driven execution" 박제 → 이 옵션 비권고.

Which approach?
