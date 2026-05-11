# Compactor 메모리 폭주 진단·안정화·재설계 — 2-Epic 설계

**날짜**: 2026-05-11
**Epic 예약**: MCT-132 (stabilize), MCT-135 (v2 재설계)
**GitHub issue 예약**: #214 (Epic-A), #215 (Epic-B)
**근본 원인 ADR**: ADR-017 §3.2 / §3.4 (현재 단일 프로세스 compactor)
**Trigger Story**: MCT-103 (50 sym 확장)

---

## §1 문제 분석

### 사실 (측정값)

- 단일 측정 (2026-05-11): `mctrader-compactor` 컨테이너 RAM **48.5 GiB / 62.73 GiB (77.32%)**, CPU **122.44%**.
- 호스트: 단일 Docker 호스트, 62.73 GiB 물리 메모리.
- 컨테이너: 단일 인스턴스 (ADR-017 §SPOF), `MCTRADER_NODE_ID` 단일 노드.

### 단발 측정의 한계 — "누수" 라는 표현은 가설이다

baseline (50 sym 확장 전) 기록 부재 + 추세 (증가/plateau) 미상.
가능 가설 4 종:
1. **Genuine leak** — ref cycle / `ParquetWriter.close()` 누락 / file handle/buffer 미해제
2. **Accumulator bloat** — L3 (24h) compaction 시 PyArrow Table 단일 materialize → 심볼당 수 GiB Table × 450 worker (50sym × 3ch × 3tier)
3. **GC retention** — PyArrow jemalloc / glibc malloc 이 free 후 OS 미반환 (RSS 고착)
4. **Legitimate scale ceiling** — 50 sym 에서 본질적으로 32+ GiB 요구

→ **측정 없이 fix 부터 들어가면 가설 오답에 시간 쓰고 재발한다.**

### MCT-103 (50 sym 확장) 이 trigger 인 근거

forward-only 누적 history (`project_universe_50.md` 메모리) + L3 daily compaction accumulator 가 결합되어 50 sym × 24h L2 Table → 단일 L3 materialize 시 폭주 가능.

---

## §2 설계 — 2-Epic 구조

### Epic-A: Compactor stabilize (1 wk)

**목적**: 즉시 OOM 위험 완화 + Epic-B 진단을 위한 관측 인프라 확보.

#### A1 Story (MCT-133) — Compactor 런타임 안정화

**범위**:
- `compose.yml`: `mctrader-compactor` 에 `mem_limit: 32g` + `restart: unless-stopped`
- 환경 변수:
  - `MALLOC_TRIM_THRESHOLD_=128k`
  - `ARROW_DEFAULT_MEMORY_POOL=system`
  - `MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS=300`
- 코드: `mctrader_data.compactor` 의 ParquetWriter close()/예외 경로 audit
  - 모든 `pq.ParquetWriter` 인스턴스 `try/finally` 또는 context manager
  - 예외 발생 시 `tmp/<target>.parquet.tmp` 정리
- 정기 `gc.collect()` 호출 — L1/L2/L3 cycle 종료 후

**진입 조건**: A2 의 1차 metric land 후 (baseline 1회 캡처 확보).

**리스크**:
- 32G mem_limit 가 정상 working set 미만이면 재시작 루프 → **그 자체가 진단 신호**, 수용.
- `ARROW_DEFAULT_MEMORY_POOL=system` 은 jemalloc → glibc 전환, free 후 OS 반환률 개선되나 allocation 속도 저하 가능 → A2 metric 으로 확인.

#### A2 Story (MCT-134) — Compactor 관측 인프라

**범위 (1차 즉시)**:
- `docker exec` 로 attach 가능한 tracemalloc snapshot 스크립트:
  - 12시간 × 10분 간격 dump → `/var/log/compactor-tracemalloc/`
  - top 25 allocator + diff (가장 큰 growth)
- baseline 1회 (A1 적용 전) + 비교 1회 (A1 적용 24h 후)

**범위 (2차 영구)**:
- Compactor 코드에 Prometheus `/metrics` endpoint 추가:
  - `pyarrow_total_allocated_bytes` (Gauge)
  - `python_gc_gen{0,1,2}_count` (Counter)
  - `compactor_tier_accumulator_bytes{tier="L1|L2|L3", channel="ticks|orderbook|orderbook_snapshot"}` (Gauge)
  - `compactor_tier_pending_segments{tier="..."}` (Gauge)
  - `compactor_writer_open_count{tier="..."}` (Gauge)
- `monitoring/prometheus.yml` — 기존 `mctrader-data-compactor` scrape job 활용 (코드 변경만)
- Grafana dashboard: "Compactor Memory & Throughput" 패널 5 개 (RSS / pyarrow_total / gc gens / accumulator / pending)

