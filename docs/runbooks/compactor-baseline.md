# Compactor baseline 캡처 runbook (MCT-134)

## 목적
Phase 0 — A1 stabilize 적용 전 / 후 비교 baseline 확보.

## 절차 (baseline = A1 적용 전)

1. compactor 컨테이너에 tracemalloc 스크립트 attach:
   ```
   # 중요: 컨테이너 내 파일명을 "tracemalloc.py" 로 하면 stdlib tracemalloc 모듈을
   # 스크립트 자신이 shadow → AttributeError. 반드시 다른 이름으로 cp.
   docker cp tools/compactor-tracemalloc.py mctrader-compactor:/tmp/compactor_capture.py
   docker exec mctrader-compactor sh -c \
       'nohup python /tmp/compactor_capture.py \
            --duration-hours 12 --interval-min 10 \
            --out /var/lib/mctrader/data/_tracemalloc/baseline \
            >/var/lib/mctrader/data/_tracemalloc/baseline.log 2>&1 &
        echo PID=$!'
   # 검증: 1-2분 뒤 snap-<ts>.pkl 파일이 baseline/ 에 생기는지 확인.
   ```

2. Prometheus 에서 12 시간 동안 다음 query 시계열 저장:
   - `compactor_process_rss_bytes{container="mctrader-compactor"}`
   - `rate(container_cpu_usage_seconds_total{name="mctrader-compactor"}[5m])`

3. 12 시간 후 tracemalloc dump 회수:
   ```
   docker cp mctrader-compactor:/var/lib/mctrader/data/_tracemalloc/baseline \
       ./baseline-2026-05-11
   ```

4. 결과 1줄 보고 (`docs/runbooks/compactor-baseline-results-YYYY-MM-DD.md`):
   - peak RSS bytes
   - 마지막 RSS bytes
   - 12h 동안 증가량
   - top 5 tracemalloc allocator (마지막 snapshot)

## A1 적용 후 (Task 9 에서 사용)

위 절차 동일하나 `--out /var/lib/mctrader/data/_tracemalloc/after-a1`. 비교 보고서: `docs/runbooks/compactor-a1-effect-YYYY-MM-DD.md`.

## 주의 — tracemalloc 스코프

이 스크립트는 **자기 자신의 Python 프로세스**의 allocator 만 본다 (compactor 본체 RSS 가 아님). compactor 본체의 메모리는 `compactor_process_rss_bytes` Prometheus gauge 로 추적. tracemalloc dump 은 capture 프로세스 자체의 미세 누수만 식별 — 두 신호를 함께 봐야 함.
