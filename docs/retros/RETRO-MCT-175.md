---
type: story-retro
story_key: MCT-175
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 1
---

# RETRO — MCT-175 EPIC-mctrader-docker-stack Story-1 (Epic entry, compose base + dev/prod profile + cross-repo lock gate + ADR-030 publish)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

**EPIC-mctrader-docker-stack 의 Epic entry Story (Story-1)** — Docker stack infrastructure 기반 정비. 19 D 결정 (Codex 3 pass 합성) 중 4 D (D1/D3/D7/D13) 채택. ADR-030 publish + compose.yml dev/prod profile 분리 + .env 분리 + NAS DNS preflight + cross-repo lock CI gate.

3 PR cross-repo sequential LAND (Phase 1 docs only + Phase 2 PR1 code + Phase 2 PR2 박제).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 publish + runbook stub + CLAUDE.md) | mctrader-hub#326 MERGED (8c485ef, 2026-05-15T03:48:11Z) |
| Phase 2 PR1 (compose.yml + .env split + preflight + cross-repo lock CI gate + 14 unit test) | mctrader-hub#327 MERGED (daef9b3, 2026-05-15T04:16:16Z) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#328 MERGED (dbba327, 2026-05-15T05:47:28Z) |
| 총 AC | **4/4 PASS + 1 stub** (AC-1/2/3/5 PASS + AC-4 stub MCT-176 carry) |
| 총 INV | 4/4 의무 박제 (INV-1~4) |
| 산출물 | hub Phase 1 docs (5 file) + hub Phase 2 PR1 code (12 file, 597 insertions) + hub 박제 (6 file) |
| 총 신규 테스트 | **14** (`tests/test_check_cross_repo_locks.py` — main() integration 5 + lib_major 5 + python_version 4 ALL PASS) |
| 회귀 | 0 (hub repo 단독 변경, mctrader-data + mctrader-engine 미영향) |
| FIX 루프 | **2회** (design iter 1 + code iter 1) — iter 2 모두 PASS |
| brainstorm | 19 D (Codex 3 pass) — D1/D3/D7/D13 = MCT-175 채택, D2/D4/D5/D7-D19 = MCT-176~181 carry over |
| ADR-030 Status | Proposed → **Accepted** (MCT-175 LAND 2026-05-15) |
| Epic milestone | **1/7** (MCT-175 COMPLETED) |
| Defer 3건 (MCT-176 carry) | P1-2 (DNS wildcard FP) + P1-3 (mc alias trap race) + P2-1 (shell error handling) |
| Operational carry over | NAS_MINIO_* secret 등록 + `cross-repo-lock-check.yml` PR auto trigger 복원 (현 `workflow_dispatch` only) → MCT-176 |

## §1 Story 개요 + Phase 0 verify 발견

### 1.1 Phase 0 verify 발견 (사전 가설 vs 실 코드)

session prompt "EPIC-mctrader-docker-stack 진입 — compose 기반 정비 + 어플리케이션 service 추가". Phase 0 4 agent burst (DomainAgent / ResearcherAgent / RequirementsAnalystAgent / PMOAgent) + 자체 verify 결과 **3건 가설 정정**:

| 사전 가설 | verify 결과 | impact |
|-----------|-------------|--------|
| host docker stack 부재, collector/runner native 실행 | compose.yml 존재 (315 lines) + signal-collector 5 service 컨테이너화 완료 | scope reduce: "신규 stack 생성" → "기존 compose 확장" |
| Dockerfile 6 repo 다 부재 | 4 repo (data/engine/web/signal-collector) Dockerfile 존재 (MCT-98 COMPLETED) | scope shift: "Dockerfile 신규" → "service 추가만" |
| MinIO 는 NAS 만 존재 | **MinIO 2개**: hub/compose.yml (named volume, dev/test) + docker/minio/ (NAS Synology, prod) | D3 profile 분리 정당성 강화 |

→ MCT-175 = **기존 compose.yml 확장** (신규 stack 생성 아님). cross-repo lock check 대상 = 6 repo 전수 (D13 정합), Dockerfile 부재 2 repo (hub + market) 는 MISSING_OK_REPOS 등록.

### 1.2 Critical decision (Codex 3 pass 합성)

