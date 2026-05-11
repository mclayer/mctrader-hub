# RETRO — MCT-132 Compactor stabilize Epic-A (2026-05-11)

**범위**: MCT-132 (Epic, parent) + MCT-133 (A1 런타임 안정화) + MCT-134 (A2 관측 인프라)
**기간**: 2026-05-11 (단일 세션, Phase 0 + Phase 1 연속 진행)
**Trigger**: `mctrader-compactor` 컨테이너 RAM 48.5 GiB / 62.73 GiB (77.32%) + CPU 122% 폭주 — 호스트 OOM 직전 단계. MCT-103 50 sym 확장 (forward-only history 누적 + L3 daily compaction accumulator) 이후 발현 가설.
**Spec**: `docs/superpowers/specs/2026-05-11-compactor-memory-fix-design.md`
**Plan**: `docs/superpowers/plans/2026-05-11-mct132-compactor-stabilize.md`
**Status**:
- 3 Story 완료 (MCT-132 Epic / MCT-133 A1 / MCT-134 A2)
- 9-task TDD 100% PASS — 신규 8 test 모두 FAIL → PASS 박제, 21/21 compactor pytest 회귀 없음
- mctrader-data PR #31 MERGED (`fcb25cd` @ 2026-05-11T13:53:36Z, 9 commits)
- mctrader-hub PR #217 MERGED (`73a1d30` @ 2026-05-11T13:53:07Z, 7 commits)
- Admin merge 양 PR 모두 적용 (mctrader-data CI pre-existing PAT broken)

**Story files**: `docs/stories/MCT-132.md`, `MCT-133.md`, `MCT-134.md` (§11 본 RETRO pointer 박제)
**Repos**: `mctrader-data` (compactor core) + `mctrader-hub` (compose / monitoring / runbook / Grafana dashboard / Story)
**선행**: MCT-103 (50 sym 확장, 2026-05-09) — trigger 추정
**후행**: MCT-135 (planned Epic-B v2 — streaming compaction + per-tier subprocess + ADR-017 amendment)

---

## 1. Overview

2-Epic 구조 중 Epic-A (Phase 0 + Phase 1 동시 land). 9 task TDD. 2 repos × admin merge.

**Epic 분할 결정**:
- **Epic-A**: 즉시 OOM mitigation (cgroup cap) + observability infra (metric + dashboard) + handle leak 가설 직접 fix (close audit)
- **Epic-B (planned, MCT-135)**: v2 재설계 — streaming compaction + per-tier subprocess + ADR-017 amendment

분할 정당화: 호스트 OOM 임박 + baseline (50 sym 확장 전) 부재라는 dual constraint — A 가 즉시성 + 진단 인프라, B 가 deep redesign.

**작업 세션 압축률**: 단일 세션에 9 task TDD + 2 PR admin merge + 3 Story §1-§10 박제 — 토큰 예산 효율 (per-task token vs 결과 commit 비율) 적정.

---

## 2. Goal triad delivery

Epic-A 의 3축 목표 — 모두 acceptance criteria 충족:

| 축 | Goal | Acceptance evidence | Status |
|----|------|---------------------|--------|
| (a) | Immediate OOM mitigation | `docker stats mctrader-compactor` LIMIT=32GiB 표시 + fresh start 433 MiB / 32 GiB cap | DONE |
| (b) | Observability infra | `curl :8080/metrics` 5 metric 응답 + Grafana dashboard uid=`mctrader-compactor` 5 panel + Prometheus scrape `mctrader-data-compactor` 정상 | DONE |
| (c) | Real leak candidate fix | L1/L2/L3 `with pq.ParquetWriter(...) as writer:` + tmp cleanup + runner interval-driven `gc.collect()` | DONE (24h 효과 검증 deferred) |

**즉시 운영 시그널 (Phase 1 land 직후)**:
- Pre-Phase-1: RSS 48.5 GiB, fresh restart 후 4.4x growth in 10min (**강한 leak signal**)
- Task 4 직후: 433 MiB / 32 GiB limit cap 확인
- Task 7 직후: `compactor_tier_pending_segments{tier="L1"}=22,497` 노출 — **별도 운영 이슈** (compaction throughput < ingestion rate, Epic-B B1 후보)

---

## 3. Story scope vs 실제 변경 매트릭스

