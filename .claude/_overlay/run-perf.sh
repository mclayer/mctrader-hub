#!/usr/bin/env bash
# .claude/_overlay/run-perf.sh — consumer가 작성하는 성능 테스트 wrapper
#
# TestAgent가 호출. baseline 대비 회귀 검증.
# Change Plan §8.3 "N/A" 명시 시 즉시 exit 0.
#
# 인터페이스:
# - 호출: .claude/_overlay/run-perf.sh [--scope=<path>]
# - 환경변수: PERF_BASELINE_NA=1 → 즉시 exit 0 (Orchestrator가 §8.3 packet 기반 설정)
# - exit 0: PASS (baseline 대비 mean 10% 이내)
# - exit non-zero: 회귀 (mean 10% 이상 악화) 또는 baseline 부재
# - stdout: 회귀 목록 (test_name + baseline mean → current mean + delta%)
#
# 아래는 pytest-benchmark 예시. 프로젝트 러너에 맞춰 교체 (k6, vegeta, criterion 등).

set -euo pipefail

[[ "${PERF_BASELINE_NA:-0}" == "1" ]] && {
  echo "PERF: skipped (Change Plan §8.3 = N/A)"
  exit 0
}

SCOPE_ARG=""
for arg in "$@"; do
  case "$arg" in
    --scope=*) SCOPE_ARG="${arg#--scope=}" ;;
  esac
done

PERF_DIR="${SCOPE_ARG:-tests/perf}"

[[ ! -d "$PERF_DIR" ]] || [[ -z "$(ls -A "$PERF_DIR" 2>/dev/null)" ]] && {
  echo "PERF: $PERF_DIR 비어있음 — auto PASS"
  exit 0
}

exec pytest "$PERF_DIR" \
  --benchmark-only \
  --benchmark-compare=tests/perf/baselines \
  --benchmark-compare-fail=mean:10%
