---
story_key: MCT-181
plan_title: "image registry pin (${IMAGE_TAG}) + backtest artifact NAS sync + Epic POLICY_FINALIZED"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 7
depends_on: MCT-180 (LAND 2026-05-15, hub#342+#343+#344 + data#67 + engine#55)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D12, D19]
epic_close: true
carry_over_from_mct180:
  - "${IMAGE_TAG} D12 image registry pin (MCT-181 owner — 본 Story)"
  - "full-stack production smoke (D11 ESCALATE Layer 3 — D12 image pin 후 production deploy carry)"
  - "R2 CRITICAL production 측정 (EPIC-tier-promotion prod-2, 별 PR)"
  - "engine#55 ci/lookahead-lint mctrader-market-upbit private-dep token (engine repo 자체 CI infra, 별 처리)"
---

# MCT-181 Implementation Plan — image registry pin + backtest NAS sync + Epic CLOSE

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** D12 (image registry pin — semver + sha + latest, prod = pin / dev = latest) + D19 (backtest-runner artifact NAS sync on completion) + EPIC-mctrader-docker-stack **POLICY_FINALIZED** 박제 (7/7 milestone). carry over 4건 정합 (D11 full-stack production smoke = D12 image pin 후 가능 명시).

**Architecture:**
- **D12 image registry pin**: compose.yml 의 `image: ghcr.io/mclayer/mctrader-{data,engine,signal-collector}:latest` → `${IMAGE_TAG:-latest}` 변수화. prod profile = release tag (vX.Y.Z) 또는 git sha pin / dev profile = latest. `.env.prod.example` 에 `IMAGE_TAG=<release_or_sha>` + `.env.dev` 에 `IMAGE_TAG=latest`. GitHub Actions `.github/workflows/image-publish.yml` 신규 — main push 시 ghcr.io 에 `:latest` + `:sha-<commit>` + (release tag 시 `:vX.Y.Z`) push (data/engine/signal-collector 3 repo, mctrader-hub orchestrates 또는 각 repo 자체 workflow).
- **D19 backtest artifact NAS sync**: backtest-runner 의 `MCTRADER_OUTPUT_DIR=/var/lib/mctrader/runs` 결과를 완료 후 NAS bucket `mctrader-backtest-runs` 별 prefix sync. completion marker (`.done` sentinel) + retry policy (NAS sync 실패 시 local 보존 + 재시도). mctrader-engine 측 backtest CLI 종료 hook 또는 hub 측 sync script.
- **Epic POLICY_FINALIZED**: scope_manifest milestone 7/7 + Epic status POLICY_FINALIZED (EPIC-tier-promotion-single-source 패턴 정합 — Epic CLOSED 자체는 production evidence 완성 후 별 PR). EPIC-RESULTS 7 Story 종합 + 19 D 결정 verify 매트릭스 + carry over registry (production smoke + R2 + ${IMAGE_TAG} prod 적용 + engine CI token).

**Tech Stack:** Docker Compose v2 (${IMAGE_TAG} variable) / GitHub Actions (image-publish, ghcr.io) / Python 3.12 (backtest NAS sync) / mctrader-data nas_uploader (MCT-163 put_streaming)

**PR Split:**
- **Phase 1 PR** (hub, docs): Story + ADR-030 §D12/§D19 amendment + Epic CLOSE 박제 준비 + CLAUDE.md
- **Phase 2 PR1** (cross-repo: hub + engine):
  - **hub PR**: compose.yml ${IMAGE_TAG} 변수화 + .env.dev/.env.prod.example IMAGE_TAG + .github/workflows/image-publish.yml
  - **engine PR**: backtest CLI 완료 hook NAS artifact sync (mctrader-engine, nas_uploader 재사용) + completion marker + retry + test
- **Phase 2 PR2** (hub, 박제): Story §11 retro + §12 측정 + Epic POLICY_FINALIZED + EPIC-RESULTS 7/7 종합 + RETRO-MCT-181 + carry over registry

---

## §1 Phase 1 PR (hub, docs only)

### 1.1 Story MCT-181.md

**Files:** Create `docs/stories/MCT-181.md`

- [ ] §1-§6: 동기 / Epic context (sequential_phase 7, Epic CLOSE) / Risk acceptance / AC 5 / INV / Risk
  - AC-1 (D12): compose.yml `image: ghcr.io/mclayer/mctrader-{data,engine,signal-collector}:${IMAGE_TAG:-latest}` 변수화 + `docker compose --profile dev/prod config` exit 0 (dev=latest / prod=pin)
  - AC-2 (D12): `.github/workflows/image-publish.yml` main push 시 ghcr.io :latest + :sha-<commit> push verify (workflow_dispatch dry-run)
  - AC-3 (D19): backtest-runner 완료 후 `mctrader-backtest-runs` NAS prefix sync + completion marker (.done) + NAS sync 실패 시 local 보존 retry
  - AC-4 (D11 carry): full-stack production smoke = D12 image pin LAND 후 가능 명시 (production deploy carry, CI 격리 불가 재확인)
  - AC-5 (Epic CLOSE): EPIC-mctrader-docker-stack 7/7 milestone + POLICY_FINALIZED + 19 D verify 매트릭스 + carry over registry (production smoke + R2 + engine CI token)

- [ ] §6.5 Change Plan §7/§11 N/A 박제
  - §7 security: ghcr.io image push = GITHUB_TOKEN (per-repo) / NAS backtest sync = 기존 NAS_MINIO_* credential. 신규 trust boundary 없음.
  - §7.4 op-risk: image pin 누락 시 dev=latest 폴백 (안전). backtest NAS sync 실패 = local 보존 retry (데이터 손실 0).
  - §11 data-migration: backtest artifact = 신규 NAS prefix `mctrader-backtest-runs` (기존 market data prefix 무관, ADR-029 market data SoT 충돌 없음). schema 변경 없음.
  - §11.6 idempotency: image push = idempotent (동일 sha 재push = no-op). backtest NAS sync = completion marker (.done) 로 재실행 idempotent (이미 sync 시 skip).

- [ ] §7-§12: Dependencies (MCT-176~180 LAND) / Test contract / Plan ref / FIX Ledger 빈 표 / Retro placeholder
- [ ] §7 Epic CLOSE carry over registry: production full-stack smoke + R2 production 측정 + engine#55 CI token + ${IMAGE_TAG} prod 실 적용 (production deploy 시점)

### 1.2 ADR-030 amendment + Epic CLOSE 준비

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] §D12 amendment box (MCT-181): image registry pin (${IMAGE_TAG} 변수 + prod release/sha pin + dev latest + image-publish.yml). D11 ESCALATE Layer 3 (full-stack production smoke) = D12 image pin 후 가능 명시
- [ ] §D19 amendment box (MCT-181): backtest artifact NAS sync (mctrader-backtest-runs prefix + completion marker + retry, ADR-029 market data SoT 무충돌)
- [ ] §References Plan(MCT-181)
- [ ] ADR-030 Status: Accepted → Accepted (Epic POLICY_FINALIZED 박제는 Phase 2 PR2)

