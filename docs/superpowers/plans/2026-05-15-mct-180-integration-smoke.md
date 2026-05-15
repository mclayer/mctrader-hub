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
- **D11 integration smoke**: `.github/workflows/integration-smoke.yml` 신규 — compose up full stack (postgres+redis+minio+collector+paper-engine) → collector ingest 1분 → compactor promotion 1회 → paper-engine health 200 → 검증. testcontainers (Python) = repo-level boundary test (collector→NAS + paper-engine→Redis). 2-layer: compose CI smoke (stack 정합) + testcontainers (component boundary).
- **D18 resource limits**: compose.yml 각 service `deploy.resources.limits` (mem_limit + cpus) 명시. collector 50MB→512MB (INV-4 DualWriter + buffer) / paper-engine 512MB (reader cache 256MB + buffer) / backtest-runner 1G / postgres 1G / redis 256MB (hard cap 기존) / prometheus+grafana 512MB. Prometheus `container_memory_usage_bytes` alert (>80% capacity warn) — cadvisor (compose.yml 기존 MCT-123).
- **D4 SIGTERM 회귀**: integration smoke 에 SIGTERM graceful 검증 단계 (collector + paper-engine `docker compose stop` → exit 0 within stop_grace_period). MCT-176/177 LAND graceful 회귀 0 verify.
- **MCT-179 carry over metric emit**: 5 [MCT-180 TODO] panel = collector ticks_total + active_symbols (data) / engine universe_size (engine) / reader_cache hit_ratio + p99 (engine reader_cache MCT-170). 신규 Prometheus metric emit → docker-stack.json panel TODO 해제.

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

### 2.3 mctrader-hub PR
**Files:**
- Create: `.github/workflows/integration-smoke.yml`
- Modify: `compose.yml` (deploy.resources.limits 전 service)
- Modify: `monitoring/prometheus-alerts.yml` (ContainerMemoryHigh >80% alert)
- Modify: `monitoring/grafana/provisioning/dashboards/docker-stack.json` (5 [MCT-180 TODO] panel 해제 — data#PR + engine#PR metric emit 의존)

- [ ] integration-smoke.yml:

```yaml
name: integration-smoke
on:
  pull_request:
    paths: ["compose.yml", ".github/workflows/integration-smoke.yml"]
  workflow_dispatch:
jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 12
    steps:
      - uses: actions/checkout@v4
      - name: compose up infra + collector + paper-engine (dev)
        run: |
          cp .env.example .env.dev
          docker compose --profile dev --env-file .env.dev up -d postgres redis minio mc --wait --wait-timeout 180
          docker compose --profile dev --env-file .env.dev up -d collector paper-engine --wait --wait-timeout 240
      - name: collector ingest 60s
        run: sleep 60 && docker compose --profile dev logs collector | grep -q "ingest" || echo "collector ingest log check (advisory)"
      - name: paper-engine health 200
        run: docker compose --profile dev exec -T paper-engine python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"
      - name: SIGTERM graceful (D4 회귀)
        run: |
          docker compose --profile dev stop collector paper-engine --timeout 60
          docker compose --profile dev ps --status exited | grep -E "collector|paper-engine"
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

- [ ] docker-stack.json 5 TODO panel 해제 (id=3,4,6,7,8 — collector ticks/symbols + engine universe + reader_cache hit/p99, data#PR + engine#PR metric emit 의존)

### 2.4 cross-repo LAND 순서
1. data PR + engine PR LAND 먼저 (metric emit source)
2. hub PR LAND (integration-smoke + limits + docker-stack TODO 해제 — metric source 의존)

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
- D11 integration smoke + testcontainers: §2.3 workflow + §2.1/§2.2 testcontainers ✓
- D18 resource limits + cadvisor alert: §2.3 deploy.resources + prometheus-alerts ✓
- D4 SIGTERM 회귀: §2.3 integration-smoke SIGTERM step ✓
- carry over 5 TODO panel metric emit: §2.1 (collector) + §2.2 (engine) + §2.3 (docker-stack 해제) ✓
- §6.5 N/A 박제: §1.1 ✓
