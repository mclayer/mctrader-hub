## Project

`mctrader` — 암호화폐 자동매매 platform (개인용). KRW base, 백테스트 + 투자금액 관리. 첫 거래소 = Bithumb. **codeforge plugin family 의 첫 비-dogfood consumer (데뷔작)**.

SSOT 상수는 `.claude/_overlay/project.yaml` 참조.

## Domain

- 백테스트 → 페이퍼 트레이딩 (실전가상) → 라이브 (실거래) 의 3 mode pipeline
- 단일 KRW base 자금 관리 + 다중 전략 + 리스크 게이트 (drawdown / kill switch / max exposure)
- 도메인 용어: OHLCV (Open/High/Low/Close/Volume), 캔들, 호가 (OrderBook), 슬리피지 (slippage), 수수료 (fee/taker), 라이브/페이퍼/백테스트, walk-forward, look-ahead bias

## 6-Repo 구조

`mctrader-hub` (본 repo) = doc-only governance hub. Story / 도메인 ADR / Epic / cross-repo 조정 SSOT. **코드 없음**.

| Repo | 역할 | 의존 |
|---|---|---|
| `mctrader-hub` | governance / Story / ADR / Epic | — |
| `mctrader-market` | 거래소 interface (Candle / OrderBook / Order Protocol) | — |
| `mctrader-market-bithumb` | Bithumb HTTP API + WebSocket impl | `mctrader-market` |
| `mctrader-data` | OHLCV collector daemon + Parquet/DuckDB 저장 | `mctrader-market` (read), `mctrader-market-bithumb` (impl 주입) |
| `mctrader-engine` | 전략 + 리스크 + CLI + **Executor module (3 mode impl)** | `mctrader-market`, `mctrader-data` |
| `mctrader-web` | Streamlit UI (백테스트 결과 / 페이퍼 모니터링 / 라이브 가시성) | `mctrader-engine` |

## TradeExecutor (3 Mode)

`mctrader-engine/executor/` 내부 module. `Protocol` interface + 3 impl:

- **Backtest** (`executor/backtest.py`) — 적재 data 만, 정해진 기간 batch. 가상 fill (slippage 모델). 실시간 데이터 없음. 자금 = 가상.
- **Paper** (`executor/paper.py`, 실전가상) — 실시간 market data + 적재 data. 가상 자금 + 가상 주문 (실제 거래소 호출 안 함). 실전 운용 사전 검증.
- **Live** (`executor/live.py`, 실거래) — 실시간 market data + 적재 data + 실제 자금 + `mctrader-market-*` 호출. Secret + kill switch + drawdown 강제.

→ MCT-2 Story 에서 ADR 화. `mctrader-engine` 내부 module 위치 결정으로 6 repo 유지.

## 기술 스택 (선택 근거)

- **언어**: Python 3.11+ (numpy/pandas/duckdb 생태계 + Streamlit + ccxt-호환 패턴)
- **저장**: Parquet (OHLCV append-only) + DuckDB (in-process OLAP for 백테스트 / Streamlit 조회)
- **UI**: Streamlit (개인용, 빠른 반복)
- **거래소 SDK**: 자체 HTTP client (Bithumb 공식 doc 기준) — ccxt 미사용 (KRW pair quirks + 제어성)

## 경로 관습 (mctrader-hub 내부)

- `docs/stories/MCT-NN.md` — Story SSOT
- `docs/adr/ADR-NN-<slug>.md` — 도메인 ADR (codeforge ADR-N 와 별 카운터)
- `docs/change-plans/<slug>.md` — Architect Change Plan
- `docs/domain-knowledge/{market,risk,backtest,paper,live,contracts}/` — Domain KB

## codeforge consumer 데뷔 의무

매 Story 종료 시 Codex 가 codeforge 자체 개선점 평가 (7 카테고리). 발견 사항:

- **codeforge 개선 카테고리** → `mclayer/plugin-codeforge` issue 등록 (label: `audit:from-mctrader-debut` + `category:*`)
- **mctrader 도메인 결정** → 본 repo (`mclayer/mctrader-hub`) 측 처리

설치 시점 발견된 plugin defect 는 `docs/stories/` 첫 entry 와 별도로 plugin-codeforge 에 즉시 등록 (debut audit pre-Story).

## Cross-repo Epic

