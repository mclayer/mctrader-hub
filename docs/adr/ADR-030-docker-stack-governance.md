# ADR-030: Docker stack governance — single-host compose + dev/prod profile + image registry + observability

## Status

Proposed (MCT-175 Phase 1 진입, 2026-05-15)
Accepted 전환 = MCT-175 LAND 시

## Context

`mctrader-hub/compose.yml` 은 인프라 stack (postgres + minio + redis + mc-init + prometheus + grafana +
nginx + exporters + signal-collector 5종) 을 정의하나, **mctrader-data (collector) + mctrader-engine
(paper-engine / backtest-runner) 어플리케이션 서비스가 누락**.

추가 미결 사항:
- dev (hub MinIO) / prod (NAS MinIO, mcnas01.internal.mclayer.it) profile 분리 부재 — 환경별 endpoint
  전환 수동
- image registry tag 정책 모호 (latest 혼용)
- container resource limits 미정의 (capacity 4 layer — ADR-029 §D11 정합 필요)
- EPIC-tier-promotion-single-source R-CRITICAL (WAL 30G 가설 미측정) carry over → 본 Epic MCT-179 책임

배경 관련 ADR:
- ADR-027 §D2 Stage 1 HTTP-only gate (NAS MinIO HTTP 평문 운영, MCT-155 TLS cutover 미확정)
- ADR-029 §D4 WAL local-only 정책 + §D11 4 layer capacity
- ADR-009 §D12 forward-only invariant

## Decision

### §D1 WAL host disk 별도 mount + L1 named volume

> owner: MCT-176

collector container 의 WAL 디렉터리는 **host bind mount** 로 박제:

```yaml
volumes:
  - /var/lib/mctrader/wal:/var/lib/mctrader/data   # host bind mount (ADR-030 §D1)
```

- **근거**: WAL = forward-only invariant (ADR-029 §D4). host disk 손실 = 영구 손실 risk 명시 acceptance.
  container lifecycle 에 의존하면 restart 시 WAL 소실 위험.
- **L1 cold cache** = `mctrader_l1` named volume (compose lifecycle 정합, 재시작 후에도 유지).
- **host disk loss acceptance**: R4 MEDIUM — 사용자 explicit accept 의무 (MCT-175 plan §0 확인).
  1d max loss window (host disk replace 후 forward-only). external backup 도입 = op risk 증가 → reject.

### §D2 paper-engine daemon + backtest-runner [oneshot] 동일 image command override

> owner: MCT-177 (paper daemon) + MCT-178 (backtest profile)

`mctrader-engine` Dockerfile = 단일 image, command override 로 분기:

```yaml
# paper-engine — daemon mode
paper-engine:
  image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
  command: ["paper", "--daemon"]
  restart: unless-stopped

# backtest-runner — oneshot (profiles: [backtest])
backtest-runner:
  image: ghcr.io/mclayer/mctrader-engine:${IMAGE_TAG:-latest}
  command: ["backtest", ...]
  profiles: ["backtest"]
  restart: "no"
```

- **근거**: image build 1회 → command 분기. dev/prod parity. backtest = profile trigger (별 invoke).

### §D3 compose profiles dev/prod + env_file 분리

> owner: MCT-175

```
Profile  │ MinIO endpoint         │ env_file
─────────┼────────────────────────┼──────────────
dev      │ http://minio:9000      │ .env.dev
prod     │ mcnas01.internal:9000  │ .env.prod
```

- `profiles: ["dev"]` — hub MinIO (minio, mc-init) service: dev profile 에서만 기동
- `profiles: ["prod"]` — NAS preflight only (스크립트 기동)
- `.env.dev` / `.env.prod` = `env_file:` 로 NAS_MINIO_* 변수 분기
- `.env.prod` = `.gitignore` 대상 (secret 포함)

**사용법**:
```bash
# dev
docker compose --profile dev --env-file .env.dev up

# prod
docker compose --profile prod --env-file .env.prod up
```

### §D7 NAS DNS 직접 해석 + preflight 검증

> owner: MCT-175 (preflight 도구) + MCT-176 (collector endpoint)

container 내부에서 `mcnas01.internal.mclayer.it:9000` DNS 직접 해석.

`scripts/preflight-nas-dns.sh` 가 `compose up` 전 3단계 검증:
1. DNS resolution (dig 또는 getent)
2. TCP connect (5s timeout)
3. S3 list bucket (mc client, optional)

exit code:
- `0` = ALL PASS
- `10` = DNS FAIL
- `20` = TCP FAIL
- `30` = S3 FAIL
- `99` = env parse FAIL

prod profile 진입 시 preflight exit 0 필수 gate.

### §D12 image registry pin — semver + sha + latest 병행

> owner: MCT-181

```
registry: ghcr.io/mclayer/{repo}:{tag}

prod  = ghcr.io/mclayer/mctrader-{repo}:sha-<7char>  (CI release 시 pin)
      + ghcr.io/mclayer/mctrader-{repo}:v{semver}    (release tag)
dev   = ghcr.io/mclayer/mctrader-{repo}:latest       (rapid iteration)
```

- **prod pin 의무**: `IMAGE_TAG=sha-xxxxxxx` .env.prod 에 박제, latest pull 금지
- **dev = latest** 허용 (local build fallback 포함)
- GitHub Actions `GITHUB_TOKEN` 사용 (ghcr.io write permission)

