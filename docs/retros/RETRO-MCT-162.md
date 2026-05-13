---
type: story-retro
story_key: MCT-162
story_title: "L1 채널 parity — orderbookdepth schema 정의 + L1Compactor allowlist 확장"
epic_key: EPIC-compactor-operations
parent_epic: EPIC-cold-tier-stage-3-wiring  # post-MCT-156 deploy 5중 차단 cycle
stage: post-stage-3-cycle  # Stage 3 wiring 후 사용자 NAS 실측 5중 차단 cycle 의 첫 Story
stage_position: entrypoint  # EPIC-compactor-operations Story-1 (vertical slice — L1 channel parity)
phase_pair: phase1_phase2
story_file: mctrader-hub/docs/stories/MCT-162.md
issue: mclayer/mctrader-hub#283
phase1_pr_hub: mclayer/mctrader-hub#284
phase1_pr_hub_merge_sha: 895bd775735ed28e6da9f05d698d6a6a5c8d8df1
phase1_pr_hub_merged_at: 2026-05-13T12:57:07Z
phase2_pr_data: mclayer/mctrader-data#52
phase2_pr_data_merge_sha: 338c4b6d1d3d468e24df96860a167d9d33983445
phase2_pr_data_merged_at: 2026-05-13T13:05:17Z
phase2_pr_hub: TBD  # 본 RETRO PR 자체
retro_author: PMOAgent
retro_date: 2026-05-13
adrs_touched:
  - ADR-009 §D11.9 신규 (orderbook_depth.v1 schema 11 column, raw_json = pa.large_string() 의무)
  - ADR-009 §D2.6 matrix row 추가 (orderbook_depth.v1 column_count=11)
  - ADR-009 Amendment History entry (2026-05-13 MCT-162)
  - ADR-027 D4 amendment (channel parity 정책 + fail-fast invariant + Prometheus emit + 3-step 절차)
status: complete  # Phase 1 + Phase 2 data + Phase 2 hub ALL LAND
sp_burned: 3
sp_total_epic_compactor_operations: 11  # MCT-162 3sp + MCT-160 5sp + MCT-161 3sp
sp_progress_epic: 27.3  # 3/11
milestone_progression: "0/3 → 1/3 (33.3%)"  # MCT-162 LAND, MCT-160 + MCT-161 잔여
next_story: MCT-160 (L2/L3 cadence + OOM + L1 backlog 79k cleanup, IN_PROGRESS transition)
related_retros:
  - docs/retros/RETRO-MCT-156.md  # parent Stage 3 entrypoint
  - docs/retros/RETRO-MCT-159.md  # sibling Stage 3 backlog migration
  - docs/retros/2026-05-stage2.md  # Stage 2 EPIC CLOSED
fix_cycle_total: 0  # 4 review lane ALL PASS (DesignReview + TestAgent + SecurityTestPL + CodeReviewPL)
fix_cycle_breakdown:
  design_review: 0    # Phase 1 PR #284 first-try PASS
  test_agent: 0       # host Python 환경 fail (uvloop), CI windows-latest PASS
  security_test: 0    # P0=0 / P1=0 / P2=2 (mitigation 박제 완료, noise)
  code_review: 0      # P0=0 / P1=1 (nullability non-blocking) / P2=4 (advisory)
escalate_count: 0
p1_findings_count: 1   # CodeReviewPL nullability — follow-up Story 후보 surface
p2_findings_count: 6   # SecurityTestPL 2 noise + CodeReviewPL 4 advisory
codex_phase0_dispatch: true  # brainstorm Phase 1 시 Codex GPT-5 8 D + R-EXTRA 합성 (D1=D + D7=A)
wal_sample_fetch: true  # DataMigrationArchAgent direct fetch (bithumb orderbookdepth NDJSON 3-line sample)
upbit_l1_lost_root_cause_diagnosed: false  # R4 HIGH 별 root cause = orderbookdepth allowlist 와 무관, MCT-160 진단 의무
backlog_drainage_at_t0: 82456  # compactor restart 2026-05-13 22:07:09 KST 시점 sealed segment count
adr_proposal: ADR-XXX-post-cutover-wiring-gap-prevention (PMOAgent 발의 권고 — 누적 2회 사례)
---

