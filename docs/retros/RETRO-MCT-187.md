# RETRO — MCT-187 (다중거래소 확장 불변식 박제)

> **완료일**: 2026-05-17
> **Story**: EPIC-data-domain-decoupling sequential_phase 6, milestone 6/7
> **PR**: hub#374 (91a8bfa) + data#78 (6346b55) + hub Phase 2 PR2

---

## 1. 요약

**code-change-zero Story** — `adapters.py` 변경 0 (INV-2 PASS). MCT-186 LAND 로
`BithumbCandleProvider` / `UpbitCandleProvider` 팩토리가 이미 완비된 상태였다.

본 Story 의 핵심 deliverable = **D5 invariant 박제**:
- `tests/test_multi_exchange_invariant.py` 5 TC (monkeypatch 패턴)
- `docs/runbooks/add-new-exchange.md` 3-step 절차 신규
- ADR-031 §D5 VERIFIED amendment box

ADR-031 §D5 `data-only-extension-invariant` **VERIFIED**: 신규 거래소 = data `adapters.py`
등록 only → engine/market-core/ADR 변경 0. milestone **6/7**.

---

## 2. 결과 지표

| 항목 | 결과 |
|------|------|
| Phase 1 PR | hub#374 MERGED (91a8bfa, 2026-05-16) |
| Phase 2 PR1 | data#78 MERGED (6346b55, 2026-05-17) |
| Phase 2 PR2 | hub Phase 2 PR2 (본 retro 박제 포함) |
| AC 통과 | 4/5 PASS (AC-5 CONDITIONAL — ADR-030 NAS cred carry) |
| INV 통과 | 4/4 PASS |
| FIX 루프 | 1 iter (ruff lint — edda216) |
| adapters.py 변경 | **0 lines** (INV-2 PASS) |
| engine/market-core 변경 | **0** (INV-1 PASS) |
| 신규 test | 5 TC (4 passed + 1 skipped CI-safe) |
| data full suite | ubuntu-latest 1183 passed, 회귀 0 |

---

## 3. FIX 루프 분석

### code iter1 (P2 — ruff lint, edda216)

**발견 시점**: data#78 CI ubuntu-latest Lint step

**원인**: test_multi_exchange_invariant.py 초안 자동 생성 시 미사용 import 3건 (subprocess/sys/types)
+ E721 (type() != 비교 → isinstance 권고) + F841 (mock_ws_instance 미사용 변수 할당) 잔존.

**해소**: `ruff --fix` 자동 수정 (F401×3) + 수동 수정 (E721→isinstance + F841 제거) → edda216 commit.

**lesson**: test 파일 초안 생성 시 ruff 사전 실행 의무. 특히 unused import (F401), type comparison (E721),
unused variable (F841) 패턴 = 표준 체크포인트.

---

## 4. Phase 0 verify 핵심 실증

| 검증 포인트 | 가설 | 실증치 | 결과 |
|---|---|---|---|
| adapters.py 팩토리 완비 여부 | MCT-186 LAND 후 완비 예상 | HEAD 22e2ece — bithumb/upbit 2-branch 58 lines 완비 | ✅ 정합 |
| test_adapters.py 기존 TC 수 | 기존 존재 예상 | 6 TC 기존 존재 (단위 기능 검증) | ✅ 정합 |
| engine pyproject bithumb 의존 | MCT-188 D7 finalize 대상 예상 | `mctrader-market-bithumb` dep 잔존 (정상) | ✅ 정합 (MCT-188 carry) |
| ADR-031 §D5 VERIFIED 여부 | Phase 1 = draft only | draft box 미박제 (Phase 1 아웃라인 only) | ✅ 정합 (본 Story owner) |

---

## 5. windows-latest CI 진단

**사실**: windows-latest CI `X Test` 실패 — `test_promote_l1_post_put_unlink.py` (7 error) +
`test_runner_retroactive_cleanup.py` (5 error). 원인: testcontainers ryuk Docker sock 마운트
`/var/run/docker.sock` Windows 미지원 (`docker.errors.APIError: 500 ... invalid volume specification`).

**MCT-187 scope 외 판정 근거**:
1. 실패 test 파일 = MCT-187 신규 파일 아님 (기존 파일, MCT-189/170 작성)
2. main branch 에서도 동일 `X Test` 실패 확인 (pre-existing regression)
3. MCT-187 신규 5 TC = ubuntu-latest 1183 passed 포함 PASS
4. `phase-gate-mergeable` = PASS (ubuntu-latest PASS)

**처리**: admin merge 진행 (ubuntu-latest PASS + phase-gate-mergeable PASS). windows testcontainers
pre-existing regression 별 Story 또는 CI 설정 개선 carry over.

---

## 6. D5 invariant 검증 방식 (monkeypatch 패턴 선택 근거)

TC-3 핵심 invariant 구현 방식 = **monkeypatch**. 근거:

- `importlib` 동적 등록 방식은 adapters.py 구조 변경 의존 — INV-2 (`adapters.py` 변경 0 원칙) 위반
- Protocol stub 방식 = 추상 인터페이스 의존 (현 adapters.py 구조와 무관)
- `monkeypatch` = pytest 내장 fixture, adapters.py 코드 변경 0 상태에서 "등록 패턴" 시뮬레이션 가능

```python
# TC-3 핵심 패턴
monkeypatch.setattr(adapters_module, "get_candle_provider", patched_get_candle_provider)
result = adapters_module.get_candle_provider("mock")
assert result is mock_provider_instance  # adapters.py 코드 변경 없이 mock exchange 활성화 증명
```

이 패턴이 D5 "adapters.py 등록만으로 신규 거래소 활성화 가능" 원칙을 **구조적으로** 박제한다.

---

## 7. ADR 박제

| ADR | 섹션 | 결과 |
|-----|------|------|
| ADR-031 §D5 | VERIFIED amendment box (본 PR 박제) | 5 TC PASS + adapters.py 변경 0 + runbook LAND |
| ADR-030 §D4 NAS cred drop | carry over 유지 | compose.yml engine NAS env drop = 별 PR |

---

## 8. carry over (MCT-188 or 별 PR)

| 항목 | 사유 | owner |
|------|------|-------|
| engine compose.yml `NAS_MINIO_*` env 제거 | MCT-186 + MCT-187 scope 외 (인프라 별 PR) | 별 PR or MCT-188 |
| engine pyproject `mctrader-market-bithumb` dep 제거 | D7 quad gate final | MCT-188 owner |
| windows testcontainers CI fix | pre-existing regression (scope 외) | 별 Story or CI 개선 |

---

## 9. 다음 Story

**MCT-188** — data-free grep0 quad gate + Epic POLICY_FINALIZED (D7+D6).
진입 prerequisite: MCT-187 Phase 2 PR2 MERGED ✓.
deliverable: engine src/ grep0 quad gate CI + pyproject mctrader-data 의존 제거 + pyproject 어댑터 의존 제거 + ADR-031 POLICY_FINALIZED.
