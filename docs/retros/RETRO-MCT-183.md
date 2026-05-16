# RETRO MCT-183 — Layer 2 read 도메인 relocation → mctrader-data

> **EPIC-data-domain-decoupling sequential_phase 2 (milestone 2/7)** · COMPLETED 2026-05-16
> 6 PR cross-repo LAND (hub#353+data#70+engine#58+hub#354+data 6450cfd lint-revert+hub Phase2 PR2)

## 1. 결과 요약

| 항목 | 결과 |
|------|------|
| AC | **5/5 PASS** (io/ data 이전 + tests green + engine 삭제 + src caller 0 dead-in-prod safe removal + ADR amendment box D-row 1:1) |
| INV | **6/6 PASS** (byte-equiv / Layer2 자족 / src caller 0 영구 / tests green / 동작 무변경 / **INV-6 compactor Protocol 무변경 — V6 동명 risk 해소**) |
| 신규 test | **8** (test_io_stats_no_engine_dep + tests/io/ 7 이전) ALL PASS |
| 회귀 | data 1020 / engine 879 신규 실패 0 |
| FIX 루프 | 설계리뷰 iter1→2→3 P0×3→×2 **max 3/3** → RESET path → post-RESET PASS / 구현리뷰 iter1 **PASS FIX 0회** |
| Codex pre-LAND audit | INV-1 lint auto-fix 사전 발견 → post-merge `6450cfd` 정정 (구현-리뷰 FIX 진입 사전 흡수, MCT-182 cold path 동형) |

## 2. R1 가드 + Phase 0 verify 정정

| # | 발견 | 시점 | 영향 |
|---|------|------|------|
| **A** | engine src/ io/ 호출자 0 (dead-in-prod) HEAD 재검증 — grep 분리 검증으로 사전 차단 | 요구사항 lane | MCT-182 V5 류 사후 정정 불요 |
| **B** | V6 동명 risk — data `compactor/reader_cache.py:19` `class ReaderCache(Protocol)` 동명 기존 | 요구사항 lane | INV-6 신설 + namespace `mctrader_data.io.*` 분리 확정 |
| **C** | R1 7회째 사전 차단 — `reader_cache.py:339-348` stats() lazy `from mctrader_engine.metrics import ...` (V5 top-level grep 미포착) | 설계 lane (CodebaseMapper) | Layer2 자족 INV-2 위반/순환 위험 → 채택안 A internal no-op 사전 정정. docker-stack 6회 사후 발견 대비 shift-left 성과 |

## 3. FIX 루프 — cross-document SSOT desync 5회 누적 + 수동 forcing function 한계 실증

### 3.1 설계리뷰 iter1→2→3 (max 3/3) → RESET path → post-RESET PASS

| iter | finding | 정정 |
|------|---------|------|
| 1 | P0-1 ADR-027 amendment 2-module ↔ 6-module desync(MCT-179/182 동형) + P0-2 Story SSOT 역전파 누락 + P0-3 §3.5 graceful no-op 구현 불가 명세(MCT-180 동형) + P1-1 byte-equiv source pin 부재 | ArchitectPL 회귀: 4 산출물 reconcile + Story 역전파 + 채택안 A 확정 + V-pin gate |
| 2 | P0-1-residual: 핵심 4산출물 정정 ✓ but 연계 권위 4곳 잔존 | ArchitectPL 회귀: ADR-027 amendment 6곳 canonical 통일 + §3.6.1 grep gate v1 박제 |
| 3 (max) | P0-1-residual-2 ADR-031:139 누락 + **P0-2-gate §3.6.1 gate 자체 결함**(scope ADR-031 미cover + pattern 변형 미매치 NO MATCH) | fix-ledger-schema 3 trigger 0 → **Orchestrator RESET path 채택** |
| RESET 수렴 | 지정목록 방식 탈피 — ADR-031:139 + **sibling MCT-182:28/235** canonical (6산출물+sibling) + **§3.6.1 gate v2 = glob-scope + 변형포괄 pattern + self-verify TEST1/TEST2** + repo-wide grep 0줄 evidence | Orchestrator 독립 verify PASS (DesignReviewPL rate-limit 대신 git/grep 직접) |

### 3.2 구현리뷰 iter1 = PASS FIX 0회 (MCT-182 lesson reapply 효과 검증)

§3.6.1 gate v2가 post-LAND repo-wide grep 0줄을 박제 → 구현-리뷰 carry 사전 차단. MCT-182 동형 "설계 self-contradiction → 구현-리뷰 FIX" 패턴 0건 실증. forcing function 영구 박제 효과.

## 4. lesson 누적 (cross-Story 트렌드) + ADR escalation 결정

### 4.1 cross-document SSOT desync **5회 누적**

| # | Story | finding |
|---|-------|---------|
| 1 | MCT-179 | ADR-030 D5/D8 swap stale (Out-of-scope 표 정의 swap) |
| 2 | MCT-182 | Change Plan §4.2("하위모듈 삭제") ↔ §6/§2.2("무중단 보존") self-contradiction |
| 3 | MCT-183 iter1 | ADR-027 amendment 2-module ↔ 6-module 핵심 4산출물 desync |
| 4 | MCT-183 iter2 | iter1 정정 후 연계 권위 4곳 2-module 축약 carry |
| 5 | MCT-183 iter3 | iter2 §3.6.1 gate 자체 결함 + ADR-031:139 reconcile scope 누락 |

### 4.2 수동 reconcile + 수동 gate 한계 = **codeforge upstream ADR escalation 결정 발의**

- iter3 P0-2-gate = ArchitectPL이 박제한 §3.6.1 gate v1 자체가 불완전 (scope 5산출물만 / pattern 조사·따옴표 고정으로 변형 미매치 NO MATCH)
- 수동 "지정 목록" 방식이 매 iter 1개 누락 발견 패턴 5회 → **구조적 한계 실증**
- RESET 후 gate v2 (glob-scope + 변형포괄 regex + self-verify TEST1/TEST2 + repo-wide grep) 박제 → 구현-리뷰 carry 사전 차단 효과 검증
- **결론**: cross-document SSOT 정합 forcing function = Story별 수동 박제로 한계 명백 → **codeforge plugin design lane SSOT reconcile mechanical gate (glob-scope + 변형포괄 regex + self-verify) 일반화 = codeforge upstream ADR escalation 후보 결정 발의 의무**. PMO-AUDIT-MCT-182 §4 (Option A self-discipline 형태) 의 mechanical gate 형태 정합 — Story별 수동 박제 한계 5회 누적 실증으로 강화

### 4.3 byte-equivalence + V-pin source = relocation Story 안전 invariant 일반화 검증

- MCT-182(contract relocate) + MCT-183(read 도메인 relocate) 2회 모두 byte-equivalence 보존 → 회귀 0
- V-pin engine origin/main hash 박제 = engine#N 삭제 후 비교 source 영구 재현 가능 (MCT-182 source pin 부재 lesson reapply 효과)
- relocation Story 패턴의 안전 invariant 화 권고 (MCT-185/MCT-186 reapply)

### 4.4 Codex pre-LAND audit → post-merge fix 흡수 패턴 (MCT-182 동형 2회째)

- data#70 LAND 후 lint auto-fix 가 INV-1 byte-equivalence 위반 → Codex pre-LAND audit 사전 발견 → post-merge `6450cfd` 정정 흡수
- MCT-182 cold path 동형 (구현-리뷰 FIX 진입 사전 차단)
- Codex 독립 peer 의 넓은 검증 scope 가 sentry 역할 → R1 가드 보강 (3회 연속 실증)

## 5. carry over (post-Story)

| # | 항목 | severity | owner |
|---|------|----------|-------|
| 1 | data tests/io/test_reader_cache_flush.py:215+221 skipped test 본문 mctrader_engine.metrics import 잔존 (Change Plan §8.2 정합 + @pytest.mark.skip, 실행 0) | non-blocking | MCT-185 (Gauge 재배선 cutover 시 정리) |
| 2 | reader_cache.py stats() Gauge 실 emit 재배선 (data 측 동등 Gauge 신설 + producer wiring) | scope 외 | MCT-185 cold-read cutover |
| 3 | engine `mctrader_engine.metrics.set_reader_cache_hit_ratio`/`set_reader_p99_ms` setter 고아화 (engine io/ 삭제 후 caller 0) | non-blocking dead code | MCT-185/188 |
| 4 | engine NAS 직독 폐기 실 amend confirm (ADR-029 §D2) | scope 외 | MCT-185 cold-read REST cutover |
| 5 | data io/ production wiring (dead-in-data → live) | scope 외 | MCT-185 |
| 6 | data-free grep0 quad gate CI + ADR-029/027 본문 결정 무변경 → 실 amend confirm | scope 외 | MCT-188 POLICY_FINALIZED |
| 7 | **codeforge upstream ADR escalation 발의** (cross-document SSOT mechanical gate plugin-level) | HIGH 누적 | PMO-AUDIT-MCT-183 + codeforge marketplace issue 발의 |

## 6. 다음 Story 진입

**MCT-184** (sequential_phase 3) — Layer 2 data REST API 신규 (FastAPI /v1 historical Arrow IPC + reverse-write POST). MCT-183 LAND prerequisite 충족 (io/ data 측 수령 완료, REST wrap 대상 확정).

진입 권고: **R1 가드 패턴 reapply** (MCT-182/183 SSOT 정합 forcing function self-discipline + §3.6.1 gate v2 cross-Story 활용 + Codex pre-LAND audit 활용). ADR escalation 결과(MCT-183 PMO-AUDIT 박제) 차후 Story Phase 0 입력 의무 (mechanical gate 가용 시 활용).
