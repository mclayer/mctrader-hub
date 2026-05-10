# MCT-128: Deprecated Agent 감사 + Hub 정리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mctrader-hub 내 TestAgent/StatefulTestAgent 잔존 주석 2개를 IntegrationTestAgent로 갱신하고, hub CLAUDE.md에 codeforge plugin 업그레이드 체크리스트를 확장 (MCT-129의 6-repo SSOT 역할)

**Architecture:** doc-only 변경 3건 (run-tests.sh, run-perf.sh, CLAUDE.md) + Story file 작성. historical docs(MCT-97 등)는 보존. MCT-129가 이 플랜 완료 후 hub CLAUDE.md 체크리스트를 포인터로 참조.

**Tech Stack:** bash(grep 검증), git

---

## 파일 구조

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `.claude/_overlay/run-tests.sh` | modify | line 4 주석 TestAgent → IntegrationTestAgent |
| `.claude/_overlay/run-perf.sh` | modify | line 4 주석 TestAgent → IntegrationTestAgent |
| `.claude/_overlay/CLAUDE.md` | modify | §codeforge 업그레이드 프로세스 확장 (step 5, 6 추가) |
| `docs/stories/MCT-128.md` | create | Story file §1-11 |

---

### Task 1: run-tests.sh 주석 갱신

**Files:**
- Modify: `.claude/_overlay/run-tests.sh:4`

- [ ] **Step 1: 현재 line 4 내용 확인**

```bash
grep -n "TestAgent" .claude/_overlay/run-tests.sh
```

Expected output:
```
4:# TestAgent가 호출. 프로젝트 러너로 unit/integration/infra 테스트 실행.
```

- [ ] **Step 2: line 4 주석 갱신**

파일 `.claude/_overlay/run-tests.sh` line 4를 다음으로 교체:

```
# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). unit/integration/infra 테스트 실행.
```

즉, 파일의 1~3줄과 5줄 이후는 그대로 두고, line 4만 교체한다.

최종 파일 상단 (1~6줄):
```bash
#!/usr/bin/env bash
# .claude/_overlay/run-tests.sh — consumer가 작성하는 기능 테스트 wrapper
#
# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). unit/integration/infra 테스트 실행.
# 성능 마커는 deselect (성능은 run-perf.sh에서).
#
```

- [ ] **Step 3: 검증**

```bash
grep -n "TestAgent\|IntegrationTestAgent" .claude/_overlay/run-tests.sh
```

Expected:
```
4:# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). unit/integration/infra 테스트 실행.
```

"TestAgent가 호출" 문자열이 사라지고 "IntegrationTestAgent가 호출"만 남아야 한다.

---

### Task 2: run-perf.sh 주석 갱신

**Files:**
- Modify: `.claude/_overlay/run-perf.sh:4`

- [ ] **Step 1: 현재 line 4 내용 확인**

```bash
grep -n "TestAgent" .claude/_overlay/run-perf.sh
```

Expected output:
```
4:# TestAgent가 호출. baseline 대비 회귀 검증.
```

- [ ] **Step 2: line 4 주석 갱신**

파일 `.claude/_overlay/run-perf.sh` line 4를 다음으로 교체:

```
# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). baseline 대비 회귀 검증.
```

최종 파일 상단 (1~6줄):
```bash
#!/usr/bin/env bash
# .claude/_overlay/run-perf.sh — consumer가 작성하는 성능 테스트 wrapper
#
# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). baseline 대비 회귀 검증.
# Change Plan §8.3 "N/A" 명시 시 즉시 exit 0.
#
```

- [ ] **Step 3: 검증**

```bash
grep -n "TestAgent\|IntegrationTestAgent" .claude/_overlay/run-perf.sh
```

Expected:
```
4:# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). baseline 대비 회귀 검증.
```

---

### Task 3: CLAUDE.md — 업그레이드 체크리스트 step 5·6 추가

**Files:**
- Modify: `.claude/_overlay/CLAUDE.md` (§codeforge 업그레이드 프로세스 섹션)

- [ ] **Step 1: 현재 업그레이드 프로세스 섹션 확인**

```bash
grep -n "codeforge 업그레이드 프로세스\|Deprecation\|Breaking" .claude/_overlay/CLAUDE.md
```

Expected: `### codeforge 업그레이드 프로세스` 섹션이 step 1~4로 구성되어 있음을 확인.

- [ ] **Step 2: step 4 뒤에 step 5·6 추가**

현재 섹션 (step 4까지):
```markdown
### codeforge 업그레이드 프로세스

codeforge plugin upgrade 시 **반드시** 각 plugin CHANGELOG 를 읽고 consumer-facing 변경 사항을 이 파일에 반영한다. 확인 순서:

1. `plugin-codeforge/CHANGELOG.md` — core (Orchestrator 지침 / ADR / contract 변경)
2. lane plugin CHANGELOGs — pmo / requirements / design / develop / test / review
3. **Breaking change** → Story workflow / plugin list / phase 순서 즉시 갱신
4. **Deprecation** → plugin list 주석 업데이트 + Story phase 에서 제거
```

step 4 줄 바로 뒤에 다음 두 줄을 추가:

```markdown
5. **Deprecated agent 잔존 참조 감사** → `grep -r "DeprecatedAgentName" . --include="*.md" --include="*.sh" -l | grep -v "CHANGELOG\|retro"` 로 active spawn 참조 확인 후 주석/설정 갱신
6. **6-repo 동기화** → 5 impl repo `.claude/_overlay/CLAUDE.md` plugin 버전 메모 동기화 (mctrader-hub §plugin 목록 기준 — MCT-129 패턴)
```

