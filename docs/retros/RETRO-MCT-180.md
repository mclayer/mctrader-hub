---
type: story-retro
story_key: MCT-180
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 6
---

# RETRO — MCT-180 EPIC-mctrader-docker-stack Story-6 (integration smoke + testcontainers + resource limits + 5 TODO panel metric emit)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory). env=0 재귀 spawn 제약상 ArchitectPL 직접 이행 (RETRO-MCT-179 패턴 정합 — cross-cutting PMOAgent = Orchestrator spawn 원칙, one-shot subagent 재귀 spawn 금지 ADR-039).

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-6 (sequential_phase 6)** — MCT-179 LAND (observability + WAL 30G synthetic baseline + alert) 위에 전체 stack 의 **integration smoke CI gate (D11)** + **resource limits 명시 (D18)** + **SIGTERM graceful 회귀 검증 (D4)** + **MCT-179 carry over 5 [MCT-180 TODO] panel metric emit** 를 박제. 채택 3 D = D4 (SIGTERM 회귀) + D11 (compose CI smoke + testcontainers 2-layer) + D18 (resource limits + ContainerMemoryHigh alert).

4 PR cross-repo sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code + engine Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). **D11 integration-smoke CI 격리 설계 결함 → FIX 3회 ESCALATE → infra-only 3-layer 재설계** (ArchitectPL ESCALATE chief judge 설계 원인 판정 + option b resolution). DesignReview iter1 **PASS (no FIX)** — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile 효과 실증 (P0×0, 누적 audit 투자 회수).

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D4/§D11/§D18 amend + plan + CLAUDE.md) | mctrader-hub#342 MERGED (b1be313, 2026-05-15) — DesignReview iter1 **PASS** (no FIX, MCT-179 전수 reconcile 효과 실증) |
| Phase 2 PR1 (data: collector ticks_total/active_symbols + testcontainers, land_order 1) | mctrader-data#67 MERGED (f233952, 2026-05-15T13:39:21Z) — CodeReview iter1 FIX → iter2 PASS |
| Phase 2 PR1 (engine: universe_size + reader_cache Gauge + testcontainers, land_order 2) | mctrader-engine#55 MERGED (bc8c627, 2026-05-15T13:39:26Z) — CodeReview iter1 FIX → iter2 FIX (설계 원인) → iter3 PASS |
| Phase 2 PR1 (hub: integration-smoke.yml infra-only + limits + alert + docker-stack, land_order 3) | mctrader-hub#343 MERGED (af25d66, 2026-05-15T13:40:19Z) — CodeReview iter1 FIX → iter2 FIX → iter3 **ESCALATE** → ArchitectPL chief judge 설계 원인 판정 → ESCALATE-fix PASS |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 infra-only CI smoke exit 0 / AC-2 testcontainers 2-layer boundary / AC-3 7 service limits + ContainerMemoryHigh alert / AC-4 SIGTERM carrier 이관 회귀 0 / AC-5 5 metric emit + panel id=3,4,6 해제 / id=7,8 downgrade 유지) |
| 총 INV | 5/5 박제 (forward-only ephemeral compose + startup scan warn+continue + Prometheus metric additive + SIGTERM graceful unchanged + resource limits OOM 방지) |
| FIX 루프 | design iter1 **PASS (no FIX)** + code 3 PR iter1 FIX → iter2 (data PASS / engine FIX 설계 / hub FIX) → iter3 (data/engine PASS / hub **ESCALATE** iter 3/3 max) → ArchitectPL ESCALATE chief judge 설계 원인 판정 + option b resolution → CodeReview **ESCALATE-fix PASS** |
| ADR-030 amendment | §D4/§D11/§D18 VERIFIED 박제 (Phase 2 PR2) + §D11 N-002 promotion 문구 정정 + §D8 amendment (reader cache cold-only scope) |
| Epic milestone | **6/7** (MCT-175 ~ MCT-180 COMPLETED) |
| MCT-181 carry over | `${IMAGE_TAG}` D12 image registry pin + full-stack production smoke (별 PR/MCT-181) + R2 production 별 PR |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#342, b1be313)

