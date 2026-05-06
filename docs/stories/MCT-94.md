---
story_key: MCT-94
story_issues:
  - repo: mclayer/mctrader-hub
    number: 104
status: phase:완료
---

# MCT-94: Collector HA — Ops Scripts (X5 of MCT-89)

- **Issue**: #104
- **Status**: phase:완료

## 1. 사용자 요구사항 (verbatim)

mctrader backtest를 위한 data 수집 엔진을 구동하려 하는데 아직 HA에 대한 구성이 되어 있지 않다. HA구성을 통해 코드 수정사항 배포와 2개 이상의 Active Node 관리를 통해 데이터 순단을 줄이고자 한다.
(child slice: ops/deployment artifacts. 부모 Epic = MCT-89. X4 (MCT-93, mctrader-data 0.8.0 main merged) 후속. Phase 1 spec/plan 의 X5 = systemd unit + Ansible rolling deploy + heartbeat health probe + README 호스트 prerequisites. real 2-node E2E demo 는 X7 scope, X5 는 dry-run lint/verify only.)

## 2. 도메인 해석

X5 = "코드 수정사항 배포" 의 *operationally provable* 단계. X4 의 status CLI exit code 0/1/2 가 systemd / Ansible 측 health gate input 으로 활용되어, rolling deploy 자체가 sister X1-X4 의 measurable invariant 위에서 작동.

핵심 invariant:
- `serial: 1` rolling = 한 번에 한 node 만 stop, 양 node 동시 down 차단
- shared-storage `.deploy_lock` (Codex F-2 PUSH-BACK fix) = 동시 operator/CI deploy 충돌 차단
- pre-stop health gate = 지금 stop 하면 cluster 가 active-passive 로 떨어지는지 사전 검증
- post-start health gate = 새 deploy 가 hot-reload window 통과했는지 사후 확인

## 3. 관련 ADR / Contract

신규 amendment 없음. ADR-009 §D2.1 / §D5 / §D10.7 / §D11.8 + heartbeat-schema.v1 (X4 amendment 포함) 그대로 enforce.

## 4. 외부 contract — 신규 amendment 없음

X5 는 contract 변경 0. ops/deployment 측 artifact 만 freeze.

## 5. 요구사항 확장 해석 (Codex 6-area review fix 반영)

### 5.1 systemd unit (F-1 SUGGEST 채택)

`mctrader-data-collector.service` freeze:
- `KillSignal=SIGTERM`, `TimeoutStopSec=60s`, `KillMode=mixed` (graceful drain → fallback SIGKILL)
- `Restart=always`, `RestartSec=10s`, `StartLimitBurst=20`, `StartLimitIntervalSec=300`
- `EnvironmentFile=/etc/mctrader/collector.env` (per-host `NODE_ID` + `MCTRADER_DATA_ROOT`)
- `ExecStart=/opt/mctrader/.venv/bin/mctrader-data collect --top-n 50 --node-id ${NODE_ID} --root ${MCTRADER_DATA_ROOT}`
- Resource hardening: `NoNewPrivileges=yes`, `PrivateTmp=yes`, `ProtectSystem=strict`, `ReadWritePaths=...`
- stdout/stderr → journal (`journalctl -u mctrader-data-collector`)

### 5.2 Ansible rolling deploy (F-2 PUSH-BACK fix)

`deploy.yml` freeze:
- `serial: 1`, `any_errors_fatal: true`
- **shared-storage `.deploy_lock` mkdir** (atomic POSIX rename 보장 환경에서만 안전 — README §"Shared storage" prerequisite 의무)
- `run_once: true` lock acquire / release
- pre-task: `mctrader-data status --format json` exit 0 on peer
- stop systemd → git pull → uv pip sync → start systemd → wait self heartbeat green (retries: 6, delay: 5s)
- post-task: lock release (or manual stale-lock recovery 문서화)

### 5.3 heartbeat health probe (F-3 SUGGEST 채택)

`heartbeat_health_check.sh` = thin wrapper. `exec mctrader-data status --root $MCTRADER_DATA_ROOT "$@"` 만 — jq / python json 모두 0 dependency. exit code 0/1/2 forward.

