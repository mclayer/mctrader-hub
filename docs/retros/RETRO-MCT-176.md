---
type: story-retro
story_key: MCT-176
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 2
---

# RETRO — MCT-176 EPIC-mctrader-docker-stack Story-2 (collector container + NAS credential rotation + effective config dump)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-2 (sequential_phase 2)** — compose stack 에 첫 어플리케이션 service 진입. MCT-175 LAND 가 만든 인프라 (compose dev/prod profile + .env split + cross-repo lock gate) 위에 `mctrader-data collector` 를 컨테이너로 활성화. ADR-030 §D7/§D9/§D14 amendment box 본문 박제 + 신규 CLI subcommand + rotation script + carry over 4건 fix.

4 PR cross-repo sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). MCT-175 P0 lesson (Story §6.5 Change Plan §7/§11 N/A 사유 박제) 재적용 → Phase 1 P0 finding 0.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D9/§D14 amend + rotation runbook + CLAUDE.md) | mctrader-hub#330 MERGED (a92e55a, 2026-05-15) |
| Phase 2 PR1 (data code: SIGTERM stub + effective-config + 8 신규 test) | mctrader-data#64 MERGED (e3141b6, 2026-05-15T08:00:41Z) |
| Phase 2 PR1 (hub code: collector service + rotation script + carry over fix + workflow trigger 복원) | mctrader-hub#331 MERGED (3498a8b, 2026-05-15T08:04:03Z) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 ~ AC-5) |
| 총 INV | 4/4 박제 (INV-1~4) |
| 산출물 | hub Phase 1 docs (5 file) + data Phase 2 PR1 code (3 file, 274 additions) + hub Phase 2 PR1 code (5 file, 275 additions / 37 deletions) + hub 박제 (6 file) |
| 총 신규 테스트 | **8** (mctrader-data `tests/test_effective_config.py` ALL PASS) |
| 회귀 (mctrader-data full suite) | **965 passed + 24 skipped + 4 xfailed** (회귀 0, MCT-172 954 baseline + 11 추가 test) |
| FIX 루프 | **4회** (design Phase 1 iter 1 + code data iter 1 + code hub iter 1, iter 2 모두 PASS) = **6 commit FIX 루프 across 2 repo** |
| ADR-030 amendment | §D7 + §D9 + §D14 VERIFIED 박제 (Phase 2 PR2 본 PR) |
| Epic milestone | **2/7** (MCT-175 + MCT-176 COMPLETED) |
| MCT-175 carry over 처리 | 4/4 (P1-2 + P1-3 + P2-1 + secret 등록 + workflow trigger 복원) |
| MCT-177 carry over | **3건** (YAML loader / signal handler wiring / 6 repo secret read 검증) |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#330, a92e55a)

- `docs/stories/MCT-176.md` — Story §1-§12 신규 (Story file)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D9 + §D14 amendment box 본문 박제 (Phase 1)
- `docs/runbooks/nas-credential-rotation-automation.md` — 신규 (automation layer runbook, manual runbook 위에 추가)
- `CLAUDE.md` — Docker stack 섹션 MCT-176 IN_PROGRESS row 추가 (sequential_phase 2 entry)
- `docs/superpowers/plans/2026-05-15-mct-176-collector-container.md` — 신규 (Phase 1 + Phase 2 PR1 + Phase 2 PR2 plan)

### 1.2 Phase 2 PR1 — data (mctrader-data#64, e3141b6)

- `src/mctrader_data/cli.py` — `effective-config` subcommand 신규 + SIGTERM handler stub (`_register_signal_handlers` + `_SHUTDOWN_REQUESTED` module-level — Story §8 line 226 intentional stub 정합, MCT-177 wiring carry)
- `tests/test_effective_config.py` — 8 신규 unit test (flat `tests/` convention 정합):
  - `test_effective_config_env_override` (env > built-in)
  - `test_yaml_overrides_builtin` (downgrade verify: `source_order=["env","built_in"]` no `yaml_default`)
  - `test_effective_config_default_format_is_json`
  - `test_effective_config_json_format` (valid JSON)
  - `test_format_yaml` (yaml.safe_load round-trip — F-004 P1 fix iter 1)
  - `test_sigterm_handler_registered` (signal.SIGTERM handler 등록 verify, stub)
  - `test_preflight_no_wildcard_fp` (P1-2 carry over verify)
  - `test_rotation_dry_run_exit_0` (P2-1 carry over verify)
