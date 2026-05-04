---
story_key: MCT-68
status: phase:완료
component: engine
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-002, ADR-006
---

# MCT-68: Strategy templates — TickScalpingStrategy + MarketMakingStrategy

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

> "전략 중에 틱띠기나 마켓 메이킹에 대한 전략도 필요하거든"

T2/T3 전략 템플릿 2종. **WFO 비적용 명시** (Codex F-15) — 본 템플릿은 ADR-006 promotion gate 통과 의무 없음 (별도 후속 Epic candidate, T2/T3 전용 검증 방법론). 사용자가 production 전략 작성 시 본 템플릿을 starting point 로 활용.

## 2. 도메인 해석

MCT-63 child #5 = **template only**. 실제 전략 = 사용자 별도 repo (e.g., `mctrader-strategies/`). 본 Story 는:

- TickScalpingStrategy: 틱띠기 (scalping) baseline
- MarketMakingStrategy: 마켓 메이킹 (MM) baseline

각 template 은 작은 합리적 default 값 + clear extension point (subclass override) + `REQUIRED_DATA_TIERS` 명시 (MCT-64 의무).

## 3. 관련 ADR

- **ADR-002 D2** — 동일 Strategy 가 backtest / paper / live 모두 동작 (MCT-67 측 enforcement). 본 template 는 strategy logic only.
- **ADR-006** — **비적용 명시** (template docstring + 본 file note). T2/T3 전략은 candle-기반 WFO promotion gate 와 다른 검증 방법론 필요 (별도 후속 Epic).

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/strategy/templates/
├── __init__.py
├── tick_scalping.py        (NEW — TickScalpingStrategy)
└── market_making.py        (NEW — MarketMakingStrategy)

mctrader-engine/tests/strategy/templates/
├── test_tick_scalping.py       (NEW — fixture event window 재생)
└── test_market_making.py       (NEW — fixture event window 재생)
```

## 5-6. 요구사항

### TickScalpingStrategy

1. **`@register_strategy("tick_scalping_v1")` + `REQUIRED_DATA_TIERS = frozenset({DataTier.TICK, DataTier.ORDERBOOK})`** — top-of-book 참조 시 orderbook 의무.
2. **로직** (default):
   - `consecutive_n` (default 3) 개 same-direction tick 이 `momentum_bps` (default 5) 이상 누적 시 시그널.
   - 시그널 = 반대편 LIMIT 주문 at top-of-book ± `entry_offset_bps` (default 1).
   - 진입 후 take-profit at `+tp_bps` (default 8), stop at `-sl_bps` (default 4), time-based forced exit at `max_hold_sec` (default 60).
   - 1 active position only (multi-position 비지원 v1).
3. **State**: 최근 N tick window (deque max=consecutive_n) + 현재 position.
4. **Extension points**: `on_tick` → subclass override 가능. `compute_signal` / `compute_entry_price` / `compute_exit_targets` 별 method 분리.
5. **Order flow**: `on_tick` 내 `self.submit_order(...)` 호출 (TradeExecutor Protocol).

### MarketMakingStrategy

6. **`@register_strategy("market_making_v1")` + `REQUIRED_DATA_TIERS = frozenset({DataTier.ORDERBOOK})`** — orderbook only.
7. **로직** (default):
   - top-of-book ± `half_spread_bps` (default 5) 위치에 양방 LIMIT post.
   - book imbalance (bid_qty - ask_qty) / (bid_qty + ask_qty) 가 `imbalance_threshold` (default 0.3) 초과 시 quote refresh (한쪽 cancel + 새 호가).
   - position > `target_position` (default 0) 시 quote skew (long-bias 시 ask 더 가까이 / bid 더 멀리).
   - inventory limit `max_inventory_qty` (default 0.1 BTC) 초과 시 한쪽 quote 중단.
8. **State**: own bid/ask order id + 현재 position + 현재 imbalance.
9. **Extension points**: `compute_quotes` / `should_refresh` / `compute_skew` method 분리.

### 공통

10. **WFO 비적용 명시** (F-15):
   - template module docstring: `"NOT a WFO-promotion-gated strategy. Use only with MCT-67 TickReplayExecutor for T2/T3 backtest. Production gating = separate Epic (TBD)."`
   - 본 Story 의 acceptance: `pytest -k 'wfo' tests/strategy/templates/` = no test (의도적).
11. **Unit test** (각 template):
   - 1 fixture event window 재생 (e.g., 100 tick + 200 orderbook event).
   - invariant assertion: signal trigger condition / order placement / exit condition.
   - position tracking 결정성.
12. **CLI registry visibility**: `mctrader-cli strategy list` (MCT-64 helper, optional) → 두 template 출력 + `REQUIRED_DATA_TIERS` 표시.
13. **버전 bump**: mctrader-engine 0.20.0 (MCT-67) → 0.21.0.
14. **CI green**.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: template 코드 only, 외부 노출 없음 (registry 등록).
- **신규 file**: `templates/tick_scalping.py` + `templates/market_making.py` + tests (4 file).
- **수정 file**: `strategy/__init__.py` (import side-effect for registry, optional).
- **Reversible**: yes (template 추가 = additive).

## 8. 사용자 ownership 명시

본 template 은 **starting point only**. 사용자 production 전략은 별도 repo (`mctrader-strategies/` 등) 에서 본 template subclass + tuning. WFO 사용 시 candle-기반 기존 strategy 사용 권장 (ADR-006 적용).
