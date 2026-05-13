# MCT-162 L1 Channel Parity + orderbookdepth Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** EPIC-compactor-operations 의 entrypoint Story-1. L1Compactor `_schema_version` allowlist 에 `orderbookdepth` 채널 추가 + WAL delta `changes` payload → parquet converter 신규 + fail-fast invariant (silent skip 차단) + Prometheus emit obligation. MCT-156 deploy 후 발견된 5중 차단 중 #1 (upbit L1 lost) + #4 (L1 backlog 79k orderbookdepth 48k 누적) 의 root cause 해소.

**Architecture:** codeforge consumer 표준 1 Story = 2 PR (Phase 1 hub PR docs only + Phase 2 mctrader-data code + mctrader-hub Phase 2 docs). ADR-009 §D11 amendment (orderbookdepth schema 정의) + ADR-027 D4 amendment (channel parity 정책). L1Compactor.compact_segment 의 `_schema_version()` dispatch + converter dispatch + path derive 확장. 모든 변경 sequential 처리 (Story-2 MCT-160 의 l2.py 변경 전 land 의무 — merge 충돌 회피).

**Tech Stack:** Python 3.13, pytest, pyarrow, prometheus_client, Docker compose. codeforge plugins (codeforge-design / codeforge-develop / codeforge-test / codeforge-review / codeforge-pmo).

**Spec reference:** [docs/superpowers/specs/2026-05-13-compactor-operations-design.md](../specs/2026-05-13-compactor-operations-design.md)

---

## File Structure

### mctrader-hub (governance)
- **Modify**: `docs/adr/ADR-009-ohlcv-schema.md` — §D11 amendment (orderbookdepth schema)
- **Modify**: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — D4 amendment append (channel parity 정책 + fail-fast)
- **Create**: `docs/stories/MCT-162.md` — Story file (§1-§12)
- **Create**: `scope_manifests/EPIC-compactor-operations.yaml` — 신규 epic manifest (본 PR 에서 land)
- **Modify**: `.codeforge/counters.json` — MCT-160 retitle + MCT-162 신규 reservation
- **Modify**: `CLAUDE.md` — EPIC-compactor-operations 진입 박제 섹션 (Phase 2 §11 산출물)
- **Create**: `docs/retros/RETRO-MCT-162.md` — Phase 2 land 직후 PMOAgent dispatch

### mctrader-data (구현)
- **Modify**: `src/mctrader_data/compactor/l1.py` — `_schema_version` 확장 (orderbookdepth) + converter dispatch + fail-fast
- **Modify**: `src/mctrader_data/nas_metrics/prometheus_exporters.py` — `compactor_unsupported_channel_total` Counter 추가
- **Create**: `tests/integration/test_l1_compactor_channel_parity.py` — orderbookdepth converter + fail-fast + Prometheus emit

---

## Task 1: 사전 조사 + Phase 1 사전 준비 (WAL payload sample fetch + counters + Issue)

**Files:**
- Modify: `mctrader-hub/.codeforge/counters.json`
- GitHub: mctrader-hub Issue #MCT-162 (Phase 1 PR target)

- [ ] **Step 1: orderbookdepth WAL payload sample fetch (의무 — schema 추론용)**

```bash
docker exec mctrader-compactor sh -c "find /var/lib/mctrader/data/wal/bithumb/orderbookdepth -name '*.ndjson.sealed' | head -1" \
  | xargs -I {} docker exec mctrader-compactor head -3 {}
```

기대 출력: NDJSON 3줄. 각 줄 = orderbookdepth event 1개. JSON keys 확인 의무 (예상: `ts_utc`, `symbol`, `changes`, `bid_or_ask`, `price`, `qty`, `node_id`, `collector_run_id` 등).

이 sample 의 정확한 schema = Phase 1 ArchitectPLAgent 가 ADR-009 §D11 amendment 본문에 박제.

- [ ] **Step 2: 사용자 결정 verify — Story-1 진입 전 preflight 의무 (D4)**

```bash
docker compose -f c:/workspace/mclayer/mctrader-data/compose.yml ps compactor
```

기대 출력: 현재 STATE = Up. 다음 Phase 2 진입 직전 stop 의무 (Task 3 Step 1 에서 실행). 본 Phase 1 PR (docs only) 는 compactor 정지 불요 — 코드 변경 0.

- [ ] **Step 3: counters.json verify (사용자가 이미 박제)**

```bash
cat c:/workspace/mclayer/mctrader-hub/.codeforge/counters.json | python -c "import json,sys; d=json.load(sys.stdin); print('next:', d['counters']['mctrader-hub']['next']); print('MCT-162 reserved:', 'MCT-162' in d['reservations'])"
```

기대 출력: `next: 162` (또는 그 이상). `MCT-162 reserved: False`. 

만약 `next < 163` 이면 본 Task Step 4 에서 `next: 163` 으로 증가 + MCT-162 reservation 추가. 사용자가 이미 MCT-159/160/161 박제했으므로 `next` 값 확인 후 부족 시 갱신.

- [ ] **Step 4: counters.json 갱신 — MCT-162 reservation + MCT-160 retitle**

`scope_manifests/MCT-160` 의 title 을 brainstorm Phase 0 결정 정합으로 retitle. PowerShell 또는 jq:

