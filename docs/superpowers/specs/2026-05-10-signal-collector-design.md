---
title: mctrader-signal-collector — 외부 시그널 수집 서비스
date: 2026-05-10
status: approved
author: Sonnet decider (mccho8865)
mctrader_epic_key: TBD
related_adr:
  - ADR-002 (TradeExecutor 3 mode — 시그널 소비는 engine 측)
out_of_scope:
  - 시그널 → 주문 직접 연결 (engine 책임)
  - ML 피처 엔지니어링 / 모델 학습
  - Twitter/X / Reddit 소셜 소스 (Tier 3, 추후 검토)
  - Glassnode / FRED (Tier 3)
---

# mctrader-signal-collector — 외부 시그널 수집 서비스

## 0. 개요 (Why)

mctrader 는 현재 Bithumb + Upbit OHLCV / WebSocket tick 만 수집한다. 거래 판단에 필요한 **외부 컨텍스트** (뉴스, 한국 리테일 수급, 글로벌 파생상품 압력, 시장 레짐) 가 없으면 엔진이 가격 패턴만 보고 결정한다.

본 Epic 은 Tier 1 외부 시그널 6종을 **`mctrader-signal-collector`** 신규 독립 서비스로 수집해 Redis Stream 에 publish 한다. Engine 은 Redis Stream 을 subscribe 해 포지션·리스크 결정에 반영한다.

**채택 접근법 — 별도 `mctrader-signal-collector` 서비스 (접근법 B)**
- 소스별 독립 프로세스 → 장애 격리
- 이벤트 드리븐(공지 모니터링) + 폴링(지표) 자연스럽게 혼용
- Engine 과 완전히 decoupled (Redis Stream 인터페이스만 공유)

---

## 1. 결정 stack

| # | 결정 | 채택 | 거부 |
|---|---|---|---|
| 1 | 서비스 배치 | **신규 독립 리포 `mctrader-signal-collector`** | mctrader-data 확장 / Hub compose sidecar |
| 2 | Engine 인터페이스 | **Redis Stream `signals:{kind}`** | Postgres polling / HTTP webhook |
| 3 | 스토리지 cold | **DuckDB warm + Postgres cold (archiver 별도)** | MinIO only / DuckDB only |
| 4 | Stale 폴백 | **neutral 시그널 publish** (값 없음, reason=stale) | 마지막 값 유지 / 퍼블리시 중단 |
| 5 | 공지 감지 방식 | **HTTP 폴링 (15초)** + dedup by announcement_id | WebSocket / Telegram 패스트패스 (v2 검토) |
| 6 | Worker 실행 단위 | **독립 Python 프로세스** (Docker 서비스별 1 컨테이너) | asyncio 단일 프로세스 내 멀티 태스크 |
| 7 | 인증 시크릿 | **compose env / `.env`** (기존 hub 패턴 일관성) | Vault / k8s Secret |
| 8 | 모니터링 | **Prometheus exporter `/metrics`** (freshness·에러율) + Grafana (기존 스택 재활용) | 별도 alert 서비스 |

---

## 2. 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│              mctrader-signal-collector                          │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ fear_greed    │  │kimchi_premium │  │    ecos       │       │
│  │ (5분 폴링)    │  │ (1분 폴링)    │  │ (일별 폴링)   │       │
│  └──────┬────────┘  └──────┬────────┘  └──────┬────────┘       │
│         │                  │                  │                 │
│  ┌──────┴──────────────────┴──────────────────┴────┐           │
│  │              publisher.py (Redis Stream)         │           │
│  │           signals:{kind}  XADD maxlen 10000      │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐                          │
│  │ announcement  │  │  coinglass    │                          │
│  │ (15초 폴링)   │  │ (1분 폴링)    │                          │
│  └──────┬────────┘  └──────┬────────┘                          │
│         │                  │                                   │
│  ┌──────┴──────────────────┴────────┐                          │
│  │     health.py  /metrics (9200)   │                          │
│  └──────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
         │ Redis Stream
         ▼
