---
story_key: MCT-64
status: phase:완료
component: engine
type: brainstorm
parent_epic: MCT-63
related_adrs: ADR-002, ADR-009
---

# MCT-64: Strategy registry + REQUIRED_DATA_TIERS frozenset

## 1. 사용자 요구사항 (verbatim, MCT-63 Epic Phase 1)

3-tier (T1 candle / T2 tick / T3 orderbook) market data 모델 도입의 첫 단계. 모든 후속 Story (MCT-66 reconstruction / MCT-67 executor / MCT-68 template / MCT-69 web) 가 의존. Codex F-4 push-back 반영: 단일 `Literal[…]` 거부, multi-tier 지원 `frozenset` 채택.

## 2. 도메인 해석

MCT-63 child #1 = **registry foundation**. 기존 mctrader-engine 의 모든 Strategy 가 candle-only 였으므로, tier declaration 의무화 + dispatch infrastructure 도입. registry 는 web UI (MCT-69) 의 strategy class selector 의 input source.

`Strategy` ABC 확장 시 backward-compat: 기존 candle-only 전략은 `REQUIRED_DATA_TIERS = frozenset({DataTier.CANDLE})` 명시 후 그대로 동작. `on_tick` / `on_orderbook` callback 은 default no-op.

## 3. 관련 ADR

- **ADR-002 D2** — 같은 view across 3 mode. `Strategy` callback API (`on_candle` / `on_tick` / `on_orderbook`) Backtest / Paper / Live 공통. tier 추가는 ADR-002 D2 invariant 강화 (mode invariant common API).
- **ADR-009 §D1~§D11** — T1/T2/T3 schema 의 source. tier coverage 검증 시 `tier_coverage` API (MCT-66) 참조.

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/strategy/
├── __init__.py           (MODIFY — Strategy ABC 확장)
├── tiers.py              (NEW — DataTier Enum)
├── registry.py           (NEW — STRATEGY_REGISTRY + decorator)
└── exceptions.py         (NEW — TierCoverageError)

mctrader-engine/src/mctrader_engine/cli.py    (MODIFY — registry import side-effect for backtest CLI)
```

## 5-6. 요구사항

1. **`DataTier` Enum** (`tiers.py`): `CANDLE = "candle"` / `TICK = "tick"` / `ORDERBOOK = "orderbook"`. ordering 의미 없음 (frozenset usage).
2. **`Strategy` ABC 확장** (`__init__.py`):
   - `REQUIRED_DATA_TIERS: ClassVar[frozenset[DataTier]]` — 누락 시 `TypeError` 명시 (직접 init 시), `register_strategy` 에서도 reject.
   - `on_candle(self, candle) -> None` — default raise NotImplementedError if `CANDLE in REQUIRED_DATA_TIERS`, else no-op.
   - `on_tick(self, tick) -> None` — same pattern with TICK.
   - `on_orderbook(self, event) -> None` — same pattern with ORDERBOOK.
3. **`STRATEGY_REGISTRY: dict[str, type[Strategy]]`** + `@register_strategy("name")` decorator (`registry.py`):
   - 동일 name 재등록 = `RuntimeError("strategy already registered: …")`.
   - decorator 가 `REQUIRED_DATA_TIERS` 부재 시 fail-fast (정의되지 않으면 등록 거부).
   - `get_strategy(name) -> type[Strategy]` lookup helper.
   - `list_strategies() -> list[StrategyInfo]` (name + REQUIRED_DATA_TIERS + docstring) — MCT-69 의 `GET /strategies` source.
4. **Backtest entry tier coverage check** (`cli.py` 또는 backtest entrypoint MODIFY):
   - 전략 instantiate 후 `REQUIRED_DATA_TIERS` 의 union 만큼 `tier_coverage` (MCT-66) 호출.
   - `T1` = `scan_candles` window coverage, `T2`/`T3` = `tier_coverage` API 호출 (MCT-66 dependency 인정 — Phase 2 에서는 stub 반환 가능, MCT-66 후 hard-wire).
   - 부족 시 `TierCoverageError` raise (어느 tier / 어느 window 가 부족한지 명시).
5. **`TierCoverageError`** (`exceptions.py`) — `requested_tiers`, `available_tiers`, `gaps` field.
6. **기존 candle-only 전략 migration**: `REQUIRED_DATA_TIERS = frozenset({DataTier.CANDLE})` 명시 + `on_candle` 구현 유지 (이미 구현됨). registry 등록 추가.
7. **Unit tests**:
   - `REQUIRED_DATA_TIERS` 누락 = TypeError fail-fast.
   - `register_strategy` 동일 name = RuntimeError.
   - decorator 가 ABC subclass 검증.
   - `Strategy().on_tick(...)` (TICK 미요구) = no-op.
   - `Strategy().on_tick(...)` (TICK 요구 + 미구현) = NotImplementedError.
   - tier coverage 부족 = `TierCoverageError`.
8. **버전 bump**: mctrader-engine 0.18.0 (or 직전 버전) → 0.19.0.
9. **CI green**.

## 7. 보안 설계 / 11. 데이터 영향

- **보안**: registry = 모듈 globals, 외부 노출 없음 (FastAPI `GET /strategies` 는 read-only listing, MCT-69 측 token 검증).
- **신규 file**: `strategy/tiers.py` / `strategy/registry.py` / `strategy/exceptions.py` + tests.
- **수정 file**: `strategy/__init__.py` (ABC 확장) / `cli.py` (tier coverage hook).
- **Reversible**: yes (ABC 확장 = backward-compat, decorator + registry = additive).
