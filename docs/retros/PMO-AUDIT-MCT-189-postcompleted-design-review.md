# PMO-AUDIT MCT-189 — post-COMPLETED design-review lane 보완 감사

> **트리거**: MCT-189 COMPLETED 박제 후 별 세션에서 codeforge-review:DesignReviewPLAgent lane-specific
> 9 검증 + Claude+Codex independent peer dispatch 수행. Story §10 박제 "design lane FIX iter = 0 (spec
> review iter1 PASS)" 가 **spec-level review only** 임이 사후 확인 — codeforge-review:DesignReviewPLAgent
> (lane-specific 9 검증 + 독립 peer) 가 정식 dispatch 되지 않았음.
>
> **timing**: 2026-05-17 (MCT-189 hub#363 박제 LAND 2026-05-16T15:41:28Z 후 별 세션)
> **dispatch base**: origin/main HEAD `ccacdce` (MCT-189 Phase 2 PR3 박제 LAND 직후)
> **검토 산출 paths (read-only)**: Story / spec / plan / domain-knowledge / ADR-029 + scope_manifest + counters.json

## 1. dispatch 결과 요약

| 항목 | 값 |
|------|-----|
| Verdict | **FIX (iteration 1/3)** |
| mechanical_category | none (fast-path 자격 없음 — 설계 의사결정 영역) |
| P0 | **1건** (F-1) |
| P1 | **5건** (F-2 / F-3 / F-4 / F-5 / F-6) |
| P2 | **4건** (F-7 / F-8 / F-9 / F-10) |
| §3.6.1 gate v2 self-verify | TEST1 0줄 stale + TEST2 ADR-032 4 file 일관 인용 = **PASS** |
| D-row ↔ scope_manifest reconcile | 4 산출물 D-1~D-10 byte-equivalent **PASS** |

## 2. Finding 9건 + 사후 정정 가능성 평가 (code-review iter1~3 효과 cross-check)

| # | severity | lane category | 영역 | 병렬 세션 code FIX iter 효과 | post-COMPLETED 정정 필요성 |
|---|----------|---------------|------|---------------------------|--------------------------|
| F-1 | **P0** | security-design | Story §7 SecurityArch 위협-완화 매핑 N/A 사유 부재 (base 템플릿 §7.7 N/A 사유 부재 → P0) | code FIX 영역 외 (문서 영역) | **valid** — post-COMPLETED amendment 후보 |
| F-2 | P1 | test-contract | plan Task 14 self-delete branch (`missing_ok=True`) vs promote_l1 본문 (`missing_ok=False`) — D-7 A idempotent 위배 가능 | **code FIX iter1 P0 "head_5xx 시나리오 부재" 부분 정정 가능성** + iter3 code-quality FIX 가 ENOENT 처리 정합화 | 정정 가능성 ≥ 70% — 별 verify 필요 |
| F-3 | P1 | data-migration | plan Task 20 `scan_and_cleanup_legacy()` Hive partition structure verified-via 부재 → false unlink risk | **code FIX iter PR2 combined F-4 (첫 sweep stall + batching) 효과 영역** | 정정 가능성 ≥ 50% — 별 verify 필요 |
| F-4 | P1 | test-contract | `test_head_5xx_retry` plan Task 16 Step 6 "별 mock 필요로 다음 Task 로 이연" 하나 별 Task 부재 | **code FIX iter1 P0 "head_5xx 시나리오 부재" 직접 정정** ✅ | 정정 가능성 ≥ 90% — 거의 확실 정정됨 |
| F-5 | P1 | observability/op-risk | legacy cleanup scan 빈도 / IO burst / NAS HEAD request rate OperationalRisk 매핑 부재 | code FIX 영역 외 (문서 영역) | **valid** — post-COMPLETED amendment 후보 |
| F-6 | P1 | observability | 신규 Counter `promote_l1_pre_delete_guard_mismatch_total` label / cardinality / Prometheus emit point 명시 부재 | **code FIX iter3 code-quality 효과 영역** (helper 추출 + Counter wiring) | 정정 가능성 ≥ 60% — 별 verify 필요 |
| F-7 | P2 | section-missing | scope_manifest D-row 표 형식 mismatch (flat carry_over_items vs design_decisions table) | code FIX 영역 외 (문서 영역) | **valid** — non-blocking, post-COMPLETED amendment 가능 |
| F-8 | P2 | design-completeness | DualWriter (nas_storage) → promotion (compactor) cross-submodule lazy import — Layer note 박제 부재 | code FIX 영역 외 (문서 영역) | **valid** — non-blocking, ADR-031 4-Layer 정합 cross-ref 보강 |
| F-9 | P2 | design-completeness | D-8 B pre-delete guard 가 sha256 metadata 미비교 justification 박제 부재 (D-4 vs D-8 inconsistency) | code FIX 영역 외 (문서 영역) | **valid** — non-blocking, design rationale 보강 |
| F-10 | P2 | implementability | plan Task 16 testcontainers fixture MCT-180 pattern reuse evidence 부재 | **code FIX iter1-3 효과 영역** (test file 직접 작성) | 정정 가능성 ≥ 80% — 거의 확실 정정됨 |

## 3. 결론 — 4 카테고리 분류

### A. 명백히 정정됨 (≥80%) — verify 만 의무
- F-4 (test_head_5xx_retry): code FIX iter1 P0 "head_5xx 시나리오 부재" 직접 정정 명시
- F-10 (testcontainers fixture): code FIX iter1-3 효과 영역

→ **carry over 0**, 별 verify (테스트 파일 read) 시 자동 해소

### B. 정정 가능성 중-고 (50~70%) — 별 verify 의무
- F-2 (missing_ok 정합)
- F-3 (Hive partition verified-via)
- F-6 (Counter label/cardinality)

→ **별 verify 권고** (data#73/#75 코드 측 확인). 미정정 발견 시 post-COMPLETED amendment 후보.

### C. 명백히 미정정 (문서 영역, valid) — post-COMPLETED amendment 후보
- **F-1 P0** (Story §7 SecurityArch 위협-완화 매핑 N/A 사유 부재)
- F-5 P1 (legacy cleanup OperationalRisk 매핑 부재)
- F-7 P2 (scope_manifest D-row 표 형식)
- F-8 P2 (Layer note 박제)
- F-9 P2 (D-8 sha256 justification)

→ **post-COMPLETED amendment 후보 5건** (P0×1 + P1×1 + P2×3). MCT-184 패턴 동형 (Story status=COMPLETED 유지 + post-completion amendment box).

### D. design-review lane 자체 누락 패턴 발견 (SSOT drift 4호 후보)

본 audit 의 trigger 가 자체로 **SSOT drift 4호 패턴 발견**:

- 박제 SSOT: Story §10 "design lane FIX iter = 0 (spec review iter1 PASS)"
- 실 SSOT: codeforge-review:DesignReviewPLAgent lane-specific 9 검증 + Claude+Codex independent peer = 미수행 (spec-only review 만 박제)
- 결과: lane-specific 9 검증이 잡았어야 할 9 finding (특히 F-1 P0 SecurityArch N/A 사유) 가 박제 단계에서 누락

| SSOT drift 호 | 트리거 | 패턴 |
|---------------|--------|------|
| 1호 (MCT-189) | operational evidence ≠ policy LAND date | image 빌드 date vs ADR-029 LAND date |
| 2호 (MCT-189) | design SSOT VERIFIED 박제 ≠ code SSOT production caller 0 | promote_l1() VERIFIED but caller 0 |
| 3호 (MCT-184) | 박제 PR title SSOT ≠ 박제 산출물 SSOT | hub#359 MERGED but RETRO+EPIC-RESULTS 미작성 |
| **4호 (MCT-189)** | **design-review lane 박제 SSOT ≠ 실 dispatch 수행 SSOT** | **"FIX iter = 0 PASS" 박제 but lane-specific 9 검증 + Claude+Codex peer 미dispatch** |

→ **codeforge upstream ADR escalation 후보 4** 발의 후보 — design-review lane dispatch 의무 mechanical gate (spec review + lane-specific 9 검증 + Claude+Codex independent peer 의 all-or-nothing 명시 + Story §10 박제 시 dispatch evidence 부재 → CI gate). codeforge#804 (박제 PR 완결도 gate) + #805 (post-merge audit lane) 의 자매 escalation 후보.

## 4. carry over 권고 (별 작업 trigger)

### Option A — MCT-189 post-COMPLETED amendment PR (MCT-184 동형)

1. **카테고리 A verify** (F-4 / F-10) — data#73/#75 코드 read + 테스트 파일 read → 명시 박제 ✅ 자동 해소
2. **카테고리 B verify + 필요시 정정** (F-2 / F-3 / F-6)
3. **카테고리 C 정정 (post-COMPLETED amendment)** — Story §7 Security N/A 사유 + §6 R7 OpRisk burst 매핑 + scope_manifest D-row 표 + DualWriter Layer note + D-8 sha256 justification

LAND 형식: doc-only fast-pass PR (mctrader-hub 영역). MCT-184 amendment 패턴 동형.

### Option B — SSOT drift 4호 정식 박제 (codeforge upstream escalation 후보 4 발의)

PMO retro (별 trigger) → SSOT drift 4호 (design-review lane 박제 SSOT ≠ 실 dispatch 수행 SSOT) 정식 박제 + codeforge upstream ADR escalation 후보 4 발의 (#804 + #805 자매).

### Option C — carry over only (별 세션)

본 audit file 박제만 LAND. 실 정정은 사용자 trigger 시 별 세션 dispatch.

## 5. 본 audit LAND meta

| 항목 | 값 |
|------|-----|
| audit 수행자 | codeforge-review:DesignReviewPLAgent (Orchestrator post-Sonnet dispatch) |
| audit 시점 | 2026-05-17 (post-MCT-189 COMPLETED 박제 LAND 직후) |
| audit base ref | origin/main HEAD `ccacdce` |
| audit 결과 LAND PR | mctrader-hub (본 audit file LAND, doc-only fast-pass) |
| follow-up Story 후보 | 없음 (carry over only, 사용자 결정 영역) |
| codeforge upstream escalation 후보 | **후보 4** 발의 후보 (design-review lane dispatch 의무 mechanical gate) |
