# RETRO — Data Collection 캔들 탭 "캔들 미수집" 오진단 fix (mctrader-web)

**범위**: mctrader-web (`ohlcv_coverage_adapter.py` 신규 + `pages/20_data_collection.py` §3 candle 카드 + §4-A candle 탭 교체)
**기간**: 2026-05-10 (single calendar day, post-MCT-126 same-session, MCT-127 직후)
**Trigger**: 사용자 보고 — 데이터 수집 대시보드의 캔들스틱 탭이 항상 "캔들 미수집" 메시지 표시
**Status**: mctrader-web `main` 직접 push 2 commit (`f174926` + `e8cef62`), CI green
**선행 회고**: `RETRO-data-collection-monitor-2026-05-09.md` (CoverageStatsWriter + 4-section page 신설)
**Story 분류 결정**: 신규 Story 생성 보류 — 선행 RETRO 의 §3 Pattern X1/X2/X3/X5 의 후속 fix 로 분류 + 본 RETRO 가 cross-reference

---

## 0. Story 분류 결정 (PMOAgent)

본 fix 의 origin Story 후보:

| 후보 | 적합성 | 판단 |
|---|---|---|
| **MCT-103** (50-symbol universe) | **불일치** — 50 sym 가동 자체는 무관, OHLCV backfill write path 도 본 작업 trigger 아님 | reject |
| **MCT-104** (`exchange_metadata.v1` + `orderbook_snapshot.v1`) | **불일치** — WS snapshot 채널 + metadata partition 작업이라 candle 미수집과 무관 | reject |
| **MCT-126** (Main Dashboard + Nav) | **인접 페이지** (`pages/main.py` vs `pages/20_data_collection.py`) 이지만 다른 페이지·다른 책임 | reject |
| **MCT-127** (codeforge plugin upgrade) | doc-only / 무관 | reject |
| **신규 Story** (MCT-128 등) | mid-size feature 가 아닌 **단일 페이지 단일 탭 fix** + 1-day single session + 2 commit + clean fix-pass | **scope 과대 — 본 fix 는 RETRO-only path 가 적절** |
| **RETRO-data-collection-monitor-2026-05-09** | 본 fix 가 surface 한 결함은 **선행 RETRO 의 Pattern X3 (file_count_today dead field) 의 sibling 결함** + Pattern X2 (Story 파일 부재로 §11 retro pointer 박제 대상 부재) 의 직접 영향 | **adopt — RETRO cross-reference path** |

→ **결정**: 본 RETRO 파일 land + RETRO-data-collection-monitor-2026-05-09 의 §3 Pattern X 시리즈에 cross-reference (Pattern X6 신설). MCT-127 §1 모범 패턴 (doc-only fast-pass + scope 좁음) 정합. **별도 신규 Story 파일 생성 비채택**.

근거: 본 작업은 RETRO-data-collection-monitor-2026-05-09 §8 권고 ("MCT-119 등 retroactive Story") 의 자연 follow-up 이지만, **2 commit + 단일 페이지 + 단일 탭 fix scope** 라 Story §1-§11 templating cost 가 ROI 미달. RETRO-only path 가 본 결함의 SSOT 박제로 충분 — 단, **선행 RETRO 의 Pattern X 시리즈에 cross-reference 추가 의무** (다음 §5 권고).

---

## 1. 결과 요약

### 1.1 산출물

**mctrader-web `main` 2 commit**:

| Commit | 변경 | LOC |
|---|---|---|
| `f174926` fix(dashboard): candle 탭 OHLCV parquet 직접 스캔으로 '캔들 미수집' 버그 수정 | `ohlcv_coverage_adapter.py` (신규) + `pages/20_data_collection.py` (§3 candle 카드 + §4-A candle 탭) + `tests/dashboard/test_ohlcv_coverage_adapter.py` (신규 10 tests) + `tests/apptest/test_page_20_data_collection.py` (monkeypatching 추가) | +427 / -61 |
| `e8cef62` fix(ohlcv-adapter): rglob node= 서브디렉 처리 + zfill 제거 + TTL 만료 테스트 | `ohlcv_coverage_adapter.py` (rglob + zfill 제거) + 테스트 보강 | +29 / -2 |

