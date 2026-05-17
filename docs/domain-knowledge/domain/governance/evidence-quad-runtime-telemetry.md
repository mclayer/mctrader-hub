---
type: domain-knowledge
domain: governance
title: Evidence Quad — Runtime Telemetry Counter
adr_cross_ref: "ADR-033 (enforcement) + ADR-032 §3.2 (quad rule)"
sibling: evidence-triad-verified-badge.md
created_at: "2026-05-17"
author: MCT-191
---

# Evidence Quad — Runtime Telemetry Counter (4th gate delta)

> **SSOT 분리**: triad v1 정의 = `evidence-triad-verified-badge.md` (sibling 페이지)
> 가 SSOT. 본 페이지 = **quad v2 4th gate delta 만** 박제 (R4 DRY mitigation).
> triad 3 evidence (file:line / caller-grep ≥1 / integration test) 는 sibling 페이지
> forward ref — 본 페이지 중복 정의 금지.
> **enforcement SSOT** = ADR-033 (어떻게 강제). **quad rule SSOT** = ADR-032 §3.2
> (무엇이 evidence).

## §1 Concept (3 — ResearcherAgent verified-via 외부 source)

triad v1 (static fitness function 3 evidence) 가 박제하지 못하는 gap = "정의 LAND +
caller-wired LAND 모두 충족하나 production traffic 0" (dead-in-prod false-negative).
4번째 게이트 = runtime telemetry counter. 근거 3 concept:

### (1) Hyrum's Law 역방향 — dead-in-prod detection

Hyrum's Law canonical = "with a sufficient number of users of an API, all observable
behaviors of your system will be depended on by somebody". 대우 (역방향) = telemetry
counter == 0 over N days → **production 의존자 부재 추정** → dead-in-prod detection.
caller-grep ≥1 (static)는 "코드 경로가 배선됨"만 증명, "실행됨"은 증명 X. counter
≥1 = 실행 박제.

source: https://lawsofsoftwareengineering.com/laws/hyrums-law/

### (2) Runtime fitness function — Building Evolutionary Architectures

triad = **static fitness function** (build-time test: file:line citation + caller grep
+ integration test PASS — 모두 CI/build 시점 측정). quad 4번째 게이트 = **runtime
fitness function** (production-time 측정: telemetry counter). Ford/Parsons/Kua
"Building Evolutionary Architectures" ch.2 — objective integrity assessment of
architectural characteristics 를 automated architectural governance test 로 격상.
static + runtime 2축 = architectural characteristic 의 완전 fitness coverage.

source: Ford/Parsons/Kua, "Building Evolutionary Architectures" ch.2

### (3) Counter monotonicity as wiring proof