최종 섹션 전체:
```markdown
### codeforge 업그레이드 프로세스

codeforge plugin upgrade 시 **반드시** 각 plugin CHANGELOG 를 읽고 consumer-facing 변경 사항을 이 파일에 반영한다. 확인 순서:

1. `plugin-codeforge/CHANGELOG.md` — core (Orchestrator 지침 / ADR / contract 변경)
2. lane plugin CHANGELOGs — pmo / requirements / design / develop / test / review
3. **Breaking change** → Story workflow / plugin list / phase 순서 즉시 갱신
4. **Deprecation** → plugin list 주석 업데이트 + Story phase 에서 제거
5. **Deprecated agent 잔존 참조 감사** → `grep -r "DeprecatedAgentName" . --include="*.md" --include="*.sh" -l | grep -v "CHANGELOG\|retro"` 로 active spawn 참조 확인 후 주석/설정 갱신
6. **6-repo 동기화** → 5 impl repo `.claude/_overlay/CLAUDE.md` plugin 버전 메모 동기화 (mctrader-hub §plugin 목록 기준 — MCT-129 패턴)
```

- [ ] **Step 3: 검증**

```bash
grep -n "step 5\|step 6\|Deprecated agent 잔존\|6-repo 동기화" .claude/_overlay/CLAUDE.md
```

Expected: step 5·6 두 줄이 출력됨.

```bash
grep -c "." .claude/_overlay/CLAUDE.md
```

이전보다 2줄 증가했는지 확인 (기존 줄 수 + 2).

---

### Task 4: MCT-128 Story file 작성

**Files:**
- Create: `docs/stories/MCT-128.md`

- [ ] **Step 1: Story file 작성**

`docs/stories/MCT-128.md` 를 다음 내용으로 작성:

```markdown
---
story_key: MCT-128
story_scope: hub
status: done
created_at: 2026-05-11
completed_at: 2026-05-11
---

# MCT-128: deprecated agent 잔존 참조 감사 + hub 정리

## §1 배경

MCT-127 (codeforge plugin 4종 업그레이드) RETRO §5 (HIGH) 권고:
codeforge-test 1.0.0에서 TestAgent/StatefulTestAgent spawn 불가 상태.
6-repo grep 스캔 결과 활성 spawn 호출 0건. mctrader-hub에만 주석 2개 잔존.

## §2 목표 및 범위

hub-only doc story.
- run-tests.sh / run-perf.sh 주석 갱신 (TestAgent → IntegrationTestAgent)
- CLAUDE.md 업그레이드 체크리스트 step 5·6 추가 (MCT-129 SSOT)
- historical docs 보존 (회고 무결성)

## §3 Acceptance Criteria

- [x] run-tests.sh line 4: "IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055)" 포함
- [x] run-perf.sh line 4: "IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055)" 포함
- [x] CLAUDE.md §codeforge 업그레이드 프로세스: step 5·6 추가 확인
- [x] historical docs (MCT-97, 과거 spec/plan): 변경 없음 (grep으로 확인)

## §4 설계 결정

spec: docs/superpowers/specs/2026-05-11-deprecated-agent-audit-spec.md

| 결정 | 선택 | 근거 |
|------|------|------|
| Story 분리 | MCT-128 hub + MCT-129 multi-repo | 책임 분리, fix-clean 가능 |
| 정책 문서화 | CLAUDE.md 기존 섹션 확장 | 기존 upgrade process 섹션에 step 추가 (YAGNI) |
| historical docs | 보존 | 회고 무결성 (RETRO-MCT-127 합의) |

## §5 구현 노트

spec: docs/superpowers/specs/2026-05-11-deprecated-agent-audit-spec.md
plan: docs/superpowers/plans/2026-05-11-mct128-deprecated-agent-audit.md

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

- [ ] **Step 2: 검증**

```bash
test -f docs/stories/MCT-128.md && echo "OK" || echo "MISSING"
grep -c "Acceptance Criteria" docs/stories/MCT-128.md
```

Expected: `OK` + `1`

---

### Task 5: Commit

**Files:**
- `.claude/_overlay/run-tests.sh`
- `.claude/_overlay/run-perf.sh`
- `.claude/_overlay/CLAUDE.md`
- `docs/stories/MCT-128.md`

- [ ] **Step 1: AC 최종 검증**

```bash
# run-tests.sh 확인
grep "IntegrationTestAgent" .claude/_overlay/run-tests.sh | grep -v "grep"

# run-perf.sh 확인
grep "IntegrationTestAgent" .claude/_overlay/run-perf.sh | grep -v "grep"

# CLAUDE.md step 5·6 확인
grep "Deprecated agent 잔존\|6-repo 동기화" .claude/_overlay/CLAUDE.md

# historical docs 변경 없음 확인 (변경된 파일 목록에 MCT-97 없어야 함)
git diff --name-only | grep "MCT-97"
```

Expected 마지막 명령: 출력 없음 (MCT-97 변경 없음)

- [ ] **Step 2: Commit**

```bash
git add .claude/_overlay/run-tests.sh .claude/_overlay/run-perf.sh .claude/_overlay/CLAUDE.md docs/stories/MCT-128.md
git commit -m "docs(mct-128): deprecated agent 잔존 주석 2개 갱신 + 업그레이드 체크리스트 step 5·6 추가

run-tests.sh / run-perf.sh: TestAgent → IntegrationTestAgent (codeforge-test 1.0.0 ADR-055).
CLAUDE.md: 업그레이드 프로세스 step 5 (deprecated agent grep) + step 6 (6-repo 동기화) 추가.
MCT-129 hub CLAUDE.md SSOT 준비 완료.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Expected: `[main <SHA>] docs(mct-128): ...`

- [ ] **Step 3: Push**

```bash
git push origin main
```

Expected: `main -> main` (bypass 메시지 포함 가능)
