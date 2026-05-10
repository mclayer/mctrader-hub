---
adr_id: ADR-024
title: Coverage / Status 측정 SSOT cover 범위 audit 의무 (dashboard 신설 시)
status: Proposed
date: 2026-05-11
related_story: null
category: Architecture / Data & Storage
evidence:
  - RETRO-data-collection-monitor-2026-05-09.md (Pattern X3 — file_count_today dead field)
  - RETRO-data-collection-candle-tab-fix-2026-05-10.md (trigger, Pattern X6/X7/X8)
related_adrs:
  - ADR-009 (OHLCV schema + partition layout)
  - ADR-018 (defensive coding baseline)
  - ADR-020 (PMO 회고 자동 dispatch)
  - ADR-022 후보 (작업 시작 게이트)
  - ADR-023 후보 (UI/로직 분리 pure helper)
---

# ADR-024: Coverage / Status 측정 SSOT cover 범위 audit 의무 (dashboard 신설 시)

## Status

Proposed — 2026-05-11. RETRO-data-collection-candle-tab-fix-2026-05-10.md §4 발의 → Orchestrator ADR 파일 직접 land.

1-week stress-test observation 후 Accepted 로 승격 예정.

## Context

### 발의 경위

2026-05-11 (세션 2026-05-10 이어짐) `mctrader.mclayer.it/data_collection` 페이지의 캔들 탭이 항상 "캔들 미수집" 을 표시하는 버그 발생. 사용자 보고 → Systematic Debugging Phase 1 에서 근본 원인 확인.

### 근본 원인 (Pattern X6)

| 단계 | 문제 |
|---|---|
| **데이터 수집** | `backfill` 커맨드가 OHLCV parquet 파일을 기록 (`market/ohlcv/schema_version=ohlcv.v1/...`) |
| **SSOT 불일치** | `coverage-stats.json` 은 WS event stream (tick/orderbook) tier 만 cover, backfill REST 수집 tier 는 cover 0 |
| **대시보드 오진단** | dashboard 가 `coverage-stats.json` 을 OHLCV candle tier 의 SSOT 로 채택 → candle tier = 항상 empty → "캔들 미수집" 표시 |
| **spec 박제 (Pattern X7)** | 선행 fix 가 "캔들 미수집 — OHLCV 집계는 compactor 또는 별도 REST API 수집기가 필요합니다" 를 안내문으로 추가, 결함을 의도된 동작으로 박제 |
| **수정 (Pattern X8)** | OHLCV parquet 디렉터리 직접 스캔 어댑터 (`ohlcv_coverage_adapter.py`) 신규 작성, 대시보드 §3/§4-A 교체 → 1차 fix 에서 ADR-009 §D2.1 `node=/` 파티션 누락, 5분 내 자가 정정 |

### 선행 사례 (Pattern X3 — RETRO-data-collection-monitor-2026-05-09.md §3)

`CoverageStatsWriter.TierStats.file_count_today` 필드가 WAL 레이어에서 항상 0 으로 기록됨. dashboard 가 해당 필드를 표시하지만 실질 데이터 없음. 수집 경로와 측정 경로의 cover 범위 불일치가 동일 패턴의 선행 사례.

### 영향 범위

- **silent duration**: 캔들 탭이 실제 OHLCV 데이터가 쌓이고 있음에도 수개월간 "미수집" 표시 가능성
- **운영 오판단**: backfill 정상 동작 여부를 dashboard 로 판단 불가
- **spec drift**: 결함 고착이 수집 아키텍처에 대한 잘못된 이해를 문서화

## Decision

### D1. Dashboard 신설 spec 에 "SSOT cover 범위" 절 의무

신규 dashboard tile / monitor / health-check section 을 설계할 때 spec 문서 (`docs/superpowers/specs/<date>-<slug>.md`) 에 다음 subsection 을 반드시 포함한다:

```markdown
## SSOT Cover 범위

| 표시 항목 | 측정 SSOT | cover 범위 | 미포함 데이터 소스 |
|---|---|---|---|
| 캔들 커버리지 | OHLCV parquet scan | backfill REST 수집 | WS compact (미구현) |
| tick lag | coverage-stats.json | WS event stream | REST backfill |
```

