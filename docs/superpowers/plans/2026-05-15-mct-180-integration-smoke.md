---
story_key: MCT-180
plan_title: "integration smoke (compose CI) + testcontainers + resource limits + MCT-180 TODO metric emit"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 6
depends_on: MCT-179 (LAND 2026-05-15, hub#339+#340+#341 + data#66)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D4, D11, D18]
carry_over_from_mct179:
  - "Grafana 5 [MCT-180 TODO] panel metric emit 신규 (collector ticks/active_symbols + engine universe_size + reader_cache hit_ratio/p99)"
  - "${IMAGE_TAG} prod pin (D12 — MCT-181 owner)"
  - "R2 CRITICAL production 측정 별 PR (EPIC-tier-promotion prod-2, carry)"
---

# MCT-180 Implementation Plan — integration smoke + testcontainers + resource limits

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** D11 (compose CI smoke + testcontainers 2-layer gate) + D18 (resource limits + container_memory alert) + D4 (SIGTERM graceful 회귀 검증) + MCT-179 carry over (5 [MCT-180 TODO] panel metric emit 신규).

**Architecture:**
- **D11 integration smoke** (ESCALATE F-301 amended, 2026-05-15): `.github/workflows/integration-smoke.yml` 신규 — **CI smoke = infra-only** (postgres+redis+minio compose up `--wait` + mc-init oneshot exit 0 만). collector/paper-engine compose up = CI 격리 구조적 불가 (sibling repo image 미배포 + build.context path 부재) → **제거**. testcontainers (Python) = repo-level boundary test (collector→NAS + paper-engine→Redis) = D11 boundary 실 검증 carrier. **full-stack compose up 검증 = production deploy carry** (D12 MCT-181 image registry pin 의존, EPIC-tier-promotion prod-2 류). 3-layer 분리: CI smoke (infra 정합) + testcontainers (component boundary) + production deploy (full-stack evidence carry). ADR-030 §D11 amendment (integration-smoke CI = infra-only) SSOT.
- **D18 resource limits**: compose.yml 각 service `deploy.resources.limits` (mem_limit + cpus) 명시. collector 50MB→512MB (INV-4 DualWriter + buffer) / paper-engine 512MB (reader cache 256MB + buffer) / backtest-runner 1G / postgres 1G / redis 256MB (hard cap 기존) / prometheus+grafana 512MB. Prometheus `container_memory_usage_bytes` alert (>80% capacity warn) — cadvisor (compose.yml 기존 MCT-123).
- **D4 SIGTERM 회귀** (ESCALATE F-301 amended, 2026-05-15): integration smoke infra-only 재설계로 collector/paper-engine compose up 제거 → SIGTERM step 동반 제거 (collector/paper-engine 부재 시 무의미). **D4 회귀 검증 carrier 이관**: testcontainers (data#67 + engine#55) + 각 repo unit test (MCT-176 `_SHUTDOWN_REQUESTED` + MCT-177 `shutdown.py` asyncio SSOT — 코드 변경 0, 회귀 검증 유지). production full-stack SIGTERM = production deploy carry.
- **MCT-179 carry over metric emit**: 5 [MCT-180 TODO] panel 중 **3 panel 해제** (id=3 collector ticks_total + id=4 active_symbols (data#67) / id=6 engine universe_size (engine#55 paper daemon emit)). **2 panel (id=7 reader_cache hit_ratio + id=8 p99) = downgrade 유지** — CodeReview FIX iter2 설계 원인 판정: paper daemon 은 ReaderCache 미인스턴스화 (MCT-170 cold read 전용 scope), cold reader/backtest 경로만 emit → 지속 panel 부적합. engine#55 stats() Gauge wiring 은 보존 (cold reader 경로 유효).

**Tech Stack:** GitHub Actions (compose integration smoke) / testcontainers-python / Docker Compose deploy.resources / cadvisor (MCT-123 LAND) / Prometheus / Python 3.12

**PR Split:**
- **Phase 1 PR** (hub, docs): Story + ADR-030 §D4/§D11/§D18 amendment + CLAUDE.md
- **Phase 2 PR1** (cross-repo: hub + data + engine):
  - **hub PR**: .github/workflows/integration-smoke.yml + compose.yml deploy.resources.limits + prometheus-alerts.yml container_memory + docker-stack.json 5 TODO panel 해제
  - **data PR**: collector mctrader_collector_ticks_total + mctrader_collector_active_symbols Prometheus metric emit + testcontainers boundary test
  - **engine PR**: mctrader_engine_universe_size + reader_cache hit_ratio/p99 Prometheus metric emit + testcontainers boundary test
- **Phase 2 PR2** (hub, 박제): Story §11 retro + Epic milestone 6/7 + RETRO + EPIC-RESULTS §Story-6

---

## §1 Phase 1 PR (hub, docs only)

### 1.1 Story MCT-180.md

**Files:** Create `docs/stories/MCT-180.md`

- [ ] §1-§6: 동기 / Epic context / Risk acceptance / AC 5 / INV / Risk
  - AC-1 (D11): `.github/workflows/integration-smoke.yml` PR push 시 compose up full stack → collector ingest → compactor promotion → paper-engine health 200 (10분 budget) PASS
  - AC-2 (D11): testcontainers boundary test (data collector→NAS mock + engine paper→Redis) PASS
  - AC-3 (D18): compose.yml deploy.resources.limits 전 service 명시 + cadvisor container_memory >80% alert rule
  - AC-4 (D4): integration smoke SIGTERM graceful (collector + paper-engine stop → exit 0 within stop_grace) 회귀 0
  - AC-5 (carry over): 5 [MCT-180 TODO] panel metric emit 신규 (collector ticks/active_symbols + engine universe_size + reader_cache hit_ratio/p99) → docker-stack.json TODO 해제

- [ ] §6.5 Change Plan §7/§11 N/A 박제
  - §7 security: integration smoke = CI 격리 환경 (실 NAS 미접근, mock/hub MinIO). 신규 trust boundary 없음.
  - §7.4 op-risk: resource limits OOM kill 위험 — limits 산정 보수적 (INV-4 + buffer). cadvisor alert >80% 선제 경보.
  - §11 data-migration: schema 변경 없음. Prometheus metric 신규 emit (additive).
  - §11.6 idempotency: integration smoke = ephemeral compose up/down (idempotent). metric emit = read-only observe.

- [ ] §7-§12: Dependencies (MCT-176~179 LAND + cadvisor MCT-123) / Test contract / Plan ref / FIX Ledger 빈 표 / Retro placeholder

### 1.2 ADR-030 amendment

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] §D4 amendment box (MCT-180): SIGTERM graceful integration smoke 회귀 검증 (MCT-176/177 LAND verify)
- [ ] §D11 amendment box (MCT-180): integration-smoke.yml (compose up full stack + collector ingest + compactor promotion + paper health, 10분 budget) + testcontainers 2-layer
- [ ] §D18 amendment box (MCT-180): deploy.resources.limits 전 service (collector 512M / paper-engine 512M / backtest 1G / postgres 1G / redis 256M / prom+grafana 512M) + cadvisor container_memory >80% alert
- [ ] §References Plan(MCT-180)

### 1.3 CLAUDE.md + scope_manifest + counters
- [ ] 7 Story chain MCT-180 IN_PROGRESS + §MCT-180 IN_PROGRESS 섹션
- [ ] scope_manifest MCT-180 IN_PROGRESS + started_date
- [ ] counters.json MCT-179 COMPLETED + MCT-180 IN_PROGRESS

### 1.4 plan git add (MCT-176 P0 lesson)

### 1.5 Phase 1 Gate
- [ ] DesignReviewPL + iter PASS + admin merge

---

## §2 Phase 2 PR1 (cross-repo: hub + data + engine, code)

### 2.1 mctrader-data PR
**Files:**
- Modify: collector — `mctrader_collector_ticks_total` Counter + `mctrader_collector_active_symbols` Gauge Prometheus emit (nas_metrics/prometheus_exporters.py MCT-171 패턴)
- Create: `tests/integration/test_collector_nas_boundary.py` (testcontainers — collector → MinIO mock boundary)

- [ ] Phase 0 verify: collector tick ingest 경로 + prometheus_exporters.py 실 구조 read 후 metric emit 위치 결정
- [ ] ticks_total = ingest 1 tick 당 inc / active_symbols = 현재 universe 활성 symbol Gauge
- [ ] testcontainers test: collector + MinIO testcontainer → put_streaming verify

### 2.2 mctrader-engine PR
**Files:**
- Modify: `mctrader_engine_universe_size` Gauge (metrics.py MCT-170 패턴) + reader_cache `nas_reader_cache_hit_ratio` Gauge + `nas_reader_p99_ms` Gauge (reader_cache.py MCT-170 hit_ratio() 메서드 → Prometheus Gauge expose)
- Create: `tests/test_paper_redis_boundary.py` (testcontainers — paper-engine → Redis testcontainer boundary)

- [ ] Phase 0 verify: metrics.py + io/reader_cache.py 실 구조 read (hit_ratio() 메서드 존재 MCT-170 LAND)
- [ ] universe_size = paper daemon 활성 universe sym count Gauge
- [ ] reader_cache hit_ratio Gauge (기존 hit_ratio() 메서드 → Prometheus expose) + p99 Histogram → p99 Gauge
- [ ] testcontainers test: paper-engine + Redis testcontainer → engine: prefix key verify

> **AMEND (CodeReview FIX iter2, 2026-05-15 — 설계 원인, Phase 0 verify lesson 5회째)**:
> `nas_reader_cache_hit_ratio` / `nas_reader_p99_ms` = **cold reader 사용 컴포넌트
> 한정** metric (backtest-runner / `ColdReader.run_smoke_test()` cutover 경로).
> **paper-engine daemon 미적용** — paper daemon = `PaperRunner` WS tick 경로,
> `ReaderCache`/`ColdReader`/`TierReader` 미인스턴스화 (Phase 0 verify 실증, runtime/
> grep 0 match). `ReaderCache.stats()` production caller = `ColdReader.run_smoke_test()`
> 1곳 (production caller 0 = cutover/backtest 경로 only). MCT-170 reader_cache =
> NAS cold read 전용 scope. → paper daemon 기동 시 영구 0.0.
> **engine#55 `stats()` Gauge producer wiring = 보존** (cold reader/backtest 경로 유효,
> docstring scope 명시만 추가, logic 변경 0). docker-stack.json panel id=7,8 =
> `[MCT-180 TODO]` downgrade **유지** (해제 취소). panel id=6 (universe_size) =
> `set_universe_size` cli.py daemon startup emit 배선 정합 → 정상 해제 유지.
> ADR-030 §D8 amendment (MCT-180 CodeReview FIX iter2) 박제 정합.

### 2.3 mctrader-hub PR
**Files:**
- Create: `.github/workflows/integration-smoke.yml`
- Modify: `compose.yml` (deploy.resources.limits 전 service)
- Modify: `monitoring/prometheus-alerts.yml` (ContainerMemoryHigh >80% alert)
- Modify: `monitoring/grafana/provisioning/dashboards/docker-stack.json` (5 [MCT-180 TODO] panel 해제 — data#PR + engine#PR metric emit 의존)

> **AMEND (CodeReview ESCALATE hub#343, iter 3/3 max — F-301 P0 설계 원인, ArchitectPL chief judge 최종 판정 2026-05-15)**:
> integration-smoke.yml 의 `compose up collector + paper-engine` step = CI 격리 환경
> **구조적 실행 불가** (sibling repo image `ghcr.io/mclayer/mctrader-{data,engine}:latest`
> 미배포 pull denied + `build.context: ../mctrader-{data,engine}` path 부재 → exit 1).
> iter1/2 mc --wait 분리는 표면 증상만 해소. **근본 = D11 설계가 CI 와 양립 불가능한
> full-stack 전제**. resolution (option b) = **CI smoke = infra-only + mc oneshot 만**,
> collector/paper-engine boundary = testcontainers 2-layer (data#67 + engine#55 LAND),
> full-stack compose up = production deploy carry (D12 MCT-181 image registry pin 의존).
> ADR-030 §D11 amendment (integration-smoke CI = infra-only) 박제 정합.

- [ ] integration-smoke.yml (ESCALATE resolution — infra-only):

```yaml
name: integration-smoke
on:
  pull_request:
    paths: ["compose.yml", ".github/workflows/integration-smoke.yml"]
  workflow_dispatch:
jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 8
    steps:
      - uses: actions/checkout@v4
      # ESCALATE resolution (F-301 P0 설계 원인, iter 3/3 max):
      # collector/paper-engine compose up = CI 격리 구조적 불가 (sibling repo
      # image 미배포 + build.context path 부재). → CI smoke = infra(postgres/
      # redis/minio) --wait + mc-init oneshot exit 0 만. collector/paper-engine
      # boundary = testcontainers 2-layer (data#67 + engine#55 LAND).
      # full-stack compose up = production deploy carry (D12 MCT-181 image pin).
      - name: compose up infra (postgres + redis + minio)
        run: |
          cp .env.example .env.dev
          docker compose --profile dev --env-file .env.dev up -d postgres redis minio --wait --wait-timeout 180
      - name: mc-init bucket bootstrap (oneshot, exit 0 verify)
        run: docker compose --profile dev --env-file .env.dev up --no-deps --exit-code-from mc mc
      - name: teardown
        if: always()
        run: docker compose --profile dev down -v
```

- [ ] compose.yml deploy.resources.limits:

```yaml
# 각 service block 에 추가
    deploy:
      resources:
        limits:
          memory: 512M   # collector/paper-engine (INV-4 50MB + reader cache 256MB + buffer)
          cpus: "1.0"
# backtest-runner: memory 1G / postgres: 1G / redis: 256M (기존 maxmemory hard cap) / prometheus+grafana: 512M
```

- [ ] prometheus-alerts.yml ContainerMemoryHigh:

```yaml
      - alert: ContainerMemoryHigh
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
        for: 5m
        labels: { severity: warning }
        annotations: { summary: "Container memory > 80% limit (D18 OOM 선제 경보)" }
```

- [ ] docker-stack.json TODO panel 해제 — **id=3,4,6 만 해제** (collector ticks/symbols data#67 LAND + engine universe_size engine#55 paper daemon emit 정합). **id=7,8 (reader_cache hit_ratio/p99) = `[MCT-180 TODO]` downgrade 유지** (CodeReview FIX iter2, 설계 원인 — reader cache = cold reader 전용 scope, paper daemon 미인스턴스화. cold read 경로만 emit, backtest-runner oneshot 지속 panel 부적합. ADR-030 §D8 amendment 정합)

### 2.4 cross-repo LAND 순서

> **AMEND (ESCALATE F-302, ArchitectPL chief judge 2026-05-15)**: data#67 + engine#55
> 선행 LAND → hub#343 재검증 (testcontainers 2-layer 가 D11 boundary 실 carrier 이므로
> data/engine LAND 가 hub#343 ESCALATE resolution 의 prerequisite). engine#55 `ci`/
> `lookahead-lint` 별개 FAILURE (`mctrader-market-upbit` private-dep git auth —
> `Invalid username or token`) = F-301/F-302 외 영역 (engine repo 자체 CI infra
> private-dep token 이슈). CodeReview iter3 PASS = lane scope 정합. engine#55 LAND
> 전 engine repo 측 private-dep token 이슈 별도 해소 필요 (본 ESCALATE 범위 외 carry).

1. **data#67 LAND** (전 check SUCCESS, LAND ready — testcontainers collector→NAS boundary source)
2. **engine#55 LAND** (CodeReview iter3 PASS; CI `ci`/`lookahead-lint` private-dep token
   별도 해소 후 — testcontainers paper→Redis boundary source)
3. **hub#343 LAND** (integration-smoke infra-only + limits + docker-stack TODO 해제 —
   data#67/engine#55 testcontainers LAND 의존, F-301 resolution 정합)

### 2.5 Gate
- AC-1~5 verify + CodeReviewPL 3-way + admin merge

---

## §3 Phase 2 PR2 (hub, 박제)

- Story §10 FIX Ledger + §11 retro + §12 측정 (integration smoke 결과 + resource limits 산정) + status COMPLETED
- ADR-030 §D4/§D11/§D18 amendment LAND confirm
- scope_manifest milestone 5/7 → 6/7
- CLAUDE.md MCT-180 COMPLETED
- RETRO-MCT-180.md (PMOAgent)
- EPIC-RESULTS §Story-6 + carry over (${IMAGE_TAG} MCT-181 + R2 production 별 PR)

---

## §4 다음 Story

MCT-180 COMPLETED → **MCT-181** (image registry pin + backtest artifact NAS sync + Epic CLOSE 박제, D12/D19). EPIC-mctrader-docker-stack 7/7 + Epic POLICY_FINALIZED.

---

## §5 Self-Review
- D11 integration smoke (ESCALATE F-301 amended): §2.3 infra-only workflow (collector/paper-engine compose up 제거) + §2.1/§2.2 testcontainers 2-layer = boundary 실 carrier + full-stack = production deploy carry (D12 MCT-181) ✓
- D18 resource limits + cadvisor alert: §2.3 deploy.resources + prometheus-alerts ✓
- D4 SIGTERM 회귀 (ESCALATE F-301 amended): testcontainers + MCT-176/177 unit test 회귀 (compose smoke SIGTERM step 제거 — infra-only) ✓
- carry over 5 TODO panel metric emit: §2.1 (collector) + §2.2 (engine) + §2.3 (docker-stack 해제, id=7/8 downgrade 유지) ✓
- §6.5 N/A 박제: §1.1 ✓
- ESCALATE resolution 3-way 정합: ADR-030 §D11 amendment (infra-only) + plan §2.3/§2.4 amend + Story §4 AC-1 재정의 (Phase 2 PR2 carry) ✓