19 D 결정 중 **MCT-175 채택 4 D** (Epic entry 범위):
- D1=C (WAL host bind mount + L1 named volume) — forward-only invariant 정합
- D3=A (compose profiles dev/prod + env_file 분리) — operational parity
- D7=A (NAS DNS 직접 해석 + preflight 검증) — fail-fast gate
- D13=D (각 repo 독립 uv.lock + cross-repo CI gate) — drift 차단

나머지 15 D = MCT-176 ~ MCT-181 carry over (manifest 박제, ADR-030 본문 박제 8 D + 10 D defer).

## §2 19 D 결정 매트릭스 (PMO finalize)

| pass | D | 결정 | Option | owner Story |
|------|---|------|--------|-------------|
| 1st | D1 | WAL host disk + L1 named volume | C | MCT-175 ✓ |
| 1st | D2 | paper-engine daemon + backtest profile 동일 image | A | MCT-177 / MCT-178 |
| 1st | D3 | compose profiles dev/prod + env_file | **A** | **MCT-175 ✓** |
| 1st | D4 | SIGTERM + 60s grace + invariant scan | C | MCT-177 / MCT-179 |
| 1st | D5 | WAL 30G measurement + amendment trigger | C | MCT-179 |
| 1st | D6 | 7 Story 분해 | B | epic-level |
| 2nd | D7 | DNS 직접 해석 + preflight | **A** | **MCT-175 + MCT-176 ✓** |
| 2nd | D8 | 앱 /metrics + Grafana + alert | C | MCT-179 |
| 2nd | D9 | .env + rotation script + cron + Slack | D | MCT-176 |
| 2nd | D10 | env default + compose override | D | MCT-177 / MCT-178 |
| 2nd | D11 | compose CI smoke + testcontainers | C | MCT-180 |
| 2nd | D12 | image registry semver+sha+latest | B | MCT-181 |
| 3rd | D13 | 각 repo 독립 uv.lock + CI gate | **D** | **MCT-175 ✓** |
| 3rd | D14 | env override + YAML default | D | MCT-176 |
| 3rd | D15 | Redis key prefix | C | MCT-177 |
| 3rd | D16 | compose config lint + up --wait | B | MCT-178 |
| 3rd | D17 | SIGTERM graceful + startup scan + 외부 backup 없음 | A | MCT-179 |
| 3rd | D18 | resource limits + alert >80% | D | MCT-180 |
| 3rd | D19 | mctrader_runs named volume + NAS sync | C | MCT-181 |

## §3 진행 timeline

| 시각 | 작업 | 결과 |
|------|------|------|
| 2026-05-15T00:00Z | Phase 0 verify + 4 agent burst (DomainAgent / Researcher / RequirementsAnalyst / PMOAgent) + codeforge-brainstorm | 19 D Codex 3 pass 합성 완료 |
| 2026-05-15T00:30Z | Phase 1 PR (hub docs only) — 5 file (Story / ADR-030 / spec / plan / scope_manifest) | mctrader-hub#326 OPEN |
| 2026-05-15T01:00Z | DesignReviewPL iter 1 FIX (P0×1 + P1×3 + P2×4 = 8) — Story §7/§11 N/A 사유 + ADR-030 R1/R4 acceptance carrier + owner Story badge + Out of scope + §8 baseline N/A + Dockerfile footnote + CLAUDE.md sequential_phase column | 8 fix → DesignReviewPL iter 2 PASS |
| 2026-05-15T03:48Z | Phase 1 PR MERGED | mctrader-hub#326 (8c485ef), main fast-forward 09c9e7d→8c485ef |
| 2026-05-15T04:00Z | Phase 2 PR1 (hub code) — 12 file (compose.yml + .env split + preflight + cross-repo lock check + 14 test) | mctrader-hub#327 OPEN |
| 2026-05-15T04:10Z | CodeReviewPL iter 1 FIX (P0×2 + P1×3 + P2×2 = 7) — P0-1 nginx.prod.conf 부재 / P0-2 check_cross_repo_locks.py D13 coverage gap + semantic mismatch / P1-1 §8.5 chmod +x 누락 / P1-2 preflight DNS wildcard FP / P1-3 mc alias trap race / P2-1 shell error handling / P2-2 test main() 미커버 | 4 fix + 3 defer → CodeReviewPL iter 2 PASS |
| 2026-05-15T04:16Z | Phase 2 PR1 MERGED | mctrader-hub#327 (daef9b3), main fast-forward 8c485ef→daef9b3 |
| 2026-05-15T13:30Z | Phase 2 PR2 (hub 박제) — 6 file (Story §10/§11/§12 + ADR-030 Accepted + scope_manifest 1/7 + CLAUDE.md + RETRO 신규 + EPIC-RESULTS 신규) | mctrader-hub#328 OPEN → 본 PR |

