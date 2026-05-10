# codeforge plugin 4종 업그레이드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** codeforge-review 1.1.0→1.2.0, codeforge-test 0.2.0→1.0.0, codeforge-develop 0.3.0→0.4.0, codeforge-design 0.4.1→0.5.0 설치 후 `.claude/_overlay/CLAUDE.md` consumer-facing 변경사항 반영.

**Architecture:** 플러그인 소스 레포(`c:\workspace\mclayer\plugin-codeforge-*`)를 Claude Code 플러그인 캐시로 복사 후 `installed_plugins.json` 갱신, 그 후 CLAUDE.md 7개 섹션 수정, 마지막으로 MCT-127 Story 파일 작성.

**Tech Stack:** PowerShell robocopy, JSON 편집, Markdown

---

## File Map

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0\` | CREATE dir | codeforge-review 신규 캐시 |
| `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0\` | CREATE dir | codeforge-test 신규 캐시 |
| `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-develop\0.4.0\` | CREATE dir | codeforge-develop 신규 캐시 |
| `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0\` | CREATE dir | codeforge-design 신규 캐시 |
| `C:\Users\mccho\.claude\plugins\installed_plugins.json` | MODIFY | 4 plugin 버전·경로·SHA 갱신 |
| `.claude/_overlay/CLAUDE.md` | MODIFY | 7개 섹션 변경 |
| `docs/stories/MCT-127.md` | CREATE | Hub Story 파일 |

---

## Task 0: codeforge-design 0.5.0 캐시 설치

**Files:**
- Create: `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0\`

- [ ] **Step 1: 소스 레포 HEAD 확인**

```powershell
cd "c:\workspace\mclayer\plugin-codeforge-design"
git log --oneline -3
git rev-parse HEAD
```

Expected: 첫 줄 = `7e36467 Merge branch 'main' ...` (CFP-319 merge)  
HEAD SHA = `7e364671f4dd5de55b1b469558f424ce03b90ef9`

- [ ] **Step 2: 캐시 디렉터리 생성 후 파일 복사**

```powershell
New-Item -ItemType Directory -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0" -Force
robocopy "c:\workspace\mclayer\plugin-codeforge-design" `
  "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0" `
  /E /XD .git .claude-plugin /XF .gitignore
```

- [ ] **Step 3: 0.5.0 핵심 변경 파일 존재 확인 (CFP-319)**

```powershell
# ArchitectAgent WS stream 실증 의무
Select-String -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0\agents\ArchitectAgent.md" -Pattern "push_interval"
# change-plan 템플릿 §8.5.1 체크리스트
Select-String -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-design\0.5.0\templates\change-plan.md" -Pattern "push_interval"
```

Expected: 각각 1줄 이상 매칭

---

## Task 1: codeforge-review 1.2.0 캐시 설치

**Files:**
- Create: `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0\`

- [ ] **Step 1: 소스 레포 HEAD 확인**

```powershell
cd "c:\workspace\mclayer\plugin-codeforge-review"
git log --oneline -3
git rev-parse HEAD
```

Expected output: 첫 줄 = `6c32d1c Merge pull request #23 from mclayer/cfp-318-reviewpl-label-preflight`  
HEAD SHA = `6c32d1cbc300ab7f380b1a8adaed90340b8dc8be`

- [ ] **Step 2: 캐시 디렉터리 생성 후 파일 복사**

```powershell
New-Item -ItemType Directory -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0" -Force
robocopy "c:\workspace\mclayer\plugin-codeforge-review" `
  "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0" `
  /E /XD .git .claude-plugin /XF .gitignore
```

- [ ] **Step 3: 복사 결과 검증**

```powershell
ls "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0"
```

Expected: `CHANGELOG.md, CLAUDE.md, README.md, agents, docs, overlay, scripts, templates` (`.git` 없음)

- [ ] **Step 4: 1.2.0 핵심 파일 존재 확인 (CFP-318 추가 파일)**

```powershell
ls "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-review\1.2.0\agents"
```

Expected: `ClaudeReviewAgent.md, CodeReviewPLAgent.md, CodexReviewAgent.md, DesignReviewPLAgent.md, SecurityTestPLAgent.md`