| Story | Scope | AC | 결과 | repo / 핵심 commit |
|---|---|---|---|---|
| MCT-132 (Epic, parent) | 2-repo 통합 박제 (compose + monitoring + runbook + Story) | 6 AC | done | hub + data (parent) |
| MCT-133 (A1 런타임) | mem_limit + glibc/arrow tune + ParquetWriter close audit + gc interval | 5 AC | done | data: `2673335` + `074ca6d` + `261505a` + `82791f6` + `03bbc82` |
| MCT-134 (A2 관측) | tracemalloc collector + metrics_server + 5 metric full export + Grafana dashboard + Phase 1 land report | 6 AC | done | data: `581be60` + `a2d61d5` + `5a185b5` + `c8f1e4f` + `5adca62`<br>hub: `9f661ab` + `dee59a5` + `60d95ff` + `4198169` + `d09d2e2` |

→ **3-Story scope 17/17 AC 100% 완료**. Epic 의 goal triad 가 Story 분기와 1:1 매핑 (A1 = (a)+(c), A2 = (b)).

### 3.1 commit 통계

| 단위 | repo | 통계 | 상태 |
|---|---|---|---|
| PR #31 | mctrader-data | 9 commits (compactor 본체 + tests) | MERGED `fcb25cd` admin merge |
| PR #217 | mctrader-hub | 7 commits (compose / monitoring / runbook / Grafana dashboard / CLAUDE.md / Story) | MERGED `73a1d30` admin merge |

### 3.2 테스트 결과

| Story | 테스트 | 로컬 | CI |
|---|---|---|---|
| MCT-133 (A1) | `test_l1_writer_close` + `test_l2_writer_close` + `test_l3_writer_close` + `test_runner_gc_interval` (4 신규) | PASS | RED — pre-existing #30 PAT broken |
| MCT-134 (A2) | `test_metrics_server` + `test_metrics_full` + `test_runner_pending_init` (3 신규, 4 case) | PASS | RED — 동일 #30 |
| Regression | 21/21 compactor pytest (mctrader-data) | PASS | — |

→ **로컬 검증 21/21 PASS**. mctrader-data CI 실패는 본 Epic 무관 — `CODEFORGE_CROSS_REPO_PAT` secret degraded 로 `mctrader-market-upbit` private dep clone 실패. **main 의 마지막 commit `264a1a2` 도 동일 fail** — 본 PR 작업 이전부터 broken. Admin merge 우회 (사용자 권한, memory `Admin merge autonomy`).

---

## 4. Cross-Story 패턴

### 4.1 Phase 0 → Phase 1 → 24h 검증 패턴

메모리 leak RCA 의 일반 3-step:
- **Phase 0 (baseline)**: tracemalloc collector + minimal metric (RSS gauge 1개) 로 leak signal 정량화 — `tools/compactor-tracemalloc.py` + `metrics_server.py` 1-metric bootstrap
- **Phase 1 (fix)**: cgroup cap + handle leak 가설 직접 fix + 5 metric full export — Task 4/5/6/7/8
- **Phase 2 (검증, deferred)**: `max_over_time(compactor_process_rss_bytes[24h])` query + fresh tracemalloc 12h capture — runbook 박제 (`compactor-mct132-phase1-land.md` §24h effect verification)

### 4.2 TDD 가 운영 bug 즉석 catch

`test_runner_pending_init.py` 가 tier_pending epoch=0 nonsense (`(now - 0.0) / interval` ≈ 5.9M / 494K 거짓 값) 을 metric 노출 전에 catch. 운영자 panic 회피 + dashboard threshold-based alerting 무효화 회피의 dual value.

→ TDD = 단순 회귀 방지 도구가 아니라 **발견 도구**. RETRO-MCT-117 / RETRO-MCT-129-130-131 의 패턴 재확인.

### 4.3 Pre-existing infra silent failure 적시 발견

Phase 1 작업 중 동반 발견·fix 한 2건:

| Bug | 발견 시점 | Root cause | Fix |
|-----|----------|-----------|-----|
| `dashboard.yml` path bug | Task 8 (Grafana dashboard 등록 안 됨) | MCT-123 의 `/var/lib/grafana/dashboards` 가 bind mount 없는 broken — 모든 Grafana dashboard 가 silent 하게 load 안 되고 있던 상태 | `60d95ff` — `/etc/grafana/provisioning/dashboards` 로 수정 |
| `tracemalloc.py` filename shadowing | Task 3 (host script 실행 시 AttributeError) | Python sys.path[0] = script dir → `import tracemalloc` 가 자기 자신 재귀 import | `dee59a5` — `compactor_capture.py` 로 rename (docstring + runbook 갱신) |