┌─────────────────────┐     ┌──────────────────────┐
│  mctrader-engine    │     │  signal-archiver      │
│  (subscribe)        │     │  DuckDB warm          │
│  포지션/리스크 결정  │     │  Postgres cold        │
└─────────────────────┘     └──────────────────────┘
```

---

## 3. Redis Stream 스키마

스트림 키: `signals:{kind}`

| kind | 내용 | TTL (maxlen) |
|------|------|-------------|
| `fear_greed` | 공포탐욕지수 | 10,000 |
| `kimchi_premium` | 김치 프리미엄 % | 10,000 |
| `ecos_fx` | KRW/USD 환율 | 1,000 |
| `announcement` | 거래소 공지 이벤트 | 50,000 |
| `coinglass` | 청산·OI·펀딩비 | 10,000 |

**공통 메시지 필드:**
```json
{
  "kind": "fear_greed",
  "ts": "2026-05-10T12:00:00Z",
  "source": "alternative.me",
  "value": 72,
  "label": "Greed",
  "stale": false,
  "raw": { ... }
}
```

**Stale 폴백 메시지:**
```json
{
  "kind": "fear_greed",
  "ts": "2026-05-10T12:05:00Z",
  "source": "alternative.me",
  "stale": true,
  "reason": "upstream_timeout",
  "value": null
}
```

---

## 4. Worker 상세

### 4-1. fear_greed (Alternative.me)
- **엔드포인트:** `https://api.alternative.me/fng/?limit=1`
- **폴링 간격:** 5분 (API 5분마다 업데이트)
- **인증:** 없음
- **시그널 활용:** 0-24=Extreme Fear / 25-49=Fear / 50-74=Greed / 75-100=Extreme Greed → engine 레짐 스로틀

### 4-2. kimchi_premium (CryptoQuant)
- **엔드포인트:** CryptoQuant REST API `korea_premium_index`
- **폴링 간격:** 1분
- **인증:** `CRYPTOQUANT_API_KEY` env
- **시그널 활용:** 프리미엄 % + z-score + 기울기 → 한국 리테일 수급 레짐

### 4-3. ecos (한국은행 ECOS API)
- **엔드포인트:** `https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/1/731Y001/D/{date}/{date}`
- **폴링 간격:** 일별 (06:00 KST 갱신 시점 이후 1회)
- **인증:** `ECOS_API_KEY` env
- **시그널 활용:** USD/KRW → kimchi_premium 계산 정규화 의존성

### 4-4. announcement (Upbit + Bithumb)
- **Upbit 엔드포인트:** `https://upbit.com/service_center/notice` HTML 파싱 (Upbit Open API 에 공지 전용 엔드포인트 없음 — 확인됨)
- **Bithumb 엔드포인트:** `https://www.bithumb.com/react/customer-support/notice/list` HTML 파싱
- **폴링 간격:** 15초
- **Dedup:** `announcement_id` (제목+날짜 해시)로 이미 처리된 공지 Redis Set에 기록
- **분류:** 상장(listing) / 상장폐지(delisting) / 입출금 중단 / 점검 / 마켓 추가
- **시그널 활용:** 상장 이벤트 → engine 이벤트 모드 진입 (첫 2h 지정가 전용, spread 제어)

**Upbit 상장 공지 포팅 참고:**
- 2025 데이터: 상장 공지 후 17~169% 펌프, 최초 2시간은 지정가만 허용
- 공지 감지 → 심볼 추출 → KRW 마켓 매핑 → `signals:announcement` publish

### 4-5. coinglass (CoinGlass)
- **엔드포인트:** CoinGlass REST API (청산, OI, 펀딩비, 롱숏 비율)
- **폴링 간격:** 1분
- **인증:** `COINGLASS_API_KEY` env
- **시그널 활용:** 청산 급등·OI 팽창·펀딩 극단값·롱숏 불균형 → 브레이크아웃 확인 또는 혼잡 리스크 필터

---

## 5. 파일 구조

```
mctrader-signal-collector/
├── workers/
│   ├── base_worker.py       # 추상 기반: poll_once(), on_error(), publish()
│   ├── fear_greed.py
│   ├── kimchi_premium.py
│   ├── ecos.py
│   ├── announcement.py      # Upbit + Bithumb 공지 파서 포함
│   └── coinglass.py
├── core/
│   ├── publisher.py         # Redis Stream XADD, stale 폴백 공통
│   ├── dedup.py             # Redis Set 기반 announcement dedup
│   └── health.py            # Prometheus /metrics 노출 (freshness, error_count)
├── tests/
│   ├── test_fear_greed.py
│   ├── test_kimchi_premium.py
│   ├── test_ecos.py
│   ├── test_announcement.py  # Upbit/Bithumb HTML fixture 기반 파서 테스트
│   └── test_coinglass.py
├── Dockerfile
├── compose.yml              # 개발용 (redis 포함)
├── pyproject.toml
└── .env.example
```

---

## 6. base_worker 계약

```python
class BaseWorker(ABC):
    kind: str
    interval_seconds: int

    @abstractmethod
    def poll_once(self) -> dict:
        """외부 API 호출 → raw dict 반환. 실패 시 예외 raise."""

    def run(self):
        while True:
            try:
                raw = self.poll_once()
                self.publisher.publish(self.kind, raw, stale=False)
                self.health.record_success(self.kind)
            except Exception as e:
                self.publisher.publish(self.kind, {}, stale=True, reason=str(e))
                self.health.record_error(self.kind)
            time.sleep(self.interval_seconds)
```

