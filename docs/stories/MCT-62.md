---
story_key: MCT-62
status: closed
closed_at: 2026-05-05
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-006
results_doc: EPIC-RESULTS-MCT-55.md
---

# MCT-62: Promotion CLI + Epic close — `mctrader-cli wfo promote` + EPIC-RESULTS-MCT-55

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-006 D6 결과 + D8 multiple testing 결과 + L4 fixture pass + (web ack OR CLI ack) → `promotion_decision.json` 작성. I2 manual ack 의무 (operator override 금지 = ADR-006 §D7 amendment 의 P→L 측 stance 와 동일 line 의 B→P 측 적용).

## 2. 도메인 해석

MCT-55 child #7 = Epic close trigger. MCT-58 (gate D6) + MCT-60 (L4 fixture) + MCT-61 (web ack parity) 모두 의존. CLI 와 web ack 가 동일 결과 (parity).

본 Story 종료 시:
1. `mctrader-cli wfo promote --decision-group X --ack "promote sma KRW-BTC 1h to paper, gate passed 12/12 + L4 clean"` 실행
2. `~/.mctrader/wfo/decision_groups/{hash}/promotion_decision.json` 생성:
   ```json
   {
     "decision_group_hash": "...",
     "promotable": true,
     "blocking_reasons": [],
     "gate_d6_passed": true,
     "gate_d6_failed_metrics": [],
     "l4_fixture_clean": true,
     "deflated_sharpe_significant": true,
     "operator_ack_text": "...",
     "operator_ack_ts": "...",
     "promotion_gate_version": "v1.0"
   }
   ```
3. `promotion_decision_created` audit event emit
4. EPIC-RESULTS-MCT-55.md 작성 (MCT-12/18/25/32/37/48 패턴, 모든 child Story merge SHA + Sonnet 자율 결정 + 후속 candidate 우선순위)

## 3. 관련 ADR

- ADR-006 D6 (B→P promotion gate) / D8 (multiple testing) / amendment §D5 / §D10 / §D11 (3 amendment 모두 본 Story 까지 enforce)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/wfo/
├── promote/                  (NEW submodule)
│   ├── __init__.py
│   ├── decision.py           (PromotionDecision Pydantic v2)
│   └── ack.py                (operator ack parser + audit event)
└── cli.py                    (MODIFY — wfo promote subcommand)

mctrader-web/src/mctrader_web/api/
└── wfo.py                    (MCT-61 의 POST /wfo/promote 가 본 Story 의 ack.py 호출)

mctrader-hub/docs/results/
└── EPIC-RESULTS-MCT-55.md    (NEW)
```

## 5-6. 요구사항

1. `PromotionDecision` Pydantic v2 frozen — 9 field (decision_group_hash / promotable / blocking_reasons / gate_d6_passed / gate_d6_failed_metrics / l4_fixture_clean / deflated_sharpe_significant / operator_ack_text / operator_ack_ts / promotion_gate_version).
2. `mctrader-cli wfo promote --decision-group X --ack TEXT` (CLI):
   - decision_group fold_report.json + L4 fixture result + correction result load
   - gate D6 + L4 + deflated Sharpe 모두 통과 시 `promotable=true`, 하나라도 fail 시 `promotable=false` + blocking_reasons populated
   - ack TEXT 미제공 시 stdin prompt (interactive only, --ack flag 권장)
   - operator override 금지 — `promotable=false` 일 때 ack 입력해도 `promotable=true` 로 변경 불가 (코드 가드 함수)
3. `promotion_decision_created` audit event emit + `~/.mctrader/wfo/decision_groups/{hash}/promotion_decision.json` save.
4. web parity — MCT-61 의 `POST /wfo/promote` 가 본 Story 의 동일 `ack.py:apply_ack()` 호출. CLI 와 web 결과 동일 (parity test 의무).
5. EPIC-RESULTS-MCT-55.md 작성:
   - 7 child Story merge SHA 표
   - Codex 7-area review aggregate (16 design decisions × 2 phases — Phase 1 + per-Story Phase 2 brainstorm)
   - Sonnet 자율 결정 핵심 list
   - 후속 candidate 우선순위 (Live mode prerequisite 충족 명시)
   - 사용자 stop count
6. memory `project_mctrader.md` finalize section 추가 (MCT-12/18/25/32/37/48 패턴).
7. Unit test: PromotionDecision strict / operator override 금지 가드 / CLI vs web ack parity (동일 input → 동일 output).
8. CI green.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: ack text = operator 책임 기록, audit log append-only.
- 신규 file: `wfo/promote/` 3 file + tests + EPIC-RESULTS-MCT-55.md.
- 수정 file: `cli.py` wfo promote, version bump engine 0.21.0 (MCT-60 또는 MCT-61 에서 이미 도달).
- Reversible: yes (Phase 5 EPIC-RESULTS 는 doc-only, file revert 충분).
