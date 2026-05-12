---
type: story-retro
story_key: MCT-150
story_title: "Stage 2 — uploader hardening + retry queue + Prometheus baseline + conditional write smoke + IP-allowlist 재확인"
epic_key: EPIC-cold-tier-nas-minio
epic_milestone: mctrader-hub#4 Epic-cold-tier-stage-2-migration
stage: 2
stage_position: first  # Stage 2 첫 Story
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-150.md
issue: mclayer/mctrader-hub#253
phase1_pr: mclayer/mctrader-hub#254
phase1_pr_merge_sha: d3f8259
phase2_pr_data: mclayer/mctrader-data#42
phase2_pr_data_merge_sha: fc73d44
phase2_pr_data_merged_at: 2026-05-12T21:33:19Z
phase2_pr_hub: mclayer/mctrader-hub#255
phase2_pr_hub_merge_sha: 57940e1
phase2_pr_hub_merged_at: 2026-05-12T21:33:24Z
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched: [ADR-027 (D5 amendment 보류), ADR-009, ADR-016, ADR-017, ADR-026, ADR-033]
status: complete
sp_burned: 5
sp_total_stage_2: 36
sp_progress_stage_2: 13.9
next_story: MCT-151 (8 SP, dual-write atomic primitives + 7종 invariant harness + L1 compaction drain barrier)
codeforge_escalation: mclayer/plugin-codeforge#525
related_retros:
  - docs/retros/RETRO-EPIC-cold-tier-nas-minio-preflight.md
  - docs/retros/RETRO-EPIC-cold-tier-stage-1-complete.md
  - docs/retros/RETRO-MCT-148.md
fix_cycle_total: 5
fix_cycle_breakdown:
  design_review: 2  # FIX#1, FIX#4
  code_review: 3    # FIX#2, FIX#3, FIX#5 (post-RESET)
escalate_count: 1   # FIX#3 max counter → Option A 사용자 confirmed RESET
---

# RETRO — MCT-150: Stage 2 첫 Story (uploader hardening + retry queue + Prometheus baseline)

## 1. Stage 2 첫 Story 위치 박제

EPIC-cold-tier-nas-minio Stage 2 (Cold Tier Migration L2/L3 → NAS MinIO 76GB) 의 **첫 단계, infrastructure floor 박제**. Stage 1 (MCT-147+148+149 MERGED 2026-05-12) 의 ADR-027 status=Accepted + 5 PoC evidence pack + NAS endpoint 가용 ALL PASS 위에서 spawn — phase_pair=phase1_phase2 (impl + TDD), 첫 Story 로서 Stage 2 의 5개 후속 Story 를 위한 fixture base 역할.

**핵심 산출물**:
- mctrader-data: nas_storage/ + nas_metrics/ + ops/ 신규 디렉토리 (총 14 file: 10 src/test/config + 4 `__init__.py` marker), **26 PASS test**
- mctrader-hub: docs/stories/MCT-150.md (1300 line) + scope_manifest Stage 2 overhaul (D2 amend + S1~S12 박제 + planned_files MCT-150~155 nas_storage/nas_metrics rename) + Grafana dashboard JSON + 3 runbook (nas-minio-secret-rotation Step 7 신설 / nas-minio-deploy / nas-minio-cutover-checklist)
- 사용자 directive 정합: RPO=0 (S8 user_confirmed) + HTTP 유지 (S12 user_confirmed) + 데이터 절대 무손실 (verbatim "절대 유실 금지")
- Addresses Stage 2 결정 4점: S4 (PUT-If-None-Match) / S10 (NAS unreachable SOP) / S11 (dual-write disk I/O baseline) / S12 (Stage 2 TLS 재검토 timing)

## 2. Lane 실행 평가 + FIX cycle 5 비용 trail

### 2.1 Lane별 실행 요약

