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

## Claude decider (구 Sonnet decider, 2026-05-14 표현 통일)

substantive 다중 결정 시 ADR-019 (CFP-59) decider protocol 적용. Claude 가 Codex 의견 + 자체 판단으로 합성 결정. 본 repo 의 도메인 ADR 작성 시에도 동일. "Sonnet decider" 프레임워크 호출은 금지 — 메모리 [feedback_phase_codex_review_loop](../../../../../Users/mccho/.claude/projects/c--workspace-mclayer-mctrader-hub/memory/feedback_phase_codex_review_loop.md) 정합.

## codeforge 의무 사용 (CFP-96 Phase 6a, ADR-027)

mctrader-hub = codeforge plugin family 의 첫 비-dogfood consumer (debut). 본 Phase 6a 진입 시점 (2026-05-05) 부터 codeforge protocol 의무 적용.

### 의존 plugin (11개) — `/plugins install` 등록 의무

> 버전 메모는 2026-05-16 `codeforge upgrade` 세션 기준 (직전 반영 = codeforge 5.23.0). marketplace.json ↔ source plugin.json byte-identical (drift 0). cache content == source HEAD (line-ending 차 제외, ADR-063 atomic invariant PASS).

```
codeforge@mclayer               # 5.75.0 — CFP-743 upgrade CLI(scripts/codeforge-upgrade.{sh,ps1})+UpgradeAgent(ADR-076 declarative 9-area reconcile); CFP-707 ADR-038 Amd4 TodoWrite 4-marker swap(⬜ pending/⏳ in_progress/✅ done/🔄 FIX 검출 lane); CFP-702 ADR-027 Amd3 §7 D4 `# BEGIN/END wrapper-managed` marker + wrapper-managed-block.yml blocking-on-pr CI; CFP-660 consumer workflow version-drift detection; ADR-053 hook SSOT = plugin-root hooks/hooks.json (settings.json fallback deprecated)
codeforge-requirements@mclayer  # 0.6.0 — CFP-510 RequirementsPL divergence 4 영역(3 semantic + 1 fact-check) + PL fact marker 5종. Wire: codeforge >= 5.24.0 의무
codeforge-design@mclayer        # 0.12.0 — design-output-v2 v2.3(spec_invariant_measurement_required); CFP-582 ArchitectPL Blanket Adversarial Debate Trigger; CFP-597 ArchitectAgent §5.7 marketplace-sync self-check(ADR-063 Amd1); CFP-528 ADR-068 Amd1 empirical-source annotation
codeforge-develop@mclayer       # 0.7.0 — CFP-507 DeveloperPL Phase 2 PR body composition(`## Lane evidence` 1회 inject·7-row); CFP-609 자율 병렬 결정 tree(parallel-dispatch-protocol-v1)
codeforge-test@mclayer          # 1.1.2 (REVIVED — ADR-055/CFP-367) — review-verdict-v4 sibling sync; IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가)
codeforge-review@mclayer        # 1.6.0 — review-verdict v4 cutover(v3 Archived) + marketplace_sync_declared field(ADR-063 Amd1); CFP-582 debate-protocol-v1 v1.2
codeforge-pmo@mclayer           # 0.1.3 — GitOpsAgent §3.5 Epic scope intersection + §3.6 marketplace-sync proactive PR dispatch(ADR-063 Amd1); ADR-045 Amd5 retro Cross-Story pattern ≥2 ADR trigger
github@claude-plugins-official
codex@openai-codex
superpowers@claude-plugins-official
claude-md-management@claude-plugins-official
```

### Adversarial Debate Protocol auto-trigger (CFP-391/411 — debate-protocol-v1)

ADR-059 lane-agnostic debate protocol + ADR-044 Amendment 1 `auto_on_divergence` dispatch mode (codeforge 5.23.0, codeforge-review 1.3.0, codeforge-requirements 0.5.1):

- **DesignReview lane**: review-verdict v4 `findings[].anchor_id` 기반 worker divergence 감지 시 자동 multi-round debate 진입 (min 3 / max 5 / soft default 4 rounds)
- **Requirements lane**: RequirementsPLAgent §1~§6 완료 후 Codex proactive check (touchpoint #4) 가 semantic divergence (AC 의미 차이 / Edge Case 누락 / Why 해석 mismatch 중 1+ hit) 감지 시 동일 debate 진입
- **Anchor 재발 escalation**: 같은 `anchor_id` 가 Story §9 에서 2회 이상 발견되면 즉시 `AskUserQuestion` escalation (ADR-059 §결정 4)
- **Token 비용 인지**: divergence 미검출 시 single-shot 유지 — 새 동작은 superset, backward-compat
- **FIX 통합**: ArchitectAgent re-run prompt 에 transcript 자동 주입, Story §9 inline append + §10 FIX Ledger `debate_artifact_ref` field

### 도메인 ADR 작성 schema (CFP-387/ADR-058 — codeforge-design 0.8.0)

본 repo `docs/adr/ADR-NN-*.md` 신규 작성 시 frontmatter + body schema:

- **frontmatter `is_transitional: true | false`** 의무 (미선언 default = `true` 안전망 추정, ADR-058 §결정 4)
- **`## 해소 기준` 섹션** 의무 (`## 결과` 직후, `## 다이어그램 (선택)` 직전):
  - `is_transitional: true` → 측정성 3-tuple (metric / who / how) 정량 명시 의무
  - `is_transitional: false` → `N/A — permanent policy` 1줄
