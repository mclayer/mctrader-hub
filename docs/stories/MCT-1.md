---
story_key: MCT-1
status: phase:요구사항
component: market
type: brainstorm
related_adr: ADR-001
---

# MCT-1: 거래소 우선순위 (Bithumb 이후 자연 확장 후보 ranking)

- **Issue**: (manual flow — story-init.yml 미배포, F2 finding 의존)
- **Status**: phase:요구사항 (Phase 1 PR)
- **Type**: brainstorm Story (decision artifact)

## 1. 사용자 요구사항 (verbatim — story-section-1-immutable 강제)

mctrader 의 거래소 우선순위 결정. 첫 거래소는 Bithumb 으로 확정 (KRW base 한국 시장 진입). Bithumb 운영 안정 후 자연 확장 시 추가할 #2 한국 거래소를 선정. 향후 #3, #4, #5 의 추가 순서까지 평가 매트릭스 형식으로 ranked list 산출.

## 2. 도메인 해석

mctrader 가 자동매매 platform 이므로 거래소 선택은 단순 "많이 쓰는 곳" 이 아닌 **자동매매 critical path** (REST API 안정성 + WebSocket realtime + 주문 실행 semantics + rate limit) 가 우선 고려. Bithumb 은 사용자 사전 결정 (한국 진입 + REST/WS 모두 가용 + KRW pair 폭). 본 Story 의 핵심은 "Bithumb 다음에 무엇을 추가하는가".

"운영 안정 후 자연 확장" trigger (D) — Bithumb 6 개월+ 안정 운영 후 단순 확장 의도. Single-point failure 대비 (A trigger) 가 아니므로 #2 가 warm spare 일 필요는 없으나, framework 자체엔 자동매매 outcome 을 좌우하는 dimension 이 모두 들어가야 한다.

## 3. 관련 ADR

- **ADR-001 거래소 우선순위** ([`../adr/ADR-001-exchange-priority.md`](../adr/ADR-001-exchange-priority.md)) — 본 Story 의 결정을 ADR 형식으로 박제 (Context / Decision / Alternatives / Consequences).

향후 ADR 후보 (out-of-scope of MCT-1):
- ADR-XXX 글로벌 거래소 도입 (USDT pair, hedge / arb 가용성) — Q2 D 결정에 따라 별도 future Story
- ADR-XXX 거래소별 API key 운영 / secret 관리 정책 — MCT-8 에서 처리 예정

## 4. 관련 코드 경로

본 Story 는 doc-only (mctrader-hub governance). 실제 거래소 adapter 코드는 다른 repo:

