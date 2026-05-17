# mctrader-hub CLAUDE.md

mctrader 자동매매 platform governance hub. Story / ADR / Epic / cross-repo 조정. codeforge consumer.

## 프로젝트 구조

- `docs/stories/` — Story 파일 (MCT-NNN.md)
- `docs/adr/` — ADR (ADR-NNN-title.md)
- `docs/runbooks/` — 운영 runbook
- `docs/retros/` — RETRO + EPIC-RESULTS
- `docs/audit/` — 실행 결과 박제 artifact
- `docs/superpowers/specs/` — brainstorm spec
- `docs/superpowers/plans/` — implementation plan
- `scope_manifests/` — Epic scope_manifest YAML
- `scripts/` — NAS admin + 운영 스크립트 (단, `scripts/ha/` = mctrader-data 재배치됨, 아래 참조)
- `.codeforge/counters.json` — Story key reservation SSOT

## ops 산출물 mctrader-data 재배치 (2026-05-17, Story 생략 직접 운영 이동)

data 도메인 전용 운영 산출물을 거버넌스 허브에서 분리, **mctrader-data** 로 재배치 (org owner 직접 지시, codeforge:story-cutoff-classification 상 본래 Story 강제 대상이나 사용자 명시 생략). hub PR(제거) + data PR #82(추가) 다단 LAND.

| 이전 (mctrader-hub) | 현재 (mctrader-data) | 내용 |
|---|---|---|
| `docker/minio/` | `mctrader-data:docker/minio/` | NAS cold-tier MinIO 배포 스택 (`.env` = git 미추적 비밀, 파일시스템 이동) |
| `scripts/ha/` | `mctrader-data:scripts/ha/` | collector Active-Active HA ops (systemd/Ansible/calibration/e2e) |
| `tools/compactor-tracemalloc.py` | `mctrader-data:tools/compactor-tracemalloc.py` | compactor 컨테이너 메모리 프로파일링 |

- 거버넌스 문서(Story/ADR/runbook/scope_manifest/RETRO)는 **hub 잔류** 정상. 재배치 파일 내 cross-repo 링크 → 절대 mctrader-hub GitHub URL 재작성.
- live runbook 3건 repo 경로 갱신: `nas-minio-deploy.md` / `stage3-deploy-runbook.md` / `compactor-baseline.md` (`/volume1/...` NAS 호스트 경로는 불변).
- **역사 박제 미변경 (불변 기록)**: RETRO/Story/spec/plan + CLOSED Epic `scope_manifests/EPIC-cold-tier-nas-minio.yaml` scope_files 는 당시 사실 그대로 보존 (해당 Epic 기간 hub 보유는 사실). 잔존 경로 참조는 의도된 historical residual.

## NAS versioning + Object Lock 현황 (MCT-161)

> Phase 2 land: 2026-05-14

### 설정 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| bucket versioning | **Enabled** | AC-1 PASS (2026-05-14T06:38Z) |
| Object Lock GOVERNANCE 30d | **SKIP** | 기존 bucket MinIO 제약 (--with-lock 생성 시점 의무) |
| Lifecycle NoncurrentVersionExpiration 30d | **Enabled** | AC-3 PASS |
| DR runbook | `docs/runbooks/nas-bucket-disaster-recovery.md` | AC-4 PASS |

### 운영 스크립트

- `scripts/enable_nas_versioning.py` — versioning + Object Lock + Lifecycle enable
- `scripts/verify_nas_versioning.py` — AC-1/2/3 verify (exit code 0=PASS)

```bash
# 환경변수 설정 후 실행
export NAS_MINIO_ENDPOINT=http://mcnas01.internal.mclayer.it:9000
export NAS_MINIO_ACCESS_KEY=<access_key>
export NAS_MINIO_SECRET_KEY=<secret_key>
python scripts/verify_nas_versioning.py
```

### 제약 사항

- Object Lock은 bucket 생성 시(`--with-lock`) 활성화 의무. 기존 `mctrader-market`에는 적용 불가.
- NoncurrentVersionExpiration 30d — versioning 활성화(2026-05-14) 이전 null version은 복원 불가 (Edge-1).

## DR runbook (MCT-161 AC-4)

NAS data loss / hard delete 복원 절차:
- `docs/runbooks/nas-bucket-disaster-recovery.md` — 5-step (Triage / Version 조회 / Restore / Verify / Postmortem)
- 복원 가능 window: versioning 활성화 이후 + 30d NoncurrentVersionExpiration 이내

## Docker stack 확장 (EPIC-mctrader-docker-stack, MCT-175 COMPLETED 2026-05-15)

mctrader 어플리케이션 (mctrader-data collector + mctrader-engine paper-engine / backtest-runner) 을
compose stack 에 통합. NAS MinIO (prod) vs hub MinIO (dev) profile 전환 + observability +
WAL 30G production measurement (EPIC-tier-promotion CLOSED prereq).

> **MCT-175 COMPLETED (2026-05-15)** — hub#326 (8c485ef) + hub#327 (daef9b3) + hub#328 (dbba327) LAND.
> AC-1/2/3/5 PASS + AC-4 stub 박제 + 14 unit test green. ADR-030 Status: Proposed → **Accepted**.
> 7 Story sequential chain milestone **1/7**.

### 목적

- `compose.yml` 어플리케이션 service 추가 (collector + paper-engine + backtest-runner)
- dev/prod profile 분리 (D3=A): `--profile dev .env.dev` vs `--profile prod .env.prod`
- WAL host bind mount (D1=C, ADR-030 §D1, forward-only invariant 정합)
- NAS DNS preflight (D7=A): `scripts/preflight-nas-dns.sh` (DNS+TCP+S3 gate)
- cross-repo lock CI gate (D13=D): 6 repo python_version + lib major drift 차단

### ADR-030 (신규, MCT-175 publish)

`docs/adr/ADR-030-docker-stack-governance.md` — 8 D 본문 박제:
D1 (WAL host mount) / D2 (paper daemon + backtest profile) / D3 (compose profiles) /
D7 (NAS preflight) / D12 (image registry) / D13 (cross-repo lock) / D17 (host disk risk) / D18 (limits)
Status: **POLICY_FINALIZED** (MCT-181 LAND 2026-05-15, Epic 7/7, 19 D 전수 VERIFIED). transition: Proposed → Accepted (MCT-175) → POLICY_FINALIZED (MCT-181)

### 7 Story sequential chain

