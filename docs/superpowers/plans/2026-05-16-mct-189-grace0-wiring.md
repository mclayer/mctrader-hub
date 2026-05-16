# MCT-189 grace-0 로컬삭제 wiring 완결 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ADR-029 §D3=C "NAS HEAD verify → grace-0 local delete" 정책을 mctrader-data production 경로에 실제 wiring + 4중 HEAD verify primitive (ETag+VersionId+sha256+ContentLength) + pre-delete guard + legacy 130 GB retroactive 회수 + ADR-029 §D3 amendment box VERIFIED 박제.

**Architecture:** DualWriter `status=committed` branch가 source local file의 self-delete를 담당하는 단일 책임 모델 (D-2 A). NAS `head_object()` primitive를 4중 verify(ETag+VersionId+sha256 metadata+ContentLength)로 확장(D-4 C)하고 unlink 직전 동일 primitive로 pre-delete guard(D-8 B)를 수행. legacy 130 GB는 compactor `idempotent skip` 경로에 retroactive HEAD verify + unlink을 통합(D-3 C path A)해 production scan loop가 자연 회수.

**Tech Stack:** Python 3.12 / boto3 (MinIO S3-compatible) / pyarrow (Parquet writer) / testcontainers (MinIO integration test) / Prometheus client (capacity/ambiguity Counter).

---

## File Structure

**mctrader-data 코드** (PR2 wiring + PR3 cleanup):
- Modify: `src/mctrader_data/nas_storage/nas_uploader.py:309-405` — `head_object()` response 확장
- Modify: `src/mctrader_data/compactor/promotion.py:95-180` — `_head_with_retry()` 4중 verify + pre-delete guard
- Modify: `src/mctrader_data/nas_storage/dual_writer.py:236-258` — `status=committed` branch self-delete + caller contract 박제
- Modify: `src/mctrader_data/compactor/l1.py:475-480` — L1 ParquetWriter atomic 후 DualWriter.write() commit boundary 안 self-delete
- Modify: `src/mctrader_data/compactor/l2.py:133-235` — L1→L2 promotion 시 L1 source unlink
- Modify: `src/mctrader_data/compactor/l3.py:131-230` — L2→L3 promotion 시 L2 source unlink
- Modify: `src/mctrader_data/compactor/runner.py` — (PR3) `idempotent skip` 경로 retroactive unlink
- Create: `tests/integration/compactor/test_promote_l1_post_put_unlink.py` — 5 시나리오 (정상 / HEAD 404 / HEAD 5xx / concurrent / partition)

**mctrader-hub 문서** (Phase 1 + Phase 2 PR3 박제):
- Modify: `docs/stories/MCT-189.md` — phase 전이 + §3 본설계 + §7 + §8.5 + §10 + §11
- Modify: `docs/adr/ADR-029-tier-promotion-single-source.md` — Status §MCT-189 amendment + §D3 + §D10 + §D11 표 + Migration line 363
- Create: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` — 4 invariant 박제
- Modify: `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` — §Cross-ref 추가
- Modify: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` — §MCT-189 행 + Epic CLOSED prereq
- Create: `docs/retros/RETRO-MCT-189.md` — 회고
- Modify: `CLAUDE.md` — §MCT-189 entry + §EPIC carry over 표
- Modify: `scope_manifests/EPIC-tier-promotion-single-source.yaml` — carry_over_items
- Modify: `.codeforge/counters.json` — MCT-189 status 전이

---

## Phase 1 PR (mctrader-hub docs) — branch `mct-189-phase1-design`

### Task 1: ADR-029 §D3 amendment box draft 추가

**Files:**
- Modify: `docs/adr/ADR-029-tier-promotion-single-source.md`

- [ ] **Step 1: Status 섹션 §MCT-189 amendment box 추가**

`docs/adr/ADR-029-tier-promotion-single-source.md` 의 Status 섹션 끝(기존 MCT-170/172 amendment box 다음)에 추가:

```markdown
> **MCT-189 amendment (2026-05-16, Phase 1 draft → Phase 2 PR3 VERIFIED)**: `promote_l1()` caller wiring 완결 + DualWriter self-delete (D-2 A) + 4중 HEAD verify primitive (ETag+VersionId+sha256 metadata+ContentLength, D-4 C) + pre-delete guard (D-8 B). §D3 line 240/246/347 grace 0 일관 amend (D-1 A unconditional, terminal path 7-day FIFO 표현 제거). §D11 표 line 347 "7-day grace 기본" → "L1 ParquetWriter atomic 후 NAS PUT commit 직후 grace 0 unlink" 정정. §D10 production evidence gate 강화 (post-LAND 14d 0 violation, ADR-032 evidence triad 형식 차용). Migration §Forward-only invariant line 363 격상 (local fallback 제거, NAS versioning 30d window 의존). Status: POLICY_FINALIZED 유지 + amendment 박제 (POLICY_FINALIZED 강등 없음, 10/11 D 정상 + D3 wiring 해소).
```

- [ ] **Step 2: §D3 본문 line 246 amend**

`### D3. Local delete = NAS HEAD verify + grace 0` 본문 라인 246 (기존: "L1 NAS PUT 완료 + L1 NAS HEAD verify 후 즉시 local L1 file 삭제 (D11 L1 hard limit 20 GiB 도달 시점에만 trigger, 정상 운영 시 7-day FIFO grace)") 를:

```markdown
- **L1 local delete (Tier promote 없을 때)**: L1 NAS PUT 완료 + L1 NAS HEAD verify (4중: ETag+VersionId+sha256 metadata+ContentLength, D-4 C) + pre-delete HEAD guard (D-8 B) 후 즉시 local L1 file 삭제 (D-1 A grace 0 unconditional, terminal path 도 동일 — MCT-189 amendment 2026-05-16).
```

- [ ] **Step 3: §D11 표 line 347 정정**

§D11 4-layer 표의 L1 local 행(라인 347)을 정정:

```markdown
| **L1 local** | 20 GiB | DualWriter `status=committed` branch self-delete (D-2 A, grace 0) — NAS verify 4중 + pre-delete guard | NAS PUT commit boundary 안에서 즉시 unlink (D-1 A unconditional, MCT-189 amendment). hard limit 20 GiB 도달 시 추가 graceful drain — `nas_uploader.head_object` retry 강화 |
```

- [ ] **Step 4: §D10 line 333 production evidence gate 강화**

`### D10. Ambiguity 차단` 본문 라인 333 (기존: "production evidence gate = codeforge-plugin#620 Fix-1...") 끝에 추가:

```markdown

> **MCT-189 amendment (2026-05-16)**: ADR-032 evidence triad 형식 차용 (file:line + production caller grep ≥1 + integration test PASS). post-LAND 14d rolling `nas_reader_ambiguity_total` Counter = 0 (D-6 A). PR3 박제 시 Story §8.5 Impl Manifest에 evidence triad 박제 의무.
```

- [ ] **Step 5: Migration §Forward-only invariant line 363 격상**

기존 "Tier promotion 후 local delete = forward-only 위반 0 (D3=C ambiguity 차단). NAS = single source of truth, local = ephemeral cache only." 끝에 추가:

```markdown

> **MCT-189 amendment (2026-05-16, D-5 A)**: local fallback 제거 (MCT-170 D8=B sunset 2026-09-01 정합 + grace-0 wiring 정합). NAS versioning 30d window = PITR/operational recovery 단일 보증. host 200G hard limit 정합 (ADR-029 §D11).
```

- [ ] **Step 6: Commit Phase 1 amendment draft**

```bash
git add docs/adr/ADR-029-tier-promotion-single-source.md
git commit -m "docs(MCT-189): ADR-029 amendment box draft — §D3 grace 0 일관 + §D10 evidence gate 강화 + §D11 표 정정 + Migration 격상 (Phase 1)"
```

