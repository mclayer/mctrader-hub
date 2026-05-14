# RETRO-MCT-173 — upbit L1 backfill (frozen WAL historical materialization)

**dispatch**: PMOAgent (MCT-173 Phase 2 LAND 후 자동 dispatch)
**date**: 2026-05-14
**story_key**: MCT-173
**epic**: EPIC-data-accumulation-umbrella

## 요약

MCT-166 LAND 이후 frozen upbit orderbooksnapshot WAL → L1 parquet historical materialization 완료.
4 sub-phase (entry scan → runner extend → backfill 실행 → verify) 단계 분할 (D7=C) 방식으로 진행.
INV-5 (V2=0 AND 별 verify Fail=0) 양쪽 통과. EPIC-data-accumulation-umbrella 종료 후보 확정.

## Phase 타임라인

| Phase | 완료 시각 | 산출물 |
|---|---|---|
| Phase 1 | 2026-05-14 (MCT-173 trigger) | spec + plan + Story §1-§7 |
| Phase 2.1 (entry scan) | 2026-05-14 | WAL inventory audit 박제 (D2=C/D9=C) |
| Phase 2.2 (runner extend) | 2026-05-14 | backfill.py + runner run_backfill() + 4 TDD test |
| Phase 2.3 (backfill 실행) | 2026-05-14T04:36 UTC | 76 segments processed, total L1=1,960 |
| Phase 2.4 (verify) | 2026-05-14T04:49 UTC | V2=0 PASS, INV-5 PASS |
| Phase 2 hub | 2026-05-14 | Story §8-§12 + channel matrix + RETRO |

## 결과

| 항목 | 값 |
|---|---|
| mctrader-data PR | #57 (MERGED, 30e67518) |
| mctrader-hub PR | Phase 2 (진행 중) |
| Total L1 parquets | 1,960 (2026-05-13: 915 / 2026-05-14: 1,045) |
| Total L1 rows | 106,883,580 |
| AC 달성 | AC-1 ~ AC-7 전부 PASS |
| INV-5 PASS | True (V2=0, Fail=0) |

## 발생 FIX 이슈

| # | 유형 | 내용 | 해결 |
|---|---|---|---|
| F1 | CI lint (ubuntu) | pre-existing scripts lint errors (MCT-164/166 era) | ruff fix + push |
| F2 | CLI path 문제 | `--root` 옵션이 Windows Git bash path로 해석 | Python API 직접 호출로 우회 |

## 잘된 점

1. **D4=A sentinel idempotency**: 실시간 compactor와 backfill 충돌 없음 — 선처리된 segments는 자동 skip.
2. **D7=C 단계 분할**: entry scan → runner extend → 실행 → verify 4단계 분리로 실측 결과 기반 설계 가능.
3. **TDD 4 test**: iter / idempotency / manifest / schema 미리 작성 → 구현 후 즉시 검증.
4. **INV-5 verify gate**: V2=0 AND 별 verify Fail=0 양쪽 필수 — defense in depth (D8=C).

## 개선점

1. **CLI `--root` path 해석**: Windows Git bash 에서 Docker volume 경로가 오작동 → Python API 직접 호출 fallback 문서화 필요.
2. **pre-existing lint**: MCT-164/166 era 스크립트에 lint 오류 잔존 → 당시 CI에서 미검출 (scripts/ 경로가 lint 대상에 늦게 포함된 것으로 추정). 이후 scripts/ 추가 시 lint 대상 명시 필요.
3. **health module 부재**: 운영 컨테이너에 MCT-165 health framework가 미포함 (이미지 버전 불일치) → V2 verify를 inline 방식으로 대체.

## EPIC-data-accumulation-umbrella 종료 후보

MCT-164/165/166/173 ALL LAND 확인:
- MCT-164: WAL freeze + 진단 도구 (COMPLETED)
- MCT-165: health 4-layer framework (COMPLETED)
- MCT-166: upbit L1 fix — WAL freeze 해제 + orderbooksnapshot L1 활성화 (COMPLETED 2026-05-14)
- MCT-173: frozen WAL historical backfill (COMPLETED 2026-05-14)

**Epic 종료 후보 조건 충족**: umbrella 내 4 Story 모두 COMPLETED. Epic CLOSE 진행 가능.
