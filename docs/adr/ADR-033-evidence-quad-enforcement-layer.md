---
adr_key: ADR-033
title: Evidence Quad Enforcement Layer
status: Proposed
class: governance
proposed_at: "2026-05-17"
owner_story: MCT-191
epic: EPIC-evidence-quad-runtime-telemetry
parent: ADR-032 §8.1 future-work
cross_ref:
  - "ADR-032 §3 (Triad Rule v1 back ref) + §8.1 (quad future-work) + §9 (Self-reference Caveat)"
  - "ADR-029/030/031 (class:production grandfathering 대상)"
  - "plugin-codeforge#804/#805/#822 (CI mechanical gate consumer carry)"
amendments: []
---

# ADR-033 — Evidence Quad Enforcement Layer

## §1 Trigger — ADR-032 §8.1 future-work owner

ADR-032 §8.1 (`docs/adr/ADR-032-verified-badge-evidence-triad.md:196-200`) 가 evidence triad
4번째 게이트 (runtime telemetry counter) 를 **별 Story MCT-NNN** future-work 으로 명시. 본
ADR-033 = 해당 future-work 의 enforcement layer SSOT 본문 격상 (신규 발명 아님 — ADR-032
기존 §8.1/§9 구조 정합).

### §1.1 근본 문제 — Hyrum's Law 역방향 dead-in-prod false-negative

triad v1 = `file:line + production caller git grep ≥1 + integration test PASS` (ADR-032 §3).
caller grep ≥1 게이트는 **dead-in-prod (test-only / deprecated caller) 를 완전 차단 불가**:
caller 가 존재해도 production traffic 이 그 code path 를 실행하지 않으면 silent
false-negative (wiring 박제 거짓 신호). Hyrum's Law 역방향 = "telemetry 0 over N days →
production 의존자 실 부재 추정" (정적 grep evidence 의 runtime 보강).

### §1.2 동형 사례 3건 (triad v1 한계 실증)

| # | 사례 | grep evidence | 실 production wiring | 결함 |
|---|------|---------------|---------------------|------|
| MCT-184 | dead-in-data (data `api/`) | caller grep ≥1 (data 내부 호출) | production caller 0 (consumer=MCT-185 cutover 전) | F-1 silent corruption + F-2 INV-3 mismatch (cutover 시 즉시 데이터 손상) |
| MCT-180 | paper daemon ReaderCache | grep 1 (`ReaderCache.stats()`) | PaperRunner WS path 미인스턴스화 = production caller 0 | docker-stack.json panel id=7,8 가공 metric → downgrade |
| MCT-179 | §D8 가공 metric | (Phase 0 verify 미수행) | LAND registry 부재 가공 metric 박제 | R2 CRITICAL deliverable (WAL 30G Epic-CLOSE-FAIL-gate alert) 무력화 |

3 사례 종합 = "caller grep ≥1 = wiring proof" 가정의 dead-in-prod false-negative 한계.
runtime telemetry counter = 4번째 게이트로 "최소 1회 production code path 실행" 박제.

## §2 Decision — Evidence Quad Rule v2 (triad superset)

> ADR-032 §3 Triad Rule v1 **back ref**. quad v2 = triad v1 의 strict superset (triad 3종
> 유지 + 4번째 게이트 추가, triad 폐기 아님).

```
quad v2 = (file:line + production caller git grep ≥1 + integration test PASS)
          AND (runtime telemetry counter ≥ 1 over N days)
```

### §2.1 4번째 게이트 — runtime telemetry counter

production traffic 이 ADR-N 결정 code path 를 실제 실행했다는 wiring evidence. counter ≥1
over N days = "관측 window 내 최소 1회 production code path 실행 박제" — dead-in-prod
(test-only / deprecated caller) false-negative 차단.

### §2.2 Counter monotonicity wiring proof (Prometheus Counter ≠ Gauge)

- **Prometheus Counter** = monotonic 누적 (only-increase, container restart 시 reset →
  `increase()` 자동 보정). 과거 임의 시점 traffic 실행 = irrefutable evidence (한 번
  올라간 누적값은 부정 불가).
- **Prometheus Gauge** = current-state instantaneous value. scrape miss / window 밖 관측 시
  false-negative (현재 0 = 과거 실행 0 아님). quad 4번째 게이트 = **Counter only**
  (Gauge 금지 — MCT-179 §D8 Gauge 가공 metric 동형 risk 차단).
- quad spec semantic = `increase(<counter>[Nd]) >= 1` (instantaneous value 비교 아님).

## §3 ADR class taxonomy (frontmatter `class` field 신규)

