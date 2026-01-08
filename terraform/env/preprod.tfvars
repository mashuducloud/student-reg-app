
################################################################################
# Pre-prod configuration (example)
################################################################################

project     = "student-reg"
environment = "pre-prod"
region      = "us-east-1"

# VPC CIDR range
vpc_cidr = "10.31.0.0/16"

# ECR registry & repos (replace with your real account ID & repo names)
ecr_registry       = "724772092393.dkr.ecr.us-east-1.amazonaws.com"
backend_repo_name  = "mashkenneth/public-student-reg-app/pre-prod"
frontend_repo_name = "mashkenneth/public-student-reg-app/pre-prod"

# Prefer digests for immutability (replace with real sha256 values)
backend_image_digest  = "sha256:3840e5090c1f5d1ead963a00bf3963241d0e8a332b9f8b385c0af26db3f504f9"
frontend_image_digest = "sha256:d5d1bb9a941ac2cbdfedd3983f966023e2f624d147b442d490ebd62b034d847d"

# Optional tag fallback (if you don't want to use digests)
# backend_image_tag  = "backend-0d8989226d24"
# frontend_image_tag = "frontend-0d8989226d24"

backend_port  = 8080
frontend_port = 3000

instance_type  = "t2.micro"
desired_count  = 1
min_count      = 1
max_count      = 1

# Budgets + cost estimates
monthly_budget_limit = 10
billing_alert_emails = ["mashudu.mambani@gmail.com"]

estimated_daily_cost   = 5
estimated_monthly_cost = 10

db_username = "studentadmin"
db_password = "ChangeMe12345!"

env_name = "pre-prod"
