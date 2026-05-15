---
type: story-retro
story_key: MCT-181
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 3
sequential_phase: 7
epic_milestone: "7/7 POLICY_FINALIZED"
---

# RETRO — MCT-181 EPIC-mctrader-docker-stack Story-7 (image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory). env=0 재귀 spawn 제약상 ArchitectPL 직접 이행 (RETRO-MCT-179/180 패턴 정합 — cross-cutting PMOAgent = Orchestrator spawn 원칙, one-shot subagent 재귀 spawn 금지 ADR-039). **Epic 마지막 Story = RETRO-MCT-181 + EPIC-mctrader-docker-stack Epic 전체 회고 동반** (§7 Epic 종합 회고).

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-7 (sequential_phase 7, Epic 마지막 Story)** — MCT-180 LAND (integration smoke + resource limits) 위에 두 개의 미결 Epic 결정 (**D12 image registry pin** + **D19 backtest artifact NAS sync**) 구현 + **Epic POLICY_FINALIZED 7/7 박제** (19 D 전수 VERIFIED). 채택 2 D = D12 (semver+sha+latest, prod=sha/release pin / dev=latest, `${IMAGE_TAG:-latest}` 변수화) + D19 (mctrader_runs named volume + NAS sync on completion, completion marker + 3회 retry + exit 0 best-effort).

4 PR cross-repo sequential LAND (hub Phase 1 docs + engine Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). **design + code 양 lane FIX 0** — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 누적 효과로 MCT-180/181 연속 design P0×0 완결 + Phase 0 verify 충실 (compose 8 ghcr.io :latest 하드코딩 실증 → AC scope 정확). Epic 마지막 Story 가 Epic 최초 FIX 0 Story = design lane shift-left 누적 성공의 완결 실증.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D12/§D19 amend + plan + CLAUDE.md) | mctrader-hub#345 MERGED (cff197d, 2026-05-15) — DesignReview iter1 **PASS** (blocking 0) |
| Phase 2 PR1 (engine: backtest CLI 완료 hook NAS sync, land_order 1) | mctrader-engine#56 MERGED (413711e, 2026-05-15T14:42:24Z) — CodeReview **PASS** (blocking 0) |
| Phase 2 PR1 (hub: compose ${IMAGE_TAG} + image-publish.yml, land_order 2) | mctrader-hub#346 MERGED (a8bcf0c, 2026-05-15T14:43:16Z) — CodeReview **PASS** (blocking 0) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 compose 8 라인 ${IMAGE_TAG:-latest} + config exit 0 / AC-2 image-publish.yml matrix 3 repo / AC-3 backtest NAS sync 9 test ALL PASS / AC-4 D11 Layer 3 production carry 명시 / AC-5 Epic 7/7 POLICY_FINALIZED + 19 D verify) |
| 총 INV | 5/5 박제 (forward-only WAL 무수정 + compose ${IMAGE_TAG:-latest} dev fallback + backtest sync 실패 local 보존 exit 0 + image push additive + NAS market data SoT 무충돌 mctrader-backtest-runs 분리) |
| FIX 루프 | design iter1 **PASS (no FIX)** + code engine#56/hub#346 iter1 **PASS (no FIX)** — **Epic 최초 FIX 0 Story** |
| ADR-030 amendment | §D12/§D19 VERIFIED confirm box 박제 (Phase 2 PR1 cross-repo LAND) + **Status POLICY_FINALIZED transition** (19 D 전수 VERIFIED) |
| Epic milestone | **7/7 POLICY_FINALIZED** (MCT-175 ~ MCT-181 COMPLETED). Epic 마지막 Story |
| Epic CLOSED prereq | prod-1~4 carry over registry 박제 (production evidence 완성 후 별 PR) |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#345, cff197d)

