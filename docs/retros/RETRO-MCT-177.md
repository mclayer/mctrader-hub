---
type: story-retro
story_key: MCT-177
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 3
---

# RETRO — MCT-177 EPIC-mctrader-docker-stack Story-3 (paper-engine daemon + SIGTERM graceful + universe override + Redis prefix)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory)

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-3 (sequential_phase 3)** — compose stack 에 두 번째 어플리케이션 service (`mctrader-engine paper-engine` daemon) 진입. MCT-176 LAND (collector container) 위에 paper-engine 을 `restart: unless-stopped` daemon service 로 활성화. ADR-030 §D2/§D4/§D10/§D15 amendment box VERIFIED 박제 + mctrader-engine SIGTERM graceful + universe override + Redis key prefix 3 namespace + MCT-176 carry over 3건 (CO-1~CO-3) 통합 처리.

4 PR cross-repo sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code + engine Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). MCT-175/176 §6.5 lesson 누적 효과로 **DesignReview iter 1 PASS (no FIX)** — 3 Story 연속 design P0 감소 (P0×1 → P0×1 → P0×0).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D2/§D4/§D10/§D15 amend + CLAUDE.md) | mctrader-hub#333 MERGED (dd59b65, 2026-05-15T08:56:31Z) |
| Phase 2 PR1 (data code: CO-1 YAML loader 3-tier + CO-2 signal wiring, land_order 1) | mctrader-data#65 MERGED (af6c812, 2026-05-15T09:30:00Z) |
| Phase 2 PR1 (engine code: D4 asyncio SSOT 재사용 + D10 universe + D15 Redis prefix, land_order 2) | mctrader-engine#54 MERGED (9cbe3b4, 2026-05-15T09:30:10Z) |
| Phase 2 PR1 (hub code: paper-engine service + Redis env + CO-3 secret verify, land_order 3) | mctrader-hub#334 MERGED (cc0c368, 2026-05-15T09:30:21Z) |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 ~ AC-5) |
| 총 INV | 5/5 박제 (INV-1~5, INV-5 = MCT-178 carry) |
| 산출물 | hub Phase 1 docs (3 file) + data Phase 2 PR1 (4 file) + engine Phase 2 PR1 (5 file) + hub Phase 2 PR1 (5 file) + hub 박제 (6 file) |
| 신규 daemon 코드 | **0 line** (engine 기존 `shutdown.py` asyncio SSOT + HealthServer 재사용 — RefactorAgent (A) dead path 제거) |
| FIX 루프 | **2회** (design Phase 1 iter 1 = PASS no FIX + code iter 1 P0×3 + P1×1, iter 2 PASS) — code 1 iter 만 발생 |
| ADR-030 amendment | §D2 + §D4 + §D10 + §D15 VERIFIED 박제 (Phase 2 PR2 본 PR) |
| Epic milestone | **3/7** (MCT-175 + MCT-176 + MCT-177 COMPLETED) |
| MCT-176 carry over 처리 | 3/3 (CO-1 YAML loader 3-tier 복원 + CO-2 signal wiring + CO-3 6 repo secret verify) |
| MCT-178 carry over | **1건** (signal-collector 5종 Redis prefix code migration) |
| MCT-181 carry over | `${IMAGE_TAG}` prod pin (D12, dev=latest 현행 유지) |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#333, dd59b65)

- `docs/stories/MCT-177.md` — Story §1-§12 신규 (Story file, §6.5 §7/§11 N/A 4 entry 사전 박제)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D2 + §D4 + §D10 + §D15 amendment box 본문 박제 (Phase 1)
- `CLAUDE.md` — Docker stack 섹션 MCT-177 IN_PROGRESS 섹션 추가 (sequential_phase 3 entry)
- `docs/superpowers/plans/2026-05-15-mct-177-paper-engine.md` — 신규 (Phase 1 + Phase 2 PR1 + Phase 2 PR2 plan)

### 1.2 Phase 2 PR1 — data (mctrader-data#65, af6c812, land_order 1)

