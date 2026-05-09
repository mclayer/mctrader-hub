---
story_key: MCT-60
status: closed
closed_at: 2026-05-05
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-005, ADR-006
results_doc: docs/retros/EPIC-RESULTS-MCT-55.md
---

# MCT-60: L4 fixture sealing — `oos_selection_loop` lineage check + Lookahead lint integration

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-005 L4 fixture (MCT-37 carry-forward, "oos_selection_loop = MCT-6 dependency 분리") + ADR-006 D5 OOS contamination 방어. Codex push-back: "K2/K3 are unacceptable. MCT-60 must land before any Epic-close claim. The oos_selection_loop test should be introduced with MCT-56 and made to fail until MCT-57/MCT-58 integration proves D5 enforcement."

## 2. 도메인 해석

MCT-55 child #5. MCT-56 에서 skeleton 도입된 L4 fixture 를 본격 sealing — `selected_param_hash` ↔ `oos_segment_read` lineage check 로 fail-injection.

핵심 invariant: "OOS read 후 같은 decision group 내 selection event 발생 = violation. selected_param_hash lineage 가 OOS-evaluated candidate 와 연결 시 fail" (ADR-006 §D5).

본 Story 종료 시:
- `mctrader-cli lookahead-lint` 가 `oos_selection_loop` pattern 추가 detect.
- CI 에 fail-injection fixture 통과 (의도적 contamination 패턴 → lint detect → exit 1 검증).

## 3. 관련 ADR

- ADR-005 L4 (lineage check fixture mechanism) / ADR-006 D5 (OOS governance, contamination 정의)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── lookahead/
│   ├── patterns/
│   │   └── oos_selection_loop.py  (MODIFY — skeleton → real lineage check)
│   ├── audit/
│   │   └── lineage.py             (audit log JSONL parser)
│   └── cli.py                     (MODIFY — pattern registry 추가)
└── wfo/
    └── lineage.py                 (MODIFY — search_space_hash + selected_param_hash lineage finalize)

tests/
├── test_lookahead_oos_selection_loop.py
└── fixtures/
    ├── oos_clean_audit.jsonl       (정상 audit log, lint pass)
    └── oos_contaminated_audit.jsonl (의도적 contamination, lint detect)
```

## 5-6. 요구사항

1. `oos_selection_loop.py` body 본격 구현 — audit log JSONL parse → `oos_segment_read` event timestamp 와 `candidate_selected` event timestamp 비교 → 동일 decision_group 내 read 가 select 이전이면 violation.
2. `selected_param_hash` lineage check — selected param 의 hash 가 `oos_evaluated` event 의 candidate_hash 집합과 일치 시 violation (selection 이 OOS 결과 본 후 결정됨).
3. Lookahead lint integration — `mctrader-cli lookahead-lint --pattern oos_selection_loop` 가 audit log JSONL 입력 받아 detect.
4. Promotion gate hook — `error_count == 0 AND expired_count == 0` 조건 (ADR-005 L1 baseline) 에 본 pattern 추가. fail 시 promotion gate D6 결과 무관 promotable=false 강제.
5. CI fail-injection fixture — `oos_clean_audit.jsonl` (lint pass) + `oos_contaminated_audit.jsonl` (lint exit 1) 양쪽 CI 검증.
6. Unit test: clean lineage / contaminated lineage / mixed scenarios / large audit log scaling.
7. CI green.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: audit log read-only parse.
- 신규 file: `lookahead/audit/lineage.py` + tests + fixtures (2 jsonl).
- 수정 file: `lookahead/patterns/oos_selection_loop.py` (skeleton → impl) + `lookahead/cli.py` pattern registry + `wfo/lineage.py` finalize. version bump engine 0.20.0 → 0.21.0.
- Reversible: yes.