**진입 조건**: 즉시 진입 (Phase 0). 1차 (tracemalloc 스크립트 + 1개 metric Counter) 가 A1 보다 먼저.

**의존**: MCT-123 (Prometheus/Grafana infra) — 완료 상태.

---

### Epic-B: Compactor v2 재설계 (2-3 wk)

**목적**: 근본 메모리 모델 변경 — A1 의 buy time 동안 진정 fix.

#### B1 Story (MCT-136) — Compactor staging 재현 환경

**범위**:
- 합성 WAL cold-start 환경 (1차):
  - 50 sym × 24h 분량 NDJSON WAL segment 합성 generator
  - `tools/compactor-staging/synth-wal.py` (현재 prod WAL 의 schema 따라)
  - compactor cold-start → A2 metric 으로 peak RSS / per-tier 측정
- 24h real full cycle 환경 (2차):
  - 별도 compose stack (`compose.staging-compactor.yml`)
  - prod WAL 의 read-only mount 또는 dual-write fork
  - 진정한 시간 흐름으로 24h 관측

**진입 조건**: A1 land + 24h baseline 확보 후 (A1 의 효과를 prod 에서 1주 검증 우선).

#### B2 Story (MCT-137) — Streaming compaction

**범위**:
- PyArrow `iter_batches` / `ParquetWriter.write_batch` loop 으로 Table materialize 회피
- 적용 위치:
  - L1: sealed segment → L1 Parquet (현재 batch 작아 영향 작음, but 일관성 위해 적용)
  - L2: L1 → L2 (1h 누적 → 단일 Table) — **핵심 변경 지점 1**
  - L3: L2 → L3 (24h 누적 → 단일 Table) — **핵심 변경 지점 2**
- 메모리 budget — `MCTRADER_COMPACTOR_PER_BATCH_ROWS=50000` (조정 가능)
- lineage manifest 의 `compacted_from` + sha256 invariant 보존 (B4 contract test)

**진입 조건**: B1 staging GREEN 후.

**검증 지표** (B1 staging 에서):
- Peak RSS < 32 GiB (50 sym, 24h cycle 1회)
- L3 cycle 동안 RSS 변동 폭 < 16 GiB

#### B3 Story (MCT-138) — Per-tier worker subprocess 분리 (조건부)

**진입 조건**: B2 staging 검증에서 peak RSS ≥ 32 GiB 또는 지속 GC pressure (gen2 frequency > baseline 5x).

**범위 (조건 충족 시만)**:
- Tier 별 subprocess 분리: L1 worker, L2 worker, L3 worker
- IPC: named volume sealed segment + state file (ADR-017 §D4 sidecar API 거부 일관)
- Per-tier mem_limit cgroup (compose 또는 systemd resource control)
- L3 worker 만 분리 + L1/L2 통합 옵션 검토 (단순화)

**status**: GitHub issue 미리 생성하되 body 에 "B2 검증 결과 미달 시 진입" 명시. label `conditional`.

#### B4 Story (MCT-139) — ADR-017 amendment + 회귀 테스트

**범위**:
- ADR-017 amendment:
  - §3.2 Compactor 책임 — streaming write contract 추가
  - §3.5 (신규) Memory budget + backpressure
  - §3.6 (B3 진입 시) Per-tier worker subprocess 구조
- `docs/domain-knowledge/contracts/compactor-memory-model.v1.md` (신규)
- 회귀 테스트:
  - 50 sym × 24h (현재 universe) — peak RSS < 32 GiB
  - 100 sym × 24h (forward extrapolation) — peak RSS < 48 GiB
  - DuckDB httpfs reader latency 측정 (B2 row group 크기 변경 영향) — MCT-122 contract 보호

**진입 조건**: B2 또는 B3 land 후.

---

## §3 진입 순서 (Gantt-like)

```
Phase 0 (즉시, 순차 강제):
  └─ MCT-134 A2 part-1 (tracemalloc 스크립트 + 1 metric Counter)
     └─ baseline 1회 캡처

Phase 1 (Phase 0 완료, 병렬):
  ├─ MCT-133 A1 (mem_limit + 런타임 tune + close audit)
  └─ MCT-134 A2 part-2 (full Prometheus export + Grafana dashboard)
     → rule-1 path-disjoint (compose.yml vs src/compactor/metrics.py)

Phase 2 (A1 land + 24h prod baseline 후):
  └─ MCT-136 B1 (staging 재현 환경)

Phase 3 (B1 staging GREEN):
  └─ MCT-137 B2 (streaming compaction)

Phase 4 (B2 staging 검증, 분기):
  ├─ [조건 A] B2 peak RSS < 32G 안정 → B3 skip
  └─ [조건 B] B2 미달 → MCT-138 B3 (per-tier 분리)

Phase 5 (B2 또는 B3 land):
  └─ MCT-139 B4 (ADR amendment + 50/100 sym 회귀)
```

