# MCT-164 upbit L1 forward-only loss 진단 Story Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MCT-165 V2 verify 잔존 YES trigger 의 root cause 진단 + WAL freeze + ADR-017/027 amendment + channel matrix 박제 + MCT-166 fix Story scope 확정. forward-only invariant 환경에서 진단/freeze 당일 처리 (D6=B).

**Architecture:** codeforge consumer 표준 1 Story = 2 PR pair. Phase 1 hub PR (docs only — ADR amendment 본문 + channel matrix + Story file + counters), Phase 2 mctrader-data PR (WAL freeze 도구 + 4 root cause 진단 스크립트 + WAL 복구 검증 + 코드 audit) + hub Phase 2 PR (진단 결과 박제 + CLAUDE.md + Story §8-§12 + RETRO). MCT-166 = fix Story (본 진단 결과 후 별 brainstorm).

**Tech Stack:** Python 3.13, pytest, pyarrow, Docker compose, gh CLI. codeforge plugins.

**Spec reference:** [docs/superpowers/specs/2026-05-14-MCT-164-upbit-wal-diagnostics-design.md](../specs/2026-05-14-MCT-164-upbit-wal-diagnostics-design.md)

---

## File Structure

### mctrader-hub (governance)

- **Modify**: `docs/adr/ADR-017-*.md` — compactor source 규약 amendment (Phase 1 PR)
- **Modify**: `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — silent-skip 차단 amendment (Phase 1 PR)
- **Create**: `docs/stories/MCT-164.md` — Story §1-§12
- **Create**: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` — channel matrix SSOT
- **Modify**: `.codeforge/counters.json` — MCT-164 title 확장 + MCT-166 reservation
- **Create**: `docs/retros/RETRO-MCT-164.md` — Phase 2 land 후 PMOAgent dispatch
- **Modify**: `CLAUDE.md` — §collector/§compactor/§WAL 규약

### mctrader-data (구현)

- **Create**: `scripts/wal_freeze.py` — WAL read-only 전환 도구
- **Create**: `scripts/upbit_wal_diagnostics.py` — 4 root cause 진단 스크립트
- **Create**: `scripts/wal_recovery_probe.py` — snapshot → depth 변환 검증
- **Create**: `docs/audit/MCT-164-code-audit.md` — collector/ingester/compactor read 결과
- **Create**: `docs/audit/MCT-164-parity-upbit-vs-bithumb.md` — D7=C parity 비교
- **Modify**: `CLAUDE.md` — §WAL freeze 도구

---

## Task 1: Phase 1 사전 — counter title 확장 + MCT-166 reservation

**Files:**
- Modify: `mctrader-hub/.codeforge/counters.json`

- [ ] **Step 1: counters.json — MCT-164 title 확장 + MCT-166 reservation**

```bash
python -c "
import json, pathlib
p = pathlib.Path('.codeforge/counters.json')
d = json.loads(p.read_text(encoding='utf-8'))
d['counters']['mctrader-hub']['next'] = 167
d['reservations']['MCT-164']['title'] = 'upbit WAL forward-only loss 진단 (channel mismatch + compactor source 규약 + ADR-017/027 amendment)'
d['reservations']['MCT-164']['retitle_history'] = [{
    'date': '2026-05-14',
    'from': 'upbit L1 lost root cause (path discovery / ingester WAL layout) — MCT-160 R7 verify 잔존 시 발의 placeholder',
    'rationale': 'MCT-165 V2 verify 잔존 YES 박제 후 brainstorm 진입 — scope = 진단 only (D1=A 2 Story 분리, fix = MCT-166 별 Story)'
}]
d['reservations']['MCT-164']['rationale'] = 'MCT-165 V2 잔존 YES trigger. forward-only loss 누적 차단 = D2=A WAL freeze 즉시 + D3=A channel mismatch 가설 우선 진단 + D9=A ADR-017/027 amendment. fix scope 는 MCT-166 별 brainstorm.'
d['reservations']['MCT-164']['phase_pair'] = 'phase1_phase2'
d['reservations']['MCT-166'] = {
    'title': 'upbit L1 forward-only loss fix (MCT-164 진단 결과 기반 — scope 확정 후 brainstorm) placeholder',
    'reserved_at': '2026-05-14',
    'epic': 'EPIC-data-accumulation-umbrella',
    'repo': 'mctrader-data',
    'phase_pair': 'tbd',
    'rationale': 'MCT-164 §10 진단 결과 (channel mismatch / path mismatch / compactor 미지원 / discovery skip 4 후보 중 확정 영역) 인용 후 fix scope brainstorm. INV-5 정합 (진단 → fix 인과 chain 강제).'
}
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
"
```