### §D13 각 repo 독립 uv.lock + cross-repo CI lock gate

> owner: MCT-175

- 6 repo 각자 `uv.lock` 유지 (monorepo lock 회피, 독립 lifecycle)
- `scripts/check_cross_repo_locks.py` — 핵심 lib (pyarrow / boto3 / pydantic / websockets) major version + python_version drift CI gate
- `.github/workflows/cross-repo-lock-check.yml` — hub PR push 마다 자동 실행
- drift = FAIL (merge 차단)

### §D17 SIGTERM graceful + startup InvariantHarness scan (외부 backup 없이)

> owner: MCT-179

- **SIGTERM handler**: collector/paper-engine/backtest-runner 모두 SIGTERM 수신 시 graceful drain
  (WAL flush + sealed segment 완료 대기, 60s timeout)
- **startup scan**: 컨테이너 시작 시 InvariantHarness 8종 scan (MCT-171 SSOT). 위반 시 warn + continue.
- **외부 backup 없음**: ADR-029 §D4 WAL local-only 정합. external backup sidecar = invariant 위반 + op
  risk 증가 → reject. host disk 손실 risk = R4 MEDIUM 명시 acceptance.

### §D18 명시 resource limits + Prometheus alert (>80% warn)

> owner: MCT-180

모든 어플리케이션 service 에 `deploy.resources.limits` 명시:

```yaml
deploy:
  resources:
    limits:
      memory: <M>m
      cpus: "<N>"
```

ADR-029 §D11 4 layer capacity 정합:
- WAL host disk: 30G (hard_limit) → container mem limit 별도
- L1 named volume: 20G → NAS 의존
- 컨테이너 memory limit: collector 512M / paper-engine 1G (MCT-180 에서 측정 후 확정)

Prometheus alert:
- `container_memory_usage_bytes` / `container_spec_memory_limit_bytes` > 0.80 → WARN
- MCT-179/180 에서 alert rule yaml 박제

## Consequences

**긍정**:
- 단일 compose stack 으로 dev/prod 동일 entry → operational parity
- env_file 분기 + profile flag 로 endpoint 전환 명시 → 운영 혼선 감소
- CI lock gate 로 cross-repo Python/lib version drift 사전 차단
- startup InvariantHarness scan 으로 컨테이너 기동 시 integrity 조기 감지

**부정 / risk**:
- R1 HIGH: NAS HTTP-only 평문 노출 (ADR-027 D2 Stage 1 한정). 내부망 + NAS firewall + .env 0600 + 90d
  rotation 으로 mitigation. MCT-155 TLS cutover는 별 Story 백로그 (MCT-176 진입 전 사용자 결정 의무).
  R1 acceptance carrier: user_acknowledged_at=2026-05-15 by mclayer8865@gmail.com (cross-ref: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md §5 R1)
- R4 MEDIUM: host disk 손실 → WAL local segment 영구 손실 (1d max). 사용자 explicit accept 완료
  (plan §0, 2026-05-15).
  R4 acceptance carrier: user_acknowledged_at=2026-05-15 by mclayer8865@gmail.com (cross-ref: docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md §5 R4)
- D17 startup scan overhead: 8 invariant 스캔 = 시작 시 I/O 증가. 60s graceful timeout 과의 균형 필요.

## Out of scope (manifest SSOT)

본 ADR 는 EPIC-mctrader-docker-stack 7 Story 범위 내 8 D 만 본문 박제. 아래 10 D 는 manifest 박제 후
별 Story 차원 결정/구현으로 defer. SSOT = `scope_manifests/EPIC-mctrader-docker-stack.yaml`.

| D | 내용 | Owner Story (manifest) |
|---|------|------------------------|
| D4 | container restart policy + healthcheck 표준 | MCT-177 / MCT-178 / MCT-180 |
| D5 | observability stack (prometheus + grafana + node-exporter) | MCT-179 |
| D8 | DR mode state machine 통합 (compose alert → dr_mode flip) | MCT-179 |
| D9 | NAS credential rotation (90d) automation | MCT-176 |
| D10 | universe override + Redis prefix isolation | MCT-177 / MCT-178 |
| D11 | compose config CI lint (yaml schema + service dep DAG) | MCT-178 |
| D14 | effective config stdout dump (collector entrypoint) | MCT-176 |
| D15 | paper-engine universe override env precedence | MCT-177 |
| D16 | backtest-runner oneshot artifact archive | MCT-178 / MCT-181 |
| D19 | backtest artifact NAS sync (별 prefix) | MCT-181 |

각 D 본문 박제 시점 = 해당 owner Story Phase 1 LAND (ADR-030 amendment box append).

## References

- Spec: `docs/superpowers/specs/2026-05-15-EPIC-mctrader-docker-stack-design.md`
- Plan: `docs/superpowers/plans/2026-05-15-mct-175-docker-stack-base.md`
- scope_manifest: `scope_manifests/EPIC-mctrader-docker-stack.yaml`
- 의존 ADR: ADR-029 (cold tier governance, §D4/§D11) / ADR-027 §D2 (HTTP Stage 1) / ADR-009 §D12
  (forward-only invariant)
- Owner Story: MCT-175 (ADR publish) / 후속 MCT-176 ~ MCT-181 (각 D 구현)
- Epic: EPIC-mctrader-docker-stack (2026-05-15 ~, 7 Story sequential)
