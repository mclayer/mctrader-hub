# EPIC-tier-promotion-single-source 별 세션 prompt — L1 NAS 저장 + 로컬 용량 제한 + tier promotion 후 local delete

> **사용법**: 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 에서 본 파일 전체 내용을 paste. Claude 가 자동으로 prerequisite 확인 + 현재 진행 상태 resume + 다음 Story 진입.
>
> **resumable**: 본 prompt 는 idempotent. 매 세션마다 paste 가능, scope_manifest milestone 확인 후 LAND 안 된 다음 Story 부터 진입.
>
> **예상 총 소요**: 6 Story × ~5-9h = **30-50 hour** (사용자 환경의 review/CI/dispatch 효율 의존). 1 session 으로 끝까지 불가, **각 Story LAND 후 새 세션 열고 본 prompt 다시 paste 권고** (context 폭증 방지).

---

## 작업 instruction (paste 시작)

EPIC-tier-promotion-single-source 자율 진행. Cold tier governance v2 — NAS = single source of truth 전면 재설계.

### 사용자 directive (autonomous)

사용자 명시 (2026-05-14):

1. **L1 도 NAS dual-write** — collector WAL → L1 ParquetWriter atomic 직후 NAS PUT 의무. ADR-027 §D5 "L1 NAS upload 금지" invariant 폐기.
2. **상위 tier promotion 후 local delete** — L1 → L2 promote 시 L1 local 삭제, L2 → L3 promote 시 L2 local 삭제. NAS = single source of truth, local = ephemeral cache only.
3. **ambiguity 차단** — 현재 dual-storage (local + NAS) 의 "어디까지가 진실의 source 인지" 모호함 차단
4. **WAL Local 유지** — WAL = local only (hot path zero-loss, ADR-017 정합)
5. **로컬 용량 제한** — WAL 30 GB + L1 20 GB + NAS 500 GB target + host 200 GB hard limit. 임계 도달 시 (D5 capacity-bounded) collector ingest block.

사용자 명시 "시간 없다 + 적극 병렬" + autonomous 자율 진행.

### Cross-Epic Prerequisite (MUST LAND 우선)

본 Epic 진입 전 다음 2 Story LAND 의무 (D9=A 정합):

- **MCT-161** (NAS bucket versioning + cross-NAS replication + MCT-153 손실 재발 방지)
  - prompt: `docs/superpowers/prompts/MCT-161-session-prompt.md`
- **MCT-163** (DualWriter 내부 streaming + L2/L3 row-batch + ADR-009 D7 amend)
  - prompt: `docs/superpowers/prompts/MCT-163-session-prompt.md`

**prerequisite 확인 명령 (본 prompt 시작 시 의무)**:

```bash
cd c:/workspace/mclayer/mctrader-hub && git fetch origin main && git pull origin main
python -c "
import json, io
with io.open('.codeforge/counters.json', encoding='utf-8') as f:
    d = json.load(f)
m161 = 'MCT-161' in d['reservations']
m163 = 'MCT-163' in d['reservations']
print(f'MCT-161 reservation still active (NOT yet LAND): {m161}')
print(f'MCT-163 reservation still active (NOT yet LAND): {m163}')
if m161 or m163:
    print('⚠ Prerequisite NOT YET LAND. 별 세션에서 MCT-161 + MCT-163 먼저 진행 의무.')
    print('  - MCT-161 prompt: docs/superpowers/prompts/MCT-161-session-prompt.md')
    print('  - MCT-163 prompt: docs/superpowers/prompts/MCT-163-session-prompt.md')
else:
    print('✅ Prerequisite ALL LAND. 본 Epic 진입 가능.')
"
```

만약 MCT-161 or MCT-163 reservation 가 여전히 active = 미LAND. **본 Epic 진입 중단** + 사용자에게 prerequisite 진행 권고 후 본 세션 종료.

### Story 분해 (MCT-167-172 sequential)

scope_manifests/EPIC-tier-promotion-single-source.yaml 정합:

| # | Story | scope | mode |
|---|-------|-------|------|
| 1 | **MCT-167** | governance singleton — ADR-NNN-tier-promotion-single-source 신규 + ADR-017/027/009 amend 3건 + DR runbook stub | Phase 1 only (hub) |
| 2 | MCT-168 | L1 NAS DualWriter wiring (compactor hot path, D1 atomic 직후 + D2 retry_queue) | Phase 1+2 (data) |
| 3 | MCT-169 | L1 NAS verify + immediate local delete + tier promotion path 재구성 (D3 + D10 invariant) | Phase 1+2 (data) |
| 4 | MCT-170 | engine reader 재구현 — L1 tier 추가 + reader NAS-first + DR mode | Phase 1+2 (engine) |
| 5 | MCT-171 | DR runbook 본문 + invariant 8종 + 용량 제한 정책 (D4=B + D5 + D6 + D11 4 layer) | Phase 1+2 (hub+data) |
| 6 | MCT-172 | EPIC 통합 smoke + ambiguity invariant verify + EPIC CLOSED | Phase 1+2 (hub+data+engine) |

