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

## 경로 관습

### mctrader-hub (governance hub)

- `docs/stories/MCT-NN.md` — Hub story SSOT (배경·방향·위임 링크만, 구현 상세 없음)
- `docs/adr/ADR-NN-<slug>.md` — 도메인 ADR (codeforge ADR-N 와 별 카운터)
- `docs/change-plans/<slug>.md` — Architect Change Plan
- `docs/domain-knowledge/{market,risk,backtest,paper,live,contracts}/` — Domain KB
- `.codeforge/counters.json` — repo별 MCT-NNN 독립 시퀀스 카운터

### impl repo (mctrader-data / market / market-bithumb / engine / web)

- `docs/stories/MCT-NN.md` — Repo story (구현 상세 전담, 해당 repo 내 독립 시퀀스)

### Story key 체계

| 위치 | 형식 | 예시 |
|---|---|---|
| mctrader-hub | `MCT-NNN` | `MCT-112` |
| impl repo | `MCT-NNN` (repo 내 독립 시퀀스) | `MCT-001` |
| Cross-repo 참조 | `{repo-name}#MCT-NNN` | `mctrader-data#MCT-001` |

기존 `MCT-1~111` = legacy-hub (파일 이동 없음). 신규 hub story는 `MCT-112`부터, 각 impl repo는 `MCT-001`부터.

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
codeforge-test@mclayer          # DEPRECATED (CFP-317/ADR-048) — CI-native 전환, 유지만
codeforge-review@mclayer
codeforge-pmo@mclayer
github@claude-plugins-official
codex@openai-codex
superpowers@claude-plugins-official
claude-md-management@claude-plugins-official
```

### codeforge 업그레이드 프로세스

codeforge plugin upgrade 시 **반드시** 각 plugin CHANGELOG 를 읽고 consumer-facing 변경 사항을 이 파일에 반영한다. 확인 순서:

1. `plugin-codeforge/CHANGELOG.md` — core (Orchestrator 지침 / ADR / contract 변경)
2. lane plugin CHANGELOGs — pmo / requirements / design / develop / test / review
3. **Breaking change** → Story workflow / plugin list / phase 순서 즉시 갱신
4. **Deprecation** → plugin list 주석 업데이트 + Story phase 에서 제거

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

- **Hub KEY**: `MCT-NNN` — 배경·방향·위임 링크만. 구현 상세 없음. `mctrader-hub/docs/stories/MCT-NNN.md`
- **Repo KEY**: `MCT-NNN` — 구현 상세 전담. 각 impl repo의 `docs/stories/MCT-NNN.md` (repo 내 독립 시퀀스)
- **Story 범위 결정**: hub only (governance/ADR/cross-repo policy) / repo only (단일 repo 구현) / hub+repo (cross-repo 구현·rollout)
- **Cross-repo 참조**: `{repo-name}#MCT-NNN` (예: `mctrader-data#MCT-001`)
- Story 신규: `.github/ISSUE_TEMPLATE/story.yml` 사용 → `story-init.yml` Action 이 §1-7 자동 scaffold (CFP-105)
- Phase: 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → CI 테스트 (`gh pr checks` polling, ADR-048) → 보안-테스트 → 완료 → **PMO 회고 (의무)**
- Sonnet decider 의무 (ADR-022) — 모든 design / scope 결정점에서 Sonnet 합성 필수

### Story 완료 의무 — PMO 회고 자동 dispatch (RETRO-MCT-107-111 §8 ESCALATE 후속)

모든 Story AC 완료 직후, Orchestrator 는 **사용자 요청 없이도** `codeforge-pmo:PMOAgent` 를 자동 dispatch 해서 §11 회고를 수행한다. 이는 admin merge autonomy (MEMORY `feedback_admin_merge_autonomy.md`) 와 동일한 자율 패턴 — 사용자 trigger 대기 금지.

- **트리거**: AC 통과 + admin merge 완료 → 다음 Story 로 직진하기 전에 PMOAgent dispatch
- **산출물**: hub story는 `mctrader-hub/docs/stories/MCT-N.md` §11, repo story는 해당 repo `docs/stories/MCT-N.md` §11 (PMOAgent 직접 write, CFP-36 owner direct write)
- **묶음 retro**: cross-Story 패턴 발견 시에도 개별 §11 은 dispatch 시점 박제, 묶음 retro 는 별도 `docs/retros/RETRO-*.md` 로 추가 작성
- **위반 이력**: MCT-107~111 5 Story 연속 0/5 누락 (RETRO-MCT-107-111 §8 참조). 이 게이트는 그 재발 방지용 SSOT.

