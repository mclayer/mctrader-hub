# MCT-128 / MCT-129: deprecated agent 감사+정리 + 6-repo CLAUDE.md 업그레이드 — spec

**Date**: 2026-05-11  
**Stories**: MCT-128 (hub-only) → MCT-129 (multi-repo, 순차 후행)  
**Scope**: TestAgent/StatefulTestAgent 잔존 참조 정리 + 6-repo CLAUDE.md codeforge 4종 업그레이드 반영

---

## 배경

MCT-127 (codeforge plugin 4종 업그레이드) 완료 후 RETRO-MCT-127 §5 (HIGH) 권고:

> "6-repo deprecated agent spawn 잔존 감사 — codeforge-test 1.0.0에서 TestAgent/StatefulTestAgent spawn 불가하므로 6 sister repo CI / agent override에서 silent fail trigger 식별 의무"

MCT-127은 hub-only였고 "다른 mctrader 6-repo CLAUDE.md 갱신"을 out-of-scope로 defer했음. MCT-128/129가 이 두 가지를 모두 해소.

### grep 스캔 결과 (2026-05-11 기준)

| Repo | 참조 파일 수 | 성격 |
|------|------------|------|
| mctrader-hub | 11 | 주석 2개(run-tests.sh/run-perf.sh) + historical docs + CLAUDE.md(MCT-127 OK) |
| mctrader-web | 0 | 없음 |
| mctrader-data | 0 | 없음 |
| mctrader-engine | 0 | 없음 |
| mctrader-market | 0 | 없음 |
| mctrader-signal-collector | 0 | 없음 |

**핵심 발견**: 활성 spawn 호출 0건. 모든 참조는 주석 또는 historical 문서.

---

## 설계 결정 (Codex review → Sonnet 합성)

| 결정 | 선택 | 근거 |
|------|------|------|
| D1: Story 분리 | **B — MCT-128 + MCT-129** | hub 정리 ↔ 6-repo 갱신 책임 분리, fix-clean 가능 |
| D2: 정책 문서화 형태 | **B (수정) — hub CLAUDE.md 전체 + 5 impl repo 1줄 포인터** | B(각 repo embed) 경량화; hub SSOT + consumer 참조 패턴 |
| D3: upstream 확인 범위 | **A — CHANGELOG 재검토만** | MCT-127에서 4종 CHANGELOG 검토 완료; upstream feedback은 별도 lane |
| D4: 6-repo CI 검증 의미 | **C — CLAUDE.md grep 검증만** | doc-only fast-pass (ADR-027); CI run 불필요 |
| D5: 6-repo CLAUDE.md 처리 | **B — MCT-129 분리** | MCT-128 체크리스트 SSOT 선행 후 MCT-129 포인터 참조 |

---

## MCT-128 변경 계획

### 대상 파일

1. **`.claude/_overlay/run-tests.sh`** — line 4 주석 갱신
   - Before: `# TestAgent가 호출. 프로젝트 러너로 unit/integration/infra 테스트 실행.`
   - After: `# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). unit/integration/infra 테스트 실행.`

2. **`.claude/_overlay/run-perf.sh`** — line 4 주석 갱신
   - Before: `# TestAgent가 호출. baseline 대비 회귀 검증.`
   - After: `# IntegrationTestAgent가 호출 (codeforge-test 1.0.0, ADR-055). baseline 대비 회귀 검증.`

3. **`.claude/_overlay/CLAUDE.md`** — "Plugin 업그레이드 체크리스트" 섹션 신설
   - 위치: Plugin 목록 섹션 바로 아래
   - 내용: CHANGELOG 확인 → deprecated agent grep → consumer doc 동기화 3-step 체크리스트

4. **`docs/stories/MCT-128.md`** — Story file 작성 (§1-11)

### historical docs 처리

보존 (읽기 전용). 대상:
- `docs/stories/MCT-97.md` — 과거 TestAgent 호출 기록 (회고 무결성)
- `docs/superpowers/plans/*.md`, `docs/superpowers/specs/*.md` — historical design docs

---

## MCT-129 변경 계획

### 대상 repo 5개

mctrader-web / mctrader-data / mctrader-engine / mctrader-market / mctrader-signal-collector

### 각 repo CLAUDE.md 공통 변경 (5개 항목)

1. **codeforge-test annotation**: `DEPRECATED` → `REVIVED (ADR-055/CFP-367) — IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가); test-verdict-v2`
2. **codeforge-design annotation**: `0.5.0 + CFP-319` 갱신
3. **codeforge-review annotation**: `1.2.0 + CFP-318` 갱신
4. **codeforge-develop annotation**: `0.4.0 + docker-compose.test.yml` 갱신
5. **Story workflow**: 통합테스트 phase 추가 (`→ 통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2) →`)
6. **Agent model tier 섹션**: InfraEngineerAgent/QADeveloperAgent/DataEngineerAgent = `claude-haiku-4-5` (ADR-042 Amendment 2)
7. **Plugin 업그레이드 체크리스트**: hub CLAUDE.md SSOT 포인터 1줄 추가