ADR frontmatter `class: governance|production|mixed` field 신규 — quad 의무 여부의
SSOT 분류 기준.

| class | 정의 | quad 의무 | 비고 |
|-------|------|-----------|------|
| **governance** | code wiring 0 (ADR 자체가 정책/프로세스 SSOT) | **면제** (triad v1 + Caveat) | telemetry counter forever 0 정상. 예: ADR-032/033/045/064 |
| **production** | code wiring 有 (ADR 가 production source 결정) | **의무** (telemetry counter ≥1 over N days) | 예: ADR-029/030/031/017/009/027 |
| **mixed** | 부분 (일부 § governance, 일부 production) | production § 만 의무 | § 단위 분류 |

### §3.1 현 ADR 분류표 (SSOT)

| ADR | class | 근거 |
|-----|-------|------|
| ADR-029 | production | `promote_l1`/DualWriter wiring (MCT-189 LAND) |
| ADR-030 | production | compose/observability wiring (MCT-175~181 LAND) |
| ADR-031 | production | `data_client`/io relocate wiring (MCT-182~188 LAND) |
| ADR-032 | governance | evidence triad rule SSOT (code wiring 0) |
| ADR-033 | governance | 본 ADR — enforcement layer rule SSOT (code wiring 0) |

> **INV (additive only)**: frontmatter 3 스타일 비동질 (ADR-029 `adr_id`+`category` /
> ADR-030·031 frontmatter 부재 / ADR-032·033 `adr_key`+`status`) 보존. `class:` field
> 만 additive 추가 — 정규화 금지 (SSOT drift 차단, F-0b).

## §4 Traffic class 차등 N days window (Q4 + Q10 = C)

quad 4번째 게이트 N days window 는 traffic class 별 차등 (single 14d 적용 시
market-closed false-negative):

| traffic class | window | 근거 |
|---------------|--------|------|
| **production-wired ADR** | 14d calendar | MCT-172 D8-4 정합 (`nas_reader_ambiguity_total` 14d rolling 선례) |
| **governance ADR** | N/A | `telemetry_counter_caveat` (§7 grandfathering, code wiring 0) |
| **trading-hot path** (collector tick = market traffic 의존) | market-open hours rolling | KRX 09:00-15:30 KST 7.5h/day × 10 trading days ≈ 75h rolling (weekend/공휴일 제외 — market-closed false-negative 차단) |
| **trading-cold path** (engine cold reader = backtest/cutover 경로) | 14d calendar | market traffic 비의존 (backfill/cutover 경로) |

### §4.1 Counter `increase()` semantic

container restart 시 counter reset = Prometheus `increase()` 자동 보정 (reset
detection + 누적 복원). quad spec = `increase(<counter>[Nd]) >= 1` (instantaneous
value 아님, §2.2 monotonicity proof 정합).

## §5 Quad meta-recursion 1단 차단 (Q5 = C)

quad 4번째 게이트 counter 자체가 dead-in-prod 면 quad PASS 거짓 신호 (MCT-179 §D8 가공
metric 동형 risk — Phase 0 verify 미수행 counter 박제 → R2 deliverable 무력화 재현).

**차단 rule**: counter-emit code path 자체 = triad v1 **reapply 의무**:
- counter 정의 file:line 박제 (decision-defined)
- counter caller `git grep` ≥1 (production emit wiring)
- counter integration test PASS (실 경로 evidence)

**무한 recursion 차단 = 1단 한정**: counter-of-counter (counter-emit 의 counter) 미적용.
quad → counter-emit triad v1 까지만 (2단 이상 재귀 금지 — verify 비용 무한 폭증 회피).

## §6 Enforcement timing (Q7 = C, sub-3 MCT-193 carry)

| 게이트 | method | trigger |
|--------|--------|---------|
| Prometheus alert rule | `increase(<counter>[Nd]) == 0` (production-wired ADR) | critical alert + GitHub issue 자동 발의 (ADR-N quad violation) |
| monthly PMO audit batch | PMO-AUDIT-*.md §lane gate 의 quad evidence verify row + class taxonomy classification drift 보정 | mctrader-hub cron workflow (monthly) |

실 운영 method (alert rule yaml + cron workflow 구현) = **sub-3 MCT-193 owner** (본
ADR-033 = rule SSOT, 운영 carrier = MCT-193, §9 carry). LAND 시점 triad v1 의무 +
post-LAND telemetry verify = MCT-193 분리.

## §7 Grandfathering scope (Q3 = C)

big-bang migration 회피 — production-wired ADR 만 점진 quad 적용:

