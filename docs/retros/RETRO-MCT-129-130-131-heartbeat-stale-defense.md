# RETRO-MCT-129-130-131 — heartbeat stale 3-layer defense

**범위**: MCT-129 (mctrader-data cli.py `_resolve_node_id`) + MCT-130 (mctrader-data HeartbeatWriter `cleanup_stale_heartbeats`) + MCT-131 (mctrader-web `00_status.py` active/stale 분기 렌더링)
**기간**: 2026-05-11 (MCT-127 → MCT-128 → MCT-129[old] → 동일 세션 연장)
**Trigger**: 2026-05-10 운영 장애 — `http://mctrader.mclayer.it/status` 페이지가 11+ 컬럼 누적으로 레이아웃 파괴. `socket.gethostname()` = Docker container short ID 변동으로 `heartbeat-{node_id}.json` 무기한 누적. 3-layer defense (원천 차단 + 누적 정리 + UI 방어) 로 영구 해결.
**Spec**: `docs/superpowers/specs/2026-05-11-heartbeat-stale-cleanup-design.md`
**Plan**: `docs/superpowers/plans/2026-05-11-heartbeat-stale-cleanup.md`
**Status**:
- 3 Story 완료 (MCT-129/130/131) + Cat B finish-up 2 commit
- AC 12/12 (100%) — fix-clean (heartbeat 본 작업 한정 FIX 0)
- mctrader-web CI **GREEN** (`25650469975` SUCCESS)
- mctrader-data CI **RED** — pre-existing infra issue (#30, 본 Story 무관) — follow-up Story 후보 등록

**Story files**: `docs/stories/MCT-129.md`, `MCT-130.md`, `MCT-131.md` (§11 PMO 회고 본 RETRO pointer 박제)
**Repos**: `mctrader-data` (cli.py + heartbeat.py) + `mctrader-web` (00_status.py)
**선행**: MCT-127/128/129[old] 3-Story doc-only 연쇄 (RETRO-MCT-129.md — 5 impl repo CLAUDE.md propagate, 2026-05-11 동일 세션 직전 완료)
**후행**: (HIGH) mctrader-data CI #30 PAT 권한 fix Story / (MED) Layer 1 적용 후 운영 검증 — stale 누적이 실제로 0 으로 수렴하는지 모니터

---

## 1. 결과 요약

### 1.1 Story scope vs 실제 변경 매트릭스

| Story | AC | 결과 | repo / commit |
|---|---|---|---|
| MCT-129 (Layer 1) | 2 AC | done — cli.py `_resolve_node_id` 우선순위 fix | `mctrader-data` `c852788` |
| MCT-130 (Layer 2) | 6 AC | done — HeartbeatWriter `cleanup_stale_heartbeats` + `run()` 호출 | `mctrader-data` `69d3c57` |
| MCT-131 (Layer 3) | 4 AC | done — 00_status.py active/stale 분기 + expander | `mctrader-web` `4eb4a43` |

→ **3-Story scope 12/12 AC 100% 완료**. 3-layer defense 가 spec §2 의 3 레이어와 1:1 매핑. 각 Story 가 단일 레이어 책임 — 가설 격리 정합.

### 1.2 commit 통계

| 단위 | repo | 통계 | 상태 |
|---|---|---|---|
| `c852788 feat(mct-129)` | mctrader-data | cli.py + tests/test_cli_node_id.py 신규 (3 test) | main 직접 push |
| `69d3c57 feat(mct-130)` | mctrader-data | heartbeat.py + tests/test_heartbeat.py append (6 test) | main 직접 push |
| `4eb4a43 feat(mct-131)` | mctrader-web | 00_status.py + tests/test_apptest_status_panel.py append (3 test) | main 직접 push |
| `a8a14d8 fix(lint)` | mctrader-web | **Cat B** — pre-existing 10 lint (F401/B904/SIM105/E402/UP037) | main 직접 push |
| `d804d73 fix(control)` | mctrader-web | **Cat B** — engine_id regex 회귀 (`[a-zA-Z0-9_-]` → `[a-z0-9_-]`) | main 직접 push |
| `1e66664 / 8b5d098 / 82c3b8d / 5cb27f1 fix(ci)` | mctrader-data | **CI infra 시도** — CODEFORGE_CROSS_REPO_PAT git auth 4 시도, 모두 실패 → #30 issue | main 직접 push (CI 검증 중) |

→ **3 본 commit + 2 Cat B finish-up (mctrader-web) + 4 CI infra 시도 (mctrader-data, 미해결)**. mctrader-hub `1e6867e docs(mct-129/130/131): heartbeat stale cleanup 구현 계획 추가` Plan commit 1건 별도.

### 1.3 테스트 결과

| Story | 테스트 | 로컬 | CI |
|---|---|---|---|
| MCT-129 | `tests/test_cli_node_id.py` 3 test (explicit > env > hostname) | PASS | RED — #30 pre-existing infra (private dep auth) |
| MCT-130 | `TestHeartbeatStaleCleanup` 6 test (stale 삭제/자기 보호/신선 보호/디렉 부재/OSError/run 호출) | PASS | RED — 동일 #30 |
| MCT-131 | AppTest 3 test (mixed/all-stale/active-only) | PASS | **GREEN** (run `25650469975` SUCCESS) |

→ **로컬 검증 12/12 PASS**. mctrader-data CI 실패는 본 Story 변경 무관 — Upbit 통합 (2026-05-09) 이후 계속 RED 상태. §5 분리 책임 박제.

### 1.4 부수 fix 비율 (RETRO-MCT-117 §4.2 표준 적용)

| 카테고리 | 사례 수 | 비중 | 분류 |
|---|---|---|---|
| 본 Story 본 작업 (MCT-129/130/131 12 AC) | 12 | 71% | 본 작업 |
| Cat A (pre-existing, 사전 인지된 별개 문제) | 0 | 0% | — |
| Cat B (self-discovered, 본 Story 작업 중 발견) | 2 commit | 12% | mctrader-web lint 10종 + engine_id regex 회귀 |
| Cat C (다른 Story finish-up) | 0 | 0% | — |
| CI infra (별도 분류) | 4 commit | 24% | mctrader-data #30 — 본 Story 무관, **분리 처리 의무** |

→ **본 작업 100% AC 달성, Cat B 2건 추가 정리, CI infra 별도 분리** (§5 참조). RETRO-MCT-126 / 127 / 128 / 129[old] 의 fix-clean 4 연속 streak 는 Cat B 2건으로 **중단** — multi-repo non-doc Story 진입 시 Cat B 발생 정상화 lane.

### 1.5 cross-repo 작업 분해

| Repo | branch | push | PR | merge | CI |
|---|---|---|---|---|---|
| `mctrader-data` | `main` (직접 push) | done (5 commit) | (없음, ADR-019 D6) | done | RED (#30) |
| `mctrader-web` | `main` (직접 push) | done (3 commit) | (없음) | done | GREEN |
| `mctrader-hub` | `main` (직접 push) | done (Plan 1 commit) | (없음) | done | n/a (doc-only) |

→ **3-repo Story**. mctrader-data 와 mctrader-web 가 **종속 순서** (Layer 1→3 의 functional dependency 있으나 commit/test 는 independent). Layer 1 적용 없이 Layer 3 만으로도 UI crash 회피 가능 — 방어 독립성 확보 design 정합.

---

## 2. Sonnet decider (Story §4 박제)

3 Story 각 §4 결정 표 종합:

| Story | 결정 | 선택 | 근거 |
|---|---|---|---|
| MCT-129 | compose.yml 변경 여부 | 변경 없음 | 이미 NODE_ID 설정됨 — cli.py 가 못 읽는 게 버그 |
| MCT-129 | helper 위치 | 모듈 레벨 함수 | 단위 테스트 격리 가능 |
| MCT-130 | start() 신설 vs run() 호출 | run() 직접 호출 | start() 메서드 없음, run() 시작 시 1회 |
| MCT-130 | TTL env var | `MCTRADER_HEARTBEAT_STALE_CLEANUP_SECONDS=300` | 5s × 60 = false-positive 0 위험 |
| MCT-130 | TOCTOU guard | mtime 재확인 후 삭제 | double-check 패턴, race 회피 |
| MCT-131 | stale 노드 표시 방법 | `st.expander(expanded=False)` | 레이아웃 파괴 없이 정보 보존 |
| MCT-131 | active 0개 guard | `max(1, len(active_nodes))` | `st.columns(0)` 예외 방지 |

→ decider 박제 7 결정점 — 3-Story 통합 시 가장 많은 결정 항목. 운영 장애 회복 Story 의 결정 밀도 박제.

---

## 3. Cat B finish-up 2건 패턴 분석 (mctrader-web)

본 Story 의 가장 lane-rich 한 발견 — Layer 3 Story 진입 시 mctrader-web 사전 회귀 노출:

### 3.1 Cat B-1: lint 10종 (commit `a8a14d8`)

| 항목 | 내용 |
|---|---|
| 발견 시점 | MCT-131 commit 후 ruff check 실행 시 |
| 분포 | F401 (unused import) / B904 (raise from) / SIM105 (contextlib.suppress) / E402 (top-level import) / UP037 (deprecated type hint) — 5 룰 10건 |
| 발생 원인 | mctrader-web 이전 commit 들 (MCT-119 ~ MCT-126 stream) 에서 누적된 lint 부채. ruff 자동 fix + 수동 수정으로 해결 |
| 분류 근거 | **Cat B** — MCT-131 본 작업과 무관, but Story 진입 시 사전 정리해야 mctrader-web CI 통과 가능. `feedback_consumer_evidence_rapid_iteration.md` 의 evidence rapid iteration 정합 |

### 3.2 Cat B-2: engine_id regex 회귀 (commit `d804d73`)

| 항목 | 내용 |
|---|---|
| 발견 시점 | MCT-131 commit 후 전체 회귀 테스트 시 `test_invalid_engine_id_returns_422` FAIL |
| 회귀 위치 | `_ENGINE_ID_RE` 가 `[a-zA-Z0-9_-]` (대문자 허용) 으로 사전 어딘가에서 잘못 완화됨 |
| 정합 기준 | `[a-z0-9_-]` (소문자 only) 가 원래 contract — 회귀 fix 로 복원 |
| 분류 근거 | **Cat B** — MCT-131 본 작업과 무관, but pre-existing 회귀가 mctrader-web CI 게이트 차단. **본 Story 의 CI GREEN 가능 조건** |

### 3.3 Cat B 발생 패턴 박제 (PMO 횡단 감사용)

- **multi-repo non-doc Story 진입 시 Cat B 발생 정상화** — doc-only Story (MCT-127/128/129[old]) fix-clean streak 4 연속은 doc-only 특성. non-doc 진입 시 pre-existing 회귀·lint 부채가 surface 되어 Cat B 1~3건 발생 normal lane
- **CI GREEN 가능 조건 = Cat B 사전 정리** — 본 Story 의 Layer 3 commit (`4eb4a43`) 만으로는 CI RED. Cat B 2 commit (`a8a14d8` + `d804d73`) 추가 후 CI GREEN (`25650469975`). 본 Story 의 CI 성공은 Cat B 정리에 의존
- **분기당 lint sweep 의무 lane 추가 후보** — mctrader-web 이 MCT-119 ~ MCT-126 까지 7 Story stream 누적 후 본 Story 진입 시 lint 부채 surface. 추후 분기 1회 ruff check 정기 sweep Story 발의 후보 (RETRO-MCT-129 §7 의 backlog 합류)
- **regex 회귀 같은 silent 회귀 감지 lane** — `_ENGINE_ID_RE` 가 `[a-zA-Z0-9_-]` 로 사전 어디서 변경됐는지 git blame 미수행. 추후 silent 회귀 감지를 위해 mctrader-web 의 `_ENGINE_ID_RE` / `_TIMEFRAME_RE` 등 contract regex 의 unit test 의무화 lane 검토

---

## 4. 3-layer defense design 의 lane 박제

본 Story 의 핵심 design 패턴 — 단일 운영 장애의 3-layer 영구 해결:

### 4.1 layer 책임 분리 정합

| Layer | 책임 | failure mode | 다른 Layer 의존 |
|---|---|---|---|
| Layer 1 (MCT-129) | 원천 차단 — `node_id` 가 hostname 으로 떨어지지 않음 | env var 미설정 시 fallback (hostname) | 없음 — independent |
| Layer 2 (MCT-130) | 누적 정리 — TTL 초과 파일 삭제 | OSError → warn + continue, 수집 차단 X | 없음 — Layer 1 적용 여부와 무관 동작 |
| Layer 3 (MCT-131) | UI 방어 — 11+ stale 노드 도착해도 레이아웃 정합 | active 0개 시 `st.columns(1)` fallback | 없음 — Layer 1/2 미적용 시에도 동작 |

→ **3 Layer 가 모두 independent failure mode 보유**. 어떤 단일 Layer 실패 시에도 다른 Layer 가 방어. defensive design 의 표준 패턴.

### 4.2 layer 적용 순서 박제

본 Story 가 Layer 1 → 2 → 3 순서로 commit. 이 순서가 **운영 안전** 측면 최적:

1. **Layer 1 우선** — 신규 stale 파일 생성을 즉시 멈춤. Layer 2 의 TTL 정리가 누적분만 처리하면 됨 (영구 누적 방지)
2. **Layer 2 그 다음** — Layer 1 적용 시점 이전 누적분 (9 stale 파일 등) 정리
3. **Layer 3 마지막** — Layer 1/2 가 ineffective 한 경우 (env var 누락, 정리 실패 등) UI 보호

→ **반대 순서 (3→2→1) 는 안전 trade-off 열등** — Layer 3 먼저 적용 시 UI 는 깨끗하나 stale 파일 누적은 계속됨 (디스크 leak). Layer 적용 순서 lane 박제 — 추후 multi-layer defense Story 진입 시 reference template.

### 4.3 spec → Story 1:1 매핑 정합

`docs/superpowers/specs/2026-05-11-heartbeat-stale-cleanup-design.md` §2 의 3 레이어가 3 Story 와 1:1 매핑. spec 분해 정합성 사례 박제:

- spec §2 레이어 1 → MCT-129 (cli.py 1줄 + helper 함수)
- spec §2 레이어 2 → MCT-130 (HeartbeatWriter 메서드 + run() 호출)
- spec §2 레이어 3 → MCT-131 (00_status.py active/stale 분기)

→ spec 의 §2 레이어 N = Story key N+128 패턴 박제. 추후 multi-layer defense Story 분해 시 spec ↔ Story 1:1 매핑 template 적용.

---

## 5. mctrader-data CI #30 분리 책임 박제

본 Story 의 가장 중요한 lane 분리 — CI 실패가 본 Story 책임이 아님:

### 5.1 #30 issue 본질

- **증상**: `uv sync --all-extras` 에서 private dep (mctrader-market / market-bithumb / market-upbit) 클론 실패
- **원인**: `CODEFORGE_CROSS_REPO_PAT` 시크릿이 3 repo 에 대한 contents:read 권한 없음
- **발생 시점**: 2026-05-09 Upbit 통합 (`90186c6 feat(compactor)` 이전) 이후 mctrader-data CI 계속 RED
- **본 Story 와의 관계**: **무관** — 본 Story 코드는 cli.py / heartbeat.py 의 변경. CI 실패는 의존성 클론 단계 (test 실행 이전)

### 5.2 본 Story 내 fix(ci) 4 commit 결과

| commit | 시도 | 결과 |
|---|---|---|
| `1e66664 fix(ci)` | `CODEFORGE_CROSS_REPO_PAT` git auth header 추가 | FAIL — PAT 권한 부족 |
| `8b5d098 fix(ci)` | `GITHUB_TOKEN` 사용 시도 | FAIL — private org repo 접근 불가 |
| `82c3b8d fix(ci)` | `oauth2:` prefix (fine-grained PAT format) | FAIL — PAT 자체 권한 문제 |
| `5cb27f1 fix(ci)` | `x-access-token` format revert | FAIL — 동일 |

→ **모든 시도는 PAT 권한 자체 문제 — repo 설정 변경 없이는 fix 불가**. 본 Story 진행 중 4 commit 시도 후 #30 issue 발의로 escalate. `feedback_escalate_to_codeforge.md` 의 escalate-and-fix 정합 — consumer workaround 거부, upstream (org PAT 설정) escalate.

### 5.3 분리 책임 박제 lane

추후 multi-repo Story 진입 시 본 패턴 적용:

- **본 Story 책임 = Story 코드의 functional 정합**. 로컬 test PASS 로 검증 충분
- **CI infra 실패는 별도 issue + follow-up Story 로 분리**. 본 Story merge / close 차단 사유 아님
- **`feedback_ci_terminal_states_classify.md` 적용** — `naive green` 대기 금지 정합. CI RED 가 본 Story 책임이 아닐 때 분리 처리 의무

→ **본 Story 의 CI 책임 = mctrader-web GREEN (Layer 3 실제 변경 repo) 만**. mctrader-data CI 는 #30 fix 까지 별도 lane.

---

## 6. Story key 충돌 처리 박제 (MCT-129 overwrite)

본 Story 의 가장 anomalous 한 lane — Story key 재사용:

### 6.1 충돌 발생 경위

| 시점 | event |
|---|---|
| 2026-05-11 (오전) | MCT-127 → MCT-128 → MCT-129[old] doc-only 3-Story 연쇄 완료 (5 impl repo CLAUDE.md propagate). RETRO-MCT-129.md 박제. commit `e381d06 docs(mct-129)` |
| 2026-05-11 (오후) | 운영 장애 회복 Story 진입 시 heartbeat stale 3-layer defense 가 MCT-129/130/131 로 키 할당 됨 |
| **충돌** | MCT-129 Story file (`docs/stories/MCT-129.md`) 이 heartbeat cli.py fix 로 **overwrite** — old MCT-129 (CLAUDE.md propagate) 의 Story file 은 git history (commit `e381d06` 의 신규 추가) 에만 남음 |

### 6.2 영향 분석

- **RETRO 파일 2개 공존**:
  - `RETRO-MCT-129.md` — 5 impl repo CLAUDE.md propagate (doc-only)
  - `RETRO-MCT-129-130-131-heartbeat-stale-defense.md` — 본 RETRO (heartbeat)
- **Story file 1개만 존재**: `docs/stories/MCT-129.md` = heartbeat cli.py fix (overwrite 후 상태). old MCT-129 Story file 본문은 git history `e381d06` 에 박제됨 — `git show e381d06:docs/stories/MCT-129.md` 로 복구 가능
- **GitHub Issue 측 영향**: 본 Story 는 GitHub Issue 없이 진행 (ADR-019 D6 doc-only fast-pass 패턴) — Issue 번호 충돌 없음

### 6.3 분리 식별 lane 박제

추후 횡단 감사 시 두 MCT-129 를 구분하는 절차:

| 구분 | old MCT-129 | new MCT-129 |
|---|---|---|
| RETRO 파일 | `RETRO-MCT-129.md` | `RETRO-MCT-129-130-131-heartbeat-stale-defense.md` |
| Story scope | 5 impl repo CLAUDE.md propagate (doc-only) | mctrader-data cli.py fix (code) |
| 완료 commit (hub) | `e381d06 docs(mct-129)` (Story file + 5 repo propagate) | `1e6867e docs(mct-129/130/131)` (Plan) — Story file 은 본 Story 시작 직전 overwrite |
| 본 repo commit | mctrader-market `84b5087` / market-bithumb `18ccf28` / data `6a34b6b` / engine `bf748d8` / web `4c5bd0a` | mctrader-data `c852788 feat(mct-129)` |
| 기간 | 2026-05-11 (오전) | 2026-05-11 (오후) |

### 6.4 PMO 입장 박제

- **Story key 재사용은 anomaly** — 정상 lane 에서는 1 key = 1 Story. 본 사례는 동일 일자 short-cycle 에서 plan author 가 old MCT-129 완료를 인지하지 못하고 키 할당
- **회피 절차 박제** — 추후 Story plan 작성 시 직전 24시간 내 commit log grep + RETRO 파일 grep 으로 key collision 사전 검증 의무
- **현재 상태 처리** — old MCT-129 Story file 복원은 **불필요**. RETRO-MCT-129.md 가 SSOT 로 충분 (Story §1-§11 정보 모두 RETRO 본문에 박제됨). git history 의 `e381d06` commit 이 보존 backup
- **post-hoc lane 박제** — 본 RETRO 의 §6 박제로 미래 횡단 감사 시 collision lane 인지 가능. RETRO-MCT-129.md 와 본 RETRO 모두 추후 reference 시 §6 본문 참조 의무

→ **권고**: `RETRO-MCT-129.md` 본문 상단에 본 RETRO §6 pointer 추가 cross-ref 보강 — 단, 본 RETRO commit 후 별도 amendment commit 으로 처리 (본 Story scope 외).

---

## 7. RETRO-MCT-129[old] 대비 lane 비교

| 항목 | RETRO-MCT-129[old] | RETRO-MCT-129/130/131 (본 RETRO) |
|---|---|---|
| commit 수 (hub 포함) | 6 (5 impl + 1 hub) | 9 (3 본 + 2 Cat B + 4 CI infra) + 1 hub Plan |
| repo 수 | 6 | 3 (data/web/hub) |
| AC 충족률 | 5/5 (100%) | 12/12 (100%) — fix-clean (heartbeat 한정) |
| Cat A/B/C fix 비율 | 0/0/0% | 0/2 commit (12%)/0 |
| CI cycle | 0 (doc-only fast-pass) | 5 (mctrader-data 4 fail + mctrader-web 1 GREEN) |
| Sonnet decider 결정점 | 3 | 7 (3 Story × 평균 2.3) |
| 자동 dispatch 게이트 | done | done |
| 패턴 분류 | multi-repo SSOT propagate (doc-only) | multi-layer defense (code, 운영 장애 회복) |

→ **doc-only Story 의 simple lane (RETRO-129[old]) vs 운영 장애 multi-layer 회복 Story 의 complex lane (본 RETRO)** 의 대비 박제. 본 RETRO 가 보유한 추가 lane:
- Cat B 2건 (multi-repo non-doc 특성)
- CI infra 분리 책임 (#30)
- Story key 충돌 처리 (§6)
- 3-layer defense design 박제 (§4)

추후 운영 장애 회복 Story 진입 시 본 RETRO 가 reference template — Layer 분해 / 적용 순서 / Cat B 발생 정상화 / CI infra 분리 lane.

---

## 8. 위반 / 개선 사항

**위반 없음**:
- AC 100% 충족 (12/12)
- 본 작업 fix-clean (Heartbeat 본 작업 FIX 0 — Cat B 는 별도 분류)
- §11 회고 자동 dispatch (`feedback_pmo_retro_mandatory.md`) 게이트 충족 — 4 Story 연속 (MCT-127 + 128 + 129[old] + 129/130/131) 자동 dispatch lane 유지
- mctrader-web CI GREEN — Story 정합 검증
- mctrader-data CI RED 는 #30 별도 분리 (본 Story 책임 외)

**개선 제안 3건 이하** (PMOAgent §5 정합):

1. **(HIGH) mctrader-data CI #30 PAT 권한 fix 후속 Story 우선 진행** — 본 Story 진입 시 4 commit fix 시도 모두 실패. mclayer org PAT 권한 설정 또는 별도 `MCTRADER_PRIVATE_DEPS_TOKEN` 시크릿 신설 필요. mctrader-data CI 가 2026-05-09 이후 계속 RED 상태로 향후 모든 mctrader-data Story 의 CI 검증 차단. follow-up Story key TBD (next available, 본 RETRO 박제 후 발의).

2. **(MED) mctrader-web `_ENGINE_ID_RE` / `_TIMEFRAME_RE` contract regex 의 unit test 의무화** — 본 Story 진입 시 `_ENGINE_ID_RE` 가 silent 회귀 (`[a-zA-Z0-9_-]` 로 잘못 완화) 발견. git blame 으로 변경 시점 추적 미수행. 추후 silent 회귀 감지를 위해 mctrader-web 의 contract regex 별 explicit unit test 신설 lane. RETRO-MCT-119-web-test-overhaul.md 의 web test 보강 stream 합류 후보.

3. **(MED) RETRO-MCT-129.md 본문 상단 cross-ref 추가** — old MCT-129 RETRO 가 본 RETRO §6 의 collision 박제를 모름. 횡단 감사 시 RETRO-MCT-129.md 만 보는 경우 collision 사실 누락. 본 RETRO commit 후 별도 amendment commit 으로 `RETRO-MCT-129.md` 상단에 본 RETRO §6 pointer 1줄 추가 권고 (본 Story scope 외 follow-up).

---

## 9. 후속 Story 후보

| 후보 | 우선순위 | 근거 | 추정 Story key |
|---|---|---|---|
| **mctrader-data CI #30 PAT 권한 fix** | **HIGH** | `mclayer/mctrader-data#30` — `CODEFORGE_CROSS_REPO_PAT` 권한 부족으로 mctrader-data CI 2026-05-09 이후 RED. 모든 후속 mctrader-data Story CI 검증 차단. org PAT 권한 추가 또는 별도 PAT 신설. | MCT-132 후보 |
| **Layer 1 적용 후 stale 누적 0 수렴 운영 검증** | MED | 본 Story 코드 변경은 commit / 로컬 test PASS. 실제 운영 환경에서 Layer 1 적용 후 `heartbeat-{node_id}.json` 파일이 NODE_BITHUMB_A / NODE_UPBIT_A 만 유지되는지 + 기존 stale 9개가 Layer 2 cleanup 으로 5분 내 사라지는지 monitor. 1주 검증 후 결과 박제. | MCT-133 후보 |
| **mctrader-web contract regex unit test 신설** | MED | §8 개선 제안 2 — `_ENGINE_ID_RE` silent 회귀 재발 방지. regex contract 별 explicit unit test 의무화 lane. | TBD |
| **분기 1회 ruff lint sweep 정기 Story** | MED | §3.3 박제 — mctrader-web 7-Story stream 누적 후 lint 10건 surface. 분기 1회 정기 sweep 으로 부채 surface 시점 분산. | TBD (분기 backlog) |
| **RETRO-MCT-129.md cross-ref amendment** | LOW | §8 개선 제안 3 — old MCT-129 RETRO 상단 cross-ref 1줄 추가. amendment commit 1회. | n/a (commit 1건) |
| **GitPython HIGH 취약점 fix** (RETRO-MCT-129[old] §7 carry-over) | HIGH | RETRO-MCT-129[old] §7 의 (HIGH) 후속 후보 — mctrader-web GitPython newline injection RCE alert. 본 Story 와 별도 trigger 로 처리. | MCT-132 또는 후속 |

---

## 10. Cross-Story 패턴 메모 (PMO 횡단 감사용)

본 RETRO 가 향후 cross-Story 패턴 분석 (PMOAgent §3 책임) 시 referenced 될 항목:

- **multi-layer defense design 의 표준 lane (§4)** — 운영 장애 회복 시 single-fix 대비 multi-layer 의 trade-off. spec ↔ Story 1:1 매핑 패턴 박제
- **Cat B 발생 정상화 lane (§3.3)** — multi-repo non-doc Story 진입 시 pre-existing 부채 surface 의 normal lane. doc-only fix-clean streak 와 분리 평가
- **CI infra 분리 책임 lane (§5)** — 본 Story 책임 외 CI 실패 (mctrader-data #30) 의 별도 처리 표준. `feedback_ci_terminal_states_classify.md` + `feedback_escalate_to_codeforge.md` 합류 패턴
- **Story key 충돌 처리 lane (§6)** — 동일 일자 short-cycle 에서 key collision 발생 시 처리 절차. plan 작성 시 24시간 grep 검증 의무화 후보
- **3-Story 통합 RETRO vs Story 별 개별 RETRO 의 선택 기준** — 본 RETRO 가 3 Story 를 단일 파일로 박제. 선택 기준: ① 단일 spec / plan 의 multi-Story 분해, ② 동일 일자 short-cycle, ③ 결정점 7+ 의 통합 lane. RETRO-MCT-107-111-code-review-fix.md / RETRO-MCT-119-120-strategy-pipeline.md / RETRO-MCT-122-123.md 와 동일 패턴
- **silent 회귀 감지 lane (§3.3 / §8 제안 2)** — contract regex 변경 추적의 어려움. unit test 의무화 lane 의 가치 — 본 Story 가 Cat B-2 발견 case 로 박제
- **escalate-and-fix 정합 사례 (§5.3)** — 4 commit consumer 시도 후 upstream (org PAT) escalate 의 정합 lane. `feedback_escalate_to_codeforge.md` 직접 적용 사례

---

**Status**: done — 본 RETRO 박제로 §11 PMO 회고 자동 dispatch 게이트 충족 (`feedback_pmo_retro_mandatory.md`). MCT-132 (mctrader-data CI #30 PAT 권한 fix) 즉시 우선 진행 권고 (HIGH).
