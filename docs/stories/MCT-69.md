---
story_key: MCT-69
status: phase:완료
component: web
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-002
---

# MCT-69: Web UI tick backtest integration — strategy selector + tick result viewer

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

T2/T3 backtest 를 web UI 로 실행 + 결과 확인. MCT-48 backtest panel 기반 확장. Codex F-17/F-22 push-back 반영: contract-first (endpoint schema 먼저 freeze) + cursor pagination + ts-window downsample.

## 2. 도메인 해석

MCT-63 child #6 = **Web UI 통합 (Epic close 측)**. mctrader-web 의 BacktestLifecycleManager (MCT-48 Phase 5) + Streamlit `02_backtest_panel.py` 확장.

핵심 design:

- **Contract-first** (F-17): FastAPI endpoint schema 먼저 정의 + Pydantic v2 strict 모델. UI 는 schema 의무 사용 (backtest-only internals 누설 방지).
- **Cursor pagination + downsample** (F-22): tick detail = 수십만 row 가능. 한번 응답 = max 10k point default + cursor next.
- **DATA_TIER 시각화**: strategy class selector 옆에 `REQUIRED_DATA_TIERS` badge.

## 3. 관련 ADR

- **ADR-002 D2** — UI 가 strategy callback API 노출 안 함 (executor internals). result manifest + summary only.

## 4. 관련 코드 경로

```
mctrader-web/src/mctrader_web/api/
├── strategies.py           (NEW — GET /strategies endpoint)
├── backtests.py            (MODIFY — GET /backtests/{id}/tick_detail 추가)
└── models.py               (MODIFY — TickDetailResponse / StrategyInfo 추가)

mctrader-web/src/mctrader_web/dashboard/pages/
└── 02_backtest_panel.py    (MODIFY — strategy selector + tick result viewer)

mctrader-web/tests/
├── test_api_strategies.py          (NEW)
├── test_api_tick_detail.py         (NEW — pagination + downsample)
└── test_dashboard_backtest.py      (MODIFY — selector + tick viewer smoke)
```

## 5-6. 요구사항

### Contract-first endpoint schema (B1~B6)

1. **`GET /strategies`** — registry listing.
   - response model `StrategyInfo` Pydantic v2 strict:
     ```
     class StrategyInfo(BaseModel):
         model_config = ConfigDict(strict=True, extra="forbid")
         name: str
         required_data_tiers: list[str]   # sorted, ["candle"|"tick"|"orderbook"]
         docstring: str | None
     ```
   - response = `list[StrategyInfo]` sorted by name.
   - 인증: token (`~/.mctrader/local_token`).
2. **`POST /backtests` (MODIFY existing)** — `strategy_name` field 추가 (registry name). 미존재 시 422.
3. **`GET /backtests/{id}/tick_detail`** — per-fill orderbook context.
   - query: `?cursor=<opaque>&downsample=<int>&limit=<int>`.
   - cursor = base64(`{ts_utc, file_offset}`). 미주입 시 = window start.
   - downsample = ts-window seconds (예: `60` = 1분 단위 1 sample). default = `0` (no downsample, max 10k point).
   - limit = max row per response. default 1000, ceiling 10000.
   - response model `TickDetailResponse`:
     ```
     class TickDetailPoint(BaseModel):
         model_config = ConfigDict(strict=True, extra="forbid")
         ts_utc: datetime
         fill_price: Decimal
         queue_position: int | None  # MCT-67 reported
         own_qty: Decimal
         book_top_bid: Decimal | None
         book_top_ask: Decimal | None

     class TickDetailResponse(BaseModel):
         model_config = ConfigDict(strict=True, extra="forbid")
         points: list[TickDetailPoint]
         next_cursor: str | None
         total_estimate: int | None
     ```
4. **`POST /backtests` 가 strategy_name 부재 시 422** + `RequiredDataTiers coverage 부족 시 422` (`detail` field 에 부족한 tier 정보).
5. **OpenAPI schema** = FastAPI 자동 생성, smoke test 가 `/openapi.json` 검증.
6. **127.0.0.1 + token 의무** (MCT-48 / MCT-50 패턴 동일).

### Streamlit `02_backtest_panel.py` 확장 (B7~B11)

7. **Strategy selector**: `GET /strategies` 호출 → dropdown. 선택 시 옆에 `REQUIRED_DATA_TIERS` badge (예: `🕯️ candle / 📊 tick / 📖 orderbook`).
8. **Backtest 시작 form**: 기존 form + `strategy_name` 추가. 422 응답 시 사용자 친화적 메시지 (어느 tier 가 부족한지).
9. **Tick result viewer** (run history selection 후 active):
   - trade list 표 (existing).
   - per-fill queue position chart (line chart, ts vs queue_position) — `GET /tick_detail` cursor pagination 으로 chunk 로드.
   - orderbook depth mini-ladder render (각 fill 시점 top 5 level bid/ask 표).
10. **Downsample slider**: 기본 10초, range 1초~5분.
11. **DATA_TIER coverage 사전 체크**: 사용자가 backtest 시작 전에 `tier_coverage` 결과 미리 표시 (gap 경고 등). MCT-66 측 API call.

### Tests (B12~B15)

12. **`/strategies` smoke**: 등록된 strategy 가 listing 에 출현 + Pydantic strict.
13. **`/tick_detail` pagination**: cursor next 의무 동작 (page 1 → 2 → end).
14. **`/tick_detail` downsample**: 동일 window 다른 downsample 인자 → 다른 row count.
15. **422 response**: 미등록 strategy / tier coverage 부족 시 detail 필드 명확.

### Common

16. **버전 bump**: mctrader-web 0.4.0 (or 직전 버전) → 0.5.0.
17. **Cross-repo dep refresh**: mctrader-engine pin 갱신 (uv lock --upgrade-package mctrader-engine).
18. **CI green**.

### MCT-63 Epic close (Phase 6 마지막)

19. **EPIC-RESULTS-MCT-63.md** 작성 (다음 패턴 참조: EPIC-RESULTS-MCT-48.md).
20. **MCT-63 Story status close**: MCT-64 ~ MCT-69 모두 phase:완료.
21. **MEMORY 업데이트**: project_mctrader.md → Epic MCT-63 종료 + T2/T3 backtest 가능 명시.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: 127.0.0.1 + token 재사용 (MCT-48 / MCT-50 / MCT-55). `/strategies` 는 single-user listing (no perm boundary 추가).
- **신규 file**: `api/strategies.py` + tests (3 file).
- **수정 file**: `api/backtests.py` (tick_detail endpoint) / `api/models.py` (response model 추가) / `dashboard/pages/02_backtest_panel.py` (UI 확장) / cross-repo lock refresh.
- **Reversible**: yes (UI 확장 = additive, 기존 candle backtest path 영향 없음).
- **Performance budget**: tick_detail 1 page < 10k row, response payload < 5MB. cursor pagination 으로 unbounded payload 회피.
