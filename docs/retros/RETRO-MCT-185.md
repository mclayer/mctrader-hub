# RETRO MCT-185 — data realtime stream + engine thin client + cold-read/reverse-write 11-place cutover

> **EPIC-data-domain-decoupling sequential_phase 4 (milestone 4/7)** · COMPLETED 2026-05-17
> 3 PR cross-repo LAND (hub#366 Phase 1 + data#76 land_order 1 + engine#59 land_order 2 + hub Phase 2 PR2 박제)
> · **가장 복잡 Story** (3 repo + production wiring 전환, ADR-032 evidence triad 선제 reapply 효력 1회 실증)
> · **FIX 0회** — DesignReview PASS FIX 0회 + code lane blocking 0 양 PR (data#76 + engine#59)

## 1. 결과 요약

| 항목 | 결과 |
|------|------|
| AC | **6/6 PASS** (AC-1 realtime SSE stream / AC-2 engine data_client HTTP / AC-3 engine src/ grep0 VERIFIED / AC-4 historical+reverse-write 11-place cutover / AC-5 CodeQL CWE-22 fix / AC-6 ADR-032 evidence triad) |
| INV | **7/7 PASS** (INV-1 engine mctrader_data 0 / INV-2 realtime schema tick.v1.1 정합 / INV-3 cold-read REST idempotent / INV-4 reverse-write sidecar SSOT / INV-5 CodeQL CWE-22 boundary / INV-6 data 회귀 0 + engine 회귀 0 / INV-7 ADR-032 evidence triad 동반) |
| AC-3 grep0 | **engine src/ 0건** — `from mctrader_data.(storage|path|orderbook_replay|paper_storage|nas_storage)` grep 결과 0 (engine#59 LAND 후 confirm) |
| 11-place cutover | cold-read 8곳 (cli.py×2, tick_replay.py×2, wfo/evaluator×2, wfo/search×2) + reverse-write 3곳 (paper_runner.py×2, nas_sync.py×1) |
| 신규 파일 | data: `realtime_stream.py` + `/v1/historical/{symbol}` OrderBook endpoint (1 파일 확장) · engine: `data_client/__init__.py` + `data_client/client.py` + `data_client/stream.py` (3 파일 신규) |
| FIX 루프 | **FIX 0회** — DesignReview PASS (blocking 0) + code data#76 PASS + code engine#59 PASS |
| ADR amendment | ADR-029 §D2 VERIFIED + ADR-031 §D2+§D3 VERIFIED (Phase 1 draft → Phase 2 PR2 VERIFIED) |
| Epic milestone | **4/7** (MCT-182 + MCT-183 + MCT-184 + MCT-185 COMPLETED) |

## 2. Phase 0 verify + ADR-032 evidence triad 선제 reapply

| # | 발견 | 시점 | 영향 |
|---|------|------|------|
| **A** | Phase 0 verify gate — engine `data_client/` 호출자 grep 0건 사전 확인 (MCT-184 dead-in-data → MCT-185 production wiring 전환 확인) | 요구사항 lane | AC-3 grep0 gate 박제 (engine#59 LAND 후 confirm) |
| **B** | ADR-032 evidence triad 선제 reapply — MCT-184 §3.6.1 gate v2 + dead-in-data 박제 패턴을 MCT-185 cutover 전 invariant 체크리스트에 통합 | 설계 lane | INV-7 evidence triad 동반 박제 — MCT-186 wiring drift 사전 차단 |
| **C** | CodeQL CWE-22 발견 — data api/ `_assert_within_root` path traversal boundary 미검증 (`os.path.abspath` 방식, GHSA 취약점) | 요구사항 lane (security scan) | AC-5 CodeQL fix = `relative_to()` boundary check LAND (data#76) |
| **D** | engine io/ 6 module (MCT-183 LAND) + cold-read 8곳 + reverse-write 3곳 cutover scope 검증 — `mctrader_data.storage` direct import 11곳 grep 실측 | Phase 0 verify (요구사항 lane) | 11-place cutover 범위 확정 (가설 오차 0) |

## 3. FIX 루프 — DesignReview PASS FIX 0회 + code lane PASS FIX 0회

### 3.1 설계리뷰 iter 1 PASS (cross-document SSOT 7회째 사전 차단)

- cross-document SSOT §3.6.1 gate v2 self-verify TEST1/TEST2 실증 (7회째 연속 사전 차단)
- D-row↔scope_manifest byte 1:1 정합 (ADR-031 §D2+§D3 draft 내용 scope_manifest 정합)
- ADR-032 evidence triad self-check (MCT-184 wiring drift invariant → MCT-185 production caller 연결 체크리스트)
- gate: `gate:design-review-pass` ✅ → phase:구현

### 3.2 code lane data#76 iter 1 PASS

- realtime_stream.py Redis XADD publisher + SSE endpoint LAND
- OrderBook endpoint 신규 LAND
- CodeQL CWE-22 `_assert_within_root` fix LAND (relative_to boundary)
- blocking 0 — P0/P1/P2 = 0/0/0

### 3.3 code lane engine#59 iter 1 PASS

- `data_client/__init__.py` + `client.py` + `stream.py` 신규 LAND
- cold-read 8곳 + reverse-write 3곳 REST 경유 cutover LAND
- AC-3 grep0 confirm (engine src/ mctrader_data.* = 0건)
- blocking 0 — P0/P1/P2 = 0/0/0

## 4. lesson 누적 (cross-Story 트렌드)

### 4.1 ADR-032 evidence triad 선제 reapply 효력 1회 실증

MCT-184 post-LAND Codex audit 발견 (박제 PR 자체 incomplete 패턴, SSOT drift 3호) + dead-in-data 박제 패턴 → MCT-185 에서 production wiring 전환 시 선제 reapply:

- pre-LAND 설계 단계: cutover scope grep 실측 (11곳 가설 오차 0) → Phase 0 verify 신뢰성 누적
- code lane: FIX 0회 달성 (ADR-032 evidence triad self-check 효과 + MCT-184 Codex audit lesson reapply)
- post-LAND: 박제 PR 5 체크리스트 전수 이행 (RETRO 존재 + EPIC-RESULTS §Story-4 + Story frontmatter status=COMPLETED + CLAUDE.md hub#TBD 0줄 + ADR amendment confirm 5/5)

### 4.2 cross-document SSOT 사전 차단 7회째 누적

| # | Story | finding | 시점 |
|---|-------|---------|------|
| 1 | MCT-179 | ADR-030 D5/D8 swap stale | pre-LAND |
| 2 | MCT-182 | Change Plan §4.2 self-contradiction | pre-LAND |
| 3 | MCT-183 iter1 | ADR-027 2-module ↔ 6-module desync | pre-LAND |
| 4 | MCT-183 iter2 | iter1 정정 후 연계 권위 4곳 carry | pre-LAND |
| 5 | MCT-183 iter3 | §3.6.1 gate 자체 결함 + ADR-031:139 누락 | pre-LAND |
| 6 | MCT-184 | 사전 차단 1회 성공 — §3.6.1 gate v2 PASS FIX 0 | pre-LAND |
| 7 | **MCT-185** | **사전 차단 1회 성공 + FIX 0회 (DesignReview + code lane 양쪽)** — ADR-032 evidence triad + Phase 0 verify 실측 | **pre-LAND + code lane (PASS FIX 0)** |

### 4.3 Phase 0 verify 실측 누적 효과

MCT-170/177/178/179/180 에서 6회 반복된 "설계가 sibling repo runtime 실상 미검증" lesson 이 MCT-182 이후 Phase 0 verify 독립 게이트로 정착. MCT-185 = Phase 0 verify + ADR-032 evidence triad 결합으로 FIX 0회 달성. 선행 Story 의 lesson reapply 누적 효과 (Epic 중반 이후 FIX 감소 추세) 실증.

### 4.4 박제 PR 5 체크리스트 자기규율 전수 이행

MCT-184 박제 PR 자체 incomplete 패턴 (SSOT drift 3호) lesson 직접 reapply:

| 항목 | 이행 |
|------|------|
| RETRO-MCT-185.md 존재 | ✅ (본 파일) |
| EPIC-RESULTS §Story-4 박제 | ✅ (본 Phase 2 PR2 산출) |
| Story frontmatter status=COMPLETED + completed_at | ✅ (2026-05-17) |
| CLAUDE.md hub#TBD 잔존 0줄 | ✅ (검증 완료) |
| ADR-029 §D2 + ADR-031 §D2/§D3 VERIFIED amendment box LAND confirm | ✅ (Phase 2 PR2 박제) |

## 5. carry over (post-Story)

| # | 항목 | severity | owner |
|---|------|----------|-------|
| 1 | engine DataClient WS stream subscribe loop wiring (realtime stream consumer full wiring) | non-blocking (SSE 기동 PASS) | MCT-186 carrier |
| 2 | engine exchange-adapter 제거 (mctrader_market_bithumb/upbit grep0) | HIGH | MCT-186 D4 |
| 3 | R2 EPIC-MCT-41 Live Mode Debut 블락 교차검증 (MCT-43~47 파일 교차 확인) | HIGH | MCT-186 진입 전 Orchestrator ordering |
| 4 | AC-4 cross-repo-contract-lock-check.sh CI env 구성 (TC-8 skipped 해소) — MCT-184 carry | non-blocking | MCT-186 / MCT-187 |
| 5 | data-free grep0 quad gate CI (MCT-188 POLICY_FINALIZED gate) | scope 외 | MCT-188 |
| 6 | codeforge upstream ADR escalation 후보 2/3 발의 (박제 PR 완결도 mechanical gate + post-merge audit lane) | HIGH 누적 | PMO-AUDIT-MCT-184 후속 (MCT-184 RETRO §4.3 이관) |

## 6. 다음 Story 진입

**MCT-186** (sequential_phase 5) — engine realtime cutover + exchange-adapter 제거 (R2 MCT-41 교차검증) — D4.

진입 권고:
- **R2 교차검증 gate** — MCT-186 진입 전 MCT-43~47 IN_PROGRESS 파일 교차 확인 (Orchestrator ordering 의무)
- **ADR-032 evidence triad reapply** — MCT-185 cutover 패턴 → MCT-186 exchange-adapter 제거 wiring drift 차단
- **grep0 gate** — engine `from mctrader_market_bithumb` / `from mctrader_market_upbit` grep0 LAND 이후 ADR-031 §D4 VERIFIED
- **Phase 0 verify 독립** — MCT-186 scope (exchange-adapter 제거 + realtime stream consumer full wiring) 별 Phase 0 코드 실측 의무