- **모달 어휘 금지**: "충분히 안정화되면" / "임시로" / "한시적" / "until further notice"
- **보안 ADR default presumption** = `is_transitional: false` (ADR-058 §결정 7)
- **Amendment 시 `sunset_justification`** 의무 (ratchet 차단, ADR-058 §결정 5)

### codeforge 업그레이드 프로세스

codeforge plugin upgrade 시 **반드시** 각 plugin CHANGELOG 를 읽고 consumer-facing 변경 사항을 이 파일에 반영한다. 확인 순서:

1. `plugin-codeforge/CHANGELOG.md` — core (Orchestrator 지침 / ADR / contract 변경)
2. lane plugin CHANGELOGs — pmo / requirements / design / develop / test / review
3. **Breaking change** → Story workflow / plugin list / phase 순서 즉시 갱신
4. **Deprecation** → plugin list 주석 업데이트 + Story phase 에서 제거
5. **Deprecated agent 잔존 참조 감사** → `grep -r "DeprecatedAgentName" . --include="*.md" --include="*.sh" -l | grep -v "CHANGELOG\|retro"` 로 active spawn 참조 확인 후 주석/설정 갱신
6. **6-repo 동기화** → 5 impl repo `.claude/_overlay/CLAUDE.md` plugin 버전 메모 동기화 (mctrader-hub §plugin 목록 기준 — MCT-129 패턴)

#### 반영 로그

- **2026-05-16** — codeforge 5.23.0 → **5.75.0** (+6 lane plugin) 일괄 반영. drift 0 (marketplace ↔ source byte-identical, cache content == HEAD). consumer-facing 핵심:
  - **CFP-743 / ADR-076 (5.75.0)** — 신규 canonical upgrade flow: `scripts/codeforge-upgrade.{sh,ps1}` thin dispatcher + `UpgradeAgent` (Orchestrator one-shot subagent, 9-area declarative reconcile + snapshot lifecycle + 사후 sanity 3종 + event log). **현재 plugin-internal (dogfood) only — `consumer-scripts.manifest` 미등록 → mctrader-hub 등 consumer 는 아직 본 manual 프로세스 유지.** consumer-distribution 완비 시 본 §업그레이드 프로세스를 UpgradeAgent flow 로 대체 예정 (escalation 후보).
  - **CFP-707 / ADR-038 Amendment 4 (5.69.0)** — TodoWrite 4-marker vocabulary swap: `⬜` pending / `⏳` in_progress / `✅` completed / `🔄` FIX 검출 lane. 기존 `⏳ pending` · `❌ FIX 원인 lane` 표기 폐기. Story §10 / 진행 시각화 표기 직접 영향 (이미 활성).
  - **CFP-702 / ADR-027 Amendment 3 §결정 7 D4 (5.74.0)** — consumer customization 보존 `# BEGIN wrapper-managed` / `# END wrapper-managed` marker + `wrapper-managed-block.yml` **blocking-on-pr CI** + `migrate-existing-customization.sh` (retroactive idempotent wrap, `--dry-run`). mctrader-hub customization 영역 marker wrap 점검 권고.
  - **CFP-660 (5.60.0)** — consumer workflow version-drift detection (`workflow-version-drift` + `check-codeforge-version-drift.sh`).
  - **ADR-053 (5.22.x)** — hook 등록 SSOT = plugin-root `hooks/hooks.json` (first-class). `.claude/settings.json` hook fallback **deprecated** (§Settings hook 등록 참조 — SessionStart polyglot wrapper 정상 동작 확인됨, 구조 전환은 별 점검).
  - lane: requirements 0.6.0 (divergence 4 영역) / design 0.12.0 (design-output-v2 v2.3) / develop 0.7.0 (DeveloperPL PR body convention) / test 1.1.2 (review-verdict-v4 sync) / review 1.6.0 (v4 cutover, v3 Archived) / pmo 0.1.3 (GitOpsAgent §3.5/§3.6 marketplace-sync). lane 신규 consumer-breaking 0.
  - **6-repo 동기화 (step 6) 미수행** — 5 sister repo `_overlay/CLAUDE.md` 버전 메모 sync 는 별 작업 (MCT-129 패턴, 후속 권고).

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
- Phase: 요구사항 → 설계 → 설계-리뷰 → 구현 → 구현-리뷰 → CI 테스트 (`gh pr checks` polling, ADR-048) → 통합테스트 (IntegrationTestAgent, ADR-055, §8.6, test-verdict-v2.2, Epic-level CFP-371/CFP-373) → 보안-테스트 → 완료 → **PMO 회고 (의무)**
- Claude decider 의무 (ADR-022) — 모든 design / scope 결정점에서 Claude 가 Codex 의견 + 자체 판단 합성 필수

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

