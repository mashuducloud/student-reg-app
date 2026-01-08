variable "env_name" {
  description = "Environment name, e.g. pre-prod"
  type        = string
}

variable "vpc_id" {
  description = "VPC where the RDS instance will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the RDS subnet group"
  type        = list(string)
}

variable "vpc_cidr" {
  description = "CIDR range of the VPC (used for SG rules)"
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

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "multi_az" {
  description = "Whether to deploy Multi-AZ (not free-tier)"
  type        = bool
  default     = false
}
