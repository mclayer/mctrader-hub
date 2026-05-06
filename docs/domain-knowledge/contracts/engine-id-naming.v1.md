# Engine ID naming convention (v1)

- **Status**: Active
- **Date**: 2026-05-06
- **Story**: MCT-97
- **Author**: ArchitectAgent (chief) + CodebaseMapperAgent (deputy)

## 목적

Admin Engine Control Panel (MCT-97) 의 control plane (`/admin/control/*`) 와 status plane (`/admin/status/*`) 가 사용하는 `engine_id` 표기를, mctrader-data heartbeat schema (v1) 의 `node_id` 와 unify.

heartbeat schema SSOT: [`heartbeat-schema.v1.md`](heartbeat-schema.v1.md)

## 규칙

### 표기 형식

`<engine_class>-<instance_token>`

| Engine class (token) | 의미 | Instance token 규칙 |
|----------------------|------|---------------------|
| `collector`          | mctrader-data collector (HA 다중 노드) | 노드 alias (`A`, `B`, `seoul-01` 등) — 운영자 결정 |
| `paper_runner`       | mctrader-engine PaperRunner | `default` 단일 (single-active-session enforcement, MCT-50) |
| `backtest`           | mctrader-engine BacktestExecutor (one-shot) | 매 trigger 시 `<RunId>` (UUID4 또는 ULID) |
| `wfo`                | mctrader-engine WFO orchestrator (one-shot) | 매 trigger 시 `<RunId>` |
| `market_gw`          | market gateway adapter | `<exchange>-<env>` 형식 (`bithumb-live`, `bithumb-paper`) |

### 예시

```
collector-A
collector-seoul-01
paper_runner-default
backtest-01J9ABCDEFG...
wfo-01J9XYZ...
market_gw-bithumb-live
```

### Invariant

1. **Heartbeat node_id ↔ control engine_id 일치**: collector heartbeat 의 `node_id` 는 본 규칙의 `engine_id` 와 동일 byte-string. heartbeat sink → control plane SM 매칭의 키.
2. **engine_class prefix**: 항상 위 5 token 중 하나로 시작. unknown prefix 는 control plane 이 400 reject.
3. **case-sensitive**: 모두 소문자 + ASCII alphanumerics + `-` + `_`. 공백 / non-ASCII 금지.
4. **stability**: 일단 발급된 `engine_id` 는 lifetime 동안 불변. instance 재시작 시 동일 id 재사용 (audit log + SM history 연결성 보장).
5. **one-shot transient**: backtest / wfo 는 매 run 마다 신규 RunId 부여 — terminal state 후 동일 id 재사용 금지 (ADR-015 SM transition rule).

## 사용처 (소비처 매핑)

| 소비처 | 필드명 | 본 규칙 적용 |
|--------|--------|--------------|
| heartbeat schema v1 (`mctrader-data`) | `node_id` | collector 의 instance_token 부 |
| `/admin/status/*` response | `engine_id` | 그대로 |
| `/admin/control/*` request body | `engine_id` | 그대로, 400 검증 |
| audit_log (ADR-016) | `engine_class`, `engine_id` 두 컬럼 분리 | engine_class 는 token, engine_id 는 full |
| Streamlit dashboard | enumerate 가능한 list | heartbeat sink 동적 + static config 합집합 |

## 변경 정책

본 contract 은 v1. 변경 시 v2 신규 파일 + 호환성 ADR. v1 은 deprecation period (≥ 1 release) 후 archive.
