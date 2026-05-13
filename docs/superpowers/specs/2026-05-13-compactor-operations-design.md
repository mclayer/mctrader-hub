---
date: 2026-05-13
epic_key: EPIC-compactor-operations
parent_dependency: EPIC-cold-tier-stage-3-wiring
status: Proposed
related_adrs:
  - ADR-027 (amend D4 — channel parity 정책)
  - ADR-009 (amend §D11 — orderbookdepth schema)
  - ADR-XXX (신규 — object store durability/versioning, MCT-161)
related_stories:
  - MCT-162 (신규 — L1 채널 parity + orderbookdepth schema)
  - MCT-160 (retitle — L2/L3 cadence + OOM + L1 backlog 79k cleanup)
  - MCT-161 (NAS durability + MCT-153 손실 재발 방지)
---

# EPIC-compactor-operations — Compactor Production 5중 차단 Fix

## 0. 동기 (Why)

MCT-156 (Stage 3 wiring) production deploy 직후 사용자 NAS bucket 실측에서 발견된 **5중 차단** 해소:

1. **upbit L1 결과 today = 0** (WAL sealed 4,749 today + 13,810 모든 date 있음에도 partition 미생성)
2. **transaction L2 자연 cadence = 0** (manual 호출 success, _run_l2 silent skip)
3. **bucket 463 obj = bithumb orderbooksnapshot only** (52 sym, upbit 0 + transaction 0)
4. **L1 backlog 76,200 → 79,427 (+3,227)** — compactor 처리 속도 < ingester ingestion 속도
5. **upbit/KRW-BTC orderbooksnapshot manual L2 OOM exit 137** (pyarrow concat_tables.sort_by 32GB memory limit + i32 offset 4GB overflow)

추가 사실:
- orderbookdepth channel = bithumb collector emit, L1Compactor `_schema_version` NotImplementedError 즉시 fail (48,629 sealed 누적)
- MCT-153 backfill 산출물 4.2 GiB / 1370 obj 손실 (bucket versioning 미활성 = 복구 불가)
- L1 NAS upload = 0 invariant (ADR-027 §D5) — 4.2 GiB 가 처음부터 NAS 진입 0 가능성

## 1. ResearcherAgent 1차 진단 (5 root cause)

1. **upbit L1 today=0**: WAL channel name (예: `orderbook` 또는 `orderbook_snapshot`) 가 L1Compactor `_schema_version` allowlist (`orderbooksnapshot`) 와 mismatch → NotImplementedError 100% throw → partition 미생성
2. **transaction L2 silent skip**: `L2Compactor.compact_hour` 의 `date_str = hour_utc.strftime("%Y-%m-%d")` 하드코딩 (now UTC date). KST→UTC date roll 시 어제 date 의 L1 결과 hit 0 → silent return None
3. **OOM 137**: orderbooksnapshot per-level row explosion (1 snapshot → 2N rows) × raw_json large_string column 누적 → `pa.concat_tables(...).sort_by("ts_utc")` 단일 buffer 32GB peak + i32 offset 4GB cap overflow
4. **L1 backlog 영구 증가**: orderbookdepth 48,629 sealed + 후속 sealed 가 NotImplementedError drainage 0, ingester 계속 sealed produce → monotonic 증가
5. **MCT-153 4.2GiB 손실**: L1 산출물은 `_dispatch_dual_write` 대상 아님 (ADR-027 §D5 L1 NAS upload=0 invariant). 4.2GiB 가 처음부터 NAS 진입 0 가능성 (hard delete 아님)

## 2. 확정된 8 결정점 + R-EXTRA (사용자 OK 2026-05-13, Codex 합성)