```python
# python script (Edit tool 또는 직접 박제)
# .codeforge/counters.json:
# 1. next: 162 → 163 (또는 이미 162 이상이면 skip)
# 2. reservations["MCT-160"]["title"] retitle: 
#    "compactor L1 backlog cleanup — orderbookdepth channel FIX + L2 offset overflow FIX + MCT-153 손실 박제 retrofit"
#    → "L2/L3 cadence + OOM + L1 backlog 79k cleanup"
#    + retitle_history append: { "date": "2026-05-13", "from": "...기존...", "rationale": "MCT-162 신규 분리로 L1 채널 parity 영역 제거" }
# 3. reservations["MCT-162"] 신규 추가:
#    { "title": "L1 채널 parity — orderbookdepth schema 정의 + L1Compactor allowlist 확장", 
#      "reserved_at": "2026-05-13", "epic": "EPIC-compactor-operations", "repo": "mctrader-data", "phase_pair": "phase1_phase2",
#      "rationale": "MCT-160 brainstorm Phase 1 D1 (옵션 D, ADR-009 §D11 amendment + ADR-027 D4 amendment) — L1 채널 parity scope 분리" }
```

- [ ] **Step 5: GitHub Issue 생성 (mctrader-hub)**

```bash
gh issue create --repo mclayer/mctrader-hub \
  --title "[MCT-162] L1 채널 parity — orderbookdepth schema 정의 + L1Compactor allowlist 확장" \
  --label "type:story" \
  --body "$(cat <<'EOF'
## Story 요약

EPIC-compactor-operations 의 entrypoint Story-1. MCT-156 deploy 후 발견된 5중 차단 중 #1 (upbit L1 lost) + #4 (L1 backlog 79k orderbookdepth 48k 누적) 의 root cause 해소.

### 진단 (ResearcherAgent + Codex 합성)

- L1Compactor `_schema_version` allowlist = (`transaction`, `orderbooksnapshot`) 만. `orderbookdepth` (bithumb collector emit) → NotImplementedError 즉시 fail → 48,629 sealed 누적
- upbit collector 의 channel name 도 allowlist mismatch 가능 (sample fetch 후 verify)
- silent skip 으로 backlog 영구 증가 (분당 ~12 sealed 추가)

## 8 결정점 (brainstorm Phase 1 사용자 OK)

- **D1**: orderbookdepth = 신규 schema 정의 (옵션 D) — ADR-009 §D11 amendment
- **D7**: ADR-027 D4 amendment — channel parity 정책 + fail-fast vs silent skip + Prometheus emit obligation

(D2-D6, D8, R-EXTRA 는 MCT-160 / MCT-161 scope)

## Phase 산출물

### Phase 1 PR (Architect lane — docs only)
- \`docs/adr/ADR-009-ohlcv-schema.md\` §D11 amendment (orderbookdepth schema)
- \`docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md\` D4 amendment (channel parity + fail-fast)
- \`docs/stories/MCT-162.md\` §1-§11 신규
- \`scope_manifests/EPIC-compactor-operations.yaml\` 신규
- \`.codeforge/counters.json\` MCT-162 reservation + MCT-160 retitle

### Phase 2 PR (Developer + QA lane)
- \`mctrader-data/src/mctrader_data/compactor/l1.py\` (\`_schema_version\` + converter + fail-fast)
- \`mctrader-data/src/mctrader_data/nas_metrics/prometheus_exporters.py\` (\`compactor_unsupported_channel_total\` Counter)
- \`mctrader-data/tests/integration/test_l1_compactor_channel_parity.py\` 신규
- \`mctrader-hub/docs/stories/MCT-162.md\` §11 self-write + CLAUDE.md 갱신

## Preflight 의무 (Phase 2 진입 직전)

\`docker compose stop compactor\` — D4 박제, fix 전 read-only diagnostic mode.

## Test Contract (§8)

1. orderbookdepth converter PASS (sample WAL → parquet, schema 정합)
2. orderbookdepth 처리 시 NotImplementedError 0 (channel allowlist 정상)
3. unsupported channel (예: 가짜 \`mock_channel\`) → NotImplementedError raise (silent skip 차단 invariant)
4. unsupported channel 발생 시 Prometheus \`compactor_unsupported_channel_total{channel=mock_channel}\` Counter +1
5. parquet schema = ADR-009 §D11 amendment 박제 column count/order/dtype 정합

## Out of Scope

- L2/L3 cadence + OOM fix (MCT-160 scope)
- NAS bucket versioning (MCT-161 scope)
- MCT-153 backfill 산출물 복구 (MCT-161 scope)
- compactor 자체 stop/start (preflight only)

## Spec / Plan

- Spec: \`docs/superpowers/specs/2026-05-13-compactor-operations-design.md\`
- Plan: \`docs/superpowers/plans/2026-05-13-mct-162-l1-channel-parity.md\`

## Parent Dependency

- EPIC-compactor-operations 신규 (본 PR 의 산출물)
- Post-cycle of EPIC-cold-tier-stage-3-wiring (MCT-156 land 후 발견된 5중 차단)
EOF
)"
```

