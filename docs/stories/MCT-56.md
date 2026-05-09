---
story_key: MCT-56
status: closed
closed_at: 2026-05-05
component: engine
type: brainstorm
parent_epic: MCT-55
related_adrs: ADR-005, ADR-006
results_doc: EPIC-RESULTS-MCT-55.md
---

# MCT-56: Foundation — SplitRegistry + AuditLog + run_manifest + decision_group lifecycle + L4 skeleton

## 1. 사용자 요구사항 (verbatim, MCT-55 Epic Phase 1)

ADR-006 D5 / D10 / amendment §D5 / §D10 의 immutable schema + lifecycle. 모든 후속 Story (search / evaluate / correction / L4 sealing / web / promote) 의 ground.

## 2. 도메인 해석

MCT-55 child #1 = serialized first. Codex push-back: "MCT-56 must define immutable schemas, lifecycle, event types, search_space_hash, and contamination semantics before MCT-57 starts producing selectable candidates."

본 Story 종료 시 사용자가 다음 single command 로 decision_group 생성 가능:

```
mctrader-cli wfo decision-group create \
  --strategy-family sma \
  --symbol KRW-BTC \
  --timeframe 1h \
  --train-days 180 --val-days 30 --oos-days 30 --embargo-days 5
```

→ `~/.mctrader/wfo/decision_groups/{registry_hash}/` 에 immutable JSON + audit log JSONL 저장.

L4 fixture skeleton = `selected_param_hash` ↔ OOS-evaluated candidate lineage detection point 을 코드에 정의 (실제 fail-injection 은 MCT-60 에서 sealing).

## 3. 관련 ADR

- ADR-005 D5 (UI partial bar diagnostic label) / L4 (lineage check fixture mechanism)
- ADR-006 D5 (OOS governance, 8 audit event 종) / D10 (run manifest 31-field) / amendment §D5 (content-addressable storage) / amendment §D10 (`promotion_gate_version` default freeze)

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader_engine/
├── wfo/                      (NEW module)
│   ├── __init__.py
│   ├── registry.py           (SplitRegistry frozen dataclass + Pydantic v2)
│   ├── audit.py              (AuditEvent 8종 + JSONL append-only writer)
│   ├── manifest.py           (RunManifest 31-field)
│   ├── decision_group.py     (lifecycle: create / freeze / list)
│   ├── lineage.py            (search_space_hash + selected_param_hash + L4 skeleton)
│   └── cli.py                (wfo group + decision-group subcommand)
├── cli.py                    (MODIFY — main.add_command(wfo))
└── lookahead/
    └── patterns/
        └── oos_selection_loop.py  (NEW skeleton, fail-injection 점 정의 only)
```

## 5-6. 요구사항

1. `SplitRegistry` Pydantic v2 frozen + content-addressable hash dir 저장 (B4): `~/.mctrader/wfo/decision_groups/{registry_hash}/registry.json`. `registry_hash` = sha256(canonical_json(model_dump_json + sort_keys + compact separators)).
2. `RunManifest` 31-field schema (D10) Pydantic v2 frozen. `promotion_gate_version` default = "v1.0" freeze (amendment §D10).
3. `AuditEvent` 8종 (D5): `split_registry_created` / `fold_materialized` / `train|validation|oos_segment_read` / `candidate_generated` / `candidate_selected` / `oos_evaluated` / `promotion_decision_created`. JSONL append-only writer + `audit_log.jsonl` per decision_group.
4. `decision_group` lifecycle (L3): manual `wfo decision-group create` 의무 + auto-create fail-fast (search 진입 시 decision_group 미존재 → exit 1 with "no decision_group, run create first").
5. `search_space_hash` 계산 (D10) — strategy_family + symbol_universe + timeframe + parameter ranges + budget 등 frozen 직렬화 hash.
6. L4 fixture skeleton — `mctrader_engine/lookahead/patterns/oos_selection_loop.py` 에 `selected_param_hash` ↔ `oos_segment_read` lineage detection point 코드 도입 (실제 fail trigger 는 MCT-60). lookahead-lint 가 import 가능.
7. CLI: `mctrader-cli wfo decision-group create` + `wfo decision-group list` + `wfo decision-group show {hash}` 3 subcommand.
8. Unit test: registry hash determinism / manifest schema strict validate / audit log append-only / decision_group fail-fast / L4 skeleton import.
9. CI: mctrader-engine lint + pyright strict + pytest pass.

## 7. 보안 설계 / 11. 데이터 영향

- 보안: registry / audit log / manifest = file-only (`~/.mctrader/wfo/`). 파일 권한 = 700 (MCT-48 의 `~/.mctrader/` 정책 일관).
- 신규 file: `wfo/` 모듈 6 file + tests/test_wfo_registry.py / test_wfo_audit.py / test_wfo_manifest.py / test_wfo_decision_group.py + `lookahead/patterns/oos_selection_loop.py` skeleton.
- 수정 file: `cli.py` (wfo group 추가), version bump engine 0.16.0 → 0.17.0.
- DB schema: 변경 없음 (JSONL append-only file).
- Reversible: yes.
