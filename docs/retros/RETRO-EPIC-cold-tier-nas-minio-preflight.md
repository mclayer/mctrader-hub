---
type: epic-preflight-retro
epic_key: EPIC-cold-tier-nas-minio
epic_title: "Cold Tier on NAS MinIO — Spike + Migration"
preflight_pr: mclayer/mctrader-hub#243
preflight_merge_sha: f816c8ce9c658ea8e31cf5c8ea4315a1e972462b
preflight_merged_at: 2026-05-12T09:20:49Z
retro_author: PMOAgent
retro_date: 2026-05-12
related_milestones: [3, 4]
planned_stories: [MCT-147, MCT-148, MCT-149, MCT-150, MCT-151, MCT-152, MCT-153, MCT-154, MCT-155]
planned_adrs: [ADR-027]
status: preflight-complete
next_action: spawn MCT-147 (RequirementsPLAgent lane)
---

# RETRO — EPIC-cold-tier-nas-minio Preflight

## 1. Epic preflight quality 평가

### 1.1 scope_manifest 완성도 (`scope_manifests/EPIC-cold-tier-nas-minio.yaml`, 397 line)

| 영역 | 박제 상태 | 평가 |
|------|-----------|------|
| 11 결정점 D1~D11 | 11/11 (decision + rationale 박제) | **A**. Codex GPT-5 11 결정점 일괄 review → Sonnet 합성 → 사용자 final approve 의 전 trail 이 YAML 본문에 보존됨. 후속 Story (특히 MCT-149 ADR-027 author) 가 D1~D11 을 직접 인용 가능. |
| 위험 R1~R9 | 9/9 (likelihood + impact + mitigation 3종 매핑) | **A**. NAS 가용성·dual-write metric·cache invalidation·partial migration·GC data loss·secret leak·TLS·ADR rework·spike evidence reuse 충돌까지 식별. 각 R 의 mitigation 이 구체 Story 번호 와 매핑돼 가시성 우수. |
| 병렬화 판정 (`parallelism_decision`) | Stage 1 serial · Stage 2 phase 2A~2E 명시 | **A**. PMOAgent 규칙 1~4 (file disjoint / interface+첫구체 / shared file / 통합 gate) 모두 인용 — phase 2C 만 병렬 (MCT-152 mctrader-data scripts ↔ MCT-154 mctrader-engine, 파일 경로 disjoint = 규칙 1) + `feedback_parallel_session_branch_race` memory 반영해 별도 worktree 의무화. |
| `planned_files` | 9 Story × 36 file 경로 사전 정의 | **A**. 후속 ArchitectPLAgent 의 Change Plan 작성 시 inventory 가 이미 박제돼 있어 재발견 비용 0. CodebaseMapper 호출 의무 약화. |
| `planned_claude_md_sections` | 3 repo × 4 section 매핑 | **A-**. mctrader-hub / mctrader-data / mctrader-engine 모두 CLAUDE.md 갱신 지점 사전 식별. 단, mctrader-data engine 측 `## ADR Index` 갱신 (ADR-027 reference) 항목 누락 — Story 진입 시 DocsAgent 가 보충 필요. |
| `epic_milestones` (gate 정의) | Stage 1/2 각각 on_pass · on_fail 분기 명시 | **A**. Stage 1 fail = Stage 2 진입 금지 + Codex review escalate, Stage 2 fail = rollback runbook (MINIO_ENDPOINT local 복귀, 7일 grace 활용) 명시. |
| `prerequisites` / `out_of_scope` | ADR-017 보존 + ADR-016 분리 + Synology Container Manager + btrfs volume 명시 / web admin_audit.sqlite + market/market-bithumb/web 코드 변경 제외 명시 | **A**. scope creep 방지 — 추후 누군가 web admin_audit 까지 묶으려 할 때 이 YAML 인용으로 차단 가능. |

**총평**: **A (95/100)**. 본 preflight 는 codeforge consumer 측 Epic 분해 산출물의 **모범 사례**. 종래 RETRO-MCT-112 (Epic-final retro) 가 9 Story 종료 후에야 박제했던 정보 (의존성·병렬성·결정점·위험)를 **Epic 진입 전에 사전 박제** 했다는 점에서 RETRO-MCT-112 패턴 대비 진전.

### 1.2 Story 분해의 codeforge convention 준수도

