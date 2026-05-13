# NAS MinIO TLS 재검토 결정 박제 — Stage 2 종료 (MCT-155)

**Authored**: 2026-05-13 (Stage 2 마지막 Story MCT-155)
**Author**: ArchitectPLAgent (chief synthesizer)
**Source**: `scope_manifests/EPIC-cold-tier-nas-minio.yaml` design_decisions S12 user_confirmed
**ADR-027 amendment**: D2 mandatory (`triggers_adr_amendment.adr=ADR-027.section=D2.trigger_story=MCT-155`)

본 runbook = Stage 2 종료 시점 사용자 confirm 박제 + ADR-027 D2 amendment 의 박제 trail.

---

## §1 사용자 confirm 결정 verbatim (S12 박제)

scope_manifest `design_decisions.S12` 직접 인용 (`user_confirmed: true`, `user_confirmed_at: 2026-05-12`):

> **S12 — Stage 2 TLS 재검토 timing (D2 escalation 의무)**
>
> **Decision**: HTTP 유지 (Stage 1 정책 연장) — Stage 2 cutover 후 MCT-155 재검토
>
> **Rationale**: 사용자 confirm — Stage 1 4중 mitigation (LAN-only + .env 0600 + 90d rotation + IP-allowlist firewall) 유지. cutover 중 TLS 활성화 = endpoint URL 변경 + dual-write invariant 재검증 강제 (disruptive)

**Stage 2 종료 시점 (MCT-155, 2026-05-13) 사용자 재확인 결정**: **HTTP 유지** (Stage 1 정책 연장 그대로).

---

## §2 TLS 도입 시 cost 분석

### §2.1 Cert 비용

| 옵션 | 비용 | 운영 부담 | 적합성 |
|---|---|---|---|
| **Self-signed cert** | $0 | client trust 박제 의무 (CA cert 양측 컨테이너 install) + 만료 monitoring | LAN 내부망 운영 시 적합 — but trust 박제 의무 부담 |
| **Let's Encrypt (public DNS)** | $0 | public DNS 의존성 + 90d rotation 자동화 + DNS challenge 설정 | NAS = public access 0 (LAN-only) → public DNS 부재 → **부적합** |
| **상용 cert (e.g. DigiCert)** | $100~$500/yr | cert renewal 절차 + 운영 vendor 의존성 | LAN 내부망 운영 시 ROI 낮음 → **부적합** |

**결론**: LAN-only 환경에서 self-signed cert 가 유일 옵션 (public DNS 없음). 그러나 client trust 박제 부담 + manual rotation 의무.

### §2.2 TLS handshake latency

- **HTTPS handshake** = TLS 1.3 기준 추가 1-RTT (~5-20ms LAN 환경)
- **MCT-148 T2 baseline** (HTTP) = 50MB p99 = 2870.65ms — TLS 추가 시 ~2890.65ms (~0.7% 증가)
- **NFR-1 (50MB < 10000ms)** = 충족 가능 — handshake overhead 무시 가능

### §2.3 Cert rotation cadence

- **Self-signed cert**: 자율 결정 — 권고 = 1년 (ADR-008 secret rotation cadence 와 별 cadence)
- **자동화 부재**: rotation 시점 양측 컨테이너 cert 교체 + container restart 의무 (90d secret rotation 과 cadence 분리)
- **rotation runbook 의무**: 별 runbook (`docs/runbooks/nas-minio-tls-cert-rotation.md`) 신설 의무 (TLS 활성화 시점)

---

## §3 TLS 도입 시 운영 부담 분석

| 항목 | 현재 (HTTP) | TLS 활성화 후 |
|---|---|---|
| **endpoint URL** | `http://nas:9000` | `https://nas:9000` (or `:9001`) — 양측 컨테이너 env 갱신 의무 |
| **client trust** | 0 | self-signed CA cert 양측 컨테이너 install + 갱신 의무 |
| **handshake monitoring** | 0 | TLS handshake fail 알람 추가 (`tls_handshake_error_total` Prometheus metric) |
| **cert expiry monitoring** | 0 | cert 만료 30d 전 alert (`tls_cert_expiry_days` Prometheus metric) |
| **rotation cadence** | 90d (secret only) | 90d (secret) + 365d (cert) — 2 cadence 운영 |
| **dual-write invariant** | 정합 (S5 7종) | **재검증 의무** (endpoint URL 변경 시 invariant verify trigger — S5 무 영향이지만 운영 verify 필요) |
| **NAS unreachable SOP** | MCT-152 land | TLS 측 추가 failure mode (cert expiry / handshake fail) — SOP 갱신 의무 |