### 대상 파일

- `../mctrader-web/.claude/_overlay/CLAUDE.md` (또는 repo 루트 CLAUDE.md 구조에 따라)
- `../mctrader-data/.claude/_overlay/CLAUDE.md`
- `../mctrader-engine/.claude/_overlay/CLAUDE.md`
- `../mctrader-market/.claude/_overlay/CLAUDE.md`
- `../mctrader-signal-collector/.claude/_overlay/CLAUDE.md`
- `docs/stories/MCT-129.md`

> **주의**: 각 repo CLAUDE.md 실제 경로는 구현 전 Read로 확인 필요 (`.claude/_overlay/CLAUDE.md` vs `CLAUDE.md` 루트)

---

## 실행 순서

```
MCT-128 (hub-only) → 완료 확인 → MCT-129 (multi-repo, 5 repo 병렬 batch)
```

MCT-128의 hub CLAUDE.md 체크리스트 섹션이 MCT-129의 포인터 대상이므로 순차 실행 필수.

---

## scope_manifest

### MCT-128

```yaml
scope_manifest:
  story_key: MCT-128
  story_type: hub-only
  parent_epic: null

  planned_adrs:
    count: 0
    rationale: |
      doc-only. 근거 ADR(ADR-055, CFP-367) upstream SSOT 이미 존재.

  planned_files:
    - path: .claude/_overlay/run-tests.sh
      change_type: modify
      note: line 4 주석 TestAgent → IntegrationTestAgent
    - path: .claude/_overlay/run-perf.sh
      change_type: modify
      note: line 4 주석 TestAgent → IntegrationTestAgent
    - path: .claude/_overlay/CLAUDE.md
      change_type: modify
      note: Plugin 업그레이드 체크리스트 섹션 신설 (MCT-129 SSOT)
    - path: docs/stories/MCT-128.md
      change_type: create
      note: Story file §1-11

  planned_claude_md_sections:
    - "Plugin 업그레이드 체크리스트"

  out_of_scope:
    - "historical story/spec/plan docs 갱신 (회고 무결성 보존)"
    - "6-repo CLAUDE.md 갱신 (MCT-129)"
    - "run-tests.sh / run-perf.sh 실제 로직 변경 (주석만)"

  risk_signals:
    - "체크리스트 섹션 위치 — Plugin 목록 바로 아래 배치 (구조 충돌 확인 필요)"
    - "historical doc 보존 원칙 vs 검색 혼선 trade-off (MCT-127 retro 합의로 보존 우선)"
```

### MCT-129

```yaml
scope_manifest:
  story_key: MCT-129
  story_type: multi-repo
  parent_epic: null

  planned_adrs:
    count: 0
    rationale: |
      doc-only. 근거 ADR 모두 upstream SSOT 존재.

  planned_files:
    - path: ../mctrader-web/CLAUDE.md (실제 경로 확인 필요)
      change_type: modify
      note: 7개 항목 공통 갱신
    - path: ../mctrader-data/CLAUDE.md (실제 경로 확인 필요)
      change_type: modify
      note: 동일
    - path: ../mctrader-engine/CLAUDE.md (실제 경로 확인 필요)
      change_type: modify
      note: 동일
    - path: ../mctrader-market/CLAUDE.md (실제 경로 확인 필요)
      change_type: modify
      note: 동일
    - path: ../mctrader-signal-collector/CLAUDE.md (실제 경로 확인 필요)
      change_type: modify
      note: 동일
    - path: docs/stories/MCT-129.md
      change_type: create
      note: Story file §1-11

  planned_claude_md_sections:
    - "codeforge-test REVIVED annotation"
    - "codeforge-design/review/develop 버전 annotation"
    - "Story workflow 통합테스트 phase"
    - "Agent model tier (Haiku 4.5)"
    - "Plugin 업그레이드 체크리스트 포인터"

  out_of_scope:
    - "hub CLAUDE.md (MCT-128)"
    - "각 repo test/CI 파이프라인 수정"
    - "historical docs 갱신"

  risk_signals:
    - "MCT-128 선행 의존 (체크리스트 SSOT 선행 필수)"
    - "각 repo CLAUDE.md 구조 차이 — 구현 전 Read 선행 필수"
    - "'도입 예정' vs '도입 완료' 표기 — IntegrationTestAgent phase 구분"
    - "5-repo PR 5개 vs 단일 cross-repo commit 전략 결정 필요"
```
