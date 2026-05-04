---
story_key: MCT-54
status: phase:요구사항
component: engine
type: brainstorm
parent_epic: MCT-48
related_adrs: ADR-006
---

# MCT-54: Promotion Evidence Bundle (ADR-006) — Epic close trigger

## 1. 사용자 요구사항 (verbatim, MCT-48 Epic Phase 1)

ADR-006 promotion gate (B→P→L) 의 P→L 측 evidence 자동 생성. "Paper run 이 promotable 인가" 의 명확한 boolean + reason list.

## 2. 도메인 해석

MCT-48 child #6 + Epic close trigger. MCT-23 의 Calibration metric (build_calibration_metrics) 이 dashboard 표시 만 되었던 약점 정정 — calibration 결과가 **promotion gate 의 mandatory input** 으로 격상.

Evidence bundle 생성기 = MCT-51 SQLite event store + MCT-52 RiskDecisionEvent / OperatorActionEvent 를 input 으로, ADR-006 thresholds 를 enforce 하여 단일 JSON deliverable 생성:

```json
{
  "run_id": "paper-sma-KRW-BTC-1h-5-20-2026-04-01",
  "evaluation_window": {"start_ts": "...", "end_ts": "...", "duration_days": 30},
  "trade_count": 102,
  "violation_count": 0,
  "calibration": {
    "fill_price_deviation_p95_bps": 12.3,
    "realized_slippage_p95_bps": 14.8,
    "decision_to_fill_delay_p95_ms": 850,
    "market_data_latency_p95_ms": 2400,
    "trade_count_delta_pct": 0.07,
    "max_drawdown_delta_abs": 0.018
  },
  "promotable": true,
  "blocking_reasons": []
}
```

`promotable: false` 의 경우 `blocking_reasons` 에 명시적 list (예: `["trade_count<100", "calibration.fill_price_deviation_p95_bps>=20", "violation_count>0"]`).

## 3. 관련 ADR

- **ADR-006 D7 amendment** (MCT-48 동반 amendment) — Paper Promotion Evidence Bundle 정의
- ADR-007 D9 (RiskPolicy hash unchanged) — bundle 의 risk_policy_hash 고정 verify

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── calibration/
│   ├── metric.py (READ — build_calibration_metrics, MCT-23)
│   └── evidence.py (NEW — build_evidence_bundle)
├── event_store/reader.py (MCT-51 reuse)
└── cli.py (MODIFY — `mctrader-cli paper evidence --run-id {id}` subcommand)

mctrader-hub/docs/
└── EPIC-RESULTS-MCT-48.md (NEW — Epic close 산출물)

mctrader-web/src/mctrader_web/dashboard/pages/
└── paper_panel.py (MODIFY — MCT-53 evidence 표시 section)
```

## 5-6. 요구사항

1. CLI: `mctrader-cli paper evidence --run-id {id} --output {path}` = evidence_bundle.json 생성. exit 0 (always, even if not promotable — 결정은 명시 field).
2. ADR-006 threshold:
   - `duration_days >= 30` OR `trade_count >= 100`
   - `violation_count == 0` (RiskDecisionEvent severity in {hard, critical} 의 count)
   - `calibration.fill_price_deviation_p95_bps < 20`
   - `calibration.realized_slippage_p95_bps < 15`
   - `calibration.decision_to_fill_delay_p95_ms < 1000`
   - `calibration.market_data_latency_p95_ms < 3000`
   - `calibration.trade_count_delta_pct <= 0.10`
   - `calibration.max_drawdown_delta_abs <= 0.02`
3. 모든 threshold AND → `promotable: true`. 하나라도 fail → `promotable: false` + blocking_reasons list.
4. risk_policy_hash 고정 verify: 평가 window 내 모든 RiskDecisionEvent 의 hash 가 동일. 변경 발견 시 promotable=false + reason="risk_policy_hash_changed".
5. Web 측 expose: MCT-53 paper_panel 에 "Evidence" expander 추가, FastAPI `/runs/{id}/evidence` (NEW endpoint, MCT-50 reuse) 통해 표시.
6. Test: promotable happy path / threshold 8건 각 fail / hash mismatch / event store empty (refuse).
7. Epic close: `EPIC-RESULTS-MCT-48.md` 작성 — Phase 1~5 PR list / Codex review aggregate / Sonnet decision log / **MCT-18 + MCT-23 retroactive scope acknowledgment** / 후속 candidate ranking 갱신 + 메모리 정정.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: evidence bundle = local file. PII 없음. Live key / KRW position 없음.
- 신규 file: `calibration/evidence.py` + `EPIC-RESULTS-MCT-48.md` + tests.
- 수정 file: `cli.py` (paper evidence subcommand), MCT-53 page.
- version bump engine 0.15.0 → 0.16.0.
- DB schema: 변경 없음 (event store reader reuse).
- Reversible: file revert + memory entry update.
