# codeforge plugin 3종 업그레이드 — MCT-127 spec

**Date**: 2026-05-10  
**Story**: MCT-127 (hub-only, doc-only)  
**Scope**: codeforge-review 1.1.0→1.2.0, codeforge-test 0.2.0→1.0.0 (MAJOR), codeforge-develop 0.3.0→0.4.0

---

## 배경

codeforge plugin 3개가 오늘(2026-05-10) 신버전 릴리스됨. 설치 버전이 마켓플레이스 최신보다 뒤처짐.  
feedback_codeforge_upgrade_process.md 의무: 각 plugin CHANGELOG 확인 → mctrader CLAUDE.md 즉시 반영.

### 버전 격차

| Plugin | 설치됨 | 최신 | 상태 |
|--------|--------|------|------|
| codeforge | 5.9.0 | 5.9.0 | ✓ |
| codeforge-review | 1.1.0 | **1.2.0** | ⚠️ MINOR |
| codeforge-test | 0.2.0 | **1.0.0** | ⚠️ MAJOR |
| codeforge-develop | 0.3.0 | **0.4.0** | ⚠️ MINOR |

---

## 변경사항 요약 (CHANGELOG 기반)

### codeforge-review 1.1.0 → 1.2.0

- **CFP-318**: 3 ReviewPLAgent (Design/Code/SecurityTest) 착수 전 `bootstrap-labels.sh` preflight 자동 실행
- **CFP-367 sibling**: CodeReviewPL `code.md` 통합테스트 사전 조건 + category enum parity
- **CFP-137**: review-verdict v4 canonical mirror 신설 + v3 Archived
- **CFP-135**: review-verdict v3 DEPRECATED PASSTHROUGH annotation backfill

### codeforge-test 0.2.0 → 1.0.0 (MAJOR — REVIVED)

- ADR-048(CI-native)로 deprecated됐던 plugin이 **ADR-055/CFP-367**로 통합테스트 lane 전용 부활
- `agents/IntegrationTestAgent.md` 신설 (Sonnet tier, §8.6 Integration Test Contract)
- `docker-compose.test.yml` 동적 실행, test-verdict-v2 생성
- TestAgent/StatefulTestAgent: deprecated 유지 (spawn 불가, 파일 보존)
- test-verdict-v1 → Archived; test-verdict-v2 canonical

### codeforge-develop 0.3.0 → 0.4.0

- `presets/docker-compose.test.yml` 신설: 3-service(app/test-db/wiremock) ephemeral 구성
- InfraEngineerAgent §8.6 사용 전제 (CFP-367 / ADR-055 sibling)

---

## 설계 결정 (Codex review → Sonnet 합성)

| 결정 | 선택 | 근거 |
|------|------|------|
| D1: Story 수 | **A — 1 Story** | hub doc-only; docker-compose.test.yml infra는 MCT-41 Live Mode 진행 시 defer |
| D2: codeforge-test CLAUDE.md 처리 | **B — 전면 재작성** | MAJOR bump; IntegrationTestAgent/§8.6/test-verdict-v2/docker-compose.test.yml 명시 필요 |
| D3: review-verdict v4 언급 | **A — 포함** | 1.2.0에 CFP-137 mirror 포함, v3 Archived → CLAUDE.md 기준 v4로 갱신 |

---

## CLAUDE.md 변경 계획 (6개)

1. **Plugin list — codeforge-review**: 주석 갱신 `1.2.0 + CFP-318: 3 ReviewPL 착수 전 bootstrap-labels.sh preflight 자동 실행`
2. **Plugin list — codeforge-test**: `DEPRECATED` 제거 → `REVIVED (ADR-055/CFP-367) — IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가); test-verdict-v2 contract`
3. **Plugin list — codeforge-develop**: 주석 갱신 `0.4.0 + presets/docker-compose.test.yml 신설 (IntegrationTestAgent §8.6 사용)`
4. **Story workflow — 통합테스트 phase 신설**: 기존 `CI 테스트 (gh pr checks polling, ADR-048)` 뒤에 통합테스트 phase 추가 — IntegrationTestAgent spawn / §8.6 계약 / docker-compose.test.yml / test-verdict-v2
5. **review lane — review-verdict v4**: v4 contract 기준 추가 (CFP-137), v3 Archived
6. **Agent model tier 섹션 추가**: InfraEngineerAgent·QADeveloperAgent·DataEngineerAgent = Haiku 4.5 (ADR-042 Amendment 2)

---

## scope_manifest

```yaml
scope_manifest:
  story_key: MCT-127
  story_type: hub-only
  parent_epic: null

  planned_adrs:
    count: 0
    rationale: |
      doc-only consumer reflexive update — 신규 설계 결정 없음.
      참조 ADR (upstream codeforge 기존):
        - ADR-055 (codeforge-test REVIVED, CFP-367)
        - ADR-048 (CI 테스트 gh pr checks polling)
        - ADR-042 Amendment 2 (Agent model tier — Haiku 4.5 확장)
        - CFP-318 (bootstrap-labels.sh preflight)
        - CFP-137 (review-verdict v4)

  planned_files:
    - path: CLAUDE.md
      change_type: modify
      sections_touched: 5
      estimated_lines_changed: ~40
    - path: docs/stories/MCT-127.md
      change_type: create
      schema: templates/story.md §1-11
    - path: installed_plugins.json
      change_type: modify
      note: codeforge-review 1.2.0, codeforge-test 1.0.0, codeforge-develop 0.4.0 버전 갱신

  planned_claude_md_sections:
    - "Plugin 목록 — codeforge-review 주석"
    - "Plugin 목록 — codeforge-test DEPRECATED 제거 + REVIVED"
    - "Plugin 목록 — codeforge-develop 주석"
    - "Story workflow — 통합테스트 phase 신설"
    - "review lane — review-verdict v4"
    - "Agent model tier 섹션 (신설)"

  out_of_scope:
    - "다른 mctrader 6-repo CLAUDE.md 갱신 (별도 Story)"
    - "IntegrationTestAgent 실제 spawn 검증 (doc-only)"
    - "docker-compose.test.yml 실파일 작성 (plugin preset 활용)"
    - "Plugin 신기능 dry-run 검증 (다음 production Story에서 자연 검증)"

  risk_signals:
    - "plugin 설치 후 agent 목록 / preset 파일 sanity check 권장"
    - "deprecated TestAgent/StatefulTestAgent spawn 잔존 여부 6-repo 감사 후속 Story 후보"
```

---

## 구현 태스크 (순차)

| # | 태스크 | 설명 |
|---|--------|------|
| T1 | Plugin 설치 | codeforge-review 1.2.0 / codeforge-test 1.0.0 / codeforge-develop 0.4.0 설치 |
| T2 | CLAUDE.md plugin list 갱신 | 변경 #1 #2 #3 |
| T3 | CLAUDE.md Story workflow 갱신 | 변경 #4 (통합테스트 phase 신설) |
| T4 | CLAUDE.md review lane 갱신 | 변경 #5 (review-verdict v4) |
| T5 | CLAUDE.md Agent model tier 갱신 | 변경 #6 (Haiku tier 섹션 추가) |
| T6 | Story file 작성 | docs/stories/MCT-127.md §1-11 |
