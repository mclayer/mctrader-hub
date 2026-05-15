---
story_key: MCT-179
plan_title: "observability (Prometheus + Grafana + alert) + WAL 30G production measurement + DR mode integration"
spec: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
epic: EPIC-mctrader-docker-stack
sequential_phase: 5
depends_on: MCT-178 (LAND 2026-05-15, hub#336+#337+#338 + signal-collector#1)
phase_pair: phase1_phase2
pr_split: 3
created_at: 2026-05-15
status: planning
decisions_implemented: [D5, D8, D17]
risk_owner:
  - "R2 CRITICAL — WAL 30G production measurement (peak market open 09:00 KST burst). EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 cross-Epic carry over"
carry_over_from_mct178:
  - "${IMAGE_TAG} prod pin (D12 — MCT-181 owner)"
  - "signal-collector LAND+7d legacy cleanup 별 PR (REDIS_MIGRATION_DUAL_WRITE=false cutover)"
---

# MCT-179 Implementation Plan — observability + WAL 30G measurement

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** D5 (Prometheus WAL bytes metric + measurement script + amendment trigger) + D8 (앱 /metrics scrape + Grafana dashboard + alert rule) + D17 (SIGTERM graceful + startup InvariantHarness scan) 통합. **R2 CRITICAL — WAL 30G production measurement** owner: synthetic baseline 측정 (MCT-172 paper mode 패턴) + production 측정 infra 구축 (실 production = 별 PR carry over).

**Architecture:**
- **D5 WAL 30G measurement**: mctrader-data `capacity_probe.py` (MCT-171 LAND) 의 WAL bytes Gauge 를 Prometheus scrape target 노출. `scripts/measure_wal_baseline.py` 신규 — paper mode synthetic 30min baseline + peak 30min burst hybrid (MCT-172 D8-2 패턴). 30G 초과 시 ADR-029 D11 hard_limit amendment 자동 발의 trigger (GitHub issue).
- **D8 observability**: collector + paper-engine /metrics (8080 이미 healthcheck, /metrics 별 endpoint) → Prometheus scrape config 추가. Grafana dashboard 신규 (WAL bytes / collector throughput / paper position / NAS hit ratio / reader cache p99). Prometheus alert rule (WAL >25G warn, >30G amend trigger, NAS 5xx, p99 >100ms).
- **D17 graceful + startup scan**: collector + paper-engine 시작 시 InvariantHarness 8종 scan (MCT-171 `invariant_harness.py` LAND). ambiguity invariant (D10) container restart race false positive 방지. SIGTERM graceful 는 MCT-176 (collector) + MCT-177 (paper-engine asyncio shutdown.py) LAND — MCT-179 = startup scan 통합 + alert.

**Tech Stack:** Prometheus (scrape + alert rule) / Grafana (dashboard provisioning) / Python 3.12 (measure script) / mctrader-data capacity_probe + invariant_harness (MCT-171 LAND)

**PR Split:**
- **Phase 1 PR** (hub, docs): Story + ADR-030 §D5/§D8/§D17 amendment + ADR-029 D11 cross-ref + CLAUDE.md
- **Phase 2 PR1** (cross-repo: hub + data):
  - **hub PR**: monitoring/prometheus.yml scrape target + monitoring/grafana/dashboards/docker-stack.json + monitoring/prometheus-alerts.yml + compose.yml /metrics port
  - **data PR**: scripts/measure_wal_baseline.py + capacity_probe WAL bytes Prometheus Gauge expose + startup InvariantHarness scan hook
- **Phase 2 PR2** (hub, 박제): Story §11 retro + §12 WAL 측정 결과 + Epic milestone 5/7 + RETRO + EPIC-RESULTS §Story-5 + R2 carry over (production 측정 별 PR)

---

## §1 Phase 1 PR (hub, docs only)

### 1.1 Story MCT-179.md

**Files:** Create `docs/stories/MCT-179.md`

- [ ] §1-§6: 동기 / Epic context / Risk acceptance / AC 5 / INV / Risk
  - AC-1 (D5): `scripts/measure_wal_baseline.py --mode paper-synthetic` exit 0 + WAL bytes 측정 결과 JSON (baseline 30min + peak 30min)
  - AC-2 (D5): WAL >30G 시 GitHub issue 자동 발의 (ADR-029 D11 hard_limit amendment trigger) dry-run verify
  - AC-3 (D8): Prometheus scrape collector + paper-engine /metrics target + Grafana dashboard JSON provisioning (docker-stack.json) + alert rule (WAL >25G warn / >30G crit)
  - AC-4 (D17): collector + paper-engine startup InvariantHarness 8종 scan 통합 (ambiguity invariant container restart race 방지)
  - AC-5 (R2): synthetic baseline 측정 결과 박제 (15G~45G hypothesis ±50% range, MCT-172 D8-2 패턴) + production 측정 별 PR carry over 명시

- [ ] §6.5 Change Plan §7/§11 N/A 박제
  - §7 security: Prometheus/Grafana = 내부 observability (인증 = Grafana admin password 기존). 신규 trust boundary 없음.
  - §7.4 op-risk: WAL 30G alert = D11 hard_limit FAIL gate. measurement script 실패 시 Epic CLOSE 차단 (D8-7=A 정합).
  - §11 data-migration: schema 변경 없음. Prometheus metric 신규 추가만 (additive).
  - §11.6 idempotency: measure_wal_baseline.py = read-only 측정 (idempotent). startup scan = read-only InvariantHarness.

- [ ] §7-§12: Dependencies (MCT-171 capacity_probe + invariant_harness LAND + MCT-176 collector + MCT-177 paper-engine) / Test contract / Plan ref / FIX Ledger 빈 표 / Retro placeholder
- [ ] §7 cross-Epic carry over: EPIC-tier-promotion-single-source prod-2 (WAL 30G production measurement) = MCT-179 흡수

### 1.2 ADR-030 amendment

**Files:** Modify `docs/adr/ADR-030-docker-stack-governance.md`

- [ ] §D5 amendment box (MCT-179): measure_wal_baseline.py paper-synthetic + peak hybrid + 30G 초과 issue 자동 발의
- [ ] §D8 amendment box (MCT-179): Prometheus scrape (collector/paper-engine /metrics) + Grafana docker-stack.json + alert rule (WAL 25G/30G + NAS 5xx + p99)
- [ ] §D17 amendment box (MCT-179): startup InvariantHarness 8종 scan (MCT-171 LAND import) + ambiguity invariant container restart race 방지
- [ ] ADR-029 D11 cross-ref: WAL 30G hard_limit = MCT-179 measurement gate (EPIC-tier-promotion prod-2 carry over)
- [ ] §References Plan(MCT-179)

### 1.3 CLAUDE.md + scope_manifest + counters
- [ ] 7 Story chain MCT-179 IN_PROGRESS + §MCT-179 IN_PROGRESS 섹션 (R2 CRITICAL owner 명시)
- [ ] scope_manifest MCT-179 IN_PROGRESS + started_date
- [ ] counters.json MCT-178 COMPLETED + MCT-179 IN_PROGRESS

### 1.4 plan git add (MCT-176 P0 lesson)

### 1.5 Phase 1 Gate
- [ ] DesignReviewPL + iter PASS + admin merge

---

## §2 Phase 2 PR1 (cross-repo: hub + data, code)

### 2.1 mctrader-data PR

**Files:**
- Create: `scripts/measure_wal_baseline.py`
- Modify: `src/mctrader_data/capacity_probe.py` (WAL bytes Prometheus Gauge expose)
- Modify: `src/mctrader_data/cli.py` (collect startup InvariantHarness 8종 scan hook)
- Create: `tests/test_measure_wal_baseline.py`

- [ ] `scripts/measure_wal_baseline.py`:

```python
#!/usr/bin/env python3
"""MCT-179 D5 — WAL 30G production measurement (paper-synthetic + peak hybrid).

Mode:
  paper-synthetic : paper mode 30min baseline + 30min peak burst synthetic (MCT-172 D8-2)
  production      : 실 production peak market open 09:00 KST burst (별 PR carry over)

Exit: 0 = WAL <= 30G / 7 = WAL > 30G (D11 hard_limit amendment trigger) / 99 = probe fail
"""
from __future__ import annotations
import json, os, sys
from mctrader_data.capacity_probe import CapacityProbe, CapacityThresholds

WAL_HARD_LIMIT_GB = 30

def main() -> int:
    mode = os.environ.get("MEASURE_MODE", "paper-synthetic")
    probe = CapacityProbe(CapacityThresholds())
    baseline = probe.measure_wal_bytes()  # MCT-171 LAND
    peak_gb = baseline / (1024**3)
    result = {
        "mode": mode,
        "wal_peak_gb": round(peak_gb, 2),
        "hard_limit_gb": WAL_HARD_LIMIT_GB,
        "verdict": "PASS" if peak_gb <= WAL_HARD_LIMIT_GB else "EXCEED",
        "hypothesis_range": "15-45 GB (±50%, MCT-172 D8-2 synthetic)",
    }
    print(json.dumps(result, indent=2))
    if peak_gb > WAL_HARD_LIMIT_GB:
        print(f"[measure] EXCEED: WAL {peak_gb:.2f}G > {WAL_HARD_LIMIT_GB}G — ADR-029 D11 hard_limit amendment 의무", file=sys.stderr)
        return 7
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [x] WAL bytes Prometheus Gauge SSOT = **`mctrader_capacity_usage_bytes{layer="WAL_local"}`** (MCT-171 LAND `prometheus_exporters.py:98` + `capacity_probe.py:331` emit, 기존 Gauge 재사용 — **신규 Gauge 추가 불요**). FIX iter1 정정: `wal_capacity_bytes` 신규 Gauge 박제 폐기 (LAND registry 부재 가공 metric). data PR scope 변경 없음 (capacity_probe Gauge 추가 작업 불필요 — MCT-171 기존 emit 경로 그대로)
- [ ] cli.py collect startup hook: `InvariantHarness().scan_all()` (MCT-171 invariant_harness.py LAND import) — 8종 scan, ambiguity (D10) container restart race log warn
- [ ] 신규 test: measure_wal_baseline paper-synthetic exit 0 + EXCEED exit 7 (mock 45G)

### 2.2 mctrader-hub PR

**Files:**
- Modify: `monitoring/prometheus.yml` (collector + paper-engine /metrics scrape target)
- Create: `monitoring/prometheus-alerts.yml` (WAL 25G/30G + NAS DR OPEN + ambiguity alert rule)
- Create: `monitoring/grafana/provisioning/dashboards/docker-stack.json` (9 panel — WAL / collector / paper position / NAS)
- Modify: `compose.yml` (collector + paper-engine 의 9090 /metrics port + prometheus alerts volume mount)

- [ ] prometheus.yml scrape job: `mctrader-collector:9090` + `mctrader-paper-engine:9090` (or 8080/metrics)
- [x] prometheus-alerts.yml (FIX iter1 정정 — 가공 metric 폐기 + 실 LAND series 바인딩):

```yaml
groups:
  - name: mctrader-docker-stack
    rules:
      - alert: WALCapacityWarn
        expr: mctrader_capacity_usage_bytes{layer="WAL_local"} > 25 * 1024^3
        for: 5m
        labels: { severity: warning }
        annotations: { summary: "WAL capacity > 25G (D11 warn)" }
      - alert: WALCapacityCritical
        expr: mctrader_capacity_usage_bytes{layer="WAL_local"} > 30 * 1024^3
        for: 1m
        labels: { severity: critical }
        annotations: { summary: "WAL > 30G — ADR-029 D11 hard_limit amendment 의무 (Epic CLOSE FAIL gate)" }
      # 폐기: nas_reader_5xx_total / nas_reader_p99_ms (LAND registry 부재 가공 metric).
      # NAS 운영 gate = engine dr_mode.py LAND (MCT-170) 실존 series. DR OPEN 전이 = D8=C hybrid proxy.
      - alert: NASReaderDROpen
        expr: increase(nas_reader_dr_transitions_total{to_state="OPEN"}[5m]) > 0
        labels: { severity: warning }
        annotations: { summary: "NAS reader DR mode OPEN transition (D8=C hybrid threshold 충족)" }
      - alert: NASReaderAmbiguity
        expr: increase(nas_reader_ambiguity_total[5m]) > 0
        labels: { severity: warning }
        annotations: { summary: "NAS reader UNKNOWN_TIER ambiguity (D10 NAS+local XOR violation)" }
```

> **metric-name SSOT** (FIX iter1 verify): WAL = `mctrader_capacity_usage_bytes{layer="WAL_local"}`
> (MCT-171 LAND) / NAS DR = `nas_reader_dr_transitions_total` + `nas_reader_ambiguity_total`
> (MCT-170 engine `io/dr_mode.py` LAND). 폐기 3종 = LAND registry 부재.

- [x] grafana docker-stack.json: 9 panel — WAL bytes gauge+trend (id=1,2 MCT-171 SSOT) /
  collector ingest+symbols (id=3,4 **MCT-180 TODO**) / paper open positions (id=5 `sum(mctrader_engine_open_positions)`
  실존) + universe size (id=6 **MCT-180 TODO**) / NAS hit_ratio (id=7 **MCT-180 TODO**) +
  reader p99 (id=8 **MCT-180 TODO**). TODO panel = description + title prefix 박제 (no-data placeholder)
- [ ] compose.yml: prometheus service 의 `./monitoring/prometheus-alerts.yml:/etc/prometheus/alerts.yml:ro` + prometheus.yml rule_files 참조 + grafana dashboard provisioning volume

### 2.3 cross-repo LAND 순서
1. data PR LAND 먼저 (capacity_probe Gauge + measure script)
2. hub PR LAND (prometheus scrape + alert + grafana)

### 2.4 측정 실행 (AC-5)
- `MEASURE_MODE=paper-synthetic python scripts/measure_wal_baseline.py` 실행 → 결과 JSON 박제 (Story §12)
- production 측정 (peak 09:00 KST) = 별 PR carry over (실 production deploy 후, MCT-172 D8-6 패턴)

### 2.5 Gate
- AC-1~5 verify + CodeReviewPL + admin merge

---

## §3 Phase 2 PR2 (hub, 박제)

- Story §10 FIX Ledger + §11 retro + §12 WAL 측정 결과 (synthetic baseline JSON) + status COMPLETED
- ADR-030 §D5/§D8/§D17 amendment LAND confirm + ADR-029 D11 cross-ref
- scope_manifest milestone 4/7 → 5/7
- CLAUDE.md MCT-179 COMPLETED + R2 CRITICAL 상태 (synthetic 측정 완료, production 별 PR carry over)
- RETRO-MCT-179.md (PMOAgent)
- EPIC-RESULTS §Story-5 + R2 carry over (production 측정 별 PR, EPIC-tier-promotion prod-2 cross-Epic)

---

## §4 다음 Story

MCT-179 COMPLETED → **MCT-180** (integration smoke + testcontainers + resource limits, D4/D11/D18).

---

## §5 Self-Review
- D5 WAL measurement: §2.1 measure_wal_baseline.py ✓
- D8 observability: §2.2 prometheus + grafana + alert ✓
- D17 startup scan: §2.1 cli.py InvariantHarness hook ✓
- R2 CRITICAL: §2.4 synthetic 측정 + production 별 PR carry over ✓
- cross-Epic carry over (EPIC-tier-promotion prod-2): §1.1 §7 + §3 EPIC-RESULTS ✓
- §6.5 N/A 박제: §1.1 ✓
