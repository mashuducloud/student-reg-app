locals {
  # Prefer digest; fall back to tag if digest not set
  image = (
    var.image_digest != null && var.image_digest != ""
    ? format("%s/%s@%s", var.ecr_registry, var.repo_name, var.image_digest)
    : format("%s/%s:%s", var.ecr_registry, var.repo_name, var.image_tag)
  )
}

########################################
# Security group for the service
########################################
resource "aws_security_group" "svc" {
  name   = "${var.name}-sg"
  vpc_id = var.vpc_id

  # No inline ingress here; we define it with a separate aws_security_group_rule

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Allow traffic from the ALB SG to this service SG
resource "aws_security_group_rule" "from_alb" {
  type                     = "ingress"
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  security_group_id        = aws_security_group.svc.id
  source_security_group_id = var.alb_sg_id
}

########################################
# IAM for EC2 instances (ECR + logs)
########################################
resource "aws_iam_role" "ec2" {
  name = "${var.name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecr" {
  name = "${var.name}-ecr"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "profile" {
  name = "${var.name}-profile"
  role = aws_iam_role.ec2.name
}

########################################
# AMI + Region
########################################
data "aws_region" "current" {}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["137112412989"] # Amazon

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

########################################
# User data (docker + app container)
########################################
locals {
  userdata = <<-EOT
    #!/bin/bash
    set -euxo pipefail

    # Install Docker & AWS CLI (Amazon Linux 2023)
    dnf -y update || true
    dnf -y install docker awscli || (yum -y install docker awscli || true)
    systemctl enable docker
    systemctl start docker

    # Login to ECR
    aws ecr get-login-password --region ${data.aws_region.current.name} \
      | docker login --username AWS --password-stdin ${var.ecr_registry}

    # Pull & run container
    docker pull ${local.image}

    cat >/etc/systemd/system/app.service <<'UNIT'
    [Unit]
    Description=App Container
    After=docker.service
    Requires=docker.service

    [Service]
    Restart=always
    ExecStart=/usr/bin/docker run --rm --name app -p ${var.container_port}:${var.container_port} ${local.image}
    ExecStop=/usr/bin/docker stop app

    [Install]
    WantedBy=multi-user.target
    UNIT

    systemctl daemon-reload
    systemctl enable app
    systemctl start app
  EOT
}

########################################
# Launch template + ASG + target group
########################################
resource "aws_launch_template" "lt" {
  name_prefix   = "${var.name}-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.profile.name
  }

  vpc_security_group_ids = [aws_security_group.svc.id]

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.disk_gb
      volume_type           = "gp3"
      delete_on_termination = true
    }
  }

  user_data = base64encode(local.userdata)
}

resource "aws_lb_target_group" "tg" {
  name        = substr(replace(var.name, ".", "-"), 0, 31)
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = var.vpc_id

  health_check {
    path    = var.healthcheck_path
    matcher = "200-399"
  }
}

resource "aws_autoscaling_group" "asg" {
  name                = "${var.name}-asg"
  vpc_zone_identifier = var.private_subnet_ids
  desired_capacity    = var.desired_count
  min_size            = var.min_count
  max_size            = var.max_count
  health_check_type   = "ELB"
  target_group_arns   = [aws_lb_target_group.tg.arn]

  launch_template {
    id      = aws_launch_template.lt.id
    version = "$Latest"
  }

  lifecycle {
    create_before_destroy = true
  }
}

output "tg_arn" {
  value = aws_lb_target_group.tg.arn
}

output "svc_sg_id" {
  value = aws_security_group.svc.id
}
