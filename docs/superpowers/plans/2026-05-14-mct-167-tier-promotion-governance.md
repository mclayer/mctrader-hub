---
plan_id: 2026-05-14-mct-167-tier-promotion-governance
story_key: MCT-167
spec_ref: 2026-05-14-MCT-167-tier-promotion-governance-design
phase: 1 (governance singleton, docs only, code 변경 0)
created: 2026-05-14
---

# Plan: MCT-167 Phase 1 — Cold tier governance v2 singleton

## Step 1 — Branch + Prerequisite verify

- branch: `mct-167-phase-1` (from `main`)
- prerequisite: MCT-161 + MCT-163 PR MERGED + RETRO LAND (2026-05-14 본 세션 verify 완료)
- ADR-NNN 번호: `ADR-029` (`ls docs/adr/` 의 다음 free 번호, 본 세션 확인 완료)

## Step 2 — 10 file 박제

### 2.1 신규 ADR (1)

- `docs/adr/ADR-029-tier-promotion-single-source.md`
- frontmatter: status=Accepted, related_story=MCT-167, related_epic=EPIC-tier-promotion-single-source, successor_of=[ADR-017, ADR-027], amends=[ADR-017 §3 D3, ADR-027 §D5/D7/D9, ADR-009 §D12.2]
- Decision: D1-D11 (scope_manifest yaml 답습)
- Consequences: Pros 5 / Cons 5 / Neutral 3
- Alternatives Considered: 3건 (Local=SoT / cold tier only / Full NAS)
- References: ADR cross-link + Story/Epic + Prerequisite + Plugin reference

### 2.2 ADR amendment (3)

- `docs/adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md` §3 D3 — "MCT-167 amendment 박제" 박스 + L1 NAS PUT 의무 + ADR-029 D1 cross-ref
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`:
  - Status Amendment Trail (2026-05-14 MCT-167 entry 추가)
  - §D5 "MCT-167 amendment" — L1 NAS upload 금지 invariant 폐기 + capacity-bounded ingest block
  - §D7 "MCT-167 amendment" — L1 tier grace 0 (L2/L3 grace 7일 유지)
  - §D9 "MCT-167 amendment" — SoT scope = all-tier (L1 + L2 + L3)
- `docs/adr/ADR-009-ohlcv-schema.md`:
  - Amendment History (2026-05-14 MCT-167 entry 추가)
  - §D12.2 "MCT-167 amendment" — forward-only invariant NAS object SoT 격상

### 2.3 DR runbook stub 확장 (1)

- `docs/runbooks/nas-bucket-disaster-recovery.md`
- "Epic-level DR scope (MCT-167 stub 확장, 본문 = MCT-171)" 섹션 추가
- 5 fail mode placeholder (L1 NAS PUT fail / NAS unreachable + capacity-bounded / clock drift / rate-limit / replication failover)
- invariant 8종 (MCT-151 7종 + ambiguity invariant 8번째)
- 용량 4 layer table (WAL/L1/NAS/Host)
- Cross-ref 박제 (ADR-029 + ADR-017/027/009 amendment + MCT-171/174)

### 2.4 Story file (1)

- `docs/stories/MCT-167.md` §1-§11
- frontmatter: story_scope=hub-only, status=IN_PROGRESS, depends_on=[MCT-161, MCT-163], related_adrs=4건
- §1 동기 / §2 Phase 0 Context / §3 11 D 결정 / §4 산출물 / §5 AC (10) / §6 INV (6) / §7 Risk (7) / §8 Test Contract (N/A) / §8.5 N/A / §9 Phase 1 PR cycle / §10 FIX Ledger / §11 Cross-ref

### 2.5 counters.json (1)

- `.codeforge/counters.json`
- MCT-167 title 확장: "tier-promotion governance — ADR-029 신규 + ADR-017/027/009 amend 3건 + DR runbook stub" (현재 동일 wording, ADR-NNN → ADR-029 explicit 만 변경)
- retitle_history append (ADR-NNN → ADR-029 박제)

### 2.6 scope_manifest yaml (1)

- `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- 본 Phase 1 = status 변경 없음 (Proposed 유지). MCT-167 status: IN_PROGRESS 전환은 Phase 2 PMO retro 시.
- Phase 2 PMO retro 시 milestone 1/6 박제 (MCT-167 status: COMPLETED).

### 2.7 brainstorm spec (1)

