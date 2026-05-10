# MCT-129: 6-repo CLAUDE.md codeforge 4종 업그레이드 반영 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader 5개 impl repo (market/market-bithumb/data/engine/web)의 `.claude/_overlay/CLAUDE.md` 에 MCT-127(codeforge 4종 업그레이드) 내용을 반영하고, Story workflow 통합테스트 phase + Agent model tier 섹션 + plugin 업그레이드 체크리스트 포인터를 추가

**Architecture:** 5개 impl repo의 동일 구조 CLAUDE.md에 동일 패턴 추가. 각 repo는 독립적으로 수정 가능(파일 경로 disjoint). MCT-128 완료 후 실행 (hub CLAUDE.md 체크리스트 포인터 대상 선행 필수). 5 repo 내부는 병렬 처리 가능하나 Task 구조상 순차 작성.

**Tech Stack:** git, grep

**전제조건**: MCT-128 완료 및 push 확인 후 이 플랜 실행

---

## 파일 구조

| 파일 | 변경 유형 |
|------|----------|
| `../mctrader-market/.claude/_overlay/CLAUDE.md` | modify (append) |
| `../mctrader-market-bithumb/.claude/_overlay/CLAUDE.md` | modify (append) |
| `../mctrader-data/.claude/_overlay/CLAUDE.md` | modify (append) |
| `../mctrader-engine/.claude/_overlay/CLAUDE.md` | modify (append) |
| `../mctrader-web/.claude/_overlay/CLAUDE.md` | modify (append) |
| `docs/stories/MCT-129.md` (mctrader-hub) | create |

## 공통 추가 블록 (5개 repo 동일)

아래 블록을 각 repo `.claude/_overlay/CLAUDE.md` 파일 **끝**에 append한다.

```markdown

### plugin 버전 메모 (MCT-129, 2026-05-11)

codeforge 4종 최신 버전 (MCT-127/MCT-128 반영):

```
codeforge-design@mclayer        # 0.5.0 — CFP-319: ArchitectAgent WS stream push_interval 실증 의무
codeforge-develop@mclayer       # 0.4.0 — presets/docker-compose.test.yml (IntegrationTestAgent §8.6)
codeforge-test@mclayer          # REVIVED (ADR-055/CFP-367) — IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가); test-verdict-v2
codeforge-review@mclayer        # 1.2.0 — CFP-318: 3 ReviewPL bootstrap-labels.sh preflight; review-verdict v4
```

### Story workflow phase (MCT-129, 2026-05-11)

요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → CI 테스트 (ADR-048) → **통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2)** → 보안-테스트 → 완료 → PMO 회고 (의무)

### Agent model tier (ADR-042 Amendment 2, 2026-05-11)

InfraEngineerAgent·QADeveloperAgent·DataEngineerAgent = `claude-haiku-4-5` (기계적 패턴 실행 카테고리).
나머지 모든 agent = Sonnet 이상.

### Plugin 업그레이드 체크리스트

`mctrader-hub/.claude/_overlay/CLAUDE.md` §"codeforge 업그레이드 프로세스" (step 1~6) 참조.
```

---

### Task 1: mctrader-market CLAUDE.md 갱신

**Files:**
- Modify: `/c/workspace/mclayer/mctrader-market/.claude/_overlay/CLAUDE.md` (append)

- [ ] **Step 1: 현재 파일 끝 확인**

```bash
tail -5 /c/workspace/mclayer/mctrader-market/.claude/_overlay/CLAUDE.md
```

Expected: 파일이 35줄 정도이며 "신규 도메인 specialization agent" 로 끝남.

- [ ] **Step 2: 공통 블록 append**

파일 끝에 "공통 추가 블록" 전체를 추가한다.

최종 파일은 기존 35줄 + 추가 블록으로 구성.

- [ ] **Step 3: 검증**

```bash
grep -n "REVIVED\|IntegrationTestAgent\|claude-haiku-4-5\|업그레이드 체크리스트" \
  /c/workspace/mclayer/mctrader-market/.claude/_overlay/CLAUDE.md
```

Expected: 4개 키워드 각 1줄 이상 출력.

---

### Task 2: mctrader-market-bithumb CLAUDE.md 갱신

**Files:**
- Modify: `/c/workspace/mclayer/mctrader-market-bithumb/.claude/_overlay/CLAUDE.md` (append)

- [ ] **Step 1: 현재 파일 끝 확인**

```bash
tail -5 /c/workspace/mclayer/mctrader-market-bithumb/.claude/_overlay/CLAUDE.md
```

- [ ] **Step 2: 공통 블록 append**

