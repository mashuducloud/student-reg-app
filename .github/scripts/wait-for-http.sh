#!/usr/bin/env bash
set -euo pipefail
URL="${1:?usage: wait-for-http.sh <url> [timeout-seconds]}"
TIMEOUT="${2:-120}"
until curl -fsS "$URL" >/dev/null; do
  TIMEOUT=$((TIMEOUT-2)) || true
  if [ "$TIMEOUT" -le 0 ]; then
    echo "Timeout waiting for $URL"
    exit 1
  fi
  sleep 2
done
echo "OK: $URL"