- AC-2 PASS verify

### 1.3 Phase 2 PR1 — hub (mctrader-hub#331, 3498a8b)

- `compose.yml` MODIFY — collector service stub 주석 → 실 서비스 정의 활성화. WAL bind mount `/var/lib/mctrader/wal:/var/lib/mctrader/data` (D1) + L1 named volume + `stop_grace_period: 60s` + healthcheck `:8080` + preflight depends_on 연결 + `COMPOSE_PROFILES` 표준 정합 (F-001 P0 fix iter 1)
- `scripts/rotate-nas-credentials.sh` CREATE — 90d rotation 자동화. step 1~5 dry-run + Slack reorder (F-002 P1 fix: step 5 Slack before step 6 revoke) + `.env.prod.bak` trap cleanup (F-003 P1 fix: EXIT/INT/TERM trap `rm -f $ENV_FILE.bak`)
- `scripts/preflight-nas-dns.sh` MODIFY — P1-2 sentinel IP `203.0.113.1` 차단 + P1-3 trap 순서 (cleanup→ERR) + P2-1 `set -euo pipefail` + `bash -n` syntax check
- `.github/workflows/cross-repo-lock-check.yml` MODIFY — `on: pull_request` 트리거 복원 (paths: `**/uv.lock`, workflow, scripts)
- `.gitignore` MODIFY — `.env.*.bak` pattern 등록 (F-003 P1 fix 보완)
- `docs/runbooks/docker-stack-deploy.md` MODIFY — `MCTRADER_CROSS_REPO_TOKEN` GitHub Actions secret 등록 가이드 박제 (Appendix B)
- AC-1/3/4/5 PASS verify

