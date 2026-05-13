# MCT-159 — L2/L3 cold tier backlog NAS migration (brainstorm spec)

**created**: 2026-05-13
**author**: codeforge-brainstorm Phase 0+1+2 (7 agent + Codex GPT-5.4 + Sonnet decider 합성)
**status**: brainstorm LAND (사용자 final confirm 2026-05-13)
**epic**: EPIC-cold-tier-stage-3-wiring (sibling 편입)
**repo**: mctrader-data (primary impl) + mctrader-hub (governance)
**counter**: MCT-159 (LAND, retitle history 박제)

---

## §1 사용자 원문 (verbatim)

> "기존 수집 데이터가 가득 차 있는 것 같은데 S3 minio로 이관 가능하다면 개정된 데이터 경로에 따라 옮기도록 하자"

### Brainstorm trigger 사실 박제 (사용자 NAS bucket + 로컬 disk 실측, 2026-05-13)

- 로컬 disk 사용 = 212 GiB / 1007 GiB (23%), market/ = 124 GiB + WAL = 59 GiB = 183 GiB
- 로컬 cold tier backlog (이관 대상) = orderbooksnapshot L2 6.1G/2305 + L3 2.4G/429 + transaction L2 186M/3335 + L3 154M/1049 = **8.85 GiB / 7118 files**
- NAS bucket `mctrader-market` = 919 MiB / 114 obj (smoke 잔재 915 MiB + market 4.4 MiB hot pipeline 5분 분)
- MCT-156 Phase 2 LAND (mctrader-data#47) 후 compactor 09:22 restart → 09:24 부터 NAS dual-write 정상 (`endpoint=mcnas01.internal.mclayer.it:9000`)
- 사용자 unstaged hot-fix 진행 중: `backfill_orchestrator.py` + `run_backfill.py` 의 `schema_version=*` glob layer 누락 정정 ("Pre-flight hot-fix 2026-05-13" 주석)

---

## §2 WHY 추출 + 명시-실제 일치도 (RequirementsAnalystAgent)

### 근본 동기 3개

1. **디스크 용량 불안 완화** — 현재 23% 사용률 비크리티컬하나 적체 증가 risk 선제 해소 의도
2. **내구성·복구 가능성 확보** — local 단독 보관 risk 회피, S3 MinIO 외부 객체 저장소로 재배치
3. **데이터 정리·운영 표준화** — 신규 schema (`tier=L{2,3}/.../date=D/hour=HH/node=MERGED/`) 정합 정리

### 명시-실제 일치도 = **불일치 가능성 높음**

| 차원 | 명시 | 실제 필요 | 괴리도 |
|---|---|---|---|
| **작업 범위** | "기존 수집 데이터" | cold tier backlog 8.85 GiB vs market 124 GiB vs WAL 59 GiB | 높음 |
| **최종 상태** | "옮기도록 하자" | 복사만? 검증+원본 삭제까지 offload? | 중간 |
| **legacy 포함 여부** | 암묵 | MCT-156 S1+S6 "legacy L2 재이관 0" vs 사용자 표현 재해석 | 높음 |

### 🔴 핵심 위험 surface (R3, HIGH severity)

사용자 명시 동기 (disk 압박 해소) = 본 Story 만으로 **미달성** (4.8% only):
- MCT-159 scope = 8.85 GiB / 전체 backlog ~183 GiB = **4.8%**
- 진짜 disk 압박 원인 = L1 sealed segment **76,200 file (~115 GiB)** + WAL 59 GiB
- L1 sealed 처리 prerequisite = `orderbookdepth` channel FIX (NotImplementedError 영구 fail) + L2 offset overflow FIX (pyarrow large_string)
- → **MCT-160 sequential 의무** (MCT-159 scope 외)

---

## §3 7 Agent Phase 0 통합 결과

### DomainAgent (4 결정점 도메인 사실 박제)

1. **신규 schema reader 호환**: ADR-009 §D2.1 + §D14 fallback (`node=` absent → `node=DEFAULT`, `tier=` absent → `tier=L1`) → mixed layout 자연 양립. ADR-027 D9 amendment 정합.
2. **forward-only invariant (ADR-009 §D12.2)**: local source 보존 + NAS append-only PUT → 정합.
3. **MCT-156 S1/S6 (legacy L2 재이관 0) 적용 영역**: 신규 schema local backlog 는 **비적용 영역** (S2/S7 정합). 단 RETRO-MCT-156 §13.5.2 박제 — S1/S6/S7 전제 깨짐 (legacy NAS 4.2 GiB 손실 확정).
4. **7종 invariant harness (MCT-151) inject 자동 의무** — MCT-153 BackfillOrchestrator 재사용 시 InvariantHarness 자동 적용.

### ResearcherAgent (3 핵심 개념 + 2 unknown unknowns)

- 핵심 개념: (1) forward-only cold tier 영역 정의 (2) dual-write 충돌 안전 backfill window (3) incident note 위치 + EPIC-RESULTS 결합 정책
- **Unknown #1 (critical)**: L1 backlog 124 GiB ≠ L2/L3 8.85 GiB 불일치 → 이관만으로 disk GC 불가능
- **Unknown #2**: `schema_version=*` glob hot-fix 가 backfill prerequisite 인지 별 commit 인지 미정 → 미적용 시 신규 schema path 정합 실패로 MCT-153 재발 위험

### RequirementsAnalystAgent (5 AC + 2 Edge Case + 3 사용자 확인)

5 AC (Given/When/Then) 확정 — §6 Acceptance Criteria 박제. Edge Case 2 = (1) 경로 매핑 실패 quarantine (2) 검증 부분 실패 시 원본 삭제 차단.

### FeasibilityAgent (등급 = 주의 필요, 4 장벽 + 4 ADR 충돌 후보)

**4 장벽**:
1. `backfill_orchestrator.py:596` `"orderbooksnapshot"` 하드코딩 → transaction channel 미커버
2. `_build_chunk_spec` hour partition 박제 누락 → ADR-027 D6 invariant #7 (schema_version pin) FAIL risk
3. chunk 폭증 24x (per-(symbol,day) → per-(symbol,day,hour)) — budget 35min 자연 수용
4. `--nas-partition-root` default = `tier=L2` 고정 → L3 명시 override 의무

**ADR 충돌 후보**:
- ADR-027 D1 (Hive prefix) — `hour=HH` + `node=MERGED` sentinel 신규 도입
- ADR-027 D6 invariant #7 — schema_version pin 정합 boundary
- ADR-009 §D2.1 — `node=MERGED` sentinel vs `node=DEFAULT` fallback
- ADR-017 hot path 무영향 — transaction channel L1→L2 promotion race

### ChangeImpactAgent (확정 4 file + 조건부 3)

| 파일 경로 | AS-IS | DELTA | Story §11 |
|---|---|---|---|
| `nas_migration/backfill_orchestrator.py` | hot-fix `schema_version=*` glob (사용자 unstaged) | channel parametrize + hour key 박제 추가 | YES |
| `scripts/migration/run_backfill.py` | hot-fix `schema_version=*` glob (사용자 unstaged) + evidence pack MCT-153 박제 | evidence pack MCT-159 갱신 + `--channel` flag 추가 | YES |
| `tests/nas_migration/test_backfill_orchestrator.py` | `make_partition_dir` 가 `schema_version=*` 미포함 | fixture 갱신 + L3 tier 케이스 추가 | YES |
| `tests/nas_migration/test_backfill_resumability_chaos.py` | 동일 fixture 패턴 | 동일 갱신 | YES |
| `compactor/runner.py` / `compactor/l1.py` | MCT-156 wiring + channel guard | 조건부 — orderbookdepth FIX 영향 시 (MCT-160 책임으로 분리) | NO |
| `nas_storage/dual_writer.py` / `nas_storage/nas_uploader.py` | MCT-151/150 primitive 안정 | 변경 0 (재사용) | NO |

**🔴 CRITICAL**: 사용자 unstaged hot-fix 가 `_discover_partitions()` 만 수정 → `make_partition_dir()` test fixture 미수정 → **8+ integration test 가 silent 통과 (total_chunks=0 오통과) 위험**. 본 Story 의 Phase 2 의무 항목.

### ContinuityAgent (RETRO-MCT-156 §13 + stage3 runbook 박제)

**이미 결정된 것 (재논의 차단)**:
- DualWriter primitive (MCT-151) 재사용 의무 — 7종 invariant 자동
- NASUploader + RetryQueue + SOPRunner (MCT-150) 재사용 의무
- L1 NAS upload 0 invariant (ADR-017 §D5 + ADR-027 §D5 + MCT-156 S3)
- HTTP 유지 (TLS 0, MCT-155 ADR-027 D2 amend LAND)
- bucket 단일 `mctrader-market` + Hive prefix (ADR-027 §D1)
- forward-only invariant (ADR-009 §D12.2)
- gc_runner D7 7d grace primitive 재사용 (MCT-155)
- EPIC-compactor-operations 신규 Epic 발의 박제 (MCT-160 reserve)

**충돌 가능 ADR**: ADR-027 D4 / D6 / D9 amendment 의무. D7 / D11 변경 0. ADR-009 §D2.1/§D14 fallback 정합 (불변).

### PMOAgent 1st pass (예비 분해)

권고 = (iii) 2 Story 분리 — 사용자 confirm LAND (Phase 1).

---

## §4 Phase 1 — Codex 일괄 review + Sonnet decider 합성

### 8 Open Design Points 최종 결정 (사용자 confirm LAND, 2026-05-13)

| D | 결정 | 옵션 | 근거 summary |
|---|---|---|---|
| **D1** | **(iii)** | MCT-159 이관 only + MCT-160/161 reserve | PMO + RETRO §13 + ResearcherAgent 정합 |
| **D2** | **(b)** | MCT-153 BackfillOrchestrator 재호출 + 2 amendment | 자연 cadence 9.2h 무효 (orderbookdepth FAIL), 신규 script 회피 |
| **D3** | **L2/L3 8.85 GiB only** | L1 backlog = MCT-160 책임 | 사용자 명시 정합 + L1 prerequisite 분리 |
| **D4** | **D4 + D6 + D9 amendment** | D7/D11 변경 0 | Stage3 wiring 확장 + RPO=0 enforce + legacy 무존재 재기술 |
| **D5** | **smoke 별 chore** | MCT-158 연계 | 원인/검증 경로 분리 |
| **D6** | **7d grace 답습** | 보수적 | forward-only + MCT-153 손실 교훈 |
| **D7** | **bucket versioning = MCT-161** | + ADR-027 §D9 축약 박제 | RETRO §13.5.2 만으로 설계 제약 승격 부족 |
| **D8** | **orderbookdepth FIX 비prerequisite** | MCT-160 책임 | scope 분리 정합 |

### Counters reservation LAND (2026-05-13)

```diff
+ MCT-159: "L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 files, channel parametrize + hour key amend)"
+   retitle_history: 기존 "compactor L1 backlog cleanup — ..." → 본 title (brainstorm Phase 1 D1 채택)
+ MCT-160: "compactor L1 backlog cleanup — orderbookdepth channel FIX + L2 offset overflow FIX + MCT-153 손실 박제 retrofit"
+   rationale: 기존 MCT-159 reservation 의 RETRO §13.4+§13.5 3 sub-issue 분리 reserve. disk 압박 진짜 해소 prerequisite.
+ MCT-161: "NAS bucket versioning 활성화 + replication 정책 + MCT-153 손실 재발 방지"
+   rationale: Phase 1 D7 (Codex 권고) — bucket versioning 미활성 = 복구 불가 확정. 본 Story 가 versioning 정책 + replication + 재발 방지 영역.
```

`.codeforge/counters.json` 박제 완료 (`mctrader-hub.next: 160 → 162`).

---

## §5 Acceptance Criteria (RequirementsAnalyst 통합)

### AC-1: 경로 규칙 준수
- **Given**: 이관 대상 범위 (L2/L3 backlog 8.85 GiB / 7118 files) + 제외 범위 (L1 sealed, WAL, smoke/) 문서 확정, 신규 schema 경로 규칙 (`tier=L{2,3}/exchange=X/symbol=Y/date=D/hour=HH/node=MERGED/part-*.parquet`) 정의됨
- **When**: BackfillOrchestrator 재호출 이관 작업 수행
- **Then**: 대상 데이터 **100%** NAS 의 신규 경로 규칙 준수, legacy 경로 혼입 0건

### AC-2: MCT-156 결정 준수
- **Given**: legacy L2 재이관 제외 정책 확정 (MCT-156 S1/S6, RETRO §13.5.2 박제)
- **When**: 이관 계획 + 결과 검토
- **Then**: legacy hour-key 부재 layout 객체 = 대상 + 결과 목록 모두에서 **제외 0건**

### AC-3: 7종 invariant ALL PASS
- **Given**: 로컬 대상 파일 사전 집계값 (파일 수 + 총 bytes + manifest sha256)
- **When**: NAS 이관 완료
- **Then**: (1) sha256 + (2) object count + (3) row count + (4) column count + (5) column name order + (6) dtype identity + (7) schema_version pin **7종 ALL PASS** — 1종이라도 FAIL 시 cutover 차단

### AC-4: MCT-153 손실 박제
- **Given**: backfill 산출물 4.2 GiB 손실 사실 확정 (RETRO §13.5.2)
- **When**: 본 Story 산출물 박제
- **Then**: (a) ADR-027 §D9 축약 amendment LAND (b) MCT-161 reserve cross-link (c) 본 Story §11 데이터 마이그레이션 trace = "local source 보존 → forward-only invariant 위반 0"

### AC-5: 로컬 디스크 압박 해소 (한계 surface)
- **Given**: AC-3 검증 완료 + 원본 삭제 정책 = 7d grace 답습
- **When**: gc_runner D7 grace 경과 후 local delete 실행
- **Then**: 로컬 해제 용량 ≥ **8.85 GiB** + WAL/hot data 무결성 보장. **§1 한계 박제 의무**: "본 Story 만으로 disk 압박 즉시 해소 미달성 (4.8% only) — MCT-160 sequential 의무"

### Edge Case 2건

1. **경로 매핑 실패**: legacy 파일 중 `date`/`hour`/`node` 정보 누락 또는 불일치 → 자동 이관 금지, quarantine 목록 분리, 수동 검토 대상화
2. **검증 부분 실패**: NAS 적재 성공 + 로컬 삭제 전 검증 일부 실패 → 재시도 가능/불가 항목 분리, 검증 완료 전 원본 삭제 차단

---

## §6 Phase 분해 + Test Contract 후보

### Phase 1 (mctrader-hub governance) — docs only, 코드 변경 0

산출물:
- `docs/adr/ADR-027-...md` D4/D6/D9 amendment (D7/D11 변경 0)
- `docs/stories/MCT-159.md` (§1~§11, codeforge Story file 표준)
- `scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml` MCT-159 추가 + S8~S15 결정 박제 + R3-R5 risk 박제
- `.codeforge/counters.json` 이미 LAND (Phase 1 작성 중)
- CLAUDE.md (mctrader-hub + mctrader-data) sections 갱신

### Phase 2 (mctrader-data 구현 + test, mctrader-hub Story §11 self-write SSOT)

**산출물 (확정 4 file + 조건부 3)**:

1. `src/mctrader_data/nas_migration/backfill_orchestrator.py` — 사용자 unstaged hot-fix LAND + channel parametrize (`Literal["orderbooksnapshot","transaction"]`) + hour key 박제 추가 (`_build_chunk_spec` `hour` 축 추가)
2. `scripts/migration/run_backfill.py` — 사용자 unstaged hot-fix LAND + `--channel` flag 추가 + evidence pack MCT-159 갱신
3. `tests/nas_migration/test_backfill_orchestrator.py` — `make_partition_dir()` fixture 갱신 (`schema_version=*` 포함) + L3 tier 케이스 + channel 매트릭스 확장
4. `tests/nas_migration/test_backfill_resumability_chaos.py` — 동일 fixture 갱신 + channel 매트릭스

**Test Contract 7종 (ADR-027 D6 invariant 정합)**:

1. AC-1 — 신규 schema path 100% 준수 (legacy 경로 혼입 0)
2. AC-2 — MCT-156 S1/S6 정합 (legacy layout 객체 제외 0건)
3. AC-3 — 7종 invariant ALL PASS (sha256 + count + row + column + name order + dtype + schema_version pin)
4. AC-4 — orderbooksnapshot + transaction 양 channel ALL PASS
5. AC-4 — L2 + L3 tier 양쪽 ALL PASS
6. AC-5 — Edge Case quarantine 자동 분리 (date/hour/node 누락 시)
7. AC-5 — 검증 실패 시 local delete 차단 (CutoverVerifier gate)

**Perf Baseline**:
- per-chunk = 3s @ 10-parallel (MCT-153 NFR-3 baseline 재사용)
- 7118 files × 3s / 10 ≈ **35 min** (NFR-3 80 min budget 내 margin 45 min)

---

## §7 ADR-027 amendment 본문 초안 (D4 + D6 + D9)

### D4 amendment (Stage 3 wiring obligation 확장)

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — L2/L3 cold tier backlog NAS migration obligation.
Stage 3 wiring (MCT-156 LAND) 후 hot pipeline NAS PUT 정상화 되었으나, wiring _이전_ 로컬 누적
L2/L3 backlog (8.85 GiB / 7118 files, 신규 schema `tier=L{2,3}/.../date=D/hour=HH/node=MERGED/`)
은 자연 cadence 적용 외 영역. 본 amendment = MCT-153 BackfillOrchestrator 의 channel parametrize
(`orderbooksnapshot` + `transaction` 양 channel) + hour key 처리 (`_build_chunk_spec` `hour` 축
추가) 2 amendment 후 재호출하여 LAND-이전 backlog 강제 이관. forward-only invariant + 7d grace +
7종 invariant ALL PASS gate 정합 의무. L1 sealed backlog (~115 GiB) + WAL (59 GiB) = 본 amendment
scope 외 (MCT-160 책임, orderbookdepth FIX + L2 offset overflow FIX prerequisite).
```

### D6 amendment (RPO=0 invariant enforce 명시)

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — backlog migration 의 7종 invariant ALL PASS gate.
본 Story 의 BackfillOrchestrator 재호출 path 가 MCT-151 InvariantHarness inject 자동 동작
(byte-level sha256 + set-level object count + row count + schema-level column count + name order +
dtype + schema_version pin 7종). 1종이라도 FAIL 시 NAS PUT 차단 + retry queue enqueue + SOP
MANUAL_GATE escalation 의무. D6 invariant wording 변경 0 — wiring path 추가만.
```

### D9 amendment (mixed layout 재해석 + legacy 무존재 박제)

```markdown
**MCT-159 amendment 박제 (2026-05-13)** — mixed layout 본문 재해석. ADR-027 §D9 amendment
(MCT-156, 2026-05-13) 본문은 NAS bucket 의 (a) MCT-153 backfill 산출물 = legacy ADR-009 §D2.1
layout + (b) MCT-156 Phase 2 신규 hot pipeline 산출물 = 신규 schema mixed 공존 박제. **그러나**
2026-05-13 deploy verification 실측에서 (a) 4.2 GiB / 1370 obj 의 **NAS 측 손실 확정 박제**
(bucket versioning 미활성 = 복구 불가, RETRO-MCT-156 §13.5.2 박제). 즉 본 시점 NAS bucket 의
mixed layout = (b) 신규 schema only — (a) 사실상 무존재. reader fallback (ADR-009 §D2.1+§D14)
은 본 Story 의 MCT-159 이관 산출물 (`node=MERGED` + `hour=HH`) 도 자연 양립 의무, but legacy
객체 부재로 fallback 의존 0. MCT-153 손실 재발 방지 = MCT-161 reserve (bucket versioning 활성화)
별 Story 책임.
```

---

## §8 위험 박제 (R3-R5)

### R3 (HIGH) — 사용자 명시 동기 본 Story 만으로 미달성

- 정량: 8.85 GiB / 전체 backlog ~183 GiB = **4.8% only**
- mitigation: §1 surface 박제 + MCT-160 sequential 의무 cross-link + Epic milestone description "3-step migration" 명시

### R4 (MEDIUM) — BackfillOrchestrator channel parametrize amend 시 transaction-only path regression

- mitigation: test_backfill_orchestrator.py + test_backfill_resumability_chaos.py 양 channel 매트릭스 확장 + transaction-only path 회귀 test 보존

### R5 (MEDIUM) — hour key 처리 amend 시 기존 NAS file naming convention 불일치

- mitigation: 기존 NAS key naming pattern 사전 측정 + spec amend 시 backward-compat 검증 + ADR-027 D4 amendment 에 key naming 결정 박제

---

## §9 scope_manifest patch (`scope_manifests/EPIC-cold-tier-stage-3-wiring.yaml`)

```yaml
# 신규 추가 entries — story_sequence + design_decisions + risks

story_sequence:
  # ... 기존 MCT-156/157/158 유지
  MCT-159:
    title: "L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 files)"
    sp: 5
    repo: "mctrader-data + mctrader-hub"
    phase_pair: phase1_phase2
    dependency:
      blocked_by:
        - MCT-156  # Stage 3 wiring LAND prerequisite
      reuses:
        - MCT-150  # NASUploader + RetryQueue + SOPRunner
        - MCT-151  # DualWriter + InvariantHarness + CompactionBarrier
        - MCT-153  # BackfillOrchestrator (channel/hour amend 후 재호출)
        - MCT-155  # gc_runner D7 7d grace
    prerequisite_evidence:
      - "MCT-153 산출물 손실 박제 (RETRO §13.5.2)"
      - "L2/L3 backlog 정량 측정 (사용자 NAS bucket + 로컬 disk 실측)"
      - "사용자 confirm 8 D 결정 (Phase 1, 2026-05-13)"
    epic_relation: "sibling (Stage 3 wiring follow-up — backlog migration only)"
    user_motive_warning: "사용자 명시 '이관' 동기 = disk 압박 해소이나 본 Story 만으로 미달성 (4.8% only). MCT-160 sequential 의무 §1 surface 박제."

design_decisions:
  # ... 기존 S1~S7 유지
  S8:
    code: "D1"
    decision: "scope = (iii) MCT-159 이관 only + MCT-160 (3 sub-issue codec FIX) + MCT-161 (versioning) reserve"
    rationale: "사용자 confirm — 본 Epic sibling 편입, 신규 Epic 비추천"
    user_confirmed: true
    user_confirmed_at: 2026-05-13
  S9:
    code: "D2"
    decision: "(b) MCT-153 BackfillOrchestrator 재호출 + 2 amendment (channel parametrize + hour key 처리)"
    rationale: "자연 cadence 9.2h 무효 (orderbookdepth NotImplementedError 영구 fail), 신규 script 회피"
    user_confirmed: true
  S10:
    code: "D3"
    decision: "scope = L2/L3 backlog 8.85 GiB only"
    rationale: "사용자 명시 정합 + L1 backlog ~115 GiB 는 MCT-160 prerequisite chain 책임"
    user_confirmed: true
  S11:
    code: "D4"
    decision: "ADR-027 D4 + D6 + D9 amendment, D7/D11 변경 0"
    rationale: "Codex 권고 + Sonnet decider 합성 — Stage3 wiring 확장 + RPO=0 enforce + legacy 무존재 재기술"
    user_confirmed: true
  S12:
    code: "D5"
    decision: "smoke/ 잔재 915 MiB 별 chore 분리 (MCT-158 연계)"
    rationale: "원인 + 검증 경로 별 도메인, MCT-158 R1 smoke gate 와 책임 경계 명확"
    user_confirmed: true
  S13:
    code: "D6"
    decision: "local GC D7 7d grace 답습 (보수적)"
    rationale: "forward-only invariant + MCT-153 손실 교훈 (즉시 삭제 면제 근거 0)"
    user_confirmed: true
  S14:
    code: "D7"
    decision: "bucket versioning = MCT-161 별 Story / 손실 사실 = ADR-027 §D9 축약 박제"
    rationale: "RETRO §13.5.2 만으로 설계 제약 승격 부족 — versioning 정책 별 Story 책임"
    user_confirmed: true
  S15:
    code: "D8"
    decision: "orderbookdepth FIX = 이관 prerequisite 아님 (MCT-160 책임)"
    rationale: "MCT-159 = 이관 only, codec FIX = MCT-160 책임 분리"
    user_confirmed: true

risks:
  # ... 기존 R1/R2 유지
  R3:
    risk: "사용자 명시 동기 (disk 압박 해소) 본 Story 만으로 미달성"
    severity: HIGH
    quantification: "MCT-159 = 8.85 GiB / 전체 backlog ~183 GiB ≈ 4.8% only"
    mitigation:
      - "§1 surface 박제 — Story 진입 즉시 한계 명시"
      - "MCT-160 sequential 의무 cross-link (#160 reserve LAND)"
      - "Epic milestone description 갱신 — backlog migration 3-step 명시"
  R4:
    risk: "BackfillOrchestrator channel parametrize amend 시 transaction-only path regression"
    severity: MEDIUM
    mitigation:
      - "양 channel test 매트릭스 확장 + transaction-only 회귀 test 보존"
  R5:
    risk: "hour key 처리 amend 시 기존 NAS file naming convention 불일치"
    severity: MEDIUM
    mitigation:
      - "기존 NAS key naming pattern 사전 측정 + backward-compat 검증 + ADR-027 D4 amend 박제"
  R6:
    risk: "make_partition_dir() test fixture 미수정 → 8+ integration test silent 통과 위험"
    severity: HIGH
    quantification: "사용자 unstaged hot-fix `_discover_partitions()` 만 수정 → test fixture 의 `schema_version=*` 누락 → total_chunks=0 오통과"
    mitigation:
      - "Phase 2 첫 step = test fixture 갱신 의무"
      - "TDD red phase (fixture 갱신 → test FAIL → 구현 진행) 강제"
```

---

## §10 의존성 + Sequential 의무

```
MCT-156 (LAND) → MCT-157 (cutover) → MCT-159 (이관, 본 Story)
                                  ↘ MCT-158 (smoke chore, 병렬)
                                  
MCT-159 (이관 LAND) → MCT-160 (L1 codec FIX + 손실 retrofit, sequential 의무)
MCT-160 (LAND) → MCT-161 (versioning 활성화, sequential 의무)
```

- MCT-159 ↔ MCT-158: **병렬 가능** (수정 경로 disjoint)
- MCT-159 → MCT-160: **순차 의무** (BackfillOrchestrator amendment 재사용)
- MCT-160 → MCT-161: **순차 의무** (versioning 활성 상태 대량 이관 storage 비용 회피)

---

## §11 spec → plan handoff

본 spec → `superpowers:writing-plans` 호출 → `docs/superpowers/plans/2026-05-13-mct-159-l2l3-backlog-nas-migration.md` 작성.

plan 산출 시 의무 박제 사항:
- Phase 1 (governance) + Phase 2 (구현) 분리
- ChangeImpactAgent 박제 확정 4 file + 조건부 3 file
- Test Contract 7종 (AC-1~AC-5 + Edge Case 2)
- Perf Baseline (35 min @ 10-parallel)
- TDD red phase 강제 (test fixture 갱신 first)
- ADR-027 D4/D6/D9 amendment 본문 §7 박제 그대로

---

**brainstorm spec LAND** — codeforge-brainstorm skill Phase 0+1+2 완료. `superpowers:writing-plans` handoff.