### 1.2 검증 상태

| 영역 | 결과 |
|---|---|
| `pytest tests/dashboard/test_ohlcv_coverage_adapter.py` | 10 PASS (신규) |
| `pytest tests/apptest/test_page_20_data_collection.py` | PASS (monkeypatching 추가, candle 탭 분기 cover) |
| mctrader-web CI | green (584+ passed) |
| 사용자 가시성 | 50-sym universe 의 candle 파티션 (backfill 적재 분) 이 §3 candle 카드 + §4-A 탭에 즉시 노출 |

---

## 2. 잘된 점

### 2.1 Adapter 분리 패턴 답습 (선행 RETRO §2.4 schema contract via JSON 동형)

신규 `ohlcv_coverage_adapter.py` 가 기존 `coverage_stats_adapter.py` / `status_adapter.py` 와 **동형 인터페이스** 채택:

- `OhlcvCoverageResult` dataclass + `is_error` / `has_data` / `latest_date` property
- `scan_ohlcv_coverage(root, *, use_cache=True)` 단일 entrypoint
- `clear_cache()` invalidation
- 5분 TTL 캐시 (`_CACHE_TTL_SECONDS = 60.0` — 타 adapter 와 cadence 정합 가까움, 실제로는 60초 vs 300초 차이는 별도 follow-up)

→ 선행 RETRO §2.2 (heartbeat_writer 미러 패턴) 에서 발의된 "신규 컴포넌트는 인접 동형 컴포넌트의 lifecycle 을 미러" 패턴이 mctrader-web adapter 레이어에서도 자연 반복.

### 2.2 Pure scan logic 으로 Streamlit 미테스트 영역 축소 (선행 RETRO §2.3 답습)

`_scan(root: Path)` 함수가 Streamlit import 0 — pyrent unit test 10건으로 hive partition 스캔 결정성 / 캐시 TTL / OSError graceful degraded / 빈 root 처리 / 다중 timeframe 누적 모두 검증. 페이지 `pages/20_data_collection.py` 자체는 분기 추가만 (candle == OHLCV adapter, tick/orderbook == coverage-stats).

→ ADR-023 후보 (선행 RETRO §4) 의 정합 사례 추가 — **2번째 실증** (data_collection_helpers.py + ohlcv_coverage_adapter.py).

### 2.3 동일 세션 내 자가 발견 → 즉시 fix 사이클 (선행 RETRO §2.5 답습)

`f174926` land 직후 `e8cef62` 로 (a) `glob("*.parquet")` → `rglob("*.parquet")` 로 수정 (실제 hive layout 의 `node=*/` 서브디렉 처리), (b) `month.zfill(2)` / `day.zfill(2)` 제거 (이미 hive partition 이 zero-padded — double padding 결함), (c) TTL 만료 테스트 추가. 사용자 trigger 없이 **5분 내 self-correction**.

→ 선행 RETRO §2.5 (Plotly colorscale 4-point 즉시 교정) 와 동형 패턴. fix-clean 라기보다 **fix-with-immediate-self-correction** lane — 본 세션 패턴으로 박제 가치 있음.

---

## 3. 발견된 이슈 — 패턴 분석 (선행 RETRO §3 Pattern X 시리즈 확장)

### Pattern X6 (신규): Coverage 측정 SSOT 가 partition 레이아웃과 불일치

**관측**:
선행 RETRO 의 4-section dashboard 가 채택한 SSOT 는 `coverage-stats.json` (5분 atomic flush by `CoverageStatsWriter`). 그러나 candle (=OHLCV) tier 의 경우:

- `coverage-stats.json` 은 collector 의 record_event 호출 시점에만 row 누적 — **WS event stream tier (tick / orderbook) 만 cover**
- OHLCV tier 는 collector 가 아닌 **별도 backfill 커맨드** (REST API 수집기) 가 적재 — record_event 호출 0 → coverage-stats 영원히 비어있음
- 사용자 관점: 50-sym universe 의 OHLCV 파티션이 `market/ohlcv/schema_version=ohlcv.v1/exchange=*/symbol=*/timeframe=*/year=*/month=*/date=*/node=*/*.parquet` 에 정상 적재되었어도, dashboard §3 candle 카드 + §4-A 탭은 항상 "캔들 미수집" 표시

**근본 원인**:

선행 RETRO 작업 시점 (2026-05-09) 에 **coverage-stats SSOT 의 cover 범위가 WS event stream 한정** 임이 spec 단계에서 명시되지 않았음. spec `2026-05-09-data-collection-monitor-design.md` §4 ("4-section page") 의 §4-A Candle 탭 정의가 "candle tier 가 coverage-stats 에 없으면 미수집 안내" 로 작성됨 → 이 가정 자체가 **OHLCV write path 와 collector record_event path 가 동형이라는 묵시 가정**에 기반.

이전 fix `01d597d` (2026-05-10 11:56) 가 이 묵시 가정을 그대로 채택 — "candle 미수집 — 현재 수집기 구독 채널: transaction, orderbookdepth, orderbooksnapshot. OHLCV 집계는 compactor 또는 별도 REST API 수집기가 필요합니다." 라는 안내문 추가. 즉 **버그를 사양으로 박제** (의도된 미수집).

본 세션이 사용자 보고를 통해 진단 정정 — 실제로는 **OHLCV partition 이 적재 중인데 SSOT 가 잘못된 source 를 보고 있음**. 신규 `ohlcv_coverage_adapter.py` 가 partition 디렉터리를 직접 스캔해 SSOT bypass.

**관련 선례**:
- 선행 RETRO §3 Pattern X3 (`file_count_today` dead field) — 같은 SSOT-vs-실제-적재 mismatch 의 sibling. 거기서는 record_event 시점에 file_count 알 수 없음 → 영원히 0. 본 사례에서는 record_event 가 OHLCV 에 호출되지 않음 → 영원히 empty.
- ADR-009 §D2.1 — `node=` partition leaf 의무. 본 fix `e8cef62` 가 `glob` → `rglob` 으로 교정한 것이 정확히 `node=*/` 서브디렉 처리. ADR 정합 검증 누락 (1차 fix `f174926` 의 결함).

**Pattern X6 의 일반화**:

```
신규 dashboard tile 추가 시:
  - SSOT (예: coverage-stats.json) 가 *어떤 write path* 에서 갱신되는지 명시
  - dashboard 가 cover 하려는 tile 의 *데이터 source path* 가 SSOT cover 범위 내인지 audit
  - cover 범위 외이면 (a) SSOT 확장 (write path 에 instrumentation 추가) 또는 (b) partition 직접 스캔 adapter 신설 — 둘 중 명시 결정
```

→ 본 결함의 진짜 origin 은 spec 단계 의 SSOT cover audit 부재. 본 RETRO 가 발의하는 ADR-024 후보 (§4 참조) 가 차단 lane.

### Pattern X7 (신규): 묵시 가정의 사양 박제 (semantic drift)

**관측**:
이전 fix `01d597d` 의 "OHLCV 집계는 compactor 또는 별도 REST API 수집기가 필요합니다" 라는 안내문이 dashboard 에 land — 이는 **결함의 사용자 가시화** + **결함을 의도된 동작으로 박제** 의 이중 effect.

**근본 원인**:
- 진단 시점에 "candle tier 가 coverage-stats 에 없다" → "candle 수집 안 된다" 로 추론. 두 단계 모두 옳지만 결론이 잘못됨 — coverage-stats 의 *cover 범위* 가 누락 변수.
- 안내문이 dashboard land 후 사용자가 실제로 보고했을 때만 결함 노출. 만약 사용자가 reporting 하지 않았다면 **silent debt** 으로 잔존.

**일반화**:

