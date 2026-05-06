# Collector HA Phase 5 — Ops Scripts (systemd + Ansible + heartbeat health probe)

**Date**: 2026-05-06
**Story**: MCT-94 (#104) — X5 child of MCT-89
**Sister Stories MERGED**: MCT-91 (X2) + MCT-92 (X3) + MCT-93 (X4)
**Spec**: `docs/superpowers/specs/2026-05-05-collector-ha-active-active-design.md`

## 0. Codex Phase 5 design review (6/6 ADOPT 합)

| F | Codex | Sonnet | Action |
|---|---|---|---|
| F-1 systemd unit | SUGGEST | 채택 | KillSignal=SIGTERM + TimeoutStopSec=60s + StartLimitBurst=20/300s + KillMode=mixed |
| F-2 Ansible deploy lock | PUSH-BACK | fix 적용 | shared-storage `.deploy_lock` mkdir + `any_errors_fatal: true` (concurrent operator 차단) |
| F-3 health probe | SUGGEST | 채택 | thin wrapper `exec mctrader-data status` (no jq dependency) |
| F-4 README prereq | SUGGEST | 채택 | NTP <1s + same uid:gid + capacity TBD by X7 |
| F-5 X5 AC | SUGGEST | 채택 | dry-run lint/verify only (real 2-node E2E → X7) |
| F-6 out-of-scope | ADOPT-AS-IS | 채택 | — |

Escalation 0.

## 1. Architect 결정 (X5 specific)

| # | 결정 | 근거 |
|---|---|---|
| 1 | systemd `KillMode=mixed` | main process SIGTERM (graceful) + child SIGKILL fallback. 60s drain window 충분 (collector buffer flush + WS close) |
| 2 | `EnvironmentFile=/etc/mctrader/collector.env` per-host | NODE_ID 가 host별 고유 — Ansible 이 deploy 시 inventory 의 `node_id` var 를 template 으로 sync 가능 (X5 plan 외) |
| 3 | shared-storage `.deploy_lock` mkdir 패턴 | NFS atomic mkdir 은 race-free distributed primitive. `.lock` 파일 (open O_EXCL) 도 가능하나 mkdir 가 더 portable |
| 4 | `any_errors_fatal: true` | 한 host failure 시 cluster 가 degraded — 즉시 중단해서 active-passive 로 떨어지는 것 차단 |
| 5 | health probe = thin wrapper | jq / Python json 의존성 0. CLI 가 이미 classification + threshold 책임 |
| 6 | README capacity TBD | X7 Calibration 측정 후 backfill. 무근거 numeric minimum 회피 |
| 7 | dry-run lint/verify only AC | real E2E 는 X7 — X5 scope 명확히 artifact freeze |
| 8 | 자동 rollback 거부 (Epic #15) | manual `git revert` + 재배포. 자동 rollback 의 false positive 위험 > 수동 절차의 비용 |

## 2. Step-by-step plan

### Step 1 — `scripts/ha/` 디렉토리 + 6 artifact 생성

- `mctrader-data-collector.service` — systemd unit (Codex F-1 fix 적용)
- `collector.env.example` — per-host env template
- `deploy.yml` — Ansible rolling deploy (Codex F-2 fix: deploy lock + any_errors_fatal)
- `inventory.example.ini` — sample inventory (`node_id` per-host var)
- `heartbeat_health_check.sh` — thin wrapper (Codex F-3 fix)
- `README.md` — host prerequisites + setup runbook + stale-lock recovery + manual rollback

### Step 2 — Story §1-9 작성 + frontmatter status: phase:완료

- `docs/stories/MCT-94.md` — Story §1-7 + §8 개발 서사 + §9 품질 게이트 + §11 회고
- 본 PR 자체가 implementation + close 통합 (mctrader-hub 측 hub-only PR — 별도 mctrader-data 변경 0)

### Step 3 — local lint (Windows skip — Linux runner 또는 deploy 시 수행)

```bash
ansible-playbook -i scripts/ha/inventory.example.ini scripts/ha/deploy.yml --syntax-check --check --diff
ansible-lint scripts/ha/deploy.yml
shellcheck scripts/ha/heartbeat_health_check.sh
systemd-analyze verify scripts/ha/mctrader-data-collector.service
```

(Windows dev workstation에서는 위 4개 모두 미설치 — README 의 manual command 형태로 운영자 측 검증 위임. CI 에서는 `setup-ansible` action / `shellcheck-action` 로 자동화 가능 — X5 scope 외, 후속 minor.)

### Step 4 — PR open + Codex implementation review + admin merge

- title: `[MCT-94] feat(ha): Ops Scripts (X5 of MCT-89) — systemd + Ansible rolling deploy + heartbeat health probe`
- body: Codex Phase 5 design 6/6 ADOPT + scripts/ha/ artifact list
- Codex implementation review 6-area (artifact 정합 / Ansible 안전성 / systemd 정합 / README 완전성 / lint 가능성 / scope creep)
- ADOPT 합 후 admin merge

### Step 5 — Memory + 다음 phase

- `project_mctrader.md` 에 Phase 5 close marker 추가
- 다음 step: X6 (mctrader-web `pages/00_status.py`)

## 3. Acceptance Criteria

- [ ] 6 artifact 모두 commit (`scripts/ha/` 하위)
- [ ] Story MCT-94 §1-9 + §11 작성
- [ ] Phase 5 plan committed
- [ ] PR open + Codex implementation review 6-area ADOPT 합
- [ ] PR admin merge
- [ ] Memory project_mctrader.md update

## 4. Out-of-scope (X6/X7/v2)

- Streamlit `00_status` panel (X6)
- Calibration C1/C2 + 양 node 30분 E2E demo (X7)
- ansible-lint/shellcheck CI workflow 자동화 (후속 minor)
- proactive alerting (v2)
- k8s/Nomad (Epic #3 거부)
- auto-rollback (Epic #15 거부)
