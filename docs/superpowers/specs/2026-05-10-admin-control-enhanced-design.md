# Admin Control 페이지 강화 설계

**날짜**: 2026-05-10  
**관련 스토리**: MCT-125 (예정)  
**범위**: mctrader-web + mctrader-hub

---

## 1. 목표

`/admin_control` 페이지에서 현재 컨테이너/엔진 상태와 유효 조작을 명확하게 표시한다.

- 각 엔진/컨테이너의 현재 상태를 페이지 진입 즉시 확인 가능
- 현재 상태에서 유효한 버튼만 활성화 (SM 충돌 사전 방지)
- 재시작 등 전환 중 상태를 실시간으로 표현 (stopping → starting → running)
- CPU/메모리 리소스 사용량을 Prometheus에서 조회해 inline 표시
- Signal Worker 5개 컨테이너 개별 및 전체 제어
- Prometheus에 엔진 상태 Gauge를 노출해 모니터링 가시성 확보

---

## 2. 아키텍처 변경 범위

### 2-1. mctrader-web — 신규 파일

| 파일 | 역할 |
|------|------|
| `api/admin/signal_control.py` | Signal Worker Docker 제어 라우터 |
| `api/admin/signal_status.py` | Signal Worker 컨테이너 상태 조회 라우터 |
| `api/admin/metrics.py` | `/metrics` Prometheus exposition 엔드포인트 |

### 2-2. mctrader-web — 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `api/main.py` | 신규 라우터 3개 등록 |
| `dashboard/pages/11_admin_control.py` | 전면 재구성 (상태 표시 + 폴링 + Signal Worker 섹션) |

### 2-3. mctrader-hub — 설정 변경

| 파일 | 변경 내용 |
|------|-----------|
| `monitoring/prometheus.yml` | `mctrader-web` scrape job 추가 (port 7821) |
| `compose.yml` | mctrader-web `api` 서비스에 Docker 소켓 마운트 추가 |

---

## 3. 신규 API 엔드포인트

### `GET /admin/status/signal-workers`

Signal Worker 5개 컨테이너의 Docker 상태 + Prometheus 리소스 조회.

```python
class SignalWorkerStatus(BaseModel):
    worker_id: str           # "fear-greed" | "ecos" | "kimchi" | "announcement" | "coinglass"
    container_name: str      # "signal-fear-greed" 등
    docker_state: str        # "running" | "stopped" | "restarting" | "exited" | "paused"
    cpu_percent: float | None
    mem_mb: float | None
    uptime_seconds: float | None

class SignalWorkersStatusResponse(BaseModel):
    workers: list[SignalWorkerStatus]
    fetched_at: str          # ISO8601 UTC
```

- 인증: viewer+ (기존 RBAC)
- Docker SDK로 컨테이너 상태 조회
- Prometheus HTTP API (`http://prometheus:9090/api/v1/query`)에서 cadvisor CPU/MEM 조회
  - `container_cpu_usage_seconds_total{name="signal-{worker}"}`
  - `container_memory_usage_bytes{name="signal-{worker}"}`

### `POST /admin/signal/{worker_id}/{verb}`

- `worker_id`: `fear-greed` | `ecos` | `kimchi` | `announcement` | `coinglass`
- `verb`: `start` | `stop` | `restart`
- 인증: operator+ (기존 RBAC)
- Idempotency-Key 헤더 지원 (기존 패턴 ADR-016)
- Docker SDK로 컨테이너 제어 → audit log 기록 (기존 audit_db 패턴)
- `restarting` 중 재요청: 409 Conflict 반환
- 허용 전환 테이블:

| 현재 상태 | start | stop | restart |
|-----------|-------|------|---------|
| running   | 409   | ✓    | ✓       |
| stopped / exited | ✓ | 409 | 409  |
| restarting | 409  | 409  | 409     |
| paused    | ✓    | ✓    | ✓       |

### `GET /metrics`

Prometheus exposition format. `prometheus_client` 라이브러리 사용.

```
# 엔진 상태 numeric encoding
# 0=stopped, 1=starting, 2=running, 3=stopping, 4=degraded, 5=crashed, 6=queued, 7=cancelling
mctrader_engine_state{engine_class="collector",engine_id="collector-default"} 2
mctrader_engine_state{engine_class="paper_runner",engine_id="paper_runner-default"} 0
mctrader_engine_state{engine_class="backtest",engine_id="backtest-idle"} 0
mctrader_engine_state{engine_class="wfo",engine_id="wfo-idle"} 0

# Signal Worker up/down
mctrader_signal_worker_up{worker="fear-greed"} 1
mctrader_signal_worker_up{worker="ecos"} 1
mctrader_signal_worker_up{worker="kimchi"} 1
mctrader_signal_worker_up{worker="announcement"} 1
mctrader_signal_worker_up{worker="coinglass"} 0

# Collector heartbeat age
mctrader_collector_heartbeat_age_seconds{engine_id="collector-default"} 3.2
```

