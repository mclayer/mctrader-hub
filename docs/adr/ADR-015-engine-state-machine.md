---
adr_id: ADR-015
title: Engine state machine for Admin Engine Control Panel (daemon + one-shot)
status: Accepted
date: 2026-05-06
related_story: MCT-97
category: web
supersedes: []
amends: []
---

# ADR-015: Engine state machine for Admin Engine Control Panel (daemon + one-shot)

## Status

Accepted — 2026-05-06. MCT-97 design phase.

- Authors: ArchitectAgent (chief) + OperationalRiskArchitectAgent (deputy)
- Reviewers: ArchitectPLAgent

## Context

MCT-97 의 5 engine class 는 두 lifecycle 패턴으로 나뉜다 — daemon (collector / paper runner) + one-shot (backtest / WFO). market gateway 는 §AS-4 grep 결과 library only (별도 process 부재) 로 SM 대상 외 (status read 만).

기존 자산:
- `mctrader_engine.runtime.paper_runner.PaperRunner`: cooperative `cancel()` 보유 (asyncio.Event 기반)
- `mctrader_engine.executor.paper.PaperExecutor`: `cancel()` + `_cancel_event` (asyncio.Event)
- `mctrader_engine.executor.backtest.BacktestExecutor`: synchronous `run()` loop, **cancel hook 부재**
- `mctrader_engine.wfo.search.coordinator`: BacktestExecutor 위 동기 loop, **cancel hook 부재**
- collector: systemd unit 자산 (MCT-94)
- mctrader-web `LifecycleManager`: paper-mode 단일 active session enforcement, GRACEFUL_STOP_TIMEOUT_SECONDS = 30s

state 표현이 코드 전반에 흩어져 있어 admin panel 의 표시 / SM transition 검증 / idempotent guard 가 일관성 부족.

## Decision

5 engine 의 lifecycle 을 **두 SM 으로 unified** 표현하고 control plane 의 모든 transition 을 검증.

### Daemon SM (collector / paper runner)

```
[stopped] ---start--->  [starting] ---ready--->  [running] ---stop--->  [stopping] ---> [stopped]
                                                    |
                                                    +---crash---> [crashed] ---restart---> [starting]
                                                    |
                                                    +---heartbeat stale > N---> [degraded]
                                                                                    |
                                                                                    +---heartbeat fresh---> [running]
                                                                                    |
                                                                                    +---stop---> [stopping]
                                                                                    |
                                                                                    +---process exit non-zero---> [crashed]
```

**State 정의**

| State | 의미 | Heartbeat 기대 |
|-------|------|----------------|
| `stopped` | 명시적 또는 graceful 종료 후 | absent |
| `starting` | start 명령 수신 ~ ready 신호 도달 직전 | optional |
| `running` | ready 신호 + heartbeat fresh | fresh (≤ N sec) |
| `stopping` | stop 명령 수신 ~ graceful timeout 직전 | optional |
| `crashed` | unexpected exit + non-zero | absent (sudden) |
| `degraded` | running 인 채 heartbeat stale > N sec | stale |

**Transition rule**

- `[running]` 중 `start` 호출 → 409 Conflict (idempotent: 이전 Idempotency-Key 와 동일하면 200 cached)
- `[stopping]` 중 `start` → 409 Conflict (race 차단)
- `[crashed]` → `restart` 또는 `start` 동일 (둘 다 `[starting]` 으로)
- `[degraded]` → control 가능 (stop / restart) — alarm-only state, control 미차단
- `[degraded]` 중 process exit non-zero (subprocess return code ≠ 0 또는 systemd `failed` 상태) 수신 → `[crashed]` 전이 + restart 회수 카운터 증가 (lock-in 회피, degraded → crashed 직접 edge)
- 자동 restart 회수 ≥ 임계 (default 3 회 / 5 분) → `[crashed]` lock + UI "manual intervention" 표시 (admin manual `stop` 으로 lock 해제)

### One-shot SM (backtest / WFO)

```
[queued] ---run--->  [running] ---success--->  [completed]
                        |
                        +---error--->  [failed]
                        |
                        +---cancel--->  [cancelling] ---> [cancelled]
```

**State 정의**

