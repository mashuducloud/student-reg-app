#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:?}"
ECR_REGISTRY="${ECR_REGISTRY:?}"
IMAGE_DEST="${IMAGE_DEST:?}"
TAG="${TAG:?}"

RDS_ENDPOINT="${RDS_ENDPOINT:?}"
DB_NAME="${DB_NAME:?}"
DB_USER="${DB_USER:?}"
DB_PASSWORD="${DB_PASSWORD:?}"

echo "Deploying tag: ${TAG}"
echo "Image dest: ${IMAGE_DEST}"

# Helper: send a command to an instance by Name tag
send() {
  local target_name="$1"
  shift
  local cmd="$*"

  aws ssm send-command \
    --region "${AWS_REGION}" \
    --document-name "AWS-RunShellScript" \
    --targets "Key=tag:Name,Values=${target_name}" \
    --parameters commands="$(printf '%s\n' "$cmd")" \
    --comment "student-reg-app preprod deploy ${TAG}" \
    --output text \
    --query "Command.CommandId"
}

login_cmd=$(cat <<EOF
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
EOF
)

# 1) Flyway (one-shot migrations)
flyway_cmd=$(cat <<EOF
set -euo pipefail
${login_cmd}
docker pull ${IMAGE_DEST}:flyway-migrations-${TAG}

docker run --rm \
  -e FLYWAY_URL="jdbc:mysql://${RDS_ENDPOINT}:3306/${DB_NAME}?allowPublicKeyRetrieval=true&useSSL=false" \
  -e FLYWAY_USER="${DB_USER}" \
  -e FLYWAY_PASSWORD="${DB_PASSWORD}" \
  -e FLYWAY_CONNECT_RETRIES=60 \
  ${IMAGE_DEST}:flyway-migrations-${TAG} \
  flyway -connectRetries=60 migrate
EOF
)

# 2) Backend (replace container)
backend_cmd=$(cat <<EOF
set -euo pipefail
${login_cmd}
docker pull ${IMAGE_DEST}:student-app-${TAG}

docker rm -f student-app || true
docker run -d --name student-app \
  --restart unless-stopped \
  -p 5000:5000 \
  -e DB_HOST="${RDS_ENDPOINT}" \
  -e DB_PORT="3306" \
  -e DB_NAME="${DB_NAME}" \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  ${IMAGE_DEST}:student-app-${TAG}

# quick health check
sleep 5
curl -fsS http://127.0.0.1:5000/health
EOF
)

# 3) Frontend (replace container)
frontend_cmd=$(cat <<EOF
set -euo pipefail
${login_cmd}
docker pull ${IMAGE_DEST}:student-frontend-${TAG}

docker rm -f student-frontend || true
docker run -d --name student-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ${IMAGE_DEST}:student-frontend-${TAG}

curl -fsS http://127.0.0.1/index.html >/dev/null || true
EOF
)

echo "Sending Flyway..."
CMD1=$(send "student-reg-app-pre-prod-flyway" "${flyway_cmd}")
echo "Flyway CommandId: ${CMD1}"

echo "Sending Backend..."
CMD2=$(send "student-reg-app-pre-prod-backend" "${backend_cmd}")
echo "Backend CommandId: ${CMD2}"

echo "Sending Frontend..."
CMD3=$(send "student-reg-app-pre-prod-frontend" "${frontend_cmd}")
echo "Frontend CommandId: ${CMD3}"

echo "SSM commands submitted."
