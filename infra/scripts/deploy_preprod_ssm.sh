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

get_instance_id() {
  local target_name="$1"

  local iid
  iid="$(
    aws ec2 describe-instances \
      --region "${AWS_REGION}" \
      --filters "Name=tag:Name,Values=${target_name}" "Name=instance-state-name,Values=running" \
      --query "Reservations[0].Instances[0].InstanceId" \
      --output text
  )"

  if [ -z "${iid}" ] || [ "${iid}" = "None" ]; then
    echo "❌ No RUNNING EC2 instance found with tag Name=${target_name}"
    echo "Tip: confirm the tag exists and the instance is running in ${AWS_REGION}."
    exit 1
  fi

  echo "${iid}"
}

# Wait until SSM has created at least one invocation record for this command+instance
wait_for_invocation() {
  local command_id="$1"
  local instance_id="$2"
  local target_name="$3"

  echo "Waiting for SSM invocation to appear for ${target_name} (InstanceId=${instance_id}, CommandId=${command_id})..."

  for _ in $(seq 1 30); do
    local status
    status="$(
      aws ssm get-command-invocation \
        --region "${AWS_REGION}" \
        --command-id "${command_id}" \
        --instance-id "${instance_id}" \
        --query "Status" \
        --output text 2>/dev/null || true
    )"

    # Once it exists, Status will be something like Pending/InProgress/Success/Failed/etc.
    if [ -n "${status}" ] && [ "${status}" != "None" ]; then
      echo "Invocation found (Status=${status})."
      return 0
    fi

    sleep 2
  done

  echo "❌ Timed out waiting for invocation to appear."
  echo "Debug: list invocations for CommandId=${command_id}:"
  aws ssm list-command-invocations \
    --region "${AWS_REGION}" \
    --command-id "${command_id}" \
    --details \
    --output json || true

  exit 1
}

send() {
  local target_name="$1"
  shift
  local cmd="$*"

  local instance_id
  instance_id="$(get_instance_id "${target_name}")"
  echo "Target ${target_name} -> ${instance_id}" >&2

  local commands_json
  commands_json="$(printf '%s\n' "$cmd" | jq -R . | jq -s .)"

  local command_id
  command_id="$(
    aws ssm send-command \
      --region "${AWS_REGION}" \
      --document-name "AWS-RunShellScript" \
      --instance-ids "${instance_id}" \
      --parameters "{\"commands\": ${commands_json}}" \
      --comment "student-reg-app preprod deploy ${TAG}" \
      --output text \
      --query "Command.CommandId"
  )" || {
    echo "❌ send-command failed for ${target_name} (${instance_id})" >&2
    exit 1
  }

  # ONLY output these two fields on stdout:
  echo "${command_id} ${instance_id}"
}

wait_cmd() {
  local command_id="$1"
  local instance_id="$2"
  local target_name="$3"

  wait_for_invocation "${command_id}" "${instance_id}" "${target_name}"

  echo "Waiting for completion: ${target_name} (InstanceId=${instance_id}, CommandId=${command_id})..."
  aws ssm wait command-executed \
    --region "${AWS_REGION}" \
    --command-id "${command_id}" \
    --instance-id "${instance_id}" || {
      echo "❌ Command failed or timed out for ${target_name}. Showing output:"
      aws ssm get-command-invocation \
        --region "${AWS_REGION}" \
        --command-id "${command_id}" \
        --instance-id "${instance_id}" \
        --output json || true
      exit 1
    }

  echo "✅ ${target_name} completed."
}

login_cmd=$(cat <<EOF
set -euo pipefail
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
EOF
)

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

sleep 5
curl -fsS http://127.0.0.1:5000/health
EOF
)

frontend_cmd=$(cat <<EOF
set -euo pipefail
${login_cmd}
docker pull ${IMAGE_DEST}:student-frontend-${TAG}

docker rm -f student-frontend || true
docker run -d --name student-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ${IMAGE_DEST}:student-frontend-${TAG}

curl -fsS http://127.0.0.1/ >/dev/null
EOF
)

echo "Sending Flyway..."
read -r CMD1 IID1 < <(send "student-reg-app-pre-prod-flyway" "${flyway_cmd}")
echo "Flyway CommandId: ${CMD1}"
wait_cmd "${CMD1}" "${IID1}" "student-reg-app-pre-prod-flyway"

echo "Sending Backend..."
read -r CMD2 IID2 < <(send "student-reg-app-pre-prod-backend" "${backend_cmd}")
echo "Backend CommandId: ${CMD2}"
wait_cmd "${CMD2}" "${IID2}" "student-reg-app-pre-prod-backend"

echo "Sending Frontend..."
read -r CMD3 IID3 < <(send "student-reg-app-pre-prod-frontend" "${frontend_cmd}")
echo "Frontend CommandId: ${CMD3}"
wait_cmd "${CMD3}" "${IID3}" "student-reg-app-pre-prod-frontend"

echo "✅ Preprod deploy completed."