| 항목 | 준수 여부 | 비고 |
|------|----------|------|
| `mctrader-hub.next` 카운터 reservation (147→156 + 9 keys) | OK | `.codeforge/counters.json` 가 SSOT, conflict 회피 위해 PR merge 후 즉시 다른 Story spawn 가능. |
| ADR 번호 reservation (`docs/adr/.reservation-ADR-027.md`) | OK | placeholder 패턴으로 동시 ADR 번호 충돌 방지 — ADR-026 다음 27 정확. |
| `phase_pair` 명시 (phase1_only vs phase1_phase2) | OK | 9 Story 중 4 = phase1_phase2 (PR pair 의무 — MCT-150/151/153/154), 5 = phase1_only (infra/docs/ADR/migration script/cutover). |
| `depends_on` 위상 정렬 | OK | 147 → 148 → 149 → 150 → 151 → {152, 154 (병렬)} → 153 → 155. cycle 없음. |
| `repo` 분포 명시 | OK | hub 3 (147, 149, 155) + data 5 (148, 150, 151, 152, 153) + engine 1 (154). |
| stage 분리 (1 spike / 2 migration) | OK | Stage 1 evidence pack land 전 Stage 2 진입 금지 gate 명시. |
| 사용자 명시 분해 (1)(2)(3) ↔ codeforge 9 Story 매핑 | A- (§2.2 참조) | 자연스러운 매핑이지만 1:1 이 아닌 1:N 분해 — 의도 보존 검증 추가 필요. |

**준수도**: **A**. codeforge plugin 의 ADR-031 (Story KEY reservation) + ADR-032 (Epic-first scope_manifest) 두 convention 모두 준수.

---

## 2. Trend / 패턴 분석

### 2.1 ADR-034 Amendment 2 (Phase 0 자동 실행) 부합도

본 Epic 의 brainstorm 흐름:

```
사용자 발의 (WebDAV/MinIO 직접 발의)
  ↓
Phase 0 (4 agent 병렬 burst) — DomainAgent / ResearcherAgent / RequirementsAnalystAgent / PMOAgent
  ↓
[Researcher 발견] WebDAV semantic gap + minio/minio#14060 → 옵션 A (NAS Container Manager + MinIO native)
[Analyst 발견] 추정 동기 ↔ 실제 필요 불일치 → WHY = 디스크 용량 부족 → tiered storage 정답
  ↓
Phase 1: Codex (GPT-5) 11 결정점 일괄 review → Sonnet 합성 → 사용자 final approve
  ↓
Phase 2: PMOAgent 2nd pass — 9 Story + 1 ADR + scope_manifest 초안
  ↓
preflight PR #243 MERGED
```

**ADR-034 Amendment 2 (`codeforge:codeforge-brainstorm` skill 의 Phase 0 자동 실행) 부합도: 100%**.

Phase 0 의 4 agent 병렬 burst 가 `feedback_brainstorm_codex_review_pattern` memory ("Q-by-Q 사용자 stop 금지, 모든 open design 결정점 Codex 일괄 dispatch → Sonnet 합성") 와 정합. Researcher 의 minio/minio#14060 발견이 사용자 원안 (WebDAV) 의 unknown unknown 을 사전 차단 — Phase 0 자동 burst 의 명백한 가치 사례.

**개선 후보 (codeforge brainstorm skill 측)**:
- Phase 0 burst 결과 중 "사용자 원안 번복" (WebDAV → Container Manager native) 이 일어난 사례를 brainstorm skill 의 `case_studies/` 에 박제하면, 향후 사용자 원안의 implementation detail 이 anti-pattern 인 경우 더 빠르게 detection 가능. → ADR 후보 §3.3 으로 발의.

### 2.2 사용자 명시 분해 (1)(2)(3) ↔ codeforge 9 Story 매핑

사용자 원안:

> 작업 분해: (1) MinIO 컨테이너에 WebDAV 부착 / (2) MinIO 컨테이너로 데이터 경로 변경 / (3) 기존 적재 데이터 이관

codeforge 9 Story 매핑:

| 사용자 (1)(2)(3) | codeforge Story | 자연스러움 |
|------|------|----------|
| (1) WebDAV 부착 → **번복**: NAS Container Manager + MinIO native (WebDAV 제거) | MCT-147 (deploy) + MCT-148 (PoC) + MCT-149 (ADR-027) | A. WebDAV→MinIO native 결정 자체가 D8 (5종 PoC) 로 박제되어 사용자 원안의 implementation detail 변경이 spike Story 1건으로 흡수됨. |
| (2) 데이터 경로 변경 | MCT-150 (uploader) + MCT-151 (dual-write) + MCT-154 (reader cache) + MCT-155 (cutover) | A-. 4 Story 로 펼쳐졌으나 각 Story 가 다른 concern (uploader 강화 / dual-write 일관성 / reader cache / hub cutover) — concerns separation 으로 타당. 단, "데이터 경로 변경" 이 한 사용자 요구 = 4 Story 가 묶여서 fail-safe rollback 가능해야 함 (Stage 2 milestone gate 가 이를 흡수). |
| (3) 기존 적재 데이터 이관 | MCT-152 (mc-mirror) + MCT-153 (GC 7일 grace) | A. forward-only invariant + 7일 grace + dry-run lock 으로 사용자 의도 "이관" 의 안전성 보장. |

**총평**: **A (자연스러움 양호)**. 1:N 분해 (1→3, 2→4, 3→2) 가 발생했지만 각 분해가 concerns separation 또는 PoC-by-PoC fail-safe 로 합리화 가능. 사용자 의도 보존을 위해 Stage 2 milestone gate 가 4 Story 통합 검증을 의무화한 것이 핵심 안전장치.

### 2.3 phase-gate-mergeable doc-only fast-pass blind spot

**관찰**: PR #243 의 변경 파일 3개 모두 doc-only/manifest:
- `.codeforge/counters.json` (manifest, 9 line diff)
- `docs/adr/.reservation-ADR-027.md` (신규 placeholder)
- `scope_manifests/EPIC-cold-tier-nas-minio.yaml` (신규 디렉터리 397 line)

phase-gate-mergeable 의 `isDocOnly` 판정 (line 135-142):
```javascript
const isDocOnly = !hasCode && files.every(f =>
  f.filename.endsWith('.md') ||
  f.filename.startsWith('docs/') ||
  f.filename.startsWith('wrapper/') ||
  f.filename.startsWith('.github/') ||
  f.filename === 'CHANGELOG.md' ||
  f.filename === 'README.md'
);
```