---

## Task 2: codeforge-test 1.0.0 캐시 설치

**Files:**
- Create: `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0\`

- [ ] **Step 1: 소스 레포 HEAD 확인**

```powershell
cd "c:\workspace\mclayer\plugin-codeforge-test"
git log --oneline -3
git rev-parse HEAD
```

Expected: 첫 줄 = `621425d fix(CFP-367): plugin.json 1.0.0 bump + CHANGELOG 항목 추가`  
HEAD SHA = `621425de35405b5e160649eac407378b17eb8200`

- [ ] **Step 2: 캐시 디렉터리 생성 후 파일 복사**

```powershell
New-Item -ItemType Directory -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0" -Force
robocopy "c:\workspace\mclayer\plugin-codeforge-test" `
  "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0" `
  /E /XD .git .claude-plugin /XF .gitignore
```

- [ ] **Step 3: IntegrationTestAgent 존재 확인 (1.0.0 핵심 신규 파일)**

```powershell
ls "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0\agents"
```

Expected: `IntegrationTestAgent.md` 포함 (TestAgent.md, StatefulTestAgent.md 도 보존)

- [ ] **Step 4: test-verdict-v2 contract 존재 확인**

```powershell
ls "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-test\1.0.0\docs\inter-plugin-contracts"
```

Expected: `test-verdict-v2.md` 포함

---

## Task 3: codeforge-develop 0.4.0 캐시 설치

**Files:**
- Create: `C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-develop\0.4.0\`

- [ ] **Step 1: 소스 레포 HEAD 확인**

```powershell
cd "c:\workspace\mclayer\plugin-codeforge-develop"
git log --oneline -3
git rev-parse HEAD
```

Expected: 첫 줄 = `0.4.0 bump` 관련 커밋  
HEAD SHA = `18cb898a0dcc4908f419e85366bf618e5b8b16e6`

- [ ] **Step 2: 캐시 디렉터리 생성 후 파일 복사**

```powershell
New-Item -ItemType Directory -Path "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-develop\0.4.0" -Force
robocopy "c:\workspace\mclayer\plugin-codeforge-develop" `
  "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-develop\0.4.0" `
  /E /XD .git .claude-plugin /XF .gitignore
