---
story_key: MCT-74
status: phase:완료
component: web
type: brainstorm
parent_epic: MCT-70
related_adrs: ADR-002
---

# MCT-74: Streamlit T2/T3 tick result viewer + Epic close

## 1. 사용자 요구사항 (verbatim, MCT-70 Epic Phase 1)

`02_backtest_panel.py` conditional render: T1 = 기존 chart, T2/T3 = trade list + per-fill orderbook context viewer + Epic close.

## 2. 도메인 해석

MCT-70 child #4 = **UI viewer + Epic close**.

핵심 design:

- **Conditional render**: 결과 manifest 읽기 → strategy 의 REQUIRED_DATA_TIERS 기준 분기. T1 (`{CANDLE}`) = 기존 equity chart + summary. T2/T3 = trade list table + queue_position chart + book mini-ladder.
- **Tick result viewer**: trade list (DataFrame), per-fill orderbook context (cursor pagination + downsample 슬라이더), queue position 시계열 (line chart, queue_position vs ts), book top bid/ask 시계열 (dual line chart).
- **Epic close**: EPIC-RESULTS-MCT-70 + 4 child Story status update.

## 3. 관련 ADR

- ADR-002 D2 — UI 가 strategy callback API 노출 안 함 (executor internals). result manifest + summary only.

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/dashboard/pages/
└── 02_backtest_panel.py    (MODIFY — conditional render T1/T2/T3 + tick viewer)

mctrader-web/src/mctrader_web/dashboard/
└── tick_viewer.py          (NEW — render_tick_result helper)

mctrader-hub/docs/
├── EPIC-RESULTS-MCT-70.md  (NEW)
└── stories/MCT-70.md ~ MCT-74.md  (status: phase:완료)
```

## 5-6. 요구사항

### Conditional render

1. **결과 manifest 읽기**: 선택된 run_id 의 `<run_dir>/manifest.json` 존재 + matching_model 검사.
   - matching_model 부재 = T1 (기존 path).
   - matching_model 존재 = T2/T3 (tick viewer).
2. **T2/T3 viewer** (`render_tick_result` helper):
   - **Trade list**: trade DataFrame (ts_utc / side / price / quantity / cumulative_pnl). pagination 지원.
   - **Queue position chart**: `/tick_detail?cursor=&downsample=` 호출 → DataFrame → Plotly line (ts vs queue_position).
   - **Book mini-ladder** at fill timestamps: top 5 level bid/ask (manifest 외 추가 read 가 필요할 수 있음 — v1 = top_bid/top_ask single-line chart).
3. **Downsample 슬라이더**: 1초~5분, default 10초.
4. **Pagination**: "Load more" button → cursor next.

### Streamlit Page Layout

5. **Page title**: "Backtest Panel" (기존 유지).
6. **Result section**: run history 선택 → `manifest.json` 검사 → conditional render.
7. **T1 path**: 기존 equity chart + 5 summary metric (no change).
8. **T2/T3 path**: 새 viewer 5 sub-section (trade list, queue chart, book chart, tier-coverage badge, summary metrics).

### Tests (smoke)

9. **AppTest smoke**: T2/T3 manifest fixture 로드 + render_tick_result 가 raise 하지 않음.
10. **Pagination smoke**: cursor → next page 작동.

### Epic close

11. **EPIC-RESULTS-MCT-70.md** (mctrader-hub) — Phase 1~5 PR 표 + Codex review summary + Sonnet decider log + Out-of-scope.
12. **Child Story status**: MCT-70 / MCT-71 / MCT-72 / MCT-73 / MCT-74 모두 `phase:완료`.
13. **MEMORY 업데이트**: project_mctrader.md → Epic MCT-70 종료 + T2/T3 backtest UI 가능 명시.

### Common

14. **버전 bump**: mctrader-web 0.8.0 → 0.9.0.
15. **CI green** (web ubuntu).

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: 기존 token + 127.0.0.1 (변경 없음).
- **신규 file**: `tick_viewer.py` + EPIC-RESULTS-MCT-70.md.
- **수정 file**: `02_backtest_panel.py`.
- **Reversible**: yes (UI 확장 = additive).
- **Performance budget**: tick_detail 1 page render < 1초 (10k point Plotly).
