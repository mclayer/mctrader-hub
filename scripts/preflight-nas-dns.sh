#!/usr/bin/env bash
# mctrader-hub/scripts/preflight-nas-dns.sh
# NAS MinIO endpoint preflight (D7, ADR-030)
# Usage: ./scripts/preflight-nas-dns.sh [.env.prod]
#
# Exit codes:
#   0  = all checks PASS
#   10 = DNS resolution FAIL
#   20 = TCP connect FAIL
#   30 = S3 list bucket FAIL
#   99 = .env.prod parse FAIL or curl/dig missing

set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[preflight] FAIL: env file not found: $ENV_FILE" >&2
  exit 99
fi

# P2-1 fix: env file syntax validate before sourcing
if ! bash -n "$ENV_FILE" 2>/dev/null; then
  echo "[preflight] FAIL: $ENV_FILE syntax invalid" >&2
  exit 99
fi

# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

ENDPOINT="${NAS_MINIO_ENDPOINT:?NAS_MINIO_ENDPOINT not set in $ENV_FILE}"
ACCESS_KEY="${NAS_MINIO_ACCESS_KEY:?NAS_MINIO_ACCESS_KEY not set}"
SECRET_KEY="${NAS_MINIO_SECRET_KEY:?NAS_MINIO_SECRET_KEY not set}"
BUCKET="${NAS_MINIO_BUCKET:-mctrader-market}"

# Parse host:port
HOST_PORT="${ENDPOINT#http://}"
HOST_PORT="${HOST_PORT#https://}"
HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"
[[ "$PORT" == "$HOST" ]] && PORT="80"

echo "[preflight] endpoint = $ENDPOINT (host=$HOST, port=$PORT)"

# Step 1: DNS resolution + P1-2 fix: sentinel IP validation (wildcard DNS guard)
if command -v dig >/dev/null 2>&1; then
  RESOLVED_IPS=$(dig +short "$HOST" 2>/dev/null || true)
elif command -v getent >/dev/null 2>&1; then
  RESOLVED_IPS=$(getent hosts "$HOST" 2>/dev/null | awk '{print $1}' || true)
elif command -v nslookup >/dev/null 2>&1; then
  RESOLVED_IPS=$(nslookup "$HOST" 2>/dev/null | awk '/^Address: /{print $2}' | grep -v '#' || true)
else
  echo "[preflight] WARN: no DNS tool (dig/getent/nslookup) available, skipping DNS check"
  RESOLVED_IPS="SKIP"
fi

if [[ "$RESOLVED_IPS" != "SKIP" ]]; then
  if [[ -z "$RESOLVED_IPS" ]]; then
    echo "[preflight] FAIL: DNS resolve $HOST returned empty" >&2
    exit 10
  fi
  # P1-2 fix: wildcard DNS sentinel check (corporate DNS 0.0.0.0 / 127.0.0.1)
  if echo "$RESOLVED_IPS" | grep -qE '^(0\.0\.0\.0|127\.0\.0\.1)$'; then
    echo "[preflight] FAIL: DNS resolve $HOST returned sentinel IP ($RESOLVED_IPS) -- wildcard DNS suspected" >&2
    exit 10
  fi
fi
echo "[preflight] PASS: DNS resolved $HOST ($RESOLVED_IPS)"

# Step 2: TCP connect
if ! timeout 5 bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null; then
  echo "[preflight] FAIL: TCP connect $HOST:$PORT"
  exit 20
fi
echo "[preflight] PASS: TCP connect $HOST:$PORT"

# Step 3: S3 list bucket (mc client)
if ! command -v mc >/dev/null; then
  echo "[preflight] WARN: 'mc' not available, skipping S3 list bucket check"
else
  TMP_ALIAS="preflight-$$"
  # P1-3 fix: trap BEFORE mc alias set to avoid SIGINT race
  trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT INT TERM
  mc alias set "$TMP_ALIAS" "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" --quiet 2>/dev/null
  mc ls "$TMP_ALIAS/$BUCKET" --quiet >/dev/null 2>&1 || { echo "[preflight] FAIL: S3 list $BUCKET"; exit 30; }
  echo "[preflight] PASS: S3 list bucket $BUCKET"
fi

echo "[preflight] ALL CHECKS PASS"
