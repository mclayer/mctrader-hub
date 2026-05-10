# RETRO-MCT-127 — codeforge plugin 4종 업그레이드 (design 0.5.0 / review 1.2.0 / test 1.0.0 / develop 0.4.0)

**범위**: MCT-127 (mctrader-hub `installed_plugins.json` + `.claude/_overlay/CLAUDE.md` 7개 섹션 갱신)
**기간**: 2026-05-10 (MCT-126 직후 동일 세션 연장 — 14번째 same-session Story)
**Trigger**: 2026-05-10 codeforge plugin family 4종 동시 release. `feedback_codeforge_upgrade_process.md` 의무 (CHANGELOG 확인 → CLAUDE.md 즉시 반영) 이행. doc-only / hub-only.
**Status**:
- mctrader-hub 단일 commit `1f083ca docs(mct-127)`
- AC 4/4 (100%) — fix-clean (FIX 0)
- doc-only fast-pass (ADR-027) 적용 — review/test/security lane skip

**Story file**: `docs/stories/MCT-127.md` (§11 PMO 회고 본 RETRO 와 동시 박제)
**Repos**: `mctrader-hub` 단일 (CLAUDE.md + installed_plugins.json) + 4 plugin 캐시 디렉터리 install (`C:\Users\mccho\.claude\plugins\cache\mclayer\<plugin>\<version>\`)

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| 영역 | 계획 (4 AC) | 실제 | 비고 |
|---|---|---|---|
| AC1 — 4 plugin 캐시 설치 + installed_plugins.json 갱신 | 의무 | done | design 0.5.0 / review 1.2.0 / test 1.0.0 / develop 0.4.0 |
| AC2 — CLAUDE.md plugin list 4 annotation 갱신 (test DEPRECATED → REVIVED 포함) | 의무 | done | 4 plugin annotation block 일괄 교체 |
| AC3 — CLAUDE.md Story workflow 통합테스트 phase 추가 | 의무 | done | `CI 테스트 → 통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2) → 보안-테스트` 한 줄 신설 |
| AC4 — CLAUDE.md Agent model tier 섹션 신설 (Haiku 4.5, ADR-042 Amendment 2) | 의무 | done | InfraEngineerAgent / QADeveloperAgent / DataEngineerAgent 3 agent 명시 |

→ **Story scope 4/4 AC 100% 완료**. 계획 외 추가 변경 없음. RETRO-MCT-126 의 12 commit / Cat A·B·C 폭발 vs 본 Story 의 single commit / single purpose — **doc-only Story 모범 패턴**.

### 1.2 commit 통계

| 단위 | 통계 | 상태 |
|---|---|---|
| `mctrader-hub` | 1 commit (`1f083ca`) | main 직접 push (ADR-019 D6) |
| `installed_plugins.json` | 4 line 변경 (4 plugin 버전 bump) | 동일 commit 포함 |
| `.claude/_overlay/CLAUDE.md` | 7 섹션 갱신 (plugin list 4 + Story workflow + Agent model tier 신설) | 동일 commit 포함 |

→ **단일 commit / 단일 repo / fix-clean**. RETRO-MCT-126 의 12 commit 다중 cycle 과 대비 가장 단순. doc-only fast-pass 적용으로 CI cycle 0회.

### 1.3 테스트 결과

doc-only Story — unit test 없음. **grep 검증으로 대체** (§6 Story file 명시).

| 검증 항목 | 결과 |
|---|---|
| `installed_plugins.json` 4 plugin 버전 grep | 통과 (4/4 bump 확인) |
| CLAUDE.md `codeforge-test@mclayer` annotation REVIVED 확인 | 통과 |
| CLAUDE.md Story workflow 통합테스트 phase 한 줄 grep | 통과 |
| CLAUDE.md Agent model tier 섹션 grep | 통과 |

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 작업 (4 AC) | 4 | 100% | 본 작업 |
| Cat A (pre-existing) | 0 | 0% | — |
| Cat B (self-discovered) | 0 | 0% | — |
| Cat C (다른 Story finish-up) | 0 | 0% | — |

→ **부수 fix 0%** — RETRO-MCT-126 의 Cat B 48% / Cat A 16% / Cat C 8% 와 정반대. doc-only Story 의 모범 — pre-existing debt finish-up 없음, self-discovered cascade 없음, 다른 Story finish-up 없음.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge |
|---|---|---|---|---|
| `mctrader-hub` | `main` (직접 push) | done | (없음, ADR-019 D6) | done |

→ **1-repo Story** — RETRO-MCT-126 와 동일 단순도. cross-repo 협업 cost 0.

---

## 2. Sonnet decider (§4 박제)

3 결정점 박제 (Story file §4):

| 결정 | 선택 | 근거 |
|---|---|---|
| Story 수 | 1 Story hub-only | docker-compose.test.yml 6-repo infra 적용 = MCT-41 defer 정당, 본 Story 는 doc-only governance 만 |
| codeforge-test CLAUDE.md 처리 | MAJOR 전면 재작성 | IntegrationTestAgent / §8.6 / test-verdict-v2 3 marker 명시 — 단순 버전 번호 갱신 거부 |
| review-verdict v4 언급 | 포함 | 1.2.0 에 CFP-137 mirror 포함, v3 Archived — annotation 에 v4 명시 |

→ decider 박제 정합. 추후 plugin 충돌 시 본 §4 가 결정 근거로 referenced 가능.

---

## 3. codeforge-test MAJOR bump 처리 lane

본 세션 첫 **MAJOR** bump (0.2.0 → 1.0.0). 처리 단계:

1. **이전 deprecation lane 확인** — `codeforge-test` 가 한때 DEPRECATED (TestAgent/StatefulTestAgent spawn 불가) 였음을 CLAUDE.md 이전 annotation 에서 확인
2. **REVIVED 결정 박제** — ADR-055 (CFP-367) 가 IntegrationTestAgent (Sonnet) 전용 plugin 으로 부활 결정
3. **plugin annotation 신규 marker 3 명시** — `IntegrationTestAgent` / `§8.6` / `test-verdict-v2` 모두 plugin list 한 줄 annotation 에 포함
4. **Story workflow phase 순서 변경 박제** — `통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2)` 가 CI 테스트 ↔ 보안-테스트 사이에 신설
5. **sibling plugin 동반 변경 박제** — codeforge-develop 0.4.0 의 `presets/docker-compose.test.yml` (CFP-367 sibling) 명시

→ **MAJOR bump templates**:
- decider §4 에 "전면 재작성" 명시
- plugin annotation 에 신규 contract 명 (test-verdict-v2 등) 명시
- Story workflow phase 순서 변경 박제 (한 줄 marker)
- sibling plugin 동반 변경 §2 변경 요약 표에 명시

---

## 4. 4종 동시 업그레이드 패턴

같은 날 4 plugin 동시 release → 1 Story 로 묶은 lane trade-off:

**장점** (본 Story 채택):
- CLAUDE.md 7개 섹션 한번에 정합 — plugin list 4 annotation 한번 + decider 1회
- `installed_plugins.json` 단일 commit
- 의무 플로우 (`feedback_codeforge_upgrade_process.md`) 가 4번 분리 실행 시 cognitive overhead 회피
- doc-only fast-pass 적용 가능

**위험** (감수):
- **bisect 어려움** — 추후 plugin 충돌 시 어느 plugin 변경이 trigger 인지 commit 단위로 격리 안 됨 (`1f083ca` 한 commit 에 4 plugin 합산)
- decider 1회로 4 결정 묶음 — review-verdict v4 / IntegrationTestAgent / ADR-055 / docker-compose preset 각각의 독립 결정점이 §4 3-row 표로 압축됨

→ **권고**:
- 4종 동시 + doc-only + 단일 release 날짜 (2026-05-10) → 1 Story 묶음 정당
- 단, **추후 MAJOR bump 2개 이상 동시 발생 시 commit 분리 검토** (4 plugin × 4 commit)
- bisect cost 가 cognitive cost 를 능가하는 시점 = MAJOR 2 이상 동시

---

## 5. 후속 Story 후보

| 후보 | 우선순위 | 근거 | 추정 Story key |
|---|---|---|---|
| **6-repo deprecated agent spawn 잔존 감사** | **HIGH** | TestAgent/StatefulTestAgent 가 codeforge-test 1.0.0 에서 spawn 불가. 6 sister repo 의 `.github/workflows/` / `scripts/` / `docs/stories/` / agent override 에서 두 agent 명 grep 후 IntegrationTestAgent 로 마이그레이션. 위반 시 Story phase 진입 silent fail. | MCT-128 후보 |
| docker-compose.test.yml MCT-41 통합 | MED | codeforge-develop 0.4.0 `presets/docker-compose.test.yml` 가 IntegrationTestAgent 의존. 본 Story defer, MCT-41 (infra Story) 시점 6-repo 적용 lane 필요. | MCT-41 amendment |
| review-verdict v3 → v4 마이그레이션 잔존 감사 | MED | codeforge-review 1.2.0 = v4 mirror, v3 Archived. 6 sister repo 의 review template / form / agent override 에서 v3 잔존 grep 후 v4 schema 정합. | TBD |
| bootstrap-labels.sh preflight 6-repo 적용 검증 | LOW | codeforge-review 1.2.0 의 3 ReviewPL bootstrap-labels.sh preflight 가 6 sister repo CI 에서 활성화 검증. label 누락 시 review lane 진입 차단. | TBD |
| WS stream push_interval 실증 lane 식별 | LOW | codeforge-design 0.5.0 의 ArchitectAgent WS stream push_interval 실증 의무가 mctrader-engine WS executor lane 에 적용 식별 (Live mode 진입 시 trigger). | MCT-? (Live mode) |

---

## 6. RETRO-MCT-126 대비 lane 비교

| 항목 | RETRO-MCT-126 | RETRO-MCT-127 |
|---|---|---|
| commit 수 | 12 (web 12, hub 1) | 1 (hub 1) |
| AC 충족률 | 3/3 (100%) | 4/4 (100%) |
| Cat A/B/C fix 비율 | 16% / 48% / 8% | 0% / 0% / 0% |
| CI cycle | 4 (ruff/pyright 누적 surface) | 0 (doc-only fast-pass) |
| Sonnet decider 결정점 | (RETRO 에 미박제) | 3 |
| 자동 dispatch 게이트 충족 | done | done |

→ **doc-only / single-purpose Story 의 모범 vs 표면 작업 + pre-existing surface 폭발 lane** 의 정반대 사례. MCT-127 같은 좁은 scope + decider 미리 박제 + fast-pass 적용 시 fix-clean 가능 — 추후 plugin upgrade Story 의 reference template.

---

## 7. 위반 / 개선 사항

**위반 없음**:
- AC 100% 충족
- fix-clean (FIX 0)
- §11 회고 자동 dispatch (`feedback_pmo_retro_mandatory.md`) 게이트 충족 — MCT-107~111 5 연속 누락 회복 lane 유지

**개선 제안 1건**:
- **CHANGELOG → CLAUDE.md 반영 grep 자동화 script 부재** — `feedback_codeforge_upgrade_process.md` 의무가 수동 4-step 절차로만 정의됨. `scripts/codeforge-upgrade-audit.ps1` (4 plugin CHANGELOG 읽고 CLAUDE.md 누락 marker 추출) 신규 lane 검토. 단, 자동화 ROI 낮으면 본 §11/RETRO 박제로 충분 — defer 가능.

---

## 8. Cross-Story 패턴 메모 (PMO 횡단 감사용)

본 RETRO 가 향후 cross-Story 패턴 분석 (PMOAgent §3 책임) 시 referenced 될 항목:

- **doc-only Story 모범 패턴 박제 (template)** — RETRO-MCT-126 (표면 작업 + pre-existing surface) 와 비교 reference
- **MAJOR bump 처리 templates** — §3 4-step 절차가 추후 codeforge-* MAJOR bump 시 직접 적용
- **4종 동시 업그레이드 trade-off** — bisect cost vs cognitive cost 임계값 박제
- **6-repo deprecated agent spawn 잔존 감사 lane** — MCT-128 진입 전 (HIGH) 우선 검토 trigger
- **plugin annotation 에 신규 contract 명 명시 의무** — `test-verdict-v2` / `review-verdict v4` 같은 contract version 이 향후 Story phase 진입 시 즉각 contract 식별 가능하게 함

---

**Status**: done — 본 RETRO 박제로 §11 PMO 회고 자동 dispatch 게이트 충족 (`feedback_pmo_retro_mandatory.md`). MCT-128 진입 전 §5 (HIGH) 후보 1개 우선 검토 권고.
