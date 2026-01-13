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

echo "Deploying tag: ${TAG}" >&2
echo "Image dest: ${IMAGE_DEST}" >&2

# Get the first RUNNING instance id with tag Name=<target_name>
get_instance_id() {
  local target_name="$1"

  local iid
  iid="$(
    aws ec2 describe-instances \
      --region "${AWS_REGION}" \
      --filters \
        "Name=tag:Name,Values=${target_name}" \
        "Name=instance-state-name,Values=running" \
      --query "Reservations[].Instances[].InstanceId | [0]" \
      --output text
  )"

  if [ -z "${iid}" ] || [ "${iid}" = "None" ]; then
    echo "❌ No RUNNING EC2 instance found with tag Name=${target_name} in ${AWS_REGION}" >&2
    exit 1
  fi

  echo "${iid}"
}

# Check if SSM sees the instance and it is Online
ssm_is_online() {
  local iid="$1"
  local status
  status="$(
    aws ssm describe-instance-information \
      --region "${AWS_REGION}" \
      --filters "Key=InstanceIds,Values=${iid}" \
      --query "InstanceInformationList[0].PingStatus" \
      --output text 2>/dev/null || true
  )"
  [ "${status}" = "Online" ]
}

# Wait for instance to become SSM Online (up to ~5 minutes)
wait_for_ssm_online() {
  local iid="$1"
  local target_name="$2"

  echo "Waiting for SSM Online: ${target_name} (${iid})..." >&2
  for _ in $(seq 1 60); do
    if ssm_is_online "${iid}"; then
      echo "✅ SSM Online: ${target_name} (${iid})" >&2
      return 0
    fi
    sleep 5
  done

  echo "❌ Instance is RUNNING but not SSM Online: ${target_name} (${iid})" >&2
  echo "Fix checklist:" >&2
  echo "  - EC2 has IAM role with AmazonSSMManagedInstanceCore" >&2
  echo "  - amazon-ssm-agent installed + running" >&2
  echo "  - outbound internet (public IP + IGW route) OR VPC endpoints (ssm, ssmmessages, ec2messages)" >&2
  exit 1
}

# Wait until SSM has created an invocation record for this command+instance
wait_for_invocation() {
  local command_id="$1"
  local instance_id="$2"
  local target_name="$3"

  echo "Waiting for SSM invocation to appear for ${target_name} (InstanceId=${instance_id}, CommandId=${command_id})..." >&2

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

    if [ -n "${status}" ] && [ "${status}" != "None" ]; then
      echo "Invocation found (Status=${status})." >&2
      return 0
    fi

    sleep 2
  done

  echo "❌ Timed out waiting for invocation to appear." >&2
  echo "Debug: list invocations for CommandId=${command_id}:" >&2
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

  wait_for_ssm_online "${instance_id}" "${target_name}"

  local commands_json
  commands_json="$(printf '%s\n' "${cmd}" | jq -R . | jq -s .)"

  local command_id
  command_id="$(
    aws ssm send-command \
      --region "${AWS_REGION}" \
      --document-name "AWS-RunShellScript" \
      --targets "Key=tag:Name,Values=${target_name}" \
      --parameters "{\"commands\": ${commands_json}}" \
      --comment "student-reg-app preprod deploy ${TAG}" \
      --query "Command.CommandId" \
      --output text
  )" || {
    echo "❌ send-command failed for ${target_name} (${instance_id})" >&2
    exit 1
  }

  # IMPORTANT: stdout must contain ONLY this line:
  echo "${command_id} ${instance_id}"
}

wait_cmd() {
  local command_id="$1"
  local instance_id="$2"
  local target_name="$3"

  wait_for_invocation "${command_id}" "${instance_id}" "${target_name}"

  echo "Waiting for completion: ${target_name} (InstanceId=${instance_id}, CommandId=${command_id})..." >&2
  aws ssm wait command-executed \
    --region "${AWS_REGION}" \
    --command-id "${command_id}" \
    --instance-id "${instance_id}" || {
      echo "❌ Command failed or timed out for ${target_name}. Showing output:" >&2
      aws ssm get-command-invocation \
        --region "${AWS_REGION}" \
        --command-id "${command_id}" \
        --instance-id "${instance_id}" \
        --output json || true
      exit 1
    }

  echo "✅ ${target_name} completed." >&2
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

docker rm -f student-frontend 2>/dev/null || true
docker run -d --name student-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ${IMAGE_DEST}:student-frontend-${TAG}

# Retry for up to ~60s without bash loops (SSM-safe)
curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://127.0.0.1/ >/dev/null || {
  echo "❌ Frontend did not become healthy in time"
  docker ps -a || true
  docker logs --tail 200 student-frontend || true
  exit 1
}

echo "✅ Frontend healthy"
EOF
)

echo "Sending Flyway..." >&2
read -r CMD1 IID1 < <(send "student-reg-app-pre-prod-flyway" "${flyway_cmd}")
echo "Flyway CommandId: ${CMD1}" >&2
wait_cmd "${CMD1}" "${IID1}" "student-reg-app-pre-prod-flyway"

echo "Sending Backend..." >&2
read -r CMD2 IID2 < <(send "student-reg-app-pre-prod-backend" "${backend_cmd}")
echo "Backend CommandId: ${CMD2}" >&2
wait_cmd "${CMD2}" "${IID2}" "student-reg-app-pre-prod-backend"

echo "Sending Frontend..." >&2
read -r CMD3 IID3 < <(send "student-reg-app-pre-prod-frontend" "${frontend_cmd}")
echo "Frontend CommandId: ${CMD3}" >&2
wait_cmd "${CMD3}" "${IID3}" "student-reg-app-pre-prod-frontend"

echo "✅ Preprod deploy completed." >&2