- `docs/stories/MCT-181.md` — Story §1-§12 신규 (§6.5 §7/§11 N/A 4 entry 사전 박제 + §7 Epic CLOSE carry over registry prod-1~4)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D12/§D19 amendment box 본문 박제 (Phase 1)
- `CLAUDE.md` — Docker stack 7 Story chain MCT-181 IN_PROGRESS 추가
- `docs/superpowers/plans/2026-05-15-mct-181-image-registry-epic-close.md` — 신규
- DesignReview iter1 **PASS (blocking 0)** — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 누적 효과 (MCT-180 P0×0 → MCT-181 P0×0 연속, 누적 audit 투자 회수 완결)

### 1.2 Phase 2 PR1 — engine (mctrader-engine#56, 413711e, land_order 1)

- `src/mctrader_engine/backtest/nas_sync.py` 신규 — `sync_run_artifacts(run_dir, run_id)`: NAS env guard + idempotent `.done` sentinel + `put_streaming()` streaming upload (MCT-163 LAND API 재사용, sha256 caller-side) + 실패 시 local 보존 (run_dir 삭제 금지) + retry_queue fallback
- `src/mctrader_engine/cli.py` — `backtest()` `EquityCurveWriter.write()` 직후 NAS sync best-effort hook. NAS 실패 시 `click.echo err` + **exit 0 유지** (backtest 결과 자체 성공 = data loss 아님)
- `BACKTEST_NAS_BUCKET = "mctrader-backtest-runs"` — ADR-029 market-data SoT 버킷 `mctrader-market` 완전 분리 (XOR ambiguity invariant 무충돌, D10 = market data SoT 대상 — backtest artifact 제외)
- `tests/test_backtest_nas_sync.py` 9 test 신규 ALL PASS (success/nas_key_format/idempotent_skip/nas_failure/queued_as_failure/already_done/no_env/partial_env/bucket_name) + 회귀 969 passed / 9 skipped 신규 실패 0 (기존 14 failed = pre-existing, base bc8c627 동일) + ruff PASS + pyright 0 errors
- CodeReview iter1 **PASS (blocking 0)**

### 1.3 Phase 2 PR1 — hub (mctrader-hub#346, a8bcf0c, land_order 2)

- `compose.yml` MODIFY — 8 ghcr.io 라인 `:latest` 하드코딩 → `${IMAGE_TAG:-latest}` 변수화 (line 224/243/263/282/301/321/358/393 — signal-collector 5 + paper-engine + backtest-runner + collector). 비-mctrader image (postgres/minio/redis/prometheus/grafana/cadvisor/nginx) 무변경
- `.env.example` + `.env.prod.example` — `IMAGE_TAG` 추가 (dev=latest / prod=release/sha pin 의무)
- `.github/workflows/image-publish.yml` 신규 (77 lines) — `push` (main) + `workflow_dispatch`, strategy.matrix 3 repo (mctrader-data/mctrader-engine/mctrader-signal-collector), `:latest` + `:sha-<7char>` + release tag 시 `:v{semver}`, checkout `MCTRADER_CROSS_REPO_TOKEN` (MCT-176 LAND) + ghcr.io login `GITHUB_TOKEN`
- CodeReview iter1 **PASS (blocking 0)** — AC-1 dev/prod config exit 0 + 8 라인 변수화 + AC-2 YAML valid + matrix 3 repo + trigger 정합 전수 PASS