기대: counters.json 갱신, MCT-164 title 확장 + MCT-166 reservation 추가, next=167.

- [ ] **Step 2: branch 생성**

```bash
git checkout -b mct-164-phase-1
```

---

## Task 2: ADR-017 amendment — compactor source 규약

**Files:**
- Modify: `mctrader-hub/docs/adr/ADR-017-*.md`

- [ ] **Step 1: ADR-017 path / 본문 확인**

```bash
ls docs/adr/ | grep "ADR-017"
```

- [ ] **Step 2: amendment 본문 추가**

ADR-017 본문 끝에 amendment 섹션 append:

```markdown
## Amendment 2 — 2026-05-14 (MCT-164)

### Compactor Source 규약 (channel matrix SSOT)

L1 / L2 / L3 compactor 의 source channel 매핑 규약:

| Tier | Source Channel (WAL) | Target Dataset (parquet) | 변환 의무 |
|---|---|---|---|
| L1 | orderbookdepth (per-event) | orderbookdepth | 1:1 |
| L1 | orderbooksnapshot (per-snapshot) | orderbookdepth | snapshot → depth 변환 의무 |
| L2 | orderbookdepth | orderbooksnapshot (per-hour) | aggregation |
| L3 | orderbooksnapshot | orderbooksnapshot (per-day) | aggregation |

### 규약 적용 의무

1. **Source channel 인식**: compactor 는 source channel 명을 명시적으로 read. silent skip (예: orderbooksnapshot WAL 발견 시 무시) 금지 (ADR-027 amendment 1 silent-skip 차단 정합).
2. **Multi-channel exchange 지원**: 같은 exchange 에서 다중 channel 가능 (예: bithumb = orderbookdepth, upbit = orderbooksnapshot). compactor 는 channel matrix 표 (docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md) 기반 dispatch.
3. **Snapshot → Depth 변환**: L1 source = orderbooksnapshot 시 compactor 가 변환 의무. 미구현 시 fail-fast (silent skip 금지).

### 검증 의무

- MCT-164 진단 결과 (`docs/stories/MCT-164.md` §10) 가 본 규약과 정합한지 확인
- MCT-166 fix Story 가 본 규약 위반 발견 시 fix scope 에 포함 의무
```

- [ ] **Step 3: Amendment History 항목 추가**

ADR-017 의 Amendment History 표에 행 추가:

```markdown
| Amendment 2 | 2026-05-14 | MCT-164 | Compactor source 규약 (channel matrix SSOT) + multi-channel exchange 지원 + snapshot → depth 변환 의무 |
```

---

## Task 3: ADR-027 amendment — silent-skip 차단 (미지원 source)

**Files:**
- Modify: `mctrader-hub/docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`

- [ ] **Step 1: silent-skip 차단 amendment 본문 추가 (Amendment 2)**

ADR-027 본문에 append:

```markdown
## Amendment 2 — 2026-05-14 (MCT-164)

### 미지원 Source Silent-skip 차단

ADR-027 Amendment 1 (MCT-160) 의 silent-skip 차단 정책을 **multi-channel exchange** 영역으로 확장:

- L1 / L2 / L3 compactor 가 미지원 source channel 발견 시 silent skip 금지 → **fail-fast + surface 의무** (Prometheus `compactor_unsupported_source_total{tier,exchange,channel}` Counter +1)
- 예: upbit WAL = orderbooksnapshot 발견 시 compactor 가 ADR-017 amendment 2 표 기반 dispatch. 표 미박제 또는 변환 미구현 시 ValueError + Prometheus emit
- MCT-164 §10 진단 결과 = 본 amendment 의 motivation root cause

### 검증 의무

- MCT-166 fix Story 가 본 amendment 정합 검증 의무 (compactor source 분기 코드에 fail-fast 적용)
- Phase 2 회귀 test = 미지원 source 주입 → ValueError + Prometheus emit 확인
```

