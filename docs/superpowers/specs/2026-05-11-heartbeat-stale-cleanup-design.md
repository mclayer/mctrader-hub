# Heartbeat Stale 파일 누적 문제 해결 설계

**날짜**: 2026-05-11  
**관련 Story**: MCT-128 (mctrader-data), MCT-129 (mctrader-web)  
**배경**: `http://mctrader.mclayer.it/status` 페이지가 수십 개 컬럼으로 깨지는 운영 장애

---

## §1 문제 분석

### 근본 원인

`mctrader-data` collector 컨테이너가 재시작될 때마다 `socket.gethostname()` 반환값이 Docker 컨테이너 short ID (e.g. `6e495e91f663`)로 바뀐다. 이 값이 `node_id`로 사용되어 `heartbeat-{node_id}.json` 파일이 신규 생성된다. 구 파일은 삭제 로직이 없어 무기한 누적된다.

### 증상

`00_status.py` 의 `st.columns(len(result.nodes))` 가 11개(또는 그 이상) 컬럼을 생성해 페이지 레이아웃이 완전히 파괴된다.

### 실증 데이터 (2026-05-10 확인)

```
총 노드 11개, worst_level=2
활성(level=0): 2개 (6e495e91f663, 8d88f77d171a)
stale(level=2): 9개 (freshness 10~36시간)
```

---

## §2 설계 — 3레이어 A안

### 레이어 1: cli.py MCTRADER_NODE_ID env var 읽기 (mctrader-data)

**목적**: stale 파일 원천 차단 — 재시작 시 동일 파일명 덮어쓰기.

> **발견**: `mctrader-data/compose.yml`에 이미 `MCTRADER_NODE_ID: "NODE_BITHUMB_A"` / `"NODE_UPBIT_A"` 가 설정되어 있다. 단지 `cli.py`가 이 env var를 읽지 않아 `socket.gethostname()` (= container short ID)으로 fallback되는 것이 실제 버그.

**compose.yml은 변경 불필요.** `cli.py` 1줄만 수정:

```python
# 현재 (버그)
resolved_node_id = node_id if node_id is not None else _socket.gethostname()

# 수정 후
# 우선순위: --node-id CLI arg > MCTRADER_NODE_ID env var > socket.gethostname()
resolved_node_id = node_id or os.environ.get("MCTRADER_NODE_ID") or _socket.gethostname()
```

**scale-out 정책**: `NODE_BITHUMB_A`, `NODE_BITHUMB_B` 처럼 compose에 명시적으로 지정. 충돌 방지는 운영자 책임.

### 레이어 2: HeartbeatWriter 시작 시 stale 정리 (mctrader-data)

**목적**: 레이어 1 도입 이전에 누적된 파일 제거 + 설정 오류 안전망.

`HeartbeatWriter.start()` 에서 실행:

```
stale_cleanup_ttl = int(os.environ.get("MCTRADER_HEARTBEAT_STALE_CLEANUP_SECONDS", "300"))

for hb_file in manifest_dir.glob("heartbeat-*.json"):
    if hb_file.name == f"heartbeat-{self.node_id}.json":
        continue  # 자기 파일 보호
    try:
        age = time.time() - hb_file.stat().st_mtime
        if age > stale_cleanup_ttl:
            # TOCTOU guard: mtime 재확인 후 삭제
            if time.time() - hb_file.stat().st_mtime > stale_cleanup_ttl:
                hb_file.unlink(missing_ok=True)
                log.info("stale heartbeat removed: %s (age=%.0fs)", hb_file.name, age)
    except OSError as e:
        log.warning("stale cleanup failed for %s: %s", hb_file.name, e)
        # 실패해도 수집 시작 계속
```

**TTL 기준**: 300s (heartbeat interval 5s의 60배) → 활성 노드 false-positive 삭제 위험 없음.

**실패 처리**: OSError → warn 로그만, 예외 미전파. 정리 실패가 수집 시작을 막지 않음.

### 레이어 3: 00_status.py 방어적 렌더링 (mctrader-web)

**목적**: 레이어 1·2 미적용 환경 또는 미래 edge case 대비 최후 방어선.

노드 분류:

```python
active_nodes = [n for n in result.nodes if n.get("level", 2) < 2]
stale_nodes  = [n for n in result.nodes if n.get("level", 2) >= 2]
```

렌더링:

```
활성 노드 (level 0/1):
  st.columns(max(1, len(active_nodes)))
  → 기존 _render_node_card() 그대로

stale 노드 (level 2):
  st.divider()
  st.caption("⛔ Stale nodes (inactive)")
  for node in stale_nodes:
      with st.expander(f"⛔ {node_id} — {freshness:.0f}초 전", expanded=False):
          st.write(f"ws_state: {ws_state}")
```

`st.columns(0)` 방지: `max(1, len(active_nodes))` guard.

---

## §3 테스트 계획

### mctrader-data (레이어 1·2)

| 케이스 | 방법 |
|--------|------|
| MCTRADER_NODE_ID 우선순위 | `--node-id` > env var > hostname 순서 단위 테스트 |
| stale 정리 — TTL 초과 파일 삭제 | tmp dir + 가짜 heartbeat 파일 (mtime 조작) + `start()` 호출 → 삭제 확인 |
| stale 정리 — 자기 파일 보호 | 같은 node_id 파일은 mtime 무관 잔존 확인 |
| stale 정리 — 활성 파일 보호 | mtime < TTL 파일은 삭제 안 됨 확인 |
| stale 정리 — OSError 내성 | 읽기전용 파일에서 warn 로그 + 예외 미전파 확인 |

### mctrader-web (레이어 3)

| 케이스 | 방법 |
|--------|------|
| 활성 노드만 있을 때 | AppTest: `st.columns` 인자 = `len(active_nodes)` |
| stale 노드 포함 시 | AppTest: `st.expander` 존재 확인, 컬럼 수 = active 수만 |
| 활성 노드 0개일 때 | AppTest: `st.columns(1)` (guard 동작) |

---

## §4 엣지 케이스

| 시나리오 | 처리 |
|----------|------|
| rolling restart overlap (구/신 컨테이너 동시 write) | 동일 node_id → atomic rename(기존 구현)으로 마지막 writer 승리 |
| 볼륨 권한 오류로 정리 실패 | warn 로그 + 수집 계속 |
| MCTRADER_NODE_ID 미설정 (기존 배포) | hostname fallback → 기존 동작 유지, backward compatible |
| heartbeat 디렉터리 부재 | glob 0 hits → 정리 루프 스킵 |

---

## §5 마이그레이션

1. 레이어 2 배포 (mctrader-data PR): HeartbeatWriter 시작 시 기존 누적 파일 300s 기준 자동 정리
2. 레이어 1 배포 (compose 변경): MCTRADER_NODE_ID 적용 → 이후 재시작부터 stale 파일 원천 차단
3. 레이어 3 배포 (mctrader-web PR): UI guard 상시 적용

순서 무관하게 각 레이어가 독립적으로 유효함. 동시 배포 가능.

---

## §6 scope_manifest (초안 — PMOAgent Phase 2 산출)

```yaml
planned_adrs: 0
planned_files:
  # mctrader-data (compose.yml 변경 불필요 — 이미 NODE_ID 설정됨)
  - mctrader-data/src/mctrader_data/cli.py
  - mctrader-data/src/mctrader_data/heartbeat.py
  - mctrader-data/tests/test_heartbeat_stale_cleanup.py
  # mctrader-web
  - mctrader-web/src/mctrader_web/dashboard/pages/00_status.py
  - mctrader-web/tests/test_apptest_status_panel.py
planned_claude_md_sections: []
```