- `docs/superpowers/specs/2026-05-14-MCT-167-tier-promotion-governance-design.md`
- spec 개요 + D1-D11 + Phase 0 Context + 산출물 매핑 + 후속 Story chain + prerequisite verify + Cross-ref

### 2.8 plan (1, 본 file)

- `docs/superpowers/plans/2026-05-14-mct-167-tier-promotion-governance.md` (본 file)

## Step 3 — Commit + Push + PR open

### 3.1 Commit message

```
docs(MCT-167): Phase 1 — ADR-029 신규 + ADR-017/027/009 amend 3건 + DR runbook stub + Story §1-§11

EPIC-tier-promotion-single-source governance singleton — Cold tier governance v2.
NAS = single source of truth for ALL tiers (L1 + L2 + L3).

ADR-029 publish (D1-D11):
- D1=B L1 NAS PUT timing (ParquetWriter atomic 직후)
- D2=B DualWriter retry_queue 재사용
- D3=C immediate local delete + NAS HEAD verify (Researcher↔PMO 충돌 해소)
- D4=B WAL local only 유지 (사용자 directive)
- D5=A_modified capacity-bounded ingest block
- D6=B bucket versioning + cross-NAS replication
- D7=A reader cache 95% hit + <100ms p99
- D8=B forward-only + local fallback migration
- D9=A MCT-161 + MCT-163 prerequisite sequential ✓
- D10=A ambiguity invariant violation enforcement
- D11 capacity_bounded 4 layer (WAL 30G / L1 20G / NAS 500G target / Host 200G)

ADR amendment 3건:
- ADR-017 §3 D3 (L1 NAS PUT 의무, ADR-027 §D5 invariant 폐기 후행)
- ADR-027 §D5+D7+D9 (L1 invariant 폐기 + L1 grace 0 + SoT all-tier 격상)
- ADR-009 §D12.2 (forward-only invariant NAS object SoT 격상)

DR runbook stub 확장 — Epic-level 5 fail mode + invariant 8종 + 용량 4 layer (본문 = MCT-171).

prerequisite verify:
- MCT-161 LAND 2026-05-14 (PR #301 + #302) — NAS bucket versioning + Object Lock
- MCT-163 LAND 2026-05-14 (PR #303 + #304) — DualWriter put_streaming + L2/L3 iter_batches

phase1_only — code 변경 0, docs only.
```

### 3.2 PR open

- title: `docs(MCT-167): Phase 1 — ADR-029 신규 + ADR-017/027/009 amend 3건 + DR runbook stub`
- label: `type:story` + `phase:설계` + `epic:tier-promotion-single-source` (필요 시 신규 label 생성)
- body: 산출물 10 file + AC 10건 + INV 6건 + prerequisite verify + cross-ref

## Step 4 — DesignReviewPL dispatch

본 ArchitectPL 가 ArchitectAgent 호출 via Orchestrator (또는 직접 dispatch).

### 4.1 검수 항목

- ADR-029 D1-D11 정합 (scope_manifest yaml vs ADR 본문 1:1 mapping)
- 3 amendment 박제 cross-ref 정합 ("MCT-167 amendment" + "ADR-029 publish" 의무)
- DR runbook stub vs MCT-171 본문 책무 분리 명확성
- INV-1 phase1_only invariant 위반 0 (code 변경 0)

### 4.2 FIX iter

- max FIX iter = 3 (Story §10 FIX Ledger SSOT)
- mechanical fast-path 허용 (typo / cross-ref miss / wording drift)

## Step 5 — CI + Admin merge

1. CI green 확인 (lint / link check / yaml validate)
2. admin merge (사용자 admin merge autonomy)

## Step 6 — PMOAgent retro

PMOAgent dispatch:
- `docs/retros/RETRO-MCT-167.md` author
- Story §12 Closure summary 박제
- counters.json MCT-167 reservation DELETE
- scope_manifest MCT-167 status: COMPLETED (milestone 1/6 박제)
- CLAUDE.md 박제 (필요 시)
- `docs/results/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` placeholder (Epic CLOSED 시점 fill)

## Step 7 — 다음 Story 권고

**MCT-168 (L1 NAS DualWriter wiring)** — 별 세션 권고 (context 폭증 방지).

- prompt: `docs/superpowers/prompts/EPIC-tier-promotion-single-source-session-prompt.md` paste
- prerequisite verify: MCT-167 LAND 확인 후 진입
- scope: `mctrader_data/compactor/runner.py` + `l1.py` + `nas_storage/dual_writer.py` (L1 mode 추가) + integration test 3건
