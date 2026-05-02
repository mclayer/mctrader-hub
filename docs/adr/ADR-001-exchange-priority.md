---
adr_id: ADR-001
title: 거래소 우선순위 — Bithumb #1 + Upbit #2 + ranked list
status: Accepted
date: 2026-05-02
related_story: MCT-1
category: market
supersedes: []
amends: []
---

# ADR-001: 거래소 우선순위 (Bithumb #1 + Upbit #2 + 한국 5-거래소 ranked list)

## Status

**Accepted** — 2026-05-02. MCT-1 Story Phase 1 PR 의 산출물.

## Context

mctrader = 개인 암호화폐 자동매매 platform (Python 3.11+, Parquet/DuckDB, Streamlit). KRW base. 6-repo 구조.

거래소 adapter 는 mctrader-market (interface) + mctrader-market-{exchange} (impl) 패턴. 첫 거래소 = Bithumb (사용자 사전 결정 — KRW base 한국 시장 진입, REST + WS 모두 가용, KRW pair 폭).

본 ADR 의 결정 범위:
1. "Bithumb 운영 안정 후 자연 확장 시" 추가할 #2 거래소 선정
2. 추가 순서 (#3, #4, #5) 까지 ranked list 산출
3. ranking 의 evaluation framework + scoring criteria 박제 — 향후 #2 actual activation 시점에 empirical re-validation 의 baseline

Trigger = 시간 기반 자연 확장 (Bithumb 6 개월+ 안정 운영 후). single-point failure 대비 (warm spare) 또는 자금 한계 분산 또는 종목 부재 보충은 본 ADR scope 외 (별도 future Story).

Scope = **한국 KRW 거래소 only**. 글로벌 (Binance/OKX/Bybit 등 USDT pair) 거래소는 base currency 가 KRW 단일에서 KRW+USDT 로 확장되는 변경 → 자금 관리 / OHLCV 스키마 (MCT-9) / Executor (MCT-2) 모두 영향 → 별도 future Story.

## Decision

### D1. Framework ranking vs Implementation sequence (분리)

본 ADR 은 두 ordering 을 분리 명시:

**Framework ranking** (10-dim API-first weighted score, 객관):

| 순위 | 거래소 | Score / 100 | 격차 |
|---:|---|---:|---|
| 1 | **Upbit** | **93.6** | — |
| 2 | **Bithumb** | **83.4** | -10.2 vs #1 |
| 3 | Coinone | 73.6 | -9.8 vs #2 |
| 4 | Korbit | 61.0 | -12.6 vs #3 |
| 5 | Gopax | 40.4 | -20.6 vs #4 |

**Implementation sequence** (사용자 사전 결정 build 순):

| build 순 | 거래소 | repo | Phase 의존 |
|---:|---|---|---|
| 1 | **Bithumb** | `mctrader-market-bithumb` (MCT-14) | Epic MCT-12 first end-to-end |
| 2 | **Upbit** | `mctrader-market-upbit` (future Story) | Bithumb 안정 운영 후 자연 확장 (D-trigger) |
| 3 | Coinone | future | activation 시점 framework re-validate |
| 4 | Korbit | future, low priority | 종목/유동성 약점 |
| 5 | Gopax | watchlist | regulatory 시점 의존 |

### D2. 핵심 결정

1. **Implementation #1 = Bithumb.** 사용자 사전 결정. framework 외 factors (lower fee 0.04%, NH농협 실명계좌, 구현 단순성, smaller-scale matched first-impl) 의 의식적 선택. §C5 "Bithumb-first 근거" 박제.
2. **Implementation #2 = Upbit.** framework score #1 (93.6) + 사용자 명시 ("upbit, bithumb 이렇게 가자") 양쪽 동의. Bithumb 안정 운영 후 자연 확장 trigger 발동 시 Upbit adapter build.
3. **#3 이후 = Coinone → Korbit → Gopax** (framework score 순). 단 activation 시점 framework re-validate 의무 (§C3).

### D3. Evaluation framework — 10 dimension API-first

자동매매 platform critical-path 가중. 사용자 framework A 결정 + Codex (codex-rescue, gpt-5.5 high) push-back 4 건 중 3 건 적용 후 최종 weights:

| Dimension | Weight | 비고 |
|---|---:|---|
| REST API 품질 | 15% | base layer 안정성 |
| WebSocket realtime | 15% | 실시간 시세 + 체결 stream |
| Rate limit / quota | 10% | bot 빈도 + multi-pair 동시 운영 |
| **주문 실행 semantics** | **10%** | tick size / min notional / partial fill / cancel race / idempotency / post-only/IOC/FOK (Codex push-back, 신규 분리) |
| Historical OHLCV depth | 8% | 백테스트 데이터 (mctrader-data 외부 보충 가능 → 10→8) |
| 유동성 | 15% | KRW pair top10 평균 일거래대금 |
| 종목 수 | 5% | liquidity-adjusted universe 기준 (Codex push-back, 10→5) |
| 수수료 (taker) | 7% | implicit cost 가 명시 fee 보다 큼 (Codex push-back, 10→7) |
| Regulatory | 10% | FIU 신고 + 은행 실명계좌 (gate 성격). Codex 15% 권장은 본인이 "gate 에 가깝다" 인정과 모순 → 10% 유지. |
| 출금/입금 안정성 | 5% | 자동매매 단계 비중 낮음 |
| **Total** | **100%** | |

### D4. Out-of-framework (activation re-validation checklist 로 분리)

- API key 운영 난이도 (발급 UX / IP whitelist / 권한 scope / rotation)
- Sandbox / testnet / dry-run 친화성
- 거래소별 사고 / 영업정지 history (regulatory 안에 부분 흡수)

→ 본 ADR 의 baseline ranking 에는 미반영. **실제 #2 (Upbit) adapter build 직전 empirical re-test 의무**.

### D5. Score matrix (1-5 scale, Confidence H/M/L, 5 거래소 모두)

| Dimension | Weight | Bithumb | Upbit | Coinone | Korbit | Gopax |
|---|---:|---|---|---|---|---|
| REST API 품질 | 15 | 4/M | 5/H | 4/M | 3/M | 2/L |
| WebSocket realtime | 15 | 4/M | 5/H | 4/M | 3/M | 2/L |
| Rate limit | 10 | 4/M | 4/H | 3/M | 3/L | 2/L |
| 주문 실행 semantics | 10 | 4/M | 4/M | 3/M | 3/L | 2/L |
| OHLCV depth | 8 | 4/M | 5/H | 4/M | 3/M | 2/L |
| 유동성 | 15 | 4/M | 5/H | 3/M | 2/M | 1/M |
| 종목 수 | 5 | 4/M | 5/H | 4/M | 2/M | 2/M |
| **수수료** | 7 | **5/H** | 4/M | 3/M | 3/M | 3/L |
| Regulatory | 10 | 5/H | 5/H | 5/H | 5/H | 3/M |
| 입출금 | 5 | 4/M | 4/M | 4/M | 4/M | 2/L |
| **Σ(점수×weight)** | | **417** | **468** | **368** | **305** | **202** |
| **Score / 100** | | **83.4** | **93.6** | **73.6** | **61.0** | **40.4** |

Bithumb 의 framework 내 distinguishing strength = 수수료 5/H (0.04% taker, Upbit 0.05% 보다 낮음). 그 외 dimension 은 Upbit 대비 -1점 (REST/WS/유동성/종목수/OHLCV) 또는 동률.

## Alternatives Considered

### A1. Liquidity-first framework (Q3 옵션 B)
- 유동성 20% / 종목수 15% / API+WS 25% / OHLCV 10% / 수수료 10% / Regulatory 10% / 출금 5% / Rate limit 5%
- **기각 사유**: 한국 top-5 거래소가 유동성 임계점 모두 충족 (Bithumb / Upbit 압도적, Coinone/Korbit/Gopax 도 단일 전략 수준 충분). 차이가 가장 크게 벌어지는 곳 = API 안정성 + WebSocket 지연. 자동매매는 1초 reconnect 실패 1회로도 손실 가능 → API-first 가 critical-path.

### A2. Balanced 9-axis 균등 가중 (Q3 옵션 C)
- 각 dimension 11.1%
- **기각 사유**: 가장 객관적이나 자동매매 platform 의 도메인 특화 가중치 손실. "모든 dimension 이 동등하다" 는 자동매매 critical path 분석과 충돌.

### A3. Trigger-only Story (Q1 옵션 D)
- 거래소 추가 trigger condition 만 정의, 실제 ranking 은 trigger 발생 시 별도 Story
- **기각 사유**: 사용자 의도 ("향후 추가 순서" — Q1 옵션 C 선택) 와 불일치. trigger 발생 시 ranking 새로 시작하면 시점 압박 하에 평가 → 의사결정 품질 저하.

### A4. Framework score 만으로 implementation sequence 결정 (Bithumb-first 사용자 사전 결정 무시)
- Upbit #1 → Bithumb #2 → Coinone → Korbit → Gopax (순수 framework score 순)
- **기각 사유**: 사용자 사전 결정 ("첫 거래소 = Bithumb" + "upbit, bithumb 이렇게 가자") 는 framework 외 factors (lower fee / NH농협 친숙도 / 구현 단순성 / smaller-scale matched first-impl) 의 의식적 선택. framework score 는 ranking 도구이지 사용자 의사결정의 sole basis 아님. framework 와 사용자 결정 충돌 시 양 ordering 모두 명시 (D1 분리) 가 정직함.
- 격차 10.2점이라 framework 외 factor 합산 영향이 그 이상이면 Bithumb-first 정당화 가능 — §C5 박제.

### A5. 글로벌 거래소 포함 (Q2 옵션 B/C)
- 한국 5 + 글로벌 (Binance/OKX/Bybit 등 USDT pair) 1-3
- **기각 사유**: base currency 확장 (KRW → KRW+USDT) 은 자금 관리 / OHLCV 스키마 / Executor 모두 영향. 본 ADR 의 단순 ranking decision 외 architectural 변경 동반 → 별도 future Story 가치 (Q2 옵션 D 선택).
- Trade-off 는 §Consequences C2 에 명시.

### A6. Framework 에 9 dimension 유지 (Codex P1 reject)
- 주문 실행 semantics 를 REST API 품질 안에 sub-가중치로 흡수
- **기각 사유**: Codex 가 정확히 지적 — "REST/WebSocket 점수가 높은 거래소가 자동매매 outcome 측면에서 과대평가될 위험". 주문 실행 semantics (idempotency / partial fill / cancel race) 는 시세 수집 layer 와 별개의 risk surface. 분리 필수.

### A7. Codex 의 full rebalance (P2 reject — partial 만 적용)
- REST 13% / WS 13% / Rate limit 9% / 주문실행 10% / OHLCV 7% / 유동성 16% / 종목수 5% / 수수료 7% / Regulatory 15% / 출금 5%
- **부분 기각 사유**: Regulatory 15% 권장은 Codex 본인이 "점수보다 gate 에 가깝다" 라고 인정한 항목과 모순. 한국 5 거래소가 모두 FIU 신고 + 은행 실명계좌 보유 사업자 (Bitsonic 등 minor 거래소는 처음부터 후보 제외) → regulatory 가 ranking 에서 차이를 만드는 dimension 이 아님 (Gopax 만 -2 점). 10% 유지가 적절.
- 종목수 5% / 수수료 7% / OHLCV 8% (10→8 partial) 는 강한 근거로 적용.

### A8. API key / sandbox / 사고 history 를 별도 dimension 추가 (Codex P3 reject — checklist 로 이관)
- framework 12-dim 으로 확장
- **기각 사유**: 본 ADR 단계 = public-knowledge baseline. 운영 난이도 / sandbox 가용성 / 시점 민감 사고 history 는 cell 별 confidence L 가 다수 → framework 안 점수가 오히려 noise 도입. activation 시 empirical re-test 책임으로 이전 (D3) 이 더 정직.

## Consequences

### C1. 단기 (즉시)

- **#2 = Upbit 으로 결정 박제.** Bithumb 안정 운영 후 자연 확장 trigger (D1) 발동 시 Upbit adapter build 시작.
- 새 repo `mclayer/mctrader-market-upbit` 가 #2 build 시점에 생성. mctrader-market interface (MCT-13) 에 의존.
- mctrader-market interface (MCT-13) 의 Candle / OrderBook / Order / Protocol 정의 시 Upbit / Coinone / Korbit / Gopax 의 구조 차이 (e.g. Upbit 의 trade event 형식, Coinone 의 nonce 방식) 까지 호환 가능한 abstraction 의무.

### C2. KRW-only scope trade-off (Codex push-back P4 박제 — 향후 scope 번복 방지)

본 ADR 이 "한국 KRW 거래소 only" 로 scope 한정한 결과로 다음 strategy space 가 차단:

- **Cross-exchange arbitrage**: 한국 / 글로벌 가격 차이 ("김치 프리미엄") 를 active 하게 활용한 arb 전략 불가능.
- **Hedge**: KRW-only 환경에서 BTC/USDT-perp 또는 옵션 등 derivatives 를 통한 hedge 불가능.
- **Capital efficiency**: 글로벌 venue 의 funding rate / leverage / margin product 미가용.
- **Price discovery**: 글로벌 거래량 우위 venue 의 즉각 가격 발견 직접 활용 불가 (한국 거래소 가격은 글로벌 가격에 lag 또는 premium 있음).

본 trade-off 는 사용자 명시 결정 (Q2=D "Korean only + 글로벌 별도 future Story") 의 의식적 선택. 향후 글로벌 venue 진출 ADR 에서 본 ADR 의 trade-off 를 명시 referencing 후 supersedes / amends 처리.

### C3. Activation re-validation checklist (실제 #2 add 직전 의무)

- [ ] **WebSocket 7일 soak test** — reconnect 횟수, heartbeat 누락, sequence gap, orderbook drift, message loss 기록
- [ ] **REST latency** — endpoint 별 p50/p95/p99, 429/5xx 빈도, retry 후 중복 주문 가능성, nonce/timestamp 오류 측정
- [ ] **Private API 소액 실주문** — market/limit, partial fill, cancel race, 미체결 조회, 체결 stream + REST reconciliation 검증
- [ ] **Rate limit 실측** — 계정 단위 / IP 단위 / endpoint 단위 / burst / sustained / 차단 해제 정책
- [ ] **API key 운영** — 발급 UX, IP whitelist, read/trade/withdraw 권한 분리 가용, key rotation 절차
- [ ] **Sandbox/testnet 부재 시** — mock replay + shadow mode 를 adapter acceptance criteria 에 포함
- [ ] **Regulatory 시점 확인** — FIU 신고 상태 / 은행 실명계좌 연동 / 사고 history / 영업정지 여부 재조회

위 checklist 미통과 시 #2 ranked candidate (= Coinone) 로 fallback 검토 (격차 20점 sensitivity 보장 → fallback 정당화 가능).

### C4. ranked list 재평가 trigger

다음 중 하나 발생 시 본 ADR 재평가 (amend 또는 supersede):

1. **Activation 시 empirical re-test 결과** baseline 점수와 단일 dimension 1점 이상 차이 (특히 confidence L cell)
2. **시점 민감 정보 변동**: 거래소 영업정지 / FIU 인가 취소 / 은행 실명계좌 단절 / 거래량 순위 5계단 이상 변동 / 수수료 정책 50% 이상 변동
3. **신규 한국 거래소 등장 또는 minor 거래소 메이저 진입**: 후보 set 변경
4. **사용자 strategy 변경**: arb / hedge / derivatives 가 mctrader scope 에 추가 (글로벌 venue ADR 트리거)

### C5. Bithumb-first implementation 근거 (out-of-framework, 추정 + 사용자 보강 대상)

framework score 기준 #1 = Upbit (93.6), Bithumb (83.4) 은 #2. 그러나 사용자 사전 결정 implementation sequence 는 Bithumb → Upbit. 격차 10.2점이라 framework 외 factor 가 합산 영향 ≥10.2점이면 Bithumb-first 합리적.

추정 Bithumb-first 근거 (사용자 본인 actual rationale 추후 보강 가능):

1. **수수료 cumulative 우위** — Bithumb 0.04% taker vs Upbit 0.05% — 자동매매 회전 시 long-run 손익 차이 substantial. framework 5/H vs 4/M 부분 반영했으나 자동매매 회전율 가정에 따라 cumulative impact 가 framework 점수보다 클 수 있음.
2. **은행 친숙도** — NH농협 실명계좌 (사용자 기존 농협 account 활용 추정). framework 외 personal-banking onboarding factor.
3. **구현 단순성** — Bithumb signature 인증 vs Upbit JWT — first-impl 학습 곡선 차이. framework 외 onboarding cost factor.
4. **Smaller-scale matched** — 개인 자동매매 first-impl 단계의 거래량 폭주 / rate limit risk 가 Bithumb 이 Upbit 보다 낮을 수 있음.
5. **Single-exchange sufficient liquidity** — KRW BTC/ETH main pair 의 Bithumb 유동성은 single-exchange 자동매매 임계점 충족.

본 추정 근거는 사용자 본인이 추후 정정/보강 가능. 정정 시 본 ADR amend (Status: Accepted → Amended).

### C6. Framework re-validate trigger (Bithumb 한정)

Bithumb adapter (mctrader-market-bithumb, MCT-14) build 후 다음 발생 시 framework score (현재 83.4) 재산출 + 본 ADR amend:

- empirical operation 6 개월+ 결과로 cell 점수 1점 이상 변동 (특히 confidence M cell)
- 거래소 정책 변경 (수수료 / rate limit / KRW pair / regulatory)
- mctrader 의 strategy 가 Bithumb 의 framework 약점 (e.g. 유동성, OHLCV depth) 에 의존도 증가

## Cross-references

- **MCT-1 Story** ([`../stories/MCT-1.md`](../stories/MCT-1.md)) — 본 ADR 의 source Story (Phase 1 PR).
- **MCT-2 (TradeExecutor)** — 향후 ADR. 3 mode (backtest/paper/live) 별 거래소 호출 정책 의존.
- **MCT-8 (API key secret 관리)** — 향후 ADR. Upbit / Bithumb 별 secret 격리.
- **MCT-9 (OHLCV 스키마 v1)** — 향후 ADR. Upbit / Bithumb candle 구조 차이 흡수 의무.
- **MCT-13 (mctrader-market interface)** — 향후 Story. Candle / OrderBook / Order Protocol 정의.
- **CFP-60 (cross-repo Epic + debut-audit)** — 의존 (Epic MCT-12 시작 전 merge 필수, 본 MCT-1 ADR 은 무관).
- **Codex 의견 dispatch** — Sonnet decider protocol (CFP-59 / ADR-019 — codeforge wrapper) 적용. 본 ADR §Decision D2 의 framework rebalance 가 Codex push-back 3건 적용 결과.

## 데뷔작 audit pre-Story note

본 Story (MCT-1) 진행 중 codeforge plugin 에 추가 install-time finding 발견 안 됨 (기존 4 finding #115~#118 외). Codex 7-카테고리 평가는 향후 정식 Story 종료 시점에 적용 예정. 단, **Codex agent (codex-rescue) 의 직접 file write 행동** 발견 — 추후 plugin-codeforge 측 finding 후보로 검토 (Codex agent 가 task dispatch 시 결과 반환만 하지 않고 docs/ 파일 직접 작성 → consumer 가 raw Codex draft 와 사용자 결정 synthesized 버전을 reconcile 하는 추가 비용 발생).