```
"미수집" / "데이터 없음" / "측정 불가" 등 default-to-empty 분기는:
  - 분기 도달 시점에 SSOT 의 cover 범위 검증 의무
  - 분기 자체에 "측정 source: <SSOT name>" 명시 (사용자가 결함 발견 시 root cause 추적 가능)
  - silent debt 회피 — empty 상태가 normal vs anomaly 인지 명시
```

→ Pattern X4 (선행 RETRO `test_run_flushes_periodically` 취약 assertion) 의 dashboard 영역 확장. test 든 dashboard 든 **negative 분기 (없음 / 실패) 의 default 가 false-positive 진단 가능성** 잠재.

### Pattern X8 (신규): 1차 fix 의 ADR 정합 검증 누락

**관측**:
1차 fix `f174926` 의 `_scan` 함수가 hive partition 의 leaf level 을 `for pq_file in date_dir.glob("*.parquet")` 로 스캔. 그러나 ADR-009 §D2.1 의 `node=` partition leaf 의무에 따르면 실제 layout 은 `date=*/node=*/*.parquet` — `glob("*.parquet")` 는 `node=*` 디렉터리만 매치하고 그 아래 parquet 미스. land 후 5분 내 `e8cef62` 에서 `rglob` 로 교정.

**근본 원인**:
- 1차 fix 작성 시 ADR-009 §D2.1 cross-reference 누락 — partition layout 의 leaf level 가정이 실제 layout 과 불일치
- TDD 가 적용됐지만 (10 unit tests in `f174926`) **fixture 가 `node=*/` 서브디렉 없이 작성** — 실제 hive layout 을 답습하지 않은 fixture 는 결함 미검출
- `e8cef62` 에서 fixture 보강 (TTL 만료 + node 서브디렉 처리)

**일반화**:

```
파티션/스토리지 layout 을 스캔하는 신규 adapter:
  - ADR (특히 §D 시리즈) 의 partition layout 명세 cross-reference 의무
  - test fixture 가 *프로덕션 실제 layout* 답습 의무 (toy fixture 거부)
  - 실제 데이터 디렉터리 (개발자 머신의 mctrader_data 마운트) 로 1회 smoke 검증 의무
```

→ 선행 RETRO §3 Pattern X4 (TDD test design 강화) 의 partition-layout 영역 확장.

---

## 4. ADR 후보 발의 (Orchestrator 회신용)

PMO `pmo_output v1.adr_proposal` 필드 inline 반환:

### ADR-024 후보: Coverage 측정 SSOT cover 범위 audit 의무 (dashboard 신설 시)

```
category: Architecture / Data & Storage
title: ADR-024: Coverage / Status 측정 SSOT cover 범위 audit 의무
trigger: 2026-05-10 mctrader-web data_collection 페이지의 candle 탭이
         coverage-stats.json (WS event stream cover only) 을 OHLCV (REST backfill cover)
         tier 측정 source 로 잘못 채택 → "캔들 미수집" 오진단 사용자 가시화
배경:
  - 선행 RETRO Pattern X3 (file_count_today dead field) 의 sibling 결함
  - SSOT 가 *어떤 write path* 에서 갱신되는지 dashboard tile 신설 시 명시 의무 부재
  - 결과: tile 이 cover 범위 외 데이터를 측정 source 로 채택 시 silent empty
문제:
  - dashboard / monitor / health-check tile 신설 시 SSOT cover 범위 검증 lane 부재
  - 결함이 사용자 보고 (production smoke) 후에야 catch — RETRO-MCT-126 §10 admin_overview 4-RC 와 동형 lane
  - "미수집" / "데이터 없음" default 분기가 false-positive 진단 박제 (Pattern X7 의 사양화)
제안 결정:
  - D1 — dashboard tile / monitor 신설 spec 에 "SSOT cover 범위" 절 의무 추가
      a) SSOT name (예: coverage-stats.json)
      b) SSOT 가 갱신되는 write path 목록 (예: collector record_event)
      c) 본 tile 이 cover 하려는 데이터의 source path (예: OHLCV partition)
      d) (b) ⊇ (c) 검증 결과 + 미달 시 (e1) SSOT 확장 또는 (e2) 직접 스캔 adapter 신설 결정
  - D2 — "미수집" / "empty" 분기 default 메시지에 "측정 source: <SSOT>" 명시 의무
      → 사용자가 결함 발견 시 root cause 추적 가능
  - D3 — 신규 partition-scan adapter 작성 시 ADR (§D 시리즈) cross-reference + fixture 가
        프로덕션 실제 layout 답습 의무 (toy fixture 거부, Pattern X8 차단)
예상 결과:
  - SSOT-vs-source mismatch silent debt 0건
  - "미수집" 분기 false-positive 진단 lane 차단
  - partition layout 변경 시 (예: ADR-009 §D2.1 의 node= 추가) 적응 lane 강화
```

