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
- `scripts/` — NAS admin + 운영 스크립트
- `.codeforge/counters.json` — Story key reservation SSOT

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
Status: Proposed (MCT-175 Phase 1 박제, LAND 시 Accepted)

### 7 Story sequential chain

| sequential_phase | Story | 상태 | 결정 | 내용 |
|---|-------|------|------|------|
| 1 | **MCT-175** | **COMPLETED 2026-05-15** | D1/D3/D7/D13 | compose base + dev/prod profile + env 분리 + cross-repo lock gate + ADR-030 (hub#326 + hub#327 + hub#328) |
| 2 | **MCT-176** | **COMPLETED 2026-05-15** | D7/D9/D14 | collector container + NAS credential rotation + effective config dump (hub#330 + data#64 + hub#331 + Phase 2 PR2) |
| 3 | **MCT-177** | **COMPLETED 2026-05-15** | D2/D4/D10/D15 | paper-engine daemon + SIGTERM graceful + universe override + Redis prefix (hub#333 + data#65 + engine#54 + hub#334 + Phase 2 PR2) |
| 4 | MCT-178 | PLANNED | D2/D4/D10/D16 | backtest-runner profile + oneshot + compose config CI lint + signal-collector Redis prefix code migration (D15 carry) |
| 5 | MCT-179 | PLANNED | D5/D8/D17 | observability + WAL 30G production measurement + DR mode + alert |
| 6 | MCT-180 | PLANNED | D4/D11/D18 | integration smoke + testcontainers + resource limits + alert rule |
| 7 | MCT-181 | PLANNED | D12/D19 | image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED |

### Key References

- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- runbook stub: `docs/runbooks/docker-stack-deploy.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md`

### Risk 현황

| Risk | Severity | 상태 |
|------|----------|------|
| R1 NAS HTTP-only 평문 | HIGH | **사용자 explicit accept (2026-05-15)** — MCT-155 TLS cutover 별 Story 백로그 |
| R2 WAL 30G 미측정 | CRITICAL | MCT-179 에서 peak 09:00 KST 1h burst 측정 의무 (EPIC-tier-promotion CLOSED prereq) |
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

**MCT-178** (backtest-runner profile + oneshot + compose config CI lint + universe override) — sequential_phase 4.
진입 prerequisite = MCT-177 Phase 2 PR2 MERGED ✓ + MCT-178 carry over 통합:
- **signal-collector 5종 Redis prefix code migration** (D15 carry — unprefixed → `signal:*` rename + 1주일 dual write + Prometheus `redis_key_migration_dual_write_active` Gauge + LAND+7d legacy cleanup)
- `${IMAGE_TAG}` prod pin (D12, MCT-181 owner — dev=latest 현행 유지)

채택 결정: D2 (backtest profile oneshot 동일 image) + D4 (SIGTERM 회귀) + D10 (universe override) + D16 (compose config lint + up --wait CI gate).

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