- [ ] **Step 2: Amendment History 항목 추가**

```markdown
| Amendment 2 | 2026-05-14 | MCT-164 | 미지원 source channel silent-skip 차단 — fail-fast + Prometheus surface 의무 |
```

---

## Task 4: channel matrix domain-knowledge SSOT 박제

**Files:**
- Create: `mctrader-hub/docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md`

- [ ] **Step 1: channel matrix file 작성**

본문 = exchange × channel × tier 매핑 표 (D8=A). 현재 추정 (진단 전, Phase 2 진단 결과 후 본문 update):

```markdown
---
domain: data-health
created: 2026-05-14
story: MCT-164
related_adrs:
  - ADR-017 Amendment 2 (compactor source 규약)
  - ADR-027 Amendment 2 (미지원 source silent-skip 차단)
---

# Exchange × Channel × Tier Matrix

mctrader-data 의 multi-exchange × multi-channel × multi-tier 매핑 SSOT.

## 추정 매트릭스 (2026-05-14 진단 전 hypothesis)

| Exchange | Collector Channel (WAL) | L1 Dataset | L2 Dataset | L3 Dataset | 비고 |
|---|---|---|---|---|---|
| bithumb | orderbookdepth | orderbookdepth | orderbooksnapshot | orderbooksnapshot | MCT-162 LAND 후 정상 |
| bithumb | transaction | transaction | transaction | transaction | 정상 |
| upbit | orderbooksnapshot | (미지원 ← MCT-164 진단) | (미지원) | (미지원) | **MCT-164 root cause 영역** |
| upbit | transaction | transaction | transaction | transaction | 추정 정상 (별 진단 필요) |

## 진단 후 update 의무

본 표는 hypothesis. MCT-164 Phase 2 진단 결과 (`docs/stories/MCT-164.md` §10) 박제 후 본 file 본문 갱신 의무 (Phase 2 PR 에서 update).

## 변환 의무 (ADR-017 Amendment 2)

- Collector channel ≠ L1 dataset 시 compactor 변환 의무
- 예: upbit orderbooksnapshot WAL → L1 orderbookdepth 변환 가능성 (MCT-164 AC-5 D4=C 검증 대상)

## Cross-ref

- ADR-017 Amendment 2 (compactor source 규약)
- ADR-027 Amendment 2 (미지원 source silent-skip 차단)
- MCT-164 (본 matrix SSOT 발의 Story)
- MCT-165 V2 (upbit L1 partition 0 trigger)
- MCT-166 (fix Story, 본 matrix 정합 fix 의무)
- docs/domain-knowledge/domain/data-health/README.md (7-layer + multi-exchange parity layer cross-ref)
```

---

## Task 5: Story file MCT-164.md §1-§7 작성

**Files:**
- Create: `mctrader-hub/docs/stories/MCT-164.md`

- [ ] **Step 1: Story file 작성**

spec §1-§9 + brainstorm 결과 박제. MCT-160 / MCT-165 패턴 답습. §8-§12 = Phase 2 박제.

frontmatter:
```yaml
---
story_key: MCT-164
story_scope: cross-repo
story_issues:
  - repo: mclayer/mctrader-hub
    number: 292  # MCT-164 trigger Issue (MCT-165 V2 잔존 YES)
status: IN_PROGRESS
epic_key: EPIC-data-accumulation-umbrella  # D7=C carry-over umbrella, MCT-165 와 동일
parent_dependency: null
depends_on:
  - MCT-165  # V2 verify 잔존 YES (V2 trigger source)
  - MCT-160  # §11 R7 carry source
  - MCT-162  # channel parity Story (bithumb-only allowlist — Researcher 유력 가설 핵심)
related_adrs:
  - "ADR-017 Amendment 2 — compactor source 규약 (Phase 1 PR)"
  - "ADR-027 Amendment 2 — 미지원 source silent-skip 차단 (Phase 1 PR)"
  - "ADR-009 §D12 — forward-only invariant (INV-1 정합, amend 0)"
created_at: 2026-05-14
completed_at: null
retro_file: docs/retros/RETRO-MCT-164.md
delegates:
  - mctrader-data
---
```

