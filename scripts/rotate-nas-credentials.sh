#!/usr/bin/env bash
# mctrader-hub/scripts/rotate-nas-credentials.sh
# NAS MinIO credential 90d rotation (ADR-030 §D9 + docs/runbooks/nas-credential-rotation-automation.md)
#
# Usage:
#   ./scripts/rotate-nas-credentials.sh [--dry-run] [--slack-webhook URL]
#
# Exit codes:
#   0  PASS
#   10 .env.prod missing
#   20 mc command fail
#   30 Slack send fail
#   99 prerequisite error (unknown arg / env file syntax invalid)

set -euo pipefail

DRY_RUN=0
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --slack-webhook) SLACK_WEBHOOK="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 99 ;;
  esac
done

ENV_FILE=".env.prod"
[[ -f "$ENV_FILE" ]] || { echo "[rotate] FAIL: $ENV_FILE missing" >&2; exit 10; }

# P2-1 fix: env file syntax validate before sourcing
if ! bash -n "$ENV_FILE" 2>/dev/null; then
  echo "[rotate] FAIL: $ENV_FILE syntax invalid" >&2
  exit 99
fi

# shellcheck disable=SC1091
set -a; source "$ENV_FILE"; set +a

# 1) Generate new credentials
NEW_ACCESS_KEY="mctrader-rotated-$(date +%Y%m%d)"
NEW_SECRET_KEY=$(openssl rand -base64 32 | tr -d '+/=' | head -c 40)

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[rotate] DRY-RUN: new access_key=$NEW_ACCESS_KEY (secret_key hidden)"
  exit 0
fi

# 2) mc admin (real rotation)
TMP_ALIAS="rotate-$$"
# P1-3 pattern: trap BEFORE set to avoid race on EXIT
trap "mc alias remove $TMP_ALIAS --quiet 2>/dev/null || true" EXIT INT TERM
mc alias set "$TMP_ALIAS" "$NAS_MINIO_ENDPOINT" "$NAS_MINIO_ACCESS_KEY" "$NAS_MINIO_SECRET_KEY" --quiet

mc admin user add "$TMP_ALIAS" "$NEW_ACCESS_KEY" "$NEW_SECRET_KEY" || { echo "[rotate] FAIL: mc admin user add" >&2; exit 20; }
mc admin policy attach "$TMP_ALIAS" readwrite --user "$NEW_ACCESS_KEY" || { echo "[rotate] FAIL: mc admin policy attach" >&2; exit 20; }

# 3) .env.prod update (atomic via sed in-place with backup)
OLD_ACCESS_KEY="$NAS_MINIO_ACCESS_KEY"
sed -i.bak \
  -e "s|^NAS_MINIO_ACCESS_KEY=.*|NAS_MINIO_ACCESS_KEY=$NEW_ACCESS_KEY|" \
  -e "s|^NAS_MINIO_SECRET_KEY=.*|NAS_MINIO_SECRET_KEY=$NEW_SECRET_KEY|" \
  "$ENV_FILE"

echo "[rotate] .env.prod updated (backup: $ENV_FILE.bak)"

# 4) collector restart (compose environment)
docker compose --profile prod restart collector || { echo "[rotate] WARN: collector restart failed"; }

# 5) old credential 5 min grace then revoke
echo "[rotate] waiting 300s before revoking old key $OLD_ACCESS_KEY ..."
sleep 300
mc admin user remove "$TMP_ALIAS" "$OLD_ACCESS_KEY" --quiet || { echo "[rotate] WARN: old key revoke failed"; }

# 6) Slack notification
if [[ -n "$SLACK_WEBHOOK" ]]; then
  curl -sf -X POST -H "Content-Type: application/json" \
    -d "{\"text\":\"[mctrader] NAS credential rotated: $OLD_ACCESS_KEY -> $NEW_ACCESS_KEY ($(date -u +%Y-%m-%dT%H:%M:%SZ))\"}" \
    "$SLACK_WEBHOOK" || { echo "[rotate] FAIL: Slack send" >&2; exit 30; }
fi

echo "[rotate] PASS -- new key: $NEW_ACCESS_KEY"