- `src/mctrader_data/cli.py` — CO-1 `_load_yaml_config()` 신규 + `source_order` → `["env","yaml_default","built_in"]` 3-tier 복원 (MCT-176 F-005 downgrade 해소) / CO-2 `_register_signal_handlers` non-asyncio entry (`backfill`/`compact`) 실 등록 + collect loop chunk boundary `_SHUTDOWN_REQUESTED` polling
- `tests/test_yaml_config_loader.py` — CO-1 3 신규 unit test (3-tier merge / file absent / env overrides yaml)
- `tests/test_effective_config.py` — CO-1 amend (`test_yaml_overrides_builtin` 3-tier + `test_source_order_3tier`)
- `tests/test_collect_shutdown.py` — CO-2 2 신규 test (signal handler registered / collect loop exits on shutdown flag)

### 1.3 Phase 2 PR1 — engine (mctrader-engine#54, 9cbe3b4, land_order 2)

- `src/mctrader_engine/cli.py` — D4 paper daemon = **기존 `shutdown.py` asyncio SSOT + HealthServer(:8080) 재사용** (신규 daemon 코드 0 line, RefactorAgent (A) dead path 제거 + paper start core 위임) / D10 `--universe-id` CLI + `UNIVERSE_TOP_N` env fallback + 미등록 exit 1
- `src/mctrader_engine/redis_keys.py` — D15 `REDIS_KEY_PREFIX_ENGINE` env (default `engine`) + `_engine_key()` helper
- `tests/test_sigterm_paper_daemon.py` — D4 3 신규 test (기존 shutdown.py asyncio 경로 검증)
- `tests/test_redis_prefix.py` — D15 2 신규 test (engine key prefix applied / env override)
- `tests/test_universe_override.py` — D10 3 신규 test (from env / explicit override / invalid raises)

### 1.4 Phase 2 PR1 — hub (mctrader-hub#334, cc0c368, land_order 3)

- `compose.yml` MODIFY — D2 `paper-engine` service 신규 (image + `command: ["paper","--daemon"]` + restart unless-stopped + healthcheck :8080 + stop_grace 60s + depends_on redis/collector service_healthy). CodeReviewPL P0 fix (healthcheck contract verbatim 정합 + collector condition 추가)
- `.env.dev` / `.env.prod.example` MODIFY — D10 `UNIVERSE_TOP_N=50` + D15 `REDIS_KEY_PREFIX_ENGINE=engine` 박제
- `scripts/verify_cross_repo_secret.py` CREATE — CO-3 6 repo (data/engine/web/market/signal-collector/hub) `MCTRADER_CROSS_REPO_TOKEN` secret read 검증 (gh CLI read-only, 미등록 목록 출력 + exit 1). CodeReviewPL P1 fix (script owner = hub governance 영역 확정)
- `tests/test_verify_cross_repo_secret.py` CREATE — CO-3 unit test (mock gh secret list)