### Settings hook 등록 (`.claude/settings.json`)

CFP-108 Phase 6a 진입 시 hook 확장:
- SessionStart: `regen-agents.sh` + `check-bootstrap.sh` 양 hook 등록 (nested 3-level schema)
- UserPromptSubmit: `userprompt-reminder.sh` 신규 등록 (CFP-104 implementation)
- Schema = EventName -> [{ matcher?, hooks: [{type: "command", command}] }] (CFP-106 #169 fix 후 정합)

### Cross-repo Story 구조 (5 sister)

5 sister repo (`mctrader-market`, `mctrader-market-bithumb`, `mctrader-data`, `mctrader-engine`, `mctrader-web`) 는 각자 `docs/stories/` 를 소유한다.

- **Hub MCT-NNN** (mctrader-hub) = 배경·방향·`delegates[]` 링크. 구현 상세 없음.
- **Repo MCT-NNN** (각 impl repo) = 구현 상세 전담. `hub_story: MCT-NNN` 역링크 포함.
- Frontmatter: hub story → `story_scope: hub` + `delegates[]`, repo story → `story_scope: repo` + `repo:` + `hub_story:`
- plugin-codeforge#342 merge 전까지는 `story_scope` + `repo` frontmatter 수동 기입.

### overlay agents (CFP-108)

- `.claude/_overlay/agents/DomainAgent.md` — 자동매매 도메인 전문가 (RequirementsPL sub-agent, CFP-37)
- `.claude/_overlay/agents/DataEngineerAgent.md` — DuckDB / Parquet / OHLCV 특화 (DeveloperPL sub-agent, CFP-39)

## ADR-019 Preflight 표준 시퀀스

MCT-100/101/102/110 parallel agent branch race 재발 방지. 6 repo 공통 의무.

### 병렬 에이전트 (2+ 동시 실행) — D1 worktree 필수

```powershell
# Step 1: Python 3.12 검증 (D2)
py -3.12 --version

# Step 2: Worktree 생성 (D1)
.\scripts\agent-worktree.ps1 -Branch "feat/branch-name"
# 반환된 절대 경로로 이동
Set-Location "<worktree-absolute-path>"

# Step 3: Venv 생성 + 활성화
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Step 4: Editable install (D3) — mctrader-hub 제외
py -3.12 -m pip install -e ".[dev]" --quiet

# Step 5: 작업 수행
py -3.12 -m pytest tests/ -v

# Step 6: Cleanup
deactivate
Set-Location "C:\workspace\mclayer\<repo>"
.\scripts\agent-worktree.ps1 -Branch "feat/branch-name" -Mode cleanup
```

### 단일 에이전트 — D4 Branch Guard 필수

```powershell
# Step 1: Python 3.12 검증 (D2)
py -3.12 --version

# Step 2: Venv 생성 + 활성화
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Step 3: Editable install (D3) — mctrader-hub 제외
py -3.12 -m pip install -e ".[dev]" --quiet

# Step 4: Branch 검증 (D4) — 커밋 직전 매번
$currentBranch = git branch --show-current
$expectedBranch = "feat/branch-name"
if ($currentBranch -ne $expectedBranch) {
    throw "BRANCH MISMATCH: expected=$expectedBranch, current=$currentBranch — aborting"
}

# Step 5: 작업 수행
py -3.12 -m pytest tests/ -v
```

### Preflight Scripts

| 스크립트 | 역할 | ADR |
|---|---|---|
| `scripts/agent-preflight.ps1` | D2/D3/D4 자동화 | ADR-019 |
| `scripts/agent-worktree.ps1` | D1 worktree 생성/정리 | ADR-019 |

### D5: 6 repo 적용 범위

| Repo | D1 worktree | D2 Python | D3 Editable | D4 Branch guard |
|---|---|---|---|---|
| mctrader-hub | 의무 | 의무 | N/A | 의무 |
| mctrader-market | 의무 | 의무 | 의무 | 의무 |
| mctrader-market-bithumb | 의무 | 의무 | 의무 | 의무 |
| mctrader-data | 의무 | 의무 | **HIGH** | 의무 |
| mctrader-engine | 의무 | 의무 | **HIGH** | 의무 |
| mctrader-web | 의무 | 의무 | 의무 | 의무 |

> `mctrader-data`, `mctrader-engine`: MCT-110에서 stale wheel 문제 직접 확인 → D3 우선순위 HIGH