순서: **MCT-167 → MCT-168 → MCT-169 → (MCT-170 ∥ MCT-171) → MCT-172** (Phase 4 = MCT-170/171 parallel).

### 진행 상태 resume 명령

매 세션 시작 시 의무:

```bash
cd c:/workspace/mclayer/mctrader-hub && git pull origin main 2>&1 | tail -2
python -c "
import json, io
with io.open('.codeforge/counters.json', encoding='utf-8') as f:
    d = json.load(f)
import io as _io, sys
sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
for k in ['MCT-167','MCT-168','MCT-169','MCT-170','MCT-171','MCT-172']:
    active = k in d['reservations']
    print(f'{k}: reservation active = {active} ({\"PROPOSED\" if active else \"COMPLETED\"})')
"
```

reservation 미active = LAND. 다음 진행 Story = 첫 active reservation.

### 단일 Story cycle 진행 의무 (모든 MCT-167-172 공통)

각 Story 진입 시 다음 cycle 자율 수행:

1. **codeforge:codeforge-brainstorm 호출** (Phase 0 자동 4-agent burst). ARGUMENTS 본문:

```
MCT-XXX — [Story title from scope_manifest]

## Story scope (counters.json + scope_manifest 정합)
[해당 Story 의 rationale + scope_manifest design_decisions 박제]

## Cross-Epic 의존
- 본 Story = EPIC-tier-promotion-single-source Story-N (총 6)
- prerequisite: MCT-161 + MCT-163 (LAND 의무)
- 본 Story LAND 후 다음 진입: MCT-XXX+1

## 사용자 directive
- 사용자 명시 "시간 없다 + 적극 병렬" + autonomous 자율 진행
- L1 NAS dual-write + tier promotion 후 local delete + WAL local + 용량 제한 (D1-D11 박제 정합)

## 의무
- Phase 0 4-agent burst → Codex review → Sonnet 합성 → 사용자 final OK 권고 → PMO 2nd pass → spec/plan → Phase 1 worktree + ArchitectPL + DesignReview + admin merge → Phase 2 worktree + DevPL + QADev + Test + Security + CodeReview + admin merge → PMOAgent retro
- Codex 권고 일괄 dispatch 패턴 (Q-by-Q 사용자 stop 금지)
```

2. **Codex review 일괄 dispatch** (모든 open design 결정점 한번에). Sonnet 합성 후 사용자 final OK 권고.

3. **Phase 2 PMO + spec/plan 작성** + chore commit + Issue 생성 (+ scope_manifests 갱신 의무 — 본 Story 의 milestone IN_PROGRESS 박제)

4. **Phase 1 worktree + ArchitectPL dispatch** (codeforge-design plugin) + DesignReviewPL 검수 + admin merge

5. **Phase 2 worktree 2-repo (data + hub, MCT-170 은 engine repo 추가)** + DeveloperPL + QADev parallel + TestAgent + SecurityTestPL + CodeReviewPL + admin merge

6. **PMOAgent retro** (RETRO-MCT-XXX.md + Story §12 + counters DELETE + scope_manifest milestone update + CLAUDE.md + DR runbook 본문 박제)

7. **본 Story LAND 후 사용자 보고** + 다음 Story 진입 권고

### Story 별 핵심 사항

#### MCT-167 (governance singleton)

- **산출**: 신규 ADR `ADR-NNN-tier-promotion-single-source.md` (D1-D11 박제) + ADR-017 §3 D3 amend + ADR-027 §D9 amend + ADR-009 §D12.2 amend + DR runbook stub `docs/runbooks/nas-bucket-disaster-recovery.md` + Story §1-§11
- **Phase 1 only** (docs only, 코드 변경 0)

#### MCT-168 (L1 NAS DualWriter wiring)

- **D1=B**: L1 ParquetWriter atomic 직후 NAS PUT
- **D2=B**: 기존 DualWriter retry_queue + local_only status 재사용
- **MCT-163 prerequisite 필수**: DualWriter 내부 streaming (data=Path) 활용 — L1 PUT latency 완화
- **산출**: `compactor/runner.py` L1 write path + `compactor/l1.py` NAS PUT hook + retry_queue
- **NFR**: L1 PUT p99 < 1500ms (NAS LAN PUT baseline + MCT-148 T2 ± buffer)

#### MCT-169 (local delete + promotion path)

- **D3=C**: NAS HEAD verify + grace 0 (immediate delete after verify)
- **D10=A**: ambiguity invariant violation (NAS object + local file 동시 존재 = test violation)
- **산출**: `compactor/promotion.py` 신규 + `l2.py/l3.py` source read = NAS GET stream + l1.py local delete + invariant test
- **변경 의무**: l2.py compact_hour, l3.py compact_day 의 source read path = local Path → NAS GET ranged read

#### MCT-170 (engine reader 재구현)

- **D7=A**: 95% cache hit + <100ms p99
- **D8=B**: forward-only + local fallback (migration window 동안)
- **산출**: `mctrader-engine/src/mctrader_engine/io/tier_reader.py` (cold_reader rename + L1 확장) + reader_cache.py L1 LRU + endpoint_router.py
- **cross-repo**: mctrader-engine