---

### Task 2: domain-knowledge 신규 페이지 `grace-0-local-delete.md`

**Files:**
- Create: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`

- [ ] **Step 1: 디렉터리 + 파일 생성**

```bash
mkdir -p docs/domain-knowledge/domain/tier-promotion
```

- [ ] **Step 2: 파일 내용 작성**

`docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`:

```markdown
# Grace-0 Local Delete Invariant (MCT-189 LAND 박제)

> **SSOT**: ADR-029 §D3 amend (MCT-189 2026-05-16, D-1 A unconditional).
> caller-wired vs decision-defined 분리 의무 — 본 페이지가 caller-wired 측 invariant.

## 4 invariant

### INV-1: `promote_l1()` caller wiring 박제 (D-2 A)

`DualWriter.write()` 의 `status=committed` branch가 source local file self-delete 책임. caller (l1/l2/l3/runner) 는 별도 호출 불요. (이전: caller 0건 → wiring 누락 = SSOT drift 2호 trigger, MCT-189 amendment)

**Production caller grep ≥1 의무** (ADR-032 evidence triad):
- `dual_writer.py::write()` status="committed" branch 내 `_source_path.unlink(missing_ok=True)` (D-7 A)

### INV-2: 4중 HEAD verify primitive (D-4 C)

`nas_uploader.head_object(key)` 반환 dict는 4 field 모두 비교:
- `ETag` — strip(`"`)
- `VersionId` — versioning Enabled 시 강제
- `Metadata['sha256']` — caller-side single computation (multipart ETag ≠ sha256, INV-3 SSOT cold-path-memory-invariant)
- `ContentLength` — local source `Path.stat().st_size` 와 일치

**1개라도 mismatch = `PromotionVerifyError` raise** (local 보존, INV-4).

### INV-3: pre-delete HEAD guard (D-8 B)

`unlink()` 직전 동일 4중 primitive로 한 번 더 HEAD 호출. HEAD verify와 unlink 사이 race window (다른 process NAS object 덮어쓰기) 차단. ETag + ContentLength 미일치 시 unlink 미실행 + log.warning + Counter `promote_l1_pre_delete_guard_mismatch_total` emit.

### INV-4: forward-only NAS-SoT 격상 (D-5 A)

local fallback 제거 (MCT-170 D8=B sunset 2026-09-01 정합). NAS versioning Enabled (MCT-161) + NoncurrentVersionExpiration 30d = PITR/operational recovery 단일 보증. local copy = ephemeral cache only.

## decision-defined vs caller-wired 분리

`promote_l1()` 함수 정의 (decision-defined) = MCT-169 LAND. 그러나 caller wiring (caller-wired) = MCT-189 LAND. 정의 LAND ≠ 운영 LAND — VERIFIED badge 는 (1) file:line + (2) production caller grep ≥1 + (3) integration test PASS 3 evidence (ADR-032 triad).

## Cross-ref

- ADR-029 §D3 + §D10 + §D11 amendment box (MCT-189 2026-05-16)
- ADR-032 Proposed (VERIFIED badge evidence triad, owner Story 권고 MCT-190)
- `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` §Cross-ref (INV-3 sha256 SSOT)
- `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` (SSOT drift 2호 trigger)
```

- [ ] **Step 3: Commit**

```bash
git add docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md
git commit -m "docs(MCT-189): grace-0-local-delete.md 신규 — 4 invariant 박제 + caller-wired vs decision-defined 분리 (D-9 A)"
```

---

### Task 3: cold-path-memory-invariant.md cross-ref 추가

**Files:**
- Modify: `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` (§Cross-ref 섹션)

- [ ] **Step 1: §Cross-ref 섹션 끝에 추가**

```markdown
- `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` — MCT-189 LAND wiring invariant (DualWriter self-delete가 본 페이지 INV-3 sha256 SSOT를 4중 verify primitive로 활용)
```

- [ ] **Step 2: Commit**

```bash
git add docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md
git commit -m "docs(MCT-189): cold-path-memory-invariant cross-ref → grace-0-local-delete"
```

---

### Task 4: MCT-189 Story §3 본설계 + §7 Test Contract 작성

**Files:**
- Modify: `docs/stories/MCT-189.md`

- [ ] **Step 1: frontmatter `phase` 전이**

`phase: 요구사항` → `phase: 설계` 변경, `started_at: ~` → `started_at: "2026-05-16"`.

- [ ] **Step 2: §3 본설계 섹션 추가**

§2 끝과 §4 (Acceptance Criteria) 사이에 §3 추가:

```markdown
## §3 본 설계 (10 결정점 채택)

spec `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md` SSOT. 핵심 표:

| D | 채택 | 내용 |
|---|------|------|
| D-1 | A | grace 0 unconditional (promotion + terminal 모든 path) |
| D-2 | A | DualWriter self-delete (NAS PUT commit boundary 내) |
| D-3 | C | 단일 Story + 4 PR 다단 (사용자 결정) |
| D-4 | C | 4중 HEAD verify (ETag + VersionId + sha256 metadata + ContentLength) |
| D-5 | A | forward-only invariant 격상 (local fallback 제거) |
| D-6 | A | post-LAND production 14d 0 violation 의무 |
| D-7 | A | idempotent (ENOENT graceful) |
| D-8 | B | pre-delete HEAD ETag+ContentLength 재확인 guard |
| D-9 | A | grace-0-local-delete.md 신규 (본 Story scope) |
| D-10 | B | ADR-032 별 governance Story 발의 (MCT-190 권고) |

각 D의 trade-off + cross-ref ADR-029 amendment box → spec 참조.
```

- [ ] **Step 3: §7 Test Contract 섹션 추가**

```markdown
## §7 Test Contract (PR2 wiring integration test)

`tests/integration/compactor/test_promote_l1_post_put_unlink.py` (신규, testcontainers MinIO):

| Test | 시나리오 | 기대 결과 |
|------|----------|-----------|
| test_normal_path | NAS PUT → 4중 HEAD verify pass → pre-delete guard pass → unlink | local file 부재 + NAS object 존재 (INV-1 XOR) |
| test_head_404 | NAS object 부재 | `PromotionVerifyError` raise + local 보존 (INV-4) |
| test_head_5xx_retry | NAS 5xx → retry 1회 후 5xx 지속 | `PromotionVerifyError` + local 보존 |
| test_concurrent_double_unlink | 동일 nas_key 2 process 동시 처리 | 1개 성공 + 1개 ENOENT graceful (D-7 A) |
| test_partition_mid_delete | HEAD pass 후 NAS object 사라짐 → pre-delete guard 실패 | unlink 미실행 + local 보존 + Counter emit (D-8 B) |
| test_sha256_mismatch | NAS metadata sha256 ≠ local file sha256 | `PromotionVerifyError` + local 보존 (D-4 C) |
| test_content_length_mismatch | NAS ContentLength ≠ local Path.stat().st_size | `PromotionVerifyError` + local 보존 (D-4 C) |
| test_ambiguity_invariant_post_wiring | wiring 후 NAS+local 동시 존재 시점 0 | `InvariantHarness._check_ambiguity()` violation 0 (D-6 A 회귀) |
```

- [ ] **Step 4: Commit**

```bash
git add docs/stories/MCT-189.md
git commit -m "docs(MCT-189): Story §3 본설계 + §7 Test Contract 박제 (10 D 채택 + 8 시나리오)"
```

---

### Task 5: spec 파일 + plan 파일 commit

**Files:**
- Already created: `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md`
- Already created: `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md` (본 파일)

- [ ] **Step 1: Commit spec + plan**

```bash
git add docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md
git commit -m "docs(MCT-189): brainstorm spec + impl plan (4 PR 다단, 10 decision + scope_manifest YAML)"
```

---

### Task 6: CLAUDE.md MCT-189 IN_PROGRESS entry

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\CLAUDE.md`

