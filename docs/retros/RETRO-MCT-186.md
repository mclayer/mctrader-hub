# RETRO — MCT-186 (engine realtime cutover + exchange-adapter 제거)

> **완료일**: 2026-05-17
> **Story**: EPIC-data-domain-decoupling sequential_phase 5, milestone 5/7
> **PR**: hub#370 (3fc9c1f) + engine#60 (773b270) + hub Phase 2 PR2

---

## 1. 요약

mctrader-engine 의 `mctrader_market_bithumb` 직접 import **5곳 5파일 전부 제거** 완료.
engine 은 이제 Redis Stream (`market:tick:{exchange}:{symbol}`) 에서 정규화된 `TickRowV1_1`
(market-core Layer 0 SSOT) 만 소비하는 **exchange-agnostic pure consumer** 다.

ADR-031 §D4 `subscribe-normalized-stream` 결정 **VERIFIED** (engine#60 AC-1 grep0 PASS).

---

## 2. 결과 지표

| 항목 | 결과 |
|------|------|
| Phase 1 PR | hub#370 MERGED (3fc9c1f, 2026-05-16T17:53:38Z) |
| Phase 2 PR1 | engine#60 MERGED (773b270, 2026-05-16T21:52:47Z) |
| Phase 2 PR2 | hub#TBD (본 retro 박제 포함) |
| AC 통과 | 7/7 PASS |
| INV 통과 | 6/6 PASS |
| FIX 루프 | design 1 iter (code 0) |
| grep0 결과 | `mctrader_market_bithumb` = **0건** (5곳 5파일 전부 제거) |
| 신규 파일 | 3 (types.py + redis_subscriber.py + test_realtime_subscriber.py) |
| 삭제 파일 | 1 (ws_wrapper.py — WsWrapperStream + StreamExhaustedError) |
| 신규 test | 4 (testcontainers integration, ALL PASS) |

---

## 3. FIX 루프 분석

### design iter1 (P0 — §3.2.4b, cli.py StreamExhaustedError)

**발견 시점**: 설계 리뷰 (Phase 1 Change Plan 검토)

**원인**: Change Plan 초안이 ws_wrapper.py 삭제를 명시했으나 `cli.py:442` 의
`StreamExhaustedError` import + `cli.py:597` catch block 의 삭제를 scope 에서 누락.
ws_wrapper.py 삭제 → dangling import → runtime `ImportError` (CI에서는 사전 통과 실패).

**판정**: 설계 원인 (Change Plan scope 정의 누락). §3.2.4b 패턴.

**해소**: Change Plan §1.5 `cli.py modification` 항목 추가 → 설계리뷰 CONDITIONAL_PASS
→ code iter1 직접 PASS (FIX 0).

**lesson**: WS adapter 삭제 시 downstream catch 블럭 포함 전수 caller 검색 의무.
`grep -rn "StreamExhaustedError"` = Phase 0 추가 체크포인트 (MCT-186 §3.2.4b 박제).

---

## 4. Phase 0 verify 핵심 실증

| 검증 포인트 | 가설 | 실증치 | 정정 |
|---|---|---|---|
| bithumb import 위치 수 | 세션 "~5곳 5파일" | **정확 5곳 5파일** | 정정 없음 (V3 실증) |
| R2 MCT-41 교차 검증 | MCT-43~47 active branch | **0건** (active branch 없음) | ZERO RISK 확인 |
| cli.py `StreamExhaustedError` | Change Plan 초안 미포함 | **2곳 (import + catch block)** | Phase 0 누락 → FIX iter1 정정 |
| engine `OrderbookSnapshot` origin | bithumb `_BaseEvent` 상속 | **engine-local dataclass 신설** | V7/V8 Phase 0 정정 (INV-3 영구) |

---

## 5. 설계 원칙 reapply

### MCT-185 LAND 패턴 준수

- `TickRowV1_1.model_validate_json()` → XREAD payload 역직렬화 (동일 패턴)
- XREAD BLOCK=1000ms count=100 → MCT-185 publisher window 정합
- `market:tick:{exchange}:{symbol}` stream key → ADR-030 §D15 namespace 정합

### MCT-180 testcontainers 패턴 재사용

- `testcontainers.redis.RedisContainer` → `test_realtime_subscriber.py` 4 test
- boundary test = XADD+XREAD round-trip / max_events / malformed_payload_skipped / ctx_manager_guard

### MCT-170/177/178/179/180 Phase 0 verify 교훈 6회째 reapply

- cli.py StreamExhaustedError = 7회째 cross-file downstream impact 누락 사례
- 파일 삭제 시 `grep -rn <symbol>` 전수 검색 의무 재확인

---

## 6. ADR 박제

| ADR | 섹션 | 결과 |
|-----|------|------|
| ADR-031 §D4 | VERIFIED amendment box | engine#60 773b270 + grep0 + integration test |
| ADR-030 §NAS cred drop | carry over 명기 | compose.yml engine NAS env drop = MCT-187 or 별 PR |

---

## 7. carry over (MCT-187 or 별 PR)

| 항목 | 사유 | owner |
|------|------|-------|
| engine compose.yml `NAS_MINIO_*` env 제거 | MCT-186 Phase 2 PR1 scope 외 (compose.yml 편집 미포함) | MCT-187 or 별 PR |
| pyproject.toml `mctrader-market-bithumb` dep 제거 | Change Plan line 69 — D7 quad gate final | MCT-188 owner |

---

## 8. 다음 Story

**MCT-187** — 다중거래소 확장 불변식 박제 (D5+D6).
진입 prerequisite: MCT-186 Phase 2 PR2 MERGED ✓.
carry over: ADR-030 compose.yml engine NAS env drop.
