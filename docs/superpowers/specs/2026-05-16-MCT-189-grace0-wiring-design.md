# MCT-189 Design Spec — ADR-029 §D3=C grace-0 로컬삭제 wiring 완결

> **Brainstorm 산출물** (codeforge-brainstorm Phase 0 4 agent burst + Codex 10 decisions + 사용자 D-3 정정 + PMO 2nd pass).
> **단일 Story** (사용자 D-3 = C). **4 PR 다단** (Phase 1 docs + Phase 2 PR1 wiring + Phase 2 PR2 legacy cleanup + Phase 2 PR3 박제).
> **Epic** = EPIC-tier-promotion-single-source carry over (POLICY_FINALIZED 유지, D3 wiring deferred → MCT-189 resolved).

## §0 Phase 0 Verify Evidence

본 spec 의 모든 코드 인용은 다음 절차로 사전 verify 됐다 (memory `feedback_phase0_verify_mandatory` 누적 lesson 7회째 — MCT-170/177/178/179/180/182/MCT-189):

| 항목 | verified-via | 결과 |
|------|-------------|------|
| `promote_l1()` 정의 존재 | Read `c:\workspace\mclayer\mctrader-data\src\mctrader_data\compactor\promotion.py:95` | ✅ 정의 완비 (HEAD verify + grace 0 unlink, INV-1~6) |
| `promote_l1()` production caller | `git grep -nE "promote_l1\(|from mctrader_data\.compactor\.promotion import"` src/** | ❌ **0건** (f233952 + HEAD main 동일) |
| `dual_writer.py` source unlink | Read `dual_writer.py:186/197/218/230/248/258` | ❌ 모두 `tmp_path` (atomic write 임시파일) — source local 삭제 0건 |
| `l1.py`/`l2.py`/`l3.py` tier promotion source 삭제 | Read `l1.py:478` / `l2.py:133,233` / `l3.py:131,228` | ❌ 모두 tmp_path exception path |
| `nas_uploader.head_object()` primitive | Read `nas_uploader.py:309,404` | ✅ 존재 (현재 ETag + VersionId 반환, sha256 metadata + ContentLength 추가 필요 — D-4 C) |
| production NAS 적재 상태 | `mctrader-compactor` 로그 `[nas_uploader] uploaded ... etag=... bytes=...` + `idempotent skip ...` | ✅ 정상 (192.168.50.200 prod NAS, retry_queue.sqlite 2.9 MB) |
| ADR-029 §D3 본문 표현 | Read `docs/adr/ADR-029-tier-promotion-single-source.md:240-249` + L347 + L352 | ⚠️ 3-way 모순 (line 240 헤더 grace 0 vs line 246 terminal 7-day FIFO + 20G hard vs line 347 표 "7-day grace 기본") |
| 운영 영향 | `docker run --rm -v mctrader_data:/d alpine du -sh /d/*` | /d/market 130.8 GB + /d/wal 38 GB (총 168.9 GB) — 2026-05-15 이후 신규 market parquet 0건, 대부분 5월 초·중순 backfill 산물 |
| ingest_blocker + capacity_probe LANDed | `curl http://localhost:8080/metrics \| grep capacity` (본 세션 응급 재배포 후) | ✅ `mctrader_capacity_usage_bytes` + `mctrader_capacity_threshold_ratio` + `mctrader_ingest_blocked_total` Gauge/Counter 노출 |

## §1 동기

2026-05-16 사용자 운영 진단 ("로컬 디스크 용량이 계속 차고 있는데 S3에 데이터 제대로 적재되고 있는가") 결과:

- **S3(NAS) 적재 자체는 정상**: `mcnas01.internal.mclayer.it:9000` (192.168.50.200) bucket `mctrader-market`, 업로드 + idempotent skip + retry queue 백로그 0 근사.
- **디스크 압박 원인**: ADR-029 §D3=C "Local delete = NAS HEAD verify + grace 0" 정책의 코드 wiring 부재. `promote_l1()` 함수는 정의됐으나 production caller = 0건. DualWriter는 NAS PUT commit 후 source local 삭제 안 함. 결과 `/d/market` 130 GB 영구 누적.
- **EPIC-tier-promotion-single-source POLICY_FINALIZED 2026-05-14 박제** vs **production 코드 wiring 부재** = **cross-document SSOT drift 2호** (1호 = mctrader-data:pilot 2026-05-13 이미지가 정책 LAND 하루 전 빌드, 본 세션 응급 재배포로 capacity_probe + ingest_blocker만 LAND).

PMO retro `docs/retros/PMO-PATTERNS-2026-05-16-ssot-drift-operational-vs-design.md` 박제: 본 drift 양건이 MCT-179 (Out-of-scope reconcile) + MCT-182 (cross-document SSOT forcing function) lesson의 3번째 재현 사례. ADR-032 "VERIFIED badge evidence triad" Proposed reservation.

사용자 결정 발화 ("Story 발의: promote_l1 wiring 코드 수정") = long-term sustainable code fix 선호. 일회성 cleanup script 거부.

## §2 4-Layer / Decision Space

본 Story는 ADR-029 §D3=C policy를 실 production wiring으로 매핑. 핵심 decision space:

1. **Local delete timing 정합** (ADR-029 §D3 line 240/246/347 모순 해소) — grace 0 unconditional vs 7d FIFO + 20G hard vs hybrid
2. **책임 위치** — DualWriter self-delete vs caller (l1/l2/l3/runner) explicit `promote_l1()` 호출
3. **Legacy 130 GB scope** — 본 Story 통합 vs MCT-190 별 Story vs hybrid (단일 Story + 다단 PR)
4. **HEAD verify primitive 강도** — ETag만 vs ETag+VersionId+sha256 vs 4중 (+ContentLength)
5. **backup/PITR window** — forward-only invariant 격상 vs `_legacy_pre_wiring` archive vs local fallback 7-30d
6. **ambiguity strict scope** — post-LAND production 0 violation vs integration test only vs cleanup 완료 후 strict
7. **concurrent delete race** — idempotent (ENOENT graceful) vs file lock
8. **NAS partition mid-delete safety** — guard 없음 vs pre-delete HEAD 재확인 vs pre+post 2회
9. **domain-knowledge 페이지** — 본 Story scope vs 별 follow-up vs skip
10. **ADR-032 evidence triad와의 관계** — 동시 Accept vs 별 governance Story vs 보류

## §3 채택된 10 결정점 (Codex 권고 + 사용자 D-3 정정)

| D | 채택 | 근거 (1줄) | 주요 trade-off |
|---|------|-----------|----------------|
| **D-1** | **A** grace 0 unconditional | ADR-029 §D3 line 240/246/347 3-way 모순을 사용자 발화("grace-0 wiring 완결")대로 grace 0 일관 amend (promotion + terminal 모든 path). | local fallback window 포기 → NAS verify primitive 신뢰도가 중요 (D-4로 강화) |
| **D-2** | **A** DualWriter self-delete | NAS PUT commit boundary 안에서 source unlink → caller 0건 재발 차단. | DualWriter 책임 범위 확대 (write + retention), 단 solo dev 환경 지속가능성 우선 |
| **D-3** | **C** (사용자) | 단일 Story MCT-189 + LAND 후 별 PR cleanup (Story 분리 없이). | Story key 절약 + 같은 retro/spec/plan + production rollback 시 PR2 만 revert 가능 |
| **D-4** | **C** 4중 verify (ETag + VersionId + sha256 metadata + ContentLength) | grace 0 = HEAD verify가 유일 안전망 → silent corruption 차단 강화. | head_object response 처리 코드 증가, legacy metadata 부재 partition fallback 필요 |
| **D-5** | **A** forward-only invariant 격상 | NAS versioning 30d window = PITR. host 200G hard limit + MCT-170 D8=B local fallback sunset (2026-09-01) 정합. | 즉시 복구 편의 상실, 보존 책임 NAS+versioning 단일화 |
| **D-6** | **A** post-LAND production 14d 0 violation | caller 0건 재발 방지 (cross-document SSOT drift 패턴 차단) — ADR-032 evidence triad 형식 차용. | LAND 기준 강화 → 14d 측정 작업 필요 |
| **D-7** | **A** idempotent (ENOENT graceful) | promotion.py INV-6 (already_promoted no-op) 이미 LAND — DualWriter self-delete missing_ok=True 통일. | 중복 시도 로그 노이즈 (lock 의존 회피) |
| **D-8** | **B** pre-delete HEAD ETag+ContentLength 재확인 | HEAD verify와 unlink 사이 race window — silent corruption 차단. | NAS request 수 +1/PUT (latency 영향 微), post-delete HEAD까지 강제 비용 회피 |
| **D-9** | **A** `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` 신규 | ADR 모순이 domain policy 해석 문제였음 — 같은 논쟁 차단. | Story scope 확장 (문서 산출물 추가) |
| **D-10** | **B** ADR-032 별 governance Story 발의 | MCT-189 = wiring 집중. ADR-032 evidence triad 일반화는 별 Story (PMO 권고 key = MCT-190). | ADR-032 제도화 지연, 단 MCT-189가 첫 evidence triad 적용 사례 (Story §8.5 박제) |

### 채택 결정 cross-ref ADR-029 amendment

- **§D3 line 240/246/347 → grace 0 일관 amend** (D-1 A)
- **§D10 line 333 → production evidence gate 강화** (D-6 A, ADR-032 형식 차용)
- **Migration §Forward-only invariant line 363 → local fallback 제거 명시** (D-5 A)
- **§D11 표 line 347 → "7-day grace 기본" 표현 정정** ("L1 ParquetWriter atomic 후 NAS PUT commit 직후 grace 0 unlink")

## §4 Scope — 4 PR Land Order

| land_order | PR | repo | 내용 핵심 | depends_on |
|------------|-----|------|----------|------------|
| **1** | Phase 1 docs | mctrader-hub | Story §3 본설계 + §7 Test Contract + spec/plan 신규 + ADR-029 §D3 amendment box draft + domain-knowledge 신규 + CLAUDE.md MCT-189 entry + scope_manifest update | — |
| **2** | Phase 2 PR1 wiring | mctrader-data | `nas_uploader.head_object()` 4중 verify 확장 + `promotion.py` pre-delete guard + `dual_writer.write()` self-delete (status=committed branch) + `l2.py`/`l3.py` tier promotion source unlink + integration test (testcontainers MinIO) | PR1 LAND |
| **3** | Phase 2 PR2 legacy cleanup | mctrader-data | runner `idempotent skip` 경로 4중 HEAD verify pass → retroactive unlink (PMO 권고 path A) | PR2 LAND |
| **4** | Phase 2 PR3 박제 | mctrader-hub | Story §8.5 Impl Manifest (ADR-032 evidence triad 형식) + §10 FIX Ledger + ADR-029 §D3 amendment box VERIFIED 박제 + scope_manifest D3 wiring carry over → resolved + EPIC-RESULTS amendment + RETRO-MCT-189.md | PR2 + PR3 LAND |

### 산출물 파일 매핑 (PMO 2nd pass scope_manifest 통합)

**mctrader-data 코드 (PR1 wiring + PR2 cleanup)**:
- `src/mctrader_data/nas_storage/nas_uploader.py:309,404` — `head_object()` response 확장 (sha256 metadata + ContentLength 추가, D-4 C)
- `src/mctrader_data/compactor/promotion.py:95-180` — `_head_with_retry()` 반환 dict 4중 verify + `local_path.unlink()` 직전 pre-delete guard (D-4 C, D-8 B)
- `src/mctrader_data/nas_storage/dual_writer.py:236-240` — `status=committed` branch에서 source unlink 통합 (D-2 A) + caller contract 박제 (`tmp_path` 가 아닌 source 측 책임 명시)
- `src/mctrader_data/compactor/l1.py:475` — L1 ParquetWriter `os.replace` 직후 DualWriter.write() commit boundary 안에서 self-delete (D-2 A wiring)
- `src/mctrader_data/compactor/l2.py:133,233` / `l3.py:131,228` — L1→L2, L2→L3 promotion 시 source unlink (D-2 A)
- `src/mctrader_data/compactor/runner.py` — D-2 A 채택 시 promote_l1() 직접 호출 불요 (dual_writer self-delete) + PR2: `idempotent skip` 경로 retroactive HEAD verify + unlink (D-3 C path A)
- `tests/integration/compactor/test_promote_l1_post_put_unlink.py` (신규) — testcontainers MinIO 5 시나리오: 정상 / HEAD 404 / HEAD 5xx / concurrent race / NAS partition

**mctrader-hub 문서 (Phase 1 + PR3 박제)**:
- `docs/stories/MCT-189.md` (update) — phase 전이 + §3 본설계 + §7 + §8.5 + §10 + §11
- `docs/adr/ADR-029-tier-promotion-single-source.md` (amendment box) — Status §MCT-189 amendment + §D3 line 240/246/347 amend + §D10 line 333 강화 + §D11 표 line 347 정정 + Migration line 363 격상
- `docs/domain-knowledge/domain/tier-promotion/grace-0-local-delete.md` (신규) — 4 invariant 박제 (promote_l1 / DualWriter self-delete / 4중 HEAD verify / pre-delete guard) + caller-wired vs decision-defined 분리 표현
- `docs/domain-knowledge/domain/parquet-streaming/cold-path-memory-invariant.md` (extend) — §Cross-ref 추가
- `docs/superpowers/specs/2026-05-16-MCT-189-grace0-wiring-design.md` (본 파일)
- `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md` (별도 — writing-plans skill 산출)
- `docs/retros/EPIC-RESULTS-EPIC-tier-promotion-single-source.md` (amendment) — §MCT-189 행 신규 + Epic CLOSED prerequisite registry "post-LAND production 14d 0 violation" 행 추가
- `docs/retros/RETRO-MCT-189.md` (신규, PR3) — 회고
- `CLAUDE.md` — §MCT-189 entry + §EPIC-tier-promotion-single-source carry over 표 갱신
- `scope_manifests/EPIC-tier-promotion-single-source.yaml` — carry_over_items 표 갱신
- `.codeforge/counters.json` — MCT-189 RESERVED → IN_PROGRESS → COMPLETED, land_prs 4건

## §5 Risk

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| **R1** | forward-only invariant 위반 — D-2 A self-delete + D-3 C retroactive unlink 의 NAS+local 동시 부재 race | **HIGH** | D-8 B pre-delete guard (ETag+ContentLength 재확인) + D-5 A NAS versioning 30d window (PITR) + integration test partition 경로 (D-6 A) |
| **R2** | post-LAND production 14d 0 violation gate failure | MEDIUM | `nas_reader_ambiguity_total` Counter (MCT-170 LAND) + `InvariantHarness._check_ambiguity()` SSOT (MCT-171 LAND) — wiring 후 즉시 emit 검증. PR2 retroactive unlink로 legacy ambiguity 자연 해소 |
| **R3** | PR1↔PR2 latency window 의 ambiguity alert 폭증 | MEDIUM | PR1 LAND 후 즉시 PR2 LAND (target latency <1h) + 30d exemption window (MCT-170 D10 패턴 차용, legacy partition 임시 거부) |
| **R4** | D-2 A self-delete vs runner promote_l1() 호출 — 설계 lane 미확정 | LOW | PMO 권고 **(i) dual_writer self-delete 단독** 채택 (caller 0건 재발 차단 최우선) — plan에서 finalize |
| **R5** | ADR-029 §D11 표 line 347 표현 잔존 → D-1 A 모순 | LOW | Phase 1 PR amendment box에 line 347 정정 명시 |
| **R6** | Phase 0 verify lesson 7회째 누적 — ADR-032 발의 trigger | LOW (PMO retro 영역) | ADR-032 별 governance Story (MCT-190 권고) — evidence triad rule 일반화. RETRO-MCT-189.md 박제 |

## §6 Dependency

| 의존 | 종류 | 상태 | 비고 |
|------|------|------|------|
| EPIC-tier-promotion-single-source POLICY_FINALIZED | prerequisite | ✓ MCT-172 LAND 2026-05-14 | 본 Story = carry over 해소 |
| MCT-169 D3=C VERIFIED (promotion.py LAND) | prerequisite | ✓ promote_l1() 정의 존재 | wiring만 추가 |
| MCT-170 D8=B local fallback sunset 2026-09-01 | prerequisite | ✓ ADR-029 §D8 박제 | D-5 A forward-only invariant 격상 정합 |
| MCT-171 InvariantHarness ambiguity SSOT | prerequisite | ✓ LAND | D-6 A production evidence gate Counter 기반 |
| **ADR-032 별 governance Story (MCT-190)** | follow-up | dependency 권고 (key reserve) | MCT-189 LAND 후 발의 (D-10 B) |
| MCT-174 NAS replication | unrelated | RESERVED (mcnas02 물리 부재) | D-5 A는 NAS versioning 30d 단일 의존, replication 도입은 별개 PITR 강화 |

## §7 PMO scope_manifest 초안 (PR1 Issue body 차용)

PMO 2nd pass 산출 scope_manifest YAML은 PR1 Issue body 와 `scope_manifests/EPIC-tier-promotion-single-source.yaml` carry_over_items 측에 그대로 차용:

```yaml
story_key: MCT-189
title: "ADR-029 §D3=C grace-0 로컬삭제 wiring 완결"
epic: EPIC-tier-promotion-single-source
epic_phase: carry_over_post_finalize
status: RESERVED  # Phase 1 LAND 시 IN_PROGRESS
sequential_phase: ~  # carry over, sequential chain 외
repo: "mctrader-hub + mctrader-data"
phase_pair: phase1_phase2_pr3  # 4 PR 다단

planned_adrs:
  - key: ADR-029
    action: amendment_box
    sections_amended:
      - "§D3 amendment box (Phase 1 draft → PR3 VERIFIED)"
      - "§D3 line 240/246/347 amend (grace 0 일관 — D-1 A)"
      - "§D10 line 333 production evidence gate 강화 (D-6 A)"
      - "§D11 표 line 347 정정 (D-1 A 정합)"
      - "Migration §Forward-only invariant line 363 (D-5 A 격상)"

related_adr_reservations:
  - key: ADR-032
    follow_up_story_key_recommendation: MCT-190

design_decisions:
  D-1: { option: A, cross_ref: "ADR-029 §D3 line 240/246/347 + §D11 표 line 347" }
  D-2: { option: A, cross_ref: "dual_writer.py L236-240" }
  D-3: { option: C, cross_ref: "사용자 결정 2026-05-16" }
  D-4: { option: C, cross_ref: "nas_uploader.py L309/L404 + promotion.py _head_with_retry" }
  D-5: { option: A, cross_ref: "ADR-029 Migration line 363 + ADR-009 §D12.2" }
  D-6: { option: A, cross_ref: "ADR-029 §D10 + ADR-032 evidence triad" }
  D-7: { option: A, cross_ref: "promotion.py INV-6" }
  D-8: { option: B, cross_ref: "promotion.py L162 직전 + dual_writer.py L236-240" }
  D-9: { option: A, cross_ref: "docs/domain-knowledge/domain/tier-promotion/" }
  D-10: { option: B, cross_ref: ".codeforge/counters.json ADR-032" }
```

전체 YAML은 PMO 2nd pass 출력 참조 (이 spec과 함께 PR1 Issue body에 통합 박제).

## §8 다음 진입 — superpowers:writing-plans

본 spec 저장 완료. 후속 = `superpowers:writing-plans` skill 호출 → `docs/superpowers/plans/2026-05-16-mct-189-grace0-wiring.md` 작성.