---

## §4 scope_manifest 초안

```yaml
epic_a_scope_manifest:
  epic_key: MCT-132
  planned_adrs: 0
  planned_files:
    - c:\workspace\mclayer\mctrader-hub\compose.yml
    - c:\workspace\mclayer\mctrader-hub\monitoring\prometheus.yml
    - c:\workspace\mclayer\mctrader-hub\monitoring\grafana\dashboards\compactor.json  # 신규
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\__init__.py
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\worker.py
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\metrics.py  # 신규
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\writer.py    # close audit
    - c:\workspace\mclayer\mctrader-hub\tools\compactor-tracemalloc.py             # 신규
  planned_claude_md_sections:
    - "Compactor 운영 (mem_limit, 런타임 tune)"
    - "Compactor 관측 (Prometheus metric, tracemalloc)"

epic_b_scope_manifest:
  epic_key: MCT-135
  planned_adrs: 1  # ADR-017 amendment
  planned_files:
    - c:\workspace\mclayer\mctrader-hub\docs\adr\ADR-017-zero-loss-ingestion-wal-tiered-compaction.md  # amendment
    - c:\workspace\mclayer\mctrader-hub\docs\domain-knowledge\contracts\compactor-memory-model.v1.md  # 신규
    - c:\workspace\mclayer\mctrader-hub\compose.staging-compactor.yml  # 신규
    - c:\workspace\mclayer\mctrader-hub\tools\compactor-staging\synth-wal.py  # 신규
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\worker.py  # streaming
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\writer.py  # iter_batches
    - c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\subprocess_runner.py  # B3 조건부
    - c:\workspace\mclayer\mctrader-data\tests\compactor\test_streaming_compaction.py
    - c:\workspace\mclayer\mctrader-data\tests\compactor\test_50sym_24h_regression.py
    - c:\workspace\mclayer\mctrader-data\tests\compactor\test_100sym_24h_regression.py
  planned_claude_md_sections:
    - "Compactor v2 streaming compaction"
    - "Compactor memory budget + backpressure"
    - "Compactor staging 재현 환경"
```

---

## §5 의존 / blocker

| 기존 Story | 상태 | 관계 |
|---|---|---|
| MCT-103 (50 sym universe) | in_progress | trigger source. blocker X, 병행 가능 |
| MCT-106 (ADR-017 원본) | done | 설계 SSOT. B4 amendment target |
| MCT-122 (DuckDB analytics) | done | L3 Parquet consumer — B2 row group 영향 측정 (B4 scope 포함) |
| MCT-123 (Prometheus/Grafana) | done | A2 의 인프라 prereq |

**Hard blocker**: 없음.
**Soft constraint**:
- L3 Parquet schema/footer 불변 (MCT-103 forward-only invariant 보호)
- DuckDB httpfs reader latency 영향 측정 (B4 회귀에 포함)

---

## §6 위험 (3 lane)

### Security
- 합성 WAL generator (B1) 가 prod WAL 의 schema 를 정확히 따라야 — synth payload 가 prod 에 leak 되지 않도록 staging compose 의 named volume 격리 필수.

### Operational
- A1 의 `mem_limit=32G` 가 정상 working set 미만이면 재시작 루프 → A2 의 RSS metric 으로 즉시 감지, mem_limit 점진 상향 fallback.
- B3 per-tier 분리 도입 시 IPC race (sealed segment 처리 중복) — lineage manifest 의 `compacted_from` 으로 idempotency 보장 필요.

### Data integrity
- B2 streaming compaction 의 lineage manifest sha256 invariant — Table materialize 단일 hash vs batch loop 의 hash 동등성 contract test 필수.
- L3 row group 크기 변경 시 DuckDB / Pandas read pattern 영향 — B4 회귀에서 query latency 측정.

---

## §7 전제·미해결 (Phase 0/1 진행 중 확정)

- `mctrader_data.compactor` 모듈의 정확한 파일 구조 — Phase 0 A2 진입 시 확인 (현재 spec 의 파일 경로는 추정).
- 24h cycle 의 peak 발생 시점 — UTC 자정 직후 즉시인지, L3 처리 중 누적인지 — A2 metric 으로 확정.
- 50 sym → 100 sym scale 의 메모리 곡선 (선형 vs 초선형) — B4 회귀에서 측정 후 ADR amendment 수치 확정.
