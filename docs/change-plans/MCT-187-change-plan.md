# MCT-187 Change Plan — 다중거래소 확장 불변식 박제 (D5+D6)

> **ArchitectPLAgent Change Plan** — MCT-187 설계 lane 산출물.
> 구현 lane은 본 Change Plan을 변경 없이 집행한다. 범위 밖 결정 금지.

---

## §1 Story 범위 요약

EPIC-data-domain-decoupling sequential_phase 6. MCT-186 COMPLETED 후 진입.

**핵심**: D5 "data-only-extension-invariant" — 신규 거래소 추가 시 engine/market-core/ADR 변경 0,
data `adapters.py` 등록만으로 활성화 가능함을 invariant test + runbook + ADR-031 §D5 VERIFIED
amendment box 로 영구 박제한다.

**코드 변경 최소**: `adapters.py` 변경 0 (MCT-186 LAND 시점 팩토리 이미 완비). 본 Story =
test 박제 + runbook 신규 + ADR amendment + carry over 처리.

---

## §2 Phase 0 실증 요약 (§0 박제 SSOT)

| V | 실증 사실 | 구현 영향 |
|---|----------|----------|
| V1/V2 | `adapters.py` bithumb/upbit 2-branch 완비 (58 lines, HEAD 22e2ece) | adapters.py 변경 0 확정 |
| V3 | `tests/test_adapters.py` 6개 기능 test 기존 존재 | 신규 파일 `tests/test_multi_exchange_invariant.py` 추가 |
| V4 | engine pyproject bithumb dep 잔존 (MCT-188 D7 final) | INV-1 grep 확인만 (pyproject 변경 0) |
| V5 | ADR-031 §D5 미박제 | 본 Story AC-3 LAND 대상 |
| V6 | MCT-186 carry over — compose.yml NAS env | hub Phase 1 PR scope 포함 (§5 결정) |

---

## §3 변경 계획 (파일 단위)

### §3.1 mctrader-hub — Phase 1 PR (docs + carry over)

| 파일 경로 | 변경 | 우선순위 |
|----------|------|---------|
| `docs/stories/MCT-187.md` | 요구사항 lane 작성본 (이미 작성) → Phase 1 PR commit | P0 |
| `docs/change-plans/MCT-187-change-plan.md` | 본 파일 | P0 |
| `docs/runbooks/add-new-exchange.md` | **신규** — 3-step 신규 거래소 추가 절차 runbook | P0 (AC-2) |
| `docs/adr/ADR-031-data-domain-decoupling.md` | §D5 VERIFIED amendment box draft (구현 전 outline, Phase 2 PR2 확정) | P0 (AC-3) |
| `docs/adr/ADR-030-docker-stack-governance.md` | NAS cred drop carry over box 추가 박제 (MCT-186 RETRO §7) | P1 (AC-5) |
| `scope_manifests/EPIC-data-domain-decoupling.yaml` | MCT-187 IN_PROGRESS + MCT-186 COMPLETED 확정 | P0 |
| `.codeforge/counters.json` | MCT-187 status IN_PROGRESS 갱신 | P0 |
| `CLAUDE.md` | §EPIC-data-domain-decoupling MCT-187 IN_PROGRESS 박제 | P1 |
| `compose.yml` (hub root) | engine service `NAS_MINIO_*` env line 제거 (MCT-186 RETRO §7 carry over, **AC-5**) | P1 (AC-5 carrier) |

### §3.2 mctrader-data — Phase 2 PR1 (land_order 1)

| 파일 경로 | 변경 | 우선순위 |
|----------|------|---------|
| `tests/test_multi_exchange_invariant.py` | **신규** — D5 invariant test 5종 (§3.4 상세) | P0 (AC-1) |
| `src/mctrader_data/adapters.py` | **변경 0** — Phase 0 V1/V2 실증 확인, 팩토리 완비 | — |

### §3.3 hub Phase 2 PR2 박제 (land_order 2, data PR1 MERGED 후)