```

- [ ] **Step 3: docker-compose.test.yml preset 존재 확인 (0.4.0 핵심 신규 파일)**

```powershell
ls "C:\Users\mccho\.claude\plugins\cache\mclayer\codeforge-develop\0.4.0\presets"
```

Expected: `docker-compose.test.yml` 포함

---

## Task 4: installed_plugins.json 갱신

**Files:**
- Modify: `C:\Users\mccho\.claude\plugins\installed_plugins.json`

- [ ] **Step 1: 현재 installed_plugins.json 상태 백업 메모**

변경 전 값 (참고용):
- `codeforge-review`: `version: "1.1.0"`, `installPath: ...1.1.0`, `gitCommitSha: "00cd7728cef203b6bf0e1429387b851ca573b407"`
- `codeforge-test`: `version: "0.2.0"`, `installPath: ...0.2.0`, `gitCommitSha: "74e89ae94cc442a3745798afeffd3f3b3e040c96"`
- `codeforge-develop`: `version: "0.3.0"`, `installPath: ...0.3.0`, `gitCommitSha: "50a4454e72a53a8a114d819f7b12b6579549ab36"`

- [ ] **Step 2: codeforge-review 항목 갱신**

`C:\Users\mccho\.claude\plugins\installed_plugins.json` 에서 `codeforge-review` 블록 수정:

```json
"codeforge-review@mclayer": [
  {
    "scope": "user",
    "installPath": "C:\\Users\\mccho\\.claude\\plugins\\cache\\mclayer\\codeforge-review\\1.2.0",
    "version": "1.2.0",
    "installedAt": "2026-05-06T04:19:07.207Z",
    "lastUpdated": "2026-05-10T09:00:00.000Z",
    "gitCommitSha": "6c32d1cbc300ab7f380b1a8adaed90340b8dc8be"
  }
]
```

- [ ] **Step 3: codeforge-test 항목 갱신**

```json
"codeforge-test@mclayer": [
  {
    "scope": "user",
    "installPath": "C:\\Users\\mccho\\.claude\\plugins\\cache\\mclayer\\codeforge-test\\1.0.0",
    "version": "1.0.0",
    "installedAt": "2026-05-06T04:19:19.206Z",
    "lastUpdated": "2026-05-10T09:00:00.000Z",
    "gitCommitSha": "621425de35405b5e160649eac407378b17eb8200"
  }
]
```

- [ ] **Step 4: codeforge-develop 항목 갱신**

```json
"codeforge-develop@mclayer": [
  {
    "scope": "user",
    "installPath": "C:\\Users\\mccho\\.claude\\plugins\\cache\\mclayer\\codeforge-develop\\0.4.0",
    "version": "0.4.0",
    "installedAt": "2026-05-06T04:19:26.207Z",
    "lastUpdated": "2026-05-10T09:00:00.000Z",
    "gitCommitSha": "18cb898a0dcc4908f419e85366bf618e5b8b16e6"
  }
]
```

- [ ] **Step 5: codeforge-design 항목 갱신**

```json
"codeforge-design@mclayer": [
  {
    "scope": "user",
    "installPath": "C:\\Users\\mccho\\.claude\\plugins\\cache\\mclayer\\codeforge-design\\0.5.0",
    "version": "0.5.0",
    "installedAt": "2026-05-06T04:19:31.561Z",
    "lastUpdated": "2026-05-10T09:00:00.000Z",
    "gitCommitSha": "7e364671f4dd5de55b1b469558f424ce03b90ef9"
  }
]
```

- [ ] **Step 6: JSON 유효성 확인**

```powershell
python -c "import json; json.load(open('C:\\Users\\mccho\\.claude\\plugins\\installed_plugins.json')); print('JSON OK')"
```

Expected: `JSON OK`

---

## Task 5: CLAUDE.md — Plugin list 3개 annotation 갱신

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md` (lines 96-107)

현재 plugin list (lines 95-107):
```
codeforge@mclayer
codeforge-requirements@mclayer
codeforge-design@mclayer
codeforge-develop@mclayer
codeforge-test@mclayer          # DEPRECATED (CFP-317/ADR-048) — CI-native 전환, 유지만
codeforge-review@mclayer
codeforge-pmo@mclayer
github@claude-plugins-official
codex@openai-codex
superpowers@claude-plugins-official
claude-md-management@claude-plugins-official
```

- [ ] **Step 1: codeforge-design annotation 추가**

`codeforge-design@mclayer`
→
`codeforge-design@mclayer        # 0.5.0 — CFP-319: ArchitectAgent WS stream push_interval 실증 의무; TestContractArch wiretap fixture; change-plan §8.5.1`

- [ ] **Step 2: codeforge-develop annotation 추가**

`codeforge-develop@mclayer` → `codeforge-develop@mclayer       # 0.4.0 — presets/docker-compose.test.yml (IntegrationTestAgent §8.6); CFP-317 PR pre-flight guard`

- [ ] **Step 3: codeforge-test DEPRECATED 제거 + REVIVED 표기**

`codeforge-test@mclayer          # DEPRECATED (CFP-317/ADR-048) — CI-native 전환, 유지만`
→
`codeforge-test@mclayer          # REVIVED (ADR-055/CFP-367) — IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가); test-verdict-v2`

- [ ] **Step 4: codeforge-review annotation 추가**

`codeforge-review@mclayer`
→
`codeforge-review@mclayer        # 1.2.0 — CFP-318: 3 ReviewPL bootstrap-labels.sh preflight; review-verdict v4 (CFP-137, v3 Archived)`

- [ ] **Step 5: 변경 검증**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" -Pattern "REVIVED|bootstrap-labels|docker-compose.test|push_interval"
```

Expected: 4줄 매칭 (각 annotation 1개씩)

---

## Task 6: CLAUDE.md — Story workflow 통합테스트 phase 신설

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md` (line 139)

