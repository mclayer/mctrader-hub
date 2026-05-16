---
type: pmo-patterns-analysis
session_date: "2026-05-16"
trigger: "운영 진단 세션 — 사용자(trader@mclayer.it) 디스크 압박 보고 → systematic-debugging Phase 1~3 진행 중 cross-document SSOT drift 2건 동시 발견"
author: PMOAgent
scope: |
  Session retro / cross-Story patterns analysis (단일 Story trigger 회고 아님). MCT-189 Story 가
  본 세션에서 RESERVED 박제됐으나 IN_PROGRESS 진입 전이므로 별 RETRO-MCT-189.md 는 본 Story
  LAND 시점 별도 작성 의무 retain.
verified_sources:
  - "production host: 컨테이너 status / image inspect / df / docker volume size 직접 측정 (2026-05-16 KST)"
  - "mctrader-data working tree: f233952 (MCT-180 LAND, 본 세션 재빌드 base) + HEAD main (MCT-182~ 시점)"
  - "git grep -nE 'promote_l1\\(|from mctrader_data\\.compactor\\.promotion import' -- 'src/**'"
  - "git grep -nE 'unlink|Path.*unlink' -- 'src/mctrader_data/nas_storage/dual_writer.py' 'src/mctrader_data/compactor/l1.py' 'src/mctrader_data/compactor/l2.py' 'src/mctrader_data/compactor/l3.py' 'src/mctrader_data/compactor/runner.py'"
  - "docs/adr/ADR-029-tier-promotion-single-source.md §D3 (line 240-246 + line 212 + line 363)"
  - "docs/stories/MCT-169.md + MCT-172.md (D3=C VERIFIED 박제)"
  - "docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md (POLICY_FINALIZED 2026-05-14)"
  - "docs/retros/EPIC-RESULTS-EPIC-mctrader-docker-stack.md (POLICY_FINALIZED 2026-05-15, ${IMAGE_TAG} prod pin = prod-1 carry over)"
  - "docs/stories/MCT-189.md (본 세션 RESERVED 박제, §0 Phase 0 evidence table)"
  - ".codeforge/counters.json (MCT-189 + ADR-032 reservation)"
related_patterns:
  - "MCT-179: ADR-030 Out-of-scope D1-D19 전수 reconcile (cross-document SSOT forcing function 1번째 사례)"
  - "MCT-182: PMOAgent Story 완료 감사 박제 (PMO-AUDIT-MCT-182, ADR 후보 발의 forcing function pattern 일반화)"
  - "MCT-189: ADR-029 §D3=C wiring 완결 Story (본 세션 발의)"
---

# PMO Patterns Analysis — Cross-Document SSOT Drift 2건 (2026-05-16 운영 진단 세션)

> PMOAgent cross-Story patterns analysis (feedback_pmo_retro_mandatory 정합). 운영 진단 세션에서
> **POLICY_FINALIZED 박제된 Epic 2건 (tier-promotion + docker-stack)** 각각 1건씩, 합계 2건의
> cross-document SSOT drift 가 동일 세션 내 발견. cross-document SSOT forcing function pattern
> 의 **2번째 + 3번째 재현 사례** 박제.

## 1. 세션 trigger + 직접 발견 evidence

### 1.1 사용자 trigger

trader@mclayer.it 2026-05-16 운영 보고: "로컬 디스크 용량이 계속 차고 있는데 S3에 데이터 제대로 적재되고 있는가."

### 1.2 systematic-debugging Phase 1~3 결과

| Phase | 가설 | 실측 결과 |
|-------|------|-----------|
| 1 (재현) | NAS 적재 실패 → 로컬에만 쌓이는 중 | 부분 기각 — NAS 자체는 정상 적재 중 (`[nas_uploader] uploaded ... etag=...` 다수) |
| 2 (관찰) | grace-0 정책이 동작하지 않음 | 확인 — /d/market 130.8 GB + /d/wal 38.1 GB 영구 누적, 신규 market parquet 2026-05-15 이후 0개 (대부분 backfill 산물) |
| 3 (가설) | (a) WAL 30G 초과 = backfill 무한 루프 + (b) market parquet 누적 = ADR-029 §D3=C wiring 부재 | 양쪽 모두 확인 |

