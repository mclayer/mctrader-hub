---
story_key: MCT-95
story_issues:
  - repo: mclayer/mctrader-hub
    number: 106
status: phase:완료
---

# MCT-95: Collector HA — Streamlit `00_status` Panel (X6 of MCT-89)

- **Issue**: #106
- **Status**: phase:완료

## 1. 사용자 요구사항 (verbatim)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: mctrader-web measure surface. 부모 Epic = MCT-89. X4 (MCT-93, mctrader-data 0.8.0) 의 status CLI 의 web consumer. Phase 1 spec/plan 의 X6 = `pages/00_status.py` Streamlit page (heartbeat freshness / lag per tier / quarantine count / dedup ratio + 임계 banner).)

## 2. 도메인 해석

X6 = "데이터 순단 0" 의 *web visible surface*. X4 의 CLI exit code 0/1/2 가 web 측 banner 색깔 (green/yellow/red) 로 1:1 매핑. operator 가 dashboard 단일 페이지에서 양 node 의 health 한눈에 확인.

핵심 boundary:
- **read-only**: writer path 영향 0 (X4 와 동일)
- **subprocess 의존**: CLI 가 single source of truth — web 측 threshold 로직 복제 차단
- **passive observation v1**: Slack/email 등 proactive push 는 v2 (Epic decision #14)

## 3. 관련 ADR / Contract

신규 ADR amendment 없음. heartbeat-schema.v1 (X4 amendment 포함) 그대로.

## 4. 외부 contract — 신규 amendment 없음

X6 는 X4 CLI contract 의 consumer — 변경 0.

## 5. 요구사항 확장 해석 (Codex 6-area review fix 반영)

### 5.1 Approach 결정 (F-1 SUGGEST 채택)

Approach A (subprocess + 5s cached adapter) 채택:
- status CLI 가 threshold 로직 owner — duplication 차단
- 5s TTL = heartbeat write interval 과 align
- 동일 thresholds 의 cache hit → subprocess fanout 차단
- "Force refresh" sidebar button → cache clear + `st.rerun()`

Approach B (직접 heartbeat read) 거부 — threshold 로직 web 측 복제 위험.
Approach C (mctrader-data 의 pure compute_status 함수 import) 거부 — X4 cli.py refactor 필요, X6 scope 외.

### 5.2 Auto-refresh (F-2 SUGGEST 채택)

`time.sleep` 거부 — Streamlit session blocking 차단.
`streamlit-autorefresh` 거부 — extra dependency.
Streamlit native rerun (`st.rerun()`) + sidebar "Force refresh" button 채택. 사용자 능동 refresh + 5s TTL cache 가 자동 freshness 제공.

### 5.3 Visual layout (F-3 ADOPT-AS-IS)

- 상단 banner: `st.error` (red) / `st.warning` (yellow) / `st.success` (green) — worst_level 매핑
- per-node card (`st.columns`): freshness + ws_state + tier_lags (st.metric) + cumulative metrics (dup_skip / quarantine / ws_reconnect / backfill_pending)
- footer: last fetched ISO timestamp + cache TTL 안내

### 5.4 AppTest scope (F-4 SUGGEST 채택)

6 scenario covered:
1. Green render (exit 0)
2. Yellow render (exit 1)
3. Red render (exit 2)
4. No heartbeat files (exit 2 + empty stdout)
5. Malformed JSON (adapter error)
6. Two nodes (cluster rendering)

`subprocess.run` + `shutil.which` patch 로 CLI mock. AppTest default_timeout=20s.

### 5.5 Dependency footprint (F-5 SUGGEST 채택)

`mctrader-data @ git+...@main` 채택.

X6 implementation review 의 F-4 PUSH-BACK 결과: 기존 `api/backtest_lifecycle.py` + `api/routes.py` 가 unconditional `import mctrader_data` 사용 — pre-existing inconsistency. Sonnet decider 채택: **core dep 으로 promote** (단일 source of truth, optional [dashboard] 제거).

### 5.6 후속 escalation (X6 scope 외)

- heartbeat history ring-buffer (X4 후속 minor)
- HeartbeatMetrics.events_total cumulative → dedup ratio denominator
- streamlit-autorefresh extension 평가 (5s 자동 push 가 사용자 stop 보다 더 가치 있는지)
- per-symbol drilldown / time-series chart (v2)

## 6. 외부 지식 배경

### 6.1 Streamlit AppTest framework

- `streamlit.testing.v1.AppTest` — official testing harness, no browser needed
- `at.run()` → DOM-like tree of widgets (markdown, success, warning, error, columns, metric)
- mock subprocess via stdlib `unittest.mock.patch`
- `default_timeout` argument for slow imports

### 6.2 Streamlit caching strategies

- `@st.cache_data` — Streamlit-native, but sensitive to Streamlit version
- module-level `_CACHE: dict` — pure Python, AppTest-friendly (status_adapter chooses this)
- threading.Lock — not needed (Streamlit single-threaded per session)

### 6.3 Streamlit page navigation

- `pages/` directory under app entry — automatic sidebar registration
- prefix `00_` `01_` `02_` controls sort order
- file name (after stripping prefix) = page label in sidebar

## 7. 설계 서사

(Phase 6 plan: `docs/superpowers/plans/2026-05-06-collector-ha-phase-6.md`)

## 8. 개발 서사

### 8.1 구현 PR (X6)

- mctrader-web PR #15 — `pages/00_status.py` + `status_adapter.py` + 16 tests + pyproject 0.13.0
- mctrader-hub 본 PR — Story §1-9 + §11 + Phase 6 plan

### 8.2 변경 surface (mctrader-web 0.12.0 → 0.13.0)

| File | 변경 |
|---|---|
| `src/mctrader_web/dashboard/status_adapter.py` (NEW) | cached subprocess wrapper (5s TTL, exit 0/1/2 mapping, malformed JSON / timeout / CLI missing → adapter error) |
| `src/mctrader_web/dashboard/pages/00_status.py` (NEW) | Streamlit page: per-node card + worst_level banner + sidebar root/threshold/refresh |
| `tests/test_status_adapter.py` (NEW, 10 tests) | exit 0/1/2, no heartbeat, malformed, CLI missing, timeout, unexpected exit, cache hit/bypass |
| `tests/test_apptest_status_panel.py` (NEW, 6 tests) | green/yellow/red/no_heartbeat/malformed/two_nodes |
| `pyproject.toml` | mctrader-data 0.8 promoted to core (Codex F-4 PUSH-BACK fix), version 0.13.0 |

### 8.3 Codex 2-tier review

#### Phase 6 design (6/6 ADOPT 합)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 approach | SUGGEST | A 채택 (subprocess + 5s cache) |
| F-2 auto-refresh | SUGGEST | Streamlit native rerun |
| F-3 layout | ADOPT-AS-IS | — |
| F-4 AppTest scope | SUGGEST | 6 scenarios 채택 |
| F-5 deps | SUGGEST | mctrader-data 채택 |
| F-6 out-of-scope | ADOPT-AS-IS | — |

#### Implementation review (5/6 ADOPT + 1 PUSH-BACK fix)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 adapter correctness | ADOPT-AS-IS | — |
| F-2 page UX | ADOPT-AS-IS | — |
| F-3 test coverage | ADOPT-AS-IS | — |
| **F-4 dependency footprint** | **PUSH-BACK** | **fix 적용** — mctrader-data core dep promotion (pre-existing api/* unconditional import 정합) |
| F-5 cross-artifact consistency | ADOPT-AS-IS | — |
| F-6 out-of-scope hygiene | ADOPT-AS-IS | — |

총 escalation 0/12 (모두 in-Phase 채택 + fix).

## 9. 품질 게이트 이력

| Gate | Result | Evidence |
|---|---|---|
| Codex Phase 6 design 6/6 review | ADOPT 합 | Story §5 + plan §0 |
| Codex implementation 6/6 review | ADOPT 5 + PUSH-BACK 1 fix 적용 | F-4 core dep promotion |
| pytest mctrader-web | **171 PASS** (155 prior + 16 new) | regression 0 vs 0.12.0 |
| ruff lint | clean | E501/B905/F541/F401 모두 fix |
| AppTest smoke 6 scenarios | PASS | streamlit.testing.v1.AppTest |
| Backward compatibility | 100% | 기존 page (01/02/03_*.py) 영향 0, api/* 변경 0 |

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|
| 1 | 2026-05-06 | implementation | Codex F-4 PUSH-BACK | api/* unconditional `import mctrader_data` 가 [dashboard] extra 만 declared = pre-existing inconsistency | mctrader-data → core dep promotion | NO |

## 11. 회고

### 11.1 Phase 6 종료 marker (2026-05-06)

X6 web measure surface 가 X4 CLI contract 위에 cleanly 작동. operator 측 web dashboard 한 페이지에서 양 node health 가시화 — 사용자 원래 요구사항 ("데이터 순단 줄이고자") 의 *visible terminal point*.

### 11.2 X6 기술 부채 surface

- streamlit-autorefresh extension 도입 평가 (자동 5s push UX vs extra dep cost)
- per-symbol breakdown / time-series chart (현재는 cumulative counter only)
- heartbeat history ring-buffer (X4 후속) 도입 시 web 의 "최근 1h ws_reconnect 추세" 차트 가능

### 11.3 Epic MCT-89 진행도 (X6 종료 시점)

| Phase | Story | 상태 |
|---|---|---|
| 1 | MCT-89 (Epic) | CLOSED ✅ |
| 2 | MCT-91 (X2) | MERGED ✅ |
| 3 | MCT-92 (X3) | MERGED ✅ |
| 4 | MCT-93 (X4) | MERGED ✅ |
| 5 | MCT-94 (X5) | MERGED ✅ |
| **6** | **MCT-95 (X6)** | **MERGED ✅ (이번 Phase)** |
| 7 | (X7 Calibration + 양 node 30분 E2E demo + Epic close) | PENDING |

다음 step = X7 (mctrader-hub) — Calibration C1/C2 (throughput / scan latency overhead) + 양 node 30분 E2E demo + Epic close + EPIC-RESULTS-MCT-89 작성.
