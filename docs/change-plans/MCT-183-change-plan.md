# Change Plan — MCT-183 Layer 2 Read 도메인 Relocation → mctrader-data (EPIC-data-domain-decoupling Story-2)

- **Story**: MCT-183
- **Status**: design-review-ready (Iteration 1 — ArchitectPLAgent 통합 검수 PASS 2026-05-16)
- **Story file**: [`docs/stories/MCT-183.md`](../stories/MCT-183.md)
- **ADR**: [ADR-029](../adr/ADR-029-tier-promotion-single-source.md) MCT-183 amendment box (io reader 6 module relocated + engine NAS 직독 폐기 **예고**, 실 confirm=MCT-185) · [ADR-027](../adr/ADR-027-cold-tier-object-storage-nas-minio.md) MCT-183 amendment box (io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2) · respects [ADR-031](../adr/ADR-031-data-domain-decoupling.md) §D2 (io-relocate 절반 진행, §D2 VERIFIED = MCT-185 cutover 후)
- **Target repo**: `mctrader-hub` (Phase 1 docs) + `mctrader-data` + `mctrader-engine` (Phase 2 cross-repo code)
- **Epic**: EPIC-data-domain-decoupling — sequential_phase 2 (strangler-fig 2단계)

## 1. 입력 요약 (Story §1 verbatim, immutable)

> "data 영역은 mctrader와 아예 분리하고 싶다. 표준 mctrader에는 호출용 interface, data에는 그를
> 처리하는 REST API가 있는게 좋겠다. 프로젝트 구조는 mctrader-hub에서도 구현할 수 있고
> mctrader-data 단독으로도 필요사항을 반영할 수 있어야겠다."

EPIC-data-domain-decoupling Story-2. 본 Story = strangler-fig **2단계** — Layer 2 (mctrader-data
= DATA-STORAGE 영역 단독 소유) read 도메인 정렬. engine `src/mctrader_engine/io/` 6 module
(`tier_reader`/`reader_cache`/`endpoint_router`/`dr_mode`/`cold_reader`/`l1_reader`, **dead-in-prod
— src caller 0**) + `tests/io/` 7 test 를 mctrader-data 로 byte-equivalence 물리 이전, engine
측 dead-in-prod 자산 안전 삭제 + ADR-029/027 amendment box 박제. cold-read 실경로 cutover =
MCT-185 owner (본 Story 범위 외).

## 2. 현재 구조 (CodebaseMapperAgent 산출 — verified-via git grep/show, origin/main HEAD 2026-05-16)

### 2.1 핵심 자산 인벤토리

