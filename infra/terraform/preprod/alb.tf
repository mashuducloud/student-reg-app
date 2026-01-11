resource "aws_lb" "alb" {
  name               = "${var.project}-${var.env}-alb"
  load_balancer_type = "application"
  internal           = false

  # Use PUBLIC subnets (from network.tf)
  subnets         = data.aws_subnets.public.ids
  security_groups = [aws_security_group.alb_sg.id]

  # Ensure IGW route exists before ALB is created
  depends_on = [aws_route.default_internet_access]
}

# --- NEW: short names to satisfy AWS 32-char limit ---
locals {
  tg_prefix = "sr-${var.env}" # e.g. sr-pre-prod
}

resource "aws_lb_target_group" "frontend_tg" {
  name     = "${local.tg_prefix}-fe" # <= 32 chars
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "backend_tg" {
  name     = "${local.tg_prefix}-be" # <= 32 chars
  port     = 5000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/health"
    matcher             = "200-399"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

locals {
  api_paths = [
    "/health*",
    "/students*",
    "/programmes*",
    "/enrolments*",
    "/attendance*",
    "/stipends*",
    "/assessments*",
    "/documents*",
    "/workplace-placements*",
    "/register*"
  ]
}

resource "aws_lb_listener_rule" "api_to_backend" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
