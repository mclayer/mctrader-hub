---
type: pmo-incident-audit
incident_key: INCIDENT-2026-05-17-disk-pressure-117GB
incident_status: PARTIAL — 코드 측 fix LAND, 운영 측 자연 회수는 사전 회귀 2건 (이슈 A NAS 403 + 이슈 B sort drift) LAND 후 점진
audit_date: "2026-05-17"
author: PMOAgent (codeforge orchestrator session, Claude Opus 4.7)
scope: cross-repo 인시던트 process pattern + ADR 후보 + codeforge governance 입력 + cross-Story trend 박제
data_side_retro: mctrader-data/docs/retros/2026-05-17-disk-pressure-incident.md  # 1차 SSOT (도메인 사실 + 디버깅 trace)
verified_sources:
  - mctrader-data#83 (WS-B `4dc11dc`, merged 2026-05-17T11:07:19Z)
  - mctrader-data#85 (WS-A `f2e2bc9`, merged 2026-05-17T12:57:37Z)
  - mctrader-data#92 (U1-ADR `ecfe150`, merged 2026-05-17T14:03:55Z)
  - mctrader-data#93 (MCT-182 + trace `be5bd50`, merged 2026-05-17T14:26:08Z)
  - mctrader-hub#393 (ADR-034 publish `ac01ab7`, merged 2026-05-17T14:03:50Z)
  - 본 세션 transcript (codeforge orchestrator)
related_adrs:
  - ADR-034 (NAS Object Key Unification — Accepted, hub SSOT)
  - ADR-027 §D6 (silent-skip 차단 — amendment 후보, Action Item 1)
  - ADR-064 (codeforge precedence rule — 1회 invocation 효과 검증)
  - ADR-040 (worktree-first workflow — 본 retro 작성 시 적용)
follow_up_adr_candidates:
  - ADR-027 §D6 Amendment: forward `_dispatch_dual_write` NAS 403 silent fallback 차단 (이슈 A 후속)
  - 신규 ADR: production-faithful test fixture 강제 게이트 (codeforge governance)
  - 신규 ADR (또는 chore): vendor wheel staleness CI gate (Dockerfile build dry-run + entrypoint import smoke)
---

# PMO Incident Audit — 디스크 압박 117GB (2026-05-17)