생성된 Issue 번호 기록 (예: #281 — 다음 task 의 PR body cross-link 에 사용).

- [ ] **Step 6: counters.json + chore commit + push to main**

```bash
cd c:/workspace/mclayer/mctrader-hub
git add .codeforge/counters.json docs/superpowers/specs/2026-05-13-compactor-operations-design.md docs/superpowers/plans/2026-05-13-mct-162-l1-channel-parity.md
git commit -m "$(cat <<'EOF'
chore(MCT-162): brainstorm spec + plan + counter 162 reserve + MCT-160 retitle

EPIC-compactor-operations entrypoint (post-MCT-156 deploy 5중 차단 cycle).

- .codeforge/counters.json: MCT-162 신규 reservation + MCT-160 retitle ("L2/L3 cadence + OOM + L1 backlog 79k cleanup") + retitle_history 박제
- docs/superpowers/specs/2026-05-13-compactor-operations-design.md (brainstorm Phase 0 + Codex + Sonnet 합성 결과)
- docs/superpowers/plans/2026-05-13-mct-162-l1-channel-parity.md (codeforge agent orchestration)

Issue: #281
Parent: EPIC-cold-tier-stage-3-wiring (MCT-156 land 후 cycle)
EOF
)"
git push origin main
```

---

## Task 2: Phase 1 worktree + ArchitectPLAgent dispatch

**Files:**
- Worktree: `mctrader-hub` branch `mct-162-phase1-architect`
- Modify: `docs/adr/ADR-009-ohlcv-schema.md` (§D11 amendment)
- Modify: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` (D4 amendment)
- Modify: `docs/stories/MCT-162.md` (신규, §1-§11)
- Create: `scope_manifests/EPIC-compactor-operations.yaml`

- [ ] **Step 1: GitOpsAgent dispatch — Phase 1 worktree 생성**

GitOpsAgent (codeforge-pmo) 호출:

```
Task: mctrader-hub Phase 1 worktree 생성

Branch: mct-162-phase1-architect (base: main)
Worktree path: c:/workspace/mclayer/mctrader-hub-mct162-phase1
Purpose: ADR-009 §D11 amendment + ADR-027 D4 amendment + Story file MCT-162 §1-§11 + scope_manifest 신규

memory feedback "Parallel hub session branch race" — worktree 채택.
```

- [ ] **Step 2: ArchitectPLAgent dispatch (worktree 내부)**

ArchitectPLAgent (codeforge-design) 호출. 6+2 deputy 자동 spawn:

```
Story: MCT-162 (Phase 1 PR — Architect lane)
Spec: c:/workspace/mclayer/mctrader-hub/docs/superpowers/specs/2026-05-13-compactor-operations-design.md
Worktree: c:/workspace/mclayer/mctrader-hub-mct162-phase1

## 사전 조사 의무 (deputy CodebaseMapperAgent 의무)

WAL payload sample fetch (orderbookdepth schema 추론용):
```bash
docker exec mctrader-compactor sh -c "find /var/lib/mctrader/data/wal/bithumb/orderbookdepth -name '*.ndjson.sealed' | head -1" \
  | xargs -I {} docker exec mctrader-compactor head -3 {}
```

Sample NDJSON 3줄을 ArchitectPLAgent 에 inject — ADR-009 §D11 amendment 본문 박제 source.

또한 upbit WAL payload sample 도 fetch — upbit channel name 정확 확인:
```bash
docker exec mctrader-compactor sh -c "ls /var/lib/mctrader/data/wal/upbit/" 
```

산출물 의무:

### 1. docs/stories/MCT-162.md §1-§11 신규 (codeforge Story file 표준)

- frontmatter: epic_key=EPIC-compactor-operations, parent_dependency=EPIC-cold-tier-stage-3-wiring, related_adrs=[ADR-009 amend §D11, ADR-027 amend D4]
- §1 동기: spec §0 (5중 차단 surface)
- §2 도메인 해석: L1Compactor architecture + WAL sealed lifecycle + channel SSOT
- §3 결정점 D1+D7 + AC 5종 (spec §8 Test Contract)
- §4 Change Impact Analysis (영향 파일 — Phase 2 scope)
- §5 통합 요구사항 명세 (FR-1~3 + NFR-1 + INV-1~2)
- §6 Change Plan D1-D11:
  - D1 영향 repo (mctrader-data + mctrader-hub)
  - D2 영향 파일 (l1.py + prometheus_exporters.py + test 1개 + ADR 2개 + Story + scope_manifest + counters)
  - D3 신규 모듈 (l1.py 의 converter dispatch — orderbookdepth handler)
  - D4 인터페이스 변경 (`_schema_version()` 의 channel allowlist 확장)
  - D5 호환성 (기존 transaction/orderbooksnapshot 동작 변경 0, fail-fast invariant 강화)
  - D6 마이그레이션 (NONE — 신규 channel 추가, schema 변경 0)
  - D7 트레이스 (Issue #281 → ADR amendment 2건 → EPIC-compactor-operations)
  - D8 Test Contract (spec §8 Test 5종)
  - D9 운영 risk (preflight stop 의무, ingester 운영 영향 0)
  - D10 보안 risk (NAS credential 무관 — Phase 1 docs only, Phase 2 도 read-only credential 무관)
  - D11 데이터 마이그레이션 (NONE)
- §7 deputy 산출 박제 (Mapper / Refactor / SecurityArch / TestContractArch / DataMigrationArch / OperationalRiskArch + LiveOps/LiveOrdering = SKIP)
- §8 Test Contract 5종 (위 AC 동일)
- §9 reservation marker DELETE 의무 (Phase 2 §11 land 직후)
- §10 FIX Ledger (초기 empty)
- §11 산출물 self-write 영역 (Phase 2 PMOAgent dispatch 후 작성)

### 2. docs/adr/ADR-009-ohlcv-schema.md §D11 amendment

D11 amendment trail append (기존 §D11 본문 보존, "MCT-162 amendment 박제 (2026-05-13)" 섹션 추가):

> **MCT-162 amendment 박제 (2026-05-13)** — orderbookdepth schema 정의 추가.
> 
> bithumb collector 의 `orderbookdepth` channel (WebSocket `orderbookdepth` subscribe) payload = **delta `changes` event**. transaction (trade row) + orderbooksnapshot (full snapshot row) 와 schema mismatch. 별 schema 정의 의무.
> 
> ### orderbookdepth.v1 schema (WAL → L1 parquet)
> 
> 본 amendment 의 trigger = MCT-156 deploy 후 발견된 48,629 sealed segment 의 NotImplementedError 누적. ResearcherAgent + CodebaseMapperAgent 가 WAL sample fetch 로 schema 직접 추론 (본 amendment 본문 박제 source).
> 
> **Columns** (ArchitectPLAgent 가 WAL sample 보고 정확 박제 — 예시):
> 
> | column | dtype | nullable | description |
> |--------|-------|----------|-------------|
> | ts_utc | timestamp[us, UTC] | NO | event timestamp |
> | symbol | string | NO | KRW-BTC 형식 |
> | side | string ('B'\|'S') | NO | bid/ask |
> | price | decimal128(38,18) | NO | level price |
> | qty | decimal128(38,18) | NO | level qty (0 = delete) |
> | node_id | string | NO | collector node |
> | collector_run_id | string | NO | run identifier |
> | ingest_seq | int64 | NO | monotonic seq |
> | validation_status | string | NO | 'OK' \| 'GAP' \| 'MALFORMED' |
> 
> (실 schema 는 WAL sample 보고 ArchitectPLAgent 가 정정 박제 의무)
> 
> **Partition path**: `market/orderbookdepth/schema_version=orderbook_depth.v1/tier=L1/exchange={ex}/symbol={sym}/date={YYYY-MM-DD}/node={node_id}/part-{run_id}.parquet`
> 
> **L2 compaction**: ADR-027 D4 amendment 정합 — DualWriter 통해 NAS dual-write. L3 = 1 day aggregate.

### 3. docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md D4 amendment append

D4 amendment trail append:

> **MCT-162 amendment 박제 (2026-05-13)** — channel parity 정책 + fail-fast invariant.
> 
> L1Compactor 의 channel allowlist (`_schema_version()` dispatch) 가 silent skip 되면 backlog 영구 누적 (MCT-156 deploy 후 orderbookdepth 48,629 sealed 누적 사례). channel parity 정책 박제:
> 
> 1. **모든 collector emit channel 은 L1/L2/L3 layer parity 의무** — 신규 channel 추가 시 ADR-009 §D11 (또는 §D10 / §D14 등) amendment + L1Compactor converter 동시 land 의무.
> 2. **Unsupported channel = fail-fast** — `NotImplementedError` raise + Prometheus counter `compactor_unsupported_channel_total{channel}` emit. silent skip 금지.
> 3. **신규 channel 추가 절차**: (a) ADR-009 schema 정의 amendment → (b) L1Compactor converter dispatch 추가 → (c) integration test (channel parity verify) 의무.

### 4. scope_manifests/EPIC-compactor-operations.yaml 신규

spec §8 의 scope_manifest 초안 그대로 박제.

### 5. `.codeforge/counters.json` MCT-160 retitle + MCT-162 신규 reservation (Task 1 Step 4 에서 main 박제 후, worktree 에서 fetch only — 별 변경 0)

## Deputy 6+2 dispatch

자동 spawn 의무:
- **CodebaseMapperAgent**: WAL sample fetch + L1Compactor 영향 매핑 + Story §6 D2 박제
- **RefactorAgent**: `_schema_version()` dispatch pattern + converter handler dispatch
- **SecurityArchitectAgent**: NAS credential 무관 (Phase 2 read-only) but Prometheus counter cardinality (channel 명 무한 증가 risk)
- **TestContractArchitectAgent**: §8 Test Contract 5종 + fail-fast invariant (silent skip 차단) verify
- **DataMigrationArchitectAgent**: D11=NONE 변호 (신규 channel 추가, 기존 schema 변경 0)
- **OperationalRiskArchitectAgent**: preflight stop 의무 + backlog drainage 측정
- **LiveOpsDeputyAgent**: SKIP
- **LiveOrderingDeputyAgent**: SKIP

산출 후 worktree 내부 `git add` + `git commit` + 보고 (Story file path + ADR amendment 위치 + scope_manifest path + deputy 산출 요약).
```

- [ ] **Step 3: DesignReviewPLAgent dispatch (Phase 1 PR 직전)**

DesignReviewPLAgent (codeforge-review) 호출:

```
Story: MCT-162 Phase 1 PR design review
Worktree: c:/workspace/mclayer/mctrader-hub-mct162-phase1
Target: docs/adr/ADR-009 §D11 amendment + docs/adr/ADR-027 D4 amendment + Story §1-§11 + scope_manifests/EPIC-compactor-operations.yaml

Lane: 설계리뷰 (Change Plan 품질 게이트)
Peer reviewers: ClaudeReviewAgent + CodexReviewAgent

집중 검토:
1. ADR-009 §D11 amendment 본문 — WAL sample 정합 (CodebaseMapperAgent fetch 결과 vs schema column 일치)
2. ADR-027 D4 amendment — channel parity 정책 + fail-fast 박제 정합
3. Story §6 D11=NONE 변호 (schema 신규 추가, 기존 schema 변경 0)
4. spec §8 8 결정점 (D1+D7 만 본 Story scope, D2-D6 + D8 + R-EXTRA 는 MCT-160/161 별 Story 정합)
5. preflight stop 의무 박제 (D4) 정합
```

PASS 시 PR 생성, FAIL 시 ArchitectPLAgent FIX iteration.

- [ ] **Step 4: Phase 1 PR 생성**

```bash
cd c:/workspace/mclayer/mctrader-hub-mct162-phase1
gh pr create --repo mclayer/mctrader-hub --base main --head mct-162-phase1-architect \
  --title "[MCT-162] Phase 1 — ADR-009 §D11 + ADR-027 D4 amendment + L1 channel parity Story + epic manifest" \
  --body "$(cat <<'EOF'
## Summary

EPIC-compactor-operations entrypoint Phase 1 PR (Architect lane, docs only).

- \`docs/adr/ADR-009-ohlcv-schema.md\` §D11 amendment — orderbookdepth schema 정의 (WAL delta changes payload)
- \`docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md\` D4 amendment — channel parity 정책 + fail-fast vs silent skip + Prometheus emit obligation
- \`docs/stories/MCT-162.md\` §1-§11 신규
- \`scope_manifests/EPIC-compactor-operations.yaml\` 신규 (epic 의 첫 PR 에서 land)

## 8 결정점 (사용자 OK 2026-05-13, brainstorm Phase 1)

- D1 (옵션 D): orderbookdepth 신규 schema 정의 ✅
- D7 (옵션 A): ADR-027 D4 amendment ✅
- (D2-D6, D8, R-EXTRA 는 MCT-160 / MCT-161)

## DesignReview

DesignReviewPLAgent verdict: PASS
- Codex GPT-5 review D1=D + D7=A ↔ 최종 산출 cross-validation
- WAL sample fetch 결과 ↔ ADR-009 §D11 schema 정합 (CodebaseMapperAgent 산출)
- 6 deputy + 2 SKIP 산출 통합 정합

## Closes

#281 (Phase 1)

## Parent

- EPIC-compactor-operations (신규, 본 PR 의 첫 manifest)
- Post-cycle of EPIC-cold-tier-stage-3-wiring (#280 hub Phase 2 MERGED)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 5: Phase 1 PR 라벨 + CI watch + admin merge**

```bash
PR_NUMBER=$(gh pr list --repo mclayer/mctrader-hub --head mct-162-phase1-architect --json number --jq '.[0].number')
gh pr edit $PR_NUMBER --repo mclayer/mctrader-hub --add-label "phase:설계-리뷰,gate:design-review-pass,type:story"
gh pr checks $PR_NUMBER --repo mclayer/mctrader-hub --watch
```

- SUCCESS → 즉시 `gh pr merge $PR_NUMBER --repo mclayer/mctrader-hub --admin --squash --delete-branch`
- FAILURE / ACTION_REQUIRED → 자동 fix→push→re-watch cycle (memory: "CI failure auto-recovery")

- [ ] **Step 6: Worktree cleanup**

GitOpsAgent dispatch — Phase 1 worktree 삭제.

---

## Task 3: Preflight stop + Phase 2 worktree (2 repo) + DeveloperPL/QADev parallel

**Files:**
- Worktree 1: `mctrader-data` branch `mct-162-phase2-dev`
- Worktree 2: `mctrader-hub` branch `mct-162-phase2-docs`
- Modify: `src/mctrader_data/compactor/l1.py`
- Modify: `src/mctrader_data/nas_metrics/prometheus_exporters.py`
- Create: `tests/integration/test_l1_compactor_channel_parity.py`
- Modify (hub): `docs/stories/MCT-162.md` §11 + `CLAUDE.md` + scope_manifest milestone

- [ ] **Step 1: Preflight stop — D4 박제**

```bash
cd c:/workspace/mclayer/mctrader-data
docker compose stop compactor
docker compose ps compactor
```

기대 출력: `mctrader-compactor   STATE: exited`. read-only diagnostic mode 진입. ingester (bithumb-ingester, upbit-ingester) 는 정상 운영 (WAL 누적 계속, hot path zero-loss invariant 유지).

- [ ] **Step 2: GitOpsAgent dispatch — Phase 2 worktree 2건 생성**

```
Task: MCT-162 Phase 2 worktree 2건 동시 생성

repo 1: mctrader-data
  branch: mct-162-phase2-dev
  base: main (mctrader-data 의 latest main, Phase 1 hub PR merge 와 무관)
  worktree: c:/workspace/mclayer/mctrader-data-mct162-phase2

repo 2: mctrader-hub
  branch: mct-162-phase2-docs
  base: main (Phase 1 PR merge 반영 후 latest)
  worktree: c:/workspace/mclayer/mctrader-hub-mct162-phase2
```

- [ ] **Step 3: DeveloperPLAgent dispatch (mctrader-data worktree)**

DeveloperPLAgent (codeforge-develop) 호출. dynamic roster: DeveloperAgent primary:

```
Story: MCT-162 Phase 2 PR (구현 lane)
Worktree: c:/workspace/mclayer/mctrader-data-mct162-phase2
Change Plan source: mctrader-hub#281 Phase 1 PR merged Story §6 + ADR-009 §D11 amendment + ADR-027 D4 amendment

산출 의무:

### 변경 1: src/mctrader_data/compactor/l1.py — `_schema_version` 확장 + converter dispatch + fail-fast

현재 코드 (예상 line 51-60):
```python
def _schema_version(channel: str) -> str:
    if channel == "transaction":
        return "tick.v1"
    if channel == "orderbooksnapshot":
        return "orderbook_snapshot.v1"
    raise NotImplementedError(
        f"_schema_version: channel '{channel}' not supported. "
        f"Supported: 'transaction', 'orderbooksnapshot'."
    )
```

신규 (MCT-162 amendment 정합):
```python
# Allowlist — ADR-009 §D11 amendment 정합 (MCT-162, 2026-05-13)
_CHANNEL_SCHEMA_VERSION: dict[str, str] = {
    "transaction": "tick.v1",
    "orderbooksnapshot": "orderbook_snapshot.v1",
    "orderbookdepth": "orderbook_depth.v1",  # MCT-162 신규
}


def _schema_version(channel: str) -> str:
    """MCT-162: channel parity 정책 (ADR-027 D4 amendment).
    
    fail-fast invariant: unsupported channel → NotImplementedError raise
    + Prometheus counter `compactor_unsupported_channel_total{channel}` emit.
    """
    if channel not in _CHANNEL_SCHEMA_VERSION:
        from mctrader_data.nas_metrics.prometheus_exporters import compactor_unsupported_channel_total
        compactor_unsupported_channel_total.labels(channel=channel).inc()
        raise NotImplementedError(
            f"_schema_version: channel '{channel}' not supported. "
            f"Supported: {sorted(_CHANNEL_SCHEMA_VERSION.keys())}. "
            f"ADR-009 §D11 amendment + ADR-027 D4 channel parity 정책 정합."
        )
    return _CHANNEL_SCHEMA_VERSION[channel]
```

또한 `compact_segment` 의 path derive 가 orderbookdepth 정합 처리되도록 (path schema = ADR-009 §D11 amendment 박제):

```python
# orderbookdepth 의 converter — WAL delta `changes` payload → pyarrow Table
def _convert_orderbookdepth_ndjson_to_arrow(rows: list[dict]) -> pa.Table:
    """MCT-162: orderbookdepth WAL → L1 parquet converter.
    
    schema = ADR-009 §D11 amendment (MCT-162) 박제:
    ts_utc, symbol, side, price (decimal128(38,18)), qty (decimal128(38,18)),
    node_id, collector_run_id, ingest_seq, validation_status
    """
    # 실 schema = ArchitectPLAgent 의 ADR amendment 본문 박제 그대로
    # (sample WAL 보고 정확 column 박제)
    ...
```

(정확한 converter 본문 = ArchitectPLAgent 의 ADR-009 §D11 amendment 박제 schema 그대로 구현)

### 변경 2: src/mctrader_data/nas_metrics/prometheus_exporters.py — Counter 신규

```python
compactor_unsupported_channel_total = Counter(
    "mctrader_compactor_unsupported_channel_total",
    "L1Compactor unsupported channel encountered (MCT-162 fail-fast)",
    ["channel"],  # cardinality risk: collector emit channel 종류만 (low)
)
```

### 변경 의무

- 기존 transaction/orderbooksnapshot 동작 변경 0 — 회귀 테스트 PASS 의무 (test_compactor_l1.py / test_compactor_l2.py / test_compactor_l3.py 기존 test ALL PASS 검증)
- ADR-009 §D11 amendment 의 schema column 정합 (CodebaseMapperAgent 의 WAL sample 보고 정확 박제)

QADeveloperAgent 별 dispatch (tests/integration/test_l1_compactor_channel_parity.py).
```

- [ ] **Step 4: QADeveloperAgent dispatch — test 작성**

QADeveloperAgent (codeforge-develop) 호출:

```
Story: MCT-162 Phase 2 PR (QADev lane)
Worktree: c:/workspace/mclayer/mctrader-data-mct162-phase2 (DevPL 와 동일, src/ vs tests/ file disjoint)

신규 file: tests/integration/test_l1_compactor_channel_parity.py

산출 의무 (Story §8 Test Contract 5종 ALL 구현):

1. test_orderbookdepth_converter_passes — sample WAL (3 line NDJSON) → compact_segment → L1 parquet 생성. schema 정합 verify (column count/order/dtype).
2. test_orderbookdepth_no_notimplementederror — `_schema_version("orderbookdepth")` → return "orderbook_depth.v1" (NotImplementedError raise 0).
3. test_unsupported_channel_fail_fast — `_schema_version("mock_unsupported")` → NotImplementedError raise (silent skip 차단 invariant).
4. test_unsupported_channel_prometheus_emit — `_schema_version("mock_unsupported")` 호출 시 `compactor_unsupported_channel_total{channel="mock_unsupported"}` Counter +1 (호출 전 0 → 호출 후 1).
5. test_orderbookdepth_parquet_schema_adr_009_d11 — 생성된 L1 parquet 의 pyarrow.Schema 가 ADR-009 §D11 amendment 박제 column 정확 일치.

test fixture: sample WAL NDJSON (실 production WAL 1 segment 의 sealed file 또는 inline NDJSON string).

pytest 실 실행 + PASS 검증 의무 (RED → impl → GREEN cycle).
```

- [ ] **Step 5: TestAgent dispatch — 실 pytest 실행 게이트**

TestAgent (codeforge-test) 호출:

```
Worktree: c:/workspace/mclayer/mctrader-data-mct162-phase2

Functional: pytest tests/integration/test_l1_compactor_channel_parity.py -v --tb=short
Regression: pytest tests/ -v --tb=line | tail -50  (기존 회귀 0 확인 — 특히 test_compactor_l1.py / test_runner_minio.py 류)

기대: 5 PASS / 0 FAIL / 0 SKIP. Phase 2 new regression 0.

FAIL 시 root-cause-decision + Story §10 FIX Ledger append + DevPL FIX iteration.
```

- [ ] **Step 6: SecurityTestPLAgent + CodeReviewPLAgent parallel dispatch**

```
SecurityTestPL: NAS credential 무관, Prometheus counter cardinality 검토 (channel 명 cardinality 폭증 risk — collector emit channel 종류만 = low cardinality 정합)
CodeReviewPL: §6 Change Plan ↔ 실 코드 1:1 정합, fail-fast invariant 정확 구현 (silent skip 차단), Counter cardinality risk
```

- [ ] **Step 7: hub Phase 2 worktree — Story §11 self-write + CLAUDE.md**

mctrader-hub Phase 2 worktree (c:/workspace/mclayer/mctrader-hub-mct162-phase2):

- `docs/stories/MCT-162.md` §11 산출물 self-write (Phase 2 PR cross-link: mctrader-data#XXX + hub#XXX)
- `CLAUDE.md` 신규 sub-section: "EPIC-compactor-operations Stage 3 wiring 후속" (Story-1 LAND 1/3, channel allowlist + fail-fast invariant 박제)
- `scope_manifests/EPIC-compactor-operations.yaml` milestone update (MCT-162 COMPLETED)
- `.codeforge/counters.json` reservations.MCT-162 DELETE (§9 박제 정합)

- [ ] **Step 8: Phase 2 PR 2건 생성**

mctrader-data Phase 2 PR:

```bash
cd c:/workspace/mclayer/mctrader-data-mct162-phase2
gh pr create --repo mclayer/mctrader-data --base main --head mct-162-phase2-dev \
  --title "[MCT-162] Phase 2 — L1Compactor orderbookdepth channel parity + fail-fast" \
  --body "$(cat <<'EOF'
## Summary

EPIC-compactor-operations Story-1 Phase 2 PR (Developer + QA lane).

ADR-009 §D11 amendment + ADR-027 D4 amendment (mctrader-hub#281 MERGED) 정합.

### 변경
- src/mctrader_data/compactor/l1.py: \`_schema_version\` 확장 (orderbookdepth) + converter dispatch + fail-fast invariant (silent skip 차단 + Prometheus emit)
- src/mctrader_data/nas_metrics/prometheus_exporters.py: \`compactor_unsupported_channel_total{channel}\` Counter 신규
- tests/integration/test_l1_compactor_channel_parity.py: 5 integration test (orderbookdepth converter + fail-fast + Prometheus emit + schema 정합)

## Review verdict 종합

- DesignReview (Phase 1 land, hub#281): PASS
- TestAgent: 5/5 PASS + Phase 2 new regression 0
- SecurityTestPL: PASS (Prometheus cardinality 검토 OK)
- CodeReviewPL: PASS (§6 Change Plan ↔ 실 코드 1:1 정합)

## Closes

mctrader-hub#281 (Phase 2)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

mctrader-hub Phase 2 PR:

```bash
cd c:/workspace/mclayer/mctrader-hub-mct162-phase2
gh pr create --repo mclayer/mctrader-hub --base main --head mct-162-phase2-docs \
  --title "[MCT-162] Phase 2 — Story §11 self-write + CLAUDE.md + scope_manifest 1/3 + counters DELETE" \
  --body "$(cat <<'EOF'
## Summary
- docs/stories/MCT-162.md §11 self-write (mctrader-data#XXX Phase 2 PR cross-link)
- CLAUDE.md "EPIC-compactor-operations Stage 3 wiring 후속" 섹션 신규
- scope_manifests/EPIC-compactor-operations.yaml milestone 1/3 (MCT-162 COMPLETED)
- .codeforge/counters.json reservations.MCT-162 DELETE (§9 박제 정합)

## Closes
#281 (Phase 2)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 9: CI watch + admin merge (2 PR sequential)**

mctrader-data 먼저 merge → mctrader-hub merge (cross-link 정합).

```bash
DATA_PR=$(gh pr list --repo mclayer/mctrader-data --head mct-162-phase2-dev --json number --jq '.[0].number')
gh pr edit $DATA_PR --repo mclayer/mctrader-data --add-label "phase:보안-테스트,gate:security-test-pass"
gh pr checks $DATA_PR --repo mclayer/mctrader-data --watch
gh pr merge $DATA_PR --repo mclayer/mctrader-data --admin --squash --delete-branch

HUB_PR=$(gh pr list --repo mclayer/mctrader-hub --head mct-162-phase2-docs --json number --jq '.[0].number')
gh pr edit $HUB_PR --repo mclayer/mctrader-hub --add-label "phase:설계-리뷰,gate:design-review-pass,type:story"
gh pr checks $HUB_PR --repo mclayer/mctrader-hub --watch
gh pr merge $HUB_PR --repo mclayer/mctrader-hub --admin --squash --delete-branch
```

- [ ] **Step 10: compactor 재시작 + L1 backlog drainage 모니터링**

Phase 2 merge 후 compactor 재시작:

```bash
cd c:/workspace/mclayer/mctrader-data
git fetch origin main && git pull origin main
docker compose build compactor
docker compose up -d compactor
sleep 30
docker logs mctrader-compactor 2>&1 | head -10
```

기대 출력: `[INFO] NAS dual-write enabled` + `[INFO] L1 compacted ... orderbookdepth ...` (NotImplementedError 0).

drainage 측정 (10분 후):
```bash
docker exec mctrader-compactor sh -c "find /var/lib/mctrader/data/wal -name '*.ndjson.sealed' | wc -l"
```

기대: 79,427 → 빠르게 감소 (orderbookdepth 48k = 정상 처리되므로 backlog 가 ingester 속도만 따라가는 수준으로 회복).

---

## Task 4: PMOAgent retro dispatch

**Files:**
- Create: `mctrader-hub/docs/retros/RETRO-MCT-162.md`
- Modify: `mctrader-hub/docs/stories/MCT-162.md` §12 (PMOAgent self-write)
- Modify: `mctrader-hub/scope_manifests/EPIC-compactor-operations.yaml` (milestone 1/3)

- [ ] **Step 1: PMOAgent dispatch**

```
Task: MCT-162 retro

Story: MCT-162 (Phase 1 + Phase 2 ALL MERGED)
Phase 1 PR: mctrader-hub#281
Phase 2 PR: mctrader-data#XXX + mctrader-hub#XXX

산출 의무:
1. docs/retros/RETRO-MCT-162.md 신규 작성:
   - 시작/종료 timestamp
   - 8 결정점 (D1+D7 본 Story scope) ↔ 실제 구현 정합 검증
   - Codex GPT-5 D1=D 권고 ↔ 실 ADR-009 §D11 amendment 정합
   - FIX iteration 발생 시 root-cause + fix-ledger §10 발췌
   - L1 backlog drainage 측정 (재시작 후 10분/1시간/24시간 backlog 추이 박제)
   - Cross-Story patterns: post-MCT-156 deploy 5중 차단 surface → MCT-162 land (1차 fix), MCT-160/161 잔여
2. docs/stories/MCT-162.md §12 self-write
3. scope_manifests/EPIC-compactor-operations.yaml milestone 1/3 박제 (MCT-162 COMPLETED, MCT-160/161 pending)
4. Cross-Story 패턴 누적 박제 (PMO ledger)
5. ADR 후보 발의 판정 (있으면)
```

---

## Task 5: 다음 Story (MCT-160) 진입 준비

- [ ] **Step 1: MCT-160 GitHub Issue + Story file scaffold**

MCT-160 = Story-2 (L2/L3 cadence + OOM + L1 backlog 79k cleanup, MCT-162 land 후 sequential 진입).

별 plan 발의:
- docs/superpowers/plans/2026-05-14-mct-160-l2-cadence-oom-cleanup.md (Task 5 본 plan 의 종료 시 작성)

- [ ] **Step 2: MCT-160 진입 조건 확인**

```bash
# 1. MCT-162 PR MERGED + ADR amendment 2건 LAND verify
gh pr view 281 --repo mclayer/mctrader-hub --json state | jq -r '.state'
# 기대: MERGED

# 2. L1 backlog 측정 (drainage 진척)
docker exec mctrader-compactor sh -c "find /var/lib/mctrader/data/wal -name '*.ndjson.sealed' | wc -l"
# 기대: 79,427 → 감소 추이 (구체적 임계는 R2 mitigation 정합)

# 3. compactor 정상 운영 확인 (orderbookdepth NotImplementedError 0)
docker logs mctrader-compactor --since 10m 2>&1 | grep -c "NotImplementedError"
# 기대: 0
```

- [ ] **Step 3: spec milestone 갱신 (MCT-162 COMPLETED)**

```bash
# scope_manifests/EPIC-compactor-operations.yaml milestone:
# - MCT-162: COMPLETED (date, PR links, L1 backlog drainage 결과)
# - MCT-160: PROPOSED → IN_PROGRESS (다음 cycle)
# - MCT-161: PROPOSED
```

---

## Self-Review

**1. Spec coverage check:**
- ✅ D1 (orderbookdepth 신규 schema) → Task 2 ArchitectPL ADR-009 §D11 amendment + Task 3 변경 1 converter
- ✅ D4 (preflight stop) → Task 3 Step 1
- ✅ D7 (ADR-027 D4 amendment) → Task 2 ArchitectPL
- ✅ Test Contract 5 (Story §8) → Task 3 Step 4 QADev
- ✅ counters.json + scope_manifest 신규 + Story file → Task 1, Task 2
- ✅ Phase 1 docs only + Phase 2 code + hub docs cross-link → Task 2/3 split
- ✅ PMOAgent retro → Task 4
- ✅ 다음 Story MCT-160 진입 준비 → Task 5
- (out of scope, MCT-160/161): D2/D3/D5/D6/D8/R-EXTRA — 별 plan 발의 시점에

**2. Placeholder scan:** 없음 — 모든 env / 파일 / 함수 / test 명 명시. ArchitectPLAgent 의 정확 ADR amendment 본문 박제 = WAL sample 보고 정확 schema 박제 (Task 2 Step 2 의무).

**3. Type consistency:**
- `_schema_version(channel: str) → str` — Story §6 + 변경 1 + test 통일
- `_CHANNEL_SCHEMA_VERSION: dict[str, str]` — 변경 1 박제 + ADR-009 §D11 amendment 본문 정합
- `compactor_unsupported_channel_total` Counter (label: `channel`) — 변경 2 + test 4 통일
- `orderbookdepth` channel name — ADR-009 §D11 amendment + 변경 1 + WAL collector emit name (mismatch 시 collector 측 별 fix Story 필요 — spec §1 root cause 1 정합)

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-mct-162-l1-channel-parity.md`. Two execution options:

1. **Subagent-Driven (recommended)** — codeforge agent 표준 (GitOpsAgent / ArchitectPLAgent / DeveloperPLAgent / QADeveloperAgent / TestAgent / SecurityTestPLAgent / CodeReviewPLAgent / PMOAgent dispatch). MCT-156 plan pattern 답습.

2. **Inline Execution** — 직접 코드 작성 (codeforge agent dispatch 우회). memory: "Always subagent-driven execution" 박제 → 비권고.

Which approach?