- `mctrader-market` (interface) — Candle / OrderBook / Order Protocol 정의 (MCT-13)
- `mctrader-market-bithumb` (impl #1) — Bithumb HTTP + WS (MCT-14)
- `mctrader-market-upbit` (impl #2, future) — 본 Story 결정 후 새 repo 생성

## 5. 요구사항 확장 해석

### 5.1 Scope 분리

본 Story 는 **한국 KRW 거래소 5 후보의 ranking only**. 글로벌 (Binance/OKX/Bybit/Coinbase 등 USDT pair) 거래소는 별도 future Story 로 분리.

근거: 글로벌 거래소 도입은 base currency 가 KRW 단일에서 KRW + USDT 로 확장되는 변경 → 자금 관리 / OHLCV 스키마 (MCT-9) / Executor (MCT-2) 모두 영향. 본 Story 의 단순 ranking 결정 외 architectural 변경 동반 → 별도 ADR 가치.

### 5.2 Trigger 정의 (D)

primary trigger = 시간 기반 자연 확장. 보조 trigger:
- (A) Bithumb single-point failure → 별 사전 준비 의무 없음 (warm spare 미요구), 발생 시 본 ranked list 재참조해 #2 즉시 build
- (B) 자금 한계 분산 → 본 Story scope 외 future Story (자금 관리 ADR)
- (C) 종목 부재 보충 → 본 Story scope 외 (전략 로드맵 의존)

### 5.3 후보 set

한국 5 후보 (FIU 신고 + 은행 실명계좌 보유 사업자 + 운영 지속):
- Bithumb (#1, 사전 결정)
- Upbit
- Coinone
- Korbit
- Gopax

검토 후 제외:
- Bitsonic / ProBit Korea / Hanbitco / FoblGate / Cashierest 등 minor: VASP 인가 상태 불안정 또는 사실상 영업 축소. 자동매매 platform 의 SLA 요구 불만족.

## 6. 외부 지식 배경

### 6.1 한국 KRW 거래소 시장 구조

- FIU (금융정보분석원) 신고 + 은행 실명계좌 연동 의무 (특정금융정보법). 신고 사업자 = 시장 진입 자격.
- 실명계좌 제휴 은행 (대표): Upbit-K뱅크, Bithumb-NH농협은행, Coinone-카카오뱅크, Korbit-신한은행, Gopax-전북은행.
- 거래량 (2024-2025 기준 추정): Upbit 압도적 > Bithumb > Coinone > Korbit ≒ Gopax.
- 자동매매 측면 distinguishing factor = REST/WS 안정성, rate limit, 주문 실행 semantics 의 ecosystem maturity.

### 6.2 API 일반 관찰 (public knowledge, confidence M)

- Upbit: REST + WebSocket 모두 성숙. 문서 깔끔, 주요 사용 사례 (community bot / lib) 풍부. **자동매매 표준 first-pick 통설**.
- Coinone: 영문 문서 + REST/WS 가용. ecosystem 은 Upbit 보다 작음.
- Korbit: REST + WS 가용. 종목 폭 좁음.
- Gopax: REST + WS 가용. 운영 / 지배구조 history 가 시점 민감.

자세한 cell-level 점수는 ADR-001 §Decision 의 score matrix.

## 7. 설계 서사

### 7.1 Framework — 10 dimension API-first

자동매매 critical-path 우선. 사용자 결정 (Q3=A) + Codex push-back (P1=A: 주문 실행 semantics 추가) + Sonnet decider rebalance (P2=B: 종목수/수수료 over-가중 보정 + OHLCV partial 환원) 적용.

| Dimension | Weight | 근거 |
|---|---:|---|
| REST API 품질 (안정성·문서·error 처리) | 15% | 자동매매 base layer. 안정성 부재 시 모든 상위 기능 무력. |
| WebSocket realtime (지연·reconnect·메시지 손실) | 15% | 실시간 시세 + 체결 stream. 1초 reconnect 실패 1회로 손실 가능. |
| Rate limit / quota | 10% | bot 빈도 + multi-pair 동시 운영 가능 여부. |
| **주문 실행 semantics (NEW)** | **10%** | tick size / min notional / partial fill / cancel race / idempotency / post-only/IOC/FOK. Codex 가 가장 강하게 challenge — REST API 품질에 묻혀 underweight 였음. |
| Historical OHLCV depth | 8% | 백테스트 데이터. 단 mctrader-data 가 외부 보충 가능해 종전 10 → 8. |
| 유동성 (KRW pair top10 평균 일거래대금) | 15% | slippage / 체결성. 한국 top-3 모두 운영 가능 임계점 충족하나 격차 있음. |
| 종목 수 (KRW pair count) | 5% | 명목 종목수 보다 liquidity-adjusted universe 가 실질 — Codex push-back 으로 10 → 5. |
| 수수료 (taker rate, 등급) | 7% | 명시 fee 보다 implicit cost (slippage / 체결실패) 가 더 큼 — Codex push-back 으로 10 → 7. |
| Regulatory (FIU 신고 + 은행 실명계좌) | 10% | gate 성격 (binary 진입 자격) 이나 사고 history / 영업정지 risk 가 점수에도 반영. Codex 의 15% 권장은 본인이 "gate 에 가깝다" 인정과 모순 → 10% 유지. |
| 출금/입금 안정성 | 5% | 자동매매 단계 비중 낮음 (운영 빈도 낮음). |
| **Total** | **100%** | |

**Out-of-framework (activation re-validation checklist 로 분리, P3=B)**:
- API key 운영 난이도 (발급 UX / IP whitelist / 권한 scope / rotation) — empirical 측정 필수
- Sandbox / testnet / dry-run 친화성 — 부재 시 mock replay + shadow mode 의무
- 거래소별 사고 / 영업정지 history (regulatory 안에 sub-가중치로 흡수) — activation 직전 시점 정보 재확인

### 7.2 Score matrix (1-5 scale, 5 거래소 모두 포함)

cell 표기: `점수 / Confidence (H/M/L)`

| Dimension | Weight | Bithumb | Upbit | Coinone | Korbit | Gopax |
|---|---:|---|---|---|---|---|
| REST API 품질 | 15 | 4/M | 5/H | 4/M | 3/M | 2/L |
| WebSocket realtime | 15 | 4/M | 5/H | 4/M | 3/M | 2/L |
| Rate limit | 10 | 4/M | 4/H | 3/M | 3/L | 2/L |
| 주문 실행 semantics | 10 | 4/M | 4/M | 3/M | 3/L | 2/L |
| OHLCV depth | 8 | 4/M | 5/H | 4/M | 3/M | 2/L |
| 유동성 | 15 | 4/M | 5/H | 3/M | 2/M | 1/M |
| 종목 수 | 5 | 4/M | 5/H | 4/M | 2/M | 2/M |
| 수수료 | 7 | 5/H | 4/M | 3/M | 3/M | 3/L |
| Regulatory | 10 | 5/H | 5/H | 5/H | 5/H | 3/M |
| 입출금 | 5 | 4/M | 4/M | 4/M | 4/M | 2/L |

Bithumb 점수 추가 근거 (Codex baseline 외부 보완):
- REST/WS = 4/M — 운영 성숙하나 Upbit 대비 약간 낮은 통설
- 유동성 = 4/M — 한국 거래량 #2 (Upbit 압도적 #1 다음)
- 종목 수 = 4/M — KRW pair 다수, Upbit 보다 약간 적음
- 수수료 = **5/H — 0.04% taker (Upbit 0.05% 보다 낮음)** ← Bithumb 의 framework 내 distinguishing strength
- Regulatory = 5/H — FIU + NH농협 실명계좌
- 입출금 = 4/M — 안정적

**Weighted score 계산** (`Σ(점수 × weight) / 5` → 100점 만점):

| Exchange | Σ(점수 × weight) | Score / 100 |
|---|---:|---:|
| Upbit | 75+75+40+40+40+75+25+28+50+20 = **468** | **93.6** |
| **Bithumb** | 60+60+40+40+32+60+20+35+50+20 = **417** | **83.4** |
| Coinone | 60+60+30+30+32+45+20+21+50+20 = **368** | **73.6** |
| Korbit | 45+45+30+30+24+30+10+21+50+20 = **305** | **61.0** |
| Gopax | 30+30+20+20+16+15+10+21+30+10 = **202** | **40.4** |

### 7.3 Framework ranking vs Implementation sequence (분리 명시)

Bithumb 점수 (83.4) 가 Upbit (93.6) 보다 10.2점 낮으므로, **순수 framework ranking 기준 #1 = Upbit**. 그러나 **사용자 사전 결정 implementation sequence = Bithumb → Upbit** ("upbit, bithumb 이렇게 가자" + 첫 거래소 = Bithumb 명시). 두 ordering 은 별개 의미 — 충돌 아님.

**Framework ranking** (객관 점수 순):

| 순위 | 거래소 | Score |
|---:|---|---:|
| 1 | Upbit | 93.6 |
| 2 | Bithumb | 83.4 |
| 3 | Coinone | 73.6 |
| 4 | Korbit | 61.0 |
| 5 | Gopax | 40.4 |

**Implementation sequence** (사용자 사전 결정 build 순):

| build 순 | 거래소 | Score | repo |
|---:|---|---:|---|
| 1 | **Bithumb** | 83.4 | `mctrader-market-bithumb` (MCT-14) |
| 2 | **Upbit** | 93.6 | `mctrader-market-upbit` (future) |
| 3 | Coinone | 73.6 | (future) |
| 4 | Korbit | 61.0 | (future, low priority) |
| 5 | Gopax | 40.4 | (watchlist, regulatory 시점 의존) |

### 7.4 Bithumb-first implementation 근거 (out-of-framework, 추정 + 사용자 보강 대상)

framework score 가 Upbit 우위인데도 사용자가 Bithumb 을 implementation #1 으로 결정한 근거 추정 (사용자 본인 actual rationale 추후 보강 가능):

1. **수수료 우위** — Bithumb 0.04% taker vs Upbit 0.05% — 자동매매 회전 시 cumulative cost 차이 (framework 내 5/H vs 4/M 로 부분 반영)
2. **은행 친숙도** — NH농협 실명계좌 (사용자 기존 농협 account 활용 추정) — framework 외 personal-banking factor
3. **구현 단순성** — Bithumb signature 방식이 Upbit JWT 인증 보다 first-impl 학습 곡선 낮음 (framework 외 onboarding cost factor)
4. **Smaller-scale matched** — 개인 자동매매 first-impl 단계에서 거래량 폭주 / rate limit risk 가 Bithumb 이 Upbit 보다 낮을 수 있음 (framework 내 rate limit 4 vs 4 동률)
5. **단일 거래소 sufficient liquidity** — KRW BTC/ETH 등 main pair 의 Bithumb 유동성은 single-exchange 자동매매 운영 임계점 모두 충족 (framework 내 4/M)

Sensitivity: Bithumb 와 Upbit 격차 10.2점이라 framework 외 위 5개 factor 합산 영향이 10.2점 이상이면 Bithumb-first 가 합리적. 1번 (cumulative fee) 만으로도 long-run 자동매매 손익 측면에서 substantial — implementation sequence 정당화 가능.

### 7.5 #2 결정 (Upbit) 견고성

Bithumb 다음 추가할 #2 거래소 = **Upbit** (사용자 명시 + framework score 동의):
- Bithumb (83.4) → Upbit (93.6) 격차 +10.2점 (framework 측 next-strongest)
- Upbit → Coinone 격차 -20.0점 (다음 후보 차이 더 큼)
- Sensitivity 견고: 단일 low-confidence cell 1점 변화로 #2 ordering 역전 안 됨

### 7.6 Activation 시 empirical re-validation checklist

실제 #2 (Upbit) adapter build 직전에 본 checklist 수행 의무. ADR-001 §Consequences 에 박제.

- [ ] **WebSocket 7일 soak test** — reconnect 횟수, heartbeat 누락, sequence gap, orderbook drift, message loss 기록
- [ ] **REST latency** — endpoint 별 p50/p95/p99, 429/5xx 빈도, retry 후 중복 주문 가능성, nonce/timestamp 오류 측정
- [ ] **Private API 소액 실주문** — market/limit, partial fill, cancel race, 미체결 조회, 체결 stream + REST reconciliation 검증
- [ ] **Rate limit 실측** — 계정 단위 / IP 단위 / endpoint 단위 / burst / sustained / 차단 해제 정책
- [ ] **API key 운영** — 발급 UX, IP whitelist, read/trade/withdraw 권한 분리 가용, key rotation 절차
- [ ] **Sandbox/testnet 부재 시** — mock replay + shadow mode 를 adapter acceptance criteria 에 포함
- [ ] **Regulatory 시점 확인** — FIU 신고 상태 / 은행 실명계좌 연동 / 사고 history / 영업정지 여부 재조회

### 7.7 Codex 의견 적용 결과

Codex (codex-rescue, gpt-5.5 high) 가 Sonnet decider protocol (CFP-59 / ADR-019) 의 second-opinion 으로 dispatch 됨. 4 strong push-back:

| Push-back | 적용 |
|---|---|
| 주문 실행 semantics 별도 dimension 분리 | ✓ 적용 (P1=A) — 10-dim framework |
| Weight rebalance (종목수 / 수수료 over-가중) | ✓ 부분 적용 (P2=B) — 종목수 10→5, 수수료 10→7, OHLCV 10→8. Regulatory 15% 권장은 거부 (Codex 본인 "gate 에 가깝다" 와 모순). |
| API key / sandbox / 사고 history dimension 추가 | ✗ framework 미반영 (P3=B) — activation re-validation checklist 로 분리 |
| KRW-only scope 의 trade-off ADR consequences 명시 | ✓ 적용 (P4=A) — ADR-001 §Consequences 에 박제 |

Codex 의 ranking 결과 (Upbit 95 > Coinone 75 > Korbit 60 > Gopax 41, Bithumb 미평가) 와 본 Story 의 framework ranking (Upbit 93.6 > Bithumb 83.4 > Coinone 73.6 > Korbit 61.0 > Gopax 40.4) 이 4 거래소 ordering 일치, 격차 비슷. Bithumb (83.4) 은 Codex 가 평가 대상으로 받지 않은 거래소 — 본 Story 후속 보강에서 추가됨. **Implementation sequence #1 = Bithumb (사용자 사전 결정), #2 = Upbit** 양 결과 모두 권장.

## 8. 개발 서사

(Phase 2 PR — 본 Story 는 doc-only Story 로 종결. "개발" 단계 N/A.)

## 9. 품질 게이트 이력

(Phase 2 PR — N/A for doc-only Story.)

## 10. FIX Ledger

| Iter | 시각 | 레인 | 트리거 | 원인 판정 | 재실행 범위 | RESET? |
|------|------|------|--------|-----------|-------------|--------|

(FIX 발생 시 append.)

## 11. 회고

(Story 완료 시 PMOAgent 작성. 본 Story 는 manual flow 로 진행 — Codex second-opinion 가 첫 적용. 본 Story 의 1차 회고:)

- **Codex push-back 효과**: 사용자가 "적극적 의견 제시" 명시 후 Codex 가 framework 누락 1건 (주문 실행 semantics) + over-가중 2건 (종목수 / 수수료) 정확 지적. 단순 confirmation 이었다면 framework 의 critical weakness 가 박제됐을 것.
- **Sonnet decider 적용 형식 학습**: 처음엔 sub-decision 마다 사용자 confirmation 받음 → 사용자 push-back "sonnet decider 수행했다면 이렇게 stop할 필요 없다" 받음. memory `feedback_sonnet_decider_autoproceed.md` 에 박제. 향후 substantive decision 시 final 정지에 "결정됨 + 근거" 만 보고하는 형태로 운영.
- **Codex agent 의 직접 file write 발견**: codex-rescue agent 가 task dispatch 시 결과를 반환만 하지 않고 docs/stories/MCT-1.md / docs/adr/ADR-001-exchange-priority.md 를 직접 작성. 사용자 결정 P1~P4 를 거치지 않은 raw Codex draft → Claude 가 synthesized 버전으로 overwrite 필요. 향후 Codex dispatch 시 "결과 반환만, file 직접 작성 금지" 명시 필요할 수 있음 (또는 본 행동을 plugin-codeforge 측 finding 으로 등록 검토).
- **데뷔작 finding 추가**: 본 Story 진행 중 codeforge plugin 에 추가 finding 발견 안 됨 (4 install-time finding 외). Codex 7-카테고리 평가는 향후 Story 종료 시점에 적용 예정.
