# RETRO-MCT-202 — Eager post-compaction cleanup cascade (3-tier grace-0 caller wiring)

> **Story**: MCT-202. **Epic**: EPIC-tier-promotion-single-source (POLICY_FINALIZED — MCT-189 후속 cascade 완결 child, MCT-202 = 마지막 child).
> **Parent dependency**: MCT-189 (WAL→L1 grace-0 wiring SSOT) → 본 Story 가 L1→L2 + L2→L3 + historical 로 cascade 완결.
> **Land window**: 2026-05-18 (Phase 1 hub #402 `db2c5d98` MERGED 09:34:58Z) ~ Phase 2 data #180 HEAD `0474f05` CI GREEN merge 대기 (본 retro = merge 전 마지막 lane 게이트).
> **Mode**: B cross-repo / Cutoff full-lane.
> **작성**: PMOAgent self-write (ADR-045 mandate / verified-via ADR-073 — FIX Ledger row + commit ref 인용).

## Outcome

사용자 가치 함수 = **컨테이너 disk-full 빈발 차단**. MCT-189 가 WAL→L1 단계 1/3 만 grace-0 eager unlink 작동시켰고, L1→L2 / L2→L3 cascade 가 미작동(production /d/market 117GB+ 누적, §0 Phase 0 verified-via `0e244e9`)이던 gap 을 caller-wiring 으로 완결:

- **root cause**: `runner.py:284 data=parquet_path` 가 `local_path == data == parquet_path` 동일 객체 전달 → `dual_writer.py:249 data != local_path` guard = False → MCT-189 LAND callee `_promote_after_nas_put` 가 의도된 분기 미진입 → L1/L2 source parquet 영구 잔존.
- **fix**: D-1 옵션 B (callee guard 제거 회피 — output self-unlink catastrophic regression 차단) — `DualWriter.write()` 에 `source_to_delete: Path | None = None` keyword-only 파라미터 추가. caller (`_dispatch_dual_write` + `_historical_dual_write`) 가 `source_to_delete=parquet_path` 명시 cascade intent 전달. backward compat (`None` default → MCT-189 LAND 동작 보존, 기존 caller 14+ 자동 호환).
- **NAS commit status gate** (사용자 답변 #2): `result.status == 'committed'` XOR `source exists` (INV-D). `local_only` / `hard_floor_blocked` = source 보존 + `scan_and_cleanup_legacy` sweep carrier 의존 보존.
- **WAL 24h grace 폐기** (사용자 답변 #3): `.sealed` segment 도 `.compacted` sentinel + NAS commit 후 즉시 unlink. disaster recovery = bucket versioning=Enabled (MCT-161) + retry_queue (MCT-156) + MCT-173 backfill 3종 흡수.
- **`committed_unlink_failed` P0 alarm**: `except OSError` 분기 신설 (Counter += 1 + log.error + return 'committed' — source 보존, sweep fallback). silent unlink 실패 차단.
- **Counter outcome 5종** (`committed_unlinked` / `committed_unlink_failed` / `local_only_retained` / `hard_floor_retained` / `already_promoted`) × 3 tier + `mctrader_retry_orphan_total{tier}` 3 + `mctrader_legacy_cleanup_race_noop_total` 1 = 19 series ≤ 50 (ADR-027 §D6 cardinality invariant 정합).
- **forward-only invariant 회복**: FIX iter3 에서 `_historical_dual_write` 고정 cascade 가 historical sequential local-only flow 에서 L2 eager unlink → L3 input 손실 = forward-only 위반을 catch → `source_to_delete` 파라미터화로 D-3 의도 충족 + forward-only 회복 확정.
- **ADR amendment 4종 LAND** (Phase 1 #402): ADR-027 §D5+§D7 / ADR-029 §D3+§D11 / ADR-017 §Amendment 4 / ADR-009 §D12.2. 새 ADR 결정점 = 0 (전부 기존 ADR amendment 흡수, FeasibilityAgent §4.2 "자연스러움" 정합).

## Lane 통과 타임라인

| Lane | 결과 | FIX iter | 비고 |
|------|------|----------|------|
| 요구사항 (Phase 0 4-agent + ChangeImpact/Feasibility/Continuity + RequirementsPL) | divergence 0 | 0 | `grace-0-local-delete.md` SSOT 발견 → "신규 설계 X, MCT-189 caller wiring 확장 O" 재정의 |
| 설계 (ArchitectPL + 6 deputy + chief author) | D-1~D-6 + 신규 D-5/D-6, INV 12종 | — | NAS GET 모드 발견 (D-2 옵션 C output-local 자연 종결) |
| 설계-리뷰 | iter1 FAIL → iter2 PASS | **1/3** (Ledger row 1) | chief author §8.5/§7.4/§7 sub-section 누락 + put_l1 propagation 미명시 → 설계 원인 재산출 |
| 구현 (DeveloperPL) | — | — | `dual_writer.py` 시그니처 + `runner.py` caller wiring + Counter 3종 + tests |
| 구현-리뷰 | iter1 FAIL → iter2 PASS | **1/3** (Ledger row 2) | `committed_unlink_failed` outcome 미구현 + §8.2 integration test 전량 미작성 → 구현 원인 재구현 (`140663881`) |
| CI-테스트 | iter1~4 FAIL → PASS | **4 iter** (Ledger row 3~6) | ruff/regression → pyright → forward-only 위반 → collision (아래 분석) |
| 통합테스트 (IntegrationTestAgent) | Baseline 4 + Story 4 PASS | — | testcontainers 2 win32 skip 정상, MCT-202 regression 0, Baseline 자동 승격 |
| 보안테스트 | N/A skip | — | `lanes.security_ai` opt-in 미설정 (CFP-317/ADR-048 정합 — code PR 기본 불필요) |
| PMO retro (본 lane) | 진행 | — | merge 전 마지막 게이트 |

## FIX Ledger 6 rows 분석 (Story §10 SSOT, Orchestrator monopoly append — PMO 읽기 전용)

분포: **설계 1 / 구현 1 / CI 4**. 패턴 요약 = chief author 초안 누락 1회 + 구현 누락 1회 + **CI 가 review lane 이 놓친 regression/lint/type/collision 4회 authoritative catch**.

| # | layer | root-cause 판정 | resolution commit (verified-via) | 핵심 학습 |
|---|-------|----------------|----------------------------------|-----------|
| 1 | 설계-리뷰 1/3 (P0×3+P1×2) | 설계 (chief author 미흡 — root-cause-decision "항상 설계") | Phase 1 #402 follow-up commit (hub) | §7/§8.5/§3/§4 API 계약 누락 — chief author 초안 self-check gap |
| 2 | 구현-리뷰 1/3 (P0×2+P1×2) | 구현 1차 가정 (DeveloperPL 진단 → ArchitectPL 최종 판정) | `140663881` (data #180) | `except OSError` branch 부재 + §8.2 integration test 전량 미작성 |
| 3 | CI-테스트 iter1 (ruff 13 + caller_absorb regression×2 + BEHIND) | 구현 (regression — root-cause-decision "Integration test FAIL: 구현") | `7bf0d4a2` + `75199f35` (data #180) | `source_to_delete` 인터페이스 추가가 기존 mock signature 미반영 — **CodeReview integration dir 미실행 gap** |
| 4 | CI-테스트 iter2 (pyright 6 type) | 구현 (test mock type-unsafe — "lint/type 단일파일: 항상 구현") | `8fbb01b0` (data #180) | NASUploadResult.status Literal 미준수 + DualWriter 생성자 param 오인 — CI-테스트 lane 다단계 (lint→type→test) |
| 5 | CI-테스트 iter3 (ubuntu 3 fail: historical l3=0 + NoSuchBucket×2) | **구현** (DeveloperPL 진단 → ArchitectPL escalate 최종판정) | `57cac077` (data #180) | `_historical_dual_write` 고정 cascade 가 historical sequential local-only flow 에서 L2 eager unlink → L3 input 손실 = **forward-only invariant 위반** → `source_to_delete` 파라미터화로 D-3 의도 충족 + forward-only 회복 확정 |
| 6 | CI-테스트 iter4 (pytest import collision) | 구현 (IntegrationTestAgent baseline 자동승격 메커니즘 결함 — "Integration test infra: 구현") | `0474f05` (data #180) | `test_eager_cleanup_cascade.py` 동일 basename 3곳 (원본 + baseline/MCT-202/ + stories/EPIC.../MCT-202/) → `--import-mode=importlib` (pyproject.toml 영구 박제) |

### 핵심 회고 포인트 (cross-Story 학습 후보)

#### (a) CodeReview iter2 PASS 였으나 CI 가 integration dir regression + forward-only 위반 catch — review lane 의 integration dir 미실행 gap

구현-리뷰 iter2 PASS 후 CI 가 3개 별개 결함을 authoritative catch:
- **Ledger row 3**: `tests/integration/test_nas_key_caller_absorb.py` 2 regression — `source_to_delete` 파라미터가 기존 integration test mock lambda signature 미반영. CodeReview 가 integration dir 미실행으로 미검출.
- **Ledger row 5**: `_historical_dual_write` 고정 cascade 가 historical sequential local-only flow (CodebaseMapper 기 지적 `L2Compactor(nas_uploader=None)`) 에서 L2 eager unlink → L3 input 손실 = **forward-only invariant 위반**. unit test green 였으나 integration historical path 가 실 결함 surface.

판정: review lane (구현-리뷰) 이 unit test 만 신뢰 + integration dir 미실행 → CI 가 유일 authoritative gate. Ledger row 3·5 의 `disputed_claims` 가 "CodeReview integration dir 미실행 gap (CI 가 authoritative catch)" 명시. **이 패턴이 cross-Story 반복되면 ADR 후보** (아래 ESCALATE 트렌드 §참조).

#### (b) IntegrationTestAgent 단독 suite run PASS ≠ 통합 collection PASS (baseline 승격 collision)

Ledger row 6: IntegrationTestAgent 가 `ecff662` baseline 자동승격 self-commit 시 단독 suite run 만 확인 → 동일 basename 3곳 (`tests/integration/` 원본 + 승격 `baseline/MCT-202/` + `stories/EPIC-tier-promotion-single-source/MCT-202/`) pytest rootdir module name collision 을 미검증 (ubuntu+windows 양 OS, exit 2). FIX = `--import-mode=importlib` (pyproject.toml 영구 박제). disputed_claims = "IntegrationTestAgent ecff662 self-commit 이 collision 미검증 (단독 suite run 만 확인, 통합 collection 미확인)".

#### (c) Codex single-peer 환경 제약

설계리뷰 + 구현리뷰 양 lane CodexReviewAgent 미가용 (sandbox PowerShell ConstrainedLanguage `[Console]::OutputEncoding` 차단). ClaudeReviewAgent single-peer 로 진행. Ledger row 1 disputed_claims = "P1-1 put_l1 propagation single-peer (Codex 미가용 carry-over)" / row 2 = "CodexReviewAgent 미가용 (sandbox PowerShell ConstrainedLanguage) single-peer". 환경 복구 후 P1-1 재검증 권고 (carry-over).

## Carry-over (4종)

| # | 출처 | carry-over 내용 | 인계 대상 |
|---|------|-----------------|-----------|
| CO-1 | ArchitectPL 권고 | Change Plan §3.3 D-3 wording 이 "historical sequential local-only flow 순서 보존" 명세 부재 (구현 자력 추론 영역 — Ledger row 5 forward-only 위반의 근접 원인) → post-LAND 명세 보강 | hub Change Plan amendment (별 doc-only chore 또는 MCT-205 흡수) |
| CO-2 | IntegrationTestAgent 권고 | ADR-055 §7 baseline 승격 layout 표준에 "pytest `--import-mode=importlib` 의존" 명세 추가 (동일 basename 3곳 collision 재발 방지, 현재 pyproject.toml 영구 박제됨) | ADR-055 §7 amendment (codeforge governance 영역 — Orchestrator 회부) |
| CO-3 | Codex 환경 제약 | 설계리뷰+구현리뷰 양 lane CodexReviewAgent 미가용 (sandbox PowerShell ConstrainedLanguage). ClaudeReviewAgent single-peer carry-over — 환경 복구 후 P1-1 (put_l1 propagation) 재검증 권고 | 환경 복구 후 별 verify (ops chore) |
| CO-4 | FIX Ledger boundary | Ledger row 1·2 가 chief author commit 으로 append (DesignReviewPL advisory note 박제). fix-event-v1 SSOT = Orchestrator-exclusive. row 3~6 은 Orchestrator 직접 append (정합). 향후 boundary 정합 확인 | codeforge fix-event-v1 contract boundary audit (별 governance) |

### D-4 carry-over 흡수 (Story §3 OUT-OF-SCOPE 기 박제)

- **MCT-203** — `promote_l1` → `promote_tier` rename (tier dimension 일반화).
- **MCT-204** — NAS object lifecycle (cascade 후 NAS L1/L2 object 회수 정책, D-2 옵션 C 결과).
- **MCT-205** — `_dispatch_dual_write` + `_historical_dual_write` 통합 refactor (drift risk 차단, CO-1 흡수 적격).
- **gc.py 폐기 검토** (D-6) — 14d production evidence gate (`mctrader_retry_orphan_total` rate = 0 + `committed_unlinked` 정상 ramp-up) 후 별 Story.
- **`gc_daemon._archive_failed` 운영 runbook 갱신** (D-4) — 본 Story 는 docstring amendment only, runbook 갱신 = PMO retro carry-over (CO-1 인접, `docs/runbooks/` 별 doc-only chore).

## Cross-Story 패턴 분석 (ADR-045 Amendment 5 §D-9)

### 패턴 1: MCT-189 → MCT-202 cascade 완결, grace-0 invariant 3-tier 전파

EPIC-tier-promotion-single-source 의 grace-0 wiring 이 MCT-189 (WAL→L1 1/3) → MCT-202 (L1→L2 + L2→L3 + historical 3/3) 으로 dimension 일반화 완결. ADR-029 §D3 의 tier dimension 이 L1 단독 → 3-tier cascade 로 박제 (§D11 신설 box, INV 12종). **EPIC-tier-promotion-single-source 마지막 child 완료** — Epic CLOSED prerequisite 잔여 = production evidence (14d telemetry + WAL 30G 실측 + evidence quad) only, 본 cascade wiring 으로 정책 차원 gap 해소.

### 패턴 2 (ESCALATE 트렌드): "review lane PASS vs CI/production 실측 결함" 재발 — 누적 카운트

이 패턴은 EPIC-tier-promotion-single-source 의 Epic Summary 가 명시한 trigger 와 **동일 계열**:
- Epic Summary (EPIC-RESULTS): "MCT-156/162/160 3-cycle 누적 실패 patterns (review lane PASS vs production 실측 결함)" — Epic 창설 동기.
- MCT-189 RETRO §2: "decision-defined ≠ caller-wired" — VERIFIED badge evidence triad 부재 (ADR-032 trigger).
- **MCT-202 (본 Story)**: 구현-리뷰 iter2 PASS 후 CI 가 integration dir regression (Ledger row 3) + forward-only 위반 (Ledger row 5) catch — **review lane 의 integration dir 미실행 gap** 이 구체적 신호.

→ **누적 ≥ 2 도달 판정**: "review lane unit-test-only PASS → integration/production 실측 결함" 패턴이 Epic 차원 trigger (MCT-156/162/160) + MCT-202 (review lane integration dir 미실행) 으로 누적 재발. ADR-045 Amendment 5 §D-9 hybrid detection (primary anchor_id strict — `review-lane-integration-dir-not-executed` / secondary root_cause_class — `review_pass_vs_actual_failure`) 양 채널 모두 충족.

## ADR 후보 발의 (Mandatory — ADR-045 Amendment 5 §D-9, escalation_action 판정)

**cross_story_pattern_adr_trigger** field 채움 (mandatory, 회피 불가):

- **anchor_id (primary, strict)**: `review-lane-integration-dir-not-executed`
- **root_cause_class (secondary fallback)**: `review_pass_vs_actual_failure`
- **누적 카운트**: ≥ 2 (Epic trigger MCT-156/162/160 계열 + MCT-202 review lane integration dir 미실행 = Ledger row 3·5 disputed_claims 박제)
- **escalation_action 판정 = `escalate_user`** (NOT `adr_draft_emitted`)

**escalate_user 채택 rationale** (false positive 안전망 — Story §5.4 EC-3 정합): 본 패턴의 root cause 는 **이미 ADR-032 (VERIFIED badge evidence triad — file:line + production caller grep ≥1 + integration test PASS, Proposed, `.codeforge/counters.json`) 가 부분 cover**. MCT-189 RETRO §ADR-032 self-reference + EPIC-RESULTS amendment 가 이미 동일 trigger 를 ADR-032 로 박제했고, owner Story = MCT-190 reservation. 본 MCT-202 의 신규 신호 = "evidence triad 의 (3) integration test PASS 가 review lane 자체 실행을 보증하지 못함 — review lane 이 unit test 만 신뢰하고 integration dir 미실행" 이라는 **ADR-032 amendment 영역**이지 신규 ADR 영역 아님. 신규 ADR draft 정식 emit 은 ADR-032 와 중복 → trivial-adjacent 판정 → 사용자/Orchestrator manual decide 의뢰가 정확.

**Orchestrator 회부 권고** (ArchitectAgent reject 가능 채널 보존):
- **권고 A (primary)**: ADR-032 (MCT-190 owner) 에 amendment — evidence triad 의 (3) 항목을 "integration test PASS" → "**review lane 이 integration dir 를 실제 실행한 evidence (collection + run log)**" 로 강화. MCT-202 Ledger row 3·5 가 첫 보강 trigger 사례.
- **권고 B (보조)**: ADR-055 §7 baseline 승격 layout 표준에 `--import-mode=importlib` 의존 명세 추가 (CO-2, Ledger row 6 — IntegrationTestAgent self-commit 이 통합 collection 미검증).
- ArchitectAgent 가 status: Proposed → Accepted | Rejected 최종 결정 (PMOAgent = proposer only, verdict 권한 없음 — ADR-035 정합).

## Epic milestone 갱신

EPIC-tier-promotion-single-source 추적 = **file-based SSOT** (`docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`, GitHub milestone 미사용 — 본 repo Epic 관리 관례, MCT-189 도 동일하게 EPIC-RESULTS amendment 처리).

- **Epic status**: POLICY_FINALIZED 유지 (6/6 core Story + carry-over MCT-189 RESOLVED + MCT-202 = cascade 완결 마지막 child).
- **MCT-202 = cascade 완결 마지막 child**: MCT-189 carry-over (WAL→L1 단독) 의 L1→L2 + L2→L3 + historical dimension gap 해소. EPIC-RESULTS §Amendment (D3=C wiring deferred) 의 후속 완결.
- **Epic CLOSED 판정**: **불가 (carry-over 잔존)**. Epic CLOSED prerequisite = production evidence (14d telemetry 0-hit + WAL 30G 실측 + evidence quad 동일 1h window, D8-9=C). MCT-202 는 정책/wiring 차원 gap 을 닫았으나 production evidence gate 는 미완 (D-6 14d production evidence gate `mctrader_retry_orphan_total` rate=0 + `committed_unlinked` ramp-up 신규 추가). Epic CLOSED transition 은 별 PR 의무 유지.
- **EPIC-RESULTS amendment 권고 (Orchestrator 회부)**: Phase 2 #180 merge 후 `EPIC-RESULTS-EPIC-tier-promotion-single-source.md` §Amendment 에 MCT-202 행 추가 (cascade 완결 박제 + Epic CLOSED prereq prod-6 신규: cascade 14d production evidence gate). 본 retro 작성 시점 = Phase 2 merge 전 → EPIC-RESULTS amendment 는 merge 후 Orchestrator/DocsAgent 경유 (PMO write boundary = retro + Story §11 only).

## Phase 2 #180 merge 회부 — ESCALATE 1건

**RETRO 완료 = merge 전 마지막 lane 게이트 충족.** 단, merge 차단 게이트 1건 ESCALATE:

### ESCALATE: phase-gate-mergeable = ACTION_REQUIRED (Story 바인딩 부재)

PR #180 현황 (verified-via 2026-05-18 `gh pr view 180`):
- CI 핵심 게이트 ALL SUCCESS: `ci-matrix (ubuntu-latest)` / `ci-matrix (windows-latest)` / `ci` / `check-gate` / `CodeQL` / `Analyze (actions)` / `Analyze (python)` = SUCCESS. `mergeable=MERGEABLE`.
- **`phase-gate-mergeable = ACTION_REQUIRED`** (`mergeStateStatus=UNSTABLE`).
- **근본 원인** (`.github/workflows/phase-gate-mergeable.yml` verified-via): PR #180 에 (1) `story_uri:` 마커 부재 → cross-repo Story frontmatter 바인딩 실패, (2) 라벨 `[]` (빈 set) → `gate:design-review-pass` 라벨 부재, (3) `[설계-리뷰] ... PASS` PR comment evidence 부재. → file-based heuristic 진입 → `required.gate = gate:design-review-pass` 미충족 → `conclusion: action_required`.

이는 **PMO retro lane 영역 외** (라벨/comment evidence 부착 = Orchestrator monopoly, PL synthesis only — CFP-61/ADR-022 §결정 4). Orchestrator 가 merge 전 다음 중 하나 처리 의무:
- (권장) PR #180 body 에 `story_uri: https://github.com/mclayer/mctrader-hub/blob/main/docs/stories/MCT-202.md` 추가 + `gate:design-review-pass` 라벨 부착 (Story frontmatter `phase: 구현` 시 design-review-pass gate 요구 — 설계리뷰 iter2 PASS evidence 기 존재).
- 또는 PR #180 에 `[설계-리뷰] ... PASS` comment 박제 (CFP-133 fallback evidence path).
- Phase 1 #402 가 doc-only fast-pass 로 merge 됐으므로 설계리뷰 PASS evidence 는 hub 측 박제 — Orchestrator 가 data #180 에 cross-repo binding 또는 라벨 보강 필요.

**FIX 횟수 정상성 판정**: 설계 1 + 구현 1 + CI 4 = 총 6 FIX. CI-테스트 lane = max 없음 (ADR-048 ∞). 설계/구현 각 1/3 으로 max 3 미달 (정상). CI 4회는 4 별개 결함 계열 (lint/regression → type → forward-only → collision) 의 순차 surface — review lane gap 의 자연 결과이며 ESCALATE 임계 미달 (FIX 루프 자체는 정상 수렴). **단 패턴 2 (review lane integration dir 미실행) 는 cross-Story 누적 ≥ 2 → ADR-032 amendment 후보 (위 §ADR 후보 발의 escalate_user 회부)**.

## Pre-LAND vs Post-LAND 검증

| 항목 | pre-LAND (retro 시점) | post-LAND (carry) |
|------|----------------------|-------------------|
| Phase 1 hub #402 | MERGED `db2c5d98` 2026-05-18T09:34:58Z (doc-only fast-pass) | ✓ |
| Phase 2 data #180 CI | ci-matrix ubuntu+windows / ci / check-gate / CodeQL ALL SUCCESS, HEAD `0474f05` | merge 대기 (phase-gate ESCALATE 해소 후) |
| unit test | ~80+ 신규 all green (Impl Manifest 8 test file) | ✓ |
| integration test | IntegrationTestAgent Baseline 4 + Story 4 PASS (testcontainers 2 win32 skip) | ✓ |
| 회귀 | MCT-202 regression 0 (기존 4 FAIL = pytest-asyncio/Windows os.rename, MCT-202 무관) | ✓ |
| ruff + pyright | 0 violation (Ledger row 3/4 FIX 후) | ✓ |
| **cascade 14d production evidence gate** | LAND 후 시작 | **carry over** — `mctrader_retry_orphan_total{tier}` rate=0 + `compactor_local_self_delete_total{outcome="committed_unlinked"}` 정상 ramp-up (D-6 gc.py 폐기 검토 prerequisite + Epic CLOSED prereq prod-6 후보) |
| Codex peer | 미가용 (sandbox ConstrainedLanguage) — ClaudeReviewAgent single-peer | **carry over (CO-3)** — 환경 복구 후 P1-1 재검증 |

## Key References

- Story SSOT: `docs/stories/MCT-202.md` (§0-§10 immutable, §11 retro cross-ref = PMO self-write)
- Change Plan: `docs/change-plans/MCT-202-eager-cleanup-cascade.md` (§1-§11 + §13 Phase 1 self-check)
- Domain Knowledge: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` (3-tier evidence triad cascade amendment)
- ADR amendment 4종: ADR-027 §D5+§D7 / ADR-029 §D3+§D11 / ADR-017 §Amendment 4 / ADR-009 §D12.2
- parent RETRO: `docs/retros/RETRO-MCT-189.md` (WAL→L1 grace-0 wiring SSOT — 본 Story cascade 의 부모)
- Epic results: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` (§Amendment D3=C wiring deferred → MCT-189 RESOLVED → MCT-202 cascade 완결)
- ADR-032 (Proposed, MCT-190 owner reservation): VERIFIED badge evidence triad — 본 retro §ADR 후보 발의 amendment 후보 (escalate_user 회부)
- LAND: hub #402 (`db2c5d98`) Phase 1 docs MERGED / data #180 (HEAD `0474f05`) Phase 2 src+tests CI GREEN merge 대기
- FIX Ledger: Story §10 `<!-- FIX-LEDGER-START/END -->` 6 rows (Orchestrator monopoly append, fix-event-v1 SSOT)
