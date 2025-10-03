# Student Reg App — CD on AWS (Blue/Green)

This bundle gives you:
- **Terraform** to provision a single **t2.micro** EC2 in the **default VPC**, with security group (22/80), EIP, and user-data that installs **Docker** + **Nginx**.
- A **GitHub Actions CD workflow** that deploys via SSH with **blue/green** on one instance by switching Nginx between two Compose stacks bound to different localhost ports.

> Free-tier friendly: single t2.micro, default VPC/Subnets, no ALB, no Route53. Blue/green is implemented with ports + Nginx.

---

## 1) Provision EC2 (Terraform)

Prereqs:
- AWS credentials with rights for EC2, VPC describe, IAM role/profile, EIP.
- Terraform >= 1.6

```bash
cd terraform
terraform init
terraform apply -auto-approve   -var="region=us-east-1"   -var="ssh_public_key=$(cat ~/.ssh/id_rsa.pub)"   -var="name_prefix=student-reg-app"   -var="allowed_ssh_cidr=YOUR.IP.ADDR.0/24"
```

Outputs will include the `public_ip` and a convenience `ssh_command`.

> On first login, create `/opt/app/shared/.env` with your production secrets (DB password, etc.). The CD workflow will **not** upload secrets—this file remains only on the server.

Example `/opt/app/shared/.env`:
```
DB_HOST=host.docker.internal
DB_PORT=3307
DB_NAME=student_registration_db
DB_USER=student
DB_PASSWORD=change_me
MYSQL_DATABASE=student_registration_db
MYSQL_USER=student
MYSQL_PASSWORD=change_me
MYSQL_ROOT_PASSWORD=change_me
MYSQL_ROOT_HOST=%
```

> The MySQL container (core) publishes `3307:3306` on the host; app containers connect to **host.docker.internal:3307** (we add the `host-gateway` entry in override).

---

## 2) GitHub Secrets

Set these in your repo **Settings → Secrets and variables → Actions → New repository secret**:

- `EC2_HOST` — public IP from Terraform output
- `EC2_USER` — for Ubuntu AMI use `ubuntu`
- `EC2_SSH_PRIVATE_KEY` — your **private** key corresponding to the uploaded public key

Optional (CI already exists separately): AWS creds are **not** required for the CD workflow below.

---

## 3) Deploy (Blue/Green)

The workflow lives at `.github/workflows/cd.yml`. It runs on:
- `workflow_dispatch` (manual)
- `push` to `dev`

What it does:

1. **Rsync** the repo to `/opt/app/releases/<git-sha>` on the instance.
2. Decide the **new color** (`blue` or `green`) based on `/opt/app/current_color`.
3. Generate a `ports.override.yml` to map:
   - blue → frontend `18080`, api `15000`, metrics `19100`
   - green → frontend `28080`, api `25000`, metrics `29100`
4. Ensure **core** services (DB, telemetry) are up under a distinct compose project `core`:
   ```bash
   docker compose -f infra/docker-compose.yml -p core up -d mysql-db otel-collector tempo prometheus grafana
   ```
5. Bring up **new color** (only `app` + `frontend`) with override and env:
   ```bash
   docker compose -f infra/docker-compose.yml -f infra/ports.override.yml      --env-file /opt/app/shared/.env      --env-file ./.env.deploy      -p <color> up -d --build app frontend
   ```
6. Health check new stack, then switch **Nginx** to its frontend port and reload.
7. Stop the **old color** stack.

To run it now, go to **Actions → CD → Run workflow**.

---

## Notes and Limits

- This uses one EC2 instance and **no load balancer** to stay free-tier-ish. Blue/green is achieved with two Compose projects and Nginx port switching.
- Only **one** MySQL/observability stack runs (project `core`). App stacks connect via `host.docker.internal:3307`.
- Ensure your repo’s `infra/docker-compose.yml` stays compatible; the workflow overrides only **ports** and **DB host/port** for `app` via an extra file.
- t2.micro is tiny—watch CPU/RAM. Consider turning off observability in prod or using profiles if you get OOM.
