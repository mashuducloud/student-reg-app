#!/usr/bin/env bash
set -euo pipefail

compose="docker compose -f infra/docker-compose.yml"

poll() {
  local url="$1" name="$2" tries="${3:-60}" sleep_s="${4:-2}"
  $compose exec -T prometheus sh -lc "
    set -eu
    ok=0
    for i in \$(seq 1 $tries); do
      if wget -qO- '$url' >/dev/null; then ok=1; break; fi
      sleep $sleep_s
    done
    [ \"\$ok\" -eq 1 ] || { echo '$name not ready'; exit 1; }
  "
}

echo "Waiting for student-app metrics..."
poll 'http://student-app:9100/metrics' 'student-app metrics'

echo "Waiting for otel-collector metrics..."
poll 'http://otel-collector:9464/metrics' 'otel-collector metrics'

echo "Waiting for Prometheus readiness..."
poll 'http://localhost:9090/-/ready' 'prometheus readiness'

echo "Health checks passed."
