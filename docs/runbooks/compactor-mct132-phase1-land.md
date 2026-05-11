# MCT-132 Phase 1 Land Report (2026-05-11)

## 변경 내역 (Phase 0 + Phase 1)

### Phase 0
- Task 1 (`581be60`, `4198169`): `tools/compactor-tracemalloc.py` collector + cleanup
- Task 2 (`a2d61d5`): compactor `/metrics` HTTP server bootstrap + RSS gauge (Linux procfs + macOS resource + Windows ctypes/psapi fallback)
- Task 3 (`5a185b5` data, `9f661ab` + `dee59a5` hub): compose `ports: ["8080:8080"]` + baseline runbook + docstring shadowing fix

### Phase 1 — 분기 α (MCT-133 A1)
- Task 4 (`2673335`): compose `mem_limit: 32g` + `memswap_limit: 32g` + 4 env vars (`MCTRADER_COMPACTOR_METRICS_PORT`, `MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS`, `MALLOC_TRIM_THRESHOLD_=131072`, `ARROW_DEFAULT_MEMORY_POOL=system`)
- Task 5 (`074ca6d`): L1Compactor — `with pq.ParquetWriter(...)` context manager + tmp cleanup on exception (handle leak fix)
- Task 6 (`261505a`, `82791f6`, `03bbc82`): L2/L3 동일 패턴 + runner `_tick` interval-driven `gc.collect()`

### Phase 1 — 분기 β (MCT-134 A2 part-2)
- Task 7 (`c8f1e4f`, `5adca62`): 5 metric full export (pyarrow_total / gc_gens / tier_pending / writer_open / process_rss) + tier_pending epoch init bug fix + tier label prime
- Task 8 (`60d95ff`): Grafana dashboard "Compactor Memory & Throughput" (5 panels) + dashboard.yml path bug fix (pre-existing, MCT-123 verification gap)

## 즉시 관측된 운영 시그널

### 진정한 leak 신호 (mem_limit 적용 전, 단일 측정)
- 초기 측정 (2026-05-11): RSS **48.5 GiB / 62.73 GiB (77%)**, CPU 122%
- 컨테이너 fresh restart 직후: 약 382 MiB → 10분 만에 **1.69 GB** (4.4x growth in 10min)
- 결론: 단순 plateau 가 아닌 **active growth pattern** — accumulator bloat 또는 ParquetWriter handle leak (Task 5/6 가 후자 fix)

### mem_limit 32G 적용 후 (Task 4 직후)
- 컨테이너 recreate fresh start: 433 MiB / 32 GiB limit
- LIMIT 컬럼이 32GiB 로 cap — 호스트 OOM 방지 달성

### Task 7 full metric land 후 (`5adca62`)
- 컨테이너 fresh start: 200 MiB
- 5 metric 모두 host scrape 노출:
  - `compactor_process_rss_bytes`: 정상 측정
  - `compactor_pyarrow_total_allocated_bytes`: 3.78 MB (fresh)
  - `compactor_python_gc_gen_count{generation="0|1|2"}`: 369/9/18 (정상 범위)
  - `compactor_tier_pending_segments{tier="L1|L2|L3"}`: **L1=22,497** (실제 sealed backlog, 별도 운영 이슈), L2/L3 = 0 (정상 — 첫 cycle 이전)
  - `compactor_writer_open_count{tier=L1|L2|L3}`: 0/0/0 (정상 — 측정 시점 inter-write)

### L1 pending 22,497 의 의미
- L1 compaction 이 sealed segment 처리를 못 따라감 — 백로그 누적
- 본 Story 의 leak fix 와는 다른 운영 이슈 (L1 throughput vs ingester rate)
- 후속 검토 필요 — MCT-135 (Epic-B v2 재설계) scope 후보

## 24h 효과 검증 — Deferred

baseline tracemalloc capture 는 Phase 1 의 매 recreate (Task 4/6/7) 마다 손실됨. 진정한 before/after 비교는 다음 절차로 별도 진행:

### 절차 (Phase 1 land + 24h 후)

1. RSS metric 24h 시계열 query:
   ```promql
   max_over_time(compactor_process_rss_bytes[24h])
   avg_over_time(compactor_process_rss_bytes[24h])
   ```

2. mem_limit 32G 적용 전 (2026-05-11 측정값 = 48.5 GiB) vs 24h 후 비교

3. tracemalloc capture (Phase 1 land 이후 fresh):
   ```
   docker cp tools/compactor-tracemalloc.py mctrader-compactor:/tmp/compactor_capture.py
   docker exec -d mctrader-compactor sh -c 'nohup python /tmp/compactor_capture.py \
       --duration-hours 12 --interval-min 10 \
       --out /var/lib/mctrader/data/_tracemalloc/after-phase1 \
       > /var/lib/mctrader/data/_tracemalloc/after-phase1.log 2>&1 &'
   ```

4. 12h 후 dump 회수 + top 25 allocator 분석.

5. 보고서 작성: `docs/runbooks/compactor-a1-effect-YYYY-MM-DD.md`

### 판정 기준

- [ ] **A1 으로 stabilize 충분**: 24h peak RSS < 32 GiB 안정 → Epic-B (MCT-135 v2 재설계) 진입 우선순위 낮춤
- [ ] **A1 만으로 부족**: peak ≥ 32 GiB 또는 mem_limit OOM kill 발생 → MCT-135 B1 → B2 진입 의무
- [ ] **L1 backlog 처리**: 별도 검토 (본 Story 와 독립)

## Pre-existing bug 발견 (별도 follow-up 후보)

1. **MCT-123 dashboard.yml path bug** (Task 8 fix): `path: /var/lib/grafana/dashboards` 가 bind mount 없는 경로 → 모든 기존 Grafana dashboard 가 load 안 됨. Task 8 에서 동반 fix 함.
2. **L1 pending 22,497**: compaction throughput < ingestion rate. Story 와 독립.

## Phase 1 land 종료 조건
- ✅ Task 1-8 all DONE
- ✅ All tests PASS (5 신규 + 기존 회귀 없음)
- ✅ Docker smoke: 32G mem_limit + 5 metric 노출 + Grafana dashboard 등록
- ⏳ Task 9 (본 task): land report + CLAUDE.md
- ⏳ 24h effect 검증: 별도 deferred