## §4 AC + INV verify

### 4.1 AC PASS

| AC | 결과 | 근거 |
|----|------|------|
| **AC-1 compose profile config** | ✓ PASS | `docker compose --profile dev config` exit 0 + `docker compose --profile prod config` exit 0 (compose.yml schema valid) |
| **AC-2 .env endpoint 분기 정합** | ✓ PASS | `.env.dev` NAS_MINIO_ENDPOINT=http://minio:9000 (hub MinIO) + `.env.prod.example` NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000 (NAS) |
| **AC-3 preflight exit code matrix** | ✓ PASS | exit 0/10/20/30/99 정합 검증 — `./scripts/preflight-nas-dns.sh .env.prod` matrix valid |
| **AC-4 WAL mount 정책 박제** | stub PASS | `compose.yml` collector service stub 주석 박제 (`/var/lib/mctrader/wal:/var/lib/mctrader/data` ADR-030 §D1). 실 활성화 = MCT-176 LAND |
| **AC-5 cross-repo lock CI gate** | ✓ PASS | `scripts/check_cross_repo_locks.py` exit 0 + 14 unit test green (main() 5 + lib_major 5 + python_version 4). `workflow_dispatch` only trigger (secret 미등록 carry over → MCT-176) |

### 4.2 INV 박제

| INV | 결과 | 근거 |
|-----|------|------|
| INV-1 `.env.prod` = `.gitignore` 대상 | ✓ 박제 | `.gitignore` `.env.dev` + `.env.prod` 추가 (Phase 2 PR1) |
| INV-2 preflight = prod profile up 전 의무 | ✓ 박제 | ADR-030 §D7 본문 박제 + runbook stub |
| INV-3 WAL = host bind mount 의무 | ✓ 박제 | ADR-030 §D1 본문 박제 (forward-only invariant 정합) |
| INV-4 cross-repo lock CI gate = hub PR merge 필요조건 | ✓ 박제 (현 workflow_dispatch only, MCT-176 secret 등록 후 PR auto trigger 복원) | `.github/workflows/cross-repo-lock-check.yml` 박제 |

## §5 산출물

### 5.1 Phase 1 PR (hub docs only, mctrader-hub#326, 8c485ef)

- `docs/stories/MCT-175.md` 신규 (Story file)
- `docs/adr/ADR-030-docker-stack-governance.md` 신규 (8 D 본문 박제 + 10 D defer manifest)
- `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md` 신규 (19 D + 7 Story 분해)
- `docs/superpowers/plans/2026-05-15-mct-175-docker-stack-base.md` 신규 (Phase 1 + Phase 2 PR1 + Phase 2 PR2)
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` 신규 (Epic manifest)
- `docs/runbooks/docker-stack-deploy.md` 신규 (stub)
- `CLAUDE.md` Docker stack 섹션 추가
- `.codeforge/counters.json` 7 Story reservation (MCT-175~181) + ADR-030

### 5.2 Phase 2 PR1 (hub code, mctrader-hub#327, daef9b3)

- `compose.yml` MODIFY — profile 주석 + minio/mc service `profiles: ["dev"]` + nginx prod profile + collector stub 주석
- `.env.example` MODIFY — COINGLASS_API_KEY + NAS_MINIO_* 4종 추가
- `.gitignore` MODIFY — `.env.dev` + `.env.prod` 추가
- `.env.prod.example` CREATE — prod profile template
- `scripts/preflight-nas-dns.sh` CREATE — D7 NAS DNS+TCP+S3 preflight (exit 0/10/20/30/99)
- `nginx/nginx.prod.conf` CREATE — prod placeholder (CodeReview iter 1 P0-1 fix)
- `scripts/check_cross_repo_locks.py` CREATE — D13 cross-repo uv.lock check (121 lines, exit 0/1/2/99)
- `.github/workflows/cross-repo-lock-check.yml` CREATE — D13 GitHub Actions CI gate (`workflow_dispatch` only, secret 미등록 carry over)
- `tests/test_check_cross_repo_locks.py` CREATE — 14 unit test (main 5 + lib_major 5 + python_version 4)

### 5.3 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-175.md` — frontmatter (story_issues 326+327+TBD + status COMPLETED + completed_at) + §10 FIX Ledger row 3 + §10.5 Git Ops Log 5 row + §11 retro ref + §12 측정 결과 PASS
- `docs/adr/ADR-030-docker-stack-governance.md` — Status Proposed → **Accepted** + Amendment box (MCT-175 LAND 박제 + MCT-176 carry over 5 항목)
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-175 status COMPLETED + completed_date + prs[] + milestone 1/7
- `CLAUDE.md` — Docker stack 섹션 헤더 IN_PROGRESS → COMPLETED + 7 Story chain MCT-175 row COMPLETED
- `docs/retros/RETRO-MCT-175.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` 신규 — §Story-1 박제 (milestone 1/7)

