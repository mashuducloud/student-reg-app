
locals {
  name = "${var.project}-${var.environment}"
}

module "net" {
  source   = "./modules/network"
  name     = local.name
  vpc_cidr = var.vpc_cidr
  az_count = var.az_count
}

module "alb" {
  source            = "./modules/alb"
  name              = local.name
  vpc_id            = module.net.vpc_id
  public_subnet_ids = module.net.public_subnet_ids
}

# FRONTEND service
module "frontend" {
  source             = "./modules/asg_service"
  name               = "${local.name}-frontend"
  vpc_id             = module.net.vpc_id
  private_subnet_ids = module.net.private_subnet_ids
  alb_sg_id          = module.alb.alb_sg_id

  instance_type  = var.instance_type
  disk_gb        = 16
  container_port = var.frontend_port

  ecr_registry = var.ecr_registry
  repo_name    = var.frontend_repo_name
  image_tag    = var.frontend_image_tag
  image_digest = var.frontend_image_digest

  desired_count = var.desired_count
  min_count     = var.min_count
  max_count     = var.max_count

  healthcheck_path = "/"
}

# BACKEND service
module "backend" {
  source             = "./modules/asg_service"
  name               = "${local.name}-backend"
  vpc_id             = module.net.vpc_id
  private_subnet_ids = module.net.private_subnet_ids
  alb_sg_id          = module.alb.alb_sg_id

  instance_type  = var.instance_type
  disk_gb        = 16
  container_port = var.backend_port

  ecr_registry = var.ecr_registry
  repo_name    = var.backend_repo_name
  image_tag    = var.backend_image_tag
  image_digest = var.backend_image_digest

  desired_count = var.desired_count
  min_count     = var.min_count
  max_count     = var.max_count

  healthcheck_path = "/health"
}

# ALB listeners + routing
resource "aws_lb_listener" "http" {
  load_balancer_arn = module.alb.alb_arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "forward"
    forward {
      target_group {
        arn = module.frontend.tg_arn
      }
    }
  }
}

# Optional: separate rule for backend on /api/*
resource "aws_lb_listener_rule" "backend_path" {
  listener_arn = aws_lb_listener.http.arn

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = module.backend.tg_arn
  }
}

module "db" {
  source = "./db"

  env_name           = var.env_name
  vpc_id             = module.net.vpc_id
  private_subnet_ids = module.net.private_subnet_ids
  vpc_cidr           = var.vpc_cidr

  db_username = var.db_username
  db_password = var.db_password
}