Prometheus **Counter** (monotonic 누적, history preserve — restart 시 reset 되나
`increase()` semantic 이 자동 보정) ≠ **Gauge** (current-state, scrape miss 시
false-negative). counter ≥1 over N days = irrefutable monotonic evidence ("측정
window 내 최소 1회 production code path 실행이 박제됨"). Gauge 는 0 으로 돌아간
순간만 scrape 되면 false-negative, Counter 는 history preserve 라 불가.

source: https://prometheus.io/docs/concepts/metric_types/
내부 모델: `nas_reader_ambiguity_total` (ADR-029 §D10, MCT-170 LAND — Counter
14d rolling 0-hit telemetry watcher 선례)

## §2 decision-defined / caller-wired / runtime-observed 3-tier 분리 invariant

sibling 페이지 §3 의 `decision-defined vs caller-wired 2-tier` 를 3-tier 로 확장.
**runtime-observed** = dynamic (실행) tier — static 2-tier 가 박제 못하는 축.

| tier | evidence | nature | LAND 시점 |
|------|----------|--------|-----------|
| decision-defined | file:line citation | static (정의) | ADR/decision LAND |
| caller-wired | production caller git grep ≥1 | static (배선) | code wiring LAND |
| **runtime-observed** | telemetry counter ≥1 over N days | **dynamic (실행)** | production traffic 후 N days |

**실증 사례 — 3-tier 분리가 detection 강화한 사례**:

- **MCT-189 130GB 누적** = decision-defined LAND ✓ + caller-wired LAND ✗
  (`promote_l1()` production caller 0건). caller-wired tier 가 차단했어야 할 gap
  (sibling 페이지 §3 motivation). 130 GB legacy Parquet 영구 누적.
- **MCT-184 dead-in-data** = decision-defined LAND ✓ + caller-wired LAND ✓
  (caller grep ≥1) + **runtime-observed ✗** (production caller 0, consumer =
  MCT-185 cutover). caller-wired tier 통과 후에도 production traffic 0 →
  **quad 4번째 게이트가 detection 을 한 단계 더 강화하는 직접 사례**.

## §3 traffic class 차등 N days (ADR-033 §4 cross-ref)

"N days" 는 단일 값 아님 — ADR class + 경로 hot/cold 별 차등. ADR-033 §4 SSOT,
본 페이지 = 운영 모델 요약:

| traffic class | N days window | 근거 |
|---------------|---------------|------|
| production-wired ADR | 14d calendar | 일반 production code path |
| governance ADR | **N/A (telemetry_counter_caveat)** | code wiring 0 → counter forever 0 정상 (false-positive 차단) |
| trading-hot (collector tick) | market-open hours rolling | KRX 09:00–15:30 KST, weekend/공휴일 제외 |
| trading-cold (engine cold reader) | 14d calendar | low-frequency cold path |

trading-hot = market-open rolling 인 이유: market-closed window 측정 시 정상
미동작이 false-negative (시장 닫혀 tick 없는데 "dead-in-prod" 오판) 차단.

**Counter `increase()` semantic** — container restart 시 counter 가 0 으로 reset
되나 Prometheus `increase()` 가 reset 을 자동 보정. enforcement 는
`increase(counter[Nd]) >= 1` 사용 (instantaneous `counter` value 아님 — restart
직후 0 false-negative 차단).

## §4 meta-recursion 1단 차단 (ADR-033 §5 cross-ref)

counter-emit code path 자체 = triad v1 reapply (counter file:line citation +
counter caller grep ≥1 + counter integration test PASS). **무한 recursion 차단** —
counter-of-counter (counter-emit 의 counter) 미적용, **1단 한정**.

근거 risk: MCT-179 §D8 가공 metric 사례 — Phase 0 verify 미수행 가공 metric 박제
→ R2 deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화 동형. counter-emit
path 가 triad v1 미적용 시 quad 4th gate 자체가 가공 metric 가능성. triad v1
reapply 1단 = 이 risk 차단의 최소 충분 조건 (2단 이상 = 무한 recursion, 비용 ≫
효용).

## §5 sibling cross-ref (R4 DRY mitigation)

- **`evidence-triad-verified-badge.md`** (triad v1 SSOT 유지) — triad 3 evidence
  정의 = sibling 페이지 forward ref. 본 quad 페이지 = **4th gate delta 만** 박제
  (DRY). sibling 페이지 §5 가 본 페이지로 cross-ref (양방향).
- **ADR-033** (`docs/adr/ADR-033-evidence-quad-enforcement-layer.md`) —
  enforcement layer SSOT (어떻게 강제: class taxonomy / traffic class N days /
  meta-recursion 1단 / Prometheus alert + monthly PMO audit).
- **ADR-032 §3.2** (`docs/adr/ADR-032-verified-badge-evidence-triad.md`) —
  quad v2 rule SSOT (무엇이 evidence: triad v1 + 4th telemetry).
  `(file:line + caller_grep ≥1 + integration_test PASS) AND
  (telemetry_counter ≥1 over N days)`.
- **`docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`**
  (MCT-189 caller-wired vs decision-defined 분리 첫 사례 — runtime-observed tier
  도입 motivation).