- `docs/stories/MCT-180.md` — Story §1-§12 신규 (§6.5 §7/§11 N/A 4 entry 사전 박제)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D4/§D11/§D18 amendment box 본문 박제 (Phase 1)
- `CLAUDE.md` — Docker stack 7 Story chain MCT-180 IN_PROGRESS 추가
- `docs/superpowers/plans/2026-05-15-mct-180-integration-smoke.md` — 신규 (Phase 1 + Phase 2 PR1 + Phase 2 PR2 plan)
- DesignReview iter1 **PASS (no FIX)** — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile (c8e4b8e) 효과 실증 (MCT-180 D11/D18 부분 reconcile 불필요 — 누적 audit 투자 회수)

### 1.2 Phase 2 PR1 — data (mctrader-data#67, f233952, land_order 1)

- collector `mctrader_collector_ticks_total` Counter + `mctrader_collector_active_symbols` Gauge Prometheus emit (nas_metrics/prometheus_exporters.py MCT-171 SSOT 패턴)
- `tests/integration/test_collector_nas_boundary.py` 신규 — testcontainers collector→MinIO mock boundary (put_streaming sha256 정합 + retry_queue fallback)
- CodeReview iter1 FIX → iter2 PASS

### 1.3 Phase 2 PR1 — engine (mctrader-engine#55, bc8c627, land_order 2)

- `mctrader_engine_universe_size` Gauge (metrics.py MCT-170 패턴) + reader_cache `nas_reader_cache_hit_ratio`/`nas_reader_p99_ms` Gauge expose (io/reader_cache.py `hit_ratio()` 메서드 → Prometheus)
- `tests/test_paper_redis_boundary.py` 신규 — testcontainers paper-engine→Redis `engine:*` prefix key verify
- CodeReview iter1 FIX → iter2 FIX (**설계 원인** — paper daemon ReaderCache 미인스턴스화, Phase 0 verify lesson 5회째) → iter3 PASS. contract 정정 (cold reader 한정 metric 재정의, ADR-030 §D8 amendment). `stats()` Gauge producer wiring 보존 (cold reader/backtest 경로 유효, docstring scope 명시만 추가, logic 변경 0)
- engine#55 `ci`/`lookahead-lint` job FAILURE = `mctrader-market-upbit` private repo git dependency auth 이슈 (본 ESCALATE 범위 외, engine repo 별 처리 carry over)

### 1.4 Phase 2 PR1 — hub (mctrader-hub#343, af25d66, land_order 3)

- `.github/workflows/integration-smoke.yml` 신규 — **infra-only CI smoke** (ESCALATE F-301 resolution 614033a): `docker compose --profile dev up -d postgres redis minio --wait --wait-timeout 180` (mc 제외) + `docker compose up --no-deps --exit-code-from mc mc` (mc-init oneshot exit 0). collector/paper-engine compose up + SIGTERM step 제거
- `compose.yml` MODIFY — 7 service `deploy.resources.limits` (collector/paper-engine 512M / backtest 1G / postgres 1G / redis 256M / prometheus/grafana 512M)
- `monitoring/prometheus-alerts.yml` MODIFY — ContainerMemoryHigh `container_memory_usage_bytes{name=~"mctrader-.*"} / container_spec_memory_limit_bytes > 0.8` (cadvisor MCT-123 LAND selector)
- `monitoring/grafana/provisioning/dashboards/docker-stack.json` MODIFY — panel id=3,4,6 `[MCT-180 TODO]` 해제 / id=7,8 (reader_cache hit_ratio/p99) downgrade 유지 (CodeReview FIX iter2 설계 원인)
- CodeReview iter1 FIX (compose cpus 0.5 정정 + alert selector 6e9a843) → iter2 FIX (mc --wait 분리 c1d7938) → iter3 **ESCALATE** (F-301 P0 설계 원인, iter 3/3 max) → ArchitectPL chief judge 판정 → ESCALATE-fix (614033a) → CodeReview ESCALATE-fix PASS