| State | 의미 |
|-------|------|
| `queued` | trigger 수신 직후, executor 시작 전 |
| `running` | executor 시작 ~ 완료 직전 |
| `cancelling` | cancel 명령 수신 ~ cooperative hook 응답 대기 |
| `completed` | 정상 종료 + 결과 파일 작성 완료 |
| `failed` | 예외 종료 (스택트레이스 audit + UI display) |
| `cancelled` | cooperative cancel 응답 후 종료 |

**Transition rule**

- `[queued]` 또는 `[running]` 중 cancel → `[cancelling]` (재진입 시 200 cached)
- `[completed | failed | cancelled]` 는 terminal — 동일 run_id 로 trigger 재요청 시 409 (UI 가 신규 run_id 발급 강제)
- `[cancelling]` 진입 후 cooperative timeout 초과 시 (default 30s) → `[failed]` 로 강제 + 부분 결과 폐기 + audit `outcome=cancel_timeout`

### Cooperative cancel hook requirement (OperationalRiskArchitect deputy)

paper_runner 는 보유 (`PaperRunner.cancel()` + `PaperExecutor._cancel_event`). 그러나:
- **BacktestExecutor**: `run()` 은 synchronous per-bar loop, cancel 부재 → P3 진입 직전 mctrader-engine PR 1건 필요 (per-bar 루프 시작에 `cancel_token: threading.Event | None = None` 인자 + 매 iteration 체크 + `CancelledError` 발생)
- **WFOOrchestrator (`wfo.search.coordinator`)**: trial 단위 fail-fast 분기는 있으나 외부 cancel 부재 → 동일 PR 에 trial 시작 시 token 체크 추가
- mctrader-web `BacktestLifecycleManager` / `WfoLifecycleManager` 가 token 보유 + cancel 명령 수신 시 `set()`

### Operational risk (OperationalRiskArchitect 5 항목)

1. **DR (disaster recovery)**: 모든 engine 동시 down (UC-8) — admin "Boot sequence" 수동 명령 + dependency order (market-gw library load → collector → paper). 자동 boot 미제공 (solo dev scope).
2. **Disconnect**: heartbeat stale > N sec 자동 감지 → `[degraded]` 표시. control 명령 evp 무관 (stop / restart 가능).
3. **Clock skew**: SM transition 의 `since_ts` 는 server-side `datetime.now(timezone.utc)` 만, 클라이언트 time 미사용. heartbeat schema (`ts`) 와 server clock 의 ±5s drift 허용.
4. **Rate limit**: control plane 분당 30 회 / status plane 분당 300 회 (per token). engine_id 별 추가 bucket 미적용 (solo dev 단순화).
5. **Env isolation**: Windows dev 의 in-process subprocess 추적과 Linux prod 의 systemd 추적 모두 `control_adapter` 단일 abstraction. SM 표현은 OS 무관 (process exit code / heartbeat 두 신호로만 결정).

## Alternatives considered

| 대안 | Reject 사유 |
|------|-------------|
| (1) 단일 SM 으로 daemon + one-shot 통합 | 의미 mismatch (`[completed]` 가 daemon 에 부적합), transition rule 폭발 |
| (2) state 표현 없이 boolean alive flag 만 | `[degraded]` / `[crashed]` 구분 불가, idempotent guard 불완전 |
| (3) per-engine custom SM | 중복 + 표시 일관성 부족 |
| (4) 외부 SM library (transitions / pytransitions) | 의존성 추가, dataclass + dispatch table 충분 |

## Consequences

- `mctrader-web/src/mctrader_web/api/admin/state_machine.py` 두 SM dataclass + transition table
- control plane endpoint 가 transition 호출 → SM 위반 시 409 + audit row
- BacktestExecutor / WFO cancel hook PR (mctrader-engine, P3 진입 직전 — Change Plan §3 예외 PR)
- panel 표시 = SM state + heartbeat age + last error + recent restart count

## Follow-up impact

- ADR-016 (audit) 의 transition row schema 와 결합 — 모든 transition 이 audit append
- AC-2 (제어 write) 의 idempotent guard 는 본 SM transition rule 위에 구현
- AC-7 (cross-platform) 의 SM 표현은 OS 무관 — control_adapter 만 분기
