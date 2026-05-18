---
story_key: MCT-202
story_scope: cross-repo
title: Eager post-compaction cleanup cascade — 3-tier grace-0 caller wiring
authored_by: ArchitectAgent (chief author)
supervised_by: ArchitectPLAgent
deputies_synthesized:
  - CodebaseMapperAgent     # §2 현재 구조 fact
  - RefactorAgent           # §3 도입할 설계 + §6 리팩토링 선행
  - SecurityArchitectAgent  # §7.1-§7.3 / §7.5-§7.6
  - OperationalRiskArchitectAgent  # §7.4 운영 리스크 + §11.6 idempotency consult
  - TestContractArchitectAgent     # §8 Test Contract
  - DataMigrationArchitectAgent    # §11.1-§11.5 / §11.6 idempotency author
parent_story: MCT-189  # WAL→L1 grace-0 wiring 완결 → 본 Story 가 L1→L2 + L2→L3 cascade 완결
epic_key: EPIC-tier-promotion-single-source
mode: B (cross-repo)
phase: 설계
related_adrs:
  - ADR-027 §D5 (eager unlink ↔ sweep race 분기 + 4xx fail-fast 정합)
  - ADR-027 §D7 (WAL grace 폐기 + NAS-SoT 격상)
  - ADR-029 §D3 (3-tier dimension 일반화)
  - ADR-029 §D11 (3-tier eager unlink invariant 신설)
  - ADR-017 §D2 (compactor cascade self-delete = caller-wiring SSOT)
  - ADR-017 §D5 (DualWriter status='committed' XOR source exists invariant)
  - ADR-009 §D12.2 (forward-only invariant 3-tier 확장)
verified_via_ref: "0e244e9 (mctrader-data origin/main HEAD, 2026-05-18)"
---

# Change Plan — MCT-202 Eager post-compaction cleanup cascade

> 본 Change Plan 은 MCT-202 의 chief author (ArchitectAgent) 가 ArchitectPLAgent 의 D-1~D-6 종합 권고 + 6 deputy 산출물을 통합 author 한다. Story SSOT `c:/workspace/mclayer/mctrader-hub/docs/stories/MCT-202.md` §1-§6 immutable. 본 Plan = §7 본 설계 + §8 Test Contract + §11 데이터 마이그레이션 + §13 Phase 1 self-check 의 expanded SSOT.

## §1 개요 (사용자 원문 + WHY + 결정 박제)

### 사용자 원문 verbatim
[user-input, Story §1] "항상 컨테이너 내에서 데이터를 보관하느라 disk full이 발생한다. mctrader-data는 L1,L2,L3로 tier마다 compactor를 거치는데 L1에서 L2로, L2에서 L3로 compact 되었으면 compact 된 이전의 데이터는 필요하지 않다. 이 compact 완료하고 삭제하는 작업이 compactor에서 잘 적용되어 수행되고 있는가? compaction 직후에 삭제해야 겠다."