| # | 결정 | 옵션 | 근거 | owner Story |
|---|------|------|------|-----|
| **D1** | orderbookdepth = 신규 schema 정의 | D | WAL payload = delta `changes`, transaction/orderbooksnapshot 와 mismatch | MCT-162 |
| **D2** | L2Compactor `compact_hour` 의 partition-level latest date lookup | B | `hour_utc=now` 하드코딩 제거 | MCT-160 |
| **D3** | streaming write — `ParquetWriter.write_table` per-file loop | A | 메모리 일정, repo 기존 pattern 답습 | MCT-160 |
| **D4** | compactor read-only diagnostic mode preflight | A | RPO=0 정합, fix 전 정지 | MCT-162 (preflight) |
| **D5** | L1 backlog 79k 자연 drainage | A | D1+D3 fix 후 orderbookdepth fast-fail + transaction/orderbooksnapshot 정상 처리 | MCT-160 |
| **D6** | MCT-159 (L2/L3 8.85 GiB migration) 별 Story 유지 | A | scope 분리 (EPIC-cold-tier-stage-3-wiring 소속) | MCT-159 (외부) |
| **D7** | ADR-027 D4 amendment append — channel parity 정책 | A | fail-fast vs silent skip + Prometheus emit obligation | MCT-162 |
| **D8** | 별 ADR-XXX 신규 — object store durability/versioning | C | bucket versioning + replication SSOT | MCT-161 |
| **R-EXTRA** | `_dispatch_dual_write` 의 `read_bytes()` memory 재할당 fix | — | OOM 보조 원인 — DualWriter.write 의 data=Path streaming | MCT-160 |

## 3. 3 Story sequential 분해

### Story-1 MCT-162 (신규) — L1 채널 parity + orderbookdepth schema 정의

**Phase 1 (Architect)**:
- ADR-009 §D11 amendment — orderbookdepth schema (WAL delta `changes` payload)
- ADR-027 D4 amendment — channel parity 정책 + fail-fast vs silent skip + Prometheus emit obligation
- Story §1-§11 작성

**Phase 2 (Developer + QA)**:
- `src/mctrader_data/compactor/l1.py`:
  - `_schema_version` 확장 (orderbookdepth 추가)
  - orderbookdepth converter 추가
  - path derive 로직 확장 (channel allowlist)
- `tests/integration/test_l1_compactor_channel_parity.py` 신규
  - orderbookdepth converter PASS
  - channel allowlist fail-fast (silent skip 금지 verify)
  - Prometheus counter emit

### Story-2 MCT-160 (retitle) — L2/L3 cadence + OOM + L1 backlog 79k cleanup

**기존 title**: "compactor L1 backlog cleanup — orderbookdepth channel FIX + L2 offset overflow FIX + MCT-153 손실 박제 retrofit"
**신규 title**: "L2/L3 cadence + OOM + L1 backlog 79k cleanup"

**Phase 1 (Architect)**:
- `L2Compactor.compact_hour` partition-level latest date lookup 설계 (D2)
- streaming write — `pa.concat_tables` 제거 후 `ParquetWriter.write_table` per-file loop 설계 (D3)
- `_dispatch_dual_write` memory fix 설계 (R-EXTRA — DualWriter.write data=Path streaming)
- Story §1-§11

**Phase 2 (Developer + QA)**:
- `src/mctrader_data/compactor/l2.py`: compact_hour partition lookup + streaming write
- `src/mctrader_data/compactor/runner.py`: `_dispatch_dual_write` memory fix + `_run_l2`/`_run_l3` date 인자 propagate
- `src/mctrader_data/nas_storage/dual_writer.py`: `write()` 의 data=Path streaming
- `tests/integration/test_l2_compact_hour_partition_lookup.py` 신규
- `tests/integration/test_dual_writer_streaming.py` 신규
- L1 backlog drainage verify (epic_close_gate 의 ≤ 1000)

### Story-3 MCT-161 — NAS bucket versioning + replication + MCT-153 손실 재발 방지

**Phase 1 (Architect)**:
- 신규 ADR-XXX (object store durability / versioning policy) author
- Story §1-§11

**Phase 2 (Developer + QA)**:
- `compose.yml`: minio bucket versioning enable
- replication 정책 박제 (or remote replication target 정의)
- bucket versioning enable verify
- MCT-153 손실 재발 방지 evidence pack

## 4. Story sequence + 의존

```
preflight: compactor read-only diagnostic mode (docker compose stop compactor)
  ↓
Story-1 MCT-162 (L1 parity) — ADR amendment 2건 + l1.py 본문
  ↓
Story-2 MCT-160 (L2/L3 cadence + OOM) — l2.py + runner.py + dual_writer.py
  ↓
Story-3 MCT-161 (NAS durability) — ADR-XXX 신규 + compose.yml
  ↓
Epic CLOSED — PMOAgent retro + L1 backlog ≤ 1000 verify
```