### 1.4 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-176.md` — frontmatter (story_issues 330+64+331+TBD + status COMPLETED + completed_at) + §10 FIX Ledger 9 row (iter 1 design 5 row + iter 1 code 7 row + iter 2 PASS 2 row) + §10.5 Git Ops Log 2 row append + §11 retro_ref + §12 측정 결과 PASS (AC + test + FIX 루프 박제)
- `docs/adr/ADR-030-docker-stack-governance.md` — Amendment box (MCT-176 LAND confirm) — §D7/§D9/§D14 VERIFIED 박제 + Phase 2 PR1 timeline + MCT-175 carry over 처리 결과 + MCT-177 carry over 3 항목
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-176 status COMPLETED + completed_date + prs[] + milestone 2/7 (completed 1→2)
- `CLAUDE.md` — Docker stack 7 Story chain MCT-176 IN_PROGRESS → COMPLETED + §MCT-176 IN_PROGRESS 섹션 → §MCT-176 COMPLETED 전면 재작성
- `docs/retros/RETRO-MCT-176.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-2 박제 (milestone 2/7)

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 collector container inspect | ✓ PASS | `docker compose --profile dev/prod config` exit 0 + collector service 정의 출력 (WAL bind mount + L1 named volume + stop_grace 60s + healthcheck) |
| AC-2 effective-config subcommand | ✓ PASS | `mctrader-data effective-config --format json/yaml` exit 0. `source_order=["env","built_in"]` downgrade (F-005 amendment, MCT-177 carry) |
| AC-3 rotation dry-run | ✓ PASS | `bash scripts/rotate-nas-credentials.sh --dry-run` exit 0 + Slack reorder + `.bak` cleanup trap |
| AC-4 MCT-175 carry over fix verify | ✓ PASS | P1-2 + P1-3 + P2-1 ALL 정합 (sentinel IP 차단 + trap 순서 + `bash -n` + `set -euo pipefail`) |
| AC-5 cross-repo-lock-check workflow trigger 복원 | ✓ PASS | `on: pull_request` 복원 + `MCTRADER_CROSS_REPO_TOKEN` secret 등록 박제 |

### 2.2 INV 박제 (4/4)

| INV | 결과 |
|-----|------|
| INV-1 forward-only (WAL 객체 삭제 금지) | ✓ 박제 — collector container 재시작 후 WAL 기존 파일 유지 verify (ADR-009 §D12 정합) |
| INV-2 WAL fsync (sealed segment 원자적 기록) | stub 박제 — SIGTERM handler stub (MCT-177 본격 구현 carry) |
| INV-3 sha256 SSOT caller-side | ✓ 박제 — `nas_uploader.put_streaming()` 호출 경로 sha256 전달 유지 (MCT-163 INV-3 정합) |
| INV-4 collector RSS peak ≤ 50 MB delta | ✓ 박제 — MCT-163 baseline (0.2 MB / 0.0 MB) 정합, collector container 진입 후 별 측정 = MCT-179 |

### 2.3 Test + 회귀

| 항목 | 결과 |
|------|------|
| Phase 2 PR1 신규 test (data) | 8 ALL PASS |
| 회귀 (data full suite) | **965 passed + 24 skipped + 4 xfailed** (회귀 0, MCT-172 954 baseline 대비 +11 추가) |
| 회귀 (hub) | 14 unit test (MCT-175 `tests/test_check_cross_repo_locks.py`) ALL PASS — secret 등록 후 trigger 복원 회귀 0 |
| ruff + pyright | PASS (FIX iter 1 자동/수동 fix 통과 후 iter 2 clean) |

### 2.4 FIX 루프 (4 iter, 6 commit)

| iter | lane | finding | resolution commit |
|------|------|---------|-------------------|
| 1 | design (Phase 1 hub docs) | P0×1 + P1×2 + P2×2 = 5 (§6.5 §7/§11 N/A 사유 + ADR-030 cron precision + source order precedence + Story §1.1 carry over impact + CLAUDE.md mini-table) | a991279 — 5 fix LAND |
| 1 | code (data Phase 2 PR1) | P1×2 + P2×2 = 4 (F-004 P1 `test_format_yaml` + `test_yaml_overrides_builtin` 누락 / F-005 P1 `source_order` false claim downgrade option B / F-006 P2 `_register_signal_handlers` unwired stub TODO / F-007 P2 `tests/unit/` → `tests/` path drift) | e5a220a — 4 fix LAND |
| 1 | code (hub Phase 2 PR1) | P0×1 + P1×2 = 3 (F-001 P0 `COMPOSE_PROFILE` → `COMPOSE_PROFILES` 표준 / F-002 P1 Slack reorder before revoke / F-003 P1 `.env.prod.bak` trap cleanup) | 2373eee → 0fb4737 — 3 fix LAND |
| 2 | all lanes | — | PASS, Phase 2 PR1 양측 MERGED |

추가 박제 commit: 5212c6f (§8.5 Impl Manifest 박제) + 094243f (phase-gate label re-trigger).

총 **6 commit FIX 루프 across 2 repo** (a991279 + e5a220a + 2373eee + 5212c6f + 0fb4737 + 094243f).

## §3 risks_realized

### 3.1 R-MCT-176-1 (secret leak, HIGH — MCT-175 R1 carry)

- **위협**: `.env.prod` NAS credential 평문 + HTTP-only 전송 + 내부망 패킷 스니핑 / 파일 유출
- **mitigation 적용**:
  - `.env.prod` `.gitignore` (MCT-175 LAND)
  - 90d rotation script LAND (D9 본 Story)
  - rotation 절차에 Slack reorder + `.bak` trap cleanup 박제 (CodeReviewPL FIX P1 fix)
  - NAS firewall IP-allowlist mctrader host only (ADR-027 §D2 carry)
- **realized**: NO — 사용자 explicit accept 유지 (mclayer8865@gmail.com, 2026-05-15)
- **carry over**: MCT-155 TLS cutover 별 Story 백로그 유지

### 3.2 R-MCT-176-2 (rotation script failure, MEDIUM)

- **위협**: `rotate-nas-credentials.sh` 실행 중 Slack webhook 실패 또는 MinIO container down → credential 불일치 + 무통보 outage
- **mitigation 적용**:
  - `set -euo pipefail` + `trap ERR` rollback 절차 박제
  - Slack 실패 시 `gh issue create` 자동 발의
  - `.bak` trap cleanup (EXIT/INT/TERM)
  - dry-run 모드 (`--dry-run`) 의무 사전 검증 (AC-3 PASS)
- **realized**: NO — Phase 2 PR1 LAND 시점 production 실행 0회 (dry-run only)
- **carry over**: 첫 90d 시점 (2026-08-13) production rotation 실행 후 telemetry 박제 의무

### 3.3 R-MCT-176-3 (effective-config false claim, MEDIUM — CodeReviewPL F-005 originated)

- **위협**: `source_order=["env","yaml_default","built_in"]` 광고하나 YAML loader 부재 = false claim → operator 운영 시 YAML override 신뢰 → 실 적용 안 됨
- **mitigation 적용**:
  - **option B 채택** (downgrade): `source_order` → `["env","built_in"]` (false claim 차단)
  - docstring + TODO(MCT-177) 주석 박제
  - Story §7 + AC-2 + §8 amendment 박제 (MCT-177 carry명시)
- **realized**: NO — CodeReviewPL FIX iter 1 시점 차단 (production 미진입)
- **carry over**: MCT-177 YAML loader 신규 + `source_order` 3-tier chain 복원 + AC-2 + §8 amend

### 3.4 R-MCT-176-4 (SIGTERM handler stub unwired, LOW)

- **위협**: Phase 2 PR1 collector service activation 후 SIGTERM 수신 시 graceful drain 미발동 → WAL flush 안 됨 → restart 시 sealed segment 불일치
- **mitigation 적용**:
  - F-006 P2 fix — TODO(MCT-177) 헤더 주석 블록 + docstring 확장 (chunk-boundary polling + non-asyncio entry point wiring 계획 명시)
  - production 미진입 (Phase 2 PR1 = compose config exit 0 verify only, collector 실 기동 = MCT-179 observability LAND 후)
- **realized**: NO — production 미진입
- **carry over**: MCT-177 `_register_signal_handlers` wiring + collect loop chunk boundary polling 통합

## §4 followups (post-Story carry over → MCT-177)

본 Story LAND 후 다음 Story (MCT-177, sequential_phase 3, paper-engine daemon) 진입 시 처리 의무:

### 4.1 MCT-177 carry over 3건 (CodeReviewPL FIX iter 1 결과)

| # | 항목 | 사유 | MCT-177 처리 |
|---|------|------|-------------|
| 1 | YAML config loader 구현 (option A) | F-005 P1 fix option B downgrade — `source_order=["env","built_in"]` (false claim 차단) | YAML loader 신규 + `source_order` → 3-tier chain (env > YAML > built_in) 복원 + AC-2 + §8 test 3-tier amend |
| 2 | `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring | F-006 P2 fix TODO 헤더 + docstring only (Phase 2 PR1 = stub) | non-asyncio entry point (`backfill` / `compact` one-shot) 측 `signal.signal()` 등록 + collect loop chunk boundary 측 `_SHUTDOWN_REQUESTED` polling 통합 |
| 3 | cross-repo-lock-check secret 6 repo 측 secret read 검증 | 현 시점 hub 측 단방향 (`MCTRADER_CROSS_REPO_TOKEN` hub-only) | 6 repo (data / engine / web / market / signal-collector / hub) 측 secret read 의무 검증 후 LAND |