**결론**: TLS 활성화 시 운영 부담 ~30-50% 증가 (cert 관리 + 추가 failure mode + 추가 monitoring).

---

## §4 외부 노출 검토 결과

### §4.1 현재 NAS 방화벽 정책 (Stage 1 정책 유지)

scope_manifest `risk_register.R10` + `R7` 정합:

- **NAS 방화벽 port 9000/9001** = mctrader 호스트 IP only (LAN 내부망 격리)
- **외부 노출** = 0 (port forwarding 0, public DNS 0)
- **방화벽 monitoring** = 90d rotation 시점 재검증 (MCT-147 deploy runbook 박제)

### §4.2 외부 노출 결정 시 TLS 활성화 trigger

**조건 (어느 하나라도 발생 시 TLS 활성화 trigger)**:

1. NAS 측 외부 노출 (port forwarding 또는 public DNS 활성화)
2. 사용자 directive 변경 (외부 access 요구)
3. 별 컨테이너 / 호스트 NAS access 추가 (mctrader 호스트 외부)
4. cert rotation 자동화 정책 land (cert manager 도입 시)

본 trigger 미발생 시 → HTTP 유지 (Stage 1 정책 연장).

---

## §5 Future re-evaluation trigger

본 결정 (HTTP 유지) 의 재검토 시점:

| Trigger | 우선순위 | 재검토 의무 항목 |
|---|---|---|
| **§4.2 외부 노출 결정** | P0 (즉시) | TLS 활성화 + cert manager 도입 + endpoint URL 갱신 |
| **NAS hardware 교체** | P1 (1주 내) | 신규 NAS 의 TLS 지원 정책 검토 + 기존 정책 유지 가부 |
| **Stage 3 또는 future Epic 발의** | P1 (Epic spawn 시점) | brainstorm Phase 0 시점 TLS 재검토 입력 |
| **Secret leak 의심** | P0 (즉시) | emergency rotation + TLS 활성화 검토 (외부 노출 가능성 평가) |
| **사용자 directive 변경** | P0 (즉시) | 사용자 confirm 변경 박제 + S12 user_confirmed update + ADR-027 D2 wording 갱신 |

---

## §6 ADR-027 D2 amendment commit 박제

본 runbook 의 결정 (HTTP 유지) → ADR-027 D2 wording 갱신:

**before (D2 현재 wording)**:
> Stage 1 = HTTP, Stage 2 = TLS 재검토 의무 (MCT-155 진입 시 사용자 confirm)

**after (D2 본 amendment 후 wording)**:
> Stage 1 = HTTP, Stage 2 = HTTP 유지 (사용자 confirm 2026-05-13, S12 user_confirmed). 4중 mitigation (LAN-only + .env 0600 + 90d rotation + IP-allowlist firewall) Stage 2 후에도 그대로 유지. TLS 활성화 trigger = §4.2 4 조건 (`docs/runbooks/nas-minio-tls-review.md` §4.2 박제).

**amendment commit**: 본 PR (`mclayer/mctrader-hub` Phase 2 PR) 의 hub 측 산출물 (ADR-027 file 직접 수정).

**scope_manifest sync**: `triggers_adr_amendment.adr=ADR-027.section=D2.status: pending → committed` (PMOAgent retro 시점 update).

---

## References

- `scope_manifests/EPIC-cold-tier-nas-minio.yaml` design_decisions S12
- `docs/adr/ADR-027-cold-tier-object-storage-nas-minio.md` D2
- `docs/runbooks/nas-minio-secret-rotation.md` (90d cadence runbook, MCT-147)
- `docs/runbooks/nas-minio-deploy.md` (NAS 방화벽 정책, MCT-147)
- ADR-008 (Secret Management policy)
