---
story_key: MCT-92
story_issues:
  - repo: mclayer/mctrader-hub
    number: 97
status: phase:요구사항
---

# MCT-92: Collector HA — Scan-side Merge + Dedup (X3 of MCT-89)

- **Issue**: #97
- **Status**: phase:요구사항

## 1. 사용자 요구사항 (verbatim — Phase 2 후속 CFP 까지 CODEOWNERS manual review 로 변경 차단)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: mctrader-data 측 scan-side merge + dedup. 부모 Epic = MCT-89. X2 (MCT-91, mctrader-data 0.6.0 main merged) 의 후속. Phase 1 spec/plan 의 X3 = `scan_*` multi-node union + tier 별 logical key dedup + `dedup.py` 신규 module + quarantine `active-active mismatch` reason. ADR-009 §D2.1 mixed legacy 영구 지원 enforce + §D10.7 T2 6-tuple + §D11.8 T3 8-tuple best-effort dedup target T2>99% / T3>95%. X2-X3 window 운영 caveat 해소 의무 — recursive partition glob `**/node=*/**/*.parquet` + legacy partition `node=DEFAULT` mapping + 양 file naming `part-*.parquet` / `{collector_run_id}-{batch_seq}.parquet` 호환.)

## 2. 도메인 해석

*(DomainAgent 작성 예정 — placeholder)*

## 3. 관련 ADR

*(RequirementsPL 작성 예정 — placeholder)*

## 4. 관련 코드 경로

*(RequirementsPL 작성 예정 — placeholder)*

## 5. 요구사항 확장 해석

*(RequirementsAnalyst 작성 예정 — placeholder)*

## 6. 외부 지식 배경

*(Researcher 작성 예정 — placeholder)*

## 7. 설계 서사

*(Architect 작성 예정 — placeholder)*

## 8. 개발 서사

*(DeveloperPL 작성 예정 — Phase 2 PR에서)*

## 9. 품질 게이트 이력

*(Review/Test PL 작성 예정 — Phase 2 PR에서)*

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

*(FIX 발생 시 append)*

## 11. 회고

*(PMOAgent 작성 예정 — Story 완료 시)*