→ **observability 도입 task 가 pre-existing gap 의 발견 도구 역할** — MCT-129/130/131 의 CI infra PAT broken 발견과 동일 패턴.

### 4.4 2-Epic 분할 디자인 패턴

호스트 OOM 임박 + baseline 부재 의 dual constraint 가 본 Epic 의 분할 정당화:
- A = (immediate mitigation) + (observability infra) + (root cause direct fix)
- B = (deep redesign 후 v2 streaming)

A 의 metric 인프라가 B 의 staging 재현 + 판정 기준 (peak RSS thresholds) 을 즉시 지원 — A 가 B 의 prerequisite. ADR-017 amendment 가 B 시점에 발의.

### 4.5 Mechanical task vs Discovery task FIX 분포

- **Mechanical (A1 — env + close pattern apply)**: FIX 0
- **Discovery (A2 — observability 도입)**: FIX 1 (tier_pending epoch=0)

→ observability/discovery task 가 noise 흡수 → FIX 발생률 ↑. mechanical task = FIX 0 패턴 재확인 (RETRO-MCT-129/130/131 와 일관).

---

## 5. Learned

### 5.1 Patterns
- **`with pq.ParquetWriter(...) as writer:` + tmp cleanup**: PyArrow 가 `__enter__/__exit__` 지원 — try/finally 보다 간결 + exception 보장. atomic rename 전 실패 시 `tmp_path.unlink()` 가 표준 cleanup.
- **fresh start metric 초기화**: epoch=0 nonsense 회피 — `if self._last_X > 0` guard + prime labels with 0. `test_runner_pending_init.py` 가 reference regression guard.
- **stdlib module 동명 internal module alias**: `from . import gc as _filesystem_gc` — Python absolute import 우선순위에 의존하지 않는 명시적 alias.
- **interval-driven hook test**: `monkeypatch.setenv` 로 interval 을 ms 단위 축소 + 2-tick test — fuzz/sleep 없이 결정적 검증.
- **3-platform RSS 측정**: Linux procfs + macOS resource + Windows ctypes/psapi fallback chain — Windows 개발 + Linux 운영 모두 지원.
- **Goal triad 패턴**: (a) mitigation + (b) observability + (c) root cause direct fix 의 3축이 단일 Epic 안에서 병행 가능.

### 5.2 Runtime tune
- `MALLOC_TRIM_THRESHOLD_=131072` — glibc malloc free 후 OS 반환 trigger 임계 (기본보다 공격적)
- `ARROW_DEFAULT_MEMORY_POOL=system` — jemalloc → glibc 전환으로 RSS 추적성 ↑
- `MCTRADER_COMPACTOR_GC_INTERVAL_SECONDS=300` — L3 cycle (1h+) 보다 짧고 CPU overhead 무시 가능

### 5.3 운영 시그널 박제
- L1 pending backlog **22,497 segments** — compaction throughput < ingestion rate 강한 signal. Epic-B B1 staging 진단 input.
- Fresh restart 후 4.4x growth in 10min — handle leak 가설 추가 근거.

---

## 6. 잘된 점 / 개선점 (composite)

### 잘된 점
- **2-Epic 분할 정합**: A 의 metric 인프라가 B 의 prerequisite — Epic 책임 분리 명확.
- **Goal triad 3/3 달성**: cgroup cap + 5 metric + close audit 모두 acceptance 충족.
- **9-task TDD 진정성**: 신규 8 test FAIL → PASS 박제, 21/21 회귀 없음.
- **Pre-existing bug 동반 fix 2건**: dashboard.yml path + tracemalloc shadowing — 별도 Story 미발의로도 즉시 해소.
- **TDD 가 tier_pending epoch=0 bug 즉석 catch**: 운영자 panic + threshold alert 무효화 양쪽 회피.
- **Admin merge autonomy 적시 사용**: pre-existing PAT broken 우회로 Epic 진행 차단 회피.

### 개선점
- **24h baseline tracemalloc 손실**: Phase 1 docker recreate 마다 reset — before/after 정량 비교 deferred.
- **L1 backlog 22,497 별도 issue 미발의**: Epic-B B1 staging 진단 통합 필요.
- **PAT 인프라 broken silent**: 본 작업 진입 시점에 발견 — 별도 follow-up Story.
- **dashboard.yml path 자기검증 게이트 부재**: MCT-123 의 모든 dashboard silent broken — e2e check 추가 필요.
- **mem_limit 32G 의 soft signal 부재**: 28G threshold alert 등록 별도 Story.
- **tier_pending L2/L3 stale interval 임시 해결**: Epic-B B1 에서 actual sealed count 로 unify.