> PMOAgent cross-repo 횡단 감사. 도메인 사실 + 디버깅 trace + lessons learned 는
> [mctrader-data 1차 retro SSOT](https://github.com/mclayer/mctrader-data/blob/main/docs/retros/2026-05-17-disk-pressure-incident.md)
> 가 담당. 본 문서는 **process pattern · gate 준수 audit · ADR 후보 발의 ·
> codeforge governance 입력 · cross-Story trend** 만 박제 (PMO 책임 경계,
> memory feedback_pmo_retro_mandatory + feedback_lane_self_write_boundary 정합).

## 1. 인시던트 개요 (verified)

| 항목 | 값 |
|------|-----|
| Incident | 디스크 압박 117GB 미해소 (mctrader-compactor production) |
| 상태 | PARTIAL — 코드 측 fix LAND, 운영 측 자연 회수 게이트 = 이슈 A + B LAND |
| Duration | ~8h (사용자 보고 ~13:00 KST → 본 세션 종료 ~21:30 KST) |
| 영향 repo | mctrader-data (1차) + mctrader-hub (ADR carrier) |
| 영향 PR | mctrader-data#83 / #85 / #92 / #93 + mctrader-hub#393 (5 PR, 1 day window) |
| 가설 정정 횟수 | 6 (H1 glob 구분자 / H3 단순 l1/ prefix / manifest-bounded / hour-filter / rglob / 멀티 RC) |
| 잘못된 fix LAND | **0** (디버깅 규율 효과 정량 — 6 prevent / 6 가설) |
| 노출 사전 회귀 | 2 (이슈 A NAS 403 + 이슈 B l2.py sort byte-order) |
| 자연 회수 이론치 | 16,946 files / batch_limit 500 / 6min cycle ≈ ~3.4h (실측 예상 52h, I/O 경합) |

## 2. Cross-repo / Cross-Story 패턴 분석 (PMO 핵심 책임)

### 패턴 #1 — 다층 결함 동시 노출 (multi-defect surfacing, CRITICAL trend)

단일 인시던트 (디스크 압박) 진단 중 **3 + 2 = 5 RC** 동시 surface:
- 직접 RC: RC-1 (forward 윈도우) + RC-2 (nas_key tier-비인지) + RC-3 (backfill 루프).
- 동반 RC: 이슈 A (NAS 403) + 이슈 B (l2.py sort byte-order).

공통 특성:
- 이슈 A/B 둘 다 단위/통합 테스트 부재 (production-faithful fixture 미박제).
- 운영 적용 단계 (WS-A 첫 실행) 에서만 surface.
- forward 경로 silent fallback (403 silent + sort fallback monotonic_violation skip) 으로 일상 운영 중 가시화 안 됨.

**PMO 판정**: 단발 사고 아님 = **구조적 트렌드**. 동형 = "production-faithful fixture
부재 → 운영 적용 단계까지 latent → 인시던트 1건이 multi-defect surfacing 자연 trigger".
EPIC-mctrader-docker-stack PMO audit (`PMO-AUDIT-EPIC-mctrader-docker-stack.md` 패턴 #1
"Phase 0 verify code lane gap 6회 재현") 와 동형 — code lane Phase 0 verify 강제 게이트
부재가 본 인시던트에서도 surface. ADR 후보 발의 근거 (§3).

### 패턴 #2 — 테스트 fixture 가 production layout 결함 마스킹 (positive lesson)

PR #85 commit `c169720` "CRITICAL fix" 사례. fixture 가 `date=*/part-*.parquet`
평면 layout 으로 seed → 비재귀 `glob` 통과 → production `date=*/node=*/part-*.parquet`
에서 0 match. fixture 와 production layout 의 drift 가 production 적용 시점에야 surface.

**PMO 판정**: 패턴 #1 의 sub-pattern. fixture-vs-production layout drift 는 production
layout SSOT 를 단위/통합 fixture 가 정확히 반영하도록 강제하는 codeforge governance rule
부재 신호. PR #85 가 `production node= layout` 회귀 단위 + 통합 5 시나리오로 박제했으나,
**전 lane / 전 repo 차원의 강제 게이트는 부재**. ADR 후보 (§3 #2).

### 패턴 #3 — vendor wheel staleness 가 deploy unblock 차단 (cross-repo bundling 트렌드)

MCT-182 vendor wheel (mctrader_market 0.1.0) 가 paper_lineage / aggregation 누락 상태로
12.1KB 박제. WS-A/B 코드는 paper_lineage 미참조라 단위/통합 테스트 통과, 그러나 신규
이미지 빌드 시 entrypoint 의 다른 모듈이 paper_lineage import → runtime
`ModuleNotFoundError`. CI 또는 staging deploy gate 에서 import smoke test 부재로
LAND 후 운영 적용 시점에야 surface.

**PMO 판정**: 본 인시던트 1회 발현이나, cross-repo bundling (vendor wheel pattern) 의
구조적 weakness. mctrader-engine / mctrader-signal-collector 등 sibling repo 의
vendor wheel 도 동형 위험 보유. ADR 후보 또는 chore (§3 #3).

### 패턴 #4 — 시스템 디버깅 규율 ROI 단일 세션 내 회수 (positive pattern, 박제 권고)

6 가설 / 0 잘못된 fix LAND. `superpowers:systematic-debugging` 의 "Verify before
continuing" 가 6/6 prevent. 정성 효과:
- 잘못된 fix 1건 LAND 시 비용 = 추가 patch 사이클 + 운영 트래픽 영향 + trust capital 소진.
- 6 가설 verify 비용 = 평균 5~10분 × 6 = ~30~60분.
- ROI = 단일 세션 내 회수 + 이후 세션 trust capital 보존.

**PMO 판정**: positive pattern. 디버깅 규율의 ROI 가 단일 인시던트 내에서 회수 = 규율
적용 의무의 정량 근거. memory feedback_systematic_debugging_mandatory 정합. EPIC
audit 의 "design lane 전수 reconcile ROI 비대칭" 패턴과 동형 (1회 비용 → 후속 다회
회수). 차기 codeforge governance 입력에 정량 case study 로 박제 권고.

### 패턴 #5 — cross-repo retrospective SSOT 도메인 분리 (positive pattern, 박제 권고)

본 인시던트 retro 가 mctrader-data (1차 사실/디버깅/lesson) + mctrader-hub (process
pattern/ADR/governance) 로 도메인 분리 박제. memory feedback_lane_self_write_boundary
정합 — repo 별 reader 가 자기 SSOT 만 보아도 의사결정 가능.

**PMO 판정**: positive pattern. 이전 EPIC-mctrader-docker-stack 의 EPIC-RESULTS (data)
+ PMO-AUDIT-EPIC (hub) 분리 동형. **차기 권고**: cross-repo 인시던트는 retro 도 도메인
분리 박제 — 단일 통합 문서 (cross-repo SSOT) 채택 금지 (codeforge governance pattern).

## 3. ADR 후보 발의 (PMO 핵심 책임)

본 인시던트 process pattern 분석 결과 3건 ADR 후보 발의.

### 후보 #1 — ADR-027 §D6 Amendment: forward `_dispatch_dual_write` NAS 403 silent fallback 차단

```markdown
---
category: Data Integrity / Operational Risk
title: "ADR-027 Amendment N: forward _dispatch_dual_write NAS 403 silent fallback 차단"
trigger: "INCIDENT-2026-05-17-disk-pressure 의 이슈 A — NAS bucket auth/policy 회귀로
forward 경로 PUT 403 silent fallback → 신규 L1 미적재 → 디스크 점유 증가. silent
failure = ADR-027 §D6 silent-skip 차단 정신 위반"
---

## 배경
- forward `_dispatch_dual_write` 가 NAS PUT 403 (bucket auth 회귀) 을 silent
  fallback (local-only) 으로 처리.
- 결과: 신규 L1 sealed segments 가 NAS 미적재 → WS-B sweep 안전망 (4중 HEAD verify) 으로
  `preserved` → 디스크 점유 증가.
- 일상 운영 중에는 가시화 안 됨 (Prometheus Counter alert 부재).

## 문제
ADR-027 §D6 (7종 invariant per-file, silent-skip 차단) 의 정신은 "처리 실패 시 명시
OperationalRiskAlert + raise". 그러나 forward 경로의 NAS PUT 403 은 silent fallback 으로
처리되어 §D6 정합 미달. 인시던트 진단 단계에 와서야 surface.

## 제안 결정 (옵션)
1. **NAS PUT 4xx → 명시 OperationalRiskAlert + Prometheus Counter emit + raise**
   (silent fallback 금지)
2. NAS PUT 5xx → retry-with-backoff + 5xx 임계 초과 시 alert (서버측 transient 보호)
3. forward 경로의 모든 silent fallback 경로 §D6 정합 audit (cross-cutting one-shot)

## 예상 결과
- NAS auth/policy 회귀의 detection latency: 운영 적용 단계 (며칠~주) → 실시간 alert (분 단위)
- 본 인시던트 동형 (sibling repo NAS PUT 경로) 재발 방지
```

### 후보 #2 — 신규 ADR: production-faithful test fixture 강제 게이트 (codeforge governance)

```markdown
---
category: Process / Quality Gate
title: "ADR-NNN: production-faithful test fixture 강제 게이트 — layout SSOT 일치 검증 의무"
trigger: "INCIDENT-2026-05-17-disk-pressure 의 rglob 사례 (PR #85 commit c169720
CRITICAL fix). fixture date=*/part-*.parquet 평면 vs production date=*/node=*/part-*.parquet
drift 가 비재귀 glob 결함을 마스킹 → production 적용 시점 0 match no-op. 패턴 #1
(다층 결함 동시 노출) 의 sub-pattern."
---

## 배경
- 본 인시던트 rglob fix 외에도 EPIC-mctrader-docker-stack 의 metric producer path 가정
  오류 (MCT-179/180) 가 동형 — fixture 가 producer instantiation 경로를 정확히 반영
  못 함.
- fixture-vs-production drift = "테스트는 통과 / production 적용 시점 surface" 패턴.

## 문제
fixture 작성 시점에 production layout SSOT 와의 일치를 강제하는 게이트 부재.
ArchitectPL deputy 도 fixture 정합성 검수 책임 미명시.

## 제안 결정 (옵션)
1. **TestContractArch deputy §8 검수 범위 확장** — §8 Test Contract 에 "fixture layout
   = production layout SSOT 1:1 일치" 항목 추가 (DesignReview lane shift-left)
2. **production layout SSOT 박제 의무** — runtime layout 변경 PR 은 SSOT 박제 의무
   (e.g. CLAUDE.md "WAL path layout" section 갱신)
3. **fixture grep gate** — production code 의 `Path.rglob` / `Path.glob` 호출 vs fixture
   의 layout 일치 grep CI gate (codeforge governance)

## 예상 결과
- fixture-vs-production drift detection: production 적용 → CI/리뷰 단계
- 본 인시던트 동형 (forward / sweep layout 가정 오류) 재발 방지
- EPIC-mctrader-docker-stack 패턴 #1 (Phase 0 verify code lane gap) 의 sub-pattern 해소
```

### 후보 #3 — 신규 ADR (또는 chore): vendor wheel staleness CI gate

```markdown
---
category: Process / Deploy Gate
title: "ADR-NNN: vendor wheel staleness CI gate — Dockerfile build dry-run + entrypoint import smoke 강제"
trigger: "INCIDENT-2026-05-17-disk-pressure 의 MCT-182 vendor wheel (mctrader_market 0.1.0)
paper_lineage 누락 — 단위/통합 테스트 통과 / 신규 이미지 빌드 후 runtime ModuleNotFoundError
restart loop. 운영 적용 시점에야 surface = deploy unblock 차단 위험."
---

## 배경
- vendor wheel pattern = sibling repo (mctrader-market / mctrader-engine 등) 코드를
  소비 repo (mctrader-data 등) 가 wheel artifact 로 bundling.
- wheel staleness = sibling repo 변경 (신규 module 추가) 후 wheel rebuild 미반영.
- 영향: 신규 이미지 빌드 시 runtime ImportError 로 deploy unblock 차단.

## 문제
- 단위/통합 테스트는 소비 코드만 검증 (vendor wheel 의 transitive import 미검증).
- CI deploy gate (Dockerfile build dry-run + entrypoint import smoke) 부재.
- LAND 후 운영 적용 시점에야 surface.

## 제안 결정 (옵션)
1. **Dockerfile build dry-run CI gate** — PR CI 에 `docker build --target <runtime>` 강제 +
   image entrypoint import smoke (`python -c "import <entrypoint_module>"`)
2. **vendor wheel rebuild trigger** — sibling repo main commit 시 소비 repo 의 wheel
   rebuild PR 자동 발의 (Renovate-style automation)
3. **vendor wheel content audit** — wheel 의 entries 목록을 PR diff 에 자동 첨부
   (paper_lineage 같은 누락이 reviewer 가시화)

## 예상 결과
- vendor wheel staleness detection: 운영 적용 → CI 단계
- 본 인시던트 동형 (sibling repo 신규 module 추가 시 소비 repo 미반영) 재발 방지
- Deploy unblock 차단 위험 제거
```

**ADR 후보 발의처**:
- 후보 #1 = mctrader-hub `docs/adr/ADR-027` Amendment (도메인 ADR carrier).
- 후보 #2, #3 = codeforge plugin 영역 (process/quality gate = 전 consumer 공통).
  Orchestrator 경유 codeforge-design ArchitectAgent spawn 입력 권고. PMO 는 발의자,
  결정자 아님.

## 4. Gate 준수 audit

### 4.1 디버깅 규율 gate

| Gate | 적용 결과 |
|------|-----------|
| `superpowers:systematic-debugging` "Verify before continuing" | **6/6 prevent** (잘못된 fix LAND 0) |
| `superpowers:test-driven-development` (WS-B helper) | 적용 (PR #83 commit `5a7dcd1` 실패→구현→통과 TDD) |
| `superpowers:verification-before-completion` (PR #85 운영 적용 전) | 적용 (CLI testcontainers 8 케이스 + 단위 6 + 통합 5) |
| `ADR-064` codeforge precedence rule ("추측 멈춤 + derived default 발화") | 1회 invocation 효과 검증 (§3.2 H3 정정 시점) |

### 4.2 ADR carrier 정합 gate

| Gate | 적용 결과 |
|------|-----------|
| ADR-031 Layer 2 (도메인 ADR carrier = hub) | 적용 (ADR-034 publish in hub#393, U1-ADR data#92 = data 측 산출물만) |
| memory feedback_lane_self_write_boundary | 적용 (본 retro = data 사실 / hub audit = process pattern, 도메인 분리 박제) |

### 4.3 cross-repo bundling gate (gap 식별)

| Gate | 상태 |
|------|------|
| vendor wheel staleness CI gate | **부재** → ADR 후보 #3 |
| production-faithful fixture 강제 | **부재** → ADR 후보 #2 |
| forward 경로 silent fallback 차단 (ADR-027 §D6 정합) | **부분** (sweep 경로는 적용, forward 경로는 gap) → ADR 후보 #1 |

## 5. Cross-Story trend (선행 EPIC 과의 동형 확인)

`PMO-AUDIT-EPIC-mctrader-docker-stack.md` (2026-05-16, milestone 7/7) 패턴 #1 과의
동형 trend 확인:

| 항목 | EPIC-mctrader-docker-stack 패턴 #1 | 본 인시던트 |
|------|----------------------------------|-------------|
| trend 명 | Phase 0 verify code lane gap (6회 재현) | 다층 결함 동시 노출 + production-faithful fixture 부재 |
| 공통 root | 설계/code 가 sibling repo runtime / 실 layout / metric producer path 를 grep 실증 없이 가설 수용 | 동일 (fixture 가 production layout 미반영 + vendor wheel 의 transitive import 미검증) |
| 횟수 | 6회 (Story 7건 중) | 본 인시던트 단발 (그러나 multi-defect 5건 surface) |
| ADR 후보 | code lane Phase 0 verify 강제 게이트 (선행 EPIC PMO audit §3) | 후보 #2 (production-faithful fixture) — 동형 sub-pattern |

**PMO 판정**: 본 인시던트의 패턴 #2 (fixture masking) = 선행 EPIC 의 Phase 0 verify code
lane gap 의 sub-pattern. **두 audit 간 cross-ref 박제 권고** — ADR 발의 시점에 두 사례
모두 trigger 박제 (정량 근거 강화).

## 6. Carry-over 후속 액션 (codeforge governance 입력)

| # | Action | 소유 | 타임라인 |
|---|---|---|---|
| 1 | ADR-027 Amendment 발의 (이슈 A 후속) — forward `_dispatch_dual_write` NAS 403 silent fallback 차단 | hub ArchitectPL (도메인 ADR carrier) | 이슈 A LAND 전 의무 |
| 2 | codeforge governance ADR 발의 — production-faithful fixture 강제 게이트 (TestContractArch deputy §8 검수 범위 확장) | codeforge-design ArchitectAgent (Orchestrator 경유) | 본 인시던트 + EPIC-docker-stack patterns #1 cross-ref 박제 후 |
| 3 | codeforge governance ADR (또는 chore) 발의 — vendor wheel staleness CI gate | codeforge / infra lane | 차기 Epic 입력 |
| 4 | codeforge `retro-template` 도구화 — 본 retro frontmatter / §1-§8 구조를 template skill 로 박제 | codeforge governance (hub PMO 발의) | LOW priority, carry-over |
| 5 | 본 인시던트 + EPIC-mctrader-docker-stack PMO audit cross-ref 의무 박제 (ADR 후보 #2 trigger 통합) | hub PMO (본 audit 의 self-ref) | 후속 audit 진행 시 |

## 7. Cross-ref

| 항목 | 위치 |
|---|---|
| 1차 retro SSOT (data 사실 + 디버깅 trace + lesson) | mctrader-data `docs/retros/2026-05-17-disk-pressure-incident.md` |
| WS-B PR (RC-2 fix) | mctrader-data#83 (`4dc11dc`) |
| WS-A PR (RC-1 회수 도구) | mctrader-data#85 (`f2e2bc9`) |
| U1-ADR PR (Phase 2 gate) | mctrader-data#92 (`ecfe150`) |
| MCT-182 + trace PR | mctrader-data#93 (`be5bd50`) |
| ADR-034 carrier PR | mctrader-hub#393 (`ac01ab7`) |
| 본 audit data 측 PR | mctrader-data#94 (1차 retro) |
| 본 audit hub 측 PR | mctrader-hub#??? (본 commit) |
| 선행 EPIC PMO audit (패턴 cross-ref) | `docs/retros/PMO-AUDIT-EPIC-mctrader-docker-stack.md` |
| EPIC nas-key-unification (별 Epic) | mctrader-data#86 / #87 / #88 / #89 / #90 close / #91 |
| 후속 Story (이슈 A) | 별 세션 발의 대기 |
| 후속 Story (이슈 B) | 별 세션 발의 대기 (spec `mctrader-data/docs/superpowers/specs/2026-05-17-compactor-sort-key-l1-naming.md` 박제) |
