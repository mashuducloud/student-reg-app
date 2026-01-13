locals {
  common_user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    # Log to file + EC2 console
    exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

    echo "== user-data started =="

    # Make dnf more reliable (avoid hanging forever)
    dnf -y clean all || true
    dnf -y makecache --setopt=timeout=30 --setopt=retries=5 || true

    echo "== installing amazon-ssm-agent =="
    dnf -y install amazon-ssm-agent --setopt=timeout=30 --setopt=retries=5

    echo "== starting amazon-ssm-agent =="
    systemctl enable --now amazon-ssm-agent
    systemctl status amazon-ssm-agent --no-pager || true

    echo "== installing docker (optional, don’t block SSM) =="
    dnf -y install docker --setopt=timeout=30 --setopt=retries=5 || true
    systemctl enable --now docker || true

    echo "== connectivity check =="
    curl -IfsS https://ssm.us-east-1.amazonaws.com/ || true

    echo "== user-data finished =="
  EOF
}


resource "aws_instance" "frontend" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnets.public.ids[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.frontend_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  user_data                   = local.common_user_data
  key_name                    = var.key_name

  tags = {
    Name = "${var.project}-${var.env}-frontend"
  }
}


resource "aws_instance" "backend" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnets.public.ids[1]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.backend_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  user_data                   = local.common_user_data
  key_name                    = var.key_name

  tags = {
    Name = "${var.project}-${var.env}-backend"
  }
}


resource "aws_instance" "flyway" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnets.public.ids[2]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.flyway_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  user_data                   = local.common_user_data
  key_name                    = var.key_name

  root_block_device {
  volume_size = 30
  volume_type = "gp3"
  }

  tags = {
    Name = "${var.project}-${var.env}-flyway"
  }
}