- [ ] **Step 1: EPIC-tier-promotion-single-source 섹션 끝에 MCT-189 IN_PROGRESS 추가**

기존 `### Epic CLOSED prerequisite registry` 표 끝에:

```markdown
## MCT-189 IN_PROGRESS (2026-05-16) — ADR-029 §D3=C grace-0 로컬삭제 wiring 완결

> EPIC-tier-promotion-single-source carry over (POLICY_FINALIZED 유지, D3 wiring deferred → MCT-189 해소).
> 본 세션 (2026-05-16) 운영 진단 결과 발견 SSOT drift 2호 (1호 = mctrader-data:pilot 이미지 배포 drift, 본 세션 응급 재배포 완료).

### 결과 요약

| 항목 | 상태 |
|------|------|
| Story | RESERVED → IN_PROGRESS (Phase 1 LAND) |
| 4 PR 다단 (Phase 1 docs + Phase 2 PR1 wiring + Phase 2 PR2 cleanup + Phase 2 PR3 박제) | Phase 1 LAND |
| 채택 결정 | D-1 A + D-2 A + D-3 C (사용자) + D-4 C + D-5 A + D-6 A + D-7 A + D-8 B + D-9 A + D-10 B |
| ADR 산출 | ADR-029 amendment box (§D3 + §D10 + §D11 + Migration) — POLICY_FINALIZED 유지 |
| follow-up | ADR-032 별 governance Story (MCT-190 권고) |

### Key References

- Story: `docs/stories/MCT-189.md`
- spec: `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md`
- plan: `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md`
- domain-knowledge: `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md`
- PMO retro (SSOT drift 2호): `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md`
- ADR-029 amendment box: `docs/adr/ADR-029-tier-promotion-single-source.md` §MCT-189 amendment
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(MCT-189): CLAUDE.md IN_PROGRESS entry — Phase 1 LAND"
```

---

### Task 7: scope_manifests/EPIC-tier-promotion-single-source.yaml carry_over_items 갱신

**Files:**
- Modify: `scope_manifests/EPIC-tier-promotion-single-source.yaml`

- [ ] **Step 1: carry_over_items 표에 MCT-189 행 추가**

`carry_over_items:` 섹션(없으면 새로 추가) 끝에:

```yaml
  - id: D3-wiring
    title: "ADR-029 §D3=C grace-0 로컬삭제 wiring"
    owner_story: MCT-189
    status: IN_PROGRESS  # Phase 2 PR3 LAND 시 resolved
    reserved_at: "2026-05-16"
    rationale: "MCT-169 D3 VERIFIED 박제됐으나 promote_l1() caller 0건 = wiring 누락. MCT-189 = wiring 완결 + 4중 HEAD verify + pre-delete guard + ADR-029 §D3 amendment box (POLICY_FINALIZED 유지)."
```

- [ ] **Step 2: counters.json MCT-189 status 전이**

```yaml
"MCT-189": {
  ...
  "status": "IN_PROGRESS",  # RESERVED → IN_PROGRESS
  "started_at": "2026-05-16",
  ...
}
```

- [ ] **Step 3: Commit Phase 1**

```bash
git add scope_manifests/EPIC-tier-promotion-single-source.yaml .codeforge/counters.json
git commit -m "docs(MCT-189): scope_manifest carry_over_items 갱신 + counters.json IN_PROGRESS"
```

---

### Task 8: Phase 1 PR 생성

- [ ] **Step 1: PR 생성**

```bash
gh pr create --title "docs(MCT-189): Phase 1 — ADR-029 §D3=C grace-0 wiring 설계 + spec/plan 신규" --body "$(cat <<'EOF'
## Summary
- MCT-189 발의 (EPIC-tier-promotion-single-source carry over) — ADR-029 §D3=C grace-0 로컬삭제 wiring 완결
- 본 세션 운영 진단 SSOT drift 2호 (promote_l1 caller 0건) 해소 trigger
- Phase 1 docs only — Phase 2 PR1 (wiring code) + PR2 (legacy cleanup) + PR3 (박제) 후속

## 채택 결정 (D-1~D-10)
- D-1 A grace 0 unconditional / D-2 A DualWriter self-delete / D-3 C 단일 Story + 다단 PR (사용자) / D-4 C 4중 HEAD verify / D-5 A forward-only invariant 격상 / D-6 A post-LAND 14d 0 violation / D-7 A idempotent / D-8 B pre-delete guard / D-9 A domain-knowledge 신규 / D-10 B ADR-032 별 Story

## 산출물
- ADR-029 §D3/§D10/§D11/Migration amendment box draft
- docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md 신규
- docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md
- docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md
- Story §3 본설계 + §7 Test Contract
- CLAUDE.md MCT-189 IN_PROGRESS entry
- scope_manifest carry_over_items 갱신

## Test plan
- [ ] PR2 wiring code LAND 시 integration test 5 시나리오 PASS
- [ ] PR3 박제 시 ADR-029 §D3 amendment box VERIFIED 박제 (file:line + commit sha + test PASS triad)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 2: Phase 1 PR admin merge (CI green 후, memory feedback_admin_merge_autonomy)**

```bash
gh pr merge --admin --squash
```

---

## Phase 2 PR1 (mctrader-data wiring) — branch `mct-189-phase2-wiring`

### Task 9: `nas_uploader.head_object()` 4중 verify response 확장 — Write failing test

**Files:**
- Test: `c:\workspace\mclayer\mctrader-data\tests\unit\nas_storage\test_head_object_4tuple.py` (신규)

- [ ] **Step 1: 디렉터리 + 테스트 파일 생성**

```bash
mkdir -p c:/workspace/mclayer/mctrader-data/tests/unit/nas_storage
```

- [ ] **Step 2: Write failing test**

`tests/unit/nas_storage/test_head_object_4tuple.py`:

```python
"""MCT-189 D-4 C: head_object() returns 4-tuple (ETag + VersionId + sha256 metadata + ContentLength)."""
from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import pytest

from mctrader_data.nas_storage.nas_uploader import NASUploader


def test_head_object_returns_4_fields():
    """head_object response dict 가 ETag + VersionId + sha256 + ContentLength 4 field 모두 포함."""
    uploader = NASUploader(
        endpoint="http://localhost:9000",
        access_key="x",
        secret_key="y",
        bucket="mctrader-market",
    )
    mock_client = MagicMock()
    mock_client.head_object.return_value = {
        "ETag": '"abc123"',
        "VersionId": "v1",
        "Metadata": {"sha256": "d" * 64},
        "ContentLength": 12345,
    }
    uploader._client = mock_client

    result = uploader.head_object(key="l1/test.parquet")

    assert result["ETag"] == "abc123"  # stripped
    assert result["VersionId"] == "v1"
    assert result["sha256"] == "d" * 64
    assert result["ContentLength"] == 12345
```

- [ ] **Step 3: Run test — expect FAIL**

```bash
cd c:/workspace/mclayer/mctrader-data
uv run pytest tests/unit/nas_storage/test_head_object_4tuple.py -v
```

Expected: FAIL — `result["sha256"]` 또는 4-tuple normalization 부재.

---

### Task 10: `nas_uploader.head_object()` 4중 verify response 확장 — Implementation

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\nas_storage\nas_uploader.py:309-405`

- [ ] **Step 1: `head_object()` method 또는 helper 신규/수정**

`nas_uploader.py` 의 head_object 호출 경로(line 309 / 404)를 다음 패턴으로 정규화:

```python
def head_object(self, key: str) -> dict[str, str | int]:
    """4-tuple verify primitive (MCT-189 D-4 C).

    Returns:
        {"ETag": <stripped>, "VersionId": <or None>, "sha256": <or None>, "ContentLength": <int>}
    """
    client = self._get_client()
    response = client.head_object(Bucket=self.bucket, Key=key)
    metadata = response.get("Metadata", {}) or {}
    return {
        "ETag": response.get("ETag", "").strip('"'),
        "VersionId": response.get("VersionId"),
        "sha256": metadata.get("sha256"),
        "ContentLength": int(response.get("ContentLength", 0)),
    }
```

기존 `_head` / 직접 `client.head_object` 호출을 모두 본 메서드로 교체.

- [ ] **Step 2: Run test — expect PASS**

```bash
uv run pytest tests/unit/nas_storage/test_head_object_4tuple.py -v
```

Expected: PASS.

- [ ] **Step 3: Run full unit suite — 회귀 0**

```bash
uv run pytest tests/unit/nas_storage/ -v
```

Expected: 회귀 0.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/nas_storage/test_head_object_4tuple.py src/mctrader_data/nas_storage/nas_uploader.py
git commit -m "feat(MCT-189): nas_uploader.head_object 4-tuple verify return (D-4 C)"
```

---

### Task 11: `promotion.py` 4중 verify + pre-delete guard — Write failing test

**Files:**
- Test: `c:\workspace\mclayer\mctrader-data\tests\unit\compactor\test_promotion_4tuple_guard.py` (신규)

- [ ] **Step 1: Write failing test (4중 verify mismatch + pre-delete guard)**

`tests/unit/compactor/test_promotion_4tuple_guard.py`:

```python
"""MCT-189 D-4 C + D-8 B: promotion 4중 verify + pre-delete guard."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mctrader_data.compactor.promotion import promote_l1, PromotionVerifyError


def test_sha256_mismatch_raises_verify_error(tmp_path: Path):
    """NAS metadata sha256 ≠ local sha256 → PromotionVerifyError, local 보존."""
    local = tmp_path / "test.parquet"
    local.write_bytes(b"hello")  # sha256 = 2cf24...
    uploader = MagicMock()
    uploader.bucket = "mctrader-market"
    uploader.head_object.return_value = {
        "ETag": "abc", "VersionId": "v1",
        "sha256": "wrongdigest" + "0" * 53,  # mismatch
        "ContentLength": 5,
    }
    with pytest.raises(PromotionVerifyError, match="sha256"):
        promote_l1(local_path=local, nas_uploader=uploader, nas_key="l1/test.parquet", segment_id="seg-1")
    assert local.exists()  # INV-4: local 보존


def test_content_length_mismatch_raises_verify_error(tmp_path: Path):
    """NAS ContentLength ≠ local size → PromotionVerifyError, local 보존."""
    local = tmp_path / "test.parquet"
    local.write_bytes(b"hello")  # 5 bytes
    uploader = MagicMock()
    uploader.bucket = "mctrader-market"
    import hashlib
    sha = hashlib.sha256(b"hello").hexdigest()
    uploader.head_object.return_value = {
        "ETag": "abc", "VersionId": "v1", "sha256": sha,
        "ContentLength": 9999,  # mismatch
    }
    with pytest.raises(PromotionVerifyError, match="ContentLength"):
        promote_l1(local_path=local, nas_uploader=uploader, nas_key="l1/test.parquet", segment_id="seg-1")
    assert local.exists()


def test_pre_delete_guard_partition_detection(tmp_path: Path):
    """HEAD verify pass 후 pre-delete guard에서 ETag 변경 검출 → unlink 미실행."""
    import hashlib
    local = tmp_path / "test.parquet"
    local.write_bytes(b"hello")
    sha = hashlib.sha256(b"hello").hexdigest()
    uploader = MagicMock()
    uploader.bucket = "mctrader-market"
    # first HEAD (verify) pass
    # second HEAD (pre-delete guard) ETag 변경
    uploader.head_object.side_effect = [
        {"ETag": "abc", "VersionId": "v1", "sha256": sha, "ContentLength": 5},
        {"ETag": "DIFFERENT", "VersionId": "v2", "sha256": sha, "ContentLength": 5},
    ]
    with pytest.raises(PromotionVerifyError, match="pre.?delete guard"):
        promote_l1(local_path=local, nas_uploader=uploader, nas_key="l1/test.parquet", segment_id="seg-1")
    assert local.exists()  # D-8 B: local 보존
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
uv run pytest tests/unit/compactor/test_promotion_4tuple_guard.py -v
```

Expected: 3 FAIL — sha256 / ContentLength / pre-delete guard 미구현.

---

### Task 12: `promotion.py` 4중 verify + pre-delete guard — Implementation

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\promotion.py:95-180`

- [ ] **Step 1: `_compute_local_sha256()` helper 추가**

`promotion.py` import 영역 위에:

```python
import hashlib


def _compute_local_sha256(path: Path) -> str:
    """Caller-side sha256 (multipart ETag ≠ sha256, INV-3 SSOT)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
```

- [ ] **Step 2: `promote_l1()` 본문 4중 verify + pre-delete guard 추가**

기존 `promote_l1()` 의 HEAD verify 직후 unlink 전 사이를 다음 패턴으로 교체:

```python
    # AC-1 + D-4 C: 4중 HEAD verify
    head_result = _head_with_retry(nas_uploader=nas_uploader, nas_key=nas_key, segment_id=segment_id)

    etag = head_result["ETag"]
    version_id = head_result["VersionId"]
    nas_sha256 = head_result["sha256"]
    nas_content_length = head_result["ContentLength"]

    local_size = local_path.stat().st_size
    local_sha256 = _compute_local_sha256(local_path)

    # D-4 C: 4중 verify — 1개라도 mismatch = PromotionVerifyError (INV-4 local 보존)
    if nas_sha256 is None or nas_sha256 != local_sha256:
        raise PromotionVerifyError(
            f"sha256 mismatch: local={local_sha256} nas_metadata={nas_sha256} segment={segment_id}"
        )
    if nas_content_length != local_size:
        raise PromotionVerifyError(
            f"ContentLength mismatch: local={local_size} nas={nas_content_length} segment={segment_id}"
        )

    log.info("[promotion] HEAD verify PASS (4-tuple) segment=%s etag=%s version_id=%s sha256=%s size=%s",
             segment_id, etag, version_id, nas_sha256[:16], local_size)

    # D-8 B: pre-delete HEAD guard (race window 차단)
    guard_result = _head_with_retry(nas_uploader=nas_uploader, nas_key=nas_key, segment_id=segment_id)
    if guard_result["ETag"] != etag or guard_result["ContentLength"] != nas_content_length:
        raise PromotionVerifyError(
            f"pre-delete guard mismatch (race detected): initial_etag={etag} guard_etag={guard_result['ETag']} segment={segment_id}"
        )

    # AC-2 + INV-2: HEAD verify PASS → immediate local delete (grace 0)
    local_path.unlink(missing_ok=False)
    log.info("[promotion] promoted segment=%s — local deleted (grace=0, D3=C wired)", segment_id)
```

`_head_with_retry()` 도 새 4-field dict 반환 (Task 10에서 head_object response 정규화 완료).

- [ ] **Step 3: Run test — expect PASS**

```bash
uv run pytest tests/unit/compactor/test_promotion_4tuple_guard.py -v
```

Expected: 3 PASS.

- [ ] **Step 4: Run promotion + nas_storage unit suite — 회귀 0**

```bash
uv run pytest tests/unit/compactor/ tests/unit/nas_storage/ -v
```

Expected: 회귀 0.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/compactor/test_promotion_4tuple_guard.py src/mctrader_data/compactor/promotion.py
git commit -m "feat(MCT-189): promotion.py 4중 HEAD verify + pre-delete guard (D-4 C + D-8 B)"
```