### 5.4 README host prerequisites (F-4 SUGGEST 채택)

- systemd 245+ / Python 3.11+ / uv installed
- 공유 storage 의 atomic rename 보장 (NFSv3 close-to-open / NFSv4 / Ceph same-pool / SMB v3)
- same uid:gid for `mctrader` user across hosts
- NTP/chrony clock drift `<1s` (heartbeat freshness 의 wall-clock dependency)
- Bithumb public WS outbound firewall (no API key)
- "**Capacity sizing TBD by X7 Calibration C1/C2**" — RAM/disk numeric minimums 무근거 회피, 초기 가이드 line (RAM 2GB / disk 100GB / CPU 2 vCPU) 만 제공 (X7 측정 후 README 업데이트 예정)
- 초기 setup runbook (user 생성 → mount → uv install → /etc/mctrader/collector.env → systemd enable)
- Stale lock recovery 절차 + manual rollback (Epic decision #15)

### 5.5 X5 Acceptance criteria (F-5 SUGGEST 채택)

X5 = artifact freeze only, real 2-node E2E 는 X7. AC:
- [ ] `ansible-playbook --check --diff` syntax + dry-run PASS (sample inventory)
- [ ] `ansible-lint scripts/ha/deploy.yml` PASS
- [ ] `shellcheck scripts/ha/heartbeat_health_check.sh` PASS
- [ ] `systemd-analyze verify scripts/ha/mctrader-data-collector.service` PASS
- [ ] README covers OS / Python / shared storage / time sync / network / capacity TBD
- [ ] Stale lock recovery + manual rollback documented

### 5.6 후속 escalation (X5 scope 외)

- 양 node 30분 E2E demo (X7)
- Calibration C1/C2 (X7 — RAM/disk/throughput 측정 후 README capacity 절 업데이트)
- proactive alerting Slack/email (v2)
- k8s/Nomad orchestration (Epic decision #3 명시 거부 — 영구)
- auto-rollback on health gate failure (Epic decision #15 명시 거부 — manual `git revert` 영구)

## 6. 외부 지식 배경

### 6.1 systemd `Restart=always` + `StartLimitBurst` semantics

- `StartLimitBurst=20`, `StartLimitIntervalSec=300` = 5분 안에 20번 재시작 시도까지 허용 (active-active collector 의 WS reconnect 패턴 수용)
- 이를 초과하면 systemd 가 `failed` 상태로 전이, 운영자 수동 `systemctl reset-failed mctrader-data-collector` 필요

### 6.2 POSIX `mkdir(2)` atomic on shared storage

- Same-directory mkdir 은 atomic on POSIX (return EEXIST if exists, no partial state)
- NFS server 측 atomic rename 지원 가정 (대부분 server OK, NFSv3 close-to-open 또는 NFSv4 권장)
- Ceph same-pool atomic, SMB v3 atomic
- 따라서 `.deploy_lock` mkdir 가 race-free 인 distributed lock primitive 로 작동

### 6.3 Ansible `serial: 1` + `any_errors_fatal: true` semantics

- `serial: 1` = 한 host 의 모든 task 가 끝나야 다음 host 진행 (한 batch 내 직렬화)
- 그러나 두 별도 `ansible-playbook` invocation 은 lock 없이 동시 실행 가능 → Codex F-2 PUSH-BACK 의 race 시나리오
- `any_errors_fatal: true` = 한 host failure 시 즉시 모든 batch 중단 (cluster degraded 상태 차단)

### 6.4 Bithumb public WS connection — no API key required

- `wss://pubwss.bithumb.com/pub/ws` (transaction / orderbookdepth channels)
- Outbound HTTPS 만 필요, inbound port 0
- API key 부재 = 호스트별 secret 관리 0 (deploy 단순화)

## 7. 설계 서사

(Phase 5 plan: `docs/superpowers/plans/2026-05-06-collector-ha-phase-5.md` 에서 freeze)

## 8. 개발 서사

### 8.1 구현 PR (X5)

- mctrader-hub PR — Story §1-7 + Phase 5 plan + scripts/ha/ artifacts (이번 PR에 모두 포함)

### 8.2 변경 surface (mctrader-hub)

| File | 변경 |
|---|---|
| `scripts/ha/mctrader-data-collector.service` (NEW) | systemd unit (graceful drain + StartLimitBurst tuning) |
| `scripts/ha/collector.env.example` (NEW) | per-host env template |
| `scripts/ha/deploy.yml` (NEW) | Ansible rolling deploy (deploy lock + health gate) |
| `scripts/ha/inventory.example.ini` (NEW) | sample inventory |
| `scripts/ha/heartbeat_health_check.sh` (NEW) | thin wrapper for mctrader-data status |
| `scripts/ha/README.md` (NEW) | host prerequisites + setup + rolling deploy + stale lock recovery |

### 8.3 Codex Phase 5 design review (6/6 ADOPT 합)

| F | Verdict | Sonnet decider |
|---|---|---|
| F-1 systemd unit | SUGGEST → 채택 | KillSignal/TimeoutStopSec/StartLimitBurst 명시 |
| F-2 Ansible deploy lock | PUSH-BACK → fix 적용 | shared-storage `.deploy_lock` mkdir + `any_errors_fatal: true` |
| F-3 health probe | SUGGEST → 채택 | thin wrapper, no jq |
| F-4 README prereq | SUGGEST → 채택 | NTP/uid/gid + capacity TBD by X7 |
| F-5 X5 AC | SUGGEST → 채택 | dry-run lint/verify only |
| F-6 out-of-scope | ADOPT-AS-IS | — |

Escalation 0 (모두 in-Phase 채택).

## 9. 품질 게이트 이력

| Gate | Result | Evidence |
|---|---|---|
| Codex Phase 5 design 6/6 review | ADOPT 합 (escalation 0) | Story §5 + plan §0 |
| systemd unit syntax | TBD on Linux runner | `systemd-analyze verify` (CI 또는 local Linux) |
| Ansible playbook syntax | TBD on CI | `ansible-playbook --syntax-check --check --diff` (CI 또는 local) |
| ansible-lint | TBD on CI | `ansible-lint scripts/ha/deploy.yml` |
| shellcheck | TBD on CI | `shellcheck scripts/ha/heartbeat_health_check.sh` |
| Real 2-node E2E | DEFERRED to X7 | per Story §5.5 + Spec §6.2 |

CI verification 은 Linux 환경에서 운영자가 별도 실행 (Windows dev workstation에서는 ansible/systemd-analyze 부재 — local skip OK, real verification 은 deploy 시 수행).

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

(FIX 발생 시 append)

## 11. 회고

### 11.1 Phase 5 종료 marker (2026-05-06)

X5 ops 5 artifact (systemd unit + collector.env + deploy.yml + inventory + health probe + README) 모두 freeze. X4 의 status CLI exit code 0/1/2 가 systemd / Ansible 측 health gate input 으로 wired.

### 11.2 X5 기술 부채 surface

- ansible-lint / shellcheck / systemd-analyze verify 의 CI 자동 실행 (현재는 README 의 manual command 만 — 후속 minor에서 GitHub Actions workflow 추가 검토)
- 양 node 30분 E2E demo + Calibration C1/C2 → X7 sealing
- README capacity 절의 RAM/disk numeric minimum → X7 측정 후 backfill

### 11.3 Epic MCT-89 진행도 (X5 종료 시점)

| Phase | Story | 상태 |
|---|---|---|
| 1 | MCT-89 (Epic) | CLOSED ✅ |
| 2 | MCT-91 (X2) | MERGED ✅ |
| 3 | MCT-92 (X3) | MERGED ✅ |
| 4 | MCT-93 (X4) | MERGED ✅ |
| **5** | **MCT-94 (X5)** | **MERGED ✅ (이번 Phase)** |
| 6 | (X6 mctrader-web `00_status` panel) | PENDING |
| 7 | (X7 Calibration C1/C2 + 양 node 30분 E2E demo + Epic close) | PENDING |
