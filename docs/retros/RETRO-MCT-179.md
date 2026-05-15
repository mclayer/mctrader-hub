---
type: story-retro
story_key: MCT-179
epic_key: EPIC-mctrader-docker-stack
status: COMPLETED
completed_at: "2026-05-15"
sp: 5
sequential_phase: 5
---

# RETRO — MCT-179 EPIC-mctrader-docker-stack Story-5 (observability + WAL 30G synthetic baseline + DR mode integration + alert rule)

> PMOAgent sub-dispatch (codeforge PMO retro 의무, memory feedback_pmo_retro_mandatory). env=1 재귀 spawn 제약상 ArchitectPL 직접 이행 (RETRO-MCT-178 패턴 정합 — cross-cutting PMOAgent = Orchestrator spawn 원칙, one-shot subagent 재귀 spawn 금지 ADR-039).

## Story 요약

**EPIC-mctrader-docker-stack 의 Story-5 (sequential_phase 5)** — MCT-178 LAND (backtest-runner oneshot + compose-validate CI lint) 위에 전체 stack observability (Prometheus scrape + Grafana 9 panel dashboard + alert rule 4종) 를 박제하고, **EPIC-tier-promotion-single-source R-CRITICAL 의무인 WAL 30G measurement (prod-2)** 를 흡수. 채택 3 D = D5 (WAL 측정 스크립트 + Prometheus Gauge + 30G 초과 amendment trigger) + D8 (앱 내장 /metrics + Grafana + alert) + D17 (startup InvariantHarness 8종 scan).