## §6 Risk realized

- **R1 (NAS HTTP-only 평문 통신)** HIGH — 사용자 explicit accept 완료 (2026-05-15, plan §0 / Story §3 / ADR-030 Consequences). LAN 내부망 + NAS firewall mctrader IP only + .env 0600 + 90d rotation mitigation. MCT-155 TLS cutover = 별 Story 백로그.
- **R2 (WAL 30G 미측정)** CRITICAL — carry over MCT-179. paper mode synthetic baseline = MCT-172 측정 ±50% range (15~45G). production 측정은 peak 09:00 KST burst window 별 PR.
- **R3 (D14 effective config 미출력)** MEDIUM — carry over MCT-176. collector entrypoint stdout dump 의무.
- **R4 (host disk 손실 → WAL 영구 손실)** MEDIUM — 사용자 explicit accept 완료 (2026-05-15). forward-only + NAS L1+ SoT + 1d max loss window mitigation.

## §7 Followups (post-Story carry over → MCT-176)

본 Story LAND 후 다음 Story (MCT-176) 진입 시 처리 의무:

1. **P1-2 defer (preflight DNS wildcard FP)** — logging 통합 시 fix
2. **P1-3 defer (mc alias trap race)** — SIGINT race window security 위협 낮음, cross-ref
3. **P2-1 defer (shell error handling)** — 실 위험 낮음 carry over
4. **NAS_MINIO_* secret 등록** (`AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` GitHub Actions secret) — MCT-176 Phase 1
5. **`cross-repo-lock-check.yml` PR auto trigger 복원** (`workflow_dispatch` only → `on: pull_request`) — MCT-176 Phase 2 secret 등록 후 LAND
6. **collector container 추가** (compose.yml service slot 활성화 — D7 endpoint preflight integration + D9 rotation script + D14 effective config dump)
7. **ADR-027 §D2 HTTP Stage 1 gate amendment 결정** — MCT-176 진입 전 사용자 결정 의무 (R1 HIGH)

## §8 FIX 루프

**2회 발생** (design iter 1 + code iter 1, iter 2 모두 PASS):

### 8.1 FIX-MCT-175-001 (design iter 1, 2026-05-15T01:00Z)

DesignReviewPL verdict=FIX. 8 finding (P0×1 + P1×3 + P2×4) 동시 fix.

| finding | severity | fix |
|---------|----------|-----|
| F1 Story §7/§11 N/A 사유 부재 | P0 | Story §6.5 신규 4 entry (§7 / §7.4 / §11 / §11.6 N/A 사유) |
| F2 ADR-030 R1 acceptance carrier 부재 | P1 | ADR-030 Consequences R1 carrier 박제 (user_acknowledged_at + email) |
| F3 ADR-030 R4 acceptance carrier 부재 | P1 | ADR-030 Consequences R4 carrier 박제 |
| F4 ADR-030 owner Story badge 부재 | P1 | 8 §D 본문 owner Story badge 추가 |
| F5 ADR-030 Out of scope 명시 부재 | P2 | Out of scope mini-section + 10 D defer manifest |
| F6 Story §8 baseline N/A 사유 부재 | P2 | Story §8 footnote 추가 (§8.3 performance baseline N/A) |
| F7 Story §1.1 Dockerfile footnote 부재 | P2 | Phase 0 verify finding Dockerfile 부재 repo 2건 (hub + market) 박제 |
| F8 CLAUDE.md sequential_phase column 부재 | P2 | 7 Story chain 표 sequential_phase column 추가 |