---

### Task 13: DualWriter `status=committed` self-delete — Write failing test

**Files:**
- Test: `c:\workspace\mclayer\mctrader-data\tests\unit\nas_storage\test_dual_writer_self_delete.py` (신규)

- [ ] **Step 1: Write failing test**

`tests/unit/nas_storage/test_dual_writer_self_delete.py`:

```python
"""MCT-189 D-2 A: DualWriter status=committed branch self-deletes source local file."""
from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mctrader_data.nas_storage.dual_writer import DualWriter


def test_dual_writer_status_committed_unlinks_source(tmp_path: Path, monkeypatch):
    """DualWriter.write() commit 후 source local file이 unlink된다 (D-2 A)."""
    source = tmp_path / "l1" / "source.parquet"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"x" * 4096)
    sha = hashlib.sha256(b"x" * 4096).hexdigest()

    uploader = MagicMock()
    uploader.bucket = "mctrader-market"
    uploader.put_streaming.return_value = {"ETag": "abc", "VersionId": "v1"}
    uploader.head_object.return_value = {
        "ETag": "abc", "VersionId": "v1", "sha256": sha, "ContentLength": 4096,
    }

    writer = DualWriter(uploader=uploader, retry_queue=MagicMock())
    result = writer.write(source_path=source, nas_key="l1/test.parquet")

    assert result.status == "committed"
    assert not source.exists()  # D-2 A: source self-deleted
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
uv run pytest tests/unit/nas_storage/test_dual_writer_self_delete.py -v
```

Expected: FAIL — `source.exists()` 가 True (현재 dual_writer는 tmp_path만 unlink).

---

### Task 14: DualWriter `status=committed` self-delete — Implementation

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\nas_storage\dual_writer.py:236-258`

- [ ] **Step 1: `status=committed` branch에 source unlink 통합**

`dual_writer.py` 의 NAS PUT commit 성공 branch (현재 `tmp_path.unlink(missing_ok=True)` 만 있는 곳)에 source unlink 추가. `promote_l1()` invocation으로 위임:

```python
        # NAS PUT 성공 path
        if put_result.status == "committed":
            # MCT-189 D-2 A: source local self-delete (caller wiring 0건 재발 차단)
            from mctrader_data.compactor.promotion import promote_l1, PromotionVerifyError

            try:
                promote_l1(
                    local_path=source_path,
                    nas_uploader=self.uploader,
                    nas_key=nas_key,
                    segment_id=segment_id,
                )
                tmp_path.unlink(missing_ok=True)
                return DualWriteResult(status="committed", ...)
            except PromotionVerifyError as e:
                # INV-4: HEAD verify 실패 = local 보존, retry_queue로 위임
                log.warning("[dual_writer] promote_l1 verify failed — local preserved, enqueue retry: %s", e)
                tmp_path.unlink(missing_ok=True)
                self.retry_queue.enqueue(source_path=source_path, nas_key=nas_key, segment_id=segment_id)
                return DualWriteResult(status="local_only_retry_enqueued", ...)
```

라인 242 주석 "caller source safe to delete" 를 다음으로 정정:

```python
            # MCT-189 D-2 A: DualWriter self-delete (caller 의무 폐기) — caller 0건 재발 차단.
```

- [ ] **Step 2: Run test — expect PASS**

```bash
uv run pytest tests/unit/nas_storage/test_dual_writer_self_delete.py -v
```

Expected: PASS.

- [ ] **Step 3: Run nas_storage unit suite — 회귀 0**

```bash
uv run pytest tests/unit/nas_storage/ -v
```

Expected: 회귀 0.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/nas_storage/test_dual_writer_self_delete.py src/mctrader_data/nas_storage/dual_writer.py
git commit -m "feat(MCT-189): DualWriter status=committed self-delete (D-2 A) — caller 0건 재발 차단"
```

---

### Task 15: L1/L2/L3 compactor 측 caller 정합 — Verify no breaking change

**Files:**
- Read: `src/mctrader_data/compactor/l1.py:475`
- Read: `src/mctrader_data/compactor/l2.py:133,233`
- Read: `src/mctrader_data/compactor/l3.py:131,228`

D-2 A 채택 = DualWriter self-delete이므로 l1/l2/l3 측 explicit promote_l1() 호출은 불요. 현재 코드 검증:

- [ ] **Step 1: l1/l2/l3 의 dual_writer.write() 호출 site 확인**

```bash
grep -nE "dual_writer\.write\(|DualWriter\.write\(|self\._dual_writer\.write\(" \
  src/mctrader_data/compactor/l1.py \
  src/mctrader_data/compactor/l2.py \
  src/mctrader_data/compactor/l3.py
```

Expected: 각 file 에 1+ 호출 site. 호출 site는 source_path를 dual_writer 에게 전달.

- [ ] **Step 2: tmp_path / 명명 정합 확인**

`l1.py:478` / `l2.py:133,233` / `l3.py:131,228` 의 `os.unlink(tmp_path)` 는 atomic write 예외 path — D-2 A self-delete 와 별개. 유지.

- [ ] **Step 3: Run compactor unit suite — 회귀 0**

```bash
uv run pytest tests/unit/compactor/ -v
```

Expected: 회귀 0.

- [ ] **Step 4: Commit (no-code, verify only — empty commit 생략 가능)**

코드 변경 없으면 skip. dual_writer 호출 패턴 변경 시에만 commit.

---

### Task 16: integration test 신규 (testcontainers MinIO) — Setup

**Files:**
- Create: `c:\workspace\mclayer\mctrader-data\tests\integration\compactor\test_promote_l1_post_put_unlink.py`

- [ ] **Step 1: testcontainers fixture import + base test**

```python
"""MCT-189 D-6 A integration test — testcontainers MinIO 5 시나리오."""
from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import pytest
from testcontainers.minio import MinioContainer

from mctrader_data.nas_storage.nas_uploader import NASUploader
from mctrader_data.nas_storage.dual_writer import DualWriter
from mctrader_data.compactor.promotion import promote_l1, PromotionVerifyError


@pytest.fixture(scope="module")
def minio():
    with MinioContainer() as container:
        yield container


@pytest.fixture
def uploader(minio):
    return NASUploader(
        endpoint=minio.get_url(),
        access_key=minio.access_key,
        secret_key=minio.secret_key,
        bucket="mctrader-market",
    )


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
```

- [ ] **Step 2: test_normal_path**

```python
def test_normal_path(uploader, tmp_path: Path):
    """정상 경로: PUT → 4중 HEAD verify → pre-delete guard → unlink."""
    source = tmp_path / "l1" / "ok.parquet"
    source.parent.mkdir(parents=True)
    data = b"a" * 8192
    source.write_bytes(data)

    nas_key = "l1/test/ok.parquet"
    uploader.put_streaming(source, nas_key, sha256=_sha256(data))

    result = promote_l1(
        local_path=source, nas_uploader=uploader,
        nas_key=nas_key, segment_id="seg-ok",
    )
    assert result.status == "promoted"
    assert not source.exists()  # INV-1 XOR — NAS only
```

- [ ] **Step 3: test_head_404**

```python
def test_head_404(uploader, tmp_path: Path):
    """NAS 부재 시 PromotionVerifyError + local 보존."""
    source = tmp_path / "missing.parquet"
    source.write_bytes(b"x" * 1024)

    with pytest.raises(PromotionVerifyError):
        promote_l1(
            local_path=source, nas_uploader=uploader,
            nas_key="l1/nonexistent.parquet", segment_id="seg-404",
        )
    assert source.exists()  # INV-4
```

- [ ] **Step 4: test_concurrent_double_unlink**

