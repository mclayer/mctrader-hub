---
adr_id: ADR-008
title: API 키 secret 관리 + Live CI 차단 + Rotation + Compromise response
status: Accepted
date: 2026-05-02
related_story: MCT-8
category: live
---

# ADR-008: Secret management — 1Password CLI + per-exchange isolation + CI block + rotation + compromise response

## Status

Accepted — 2026-05-02. MCT-8 Phase 1 PR.

## Context

ADR-002 D9 (Backtest/Paper secret-free, Live --confirm-live + 격리) + ADR-007 D9 (risk policy amendment 권한) 구체화. Personal-platform (single user, 1억 이하 KRW) 단계.

핵심 invariant: \"CI 에 live secret 절대 미존재. live mode CI 기본 fail (skip 아님).\"

## Decision

### D1. Secret storage = 1Password CLI default

- Permanent: 1Password item
- Runtime: live 실행 직전 process-local env / in-memory config 변환
- File 영구 저장: **금지**. 예외 = age-encrypted disaster recovery backup
- CI secret: 미제공
- `.env.example`: key 이름만, 값 절대 미포함

### D2. Per-exchange + per-account namespace isolation

```
mctrader/live/bithumb/spot/main/{connect_key, secret_key}
mctrader/live/upbit/spot/main/{access_key, secret_key, jwt_signing_policy}
```

`ExchangeCredential` = exchange 별 concrete type. Upbit JWT 서명 = adapter 내부 only.

### D3. Permission 정책

- 출금 권한 비활성화 의무
- IP allowlist 가능 시 활성
- Read-only key 분리 = 거래소 scope 명확 분리 시만 (조건부)
- 거래소 scope 미분리 시 = 별도 adapter interface 로 대체 (live order submit capability 분리)

### D4. Loading lifecycle

| Mode | Secret access | 실패 메시지 |
|---|---|---|
| Backtest | **forbidden** | \"secret access forbidden in backtest mode\" |
| Paper | **forbidden** | 동일 |
| Live | allowed (3-condition AND) | — |

Live 3-condition: `mode==live` + `--confirm-live` + `runtime isolation`.

### D5. CI block

| CI + mode | 정책 |
|---|---|
| backtest | 허용, secret forbidden |
| paper | 허용, secret forbidden |
| live | **기본 fail** |
| live + MCTRADER_ALLOW_LIVE_TEST=1 | dry-run / shadow only |
| live + real secret | **금지** |

CI guard = production entrypoint (`LiveRunner.start()` / `SecretProvider.load_live_credentials()`). Indicator: `CI` / `GITHUB_ACTIONS` / `BUILD_BUILDID` / `JENKINS_URL`.

### D6. Logging policy

- Log: key 존재 여부 / item path / account alias
- 미기록: raw value / prefix / length / HMAC input / JWT payload preimage

### D7. Rotation = event-driven + 정기

- 정기: 반기 1회
- 점검: 분기
- Event-driven 즉시: secret scan hit / 침해 의심 / CI log 노출 / 잘못된 commit / 거래소 이상 / unknown API call

Procedure (8-step):
1. 새 key 발급 (출금 끔 / IP allowlist / 최소 permission)
2. Secret store 등록 (날짜 포함 version)
3. Shadow verification (read-only / dry-run payload)
4. Grace window 24h (max 72h)
5. Cutover (active_key_id 전환 + process 재시작)
6. Ledger reconcile
7. Old key revoke
8. Evidence 기록 (raw secret 미기록)

### D8. Compromise emergency response

```
1. ADR-007 critical_stop 발동
2. Open order cancel (API or UI)
3. Key revoke
4. Risk freeze (amendment 권한 lock)
5. Ledger reconcile (침해 시점부터 전체)
6. New key issue (원인 확인 전 live 미연결)
7. Post-incident ADR-007 amendment
```

Live 재개 = critical_stop 해제 + 새 key + reconcile + risk policy 확인.

### D9. Pre-commit + CI scan

- gitleaks + trufflehog (CI 양쪽 권장)
- `.gitignore`: `.env*`, `secrets.*`, `*.key`, `*.pem`, `*.p12`, `*.age.key`, `.op-session`
- Scan rule: Bithumb / Upbit key shape + generic high entropy + JWT-like + env var names

### D10. Operation ledger

```python
@dataclass(frozen=True)
class OperationEvent:
    operator_id: str
    role: Literal["operator", "secret_holder"]
    action: str
    exchange: str
    account_alias: str
    timestamp: datetime
    result: Literal["success", "failure"]
    evidence_ref: str
```

Single user 단계 = 동일인. 같은 사람이라도 secret 변경 ↔ risk 완화 = 별도 event.

### D11. Backup

- Primary: 1Password 자체 복구
- Secondary: age-encrypted offline (private key 별도 저장)
- 금지: paper raw secret / online replication (Dropbox / iCloud / Drive)

## Alternatives Considered

### A1. Vault as primary
- **기각**: 팀 운영 강함, personal 과도. 운영 복잡도 가치 낮음.

### A2. Plain `.env.local` 파일
- **기각**: 실수 커밋 / 백업 / 인덱싱 위험. `.gitignore` ≠ 보안.

### A3. Env var permanent storage
- **기각**: process tree leak / shell history / crash dump. runtime 만 사용.

### A4. Same secret structure for Bithumb + Upbit
- **기각**: Upbit JWT 서명 vs Bithumb HMAC 차이. concrete type 분리 의무.

### A5. CI live skip (fail 대신)
- **기각**: silent path 방치 위험. fail 의무.

### A6. Read-only key 강제 분리
- **기각**: 거래소 scope 미분리 = 자기기만. 조건부 적용.

### A7. 월 1회 rotation 강제
- **기각**: personal 운영 부담 + 실수 위험. 반기 + event-driven 권장.

### A8. 0-hour grace window (즉시 cutover)
- **기각**: permission / IP / JWT / nonce 검증 시간 필요. 24h grace.

### A9. critical_stop 자동 recovery
- **기각**: key revoke + reconcile + risk 검토 의무. manual operator authority.

## Consequences

### C1. Live 진입 = 3-condition AND
mode + --confirm-live + isolated runtime. CI 자동 차단.

### C2. Backtest / Paper 의 secret access = bug
실패 메시지 명시적. 개발자가 secret 추가로 우회 시도 차단.

### C3. ADR-007 critical_stop 직접 연계
key compromise = 즉시 live block + risk freeze. 자동 amend 금지.

### C4. Pre-commit + CI scan 의무
모든 commit / PR 에 gitleaks + trufflehog 통과.

### C5. Operation ledger 의무
모든 secret rotation / risk amendment / live start-stop = OperationEvent 기록.

### C6. Bithumb / Upbit adapter 분리 의무
Upbit JWT 서명 = adapter 내부 only. raw secret 외부 전파 미금지.

## Cross-references

- ADR-002 D9 / ADR-007 D9
- MCT-12 Epic — Bithumb 첫 Live 진입 시 본 ADR 적용
- ADR-013 (예정, mctrader-market interface) — ExchangeCredential 의 adapter 측 사용