본문 = spec §1-§7 박제 (Why / Phase 0 결과 / 9 D 결정 / AC 7 / INV 5 / Risk 3 / Phase 분할 / cross-ref).

---

## Task 6: Phase 1 PR open + DesignReviewPL + admin merge

- [ ] **Step 1: Issue #292 link + body update**

이미 Issue #292 OPEN (trigger 박제). brainstorm 진입 결과 + 9 D 결정 + Phase 분할 본 PR 에서 박제 의무.

- [ ] **Step 2: Phase 1 commit**

```bash
git add .codeforge/counters.json docs/adr/ADR-017-*.md docs/adr/ADR-027-*.md \
        docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md \
        docs/stories/MCT-164.md \
        docs/superpowers/specs/2026-05-14-MCT-164-upbit-wal-diagnostics-design.md \
        docs/superpowers/plans/2026-05-14-mct-164-upbit-wal-diagnostics.md

git commit -m "docs(MCT-164): Phase 1 — spec + plan + Story §1-§7 + ADR-017/027 amendment 본문 + channel matrix + counters"
```

- [ ] **Step 3: push + PR open**

```bash
git push -u origin mct-164-phase-1
gh pr create --repo mclayer/mctrader-hub --base main --head mct-164-phase-1 \
  --title "[MCT-164] Phase 1 — upbit WAL forward-only loss 진단 spec + ADR-017/027 amendment + channel matrix" \
  --body "Closes part of #292 (Phase 1 docs only).

## Scope

9 D 결정 (Codex 합성 + Sonnet, D1=A 사용자 confirm):
- D1=A 2 Story 분리 (MCT-164 진단 / MCT-166 fix)
- D2=A WAL freeze + 진단 동시 (Phase 2 entry)
- D3=A channel mismatch 가설 우선
- D4=C WAL 복구 시도 → 실패 시 forward-only
- D5=C fix scope = 진단 후
- D6=B 일반 Story flow + 당일 처리
- D7=C upbit + bithumb 비교
- D8=A channel matrix domain-knowledge 박제
- D9=A ADR-017/027 amendment

## File

- spec + plan
- Story file §1-§7
- ADR-017 Amendment 2 (compactor source 규약) + ADR-027 Amendment 2 (silent-skip 차단)
- channel matrix domain-knowledge SSOT
- counters: MCT-164 title 확장 + MCT-166 reservation, next=167

## Phase 2

mctrader-data WAL freeze + 진단 스크립트 + 코드 audit + WAL 복구 probe. hub Phase 2 = 진단 결과 박제 + RETRO + Story §8-§12 + CLAUDE.md."

gh pr edit <PR#> --add-label "type:story" --add-label "phase:설계"
```

- [ ] **Step 4: DesignReviewPLAgent dispatch**

PASS → phase:설계-리뷰 + gate:design-review-pass label transition (MCT-165 패턴).

- [ ] **Step 5: CI green → admin merge**

```bash
gh pr merge <PR#> --admin --squash --delete-branch
```

---

## Task 7: Phase 2 — mctrader-data WAL freeze + 진단

**Files (mctrader-data working dir):**
- Create: `scripts/wal_freeze.py`
- Create: `scripts/upbit_wal_diagnostics.py`
- Create: `scripts/wal_recovery_probe.py`
- Create: `docs/audit/MCT-164-code-audit.md`
- Create: `docs/audit/MCT-164-parity-upbit-vs-bithumb.md`

- [ ] **Step 1: WAL freeze 도구 (AC-1)**

`scripts/wal_freeze.py` — upbit WAL 의 sealed segments 를 read-only 로 전환 (chmod 444 또는 별 디렉터리 이동). 신규 쓰기 차단 검증. INV-1 정합.

- [ ] **Step 2: 4 root cause 진단 스크립트 (AC-2/3/4)**