**`.codeforge/` 와 `scope_manifests/` 접두 미인식** → `isDocOnly = false` → 우회 위해 `type:epic` 라벨 부여 (line 134 `isEpicLabel`) → fast-pass 통과. 라벨 우회 자체는 정상 동작이지만, **본 PR 은 doc-only 의 성격을 띠는 manifest PR** — type:epic 라벨이 없었다면 무한정 ACTION_REQUIRED 상태 (CFP-106 #143 fix 의 회귀).

**재발 가능성**: **HIGH**. 이유:
1. codeforge plugin 채택 consumer (mctrader-hub 외 다른 mclayer org repo) 가 동일 Epic preflight pattern 적용 시 동일 manifest 디렉터리 (`.codeforge/counters.json` 갱신 + `scope_manifests/EPIC-*.yaml` 신규) 가 발생.
2. `type:epic` 라벨이 누락된 preflight PR 의 경우 phase-gate-mergeable 가 ACTION_REQUIRED 로 영구 대기 — solo dev 의 admin merge 의존 강제.
3. 본 retro 작성 시점 (2026-05-12) 기준 mctrader-hub 만 codeforge consumer 이나, ADR-031/032 reservation pattern 가 정착된 후 다른 repo (mctrader-data, mctrader-engine, mctrader-web, mctrader-market 등) 에서도 동일 manifest 디렉터리 사용 가능성.

→ ADR 후보 §3.1 로 발의.

---

## 3. ADR 후보 발의 (codeforge plugin 측)

PMOAgent 가 **inline ADR draft** 형태로 codeforge plugin 의 ArchitectAgent 에 escalate. 본 retro 작성 시점에서 발의:

### 3.1 ADR-NNN: phase-gate-mergeable doc-only fast-pass 에 codeforge manifest 접두 추가

**Category**: Infrastructure (CI workflow policy)
**Trigger**: mctrader-hub#243 (EPIC-cold-tier-nas-minio preflight) — `.codeforge/counters.json` + `scope_manifests/EPIC-*.yaml` doc-only 임에도 `isDocOnly = false` → type:epic 라벨 의존 우회

**배경**: CFP-106 #143 fix 가 mctrader debug F6 단계에서 `type:epic` 라벨 + 일반 doc 경로 (`docs/`, `wrapper/`, `*.md`, `.github/`) 의 fast-pass 를 도입했으나, codeforge plugin 의 ADR-031 (counter reservation) + ADR-032 (Epic-first scope_manifest) 가 정착된 후 등장한 **manifest 디렉터리** (`.codeforge/`, `scope_manifests/`) 가 fast-pass 화이트리스트에 미포함.

**문제**:
- Preflight PR (manifest-only) 가 `type:epic` 라벨 누락 시 phase-gate-mergeable 의 ACTION_REQUIRED 무한 대기 → admin merge 강제.
- Solo dev (mclayer org owner) 환경에서 메모리 `feedback_admin_merge_autonomy` 로 우회 가능하나, 다중 dev consumer 채택 시 회귀 가능.

**제안 결정**: `phase-gate-mergeable.yml` 의 `isDocOnly` 판정에 다음 접두 추가:
```javascript
f.filename.startsWith('.codeforge/') ||
f.filename.startsWith('scope_manifests/') ||
```

**예상 결과**: codeforge consumer 의 Epic preflight PR 이 `type:epic` 라벨 의존 없이도 fast-pass 통과. CFP-106 #143 fix 의 의도 보존 (admin merge 부담 회피).

**검증 조건**: 본 변경 후 mctrader-hub#243 형식 PR (`.codeforge/` + `scope_manifests/` 만 변경, type:epic 라벨 미부여) 이 phase-gate-mergeable success conclusion 획득.

**플러그인 측 위치**: `plugins/codeforge/.../phase-gate-mergeable.yml` (consumer overlay 또는 upstream template).

### 3.2 ADR-NNN: `scope_manifests/` 디렉터리의 codeforge convention 화

**Category**: Architecture (codeforge consumer-facing directory convention)
**Trigger**: mctrader-hub#243 가 `scope_manifests/EPIC-cold-tier-nas-minio.yaml` 신규 디렉터리로 도입했으나 codeforge plugin SSOT (ADR 또는 wrapper) 에 convention 부재

**배경**: codeforge plugin 의 PMOAgent 가 Epic 분해 자문 시 scope_manifest YAML 박제 의무가 있으나, **저장 위치 convention 부재** (현재는 `scope_manifests/EPIC-*.yaml` ad-hoc 명명). consumer 별 위치 divergence 가능.

**문제**:
- consumer 별 manifest 위치 분기 시 codeforge plugin 의 후속 Story spawn agent 가 manifest discovery 비용 발생.
- ADR-032 (Epic-first scope_manifest) 에서 위치 규약을 정의하지 않은 상태.

**제안 결정**: codeforge plugin 측에서 표준 위치 SSOT 화:
- 경로: `scope_manifests/EPIC-<slug>.yaml`
- schema v1: 본 retro §1.1 의 11 항목 (epic / design_decisions / planned_stories / planned_adrs / planned_files / planned_claude_md_sections / epic_milestones / parallelism_decision / risk_register / ownership / references) 필수.
- ADR 후보: ADR-032 amendment 또는 신규 ADR-NNN.

**예상 결과**: 모든 codeforge consumer repo 의 Epic preflight 가 동일 schema YAML 박제 — PMOAgent · ArchitectPLAgent · DeveloperPLAgent 의 cross-repo handoff 비용 절감.

**검증 조건**: codeforge plugin upstream SSOT 갱신 후, mctrader-hub 의 `scope_manifests/EPIC-cold-tier-nas-minio.yaml` 가 새 schema lint 통과.

### 3.3 ADR-NNN (선택): Phase 0 burst 결과의 "사용자 원안 번복" 사례 박제

**Category**: Architecture (codeforge brainstorm skill knowledge base)
**Trigger**: 본 Epic 에서 사용자 원안 WebDAV → Phase 0 Researcher 가 minio/minio#14060 발견 → 옵션 A (Container Manager + MinIO native) 로 번복. **사용자 implementation detail 의 anti-pattern 사전 차단** 사례.

**제안**: codeforge brainstorm skill 의 `case_studies/` 또는 `playbook §X` 에 본 사례 박제 — Phase 0 Researcher 의 "minio/minio#14060 같은 upstream issue 검색" 패턴이 implementation detail anti-pattern 차단의 표준 절차임을 명시.

**우선순위**: LOW (§3.1 / §3.2 보다 후순위, 실제 brainstorm skill 사용자가 benefit 측정 필요).

---

## 4. Pre-flight checklist 박제

### 4.1 preflight 완료 항목 (PR #243 MERGED 시점)

- [x] **scope_manifest 작성** — `scope_manifests/EPIC-cold-tier-nas-minio.yaml` (397 line, 11 결정점 + 위험 R1~R9 + 병렬 판정 + planned_files 박제)
- [x] **카운터 reservation** — `.codeforge/counters.json` mctrader-hub.next 147→156 + 9 keys (MCT-147~155)
- [x] **ADR 번호 reservation** — `docs/adr/.reservation-ADR-027.md` placeholder
- [x] **GitHub Milestone 생성** — #3 Epic-cold-tier-stage-1-spike, #4 Epic-cold-tier-stage-2-migration
- [x] **brainstorm trail 박제** — `.tmp/brainstorm-cold-tier-nas-minio.md` (Phase 0/1/2 합의 본문)
- [x] **plan 박제** — `.tmp/plan-cold-tier-nas-minio.md`
- [x] **preflight PR merge** — #243 type:epic 라벨 fast-pass 통과 (CFP-106 #143 fix path)

### 4.2 다음 단계 (MCT-147 spawn 절차)

```
Step 1. RequirementsPLAgent spawn (MCT-147)
        input: scope_manifests/EPIC-cold-tier-nas-minio.yaml + MCT-147 row + planned_files
        output: docs/stories/MCT-147.md §1-6 (requirements 박제)

Step 2. ArchitectPLAgent spawn (MCT-147)
        input: MCT-147.md §1-6 + scope_manifest D1/D2/D3/D7/D8 + ADR-017/008
        output: docs/stories/MCT-147.md §7 (Change Plan) — docker-compose.yml + runbook 2종

Step 3. DeveloperPLAgent spawn (MCT-147)
        input: §7 Change Plan + planned_files (5개 — docker/minio/docker-compose.yml + README + runbook 2종 + Story §1-6)
        output: 실 파일 5개 author + tests 없음 (infra Story)

Step 4. CodeReviewPLAgent spawn (MCT-147)
        input: §7 + §8.5 Impl Manifest
        output: docs/stories/MCT-147.md §9 (review pass)

Step 5. PMOAgent retro (MCT-147 완료)
        memory feedback_pmo_retro_mandatory 의무 트리거
        output: docs/retros/RETRO-MCT-147.md + Story §11 retro pointer

Gate (Step 6 진입 자격):
  MCT-147 MERGED + NAS MinIO endpoint 가용 (Synology Container Manager up)
  → MCT-148 (PoC 5종) spawn

Gate (Step 7 진입 자격):
  MCT-148 MERGED + 5종 PoC ALL PASS evidence pack land
  → MCT-149 (ADR-027 author) spawn
  주의: PoC 결과로 결정점 D1~D8 번복 시 ADR-027 rework — risk R8 mitigation per scope_manifest

Gate (Stage 1 종료):
  MCT-149 MERGED + ADR-027 status=Accepted
  → Stage 2 brainstorm 재실행 권고 (PoC 결과 반영, scope_manifest D9~D11 재검토)
  → Stage 2 진입 자격 milestone #3 close
```

### 4.3 PMOAgent 모니터링 의무 (Stage 1 진행 중)

- [ ] MCT-147 land 후 cross-Story FIX 패턴 분석 시작 (RETRO-MCT-147 + Story §11)
- [ ] MCT-148 evidence pack land 직후 quick audit gate — D1~D8 번복 여부 검토 (scope_manifest R8 mitigation)
- [ ] MCT-149 ADR-027 author 직전 brainstorm Phase 0 재실행 권고 평가 (PoC 결과 → 결정점 영향 확인)
- [ ] Stage 1 종료 시 본 retro `status` frontmatter 갱신: `preflight-complete` → `stage-1-complete`

### 4.4 ADR 후보 escalate 의무

본 retro §3.1 / §3.2 ADR draft 를 다음 PMOAgent dispatch 시점에 codeforge plugin ArchitectAgent 에 escalate:
- escalate trigger: 본 retro land 직후 (즉시)
- payload: `pmo_output v1.adr_proposal` 필드 (codeforge-pmo CLAUDE.md §4 ADR 후보 발의 schema)
- 처리: Orchestrator → codeforge-design plugin → ArchitectAgent → 신규 ADR file author (`status=Proposed`)

---

## 5. 한줄 요약

본 preflight 는 codeforge consumer Epic 분해의 **모범 사례 (A 95/100)** — Phase 0 burst 가 사용자 implementation detail (WebDAV) 의 anti-pattern 을 사전 차단했고, 9 Story / 11 결정점 / 위험 9 / 병렬화 판정 / planned_files 36 개가 Epic 진입 전에 박제됨. **개선 후보 2건** (phase-gate-mergeable `.codeforge/` + `scope_manifests/` 접두 추가, scope_manifests 위치 SSOT 화) 을 codeforge plugin ArchitectAgent 에 escalate.