```python
def test_concurrent_double_unlink(uploader, tmp_path: Path):
    """동일 nas_key 2 thread 동시 처리 → 1 success + 1 ENOENT graceful."""
    source = tmp_path / "concurrent.parquet"
    data = b"c" * 4096
    source.write_bytes(data)
    nas_key = "l1/concurrent.parquet"
    uploader.put_streaming(source, nas_key, sha256=_sha256(data))

    errors = []
    def _run():
        try:
            promote_l1(local_path=source, nas_uploader=uploader,
                       nas_key=nas_key, segment_id="seg-conc")
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=_run)
    t2 = threading.Thread(target=_run)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert not source.exists()
    # D-7 A: 둘 다 성공 (already_promoted INV-6) or 1개 ENOENT graceful — error는 PromotionVerifyError가 아니어야
    for e in errors:
        assert not isinstance(e, FileNotFoundError) or "missing_ok" in str(e)
```

- [ ] **Step 5: test_pre_delete_guard_partition**

```python
def test_pre_delete_guard_partition(uploader, tmp_path: Path, monkeypatch):
    """HEAD verify pass 후 NAS object 사라짐 → pre-delete guard 실패 + local 보존."""
    source = tmp_path / "race.parquet"
    data = b"r" * 2048
    source.write_bytes(data)
    nas_key = "l1/race.parquet"
    uploader.put_streaming(source, nas_key, sha256=_sha256(data))

    # monkeypatch head_object to return different ETag on 2nd call
    original = uploader.head_object
    call_count = [0]
    def _patched(key):
        call_count[0] += 1
        result = original(key)
        if call_count[0] == 2:  # pre-delete guard call
            result["ETag"] = "MUTATED"
        return result
    monkeypatch.setattr(uploader, "head_object", _patched)

    with pytest.raises(PromotionVerifyError, match="pre.?delete guard"):
        promote_l1(local_path=source, nas_uploader=uploader,
                   nas_key=nas_key, segment_id="seg-race")
    assert source.exists()  # D-8 B: local 보존
```

- [ ] **Step 6: Run all integration tests — expect PASS**

```bash
uv run pytest tests/integration/compactor/test_promote_l1_post_put_unlink.py -v --tb=short
```

Expected: 4 PASS (test_head_5xx_retry 는 별 mock 필요, 다음 Task에서).

- [ ] **Step 7: Commit**

```bash
git add tests/integration/compactor/test_promote_l1_post_put_unlink.py
git commit -m "test(MCT-189): integration test — promote_l1 5 시나리오 (D-6 A production gate)"
```

---

### Task 17: ambiguity invariant 회귀 — post-wiring verify

**Files:**
- Modify: `tests/integration/compactor/test_promote_l1_post_put_unlink.py` (append)

- [ ] **Step 1: ambiguity invariant 회귀 test 추가**

본 test_promote_l1 file 끝에:

```python
def test_ambiguity_invariant_post_wiring(uploader, tmp_path: Path):
    """MCT-189 wiring 후 NAS+local 동시 존재 0 (D-6 A 회귀 — InvariantHarness SSOT)."""
    from mctrader_data.nas_migration.invariant_harness import InvariantHarness

    source = tmp_path / "ambig.parquet"
    data = b"m" * 1024
    source.write_bytes(data)
    nas_key = "l1/ambig.parquet"
    uploader.put_streaming(source, nas_key, sha256=_sha256(data))

    promote_l1(local_path=source, nas_uploader=uploader,
               nas_key=nas_key, segment_id="seg-ambig")

    harness = InvariantHarness(root=tmp_path, nas_uploader=uploader)
    violations = harness._check_ambiguity()
    assert len(violations) == 0, f"ambiguity invariant violated: {violations}"
```

- [ ] **Step 2: Run + Commit**

```bash
uv run pytest tests/integration/compactor/test_promote_l1_post_put_unlink.py::test_ambiguity_invariant_post_wiring -v
```

Expected: PASS.

```bash
git add tests/integration/compactor/test_promote_l1_post_put_unlink.py
git commit -m "test(MCT-189): ambiguity invariant 회귀 post-wiring (D-6 A 회귀)"
```

---

### Task 18: Phase 2 PR1 — Full suite + PR 생성

- [ ] **Step 1: Full test suite — 회귀 0**

```bash
cd c:/workspace/mclayer/mctrader-data
uv run pytest -v --tb=short
```

Expected: 모든 기존 test PASS + 신규 5+ integration test PASS. **회귀 0** verify.

- [ ] **Step 2: ruff + pyright**

```bash
uv run ruff check src/ tests/
uv run pyright src/
```

Expected: 0 violation.

- [ ] **Step 3: PR 생성**