---

## 7. Hub compose.yml 통합

기존 `mctrader-hub/compose.yml` 에 signal-collector 서비스 추가:

```yaml
signal-fear-greed:
  image: mctrader-signal-collector:latest
  command: ["python", "-m", "workers.fear_greed"]
  environment:
    - REDIS_URL=redis://redis:6379
  networks: [mctrader_net]
  restart: unless-stopped

signal-kimchi-premium:
  image: mctrader-signal-collector:latest
  command: ["python", "-m", "workers.kimchi_premium"]
  environment:
    - REDIS_URL=redis://redis:6379
    - CRYPTOQUANT_API_KEY=${CRYPTOQUANT_API_KEY}
  networks: [mctrader_net]
  restart: unless-stopped

signal-ecos:
  image: mctrader-signal-collector:latest
  command: ["python", "-m", "workers.ecos"]
  environment:
    - REDIS_URL=redis://redis:6379
    - ECOS_API_KEY=${ECOS_API_KEY}
  networks: [mctrader_net]
  restart: unless-stopped

signal-announcement:
  image: mctrader-signal-collector:latest
  command: ["python", "-m", "workers.announcement"]
  environment:
    - REDIS_URL=redis://redis:6379
  networks: [mctrader_net]
  restart: unless-stopped

signal-coinglass:
  image: mctrader-signal-collector:latest
  command: ["python", "-m", "workers.coinglass"]
  environment:
    - REDIS_URL=redis://redis:6379
    - COINGLASS_API_KEY=${COINGLASS_API_KEY}
  networks: [mctrader_net]
  restart: unless-stopped
```

---

## 8. 테스트 계약

| 대상 | 테스트 유형 | 커버리지 목표 |
|------|------------|--------------|
| 각 Worker `poll_once()` | Unit + fixture mock | happy path + upstream 타임아웃 |
| `publisher.publish()` | Unit (fakeredis) | normal + stale 메시지 포맷 |
| announcement 파서 (Upbit/Bithumb) | Unit + HTML fixture | 상장·폐지·점검 분류 정확도 |
| dedup (announcement_id) | Unit | 중복 publish 방지 |
| `health.py` Prometheus 메트릭 | Unit | freshness_seconds, error_count |
| Integration (Redis 실제) | Integration | publish → XREAD 왕복 |

---

## 9. 리스크 및 완화

| 리스크 | 완화 |
|--------|------|
| 공지 HTML 구조 변경 → 무음 실패 | freshness 메트릭 알람 + 파서 fixture 테스트 CI 포함 |
| Telegram 스푸핑 (미사용이나 추후 검토 시) | 공식 HTTP 폴링 우선, Telegram 보조로만 사용 |
| 외부 API stale → 잘못된 주문 | stale 시 neutral publish 의무, engine 이 stale=true 시 시그널 무시 |
| 파생상품 데이터 오프쇼어 기준 → KRW 오판 | engine 에서 파생 시그널 weight 보수적으로 설정 |
| CryptoQuant / CoinGlass rate limit | 지수 백오프 + 에러 메트릭 노출 |

---

## 10. 구현 순서 (Codex 권고 반영)

1. **ECOS worker** — KRW/USD 정규화 의존성, 모든 kimchi 계산 선행 작업
2. **kimchi_premium worker** — FX 기반 완료 후 한국 특화 레짐 피처
3. **fear_greed worker** — 저복잡도, 외부 피처 파이프라인 E2E 검증
4. **core (publisher + health)** — 1~3 공통 기반, 1 착수 전 완성
5. **announcement worker** — Upbit 먼저, Bithumb 추가 (이벤트 파이프라인)
6. **coinglass worker** — 한국 네이티브 안정화 후 글로벌 파생 레이어

---

## 11. Phase 1 스코프 아웃 (추후 Epic)

**signal-archiver** (Architecture 다이어그램 내 점선 박스):
- DuckDB warm / Postgres cold 아카이빙은 Phase 1 스코프 아웃
- Phase 1 에서는 Redis Stream `maxlen` 으로 최신 N개만 유지
- 아카이빙은 별도 Story 로 분리

---

## 12. 스코프 아웃

- 시그널 → 주문 직접 실행 (engine 책임)
- ML 피처 스토어 / 모델 학습
- Twitter/X, Reddit 소셜 소스
- Glassnode (Tier 3, BTC/ETH 온체인 느림 + 비용 과대)
- FRED API (Tier 3, 너무 느린 업데이트)
- Telegram 패스트패스 (v2 검토)