- [ ] **Step 1: 현재 Phase 라인 확인**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" -Pattern "^- Phase: "
```

Expected: `CI 테스트 (\`gh pr checks\` polling, ADR-048) → 보안-테스트 →` 포함

- [ ] **Step 2: Phase 라인에 통합테스트 phase 삽입**

기존:
```
- Phase: 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → CI 테스트 (`gh pr checks` polling, ADR-048) → 보안-테스트 → 완료 → **PMO 회고 (의무)**
```

변경 후:
```
- Phase: 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → CI 테스트 (`gh pr checks` polling, ADR-048) → 통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2) → 보안-테스트 → 완료 → **PMO 회고 (의무)**
```

- [ ] **Step 3: 변경 검증**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" -Pattern "통합테스트"
```

Expected: `→ 통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2) →` 매칭

---

## Task 7: CLAUDE.md — Agent model tier 섹션 신설

**Files:**
- Modify: `c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md` (overlay agents 섹션 뒤, line 170 이후)

- [ ] **Step 1: 삽입 위치 확인**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" -Pattern "overlay agents"
```

Expected: `### overlay agents (CFP-108)` 라인 번호 확인

- [ ] **Step 2: overlay agents 섹션 뒤에 신규 섹션 삽입**

`- \`.claude/_overlay/agents/DataEngineerAgent.md\` — ...` 줄 다음에 아래 삽입:

```markdown

### Agent model tier (ADR-042 Amendment 2 — 2026-05-10)

InfraEngineerAgent·QADeveloperAgent·DataEngineerAgent = `claude-haiku-4-5` (기계적 패턴 실행 카테고리).
나머지 모든 agent = Sonnet 이상 (ADR-042 §결정-1 3-tier 매트릭스).
롤백 트리거: 해당 agent 의 ESCALATE rate 급증 또는 품질 저하 시 ADR-042 governance re-audit (ADR-042 §결정-5/6).
```

- [ ] **Step 3: 변경 검증**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" -Pattern "claude-haiku-4-5"
```

Expected: `InfraEngineerAgent·QADeveloperAgent·DataEngineerAgent = \`claude-haiku-4-5\`` 매칭

---

## Task 8: MCT-127 Story 파일 작성

**Files:**
- Create: `c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-127.md`

- [ ] **Step 1: Story 파일 생성**

`c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-127.md` 신규 작성:

```markdown
---
story_key: MCT-127
story_scope: hub
status: done
created_at: 2026-05-10
completed_at: 2026-05-10
---

# MCT-127: codeforge plugin 3종 업그레이드 (review 1.2.0 / test 1.0.0 / develop 0.4.0)

## §1 배경

codeforge plugin 3개가 2026-05-10 신버전 릴리스됨.
feedback_codeforge_upgrade_process.md 의무(CHANGELOG 확인 → CLAUDE.md 즉시 반영) 이행.

## §2 목표 및 범위

hub-only doc story — plugin 설치 + CLAUDE.md 6개 섹션 반영.

### 변경 요약

| Plugin | 이전 | 신버전 | 주요 변경 |
|--------|------|--------|-----------|
| codeforge-review | 1.1.0 | 1.2.0 | CFP-318: 3 ReviewPL bootstrap-labels.sh preflight; review-verdict v4 (CFP-137) |
| codeforge-test | 0.2.0 | 1.0.0 (MAJOR) | REVIVED (ADR-055): IntegrationTestAgent; test-verdict-v2; TestAgent/StatefulTestAgent deprecated |
| codeforge-develop | 0.3.0 | 0.4.0 | presets/docker-compose.test.yml 신설 (CFP-367 sibling) |

## §3 Acceptance Criteria

- [ ] 3 plugin 신버전이 캐시에 설치되고 installed_plugins.json 갱신됨
- [ ] CLAUDE.md plugin list: codeforge-test DEPRECATED 제거 + REVIVED 표기, review/develop annotation 갱신
- [ ] CLAUDE.md Story workflow: 통합테스트 phase (IntegrationTestAgent, ADR-055) 추가
- [ ] CLAUDE.md Agent model tier 섹션 신설 (Haiku 4.5, ADR-042 Amendment 2)

## §4 설계 결정 (Sonnet decider)

| 결정 | 선택 | 근거 |
|------|------|------|
| Story 수 | 1 Story hub-only | docker-compose.test.yml infra = MCT-41 defer |
| codeforge-test CLAUDE.md 처리 | MAJOR 전면 재작성 | IntegrationTestAgent/§8.6/test-verdict-v2 명시 |
| review-verdict v4 언급 | 포함 | 1.2.0에 CFP-137 mirror 포함, v3 Archived |

## §5 구현 노트

spec: `docs/superpowers/specs/2026-05-10-codeforge-plugin-upgrade-design.md`
plan: `docs/superpowers/plans/2026-05-10-codeforge-plugin-upgrade.md`

## §6 테스트 전략

doc-only story — unit test 없음. 각 Task 후 grep 검증으로 대체.

## §7 Change Plan

N/A (doc-only, no code change)

## §8 Test Contract

N/A

## §9 Review

doc-only story — review phase skip (ADR-027 doc-only fast-pass)

## §10 FIX Ledger

없음

## §11 PMO 회고

[PMOAgent 작성 예정]
```