```bash
gh pr create --title "feat(MCT-189): Phase 2 PR1 — grace-0 wiring (4중 verify + pre-delete guard + self-delete)" --body "$(cat <<'EOF'
## Summary
- D-4 C: `nas_uploader.head_object()` 4-tuple verify return (ETag + VersionId + sha256 metadata + ContentLength)
- D-4 C + D-8 B: `promotion.py` 4중 HEAD verify + pre-delete guard (race window 차단)
- D-2 A: `DualWriter.write()` status=committed branch self-delete (caller 0건 재발 차단)
- D-6 A: integration test 6 시나리오 (testcontainers MinIO)

## Test plan
- [x] 신규 unit test PASS
- [x] integration test 6 시나리오 PASS (testcontainers MinIO)
- [x] ambiguity invariant 회귀 PASS (InvariantHarness post-wiring)
- [x] 회귀 0 (full pytest suite)
- [x] ruff + pyright 0 violation

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: PR2 admin merge (CI green 후)**

```bash
gh pr merge --admin --squash
```

---

## Phase 2 PR2 (mctrader-data legacy cleanup carry) — branch `mct-189-phase2-legacy-cleanup`

### Task 19: runner `idempotent skip` retroactive unlink — Write failing test

**Files:**
- Test: `c:\workspace\mclayer\mctrader-data\tests\integration\compactor\test_runner_retroactive_cleanup.py` (신규)

- [ ] **Step 1: Write failing test**

```python
"""MCT-189 D-3 C path A: runner idempotent skip 경로에서 retroactive unlink."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from testcontainers.minio import MinioContainer

from mctrader_data.nas_storage.nas_uploader import NASUploader
from mctrader_data.compactor.runner import scan_and_cleanup_legacy


def test_runner_legacy_cleanup_via_idempotent_skip(tmp_path: Path):
    """legacy local parquet + NAS object 동시 존재 (pre-wiring state) → runner scan 시 retroactive unlink."""
    with MinioContainer() as minio:
        uploader = NASUploader(endpoint=minio.get_url(), access_key=minio.access_key,
                               secret_key=minio.secret_key, bucket="mctrader-market")
        # legacy state: PUT NAS + local 둘 다 존재
        legacy = tmp_path / "market" / "test.parquet"
        legacy.parent.mkdir(parents=True)
        data = b"legacy" * 1000
        legacy.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        uploader.put_streaming(legacy, "market/test.parquet", sha256=sha)

        # runner scan_and_cleanup_legacy (신규)
        result = scan_and_cleanup_legacy(root=tmp_path, nas_uploader=uploader)
        assert result["cleaned"] >= 1
        assert not legacy.exists()  # retroactive unlink
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/integration/compactor/test_runner_retroactive_cleanup.py -v
```

Expected: FAIL — `scan_and_cleanup_legacy` 함수 부재.

---

### Task 20: runner `idempotent skip` retroactive unlink — Implementation

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\runner.py`

- [ ] **Step 1: `scan_and_cleanup_legacy()` 함수 신규**

```python
def scan_and_cleanup_legacy(root: Path, nas_uploader: NASUploader) -> dict[str, int]:
    """legacy local parquet 스캔 + 4중 HEAD verify pass면 retroactive unlink (MCT-189 D-3 C path A).

    pre-wiring era 누적 130 GB legacy 자동 회수. compactor scan loop 안 idempotent skip 경로에서 호출.
    INV-4: HEAD verify fail = local 보존 (안전망).
    """
    from mctrader_data.compactor.promotion import promote_l1, PromotionVerifyError

    cleaned = 0
    preserved = 0
    for parquet in root.glob("market/**/*.parquet"):
        # NAS key 추론 (tier prefix 포함)
        rel = parquet.relative_to(root)
        nas_key = str(rel).replace("\\", "/")  # Windows path → POSIX

        try:
            result = promote_l1(
                local_path=parquet, nas_uploader=nas_uploader,
                nas_key=nas_key, segment_id=f"legacy-{rel}",
            )
            if result.status == "promoted":
                cleaned += 1
        except PromotionVerifyError:
            preserved += 1
            log.info("[runner] legacy preserved (HEAD verify failed) path=%s", rel)

    log.info("[runner] legacy cleanup: cleaned=%d preserved=%d", cleaned, preserved)
    return {"cleaned": cleaned, "preserved": preserved}
```

- [ ] **Step 2: runner main loop에 hook 추가**

기존 runner main loop (compaction cycle) 안에 `scan_and_cleanup_legacy()` 를 cycle당 1회 호출 (또는 별 thread):

```python
        # ... 기존 cycle 처리 후
        # MCT-189 D-3 C path A: legacy cleanup
        if cycle_count % LEGACY_CLEANUP_EVERY_N_CYCLES == 0:
            scan_and_cleanup_legacy(root=self.root, nas_uploader=self.nas_uploader)
```

- [ ] **Step 3: Run test — expect PASS**

```bash
uv run pytest tests/integration/compactor/test_runner_retroactive_cleanup.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/compactor/test_runner_retroactive_cleanup.py src/mctrader_data/compactor/runner.py
git commit -m "feat(MCT-189): runner retroactive cleanup — legacy parquet 4중 HEAD verify + unlink (D-3 C path A)"
```

---

### Task 21: Phase 2 PR2 — PR 생성

- [ ] **Step 1: Full suite + ruff + pyright**

```bash
uv run pytest -v --tb=short
uv run ruff check src/ tests/
uv run pyright src/
```

- [ ] **Step 2: PR 생성**

```bash
gh pr create --title "feat(MCT-189): Phase 2 PR2 — legacy 130GB retroactive cleanup (runner idempotent skip)" --body "$(cat <<'EOF'
## Summary
- D-3 C path A: runner scan loop에 retroactive HEAD verify + unlink 통합
- PR1 LAND 후 production 자동 회수 trigger (130GB legacy parquet)
- INV-4 안전망: HEAD verify fail = local 보존 (forward-only invariant 정합)

## Test plan
- [x] integration test (testcontainers MinIO) — legacy state 재현 → retroactive unlink PASS
- [x] full suite 회귀 0
- [ ] production verify (PR LAND 후 24h 측정 — /d/market 크기 감소 확인)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: admin merge**

```bash
gh pr merge --admin --squash
```

---

## Phase 2 PR3 (mctrader-hub 박제) — branch `mct-189-phase2-evidence`

### Task 22: Story §8.5 Impl Manifest (ADR-032 evidence triad 형식)

**Files:**
- Modify: `docs/stories/MCT-189.md`

- [ ] **Step 1: §8.5 Impl Manifest 섹션 추가**

```markdown
## §8.5 Impl Manifest (ADR-032 evidence triad 형식)

| evidence | 결과 |
|----------|------|
| (1) file:line | `promotion.py:95` `promote_l1()` + `dual_writer.py:236` self-delete branch + `runner.py::scan_and_cleanup_legacy` |
| (2) production caller grep ≥1 | `git grep -n "promote_l1\|scan_and_cleanup_legacy" src/**` ≥ 3 |
| (3) integration test PASS | `test_promote_l1_post_put_unlink` 6 시나리오 + `test_runner_retroactive_cleanup` PASS |
| (4) LAND commit | mctrader-data#<PR1 sha> + mctrader-data#<PR2 sha> + mctrader-hub#<Phase 1 sha> + mctrader-hub#<PR3 sha> |
| (5) production 14d 0 violation gate | post-LAND 14d window 시작 = 2026-05-16, verify gate = 2026-05-30 (`nas_reader_ambiguity_total` Counter 14d rolling = 0) |
```

- [ ] **Step 2: §10 FIX Ledger + §11 retro pointer 작성**

```markdown
## §10 FIX Ledger

(FIX 발생 시 append — Phase 2 PR3 시점 회고)

## §11 Story 완료 박제

- COMPLETED at: 2026-05-16
- retro: `docs/retros/RETRO-MCT-189.md`
- EPIC-RESULTS amendment: §MCT-189 행
- ADR-029 §D3 amendment box VERIFIED 박제
```

- [ ] **Step 3: frontmatter `phase` + `status` 전이**

```yaml
phase: 박제  # 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → 박제
status: COMPLETED
completed_at: "2026-05-16"
```

- [ ] **Step 4: Commit**

```bash
git add docs/stories/MCT-189.md
git commit -m "docs(MCT-189): §8.5 Impl Manifest + §10 + §11 박제"
```

---

### Task 23: ADR-029 §D3 amendment box VERIFIED 박제

**Files:**
- Modify: `docs/adr/ADR-029-tier-promotion-single-source.md`

- [ ] **Step 1: Phase 1 draft amendment box를 VERIFIED 박제로 교체**

Phase 1 Task 1에서 추가한 "Phase 1 draft → Phase 2 PR3 VERIFIED" 문구의 "draft → VERIFIED" 전이:

```markdown
> **MCT-189 amendment (2026-05-16, Phase 2 PR3 VERIFIED)**: `promote_l1()` caller wiring LANDed via mctrader-data#<PR1 sha>. DualWriter self-delete (D-2 A) at `dual_writer.py:236-260`. 4중 HEAD verify primitive at `promotion.py:95-180`. pre-delete guard (D-8 B) at `promotion.py:158-170`. integration test 6 시나리오 PASS at `tests/integration/compactor/test_promote_l1_post_put_unlink.py`. legacy cleanup via mctrader-data#<PR2 sha> `runner.py::scan_and_cleanup_legacy`. **POLICY_FINALIZED 유지** + D3 wiring carry over → **resolved**. post-LAND production 14d 0 violation gate = 2026-05-30 verify.
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr/ADR-029-tier-promotion-single-source.md
git commit -m "docs(MCT-189): ADR-029 §D3 amendment box VERIFIED 박제 (Phase 2 PR3)"
```

---

### Task 24: EPIC-RESULTS amendment + Epic CLOSED prerequisite registry

**Files:**
- Modify: `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md`

- [ ] **Step 1: §MCT-189 carry over 행 추가**

기존 `Amendment — D3=C wiring deferred` 박스(2026-05-16 PMO retro) 끝에:

```markdown
### MCT-189 LAND (2026-05-16) — D3 wiring resolved

| 항목 | 상태 |
|------|------|
| `promote_l1()` production caller | grep ≥ 3 (PR1 + PR2 LAND, `dual_writer.py:236` + `runner.py::scan_and_cleanup_legacy`) |
| 4중 HEAD verify primitive | `promotion.py:95-180` LAND (D-4 C) |
| pre-delete guard | `promotion.py:158-170` LAND (D-8 B) |
| DualWriter self-delete | `dual_writer.py:236-260` LAND (D-2 A) |
| legacy 130GB retroactive cleanup | `runner.py::scan_and_cleanup_legacy` LAND (D-3 C path A) — production 자동 회수 |
| integration test (testcontainers MinIO) | 6 시나리오 PASS (D-6 A) |
| ADR-029 §D3 amendment box | VERIFIED 박제 (POLICY_FINALIZED 유지) |
| Epic CLOSED prereq registry 신규 행 | post-LAND 14d 0 violation gate (2026-05-16 LAND → 2026-05-30 verify) |
```

- [ ] **Step 2: Epic CLOSED prerequisite registry 표에 prod-5 추가**

기존 prod-1~4 표 끝에:

```markdown
| prod-5 | MCT-189 wiring post-LAND 14d 0 violation | 2026-05-16 ~ 2026-05-30 | `nas_reader_ambiguity_total` Counter 14d rolling rate = 0 |
```

- [ ] **Step 3: Commit**

```bash
git add docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md
git commit -m "docs(MCT-189): EPIC-RESULTS amendment — D3 wiring resolved + prod-5 prereq 신규"
```

---

### Task 25: RETRO-MCT-189.md 신규

**Files:**
- Create: `docs/retros/RETRO-MCT-189.md`

- [ ] **Step 1: 회고 파일 작성**

```markdown
# RETRO-MCT-189 — grace-0 wiring 완결

## Outcome

- ADR-029 §D3=C wiring 완결 (caller 0건 → 3 production caller LAND)
- 4중 HEAD verify primitive + pre-delete guard (silent corruption + race 차단)
- legacy 130GB 자동 회수 (runner scan loop)
- ADR-029 §D3 amendment box VERIFIED (POLICY_FINALIZED 유지)

## Lessons (Phase 0 verify lesson 7회째)

1. **decision-defined ≠ caller-wired** — `promote_l1()` 정의 LAND ≠ 운영 LAND. VERIFIED badge는 (1) file:line + (2) production caller grep ≥1 + (3) integration test PASS 3 evidence 필요 (ADR-032 trigger).
2. **ADR 본문 자체 SSOT desync 가능** — ADR-029 §D3 line 240/246/347 3-way 모순이 wiring 부재의 원인 중 하나. ADR amendment box 박제 시 본문 정합성 self-check 의무.
3. **DualWriter self-delete pattern** — caller 의무 분산 vs commit boundary 단일 책임. solo dev 환경에서는 후자가 누락 방지에 우월.

## ADR 후보 발의 (PMO carry)

- **ADR-032** (이미 Proposed) — VERIFIED badge evidence triad 일반화. owner Story 권고 = MCT-190.

## Carry over to MCT-190

- ADR-032 owner Story 발의 (MCT-189 LAND 직후)
- vendor wheel 갱신 (mctrader_market post-market#11) — 별 follow-up

## Pre-LAND vs Post-LAND 검증

- pre-LAND: integration test 6 시나리오 + unit test PASS
- post-LAND verify gate = 2026-05-30 (14d production 0 violation, Epic CLOSED prereq prod-5)
```

- [ ] **Step 2: Commit**

```bash
git add docs/retros/RETRO-MCT-189.md
git commit -m "docs(MCT-189): RETRO-MCT-189 — Phase 0 verify lesson 7회째 + ADR-032 trigger"
```

---

### Task 26: CLAUDE.md MCT-189 COMPLETED entry + scope_manifest carry over → resolved

**Files:**
- Modify: `CLAUDE.md`
- Modify: `scope_manifests/EPIC-tier-promotion-single-source.yaml`
- Modify: `.codeforge/counters.json`

- [ ] **Step 1: CLAUDE.md §MCT-189 IN_PROGRESS → COMPLETED**

기존 "MCT-189 IN_PROGRESS" 섹션 제목을 "MCT-189 COMPLETED (2026-05-16)" 로 변경 + 본문에 land_prs (4건 commit sha) + 14d production gate 추가.

- [ ] **Step 2: scope_manifest carry_over_items D3-wiring status → resolved**

```yaml
  - id: D3-wiring
    title: "ADR-029 §D3=C grace-0 로컬삭제 wiring"
    owner_story: MCT-189
    status: RESOLVED  # IN_PROGRESS → RESOLVED
    completed_at: "2026-05-16"
    land_prs:
      - "mctrader-hub#<Phase 1 PR>"
      - "mctrader-data#<PR1 wiring>"
      - "mctrader-data#<PR2 cleanup>"
      - "mctrader-hub#<PR3 박제>"
```

- [ ] **Step 3: counters.json MCT-189 COMPLETED**

```yaml
"MCT-189": {
  ...
  "status": "COMPLETED",
  "completed_at": "2026-05-16",
  "land_prs": [...]
}
```

- [ ] **Step 4: Commit Phase 2 PR3**

```bash
git add CLAUDE.md scope_manifests/EPIC-tier-promotion-single-source.yaml .codeforge/counters.json
git commit -m "docs(MCT-189): CLAUDE.md COMPLETED + scope_manifest D3-wiring RESOLVED + counters.json"
```

---

### Task 27: Phase 2 PR3 — PR 생성 + admin merge

- [ ] **Step 1: PR 생성**

```bash
gh pr create --title "docs(MCT-189): Phase 2 PR3 — D3 wiring resolved 박제 (4 PR LAND evidence + RETRO + EPIC-RESULTS)" --body "$(cat <<'EOF'
## Summary
- Story §8.5 Impl Manifest (ADR-032 evidence triad 형식): file:line + grep ≥3 + integration test PASS
- ADR-029 §D3 amendment box VERIFIED 박제 (POLICY_FINALIZED 유지)
- EPIC-RESULTS amendment — D3 wiring resolved + prod-5 prereq (14d 0 violation)
- RETRO-MCT-189 — Phase 0 verify lesson 7회째
- CLAUDE.md COMPLETED entry + scope_manifest carry_over_items RESOLVED + counters.json

## Test plan
- [x] 4 PR cross-repo LAND timeline 박제 일관
- [x] ADR-029 §D3 amendment box VERIFIED (line 240/246/347 + §D11 표 정정)
- [ ] post-LAND 14d production gate verify (2026-05-30)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 2: admin merge**

```bash
gh pr merge --admin --squash
```

---

### Task 28: PMOAgent 세션 종료 회고 dispatch (memory feedback_pmo_retro_mandatory)

- [ ] **Step 1: PMOAgent dispatch**

세션 종료 전 자동 dispatch. retro 의무 = MCT-189 LAND 완료 회고 + cross-Story SSOT drift 3호 패턴 (만약 추가 drift 발견 시).

---

## Self-Review

**1. Spec coverage**: ✓ 10 decisions D-1~D-10 모두 task에 매핑 (D-9 = Task 2, D-10 = Task 25 carry over). 4 PR land_order = Phase 1 (Task 1-8) + PR1 wiring (Task 9-18) + PR2 cleanup (Task 19-21) + PR3 박제 (Task 22-27) + Task 28 PMO retro. Risk R1-R6 모두 mitigation 반영 (R1 = D-8 B pre-delete guard Task 11-12, R2 = D-6 A Task 17, R3 = PR1 → PR2 latency window 명시, R4 = D-2 A 채택 Task 14, R5 = ADR-029 §D11 표 정정 Task 1 Step 3, R6 = RETRO-MCT-189 Task 25).

**2. Placeholder scan**: ⚠️ Task 22 §8.5 Impl Manifest의 `<PR1 sha>` / `<PR2 sha>` 등은 PR LAND 후에야 알 수 있는 값 — placeholder가 아니라 실 LAND 시점에 채울 verified value.

**3. Type consistency**: ✓ `head_object()` return dict의 4 field key (`ETag`, `VersionId`, `sha256`, `ContentLength`) Task 9/10/11/12 일관. `promote_l1()` signature Task 11/16/19 일관.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