### 4.2 Epic-level carry over (MCT-179 R2 CRITICAL 유지)

- **R2 WAL 30G production measurement**: MCT-172 R-CRITICAL carry over 유지. peak market open 09:00 KST burst 측정 의무 (MCT-179 owner). 30G 초과 시 D11 hard_limit amendment 발의 (FAIL gate).

### 4.3 첫 90d rotation 실행 박제 (post-MCT-176 별 PR)

- 2026-08-13 (production rotation 첫 실행 후) — telemetry quad (.env.prod sha256 + Slack message + git commit + compose restart log) 박제 의무

## §5 lessons (process learnings)

### 5.1 MCT-175 P0 lesson 재적용 효과 (Phase 1 P0 finding 0)

MCT-175 RETRO §8.1 design iter 1 F1 P0 (Story §6.5 Change Plan §7/§11 N/A 사유 부재) 학습을 본 Story Phase 1 진입 시점부터 §6.5 신규 4 entry 작성 → DesignReviewPL Phase 1 iter 1 P0×1만 발생 (5 finding 모두 P1/P2 중심). lesson reapply 효과 검증됨.

### 5.2 cross-repo Phase 2 PR1 LAND order — data 먼저 LAND 후 hub LAND

본 Story 의 Phase 2 PR1 은 cross-repo (data + hub 양측 신규 코드). LAND order는:
1. data#64 MERGED 먼저 (e3141b6, 08:00:41Z) — CLI subcommand + 8 test
2. hub#331 MERGED 후 (3498a8b, 08:04:03Z) — compose.yml 수정 + rotation script