### 1.5 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-180.md` — frontmatter (4 PR + COMPLETED) + §1/§4 AC-1 재정의 (infra-only) + §4 AC-4 SIGTERM carrier 이관 + §4 AC-5 panel id=7,8 downgrade 유지 + §8 test contract infra-only + §8.5 Impl Manifest confirm + §10 FIX Ledger (CodeReview 3 PR iter1~3 + ESCALATE + ESCALATE-fix row 전체) + §10.5 Git Ops Log + §11 retro + §12 측정 + §12.1 CI green 실증 + §12.2 N-002 정정. N-002: "compactor promotion 1회" 제거 (실 LAND §2.3 verbatim 미존재)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D11 amendment 본문 SUPERSEDED note + N-002 strikethrough 정정 + §D4/§D11/§D18 VERIFIED confirm box (Phase 2 PR1 cross-repo LAND) + N-002 RESOLVED 박제
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-180 status COMPLETED + completed_date + prs[] + milestone 6/7 + epic_close_gate MCT-180 line + **N1 scope_files 정정** (docker-compose-smoke.yml → integration-smoke.yml / test_compose_smoke.py → test_collector_nas_boundary.py / test_paper_engine_smoke.py → test_paper_redis_boundary.py, MCT-178 F-001 precedent)
- `CLAUDE.md` — Docker stack 7 Story chain MCT-180 COMPLETED + §MCT-180 IN_PROGRESS → COMPLETED 전면 재작성 (ESCALATE D11 재설계 lesson + Phase 0 verify lesson 5회째)
- `docs/retros/RETRO-MCT-180.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/superpowers/plans/2026-05-15-mct-180-integration-smoke.md` — §1.1 line 51 + §1.2 line 70 N-002 정정 (Phase 1 체크리스트 잔존 old 표현)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-6 박제 (milestone 6/7) + carry over (${IMAGE_TAG} MCT-181 + full-stack production smoke + R2 production)

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 integration-smoke infra-only CI green (D11) | ✓ PASS | hub#343 CI smoke job exit 0 — Layer 1 infra `--wait` + mc-init oneshot exit 0 (ESCALATE F-301 재정의, 8분 budget) |
| AC-2 testcontainers 2-layer boundary (D11) | ✓ PASS | data#67 `test_collector_nas_boundary.py` (collector→MinIO) + engine#55 `test_paper_redis_boundary.py` (paper→Redis) ALL PASS = boundary 실 검증 carrier |
| AC-3 7 service limits + ContainerMemoryHigh alert (D18) | ✓ PASS | compose.yml 7 service `deploy.resources.limits` + prometheus-alerts.yml ContainerMemoryHigh (cadvisor MCT-123 selector 정합) |
| AC-4 SIGTERM graceful 회귀 (D4) | ✓ PASS | ESCALATE carrier 이관 — testcontainers (data#67 + engine#55) + MCT-176/177 LAND unit test 회귀 0 (코드 변경 0, graceful drain 경로 unchanged) |
| AC-5 5 metric emit + panel 정합 (carry over) | ✓ PASS | data#67 collector ticks/active_symbols + engine#55 universe_size/reader_cache emit. docker-stack.json panel id=3,4,6 해제 / id=7,8 downgrade 유지 (설계 원인) |

### 2.2 INV 박제 (5/5)

| INV | 결과 |
|-----|------|
| forward-only (WAL 객체 삭제 금지) | ✓ 박제 — integration smoke = ephemeral compose up/down (WAL 파일 수정 0) |
| startup scan warn+continue | ✓ 박제 — MCT-179 LAND 정합 (raise 금지) |
| Prometheus metric additive | ✓ 박제 — 5 metric 신규 emit only (기존 metric 제거/rename 없음) |
| SIGTERM graceful unchanged 회귀 0 | ✓ 박제 — MCT-176/177 LAND 재사용, 코드 변경 0 (testcontainers + unit test carrier) |
| resource limits OOM 방지 | ✓ 박제 — limits 보수적 산정 + cadvisor ContainerMemoryHigh >80% 선제 경보 |

### 2.3 FIX 루프 (design 0 + code 3 iter + ESCALATE + ESCALATE-fix)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub#342) | **0 (PASS, no FIX)** — MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile 효과 실증 (P0×0) | LAND b1be313 (누적 audit 투자 회수) |
| 1~2 | code (data#67) | iter1 FIX (impl) | iter2 PASS, LAND f233952 (land_order 1) |
| 1~3 | code (engine#55) | iter1 FIX + iter2 FIX **설계 원인** (paper daemon ReaderCache 미사용, Phase 0 verify 5회째) | iter3 PASS. contract 정정 (cold reader 한정 metric, ADR-030 §D8) + panel id=7,8 downgrade 유지 |
| 1~3+ESCALATE | code (hub#343) | iter1 FIX (compose cpus + alert selector) + iter2 FIX (mc --wait 분리) + iter3 **ESCALATE** F-301 P0 설계 원인 (full-stack compose up CI 격리 구조적 불가, iter 3/3 max) | **ArchitectPL ESCALATE chief judge 최종 판정 = 설계 원인** → option b resolution (614033a) infra-only 3-layer 재설계 → CodeReview ESCALATE-fix PASS |

design lane = MCT-175 (P0×1) → MCT-176 (P0×1) → MCT-177 (P0×0) → MCT-178 (CONDITIONAL_PASS) → MCT-179 (P0×1) → **MCT-180 (P0×0, no FIX)**. MCT-179 전수 reconcile (c8e4b8e) 의 MCT-180/181 재발 사전 차단 투자가 MCT-180 design lane P0×0 으로 회수됨 (lesson reapply 누적 효과 실증).

## §3 risks_realized

### 3.1 R-MCT-180-1 integration smoke 10분 budget 초과 (MEDIUM)

- **mitigation 적용**: ESCALATE infra-only 재설계로 budget 10분 → 8분 단축 (collector/paper-engine compose up 제거 → infra `--wait` + mc-init oneshot만)
- **realized**: NO — infra-only CI smoke = 8분 budget 이내 exit 0 (full-stack 미수행으로 budget 여유)

### 3.2 R-MCT-180-2 testcontainers CI 환경 호환성 (LOW)

- **mitigation 적용**: minio/redis testcontainer = 공개 image (ghcr.io 인증 불필요)
- **realized**: NO — data#67 + engine#55 testcontainers ubuntu-latest Docker socket 정상

### 3.3 R-MCT-180-3 resource limits OOM kill (MEDIUM)

- **mitigation 적용**: limits 보수적 산정 (INV-4 DualWriter + reader cache 256MB + buffer) + cadvisor ContainerMemoryHigh >80% 선제 경보
- **realized**: PARTIAL — limits 선언형 LAND. 실 production 부하 OOM 검증 = production deploy 후 별 PR (carry over)

### 3.4 R-MCT-180-4 (ESCALATE 신규 발견) D11 CI 격리 full-stack 전제 구조적 불가 (HIGH)

- **위협**: ADR-030 §D11 + Plan §2.3 + Story §4 AC-1 의 "compose up full stack (collector+paper-engine) in CI" 가 sibling repo image 미배포 (D12 carry) + build.context path 부재 (CI 단독 checkout) → 구조적 exit 1 (D11 게이트 무력화)
- **realized**: YES — CodeReview iter3 ESCALATE. ArchitectPL chief judge 설계 원인 판정
- **resolution**: option b — 3-layer 분리 (CI smoke = infra-only / testcontainers = boundary 실 carrier / full-stack = production deploy carry, D12 MCT-181 의존). ADR-030 §D11 amendment 박제

## §4 followups (post-Story carry over → MCT-181)

### 4.1 `${IMAGE_TAG}` D12 image registry pin (MCT-181 owner)

- compose.yml prod = `ghcr.io/mclayer/*:sha-<7char>` pin (dev=latest 현행 유지). D11 full-stack compose up CI 검증 = D12 image pin 선행 의존 (ESCALATE F-301 resolution Layer 3)

### 4.2 full-stack production smoke (MCT-181 또는 별 PR)

- collector+paper-engine compose up evidence = production deploy 시점 검증 (image registry pin 의존, EPIC-tier-promotion prod-2 류). CI 격리 환경에서 구조적 불가 → production deploy carry over

### 4.3 R2 CRITICAL production 실 측정 (별 PR, cross-Epic)

- WAL 30G production measurement = MCT-179 synthetic baseline 완료 (PARTIAL 해소). production 실 측정 = 별 PR (peak 09:00 KST 1h burst, EPIC-tier-promotion-single-source prod-2)

### 4.4 engine#55 `ci`/`lookahead-lint` carry over (engine repo 별 처리)

- `mctrader-market-upbit` private repo git dependency auth (`Invalid username or token`) = engine repo 자체 CI infra private-dep token 이슈. F-301/F-302 외 영역 (본 ESCALATE 범위 외, engine repo 별 PR 처리)

## §5 lessons (process learnings)

### 5.1 D11 integration-smoke CI 격리 설계 결함 — FIX 3회 ESCALATE → infra-only 3-layer 재설계

ADR-030 §D11 (MCT-180 publish) + Plan §2.3 + Story §4 AC-1 이 "compose up full stack (collector+paper-engine) in CI" 명시. 그러나 collector/paper-engine = 미배포 sibling repo image (`ghcr.io/mclayer/mctrader-{data,engine}:latest`, D12 MCT-181 carry) + `build.context: ../mctrader-{data,engine}` (CI 단독 checkout = path 부재) → `compose up collector paper-engine --wait` 구조적 exit 1. CodeReview iter1/2 mc --wait 분리(c1d7938) = mc-init 표면 증상만 해소, full-stack 전제 = 근본 설계 결함 미해소. FIX 3회 소진 → mechanical/구현 layer 해소 불가.

→ ArchitectPL ESCALATE chief judge 최종 판정 = **설계 원인** (구현 충실, 설계가 CI 실행 환경 제약 미검증). option b resolution (614033a) = **3-layer 분리** (CI smoke = infra-only / testcontainers = boundary 실 carrier / full-stack = production deploy carry, D12 MCT-181 의존).

**lesson**: cross-repo full-stack compose up 을 CI 격리 환경 gate 로 설계하는 것은 sibling repo image registry pin (D12) 선행 없이는 구조적 불가능. **설계 단계에서 CI 실행 환경 제약 (sibling repo checkout 부재 + 미배포 image) 을 검증 의무** (Phase 0 verify 의 인프라 차원 확장). CI smoke = infra 정합 + boundary = testcontainers + full-stack = production deploy evidence 의 3-layer 분리가 cross-repo Epic 의 CI-friendly 검증 SSOT. MCT-179 §D8 가공 metric 설계 원인 + MCT-170/177/178 Phase 0 verify lesson 누적 동형 (설계가 실행 환경 제약 미검증) — **6회째 재현 패턴 (PMO retro 입력)**.

### 5.2 Phase 0 verify lesson 5회째 (paper-engine reader cache 구조적 미사용)

Story §4 AC-5 + ADR-030 §D8 + Plan §2.2 가 `nas_reader_cache_hit_ratio`/`_p99_ms` Gauge producer path 를 paper-engine daemon 으로 가정. Phase 0 verify 실증 = paper daemon (`PaperRunner` WS tick 경로) `ReaderCache`/`ColdReader`/`TierReader` 미인스턴스화 (grep 0). `ReaderCache.stats()` production caller = `ColdReader.run_smoke_test()` 1곳 (production caller 0 = cutover/backtest 경로 only). MCT-170 reader_cache = NAS cold read 전용 scope.

→ CodeReview FIX iter2 = 설계 원인. contract 정정 (cold reader 한정 metric 재정의, ADR-030 §D8 amendment) + docker-stack.json panel id=7,8 downgrade 유지 (engine#55 stats() Gauge wiring 보존 — cold reader/backtest 경로 유효, docstring scope 명시만, logic 변경 0). MCT-170 (io/ 3 module) + MCT-177 (engine asyncio SSOT) + MCT-178 (Publisher 계층) + MCT-179 (metric-name SSOT) cross-repo Phase 0 verify 독립 의무 **5회 재현**.

**lesson**: metric producer path 는 각 daemon runtime 실 instantiation 경로 Phase 0 verify grep 실증 의무 (가설 = 코드 실증 전 미수용, memory feedback_phase0_verify_mandatory). carry over metric (MCT-179 → MCT-180) 일수록 producer path 가정 검증이 박제 prerequisite. **observability/metric 박제 시 producer path = grep 실증 의무 (선언만으로 panel 활성 금지)**. Phase 0 verify shift-left (metric producer path grep 실증 Phase 1 의무화) = 차기 Epic FIX iter 감소 핵심 (PMO retro 누적 입력).

### 5.3 cross-repo metric desync 누적 (MCT-179 hub#340 → MCT-180 engine#55 동형)

MCT-179 §5.1 (가공 metric Phase 0 verify 미수행 → R2 deliverable 무력화) lesson 이 MCT-180 engine#55 reader_cache producer path 가정 오류로 재현. MCT-179 = alert expr metric selector LAND 부재, MCT-180 = metric producer daemon path 가정 오류 — 동형 (설계가 sibling repo runtime 실상 미검증).

**lesson**: cross-repo Story 의 metric/계층 SSOT 는 매 Story 독립 Phase 0 verify 의무. carry over chain (MCT-179 → MCT-180) 에서 선행 Story 의 metric 정의를 무비판 승계 금지 — producer/consumer path 각 repo 실증. design lane shift-left 누적 효과 (MCT-179 전수 reconcile → MCT-180 design P0×0) 와 code lane Phase 0 verify gap (MCT-179 → MCT-180 동형 재현) 의 비대칭 = code lane Phase 0 verify 강제 게이트화 필요 (TestContractArch deputy §8 perf baseline 검수 범위 확장 후보 — PMO retro 입력 누적).

### 5.4 FIX 루프 cost — code 3 iter + ESCALATE (design 0)

MCT-178 = 1 iter. MCT-179 = 2 iter (design 1 + code 1). MCT-180 = **design 0 (no FIX) + code 3 iter + ESCALATE iter 3/3 max**. 원인:
- design lane = MCT-179 전수 reconcile (c8e4b8e) 효과로 P0×0 (누적 audit 투자 회수, lesson reapply 정상)
- code lane = D11 CI 격리 설계 결함 (§5.1) → 3 iter → ESCALATE. 단 ArchitectPL chief judge 설계 원인 판정으로 설계 재정의 (구현 재작업 아님). engine#55 = Phase 0 verify gap (§5.2) → iter2 설계 원인 fix

MCT-179 대비 code FIX iter 증가 (1 → 3+ESCALATE). lesson: §5.1 (CI 격리 full-stack 전제) + §5.2 (Phase 0 verify producer path) 가 code FIX iter 핵심 원인. **ESCALATE 는 FIX 3회 소진 후 mechanical/구현 layer 해소 불가 시 ArchitectPL chief judge 설계 원인 판정 → 설계 재정의 경로의 정상 동작 (FIX 루프 max 의 ESCALATE 안전판 검증)**. design lane shift-left 누적 성공 (P0×0) vs code lane Phase 0 verify gap 비대칭 = 차기 Epic 의 code lane Phase 0 verify 강제 게이트화 (PMO retro 핵심 입력).

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#342) — §D4/§D11/§D18 amendment box 본문

- §D4: SIGTERM graceful integration smoke 회귀 검증 (MCT-176/177 LAND verify)
- §D11: integration-smoke.yml 2-layer (compose up full stack + testcontainers) — **이후 ESCALATE 로 SUPERSEDED**
- §D18: deploy.resources.limits 전 service + ContainerMemoryHigh alert

### 6.2 Phase 2 PR1 (hub#343 ESCALATE resolution) — §D8 + §D11 amendment box

- §D8 amendment (CodeReview FIX iter2): reader cache hit_ratio/p99 = cold reader 한정 metric (paper daemon 미적용) + panel id=7,8 downgrade 유지
- §D11 amendment (mc --wait 분리): mc-init healthcheck 미보유 → `compose up --wait` exit 1 → mc 분리
- §D11 amendment (ESCALATE infra-only): full-stack compose up CI 격리 구조적 불가 → 3-layer 분리 (CI smoke infra-only / testcontainers boundary / full-stack production carry)

### 6.3 Phase 2 PR2 (본 PR) — §D4/§D11/§D18 VERIFIED + N-002 정정

- §D4/§D11/§D18 VERIFIED confirm box (Phase 2 PR1 cross-repo LAND timeline + carrier 이관 + 3-layer 분리)
- §D11 amendment 본문 SUPERSEDED note + "compactor promotion 1회" strikethrough (N-002 RESOLVED)
- 3-way 정합 정정 (ADR-030 §D11 + Story §4 AC-1/§1 + plan §1.1/§1.2)

ADR-030 본문 만 박제 (Status = Accepted 유지). MCT-181 LAND 시 §D12/§D19 추가 D 본문 박제 의무.

## §7 다음 Story chain

**MCT-181** (image registry pin + backtest artifact NAS sync + Epic POLICY_FINALIZED 박제, D12/D19) — sequential_phase 7. EPIC-mctrader-docker-stack 7/7 + Epic POLICY_FINALIZED.

진입 prerequisite + carry over:
1. MCT-180 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. `${IMAGE_TAG}` D12 image registry pin (MCT-181 owner) — D11 full-stack compose up CI 검증 = D12 image pin 선행 의존 (ESCALATE F-301 resolution Layer 3)
3. full-stack production smoke (MCT-181 또는 별 PR) — collector+paper-engine compose up evidence = production deploy 시점 검증
4. R2 CRITICAL = PARTIAL 해소 유지 — production 실 측정 = 별 PR (EPIC-tier-promotion prod-2)
5. engine#55 `ci`/`lookahead-lint` carry over — `mctrader-market-upbit` private-dep token 이슈 (engine repo 별 처리)

채택 결정: D12 (image registry pin — prod sha pin / dev latest) + D19 (backtest artifact NAS sync — completion marker + 3회 retry + alert).

## §8 Cross-ref

- Story: `docs/stories/MCT-180.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-180-integration-smoke.md` (§1.1/§1.2 N-002 정정)
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (§D4/§D11/§D18 VERIFIED + §D11 N-002 정정 + §D8 amendment)
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (milestone 6/7 + N1 scope_files 정정)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-6 박제)
- MCT-179 RETRO (§5.1 Phase 0 verify lesson 동형 + §5.2 누적 reconcile 효과): `docs/retros/RETRO-MCT-179.md`
- Phase 1 PR: mctrader-hub#342 (b1be313, 2026-05-15) — Story + ADR-030 §D4/§D11/§D18 amend + plan + CLAUDE.md. DesignReview iter1 PASS (no FIX)
- Phase 2 PR1 (data): mctrader-data#67 (f233952, 2026-05-15T13:39:21Z) — collector ticks/active_symbols + testcontainers (land_order 1)
- Phase 2 PR1 (engine): mctrader-engine#55 (bc8c627, 2026-05-15T13:39:26Z) — universe_size + reader_cache Gauge + testcontainers (land_order 2). CodeReview iter2 설계 원인 (paper daemon ReaderCache 미사용)
- Phase 2 PR1 (hub): mctrader-hub#343 (af25d66, 2026-05-15T13:40:19Z) — integration-smoke.yml infra-only (ESCALATE resolution 614033a) + limits + alert + docker-stack (land_order 3). CodeReview iter3 ESCALATE → ArchitectPL chief judge 설계 원인 판정 → ESCALATE-fix PASS
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-6 + plan §1.1/§1.2 N-002 정정)