### (선행 RETRO §4 ADR-022 / ADR-023 후보 재발의 강화)

본 fix 작업 자체도 **MCT-XXX Story 부재** + **base branch 검증 누락** 가능성에 노출됐으나, 다행히 (a) 1-day single session, (b) 2 commit 만, (c) 사용자 직접 보고 trigger 라 silent loss 발생 안 함. 다만:

- ADR-022 (작업 시작 게이트) 가 채택됐다면 본 작업 시점에도 Story 자동 생성 제안이 있었을 것 — 별도 신규 Story 파일 land vs RETRO-only path 의 trade-off 분석이 게이트 단계에서 이루어졌을 것
- ADR-023 (UI/로직 분리 — pure helper module) 의 2번째 실증 사례로 본 fix 의 `ohlcv_coverage_adapter.py` 가 정합

→ ADR-022 / ADR-023 발의는 선행 RETRO 의 발의분 그대로 — 본 RETRO 가 trigger evidence 1건 추가 (총 2건 evidence).

---

## 5. 개선 제안 3건 (다음 세션 반영)

1. **선행 RETRO Pattern X 시리즈 cross-reference 갱신** — `RETRO-data-collection-monitor-2026-05-09.md` §3 끝에 본 RETRO link 추가 (Pattern X6/X7/X8 후속). PMOAgent 본 dispatch 의 Edit 산출물로 처리.

2. **Dashboard tile 신설 spec 템플릿 보강** — `docs/superpowers/specs/<date>-<slug>.md` 의 dashboard / monitor / health-check section 에 "SSOT cover 범위" subsection 의무화. 다음 dashboard Story 진입 시 spec 작성 lane 에 즉시 채택. ADR-024 D1 의 즉시 운영 부분.

3. **신규 partition-scan adapter 의 fixture 프로덕션 답습 체크리스트** — 신규 hive partition 스캔 함수 작성 시 ADR-009 §D2.1 (또는 해당 partition layout ADR) cross-reference 의무 + fixture 가 leaf level (`node=*/`) 포함 검증. ADR-024 D3 의 즉시 운영 부분.

---

## 6. 토큰·시간 분포 (대략)

| 구간 | 예상 분포 |
|---|---|
| 사용자 보고 → 진단 (coverage-stats vs OHLCV partition mismatch 발견) | ~20% |
| 1차 fix `f174926` — `ohlcv_coverage_adapter.py` 신규 + 페이지 분기 + 10 unit tests + apptest monkeypatching | ~50% |
| 1차 fix 자가 검증 → `node=*/` 서브디렉 누락 발견 + zfill double padding 발견 | ~10% |
| 2차 fix `e8cef62` — rglob + zfill 제거 + TTL 만료 테스트 | ~10% |
| 회고 (이 문서) | ~10% |

→ 1차 fix 가 사용자 보고에 즉시 응답 (~70% 가 fix 작업), 자가 검증 → 5분 내 2차 fix self-correction. **fix-with-immediate-self-correction lane** 패턴.

---

## 7. 관련 ADR · MEMORY · 회고

