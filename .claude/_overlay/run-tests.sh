#!/usr/bin/env bash
# .claude/_overlay/run-tests.sh — consumer가 작성하는 기능 테스트 wrapper
#
# TestAgent가 호출. 프로젝트 러너로 unit/integration/infra 테스트 실행.
# 성능 마커는 deselect (성능은 run-perf.sh에서).
#
# 인터페이스:
# - 호출: .claude/_overlay/run-tests.sh [--scope=<path>]
# - exit 0: ALL PASS
# - exit non-zero: 하나 이상 FAIL
# - stdout: 통과 개수 + 실패 목록 (test_file::test_name + 에러 유형·메시지)
#
# 아래는 pytest 예시. 프로젝트 러너에 맞춰 교체.

set -euo pipefail

SCOPE_ARG=""
for arg in "$@"; do
  case "$arg" in
    --scope=*) SCOPE_ARG="${arg#--scope=}" ;;
  esac
done

PATHS=("tests/unit" "tests/integration" "tests/infra")
[[ -n "$SCOPE_ARG" ]] && PATHS=("$SCOPE_ARG")

# 예: pytest (성능 마커 deselect)
exec pytest "${PATHS[@]}" \
  -m "not perf" \
  --tb=short \
  -q
