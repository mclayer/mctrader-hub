---
story: MCT-166
title: upbit L1 forward-only loss fix (channel mismatch 해소 + 선결 게이트)
date: 2026-05-14
brainstorm_skill: codeforge:brainstorm
phase_0_agents: [DomainAgent, ResearcherAgent, RequirementsAnalystAgent, PMOAgent]
phase_1_decider: codex (GPT-5.4) 합성 → Sonnet 채택
trigger: MCT-164 §10 진단 결과 channel mismatch 단일 확정 (Issue #295)
related_stories: [MCT-164 (진단 source), MCT-165 (verify framework), MCT-173 (backfill, D3=B 별 Story trigger)]
status: spec
---

# MCT-166 — upbit L1 forward-only loss fix Story

## 1. Why (사용자 동기)

사용자 원문: > "수행해"

MCT-164 ALL LAND 직후. INV-5 진단 → fix 인과 chain 강제.

### MCT-164 §10 진단 결과 인용 (필수, INV-5)

**Root cause 단일 확정 = (c) channel_mismatch**:
```python
# collector.py:82
if self._include_orderbook and self._exchange == "bithumb":
    ingesters["orderbookdepth"] = WalIngester(channel="orderbookdepth", ...)
```
upbit collector = orderbooksnapshot 만 emit → orderbookdepth WAL 없음 → L1 = 0.

**WAL 복구 verdict**: 부분 가능 (snapshot WAL → snapshot L1 직접 compaction 가능, snapshot → depth 변환 semantic loss 허용 시 가능).

### 근본 동기 (Phase 0 RequirementsAnalystAgent)

forward-only 손실 누적 차단 (WAL freeze 상태 = upbit 신규 수집 0, 정상 수집 부재) + frozen WAL 복구 + INV-5 진단 인용 의무.

## 2. Context 패킷 (Phase 0)

### DomainAgent
- exchange-channel-matrix.md MCT-166 fix 대상 명시 (upbit orderbookdepth 행 = "결함, Root Cause channel_mismatch")
- ADR-017 Amendment 2 변환 의무 + ADR-027 Amendment 2 fail-fast 정합 의무
- **upbit WebSocket orderbook_delta event 지원 여부 = 지식 공백** (외부 spec 조사 필수)

### ResearcherAgent
- **핵심 개념 3**:
  - Snapshot vs Delta semantic asymmetry (snapshot=stateful full-book / depth=stateless delta event)
  - Forward-only invariant temporal scope: frozen WAL replay = historical materialization ≠ backfill (Kafka log compaction 선례)
  - Allowlist as feature flag vs spec assertion drift (MCT-162 bithumb-only = incremental rollout flag 였으나 SSOT 부재로 spec assertion 으로 drift)
- **Unknowns 2**: upbit WS adapter orderbook_delta 미구현 시 fallback (synthetic-delta 변환 vs 신규 channel subscribe, CCXT pro pattern) / Compaction idempotency under partial WAL (Kafka KIP-98)
- **Recommendation**: primary 우선 (semantic preservation), upbit native delta 부재 확정 시에만 alternative escalate

### RequirementsAnalystAgent
- WHY: forward-only 손실 누적 차단 + INV-5 진단 인용
- 확장 3: 선결 조건 분기 명시 / backfill 포함 여부 결정 / ADR-027 Amendment 2 fail-fast 정합
- 10 ambiguity 영역 surface

### PMOAgent
- 1 Story + 선결 게이트 분기 (primary/alternative fundamentally different code surface)
- carry-over umbrella label only
- **risk**: §3 scope 사전 확정 불가, 선결 결과 박제 후 §3/§8/§8.5 amendment 의무

## 3. Phase 1 — 9 결정점 (Codex 합성 + Sonnet 채택)

| D | 결정 | 핵심 |
|---|---|---|
| **D1** | **B** | Phase 2 entry 즉시 선결 검증 (upbit WS adapter `orderbook_delta` 지원 여부 코드 read + 외부 공식 spec) |
| **D2** | **C** | primary vs alternative = 선결 결과 후 자율 결정 (primary 우선 권고이나 지식 공백) |
| **D3** | **B** | backfill 별 Story 분리 (MCT-173 후보, scope 통제, Researcher temporal scope 정합) |
| **D4** | **C** | collector + compactor 양쪽 fail-fast (defense in depth, ADR-027 Amendment 2 정합) |
| **D5** | **A** | channel matrix hypothesis → confirmed → 결함 → 정상 전이 박제 (INV-5 SSOT) |
| **D6** | **B** | 일반 Story flow + 당일 처리 (MCT-164 답습) |
| **D7** | **C** | 1 Story + 선결 게이트 분기 (PMO 권고) |
| **D8** | **A** | fix LAND 즉시 WAL freeze 해제 (verify 후 자동) |
| **D9** | **C** | MCT-165 health framework 재실행 + 별 verify 스크립트 (defense in depth) |

## 4. Acceptance Criteria (7 개, PMOAgent 2nd pass)

- **AC-1 (선결 게이트)**: Given Phase 2 entry, When upbit WS adapter `orderbook_delta` 지원 여부 확인, Then 결과 박제 + primary/alternative path 결정
- **AC-2 (fix LAND)**: Given fix 구현 완료, When `python -m mctrader_data.collector` 30 분 실행, Then `data/L1/exchange=upbit/symbol=*/date=2026-05-14/*.parquet` ≥ 1 partition 생성
- **AC-3 (health verdict)**: Given fix LAND 후, When `data_health_check --tier L1 --exchange upbit` 실행, Then V2 (forward-only loss) verdict 0 건
- **AC-4 (collector fail-fast)**: Given allowlist 에 unsupported (exchange, channel) 조합 추가, When collector boot, Then ValueError raise + `collector_unsupported_channel_total` +1
- **AC-5 (compactor fail-fast)**: Given L1 compactor source discovery 시 unsupported channel, When compactor 실행, Then fail-fast + `compactor_unsupported_source_total{tier,exchange,channel}` +1
- **AC-6 (WAL freeze 해제)**: Given AC-2 + AC-3 green, When verify 스크립트 실행, Then WAL freeze flag (`data/.wal-freeze/upbit-L1`) 자동 제거
- **AC-7 (channel matrix 정합)**: Given fix LAND, When `exchange-channel-matrix.md` read, Then upbit orderbookdepth 행 = "정상" + INV-5 전이 박제

## 5. Invariant (5 개)

- **INV-1**: ADR-027 Amendment 2 fail-fast — collector + compactor 양쪽 unsupported channel/exchange 조합 silent-skip 금지
- **INV-2**: ADR-009 nullability discipline — channel matrix dispatch 분기 시 None branch 명시 (ADR-017 Amendment 2)
- **INV-3**: forward-only history 보존 — backfill 미수행 (MCT-173 별 Story), 본 Story 는 t≥fix-LAND 시점부터만 누적
- **INV-4**: WAL freeze SSOT — freeze 해제 trigger = verify 스크립트 단일 경로 (수동 rm 금지)
- **INV-5**: channel matrix 상태 전이 박제 — hypothesis → confirmed → 결함 → 정상 4 단계 SSOT (D5=A)

## 6. Risk (3 개)

- **R1 (High)**: upbit WS `orderbook_delta` 미지원 → primary path 불가, alternative path (compactor 분기) 만 가능. 영향: D2 결정 의존, AC-2 partition 생성 경로 변경. **완화**: D1=B Phase 2 entry 선결 + D7=C 게이트 분기로 명시
- **R2 (Mid)**: compactor source discovery 변경이 기존 binance/bybit L1 partition 회귀 유발. 영향: 회귀 테스트 필수, ADR-017 Amendment 2 정합 검증. **완화**: §8 Test Contract 회귀 테스트 의무 + 단위 + 통합 양쪽
- **R3 (Low)**: MCT-165 health framework 재실행 시 V2 외 verdict (V1/V3) 동시 검출 → 본 Story scope 외 발견 → MCT-174+ 별 Story trigger 가능성. **완화**: §10 FIX Ledger surface only, 별 Story 발의

## 7. Phase 분할

| Phase | 산출물 | wall-clock | PR |
|---|---|---|---|
| Phase 1 | spec + plan + Story file §1-§7 + counters title 확장 + MCT-173 reservation | 즉시 | mctrader-hub Phase 1 PR |
| Phase 2.1 (선결 게이트) | upbit WS adapter orderbook_delta 지원 여부 검증 + 결과 박제 | 즉시 | mctrader-data Phase 2 PR (선결 commit) |
| Phase 2.2 (fix) | primary OR alternative path 구현 + 단위/통합 테스트 + fail-fast (collector + compactor) | 즉시 | mctrader-data Phase 2 PR (fix commit) |
| Phase 2.3 (verify + freeze 해제) | MCT-165 health framework 재실행 + 별 verify 스크립트 + WAL freeze 해제 | 즉시 | mctrader-data Phase 2 PR (verify commit) |
| Phase 2 hub | 결과 박제 + channel matrix update (결함→정상) + Story §8-§12 + CLAUDE.md + RETRO | 즉시 (당일) | mctrader-hub Phase 2 PR |
| MCT-173 trigger | backfill Story brainstorm 진입 (D3=B 별 Story) | 별 세션 (본 Story 종료 후) | MCT-173 Phase 1 PR (별 발의) |

## 8. scope_manifest 초안 (PMOAgent 2nd pass)

```yaml
planned_adrs:
  amendment: []  # 본 Story 는 ADR-017/027 Amendment 2 정합 검증 의무만, 추가 amendment 없음
  reservation_only: []

planned_files:
  mctrader-data:
    - src/mctrader_data/collector.py: L82 조건 제거 또는 channel matrix dispatch
    - src/mctrader_data/ingesters/upbit_orderbookdepth.py: primary path 시 신규 ingester (선결 결과 의존)
    - src/mctrader_data/compactor/l1.py: alternative path 시 orderbooksnapshot source 분기 활성화 + fail-fast
    - src/mctrader_data/allowlist.py: unsupported channel/exchange ValueError (collector level fail-fast)
    - src/mctrader_data/metrics.py: compactor_unsupported_source_total + collector_unsupported_channel_total Counter 신규
    - scripts/verify_upbit_l1_fix.py: WAL freeze 해제 + partition 존재 verify 스크립트
    - scripts/upbit_ws_capability_probe.py: 선결 검증 — orderbook_delta event 지원 여부 코드 read + 외부 spec 확인
    - tests/unit/test_collector_l1_dispatch.py: 단위 — channel matrix dispatch + fail-fast
    - tests/integration/test_upbit_l1_partition.py: 통합 — 30 분 collector → partition 생성
    - tests/integration/test_compactor_fail_fast.py: 통합 — unsupported source ValueError + Prometheus
    - docs/audit/MCT-166-precondition-upbit-ws-capability.md: 선결 결과 박제 (D1=B)
    - CLAUDE.md: upbit L1 status + channel matrix dispatch 갱신

  mctrader-hub:
    - docs/stories/MCT-166.md: Story file §1-§12
    - docs/superpowers/specs/2026-05-14-MCT-166-upbit-l1-fix-design.md: spec
    - docs/superpowers/plans/2026-05-14-mct-166-upbit-l1-fix.md: plan
    - docs/domain-knowledge/domain/data-health/exchange-channel-matrix.md: upbit orderbookdepth 결함→정상 전이 박제 (INV-5)
    - docs/retros/RETRO-MCT-166.md: PMO retro
    - CLAUDE.md: §upbit L1 status + §WAL freeze flags + §pending stories (MCT-173)
    - .codeforge/counters.json: MCT-166 title 확장 + MCT-173 reservation (next 173→174)

planned_claude_md_sections:
  - mctrader-hub/CLAUDE.md §upbit L1 status (forward-only loss 해소 2026-05-14)
  - mctrader-hub/CLAUDE.md §WAL freeze flags > upbit-L1 해제 (MCT-166 LAND)
  - mctrader-hub/CLAUDE.md §pending stories > MCT-173 (upbit L1 backfill, D3=B)

counters_reservation:
  current: MCT-166  # title 확장 박제분
  next_reservation: MCT-173  # backfill Story (D3=B), Phase 2 종료 시 Issue 발의
```

## 9. Cross-ref

- **MCT-164 §10** (진단 결과 SSOT, INV-5 인용 의무)
- **MCT-165 V2** (verify trigger source — fix 후 V2 잔존 NO 의무 AC-3)
- **MCT-162** (channel parity Story, bithumb-only allowlist 원인 source)
- **MCT-173** (backfill Story, D3=B 별 Story trigger, 본 Phase 1 PR 에서 reservation)
- **ADR-017 Amendment 2** (compactor source 규약 + channel matrix SSOT, INV-2 정합)
- **ADR-027 Amendment 2** (미지원 source silent-skip 차단, INV-1 정합)
- **ADR-009 §D12** (forward-only invariant, INV-3 정합)
- **Issue #295** (MCT-166 trigger, 본 Story Phase 2 close)

## 10. Open Question Resolution (Sonnet decider 채택)

- **OQ-1 → 선결 게이트 timing**: D1=B Phase 2 entry 즉시 (Phase 1 PR 시점에는 코드 read 미진행, MCT-164 패턴 답습 = Phase 1 docs only)
- **OQ-2 → primary path 선결 미지원 시 fallback**: D2=C 자율 결정 — Researcher 권고 alternative escalate (compactor 분기 활성화, ADR-017 Amendment 2 channel matrix dispatch)
- **OQ-3 → backfill scope**: D3=B 별 Story (MCT-173) — forward-only invariant temporal scope (Researcher) + scope 통제 우선

## 11. Phase 2 진입 시 별도 의무

- mctrader-data Phase 2 PR open 시 첫 commit = 선결 검증 스크립트 + 결과 박제 (D1=B)
- 선결 결과에 따라 §3 / §8 / §8.5 amendment (Story file 본문 update)
- WAL freeze 해제 = verify (AC-2 + AC-3) green 후 자동 (수동 rm 금지 INV-4)
- PMOAgent retro 자동 dispatch (memory feedback_pmo_retro_mandatory)
- MCT-173 backfill Issue 발의 (별 세션 brainstorm trigger)
