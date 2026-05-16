---
type: pmo-story-retro-audit
story_key: MCT-186
epic_key: EPIC-data-domain-decoupling
epic_status: phase:IN_PROGRESS
milestone: "5/7"
story_status: COMPLETED
story_completed_at: "2026-05-17"
audit_date: "2026-05-17"
author: PMOAgent
scope: |
  단일 Story 완료 회고 감사 (게이트 준수 + FIX 루프 정합 + cross-Story 패턴 갱신 + 박제 PR
  5 체크리스트 cross-Story reapply 5/5 PASS 실효 검증 + ADR-032 evidence triad 2회 연속
  선제 reapply 실증 + code FIX 0회 design shift-left ROI 재증명 + 다음 Story 진입 권고).
  본 Story 회고는 RETRO-MCT-186.md (self-write SSOT, 8 sections) + EPIC-RESULTS §Story-5
  + Story §12 회고 (PMOAgent sub-dispatch) 가 SSOT. 본 문서는 PMO 횡단 감사 영역만 다룬다
  (게이트 준수 audit + cross-Story 트렌드 정밀 분석 + Phase 0 verify R1 가드 패턴 누적 +
  §3.2.4b file-delete caller grep gap 신규 lesson 박제 + Epic 진행 트렌드 갱신).
verified_sources:
  - "docs/stories/MCT-186.md (frontmatter COMPLETED 2026-05-17 + §0 Phase 0 Verify Gate V1-V10 + §9.2 AC/INV 전수 PASS + §10 FIX Ledger 1 row (design iter1 P0 §3.2.4b) + §11 LAND 3 행 + §12 PMOAgent 회고)"
  - "docs/retros/RETRO-MCT-186.md (self-write SSOT, 8 sections — 결과 지표 + FIX 루프 + Phase 0 verify 실증 + 설계 원칙 reapply + ADR 박제 + carry over + 다음 Story)"
  - "docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md (§Story-5 박제 + milestone 5/7 + ADR-031 §D4 VERIFIED)"
  - "docs/change-plans/MCT-186-change-plan.md (§1.5 cli.py modification + §3.2.4b 박제)"
  - "docs/retros/PMO-AUDIT-MCT-184.md (선행 PMO 감사 §4 codeforge upstream ADR escalation 후보 1+2+3 발의 baseline)"
  - "scope_manifests/EPIC-data-domain-decoupling.yaml (milestone 5/7 + D4 VERIFIED + epic_status_history)"
  - "plugin-codeforge#795 (OPEN): cross-document SSOT mechanical gate ADR escalation"
  - "plugin-codeforge#804 (OPEN): 박제 PR 자체 완결도 mechanical gate (후보 2)"
  - "plugin-codeforge#805 (OPEN): post-merge audit lane 신설 (후보 3)"
  - "git log: hub#370 (3fc9c1f, 2026-05-16T17:53:38Z Phase 1) + engine#60 (773b270, 2026-05-16T21:52:47Z Phase 2 PR1) + hub#371 (cab600b, 2026-05-16T22:07:13Z Phase 2 PR2 박제)"
---

# PMO Story 완료 감사 — MCT-186 (engine realtime cutover + exchange-adapter 제거)

