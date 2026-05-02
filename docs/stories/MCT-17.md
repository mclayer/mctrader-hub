---
story_key: MCT-17
status: phase:대기
component: web
type: brainstorm
parent_epic: MCT-12
related_adrs: ADR-010, ADR-011
---

# MCT-17: mctrader-web Streamlit equity curve dashboard

## 1. 사용자 요구사항 (verbatim, MCT-12 Epic)

> "MCT-17: mctrader-web Streamlit equity curve"

## 2. 목표

`mctrader-web` repo:
- Streamlit single-page app
- equity_curve.csv (MCT-16 산출) 읽어 chart 표시
- final equity / max drawdown / sharpe (ExecutionReport JSON 에서 추출) 표시
- finalized output 만 read (live DuckDB concurrent read = MCT-12 out-of-scope)

## 3. 시작 조건

- MCT-16 Phase 2 merge — equity_curve.csv + ExecutionReport JSON schema freeze
- 첫 publish version = `0.1.0`

## 4. 의존

- 상위 의존: MCT-16 (output schema)
- 하위 의존자: 없음 (Epic 의 마지막 child)

## 5. Acceptance (placeholder — Phase 1 brainstorm 에서 확정)

- TBD: Streamlit page 구성 (single page vs multi-tab)
- TBD: chart library (plotly vs altair vs streamlit native)
- TBD: equity_curve 갱신 정책 (file watch vs manual refresh — MCT-12 = manual)
- TBD: 결과 file 위치 발견 (default path 또는 user upload)

## 6. Phase 1 brainstorm 진행

MCT-16 Phase 2 merge 후 Codex 일괄 dispatch → Sonnet 합성 → Story doc → Phase 1 PR. (가장 가벼운 single Story — 시각화 only.)

## 7. CFP-60 debut-audit

Phase 2 merge 직후 audit signal check + 7-카테고리 평가. **Epic 의 마지막 child = Epic close PR 의 trigger.**

## 8. Epic 종료 trigger

본 Story Phase 2 merge + Blocking AC B1~B6 통과 시 MCT-12 Epic close PR (EPIC-RESULTS.md + final equity/sharpe/drawdown/Codex aggregate adoption rate) 작성.
