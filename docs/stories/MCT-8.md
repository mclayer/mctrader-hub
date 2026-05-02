---
story_key: MCT-8
status: phase:요구사항
component: live
type: brainstorm
related_adr: ADR-008
---

# MCT-8: API 키 secret 관리 + Live CI 차단 정책

## 1. 사용자 요구사항 (verbatim)

mctrader 의 API 키 secret 관리 + live CI 차단 정책 (paper 모드 가상 자금 시뮬레이션 포함). ADR-002 D9 (Backtest/Paper secret-free, Live --confirm-live + 격리) 의 구체화 + ADR-007 D9 (risk policy amendment 권한) 와 연계.

## 2. 도메인 해석

ADR-002 / ADR-007 baseline. Personal-platform (single user, single machine, 1억 이하 KRW) 단계의 합리적 default. 핵심 invariant: \"CI 에 live secret 절대 미존재. live mode CI 기본 fail.\"

## 3. 관련 ADR

- ADR-008 ([`../adr/ADR-008-secret-management.md`](../adr/ADR-008-secret-management.md))
- baseline: ADR-002 D9 / ADR-007 D9

## 4. 관련 코드 경로

```
mctrader-engine/src/mctrader/secret/
├── provider.py            # SecretProvider Protocol (1Password CLI default)
├── credentials.py         # ExchangeCredential (per-exchange concrete type)
├── lifecycle.py           # mode-dependent load policy (Backtest/Paper forbid)
├── ci_guard.py            # CI indicator detection + block
├── rotation.py            # key rotation procedure + grace window
└── audit.py               # operation ledger (operator + secret_holder)
```

## 5-6. 요구사항 / 외부 지식

Reference: 12-factor app / OWASP Secrets / Bithumb (Connect/Secret) / Upbit (Access/Secret + JWT) / gitleaks / trufflehog / `op` (1Password CLI).

## 7. 설계 서사 (요약)

### 7.1 Secret storage = 1Password CLI default

비교:
| 방식 | 평가 | 채택 |
|---|---|---|
| Env var | runtime injection 만, 영구 저장 부적합 (process tree leak / shell history / crash dump) | runtime only |
| Plain file | 실수 커밋 / 백업 동기화 / editor 인덱싱 | **금지** |
| OS keyring | personal OK, headless 재현성 약함 | optional |
| age-encrypted yaml | Git 에 암호문 저장 가능, 복호화 키 관리 다시 문제 | offline backup only |
| 1Password CLI | 비용 / 운영 / 복구 / offline 모두 균형 | **default** |
| Vault | 팀 운영 강함, personal 과도 | 미채택 |

### 7.2 Per-exchange + per-account namespace

```
mctrader/live/bithumb/spot/main/connect_key
mctrader/live/bithumb/spot/main/secret_key
mctrader/live/upbit/spot/main/access_key
mctrader/live/upbit/spot/main/secret_key
mctrader/live/upbit/spot/main/jwt_signing_policy
```

`ExchangeCredential` = exchange 별 concrete type. Bithumb spot ↔ Upbit spot 같은 구조체 미사용. **Upbit JWT 서명 = adapter 내부에서만 수행. Secret raw value 외부 logging / metrics / error context 미노출.**

### 7.3 Loading lifecycle (mode 별)

| Mode | Secret access | 실패 메시지 |
|---|---|---|
| Backtest | **금지 (load 시도 = bug)** | \"secret access forbidden in backtest mode\" |
| Paper | **금지 (Paper = 가상 자금, secret 불필요)** | 동일 |
| Live | 허용 (3-condition AND) | — |

Live entry 3-condition:
1. `mode == live` (CLI flag)
2. `--confirm-live` (human intent gate)
3. `runtime isolation` (live process ↔ backtest worker / CI / notebook 분리)

### 7.4 CI block 정책

| CI + mode | 정책 |
|---|---|
| backtest | 허용, secret forbidden |
| paper | 허용, secret forbidden |
| live | **기본 fail** (skip 아님 — silent path 위험) |
| live + MCTRADER_ALLOW_LIVE_TEST=1 | dry-run / shadow only, real order forbidden |
| live + real secret | **금지** |

CI guard = **production entrypoint 가까이** (test code 아님). `LiveRunner.start()` / `SecretProvider.load_live_credentials()` 에서 `CI=true` / `GITHUB_ACTIONS` / `BUILD_BUILDID` / `JENKINS_URL` 등 indicator 감지 시 block.