### 1.3 발견된 2 drift

| # | Drift | Layer |
|---|-------|-------|
| **Drift A** | mctrader-data:pilot **created 2026-05-13T15:51:28Z** image (pkg 0.9.0) 가 production 7 컨테이너(compactor + ingester-upbit + ingester-bithumb + backfill-upbit + backfill-bithumb) 에서 **2026-05-13 ~ 2026-05-16 (2일+)** 가동 중. 즉 EPIC-tier-promotion-single-source POLICY_FINALIZED 2026-05-14 + EPIC-mctrader-docker-stack POLICY_FINALIZED 2026-05-15 양쪽 정책 적용 무의 image | **operational** (image 배포 layer) |
| **Drift B** | ADR-029 §D3=C "Local delete = NAS HEAD verify + grace 0" + MCT-169 D3 VERIFIED + EPIC-tier-promotion-single-source POLICY_FINALIZED 박제됐으나, `promote_l1()` 호출 site = **0건** (f233952 + HEAD main 동일 grep). DualWriter / l1.py / l2.py / l3.py / runner.py 어느 쪽도 NAS PUT commit 후 source local unlink 없음 (`tmp_path` unlink 만) | **architecture** (코드 wiring layer) |

## 2. Drift A — 이미지 배포 drift (operational layer)

### 2.1 정책 timeline vs production image timeline

| 시각 | 사건 | image |
|------|------|-------|
| 2026-05-13T15:51:28Z | mctrader-data:pilot **build** (pkg 0.9.0, MCT-167 이전 시점) | pilot (old) |
| 2026-05-14 | EPIC-tier-promotion-single-source **POLICY_FINALIZED 박제** (MCT-167+168+169+170+171+172 LAND, capacity_probe + ingest_blocker + DualWriter L1 NAS PUT) | pilot (old) **그대로 가동** |
| 2026-05-15 | EPIC-mctrader-docker-stack **POLICY_FINALIZED 박제** (MCT-175~181 LAND, ${IMAGE_TAG} prod pin = prod-1 carry over, dev=latest 현행 유지) | pilot (old) **그대로 가동** |
| 2026-05-16 | 본 세션 진단 → mctrader-data 신 이미지 (f233952 base, MCT-180 LAND commit 시점) 재빌드 + compactor + ingester 2 service force-recreate | pilot (new) |

### 2.2 image base commit 선정 근거