- **적용 조건**: 새 dashboard page 또는 기존 page 에 새 monitoring section 추가 시
- **검증 시점**: spec review 단계 (codeforge-design ArchitectPLAgent 또는 spec-reviewer)
- **"미수집" / "empty" 분기**: 기본 메시지에 `측정 source: <SSOT>` 명시 의무

### D2. "미수집" / "empty" 분기 메시지 포맷 의무

Dashboard 에서 데이터가 없음을 표시할 때 다음 포맷을 사용한다:

```python
# 올바른 예
st.info(
    "캔들 미수집 — OHLCV parquet 파일 없음 (측정 source: market/ohlcv/ 디렉터리 스캔)\n\n"
    "backfill 컨테이너(`backfill-bithumb`, `backfill-upbit`) 실행 상태를 확인하세요."
)

# 잘못된 예 (spec 박제 Pattern X7 재발 가능)
st.info(
    "캔들 미수집 — 현재 수집기 구독 채널: `transaction, orderbookdepth, orderbooksnapshot`\n\n"
    "OHLCV 집계는 compactor 또는 별도 REST API 수집기가 필요합니다."
)
```

메시지에 포함해야 할 요소:

| 요소 | 예시 |
|---|---|
| 미수집 판정 근거 | "OHLCV parquet 파일 없음" |
| 측정 SSOT 명시 | "(측정 source: market/ohlcv/ 디렉터리 스캔)" |
| 운영 액션 | "backfill 컨테이너 실행 상태를 확인하세요" |

### D3. Partition-scan adapter 작성 시 ADR cross-reference + fixture 검증 의무

신규 Hive partition 스캔 어댑터 (예: `ohlcv_coverage_adapter.py`) 를 작성할 때:

1. **ADR cross-reference**: 해당 partition layout 을 정의한 ADR 을 docstring 에 명시
   ```python
   """OHLCV parquet 디렉터리 스캔 어댑터.

   Partition layout: ADR-009 §D2 (derive_partition_path).
   node= leaf level: ADR-009 §D2.1 (HA active-active).
   """
   ```

2. **Fixture 프로덕션 답습**: 테스트 fixture 가 `node=` 서브디렉터리 레벨을 포함한 실제 partition 구조를 검증
   ```python
   # 프로덕션 경로: date_dir/node={node_id}/part-*.parquet
   # 테스트 fixture 가 node= 서브디렉터리 케이스 포함 의무
   def test_scan_with_node_partition(tmp_path):
       date_dir = ... / "date=03" / "node=NODE_A"
       (date_dir / "part-abc.parquet").write_bytes(b"x")
       result = scan_ohlcv_coverage(tmp_path)
       assert result.has_data
   ```

3. **rglob vs glob 선택**: `date_dir/*.parquet` (glob) 대신 `date_dir/**/*.parquet` (rglob) 또는 명시적 서브디렉터리 순회 — ADR-009 §D2.1 의 `node=` 레벨 존재 가능성 전제

### D4. 기존 adapter 소급 감사 (1-week observation 기간)

이 ADR accept 시점으로부터 1주 이내, 기존 coverage / status adapter 에 대해 D1~D3 를 소급 감사한다:

| 대상 | 감사 항목 |
|---|---|
| `coverage_stats_adapter.py` | SSOT = `coverage-stats.json`, cover = WS event stream only → 명시 comment 추가 |
| `status_adapter.py` | SSOT = `heartbeat-*.json`, cover = WS daemon heartbeat only → 명시 |
| `ohlcv_coverage_adapter.py` | ADR-009 cross-reference docstring + `node=` fixture (D3 즉시 적용 완료 여부 확인) |

## Alternatives Considered

### A1. `coverage-stats.json` 에 backfill tier 추가 — 기각

- **제안**: backfill 커맨드 종료 시 `coverage-stats.json` 의 candle tier 를 업데이트
- **기각 사유**:
  - `coverage-stats.json` 은 WS daemon 프로세스 내 in-memory 상태의 flush (5분 주기), backfill 은 일회성 CLI batch — 책임 혼합
  - WS daemon 재시작 시 `coverage-stats.json` 리셋됨 → backfill 기록 유실
  - 두 데이터 소스를 단일 파일에 혼합 시 SSOT 분리 원칙 위반

