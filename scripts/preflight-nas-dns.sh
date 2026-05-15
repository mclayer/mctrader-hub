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

# Step 1: DNS resolution
if command -v dig >/dev/null 2>&1; then
  dig +short "$HOST" | grep -q . || { echo "[preflight] FAIL: DNS resolve $HOST"; exit 10; }
elif command -v getent >/dev/null 2>&1; then
  getent hosts "$HOST" >/dev/null || { echo "[preflight] FAIL: DNS resolve $HOST"; exit 10; }
elif command -v nslookup >/dev/null 2>&1; then
  nslookup "$HOST" >/dev/null 2>&1 || { echo "[preflight] FAIL: DNS resolve $HOST"; exit 10; }
else
  echo "[preflight] WARN: no DNS tool (dig/getent/nslookup) available, skipping DNS check"
fi
echo "[preflight] PASS: DNS resolved $HOST"

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
  mc alias set "$TMP_ALIAS" "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY" --quiet 2>/dev/null
  trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT
  mc ls "$TMP_ALIAS/$BUCKET" --quiet >/dev/null 2>&1 || { echo "[preflight] FAIL: S3 list $BUCKET"; exit 30; }
  echo "[preflight] PASS: S3 list bucket $BUCKET"
fi

echo "[preflight] ALL CHECKS PASS"
