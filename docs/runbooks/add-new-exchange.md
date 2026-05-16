# 신규 거래소 추가 runbook (D5 invariant — data 단독, engine 변경 0)

> **ADR-031 §D5 `data-only-extension-invariant`** — 신규 거래소 추가는 data 레이어 단독으로
> 완결된다. engine 변경 0 / market-core 변경 0 / ADR 변경 0.
>
> **SSOT**: `docs/adr/ADR-031-data-domain-decoupling.md §D5` + `scope_manifests/EPIC-data-domain-decoupling.yaml §design_decisions.D5`
> **검증 gate**: `tests/test_multi_exchange_invariant.py` (MCT-187 LAND, data full suite 포함)

---

## 전제 조건

- mctrader-market-bithumb (v0.3.0) / mctrader-market-upbit (v0.1.0) 을 Layer 1 어댑터 패턴 레퍼런스로 사용
- `mctrader-market` CandleProvider / OrderBookProvider Protocol 이해 필수 (Layer 0 SSOT)
- `mctrader-data adapters.py` 편집 권한 + data repo PR 생성 권한

---

## Step 1: Layer 1 어댑터 repo 신설

새 거래소 `<exchange>` 에 대해 `mctrader-market-<exchange>` GitHub repo 를 신설한다.

### 1-1 repo 생성

```bash
gh repo create mclayer/mctrader-market-<exchange> --private
```

### 1-2 패키지 구조 초기화

```
mctrader-market-<exchange>/
  src/
    mctrader_market_<exchange>/
      __init__.py
      adapter.py      # CandleProvider Protocol 구현
      ws_client.py    # WebSocketStream Protocol 구현 (실시간 수집)
      types.py        # 거래소 내부 이벤트 타입 (engine 미노출)
  pyproject.toml
  tests/
```

### 1-3 adapter.py (CandleProvider Protocol 구현)

```python
# src/mctrader_market_<exchange>/adapter.py
from mctrader_market.protocols import CandleProvider  # Layer 0 Protocol SSOT
from mctrader_market.candle import CandleModel

class <Exchange>CandleProvider:
    """Layer 1 — <Exchange> CandleProvider (CandleProvider Protocol 준수)."""

    def get_candles(self, symbol, timeframe, start, end) -> list[CandleModel]:
        # 거래소 REST API 호출 → CandleModel 정규화
        ...
```

### 1-4 ws_client.py (WebSocketStream Protocol 구현)

```python
# src/mctrader_market_<exchange>/ws_client.py
# Layer 0 TickRowV1_1 (market-core SSOT) 정규화 의무
# stream key: market:tick:{exchange}:{symbol} (ADR-030 §D15 prefix)
```

### 1-5 pyproject.toml 의존

```toml
[project]
dependencies = [
    "mctrader-market @ git+https://github.com/mclayer/mctrader-market.git@main",
    # mctrader-data 의존 금지 (Layer 1 = Layer 0 의존만)
    # mctrader-engine 의존 금지
]
```

### 1-6 검증 체크리스트 (Step 1)

- [ ] `mctrader-market.protocols.CandleProvider` Protocol 준수 확인 (`isinstance` 또는 `runtime_checkable` 통과)
- [ ] engine import 없음 (`grep -rn "mctrader_engine" src/` = 0건)
- [ ] mctrader-data import 없음 (`grep -rn "mctrader_data" src/` = 0건)
- [ ] mctrader-market import 만 존재 (Layer 0 SSOT 단방향)

---

## Step 2: mctrader-data adapters.py 등록

`mctrader-data` repo 의 `src/mctrader_data/adapters.py` 에 신규 거래소 분기를 추가한다.

### 2-1 get_candle_provider 분기 추가

```python
# src/mctrader_data/adapters.py
def get_candle_provider(exchange: str) -> object:
    if exchange == "bithumb":
        from mctrader_market_bithumb.adapter import BithumbCandleProvider
        return BithumbCandleProvider()
    if exchange == "upbit":
        from mctrader_market_upbit.adapter import UpbitCandleProvider
        return UpbitCandleProvider()
    # ↓ 신규 거래소 추가 (이 줄만 추가)
    if exchange == "<exchange>":
        from mctrader_market_<exchange>.adapter import <Exchange>CandleProvider
        return <Exchange>CandleProvider()
    raise ValueError(f"unknown exchange: {exchange!r}")
```