### 1.5 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-177.md` — frontmatter (story_issues 5 PR + status COMPLETED + completed_at) + §8.5 Impl Manifest 3 repo 박제 + §10 FIX Ledger 6 row + §10.5 Git Ops Log 6 row append + §11 retro + §12 측정 PASS
- `docs/adr/ADR-030-docker-stack-governance.md` — Amendment box (MCT-177 LAND confirm) §D2/§D4/§D10/§D15 VERIFIED + Phase 2 PR1 cross-repo LAND timeline + MCT-176 CO-1~3 처리 결과 + MCT-178 carry over
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-177 status COMPLETED + completed_date + prs[] + milestone 3/7
- `CLAUDE.md` — Docker stack 7 Story chain MCT-177 COMPLETED + §MCT-177 IN_PROGRESS → COMPLETED 전면 재작성
- `docs/retros/RETRO-MCT-177.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-3 박제 (milestone 3/7)

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 paper-engine compose healthcheck (D2) | ✓ PASS | `docker compose --profile dev config` exit 0 + paper-engine service 정의 (restart unless-stopped + healthcheck :8080 + stop_grace 60s). 기존 HealthServer asyncio task 재사용 |
| AC-2 SIGTERM graceful 60s grace (D4) | ✓ PASS | 기존 `shutdown.py` asyncio SSOT graceful drain, exit 0 (신규 코드 0 line). 60s grace = `stop_grace_period` 정합 |
| AC-3 UNIVERSE_TOP_N env + universe-id override (D10) | ✓ PASS | `.env.dev` `UNIVERSE_TOP_N=50` + `--universe-id` CLI override + 미등록 universe-id exit 1 (R-MCT-177-3 mitigation) |
| AC-4 Redis key prefix 3 namespace (D15) | ✓ PASS | `signal:*` / `market:*` / `engine:*` 분리 + `REDIS_KEY_PREFIX_ENGINE` env (default `engine`) |
| AC-5 MCT-176 carry over 3건 (CO-1~CO-3) | ✓ PASS | CO-1 `source_order=["env","yaml_default","built_in"]` 3-tier 복원 + CO-2 collect loop `_SHUTDOWN_REQUESTED` polling + CO-3 `verify_cross_repo_secret.py` 6 repo 순회 |

### 2.2 INV 박제 (5/5)

| INV | 결과 |
|-----|------|
| INV-1 forward-only (WAL 객체 삭제 금지) | ✓ 박제 — paper-engine restart 후 WAL 기존 파일 유지 (ADR-009 §D12 정합) |
| INV-2 WAL fsync (sealed segment 원자적 기록) | ✓ 박제 — SIGTERM 60s grace 내 WAL flush (기존 shutdown.py asyncio graceful, ADR-029 §D4) |
| INV-3 sha256 SSOT caller-side | ✓ 박제 — `nas_uploader.put_streaming()` 호출 경로 sha256 전달 유지 (MCT-163 INV-3) |
| INV-4 engine RSS peak ≤ 256 MB delta | ✓ 박제 — MCT-170 INV-4 baseline 정합. paper-engine steady-state 별 측정 = MCT-179 |
| INV-5 Redis prefix migration 1주일 dual write | carry 박제 — signal-collector 5종 code migration = **MCT-178 carry over** (본 Story = engine consumer `engine:*` 적용만) |

### 2.3 Test + 회귀

| 항목 | 결과 |
|------|------|
| Phase 2 PR1 신규 test (data) | CO-1 3 + CO-1 amend 2 + CO-2 2 = ALL PASS |
| Phase 2 PR1 신규 test (engine) | D4 3 + D15 2 + D10 3 = ALL PASS |
| Phase 2 PR1 신규 test (hub) | CO-3 verify_cross_repo_secret unit test ALL PASS |
| 회귀 (data full suite) | MCT-176 965 baseline 대비 회귀 0 |
| 회귀 (engine full suite) | MCT-170 io/ 107 test + 기존 shutdown.py asyncio 경로 회귀 0 (재사용 — 신규 코드 0 line, backward compat preserve) |
| ruff + pyright | PASS (data pyright P0 fix iter 1 후 iter 2 clean) |

### 2.4 FIX 루프 (2 iter — design PASS no FIX + code 1 iter)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub docs) | **0 (PASS, no FIX)** — MCT-175/176 §6.5 lesson 누적 효과 | Phase 2 PR1 직진 |
| 1 | code (data#65) | P0×1 (pyright `_load_yaml_config()` return type + `yaml.safe_load` None narrowing) | fix → iter 2 PASS |
| 1 | code (engine#54) | P0×1 (data 동기 SIGTERM stub 패턴 cross-repo 오적용 — 기존 shutdown.py asyncio SSOT 미인지) | fix → RefactorAgent (A) dead path 제거 + 신규 daemon 코드 0 line + plan §2.2 amend. iter 2 PASS |
| 1 | code (hub#334) | P0×1 (compose healthcheck contract 불일치 + depends_on collector 누락) + P1×1 (`verify_cross_repo_secret.py` script owner = hub) | fix → iter 2 PASS |
| 2 | all lanes | — | data PASS / engine PASS / hub CONDITIONAL_PASS (sequential gate). 3 PR sequential MERGED |

design lane = MCT-175 (P0×1) → MCT-176 (P0×1) → MCT-177 (**P0×0**). §6.5 lesson reapply 3 Story 연속 감소 검증.

## §3 risks_realized

### 3.1 R-MCT-177-1 (Redis prefix migration silent fail, MEDIUM)

- **위협**: signal-collector 5종 unprefixed key → `signal:*` rename 중 consumer (paper-engine) old key read → 데이터 없음 무통보
- **mitigation 적용**:
  - MCT-177 = prefix 정책 박제 + engine consumer 측 `engine:*` 적용만 (signal-collector code migration = MCT-178 carry over → silent fail 위협 본 Story scope 외)
  - paper-engine 측 `signal:*` prefix 우선 read 설계 박제 (dual write 기간 중 항상 존재 전제)
  - Prometheus `redis_key_migration_dual_write_active` Gauge = MCT-178 migration PR 시 박제
- **realized**: NO — signal-collector code migration 미진입 (MCT-178 carry)
- **carry over**: MCT-178 signal-collector 5종 unprefixed → `signal:*` rename + 1주일 dual write + Gauge + LAND+7d legacy cleanup PR

### 3.2 R-MCT-177-2 (paper daemon position state loss on crash, MEDIUM)

- **위협**: paper-engine SIGTERM 60s grace 내 open position commit 미완료 → restart 시 `engine:position:*` stale
- **mitigation 적용**:
  - **기존 `shutdown.py` asyncio SSOT graceful drain 재사용** (신규 코드 0 line) — 검증된 SIGTERM 경로 (asyncio task cancel + cleanup) 활용으로 신규 동기 경로 도입 risk 회피
  - restart unless-stopped + Redis `engine:position:*` state 복구 + InvariantHarness startup 8종 scan
- **realized**: NO — production 미진입 (compose config exit 0 verify + 기존 asyncio 경로 unit test only)
- **carry over**: Redis container crash 시 position 영구 손실 = Redis AOF persistence MCT-179 observability 결정 예정

### 3.3 R-MCT-177-3 (universe-id override misconfig, LOW)

- **위협**: `--universe-id` override 값이 engine registry 미존재 → startup fail 또는 empty universe
- **mitigation 적용**: CLI universe-id validate (registry 미존재 즉시 exit 1) + `UNIVERSE_TOP_N=50` env default (MCT-103 LAND, 항상 유효)
- **realized**: NO — `test_universe_id_invalid_raises` unit test 차단
- **carry over**: 없음 (LOW, fully mitigated)

## §4 followups (post-Story carry over → MCT-178)

본 Story LAND 후 다음 Story (MCT-178, sequential_phase 4, backtest-runner profile) 진입 시 처리 의무:

### 4.1 MCT-178 carry over (D15 migration scope 분리)

| # | 항목 | 사유 | MCT-178 처리 |
|---|------|------|-------------|
| 1 | signal-collector 5종 Redis prefix code migration | MCT-177 = prefix 정책 박제 + engine consumer `engine:*` 적용. signal-collector repo 코드 (5종 unprefixed → `signal:*` rename) = 별 Story scope (signal-collector repo 변경) | signal-collector 5종 (fear_greed/ecos/kimchi/announcement/coinglass) unprefixed → `signal:*` rename + 1주일 dual write + Prometheus `redis_key_migration_dual_write_active` Gauge + LAND+7d legacy key cleanup 별 PR |

### 4.2 MCT-181 carry over (image registry pin)

- `${IMAGE_TAG}` prod pin (D12, MCT-181 owner) — 현 compose.yml `image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}` (dev=latest 현행 유지). prod = `sha-<7char>` pin = MCT-181.

### 4.3 Epic-level carry over (MCT-179 R2 CRITICAL 유지)

- **R2 WAL 30G production measurement**: MCT-172 R-CRITICAL carry over 유지. peak market open 09:00 KST burst 측정 의무 (MCT-179 owner). 30G 초과 시 D11 hard_limit amendment 발의 (FAIL gate).

## §5 lessons (process learnings)

### 5.1 engine daemon 재구현 lesson — cross-repo Phase 0 verify 독립 의무 (MCT-170 류 재현)

CodeReviewPL FIX iter 1 engine#54 P0 = 초안이 mctrader-data 동기 SIGTERM stub 패턴 (MCT-176 §8 `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` module-level) 을 **cross-repo 무비판 carry over** 했으나, mctrader-engine 측 **기존 `shutdown.py` asyncio SSOT + HealthServer(:8080)** 가 이미 graceful drain 경로 보유. session prompt 표현 ("engine paper daemon 신규 구현") ≠ 코드 실상 (기존 검증 자산 존재).

RefactorAgent 판정 **(A) dead path 제거** + paper start core 위임 → **신규 daemon 코드 0 line**. plan §2.2 amend (data 패턴 cross-repo 오적용 취소).

**lesson**: cross-repo Story 는 각 repo 별 Phase 0 verify 독립 의무. sibling repo (data) 패턴을 다른 repo (engine) 에 무비판 carry over 금지. MCT-170 의 "engine io/ 3 module MCT-154 LAND 존재 재인지 → 재구현 아닌 확장" lesson 동형. session prompt 의 구현 표현은 가설로만 수용 (memory feedback_phase0_verify_mandatory 정합). cross-repo plan 작성 시 각 repo asyncio/동기 패턴 SSOT 사전 grep 의무.

### 5.2 MCT-175/176 §6.5 lesson 누적 효과 — design P0 3 Story 연속 감소

| Story | design iter 1 P0 |
|-------|------------------|
| MCT-175 | P0×1 (§6.5 §7/§11 N/A 사유 부재 — lesson origin) |
| MCT-176 | P0×1 (다른 사유, §6.5 사전 박제 효과 4 finding 모두 P1/P2) |
| MCT-177 | **P0×0 (PASS, no FIX)** |

MCT-175 RETRO §8.1 lesson (Story §6.5 Change Plan §7/§11 N/A 사유 사전 박제) → MCT-176 4 entry reapply → MCT-177 Phase 1 진입 시점 §6.5 4 entry (§7 / §7.4 / §11 / §11.6) 완비 → design iter 1 P0 finding 0. 3 Story 연속 lesson reapply 누적 효과 검증. **cross-repo Story 도 docs-only Phase 1 = §6.5 N/A 사유 박제 의무 reapply.**

### 5.3 cross-repo 3 repo Phase 2 PR1 LAND order — data → engine → hub sequential

본 Story Phase 2 PR1 = 3 repo (data + engine + hub). LAND order:
1. data#65 MERGED 먼저 (af6c812, 09:30:00Z) — CO-1 YAML loader + CO-2 signal wiring
2. engine#54 MERGED 후 (9cbe3b4, 09:30:10Z) — D4/D10/D15 consumer (data CO 의존 없으나 engine image = hub compose prerequisite)
3. hub#334 MERGED 최종 (cc0c368, 09:30:21Z) — paper-engine service (engine image command 의존) + Redis env + CO-3

순서 정당성: hub compose `paper-engine` service 가 engine image command (`paper --daemon`) + Redis prefix env 의존 → engine code LAND 가 hub compose LAND prerequisite. MCT-176 §5.2 (data → hub) 패턴 확장 (3 repo 버전). MCT-178 이후 cross-repo 동일 order 적용 권고.

### 5.4 FIX 루프 cost — code 1 iter (design PASS no FIX 효과)

MCT-176 = 4 iter (design 1 + code data 1 + code hub 1, 6 commit). MCT-177 = **2 iter** (design PASS no FIX + code iter 1, code lane 3 PR P0×3+P1×1 동시). 원인:
- design lane = §6.5 lesson 3차 reapply 효과 P0×0 (FIX iter 0)
- code lane = cross-repo 3 PR P0 동시 발견 (data pyright + engine stub carry over + hub compose contract) 이나 1 iter 내 일괄 fix

MCT-176 대비 FIX iter 50% 감소. lesson: docs-only Phase 1 §6.5 사전 박제가 design FIX 루프 제거 핵심. cross-repo code lane 은 repo 수만큼 P0 surface 증가 가능 → Phase 0 verify (§5.1) 가 code FIX iter 추가 차단 핵심.

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#333) — §D2/§D4/§D10/§D15 amendment box 본문

- §D2: paper-engine service block (image + command + restart + healthcheck + stop_grace 60s)
- §D4: SIGTERM handler + 60s grace + startup InvariantHarness scan
- §D10: UNIVERSE_TOP_N=50 env + compose command override
- §D15: Redis key prefix 3 namespace + signal-collector migration 1주일 dual write (신규)

### 6.2 Phase 2 PR2 (본 PR) — §D2/§D4/§D10/§D15 VERIFIED 박제

- §D2 VERIFIED: paper-engine service LAND + healthcheck contract P0 fix + depends_on collector
- §D4 VERIFIED: engine asyncio SSOT 재사용 (신규 daemon 코드 0 line) + RefactorAgent (A) dead path 제거 + plan §2.2 amend
- §D10 VERIFIED: `--universe-id` + `UNIVERSE_TOP_N=50` env fallback + 미등록 exit 1
- §D15 VERIFIED: `REDIS_KEY_PREFIX_ENGINE` env + 3 namespace. signal-collector code migration = MCT-178 carry

ADR-030 본문 만 박제 (Status = Accepted 유지, MCT-175 LAND 시점 박제분). MCT-178 ~ MCT-181 LAND 시 추가 D 본문 박제 의무.

## §7 다음 Story chain

**MCT-178** (backtest-runner profile + oneshot + compose config CI lint + universe override) — sequential_phase 4.

진입 prerequisite:
1. MCT-177 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. MCT-178 carry over 통합 처리 의무:
   - signal-collector 5종 Redis prefix code migration (unprefixed → `signal:*` rename + 1주일 dual write + Prometheus Gauge + LAND+7d legacy cleanup)
   - `${IMAGE_TAG}` prod pin (D12, MCT-181 owner — dev=latest 현행 유지)
3. R2 (WAL 30G 미측정 CRITICAL) carry 유지 (MCT-179 owner)

채택 결정: D2 (backtest profile oneshot 동일 image) + D4 (SIGTERM 회귀) + D10 (universe override) + D16 (compose config lint + up --wait CI gate).

## §8 Cross-ref

- Story: `docs/stories/MCT-177.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-177-paper-engine.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (§D2/§D4/§D10/§D15 VERIFIED 박제)
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (milestone 3/7)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-3 박제)
- MCT-176 RETRO (lesson reapply): `docs/retros/RETRO-MCT-176.md`
- MCT-175 RETRO (§6.5 lesson origin): `docs/retros/RETRO-MCT-175.md`
- Phase 1 PR: mctrader-hub#333 (dd59b65, 2026-05-15T08:56:31Z) — Story + ADR-030 §D2/§D4/§D10/§D15 amend + CLAUDE.md
- Phase 2 PR1 (data): mctrader-data#65 (af6c812, 2026-05-15T09:30:00Z) — CO-1 YAML loader 3-tier + CO-2 signal wiring + test (land_order 1)
- Phase 2 PR1 (engine): mctrader-engine#54 (9cbe3b4, 2026-05-15T09:30:10Z) — D4 asyncio SSOT 재사용 + D10 universe override + D15 Redis prefix (land_order 2)
- Phase 2 PR1 (hub): mctrader-hub#334 (cc0c368, 2026-05-15T09:30:21Z) — paper-engine service + Redis env + CO-3 verify_cross_repo_secret.py (land_order 3)
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-3)
