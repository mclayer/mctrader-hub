# MCT-171 별 세션 prompt — DR runbook 본문 + invariant 8종 확장 + 4 layer 용량 제한 정책

> **사용법**: 새 Claude Code 세션 (working dir = `c:/workspace/mclayer/mctrader-hub`) 에서 본 파일 전체 내용을 paste. Claude 가 자동으로 prerequisite verify + Phase 0 verify (코드/파일 실 verify 의무) + brainstorm + spec/plan + Phase 1 → Phase 2 → PMO retro cycle 자율 진행.
>
> **resumable + idempotent**: 매 세션 paste 가능.
>
> **예상 소요**: brainstorm 30min + spec/plan 30min + Phase 1 docs 1h + Phase 2 wiring (collector ingest block + invariant 8종 + capacity probe) 2-3h + PMO retro 30min = **~4-6h**.

---

## 작업 instruction (paste 시작)

MCT-171 cycle 자율 진행. EPIC-tier-promotion-single-source Story-5 (penultimate).

### 사용자 directive (autonomous)

사용자 명시:
- "시간 없다 + 적극 병렬" + autonomous 자율 진행
- D4=B WAL sealed local only 유지 (사용자 directive)
- D5=A_modified capacity-bounded ingest block
- D6=B bucket versioning + cross-NAS replication (MCT-161 ✓, MCT-174 reserve)
- D11 4 layer capacity (WAL 30G / L1 20G / NAS 500G / Host 200G)

### Cross-Epic Prerequisite (ALL LAND 확인 의무)

본 Story 진입 전 prerequisite Story LAND 의무:

- **MCT-167** (governance singleton — ADR-029 publish + ADR-017/027/009 amend 3건 + DR runbook stub) ✓ LAND 2026-05-14 (PR #305 + #306)
- **MCT-168** (L1 NAS DualWriter wiring — D1+D2 impl) ✓ LAND 2026-05-14 (PR #307 + data #59 + #308 + #309)
- **MCT-169** (local delete + tier promotion + ambiguity invariant — D3+D10 impl) ✓ LAND 2026-05-14 (PR #310 + data #60 + #311 + #312)
- **MCT-170** (engine reader L1 확장 + DR mode 신규 — D7+D8 impl) ✓ LAND 2026-05-14 (PR #314 + data #61 + engine #53 + #315)

**prerequisite 확인 명령 (본 prompt 시작 시 의무)**:

```bash
cd c:/workspace/mclayer/mctrader-hub && git fetch origin main && git pull origin main 2>&1 | tail -2
python -c "
import json, io
with io.open('.codeforge/counters.json', encoding='utf-8') as f:
    d = json.load(f)
for k in ['MCT-167','MCT-168','MCT-169','MCT-170']:
    active = k in d['reservations']
    status = 'PROPOSED (NOT LAND)' if active else 'COMPLETED (LAND)'
    print(f'{k}: {status}')
mct171 = 'MCT-171' in d['reservations']
print(f'MCT-171 reservation active (ready to enter): {mct171}')
"
```

기대 출력:
```
MCT-167: COMPLETED (LAND)
MCT-168: COMPLETED (LAND)
MCT-169: COMPLETED (LAND)
MCT-170: COMPLETED (LAND)
MCT-171 reservation active (ready to enter): True
```

만약 MCT-167/168/169/170 중 하나라도 reservation active = 미LAND → 본 prompt 진행 중단 + 사용자 보고.

### Story scope (counters.json + EPIC scope_manifest 박제)

`.codeforge/counters.json` MCT-171 reservation:

> "DR runbook 본문 + invariant 8종 확장 + 용량 제한 정책 (D4=B WAL local + D5 capacity-based ingest block + D6 versioning+replication)"
> epic: EPIC-tier-promotion-single-source
> repo: mctrader-hub
> phase_pair: phase1_phase2
> rationale: "MCT-167-170 LAND 후, D11 신규 용량 제한 (WAL 30G + L1 20G + NAS 500G target + host 200G hard limit)"

### Background

본 Story = EPIC-tier-promotion-single-source 의 운영 안전성 박제 Story. MCT-167 ADR-029 publish 시 DR runbook **stub** (5 fail mode placeholder + invariant 8종 + 4 layer capacity 표 placeholder) 만 박제. 본 Story = **본문 step-by-step** 작성 + invariant 8종 enforcement + capacity-bounded ingest block 구현.

DR runbook stub 현 상태:
- `docs/runbooks/nas-bucket-disaster-recovery.md` (341 lines, MCT-161 + MCT-167 stub 확장 박제분)
- Epic-level scope 5 fail mode placeholder (L1 NAS PUT fail / NAS unreachable + capacity-bounded / clock drift / rate-limit / replication failover)
- invariant 8종 placeholder (MCT-151 7종 + ambiguity invariant 8번째, MCT-169 LAND)
- 4 layer capacity 표 placeholder

본 Story = stub → **운영 가능 runbook** 격상.

### D4 + D5 + D6 + D11 결정 (ADR-029 박제분)

- **D4=B**: WAL sealed segment local only 유지 (사용자 directive, RPO=0 보장은 D1 단독 의존)
- **D5=A_modified**: NAS unreachable 시 capacity-bounded ingest block (D11 용량 임계 도달 시점에만 block, 정상 운영 시 hot path 영향 0)
- **D6=B**: bucket versioning ✓ (MCT-161 LAND) + cross-NAS replication (MCT-174 reserve, mcnas02 물리 부재 해소 후 진입)
- **D11**: capacity_bounded 4 layer (WAL 30G / L1 20G / NAS 500G target + 1TB hard limit / Host 200G hard limit)

### Phase 0 verify 의무 (MCT-170 lesson)

**[[feedback_phase0_verify_mandatory]] 박제 — 본 Story 진입 시 첫 act**:

session prompt 표현은 가설. 다음 실제 사실 verify 의무:

1. **DR runbook stub 실 상태 verify**:
   ```bash
   wc -l docs/runbooks/nas-bucket-disaster-recovery.md  # 현재 341 lines stub
   grep -n "^## \|^### " docs/runbooks/nas-bucket-disaster-recovery.md  # 섹션 구조
   grep -c "TODO\|placeholder\|MCT-171" docs/runbooks/nas-bucket-disaster-recovery.md  # placeholder count
   ```

2. **invariant 8종 현 상태 verify (MCT-151 InvariantHarness + MCT-169 ambiguity invariant)**:
   ```bash
   ls c:/workspace/mclayer/mctrader-data/src/mctrader_data/nas_storage/ | grep -i invariant
   grep -rn "class.*Invariant\|verify_no_ambiguity\|InvariantHarness" c:/workspace/mclayer/mctrader-data/src/mctrader_data/ | head -20
   grep -rn "MCT-151\|7종" c:/workspace/mclayer/mctrader-data/src/ | head -10
   ```

3. **4 layer capacity 측정 baseline verify (D11 hard limit 정합)**:
   ```bash
   # WAL local size 실측
   du -sh c:/workspace/mclayer/mctrader-data/data/wal/ 2>&1 | head -3
   # L1 local size 실측
   du -sh c:/workspace/mclayer/mctrader-data/data/l1/ 2>&1 | head -3
   # Host disk total
   df -h c:/ 2>&1 | head -3
   # NAS bucket size — production 측정 (mc admin info or mc du)
   ```

4. **collector ingest block 구현 위치 verify (D5 capacity-bounded)**:
   ```bash
   grep -rn "class.*Collector\|ingest_block\|capacity_check" c:/workspace/mclayer/mctrader-data/src/mctrader_data/collector/ | head -20
   ```

5. **NAS replication 의존 (MCT-174 reservation status)**:
   ```bash
   python -c "
   import json, io
   with io.open('.codeforge/counters.json', encoding='utf-8') as f:
       d = json.load(f)
   r = d['reservations'].get('MCT-174')
   import json as j
   print(j.dumps(r, ensure_ascii=False, indent=2) if r else 'MCT-174 reservation 부재')
   "
   ```

Phase 0 verify 결과를 spec §1.2 amendment + counters/scope_manifest retitle 박제 의무 (필요 시).

### 산출물 (cross-repo: mctrader-hub + mctrader-data)

**mctrader-hub (primary)**:
- `docs/runbooks/nas-bucket-disaster-recovery.md` 본문 확장 — 5 fail mode step-by-step (Triage / 진단 / 복구 / Verify / Postmortem)
- `docs/stories/MCT-171.md` §1-§12
- `docs/superpowers/specs/2026-05-14-MCT-171-dr-runbook-capacity-design.md` 신규
- `docs/superpowers/plans/2026-05-14-mct-171-dr-runbook-capacity.md` 신규
- `docs/adr/ADR-029-tier-promotion-single-source.md` §D4 + §D5 + §D11 verify status 박제 (필요 시 amendment)
- `scope_manifests/EPIC-tier-promotion-single-source.yaml` milestone 5/6 IN_PROGRESS → COMPLETED
- `CLAUDE.md` §DR runbook 본문 + §invariant 8종 + §4 layer capacity (3 section append)
- `.codeforge/counters.json` MCT-171 title 확장 + retitle_history (Phase 0 verify 결과 amendment 박제 시)
- `docs/retros/RETRO-MCT-171.md` 신규 (PMOAgent dispatch)

**mctrader-data (capacity probe + ingest block + invariant 8종)**:
- `src/mctrader_data/nas_storage/invariant_harness.py` 확장 — MCT-151 7종 + ambiguity invariant 8번째 통합 (MCT-169 verify_no_ambiguity 답습)
- `src/mctrader_data/collector/capacity_probe.py` 신규 — 4 layer capacity 측정 (WAL + L1 + NAS + Host) + threshold 검사
- `src/mctrader_data/collector/ingest_blocker.py` 신규 또는 기존 collector 측 확장 — D5 capacity-bounded ingest block (D11 임계 도달 시점에만 trigger)
- `tests/integration/test_invariant_harness_8.py` 신규 — 8종 invariant 전수 verify
- `tests/integration/test_capacity_probe.py` 신규 — 4 layer threshold 정확성
- `tests/integration/test_ingest_block.py` 신규 — D11 임계 + D5 ingest block 동작 verify

### 작업 흐름 (codeforge 표준 cycle, MCT-167/168/169/170 패턴 답습)

#### Phase 0: brainstorm 자동 진입 + verify 의무

ADR-029 D4+D5+D6+D11 박제분 답습. 4 에이전트 burst (Domain / Researcher / Analyst / PMO) 빠르게 dispatch. **각 agent prompt 에 verified-via 의무 명시** (ADR-073 §결정 1).

```
codeforge:codeforge-brainstorm 호출 시 ARGUMENTS:

MCT-171 — DR runbook 본문 + invariant 8종 확장 + 4 layer 용량 제한 정책

## Scope
- DR runbook step-by-step 본문 작성 (5 fail mode triage/진단/복구/verify/postmortem)
- invariant 8종 enforcement (MCT-151 7종 + ambiguity 8번째)
- 4 layer capacity 제한 (WAL 30G + L1 20G + NAS 500G target + Host 200G hard limit)
- collector ingest block (D5 capacity-bounded, 정상 운영 시 hot path 영향 0)

## 핵심 결정점 (예상)
1. DR runbook 5 fail mode 우선순위 + escalation chain
2. invariant 8종 enforcement timing (per-write vs periodic sweep)
3. 4 layer capacity probe 주기 (continuous vs N분 sample)
4. ingest block 정책 (immediate vs graceful drain)
5. Prometheus metric 누락 검출 (capacity threshold approaching alert)
6. NAS replication (MCT-174 reservation) trigger timing — 본 Story scope 인지 vs 별 Story
7. WAL 30G hard limit 도달 시 fallback (D4 local only 정합)

## Cross-Epic 의존
- prerequisite: MCT-167 + MCT-168 + MCT-169 + MCT-170 (ALL LAND ✓ 2026-05-14)
- 본 Story = EPIC-tier-promotion Story-5 (총 6 중)
- 본 Story LAND 후: MCT-172 (Epic CLOSED, D9+D10 verify + D8 sunset finalize)

## Phase 0 verify 의무 (MCT-170 lesson — [[feedback_phase0_verify_mandatory]])
- DR runbook stub 현 상태 직접 `wc -l` + `grep` verify (341 lines stub 박제)
- invariant 8종 현 위치 `grep -rn class.*Invariant` mctrader-data
- 4 layer capacity baseline 실측 `du -sh` (WAL/L1/NAS/Host)
- collector ingest block 구현 위치 `grep -rn class.*Collector` verify

## 의무
- Phase 0 4-agent burst → Phase 0 verify 자동 → Codex review → Sonnet 합성 → PMO 2nd pass → spec/plan → Phase 1 PR → Phase 2 (cross-repo: data + hub) → PMOAgent retro
- Codex 권고 일괄 dispatch 패턴 (Q-by-Q 사용자 stop 금지, [[feedback_brainstorm_codex_review_pattern]])
- 4 PR cross-repo sequential or hub primary + data PR follow-on (PMO 2nd pass 결정)
- preflight: production ingest 정상 운영 보장 (collector capacity probe 측정 시 hot path 영향 0)
```

#### Phase 1: 직접 docs 작성 (codeforge story-cutoff-classification doc-only fast-path)

ADR amendment 의무는 verify 후 결정 — ADR-029 §D4/§D5/§D11 verify status entry 박제만 (필요 시 minor amendment).

- Story §1-§11 + spec + plan + DR runbook 본문 확장 + counters retitle + scope_manifest milestone 5/6 IN_PROGRESS
- DesignReviewPL dispatch (DR runbook 5 fail mode 정합 + invariant 8종 design + 4 layer capacity 측정 정확성)
- CI green → admin merge

#### Phase 2: DevPL + QADev parallel dispatch (cross-repo)

**mctrader-data PR (primary impl)**:
- invariant_harness.py 확장 (7종 → 8종)
- capacity_probe.py 신규 (4 layer 측정)
- ingest_blocker.py 신규 (D5 capacity-bounded)
- 3 integration test 신규
- TDD: failing test → minimal impl → pass → commit

**mctrader-hub PR (박제)**:
- Story §11 retro_file + §12 측정 결과 + DR runbook 본문 LAND verify
- scope_manifest milestone 5/6 COMPLETED
- CLAUDE.md 측정 결과 박제 (D11 capacity threshold 실측)

#### Phase 2 PMOAgent retro

`docs/retros/RETRO-MCT-171.md` 신규 + Story §12 + counters DELETE + scope_manifest milestone 5/6 COMPLETED + EPIC-RESULTS placeholder update.

### 가드레일

1. **D4=B WAL local only invariant**: WAL sealed segment NAS PUT 금지 (사용자 directive). 위반 시 invariant test fail.
2. **D5 capacity-bounded trigger**: 정상 운영 시 collector hot path 영향 0 (D11 임계 미도달 시 ingest 정상). 실측으로 verify.
3. **D11 hard limit 정확성**: 4 layer hard limit 실측 검증 (WAL 30G + L1 20G + NAS 1TB + Host 200G). du -sh 실측 + threshold alert verify.
4. **invariant 8종 backward compat**: MCT-151 7종 InvariantHarness API 변경 0 (8종 확장만, 기존 caller 회귀 0).
5. **DR runbook actionable**: 5 fail mode 본문 step-by-step 운영 가능 수준 (placeholder/TBD 0건). 운영자 직접 follow-along 가능.
6. **CI failure auto-recovery** ([[feedback_ci_failure_auto_recovery]])
7. **Admin merge autonomy** ([[feedback_admin_merge_autonomy]])
8. **PMO retro mandatory** ([[feedback_pmo_retro_mandatory]])
9. **Phase 0 verify mandatory** ([[feedback_phase0_verify_mandatory]] — MCT-170 lesson)

### Risk (예상)

- **R1 (High)**: D11 hard limit 미실측 / threshold drift — WAL 30G + L1 20G 등 hard limit 의 base assumption 이 실측 부재면 ingest block false trigger 또는 detection 지연. 완화: Phase 0 verify 시 baseline 실측 + Prometheus continuous probe + threshold ±10% margin.
- **R2 (Mid)**: invariant 8종 enforcement timing — per-write 시 hot path 영향 vs periodic sweep 시 detection lag. 완화: per-write 가벼운 check (NAS+local XOR) + 1h periodic deep sweep hybrid.
- **R3 (Mid)**: DR runbook 5 fail mode 우선순위 — 운영자 actionability 가 fail mode 분기 명확성에 의존. 완화: runbook 첫 페이지 = quick triage flowchart + 각 fail mode 별 step-by-step.
- **R4 (Low)**: MCT-174 (NAS replication, D6 mcnas02 prerequisite) reservation 미LAND — 본 Story 진입 시 D6 cross-NAS replication step 은 "MCT-174 future" placeholder 박제. 완화: MCT-174 reservation rationale 인용 + replication step은 skip but DR runbook 측 future hook 박제.

### 진행 메모

- 본 Story = cross-repo (mctrader-hub + mctrader-data). 3 PR 가능 (Phase 1 hub docs / Phase 2 data code / Phase 2 hub 박제).
- D4=B (WAL local only) = 사용자 directive 우선 (Codex 원 권고 C 거부 박제 ADR-029 §D4 line 165).
- D11 4 layer hard limit 의 NAS 500G target / 1TB hard limit = production 실측 후 finalize (ADR amendment 가능성).
- 후속 MCT-172 (Epic CLOSED) = D9+D10 verify + D8 sunset finalize + 1h production 측정 + EPIC RESULTS author.

### 산출 후 보고 의무

- (a) Phase 1 + Phase 2 cross-repo PR # + merge commit
- (b) 4 review lane 결과
- (c) DR runbook 본문 lines 추가 (stub 341 → 본문 N lines)
- (d) invariant 8종 enforcement 측정 결과 (per-write latency + periodic sweep 빈도)
- (e) 4 layer capacity 실측 baseline 박제 (WAL/L1/NAS/Host 현재 size)
- (f) D5 ingest block 동작 verify (D11 임계 도달 시 trigger + 정상 시 hot path 영향 0)
- (g) scope_manifest milestone (5/6 COMPLETED)
- (h) 다음 Story (MCT-172 = Epic CLOSED + D9+D10 verify + D8 sunset finalize + 1h production 측정 + EPIC-RESULTS author) 진입 권고

### 본 Story LAND 후 다음 진입

**MCT-172** — Epic CLOSED, D9+D10 verify (1h production ambiguity invariant 위반 0) + D8 sunset finalize + EPIC-RESULTS Story-6 entry + Epic milestone 6/6 COMPLETED.

진입 prompt 미작성 — 본 Story LAND 후 PMOAgent dispatch 시 `docs/superpowers/prompts/MCT-172-session-prompt.md` 자동 author 의무.

---

## paste 끝 — 별 세션에서 Claude 자율 진행

본 prompt 가 self-contained + resumable. 매 세션 paste 가능, scope_manifest milestone 확인 후 진행 위치 자동 결정.

**Critical risk** (본 Story):
- R1 HIGH: D11 4 layer hard limit 미실측 시 ingest block false/missed trigger
- R2 MID: invariant 8종 enforcement timing (per-write vs periodic sweep)
- R3 MID: DR runbook 운영자 actionability (5 fail mode 분기 명확성)
- R4 LOW: MCT-174 NAS replication 의존 (D6 future hook 박제로 mitigation)

**prerequisite ALL LAND 박제 (2026-05-14)**:
- MCT-167 (governance singleton, ADR-029) ✓
- MCT-168 (L1 NAS DualWriter wiring) ✓
- MCT-169 (local delete + tier promotion + ambiguity invariant) ✓
- MCT-170 (engine reader L1 확장 + DR mode + reader cache byte budget) ✓ (D7 hit_ratio 0.95 + p99 0.016ms PASS)

EPIC-tier-promotion-single-source milestone 4/6 → 본 Story land 시 5/6.

**Phase 0 verify lessons (MCT-170 박제)**:
- session prompt 표현은 가설. 코드/파일 실 verify (ls / grep / Read) 의무 — `[[feedback_phase0_verify_mandatory]]`
- DR runbook stub 현 상태 (341 lines) + invariant harness 현 위치 + 4 layer capacity baseline 실측 의무
- Phase 0 4 agent prompt 안에 verified-via annotation 의무 (ADR-073 §결정 1)