> PMOAgent 단일 Story 완료 trigger 회고 감사 (feedback_pmo_retro_mandatory +
> feedback_escalate_to_codeforge + feedback_cross_plugin_drift_detection 정합). 자체 회고
> (RETRO-MCT-186) + Story §12 회고 (4-field schema) 는 self-write SSOT — 본 문서는 **PMO
> 횡단 감사** 영역만 다룬다:
> (1) 게이트 준수 audit (Preflight·FIX 카운터·§10 FIX Ledger·§11 LAND 박제 정합 + 박제 PR
>     5 체크리스트 cross-Story reapply 실효 검증)
> (2) cross-Story 패턴 정밀 분석 (Phase 0 verify R1 가드 효과 10회째 누적 + §3.2.4b
>     file-delete caller grep gap 신규 lesson + ADR-032 evidence triad 2회 연속 선제 reapply
>     + code lane FIX 0회 design shift-left ROI 재증명)
> (3) codeforge upstream ADR escalation 후보 1/2/3 evidence row 갱신 (#795/#804/#805 누적)
> (4) Epic 진행 트렌드 갱신 (milestone 5/7) + 다음 Story (MCT-187) 진입 권고 (7 항목 reapply)

## 1. Story 개요 (verified)

| 항목 | 값 |
|------|-----|
| Story | MCT-186 (sequential_phase 5, milestone **5/7**) |
| Epic | EPIC-data-domain-decoupling (4-Layer 다중거래소 확장 아키텍처) |
| 결정 | D4 (engine exchange-adapter 제거 — `option_chosen: subscribe-normalized-stream`) |
| 결과 | COMPLETED 2026-05-17. **AC 7/7 PASS / INV 6/6 PASS / 회귀 0 (881 passed)**. AC-1 grep0 = engine `src/` `from mctrader_market_bithumb` = **0건** (5곳 5파일 전부 제거) |
| 신규 파일 | 3 (`realtime/types.py` engine-local OrderbookSnapshot + `realtime/redis_subscriber.py` XREAD asyncio + `tests/test_realtime_subscriber.py` 4 testcontainers integration test) |
| 삭제 파일 | 1 (`runtime/ws_wrapper.py` — `WsWrapperStream` + `StreamExhaustedError` 완전 제거) |
| 수정 파일 | 7 (fill/simulated.py + realtime/stream_consumer.py + runtime/mock_stream.py + runtime/paper_runner.py + cli.py + pyproject.toml + tests/test_simulated_fill.py + tests/test_paper_executor.py) |
| 신규 test | 4 testcontainers[redis] integration test ALL PASS |
| PR | 3 (hub#370 Phase 1 docs + engine#60 Phase 2 PR1 code + hub#371 Phase 2 PR2 박제) |
| ADR 산출물 | **ADR-031 §D4 VERIFIED** (evidence triad: file:line + grep0 + integration test) + **ADR-030 NAS cred drop amendment box** (compose.yml engine NAS env 실 제거 = MCT-187 carry) |
| FIX 루프 | **design iter1 P0 1회** (cli.py StreamExhaustedError ws_wrapper.py 삭제 의존 발견 → §3.2.4b scope 추가 → CONDITIONAL_PASS → code iter PASS) + **code iter 0회** (engine#60 직접 PASS) |

## 2. 게이트 준수 audit (PMO 핵심 책임)

### 2.1 lane gate 전수 검증

| lane | gate verdict | iter | 비고 |
|------|--------------|------|------|
| 요구사항 | PASS | iter 1 | §0 Phase 0 Verify Gate V1-V10 박제 (engine repo HEAD `git fetch origin` 실증 + 5곳 5파일 bithumb import grep 전수 + V7/V8 `OrderbookSnapshotEvent` cascade 정정 발견 + V10 `_build_upstream_stream()` lazy import 분석) + R1 가드 의무 reapply (PMO-AUDIT-MCT-184 §6.2 8 항목) |
| 설계 | CONDITIONAL_PASS → PASS | iter 1 | ArchitectPL Change Plan §3.2.4b 신규 추가 (cli.py StreamExhaustedError import + catch block 제거 — ws_wrapper.py 삭제 연쇄). **§3.2.4b = 본 Story 신규 박제 lesson key** |
| **설계-리뷰** | **CONDITIONAL_PASS → PASS** | iter 1 P0×1 | **P0 finding: cli.py StreamExhaustedError ws_wrapper.py 삭제 의존 발견** (Change Plan 초안 §3.2 scope 누락). 정정: Change Plan §1.5 cli.py modification + §3.2.4b 박제. `gate:design-review-pass` ✓ |
| 구현 | PASS | iter 1 | engine#60 Phase 2 PR1 직접 PASS. 5곳 5파일 bithumb import 제거 + RedisStreamSubscriber + engine-local OrderbookSnapshot + ws_wrapper.py 삭제. 881 passed 신규 실패 0 |
| **구현-리뷰** | **PASS FIX 0회** | iter 1 | **code lane FIX 0회 달성** — design lane 조기 P0 차단 (§3.2.4b 추가) → code lane clean direct PASS. **MCT-179/183 lesson reapply 효과 누적 (design shift-left ROI 재증명 2회 연속)** |
| 통합테스트 | SKIP | — | Epic 7/7 후 1회 (MCT-188 owner) — 정상 |
| 보안테스트 | SKIP | — | lanes.security_ai default false — 정상. T1 path traversal / T2 DoS = redis_subscriber.py `BLOCK=1000ms count=100` + 5× retry exponential backoff 0.5s base = bounded resource consumption |

**판정**: pre-LAND 6 lane 게이트 전수 PASS. 설계-리뷰 iter1 P0 1건 (§3.2.4b cli.py
StreamExhaustedError) 발견은 **건강한 정상 작동** — design lane shift-left filter
효과 실증 (post-LAND silent ImportError 차단). 후속 lane 전수 PASS FIX 0회 = **design
shift-left ROI 회수 재증명 2회 연속** (MCT-184 pre-LAND P0×0 + MCT-186 code FIX 0회).

### 2.2 §10 FIX Ledger Orchestrator 독점 append 정합

- §10 헤더 명시: "Orchestrator 독점 append (fix-event-v1 contract). 본 에이전트 직접
  기록 금지." ✓
- 1 row 정합:
  - **iter 1 (design P0)** row: `lane = 설계-리뷰 / finding = cli.py StreamExhaustedError
    ws_wrapper.py 삭제 의존 발견 / 원인 = 설계 누락 / 처리 = Change Plan §3.2.4b 추가`
    = MCT-179 ESCALATE 동형 단발 P0 (단 chief judge 미발동 — design iter1 CONDITIONAL_PASS
    내 정정으로 해소)
- post-LAND Codex audit finding = **0건** (MCT-184 F-1~F-4 동형 미발생) → MCT-184
  post-merge audit sentry 3회 연속 효과의 추세 평가 = MCT-186 4회 연속 발견 부재
  (혹은 self-discipline 적용 효과)

**판정**: §10 Orchestrator 독점 append 룰 위반 0. fix-event-v1 contract 정합. design
lane P0 단발 + code lane FIX 0회 + post-LAND Codex audit finding 0 = **3 layer
gate 모두 정상 작동 + design shift-left filter 효과 1회 추가 실증**.

### 2.3 §11 LAND timeline 정합 (3 PR sequential 박제)

| land_order | repo | PR | commit | git verify | 박제 내용 |
|-----------|------|----|--------|-----------|----------|
| 1 | hub Phase 1 | #370 | `3fc9c1f` | (MERGED 2026-05-16T17:53:38Z) | docs only — Story §0-§11 + ADR-031 §D4 amendment box draft + ADR-030 NAS cred drop amendment box + Change Plan + scope_manifest MCT-186 IN_PROGRESS + CLAUDE.md |
| 2 | engine | #60 | `773b270` | (MERGED 2026-05-16T21:52:47Z) | Phase 2 PR1 — 5곳 5파일 bithumb import 제거 + `realtime/types.py` + `realtime/redis_subscriber.py` + `runtime/ws_wrapper.py` 삭제 + `tests/test_realtime_subscriber.py` 4 testcontainers PASS + 881 passed 신규 실패 0 |
| 3 | hub Phase 2 PR2 | #371 | `cab600b` | (MERGED 2026-05-16T22:07:13Z) | Phase 2 PR2 박제 — Story §8.5 Impl Manifest + ADR-031 §D4 VERIFIED + ADR-030 NAS cred drop LAND confirm + scope_manifest 5/7 + CLAUDE.md COMPLETED + RETRO-MCT-186 + EPIC-RESULTS §Story-5 |

**판정**: land_order 3 PR sequential 엄수. **박제 PR 5 체크리스트 (RETRO 존재 +
EPIC-RESULTS §Story-N + frontmatter status=COMPLETED + completed_at + CLAUDE.md
hub#TBD 잔존 0줄 + ADR amendment confirm) 5/5 PASS** = MCT-184 SSOT drift 3호 동형
재발 0 — **self-discipline 효과 검증 1회 (mechanical gate plugin-codeforge#804 미가용
전 유지 의무)**. 단 §12 회고 PMOAgent sub-dispatch row 가 hub#371 LAND 시점에 TBD 였던
→ 본 retro 작업 시점에 박제 완결 (4-field schema). 통상적 sub-dispatch 시점 분리
패턴 (audit-time amendment) 정합.

### 2.4 ADR-031 D-row ↔ scope_manifest §design_decisions 정합 (MCT-186 영역)

| D | option_chosen | owner_story | 상태 | 판정 |
|---|---------------|-------------|------|------|
| D4 | `subscribe-normalized-stream` | `MCT-186 (engine exchange-adapter 제거 — bithumb import 5곳 5파일 제거 + RedisStreamSubscriber + TickRowV1_1 정규화 소비)` | **VERIFIED 2026-05-17** (evidence triad: redis_subscriber.py:93-173 + paper_runner.py:265-274 caller grep + tests/test_realtime_subscriber.py 4종 PASS) | ✓ 정합 |
| D6 | `new-adr-031 + amendment` | `MCT-182 (publish) + MCT-188 (POLICY_FINALIZED)` | D1 VERIFIED (MCT-182) + D2 partial → VERIFIED (MCT-183/185) + D3 partial → VERIFIED (MCT-184/185) + **D4 VERIFIED (MCT-186)** + D5 RESERVED (MCT-187) + D7 RESERVED (MCT-188) | ✓ MCT-186 amendment box LAND confirm |

**판정**: D4 VERIFIED 상태 정확 (engine src/ bithumb import = 0건 grep0 + RedisStreamSubscriber
wiring file:line + testcontainers integration test triad 충족). D6 amendment box 박제 ↔
scope_manifest §epic_status_history 5 row 정합 (MCT-182~186). **Epic D-row 진행 5/7
누적 (D1+D2+D3+D4 VERIFIED, D5/D6/D7 RESERVED)** — POLICY_FINALIZED 전이 = MCT-188.

### 2.5 박제 PR 5 체크리스트 cross-Story reapply 실효 평가

MCT-184 PMO-AUDIT §4.3 박제 PR 자체 완결도 mechanical gate (codeforge upstream 후보 2,
plugin-codeforge#804) 의 5 체크리스트 self-discipline 이 MCT-186 에서 어떻게 reapply
됐는지 evidence 박제:

| 체크 항목 | MCT-184 hub#359 (SSOT drift 3호 발생) | **MCT-186 hub#371 (사전 차단)** | 평가 |
|----------|-----------------------------------------|-------------------------------------|------|
| RETRO 존재 | hub#359 MERGED 시점 미생성 → hub#360 amendment | **hub#371 박제 PR LAND 시점에 RETRO-MCT-186.md 신규 동반 LAND** | ✓ self-discipline 성공 |
| EPIC-RESULTS §Story-N | hub#359 미작성 → hub#360 amendment | **hub#371 박제 PR LAND 시점에 EPIC-RESULTS §Story-5 동반 박제 (12 §Story section 누적)** | ✓ self-discipline 성공 |
| frontmatter status=COMPLETED | hub#359 미전환 → hub#360 amendment | **hub#371 시점에 `status: COMPLETED` + `completed_at: "2026-05-17"` 동반 LAND** | ✓ self-discipline 성공 |
| CLAUDE.md hub#TBD 잔존 0줄 | hub#359 후 F-3 hub#TBD 잔존 → hub#360 amendment | **hub#371 LAND 시점에 CLAUDE.md `MCT-186 COMPLETED (2026-05-17)` 섹션 + hub#371 (cab600b) 실 commit 명기** | ✓ self-discipline 성공 |
| ADR amendment confirm | hub#359 부분 carry → hub#360 amendment | **hub#371 시점에 ADR-031 §D4 VERIFIED 박제 + ADR-030 NAS cred drop amendment box (실 compose wiring = MCT-187 carry 명기)** | ✓ self-discipline 성공 |

**판정**: 박제 PR 5 체크리스트 **5/5 PASS = MCT-184 SSOT drift 3호 동형 재발 0**.
self-discipline 효과 검증 **1회 실증** (mechanical gate plugin-codeforge#804 미가용 전
유지 의무). §12 회고 PMOAgent sub-dispatch row 만 audit-time amendment (통상 패턴
정합). **plugin-codeforge#804 ADR escalation 의 추가 evidence row** (self-discipline 가능
성 입증 = mechanical gate 의 정량 cost-benefit 분석에 회수 가능 사례 1건 추가).

### 2.6 게이트 준수 종합

pre-LAND 6 lane 전수 PASS + design iter1 P0×1 (§3.2.4b cli.py — 정상 shift-left filter)
+ code FIX 0회 + post-LAND Codex audit finding 0. 박제 PR 5 체크리스트 5/5 PASS (MCT-184
SSOT drift 3호 동형 재발 0). PMO 감사 발견 차단 사항 **0건**. 본 Story 의 운영 = **design
shift-left ROI 회수 재증명 2회 연속 + 박제 PR self-discipline 1회 실증 + ADR-032 evidence
triad 2회 연속 선제 reapply**.

## 3. cross-Story 패턴 정밀 분석

### 패턴 #1 — Phase 0 verify R1 가드 효과 누적 (10회째 사전 차단)

docker-stack Epic 누적 6회 사후 발견 → MCT-182 2건 + MCT-183 3건 + MCT-184 1건 + MCT-185
사전 차단 → **MCT-186 사전 차단 2건 (V7/V8 OrderbookSnapshotEvent cascade) = 10회째 누적
확장**:

| # | Story | 가설 / risk | 실상 / 정정 | 정정 시점 |
|---|-------|------------|------------|-----------|
| 1-6 | MCT-170/177/178/179/180 (docker-stack) | (전수 6회 사후 발견) | — | 코드 작업 후 |
| 7 | MCT-182 | engine CandleModel 5곳 import | 4곳 (docstring 오집계) | 요구사항 lane ✓ |
| 8-A/B/C | MCT-183 | 3건 사전 차단 (호출자 / namespace / lazy import) | HEAD 재검증 + INV-6 신규 | 요구사항 + 설계 lane ✓ |
| 9 | MCT-184 | data web framework / api/ namespace 부재 가설 | V1-V8 전수 HEAD 실증 정합 + lazy import grep reapply | 요구사항 lane ✓ |
| (MCT-185) | dead-in-data → live cutover 11 곳 caller | V1-V6 전수 HEAD 실증 정합 | 요구사항 lane ✓ |
| **10-A** | **MCT-186** | engine bithumb import "~5곳 5파일" 가설 | **정확 5곳 5파일 (V3 grep 전수)** = 정정 0 | **요구사항 lane V3 ✓** |
| **10-B** | **MCT-186** | `stream_consumer._latest_orderbook` 타입 = `OrderbookSnapshotEvent` (bithumb) 가설 | **V7 정정 발견**: `fill/simulated.py:60 orderbook: OrderbookSnapshotEvent` 파라미터 + `test_simulated_fill.py` `_OrderbookLevel` 직접 사용 → engine-local `OrderbookSnapshot` 신설 의무 + test 교체 의무 추가 | **요구사항 lane V7/V8 ✓ (Phase 0 cascade 정정 발견)** |

**PMO 판정**: docker-stack 6회 사후 발견 → 본 Epic MCT-182 2건 + MCT-183 3건 + MCT-184 1건
+ MCT-185 사전 차단 + MCT-186 2건 (V7/V8 cascade) = **10회째 사전 차단 누적**. R1 가드
패턴 + V-체크 박제 + **V7/V8 cascade 정정 (캐시 타입 / fill 엔진 파라미터 / test fixture
삼중 정정)** = MCT-186 의 특징적 산출물. 후속 Story (MCT-187/188) 동일 reapply **강제**.

### 패턴 #2 — §3.2.4b file-delete caller grep gap 신규 lesson (cross-file downstream impact 8회째 동형)

본 Story 의 핵심 신규 lesson — design iter1 P0 fix (§3.2.4b cli.py StreamExhaustedError) 의
일반화:

| # | Story | 동형 패턴 (cross-file downstream impact 누락) | 정정 mechanism |
|---|-------|--------------------------------------------|--------------|
| 1-6 | MCT-170/177/178/179/180 (docker-stack 6회) | cross-repo Phase 0 verify gap (sibling runtime 실상 미검증) | 후행 amendment |
| 7 | MCT-183 8-C | `reader_cache.py:339-348` lazy/conditional import grep gap (top-level grep only) | 요구사항 lane lazy import grep 의무 reapply |
| **8** | **MCT-186 §3.2.4b** | **cli.py StreamExhaustedError import + catch block ws_wrapper.py 삭제 연쇄 누락 (Change Plan 초안 §3.2 scope 정의 누락)** | **설계리뷰 iter1 P0 fix → Change Plan §3.2.4b 박제** |

**일반화 lesson**: 파일 삭제 의도 시 **양방향 grep 의무**:
- (a) `grep -rn "from <deleted_module>" src/ tests/` (import 발견)
- (b) `grep -rn "<deleted_symbol>" src/ tests/` (catch block / exception 사용 + 타입 어노테이션)

MCT-186 의 경우 (a) 만 수행 → `cli.py:442 from mctrader_engine.runtime.ws_wrapper import
StreamExhaustedError` 는 포착 / `cli.py:597 except StreamExhaustedError` 는 (b) 미수행으로 누락.

**PMO 판정**: 본 lesson = **§0 Phase 0 Verify Gate 의 고정 V-체크 slot 으로 박제 의무**
(MCT-187 reapply 후보). 양방향 grep 의무를 명문화하면 MCT-188 D7 quad gate `pyproject.toml`
`mctrader-market-bithumb` 의존 line 제거 시점에도 동형 패턴 사전 차단 가능 (engine 외 sibling
repo signal-collector / data / market-core 의 import 잔존 grep 의무).

### 패턴 #3 — ADR-032 evidence triad 2회 연속 선제 reapply (cross-Story 추세 확립)

MCT-184 dead-in-data 박제 + MCT-185 cold-read cutover 11-place evidence triad → **MCT-186
exchange-adapter 제거 evidence triad = 2회 연속 선제 reapply**:

| Story | evidence triad 적용 영역 | file:line | caller grep | integration test |
|-------|------------------------|----------|------------|---------------|
| MCT-184 | dead-in-data 박제 (production caller 0 + consumer=MCT-185) | routes_v1.py:191-196 + 244-247 | TC-9 production caller 0 evidence | TC-1~11 21 test PASS |
| MCT-185 | cold-read cutover 11-place + reverse-write 3-place | cli.py×2 + tick_replay.py×2 + wfo/evaluator×2 + wfo/search×2 + paper_runner.py×2 + nas_sync.py×1 | engine src/ `from mctrader_data.(storage\|path\|...)` grep0 PASS | (cross-repo integration) |
| **MCT-186** | engine exchange-adapter 제거 (5곳 5파일 + RedisStreamSubscriber) | **redis_subscriber.py:93-173 + paper_runner.py:265-274** | **engine src/ `from mctrader_market_bithumb` grep = 0건 PASS** | **tests/test_realtime_subscriber.py 4 testcontainers[redis] integration test ALL PASS** |

**PMO 판정**: ADR-032 evidence triad **3회 연속 누적 적용** (MCT-184/185/186) = **추세
확립** (MCT-189 wiring drift 동형 패턴 사전 차단 invariant). 후속 Story (MCT-187 invariant
test + MCT-188 D7 quad gate CI) 동형 reapply 의무.

### 패턴 #4 — design lane shift-left ROI 회수 재증명 (Epic 트렌드 갱신)

PMO-AUDIT-MCT-184 §3 패턴 #5 baseline 갱신:

| Story | design lane FIX P0 (pre-LAND) | code lane FIX P0 (pre-LAND) | 비고 |
|-------|------------------------------|---------------------------|------|
| MCT-179 (docker-stack) | 1회 (1 iter) | 0회 | Out-of-scope D1-D19 전수 reconcile (c8e4b8e) — 선제 reapply baseline |
| MCT-180/181 (docker-stack) | 0회 | code-only FIX | MCT-179 reconcile 회수 |
| MCT-182 (data-domain Epic entry) | 1회 (P0×2) | 0회 | D1-D7 전수 reconcile — 선제 reapply |
| MCT-183 | 3→2→2 (max 3/3 + RESET) | 0회 | cross-document SSOT carry 5회 누적 — 부담 증가 |
| MCT-184 | **0회 (FIX 0회)** | BYPASS (dead-in-data) | §3.6.1 gate v2 cross-Story reapply 실효 |
| MCT-185 | **0회 (FIX 0회)** | 0회 | 박제 PR 5 체크리스트 첫 적용 |
| **MCT-186** | **1회 (§3.2.4b P0 — design shift-left filter 정상 작동)** | **0회 (code FIX 0회)** | **design lane shift-left ROI 재증명 2회 연속 (MCT-184 + MCT-186)** |

**판정**: MCT-179 lesson reapply (Epic 시점 D-row 전수 reconcile) + MCT-183 RESET path
(§3.6.1 gate v2 박제) 의 **2단계 forcing function 투자** 의 회수가 MCT-184 + MCT-186 =
**code FIX 0회 2회 연속 달성**. MCT-186 design iter1 P0×1 = shift-left filter 의 정상
작동 (post-LAND silent ImportError 차단) — health 한 indicator. **후속 Story (MCT-187/188)
도 design lane FIX P0×2 이상 누적 시 ESCALATE trigger** monitoring 의무.

### 패턴 #5 — Codex post-LAND audit sentry 추세 (MCT-184 3회 연속 → MCT-186 발견 0 변화)

MCT-184 PMO-AUDIT §3 패턴 #4 baseline:
- MCT-182 cold path 동형 (data#69 fix1 carry) = 1회
- MCT-183 lint-revert 동형 (`6450cfd` post-merge) = 2회
- MCT-184 F-1~F-4 post-LAND audit 4건 (P0×3 + P1×1) = **3회**

**MCT-185/186 추세**:
- MCT-185 post-LAND audit finding = 0건
- **MCT-186 post-LAND audit finding = 0건**

**판정**: Codex post-LAND audit sentry 3회 연속 누적 후 2회 연속 발견 0 — **추세 변화**.
가능한 해석 2가지:
- (a) MCT-184 self-discipline reapply (Codex post-LAND audit 4 axis 의무 운용 — pre-LAND
  단계에서 production correctness + bytes-level 정밀도 + SSOT 재검증 자체 적용) 효과
- (b) Story scope 차이 (MCT-185 cold-read cutover + MCT-186 exchange-adapter 제거 = 산술
  연산이 적어 silent corruption surface 자체가 작음 — MCT-184 routes_v1 ts_utc/sha256
  영역과 비교 시)

**plugin-codeforge#805 (post-merge audit lane 신설, 후보 3) ADR escalation 의 evidence
row 갱신** = 발견 추세가 (a)/(b) 어느 쪽인지 분리 의무 (MCT-187/188 post-LAND audit
finding ≥ 1건 발생 시 priority 가속, 0건 유지 시 (a) self-discipline 효과 가설 강화).

## 4. codeforge upstream ADR escalation evidence row 갱신

본 Story 의 evidence 가 사전 PMO-AUDIT-MCT-184 §4 발의된 3건 escalation 의 누적 정량
근거 갱신 영역:

### 4.1 plugin-codeforge#795 (cross-document SSOT mechanical gate, 후보 1)

| 영역 | MCT-184 baseline | **MCT-186 갱신** |
|------|------------------|------------------|
| pre-LAND gate v2 cross-Story reapply 누적 | 1회 사전 차단 (MCT-184) | **3회 누적** (MCT-184 + MCT-185 + MCT-186) |
| 사전 차단 수단 | §3.6.1 gate v2 (MCT-183 RESET path 박제) | + MCT-186 V7/V8 cascade 정정 (R1 가드 + §0 Phase 0 V-체크) |

**판정**: #795 ADR escalation 의 evidence row **3회 누적 사전 차단** = mechanical gate
화 정량 회수 가능성 입증 (consumer self-discipline 만으로 cross-Story 3회 효과 = upstream
plugin 가용 시 안전 마진 증대 효과 정량 baseline).

### 4.2 plugin-codeforge#804 (박제 PR 자체 완결도 mechanical gate, 후보 2)

| 영역 | MCT-184 baseline | **MCT-186 갱신** |
|------|------------------|------------------|
| 박제 PR 5 체크리스트 self-discipline reapply | (MCT-184 발견 = trigger) | **MCT-186 hub#371 5/5 PASS** (RETRO + EPIC-RESULTS §Story-5 + frontmatter COMPLETED + completed_at + CLAUDE.md hub#TBD 0줄 + ADR amendment confirm) |
| SSOT drift 3호 동형 재발 | (MCT-184 발생) | **재발 0 (사전 차단 1회 실증)** |

**판정**: #804 ADR escalation 의 evidence row 갱신 = **consumer self-discipline 만으로
2회 연속 (MCT-185 + MCT-186) SSOT drift 3호 동형 재발 0 달성** = mechanical gate plugin
가용 시 추가 회수 effect = false negative 차단 (operator 실수 fallback). 다만 self-
discipline 가능성 입증 = mechanical gate priority 변경 평가 필요 (HIGH 유지 vs MEDIUM 강등).

### 4.3 plugin-codeforge#805 (post-merge audit lane 신설, 후보 3)

| 영역 | MCT-184 baseline | **MCT-186 갱신** |
|------|------------------|------------------|
| Codex post-LAND audit finding 연속 추세 | 3회 누적 P0/P1 발견 (MCT-182/183/184) | **2회 연속 발견 0 (MCT-185/186) — 추세 변화** |

**판정**: #805 ADR escalation 의 evidence row 갱신 = 발견 추세 변화 = **priority HIGH
재평가 의무** (3회 연속 + 추가 후속 0 / 발견 추세 분리 필요). MCT-187/188 post-LAND finding
≥ 1건 발생 시 priority 가속, 0건 유지 시 (a) self-discipline 효과 가설 강화 + priority 강등.

## 5. carry-over registry (post-Story)

RETRO-MCT-186 §7 carry over 2건 + Story §12 carry over 3건 + 본 PMO 감사 추가 1건 =
**통합 carry registry**:

| # | 항목 | severity | owner | 출처 |
|---|------|----------|-------|------|
| 1 | `compose.yml` engine `paper-engine`/`backtest-runner` service `NAS_MINIO_*` env 행 제거 | non-blocking | MCT-187 or 별 hub PR | RETRO §7 + Story §12 |
| 2 | `pyproject.toml` `mctrader-market-bithumb` git dependency line 제거 (D7 quad gate final) | non-blocking | MCT-188 owner | RETRO §7 + Story §12 |
| 3 | ADR-030 compose.yml engine NAS cred drop amendment box → VERIFIED 전환 | doc-only | carry over 1번 LAND 후 | Story §12 |
| 4 | **§3.2.4b file-delete caller grep gap lesson 을 §0 Phase 0 Verify Gate 고정 V-체크 slot 으로 박제** (양방향 grep: import + symbol 사용) | **process (신규 lesson)** | **MCT-187 reapply 첫 적용** | **본 audit §3 패턴 #2** |

## 6. 다음 Story 진입 권고 (MCT-187)

### 6.1 진입 prerequisite

| # | 항목 | 상태 |
|---|------|------|
| 1 | MCT-186 박제 hub PR #371 (cab600b) LAND | ✅ 충족 (2026-05-16T22:07:13Z) |
| 2 | ADR-031 §D4 VERIFIED + ADR-030 NAS cred drop amendment box LAND | ✅ 충족 (실 compose wiring = MCT-187 carry) |
| 3 | scope_manifest milestone 5/7 + epic_status_history 5 row | ✅ 충족 |
| 4 | RETRO-MCT-186 + EPIC-RESULTS §Story-5 박제 | ✅ 충족 (hub PR #371 LAND 시 동반) |
| 5 | Story §12 PMOAgent 회고 4-field schema 박제 | ✅ 충족 (본 retro 작업) |
| 6 | 본 PMO 감사 (PMO-AUDIT-MCT-186) | ✅ 충족 (본 작업 산출물) |
| 7 | R2 (MCT-41) 활성 branch 재 cross-check (engine repo `git branch -a` MCT-43~47/live 키워드 0건) | **MCT-187 진입 직전 재실행 의무** |

전수 충족 (7번 = MCT-187 진입 직전 재실행 의무). MCT-187 진입 가능.

### 6.2 MCT-187 진입 권고 (MCT-182~186 lesson 누적 reapply 의무 — 7 항목)

**MCT-187** (sequential_phase 6, milestone **6/7**) — 다중거래소 확장 불변식 박제
(D5 invariant test + D6 runbook add-new-exchange.md). cross_repo: hub + (선택적 engine
+ market-core).

**필수 reapply 항목 — 7 항목** (MCT-182~186 lesson 누적):

| # | 항목 | 출처 | 본 Story 강조 |
|---|------|------|--------------|
| 1 | R1 가드 + §0 Phase 0 Verify Gate (V-체크) | MCT-182~186 lesson | MCT-186 carry over (compose.yml NAS env drop + pyproject.toml dep) 실 LAND 시점의 sibling repo 영향 deep-verify (signal-collector / data / market-core import grep 의무) |
| 2 | **§3.2.4b 양방향 grep 의무 (import + symbol 사용)** | **본 audit 신규 lesson** | **pyproject.toml `mctrader-market-bithumb` dep 제거 시 (MCT-188 carry) cross-repo 양방향 grep 의무 사전 reapply** — MCT-186 발견 cross-file downstream impact 패턴 cross-repo 일반화 |
| 3 | cross-document SSOT forcing function self-discipline (§3.6.1 gate v2 cross-Story reapply) | PMO-AUDIT-MCT-184 §4 | mechanical gate (plugin-codeforge#795) 미가용 전 까지 self-discipline 유지 |
| 4 | 박제 PR 5 체크리스트 self-discipline (mechanical gate plugin-codeforge#804 미가용 전) | MCT-184 §4 + 본 audit §2.5 | MCT-185 + MCT-186 = 2회 연속 5/5 PASS 추세 유지 |
| 5 | post-merge audit lane self-discipline (mechanical lane plugin-codeforge#805 미가용 전) | MCT-184 §4 + 본 audit §3 패턴 #5 | MCT-185 + MCT-186 = 2회 연속 발견 0 추세 — MCT-187 post-LAND finding ≥ 1건 발생 시 priority 가속 monitoring |
| 6 | ADR-032 evidence triad reapply | MCT-184/185/186 (3회 연속 누적) | D5 invariant test 산출물에 적용 (file:line + caller grep + integration test) |
| 7 | R2 (MCT-41) 활성 branch 재 cross-check (engine#N 진입 직전) | MCT-186 INV-6 | engine repo `git branch -a` MCT-43~47/live 키워드 0건 확인 후 진입 |

### 6.3 R2 (MCT-41 블락) 영향 평가

MCT-187 = 다중거래소 확장 불변식 박제 (D5 invariant test + D6 runbook) → engine 측
cross-cutting 가능성. **MCT-187 진입 전 MCT-43~47 IN_PROGRESS 파일 교차 검증 의무**
(scope_manifest §dependency.parallel_safe_with 재평가 + R2 ZERO RISK effective verify,
Orchestrator ordering 결정 책임). MCT-186 INV-6 PASS 시점 (engine#60 LAND 직전) MCT-43~47
branch/commit = 0건 확인 후 LAND — MCT-187 진입 시점 재 cross-check 의무 유지.

## 7. Epic 진행 트렌드 baseline 갱신 (후속 PMO 감사 reference)

PMO-AUDIT-MCT-184 §7 baseline 갱신:

| 항목 | MCT-182 | MCT-183 | MCT-184 | **MCT-185** | **MCT-186** | 트렌드 |
|------|---------|---------|---------|-------------|-------------|--------|
| 설계리뷰 FIX P0 (pre-LAND) | 1회 | 3→2→2 (max 3/3 + RESET) | 0회 | 0회 | **1회 (§3.2.4b — design shift-left filter 정상)** | (design shift-left filter 정상 작동 1회) |
| 구현리뷰 FIX P0 (pre-LAND) | 0회 (P1×2) | 0회 | BYPASS (dead-in-data) | 0회 | **0회 (FIX 0회)** | ↓ (code lane FIX 0회 2회 연속) |
| iter 1 (post-LAND Codex audit) | 0회 | 0회 | 4건 (P0×3 + P1×1) | 0회 | **0회** | (3회 연속 후 2회 연속 발견 0) |
| ESCALATE | 0회 | 0회 (RESET path 1회) | 0회 | 0회 | **0회** | — |
| Phase 0 verify gap | 0회 (사전 차단 2건) | 0회 (사전 차단 3건) | 0회 (사전 차단 1건) | 0회 | **0회 (사전 차단 2건 — V7/V8 cascade)** | (사전 차단 누적 **10회**) |
| 신규 test | 72 | 8 | 21 + 2 skipped | (cross-repo) | **4 testcontainers** | (Story scope 차이) |
| ADR 산출물 | 1 신규 (ADR-031 Proposed→Accepted) | amendment box 2 (ADR-027/029) + §D2 partial | §D3 partial VERIFIED + ADR-030 amend box | §D2 + §D3 VERIFIED + ADR-029 §D2 VERIFIED | **§D4 VERIFIED + ADR-030 NAS cred drop amend box** | (D-row 진행 5/7 누적) |
| cross-repo PR | 7 | 6 | 4 (single-repo data) | (3 PR: data + engine + hub×2) | **3 PR (hub + engine + hub)** | (Story scope 차이) |
| land_order 위반 | 0회 | 0회 | 0회 | 0회 | **0회** | — |
| cross-document SSOT desync (Story-내) | 1회 | 4회 (iter1+iter2+iter3) | 0회 (사전 차단) | 0회 | **0회** | ↓↓ (gate v2 cross-Story reapply 회수 3회 누적) |
| **SSOT drift cross-Story layer** | 0 | 0 | 3호 신규 | 0 (5/5 PASS) | **0 (5/5 PASS)** | (self-discipline 효과 2회 연속) |
| RESET path 발동 | 0회 | 1회 정상 발동 | 0회 | 0회 | **0회** | — |
| forcing function gate 영구 박제 | 0회 | 1회 (§3.6.1 gate v2) | 1회 reapply 실효 | reapply 실효 2회 | **reapply 실효 3회 + §3.2.4b 신규 박제 후보** | (Story 별 비용 → cross-Story 회수 누적) |
| Codex post-LAND audit sentry | 1회 (data#69 fix1) | 1회 (lint-revert) | 1회 (F-1~F-4) | 0회 | **0회** | (3회 연속 → 2회 연속 발견 0 추세 변화) |

**후속 Story 모니터링 KPI 갱신**:

1. **design lane FIX P0 누적 추이 (pre-LAND)** = mechanical gate plugin 가용 전 self-
   discipline 효과 측정 KPI. MCT-186 P0×1 (§3.2.4b — shift-left filter 정상). P0×2
   이상 누적 발생 시 ESCALATE trigger (MCT-187/188 monitoring)

2. **post-LAND iter 1 Codex audit finding 추이** = post-merge audit lane 의무 lane 화
   timeline. MCT-185 + MCT-186 = 2회 연속 발견 0 = **#805 priority 재평가 의무** (MCT-187/188
   post-LAND finding ≥ 1건 시 priority 가속)

3. **Phase 0 verify gap 누적 0 유지** = R1 가드 ROI 회수 핵심 KPI. MCT-186 = **10회 누적
   사전 차단 유지** (V7/V8 cascade 정정 신규 추가)

4. **SSOT drift cross-Story layer 추이** = mechanical gate #804 의무 lane 화 timeline.
   MCT-185 + MCT-186 = 2회 연속 5/5 PASS = **self-discipline 효과 추세 유지** (4호 발생 시
   priority 가속)

5. **§3.2.4b 양방향 grep 의무 reapply 추이** = MCT-186 신규 lesson 의 효과 측정 KPI.
   MCT-187 Phase 0 V-체크 적용 + MCT-188 D7 quad gate (pyproject 의존 line 제거 시점) 적용
   = 2 Story reapply 효과 누적 평가

## 8. 종합 판정

| 항목 | 결과 |
|------|------|
| 게이트 준수 | **pre-LAND 6 lane 전수 PASS** (요구사항 + 설계 CONDITIONAL_PASS→PASS + 설계리뷰 P0×1 정상 shift-left filter + 구현 PASS + 구현리뷰 FIX 0회 + 통합/보안 SKIP 정상) + §10 fix-event-v1 1 row 정합 + §11 LAND 3 행 정합 + D-row D4 VERIFIED 정합 |
| 박제 PR 5 체크리스트 cross-Story reapply | **5/5 PASS = MCT-184 SSOT drift 3호 동형 재발 0** (2회 연속 실증 — MCT-185 + MCT-186, self-discipline 효과 검증) |
| design lane shift-left ROI 회수 재증명 | **code lane FIX 0회 2회 연속 달성** (MCT-184 + MCT-186) — MCT-179 lesson reapply 효과 누적 |
| ADR-032 evidence triad 선제 reapply | **3회 연속 누적 적용** (MCT-184/185/186) — 추세 확립 (MCT-189 wiring drift 동형 사전 차단 invariant) |
| cross-Story 패턴 | **5건 박제** (R1 가드 효과 10회째 / §3.2.4b file-delete caller grep gap 신규 lesson / ADR-032 evidence triad 3회 연속 / design shift-left ROI 회수 2회 연속 / Codex post-LAND audit 추세 변화) |
| codeforge upstream ADR escalation evidence | **#795 (cross-document SSOT mechanical gate) 3회 누적 사전 차단** + **#804 (박제 PR 자체 완결도) 2회 연속 5/5 PASS 추세** + **#805 (post-merge audit lane) 추세 변화 priority 재평가 의무** |
| Phase 0 verify gap | **10회 누적 사전 차단 유지** (MCT-186 V7/V8 cascade 정정 신규 2건) |
| carry-over | **4건 registry** (compose.yml NAS env drop + pyproject dep 제거 + ADR-030 VERIFIED 전환 + §3.2.4b 양방향 grep 의무 lesson 박제) |
| 다음 Story | **MCT-187 진입 가능** — R1 가드 패턴 reapply 7 항목 (6 누적 + 본 audit 신규 1 §3.2.4b 양방향 grep 의무) |

**PMO 결론**:

MCT-186 = **engine = exchange-agnostic pure consumer 전환 완결 + ADR-031 §D4 VERIFIED**
(evidence triad: file:line + grep0 + testcontainers integration test) + **박제 PR 5
체크리스트 cross-Story reapply 5/5 PASS 2회 연속 실증** (SSOT drift 3호 동형 재발 0) +
**design lane shift-left ROI 회수 재증명 2회 연속** (code FIX 0회 달성) + **ADR-032
evidence triad 3회 연속 누적 적용 = 추세 확립** + **§3.2.4b file-delete caller grep gap
신규 lesson 박제** (cross-file downstream impact 8회째 동형 정정 mechanism 일반화).

**가장 중요한 산출물 = §3.2.4b 양방향 grep 의무 lesson 박제** — 파일 삭제 의도 시 (a)
import grep + (b) symbol 사용 grep 양방향 의무. MCT-188 D7 quad gate (`pyproject.toml`
`mctrader-market-bithumb` dep 제거) 시점에 cross-repo 일반화 reapply 의무 (engine 외
signal-collector / data / market-core 의 import 잔존 grep 의무).

**Codex post-LAND audit sentry 추세 변화** (3회 연속 발견 → 2회 연속 발견 0) = **#805
ADR escalation priority 재평가 의무** (MCT-187/188 post-LAND finding ≥ 1건 발생 시
priority 가속, 0건 유지 시 self-discipline 효과 가설 강화).

**다음 Story MCT-187 진입 권고**: R1 가드 + §0 Phase 0 Verify Gate (양방향 grep V-체크
slot 신규 박제) + cross-document SSOT self-discipline (§3.6.1 gate v2 cross-Story reapply)
+ 박제 PR 5 체크리스트 self-discipline (3회 연속 PASS 추세 유지) + post-merge audit lane
self-discipline (3회 연속 발견 0 추세 유지 monitoring) + ADR-032 evidence triad reapply
(D5 invariant test 산출물 적용) + R2 (MCT-41) 활성 branch 재 cross-check **7 항목 의무**.