### Agent model tier (ADR-042 Amendments 2/5 — 2026-05-10/12)

InfraEngineerAgent·QADeveloperAgent·DataEngineerAgent = `claude-haiku-4-5` (기계적 패턴 실행 카테고리).
CodebaseMapperAgent·RefactorAgent·ChangeImpactAgent·DeveloperPLAgent = `claude-sonnet-4-6` selective rollback 대상 (ADR-057 Amendment 3 / ADR-042 Amendment 5, CFP-448 — 4 agent 실측 정합).
FeasibilityAgent·ContinuityAgent = `claude-opus-4-7` 유지 (deep reasoning / cross-Story continuity).
나머지 모든 agent = Sonnet 이상, 단 lane PL 중 Opus 지정 agent 는 해당 plugin agent frontmatter 가 SSOT (ADR-042 §결정-1 3-tier 매트릭스).
롤백 트리거: 해당 agent 의 ESCALATE rate 급증 또는 품질 저하 시 ADR-042 governance re-audit (ADR-042 §결정-5/6).

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

## Compactor 운영 + 관측

- 컨테이너: `mctrader-compactor` (mctrader-data compose service), `mem_limit: 32G`, `memswap_limit: 32G` (swap disabled)
- 핵심 env: `MALLOC_TRIM_THRESHOLD_=131072` (glibc free 후 OS 반환), `ARROW_DEFAULT_MEMORY_POOL=system` (PyArrow jemalloc → glibc), `MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS=300`, `MCTRADER_COMPACTOR_METRICS_PORT=8080`
- mem_limit 초과 시 `restart: unless-stopped` — `compactor_process_rss_bytes` metric 으로 즉시 감지
- `/metrics`: `http://mctrader-compactor:8080/metrics` (host: `localhost:8080`), Prometheus job `mctrader-data-compactor`, Grafana `mctrader/Compactor Memory & Throughput` (uid `mctrader-compactor`)
- 5 metric (MCT-134 Phase 1): `compactor_process_rss_bytes` / `compactor_pyarrow_total_allocated_bytes` / `compactor_python_gc_gen_count{generation}` / `compactor_tier_pending_segments{tier}` / `compactor_writer_open_count{tier}`
- SSOT runbook: [docs/runbooks/compactor-mct132-phase1-land.md](../../docs/runbooks/compactor-mct132-phase1-land.md), [docs/runbooks/compactor-baseline.md](../../docs/runbooks/compactor-baseline.md)
- tracemalloc collector: `tools/compactor-tracemalloc.py` (컨테이너 내 `/tmp/compactor_capture.py` 로 cp — shadowing 회피)

## ADR Index

본 overlay 의 ADR Index 섹션 — 신규 ADR 추가 시 entry append 의무 (Story `planned_claude_md_sections` 박제 trail). 기존 ADR (ADR-001 ~ ADR-026) entry 는 별 Story (ADR Index housekeeping) scope — 본 섹션은 본 Story 진입 시점 (MCT-149, 2026-05-12) 의 ADR-027 entry 만 신규 추가.