- **ADR**:
  - ADR-009 §D2.1 (`node=` partition leaf 의무) — 1차 fix `f174926` 의 결함 root cause, 2차 fix `e8cef62` 의 직접 정합
  - ADR-022 후보 (작업 시작 게이트) — 본 작업도 단일 Story 부재 lane 에 노출, 2nd evidence
  - ADR-023 후보 (UI/로직 분리 pure helper) — `ohlcv_coverage_adapter.py` 가 2nd evidence
  - **ADR-024 후보** (Coverage SSOT cover 범위 audit) — 본 RETRO 가 발의 origin
- **MEMORY**:
  - `feedback_pmo_retro_mandatory.md` — 본 회고 자동 dispatch trigger
  - `feedback_consumer_evidence_rapid_iteration.md` — 사용자 보고 → 1-day fix → 동일 세션 self-correction lane 의 정합
- **선행 회고**:
  - `RETRO-data-collection-monitor-2026-05-09.md` — Pattern X1~X5 의 origin, 본 RETRO 의 §3 Pattern X6/X7/X8 가 직접 확장
  - `RETRO-MCT-126-admin-overview-runtime-fix.md` — production smoke 첫 catch lane 의 인접 사례 (4-RC vs 본 사례 1-RC)
  - `RETRO-MCT-127.md` — doc-only / single-purpose Story 의 모범 형식, 본 RETRO 의 "신규 Story 미생성 + RETRO-only path" 결정의 정합 evidence

---

## 8. 결정 박제 — 본 RETRO 가 신규 Story 를 생성하지 않는 이유

PMOAgent `Story 분류 결정` (§0) 의 자세한 근거:

| 비교 축 | 신규 Story 생성 시 | RETRO-only path |
|---|---|---|
| Templating cost | §1-§11 + Sonnet decider + Acceptance Criteria + Evidence inventory + Test Contract — **2 commit 의 fix 에 과다** | RETRO 1 file — 적정 |
| SSOT 박제 | Story §8.5 Impl Manifest = 2 commit 정도 → 빈약 | RETRO §1.1 산출물 표 + §3 Pattern X6/X7/X8 — 충분 |
| Cross-reference | 신규 Story 가 선행 RETRO 와 새 Story 양쪽 maintain — 2 점 SSOT | RETRO 가 선행 RETRO 와 1:1 chain — 단일 SSOT |
| ADR 발의 | Story §11 carry-over → RETRO → ADR — 3 hop | RETRO → ADR — 2 hop, 즉시 |
| 회고 자동 dispatch trigger | ADR-020 (Story 완료 게이트) 의무 trigger | RETRO `feedback_pmo_retro_mandatory.md` 즉시 dispatch |
| MCT-127 모범 패턴 정합 | scope 좁음 + decider 미리 박제 + fast-pass = doc-only Story 후보 | doc-only path 도 가능하지만 scope 가 fix 1건이라 RETRO-only 가 더 정합 |

**결정**: RETRO-only path. 본 결정은 **선행 RETRO 의 Pattern X2 (Story 파일 부재) 와 다른 결정** — Pattern X2 는 mid-size feature (10 task plan + 4-section page) 가 Story 미생성한 것을 결함으로 분류, 본 사례는 2 commit fix 가 Story 미생성한 것을 정상 분류. 차이 = scope.

→ 다음 ADR-022 (작업 시작 게이트) 채택 시 본 fix 같은 *fix-only scope* 와 *mid-size feature scope* 의 Story 의무 임계가 명시 결정 의무. 본 RETRO 가 임계 candidate evidence: **2 commit + 1-day session + adapter 신규 1 + 페이지 분기 1 = RETRO-only path**, **5+ commit OR mid-size feature OR cross-repo = Story 의무**.

---

**작성**: PMOAgent (Story 완료 회고 감사 + Cross-Story 패턴 분석, codeforge-pmo plugin)
**작성일**: 2026-05-10
**관련 commit**:
  - mctrader-web: `f174926` (1차 fix) + `e8cef62` (self-correction)
**연관 RETRO**: `RETRO-data-collection-monitor-2026-05-09.md` (직접 확장 chain)
**ADR 후보 발의**: ADR-024 (Coverage SSOT cover 범위 audit) — Orchestrator 회신