순서: PMO 규칙 2 (인터페이스+첫 구체 vertical slice) + 규칙 3 (merge 충돌 회피, l1.py / l2.py / dual_writer.py 동시 수정 시 충돌).

## 5. Preflight obligation

| Story | obligation | verify |
|-------|-----------|--------|
| MCT-162 | compactor read-only diagnostic mode (`docker compose stop compactor`) | `docker compose ps compactor` STATE = exited |
| MCT-160 | L1 backlog size 측정 (R1 mitigation — OOM 임계 초과 여부) | `find /var/.../wal -name '*.ndjson.sealed' | wc -l` 박제 |
| MCT-161 | MCT-160 land verify — L1 backlog ≤ 1000 도달 | epic_close_gate 의 MCT-160 항목 satisfied |

## 6. Risks

- **R1 (HIGH)**: L1 backlog 진행 중 자라며 cleanup 시 OOM 재발 — Story-2 진입 시점 L1 backlog 가 OOM 임계 초과 가능. mitigation: D4 preflight + D3 streaming write + D2 partition lookup 결합.
- **R2 (MEDIUM)**: drainage 속도 < 유입 속도 — Story-2 land 후에도 L1 backlog ≤ 1000 미달 가능. mitigation: epic_close_gate verify + batch size 조정 또는 별 cleanup batch Story.
- **R3 (MEDIUM)**: ADR-XXX 발의 timeline 지연 — Story-3 까지 NAS bucket versioning 미적용. mitigation: Story-3 진입 시 ADR-XXX 신규 author + versioning enable 동시 land.

## 7. Epic close gate

- MCT-162 PR MERGED + ADR-027 D4 amendment + ADR-009 §D11 amendment land
- MCT-160 PR MERGED + L1 backlog ≤ 1000 verify (자연 drainage 확인)
- MCT-161 PR MERGED + ADR-XXX 신규 land + NAS bucket versioning enable verify
- PMOAgent retro write (templates/retro.md schema)
- Epic milestone description 갱신 + gate:retro-complete label

## 8. scope_manifest 초안 (Phase 1 PR Issue body 첨부용)