Dry-run = order payload 생성, exchange submit 미호출. Shadow = mock exchange / sandbox adapter. Sandbox credential = production live credential 과 완전히 다른 namespace.

### 7.5 Permission 정책

- 거래소 console: 출금 권한 비활성화 의무
- IP allowlist: 가능 시 활성 (개인 노트북 = IP 변동 → trade-off)
- Read-only key 분리 = **조건부**: 거래소가 scope 명확 분리 시만 가치. 거래소 scope 미분리 = key 분리 자기기만, 별도 adapter interface 차단으로 대체.

### 7.6 Logging 정책

- Secret provider: key 존재 여부 / item path / account alias 만 log
- 미기록: raw value / prefix / length / HMAC input / JWT payload preimage

### 7.7 Rotation (event-driven + 정기 점검)

- 정기: 반기 1회 (월 1 = 부담, 연 1 = 느슨)
- 분기 점검: rotation 필요성 평가
- Event-driven 즉시: secret scan hit / 머신 침해 의심 / CI log 노출 / 잘못된 commit / 거래소 이상 주문 / unknown API call

Procedure 8-step:
1. 새 key 발급 (출금 권한 끔, IP allowlist, 최소 permission)
2. Secret store 등록 (날짜 포함 item version, e.g. `upbit/spot/main/trade/2026-05`)
3. Shadow verification (read-only / permission-safe endpoint, dry-run payload 까지)
4. Grace window (default 24h, max 72h)
5. Cutover (`active_key_id` 전환 + process 재시작)
6. Ledger reconcile (전환 전후 주문/체결/잔고/수수료/미체결 대조)
7. Old key revoke (grace window 종료 후 거래소 폐기)
8. Evidence 기록 (rotation_date / operator / exchange / account_alias / old_key_revoked / reconcile_result, raw secret 미기록)

### 7.8 Compromise emergency response

```
1. critical_stop 발동 (ADR-007 D7) — live submit 즉시 중지
2. Open order cancel (가능 시 API, 불가 시 거래소 UI 직접)
3. Key revoke (거래소 console)
4. Risk freeze — risk policy amendment 권한 lock (limit 상향 / live 재개 금지)
5. Ledger reconcile (침해 의심 시점부터 모든 주문/체결/입출금/잔고)
6. New key issue (원인 확인 전 live 미연결)
7. Post-incident amendment — ADR-007 risk policy 손실 한도 / symbol allowlist / order size cap / cooldown 재검토
```

Live 재개 조건: critical_stop 해제 + 새 key active + reconcile complete + risk policy 확인.

### 7.9 Pre-commit + CI scan

- 도구: gitleaks + trufflehog (둘 다 CI 권장, local pre-commit = gitleaks fast scan)
- `.gitignore` (실수 방지, 보안 장치 아님):
  ```
  .env / .env.* (단 !.env.example) / secrets.* / *.key / *.pem / *.p12 / *.age.key / .op-session
  ```
- Scan rule: Bithumb connect key + Upbit access key + generic high entropy + JWT-like token + known env var names

### 7.10 Operation ledger (operator authority)

```python
@dataclass(frozen=True)
class OperationEvent:
    operator_id: str        # 'local-user' or 사용자 alias
    role: Literal["operator", "secret_holder"]
    action: str             # rotate_key / amend_risk / live_start / live_stop / etc.
    exchange: str
    account_alias: str
    timestamp: datetime
    result: Literal["success", "failure"]
    evidence_ref: str       # operation log entry id
```

Single user 단계 = operator + secret_holder 동일인. 그러나 같은 사람이라도 \"secret 변경\"과 \"risk 정책 완화\" 는 별도 event 로 기록. 향후 multi-operator 확장 가능 schema.

### 7.11 Backup

- Primary: 1Password 자체 복구
- Secondary: age-encrypted offline yaml (복호화 private key = 같은 머신 / cloud sync 폴더 미배치)
- **금지**: plain paper raw API secret (재발급 가능 → backup 목표 = 절차 + account access 보존)
- **금지**: online replication (Dropbox / iCloud / Drive)

### 7.12 Codex 적용

채택률 14/14. Sonnet 거부 0.

## 8-11

(Phase 2 N/A — doc-only Story.)