### 2-2 get_ws_stream 분기 추가

```python
def get_ws_stream(exchange: str, symbol: Symbol, *, include_transactions: bool, ...) -> object:
    # ... bithumb / upbit 기존 분기 ...
    if exchange == "<exchange>":
        from mctrader_market_<exchange>.ws_client import <Exchange>WebSocketStream
        channels = []
        if include_transactions:
            channels.append("<transaction_channel_name>")
        # ... 거래소별 채널 매핑 ...
        return <Exchange>WebSocketStream(symbol=symbol, channels=channels, **kwargs)
    raise ValueError(f"unknown exchange: {exchange!r}")
```

### 2-3 pyproject.toml 의존 추가 (data repo)

```toml
[project.dependencies]
# 기존 의존 유지 ...
"mctrader-market-<exchange> @ git+https://github.com/mclayer/mctrader-market-<exchange>.git@main",
```

### 2-4 검증 체크리스트 (Step 2)

- [ ] `uv run pytest tests/test_adapters.py -v` — 기존 6 TC PASS (회귀 0)
- [ ] `uv run pytest tests/test_multi_exchange_invariant.py -v` — D5 invariant test 5 TC PASS
- [ ] `grep -rn "mctrader_engine" src/mctrader_data/adapters.py` = 0건 (engine 의존 0)
- [ ] **engine repo 변경 0** — PR diff 에 `mctrader-engine/` 파일 없음
- [ ] **market-core repo 변경 0** — PR diff 에 `mctrader-market/` 파일 없음 (Layer 0 변경 0)
- [ ] **ADR 변경 0** — `docs/adr/` 변경 없음 (D5 invariant 영구)

---

## Step 3: data 수집/정규화 설정

`mctrader-data` 의 수집기(`collector.py` 또는 관련 설정)에 신규 거래소를 활성화한다.

### 3-1 수집 설정 추가

신규 거래소의 Symbol 목록 + 채널 설정을 data 수집 설정에 추가한다. 구체적 방식은 data repo
`collector.py` 또는 설정 파일 구조에 따름.

### 3-2 정규화 검증

- TickRowV1_1 schema 정합 (market-core Layer 0 SSOT)
- Redis Stream publish key: `market:tick:<exchange>:<symbol>` (ADR-030 §D15)

### 3-3 검증 체크리스트 (Step 3)

- [ ] 신규 거래소 tick 수집 smoke test (data 로컬 실행)
- [ ] Redis Stream `market:tick:<exchange>:*` XREAD 확인
- [ ] TickRowV1_1 deserialization 성공 (engine Redis subscriber 패턴 정합)

---

## 필수 불변식 체크리스트 (merge 전 전수 확인)

D5 invariant — 이 체크리스트를 통과해야만 PR merge 가능:

```
[ ] engine repo 변경 0  (git diff --name-only | grep mctrader-engine = 0)
[ ] market-core repo 변경 0  (git diff --name-only | grep mctrader-market/src = 0)
[ ] ADR 변경 0  (docs/adr/ 파일 변경 없음, D5 invariant = ADR 불요)
[ ] tests/test_multi_exchange_invariant.py PASS (5 TC, 0 FAIL)
[ ] tests/test_adapters.py PASS (6 TC, 0 FAIL — 기존 회귀 0)
[ ] data full suite 신규 실패 0
```

---

## 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/adr/ADR-031-data-domain-decoupling.md §D5` | D5 결정 SSOT + VERIFIED amendment box |
| `scope_manifests/EPIC-data-domain-decoupling.yaml §design_decisions.D5` | D5 option_chosen/rationale |
| `src/mctrader_data/adapters.py` | 팩토리 코드 SSOT |
| `tests/test_multi_exchange_invariant.py` | D5 invariant 회귀 방지 test (MCT-187 LAND) |
| `docs/runbooks/nas-credential-rotation-automation.md` | NAS credential 관련 |
| `mctrader-market-bithumb` / `mctrader-market-upbit` | Layer 1 어댑터 레퍼런스 구현 |