- [ ] **Step 2: 파일 존재 확인**

```powershell
ls "c:\workspace\mclayer\mctrader-hub\docs\stories\MCT-127.md"
```

Expected: 파일 존재

---

## Task 9: 최종 검증 및 커밋

**Files:**
- 모든 변경 파일

- [ ] **Step 1: CLAUDE.md 최종 전체 변경 검증**

```powershell
Select-String -Path "c:\workspace\mclayer\mctrader-hub\.claude\_overlay\CLAUDE.md" `
  -Pattern "REVIVED|bootstrap-labels|docker-compose.test|통합테스트|claude-haiku-4-5"
```

Expected: 5줄 이상 매칭 (각 변경사항 대응)

- [ ] **Step 2: git status 확인**

```powershell
cd "c:\workspace\mclayer\mctrader-hub"
git status
```

Expected: `.claude/_overlay/CLAUDE.md` modified, `docs/stories/MCT-127.md` new file

- [ ] **Step 3: installed_plugins.json 버전 확인**

```powershell
python -c "
import json
data = json.load(open('C:\\Users\\mccho\\.claude\\plugins\\installed_plugins.json'))
for p in ['codeforge-review@mclayer', 'codeforge-test@mclayer', 'codeforge-develop@mclayer']:
    v = data['plugins'][p][0]['version']
    print(f'{p}: {v}')
"
```

Expected:
```
codeforge-review@mclayer: 1.2.0
codeforge-test@mclayer: 1.0.0
codeforge-develop@mclayer: 0.4.0
```

- [ ] **Step 4: 커밋**

```powershell
git add ".claude/_overlay/CLAUDE.md" "docs/stories/MCT-127.md"
git commit -m "docs(mct-127): codeforge plugin 3종 업그레이드 — review 1.2.0 / test 1.0.0 / develop 0.4.0 CLAUDE.md 반영"
```

Note: `installed_plugins.json` 은 `.gitignore` 또는 user-scope 파일이므로 커밋 제외.

---

## Self-Review Checklist

### Spec coverage

| Spec 요구사항 | 대응 Task |
|--------------|----------|
| codeforge-design 0.5.0 설치 | Task 0 |
| codeforge-review 1.2.0 설치 | Task 1 |
| codeforge-test 1.0.0 설치 | Task 2 |
| codeforge-develop 0.4.0 설치 | Task 3 |
| installed_plugins.json 갱신 | Task 4 |
| Plugin list 4개 annotation | Task 5 |
| Story workflow 통합테스트 phase | Task 6 |
| review-verdict v4 언급 | Task 5 (codeforge-review annotation 포함) |
| Agent model tier 섹션 | Task 7 |
| MCT-127 Story 파일 | Task 8 |
| 커밋 | Task 9 |

→ 모든 spec 요구사항 커버됨.

### 후속 고려 (out-of-scope)

- `TestAgent`/`StatefulTestAgent` spawn 잔존 여부 6-repo 감사 → 별도 Story 후보
- docker-compose.test.yml 실파일 생성 → MCT-41 Live Mode 진행 시 impl repo에서 작성