### 1.4 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-181.md` — frontmatter (4 PR + COMPLETED + completed_at) + §10 FIX Ledger (design+code FIX 0 + Epic design lane FIX 누적) + §10.5 Git Ops Log + §11 retro (Epic 회고 핵심 4) + §12 측정 (AC-1~5 PASS) + §12.1 Epic 19 D verify 매트릭스
- `docs/adr/ADR-030-docker-stack-governance.md` — Status **POLICY_FINALIZED** transition (19 D 전수 VERIFIED 매트릭스 + Epic CLOSE carry over registry) + §D12/§D19 VERIFIED confirm box (Phase 2 PR1 cross-repo LAND)
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-181 status COMPLETED + prs[] + milestone **7/7** + epic_status **POLICY_FINALIZED** + epic_status_history + epic_closed_prerequisite (prod-1~4 registry) + N1 scope_files 정정 (MCT-178 F-001 precedent)
- `CLAUDE.md` — 7 Story chain MCT-181 COMPLETED + **§EPIC-mctrader-docker-stack POLICY_FINALIZED 종합 섹션** (19 D 전수 VERIFIED + 7 Story 완료 현황 + FIX 통계 + Epic CLOSED prereq registry). EPIC-tier-promotion-single-source POLICY_FINALIZED 패턴 정합
- `docs/retros/RETRO-MCT-181.md` 신규 — 본 파일 (PMOAgent sub-dispatch, Story retro + Epic 전체 회고)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-7 + **Epic POLICY_FINALIZED 종합** (7 Story timeline + 19 D 결정 매트릭스 + FIX 통계 + carry over registry)
- `.codeforge/counters.json` — MCT-181 COMPLETED + Epic POLICY_FINALIZED

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 compose ${IMAGE_TAG:-latest} 변수화 (D12) | ✓ PASS | hub#346 — 8 라인 변수화 (224/243/263/282/301/321/358/393) + `docker compose --profile dev/prod config` exit 0 (dev=latest / prod=sha-abc1234 주입) |
| AC-2 image-publish.yml matrix 3 repo (D12) | ✓ PASS | hub#346 — YAML valid + matrix 3 repo (data/engine/signal-collector) + trigger (main push + workflow_dispatch) + 비-mctrader image 무변경 |
| AC-3 backtest NAS sync + .done + retry (D19) | ✓ PASS | engine#56 — `tests/test_backtest_nas_sync.py` 9 test ALL PASS + 회귀 969 passed 신규 실패 0 |
| AC-4 D11 Layer 3 production carry 명시 | ✓ PASS | Phase 1 docs 박제 (§7 carry over registry prod-1~4 + ADR-030 §D12 D11 ESCALATE Layer 3 cross-ref) |
| AC-5 Epic 7/7 POLICY_FINALIZED + 19 D verify | ✓ PASS | Phase 2 PR2 — scope_manifest 7/7 epic_status POLICY_FINALIZED + ADR-030 Status POLICY_FINALIZED + EPIC-RESULTS 19 D 전수 VERIFIED 매트릭스 + CLAUDE.md 종합 |

### 2.2 INV 박제 (5/5)

| INV | 결과 |
|-----|------|
| forward-only (WAL 객체 삭제 금지) | ✓ 박제 — backtest NAS sync = 별 prefix `mctrader-backtest-runs` (market data prefix 무관, WAL 수정 0) |
| compose ${IMAGE_TAG:-latest} (dev fallback latest) | ✓ 박제 — `docker compose config` exit 0 (dev=latest / prod=sha pin) |
| backtest NAS sync 실패 = local 보존 + exit 0 | ✓ 박제 — engine#56 retry 소진 → local 보존 + log warn + exit 0 (backtest result intact, best-effort) |
| image push = additive | ✓ 박제 — image-publish.yml = push :latest + :sha-* only (기존 tag 삭제 step 없음) |
| NAS market data SoT 무충돌 | ✓ 박제 — `BACKTEST_NAS_BUCKET = "mctrader-backtest-runs"` (market data `mctrader-market` 완전 분리, ambiguity invariant 무충돌) |