3 PR cross-repo sequential LAND (hub Phase 1 docs + data Phase 2 PR1 code + hub Phase 2 PR1 code + hub Phase 2 PR2 박제). **R2 CRITICAL = synthetic baseline 측정 완료 (PARTIAL 해소)**, production 실 측정 = 별 PR carry over (peak market open 09:00 KST 1h burst, EPIC-tier-promotion prod-2 cross-Epic). FIX 2 iter (design iter1 P0 + code hub#340 iter1 P1×2, 양측 설계 원인) — design lane P0×0 연속 단절 (MCT-178 CONDITIONAL_PASS 에 이어 2 Story 연속), code lane R2 deliverable 무력화 후 설계 원인 fix 로 기능 회복.

## 결과 요약

| 항목 | 결과 |
|------|------|
| Phase 1 PR (hub docs + ADR-030 §D5/§D8/§D17 amend + CLAUDE.md) | mctrader-hub#339 MERGED (fabba57, 2026-05-15) — DesignReview iter1 P0 (ADR-030 Out-of-scope D5/D8 stale) → 전수 reconcile c8e4b8e → iter2 PASS |
| Phase 2 PR1 (data code: measure_wal_baseline.py + capacity_probe Gauge + cli.py startup scan, land_order 1) | mctrader-data#66 MERGED (e4a2cc2, 2026-05-15T11:51:56Z) — +547 lines, CodeReview iter1 PASS |
| Phase 2 PR1 (hub code: prometheus.yml + prometheus-alerts.yml + docker-stack.json + compose.yml, land_order 2) | mctrader-hub#340 MERGED (64feb73, 2026-05-15T11:52:49Z) — CodeReview iter1 P1×2 metric desync → 설계 원인 fix 64647c7 → iter2 PASS |
| Phase 2 PR2 (hub 박제, 본 PR) | mctrader-hub#TBD |
| 총 AC | **5/5 PASS** (AC-1 measure script paper-synthetic exit 0 / AC-2 >30G exit 7 D11 trigger / AC-3 prometheus scrape + grafana + alert / AC-4 startup InvariantHarness scan / AC-5 synthetic baseline + production 별 PR carry over) |
| 총 INV | 4/4 박제 (forward-only read-only probe + startup scan warn+continue + Prometheus metric additive + WAL 30G hard_limit FAIL gate) |
| FIX 루프 | **2 iter** (design iter1 P0 ADR-030 stale → 전수 reconcile c8e4b8e → iter2 PASS + code hub#340 iter1 P1×2 metric desync → 설계 원인 fix 64647c7 → iter2 PASS. data#66 iter1 PASS) |
| ADR-030 amendment | §D5/§D8/§D17 VERIFIED 박제 (Phase 2 PR2) + metric-name SSOT 표 박제 |
| Epic milestone | **5/7** (MCT-175 + MCT-176 + MCT-177 + MCT-178 + MCT-179 COMPLETED) |
| R2 CRITICAL 상태 | **PARTIAL 해소** — synthetic baseline 측정 완료 (verdict=PASS). production 실 측정 = 별 PR carry over (EPIC-tier-promotion prod-2) |
| MCT-180 carry over | Grafana 5 panel metric emit 신규 (collector ticks/symbols + engine universe_size + reader_cache hit_ratio/p99) |
| MCT-181 carry over | `${IMAGE_TAG}` prod pin (D12, dev=latest 현행 유지) |

## §1 delivered (산출물 단위)

### 1.1 Phase 1 PR (hub docs only, mctrader-hub#339, fabba57)

- `docs/stories/MCT-179.md` — Story §1-§12 신규 (§6.5 §7/§11 N/A 4 entry 사전 박제 — §7 Security / §7.4 Op-risk / §11 Data-migration / §11.6 Idempotency)
- `docs/adr/ADR-030-docker-stack-governance.md` — §D5/§D8/§D17 amendment box 본문 박제 (Phase 1) + **Out-of-scope 표 D1-D19 전수 reconcile** (DesignReview FIX iter1, c8e4b8e)
- `CLAUDE.md` — Docker stack 섹션 MCT-179 IN_PROGRESS 추가 (sequential_phase 5 entry)
- `docs/superpowers/plans/2026-05-15-mct-179-observability-wal30g.md` — 신규 (224 lines, Phase 1 + Phase 2 PR1 + Phase 2 PR2 plan)

### 1.2 Phase 2 PR1 — data (mctrader-data#66, e4a2cc2, land_order 1)

- `scripts/measure_wal_baseline.py` 신규 (135 lines) — paper-synthetic/production mode, exit 0 (PASS) / 7 (EXCEED >30G, ADR-029 D11 hard_limit amendment trigger) / 99 (probe fail). JSON stdout (mode/wal_bytes/wal_peak_gb/hard_limit_gb/verdict/hypothesis_range). read-only probe (forward-only invariant 정합)
- `src/mctrader_data/capacity_probe.py` 확장 (31 lines) — `measure_wal_bytes()` + `emit_wal_capacity_gauge()` 편의 메서드 (MCT-171 LAND `emit_capacity_usage` 패턴 정합, `mctrader_capacity_usage_bytes{layer="WAL_local"}` Gauge expose — **deprecated `wal_capacity_bytes` Gauge 미도입**)
- `src/mctrader_data/cli.py` 확장 (71 lines) — collect 커맨드 startup InvariantHarness 8종 scan hook (NAS_MINIO_ENDPOINT 미설정 graceful skip + ambiguity D10 fail → log.warning 전용, raise 금지)
- `tests/test_measure_wal_baseline.py` 신규 (310 lines, 20 test) — TestPaperSyntheticPass / TestExceedExit7 / TestProbeFailExit99 / TestProductionMode / TestCapacityProbeWalBytes. 846 회귀 0
- 총 +547 lines, deletion 0

### 1.3 Phase 2 PR1 — hub (mctrader-hub#340, 64feb73, land_order 2)

- `monitoring/prometheus.yml` MODIFY — `rule_files` 추가 + `mctrader-collector:8080` scrape job 신규 + paper-engine target container_name fix (`mctrader-engine-paper:8080` 오기 → `mctrader-paper-engine:8080`)
- `monitoring/prometheus-alerts.yml` CREATE — alert 4종 (CodeReview FIX iter1 정정 후): WALCapacityWarn/Critical = `mctrader_capacity_usage_bytes{layer="WAL_local"}` (MCT-171 SSOT) + NASReaderDROpen = `nas_reader_dr_transitions_total{to_state="OPEN"}` + NASReaderAmbiguity = `nas_reader_ambiguity_total` (MCT-170 dr_mode.py 실 series)
- `monitoring/grafana/provisioning/dashboards/docker-stack.json` CREATE — 9 panel (id=1,2 MCT-171 WAL SSOT + id=5 `sum(mctrader_engine_open_positions)` MCT-170 실존 + id=3,4,6,7,8 `[MCT-180 TODO]` no-data placeholder)
- `compose.yml` MODIFY — prometheus service `./monitoring/prometheus-alerts.yml:/etc/prometheus/alerts.yml:ro` volume mount

### 1.4 Phase 2 PR2 (hub 박제, 본 PR)

- `docs/stories/MCT-179.md` — frontmatter (story_issues 4 PR + status COMPLETED + completed_at) + §10 FIX Ledger 3 row (design iter1 + code hub#340 iter1 + code data#66 iter1) + §10.5 Git Ops Log 5 row + §11 retro (4 lesson) + §12 WAL synthetic 측정 결과 JSON 박제 + **§12.1 P2 문구 정정** ("data#66 코드 변경 0" → "deprecated Gauge 미도입, MCT-171 SSOT emit, FIX 불요, +547 lines")
- `docs/adr/ADR-030-docker-stack-governance.md` — Amendment box (MCT-179 LAND confirm) §D5/§D8/§D17 VERIFIED + metric-name SSOT 표 박제 (실존/부재/MCT-180 downgrade 분류)
- `scope_manifests/EPIC-mctrader-docker-stack.yaml` — MCT-179 status COMPLETED + completed_date + prs[] + milestone 5/7 + epic_close_gate MCT-179 line
- `CLAUDE.md` — Docker stack 7 Story chain MCT-179 COMPLETED + §MCT-179 IN_PROGRESS → COMPLETED 전면 재작성 + R2 risk 현황 PARTIAL 해소
- `docs/retros/RETRO-MCT-179.md` 신규 — 본 파일 (PMOAgent sub-dispatch)
- `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` — §Story-5 박제 (milestone 5/7) + R2 carry over (production 측정 별 PR, EPIC-tier-promotion prod-2)

## §2 measurements (수치 + verify)

### 2.1 AC PASS (5/5)

| AC | 결과 | 근거 |
|----|------|------|
| AC-1 WAL 측정 스크립트 paper-synthetic exit 0 (D5) | ✓ PASS | `MEASURE_MODE=paper-synthetic python scripts/measure_wal_baseline.py` exit 0 + JSON `verdict: PASS`, `wal_peak_gb: 0.0` (read-only probe, 무 WAL 환경 = 0 측정, MCT-172 D8-2 패턴) |
| AC-2 WAL 30G 초과 exit 7 D11 trigger (D5) | ✓ PASS | `WAL_HARD_LIMIT_GB=0` mock (1 MiB WAL) → `verdict: EXCEED` + exit 7 + stderr "ADR-029 D11 hard_limit amendment 의무 (D8-7=A FAIL gate)" |
| AC-3 Prometheus + Grafana + alert rule (D8) | ✓ PASS | prometheus.yml scrape job (collector/paper-engine :8080) + prometheus-alerts.yml 4 rule (실 LAND series 바인딩) + docker-stack.json 9 panel provisioning |
| AC-4 startup InvariantHarness scan (D17) | ✓ PASS | cli.py collect startup InvariantHarness 8종 scan hook (graceful skip + ambiguity D10 → log.warning 전용) |
| AC-5 synthetic baseline + production 별 PR carry over (R2) | ✓ PASS | synthetic baseline verdict=PASS 박제 (§12) + production 실 측정 = 별 PR carry over (peak 09:00 KST 1h burst, EPIC-tier-promotion prod-2) |

### 2.2 INV 박제 (4/4)

| INV | 결과 |
|-----|------|
| forward-only (WAL 객체 삭제 금지) | ✓ 박제 — measure_wal_baseline.py = read-only probe (WAL 파일 수정 0, ADR-009 §D12 정합) |
| startup scan warn+continue | ✓ 박제 — InvariantHarness violation = log.warning 전용 + 프로세스 계속 (raise 금지, ADR-030 §D17) |
| Prometheus metric additive | ✓ 박제 — MCT-171 기존 Gauge 재사용 (`mctrader_capacity_usage_bytes`), 신규 가공 Gauge 미도입. 기존 metric 제거/rename 없음 |
| WAL 30G hard_limit FAIL gate | ✓ 박제 — exit 7 + D11 amendment 발의 의무 (D8-7=A, Epic CLOSE FAIL gate). AC-2 검증 |

### 2.3 Test + 회귀

| 항목 | 결과 |
|------|------|
| Phase 2 PR1 신규 test (data#66) | 20 test (test_measure_wal_baseline.py) ALL PASS |
| 회귀 (data full suite) | 846 passed + 20 skipped + 4 xfailed (회귀 0) |
| Phase 2 PR1 (hub#340) | docker compose config --quiet exit 0 + prometheus-alerts.yml YAML valid + docker-stack.json valid JSON (compose regression 0) |
| ruff + pyright (data) | PASS (수동 FIX 1회: N814 noqa + F401 제거) |

### 2.4 FIX 루프 (2 iter — design 1 + code 1)

| iter | lane | finding | resolution |
|------|------|---------|------------|
| 1 | design (Phase 1 hub docs) | **P0** — ADR-030 "Out of scope" 표 D5/D8 정의 swap stale (scope_manifest §design_decisions SSOT desync). MCT-178 F-001 (D11/D16) 동형 누적 — 매 Story 부분 reconcile 시 MCT-180/181 재발 예상 | **설계 원인** — ArchitectPL 전수 정정 (c8e4b8e): D1-D19 전체 row 를 scope_manifest SSOT 와 1:1 전수 정합 (D4/D5/D8 정의 + D6 누락 row + D10/D14/D15/D19 verbatim + 헤더 "10 D"→"11 D"). reconciliation note 박제. DesignReview iter2 PASS |
| 1 | code (hub#340) | **P1×2** — (F-1) alert expr `wal_capacity_bytes` 가공 metric → R2 CRITICAL deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화. (F-2) `nas_reader_5xx_total`/`nas_reader_p99_ms`/collector·universe metric LAND 부재 (Grafana no-data) | **설계 원인** — ArchitectPL 최종 판정: ADR-030 §D8 + Plan §2.2 가 Phase 0 verify 미수행 가공 metric 박제 (구현은 설계 충실 추종). fix (64647c7): WAL → `mctrader_capacity_usage_bytes{layer="WAL_local"}` (MCT-171 SSOT) + NAS → `nas_reader_dr_transitions_total`/`nas_reader_ambiguity_total` (MCT-170 실 series) + 미실존 panel `[MCT-180 TODO]` downgrade. **R2 deliverable 기능 회복**. CodeReview iter2 PASS |
| 1 | code (data#66) | **0 blocking (PASS)** — deprecated Gauge 미도입, MCT-171 LAND `emit_capacity_usage` 패턴 정합 metric-name SSOT 정합 (+547 lines) | PASS, LAND (e4a2cc2, land_order 1) |

design lane = MCT-175 (P0×1) → MCT-176 (P0×1) → MCT-177 (P0×0) → MCT-178 (CONDITIONAL_PASS) → **MCT-179 (P0×1)**. P0×0 연속 단절 2 Story 연속 — 원인 = ADR-030 누적 정책 drift (§5.2 참조, MCT-178 §5.2 동형).

## §3 risks_realized

### 3.1 R-MCT-179-1 WAL 측정값 production 괴리 (HIGH)

- **위협**: paper-synthetic 측정값 이 production 실 peak (50sym × 3ch × 12seg/h burst) 와 크게 다를 경우 → D11 amendment 발의 판단 오류
- **mitigation 적용**: synthetic = paper mode (MCT-172 D8-2 패턴) read-only probe + 초과 시 즉시 exit 7 + GitHub issue 자동 발의 → 사용자 판단
- **realized**: PARTIAL — synthetic 환경 = 무 WAL (wal_peak_gb=0.0), hypothesis 15-45 GB verify 는 production 실 측정 필요
- **carry over**: production 실 측정 = 별 PR (peak market open 09:00 KST 1h burst window, EPIC-tier-promotion-single-source prod-2). R2 CRITICAL = PARTIAL 해소 유지

### 3.2 R-MCT-179-2 Prometheus scrape fail (MEDIUM)

- **위협**: collector/paper-engine /metrics endpoint 미노출 또는 포트 불일치 → scrape miss → alert 미발화 (silent WAL 초과)
- **mitigation 적용**: Phase 0 verify 로 실 포트 확인 (`:9090` 가설 기각 → 실 `:8080/metrics`) + paper-engine container_name fix (`mctrader-engine-paper` 오기 → `mctrader-paper-engine`)
- **realized**: NO — Phase 0 verify 가 포트 가설 오류 + 기존 container_name 오기 선제 차단
- **carry over**: 실 scrape target state=up 확인 = MCT-180 testcontainers integration smoke

### 3.3 R-MCT-179-3 InvariantHarness startup scan overhead (LOW)

- **위협**: 8종 scan = I/O 증가 → container cold start 지연 (60s SIGTERM grace 압박)
- **mitigation 적용**: warn+continue (hard abort 아님, raise 금지) + NAS_MINIO_ENDPOINT 미설정 graceful skip
- **realized**: NO — graceful skip + log.warning 전용 으로 cold start 영향 최소
- **carry over**: startup time 회귀 검증 = MCT-180 testcontainers smoke

## §4 followups (post-Story carry over → MCT-180)

### 4.1 R2 CRITICAL production 실 측정 (별 PR, cross-Epic)

- **WAL 30G production measurement**: synthetic baseline 측정 완료 (R2 PARTIAL 해소). production 실 측정 = 별 PR (실 production deploy + peak market open 09:00 KST 1h burst window). 30G 초과 시 ADR-029 D11 hard_limit amendment 발의 (D8-7=A FAIL gate). **EPIC-tier-promotion-single-source Epic CLOSED prereq prod-2 = 본 별 PR 이 충족**

### 4.2 MCT-180 Grafana panel metric emit 신규 (carry over)

- `[MCT-180 TODO]` 5 panel 활성 의무: `mctrader_collector_ticks_total` + `mctrader_collector_active_symbols` (data collector.py emit 신규) + `mctrader_engine_universe_size` (engine metrics.py Gauge 신규) + `nas_reader_cache_hit_ratio` + `nas_reader_p99_ms` (engine reader_cache.py Gauge/Histogram expose 신규)

### 4.3 MCT-181 carry over (image registry pin)

- `${IMAGE_TAG}` prod pin (D12, MCT-181 owner) — 현 compose.yml dev=latest 현행 유지. prod = `sha-<7char>` pin = MCT-181

## §5 lessons (process learnings)

### 5.1 설계가 가공 metric 박제 — Phase 0 verify 독립 의무 4회 재현 (MCT-170/177/178 §5.1 동형)

CodeReview hub#340 iter1 P1×2 = ADR-030 §D8 + Plan §2.2 가 LAND registry 부재 가공 metric (`wal_capacity_bytes`/`nas_reader_5xx_total`/`nas_reader_p99_ms`/collector·universe metric) 을 박제. 구현 (hub#340) 은 설계 표기 충실 추종 → **R2 CRITICAL deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화** (미발화 alert = silent WAL 초과 risk). Phase 0 verify (engine `io/dr_mode.py` + `metrics.py` + data `prometheus_exporters.py` grep 실증) 미수행 으로 가공 metric 이 Phase 1 박제 진입.

→ ArchitectPL 최종 판정 = **설계 원인** (구현 충실, 설계 표기 desync). MCT-170 ("engine io/ 3 module MCT-154 LAND 존재 재인지") + MCT-177 ("data 동기 SIGTERM stub cross-repo 오적용 — engine asyncio SSOT 존재") + MCT-178 ("5 worker 개별 SET 가설 ≠ Publisher 단일 계층") lesson **4회 재현**.

**lesson**: cross-repo Story 에서 sibling repo 의 metric/API/계층 SSOT 는 Phase 0 verify grep 실증 의무. session prompt + plan pseudocode 의 metric-name 표현 ("wal_capacity_bytes Gauge") 은 가설로만 수용 (memory feedback_phase0_verify_mandatory 정합). **observability/alert 박제 시 alert expr 의 모든 metric selector 는 LAND registry grep 실증 의무 — 미발화 alert 는 R2 같은 CRITICAL deliverable 를 silent 무력화** (가공 metric 박제 = deliverable functional gap). DesignReview/CodeReview lane 의 metric-name LAND verify 가 Phase 1 박제 단계로 shift-left 필요 (TestContractArch deputy §8 perf baseline 타당성 검수 범위 확장 후보 — PMO retro 입력).

### 5.2 ADR-030 Out-of-scope 표 D1-D19 전수 reconcile — 누적 stale 근본 차단 (MCT-178 §5.2 누적 drift lesson 연속)

DesignReview iter1 P0 = ADR-030 "Out of scope" 표 D5/D8 정의 swap stale (scope_manifest §design_decisions SSOT desync). MCT-178 F-001 (D11/D16 swap, MCT-175 LAND 박제 stale 이 4 Story 만에 surface) 동형 누적. 매 Story 가 자기 D 만 부분 reconcile 하면 MCT-180 (D11/D18) / MCT-181 (D12/D19) 에서 재발 확정.

→ ArchitectPL 판정 = 부분 reconcile 반복 = lesson reapply 무력화. **D1-D19 전체 row 를 scope_manifest §design_decisions SSOT 와 1:1 전수 정합** (c8e4b8e) + reconciliation note (Out-of-scope 표 = navigational only, SSOT = scope_manifest) 박제. 누적 stale 근본 차단.

**lesson**: MCT-178 §5.2 "lesson reapply 누적 효과는 신규 finding 만 감소, 기존 박제 stale 은 별 trigger surface" 의 **근본 해결책 = 부분 reconcile (Story 단위 자기 D) 아닌 전수 reconcile (전체 row SSOT 1:1)**. Epic 중간 Story 의 누적 정책 문서 audit 은 자기 D 가 아닌 전 D 범위 + SSOT navigational-only 명시 (정의/owner 분쟁 시 단일 SSOT 우선 룰 박제). ArchitectPLAgent §3 deputy author input 통합 정합성 검수 범위 = 자기 Story D 가 아닌 전체 ADR↔scope_manifest cross-check 의무.

### 5.3 R2 CRITICAL cross-Epic carry over 흡수 — synthetic/production 측정 분리 박제 필수

MCT-179 = EPIC-tier-promotion-single-source prod-2 (WAL 30G production measurement) cross-Epic carry over 흡수. synthetic baseline (paper-synthetic read-only probe, AC-1/AC-5) = 본 Story 완결, production 실 측정 (peak 09:00 KST 1h burst) = 별 PR carry over 로 명확 분리 박제.

**lesson**: cross-Epic carry over (다른 Epic 의 CLOSED prereq) 흡수 시 **측정 가능 범위 (synthetic) vs production 의존 범위 (실 deploy 후) 를 AC 단계 분리 박제 의무**. R2 CRITICAL = "PARTIAL 해소" 명시 (완전 해소 아님) + production 별 PR carry over gate 박제. 측정 deliverable 을 단일 Story 에 강제 흡수하면 production deploy 미완 으로 Story FAIL gate 발생 — synthetic/production 분리가 cross-Epic carry over 의 정상 패턴. EPIC-tier-promotion prod-2 = 본 별 PR (production 실 측정) 이 충족.

### 5.4 FIX 루프 cost — 2 iter (design P0 전수 reconcile + code P1×2 설계 원인 fix)

MCT-178 = 1 iter (design CONDITIONAL_PASS fast-fix + code PASS 양 PR). MCT-179 = **2 iter** (design iter1 P0 전수 reconcile + code hub#340 iter1 P1×2 설계 원인 fix, data#66 PASS). 원인:
- design lane = §6.5 lesson reapply 정상 (신규 finding 0) + 누적 drift P0 (전수 reconcile = MCT-178 부분 reconcile 의 근본 해결, MCT-180/181 재발 사전 차단 투자)
- code lane = Phase 0 verify 미수행 가공 metric 박제 (§5.1) → P1×2 설계 원인. 단 ArchitectPL 최종 판정 (설계 원인) 으로 1 code iter 내 fix (구현 재작업 아님, 설계 표기 정정)

MCT-178 대비 FIX iter 1 증가. lesson: §5.1 (Phase 0 verify 가공 metric) 이 code FIX iter 핵심 원인. design 전수 reconcile (§5.2) 은 1 iter 비용 이나 MCT-180/181 재발 사전 차단 (누적 audit 투자 = 후속 Story FIX iter 절감). **Phase 0 verify shift-left (metric-name LAND grep 실증을 Phase 1 박제 전 의무화) 가 차기 Epic FIX iter 감소 핵심** (PMO retro 입력).

## §6 ADR-030 amendment 박제 timeline

### 6.1 Phase 1 (hub#339) — §D5/§D8/§D17 amendment box 본문 + Out-of-scope 전수 reconcile

- §D5: measure_wal_baseline.py + Prometheus Gauge SSOT (FIX iter1 정정 — `mctrader_capacity_usage_bytes{layer="WAL_local"}` MCT-171 LAND, `wal_capacity_bytes` 가공 폐기) + 30G 초과 amendment trigger + cross-Epic carry over
- §D8: Prometheus scrape + alert rule (FIX iter1 정정 — 실 LAND series 바인딩) + Grafana 9 panel (`[MCT-180 TODO]` placeholder)
- §D17: startup InvariantHarness scan (warn+continue) + SIGTERM MCT-176/177 LAND 재사용
- Out-of-scope 표 D1-D19 전수 reconcile (c8e4b8e, navigational only + SSOT = scope_manifest 명시)

### 6.2 Phase 2 PR2 (본 PR) — §D5/§D8/§D17 VERIFIED + metric-name SSOT 표

- §D5 VERIFIED: measure_wal_baseline.py LAND (AC-1/AC-5 PASS + AC-2 EXCEED exit 7) + Prometheus Gauge SSOT (data#66 deprecated Gauge 미도입, +547 lines) + R2 PARTIAL 해소 + production 별 PR carry over
- §D8 VERIFIED: Phase 0 verify 정정 (:8080 + container_name fix) + alert rule (MCT-171 SSOT + MCT-170 dr_mode 실 series) + Grafana 9 panel + compose.yml volume mount
- §D17 VERIFIED: collector cli.py startup scan + API 정정 (scan_all() 부재 → verify() per-partition) + SIGTERM MCT-176/177 재사용
- metric-name SSOT 표: 실존 4 metric + 부재 폐기 3 + MCT-180 downgrade 4 분류 박제

ADR-030 본문 만 박제 (Status = Accepted 유지). MCT-180 ~ MCT-181 LAND 시 추가 D 본문 박제 의무.

## §7 다음 Story chain

**MCT-180** (integration smoke + testcontainers + resource limits + alert rule) — sequential_phase 6.

진입 prerequisite:
1. MCT-179 Phase 2 PR2 MERGED ✓ (본 PR LAND 시점)
2. carry over: Grafana 5 panel metric emit 신규 (collector ticks/symbols + engine universe_size + reader_cache hit_ratio/p99 — `[MCT-180 TODO]` placeholder 활성)
3. carry over: `${IMAGE_TAG}` prod pin (D12, MCT-181 owner — dev=latest 현행 유지)
4. **R2 CRITICAL = PARTIAL 해소 유지** — production 실 측정 = 별 PR (peak 09:00 KST 1h burst, EPIC-tier-promotion-single-source prod-2)

채택 결정: D4 (SIGTERM graceful 회귀) + D11 (compose CI smoke + testcontainers 2 layer gate) + D18 (resource limits + container_memory_usage_bytes alert).

## §8 Cross-ref

- Story: `docs/stories/MCT-179.md`
- spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- plan: `docs/superpowers/plans/2026-05-15-mct-179-observability-wal30g.md`
- ADR-030: `docs/adr/ADR-030-docker-stack-governance.md` (§D5/§D8/§D17 VERIFIED + metric-name SSOT 표 + Out-of-scope 전수 reconcile)
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml` (milestone 5/7)
- EPIC-RESULTS: `docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md` (§Story-5 박제)
- MCT-178 RETRO (§5.2 누적 drift lesson 연속): `docs/retros/RETRO-MCT-178.md`
- MCT-177 RETRO (§5.1 Phase 0 verify lesson 동형): `docs/retros/RETRO-MCT-177.md`
- ADR-029 §D11 cross-ref: WAL 30G hard_limit SSOT (EPIC-tier-promotion-single-source prod-2)
- Phase 1 PR: mctrader-hub#339 (fabba57, 2026-05-15) — Story + ADR-030 §D5/§D8/§D17 amend + Out-of-scope 전수 reconcile (c8e4b8e) + CLAUDE.md
- Phase 2 PR1 (data): mctrader-data#66 (e4a2cc2, 2026-05-15T11:51:56Z) — measure_wal_baseline.py + capacity_probe Gauge + cli.py startup scan + 20 test (land_order 1)
- Phase 2 PR1 (hub): mctrader-hub#340 (64feb73, 2026-05-15T11:52:49Z) — prometheus.yml + prometheus-alerts.yml + docker-stack.json + compose.yml. 설계 원인 fix 64647c7 (land_order 2)
- Phase 2 PR2 (hub 박제): mctrader-hub#TBD — 본 PR (6 file: Story + ADR-030 + scope_manifest + CLAUDE.md + RETRO 신규 + EPIC-RESULTS §Story-5 + §12.1 P2 정정)