파일 끝에 "공통 추가 블록" 전체를 추가한다.

- [ ] **Step 3: 검증**

```bash
grep -n "REVIVED\|IntegrationTestAgent\|claude-haiku-4-5\|업그레이드 체크리스트" \
  /c/workspace/mclayer/mctrader-market-bithumb/.claude/_overlay/CLAUDE.md
```

Expected: 4개 키워드 각 1줄 이상 출력.

---

### Task 3: mctrader-data CLAUDE.md 갱신

**Files:**
- Modify: `/c/workspace/mclayer/mctrader-data/.claude/_overlay/CLAUDE.md` (append)

- [ ] **Step 1: 현재 파일 끝 확인**

```bash
tail -5 /c/workspace/mclayer/mctrader-data/.claude/_overlay/CLAUDE.md
```

- [ ] **Step 2: 공통 블록 append**

파일 끝에 "공통 추가 블록" 전체를 추가한다.

- [ ] **Step 3: 검증**

```bash
grep -n "REVIVED\|IntegrationTestAgent\|claude-haiku-4-5\|업그레이드 체크리스트" \
  /c/workspace/mclayer/mctrader-data/.claude/_overlay/CLAUDE.md
```

Expected: 4개 키워드 각 1줄 이상 출력.

---

### Task 4: mctrader-engine CLAUDE.md 갱신

**Files:**
- Modify: `/c/workspace/mclayer/mctrader-engine/.claude/_overlay/CLAUDE.md` (append)

- [ ] **Step 1: 현재 파일 끝 확인**

```bash
tail -5 /c/workspace/mclayer/mctrader-engine/.claude/_overlay/CLAUDE.md
```

- [ ] **Step 2: 공통 블록 append**

파일 끝에 "공통 추가 블록" 전체를 추가한다.

- [ ] **Step 3: 검증**

```bash
grep -n "REVIVED\|IntegrationTestAgent\|claude-haiku-4-5\|업그레이드 체크리스트" \
  /c/workspace/mclayer/mctrader-engine/.claude/_overlay/CLAUDE.md
```

Expected: 4개 키워드 각 1줄 이상 출력.

---

### Task 5: mctrader-web CLAUDE.md 갱신

**Files:**
- Modify: `/c/workspace/mclayer/mctrader-web/.claude/_overlay/CLAUDE.md` (append)

- [ ] **Step 1: 현재 파일 끝 확인**

```bash
tail -5 /c/workspace/mclayer/mctrader-web/.claude/_overlay/CLAUDE.md
```

- [ ] **Step 2: 공통 블록 append**

파일 끝에 "공통 추가 블록" 전체를 추가한다.

- [ ] **Step 3: 검증**

```bash
grep -n "REVIVED\|IntegrationTestAgent\|claude-haiku-4-5\|업그레이드 체크리스트" \
  /c/workspace/mclayer/mctrader-web/.claude/_overlay/CLAUDE.md
```

Expected: 4개 키워드 각 1줄 이상 출력.

---

### Task 6: 전체 검증 + MCT-129 Story file 작성 (hub)

**Files:**
- Verify: 5개 repo CLAUDE.md
- Create: `docs/stories/MCT-129.md` (in mctrader-hub)

- [ ] **Step 1: 5-repo 일괄 grep 검증**

```bash
for repo in mctrader-market mctrader-market-bithumb mctrader-data mctrader-engine mctrader-web; do
  count=$(grep -c "REVIVED" /c/workspace/mclayer/$repo/.claude/_overlay/CLAUDE.md 2>/dev/null || echo 0)
  echo "[$repo] REVIVED count: $count"
done
```

Expected: 모든 repo에서 `REVIVED count: 1` 출력.

- [ ] **Step 2: MCT-129 Story file 작성 (mctrader-hub)**

`docs/stories/MCT-129.md` 를 다음 내용으로 작성:

```markdown
---
story_key: MCT-129
story_scope: hub
status: done
created_at: 2026-05-11
completed_at: 2026-05-11
delegates:
  - mctrader-market (CLAUDE.md 갱신)
  - mctrader-market-bithumb (CLAUDE.md 갱신)
  - mctrader-data (CLAUDE.md 갱신)
  - mctrader-engine (CLAUDE.md 갱신)
  - mctrader-web (CLAUDE.md 갱신)
---

# MCT-129: 5 impl repo CLAUDE.md codeforge 4종 업그레이드 반영

## §1 배경

MCT-127 (codeforge plugin 4종 업그레이드) 은 hub-only였고 "다른 mctrader 6-repo CLAUDE.md 갱신"을 out-of-scope로 defer.
MCT-128 (hub 감사+정리) 완료 후 5 impl repo에 동일 업그레이드 내용 반영.
MCT-128 체크리스트 SSOT 선행 완료 → 6-repo 동기화 step 6 이행.

## §2 목표 및 범위

5 impl repo (market/market-bithumb/data/engine/web) `.claude/_overlay/CLAUDE.md` 에 추가:
- plugin 버전 메모 (codeforge 4종 최신)
- Story workflow 통합테스트 phase
- Agent model tier 섹션 (Haiku 4.5, ADR-042 Amendment 2)
- Plugin 업그레이드 체크리스트 포인터 (hub SSOT)

## §3 Acceptance Criteria

- [x] mctrader-market CLAUDE.md: REVIVED / 통합테스트 / claude-haiku-4-5 / 체크리스트 포인터 포함
- [x] mctrader-market-bithumb CLAUDE.md: 동일 4개 키워드 포함
- [x] mctrader-data CLAUDE.md: 동일 4개 키워드 포함
- [x] mctrader-engine CLAUDE.md: 동일 4개 키워드 포함
- [x] mctrader-web CLAUDE.md: 동일 4개 키워드 포함

## §4 설계 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 변경 방식 | append (공통 블록) | 5 repo 구조 동일, YAGNI |
| 체크리스트 위치 | hub SSOT 포인터 | 중복 방지, MCT-128 체크리스트 단일 관리 |
| Story 분리 | MCT-128 + MCT-129 | hub 정리 선행 → 포인터 대상 확보 |

## §5 구현 노트

spec: docs/superpowers/specs/2026-05-11-deprecated-agent-audit-spec.md
plan: docs/superpowers/plans/2026-05-11-mct129-6repo-claude-upgrade.md
선행 Story: MCT-128 (hub 체크리스트 SSOT)

## §6 테스트 전략

doc-only — grep 검증으로 대체.

## §7 Change Plan

N/A (doc-only)

## §8 Test Contract

N/A

## §9 Review

doc-only — ADR-027 doc-only fast-pass.

## §10 FIX Ledger

없음

## §11 PMO 회고

[PMOAgent 작성 예정]
```

- [ ] **Step 3: Story file 확인**

```bash
test -f docs/stories/MCT-129.md && echo "OK" || echo "MISSING"
```

---

### Task 7: 5-repo 커밋 + hub 커밋

- [ ] **Step 1: 5개 impl repo 각각 커밋**

각 repo에서 개별 커밋:

```bash
# mctrader-market
cd /c/workspace/mclayer/mctrader-market
git add .claude/_overlay/CLAUDE.md
git commit -m "docs(mct-129): codeforge 4종 업그레이드 CLAUDE.md 반영 — test REVIVED / 통합테스트 phase / Haiku tier

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# mctrader-market-bithumb
cd /c/workspace/mclayer/mctrader-market-bithumb
git add .claude/_overlay/CLAUDE.md
git commit -m "docs(mct-129): codeforge 4종 업그레이드 CLAUDE.md 반영 — test REVIVED / 통합테스트 phase / Haiku tier

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# mctrader-data
cd /c/workspace/mclayer/mctrader-data
git add .claude/_overlay/CLAUDE.md
git commit -m "docs(mct-129): codeforge 4종 업그레이드 CLAUDE.md 반영 — test REVIVED / 통합테스트 phase / Haiku tier

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# mctrader-engine
cd /c/workspace/mclayer/mctrader-engine
git add .claude/_overlay/CLAUDE.md
git commit -m "docs(mct-129): codeforge 4종 업그레이드 CLAUDE.md 반영 — test REVIVED / 통합테스트 phase / Haiku tier

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# mctrader-web
cd /c/workspace/mclayer/mctrader-web
git add .claude/_overlay/CLAUDE.md
git commit -m "docs(mct-129): codeforge 4종 업그레이드 CLAUDE.md 반영 — test REVIVED / 통합테스트 phase / Haiku tier

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 2: hub MCT-129 Story file 커밋**

```bash
cd /c/workspace/mclayer/mctrader-hub
git add docs/stories/MCT-129.md
git commit -m "docs(mct-129): 5 impl repo CLAUDE.md 업그레이드 반영 완료 Story

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 3: 5 impl repo push**

```bash
for repo in mctrader-market mctrader-market-bithumb mctrader-data mctrader-engine mctrader-web; do
  cd /c/workspace/mclayer/$repo
  git push origin main
  echo "[$repo] pushed"
done
```

- [ ] **Step 4: hub push**

```bash
cd /c/workspace/mclayer/mctrader-hub
git push origin main
```