#### MCT-171 (DR runbook + invariant 8종 + 용량 제한)

- **D4=B**: WAL local only (사용자 directive)
- **D5=A_modified**: capacity-bounded ingest block
- **D6=B**: bucket versioning + cross-NAS replication (MCT-161 정합)
- **D11**: 4 layer 용량 제한
  - WAL local: 30 GB hard limit → 임계 시 collector ingest block
  - L1 local: 20 GB hard limit → oldest FIFO delete after NAS verify
  - NAS bucket: 500 GB target / 1 TB hard limit → L3 oldest 30day+ cold archive 이전
  - Host disk: 200 GB hard limit → alert + manual cleanup
- **invariant harness 8종**: 기존 7종 + Invariant-8 (L1 NAS PUT verify ↔ local delete atomic 정합)
- **산출**: `docs/runbooks/nas-bucket-disaster-recovery.md` 본문 + `compactor/capacity_guard.py` 신규 + `nas_storage/invariant_harness.py` 8종 확장

#### MCT-172 (Epic-level integration smoke + EPIC CLOSED)

- **산출**: cross-Story e2e (collector → compactor L1 NAS write → local delete → L2 promotion (NAS GET source) → engine reader NAS-first → DR mode degradation) + Epic 종료 gate + EPIC-RESULTS-EPIC-tier-promotion-single-source.md
- **gate**:
  - 6 Story PR ALL MERGED
  - 4 ADR amendment LAND + 신규 ADR LAND
  - DR runbook 본문 + invariant 8종
  - production evidence quad (bucket + log + Prometheus + drainage) ALL PASS
  - PMOAgent retro

### 종료 조건

EPIC-tier-promotion-single-source milestone 6/6 (100%) 도달 시 EPIC CLOSED + EPIC-RESULTS 박제 + PMOAgent ADR-XXX `post-cutover-wiring-gap-prevention` 정식 발의 (codeforge-plugin#620 Fix-1 mctrader-consumer 측 implementation 완료).

### 진행 메모

- 본 Epic = **mctrader 의 cold tier governance v2 전면 재설계**. 매우 큰 scope (6 Story × 4-9h = 30-50h 추산).
- 매 Story LAND 후 새 세션 권고 (context 폭증 방지)
- preflight `docker compose stop compactor` (Phase 2 진입 직전 의무, 각 cycle)
- MCT-148 T2 latency baseline ±15% gate 정합 (cf. ADR-027 §D6 NFR)
- branch race 방지 — 본 working dir branch 확인 + main checkout 후 진행 (memory: "Parallel hub session branch race")
- 사용자 별 작업 (MCT-164/165/166 등 다른 Epic) 진행 중일 수 있음 — counters.json 박제 시 fetch + merge 의무

### 진행 패턴 (모든 Story 공통)

```
1. prerequisite verify (이전 Story LAND 확인)
2. preflight (compactor 정지)
3. counter reservation verify + Issue 생성
4. Phase 1 worktree + ArchitectPL + DesignReview + admin merge
5. Phase 2 worktree 2-repo + DevPL/QADev parallel + Test/Security/CodeReview + admin merge
6. PMOAgent retro + Story §12 + counters DELETE + scope_manifest milestone update + CLAUDE.md
7. compactor 재시작 + drainage 측정 (다음 cycle 의 baseline)
8. 다음 Story 진입 권고 + 사용자 보고
```

### 산출 후 보고 의무

각 Story LAND 시:
- (a) Phase 1 + Phase 2 PR # + merge commit
- (b) 4 review lane 결과
- (c) production 측정 결과 (해당 Story 의 invariant)
- (d) scope_manifest milestone (X/6)
- (e) 다음 Story 진입 권고

EPIC CLOSED 시:
- EPIC-RESULTS doc 박제 위치
- 5중 차단 (MCT-156 cycle 박제) 진척 — 본 Epic 으로 #1/#2/#3/#5 ALL 해소 (#4 drainage lever 는 MCT-160 + MCT-163 정합)
- production evidence quad
- post-cutover wiring gap pattern 누적 종결 (3-cycle 패턴 종결)

---

## paste 끝 — 별 세션에서 Claude 자율 진행

본 prompt 가 resumable + idempotent. 매 세션 paste 가능, scope_manifest milestone 확인 후 진행 위치 자동 결정.

**총 소요 추정**: 30-50 hour (6 Story × 5-9h). 1 session 으로 완료 불가, **각 Story LAND 후 새 세션 권고**.

**Critical risk** (본 Epic):
- R1 HIGH: L1 NAS PUT latency 가 compactor throughput 영향 → MCT-163 prerequisite + MCT-148 T2 baseline ±15% gate
- R2 HIGH: NAS unreachable 시 ingest block (D5) = 시장 실시간 데이터 손실 risk → D11 capacity-bounded + D6 cross-NAS replication
- R3 MEDIUM: WAL local only (D4=B) = sealed→L1 derive fail 시 RPO ≠ 0
- R4 MEDIUM: D3=C version/etag false delete risk
- R5 LOW: MCT-154 engine reader 재구현 (MCT-170) latency baseline 재측정 의무