| 파일 경로 | 변경 |
|----------|------|
| `docs/stories/MCT-187.md` | §8.5 Impl Manifest + §9 구현 요약 + §10 FIX Ledger + §11 PR2 박제 + frontmatter status COMPLETED |
| `docs/adr/ADR-031-data-domain-decoupling.md` | §D5 VERIFIED amendment box 확정 (git sha + grep 결과 + test 결과) |
| `scope_manifests/EPIC-data-domain-decoupling.yaml` | milestone 6/7 + MCT-187 COMPLETED |
| `.codeforge/counters.json` | MCT-187 status=COMPLETED + epic_milestone=6/7 |
| `CLAUDE.md` | MCT-187 COMPLETED 박제 + "신규 거래소 추가 = data 단독" 섹션 |
| `docs/retros/RETRO-MCT-187.md` | 신규 RETRO 박제 |
| `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` | §Story-6 추가 |

### §3.4 invariant test 설계 (AC-1 carrier)

`tests/test_multi_exchange_invariant.py` 5종 test:

```
TC-1  test_known_exchanges_registered
      adapters.KNOWN_EXCHANGES (또는 동등 접근법) bithumb + upbit 포함 확인.
      없으면: get_candle_provider("bithumb") + get_candle_provider("upbit") 호출 각 성공
      → ValueError 미발생 확인 (Phase 0 V1 팩토리 존재 재확인)

TC-2  test_unknown_exchange_raises_value_error
      get_candle_provider("mock") → ValueError("unknown exchange") 확인.
      "data 단독 활성화" = adapters.py 등록 없이 mock 거래소 미등록 상태 검증
      (D5: 임의 거래소는 등록 없이 engine/market-core 변경 없이 활성화 불가)

TC-3  test_new_exchange_activation_requires_only_adapters_registration
      (핵심 D5 invariant test)
      monkeypatch 를 사용해 get_candle_provider 내부에 "mock" branch 주입:
      adapters.py 코드 변경 없이 monkey-patch 로 mock 등록 → 호출 성공.
      engine 파일 변경 0 / market-core 파일 변경 0 grep 검증 포함.
      engine repo path / market repo path 존재 시 grep 수행, 없으면 skip (CI 환경 정합)

TC-4  test_engine_has_no_new_exchange_dependency
      (INV-1 carrier)
      `subprocess.run(["git", "show", "HEAD:pyproject.toml"], ...)` 또는
      `open(ENGINE_PYPROJECT_PATH)` → `mctrader-market-bithumb` 존재 확인 (MCT-188 finalize 전 잔존 정상).
      단, engine pyproject 에 새 거래소 어댑터 추가가 없음 검증 (본 Story scope 에서 추가한 것 없음).
      환경 부재 시 pytest.skip("engine repo unavailable") — CI-safe

TC-5  test_adapters_py_structure_invariant
      (INV-2 carrier)
      adapters.py import count 검증:
      `from mctrader_data.adapters import get_candle_provider, get_ws_stream`
      → 두 함수 모두 callable 확인
      + adapters.py 파일 자체 hash 또는 line count 변화 없음 (Phase 0 V1/V2 재확인)
      실제로는 callable 확인만으로 충분 (hash 고정 = over-constraint)
```

**채택 방식**: monkey-patch 기반 (importlib 동적 등록 대비 adapters.py 코드 변경 0 원칙 정합).
external 의존 없음 → unit test (testcontainers 불필요). pytest.monkeypatch fixture 사용.

---

## §4 공동 소유 파일 / 순서 의존

| 파일 | 소유 | 순서 |
|------|------|------|
| `compose.yml` | hub | Phase 1 PR 포함 (engine NAS env 제거 — 단순 라인 삭제, 설계 위험 0) |
| `docs/adr/ADR-031-*.md` | hub | Phase 1 outline → Phase 2 PR2 확정 |
| `tests/test_multi_exchange_invariant.py` | data | Phase 2 PR1 (land_order 1) — hub Phase 1 MERGED 후 |
| Phase 2 PR2 박제 | hub | data PR1 MERGED 후 |

의존성: hub Phase 1 PR MERGED → data Phase 2 PR1 → hub Phase 2 PR2.

