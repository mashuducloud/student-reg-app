#!/usr/bin/env bash
set -euo pipefail
# Smoke health for student-reg-app stack: run checks from inside the Prometheus container.

COMPOSE_FILE="infra/docker-compose.yml"
PROM_SVC="prometheus"
APP_METRICS_URL="http://student-app:9100/metrics"
OTEL_METRICS_URL="http://otel-collector:9464/metrics"
PROM_READY_URL="http://localhost:9090/-/ready"

retry() {
  local max="$1"; shift
  local delay="$1"; shift
  local name="$1"; shift
  local i
  for i in $(seq 1 "$max"); do
    if "$@"; then
      echo "[OK] ${name}"
      return 0
    fi
    echo "[wait] ${name} (attempt $i/${max})"
    sleep "$delay"
  done
  echo "[FAIL] ${name} after ${max} attempts"
  return 1
}

in_prom() {
  docker compose -f "${COMPOSE_FILE}" exec -T "${PROM_SVC}" sh -lc "$*"
}

echo "== docker compose ps =="
docker compose -f "${COMPOSE_FILE}" ps || true

retry 30 2 "student-app metrics"   in_prom "wget -qO- ${APP_METRICS_URL} >/dev/null"

retry 30 2 "otel-collector metrics"   in_prom "wget -qO- ${OTEL_METRICS_URL} >/dev/null"

retry 20 2 "prometheus readiness"   in_prom "wget -qO- ${PROM_READY_URL} >/dev/null"

echo "== Active targets (host API port 9091) =="
curl -fsS "http://localhost:9091/api/v1/targets?state=active" | jq -r '.data.activeTargets[].labels.job' || true

echo "Health checks completed successfully."
