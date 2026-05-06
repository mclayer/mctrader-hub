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
collector-NODE_A          # heartbeat node_id = "NODE_A" 와 동일 byte-string 의 instance_token 부 (Invariant 1)
collector-seoul-01        # heartbeat node_id = "seoul-01" 인 경우
paper_runner-default
backtest-01J9ABCDEFG...
wfo-01J9XYZ...
market_gw-bithumb-live
```

### Invariant

1. **Heartbeat node_id ↔ control engine_id 매핑 (collector 한정)**:
   `engine_id == f"collector-{heartbeat.node_id}"`. mctrader-web control plane 이 heartbeat sink 의 `node_id` (예: `NODE_A`) 를 읽어 `collector-` prefix 를 부착하여 `engine_id` (예: `collector-NODE_A`) 를 합성한다. mctrader-data heartbeat writer 변경 0 (heartbeat schema v1 immutable). 다른 engine_class (paper_runner / backtest / wfo / market_gw) 는 heartbeat 미발신이므로 본 invariant N/A — 해당 engine 의 `engine_id` 는 ADR-014 control plane / static config / one-shot RunId 가 발번한다.
2. **engine_class prefix**: 항상 위 5 token 중 하나로 시작. unknown prefix 는 control plane 이 400 reject.
3. **case-sensitive**: 본 규칙의 prefix (5 token) 는 소문자. instance_token 부분은 ASCII alphanumerics + `-` + `_` 허용 (대문자 허용 — 예: `NODE_A` heartbeat node_id 보존). 공백 / non-ASCII 금지. regex: `^(collector|paper_runner|backtest|wfo|market_gw)-[A-Za-z0-9_-]{1,64}$`.
4. **stability**: 일단 발급된 `engine_id` 는 lifetime 동안 불변. instance 재시작 시 동일 id 재사용 (audit log + SM history 연결성 보장).
5. **one-shot transient**: backtest / wfo 는 매 run 마다 신규 RunId 부여 — terminal state 후 동일 id 재사용 금지 (ADR-015 SM transition rule).

## 사용처 (소비처 매핑)

| 소비처 | 필드명 | 본 규칙 적용 |
|--------|--------|--------------|
| heartbeat schema v1 (`mctrader-data`) | `node_id` | collector 의 instance_token 부 (mctrader-web control plane 이 `collector-` prefix 부착하여 `engine_id` 합성, Invariant 1) |
| `/admin/status/*` response | `engine_id` | 그대로 |
| `/admin/control/*` request body | `engine_id` | 그대로, 400 검증 |
| audit_log (ADR-016) | `engine_class`, `engine_id` 두 컬럼 분리 | engine_class 는 token, engine_id 는 full |
| Streamlit dashboard | enumerate 가능한 list | heartbeat sink 동적 (collector) + static config (paper_runner / market_gw) + one-shot RunId 합집합 |

## 변경 정책

본 contract 은 v1. 변경 시 v2 신규 파일 + 호환성 ADR. v1 은 deprecation period (≥ 1 release) 후 archive.