`mctrader-hub` 의 Epic = 6 repo 에 걸친 작업 graph. 각 child Story 는 owner repo 에서 작성하나 parent Epic milestone 은 hub 에서 추적. `epic_dependencies` field 사용 (CFP-60 Phase 1 ADR-020 wrapper extension 후 활성).

## 의존 관계

- **Session 1** (다른 세션): `mclayer/plugin-codeforge` 의 CFP-60 (cross-repo Epic + debut-audit + phase-gap signal) 진행 중. Phase 1 PR merge 가 본 repo 의 Epic MCT-12 시작 전 dependency.
- **본 세션** (Session 2): mctrader-hub scaffolding + MCT-1 ~ MCT-11 도메인 ADR 작성 가능. MCT-12 (Bithumb OHLCV → SMA backtest end-to-end) 은 CFP-60 merge 후.

## Sonnet decider

substantive 다중 결정 시 ADR-019 (CFP-59) Sonnet decider protocol 적용. 본 repo 의 도메인 ADR 작성 시에도 동일.

## codeforge 의무 사용 (CFP-96 Phase 6a, ADR-027)

mctrader-hub = codeforge plugin family 의 첫 비-dogfood consumer (debut). 본 Phase 6a 진입 시점 (2026-05-05) 부터 codeforge protocol 의무 적용.

### 의존 plugin (9개) — `/plugins install` 등록 의무

```
codeforge@mclayer
codeforge-requirements@mclayer
codeforge-design@mclayer
codeforge-develop@mclayer
codeforge-test@mclayer
codeforge-review@mclayer
codeforge-pmo@mclayer
github@claude-plugins-official
codex@openai-codex
superpowers@claude-plugins-official
claude-md-management@claude-plugins-official
```

### 3-trigger enforcement (ADR-027 §결정-2)

1. **Primary** — Story phase 진입: `phase-gate-mergeable.yml` (CFP-106 fast-pass 적용 — type:epic + doc-only 자동 success) + `phase-label-invariant.yml`
2. **Secondary** — UserPromptSubmit hook: 변경 요청 prompt regex 검출 → reminder inject (`overlay/hooks/userprompt-reminder.sh`)
3. **Tertiary** — SessionStart hook: `regen-agents.sh` (overlay merge) + `check-bootstrap.sh` (9 plugin / 7 workflow / 3 form / project.yaml schema 검증)

### Bypass (HOTFIX 시)

```bash
HOTFIX_BYPASS_CODEFORGE=1 HOTFIX_BYPASS_REASON='<incident-id>' <명령>
```

양 env 모두 set 의무. flag 만 set 시 reminder 에 WARN.

### Story workflow (codeforge ζ arc)

- KEY: `MCT-N` (mctrader 6-repo 통합 카운터, project.yaml `github.story_key_prefix=MCT`)
- Story 신규: `.github/ISSUE_TEMPLATE/story.yml` 사용 → `story-init.yml` Action 이 §1-7 자동 scaffold (CFP-105)
- Path: `docs/stories/MCT-N.md` (single-repo flavor, CFP-65)
- Phase: 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → 구현-테스트 → 보안-테스트 → 완료
- Sonnet decider 의무 (ADR-022) — 모든 design / scope 결정점에서 Sonnet 합성 필수

### Settings hook 등록 (`.claude/settings.json`)

CFP-108 Phase 6a 진입 시 hook 확장:
- SessionStart: `regen-agents.sh` + `check-bootstrap.sh` 양 hook 등록 (nested 3-level schema)
- UserPromptSubmit: `userprompt-reminder.sh` 신규 등록 (CFP-104 implementation)
- Schema = EventName -> [{ matcher?, hooks: [{type: "command", command}] }] (CFP-106 #169 fix 후 정합)

### Cross-repo Story 추적 (5 sister)

5 sister repo (`mctrader-market`, `mctrader-market-bithumb`, `mctrader-data`, `mctrader-engine`, `mctrader-web`) 의 변경도 hub MCT-N 으로 추적 (Mode B cross-repo, ADR-020).
Phase 6b (CFP-111) 에서 5 sister repo 의 codeforge adoption 완료 예정 (Phase 6a 의 finding fix-back 후).

### overlay agents (CFP-108)

- `.claude/_overlay/agents/DomainAgent.md` — 자동매매 도메인 전문가 (RequirementsPL sub-agent, CFP-37)
- `.claude/_overlay/agents/DataEngineerAgent.md` — DuckDB / Parquet / OHLCV 특화 (DeveloperPL sub-agent, CFP-39)