```yaml
epic_key: EPIC-compactor-operations
epic_title: "compactor operations — L1 channel parity + L2 cadence + NAS durability"
parent_dependency: EPIC-cold-tier-stage-3-wiring
parent_dependency_note: "MCT-156 land 후 cycle — L1 backlog 79k 가 MCT-156 deploy 시점부터 누적 시작"

planned_adrs:
  amendments:
    - { adr: ADR-027, section: D4, title: "channel parity 정책 + fail-fast", owner: MCT-162 }
    - { adr: ADR-009, section: §D11, title: "orderbookdepth schema (WAL delta changes)", owner: MCT-162 }
  new_proposals:
    - { adr: ADR-XXX, title: "object store durability / versioning policy", owner: MCT-161, status: Proposed }

planned_files:
  mctrader-data:
    - { path: src/mctrader_data/compactor/l1.py, owner: MCT-162, change: "_schema_version + orderbookdepth converter + path derive" }
    - { path: src/mctrader_data/compactor/l2.py, owner: MCT-160, change: "compact_hour partition-level latest date lookup + ParquetWriter streaming" }
    - { path: src/mctrader_data/compactor/runner.py, owner: MCT-160, change: "_dispatch_dual_write memory fix + date propagate" }
    - { path: src/mctrader_data/nas_storage/dual_writer.py, owner: MCT-160, change: "write() data=Path streaming" }
    - { path: tests/integration/test_l1_compactor_channel_parity.py, owner: MCT-162, change: "신규" }
    - { path: tests/integration/test_l2_compact_hour_partition_lookup.py, owner: MCT-160, change: "신규" }
    - { path: tests/integration/test_dual_writer_streaming.py, owner: MCT-160, change: "신규" }
    - { path: compose.yml, owner: MCT-161, change: "minio bucket versioning enable" }
  mctrader-hub:
    - { path: docs/adr/ADR-027-*.md, owner: MCT-162, change: "D4 amendment" }
    - { path: docs/adr/ADR-009-*.md, owner: MCT-162, change: "§D11 amendment" }
    - { path: docs/adr/ADR-XXX-object-store-durability.md, owner: MCT-161, change: "신규 ADR" }
    - { path: docs/stories/MCT-162.md, owner: MCT-162, change: "신규" }
    - { path: docs/stories/MCT-160.md, owner: MCT-160, change: "retitle + scope rewrite" }
    - { path: docs/stories/MCT-161.md, owner: MCT-161, change: "신규" }
    - { path: scope_manifests/EPIC-compactor-operations.yaml, owner: MCT-162, change: "신규 manifest" }
    - { path: .codeforge/counters.json, owner: MCT-162, change: "next 162→163 + MCT-160 retitle" }

design_decisions:
  D1: { decision: "orderbookdepth 신규 schema", binding: "ADR-009 §D11", owner: MCT-162 }
  D2: { decision: "compact_hour partition-level latest date lookup", binding: "구현", owner: MCT-160 }
  D3: { decision: "streaming write (concat_tables 제거)", binding: "구현", owner: MCT-160 }
  D4: { decision: "compactor read-only preflight", binding: "preflight_obligation", owner: MCT-162 }
  D5: { decision: "L1 backlog 자연 drainage", binding: "epic_close_gate", owner: MCT-160 }
  D6: { decision: "MCT-159 별 Story 유지", binding: "scope 분리", owner: MCT-159 외부 }
  D7: { decision: "ADR-027 D4 amendment", binding: "ADR-027 D4", owner: MCT-162 }
  D8: { decision: "별 ADR-XXX 신규", binding: "ADR-XXX", owner: MCT-161 }
  R-EXTRA: { decision: "_dispatch_dual_write read_bytes fix", binding: "구현", owner: MCT-160 }

risks:
  R1: { severity: HIGH, desc: "L1 backlog 진행 중 OOM 재발", mitigation: "D4 preflight + D3 streaming + D2 partition lookup", owner: MCT-160 }
  R2: { severity: MEDIUM, desc: "drainage < 유입 속도", mitigation: "epic_close_gate verify + batch 조정", owner: MCT-160 }
  R3: { severity: MEDIUM, desc: "ADR-XXX 발의 지연", mitigation: "Story-3 진입 시 신규 author + versioning 동시 land", owner: MCT-161 }

dependency:
  blocked_by: [EPIC-cold-tier-stage-3-wiring]
  reuses_primitives: [NASUploader, DualWriter, RetryQueue, InvariantHarness, SOPRunner]

story_sequence:
  - { story: MCT-162, phase: 1, rule: "규칙 2 — 인터페이스+첫 구체" }
  - { story: MCT-160, phase: 2, rule: "규칙 3 — merge 충돌 회피" }
  - { story: MCT-161, phase: 3, rule: "규칙 3 — durability 정책 정립" }

epic_close_gate:
  - "MCT-162 PR MERGED + ADR amendment 2건"
  - "MCT-160 PR MERGED + L1 backlog ≤ 1000 verify"
  - "MCT-161 PR MERGED + ADR-XXX 신규 land + versioning verify"
  - "PMOAgent retro + gate:retro-complete"
```

## 9. 합성 trail

- **Phase 0 4-agent burst** (2026-05-13 21:00 KST): DomainAgent (domain-knowledge 부재 surface) + ResearcherAgent (5 root cause 1차 진단) + RequirementsAnalystAgent (WHY + AC) + PMOAgent (3 Story 예비 분해)
- **Codex GPT-5 review** (2026-05-13 21:30 KST): 8 결정점 일괄 dispatch, 응답 (D1=D / D2=B / D3=A / D4=A / D5=A / D6=A / D7=A / D8=C) + R-EXTRA surface
- **Sonnet 합성** (2026-05-13): 사용자 final OK
- **PMOAgent 2nd pass** (2026-05-13 21:45 KST): 확정 설계 분해 → 3 Story sequential + scope_manifest 풍부
