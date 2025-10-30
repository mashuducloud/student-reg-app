#!/usr/bin/env bash
set -euo pipefail

compose="docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml"
echo "Running in-network health checks from inside 'prometheus' container..."

# Wait for student-app metrics
ok=0
for i in $(seq 1 30); do
  if $compose exec -T prometheus sh -lc 'wget -qO- http://student-app:9100/metrics | head -n1 >/dev/null'; then
    ok=1; break
  fi
  sleep 2
done
[ "$ok" -eq 1 ] || { echo "student-app metrics not ready"; exit 1; }

# Wait for otel-collector metrics
ok=0
for i in $(seq 1 30); do
  if $compose exec -T prometheus sh -lc 'wget -qO- http://otel-collector:9464/metrics | head -n1 >/dev/null'; then
    ok=1; break
  fi
  sleep 2
done
[ "$ok" -eq 1 ] || { echo "otel-collector metrics not ready"; exit 1; }

# Prometheus readiness
$compose exec -T prometheus sh -lc 'wget -qO- http://localhost:9090/-/ready >/dev/null'
echo "In-network health checks OK."