| Lane | 결과 | FIX | 시간 비용 (대략) |
|------|------|-----|----------------|
| RequirementsPLAgent | §1~§5 author + Stage 2 brainstorm spec + scope_manifest 직접 인용 | 0 | 1 spawn |
| ArchitectPLAgent (chief + 6 deputy 통합) | §6~§11 author (CodebaseMapper + Refactor + SecurityArch + TestContractArch + DataMigrationArch + OpRiskArch) | 0 | 1 spawn |
| QADev | §8 Test Contract 4 P0/P1 + 1 P2 Optional + Test 14 file scaffold | 0 | 1 spawn |
| Dev (Phase 1) | §1~§11 박제 + scope_manifest overhaul + runbook Step 7 신설 + Grafana dashboard JSON | 0 | 1 spawn (PR #254 merged) |
| DesignReviewPL | **FIX#1 (P0=0/P1=3/P2=4)** → ArchitectPL re-spawn → PASS | 1 | 1 spawn + 1 ArchitectPL re-spawn + 1 verify spawn |
| Dev (Phase 2 impl, mctrader-data) | nas_storage + nas_metrics + ops + tests scaffold (TDD red→green) | 0 | 1 spawn (PR #42 first push) |
| CodeReviewPL (Codex GPT-5.4 + Claude Opus 4.7 합성) | **FIX#2 (P0=2/P1=3/P2=3)** → ArchitectPL Change Plan + Dev impl 회귀 → 5/8 PASS, 2 NEW FIX#3 | 1 | 1 spawn + ArchitectPL re-spawn + Dev impl 회귀 + verify spawn |
| CodeReviewPL (FIX#3) | dimensional extension P0-NEW-1 + P1-NEW-1 → ArchitectPL + Dev → PASS, 2 NEW P1 spawn ESCALATE | 1 | 1 spawn + verify (max counter 3/3 도달) |
| **ESCALATE → 사용자 Option A confirm** | RESET 의무 trigger | — | 1 turn (user confirm) |
| ArchitectPLAgent (FIX#4 design re-spawn, RESET 구현-리뷰) | §6.2.2 unconditional guard 박제 + §6.7 enum SSOT 박제 + §10 RESET marker 박제 | 1 | 1 spawn (DesignReviewPL FIX#4 verify PASS, code-review counter RESET 0) |
| Dev (FIX#4 impl 회귀) | retry_queue.py:202-216 Stage 1 unconditional 위치 정확 + hard_floor_breached → hard_floor_blocked rename 정합 | 0 | 1 spawn |
| CodeReviewPL (FIX#5, fresh after RESET 1/3) | Codex + Claude 합의, finding 0, axis 5/5 clean, regression 0 | 1 (verify) | 1 spawn |
| SecurityTestPL | 이전 PASS 재사용 (impl scope = 1-block move + invariant test 추가 만, security finding axis 영향 0) | 0 | 0 spawn (재사용) |
| CI | mctrader-data PRIVATE deps PAT pre-existing failure (orthogonal) | — | admin merge override |
| PMOAgent (본 retro) | Story §12 + 본 RETRO file + scope_manifest milestone 갱신 | 0 | 1 spawn |

**총 spawn ~14회** (preflight + Stage 1 사전 박제 trail 가 RequirementsPL → ArchitectPL handoff 비용을 0 으로 환원). 본 Story = Stage 2 첫 phase1_phase2 Story 로 평소 phase1_only Story (~8 spawn) 대비 ~75% ↑.

### 2.2 FIX cycle 5 박제 (max counter 도달 + RESET pattern)

| FIX# | Lane | Verdict | Root cause | Action | Status |
|---|---|---|---|---|---|
| 1 | design-review | FIX (P0=0/P1=3/P2=4) | 설계 (Phase 1 Story design author 미흡) | 7 fix actions: F1 AC-5 runbook step→7 / F2 §8.3 ±15% 단일 gate / F3 Grafana dashboard JSON 산출물 명시 / F4 plan stale 제거 / F5 RetryQueue sqlite-WAL 박제 / F6 rollback 14 file marker 명시 / F7 credential masking invariant | closed |
| 2 | code-review | FIX (P0=2/P1=3/P2=3) | 설계 boundary (§6.2.2 RetryQueue bounded semantics ↔ S8 RPO=0 invariant 충돌) | 8 fix actions: P0-1 quarantine=drop → quarantine=retry-with-backoff 재정의 (Option A) / P0-2 drain() context-aware put + suppress_enqueue 매개변수 / P1-1 queue_bytes Gauge + 10GB alert / P1-2 drain chaos test 실제 NASUploader / P1-3 _get_client() threading.Lock / P2-1 nas_storage/nas_metrics rename / P2-2 ETag fallback false-positive / P2-3 _grace_extended idempotent | closed (5/8 PASS, 2 NEW spawn FIX#3) |
| 3 | code-review | FIX (P0-NEW-1 + P1-NEW-1) | 설계+구현 dimensional extension (P0-1/P1-1 fix 가 boundary 일부만 cover) | P0-NEW-1: hard_floor_blocked propagation — PutResult enum 5종 확장 + put() 가 enqueue() 결과 그대로 propagate (caller contract: queued=persisted, hard_floor_blocked=NOT persisted, source retain) / P1-NEW-1: depth() + bytes_used() include_quarantined 매개변수 (default True, AC-4 threshold under-report 차단) | closed (P0-NEW-1+P1-NEW-1 verify PASS, **2 NEW P1 spawn → ESCALATE Option A redirect, max counter 3/3 도달**) |
| 4 | design-review (RESET 구현-리뷰) | FIX | 설계 박제 incompleteness (FIX#3 dimensional 갱신 시 §6.2.2 unconditional guard 박제 누락 + §6.7/§8.2 13곳 wording desync) | ArchitectPL re-spawn (hub e81b7fb): P1-NEW-2 §6.2.2 enqueue() 진입 흐름 직교 2-stage guard 박제 (Stage 1 unconditional + Stage 2 conditional) + P1-NEW-3 §6.7 caller contract enum naming SSOT 박제 (hard_floor_blocked single string 통일, hard_floor_breached 사용 금지) | closed (DesignReviewPL FIX#4 verify PASS, **design-review counter 2/3, code-review RESET counter 0/3**) |
| 5 | code-review (fresh after RESET 1/3) | FIX (verify PASS) | 구현 (FIX#3 시점 P1-NEW-2 hard_floor check 위치 결함) | DeveloperPL impl 회귀 (mctrader-data 9eb3f40 + hub 2fdf123): P1-NEW-2 Stage 1 unconditional 위치 정확 (retry_queue.py:202-216) / P1-NEW-3 enum SSOT (hard_floor_breached 0 hits) / 신규 test invariant 박제 (test_hard_floor_unconditional_guard_quarantined_heavy GREEN) / Regression 0 (26 PASS) / Story §6.2.2 line-by-line 정합 / CI orthogonal PAT failure 검증 | closed (Codex GPT-5.4 + Claude Opus 4.7 합의, P0=0/P1=0/P2=0, code-review counter 1/3) |

**총평**: phase1_phase2 Story 의 boundary completeness 가 phase1_only governance Story 보다 현저히 ↑ — 5 FIX cycle (design 2 + code 3) + 1 ESCALATE + 1 RESET = Stage 2 첫 Story 단일 Phase 2 진행 비용. ESCALATE → Option A → RESET pattern 의 process 결함 surface trigger = codeforge #525.

### 2.3 codeforge upstream escalation #525 통보 link

본 Story 가 codeforge plugin process 결함 발견 trigger:
- **Issue**: [mclayer/plugin-codeforge#525](https://github.com/mclayer/plugin-codeforge/issues/525) — `[ESC] FIX cycle ESCALATION pattern: design-review ↔ code-review boundary completeness gap (MCT-150 Phase 2 case study)` (OPEN 2026-05-12)
- **5 root cause hypothesis** (consumer 권고):
  1. **ArchitectPL boundary completeness invariants 부재** — FIX#3 P0-NEW-1 dimensional extension surface 시점 ArchitectPL 가 dimension 누락 self-detect 못 함
  2. **wording SSOT 자동화 부재** — FIX#4 P1-NEW-3 의 `hard_floor_breached` ↔ `hard_floor_blocked` desync 13곳 (mechanical rename automation 부재)
  3. **fix-ledger-schema RESET 정책 명세 부재** — FIX#3 max counter 3/3 도달 시 ESCALATE → 사용자 confirm Option A → design-review re-spawn → code-review counter RESET 0 의 정합 명세 부재
  4. **mechanical rename 자동화 부재** — 10 hits living spec rename 시 historical narrative immutable 영역 보존 의무 자동 detection 부재
  5. **dimensional extension anti-pattern** — FIX#2 P0-1 quarantine retry-with-backoff fix 가 §6.7 caller contract enum dimensional 미반영 → FIX#3 spawn → FIX#4 wording SSOT spawn (cascade)
- **MCT-150 측 진행과 독립 (orthogonal)**: codeforge #525 = process 개선 trigger, mctrader-hub 측 MCT-151 진입 차단 0
- **memory CF-5 박제**: `~/.claude/projects/.../memory/project_codeforge_debut.md` (consumer evidence rapid iteration 패턴)

## 3. Cross-Story 패턴 분석 (Stage 1 vs Stage 2 첫 Story 비교)

### 3.1 phase_pair 차이의 비용 정량

| 항목 | Stage 1 (MCT-147+148+149) | Stage 2 첫 Story (MCT-150) | 비율 |
|---|---|---|---|
| **phase_pair** | 3 Story 모두 phase1_only | phase1_phase2 (impl + TDD + 14 file) | — |
| **wall-clock** | ~3시간 4분 (3 Story 단일 day) | ~6.5시간 (단일 day, 5 FIX cycle 포함) | 본 Story 1개 = Stage 1 3 Story 의 ~2.1배 |
| **FIX cycle** | 각 Story 1-2 cycle (총 4 cycle, 평균 1.33/Story) | **5 cycle 단일 Story** | ~3.75배 (per Story) |
| **escalate** | 0 | 1 (FIX#3 max counter → Option A 사용자 confirm RESET) | — |
| **lane spawn 합산** | ~25 spawn (3 Story 평균 8.33/Story) | ~14 spawn (단일 Story) | per Story 1.68배 |
| **upstream escalation** | ADR 후보 1건 (phase-gate-mergeable fast-pass prefix 확장, codeforge plugin) | **codeforge issue #525 신규 발의** (FIX cycle process gap, 5 root cause hypothesis) | phase1_phase2 가 process 결함 surface trigger 역할 |

**판정 1**: phase1_phase2 Story 의 boundary completeness 요구가 phase1_only governance Story 보다 현저히 ↑ — ArchitectPL deputy 6 통합 시 더 엄격한 invariants 필요.

**판정 2**: 본 Story 의 spawn count (14) 가 Stage 1 평균 (8.33) 의 ~1.68배 — phase1_phase2 의 자연스러운 비용 증가 (impl + TDD + chaos test 추가). 단, 5 FIX cycle 자체는 abnormal (phase1_only 평균 1.33 의 ~3.75배) — codeforge process 결함 surface 가 origin.

### 3.2 phase1_phase2 patterns (Stage 2 잔존 5 Story 위험 surface)

본 Story trail 에서 도출되는 잔존 Stage 2 Story 의 위험 surface:

| Story | phase_pair | 예측 risk | mitigation 권고 |
|---|---|---|---|
| MCT-151 (8 SP) | phase1_phase2 | 7종 invariant harness boundary completeness (S5 박제 7종 invariant 의 column dtype identity + schema_version pin 등 dimensional extension 위험) | RequirementsPL/ArchitectPL spawn 시 FIX#3 dimensional extension anti-pattern 경계 박제 의무 (codeforge #525 hypothesis 5) |
| MCT-152 (5 SP) | phase1_phase2 | dual-write window 운영 (시간축) ↔ NAS unreachable SOP 실전 가동 — 본 Story §6.2.4 NASUnreachableSOPRunner 의 1000seg/10GB threshold + 24h gate 가 false positive 또는 false negative 발생 가능 | ADR-027 D5 amendment trigger (S10 박제 mandatory: false → MCT-155 retro 시점 reopen) |
| MCT-153 (8 SP) | phase1_phase2 | 76GB closed-day per-(symbol, day) tuple chunking — 본 Story HEAD-then-PUT idempotency (AC-1) 의 1차 consumer, content-addressable PUT path 정합 검증 의무 | MCT-153 entry 시 본 Story §11 데이터 마이그레이션 §11.3 handoff table 인용 의무 |
| MCT-154 (5 SP) | phase1_phase2 | reader endpoint cutover (cache flush + verify) — 본 Story Prometheus 4종 metric 이 cutover verify input 의 1축 | ADR-027 D4 amendment trigger (S9 박제 mandatory: false → MCT-154 시점 amendment 결정) |
| MCT-155 (5 SP) | phase1_phase2 | local GC + secret rotation 첫 cycle + TLS 재검토 user confirm + RPO=0 검증 회고 — 본 Story retry queue persistent 가 cutover-1s/+1s diff 0 의 prerequisite | ADR-027 D2 amendment trigger (S12 박제 **mandatory** → MCT-155 진입 시 user confirm + amendment 의무) |

### 3.3 Stage 2 의 cross-Story 패턴 트래킹 의무

다음 5 Story 진행 중 모니터링 항목:

1. **boundary completeness gap 재발 여부** — codeforge #525 hypothesis 1 의 입증 또는 반증
2. **wording SSOT desync 재발 여부** — codeforge #525 hypothesis 2 의 입증 또는 반증
3. **max FIX counter 도달 빈도** — Stage 2 5 Story 중 N건 max 도달 시 RESET pattern 정착화 신호
4. **ADR-027 amendment 4건 진행 trail** — D2 (mandatory MCT-155) / D5 (optional 보류) / D6 (mandatory MCT-151) / D4 (optional MCT-154)

## 4. Stage 2 진행 상태 박제

### 4.1 누적 진척

- **MCT-150 = Stage 2 첫 Story 완료** (5 SP, 2026-05-12, Issue #253 closed + PR data#42 + hub#255 ALL MERGED)
- **누적 진행**: 5 SP / 36 SP total = **13.9%**
- **잔존 Stage 2 stories**: MCT-151~155 (5 stories, 31 SP)

### 4.2 다음 Story = MCT-151 (8 SP)

- **scope**: dual-write atomic primitives + 7종 invariant harness + L1 compaction drain barrier
- **addresses**: S2 (L1 compaction quiesce) / S5 (7종 invariant) / S8 (RPO=0 cutover)
- **depends_on**: MCT-150 ✅
- **parallel_with**: MCT-150 (handoff 완료 — 본 Story metric schema freeze + NASUploader API contract 박제로 MCT-151 본격 진입 가능)
- **isolation**: 별도 worktree 의무 (memory feedback_parallel_session_branch_race)

### 4.3 MCT-151 entry 의무 (handoff verify)

본 Story (MCT-150) → MCT-151 handoff 4점:

| handoff item | 본 Story SSOT | MCT-151 consume + verify 의무 |
|---|---|---|
| **Metric schema freeze** | `nas_uploader_*` namespace prefix (§6.2.3 PrometheusExporter 5종 metric: success/fail/latency/queue_depth/queue_bytes) | MCT-151 invariant_harness 가 `nas_invariant_*` prefix 사용 → prefix-disjoint 정합 (collision 0 verify) |
| **NASUploader API contract** | `put(suppress_enqueue: bool = False)` + `PutResult.status` 5종 enum (uploaded/skipped_idempotent/queued/skipped_etag_overwrite/hard_floor_blocked) | MCT-151 dual_writer 가 NASUploader.put() 직접 inject + PutResult.status switch 박제 (caller source 삭제 결정) verify |
| **RetryQueue persistence semantics** | sqlite-WAL 4-state schema + drain backoff [1m/5m/30m/2h] | MCT-152 dual_write_window_runner 가 NAS unreachable transient 처리 시 inject (drain cycle 재PUT 시 HEAD-then-PUT idempotency 1차 방어선) |
| **AC-5 IP-allowlist re-audit (90d cadence)** | runbook `nas-minio-secret-rotation.md` Step 7 신설 (FIX#1 F1 옵션 A) | MCT-155 secret rotation 첫 cycle 시 재실행 의무 |

### 4.4 Stage 2 timeline (전체 phase 분해)

```
Phase 2A: MCT-150 ✅ + MCT-151 parallel_with_handoff (← 다음)
Phase 2B: MCT-151 standalone (atomic primitive vertical slice)
Phase 2C: MCT-152 + MCT-153 parallel (dual-write window + backfill 76GB)
Phase 2D: MCT-154 cutover singleton (reader endpoint flip + dual-write 7d 연장)
Phase 2E: MCT-155 GC + secret rotation 첫 cycle + TLS 재검토 + RPO=0 회고
```

## 5. ADR-027 amendment 후보 박제 status (Stage 2 진행 중 처리 예정)

| Decision | Stage 2 신규 박제 | trigger story | mandatory | 본 Story 시점 처리 |
|---|---|---|---|---|
| **D2 (TLS)** | S12 박제 (HTTP 유지, Stage 2 cutover 후 MCT-155 재검토) | MCT-155 | **mandatory** | 보류 (MCT-155 진입 시 사용자 confirm + amendment) |
| **D5 (NAS unreachable SOP)** | S10 박제 (1000seg/10GB threshold + 24h manual gate) | MCT-150 | optional | **본 Story 종료 시점 amendment 보류** (§5.1 결정, MCT-155 retro 시점 reopen) |
| **D6 (invariant)** | S5 박제 (7종 invariant) | MCT-151 | **mandatory** | 보류 (MCT-151 진입 시 amendment) |
| **D4 (cutover)** | S9 박제 (dual-write 7d 연장) | MCT-154 | optional | 보류 (MCT-154 진입 시 amendment 결정) |

### 5.1 D5 amendment 보류 결정 근거 (PMOAgent recommendation)

본 Story 종료 시점 D5 amendment 처리 결정 = **보류 (defer to Stage 2 종료 시점 = MCT-155 retro)**. 근거:

1. **mandatory: false** — scope_manifest 박제 자체가 optional 명시
2. **본 Story 의 D5 구체화는 §6.2.4 NASUnreachableSOPRunner + §11 데이터 마이그레이션 박제로 완료** — ADR-027 본문 amend 없이 Story file SSOT 가 cross-link 정합 (MCT-152 dual-write window 운영 시 active consume)
3. **MCT-152 dual-write window 실전 운영 결과** 가 amendment input — D5 (1000seg/10GB threshold + 24h gate) 의 실 운영 결과 (false positive rate / SOP MANUAL_GATE 발동 횟수) 박제 후 amend 가 의미 있음. 현시점 amend = 사변 (speculative)
4. **D6 (mandatory MCT-151 trigger) 와 D2 (mandatory MCT-155 trigger) 가 강제** — 두 amendment 가 우선

**잔존 의무**: MCT-155 retro 진입 시 본 결정 reopen + S10 실 운영 데이터 (MCT-152 dual-write 4주 + MCT-153 backfill ~7분) 기반 amendment 결정.

## 6. PMO Cross-Story 감사 메모

### 6.1 사전 박제 trail 의 가치 입증 (Stage 1 패턴 계승)

Stage 1 RETRO-EPIC-cold-tier-stage-1-complete §6 의 preflight 박제 (A 95/100) 패턴이 Stage 2 첫 Story 에서도 그대로 작동:

- **brainstorm spec (`.tmp/brainstorm-cold-tier-nas-minio-stage2.md`, 328 line)** 의 12 결정점 (S1~S12) + Codex (GPT-5) batch review + Sonnet decider 합성 + 사용자 2점 confirm (S8/S12) → Phase 0 자동 burst 결과
- **scope_manifest Stage 2 overhaul** 의 design_decisions (S1~S12 + 4 amendment 후보) + planned_files (MCT-150~155 + nas_storage/nas_metrics rename) + parallelism_decision (5-phase 분해) → ArchitectPL §6 Change Plan author 시 결정 재발견 비용 0
- **Stage 1 trail 직접 인용** (ADR-027 D1~D11 + MCT-148 evidence pack 5 PoC + MCT-147 4중 mitigation) → §1 / §6 / §11 모두 추론 0, transcribe 박제

**판정**: 사전 박제 trail 의 가치가 Stage 2 첫 Story 에서도 입증. 단, phase1_phase2 의 자연스러운 비용 증가 (impl + TDD + chaos test) 와 codeforge process 결함 surface (5 FIX cycle) 는 사전 박제로 회피 불가.

### 6.2 phase1_phase2 boundary completeness 패턴 (재발 여부 트래킹)

본 Story 의 5 FIX cycle = phase1_phase2 의 boundary completeness 가 phase1_only governance Story 보다 ~3.75배 ↑ 의 측정값. Stage 2 잔존 5 Story (MCT-151~155) 의 FIX cycle 평균이 ~5 cycle 정착 시:

- codeforge #525 hypothesis 1 (ArchitectPL boundary completeness invariants 부재) **입증**
- codeforge plugin upstream 측 ArchitectPL prompt 강화 ADR 발의 의무 (예: dimensional extension self-check checklist 추가)
- mctrader-hub 측 ADR 후보 0 (process 개선은 codeforge 측 영역, consumer 영역 박제 의무 0)

본 RETRO 가 트래킹 base — Stage 2 5 Story 종료 시점 RETRO-EPIC-cold-tier-stage-2-complete.md 에서 5 Story FIX cycle 평균 합산 + codeforge #525 hypothesis 입증/반증 박제 의무.

### 6.3 ESCALATE → Option A → RESET pattern 의 정착화

본 Story FIX#3 → ESCALATE → 사용자 Option A confirm → FIX#4 design-review re-spawn → code-review counter RESET 0 → FIX#5 fresh PASS pattern 의 박제:

- **ESCALATE 의무 trigger**: max FIX counter (3/3) 도달 + 추가 finding surface 시 즉시 ESCALATE — Orchestrator 가 사용자 confirm 의무
- **RESET 의무 trigger**: design-review re-spawn 후 code-review counter 0/3 재시작 — fix-event-v1 contract 의무 (Orchestrator 단독 §10 append 독점)
- **codeforge #525 hypothesis 3 (RESET 정책 명세 부재)** = 본 Story 가 첫 입증 case → codeforge plugin upstream 측 fix-ledger-schema 정합 명세 신규 의무

### 6.4 토큰 예산 vs 실제 (참고)

본 Story 의 토큰 비용 정량 추적 = `.claude-work/progress/MCT-150.md` (Orchestrator-owned live progress trace, playbook §14 도입 후 Story). 추정:

- 14 spawn (§2.1 표) × 평균 ~50K input + ~10K output token = ~840K total (대략)
- 5 FIX cycle 비용 = ~5 lane spawn × 평균 = ~250K (FIX cycle 의 ~30% 차지)
- 사전 박제 trail (brainstorm spec + scope_manifest + Stage 1 RETRO) 가 Phase 0 RequirementsPL/ArchitectPL handoff 비용을 ~70% 절감 (재발견 비용 0)

**판정**: phase1_phase2 첫 Story 의 토큰 비용 = phase1_only Story (~400K) 의 ~2.1배 (wall-clock 비율과 정합). FIX cycle 5 회 비용 정량 측정값 = 다음 phase1_phase2 Story (MCT-151) 예산 책정 base.

## 7. 산출물 (PMOAgent self-write 의무)

본 RETRO 가 박제한 산출물:

| 산출물 | path | 작성 path |
|---|---|---|
| Story §12 retro append | `docs/stories/MCT-150.md` §12 | PMOAgent self-write (CFP-36 + CFP-26 Phase 0a) ✅ |
| 본 RETRO file | `docs/retros/RETRO-MCT-150.md` | PMOAgent self-write (Stage 1 RETRO-MCT-148.md 패턴 정합) ✅ |
| scope_manifest milestone 갱신 | `scope_manifests/EPIC-cold-tier-nas-minio.yaml` epic_milestones | PMOAgent self-write (Stage 2 progress 5/36 SP 박제) ✅ |
| PR comment + Issue close | Issue #253 + PR #42 + #255 | Issue #253 already closed 2026-05-12 + PR ALL MERGED — comment skip (Story §12 박제로 충족) |

## 8. 한줄 요약

**MCT-150 Stage 2 첫 Story COMPLETE** — uploader hardening (HEAD-then-PUT idempotency + retry queue sqlite-WAL persistent) + Prometheus baseline (nas_uploader_* 5종 metric + alert) + IP-allowlist 재확인 (Step 7 신설) + NAS unreachable SOP 박제 (1000seg/10GB threshold + 24h gate) — Issue #253 closed + PR data#42 (fc73d44) + hub#255 (57940e1) ALL MERGED 2026-05-12 21:33Z, 14 file + 26 PASS test, addresses S4/S10/S11/S12 4점, **5 FIX cycle (design 2 + code 3) + 1 ESCALATE + 1 RESET pattern** = phase1_phase2 boundary completeness 가 phase1_only Story 보다 ~3.75배 ↑ 측정값, **codeforge upstream issue #525 신규 발의** (5 root cause hypothesis, mctrader-hub 진행과 orthogonal), Stage 2 진행 5 SP / 36 SP = **13.9%**, ADR-027 D5 amendment 보류 결정 (MCT-155 retro 시점 reopen), 다음 = **MCT-151 spawn** (8 SP, dual-write atomic primitives + 7종 invariant harness, MCT-150 metric schema freeze + NASUploader API contract handoff verify 의무).