### 1.3 CLAUDE.md + scope_manifest + counters
- [ ] 7 Story chain MCT-181 IN_PROGRESS + §MCT-181 IN_PROGRESS 섹션 (Epic CLOSE owner)
- [ ] scope_manifest MCT-181 IN_PROGRESS + started_date
- [ ] counters.json MCT-180 COMPLETED + MCT-181 IN_PROGRESS

### 1.4 plan git add (MCT-176 P0 lesson)

### 1.5 Phase 1 Gate
- [ ] DesignReviewPL + iter PASS + admin merge

---

## §2 Phase 2 PR1 (cross-repo: hub + engine, code)

### 2.1 mctrader-hub PR

**Files:**
- Modify: `compose.yml` (image ${IMAGE_TAG:-latest} 변수화 — data/engine/signal-collector 5종)
- Modify: `.env.dev` (IMAGE_TAG=latest) / `.env.prod.example` (IMAGE_TAG=<release_or_sha>)
- Create: `.github/workflows/image-publish.yml`

- [ ] compose.yml image 변수화:

```yaml
# collector
image: ghcr.io/mclayer/mctrader-data:${IMAGE_TAG:-latest}
# paper-engine + backtest-runner
image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
# signal-collector 5종
image: ghcr.io/mclayer/mctrader-signal-collector:${IMAGE_TAG:-latest}
```

- [ ] .env.dev: `IMAGE_TAG=latest` / .env.prod.example: `IMAGE_TAG=<release_tag_or_git_sha>` (주석: prod = release vX.Y.Z 또는 sha-<commit> pin 의무)

- [ ] image-publish.yml:

```yaml
name: image-publish
on:
  push:
    branches: [main]
  workflow_dispatch:
jobs:
  publish:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo: [mctrader-data, mctrader-engine, mctrader-signal-collector]
    steps:
      - uses: actions/checkout@v4
        with:
          repository: mclayer/${{ matrix.repo }}
          token: ${{ secrets.MCTRADER_CROSS_REPO_TOKEN }}
      - name: ghcr login
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - name: build + push
        run: |
          SHA_TAG="sha-$(git rev-parse --short HEAD)"
          docker build -t ghcr.io/mclayer/${{ matrix.repo }}:latest -t ghcr.io/mclayer/${{ matrix.repo }}:${SHA_TAG} .
          docker push ghcr.io/mclayer/${{ matrix.repo }}:latest
          docker push ghcr.io/mclayer/${{ matrix.repo }}:${SHA_TAG}
```

### 2.2 mctrader-engine PR

**Files:**
- Modify: backtest CLI 완료 hook — NAS artifact sync (nas_uploader MCT-163 put_streaming 재사용)
- Create: `tests/test_backtest_nas_sync.py`

- [ ] Phase 0 verify: mctrader-engine backtest CLI 종료 경로 + MCTRADER_OUTPUT_DIR + nas_uploader API (MCT-163 put_streaming) 실 구조 read
- [ ] backtest 완료 후: `/var/lib/mctrader/runs/<run_id>/` → NAS `mctrader-backtest-runs/<run_id>/` sync. completion marker `<run_id>/.done` sentinel. NAS sync 실패 시 local 보존 + log warn + exit 0 (backtest 결과 자체는 성공, sync 는 best-effort retry)
- [ ] 신규 test: backtest NAS sync (mock nas_uploader) + completion marker + sync 실패 시 local 보존 verify

### 2.3 cross-repo LAND 순서
1. engine PR LAND 먼저 (backtest NAS sync)
2. hub PR LAND (compose ${IMAGE_TAG} + image-publish.yml)

### 2.4 Gate
- AC-1~5 verify + CodeReviewPL 2-way + admin merge

---

## §3 Phase 2 PR2 (hub, 박제 + Epic POLICY_FINALIZED)

- [ ] Story §10 FIX Ledger + §11 retro + §12 측정 (AC-1~5 PASS + cross-repo LAND) + status COMPLETED
- [ ] ADR-030 §D12/§D19 amendment LAND confirm
- [ ] scope_manifest milestone 6/7 → **7/7** + Epic status: phase:요구사항-PLANNED → **POLICY_FINALIZED**
- [ ] CLAUDE.md MCT-181 COMPLETED + §EPIC-mctrader-docker-stack POLICY_FINALIZED 박제 (7 Story 종합 + 19 D verify + carry over registry)
- [ ] docs/retros/RETRO-MCT-181.md (PMOAgent)
- [ ] docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md — §Story-7 + Epic POLICY_FINALIZED 종합 (7 Story timeline + 19 D 결정 매트릭스 + FIX 통계 + Phase 0 verify lesson 6회 + ESCALATE 1회 + carry over registry: production smoke / R2 production / engine CI token / Epic CLOSED 별 PR)
- [ ] Epic CLOSED prerequisite (post-POLICY_FINALIZED carry over, 별 PR/Story 의무):
  - prod-1: ${IMAGE_TAG} prod 실 적용 (production deploy 시 release/sha pin)
  - prod-2: full-stack production smoke (collector+paper-engine compose up evidence, D11 ESCALATE Layer 3)
  - prod-3: R2 CRITICAL WAL 30G production 측정 (EPIC-tier-promotion prod-2 cross-Epic)
  - prod-4: Epic CLOSED 박제 PR (POLICY_FINALIZED → CLOSED, production evidence 완성 후)

---

## §4 Epic 완료

MCT-181 COMPLETED → **EPIC-mctrader-docker-stack POLICY_FINALIZED (7/7)**. Epic CLOSED = production evidence 완성 후 별 PR (EPIC-tier-promotion-single-source 패턴 정합).

---

## §5 Self-Review
- D12 image registry pin: §2.1 compose ${IMAGE_TAG} + image-publish.yml ✓
- D19 backtest NAS sync: §2.2 engine 완료 hook + completion marker + retry ✓
- Epic POLICY_FINALIZED: §3 milestone 7/7 + EPIC-RESULTS 종합 ✓
- carry over 4건 (production smoke + R2 + engine CI token + ${IMAGE_TAG} prod): §1.1 §7 + §3 Epic CLOSED prerequisite ✓
- §6.5 N/A 박제: §1.1 ✓
- §11 backtest artifact = 신규 NAS prefix (ADR-029 market data SoT 무충돌): §1.1 ✓
