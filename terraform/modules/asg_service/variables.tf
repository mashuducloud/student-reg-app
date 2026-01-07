variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_sg_id" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "disk_gb" {
  type = number
}

variable "container_port" {
  type = number
}

variable "ecr_registry" {
  type = string
}

variable "repo_name" {
  type = string
}

variable "image_tag" {
  type        = string
  default     = null
  description = "Fallback tag if digest is not set."
}

variable "image_digest" {
  type        = string
  default     = null
  description = "Preferred sha256 image digest."
}

variable "desired_count" {
  type = number
}

variable "min_count" {
  type = number
}

variable "max_count" {
  type = number
}

variable "healthcheck_path" {
  type = string
}