---

## §5 hub Phase 1 scope 결정 (MCT-186 carry over)

engine `compose.yml` `engine` service NAS_MINIO_* env 제거 = **hub Phase 1 PR scope 포함**.

근거:
- compose.yml 편집 = hub 소유 (hub root) — hub Phase 1 PR 에 단순 라인 삭제로 포함 가능
- ADR-030 §NAS cred drop VERIFIED amendment = Phase 2 PR2 확정 박제 (ADR-030 본문 변경 0 — amendment box 추가만)
- data Phase 2 PR1 scope 와 파일 disjoint (compose.yml ↔ tests/test_multi_exchange_invariant.py)

---

## §6 Test Contract (§8 SSOT)

| 항목 | 내용 |
|------|------|
| test 파일 | `tests/test_multi_exchange_invariant.py` (신규, 5 TC) |
| test 종류 | unit (external 의존 없음, monkeypatch) |
| CI requirement | `uv run pytest tests/test_multi_exchange_invariant.py -v` → 5 PASS (0 FAIL 0 ERROR) |
| 회귀 gate | data full suite — 신규 실패 0 |
| Perf Baseline | N/A (performance 변경 0) |
| Testcontainers | 불필요 (external service 없음) |

---

## §3.6.1 gate v2 cross-Story reapply (MCT-182/183/184/185/186 SSOT 계승)

**D5 row ↔ 4 산출물 1:1 reconcile 체크리스트** (구현 lane 실행 전 ArchitectPL self-verify):

| 산출물 | D5 항목 | 정합 여부 |
|--------|---------|---------|
| `scope_manifests/EPIC-data-domain-decoupling.yaml` `§design_decisions.D5` | `option_chosen: data-only-extension-invariant` / `owner_story: MCT-187` | ✅ 정합 (현행 SSOT) |
| `ADR-031 §D5 amendment box` | `data-only-extension-invariant VERIFIED` / engine 변경 0 / market-core 변경 0 / adapters.py 등록 only | 구현 후 확정 |
| `Change Plan §3/§6` | invariant test 5 TC + runbook 3-step | ✅ 본 파일 |
| `MCT-187 Story §4 DELTA / §5 AC` | D5 내용 1:1 정합 | ✅ Story §4/§5 |

**TEST1** (post-Phase 1 PR): `grep -r "data-only-extension-invariant\|D5.*VERIFIED\|MCT-187" docs/adr/ADR-031-*.md` → amendment box 확인.
**TEST2** (post-Phase 2 PR2): `grep -r "engine 변경 0.*market-core 변경 0\|신규 거래소 추가" CLAUDE.md` → CLAUDE.md 섹션 확인.

---

## §3.6.2 박제 PR 5 체크리스트

Phase 2 PR2 LAND 전 완결 의무:

- [ ] `docs/stories/MCT-187.md` §8.5 Impl Manifest 작성 (DeveloperPL CFP-39)
- [ ] `docs/retros/RETRO-MCT-187.md` 신규 박제
- [ ] `docs/retros/EPIC-RESULTS-EPIC-data-domain-decoupling.md` §Story-6 추가
- [ ] `scope_manifests/EPIC-data-domain-decoupling.yaml` milestone 6/7 갱신
- [ ] `CLAUDE.md` MCT-187 COMPLETED + D5 invariant 섹션 신규
- [ ] `.codeforge/counters.json` MCT-187 status=COMPLETED + epic_milestone=6/7
- [ ] `ADR-031 §D5 VERIFIED` amendment box 확정 (git sha + grep 결과)
- [ ] `ADR-030 §NAS cred drop VERIFIED` amendment box 확정

---

## §3.6.3 Codex post-LAND 4 axis audit (Phase 2 PR1 MERGED 후)

| axis | 확인 항목 |
|------|----------|
| correctness | invariant test 5 TC 실 assertion 논리 정확성 (monkey-patch scope / ValueError match / grep 방식) |
| production-safety | adapters.py 변경 0 확인 (코드 변경 없어 production 영향 0) |
| SSOT 정합 | ADR-031 §D5 amendment box ↔ scope_manifest D5 ↔ Change Plan §3 1:1 정합 |
| test coverage | test_multi_exchange_invariant.py 5 TC 각 assertion 실효성 + 미포착 edge case |