---

## 7. Follow-up

| 우선순위 | 항목 | trigger / 근거 |
|---------|------|---------------|
| HIGH | **24h 효과 검증 Story** | `max_over_time(compactor_process_rss_bytes[24h])` + fresh tracemalloc 12h capture → peak RSS 기준 Epic-B priority 결정 (`docs/runbooks/compactor-mct132-phase1-land.md` §24h effect verification) |
| HIGH | **PAT 인프라 fix Story** | `CODEFORGE_CROSS_REPO_PAT` secret 갱신 또는 mctrader-data workflow `--all-extras` 의존 분리 — mctrader-data CI green 복구. RETRO-MCT-129-130-131 #30 동일 trigger |
| HIGH | **MCT-123 dashboard load 자기검증 Story** | Grafana API `/api/search?type=dash-db` 응답 카운트 vs `monitoring/grafana/provisioning/dashboards/*.json` 카운트 일치 검증 — e2e dashboard load gate |
| MED | **L1 backlog 22,497 → Epic-B B1 통합** | compaction throughput < ingestion rate signal 을 Epic-B B1 staging 진단 input 으로 통합 |
| MED | **Grafana alert 등록 Story** | `process_rss_bytes ≥ 28GiB` + `tier_pending_segments{tier="L1"} ≥ 10000` + `writer_open_count` non-zero divergence — 5 panel 위에 alert 레이어 |
| MED | **MCT-135 Epic-B 발의** | streaming compaction + per-tier subprocess + ADR-017 amendment (planned) |
| LOW | **tier_pending L2/L3 semantics unify (Epic-B B1)** | stale interval count → actual sealed segment count 로 L1 과 일치 |
| LOW | **docker-compose v3 migration 점검** | `memswap_limit` deprecated 대응 → `deploy.resources.limits.memory` |
| LOW | **GC retention 분포 측정** | tracemalloc 12h capture 후 gen2 collect interval distribution 분석 — 300s interval 의 정량 근거 보완 |
| LOW | **tracemalloc collector sidecar 패턴 검토** | docker recreate 무관하게 baseline 유지 — Epic-B staging 재현 인프라 통합 가능성 |
| LOW | **fresh start metric 초기화 standard practice 박제** | `if self._last_X > 0` guard + prime labels 패턴을 CLAUDE.md `Compactor 관측` 섹션에 일반 가이드로 |

---

## 8. ADR 후보

본 Epic 에서 직접 발의된 ADR 없음 (Epic-B 시점에 ADR-017 amendment 예정). 단 다음 패턴들은 ADR 후보로 고려 가능:

- **2-Epic 분할 패턴 의 trigger condition**: 단일 RCA Story 가 (immediate mitigation + observability) 와 (deep redesign) 으로 분할 가능한 시점의 정량 기준 (호스트 OOM 임박, baseline 부재, …).
- **Pre-existing observability gap 발견 시 동반 fix vs 별도 Story 분리 정책**: dashboard.yml path / tracemalloc shadowing 처럼 작업 중 silent broken 발견 시 Story scope 안에 fix 흡수 vs 별도 Story 발의의 결정 기준.

→ Cross-Story 패턴 분석 (PMOAgent 다중 Story 감사) 시점에 재검토.

---

## 9. Self-review

- **회고의 학습 자산 명확성**: 7 pattern (close + cleanup / metric 초기화 / module alias / interval test / 3-platform RSS / goal triad / 운영 시그널) 모두 reusable reference 가 박제됨.
- **Follow-up 명확성**: 11 follow-up 모두 trigger + 근거 + 우선순위 박제. HIGH 3건 (24h 검증 / PAT fix / dashboard 자기검증) 이 즉시 후속 가능.
- **Cross-Story 패턴 진정성**: 4-pattern (Phase 0→1→2 / TDD discovery / pre-existing surface / 2-Epic 분할) 이 다른 Story 와의 reference link 박제 — RETRO-MCT-117 / 129-130-131 인용.
- **Source-of-truth fidelity**: PR #31 + #217 SHA, commit hash, AC 17/17, 21 test PASS, 시그널 정량 (48.5 GiB / 4.4x / 22,497) 모두 source-of-truth 와 일치.
