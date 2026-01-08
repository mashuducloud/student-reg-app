
variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type    = string
  default = "us-east-1"
}

# Networking
variable "vpc_cidr" {
  type    = string
  default = "10.31.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

# ECR app images
variable "ecr_registry" {
  type        = string
  description = "ECR registry hostname, e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com"
}

variable "backend_repo_name" {
  type = string
}

variable "frontend_repo_name" {
  type = string
}

variable "backend_image_digest" {
  type        = string
  default     = null
  description = "sha256 digest for backend image (preferred)."
}

variable "frontend_image_digest" {
  type        = string
  default     = null
  description = "sha256 digest for frontend image (preferred)."
}

variable "backend_image_tag" {
  type        = string
  default     = null
  description = "fallback tag if digest not set."
}

variable "frontend_image_tag" {
  type        = string
  default     = null
  description = "fallback tag if digest not set."
}

# App ports
variable "backend_port" {
  type    = number
  default = 8080
}

variable "frontend_port" {
  type    = number
  default = 3000
}

# EC2 sizing
variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "min_count" {
  type    = number
  default = 1
}

variable "max_count" {
  type    = number
  default = 2
}

# Optional DNS (not wired to HTTPS in this minimal bundle)
variable "zone_id" {
  type    = string
  default = null
}

variable "app_domain" {
  type    = string
  default = null
}

################################################################################
# Cost / budgets
################################################################################

variable "monthly_budget_limit" {
  type        = number
  default     = 10
  description = "Monthly cost budget in USD for this account/environment."
}

variable "billing_alert_emails" {
  type        = list(string)
  default     = []
  description = "Email recipients for AWS Budget alerts. If empty, no budget is created."
}

variable "estimated_daily_cost" {
  type        = number
  default     = 5
  description = "Static estimate of daily cost in USD (for info outputs only)."
}

variable "estimated_monthly_cost" {
  type        = number
  default     = 10
  description = "Static estimate of monthly cost in USD (for info outputs only)."
}

variable "env_name" {
  description = "Environment name, e.g. pre-prod"
  type        = string
}

variable "db_username" {
  description = "Master username for the RDS SQL Server instance"
  type        = string
}

variable "db_password" {
  description = "Master password for the RDS SQL Server instance"
  type        = string
  sensitive   = true
}