- 인증 불필요 (Prometheus scraper가 직접 호출)
- `/metrics` 경로는 기존 FastAPI 라우터에 추가

---

## 4. Prometheus 설정 변경

### monitoring/prometheus.yml 추가

```yaml
- job_name: mctrader-web
  static_configs:
    - targets: ['mctrader-web-api:7821']
  metrics_path: /metrics
  scrape_interval: 15s
```

### compose.yml 변경 (mctrader-hub)

mctrader-web 스택은 별도 repo에서 관리되므로, **mctrader-web repo의 compose.yml** (`api` 서비스)에 Docker 소켓 마운트 추가:

```yaml
services:
  api:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Signal Worker 제어용
```

---

## 5. Streamlit 페이지 재구성 (11_admin_control.py)

### 5-1. 페이지 구조

```
┌─────────────────────────────────────────────┐
│ 상단 요약 바: 엔진 N/5 running · Signal N/5 up │
│             마지막 조회 Xs 전 · 자동 갱신 중    │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ 섹션: 엔진 프로세스                           │
│  Collector  [● RUNNING]  hb 2s · 업타임 4h  │
│  [START▪] [STOP] [RESTART]  CPU 0.3% 42MB  │
│  ─────────────────────────────────────────  │
│  Paper Runner  [● STOPPED]                  │
│  [START] [STOP▪] [RESTART▪]                 │
│  (반복...)                                   │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ 섹션: Signal Worker 컨테이너   [전체 START/STOP/RESTART] │
│  ┌──────────────┐ ┌──────────────┐          │
│  │ fear-greed   │ │ ecos         │          │
│  │ ● UP         │ │ ● UP         │          │
│  │ CPU/MEM      │ │ CPU/MEM      │          │
│  │ [S▪][STOP][R]│ │ [S▪][STOP][R]│          │
│  └──────────────┘ └──────────────┘          │
│  (2열 그리드, 5개)                           │
└─────────────────────────────────────────────┘
```

### 5-2. 상태 전환 진행 표시

전환 중 상태(starting / stopping / restarting)가 감지되면 스텝 UI 표시:

```
[● running] → [⟳ stopping] → [⟳ starting] → [● running]
                  ^현재 단계 색상 강조
```

- 현재 단계: teal(`#17a2b8`) + 애니메이션 pulse
- 완료 단계: 회색
- 다음 단계: 회색(대기)
- 모든 버튼 비활성화 (전환 완료 전)

### 5-3. Polling 주기

| 상태 | 갱신 주기 |
|------|----------|
| 평온 (all running/stopped) | 10초 |
| 전환 감지 (any starting/stopping/restarting) | 2초 |
| 액션 직후 | 즉시 1회 재조회 → 2초 polling |

구현: `st.empty()` placeholder + `time.sleep(N)` + `st.rerun()`

### 5-4. 유효 버튼 활성화 규칙

엔진 프로세스 (ADR-015 SM 기반):

| SM state | start | stop | restart |
|----------|-------|------|---------|
| stopped / cancelled / failed | ✓ | ✗ | ✗ |
| running / completed | ✗ | ✓ | ✓ |
| starting / stopping | ✗ | ✗ | ✗ |
| degraded | ✗ | ✓ | ✓ |
| queued (oneshot) | trigger▪ | ✗ | cancel만 |
| cancelling (oneshot) | trigger▪ | ✗ | ✗ |

> **One-shot 엔진(backtest, wfo)**: `start/stop/restart` 대신 `trigger/cancel` 동사 사용. SM state가 stopped/failed/cancelled이면 trigger 활성, queued/running/cancelling이면 cancel 활성.

Signal Worker (Docker state 기반): 위 `POST /admin/signal` 허용 전환 테이블과 동일.

---

## 6. 의존성 추가

mctrader-web `pyproject.toml`:
- `docker` (docker-py SDK) — Signal Worker Docker 제어
- `prometheus_client` — `/metrics` 엔드포인트 노출

---

## 7. 테스트 계획

| 항목 | 방법 |
|------|------|
| `GET /admin/status/signal-workers` | Docker SDK mock + Prometheus mock |
| `POST /admin/signal/{worker}/{verb}` | 허용/차단 전환 테이블 커버리지 |
| `GET /metrics` | exposition 포맷 파싱 검증 |
| 버튼 활성화 로직 | SM state별 `_allowed_verbs()` unit test |
| 전환 상태 진행 표시 | 수동 E2E (자동화 어려움) |

---

## 8. 제외 범위

- `10_admin_overview.py` 변경 없음 (기존 역할 유지)
- Grafana 대시보드 업데이트 (별도 스토리)
- Signal Worker 이외의 Docker 컨테이너 제어 (postgres, redis 등) — 현 스코프 외
