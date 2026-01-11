variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "student-reg-app"
}

variable "env" {
  type    = string
  default = "pre-prod"
}

variable "ecr_registry" {
  type    = string
  default = "724772092393.dkr.ecr.us-east-1.amazonaws.com"
}

variable "app_repo" {
  type    = string
  default = "mashkenneth/public-student-reg-app/pre-prod"
}

# RDS
variable "db_name" {
  type    = string
  default = "studentregapppreprod"
}

variable "db_username" {
  type    = string
  default = "admin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "allow_ssh" {
  type    = bool
  default = false
}

variable "ssh_cidr" {
  type    = string
  default = "0.0.0.0/0"
}
variable "key_name" {
  type        = string
  description = "EC2 key pair name for emergency SSH access"
}