### WHY (가치 함수)
- 컨테이너 disk-full 빈발 차단 + 재발 방지 + 운영 부담 0
- WAL→L1 단계 (MCT-189 LAND, PR #73 + #75) 만 작동 → L1→L2, L2→L3 미작동 → local 영구 누적 → disk full
- 본 Story = caller wiring gap 해소 + 3-tier 동형 eager unlink 박제

### chief author 의 D-1~D-6 최종 결정 박제

| Decision | 채택안 | rationale 요약 |
|---|---|---|
| **D-1** | **옵션 B (caller-side, `source_to_delete: Path \| None = None`)** | callee semantic 보존 (MCT-189 D-2 A 분기 유지), MCT-160 D6 streaming guard 깨짐 0, caller 의도 명시 박제 |
| **D-2** | **옵션 C (output-local 자연 종결)** | cascade target = L2/L3 compactor output (방금 생성된 local parquet) = 항상 local 존재. NAS GET 모드라도 output 은 local. input source NAS object 회수 = 별 Story carry-over (MCT-204 후보) |
| **D-3** | **포함 + `_historical_dual_write` 4xx wrap 동시 LAND** | 사용자 답변 #1 "3 단계 전부" 자연 해석 + SecurityArch T-5 (`NASOperationalAlert` propagation drift 차단) |
| **D-4** | **docstring amendment + runbook 별 인계 (PMO retro carry-over)** | OpRiskArch INV-I = `gc_daemon._archive_failed` 의 status 분기 자연 보존 (의미 변경 0). 운영 runbook 갱신은 별 Story |
| **D-5 (SecurityArch T-6 신규)** | **옵션 C (path snapshot 유지 + `mctrader_retry_orphan_total{tier}` Counter)** | INV-4 memory budget 보존, sweep cycle 자연 회수 (legacy safety net), gauge cardinality ≤ 50 |
| **D-6 (OpRiskArch INV-H 신규)** | **gc.py `run_gc()` legacy safety net 보존** | 즉시 폐기 시 transient race window 흡수 0, 14d production evidence gate 후 별 Story 폐기 검토 |
| **Counter outcome** | **5종 채택**: `committed_unlinked` / `committed_unlink_failed` / `local_only_retained` / `hard_floor_retained` / **`already_promoted`** | restart recovery + sweep cycle 빈번 (TestContract 의제 1 PL 권고 채택). 3-tier × 5 outcome = 15 series ≤ 50 (ADR-027 §D6 cardinality invariant 정합) |
| **§11.6 idempotency replay** | **활성화** | MCT-189 INV-6 propagation, replay 빈도 박제 의무 (DataMigration §11.6) |

## §2 영향 영역 (touched_top_level_paths)

### mctrader-data (Phase 2 PR, src + tests)

- `src/mctrader_data/compactor/runner.py` — `_dispatch_dual_write` + `_historical_dual_write` 양쪽 `source_to_delete=parquet_path` 명시 파라미터 전달
- `src/mctrader_data/compactor/l2.py` — 변경 0 (output path 만 caller 측 use)
- `src/mctrader_data/compactor/l3.py` — 변경 0 (동일)
- `src/mctrader_data/compactor/gc_daemon.py` — docstring amendment only (D-4, 의미 변경 0)
- `src/mctrader_data/compactor/gc.py` — 변경 0 (D-6 legacy safety net 보존)
- `src/mctrader_data/nas_storage/dual_writer.py` — `write()` 시그니처에 `source_to_delete: Path | None = None` keyword-only 파라미터 추가 + 신규 분기 + `_promote_after_nas_put` 5 outcome 반환
- `src/mctrader_data/nas_storage/nas_uploader.py` — `enqueue_retry` race-C 신호 Counter (`mctrader_retry_orphan_total`) emit (D-5)
- `src/mctrader_data/nas_metrics/prometheus_exporters.py` — `compactor_local_self_delete_total{tier,outcome}` (5 outcome) + `mctrader_retry_orphan_total{tier}` 신규 (12 + 3 = 15 series, ≤ 50)
- `tests/unit/nas_storage/test_dual_writer_eager_l2_l3.py` — D-1 옵션 B 신규 분기 (TestContract 의제 2)
- `tests/integration/test_eager_cleanup_cascade.py` — 3-tier × 5 outcome E2E + sweep race + §11.6 replay
- `tests/unit/compactor/test_runner_dispatch_dual_write.py` — `source_to_delete` 전달 박제 + `NASOperationalAlert` re-raise
- `tests/unit/compactor/test_runner_historical_dual_write.py` — historical path 동형 (D-3)
- `tests/unit/compactor/test_metrics_self_delete.py` — 5 outcome × 3 tier parametrize + cardinality assert

### mctrader-hub (Phase 1 PR, docs)

- `docs/stories/MCT-202.md` — §3 / §6 / §7 / §11 self-write (chief author 직접 갱신)
- `docs/change-plans/MCT-202-eager-cleanup-cascade.md` — **본 문서** (신규)
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` — §D5 + §D7 amendment box
- `docs/adr/ADR-029-tier-promotion-single-source.md` — §D3 + §D11 amendment box (§D11 신설)
- `docs/adr/ADR-017-zero-loss-ingestion-wal-tiered-compaction.md` — §D2 + §D5 amendment box
- `docs/adr/ADR-009-ohlcv-schema.md` — §D12.2 annotation amendment
- `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` — 3-tier 확장 amendment

## §3 변경 사항 (chief author 결정 결과)

### 3.1 D-1 채택: caller-side `source_to_delete` 명시 전달 (옵션 B)

**`DualWriter.write()` 시그니처 변경**:

```python
def write(
    self,
    *,
    local_path: Path,
    nas_key: str,
    data: bytes | Path,
    sha256: str,
    source_to_delete: Path | None = None,   # NEW (MCT-202)
) -> DualWriteResult:
```

semantics:
- `source_to_delete is None` → 기존 동작 보존 (MCT-189 LAND, `isinstance(data, Path) and data != local_path` guard 그대로). regression 차단 의무.
- `source_to_delete is not None` → caller 가 명시 cascade intent. `nas_put_result.status in _COMMITTED_STATUSES` 시 `_promote_after_nas_put(source_to_delete, nas_key, sha256)` 진입.

**왜 옵션 A 거부 (Refactor 산출물)**:
- 옵션 A = `data != local_path` guard 단순 제거 → `data == local_path == parquet_path` 동일 객체 시 `_promote_after_nas_put` 가 output self-unlink 시도 → `local_path` 자기 자신 unlink (catastrophic regression).
- 옵션 B = 명시 파라미터로 self vs source 구분 → callee 가 의도된 cascade 만 처리.

### 3.2 D-2 채택: output-local 자연 종결 (옵션 C)

cascade target = compactor **output** parquet (방금 `os.replace(tmp, out_path)` atomic rename 완료된 local file). NAS GET 모드 (compactor 가 NAS object 를 source 로 GET) 에서도 output 은 항상 local 생성 → false problem.

**input source 회수 (NAS object 측 회수)** 는 본 Story 범위 외:
- L1 → L2: input = L1 parquet (local sweep 가 회수, `scan_and_cleanup_legacy`) OR input = NAS L1 object (회수 정책 부재 = carry-over)
- L2 → L3: 동형

별 Story carry-over 권고: **MCT-204** (post-LAND 별 Story) — NAS object lifecycle (L1 NAS object 가 L2 cascade 완료 후 NAS bucket lifecycle policy or explicit DELETE 처리). 본 Story = local file lifecycle 만.

### 3.3 D-3 채택: `_historical_dual_write` 동형 cascade + 4xx wrap 동시 LAND

`runner.py:447-487 _historical_dual_write` 도 동형 `source_to_delete=parquet_path` 전달 +
**`NASOperationalAlert` re-raise wrap** (`_dispatch_dual_write` 의 try/except 패턴 mirror).

이유 (SecurityArch T-5):
- 현재 `_historical_dual_write` 는 `dual_writer.write()` 호출을 try/except 로 wrap 0 → `NASOperationalAlert` (4xx fail-fast) propagate 가 raw exception 으로 historical caller 까지 전파. `_dispatch_dual_write` 와 drift.
- 본 Story 가 cascade wiring 동시 LAND 시점에 wrap 일관화 의무.

### 3.4 D-4 채택: `gc_daemon._archive_failed` docstring amendment only

`gc_daemon.py` 의 `_archive_failed` (status='local_only' / 'hard_floor_blocked' 7d extension 처리) 는 의미 변경 0. 본 Story 가 source 보존 → eager cascade gate 통과 0 → 기존 `_archive_failed` 분기 자연 propagation.

docstring 추가:
```python
"""...기존...
MCT-202 amendment (2026-05-18): cascade gate 가 status='committed' XOR source unlink
(INV-D). 본 함수의 'local_only' / 'hard_floor_blocked' 분기는 cascade 가 source 보존 후
진입 — 의미 변경 0, 자연 propagation (ADR-027 §D5 amendment box 정합).
"""
```

운영 runbook (`docs/runbook/`) 갱신 = 별 인계 (PMO retro carry-over, Story §3 OUT-OF-SCOPE 박제).

### 3.5 D-5 채택 (SecurityArch T-6): `enqueue_retry` race-C path snapshot + orphan Counter

**`dual_writer._promote_after_nas_put` 의 `PromotionVerifyError` 분기**:

```python
except PromotionVerifyError as e:
    log.warning("[dual_writer] promote_l1 verify failed — enqueue retry_queue, status=local_only: %s", e)
    self._uploader.enqueue_retry(key=nas_key, data=source, sha256=sha256)
    # MCT-202 D-5: orphan visibility — sweep cycle 자연 회수까지 추적
    mctrader_retry_orphan_total.labels(tier=self._tier_label_from_key(nas_key)).inc()
    return "local_only"
```

`mctrader_retry_orphan_total{tier}` Counter 신규 (3 series ≤ 50). 의미: HEAD verify fail → retry_queue enqueue → source 보존 → 다음 sweep cycle 자연 회수까지 orphan window 가시화.

`_tier_label_from_key(nas_key)` = `build_nas_key` 의 `tier=L{1,2,3}/` 컴포넌트 parse (DualWriter 내부 helper, `runner.py::scan_and_cleanup_legacy` 의 tier 추출 패턴 답습).

### 3.6 D-6 채택 (OpRiskArch INV-H): `gc.py run_gc()` legacy safety net 보존

`gc.py::run_gc()` (7d FIFO grace + dry-run + 순차 GC) = 변경 0. 폐기 검토 = 14d production evidence gate (cascade post-LAND 14d rolling `mctrader_retry_orphan_total` = 0 + `compactor_local_self_delete_total{outcome="committed_unlinked"}` 정상 ramp-up) 후 별 Story carry-over.

이유 (OpRiskArch):
- 즉시 폐기 시 transient race window (e.g. cascade caller wiring bug, sweep cycle stall) 흡수 0 → disk-full 재발 risk.
- 14d production evidence 박제 후 safety net 자연 deprecation.

### 3.7 Counter 5 outcome 채택 (TestContract 의제 1)

`compactor_local_self_delete_total{tier, outcome}` 5 outcome:

| outcome | 진입 조건 | source 상태 |
|---|---|---|
| `committed_unlinked` | NAS commit + 4-HEAD pass + unlink success | unlinked |
| `committed_unlink_failed` | NAS commit + 4-HEAD pass + unlink OSError | retained (sweep fallback) |
| `local_only_retained` | NAS status='queued' (retry_queue enqueue) | retained |
| `hard_floor_retained` | NAS status='hard_floor_blocked' | retained |
| **`already_promoted`** (NEW) | restart recovery / sweep cycle 진입 시 source 부재 (concurrent unlink) | absent (idempotent no-op) |

3 tier × 5 outcome = 15 series + `mctrader_retry_orphan_total{tier}` 3 series = **18 series 총** (≤ 50 ADR-027 §D6 invariant 정합).

### 3.8 §11.6 idempotency replay 활성화

MCT-189 INV-6 propagation: cascade 가 동일 (tier, parquet_path, sha256) 입력 재실행 시 idempotent.

3 case (TestContract §8 박제 의무):
- **Case 1**: NAS object 이미 commit (sha256 metadata match) + local source 존재 → `_promote_after_nas_put` 가 4-HEAD verify pass + unlink. Counter `committed_unlinked` += 1.
- **Case 2**: NAS object 이미 commit + local source 부재 (1차 cascade 완료 후 재실행) → `_promote_after_nas_put` `FileNotFoundError` graceful → Counter `already_promoted` += 1. status='committed' 반환 (D-7 A 정합).
- **Case 3**: NAS PUT 재실행 → `nas_uploader.put_streaming` HEAD-then-PUT idempotency (sha256 metadata match → `skipped_idempotent`) → `_COMMITTED_STATUSES` 진입 → cascade 정상.

### 3.9 sweep race FileNotFoundError 별 분기 (SecurityArch T-7)

`runner.py:394 scan_and_cleanup_legacy` 의 `except (OSError, RuntimeError)` 가 `FileNotFoundError` (race window) 를 `errors` 로 분류 → 본 Story 가 `race_noop` 별 분기 추가:

```python
except FileNotFoundError:
    # MCT-202 sweep race window — eager cascade 가 이미 unlink. graceful no-op.
    log.debug("[runner] sweep race noop (eager cascade already unlinked) nas_key=%s", nas_key)
    # cleaned 도 errors 도 아님 — race_noop 카운터 별도 emit
    mctrader_legacy_cleanup_race_noop_total.inc()
except (OSError, RuntimeError):
    errors += 1
    log.exception("[runner] legacy cleanup error nas_key=%s", nas_key)
```

`mctrader_legacy_cleanup_race_noop_total` 신규 Counter (1 series, label 0 — sweep cycle 자체가 race 만 보고).

## §4 인터페이스 변경

### 4.1 `DualWriter.write()` 시그니처

before (`dual_writer.py:138-145`):
```python
def write(
    self,
    *,
    local_path: Path,
    nas_key: str,
    data: bytes | Path,
    sha256: str,
) -> DualWriteResult:
```

after:
```python
def write(
    self,
    *,
    local_path: Path,
    nas_key: str,
    data: bytes | Path,
    sha256: str,
    source_to_delete: Path | None = None,   # MCT-202: caller-side explicit cascade intent
) -> DualWriteResult:
```

**backward compat**: `source_to_delete=None` default → MCT-189 LAND 동작 유지 (regression 차단).

### 4.2 `_promote_after_nas_put` 반환 타입 확장

before:
```python
def _promote_after_nas_put(...) -> Literal["committed", "local_only"]:
```

after:
```python
def _promote_after_nas_put(...) -> Literal["committed", "local_only", "already_promoted"]:
```

`already_promoted` = `FileNotFoundError` 분기 (concurrent unlink / idempotent re-entry). 기존 `return "committed"` (D-7 A) → `return "already_promoted"` 로 분화 (Counter outcome 5종 정합).

INV-1 XOR 만족 (NAS object 존재 + local source 부재) 동일.

### 4.3 신규 Prometheus metric

```python
# prometheus_exporters.py 신규 3종
compactor_local_self_delete_total = Counter(
    "compactor_local_self_delete_total",
    "Compactor local source self-delete outcome (MCT-202 cascade)",
    labelnames=["tier", "outcome"],
)
# outcome enum: committed_unlinked / committed_unlink_failed / local_only_retained
#               / hard_floor_retained / already_promoted

mctrader_retry_orphan_total = Counter(
    "mctrader_retry_orphan_total",
    "PromotionVerifyError → retry_queue enqueue (source 보존, sweep cycle 자연 회수)",
    labelnames=["tier"],
)

mctrader_legacy_cleanup_race_noop_total = Counter(
    "mctrader_legacy_cleanup_race_noop_total",
    "scan_and_cleanup_legacy sweep race noop (eager cascade 가 이미 unlink, graceful skip)",
)
```

cardinality:
- `compactor_local_self_delete_total`: 3 tier × 5 outcome = 15 series
- `mctrader_retry_orphan_total`: 3 series
- `mctrader_legacy_cleanup_race_noop_total`: 1 series

**총 19 series 추가** → 기존 active label set 과 합산 ≤ 50 (ADR-027 §D6 cardinality invariant 정합).

## §5 데이터 모델 (변경 0)

- L1/L2/L3 Parquet schema: 변경 0 (ADR-009 §D2 정합).
- NAS object key layout: 변경 0 (ADR-034 `build_nas_key` SSOT 정합).
- `.compacted` sentinel: 변경 0 (ADR-017 §D2 정합).
- WAL `.sealed` segment naming: 변경 0.

본 Story = **lifecycle 변경 only** (path layout / schema / sentinel 보존).

## §6 의존성

- **MCT-156** (LAND) — streaming sha256 chunk read
- **MCT-160** (LAND) — D6 Path streaming guard
- **MCT-161** (LAND) — bucket versioning Enabled (PITR rollback 안전망)
- **MCT-169** (LAND) — NAS GET source path
- **MCT-189** (LAND) — WAL→L1 grace-0 caller-wired self-delete (본 Story = cascade 확장)
- **MCT-173** (LAND) — backfill mode (WAL grace 폐기 시 disaster recovery 흡수)
- **MCT-141** (LAND) — ADR-034 U2-HELPER (build_nas_key SSOT)

## §7 본 설계 (6 deputy 통합 INV 12종)

### §7.1 SecurityArch — 4-tuple HEAD verify 3-tier 동형 (INV-SEC-1)

`promote_l1` 의 4-tuple HEAD verify (ETag + VersionId + sha256 Metadata + ContentLength) 가 cascade 3-tier 모두 동형 적용. callee 변경 0, caller 측 `source_to_delete=parquet_path` 명시만으로 자연 propagation.

verified-via: `dual_writer.py:298-332 _promote_after_nas_put` (MCT-189 LAND, `0e244e9`).

### §7.2 SecurityArch — Pre-delete HEAD guard (INV-SEC-2 = INV-B)

`promote_l1` 내부 pre-delete HEAD guard (race window 차단) 재사용. caller 가 별 guard 추가 0.

### §7.3 SecurityArch — status XOR source exists (INV-SEC-3 = INV-D)

| `result.status` | source 상태 |
|---|---|
| `committed` | unlinked (4-HEAD pass) OR already_promoted (concurrent unlink) |
| `local_only` | retained |
| `hard_floor_blocked` | retained |

mutually exclusive (XOR) 보증. invariant test 박제 의무 (§8.1).

### §7.4 OperationalRiskArch — 운영 리스크 표 (INV-E~I 5종)

| INV | 영역 | 내용 | 검증 |
|---|---|---|---|
| **INV-E** | env isolation | `self._dual_writer is None` 분기에서 cascade 0 (test/local dev 환경 보존) | `runner.py:281` guard 박제 |
| **INV-F** | DR layer demotion | local volume DR (replica 책임) ↓ + NAS bucket versioning DR (PITR + Object Lock 30d) ↑ | MCT-161 LAND + ADR-027 §D6 prerequisite |
| **INV-G** | operator window 0 | monitoring 강도 의존 (alarm 임계치 P0 = `compactor_local_self_delete_total{outcome="committed_unlink_failed"}` rate, P2 = `mctrader_retry_orphan_total` rate) | Grafana alert (별 인계, runbook) |
| **INV-H** | gc.py 보존 (D-6) | `run_gc()` 7d FIFO grace = legacy safety net. 14d production evidence gate 후 별 Story 폐기 검토 | grep `def run_gc` 1 hit 유지 |
| **INV-I** | gc_daemon `_archive_failed` 의미 변경 0 (D-4) | status='local_only' / 'hard_floor_blocked' 7d extension 분기 자연 보존 | docstring amendment only, 코드 변경 0 |

### §7.5 SecurityArch — 위협 ↔ 완화 매트릭스 (T-1~T-10)

| T-# | 위협 | 완화 |
|---|---|---|
| T-1 | output self-unlink regression (D-1 옵션 A 시) | **D-1 옵션 B 채택** (callee `source_to_delete` 명시) |
| T-2 | NAS GET 모드 input source 미회수 | **D-2 옵션 C 채택** + 별 Story MCT-204 carry-over |
| T-3 | `_historical_dual_write` cascade drift | **D-3 동시 LAND** (`source_to_delete` + 4xx wrap) |
| T-4 | restart recovery 시 source 부재 → Counter outcome 부재 | **`already_promoted` 5번째 outcome 추가** (의제 1 채택) |
| T-5 | `NASOperationalAlert` raw propagation drift (historical path) | **`_historical_dual_write` re-raise wrap 동시 LAND** (D-3) |
| T-6 | `PromotionVerifyError` → `enqueue_retry` 시 source 추적 0 | **D-5 옵션 C** (path snapshot + `mctrader_retry_orphan_total` Counter) |
| T-7 | sweep race window → `errors` 오분류 | **`FileNotFoundError` 별 분기 + `mctrader_legacy_cleanup_race_noop_total` Counter** |
| T-8 | sha256 hex Prom label 누출 (cardinality 폭증) | **log only, Counter label = tier (low cardinality)** |
| T-9 | bucket versioning OFF 환경 silent delete | **start gate: bucket versioning=Enabled 확인 (MCT-161 prerequisite)** |
| T-10 | concurrent compactor instances (multi-node) | **`.compacted` sentinel atomic + NAS HEAD-then-PUT idempotency** (ADR-017 §D2 정합) |

### §7.6 SecurityArch — sha256 hex log only, Prom label 0 (INV-SEC-6)

sha256 = log message 만 (`log.info("...sha256=%r")`). Prometheus Counter labelnames 에 sha256 포함 금지 (cardinality 무한 폭증 risk).

### §7.7 NAS GET 모드 cascade 정합 (chief author 신규 sub-section)

production 환경 = compactor 가 NAS object 를 source 로 GET (ADR-034 layout `market/<channel>/schema_version=*/tier=L1/...` flat). cascade 영향:

- **input source** (compactor 가 GET 한 NAS object) = 본 Story 회수 0 (D-2 옵션 C). MCT-204 별 Story.
- **output local** (compactor 가 생성한 L2/L3 local parquet) = 본 Story cascade target. NAS GET 모드 여부 무관, output 은 항상 local 생성 → cascade 동작 동일.

verified-via: `l2.py:147-149` (`os.replace(str(tmp), str(out_path))` atomic rename → local out_path 생성), `l3.py:147-149` 동형.

### §7.8 INV 12종 종합

| INV | 출처 | 내용 |
|---|---|---|
| INV-A | Story §4 | eager unlink ↔ sweep race → graceful no-op (FileNotFoundError catch) |
| INV-B | Story §4 | pre-delete HEAD guard 재사용 (MCT-189 INV-3 동형) |
| INV-C | Story §4 | forward-only invariant 3-tier 확장 (ADR-009 §D12.2) |
| INV-D | Story §4 | status='committed' XOR source exists |
| INV-E | OpRiskArch | `_dual_writer is None` 분기 cascade 0 |
| INV-F | OpRiskArch | DR layer demotion (local ↓ + NAS versioning ↑) |
| INV-G | OpRiskArch | operator monitoring 강도 의존 |
| INV-H | OpRiskArch | gc.py `run_gc()` legacy safety net 보존 |
| INV-I | OpRiskArch | gc_daemon `_archive_failed` 의미 변경 0 |
| INV-SEC-1 | SecurityArch | 4-tuple HEAD verify 3-tier 동형 |
| INV-SEC-6 | SecurityArch | sha256 hex log only, Prom label 0 |
| INV-SEC-7 | SecurityArch | `enqueue_retry` orphan Counter (D-5) |

## §8 Test Contract

### §8.1 Unit tests

**`tests/unit/nas_storage/test_dual_writer_eager_l2_l3.py`** (TestContract 의제 2):

```python
# 1. source_to_delete=None → 기존 MCT-189 동작 (regression 차단)
def test_source_to_delete_none_preserves_mct189_behavior():
    """data=Path, data != local_path → 기존 분기 진입, source unlink."""
    ...

# 2. source_to_delete=Path → 명시 cascade intent
def test_source_to_delete_explicit_triggers_cascade():
    """source_to_delete=parquet_path → committed 시 unlink."""
    ...

# 3. status XOR source exists (INV-D)
@pytest.mark.parametrize("status,source_exists", [
    ("committed", False),       # unlinked
    ("local_only", True),       # retained
    ("hard_floor_blocked", True),  # retained
])
def test_status_xor_source_exists(status, source_exists):
    ...

# 4. already_promoted outcome (Counter outcome 5)
def test_already_promoted_idempotent_no_op():
    """source 부재 시 FileNotFoundError graceful → already_promoted Counter += 1."""
    ...
```

**`tests/unit/compactor/test_runner_dispatch_dual_write.py`**:

```python
def test_dispatch_passes_source_to_delete_eq_parquet_path():
    """_dispatch_dual_write 가 source_to_delete=parquet_path 명시 전달."""
    ...

def test_nas_operational_alert_reraise_propagation():
    """4xx fail-fast → NASOperationalAlert propagate (silent skip 0)."""
    ...
```

**`tests/unit/compactor/test_runner_historical_dual_write.py`** (D-3 동형):

```python
def test_historical_passes_source_to_delete():
    """_historical_dual_write 동형 source_to_delete 전달."""
    ...

def test_historical_nas_operational_alert_reraise():
    """_historical_dual_write 도 4xx fail-fast re-raise (T-5 drift 차단)."""
    ...
```

**`tests/unit/compactor/test_metrics_self_delete.py`**:

```python
@pytest.mark.parametrize("tier", ["L1", "L2", "L3"])
@pytest.mark.parametrize("outcome", [
    "committed_unlinked", "committed_unlink_failed",
    "local_only_retained", "hard_floor_retained", "already_promoted",
])
def test_counter_emit_parametrize(tier, outcome):
    """3 tier × 5 outcome = 15 series, cardinality assert."""
    ...

def test_cardinality_total_le_50():
    """compactor_local_self_delete + retry_orphan + race_noop ≤ 50 series."""
    ...

def test_sha256_not_in_prom_label():
    """INV-SEC-6: sha256 hex Prometheus label 0."""
    ...
```

### §8.2 Integration tests

**`tests/integration/test_eager_cleanup_cascade.py`** (testcontainers MinIO):

```python
def test_l1_to_l2_cascade_source_eager_unlink():
    """L1 parquet 생성 → L2 compaction → L1 source 4-HEAD verify pass → unlink."""
    # Given: L1 parquet local + L1 NAS object
    # When: _run_l2 dispatch → DualWriter.write(source_to_delete=l1_parquet)
    # Then: L2 NAS commit + L1 parquet local 부재
    ...

def test_l2_to_l3_cascade_source_eager_unlink():
    """L2 parquet 생성 → L3 compaction → L2 source unlink."""
    ...

def test_sweep_race_filenotfounderror_branch():
    """eager cascade 가 이미 unlink → sweep cycle FileNotFoundError graceful."""
    # Given: L1 parquet, eager cascade 가 이미 unlink
    # When: scan_and_cleanup_legacy 가 동일 path 진입
    # Then: race_noop Counter += 1, errors Counter == 0
    ...

def test_idempotent_replay_case_1_re_entry_with_local():
    """§11.6 Case 1: source 존재 + NAS commit 재진입 → committed_unlinked."""
    ...

def test_idempotent_replay_case_2_re_entry_without_local():
    """§11.6 Case 2: source 부재 + NAS commit 재진입 → already_promoted."""
    ...

def test_idempotent_replay_case_3_nas_put_skipped_idempotent():
    """§11.6 Case 3: NAS HEAD-then-PUT skipped_idempotent → committed cascade."""
    ...
```

### §8.3 성능 영향

- DualWriter.write 추가 latency: `source_to_delete` 분기 진입 시 `_promote_after_nas_put` 호출 (기존 MCT-189 path 와 동일 비용) — 추가 latency ≈ 0.
- Prometheus Counter emit: O(1) per dispatch (label cardinality 15 + 3 + 1 = 19) — 성능 영향 0.
- 3-tier 동시 cascade 시 disk reclaim rate ↑ (production 실측 117GB 누적 → 자연 회수).

**N/A 명시**: 성능 회귀 risk 0 (callee 변경 0, caller 측 명시 파라미터만 추가).

## §9 분기 선택 (D-1~D-6 결정 요약 + 별 Story carry-over)

### 채택안 종합

D-1 = 옵션 B / D-2 = 옵션 C / D-3 = 포함 + 4xx wrap / D-4 = docstring amendment / D-5 = 옵션 C / D-6 = 보존 / Counter outcome 5종 / §11.6 활성화.

### 별 Story carry-over (OUT-OF-SCOPE)

- **MCT-203** — `promote_l1` SSOT rename → `promote_tier` (tier dimension 일반화).
- **MCT-204** — NAS object lifecycle (cascade 후 NAS L1/L2 object 측 회수 정책).
- **MCT-205** — `_dispatch_dual_write` + `_historical_dual_write` 통합 refactor (drift risk 차단).
- **gc.py 폐기 검토** — 14d production evidence gate 후 별 Story (D-6).
- **운영 runbook 갱신** — `gc_daemon._archive_failed` operator 정책 (D-4, PMO retro carry-over).

## §10 ADR 정합성 (amendment 4종)

본 Story 가 신규 ADR 발행 0. 모든 결정은 기존 ADR amendment 흡수 (Story §11 FeasibilityAgent 권고 정합).

amendment 박제 위치:
- **ADR-027 §D5** — eager unlink ↔ sweep race 분기 + 4xx fail-fast 정합 amendment box (본 Plan §3.3 + §3.9)
- **ADR-027 §D7** — WAL 24h grace 폐기 + NAS-SoT 격상 + retry_queue + MCT-173 backfill 3종 흡수 amendment box
- **ADR-029 §D3** — grace-0 tier dimension 일반화 (L1 단독 → 3-tier cascade) amendment box (본 Plan §3.1)
- **ADR-029 §D11** (신설) — 3-tier eager unlink invariant (INV-A~D 4종 + INV-E~I 5종 + INV-SEC-1/6/7) amendment box
- **ADR-017 §D2** — compactor cascade self-delete = caller-wiring SSOT (callee 내부 source unlink path 부재 박제) amendment box
- **ADR-017 §D5** — DualWriter status='committed' XOR source exists invariant 박제 amendment box
- **ADR-009 §D12.2** — forward-only invariant 3-tier 확장 annotation

## §11 데이터 마이그레이션

### §11.1 PIT snapshot 정책

본 Story = lifecycle 변경 only. 기존 데이터 (L1/L2/L3 parquet, NAS object) PIT 영향 0. forward-only invariant (ADR-009 §D12.2) 정합 — 본 Story LAND 시점 이후 신규 cascade 만 적용.

### §11.2 NAS object lifecycle 영향

NAS object = 본 Story 변경 0. 기존 path layout (ADR-034 `build_nas_key` SSOT) 그대로 보존. NAS bucket versioning=Enabled (MCT-161 LAND) + NoncurrentVersionExpiration 30d 안전망 유지.

### §11.3 Sentinel 호환성

`.compacted` sentinel (ADR-017 §D2) = 변경 0. cascade 가 sentinel emit 의존 0 (caller-wired, sentinel 부재 환경에서도 정상 동작).

### §11.4 Rollback 절차

본 Story Phase 2 (mctrader-data src) revert 시:
1. `DualWriter.write()` 시그니처 `source_to_delete` 파라미터 제거 (PR revert)
2. caller (`_dispatch_dual_write` + `_historical_dual_write`) 의 `source_to_delete=parquet_path` 전달 제거
3. 신규 Counter 3종 제거 (Prometheus scrape 호환성 자연 보존 — Counter 부재 = 0 emit)

rollback 후 → MCT-189 LAND 상태 복귀 (WAL→L1 only cascade). disk-full 빈발 재발 risk = 운영 SOP `scan_and_cleanup_legacy` sweep 강화 (batch_limit=2000 등) 로 임시 완화.

### §11.5 데이터 무결성 검증

본 Story = lifecycle only → schema / row count / sha256 영향 0. 별도 무결성 검증 절차 부재.

단, **cascade post-LAND 14d production evidence gate** (D-6 정합):
- `mctrader_retry_orphan_total` rate = 0 (정상)
- `compactor_local_self_delete_total{outcome="committed_unlinked"}` 정상 ramp-up (3-tier 분포 균형)
- `compactor_local_self_delete_total{outcome="committed_unlink_failed"}` rate < 0.1% (P0 alarm)
- local disk usage 정상 감소 곡선 (117GB → 안정 수준)

### §11.6 idempotency replay (CONDITIONAL 활성화, MCT-189 INV-6 propagation)

본 Story 가 `_promote_after_nas_put` 의 `FileNotFoundError` 분기 + `nas_uploader.put_streaming` HEAD-then-PUT idempotency 재사용 → 동일 (tier, parquet_path, sha256) 입력 재실행 시 idempotent.

**replay 빈도 박제 의무 (PL 권고 채택)**:

| 빈도 | trigger | 처리 |
|---|---|---|
| 빈번 | restart recovery (compactor pod restart, K8s OOMKilled 등) | 부분 cascade 후 재진입 — `already_promoted` 또는 `committed_unlinked` outcome 균등 분포 |
| 빈번 | sweep cycle (`scan_and_cleanup_legacy` 6-min cadence) | source 부재 → `FileNotFoundError` → race_noop Counter (별 분기) |
| 드물 | manual replay (operator intervention) | `mctrader compact --replay <date>` (별 CLI 가능, MCT-203 carry-over) |

3 case verification (§3.8):
- Case 1 (source 존재 + NAS commit): `committed_unlinked` outcome
- Case 2 (source 부재 + NAS commit): `already_promoted` outcome
- Case 3 (NAS HEAD-then-PUT match): `skipped_idempotent` → committed cascade

Integration test §8.2 가 3 case 전부 박제 (test_idempotent_replay_case_1/2/3).

### §11.7 N/A 영역

- 신규 storage backend 도입: N/A
- schema migration: N/A
- backfill script: N/A (lifecycle only)
- data conversion: N/A

## §12 RDS 영향

N/A — 본 Story 는 NAS object storage + local filesystem lifecycle 만 영향. RDS / RDB 미사용.

## §13 Phase 1 산출물 self-check 결과

### A. Mechanical 7-item (ADR-065 / CFP-438) — non-marketplace 영역

| # | item | status | rationale |
|---|---|---|---|
| 1 | label-registry-v2.md 변경 시 bootstrap-labels.sh sync | NA | 본 Story label registry 미변경 |
| 2 | doc-locations.yaml 변경 시 check-doc-locations.sh --regen | NA | 본 Story doc-locations 미변경 |
| 3 | 신규 templates/github-workflows/*.yml 시 self-app copy | NA | 본 Story workflow 미신설 |
| 4 | CLAUDE.md / docs/** link target Phase 1 분배 확인 | PASS | docs/stories/MCT-202.md + docs/change-plans/MCT-202-* + docs/adr/ADR-027/029/017/009 + docs/domain-knowledge/grace-0-local-delete.md = 모두 Phase 1 PR scope |
| 5 | MANIFEST.yaml registries 블록 갱신 | NA | 본 Story inter-plugin contract 미변경 |
| 6 | section-ownership.yaml policy row append | NA | 본 Story parallel work 영역 외 |
| 7 | doc-locations.yaml 신규 doc type row | NA | 신규 doc type 미신설 |

**mechanical_self_check_passed: true** (PASS 1 + NA 6, FAIL 0).

### B. Semantic boundary completeness 4-invariant (ADR-068 / CFP-527)

| Invariant | 영역 | status | verification format |
|---|---|---|---|
| I-1 | API contract semantic completeness | PASS | §4.1 `DualWriter.write()` 시그니처 + §4.2 `_promote_after_nas_put` 반환 enum (committed/local_only/already_promoted) docstring + enum × 의미 매핑표 (§3.7 Counter 5 outcome 표) |
| I-2 | Cross-module propagation completeness | PASS | §3.7 Counter outcome × caller 처리 매핑표 (5 outcome × 3 caller: `_dispatch_dual_write` / `_historical_dual_write` / sweep `scan_and_cleanup_legacy`) |
| I-3 | Guard placement intent | PASS | §3.1 `source_to_delete is None` guard = 함수 진입 직후 (callee `dual_writer.py:239` `nas_put_result.status in _COMMITTED_STATUSES` 분기 내 추가 guard 도식) |
| I-4 | Wording SSOT | PASS | Story §3/§7 ↔ ADR-029 §D11 (신설) ↔ impl identifier (`source_to_delete`, `already_promoted`) 3-column 대조 — wording SSOT `DualWriteResult.status` enum + `compactor_local_self_delete_total` outcome enum 정합 |

**boundary_completeness_self_check_passed: true** (PASS 4, FAIL 0).

### C. Dimensional empirical grounding (ADR-068 Amendment 1 / CFP-528)

quantitative parameter 별 empirical-source annotation:

| parameter | dimension | value | empirical_source | status |
|---|---|---|---|---|
| Counter cardinality 상한 | cardinality | ≤ 50 | ADR-027 §D6 invariant SSOT | PASS |
| Counter 신규 series | cardinality | 19 series (15 + 3 + 1) | §4.3 표 직접 산출 | PASS |
| `scan_and_cleanup_legacy` batch_limit default | rate | 500 per-sweep | `runner.py:316 _LEGACY_BATCH_DEFAULT=500` (production verified) | PASS |
| sweep cycle cadence | rate | 6-min | `runner.py:332 docstring` (production verified, MCT-189 LAND) | PASS |
| `mctrader_retry_orphan_total` P2 alarm 임계치 | rate | TBD (post-LAND 14d production 실측 후) | `[empirical-source: TBD]` — Phase 1.5 wiretap (production rolling 14d) 후 확정 | PASS (TBD 박제) |
| `committed_unlink_failed` P0 alarm 임계치 | rate | < 0.1% | `[empirical-source: TBD]` — production deploy 후 P0 baseline 측정 | PASS (TBD 박제) |
| local disk reclaim 목표 | volume | 117GB → 안정 수준 (TBD) | `[empirical-source: production 2026-05-18 실측]` (Story §0 verified-via `0e244e9`) | PASS |
| NAS HEAD-then-PUT idempotency 4-HEAD verify | accuracy | ETag + VersionId + sha256 Metadata + ContentLength 4-tuple | ADR-029 §D3 + MCT-189 INV-2 SSOT | PASS |

**dimensional_empirical_self_check_passed: true** (PASS 8, FAIL 0). TBD 박제 2종 = Phase 1.5 wiretap 의무 (post-LAND 14d production 측정).

### D. Marketplace sync proactive (ADR-063 Amendment 1 / CFP-597)

본 Story = marketplace 영역 외 (mctrader-data + mctrader-hub, plugin marketplace 미관여). `plugin.json` mirrored field diff 0.

**marketplace_sync_required: false** (silent skip 금지 — 본 항목 명시).

### 종합 verdict packet field

```yaml
mechanical_self_check_passed: true
boundary_completeness_self_check_passed: true
dimensional_empirical_self_check_passed: true
marketplace_sync_declared: false  # mirrored field 변경 0
```

4 필드 모두 PASS → Phase 1 commit 진행 ready.

---

**Phase 1 PR scope** (mctrader-hub): 본 Change Plan + ADR amendment 4종 + grace-0-local-delete.md amendment + Story §3/§6/§7/§11 self-write.

**Phase 2 PR scope** (mctrader-data): `dual_writer.py` 시그니처 변경 + `runner.py` caller wiring (`_dispatch_dual_write` + `_historical_dual_write`) + Prometheus Counter 신규 + tests/** (unit + integration).