순서 정당성: hub 측 collector service 가 data 측 `effective-config` subcommand 호출 의무 (operator verify hook). data LAND 가 hub LAND prerequisite (역방향 시 false claim). MCT-168/170/172 패턴 정합. MCT-177 이후 cross-repo 양측 동시 LAND 도 동일 order 적용 권고.

### 5.3 false-claim 차단 — option A vs option B 선택 기준

F-005 P1 (`source_order` false claim) fix 시 2개 option 존재:
- option A: YAML loader 즉시 구현 (scope creep, Phase 2 PR1 LAND blocking)
- option B: `source_order` downgrade + TODO + carry over (즉시 차단 + 후속 Story 명시)

**option B 채택** → 후속 Story (MCT-177) 진입 시점에 YAML loader 본격 구현 + 3-tier 복원. 본 Story = "compose 측 service 슬롯 활성화 + rotation + effective-config 골격" scope 정합. 사용자 acknowledged Phase 1 LAND 후 carry over 3 항목 명시.

lesson: false claim 발견 시 downgrade + carry over 가 신뢰 가능한 박제. 즉시 fix 가 scope creep 위협 시 option B 우선.

### 5.4 4 iter FIX 루프 cost (Phase 1 design 1 + Phase 2 code data 1 + code hub 1)

6 commit FIX 루프 (총 4 iter) — MCT-175 의 2 iter 대비 2배. 원인 분석:
- Phase 2 PR1 = cross-repo (data + hub) 양측 → CodeReviewPL 2회 발동 (data 1 + hub 1)
- Phase 1 docs only = design 1회 (P0 lesson reapply 효과로 P0 finding 0, 5 finding 모두 P1/P2)

MCT-177 cross-repo (hub + engine) 동일 패턴 예상 — code FIX iter 1 = 2회 (hub + engine 각 1회). retro/spec 작성 시점에 RETRO-MCT-175 + MCT-176 둘 다 참조 의무.

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#330) — §D9 + §D14 amendment box 본문

- §D9: rotation script path + cron + Slack + failure → GitHub Issue
- §D14: CLI subcommand + source order + operator verify hook

### 6.2 Phase 2 PR2 (본 PR) — §D7 + §D9 + §D14 VERIFIED 박제

- §D7 VERIFIED: preflight collector wiring + MCT-175 carry over fix 3건 (P1-2 + P1-3 + P2-1)
- §D9 VERIFIED: Slack reorder + `.bak` trap cleanup + `.gitignore` pattern
- §D14 VERIFIED: CodeReviewPL FIX iter 1 amendment (option B downgrade) + MCT-177 carry over

ADR-030 본문 만 박제 (Status = Accepted 유지, MCT-175 LAND 시점 박제분). MCT-177 ~ MCT-181 LAND 시 추가 D 본문 박제 의무.

## §7 다음 Story chain

**MCT-177** (paper-engine daemon + SIGTERM graceful + universe override + Redis prefix) — sequential_phase 3.

진입 prerequisite:
1. MCT-176 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. MCT-177 carry over 3 항목 통합 처리 의무:
   - YAML config loader (option A) + `source_order` 3-tier 복원
   - `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring
   - cross-repo-lock-check secret 6 repo 측 secret read 검증
3. ADR-027 §D2 Stage 1 HTTP gate amendment 결정 carry over (R1 HIGH 유지, 사용자 explicit accept 박제분)

채택 결정: D2 (paper daemon + backtest profile 동일 image) + D4 (SIGTERM 60s grace + startup invariant scan) + D10 (universe env↔command override) + D15 (Redis key prefix).

## §8 Cross-ref

- Story: `docs/stories/MCT-176.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-176-collector-container.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (§D7 + §D9 + §D14 VERIFIED 박제)
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (milestone 2/7)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-2 박제)
- automation runbook: `docs/runbooks/nas-credential-rotation-automation.md`
- MCT-175 RETRO (lesson reapply): `docs/retros/RETRO-MCT-175.md`
- Phase 1 PR: mctrader-hub#330 (a92e55a, 2026-05-15) — Story + ADR-030 §D9/§D14 amend + rotation runbook + CLAUDE.md
- Phase 2 PR1 (data): mctrader-data#64 (e3141b6, 2026-05-15T08:00:41Z) — CLI SIGTERM stub + effective-config + 8 test
- Phase 2 PR1 (hub): mctrader-hub#331 (3498a8b, 2026-05-15T08:04:03Z) — collector service 활성화 + rotation script + carry over fix + workflow trigger 복원
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-2)