- HEAD main (MCT-182~ 시점) 빌드 시도 → **ModuleNotFoundError**: `mctrader_data/paper_lineage.py:25` `from mctrader_market.paper_lineage import (...)` 시도하나 vendor wheel `mctrader_market-0.1.0-py3-none-any.whl` (2026-05-10 build, market#11 LAND 이전) 에 해당 모듈 없음 → 빌드 불가
- f233952 (MCT-180 LAND commit) 선택 근거: (a) capacity_probe + ingest_blocker + DualWriter L1 NAS PUT 모두 LAND 완료 (b) MCT-182 vendor wheel 의존 미진입 (c) vendor wheel 호환

### 2.3 본 세션 응급 조치 결과

| 조치 | 결과 |
|------|------|
| backfill-upbit/bithumb 무한 루프 (`while true; backfill --days 90; sleep 3600`) stop | Exited 137 (graceful kill) |
| compactor + ingester-upbit + ingester-bithumb 신 이미지 force-recreate | Up + `/metrics` 정상 응답 |
| capacity_probe + ingest_blocker live Gauge/Counter 노출 확인 | `mctrader_capacity_usage_bytes` / `mctrader_capacity_threshold_ratio` / `mctrader_ingest_blocked_total` 출력 확인 |
| DualWriter L1 NAS PUT commit 시도 | `status=committed (ADR-029 D1=B)` 248건 commit, 에러 0 |

→ **forward bloat 차단 완료**. legacy 130 GB 자동 회수는 Drift B (코드 wiring) 해결 후 또는 별 cleanup script (MCT-189 §3 S6 검토 대상).

### 2.4 근본 원인

EPIC-mctrader-docker-stack POLICY_FINALIZED 박제 시 **`${IMAGE_TAG}` prod 실 적용 = prod-1 carry over** (production deploy 후 release/sha pin 별 PR 의무) 로 명시됐으나, prod-1 carry over 가 **실 production 컨테이너 image 갱신 trigger** 와 연결되지 않음. 즉 정책 LAND ↔ image 재빌드/재배포 사이의 forcing function 부재.

## 3. Drift B — 코드 wiring drift (architecture layer)

### 3.1 박제 vs 실 코드 evidence table

| 검증 항목 | 박제 가설 (CLAUDE.md / ADR-029 / EPIC-RESULTS) | 실측 결과 | 판정 |
|-----------|--------------------------------------------|-----------|------|
| `promote_l1()` 호출 site | MCT-169 D3=C VERIFIED — runner 파이프라인 wiring 완료 | `git grep -nE "promote_l1\(\|from mctrader_data\.compactor\.promotion import"` = **0건** (f233952 + HEAD main 동일) | ❌ wiring 부재 |
| `dual_writer.py` post-PUT source local unlink | NAS PUT commit 후 source unlink (D3=C) | 모든 `unlink` 호출이 `tmp_path` (atomic write 임시파일) 만. line 242 주석 "NAS queued ... caller source safe to delete" → caller 의무 떠넘김, but caller (l1.py/l2.py/l3.py/runner.py) 도 호출 안 함 | ❌ 로직 부재 |
| `l2.py` / `l3.py` tier promotion 시 source local 삭제 | L1→L2 승급 시 L1 source 삭제, L2→L3 승급 시 L2 source 삭제 (ADR-029 §D3 line 244-245) | tier promotion src/ 측 source unlink 호출 0건 | ❌ 로직 부재 |
| MCT-169 §11 박제 | D3 VERIFIED (NAS HEAD verify + immediate local delete) | Story §11 박제는 "D3 VERIFIED" 명시, but production caller grep evidence 부재 | ⚠️ false positive |

### 3.2 ADR-029 §D3 박제 vs 실상 cite

ADR-029 본문 인용:
- line 212: "ADR-027 §D7 local GC 7일 grace 정책 = L1 tier 에 대해 grace 0 (D3=C, NAS HEAD verify 후 immediate delete) 로 확장"
- line 240-246: §D3 본문 "Tier promotion 후 local file delete 정책 = **NAS HEAD verify + grace 0 (immediate after verify)**: L1→L2 promotion 시 L2 NAS PUT 완료 + L2 NAS HEAD verify (version/etag exact match + sha256 verify) 후 즉시 local L1 file 삭제..."
- line 363: "Tier promotion 후 local delete = forward-only 위반 0 (D3=C ambiguity 차단)"

실 production 코드 결과: 위 정책의 **enforcement layer = 0** (caller 없음 → ambiguity 차단도 0).

### 3.3 근본 원인 (RCA — 5 Whys 압축)

1. **Why** 130 GB legacy parquet 누적? → grace-0 local delete 미작동
2. **Why** grace-0 local delete 미작동? → `promote_l1()` 정의는 있으나 caller 0건
3. **Why** caller 0건? → MCT-169 LAND 시점 wiring 박제 누락
4. **Why** wiring 누락이 VERIFIED 박제로 통과? → review lane 이 `정책 박제 + 함수 정의` 만 검증, **production caller grep + integration test 실 호출** 미검증
5. **Why** 5 Why 누락 검증 절차 부재? → Story §11 박제 + scope_manifest VERIFIED badge 가 "**evidence triad** (file:line + caller grep + integration test)" 의무화 안 됨 (**ADR 후보 발의 trigger**, §6 참조)

### 3.4 Drift B 와 MCT-179 §D8 가공 metric 사건의 동형성

| 항목 | MCT-179 §D8 가공 metric (cross-document SSOT 1번째 사례) | MCT-189 §D3=C wiring 부재 (본 사례) |
|------|-------------------------------------------------------|------------------------------------|
| 박제 vs 실상 gap | alert/dashboard 가 emit 안 되는 metric 지칭 (`wal_capacity_bytes` 등) | ADR 가 호출되지 않는 함수 지칭 (`promote_l1()`) |
| review 통과 evidence | metric **이름** + ADR-030 §D8 박제 | 함수 **정의** + ADR-029 §D3 박제 |
| 결정적 부재 | Phase 0 verify 가 producer path = MCT-171 LAND SSOT (`mctrader_capacity_usage_bytes`) 실 grep 미수행 | Phase 0 verify 가 `promote_l1()` caller grep 미수행 |
| 영향 | R2 CRITICAL deliverable (WAL 30G alert) 무력화 | §D3=C deliverable (grace-0 local delete) 무력화, 130 GB 누적 |
| 해소 | MCT-179 fix 64647c7 — MCT-171 SSOT 정렬, R2 회복 | MCT-189 LAND — wiring 완결 + ADR-029 §D3 amendment box (evidence triad 박제) |

→ **MCT-179 lesson 이 MCT-189 trigger 코드 lane 에 미적용**. Phase 0 verify 의 grep 1회만 추가했으면 MCT-169 LAND 시점에 차단 가능했음.

## 4. cross-document SSOT forcing function pattern — 3 사례 누적

| # | 사례 | 발견 시점 | drift 유형 | 해소 |
|---|------|----------|-----------|------|
| 1 | MCT-179 ADR-030 Out-of-scope D1-D19 전수 reconcile | 2026-05-15 (MCT-179 design iter1 P0) | ADR row ↔ scope_manifest §design_decisions desync | ArchitectPL 1회 전수 reconcile (c8e4b8e) → MCT-180/181 design P0×0 회수 |
| 2 | MCT-182 PMOAgent Story 완료 감사 박제 (PMO-AUDIT-MCT-182, ADR 후보 발의 forcing function 일반화) | 2026-05-16 (Story LAND 직후 PMO retro) | Story §11 박제 SSOT 와 §8.5 Impl Manifest 의 정합 의무 일반화 | PMO 자체 audit 박제 + ADR-NNN 후보 발의 path 일반화 |
| 3 | **본 사례 — Drift A (image deploy) + Drift B (코드 wiring)** | 2026-05-16 (운영 진단 세션) | (A) POLICY_FINALIZED 박제 ↔ production image 적용 사이 forcing function 부재 / (B) VERIFIED 박제 ↔ production caller 실재 사이 evidence 부재 | (A) prod-1 carry over → image redeploy trigger 별 절차 의무화 (현 세션 응급 처리 + 일반화 = ADR-032 §3) / (B) MCT-189 wiring 완결 + ADR-032 evidence triad 의무화 |

→ 3 사례 모두 **"박제 (badge) ↔ 실상 (runtime/code) 사이의 forcing function 부재"** 의 동일 root cause. 일반화 룰 발의 = ADR-032 (§6).

## 5. EPIC-tier-promotion-single-source POLICY_FINALIZED 정직 박제

본 PMO retro 는 EPIC-RESULTS-EPIC-tier-promotion-single-source.md 의 Status 강등을 권장하지 **않음**. 사유:

- D1+D2+D4+D5+D6+D7+D8+D9+D10+D11 = LAND VERIFIED 정상
- D3 만 wiring 부재 (10/11 정상, 1/11 partial)
- POLICY_FINALIZED 의 "정책 finalize" 의미와 정합 (D8-3=A — 정책 finalize only + telemetry watcher, 실 sunset 별 Story 정합 패턴)
- Epic CLOSED prerequisite (prod-1~4) 가 production evidence 완성 후 별 PR 로 분리된 정책 정합

대신 **EPIC-RESULTS amendment box 추가** (§7) — D3 wiring deferred 정직 박제 + MCT-189 carry over 명시.

## 6. ADR 후보 발의 — ADR-032 evidence triad

### 6.1 발의 근거

3 사례 누적 → "박제 badge ↔ 실상 forcing function 부재" pattern 일반화 의무. cross-document SSOT 강화 룰.

### 6.2 ADR-032 expected sections (counters.json 예약 박제분)

- **§1 trigger** — 3 사례 분석 (MCT-179 §D8 / MCT-182 PMO 일반화 / MCT-189 §D3=C wiring 부재)
- **§2 evidence triad rule** — Story §11 VERIFIED 박제 또는 scope_manifest D-row VERIFIED 박제 시 다음 3 evidence 모두 박제 의무:
  1. **file:line** (실 구현 코드의 파일 경로 + 라인 번호)
  2. **production caller grep ≥1** (production 코드 경로에서 해당 함수/symbol 호출 site grep 결과 ≥ 1건. tests/ 단독 = 미충족)
  3. **integration test result** (해당 deliverable 의 boundary integration test 또는 production smoke evidence)
- **§3 enforcement layer**:
  - scope_manifest schema 확장: `verify_evidence` field 신설 (file_line / caller_grep_paths / integration_test_id 3-tuple)
  - Story §11 박제 의무: `### §11.X D-N VERIFIED — evidence triad` 박스 신설
  - PMO audit gate: PMO Story 완료 감사 시 3 evidence 부재 = audit FAIL (강제 amendment box 박제)
- **§4 Story §8.5 Impl Manifest 와의 통합** — §8.5 가 production caller grep 결과를 매핑표에 포함하면 §2 의 grep evidence 자동 충족 (DeveloperPL self-write 책임 확장)
- **§5 면제 — POLICY_FINALIZED 시 prod evidence carry-over**:
  - Epic POLICY_FINALIZED 박제 시 일부 deliverable 의 production evidence 가 미완 (예: WAL 30G prod 실측, full-stack production smoke) 인 경우 → **prerequisite registry table 명시 의무** (EPIC-RESULTS prod-N carry over table 패턴)
  - prod-N carry over 된 항목은 evidence triad 의 (3) integration test 항목을 "prod-N carry, production deploy 후 별 PR" 로 명시 박제 가능 (단 § 2 의 (1) file:line + (2) caller grep 은 면제 불가)

### 6.3 owner Story

ADR-032 owner = 미정. MCT-189 LAND 시점에 §D3=C amendment box 박제와 동시에 ADR-032 Accepted 후보. 또는 별 governance Story (MCT-NNN, 본 retro LAND 후 사용자 결정).

## 7. EPIC-RESULTS amendment box 의무 (별 PR 또는 본 retro PR 동시)

EPIC-RESULTS-EPIC-tier-promotion-single-source.md 본문에 다음 amendment box 박제 의무:

```markdown
## Amendment — D3=C wiring deferred (2026-05-16 운영 진단 세션 발견)

> POLICY_FINALIZED 2026-05-14 박제 시점에 D3=C "Local delete = NAS HEAD verify + grace 0"
> 정책 finalize 와 `promote_l1()` 함수 정의는 완료됐으나, 실 production 호출 site (runner /
> dual_writer / l1 / l2 / l3) wiring 이 누락됨. 2026-05-16 운영 진단 세션 (사용자 디스크
> 압박 보고 → systematic-debugging Phase 1~3) 에서 발견.

**evidence (2026-05-16)**:
- `git grep -nE "promote_l1\(|from mctrader_data\.compactor\.promotion import" -- 'src/**'` = 0건
- dual_writer.py unlink 호출 = `tmp_path` (atomic temp) 만, L1/L2/L3 source unlink 0
- 결과: production /d/market 130.8 GB legacy Parquet 누적 (NAS 적재는 정상, 로컬 회수만 부재)

**carry over (Epic CLOSED prerequisite 보강)**:
- prod-D3-wiring: **MCT-189** (ADR-029 §D3=C grace-0 로컬삭제 wiring 완결) — RESERVED 2026-05-16
- legacy 130 GB cleanup = MCT-189 §3 S6 검토 대상 (compactor scan retroactive vs oneshot vs 사용자 explicit)
- ADR-029 §D3 amendment box LAND 의무 = MCT-189 AC-6

**관련 lesson 적용**:
- ADR-032 (Proposed, PMO 발의 2026-05-16) — VERIFIED badge evidence triad 의무화. 본 사례가 trigger 3번째.

본 amendment box 박제 = POLICY_FINALIZED 정직성 보강. Epic Status 강등 아님 (10/11 D 정상, D3 wiring deferred only).
```

## 8. carry over registry (PMO 측 trace)

| # | carry over | owner | timing |
|---|------------|-------|--------|
| C1 | MCT-189 (§D3=C wiring 완결) — Story 완료 시 별 RETRO-MCT-189.md 작성 + EPIC-RESULTS amendment box 갱신 + ADR-029 §D3 amendment box 박제 | MCT-189 owner | Story LAND |
| C2 | ADR-032 본문 author + Accepted transition | MCT-189 LAND 시점 동시 author 또는 별 governance Story | MCT-189 LAND 또는 별 Story |
| C3 | image 재배포 trigger 일반화 (Drift A 측 forcing function) — ADR-030 amendment box 또는 별 ops runbook | EPIC-mctrader-docker-stack carry (prod-1 amend 시) | 별 PR |
| C4 | mctrader-data main HEAD 빌드 가능 상태 회복 — vendor wheel `mctrader_market` 재빌드 (market#11 4902b53c base) | 별 follow-up | mctrader-data 별 PR |
| C5 | mctrader-engine-paper crash-loop + signal-announcement / signal-fear-greed Exited(255) 2일+ 방치 | 별 ops 사안 (본 retro 본문 외) | ops chore |
| C6 | WAL 30G hard 위반 (38 GB) — backfill 무한 루프 stop 완료, WAL gc 24h grace 자연 드레인 monitoring | 24h drain 후 자연 해소 verify (또는 PMO audit 별 trigger) | 자연 드레인 |

## 9. 정직 박제 — 본 PMO retro 가 무엇을 못 박제하는가

- **MCT-156/162/160 3-cycle 패턴과의 정합**: EPIC-tier-promotion-single-source 자체가 "review lane PASS vs production 실측 결함" 의 해소 Epic 으로 발의됐는데 (EPIC-RESULTS §Epic Summary), Drift B 가 정확히 그 동일 pattern 의 4번째 재현. 즉 Epic 의 raison d'être 가 Epic 자체에서 1회 재현됨. 본 retro 는 이를 정직 박제하나 Epic CLOSED 의 production evidence quad (prod-1~4) 가 강화 evidence triad 적용 시 어디까지 효과적일지는 향후 별 audit 의무.
- **이미지 재배포 forcing function 의 표준화 부재**: 본 retro 가 Drift A 응급 조치 + ADR-032 §5 carry-over 박제만 다룸. 일반화 자체 (ADR-030 amendment box 또는 별 ops runbook) 는 carry C3 로 미룸.
- **MCT-189 §3 S6 cleanup 처리 option 결정**: 본 retro 가 결정하지 않음. MCT-189 설계 lane (Q1 + Q2) 에서 결정.

## Cross-ref

- 본 retro: `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- 발의 Story: `docs/stories/MCT-189.md` (RESERVED)
- ADR 후보: `.codeforge/counters.json` ADR-032 reservation
- amendment 대상 1: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` (D3=C wiring deferred amendment box)
- amendment 대상 2 (MCT-189 LAND 시): `docs/adr/ADR-029-tier-promotion-single-source.md` §D3 amendment box
- 관련 1번째 사례: `docs/retros/RETRO-MCT-179.md` (ADR-030 Out-of-scope reconcile c8e4b8e)
- 관련 2번째 사례: `docs/retros/PMO-AUDIT-MCT-182.md` (PMO 일반화)
- production 시점 image: `mctrader-data:pilot` (2026-05-13T15:51:28Z → 2026-05-16 신 이미지 재빌드)
