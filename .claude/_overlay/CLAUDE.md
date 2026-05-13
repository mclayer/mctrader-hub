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
codeforge@mclayer               # 5.23.0 — CFP-423 Python script-writing convention; CFP-436 marketplace/plugin.json atomic invariant; CFP-455 evidence-check-registry v1.1 current_tier; CFP-445/449 decision-principle lint; CFP-448/490 selective Sonnet rollback + lane-evidence guard
codeforge-requirements@mclayer  # 0.5.1 — CFP-411 codex-proactive-check worker + semantic divergence 3 criteria; CFP-448 ChangeImpactAgent Opus→Sonnet rollback. Wire: codeforge >= 5.23.0 의무
codeforge-design@mclayer        # 0.8.0 — CFP-387 ADR template is_transitional + 해소 기준 schema; CFP-448 CodebaseMapperAgent/RefactorAgent Opus→Sonnet rollback + mandate boundary text
codeforge-develop@mclayer       # 0.5.1 — CFP-448 DeveloperPLAgent Opus→Sonnet rollback (ADR-042 Amendment 5 §결정 1 (b)); CFP-317 PR pre-flight guard 유지
codeforge-test@mclayer          # 1.1.1 (REVIVED — ADR-055/CFP-367 + Amendment 2/CFP-371/CFP-373) — test-verdict-v2.2 story_keys[] + attribution_confidence; IntegrationTestAgent(Sonnet) active; TestAgent/StatefulTestAgent deprecated (spawn 불가)
codeforge-review@mclayer        # 1.3.0 — CFP-391 review-pl-base §3.0~§3.3 debate-protocol-v1 dispatch SOP + review-verdict v4.0→v4.1 (findings[].anchor_id optional field)
codeforge-pmo@mclayer           # 0.1.0
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

## Compactor 운영 (MCT-132 Phase 1)

- 컨테이너: `mctrader-compactor` (mctrader-data compose service)
- `mem_limit: 32G` (호스트 62.73GiB 의 절반), `memswap_limit: 32G` (swap disabled)
- 환경변수:
  - `MALLOC_TRIM_THRESHOLD_=131072` (glibc free 후 OS 반환 trigger)
  - `ARROW_DEFAULT_MEMORY_POOL=system` (PyArrow jemalloc → glibc 전환)
  - `MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS=300` (runner 가 5분 주기 `gc.collect()` 호출)
  - `MCTRADER_COMPACTOR_METRICS_PORT=8080`
- mem_limit 초과 시 `restart: unless-stopped` — A2 metric (`compactor_process_rss_bytes`) 으로 즉시 감지
- L1/L2/L3 ParquetWriter `with` context manager + tmp 파일 cleanup on exception

## Compactor 관측 (MCT-134 Phase 1)

- `/metrics`: `http://mctrader-compactor:8080/metrics` (host expose: `localhost:8080`)
- Prometheus scrape job: `mctrader-data-compactor` (`monitoring/prometheus.yml`)
- Grafana dashboard: `mctrader/Compactor Memory & Throughput` (uid: `mctrader-compactor`)
- 5 metric:
  - `compactor_process_rss_bytes` — process RSS (procfs primary, resource/ctypes fallback)
  - `compactor_pyarrow_total_allocated_bytes` — PyArrow default memory pool
  - `compactor_python_gc_gen_count{generation="0|1|2"}` — Python GC generation counts
  - `compactor_tier_pending_segments{tier="L1|L2|L3"}` — L1: sealed segment count, L2/L3: elapsed/interval (epoch 0 인 경우 0)
  - `compactor_writer_open_count{tier="L1|L2|L3"}` — paired inc/dec around ParquetWriter
- Phase 1 land report: `docs/runbooks/compactor-mct132-phase1-land.md`
- Baseline capture runbook: `docs/runbooks/compactor-baseline.md`
- tracemalloc collector: `tools/compactor-tracemalloc.py` (컨테이너 내 `/tmp/compactor_capture.py` 로 cp — shadowing 회피)

## ADR Index