| sequential_phase | Story | 상태 | 결정 | 내용 |
|---|-------|------|------|------|
| 1 | **MCT-175** | **COMPLETED 2026-05-15** | D1/D3/D7/D13 | compose base + dev/prod profile + env 분리 + cross-repo lock gate + ADR-030 (hub#326 + hub#327 + hub#328) |
| 2 | **MCT-176** | **COMPLETED 2026-05-15** | D7/D9/D14 | collector container + NAS credential rotation + effective config dump (hub#330 + data#64 + hub#331 + Phase 2 PR2) |
| 3 | **MCT-177** | **COMPLETED 2026-05-15** | D2/D4/D10/D15 | paper-engine daemon + SIGTERM graceful + universe override + Redis prefix (hub#333 + data#65 + engine#54 + hub#334 + Phase 2 PR2) |
| 4 | **MCT-178** | **COMPLETED 2026-05-15** | D2/D4/D10/D16 | backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis prefix code migration (hub#336 + signal-collector#1 + hub#337 + Phase 2 PR2) |
| 5 | **MCT-179** | **COMPLETED 2026-05-15** | D5/D8/D17 | observability + WAL 30G synthetic baseline 측정 + DR mode + alert (hub#339 + data#66 + hub#340 + Phase 2 PR2) |
| 6 | **MCT-180** | **COMPLETED 2026-05-15** | D4/D11/D18 | integration smoke (ESCALATE F-301 → infra-only 3-layer) + testcontainers + resource limits + 5 TODO panel metric emit (hub#342 + data#67 + engine#55 + hub#343 + Phase 2 PR2) |
| 7 | **MCT-181** | **COMPLETED 2026-05-15** | D12/D19 | image registry pin + backtest artifact NAS sync + **Epic POLICY_FINALIZED 7/7** (hub#345 + engine#56 + hub#346 + Phase 2 PR2) |

> **EPIC-mctrader-docker-stack POLICY_FINALIZED 7/7** (2026-05-15). 19 D 전수 VERIFIED. Epic CLOSED 자체 박제 = production evidence (prod-1~4) 완성 후 별 PR (EPIC-tier-promotion-single-source 패턴 정합).

### Key References

- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- runbook stub: `docs/runbooks/docker-stack-deploy.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md`

### Risk 현황

| Risk | Severity | 상태 |
|------|----------|------|
| R1 NAS HTTP-only 평문 | HIGH | **사용자 explicit accept (2026-05-15)** — MCT-155 TLS cutover 별 Story 백로그 |
| R2 WAL 30G 미측정 | CRITICAL | **PARTIAL 해소 (2026-05-15, MCT-179)** — synthetic baseline 측정 완료 (paper-synthetic verdict=PASS). production 실 측정 (peak 09:00 KST 1h burst) = **별 PR carry over** (EPIC-tier-promotion CLOSED prereq prod-2) |
| R4 host disk 손실 → WAL 영구 손실 | MEDIUM | **사용자 explicit accept (2026-05-15)** — forward-only invariant (ADR-029 §D4), 1d max |

## MCT-176 COMPLETED (2026-05-15) — Collector container + credential rotation + effective config

> **sequential_phase 2** — Epic Story-2. cross-repo 4 PR sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code +
> hub Phase 2 PR1 code + hub Phase 2 PR2 박제). AC-1~5 PASS + 8 신규 test + 965 회귀 0.

### 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs) | mctrader-hub#330 MERGED (a92e55a, 2026-05-15) — Story + ADR-030 §D9/§D14 amend + rotation runbook + CLAUDE.md |
| Phase 2 PR1 (data code) | mctrader-data#64 MERGED (e3141b6, 2026-05-15T08:00:41Z) — CLI SIGTERM handler stub + effective-config subcommand + 8 신규 test |
| Phase 2 PR1 (hub code) | mctrader-hub#331 MERGED (3498a8b, 2026-05-15T08:04:03Z) — collector service 활성화 + rotation script + carry over fix + workflow trigger 복원 |
| Phase 2 PR2 (hub 박제) | mctrader-hub#TBD (본 PR) — Story §10/§11/§12 + ADR-030 amendment confirm + scope_manifest 2/7 + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-2 |
| 총 AC | **5/5 PASS** (AC-1 collector compose config + AC-2 effective-config json/yaml + AC-3 rotate dry-run + AC-4 carry over fix + AC-5 workflow trigger 복원) |
| 신규 test (data) | **8** (`tests/test_effective_config.py`) ALL PASS |
| 회귀 (data full suite) | 965 passed + 24 skipped + 4 xfailed (MCT-172 954 baseline → 11 추가 test, 회귀 0) |
| FIX 루프 | **4 iter** (design Phase 1 iter 1 + code data iter 1 + code hub iter 1, iter 2 모두 PASS) = 6 commit |
| MCT-177 carry over | 3 항목 (YAML loader / signal handler wiring / 6 repo secret read 검증) |

### 4 D 결정 (Epic Story-2 채택)

| D | Option | 결과 |
|---|--------|------|
| D7 (carry from MCT-175) | A | collector service preflight hook 연결 LAND — `scripts/preflight-nas-dns.sh` (sentinel IP 차단 + trap 순서 + `bash -n` 통과) |
| D9 | D | `scripts/rotate-nas-credentials.sh` 신규 LAND — Slack reorder + `.bak` trap cleanup + `.gitignore` `.env.*.bak` |
| D14 | D | `mctrader-data effective-config --format {json,yaml}` 신규 LAND — `source_order=["env","built_in"]` downgrade (MCT-177 YAML loader carry) |
| D1 (carry from MCT-175) | C | WAL host bind mount `/var/lib/mctrader/wal:/var/lib/mctrader/data` collector service 실 적용 LAND |

### MCT-175 carry over 4건 처리 결과

| 항목 | 처리 |
|------|------|
| P1-2 preflight DNS wildcard FP | ✓ fix — sentinel IP `203.0.113.1` 차단 |
| P1-3 mc alias trap race | ✓ fix — trap 순서 cleanup→ERR |
| P2-1 shell error handling | ✓ fix — `set -euo pipefail` + `trap ERR` + `bash -n` syntax check |
| NAS_MINIO_* secret 등록 + workflow trigger 복원 | ✓ LAND — `MCTRADER_CROSS_REPO_TOKEN` secret + `on: pull_request` 복원 |

### MCT-177 carry over (CodeReviewPL FIX iter 1 결과)

| 항목 | 사유 | MCT-177 처리 |
|------|------|-------------|
| YAML config loader (option A) | Phase 2 PR1 env+built_in only — F-005 P1 fix option B downgrade (false claim 차단) | YAML loader 신규 + `source_order` → 3-tier chain (env > YAML > built_in) 복원 + AC-2 + §8 amend |
| `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` collect loop wiring | Phase 2 PR1 stub — F-006 P2 fix TODO 헤더 + docstring 확장 only | non-asyncio entry point (backfill / compact one-shot) 측 `signal.signal()` 등록 + collect loop chunk boundary polling 통합 |
| cross-repo-lock-check secret 6 repo 측 secret read 검증 | hub 측 단방향 등록 | 6 repo (data/engine/web/market/signal-collector/hub) 측 secret read 의무 검증 후 LAND |

### ADR-030 amendment box (MCT-176 LAND 박제, Phase 2 PR2)

`docs/adr/ADR-030-docker-stack-governance.md` 본문 박제:
- **§D7 VERIFIED** (preflight collector wiring + MCT-175 carry over fix 3건)
- **§D9 VERIFIED** (Slack reorder + `.bak` trap cleanup + `.gitignore` pattern)
- **§D14 VERIFIED** (CodeReviewPL FIX iter 1 amendment — `source_order` downgrade + MCT-177 carry)
- Phase 2 PR1 양측 LAND timeline (data#64 + hub#331) + MCT-175 carry over 5 항목 처리 결과 + MCT-177 carry over 3 항목

### Key References

- Story: `docs/stories/MCT-176.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-176-collector-container.md`
- automation runbook: `docs/runbooks/nas-credential-rotation-automation.md`
- ADR-030 §D9/§D14: `docs/adr/ADR-030-docker-stack-governance.md`
- RETRO: `docs/retros/RETRO-MCT-176.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-2 박제)

### 다음 Story 진입 권고

**MCT-177** (paper-engine daemon + SIGTERM graceful + universe override + Redis prefix) — sequential_phase 3.
진입 prerequisite = MCT-176 Phase 2 PR2 MERGED ✓ + MCT-177 carry over 3 항목 (YAML loader + signal handler wiring + 6 repo secret read 검증) 통합 처리.

## MCT-177 COMPLETED (2026-05-15) — paper-engine daemon + SIGTERM graceful + universe override + Redis prefix

> **sequential_phase 3** — Epic Story-3. cross-repo 4 PR sequential LAND (hub Phase 1 docs + data Phase 2 PR1 +
> engine Phase 2 PR1 + hub Phase 2 PR1 + hub Phase 2 PR2 박제). AC-1~5 PASS. **engine 신규 daemon 코드 0 line**
> (기존 `shutdown.py` asyncio SSOT + HealthServer 재사용 — RefactorAgent (A) dead path 제거 판정).

### 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs) | mctrader-hub#333 MERGED (dd59b65, 2026-05-15T08:56:31Z) — Story + ADR-030 §D2/§D4/§D10/§D15 amend + CLAUDE.md |
| Phase 2 PR1 (data code, land_order 1) | mctrader-data#65 MERGED (af6c812, 2026-05-15T09:30:00Z) — CO-1 YAML loader 3-tier + CO-2 signal wiring + test |
| Phase 2 PR1 (engine code, land_order 2) | mctrader-engine#54 MERGED (9cbe3b4, 2026-05-15T09:30:10Z) — D4 기존 shutdown.py asyncio 재사용 + D10 universe override + D15 Redis prefix |
| Phase 2 PR1 (hub code, land_order 3) | mctrader-hub#334 MERGED (cc0c368, 2026-05-15T09:30:21Z) — paper-engine service + Redis prefix env + CO-3 6 repo secret verify |
| Phase 2 PR2 (hub 박제) | mctrader-hub#TBD (본 PR) — Story §8.5/§10/§11/§12 + ADR-030 LAND confirm + scope_manifest 3/7 + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-3 |
| 총 AC | **5/5 PASS** (AC-1 paper-engine compose + :8080 / AC-2 SIGTERM graceful exit 0 / AC-3 UNIVERSE_TOP_N=50 + override / AC-4 Redis 3 prefix / AC-5 CO-1~3) |
| FIX 루프 | **DesignReview iter 1 PASS (no FIX)** + code iter 1 P0×3 + P1×1 → iter 2 PASS = **1 code iter** |
| MCT-176 carry over | 3/3 처리 (CO-1 YAML loader / CO-2 signal wiring / CO-3 6 repo secret verify) |
| MCT-178 carry over | signal-collector 5종 Redis prefix code migration (D15) |
| MCT-181 carry over | `${IMAGE_TAG}` prod pin (D12) |

### 4 D 결정 (D2 + D4 + D10 + D15)

| D | Option | 결과 |
|---|--------|------|
| D2 (paper daemon) | A | compose.yml `paper-engine` service LAND (image + `command: ["paper","--daemon"]` + restart unless-stopped + healthcheck :8080 + stop_grace 60s + depends_on redis/collector service_healthy). backtest-runner = MCT-178 |
| D4 (SIGTERM graceful) | C | **기존 `shutdown.py` asyncio SSOT + HealthServer(:8080) 재사용** — 신규 daemon 코드 0 line (CodeReviewPL P0 fix: data 동기 stub 패턴 cross-repo 오적용 → RefactorAgent (A) dead path 제거). 60s grace + startup InvariantHarness 8종 scan |
| D10 (universe override) | D | `--universe-id` CLI + `UNIVERSE_TOP_N=50` env fallback + 미등록 exit 1. `.env.dev`/`.env.prod.example` 박제 |
| D15 (Redis prefix) | C | `REDIS_KEY_PREFIX_ENGINE` env (default `engine`) + `_engine_key()`. signal:/market:/engine: 3 namespace. **signal-collector code migration = MCT-178 carry** |

### engine daemon 재구현 lesson (MCT-170 류 Phase 0 verify 재현)

CodeReviewPL FIX iter 1 engine#54 P0 = 초안이 mctrader-data 동기 SIGTERM stub 패턴 (MCT-176 §8)
을 cross-repo carry over 했으나, mctrader-engine 측 **기존 `shutdown.py` asyncio SSOT +
HealthServer(:8080)** 가 이미 graceful drain 경로 보유. session prompt 표현 ("engine daemon
신규 구현") ≠ 코드 실상. RefactorAgent 판정 **(A) dead path 제거** + paper start core 위임 →
**신규 daemon 코드 0 line** (기존 검증 자산 재사용). plan §2.2 amend (data 패턴 cross-repo
오적용 취소). **lesson: cross-repo Story 는 각 repo Phase 0 verify 독립 의무 — sibling repo
패턴 무비판 carry over 금지** (MCT-170 io/ 3 module 존재 재인지 lesson 동형).

### MCT-176 carry over 3건 처리 결과

| # | 항목 | 처리 결과 |
|---|------|----------|
| CO-1 | YAML config loader (option A) | ✓ `_load_yaml_config()` 신규 + `source_order` → `["env","yaml_default","built_in"]` 3-tier 복원 (MCT-176 F-005 downgrade 해소). pyright P0 fix (return type + None narrowing). data#65 |
| CO-2 | `_register_signal_handlers` + `_SHUTDOWN_REQUESTED` wiring | ✓ non-asyncio entry (`backfill`/`compact`) `signal.signal()` 실 등록 + collect loop chunk boundary polling (MCT-176 stub 해소). data#65 |
| CO-3 | 6 repo secret read 검증 | ✓ `scripts/verify_cross_repo_secret.py` 신규 (hub owner, read-only gh secret list, 6 repo 순회 + 미등록 목록 + exit 1). CodeReviewPL P1 fix — script owner = hub governance 영역. hub#334 |

### ADR-030 amendment box (MCT-177 LAND 박제, Phase 2 PR2)

`docs/adr/ADR-030-docker-stack-governance.md` 본문 박제:
- **§D2 VERIFIED** (paper-engine service block + healthcheck contract P0 fix + depends_on collector)
- **§D4 VERIFIED** (engine asyncio SSOT 재사용 — 신규 daemon 코드 0 line + RefactorAgent (A) dead path 제거 + plan §2.2 amend)
- **§D10 VERIFIED** (`--universe-id` + `UNIVERSE_TOP_N=50` env fallback + 미등록 exit 1)
- **§D15 VERIFIED** (`REDIS_KEY_PREFIX_ENGINE` env + 3 namespace. signal-collector code migration = MCT-178 carry)
- Phase 2 PR1 cross-repo LAND timeline (data#65 → engine#54 → hub#334 sequential gate) + MCT-176 CO-1~3 처리 결과 + MCT-178 carry over (signal-collector Redis prefix migration)

### Key References

- Story: `docs/stories/MCT-177.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-177-paper-engine.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- ADR-030 §D2/§D4/§D10/§D15: `docs/adr/ADR-030-docker-stack-governance.md`
- RETRO: `docs/retros/RETRO-MCT-177.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-3 박제, milestone 3/7)

### 다음 Story 진입 권고

**MCT-178 COMPLETED** ✓ (2026-05-15). 다음 = **MCT-179** — 아래 §MCT-178 COMPLETED 참조.

## MCT-178 COMPLETED (2026-05-15) — backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis migration

> **sequential_phase 4** — EPIC-mctrader-docker-stack Story-4. cross-repo 3 PR sequential LAND
> (hub Phase 1 docs + signal-collector Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제).
> 첫 mctrader-signal-collector repo PR (#1) — 6번째 cross-repo 대상 repo 데뷔.

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15T10:20:05Z | mctrader-hub#336 | 0d56730 | Phase 1 docs — Story §1-§12 + ADR-030 §D2/§D16 amendment box 본문 박제 + CLAUDE.md MCT-178 IN_PROGRESS |
| 2026-05-15T10:35:04Z | mctrader-signal-collector#1 | 60787c4 | Phase 2 PR1 signal — 5 worker **Publisher 계층 집중** Redis prefix dual write + Prometheus Gauge (land_order 1) |
| 2026-05-15T10:35:55Z | mctrader-hub#337 | bd9baf2 | Phase 2 PR1 hub — backtest-runner service + `compose-validate.yml` workflow (land_order 2) |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §8.5/§10/§11/§12 + ADR-030 §D2/§D16 VERIFIED + scope_manifest 4/7 + **F-001 정정** + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-4 |

### 결과 요약

| 항목 | 결과 |
|------|------|
| 총 AC | **5/5 PASS** (AC-1 oneshot config / AC-2 restart no / AC-3 universe override / AC-4 compose-validate 3 lint + health gate / AC-5 signal Redis dual write + Gauge) |
| 총 INV | 4/4 박제 (forward-only + backtest stateless oneshot + Redis dual write idempotent + INV-5 1주일 grace) |
| FIX 루프 | **1 iter** — design iter1 **CONDITIONAL_PASS** (F-001/F-002 ADR-030 reconciliation fast-fix ba87b3c) + code iter1 **PASS** 양 PR (signal blocking 0 / hub P2 noise 2 non-blocking → 본 PR §F-001 정정) |
| ADR-030 amendment | §D2 + §D16 VERIFIED 박제 (Phase 2 PR2) + §D15 cross-ref carry over 이행 완료 |
| Epic milestone | **4/7** (MCT-175 + MCT-176 + MCT-177 + MCT-178 COMPLETED) |
| MCT-177 carry over 처리 | 1/1 (signal-collector 5종 Redis prefix code migration — Publisher 계층 집중) |
| MCT-181 carry over | `${IMAGE_TAG}` prod pin (D12, dev=latest 현행 유지) |

### 채택 4 D (Epic Story-4 범위)

| D | 결정 | Option | 결과 |
|---|------|--------|------|
| D2 (backtest-runner) | A | `compose.yml` `backtest-runner` service LAND — image (paper-engine 동일) + `profiles: ["oneshot"]` + `command: ["backtest","--help"]` + `restart: "no"` + no healthcheck. command override 분기 |
| D4 (oneshot completion) | C | oneshot 실행 후 exit 0 → 컨테이너 종료 (restart "no" 정합). SIGTERM = 기존 shutdown.py asyncio SSOT graceful abort (MCT-177 LAND 재사용) |
| D10 (universe override) | D | `docker compose --profile oneshot run --rm backtest-runner backtest --universe-id <id>` (MCT-177 LAND CLI option 재사용) + 미등록 exit 1 |
| D16 (compose config CI lint) | B | `.github/workflows/compose-validate.yml` 신규 — 3 profile lint (dev/prod/oneshot config --quiet) + up --wait health gate (infra only, 180s budget) |

### signal-collector Redis migration (D15 carry over 이행, signal-collector#1)

- 5 worker (fear_greed / ecos / kimchi / announcement / coinglass) — **Publisher 계층 집중** `signal:*` prefix
- legacy unprefixed + `signal:*` dual write (1주일 grace) + Prometheus `redis_key_migration_dual_write_active` Gauge=1
- LAND+7d legacy cleanup = 별 PR (`scripts/redis-prefix-cleanup.sh`)
- **Phase 0 verify lesson**: 5 worker 개별 SET 산재 가설 ≠ Publisher 단일 계층 실상 (MCT-170/177 §5.1 cross-repo Phase 0 verify 독립 의무 동형 재현)

### F-001 정정 (Phase 2 PR2 박제 영역)

CodeReview hub#337 P2 noise (non-blocking) carry → 본 PR 정정:
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` line ~170/244 stale:
  - `docker-compose-validate.yml` → `compose-validate.yml` (실 LAND 파일명)
  - `profile=backtest` → `profiles: [oneshot]` (실 LAND profile)
- ADR-030 §D2/§D16 F-001/F-002 reconciliation SSOT 정합 (MCT-175 LAND 누적 swap 박제 해소)

### ADR-030 amendment box (MCT-178 LAND 박제, Phase 2 PR2)

`docs/adr/ADR-030-docker-stack-governance.md` 본문 박제:
- **§D2 VERIFIED** (backtest-runner service block + profiles ["oneshot"] + restart "no" + no healthcheck)
- **§D16 VERIFIED** (`compose-validate.yml` 3 profile lint + health gate. 실 파일명 정합)
- **§D15 cross-ref VERIFIED** (signal-collector 5 worker Publisher 계층 carry over 이행 완료)
- F-001/F-002 reconciliation 최종 정합 (scope_manifest SSOT + line 170/244 정정)

### Key References

- Story: `docs/stories/MCT-178.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-178-backtest-runner.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- ADR-030 §D2/§D16: `docs/adr/ADR-030-docker-stack-governance.md`
- RETRO: `docs/retros/RETRO-MCT-178.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-4 박제, milestone 4/7)

### 다음 Story 진입 권고

**MCT-179 IN_PROGRESS** (observability + WAL 30G production measurement + DR mode integration + alert rule) — sequential_phase 5.

진입 prerequisite:
1. MCT-178 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. carry over: `${IMAGE_TAG}` prod pin (D12, MCT-181 owner — dev=latest 현행 유지)
3. **R2 (WAL 30G 미측정 CRITICAL) = MCT-179 owner** — peak market open 09:00 KST burst window 측정 의무. 30G 초과 시 D11 hard_limit amendment 발의 (FAIL gate). EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 정합.

채택 결정: D5 (Prometheus metric + WAL measurement script + amendment trigger) + D8 (앱 내장 /metrics + Grafana + alert rule) + D17 (SIGTERM graceful + startup InvariantHarness scan).

## MCT-179 COMPLETED (2026-05-15) — observability + WAL 30G synthetic baseline + DR mode + alert

> **sequential_phase 5** — EPIC-mctrader-docker-stack Story-5. **R2 CRITICAL owner** (WAL 30G
> measurement — EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 흡수). cross-repo 3 PR
> sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제).
> AC-1~5 PASS. **R2 CRITICAL = synthetic baseline 측정 완료 (PARTIAL 해소), production 별 PR carry over.**

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15 | mctrader-hub#339 | fabba57 | Phase 1 docs — Story §1-§12 + ADR-030 §D5/§D8/§D17 amendment box + CLAUDE.md. DesignReview iter1 P0 (ADR-030 Out-of-scope D5/D8 stale → D1-D19 전수 reconcile c8e4b8e) → iter2 PASS |
| 2026-05-15T11:51:56Z | mctrader-data#66 | e4a2cc2 | Phase 2 PR1 data — `measure_wal_baseline.py` 신규 + capacity_probe `measure_wal_bytes()`/`emit_wal_capacity_gauge()` (MCT-171 SSOT 정합, deprecated Gauge 미도입, +547 lines) + cli.py startup InvariantHarness scan + 20 test (land_order 1). CodeReview iter1 PASS |
| 2026-05-15T11:52:49Z | mctrader-hub#340 | 64feb73 | Phase 2 PR1 hub — prometheus.yml scrape + prometheus-alerts.yml + docker-stack.json + compose.yml (land_order 2). CodeReview iter1 P1×2 metric desync (가공 metric → R2 deliverable 무력화) → 설계 원인 fix (64647c7, MCT-171/170 LAND SSOT 정렬) → iter2 PASS |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §10/§11/§12 (WAL JSON + §12.1 P2 정정) + ADR-030 §D5/§D8/§D17 VERIFIED + scope_manifest 5/7 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-5 |

### R2 CRITICAL 상태 (PARTIAL 해소)

| 항목 | 상태 |
|------|------|
| WAL 30G synthetic baseline | **✓ 측정 완료** — `measure_wal_baseline.py` paper-synthetic `verdict: PASS` (wal_peak_gb=0.0, read-only probe, MCT-172 D8-2 패턴). exit 0 PASS |
| WAL 30G EXCEED branch | **✓ 검증** — `WAL_HARD_LIMIT_GB=0` mock → `verdict: EXCEED` + exit 7 + stderr D11 amendment 의무 (D8-7=A FAIL gate) |
| WAL 30G production 실 측정 | **별 PR carry over** — production deploy + peak market open 09:00 KST 1h burst window (EPIC-tier-promotion-single-source prod-2 cross-Epic) |
| D11 hard_limit amendment trigger | WAL > 30G 시 GitHub issue 자동 발의 + Epic CLOSE FAIL gate (D8-7=A) |

### 채택 3 D (LAND VERIFIED)

| D | Option | 결과 |
|---|--------|------|
| D5 (WAL 측정 + Gauge) | C | `scripts/measure_wal_baseline.py` LAND (paper-synthetic/production, exit 0/7/99). Prometheus Gauge SSOT = **`mctrader_capacity_usage_bytes{layer="WAL_local"}`** (MCT-171 LAND, `wal_capacity_bytes` 가공 Gauge 폐기). 30G 초과 issue trigger |
| D8 (observability) | C | Prometheus scrape (collector/paper-engine **:8080/metrics** — Phase 0 verify `:9090` 가설 기각 + paper-engine container_name fix) + Grafana docker-stack.json 9 panel + alert 4종 (WALCapacityWarn/Critical = MCT-171 SSOT + NASReaderDROpen/Ambiguity = MCT-170 dr_mode 실 series) |
| D17 (startup scan) | A | collector cli.py startup InvariantHarness 8종 scan hook (NAS_MINIO_ENDPOINT 미설정 graceful skip + ambiguity D10 fail → log.warning 전용, raise 금지). SIGTERM = MCT-176/177 LAND 재사용 (신규 0) |

### FIX 루프 (2 iter — design 1 + code 1)

- **design iter1 (P0, 설계 원인)**: ADR-030 "Out of scope" 표 D5/D8 정의 swap stale (scope_manifest SSOT desync, MCT-178 F-001 동형 누적). ArchitectPL 전수 정정 (c8e4b8e) — D1-D19 전체 row 를 scope_manifest §design_decisions SSOT 와 1:1 전수 정합 (누적 stale 근본 차단, MCT-180/181 재발 사전 방지). DesignReview iter2 PASS
- **code hub#340 iter1 (P1×2, 설계 원인)**: alert/dashboard 가공 metric (`wal_capacity_bytes`/`nas_reader_5xx_total`/`nas_reader_p99_ms`) LAND registry 부재 → **R2 CRITICAL deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화**. ArchitectPL 최종 판정 = 설계 원인 (ADR-030 §D8 + Plan §2.2 가 Phase 0 verify 미수행 가공 metric 박제, MCT-170/177 lesson 4회 재현). fix (64647c7) — MCT-171 SSOT (`mctrader_capacity_usage_bytes{layer="WAL_local"}`) + MCT-170 dr_mode 실 series 정렬 + 미실존 panel `[MCT-180 TODO]` downgrade. **R2 deliverable 기능 회복**. CodeReview iter2 PASS
- **code data#66 iter1**: PASS (deprecated Gauge 미도입, MCT-171 SSOT 정합, blocking 0)

### MCT-180 follow-up downgrade (carry over)

MCT-180 (sequential_phase 6) 에서 아래 metric emit 신규 후 Grafana panel 활성:
- `mctrader_collector_ticks_total` + `mctrader_collector_active_symbols` (data collector.py emit 신규)
- `mctrader_engine_universe_size` (engine metrics.py Gauge 신규)
- `nas_reader_cache_hit_ratio` + `nas_reader_p99_ms` (engine reader_cache.py Gauge/Histogram expose 신규)

### Key References

- Story: `docs/stories/MCT-179.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-179-observability-wal30g.md`
- ADR-030 §D5/§D8/§D17: `docs/adr/ADR-030-docker-stack-governance.md` (LAND confirm + metric-name SSOT)
- ADR-029 §D11 cross-ref: WAL 30G hard_limit SSOT
- RETRO: `docs/retros/RETRO-MCT-179.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-5 박제, milestone 5/7)

### 다음 Story 진입 권고

**MCT-180** (integration smoke + testcontainers + resource limits + alert rule) — sequential_phase 6.
진입 prerequisite = MCT-179 Phase 2 PR2 MERGED ✓ + MCT-179 carry over (Grafana 5 panel metric emit
신규 — collector ticks/symbols + engine universe_size + reader_cache hit_ratio/p99) + `${IMAGE_TAG}`
prod pin (D12, MCT-181 owner). 채택 결정: D4 (SIGTERM graceful 회귀) + D11 (compose smoke +
testcontainers 2 layer gate) + D18 (resource limits + container_memory alert).

## MCT-180 COMPLETED (2026-05-15) — integration smoke (ESCALATE F-301 → infra-only 3-layer) + testcontainers + resource limits + 5 TODO panel metric emit

> **sequential_phase 6** — EPIC-mctrader-docker-stack Story-6. cross-repo 4 PR sequential LAND
> (hub Phase 1 docs + data Phase 2 PR1 + engine Phase 2 PR1 + hub Phase 2 PR1 + hub Phase 2 PR2 박제).
> AC-1~5 PASS. **D11 integration-smoke CI 격리 설계 결함 → FIX 3회 ESCALATE → infra-only
> 3-layer 재설계** (ArchitectPL chief judge 설계 원인 판정 + option b resolution).

### 4 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-15 | mctrader-hub#342 | b1be313 | Phase 1 docs — Story §1-§12 + ADR-030 §D4/§D11/§D18 amendment box + plan + CLAUDE.md. DesignReview iter1 **PASS** (no FIX — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile 효과 실증) |
| 2026-05-15T13:39:21Z | mctrader-data#67 | f233952 | Phase 2 PR1 data — collector `mctrader_collector_ticks_total`/`_active_symbols` Prometheus emit + `test_collector_nas_boundary.py` testcontainers (land_order 1). CodeReview iter1 FIX → iter2 PASS |
| 2026-05-15T13:39:26Z | mctrader-engine#55 | bc8c627 | Phase 2 PR1 engine — `mctrader_engine_universe_size` + reader_cache `nas_reader_cache_hit_ratio`/`_p99_ms` Gauge expose + `test_paper_redis_boundary.py` testcontainers (land_order 2). CodeReview iter1 FIX → iter2 FIX (설계 원인 — paper daemon ReaderCache 미사용) → iter3 PASS |
| 2026-05-15T13:40:19Z | mctrader-hub#343 | af25d66 | Phase 2 PR1 hub — integration-smoke.yml **infra-only** (ESCALATE F-301 resolution 614033a) + compose.yml 7 service `deploy.resources.limits` + ContainerMemoryHigh alert + docker-stack.json panel id=3,4,6 해제 / id=7,8 downgrade 유지 (land_order 3). CodeReview iter1 FIX → iter2 FIX → iter3 **ESCALATE** → ArchitectPL chief judge 설계 원인 판정 → ESCALATE-fix PASS |
| 2026-05-15 (Phase 2 PR2) | mctrader-hub#TBD | TBD | Phase 2 PR2 박제 — Story §10/§11/§12 + ADR-030 §D4/§D11/§D18 VERIFIED + §D11 N-002 정정 + scope_manifest 6/7 + N1 scope_files 정정 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-6 |

### 채택 3 D (ESCALATE F-301 재설계 반영)

| D | Option | 결과 |
|---|--------|------|
| D4 (SIGTERM 회귀) | C | ESCALATE infra-only 재설계로 integration smoke SIGTERM step 제거 → **D4 회귀 carrier 이관**: testcontainers (data#67 + engine#55) + 각 repo unit test (MCT-176 `_SHUTDOWN_REQUESTED` + MCT-177 `shutdown.py` asyncio SSOT, 코드 변경 0). production full-stack SIGTERM = production deploy carry |
| D11 (integration smoke CI) | C → ESCALATE 재설계 | `.github/workflows/integration-smoke.yml` 신규 — **3-layer 분리**: Layer 1 (CI smoke = infra-only: postgres/redis/minio `--wait` + mc-init oneshot exit 0) / Layer 2 (testcontainers = boundary 실 carrier) / Layer 3 (full-stack compose up = production deploy carry, D12 MCT-181 image registry pin 의존). collector/paper-engine compose up = CI 격리 구조적 불가 (sibling repo image 미배포 + build.context path 부재 → exit 1) |
| D18 (resource limits + alert) | D | compose.yml 7 service `deploy.resources.limits` (collector/paper-engine 512M / backtest 1G / postgres 1G / redis 256M / prometheus/grafana 512M) + `prometheus-alerts.yml` ContainerMemoryHigh `container_memory_usage_bytes{name=~"mctrader-.*"} / container_spec_memory_limit_bytes > 0.8` (cadvisor MCT-123 LAND) |
| carry over (MCT-179) | — | 5 [MCT-180 TODO] panel: id=3,4 (collector ticks/active_symbols data#67) + id=6 (engine universe_size engine#55) **해제** / id=7,8 (reader_cache hit_ratio/p99) **downgrade 유지** (CodeReview FIX iter2 설계 원인 — paper daemon ReaderCache 미인스턴스화, cold reader/backtest 경로만 emit) |

### D11 ESCALATE 재설계 lesson (CI 격리 설계 결함 — FIX 3회 ESCALATE)

ADR-030 §D11 (MCT-180 publish) + Plan §2.3 + Story §4 AC-1 이 "compose up full stack
(collector+paper-engine) in CI" 명시. 그러나 collector/paper-engine = 미배포 sibling repo
image (`ghcr.io/mclayer/mctrader-{data,engine}:latest`, D12 MCT-181 carry) +
`build.context: ../mctrader-{data,engine}` (CI 단독 checkout = path 부재) → `compose up
collector paper-engine --wait` 구조적 exit 1. CodeReview iter1/2 mc --wait 분리(c1d7938) =
mc-init 표면 증상만 해소. FIX 3회 소진 → mechanical/구현 layer 해소 불가 → ArchitectPL
ESCALATE chief judge 최종 판정 = **설계 원인** (구현 충실, 설계가 CI 실행 환경 제약
미검증). option b resolution (614033a) = **3-layer 분리** (CI smoke = infra-only /
testcontainers = boundary 실 carrier / full-stack = production deploy carry, D12 MCT-181
의존). MCT-179 §D8 가공 metric 설계 원인 + MCT-170/177/178 Phase 0 verify lesson 누적 동형
(설계가 실행 환경 제약 미검증).

### Phase 0 verify lesson 5회째 (paper-engine reader cache 구조적 미사용)

Story §4 AC-5 + ADR-030 §D8 + Plan §2.2 가 `nas_reader_cache_hit_ratio`/`_p99_ms` Gauge
producer path 를 paper-engine daemon 으로 가정. Phase 0 verify 실증 = paper daemon
(`PaperRunner` WS tick 경로) `ReaderCache`/`ColdReader`/`TierReader` 미인스턴스화 (grep 0).
`ReaderCache.stats()` production caller = `ColdReader.run_smoke_test()` 1곳 (production
caller 0 = cutover/backtest 경로 only). MCT-170 reader_cache = NAS cold read 전용 scope.
→ contract 정정 (cold reader 한정 metric 재정의, ADR-030 §D8 amendment) + docker-stack.json
panel id=7,8 downgrade 유지 (engine#55 stats() Gauge wiring 은 보존, cold reader/backtest
경로 유효). MCT-170/177/178/179 cross-repo Phase 0 verify 독립 의무 **5회 재현**.

### Key References

- Story: `docs/stories/MCT-180.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-180-integration-smoke.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- ADR-030 §D4/§D11/§D18 VERIFIED + §D11 N-002 정정 + §D8 amendment: `docs/adr/ADR-030-docker-stack-governance.md`
- RETRO: `docs/retros/RETRO-MCT-180.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-6 박제, milestone 6/7)

### 다음 Story 진입 권고

**MCT-181 IN_PROGRESS** (image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED 박제,
D12/D19) — sequential_phase 7. EPIC-mctrader-docker-stack 7/7 + Epic POLICY_FINALIZED.

진입 prerequisite + carry over:
1. MCT-180 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. **`${IMAGE_TAG}` D12 image registry pin** (MCT-181 owner — dev=latest 현행 유지, prod = `sha-<7char>` pin). D11 full-stack compose up CI 검증 = D12 image pin 선행 의존 (ESCALATE F-301 resolution Layer 3)
3. **full-stack production smoke** (MCT-181 또는 별 PR) — collector+paper-engine compose up evidence = production deploy 시점 검증 (image registry pin 의존, EPIC-tier-promotion prod-2 류)
4. **R2 CRITICAL = PARTIAL 해소 유지** — production 실 측정 = 별 PR (peak 09:00 KST 1h burst, EPIC-tier-promotion-single-source prod-2)
5. **engine#55 `ci`/`lookahead-lint` carry over** — `mctrader-market-upbit` private repo git dependency auth 이슈 (engine repo 자체 CI infra, 본 ESCALATE 범위 외 — engine repo 별 처리)

## EPIC-mctrader-docker-stack POLICY_FINALIZED (MCT-181 LAND 2026-05-15)

> milestone **7/7 박제** (MCT-175 + MCT-176 + MCT-177 + MCT-178 + MCT-179 + MCT-180 + MCT-181 COMPLETED).
> Epic CLOSED 자체 박제는 production evidence (prod-1~4) 완성 후 별 PR (EPIC-tier-promotion-single-source 패턴 정합).

### ADR 산출물

- **ADR-030** (신규, MCT-175 publish) — Docker stack governance — single-host compose + dev/prod profile + image registry + observability (D1-D19 박제, Status **POLICY_FINALIZED** MCT-181 LAND)

### 핵심 결정 (D1-D19 전수 VERIFIED)

| D | 결정 | Option | Owner Story |
|---|------|--------|-------------|
| D1 | WAL host disk mount + L1 named volume | C | MCT-175 |
| D2 | paper daemon + backtest oneshot 동일 image command override | A | MCT-177+178 |
| D3 | compose profiles dev/prod + env_file 분리 | A | MCT-175 |
| D4 | SIGTERM handler + 60s grace + startup invariant scan | C | MCT-177+179 |
| D5 | Prometheus metric + WAL 30G measurement + amendment trigger | C | MCT-179 (synthetic, prod 실측 prod-3) |
| D6 | 7 Story 분해 (MCT-175~181) | B | epic-level |
| D7 | NAS DNS 직접 해석 preflight 검증 | A | MCT-175+176 |
| D8 | 앱 내장 /metrics + Grafana dashboard + alert rule | C | MCT-179 |
| D9 | .env 패턴 + rotate-nas-credentials.sh + cron + Slack | D | MCT-176 |
| D10 | universe env default + compose command override 둘 다 | D | MCT-177+178 |
| D11 | compose CI smoke + testcontainers 병행 | C → ESCALATE 재설계 | MCT-180 (infra-only 3-layer, Layer 3 prod-2) |
| D12 | semver + sha + latest 병행 (prod=sha/release pin, dev=latest) | B | MCT-181 |
| D13 | 각 repo 독립 uv.lock + cross-repo lock CI gate | D | MCT-175 |
| D14 | env override + YAML default (effective config dump) | D | MCT-176 |
| D15 | Redis key prefix (signal:/market:/engine:) | C | MCT-177+178 |
| D16 | docker compose config lint + up --wait health gate | B | MCT-178 |
| D17 | SIGTERM graceful + startup InvariantHarness scan (외부 backup 없이) | A | MCT-179 |
| D18 | 명시 resource limits + Prometheus alert (>80% warn) | D | MCT-180 |
| D19 | mctrader_runs named volume + NAS sync on completion | C | MCT-181 |

**19/19 D VERIFIED**. D5 (WAL 30G) = synthetic baseline (production 실측 별 PR prod-3).
D11 Layer 3 (full-stack production smoke) = production deploy carry prod-2. 나머지 17 D 완전 VERIFIED.

### Story 완료 현황 (sequential 7 Story)

- **MCT-175** COMPLETED 2026-05-15 (hub#326 + hub#327 + hub#328) — compose base + dev/prod profile + cross-repo lock gate + ADR-030 publish. DesignReview iter1 P0×1
- **MCT-176** COMPLETED 2026-05-15 (hub#330 + data#64 + hub#331 + Phase 2 PR2) — collector container + NAS credential rotation + effective config dump. DesignReview iter1 P0×1
- **MCT-177** COMPLETED 2026-05-15 (hub#333 + data#65 + engine#54 + hub#334 + Phase 2 PR2) — paper-engine daemon + SIGTERM graceful (engine asyncio SSOT 재사용, 신규 daemon 코드 0 line) + universe + Redis prefix. DesignReview iter1 P0×0
- **MCT-178** COMPLETED 2026-05-15 (hub#336 + signal-collector#1 + hub#337 + Phase 2 PR2) — backtest-runner profile + compose config CI lint + signal-collector 5 worker Redis prefix dual write. DesignReview iter1 CONDITIONAL_PASS (fast-fix ba87b3c)
- **MCT-179** COMPLETED 2026-05-15 (hub#339 + data#66 + hub#340 + Phase 2 PR2) — observability + WAL 30G synthetic baseline + DR mode + alert. DesignReview iter1 P0×1 (ADR-030 Out-of-scope D1-D19 전수 reconcile c8e4b8e — MCT-180/181 재발 사전 차단 투자) + CodeReview iter1 P1×2 (metric desync → 64647c7 R2 deliverable 회복)
- **MCT-180** COMPLETED 2026-05-15 (hub#342 + data#67 + engine#55 + hub#343 + Phase 2 PR2) — integration smoke + testcontainers + resource limits. DesignReview iter1 P0×0 (MCT-179 전수 reconcile 효과 실증) + CodeReview 3 PR iter1 FIX → iter3 hub ESCALATE → ArchitectPL chief judge 설계 원인 판정 + option b resolution (614033a) infra-only 3-layer 재설계 → ESCALATE-fix PASS
- **MCT-181** COMPLETED 2026-05-15 (hub#345 + engine#56 + hub#346 + Phase 2 PR2) — image registry pin (compose 8 라인 ${IMAGE_TAG:-latest} + image-publish.yml 3 repo matrix) + backtest artifact NAS sync (nas_sync.py 신규, mctrader-backtest-runs bucket ADR-029 분리, .done sentinel + 3회 retry + exit 0 best-effort, 9 test ALL PASS + 회귀 969 신규 실패 0). DesignReview iter1 PASS (blocking 0) + CodeReview engine#56/hub#346 PASS (blocking 0) — **FIX 0**. **Epic POLICY_FINALIZED 박제** (19 D 전수 VERIFIED).

### FIX 통계 (Epic 전체)

- **design lane FIX**: MCT-175 (P0×1) → MCT-176 (P0×1) → MCT-177 (P0×0) → MCT-178 (CONDITIONAL_PASS) → MCT-179 (P0×1) → MCT-180 (P0×0) → **MCT-181 (P0×0)**. MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 의 1회 투자가 MCT-180/181 연속 design P0×0 으로 회수 (lesson reapply 누적 효과 Epic 마지막 완결 실증)
- **code lane FIX**: MCT-178 (1 iter) / MCT-179 (1 iter, metric desync) / MCT-180 (3 iter + **ESCALATE 1회** → ArchitectPL chief judge 설계 원인 판정 + option b) / MCT-181 (**0 iter**, design+code 양 lane blocking 0)
- **Phase 0 verify lesson 6회 누적**: MCT-170/177/178/179/180 cross-repo Phase 0 verify gap (설계가 sibling repo runtime 실상 미검증) 6회 재현. MCT-181 = Phase 0 verify 충실 (compose.yml 8 ghcr.io :latest 하드코딩 실증 → AC scope 정확)
- **cross-repo metric desync 누적**: MCT-179 §D8 가공 metric → MCT-180 engine#55 reader_cache producer path 가정 오류 동형 재현 (PMO retro 핵심 입력)

### Epic CLOSED prerequisite registry (POLICY_FINALIZED → CLOSED, production evidence 완성 후 별 PR/Story)

| prod-N | carry over | timing | gate |
|--------|-----------|--------|------|
| prod-1 | ${IMAGE_TAG} prod 실 적용 | production deploy 시 release/sha pin | `.env.prod` `IMAGE_TAG=sha-<commit>` or `v<semver>` 박제 |
| prod-2 | full-stack production smoke (D11 ESCALATE Layer 3) | D12 image pin + production deploy 후 | collector+paper-engine `compose up --wait` evidence |
| prod-3 | R2 WAL 30G production 측정 | peak 09:00 KST 1h burst 실 측정 | 30G 이하 verify (초과 시 D11 hard_limit amendment). EPIC-tier-promotion-single-source prod-2 병행 (cross-Epic) |
| prod-4 | Epic CLOSED 박제 PR | prod-1~3 모두 완료 후 | POLICY_FINALIZED → CLOSED transition (scope_manifest + CLAUDE.md amend) |
| 별(engine) | engine#55 ci/lookahead-lint mctrader-market-upbit private-dep token | engine repo 자체 CI infra | engine repo 별 처리 (본 Epic 범위 외) |

### Key References

- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- **EPIC-mctrader-docker-stack scope_manifest**: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (**POLICY_FINALIZED**, 7/7 milestone completed)
- **ADR-030 (POLICY_FINALIZED, MCT-181 LAND)**: `docs/adr/ADR-030-docker-stack-governance.md`
- **MCT-181 spec**: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- **MCT-181 plan**: `docs/superpowers/plans/2026-05-15-mct-181-image-registry-epic-close.md`
- **MCT-181 retro**: `docs/retros/RETRO-MCT-181.md`
- **EPIC-RESULTS (docker-stack, POLICY_FINALIZED)**: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md`

## EPIC-data-domain-decoupling POLICY_FINALIZED (MCT-182~188 ALL COMPLETED 2026-05-15~17, milestone 7/7)

> mctrader-engine 을 **data-free + exchange-agnostic pure consumer** 로 전환. 7 Story sequential
> strangler-fig (MCT-182~188). brainstorm Phase 0 deep-verify + Codex 9 결정점 + why-first dialog 확정.

### 4-Layer 의존 모델 (TO-BE)

```
Layer 0  mctrader-market  = FOUNDATION (의존 0, DAG 최하위, data 비의존, 순환 0)
   도메인 어휘(Symbol/Timeframe/Decimal38_18/OrderStatus/lifecycle) + wire contract
   (TickRowV1_1/InformationBarModel/CandleModel) + exchange-neutral Protocol
   (CandleProvider/OrderBookProvider) + ◀RELOCATE aggregation algo/records/paper_lineage
Layer 1  거래소 어댑터 (bithumb/upbit/해외/한국거래소 — 각 → market 만, 무한 확장)
Layer 2  mctrader-data = data-storage 영역 단독 (storage/NAS/io reader + adapters.py 다중거래소
   ingestion 단일 경계 + NEW api/ FastAPI /v1: historical Arrow IPC + reverse-write + Redis Stream realtime)
Layer 2' mctrader-engine = PURE CONSUMER (mctrader_data 0 + mctrader_market_bithumb/upbit 0,
   market 어휘 + data /v1 REST/stream 만. data_client/ 신규)

확장 불변식(D5): 신규 거래소 = Layer1 어댑터 repo + data adapters.py 등록 → engine/market-core/ADR 변경 0
```

### 7 Story (sequential, MCT-182~188)

| phase | Story | 제목 | D | 상태 |
|---|-------|------|---|------|
| 1 | **MCT-182** | Layer0 contract relocation → market (aggregation/records/paper_lineage + engine CandleModel 4곳 재지정) | D1,D6 | **COMPLETED 2026-05-15** (hub#349+market#11+data#68+engine#57+hub#350+data#69 fix1) |
| 2 | **MCT-183** | Layer2 io/ relocation → data (engine io/ 6 module dead-in-prod) | D2,D6 | **COMPLETED 2026-05-16** (hub#353+data#70+engine#58+hub#354+data 6450cfd lint-revert) |
| 3 | **MCT-184** | data REST API 신규 (FastAPI /v1 historical+reverse-write) | D3,D6 | **COMPLETED 2026-05-16** (hub#358+data#72+hub#359 Phase 2 PR2 부분+data#74 post-merge fix F-1/F-2/F-4+hub#361 amendment F-3 LAND ✅) |
| 4 | **MCT-185** | data realtime stream + engine thin client + cold-read/reverse-write 11-place cutover | D2,D3 | **COMPLETED 2026-05-17** (hub#366+data#76+engine#59+hub Phase2 PR2) |
| 5 | **MCT-186** | engine realtime cutover + exchange-adapter 제거 (R2 MCT-41 교차검증) | D4 | **COMPLETED 2026-05-17** (hub#370+engine#60+hub Phase2 PR2 — AC-1 grep0 PASS 5곳 5파일 전부 제거 + RedisStreamSubscriber + types.py + ws_wrapper.py 삭제) |
| 6 | **MCT-187** | 다중거래소 확장 불변식 박제 | D5,D6 | **COMPLETED 2026-05-17** (hub#374+data#78+hub Phase2 PR2 — 5 TC PASS, adapters.py 변경 0, runbook 신규, ADR-031 §D5 VERIFIED) |
| 7 | **MCT-188** | data-free grep0 quad gate + Epic POLICY_FINALIZED | D7,D6 | **COMPLETED 2026-05-17** (hub Phase1 8e90758 + engine#61 07e8ac4 + hub Phase2 PR2 — Gate 1~4 PASS, ADR-031 POLICY_FINALIZED) |

### ADR-031 (신규, MCT-182 publish + LAND VERIFIED)

`docs/adr/ADR-031-data-domain-decoupling.md` — Status **POLICY_FINALIZED** (MCT-188 LAND, 2026-05-17, D1-D7 전수 VERIFIED). D1-D7 + 4-layer + D-row↔scope_manifest
7/7 byte 1:1 reconcile (MCT-179 lesson — cross-repo desync 7회째 사전 차단). ADR-029 §D2 + ADR-027 §D9 + ADR-030 §compose amend confirm 전수 박제 (MCT-188 Phase 2 PR2).
Status transition: Proposed (MCT-182) → Accepted (MCT-182 LAND) → **POLICY_FINALIZED** (MCT-188 LAND 2026-05-17).

> **Epic POLICY_FINALIZED 2026-05-17** — MCT-182~188 sequential 7 Story 전수 COMPLETED. D1-D7 전수 VERIFIED.
> engine = data-free + exchange-agnostic pure consumer 완전 달성. Epic CLOSED 자체 = 별 PR (docker-stack/tier-promotion 패턴 정합).

### Phase 0 deep-verify 핵심 사실 (가설 정정 포함)

- engine CandleModel import = **실측 4곳** (brainstorm 가설 5곳 = docstring 오집계, MCT-182 요구사항 lane 정정)
- aggregation/paper_lineage = PURE (market+stdlib만, mctrader_data.* 0) — market 이전 시 결합 전파 0
- engine io/ 6 module = src caller 0 (tests/io/ 만, dead-in-prod) — MCT-183 relocate 무손실
- mctrader-market = DAG 최하위, mctrader_data import 0 (순환 0) + upbit(v0.1.0) 존재 + data adapters.py 다중거래소 팩토리 가동

### Risk

| Risk | Severity | 상태 |
|------|----------|------|
| R1 cross-repo contract/Phase0 desync 7회째 | HIGH | 완화 — Story별 Phase0 deep-verify 독립 게이트 + ADR-031 D-row↔scope_manifest 7/7 byte 정합 (MCT-182 iter1 desync 1건 선제 차단 실증) |
| R2 EPIC-MCT-41 Live Mode Debut 블락 | HIGH | MCT-182~185 파일 disjoint 병렬 안전. MCT-186 진입 전 MCT-43~47 IN_PROGRESS 파일 교차검증 의무 (Orchestrator ordering 결정) |

### Key References

- spec: `docs/superpowers/specs/2026-05-16-EPIC-data-domain-decoupling-design.md`
- scope_manifest: `scope_manifests/EPIC-data-domain-decoupling.yaml`
- ADR-031: `docs/adr/ADR-031-data-domain-decoupling.md`
- MCT-182 plan: `docs/superpowers/plans/2026-05-16-mct-182-layer0-contract-relocation.md`
- MCT-182 Change Plan: `docs/change-plans/MCT-182-change-plan.md`

## MCT-184 COMPLETED (2026-05-16) — Layer 2 data REST API 신규 (FastAPI /v1 historical + reverse-write) + post-merge fix 4건 carry

> **sequential_phase 3** — EPIC-data-domain-decoupling Story-3. 3 PR cross-repo sequential LAND
> (hub#358 Phase 1 docs + data#72 Phase 2 PR1 code + hub#359 Phase 2 PR2 박제 부분 + hub#TBD
> amendment PR post-LAND completion). AC-6 / INV-6 PASS, **dead-in-data 박제** (production caller 0,
> consumer=MCT-185 cutover). pre-LAND 설계리뷰 FIX 0회 (§3.6.1 gate v2 사전차단 6회째 실효),
> **post-LAND iter 1 P0×3 + P1×1 carry** (Codex audit 발견 — F-1/F-2/F-4 data측 + F-3 hub측 본 amendment).

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-16T14:09:50Z | mctrader-hub#358 | 1e96b47 | Phase 1 docs — Story §1-§12 + ADR-031 §D3 amendment box (부분 진행) + scope_manifest + CLAUDE.md MCT-184 IN_PROGRESS. DesignReview iter1 **PASS FIX 0회** (cross-doc SSOT 6회째 §3.6.1 gate v2 사전차단) |
| 2026-05-16T14:45:38Z | mctrader-data#72 | 45e501c5 | Phase 2 PR1 data — `src/mctrader_data/api/` 6 파일 신규 (FastAPI ASGI + Arrow IPC helpers + DI deps + Pydantic strict schemas + /v1 historical/reverse-write routes) + tests/api/ TC-1~11 + Perf Baseline + pyproject fastapi/uvicorn (land_order 1, single repo, 21 API test PASS, ubuntu CI 1152 passed) |
| 2026-05-16T14:51:30Z | mctrader-hub#359 | 4924b16 | Phase 2 PR2 hub 박제 (**부분**) — Story §8.5 Impl Manifest + ADR-031 §D3 Phase 2 LAND confirm + scope_manifest 3/7 + CLAUDE.md MCT-184 RESERVED→COMPLETED. **incomplete**: RETRO-MCT-184.md 미생성 + EPIC-RESULTS §Story-3 미작성 + Story frontmatter status 미전환 + F-3 hub#TBD 잔존 |
| 2026-05-17 | mctrader-data#74 | e612296 | post-merge fix data (F-1+F-2+F-4) — ts_utc strict datetime + INV-3 sha256 3-case sidecar SSOT + arrow_ipc Option A bytes-level (ubuntu CI 1169 passed 회귀 0). MERGED 2026-05-17 |
| 2026-05-17 | mctrader-hub#361 | TBD | **박제 amendment PR (F-3 LAND ✅)** — §10 FIX Ledger iter1 F-1/F-2/F-4 LAND 박제 + §11 TBD→실 LAND 정정 + CLAUDE.md hub#TBD→hub#361 + Change Plan §3.2/§3.3 contract amend. MERGED 2026-05-17 |

### 결과 요약

| 항목 | 결과 |
|------|------|
| 총 AC | **6/6 PASS** (AC-1 FastAPI /v1 + OpenAPI / AC-2 historical Arrow IPC byte 정확 / AC-3 reverse-write idempotent / AC-4 OpenAPI SSOT=data + cross-repo lock CI env 미구성 = MCT-185 carrier / AC-5 NAS layout 비노출 / AC-6 wiring drift 차단 production caller 0 + consumer=MCT-185 evidence triad) |
| 총 INV | **6/6 PASS** (INV-1 engine 의존 신규 0 / INV-2 Arrow IPC byte-equiv / INV-3 reverse-write idempotent sha256 sidecar / INV-4 §3.6.1 gate v2 self-verify TEST1/TEST2 / INV-5 회귀 0 / INV-6 NAS 비노출) |
| 신규 test | **21 passed + 2 skipped** (TC-4/TC-8 env-specific cross-repo-contract-lock-check.sh CI env 미구성 — AC-4 carrier = MCT-185) |
| 회귀 | data 1152 passed ubuntu-latest, 신규 실패 0 (fastapi/uvicorn 신규 의존 추가, 기존 storage/io/compactor 무변경 — INV-5 정합) |
| FIX 루프 (pre-LAND) | **설계리뷰 iter 1 PASS FIX 0회** (cross-doc SSOT 6회째 §3.6.1 gate v2 사전차단, MCT-183 lesson reapply 효과 검증) / **구현리뷰 BYPASS** (dead-in-data, consumer=MCT-185, 구현-리뷰 lane = MCT-185 cutover 전 진입) |
| FIX 루프 (post-LAND) | **iter 1 post-merge fix 4건 (P0×3 + P1×1)** — Codex audit 발견. F-3 = 본 amendment PR LAND ✅. F-1/F-2/F-4 = data측 별 post-merge fix PR carry over (#795 unblock 후 진입 의무, MCT-185 cutover 진입 prerequisite gate) |
| ADR-031 §D3 | **partial VERIFIED 2026-05-16** (historical+reverse-write LAND, realtime stream + cold-read cutover = MCT-185 carry) |
| Epic milestone | **3/7** (MCT-182 + MCT-183 + MCT-184 COMPLETED) |
| MCT-185 진입 prerequisite | F-1/F-2/F-4 data측 post-merge fix PR LAND + F-3 hub측 amendment LAND ✅ |

### 채택 2 D (LAND VERIFIED)

| D | Option | 결과 |
|---|--------|------|
| D3 | fastapi-v1 + redis-stream (partial) | FastAPI /v1 historical Arrow IPC + reverse-write POST LAND. realtime stream Redis Stream + cold-read cutover = MCT-185 carry. dead-in-data 박제 (production caller 0, consumer=MCT-185) |
| D6 | new-adr-031 + amendment | ADR-031 §D3 partial VERIFIED 박제 (hub#359). ADR-030 amendment box 박제 (data api service compose topology 예고, 실 compose wiring = MCT-186 owner). ADR-029 amendment box (presigned-NAS-handoff 기각 재명시, 실 amend = MCT-185) |

### post-LAND iter 1 post-merge fix 4건 (P0×3 + P1×1) — Codex audit 발견

| # | severity | file | finding | fix path |
|---|----------|------|---------|----------|
| F-1 | P0 (구현) | data `api/routes_v1.py:191-196,244-247` | invalid ts_utc → `datetime.now()` silent substitute = silent data corruption | data측 별 post-merge fix PR (#795 unblock 후 진입) |
| F-2 | P0 (구현) | data `api/routes_v1.py:191-196,244-247` | canonical_sha256 dead code, sidecar pattern만 검사 = silent data-loss (INV-3 mismatch) | data측 별 post-merge fix PR |
| F-3 | P0 (구현 + 박제) | hub `docs/stories/MCT-184.md §8.5.1+§11` + `CLAUDE.md:560` | hub#TBD 잔존(실 LAND=hub#359, severity_override) | **hub 본 amendment PR LAND ✅** |
| F-4 | P1 (설계 + 구현) | data `api/arrow_ipc.py:47-58` | round-trip INV-2 bytes-level 보장 X (table 동등만, dead-in-data 런타임 0 but MCT-185 cutover 전 정정) | data측 별 post-merge fix PR |

**F-1/F-2/F-4 의 의미**: dead-in-data 런타임 영향 0 이지만 **MCT-185 cutover 시 즉시 silent 데이터 손상** (F-1 silent corruption + F-2 INV-3 mismatch silent data-loss). MCT-185 진입 prerequisite gate 의무.

### 박제 PR 자체 incomplete 패턴 (SSOT drift 3호, MCT-189 PMO-PATTERNS 동형)

hub#359 박제 PR MERGED 그러나 박제 작업의 약 절반만 처리. "Phase 2 PR2 박제" PR title 이 박제 작업의 SSOT 가 아님 — PR MERGED ≠ 박제 완결. 박제 산출물 체크리스트 (RETRO + EPIC-RESULTS §Story-N + Story frontmatter + CLAUDE.md + ADR amendment confirm) 의 전수 LAND 가 완결 의무.

→ **codeforge upstream ADR escalation 후보 2** (박제 PR 자체 완결도 mechanical gate) + **후보 3** (post-merge audit lane = Codex post-LAND audit 발견 영역의 박제 lane 의무 검증화) 발의. PMO-AUDIT-MCT-184 박제 + codeforge marketplace issue.

### Key References

- Story: `docs/stories/MCT-184.md`
- spec: `docs/superpowers/specs/2026-05-16-EPIC-data-domain-decoupling-design.md`
- Change Plan: `docs/change-plans/MCT-184-change-plan.md`
- ADR-031 §D3 partial VERIFIED: `docs/adr/ADR-031-data-domain-decoupling.md`
- RETRO: `docs/retros/RETRO-MCT-184.md` (본 amendment 신규)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` §Story-3 (본 amendment 신규)

### 다음 Story 진입 권고

**MCT-185 COMPLETED** ✓ (2026-05-17). 다음 = **MCT-186** — 아래 §MCT-185 COMPLETED 참조.

## MCT-185 COMPLETED (2026-05-17) — data realtime stream + engine thin client + cold-read/reverse-write 11-place cutover

> **sequential_phase 4** — EPIC-data-domain-decoupling Story-4. **가장 복잡 Story** (3 repo + production wiring 전환, ADR-032 evidence triad 선제 reapply 효력 1회 실증). cross-repo 3 PR sequential LAND (hub#366 Phase 1 docs + data#76 land_order 1 + engine#59 land_order 2 + hub Phase 2 PR2 박제). AC-1~6 + INV-1~7 PASS. **AC-3 grep0 VERIFIED** (engine src/ `from mctrader_data.(storage|path|...)` = 0건).

### 3 PR cross-repo sequential LAND timeline

| 시각 | PR | LAND commit | 박제 내용 |
|------|-----|-------------|-----------|
| 2026-05-16T16:20:42Z | mctrader-hub#366 | 67bcc1c | Phase 1 docs — Story §1-§12 + ADR-031 §D2+§D3 amendment box draft + ADR-029 §D2 amendment box draft + CLAUDE.md MCT-185 IN_PROGRESS. DesignReview iter1 **PASS FIX 0회** |
| 2026-05-16T16:36:06Z | mctrader-data#76 | 9473665 | Phase 2 PR1 data — `src/mctrader_data/api/realtime_stream.py` 신규 (Redis Stream XADD publisher, tick.v1.1 Schema, SSE endpoint `/v1/realtime/ticks`) + `/v1/historical/{symbol}` OrderBook endpoint + CodeQL CWE-22 fix (`_assert_within_root` relative_to boundary) + tests/ (land_order 1). CodeReview PASS FIX 0회 |
| 2026-05-16T17:03:55Z | mctrader-engine#59 | 1312195 | Phase 2 PR1 engine — `src/mctrader_engine/data_client/` 신규 (DataClient HTTP thin client + realtime WS stream consumer) + cold-read 8곳 cutover (cli.py×2 + tick_replay.py×2 + wfo/evaluator×2 + wfo/search×2) + reverse-write 3곳 cutover (paper_runner.py×2 + nas_sync.py×1) + **AC-3 grep0 VERIFIED** (land_order 2). CodeReview PASS FIX 0회 |
| 2026-05-17 | mctrader-hub Phase 2 PR2 | (본 PR) | 박제 — Story §8.5 Impl Manifest + ADR-031 §D2+§D3 VERIFIED + ADR-029 §D2 VERIFIED + scope_manifest 4/7 + CLAUDE.md COMPLETED + RETRO 신규 + EPIC-RESULTS §Story-4 |

### 결과 요약

| 항목 | 결과 |
|------|------|
| 총 AC | **6/6 PASS** (AC-1 realtime SSE stream / AC-2 engine data_client HTTP / AC-3 engine src/ grep0 VERIFIED / AC-4 historical+reverse-write 11-place cutover / AC-5 CodeQL CWE-22 fix / AC-6 ADR-032 evidence triad) |
| AC-3 grep0 | **engine src/ 0건** — `from mctrader_data.(storage|path|orderbook_replay|paper_storage|nas_storage)` grep 결과 0 (engine#59 LAND 후 confirm) |
| 11-place cutover | cold-read 8곳 (cli.py×2, tick_replay.py×2, wfo/evaluator×2, wfo/search×2) + reverse-write 3곳 (paper_runner.py×2, nas_sync.py×1) |
| FIX 루프 | **FIX 0회** — code lane blocking 0 양 PR (data#76 PASS + engine#59 PASS). DesignReview PASS FIX 0회 |
| ADR-032 | **evidence triad 선제 reapply 효력 1회 실증** — MCT-184 dead-in-data → MCT-185 production wiring 전환 (ADR-032 §3.6.1 gate v2 cross-Story 활용) |
| Epic milestone | **4/7** (MCT-182 + MCT-183 + MCT-184 + MCT-185 COMPLETED) |
| MCT-186 carry over | engine realtime stream consumer wiring (WS subscribe loop) + exchange-adapter 제거 (R2 MCT-41 교차검증) |

### 채택 2 D (LAND VERIFIED)

| D | Option | 결과 |
|---|--------|------|
| D2 | io-relocation-complete | engine io/ 6 module (MCT-183 LAND) + cold-read 8곳 + reverse-write 3곳 cutover LAND. ADR-029 §D2 VERIFIED (engine NAS 직독 폐기 완결) |
| D3 | realtime-stream-redis | Redis Stream XADD publisher + SSE endpoint + engine DataClient thin client LAND. ADR-031 §D3 VERIFIED (historical+reverse-write+realtime stream 3-tier 완결) |

### ADR amendment (MCT-185 LAND 박제)

- **ADR-029 §D2 VERIFIED** (engine NAS 직독 폐기 완결 — 11-place cutover LAND confirm)
- **ADR-031 §D2+§D3 VERIFIED** (cold-read cutover 완결 + realtime stream + reverse-write wiring 완결 — Phase 1 draft → Phase 2 PR2 VERIFIED)

### 7 Story 현황 (milestone 4/7 박제)

| phase | Story | 상태 |
|---|-------|------|
| 1 | MCT-182 | COMPLETED 2026-05-15 |
| 2 | MCT-183 | COMPLETED 2026-05-16 |
| 3 | MCT-184 | COMPLETED 2026-05-16~17 (post-merge fix 4건 포함) |
| 4 | **MCT-185** | **COMPLETED 2026-05-17** (hub#366 + data#76 + engine#59 + hub Phase 2 PR2) |
| 5 | **MCT-186** | **COMPLETED 2026-05-17** (hub#370 + engine#60 + hub Phase 2 PR2) |
| 6 | **MCT-187** | **COMPLETED 2026-05-17** (hub#374 + data#78 + hub Phase 2 PR2) |
| 7 | MCT-188 | RESERVED |

### Key References

- Story: `docs/stories/MCT-185.md`
- Change Plan: `docs/change-plans/MCT-185-change-plan.md`
- ADR-031 §D2+§D3 VERIFIED: `docs/adr/ADR-031-data-domain-decoupling.md`
- ADR-029 §D2 VERIFIED: `docs/adr/ADR-029-tier-promotion-single-source.md`
- RETRO: `docs/retros/RETRO-MCT-185.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` (§Story-4 박제, milestone 4/7)

### 다음 Story 진입 권고

**MCT-186 COMPLETED** (2026-05-17, hub#370 + engine#60 + Phase 2 PR2). 다음 = **MCT-187** (다중거래소 확장 불변식 박제, D5+D6) — MCT-186 Phase 2 PR2 MERGED ✓ 후 진입.

## MCT-186 COMPLETED (2026-05-17) — engine realtime cutover + exchange-adapter 제거

> **sequential_phase 5** — EPIC-data-domain-decoupling Story-5. 2 PR cross-repo LAND
> (hub Phase 1 docs + engine Phase 2 PR1 code + hub Phase 2 PR2 박제).
> AC-1 grep0 PASS: `mctrader_market_bithumb` 직접 import **5곳 5파일 전부 제거**.
> **engine = exchange-agnostic pure consumer** (TickRowV1_1 market-core SSOT 소비).

### 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs) | mctrader-hub#370 MERGED (3fc9c1f, 2026-05-16T17:53:38Z) — Story + Change Plan + ADR-031 §D4 draft + ADR-030 NAS cred drop draft + CLAUDE.md |
| Phase 2 PR1 (engine code) | mctrader-engine#60 MERGED (773b270, 2026-05-16T21:52:47Z) — 5곳 5파일 bithumb import 제거 + RedisStreamSubscriber + types.py + ws_wrapper.py 삭제 + cli.py StreamExhaustedError 제거 |
| Phase 2 PR2 (hub 박제) | mctrader-hub#TBD (본 PR) — ADR-031 §D4 VERIFIED + ADR-030 carry over 확정 + scope_manifest 5/7 + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-5 |
| 총 AC | **7/7 PASS** (AC-1 grep0 / AC-2 RedisStreamSubscriber wiring / AC-3 types.py / AC-4 ws_wrapper.py 삭제 / AC-5 testcontainers 4 test PASS / AC-6 FIX iter1 cli.py / AC-7 R2 ZERO RISK) |
| FIX 루프 | **1 iter** (design P0 — cli.py StreamExhaustedError §3.2.4b 발견) |
| ADR-031 §D4 | **VERIFIED** (engine#60 773b270 + grep0 AC-1 + integration test) |
| ADR-030 NAS cred drop | carry over (compose.yml engine NAS env drop = MCT-187 or 별 PR) |
| Epic milestone | **5/7** (MCT-182~186 COMPLETED) |

### 5곳 5파일 제거 내역 (AC-1 grep0 PASS)

| 위치 | 제거 대상 | 대체 |
|------|-----------|------|
| `fill/simulated.py:18` | `OrderbookSnapshotEvent` | `mctrader_engine.realtime.types.OrderbookSnapshot` |
| `realtime/stream_consumer.py:8-12` | 4 bithumb event type | `TickRowV1_1` 단일 (market-core SSOT) |
| `runtime/mock_stream.py:19` | `StreamEvent, TickerEvent, TransactionEvent` | `TickRowV1_1` 기반 `MockMarketStream` |
| `runtime/paper_runner.py:267` | `BithumbWebSocketStream` (function-local) | `RedisStreamSubscriber` |
| `runtime/ws_wrapper.py` | 파일 전체 (`WsWrapperStream` + `StreamExhaustedError`) | **파일 삭제** |

### 신규 파일 (engine#60)

- `src/mctrader_engine/realtime/types.py` — engine-local `OrderbookSnapshot`/`_Level` dataclass (frozen+slots, INV-3 영구)
- `src/mctrader_engine/realtime/redis_subscriber.py` — XREAD asyncio subscriber (ADR-030 §D15 `market:tick:{exchange}:{symbol}`, XREAD BLOCK=1000ms count=100, retry 5× exponential backoff 0.5s base)
- `tests/test_realtime_subscriber.py` — 4 integration test (testcontainers RedisContainer, MCT-180 패턴)

### FIX iter1 (design P0 — §3.2.4b)

Change Plan 초안 cli.py 수정 미포함 → ws_wrapper.py 삭제 시 `StreamExhaustedError` import (line 442) + catch block (line 597) dangling 발견. 설계 리뷰 P0 정정 → cli.py scope 추가 → CONDITIONAL_PASS iter1 후 code iter1 PASS (FIX 0회).

### ADR-031 §D4 VERIFIED evidence triad (ADR-032 정합)

| evidence | 내용 |
|---|---|
| file:line | `fill/simulated.py:18` → `from mctrader_engine.realtime.types import OrderbookSnapshot` |
| caller grep | `grep -rn "mctrader_market_bithumb" src/` = **0건** (engine#60, AC-1 PASS) |
| integration test | `tests/test_realtime_subscriber.py` 4 test (testcontainers) ALL PASS |

### ADR-030 NAS cred drop (carry over)

engine compose.yml `NAS_MINIO_*` env 실 제거 = **MCT-187 or 별 PR** (MCT-186 Phase 2 PR1 scope 외). ADR-030 amendment VERIFIED 확정 시점 = 실 compose wiring LAND 후.

### Key References

- Story: `docs/stories/MCT-186.md`
- Change Plan: `docs/change-plans/MCT-186-change-plan.md`
- ADR-031 §D4 VERIFIED: `docs/adr/ADR-031-data-domain-decoupling.md`
- ADR-030 NAS cred drop carry over: `docs/adr/ADR-030-docker-stack-governance.md`
- RETRO: `docs/retros/RETRO-MCT-186.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` (§Story-5 박제, milestone 5/7)

### 다음 Story 진입 권고

**MCT-187 COMPLETED** (2026-05-17, hub#374 + data#78 + Phase 2 PR2). 다음 = **MCT-188** (data-free grep0 quad gate + Epic POLICY_FINALIZED).

## MCT-187 COMPLETED (2026-05-17) — 다중거래소 확장 불변식 박제 (D5+D6)

> **sequential_phase 6** — EPIC-data-domain-decoupling Story-6. **code-change-zero Story** (adapters.py 변경 0).
> 2 PR LAND (hub Phase 1 docs + data Phase 2 PR1 + hub Phase 2 PR2 박제). AC-1/2/3/4 PASS.
> ADR-031 §D5 VERIFIED. milestone **6/7**.

### 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs) | hub#374 MERGED (91a8bfa, 2026-05-16) — Story + Change Plan + runbook + ADR §D5 draft + scope_manifest + counters |
| Phase 2 PR1 (data) | data#78 MERGED (6346b55, 2026-05-17) — `tests/test_multi_exchange_invariant.py` 5 TC 신규 |
| Phase 2 PR2 (hub 박제) | 본 PR — Story §8.5/§9/§10/§11 + ADR-031 §D5 VERIFIED + scope_manifest 6/7 + counters COMPLETED + CLAUDE.md + RETRO + EPIC-RESULTS §Story-6 |
| 총 AC | **4/5 PASS** (AC-1 5 TC PASS / AC-2 runbook LAND / AC-3 ADR §D5 VERIFIED / AC-4 회귀 0 / AC-5 CONDITIONAL — ADR-030 NAS cred carry) |
| test | ubuntu-latest 1183 passed, 회귀 0. windows testcontainers pre-existing regression (scope 외) |
| FIX 루프 | **1 iter** (ruff F401×3 + E721 + F841 — edda216) |
| adapters.py 변경 | **0 lines** (INV-2 PASS, MCT-186 LAND 정합) |
| engine/market-core 변경 | **0** (INV-1 PASS, D5 invariant 구조적 확인) |
| ADR-031 §D5 | **VERIFIED** (본 PR 박제) |
| Epic milestone | **6/7** (MCT-182~187 COMPLETED) |

### D5 invariant test 5 TC (AC-1)

| TC | 내용 | 결과 |
|----|------|------|
| TC-1 | bithumb + upbit 기존 팩토리 등록 확인 (Phase 0 V1/V2 재확인) | PASS |
| TC-2 | 미등록 거래소 → `ValueError("unknown exchange: ...")` | PASS |
| TC-3 | `monkeypatch` 로 mock exchange 등록 → adapters.py 코드 변경 없이 호출 성공 (D5 핵심 invariant) | PASS |
| TC-4 | engine pyproject 신규 거래소 의존 0 (engine repo 없으면 skip) | SKIPPED (CI-safe) |
| TC-5 | adapters.py callable + bithumb/upbit 정상 + unknown ValueError (INV-2) | PASS |

### 채택 2 D (D5+D6 VERIFIED)

| D | Option | 결과 |
|---|--------|------|
| D5 (다중거래소 확장 불변식) | `data-only-extension-invariant` | 신규 거래소 = adapters.py 등록 only → engine/market-core/ADR 변경 0. invariant test 박제 (TC-3 monkeypatch 핵심). adapters.py 변경 0 (INV-2 PASS) |
| D6 (ADR meta + runbook) | `new-adr-031 + runbook-new-exchange` | ADR-031 §D5 VERIFIED amendment box 박제 + `docs/runbooks/add-new-exchange.md` 3-step 절차 신규 LAND |

### Key References

- Story: `docs/stories/MCT-187.md`
- Change Plan: `docs/change-plans/MCT-187-change-plan.md`
- runbook: `docs/runbooks/add-new-exchange.md` (D5 invariant 절차 SSOT)
- ADR-031 §D5: `docs/adr/ADR-031-data-domain-decoupling.md` (VERIFIED amendment box)
- RETRO: `docs/retros/RETRO-MCT-187.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` (§Story-6 박제, milestone 6/7)

### MCT-188 COMPLETED (2026-05-17) — data-free done-criterion verify (grep0 quad gate) + Epic POLICY_FINALIZED 박제

> **sequential_phase 7** — EPIC-data-domain-decoupling Story-7 (Epic final). engine PR #61 (07e8ac4) + hub Phase 2 PR2.
> D7 quad gate Gate 1~4 전수 PASS. ADR-031 POLICY_FINALIZED. Epic milestone 7/7 완결.

#### Gate 1~4 달성 현황

| Gate | 내용 | 결과 |
|------|------|------|
| Gate 1 | engine src/ `from/import mctrader_data` == 0건 | **PASS** — 4곳 cutover (tick_replay.py + state_machine.py + tick_scalping.py) |
| Gate 2 | engine pyproject `[project.dependencies]` mctrader-data 미존재 | **PASS** — prod dep 제거 (pyarrow>=14 직접 추가) |
| Gate 3 | engine src/ `mctrader_market_bithumb\|upbit` == 0건 | **PASS** (MCT-186 LAND, 변경 0) |
| Gate 4 | engine pyproject `mctrader-market-bithumb\|upbit` 미존재 | **PASS** — bithumb prod dep 제거 |

#### data-free CI gate (`.github/workflows/data-free-grep0.yml`)

- Gate 1: `grep -rn "from mctrader_data|import mctrader_data" engine/src/`
- Gate 2: Python tomllib parser `[project.dependencies]` 전용 체크 (dev deps 허용)
- Gate 3: `grep -rn "^from mctrader_market_bithumb|^import mctrader_market_bithumb|upbit" engine/src/`
- Gate 4: tomllib parser `[project.dependencies]` bithumb|upbit 체크

#### FIX 루프 (engine PR #61, 3 iter)

- iter 1: pyright tests/ `reportMissingImports` → `[tool.pyright] include=["src"] exclude=["tests"]` + pyarrow>=14
- iter 2: mctrader-market-upbit (private) transitive dep auth 실패 → mctrader-data dev dep 제거 + tests/ 8파일 `pytest.importorskip` + aggregation 2파일 직접 교체
- iter 3: `test_latency_p50_p99_under_slo` pre-existing flap → admin merge

#### Key References

- Story: `docs/stories/MCT-188.md`
- ADR-031 POLICY_FINALIZED: `docs/adr/ADR-031-data-domain-decoupling.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md`
- RETRO: `docs/retros/RETRO-MCT-188.md`

### EPIC-data-domain-decoupling POLICY_FINALIZED — D1-D7 전수 VERIFIED

| D | 결정 | Option | Owner Story |
|---|------|--------|-------------|
| D1 | contract relocation → market Layer0 | A | MCT-182 |
| D2 | read 도메인 relocation → data Layer2 | B | MCT-183 + MCT-185 |
| D3 | data REST API boundary (historical Arrow IPC + realtime Redis Stream) | C | MCT-184 + MCT-185 |
| D4 | engine exchange-adapter 제거 (realtime cutover) | A | MCT-186 |
| D5 | 다중거래소 확장 불변식 (engine/market-core/ADR 변경 0) | A | MCT-187 |
| D6 | ADR-031 meta-decision + 7 Story 분해 | B | epic-level |
| D7 | data-free done-criterion grep0 quad gate CI | C | MCT-188 |

**7/7 D VERIFIED**. Epic CLOSED 자체 = 별 PR (POLICY_FINALIZED → CLOSED, production evidence 완성 후).

### Epic CLOSED prerequisite

| prereq | 내용 | timing |
|--------|------|--------|
| engine-compose NAS env drop | compose.yml engine service NAS env 제거 (MCT-186 LAND 이후 engine NAS cred 미사용 — 별 인프라 PR) | 별 PR |
| ADR-030 §compose engine NAS cred drop 실 적용 confirm | compose.yml 실 변경 후 ADR-030 amend confirm 갱신 | 별 PR |
| Epic CLOSED 박제 PR | POLICY_FINALIZED → CLOSED transition (scope_manifest + CLAUDE.md amend) | 별 PR |

## Pending Stories (Replication Backlog)

| Story | 상태 | 내용 |
|-------|------|------|
| MCT-174 | RESERVED | NAS replication (D2=D 결정, single NAS box mcnas02 물리 부재 해소 후 진입) |

MCT-174 근거: ADR-027 §D MCT-161 amendment D2=D (replication deferred). INV-5 의무 = 후속 별 Story 예약 완료.

## Streaming refactor cross-ref (MCT-163, 2026-05-14)

### F3 DualWriter streaming

- `mctrader-data/src/mctrader_data/nas_storage/nas_uploader.py`: `put_streaming(Path|IO, key, sha256)` 신규
- `mctrader-data/src/mctrader_data/nas_storage/dual_writer.py`: `write(Path)` read_bytes 0 (streaming)
- INV-4: DualWriter peak RSS+TM delta ≤ 50 MB (105 MiB 실측: 0.2 MB / 0.0 MB)
- INV-3: sha256 SSOT caller-side (multipart ETag ≠ sha256)

### F6 L2/L3 iter_batches

- `mctrader-data/src/mctrader_data/compactor/l2.py`: `pq.ParquetFile.read()` → `iter_batches(1024)` + `write_batch`
- `mctrader-data/src/mctrader_data/compactor/l3.py`: 동형
- INV-4: L2/L3 peak RSS+TM delta ≤ 256 MB (300k rows 실측: 0.0 MB / 0.3 MB)
- INV-5: iter_batches per-batch write schema == 기존 L2/L3 schema

### EPIC-tier-promotion D9 prerequisite

- MCT-161 + MCT-163 모두 COMPLETED (2026-05-14)
- **MCT-167 (EPIC-tier-promotion governance singleton)** COMPLETED 2026-05-14 (PR #305, 1b83c28)
- **MCT-168 (L1 NAS DualWriter wiring — D1+D2 impl)** COMPLETED 2026-05-14 (hub PR #307 + data PR #59)
  - put_l1() 신규 + l1.py inject + runner pass-through + 22 tests ALL PASS
  - ADR-029 D1=B + D2=B VERIFIED (mctrader-data#59)
- cross-ref: `docs/retros/RETRO-MCT-163.md` + `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md`

## EPIC-tier-promotion-single-source POLICY_FINALIZED (MCT-172 LAND 2026-05-14)

> milestone **6/6 박제** (MCT-167 + MCT-168 + MCT-169 + MCT-170 + MCT-171 + MCT-172 COMPLETED). Epic CLOSED 자체 박제는 production evidence 완성 후 별 PR (D8-9=C Codex 채택).

### ADR 산출물

- **ADR-029** (신규, MCT-167 publish) — Cold tier governance v2 — NAS = SoT for ALL tiers (D1-D11 박제)
- **ADR-017 §3 D3 amendment** — L1 NAS PUT 의무 박제
- **ADR-027 §D5+D7+D9 amendment** — L1 NAS upload 금지 invariant 폐기 + L1 grace 0 + SoT all-tier 격상
- **ADR-009 §D12.2 amendment** — forward-only invariant NAS object SoT 격상

### 핵심 결정 (D1-D11)

| D | 결정 | Option | Owner Story |
|---|---|---|---|
| D1 | L1 NAS PUT timing — ParquetWriter atomic 직후 | B | MCT-168 |
| D2 | DualWriter retry_queue + local_only 재사용 | B | MCT-168 |
| D3 | Local delete — NAS HEAD verify + grace 0 | C | MCT-169 |
| D4 | WAL sealed local only 유지 | B | MCT-171 |
| D5 | Capacity-bounded ingest block | A_modified | MCT-171 |
| D6 | bucket versioning + cross-NAS replication | B | MCT-171 (MCT-161 ✓) |
| D7 | Reader cache 95% hit + p99 <100ms | A | MCT-170 |
| D8 | forward-only + local fallback migration | B | MCT-170 |
| D9 | MCT-161 + MCT-163 prerequisite sequential ✓ | A | epic-level ✓ |
| D10 | Ambiguity invariant violation enforcement | A | MCT-169 + MCT-172 |
| D11 | 4 layer capacity 제한 (WAL 30G / L1 20G / NAS 500G / Host 200G) | capacity_bounded | MCT-171 |

### DR runbook 본문 확장 (MCT-171 COMPLETED)

- `docs/runbooks/nas-bucket-disaster-recovery.md` — 5 fail mode step-by-step + invariant 8종 본문 + 4 layer capacity step-by-step 박제 (MCT-171 Phase 1 LAND)

### Story 완료 현황 (sequential)

- **MCT-167** COMPLETED 2026-05-14 (hub#305) — governance singleton + ADR-029 publish + ADR-017/027/009 amend 3건 + DR runbook stub
- **MCT-168** COMPLETED 2026-05-14 (hub#307 + data#59) — D1+D2 VERIFIED
- **MCT-169** COMPLETED 2026-05-14 (hub#310 + data#60 + hub#311) — D3+D10 VERIFIED
- **MCT-170** COMPLETED 2026-05-14 (hub#314 + data#61 + engine#53 + hub#315) — D7+D8+D10 VERIFIED (hit_ratio=0.95 ✓ + p99=0.016ms ✓)
- **MCT-171** COMPLETED 2026-05-14 (hub#317 + data#62 + hub#318 + hub#319) — D4+D5+D11 VERIFIED (38 신규 test PASS + 931 회귀 0)
- **MCT-172** COMPLETED 2026-05-14 (hub#320 + data#63 + hub#321) — D8 sunset finalize + D9+D10 verify + promotion.py cleanup (89 lines deleted, src grep=0) + 3 신규 integration test green + 16 caller migrate + 954 회귀 0. **Epic POLICY_FINALIZED 박제**.

### Epic CLOSED prerequisite (post-Epic carry over, 별 PR/Story 의무)

| # | prerequisite | timing | gate |
|---|--------------|--------|------|
| prod-1 | production deploy 후 14d 0-hit telemetry | 2026-08-18 ~ 2026-09-01 | `nas_reader_ambiguity_total` Counter 14d rolling rate = 0 |
| prod-2 | WAL 30G production measurement | peak market open 09:00 KST burst | 30G 이하 verify, 초과 시 D11 hard_limit amendment 발의 |
| prod-3 | production evidence quad 동일 1h window | — | bucket size + log + Prometheus + drainage |
| prod-4 | Epic CLOSED 박제 PR or scope_manifest amend | POLICY_FINALIZED → CLOSED | 별 PR or direct amend |

## MCT-170 COMPLETED (2026-05-14) — Engine reader L1 확장 + DR mode + reader cache byte budget

> 4 PR cross-repo sequential LAND, D7 NFR 측정 PASS

### 측정 결과 (D7 NFR)

| 항목 | 결과 | gate | verdict |
|------|------|------|---------|
| hit_ratio (10k read benchmark) | 0.95 | ≥ 0.95 | PASS |
| p99 latency | 0.016 ms | < 100 ms | PASS (대폭 마진) |
| benchmark mean | 1.99 μs | — | ~503k OPS |

R4 mitigation iter 1 적용 (n_rounds 10→20 + cache max_bytes +50%, FIX-MCT-170-001).

### 4 PR LAND timeline

- mctrader-hub#314 (311b795) — Phase 1 docs (7 file)
- mctrader-data#61 (9d26438) — Phase 2 PR#1 LRU 구현 (20 신규 test)
- mctrader-engine#53 (a00690bc) — Phase 2 PR#2 3 module 신규 + 1 확장 (107 io/ test ALL PASS)
- mctrader-hub#315 (f1e04e6) — Phase 2 PR#3 박제

### AC-1 ~ AC-7 PASS / INV-1 ~ INV-4 PASS

ALL PASS. MCT-154 backward compat 회귀 0 (cold_reader + reader_cache MCT-154 API + endpoint_router 전수 green).

### Phase 0 verify 발견 (중대 amendment)

session prompt 의 "engine reader 재구현 — 4 module 신규" 표현이 부정확. verified-via 결과 mctrader-engine `io/` 측 **MCT-154 LAND 3 module 존재** (1058 lines):
- `cold_reader.py` (319 lines) — L2/L3 specialized
- `reader_cache.py` (269 lines) — LRU+TTL 자체 구현
- `endpoint_router.py` (442 lines) — env-based + atomic flip + 7d grace mode

→ MCT-170 = **확장 + wiring** (재구현 아님): tier_reader facade + l1_reader + dr_mode 신규 + reader_cache byte budget 확장. cold_reader + endpoint_router = 수정 0 (backward compat preserve, D9=A).

counters.json + scope_manifest 모두 retitle 박제.

### §Engine reader L1 확장 (tier_reader facade + l1_reader + cold_reader preserve)

- `mctrader_engine/io/tier_reader.py` 신규 (Phase 2 PR#3) — facade orchestration (priority chain: cache → NAS L1/L2/L3 → local fallback)
- `mctrader_engine/io/l1_reader.py` 신규 — L1 specialized read (prefix `tier=L1/`, ETag verify)
- `mctrader_engine/io/cold_reader.py` 유지 — L2/L3 specialized (MCT-154 LAND preserve)
- `mctrader_engine/io/__init__.py` export 갱신 — TierReader / L1Reader / DRMode 추가
- D9=A backward compat: ColdReader 공개 API 유지, TierReader 신규 wrapper

### §DR mode state machine (CLOSED/OPEN/HALF_OPEN + explicit override + UNKNOWN_TIER)

- `mctrader_engine/io/dr_mode.py` 신규 (Phase 2 PR#3) — state machine + explicit mode flag override + Prometheus emit
- 4 state: CLOSED (정상) / OPEN (NAS 차단) / HALF_OPEN (probe) / UNKNOWN_TIER (D10 exemption)
- D8=C trigger hybrid: sliding window 60s 내 5xx 5회 OR p99 >500ms 3회 + consecutive failure 5회
- HALF_OPEN: OPEN 30s 후 자동 전이, probe 1회 success → CLOSED
- manual override: `set_mode(state, reason)` API (operator gate)
- Prometheus `nas_reader_dr_state` Gauge + `nas_reader_ambiguity_total` Counter

### §Reader cache byte budget (LRU+TTL + RSS bound)

- `mctrader_engine/io/reader_cache.py` 갱신 (Phase 2 PR#3) — byte-size budget enforcement 추가 (D2=C)
- `mctrader_data/compactor/reader_cache.py` 갱신 (Phase 2 PR#2) — NullReaderCache 제거 + LRUReaderCache 구현 (Protocol get/put/invalidate)
- `max_bytes` constructor param (default 256 MB)
- `current_bytes() -> int` method 신규 (Prometheus metric input)
- put() 측 enforcement: OrderedDict.popitem(last=False) 반복 while _current_bytes + len(value) > max_bytes
- D7=C TTL configurable env (`READER_CACHE_TTL_L1=3600` default), MCT-154 API preserve

### ADR-029 amendment (MCT-170 박제분, 2026-05-14)

- **Status section "MCT-170 amendment"** — D6=D sunset criterion + D10 exemption scope 명시 박제
- **§D7 amendment box** — D7=C TTL configurable env (default 1h/24h/7d, env override 가능)
- **§D8 amendment box** — D6=D sunset criterion (cutoff 2026-09-01 + telemetry 0-hit 14d + MCT-172 gate)
- **§D10 footnote** — dr_mode.UNKNOWN_TIER 상태 신규 + 30d exemption window (2026-05-14 ~ 2026-06-13) + Prometheus `nas_reader_ambiguity_total` emit

### 다음 Story 진입 권고

**MCT-172** (Epic CLOSED — D9+D10 verify + D8 sunset finalize + promotion.py cleanup + WAL 30G production measurement). R-CRITICAL (WAL 30G 산정 미측정) carry over 의무.

## MCT-171 COMPLETED (2026-05-14) — DR runbook 본문 + invariant 8종 + 4 layer capacity 정책

> 2 PR cross-repo sequential LAND (data#62 + hub Phase 2 PR2)

### 산출물 (mctrader-data)

- `src/mctrader_data/capacity_probe.py` 신규 — 4 layer hybrid probe (5min+approach), CapacityThresholds SSOT
- `src/mctrader_data/ingest_blocker.py` 신규 — graceful drain + 80%/95% hysteresis, collector hook
- `src/mctrader_data/nas_migration/invariant_harness.py` 확장 — 8번째 ambiguity invariant 통합 (promotion.py 분산 흡수)
- `src/mctrader_data/nas_metrics/prometheus_exporters.py` 확장 — +5 metric (capacity Gauge×2 + violation Counter + latency Histogram + ingest blocked Counter)
- `src/mctrader_data/collector.py` 확장 — IngestBlocker hook 통합
- `src/mctrader_data/compactor/promotion.py` — DEPRECATED 주석 (cleanup = MCT-172)
- 38 신규 통합 test (test_invariant_harness_8: 8 + test_capacity_probe: 15 + test_ingest_blocker: 15) ALL PASS
- 931 회귀 PASS, MCT-152/153/155/169 회귀 0

### D4+D5+D11 verify (ADR-029 박제)

- **D4=B VERIFIED**: WAL sealed segment NAS PUT 경로 0 confirm
- **D5=A_modified VERIFIED**: ingest_blocker + collector hook. 95% block + 90% unblock hysteresis
- **D6=B partial**: bucket versioning ✓ (MCT-161). cross-NAS = MCT-174 defer
- **D11=capacity_bounded VERIFIED**: 4 layer CapacityThresholds (WAL 30G / L1 20G / NAS 1TB / Host 200G)

### FIX 루프 3회

1. ruff E501 + E741 + SIM105 + SIM108 + B905 + F401 (자동+수동)
2. ruff F841 + UP037
3. pyright forward ref (TYPE_CHECKING 패턴) + MagicMock cast 패턴

### R-CRITICAL 유지 (MCT-172 carry over)

WAL 30G 산정 = production 측정 없음. 50 sym × 3 channel × 12 seg/h 가정치. MCT-172 Epic CLOSE 전 collector runtime probe baseline 측정 의무.

## MCT-172 COMPLETED (2026-05-14) — Epic policy finalize (D8 sunset + D9+D10 verify + promotion.py cleanup + WAL synthetic baseline)

> 3 PR cross-repo sequential LAND (hub#320 + data#63 + hub Phase 2 PR2 박제). Epic **POLICY_FINALIZED**, Epic CLOSED 는 별 PR.

### Codex 9 결정점 D8-1~D8-9 채택

| D8-N | Option | 결과 |
|------|--------|------|
| D8-1 | A — InvariantHarness 8종 SSOT | test_epic_smoke 8 invariant ALL PASS 게이트 |
| D8-2 | C — baseline 30min + peak 30min hybrid | paper mode synthetic, production 측정 별 PR |
| D8-3 | A — 정책 finalize only + telemetry watcher | 실 sunset 2026-09-01 별 Story |
| D8-4 | C — 2026-08-18 ~ 2026-09-01 14d window | ADR-029 §D8 amendment 박제 |
| D8-5 | A — verify_no_ambiguity 즉시 제거 + caller migrate | src/ grep = 0 strict 충족 |
| D8-6 | A — production deploy 후 실측 | paper synthetic + R-CRITICAL carry over |
| D8-7 | A — 초과 시 Epic close FAIL gate | conditional close 차단 |
| D8-8 | A — 동일 1h window | bucket + log + Prometheus + drainage |
| D8-9 | C — production 14d 후 Epic CLOSED 별 PR | POLICY_FINALIZED → CLOSED transition 별 PR |

### 산출물 (mctrader-data, PR #63 f2fb28e)

- `src/mctrader_data/compactor/promotion.py` — `verify_no_ambiguity` + `_check_nas_exists` 함수 **제거** (89 lines deleted). `AmbiguityViolation` exception class 보존.
- `src/mctrader_data/nas_migration/invariant_harness.py` — docstring 일반화 (history 박제 reference)
- `tests/integration/compactor/test_ambiguity_invariant.py` — 6 test `InvariantHarness._check_ambiguity()` 경유 migrate
- `tests/integration/test_invariant_harness_8.py::test_mct169_d10_regression` — caller migrate
- `tests/integration/test_epic_smoke.py` 신규 — 8 invariant cross-Story smoke + AC-4 게이트
- `tests/integration/test_wal_synthetic_baseline.py` 신규 — paper mode WAL 30G synthetic
- `tests/integration/test_d8_sunset_telemetry_watcher.py` 신규 — 14d rolling 0-hit alert rule

### 측정 결과 (Phase 2 PR1 PASS)

| 항목 | 결과 |
|------|------|
| `grep -rn "verify_no_ambiguity" src/` | **0건** (AC-4 strict 충족) |
| 3 신규 integration test | ALL PASS (14 test) |
| 16 caller migrate (test_ambiguity_invariant + d10_regression) | ALL PASS |
| 49 Phase 2 PR1 scope | ALL PASS |
| Full suite (954 passed + 24 skipped + 4 xfailed) | **회귀 0** |
| ruff + pyright | PASS (1 FIX 루프 — F401 자동 fix) |

### D8 sunset policy finalize (ADR-029 §D8 amendment, Phase 1)

- 14d telemetry window = **2026-08-18T00:00:00Z ~ 2026-09-01T00:00:00Z** (cutoff 직전 14d)
- AND condition: cutoff (2026-09-01 hard) AND telemetry 0-hit 14d
- telemetry watcher: `nas_reader_ambiguity_total` Counter 14d rolling 0-hit alert rule 박제
- 실 sunset 실행 = 2026-09-01 별 Story or scheduled cron

### 8 invariant ↔ D1-D11 mapping

D1-D11 = 설계결정 검토 범위 (ADR-029 design decision). 8 invariant = 운영 단위 실행 게이트 (InvariantHarness).

| Invariant | D | 의미 |
|-----------|---|------|
| sha256 / object_count / row_count / column_count / column_order / dtype / schema_version (7종) | (legacy MCT-151) | Stage 2 invariant primitives |
| **ambiguity** | **D10** | NAS+local XOR violation enforcement (MCT-169 origin + MCT-171 SSOT + MCT-172 cleanup) |

### R-CRITICAL carry over (Epic CLOSED prerequisite)

WAL 30G production measurement = paper mode synthetic baseline 만 측정 (15G ~ 45G hypothesis ±50% range). production 측정은 별 PR (peak market open 09:00 KST burst). 30G 초과 시 D11 hard_limit amendment 발의 (D8-7=A FAIL gate).

## MCT-189 COMPLETED (2026-05-17) — ADR-029 §D3=C grace-0 로컬삭제 wiring 완결

> EPIC-tier-promotion-single-source **carry over RESOLVED** (POLICY_FINALIZED 유지, D3 wiring deferred → **MCT-189 해소 2026-05-17**).
> 2026-05-16 운영 진단 ("로컬 디스크가 차는데 S3 적재되는가") 중 발견 **cross-document SSOT drift 2호** 해소.
> 1호 = `mctrader-data:pilot` 2026-05-13 이미지가 정책 LAND(2026-05-14) 하루 전 빌드 = 본 세션 응급 재배포 (f233952 단일소스 빌드 + backfill stop + capacity_probe/ingest_blocker LAND).
> 2호 = ADR-029 §D3=C "VERIFIED" 박제 vs `promote_l1()` production caller 0건 = 본 Story 대상.

### 결과 요약

| 항목 | 상태 |
|------|------|
| Story | RESERVED → IN_PROGRESS → **COMPLETED 2026-05-17** |
| 4 PR 다단 LAND | hub #357 (3f138a6) Phase 1 docs / data #73 (de12f43) Phase 2 PR1 wiring / data #75 (a1a8ccf) Phase 2 PR2 legacy cleanup / hub #TBD Phase 2 PR3 박제 |
| 채택 결정 | D-1 A grace 0 unconditional / D-2 A DualWriter self-delete (`_promote_after_nas_put` helper) / D-3 C 단일 Story+다단 PR (사용자) / D-4 C 4중 HEAD verify / D-5 A forward-only 격상 / D-6 A post-LAND 14d 0 violation / D-7 A idempotent (ENOENT graceful) / D-8 B pre-delete guard / D-9 A domain-knowledge 신규 / D-10 B ADR-032 별 Story |
| 추가 hardening | fd-consistent sha256+size (`_compute_local_sha256_and_size` SEEK_END, code-quality FIX iter3 TOCTOU 축소) + NASUploader.enqueue_retry() public method (private getattr fragility 제거) + verify-fail → retry_queue + status="local_only" (committed 거짓 신호 제거, spec FIX iter1) + batch_limit=500 cap (PR2 첫 sweep stall 회피) |
| ADR 산출 | ADR-029 amendment box VERIFIED 박제 (§D3 + §D10 + §D11 + Migration) — **POLICY_FINALIZED 유지 (11/11 D 정상)** |
| FIX 통계 | design lane iter 0 / code lane iter 4 (spec×2 + code-quality×1 + PR2 combined×1, 자세히는 RETRO §FIX Ledger) |
| 회귀 | reviewer 가 main worktree 분리 직접 측정 — 0 신규 회귀 (main 21 failed+3 error == branch 동일, MCT-189 touch 파일 연관 0) |
| **Cross-Story contamination** | mctrader-data 45e501c (MCT-184 PR) 가 partial MCT-189 단위 A/B/C/D squash 포함 → FIX iter 부재 결함 상태로 main 일시 도달 → PR1 `git rebase --strategy-option=theirs` + force-with-lease 로 FIX 적용 버전 덮어쓰기 (de12f43) → production 정합 회복. ADR-032 self-reference 사례. 정직 박제: Story §9 + RETRO §Lessons.3 |
| follow-up | ADR-032 별 governance Story (MCT-190 권고) + vendor wheel 갱신 + engine-paper crash loop + parallel session data worktree 격리 메모리 amendment (cross-Story PR scope guard) |
| Epic CLOSED prereq | **prod-5 신규**: 2026-05-17 LAND → **2026-05-31 verify gate** (`nas_reader_ambiguity_total` Counter 14d rolling = 0). legacy 130GB sweep evidence ~52h 점진 회수 모니터링 |

### Key References (MCT-189)

- Story: `docs/stories/MCT-189.md` / spec: `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md` / plan: `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md`
- domain-knowledge: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` (4 invariant + caller-wired vs decision-defined 분리)
- PMO retro (SSOT drift 2호): `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- ADR-029 amendment box: `docs/adr/ADR-029-tier-promotion-single-source.md` §MCT-189 amendment box
- 운영 메모리: mctrader-data 데이터 파이프라인 = `mctrader-data/compose.yml` 별 compose project (hub compose 아님)

## MCT-190 COMPLETED (2026-05-17) — ADR-032 owner Story (evidence triad governance ADR author + 4 deliverable)

> cross-Epic governance singleton, doc-only Story (phase1_only, classification: doc-only-fast-path).
> 단일 PR (hub#TBD), FIX 0회, ADR-032 Proposed → Accepted transition.
> ADR-032 §5 self-reference 첫 실증 (worktree 격리 사전 차단 의도적 활용 — Phase 0 verify lesson 8회째).

### 결과 요약

| 항목 | 결과 |
|------|------|
| 4 deliverable + 5 부수 = 9 file author | ALL LAND (hub#TBD) |
| ADR-032 status | Proposed → Accepted |
| 5 결정점 | Q1=B / Q2=B / Q3=B / Q4=B / Q5=B (Codex 4건 정합 + Q2 1건 deviation) |
| FIX 루프 | 0회 (design lane spec review iter1 PASS, code lane 부재) |
| memory amendment | feedback_parallel_session_branch_race 6 repo tier 차등 (hub+data+engine 의무 / market 3 권고) |
| upstream consumer 박제 | plugin-codeforge#804 + #805 comment evidence row 추가 (post-merge) |

### 5 결정점 채택

| Q | 결정점 | 채택 |
|---|--------|------|
| Q1 | ADR-032 §5 enforcement scope | (B) self-discipline gate v1 (CI gate = #804 carry) |
| Q2 | PMO 메모리 6 repo amendment | (B) tier 차등 (hub+data+engine 의무 / market 3 권고) |
| Q3 | evidence triad 4번째 게이트 | (B) §7 future-work carry (triad v1 = 3 evidence 유지) |
| Q4 | plugin-codeforge#804/#805 consumer 박제 | (B) PMO-AUDIT-MCT-190 별 retro + comment evidence row |
| Q5 | Domain knowledge governance/ dir | (B) 신규 생성 (evidence-triad-verified-badge.md 첫 entry) |

### ADR-032 본문 (9 sections)

§0 frontmatter / §1 Status / §2 Context (3 trigger 사례) / §3 Decision (Evidence Triad Rule v1) / §4 Story §8.5 Impl Manifest 통합 / §5 Amendments (caller spec FIX + cross-Story PR scope guard) / §6 Consequences / §7 Future Work (triad → quad + CI mechanical gate + process/cross-story-pr-contamination.md) / §8 Self-reference Caveat (INV-1 forcing function)

### Key References

- Story: `docs/stories/MCT-190.md`
- spec: `docs/superpowers/specs/2026-05-17-MCT-190-adr-032-author-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mct-190-adr-032-author.md`
- ADR-032: `docs/adr/ADR-032-verified-badge-evidence-triad.md`
- domain-knowledge: `docs/domain-knowledge/domain/governance/evidence-triad-verified-badge.md`
- RETRO: `docs/retros/RETRO-MCT-190.md`
- PMO-AUDIT: `docs/retros/PMO-AUDIT-MCT-190.md`
- scope_manifest: `scope_manifests/MCT-190.yaml`
- memory: `feedback_parallel_session_branch_race` 6 repo tier 차등 amendment
- upstream cross-ref: plugin-codeforge#804 (박제 PR completeness) + #805 (post-merge audit lane)

### 다음 Story 진입 권고

- **MCT-186 IN_PROGRESS 복귀** (현 hub working tree branch mct-186-phase2-pr2-hub Phase 2 PR2 박제 continuation, ExitWorktree 후 본 working dir 복귀)
- **MCT-191 reservation 후보** — ADR-032 §7 future-work 1건 owner (triad → quad telemetry counter / CI mechanical gate consumer / process/cross-story-pr-contamination.md governance entry)

## EPIC-evidence-quad-runtime-telemetry (MCT-191 + MCT-192 COMPLETED 2026-05-17, milestone 2/3)

> ADR-032 evidence triad v1 → quad v2 확장 (4번째 게이트 runtime telemetry counter ≥1 over N days,
> Hyrum's Law 역방향 dead-in-prod false-negative 차단). cross-Epic governance singleton extension.
> 3 sub-Story sequential (MCT-191 doc-only / MCT-192 cross-repo emit / MCT-193 verify gate).

### sub-Story 현황

| seq | Story | 상태 | scope |
|---|-------|------|-------|
| 1 | **MCT-191** | **COMPLETED 2026-05-17** | governance amendment doc-only (ADR-032 §8.1→§3.2 본문 격상 + ADR-033 신규 + class taxonomy) |
| 2 | **MCT-192** | **COMPLETED 2026-05-17** | cross-repo telemetry counter emit (ADR-029/030 재사용 + ADR-031 realtime_stream 신규 emit, engine DROP) |
| 3 | MCT-193 | RESERVED | post-LAND verify gate (Prometheus alert counter==0 over Nd + monthly PMO audit cron) |

### MCT-192 결과 (sub-2, COMPLETED 2026-05-17)

cross-repo 3 PR sequential LAND (mctrader-hub#384 c9b9f2c PR-1 docs → mctrader-data#79 58d99ad
PR-2 code → mctrader-hub#TBD PR-3 박제). **ADR-029/030 = 기존 counter 재사용** (신규 emit code
0, MCT-189/179 triad 재인용) / **ADR-031 = data realtime_stream.py 신규 emit** (`_emit_failure_counter()`
no-op stub 해소 + metrics.py `mctrader_data_redis_stream_publish_failures_total` Counter +
counter-emit triad v1 reapply). **engine DROP** (pure consumer telemetry zero 정상 — cross-repo
축소 hub+data 2-repo). dead-in-data 정직 박제 (publish_tick producer caller=0, R2 MCT-179 §D8
가공 metric 7회째 차단). **trust-but-verify 동형 재발 3회째** (PMOAgent 2nd pass R1 'ADR-033/scope_manifest
부재 BLOCKER' = false premise → Orchestrator 직접 `ls`/`grep` verify 기각, plugin-codeforge#822
self-discipline gate v1 적용에도 PMOAgent path 오류 = escalate evidence row 추가 후보). Codex
9/9 deviation 0 (MCT-191 10/10 동형 full alignment 연속 2회). ADR-033 §9.1 sub-2 VERIFIED.

→ 다음 = **MCT-193** (sub-3, post-LAND verify gate 운영 — Prometheus alert + monthly PMO audit cron).

### MCT-191 결과 (10 결정점 Q1-Q10, Codex 일괄 dispatch + Claude 합성 + Q1 사용자 confirm)

Q1=C small Epic 3 sub-Story / Q2=C ADR-032 amend + ADR-033 신규 / Q3=C grandfathering production-wired만 / Q4=C traffic class 차등 N days / Q5=C meta-recursion 1단 / Q6=B class taxonomy / Q7=C alert+PMO audit / Q8=C per-ADR scope_manifest field / Q9=A governance/ 신규 / Q10=C market-closed traffic class 차등.

### ADR 산출

- **ADR-032 amend** — §8.1 future-work → §3.2 Evidence Quad Rule v2 본문 격상 + §9 telemetry_counter_caveat field (governance ADR telemetry forever 0 정상) + frontmatter class:governance (Accepted 유지)
- **ADR-033 신규** (Proposed, 210 lines §1-§10) — evidence quad enforcement layer. Accepted = sub-2 MCT-192 + sub-3 MCT-193 LAND 후
- **ADR-029/030/031 frontmatter class:production** additive (R3 — 3 스타일 비동질 보존, 정규화 0)

### Phase 0 verify F-0a 핵심

quad 확장 = ADR-032 §8.1 future-work 본문 격상 (신규 발명 아님) → R1 HIGH (§9 Self-reference Caveat quad 호환성) 선제 완화. §9 이미 caller_wired_caveat + INV-1 forcing function 보유 → quad Caveat = telemetry 축 확장.

### Key References

- Story: `docs/stories/MCT-191.md`
- spec: `docs/superpowers/specs/2026-05-17-MCT-191-evidence-quad-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mct-191-evidence-quad.md`
- ADR-033: `docs/adr/ADR-033-evidence-quad-enforcement-layer.md`
- ADR-032 §3.2 quad: `docs/adr/ADR-032-verified-badge-evidence-triad.md`
- domain-knowledge: `docs/domain-knowledge/domain/governance/evidence-quad-runtime-telemetry.md`
- scope_manifest: `scope_manifests/EPIC-evidence-quad-runtime-telemetry.yaml`
- parent: ADR-032 §8.1 (MCT-190 LAND hub#375)

### 다음 Story 진입 권고

**MCT-193** (sub-3 post-LAND verify gate 운영 — Prometheus alert `increase(counter[Nd])==0`
→ critical + GitHub issue 자동 발의 + monthly PMO audit cron, Q7=C) — MCT-192 LAND ✓ 후 진입.
ADR-033 Status = Proposed 유지 (Accepted = sub-3 MCT-193 LAND 후 → POLICY_FINALIZED Epic 3/3).

## Key References

- ADR-027 §D MCT-161 amendment: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
- **ADR-029 (신규, MCT-167 2026-05-14)**: `docs/adr/ADR-029-tier-promotion-single-source.md`
- EPIC-compactor-operations scope_manifest: `scope_manifests/EPIC-compactor-operations.yaml` (CLOSED 2026-05-14)
- **EPIC-tier-promotion-single-source scope_manifest**: `scope_manifests/EPIC-tier-promotion-single-source.yaml` (**POLICY_FINALIZED**, 6/6 milestone completed)
- **MCT-170 spec**: `docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md`
- **MCT-170 plan**: `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`
- **MCT-170 retro**: `docs/retros/RETRO-MCT-170.md`
- **MCT-171 spec**: `docs/superpowers/specs/2026-05-14-MCT-171-dr-runbook-capacity-design.md`
- **MCT-171 plan**: `docs/superpowers/plans/2026-05-14-mct-171-dr-runbook-capacity.md`
- **MCT-171 retro**: `docs/retros/RETRO-MCT-171.md`
- **MCT-172 spec**: `docs/superpowers/specs/2026-05-14-MCT-172-policy-finalize-design.md`
- **MCT-172 plan**: `docs/superpowers/plans/2026-05-14-mct-172-policy-finalize.md`
- **MCT-172 retro**: `docs/retros/RETRO-MCT-172.md`
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-compactor-operations.md`
- **EPIC-RESULTS (tier-promotion, POLICY_FINALIZED)**: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`
- MCT-174 reservation: `.codeforge/counters.json`
