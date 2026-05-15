---
epic_key: EPIC-mctrader-docker-stack
date: 2026-05-15
type: brainstorm-spec
scope: Epic-level (7 Story sequential)
scope_manifest: scope_manifests/EPIC-mctrader-docker-stack.yaml
brainstorm_skill: codeforge:codeforge-brainstorm
codex_review_passes: 3
total_decisions: 19
story_count: 7
adr_new: ADR-030
adr_amendments: [ADR-027 §D2 optional]
related_epics:
  - EPIC-tier-promotion-single-source (POLICY_FINALIZED 2026-05-14, prod-prereq carry over → MCT-179)
  - EPIC-cold-tier-nas-minio (COMPLETED MCT-147~150)
  - MCT-98 Dockerization Epic (COMPLETED 2026-05-08)
pre_lookup_evidence:
  - "compose.yml: c:\\workspace\\mclayer\\mctrader-hub\\compose.yml (verified-via: Read tool, 315 lines)"
  - "docker/minio/docker-compose.yml: 52 lines (verified-via: Read tool)"
  - "mctrader-data/Dockerfile: 49 lines (verified-via: Read tool)"
  - "mctrader-engine/Dockerfile: 61 lines (verified-via: Read tool)"
  - "NAS_MINIO_* env: mctrader-data/src/mctrader_data/cli.py:681-706 (verified-via: Grep)"
  - "counters.json mctrader-hub.next: 175 → 182 reserved (verified-via: Read tool + Bash)"
---

# EPIC-mctrader-docker-stack — Brainstorm Spec

## 0. Problem Statement

**사용자 원문 (2026-05-15)**: "data 영역을 로컬이 아니라 다른 docker에서 사용 가능하게 만들어야한다."

**IDE 열린 파일**: `c:\workspace\mclayer\mctrader-hub\docker\minio\.env` (NAS Synology MinIO compose stack 의 환경변수 파일)

요청이 4가지로 해석 가능 (a/b/c/d) — 사용자 confirm 결과:
- **(b)+(d) 결합** = mctrader 컴포넌트 docker화 + NAS MinIO wiring 완성

## 1. Why (Analyst 추정 → 사용자 확정)

RequirementsAnalystAgent 가 88% 추정 → 사용자 dialog 후 확정:

> **why**: hub/compose.yml 인프라 stack (postgres+minio+redis+prometheus+grafana+nginx+exporters+signal-collector 5종) 은 이미 존재하나, **mctrader-data (collector) + mctrader-engine (paper-engine/runner) 어플리케이션 서비스가 누락**. 사용자는 .env 파일을 열어두고 "어플리케이션 컨테이너들이 NAS MinIO 에 어떻게 접근하느냐"의 인프라 wiring 문제를 의식하고 있다.

**확정 scope**: Full — collector + paper-engine + backtest profile + observability + WAL 30G prod measurement + EPIC-tier-promotion CLOSED gate 동반.

## 2. Phase 0 verify finding (중대 인식 update)

Phase 0 4 agent burst 결과 + 자체 verify 로 **PMOAgent 초기 가설이 부정확**한 부분 발견:

| 사전 가설 (PMOAgent 1st pass) | 실제 verify 결과 |
|------------------------------|------------------|
| "host docker stack 부재, collector/runner/engine host native 실행" | compose.yml 존재 + signal-collector 5 service 이미 컨테이너화. **단 mctrader-data/engine 만 누락** |
| "Dockerfile 6 repo 다 부재" | 4 repo (data/engine/web/signal-collector) Dockerfile 존재 (MCT-98 Epic COMPLETED) |
| "MinIO 는 NAS 만 존재" | **MinIO 2개 존재**: hub/compose.yml (named volume, dev/test 추정) + docker/minio/ (NAS Synology, prod) |

→ **session prompt 표현은 가설로만 수용** 의무 (feedback_phase0_verify_mandatory) 정합. spec 진입 전 actual 파일 verify 필수.

## 3. Design Decision Trail (19 D, 3 pass Codex)

`scope_manifests/EPIC-mctrader-docker-stack.yaml` §design_decisions 박제 (19 D × 각 option_chosen + rationale + owner_story).

### Pass 1 — Infrastructure (D1-D6)
| D | 결정 | Option |
|---|------|--------|
| D1 | WAL host disk + L1 named volume | C |
| D2 | paper daemon + backtest profile (동일 image) | A |
| D3 | compose profiles dev/prod + env_file 분리 | A |
| D4 | SIGTERM + 60s grace + start-time invariant | C |
| D5 | Prometheus + measurement script + amend trigger | C |
| D6 | 7 Story sequential 분해 | B |

### Pass 2 — Wiring (D7-D12)
| D | 결정 | Option |
|---|------|--------|
| D7 | DNS 직접 해석 + preflight 검증 | A |
| D8 | 앱 /metrics + Grafana dashboard + alert | C |
| D9 | .env + rotate-nas-credentials.sh + cron + Slack | D |
| D10 | env default + compose command override | D |
| D11 | compose CI smoke + testcontainers 병행 | C |
| D12 | semver + sha + latest (prod = pin, dev = latest) | B |

### Pass 3 — Detail (D13-D19)
| D | 결정 | Option |
|---|------|--------|
| D13 | 각 repo 독립 uv.lock + CI lock-version gate | D |
| D14 | env override + YAML default (effective config dump) | D |
| D15 | Redis key prefix (signal:/market:/engine:) | C |
| D16 | docker compose config lint + up --wait health | B |
| D17 | SIGTERM graceful + startup InvariantHarness scan | A |
| D18 | resource limits + Prometheus alert >80% warn | D |
| D19 | mctrader_runs named volume + NAS sync on completion | C |

## 4. 19 D ↔ 7 Story Matrix (PMO 통합 finalize)