본 overlay 의 ADR Index 섹션 — 신규 ADR 추가 시 entry append 의무 (Story `planned_claude_md_sections` 박제 trail). 기존 ADR (ADR-001 ~ ADR-026) entry 는 별 Story (ADR Index housekeeping) scope — 본 섹션은 본 Story 진입 시점 (MCT-149, 2026-05-12) 의 ADR-027 entry 만 신규 추가.

- **ADR-027** — Cold Tier Object Storage on NAS MinIO. status=Accepted (2026-05-12, MCT-149). EPIC-cold-tier-nas-minio Stage 1 종료 governance. ADR-017 successor (cold tier extension), ADR-016 complement. D1~D11 + MCT-148 5 PoC PASS evidence transcribe. Stage 2 (MCT-150~155) 진입 자격 박제. [docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md](../../docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md)

## 인프라 — Cold Tier (MCT-147 ~ MCT-155 EPIC-cold-tier-nas-minio)

`mctrader-data` 의 cold tier (L2/L3 compacted Parquet) 를 외부 Synology NAS Container Manager 위 MinIO 컨테이너로 이관 (ADR-027). 호스트 disk 용량 압박 해소 + ADR-017 zero-loss invariant (collector hot path / WAL / L1 = local 유지) 보존.

### Stage 1 종료 (MCT-149, 2026-05-12)

- **MCT-147** (MERGED, `mctrader-hub#246` 409d076) — NAS MinIO 컨테이너 deploy + `mctrader-market` bucket 초기화 + 90일 credential rotation runbook + 4중 mitigation (.env 0600 / .gitignore / NAS 방화벽 ACL / IAM 분리).
- **MCT-148** (MERGED, `mctrader-data#40` d3e2af5) — 5 PoC PASS evidence (T1 HTTP health 2/2 / T2 latency baseline 4/4 / T3 large PUT 50MB sha256 IDENTICAL 3/3 / T4 restart idempotency recovery_ms=30.56 / T5 partial visibility atomic_invariant=true). pytest 10 PASSED in 107.76s.
- **MCT-149** (본 Story) — ADR-027 본문 publish + Stage 1 종료 governance.

### Stage 1 운영 정책 (ADR-027 §Decision 박제)

- **endpoint protocol (D2 amend)**: **Stage 1 = HTTP** (LAN 내부망 only, NAS 방화벽 port 9000/9001 = mctrader 호스트 IP only + `.env` 0600 + 90일 rotation). **Stage 2 = TLS 재검토** (MCT-155 진입 시 사용자 confirm 의무).
- **bucket layout (D1)**: 단일 `mctrader-market` + Hive prefix (`schema_version/exchange/node/tier/date`).
- **credential rotation cadence (D2)**: 90일 (`docs/runbooks/nas-minio-secret-rotation.md`).
- **NAS 방화벽 룰 audit cadence (R10 신규)**: 90일 rotation 시점 정기 audit 의무.

### Stage 2 진입 (MCT-150 ~ MCT-155, 본 ADR merge 후 brainstorm Phase 0 재실행 권고)

| Story | scope |
|-------|-------|
| MCT-150 | `minio_uploader.py` hardening (retry queue + Prometheus metrics + alert) |
| MCT-151 | dual-write atomic primitives + 3종 invariant 검증 harness (sha256 + object count + parquet row count) |
| MCT-152 | dual-write window 운영 (2-4주, drift 측정) |
| MCT-153 | backfill (historic L2/L3 cold tier asset 이관) |
| MCT-154 | reader endpoint cutover + engine smoke test (read-through LRU/TTL cache) |
| MCT-155 | local GC (7일 grace + dry-run) + secret rotation 첫 cycle + Stage 2 TLS 재검토 사용자 confirm |

### Hot path 무영향 invariant (D5, ADR-017 정합)

- **collector WAL + L1 ParquetWriter** = local volume 유지 (ADR-017 zero-loss invariant).
- **NAS unreachable failure mode** = compactor retry queue + backlog alert. WAL / L1 / hot path 무영향 (D5 박제).
- **alert metric** (MCT-150 산출물): `cold_writer_backlog_segments` + `cold_writer_retry_count_total` (Prometheus) + Grafana dashboard `mctrader/Cold Writer Health`.

### Stage 3 wiring (EPIC-cold-tier-stage-3-wiring, MCT-156 ~ MCT-158, post-Stage 2 follow-up)