### 2.3 FIX 루프 (Epic 최초 FIX 0)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub#345) | **0 (PASS, blocking 0)** — MCT-179 ADR-030 전수 reconcile 누적 효과 (MCT-180 P0×0 → MCT-181 P0×0 연속) | LAND cff197d |
| 1 | code (engine#56) | **0 (PASS, blocking 0)** — backtest NAS sync hook + 9 test ALL PASS + 회귀 969 신규 실패 0 | LAND 413711e (land_order 1) |
| 1 | code (hub#346) | **0 (PASS, blocking 0)** — compose 8 라인 변수화 + image-publish.yml + AC verify 전수 PASS | LAND a8bcf0c (land_order 2) |

**MCT-181 = Epic 7 Story 중 유일한 design+code 양 lane FIX 0 Story**. design lane = MCT-175(P0×1)→176(P0×1)→177(P0×0)→178(CONDITIONAL)→179(P0×1)→180(P0×0)→**181(P0×0)**. MCT-179 전수 reconcile (c8e4b8e) 의 MCT-180/181 재발 사전 차단 1회 투자가 Epic 마지막 2 Story 연속 design P0×0 으로 회수 (lesson reapply 누적 효과 완결 실증).

## §3 risks_realized

### 3.1 R-MCT-181-1 image-publish.yml cross-repo checkout 권한 (HIGH)

- **mitigation 적용**: MCT-176 LAND `MCTRADER_CROSS_REPO_TOKEN` secret 재사용. strategy.matrix 3 repo 각 checkout `token`
- **realized**: NO — hub#346 image-publish.yml YAML valid + matrix 3 repo 정합 LAND (실 ghcr.io push = production deploy 시점 prod-1 carry, dry-run 미수행 — workflow_dispatch 실 발동은 prod 적용 시)

### 3.2 R-MCT-181-2 backtest artifact NAS sync 재실행 idempotency (MEDIUM)

- **mitigation 적용**: `.done` marker 존재 시 sync skip (idempotent). 새 backtest = 새 run_id (timestamp-based UUID)
- **realized**: NO — engine#56 `test_backtest_sync_idempotent` (already_done) PASS = `.done` 존재 시 put_streaming 미호출 verify

### 3.3 R-MCT-181-3 ${IMAGE_TAG} prod pin 미적용 시 dev=latest 폴백 (LOW)

- **mitigation 적용**: `.env.prod.example` `IMAGE_TAG=<release_tag_or_git_sha>` 주석 의무 박제
- **realized**: PARTIAL — 선언형 LAND. 실 production prod pin 적용 = production deploy 시점 별 PR (prod-1 carry over)

## §4 followups (Epic CLOSED prerequisite — production evidence 완성 후 별 PR/Story)

| prod-N | carry over | timing | gate |
|--------|-----------|--------|------|
| prod-1 | ${IMAGE_TAG} prod 실 적용 | production deploy 시 release/sha pin | `.env.prod` `IMAGE_TAG=sha-<commit>` or `v<semver>` 박제 |
| prod-2 | full-stack production smoke (D11 ESCALATE Layer 3) | D12 image pin + production deploy 후 | collector+paper-engine `compose up --wait` evidence |
| prod-3 | R2 WAL 30G production 측정 | peak 09:00 KST 1h burst 실 측정 | 30G 이하 verify (초과 시 D11 hard_limit amendment). EPIC-tier-promotion-single-source prod-2 병행 (cross-Epic) |
| prod-4 | Epic CLOSED 박제 PR | prod-1~3 모두 완료 후 | POLICY_FINALIZED → CLOSED transition |
| 별(engine) | engine#55 ci/lookahead-lint mctrader-market-upbit private-dep token | engine repo 자체 CI infra | engine repo 별 처리 (본 Epic 범위 외) |

## §5 lessons (Story-level process learnings)

### 5.1 Epic 마지막 Story FIX 0 = design lane shift-left 누적 성공의 완결 실증

MCT-181 = EPIC-mctrader-docker-stack 7 Story 중 유일한 design+code 양 lane FIX 0 Story. 원인 2종:
1. **design lane** = MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 의 MCT-180/181 재발 사전 차단 투자 회수 (MCT-180 P0×0 → MCT-181 P0×0 연속). 매 Story 자기 D 만 부분 reconcile 시 stale 누적 → 1회 전수 reconcile 투자가 마지막 2 Story design P0×0 으로 ROI 회수
2. **code lane** = Phase 0 verify 충실 (compose.yml 8 ghcr.io :latest 하드코딩 grep 실증 → AC scope 정확). MCT-170/177/178/179/180 의 Phase 0 verify gap (설계가 sibling repo runtime 실상 미검증, 6회 재현) 이 MCT-181 에서 미재현 — D12 (선언형 compose 변수화) + D19 (engine backtest hook, 단일 repo) 가 cross-repo runtime 가정 의존도 낮음

**lesson**: design lane shift-left (전수 reconcile 1회 투자) 와 code lane Phase 0 verify 충실이 동시 적용된 Story 는 FIX 0 달성 가능. 단 MCT-181 의 FIX 0 은 D12/D19 의 cross-repo runtime 의존도가 낮은 (선언형 + 단일 repo) 특성도 기여 — MCT-180 류 cross-repo full-stack 검증 Story 와 단순 비교 불가. **design lane shift-left 누적 효과는 실증되었으나, code lane Phase 0 verify 강제 게이트화 (TestContractArch §8 검수 범위 확장) 는 차기 Epic 의 cross-repo Story 에서 여전히 필요** (PMO retro 누적 입력 — MCT-180 §5.3 동형).

### 5.2 best-effort NAS sync (exit 0 유지) = backtest 결과 보존 우선 설계 정합

D19 backtest NAS sync = sync 실패 시 retry 3회 → local 보존 + log warn + **exit 0 유지** (backtest 결과 자체 성공 = data loss 아님). engine#56 `test_backtest_sync_nas_failure_local_preserve` (nas_failure) + `queued_as_failure` PASS 로 검증.

**lesson**: 부수 작업 (artifact sync) 실패가 본 작업 (backtest 연산) 결과를 무효화하면 안 됨. best-effort + idempotent (`.done` marker) + retry_queue fallback = 데이터 손실 0 보장하면서 sync 일시 실패 허용. R5 (local↔remote 갈림) mitigation = `.done` marker 미존재 run_id 만 manual reconcile (`put_streaming()` 재호출). 이 패턴 = MCT-163 DualWriter best-effort streaming 과 동형 (부수 NAS PUT 실패 ≠ 본 데이터 손실).

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#345) — §D12/§D19 amendment box 본문

- §D12: image registry pin (prod=sha/release pin / dev=latest, `${IMAGE_TAG:-latest}` 변수화) + image-publish.yml 신규 명세 + D11 ESCALATE Layer 3 cross-ref
- §D19: backtest artifact NAS sync (`mctrader-backtest-runs/` prefix + completion marker + retry + idempotent + ADR-029 §D1 market data SoT 무충돌)

### 6.2 Phase 2 PR2 (본 PR) — §D12/§D19 VERIFIED + Status POLICY_FINALIZED

- §D12 VERIFIED confirm box (hub#346 a8bcf0c — compose 8 라인 변수화 + image-publish.yml 77 lines + AC verify 전수 PASS)
- §D19 VERIFIED confirm box (engine#56 413711e — nas_sync.py 신규 + cli.py best-effort hook + 9 test ALL PASS + 회귀 969 신규 실패 0)
- **Status transition**: Accepted → **POLICY_FINALIZED** (19 D 전수 VERIFIED 매트릭스 + Epic CLOSE carry over registry prod-1~4)

ADR-030 19 D 전수 VERIFIED 완결 → Status POLICY_FINALIZED. Epic CLOSED 자체 = production evidence (prod-1~4) 완성 후 별 PR (prod-4).

---

## §7 EPIC-mctrader-docker-stack Epic 전체 회고 (POLICY_FINALIZED 7/7)

> Epic 마지막 Story RETRO 동반 Epic 종합 회고. EPIC-tier-promotion-single-source 패턴 정합.

### 7.1 Epic 7 Story timeline (sequential)

| phase | Story | 결정 | LAND | design FIX | code FIX |
|-------|-------|------|------|-----------|----------|
| 1 | MCT-175 | D1/D3/D7/D13 | hub#326+327+328 | P0×1 | — |
| 2 | MCT-176 | D7/D9/D14 | hub#330+data#64+hub#331 | P0×1 | — |
| 3 | MCT-177 | D2/D4/D10/D15 | hub#333+data#65+engine#54+hub#334 | P0×0 | — |
| 4 | MCT-178 | D2/D4/D10/D16 | hub#336+sigcol#1+hub#337 | CONDITIONAL_PASS | 1 iter |
| 5 | MCT-179 | D5/D8/D17 | hub#339+data#66+hub#340 | P0×1 (전수 reconcile c8e4b8e) | 1 iter (metric desync) |
| 6 | MCT-180 | D4/D11/D18 | hub#342+data#67+engine#55+hub#343 | P0×0 | 3 iter + **ESCALATE** |
| 7 | **MCT-181** | **D12/D19** | hub#345+engine#56+hub#346 | **P0×0** | **0 iter** |

### 7.2 Epic 19 D 결정 매트릭스 (전수 VERIFIED)

19 D = 3 pass Codex review (D1-D6 infra / D7-D12 wiring / D13-D19 detail) → 7 Story sequential 분해 (D6=B). 19/19 VERIFIED. 단 2 D = production evidence carry: D5 (WAL 30G synthetic → prod-3 production 실측), D11 Layer 3 (full-stack production smoke → prod-2). 나머지 17 D 완전 VERIFIED.

### 7.3 Epic 전체 FIX 통계 + 패턴

- **design lane**: P0×1 (175) → P0×1 (176) → P0×0 (177) → CONDITIONAL (178) → P0×1 (179) → P0×0 (180) → P0×0 (181). **MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 1회 투자 → MCT-180/181 연속 design P0×0** (lesson reapply 누적 효과 ROI 실증, Epic 마지막 완결)
- **code lane**: 178 (1 iter) → 179 (1 iter metric desync) → 180 (**3 iter + ESCALATE 1회**) → 181 (0 iter). ESCALATE = MCT-180 D11 CI 격리 설계 결함 (full-stack compose up CI 격리 구조적 불가) → FIX 3회 소진 → ArchitectPL chief judge **설계 원인 판정** → option b resolution (614033a) infra-only 3-layer 재설계 → ESCALATE-fix PASS (**FIX 루프 max 의 ESCALATE 안전판 정상 동작 검증**)
- **Phase 0 verify lesson 6회 누적**: MCT-170/177/178/179/180 cross-repo Phase 0 verify gap (설계가 sibling repo runtime 실상 미검증) 6회 재현. 동형 = "설계가 실행 환경/runtime 제약 미검증" (MCT-179 §D8 가공 metric + MCT-180 paper daemon ReaderCache 미사용 + MCT-180 D11 CI 격리 full-stack 전제). MCT-181 = Phase 0 verify 충실 (compose 8 ghcr.io :latest 실증)
- **cross-repo metric desync 누적**: MCT-179 §D8 가공 metric LAND 부재 → MCT-180 engine#55 reader_cache producer path 가정 오류 동형 재현 (carry over chain 의 무비판 승계 위험)

### 7.4 Epic 핵심 lesson (PMO retro 누적 입력)

1. **design lane shift-left 누적 성공 완결 실증** — 매 Story 부분 reconcile (stale 누적) vs 1회 전수 reconcile (MCT-179 c8e4b8e) 의 ROI 비대칭. 전수 reconcile 1회 투자 = MCT-180/181 연속 design P0×0 회수. **차기 Epic 의 ADR/scope_manifest SSOT 정합 = Epic 초중반 전수 reconcile 1회 의무화 권고** (Story별 부분 reconcile 금지)
2. **ESCALATE 안전판 검증** — MCT-180 D11 CI 격리 설계 결함이 FIX 3회 (mechanical/구현 layer) 소진 후 ArchitectPL chief judge 설계 원인 판정 → 설계 재정의 (구현 재작업 아님) 경로로 정상 해소. FIX 루프 max 의 ESCALATE = 설계 결함의 안전판 (구현 무한 FIX loop 방지)
3. **code lane Phase 0 verify 강제 게이트화 필요 (미해소 carry over)** — design lane shift-left (전수 reconcile → P0×0 누적 성공) 와 code lane Phase 0 verify gap (6회 재현) 의 비대칭. design lane = lesson reapply 누적 성공, code lane = 동형 재현 지속. **차기 Epic = code lane Phase 0 verify 강제 게이트화 (TestContractArch deputy §8 perf baseline 검수 범위에 metric/runtime producer path grep 실증 추가) — PMO retro 핵심 입력 (MCT-180 §5.3 + MCT-181 §5.1 동형 누적)**
4. **cross-repo Epic 의 CI-friendly 검증 SSOT** — full-stack compose up CI gate = sibling repo image registry pin (D12) 선행 없이 구조적 불가. CI smoke = infra 정합 / boundary = testcontainers / full-stack = production deploy evidence 의 3-layer 분리가 cross-repo Epic 의 CI 검증 SSOT (MCT-180 ESCALATE resolution → Epic 차원 패턴 박제)

### 7.5 Epic 산출물 종합

- **ADR-030** (신규, POLICY_FINALIZED) — Docker stack governance 19 D
- **compose.yml** — collector + paper-engine + backtest-runner service 추가 + dev/prod profile + 8 라인 ${IMAGE_TAG:-latest} + 7 service deploy.resources.limits
- **신규 workflow 3종** — cross-repo-lock-check.yml (D13) + compose-validate.yml (D16) + integration-smoke.yml (D11 infra-only) + image-publish.yml (D12)
- **cross-repo code** — mctrader-data (collector entrypoint + effective config dump + testcontainers) + mctrader-engine (SIGTERM asyncio SSOT + universe override + reader_cache Gauge + backtest NAS sync) + mctrader-signal-collector (5 worker Redis prefix dual write)
- **observability** — Grafana docker-stack dashboard + Prometheus scrape + alert rule (ContainerMemoryHigh + WAL 30G FAIL gate)
- **runbook** — docker-stack-deploy.md + nas-minio-secret-rotation.md amend

### 7.6 Epic CLOSED transition (prod-1~4 carry over)

Epic = **POLICY_FINALIZED** (정책 finalize 완료, 19 D 전수 VERIFIED). Epic **CLOSED** 자체 박제 = production evidence (prod-1 ${IMAGE_TAG} prod 적용 / prod-2 full-stack production smoke / prod-3 R2 WAL 30G production 측정 / prod-4 Epic CLOSED 박제 PR) 완성 후 별 PR. prod-3 = EPIC-tier-promotion-single-source prod-2 와 cross-Epic 병행 (WAL 30G production 측정 = 두 Epic 공통 CLOSED prerequisite). engine#55 ci/lookahead-lint token 이슈 = engine repo 별 처리 (본 Epic 범위 외).

## §8 Cross-ref

- Story: `docs/stories/MCT-181.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-181-image-registry-epic-close.md`
- ADR-030 (POLICY_FINALIZED, §D12/§D19 VERIFIED): `docs/adr/ADR-030-docker-stack-governance.md`
- scope_manifest (POLICY_FINALIZED 7/7): `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- EPIC-RESULTS (POLICY_FINALIZED 종합): `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md`
- 전 Story RETRO: `docs/retros/RETRO-MCT-175.md` ~ `RETRO-MCT-180.md`
- Parent Epic results (POLICY_FINALIZED, cross-Epic prod-3 병행): `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- Phase 1 PR: mctrader-hub#345 (cff197d, 2026-05-15) — Story + ADR-030 §D12/§D19 amend + plan + CLAUDE.md. DesignReview iter1 PASS (blocking 0)
- Phase 2 PR1 (engine): mctrader-engine#56 (413711e, 2026-05-15T14:42:24Z) — backtest CLI 완료 hook NAS sync (land_order 1). CodeReview PASS (blocking 0)
- Phase 2 PR1 (hub): mctrader-hub#346 (a8bcf0c, 2026-05-15T14:43:16Z) — compose ${IMAGE_TAG} + image-publish.yml (land_order 2). CodeReview PASS (blocking 0)
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (7 file: Story + ADR-030 POLICY_FINALIZED + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-7 + counters.json)