`scripts/upbit_wal_diagnostics.py`:
- (a) path mismatch: collector / ingester / compactor write path 추적 (read-only)
- (b) L1 compactor upbit 미지원: l1.py source 분기 read
- (c) channel mismatch: collector allowlist + ingester partition key + L1 discovery 추적
- (d) partition discovery skip: L1 compaction runner read

각 후보별 "확정 / 기각 / 부분기여" verdict 박제 (INV-3).

- [ ] **Step 3: WAL 복구 probe (AC-5 D4=C)**

`scripts/wal_recovery_probe.py` — frozen upbit WAL 의 orderbooksnapshot → orderbookdepth 변환 가능성 검증. 변환 가능 = MCT-166 fix scope 에 backfill 포함. 불가 = forward-only acceptable + 손실 구간 박제 (R1 완화).

- [ ] **Step 4: parity 비교 (AC-6 D7=C)**

`docs/audit/MCT-164-parity-upbit-vs-bithumb.md` — bithumb 정상 / upbit 결함 code path diff. asymmetry root 박제.

- [ ] **Step 5: mctrader-data Phase 2 commit + PR**

```bash
cd c:/workspace/mclayer/mctrader-data
git checkout -b mct-164-phase-2
git add scripts/wal_freeze.py scripts/upbit_wal_diagnostics.py scripts/wal_recovery_probe.py docs/audit/MCT-164-*.md
git commit -m "feat(MCT-164): Phase 2 — WAL freeze + 4 root cause 진단 + WAL 복구 probe + parity 비교"
git push -u origin mct-164-phase-2
gh pr create --repo mclayer/mctrader-data --title "[MCT-164] Phase 2 — upbit WAL forward-only loss 진단 + freeze + 복구 probe" --body "..."
```

- [ ] **Step 6: CodeReviewPLAgent + SecurityTestPLAgent dispatch + admin merge**

---

## Task 8: Phase 2 hub PR — 진단 결과 박제 + Story §8-§12 + RETRO + CLAUDE.md

**Files (mctrader-hub working dir):**
- Modify: `docs/stories/MCT-164.md` — §8-§12 추가
- Modify: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` — 진단 결과 기반 표 update
- Create: `docs/retros/RETRO-MCT-164.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Story §8-§12 박제**

- §8 Test Contract (mctrader-data 진단 스크립트 의 test 박제)
- §9 Operational Risk
- §10 진단 결과 (INV-3 — 4 후보 verdict + root cause 확정 영역)
- §11 Invariant cross-ref
- §12 PMOAgent retro (PMOAgent dispatch 영역)

- [ ] **Step 2: channel matrix domain-knowledge update**

진단 결과 기반 표 update (hypothesis → 실제 fact).

- [ ] **Step 3: CLAUDE.md 갱신**

§collector / §compactor / §WAL 규약 신규 (ADR-017/027 Amendment 2 cross-ref).

- [ ] **Step 4: RETRO 박제**

PMOAgent dispatch — memory `feedback_pmo_retro_mandatory` 정합.

- [ ] **Step 5: hub Phase 2 commit + PR + admin merge**

---

## Task 9: MCT-166 fix Story trigger

본 Story 종료 시점에:
1. Issue #292 close (gate:retro-complete + 진단 결과 summary)
2. MCT-166 Issue 발의 (진단 결과 인용 + fix scope 명시 + brainstorm 진입 의무 박제)
3. MCT-166 = 별 세션 brainstorm (codeforge:brainstorm Phase 0~2 + spec + plan + Story file + Phase 1 PR)

---

## Self-Review

- [x] Spec §1-§9 coverage: 각 결정 D1~D9 → Task 매핑
- [x] Placeholder scan: ADR amendment 본문 hypothesis 영역 = Phase 2 진단 후 update 의무 명시 (silent placeholder 아님)
- [x] Type consistency: 진단 verdict 3-state ("확정/기각/부분기여", INV-3) cross-task 일관
- [x] Cross-repo handling: hub/data working dir 명시 + branch race 회피
- [x] Forward-only loss accumulation 긴급도 = Phase 2 entry 즉시 WAL freeze (D2=A INV-1)

---

## Execution Handoff

Plan complete. Execution = Subagent-Driven (memory feedback_subagent_execution).