| 대상 | 의무 | 비고 |
|------|------|------|
| production-wired ADR (ADR-029/030/031/017/009/027) | quad 의무 | MCT-191 LAND 후 telemetry counter ≥1 verify (sub-2 emit / sub-3 gate) |
| governance ADR (ADR-032/033/045/064) | triad v1 + `telemetry_counter_caveat` | quad 면제 (code wiring 0 → telemetry forever 0 정상, false-positive fail 차단) |
| MCT-191 LAND 후 신규 production ADR | quad 의무 (default) | 신규 ADR 부터 quad 기본 적용 |

기존 ADR big migration 회피 = production-wired ADR 만 점진 적용 (sub-2 scope). governance
ADR `telemetry_counter_caveat` = ADR-032 §9 Self-reference Caveat 의 telemetry 축 확장
(INV-1 forcing function reapply — governance ADR self-reference quad verify 자가붕괴 차단,
R1 mitigation).

## §8 Consequences / Cross-ref

**Positive**:
- dead-in-prod false-negative 차단 (MCT-184/180/179 3 사례 동형 risk 구조적 해소)
- Counter monotonicity = irrefutable runtime wiring proof (Gauge scrape-miss 한계 극복)
- class taxonomy = quad 의무 여부 SSOT (governance/production 명시 분류, 자가붕괴 차단)

**Negative**:
- 박제 의무 ↑ (quad 4번째 게이트 + counter-emit triad v1 reapply §5)
- cross-repo telemetry emit 의존 (sub-2 MCT-192 carrier — data + engine code wiring)
- 실 enforcement (alert rule + cron) = sub-3 MCT-193 carry (본 ADR = rule SSOT only)

**Cross-ref**:
- **ADR-032 §3** (Triad Rule v1 — quad v2 back ref base) + **§8.1** (quad future-work
  본문 격상 carrier) + **§9** (Self-reference Caveat — `telemetry_counter_caveat` =
  telemetry 축 확장)
- **ADR-029/030/031** (class:production grandfathering 대상, §3.1/§7)
- **plugin-codeforge#804** (박제 PR completeness CI gate) + **#805** (post-merge audit
  lane) + **#822** (subagent self-report verify gate) — CI mechanical gate consumer carry
- **MCT-184/180/179** dead-in-prod 동형 사례 (§1.2 trigger)
- **EPIC-evidence-quad-runtime-telemetry** sub-2 MCT-192 (cross-repo telemetry emit) +
  sub-3 MCT-193 (verify gate 운영)

## §9 Future Work / Out of Scope (carry)

### §9.1 sub-2 MCT-192 — cross-repo telemetry counter emit

mctrader-data (collector / api) + mctrader-engine (data_client / realtime / cold reader)
production code path 에 telemetry counter emit 신규. counter-emit code path = §5
meta-recursion 1단 triad v1 reapply 의무 (counter 정의 file:line + caller grep ≥1 +
integration test PASS).

### §9.2 sub-3 MCT-193 — post-LAND verify gate 운영 method

§6 enforcement 의 실 carrier — Prometheus alert rule yaml (`increase(<counter>[Nd]) == 0`
→ critical + GitHub issue 자동 발의) + monthly PMO audit cron workflow (class taxonomy
drift 보정). 본 ADR-033 §6 = rule SSOT, 운영 구현 = MCT-193.

### §9.3 counter family SSOT (Q8 = C)

counter name + family + emit location = per-ADR scope_manifest `verify_evidence.
telemetry_counter` field 분산 (ADR-N별 SSOT, 중앙 registry 미도입 — additive 정합). schema
정의 = MCT-191, 적용 = sub-2 MCT-192.

## §10 Status

**Proposed** (2026-05-17, MCT-191 Phase 1 publish)

상태 transition: **Proposed (MCT-191 LAND)** → Accepted (sub-2 MCT-192 + sub-3 MCT-193
LAND 후, telemetry counter emit + verify gate 운영 검증 완결 시점) → POLICY_FINALIZED
(EPIC-evidence-quad-runtime-telemetry 3/3 milestone COMPLETED).

- **owner_story**: MCT-191 (EPIC-evidence-quad-runtime-telemetry sub-1, doc-only,
  PMO+Codex 권고 small Epic 3 sub-Story 분해)
- **parent**: ADR-032 §8.1 future-work (MCT-190 LAND 2026-05-17, hub#375 6f19ec0)
- **self-reference Caveat**: 본 ADR-033 = `class: governance` → quad 면제 (§7
  grandfathering). telemetry counter forever 0 정상 (`telemetry_counter_caveat` INV-1
  reapply). triad v1 self-reference 적용 (ADR-032 §9 pattern 정합).