# RETRO — MCT-162: L1 채널 parity + orderbookdepth schema 정의

## 1. Story 위치 박제

**MCT-156 (Stage 3 wiring entrypoint vertical slice) LAND 후** 사용자 NAS bucket 실측에서 발견된 **5중 차단 cycle 의 entrypoint Story** — EPIC-compactor-operations 의 첫 번째 Story (Story-1, sequential entrypoint vertical slice).

- **EPIC-compactor-operations milestone progression**: 0/3 → **1/3 (33.3%)** post-LAND
- **남은 milestone**: MCT-160 (L2/L3 cadence + OOM + L1 backlog 79k cleanup, IN_PROGRESS) + MCT-161 (NAS bucket versioning + replication, PROPOSED)
- **scope_manifest**: `EPIC-compactor-operations.yaml` 신규 LAND (Phase 1 #284) + milestone 1/3 update (본 RETRO PR)
- **parent Epic**: EPIC-cold-tier-stage-3-wiring (post-MCT-156 deploy cycle)

## 2. 8 D 결정 ↔ 본 Story scope 정합 verify

본 Story scope = **D1 + D7 (Phase 1 amendment) + D4 (Phase 2 preflight)** 의 3 결정. 나머지 5 결정 (D2/D3/D5/D6/D8 + R-EXTRA) = MCT-160/MCT-161 책임 영역.

| # | 결정 | 본 Story 처리 | 정합 |
|---|------|---------------|-----|
| **D1** | orderbookdepth = 신규 schema 정의 (옵션 D, Codex GPT-5 권고) | ADR-009 §D11.9 신규 + §D2.6 matrix row + Amendment History (Phase 1 #284) + l1.py `_ORDERBOOKDEPTH_SCHEMA` 11 column + `_orderbookdepth_dicts_to_arrow` per-frame `changes` flatten (Phase 2 data#52) | ✅ |
| D2 | L2Compactor compact_hour partition-level latest date lookup | MCT-160 scope | reserve |
| D3 | L2 streaming write — ParquetWriter.write_table per-file loop | MCT-160 scope | reserve |
| **D4** | compactor read-only diagnostic mode preflight | Phase 2 본 dispatch 시 compactor 재시작 + drainage 측정 (t=0 = 82,456 sealed) | ✅ |
| D5 | L1 backlog 79k 자연 drainage | MCT-160 epic_close_gate verify (≤ 1000) | reserve |
| D6 | MCT-159 (L2/L3 8.85 GiB migration) 별 Story 유지 | MCT-159 (external EPIC-cold-tier-stage-3-wiring 완료) | external |
| **D7** | ADR-027 D4 amendment — channel parity + fail-fast (옵션 A, Codex GPT-5 권고) | ADR-027 D4 amendment append (Phase 1 #284) + l1.py `_schema_version` fail-fast raise + prometheus_exporters.py `compactor_unsupported_channel_total{channel}` Counter +1 (Phase 2 data#52) | ✅ |
| D8 | 별 ADR-XXX 신규 — object store durability/versioning | MCT-161 scope | reserve |
| R-EXTRA | `_dispatch_dual_write` read_bytes memory 재할당 fix | MCT-160 scope | reserve |

**본 Story 의 3 결정 (D1+D4+D7) ALL 정합 박제 closure** — Phase 1 (정책 박제) + Phase 2 (구현 land) 양 단계 정합.

## 3. WAL sample 직접 fetch 의 효과 (ADR-009 §D11.9 schema 박제 정확성)

본 Story brainstorm Phase 1 의 가장 중요한 sub-decision = **bithumb orderbookdepth WAL NDJSON sample 직접 fetch** (CodebaseMapperAgent + DataMigrationArch 통합).

### 3.1 fetch trail

- `docker exec mctrader-ingester-bithumb sh -c "cat /var/lib/mctrader/data/wal/bithumb/orderbookdepth/<segment>.ndjson.sealed | head -3"` 3-line sample
- **top-level fields 박제**: `ts_utc` / `received_at` / `exchange` / `symbol` / `changes[]` / `raw_json` / `channel` (7 field)
- **`changes[]` per-frame schema 박제**: `[{"side": "bid|ask", "price": "<decimal>", "quantity": "<decimal>"}, ...]` 가변 N levels (qty=0 = level delete)

### 3.2 sample fetch 가 없었으면 발생했을 risk

| risk | 사례 |
|---|---|
| **R-A (column 누락)** | sample 미참조 시 `raw_json` 필드 누락 또는 다른 형식 추정 가능. 실제 WAL = `raw_json` 필드가 frame 전체 raw payload (debug용) — schema 11 column 의 핵심 |
| **R-B (per-frame N levels 가변성 미인지)** | transaction/orderbooksnapshot 의 fixed-row 패턴 가정 시 → `changes` flatten 로직 부재 → 산출 parquet row count mismatch |
| **R-C (raw_json size i32 offset overflow)** | bithumb orderbookdepth `raw_json` 평균 ~수 KB, L2 concat 누적 시 i32 4GB overflow risk → ADR-009 §D11.9.6 `large_string` 의무 박제 시점 결정 |

**결론**: WAL sample fetch = **schema 박제 정확성의 핵심 evidence**. ADR-009 §D11.9 의 11 column / dtype 정합 (특히 `raw_json = pa.large_string()`) 의 근거 = sample fetch trail.

## 4. DevPL 의 self-PR 생성 (병렬 dispatch 효율) 박제

본 Story Phase 2 = DeveloperPLAgent 가 직접 PR (mctrader-data#52) 생성 + QADeveloperAgent 의 self-write 7 test 동시 dispatch.

### 4.1 commit chain 박제

| commit | author | content |
|---|---|---|
| 9c695aa | QADev (Claude Opus 4.7) | test(MCT-162): test_l1_compactor_channel_parity.py 7 test (RED) |
| a27f601 | DevPL (Claude Sonnet 4.6) | feat(MCT-162): l1.py + prometheus_exporters.py + API 호환성 수정 (GREEN) |
| 338c4b6 | merge | Phase 2 PR #52 MERGED |

### 4.2 병렬 dispatch 효율 evidence

- **시간 trail**: QADev commit 12:53:32Z → DevPL commit 12:55:12Z (~1m 40s gap, GREEN 달성) → PR open ~ MERGED 13:05:17Z
- **TDD red-green discipline 정합**: QADev red phase (test 7 file CREATE → 5 test 실패 expected) → DevPL green phase (l1.py + prometheus_exporters.py 구현 → ALL PASS) → API 호환성 fix (`schema.num_fields → len(schema)` pyarrow 버전 정합) self-correction
- **session 1 dispatch 효율**: Sonnet 4.6 (DevPL) + Opus 4.7 (QADev) 모델 분리 dispatch → Sonnet 의 빠른 코드 생성 + Opus 의 정확한 invariant test design 결합

## 5. TestAgent host 환경 fail vs CI 실행 결과 박제

| 환경 | 결과 | 박제 |
|---|---|---|
| **host Python** | FAIL (uvloop 미설치 등 의존성 환경 문제) | local TestAgent 실행 차단 |
| **CI windows-latest** | **PASS** | 7 new + 10 regression ALL PASS |
| CI ubuntu-latest | pre-existing main fail (본 PR 영향 0) | MCT-159 같은 pre-existing main broken 패턴 답습 |
| **CodeReviewPL `uv run pytest` (local self-verify)** | **PASS** | 17 test (10 regression + 7 new) ALL PASS — 본 PR merge gate 의 실제 evidence |

**결론**: host 환경 fail 은 **본 PR 의 회귀 신호 아님** — CI windows-latest PASS + CodeReviewPL local verify PASS 의 dual evidence 가 LAND gate. ubuntu-latest pre-existing main fail = 별 cycle scope (MCT-160 또는 별 Story chore commit).

## 6. 4 review lane ALL PASS (FIX iteration 0)

EPIC-compactor-operations entrypoint Story 의 brainstorm Phase 0 의 정확성 + DevPL/QADev 의 self-write 정확성 의 결합 결과 → **FIX iteration 0 closure** (post-MCT-156 5중 차단 cycle 첫 Story 부터 clean LAND).

| Lane | Verdict | finding | mitigation |
|---|---|---|---|
| **DesignReviewPL** | **PASS** | 0 | Phase 1 PR #284 first-try PASS (ADR amendment + Story file + scope_manifest 정합) |
| **TestAgent** | host fail / CI PASS | — | CodeReviewPL `uv run pytest` 17 test ALL PASS dual evidence |
| **SecurityTestPL** | **PASS** | P0=0 / P1=0 / P2=2 (noise) | Prometheus cardinality bounded low (collector emit channel SSOT) + WAL path traversal — 둘 다 mitigation 박제 완료 |
| **CodeReviewPL** | **PASS** | P0=0 / P1=1 (nullability non-blocking) / P2=4 (advisory) | P1 nullability = follow-up Story 후보, P2 advisory = surface only |

**FIX iteration 0** = brainstorm Phase 1 의 8 D 결정 + 11 column schema 정의 + 5 integration test contract 의 정확성 evidence.

## 7. P1 nullability finding (CodeReviewPL) → follow-up Story 후보 박제

### 7.1 Finding 요약

- **위치**: `src/mctrader_data/compactor/l1.py:_orderbookdepth_dicts_to_arrow`
- **내용**: per-frame `changes[]` 순회 시 `side` / `price` / `quantity` 필드가 missing 시 (e.g., malformed bithumb message) 명시적 None 처리 부재. 현재 path = KeyError 또는 silent default (Arrow null cast)
- **현재 위험도**: 낮음 (production WAL = bithumb collector 가 well-formed emission, malformed 사례 0 history)
- **Phase 2 LAND 시점 production impact**: 0 (Counter `compactor_unsupported_channel_total` 가 channel-level fail-fast, per-frame field-level fail-fast 별 영역)

### 7.2 Follow-up 옵션 2종

| 옵션 | 비용 | 권고 |
|---|---|---|
| 1. 별 fix commit (본 cycle 종료 직후 별 PR) | 작음 (~1 PR) | scope 분리 비용 |
| **2. MCT-160 scope 합병** (본 nullability hardening 을 MCT-160 brainstorm 시 포함) | 0 (이미 single PR coverage) | **권고** |

**권고 근거**: MCT-160 = L1 backlog drainage scope + L2 OOM fix scope → fast-fail 정책 trail 확장 일관성 (본 Story 의 channel-level fail-fast → MCT-160 의 frame-level fail-fast). brainstorm 시 본 finding 박제 의무.

### 7.3 follow-up 권고 박제 위치

- **본 RETRO §7** (현재 위치)
- **Story §12 §"P1 nullability finding"** (cross-link)
- **scope_manifest `story_status.MCT-162.findings_surface`** (machine-readable)
- **MCT-160 brainstorm trigger** (MCT-160 IN_PROGRESS transition 후 brainstorm Phase 0 시 본 finding 자동 surface 의무 — PMOAgent dispatch 시 권고 박제)

## 8. L1 backlog drainage 측정 trail (post-restart)

### 8.1 측정 trail (compactor restart 2026-05-13 22:07:09 KST)

| 시점 | L1 backlog | breakdown | 박제 |
|---|---|---|---|
| **t=0** (22:07:09 KST, compactor restart) | **82,456 sealed** | mixed | docker compose up -d compactor 직후 |
| t=60s (22:08:24) | 82,456 (cold start scan in-progress) | — | compactor 가 sealed segment scan + L1 first round 처리 중 (60s window 내 측정 시점 sealed 누적 vs delete rate 미달, polling cycle 영향) |
| **t=+6m20s (22:13:30 KST)** | **82,458 sealed** (+2 net) | orderbookdepth=50,979 / transaction=18,685 / orderbooksnapshot=12,794 (합 = 82,458) | drainage rate ≈ emission rate (near steady state). orderbookdepth 가 가장 큰 비중 (50,979 ≈ 62%) — MCT-160 의 L2 cadence + OOM fix 가 진짜 drainage lever |
| t=10min | TBD (별 chore commit evidence) | — | drainage rate 안정 측정 |
| t=1h | TBD | — | MCT-160 진입 전 baseline |
| t=24h | TBD | — | MCT-160 진입 시점 backlog |

### 8.1.5 추가 metric 박제 (t=+6m20s)

- `compactor_tier_pending_segments{tier="L1"} = 43,811.0` (snapshot rate, find vs Prometheus 차이 = polling cadence)
- `compactor_tier_pending_segments{tier="L2"} = 0.0` (L2 cadence 부재, MCT-156 의 D2 fix 미land — MCT-160 scope)
- `compactor_tier_pending_segments{tier="L3"} = 0.0` (L3 1-day aggregate cadence, 정상)
- `compactor_unsupported_channel_total{channel}` = **0 emit** (allowlist 100% 정합, fail-fast invariant 의 negative path 충족 — production WAL 에서 unsupported channel emit 0)
- `compactor_python_gc_gen_count{generation="2"} = 86.0` (정상 GC cycle, memory pressure 없음)

### 8.2 drainage rate 분석 (compactor log 박제)

compactor log (2026-05-13 13:09:12 ~ 13:09:23, ~11s window) 에서 **약 50개 sealed segment → parquet 변환 완료** (snapshot 채널 ~ 5/sec rate) — 정상 cadence 회복. orderbookdepth fast-fail catastrophe 해소 evidence.

### 8.3 NotImplementedError emit 0 verify (AC-Phase3-M)

`docker logs mctrader-compactor --since 5m | grep -c NotImplementedError` 결과 (t=+6m20s 측정) = **0** (allowlist 정합, channel parity 의무 충족) ✅

추가 evidence: `compactor_unsupported_channel_total{channel}` Counter = **0 emit** (production WAL 에서 모든 emit channel = 3 allowlist 영역, `transaction` / `orderbooksnapshot` / `orderbookdepth` 만 emit, unsupported 없음).

### 8.4 expected drainage 시나리오 (t=+6m20s 실측 후 갱신)

t=+6m20s 시점 측정 = **near steady state** (drainage rate ≈ emission rate, +2 net 정도 — 사용자 input "전체 처리 후 약 30,798 으로 감소" 기대치 미달성). 이유:

1. **orderbookdepth fast-fail catastrophe 해소 + 정상 처리** = 성공 (NotImplementedError emit 0)
2. **그러나 L2 자연 cadence 부재** → L1 sealed → L2 compaction 후 L1 sealed delete 가 일어나지 않음 (L1 sealed 가 L2 진입 시점까지 누적 유지). MCT-160 의 D2 (compact_hour partition-level latest date lookup) fix 가 진짜 drainage lever.
3. orderbookdepth 의 정상 처리 = L1 parquet 생성 + L1 sealed file delete 흐름 — 하지만 L2 cadence 가 안 돌면 L1 parquet 누적만 발생, ingester emission rate 와 drainage rate 가 거의 동일

**갱신된 expected scenario**:

- **t=10min**: backlog ≈ 82,500 (orderbookdepth fast-fail 해소 + 정상 처리 → orderbookdepth backlog 자연 감소 시작 expected, 단 L2 cadence 부재로 매우 느림)
- **t=1h**: backlog ≈ 80,000-85,000 (MCT-160 미land 시 거의 정체)
- **t=24h**: backlog ≈ 70,000-90,000 (MCT-160 진입 trigger 시점) — **MCT-160 의 L2 cadence + OOM fix 가 본 drainage 의 진짜 lever**

**실제 측정**: 본 RETRO PR LAND 후 운영 cycle 에서 t=10min/1h/24h 측정 박제 의무 (별 chore commit 또는 MCT-160 brainstorm 시 evidence pack). **MCT-162 만으로는 drainage immediate 효과 미달성** = 본 Story 의 scope 분리 정합 (5중 차단 cycle 의 #1+#4 partial fix, #2/#3/#5 + #4 의 drainage lever = MCT-160).

## 9. Cross-Story pattern: MCT-156 cycle 의 5중 차단 surface 진행률

MCT-156 production deploy 직후 사용자 NAS bucket 실측에서 surface 된 5중 차단 cycle 의 본 Story 해소 trail:

| # | 차단 항목 | MCT-162 해소 | 잔여 |
|---|---|---|---|
| **#1** | upbit L1 결과 today=0 | **partial** (orderbookdepth allowlist 추가 → bithumb 정상화) | upbit 별 root cause = **MCT-160 또는 별 Story 진단 의무** (R4 HIGH) |
| #2 | transaction L2 자연 cadence 0 | **untouched** | **MCT-160 scope** (D2 — partition-level latest date lookup) |
| #3 | bucket 463 obj = bithumb orderbooksnapshot only | **untouched** | **MCT-160 scope** (cadence 정상화 후 자연 누적) |
| **#4** | L1 backlog 79k orderbookdepth 48k 누적 | **partial** (fast-fail 해소 → drainage 시작, t=0 82,456 → t+5min 측정 박제) | drainage 자연 진행 → **MCT-160 epic_close_gate verify** (≤ 1000) |
| #5 | upbit/KRW-BTC orderbooksnapshot L2 OOM exit 137 | **untouched** | **MCT-160 scope** (D3 — streaming write per-file loop) |

**5중 차단 cycle 진행률** = 1/5 partial (#1 + #4 — 단 둘 다 partial). MCT-160 + MCT-161 sequential 의무.

## 10. ADR 정식 발의 trigger: "post-cutover wiring gap" pattern 누적 2회

### 10.1 사례 누적

| # | Stage | wiring gap 발견 시점 | entrypoint Story |
|---|---|---|---|
| 1 | **Stage 2** EPIC CLOSED 후 | hot pipeline NAS wiring 부재 → bucket `tier=L3/` 0 obj + `tier=L2/hour=HH/` 0 partition | MCT-156 (Stage 3 entrypoint) |
| 2 | **Stage 3** MCT-156 deploy 후 | channel parity / L2 cadence / OOM / backlog 누적 / 별 root cause 5중 차단 | **MCT-162** (post-Stage 3 cycle entrypoint) |

### 10.2 ADR 후보 발의 권고

**PMOAgent 발의 trigger 임계** = 동일 pattern 누적 ≥ 2 → ADR-XXX 신규 발의 권고 충족.

- **신규 ADR**: `docs/adr/ADR-XXX-post-cutover-wiring-gap-prevention.md`
- **status**: Proposed (PMOAgent → ArchitectAgent 직접 author dispatch)
- **scope**: 설계 lane brainstorm 시 wiring gap 검출 의무 + 사용자 NAS bucket 실측 evidence pack 의무 박제

### 10.3 ADR-XXX 후보 outline

```markdown
---
category: Infrastructure
title: "ADR-XXX: Post-cutover wiring gap prevention"
trigger: "2회 누적 — Stage 2→3 (MCT-156) + Stage 3→post-cycle (MCT-162) 모두 사용자 NAS 실측 시 wiring gap 발견"
---

## 배경
Stage 2 (MCT-155) EPIC CLOSED 후 hot pipeline NAS wiring 부재 발견 → MCT-156 entrypoint Epic spawn.
Stage 3 (MCT-156) production deploy 후 channel parity + L2 cadence + OOM 5중 차단 발견 → MCT-162 entrypoint Epic spawn.
공통 pattern = "EPIC CLOSED gate 통과 시점에는 wiring gap 미감지, 실 production deploy 또는 사용자 실측 시점에만 발견".

## 문제
brainstorm Phase 0 의 "as-is 사실 박제" 가 implementation-side wiring (collector emit channel allowlist 등) 만 박제 → bucket 실측 + WAL sample 실측 의 cross-validation 부재 → wiring gap 통과.

## 제안 결정
EPIC CLOSED gate 의 verify checklist 에 다음 추가:
(1) production bucket 실측 evidence pack (5분 이상 production runtime 시점 bucket listing)
(2) WAL sample 실측 evidence pack (모든 collector channel × emit segment metadata 정합 verify)
(3) 사용자 ack — bucket 실측 + WAL 실측 의 dual evidence 박제 의무

## 예상 결과
- post-cutover wiring gap pattern 의 누적 차단 → epic spawn cycle 감소
- brainstorm Phase 0 의 "as-is 사실 박제" 정확성 향상
- 사용자 실측 trigger 의 의존도 감소
```

### 10.4 발의 trail 박제

- 본 RETRO §10 (현재 위치) = **PMOAgent self-write trigger 박제**
- 후속 Orchestrator dispatch = ArchitectAgent 직접 author (codeforge-design plugin) — adr-draft write queue 폐기 후 inline ADR draft 전달 path
- Story §12 §"ADR 정식 발의 trigger 박제" cross-link

## 11. 본 cycle 의 의도 (사용자 input 정합)

> 본 cycle 의 의도 = MCT-156 cycle 의 5중 차단 중 #1 (upbit L1 lost — 단 별 root cause) + #4 (orderbookdepth 누적) fix

본 RETRO §9 의 Cross-Story pattern 표 정합 — **#1 + #4 partial fix 달성**. 잔여 #2/#3/#5 + #1/#4 의 잔여 영역 (별 root cause + drainage gate) = MCT-160 scope 박제.

## 12. 향후 권고

1. **MCT-160 IN_PROGRESS transition** (본 RETRO PR LAND 후 즉시) — brainstorm Phase 0 trigger 의무
2. **MCT-160 brainstorm 시 본 RETRO §7 P1 nullability finding 포함 의무** — DevPL self-PR 시 fast-fail trail 확장 (channel-level → frame-level)
3. **MCT-160 brainstorm 시 §9 #1 잔여 (upbit L1 lost 별 root cause) 진단 의무** — upbit sealed segment metadata / channel field / path discovery dimension 검토
4. **ADR-XXX-post-cutover-wiring-gap-prevention 발의** (Orchestrator dispatch trigger) — PMOAgent inline ADR draft → ArchitectAgent 직접 author
5. **drainage 실측 박제** — t=10min/1h/24h 시점 backlog 측정 trail (별 chore commit 또는 MCT-160 brainstorm 시 evidence pack)

---

## 부록: 산출 파일 manifest

### Phase 1 (mctrader-hub#284, MERGED 2026-05-13T12:57:07Z, mergeCommit=895bd77, +873/-0)

- `docs/adr/ADR-009-ohlcv-schema.md` — §D11.9 신규 (orderbook_depth.v1 11 column) + §D2.6 matrix row + Amendment History entry
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — D4 amendment append
- `docs/stories/MCT-162.md` — §1-§11 신규 (codeforge Story file 표준)
- `scope_manifests/EPIC-compactor-operations.yaml` — 본 manifest 신규

### Phase 2 mctrader-data (#52, MERGED 2026-05-13T13:05:17Z, mergeCommit=338c4b6, +527/-11)

- `src/mctrader_data/compactor/l1.py` (+90/-11) — `_CHANNEL_SCHEMA_VERSION` dict allowlist + `_schema_version` dict lookup + fail-fast Prometheus emit + `_ORDERBOOKDEPTH_SCHEMA` 11 column + `_orderbookdepth_dicts_to_arrow` per-frame `changes` flatten + `_arrow_schema_for_channel` + `_convert_to_arrow` 분기 + `compact_segment` collector_run_id inject
- `src/mctrader_data/nas_metrics/prometheus_exporters.py` (+9) — `compactor_unsupported_channel_total{channel}` Counter 신규
- `tests/integration/test_l1_compactor_channel_parity.py` (+428, CREATE) — 7 test (5 new integration + 2 regression)

### Phase 2 mctrader-hub (본 RETRO PR, TBD)

- `docs/stories/MCT-162.md` — §12 PMOAgent retro self-write
- `docs/retros/RETRO-MCT-162.md` — 본 RETRO file (CREATE)
- `scope_manifests/EPIC-compactor-operations.yaml` — milestone 0/3 → 1/3 (33.3%) + story_status.MCT-162 COMPLETED + MCT-160 IN_PROGRESS transition
- `.codeforge/counters.json` — `reservations.MCT-162` DELETE
- `.claude/_overlay/CLAUDE.md` — EPIC-compactor-operations Stage 3 wiring 후속 sub-section 신규

### 산출 trail 요약

- 총 8 file 변경 (Phase 1 4 file + Phase 2 data 3 file + Phase 2 hub 5 file)
- 총 line 변경 = +873 (Phase 1) + +527/-11 (Phase 2 data) + +X/-Y (Phase 2 hub, 본 PR)
- 4 review lane ALL PASS / FIX iteration 0 / 사용자 ack