| 자산 | 경로 (origin/main HEAD) | verified fact | 본 Story 와 관계 |
|------|------|---------------|-------------------|
| io/ 6 module | `mctrader-engine/src/mctrader_engine/io/{cold_reader,dr_mode,endpoint_router,l1_reader,reader_cache,tier_reader}.py` | `git ls-tree origin/main` 실측 6 module + `__init__.py`. top-level import = stdlib only (`__future__`/`hashlib`/`logging`/`time`/`threading`/`os`/`math`/`uuid`/`dataclasses`/`datetime`/`pathlib`/`collections`/`typing`) | **data 물리 이전 + engine 삭제** |
| io/__init__.py | `mctrader-engine/src/mctrader_engine/io/__init__.py` | 13 심볼 export (`__all__`: CacheEntry/CacheFlushResult/ColdReader/DRMode/EndpointFlipResult/EndpointRouter/GraceModeState/L1ReadResult/L1Reader/ReadResult/ReaderCache/TierReadResult/TierReader). 6 `from mctrader_engine.io.X import` self-import (line 17-26) | **data 측 동일 export — self-import 6줄만 재지정** |
| io/ 6 module 내부 cross-import | (검증) | **0건** — 6 module 서로 `from/import mctrader_engine` 매치 0 (각 module top import = stdlib only). `io/__init__.py` 만 6 module import | **byte-equiv relocate 시 6 module 본문 import 재지정 불요** |
| **reader_cache.py stats() producer-wiring 블록** | `io/reader_cache.py:339-348` | `stats()` (line 319) 메서드 본문 내 producer-wiring 블록 = 주석 1줄(339) + `from mctrader_engine.metrics import set_reader_cache_hit_ratio as _set_hit_ratio` + `set_reader_p99_ms as _set_p99_ms` lazy import 6줄(340-345 multi-line ×2) + 빈줄(346) + `_set_hit_ratio`/`_set_p99_ms` 호출 2줄(347-348) (FIX-MCT-180 engine#55 P1 producer wiring). io/ 6 module 中 **단 1곳만** 비-io.* mctrader_engine 의존 | **byte-equiv 예외 1건 — §3.5 채택안 A 외부 import 없는 내부 no-op 블록 치환 (range 339-348)** |
| engine metrics setter | `mctrader-engine/src/mctrader_engine/metrics.py:43-79` | `nas_reader_cache_hit_ratio` Gauge (line 43) / `nas_reader_p99_ms` Gauge (line 48) / `set_reader_cache_hit_ratio` (line 72) / `set_reader_p99_ms` (line 77). **data 측 동등 Gauge 부재** (data src/ grep 0건) | reader_cache.py stats() producer wiring 대상 (data 측 부재 — §3.5) |
| tests/io/ 7 test | `mctrader-engine/tests/io/{test_dr_mode,test_endpoint_cutover,test_l1_reader,test_reader_cache_budget,test_reader_cache_flush,test_reader_perf,test_tier_reader}.py` + `__init__.py` | 7 test 전수 `from mctrader_engine.io.*` import 확증. `test_reader_cache_flush.py:215` = `from mctrader_engine.metrics import nas_reader_cache_hit_ratio, nas_reader_p99_ms` (함수 내 lazy, io/ 외 의존 1건) | **data 이전 + import path 재지정, test_reader_cache_flush engine.metrics = graceful skip 정합** |
| engine src/ io/ 호출자 | `mctrader-engine/src/` (io/ 제외) | **0건** (3-modal git grep origin/main: (A) `from/import mctrader_engine.io` io/제외 = 0 rc=1 / (B) bare 심볼 `TierReader\|ReaderCache\|EndpointRouter\|DRMode\|ColdReader\|L1Reader` io/제외 = 0 rc=1 / (C) 전 src/ `mctrader_engine.io` = io/__init__.py 6 self-import 만) | **dead-in-prod 안전 제거 근거 (삭제 후 import 깨짐 0)** |
| data io/ 부재 | `mctrader-data/src/mctrader_data/io/` | `git ls-tree origin/main` = **ABSENT**. data src/ io reader 심볼 (`TierReader\|EndpointRouter\|DRMode\|L1Reader`) 충돌 grep = 0건 (rc=1). data `tests/io/` = ABSENT | **신규 io/ 배치 충돌 0** |
| data compactor ReaderCache 동명 | `mctrader-data/src/mctrader_data/compactor/reader_cache.py:19` | `@runtime_checkable class ReaderCache(Protocol)` (get/put/invalidate — D7 reader cache interface ADR-029 D7=A 계약). LRUReaderCache 구현체 동거 | **무변경 (INV-6) — 다른 namespace (`compactor.reader_cache` vs 신규 `io.reader_cache`)** |

### 2.2 결합도 분석 (RefactorAgent + CodebaseMapper 협업)

- **io/ 6 module → mctrader_data/mctrader_market 의존: 0** (Story §0 V5 정합 — top-level stdlib only)
- **io/ 6 module 간 cross-import: 0** — 6 module 서로 import 안 함. `io/__init__.py` 만 6 module
  import (line 17-26). → byte-equiv relocate 시 **6 module 본문 import 재지정 불요**, `io/__init__.py`
  6 self-import 줄만 `from mctrader_engine.io.X` → `from mctrader_data.io.X` 재지정
- **io/ → engine 비-io.* 의존: 1건** (`reader_cache.py:339-348` stats() producer-wiring
  블록 = 주석 + `from mctrader_engine.metrics import set_reader_cache_hit_ratio,
  set_reader_p99_ms` lazy import + `_set_*` 호출 2줄). 나머지 5 module + reader_cache.py
  339-348 외 = 완전 stdlib only. **byte-equivalence relocate 시 data → engine 역의존
  발생 (INV-2 위반 + 순환 위험) → §3.5 채택안 A 외부 import 없는 내부 no-op 블록 치환 필수**
- **data compactor.reader_cache.ReaderCache(Protocol) ↔ 신규 io.reader_cache: namespace
  분리, 물리 충돌 0** — `mctrader_data.compactor.reader_cache` (Protocol 추상) vs
  `mctrader_data.io.reader_cache` (LRU+TTL 구현체). compactor Protocol 무변경 (INV-6)

### 2.3 변경 영향 지도

| 영향 자산 | 영향 종류 | 보존/대체 |
|----------|----------|----------|
| io/ 6 module 코드 본문 | **무변경 (byte-equivalence)** | 물리 이동 — 재구현 0 (INV-1) |
| `io/__init__.py` 6 self-import 줄 | **재지정** | `from mctrader_engine.io.X` → `from mctrader_data.io.X` (13 심볼 export 동일 유지) |
| `reader_cache.py:339-348` stats() producer-wiring 블록 | **no-op 블록 치환 예외 (1건, §3.5 채택안 A)** | data 측 외부 import 없는 내부 no-op 주석 블록 치환 (engine 원본 10줄 → data 3줄 주석. `try/except ImportError` 회피 — §8.1 INV-2 grep gate `from mctrader_engine`/`from mctrader_data` 무위반. dead-in-data — Gauge 실 emit 재배선 = MCT-185) |
| tests/io/ 7 test | **import path 재지정 + green** | `from mctrader_engine.io.*` → `from mctrader_data.io.*` (로직 byte-equiv, INV-4). test_reader_cache_flush.py:215 engine.metrics lazy = graceful skip 정합 |
| engine io/ 6 module + `__init__.py` + tests/io/ | **물리 삭제** | dead-in-prod 안전 제거 (src caller 0, INV-3) — io 패키지 소멸 |
| data compactor.reader_cache.ReaderCache(Protocol) | **무변경 (INV-6)** | 다른 namespace — 비접촉 |
| ADR-029/027 본문 | **amendment box 추가만** | io reader relocated 박제 + engine NAS 직독 폐기 예고 (본문 결정 무변경) |

## 3. 도입할 설계 (RefactorAgent 산출 + ArchitectAgent 통합)

### 3.1 4-Layer Layer 2 read 도메인 정렬 (high-level)

```
 mctrader-data (Layer 2 — DATA-STORAGE 영역 단독 소유)
   src/mctrader_data/
   ├── io/                       ◀ NEW 서브패키지 (← engine io/ 6 module byte-equiv 이전)
   │   ├── __init__.py           13 심볼 export (6 self-import → mctrader_data.io.X 재지정)
   │   ├── tier_reader.py        facade orchestration (MCT-170, byte-equiv)
   │   ├── reader_cache.py       LRU+TTL+byte budget (MCT-154+170, byte-equiv,
   │   │                           stats() producer-wiring 블록 339-348 → §3.5 채택안 A no-op 블록)
   │   ├── endpoint_router.py    env endpoint + atomic flip + 7d grace (MCT-154, byte-equiv)
   │   ├── dr_mode.py            DR state machine CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER (MCT-170)
   │   ├── cold_reader.py        NAS cold L2/L3 read API (MCT-154, byte-equiv)
   │   └── l1_reader.py          L1 specialized read (MCT-170, byte-equiv)
   ├── compactor/reader_cache.py = ReaderCache(Protocol) (무변경 — 다른 namespace, INV-6)
   └── tests/io/                 ◀ NEW (← engine tests/io/ 7 test, import path 재지정)
        상태: dead-in-prod → dead-in-data (production wiring = MCT-185)
 mctrader-engine (Layer 2' — PURE CONSUMER 진행)
   └── src/mctrader_engine/io/ 6 module + __init__.py + tests/io/ 7 test = 물리 삭제
        (src caller 0 = 삭제 후 import 깨짐 0, io 패키지 소멸)
 mctrader-hub (ADR governance):
   ADR-029 MCT-183 amendment box ← io reader 6 module relocated + NAS 직독 폐기 예고
   ADR-027 MCT-183 amendment box ← io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to data Layer2
```

### 3.2 namespace 분리 확정 (V6 동명 risk 해소 — SSOT 박제)

- 신규 io/ 6 module = **`src/mctrader_data/io/` 서브패키지** (`mctrader_data.io.*`)
- data 기존 `src/mctrader_data/compactor/reader_cache.py:19` `@runtime_checkable class
  ReaderCache(Protocol)` (get/put/invalidate — compactor 측 추상, ADR-029 D7=A 계약) =
  **무변경 (INV-6)**. 신규 `mctrader_data.io.reader_cache.ReaderCache` = LRU+TTL 구현체
  (engine 원본 byte-equiv). **다른 namespace → 물리 충돌 0** (`mctrader_data.compactor.reader_cache`
  vs `mctrader_data.io.reader_cache`). 동명 모듈 혼동 risk = 서브패키지 명시 배치로 해소
- data `src/mctrader_data/io/__init__.py` public API = engine 원본 13 심볼 byte 동일
  (`__all__` 동일 유지 — contract pin)

### 3.3 import path 재지정 규칙 (RefactorAgent 채택 — byte-equivalence 보존)

- **io/ 6 module 본문**: import 재지정 **불요** (§2.2 — 6 module 간 cross-import 0건, 각
  module stdlib only). 코드 본문 byte-for-byte 이동 (재구현 0, INV-1)
- **`io/__init__.py`**: 6 self-import 줄만 재지정 (engine 원본 13 심볼 export 동일):
  ```python
  # src/mctrader_data/io/__init__.py (engine 원본 byte-equiv, 6 import 줄만 path 재지정)
  from mctrader_data.io.cold_reader import ColdReader, ReadResult       # was: mctrader_engine.io.cold_reader
  from mctrader_data.io.dr_mode import DRMode
  from mctrader_data.io.endpoint_router import EndpointFlipResult, EndpointRouter, GraceModeState
  from mctrader_data.io.l1_reader import L1ReadResult, L1Reader
  from mctrader_data.io.reader_cache import CacheEntry, CacheFlushResult, ReaderCache
  from mctrader_data.io.tier_reader import TierReadResult, TierReader
  __all__ = [...]  # engine 원본 13 심볼 byte 동일
  ```
- **tests/io/ 7 test**: `from mctrader_engine.io.*` → `from mctrader_data.io.*` import path
  재지정만 (테스트 로직 byte-equivalence, INV-4)

### 3.4 io/__init__.py 삭제 처리 확정 (engine io 패키지 소멸)

engine `src/mctrader_engine/io/` 전체 (6 module + `__init__.py`) + `tests/io/` (7 test +
`__init__.py`) = **물리 삭제** (`git rm -r src/mctrader_engine/io/ tests/io/`). `io/__init__.py`
= 6 module re-export only → 6 module 삭제 시 동반 삭제 (**빈 패키지 잔존 아님** — src caller
0 = dangling import 0, §0 V3 정합. 빈 패키지 잔존은 무의미 + grep0 noise).

### 3.5 byte-equivalence 예외 1건 — reader_cache.py stats() producer-wiring 블록 (Change Plan SSOT, P0-3 채택안 = A)

> **R1 가드 사전 차단 발견 (설계 lane, 코드 작업 전)** — Story §3.4 + ADR-029 MCT-183
> amendment box 정합. docker-stack Phase 0 verify gap 6회 + MCT-179→180 producer-path
> desync 동형의 **7회째 사전 차단** (MCT-182 R1 가드 패턴 계승). 설계리뷰 iter1 P0-3
> (executable design gap) 해소 — git 실측 정확 hunk 재대조 + 구현 가능 단일 해소안 확정.

**fact (verified-via `git show origin/main:src/mctrader_engine/io/reader_cache.py | nl
-ba` 2026-05-16, P0-3 정확 hunk 재실측)**: `io/reader_cache.py:319 stats()` 메서드
본문 내 producer-wiring **블록 = line 339-348** (주석 1줄 + import 6줄[340-345,
multi-line `from ... import (\n    X as Y,\n)` 형식 ×2] + 빈줄 1줄[346] + 호출 2줄
[347-348]):
```python
339:        # producer wiring (FIX-MCT-180 engine#55 P1): live 값 → Prometheus Gauge.
340:        from mctrader_engine.metrics import (
341:            set_reader_cache_hit_ratio as _set_hit_ratio,
342:        )
343:        from mctrader_engine.metrics import (
344:            set_reader_p99_ms as _set_p99_ms,
345:        )
346:
347:        _set_hit_ratio(hit_ratio)
348:        _set_p99_ms(p99_ms)
```
- 출처 = FIX-MCT-180 engine#55 P1 producer wiring (MCT-180 LAND). `set_reader_*` =
  engine `metrics.py:72/77` 정의. data 측 동등 Gauge/setter **부재** (data src/ grep 0건)
- Story §0 V5 (top-level grep) 미포착 — 본 lazy import 는 stats() **함수 본문 내부** (Story
  §0 V5 가설 stdlib only ↔ 실상 stats() lazy engine.metrics 의존 **부분 불일치**, 설계
  lane 사전 발견)
- **이전 §3.5 초안 결함 (P0-3 설계리뷰 지적, 정정 대상)**: ① "lazy import 2줄(340/343)
  만 no-op" 명세는 import만 치환 시 line 347/348 `_set_hit_ratio`/`_set_p99_ms` 호출이
  **NameError** (실 hunk = import+호출 4 statement, "2줄" 과소 산정). ② `try: from
  mctrader_data.metrics import ...; except ImportError: pass` 안은 §8.1 INV-2 grep
  gate(data io/ `from mctrader_data` == 0건) 에 **걸림** + "2줄 외 0" diff 초과 (블록화).
  → 구현 불가 명세 (MCT-180 ESCALATE 동형) → 채택안 (A) 로 단일화.

**설계 결정 (P0-3 채택안 = (A) — 외부 import 없는 내부 no-op 블록 치환, scope 최소 +
Layer2 자족 INV-2 순수성)**:

byte-equivalence relocate 시 `mctrader_data.io.reader_cache.stats()` 가
`from mctrader_engine.metrics import ...` lazy import → mctrader-data → mctrader-engine
역의존 (Layer2 자족 INV-2 위반 + 순환 위험). **해소 = producer-wiring 블록(339-348)
전체를 외부 import 없는 내부 no-op 블록으로 치환** (data.metrics 신설 회피 — 채택안 (B)
는 MCT-185 scope 침범 소지로 기각):

- **정정 hunk (data#N 측 reader_cache.py — engine 원본 line 339-348 → data no-op 블록)**:
  ```python
  # producer-wiring no-op (MCT-183 relocate: engine.metrics 외부 의존 제거 —
  # Layer2 자족 INV-2. dead-in-data → stats() production caller 0, Gauge 실 emit
  # 재배선 = MCT-185 cold-read cutover owner. set_reader_* setter 부재 시 no-op).
  ```
  (engine 원본 10줄[339-348 주석+import 6+빈줄+호출 2] → data 측 3줄 주석 no-op 블록.
  외부 import 0 → §8.1 INV-2 grep gate `from mctrader_data`/`from mctrader_engine`
  무위반. stats() 의 `hit_ratio`/`p99_ms` 계산 + dict return = **무변경** — Gauge
  set 호출만 제거, 반환값 byte-equivalence 보존)
- **dead-in-data 라 동작 영향 0**: data 측 io/ = production caller 0 (stats() 실호출 0).
  Gauge set 제거 = NFR verdict 무영향 (§8 INV-4 — `test_reader_perf` 는 hit_ratio/p99
  직접 계산, Gauge 비의존). Gauge 실 emit 재배선 = **MCT-185 (cold-read cutover) owner**
  (data REST 측 metric 재정의 — scope 경계, ADR-029 MCT-183 amendment box 정합)
- **INV-1 byte-equivalence 예외 명문화 (P0-3 정정 — "2줄" → "producer-wiring 블록")**:
  io/ 6 module 中 reader_cache.py stats() **producer-wiring 블록 (engine 원본 line
  339-348, 10줄)** 만 data no-op 블록 치환 = byte-equivalence "import-path-재지정-only"
  의 producer-wiring 예외 1건. 정확 diff hunk = §8.2 허용 명문 (line 339-348 range,
  INV-2 grep 무위반 — 외부 import 0). 나머지 전 코드 본문 (5 module + reader_cache.py
  의 339-348 외 전체) byte-for-byte 보존
- `tests/io/test_reader_cache_flush.py:215` `test_stats_emits_prometheus_gauges` =
  engine.metrics Gauge 검증 test → data 측 **로직 정정 동반 의무** (engine.metrics
  부재 + data stats() no-op → Gauge assert 불가). 정정 = `pytest.mark.skip(reason=
  "MCT-183 relocate: Gauge emit = MCT-185 cutover owner, dead-in-data no-op")` 또는
  no-op 후 `stats()` 반환 dict 만 assert (hit_ratio/p99 값 검증 유지 — cold reader
  한정 metric MCT-180 §D8 contract 정합, paper daemon 미적용 박제 유지). NFR test
  `test_reader_perf` = engine.metrics 비의존 (직접 계산) → 이전 동등 verdict 보존 (INV-4)
- **P0-3 회귀 test 추가 의무 (§8 신규)**: `tests/io/test_reader_cache_budget.py` 또는
  신규 `tests/test_io_stats_no_engine_dep.py` — "engine.metrics 미설치(부재) 환경에서
  `ReaderCache.stats()` 정상 dict 반환 (NameError/ImportError 0) + hit_ratio/p99 값
  정확" 회귀 (clean subprocess `sys.modules` 에 `mctrader_engine` 부재 assert). data
  측 stats() no-op 후 외부 의존 0 실증 (INV-2 + P0-3 executable 검증)

### 3.6 D-row ↔ scope_manifest 1:1 reconcile (MCT-179 lesson reapply — R1 가드)

> MCT-182 D-row 7/7 reconcile 패턴 계승 + PMO-AUDIT-MCT-182 §4 cross-document SSOT 정합
> forcing function self-discipline. 본 Story 4 산출물 (Story §본문 / scope_manifest /
> ADR-029·027 amendment box / Change Plan §3) D2 row 기준 전수 1:1.

| 항목 | scope_manifest | ADR amendment box | Change Plan | Story | reconcile |
|------|----------------|-------------------|-------------|-------|-----------|
| D2 option | `§design_decisions.D2.option_chosen: io-relocate + cold-read-behind-REST` | ADR-029 box "io reader 6 module relocated (D2 io-relocate 절반)" | §3.1 io relocate | §2 목표 D2 | ✅ 1:1 |
| D2 owner | `§design_decisions.D2.owner_story: MCT-183 (io relocate) + MCT-185 (cold-read cutover)` | ADR-029 box "실 NAS 직독 폐기 confirm = MCT-185" | §3.5 "Gauge 재배선 = MCT-185 owner" | §2 비목표 (cutover=MCT-185) | ✅ 1:1 |
| ADR-029 amend | `§planned_adrs.amendments[0]` ADR-029 `owner: MCT-183 (relocate) + MCT-185 (cutover confirm)` | ADR-029 MCT-183 amendment box (relocated + 폐기 예고) | §10 ADR 판단 | §0 V7 / §4.3 | ✅ 1:1 |
| ADR-027 amend | `§planned_adrs.amendments[1]` ADR-027 `section: io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2` / `owner_story: MCT-183 (io reader 6 module relocate)` | ADR-027 MCT-183 amendment box 헤더 "io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2 소유" | §10 ADR 판단 | §4.3 row + frontmatter related_adrs "io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2" | ✅ 1:1 (P0-1 reconcile — 4 산출물 6-module 명시 list **byte 동일**, +N 괄호 회피 정직 판정. endpoint_router/dr_mode = ADR-027 §D9 명시 module, 나머지 4 = io/ 묶음 relocate) |
| MCT-183 decisions | `§story_decision_matrix.MCT-183.decisions: [D2, D6]` | ADR-029/027 box D2(relocate)+D6(amendment) | §1 D2+D6 | frontmatter `decisions_implemented: [D2, D6]` | ✅ 1:1 |
| MCT-183 cross_repo | `§story_decision_matrix.MCT-183.cross_repo` (hub/data/engine 3 entry) | — | §9.1 land_order | §4.4 DELTA | ✅ 1:1 |
| land_order | `§story_decision_matrix.MCT-183.land_order: hub Phase1 → data#N → engine#N → hub Phase2 PR2` | — | §9.1/§11.3 | §4.4 land_order | ✅ 1:1 |

**reconcile verdict**: 4 산출물 D2 row 기준 **전수 1:1 정합** (7/7 row). MCT-182 D-row
7/7 reconcile + PMO-AUDIT-MCT-182 §4 forcing function self-discipline reapply. 1차 FIX
발생 시 정정 산출물 list ↔ 4 산출물 동반 reconcile 체크리스트 의무 (MCT-182 설계리뷰
iter1 F-2 scope_manifest 단독 정정·Change Plan 동반 누락 → 구현리뷰 carry 한 cross-document
desync 동형 사전 차단).

### 3.6.1 ADR-027 amendment canonical string + 잔존 축약 grep gate (MCT-179/182/183 desync 동형 영구 차단 forcing function)

> **설계리뷰 iter3/3 (RESET) P0-1-residual-2 + P0-2-gate 정정 (수동 "지정 목록"
> reconcile 의 구조적 한계 → repo-wide glob-scope + 변형포괄 pattern 자기검증 gate 로
> 영구 차단)**: iter1→2→3 매 iter ArchitectPL 지정 산출물만 정정 → Codex 넓은 grep 이
> 미지정 1곳 추가 적발 (cross-document SSOT desync **5회 누적**, MCT-179→182→183
> iter1→2→3). 근본 = 수동 "지정 목록" 방식 자체가 누락 구조적 + 구 gate 가 조사(`로`)
> /따옴표 고정이라 ADR-031:139 변형(조사/따옴표 없음) 놓침. **본 RESET 회귀 = 지정
> 목록 탈피 — glob-scope + 변형포괄 regex + self-verify 로 forcing function 완전 박제.**

**canonical string (ADR-027 MCT-183 amendment 전 박제 위치 SSOT — byte 동일 의무)**:
```
io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2
```

**잔존 축약 grep gate v2 (glob-scope + 변형포괄 — data#N 착수 전 + DesignReview/
CodeReview lane verdict 직전 의무 검증, 실 stale != 0 시 P0 차단)**:

```bash
# scope = glob 기반 (지정 목록 탈피 — 본 Epic 권위 SSOT 전수 + 차후 누락 방지):
#   docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md
#   scope_manifests/EPIC-data-domain-decoupling.yaml
# pattern = 변형포괄 regex (조사 optional + 따옴표 optional + 구분자 [ +/] 변형 +
#   relocat|이전 ko/en 동시 포괄). ADR-027 MCT-183 amendment 의 2-module 축약 잔존
#   == 0 검증 (canonical 6-module list 동반 시 endpoint_router~dr_mode~relocat 거리
#   >40 → 자연 미매치 = false positive 0, self-verify 검증됨).
grep -rnE "endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat|이전)" \
  docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md \
  scope_manifests/EPIC-data-domain-decoupling.yaml \
  | grep -ivE "io reader 6 module \(endpoint|FIX Ledger|grep gate|gate 패턴|grep -rnE|P0-1-residual|cross-document-ssot-desync|design-review (iter|RESET)|tier_reader/reader_cache/endpoint_router/dr_mode|\(tier_reader/reader_cache|relocated to mctrader-data Layer2\`|TEST[12]|구 pattern|canonical string"
# 예외 필터 보강 (iter3 RESET — MCT-182:135 false positive + §3.6.1 gate self-verify
#   TEST 설명 내 canonical 인용 차단):
#   io/ 6 module 정상 inventory `(tier_reader/reader_cache/endpoint_router/dr_mode/
#   cold_reader/l1_reader)` 나열 = D2 relocate 결정 record (ADR-027 amendment scope
#   아님 — module-list 순서 inventory). canonical/이력/gate정의 동반 예외.
# 기대: 0줄 (실 stale 0). 매치 발생 = ADR-027 amendment 2-module 축약 carry → P0 차단
```

> **gate self-verify (pattern 유효성 실증 — 매 gate 변경 시 의무)**:
> - **TEST1 (포착력)**: ADR-031:139 정정 전 원본 변형 `engine io/ endpoint_router +
>   dr_mode = mctrader-data relocated (Layer2 소유)` (조사 `로` 없음 + 따옴표 없음) →
>   신 pattern `endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat|이전)` **MATCH ✓**
>   (구 pattern `endpoint_router ?/ ?dr_mode relocated|..로 relocated\(Layer2 소유\)\"`
>   = **NO MATCH ✗** — 구 gate 가 ADR-031:139 변형 놓침 = iter3 carry 근본 원인 실증)
> - **TEST2 (false positive 0)**: canonical string `io reader 6 module
>   (endpoint_router/dr_mode/reader_cache/...) relocated to mctrader-data Layer2` →
>   신 pattern **NO MATCH** (canonical 은 `endpoint_router/dr_mode` 뒤 40자 내
>   `relocat` 미존재 — 6-module list 4 module 이 사이에 위치 거리 초과). 추가 안전
>   망 = `grep -ivE "io reader 6 module (endpoint"` 예외 필터 (canonical prefix
>   동반 시 무조건 제외)

> **예외 (정상 잔존, gate 무위반 — `grep -ivE` 필터 명문)**:
> - `io reader 6 module (endpoint_router/...` canonical prefix 동반 (정정 산출물)
> - `endpoint_router/dr_mode = ADR-027 §D9 명시 module, 나머지 4 = io/ 묶음 relocate`
>   = canonical 부연 설명 (6-module list 동반, 40자 거리 초과로 자연 미매치)
> - FIX Ledger iter row 내 `P0-1-residual` finding 인용 + gate 패턴 정의 자체 +
>   `cross-document-ssot-desync` / `design-review iter|RESET` 이력 박제 (필터 제외)
> - io/ 6 module 정상 inventory (`tier_reader/reader_cache/endpoint_router/dr_mode/
>   cold_reader/l1_reader` module 나열 = ADR-027 amendment scope 아닌 D2 결정 record)
> - `docs/retros/*` 과거 Story(MCT-154/170) 회고 io/ 언급 = 본 MCT-183 ADR-027
>   amendment 무관 (glob scope `docs/retros/` 미포함 — gate scope 외)

> **sibling Story 산출물 canonical 정정 의무 (iter3 RESET — 전수성 절대 보장 핵심)**:
> glob scope `docs/stories/MCT-18*.md` = MCT-182 도 포함. **MCT-182 (COMPLETED sibling
> Story) frontmatter related_adrs + Continuity 표 의 ADR-027 amendment owner-scope
> 기술 (`실 amend = MCT-183 (...)`) = MCT-183 의 ADR-027 amendment scope 를 직접
> 박제하는 cross-document SSOT** → canonical 통일 대상 (정정 완료: MCT-182:28
> frontmatter + MCT-182:235 Continuity 표). RETRO/회고 본문(`docs/retros/`)은 회고
> 시점 박제(scope 기술 아님)라 gate scope 외이나, **owner-scope 를 기술하는 모든
> Epic 권위 SSOT (Story frontmatter/cross_repo/Continuity 표 포함) 는 sibling
> Story 라도 canonical 통일 의무** (지정 목록 방식 탈피 — repo-wide 전수성 보장).
> 이것이 iter1→3 carry 의 근본(MCT-183 산출물만 보던 지정 목록 한계) 영구 차단.

**전수성 절대 보장 명령 (지정 목록 탈피 — repo-wide grep, 본 RESET 회귀 의무)**:
```bash
grep -rn "endpoint_router" docs/ scope_manifests/ \
  | grep -iv "io reader 6 module\|FIX Ledger\|gate 패턴\|grep gate\|6 module (endpoint"
# 기대: ADR-027 amendment 2-module 축약 0줄 (canonical/이력/gate정의/D2 inventory/
#   retros 과거Story 외 — 실 stale 0 확인. 본 RESET 회귀 evidence 첨부 의무)
```

본 gate v2 = MCT-179 (ADR-030 D5/D8 swap) + MCT-182 (§4.2 self-contradiction) +
MCT-183 iter1→2→3 (ADR-027 amendment 축약 부분 이행 — **수동 지정 목록 방식의 구조적
한계**) **cross-document SSOT desync 5회 누적 동형의 영구 차단 forcing function**
(PMO-AUDIT-MCT-182 §4 Option A self-discipline 의 자기검증 완전 박제 — glob-scope +
변형포괄 + self-verify TEST1/TEST2 로 부분 이행 + pattern 사각 동시 차단). **수동
reconcile 한계 자체 = codeforge upstream ADR escalation 후보** (PMO retro 입력 —
지정 목록 방식 탈피 forcing function 일반화).

## 4. 외부 인터페이스

### 4.1 import surface (변경 표)

| consumer | AS-IS import | TO-BE import | 마이그레이션 |
|----------|--------------|--------------|-------------|
| engine src/ | (io/ 6 module 호출자 = **0건** — dead-in-prod) | (삭제 — 호출자 0) | 없음 (src caller 0 = 삭제 후 import 깨짐 0) |
| data 신규/외부 consumer | — | `from mctrader_data.io import TierReader, ReaderCache, EndpointRouter, DRMode, ColdReader, L1Reader, ...` | Layer2 io reader 직접 import (production wiring = MCT-185) |
| data compactor | `from mctrader_data.compactor.reader_cache import ReaderCache` (Protocol) | (동일 — 무변경, INV-6) | 없음 (다른 namespace, 비접촉) |
| tests/io/ 7 test (data 이전) | `from mctrader_engine.io.*` | `from mctrader_data.io.*` | import path 재지정 (로직 byte-equiv) |

**부작용 변경 없음**: relocation = namespace 이동 + import 경로 재지정. io/ 6 module 동작·
invariant (DR state machine / endpoint atomic flip / LRU byte budget / ETag verify / mixed
layout 호환) byte-for-byte 동등 (INV-1/INV-5). 유일 예외 = reader_cache.py stats()
producer-wiring 블록(line 339-348) → data 측 외부 import 없는 내부 no-op 블록 치환
(dead-in-data, 동작 영향 0, §3.5 채택안 A). API signature 변경 0.

### 4.2 패키지 layout 변화

- data: `src/mctrader_data/io/` 서브패키지 신규 (6 module + `__init__.py`) + `tests/io/`
  신규 (7 test + `__init__.py`). `compactor/reader_cache.py` 무변경 (INV-6)
- engine: `src/mctrader_engine/io/` (6 module + `__init__.py`) + `tests/io/` (7 test +
  `__init__.py`) **물리 삭제** (io 패키지 소멸 — 빈 패키지 잔존 아님)

## 5. 비기능 (perf / observability)

### 5.1 Performance Baseline — N/A 명시 (TestContractArch 산출)

- **Perf Baseline = N/A (불요)** — 본 Story = io/ 6 module **relocation** (namespace 이동 +
  import 경로 재지정). 알고리즘/자료구조/호출 경로 무변경 → perf 무영향. 자동룰 SSOT 정합
  ("relocation/refactor-only Story → Perf Baseline N/A + 사유 1줄"). MCT-182 패턴 reapply.
- **사유**: io/ 6 module 코드 본문 byte-equivalence (동일 함수 본문 물리 이동). reader_cache
  LRU/TTL/byte budget 연산 경로 동일. `test_reader_perf` NFR (MCT-170 D7: hit_ratio≥0.95 /
  p99<100ms) = engine.metrics 비의존 (hit_ratio/p99 직접 계산) → 이전 동등 verdict (relocate
  ≠ 성능 변경 — §8.2 INV-4).
- **§8.5 spawn-time trigger (CFP-378 AC-5)**: §8.5 4 조건 (long-running connection /
  stateful in-memory cache / background worker / process restart-aware) **4개 모두 N** →
  **§8.5_active=false**. 근거: 본 Story = dead-in-prod io/ relocation (신규 connection/
  cache/worker/restart-aware system 도입 0 — io reader 는 dead-in-data 미배선 유지,
  production wiring = MCT-185). TestContractArch 본 결정 verbatim 반영.

### 5.2 Observability

- **N/A** — internal io/ relocation, metric/alert/health 표면 무변경. reader_cache stats()
  producer-wiring 블록(339-348) = data 측 외부 import 없는 내부 no-op 블록 치환 (dead-
  in-data, emit 0 — 실 emit 재배선 = MCT-185). 신규 observability surface 0 (§3.5 채택안 A).

## 6. 리팩터링 선행

- **선행 PR 없음** — Phase 0 verify (§8.0) 가 유일 선행 게이트
- io/ 6 module = dead-in-prod (engine src caller 0) → 사용처 사전 마이그레이션 불요 (삭제
  후 import 깨짐 0). data 측 io/ = dead-in-data (production wiring = MCT-185 — 본 Story
  는 물리 이전 + tests/io/ green 만)
- reader_cache.py stats() producer-wiring 블록(339-348) = §3.5 채택안 A 외부 import
  없는 내부 no-op 블록 치환 (사전 리팩터링 아닌 relocate scope 내 예외 처리)

## 7. 보안 / 운영 리스크 설계

### 7.1 Trust boundary (SecurityArchitectAgent 산출 — 약함 간략 declare)

- **신규 trust boundary 0** — 본 Story = dead-in-prod io/ 6 module 의 cross-repo namespace
  물리 이동 + engine 삭제 + import path 재지정. 네트워크 표면/IPC/직렬화 경계/외부 입력
  처리 경로 **무변화**. attack surface delta = 0.
- io/ 6 module = in-process python NAS read API (stdlib only — 외부 입력 파싱/network/
  credential 신규 0). relocate ≠ 보안 표면 변경. internal module relocation — SecurityArch
  primary 영역 약함 (간략 declare 정합).

### 7.2 Auth / authz

- **N/A** — auth/credential/secret 신규 0. ADR-008 변경 0. io/ NAS reader 의 endpoint
  resolution 은 env 기반 (credential 신규 도입 0, 거주 이전만).

### 7.3 데이터 보호

- **N/A** — PII/sensitive data 처리 경로 무변경. io/ reader 는 NAS object read (parquet)
  — 본 Story dead-in-data 미배선 유지 (실 read 경로 = MCT-185 cutover).

### 7.4 운영 리스크 (OperationalRiskArchitectAgent 산출 — CONDITIONAL N/A)

| 항목 | 판정 | 사유 |
|------|------|------|
| DR / disconnect / clock / rate-limit / env-isolation | **N/A** | 본 Story = docs-only Phase 1 + dead-in-prod io/ 물리 이전 + 삭제. 신규 service/daemon/connection/scheduler 도입 0. runtime topology 무변경 (compose/credential/network 무변경). io reader = dead-in-data 미배선 (실 배선 = MCT-185). |
| dr_mode.py DR state machine 거주 이전 | **N/A (동작 무변경)** | dr_mode (CLOSED/OPEN/HALF_OPEN/UNKNOWN_TIER) = dead-in-prod 자산 거주 이전 — 실 DR 동작 미배선 (production caller 0). state machine 로직 byte-equiv 보존 (INV-5). 실 DR 운영 = MCT-185 cutover 후 |
| 유일 운영 risk = cross-repo land_order desync (R1) | **§9 Rollout/Backout 에서 다룸** | land_order (hub P1→data#N→engine#N→hub P2) 위반 시 일시적 양측 io/ 부재 window — dead-in-prod 라 production 무영향이나 land_order 정합 의무 (release-ordering risk, §9.3 backout 으로 완화) |

> §8.5 spawn-time trigger 결정 (CFP-378 AC-5): §8.5 4 조건 **4개 모두 N** →
> **§8.5_active=false** (§5.1 정합). 근거: dead-in-prod io/ relocation, 신규 connection/
> cache/worker/restart-aware system 도입 0. TestContractArch 본 결정 verbatim 반영.

### 7.5 Threat modeling (STRIDE 요약)

- Spoofing/Tampering/Repudiation/Information disclosure/DoS/Elevation = **전 N/A** —
  dead-in-prod in-process 모듈 cross-repo 이동, 외부 trust boundary delta 0. 신규 위협
  벡터 부재 (io reader 실 배선 0 — 미배선 자산 거주 이전).

### 7.6 보안 ack

SecurityArchitectAgent 채택 — author Architect agree. 본 변경은 외부 trust boundary 추가 0,
dead-in-prod io/ 코드 cross-repo 이동 + 삭제 only. attack surface 무변화 (internal module
relocation 약함 정합).

### 7.7 N/A 영역 (박제)

- 외부 API 노출 0 / secret·credential 신규 0 / 네트워크 표면 0 / 신규 trust boundary 0
- §7.4 운영 리스크 5 항목 = CONDITIONAL N/A (relocation Story — runtime topology 무변경,
  io reader dead-in-data 미배선)

## 8. Test Contract (TestContractArchitectAgent 산출 + Architect 통합)

### 8.0 Phase 0 Verify Gate (코드 작업(data#N) 착수 전 design/impl lane 의무, R1 가드)

> **본 절은 코드 작업(data#N) 착수 전 design/impl lane 이 선이행 의무.** session/brainstorm/
> Story §0 박제는 가설로 수용 — origin HEAD 기준 재검증 의무 (docker-stack Phase 0 verify
> gap 6회 + MCT-179→180 desync 동형 → 7회째 사전 차단). 설계 lane 박제 시점 (2026-05-16)
> 본 gate 전수 실행 완료 — 결과 박제 (V2/V3/V4 정합, V5 부분 불일치 1건 §3.5 사전 정정).

| Gate | 명령 | 기대 | 불일치 시 |
|------|------|------|-----------|
| **V1 (git fetch 3 repo)** | `git -C c:/workspace/mclayer/mctrader-data fetch origin && git -C .../mctrader-engine fetch origin && git -C .../mctrader-hub fetch origin` | working tree stale 차단 (origin HEAD 기준 재grep 전제) | — |
| **V3-A (module import 0)** | `git -C .../mctrader-engine grep -nE "from mctrader_engine\.io\|import mctrader_engine\.io" origin/main -- 'src/**/*.py' ':!src/mctrader_engine/io/**'` | **0건 (rc=1)** | **STOP → ArchitectPL escalate** (R1 desync) |
| **V3-B (bare 심볼 0)** | `git -C .../mctrader-engine grep -nE "\b(TierReader\|ReaderCache\|EndpointRouter\|DRMode\|ColdReader\|L1Reader)\b" origin/main -- 'src/**/*.py' ':!src/mctrader_engine/io/**'` | **0건 (rc=1)** | STOP → escalate |
| **V3-C (io/__init__ self-import만)** | `git -C .../mctrader-engine grep -n "mctrader_engine\.io" origin/main -- 'src/**/*.py'` | `io/__init__.py` 6 self-import 만 (외부 src caller 0) | STOP → escalate |
| **V5 재확인 (io/ 6 module stdlib only + 예외 1건)** | `git -C .../mctrader-engine show origin/main:src/mctrader_engine/io/reader_cache.py \| nl -ba \| sed -n '336,360p'` + `git grep -nE "from mctrader_engine\|import mctrader_engine" origin/main -- 'src/mctrader_engine/io/**/*.py' \| grep -v "mctrader_engine\.io\."` | `reader_cache.py` producer-wiring 블록 **line 339-348** (주석 1 + import 6 multi-line + 빈줄 + 호출 2) **1건만** (나머지 5 module + reader_cache.py 339-348 외 = stdlib only) — §3.5 채택안 A no-op 블록 치환 대상 확인 | 339-348 외 추가 발견 시 STOP → escalate |
| **V6 namespace 충돌 재확인** | `git -C .../mctrader-data grep -nE "\b(TierReader\|EndpointRouter\|DRMode\|L1Reader)\b" origin/main -- 'src/**/*.py'` + `git ls-tree origin/main -- 'src/mctrader_data/io/'` | data io reader 심볼 충돌 0건 + `src/mctrader_data/io/` ABSENT | STOP → escalate |
| **V-pin (byte-equiv source pin — P1-1)** | `git -C .../mctrader-engine rev-parse origin/main` (data#N 시점 1회 record) | engine `origin/main` 고정 commit hash — byte-equiv 비교 source pin (engine#N 삭제 후 재현 불가 차단). hub/data#N 측 expected source = 본 pinned tree | hash 미기록 시 STOP → escalate |

> 설계 lane 박제 (2026-05-16 origin/main HEAD): V1 fetch ✓ / V3-A 0건 ✓ / V3-B 0건 ✓ /
> V3-C io/__init__ 6 self-import 만 ✓ / **V5 = reader_cache.py producer-wiring 블록
> line 339-348 (주석 339 + import 340-345 multi-line ×2 + 빈줄 346 + 호출 347-348)
> 1건 발견 — §3.5 채택안 A 내부 no-op 블록 치환 사전 정정 (설계리뷰 iter1 P0-3
> executable hunk 재실측)** / V6 충돌 0 + data io/ ABSENT ✓ / V-pin = data#N 착수
> 시점 engine `origin/main` rev-parse hash record 의무 (P1-1).
> data#N 착수 시점에 V1 fetch 후 위 gate 전수 재실행 — §0/§3.5 와 재대조, 339-348
> 외 추가 발견 or V3 ≠ 0건 시 escalate.

### 8.1 Invariant (byte-equivalence + dead-in-prod 안전 제거)

- **INV-1 [byte-equivalence]**: io/ 6 module 코드 본문 = engine 원본 byte-for-byte 동등.
  **유일 예외 = `reader_cache.py` stats() producer-wiring 블록 (engine 원본 line
  339-348: 주석 1 + lazy import 6 multi-line + 빈줄 + 호출 2)** → data 측 외부 import
  없는 **내부 no-op 블록 치환** (§3.5 채택안 A — 설계리뷰 iter1 P0-2/P0-3 정정,
  "2줄" 과소 산정 → "producer-wiring 블록 339-348" 정정)
  - **P1-1 byte-equiv source pin**: 비교 source = engine `origin/main` **고정 commit
    hash** (data#N 착수 시점 §8.0 V-pin 1회 record — engine#N 삭제 후 재현 불가 차단).
    hub/data#N 측 expected = 본 pinned tree 의 io/ 6 module
  - 테스트: `tests/io/` 7 test 의 state machine·flip·budget·verify 케이스 ALL PASS +
    `tests/test_io_relocation_byte_equiv.py` (engine `origin/main` pinned tree ↔ data
    6 module diff = `io/__init__.py` import path 6줄 + `reader_cache.py` stats()
    producer-wiring 블록 **range 339-348** 외 0. 정확 diff hunk = §8.2 허용 명문)
- **INV-2 [io/ Layer2 자족 — 외부 패키지 의존 0]**: data `src/mctrader_data/io/`
  `git grep -E "import mctrader_data\|from mctrader_data\|import mctrader_market\|from
  mctrader_market\|import mctrader_engine\|from mctrader_engine"` == **0건** (relocate
  후 mctrader_data/mctrader_market/mctrader_engine 내부 의존 신규 0). reader_cache.py
  stats() producer-wiring 블록 = **외부 import 없는 내부 no-op 블록 치환** (§3.5 채택안
  A — `mctrader_data.metrics` 신설 회피, engine.metrics 역의존 제거. grep gate 무위반
  — 외부 import 0)
  - 테스트: `tests/test_io_layer2_self_contained.py::test_io_no_external_dep` +
    `tests/test_io_stats_no_engine_dep.py` (clean subprocess `import
    mctrader_data.io.reader_cache; assert "mctrader_engine" not in sys.modules` +
    `ReaderCache.stats()` 정상 dict 반환 — engine.metrics 미설치 환경 NameError/
    ImportError 0, P0-3 executable 회귀)
- **INV-3 [engine src caller 0 영구 — dead-in-prod 안전 제거]**: engine io/ 삭제 후 engine
  `src/` `from/import mctrader_engine.io` + bare 심볼 grep == 0건 + full suite import error 0
  - grep gate: engine `git grep -nE "from mctrader_engine\.io|import mctrader_engine\.io"
    -- 'src/**/*.py'` == 0 AND bare 심볼 == 0 (io/ 삭제 후 전 src/)
  - 테스트: `tests/test_io_deleted_no_dangling.py::test_engine_src_io_grep_zero`
- **INV-4 [tests/io/ 7 test green — 로직 byte-equivalence]**: data 측 `tests/io/` 7 test
  ALL PASS (import path 재지정만, 로직 무변경). `test_reader_perf` NFR (hit_ratio≥0.95 /
  p99<100ms) = 이전 동등 verdict (engine.metrics 비의존 — 직접 계산). `test_reader_cache_flush.py:215`
  engine.metrics lazy = data graceful skip 정합 (cold reader 한정 metric, MCT-180 §D8
  contract 정합 — NFR verdict 무영향)
  - 테스트: data 측 `tests/io/` 7 test green + data full suite 회귀 신규 실패 0
- **INV-5 [io/ 6 module 동작·invariant 무변경]**: DR state machine (CLOSED/OPEN/HALF_OPEN/
  UNKNOWN_TIER) / endpoint atomic flip / LRU byte budget / ETag verify / mixed layout
  호환 거주 이전 후에도 보존
  - 테스트: `tests/io/` 7 test 의 state machine·flip·budget·verify 검증 케이스 ALL PASS
- **INV-6 [data compactor.reader_cache.ReaderCache(Protocol) 무변경]**: `compactor/reader_cache.py`
  diff = 0 + data compactor 테스트 회귀 신규 실패 0 (다른 namespace — 비접촉)
  - grep gate: `git diff` `src/mctrader_data/compactor/reader_cache.py` == 0
  - 테스트: 기존 data `tests/compactor/` green 유지

### 8.1 INV-1 amendment box (post-completion 2026-05-17, hub#TBD post-completion amendment LAND)

> **트리거**: data#70 post-merge audit (Codex) 가 INV-1 위반 5건 (ruff --fix --select F401,SIM105
> lint auto-fix 의도치 않은 적용) 발견. 6450cfd direct commit 으로 1차 부분 정정 (cold_reader
> 등 partial), 그러나 ruff per-file-ignores 정책 미박제 + 5 module 전수 revert 미완 → data#71
> PR carry over. CFP-795 isPostMergeFix 4번째 fast-pass source 정식 escalation 발의 trigger.

**amendment 결정 (LAND 박제)**:

- **AM-1 (relocate 자산 ruff per-file-ignores 정책 명문)**:
  - data `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` 에 `"src/mctrader_data/io/*.py" = ["F401", "SIM105"]` 추가 (data#71 950e82b)
  - **사유**: relocate 자산 (engine origin/main byte-equivalent) 의 INV-1 보존 의무 → ruff auto-fix 격리. 재발생 차단 mechanical gate.
  - **carry over (MCT-185 cutover)**: io/ 가 production caller 연결 + cold-read REST cutover 시점에 lint 재적용 (per-file-ignores 해제 + auto-fix 검증). io/ 자산이 더 이상 byte-equivalence 의무가 아니게 되는 시점 = MCT-185 LAND 시점. ADR-031 §D2 partial → full VERIFIED 전환 시 amendment 박제.

- **AM-2 (INV-1 위반 5 module 전수 revert)**:
  - data#71 6450cfd commit = INV-1 byte-equivalence 5 module 전수 revert (cold_reader.py line 35-36 field/Optional import 복원 + dr_mode.py contextlib.suppress → try/except revert + endpoint_router.py field/Optional 복원 + l1_reader.py field 복원 + reader_cache.py:36 Optional 복원 + tier_reader.py field 복원)
  - **engine origin/main `c6249fa6` byte-for-byte 동일 verify** (data main = §11.1 행 8 LAND commit 박제 후)

- **AM-3 (CFP-795 isPostMergeFix carrier)**:
  - data#71 = CFP-795 isPostMergeFix 1st 적용 case. 3-조건 AND gate (post-merge-fix label + hub §10 binding + 양면 §7 보안 non-touch) 통과 → phase-gate-mergeable fast-pass.
  - hub-side carrier: 본 §10 post-merge 1 row + §11.1 행 8/9 + Story §10 (mctrader-hub `docs/stories/MCT-183.md`) 모두 binding marker carrier 의무 (CFP-795 isPostMergeFix Cond 2 source).

### 8.2 byte-equivalence 회귀 (engine origin/main pinned tree ↔ data 이전 6 module)

> **P1-1 source pin**: 비교 source = engine `origin/main` 고정 commit hash (§8.0
> V-pin, data#N 착수 시점 1회 record — engine#N 삭제 후 재현 불가 차단). 정확 diff
> hunk range 명문 (P0-3 — "2줄" 과소 산정 → producer-wiring 블록 339-348).

| 검증 | 방법 | INV |
|------|------|-----|
| io/ 6 module 코드 본문 byte-equiv | engine `origin/main` pinned tree ↔ data 6 module diff = **(a)** `io/__init__.py` import path **6줄** (340-345 self-import → mctrader_data.io.X) + **(b)** `reader_cache.py` stats() producer-wiring 블록 **range line 339-348** (engine 원본 10줄 = 주석 339 + import 340-345 + 빈줄 346 + 호출 347-348 → data 측 외부 import 없는 no-op 주석 블록 치환) 외 **0** (§3.5 채택안 A 정확 hunk 명문 — INV-2 grep 무위반: data 측 치환 블록에 외부 import 0) | INV-1 |
| io/ 6 module 동작 회귀 | data `tests/io/` 7 test (state machine/flip/budget/verify) ALL PASS | INV-5 |
| **stats() no-op executable 회귀 (P0-3)** | 신규 `tests/test_io_stats_no_engine_dep.py` — engine.metrics 미설치(부재) 환경 clean subprocess `import mctrader_data.io.reader_cache; ReaderCache(...).stats()` → NameError/ImportError **0** + 반환 dict `hit_ratio`/`p99_ms` 값 정확 + `sys.modules` 에 `mctrader_engine` 부재 assert | INV-1/INV-2 |
| Perf Baseline | `test_reader_perf` NFR 이전 동등 verdict (relocate 라 perf 무영향 — engine.metrics 비의존 직접 계산, reader_perf.py 이전 green 으로 충분, §5.1 N/A 정합) | INV-4 |
| `test_reader_cache_flush` 정정 회귀 | engine 원본 `test_stats_emits_prometheus_gauges` (L215 engine.metrics Gauge assert) = data 측 `pytest.mark.skip(reason="MCT-183 relocate: Gauge emit = MCT-185 cutover owner, dead-in-data no-op")` 또는 stats() 반환 dict 만 assert (hit_ratio/p99 값 검증 유지) — 로직 정정 동반 (§3.5) | INV-4 |
| compactor Protocol 회귀 | `compactor/reader_cache.py` diff 0 + data compactor 테스트 회귀 0 | INV-6 |

### 8.2 INV-4 amendment box (post-completion 2026-05-17, hub#TBD post-completion amendment LAND)

> **트리거**: data#70 LAND 후 발견 — `tests/io/` 7 test 가 ubuntu CI 환경에서 (A) pyright type
> error 1건 + (B) flaky timing tolerance (test_reader_perf p99 latency assertion) + (C) CacheEntry
> dataclass 정식화 부재 (dict-tuple 혼용) 발견. data#70 의 byte-equivalence INV-1 보존은 src/
> 한정이며 tests/io/ 는 relocate 시 CI 정합 의무 (INV-4 "tests/io/ 7 test green") 가 CI 통과
> 의무 카테고리임을 명문 amendment.

**amendment 결정 (LAND 박제)**:

- **AM-4 (tests/io/ pyright fix + timing tolerance + CacheEntry 정식화 = CI 통과 의무 카테고리)**:
  - tests/io/ test 의 CI 통과 의무 (data ubuntu-latest CI green) 가 INV-4 carrier — pyright type error 정정 + timing tolerance 안정화 + CacheEntry dataclass 정식화 (dict-tuple 혼용 제거) 모두 byte-equivalence INV-1 영역과 분리 (src/ 가 아닌 tests/ 영역).
  - **engine origin/main 의 tests/io/ 7 test** = data 측에 byte-relocate 시점 = engine 측 CI 가 통과한 시점 → data 측에서도 CI 통과 의무. 단 data 측 환경 (newer pyright, slower CI runner) 에서 fix 필요 → CI 통과 의무 카테고리 명문.
  - **carry**: tests/io/ 가 production wiring (MCT-185 cutover) 시점에 다시 검증 의무. pyright + timing tolerance + CacheEntry 정식화는 MCT-185 cutover 와 무관 — relocate 시점에 정식 박제 (본 amendment box).

- **AM-5 (data#71 PR 가 §8.2 INV-4 정정 동반 포함)**:
  - data#71 PR scope = INV-1 revert (§8.1 AM-2) + ruff per-file-ignores (§8.1 AM-1) + tests/io/ pyright/timing/CacheEntry 정정 (§8.2 AM-4) 통합.
  - 사용자 결정 옵션 A (hub Phase 2 PR2 박제 시 통합) → 본 post-completion amendment 로 확장 (Phase 2 PR2 hub#355 LAND 후 발견되어 post-completion 별 PR carry over).

### 8.3 engine 삭제 후 회귀 (engine#N)

- engine `src/mctrader_engine/io/` + `tests/io/` 삭제 후 engine full suite 회귀 신규 실패 0
  (src caller 0 = 삭제 후 import 깨짐 0, INV-3)
- engine `git grep` io/ 6 module 호출 흔적 = 0건 (3-modal — module import + bare 심볼,
  io/ 삭제 후 전 src/) — dangling import 0
- **engine.metrics setter 고아화 비차단 확인**: engine `set_reader_cache_hit_ratio`/
  `set_reader_p99_ms` (metrics.py:72/77) 는 io/ 삭제 후 engine 측 caller 0 가능 —
  본 Story scope 외 (engine.metrics 자체 모듈 무변경, 고아 setter 잔존 무해 — dead
  code cleanup = MCT-185/188 carry, 본 Story 는 io/ relocate only)

### 8.4 채택/반박

- TestContractArch 6 invariant (byte-equiv/Layer2 자족/src caller 0 영구/tests green/동작
  무변경/compactor Protocol 무변경) + Phase 0 Gate (V1+V3 3-modal+V5+V6+V-pin) + engine
  삭제 grep gate + P0-3 stats() no-op executable 회귀 모두 chief author 채택
- Perf Baseline = N/A (§5.1 — relocation, perf 무영향. reader_perf.py 이전 green 으로
  충분) chief author 채택 (§8.5_active=false 정합)
- **chief author 반박/보강 1건 (설계리뷰 iter1 P0-2/P0-3 정정 반영)**: TestContractArch
  seed = "io/ byte-equiv 전수 diff 0". 설계 lane CodebaseMapper fact (reader_cache.py
  stats() producer-wiring engine.metrics) 반영 → INV-1 을 "(a) `io/__init__.py` import
  path 6줄 + (b) reader_cache.py stats() producer-wiring 블록 range 339-348 외 0" 으로
  정정 (byte-equivalence 예외 1건 명문화 — §3.5 채택안 A SSOT 정합, "2줄" 과소 산정
  정정). Story §5 AC-1/§6 INV-1/INV-2/§4.2 동반 역전파 완료 (P0-2 — cross-document
  SSOT 정합 forcing function). TestContractArch 보강 수용
- data full suite 회귀 신규 실패 0 + engine full suite 회귀 신규 실패 0 = DesignReview evidence

## 9. Rollout / Backout

### 9.1 Rollout (cross-repo sequential LAND — land_order 엄수)

```
hub Phase 1 (docs)  →  data#N  →  engine#N  →  hub Phase 2 PR2 (박제)
   (land_order 0)     (order 1)   (order 2)    (박제)
```

1. **hub Phase 1**: Story §0-§11 + ADR-029/027 MCT-183 amendment box + scope_manifest
   MCT-183 IN_PROGRESS + CLAUDE.md + counters.json. CI green 후 admin merge
2. **data#N (order 1)**: `src/mctrader_data/io/` 6 module byte-equiv 수령 + `io/__init__.py`
   6 self-import 재지정 + reader_cache.py stats() producer-wiring 블록(339-348) 외부
   import 없는 내부 no-op 블록 치환 (§3.5 채택안 A) + `test_io_stats_no_engine_dep.py`
   회귀 추가 + `tests/io/` 7 test import path 재지정 (+ `test_reader_cache_flush`
   stats Gauge test skip/정정) + green + data full suite 회귀 0. CI green 후 admin merge
3. **engine#N (order 2)**: `git rm -r src/mctrader_engine/io/ tests/io/` (io 패키지 소멸)
   + engine full suite 회귀 0 + grep gate (io/ 6 module 호출 0). CI green 후 admin merge
4. **hub Phase 2 PR2**: Story §11 박제 + ADR-029/027 amendment box VERIFIED + scope_manifest
   milestone 2/7 + CLAUDE.md COMPLETED + RETRO + EPIC-RESULTS §Story-2

### 9.2 Cutover 전략

- **무중단** — io/ 6 module = dead-in-prod (engine src caller 0). data#N 수령 시점 data
  측 dead-in-data (production wiring 0 — MCT-185). engine#N 삭제 시점 src caller 0 =
  production import 깨짐 0. **production 무영향 cross-repo 물리 이전**
- 각 PR 독립 CI green 후 admin merge — **data 수령 선행 / engine 삭제 후행 엄수** (역순
  시 일시적 양측 io/ 부재 window — dead-in-prod 라 production 무영향이나 land_order 정합
  의무, R1 가드)

### 9.3 Backout 조건 / 절차

| 시점 | backout |
|------|---------|
| data#N LAND 후 engine#N 전 | data revert (io/ 6 module + tests/io/ 삭제 — engine io/ 원본 잔존, 영향 0) |
| engine#N LAND 후 | **land_order 역순** — engine revert (io/ 6 module + tests/io/ 복구) 선행 → 필요 시 data revert. engine io/ 단독 삭제 잔존 시 dead-in-prod 라 production 무영향이나 정합 위해 양측 복구 |
| Phase 0 verify 불일치 (V3 ≠ 0건 or V5 1건 외 추가) | data#N 착수 전 STOP → ArchitectPL escalate (코드 작업 진입 차단, R1 desync 사전 차단) |

- **rollback 무결성**: backout = **land_order 역순** (engine 복구 → data 삭제). data#N
  LAND 후 engine#N 전 단계는 data 단독 revert 안전 (engine io/ 원본 잔존). engine#N
  LAND 후는 engine io/ 복구 선행 (dead-in-prod 라 production 무영향이나 cross-repo
  정합 보존)

## 10. ADR 판단

- **ADR-029 MCT-183 amendment box 박제 완료** — `docs/adr/ADR-029-tier-promotion-single-source.md`
  Status 섹션 (D1+D2 verify status 직후). io reader 6 module relocated to mctrader-data
  (D2 io-relocate 절반, byte-equiv) + engine NAS 직독 폐기 **예고** (실 confirm = MCT-185)
  + Phase 0 verify 발견 (reader_cache.py stats() lazy engine.metrics, R1 가드 7회째 사전
  차단) + D-row ↔ scope_manifest 1:1 reconcile 박제
- **ADR-027 MCT-183 amendment box 박제 완료** — `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md`
  §D9 (MCT-167 amendment 직후). io reader 6 module (endpoint_router/dr_mode/reader_cache/
  cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2 소유 (endpoint_router/
  dr_mode = ADR-027 §D9 명시 module, 나머지 4 = io/ 묶음 relocate — scope_manifest
  §planned_adrs.amendments ADR-027 ↔ box 헤더/본문 byte 1:1, P0-1 reconcile) + MCT-156
  amendment "io/ 3 module 영향 0" = 거주 이전 후에도 동작 영향 0 정합 명시 + D-row reconcile
- **ADR-029/027 본문 결정 무변경** — relocate ≠ 정책 변경. §D9 SoT 모델·mixed layout
  호환·forward-only invariant 자체 무변경 (거주 repo 만 이전). 실 NAS 직독 폐기 confirm
  = MCT-185 owner (scope 경계 — amendment box 예고만)
- **ADR-031 §D2 정합** — 본 Story = §D2 `io-relocate + cold-read-behind-REST` 의 io-relocate
  절반 진행. §D2 VERIFIED = MCT-185 cold-read cutover LAND 후 (본 Story 는 부분 진행 —
  amendment box 박제, VERIFIED 아님). ADR-031 본문 무변경 (amend 불요 — §D2 record only)

## 11. 데이터 마이그레이션 (DataMigrationArchitectAgent 산출)

### 11.1 마이그레이션 분류 (io relocation = code-level, persisted-data migration 0)

| 분류 | 본 Story | 처리 |
|------|----------|------|
| persisted data (Parquet/DB/NAS object) schema 변경 | **없음** | io reader = NAS object **read** 자산 (write 0). dead-in-prod 미배선 — 기존 Parquet/object 무영향. schema/layout 무변경 |
| wire/serialization format 변경 | **없음** | io/ 6 module 동작 byte-equivalence (INV-1/INV-5) — endpoint/cache/DR 로직 출력 동일 |
| code-level module relocation | **본 Story 본질** | cross-repo namespace 이동 — §11.2 무결성 invariant |

### 11.2 Integrity invariant (byte-equivalence 무결성 — DataMigrationArch primary)

- **byte-equivalence**: io/ 6 module 코드 본문 = engine 원본 byte-for-byte 동등 (INV-1).
  유일 예외 = reader_cache.py stats() producer-wiring 블록 (engine 원본 line 339-348)
  → data 측 외부 import 없는 내부 no-op 블록 치환 (§3.5 채택안 A — dead-in-data, 동작
  영향 0). P1-1 비교 source = engine `origin/main` pinned tree (§8.0 V-pin). relocate
  ≠ 동작 변경 = 무결성 SSOT
- **동작·invariant 무결성**: DR state machine / endpoint atomic flip / LRU byte budget /
  ETag verify / mixed layout 호환 = 거주 이전 후 보존 (INV-5 — tests/io/ 7 test green
  으로 검증)
- **compactor Protocol SSOT 격리**: `mctrader_data.compactor.reader_cache.ReaderCache(Protocol)`
  무변경 (INV-6) — 신규 `mctrader_data.io.reader_cache.ReaderCache` (구현체) 와 다른
  namespace. compactor 측 추상 비접촉 = SSOT 이중화 0

### 11.3 Cutover 무결성 (cross-repo land_order)

- **data#N LAND (io/ 수령 + green) → engine#N (io/ 삭제) 순서 엄수** (§9.1). 역순 시 일시적
  양측 io/ 부재 window — dead-in-prod 라 production 무영향이나 land_order = 무결성 게이트
- data full suite 회귀 신규 실패 0 + engine full suite 회귀 신규 실패 0 + tests/io/ 7
  test green = 무결성 PASS 기준

### 11.4 Rollback 무결성 (land_order 역순)

- backout = **land_order 역순** (engine io/ 복구 → data io/ 삭제, §9.3). data#N LAND
  후 engine#N 전 = data 단독 revert 안전 (engine io/ 원본 잔존 — dead-in-prod). engine#N
  LAND 후 = engine io/ 복구 선행 (cross-repo 정합 보존). DataMigrationArch 무결성 정합 =
  "data 수령 ↔ engine 삭제 land_order 동시성 보존"

### 11.5 Idempotency

- **N/A (해당 없음)** — io relocation 은 1회성 code-level 모듈 이동 (재실행 가능한 data
  migration job 아님). cross-repo PR sequential LAND = git merge idempotency (동일 PR
  재merge = no-op). persisted-data 재처리 경로 부재 (io reader dead-in-prod 미배선).

> §11.6 (idempotency CONDITIONAL — DataMigrationArch primary + OperationalRiskArchitect
> consult): 본 Story 는 idempotent 재처리 대상 (background job / data migration job /
> queue consumer) 도입 0 → §11.6 = **N/A**. OperationalRiskArchitect consult 결과 =
> consult 대상 부재 (relocation Story, runtime job 무도입, io reader dead-in-data 미배선).

### 11.7 N/A (박제)

- persisted-data schema breaking change 0 (io reader = NAS read 자산, write 0, dead-in-prod
  미배선)
- RDB 마이그레이션 0 / NAS object layout 변경 0 / wire format 변경 0
- idempotency (§11.5/11.6) = N/A (1회성 code relocation, runtime job 무도입)

## 12. PL 검수 결과

### 12.1 ArchitectPL 1차 검수 (2026-05-16, Iteration 1)

**§섹션별 deputy author input 통합 정합성 (메타-규칙)**:

| §절 | deputy | 통합 정합성 | 판정 |
|-----|--------|-------------|------|
| §2 | CodebaseMapperAgent | verified-via git grep/show origin/main HEAD fact (가설 0) — io/ 6 module stdlib only / 6 module cross-import 0 / **reader_cache.py producer-wiring 블록 line 339-348 stats() engine.metrics 신규 발견 (설계리뷰 iter1 P0-3 executable hunk 재실측)** / engine src caller 0 / data io/ ABSENT / compactor ReaderCache 동명 변호 근거 채택 | ✅ PASS |
| §3·§6 | RefactorAgent | namespace 분리 (`mctrader_data.io` 서브패키지) + io/__init__ 6 self-import 재지정 + byte-equiv 예외 1건 = §3.5 채택안 A 외부 import 없는 내부 no-op 블록 치환 (range 339-348, INV-2 grep 무위반) + io 패키지 소멸 — 제안 범위 준수 | ✅ PASS |
| §7 (§7.1-§7.3, §7.5-§7.6) | SecurityArchitectAgent | 신규 trust boundary 0 / attack surface delta 0 간략 declare (internal module relocation 약함 정합 — declare 적정) | ✅ PASS |
| §7.4 | OperationalRiskArchitectAgent | DR/disconnect/clock/rate-limit/env 5 항목 CONDITIONAL N/A + dr_mode 거주 이전 동작 무변경 + §8.5_active=false 결정 verbatim (약함 정합 — declare 적정) | ✅ PASS |
| §8 | TestContractArchitectAgent | 6 invariant (byte-equiv/Layer2 자족/src caller 0 영구/tests green/동작 무변경/compactor Protocol 무변경) + Phase 0 Gate (V1+V3 3-modal+V5+V6+V-pin) + P0-3 stats() no-op executable 회귀 + Perf N/A. **chief author 반박/보강 1건 (설계리뷰 iter1 P0-2/P0-3 정정)**: INV-1 byte-equiv 를 "(a) io/__init__ import path 6줄 + (b) reader_cache.py stats() producer-wiring 블록 range 339-348 외 0" 으로 정정 ("2줄" 과소 산정 → 블록 339-348, §3.5 채택안 A SSOT 정합). Story §5 AC-1/§6 INV-1/INV-2/§4.2 동반 역전파 (P0-2 forcing function) | ✅ PASS |
| §11 (§11.1-§11.5, §11.7) | DataMigrationArchitectAgent | byte-equivalence 무결성 + 동작 invariant 보존 + compactor Protocol SSOT 격리 + rollback land_order 역순 매핑 반영 | ✅ PASS |
| §11.6 | DataMigrationArch primary + OperationalRiskArch consult | idempotency CONDITIONAL N/A (runtime job 무도입, io reader dead-in-data) — consult 대상 부재 박제 | ✅ PASS |

**§섹션 누락 차단**: §7 ✓ §7.4 ✓ §8 ✓ §10 ✓ §11 ✓ — 전 present (DesignReview P0 차단 대상 0)

**6 인계 조건 반영 확인 (요구사항 lane verdict)**:
1. **Phase 0 V1/V3 재대조 의무** — §8.0 Phase 0 Verify Gate 절 명문화 + 설계 lane origin/main
   HEAD 전수 재실행 (V2/V3/V4 정합, V5 부분 불일치 1건 §3.5 사전 정정) ✓
2. **V6 동명 risk — namespace 분리 확정** — §3.2: `mctrader_data.io` 서브패키지 명시 배치
   + compactor.reader_cache.ReaderCache(Protocol) 무변경 (INV-6) + 6 module cross-import
   0 실증 (io/__init__ 6줄만 재지정) ✓
3. **byte-equivalence 경계** — §3.3/§3.5: io/ 6 module 본문 무변경 + 예외 1건 (stats()
   lazy) graceful no-op 명문화 (INV-1) ✓
4. **land_order** — §9.1/§11.3: data#N (수령) 선행 / engine#N (삭제) 후행 + rollback 역순 ✓
5. **ADR amendment box D-row 1:1 reconcile** — ADR-029/027 MCT-183 amendment box 박제 +
   §3.6 reconcile 표 (4 산출물 7/7 byte 1:1) ✓
6. **io/__init__.py 삭제 처리** — §3.4: engine io 패키지 소멸 (빈 패키지 잔존 아님) ✓

**Deputy 재spawn 이력**: 0회 (6 deputy 1-pass — CONDITIONAL LiveOps/LiveOrdering 미spawn
(internal relocation, real funds/live API 무관). Phase 0 fact 사전 정합 + reader_cache.py
stats() 신규 발견은 CodebaseMapper 1-pass 내 verified — clarification 재spawn 불요)

- **VERDICT (1차)**: **PASS** (설계리뷰 iter1 전 — §12.2 FIX 정정 후 재실행 신호)

### 12.2 ArchitectPL 설계리뷰 iter1 FIX 회귀 정정 (2026-05-16, design-review iter 1/3)

설계리뷰 verdict = FIX iter 1/3 (P0×3 + P1×1, 전부 설계 원인 — root-cause-decision:
설계 리뷰 P0 → 항상 설계). ArchitectPL 직접 회귀 (DeveloperPL 미개입). PMO-AUDIT-MCT-182
§4 forcing function self-discipline = **4 산출물 동반 reconcile** (1차 정정 시 일부만
정정 금지, 전수 byte 정합).

| finding | severity | 최종 판정 | 정정 |
|---------|----------|-----------|------|
| P0-1 cross-document SSOT desync (scope_manifest ADR-027 = 2 module ↔ ADR-027 box = 6 module ↔ §3.6 row 4 "+4 괄호" 오판정) | P0 | **설계 원인** (MCT-179/182 동형 재발, PMO-AUDIT-MCT-182 §4 정확 예측) | **4 산출물 동반 reconcile** — scope_manifest §planned_adrs.amendments ADR-027 = 6-module 전체 relocate 확장 (`section/change/owner` byte 갱신) ↔ ADR-027 amendment box 헤더/본문/D-row 인용 6-module list 통일 ↔ Change Plan §3.6 row 4 정직 판정 (괄호 회피, byte 동일 명문) ↔ Story §4.3 row + frontmatter related_adrs + §5 AC-5 6-module 명시 |
| P0-2 Story SSOT 역전파 누락 (§8.4 chief author 정정이 Change Plan 내부만 → Story §5 AC-1/§6 INV-1·INV-2/§4.2 미반영, PMO-AUDIT-MCT-182 §3 패턴 #2 사전 발현) | P0 | **설계 원인** (Story = 권위 SSOT, cross-document 역전파 의무) | Story §5 AC-1 Then 절 + §6 INV-1/INV-2 + §4.2 (relocate 결합 전파 위험 행 + 종합 문장) 에 reader_cache.stats() producer-wiring 예외 + 6 module cross-import 0 실증 = Change Plan §8.1 텍스트와 동일 역전파. §4.2 "stdlib only" → "(top-level) stdlib only + §3.4 lazy metrics 예외 발견" 명시 |
| P0-3 executable design gap (§3.5 "lazy 2줄 no-op" → import만 no-op 시 호출 2줄 NameError + `try/except` 블록화는 INV-2 grep gate 걸림 + "2줄 외 0" diff 초과, MCT-180 ESCALATE 동형 구현 불가 명세) | P0 | **설계 원인** (구현 불가 명세 — executable 명세 의무) | git 실측 정확 hunk 재대조 (`reader_cache.py` producer-wiring 블록 = **line 339-348**, 주석 1+import 6 multi-line+빈줄+호출 2). **채택안 (A) 확정** = 외부 import 없는 내부 no-op 블록 치환 (data.metrics 신설 회피 — (B)는 MCT-185 scope 침범 기각). §3.5/§8.1/§8.2 정확 hunk range 339-348 명문 + INV-2 grep 무위반 (외부 import 0) + **P0-3 회귀 test `tests/test_io_stats_no_engine_dep.py` 추가 의무** (engine.metrics 미설치 시 stats() 정상 dict 반환 NameError/ImportError 0) |
| P1-1 byte-equiv 검증 source pin 부재 (engine#N 삭제 후 재현 불가, carry 비차단) | P1 | **설계 보강** | §8.0 V-pin gate 추가 (data#N 착수 시점 engine `origin/main` rev-parse hash 1회 record) + §8.1 INV-1/§8.2 비교 source = pinned tree 명문 |

**root-cause-decision table 적용**: 설계 리뷰 P0×3 → 전부 설계 원인 (table 정합 —
설계 리뷰 P0 = 항상 설계). **수용, 반론 없음.** ArchitectPL 직접 회귀 정정 완료
(DeveloperPL 미개입 — 설계 lane 내 cross-document reconcile + executable 명세 정정).
Deputy 재spawn 0 (CodebaseMapper fact 재실측은 PL 직접 verified-via git show, P0-3
hunk 재대조).

**4 산출물 동반 reconcile 표 (P0-1, PMO-AUDIT-MCT-182 §4 forcing function)**:

| 산출물 | ADR-027 amendment 박제 텍스트 | 정정 |
|--------|------|------|
| scope_manifest §planned_adrs.amendments[1] | `section: io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2` / `owner_story: MCT-183 (io reader 6 module relocate)` | ✅ 6-module 확장 |
| ADR-027 amendment box (헤더 + D-row 인용) | "io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2 소유" | ✅ scope_manifest 와 byte 동일 |
| Change Plan §3.6 row 4 + §10 + frontmatter | 6-module list 명시 (괄호 회피 정직 판정) | ✅ 1:1 |
| Story §4.3 row + frontmatter related_adrs + §5 AC-5 | "io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2" | ✅ 1:1 |

**VERDICT (설계리뷰 iter1 FIX 회귀)**: P0×3 + P1×1 전수 정정 완료 (4 산출물 동반
reconcile + executable 명세 확정 + Story 역전파). io relocate 본질 무변경 (code-logic
0 변경 — namespace/no-op/문서 정합만). **설계 리뷰 재실행 신호** (Orchestrator 경유
DesignReviewPL 재스폰).

- **잔여 risk (정정 후)**:
  - **R1 (cross-repo desync 7회째, HIGH)** — §8.0 Phase 0 Gate (V1+V3+V5+V6+V-pin) +
    §3.6 D-row reconcile (P0-1 4 산출물 6-module byte 1:1) + §3.5 채택안 A executable
    명세로 완화. **설계 lane 사전 차단 1건 실증** (reader_cache.py stats()
    producer-wiring 블록 339-348 — Story §0 V5 미포착분, 코드 작업 전 발견 → 채택안
    A no-op 블록 명문화). MCT-179/182 cross-document desync 동형 = 설계리뷰 iter1
    에서 4 산출물 reconcile 로 사전 차단 (PMO-AUDIT-MCT-182 §4 forcing function
    self-discipline 실증 — 1 FIX 사이클 비용으로 carry 차단)
  - **R2 (MCT-41 블락, HIGH)** = MCT-186 owner (본 Story = engine io/ dead-in-prod +
    data namespace 배치, MCT-41 파일 disjoint — 병렬 안전, 본 Story 무관)
  - **잔여 carry over (MCT-185)**: reader_cache.py stats() Gauge 실 emit 재배선 (data
    측 동등 Gauge 신설 + producer wiring) = MCT-185 cold-read cutover owner (본 Story =
    채택안 A no-op only, scope 경계 박제). engine.metrics 고아 setter cleanup = MCT-185/188 carry

### 12.3 ArchitectPL 설계리뷰 iter2 FIX 회귀 정정 (2026-05-16, design-review iter 2/3)

설계리뷰 iter2 verdict = FIX (P0×1 잔존 — **P0-1-residual**). P0-2/P0-3/P1-1 = iter1
해소 confirm (재변경 금지, 회귀 0 유지). root-cause-decision 정합 (설계 리뷰 P0 →
설계 원인). ArchitectPL 직접 회귀. **narrow scope — 단일 축: ADR-027 MCT-183
amendment 전수 canonical 통일**.

| finding | severity | 최종 판정 | 정정 |
|---------|----------|-----------|------|
| P0-1-residual (iter1 부분 이행 carry — 핵심 4산출물 6-module canonical 정정 완료 byte 1:1 ✓ 이나 연계 권위 SSOT 5곳 2-module 축약 잔존, MCT-179/182 desync **4회째 동형**) | P0 | **설계 원인** (1차 정정 부분 이행 carry — PMO-AUDIT-MCT-182 §4 forcing function 예측 패턴 실증) | ADR-027 MCT-183 amendment 전수 grep canonical 통일 **6곳** (scope_manifest:61 §D6 rationale + scope_manifest:90 §story_decision_matrix cross_repo + ADR-029:107-109 box cross-ref + Story:149 §2 비목표 D6 + Story:534 §7.2 cross-ref + Story:263 §4.0 동형) → canonical string `io reader 6 module (endpoint_router/dr_mode/reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2` byte 통일. **§3.6.1 잔존 축약 grep gate 박제** (5 산출물 전수, 후행 lane verdict 전 자동 검출 — MCT-179/182/183 desync 동형 영구 차단 forcing function) |

**root-cause-decision table 적용**: 설계 리뷰 P0×1 → 설계 원인 (table 정합). **수용,
반론 없음.** ArchitectPL 직접 회귀 (DeveloperPL 미개입 — narrow scope cross-document
canonical 통일). Deputy 재spawn 0. **iter1 해소 항목 재변경 금지 확인**: P0-2 (Story
역전파) / P0-3 (채택안 A executable 명세) / P1-1 (V-pin source pin) = byte 동일 유지
(회귀 0 — io relocate code-logic 무변경).

**전수 grep 결과 evidence (정정 후)**:
- 잔존 축약 grep gate (§3.6.1) 실행 = **실 stale 0** (매치 3건 = 전부 정상: §10 FIX
  Ledger iter2 P0-1-residual finding 이력 인용 1 + §3.6.1 grep gate 패턴 정의 1 +
  gate 예외 부연 설명 1 — 모두 gate 예외 명문 정합)
- canonical string 전수 count = scope_manifest 3 + ADR-027 1 + Story 4 + Change Plan
  6 = **14건** (ADR-029 = line-wrap cross-ref 6-module 완전 동반 L109-111 + amendment
  box 본문 "io reader 6 module relocated" 박제 L50/54/65 — canonical 의미 정합)
- iter1 핵심 4산출물 (§planned_adrs.amendments / ADR-027 box 헤더 / Change Plan §3.6
  row 4 / Story §4.3·AC-5·frontmatter) = byte 1:1 재확인, **재변경 0** (지정 4산출물
  iter1 정정 보존)

**reconcile gate 박제 위치**: Change Plan **§3.6.1** (ADR-027 amendment canonical
string + 잔존 축약 grep gate). data#N 착수 전 + DesignReview/CodeReview lane verdict
직전 의무 검증 (0 이 아니면 P0 차단) — PMO-AUDIT-MCT-182 §4 Option A forcing function
self-discipline 실 박제.

**VERDICT (설계리뷰 iter2 FIX 회귀)**: P0-1-residual 정정 완료 (ADR-027 amendment
6곳 canonical 통일 + §3.6.1 grep gate 박제). P0-2/P0-3/P1-1 iter1 해소 confirm
(재변경 0). io relocate code-logic 무변경. **설계 리뷰 iter3 재실행 신호** (Orchestrator
경유 DesignReviewPL 재스폰 — narrow scope).

### 12.4 ArchitectPL 설계리뷰 iter3/3 RESET 수렴 회귀 (2026-05-16, design-review RESET)

설계리뷰 iter3/3 (max) = FIX P0×2 → fix-ledger-schema 3종 escalation trigger 0 충족
→ Orchestrator **RESET path 채택** (사용자 escalation 생략, 수렴 경로 명확). RESET
설계-리뷰 카운터 → ArchitectPL **수렴 회귀** (마지막 — 전수성 절대 보장 의무).
root-cause-decision 정합 (설계 리뷰 P0 → 설계 원인).

**근본 진단**: cross-document SSOT desync **5회 누적** (MCT-179→182→183 iter1→2→3).
매 iter ArchitectPL **지정 산출물만** 정정 → Codex 넓은 grep 이 미지정 1곳 추가
적발. 근본 = **수동 "지정 목록" reconcile 방식 자체가 누락 구조적** + 구 gate 가
조사(`로`)/따옴표 고정이라 ADR-031:139 변형(조사/따옴표 없음) + MCT-182 sibling
Story owner-scope 기술 놓침.

| finding | severity | 최종 판정 | 정정 |
|---------|----------|-----------|------|
| P0-1-residual-2 (6번째 산출물 ADR-031:139 amendment table row 2-module 축약 + sibling MCT-182:28/235 owner-scope 기술 축약 — 지정 목록 방식 5회째 carry) | P0 | **설계 원인** (수동 지정 목록 구조적 한계) | ADR-031:139 row canonical 6-module + owner `MCT-183 (io reader 6 module relocate)` 정정 (ADR-031:98 §D2 = 6-module 정상 inventory 정정 불요) + **sibling MCT-182:28 frontmatter related_adrs + MCT-182:235 Continuity 표 canonical 정정** (전수성 — owner-scope 기술 SSOT 는 sibling Story 라도 통일 의무) |
| P0-2-gate (§3.6.1 grep gate forcing function 불완전 — 지정 5산출물 scope + 조사/따옴표 고정 pattern 으로 ADR-031:139 변형 미포착, gate 무력) | P0 | **설계 원인** (gate 자체 사각 — 자기검증 부재) | §3.6.1 **gate v2 완전화**: ① scope = glob 기반 (`docs/adr/ADR-0*.md docs/stories/MCT-18*.md docs/change-plans/MCT-18*.md` + scope_manifest — 지정 목록 탈피) ② pattern = 변형포괄 regex `endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat|이전)` (조사 optional + 따옴표 optional + 구분자 변형 + ko/en) ③ **gate self-verify TEST1/TEST2 명문** (TEST1 = ADR-031:139 변형 신 pattern MATCH ✓ / 구 pattern NO MATCH ✗ 실증 / TEST2 = canonical false positive 0) ④ 예외 필터 보강 (io/ 6-module inventory + sibling Story + gate 정의 자체) ⑤ 전수성 절대 보장 = repo-wide grep 의무 명령 |

**root-cause-decision table 적용**: 설계 리뷰 P0×2 → 전부 설계 원인 (table 정합).
**수용, 반론 없음.** ArchitectPL RESET 수렴 회귀 (DeveloperPL 미개입). Deputy
재spawn 0. **iter1-2 해소 항목 재변경 0 confirm**: P0-2 (Story §6 INV byte) /
P0-3 (채택안 A 339-348 no-op + test_io_stats_no_engine_dep §8 — 채택안 A count
Change Plan 19 + Story 9 유지) / P1-1 (§8.0 V-pin gate line 441 보존) / iter1-2
핵심 6곳 canonical = byte 보존 (io relocate code-logic 무변경).

**전수성 절대 보장 evidence (지정 목록 탈피 — repo-wide grep)**:
```
[repo-wide grep] grep -rn "endpoint_router" docs/ scope_manifests/ | grep -iE \
  "endpoint_router[ +/]+dr_mode.{0,40}(relocat|이전)" | grep -ivE "<예외 필터>"
→ 0줄 (rc=1) — ADR-027 amendment 2-module 축약 repo 전체 소멸, 실 stale 0
[gate v2 실행] glob-scope + 변형포괄 pattern + 예외 필터 완전 보강
→ 0줄 (rc=1) — gate v2 PASS, false positive 0
[gate self-verify] TEST1: ADR-031:139 원본 변형 → 신 pattern MATCH ✓ /
  구 pattern NO MATCH ✗ (iter3 carry 근본 원인 실증). TEST2: canonical → NO MATCH ✓
```

ADR-031:139 정정 후 canonical = `io reader 6 module (endpoint_router/dr_mode/
reader_cache/cold_reader/tier_reader/l1_reader) relocated to mctrader-data Layer2`
+ owner `MCT-183 (io reader 6 module relocate)`. MCT-182:28 frontmatter +
MCT-182:235 Continuity 표 동일 canonical 통일 (sibling Story 전수성).

**reconcile gate 박제 위치 + scope/pattern diff**:
- 위치 = Change Plan **§3.6.1** (gate v2 — glob-scope + 변형포괄 + self-verify)
- scope diff: 지정 5산출물 list → **glob `docs/adr/ADR-0*.md docs/stories/MCT-18*.md
  docs/change-plans/MCT-18*.md` + scope_manifest** (지정 목록 탈피, 차후 누락 방지)
- pattern diff: `endpoint_router ?/ ?dr_mode relocated|..로 relocated\(Layer2 소유\)\"`
  (조사/따옴표 고정) → `endpoint_router[ +/]+dr_mode[^\n]{0,40}(relocat|이전)`
  (조사/따옴표 optional + 구분자 변형 + ko/en 포괄 — self-verify TEST1 검증)

**수동 reconcile 한계 = codeforge upstream ADR escalation 후보** (PMO retro 입력):
지정 목록 방식이 5회 carry 발생 → 자기검증 gate (glob-scope + 변형포괄 + self-verify)
forcing function 일반화 = codeforge plugin design lane SSOT reconcile 표준 후보
(PMO-AUDIT-MCT-182 §4 Option A 의 자기검증 완전 박제 형태). escalate-and-fix 정합.

**VERDICT (설계리뷰 iter3 RESET 수렴 회귀)**: P0-1-residual-2 + P0-2-gate 정정
완료 (ADR-031:139 + sibling MCT-182:28/235 canonical 통일 + §3.6.1 gate v2 자기검증
완전화). 전수성 절대 보장 = repo-wide grep 0줄 + gate v2 PASS + self-verify
TEST1/TEST2 실증. iter1-2 해소 confirm (재변경 0). io relocate code-logic 무변경.
**설계 리뷰 재실행(post-RESET) 신호** (Orchestrator 경유 DesignReviewPL 재스폰 —
RESET 카운터, 수렴 경로 명확).