### A2. coverage-stats.json schema 에 backfill 섹션 추가 — 기각

- **제안**: `{"ws_tiers": {...}, "backfill_tiers": {...}}` 로 schema 확장
- **기각 사유**: backfill 은 이미 parquet 파일을 생성하며, 그 파일 자체가 최신 상태의 SSOT. 별도 JSON 은 중간 표현(intermediate representation) 을 추가하는 것이며, SSOT 가 parquet 인 상황에서 중간 표현 관리 overhead 만 증가.

### A3. Dashboard 에 "캔들 미수집 — 설계상 미구현" 표시 — 기각 (Pattern X7 재발)

- **제안**: "이것은 미구현 기능이므로 정직하게 안내한다"
- **기각 사유**: 실제로 backfill 은 데이터를 기록하고 있다. "미구현"으로 표시하는 것은 사실과 다르며, 운영자가 실제 수집 상태를 파악할 수 없게 한다. Pattern X7 (묵시 가정의 사양 박제) 재발.

## Consequences

### C1. Dashboard spec 품질 향상

D1 의 "SSOT cover 범위" 절 의무화로 신규 dashboard section 설계 시점에 데이터 소스와 측정 경로의 불일치가 조기 발견된다. spec review 에서 cover 범위 누락이 차단 요소가 됨.

### C2. Pattern X7 재발 차단

D2 의 메시지 포맷 의무화로 "결함을 의도된 동작으로 박제" 하는 Pattern X7 이 구조적으로 차단된다. "미수집" 메시지는 반드시 측정 SSOT 와 운영 액션을 포함해야 하므로, 개발자가 SSOT cover 범위를 검토하지 않고 안내 메시지를 작성할 수 없다.

### C3. Adapter 코드 품질 향상

D3 의 ADR cross-reference + fixture 검증 의무로 신규 partition-scan adapter 작성 시 partition layout ADR 을 필수 참조하게 되며, `node=` 같은 edge-case leaf level 이 누락되는 Pattern X8 이 차단된다.

### C4. 소급 audit overhead (D4, 단기)

기존 3개 adapter 에 대한 1-week 소급 감사가 추가 작업이 된다. 대상이 3개 파일로 한정적이므로 overhead 는 낮다.

### C5. ADR-022/ADR-023 후보와의 관계

- **ADR-022 후보 (작업 시작 게이트)**: 본 ADR D1 의 "spec review 단계 검증" 은 ADR-022 의 작업 시작 게이트 내 spec audit 항목으로 자연 통합됨. ADR-022 채택 시 D1 검증을 game-of-tasks 시작 체크리스트에 포함.
- **ADR-023 후보 (UI/로직 분리 pure helper)**: `ohlcv_coverage_adapter.py` 가 UI 와 스토리지 스캔 로직 분리의 2번째 실증 사례. ADR-023 채택 시 D3 의 adapter 패턴이 공식 구현 가이드로 승격.

## Cross-references

- `docs/retros/RETRO-data-collection-candle-tab-fix-2026-05-10.md` (trigger, Pattern X6/X7/X8)
- `docs/retros/RETRO-data-collection-monitor-2026-05-09.md` (Pattern X3 선행 사례)
- `mctrader-web` commit `f174926`, `e8cef62` (implementation evidence)
- ADR-009 §D2, §D2.1 (OHLCV partition layout + node= HA level)
- ADR-018 (defensive coding baseline — 경계 검증 의무)
- ADR-020 (PMO 회고 자동 dispatch — 본 ADR 발의 경로)
- ADR-022 후보 (작업 시작 게이트)
- ADR-023 후보 (UI/로직 분리 pure helper)
- `mctrader-web/src/mctrader_web/dashboard/ohlcv_coverage_adapter.py` (D3 즉시 적용 구현체)
- `mctrader-web/src/mctrader_web/dashboard/coverage_stats_adapter.py` (D4 소급 감사 대상)