Stage 2 EPIC CLOSED 2026-05-13 (mctrader-hub#277) 후 사용자 NAS bucket 실측에서 발견된 핵심 gap — hot pipeline (compactor) NAS wiring 부재 해소. bucket `mctrader-market` 실측 결과 `tier=L3/` prefix 0개 + `tier=L2/` 안 `hour=HH/` partition 0개 = Stage 2 production-grade primitive (NAS+DualWriter+InvariantHarness+SOPRunner+BackfillOrchestrator) 가 완성됐음에도 hot pipeline 자체가 NAS endpoint 안 가는 환경에서 운영 중이었음.

**Stage 3 milestone progression** (post-MCT-156 LAND + MCT-159 spawn):

| Story | scope | 상태 |
|-------|-------|-----|
| **MCT-156** ✅ | compactor NAS wiring + L2/L3 DualWriter injection (entrypoint vertical slice) | **COMPLETED 2026-05-13** (#279 Phase 1 + mctrader-data#47 Phase 2 + #280 hub Phase 2) |
| MCT-157 | Prometheus layout label 분리 + observability (legacy_node_default vs new_node_merged) | PROPOSED |
| MCT-158 | release gate smoke test + cutover runbook + EPIC CLOSED gate (6h bucket prefix 출현 verify) | PROPOSED (depends_on: 156, 157) |
| **MCT-159** | **L2/L3 cold tier backlog NAS migration (~8.85 GiB / 7118 file, channel parametrize + hour key amend)** | **PROPOSED 2026-05-13** (sibling, parallel_after_156) |

milestone 1/4 = 25% (post-MCT-156 LAND, MCT-159 sibling 추가 후).

### Stage 3 backlog migration follow-up (MCT-159, post-MCT-156 wiring)

MCT-156 Phase 2 LAND (`mctrader-data#47` dff8aa5) 후 compactor 09:22 restart → 09:24 부터 NAS dual-write 정상화. **그러나** wiring _이전_ 로컬 누적 L2/L3 backlog (8.85 GiB / 7118 file, 신규 schema `tier=L{2,3}/.../date=D/hour=HH/node=MERGED/`) 는 자연 cadence 적용 외 영역 (orderbookdepth NotImplementedError 영구 fail → L2 자연 trigger ETA 9.2h 무효, RETRO-MCT-156 §13.4 박제). MCT-159 = MCT-153 `BackfillOrchestrator` 의 2 amendment (channel parametrize + hour key 처리) 후 재호출하여 LAND-이전 backlog 강제 이관.

**Sequential 3-step disk 압박 해소 박제**:

| Step | Story | Scope | Disk 추정 |
|------|-------|-------|----------|
| 1 | **MCT-159 (active)** | L2/L3 cold tier 8.85 GiB / 7118 file | ~4.8% |
| 2 | MCT-160 (reserve, EPIC-compactor-operations) | compactor L1 backlog cleanup (orderbookdepth FIX + L2 offset overflow FIX + MCT-153 손실 retrofit) | ~62% (L1 ~115 GiB) |
| 3 | MCT-161 (reserve, EPIC-compactor-operations) | NAS bucket versioning 활성화 + replication 정책 + 손실 재발 방지 | 0% (정책) |

**MCT-159 만으로 disk 압박 즉시 해소 미달성 (4.8% only)** — MCT-160/MCT-161 sequential 의무 박제 (Story §1 R3 first surface).

### Stage 3 운영 가이드 (MCT-156 산출물 기반)

#### DualWriter inject pattern (NAS_MINIO_ENDPOINT env 부재 시 degraded mode)

`mctrader-data/src/mctrader_data/cli.py` 의 `compact_cmd` 가 `NAS_MINIO_ENDPOINT` env 분기:

- env set → `NASUploader` + `RetryQueue` + `DualWriter` lazy build 후 `CompactorRunner(dual_writer=...)` inject → L2/L3 compaction 산출물 자동 dual-write
- env 부재 → `dual_writer=None` 으로 `CompactorRunner` build → **degraded mode** (NAS PUT skip, local Parquet only — test/local dev 호환 경로)

운영 환경 의무: `NAS_MINIO_ENDPOINT` + `NAS_MINIO_ACCESS_KEY` + `NAS_MINIO_SECRET_KEY` + `NAS_MINIO_BUCKET` 4 env 모두 set (`.env.example` placeholder 정합).

#### `DualWriter.write()` API 정합 (signature SSOT)

Change Plan 초안의 `dual_writer.put(local_path, nas_key, sha256)` 명세는 **추정 signature** (Codex Phase 0 brainstorm 시점 박제). 실제 MCT-151 land API:

```python
DualWriter.write(*, local_path, nas_key, data, sha256) -> DualWriteResult
# DualWriteResult.status ∈ {"committed", "local_only", "hard_floor_blocked"}
```

`_dispatch_dual_write` helper 안에서 `parquet_path.read_bytes()` 로 payload 조달 후 호출. status 3종 caller contract:
- `committed` = 정상 (local + NAS 양쪽 commit)
- `local_only` = NAS unreachable → retry_queue enqueue 자동, log info
- `hard_floor_blocked` = retry queue hard floor (1000 seg / 10GB) 도달 → log error + Prometheus alert + SOP MANUAL_GATE escalation

#### Legacy MinioUploader deprecation 박제

`mctrader-data/src/mctrader_data/compactor/minio_uploader.py` = MCT-156 Phase 2 에서 **호출처 production 0** + module docstring `.. deprecated:: MCT-156 (Stage 3 wiring)` 마킹. **모듈 file 자체 삭제는 후속 Epic** (post-EPIC-cold-tier-stage-3-wiring closure).

#### Mixed layout reader 책임 경계 (ADR-009 §D2.1+§D14 fallback 자연 양립)

NAS bucket 에 (a) MCT-153 backfill 산출물 legacy layout (`tier=L2/.../date=D/[node=N/]file.parquet`, hour 부재) + (b) MCT-156 Phase 2 이후 신규 hot pipeline 산출물 신규 schema (`tier=L2/.../date=D/hour=HH/node=MERGED/part-*.parquet`) mixed 공존.

- reader 호환 = ADR-009 §D2.1 (`node=` absent → `node=DEFAULT`) + §D14 (`tier=` absent → `tier=L1`) fallback 박제로 자연 보장
- `scan_*` API partition pruning 양쪽 layout mixed scan 양립
- legacy 객체 retroactive 재구조 비권고 (S6 결정 박제)
- ADR-027 D9 amendment 본문 정합 (MCT-156 Phase 1 LAND)

### Stage 3 release gate (R1 smoke test 의무, MCT-158 owner)

MCT-158 = Stage 3 EPIC CLOSED gate 의무. 6h smoke test 의 production NAS bucket 실측 evidence pack:

- `tier=L2/.../hour=HH/node=MERGED/` 출현 verify
- `tier=L3/.../node=MERGED/` 출현 verify
- `mctrader_dual_write_result_total{status="committed", tier="L2|L3"}` Counter 증가 evidence
- retry queue backlog = 0 baseline (hard_floor_blocked = 0)

### post-Epic refactor 후보 surface (Stage 3 EPIC CLOSED 후 검토)

MCT-156 Phase 2 CodeReviewPL P2 advisory finding 2건 — NFR-1 (< 3000ms) 안에서 흡수, post-Epic refactor 후보로 surface:

- **sha256 dup hashing** — `compactor/runner.py._dispatch_dual_write` + `DualWriter.write()` 내부 NASUploader 양쪽에서 identical input 2회 hash. refactor 후보 = `DualWriter.write()` API 에 `precomputed_sha256` param 추가.
- **tmp_dw double-write** — DualWriter local commit 시 tmp file roundtrip + NASUploader 가 tmp read → MinIO PUT = 디스크 IO 2회. refactor 후보 = in-memory bytes hand-off (현재는 cross-process safety 위해 tmp 경유).

추가 surface:
- legacy `MinioUploader` 모듈 file 삭제 (호출처 production 0, deprecation 마킹 → file 자체 삭제)
- mctrader-data main 의 pre-existing 9 test failure 해소 (별 Story 후보, PMOAgent 누적 patterns 1건)
