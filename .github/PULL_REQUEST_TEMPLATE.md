<!--
  CodeForge PR Template — 다음 두 형식 중 하나를 사용하세요.

  Phase 1 PR (요구사항·설계·설계리뷰 lane): docs/stories/**/§1-7 + docs/change-plans/**/+ docs/adr/**
  Phase 2 PR (구현·구현리뷰·구현테스트·보안테스트 lane): src/** + tests/** + docs/stories/**/§8-11 append

  사용하지 않는 phase 섹션은 통째로 삭제하세요.
-->

## Story

- Story Issue: # (자동 매핑)
- Story SSOT: `docs/stories/<KEY>.md`
- Change Plan: `docs/change-plans/<slug>.md`

---

## (Phase 1 only) 요구사항·설계·설계리뷰 PR

### 변경 요약
<!-- 무엇을 했는가, 왜 (1-3 bullet) -->

### 핵심 설계 결정
<!-- ADR 신규/갱신 여부, 핵심 결정 근거 -->
- ADR: `docs/adr/ADR-NNN-<slug>.md`
- 결정 근거: ...

### 설계 리뷰 PASS 증거
- 설계 리뷰 iteration: <N>회
- DesignReviewPL 종합 판정: PASS
- ADR 정합성: 위반 0건
- (또는) Change Plan §3 vs ADR 정합성 확인 결과

### Test plan (Phase 1)
<!-- 본 PR 머지 전에 수행할 검토 -->
- [ ] Story §1 verbatim 그대로 (story-init.yml 결과 검증)
- [ ] §3-§7 모두 채워짐 (placeholder 0건)
- [ ] ADR 정합성 위반 0건
- [ ] CodebaseMapper 분석 §2 ↔ Refactor 제안 §3 대립 조정 명시

---

## (Phase 2 only) 구현·구현리뷰·구현테스트·보안테스트 PR

Closes #<Story Issue 번호>

### 변경 요약
<!-- 무엇을 했는가, 왜 (1-3 bullet) -->

### Impl Manifest §8.5
<!-- subissue-from-impl-manifest.yml이 자동 생성하는 sub-issue 목록 (자동 채움) -->

### Test plan (Phase 2)
- [ ] 단위 테스트 PASS
- [ ] 통합 테스트 PASS
- [ ] 인프라 테스트 PASS (해당 시)
- [ ] 성능 테스트: baseline 대비 mean ≤ +10%
- [ ] 보안 테스트 PASS (Dependabot/CodeQL/Secret Scanning + Claude/Codex Security)

### FIX 이력
<!-- docs/stories/<KEY>.md §10 FIX Ledger 참조 -->
- 구현 리뷰 FIX iteration: <N>회 (최대 3)
- 구현 테스트 FIX iteration: <N>회 (무제한)
- 보안 테스트 FIX iteration: <N>회 (무제한)

---

🤖 Generated with [CodeForge plugin](https://github.com/mctrader/plugin-codeforge)