3 pass Codex drift 를 PMO 가 통합:

| Story | 제목 | 책임 D | cross-repo PR | depends_on |
|-------|------|--------|---------------|------------|
| **MCT-175** | compose base + dev/prod profile + env 분리 + cross-repo lock gate + ADR-030 publish | D1 / D3 / D7 / D13 | mctrader-hub (Phase 1 docs+ADR / Phase 2 compose+env+CI) | — |
| **MCT-176** | collector container + NAS credential rotation + effective config dump | D7 / D9 / D14 | mctrader-hub + mctrader-data | MCT-175 |
| **MCT-177** | paper-engine daemon + SIGTERM graceful + universe override + Redis prefix | D2 / D4 / D10 / D15 | mctrader-hub + mctrader-engine | MCT-176 |
| **MCT-178** | backtest-runner profile + oneshot + compose config CI lint | D2 / D4 / D10 / D16 | mctrader-hub + mctrader-engine | MCT-177 |
| **MCT-179** | observability + WAL 30G production measurement + DR mode + alert rule | D5 / D8 / D17 | mctrader-hub + mctrader-data + mctrader-engine | MCT-178 |
| **MCT-180** | integration smoke + testcontainers + resource limits + alert | D4 / D11 / D18 | mctrader-hub + mctrader-data + mctrader-engine | MCT-179 |
| **MCT-181** | image registry pin + backtest artifact NAS sync + Epic 박제 | D12 / D19 | mctrader-hub + mctrader-data + mctrader-engine | MCT-180 |

**LAND chain**: strict sequential. 각 Story 가 직전 LAND 의 service slot / image / metric / volume 의존.

## 5. Risk Registry

| Severity | Risk | Owner Story / 대응 |
|----------|------|---------------------|
| **HIGH** ✅ accepted | NAS HTTP-only 평문 (ADR-027 D2 Stage 1 한정, MCT-155 cutover 미확정) | **user_acknowledged_at: 2026-05-15** by mclayer8865@gmail.com. Mitigation: LAN 내부망 + NAS firewall mctrader IP only + .env 0600 + 90d rotation. MCT-155 defer (별 cutover Story 미예약) |
| **CRITICAL carry over** | WAL 30G 가설 미측정 (50sym×3ch×12seg/h ±50% range) | **MCT-179** (peak market open 09:00 KST 측정) — EPIC-tier-promotion CLOSED prereq |
| **MEDIUM** | D14 effective config 출력 미존재 시 env↔YAML 우선순위 운영 혼선 | MCT-176 (effective config dump CLI) |
| **MEDIUM** ✅ accepted | D17 host disk 손실 → 데이터 영구 손실 (forward-only invariant) | **user_acknowledged_at: 2026-05-15** by mclayer8865@gmail.com. Rationale: ADR-029 §D4 WAL local-only + ADR-009 §D12 forward-only invariant. backup sidecar = invariant 위반 + op risk 증가 → reject. Loss window = 1d max (host disk replace 후 forward-only) |
| **MEDIUM** | D19 NAS sync 실패 시 local↔remote artifact 갈림 | MCT-181 (completion marker + retry policy) |
| **LOW** | dev/prod profile config drift | MCT-178 (compose config CI gate) |

## 6. Carry Over from EPIC-tier-promotion-single-source

POLICY_FINALIZED 2026-05-14 의 prod-2 prereq (WAL 30G production measurement) = **MCT-179 책임 흡수**:
- peak market open 09:00 KST burst window 측정
- 30G 초과 시 ADR-029 D11 hard_limit amendment 발의 (D8-7=A FAIL gate)
- production evidence quad (bucket size + log + Prometheus + drainage) 동일 1h window

## 7. ADR-030 Reservation

- **Key**: ADR-030
- **Title**: Docker stack governance — single-host compose + dev/prod profile + image registry + observability
- **Owner Story**: MCT-175 (Epic entry, ADR publish 동반)
- **Status**: Proposed → MCT-175 LAND 시 Accepted 전환
- **본문 박제 대상 8 D**: D1 / D2 / D3 / D7 / D12 / D13 / D17 / D18 (governance level)
- **본문 박제 제외**: D4 / D5 / D8-D11 / D14-D16 / D19 (Story 구현 detail — manifest 박제로 충분)

## 8. Artifact Reference

- scope_manifest: [scope_manifests/EPIC-mctrader-docker-stack.yaml](../../../scope_manifests/EPIC-mctrader-docker-stack.yaml) (341 lines)
- counters.json: `mctrader-hub.next` 175 → 182, 8 reservation 추가 (MCT-175~181 + ADR-030)
- Codex review trail: 3 pass × 19 결정 (대화 transcript = brainstorm session)

## 9. Next Entry

`superpowers:writing-plans` 스킬 호출 → **MCT-175** plan 작성 (Story 1, Epic entry).

Sequential chain 이므로 MCT-176~181 plan 은 각 Story 진입 시점에 작성 (직전 Story LAND artifact 의존성 반영).

## 10. Brainstorm Session Trail

- Phase 0 (2026-05-15): 4 agent parallel burst — DomainAgent / ResearcherAgent / RequirementsAnalystAgent / PMOAgent
- Phase 0 verify: 6 repo Dockerfile 상태 + compose.yml + .env / NAS_MINIO_* env 변수 실측
- Phase 1 dialog × 4회: 의도 명확화 (b+d 결합) + MinIO dual + runner 정체성 + Scope full
- Phase 1 Codex × 3 pass: D1-D6 → D7-D12 → D13-D19 (19 결정 + 7 Story matrix drift 통합)
- Phase 2 PMO 2nd pass: 19 D ↔ 7 Story 통합 매트릭스 + scope_manifest YAML + counters reservation