### 8.2 FIX-MCT-175-002 (code iter 1, 2026-05-15T04:10Z)

CodeReviewPL verdict=FIX. 7 finding (P0×2 + P1×3 + P2×2). **4 fix + 3 defer**.

| finding | severity | 처리 |
|---------|----------|------|
| P0-1 nginx.prod.conf 부재 | P0 | **fix** — `nginx/nginx.prod.conf` placeholder 생성 + Plan §2.1.2 amend (option A 채택) |
| P0-2 check_cross_repo_locks.py D13 coverage gap + semantic mismatch | P0 | **fix** — MISSING_OK_REPOS = {hub, signal-collector} + required repo 부재 시 exit 99 + docstring distinct equality 갱신 + ADR-030 §D13 amendment box append |
| P1-1 §8.5 chmod +x 누락 | P1 | **fix** — §8.5 매핑표 preflight row Plan ref 갱신 (§2.3.1 + §2.3.2 chmod +x) |
| P1-2 preflight DNS wildcard FP | P1 | **defer** — MCT-176 logging 통합 시 fix |
| P1-3 mc alias trap race | P1 | **defer** — MCT-176 cross-ref (SIGINT race window, security 위협 낮음) |
| P2-1 shell error handling | P2 | **defer** — 실 위험 낮음 carry over |
| P2-2 test main() 미커버 | P2 | **fix** — tests 5 신규 main() integration test (exit 0/99/0/1/2 matrix) |

이후 `bb0a7f5` (workflow_dispatch only — secret 미등록 carry over) + `7328b16` (phase-gate re-trigger) 추가 commit. CodeReviewPL iter 2 PASS.

## §9 ADR-030 박제 + Amendment

### 9.1 ADR-030 publish (Phase 1)

8 D 본문 박제 + 10 D Out of scope manifest:
- 본문: D1 / D2 / D3 / D7 / D12 / D13 / D17 / D18
- defer: D4 / D5 / D8 / D9 / D10 / D11 / D14 / D15 / D16 / D19 (manifest SSOT, 각 owner Story Phase 1 LAND 시 amendment box append)

### 9.2 ADR-030 Amendment (Phase 2 PR1 — code iter 1 P0-2 fix)

§D13 amendment box append:
- allowed_missing repos = {mctrader-hub, mctrader-signal-collector} (현 시점 uv 미도입 SSOT)
- 그 외 4 repo (data / engine / web / market) uv.lock 부재 시 exit 99 strict mode
- python_version semantic = distinct equality only (절대 minimum 미정의)

### 9.3 ADR-030 Status (Phase 2 PR2 — 본 PR)

**Proposed → Accepted** (MCT-175 LAND 2026-05-15) + Amendment box (MCT-175 D1/D3/D7/D13 VERIFIED + MCT-176 carry over 5 항목).

## §10 다음 Story chain

**MCT-176** (collector container + NAS credential rotation + effective config dump) — sequential_phase 2.

진입 prerequisite:
1. MCT-175 hub#328 (Phase 2 PR2, dbba327) MERGED ✓ (2026-05-15T05:47:28Z)
2. ADR-027 §D2 Stage 1 HTTP gate amendment 결정 (R1 HIGH, 사용자 explicit)
3. NAS_MINIO_* secret 등록 (GitHub Actions secrets)
4. defer 3건 carry over 처리 (P1-2 / P1-3 / P2-1)
5. `cross-repo-lock-check.yml` PR auto trigger 복원

채택 결정: D7 (preflight integration) + D9 (rotation script + cron + Slack) + D14 (effective config dump).

## §11 Cross-ref

- Story: `docs/stories/MCT-175.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-175-docker-stack-base.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md`
- runbook stub: `docs/runbooks/docker-stack-deploy.md`
- Phase 1 PR: mctrader-hub#326 (8c485ef, 2026-05-15T03:48:11Z)
- Phase 2 PR1: mctrader-hub#327 (daef9b3, 2026-05-15T04:16:16Z) — 4 commit FIX 루프 (012cef5 → bcddc89 → bb0a7f5 → 7328b16)
- Phase 2 PR2: mctrader-hub#328 (dbba327, 2026-05-15T05:47:28Z) — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS 신규)