- **ADR-027** — Cold Tier Object Storage on NAS MinIO. status=Accepted (2026-05-12, MCT-149). EPIC-cold-tier-nas-minio Stage 1 종료 governance. ADR-017 successor (cold tier extension), ADR-016 complement. D1~D11 + MCT-148 5 PoC PASS evidence transcribe. Stage 2 (MCT-150~155) 진입 자격 박제. [docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md](../../docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md)

## 인프라 — Cold Tier (EPIC-cold-tier-nas-minio + Stage 3 wiring)

`mctrader-data` 의 cold tier (L2/L3 compacted Parquet) 를 외부 Synology NAS Container Manager 위 MinIO 컨테이너로 이관 (ADR-027). 호스트 disk 용량 압박 해소 + ADR-017 zero-loss invariant (collector hot path / WAL / L1 = local 유지) 보존.

### Historical milestone summary

- **Stage 1** (MCT-147~149, CLOSED 2026-05-12) — NAS deploy + 5 PoC PASS + ADR-027 publish. SSOT: [ADR-027](../../docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md), [docs/runbooks/nas-minio-secret-rotation.md](../../docs/runbooks/nas-minio-secret-rotation.md)
- **Stage 2** (MCT-150~155, CLOSED 2026-05-13 mctrader-hub#277) — production-grade primitive: NAS uploader + DualWriter + InvariantHarness + SOPRunner + BackfillOrchestrator. SSOT: 각 Story §11 + retros/
- **Stage 3 wiring** (EPIC-cold-tier-stage-3-wiring, IN_PROGRESS) — Stage 2 후 NAS bucket 실측에서 hot pipeline NAS wiring 부재 발견. MCT-156 ✅ LAND 2026-05-13 (compactor NAS wiring + DualWriter inject). MCT-157/158/159 PROPOSED
- **EPIC-compactor-operations** (MCT-160~162, IN_PROGRESS) — MCT-156 deploy 직후 5중 차단 cycle (upbit L1 zero / L2 cadence / L1 backlog 79k / orderbookdepth schema / L2 OOM) 해소. MCT-162 ✅ LAND 2026-05-13 (channel parity + orderbookdepth schema)
- **Disk 압박 sequential**: MCT-159 (L2/L3 backlog 8.85 GiB) → MCT-160 (L1 backlog ~115 GiB ~62%) → MCT-161 (NAS versioning + replication 정책)

### Stage 1 운영 정책 (ADR-027 §Decision SSOT, 활성)

- **endpoint protocol**: Stage 1/2 = HTTP (LAN 내부망 only, NAS 방화벽 port 9000/9001 = mctrader 호스트 IP only + `.env` 0600 + 90일 rotation). Stage 3+ = TLS 재검토 (사용자 confirm 의무)
- **bucket layout**: 단일 `mctrader-market` + Hive prefix (`schema_version/exchange/node/tier/date/[hour]`)
- **credential rotation cadence**: 90일 (NAS 방화벽 룰 audit 동시 의무, `docs/runbooks/nas-minio-secret-rotation.md`)
- **Hot path 무영향 invariant** (ADR-017 정합): collector WAL + L1 ParquetWriter = local volume 유지. NAS unreachable → compactor retry queue + backlog alert. WAL/L1/hot path 무영향. Alert metric: `cold_writer_backlog_segments` + `cold_writer_retry_count_total`

### Stage 3 운영 가이드 (현재 활성)

#### DualWriter inject pattern (`NAS_MINIO_ENDPOINT` env 분기)

`mctrader-data/src/mctrader_data/cli.py` 의 `compact_cmd`:
- env set → `NASUploader` + `RetryQueue` + `DualWriter` build → `CompactorRunner(dual_writer=...)` inject → L2/L3 자동 dual-write
- env 부재 → `dual_writer=None` → **degraded mode** (NAS PUT skip, local Parquet only — test/local dev 호환)

운영 의무: `NAS_MINIO_ENDPOINT` + `NAS_MINIO_ACCESS_KEY` + `NAS_MINIO_SECRET_KEY` + `NAS_MINIO_BUCKET` 4 env 모두 set (`.env.example` placeholder 정합).

#### `DualWriter.write()` API SSOT (MCT-151 land)

```python
DualWriter.write(*, local_path, nas_key, data, sha256) -> DualWriteResult
# DualWriteResult.status ∈ {"committed", "local_only", "hard_floor_blocked"}
```

- `committed` = local + NAS 양쪽 commit (정상)
- `local_only` = NAS unreachable → retry_queue enqueue 자동 (log info)
- `hard_floor_blocked` = retry queue hard floor (1000 seg / 10GB) → log error + Prometheus alert + SOP MANUAL_GATE escalation

#### Channel parity 정책 (ADR-027 D4 amendment, MCT-162 land)

- 모든 collector emit channel = L1/L2/L3 layer parity 의무
- unsupported channel = `NotImplementedError` raise + `mctrader_compactor_unsupported_channel_total{channel}` Counter +1 emit (**silent skip 금지**)
- silent skip catastrophe (MCT-156 deploy 후 48,629 sealed silent backlog) 재발 방지

#### orderbookdepth schema (ADR-009 §D11.9, MCT-162 land)

- schema_version = `orderbook_depth.v1`, 11 column flat row (per-frame `changes[]` flatten, qty=0 = level delete)
- column list: `ts_utc / received_at / exchange / symbol / side / price / quantity / raw_json / node_id / collector_run_id / ingest_seq`
- **`raw_json` column dtype = `pa.large_string()` 의무** (LargeUtf8 i64 offset, L2 concat 누적 i32 4GB overflow 차단)

#### 신규 channel 추가 3-step 절차 (의무)

1. **ADR-009 §D11.X amendment** — schema 정의 (column list + dtype + invariant + §D2.6 matrix row)
2. **L1Compactor**:
   - `_CHANNEL_SCHEMA_VERSION[<channel>] = "<schema>.v1"` allowlist entry
   - `_<channel>_dicts_to_arrow(rows) -> pa.Table` converter
   - `_arrow_schema_for_channel(channel)` + `_convert_to_arrow(channel, rows)` 분기
3. **integration test** — `tests/integration/test_l1_compactor_<channel>_parity.py` (5종 min: converter PASS + fail-fast + Prometheus emit + schema invariant + large_string verify if applicable)

#### Mixed layout reader 책임 경계 (ADR-009 §D2.1 + §D14 fallback)

NAS bucket 에 legacy layout (MCT-153 backfill, hour 부재) + 신규 schema (MCT-156+, `hour=HH/node=MERGED/`) mixed 공존. ADR-009 fallback (`node=` absent → `DEFAULT`, `tier=` absent → `L1`) 으로 자연 양립. legacy 객체 retroactive 재구조 비권고. ADR-027 D9 amendment 정합.

#### Legacy MinioUploader deprecation

`mctrader-data/src/mctrader_data/compactor/minio_uploader.py` = MCT-156 Phase 2 production 호출처 0 + `.. deprecated:: MCT-156` 마킹. 모듈 file 삭제는 post-EPIC-cold-tier-stage-3-wiring closure 후속 Epic.

### Stage 3 release gate (MCT-158 owner, EPIC CLOSED gate)

6h smoke test 의 production NAS bucket 실측 evidence pack:
- `tier=L2/.../hour=HH/node=MERGED/` 출현 verify
- `tier=L3/.../node=MERGED/` 출현 verify
- `mctrader_dual_write_result_total{status="committed", tier="L2|L3"}` Counter 증가
- retry queue backlog = 0 baseline (hard_floor_blocked = 0)

### Post-Epic refactor surface (검토 후보)

- **sha256 dup hashing** — `compactor/runner.py._dispatch_dual_write` + `DualWriter.write()` 양쪽 identical input 2회 hash. refactor = `precomputed_sha256` param 추가
- **tmp_dw double-write** — DualWriter local commit + NAS PUT 디스크 IO 2회. refactor = in-memory bytes hand-off (현재 cross-process safety 위해 tmp 경유)
- legacy `minio_uploader.py` module file 삭제 (호출처 production 0)
- mctrader-data main 의 pre-existing 9 test failure 해소 (PMOAgent 누적 patterns 1건)
- ADR-XXX-post-cutover-wiring-gap-prevention 발의 (누적 2회 pattern 박제, MCT-156 deploy gap)

### 데이터 헬스 프레임워크 (MCT-165, 2026-05-14)

`mctrader-data#54` (PR mct-165-phase-2) — 4-layer data accumulation health verification CLI.

**4 layer**: volume / gap / file_count / lag
**CLI**: `mctrader-data health-check --target collector --window 5d --start-date 2026-05-09 --output markdown`
**Exit code**: 0=ALL PASS, 1=any FAIL, 2=tool error (INV-4)
**Rolling baseline**: NotImplementedError (ADR-028 Reserved — 후속 PR)

**실제 storage layout** (reconciled 2026-05-14):
```
MCTRADER_DATA_ROOT/market/orderbookdepth/schema_version=orderbook_depth.v1/
  tier={L1|L2|L3}/exchange={exchange}/symbol={symbol}/
  date={YYYY-MM-DD}/[hour={H}/][node={node}/]part-*.parquet
WAL: MCTRADER_DATA_ROOT/wal/{exchange}/orderbookdepth/{symbol}/{YYYY-MM-DD}/segment-*.ndjson
```

**D+5 verify 결과 (2026-05-14)**:
- V1 volume: FAIL (5d expected 기준) / PASS (4d 기준 재추산, 실측 4d=2.973 GiB)
- V2 upbit L1: 잔존 YES → **MCT-164 trigger**
- V3 per-sym: median 35 MiB / p10 14 MiB / p90 110 MiB (50 sym × 4d, L1 bithumb)

**D+7 (2026-05-16)**: 5d 완전 window V1 재검증 예정. 별 세션.

**Cross-ref**: MCT-165 Story / ADR-028 Reserved / ADR-009 §D12 / MCT-164 (upbit L1 root cause placeholder).

---

## Collector channel allowlist 규약 (MCT-164, 2026-05-14)

**Root cause 확정 (MCT-164 §10)**: `collector.py _build_ingesters()` 에서 `exchange == "bithumb"` 조건으로
`orderbookdepth` ingester 를 bithumb 전용으로 제한. upbit = orderbooksnapshot WAL 만 생성.

```python
# collector.py _build_ingesters() 현재 상태 (MCT-164 확정 root cause — MCT-166 fix 대상)
if self._include_orderbook and self._exchange == "bithumb":
    ingesters["orderbookdepth"] = WalIngester(channel="orderbookdepth", ...)
```

- **bithumb**: orderbookdepth + orderbooksnapshot + transaction WAL
- **upbit**: orderbooksnapshot + transaction WAL 만 (orderbookdepth 없음 → L1 = 0)
- **신규 exchange 추가**: channel allowlist + WS adapter event 지원 여부 동시 확인 의무

**channel matrix SSOT**: `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md`

## Ingester partition key 규약 (MCT-164, 2026-05-14)

`WalIngester(channel=<channel>)` 파라미터 = WAL path `<channel>` 디렉터리 결정.
collector emit channel = WAL partition key = L1 output channel 디렉터리 (1:1 정합).

## Compactor source 분기 규약 (MCT-164, ADR-017 Amendment 2)

L1 compactor `_CHANNEL_SCHEMA_VERSION` allowlist: transaction / orderbooksnapshot / orderbookdepth.
exchange 별 분기 없음. 미지원 channel = NotImplementedError raise (silent skip 금지 — ADR-027 Amendment 1).
channel 추가 시 allowlist + `_convert_to_arrow` + `_arrow_schema_for_channel` 동시 갱신 의무.

## WAL path layout (MCT-164)

```
<root>/wal/<exchange>/<channel>/<symbol>/<date>/
    segment-<ts>-<node_id>.ndjson
    segment-<ts>-<node_id>.ndjson.sealed
    segment-<ts>-<node_id>.ndjson.sealed.compacted
```

**WAL freeze 도구** (forward-only loss 즉시 차단):
```bash
python scripts/wal_freeze.py --root <data_root> --exchange upbit --execute --verify
```

## exchange-channel-matrix cross-ref (MCT-164, ADR-017 Amendment 2)

- `docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md` — SSOT (hypothesis → confirmed 2026-05-14)
- MCT-166 fix Story = 본 matrix "결함" 행 fix 의무 (INV-5 인과 chain 강제)
- MCT-173 backfill Result 추가 (2026-05-14): frozen WAL → L1 historical materialization PASS

## backfill mode (MCT-173, 2026-05-14)

`mctrader-data compact --backfill`: frozen WAL sealed segments → L1 parquet 일괄 생성.

```bash
# Production (docker exec):
docker exec mctrader-compactor python -c "
from pathlib import Path
from mctrader_data.compactor.runner import run_backfill
result = run_backfill(root=Path('/var/lib/mctrader/data'), exchange='upbit', tier='L1', channel='orderbooksnapshot')
print(f'processed={result.segments_processed} l1={result.l1_parquets_created}')
"
```

- INV-2: `.compacted` sentinel idempotency (재실행 safe)
- INV-5 verify gate: V2=0 AND partial loss Fail=0 → RETRO 허용
- Phase 2.4 결과: L1 rows=106,883,580, V2=0 PASS, partial loss Fail=0