---

## §7 add-new-exchange.md runbook 설계 (AC-2 carrier)

`docs/runbooks/add-new-exchange.md` 구조 (3-step):

```
# 신규 거래소 추가 runbook (D5 invariant — engine 변경 0 / market-core 변경 0)

## Step 1: Layer 1 어댑터 repo 신설
- `mctrader-market-<exchange>` 신규 repo 생성
- `adapter.py` — `CandleProvider` Protocol 구현 (`get_candle_provider` 반환 타입)
- `ws_client.py` — `WebSocketStream` Protocol 구현 (`get_ws_stream` 반환 타입)
- `pyproject.toml` — `mctrader-market` 의존 (Layer 0 SSOT)
- 검증: `mctrader-market.protocols.CandleProvider` / `OrderBookProvider` Protocol 준수

## Step 2: mctrader-data adapters.py 등록
- `src/mctrader_data/adapters.py` `get_candle_provider` + `get_ws_stream` 에 분기 추가:
  `if exchange == "<name>": from mctrader_market_<exchange>.adapter import ...`
- `pyproject.toml` — `mctrader-market-<exchange>` 의존 추가
- 검증: `uv run pytest tests/test_adapters.py tests/test_multi_exchange_invariant.py` PASS
- engine 변경 0 / market-core 변경 0 / ADR 0 (D5 invariant 영구)

## Step 3: data 수집/정규화 설정
- `collector.py` 수집 설정 — exchange 추가
- 신규 Symbol mapping + normalizer 등록
- 검증: 신규 거래소 tick 수집 smoke test

## 체크리스트 (merge 전)
- [ ] engine repo 변경 0 (PR diff engine/ 파일 없음)
- [ ] market-core repo 변경 0 (PR diff mctrader-market/ 파일 없음)
- [ ] ADR 변경 0 (ADR-031 §D5 invariant — 신규 거래소 추가 = ADR 불필요)
- [ ] `tests/test_multi_exchange_invariant.py` PASS (D5 invariant 회귀 0)
```

---

## §8 변경 순서 (land_order)

```
1. hub Phase 1 PR (mct-187-phase1-multi-exchange-invariant branch, 이미 생성)
   - Story + Change Plan + runbook + ADR-031 §D5 outline + ADR-030 carry over box
   - scope_manifest + counters (IN_PROGRESS) + CLAUDE.md 임시 + compose.yml NAS env 제거
   CI green → admin merge

2. data Phase 2 PR1 (branch: mct-187-phase2-data-invariant, 신규 생성)
   - tests/test_multi_exchange_invariant.py 5 TC
   data CI green → admin merge

3. hub Phase 2 PR2 (branch: mct-187-phase2-pr2-bagje, 신규 생성)
   - Story §8.5 + §9 + §10 + §11 + frontmatter COMPLETED
   - ADR-031 §D5 VERIFIED 확정 + ADR-030 NAS cred drop VERIFIED
   - scope_manifest 6/7 + counters COMPLETED + CLAUDE.md COMPLETED
   - RETRO-MCT-187.md + EPIC-RESULTS §Story-6
   CI green → admin merge
```

---

## §9 위험 / 에스컬레이션 기준

| 위험 | 대응 |
|------|------|
| adapters.py 변경 필요 발견 (Phase 0 V1/V2 실증 오류) | 즉시 ArchitectPL 보고 — code 변경 범위 재산정 |
| invariant test CI 실패 (test 자체 오류) | DeveloperPL 1차 진단 → ArchitectPL 최종 판정 |
| compose.yml NAS env 제거 후 engine CI 영향 발견 | 설계 원인 추정 → ArchitectPL 즉시 에스컬레이션 |
| §3.6.1 gate v2 reconcile 불일치 | ArchitectPL 인계 — 4 산출물 동반 정정 |
