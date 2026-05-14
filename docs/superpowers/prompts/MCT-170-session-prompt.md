# MCT-170 별 세션 prompt — engine reader 재구현 (L1 tier 추가 + reader 우선순위 NAS-first + DR mode)

> **사용법**: 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 에서 본 파일 전체 내용을 paste. Claude 가 자동으로 prerequisite verify + brainstorm 답습 + Phase 1 → Phase 2 → PMO retro cycle 자율 진행.
>
> **resumable + idempotent**: 매 세션 paste 가능.
>
> **예상 소요**: brainstorm 30min + spec/plan 30min + Phase 1 1-2h + Phase 2 (cross-repo engine) 3-5h + PMO retro 30min = **~5-9h**.

---

## 작업 instruction (paste 시작)

MCT-170 cycle 자율 진행. EPIC-tier-promotion-single-source Story-4.

### 사용자 directive (autonomous)

사용자 명시:
- "시간 없다 + 적극 병렬" + autonomous 자율 진행
- D7=A 95% cache hit + <100ms p99
- D8=B forward-only + local fallback (migration window 동안)
- engine reader = NAS-first (D10 ambiguity 정합)

### Cross-Epic Prerequisite (ALL LAND 확인 의무)

본 Story 진입 전 다음 prerequisite Story LAND 의무:

- **MCT-167** (governance singleton — ADR-029 + ADR-017 §3 D3 amend + ADR-027 §D5+D7+D9 amend + ADR-009 §D12.2 amend + DR runbook stub) ✓ LAND 2026-05-14 (PR #305 + #306)
- **MCT-168** (L1 NAS DualWriter wiring — D1+D2 impl) ✓ LAND 2026-05-14 (PR #307 + data #59 + #308 + #309)
- **MCT-169** (local delete + tier promotion + ambiguity invariant — D3+D10 impl) ✓ LAND 2026-05-14 (PR #310 + data #60 + #311 + #312)

**prerequisite 확인 명령 (본 prompt 시작 시 의무)**:

```bash
cd c:/workspace/mclayer/mctrader-hub && git fetch origin main && git pull origin main 2>&1 | tail -2
python -c "
import json, io
with io.open('.codeforge/counters.json', encoding='utf-8') as f:
    d = json.load(f)
for k in ['MCT-167','MCT-168','MCT-169']:
    active = k in d['reservations']
    status = 'PROPOSED (NOT LAND)' if active else 'COMPLETED (LAND)'
    print(f'{k}: {status}')
mct170 = 'MCT-170' in d['reservations']
print(f'MCT-170 reservation active (ready to enter): {mct170}')
"
```

기대 출력:
```
MCT-167: COMPLETED (LAND)
MCT-168: COMPLETED (LAND)
MCT-169: COMPLETED (LAND)
MCT-170 reservation active (ready to enter): True
```

만약 MCT-167/168/169 중 하나라도 reservation active = 미LAND → 본 prompt 진행 중단 + 사용자 보고.

### Story scope (counters.json + EPIC scope_manifest 박제)

`.codeforge/counters.json` MCT-170 reservation:

> "engine reader 재구현 — L1 tier 추가 + reader NAS-first + DR mode"
> epic: EPIC-tier-promotion-single-source
> repo: mctrader-engine
> phase_pair: phase1_phase2
> rationale: "MCT-167 LAND 후 진입, D7=A 95% cache hit + p99 <100ms + D8=B forward-only + local fallback migration"

### Background

본 Story = EPIC-tier-promotion-single-source 의 핵심 reader 측 재구현. NAS = single source of truth 채택 (D10 ambiguity invariant 정합, MCT-169 LAND) 후 engine reader 가 NAS GET 우선 + L1 LRU cache + DR mode degradation 의무.

MCT-169 산출물 `compactor/reader_cache.py NullReaderCache placeholder` = 본 Story 의 LRU 구현 후 교체 의무.

기존 engine reader (`mctrader-engine/src/mctrader_engine/io/`) 의 cold_reader 가 local Path scan 가정. 본 Story = NAS-first 재구현 + L1 tier 추가 + cache layer.

### D7 + D8 결정 (ADR-029 박제분)

- **D7=A**: Reader cache 95% hit + <100ms p99 (aggressive cache, NAS-first hot path 체감 지연 억제)
- **D8=B**: forward-only + local fallback (migration window 동안 — 신규 NAS 산출물 reader 우선, legacy local 산출물 fallback)

### 산출물 (cross-repo: mctrader-engine + mctrader-hub)

**mctrader-engine (primary impl)**:
- `mctrader-engine/src/mctrader_engine/io/tier_reader.py` 신규 — cold_reader rename + L1 확장. 우선순위: NAS GET → L1 cache → local fallback (D8=B migration window 한정)
- `mctrader-engine/src/mctrader_engine/io/reader_cache.py` 신규 — L1 LRU cache (95% hit target, p99 <100ms NFR)
- `mctrader-engine/src/mctrader_engine/io/endpoint_router.py` 신규 — NAS endpoint 결정 (`NAS_MINIO_ENDPOINT` env, retry, circuit breaker)
- `mctrader-engine/src/mctrader_engine/io/dr_mode.py` 신규 — DR mode degradation (NAS unreachable 시 local fallback 명시 + Prometheus emit)
- `mctrader-engine/tests/io/test_tier_reader.py` + `test_reader_cache.py` + `test_endpoint_router.py` + `test_dr_mode.py` 신규
- `mctrader-engine/CLAUDE.md` 갱신

**mctrader-data (NullReaderCache 제거)**:
- `mctrader_data/compactor/reader_cache.py` 의 NullReaderCache placeholder = MCT-170 engine 측 LRU 구현으로 contract 정합 + data 측 cache 사용처 검토 (data 측 reader 가 engine cache 활용 패턴 확인)

**mctrader-hub (governance)**:
- `docs/stories/MCT-170.md` §1-§12
- `docs/superpowers/specs/2026-05-14-MCT-170-engine-reader-design.md`
- `docs/superpowers/plans/2026-05-14-mct-170-engine-reader.md`
- `docs/retros/RETRO-MCT-170.md` (PMOAgent dispatch)
- `CLAUDE.md` §engine reader NAS-first + §DR mode + §reader cache
- `.codeforge/counters.json` MCT-170 title 확장 + retitle_history
- `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 3/6 → 4/6 (Phase 2 retro)

### 작업 흐름 (codeforge 표준 cycle, MCT-167/168/169 패턴 답습)

#### Phase 0: brainstorm 자동 진입

ADR-029 D7+D8 박제분 답습. 4 에이전트 burst (Domain / Researcher / Analyst / PMO) 빠르게 dispatch.

```
codeforge:codeforge-brainstorm 호출 시 ARGUMENTS:

MCT-170 — engine reader 재구현 (L1 tier 추가 + NAS-first + L1 LRU cache + DR mode)

## Scope
- mctrader-engine io/ 4 module 신규 (tier_reader / reader_cache / endpoint_router / dr_mode)
- D7=A 95% cache hit + p99 <100ms NFR
- D8=B forward-only + local fallback migration window
- MCT-169 NullReaderCache placeholder → LRU 구현 교체 의무

## 핵심 결정점 (예상)
1. LRU cache 라이브러리 (cachetools / functools.lru_cache / 자체 구현)
2. cache size budget (예: 500MB L1 segments × 50 sym)
3. cache invalidation (TTL vs NAS HEAD verify)
4. DR mode trigger (NAS HEAD 5xx N회 / latency p99 임계)
5. endpoint_router circuit breaker (cooldown / retry)
6. local fallback migration window (timeout / sunset)

## Cross-Epic 의존
- prerequisite: MCT-167 + MCT-168 + MCT-169 (ALL LAND ✓)
- 본 Story = EPIC-tier-promotion Story-4 (총 6 중)
- 본 Story LAND 후: MCT-171 (DR runbook 본문 + invariant 8종 + 4 layer capacity)

## 의무
- Phase 0 4-agent burst → Codex review → Sonnet 합성 → PMO 2nd pass → spec/plan → Phase 1 PR → Phase 2 (cross-repo: engine + data + hub) → PMOAgent retro
- Codex 권고 일괄 dispatch 패턴 (Q-by-Q 사용자 stop 금지)
- cross-repo branch race 회피 (mctrader-engine 별 worktree 또는 별 working dir)
- preflight: engine 정지 후 진입 의무 (mctrader-engine 컨테이너 stop)
```

#### Phase 1: ArchitectPL dispatch (또는 직접 docs only)

ADR amendment 의무 없음 (ADR-029 LAND 후 D7/D8 owner = MCT-170, verify status 박제만).

- Story §1-§11 + spec + plan + counters title 확장 + scope_manifest milestone IN_PROGRESS
- DesignReviewPL → CI green → admin merge

#### Phase 2: DevPL + QADev parallel dispatch (cross-repo)

**mctrader-engine PR (primary)**:
- tier_reader.py + reader_cache.py + endpoint_router.py + dr_mode.py + 4 test
- TDD: failing test → minimal impl → pass → commit
- backward compat: 기존 cold_reader API 유지 (deprecation marker)

**mctrader-data PR (NullReaderCache 정리)**:
- `compactor/reader_cache.py` NullReaderCache placeholder = engine 측 LRU import 또는 deprecation
- 기존 L2/L3 source = NAS GET (MCT-169 LAND) 와 정합 검증

**mctrader-hub PR**:
- Story §8-§12 + RETRO + CLAUDE.md + scope_manifest milestone 4/6 COMPLETED

#### Phase 2 PMOAgent retro

RETRO-MCT-170.md 신규 + Story §12 + counters DELETE + scope_manifest milestone update + CLAUDE.md + EPIC-RESULTS placeholder update.

### 가드레일

1. **D7=A NFR**: reader cache 95% hit (production 측정) + p99 <100ms (synthetic benchmark + production p99)
2. **D8=B migration window**: local fallback path 유지 (MCT-172 EPIC CLOSED 시 sunset)
3. **MCT-169 NullReaderCache 정리**: engine 측 LRU 구현 후 data 측 placeholder 제거 또는 import 변경
4. **Backward compat**: 기존 cold_reader API 유지 (mctrader-engine 외부 caller 회귀 0)
5. **Cross-repo branch race**: mctrader-engine working dir 별 (memory feedback_parallel_session_branch_race)
6. **CI failure auto-recovery** (memory feedback_ci_failure_auto_recovery)
7. **Admin merge autonomy** (memory feedback_admin_merge_autonomy)
8. **PMO retro mandatory** (memory feedback_pmo_retro_mandatory)

### Risk (예상)

- **R1 (High)**: D7 95% cache hit 미달 → reader latency 증가 → backtest p99 회귀. 완화: cache size 보수적 budget + production p99 측정 + 미달 시 size up
- **R2 (Mid)**: DR mode trigger threshold tuning (NAS HEAD 5xx N회 / latency 임계) — 임계 너무 낮으면 false positive, 너무 높으면 detection 지연. 완화: production telemetry + 임계 ADR 박제
- **R3 (Mid)**: local fallback migration window 정의 모호 — MCT-172 sunset gate 명시 필요. 완화: D8=B forward-only + local fallback 정합 ADR-029 D8 박제 인용

### 진행 메모

- 본 Story = cross-repo (mctrader-engine + mctrader-data + mctrader-hub). 3 PR pair 가능 (Phase 1 hub docs only / Phase 2 engine code + data NullReaderCache + hub 박제).
- preflight: engine 컨테이너 stop 의무 (Phase 2 진입 직전).
- production benchmark: D7 p99 측정 = MCT-148 T2 baseline 답습 (NAS LAN PUT/GET latency baseline).
- backward compat: 기존 cold_reader caller (backtest engine, paper engine) 회귀 0.

### 산출 후 보고 의무

- (a) Phase 1 + Phase 2 cross-repo PR # + merge commit
- (b) 4 review lane 결과
- (c) D7 cache hit 95% 측정 결과
- (d) D7 p99 <100ms 측정 결과
- (e) DR mode trigger threshold 박제
- (f) MCT-169 NullReaderCache placeholder 제거 verify
- (g) scope_manifest milestone (4/6)
- (h) 다음 Story (MCT-171 = DR runbook 본문 + invariant 8종 + 4 layer capacity) 진입 권고

### 본 Story LAND 후 다음 진입

**MCT-171** — DR runbook 본문 + invariant 8종 + 용량 제한 정책 (D4=B WAL local + D5=A_modified capacity-bounded ingest block + D6=B versioning+replication + D11 4 layer capacity).

진입 prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md` (resumable, idempotent).

---

## paste 끝 — 별 세션에서 Claude 자율 진행

본 prompt 가 self-contained + resumable. 매 세션 paste 가능, scope_manifest milestone 확인 후 진행 위치 자동 결정.

**Critical risk** (본 Story):
- R1 HIGH: D7 95% cache hit + p99 <100ms NFR 미달 시 backtest engine 회귀
- R2 MID: DR mode threshold tuning (false positive vs detection lag)
- R3 MID: local fallback migration window sunset (MCT-172 gate)

**prerequisite ALL LAND 박제 (2026-05-14)**:
- MCT-167 (governance singleton, ADR-029) ✓
- MCT-168 (L1 NAS DualWriter wiring) ✓
- MCT-169 (local delete + tier promotion + ambiguity invariant) ✓

EPIC-tier-promotion-single-source milestone 3/6 → 본 Story land 시 4/6.
